/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

#ifndef BE_MANIFEST_H
#define BE_MANIFEST_H

#include <be/types.h>

#define BE_MODEL_VERSION	2U
#define BE_MODEL_HART_ID	0U
#define BE_PAGE_SIZE		BE_U64_C(4096)

#define BE_MAX_DOMAINS		2U
#define BE_MAX_RESOURCES	11U
#define BE_MAX_AUTHORITIES	12U
#define BE_MAX_ROOTS		2U
#define BE_MAX_MAPPINGS		12U
#define BE_MAX_SAVED_STATES	2U
#define BE_MAX_CHANNELS		1U

#define BE_OWNER_MONITOR	(1U << 0)
#define BE_OWNER_MANAGEMENT	(1U << 1)
#define BE_OWNER_PROTECTED	(1U << 2)
#define BE_OWNER_VS_MASK	(BE_OWNER_MANAGEMENT | BE_OWNER_PROTECTED)
#define BE_OWNER_ALL_MASK	(BE_OWNER_MONITOR | BE_OWNER_VS_MASK)

/**
 * enum be_architecture - architectures accepted by Model 0.2
 * @BE_ARCH_INVALID: fail-closed sentinel
 * @BE_ARCH_RISCV64: bounded RV64 architecture profile
 * @BE_ARCH_COUNT: upper bound for range checks
 */
enum be_architecture {
	BE_ARCH_INVALID = 0,
	BE_ARCH_RISCV64,
	BE_ARCH_COUNT,
};

/**
 * enum be_profile - versioned architecture-model profiles
 * @BE_PROFILE_INVALID: fail-closed sentinel
 * @BE_PROFILE_POLICY_NEUTRAL_SINGLE_HART_TWO_DOMAIN: Model 0.2 profile
 * @BE_PROFILE_COUNT: upper bound for range checks
 */
enum be_profile {
	BE_PROFILE_INVALID = 0,
	BE_PROFILE_POLICY_NEUTRAL_SINGLE_HART_TWO_DOMAIN,
	BE_PROFILE_COUNT,
};

/**
 * enum be_proposal_vocabulary - untrusted proposal-source vocabulary
 * @BE_VOCABULARY_INVALID: fail-closed sentinel
 * @BE_VOCABULARY_RELATIONS_A: first neutral source vocabulary
 * @BE_VOCABULARY_RELATIONS_B: second neutral source vocabulary
 * @BE_VOCABULARY_COUNT: upper bound for range checks
 *
 * This value is retained only for deterministic proposal reporting. It is
 * excluded from canonical authority, configuration identity, and enforcement.
 */
enum be_proposal_vocabulary {
	BE_VOCABULARY_INVALID = 0,
	BE_VOCABULARY_RELATIONS_A,
	BE_VOCABULARY_RELATIONS_B,
	BE_VOCABULARY_COUNT,
};

/**
 * enum be_domain_id - fixed untrusted VS-domain abstractions
 * @BE_DOMAIN_INVALID: fail-closed sentinel
 * @BE_DOMAIN_MANAGEMENT: untrusted management-domain abstraction
 * @BE_DOMAIN_PROTECTED: untrusted protected-domain abstraction
 * @BE_DOMAIN_COUNT: upper bound for range checks
 */
enum be_domain_id {
	BE_DOMAIN_INVALID = 0,
	BE_DOMAIN_MANAGEMENT,
	BE_DOMAIN_PROTECTED,
	BE_DOMAIN_COUNT,
};

/**
 * enum be_resource_kind - platform-inventory resource classes
 * @BE_RESOURCE_INVALID: fail-closed sentinel
 * @BE_RESOURCE_MONITOR_CODE: trusted HS code extent
 * @BE_RESOURCE_MONITOR_DATA: trusted HS data extent
 * @BE_RESOURCE_ROOT_TABLE: trusted G-stage table storage
 * @BE_RESOURCE_TRUSTED_STACK: trusted transition-stack storage
 * @BE_RESOURCE_SAVED_STATE: trusted saved-register storage
 * @BE_RESOURCE_ASSIGNABLE: storage whose private/shared role is proposed
 * @BE_RESOURCE_KIND_COUNT: upper bound for range checks
 */
enum be_resource_kind {
	BE_RESOURCE_INVALID = 0,
	BE_RESOURCE_MONITOR_CODE,
	BE_RESOURCE_MONITOR_DATA,
	BE_RESOURCE_ROOT_TABLE,
	BE_RESOURCE_TRUSTED_STACK,
	BE_RESOURCE_SAVED_STATE,
	BE_RESOURCE_ASSIGNABLE,
	BE_RESOURCE_KIND_COUNT,
};

