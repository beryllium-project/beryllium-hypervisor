// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: exhaustive host-side unit and adversarial test suite for the
 *          accepted R2 non-privileged Sv39x4 backend. Exercises the full
 *          thirteen-resource fixed profile through R1 seal+derive into R2
 *          build+walk, covering every positive and negative case in the
 *          accepted plan's test matrix.
 * Trust:   test tool only. It grants no runtime authority, links no image,
 *          executes no privileged code, and makes no QEMU or hardware claim.
 * Scope:   R2 host evidence only. It checks offline fixed fixtures and exact
 *          rejection classes where the mechanism contract makes them specific.
 */
#include <stdio.h>
#include <string.h>

#include <be/manifest.h>
#include <be/r1-config.h>
#include <be/r2.h>
#include <be/state.h>

/* --- Fixed pool bases from R0 layout --- */

#define POOL_BASE_MANAGEMENT	BE_U64_C(0x80214000)
#define POOL_BASE_PROTECTED	BE_U64_C(0x8021c000)

/* --- Expected HGATP values --- */

#define HGATP_MANAGEMENT \
	(BE_HGATP_MODE_SV39X4 | (POOL_BASE_MANAGEMENT >> 12))
#define HGATP_PROTECTED \
	(BE_HGATP_MODE_SV39X4 | (POOL_BASE_PROTECTED >> 12))

/* --- Fixed 32 KiB pool arrays (static, no heap) --- */

static be_u8 pool_buf_management[BE_SV39X4_POOL_SIZE];
static be_u8 pool_buf_protected[BE_SV39X4_POOL_SIZE];


/* --- Test infrastructure --- */

static int failures;
static int test_count;


static void fail_named(const char *name)
{
	printf("BE_R2_CHECK: FAIL %s\n", name);
	++failures;
}

static void pass_named(const char *name)
{
	(void)name;
	++test_count;
}

static void require(int condition, const char *name)
{
	++test_count;
	if (!condition)
		fail_named(name);
}

static void expect_check(const char *name, enum be_check_result actual,
			 enum be_check_result expected)
{
	++test_count;
	if (actual != expected) {
		printf("BE_R2_CHECK: FAIL %s expected=%s actual=%s\n", name,
		       be_check_result_name(expected),
		       be_check_result_name(actual));
		++failures;
	}
}

/* --- Byte-buffer LE helpers (same as implementation) --- */

static be_u64 load_le64(const be_u8 *src)
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

static void store_le64(be_u8 *dst, be_u64 value)
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

/* --- Pool helper: zero and set up default descriptors --- */

static void init_pools(struct be_r2_pool_desc pools[2])
{
	memset(pool_buf_management, 0, BE_SV39X4_POOL_SIZE);
	memset(pool_buf_protected, 0, BE_SV39X4_POOL_SIZE);
	pools[0].base = POOL_BASE_MANAGEMENT;
	pools[0].buf = pool_buf_management;
	pools[0].buf_size = BE_SV39X4_POOL_SIZE;
	pools[1].base = POOL_BASE_PROTECTED;
	pools[1].buf = pool_buf_protected;
	pools[1].buf_size = BE_SV39X4_POOL_SIZE;
}

static int pool_is_zeroed(const be_u8 *buf, be_u64 size)
{
	be_u64 i;

	for (i = 0U; i < size; ++i) {
		if (buf[i] != 0U)
			return 0;
	}
	return 1;
}

/* --- R1 setup: drive runtime through copy/validate/seal/derive --- */

static int prepare_derived(struct be_runtime *runtime)
{
	enum be_runtime_result rr;

	*runtime = (struct be_runtime)BE_RUNTIME_INITIALIZER;
	rr = be_runtime_copy_inventory(runtime, be_r1_inventory());
	if (rr != BE_RUNTIME_OK)
		return 0;
	rr = be_runtime_copy_proposal(runtime, be_r1_proposal());
	if (rr != BE_RUNTIME_OK)
		return 0;
	rr = be_runtime_validate(runtime);
	if (rr != BE_RUNTIME_OK)
		return 0;
	rr = be_runtime_seal(runtime);
	if (rr != BE_RUNTIME_OK)
		return 0;
	rr = be_runtime_derive(runtime);
	if (rr != BE_RUNTIME_OK)
		return 0;
	return runtime->phase == BE_RUNTIME_PHASE_DERIVED;
}

/* ===================================================================
 * POSITIVE TESTS
 * =================================================================== */

/* P1/P5: full end-to-end build succeeds with BUILT state */
static void test_p1_full_build(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "p1-r1-setup");

	init_pools(pools);
	memset(&output, 0, sizeof(output));

	rc = be_r2_build(&runtime, pools, &output);
	expect_check("p1-build-ok", rc, BE_CHECK_OK);
	require(output.state == BE_R2_STATE_BUILT, "p1-state-built");
	pass_named("p1");
}

