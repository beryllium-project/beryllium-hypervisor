// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Host tests for the policy layer: A1 to A8, the decision function, the
 * adapter from Model 0.2's canonical state, sealing with policy, and the
 * static hart binding's checks.
 *
 * The instances are the generated fixtures (build/model/policy/fixtures.c);
 * each defect below is a copy of one with a single change. The expected
 * failing analyses are those mvp/tools/policy-check.py pins for the same
 * defects. Host evidence only: not a C refinement of the Rocq functions.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <be/fixtures.h>
#include <be/policy_fixtures.h>

#define CHECK(condition) check((condition) != 0, #condition, __LINE__)
#define EXPECTED_CHECKS 169U

#define A(n)		((be_u32)1U << ((n) - 1U))
#define READ		BE_POLICY_PERM_READ
#define WRITE		BE_POLICY_PERM_WRITE
#define MAP		BE_POLICY_PERM_MAP
#define MEMORY		BE_POLICY_CLASS_MEMORY
#define CHANNEL		BE_POLICY_CLASS_CHANNEL
#define DOMAIN		BE_POLICY_CLASS_DOMAIN

static be_size checks;

static void check(int ok, const char *text, int line)
{
	++checks;
	if (ok)
		return;
	fprintf(stderr, "policy_test.c:%d: check failed: %s\n", line, text);
	abort();
}

static const struct be_policy_fixture *fixture(const char *name)
{
	be_size index;

	for (index = 0U; index < be_policy_fixture_count(); ++index) {
		if (strcmp(be_policy_fixture(index)->name, name) == 0)
			return be_policy_fixture(index);
	}
	fprintf(stderr, "policy_test.c: no fixture %s\n", name);
	abort();
}

static struct be_raw_instance copy(const char *name)
{
	return *fixture(name)->instance;
}

static void set_perms(be_size *count, be_u32 *perms, const be_u32 *values,
		      be_size value_count)
{
	be_size index;

	*count = value_count;
	for (index = 0U; index < value_count; ++index)
		perms[index] = values[index];
}

static void add_rule(struct be_raw_instance *instance, be_u32 source,
		     be_u32 target, be_u32 class_id, const be_u32 *perms,
		     be_size count, int with_need)
{
	struct be_raw_rule *rule =
		&instance->policy.rules[instance->policy.rule_count++];

	rule->source = source;
	rule->target = target;
	rule->class_id = class_id;
	set_perms(&rule->perm_count, rule->perms, perms, count);
	if (with_need) {
		struct be_raw_need *need =
			&instance->needs[instance->need_count++];

		need->source = source;
		need->target = target;
		need->class_id = class_id;
		set_perms(&need->perm_count, need->perms, perms, count);
	}
}

static void append(be_size *count, be_u32 *perms, be_u32 permission)
{
	perms[(*count)++] = permission;
}

static be_u32 failed(const struct be_raw_instance *instance)
{
	struct be_policy_verdicts verdicts;

	be_policy_verdicts(instance, &verdicts);
	return verdicts.failed;
}

static enum be_policy_code validate(const struct be_raw_instance *instance)
{
	struct be_policy_validated validated;
	struct be_policy_result result;
	enum be_policy_code code =
		be_policy_validate(&instance->policy, &instance->labeling,
				   &instance->view, &validated, &result);

	check(code == BE_POLICY_OK ||
		      (result.count == 1U && result.items[0].code == code &&
		       validated.policy.rule_count == 0U),
	      "A1 reports its first finding and publishes nothing", __LINE__);
	return code;
}

static int same_relation(const struct be_policy_relation *left,
			 const struct be_policy_relation *right)
{
	return memcmp(left, right, sizeof(*left)) == 0;
}

static be_size pairs(const struct be_policy_relation *relation)
{
	be_size count = 0U;
	be_size source;
	be_u32 row;

	for (source = 0U; source < BE_POLICY_MAX_TYPES; ++source) {
		for (row = relation->row[source]; row != 0U; row &= row - 1U)
			++count;
	}
	return count;
}

