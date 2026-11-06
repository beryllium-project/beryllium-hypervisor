/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

#ifndef BE_POLICY_H
#define BE_POLICY_H

#include <be/manifest.h>

/*
 * Security model v1's policy layer as bounded host-model data (MVP M3-4).
 *
 * The raw structures mirror the raw-term vocabulary that model/proof/Policy.v
 * defines: every name is a natural number that the build-time generator,
 * tools/gen-policy-fixtures.mjs, assigns. Type identifiers follow the policy's
 * declaration order; class and permission identifiers are the v1 vocabulary
 * below, which is the declaration order of security model v1 Part 2's
 * classes; subjects are the monitor and then the domains; objects follow the
 * labeling. Nothing here parses a file, and no structure is a runtime input.
 */

#define BE_POLICY_MAX_TYPES		16U
#define BE_POLICY_MAX_CLASSES		8U
#define BE_POLICY_MAX_PERMS		16U
#define BE_POLICY_MAX_RULES		24U
#define BE_POLICY_MAX_SUBJECTS		8U
#define BE_POLICY_MAX_OBJECTS		24U
#define BE_POLICY_MAX_LABELS		40U
#define BE_POLICY_MAX_NEEDS		24U
#define BE_POLICY_MAX_GRANTS		24U
#define BE_POLICY_MAX_CHANNELS		4U
#define BE_POLICY_MAX_OWNERSHIPS	16U
#define BE_POLICY_MAX_BINDINGS		8U
#define BE_POLICY_MAX_HARTS		8U
#define BE_POLICY_MAX_FINDINGS		16U
#define BE_POLICY_ANALYSES		8U

/* Security model v1 Part 2's classes and permissions, in declaration order. */
#define BE_POLICY_CLASS_MEMORY		0U
#define BE_POLICY_CLASS_CHANNEL		1U
#define BE_POLICY_CLASS_DOMAIN		2U
#define BE_POLICY_CLASS_MANIFEST	3U
#define BE_POLICY_PERM_READ		0U
#define BE_POLICY_PERM_WRITE		1U
#define BE_POLICY_PERM_EXECUTE		2U
#define BE_POLICY_PERM_MAP		3U
#define BE_POLICY_PERM_SEND		4U
#define BE_POLICY_PERM_RECEIVE		5U
#define BE_POLICY_PERM_ENTER		6U
#define BE_POLICY_PERM_SWITCH_TO	7U
#define BE_POLICY_PERM_TERMINATE	8U
#define BE_POLICY_PERM_PAUSE		9U

/* The monitor is subject zero; every other labeled subject is a domain. */
#define BE_POLICY_MONITOR_SUBJECT	0U

/**
 * struct be_raw_class - one declared class and its permissions
 * @class_id: class identifier
 * @perm_count: number of permissions
 * @perms: permission identifiers
 */
struct be_raw_class {
	be_u32 class_id;
	be_size perm_count;
	be_u32 perms[BE_POLICY_MAX_PERMS];
};

/**
 * struct be_raw_rule - one allow(source, target, class, permissions) rule
 * @source: source type
 * @target: target type
 * @class_id: object class
 * @perm_count: number of permissions
 * @perms: permission identifiers as the rule lists them
 */
struct be_raw_rule {
	be_u32 source;
	be_u32 target;
	be_u32 class_id;
	be_size perm_count;
	be_u32 perms[BE_POLICY_MAX_PERMS];
};

/**
 * struct be_raw_policy - a policy (T, C, P, R) over identifiers
 * @type_count: number of declared types
 * @types: declared type identifiers
 * @class_count: number of declared classes
 * @classes: declared classes with their permissions
 * @rule_count: number of rules
 * @rules: allow rules, which may name undeclared identifiers until A1
 */
