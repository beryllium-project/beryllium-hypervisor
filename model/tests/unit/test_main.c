// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Host tests for Model 0.2 validation, sealing, derivation, and behavior.
 *
 * GCC and Clang compile the same restricted-C core. These tests are host
 * evidence, not a C refinement, privileged runtime, or hardware result.
 */
#include <assert.h>
#include <stdio.h>

#include <be/fixtures.h>
#include <be/state.h>

#define MANAGEMENT_PRIVATE_GPA	BE_U64_C(0x40000000)
#define PROTECTED_PRIVATE_GPA	BE_U64_C(0x40001000)
#define SHARED_GPA		BE_U64_C(0x40002000)
#define REGISTER_SENTINEL	BE_U64_C(0x1122334455667788)
#define PROTECTED_SENTINEL	BE_U64_C(0x8877665544332211)

static struct be_platform_inventory mutable_inventory(void)
{
	return *be_fixture_inventory();
}

static struct be_proposal mutable_proposal(enum be_fixture_id fixture)
{
	const struct be_proposal *source = be_fixture_proposal(fixture);

	assert(source != NULL);
	return *source;
}

static void expect_inventory(const char *name,
			     const struct be_platform_inventory *inventory,
			     enum be_check_result expected)
{
	enum be_check_result actual = be_check_inventory(inventory);

	if (actual != expected) {
		fprintf(stderr, "%s: expected %s, received %s\n", name,
			be_check_result_name(expected),
			be_check_result_name(actual));
	}
	assert(actual == expected);
}

static void expect_proposal(const char *name,
			    const struct be_platform_inventory *inventory,
			    const struct be_proposal *proposal,
			    enum be_check_result expected)
{
	struct be_canonical_state canonical = {
		.configuration_id = BE_U64_C(0xffffffffffffffff),
		.domain_count = 1U,
	};
	enum be_check_result actual =
		be_canonicalize(inventory, proposal, &canonical);

	if (actual != expected) {
		fprintf(stderr, "%s: expected %s, received %s\n", name,
			be_check_result_name(expected),
			be_check_result_name(actual));
	}
	assert(actual == expected);
	if (expected != BE_CHECK_OK) {
		assert(canonical.configuration_id == 0U);
		assert(canonical.domain_count == 0U);
		assert(canonical.frame_count == 0U);
	}
}

static struct be_canonical_state
canonical_fixture(enum be_fixture_id fixture)
{
	struct be_canonical_state canonical;

	assert(be_canonicalize(
		       be_fixture_inventory(), be_fixture_proposal(fixture),
		       &canonical) == BE_CHECK_OK);
	return canonical;
}

static struct be_enforcement_state
enforcement_fixture(enum be_fixture_id fixture)
{
	struct be_canonical_state canonical = canonical_fixture(fixture);
	struct be_enforcement_state enforcement;

	assert(be_derive_enforcement(&canonical, &enforcement) ==
	       BE_CHECK_OK);
	return enforcement;
}

static void reidentify(struct be_canonical_state *canonical)
{
	canonical->configuration_id =
		be_configuration_identity(canonical);
}

