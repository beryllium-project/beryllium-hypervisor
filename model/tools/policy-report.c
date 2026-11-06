// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Emit a deterministic report of the policy layer's instances.
 *
 * For each generated instance: its counts, its identities, A1 to A8 with
 * the details mvp/tools/policy-check.py writes for the same results, and
 * its hart binding; then the adapter from Model 0.2's canonical state and
 * the policy-sealed identity of the projection. Identities are reporting
 * and equivalence scalars, not cryptographic measurements.
 */
#include <stdio.h>
#include <string.h>

#include <be/fixtures.h>
#include <be/policy_fixtures.h>

#define DETAIL_BYTES 512U

struct detail {
	char text[DETAIL_BYTES];
	be_size length;
};

static void append(struct detail *detail, const char *text)
{
	while (*text != '\0' && detail->length + 1U < DETAIL_BYTES)
		detail->text[detail->length++] = *text++;
	detail->text[detail->length] = '\0';
}

static const char *type_name(const struct be_policy_names *names,
			     be_u32 type)
{
	return type < names->type_count ? names->types[type] : "invalid";
}

/* Sort type pairs (or single types, second zero) by their names. */
static void sort_pairs(const struct be_policy_names *names, be_u32 *first,
		       be_u32 *second, be_size count)
{
	be_size index;
	be_size position;

	for (index = 1U; index < count; ++index) {
		be_u32 left = first[index];
		be_u32 right = second[index];

		for (position = index; position > 0U; --position) {
			int order = strcmp(type_name(names, first[position - 1U]),
					   type_name(names, left));

			if (order < 0 ||
			    (order == 0 &&
			     strcmp(type_name(names, second[position - 1U]),
				    type_name(names, right)) <= 0))
				break;
			first[position] = first[position - 1U];
			second[position] = second[position - 1U];
		}
		first[position] = left;
		second[position] = right;
	}
}

static void relation_text(const struct be_policy_names *names,
			  const struct be_policy_relation *relation,
			  struct detail *detail)
{
	be_u32 first[BE_POLICY_MAX_TYPES * BE_POLICY_MAX_TYPES];
	be_u32 second[BE_POLICY_MAX_TYPES * BE_POLICY_MAX_TYPES];
	be_size count = 0U;
	be_u32 source;
	be_u32 target;
	be_size index;

	for (source = 0U; source < BE_POLICY_MAX_TYPES; ++source) {
		for (target = 0U; target < BE_POLICY_MAX_TYPES; ++target) {
			if ((relation->row[source] & ((be_u32)1U << target)) !=
			    0U) {
				first[count] = source;
				second[count++] = target;
			}
		}
	}
	sort_pairs(names, first, second, count);
	append(detail, "{");
	for (index = 0U; index < count; ++index) {
		append(detail, index == 0U ? "(" : ", (");
		append(detail, type_name(names, first[index]));
		append(detail, ", ");
		append(detail, type_name(names, second[index]));
		append(detail, ")");
	}
	append(detail, "}");
}

static void a5_text(const struct be_policy_names *names,
		    const struct be_policy_result *result,
		    struct detail *detail)
{
	be_u32 targets[BE_POLICY_MAX_FINDINGS];
	be_u32 writers[BE_POLICY_MAX_FINDINGS];
	be_size count = 0U;
	be_size index;

	for (index = 0U; index < result->count &&
			 index < BE_POLICY_MAX_FINDINGS;
	     ++index) {
		targets[count] = result->items[index].first;
		writers[count++] = result->items[index].second;
	}
	sort_pairs(names, targets, writers, count);
	for (index = 0U; index < count; ++index) {
		append(detail, index == 0U ? "" : "; ");
		append(detail, type_name(names, targets[index]));
		append(detail, ": static, not revocable, single writer ");
		append(detail, type_name(names, writers[index]));
	}
	if (count == 0U)
		append(detail, "no shared writable storage");
}

static void print_check(be_size analysis, int pass, const char *detail,
			int last)
{
	printf("        {\"analysis\":\"A%lu\",\"result\":\"%s\","
	       "\"detail\":\"%s\"}%s\n",
	       analysis, pass ? "pass" : "fail", detail, last ? "" : ",");
}

static void failure_text(const struct be_policy_result *result,
			 struct detail *detail)
{
	char text[96];

	snprintf(text, sizeof(text), "%lu findings, the first %s",
		 result->failures, be_policy_code_name(result->first_failure));
	append(detail, text);
}

