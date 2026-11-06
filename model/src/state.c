// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Executable state machine for the bounded Model 0.2 mechanism contract.
 *
 * Inventory, proposal, validation, sealing, derivation, and activation remain
 * distinct. The retained access and switch behavior can run only from state
 * derived from the sealed canonical authority.
 */
#include <be/state.h>

static enum be_model_result
fail_model(struct be_model *model, enum be_check_result result)
{
	if (model != (struct be_model *)0) {
		if (model->sealed == 0U) {
			model->canonical =
				(struct be_canonical_state){ 0 };
			model->enforcement =
				(struct be_enforcement_state){ 0 };
			model->validated_identity = 0U;
		}
		model->check_result = result;
		model->phase = BE_PHASE_FAILED;
		model->active_domain = BE_DOMAIN_INVALID;
		model->pending_domain = BE_DOMAIN_INVALID;
		model->fence_complete = 0U;
	}
	return BE_MODEL_FAILED;
}

static int domain_is_valid(enum be_domain_id domain)
{
	return domain == BE_DOMAIN_MANAGEMENT ||
	       domain == BE_DOMAIN_PROTECTED;
}

static int rights_are_valid(be_u32 rights)
{
	if (rights == 0U || (rights & ~(be_u32)BE_RIGHT_ALL) != 0U)
		return 0;
	if ((rights & BE_RIGHT_WRITE) != 0U &&
	    (rights & BE_RIGHT_READ) == 0U)
		return 0;
	return 1;
}

static const struct be_domain_desc *
model_domain(const struct be_model *model, enum be_domain_id domain)
{
	be_size index;

	for (index = 0U; index < model->canonical.domain_count; ++index) {
		if (model->canonical.domains[index].id == domain)
			return &model->canonical.domains[index];
	}
	return (const struct be_domain_desc *)0;
}

static const struct be_root_image *
model_root(const struct be_model *model, enum be_domain_id domain)
{
	be_size index;

	for (index = 0U; index < model->enforcement.root_count; ++index) {
		if (model->enforcement.roots[index].domain == domain)
			return &model->enforcement.roots[index];
	}
	return (const struct be_root_image *)0;
}

static struct be_saved_register_state *
model_saved_state(struct be_model *model, enum be_domain_id domain)
{
	be_size index;

	for (index = 0U; index < BE_MAX_SAVED_STATES; ++index) {
		if (model->saved[index].owner == domain)
			return &model->saved[index];
	}
	return (struct be_saved_register_state *)0;
}

static const struct be_saved_register_state *
model_saved_state_const(const struct be_model *model,
			enum be_domain_id domain)
{
	be_size index;

	for (index = 0U; index < BE_MAX_SAVED_STATES; ++index) {
		if (model->saved[index].owner == domain)
			return &model->saved[index];
	}
	return (const struct be_saved_register_state *)0;
}

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

static enum be_check_result
sealed_integrity_result(const struct be_model *model)
{
	enum be_check_result result;

	if (model->sealed == 0U || model->sealed_identity == 0U ||
	    model->canonical.configuration_id != model->sealed_identity)
		return BE_CHECK_INTEGRITY;
	result = be_check_canonical(&model->canonical);
	if (result != BE_CHECK_OK)
		return result;
	return BE_CHECK_OK;
}

static enum be_check_result
enforcement_integrity_result(const struct be_model *model)
{
	enum be_check_result result = sealed_integrity_result(model);

	if (result != BE_CHECK_OK)
		return result;
	return be_check_enforcement(&model->canonical, &model->enforcement);
}

static int selected_binding_is_valid(const struct be_model *model,
				     enum be_domain_id domain)
{
	const struct be_domain_desc *description = model_domain(model, domain);
	const struct be_root_image *root = model_root(model, domain);

