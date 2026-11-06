// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: deterministic host-side unit and adversarial checker for the
 *          accepted R1 non-privileged pure-C mechanism. It exercises the full
 *          thirteen-resource fixed profile through copy, validation,
 *          canonicalization, sealing, derivation, reporting, and terminal
 *          fail-closed phase logic.
 * Trust:   test tool only. It grants no runtime authority, links no image,
 *          executes no privileged code, and makes no QEMU or hardware claim.
 * Scope:   R1 host evidence only. It checks offline fixed fixtures and exact
 *          rejection classes where the mechanism contract makes them specific.
 */
#include <stdio.h>
#include <string.h>

#include <be/manifest.h>
#include <be/r1-config.h>
#include <be/state.h>

#define BE_GPA_MANAGEMENT_PRIVATE	BE_U64_C(0x40000000)
#define BE_GPA_PROTECTED_PRIVATE	BE_U64_C(0x40001000)
#define BE_GPA_SHARED			BE_U64_C(0x40002000)
#define BE_GPA_GUEST_CODE_MANAGEMENT	BE_U64_C(0x40010000)
#define BE_GPA_GUEST_CODE_PROTECTED	BE_U64_C(0x40011000)

#define BE_ROOT_MANAGEMENT		101U
#define BE_ROOT_PROTECTED		102U

static int failures;

static void fail_named(const char *name)
{
	printf("BE_R1_CHECK: FAIL %s\n", name);
	++failures;
}

static void fail_check(const char *name, enum be_check_result expected,
		       enum be_check_result actual)
{
	printf("BE_R1_CHECK: FAIL %s expected=%s actual=%s\n", name,
	       be_check_result_name(expected),
	       be_check_result_name(actual));
	++failures;
}

static void fail_runtime(const char *name, enum be_runtime_result expected,
			 enum be_runtime_result actual)
{
	printf("BE_R1_CHECK: FAIL %s expected=%u actual=%u\n", name,
	       (unsigned int)expected, (unsigned int)actual);
	++failures;
}

static void require_named(int condition, const char *name)
{
	if (!condition)
		fail_named(name);
}

static void expect_check(const char *name, enum be_check_result actual,
			 enum be_check_result expected)
{
	if (actual != expected)
		fail_check(name, expected, actual);
}

static void expect_runtime(const char *name, enum be_runtime_result actual,
			   enum be_runtime_result expected)
{
	if (actual != expected)
		fail_runtime(name, expected, actual);
}

static const char *phase_name(enum be_runtime_phase phase)
{
	switch (phase) {
	case BE_RUNTIME_PHASE_EMPTY:
		return "empty";
	case BE_RUNTIME_PHASE_INVENTORY_COPIED:
		return "inventory-copied";
	case BE_RUNTIME_PHASE_PROPOSAL_COPIED:
		return "proposal-copied";
	case BE_RUNTIME_PHASE_VALIDATED:
		return "validated";
	case BE_RUNTIME_PHASE_SEALED:
		return "sealed";
	case BE_RUNTIME_PHASE_DERIVED:
		return "derived";
	case BE_RUNTIME_PHASE_FAILED:
		return "failed";
	default:
		return "invalid";
	}
}

static void expect_phase(const char *name, enum be_runtime_phase actual,
			 enum be_runtime_phase expected)
{
	if (actual != expected) {
		printf("BE_R1_CHECK: FAIL %s expected=%s actual=%s\n", name,
		       phase_name(expected), phase_name(actual));
		++failures;
	}
}

/*
 * Start an independent host-test scenario with fresh local storage. This is
 * not an R1 state-machine operation and is never used to recover a scenario
 * after it enters BE_RUNTIME_PHASE_FAILED.
 */
static void begin_test_scenario(struct be_runtime *runtime)
{
	*runtime = (struct be_runtime)BE_RUNTIME_INITIALIZER;
}

static int canonical_is_zero(const struct be_canonical_state *canonical)
{
	static const struct be_canonical_state zero;

	return memcmp(canonical, &zero, sizeof(*canonical)) == 0;
}

static int enforcement_is_zero(const struct be_enforcement_state *enforcement)
{
	static const struct be_enforcement_state zero;

	return memcmp(enforcement, &zero, sizeof(*enforcement)) == 0;
}

static int report_is_zero(const struct be_runtime_report *report)
{
	static const struct be_runtime_report zero;

	return memcmp(report, &zero, sizeof(*report)) == 0;
}

static struct be_platform_inventory mutable_inventory(void)
{
	return *be_r1_inventory();
}

static struct be_proposal mutable_proposal(void)
{
	return *be_r1_proposal();
}

static void reidentify(struct be_canonical_state *canonical)
{
	canonical->configuration_id = be_configuration_identity(canonical);
}

static struct be_resource_desc *
find_inventory_resource(struct be_platform_inventory *inventory, be_u32 id)
{
	be_size index;

	for (index = 0U; index < inventory->resource_count; ++index) {
		if (inventory->resources[index].id == id)
			return &inventory->resources[index];
	}
	return (struct be_resource_desc *)0;
}

static struct be_domain_request *find_proposal_domain(struct be_proposal *proposal,
						      enum be_domain_id id)
{
	be_size index;

	for (index = 0U; index < proposal->domain_count; ++index) {
		if (proposal->domains[index].id == id)
			return &proposal->domains[index];
	}
	return (struct be_domain_request *)0;
}

static struct be_resource_request *
find_proposal_resource(struct be_proposal *proposal, be_u32 resource_id)
{
	be_size index;

	for (index = 0U; index < proposal->resource_count; ++index) {
		if (proposal->resources[index].resource_id == resource_id)
			return &proposal->resources[index];
	}
	return (struct be_resource_request *)0;
}

static struct be_authority_request *
find_proposal_authority(struct be_proposal *proposal, enum be_domain_id domain,
			be_u64 gpa)
{
	be_size index;

	for (index = 0U; index < proposal->authority_count; ++index) {
		if (proposal->authorities[index].domain == domain &&
		    proposal->authorities[index].gpa == gpa)
			return &proposal->authorities[index];
	}
	return (struct be_authority_request *)0;
}

static const struct be_domain_desc *
find_domain(const struct be_canonical_state *canonical, enum be_domain_id id)
{
	be_size index;

	for (index = 0U; index < canonical->domain_count; ++index) {
		if (canonical->domains[index].id == id)
			return &canonical->domains[index];
	}
	return (const struct be_domain_desc *)0;
}

