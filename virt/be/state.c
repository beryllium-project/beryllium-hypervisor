// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: fail-closed R1 runtime phase machine for copied, validated, sealed,
 *          derived, and reported Beryllium mechanism state.
 * Trust:   non-privileged control implementation only. No copied or mutated
 *          state becomes authoritative unless all checks succeed.
 * Scope:   accepted R1 non-privileged mechanism only. This component performs
 *          no privileged instruction, page-table, trap, or boot work.
 */
#include <be/state.h>

static int enforcement_is_empty(const struct be_enforcement_state *state)
{
	be_size root_index;

	if (state->configuration_id != 0U || state->root_count != 0U)
		return 0;
	for (root_index = 0U; root_index < BE_MAX_ROOTS; ++root_index) {
		const struct be_root_image *root = &state->roots[root_index];
		be_size mapping_index;

		if (root->root_id != 0U || root->root_table_frame != 0U ||
		    root->domain != BE_DOMAIN_INVALID ||
		    root->vcpu_id != 0U || root->vmid != 0U ||
		    root->trusted_stack_frame != 0U ||
		    root->saved_state_id != 0U ||
		    root->saved_state_frame != 0U ||
		    root->mapping_count != 0U)
			return 0;
		for (mapping_index = 0U;
		     mapping_index < BE_MAX_MAPPINGS; ++mapping_index) {
			const struct be_mapping_desc *mapping =
				&root->mappings[mapping_index];

			if (mapping->gpa != 0U || mapping->frame_id != 0U ||
			    mapping->rights != 0U)
				return 0;
		}
	}
	return 1;
}

static enum be_runtime_result
fail_runtime(struct be_runtime *runtime, enum be_check_result result)
{
	if (runtime != (struct be_runtime *)0) {
		if (runtime->sealed == 0U) {
			runtime->canonical = (struct be_canonical_state){ 0 };
			runtime->enforcement = (struct be_enforcement_state){ 0 };
			runtime->validated_identity = 0U;
			runtime->sealed_identity = 0U;
		} else {
			runtime->enforcement = (struct be_enforcement_state){ 0 };
		}
		runtime->check_result = result;
		runtime->phase = BE_RUNTIME_PHASE_FAILED;
	}
	return BE_RUNTIME_FAILED;
}

static enum be_check_result sealed_integrity_result(
	const struct be_runtime *runtime)
{
	enum be_check_result result;

	if (runtime->sealed == 0U || runtime->validated_identity == 0U ||
	    runtime->sealed_identity == 0U ||
	    runtime->validated_identity != runtime->sealed_identity ||
	    runtime->canonical.configuration_id != runtime->sealed_identity)
		return BE_CHECK_INTEGRITY;
	result = be_check_canonical(&runtime->canonical);
	if (result != BE_CHECK_OK)
		return result;
	return BE_CHECK_OK;
}

static enum be_check_result enforcement_integrity_result(
	const struct be_runtime *runtime)
{
	enum be_check_result result = sealed_integrity_result(runtime);

	if (result != BE_CHECK_OK)
		return result;
	return be_check_enforcement(&runtime->canonical,
				    &runtime->enforcement);
}

enum be_runtime_result
be_runtime_copy_inventory(struct be_runtime *runtime,
			  const struct be_platform_inventory *inventory)
{
	if (runtime == (struct be_runtime *)0)
		return BE_RUNTIME_FAILED;
	if (runtime->phase == BE_RUNTIME_PHASE_FAILED)
		return BE_RUNTIME_FAILED;
	if (runtime->phase != BE_RUNTIME_PHASE_EMPTY)
		return fail_runtime(runtime, BE_CHECK_INVALID_PHASE);
	if (inventory == (const struct be_platform_inventory *)0)
		return fail_runtime(runtime, BE_CHECK_NULL);

	runtime->inventory = *inventory;
	runtime->proposal = (struct be_proposal){ 0 };
	runtime->canonical = (struct be_canonical_state){ 0 };
	runtime->enforcement = (struct be_enforcement_state){ 0 };
	runtime->validated_identity = 0U;
	runtime->sealed_identity = 0U;
	runtime->sealed = 0U;
	runtime->phase = BE_RUNTIME_PHASE_INVENTORY_COPIED;
	runtime->check_result = BE_CHECK_INCOMPLETE;
	return BE_RUNTIME_OK;
}

enum be_runtime_result
be_runtime_copy_proposal(struct be_runtime *runtime,
			 const struct be_proposal *proposal)
{
	if (runtime == (struct be_runtime *)0)
		return BE_RUNTIME_FAILED;
	if (runtime->phase == BE_RUNTIME_PHASE_FAILED)
		return BE_RUNTIME_FAILED;
	if (runtime->phase != BE_RUNTIME_PHASE_INVENTORY_COPIED)
		return fail_runtime(runtime, BE_CHECK_INVALID_PHASE);
	if (proposal == (const struct be_proposal *)0)
		return fail_runtime(runtime, BE_CHECK_NULL);

	runtime->proposal = *proposal;
	runtime->canonical = (struct be_canonical_state){ 0 };
	runtime->enforcement = (struct be_enforcement_state){ 0 };
	runtime->validated_identity = 0U;
	runtime->sealed_identity = 0U;
	runtime->sealed = 0U;
	runtime->phase = BE_RUNTIME_PHASE_PROPOSAL_COPIED;
	runtime->check_result = BE_CHECK_INCOMPLETE;
	return BE_RUNTIME_OK;
}

enum be_runtime_result be_runtime_validate(struct be_runtime *runtime)
{
	enum be_check_result result;
	struct be_canonical_state candidate = { 0 };