struct be_raw_policy {
	be_size type_count;
	be_u32 types[BE_POLICY_MAX_TYPES];
	be_size class_count;
	struct be_raw_class classes[BE_POLICY_MAX_CLASSES];
	be_size rule_count;
	struct be_raw_rule rules[BE_POLICY_MAX_RULES];
};

/**
 * enum be_raw_entity - the two kinds of labeled entity
 * @BE_RAW_SUBJECT: a subject (the monitor or a domain)
 * @BE_RAW_OBJECT: an object (memory, channel, or other governed object)
 */
enum be_raw_entity {
	BE_RAW_SUBJECT = 0,
	BE_RAW_OBJECT,
};

/**
 * struct be_raw_label - one labeling assignment
 * @kind: subject or object
 * @entity: subject or object identifier
 * @type: assigned type
 */
struct be_raw_label {
	enum be_raw_entity kind;
	be_u32 entity;
	be_u32 type;
};

/**
 * struct be_raw_object - one object of the configuration
 * @object: object identifier
 * @class_id: the object's class
 */
struct be_raw_object {
	be_u32 object;
	be_u32 class_id;
};

/**
 * struct be_raw_labeling - the configuration's entities and their labels
 * @subject_count: number of subjects of the configuration
 * @subjects: subject identifiers, the monitor first
 * @object_count: number of objects of the configuration
 * @objects: object identifiers with their classes
 * @label_count: number of labeling assignments
 * @labels: assignments, which may be missing, repeated, or dangling until A1
 */
struct be_raw_labeling {
	be_size subject_count;
	be_u32 subjects[BE_POLICY_MAX_SUBJECTS];
	be_size object_count;
	struct be_raw_object objects[BE_POLICY_MAX_OBJECTS];
	be_size label_count;
	struct be_raw_label labels[BE_POLICY_MAX_LABELS];
};

/**
 * struct be_raw_need - one need set N(source, target, class) of A4
 * @source: source type
 * @target: target type
 * @class_id: class
 * @perm_count: number of permissions
 * @perms: permissions the use case requires
 */
struct be_raw_need {
	be_u32 source;
	be_u32 target;
	be_u32 class_id;
	be_size perm_count;
	be_u32 perms[BE_POLICY_MAX_PERMS];
};

/**
 * struct be_raw_grant - one right the manifest grants
 * @subject: receiving domain
 * @object: object, or for the domain class the target domain's subject
 * @class_id: class in which the right is granted
 * @perm_count: number of permissions
 * @perms: map and leaf rights, a channel end, or management permissions
 */
struct be_raw_grant {
	be_u32 subject;
	be_u32 object;
	be_u32 class_id;
	be_size perm_count;
	be_u32 perms[BE_POLICY_MAX_PERMS];
};

/**
 * struct be_raw_channel - one declared channel
 * @object: the channel object
 * @storage: its storage object, of class memory
 * @writer: writing domain
 * @reader: reading domain
 */
struct be_raw_channel {
	be_u32 object;
	be_u32 storage;
	be_u32 writer;
	be_u32 reader;
};

/**
 * struct be_raw_ownership - one memory object's owning domain
 * @object: owned object
 * @owner: owning domain's subject
 */
struct be_raw_ownership {
	be_u32 object;
	be_u32 owner;
};

/**
 * struct be_raw_binding - one domain's static hart binding
 * @domain: bound domain's subject
 * @hart: platform hart number
 */
struct be_raw_binding {
	be_u32 domain;
	be_u32 hart;
};

/**
 * struct be_raw_view - what the sealed configuration grants and binds
 * @ownership_count: number of ownerships
 * @ownerships: domain-owned memory objects
 * @channel_count: number of channels
 * @channels: declared channels
 * @grant_count: number of grants
 * @grants: rights the manifest grants
 * @binding_count: number of hart bindings
 * @bindings: hart bindings, mechanism metadata outside A8
 * @hart_count: number of started harts
 * @harts: started harts, the control hart among them
 * @control_hart: the control hart
 *
 * Monitor memory has no ownership: it is the memory no ownership names and
 * no channel uses (security model v1 Revision 1, R1.3, keeps bindings and
 * harts outside A8).
 */