static const struct be_frame_desc *
find_frame(const struct be_canonical_state *canonical, be_u32 id)
{
	be_size index;

	for (index = 0U; index < canonical->frame_count; ++index) {
		if (canonical->frames[index].id == id)
			return &canonical->frames[index];
	}
	return (const struct be_frame_desc *)0;
}

static const struct be_authority_desc *
find_authority(const struct be_canonical_state *canonical,
	       enum be_domain_id domain, be_u64 gpa)
{
	be_size index;

	for (index = 0U; index < canonical->authority_count; ++index) {
		if (canonical->authorities[index].domain == domain &&
		    canonical->authorities[index].gpa == gpa)
			return &canonical->authorities[index];
	}
	return (const struct be_authority_desc *)0;
}

static const struct be_root_image *
find_root(const struct be_enforcement_state *enforcement,
	  enum be_domain_id domain)
{
	be_size index;

	for (index = 0U; index < enforcement->root_count; ++index) {
		if (enforcement->roots[index].domain == domain)
			return &enforcement->roots[index];
	}
	return (const struct be_root_image *)0;
}

static int root_has_mapping(const struct be_root_image *root, be_u64 gpa,
			    be_u32 frame_id, be_u32 rights)
{
	be_size index;

	for (index = 0U; index < root->mapping_count; ++index) {
		if (root->mappings[index].gpa == gpa &&
		    root->mappings[index].frame_id == frame_id &&
		    root->mappings[index].rights == rights)
			return 1;
	}
	return 0;
}

static void expect_proposal_failure(const char *name,
				    const struct be_platform_inventory *inventory,
				    const struct be_proposal *proposal,
				    enum be_check_result expected)
{
	struct be_canonical_state canonical;
	enum be_check_result actual;

	memset(&canonical, 0x5a, sizeof(canonical));
	actual = be_canonicalize(inventory, proposal, &canonical);
	expect_check(name, actual, expected);
	if (expected != BE_CHECK_OK)
		require_named(canonical_is_zero(&canonical),
			      "proposal-failure-zero-publication");
}

static void expect_derive_failure(const char *name,
				  const struct be_canonical_state *canonical,
				  enum be_check_result expected)
{
	struct be_enforcement_state enforcement;
	enum be_check_result actual;

	memset(&enforcement, 0x5a, sizeof(enforcement));
	actual = be_derive_enforcement(canonical, &enforcement);
	expect_check(name, actual, expected);
	if (expected != BE_CHECK_OK)
		require_named(enforcement_is_zero(&enforcement),
			      "derive-failure-zero-publication");
}

static int prepare_validated(struct be_runtime *runtime,
			     const struct be_proposal *proposal,
			     const char *tag)
{
	begin_test_scenario(runtime);
	expect_phase("initialize-empty", runtime->phase,
		     BE_RUNTIME_PHASE_EMPTY);
	expect_runtime(tag, be_runtime_copy_inventory(runtime, be_r1_inventory()),
		       BE_RUNTIME_OK);
	if (runtime->phase != BE_RUNTIME_PHASE_INVENTORY_COPIED)
		return 0;
	expect_runtime(tag, be_runtime_copy_proposal(runtime, proposal),
		       BE_RUNTIME_OK);
	if (runtime->phase != BE_RUNTIME_PHASE_PROPOSAL_COPIED)
		return 0;
	expect_runtime(tag, be_runtime_validate(runtime), BE_RUNTIME_OK);
	return runtime->phase == BE_RUNTIME_PHASE_VALIDATED;
}

static int prepare_derived(struct be_runtime *runtime,
			   const struct be_proposal *proposal,
			   const char *tag)
{
	if (!prepare_validated(runtime, proposal, tag))
		return 0;
	expect_runtime(tag, be_runtime_seal(runtime), BE_RUNTIME_OK);
	if (runtime->phase != BE_RUNTIME_PHASE_SEALED)
		return 0;
	expect_runtime(tag, be_runtime_derive(runtime), BE_RUNTIME_OK);
	return runtime->phase == BE_RUNTIME_PHASE_DERIVED;
}

static void expect_failed_state_sticky(struct be_runtime *runtime,
				       const char *prefix)
{
	struct be_runtime_report report;

	memset(&report, 0xa5, sizeof(report));
	expect_runtime(prefix,
		       be_runtime_copy_inventory(runtime, be_r1_inventory()),
		       BE_RUNTIME_FAILED);
	expect_runtime(prefix,
		       be_runtime_copy_proposal(runtime, be_r1_proposal()),
		       BE_RUNTIME_FAILED);
	expect_runtime(prefix, be_runtime_validate(runtime), BE_RUNTIME_FAILED);
	expect_runtime(prefix, be_runtime_seal(runtime), BE_RUNTIME_FAILED);
	expect_runtime(prefix, be_runtime_derive(runtime), BE_RUNTIME_FAILED);
	expect_runtime(prefix, be_runtime_report(runtime, &report),
		       BE_RUNTIME_FAILED);
	require_named(report_is_zero(&report), "failed-state-report-zero");
	expect_phase("failed-state-sticky-phase", runtime->phase,
		     BE_RUNTIME_PHASE_FAILED);
}

static void shuffle_equivalent_proposal(struct be_proposal *proposal)
{
	struct be_resource_request resources[BE_MAX_RESOURCES];
	struct be_authority_request authorities[BE_MAX_AUTHORITIES];
	struct be_domain_request domains[BE_MAX_DOMAINS];

	memcpy(resources, proposal->resources, sizeof(resources));
	memcpy(authorities, proposal->authorities, sizeof(authorities));
	memcpy(domains, proposal->domains, sizeof(domains));

	proposal->proposal_id = BE_U64_C(0x52010000000000f1);
	proposal->source_vocabulary = BE_VOCABULARY_B;

	proposal->domains[0] = domains[1];
	proposal->domains[1] = domains[0];

	proposal->resources[0] = resources[12];
	proposal->resources[1] = resources[8];
	proposal->resources[2] = resources[4];
	proposal->resources[3] = resources[0];
	proposal->resources[4] = resources[10];
	proposal->resources[5] = resources[6];
	proposal->resources[6] = resources[2];
	proposal->resources[7] = resources[11];
	proposal->resources[8] = resources[7];
	proposal->resources[9] = resources[3];
	proposal->resources[10] = resources[9];
	proposal->resources[11] = resources[5];
	proposal->resources[12] = resources[1];

	proposal->authorities[0] = authorities[5];
	proposal->authorities[1] = authorities[2];
	proposal->authorities[2] = authorities[0];
	proposal->authorities[3] = authorities[4];
	proposal->authorities[4] = authorities[1];
	proposal->authorities[5] = authorities[3];
}