static void test_valid_inputs_and_source_independence(void)
{
	struct be_canonical_state source_a =
		canonical_fixture(BE_FIXTURE_SOURCE_A);
	struct be_canonical_state source_b =
		canonical_fixture(BE_FIXTURE_SOURCE_B);
	struct be_enforcement_state derived_a;
	struct be_enforcement_state derived_b;

	expect_inventory("fixed inventory", be_fixture_inventory(),
			 BE_CHECK_OK);
	assert(source_a.configuration_id != 0U);
	assert(source_a.configuration_id == source_b.configuration_id);
	assert(source_a.domains[0].id == source_b.domains[0].id);
	assert(source_a.domains[1].id == source_b.domains[1].id);
	assert(source_a.frames[0].id == source_b.frames[0].id);
	assert(source_a.frames[BE_MAX_RESOURCES - 1U].id ==
	       source_b.frames[BE_MAX_RESOURCES - 1U].id);
	assert(source_a.authorities[0].domain ==
	       source_b.authorities[0].domain);
	assert(source_a.authorities[3].rights ==
	       source_b.authorities[3].rights);
	assert(be_derive_enforcement(&source_a, &derived_a) == BE_CHECK_OK);
	assert(be_derive_enforcement(&source_b, &derived_b) == BE_CHECK_OK);
	assert(derived_a.configuration_id == derived_b.configuration_id);
	assert(derived_a.roots[0].mapping_count ==
	       derived_b.roots[0].mapping_count);
	assert(derived_a.roots[1].mappings[1].rights ==
	       derived_b.roots[1].mappings[1].rights);

	assert(be_fixture_proposal(BE_FIXTURE_INVALID) == NULL);
	assert(be_fixture_proposal(BE_FIXTURE_COUNT) == NULL);
	assert(be_fixture_name(BE_FIXTURE_SOURCE_A) != NULL);
	assert(be_fixture_name(BE_FIXTURE_SOURCE_B) != NULL);
	assert(be_fixture_name(BE_FIXTURE_INVALID) != NULL);
}

static void test_inventory_rejections(void)
{
	struct be_platform_inventory inventory = mutable_inventory();

	expect_inventory("null inventory", NULL, BE_CHECK_NULL);
	inventory.model_version = 1U;
	expect_inventory("unsupported inventory version", &inventory,
			 BE_CHECK_UNSUPPORTED);
	inventory = mutable_inventory();
	inventory.resource_count = BE_MAX_RESOURCES - 1U;
	expect_inventory("incomplete inventory", &inventory,
			 BE_CHECK_INCOMPLETE);
	inventory = mutable_inventory();
	inventory.resources[0].base += 1U;
	expect_inventory("unaligned resource", &inventory,
			 BE_CHECK_UNSUPPORTED);
	inventory = mutable_inventory();
	inventory.resources[10].id = inventory.resources[9].id;
	expect_inventory("duplicate resource", &inventory,
			 BE_CHECK_DUPLICATE_RESOURCE);
	inventory = mutable_inventory();
	inventory.resources[10].base = inventory.resources[9].base;
	expect_inventory("overlapping resource", &inventory,
			 BE_CHECK_OVERLAPPING_RESOURCE);
	inventory = mutable_inventory();
	inventory.resources[10].kind = BE_RESOURCE_SAVED_STATE;
	expect_inventory("wrong inventory class count", &inventory,
			 BE_CHECK_INCOMPLETE);
	inventory = mutable_inventory();
	inventory.resources[10].size = 0U;
	expect_inventory("zero resource size", &inventory,
			 BE_CHECK_UNSUPPORTED);
}

static void test_proposal_envelope_rejections(void)
{
	struct be_platform_inventory inventory = mutable_inventory();
	struct be_proposal proposal =
		mutable_proposal(BE_FIXTURE_SOURCE_A);

	expect_proposal("null proposal", &inventory, NULL, BE_CHECK_NULL);
	expect_proposal("null inventory", NULL, &proposal, BE_CHECK_NULL);
	proposal.proposal_id = 0U;
	expect_proposal("zero proposal identity", &inventory, &proposal,
			BE_CHECK_UNSUPPORTED);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.source_vocabulary = BE_VOCABULARY_INVALID;
	expect_proposal("invalid source vocabulary", &inventory, &proposal,
			BE_CHECK_UNSUPPORTED);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.domain_count = 1U;
	expect_proposal("incomplete domains", &inventory, &proposal,
			BE_CHECK_INCOMPLETE);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.resource_count = BE_MAX_RESOURCES - 1U;
	expect_proposal("incomplete resources", &inventory, &proposal,
			BE_CHECK_INCOMPLETE);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.authority_count = 3U;
	expect_proposal("incomplete authority", &inventory, &proposal,
			BE_CHECK_INCOMPLETE);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.channel_count = 0U;
	expect_proposal("incomplete channel", &inventory, &proposal,
			BE_CHECK_INCOMPLETE);

	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.published_root_count = 1U;
	expect_proposal("producer-published root", &inventory, &proposal,
			BE_CHECK_DIRECT_AUTHORITY);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.published_mapping_count = 1U;
	expect_proposal("producer-published mapping", &inventory, &proposal,
			BE_CHECK_DIRECT_AUTHORITY);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.published_active_domain = BE_DOMAIN_MANAGEMENT;
	expect_proposal("producer-published active domain", &inventory,
			&proposal, BE_CHECK_DIRECT_AUTHORITY);
}

