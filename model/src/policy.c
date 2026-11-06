// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

/*
 * Security model v1's analyses over bounded raw policy-layer data (MVP M3-4).
 *
 * A1 validates raw identifiers into a typed labeling; A2 to A8 follow
 * security model v1 Part 3 as the MVP's offline checker,
 * mvp/tools/policy-check.py, reads it, so that the two checkers and the Rocq
 * oracle can be compared verdict by verdict. Sealing with policy wraps
 * Model 0.2's accepted canonical state and admits it only when A1 to A6 and
 * A8 pass. Host evidence only: no C refinement of the Rocq functions.
 */
#include <be/policy.h>

#define TYPE_BIT(type)		((be_u32)1U << (type))
#define IDENTITY_POLICY		BE_U64_C(1)
#define IDENTITY_LABELING	BE_U64_C(2)
#define IDENTITY_VIEW		BE_U64_C(3)
#define IDENTITY_COMBINED	BE_U64_C(4)

_Static_assert(BE_POLICY_MAX_TYPES <= 32U, "type sets are 32-bit masks");
_Static_assert(BE_MAX_RESOURCES <= BE_POLICY_MAX_OWNERSHIPS &&
		       BE_MAX_RESOURCES + BE_MAX_CHANNELS <=
			       BE_POLICY_MAX_OBJECTS &&
		       BE_MAX_DOMAINS + 1U <= BE_POLICY_MAX_SUBJECTS &&
		       BE_MAX_CHANNELS <= BE_POLICY_MAX_CHANNELS &&
		       BE_MAX_AUTHORITIES + 2U * BE_MAX_CHANNELS <=
			       BE_POLICY_MAX_GRANTS,
	       "Model 0.2's canonical state fits the policy view");

static int list_has(const be_u32 *list, be_size count, be_u32 value)
{
	be_size index;

	for (index = 0U; index < count; ++index) {
		if (list[index] == value)
			return 1;
	}
	return 0;
}

static int list_repeats(const be_u32 *list, be_size count)
{
	be_size index;

	for (index = 1U; index < count; ++index) {
		if (list_has(list, index, list[index]))
			return 1;
	}
	return 0;
}

static void result_reset(struct be_policy_result *result)
{
	*result = (struct be_policy_result){ 0 };
}

static void result_add(struct be_policy_result *result,
		       enum be_policy_code code, be_size index, be_u32 first,
		       be_u32 second)
{
	if (result->count < BE_POLICY_MAX_FINDINGS) {
		struct be_policy_finding *item = &result->items[result->count];

		item->code = code;
		item->index = (be_u32)index;
		item->first = first;
		item->second = second;
	}
	++result->count;
	if (code == BE_POLICY_A5_STATIC_SINGLE_WRITER)
		return;
	if (result->failures == 0U)
		result->first_failure = code;
	++result->failures;
}

static const struct be_raw_class *
find_class(const struct be_raw_policy *policy, be_u32 class_id)
{
	be_size index;

	for (index = 0U; index < policy->class_count; ++index) {
		if (policy->classes[index].class_id == class_id)
			return &policy->classes[index];
	}
	return (const struct be_raw_class *)0;
}

static int subject_listed(const struct be_raw_labeling *labeling,
			  be_u32 subject)
{
	return list_has(labeling->subjects, labeling->subject_count, subject);
}

static int object_listed(const struct be_raw_labeling *labeling,
			 be_u32 object)
{
	be_size index;

	for (index = 0U; index < labeling->object_count; ++index) {
		if (labeling->objects[index].object == object)
			return 1;
	}
	return 0;
}

static enum be_policy_code
check_bounds(const struct be_raw_policy *policy,
	     const struct be_raw_labeling *labeling,
	     const struct be_raw_view *view, be_size *where)
{
	be_size index;

	if (policy->type_count > BE_POLICY_MAX_TYPES ||
	    policy->class_count > BE_POLICY_MAX_CLASSES ||
	    policy->rule_count > BE_POLICY_MAX_RULES ||
	    labeling->subject_count > BE_POLICY_MAX_SUBJECTS ||
	    labeling->object_count > BE_POLICY_MAX_OBJECTS ||
	    labeling->label_count > BE_POLICY_MAX_LABELS ||
	    view->ownership_count > BE_POLICY_MAX_OWNERSHIPS ||
	    view->channel_count > BE_POLICY_MAX_CHANNELS ||
	    view->grant_count > BE_POLICY_MAX_GRANTS ||
	    view->binding_count > BE_POLICY_MAX_BINDINGS ||
	    view->hart_count > BE_POLICY_MAX_HARTS)
		return BE_POLICY_A1_BOUND;
	for (index = 0U; index < policy->type_count; ++index) {
		*where = index;
		if (policy->types[index] >= BE_POLICY_MAX_TYPES)
			return BE_POLICY_A1_BOUND;
	}
	for (index = 0U; index < policy->class_count; ++index) {
		*where = index;
		if (policy->classes[index].perm_count > BE_POLICY_MAX_PERMS)
			return BE_POLICY_A1_BOUND;
	}
	for (index = 0U; index < policy->rule_count; ++index) {
		*where = index;
		if (policy->rules[index].perm_count > BE_POLICY_MAX_PERMS)
			return BE_POLICY_A1_BOUND;
	}
	for (index = 0U; index < labeling->subject_count; ++index) {
		*where = index;
		if (labeling->subjects[index] >= BE_POLICY_MAX_SUBJECTS)
			return BE_POLICY_A1_BOUND;
	}
	for (index = 0U; index < labeling->object_count; ++index) {
		*where = index;
		if (labeling->objects[index].object >= BE_POLICY_MAX_OBJECTS)
			return BE_POLICY_A1_BOUND;
	}
	for (index = 0U; index < view->grant_count; ++index) {
		*where = index;
		if (view->grants[index].perm_count > BE_POLICY_MAX_PERMS)
			return BE_POLICY_A1_BOUND;
	}
	return BE_POLICY_OK;
}