static void test_positive_flow_and_report(void)
{
	struct be_runtime runtime;
	struct be_runtime_report report;
	static const struct be_runtime_report zero_report;
	const struct be_domain_desc *management_domain;
	const struct be_domain_desc *protected_domain;
	const struct be_frame_desc *frame;
	const struct be_authority_desc *authority;
	const struct be_root_image *root;

	if (!prepare_derived(&runtime, be_r1_proposal(), "positive-flow"))
		return;

	expect_phase("positive-derived-phase", runtime.phase,
		     BE_RUNTIME_PHASE_DERIVED);
	expect_check("positive-runtime-check-result", runtime.check_result,
		     BE_CHECK_OK);
	expect_check("positive-canonical-recheck",
		     be_check_canonical(&runtime.canonical), BE_CHECK_OK);
	expect_check("positive-enforcement-recheck",
		     be_check_enforcement(&runtime.canonical,
					  &runtime.enforcement),
		     BE_CHECK_OK);

	require_named(runtime.validated_identity != 0U,
		      "positive-validated-identity-nonzero");
	require_named(runtime.validated_identity ==
			      runtime.canonical.configuration_id,
		      "positive-validated-identity-match");
	require_named(runtime.sealed_identity == runtime.validated_identity,
		      "positive-sealed-identity-match");
	require_named(runtime.enforcement.configuration_id ==
			      runtime.sealed_identity,
		      "positive-derived-identity-match");
	require_named(runtime.sealed != 0U, "positive-sealed-flag");

	require_named(runtime.inventory.resource_count == 13U,
		      "positive-inventory-count");
	require_named(runtime.proposal.resource_count == 13U,
		      "positive-proposal-count");
	require_named(runtime.canonical.frame_count == 13U,
		      "positive-canonical-frame-count");
	require_named(runtime.canonical.authority_count == 6U,
		      "positive-canonical-authority-count");
	require_named(runtime.canonical.saved_state_count == 2U,
		      "positive-canonical-saved-state-count");
	require_named(runtime.canonical.channel_count == 1U,
		      "positive-canonical-channel-count");
	require_named(runtime.enforcement.root_count == 2U,
		      "positive-derived-root-count");
	require_named(runtime.enforcement.roots[0].mapping_count == 3U,
		      "positive-derived-root0-mapping-count");
	require_named(runtime.enforcement.roots[1].mapping_count == 3U,
		      "positive-derived-root1-mapping-count");

	management_domain =
		find_domain(&runtime.canonical, BE_DOMAIN_MANAGEMENT);
	protected_domain =
		find_domain(&runtime.canonical, BE_DOMAIN_PROTECTED);
	require_named(management_domain != (const struct be_domain_desc *)0,
		      "positive-management-domain-present");
	require_named(protected_domain != (const struct be_domain_desc *)0,
		      "positive-protected-domain-present");
	if (management_domain != (const struct be_domain_desc *)0) {
		require_named(management_domain->root_id == BE_ROOT_MANAGEMENT,
			      "positive-management-root-id");
		require_named(management_domain->root_table_frame == 3U,
			      "positive-management-root-frame");
		require_named(management_domain->trusted_stack_frame == 5U,
			      "positive-management-stack-frame");
		require_named(management_domain->saved_state_id == 1U,
			      "positive-management-saved-id");
		require_named(management_domain->saved_state_frame == 7U,
			      "positive-management-saved-frame");
	}
	if (protected_domain != (const struct be_domain_desc *)0) {
		require_named(protected_domain->root_id == BE_ROOT_PROTECTED,
			      "positive-protected-root-id");
		require_named(protected_domain->root_table_frame == 4U,
			      "positive-protected-root-frame");
		require_named(protected_domain->trusted_stack_frame == 6U,
			      "positive-protected-stack-frame");
		require_named(protected_domain->saved_state_id == 2U,
			      "positive-protected-saved-id");
		require_named(protected_domain->saved_state_frame == 8U,
			      "positive-protected-saved-frame");
	}

	frame = find_frame(&runtime.canonical, 9U);
	require_named(frame != (const struct be_frame_desc *)0,
		      "positive-management-private-frame-present");
	if (frame != (const struct be_frame_desc *)0)
		require_named(frame->owner_mask == BE_OWNER_MANAGEMENT,
			      "positive-management-private-owner");

	frame = find_frame(&runtime.canonical, 10U);
	require_named(frame != (const struct be_frame_desc *)0,
		      "positive-protected-private-frame-present");
	if (frame != (const struct be_frame_desc *)0)
		require_named(frame->owner_mask == BE_OWNER_PROTECTED,
			      "positive-protected-private-owner");

	frame = find_frame(&runtime.canonical, 11U);
	require_named(frame != (const struct be_frame_desc *)0,
		      "positive-shared-frame-present");
	if (frame != (const struct be_frame_desc *)0)
		require_named(frame->owner_mask == 0U, "positive-shared-owner");

	frame = find_frame(&runtime.canonical, 12U);
	require_named(frame != (const struct be_frame_desc *)0,
		      "positive-management-code-frame-present");
	if (frame != (const struct be_frame_desc *)0) {
		require_named(frame->class == BE_FRAME_GUEST_CODE,
			      "positive-management-code-class");
		require_named(frame->owner_mask == BE_OWNER_MANAGEMENT,
			      "positive-management-code-owner");
	}

	frame = find_frame(&runtime.canonical, 13U);
	require_named(frame != (const struct be_frame_desc *)0,
		      "positive-protected-code-frame-present");
	if (frame != (const struct be_frame_desc *)0) {
		require_named(frame->class == BE_FRAME_GUEST_CODE,
			      "positive-protected-code-class");
		require_named(frame->owner_mask == BE_OWNER_PROTECTED,
			      "positive-protected-code-owner");
	}

	authority = find_authority(&runtime.canonical, BE_DOMAIN_MANAGEMENT,
				   BE_GPA_MANAGEMENT_PRIVATE);
	require_named(authority != (const struct be_authority_desc *)0,
		      "positive-management-private-authority-present");
	if (authority != (const struct be_authority_desc *)0)
		require_named(authority->rights ==
				      (BE_RIGHT_READ | BE_RIGHT_WRITE),
			      "positive-management-private-rights");

	authority = find_authority(&runtime.canonical, BE_DOMAIN_PROTECTED,
				   BE_GPA_PROTECTED_PRIVATE);
	require_named(authority != (const struct be_authority_desc *)0,
		      "positive-protected-private-authority-present");
	if (authority != (const struct be_authority_desc *)0)
		require_named(authority->rights ==
				      (BE_RIGHT_READ | BE_RIGHT_WRITE),
			      "positive-protected-private-rights");

	authority = find_authority(&runtime.canonical, BE_DOMAIN_MANAGEMENT,
				   BE_GPA_SHARED);
	require_named(authority != (const struct be_authority_desc *)0,
		      "positive-management-shared-authority-present");
	if (authority != (const struct be_authority_desc *)0)
		require_named(authority->rights ==
				      (BE_RIGHT_READ | BE_RIGHT_WRITE),
			      "positive-management-shared-rights");

	authority = find_authority(&runtime.canonical, BE_DOMAIN_PROTECTED,
				   BE_GPA_SHARED);
	require_named(authority != (const struct be_authority_desc *)0,
		      "positive-protected-shared-authority-present");
	if (authority != (const struct be_authority_desc *)0)
		require_named(authority->rights == BE_RIGHT_READ,
			      "positive-protected-shared-rights");

	authority = find_authority(&runtime.canonical, BE_DOMAIN_MANAGEMENT,
				   BE_GPA_GUEST_CODE_MANAGEMENT);
	require_named(authority != (const struct be_authority_desc *)0,
		      "positive-management-code-authority-present");
	if (authority != (const struct be_authority_desc *)0)
		require_named(authority->rights ==
				      (BE_RIGHT_READ | BE_RIGHT_EXECUTE),
			      "positive-management-code-rights");

	authority = find_authority(&runtime.canonical, BE_DOMAIN_PROTECTED,
				   BE_GPA_GUEST_CODE_PROTECTED);
	require_named(authority != (const struct be_authority_desc *)0,
		      "positive-protected-code-authority-present");
	if (authority != (const struct be_authority_desc *)0)
		require_named(authority->rights ==
				      (BE_RIGHT_READ | BE_RIGHT_EXECUTE),
			      "positive-protected-code-rights");

	root = find_root(&runtime.enforcement, BE_DOMAIN_MANAGEMENT);
	require_named(root != (const struct be_root_image *)0,
		      "positive-management-root-present");
	if (root != (const struct be_root_image *)0) {
		require_named(root->root_id == BE_ROOT_MANAGEMENT,
			      "positive-management-root-derived-id");
		require_named(root->root_table_frame == 3U,
			      "positive-management-root-derived-frame");
		require_named(root_has_mapping(root, BE_GPA_MANAGEMENT_PRIVATE,
					       9U,
					       BE_RIGHT_READ |
						       BE_RIGHT_WRITE),
			      "positive-management-root-private-map");
		require_named(root_has_mapping(root, BE_GPA_SHARED, 11U,
					       BE_RIGHT_READ |
						       BE_RIGHT_WRITE),
			      "positive-management-root-shared-map");
		require_named(root_has_mapping(root,
					       BE_GPA_GUEST_CODE_MANAGEMENT,
					       12U,
					       BE_RIGHT_READ |
						       BE_RIGHT_EXECUTE),
			      "positive-management-root-code-map");
	}

	root = find_root(&runtime.enforcement, BE_DOMAIN_PROTECTED);
	require_named(root != (const struct be_root_image *)0,
		      "positive-protected-root-present");
	if (root != (const struct be_root_image *)0) {
		require_named(root->root_id == BE_ROOT_PROTECTED,
			      "positive-protected-root-derived-id");
		require_named(root->root_table_frame == 4U,
			      "positive-protected-root-derived-frame");
		require_named(root_has_mapping(root, BE_GPA_PROTECTED_PRIVATE,
					       10U,
					       BE_RIGHT_READ |
						       BE_RIGHT_WRITE),
			      "positive-protected-root-private-map");
		require_named(root_has_mapping(root, BE_GPA_SHARED, 11U,
					       BE_RIGHT_READ),
			      "positive-protected-root-shared-map");
		require_named(root_has_mapping(root,
					       BE_GPA_GUEST_CODE_PROTECTED,
					       13U,
					       BE_RIGHT_READ |
						       BE_RIGHT_EXECUTE),
			      "positive-protected-root-code-map");
	}

	memset(&report, 0, sizeof(report));
	expect_runtime("positive-report", be_runtime_report(&runtime, &report),
		       BE_RUNTIME_OK);
	require_named(memcmp(&report, &zero_report, sizeof(report)) != 0,
		      "positive-report-summary-nonzero");
	require_named(report.schema_version == BE_R1_REPORT_SCHEMA_VERSION,
		      "positive-report-schema-version");
	require_named(report.phase == BE_RUNTIME_PHASE_DERIVED,
		      "positive-report-phase");
	require_named(report.check_result == BE_CHECK_OK,
		      "positive-report-check-result");
	require_named(report.configuration_id ==
			      runtime.canonical.configuration_id,
		      "positive-report-configuration-id");
	require_named(report.frame_count == 13U,
		      "positive-report-frame-count");
	require_named(report.authority_count == 6U,
		      "positive-report-authority-count");
	require_named(report.root_count == 2U,
		      "positive-report-root-count");
	require_named(report.mapping_count == 6U,
		      "positive-report-mapping-count");
	require_named(report.sealed != 0U, "positive-report-sealed");
}

