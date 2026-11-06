// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: emit a deterministic JSON report for the successful R1 pure-C
 *          full-profile flow. The report shows the fixed thirteen canonical
 *          frames, six canonical authorities, and both abstract derived roots
 *          with their exact three mappings.
 * Trust:   report tool only. The configuration identity is used only for
 *          deterministic reporting and equivalence; it is not integrity
 *          measurement, attestation, or privileged runtime input.
 * Scope:   host evidence for the accepted R1 pure-C mechanism only. It links
 *          no image, executes no privileged code, and carries no QEMU or
 *          hardware result.
 */
#include <stdio.h>

#include <be/manifest.h>
#include <be/r1-config.h>
#include <be/state.h>

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

static int prepare(struct be_runtime *runtime)
{
	return be_runtime_copy_inventory(runtime, be_r1_inventory()) ==
		       BE_RUNTIME_OK &&
	       be_runtime_copy_proposal(runtime, be_r1_proposal()) ==
		       BE_RUNTIME_OK &&
	       be_runtime_validate(runtime) == BE_RUNTIME_OK &&
	       be_runtime_seal(runtime) == BE_RUNTIME_OK &&
	       be_runtime_derive(runtime) == BE_RUNTIME_OK;
}

static void report_domains(const struct be_canonical_state *canonical)
{
	be_size index;

	printf("  \"domains\":[\n");
	for (index = 0U; index < canonical->domain_count; ++index) {
		const struct be_domain_desc *domain = &canonical->domains[index];

		printf("    {\"id\":%u,\"name\":\"%s\",\"vcpu\":%u,"
		       "\"root\":%u,\"root_storage\":%u,\"vmid\":%u,"
		       "\"trusted_stack\":%u,\"saved_state\":%u,"
		       "\"saved_state_storage\":%u}%s\n",
		       domain->id, be_domain_name(domain->id),
		       domain->vcpu_id, domain->root_id,
		       domain->root_table_frame, domain->vmid,
		       domain->trusted_stack_frame, domain->saved_state_id,
		       domain->saved_state_frame,
		       index + 1U == canonical->domain_count ? "" : ",");
	}
	printf("  ],\n");
}

static void report_frames(const struct be_canonical_state *canonical)
{
	be_size index;

	printf("  \"frames\":[\n");
	for (index = 0U; index < canonical->frame_count; ++index) {
		const struct be_frame_desc *frame = &canonical->frames[index];

		printf("    {\"id\":%u,\"base\":\"0x%016lx\","
		       "\"size\":\"0x%016lx\",\"class\":\"%s\","
		       "\"owner\":\"%s\"}%s\n",
		       frame->id, frame->base, frame->size,
		       be_frame_class_name(frame->class),
		       owner_name(frame->owner_mask),
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

		printf("    {\"id\":%u,\"domain\":\"%s\",\"vcpu\":%u,"
		       "\"root_storage\":%u,\"vmid\":%u,"
		       "\"trusted_stack\":%u,\"saved_state\":%u,"
		       "\"saved_state_storage\":%u,\"mappings\":[",
		       root->root_id, be_domain_name(root->domain),
		       root->vcpu_id, root->root_table_frame, root->vmid,
		       root->trusted_stack_frame, root->saved_state_id,
		       root->saved_state_frame);
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
	struct be_runtime runtime = BE_RUNTIME_INITIALIZER;
	struct be_runtime_report report;

	if (!prepare(&runtime)) {
		fprintf(stderr, "r1 full-profile preparation failed: %s\n",
			be_check_result_name(runtime.check_result));
		return 1;
	}
	if (be_runtime_report(&runtime, &report) != BE_RUNTIME_OK) {
		fprintf(stderr, "r1 report summary failed: %s\n",
			be_check_result_name(runtime.check_result));
		return 1;
	}

	printf("{\n");
	printf("  \"schema\":\"be-r1-full-profile-v1\",\n");
	printf("  \"package\":\"single-hart-runtime-r1\",\n");
	printf("  \"scope\":\"pure-c-mechanism-host-report\",\n");
	printf("  \"summary\":{\n");
	printf("    \"schema_version\":%u,\n", report.schema_version);
	printf("    \"configuration_version\":%u,\n",
	       BE_CONFIGURATION_VERSION);
	printf("    \"hart_id\":%u,\n", BE_CONFIGURATION_HART_ID);
	printf("    \"configuration_identity\":\"0x%016lx\",\n",
	       report.configuration_id);
	printf("    \"validated_identity\":\"0x%016lx\",\n",
	       runtime.validated_identity);
	printf("    \"sealed_identity\":\"0x%016lx\",\n",
	       runtime.sealed_identity);
	printf("    \"phase\":\"%s\",\n", phase_name(report.phase));
	printf("    \"check_result\":\"%s\",\n",
	       be_check_result_name(report.check_result));
	printf("    \"sealed\":\"%s\",\n", report.sealed != 0U ? "yes" : "no");
	printf("    \"inventory_resources\":%lu,\n",
	       (unsigned long)runtime.inventory.resource_count);
	printf("    \"proposal_resources\":%lu,\n",
	       (unsigned long)runtime.proposal.resource_count);
	printf("    \"canonical_frames\":%lu,\n",
	       (unsigned long)report.frame_count);
	printf("    \"canonical_authorities\":%lu,\n",
	       (unsigned long)report.authority_count);
	printf("    \"derived_roots\":%lu,\n",
	       (unsigned long)report.root_count);
	printf("    \"derived_mappings\":%lu\n",
	       (unsigned long)report.mapping_count);
	printf("  },\n");
	report_domains(&runtime.canonical);
	report_frames(&runtime.canonical);
	report_authorities(&runtime.canonical);
	report_roots(&runtime.enforcement);
	printf("  \"claims\":{\n");
	printf("    \"full_profile_resources\":13,\n");
	printf("    \"guest_code_overlays\":2,\n");
	printf("    \"model_0_2_refinement\":\"no\",\n");
	printf("    \"identity_use\":\"deterministic-reporting-only\",\n");
	printf("    \"privileged_code\":\"no\",\n");
	printf("    \"linked_image\":\"no\",\n");
	printf("    \"qemu_beryllium_result\":\"NOT-RUN\",\n");
	printf("    \"hardware_validation\":\"NOT-RUN\"\n");
	printf("  }\n");
	printf("}\n");
	return 0;
}