/* P2: management HGATP exact value */
static void test_p2_hgatp_management(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;

	require(prepare_derived(&runtime), "p2-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	be_r2_build(&runtime, pools, &output);
	require(output.state == BE_R2_STATE_BUILT, "p2-state-built");
	require(output.results[0].hgatp == HGATP_MANAGEMENT,
		"p2-hgatp-management-exact");
	pass_named("p2");
}

/* P3: protected HGATP exact value */
static void test_p3_hgatp_protected(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;

	require(prepare_derived(&runtime), "p3-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	be_r2_build(&runtime, pools, &output);
	require(output.state == BE_R2_STATE_BUILT, "p3-state-built");
	require(output.results[1].hgatp == HGATP_PROTECTED,
		"p3-hgatp-protected-exact");
	pass_named("p3");
}

/* P4: leaf count == 3 for each root */
static void test_p4_leaf_counts(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;

	require(prepare_derived(&runtime), "p4-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	be_r2_build(&runtime, pools, &output);
	require(output.state == BE_R2_STATE_BUILT, "p4-state-built");
	require(output.results[0].leaf_count == 3U, "p4-leaf-count-mgmt");
	require(output.results[1].leaf_count == 3U, "p4-leaf-count-prot");
	pass_named("p4");
}

/* P7: exactly 1 root pointer, 1 L1 pointer, 3 leaves per pool */
static void test_p7_pool_structure(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	be_u32 root_index;

	require(prepare_derived(&runtime), "p7-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	be_r2_build(&runtime, pools, &output);
	require(output.state == BE_R2_STATE_BUILT, "p7-state-built");

	for (root_index = 0U; root_index < 2U; ++root_index) {
		be_u8 *buf = pools[root_index].buf;
		be_u64 pte;
		be_u32 ptr_count = 0U;
		be_u32 leaf_count = 0U;
		be_u32 i;

		/* Count root pointer PTEs. */
		for (i = 0U; i < 2048U; ++i) {
			pte = load_le64(buf + (be_u64)i * 8U);
			if (pte != 0U) {
				/* V=1, RWX=0 → pointer */
				require((pte & 1U) != 0U, "p7-root-pte-valid");
				require((pte & 0xEU) == 0U,
					"p7-root-pte-pointer");
				++ptr_count;
			}
		}
		require(ptr_count == 1U, "p7-one-root-pointer");

		/* Count L1 pointer PTEs. */
		ptr_count = 0U;
		for (i = 0U; i < 512U; ++i) {
			pte = load_le64(buf + BE_U64_C(0x4000) +
					(be_u64)i * 8U);
			if (pte != 0U) {
				require((pte & 1U) != 0U, "p7-l1-pte-valid");
				require((pte & 0xEU) == 0U,
					"p7-l1-pte-pointer");
				++ptr_count;
			}
		}
		require(ptr_count == 1U, "p7-one-l1-pointer");

		/* Count L0 leaf PTEs. */
		for (i = 0U; i < 512U; ++i) {
			pte = load_le64(buf + BE_U64_C(0x5000) +
					(be_u64)i * 8U);
			if (pte != 0U)
				++leaf_count;
		}
		require(leaf_count == 3U, "p7-three-leaves");
	}
	pass_named("p7");
}

/* P8: all root entries except index 1 are zero */
static void test_p8_root_unused(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	be_u32 root_index, i;

	require(prepare_derived(&runtime), "p8-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	be_r2_build(&runtime, pools, &output);
	require(output.state == BE_R2_STATE_BUILT, "p8-state-built");

	for (root_index = 0U; root_index < 2U; ++root_index) {
		be_u8 *buf = pools[root_index].buf;

		for (i = 0U; i < 2048U; ++i) {
			be_u64 pte = load_le64(buf + (be_u64)i * 8U);

			if (i == 1U)
				require(pte != 0U, "p8-root-entry-1-present");
			else
				require(pte == 0U, "p8-root-entry-zero");
		}
	}
	pass_named("p8");
}

/* P9: all L1 entries except index 0 are zero */
static void test_p9_l1_unused(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	be_u32 root_index, i;

	require(prepare_derived(&runtime), "p9-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	be_r2_build(&runtime, pools, &output);
	require(output.state == BE_R2_STATE_BUILT, "p9-state-built");

	for (root_index = 0U; root_index < 2U; ++root_index) {
		be_u8 *buf = pools[root_index].buf;

		for (i = 0U; i < 512U; ++i) {
			be_u64 pte = load_le64(buf + BE_U64_C(0x4000) +
					       (be_u64)i * 8U);
			if (i == 0U)
				require(pte != 0U, "p9-l1-entry-0-present");
			else
				require(pte == 0U, "p9-l1-entry-zero");
		}
	}
	pass_named("p9");
}

/* P10: spare pages (6, 7) are entirely zero */
static void test_p10_spare_pages(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	be_u32 root_index;

	require(prepare_derived(&runtime), "p10-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	be_r2_build(&runtime, pools, &output);
	require(output.state == BE_R2_STATE_BUILT, "p10-state-built");

	for (root_index = 0U; root_index < 2U; ++root_index) {
		be_u8 *buf = pools[root_index].buf;

		require(pool_is_zeroed(buf + BE_U64_C(0x6000),
				       BE_U64_C(0x2000)),
			"p10-spare-zeroed");
	}
	pass_named("p10");
}

/* P11: independent re-walk via be_r2_walk_and_check */
static void test_p11_rewalk(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(prepare_derived(&runtime), "p11-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	be_r2_build(&runtime, pools, &output);
	require(output.state == BE_R2_STATE_BUILT, "p11-state-built");

	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("p11-rewalk-ok", rc, BE_CHECK_OK);
	require(leaf_sets[0].count == 3U, "p11-rewalk-count-0");
	require(leaf_sets[1].count == 3U, "p11-rewalk-count-1");

	/* Verify exact GPA/PA/rights for management root leaves. */
	{
		int found_priv = 0, found_shared = 0, found_code = 0;
		be_size i;

		for (i = 0U; i < leaf_sets[0].count; ++i) {
			struct be_r2_leaf *l = &leaf_sets[0].leaves[i];

			if (l->gpa == BE_U64_C(0x40000000) &&
			    l->pa == BE_U64_C(0x8022e000) &&
			    l->rights == (BE_RIGHT_READ | BE_RIGHT_WRITE))
				found_priv = 1;
			else if (l->gpa == BE_U64_C(0x40002000) &&
				 l->pa == BE_U64_C(0x80230000) &&
				 l->rights == (BE_RIGHT_READ | BE_RIGHT_WRITE))
				found_shared = 1;
			else if (l->gpa == BE_U64_C(0x40010000) &&
				 l->pa == BE_U64_C(0x80232000) &&
				 l->rights ==
					 (BE_RIGHT_READ | BE_RIGHT_EXECUTE))
				found_code = 1;
		}
		require(found_priv, "p11-mgmt-private-leaf");
		require(found_shared, "p11-mgmt-shared-leaf");
		require(found_code, "p11-mgmt-code-leaf");
	}

	/* Verify exact GPA/PA/rights for protected root leaves. */
	{
		int found_priv = 0, found_shared = 0, found_code = 0;
		be_size i;

		for (i = 0U; i < leaf_sets[1].count; ++i) {
			struct be_r2_leaf *l = &leaf_sets[1].leaves[i];

			if (l->gpa == BE_U64_C(0x40001000) &&
			    l->pa == BE_U64_C(0x8022f000) &&
			    l->rights == (BE_RIGHT_READ | BE_RIGHT_WRITE))
				found_priv = 1;
			else if (l->gpa == BE_U64_C(0x40002000) &&
				 l->pa == BE_U64_C(0x80230000) &&
				 l->rights == BE_RIGHT_READ)
				found_shared = 1;
			else if (l->gpa == BE_U64_C(0x40011000) &&
				 l->pa == BE_U64_C(0x80233000) &&
				 l->rights ==
					 (BE_RIGHT_READ | BE_RIGHT_EXECUTE))
				found_code = 1;
		}
		require(found_priv, "p11-prot-private-leaf");
		require(found_shared, "p11-prot-shared-leaf");
		require(found_code, "p11-prot-code-leaf");
	}
	pass_named("p11");
}

/* ===================================================================
 * NEGATIVE TESTS — R1 integrity
 * =================================================================== */

/* N1: NULL runtime */
static void test_n1_null_runtime(void)
{
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build((const struct be_runtime *)0, pools, &output);
	expect_check("n1-null-runtime", rc, BE_CHECK_NULL);
	require(output.state == BE_R2_STATE_FAILED, "n1-state-failed");
	pass_named("n1");
}

/* N2: runtime in SEALED phase (not DERIVED) */
static void test_n2_wrong_phase_sealed(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	*(&runtime) = (struct be_runtime)BE_RUNTIME_INITIALIZER;
	be_runtime_copy_inventory(&runtime, be_r1_inventory());
	be_runtime_copy_proposal(&runtime, be_r1_proposal());
	be_runtime_validate(&runtime);
	be_runtime_seal(&runtime);
	/* DO NOT derive — stay at SEALED */

	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n2-wrong-phase-sealed", rc, BE_CHECK_INVALID_PHASE);
	require(output.state == BE_R2_STATE_FAILED, "n2-state-failed");
	require(pool_is_zeroed(pool_buf_management, BE_SV39X4_POOL_SIZE),
		"n2-pool0-scrubbed");
	require(pool_is_zeroed(pool_buf_protected, BE_SV39X4_POOL_SIZE),
		"n2-pool1-scrubbed");
	pass_named("n2");
}

/* N3: runtime in EMPTY phase */
static void test_n3_wrong_phase_empty(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	runtime = (struct be_runtime)BE_RUNTIME_INITIALIZER;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n3-wrong-phase-empty", rc, BE_CHECK_INVALID_PHASE);
	require(output.state == BE_R2_STATE_FAILED, "n3-state-failed");
	pass_named("n3");
}

/* N4: canonical identity mutated */
static void test_n4_identity_mismatch(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n4-r1-setup");
	runtime.canonical.configuration_id += 1U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n4-identity-mismatch", rc, BE_CHECK_INTEGRITY);
	require(output.state == BE_R2_STATE_FAILED, "n4-state-failed");
	pass_named("n4");
}

/* N5: enforcement configuration_id mismatch */
static void test_n5_enforcement_id_mismatch(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n5-r1-setup");
	runtime.enforcement.configuration_id += 1U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n5-enforcement-id-mismatch", rc, BE_CHECK_INTEGRITY);
	require(output.state == BE_R2_STATE_FAILED, "n5-state-failed");
	pass_named("n5");
}

/* N6: sealed == 0 */
static void test_n6_not_sealed(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n6-r1-setup");
	runtime.sealed = 0U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n6-not-sealed", rc, BE_CHECK_INTEGRITY);
	require(output.state == BE_R2_STATE_FAILED, "n6-state-failed");
	pass_named("n6");
}

/* N7: output already BUILT */
static void test_n7_output_already_built(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n7-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	output.state = BE_R2_STATE_BUILT;
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n7-already-built", rc, BE_CHECK_INVALID_PHASE);
	/* State remains BUILT (no change). */
	require(output.state == BE_R2_STATE_BUILT, "n7-state-unchanged");
	pass_named("n7");
}

/* N8: output already FAILED */
static void test_n8_output_already_failed(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n8-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	output.state = BE_R2_STATE_FAILED;
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n8-already-failed", rc, BE_CHECK_INVALID_PHASE);
	require(output.state == BE_R2_STATE_FAILED, "n8-state-unchanged");
	pass_named("n8");
}

/* N8a: NULL output pointer */
static void test_n8a_null_output(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n8a-r1-setup");
	init_pools(pools);
	rc = be_r2_build(&runtime, pools, (struct be_r2_output *)0);
	expect_check("n8a-null-output", rc, BE_CHECK_NULL);
	pass_named("n8a");
}

/* N8b: validated_identity zeroed */
static void test_n8b_validated_identity_zero(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n8b-r1-setup");
	runtime.validated_identity = 0U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n8b-validated-id-zero", rc, BE_CHECK_INTEGRITY);
	require(output.state == BE_R2_STATE_FAILED, "n8b-state-failed");
	pass_named("n8b");
}

/* N8c: sealed_identity zeroed */
static void test_n8c_sealed_identity_zero(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n8c-r1-setup");
	runtime.sealed_identity = 0U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n8c-sealed-id-zero", rc, BE_CHECK_INTEGRITY);
	require(output.state == BE_R2_STATE_FAILED, "n8c-state-failed");
	pass_named("n8c");
}

/* N8d: validated_identity != sealed_identity */
static void test_n8d_identity_mismatch(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n8d-r1-setup");
	runtime.validated_identity = runtime.sealed_identity + 1U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n8d-identity-mismatch", rc, BE_CHECK_INTEGRITY);
	require(output.state == BE_R2_STATE_FAILED, "n8d-state-failed");
	pass_named("n8d");
}

/* N8e: sealed_identity != canonical.configuration_id */
static void test_n8e_sealed_ne_canonical(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n8e-r1-setup");
	/* Mutate sealed to something else (canonical stays same). */
	runtime.sealed_identity = runtime.canonical.configuration_id + 1U;
	runtime.validated_identity = runtime.sealed_identity;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n8e-sealed-ne-canonical", rc, BE_CHECK_INTEGRITY);
	require(output.state == BE_R2_STATE_FAILED, "n8e-state-failed");
	pass_named("n8e");
}

/* N8f: be_configuration_identity(canonical) != configuration_id */
static void test_n8f_recompute_mismatch(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n8f-r1-setup");
	/* Mutate a scalar that changes identity but keep stored id the same. */
	runtime.canonical.hart_id = 99U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n8f-recompute-mismatch", rc, BE_CHECK_INTEGRITY);
	require(output.state == BE_R2_STATE_FAILED, "n8f-state-failed");
	pass_named("n8f");
}

/* N8g: check_result != BE_CHECK_OK */
static void test_n8g_check_result_bad(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n8g-r1-setup");
	runtime.check_result = BE_CHECK_INCOMPLETE;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n8g-check-result-bad", rc, BE_CHECK_INTEGRITY);
	require(output.state == BE_R2_STATE_FAILED, "n8g-state-failed");
	pass_named("n8g");
}

/* ===================================================================
 * NEGATIVE TESTS — pool descriptors
 * =================================================================== */

/* N9: NULL pool buf (first) */
static void test_n9_null_buf(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n9-r1-setup");
	init_pools(pools);
	pools[0].buf = (be_u8 *)0;
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n9-null-buf", rc, BE_CHECK_NULL);
	require(output.state == BE_R2_STATE_FAILED, "n9-state-failed");
	/* Second pool should be scrubbed (it was scrub-safe). */
	require(pool_is_zeroed(pool_buf_protected, BE_SV39X4_POOL_SIZE),
		"n9-safe-pool-scrubbed");
	pass_named("n9");
}

/* N9a: NULL pools pointer */
static void test_n9a_null_pools(void)
{
	static struct be_runtime runtime;
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n9a-r1-setup");
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, (struct be_r2_pool_desc *)0, &output);
	expect_check("n9a-null-pools", rc, BE_CHECK_NULL);
	require(output.state == BE_R2_STATE_FAILED, "n9a-state-failed");
	pass_named("n9a");
}

/* N10: pool base not 16 KiB aligned */
static void test_n10_pool_misaligned(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n10-r1-setup");
	init_pools(pools);
	pools[0].base = POOL_BASE_MANAGEMENT + 0x1000U;
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n10-pool-misaligned", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n10-state-failed");
	require(pool_is_zeroed(pool_buf_management, BE_SV39X4_POOL_SIZE),
		"n10-pool0-scrubbed");
	require(pool_is_zeroed(pool_buf_protected, BE_SV39X4_POOL_SIZE),
		"n10-pool1-scrubbed");
	pass_named("n10");
}

/* N11: pool buf_size undersized */
static void test_n11_undersized(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n11-r1-setup");
	init_pools(pools);
	pools[0].buf_size = BE_SV39X4_POOL_SIZE - 1U;
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n11-undersized", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n11-state-failed");
	/* Only the safe descriptor (pools[1]) should be scrubbed. */
	require(pool_is_zeroed(pool_buf_protected, BE_SV39X4_POOL_SIZE),
		"n11-safe-pool-scrubbed");
	pass_named("n11");
}

/* N12: pool buf_size oversized */
static void test_n12_oversized(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n12-r1-setup");
	init_pools(pools);
	pools[1].buf_size = BE_SV39X4_POOL_SIZE + 1U;
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n12-oversized", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n12-state-failed");
	require(pool_is_zeroed(pool_buf_management, BE_SV39X4_POOL_SIZE),
		"n12-safe-pool-scrubbed");
	pass_named("n12");
}

/* N13: duplicate pool base */
static void test_n13_duplicate_base(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n13-r1-setup");
	init_pools(pools);
	pools[1].base = pools[0].base;
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n13-duplicate-base", rc, BE_CHECK_DUPLICATE_RESOURCE);
	require(output.state == BE_R2_STATE_FAILED, "n13-state-failed");
	pass_named("n13");
}

/* N14: host-buffer start-pointer alias */
static void test_n14_duplicate_buf(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n14-r1-setup");
	init_pools(pools);
	pools[1].buf = pools[0].buf;
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n14-duplicate-buf", rc, BE_CHECK_DUPLICATE_RESOURCE);
	require(output.state == BE_R2_STATE_FAILED, "n14-state-failed");
	pass_named("n14");
}

/* N15: pool base PPN exceeds 44 bits (implies PA > 56 bits).
 * Any PPN exceeding 44 bits necessarily has PA exceeding 56 bits, so the
 * PA-width check in validate_pool_desc fires first returning UNSUPPORTED. */
static void test_n15_ppn_overflow(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n15-r1-setup");
	init_pools(pools);
	/* 1<<56 is both 16K-aligned and exceeds 56-bit PA space. */
	pools[0].base = BE_U64_C(0x100000000000000);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n15-ppn-overflow", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n15-state-failed");
	pass_named("n15");
}

/* N16: pool base + size overflows 64 bits */
static void test_n16_64bit_overflow(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n16-r1-setup");
	init_pools(pools);
	pools[0].base = BE_U64_C(0xFFFFFFFFFFFF0000);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n16-64bit-overflow", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n16-state-failed");
	pass_named("n16");
}

/* N16a: pool base exceeds 56-bit PA space */
static void test_n16a_pa_exceed(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n16a-r1-setup");
	init_pools(pools);
	/* Above 56-bit limit, 16K aligned. */
	pools[0].base = BE_U64_C(0x100000000000000);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n16a-pa-exceed", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n16a-state-failed");
	pass_named("n16a");
}

/* N16b: pool last byte exceeds 56-bit PA space (boundary crossing) */
static void test_n16b_pa_boundary(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n16b-r1-setup");
	init_pools(pools);
	/* base within 56 bits but base+size-1 > mask.
	 * Max PA mask is (1<<56)-1. Pick a base 16K-aligned near the end. */
	pools[0].base = (BE_U64_C(1) << 56) - BE_U64_C(0x4000);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n16b-pa-boundary", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n16b-state-failed");
	pass_named("n16b");
}

