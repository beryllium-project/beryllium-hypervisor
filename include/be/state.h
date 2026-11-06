/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: non-privileged R1 runtime state machine for copied, validated,
 *          sealed, derived, and reported Beryllium mechanism state.
 * Trust:   public control-state contract only. Copied data is non-authoritative
 *          until validation, sealing, and derivation complete successfully.
 * Scope:   accepted R1 non-privileged mechanism only.
 */

#ifndef BE_STATE_H
#define BE_STATE_H

#include <be/manifest.h>

/**
 * enum be_runtime_phase - runtime control states for the R1 mechanism
 * @BE_RUNTIME_PHASE_EMPTY: statically initialized; no copied input is present
 * @BE_RUNTIME_PHASE_INVENTORY_COPIED: inventory copied but not validated
 * @BE_RUNTIME_PHASE_PROPOSAL_COPIED: proposal copied but not validated
 * @BE_RUNTIME_PHASE_VALIDATED: canonical state built but not yet authoritative
 * @BE_RUNTIME_PHASE_SEALED: canonical state sealed and authoritative
 * @BE_RUNTIME_PHASE_DERIVED: abstract enforcement derived from sealed state
 * @BE_RUNTIME_PHASE_FAILED: terminal fail-closed state
 */
enum be_runtime_phase {
	BE_RUNTIME_PHASE_EMPTY = 0,
	BE_RUNTIME_PHASE_INVENTORY_COPIED,
	BE_RUNTIME_PHASE_PROPOSAL_COPIED,
	BE_RUNTIME_PHASE_VALIDATED,
	BE_RUNTIME_PHASE_SEALED,
	BE_RUNTIME_PHASE_DERIVED,
	BE_RUNTIME_PHASE_FAILED,
};

/**
 * enum be_runtime_result - runtime API result
 * @BE_RUNTIME_OK: operation completed successfully
 * @BE_RUNTIME_FAILED: operation failed and entered or retained terminal failure
 */
enum be_runtime_result {
	BE_RUNTIME_OK = 0,
	BE_RUNTIME_FAILED,
};

#define BE_R1_REPORT_SCHEMA_VERSION	1U

/*
 * Fresh runtime storage must use this initializer. No R1 API transitions a
 * failed instance back to an earlier phase. The trusted caller owns the C
 * storage and could overwrite any public object out of band; later platform
 * integration must instead treat a failed instance as discarded and follow
 * the accepted terminal-shutdown path.
 */
#define BE_RUNTIME_INITIALIZER { \
	.phase = BE_RUNTIME_PHASE_EMPTY, \
	.check_result = BE_CHECK_INCOMPLETE, \
}

/**
 * struct be_runtime_report - deterministic R1 runtime summary
 * @schema_version: %BE_R1_REPORT_SCHEMA_VERSION
 * @phase: current runtime phase
 * @check_result: latest checker or integrity result
 * @configuration_id: deterministic reporting-only identity
 * @frame_count: canonical frame count
 * @authority_count: canonical authority count
 * @root_count: derived root count
 * @mapping_count: total derived mapping count across all roots
 * @sealed: canonical state is authoritative
 */
struct be_runtime_report {
	be_u32 schema_version;
	enum be_runtime_phase phase;
	enum be_check_result check_result;
	be_u64 configuration_id;
	be_size frame_count;
	be_size authority_count;
	be_size root_count;
	be_size mapping_count;
	be_u32 sealed;
};

/**
 * struct be_runtime - complete private state of the R1 mechanism
 * @inventory: copied platform inventory
 * @proposal: copied untrusted proposal
 * @canonical: validated canonical state
 * @enforcement: derived abstract enforcement state
 * @phase: current control phase
 * @check_result: latest checker or integrity result
 * @validated_identity: identity retained across validation
 * @sealed_identity: identity retained after sealing
 * @sealed: canonical state is authoritative
 */
struct be_runtime {
	struct be_platform_inventory inventory;
	struct be_proposal proposal;
	struct be_canonical_state canonical;
	struct be_enforcement_state enforcement;
	enum be_runtime_phase phase;
	enum be_check_result check_result;
	be_u64 validated_identity;
	be_u64 sealed_identity;
	be_u32 sealed;
};

/**
 * be_runtime_copy_inventory - copy one bounded inventory without validating it
 * @runtime: empty runtime
 * @inventory: bounded inventory to copy
 *
 * Return: %BE_RUNTIME_OK, or terminal %BE_RUNTIME_FAILED.
 */
enum be_runtime_result
be_runtime_copy_inventory(struct be_runtime *runtime,
			  const struct be_platform_inventory *inventory);

/**
 * be_runtime_copy_proposal - copy one bounded proposal without validating it
 * @runtime: inventory-copied runtime
 * @proposal: bounded proposal to copy
 *
 * Return: %BE_RUNTIME_OK, or terminal %BE_RUNTIME_FAILED.
 */
enum be_runtime_result
be_runtime_copy_proposal(struct be_runtime *runtime,
			 const struct be_proposal *proposal);

/**
 * be_runtime_validate - validate the copied inventory and proposal
 * @runtime: proposal-copied runtime
 *
 * Return: %BE_RUNTIME_OK, or terminal %BE_RUNTIME_FAILED.
 */
enum be_runtime_result be_runtime_validate(struct be_runtime *runtime);

/**
 * be_runtime_seal - make validated canonical state authoritative exactly once
 * @runtime: validated runtime with no prepublished enforcement
 *
 * Return: %BE_RUNTIME_OK, or terminal %BE_RUNTIME_FAILED.
 */
enum be_runtime_result be_runtime_seal(struct be_runtime *runtime);

/**
 * be_runtime_derive - derive abstract enforcement solely from sealed state
 * @runtime: sealed runtime
 *
 * Return: %BE_RUNTIME_OK, or terminal %BE_RUNTIME_FAILED.
 */
enum be_runtime_result be_runtime_derive(struct be_runtime *runtime);

/**
 * be_runtime_report - emit a deterministic report from derived state
 * @runtime: derived runtime
 * @report: output report, zeroed before work
 *
 * Return: %BE_RUNTIME_OK, or terminal %BE_RUNTIME_FAILED.
 */
enum be_runtime_result
be_runtime_report(struct be_runtime *runtime, struct be_runtime_report *report);

/**
 * be_runtime_phase_name - return the stable name of a runtime phase
 * @phase: phase to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_runtime_phase_name(enum be_runtime_phase phase);

/**
 * be_runtime_result_name - return the stable name of a runtime result
 * @result: result to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_runtime_result_name(enum be_runtime_result result);

#endif
