// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP core profile's identity, the G-stage builder's inputs
 *          from the derived roots (mvp-core.h; planning/mvp-m6-plan.md, D-1
 *          to D-3 and Q6), and the console input grants from them
 *          (planning/mvp-m7-plan.md, D-5).
 * Trust:   restricted C over the sealed state, which hart 0 alone reads
 *          before any domain hart starts. No CSR, fence, or I/O.
 * Scope:   the MVP line from M6.
 */
#include "mvp-core.h"

/* Each value as eight little-endian bytes, in order. */
static void fields(struct be_mvp_sha256 *context, const be_u64 *values,
		   be_u64 count)
{
	be_u8 bytes[8];
	be_u64 index;
	be_u64 byte;

	for (index = 0U; index < count; ++index) {
		for (byte = 0U; byte < sizeof(bytes); ++byte)
			bytes[byte] = (be_u8)(values[index] >> (8U * byte));
		be_mvp_sha256_update(context, bytes, sizeof(bytes));
	}
}

void be_mvp_core_identity(const struct be_platform_inventory *inventory,
			  const struct be_proposal *proposal,
			  be_u8 identity[BE_MVP_SHA256_BYTES])
{
	const be_u64 head[6] = {
		inventory->configuration_version,
		(be_u64)inventory->architecture, (be_u64)inventory->profile,
		inventory->hart_id, inventory->hart_count,
		inventory->resource_count,
	};
	const be_u64 tail[3] = {
		proposal->published_root_count,
		proposal->published_mapping_count,
		(be_u64)proposal->published_active_domain,
	};
	struct be_mvp_sha256 context;
	be_size index;

	be_mvp_sha256_init(&context);
	fields(&context, head, 6U);
	for (index = 0U; index < inventory->resource_count &&
			 index < BE_MAX_RESOURCES; ++index) {
		const struct be_resource_desc *at =
			&inventory->resources[index];
		const be_u64 values[4] = { at->id, at->base, at->size,
					   (be_u64)at->kind };

		fields(&context, values, 4U);
	}
	fields(&context, (const be_u64[3]){ proposal->proposal_id,
		(be_u64)proposal->source_vocabulary,
		proposal->domain_count }, 3U);
	for (index = 0U; index < proposal->domain_count &&
			 index < BE_MAX_DOMAINS; ++index) {
		const struct be_domain_request *at = &proposal->domains[index];
		const be_u64 values[9] = {
			(be_u64)at->id, at->vcpu_id, at->root_id,
			at->root_resource_id, at->vmid,
			at->trusted_stack_resource_id, at->saved_state_id,
			at->saved_state_resource_id, at->hart_id,
		};

		fields(&context, values, 9U);
	}
	fields(&context, &proposal->resource_count, 1U);
	for (index = 0U; index < proposal->resource_count &&
			 index < BE_MAX_RESOURCES; ++index) {
		const struct be_resource_request *at =
			&proposal->resources[index];
		const be_u64 values[5] = { at->resource_id, at->base, at->size,
					   (be_u64)at->class,
					   (be_u64)at->owner };

		fields(&context, values, 5U);
	}
	fields(&context, &proposal->authority_count, 1U);
	for (index = 0U; index < proposal->authority_count &&
			 index < BE_MAX_AUTHORITIES; ++index) {
		const struct be_authority_request *at =
			&proposal->authorities[index];
		const be_u64 values[4] = { (be_u64)at->domain, at->gpa,
					   at->resource_id, at->rights };

		fields(&context, values, 4U);
	}
	fields(&context, &proposal->channel_count, 1U);
	for (index = 0U; index < proposal->channel_count &&
			 index < BE_MAX_CHANNELS; ++index) {
		const struct be_channel_request *at =
			&proposal->channels[index];
		const be_u64 values[6] = { at->id, (be_u64)at->source,
					   (be_u64)at->target, at->resource_id,
					   at->source_rights,
					   at->target_rights };

		fields(&context, values, 6U);
	}
	fields(&context, tail, 3U);
	be_mvp_sha256_final(&context, identity);
}

static const struct be_frame_desc *
frame_of(const struct be_canonical_state *canonical, be_u32 id)
{
	be_size index;

	for (index = 0U; index < canonical->frame_count &&
			 index < BE_MAX_RESOURCES; ++index) {
		if (canonical->frames[index].id == id)
			return &canonical->frames[index];
	}
	return (const struct be_frame_desc *)0;
}