/* N16c: one valid descriptor, one invalid (NULL buf) → valid one scrubbed */
static void test_n16c_one_valid_one_null(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n16c-r1-setup");
	init_pools(pools);
	/* Mark pool_buf_management with pattern to verify scrubbing. */
	memset(pool_buf_management, 0xAA, BE_SV39X4_POOL_SIZE);
	pools[1].buf = (be_u8 *)0;
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n16c-one-valid-one-null", rc, BE_CHECK_NULL);
	require(output.state == BE_R2_STATE_FAILED, "n16c-state-failed");
	/* Pool 0 was scrub-safe and should have been zeroed. */
	require(pool_is_zeroed(pool_buf_management, BE_SV39X4_POOL_SIZE),
		"n16c-valid-pool-scrubbed");
	pass_named("n16c");
}

/* N16d: early failure after valid pools → both pools scrubbed */
static void test_n16d_early_failure_scrub(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n16d-r1-setup");
	/* Break the R1 integrity after pool validation will pass. */
	runtime.sealed = 0U;
	init_pools(pools);
	/* Write non-zero pattern to verify scrub. */
	memset(pool_buf_management, 0xBB, BE_SV39X4_POOL_SIZE);
	memset(pool_buf_protected, 0xCC, BE_SV39X4_POOL_SIZE);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n16d-early-failure", rc, BE_CHECK_INTEGRITY);
	require(output.state == BE_R2_STATE_FAILED, "n16d-state-failed");
	require(pool_is_zeroed(pool_buf_management, BE_SV39X4_POOL_SIZE),
		"n16d-pool0-scrubbed");
	require(pool_is_zeroed(pool_buf_protected, BE_SV39X4_POOL_SIZE),
		"n16d-pool1-scrubbed");
	pass_named("n16d");
}