	if (description == (const struct be_domain_desc *)0 ||
	    root == (const struct be_root_image *)0)
		return 0;
	return model->selected_vcpu == description->vcpu_id &&
	       model->selected_vcpu == root->vcpu_id &&
	       model->selected_root == description->root_id &&
	       model->selected_root == root->root_id &&
	       model->selected_vmid == description->vmid &&
	       model->selected_vmid == root->vmid &&
	       model->selected_stack == description->trusted_stack_frame &&
	       model->selected_stack == root->trusted_stack_frame &&
	       model->selected_saved_state == description->saved_state_id &&
	       model->selected_saved_state == root->saved_state_id &&
	       model->selected_saved_state_frame ==
		       description->saved_state_frame &&
	       model->selected_saved_state_frame == root->saved_state_frame;
}

static enum be_check_result
running_integrity_result(const struct be_model *model)
{
	enum be_check_result result = enforcement_integrity_result(model);

	if (result != BE_CHECK_OK)
		return result;
	if (model->phase != BE_PHASE_ACTIVE ||
	    model->fence_complete == 0U ||
	    !domain_is_valid(model->active_domain) ||
	    !selected_binding_is_valid(model, model->active_domain))
		return BE_CHECK_BINDING;
	return BE_CHECK_OK;
}

static void select_binding(struct be_model *model,
			   const struct be_domain_desc *domain)
{
	model->selected_vcpu = domain->vcpu_id;
	model->selected_root = domain->root_id;
	model->selected_vmid = domain->vmid;
	model->selected_stack = domain->trusted_stack_frame;
	model->selected_saved_state = domain->saved_state_id;
	model->selected_saved_state_frame = domain->saved_state_frame;
}

static void clear_registers(struct be_register_file *registers)
{
	be_size index;

	for (index = 0U; index < BE_MODEL_REGISTER_COUNT; ++index)
		registers->value[index] = 0U;
}

static void copy_registers(struct be_register_file *target,
			   const struct be_register_file *source)
{
	be_size index;

	for (index = 0U; index < BE_MODEL_REGISTER_COUNT; ++index)
		target->value[index] = source->value[index];
}

static void clear_cache(struct be_model *model)
{
	be_size index;

	for (index = 0U; index < BE_MAX_CACHE_ENTRIES; ++index) {
		model->cache[index].valid = 0U;
		model->cache[index].vmid = 0U;
		model->cache[index].gpa = 0U;
		model->cache[index].frame_id = 0U;
		model->cache[index].rights = 0U;
	}
}

static const struct be_cached_translation *
find_cached_translation(const struct be_model *model, be_u64 gpa)
{
	be_size index;

	for (index = 0U; index < BE_MAX_CACHE_ENTRIES; ++index) {
		if (model->cache[index].valid != 0U &&
		    model->cache[index].vmid == model->selected_vmid &&
		    model->cache[index].gpa == gpa)
			return &model->cache[index];
	}
	return (const struct be_cached_translation *)0;
}

static enum be_model_result
cache_translation(struct be_model *model,
		  const struct be_mapping_desc *mapping)
{
	be_size index;

	for (index = 0U; index < BE_MAX_CACHE_ENTRIES; ++index) {
		if (model->cache[index].valid == 0U) {
			model->cache[index].valid = 1U;
			model->cache[index].vmid = model->selected_vmid;
			model->cache[index].gpa = mapping->gpa;
			model->cache[index].frame_id = mapping->frame_id;
			model->cache[index].rights = mapping->rights;
			return BE_MODEL_ALLOWED;
		}
	}
	return fail_model(model, BE_CHECK_INCOMPLETE);
}

void be_model_reset(struct be_model *model)
{
	be_size index;

	if (model == (struct be_model *)0)
		return;
	*model = (struct be_model){ 0 };
	model->phase = BE_PHASE_EMPTY;
	model->check_result = BE_CHECK_INCOMPLETE;
	model->active_domain = BE_DOMAIN_INVALID;
	model->pending_domain = BE_DOMAIN_INVALID;
	for (index = 0U; index < BE_MAX_SAVED_STATES; ++index)
		model->saved[index].owner = BE_DOMAIN_INVALID;
}

enum be_model_result
be_model_bind_inventory(struct be_model *model,
			const struct be_platform_inventory *inventory)
{
	enum be_check_result result;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	if (model->phase != BE_PHASE_EMPTY)
		return fail_model(model, BE_CHECK_INVALID_PHASE);
	result = be_check_inventory(inventory);
	model->check_result = result;
	if (result != BE_CHECK_OK)
		return fail_model(model, result);
	model->inventory = *inventory;
	model->phase = BE_PHASE_INVENTORY_BOUND;
	return BE_MODEL_OK;
}