struct be_raw_view {
	be_size ownership_count;
	struct be_raw_ownership ownerships[BE_POLICY_MAX_OWNERSHIPS];
	be_size channel_count;
	struct be_raw_channel channels[BE_POLICY_MAX_CHANNELS];
	be_size grant_count;
	struct be_raw_grant grants[BE_POLICY_MAX_GRANTS];
	be_size binding_count;
	struct be_raw_binding bindings[BE_POLICY_MAX_BINDINGS];
	be_size hart_count;
	be_u32 harts[BE_POLICY_MAX_HARTS];
	be_u32 control_hart;
};

/**
 * struct be_raw_instance - a policy, labeling, need sets, and view
 * @policy: raw policy
 * @labeling: raw labeling
 * @need_count: number of need sets
 * @needs: need sets of A4
 * @view: manifest view
 */
struct be_raw_instance {
	struct be_raw_policy policy;
	struct be_raw_labeling labeling;
	be_size need_count;
	struct be_raw_need needs[BE_POLICY_MAX_NEEDS];
	struct be_raw_view view;
};

/**
 * struct be_policy_validated - a policy, labeling, and view that passed A1
 * @policy: copied policy
 * @labeling: copied labeling
 * @view: copied view
 * @subject_present: nonzero for each subject of the configuration
 * @subject_type: each subject's one type
 * @object_present: nonzero for each object of the configuration
 * @object_type: each object's one type
 * @object_class: each object's class
 */
struct be_policy_validated {
	struct be_raw_policy policy;
	struct be_raw_labeling labeling;
	struct be_raw_view view;
	be_u8 subject_present[BE_POLICY_MAX_SUBJECTS];
	be_u32 subject_type[BE_POLICY_MAX_SUBJECTS];
	be_u8 object_present[BE_POLICY_MAX_OBJECTS];
	be_u32 object_type[BE_POLICY_MAX_OBJECTS];
	be_u32 object_class[BE_POLICY_MAX_OBJECTS];
};

/**
 * enum be_policy_code - analysis findings and sealing results
 * @BE_POLICY_OK: no finding
 * @BE_POLICY_NULL: a required pointer is absent
 * @BE_POLICY_A1_BOUND: an identifier or count exceeds a bound
 * @BE_POLICY_A1_DUPLICATE_TYPE: a type is declared twice
 * @BE_POLICY_A1_DUPLICATE_CLASS: a class is declared twice
 * @BE_POLICY_A1_CLASS_PERMISSIONS: a class's permissions are empty or repeat
 * @BE_POLICY_A1_UNDECLARED_TYPE: a rule or label names an undeclared type
 * @BE_POLICY_A1_UNDECLARED_CLASS: a rule names an undeclared class
 * @BE_POLICY_A1_EMPTY_PERMISSIONS: a rule's permission set is empty
 * @BE_POLICY_A1_UNKNOWN_PERMISSION: a rule's permission is not its class's
 * @BE_POLICY_A1_REPEATED_PERMISSION: a rule names a permission twice
 * @BE_POLICY_A1_DUPLICATE_ENTITY: the configuration lists an entity twice
 * @BE_POLICY_A1_UNKNOWN_ENTITY: a label names no entity of the configuration
 * @BE_POLICY_A1_UNLABELED: an entity of the configuration has no label
 * @BE_POLICY_A1_DOUBLY_LABELED: an entity has two labels
 * @BE_POLICY_A2_SOURCE_UNREACHABLE: a rule's source labels no subject
 * @BE_POLICY_A2_TARGET_UNREACHABLE: a rule's target labels no object of its class
 * @BE_POLICY_A3_MONITOR_MEMORY: a domain type holds a permission on monitor memory
 * @BE_POLICY_A3_FOREIGN_PRIVATE_MAP: a domain type maps another's private type
 * @BE_POLICY_A3_CHANNEL_WITHOUT_STORAGE: a channel rule has no memory rule
 * @BE_POLICY_A3_DOMAIN_TARGET: a domain rule names its own or a non-domain type
 * @BE_POLICY_A3_STORAGE_WITHOUT_CHANNEL: shared storage lacks a channel rule
 * @BE_POLICY_A4_MALFORMED_NEED: a need entry is not one set of declared names
 * @BE_POLICY_A4_NO_NEED: a rule has no need set
 * @BE_POLICY_A4_EXCESS: a rule grants a permission outside its need set
 * @BE_POLICY_A5_MULTIPLE_WRITERS: shared writable storage has two writers
 * @BE_POLICY_A5_STATIC_SINGLE_WRITER: a note: static, not revocable, one writer
 * @BE_POLICY_A6_UNDECLARED_FLOW: F+ holds a pair outside D+
 * @BE_POLICY_A6_UNREALIZED_CHANNEL: D+ holds a pair outside F+
 * @BE_POLICY_A7_DELEGATION: a domain holds a domain permission that grants
 * @BE_POLICY_A8_UNALLOWED: a granted permission is allowed by no rule
 * @BE_POLICY_SEAL_CANONICAL: the canonical state fails Model 0.2's check
 * @BE_POLICY_SEAL_CONFIGURATION: the labeling is not the canonical state's
 * @BE_POLICY_CODE_COUNT: upper bound for range checks
 */