static void test_source_order_vocabulary_and_proposal_id_equivalence(void)
{
	struct be_proposal shuffled = mutable_proposal();
	struct be_runtime source_a;
	struct be_runtime source_b;

	shuffle_equivalent_proposal(&shuffled);
	if (!prepare_derived(&source_a, be_r1_proposal(), "source-a-derived"))
		return;
	if (!prepare_derived(&source_b, &shuffled, "source-b-derived"))
		return;

	require_named(source_a.canonical.configuration_id != 0U,
		      "source-equivalence-identity-nonzero");
	require_named(source_a.canonical.configuration_id ==
			      source_b.canonical.configuration_id,
		      "source-equivalence-identity-match");
	require_named(memcmp(&source_a.canonical, &source_b.canonical,
				     sizeof(source_a.canonical)) == 0,
		      "source-equivalence-canonical-bytes");
	require_named(memcmp(&source_a.enforcement, &source_b.enforcement,
				     sizeof(source_a.enforcement)) == 0,
		      "source-equivalence-enforcement-bytes");
}

static void test_null_and_wrong_phase_behaviour(void)
{
	struct be_runtime runtime;
	struct be_runtime_report report;

	expect_runtime("null-copy-inventory",
		       be_runtime_copy_inventory((struct be_runtime *)0,
						 be_r1_inventory()),
		       BE_RUNTIME_FAILED);
	expect_runtime("null-copy-proposal",
		       be_runtime_copy_proposal((struct be_runtime *)0,
						be_r1_proposal()),
		       BE_RUNTIME_FAILED);
	expect_runtime("null-validate",
		       be_runtime_validate((struct be_runtime *)0),
		       BE_RUNTIME_FAILED);
	expect_runtime("null-seal", be_runtime_seal((struct be_runtime *)0),
		       BE_RUNTIME_FAILED);
	expect_runtime("null-derive", be_runtime_derive((struct be_runtime *)0),
		       BE_RUNTIME_FAILED);
	expect_runtime("null-report-state",
		       be_runtime_report((struct be_runtime *)0, &report),
		       BE_RUNTIME_FAILED);

	begin_test_scenario(&runtime);
	expect_runtime("null-inventory-input",
		       be_runtime_copy_inventory(&runtime,
						 (const struct be_platform_inventory *)0),
		       BE_RUNTIME_FAILED);
	expect_phase("null-inventory-input-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	expect_check("null-inventory-input-check", runtime.check_result,
		     BE_CHECK_NULL);

	begin_test_scenario(&runtime);
	expect_runtime("wrong-phase-copy-proposal",
		       be_runtime_copy_proposal(&runtime, be_r1_proposal()),
		       BE_RUNTIME_FAILED);
	expect_phase("wrong-phase-copy-proposal-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	expect_check("wrong-phase-copy-proposal-check", runtime.check_result,
		     BE_CHECK_INVALID_PHASE);

	begin_test_scenario(&runtime);
	expect_runtime("wrong-phase-validate",
		       be_runtime_validate(&runtime), BE_RUNTIME_FAILED);
	expect_phase("wrong-phase-validate-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	expect_check("wrong-phase-validate-check", runtime.check_result,
		     BE_CHECK_INVALID_PHASE);

	begin_test_scenario(&runtime);
	expect_runtime("wrong-phase-seal", be_runtime_seal(&runtime),
		       BE_RUNTIME_FAILED);
	expect_phase("wrong-phase-seal-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	expect_check("wrong-phase-seal-check", runtime.check_result,
		     BE_CHECK_INVALID_PHASE);

	begin_test_scenario(&runtime);
	expect_runtime("wrong-phase-derive", be_runtime_derive(&runtime),
		       BE_RUNTIME_FAILED);
	expect_phase("wrong-phase-derive-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	expect_check("wrong-phase-derive-check", runtime.check_result,
		     BE_CHECK_INVALID_PHASE);

	begin_test_scenario(&runtime);
	memset(&report, 0xa5, sizeof(report));
	expect_runtime("wrong-phase-report",
		       be_runtime_report(&runtime, &report),
		       BE_RUNTIME_FAILED);
	expect_phase("wrong-phase-report-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	expect_check("wrong-phase-report-check", runtime.check_result,
		     BE_CHECK_INVALID_PHASE);
	require_named(report_is_zero(&report), "wrong-phase-report-zero");

	begin_test_scenario(&runtime);
	expect_runtime("copy-inventory-for-null-proposal",
		       be_runtime_copy_inventory(&runtime, be_r1_inventory()),
		       BE_RUNTIME_OK);
	expect_runtime("null-proposal-input",
		       be_runtime_copy_proposal(&runtime,
						(const struct be_proposal *)0),
		       BE_RUNTIME_FAILED);
	expect_phase("null-proposal-input-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	expect_check("null-proposal-input-check", runtime.check_result,
		     BE_CHECK_NULL);

	if (!prepare_derived(&runtime, be_r1_proposal(), "null-report-output-pre"))
		return;
	expect_runtime("null-report-output",
		       be_runtime_report(&runtime,
					 (struct be_runtime_report *)0),
		       BE_RUNTIME_FAILED);
	expect_phase("null-report-output-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	expect_check("null-report-output-check", runtime.check_result,
		     BE_CHECK_NULL);
}

