/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: bounded architecture-neutral R5 checked-switch contract for the
 *          fixed management -> protected -> management -> shutdown sequence.
 * Trust:   public R5 mechanism contract. Assembly owns frame transfer, CSR
 *          writes, the local fence, and the no-call restore/SRET tail; this
 *          contract validates only monitor-owned copies and acknowledgements.
 * Scope:   R5 only. No scheduling, restart, rollback, dynamic binding, root or
 *          PTE edit, policy decision, guest SBI, or R6+ behavior.
 */

#ifndef BE_R5_H
#define BE_R5_H

#include <be/r4.h>

/** @BE_R5_REPORT_SCHEMA: deterministic R5 report schema */
#define BE_R5_REPORT_SCHEMA		"be-r5-checked-switch-v1"

/** @BE_R5_SCAUSE_STORE_GUEST_PAGE_FAULT: store/AMO G-stage fault cause */
#define BE_R5_SCAUSE_STORE_GUEST_PAGE_FAULT BE_U64_C(23)

/* Fixed management fixture slots reached only after the accepted R4 prelude. */
/** @BE_R5_MANAGEMENT_RESTORE_PC: saved R4 sepc restored by the return switch */
#define BE_R5_MANAGEMENT_RESTORE_PC	BE_U64_C(0x40010034)
/** @BE_R5_MANAGEMENT_FINAL_EVENT_PC: fixed completion-event slot */
#define BE_R5_MANAGEMENT_FINAL_EVENT_PC	BE_U64_C(0x40010038)
/** @BE_R5_MANAGEMENT_LOOP_PC: linked self-loop that must never execute */
#define BE_R5_MANAGEMENT_LOOP_PC	BE_U64_C(0x4001003c)

/* Fixed protected fixture slots; every slot is one four-byte instruction. */
/** @BE_R5_PROTECTED_ENTRY_PC: first protected VS instruction */
#define BE_R5_PROTECTED_ENTRY_PC	BE_U64_C(0x40011000)
/** @BE_R5_PROTECTED_LOAD_FAULT_PC: denied management-private load slot */
#define BE_R5_PROTECTED_LOAD_FAULT_PC	BE_U64_C(0x40011014)
/** @BE_R5_PROTECTED_LOAD_RESUME_PC: same-domain resume after the denied load */
#define BE_R5_PROTECTED_LOAD_RESUME_PC	BE_U64_C(0x40011018)
/** @BE_R5_PROTECTED_STORE_FAULT_PC: denied shared-store slot */
#define BE_R5_PROTECTED_STORE_FAULT_PC	BE_U64_C(0x40011024)
/** @BE_R5_PROTECTED_STORE_RESUME_PC: same-domain resume after the denied store */
#define BE_R5_PROTECTED_STORE_RESUME_PC	BE_U64_C(0x40011028)
/** @BE_R5_PROTECTED_EVENT_PC: protected switch-event slot */
#define BE_R5_PROTECTED_EVENT_PC	BE_U64_C(0x40011030)
/** @BE_R5_PROTECTED_SAVED_PC: advanced protected sepc, saved but not executed */
#define BE_R5_PROTECTED_SAVED_PC	BE_U64_C(0x40011034)

/* Fixed protected binding. Identifiers are names, never authority. */
/** @BE_R5_PROTECTED_VCPU_ID: protected vCPU identity */
#define BE_R5_PROTECTED_VCPU_ID		2U
/** @BE_R5_PROTECTED_ROOT_ID: immutable protected R2 root identity */
#define BE_R5_PROTECTED_ROOT_ID		102U
/** @BE_R5_PROTECTED_SAVED_STATE_ID: protected saved-state identity */
#define BE_R5_PROTECTED_SAVED_STATE_ID	2U
/** @BE_R5_PROTECTED_GUEST_SP: exclusive top of the protected private page */
#define BE_R5_PROTECTED_GUEST_SP	BE_U64_C(0x40002000)
/** @BE_R5_PROTECTED_TRUSTED_SP: exclusive top of the protected trusted stack */
#define BE_R5_PROTECTED_TRUSTED_SP	BE_U64_C(0x8022a000)
/** @BE_R5_PROTECTED_SAVED_PA: protected saved-state physical page */
#define BE_R5_PROTECTED_SAVED_PA	BE_U64_C(0x8022c000)