enum be_model_result
be_model_copy_proposal(struct be_model *model,
		       const struct be_proposal *proposal)
{
	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	if (model->phase != BE_PHASE_INVENTORY_BOUND)
		return fail_model(model, BE_CHECK_INVALID_PHASE);
	if (proposal == (const struct be_proposal *)0)
		return fail_model(model, BE_CHECK_NULL);
	model->proposal = *proposal;
	model->phase = BE_PHASE_PROPOSAL_COPIED;
	return BE_MODEL_OK;
}

enum be_model_result be_model_validate(struct be_model *model)
{
	enum be_check_result result;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	if (model->phase != BE_PHASE_PROPOSAL_COPIED)
		return fail_model(model, BE_CHECK_INVALID_PHASE);
	result = be_canonicalize(
		&model->inventory, &model->proposal, &model->canonical);
	model->check_result = result;
	if (result != BE_CHECK_OK)
		return fail_model(model, result);
	model->validated_identity = model->canonical.configuration_id;
	model->phase = BE_PHASE_VALIDATED;
	return BE_MODEL_OK;
}

enum be_model_result be_model_seal(struct be_model *model)
{
	enum be_check_result result;
	be_size index;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	if (model->phase != BE_PHASE_VALIDATED)
		return fail_model(model, BE_CHECK_INVALID_PHASE);
	if (!enforcement_is_empty(&model->enforcement) ||
	    model->active_domain != BE_DOMAIN_INVALID ||
	    model->pending_domain != BE_DOMAIN_INVALID)
		return fail_model(model, BE_CHECK_DIRECT_AUTHORITY);
	result = be_check_canonical(&model->canonical);
	if (result != BE_CHECK_OK ||
	    model->canonical.configuration_id !=
		    model->validated_identity)
		return fail_model(
			model, result == BE_CHECK_OK ?
				       BE_CHECK_INTEGRITY :
				       result);

	for (index = 0U; index < BE_MAX_SAVED_STATES; ++index) {
		model->saved[index].id =
			model->canonical.saved_states[index].id;
		model->saved[index].owner =
			model->canonical.saved_states[index].owner;
		model->saved[index].frame_id =
			model->canonical.saved_states[index].frame_id;
		clear_registers(&model->saved[index].registers);
	}
	clear_registers(&model->live_registers);
	clear_cache(model);
	model->sealed_identity = model->validated_identity;
	model->sealed = 1U;
	model->check_result = BE_CHECK_OK;
	model->phase = BE_PHASE_SEALED;
	return BE_MODEL_OK;
}

enum be_model_result be_model_derive_roots(struct be_model *model)
{
	enum be_check_result result;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	if (model->phase != BE_PHASE_SEALED)
		return fail_model(model, BE_CHECK_INVALID_PHASE);
	result = sealed_integrity_result(model);
	if (result != BE_CHECK_OK)
		return fail_model(model, result);
	if (!enforcement_is_empty(&model->enforcement)) {
		model->enforcement = (struct be_enforcement_state){ 0 };
		return fail_model(model, BE_CHECK_DIRECT_AUTHORITY);
	}
	result = be_derive_enforcement(
		&model->canonical, &model->enforcement);
	model->check_result = result;
	if (result != BE_CHECK_OK) {
		model->enforcement = (struct be_enforcement_state){ 0 };
		return fail_model(model, result);
	}
	model->phase = BE_PHASE_ROOTS_DERIVED;
	return BE_MODEL_OK;
}