static void test_inventory_closure_and_resource_rejections(void)
{
	struct be_platform_inventory inventory = mutable_inventory();
	struct be_proposal proposal =
		mutable_proposal(BE_FIXTURE_SOURCE_A);

	proposal.resources[10].resource_id = 99U;
	expect_proposal("unknown proposal resource", &inventory, &proposal,
			BE_CHECK_INVENTORY_CLOSURE);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.resources[10].base += BE_PAGE_SIZE;
	expect_proposal("proposal base differs from inventory", &inventory,
			&proposal, BE_CHECK_INVENTORY_CLOSURE);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.resources[10].size += BE_PAGE_SIZE;
	expect_proposal("proposal size differs from inventory", &inventory,
			&proposal, BE_CHECK_INVENTORY_CLOSURE);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.resources[10].resource_id =
		proposal.resources[9].resource_id;
	expect_proposal("duplicate proposal resource", &inventory, &proposal,
			BE_CHECK_DUPLICATE_RESOURCE);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.resources[0].class = BE_FRAME_PRIVATE;
	expect_proposal("monitor resource reclassified", &inventory,
			&proposal, BE_CHECK_EXCLUDED_MAPPING);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.resources[8].owner = BE_DOMAIN_INVALID;
	expect_proposal("private resource lacks owner", &inventory, &proposal,
			BE_CHECK_PRIVATE_OWNER);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.resources[10].owner = BE_DOMAIN_MANAGEMENT;
	expect_proposal("shared resource has owner", &inventory, &proposal,
			BE_CHECK_UNDECLARED_SHARED);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.resources[8].class = BE_FRAME_SHARED;
	proposal.resources[8].owner = BE_DOMAIN_INVALID;
	expect_proposal("extra shared resource", &inventory, &proposal,
			BE_CHECK_UNDECLARED_SHARED);
}

static void test_binding_rejections(void)
{
	struct be_platform_inventory inventory = mutable_inventory();
	struct be_proposal proposal =
		mutable_proposal(BE_FIXTURE_SOURCE_A);

	proposal.domains[1].id = BE_DOMAIN_MANAGEMENT;
	expect_proposal("duplicate domain", &inventory, &proposal,
			BE_CHECK_BINDING);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.domains[0].vcpu_id = 0U;
	expect_proposal("zero vcpu", &inventory, &proposal,
			BE_CHECK_UNSUPPORTED);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.domains[0].vmid = 0x4000U;
	expect_proposal("unsupported vmid", &inventory, &proposal,
			BE_CHECK_UNSUPPORTED);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.domains[0].root_resource_id = 5U;
	expect_proposal("wrong root resource kind", &inventory, &proposal,
			BE_CHECK_BINDING);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.domains[0].trusted_stack_resource_id = 3U;
	expect_proposal("wrong stack resource kind", &inventory, &proposal,
			BE_CHECK_BINDING);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.domains[0].saved_state_resource_id = 5U;
	expect_proposal("wrong saved-state resource kind", &inventory,
			&proposal, BE_CHECK_BINDING);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.domains[1].vcpu_id = proposal.domains[0].vcpu_id;
	expect_proposal("duplicate vcpu binding", &inventory, &proposal,
			BE_CHECK_BINDING);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.domains[1].root_id = proposal.domains[0].root_id;
	expect_proposal("duplicate root binding", &inventory, &proposal,
			BE_CHECK_BINDING);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.domains[1].saved_state_id =
		proposal.domains[0].saved_state_id;
	expect_proposal("duplicate saved-state binding", &inventory,
			&proposal, BE_CHECK_BINDING);
}

