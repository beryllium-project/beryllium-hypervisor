/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: fixed-profile R1 inventory, proposal, canonical, and enforcement
 *          contract for the bounded single-hart Beryllium runtime.
 * Trust:   public checker and runtime-state contract only. Copied proposals are
 *          non-authoritative until validation, sealing, and derivation succeed.
 * Scope:   accepted R1 non-privileged mechanism only. This header is separate
 *          from Model 0.2 source and carries the full thirteen-resource runtime
 *          profile including guest-code resources.
 */

#ifndef BE_MANIFEST_H
#define BE_MANIFEST_H

#include <be/types.h>

#define BE_CONFIGURATION_VERSION	1U
#define BE_CONFIGURATION_HART_ID	0U
#define BE_PAGE_SIZE			BE_U64_C(4096)

#define BE_MAX_DOMAINS			2U
#define BE_MAX_RESOURCES		13U
#define BE_MAX_AUTHORITIES		6U
#define BE_MAX_ROOTS			2U
#define BE_MAX_MAPPINGS			6U
#define BE_MAX_SAVED_STATES		2U
#define BE_MAX_CHANNELS			1U

#define BE_OWNER_MONITOR		(1U << 0)
#define BE_OWNER_MANAGEMENT		(1U << 1)
#define BE_OWNER_PROTECTED		(1U << 2)
#define BE_OWNER_VS_MASK		(BE_OWNER_MANAGEMENT | BE_OWNER_PROTECTED)
#define BE_OWNER_ALL_MASK		(BE_OWNER_MONITOR | BE_OWNER_VS_MASK)

/**
 * enum be_architecture - architectures accepted by the R1 runtime checker
 * @BE_ARCH_INVALID: fail-closed sentinel
 * @BE_ARCH_RISCV64: bounded RV64 runtime profile
 * @BE_ARCH_COUNT: upper bound for range checks
 */
enum be_architecture {
	BE_ARCH_INVALID = 0,
	BE_ARCH_RISCV64,
	BE_ARCH_COUNT,
};

/**
 * enum be_profile - accepted runtime profiles
 * @BE_PROFILE_INVALID: fail-closed sentinel
 * @BE_PROFILE_FIXED_SINGLE_HART_TWO_DOMAIN: accepted fixed R1 profile
 * @BE_PROFILE_COUNT: upper bound for range checks
 */
enum be_profile {
	BE_PROFILE_INVALID = 0,
	BE_PROFILE_FIXED_SINGLE_HART_TWO_DOMAIN,
	BE_PROFILE_COUNT,
};

/**
 * enum be_proposal_vocabulary - copied producer metadata vocabulary
 * @BE_VOCABULARY_INVALID: fail-closed sentinel
 * @BE_VOCABULARY_A: first neutral source vocabulary
 * @BE_VOCABULARY_B: second neutral source vocabulary
 * @BE_VOCABULARY_COUNT: upper bound for range checks
 *
 * Source vocabulary is reporting metadata only. It is excluded from canonical
 * authority, configuration identity, and derived enforcement.
 */
enum be_proposal_vocabulary {
	BE_VOCABULARY_INVALID = 0,
	BE_VOCABULARY_A,
	BE_VOCABULARY_B,
	BE_VOCABULARY_COUNT,
};

/**
 * enum be_domain_id - fixed untrusted VS-domain identifiers
 * @BE_DOMAIN_INVALID: fail-closed sentinel
 * @BE_DOMAIN_MANAGEMENT: retained management-domain identifier for R0 traceability
 * @BE_DOMAIN_PROTECTED: retained protected-domain identifier for R0 traceability
 * @BE_DOMAIN_COUNT: upper bound for range checks
 */
enum be_domain_id {
	BE_DOMAIN_INVALID = 0,
	BE_DOMAIN_MANAGEMENT,
	BE_DOMAIN_PROTECTED,
	BE_DOMAIN_COUNT,
};