static enum be_policy_code check_policy(const struct be_raw_policy *policy,
					be_size *where, be_u32 *what)
{
	be_size index;
	be_size perm;

	for (index = 0U; index < policy->class_count; ++index) {
		const struct be_raw_class *class = &policy->classes[index];

		*where = index;
		*what = class->class_id;
		if (find_class(policy, class->class_id) != class)
			return BE_POLICY_A1_DUPLICATE_CLASS;
		if (class->perm_count == 0U ||
		    list_repeats(class->perms, class->perm_count))
			return BE_POLICY_A1_CLASS_PERMISSIONS;
	}
	for (index = 0U; index < policy->type_count; ++index) {
		*where = index;
		*what = policy->types[index];
		if (list_has(policy->types, index, policy->types[index]))
			return BE_POLICY_A1_DUPLICATE_TYPE;
	}
	for (index = 0U; index < policy->rule_count; ++index) {
		const struct be_raw_rule *rule = &policy->rules[index];
		const struct be_raw_class *class =
			find_class(policy, rule->class_id);

		*where = index;
		*what = rule->source;
		if (!list_has(policy->types, policy->type_count, rule->source))
			return BE_POLICY_A1_UNDECLARED_TYPE;
		*what = rule->target;
		if (!list_has(policy->types, policy->type_count, rule->target))
			return BE_POLICY_A1_UNDECLARED_TYPE;
		*what = rule->class_id;
		if (class == (const struct be_raw_class *)0)
			return BE_POLICY_A1_UNDECLARED_CLASS;
		if (rule->perm_count == 0U)
			return BE_POLICY_A1_EMPTY_PERMISSIONS;
		for (perm = 0U; perm < rule->perm_count; ++perm) {
			*what = rule->perms[perm];
			if (!list_has(class->perms, class->perm_count,
				      rule->perms[perm]))
				return BE_POLICY_A1_UNKNOWN_PERMISSION;
			if (list_has(rule->perms, perm, rule->perms[perm]))
				return BE_POLICY_A1_REPEATED_PERMISSION;
		}
	}
	return BE_POLICY_OK;
}

static enum be_policy_code
check_labeling(const struct be_raw_policy *policy,
	       const struct be_raw_labeling *labeling,
	       struct be_policy_validated *candidate, be_size *where,
	       be_u32 *what)
{
	be_size index;

	for (index = 0U; index < labeling->subject_count; ++index) {
		*where = index;
		*what = labeling->subjects[index];
		if (list_has(labeling->subjects, index, *what))
			return BE_POLICY_A1_DUPLICATE_ENTITY;
	}
	for (index = 0U; index < labeling->object_count; ++index) {
		*where = index;
		*what = labeling->objects[index].object;
		if (candidate->object_present[*what] != 0U)
			return BE_POLICY_A1_DUPLICATE_ENTITY;
		candidate->object_present[*what] = 1U;
		candidate->object_class[*what] =
			labeling->objects[index].class_id;
	}
	for (index = 0U; index < labeling->label_count; ++index) {
		const struct be_raw_label *label = &labeling->labels[index];
		int subject = label->kind == BE_RAW_SUBJECT;
		be_u8 *labeled;

		*where = index;
		*what = label->entity;
		if (subject ? !subject_listed(labeling, label->entity) :
			      (label->kind != BE_RAW_OBJECT ||
			       !object_listed(labeling, label->entity)))
			return BE_POLICY_A1_UNKNOWN_ENTITY;
		if (!list_has(policy->types, policy->type_count, label->type))
			return BE_POLICY_A1_UNDECLARED_TYPE;
		labeled = subject ? &candidate->subject_present[label->entity] :
				    &candidate->object_present[label->entity];
		if (*labeled == 2U)
			return BE_POLICY_A1_DOUBLY_LABELED;
		*labeled = 2U;
		if (subject)
			candidate->subject_type[label->entity] = label->type;
		else
			candidate->object_type[label->entity] = label->type;
	}
	for (index = 0U; index < labeling->subject_count; ++index) {
		*where = index;
		*what = labeling->subjects[index];
		if (candidate->subject_present[*what] != 2U)
			return BE_POLICY_A1_UNLABELED;
	}
	for (index = 0U; index < labeling->object_count; ++index) {
		*where = index;
		*what = labeling->objects[index].object;
		if (candidate->object_present[*what] != 2U)
			return BE_POLICY_A1_UNLABELED;
	}
	return BE_POLICY_OK;
}

static enum be_policy_code
check_view_entities(const struct be_raw_labeling *labeling,
		    const struct be_raw_view *view, be_size *where,
		    be_u32 *what)
{
	be_size index;

	for (index = 0U; index < view->ownership_count; ++index) {
		*where = index;
		*what = view->ownerships[index].object;
		if (!object_listed(labeling, *what))
			return BE_POLICY_A1_UNLABELED;
		*what = view->ownerships[index].owner;
		if (!subject_listed(labeling, *what))
			return BE_POLICY_A1_UNLABELED;
	}
	for (index = 0U; index < view->channel_count; ++index) {
		const struct be_raw_channel *channel = &view->channels[index];

		*where = index;
		*what = channel->object;
		if (!object_listed(labeling, channel->object))
			return BE_POLICY_A1_UNLABELED;
		*what = channel->storage;
		if (!object_listed(labeling, channel->storage))
			return BE_POLICY_A1_UNLABELED;
		*what = channel->writer;
		if (!subject_listed(labeling, channel->writer))
			return BE_POLICY_A1_UNLABELED;
		*what = channel->reader;
		if (!subject_listed(labeling, channel->reader))
			return BE_POLICY_A1_UNLABELED;
	}
	for (index = 0U; index < view->grant_count; ++index) {
		const struct be_raw_grant *grant = &view->grants[index];

		*where = index;
		*what = grant->subject;
		if (!subject_listed(labeling, grant->subject))
			return BE_POLICY_A1_UNLABELED;
		*what = grant->object;
		if (grant->class_id == BE_POLICY_CLASS_DOMAIN ?
			    !subject_listed(labeling, grant->object) :
			    !object_listed(labeling, grant->object))
			return BE_POLICY_A1_UNLABELED;
	}
	for (index = 0U; index < view->binding_count; ++index) {
		*where = index;
		*what = view->bindings[index].domain;
		if (!subject_listed(labeling, *what))
			return BE_POLICY_A1_UNLABELED;
	}
	return BE_POLICY_OK;
}

enum be_policy_code
be_policy_validate(const struct be_raw_policy *policy,
		   const struct be_raw_labeling *labeling,
		   const struct be_raw_view *view,
		   struct be_policy_validated *validated,
		   struct be_policy_result *result)
{
	struct be_policy_validated candidate = { 0 };
	enum be_policy_code code;
	be_size where = 0U;
	be_u32 what = 0U;

	if (result != (struct be_policy_result *)0)
		result_reset(result);
	if (validated != (struct be_policy_validated *)0)
		*validated = (struct be_policy_validated){ 0 };
	if (policy == (const struct be_raw_policy *)0 ||
	    labeling == (const struct be_raw_labeling *)0 ||
	    view == (const struct be_raw_view *)0 ||
	    validated == (struct be_policy_validated *)0)
		return BE_POLICY_NULL;

	code = check_bounds(policy, labeling, view, &where);
	if (code == BE_POLICY_OK)
		code = check_policy(policy, &where, &what);
	if (code == BE_POLICY_OK)
		code = check_labeling(policy, labeling, &candidate, &where,
				      &what);
	if (code == BE_POLICY_OK)
		code = check_view_entities(labeling, view, &where, &what);
	if (code != BE_POLICY_OK) {
		if (result != (struct be_policy_result *)0)
			result_add(result, code, where, what, 0U);
		return code;
	}
	candidate.policy = *policy;
	candidate.labeling = *labeling;
	candidate.view = *view;
	*validated = candidate;
	return BE_POLICY_OK;
}