/* Fixed denied protected accesses. htval is the ratified shifted GPA. */
/** @BE_R5_PROTECTED_LOAD_DENIED_GVA: denied management-private address */
#define BE_R5_PROTECTED_LOAD_DENIED_GVA	BE_U64_C(0x40000000)
/** @BE_R5_PROTECTED_LOAD_DENIED_GPA: denied management-private guest physical */
#define BE_R5_PROTECTED_LOAD_DENIED_GPA	BE_U64_C(0x40000000)
/** @BE_R5_PROTECTED_LOAD_DENIED_HTVAL: shifted denied load GPA */
#define BE_R5_PROTECTED_LOAD_DENIED_HTVAL BE_U64_C(0x10000000)
/** @BE_R5_SHARED_STORE_DENIED_GVA: denied shared-store address */
#define BE_R5_SHARED_STORE_DENIED_GVA	BE_U64_C(0x40002000)
/** @BE_R5_SHARED_STORE_DENIED_GPA: denied shared-store guest physical */
#define BE_R5_SHARED_STORE_DENIED_GPA	BE_U64_C(0x40002000)
/** @BE_R5_SHARED_STORE_DENIED_HTVAL: shifted denied store GPA */
#define BE_R5_SHARED_STORE_DENIED_HTVAL	BE_U64_C(0x10000800)

/* Fixed backing and event values. */
/** @BE_R5_PROTECTED_PRIVATE_VALUE: protected-private write/readback value */
#define BE_R5_PROTECTED_PRIVATE_VALUE	BE_U64_C(51)
/** @BE_R5_DENIED_STORE_CANDIDATE: value the denied shared store must not commit */
#define BE_R5_DENIED_STORE_CANDIDATE	BE_U64_C(68)
/** @BE_R5_PROTECTED_EVENT_ID: protected switch-event identifier */
#define BE_R5_PROTECTED_EVENT_ID	BE_U64_C(2)
/** @BE_R5_FINAL_EVENT_ID: management completion-event identifier */
#define BE_R5_FINAL_EVENT_ID		BE_U64_C(3)

/** @BE_R5_SHUTDOWN_TYPE: only allowlisted terminal request (shutdown) */
#define BE_R5_SHUTDOWN_TYPE		BE_U64_C(0)
/** @BE_R5_SHUTDOWN_REASON: only allowlisted terminal reason (none) */
#define BE_R5_SHUTDOWN_REASON		BE_U64_C(0)

/** @BE_R5_GPR_SP: frame index of x2, the guest stack pointer */
#define BE_R5_GPR_SP			BE_R4_GPR_INDEX(2U)
/** @BE_R5_GPR_S0: frame index of x8, the retained management readback */
#define BE_R5_GPR_S0			BE_R4_GPR_INDEX(8U)

_Static_assert(BE_R5_GPR_SP < 31U, "R5 stack-pointer index escapes the frame");
_Static_assert(BE_R5_GPR_S0 < 31U, "R5 s0 index escapes the frame");

/**
 * enum be_r5_phase - one-way bounded R5 checked-switch sequence
 * @BE_R5_PHASE_FRESH: nothing imported; only one exact R4 import is admitted
 * @BE_R5_PHASE_IMPORT_R4_COMPLETE: exact in-image R4 COMPLETE state imported
 * @BE_R5_PHASE_PENDING_PROTECTED: unpublished protected target constructed
 * @BE_R5_PHASE_PROTECTED_FENCED: protected root written, fenced, and read back
 * @BE_R5_PHASE_PROTECTED_PUBLISHED_EXPECT_LOAD_FAULT: protected active; the
 *	only accepted next exit is the denied management-private load
 * @BE_R5_PHASE_PROTECTED_EXPECT_SHARED_STORE_FAULT: only the denied shared
 *	store is accepted next
 * @BE_R5_PHASE_PROTECTED_EXPECT_SWITCH_EVENT: only the protected switch event
 *	is accepted next
 * @BE_R5_PHASE_PENDING_MANAGEMENT: unpublished management target constructed
 * @BE_R5_PHASE_MANAGEMENT_FENCED: management root written, fenced, read back
 * @BE_R5_PHASE_MANAGEMENT_PUBLISHED_EXPECT_FINAL_EVENT: management active; only
 *	the completion event is accepted next
 * @BE_R5_PHASE_COMPLETE: completion event validated; only shutdown remains
 * @BE_R5_PHASE_FAILED: terminal; no rollback, retry, or future guest entry
 */