enum be_policy_code {
	BE_POLICY_OK = 0,
	BE_POLICY_NULL,
	BE_POLICY_A1_BOUND,
	BE_POLICY_A1_DUPLICATE_TYPE,
	BE_POLICY_A1_DUPLICATE_CLASS,
	BE_POLICY_A1_CLASS_PERMISSIONS,
	BE_POLICY_A1_UNDECLARED_TYPE,
	BE_POLICY_A1_UNDECLARED_CLASS,
	BE_POLICY_A1_EMPTY_PERMISSIONS,
	BE_POLICY_A1_UNKNOWN_PERMISSION,
	BE_POLICY_A1_REPEATED_PERMISSION,
	BE_POLICY_A1_DUPLICATE_ENTITY,
	BE_POLICY_A1_UNKNOWN_ENTITY,
	BE_POLICY_A1_UNLABELED,
	BE_POLICY_A1_DOUBLY_LABELED,
	BE_POLICY_A2_SOURCE_UNREACHABLE,
	BE_POLICY_A2_TARGET_UNREACHABLE,
	BE_POLICY_A3_MONITOR_MEMORY,
	BE_POLICY_A3_FOREIGN_PRIVATE_MAP,
	BE_POLICY_A3_CHANNEL_WITHOUT_STORAGE,
	BE_POLICY_A3_DOMAIN_TARGET,
	BE_POLICY_A3_STORAGE_WITHOUT_CHANNEL,
	BE_POLICY_A4_MALFORMED_NEED,
	BE_POLICY_A4_NO_NEED,
	BE_POLICY_A4_EXCESS,
	BE_POLICY_A5_MULTIPLE_WRITERS,
	BE_POLICY_A5_STATIC_SINGLE_WRITER,
	BE_POLICY_A6_UNDECLARED_FLOW,
	BE_POLICY_A6_UNREALIZED_CHANNEL,
	BE_POLICY_A7_DELEGATION,
	BE_POLICY_A8_UNALLOWED,
	BE_POLICY_SEAL_CANONICAL,
	BE_POLICY_SEAL_CONFIGURATION,
	BE_POLICY_CODE_COUNT,
};

/**
 * struct be_policy_finding - one finding or note
 * @code: what was found
 * @index: rule, label, need, grant, or entity index, as @code defines
 * @first: a type, entity, or permission identifier
 * @second: a second identifier, or zero
 */
