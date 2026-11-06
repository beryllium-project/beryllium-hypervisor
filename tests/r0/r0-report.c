// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: emit a deterministic Model 0.2 core-projection trace for the frozen
 *          R0 configuration constants. The report shows every frozen constant
 *          instantiating the accepted abstract domains, frames, channel, and
 *          rights.
 * Trust:   report tool only. The configuration identity is a reporting and
 *          equivalence scalar, not an integrity measurement or attestation.
 * Scope:   R0 freeze only; the eleven-resource core projection. The two R-X
 *          guest-code overlays of the full profile are outside this trace and
 *          are not a Model 0.2 refinement.
 */
#include <stdio.h>

#include <be/state.h>
#include <be/r0-config.h>

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

static int prepare(struct be_model *model)
{
	be_model_reset(model);
	return be_model_bind_inventory(model, be_r0_core_inventory()) ==
		       BE_MODEL_OK &&
	       be_model_copy_proposal(model, be_r0_core_proposal()) ==
		       BE_MODEL_OK &&
	       be_model_validate(model) == BE_MODEL_OK &&
	       be_model_seal(model) == BE_MODEL_OK &&
	       be_model_derive_roots(model) == BE_MODEL_OK;
}

static void report_frames(const struct be_canonical_state *canonical)
{
	be_size index;

	printf("  \"frames\":[\n");
	for (index = 0U; index < canonical->frame_count; ++index) {
		const struct be_frame_desc *frame = &canonical->frames[index];

		printf("    {\"id\":%u,\"base\":\"0x%016lx\","
		       "\"size\":\"0x%016lx\",\"class\":\"%s\"}%s\n",
		       frame->id, frame->base, frame->size,
		       be_frame_class_name(frame->class),
		       index + 1U == canonical->frame_count ? "" : ",");
	}
	printf("  ],\n");
}

static void report_authorities(const struct be_canonical_state *canonical)
{
	be_size index;

	printf("  \"authorities\":[\n");
	for (index = 0U; index < canonical->authority_count; ++index) {
		const struct be_authority_desc *authority =
			&canonical->authorities[index];
		char rights[4];

		rights_name(authority->rights, rights);
		printf("    {\"domain\":\"%s\",\"gpa\":\"0x%016lx\","
		       "\"frame\":%u,\"rights\":\"%s\"}%s\n",
		       be_domain_name(authority->domain), authority->gpa,
		       authority->frame_id, rights,
		       index + 1U == canonical->authority_count ? "" : ",");
	}
	printf("  ],\n");
}

static void report_roots(const struct be_enforcement_state *enforcement)
{
	be_size index;

	printf("  \"roots\":[\n");
	for (index = 0U; index < enforcement->root_count; ++index) {
		const struct be_root_image *root = &enforcement->roots[index];
		be_size mapping;

		printf("    {\"id\":%u,\"domain\":\"%s\",\"vmid\":%u,"
		       "\"mappings\":[",
		       root->root_id, be_domain_name(root->domain),
		       root->vmid);
		for (mapping = 0U; mapping < root->mapping_count; ++mapping) {
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
	printf("  ],\n");
}

int main(void)
{
	struct be_model model;

	if (!prepare(&model)) {
		fprintf(stderr, "r0 core projection preparation failed: %s\n",
			be_check_result_name(model.check_result));
		return 1;
	}

	printf("{\n");
	printf("  \"schema\":\"be-r0-core-projection\",\n");
	printf("  \"model_version\":%u,\n", BE_MODEL_VERSION);
	printf("  \"profile\":\"%s\",\n",
	       be_profile_name(model.canonical.profile));
	printf("  \"configuration_identity\":\"0x%016lx\",\n",
	       model.canonical.configuration_id);
	printf("  \"core_projection_resources\":%lu,\n",
	       (unsigned long)model.canonical.frame_count);
	report_frames(&model.canonical);
	report_authorities(&model.canonical);
	report_roots(&model.enforcement);
	printf("  \"full_profile_resources\":13,\n");
	printf("  \"guest_code_overlays\":2,\n");
	printf("  \"model_0_2_refinement\":\"no\",\n");
	printf("  \"identity_use\":\"deterministic-reporting-only\",\n");
	printf("  \"qemu_beryllium_result\":\"NOT-RUN\"\n");
	printf("}\n");
	return 0;
}