enum be_r5_phase {
	BE_R5_PHASE_FRESH = 0,
	BE_R5_PHASE_IMPORT_R4_COMPLETE,
	BE_R5_PHASE_PENDING_PROTECTED,
	BE_R5_PHASE_PROTECTED_FENCED,
	BE_R5_PHASE_PROTECTED_PUBLISHED_EXPECT_LOAD_FAULT,
	BE_R5_PHASE_PROTECTED_EXPECT_SHARED_STORE_FAULT,
	BE_R5_PHASE_PROTECTED_EXPECT_SWITCH_EVENT,
	BE_R5_PHASE_PENDING_MANAGEMENT,
	BE_R5_PHASE_MANAGEMENT_FENCED,
	BE_R5_PHASE_MANAGEMENT_PUBLISHED_EXPECT_FINAL_EVENT,
	BE_R5_PHASE_COMPLETE,
	BE_R5_PHASE_FAILED,
};

/**
 * enum be_r5_error - stable R5 terminal result classes
 * @BE_R5_ERROR_NONE: no failure
 * @BE_R5_ERROR_NULL: required pointer is absent
 * @BE_R5_ERROR_INVALID_PHASE: invalid order, duplicate, or replayed operation
 * @BE_R5_ERROR_IMPORT: R4 state is not the exact accepted in-image COMPLETE
 * @BE_R5_ERROR_BINDING: active or target binding identity differs
 * @BE_R5_ERROR_PENDING: pending record is absent, stale, or malformed
 * @BE_R5_ERROR_TRUSTED_STACK: trusted-stack identity differs from the binding
 * @BE_R5_ERROR_SAVED_PAGE: monitor saved page differs from the binding
 * @BE_R5_ERROR_HGATP: source HGATP differs from the active binding
 * @BE_R5_ERROR_VS_ORIGIN: exit did not originate in VS under fixed controls
 * @BE_R5_ERROR_VSATP: VS-stage translation is not Bare
 * @BE_R5_ERROR_FRAME_RESERVED: frame reserved word is nonzero
 * @BE_R5_ERROR_FRAME_STATE: frame content is not the exact retained frame
 * @BE_R5_ERROR_FENCE: required V=0 ordering or local fence is unacknowledged
 * @BE_R5_ERROR_TARGET_READBACK: target HGATP write or readback differs
 * @BE_R5_ERROR_TARGET_RESET: target reset state or S-frame preparation differs
 * @BE_R5_ERROR_ENTRY_CONTROLS: hstatus/sstatus entry controls differ
 * @BE_R5_ERROR_PUBLICATION: publication would leave a partial transition
 * @BE_R5_ERROR_HART: observation is not for the fixed hart
 * @BE_R5_ERROR_INTERRUPT: an interrupt was delivered
 * @BE_R5_ERROR_CAUSE: exception cause is not the one expected in this phase
 * @BE_R5_ERROR_PC: exit PC differs from the frozen fixture slot
 * @BE_R5_ERROR_GVA: denied-access GVA differs
 * @BE_R5_ERROR_HTVAL_OVERFLOW: nonzero htval cannot be shifted safely
 * @BE_R5_ERROR_GPA: reconstructed denied-access GPA differs
 * @BE_R5_ERROR_TRAP_METADATA: non-fault trap metadata is nonzero
 * @BE_R5_ERROR_EVENT_ARGS: event register protocol differs
 * @BE_R5_ERROR_BACKING: private/shared backing observations differ
 * @BE_R5_ERROR_SHUTDOWN_RETURNED: allowlisted shutdown reported success but
 *	returned, which is itself terminal
 * @BE_R5_ERROR_SHUTDOWN_REJECTED: firmware rejected the allowlisted shutdown
 *
 * These are diagnostic classes only. None of them creates recovery.
 */