/**
 * enum be_frame_class - canonical physical-frame classes
 * @BE_FRAME_INVALID: fail-closed sentinel
 * @BE_FRAME_MONITOR_CODE: trusted HS model code
 * @BE_FRAME_MONITOR_DATA: trusted HS model and canonical state
 * @BE_FRAME_ROOT_TABLE: G-stage root and lower-level table storage
 * @BE_FRAME_TRUSTED_STACK: HS transition stack storage
 * @BE_FRAME_SAVED_STATE: HS saved-register storage
 * @BE_FRAME_PRIVATE: one-domain private backing
 * @BE_FRAME_SHARED: explicitly declared channel backing
 * @BE_FRAME_CLASS_COUNT: upper bound for range checks
 */
enum be_frame_class {
	BE_FRAME_INVALID = 0,
	BE_FRAME_MONITOR_CODE,
	BE_FRAME_MONITOR_DATA,
	BE_FRAME_ROOT_TABLE,
	BE_FRAME_TRUSTED_STACK,
	BE_FRAME_SAVED_STATE,
	BE_FRAME_PRIVATE,
	BE_FRAME_SHARED,
	BE_FRAME_CLASS_COUNT,
};

/**
 * enum be_access_right - modeled G-stage access rights
 * @BE_RIGHT_READ: read authority
 * @BE_RIGHT_WRITE: write authority
 * @BE_RIGHT_EXECUTE: execute authority
 */
enum be_access_right {
	BE_RIGHT_READ = 1U << 0,
	BE_RIGHT_WRITE = 1U << 1,
	BE_RIGHT_EXECUTE = 1U << 2,
};

#define BE_RIGHT_ALL	(BE_RIGHT_READ | BE_RIGHT_WRITE | BE_RIGHT_EXECUTE)

/**
 * struct be_resource_desc - one bounded platform resource
 * @id: stable inventory-local resource identity
 * @base: page-aligned physical base
 * @size: nonzero page-multiple extent size
 * @kind: platform resource class
 */
struct be_resource_desc {
	be_u32 id;
	be_u64 base;
	be_u64 size;
	enum be_resource_kind kind;
};

/**
 * struct be_platform_inventory - normalized platform/resource input
 * @model_version: BE_MODEL_VERSION
 * @architecture: fixed architecture identifier
 * @profile: fixed Model 0.2 profile
 * @hart_id: sole active hart
 * @resource_count: complete bounded resource count
 * @resources: physical extents and immutable platform classes
 *
 * The inventory describes resources. It grants no domain authority.
 */
struct be_platform_inventory {
	be_u32 model_version;
	enum be_architecture architecture;
	enum be_profile profile;
	be_u32 hart_id;
	be_size resource_count;
	struct be_resource_desc resources[BE_MAX_RESOURCES];
};

/**
 * struct be_domain_request - proposed domain-to-transition binding
 * @id: requested canonical domain identity
 * @vcpu_id: requested sole vCPU identity
 * @root_id: requested G-stage root identity
 * @root_resource_id: inventory resource requested for root storage
 * @vmid: requested modeled HGATP VMID
 * @trusted_stack_resource_id: requested trusted transition stack
 * @saved_state_id: requested saved-state identity
 * @saved_state_resource_id: requested saved-state storage
 */
struct be_domain_request {
	enum be_domain_id id;
	be_u32 vcpu_id;
	be_u32 root_id;
	be_u32 root_resource_id;
	be_u32 vmid;
	be_u32 trusted_stack_resource_id;
	be_u32 saved_state_id;
	be_u32 saved_state_resource_id;
};

/**
 * struct be_resource_request - proposed use of one inventory extent
 * @resource_id: exact inventory resource identity
 * @base: proposed extent base, which must match the inventory
 * @size: proposed extent size, which must match the inventory
 * @class: requested canonical frame class
 * @owner: requested private owner, or BE_DOMAIN_INVALID
 */
struct be_resource_request {
	be_u32 resource_id;
	be_u64 base;
	be_u64 size;
	enum be_frame_class class;
	enum be_domain_id owner;
};

/**
 * struct be_authority_request - proposed domain mapping authority
 * @domain: requested receiving domain
 * @gpa: requested guest-physical page
 * @resource_id: requested inventory backing
 * @rights: requested maximum R/W/X rights
 */