struct be_policy_finding {
	enum be_policy_code code;
	be_u32 index;
	be_u32 first;
	be_u32 second;
};

/**
 * struct be_policy_result - one analysis's bounded findings
 * @failures: failing findings, counted beyond the bound
 * @first_failure: the first failing finding's code, or BE_POLICY_OK
 * @count: findings and notes, counted beyond the bound
 * @items: the first BE_POLICY_MAX_FINDINGS findings and notes
 */
struct be_policy_result {
	be_size failures;
	enum be_policy_code first_failure;
	be_size count;
	struct be_policy_finding items[BE_POLICY_MAX_FINDINGS];
};

/**
 * struct be_policy_relation - a relation on types, one successor mask per type
 * @row: bit t of row[s] holds the pair (s, t)
 */
struct be_policy_relation {
	be_u32 row[BE_POLICY_MAX_TYPES];
};

/**
 * struct be_policy_verdicts - the eight analyses' verdicts
 * @evaluated: bit n-1 set when An was evaluated (A2 to A8 need A1)
 * @failed: bit n-1 set when An failed
 */
struct be_policy_verdicts {
	be_u32 evaluated;
	be_u32 failed;
};

/**
 * struct be_sealed_with_policy - a policy-sealed configuration's identities
 * @canonical_identity: Model 0.2's canonical identity, or the view identity
 *	for a view sealed without a canonical state
 * @policy_identity: be_policy_identity() of the policy
 * @labeling_identity: be_labeling_identity() of the labeling
 * @configuration_identity: be_combined_identity() of the three
 *
 * Need sets are inputs to A4 and are not part of any identity.
 */
struct be_sealed_with_policy {
	be_u64 canonical_identity;
	be_u64 policy_identity;
	be_u64 labeling_identity;
	be_u64 configuration_identity;
};

/**
 * enum be_binding_result - the static hart binding's checks (I13, I14)
 * @BE_BINDING_OK: injective and total into the non-control harts
 * @BE_BINDING_NOT_APPLICABLE: no binding: not a binding instance
 * @BE_BINDING_UNKNOWN: a binding names a non-domain or an unstarted hart
 * @BE_BINDING_CONTROL_HART: a domain is bound to the control hart
 * @BE_BINDING_NOT_INJECTIVE: two domains are bound to one hart
 * @BE_BINDING_NOT_TOTAL: a domain has no binding, or two
 */
enum be_binding_result {
	BE_BINDING_OK = 0,
	BE_BINDING_NOT_APPLICABLE,
	BE_BINDING_UNKNOWN,
	BE_BINDING_CONTROL_HART,
	BE_BINDING_NOT_INJECTIVE,
	BE_BINDING_NOT_TOTAL,
};

/**
 * be_policy_validate - A1: validate raw names into a typed labeling
 * @policy: raw policy
 * @labeling: raw labeling
 * @view: manifest view whose entities must be the labeling's
 * @validated: output written only when A1 passes
 * @result: optional; receives the first finding
 *
 * Return: BE_POLICY_OK, or the first A1 finding.
 */
enum be_policy_code
be_policy_validate(const struct be_raw_policy *policy,
		   const struct be_raw_labeling *labeling,
		   const struct be_raw_view *view,
		   struct be_policy_validated *validated,
		   struct be_policy_result *result);

/**
 * be_policy_decide - the policy's total, default-deny decision (I10)
 * @validated: validated policy
 * @source: source type
 * @target: target type
 * @class_id: class
 * @permission: permission
 *
 * Return: 1 if some rule allows the permission, otherwise 0.
 */
int be_policy_decide(const struct be_policy_validated *validated,
		     be_u32 source, be_u32 target, be_u32 class_id,
		     be_u32 permission);

/**
 * be_policy_a2 - unreachable authority
 * @validated: validated policy, labeling, and view
 * @result: findings
 *
 * Return: 1 on pass, 0 on failure.
 */
