// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Execute the visible Model 0.2 initialization and retained switch sequence.
 *
 * This host tool exercises only the non-runtime restricted-C model.
 */
#include <stdio.h>
#include <string.h>

#include <be/fixtures.h>
#include <be/state.h>

#define MANAGEMENT_PRIVATE_GPA	BE_U64_C(0x40000000)
#define PROTECTED_PRIVATE_GPA	BE_U64_C(0x40001000)
#define SHARED_GPA		BE_U64_C(0x40002000)
#define MANAGEMENT_SENTINEL	BE_U64_C(0x4d414e4147454d45)

static enum be_fixture_id parse_fixture(const char *name)
{
	if (strcmp(name, "source-a") == 0)
		return BE_FIXTURE_SOURCE_A;
	if (strcmp(name, "source-b") == 0)
		return BE_FIXTURE_SOURCE_B;
	return BE_FIXTURE_INVALID;
}

static int require_result(const char *operation,
			  enum be_model_result actual,
			  enum be_model_result expected)
{
	printf("%-36s %s\n", operation, be_model_result_name(actual));
	if (actual == expected)
		return 1;
	fprintf(stderr, "%s: expected %s, received %s\n", operation,
		be_model_result_name(expected), be_model_result_name(actual));
	return 0;
}

int main(int argc, char **argv)
{
	const struct be_platform_inventory *inventory;
	const struct be_proposal *proposal;
	enum be_fixture_id fixture;
	struct be_model model;
	be_u64 restored;

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

	printf("Beryllium Architecture Model 0.2\n");
	printf("fixture=%s proposal=0x%016lx vocabulary=%s\n",
	       be_fixture_name(fixture), proposal->proposal_id,
	       be_proposal_vocabulary_name(proposal->source_vocabulary));

	be_model_reset(&model);
	if (!require_result("bind platform inventory",
			    be_model_bind_inventory(&model, inventory),
			    BE_MODEL_OK) ||
	    !require_result("copy untrusted proposal",
			    be_model_copy_proposal(&model, proposal),
			    BE_MODEL_OK) ||
	    !require_result("validate canonical state",
			    be_model_validate(&model), BE_MODEL_OK))
		return 1;
	printf("%-36s 0x%016lx\n", "canonical configuration identity",
	       model.canonical.configuration_id);
	if (!require_result("seal canonical authority",
			    be_model_seal(&model), BE_MODEL_OK) ||
	    !require_result("derive enforcement roots",
			    be_model_derive_roots(&model), BE_MODEL_OK) ||
	    !require_result("activate management binding",
			    be_model_activate(
				    &model, BE_DOMAIN_MANAGEMENT),
			    BE_MODEL_OK) ||
	    !require_result("set management saved-state input",
			    be_model_write_register(
				    &model, 0U, MANAGEMENT_SENTINEL),
			    BE_MODEL_OK) ||
	    !require_result("management private read/write",
			    be_model_access(&model, MANAGEMENT_PRIVATE_GPA,
					    BE_RIGHT_READ |
						    BE_RIGHT_WRITE),
			    BE_MODEL_ALLOWED) ||
	    !require_result("management cross-private denial",
			    be_model_access(&model, PROTECTED_PRIVATE_GPA,
					    BE_RIGHT_READ),
			    BE_MODEL_DENIED) ||
	    !require_result("management channel write",
			    be_model_access(&model, SHARED_GPA,
					    BE_RIGHT_READ |
						    BE_RIGHT_WRITE),
			    BE_MODEL_ALLOWED) ||
	    !require_result("select protected binding",
			    be_model_begin_switch(
				    &model, BE_DOMAIN_PROTECTED),
			    BE_MODEL_OK))
		return 1;

	printf("%-36s %lu retained\n", "cached translations before fence",
	       be_model_cache_count(&model));
	if (be_model_cache_count(&model) == 0U ||
	    model.fence_complete != 0U) {
		fprintf(stderr, "switch did not expose stale translations\n");
		return 1;
	}
	if (!require_result("complete global HFENCE.GVMA",
			    be_model_complete_fence(&model),
			    BE_MODEL_OK))
		return 1;
	printf("%-36s %lu retained\n", "cached translations after fence",
	       be_model_cache_count(&model));
	if (be_model_cache_count(&model) != 0U ||
	    !require_result("finish protected entry",
			    be_model_finish_switch(&model),
			    BE_MODEL_OK) ||
	    !require_result("protected private read/write",
			    be_model_access(&model, PROTECTED_PRIVATE_GPA,
					    BE_RIGHT_READ |
						    BE_RIGHT_WRITE),
			    BE_MODEL_ALLOWED) ||
	    !require_result("protected cross-private denial",
			    be_model_access(&model, MANAGEMENT_PRIVATE_GPA,
					    BE_RIGHT_READ),
			    BE_MODEL_DENIED) ||
	    !require_result("protected channel read",
			    be_model_access(&model, SHARED_GPA,
					    BE_RIGHT_READ),
			    BE_MODEL_ALLOWED) ||
	    !require_result("protected channel write denial",
			    be_model_access(&model, SHARED_GPA,
					    BE_RIGHT_READ |
						    BE_RIGHT_WRITE),
			    BE_MODEL_DENIED) ||
	    !require_result("switch back to management",
			    be_model_begin_switch(
				    &model, BE_DOMAIN_MANAGEMENT),
			    BE_MODEL_OK) ||
	    !require_result("fence before management re-entry",
			    be_model_complete_fence(&model),
			    BE_MODEL_OK) ||
	    !require_result("finish management re-entry",
			    be_model_finish_switch(&model),
			    BE_MODEL_OK) ||
	    !require_result("read restored management state",
			    be_model_read_register(&model, 0U, &restored),
			    BE_MODEL_OK))
		return 1;
	if (restored != MANAGEMENT_SENTINEL) {
		fprintf(stderr, "management saved state was not restored\n");
		return 1;
	}

	printf("BE_MODEL_RESULT: PASS fixture=%s\n",
	       be_fixture_name(fixture));
	return 0;
}