enum be_model_result
be_model_activate(struct be_model *model, enum be_domain_id domain)
{
	const struct be_domain_desc *description;
	const struct be_saved_register_state *saved;
	enum be_check_result result;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	if (model->phase != BE_PHASE_ROOTS_DERIVED)
		return fail_model(model, BE_CHECK_INVALID_PHASE);
	if (!domain_is_valid(domain))
		return fail_model(model, BE_CHECK_BINDING);
	result = enforcement_integrity_result(model);
	if (result != BE_CHECK_OK)
		return fail_model(model, result);
	description = model_domain(model, domain);
	saved = model_saved_state_const(model, domain);
	if (description == (const struct be_domain_desc *)0 ||
	    saved == (const struct be_saved_register_state *)0)
		return fail_model(model, BE_CHECK_BINDING);

	select_binding(model, description);
	if (!selected_binding_is_valid(model, domain))
		return fail_model(model, BE_CHECK_BINDING);
	copy_registers(&model->live_registers, &saved->registers);
	model->active_domain = domain;
	model->pending_domain = BE_DOMAIN_INVALID;
	model->fence_complete = 1U;
	model->phase = BE_PHASE_ACTIVE;
	return BE_MODEL_OK;
}

enum be_model_result
be_model_access(struct be_model *model, be_u64 gpa, be_u32 rights)
{
	const struct be_cached_translation *cached;
	const struct be_root_image *root;
	enum be_check_result result;
	be_size index;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	if (model->phase == BE_PHASE_FAILED)
		return BE_MODEL_FAILED;
	result = running_integrity_result(model);
	if (result != BE_CHECK_OK)
		return fail_model(model, result);
	if ((gpa & (BE_PAGE_SIZE - BE_U64_C(1))) != 0U ||
	    !rights_are_valid(rights))
		return BE_MODEL_DENIED;

	cached = find_cached_translation(model, gpa);
	if (cached != (const struct be_cached_translation *)0)
		return (rights & ~cached->rights) == 0U ?
			       BE_MODEL_ALLOWED :
			       BE_MODEL_DENIED;

	root = model_root(model, model->active_domain);
	if (root == (const struct be_root_image *)0)
		return fail_model(model, BE_CHECK_BINDING);
	for (index = 0U; index < root->mapping_count; ++index) {
		const struct be_mapping_desc *mapping = &root->mappings[index];

		if (mapping->gpa != gpa)
			continue;
		if ((rights & ~mapping->rights) != 0U)
			return BE_MODEL_DENIED;
		return cache_translation(model, mapping);
	}
	return BE_MODEL_DENIED;
}

enum be_model_result
be_model_write_register(struct be_model *model, be_size index, be_u64 value)
{
	enum be_check_result result;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	result = running_integrity_result(model);
	if (result != BE_CHECK_OK || index >= BE_MODEL_REGISTER_COUNT)
		return fail_model(
			model, result == BE_CHECK_OK ?
				       BE_CHECK_UNSUPPORTED :
				       result);
	model->live_registers.value[index] = value;
	return BE_MODEL_OK;
}

enum be_model_result
be_model_read_register(struct be_model *model, be_size index, be_u64 *value)
{
	enum be_check_result result;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	result = running_integrity_result(model);
	if (result != BE_CHECK_OK || index >= BE_MODEL_REGISTER_COUNT ||
	    value == (be_u64 *)0)
		return fail_model(
			model, result == BE_CHECK_OK ?
				       BE_CHECK_UNSUPPORTED :
				       result);
	*value = model->live_registers.value[index];
	return BE_MODEL_OK;
}

enum be_model_result
be_model_read_saved_register(const struct be_model *model,
			     enum be_domain_id domain, be_size index,
			     be_u64 *value)
{
	const struct be_saved_register_state *saved;

	if (model == (const struct be_model *)0 ||
	    model->sealed == 0U || !domain_is_valid(domain) ||
	    index >= BE_MODEL_REGISTER_COUNT || value == (be_u64 *)0 ||
	    sealed_integrity_result(model) != BE_CHECK_OK)
		return BE_MODEL_FAILED;
	saved = model_saved_state_const(model, domain);
	if (saved == (const struct be_saved_register_state *)0)
		return BE_MODEL_FAILED;
	*value = saved->registers.value[index];
	return BE_MODEL_OK;
}