struct be_authority_request {
	enum be_domain_id domain;
	be_u64 gpa;
	be_u32 resource_id;
	be_u32 rights;
};

/**
 * struct be_channel_request - proposed directional storage channel
 * @id: requested channel identity
 * @source: requested writing endpoint
 * @target: requested read-only endpoint
 * @resource_id: requested shared backing
 * @source_rights: requested source rights
 * @target_rights: requested target rights
 */
struct be_channel_request {
	be_u32 id;
	enum be_domain_id source;
	enum be_domain_id target;
	be_u32 resource_id;
	be_u32 source_rights;
	be_u32 target_rights;
};

/**
 * struct be_proposal - copied untrusted policy-neutral configuration proposal
 * @proposal_id: reporting-only producer identity
 * @source_vocabulary: reporting-only neutral source vocabulary
 * @domain_count: complete requested domain count
 * @domains: requested domain/vCPU/root/stack/saved-state bindings
 * @resource_count: complete requested inventory assignment count
 * @resources: requested extent classes and private ownership
 * @authority_count: complete requested domain mapping authority count
 * @authorities: requested GPA/resource/right relationships
 * @channel_count: complete requested channel count
 * @channels: requested directional shared-memory channel
 * @published_root_count: forbidden producer-supplied derived-root claim
 * @published_mapping_count: forbidden producer-supplied mapping claim
 * @published_active_domain: forbidden producer-supplied active binding
 *
 * The final three fields model direct-authority injection attempts. Accepted
 * proposals must leave them empty; producer claims never become authority.
 */
struct be_proposal {
	be_u64 proposal_id;
	enum be_proposal_vocabulary source_vocabulary;
	be_size domain_count;
	struct be_domain_request domains[BE_MAX_DOMAINS];
	be_size resource_count;
	struct be_resource_request resources[BE_MAX_RESOURCES];
	be_size authority_count;
	struct be_authority_request authorities[BE_MAX_AUTHORITIES];
	be_size channel_count;
	struct be_channel_request channels[BE_MAX_CHANNELS];
	be_size published_root_count;
	be_size published_mapping_count;
	enum be_domain_id published_active_domain;
};

/**
 * struct be_domain_desc - canonical domain-to-transition binding
 * @id: canonical domain identity
 * @vcpu_id: sole vCPU identity
 * @root_id: sole G-stage root identity
 * @root_table_frame: monitor-owned root storage
 * @vmid: modeled HGATP VMID
 * @trusted_stack_frame: HS transition stack
 * @saved_state_id: disjoint saved-register state identity
 * @saved_state_frame: monitor-owned saved-register storage
 */
struct be_domain_desc {
	enum be_domain_id id;
	be_u32 vcpu_id;
	be_u32 root_id;
	be_u32 root_table_frame;
	be_u32 vmid;
	be_u32 trusted_stack_frame;
	be_u32 saved_state_id;
	be_u32 saved_state_frame;
};

/**
 * struct be_frame_desc - canonical physical extent and ownership
 * @id: canonical inventory resource identity
 * @base: page-aligned physical base
 * @size: nonzero page-multiple extent size
 * @class: security class controlling mapping eligibility
 * @owner_mask: monitor or VS ownership bits; shared backing has no owner bit
 */
struct be_frame_desc {
	be_u32 id;
	be_u64 base;
	be_u64 size;
	enum be_frame_class class;
	be_u32 owner_mask;
};

/**
 * struct be_authority_desc - canonical domain mapping authority
 * @domain: domain receiving authority
 * @gpa: guest-physical address at which authority may be installed
 * @frame_id: canonical backing frame
 * @rights: maximum R/W/X rights
 */
struct be_authority_desc {
	enum be_domain_id domain;
	be_u64 gpa;
	be_u32 frame_id;
	be_u32 rights;
};

/**
 * struct be_saved_state_desc - canonical saved-state ownership and storage
 * @id: canonical state identity
 * @owner: sole domain whose registers occupy this state
 * @frame_id: monitor-owned saved-state storage
 */
struct be_saved_state_desc {
	be_u32 id;
	enum be_domain_id owner;
	be_u32 frame_id;
};

/**
 * struct be_channel_desc - canonical directional storage channel
 * @id: canonical channel identity
 * @source: sole writing endpoint
 * @target: read-only receiving endpoint
 * @frame_id: explicitly shared backing frame
 * @source_rights: source R/W rights
 * @target_rights: target read rights
 */