/* ===================================================================
 * NEGATIVE TESTS — root and mapping
 * =================================================================== */

/* N17: enforcement root_count != 2 */
static void test_n17_root_count(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n17-r1-setup");
	runtime.enforcement.root_count = 1U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n17-root-count", rc, BE_CHECK_INCOMPLETE);
	require(output.state == BE_R2_STATE_FAILED, "n17-state-failed");
	pass_named("n17");
}

/* N18: root with mapping_count != 3 */
static void test_n18_mapping_count(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n18-r1-setup");
	runtime.enforcement.roots[0].mapping_count = 2U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n18-mapping-count", rc, BE_CHECK_INCOMPLETE);
	require(output.state == BE_R2_STATE_FAILED, "n18-state-failed");
	pass_named("n18");
}

/* N19: frame ID absent from canonical frames */
static void test_n19_absent_frame(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n19-r1-setup");
	/* Change first mapping's frame_id to something that doesn't exist. */
	runtime.enforcement.roots[0].mappings[0].frame_id = 999U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n19-absent-frame", rc, BE_CHECK_UNDECLARED_MAPPING);
	require(output.state == BE_R2_STATE_FAILED, "n19-state-failed");
	pass_named("n19");
}

/* N20: frame with non-4 KiB size.
 * Changing frame 9 to 0x2000 causes overlap with frame 10 in the tightly
 * packed layout. be_check_canonical (called during R1 revalidation) catches
 * the overlap before the builder's resolve_frame_pa runs. */
static void test_n20_frame_size(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;
	be_size i;

	require(prepare_derived(&runtime), "n20-r1-setup");
	for (i = 0U; i < runtime.canonical.frame_count; ++i) {
		if (runtime.canonical.frames[i].id == 9U) {
			runtime.canonical.frames[i].size = BE_U64_C(0x2000);
			break;
		}
	}
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;

	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n20-frame-size", rc, BE_CHECK_OVERLAPPING_RESOURCE);
	require(output.state == BE_R2_STATE_FAILED, "n20-state-failed");
	pass_named("n20");
}

/* N21: frame with wrong class (ROOT_TABLE as leaf target).
 * Changing a PRIVATE frame to ROOT_TABLE violates be_check_canonical's
 * private-owner check during R1 revalidation. */
static void test_n21_frame_class(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;
	be_size i;

	require(prepare_derived(&runtime), "n21-r1-setup");
	for (i = 0U; i < runtime.canonical.frame_count; ++i) {
		if (runtime.canonical.frames[i].id == 9U) {
			runtime.canonical.frames[i].class = BE_FRAME_ROOT_TABLE;
			break;
		}
	}
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;

	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n21-frame-class", rc, BE_CHECK_PRIVATE_OWNER);
	require(output.state == BE_R2_STATE_FAILED, "n21-state-failed");
	pass_named("n21");
}

/* N22: frame PA not page-aligned */
static void test_n22_frame_alignment(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;
	be_size i;

	require(prepare_derived(&runtime), "n22-r1-setup");
	for (i = 0U; i < runtime.canonical.frame_count; ++i) {
		if (runtime.canonical.frames[i].id == 9U) {
			runtime.canonical.frames[i].base += 0x100U;
			break;
		}
	}
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;

	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n22-frame-alignment", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n22-state-failed");
	pass_named("n22");
}

/* N23: frame PA exceeds 56-bit width */
static void test_n23_frame_pa_width(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;
	be_size i;

	require(prepare_derived(&runtime), "n23-r1-setup");
	for (i = 0U; i < runtime.canonical.frame_count; ++i) {
		if (runtime.canonical.frames[i].id == 9U) {
			runtime.canonical.frames[i].base =
				BE_U64_C(0x200000000000000);
			break;
		}
	}
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;

	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n23-frame-pa-width", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n23-state-failed");
	pass_named("n23");
}

/* N23a: frame PA with 64-bit overflow (base + size wraps).
 * Since the tightly packed fixed layout has no room for a 4K frame whose
 * last byte crosses 56-bit PA space without exceeding PA_MASK on the base
 * itself, we test 64-bit overflow: a page-aligned base near UINT64_MAX. */
static void test_n23a_frame_pa_overflow(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;
	be_size i;

	require(prepare_derived(&runtime), "n23a-r1-setup");
	for (i = 0U; i < runtime.canonical.frame_count; ++i) {
		if (runtime.canonical.frames[i].id == 9U) {
			/* This exceeds PA_MASK and will be caught. */
			runtime.canonical.frames[i].base =
				BE_U64_C(0xFFFFFFFFFFFFF000);
			break;
		}
	}
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;

	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	/* be_check_canonical catches this during R1 revalidation. */
	require(rc != BE_CHECK_OK, "n23a-frame-pa-overflow-rejected");
	require(output.state == BE_R2_STATE_FAILED, "n23a-state-failed");
	pass_named("n23a");
}

/* N24: mapping GPA with bits [63:41] nonzero.
 * be_check_enforcement catches the mutated mapping during R1 revalidation
 * because no canonical authority matches the fabricated GPA. */
static void test_n24_gpa_width(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n24-r1-setup");
	runtime.enforcement.roots[0].mappings[0].gpa =
		BE_U64_C(0x8000000000000);
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n24-gpa-width", rc, BE_CHECK_UNDECLARED_MAPPING);
	require(output.state == BE_R2_STATE_FAILED, "n24-state-failed");
	pass_named("n24");
}

/* N25: mapping GPA not page-aligned */
static void test_n25_gpa_alignment(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n25-r1-setup");
	runtime.enforcement.roots[0].mappings[0].gpa =
		BE_U64_C(0x40000800);
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n25-gpa-alignment", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n25-state-failed");
	pass_named("n25");
}

/* N26: mapping rights == 0.
 * be_check_enforcement catches zero rights during R1 revalidation. */