static void expect_instance(const char *name, be_size grants, be_size flows,
			    const char *const *notes, be_size note_count,
			    enum be_binding_result binding)
{
	const struct be_policy_fixture *expected = fixture(name);
	const struct be_raw_instance *instance = expected->instance;
	const struct be_policy_names *names = expected->names;
	struct be_policy_validated validated;
	struct be_policy_verdicts verdicts;
	struct be_policy_result result;
	struct be_policy_relation flow;
	struct be_policy_relation channel;
	be_size undeclared = 1U;
	be_size index;

	be_policy_verdicts(instance, &verdicts);
	CHECK(verdicts.evaluated == 0xffU && verdicts.failed == 0U);
	CHECK(be_policy_validate(&instance->policy, &instance->labeling,
				 &instance->view, &validated,
				 &result) == BE_POLICY_OK);
	CHECK(instance->view.grant_count == grants);
	CHECK(be_policy_view_flows(&instance->view, &undeclared) == flows &&
	      undeclared == 0U);
	CHECK(be_policy_a5(&validated, &result) && result.failures == 0U &&
	      result.count == note_count);
	for (index = 0U; index < note_count; ++index) {
		const struct be_policy_finding *note = &result.items[index];

		CHECK(note->code == BE_POLICY_A5_STATIC_SINGLE_WRITER &&
		      strcmp(names->types[note->first], notes[2U * index]) ==
			      0 &&
		      strcmp(names->types[note->second],
			     notes[2U * index + 1U]) == 0);
	}
	be_policy_relations(&validated, &flow, &channel);
	CHECK(same_relation(&flow, &channel) && pairs(&flow) == flows);
	be_policy_closure(&flow);
	be_policy_closure(&channel);
	CHECK(same_relation(&flow, &channel));
	CHECK(be_policy_a7(&validated, &result) && result.count == 0U);
	CHECK(be_policy_check_bindings(&instance->labeling,
				       &instance->view) == binding);
}

static void test_instances(void)
{
	static const char *const instance1[] = { "shared_mp_t", "mgmt_t" };
	static const char *const instance2[] = { "shared_wr_t", "writer_t" };
	static const char *const instance3[] = { "req_t", "host_t", "resp_t",
						 "prot_t" };

	CHECK(be_policy_fixture_count() == 4U &&
	      be_policy_fixture(4U) == (const struct be_policy_fixture *)0);
	/* M3-5's seeded set (fixtures/mutations.json, count 91, seed 73). */
	CHECK(be_policy_mutation_count() == 91U &&
	      be_policy_mutation(91U) == (const struct be_policy_fixture *)0);
	expect_instance("instance1", 8U, 1U, instance1, 1U,
			BE_BINDING_NOT_APPLICABLE);
	expect_instance("instance2", 6U, 1U, instance2, 1U, BE_BINDING_OK);
	expect_instance("instance3", 12U, 2U, instance3, 2U, BE_BINDING_OK);
	expect_instance("instance1_m02", 6U, 1U, instance1, 1U,
			BE_BINDING_NOT_APPLICABLE);
	/* The MVP checker's policy identities for the same files. */
	CHECK(strcmp(fixture("instance2")->policy_sha256,
		     "4a1fac2bdea04cbcf4f3248c21cb41cf"
		     "2823625b46d284c45d9c69b6a25b8b2d") == 0);
	CHECK(strcmp(fixture("instance3")->policy_sha256,
		     "bfecfa923eaa64782cca2f662091de13"
		     "29eba2c969408a59f04a8c0234fc79aa") == 0);
	CHECK(fixture("instance1_m02")->projection != 0U &&
	      fixture("instance1")->projection == 0U);
}