static void test_channel_and_authority_rejections(void)
{
	struct be_platform_inventory inventory = mutable_inventory();
	struct be_proposal proposal =
		mutable_proposal(BE_FIXTURE_SOURCE_A);

	proposal.channels[0].target_rights =
		BE_RIGHT_READ | BE_RIGHT_WRITE;
	expect_proposal("channel target may not write", &inventory, &proposal,
			BE_CHECK_CHANNEL_RIGHTS);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.channels[0].source = BE_DOMAIN_PROTECTED;
	expect_proposal("wrong channel direction", &inventory, &proposal,
			BE_CHECK_CHANNEL_RIGHTS);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.channels[0].resource_id = 9U;
	expect_proposal("private channel backing", &inventory, &proposal,
			BE_CHECK_UNDECLARED_SHARED);

	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.authorities[0].domain = BE_DOMAIN_INVALID;
	expect_proposal("invalid authority domain", &inventory, &proposal,
			BE_CHECK_UNSUPPORTED);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.authorities[0].gpa += 1U;
	expect_proposal("unaligned authority gpa", &inventory, &proposal,
			BE_CHECK_UNSUPPORTED);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.authorities[0].rights = BE_RIGHT_WRITE;
	expect_proposal("write without read", &inventory, &proposal,
			BE_CHECK_UNSUPPORTED);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.authorities[0].resource_id = 1U;
	expect_proposal("monitor authority", &inventory, &proposal,
			BE_CHECK_EXCLUDED_MAPPING);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.resources[8].owner = BE_DOMAIN_PROTECTED;
	expect_proposal("wrong private authority owner", &inventory,
			&proposal, BE_CHECK_PRIVATE_OWNER);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.authorities[3].rights =
		BE_RIGHT_READ | BE_RIGHT_WRITE;
	expect_proposal("channel authority exceeds endpoint", &inventory,
			&proposal, BE_CHECK_CHANNEL_RIGHTS);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.authorities[1] = proposal.authorities[0];
	expect_proposal("duplicate authority", &inventory, &proposal,
			BE_CHECK_UNDECLARED_MAPPING);
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.authorities[0].rights |= BE_RIGHT_EXECUTE;
	expect_proposal("private authority exceeds fixed profile", &inventory,
			&proposal, BE_CHECK_EXCESS_RIGHTS);
}