static void test_n26_zero_rights(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n26-r1-setup");
	runtime.enforcement.roots[0].mappings[0].rights = 0U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n26-zero-rights", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n26-state-failed");
	pass_named("n26");
}

/* N27: mapping rights W without R */
static void test_n27_w_without_r(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n27-r1-setup");
	runtime.enforcement.roots[0].mappings[0].rights = BE_RIGHT_WRITE;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n27-w-without-r", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n27-state-failed");
	pass_named("n27");
}

/* N28: mapping with VPN2 != 1.
 * be_check_enforcement catches the mutated GPA during R1 revalidation
 * because no canonical authority matches. */
static void test_n28_vpn2_wrong(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n28-r1-setup");
	runtime.enforcement.roots[0].mappings[0].gpa = BE_U64_C(0x00000000);
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n28-vpn2-wrong", rc, BE_CHECK_UNDECLARED_MAPPING);
	require(output.state == BE_R2_STATE_FAILED, "n28-state-failed");
	pass_named("n28");
}

/* N29: mapping with VPN1 != 0.
 * be_check_enforcement catches the mutated GPA during R1 revalidation. */
static void test_n29_vpn1_wrong(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n29-r1-setup");
	runtime.enforcement.roots[0].mappings[0].gpa = BE_U64_C(0x40200000);
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n29-vpn1-wrong", rc, BE_CHECK_UNDECLARED_MAPPING);
	require(output.state == BE_R2_STATE_FAILED, "n29-state-failed");
	pass_named("n29");
}

/* N30: duplicate GPA in one root.
 * be_check_enforcement catches the mismatched mapping during R1 revalidation
 * because mapping[1]'s frame_id at the duplicated GPA doesn't match canonical
 * authority. */
static void test_n30_duplicate_gpa(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n30-r1-setup");
	runtime.enforcement.roots[0].mappings[1].gpa =
		runtime.enforcement.roots[0].mappings[0].gpa;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n30-duplicate-gpa", rc, BE_CHECK_UNDECLARED_MAPPING);
	require(output.state == BE_R2_STATE_FAILED, "n30-state-failed");
	pass_named("n30");
}

/* N31: swapped pools (management pool for protected root) */
static void test_n31_swapped_pools(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n31-r1-setup");
	init_pools(pools);
	/* Swap bases. */
	pools[0].base = POOL_BASE_PROTECTED;
	pools[1].base = POOL_BASE_MANAGEMENT;
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n31-swapped-pools", rc, BE_CHECK_BINDING);
	require(output.state == BE_R2_STATE_FAILED, "n31-state-failed");
	pass_named("n31");
}

/* N32: same pool descriptor for both roots */
static void test_n32_same_pool(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n32-r1-setup");
	init_pools(pools);
	pools[1] = pools[0];
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n32-same-pool", rc, BE_CHECK_DUPLICATE_RESOURCE);
	require(output.state == BE_R2_STATE_FAILED, "n32-state-failed");
	pass_named("n32");
}

/* ===================================================================
 * NEGATIVE TESTS — walker structural (post-build corruption)
 *
 * These tests perform a successful build then corrupt pool contents
 * and call the public re-walk to verify detection.
 * =================================================================== */

/* Helper: do a successful build and return the output. */
static int build_success(struct be_runtime *runtime,
			 struct be_r2_pool_desc pools[2],
			 struct be_r2_output *output)
{
	if (!prepare_derived(runtime))
		return 0;
	init_pools(pools);
	memset(output, 0, sizeof(*output));
	return be_r2_build(runtime, pools, output) == BE_CHECK_OK &&
	       output->state == BE_R2_STATE_BUILT;
}