static void test_a1_refusals(void)
{
	struct be_raw_instance instance = copy("instance2");
	struct be_policy_validated validated;

	CHECK(validate(&instance) == BE_POLICY_OK);
	instance.policy.rules[1].target = 9U;
	CHECK(validate(&instance) == BE_POLICY_A1_UNDECLARED_TYPE);
	CHECK(failed(&instance) == A(1));
	instance = copy("instance2");
	instance.policy.rules[2].perms[0] = READ;
	CHECK(validate(&instance) == BE_POLICY_A1_UNKNOWN_PERMISSION);
	instance = copy("instance2");
	instance.policy.rules[4].perm_count = 0U;
	CHECK(validate(&instance) == BE_POLICY_A1_EMPTY_PERMISSIONS);
	instance = copy("instance2");
	instance.policy.rules[4].perms[1] = READ;
	CHECK(validate(&instance) == BE_POLICY_A1_REPEATED_PERMISSION);
	instance = copy("instance2");
	instance.policy.rules[2].class_id = DOMAIN;
	CHECK(validate(&instance) == BE_POLICY_A1_UNDECLARED_CLASS);
	instance = copy("instance2");
	instance.labeling.label_count -= 1U;
	CHECK(validate(&instance) == BE_POLICY_A1_UNLABELED);
	instance = copy("instance2");
	instance.labeling.labels[instance.labeling.label_count++] =
		(struct be_raw_label){ BE_RAW_SUBJECT, 1U, 2U };
	CHECK(validate(&instance) == BE_POLICY_A1_DOUBLY_LABELED);
	instance = copy("instance2");
	instance.labeling.labels[5].type = 7U;
	CHECK(validate(&instance) == BE_POLICY_A1_UNDECLARED_TYPE);
	instance = copy("instance2");
	instance.labeling.labels[5].entity = 12U;
	CHECK(validate(&instance) == BE_POLICY_A1_UNKNOWN_ENTITY);
	instance = copy("instance2");
	instance.policy.types[instance.policy.type_count++] = 3U;
	CHECK(validate(&instance) == BE_POLICY_A1_DUPLICATE_TYPE);
	instance = copy("instance2");
	instance.policy.classes[1].class_id = MEMORY;
	CHECK(validate(&instance) == BE_POLICY_A1_DUPLICATE_CLASS);
	instance = copy("instance2");
	instance.policy.types[6] = BE_POLICY_MAX_TYPES;
	CHECK(validate(&instance) == BE_POLICY_A1_BOUND);
	instance = copy("instance2");
	instance.view.grants[1].object = 11U;
	CHECK(validate(&instance) == BE_POLICY_A1_UNLABELED);
	instance = copy("instance2");
	instance.labeling.objects[1].object = 0U;
	CHECK(validate(&instance) == BE_POLICY_A1_DUPLICATE_ENTITY);
	CHECK(be_policy_validate((const struct be_raw_policy *)0,
				 &instance.labeling, &instance.view, &validated,
				 (struct be_policy_result *)0) ==
	      BE_POLICY_NULL);
}