static void test_canonical_and_derived_integrity(void)
{
	struct be_canonical_state canonical =
		canonical_fixture(BE_FIXTURE_SOURCE_A);
	struct be_enforcement_state enforcement =
		enforcement_fixture(BE_FIXTURE_SOURCE_A);

	assert(be_check_canonical(&canonical) == BE_CHECK_OK);
	assert(be_check_enforcement(&canonical, &enforcement) ==
	       BE_CHECK_OK);

	canonical.configuration_id ^= 1U;
	assert(be_check_canonical(&canonical) == BE_CHECK_INTEGRITY);
	canonical = canonical_fixture(BE_FIXTURE_SOURCE_A);
	canonical.domains[0].root_id = canonical.domains[1].root_id;
	reidentify(&canonical);
	assert(be_check_canonical(&canonical) == BE_CHECK_BINDING);
	canonical = canonical_fixture(BE_FIXTURE_SOURCE_A);
	canonical.authorities[0].frame_id = 1U;
	reidentify(&canonical);
	assert(be_check_canonical(&canonical) ==
	       BE_CHECK_EXCLUDED_MAPPING);
	canonical = canonical_fixture(BE_FIXTURE_SOURCE_A);
	canonical.authorities[0].rights |= BE_RIGHT_EXECUTE;
	reidentify(&canonical);
	assert(be_check_canonical(&canonical) == BE_CHECK_EXCESS_RIGHTS);

	canonical = canonical_fixture(BE_FIXTURE_SOURCE_A);
	enforcement = enforcement_fixture(BE_FIXTURE_SOURCE_A);
	enforcement.configuration_id ^= 1U;
	assert(be_check_enforcement(&canonical, &enforcement) ==
	       BE_CHECK_INTEGRITY);
	enforcement = enforcement_fixture(BE_FIXTURE_SOURCE_A);
	enforcement.roots[0].root_id = 102U;
	assert(be_check_enforcement(&canonical, &enforcement) ==
	       BE_CHECK_BINDING);
	enforcement = enforcement_fixture(BE_FIXTURE_SOURCE_A);
	enforcement.roots[0].mappings[0].frame_id = 1U;
	assert(be_check_enforcement(&canonical, &enforcement) ==
	       BE_CHECK_EXCLUDED_MAPPING);
	enforcement = enforcement_fixture(BE_FIXTURE_SOURCE_A);
	enforcement.roots[0].mappings[0].rights |= BE_RIGHT_EXECUTE;
	assert(be_check_enforcement(&canonical, &enforcement) ==
	       BE_CHECK_EXCESS_RIGHTS);
	enforcement = enforcement_fixture(BE_FIXTURE_SOURCE_A);
	enforcement.roots[0].mapping_count = 1U;
	assert(be_check_enforcement(&canonical, &enforcement) ==
	       BE_CHECK_INCOMPLETE);
}

static void prepare_to_validated(struct be_model *model,
				 enum be_fixture_id fixture)
{
	be_model_reset(model);
	assert(model->phase == BE_PHASE_EMPTY);
	assert(be_model_bind_inventory(
		       model, be_fixture_inventory()) == BE_MODEL_OK);
	assert(model->phase == BE_PHASE_INVENTORY_BOUND);
	assert(be_model_copy_proposal(
		       model, be_fixture_proposal(fixture)) == BE_MODEL_OK);
	assert(model->phase == BE_PHASE_PROPOSAL_COPIED);
	assert(be_model_validate(model) == BE_MODEL_OK);
	assert(model->phase == BE_PHASE_VALIDATED);
	assert(model->sealed == 0U);
	assert(model->enforcement.root_count == 0U);
}

static void prepare_to_roots(struct be_model *model,
			     enum be_fixture_id fixture)
{
	prepare_to_validated(model, fixture);
	assert(be_model_seal(model) == BE_MODEL_OK);
	assert(model->phase == BE_PHASE_SEALED);
	assert(model->sealed != 0U);
	assert(be_model_derive_roots(model) == BE_MODEL_OK);
	assert(model->phase == BE_PHASE_ROOTS_DERIVED);
	assert(model->enforcement.root_count == BE_MAX_ROOTS);
	assert(model->active_domain == BE_DOMAIN_INVALID);
}

static void prepare_active(struct be_model *model,
			   enum be_fixture_id fixture)
{
	prepare_to_roots(model, fixture);
	assert(be_model_activate(model, BE_DOMAIN_MANAGEMENT) ==
	       BE_MODEL_OK);
	assert(model->phase == BE_PHASE_ACTIVE);
	assert(model->active_domain == BE_DOMAIN_MANAGEMENT);
}