	if (runtime == (struct be_runtime *)0)
		return BE_RUNTIME_FAILED;
	if (runtime->phase == BE_RUNTIME_PHASE_FAILED)
		return BE_RUNTIME_FAILED;
	if (runtime->phase != BE_RUNTIME_PHASE_PROPOSAL_COPIED)
		return fail_runtime(runtime, BE_CHECK_INVALID_PHASE);

	result = be_check_inventory(&runtime->inventory);
	if (result != BE_CHECK_OK)
		return fail_runtime(runtime, result);
	result = be_canonicalize(&runtime->inventory, &runtime->proposal,
				 &candidate);
	if (result != BE_CHECK_OK)
		return fail_runtime(runtime, result);

	runtime->canonical = candidate;
	runtime->enforcement = (struct be_enforcement_state){ 0 };
	runtime->validated_identity = candidate.configuration_id;
	runtime->sealed_identity = 0U;
	runtime->sealed = 0U;
	runtime->check_result = BE_CHECK_OK;
	runtime->phase = BE_RUNTIME_PHASE_VALIDATED;
	return BE_RUNTIME_OK;
}

enum be_runtime_result be_runtime_seal(struct be_runtime *runtime)
{
	enum be_check_result result;

	if (runtime == (struct be_runtime *)0)
		return BE_RUNTIME_FAILED;
	if (runtime->phase == BE_RUNTIME_PHASE_FAILED)
		return BE_RUNTIME_FAILED;
	if (runtime->phase != BE_RUNTIME_PHASE_VALIDATED)
		return fail_runtime(runtime, BE_CHECK_INVALID_PHASE);
	if (runtime->sealed != 0U || runtime->sealed_identity != 0U)
		return fail_runtime(runtime, BE_CHECK_INTEGRITY);
	if (!enforcement_is_empty(&runtime->enforcement))
		return fail_runtime(runtime, BE_CHECK_DIRECT_AUTHORITY);

	result = be_check_canonical(&runtime->canonical);
	if (result != BE_CHECK_OK)
		return fail_runtime(runtime, result);
	if (runtime->validated_identity == 0U ||
	    runtime->canonical.configuration_id != runtime->validated_identity)
		return fail_runtime(runtime, BE_CHECK_INTEGRITY);

	runtime->sealed_identity = runtime->validated_identity;
	runtime->sealed = 1U;
	runtime->check_result = BE_CHECK_OK;
	runtime->phase = BE_RUNTIME_PHASE_SEALED;
	return BE_RUNTIME_OK;
}

enum be_runtime_result be_runtime_derive(struct be_runtime *runtime)
{
	enum be_check_result result;
	struct be_enforcement_state candidate = { 0 };

	if (runtime == (struct be_runtime *)0)
		return BE_RUNTIME_FAILED;
	if (runtime->phase == BE_RUNTIME_PHASE_FAILED)
		return BE_RUNTIME_FAILED;
	if (runtime->phase != BE_RUNTIME_PHASE_SEALED)
		return fail_runtime(runtime, BE_CHECK_INVALID_PHASE);

	result = sealed_integrity_result(runtime);
	if (result != BE_CHECK_OK)
		return fail_runtime(runtime, result);
	if (!enforcement_is_empty(&runtime->enforcement))
		return fail_runtime(runtime, BE_CHECK_DIRECT_AUTHORITY);
	result = be_derive_enforcement(&runtime->canonical, &candidate);
	if (result != BE_CHECK_OK)
		return fail_runtime(runtime, result);
	result = be_check_enforcement(&runtime->canonical, &candidate);
	if (result != BE_CHECK_OK)
		return fail_runtime(runtime, result);

	runtime->enforcement = candidate;
	runtime->check_result = BE_CHECK_OK;
	runtime->phase = BE_RUNTIME_PHASE_DERIVED;
	return BE_RUNTIME_OK;
}

enum be_runtime_result
be_runtime_report(struct be_runtime *runtime, struct be_runtime_report *report)
{
	enum be_check_result result;
	be_size index;
	be_size mapping_count = 0U;

	if (report != (struct be_runtime_report *)0)
		*report = (struct be_runtime_report){ 0 };
	if (runtime == (struct be_runtime *)0)
		return BE_RUNTIME_FAILED;
	if (runtime->phase == BE_RUNTIME_PHASE_FAILED)
		return BE_RUNTIME_FAILED;
	if (report == (struct be_runtime_report *)0)
		return fail_runtime(runtime, BE_CHECK_NULL);
	if (runtime->phase != BE_RUNTIME_PHASE_DERIVED)
		return fail_runtime(runtime, BE_CHECK_INVALID_PHASE);

	result = enforcement_integrity_result(runtime);
	if (result != BE_CHECK_OK)
		return fail_runtime(runtime, result);
	for (index = 0U; index < runtime->enforcement.root_count; ++index)
		mapping_count += runtime->enforcement.roots[index].mapping_count;

	report->schema_version = BE_R1_REPORT_SCHEMA_VERSION;
	report->phase = runtime->phase;
	report->check_result = runtime->check_result;
	report->configuration_id = runtime->sealed_identity;
	report->frame_count = runtime->canonical.frame_count;
	report->authority_count = runtime->canonical.authority_count;
	report->root_count = runtime->enforcement.root_count;
	report->mapping_count = mapping_count;
	report->sealed = runtime->sealed;
	return BE_RUNTIME_OK;
}

const char *be_runtime_phase_name(enum be_runtime_phase phase)
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

const char *be_runtime_result_name(enum be_runtime_result result)
{
	switch (result) {
	case BE_RUNTIME_OK:
		return "ok";
	case BE_RUNTIME_FAILED:
		return "failed";
	default:
		return "invalid";
	}
}