int be_policy_a2(const struct be_policy_validated *validated,
		 struct be_policy_result *result);

/**
 * be_policy_a3 - contradictory authority against I1, I2, and the channels
 * @validated: validated policy, labeling, and view
 * @result: findings
 *
 * Return: 1 on pass, 0 on failure.
 */
int be_policy_a3(const struct be_policy_validated *validated,
		 struct be_policy_result *result);

/**
 * be_policy_a4 - over-broad authority against the need sets
 * @validated: validated policy, labeling, and view
 * @needs: need sets
 * @need_count: number of need sets
 * @result: findings
 *
 * Return: 1 on pass, 0 on failure.
 */
int be_policy_a4(const struct be_policy_validated *validated,
		 const struct be_raw_need *needs, be_size need_count,
		 struct be_policy_result *result);

/**
 * be_policy_a5 - non-revocable authority; single-writer storage is a note
 * @validated: validated policy, labeling, and view
 * @result: findings and notes
 *
 * Return: 1 on pass, 0 on failure.
 */
int be_policy_a5(const struct be_policy_validated *validated,
		 struct be_policy_result *result);

/**
 * be_policy_relations - the flow relation F and the channel relation D
 * @validated: validated policy
 * @flows: F, write by one type and read by another of one target type
 * @channels: D, send by one type and receive by another of one target type
 */
void be_policy_relations(const struct be_policy_validated *validated,
			 struct be_policy_relation *flows,
			 struct be_policy_relation *channels);

/**
 * be_policy_closure - transitive closure of a relation
 * @relation: relation to close in place
 */
void be_policy_closure(struct be_policy_relation *relation);

/**
 * be_policy_a6 - information flow modulo the declared channels: F+ = D+
 * @validated: validated policy, labeling, and view
 * @result: findings
 *
 * Return: 1 on pass, 0 on failure.
 */
int be_policy_a6(const struct be_policy_validated *validated,
		 struct be_policy_result *result);

/**
 * be_policy_a7 - authority non-amplification, vacuous without delegation
 * @validated: validated policy, labeling, and view
 * @result: findings
 *
 * Return: 1 on pass, 0 when a domain holds a domain permission other than
 * pause or terminate, for which no request vocabulary exists.
 */
int be_policy_a7(const struct be_policy_validated *validated,
		 struct be_policy_result *result);

/**
 * be_policy_a8 - manifest conformance: every grant is allowed by a rule
 * @validated: validated policy, labeling, and view
 * @result: findings
 *
 * Return: 1 on pass, 0 on failure.
 */
int be_policy_a8(const struct be_policy_validated *validated,
		 struct be_policy_result *result);

/**
 * be_policy_verdicts - run A1 to A8 on one raw instance
 * @instance: raw instance
 * @verdicts: evaluated and failed analyses
 */
void be_policy_verdicts(const struct be_raw_instance *instance,
			struct be_policy_verdicts *verdicts);

/**
 * be_policy_view_flows - the view's flows: one domain's write and another's
 *	read of one memory object
 * @view: manifest view
 * @undeclared: optional; receives the flows no channel declares
 *
 * Return: number of flows.
 */
be_size be_policy_view_flows(const struct be_raw_view *view,
			     be_size *undeclared);

/**
 * be_policy_identity - deterministic reporting identity of a raw policy
 * @policy: policy whose fields are folded in fixed order
 *
 * Return: identity, or zero for NULL or an out-of-bound count.
 */
be_u64 be_policy_identity(const struct be_raw_policy *policy);

/**
 * be_labeling_identity - deterministic reporting identity of a raw labeling
 * @labeling: labeling whose fields are folded in fixed order
 *
 * Return: identity, or zero for NULL or an out-of-bound count.
 */
be_u64 be_labeling_identity(const struct be_raw_labeling *labeling);