enum be_model_result
be_model_begin_switch(struct be_model *model, enum be_domain_id target)
{
	const struct be_domain_desc *description;
	struct be_saved_register_state *source;
	enum be_check_result result;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	result = running_integrity_result(model);
	if (result != BE_CHECK_OK || !domain_is_valid(target) ||
	    target == model->active_domain)
		return fail_model(
			model, result == BE_CHECK_OK ?
				       BE_CHECK_BINDING :
				       result);
	description = model_domain(model, target);
	source = model_saved_state(model, model->active_domain);
	if (description == (const struct be_domain_desc *)0 ||
	    source == (struct be_saved_register_state *)0)
		return fail_model(model, BE_CHECK_BINDING);

	copy_registers(&source->registers, &model->live_registers);
	clear_registers(&model->live_registers);
	model->pending_domain = target;
	model->active_domain = BE_DOMAIN_INVALID;
	select_binding(model, description);
	model->fence_complete = 0U;
	model->phase = BE_PHASE_SWITCHING;
	if (!selected_binding_is_valid(model, target))
		return fail_model(model, BE_CHECK_BINDING);
	return BE_MODEL_OK;
}

enum be_model_result be_model_complete_fence(struct be_model *model)
{
	enum be_check_result result;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	if (model->phase != BE_PHASE_SWITCHING)
		return fail_model(model, BE_CHECK_INVALID_PHASE);
	result = enforcement_integrity_result(model);
	if (result != BE_CHECK_OK ||
	    !domain_is_valid(model->pending_domain) ||
	    !selected_binding_is_valid(model, model->pending_domain) ||
	    model->fence_complete != 0U)
		return fail_model(
			model, result == BE_CHECK_OK ?
				       BE_CHECK_BINDING :
				       result);
	clear_cache(model);
	model->fence_complete = 1U;
	return BE_MODEL_OK;
}

enum be_model_result be_model_finish_switch(struct be_model *model)
{
	const struct be_saved_register_state *target;
	enum be_check_result result;

	if (model == (struct be_model *)0)
		return BE_MODEL_FAILED;
	if (model->phase != BE_PHASE_SWITCHING)
		return fail_model(model, BE_CHECK_INVALID_PHASE);
	result = enforcement_integrity_result(model);
	if (result != BE_CHECK_OK || model->fence_complete == 0U ||
	    !domain_is_valid(model->pending_domain) ||
	    !selected_binding_is_valid(model, model->pending_domain))
		return fail_model(
			model, result == BE_CHECK_OK ?
				       BE_CHECK_BINDING :
				       result);
	target = model_saved_state_const(model, model->pending_domain);
	if (target == (const struct be_saved_register_state *)0)
		return fail_model(model, BE_CHECK_BINDING);
	copy_registers(&model->live_registers, &target->registers);
	model->active_domain = model->pending_domain;
	model->pending_domain = BE_DOMAIN_INVALID;
	model->phase = BE_PHASE_ACTIVE;
	return BE_MODEL_OK;
}

be_size be_model_cache_count(const struct be_model *model)
{
	be_size count = 0U;
	be_size index;

	if (model == (const struct be_model *)0)
		return 0U;
	for (index = 0U; index < BE_MAX_CACHE_ENTRIES; ++index) {
		if (model->cache[index].valid != 0U)
			++count;
	}
	return count;
}

const char *be_model_phase_name(enum be_model_phase phase)
{
	switch (phase) {
	case BE_PHASE_EMPTY:
		return "empty";
	case BE_PHASE_INVENTORY_BOUND:
		return "inventory-bound";
	case BE_PHASE_PROPOSAL_COPIED:
		return "proposal-copied";
	case BE_PHASE_VALIDATED:
		return "validated";
	case BE_PHASE_SEALED:
		return "sealed";
	case BE_PHASE_ROOTS_DERIVED:
		return "roots-derived";
	case BE_PHASE_ACTIVE:
		return "active";
	case BE_PHASE_SWITCHING:
		return "switching";
	case BE_PHASE_FAILED:
		return "failed";
	default:
		return "invalid";
	}
}

const char *be_model_result_name(enum be_model_result result)
{
	switch (result) {
	case BE_MODEL_OK:
		return "ok";
	case BE_MODEL_ALLOWED:
		return "allowed";
	case BE_MODEL_DENIED:
		return "denied";
	case BE_MODEL_FAILED:
		return "failed";
	default:
		return "invalid";
	}
}
