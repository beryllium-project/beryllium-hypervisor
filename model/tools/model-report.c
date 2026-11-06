// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Emit a deterministic proposal-to-enforcement report for Model 0.2.
 *
 * The configuration identity is a reporting/equivalence scalar, not a
 * cryptographic integrity measurement, attestation, or runtime input.
 */
#include <stdio.h>
#include <string.h>

#include <be/fixtures.h>
#include <be/state.h>

static enum be_fixture_id parse_fixture(const char *name)
{
	if (strcmp(name, "source-a") == 0)
		return BE_FIXTURE_SOURCE_A;
	if (strcmp(name, "source-b") == 0)
		return BE_FIXTURE_SOURCE_B;
	return BE_FIXTURE_INVALID;
}

static void rights_name(be_u32 rights, char output[4])
{
	be_size length = 0U;

	if ((rights & BE_RIGHT_READ) != 0U)
		output[length++] = 'r';
	if ((rights & BE_RIGHT_WRITE) != 0U)
		output[length++] = 'w';
	if ((rights & BE_RIGHT_EXECUTE) != 0U)
		output[length++] = 'x';
	output[length] = '\0';
}

static const char *owner_name(be_u32 owner_mask)
{
	if (owner_mask == BE_OWNER_MONITOR)
		return "monitor";
	if (owner_mask == BE_OWNER_MANAGEMENT)
		return "management";
	if (owner_mask == BE_OWNER_PROTECTED)
		return "protected";
	if (owner_mask == 0U)
		return "channel";
	return "invalid";
}

static const char *requested_owner_name(enum be_domain_id owner)
{
	return owner == BE_DOMAIN_INVALID ? "none" : be_domain_name(owner);
}

static int prepare_report_model(struct be_model *model,
				const struct be_platform_inventory *inventory,
				const struct be_proposal *proposal)
{
	be_model_reset(model);
	return be_model_bind_inventory(model, inventory) == BE_MODEL_OK &&
	       be_model_copy_proposal(model, proposal) == BE_MODEL_OK &&
	       be_model_validate(model) == BE_MODEL_OK &&
	       be_model_seal(model) == BE_MODEL_OK &&
	       be_model_derive_roots(model) == BE_MODEL_OK;
}

static void report_proposal(const struct be_proposal *proposal)
{
	be_size index;

	printf("  \"proposal\":{\n");
	printf("    \"id\":\"0x%016lx\",\n", proposal->proposal_id);
	printf("    \"source_vocabulary\":\"%s\",\n",
	       be_proposal_vocabulary_name(proposal->source_vocabulary));
	printf("    \"domains\":[\n");
	for (index = 0U; index < proposal->domain_count; ++index) {
		const struct be_domain_request *domain =
			&proposal->domains[index];

		printf("      {\"id\":%u,\"vcpu\":%u,\"root\":%u,"
		       "\"root_resource\":%u,\"vmid\":%u,"
		       "\"trusted_stack_resource\":%u,\"saved_state\":%u,"
		       "\"saved_state_resource\":%u}%s\n",
		       domain->id, domain->vcpu_id, domain->root_id,
		       domain->root_resource_id, domain->vmid,
		       domain->trusted_stack_resource_id,
		       domain->saved_state_id,
		       domain->saved_state_resource_id,
		       index + 1U == proposal->domain_count ? "" : ",");
	}
	printf("    ],\n");
	printf("    \"resources\":[\n");
	for (index = 0U; index < proposal->resource_count; ++index) {
		const struct be_resource_request *resource =
			&proposal->resources[index];

		printf("      {\"id\":%u,\"base\":\"0x%016lx\","
		       "\"size\":\"0x%016lx\",\"class\":\"%s\","
		       "\"owner\":\"%s\"}%s\n",
		       resource->resource_id, resource->base, resource->size,
		       be_frame_class_name(resource->class),
		       requested_owner_name(resource->owner),
		       index + 1U == proposal->resource_count ? "" : ",");
	}
	printf("    ],\n");
	printf("    \"authorities\":[\n");
	for (index = 0U; index < proposal->authority_count; ++index) {
		const struct be_authority_request *authority =
			&proposal->authorities[index];
		char rights[4];

		rights_name(authority->rights, rights);
		printf("      {\"domain\":\"%s\",\"gpa\":\"0x%016lx\","
		       "\"resource\":%u,\"rights\":\"%s\"}%s\n",
		       be_domain_name(authority->domain), authority->gpa,
		       authority->resource_id, rights,
		       index + 1U == proposal->authority_count ? "" : ",");
	}
	printf("    ],\n");
	{
		const struct be_channel_request *channel =
			&proposal->channels[0];
		char source_rights[4];
		char target_rights[4];

		rights_name(channel->source_rights, source_rights);
		rights_name(channel->target_rights, target_rights);
		printf("    \"channel\":{\"id\":%u,\"source\":\"%s\","
		       "\"target\":\"%s\",\"resource\":%u,"
		       "\"source_rights\":\"%s\","
		       "\"target_rights\":\"%s\"},\n",
		       channel->id, be_domain_name(channel->source),
		       be_domain_name(channel->target),
		       channel->resource_id, source_rights, target_rights);
	}
	printf("    \"direct_authority\":{"
	       "\"roots\":%lu,\"mappings\":%lu,\"active\":\"%s\"}\n",
	       proposal->published_root_count,
	       proposal->published_mapping_count,
	       be_domain_name(proposal->published_active_domain));
	printf("  },\n");
}