int be_policy_decide(const struct be_policy_validated *validated,
		     be_u32 source, be_u32 target, be_u32 class_id,
		     be_u32 permission)
{
	be_size index;

	if (validated == (const struct be_policy_validated *)0)
		return 0;
	for (index = 0U; index < validated->policy.rule_count; ++index) {
		const struct be_raw_rule *rule = &validated->policy.rules[index];

		if (rule->source == source && rule->target == target &&
		    rule->class_id == class_id &&
		    list_has(rule->perms, rule->perm_count, permission))
			return 1;
	}
	return 0;
}

static int rule_has(const struct be_raw_rule *rule, be_u32 class_id,
		    be_u32 permission)
{
	return rule->class_id == class_id &&
	       list_has(rule->perms, rule->perm_count, permission);
}

/* The types that label a domain: every labeled subject but the monitor. */
static be_u32 domain_types(const struct be_policy_validated *validated)
{
	be_u32 types = 0U;
	be_size index;

	for (index = 0U; index < validated->labeling.subject_count; ++index) {
		be_u32 subject = validated->labeling.subjects[index];

		if (subject != BE_POLICY_MONITOR_SUBJECT)
			types |= TYPE_BIT(validated->subject_type[subject]);
	}
	return types;
}

static int is_domain(const struct be_policy_validated *validated,
		     be_u32 subject)
{
	return subject != BE_POLICY_MONITOR_SUBJECT &&
	       subject_listed(&validated->labeling, subject);
}

int be_policy_a2(const struct be_policy_validated *validated,
		 struct be_policy_result *result)
{
	be_u32 domains = domain_types(validated);
	be_u32 sources = 0U;
	be_size index;
	be_size object;

	result_reset(result);
	for (index = 0U; index < validated->labeling.subject_count; ++index)
		sources |= TYPE_BIT(validated->subject_type
					    [validated->labeling.subjects[index]]);
	for (index = 0U; index < validated->policy.rule_count; ++index) {
		const struct be_raw_rule *rule = &validated->policy.rules[index];
		int reachable = rule->class_id == BE_POLICY_CLASS_DOMAIN &&
				(domains & TYPE_BIT(rule->target)) != 0U;

		for (object = 0U; object < validated->labeling.object_count;
		     ++object) {
			be_u32 id = validated->labeling.objects[object].object;

			if (validated->object_class[id] == rule->class_id &&
			    validated->object_type[id] == rule->target)
				reachable = 1;
		}
		if ((sources & TYPE_BIT(rule->source)) == 0U)
			result_add(result, BE_POLICY_A2_SOURCE_UNREACHABLE,
				   index, rule->source, 0U);
		else if (!reachable)
			result_add(result, BE_POLICY_A2_TARGET_UNREACHABLE,
				   index, rule->target, 0U);
	}
	return result->failures == 0U;
}

/*
 * Monitor memory is the labeled memory no ownership names and no channel
 * uses: the MVP's objects owned by "monitor", and Model 0.2's frames 1-8.
 */
static be_u32 monitor_types(const struct be_policy_validated *validated)
{
	const struct be_raw_view *view = &validated->view;
	be_u32 types = 0U;
	be_size index;
	be_size other;

	for (index = 0U; index < validated->labeling.object_count; ++index) {
		be_u32 object = validated->labeling.objects[index].object;
		int used = 0;

		for (other = 0U; other < view->ownership_count; ++other)
			used |= view->ownerships[other].object == object;
		for (other = 0U; other < view->channel_count; ++other)
			used |= view->channels[other].object == object ||
				view->channels[other].storage == object;
		if (!used)
			types |= TYPE_BIT(validated->object_type[object]);
	}
	return types;
}

static be_u32 holders(const struct be_policy_validated *validated,
		      be_u32 class_id, be_u32 target)
{
	be_u32 sources = 0U;
	be_size index;

	for (index = 0U; index < validated->policy.rule_count; ++index) {
		const struct be_raw_rule *rule = &validated->policy.rules[index];

		if (rule->class_id == class_id && rule->target == target)
			sources |= TYPE_BIT(rule->source);
	}
	return sources;
}

/* Whether some domain of type SOURCE maps another domain's object of TYPE. */
static int maps_foreign(const struct be_policy_validated *validated,
			be_u32 source, be_u32 type)
{
	const struct be_raw_view *view = &validated->view;
	be_size index;
	be_size subject;

	for (index = 0U; index < view->ownership_count; ++index) {
		be_u32 owner = view->ownerships[index].owner;

		if (!is_domain(validated, owner) ||
		    validated->object_type[view->ownerships[index].object] !=
			    type)
			continue;
		for (subject = 0U; subject < validated->labeling.subject_count;
		     ++subject) {
			be_u32 domain = validated->labeling.subjects[subject];

			if (is_domain(validated, domain) &&
			    validated->subject_type[domain] == source &&
			    domain != owner)
				return 1;
		}
	}
	return 0;
}

int be_policy_a3(const struct be_policy_validated *validated,
		 struct be_policy_result *result)
{
	be_u32 domains = domain_types(validated);
	be_u32 monitor = monitor_types(validated);
	be_size index;
	be_u32 target;
	be_u32 source;

	result_reset(result);
	for (index = 0U; index < validated->policy.rule_count; ++index) {
		const struct be_raw_rule *rule = &validated->policy.rules[index];
		int domain = (domains & TYPE_BIT(rule->source)) != 0U;

		if (domain && (monitor & TYPE_BIT(rule->target)) != 0U)
			result_add(result, BE_POLICY_A3_MONITOR_MEMORY, index,
				   rule->source, rule->target);
		if (domain &&
		    rule_has(rule, BE_POLICY_CLASS_MEMORY, BE_POLICY_PERM_MAP) &&
		    maps_foreign(validated, rule->source, rule->target))
			result_add(result, BE_POLICY_A3_FOREIGN_PRIVATE_MAP,
				   index, rule->source, rule->target);
		if (rule->class_id == BE_POLICY_CLASS_CHANNEL &&
		    (holders(validated, BE_POLICY_CLASS_MEMORY, rule->target) &
		     TYPE_BIT(rule->source)) == 0U)
			result_add(result, BE_POLICY_A3_CHANNEL_WITHOUT_STORAGE,
				   index, rule->source, rule->target);
		if (domain && rule->class_id == BE_POLICY_CLASS_DOMAIN &&
		    (rule->target == rule->source ||
		     (domains & TYPE_BIT(rule->target)) == 0U))
			result_add(result, BE_POLICY_A3_DOMAIN_TARGET, index,
				   rule->source, rule->target);
	}
	for (target = 0U; target < BE_POLICY_MAX_TYPES; ++target) {
		be_u32 memory = holders(validated, BE_POLICY_CLASS_MEMORY,
					target);
		be_u32 channel = holders(validated, BE_POLICY_CLASS_CHANNEL,
					 target);

		if ((memory & (memory - 1U)) == 0U)
			continue;
		for (source = 0U; source < BE_POLICY_MAX_TYPES; ++source) {
			if ((memory & TYPE_BIT(source)) != 0U &&
			    (channel & TYPE_BIT(source)) == 0U)
				result_add(result,
					   BE_POLICY_A3_STORAGE_WITHOUT_CHANNEL,
					   target, source, target);
		}
	}
	return result->failures == 0U;
}