/* N33: corrupted root pointer PPN */
static void test_n33_corrupt_root_ppn(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n33-build");
	/* Corrupt root pointer PPN in first pool. */
	pte = load_le64(pools[0].buf + 8U);
	pte ^= (BE_U64_C(1) << 10); /* Flip bit in PPN. */
	store_le64(pools[0].buf + 8U, pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n33-corrupt-root-ppn", rc, BE_CHECK_INTEGRITY);
	pass_named("n33");
}

/* N34: out-of-pool L1 pointer PPN */
static void test_n34_corrupt_l1_ppn(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n34-build");
	/* Corrupt L1 pointer PPN. */
	pte = load_le64(pools[0].buf + BE_U64_C(0x4000));
	pte ^= (BE_U64_C(1) << 10);
	store_le64(pools[0].buf + BE_U64_C(0x4000), pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n34-corrupt-l1-ppn", rc, BE_CHECK_INTEGRITY);
	pass_named("n34");
}

/* N35: L2 leaf (root entry with V=1 and R set) */
static void test_n35_l2_leaf(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n35-build");
	/* Turn root pointer into a leaf by setting R bit. */
	pte = load_le64(pools[0].buf + 8U);
	pte |= BE_U64_C(0x2); /* Set R. */
	store_le64(pools[0].buf + 8U, pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n35-l2-leaf", rc, BE_CHECK_UNSUPPORTED);
	pass_named("n35");
}

/* N36: L1 leaf (L1 entry with V=1 and R/W/X set) */
static void test_n36_l1_leaf(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n36-build");
	/* Turn L1 pointer into a leaf by setting R bit. */
	pte = load_le64(pools[0].buf + BE_U64_C(0x4000));
	pte |= BE_U64_C(0x2); /* Set R. */
	store_le64(pools[0].buf + BE_U64_C(0x4000), pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n36-l1-leaf", rc, BE_CHECK_UNSUPPORTED);
	pass_named("n36");
}

/* N37: unexpected extra leaf in L0 */
static void test_n37_extra_leaf(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 fake_leaf;

	require(build_success(&runtime, pools, &output), "n37-build");
	/* Insert fake leaf at VPN0=3 (which should be zero). */
	fake_leaf = BE_U64_C(1) | /* V */
		    BE_U64_C(0x2) | /* R */
		    BE_U64_C(0x10) | /* U */
		    BE_U64_C(0x40) | /* A */
		    (BE_U64_C(0x80230) << 10); /* PPN */
	store_le64(pools[0].buf + BE_U64_C(0x5000) + 3U * 8U, fake_leaf);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n37-extra-leaf", rc, BE_CHECK_INTEGRITY);
	pass_named("n37");
}

/* N38: missing leaf (entry zeroed after build) */
static void test_n38_missing_leaf(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(build_success(&runtime, pools, &output), "n38-build");
	/* Zero the first leaf entry (VPN0=0). */
	store_le64(pools[0].buf + BE_U64_C(0x5000), 0U);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n38-missing-leaf", rc, BE_CHECK_INTEGRITY);
	pass_named("n38");
}

/* N39: leaf with wrong PA (PPN modified) */
static void test_n39_wrong_pa(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n39-build");
	/* Modify PPN of first leaf entry. */
	pte = load_le64(pools[0].buf + BE_U64_C(0x5000));
	pte ^= (BE_U64_C(1) << 10);
	store_le64(pools[0].buf + BE_U64_C(0x5000), pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n39-wrong-pa", rc, BE_CHECK_INTEGRITY);
	pass_named("n39");
}

/* N40: leaf with wrong rights */
static void test_n40_wrong_rights(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n40-build");
	/* Toggle X bit on first leaf (originally RW, becomes RWX). */
	pte = load_le64(pools[0].buf + BE_U64_C(0x5000));
	pte |= BE_U64_C(0x8); /* Set X. */
	store_le64(pools[0].buf + BE_U64_C(0x5000), pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n40-wrong-rights", rc, BE_CHECK_INTEGRITY);
	pass_named("n40");
}

/* N41: leaf with U=0 */
static void test_n41_no_u(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n41-build");
	pte = load_le64(pools[0].buf + BE_U64_C(0x5000));
	pte &= ~BE_U64_C(0x10); /* Clear U. */
	store_le64(pools[0].buf + BE_U64_C(0x5000), pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n41-no-u", rc, BE_CHECK_INTEGRITY);
	pass_named("n41");
}

/* N42: leaf with A=0 */
static void test_n42_no_a(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n42-build");
	pte = load_le64(pools[0].buf + BE_U64_C(0x5000));
	pte &= ~BE_U64_C(0x40); /* Clear A. */
	store_le64(pools[0].buf + BE_U64_C(0x5000), pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n42-no-a", rc, BE_CHECK_INTEGRITY);
	pass_named("n42");
}

/* N43: writable leaf with D=0 */
static void test_n43_w_without_d(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n43-build");
	/* First leaf of mgmt root is RW → has D=1. Clear it. */
	pte = load_le64(pools[0].buf + BE_U64_C(0x5000));
	pte &= ~BE_U64_C(0x80); /* Clear D. */
	store_le64(pools[0].buf + BE_U64_C(0x5000), pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n43-w-without-d", rc, BE_CHECK_INTEGRITY);
	pass_named("n43");
}

/* N44: leaf with bits [63:54] nonzero */
static void test_n44_high_bits(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n44-build");
	pte = load_le64(pools[0].buf + BE_U64_C(0x5000));
	pte |= (BE_U64_C(1) << 54); /* Set a forbidden high bit. */
	store_le64(pools[0].buf + BE_U64_C(0x5000), pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n44-high-bits", rc, BE_CHECK_INTEGRITY);
	pass_named("n44");
}

/* N45: leaf with G=1 */
static void test_n45_g_set(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n45-build");
	pte = load_le64(pools[0].buf + BE_U64_C(0x5000));
	pte |= BE_U64_C(0x20); /* Set G. */
	store_le64(pools[0].buf + BE_U64_C(0x5000), pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n45-g-set", rc, BE_CHECK_INTEGRITY);
	pass_named("n45");
}

/* N46: leaf with RSW nonzero */
static void test_n46_rsw_nonzero(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n46-build");
	pte = load_le64(pools[0].buf + BE_U64_C(0x5000));
	pte |= (BE_U64_C(1) << 8); /* Set RSW bit 8. */
	store_le64(pools[0].buf + BE_U64_C(0x5000), pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n46-rsw-nonzero", rc, BE_CHECK_INTEGRITY);
	pass_named("n46");
}

/* N47: nonzero root entry at index != 1 */
static void test_n47_unexpected_root_entry(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(build_success(&runtime, pools, &output), "n47-build");
	/* Write something at root entry index 5. */
	store_le64(pools[0].buf + 5U * 8U, BE_U64_C(0xDEADBEEF));
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n47-unexpected-root-entry", rc, BE_CHECK_INTEGRITY);
	pass_named("n47");
}

/* N48: nonzero L1 entry at index != 0 */
static void test_n48_unexpected_l1_entry(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(build_success(&runtime, pools, &output), "n48-build");
	store_le64(pools[0].buf + BE_U64_C(0x4000) + 3U * 8U,
		   BE_U64_C(0xCAFEBABE));
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n48-unexpected-l1-entry", rc, BE_CHECK_INTEGRITY);
	pass_named("n48");
}

/* N49: nonzero spare page content */
static void test_n49_spare_nonzero(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(build_success(&runtime, pools, &output), "n49-build");
	pools[0].buf[BE_U64_C(0x6000)] = 0x42U;
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n49-spare-nonzero", rc, BE_CHECK_INTEGRITY);
	pass_named("n49");
}

/* N50: malformed pointer PTE (V=1, RWX=0 but U nonzero) */
static void test_n50_malformed_pointer(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 pte;

	require(build_success(&runtime, pools, &output), "n50-build");
	/* Set U on the root pointer. */
	pte = load_le64(pools[0].buf + 8U);
	pte |= BE_U64_C(0x10); /* U. */
	store_le64(pools[0].buf + 8U, pte);
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n50-malformed-pointer", rc, BE_CHECK_INTEGRITY);
	pass_named("n50");
}

/* N51: pointer PTE PPN exceeds 44 bits — not directly testable via pool
 * corruption since PPN comes from pool.base which is fixed. We test via
 * the walker checking the root pointer PPN exceeds 44 bits by putting a
 * huge value in the PPN field. */
static void test_n51_pointer_ppn_overflow(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	be_u64 huge_ppn;

	require(build_success(&runtime, pools, &output), "n51-build");
	/* Replace root pointer PTE with one whose PPN exceeds 44 bits. */
	huge_ppn = (BE_U64_C(1) << 44); /* 45-bit PPN. */
	store_le64(pools[0].buf + 8U, BE_U64_C(1) | (huge_ppn << 10));
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	/* Walker should detect PPN mismatch vs expected page-4 addr. */
	expect_check("n51-pointer-ppn-overflow", rc, BE_CHECK_INTEGRITY);
	pass_named("n51");
}

/* ===================================================================
 * NEGATIVE TESTS — failure isolation
 * =================================================================== */

/* N52: first root build fails → both pools zeroed and both results zeroed */
static void test_n52_first_root_failure(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n52-r1-setup");
	/* Corrupt first root's mapping to fail during build. */
	runtime.enforcement.roots[0].mappings[0].gpa =
		BE_U64_C(0x80000000); /* VPN2=2, will fail geometry. */
	init_pools(pools);
	memset(pool_buf_management, 0xAA, BE_SV39X4_POOL_SIZE);
	memset(pool_buf_protected, 0xBB, BE_SV39X4_POOL_SIZE);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	require(rc != BE_CHECK_OK, "n52-failure-expected");
	require(output.state == BE_R2_STATE_FAILED, "n52-state-failed");
	require(pool_is_zeroed(pool_buf_management, BE_SV39X4_POOL_SIZE),
		"n52-pool0-zeroed");
	require(pool_is_zeroed(pool_buf_protected, BE_SV39X4_POOL_SIZE),
		"n52-pool1-zeroed");
	require(output.results[0].hgatp == 0U, "n52-result0-hgatp-zero");
	require(output.results[0].leaf_count == 0U,
		"n52-result0-leaf-count-zero");
	require(output.results[1].hgatp == 0U, "n52-result1-hgatp-zero");
	require(output.results[1].leaf_count == 0U,
		"n52-result1-leaf-count-zero");
	pass_named("n52");
}

/* N53: second root build fails → both pools zeroed */
static void test_n53_second_root_failure(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n53-r1-setup");
	/* Corrupt second root's mapping to fail. */
	runtime.enforcement.roots[1].mappings[0].gpa =
		BE_U64_C(0x80000000); /* VPN2=2, wrong geometry. */
	init_pools(pools);
	memset(pool_buf_management, 0xCC, BE_SV39X4_POOL_SIZE);
	memset(pool_buf_protected, 0xDD, BE_SV39X4_POOL_SIZE);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	require(rc != BE_CHECK_OK, "n53-failure-expected");
	require(output.state == BE_R2_STATE_FAILED, "n53-state-failed");
	require(pool_is_zeroed(pool_buf_management, BE_SV39X4_POOL_SIZE),
		"n53-pool0-zeroed");
	require(pool_is_zeroed(pool_buf_protected, BE_SV39X4_POOL_SIZE),
		"n53-pool1-zeroed");
	pass_named("n53");
}

/* N54: walker fails on second root → both pools/results zeroed
 * We can't easily force a walker-only failure after build success through
 * the public API because build already walks internally. Instead we corrupt
 * the second pool AFTER build and use the public re-walk. */
static void test_n54_walker_fails_second(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(build_success(&runtime, pools, &output), "n54-build");
	/* Corrupt second pool's spare area. */
	pools[1].buf[BE_U64_C(0x7000)] = 0xFFU;
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("n54-walker-second-fail", rc, BE_CHECK_INTEGRITY);
	/* Re-walk is read-only: it doesn't scrub/change state. Verify it reports error. */
	pass_named("n54");
}

/* N55: after failure, output state is terminal */
static void test_n55_terminal_state(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n55-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	/* Force failure. */
	runtime.sealed = 0U;
	rc = be_r2_build(&runtime, pools, &output);
	require(rc != BE_CHECK_OK, "n55-initial-failure");
	require(output.state == BE_R2_STATE_FAILED, "n55-state-failed");

	/* Attempt retry — should reject due to non-EMPTY state. */
	runtime.sealed = 1U; /* "Fix" runtime — doesn't matter. */
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n55-no-retry", rc, BE_CHECK_INVALID_PHASE);
	require(output.state == BE_R2_STATE_FAILED, "n55-still-failed");
	pass_named("n55");
}

/* N56: after R2 failure, R1 runtime phase remains DERIVED */
static void test_n56_r1_unchanged(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;

	require(prepare_derived(&runtime), "n56-r1-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	/* Force failure. */
	runtime.enforcement.root_count = 0U;
	be_r2_build(&runtime, pools, &output);
	/* Runtime phase should still be DERIVED (R2 doesn't change it). */
	require(runtime.phase == BE_RUNTIME_PHASE_DERIVED, "n56-r1-phase");
	/* check_result was OK before and should be unchanged. */
	require(runtime.check_result == BE_CHECK_OK, "n56-r1-check-result");
	pass_named("n56");
}

/* ===================================================================
 * NEGATIVE TESTS — frozen-profile divergence
 * =================================================================== */

/* N57: non-frozen root IDs (201/202 instead of 101/102) */
static void test_n57_non_frozen_root_ids(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n57-r1-setup");
	runtime.enforcement.roots[0].root_id = 201U;
	runtime.enforcement.roots[1].root_id = 202U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n57-non-frozen-root-ids", rc, BE_CHECK_BINDING);
	require(output.state == BE_R2_STATE_FAILED, "n57-state-failed");
	pass_named("n57");
}

/* N58: non-frozen domain ordering (protected first) */
static void test_n58_domain_ordering(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n58-r1-setup");
	/* Swap domain assignments. */
	runtime.enforcement.roots[0].domain = BE_DOMAIN_PROTECTED;
	runtime.enforcement.roots[1].domain = BE_DOMAIN_MANAGEMENT;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n58-domain-ordering", rc, BE_CHECK_BINDING);
	require(output.state == BE_R2_STATE_FAILED, "n58-state-failed");
	pass_named("n58");
}

/* N59: non-frozen mapping GPA */
static void test_n59_non_frozen_gpa(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n59-r1-setup");
	/* Change a mapping GPA to a valid-geometry but non-frozen address. */
	runtime.enforcement.roots[0].mappings[0].gpa = BE_U64_C(0x40003000);
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	/* This will fail because frozen-profile check catches binding mismatches,
	 * or at least the canonical checker won't match. */
	require(rc != BE_CHECK_OK, "n59-non-frozen-gpa-rejected");
	require(output.state == BE_R2_STATE_FAILED, "n59-state-failed");
	pass_named("n59");
}

/* N60: non-frozen configuration_version */
static void test_n60_wrong_version(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n60-r1-setup");
	runtime.canonical.configuration_version = 99U;
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n60-wrong-version", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n60-state-failed");
	pass_named("n60");
}

/* N61: non-frozen architecture */
static void test_n61_wrong_arch(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n61-r1-setup");
	runtime.canonical.architecture = BE_ARCH_INVALID;
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n61-wrong-arch", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n61-state-failed");
	pass_named("n61");
}

/* N62: non-frozen profile */
static void test_n62_wrong_profile(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n62-r1-setup");
	runtime.canonical.profile = BE_PROFILE_INVALID;
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n62-wrong-profile", rc, BE_CHECK_UNSUPPORTED);
	require(output.state == BE_R2_STATE_FAILED, "n62-state-failed");
	pass_named("n62");
}

/* N64: mapping_count exceeds frozen 3 */
static void test_n64_excess_mappings(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "n64-r1-setup");
	runtime.enforcement.roots[0].mapping_count = 4U;
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	expect_check("n64-excess-mappings", rc, BE_CHECK_INCOMPLETE);
	require(output.state == BE_R2_STATE_FAILED, "n64-state-failed");
	pass_named("n64");
}

/* ===================================================================
 * ADDITIONAL: walk_and_check precondition tests
 * =================================================================== */

static void test_walk_null_runtime(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(build_success(&runtime, pools, &output), "walk-null-rt-build");
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check((const struct be_runtime *)0, pools, &output,
				  leaf_sets);
	expect_check("walk-null-runtime", rc, BE_CHECK_NULL);
	pass_named("walk-null-runtime");
}

static void test_walk_null_pools(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(build_success(&runtime, pools, &output), "walk-null-pools-build");
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, (const struct be_r2_pool_desc *)0,
				  &output, leaf_sets);
	expect_check("walk-null-pools", rc, BE_CHECK_NULL);
	pass_named("walk-null-pools");
}

static void test_walk_null_output(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(build_success(&runtime, pools, &output), "walk-null-out-build");
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools,
				  (const struct be_r2_output *)0, leaf_sets);
	expect_check("walk-null-output", rc, BE_CHECK_NULL);
	pass_named("walk-null-output");
}

static void test_walk_null_leafsets(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(build_success(&runtime, pools, &output), "walk-null-ls-build");
	rc = be_r2_walk_and_check(&runtime, pools, &output,
				  (struct be_r2_leaf_set *)0);
	expect_check("walk-null-leafsets", rc, BE_CHECK_NULL);
	pass_named("walk-null-leafsets");
}

static void test_walk_not_built(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(prepare_derived(&runtime), "walk-not-built-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	/* output state is EMPTY, not BUILT. */
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	expect_check("walk-not-built", rc, BE_CHECK_INVALID_PHASE);
	pass_named("walk-not-built");
}

/* ===================================================================
 * AUDIT TESTS — core-plan mismatch detection
 *
 * These tests exercise specific plan requirements that the core MAY not
 * implement correctly. If any AUDIT test fails, the core contradicts the
 * accepted plan and the todo must be marked blocked.
 * =================================================================== */

/*
 * AUDIT-1: validate_frozen_profile should reject mutated frame tuples.
 * The accepted plan §Frozen fixed-profile validation says "All 13 canonical
 * frames are validated for ID, base, size, class, and owner_mask against the
 * frozen R0 layout constants." If the frozen-profile validation does NOT check
 * individual frame fields, a mutated frame base should pass R2 build (which
 * would be a plan mismatch).
 *
 * We mutate frame 1 (monitor-code) base from 0x80200000 to 0x80200000+0x1000
 * and recompute identity. The R1 revalidation's be_check_canonical may or may
 * not catch this depending on what it validates. If the build succeeds, the
 * frozen-profile check is incomplete per plan.
 */
static void test_audit_frozen_frame_base(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;
	be_size i;

	require(prepare_derived(&runtime), "audit-frame-base-setup");
	/* Mutate frame 1 (monitor-code) base by one page. */
	for (i = 0U; i < runtime.canonical.frame_count; ++i) {
		if (runtime.canonical.frames[i].id == 1U) {
			runtime.canonical.frames[i].base += BE_PAGE_SIZE;
			break;
		}
	}
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;

	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	/* Plan requires rejection (frame base doesn't match frozen layout). */
	require(rc != BE_CHECK_OK, "audit-frozen-frame-base-rejected");
	require(output.state == BE_R2_STATE_FAILED,
		"audit-frozen-frame-base-failed");
	pass_named("audit-frozen-frame-base");
}

/*
 * AUDIT-2: validate_frozen_profile should reject mutated saved-state fields.
 * The plan says frozen profile validation checks saved_state_count and
 * bindings. If we mutate saved_states[0].owner to the wrong domain, the
 * frozen-profile check should reject it.
 */
static void test_audit_frozen_saved_state(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "audit-saved-state-setup");
	/* Swap saved-state owner to wrong domain. */
	runtime.canonical.saved_states[0].owner = BE_DOMAIN_PROTECTED;
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;

	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	/* Plan requires rejection for non-frozen saved-state binding. */
	require(rc != BE_CHECK_OK, "audit-frozen-saved-state-rejected");
	require(output.state == BE_R2_STATE_FAILED,
		"audit-frozen-saved-state-failed");
	pass_named("audit-frozen-saved-state");
}

/*
 * AUDIT-3: validate_frozen_profile should reject mutated channel fields.
 * The plan says channels are part of the frozen profile. If we mutate the
 * channel's source_rights, the frozen-profile check should reject it.
 */
static void test_audit_frozen_channel(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	enum be_check_result rc;

	require(prepare_derived(&runtime), "audit-channel-setup");
	/* Mutate channel source_rights. */
	runtime.canonical.channels[0].source_rights = BE_RIGHT_READ;
	runtime.canonical.configuration_id =
		be_configuration_identity(&runtime.canonical);
	runtime.sealed_identity = runtime.canonical.configuration_id;
	runtime.validated_identity = runtime.canonical.configuration_id;
	runtime.enforcement.configuration_id =
		runtime.canonical.configuration_id;

	init_pools(pools);
	memset(&output, 0, sizeof(output));
	rc = be_r2_build(&runtime, pools, &output);
	/* Plan requires rejection for non-frozen channel. */
	require(rc != BE_CHECK_OK, "audit-frozen-channel-rejected");
	require(output.state == BE_R2_STATE_FAILED,
		"audit-frozen-channel-failed");
	pass_named("audit-frozen-channel");
}

/*
 * AUDIT-4: be_r2_walk_and_check should return UNSUPPORTED (not NULL) for
 * a pool with valid buf but wrong buf_size.
 * The plan §Pool descriptor validation says buf_size != 32768 is UNSUPPORTED.
 * The implementation uses pool_is_scrub_safe which returns false for wrong
 * buf_size and then returns BE_CHECK_NULL, conflating size error with NULL.
 */
static void test_audit_walk_wrong_bufsize(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;

	require(build_success(&runtime, pools, &output), "audit-bufsize-build");
	/* Corrupt buf_size after successful build. */
	pools[0].buf_size = BE_SV39X4_POOL_SIZE - 1U;
	memset(leaf_sets, 0, sizeof(leaf_sets));
	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	/* Plan says UNSUPPORTED for wrong buf_size; implementation may return NULL. */
	require(rc == BE_CHECK_UNSUPPORTED,
		"audit-walk-wrong-bufsize-returns-unsupported");
	pass_named("audit-walk-wrong-bufsize");
}

/*
 * AUDIT-5: be_r2_walk_and_check should zero leaf_sets before returning
 * INVALID_PHASE when output is not BUILT.
 * The plan header says leaf_sets are "zeroed at entry" by the implementation.
 * If leaf_sets are not zeroed before returning, caller sees stale data.
 */
static void test_audit_walk_leafsets_zeroed_on_phase_error(void)
{
	static struct be_runtime runtime;
	struct be_r2_pool_desc pools[2];
	struct be_r2_output output;
	struct be_r2_leaf_set leaf_sets[2];
	enum be_check_result rc;
	int zeroed;

	require(prepare_derived(&runtime), "audit-leafzero-setup");
	init_pools(pools);
	memset(&output, 0, sizeof(output));
	/* output.state is EMPTY (not BUILT). */

	/* Fill leaf_sets with a nonzero pattern. */
	memset(leaf_sets, 0xAA, sizeof(leaf_sets));

	rc = be_r2_walk_and_check(&runtime, pools, &output, leaf_sets);
	require(rc == BE_CHECK_INVALID_PHASE, "audit-leafzero-phase-error");

	/* Plan requires leaf_sets zeroed at entry (before any return). */
	{
		static const struct be_r2_leaf_set zero_set;

		zeroed = (memcmp(&leaf_sets[0], &zero_set, sizeof(zero_set)) == 0 &&
			  memcmp(&leaf_sets[1], &zero_set, sizeof(zero_set)) == 0);
	}
	require(zeroed, "audit-walk-leafsets-zeroed-before-phase-return");
	pass_named("audit-walk-leafsets-zeroed");
}


int main(void)
{
	printf("BE_R2_CHECK: starting R2 Sv39x4 backend host tests\n");

	/* Positive tests. */
	test_p1_full_build();
	test_p2_hgatp_management();
	test_p3_hgatp_protected();
	test_p4_leaf_counts();
	test_p7_pool_structure();
	test_p8_root_unused();
	test_p9_l1_unused();
	test_p10_spare_pages();
	test_p11_rewalk();

	/* R1 integrity adversarial. */
	test_n1_null_runtime();
	test_n2_wrong_phase_sealed();
	test_n3_wrong_phase_empty();
	test_n4_identity_mismatch();
	test_n5_enforcement_id_mismatch();
	test_n6_not_sealed();
	test_n7_output_already_built();
	test_n8_output_already_failed();
	test_n8a_null_output();
	test_n8b_validated_identity_zero();
	test_n8c_sealed_identity_zero();
	test_n8d_identity_mismatch();
	test_n8e_sealed_ne_canonical();
	test_n8f_recompute_mismatch();
	test_n8g_check_result_bad();

	/* Pool descriptor adversarial. */
	test_n9_null_buf();
	test_n9a_null_pools();
	test_n10_pool_misaligned();
	test_n11_undersized();
	test_n12_oversized();
	test_n13_duplicate_base();
	test_n14_duplicate_buf();
	test_n15_ppn_overflow();
	test_n16_64bit_overflow();
	test_n16a_pa_exceed();
	test_n16b_pa_boundary();
	test_n16c_one_valid_one_null();
	test_n16d_early_failure_scrub();

	/* Root and mapping adversarial. */
	test_n17_root_count();
	test_n18_mapping_count();
	test_n19_absent_frame();
	test_n20_frame_size();
	test_n21_frame_class();
	test_n22_frame_alignment();
	test_n23_frame_pa_width();
	test_n23a_frame_pa_overflow();
	test_n24_gpa_width();
	test_n25_gpa_alignment();
	test_n26_zero_rights();
	test_n27_w_without_r();
	test_n28_vpn2_wrong();
	test_n29_vpn1_wrong();
	test_n30_duplicate_gpa();
	test_n31_swapped_pools();
	test_n32_same_pool();

	/* Walker structural adversarial. */
	test_n33_corrupt_root_ppn();
	test_n34_corrupt_l1_ppn();
	test_n35_l2_leaf();
	test_n36_l1_leaf();
	test_n37_extra_leaf();
	test_n38_missing_leaf();
	test_n39_wrong_pa();
	test_n40_wrong_rights();
	test_n41_no_u();
	test_n42_no_a();
	test_n43_w_without_d();
	test_n44_high_bits();
	test_n45_g_set();
	test_n46_rsw_nonzero();
	test_n47_unexpected_root_entry();
	test_n48_unexpected_l1_entry();
	test_n49_spare_nonzero();
	test_n50_malformed_pointer();
	test_n51_pointer_ppn_overflow();

	/* Failure isolation. */
	test_n52_first_root_failure();
	test_n53_second_root_failure();
	test_n54_walker_fails_second();
	test_n55_terminal_state();
	test_n56_r1_unchanged();

	/* Frozen-profile divergence. */
	test_n57_non_frozen_root_ids();
	test_n58_domain_ordering();
	test_n59_non_frozen_gpa();
	test_n60_wrong_version();
	test_n61_wrong_arch();
	test_n62_wrong_profile();
	test_n64_excess_mappings();

	/* walk_and_check precondition tests. */
	test_walk_null_runtime();
	test_walk_null_pools();
	test_walk_null_output();
	test_walk_null_leafsets();
	test_walk_not_built();

	/* Audit tests — core-plan mismatch detection. */
	test_audit_frozen_frame_base();
	test_audit_frozen_saved_state();
	test_audit_frozen_channel();
	test_audit_walk_wrong_bufsize();
	test_audit_walk_leafsets_zeroed_on_phase_error();

	printf("BE_R2_CHECK: %d tests, %d failures\n", test_count, failures);
	if (failures > 0) {
		printf("BE_R2_CHECK: FAIL\n");
		return 1;
	}
	printf("BE_R2_CHECK: PASS\n");
	return 0;
}