static void
report_inventory(const struct be_platform_inventory *inventory)
{
	be_size index;

	printf("  \"inventory\":{\n");
	printf("    \"architecture\":\"%s\",\n",
	       be_architecture_name(inventory->architecture));
	printf("    \"profile\":\"%s\",\n",
	       be_profile_name(inventory->profile));
	printf("    \"hart\":%u,\n", inventory->hart_id);
	printf("    \"resources\":[\n");
	for (index = 0U; index < inventory->resource_count; ++index) {
		const struct be_resource_desc *resource =
			&inventory->resources[index];

		printf("      {\"id\":%u,\"base\":\"0x%016lx\","
		       "\"size\":\"0x%016lx\",\"kind\":\"%s\"}%s\n",
		       resource->id, resource->base, resource->size,
		       be_resource_kind_name(resource->kind),
		       index + 1U == inventory->resource_count ? "" : ",");
	}
	printf("    ]\n");
	printf("  },\n");
}

static void report_canonical(const struct be_canonical_state *canonical)
{
	be_size index;

	printf("  \"canonical\":{\n");
	printf("    \"configuration_identity\":\"0x%016lx\",\n",
	       canonical->configuration_id);
	printf("    \"domains\":[\n");
	for (index = 0U; index < canonical->domain_count; ++index) {
		const struct be_domain_desc *domain =
			&canonical->domains[index];

		printf("      {\"id\":%u,\"name\":\"%s\",\"vcpu\":%u,"
		       "\"root\":%u,\"root_table\":%u,\"vmid\":%u,"
		       "\"trusted_stack\":%u,\"saved_state\":%u,"
		       "\"saved_state_frame\":%u}%s\n",
		       domain->id, be_domain_name(domain->id),
		       domain->vcpu_id, domain->root_id,
		       domain->root_table_frame, domain->vmid,
		       domain->trusted_stack_frame, domain->saved_state_id,
		       domain->saved_state_frame,
		       index + 1U == canonical->domain_count ? "" : ",");
	}
	printf("    ],\n");
	printf("    \"frames\":[\n");
	for (index = 0U; index < canonical->frame_count; ++index) {
		const struct be_frame_desc *frame =
			&canonical->frames[index];

		printf("      {\"id\":%u,\"base\":\"0x%016lx\","
		       "\"size\":\"0x%016lx\",\"class\":\"%s\","
		       "\"owner\":\"%s\"}%s\n",
		       frame->id, frame->base, frame->size,
		       be_frame_class_name(frame->class),
		       owner_name(frame->owner_mask),
		       index + 1U == canonical->frame_count ? "" : ",");
	}
	printf("    ],\n");
	printf("    \"saved_states\":[\n");
	for (index = 0U; index < canonical->saved_state_count; ++index) {
		const struct be_saved_state_desc *saved =
			&canonical->saved_states[index];

		printf("      {\"id\":%u,\"owner\":\"%s\","
		       "\"frame\":%u}%s\n",
		       saved->id, be_domain_name(saved->owner),
		       saved->frame_id,
		       index + 1U == canonical->saved_state_count ? "" :
								     ",");
	}
	printf("    ],\n");
	{
		const struct be_channel_desc *channel =
			&canonical->channels[0];
		char source_rights[4];
		char target_rights[4];

		rights_name(channel->source_rights, source_rights);
		rights_name(channel->target_rights, target_rights);
		printf("    \"channel\":{\"id\":%u,\"source\":\"%s\","
		       "\"target\":\"%s\",\"frame\":%u,"
		       "\"source_rights\":\"%s\","
		       "\"target_rights\":\"%s\"},\n",
		       channel->id, be_domain_name(channel->source),
		       be_domain_name(channel->target), channel->frame_id,
		       source_rights, target_rights);
	}
	printf("    \"authorities\":[\n");
	for (index = 0U; index < canonical->authority_count; ++index) {
		const struct be_authority_desc *authority =
			&canonical->authorities[index];
		char rights[4];

		rights_name(authority->rights, rights);
		printf("      {\"domain\":\"%s\",\"gpa\":\"0x%016lx\","
		       "\"frame\":%u,\"rights\":\"%s\"}%s\n",
		       be_domain_name(authority->domain), authority->gpa,
		       authority->frame_id, rights,
		       index + 1U == canonical->authority_count ? "" : ",");
	}
	printf("    ]\n");
	printf("  },\n");
}