/* Single defects with the failing analyses policy-check.py pins for them. */
static void test_analysis_failures(void)
{
	static const be_u32 read[] = { READ };
	static const be_u32 write[] = { WRITE };
	static const be_u32 map[] = { MAP };
	static const be_u32 pause[] = { BE_POLICY_PERM_PAUSE };
	struct be_raw_instance instance = copy("instance2");
	struct be_policy_validated validated;
	struct be_policy_result result;

	/* A rule whose target labels no object. */
	instance.policy.types[instance.policy.type_count++] = 7U;
	add_rule(&instance, 1U, 7U, MEMORY, read, 1U, 1);
	CHECK(failed(&instance) == A(2));
	/* A domain type on monitor memory; a map of the reader's window. */
	instance = copy("instance2");
	add_rule(&instance, 1U, 6U, MEMORY, read, 1U, 1);
	CHECK(failed(&instance) == A(3));
	CHECK(be_policy_validate(&instance.policy, &instance.labeling,
				 &instance.view, &validated,
				 &result) == BE_POLICY_OK &&
	      !be_policy_a3(&validated, &result) &&
	      result.first_failure == BE_POLICY_A3_MONITOR_MEMORY);
	instance = copy("instance2");
	add_rule(&instance, 1U, 4U, MEMORY, map, 1U, 1);
	CHECK(failed(&instance) == A(3));
	/* Shared storage with no channel rule: the reader's dropped. */
	instance = copy("instance2");
	instance.policy.rule_count = 5U;
	instance.need_count = 5U;
	CHECK(failed(&instance) == (A(3) | A(6) | A(8)));
	/* The writer's channel rule widened; a rule with no need set. */
	instance = copy("instance2");
	append(&instance.policy.rules[2].perm_count,
	       instance.policy.rules[2].perms, BE_POLICY_PERM_RECEIVE);
	CHECK(failed(&instance) == A(4));
	instance = copy("instance2");
	instance.need_count = 5U;
	CHECK(failed(&instance) == A(4));
	/* A reader write rule on the shared page, its need included. */
	instance = copy("instance2");
	add_rule(&instance, 2U, 5U, MEMORY, write, 1U, 0);
	append(&instance.needs[4].perm_count, instance.needs[4].perms, WRITE);
	CHECK(failed(&instance) == (A(5) | A(6)));
	/* Two writers, both declared in both directions. */
	add_rule(&instance, 2U, 5U, CHANNEL,
		 (const be_u32[]){ BE_POLICY_PERM_SEND }, 1U, 0);
	add_rule(&instance, 1U, 5U, CHANNEL,
		 (const be_u32[]){ BE_POLICY_PERM_RECEIVE }, 1U, 0);
	append(&instance.needs[5].perm_count, instance.needs[5].perms,
	       BE_POLICY_PERM_SEND);
	append(&instance.needs[2].perm_count, instance.needs[2].perms,
	       BE_POLICY_PERM_RECEIVE);
	CHECK(failed(&instance) == A(5));
	/* A declared channel with no storage: the reader maps, cannot read. */
	instance = copy("instance2");
	instance.policy.rules[4].perms[0] = MAP;
	instance.policy.rules[4].perm_count = 1U;
	CHECK(failed(&instance) == (A(6) | A(8)));
	/* The manifest grants G0 execute on the shared page. */
	instance = copy("instance2");
	append(&instance.view.grants[1].perm_count, instance.view.grants[1].perms,
	       BE_POLICY_PERM_EXECUTE);
	CHECK(failed(&instance) == A(8));
	/* Instance 3: a domain rule on its own type, then on a page type. */
	instance = copy("instance3");
	add_rule(&instance, 1U, 1U, DOMAIN, pause, 1U, 1);
	CHECK(failed(&instance) == A(3));
	instance = copy("instance3");
	add_rule(&instance, 1U, 5U, DOMAIN, pause, 1U, 1);
	CHECK(failed(&instance) == (A(2) | A(3)));
	/* A management grant without a rule: G1 pauses G0. */
	instance = copy("instance3");
	instance.view.grants[instance.view.grant_count++] =
		(struct be_raw_grant){ 2U, 1U, DOMAIN, 1U, { BE_POLICY_PERM_PAUSE } };
	CHECK(failed(&instance) == A(8));
	/* The secret readable by the host; a channel rule without memory. */
	instance = copy("instance3");
	add_rule(&instance, 1U, 7U, MEMORY, (const be_u32[]){ READ, MAP }, 2U,
		 1);
	CHECK(failed(&instance) == A(3));
	instance = copy("instance3");
	instance.policy.rules[7] = instance.policy.rules[11];
	instance.policy.rule_count = 11U;
	CHECK(failed(&instance) == (A(3) | A(6) | A(8)));
	/* A domain permission beyond pause and terminate. */
	instance = copy("instance3");
	append(&instance.policy.rules[5].perm_count,
	       instance.policy.rules[5].perms, BE_POLICY_PERM_ENTER);
	append(&instance.needs[5].perm_count, instance.needs[5].perms,
	       BE_POLICY_PERM_ENTER);
	CHECK(failed(&instance) == A(7));
}

