// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Policy-neutral validator, canonicalizer, and root derivation for Model 0.2.
 *
 * The host implementation copies no proposal field into authority without
 * inventory closure and complete structural validation. Canonical and derived
 * outputs remain zero until their respective operations succeed.
 */
#include <be/manifest.h>

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

static int resource_extent_is_valid(const struct be_resource_desc *resource)
{
	if (resource->id == 0U || resource->size == 0U)
		return 0;
	if ((resource->base & (BE_PAGE_SIZE - BE_U64_C(1))) != 0U ||
	    (resource->size & (BE_PAGE_SIZE - BE_U64_C(1))) != 0U)
		return 0;
	if (resource->base + resource->size < resource->base)
		return 0;
	return 1;
}

static int frame_extent_is_valid(const struct be_frame_desc *frame)
{
	struct be_resource_desc resource = {
		.id = frame->id,
		.base = frame->base,
		.size = frame->size,
		.kind = BE_RESOURCE_ASSIGNABLE,
	};

	return resource_extent_is_valid(&resource);
}

static int resource_extents_overlap(const struct be_resource_desc *left,
				    const struct be_resource_desc *right)
{
	be_u64 left_end = left->base + left->size;
	be_u64 right_end = right->base + right->size;

	return left->base < right_end && right->base < left_end;
}

static int frame_extents_overlap(const struct be_frame_desc *left,
				 const struct be_frame_desc *right)
{
	be_u64 left_end = left->base + left->size;
	be_u64 right_end = right->base + right->size;

	return left->base < right_end && right->base < left_end;
}

static const struct be_resource_desc *
find_resource(const struct be_platform_inventory *inventory, be_u32 id)
{
	be_size index;

	for (index = 0U; index < inventory->resource_count; ++index) {
		if (inventory->resources[index].id == id)
			return &inventory->resources[index];
	}
	return (const struct be_resource_desc *)0;
}

static const struct be_resource_request *
find_resource_request(const struct be_proposal *proposal, be_u32 id)
{
	be_size index;

	for (index = 0U; index < proposal->resource_count; ++index) {
		if (proposal->resources[index].resource_id == id)
			return &proposal->resources[index];
	}
	return (const struct be_resource_request *)0;
}

static const struct be_domain_request *
find_domain_request(const struct be_proposal *proposal,
		    enum be_domain_id domain)
{
	be_size index;

	for (index = 0U; index < proposal->domain_count; ++index) {
		if (proposal->domains[index].id == domain)
			return &proposal->domains[index];
	}
	return (const struct be_domain_request *)0;
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

static const struct be_domain_desc *
find_domain(const struct be_canonical_state *canonical,
	    enum be_domain_id domain)
{
	be_size index;

	for (index = 0U; index < canonical->domain_count; ++index) {
		if (canonical->domains[index].id == domain)
			return &canonical->domains[index];
	}
	return (const struct be_domain_desc *)0;
}

static const struct be_authority_desc *
find_authority(const struct be_canonical_state *canonical,
	       enum be_domain_id domain, be_u64 gpa, be_u32 frame_id)
{
	be_size index;