static int need_is_declared(const struct be_policy_validated *validated,
			    const struct be_raw_need *need)
{
	const struct be_raw_policy *policy = &validated->policy;
	const struct be_raw_class *class = find_class(policy, need->class_id);
	be_size perm;

	if (!list_has(policy->types, policy->type_count, need->source) ||
	    !list_has(policy->types, policy->type_count, need->target) ||
	    class == (const struct be_raw_class *)0 || need->perm_count == 0U ||
	    need->perm_count > BE_POLICY_MAX_PERMS ||
	    list_repeats(need->perms, need->perm_count))
		return 0;
	for (perm = 0U; perm < need->perm_count; ++perm) {
		if (!list_has(class->perms, class->perm_count,
			      need->perms[perm]))
			return 0;
	}
	return 1;
}

static int same_key(const struct be_raw_need *need, be_u32 source,
		    be_u32 target, be_u32 class_id)
{
	return need->source == source && need->target == target &&
	       need->class_id == class_id;
}

int be_policy_a4(const struct be_policy_validated *validated,
		 const struct be_raw_need *needs, be_size need_count,
		 struct be_policy_result *result)
{
	be_u8 accepted[BE_POLICY_MAX_NEEDS] = { 0 };
	be_size index;
	be_size other;
	be_size perm;

	result_reset(result);
	if (need_count > BE_POLICY_MAX_NEEDS ||
	    (needs == (const struct be_raw_need *)0 && need_count != 0U)) {
		result_add(result, BE_POLICY_A4_MALFORMED_NEED, need_count, 0U,
			   0U);
		return 0;
	}
	for (index = 0U; index < need_count; ++index) {
		const struct be_raw_need *need = &needs[index];
		int repeated = 0;

		for (other = 0U; other < index; ++other)
			repeated |= accepted[other] != 0U &&
				    same_key(&needs[other], need->source,
					     need->target, need->class_id);
		if (repeated || !need_is_declared(validated, need))
			result_add(result, BE_POLICY_A4_MALFORMED_NEED, index,
				   need->source, need->target);
		else
			accepted[index] = 1U;
	}
	for (index = 0U; index < validated->policy.rule_count; ++index) {
		const struct be_raw_rule *rule = &validated->policy.rules[index];
		const struct be_raw_need *need = (const struct be_raw_need *)0;

		for (other = 0U; other < need_count; ++other) {
			if (accepted[other] != 0U &&
			    same_key(&needs[other], rule->source, rule->target,
				     rule->class_id))
				need = &needs[other];
		}
		if (need == (const struct be_raw_need *)0) {
			result_add(result, BE_POLICY_A4_NO_NEED, index,
				   rule->source, rule->target);
			continue;
		}
		for (perm = 0U; perm < rule->perm_count; ++perm) {
			if (!list_has(need->perms, need->perm_count,
				      rule->perms[perm])) {
				result_add(result, BE_POLICY_A4_EXCESS, index,
					   rule->perms[perm], 0U);
				break;
			}
		}
	}
	return result->failures == 0U;
}

static be_u32 holders_with(const struct be_policy_validated *validated,
			   be_u32 class_id, be_u32 target, be_u32 permission)
{
	be_u32 sources = 0U;
	be_size index;

	for (index = 0U; index < validated->policy.rule_count; ++index) {
		const struct be_raw_rule *rule = &validated->policy.rules[index];

		if (rule->target == target &&
		    rule_has(rule, class_id, permission))
			sources |= TYPE_BIT(rule->source);
	}
	return sources;
}

static be_u32 lowest_type(be_u32 types)
{
	be_u32 type = 0U;

	while (type < BE_POLICY_MAX_TYPES && (types & TYPE_BIT(type)) == 0U)
		++type;
	return type;
}

int be_policy_a5(const struct be_policy_validated *validated,
		 struct be_policy_result *result)
{
	be_u32 target;

	result_reset(result);
	for (target = 0U; target < BE_POLICY_MAX_TYPES; ++target) {
		be_u32 writers = holders_with(validated, BE_POLICY_CLASS_MEMORY,
					      target, BE_POLICY_PERM_WRITE);
		be_u32 readers = holders_with(validated, BE_POLICY_CLASS_MEMORY,
					      target, BE_POLICY_PERM_READ);

		/* Shared: some reader is not some writer (writers nonempty). */
		if (writers == 0U || readers == 0U ||
		    ((writers & (writers - 1U)) == 0U && readers == writers))
			continue;
		if ((writers & (writers - 1U)) != 0U)
			result_add(result, BE_POLICY_A5_MULTIPLE_WRITERS, target,
				   target, writers);
		else
			result_add(result, BE_POLICY_A5_STATIC_SINGLE_WRITER,
				   target, target, lowest_type(writers));
	}
	return result->failures == 0U;
}

static void relation(const struct be_policy_validated *validated,
		     be_u32 class_id, be_u32 first, be_u32 second,
		     struct be_policy_relation *out)
{
	be_size one;
	be_size two;

	*out = (struct be_policy_relation){ 0 };
	for (one = 0U; one < validated->policy.rule_count; ++one) {
		const struct be_raw_rule *left = &validated->policy.rules[one];

		if (!rule_has(left, class_id, first))
			continue;
		for (two = 0U; two < validated->policy.rule_count; ++two) {
			const struct be_raw_rule *right =
				&validated->policy.rules[two];

			if (rule_has(right, class_id, second) &&
			    left->target == right->target &&
			    left->source != right->source)
				out->row[left->source] |=
					TYPE_BIT(right->source);
		}
	}
}

void be_policy_relations(const struct be_policy_validated *validated,
			 struct be_policy_relation *flows,
			 struct be_policy_relation *channels)
{
	relation(validated, BE_POLICY_CLASS_MEMORY, BE_POLICY_PERM_WRITE,
		 BE_POLICY_PERM_READ, flows);
	relation(validated, BE_POLICY_CLASS_CHANNEL, BE_POLICY_PERM_SEND,
		 BE_POLICY_PERM_RECEIVE, channels);
}