static void test_decide(void)
{
	const struct be_raw_instance *instance = fixture("instance1")->instance;
	struct be_policy_validated validated;
	struct be_raw_policy empty;
	be_size allowed = 0U;
	be_u32 source;
	be_u32 target;
	be_u32 class_id;
	be_u32 perm;

	CHECK(be_policy_validate(&instance->policy, &instance->labeling,
				 &instance->view, &validated,
				 (struct be_policy_result *)0) == BE_POLICY_OK);
	CHECK(be_policy_decide(&validated, 1U, 3U, MEMORY, READ));
	/* B2's denied load and store are the policy's deny. */
	CHECK(!be_policy_decide(&validated, 2U, 3U, MEMORY, READ));
	CHECK(!be_policy_decide(&validated, 2U, 7U, MEMORY, WRITE));
	CHECK(be_policy_decide(&validated, 2U, 7U, CHANNEL,
			       BE_POLICY_PERM_RECEIVE));
	CHECK(!be_policy_decide(&validated, 0U, 8U, MEMORY, READ));
	CHECK(!be_policy_decide(&validated, 99U, 99U, 99U, 99U));
	CHECK(!be_policy_decide((const struct be_policy_validated *)0, 1U, 3U,
				MEMORY, READ));
	/* Total and default-deny: exactly the rules' 19 permissions allow. */
	for (source = 0U; source < BE_POLICY_MAX_TYPES; ++source)
		for (target = 0U; target < BE_POLICY_MAX_TYPES; ++target)
			for (class_id = 0U; class_id < BE_POLICY_MAX_CLASSES;
			     ++class_id)
				for (perm = 0U; perm < BE_POLICY_MAX_PERMS;
				     ++perm)
					allowed += (be_size)be_policy_decide(
						&validated, source, target,
						class_id, perm);
	CHECK(allowed == 19U);
	empty = instance->policy;
	empty.rule_count = 0U;
	CHECK(be_policy_validate(&empty, &instance->labeling, &instance->view,
				 &validated, (struct be_policy_result *)0) ==
		      BE_POLICY_OK &&
	      !be_policy_decide(&validated, 1U, 3U, MEMORY, READ));
}

static struct be_canonical_state canonical(enum be_fixture_id id)
{
	struct be_canonical_state state;

	CHECK(be_canonicalize(be_fixture_inventory(), be_fixture_proposal(id),
			      &state) == BE_CHECK_OK);
	return state;
}

static void test_adapter(void)
{
	const struct be_raw_view *projection =
		&fixture("instance1_m02")->instance->view;
	struct be_canonical_state state = canonical(BE_FIXTURE_SOURCE_A);
	struct be_raw_view view;
	struct be_raw_view other;

	CHECK(be_view_of_canonical(&state, &view) == BE_POLICY_OK);
	CHECK(be_raw_view_equal(&view, projection));
	CHECK(view.ownership_count == 2U && view.channel_count == 1U &&
	      view.grant_count == 6U && view.binding_count == 0U &&
	      view.hart_count == 1U && view.harts[0] == 0U);
	state = canonical(BE_FIXTURE_SOURCE_B);
	CHECK(be_view_of_canonical(&state, &other) == BE_POLICY_OK &&
	      be_raw_view_equal(&other, projection));
	other.grants[4].perms[1] = WRITE;
	CHECK(!be_raw_view_equal(&other, projection));
	state.configuration_id ^= 1U;
	CHECK(be_view_of_canonical(&state, &view) ==
		      BE_POLICY_SEAL_CANONICAL &&
	      view.grant_count == 0U);
	CHECK(be_view_of_canonical((const struct be_canonical_state *)0,
				   &view) == BE_POLICY_NULL);
}

static enum be_policy_code seal(const struct be_canonical_state *state,
				const struct be_raw_instance *instance,
				struct be_sealed_with_policy *sealed)
{
	enum be_policy_code code = be_seal_with_policy(
		state, &instance->policy, &instance->labeling, instance->needs,
		instance->need_count, sealed);

	check(code == BE_POLICY_OK || sealed->configuration_identity == 0U,
	      "a refused seal publishes no identity", __LINE__);
	return code;
}