static void test_inventory_rejections(void)
{
	struct be_platform_inventory inventory = mutable_inventory();

	expect_check("inventory-null", be_check_inventory((const struct be_platform_inventory *)0),
		     BE_CHECK_NULL);

	inventory.resource_count = 12U;
	expect_check("inventory-count-incomplete",
		     be_check_inventory(&inventory), BE_CHECK_INCOMPLETE);

	inventory = mutable_inventory();
	find_inventory_resource(&inventory, 13U)->size = 0U;
	expect_check("inventory-zero-size", be_check_inventory(&inventory),
		     BE_CHECK_UNSUPPORTED);

	inventory = mutable_inventory();
	find_inventory_resource(&inventory, 13U)->base += 1U;
	expect_check("inventory-unaligned-base", be_check_inventory(&inventory),
		     BE_CHECK_UNSUPPORTED);

	inventory = mutable_inventory();
	find_inventory_resource(&inventory, 13U)->base =
		~BE_U64_C(0) - (BE_PAGE_SIZE - BE_U64_C(1));
	find_inventory_resource(&inventory, 13U)->size =
		BE_PAGE_SIZE + BE_PAGE_SIZE;
	expect_check("inventory-overflow-extent",
		     be_check_inventory(&inventory), BE_CHECK_UNSUPPORTED);

	inventory = mutable_inventory();
	find_inventory_resource(&inventory, 13U)->kind = BE_RESOURCE_KIND_COUNT;
	expect_check("inventory-invalid-kind", be_check_inventory(&inventory),
		     BE_CHECK_UNSUPPORTED);

	inventory = mutable_inventory();
	find_inventory_resource(&inventory, 13U)->id = 12U;
	expect_check("inventory-duplicate-id", be_check_inventory(&inventory),
		     BE_CHECK_DUPLICATE_RESOURCE);

	inventory = mutable_inventory();
	find_inventory_resource(&inventory, 13U)->base =
		find_inventory_resource(&inventory, 12U)->base;
	expect_check("inventory-overlap", be_check_inventory(&inventory),
		     BE_CHECK_OVERLAPPING_RESOURCE);

	inventory = mutable_inventory();
	find_inventory_resource(&inventory, 13U)->kind = BE_RESOURCE_SAVED_STATE;
	expect_check("inventory-wrong-composition",
		     be_check_inventory(&inventory), BE_CHECK_INCOMPLETE);
}