	for (index = 0U; index < canonical->authority_count; ++index) {
		const struct be_authority_desc *authority =
			&canonical->authorities[index];

		if (authority->domain == domain && authority->gpa == gpa &&
		    authority->frame_id == frame_id)
			return authority;
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

static enum be_frame_class
fixed_frame_class(enum be_resource_kind kind)
{
	switch (kind) {
	case BE_RESOURCE_MONITOR_CODE:
		return BE_FRAME_MONITOR_CODE;
	case BE_RESOURCE_MONITOR_DATA:
		return BE_FRAME_MONITOR_DATA;
	case BE_RESOURCE_ROOT_TABLE:
		return BE_FRAME_ROOT_TABLE;
	case BE_RESOURCE_TRUSTED_STACK:
		return BE_FRAME_TRUSTED_STACK;
	case BE_RESOURCE_SAVED_STATE:
		return BE_FRAME_SAVED_STATE;
	default:
		return BE_FRAME_INVALID;
	}
}

static be_u32 owner_mask_for(enum be_domain_id owner)
{
	if (owner == BE_DOMAIN_MANAGEMENT)
		return BE_OWNER_MANAGEMENT;
	if (owner == BE_DOMAIN_PROTECTED)
		return BE_OWNER_PROTECTED;
	return 0U;
}

static int authority_before(const struct be_authority_desc *left,
			    const struct be_authority_desc *right)
{
	if (left->domain != right->domain)
		return left->domain < right->domain;
	if (left->gpa != right->gpa)
		return left->gpa < right->gpa;
	return left->frame_id < right->frame_id;
}

static void sort_frames(struct be_canonical_state *canonical)
{
	be_size index;

	for (index = 1U; index < canonical->frame_count; ++index) {
		struct be_frame_desc value = canonical->frames[index];
		be_size position = index;

		while (position > 0U &&
		       value.id < canonical->frames[position - 1U].id) {
			canonical->frames[position] =
				canonical->frames[position - 1U];
			--position;
		}
		canonical->frames[position] = value;
	}
}

static void sort_authorities(struct be_canonical_state *canonical)
{
	be_size index;

	for (index = 1U; index < canonical->authority_count; ++index) {
		struct be_authority_desc value =
			canonical->authorities[index];
		be_size position = index;

		while (position > 0U &&
		       authority_before(
			       &value,
			       &canonical->authorities[position - 1U])) {
			canonical->authorities[position] =
				canonical->authorities[position - 1U];
			--position;
		}
		canonical->authorities[position] = value;
	}
}

enum be_check_result
be_check_inventory(const struct be_platform_inventory *inventory)
{
	be_size index;
	be_size other;
	be_size monitor_code = 0U;
	be_size monitor_data = 0U;
	be_size root_table = 0U;
	be_size trusted_stack = 0U;
	be_size saved_state = 0U;
	be_size assignable = 0U;

	if (inventory == (const struct be_platform_inventory *)0)
		return BE_CHECK_NULL;
	if (inventory->model_version != BE_MODEL_VERSION ||
	    inventory->architecture != BE_ARCH_RISCV64 ||
	    inventory->profile !=
		    BE_PROFILE_POLICY_NEUTRAL_SINGLE_HART_TWO_DOMAIN ||
	    inventory->hart_id != BE_MODEL_HART_ID)
		return BE_CHECK_UNSUPPORTED;
	if (inventory->resource_count != BE_MAX_RESOURCES)
		return BE_CHECK_INCOMPLETE;

	for (index = 0U; index < inventory->resource_count; ++index) {
		const struct be_resource_desc *resource =
			&inventory->resources[index];

		if (!resource_extent_is_valid(resource) ||
		    resource->kind <= BE_RESOURCE_INVALID ||
		    resource->kind >= BE_RESOURCE_KIND_COUNT)
			return BE_CHECK_UNSUPPORTED;
	}
	for (index = 0U; index < inventory->resource_count; ++index) {
		for (other = index + 1U; other < inventory->resource_count;
		     ++other) {
			if (inventory->resources[index].id ==
			    inventory->resources[other].id)
				return BE_CHECK_DUPLICATE_RESOURCE;
		}
	}
	for (index = 0U; index < inventory->resource_count; ++index) {
		for (other = index + 1U; other < inventory->resource_count;
		     ++other) {
			if (resource_extents_overlap(
				    &inventory->resources[index],
				    &inventory->resources[other]))
				return BE_CHECK_OVERLAPPING_RESOURCE;
		}
	}

	for (index = 0U; index < inventory->resource_count; ++index) {
		switch (inventory->resources[index].kind) {
		case BE_RESOURCE_MONITOR_CODE:
			++monitor_code;
			break;
		case BE_RESOURCE_MONITOR_DATA:
			++monitor_data;
			break;
		case BE_RESOURCE_ROOT_TABLE:
			++root_table;
			break;
		case BE_RESOURCE_TRUSTED_STACK:
			++trusted_stack;
			break;
		case BE_RESOURCE_SAVED_STATE:
			++saved_state;
			break;
		case BE_RESOURCE_ASSIGNABLE:
			++assignable;
			break;
		default:
			return BE_CHECK_UNSUPPORTED;
		}
	}
	if (monitor_code != 1U || monitor_data != 1U ||
	    root_table != BE_MAX_ROOTS ||
	    trusted_stack != BE_MAX_DOMAINS ||
	    saved_state != BE_MAX_SAVED_STATES || assignable != 3U)
		return BE_CHECK_INCOMPLETE;
	return BE_CHECK_OK;
}

static enum be_check_result
canonicalize_frames(const struct be_platform_inventory *inventory,
		    const struct be_proposal *proposal,
		    struct be_canonical_state *canonical)
{
	be_size index;
	be_size other;

	for (index = 0U; index < proposal->resource_count; ++index) {
		const struct be_resource_request *request =
			&proposal->resources[index];
		const struct be_resource_desc *resource =
			find_resource(inventory, request->resource_id);
		enum be_frame_class fixed;
		struct be_frame_desc *frame = &canonical->frames[index];

		if (resource == (const struct be_resource_desc *)0 ||
		    request->base != resource->base ||
		    request->size != resource->size)
			return BE_CHECK_INVENTORY_CLOSURE;
		for (other = index + 1U; other < proposal->resource_count;
		     ++other) {
			if (request->resource_id ==
			    proposal->resources[other].resource_id)
				return BE_CHECK_DUPLICATE_RESOURCE;
		}

		fixed = fixed_frame_class(resource->kind);
		if (fixed != BE_FRAME_INVALID) {
			if (request->class != fixed ||
			    request->owner != BE_DOMAIN_INVALID)
				return BE_CHECK_EXCLUDED_MAPPING;
			frame->owner_mask = BE_OWNER_MONITOR;
		} else if (resource->kind == BE_RESOURCE_ASSIGNABLE &&
			   request->class == BE_FRAME_PRIVATE) {
			if (!domain_is_valid(request->owner))
				return BE_CHECK_PRIVATE_OWNER;
			frame->owner_mask = owner_mask_for(request->owner);
		} else if (resource->kind == BE_RESOURCE_ASSIGNABLE &&
			   request->class == BE_FRAME_SHARED) {
			if (request->owner != BE_DOMAIN_INVALID)
				return BE_CHECK_UNDECLARED_SHARED;
			frame->owner_mask = 0U;
		} else {
			return BE_CHECK_EXCLUDED_MAPPING;
		}

		frame->id = resource->id;
		frame->base = resource->base;
		frame->size = resource->size;
		frame->class = request->class;
	}
	for (index = 0U; index < inventory->resource_count; ++index) {
		if (find_resource_request(
			    proposal, inventory->resources[index].id) ==
		    (const struct be_resource_request *)0)
			return BE_CHECK_INVENTORY_CLOSURE;
	}
	canonical->frame_count = proposal->resource_count;
	sort_frames(canonical);
	return BE_CHECK_OK;
}

static enum be_check_result
canonicalize_domains(const struct be_platform_inventory *inventory,
		     const struct be_proposal *proposal,
		     struct be_canonical_state *canonical)
{
	static const enum be_domain_id domain_order[BE_MAX_DOMAINS] = {
		BE_DOMAIN_MANAGEMENT,
		BE_DOMAIN_PROTECTED,
	};
	be_size index;
	be_size other;

	for (index = 0U; index < proposal->domain_count; ++index) {
		if (!domain_is_valid(proposal->domains[index].id))
			return BE_CHECK_UNSUPPORTED;
		for (other = index + 1U; other < proposal->domain_count;
		     ++other) {
			if (proposal->domains[index].id ==
			    proposal->domains[other].id)
				return BE_CHECK_BINDING;
		}
	}

	for (index = 0U; index < BE_MAX_DOMAINS; ++index) {
		const struct be_domain_request *request =
			find_domain_request(proposal, domain_order[index]);
		const struct be_resource_desc *root_resource;
		const struct be_resource_desc *stack_resource;
		const struct be_resource_desc *saved_resource;
		struct be_domain_desc *domain = &canonical->domains[index];
		struct be_saved_state_desc *saved =
			&canonical->saved_states[index];

		if (request == (const struct be_domain_request *)0)
			return BE_CHECK_INCOMPLETE;
		if (request->vcpu_id == 0U || request->root_id == 0U ||
		    request->root_resource_id == 0U ||
		    request->trusted_stack_resource_id == 0U ||
		    request->saved_state_id == 0U ||
		    request->saved_state_resource_id == 0U ||
		    request->vmid > 0x3fffU)
			return BE_CHECK_UNSUPPORTED;

		root_resource =
			find_resource(inventory, request->root_resource_id);
		stack_resource = find_resource(
			inventory, request->trusted_stack_resource_id);
		saved_resource = find_resource(
			inventory, request->saved_state_resource_id);
		if (root_resource == (const struct be_resource_desc *)0 ||
		    root_resource->kind != BE_RESOURCE_ROOT_TABLE ||
		    stack_resource == (const struct be_resource_desc *)0 ||
		    stack_resource->kind != BE_RESOURCE_TRUSTED_STACK ||
		    saved_resource == (const struct be_resource_desc *)0 ||
		    saved_resource->kind != BE_RESOURCE_SAVED_STATE)
			return BE_CHECK_BINDING;

		domain->id = request->id;
		domain->vcpu_id = request->vcpu_id;
		domain->root_id = request->root_id;
		domain->root_table_frame = request->root_resource_id;
		domain->vmid = request->vmid;
		domain->trusted_stack_frame =
			request->trusted_stack_resource_id;
		domain->saved_state_id = request->saved_state_id;
		domain->saved_state_frame =
			request->saved_state_resource_id;
		saved->id = request->saved_state_id;
		saved->owner = request->id;
		saved->frame_id = request->saved_state_resource_id;
	}

	for (index = 0U; index < BE_MAX_DOMAINS; ++index) {
		for (other = index + 1U; other < BE_MAX_DOMAINS; ++other) {
			const struct be_domain_desc *left =
				&canonical->domains[index];
			const struct be_domain_desc *right =
				&canonical->domains[other];

			if (left->vcpu_id == right->vcpu_id ||
			    left->root_id == right->root_id ||
			    left->root_table_frame ==
				    right->root_table_frame ||
			    left->trusted_stack_frame ==
				    right->trusted_stack_frame ||
			    left->saved_state_id == right->saved_state_id ||
			    left->saved_state_frame ==
				    right->saved_state_frame)
				return BE_CHECK_BINDING;
		}
	}
	canonical->domain_count = BE_MAX_DOMAINS;
	canonical->saved_state_count = BE_MAX_SAVED_STATES;
	return BE_CHECK_OK;
}

static enum be_check_result
canonicalize_channel(const struct be_proposal *proposal,
		     struct be_canonical_state *canonical)
{
	const struct be_channel_request *request = &proposal->channels[0];
	const struct be_frame_desc *frame =
		find_frame(canonical, request->resource_id);
	struct be_channel_desc *channel = &canonical->channels[0];

	if (request->id == 0U ||
	    request->source != BE_DOMAIN_MANAGEMENT ||
	    request->target != BE_DOMAIN_PROTECTED ||
	    request->source == request->target ||
	    request->source_rights !=
		    (BE_RIGHT_READ | BE_RIGHT_WRITE) ||
	    request->target_rights != BE_RIGHT_READ)
		return BE_CHECK_CHANNEL_RIGHTS;
	if (frame == (const struct be_frame_desc *)0 ||
	    frame->class != BE_FRAME_SHARED || frame->owner_mask != 0U)
		return BE_CHECK_UNDECLARED_SHARED;

	channel->id = request->id;
	channel->source = request->source;
	channel->target = request->target;
	channel->frame_id = request->resource_id;
	channel->source_rights = request->source_rights;
	channel->target_rights = request->target_rights;
	canonical->channel_count = BE_MAX_CHANNELS;
	return BE_CHECK_OK;
}

static enum be_check_result
canonicalize_authorities(const struct be_proposal *proposal,
			 struct be_canonical_state *canonical)
{
	const struct be_channel_desc *channel = &canonical->channels[0];
	be_size index;
	be_size other;

	for (index = 0U; index < proposal->authority_count; ++index) {
		const struct be_authority_request *request =
			&proposal->authorities[index];
		const struct be_frame_desc *frame =
			find_frame(canonical, request->resource_id);
		struct be_authority_desc *authority =
			&canonical->authorities[index];
		be_u32 expected_owner;

		if (!domain_is_valid(request->domain) ||
		    (request->gpa & (BE_PAGE_SIZE - BE_U64_C(1))) != 0U ||
		    !rights_are_valid(request->rights))
			return BE_CHECK_UNSUPPORTED;
		if (frame == (const struct be_frame_desc *)0)
			return BE_CHECK_INVENTORY_CLOSURE;
		if (frame->class != BE_FRAME_PRIVATE &&
		    frame->class != BE_FRAME_SHARED)
			return BE_CHECK_EXCLUDED_MAPPING;

		expected_owner = owner_mask_for(request->domain);
		if (frame->class == BE_FRAME_PRIVATE &&
		    frame->owner_mask != expected_owner)
			return BE_CHECK_PRIVATE_OWNER;
		if (frame->class == BE_FRAME_SHARED) {
			be_u32 expected_rights;

			if (frame->id != channel->frame_id)
				return BE_CHECK_UNDECLARED_SHARED;
			if (request->domain == channel->source)
				expected_rights = channel->source_rights;
			else if (request->domain == channel->target)
				expected_rights = channel->target_rights;
			else
				return BE_CHECK_UNDECLARED_SHARED;
			if (request->rights != expected_rights)
				return BE_CHECK_CHANNEL_RIGHTS;
		}

		for (other = index + 1U; other < proposal->authority_count;
		     ++other) {
			const struct be_authority_request *candidate =
				&proposal->authorities[other];

			if (request->domain == candidate->domain &&
			    (request->gpa == candidate->gpa ||
			     request->resource_id ==
				     candidate->resource_id))
				return BE_CHECK_UNDECLARED_MAPPING;
		}

		authority->domain = request->domain;
		authority->gpa = request->gpa;
		authority->frame_id = request->resource_id;
		authority->rights = request->rights;
	}
	canonical->authority_count = proposal->authority_count;
	sort_authorities(canonical);
	return BE_CHECK_OK;
}

enum be_check_result
be_canonicalize(const struct be_platform_inventory *inventory,
		const struct be_proposal *proposal,
		struct be_canonical_state *canonical)
{
	struct be_canonical_state candidate = { 0 };
	enum be_check_result result;

	if (canonical == (struct be_canonical_state *)0)
		return BE_CHECK_NULL;
	*canonical = (struct be_canonical_state){ 0 };
	if (inventory == (const struct be_platform_inventory *)0 ||
	    proposal == (const struct be_proposal *)0)
		return BE_CHECK_NULL;

	result = be_check_inventory(inventory);
	if (result != BE_CHECK_OK)
		return result;
	if (proposal->proposal_id == 0U ||
	    proposal->source_vocabulary <= BE_VOCABULARY_INVALID ||
	    proposal->source_vocabulary >= BE_VOCABULARY_COUNT)
		return BE_CHECK_UNSUPPORTED;
	if (proposal->domain_count != BE_MAX_DOMAINS ||
	    proposal->resource_count != inventory->resource_count ||
	    proposal->authority_count != 4U ||
	    proposal->channel_count != BE_MAX_CHANNELS)
		return BE_CHECK_INCOMPLETE;
	if (proposal->published_root_count != 0U ||
	    proposal->published_mapping_count != 0U ||
	    proposal->published_active_domain != BE_DOMAIN_INVALID)
		return BE_CHECK_DIRECT_AUTHORITY;

	candidate.model_version = inventory->model_version;
	candidate.architecture = inventory->architecture;
	candidate.profile = inventory->profile;
	candidate.hart_id = inventory->hart_id;

	result = canonicalize_frames(inventory, proposal, &candidate);
	if (result != BE_CHECK_OK)
		return result;
	result = canonicalize_domains(inventory, proposal, &candidate);
	if (result != BE_CHECK_OK)
		return result;
	result = canonicalize_channel(proposal, &candidate);
	if (result != BE_CHECK_OK)
		return result;
	result = canonicalize_authorities(proposal, &candidate);
	if (result != BE_CHECK_OK)
		return result;

	candidate.configuration_id = be_configuration_identity(&candidate);
	result = be_check_canonical(&candidate);
	if (result != BE_CHECK_OK)
		return result;
	*canonical = candidate;
	return BE_CHECK_OK;
}

static enum be_check_result
check_canonical_frames(const struct be_canonical_state *canonical)
{
	be_size index;
	be_size other;
	be_size monitor_code = 0U;
	be_size monitor_data = 0U;
	be_size root_table = 0U;
	be_size trusted_stack = 0U;
	be_size saved_state = 0U;
	be_size private_frame = 0U;
	be_size shared = 0U;

	for (index = 0U; index < canonical->frame_count; ++index) {
		const struct be_frame_desc *frame = &canonical->frames[index];

		if (!frame_extent_is_valid(frame) ||
		    frame->class <= BE_FRAME_INVALID ||
		    frame->class >= BE_FRAME_CLASS_COUNT ||
		    (frame->owner_mask & ~BE_OWNER_ALL_MASK) != 0U)
			return BE_CHECK_UNSUPPORTED;
		if (index > 0U &&
		    canonical->frames[index - 1U].id >= frame->id)
			return BE_CHECK_DUPLICATE_RESOURCE;

		switch (frame->class) {
		case BE_FRAME_MONITOR_CODE:
			++monitor_code;
			break;
		case BE_FRAME_MONITOR_DATA:
			++monitor_data;
			break;
		case BE_FRAME_ROOT_TABLE:
			++root_table;
			break;
		case BE_FRAME_TRUSTED_STACK:
			++trusted_stack;
			break;
		case BE_FRAME_SAVED_STATE:
			++saved_state;
			break;
		case BE_FRAME_PRIVATE:
			++private_frame;
			if (frame->owner_mask != BE_OWNER_MANAGEMENT &&
			    frame->owner_mask != BE_OWNER_PROTECTED)
				return BE_CHECK_PRIVATE_OWNER;
			break;
		case BE_FRAME_SHARED:
			++shared;
			if (frame->owner_mask != 0U)
				return BE_CHECK_UNDECLARED_SHARED;
			break;
		default:
			return BE_CHECK_UNSUPPORTED;
		}
		if (frame->class != BE_FRAME_PRIVATE &&
		    frame->class != BE_FRAME_SHARED &&
		    frame->owner_mask != BE_OWNER_MONITOR)
			return BE_CHECK_PRIVATE_OWNER;

		for (other = index + 1U; other < canonical->frame_count;
		     ++other) {
			if (frame_extents_overlap(
				    frame, &canonical->frames[other]))
				return BE_CHECK_OVERLAPPING_RESOURCE;
		}
	}
	if (monitor_code != 1U || monitor_data != 1U ||
	    root_table != BE_MAX_ROOTS ||
	    trusted_stack != BE_MAX_DOMAINS ||
	    saved_state != BE_MAX_SAVED_STATES ||
	    private_frame != BE_MAX_DOMAINS || shared != BE_MAX_CHANNELS)
		return BE_CHECK_INCOMPLETE;
	return BE_CHECK_OK;
}

static enum be_check_result
check_canonical_domains(const struct be_canonical_state *canonical)
{
	static const enum be_domain_id domain_order[BE_MAX_DOMAINS] = {
		BE_DOMAIN_MANAGEMENT,
		BE_DOMAIN_PROTECTED,
	};
	be_size index;
	be_size other;

	for (index = 0U; index < canonical->domain_count; ++index) {
		const struct be_domain_desc *domain =
			&canonical->domains[index];
		const struct be_saved_state_desc *saved =
			&canonical->saved_states[index];
		const struct be_frame_desc *root =
			find_frame(canonical, domain->root_table_frame);
		const struct be_frame_desc *stack =
			find_frame(canonical, domain->trusted_stack_frame);
		const struct be_frame_desc *state =
			find_frame(canonical, domain->saved_state_frame);

		if (domain->id != domain_order[index] ||
		    domain->vcpu_id == 0U || domain->root_id == 0U ||
		    domain->vmid > 0x3fffU)
			return BE_CHECK_BINDING;
		if (root == (const struct be_frame_desc *)0 ||
		    root->class != BE_FRAME_ROOT_TABLE ||
		    stack == (const struct be_frame_desc *)0 ||
		    stack->class != BE_FRAME_TRUSTED_STACK ||
		    state == (const struct be_frame_desc *)0 ||
		    state->class != BE_FRAME_SAVED_STATE)
			return BE_CHECK_BINDING;
		if (saved->id != domain->saved_state_id ||
		    saved->owner != domain->id ||
		    saved->frame_id != domain->saved_state_frame)
			return BE_CHECK_BINDING;

		for (other = index + 1U; other < canonical->domain_count;
		     ++other) {
			const struct be_domain_desc *candidate =
				&canonical->domains[other];

			if (domain->vcpu_id == candidate->vcpu_id ||
			    domain->root_id == candidate->root_id ||
			    domain->root_table_frame ==
				    candidate->root_table_frame ||
			    domain->trusted_stack_frame ==
				    candidate->trusted_stack_frame ||
			    domain->saved_state_id ==
				    candidate->saved_state_id ||
			    domain->saved_state_frame ==
				    candidate->saved_state_frame)
				return BE_CHECK_BINDING;
		}
	}
	return BE_CHECK_OK;
}

static enum be_check_result
check_canonical_channel(const struct be_canonical_state *canonical)
{
	const struct be_channel_desc *channel = &canonical->channels[0];
	const struct be_frame_desc *backing =
		find_frame(canonical, channel->frame_id);

	if (channel->id == 0U ||
	    channel->source != BE_DOMAIN_MANAGEMENT ||
	    channel->target != BE_DOMAIN_PROTECTED ||
	    channel->source == channel->target ||
	    channel->source_rights !=
		    (BE_RIGHT_READ | BE_RIGHT_WRITE) ||
	    channel->target_rights != BE_RIGHT_READ)
		return BE_CHECK_CHANNEL_RIGHTS;
	if (backing == (const struct be_frame_desc *)0 ||
	    backing->class != BE_FRAME_SHARED ||
	    backing->owner_mask != 0U)
		return BE_CHECK_UNDECLARED_SHARED;
	return BE_CHECK_OK;
}

static enum be_check_result
check_canonical_authorities(const struct be_canonical_state *canonical)
{
	const struct be_channel_desc *channel = &canonical->channels[0];
	be_size index;
	be_size other;
	be_size management_private = 0U;
	be_size management_shared = 0U;
	be_size protected_private = 0U;
	be_size protected_shared = 0U;

	for (index = 0U; index < canonical->authority_count; ++index) {
		const struct be_authority_desc *authority =
			&canonical->authorities[index];
		const struct be_frame_desc *frame =
			find_frame(canonical, authority->frame_id);

		if (!domain_is_valid(authority->domain) ||
		    (authority->gpa & (BE_PAGE_SIZE - BE_U64_C(1))) != 0U ||
		    !rights_are_valid(authority->rights))
			return BE_CHECK_UNSUPPORTED;
		if (index > 0U &&
		    !authority_before(
			    &canonical->authorities[index - 1U],
			    authority))
			return BE_CHECK_UNDECLARED_MAPPING;
		if (frame == (const struct be_frame_desc *)0)
			return BE_CHECK_UNDECLARED_MAPPING;
		if (frame->class != BE_FRAME_PRIVATE &&
		    frame->class != BE_FRAME_SHARED)
			return BE_CHECK_EXCLUDED_MAPPING;
		if (frame->class == BE_FRAME_PRIVATE) {
			if (frame->owner_mask !=
			    owner_mask_for(authority->domain))
				return BE_CHECK_PRIVATE_OWNER;
			if (authority->rights !=
			    (BE_RIGHT_READ | BE_RIGHT_WRITE))
				return BE_CHECK_EXCESS_RIGHTS;
			if (authority->domain == BE_DOMAIN_MANAGEMENT)
				++management_private;
			else
				++protected_private;
		} else {
			if (frame->id != channel->frame_id)
				return BE_CHECK_UNDECLARED_SHARED;
			if (authority->domain == channel->source &&
			    authority->rights == channel->source_rights)
				++management_shared;
			else if (authority->domain == channel->target &&
				 authority->rights ==
					 channel->target_rights)
				++protected_shared;
			else
				return BE_CHECK_CHANNEL_RIGHTS;
		}

		for (other = index + 1U;
		     other < canonical->authority_count; ++other) {
			const struct be_authority_desc *candidate =
				&canonical->authorities[other];

			if (authority->domain == candidate->domain &&
			    (authority->gpa == candidate->gpa ||
			     authority->frame_id == candidate->frame_id))
				return BE_CHECK_UNDECLARED_MAPPING;
		}
	}
	if (management_private != 1U || management_shared != 1U ||
	    protected_private != 1U || protected_shared != 1U)
		return BE_CHECK_INCOMPLETE;
	return BE_CHECK_OK;
}

enum be_check_result
be_check_canonical(const struct be_canonical_state *canonical)
{
	enum be_check_result result;

	if (canonical == (const struct be_canonical_state *)0)
		return BE_CHECK_NULL;
	if (canonical->model_version != BE_MODEL_VERSION ||
	    canonical->architecture != BE_ARCH_RISCV64 ||
	    canonical->profile !=
		    BE_PROFILE_POLICY_NEUTRAL_SINGLE_HART_TWO_DOMAIN ||
	    canonical->hart_id != BE_MODEL_HART_ID)
		return BE_CHECK_UNSUPPORTED;
	if (canonical->domain_count != BE_MAX_DOMAINS ||
	    canonical->frame_count != BE_MAX_RESOURCES ||
	    canonical->authority_count != 4U ||
	    canonical->saved_state_count != BE_MAX_SAVED_STATES ||
	    canonical->channel_count != BE_MAX_CHANNELS)
		return BE_CHECK_INCOMPLETE;

	result = check_canonical_frames(canonical);
	if (result != BE_CHECK_OK)
		return result;
	result = check_canonical_domains(canonical);
	if (result != BE_CHECK_OK)
		return result;
	result = check_canonical_channel(canonical);
	if (result != BE_CHECK_OK)
		return result;
	result = check_canonical_authorities(canonical);
	if (result != BE_CHECK_OK)
		return result;
	if (canonical->configuration_id == 0U ||
	    canonical->configuration_id !=
		    be_configuration_identity(canonical))
		return BE_CHECK_INTEGRITY;
	return BE_CHECK_OK;
}

static be_u64 identity_byte(be_u64 identity, be_u8 value)
{
	identity ^= (be_u64)value;
	identity *= BE_U64_C(1099511628211);
	return identity;
}

static be_u64 identity_u64(be_u64 identity, be_u64 value)
{
	be_size index;

	for (index = 0U; index < 8U; ++index) {
		identity = identity_byte(identity, (be_u8)(value & 0xffU));
		value >>= 8U;
	}
	return identity;
}

be_u64
be_configuration_identity(const struct be_canonical_state *canonical)
{
	be_u64 identity = BE_U64_C(14695981039346656037);
	be_size index;

	if (canonical == (const struct be_canonical_state *)0 ||
	    canonical->domain_count > BE_MAX_DOMAINS ||
	    canonical->frame_count > BE_MAX_RESOURCES ||
	    canonical->authority_count > BE_MAX_AUTHORITIES ||
	    canonical->saved_state_count > BE_MAX_SAVED_STATES ||
	    canonical->channel_count > BE_MAX_CHANNELS)
		return 0U;

	identity = identity_u64(identity, canonical->model_version);
	identity = identity_u64(identity, (be_u64)canonical->architecture);
	identity = identity_u64(identity, (be_u64)canonical->profile);
	identity = identity_u64(identity, canonical->hart_id);
	identity = identity_u64(identity, canonical->domain_count);
	for (index = 0U; index < canonical->domain_count; ++index) {
		const struct be_domain_desc *domain =
			&canonical->domains[index];

		identity = identity_u64(identity, (be_u64)domain->id);
		identity = identity_u64(identity, domain->vcpu_id);
		identity = identity_u64(identity, domain->root_id);
		identity = identity_u64(
			identity, domain->root_table_frame);
		identity = identity_u64(identity, domain->vmid);
		identity = identity_u64(
			identity, domain->trusted_stack_frame);
		identity = identity_u64(identity, domain->saved_state_id);
		identity = identity_u64(
			identity, domain->saved_state_frame);
	}
	identity = identity_u64(identity, canonical->frame_count);
	for (index = 0U; index < canonical->frame_count; ++index) {
		const struct be_frame_desc *frame = &canonical->frames[index];

		identity = identity_u64(identity, frame->id);
		identity = identity_u64(identity, frame->base);
		identity = identity_u64(identity, frame->size);
		identity = identity_u64(identity, (be_u64)frame->class);
		identity = identity_u64(identity, frame->owner_mask);
	}
	identity = identity_u64(identity, canonical->authority_count);
	for (index = 0U; index < canonical->authority_count; ++index) {
		const struct be_authority_desc *authority =
			&canonical->authorities[index];

		identity = identity_u64(identity, (be_u64)authority->domain);
		identity = identity_u64(identity, authority->gpa);
		identity = identity_u64(identity, authority->frame_id);
		identity = identity_u64(identity, authority->rights);
	}
	identity = identity_u64(identity, canonical->saved_state_count);
	for (index = 0U; index < canonical->saved_state_count; ++index) {
		const struct be_saved_state_desc *saved =
			&canonical->saved_states[index];

		identity = identity_u64(identity, saved->id);
		identity = identity_u64(identity, (be_u64)saved->owner);
		identity = identity_u64(identity, saved->frame_id);
	}
	identity = identity_u64(identity, canonical->channel_count);
	for (index = 0U; index < canonical->channel_count; ++index) {
		const struct be_channel_desc *channel =
			&canonical->channels[index];

		identity = identity_u64(identity, channel->id);
		identity = identity_u64(identity, (be_u64)channel->source);
		identity = identity_u64(identity, (be_u64)channel->target);
		identity = identity_u64(identity, channel->frame_id);
		identity = identity_u64(identity, channel->source_rights);
		identity = identity_u64(identity, channel->target_rights);
	}
	return identity;
}

enum be_check_result
be_derive_enforcement(const struct be_canonical_state *canonical,
		      struct be_enforcement_state *enforcement)
{
	struct be_enforcement_state candidate = { 0 };
	enum be_check_result result;
	be_size domain_index;

	if (enforcement == (struct be_enforcement_state *)0)
		return BE_CHECK_NULL;
	*enforcement = (struct be_enforcement_state){ 0 };
	result = be_check_canonical(canonical);
	if (result != BE_CHECK_OK)
		return result;

	candidate.configuration_id = canonical->configuration_id;
	candidate.root_count = canonical->domain_count;
	for (domain_index = 0U;
	     domain_index < canonical->domain_count; ++domain_index) {
		const struct be_domain_desc *domain =
			&canonical->domains[domain_index];
		struct be_root_image *root =
			&candidate.roots[domain_index];
		be_size authority_index;

		root->root_id = domain->root_id;
		root->root_table_frame = domain->root_table_frame;
		root->domain = domain->id;
		root->vcpu_id = domain->vcpu_id;
		root->vmid = domain->vmid;
		root->trusted_stack_frame = domain->trusted_stack_frame;
		root->saved_state_id = domain->saved_state_id;
		root->saved_state_frame = domain->saved_state_frame;
		for (authority_index = 0U;
		     authority_index < canonical->authority_count;
		     ++authority_index) {
			const struct be_authority_desc *authority =
				&canonical->authorities[authority_index];
			struct be_mapping_desc *mapping;

			if (authority->domain != domain->id)
				continue;
			if (root->mapping_count >= BE_MAX_MAPPINGS)
				return BE_CHECK_INCOMPLETE;
			mapping = &root->mappings[root->mapping_count++];
			mapping->gpa = authority->gpa;
			mapping->frame_id = authority->frame_id;
			mapping->rights = authority->rights;
		}
	}

	result = be_check_enforcement(canonical, &candidate);
	if (result != BE_CHECK_OK)
		return result;
	*enforcement = candidate;
	return BE_CHECK_OK;
}

static int root_contains_authority(const struct be_root_image *root,
				   const struct be_authority_desc *authority)
{
	be_size index;

	for (index = 0U; index < root->mapping_count; ++index) {
		const struct be_mapping_desc *mapping = &root->mappings[index];

		if (mapping->gpa == authority->gpa &&
		    mapping->frame_id == authority->frame_id)
			return 1;
	}
	return 0;
}

enum be_check_result
be_check_enforcement(const struct be_canonical_state *canonical,
		     const struct be_enforcement_state *enforcement)
{
	enum be_check_result result;
	be_size index;

	if (canonical == (const struct be_canonical_state *)0 ||
	    enforcement == (const struct be_enforcement_state *)0)
		return BE_CHECK_NULL;
	result = be_check_canonical(canonical);
	if (result != BE_CHECK_OK)
		return result;
	if (enforcement->configuration_id != canonical->configuration_id)
		return BE_CHECK_INTEGRITY;
	if (enforcement->root_count != BE_MAX_ROOTS)
		return BE_CHECK_INCOMPLETE;

	for (index = 0U; index < enforcement->root_count; ++index) {
		const struct be_root_image *root =
			&enforcement->roots[index];
		const struct be_domain_desc *domain =
			find_domain(canonical, root->domain);
		be_size mapping_index;
		be_size expected_mappings = 0U;

		if (domain == (const struct be_domain_desc *)0 ||
		    root->domain != canonical->domains[index].id ||
		    root->root_id != domain->root_id ||
		    root->root_table_frame != domain->root_table_frame ||
		    root->vcpu_id != domain->vcpu_id ||
		    root->vmid != domain->vmid ||
		    root->trusted_stack_frame !=
			    domain->trusted_stack_frame ||
		    root->saved_state_id != domain->saved_state_id ||
		    root->saved_state_frame != domain->saved_state_frame)
			return BE_CHECK_BINDING;

		for (mapping_index = 0U;
		     mapping_index < canonical->authority_count;
		     ++mapping_index) {
			if (canonical->authorities[mapping_index].domain ==
			    domain->id)
				++expected_mappings;
		}
		if (root->mapping_count != expected_mappings ||
		    root->mapping_count == 0U ||
		    root->mapping_count > BE_MAX_MAPPINGS)
			return BE_CHECK_INCOMPLETE;

		for (mapping_index = 0U;
		     mapping_index < root->mapping_count; ++mapping_index) {
			const struct be_mapping_desc *mapping =
				&root->mappings[mapping_index];
			const struct be_frame_desc *frame =
				find_frame(canonical, mapping->frame_id);
			const struct be_authority_desc *authority;
			be_size other;

			if ((mapping->gpa &
			     (BE_PAGE_SIZE - BE_U64_C(1))) != 0U ||
			    !rights_are_valid(mapping->rights))
				return BE_CHECK_UNSUPPORTED;
			if (frame == (const struct be_frame_desc *)0)
				return BE_CHECK_UNDECLARED_MAPPING;
			if (frame->class != BE_FRAME_PRIVATE &&
			    frame->class != BE_FRAME_SHARED)
				return BE_CHECK_EXCLUDED_MAPPING;
			authority = find_authority(
				canonical, root->domain, mapping->gpa,
				mapping->frame_id);
			if (authority ==
			    (const struct be_authority_desc *)0)
				return BE_CHECK_UNDECLARED_MAPPING;
			if ((mapping->rights & ~authority->rights) != 0U)
				return BE_CHECK_EXCESS_RIGHTS;
			for (other = mapping_index + 1U;
			     other < root->mapping_count; ++other) {
				if (mapping->gpa ==
					    root->mappings[other].gpa ||
				    mapping->frame_id ==
					    root->mappings[other].frame_id)
					return BE_CHECK_UNDECLARED_MAPPING;
			}
		}
	}

	for (index = 0U; index < canonical->authority_count; ++index) {
		const struct be_authority_desc *authority =
			&canonical->authorities[index];
		const struct be_root_image *root =
			find_root(enforcement, authority->domain);

		if (root == (const struct be_root_image *)0 ||
		    !root_contains_authority(root, authority))
			return BE_CHECK_UNDECLARED_MAPPING;
	}
	return BE_CHECK_OK;
}

const char *be_check_result_name(enum be_check_result result)
{
	switch (result) {
	case BE_CHECK_OK:
		return "ok";
	case BE_CHECK_NULL:
		return "null";
	case BE_CHECK_INVALID_PHASE:
		return "invalid-phase";
	case BE_CHECK_INCOMPLETE:
		return "incomplete";
	case BE_CHECK_UNSUPPORTED:
		return "unsupported";
	case BE_CHECK_DIRECT_AUTHORITY:
		return "direct-authority";
	case BE_CHECK_DUPLICATE_RESOURCE:
		return "duplicate-resource";
	case BE_CHECK_OVERLAPPING_RESOURCE:
		return "overlapping-resource";
	case BE_CHECK_INVENTORY_CLOSURE:
		return "inventory-closure";
	case BE_CHECK_PRIVATE_OWNER:
		return "private-owner";
	case BE_CHECK_EXCLUDED_MAPPING:
		return "excluded-mapping";
	case BE_CHECK_UNDECLARED_MAPPING:
		return "undeclared-mapping";
	case BE_CHECK_EXCESS_RIGHTS:
		return "excess-rights";
	case BE_CHECK_UNDECLARED_SHARED:
		return "undeclared-shared";
	case BE_CHECK_CHANNEL_RIGHTS:
		return "channel-rights";
	case BE_CHECK_BINDING:
		return "binding";
	case BE_CHECK_INTEGRITY:
		return "integrity";
	default:
		return "invalid";
	}
}

const char *be_architecture_name(enum be_architecture architecture)
{
	return architecture == BE_ARCH_RISCV64 ? "riscv64" : "invalid";
}

const char *be_profile_name(enum be_profile profile)
{
	return profile ==
			       BE_PROFILE_POLICY_NEUTRAL_SINGLE_HART_TWO_DOMAIN ?
		       "policy-neutral-single-hart-two-domain" :
		       "invalid";
}

const char *
be_proposal_vocabulary_name(enum be_proposal_vocabulary vocabulary)
{
	if (vocabulary == BE_VOCABULARY_RELATIONS_A)
		return "relations-a";
	if (vocabulary == BE_VOCABULARY_RELATIONS_B)
		return "relations-b";
	return "invalid";
}

const char *be_domain_name(enum be_domain_id domain)
{
	if (domain == BE_DOMAIN_MANAGEMENT)
		return "management";
	if (domain == BE_DOMAIN_PROTECTED)
		return "protected";
	return "invalid";
}

const char *be_resource_kind_name(enum be_resource_kind kind)
{
	switch (kind) {
	case BE_RESOURCE_MONITOR_CODE:
		return "monitor-code";
	case BE_RESOURCE_MONITOR_DATA:
		return "monitor-data";
	case BE_RESOURCE_ROOT_TABLE:
		return "root-table";
	case BE_RESOURCE_TRUSTED_STACK:
		return "trusted-stack";
	case BE_RESOURCE_SAVED_STATE:
		return "saved-state";
	case BE_RESOURCE_ASSIGNABLE:
		return "assignable";
	default:
		return "invalid";
	}
}

const char *be_frame_class_name(enum be_frame_class class)
{
	switch (class) {
	case BE_FRAME_MONITOR_CODE:
		return "monitor-code";
	case BE_FRAME_MONITOR_DATA:
		return "monitor-data";
	case BE_FRAME_ROOT_TABLE:
		return "root-table";
	case BE_FRAME_TRUSTED_STACK:
		return "trusted-stack";
	case BE_FRAME_SAVED_STATE:
		return "saved-state";
	case BE_FRAME_PRIVATE:
		return "private";
	case BE_FRAME_SHARED:
		return "shared";
	default:
		return "invalid";
	}
}