static void test_seal(void)
{
	static const be_u32 read[] = { READ };
	static const be_u32 write[] = { WRITE };
	const struct be_raw_instance *projection =
		fixture("instance1_m02")->instance;
	struct be_canonical_state state = canonical(BE_FIXTURE_SOURCE_A);
	struct be_canonical_state other = canonical(BE_FIXTURE_SOURCE_B);
	struct be_sealed_with_policy sealed;
	struct be_sealed_with_policy again;
	struct be_raw_instance instance;
	be_size index;

	CHECK(seal(&state, projection, &sealed) == BE_POLICY_OK);
	CHECK(sealed.canonical_identity == BE_U64_C(0x2a4c5a62bc446015) &&
	      sealed.policy_identity == be_policy_identity(&projection->policy) &&
	      sealed.labeling_identity ==
		      be_labeling_identity(&projection->labeling) &&
	      sealed.configuration_identity ==
		      be_combined_identity(sealed.canonical_identity,
					   sealed.policy_identity,
					   sealed.labeling_identity));
	CHECK(sealed.configuration_identity == BE_U64_C(0x97cc83217469369d));
	CHECK(seal(&other, projection, &again) == BE_POLICY_OK &&
	      memcmp(&sealed, &again, sizeof(sealed)) == 0);
	/* Need sets are inputs to A4, not to the identity. */
	instance = *projection;
	for (index = 0U; index < instance.need_count; ++index)
		instance.needs[index] =
			projection->needs[instance.need_count - 1U - index];
	CHECK(seal(&state, &instance, &again) == BE_POLICY_OK &&
	      memcmp(&sealed, &again, sizeof(sealed)) == 0);

	/* Each failing analysis refuses; the first failing finding is why. */
	instance = *projection;
	instance.policy.rules[0].source = 7U;
	CHECK(seal(&state, &instance, &sealed) ==
	      BE_POLICY_A1_UNDECLARED_TYPE);
	instance = *projection;
	instance.policy.types[instance.policy.type_count++] = 7U;
	add_rule(&instance, 1U, 7U, MEMORY, read, 1U, 1);
	CHECK(seal(&state, &instance, &sealed) ==
	      BE_POLICY_A2_TARGET_UNREACHABLE);
	instance = *projection;
	add_rule(&instance, 1U, 6U, MEMORY, read, 1U, 1);
	CHECK(seal(&state, &instance, &sealed) == BE_POLICY_A3_MONITOR_MEMORY);
	instance = *projection;
	instance.policy.rules[4] = instance.policy.rules[5];
	instance.policy.rule_count = 5U;
	CHECK(seal(&state, &instance, &sealed) ==
	      BE_POLICY_A3_CHANNEL_WITHOUT_STORAGE);
	instance = *projection;
	instance.need_count -= 1U;
	CHECK(seal(&state, &instance, &sealed) == BE_POLICY_A4_NO_NEED);
	instance = *projection;
	add_rule(&instance, 2U, 5U, MEMORY, write, 1U, 0);
	append(&instance.needs[4].perm_count, instance.needs[4].perms, WRITE);
	CHECK(seal(&state, &instance, &sealed) ==
	      BE_POLICY_A5_MULTIPLE_WRITERS);
	instance = *projection;
	instance.policy.rules[4].perms[0] = MAP;
	instance.policy.rules[4].perm_count = 1U;
	CHECK(seal(&state, &instance, &sealed) ==
	      BE_POLICY_A6_UNREALIZED_CHANNEL);
	instance = *projection;
	instance.policy.rules[0].perm_count = 2U;
	CHECK(seal(&state, &instance, &sealed) == BE_POLICY_A8_UNALLOWED);
	/* A7 is not a sealing condition: a domain permission alone seals. */
	instance = *projection;
	instance.policy.classes[instance.policy.class_count++] =
		(struct be_raw_class){ DOMAIN, 4U, { 6U, 7U, 8U, 9U } };
	add_rule(&instance, 1U, 2U, DOMAIN,
		 (const be_u32[]){ BE_POLICY_PERM_ENTER }, 1U, 1);
	CHECK(failed(&instance) == A(7) &&
	      seal(&state, &instance, &sealed) == BE_POLICY_OK);
	/* Another configuration's labeling, a changed state, no state. */
	CHECK(seal(&state, fixture("instance2")->instance, &sealed) ==
	      BE_POLICY_SEAL_CONFIGURATION);
	other.frames[0].base += BE_PAGE_SIZE;
	CHECK(seal(&other, projection, &sealed) == BE_POLICY_SEAL_CANONICAL);
	CHECK(seal((const struct be_canonical_state *)0, projection,
		   &sealed) == BE_POLICY_NULL);
}