void be_policy_closure(struct be_policy_relation *relation)
{
	be_size middle;
	be_size source;

	for (middle = 0U; middle < BE_POLICY_MAX_TYPES; ++middle) {
		for (source = 0U; source < BE_POLICY_MAX_TYPES; ++source) {
			if ((relation->row[source] &
			     TYPE_BIT(middle)) != 0U)
				relation->row[source] |= relation->row[middle];
		}
	}
}

int be_policy_a6(const struct be_policy_validated *validated,
		 struct be_policy_result *result)
{
	struct be_policy_relation flows;
	struct be_policy_relation channels;
	be_u32 source;
	be_u32 target;

	result_reset(result);
	be_policy_relations(validated, &flows, &channels);
	be_policy_closure(&flows);
	be_policy_closure(&channels);
	for (source = 0U; source < BE_POLICY_MAX_TYPES; ++source) {
		for (target = 0U; target < BE_POLICY_MAX_TYPES; ++target) {
			be_u32 bit = TYPE_BIT(target);

			if ((flows.row[source] & ~channels.row[source] & bit) !=
			    0U)
				result_add(result, BE_POLICY_A6_UNDECLARED_FLOW,
					   source, source, target);
			if ((channels.row[source] & ~flows.row[source] & bit) !=
			    0U)
				result_add(result,
					   BE_POLICY_A6_UNREALIZED_CHANNEL,
					   source, source, target);
		}
	}
	return result->failures == 0U;
}

int be_policy_a7(const struct be_policy_validated *validated,
		 struct be_policy_result *result)
{
	be_u32 domains = domain_types(validated);
	be_size index;
	be_size perm;

	result_reset(result);
	for (index = 0U; index < validated->policy.rule_count; ++index) {
		const struct be_raw_rule *rule = &validated->policy.rules[index];

		if (rule->class_id != BE_POLICY_CLASS_DOMAIN ||
		    (domains & TYPE_BIT(rule->source)) == 0U)
			continue;
		for (perm = 0U; perm < rule->perm_count; ++perm) {
			if (rule->perms[perm] != BE_POLICY_PERM_PAUSE &&
			    rule->perms[perm] != BE_POLICY_PERM_TERMINATE)
				result_add(result, BE_POLICY_A7_DELEGATION,
					   index, rule->perms[perm], 0U);
		}
	}
	return result->failures == 0U;
}

int be_policy_a8(const struct be_policy_validated *validated,
		 struct be_policy_result *result)
{
	const struct be_raw_view *view = &validated->view;
	be_size index;
	be_size perm;

	result_reset(result);
	for (index = 0U; index < view->grant_count; ++index) {
		const struct be_raw_grant *grant = &view->grants[index];
		be_u32 source = validated->subject_type[grant->subject];
		be_u32 target = grant->class_id == BE_POLICY_CLASS_DOMAIN ?
					validated->subject_type[grant->object] :
					validated->object_type[grant->object];

		for (perm = 0U; perm < grant->perm_count; ++perm) {
			if (!be_policy_decide(validated, source, target,
					      grant->class_id,
					      grant->perms[perm]))
				result_add(result, BE_POLICY_A8_UNALLOWED, index,
					   grant->perms[perm], 0U);
		}
	}
	return result->failures == 0U;
}

/* A1 to A8 on a validated value; bit n-1 of the return is An's failure. */
static be_u32 analyze(const struct be_policy_validated *validated,
		      const struct be_raw_need *needs, be_size need_count,
		      enum be_policy_code *first)
{
	struct be_policy_result result;
	be_u32 failed = 0U;
	int pass[BE_POLICY_ANALYSES];
	be_size index;

	pass[0] = 1;
	pass[1] = be_policy_a2(validated, &result);
	if (!pass[1] && *first == BE_POLICY_OK)
		*first = result.first_failure;
	pass[2] = be_policy_a3(validated, &result);
	if (!pass[2] && *first == BE_POLICY_OK)
		*first = result.first_failure;
	pass[3] = be_policy_a4(validated, needs, need_count, &result);
	if (!pass[3] && *first == BE_POLICY_OK)
		*first = result.first_failure;
	pass[4] = be_policy_a5(validated, &result);
	if (!pass[4] && *first == BE_POLICY_OK)
		*first = result.first_failure;
	pass[5] = be_policy_a6(validated, &result);
	if (!pass[5] && *first == BE_POLICY_OK)
		*first = result.first_failure;
	pass[6] = be_policy_a7(validated, &result);
	pass[7] = be_policy_a8(validated, &result);
	if (!pass[7] && *first == BE_POLICY_OK)
		*first = result.first_failure;
	for (index = 0U; index < BE_POLICY_ANALYSES; ++index) {
		if (!pass[index])
			failed |= (be_u32)1U << index;
	}
	return failed;
}

void be_policy_verdicts(const struct be_raw_instance *instance,
			struct be_policy_verdicts *verdicts)
{
	struct be_policy_validated validated;
	enum be_policy_code first = BE_POLICY_OK;

	if (verdicts == (struct be_policy_verdicts *)0)
		return;
	verdicts->evaluated = 1U;
	verdicts->failed = 1U;
	if (instance == (const struct be_raw_instance *)0 ||
	    be_policy_validate(&instance->policy, &instance->labeling,
			       &instance->view, &validated,
			       (struct be_policy_result *)0) != BE_POLICY_OK)
		return;
	verdicts->evaluated = (1U << BE_POLICY_ANALYSES) - 1U;
	verdicts->failed = analyze(&validated, instance->needs,
				   instance->need_count, &first);
}