static void test_proposal_envelope_rejections(void)
{
	struct be_platform_inventory inventory = mutable_inventory();
	struct be_proposal proposal = mutable_proposal();
	struct be_resource_request *resource;

	expect_proposal_failure("proposal-null", &inventory,
				(const struct be_proposal *)0, BE_CHECK_NULL);
	expect_proposal_failure("proposal-null-inventory",
				(const struct be_platform_inventory *)0,
				&proposal, BE_CHECK_NULL);

	proposal.proposal_id = 0U;
	expect_proposal_failure("proposal-zero-id", &inventory, &proposal,
				BE_CHECK_UNSUPPORTED);

	proposal = mutable_proposal();
	proposal.source_vocabulary = BE_VOCABULARY_INVALID;
	expect_proposal_failure("proposal-invalid-vocabulary", &inventory,
				&proposal, BE_CHECK_UNSUPPORTED);

	proposal = mutable_proposal();
	proposal.domain_count = 1U;
	expect_proposal_failure("proposal-wrong-domain-count", &inventory,
				&proposal, BE_CHECK_INCOMPLETE);

	proposal = mutable_proposal();
	proposal.resource_count = 12U;
	expect_proposal_failure("proposal-wrong-resource-count", &inventory,
				&proposal, BE_CHECK_INCOMPLETE);

	proposal = mutable_proposal();
	proposal.authority_count = 5U;
	expect_proposal_failure("proposal-wrong-authority-count", &inventory,
				&proposal, BE_CHECK_INCOMPLETE);

	proposal = mutable_proposal();
	proposal.published_root_count = 1U;
	expect_proposal_failure("proposal-direct-root-publication", &inventory,
				&proposal, BE_CHECK_DIRECT_AUTHORITY);

	proposal = mutable_proposal();
	proposal.published_mapping_count = 1U;
	expect_proposal_failure("proposal-direct-mapping-publication",
				&inventory, &proposal,
				BE_CHECK_DIRECT_AUTHORITY);

	proposal = mutable_proposal();
	proposal.published_active_domain = BE_DOMAIN_MANAGEMENT;
	expect_proposal_failure("proposal-direct-active-publication",
				&inventory, &proposal,
				BE_CHECK_DIRECT_AUTHORITY);

	proposal = mutable_proposal();
	resource = find_proposal_resource(&proposal, 13U);
	resource->resource_id = 99U;
	expect_proposal_failure("proposal-resource-closure-missing", &inventory,
				&proposal, BE_CHECK_INVENTORY_CLOSURE);

	proposal = mutable_proposal();
	resource = find_proposal_resource(&proposal, 13U);
	resource->resource_id = 12U;
	expect_proposal_failure("proposal-resource-duplicate", &inventory,
				&proposal, BE_CHECK_DUPLICATE_RESOURCE);

	proposal = mutable_proposal();
	resource = find_proposal_resource(&proposal, 13U);
	resource->base += BE_PAGE_SIZE;
	expect_proposal_failure("proposal-resource-base-mismatch", &inventory,
				&proposal, BE_CHECK_INVENTORY_CLOSURE);

	proposal = mutable_proposal();
	resource = find_proposal_resource(&proposal, 13U);
	resource->size += BE_PAGE_SIZE;
	expect_proposal_failure("proposal-resource-size-mismatch", &inventory,
				&proposal, BE_CHECK_INVENTORY_CLOSURE);
}

static void test_binding_rejections(void)
{
	struct be_platform_inventory inventory = mutable_inventory();
	struct be_proposal proposal = mutable_proposal();
	struct be_domain_request *management;
	struct be_domain_request *protected;

	proposal.domains[1].id = BE_DOMAIN_MANAGEMENT;
	expect_proposal_failure("binding-duplicate-domain", &inventory,
				&proposal, BE_CHECK_BINDING);

	proposal = mutable_proposal();
	proposal.domain_count = 1U;
	expect_proposal_failure("binding-missing-domain", &inventory,
				&proposal, BE_CHECK_INCOMPLETE);

	proposal = mutable_proposal();
	management = find_proposal_domain(&proposal, BE_DOMAIN_MANAGEMENT);
	protected = find_proposal_domain(&proposal, BE_DOMAIN_PROTECTED);
	protected->vcpu_id = management->vcpu_id;
	expect_proposal_failure("binding-duplicate-vcpu", &inventory,
				&proposal, BE_CHECK_BINDING);

	proposal = mutable_proposal();
	management = find_proposal_domain(&proposal, BE_DOMAIN_MANAGEMENT);
	protected = find_proposal_domain(&proposal, BE_DOMAIN_PROTECTED);
	protected->root_id = management->root_id;
	expect_proposal_failure("binding-duplicate-root-id", &inventory,
				&proposal, BE_CHECK_BINDING);

	proposal = mutable_proposal();
	management = find_proposal_domain(&proposal, BE_DOMAIN_MANAGEMENT);
	protected = find_proposal_domain(&proposal, BE_DOMAIN_PROTECTED);
	protected->root_resource_id = management->root_resource_id;
	expect_proposal_failure("binding-duplicate-root-storage", &inventory,
				&proposal, BE_CHECK_BINDING);

	proposal = mutable_proposal();
	management = find_proposal_domain(&proposal, BE_DOMAIN_MANAGEMENT);
	protected = find_proposal_domain(&proposal, BE_DOMAIN_PROTECTED);
	protected->trusted_stack_resource_id =
		management->trusted_stack_resource_id;
	expect_proposal_failure("binding-duplicate-stack-storage", &inventory,
				&proposal, BE_CHECK_BINDING);

	proposal = mutable_proposal();
	management = find_proposal_domain(&proposal, BE_DOMAIN_MANAGEMENT);
	protected = find_proposal_domain(&proposal, BE_DOMAIN_PROTECTED);
	protected->saved_state_id = management->saved_state_id;
	expect_proposal_failure("binding-duplicate-saved-id", &inventory,
				&proposal, BE_CHECK_BINDING);

	proposal = mutable_proposal();
	management = find_proposal_domain(&proposal, BE_DOMAIN_MANAGEMENT);
	protected = find_proposal_domain(&proposal, BE_DOMAIN_PROTECTED);
	protected->saved_state_resource_id =
		management->saved_state_resource_id;
	expect_proposal_failure("binding-duplicate-saved-storage", &inventory,
				&proposal, BE_CHECK_BINDING);

	proposal = mutable_proposal();
	management = find_proposal_domain(&proposal, BE_DOMAIN_MANAGEMENT);
	management->vmid = 1U;
	expect_proposal_failure("binding-nonzero-vmid", &inventory, &proposal,
				BE_CHECK_BINDING);

	proposal = mutable_proposal();
	management = find_proposal_domain(&proposal, BE_DOMAIN_MANAGEMENT);
	management->root_resource_id = 5U;
	expect_proposal_failure("binding-wrong-root-resource-class",
				&inventory, &proposal, BE_CHECK_BINDING);

	proposal = mutable_proposal();
	management = find_proposal_domain(&proposal, BE_DOMAIN_MANAGEMENT);
	management->trusted_stack_resource_id = 3U;
	expect_proposal_failure("binding-wrong-stack-resource-class",
				&inventory, &proposal, BE_CHECK_BINDING);

	proposal = mutable_proposal();
	management = find_proposal_domain(&proposal, BE_DOMAIN_MANAGEMENT);
	management->saved_state_resource_id = 5U;
	expect_proposal_failure("binding-wrong-saved-resource-class",
				&inventory, &proposal, BE_CHECK_BINDING);
}