static void test_phases_copying_and_no_partial_publication(void)
{
	struct be_platform_inventory inventory = mutable_inventory();
	struct be_proposal proposal =
		mutable_proposal(BE_FIXTURE_SOURCE_A);
	struct be_model model;

	be_model_reset(&model);
	assert(be_model_access(&model, MANAGEMENT_PRIVATE_GPA,
			       BE_RIGHT_READ) == BE_MODEL_FAILED);
	assert(model.phase == BE_PHASE_FAILED);
	assert(model.active_domain == BE_DOMAIN_INVALID);

	be_model_reset(&model);
	assert(be_model_validate(&model) == BE_MODEL_FAILED);
	assert(model.phase == BE_PHASE_FAILED);
	assert(model.check_result == BE_CHECK_INVALID_PHASE);
	assert(model.canonical.configuration_id == 0U);
	assert(model.enforcement.root_count == 0U);

	be_model_reset(&model);
	inventory.resources[10].base = inventory.resources[9].base;
	assert(be_model_bind_inventory(&model, &inventory) ==
	       BE_MODEL_FAILED);
	assert(model.phase == BE_PHASE_FAILED);
	assert(model.canonical.configuration_id == 0U);

	inventory = mutable_inventory();
	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	be_model_reset(&model);
	assert(be_model_bind_inventory(&model, &inventory) == BE_MODEL_OK);
	assert(be_model_copy_proposal(&model, &proposal) == BE_MODEL_OK);
	proposal.resources[0].class = BE_FRAME_PRIVATE;
	inventory.resources[0].kind = BE_RESOURCE_ASSIGNABLE;
	assert(be_model_validate(&model) == BE_MODEL_OK);
	assert(be_model_seal(&model) == BE_MODEL_OK);
	assert(be_model_derive_roots(&model) == BE_MODEL_OK);

	proposal = mutable_proposal(BE_FIXTURE_SOURCE_A);
	proposal.published_mapping_count = 1U;
	be_model_reset(&model);
	assert(be_model_bind_inventory(
		       &model, be_fixture_inventory()) == BE_MODEL_OK);
	assert(be_model_copy_proposal(&model, &proposal) == BE_MODEL_OK);
	assert(be_model_validate(&model) == BE_MODEL_FAILED);
	assert(model.check_result == BE_CHECK_DIRECT_AUTHORITY);
	assert(model.canonical.configuration_id == 0U);
	assert(model.enforcement.root_count == 0U);

	prepare_to_validated(&model, BE_FIXTURE_SOURCE_A);
	model.enforcement.roots[0].domain = BE_DOMAIN_MANAGEMENT;
	assert(be_model_seal(&model) == BE_MODEL_FAILED);
	assert(model.check_result == BE_CHECK_DIRECT_AUTHORITY);
	assert(model.canonical.configuration_id == 0U);
	assert(model.enforcement.root_count == 0U);

	prepare_to_validated(&model, BE_FIXTURE_SOURCE_A);
	model.canonical.domains[0].root_id = 102U;
	assert(be_model_seal(&model) == BE_MODEL_FAILED);
	assert(model.canonical.configuration_id == 0U);

	prepare_to_validated(&model, BE_FIXTURE_SOURCE_A);
	assert(be_model_seal(&model) == BE_MODEL_OK);
	model.enforcement.root_count = 1U;
	assert(be_model_derive_roots(&model) == BE_MODEL_FAILED);
	assert(model.check_result == BE_CHECK_DIRECT_AUTHORITY);
	assert(model.enforcement.root_count == 0U);
	assert(model.active_domain == BE_DOMAIN_INVALID);

	prepare_to_roots(&model, BE_FIXTURE_SOURCE_A);
	model.enforcement.roots[0].mappings[0].rights |=
		BE_RIGHT_EXECUTE;
	assert(be_model_activate(&model, BE_DOMAIN_MANAGEMENT) ==
	       BE_MODEL_FAILED);
	assert(model.phase == BE_PHASE_FAILED);
	assert(model.check_result == BE_CHECK_EXCESS_RIGHTS);
	assert(model.active_domain == BE_DOMAIN_INVALID);

	prepare_to_roots(&model, BE_FIXTURE_SOURCE_A);
	model.enforcement.roots[0].root_id = 102U;
	assert(be_model_activate(&model, BE_DOMAIN_MANAGEMENT) ==
	       BE_MODEL_FAILED);
	assert(model.check_result == BE_CHECK_BINDING);
	assert(model.active_domain == BE_DOMAIN_INVALID);
}