static void report_checks(const struct be_policy_fixture *fixture)
{
	const struct be_raw_instance *instance = fixture->instance;
	const struct be_policy_names *names = fixture->names;
	struct be_policy_validated validated;
	struct be_policy_result result;
	struct be_policy_relation flows;
	struct be_policy_relation channels;
	struct detail detail = { { 0 }, 0U };
	char text[DETAIL_BYTES];
	be_size index;
	int domains = 0;
	int pass;

	printf("      \"checks\":[\n");
	if (be_policy_validate(&instance->policy, &instance->labeling,
			       &instance->view, &validated,
			       &result) != BE_POLICY_OK) {
		failure_text(&result, &detail);
		print_check(1U, 0, detail.text, 0);
		for (index = 2U; index <= BE_POLICY_ANALYSES; ++index)
			printf("        {\"analysis\":\"A%lu\",\"result\":"
			       "\"not-run\",\"detail\":\"A1 failed: nothing "
			       "downstream is evaluated\"}%s\n",
			       index, index == BE_POLICY_ANALYSES ? "" : ",");
		printf("      ],\n");
		return;
	}
	for (index = 0U; index < instance->policy.rule_count; ++index)
		domains |= instance->policy.rules[index].class_id ==
			   BE_POLICY_CLASS_DOMAIN;
	snprintf(text, sizeof(text),
		 "%lu types, %lu classes, %lu rules; %lu subjects and %lu "
		 "objects, each labeled once",
		 instance->policy.type_count, instance->policy.class_count,
		 instance->policy.rule_count, instance->labeling.subject_count,
		 instance->labeling.object_count);
	print_check(1U, 1, text, 0);

	pass = be_policy_a2(&validated, &result);
	snprintf(text, sizeof(text),
		 "%lu rules, each reachable under the labeling",
		 instance->policy.rule_count);
	detail = (struct detail){ { 0 }, 0U };
	failure_text(&result, &detail);
	print_check(2U, pass, pass ? text : detail.text, 0);

	pass = be_policy_a3(&validated, &result);
	detail = (struct detail){ { 0 }, 0U };
	if (pass) {
		append(&detail, "no domain type holds a permission on monitor "
				"memory or map on another domain's private "
				"type; every channel rule has its storage, and "
				"all shared storage its channel rules");
		if (domains)
			append(&detail, "; every domain rule names another "
					"domain's type");
	} else {
		failure_text(&result, &detail);
	}
	print_check(3U, pass, detail.text, 0);

	pass = be_policy_a4(&validated, instance->needs, instance->need_count,
			    &result);
	snprintf(text, sizeof(text), "%lu rules, each within its need set",
		 instance->policy.rule_count);
	detail = (struct detail){ { 0 }, 0U };
	failure_text(&result, &detail);
	print_check(4U, pass, pass ? text : detail.text, 0);

	pass = be_policy_a5(&validated, &result);
	detail = (struct detail){ { 0 }, 0U };
	if (pass)
		a5_text(names, &result, &detail);
	else
		failure_text(&result, &detail);
	print_check(5U, pass, detail.text, 0);

	pass = be_policy_a6(&validated, &result);
	detail = (struct detail){ { 0 }, 0U };
	be_policy_relations(&validated, &flows, &channels);
	if (!pass) {
		failure_text(&result, &detail);
	} else if (memcmp(&flows, &channels, sizeof(flows)) == 0) {
		append(&detail, "F = D = ");
		relation_text(names, &channels, &detail);
		append(&detail, "; F+ = D+");
	} else {
		append(&detail, "F = ");
		relation_text(names, &flows, &detail);
		append(&detail, ", D = ");
		relation_text(names, &channels, &detail);
		append(&detail, "; F+ = D+");
	}
	print_check(6U, pass, detail.text, 0);

	pass = be_policy_a7(&validated, &result);
	detail = (struct detail){ { 0 }, 0U };
	if (pass)
		append(&detail,
		       domains ? "vacuous: domains hold only pause and "
				 "terminate, which make no grant, and no "
				 "delegation exists" :
				 "vacuous: no domain holds a domain permission "
				 "and no delegation exists");
	else
		failure_text(&result, &detail);
	print_check(7U, pass, detail.text, 0);

	pass = be_policy_a8(&validated, &result);
	snprintf(text, sizeof(text), "%lu grants, each allowed by its rule",
		 instance->view.grant_count);
	detail = (struct detail){ { 0 }, 0U };
	failure_text(&result, &detail);
	print_check(8U, pass, pass ? text : detail.text, 1);
	printf("      ],\n");
}