enum be_r5_error {
	BE_R5_ERROR_NONE = 0,
	BE_R5_ERROR_NULL,
	BE_R5_ERROR_INVALID_PHASE,
	BE_R5_ERROR_IMPORT,
	BE_R5_ERROR_BINDING,
	BE_R5_ERROR_PENDING,
	BE_R5_ERROR_TRUSTED_STACK,
	BE_R5_ERROR_SAVED_PAGE,
	BE_R5_ERROR_HGATP,
	BE_R5_ERROR_VS_ORIGIN,
	BE_R5_ERROR_VSATP,
	BE_R5_ERROR_FRAME_RESERVED,
	BE_R5_ERROR_FRAME_STATE,
	BE_R5_ERROR_FENCE,
	BE_R5_ERROR_TARGET_READBACK,
	BE_R5_ERROR_TARGET_RESET,
	BE_R5_ERROR_ENTRY_CONTROLS,
	BE_R5_ERROR_PUBLICATION,
	BE_R5_ERROR_HART,
	BE_R5_ERROR_INTERRUPT,
	BE_R5_ERROR_CAUSE,
	BE_R5_ERROR_PC,
	BE_R5_ERROR_GVA,
	BE_R5_ERROR_HTVAL_OVERFLOW,
	BE_R5_ERROR_GPA,
	BE_R5_ERROR_TRAP_METADATA,
	BE_R5_ERROR_EVENT_ARGS,
	BE_R5_ERROR_BACKING,
	BE_R5_ERROR_SHUTDOWN_RETURNED,
	BE_R5_ERROR_SHUTDOWN_REJECTED,
};

/**
 * enum be_r5_direction - the only two accepted checked-switch directions
 * @BE_R5_DIRECTION_NONE: no transition is in flight
 * @BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED: first checked switch
 * @BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT: return switch
 */
enum be_r5_direction {
	BE_R5_DIRECTION_NONE = 0,
	BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
	BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
};

/**
 * enum be_r5_frame_mode - how the target frame is obtained
 * @BE_R5_FRAME_MODE_NONE: no transition is in flight
 * @BE_R5_FRAME_MODE_INITIAL: monitor-created initial protected frame
 * @BE_R5_FRAME_MODE_SAVED: exact retained management frame
 */
enum be_r5_frame_mode {
	BE_R5_FRAME_MODE_NONE = 0,
	BE_R5_FRAME_MODE_INITIAL,
	BE_R5_FRAME_MODE_SAVED,
};

/**
 * enum be_r5_exit_class - accepted serviceable R5 guest exits
 * @BE_R5_EXIT_NONE: no serviceable exit
 * @BE_R5_EXIT_PROTECTED_DENIED_LOAD: denied management-private load
 * @BE_R5_EXIT_PROTECTED_DENIED_SHARED_STORE: denied shared store
 * @BE_R5_EXIT_PROTECTED_SWITCH_EVENT: protected return-switch event
 * @BE_R5_EXIT_MANAGEMENT_FINAL_EVENT: management completion event
 */
enum be_r5_exit_class {
	BE_R5_EXIT_NONE = 0,
	BE_R5_EXIT_PROTECTED_DENIED_LOAD,
	BE_R5_EXIT_PROTECTED_DENIED_SHARED_STORE,
	BE_R5_EXIT_PROTECTED_SWITCH_EVENT,
	BE_R5_EXIT_MANAGEMENT_FINAL_EVENT,
};