static void
report_enforcement(const struct be_enforcement_state *enforcement)
{
	be_size index;

	printf("  \"derived\":{\n");
	printf("    \"configuration_identity\":\"0x%016lx\",\n",
	       enforcement->configuration_id);
	printf("    \"roots\":[\n");
	for (index = 0U; index < enforcement->root_count; ++index) {
		const struct be_root_image *root =
			&enforcement->roots[index];
		be_size mapping;

		printf("      {\"id\":%u,\"root_table\":%u,"
		       "\"domain\":\"%s\",\"vcpu\":%u,\"vmid\":%u,"
		       "\"trusted_stack\":%u,\"saved_state\":%u,"
		       "\"saved_state_frame\":%u,\"mappings\":[",
		       root->root_id, root->root_table_frame,
		       be_domain_name(root->domain), root->vcpu_id,
		       root->vmid, root->trusted_stack_frame,
		       root->saved_state_id, root->saved_state_frame);
		for (mapping = 0U; mapping < root->mapping_count;
		     ++mapping) {
			const struct be_mapping_desc *entry =
				&root->mappings[mapping];
			char rights[4];

			rights_name(entry->rights, rights);
			printf("%s{\"gpa\":\"0x%016lx\",\"frame\":%u,"
			       "\"rights\":\"%s\"}",
			       mapping == 0U ? "" : ",", entry->gpa,
			       entry->frame_id, rights);
		}
		printf("]}%s\n",
		       index + 1U == enforcement->root_count ? "" : ",");
	}
	printf("    ]\n");
	printf("  },\n");
}

int main(int argc, char **argv)
{
	const struct be_platform_inventory *inventory;
	const struct be_proposal *proposal;
	enum be_fixture_id fixture;
	struct be_model model;

	if (argc != 2) {
		fprintf(stderr, "usage: %s source-a|source-b\n", argv[0]);
		return 2;
	}
	fixture = parse_fixture(argv[1]);
	inventory = be_fixture_inventory();
	proposal = be_fixture_proposal(fixture);
	if (proposal == (const struct be_proposal *)0) {
		fprintf(stderr, "unsupported fixture: %s\n", argv[1]);
		return 2;
	}
	if (!prepare_report_model(&model, inventory, proposal)) {
		fprintf(stderr, "%s: model preparation failed: %s\n", argv[1],
			be_check_result_name(model.check_result));
		return 1;
	}

	printf("{\n");
	printf("  \"schema\":\"be-model-0.2\",\n");
	printf("  \"model_version\":%u,\n", BE_MODEL_VERSION);
	printf("  \"fixture\":\"%s\",\n", be_fixture_name(fixture));
	report_proposal(proposal);
	report_inventory(inventory);
	printf("  \"checker\":\"%s\",\n",
	       be_check_result_name(model.check_result));
	printf("  \"phase\":\"%s\",\n", be_model_phase_name(model.phase));
	report_canonical(&model.canonical);
	report_enforcement(&model.enforcement);
	printf("  \"identity_use\":\"deterministic-reporting-only\",\n");
	printf("  \"claim_scope\":\"bounded-abstract-model-and-host-checker\"\n");
	printf("}\n");
	return 0;
}
