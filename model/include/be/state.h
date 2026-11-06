/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

#ifndef BE_STATE_H
#define BE_STATE_H

#include <be/manifest.h>

#define BE_MODEL_REGISTER_COUNT	8U
#define BE_MAX_CACHE_ENTRIES	BE_MAX_MAPPINGS

/**
 * enum be_model_phase - executable Model 0.2 control states
 * @BE_PHASE_EMPTY: reset state; no input is bound
 * @BE_PHASE_INVENTORY_BOUND: validated inventory copied
 * @BE_PHASE_PROPOSAL_COPIED: untrusted proposal copied but not validated
 * @BE_PHASE_VALIDATED: canonical state built but not authoritative
 * @BE_PHASE_SEALED: canonical state sealed and authoritative
 * @BE_PHASE_ROOTS_DERIVED: enforcement derived but no domain runnable
 * @BE_PHASE_ACTIVE: one correctly bound domain is active
 * @BE_PHASE_SWITCHING: target binding selected but entry is blocked
 * @BE_PHASE_FAILED: terminal fail-closed state
 */
enum be_model_phase {
	BE_PHASE_EMPTY = 0,
	BE_PHASE_INVENTORY_BOUND,
	BE_PHASE_PROPOSAL_COPIED,
	BE_PHASE_VALIDATED,
	BE_PHASE_SEALED,
	BE_PHASE_ROOTS_DERIVED,
	BE_PHASE_ACTIVE,
	BE_PHASE_SWITCHING,
	BE_PHASE_FAILED,
};

/**
 * enum be_model_result - executable operation result
 * @BE_MODEL_OK: state transition completed
 * @BE_MODEL_ALLOWED: modeled access was authorized
 * @BE_MODEL_DENIED: modeled access was rejected without granting authority
 * @BE_MODEL_FAILED: operation entered or retained terminal failure
 */
enum be_model_result {
	BE_MODEL_OK = 0,
	BE_MODEL_ALLOWED,
	BE_MODEL_DENIED,
	BE_MODEL_FAILED,
};

/**
 * struct be_register_file - bounded saved architectural-state projection
 * @value: abstract general-register values
 */
struct be_register_file {
	be_u64 value[BE_MODEL_REGISTER_COUNT];
};

/**
 * struct be_saved_register_state - one domain-owned saved state
 * @id: canonical saved-state identity
 * @owner: sole domain whose values this slot may contain
 * @frame_id: monitor-owned canonical storage
 * @registers: saved register projection
 */
struct be_saved_register_state {
	be_u32 id;
	enum be_domain_id owner;
	be_u32 frame_id;
	struct be_register_file registers;
};

/**
 * struct be_cached_translation - stale-authority hazard projection
 * @valid: entry contains a prior successful translation
 * @vmid: VMID tag used for lookup
 * @gpa: translated guest-physical page
 * @frame_id: resolved backing frame
 * @rights: cached R/W/X authority
 */
struct be_cached_translation {
	be_u32 valid;
	be_u32 vmid;
	be_u64 gpa;
	be_u32 frame_id;
	be_u32 rights;
};

/**
 * struct be_model - complete executable Model 0.2 state
 * @inventory: validated private inventory copy
 * @proposal: copied untrusted proposal
 * @canonical: validated state, authoritative only after sealing
 * @enforcement: roots derived only from sealed canonical state
 * @phase: current control phase
 * @check_result: latest validation or integrity result
 * @validated_identity: identity retained across the seal boundary
 * @sealed_identity: immutable identity retained after sealing
 * @sealed: canonical state is authoritative
 * @active_domain: currently executing domain, or BE_DOMAIN_INVALID
 * @pending_domain: target selected during a switch
 * @selected_vcpu: selected vCPU identity
 * @selected_root: selected modeled HGATP root identity
 * @selected_vmid: selected modeled HGATP VMID
 * @selected_stack: selected trusted transition stack
 * @selected_saved_state: selected saved-register state
 * @selected_saved_state_frame: selected saved-register storage
 * @fence_complete: required translation invalidation has completed
 * @live_registers: current domain's abstract register projection
 * @saved: disjoint saved-register states
 * @cache: modeled G-stage translation cache
 */