static void test_access_and_source_independent_behavior(void)
{
	struct be_model model;

	prepare_active(&model, BE_FIXTURE_SOURCE_A);
	assert(be_model_access(&model, MANAGEMENT_PRIVATE_GPA,
			       BE_RIGHT_READ | BE_RIGHT_WRITE) ==
	       BE_MODEL_ALLOWED);
	assert(be_model_access(&model, PROTECTED_PRIVATE_GPA,
			       BE_RIGHT_READ) == BE_MODEL_DENIED);
	assert(be_model_access(&model, SHARED_GPA,
			       BE_RIGHT_READ | BE_RIGHT_WRITE) ==
	       BE_MODEL_ALLOWED);
	assert(be_model_access(&model, SHARED_GPA,
			       BE_RIGHT_EXECUTE) == BE_MODEL_DENIED);
	assert(model.phase == BE_PHASE_ACTIVE);
	assert(be_model_cache_count(&model) == 2U);

	prepare_active(&model, BE_FIXTURE_SOURCE_B);
	assert(be_model_access(&model, MANAGEMENT_PRIVATE_GPA,
			       BE_RIGHT_READ | BE_RIGHT_WRITE) ==
	       BE_MODEL_ALLOWED);
	assert(be_model_access(&model, PROTECTED_PRIVATE_GPA,
			       BE_RIGHT_READ) == BE_MODEL_DENIED);
	assert(be_model_access(&model, SHARED_GPA,
			       BE_RIGHT_READ | BE_RIGHT_WRITE) ==
	       BE_MODEL_ALLOWED);
}

static void test_checked_switch_and_saved_state(void)
{
	struct be_model model;
	be_u64 value;

	prepare_active(&model, BE_FIXTURE_SOURCE_B);
	assert(model.selected_vmid == 0U);
	assert(be_model_write_register(&model, 0U, REGISTER_SENTINEL) ==
	       BE_MODEL_OK);
	assert(be_model_access(&model, SHARED_GPA,
			       BE_RIGHT_READ | BE_RIGHT_WRITE) ==
	       BE_MODEL_ALLOWED);
	assert(be_model_begin_switch(&model, BE_DOMAIN_PROTECTED) ==
	       BE_MODEL_OK);
	assert(model.phase == BE_PHASE_SWITCHING);
	assert(model.active_domain == BE_DOMAIN_INVALID);
	assert(model.pending_domain == BE_DOMAIN_PROTECTED);
	assert(model.selected_vmid == 0U);
	assert(model.fence_complete == 0U);
	assert(be_model_cache_count(&model) == 1U);
	assert(be_model_read_saved_register(
		       &model, BE_DOMAIN_MANAGEMENT, 0U, &value) ==
	       BE_MODEL_OK);
	assert(value == REGISTER_SENTINEL);
	assert(be_model_read_saved_register(
		       &model, BE_DOMAIN_PROTECTED, 0U, &value) ==
	       BE_MODEL_OK);
	assert(value == 0U);

	assert(be_model_complete_fence(&model) == BE_MODEL_OK);
	assert(model.fence_complete != 0U);
	assert(be_model_cache_count(&model) == 0U);
	assert(be_model_finish_switch(&model) == BE_MODEL_OK);
	assert(model.active_domain == BE_DOMAIN_PROTECTED);
	assert(be_model_read_register(&model, 0U, &value) == BE_MODEL_OK);
	assert(value == 0U);
	assert(be_model_access(&model, PROTECTED_PRIVATE_GPA,
			       BE_RIGHT_READ | BE_RIGHT_WRITE) ==
	       BE_MODEL_ALLOWED);
	assert(be_model_access(&model, MANAGEMENT_PRIVATE_GPA,
			       BE_RIGHT_READ) == BE_MODEL_DENIED);
	assert(be_model_access(&model, SHARED_GPA,
			       BE_RIGHT_READ) == BE_MODEL_ALLOWED);
	assert(be_model_access(&model, SHARED_GPA,
			       BE_RIGHT_READ | BE_RIGHT_WRITE) ==
	       BE_MODEL_DENIED);

	assert(be_model_write_register(&model, 0U, PROTECTED_SENTINEL) ==
	       BE_MODEL_OK);
	assert(be_model_begin_switch(&model, BE_DOMAIN_MANAGEMENT) ==
	       BE_MODEL_OK);
	assert(be_model_complete_fence(&model) == BE_MODEL_OK);
	assert(be_model_finish_switch(&model) == BE_MODEL_OK);
	assert(be_model_read_register(&model, 0U, &value) == BE_MODEL_OK);
	assert(value == REGISTER_SENTINEL);
	assert(be_model_read_saved_register(
		       &model, BE_DOMAIN_PROTECTED, 0U, &value) ==
	       BE_MODEL_OK);
	assert(value == PROTECTED_SENTINEL);
}