/**
 * enum be_r5_action - complete R5 dispositions
 * @BE_R5_ACTION_NONE: no disposition has been produced
 * @BE_R5_ACTION_RESUME_SAME_DOMAIN_FULL_FRAME: restore the complete frame under
 *	the unchanged active binding and resume at the advanced frame sepc
 * @BE_R5_ACTION_SWITCH_TO_MANAGEMENT: the protected event was serviced; the
 *	return transaction may now construct its pending record
 * @BE_R5_ACTION_ENTER_TARGET: published target may be entered by the no-call
 *	assembly tail
 * @BE_R5_ACTION_SHUTDOWN: request exactly the allowlisted terminal shutdown
 * @BE_R5_ACTION_TERMINAL: no restore, entry, or retry is authorized
 */
enum be_r5_action {
	BE_R5_ACTION_NONE = 0,
	BE_R5_ACTION_RESUME_SAME_DOMAIN_FULL_FRAME,
	BE_R5_ACTION_SWITCH_TO_MANAGEMENT,
	BE_R5_ACTION_ENTER_TARGET,
	BE_R5_ACTION_SHUTDOWN,
	BE_R5_ACTION_TERMINAL,
};

/**
 * struct be_r5_observation - monitor-owned facts sampled for one exit
 * @hart_id: current hart
 * @active: caller's current active binding
 * @current_hgatp: HGATP readback for the source domain
 * @hstatus: hypervisor status readback; proves VS origin and fixed controls
 * @vsatp: VS-stage translation readback, required Bare
 * @trusted_sp: trusted-stack identity actually in use for this exit
 * @saved_state_pa: monitor saved page the platform used for this frame
 * @management_private_value: management-private backing observation
 * @protected_private_value: protected-private backing observation
 * @shared_value: shared backing observation
 *
 * Every field is monitor-sampled. No guest pointer, guest register, or fault
 * address may select monitor context or storage.
 */
struct be_r5_observation {
	be_u64 hart_id;
	struct be_r3_binding active;
	be_u64 current_hgatp;
	be_u64 hstatus;
	be_u64 vsatp;
	be_u64 trusted_sp;
	be_u64 saved_state_pa;
	be_u64 management_private_value;
	be_u64 protected_private_value;
	be_u64 shared_value;
};

/**
 * struct be_r5_pending - exactly one complete unpublished target record
 * @direction: accepted switch direction
 * @frame_mode: how the target frame is obtained
 * @source: exact active binding retained as the transaction source
 * @target: complete unpublished target binding
 */
struct be_r5_pending {
	enum be_r5_direction direction;
	enum be_r5_frame_mode frame_mode;
	struct be_r3_binding source;
	struct be_r3_binding target;
};

/**
 * struct be_r5_fence_ack - ordered root-write acknowledgement
 * @source_hgatp: HGATP observed before the target write
 * @hgatp_written: value the platform wrote while V=0
 * @hgatp_readback: value read after the local HFENCE.GVMA
 * @virtualization_off: one only when the write happened with V=0
 * @fence_completed: one only after the local all-GPA/all-VMID fence
 *
 * An HGATP write alone supplies no ordering: both acknowledgements are
 * required before any pre-publication state may advance.
 */
struct be_r5_fence_ack {
	be_u64 source_hgatp;
	be_u64 hgatp_written;
	be_u64 hgatp_readback;
	be_u32 virtualization_off;
	be_u32 fence_completed;
};

/**
 * struct be_r5_entry_state - verified target reset state before publication
 * @hgatp: HGATP readback immediately before publication
 * @hstatus: required hypervisor controls including SPV and VTVM
 * @sstatus: required supervisor controls; exactly SPP within the control mask
 * @vsatp: VS-stage translation, required Bare
 * @vstvec: target VS trap vector, required reset
 * @vsepc: target VS exception PC, required reset
 * @vscause: target VS cause, required reset
 * @vstval: target VS trap value, required reset
 * @trusted_sp: trusted-stack identity prepared for the target
 * @saved_state_pa: monitor saved page selected for the target restore frame
 *
 * The reset VS readback is taken before the assembly tail restores the target
 * frame, so no residual source VS state can survive a checked switch.
 */