static void test_ownership_and_authority_rejections(void)
{
	struct be_platform_inventory inventory = mutable_inventory();
	struct be_proposal proposal = mutable_proposal();
	struct be_resource_request *resource;
	struct be_authority_request *authority;

	resource = find_proposal_resource(&proposal, 9U);
	resource->owner = BE_DOMAIN_PROTECTED;
	expect_proposal_failure("ownership-wrong-private-owner", &inventory,
				&proposal, BE_CHECK_PRIVATE_OWNER);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_MANAGEMENT_PRIVATE);
	authority->resource_id = 10U;
	expect_proposal_failure("ownership-cross-private-mapping", &inventory,
				&proposal, BE_CHECK_PRIVATE_OWNER);

	proposal = mutable_proposal();
	resource = find_proposal_resource(&proposal, 12U);
	resource->owner = BE_DOMAIN_PROTECTED;
	expect_proposal_failure("ownership-wrong-guest-code-owner", &inventory,
				&proposal, BE_CHECK_PRIVATE_OWNER);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_GUEST_CODE_MANAGEMENT);
	authority->domain = BE_DOMAIN_PROTECTED;
	expect_proposal_failure("ownership-wrong-guest-code-domain",
				&inventory, &proposal, BE_CHECK_PRIVATE_OWNER);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_GUEST_CODE_MANAGEMENT);
	authority->rights = BE_RIGHT_READ | BE_RIGHT_WRITE;
	expect_proposal_failure("authority-guest-code-not-rx", &inventory,
				&proposal, BE_CHECK_EXCESS_RIGHTS);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_MANAGEMENT_PRIVATE);
	authority->rights = BE_RIGHT_READ;
	expect_proposal_failure("authority-private-not-rw", &inventory,
				&proposal, BE_CHECK_EXCESS_RIGHTS);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_MANAGEMENT_PRIVATE);
	authority->rights =
		BE_RIGHT_READ | BE_RIGHT_WRITE | BE_RIGHT_EXECUTE;
	expect_proposal_failure("authority-write-execute", &inventory,
				&proposal, BE_CHECK_UNSUPPORTED);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_MANAGEMENT_PRIVATE);
	authority->rights = BE_RIGHT_WRITE;
	expect_proposal_failure("authority-write-without-read", &inventory,
				&proposal, BE_CHECK_UNSUPPORTED);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_MANAGEMENT_PRIVATE);
	authority->rights = 0U;
	expect_proposal_failure("authority-zero-rights", &inventory, &proposal,
				BE_CHECK_UNSUPPORTED);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_MANAGEMENT_PRIVATE);
	authority->rights = (be_u32)(BE_RIGHT_ALL | 0x80U);
	expect_proposal_failure("authority-unknown-rights", &inventory,
				&proposal, BE_CHECK_UNSUPPORTED);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_MANAGEMENT_PRIVATE);
	authority->resource_id = 1U;
	expect_proposal_failure("authority-monitor-mapping", &inventory,
				&proposal, BE_CHECK_EXCLUDED_MAPPING);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_MANAGEMENT_PRIVATE);
	authority->resource_id = 3U;
	expect_proposal_failure("authority-root-mapping", &inventory,
				&proposal, BE_CHECK_EXCLUDED_MAPPING);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_MANAGEMENT_PRIVATE);
	authority->resource_id = 5U;
	expect_proposal_failure("authority-stack-mapping", &inventory,
				&proposal, BE_CHECK_EXCLUDED_MAPPING);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_MANAGEMENT_PRIVATE);
	authority->resource_id = 7U;
	expect_proposal_failure("authority-saved-mapping", &inventory,
				&proposal, BE_CHECK_EXCLUDED_MAPPING);

	proposal = mutable_proposal();
	proposal.authorities[1] = proposal.authorities[0];
	expect_proposal_failure("authority-duplicate-gpa-and-backing",
				&inventory, &proposal,
				BE_CHECK_UNDECLARED_MAPPING);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_PROTECTED,
					    BE_GPA_SHARED);
	authority->rights = BE_RIGHT_READ | BE_RIGHT_WRITE;
	expect_proposal_failure("authority-wrong-shared-rights",
				&inventory, &proposal,
				BE_CHECK_CHANNEL_RIGHTS);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_MANAGEMENT,
					    BE_GPA_SHARED);
	authority->resource_id = 9U;
	expect_proposal_failure("authority-wrong-shared-backing",
				&inventory, &proposal,
				BE_CHECK_UNDECLARED_MAPPING);

	proposal = mutable_proposal();
	authority = find_proposal_authority(&proposal, BE_DOMAIN_PROTECTED,
					    BE_GPA_SHARED);
	authority->gpa = BE_GPA_PROTECTED_PRIVATE;
	expect_proposal_failure("authority-missing-shared-authority",
				&inventory, &proposal,
				BE_CHECK_UNDECLARED_MAPPING);

	proposal = mutable_proposal();
	proposal.authorities[5] =
		*find_proposal_authority(&proposal, BE_DOMAIN_PROTECTED,
					 BE_GPA_SHARED);
	expect_proposal_failure("authority-extra-shared-authority",
				&inventory, &proposal,
				BE_CHECK_UNDECLARED_MAPPING);

	proposal = mutable_proposal();
	proposal.channels[0].source = BE_DOMAIN_PROTECTED;
	expect_proposal_failure("channel-wrong-direction", &inventory,
				&proposal, BE_CHECK_CHANNEL_RIGHTS);

	proposal = mutable_proposal();
	proposal.channels[0].target_rights =
		BE_RIGHT_READ | BE_RIGHT_WRITE;
	expect_proposal_failure("channel-wrong-target-rights", &inventory,
				&proposal, BE_CHECK_CHANNEL_RIGHTS);

	proposal = mutable_proposal();
	proposal.channels[0].resource_id = 9U;
	expect_proposal_failure("channel-wrong-backing", &inventory, &proposal,
				BE_CHECK_UNDECLARED_SHARED);
}