struct be_channel_desc {
	be_u32 id;
	enum be_domain_id source;
	enum be_domain_id target;
	be_u32 frame_id;
	be_u32 source_rights;
	be_u32 target_rights;
};

/**
 * struct be_canonical_state - validated canonical state sealed by HS
 * @model_version: BE_MODEL_VERSION
 * @architecture: fixed architecture identifier
 * @profile: fixed Model 0.2 profile
 * @hart_id: sole active hart
 * @configuration_id: deterministic reporting-only canonical identity
 * @domain_count: complete canonical domain count
 * @domains: sorted immutable transition bindings
 * @frame_count: complete canonical extent count
 * @frames: sorted extent, class, and ownership declarations
 * @authority_count: complete canonical authority count
 * @authorities: sorted maximum domain/GPA/frame rights
 * @saved_state_count: complete canonical saved-state count
 * @saved_states: sorted disjoint saved-state ownership
 * @channel_count: complete canonical channel count
 * @channels: sorted directional shared-memory channels
 *
 * Proposal identity, source vocabulary, and record order are deliberately
 * absent. The configuration identity is not a cryptographic measurement.
 */
struct be_canonical_state {
	be_u32 model_version;
	enum be_architecture architecture;
	enum be_profile profile;
	be_u32 hart_id;
	be_u64 configuration_id;
	be_size domain_count;
	struct be_domain_desc domains[BE_MAX_DOMAINS];
	be_size frame_count;
	struct be_frame_desc frames[BE_MAX_RESOURCES];
	be_size authority_count;
	struct be_authority_desc authorities[BE_MAX_AUTHORITIES];
	be_size saved_state_count;
	struct be_saved_state_desc saved_states[BE_MAX_SAVED_STATES];
	be_size channel_count;
	struct be_channel_desc channels[BE_MAX_CHANNELS];
};

/**
 * struct be_mapping_desc - one internally derived root mapping
 * @gpa: guest-physical page base
 * @frame_id: canonical backing frame
 * @rights: derived R/W/X PTE rights
 */
struct be_mapping_desc {
	be_u64 gpa;
	be_u32 frame_id;
	be_u32 rights;
};

/**
 * struct be_root_image - internally derived G-stage root
 * @root_id: root identity
 * @root_table_frame: monitor-owned root storage
 * @domain: bound domain
 * @vcpu_id: bound vCPU
 * @vmid: modeled VMID
 * @trusted_stack_frame: incoming HS transition stack
 * @saved_state_id: incoming saved-register state
 * @saved_state_frame: monitor-owned saved-register storage
 * @mapping_count: complete derived mapping count
 * @mappings: exact modeled leaf mappings
 */
struct be_root_image {
	be_u32 root_id;
	be_u32 root_table_frame;
	enum be_domain_id domain;
	be_u32 vcpu_id;
	be_u32 vmid;
	be_u32 trusted_stack_frame;
	be_u32 saved_state_id;
	be_u32 saved_state_frame;
	be_size mapping_count;
	struct be_mapping_desc mappings[BE_MAX_MAPPINGS];
};

/**
 * struct be_enforcement_state - enforcement derived only from sealed state
 * @configuration_id: canonical state from which this state was derived
 * @root_count: complete internally derived root count
 * @roots: domain roots and mappings
 */
struct be_enforcement_state {
	be_u64 configuration_id;
	be_size root_count;
	struct be_root_image roots[BE_MAX_ROOTS];
};

/**
 * enum be_check_result - deterministic Model 0.2 rejection classes
 * @BE_CHECK_OK: input or state accepted
 * @BE_CHECK_NULL: required pointer is absent
 * @BE_CHECK_INVALID_PHASE: operation is invalid in the current phase
 * @BE_CHECK_INCOMPLETE: required bounded input is missing
 * @BE_CHECK_UNSUPPORTED: version, enum, value, right, or extent is unsupported
 * @BE_CHECK_DIRECT_AUTHORITY: producer or pre-seal state publishes authority
 * @BE_CHECK_DUPLICATE_RESOURCE: resource identities are duplicated
 * @BE_CHECK_OVERLAPPING_RESOURCE: physical resource extents overlap
 * @BE_CHECK_INVENTORY_CLOSURE: proposal extent is absent from the inventory
 * @BE_CHECK_PRIVATE_OWNER: private ownership is absent, ambiguous, or wrong
 * @BE_CHECK_EXCLUDED_MAPPING: authority reaches monitor-owned state
 * @BE_CHECK_UNDECLARED_MAPPING: mapping lacks exact canonical authority
 * @BE_CHECK_EXCESS_RIGHTS: derived rights exceed canonical authority
 * @BE_CHECK_UNDECLARED_SHARED: shared backing is not the declared channel
 * @BE_CHECK_CHANNEL_RIGHTS: endpoint rights violate channel direction
 * @BE_CHECK_BINDING: vCPU/root/VMID/stack/saved-state binding is wrong
 * @BE_CHECK_INTEGRITY: canonical or derived identity changed after validation
 */