/**
 * be_view_identity - deterministic reporting identity of a manifest view
 * @view: view whose fields are folded in fixed order
 *
 * Return: identity, or zero for NULL or an out-of-bound count.
 */
be_u64 be_view_identity(const struct be_raw_view *view);

/**
 * be_combined_identity - one configuration identity from three
 * @manifest: canonical (or view) identity
 * @policy: policy identity
 * @labeling: labeling identity
 *
 * Return: identity folded in the MVP checker's order: manifest, policy,
 * labeling.
 */
be_u64 be_combined_identity(be_u64 manifest, be_u64 policy, be_u64 labeling);

/**
 * be_view_of_canonical - Model 0.2's canonical state as a manifest view
 * @canonical: canonical state that passes be_check_canonical()
 * @view: output written only on success
 *
 * Subjects are the monitor and the canonical domains in order; objects are
 * the canonical frames in order and then the channels; each authority is a
 * memory grant of map and its leaf rights, and each channel end a send or
 * receive grant.
 *
 * Return: BE_POLICY_OK, BE_POLICY_NULL, or BE_POLICY_SEAL_CANONICAL.
 */
enum be_policy_code
be_view_of_canonical(const struct be_canonical_state *canonical,
		     struct be_raw_view *view);

/**
 * be_raw_view_equal - structural equality of two views
 * @left: first view
 * @right: second view
 *
 * Return: 1 when every count and element is equal, otherwise 0.
 */
int be_raw_view_equal(const struct be_raw_view *left,
		      const struct be_raw_view *right);

/**
 * be_seal_view_with_policy - seal a view only when A1 to A6 and A8 pass
 * @view: manifest view
 * @manifest_identity: the view's canonical or reporting identity
 * @policy: raw policy
 * @labeling: raw labeling
 * @needs: need sets of A4
 * @need_count: number of need sets
 * @sealed: output written only on success
 *
 * Return: BE_POLICY_OK, or the first failing finding's code.
 */
enum be_policy_code
be_seal_view_with_policy(const struct be_raw_view *view,
			 be_u64 manifest_identity,
			 const struct be_raw_policy *policy,
			 const struct be_raw_labeling *labeling,
			 const struct be_raw_need *needs, be_size need_count,
			 struct be_sealed_with_policy *sealed);

/**
 * be_seal_with_policy - seal Model 0.2's canonical state with a policy
 * @canonical: canonical state
 * @policy: raw policy
 * @labeling: raw labeling of the canonical state's subjects and objects
 * @needs: need sets of A4
 * @need_count: number of need sets
 * @sealed: output written only on success
 *
 * The accepted canonical state and its sealing are unchanged; this record
 * exists only when A1 to A6 and A8 pass on be_view_of_canonical().
 *
 * Return: BE_POLICY_OK, or why the configuration must not be sealed.
 */
enum be_policy_code
be_seal_with_policy(const struct be_canonical_state *canonical,
		    const struct be_raw_policy *policy,
		    const struct be_raw_labeling *labeling,
		    const struct be_raw_need *needs, be_size need_count,
		    struct be_sealed_with_policy *sealed);

/**
 * be_policy_check_bindings - the static hart binding's checks (I13, I14)
 * @labeling: the configuration's subjects; every non-monitor one is a domain
 * @view: bindings, started harts, and the control hart
 *
 * Return: BE_BINDING_NOT_APPLICABLE for a view with no binding, otherwise
 * the first failing check or BE_BINDING_OK.
 */
enum be_binding_result
be_policy_check_bindings(const struct be_raw_labeling *labeling,
			 const struct be_raw_view *view);

/**
 * be_policy_code_name - stable report name for a code
 * @code: code to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_policy_code_name(enum be_policy_code code);

/**
 * be_binding_result_name - stable report name for a binding result
 * @result: result to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_binding_result_name(enum be_binding_result result);

#endif