static void test_fail_closed_transitions_and_integrity(void)
{
	struct be_model model;

	prepare_active(&model, BE_FIXTURE_SOURCE_A);
	assert(be_model_begin_switch(&model, BE_DOMAIN_PROTECTED) ==
	       BE_MODEL_OK);
	assert(be_model_finish_switch(&model) == BE_MODEL_FAILED);
	assert(model.phase == BE_PHASE_FAILED);
	assert(be_model_complete_fence(&model) == BE_MODEL_FAILED);
	assert(be_model_access(&model, SHARED_GPA,
			       BE_RIGHT_READ) == BE_MODEL_FAILED);

	prepare_active(&model, BE_FIXTURE_SOURCE_A);
	assert(be_model_begin_switch(&model, BE_DOMAIN_MANAGEMENT) ==
	       BE_MODEL_FAILED);
	assert(model.phase == BE_PHASE_FAILED);

	prepare_active(&model, BE_FIXTURE_SOURCE_A);
	model.selected_root = 102U;
	assert(be_model_access(&model, MANAGEMENT_PRIVATE_GPA,
			       BE_RIGHT_READ) == BE_MODEL_FAILED);
	assert(model.check_result == BE_CHECK_BINDING);

	prepare_active(&model, BE_FIXTURE_SOURCE_A);
	model.canonical.authorities[0].rights |= BE_RIGHT_EXECUTE;
	assert(be_model_access(&model, MANAGEMENT_PRIVATE_GPA,
			       BE_RIGHT_READ) == BE_MODEL_FAILED);
	assert(model.check_result == BE_CHECK_EXCESS_RIGHTS);

	prepare_to_validated(&model, BE_FIXTURE_SOURCE_A);
	assert(be_model_derive_roots(&model) == BE_MODEL_FAILED);
	assert(model.check_result == BE_CHECK_INVALID_PHASE);
	assert(model.canonical.configuration_id == 0U);
}

int main(void)
{
	test_valid_inputs_and_source_independence();
	test_inventory_rejections();
	test_proposal_envelope_rejections();
	test_inventory_closure_and_resource_rejections();
	test_binding_rejections();
	test_channel_and_authority_rejections();
	test_canonical_and_derived_integrity();
	test_phases_copying_and_no_partial_publication();
	test_access_and_source_independent_behavior();
	test_checked_switch_and_saved_state();
	test_fail_closed_transitions_and_integrity();
	printf("Beryllium Architecture Model 0.2 unit tests: PASS\n");
	return 0;
}