/**
 * enum be_resource_kind - inventory resource classes
 * @BE_RESOURCE_INVALID: fail-closed sentinel
 * @BE_RESOURCE_MONITOR_CODE: trusted HS code extent
 * @BE_RESOURCE_MONITOR_DATA: trusted HS data extent
 * @BE_RESOURCE_ROOT_TABLE: trusted G-stage root/table storage
 * @BE_RESOURCE_TRUSTED_STACK: trusted transition-stack storage
 * @BE_RESOURCE_SAVED_STATE: trusted saved-register storage
 * @BE_RESOURCE_ASSIGNABLE: assignable private-or-shared runtime data frame
 * @BE_RESOURCE_GUEST_CODE: domain-owned operational guest-code frame
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
	BE_RESOURCE_GUEST_CODE,
	BE_RESOURCE_KIND_COUNT,
};

/**
 * enum be_frame_class - canonical frame classes
 * @BE_FRAME_INVALID: fail-closed sentinel
 * @BE_FRAME_MONITOR_CODE: trusted HS code frame
 * @BE_FRAME_MONITOR_DATA: trusted HS data frame
 * @BE_FRAME_ROOT_TABLE: trusted root/table frame
 * @BE_FRAME_TRUSTED_STACK: trusted transition-stack frame
 * @BE_FRAME_SAVED_STATE: trusted saved-register frame
 * @BE_FRAME_PRIVATE: domain-owned private RW frame
 * @BE_FRAME_SHARED: explicitly declared directional shared frame
 * @BE_FRAME_GUEST_CODE: domain-owned guest-code R-X frame
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
	BE_FRAME_GUEST_CODE,
	BE_FRAME_CLASS_COUNT,
};

/**
 * enum be_access_right - modeled R/W/X rights
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
 * struct be_resource_desc - one bounded inventory resource
 * @id: stable inventory-local identity
 * @base: page-aligned physical base
 * @size: nonzero page-multiple extent size
 * @kind: immutable resource class
 */
struct be_resource_desc {
	be_u32 id;
	be_u64 base;
	be_u64 size;
	enum be_resource_kind kind;
};

/**
 * struct be_platform_inventory - copied normalized platform inventory
 * @configuration_version: BE_CONFIGURATION_VERSION
 * @architecture: accepted architecture identifier
 * @profile: accepted fixed profile identifier
 * @hart_id: sole active hart identifier
 * @resource_count: complete bounded resource count
 * @resources: immutable resource declarations
 */