enum be_check_result {
	BE_CHECK_OK = 0,
	BE_CHECK_NULL,
	BE_CHECK_INVALID_PHASE,
	BE_CHECK_INCOMPLETE,
	BE_CHECK_UNSUPPORTED,
	BE_CHECK_DIRECT_AUTHORITY,
	BE_CHECK_DUPLICATE_RESOURCE,
	BE_CHECK_OVERLAPPING_RESOURCE,
	BE_CHECK_INVENTORY_CLOSURE,
	BE_CHECK_PRIVATE_OWNER,
	BE_CHECK_EXCLUDED_MAPPING,
	BE_CHECK_UNDECLARED_MAPPING,
	BE_CHECK_EXCESS_RIGHTS,
	BE_CHECK_UNDECLARED_SHARED,
	BE_CHECK_CHANNEL_RIGHTS,
	BE_CHECK_BINDING,
	BE_CHECK_INTEGRITY,
};

/**
 * be_check_inventory - validate the bounded normalized platform inventory
 * @inventory: inventory to validate
 *
 * Return: deterministic rejection class, or BE_CHECK_OK.
 */
enum be_check_result
be_check_inventory(const struct be_platform_inventory *inventory);

/**
 * be_canonicalize - validate and canonicalize one copied proposal
 * @inventory: validated platform inventory
 * @proposal: copied untrusted proposal
 * @canonical: output written only after complete successful validation
 *
 * Return: deterministic rejection class, or BE_CHECK_OK.
 */
enum be_check_result
be_canonicalize(const struct be_platform_inventory *inventory,
		const struct be_proposal *proposal,
		struct be_canonical_state *canonical);

/**
 * be_check_canonical - independently validate canonical state and identity
 * @canonical: canonical state to validate
 *
 * Return: deterministic rejection class, or BE_CHECK_OK.
 */
enum be_check_result
be_check_canonical(const struct be_canonical_state *canonical);

/**
 * be_derive_enforcement - derive roots solely from canonical sealed state
 * @canonical: valid canonical state
 * @enforcement: output written only after complete successful derivation
 *
 * Return: deterministic rejection class, or BE_CHECK_OK.
 */
enum be_check_result
be_derive_enforcement(const struct be_canonical_state *canonical,
		      struct be_enforcement_state *enforcement);

/**
 * be_check_enforcement - validate derived state against canonical authority
 * @canonical: valid canonical state
 * @enforcement: derived roots and mappings to validate
 *
 * Return: deterministic rejection class, or BE_CHECK_OK.
 */
enum be_check_result
be_check_enforcement(const struct be_canonical_state *canonical,
		     const struct be_enforcement_state *enforcement);

/**
 * be_configuration_identity - compute deterministic canonical report identity
 * @canonical: canonical state whose scalar fields are folded in fixed order
 *
 * Return: reporting-only identity, or zero for NULL.
 */
be_u64
be_configuration_identity(const struct be_canonical_state *canonical);

/**
 * be_check_result_name - stable report name for a checker result
 * @result: result to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_check_result_name(enum be_check_result result);

/**
 * be_architecture_name - stable report name for an architecture
 * @architecture: architecture to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_architecture_name(enum be_architecture architecture);

/**
 * be_profile_name - stable report name for a profile
 * @profile: profile to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_profile_name(enum be_profile profile);

/**
 * be_proposal_vocabulary_name - stable proposal-source vocabulary name
 * @vocabulary: vocabulary to name
 *
 * Return: constant name, or "invalid".
 */
const char *
be_proposal_vocabulary_name(enum be_proposal_vocabulary vocabulary);

/**
 * be_domain_name - stable report name for a domain
 * @domain: domain to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_domain_name(enum be_domain_id domain);

/**
 * be_resource_kind_name - stable report name for an inventory kind
 * @kind: resource kind to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_resource_kind_name(enum be_resource_kind kind);

/**
 * be_frame_class_name - stable report name for a canonical frame class
 * @class: class to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_frame_class_name(enum be_frame_class class);

#endif