be_size be_policy_view_flows(const struct be_raw_view *view,
			     be_size *undeclared)
{
	static const struct be_raw_view empty;
	be_size flows = 0U;
	be_size hidden = 0U;
	be_size writer;
	be_size reader;
	be_size channel;

	if (view == (const struct be_raw_view *)0 ||
	    be_view_identity(view) == 0U)
		view = &empty;
	for (writer = 0U; writer < view->grant_count; ++writer) {
		const struct be_raw_grant *write = &view->grants[writer];

		if (write->class_id != BE_POLICY_CLASS_MEMORY ||
		    !list_has(write->perms, write->perm_count,
			      BE_POLICY_PERM_WRITE))
			continue;
		for (reader = 0U; reader < view->grant_count; ++reader) {
			const struct be_raw_grant *read = &view->grants[reader];
			int declared = 0;

			if (read->class_id != BE_POLICY_CLASS_MEMORY ||
			    read->object != write->object ||
			    read->subject == write->subject ||
			    !list_has(read->perms, read->perm_count,
				      BE_POLICY_PERM_READ))
				continue;
			for (channel = 0U; channel < view->channel_count;
			     ++channel) {
				const struct be_raw_channel *declaring =
					&view->channels[channel];

				declared |= declaring->storage == write->object &&
					    declaring->writer == write->subject &&
					    declaring->reader == read->subject;
			}
			++flows;
			hidden += declared ? 0U : 1U;
		}
	}
	if (undeclared != (be_size *)0)
		*undeclared = hidden;
	return flows;
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

static be_u64 identity_list(be_u64 identity, const be_u32 *list,
			    be_size count)
{
	be_size index;

	identity = identity_u64(identity, count);
	for (index = 0U; index < count; ++index)
		identity = identity_u64(identity, list[index]);
	return identity;
}

be_u64 be_policy_identity(const struct be_raw_policy *policy)
{
	be_u64 identity = BE_U64_C(14695981039346656037);
	be_size index;

	if (policy == (const struct be_raw_policy *)0 ||
	    policy->type_count > BE_POLICY_MAX_TYPES ||
	    policy->class_count > BE_POLICY_MAX_CLASSES ||
	    policy->rule_count > BE_POLICY_MAX_RULES)
		return 0U;
	identity = identity_u64(identity, IDENTITY_POLICY);
	identity = identity_list(identity, policy->types, policy->type_count);
	identity = identity_u64(identity, policy->class_count);
	for (index = 0U; index < policy->class_count; ++index) {
		const struct be_raw_class *class = &policy->classes[index];

		if (class->perm_count > BE_POLICY_MAX_PERMS)
			return 0U;
		identity = identity_u64(identity, class->class_id);
		identity = identity_list(identity, class->perms,
					 class->perm_count);
	}
	identity = identity_u64(identity, policy->rule_count);
	for (index = 0U; index < policy->rule_count; ++index) {
		const struct be_raw_rule *rule = &policy->rules[index];

		if (rule->perm_count > BE_POLICY_MAX_PERMS)
			return 0U;
		identity = identity_u64(identity, rule->source);
		identity = identity_u64(identity, rule->target);
		identity = identity_u64(identity, rule->class_id);
		identity = identity_list(identity, rule->perms,
					 rule->perm_count);
	}
	return identity;
}

be_u64 be_labeling_identity(const struct be_raw_labeling *labeling)
{
	be_u64 identity = BE_U64_C(14695981039346656037);
	be_size index;

	if (labeling == (const struct be_raw_labeling *)0 ||
	    labeling->subject_count > BE_POLICY_MAX_SUBJECTS ||
	    labeling->object_count > BE_POLICY_MAX_OBJECTS ||
	    labeling->label_count > BE_POLICY_MAX_LABELS)
		return 0U;
	identity = identity_u64(identity, IDENTITY_LABELING);
	identity = identity_list(identity, labeling->subjects,
				 labeling->subject_count);
	identity = identity_u64(identity, labeling->object_count);
	for (index = 0U; index < labeling->object_count; ++index) {
		identity = identity_u64(identity,
					labeling->objects[index].object);
		identity = identity_u64(identity,
					labeling->objects[index].class_id);
	}
	identity = identity_u64(identity, labeling->label_count);
	for (index = 0U; index < labeling->label_count; ++index) {
		const struct be_raw_label *label = &labeling->labels[index];

		identity = identity_u64(identity, (be_u64)label->kind);
		identity = identity_u64(identity, label->entity);
		identity = identity_u64(identity, label->type);
	}
	return identity;
}

be_u64 be_view_identity(const struct be_raw_view *view)
{
	be_u64 identity = BE_U64_C(14695981039346656037);
	be_size index;

	if (view == (const struct be_raw_view *)0 ||
	    view->ownership_count > BE_POLICY_MAX_OWNERSHIPS ||
	    view->channel_count > BE_POLICY_MAX_CHANNELS ||
	    view->grant_count > BE_POLICY_MAX_GRANTS ||
	    view->binding_count > BE_POLICY_MAX_BINDINGS ||
	    view->hart_count > BE_POLICY_MAX_HARTS)
		return 0U;
	identity = identity_u64(identity, IDENTITY_VIEW);
	identity = identity_u64(identity, view->ownership_count);
	for (index = 0U; index < view->ownership_count; ++index) {
		identity = identity_u64(identity,
					view->ownerships[index].object);
		identity = identity_u64(identity, view->ownerships[index].owner);
	}
	identity = identity_u64(identity, view->channel_count);
	for (index = 0U; index < view->channel_count; ++index) {
		const struct be_raw_channel *channel = &view->channels[index];

		identity = identity_u64(identity, channel->object);
		identity = identity_u64(identity, channel->storage);
		identity = identity_u64(identity, channel->writer);
		identity = identity_u64(identity, channel->reader);
	}
	identity = identity_u64(identity, view->grant_count);
	for (index = 0U; index < view->grant_count; ++index) {
		const struct be_raw_grant *grant = &view->grants[index];

		if (grant->perm_count > BE_POLICY_MAX_PERMS)
			return 0U;
		identity = identity_u64(identity, grant->subject);
		identity = identity_u64(identity, grant->object);
		identity = identity_u64(identity, grant->class_id);
		identity = identity_list(identity, grant->perms,
					 grant->perm_count);
	}
	identity = identity_u64(identity, view->binding_count);
	for (index = 0U; index < view->binding_count; ++index) {
		identity = identity_u64(identity, view->bindings[index].domain);
		identity = identity_u64(identity, view->bindings[index].hart);
	}
	identity = identity_list(identity, view->harts, view->hart_count);
	return identity_u64(identity, view->control_hart);
}

be_u64 be_combined_identity(be_u64 manifest, be_u64 policy, be_u64 labeling)
{
	be_u64 identity = BE_U64_C(14695981039346656037);

	identity = identity_u64(identity, IDENTITY_COMBINED);
	identity = identity_u64(identity, manifest);
	identity = identity_u64(identity, policy);
	return identity_u64(identity, labeling);
}

static be_size frame_object(const struct be_canonical_state *canonical,
			    be_u32 frame_id)
{
	be_size index;

	for (index = 0U; index < canonical->frame_count; ++index) {
		if (canonical->frames[index].id == frame_id)
			break;
	}
	return index;
}

static be_u32 owner_mask(enum be_domain_id domain)
{
	if (domain == BE_DOMAIN_MANAGEMENT)
		return BE_OWNER_MANAGEMENT;
	if (domain == BE_DOMAIN_PROTECTED)
		return BE_OWNER_PROTECTED;
	return 0U;
}

static void add_grant(struct be_raw_view *view, be_u32 subject,
		      be_u32 object, be_u32 class_id, be_u32 rights)
{
	struct be_raw_grant *grant = &view->grants[view->grant_count++];

	grant->subject = subject;
	grant->object = object;
	grant->class_id = class_id;
	if (class_id != BE_POLICY_CLASS_MEMORY) {
		grant->perms[grant->perm_count++] = rights;
		return;
	}
	grant->perms[grant->perm_count++] = BE_POLICY_PERM_MAP;
	if ((rights & BE_RIGHT_READ) != 0U)
		grant->perms[grant->perm_count++] = BE_POLICY_PERM_READ;
	if ((rights & BE_RIGHT_WRITE) != 0U)
		grant->perms[grant->perm_count++] = BE_POLICY_PERM_WRITE;
	if ((rights & BE_RIGHT_EXECUTE) != 0U)
		grant->perms[grant->perm_count++] = BE_POLICY_PERM_EXECUTE;
}

enum be_policy_code
be_view_of_canonical(const struct be_canonical_state *canonical,
		     struct be_raw_view *view)
{
	struct be_raw_view candidate = { 0 };
	be_size domain;
	be_size index;

	if (view == (struct be_raw_view *)0)
		return BE_POLICY_NULL;
	*view = (struct be_raw_view){ 0 };
	if (canonical == (const struct be_canonical_state *)0)
		return BE_POLICY_NULL;
	if (be_check_canonical(canonical) != BE_CHECK_OK)
		return BE_POLICY_SEAL_CANONICAL;

	/*
	 * Subject 0 is the monitor and subject n the canonical domain at
	 * index n - 1; object n is the frame at index n, and the channels
	 * follow the frames. Only private frames have a domain owner.
	 */
	for (index = 0U; index < canonical->frame_count; ++index) {
		const struct be_frame_desc *frame = &canonical->frames[index];

		for (domain = 0U; domain < canonical->domain_count; ++domain) {
			struct be_raw_ownership *owned;

			if (frame->class != BE_FRAME_PRIVATE ||
			    frame->owner_mask !=
				    owner_mask(canonical->domains[domain].id))
				continue;
			owned = &candidate.ownerships
					 [candidate.ownership_count++];
			owned->object = (be_u32)index;
			owned->owner = (be_u32)domain + 1U;
		}
	}
	for (index = 0U; index < canonical->channel_count; ++index) {
		const struct be_channel_desc *channel =
			&canonical->channels[index];
		struct be_raw_channel *out = &candidate.channels[index];

		out->object = (be_u32)(canonical->frame_count + index);
		out->storage =
			(be_u32)frame_object(canonical, channel->frame_id);
		for (domain = 0U; domain < canonical->domain_count; ++domain) {
			if (canonical->domains[domain].id == channel->source)
				out->writer = (be_u32)domain + 1U;
			if (canonical->domains[domain].id == channel->target)
				out->reader = (be_u32)domain + 1U;
		}
	}
	candidate.channel_count = canonical->channel_count;
	for (domain = 0U; domain < canonical->domain_count; ++domain) {
		enum be_domain_id id = canonical->domains[domain].id;
		be_u32 subject = (be_u32)domain + 1U;

		for (index = 0U; index < canonical->authority_count; ++index) {
			const struct be_authority_desc *authority =
				&canonical->authorities[index];

			if (authority->domain == id)
				add_grant(&candidate, subject,
					  (be_u32)frame_object(
						  canonical,
						  authority->frame_id),
					  BE_POLICY_CLASS_MEMORY,
					  authority->rights);
		}
		for (index = 0U; index < canonical->channel_count; ++index) {
			if (canonical->channels[index].source == id)
				add_grant(&candidate, subject,
					  candidate.channels[index].object,
					  BE_POLICY_CLASS_CHANNEL,
					  BE_POLICY_PERM_SEND);
			if (canonical->channels[index].target == id)
				add_grant(&candidate, subject,
					  candidate.channels[index].object,
					  BE_POLICY_CLASS_CHANNEL,
					  BE_POLICY_PERM_RECEIVE);
		}
	}
	candidate.hart_count = 1U;
	candidate.harts[0] = canonical->hart_id;
	candidate.control_hart = canonical->hart_id;
	*view = candidate;
	return BE_POLICY_OK;
}

static int perms_equal(be_size left_count, const be_u32 *left,
		       be_size right_count, const be_u32 *right)
{
	be_size index;

	if (left_count != right_count || left_count > BE_POLICY_MAX_PERMS)
		return 0;
	for (index = 0U; index < left_count; ++index) {
		if (left[index] != right[index])
			return 0;
	}
	return 1;
}

int be_raw_view_equal(const struct be_raw_view *left,
		      const struct be_raw_view *right)
{
	be_size index;

	if (left == (const struct be_raw_view *)0 ||
	    right == (const struct be_raw_view *)0 ||
	    be_view_identity(left) == 0U || be_view_identity(right) == 0U ||
	    left->ownership_count != right->ownership_count ||
	    left->channel_count != right->channel_count ||
	    left->grant_count != right->grant_count ||
	    left->binding_count != right->binding_count ||
	    !perms_equal(left->hart_count, left->harts, right->hart_count,
			 right->harts) ||
	    left->control_hart != right->control_hart)
		return 0;
	for (index = 0U; index < left->ownership_count; ++index) {
		if (left->ownerships[index].object !=
			    right->ownerships[index].object ||
		    left->ownerships[index].owner !=
			    right->ownerships[index].owner)
			return 0;
	}
	for (index = 0U; index < left->channel_count; ++index) {
		const struct be_raw_channel *a = &left->channels[index];
		const struct be_raw_channel *b = &right->channels[index];

		if (a->object != b->object || a->storage != b->storage ||
		    a->writer != b->writer || a->reader != b->reader)
			return 0;
	}
	for (index = 0U; index < left->grant_count; ++index) {
		const struct be_raw_grant *a = &left->grants[index];
		const struct be_raw_grant *b = &right->grants[index];

		if (a->subject != b->subject || a->object != b->object ||
		    a->class_id != b->class_id ||
		    !perms_equal(a->perm_count, a->perms, b->perm_count,
				 b->perms))
			return 0;
	}
	for (index = 0U; index < left->binding_count; ++index) {
		if (left->bindings[index].domain !=
			    right->bindings[index].domain ||
		    left->bindings[index].hart != right->bindings[index].hart)
			return 0;
	}
	return 1;
}

enum be_policy_code
be_seal_view_with_policy(const struct be_raw_view *view,
			 be_u64 manifest_identity,
			 const struct be_raw_policy *policy,
			 const struct be_raw_labeling *labeling,
			 const struct be_raw_need *needs, be_size need_count,
			 struct be_sealed_with_policy *sealed)
{
	struct be_policy_validated validated;
	enum be_policy_code code;
	enum be_policy_code first = BE_POLICY_OK;

	if (sealed == (struct be_sealed_with_policy *)0)
		return BE_POLICY_NULL;
	*sealed = (struct be_sealed_with_policy){ 0 };
	if (needs == (const struct be_raw_need *)0 && need_count != 0U)
		return BE_POLICY_NULL;
	code = be_policy_validate(policy, labeling, view, &validated,
				  (struct be_policy_result *)0);
	if (code != BE_POLICY_OK)
		return code;
	if ((analyze(&validated, needs, need_count, &first) &
	     ~((be_u32)1U << 6U)) != 0U)
		return first;
	sealed->canonical_identity = manifest_identity;
	sealed->policy_identity = be_policy_identity(policy);
	sealed->labeling_identity = be_labeling_identity(labeling);
	sealed->configuration_identity = be_combined_identity(
		manifest_identity, sealed->policy_identity,
		sealed->labeling_identity);
	return BE_POLICY_OK;
}

/* The labeling's entities are exactly the adapter's subjects and objects. */
static int labeling_is_canonical(const struct be_canonical_state *canonical,
				 const struct be_raw_labeling *labeling)
{
	be_size expected = canonical->frame_count + canonical->channel_count;
	be_size index;
	be_size object;

	if (labeling->subject_count != canonical->domain_count + 1U ||
	    labeling->object_count != expected ||
	    labeling->object_count > BE_POLICY_MAX_OBJECTS)
		return 0;
	for (index = 0U; index < labeling->subject_count; ++index) {
		if (!subject_listed(labeling, (be_u32)index))
			return 0;
	}
	for (index = 0U; index < expected; ++index) {
		be_u32 class_id = index < canonical->frame_count ?
					  BE_POLICY_CLASS_MEMORY :
					  BE_POLICY_CLASS_CHANNEL;
		int found = 0;

		for (object = 0U; object < labeling->object_count; ++object)
			found |= labeling->objects[object].object == index &&
				 labeling->objects[object].class_id == class_id;
		if (!found)
			return 0;
	}
	return 1;
}

enum be_policy_code
be_seal_with_policy(const struct be_canonical_state *canonical,
		    const struct be_raw_policy *policy,
		    const struct be_raw_labeling *labeling,
		    const struct be_raw_need *needs, be_size need_count,
		    struct be_sealed_with_policy *sealed)
{
	struct be_raw_view view;
	enum be_policy_code code;

	if (sealed == (struct be_sealed_with_policy *)0)
		return BE_POLICY_NULL;
	*sealed = (struct be_sealed_with_policy){ 0 };
	if (policy == (const struct be_raw_policy *)0 ||
	    labeling == (const struct be_raw_labeling *)0)
		return BE_POLICY_NULL;
	code = be_view_of_canonical(canonical, &view);
	if (code != BE_POLICY_OK)
		return code;
	if (!labeling_is_canonical(canonical, labeling))
		return BE_POLICY_SEAL_CONFIGURATION;
	return be_seal_view_with_policy(&view, canonical->configuration_id,
					policy, labeling, needs, need_count,
					sealed);
}

enum be_binding_result
be_policy_check_bindings(const struct be_raw_labeling *labeling,
			 const struct be_raw_view *view)
{
	be_size index;
	be_size other;

	if (labeling == (const struct be_raw_labeling *)0 ||
	    view == (const struct be_raw_view *)0 ||
	    labeling->subject_count > BE_POLICY_MAX_SUBJECTS ||
	    view->binding_count > BE_POLICY_MAX_BINDINGS ||
	    view->hart_count > BE_POLICY_MAX_HARTS)
		return BE_BINDING_UNKNOWN;
	if (view->binding_count == 0U)
		return BE_BINDING_NOT_APPLICABLE;
	if (!list_has(view->harts, view->hart_count, view->control_hart))
		return BE_BINDING_UNKNOWN;
	for (index = 0U; index < view->binding_count; ++index) {
		const struct be_raw_binding *binding = &view->bindings[index];

		if (binding->domain == BE_POLICY_MONITOR_SUBJECT ||
		    !subject_listed(labeling, binding->domain) ||
		    !list_has(view->harts, view->hart_count, binding->hart))
			return BE_BINDING_UNKNOWN;
	}
	for (index = 0U; index < view->binding_count; ++index) {
		if (view->bindings[index].hart == view->control_hart)
			return BE_BINDING_CONTROL_HART;
	}
	for (index = 0U; index < view->binding_count; ++index) {
		for (other = index + 1U; other < view->binding_count; ++other) {
			if (view->bindings[index].hart ==
				    view->bindings[other].hart &&
			    view->bindings[index].domain !=
				    view->bindings[other].domain)
				return BE_BINDING_NOT_INJECTIVE;
		}
	}
	for (index = 0U; index < labeling->subject_count; ++index) {
		be_u32 domain = labeling->subjects[index];
		be_size bound = 0U;

		if (domain == BE_POLICY_MONITOR_SUBJECT)
			continue;
		for (other = 0U; other < view->binding_count; ++other)
			bound += view->bindings[other].domain == domain;
		if (bound != 1U)
			return BE_BINDING_NOT_TOTAL;
	}
	return BE_BINDING_OK;
}

const char *be_policy_code_name(enum be_policy_code code)
{
	static const char *const names[BE_POLICY_CODE_COUNT] = {
		"ok",
		"null",
		"a1-bound",
		"a1-duplicate-type",
		"a1-duplicate-class",
		"a1-class-permissions",
		"a1-undeclared-type",
		"a1-undeclared-class",
		"a1-empty-permissions",
		"a1-unknown-permission",
		"a1-repeated-permission",
		"a1-duplicate-entity",
		"a1-unknown-entity",
		"a1-unlabeled",
		"a1-doubly-labeled",
		"a2-source-unreachable",
		"a2-target-unreachable",
		"a3-monitor-memory",
		"a3-foreign-private-map",
		"a3-channel-without-storage",
		"a3-domain-target",
		"a3-storage-without-channel",
		"a4-malformed-need",
		"a4-no-need",
		"a4-excess",
		"a5-multiple-writers",
		"a5-static-single-writer",
		"a6-undeclared-flow",
		"a6-unrealized-channel",
		"a7-delegation",
		"a8-unallowed",
		"seal-canonical",
		"seal-configuration",
	};

	return code < BE_POLICY_CODE_COUNT ? names[code] : "invalid";
}

const char *be_binding_result_name(enum be_binding_result result)
{
	switch (result) {
	case BE_BINDING_OK:
		return "ok";
	case BE_BINDING_NOT_APPLICABLE:
		return "not-applicable";
	case BE_BINDING_UNKNOWN:
		return "unknown";
	case BE_BINDING_CONTROL_HART:
		return "control-hart";
	case BE_BINDING_NOT_INJECTIVE:
		return "not-injective";
	case BE_BINDING_NOT_TOTAL:
		return "not-total";
	default:
		return "invalid";
	}
}