static void report_instance(const struct be_policy_fixture *fixture,
			    int last)
{
	const struct be_raw_instance *instance = fixture->instance;
	be_u64 view = be_view_identity(&instance->view);
	be_u64 policy = be_policy_identity(&instance->policy);
	be_u64 labeling = be_labeling_identity(&instance->labeling);
	be_size undeclared = 0U;
	be_size flows = be_policy_view_flows(&instance->view, &undeclared);

	printf("    {\n");
	printf("      \"name\":\"%s\",\n", fixture->name);
	printf("      \"source\":\"%s\",\n", fixture->source);
	printf("      \"policy_sha256\":\"%s\",\n", fixture->policy_sha256);
	printf("      \"projection\":%s,\n",
	       fixture->projection != 0U ? "true" : "false");
	printf("      \"counts\":{\"types\":%lu,\"classes\":%lu,"
	       "\"rules\":%lu,\"subjects\":%lu,\"objects\":%lu,"
	       "\"labels\":%lu,\"needs\":%lu,\"ownerships\":%lu,"
	       "\"channels\":%lu,\"grants\":%lu,\"flows\":%lu,"
	       "\"undeclared_flows\":%lu,\"bindings\":%lu,\"harts\":%lu},\n",
	       instance->policy.type_count, instance->policy.class_count,
	       instance->policy.rule_count, instance->labeling.subject_count,
	       instance->labeling.object_count, instance->labeling.label_count,
	       instance->need_count, instance->view.ownership_count,
	       instance->view.channel_count, instance->view.grant_count, flows,
	       undeclared, instance->view.binding_count,
	       instance->view.hart_count);
	printf("      \"identity\":{\"view\":\"0x%016lx\","
	       "\"policy\":\"0x%016lx\",\"labeling\":\"0x%016lx\","
	       "\"configuration\":\"0x%016lx\"},\n",
	       view, policy, labeling,
	       be_combined_identity(view, policy, labeling));
	report_checks(fixture);
	printf("      \"binding\":\"%s\"\n",
	       be_binding_result_name(be_policy_check_bindings(
		       &instance->labeling, &instance->view)));
	printf("    }%s\n", last ? "" : ",");
}

/* Return: nonzero when both canonical sources give the projection's view. */
static int report_adapter(const struct be_policy_fixture *projection)
{
	static const enum be_fixture_id sources[] = { BE_FIXTURE_SOURCE_A,
						      BE_FIXTURE_SOURCE_B };
	const struct be_raw_instance *instance = projection->instance;
	struct be_sealed_with_policy sealed[2];
	enum be_policy_code code[2];
	int equal = 1;
	be_size index;

	for (index = 0U; index < BE_ARRAY_SIZE(sources); ++index) {
		struct be_canonical_state canonical;
		struct be_raw_view view;

		equal &= be_canonicalize(be_fixture_inventory(),
					 be_fixture_proposal(sources[index]),
					 &canonical) == BE_CHECK_OK &&
			 be_view_of_canonical(&canonical, &view) ==
				 BE_POLICY_OK &&
			 be_raw_view_equal(&view, &instance->view);
		code[index] = be_seal_with_policy(
			&canonical, &instance->policy, &instance->labeling,
			instance->needs, instance->need_count, &sealed[index]);
	}
	equal &= code[0] == code[1] &&
		 memcmp(&sealed[0], &sealed[1], sizeof(sealed[0])) == 0;
	printf("  \"adapter\":{\n");
	printf("    \"fixtures\":[\"%s\",\"%s\"],\n",
	       be_fixture_name(BE_FIXTURE_SOURCE_A),
	       be_fixture_name(BE_FIXTURE_SOURCE_B));
	printf("    \"projection\":\"%s\",\n", projection->name);
	printf("    \"view_equals_projection\":%s,\n", equal ? "true" : "false");
	printf("    \"seal\":\"%s\",\n", be_policy_code_name(code[0]));
	printf("    \"identity\":{\"canonical\":\"0x%016lx\","
	       "\"policy\":\"0x%016lx\",\"labeling\":\"0x%016lx\","
	       "\"configuration\":\"0x%016lx\"}\n",
	       sealed[0].canonical_identity, sealed[0].policy_identity,
	       sealed[0].labeling_identity, sealed[0].configuration_identity);
	printf("  },\n");
	return equal && code[0] == BE_POLICY_OK;
}

int main(void)
{
	const struct be_policy_fixture *projection =
		(const struct be_policy_fixture *)0;
	be_size count = be_policy_fixture_count();
	be_size index;
	int adapter;

	printf("{\n");
	printf("  \"schema\":\"be-model-policy-report-v1\",\n");
	printf("  \"model_version\":%u,\n", BE_MODEL_VERSION);
	printf("  \"instances\":[\n");
	for (index = 0U; index < count; ++index) {
		const struct be_policy_fixture *fixture =
			be_policy_fixture(index);

		if (fixture->projection != 0U)
			projection = fixture;
		report_instance(fixture, index + 1U == count);
	}
	printf("  ],\n");
	printf("  \"mutations\":%lu,\n", be_policy_mutation_count());
	if (projection == (const struct be_policy_fixture *)0) {
		fprintf(stderr, "policy-report: no projection fixture\n");
		return 1;
	}
	adapter = report_adapter(projection);
	printf("  \"identity_use\":\"deterministic-reporting-only\",\n");
	printf("  \"claim_scope\":\"bounded-host-checker-not-a-refinement\"\n");
	printf("}\n");
	return adapter ? 0 : 1;
}