struct be_r5_entry_state {
	be_u64 hgatp;
	be_u64 hstatus;
	be_u64 sstatus;
	be_u64 vsatp;
	be_u64 vstvec;
	be_u64 vsepc;
	be_u64 vscause;
	be_u64 vstval;
	be_u64 trusted_sp;
	be_u64 saved_state_pa;
};

/**
 * struct be_r5_result - transactionally produced serviceable-exit decision
 * @action: complete disposition
 * @exit_class: accepted exit classification
 * @advanced_pc: exact sepc written into the saved frame, or zero when the
 *	frame is deliberately left unchanged
 * @shutdown_type: allowlisted terminal request, set only for shutdown
 * @shutdown_reason: allowlisted terminal reason, set only for shutdown
 * @active: unchanged binding of the domain that exited
 */
struct be_r5_result {
	enum be_r5_action action;
	enum be_r5_exit_class exit_class;
	be_u64 advanced_pc;
	be_u64 shutdown_type;
	be_u64 shutdown_reason;
	struct be_r3_binding active;
};

/**
 * struct be_r5_transition - published checked-switch entry parameters
 * @action: %BE_R5_ACTION_ENTER_TARGET after successful publication
 * @direction: published switch direction
 * @frame_mode: frame mode used for the target
 * @active: published target binding
 * @entry_pc: sepc of the prepared target frame
 * @entry_sp: guest stack pointer of the prepared target frame
 * @trusted_sp: trusted stack owned by the target domain
 * @saved_state_pa: monitor saved page holding the target restore frame
 */
struct be_r5_transition {
	enum be_r5_action action;
	enum be_r5_direction direction;
	enum be_r5_frame_mode frame_mode;
	struct be_r3_binding active;
	be_u64 entry_pc;
	be_u64 entry_sp;
	be_u64 trusted_sp;
	be_u64 saved_state_pa;
};

/**
 * struct be_r5_state - bounded R5 authority and sequence state
 * @phase: one-way R5 phase
 * @error: sticky first terminal error
 * @action: latest complete disposition, or terminal after failure
 * @shutdown_detail: retained SBI classification when shutdown returned
 * @active: published binding of the currently authorized domain
 * @pending: exactly one unpublished target record, or cleared
 * @management_frame: exact imported R4 frame, retained unchanged for the
 *	return switch and compared byte-for-byte before publication
 * @configuration_id: accepted configuration identity
 * @management_hgatp: accepted management HGATP
 * @protected_hgatp: accepted protected HGATP
 * @protected_saved_pc: advanced protected sepc saved by the switch event
 * @switch_requested: one only after the validated protected switch event
 * @exit_count: serviceable exits, bounded to four
 * @switch_count: published checked switches, bounded to two
 */
struct be_r5_state {
	enum be_r5_phase phase;
	enum be_r5_error error;
	enum be_r5_action action;
	enum be_r3_error shutdown_detail;
	struct be_r3_binding active;
	struct be_r5_pending pending;
	struct be_r4_frame management_frame;
	be_u64 configuration_id;
	be_u64 management_hgatp;
	be_u64 protected_hgatp;
	be_u64 protected_saved_pc;
	be_u32 switch_requested;
	be_u32 exit_count;
	be_u32 switch_count;
};

#define BE_R5_STATE_INITIALIZER { \
	.phase = BE_R5_PHASE_FRESH, \
	.error = BE_R5_ERROR_NONE, \
	.action = BE_R5_ACTION_NONE, \
	.shutdown_detail = BE_R3_ERROR_NONE, \
}