/* A domain's index: the management identifier's 0, the protected's 1. */
static be_u64 domain_index(enum be_domain_id domain)
{
	return (be_u64)domain - (be_u64)BE_DOMAIN_MANAGEMENT;
}

/* One root's page mapping into the page records, kept in GPA order. */
static int add_page(const struct be_canonical_state *canonical,
		    const struct be_mapping_desc *mapping,
		    const struct be_frame_desc *frame, be_u64 domain,
		    struct be_mvp_gstage_page *pages, be_u64 *count)
{
	be_size index;
	be_u64 at;

	for (at = 0U; at < *count; ++at) {
		if (pages[at].hpa != frame->base)
			continue;
		if (pages[at].gpa != mapping->gpa)
			return 0;
		pages[at].rights[domain] = mapping->rights;
		return 1;
	}
	if (*count >= BE_MVP_PAGES_MAX ||
	    frame->size != BE_MVP_GSTAGE_PAGE_BYTES)
		return 0;
	for (at = *count; at > 0U && pages[at - 1U].gpa > mapping->gpa; --at)
		pages[at] = pages[at - 1U];
	pages[at] = (struct be_mvp_gstage_page){
		.gpa = mapping->gpa, .hpa = frame->base, .bytes = frame->size,
		.kind = BE_MVP_PAGE_SECRET, .writer = BE_MVP_PAGE_NONE,
		.reader = frame->owner_mask == BE_OWNER_PROTECTED ? 1U : 0U,
	};
	for (index = 0U; index < canonical->channel_count &&
			 index < BE_MAX_CHANNELS; ++index) {
		const struct be_channel_desc *channel =
			&canonical->channels[index];

		if (channel->frame_id != frame->id)
			continue;
		pages[at].kind = BE_MVP_PAGE_CHANNEL;
		pages[at].writer = domain_index(channel->source);
		pages[at].reader = domain_index(channel->target);
	}
	pages[at].rights[domain] = mapping->rights;
	++*count;
	return 1;
}

int be_mvp_core_gstage(const struct be_canonical_state *canonical,
		       const struct be_enforcement_state *enforcement,
		       struct be_mvp_gstage_desc *descs,
		       struct be_mvp_gstage_page *pages, be_u64 *count)
{
	be_u64 domain;
	be_size index;

	*count = 0U;
	if (enforcement->root_count != BE_MVP_DOMAINS)
		return 0;
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		const struct be_root_image *root = &enforcement->roots[domain];
		const struct be_frame_desc *pool =
			frame_of(canonical, root->root_table_frame);
		be_u64 windows = 0U;

		if (pool == (const struct be_frame_desc *)0 ||
		    domain_index(root->domain) != domain)
			return 0;
		descs[domain] = (struct be_mvp_gstage_desc){
			.pool_pa = pool->base, .vmid = root->vmid,
			.hart = root->hart_id,
		};
		for (index = 0U; index < root->mapping_count &&
				 index < BE_MAX_MAPPINGS; ++index) {
			const struct be_mapping_desc *mapping =
				&root->mappings[index];
			const struct be_frame_desc *frame =
				frame_of(canonical, mapping->frame_id);

			if (frame == (const struct be_frame_desc *)0)
				return 0;
			if (frame->class != BE_FRAME_GUEST_CODE) {
				if (!add_page(canonical, mapping, frame, domain,
					      pages, count))
					return 0;
				continue;
			}
			descs[domain].gpa_base = mapping->gpa;
			descs[domain].hpa_base = frame->base;
			descs[domain].size = frame->size;
			++windows;
		}
		if (windows != 1U)
			return 0;
	}
	return 1;
}

int be_mvp_core_console(const struct be_enforcement_state *enforcement,
			be_u64 *grants)
{
	be_u64 found = 0U;
	be_u64 domain;

	*grants = 0U;
	if (enforcement->root_count != BE_MVP_DOMAINS)
		return 0;
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		const struct be_root_image *root = &enforcement->roots[domain];

		if (domain_index(root->domain) != domain ||
		    root->console_input > 1U)
			return 0;
		found |= (be_u64)root->console_input << domain;
	}
	*grants = found;
	return 1;
}

int be_mvp_core_same(const void *left, const void *right, be_u64 bytes)
{
	const be_u8 *one = left;
	const be_u8 *two = right;
	be_u8 differ = 0U;
	be_u64 index;

	for (index = 0U; index < bytes; ++index)
		differ |= (be_u8)(one[index] ^ two[index]);
	return differ == 0U;
}