static void test_no_partial_outputs_and_integrity(void)
{
	struct be_runtime runtime;
	struct be_proposal bad_proposal = mutable_proposal();
	struct be_canonical_state canonical;
	struct be_runtime_report report;

	bad_proposal.published_root_count = 1U;
	begin_test_scenario(&runtime);
	expect_runtime("validate-bad-proposal-copy-inventory",
		       be_runtime_copy_inventory(&runtime, be_r1_inventory()),
		       BE_RUNTIME_OK);
	expect_runtime("validate-bad-proposal-copy-proposal",
		       be_runtime_copy_proposal(&runtime, &bad_proposal),
		       BE_RUNTIME_OK);
	expect_runtime("validate-bad-proposal",
		       be_runtime_validate(&runtime), BE_RUNTIME_FAILED);
	expect_phase("validate-bad-proposal-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	expect_check("validate-bad-proposal-check", runtime.check_result,
		     BE_CHECK_DIRECT_AUTHORITY);
	require_named(canonical_is_zero(&runtime.canonical),
		      "validate-bad-proposal-canonical-zero");
	require_named(enforcement_is_zero(&runtime.enforcement),
		      "validate-bad-proposal-enforcement-zero");
	require_named(runtime.validated_identity == 0U,
		      "validate-bad-proposal-validated-zero");

	memset(&canonical, 0, sizeof(canonical));
	expect_check("direct-derive-source-canonicalize",
		     be_canonicalize(be_r1_inventory(), be_r1_proposal(),
				     &canonical),
		     BE_CHECK_OK);
	canonical.authorities[0].frame_id = 1U;
	reidentify(&canonical);
	expect_derive_failure("direct-derive-no-partial-output", &canonical,
			      BE_CHECK_EXCLUDED_MAPPING);

	if (!prepare_validated(&runtime, be_r1_proposal(), "seal-integrity-pre"))
		return;
	runtime.canonical.domains[0].root_id = runtime.canonical.domains[1].root_id;
	expect_runtime("seal-canonical-mutated", be_runtime_seal(&runtime),
		       BE_RUNTIME_FAILED);
	expect_phase("seal-canonical-mutated-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	require_named(canonical_is_zero(&runtime.canonical),
		      "seal-canonical-mutated-zero");
	require_named(enforcement_is_zero(&runtime.enforcement),
		      "seal-canonical-mutated-enforcement-zero");

	if (!prepare_validated(&runtime, be_r1_proposal(), "seal-direct-authority-pre"))
		return;
	runtime.enforcement.roots[0].domain = BE_DOMAIN_MANAGEMENT;
	expect_runtime("seal-direct-authority-injection",
		       be_runtime_seal(&runtime), BE_RUNTIME_FAILED);
	expect_phase("seal-direct-authority-injection-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	expect_check("seal-direct-authority-injection-check",
		     runtime.check_result, BE_CHECK_DIRECT_AUTHORITY);
	require_named(canonical_is_zero(&runtime.canonical),
		      "seal-direct-authority-injection-zero");
	require_named(enforcement_is_zero(&runtime.enforcement),
		      "seal-direct-authority-injection-enforcement-zero");

	if (!prepare_validated(&runtime, be_r1_proposal(), "derive-integrity-pre"))
		return;
	expect_runtime("derive-integrity-seal", be_runtime_seal(&runtime),
		       BE_RUNTIME_OK);
	runtime.canonical.frames[12].owner_mask = BE_OWNER_MANAGEMENT;
	expect_runtime("derive-canonical-mutated", be_runtime_derive(&runtime),
		       BE_RUNTIME_FAILED);
	expect_phase("derive-canonical-mutated-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	require_named(enforcement_is_zero(&runtime.enforcement),
		      "derive-canonical-mutated-enforcement-zero");

	if (!prepare_derived(&runtime, be_r1_proposal(), "report-integrity-pre"))
		return;
	memset(&report, 0xa5, sizeof(report));
	runtime.canonical.authorities[0].rights |= BE_RIGHT_EXECUTE;
	expect_runtime("report-canonical-mutated",
		       be_runtime_report(&runtime, &report),
		       BE_RUNTIME_FAILED);
	expect_phase("report-canonical-mutated-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	require_named(report_is_zero(&report),
		      "report-canonical-mutated-zero");

	if (!prepare_derived(&runtime, be_r1_proposal(), "report-derived-mutated-pre"))
		return;
	memset(&report, 0xa5, sizeof(report));
	runtime.enforcement.roots[0].mappings[0].rights |= BE_RIGHT_EXECUTE;
	expect_runtime("report-derived-mutated",
		       be_runtime_report(&runtime, &report),
		       BE_RUNTIME_FAILED);
	expect_phase("report-derived-mutated-phase", runtime.phase,
		     BE_RUNTIME_PHASE_FAILED);
	require_named(report_is_zero(&report), "report-derived-mutated-zero");
}

static void test_terminal_failure(void)
{
	struct be_runtime runtime;

	begin_test_scenario(&runtime);
	expect_runtime("failed-state-entry",
		       be_runtime_validate(&runtime), BE_RUNTIME_FAILED);
	expect_failed_state_sticky(&runtime, "failed-state-sticky");
}

int main(void)
{
	test_positive_flow_and_report();
	test_source_order_vocabulary_and_proposal_id_equivalence();
	test_null_and_wrong_phase_behaviour();
	test_inventory_rejections();
	test_proposal_envelope_rejections();
	test_binding_rejections();
	test_ownership_and_authority_rejections();
	test_no_partial_outputs_and_integrity();
	test_terminal_failure();

	if (failures != 0) {
		printf("BE_R1_CHECK: FAIL failures=%d\n", failures);
		return 1;
	}
	printf("BE_R1_CHECK: PASS resources=13 authorities=6 roots=2 mappings=6\n");
	return 0;
}