struct be_model {
	struct be_platform_inventory inventory;
	struct be_proposal proposal;
	struct be_canonical_state canonical;
	struct be_enforcement_state enforcement;
	enum be_model_phase phase;
	enum be_check_result check_result;
	be_u64 validated_identity;
	be_u64 sealed_identity;
	be_u32 sealed;
	enum be_domain_id active_domain;
	enum be_domain_id pending_domain;
	be_u32 selected_vcpu;
	be_u32 selected_root;
	be_u32 selected_vmid;
	be_u32 selected_stack;
	be_u32 selected_saved_state;
	be_u32 selected_saved_state_frame;
	be_u32 fence_complete;
	struct be_register_file live_registers;
	struct be_saved_register_state saved[BE_MAX_SAVED_STATES];
	struct be_cached_translation cache[BE_MAX_CACHE_ENTRIES];
};

/**
 * be_model_reset - return an executable model to empty state
 * @model: model to reset; NULL is ignored
 */
void be_model_reset(struct be_model *model);

/**
 * be_model_bind_inventory - validate and copy normalized platform resources
 * @model: empty model
 * @inventory: bounded normalized inventory
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED.
 */
enum be_model_result
be_model_bind_inventory(struct be_model *model,
			const struct be_platform_inventory *inventory);

/**
 * be_model_copy_proposal - copy untrusted proposal state
 * @model: inventory-bound model
 * @proposal: bounded proposal to copy
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED.
 */
enum be_model_result
be_model_copy_proposal(struct be_model *model,
		       const struct be_proposal *proposal);

/**
 * be_model_validate - validate and canonicalize the copied proposal
 * @model: proposal-copied model
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED with no canonical output.
 */
enum be_model_result be_model_validate(struct be_model *model);

/**
 * be_model_seal - make validated canonical state authoritative
 * @model: validated model with no producer-published enforcement
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED.
 */
enum be_model_result be_model_seal(struct be_model *model);

/**
 * be_model_derive_roots - derive enforcement solely from sealed state
 * @model: sealed model
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED with no derived output.
 */
enum be_model_result be_model_derive_roots(struct be_model *model);

/**
 * be_model_activate - validate derived state and enter one domain
 * @model: roots-derived model
 * @domain: fixed domain to activate
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED.
 */
enum be_model_result
be_model_activate(struct be_model *model, enum be_domain_id domain);

/**
 * be_model_access - model one G-stage access from the active domain
 * @model: active model
 * @gpa: guest-physical page base
 * @rights: one or more requested R/W/X rights
 *
 * Return: BE_MODEL_ALLOWED, BE_MODEL_DENIED, or terminal BE_MODEL_FAILED.
 */
enum be_model_result
be_model_access(struct be_model *model, be_u64 gpa, be_u32 rights);

/**
 * be_model_write_register - update one live abstract register
 * @model: active model
 * @index: bounded register index
 * @value: arbitrary domain-supplied value
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED.
 */
enum be_model_result
be_model_write_register(struct be_model *model, be_size index, be_u64 value);

/**
 * be_model_read_register - read one live abstract register
 * @model: active model
 * @index: bounded register index
 * @value: output location
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED.
 */
enum be_model_result
be_model_read_register(struct be_model *model, be_size index, be_u64 *value);

/**
 * be_model_read_saved_register - inspect one domain-owned saved register
 * @model: sealed model
 * @domain: saved-state owner
 * @index: bounded register index
 * @value: output location
 *
 * Return: BE_MODEL_OK, or BE_MODEL_FAILED without changing the model.
 */
enum be_model_result
be_model_read_saved_register(const struct be_model *model,
			     enum be_domain_id domain, be_size index,
			     be_u64 *value);

/**
 * be_model_begin_switch - save the source and select target bindings
 * @model: active source-domain model
 * @target: distinct target domain
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED.
 */
enum be_model_result
be_model_begin_switch(struct be_model *model, enum be_domain_id target);

/**
 * be_model_complete_fence - model global HFENCE.GVMA completion
 * @model: switching model after target-root selection
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED.
 */
enum be_model_result be_model_complete_fence(struct be_model *model);

/**
 * be_model_finish_switch - restore target state and permit target entry
 * @model: switching model with completed fence
 *
 * Return: BE_MODEL_OK, or terminal BE_MODEL_FAILED.
 */
enum be_model_result be_model_finish_switch(struct be_model *model);

/**
 * be_model_cache_count - count valid modeled cached translations
 * @model: model to inspect
 *
 * Return: number of valid entries, or zero for NULL.
 */
be_size be_model_cache_count(const struct be_model *model);

/**
 * be_model_phase_name - stable report name for a phase
 * @phase: phase to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_model_phase_name(enum be_model_phase phase);

/**
 * be_model_result_name - stable report name for an operation result
 * @result: result to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_model_result_name(enum be_model_result result);

#endif