static be_u64 seal_view(const char *name)
{
	const struct be_raw_instance *instance = fixture(name)->instance;
	struct be_sealed_with_policy sealed;

	CHECK(be_seal_view_with_policy(
		      &instance->view, be_view_identity(&instance->view),
		      &instance->policy, &instance->labeling, instance->needs,
		      instance->need_count, &sealed) == BE_POLICY_OK);
	return sealed.configuration_identity;
}

static void test_identities(void)
{
	struct be_raw_instance instance = copy("instance3");
	be_u64 policy = be_policy_identity(&instance.policy);
	be_u64 labeling = be_labeling_identity(&instance.labeling);
	be_u64 view = be_view_identity(&instance.view);

	CHECK(seal_view("instance1") == BE_U64_C(0x63c22d4da9dcedfa));
	CHECK(seal_view("instance2") == BE_U64_C(0x109e99ab2a212420));
	CHECK(seal_view("instance3") == BE_U64_C(0x735e5d85aea8ba73));
	CHECK(seal_view("instance1_m02") == BE_U64_C(0x2145ed531d6de1c8));
	CHECK(policy == BE_U64_C(0xc3b09774674d8be8) &&
	      labeling == BE_U64_C(0x52a3bf8f54d7692c) &&
	      view == BE_U64_C(0x3693da3361e29728));
	instance.policy.rules[5].perms[0] = BE_POLICY_PERM_TERMINATE;
	instance.labeling.labels[7].type = 6U;
	instance.view.grants[0].perms[0] = READ;
	CHECK(be_policy_identity(&instance.policy) != policy &&
	      be_labeling_identity(&instance.labeling) != labeling &&
	      be_view_identity(&instance.view) != view);
	CHECK(be_combined_identity(view, policy, labeling) !=
	      be_combined_identity(policy, view, labeling));
	instance.policy.rule_count = BE_POLICY_MAX_RULES + 1U;
	CHECK(be_policy_identity(&instance.policy) == 0U &&
	      be_policy_identity((const struct be_raw_policy *)0) == 0U);
}

static void test_bindings(void)
{
	struct be_raw_instance instance = copy("instance3");
	const struct be_raw_labeling *labeling = &instance.labeling;

	instance.view.bindings[1].hart = 1U;
	CHECK(be_policy_check_bindings(labeling, &instance.view) ==
	      BE_BINDING_NOT_INJECTIVE);
	instance = copy("instance3");
	instance.view.bindings[0].hart = 0U;
	CHECK(be_policy_check_bindings(labeling, &instance.view) ==
	      BE_BINDING_CONTROL_HART);
	instance = copy("instance3");
	instance.view.binding_count = 1U;
	CHECK(be_policy_check_bindings(labeling, &instance.view) ==
	      BE_BINDING_NOT_TOTAL);
	instance = copy("instance3");
	instance.view.bindings[1].domain = 1U;
	CHECK(be_policy_check_bindings(labeling, &instance.view) ==
	      BE_BINDING_NOT_TOTAL);
	instance = copy("instance3");
	instance.view.bindings[1].hart = 5U;
	CHECK(be_policy_check_bindings(labeling, &instance.view) ==
	      BE_BINDING_UNKNOWN);
	instance = copy("instance3");
	instance.view.bindings[0].domain = BE_POLICY_MONITOR_SUBJECT;
	CHECK(be_policy_check_bindings(labeling, &instance.view) ==
	      BE_BINDING_UNKNOWN);
	instance = copy("instance3");
	instance.view.control_hart = 3U;
	CHECK(be_policy_check_bindings(labeling, &instance.view) ==
	      BE_BINDING_UNKNOWN);
	/* The binding is outside A8: a binding defect fails no analysis. */
	instance = copy("instance3");
	instance.view.bindings[1].hart = 1U;
	CHECK(failed(&instance) == 0U);
}

int main(void)
{
	test_instances();
	test_a1_refusals();
	test_analysis_failures();
	test_decide();
	test_adapter();
	test_seal();
	test_identities();
	test_bindings();
	CHECK(checks == EXPECTED_CHECKS - 1U);
	printf("Beryllium policy layer unit tests: PASS checks=%lu "
	       "instances=%lu mutations=%lu\n",
	       checks, be_policy_fixture_count(), be_policy_mutation_count());
	return 0;
}