/**
 * be_r5_import_r4_complete - import the exact in-image R4 COMPLETE state
 * @state: fresh R5 state
 * @r4: R4 state that reached COMPLETE in this image
 * @frame: advanced management frame saved by the R4 event trap
 * @observation: exact current binding, controls, and backing observations
 *
 * This is the only R4-to-R5 seam. It admits no earlier-image, partial, failed,
 * or synthetic execution state, and retains @frame unchanged for the return
 * switch. R5 suppresses the R4 same-management restore decision.
 *
 * Return: %BE_R5_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r5_error
be_r5_import_r4_complete(struct be_r5_state *state,
			 const struct be_r4_state *r4,
			 const struct be_r4_frame *frame,
			 const struct be_r5_observation *observation);

/**
 * be_r5_prepare_pending - construct exactly one unpublished target record
 * @state: imported state, or a state whose protected switch event was serviced
 * @direction: accepted direction for the current phase
 * @pending: complete pending record written only on success
 *
 * The target binding is derived only from fixed monitor constants and the
 * checked source binding; no caller may propose or attenuate it.
 *
 * Return: %BE_R5_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r5_error
be_r5_prepare_pending(struct be_r5_state *state,
		      enum be_r5_direction direction,
		      struct be_r5_pending *pending);

/**
 * be_r5_note_target_fenced - accept the ordered write/fence/readback evidence
 * @state: state holding one complete pending record
 * @ack: exact source, written, fenced, and read-back root evidence
 *
 * Return: %BE_R5_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r5_error
be_r5_note_target_fenced(struct be_r5_state *state,
			 const struct be_r5_fence_ack *ack);

/**
 * be_r5_publish_target - verify target reset state, prepare the S-frame, and
 *			  atomically publish the target
 * @state: fenced state holding one complete pending record
 * @entry: verified target reset state and entry controls
 * @target_frame: monitor saved page content for the target; written with the
 *	monitor-created initial frame, or compared with the retained frame
 * @transition: entry parameters written only after successful publication
 *
 * Publication is the last restricted-C step: it makes the target active and
 * clears pending in one transition. No target instruction may execute before
 * it, and any later trap before SRET is terminal.
 *
 * Return: %BE_R5_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r5_error
be_r5_publish_target(struct be_r5_state *state,
		     const struct be_r5_entry_state *entry,
		     struct be_r4_frame *target_frame,
		     struct be_r5_transition *transition);

/**
 * be_r5_handle_exit - validate and service exactly one fixed R5 guest exit
 * @state: active R5 sequence state
 * @frame: complete monitor-owned saved frame for the running domain
 * @observation: exact current binding, controls, and backing observations
 * @result: decision written only after complete successful validation
 *
 * On success only frame.sepc is deliberately changed, and the completion event
 * leaves the frame untouched because no guest entry follows it. No failed
 * validation changes @frame or @result.
 *
 * Return: %BE_R5_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r5_error
be_r5_handle_exit(struct be_r5_state *state, struct be_r4_frame *frame,
		  const struct be_r5_observation *observation,
		  struct be_r5_result *result);

/**
 * be_r5_note_shutdown_returned - classify a terminal shutdown that returned
 * @state: complete R5 state that requested the allowlisted shutdown
 * @sbi_error: signed firmware error returned in a0
 *
 * A successful allowlisted shutdown is non-returning, so any return is
 * terminal. The firmware classification is retained for diagnosis only.
 *
 * Return: retained terminal error; never %BE_R5_ERROR_NONE.
 */
enum be_r5_error
be_r5_note_shutdown_returned(struct be_r5_state *state, long sbi_error);

/**
 * be_r5_fail - enter terminal R5 failure and remove sequence authority
 * @state: R5 state, if available
 * @error: nonzero first error to retain
 *
 * Return: retained terminal error.
 */
enum be_r5_error be_r5_fail(struct be_r5_state *state, enum be_r5_error error);

/** be_r5_phase_name - return a stable phase name */
const char *be_r5_phase_name(enum be_r5_phase phase);
/** be_r5_error_name - return a stable error name */
const char *be_r5_error_name(enum be_r5_error error);
/** be_r5_direction_name - return a stable direction name */
const char *be_r5_direction_name(enum be_r5_direction direction);
/** be_r5_frame_mode_name - return a stable frame-mode name */
const char *be_r5_frame_mode_name(enum be_r5_frame_mode frame_mode);
/** be_r5_exit_class_name - return a stable exit-class name */
const char *be_r5_exit_class_name(enum be_r5_exit_class exit_class);
/** be_r5_action_name - return a stable action name */
const char *be_r5_action_name(enum be_r5_action action);

#endif
