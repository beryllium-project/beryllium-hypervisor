// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Run security model v1's analyses on the generated policy-layer fixtures.
 *
 * Prints one verdict line per instance and per mutation, in the stable form
 * the differential check reads, each followed by its findings and notes:
 *
 *   BE_POLICY_VERDICT name=N A1=R ... A8=R identity=0x...
 *   BE_POLICY_FINDING name=N analysis=An code=C index=I first=F second=S
 *   BE_POLICY_NOTE name=N analysis=A5 code=C target=T writer=W
 *   BE_POLICY_BINDING name=N result=R
 *
 * where R is pass, fail, or not-run (A2 to A8 after an A1 failure). The
 * instances are compiled-in data; this tool reads no file.
 */
#include <stdio.h>

#include <be/policy_fixtures.h>

typedef int (*be_policy_analysis)(const struct be_policy_validated *,
				  struct be_policy_result *);

static const char *type_name(const struct be_policy_fixture *fixture,
			     be_u32 type)
{
	return type < fixture->names->type_count ? fixture->names->types[type] :
						   "invalid";
}

static void print_result(const struct be_policy_fixture *fixture,
			 be_size analysis,
			 const struct be_policy_result *result)
{
	be_size index;

	for (index = 0U; index < result->count &&
			 index < BE_POLICY_MAX_FINDINGS;
	     ++index) {
		const struct be_policy_finding *item = &result->items[index];

		if (item->code == BE_POLICY_A5_STATIC_SINGLE_WRITER) {
			printf("BE_POLICY_NOTE name=%s analysis=A%lu code=%s "
			       "target=%s writer=%s\n",
			       fixture->name, analysis,
			       be_policy_code_name(item->code),
			       type_name(fixture, item->first),
			       type_name(fixture, item->second));
			continue;
		}
		printf("BE_POLICY_FINDING name=%s analysis=A%lu code=%s "
		       "index=%u first=%u second=%u\n",
		       fixture->name, analysis, be_policy_code_name(item->code),
		       item->index, item->first, item->second);
	}
	if (result->count > BE_POLICY_MAX_FINDINGS)
		printf("BE_POLICY_FINDING name=%s analysis=A%lu more=%lu\n",
		       fixture->name, analysis,
		       result->count - BE_POLICY_MAX_FINDINGS);
}

/* Return: nonzero when every analysis passes. */
static int run_fixture(const struct be_policy_fixture *fixture)
{
	static const be_policy_analysis analyses[] = {
		be_policy_a2, be_policy_a3, (be_policy_analysis)0,
		be_policy_a5, be_policy_a6, be_policy_a7, be_policy_a8,
	};
	const struct be_raw_instance *instance = fixture->instance;
	struct be_policy_validated validated;
	struct be_policy_verdicts verdicts;
	struct be_policy_result result;
	be_size index;

	be_policy_verdicts(instance, &verdicts);
	printf("BE_POLICY_VERDICT name=%s", fixture->name);
	for (index = 0U; index < BE_POLICY_ANALYSES; ++index) {
		be_u32 bit = (be_u32)1U << index;

		printf(" A%lu=%s", index + 1U,
		       (verdicts.evaluated & bit) == 0U ? "not-run" :
		       (verdicts.failed & bit) != 0U	? "fail" :
							  "pass");
	}
	printf(" identity=0x%016lx\n",
	       be_combined_identity(be_view_identity(&instance->view),
				    be_policy_identity(&instance->policy),
				    be_labeling_identity(&instance->labeling)));
	if (be_policy_validate(&instance->policy, &instance->labeling,
			       &instance->view, &validated,
			       &result) != BE_POLICY_OK) {
		print_result(fixture, 1U, &result);
	} else {
		for (index = 0U; index < BE_ARRAY_SIZE(analyses); ++index) {
			if (analyses[index] == (be_policy_analysis)0)
				be_policy_a4(&validated, instance->needs,
					     instance->need_count, &result);
			else
				analyses[index](&validated, &result);
			print_result(fixture, index + 2U, &result);
		}
	}
	printf("BE_POLICY_BINDING name=%s result=%s\n", fixture->name,
	       be_binding_result_name(be_policy_check_bindings(
		       &instance->labeling, &instance->view)));
	return verdicts.failed == 0U;
}

int main(void)
{
	be_size passed = 0U;
	be_size index;

	for (index = 0U; index < be_policy_fixture_count(); ++index)
		passed += (be_size)run_fixture(be_policy_fixture(index));
	for (index = 0U; index < be_policy_mutation_count(); ++index)
		(void)run_fixture(be_policy_mutation(index));
	if (passed != be_policy_fixture_count()) {
		printf("BE_POLICY_RUN: FAIL instances=%lu passed=%lu\n",
		       be_policy_fixture_count(), passed);
		return 1;
	}
	printf("BE_POLICY_RUN: PASS instances=%lu mutations=%lu\n",
	       be_policy_fixture_count(), be_policy_mutation_count());
	return 0;
}