struct be_platform_inventory {
	be_u32 configuration_version;
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
 * @root_resource_id: requested inventory resource for root storage
 * @vmid: requested modeled VMID; fixed profile requires zero
 * @trusted_stack_resource_id: requested trusted transition stack resource
 * @saved_state_id: requested saved-state identity
 * @saved_state_resource_id: requested saved-state storage resource
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
 * struct be_resource_request - proposed use of one inventory resource
 * @resource_id: exact inventory resource identity
 * @base: proposed extent base; must match the inventory
 * @size: proposed extent size; must match the inventory
 * @class: requested canonical frame class
 * @owner: requested owner for private or guest-code frames, or invalid
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
 * @gpa: requested guest-physical page base
 * @resource_id: requested backing resource identity
 * @rights: requested maximum R/W/X rights
 */
struct be_authority_request {
	enum be_domain_id domain;
	be_u64 gpa;
	be_u32 resource_id;
	be_u32 rights;
};

/**
 * struct be_channel_request - proposed directional shared-memory channel
 * @id: requested channel identity
 * @source: requested source endpoint
 * @target: requested target endpoint
 * @resource_id: requested shared backing resource identity
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
 * struct be_proposal - copied untrusted configuration proposal
 * @proposal_id: reporting-only producer identity
 * @source_vocabulary: reporting-only producer vocabulary metadata
 * @domain_count: complete proposed domain count
 * @domains: proposed domain bindings
 * @resource_count: complete proposed resource assignments
 * @resources: proposed frame-class and ownership requests
 * @authority_count: complete proposed authorities
 * @authorities: proposed GPA/resource/right relationships
 * @channel_count: complete proposed channel count
 * @channels: proposed directional shared-memory channels
 * @published_root_count: forbidden producer-supplied derived-root claim
 * @published_mapping_count: forbidden producer-supplied mapping claim
 * @published_active_domain: forbidden producer-supplied active-domain claim
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
 * @root_id: sole root identity
 * @root_table_frame: monitor-owned root storage frame identity
 * @vmid: modeled VMID; fixed profile requires zero
 * @trusted_stack_frame: monitor-owned transition-stack frame identity
 * @saved_state_id: disjoint saved-state identity
 * @saved_state_frame: monitor-owned saved-state frame identity
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
 * struct be_frame_desc - canonical physical frame and ownership declaration
 * @id: canonical resource identity
 * @base: page-aligned physical base
 * @size: nonzero page-multiple extent size
 * @class: canonical frame class
 * @owner_mask: monitor or domain ownership bits; shared frames carry no owner
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
 * @domain: receiving domain
 * @gpa: guest-physical page base
 * @frame_id: canonical backing frame identity
 * @rights: maximum canonical R/W/X rights
 */
struct be_authority_desc {
	enum be_domain_id domain;
	be_u64 gpa;
	be_u32 frame_id;
	be_u32 rights;
};

/**
 * struct be_saved_state_desc - canonical saved-state ownership and storage
 * @id: canonical saved-state identity
 * @owner: sole owning domain
 * @frame_id: monitor-owned storage frame identity
 */
struct be_saved_state_desc {
	be_u32 id;
	enum be_domain_id owner;
	be_u32 frame_id;
};

/**
 * struct be_channel_desc - canonical directional shared-memory channel
 * @id: canonical channel identity
 * @source: sole writing endpoint
 * @target: sole read-only receiving endpoint
 * @frame_id: explicitly shared backing frame identity
 * @source_rights: canonical source rights
 * @target_rights: canonical target rights
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
 * struct be_canonical_state - validated and sealable runtime state
 * @configuration_version: BE_CONFIGURATION_VERSION
 * @architecture: accepted architecture identifier
 * @profile: accepted fixed profile identifier
 * @hart_id: sole active hart identifier
 * @configuration_id: deterministic reporting-only configuration identity
 * @domain_count: complete canonical domain count
 * @domains: fixed-order canonical domain bindings
 * @frame_count: complete canonical frame count
 * @frames: sorted canonical frames
 * @authority_count: complete canonical authority count
 * @authorities: sorted canonical authorities
 * @saved_state_count: complete canonical saved-state count
 * @saved_states: fixed-order saved-state bindings
 * @channel_count: complete canonical channel count
 * @channels: canonical channels
 */
struct be_canonical_state {
	be_u32 configuration_version;
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
 * struct be_mapping_desc - one abstract derived root mapping
 * @gpa: guest-physical page base
 * @frame_id: canonical backing frame identity
 * @rights: derived R/W/X rights
 */
struct be_mapping_desc {
	be_u64 gpa;
	be_u32 frame_id;
	be_u32 rights;
};

/**
 * struct be_root_image - one abstract derived domain root
 * @root_id: root identity
 * @root_table_frame: monitor-owned root storage frame identity
 * @domain: bound domain identity
 * @vcpu_id: bound vCPU identity
 * @vmid: bound modeled VMID
 * @trusted_stack_frame: bound transition-stack frame identity
 * @saved_state_id: bound saved-state identity
 * @saved_state_frame: bound saved-state frame identity
 * @mapping_count: complete derived mapping count for this root
 * @mappings: abstract root mappings
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
 * @configuration_id: canonical state identity from which roots were derived
 * @root_count: complete derived root count
 * @roots: abstract roots and mappings
 */
struct be_enforcement_state {
	be_u64 configuration_id;
	be_size root_count;
	struct be_root_image roots[BE_MAX_ROOTS];
};

/**
 * enum be_check_result - deterministic checker results
 * @BE_CHECK_OK: input or state accepted
 * @BE_CHECK_NULL: required pointer is absent
 * @BE_CHECK_INVALID_PHASE: operation is invalid in the current phase
 * @BE_CHECK_INCOMPLETE: required bounded input is missing
 * @BE_CHECK_UNSUPPORTED: version, enum, value, right, or extent is unsupported
 * @BE_CHECK_DIRECT_AUTHORITY: producer or pre-seal state publishes authority
 * @BE_CHECK_DUPLICATE_RESOURCE: resource identities are duplicated
 * @BE_CHECK_OVERLAPPING_RESOURCE: physical resource extents overlap
 * @BE_CHECK_INVENTORY_CLOSURE: proposal extent is absent from the inventory
 * @BE_CHECK_PRIVATE_OWNER: private or guest-code ownership is absent or wrong
 * @BE_CHECK_EXCLUDED_MAPPING: authority reaches monitor-owned state
 * @BE_CHECK_UNDECLARED_MAPPING: mapping lacks exact canonical backing declaration
 * @BE_CHECK_EXCESS_RIGHTS: rights exceed the accepted fixed-profile authority
 * @BE_CHECK_UNDECLARED_SHARED: shared backing is not the declared channel
 * @BE_CHECK_CHANNEL_RIGHTS: channel rights violate the fixed direction
 * @BE_CHECK_BINDING: domain/root/VMID/stack/saved-state binding is wrong
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
 * Return: deterministic rejection class, or %BE_CHECK_OK.
 */
enum be_check_result
be_check_inventory(const struct be_platform_inventory *inventory);

/**
 * be_canonicalize - validate and canonicalize one copied proposal
 * @inventory: validated platform inventory
 * @proposal: copied untrusted proposal
 * @canonical: output written only after complete successful validation
 *
 * Return: deterministic rejection class, or %BE_CHECK_OK.
 */
enum be_check_result
be_canonicalize(const struct be_platform_inventory *inventory,
		const struct be_proposal *proposal,
		struct be_canonical_state *canonical);

/**
 * be_check_canonical - independently validate canonical state and identity
 * @canonical: canonical state to validate
 *
 * Return: deterministic rejection class, or %BE_CHECK_OK.
 */
enum be_check_result
be_check_canonical(const struct be_canonical_state *canonical);

/**
 * be_derive_enforcement - derive abstract roots solely from sealed authority
 * @canonical: valid canonical state
 * @enforcement: output written only after complete successful derivation
 *
 * Return: deterministic rejection class, or %BE_CHECK_OK.
 */
enum be_check_result
be_derive_enforcement(const struct be_canonical_state *canonical,
		      struct be_enforcement_state *enforcement);

/**
 * be_check_enforcement - validate derived state against canonical authority
 * @canonical: valid canonical state
 * @enforcement: derived roots and mappings to validate
 *
 * Return: deterministic rejection class, or %BE_CHECK_OK.
 */
enum be_check_result
be_check_enforcement(const struct be_canonical_state *canonical,
		     const struct be_enforcement_state *enforcement);

/**
 * be_configuration_identity - compute deterministic configuration identity
 * @canonical: canonical state whose sorted scalar fields are folded in order
 *
 * The returned scalar is for reporting and equivalence only. It is never an
 * integrity measurement or attestation token.
 *
 * Return: reporting-only identity, or zero for %NULL.
 */
be_u64 be_configuration_identity(const struct be_canonical_state *canonical);

/**
 * be_check_result_name - return the stable name of a checker result
 * @result: result to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_check_result_name(enum be_check_result result);

/**
 * be_architecture_name - return the stable name of an architecture
 * @architecture: architecture to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_architecture_name(enum be_architecture architecture);

/**
 * be_profile_name - return the stable name of a profile
 * @profile: profile to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_profile_name(enum be_profile profile);

/**
 * be_proposal_vocabulary_name - return the stable name of a proposal vocabulary
 * @vocabulary: vocabulary to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_proposal_vocabulary_name(enum be_proposal_vocabulary vocabulary);

/**
 * be_domain_name - return the stable name of a domain identifier
 * @domain: domain to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_domain_name(enum be_domain_id domain);

/**
 * be_resource_kind_name - return the stable name of a resource kind
 * @kind: resource kind to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_resource_kind_name(enum be_resource_kind kind);

/**
 * be_frame_class_name - return the stable name of a frame class
 * @class: frame class to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_frame_class_name(enum be_frame_class class);

#endif
