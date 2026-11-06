/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: bounded architecture-neutral R4 trap-frame, classification, and
 *          same-management full-frame resume contract.
 * Trust:   public R4 mechanism contract. Assembly owns frame transfer; the
 *          restricted-C mechanism validates only monitor-owned copies.
 * Scope:   R4 only. No switching, protected entry, HGATP writes, or fences.
 */

#ifndef BE_R4_H
#define BE_R4_H

#include <be/r3.h>

#define BE_R4_INTERRUPT_BIT		(BE_U64_C(1) << 63)
#define BE_R4_SCAUSE_VS_ECALL		BE_U64_C(10)
#define BE_R4_SCAUSE_LOAD_GUEST_PAGE_FAULT BE_U64_C(21)
#define BE_R4_SCAUSE_VIRTUAL_INSTRUCTION	BE_U64_C(22)

#define BE_R4_FAULT_PC			BE_U64_C(0x40010014)
#define BE_R4_EVENT_PC			BE_U64_C(0x40010030)
#define BE_R4_DENIED_GVA		BE_U64_C(0x40001000)
#define BE_R4_DENIED_GPA		BE_U64_C(0x40001000)
#define BE_R4_DENIED_HTVAL		BE_U64_C(0x10000400)
#define BE_R4_INSTRUCTION_SIZE		BE_U64_C(4)

#define BE_R4_PRIVATE_VALUE		BE_U64_C(17)
#define BE_R4_SHARED_VALUE		BE_U64_C(34)
#define BE_R4_EVENT_ID			BE_U64_C(1)
#define BE_R4_EVENT_VERSION_FUNCTION	BE_U64_C(0)

#define BE_R4_GPR_INDEX(register_number) ((register_number) - 1U)
#define BE_R4_GPR_A0			BE_R4_GPR_INDEX(10U)
#define BE_R4_GPR_A1			BE_R4_GPR_INDEX(11U)
#define BE_R4_GPR_A6			BE_R4_GPR_INDEX(16U)
#define BE_R4_GPR_A7			BE_R4_GPR_INDEX(17U)

/**
 * struct be_r4_frame - exact monitor-owned R4 saved frame
 * @gpr: x1-x31 in architectural order; element xN-1 contains xN
 * @vstvec: saved VS trap-vector CSR
 * @vsepc: saved VS exception PC CSR
 * @vscause: saved VS cause CSR
 * @vstval: saved VS trap-value CSR
 * @scause: HS trap cause captured on VS exit
 * @sepc: HS trap PC captured on VS exit and resume target on return
 * @stval: HS trap value captured on VS exit
 * @htval: hypervisor trap value captured on VS exit
 * @reserved: required zero; fixed space for ABI integrity, not future authority
 *
 * Reset controls and htinst are deliberately excluded. Assembly copies this
 * complete 320-byte frame to monitor-owned saved-state storage. Active binding
 * identities are retained separately in struct be_r4_state.
 */
struct be_r4_frame {
	be_u64 gpr[31];
	be_u64 vstvec;
	be_u64 vsepc;
	be_u64 vscause;
	be_u64 vstval;
	be_u64 scause;
	be_u64 sepc;
	be_u64 stval;
	be_u64 htval;
	be_u64 reserved;
};

#define BE_R4_ASSERT_GPR_OFFSET(number) \
	_Static_assert(__builtin_offsetof(struct be_r4_frame, gpr) + \
		       ((number) - 1U) * sizeof(be_u64) == \
		       ((number) - 1U) * 8U, \
		       "R4 frame x" #number " offset differs")

BE_R4_ASSERT_GPR_OFFSET(1);
BE_R4_ASSERT_GPR_OFFSET(2);
BE_R4_ASSERT_GPR_OFFSET(3);
BE_R4_ASSERT_GPR_OFFSET(4);
BE_R4_ASSERT_GPR_OFFSET(5);
BE_R4_ASSERT_GPR_OFFSET(6);
BE_R4_ASSERT_GPR_OFFSET(7);
BE_R4_ASSERT_GPR_OFFSET(8);
BE_R4_ASSERT_GPR_OFFSET(9);
BE_R4_ASSERT_GPR_OFFSET(10);
BE_R4_ASSERT_GPR_OFFSET(11);
BE_R4_ASSERT_GPR_OFFSET(12);
BE_R4_ASSERT_GPR_OFFSET(13);
BE_R4_ASSERT_GPR_OFFSET(14);
BE_R4_ASSERT_GPR_OFFSET(15);
BE_R4_ASSERT_GPR_OFFSET(16);
BE_R4_ASSERT_GPR_OFFSET(17);
BE_R4_ASSERT_GPR_OFFSET(18);
BE_R4_ASSERT_GPR_OFFSET(19);
BE_R4_ASSERT_GPR_OFFSET(20);
BE_R4_ASSERT_GPR_OFFSET(21);
BE_R4_ASSERT_GPR_OFFSET(22);
BE_R4_ASSERT_GPR_OFFSET(23);
BE_R4_ASSERT_GPR_OFFSET(24);
BE_R4_ASSERT_GPR_OFFSET(25);
BE_R4_ASSERT_GPR_OFFSET(26);
BE_R4_ASSERT_GPR_OFFSET(27);
BE_R4_ASSERT_GPR_OFFSET(28);
BE_R4_ASSERT_GPR_OFFSET(29);
BE_R4_ASSERT_GPR_OFFSET(30);
BE_R4_ASSERT_GPR_OFFSET(31);

_Static_assert(__builtin_offsetof(struct be_r4_frame, vstvec) == 248U,
	       "R4 frame vstvec offset differs");
_Static_assert(__builtin_offsetof(struct be_r4_frame, vsepc) == 256U,
	       "R4 frame vsepc offset differs");
_Static_assert(__builtin_offsetof(struct be_r4_frame, vscause) == 264U,
	       "R4 frame vscause offset differs");
_Static_assert(__builtin_offsetof(struct be_r4_frame, vstval) == 272U,
	       "R4 frame vstval offset differs");
_Static_assert(__builtin_offsetof(struct be_r4_frame, scause) == 280U,
	       "R4 frame scause offset differs");
_Static_assert(__builtin_offsetof(struct be_r4_frame, sepc) == 288U,
	       "R4 frame sepc offset differs");
_Static_assert(__builtin_offsetof(struct be_r4_frame, stval) == 296U,
	       "R4 frame stval offset differs");
_Static_assert(__builtin_offsetof(struct be_r4_frame, htval) == 304U,
	       "R4 frame htval offset differs");
_Static_assert(__builtin_offsetof(struct be_r4_frame, reserved) == 312U,
	       "R4 frame reserved offset differs");
_Static_assert(sizeof(struct be_r4_frame) == 320U,
	       "R4 frame size differs");
_Static_assert(_Alignof(struct be_r4_frame) == 8U,
	       "R4 frame alignment differs");

#undef BE_R4_ASSERT_GPR_OFFSET

/**
 * enum be_r4_phase - one-way bounded R4 sequence
 * @BE_R4_PHASE_EMPTY: no accepted R3 state has been imported
 * @BE_R4_PHASE_EXPECT_FAULT: management is running before the denied load
 * @BE_R4_PHASE_EXPECT_EVENT: denied load was serviced; private event is next
 * @BE_R4_PHASE_COMPLETE: exactly one private event was serviced
 * @BE_R4_PHASE_FAILED: terminal failure; all sequence authority is removed
 */
enum be_r4_phase {
	BE_R4_PHASE_EMPTY = 0,
	BE_R4_PHASE_EXPECT_FAULT,
	BE_R4_PHASE_EXPECT_EVENT,
	BE_R4_PHASE_COMPLETE,
	BE_R4_PHASE_FAILED,
};

/**
 * enum be_r4_error - stable R4 terminal result classes
 * @BE_R4_ERROR_NONE: no failure
 * @BE_R4_ERROR_NULL: required pointer is absent
 * @BE_R4_ERROR_INVALID_PHASE: begin/trap is out of sequence
 * @BE_R4_ERROR_R3_STATE: R3 state is not the exact accepted entry state
 * @BE_R4_ERROR_BINDING: active binding identity differs
 * @BE_R4_ERROR_FRAME_RESERVED: frame reserved word is nonzero
 * @BE_R4_ERROR_INTERRUPT: an interrupt was delivered
 * @BE_R4_ERROR_CAUSE: exception cause is not the one expected in this phase
 * @BE_R4_ERROR_HART: trap observation is not for the fixed hart
 * @BE_R4_ERROR_HGATP: current HGATP differs from the active management root
 * @BE_R4_ERROR_PC: trap PC differs from the fixed sequence
 * @BE_R4_ERROR_GVA: denied-load GVA differs
 * @BE_R4_ERROR_HTVAL_OVERFLOW: nonzero htval cannot be shifted safely
 * @BE_R4_ERROR_GPA: reconstructed denied-load GPA differs
 * @BE_R4_ERROR_TRAP_METADATA: non-fault trap metadata is nonzero
 * @BE_R4_ERROR_BACKING: private/protected/shared observations differ
 * @BE_R4_ERROR_EVENT_ARGS: private-event register protocol differs
 */
enum be_r4_error {
	BE_R4_ERROR_NONE = 0,
	BE_R4_ERROR_NULL,
	BE_R4_ERROR_INVALID_PHASE,
	BE_R4_ERROR_R3_STATE,
	BE_R4_ERROR_BINDING,
	BE_R4_ERROR_FRAME_RESERVED,
	BE_R4_ERROR_INTERRUPT,
	BE_R4_ERROR_CAUSE,
	BE_R4_ERROR_HART,
	BE_R4_ERROR_HGATP,
	BE_R4_ERROR_PC,
	BE_R4_ERROR_GVA,
	BE_R4_ERROR_HTVAL_OVERFLOW,
	BE_R4_ERROR_GPA,
	BE_R4_ERROR_TRAP_METADATA,
	BE_R4_ERROR_BACKING,
	BE_R4_ERROR_EVENT_ARGS,
};

/**
 * enum be_r4_trap_class - accepted serviceable R4 trap classes
 * @BE_R4_TRAP_NONE: no serviceable trap
 * @BE_R4_TRAP_EXPECTED_DENIED_LOAD: fixed management denied-load fault
 * @BE_R4_TRAP_PRIVATE_EVENT: fixed management private-event ECALL
 */
enum be_r4_trap_class {
	BE_R4_TRAP_NONE = 0,
	BE_R4_TRAP_EXPECTED_DENIED_LOAD,
	BE_R4_TRAP_PRIVATE_EVENT,
};

/**
 * enum be_r4_decision - complete R4 disposition
 * @BE_R4_DECISION_NONE: no disposition has been produced
 * @BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME: restore the complete
 *	frame under the unchanged management binding and resume at frame.sepc
 * @BE_R4_DECISION_TERMINAL: no restore or guest entry is authorized
 */
enum be_r4_decision {
	BE_R4_DECISION_NONE = 0,
	BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME,
	BE_R4_DECISION_TERMINAL,
};

/**
 * struct be_r4_observation - monitor-owned facts sampled for one trap
 * @hart_id: current hart
 * @active: caller's current active binding
 * @current_hgatp: current HGATP CSR readback; R4 never writes it
 * @private_value: management-private backing observation
 * @protected_value: protected-private backing observation
 * @shared_value: shared backing observation
 */
struct be_r4_observation {
	be_u64 hart_id;
	struct be_r3_binding active;
	be_u64 current_hgatp;
	be_u64 private_value;
	be_u64 protected_value;
	be_u64 shared_value;
};

/**
 * struct be_r4_result - transactionally produced serviceable-trap decision
 * @decision: complete disposition
 * @trap_class: accepted trap classification
 * @resume_pc: exact post-instruction resume PC
 * @active: unchanged binding under which the full frame is restored
 */
struct be_r4_result {
	enum be_r4_decision decision;
	enum be_r4_trap_class trap_class;
	be_u64 resume_pc;
	struct be_r3_binding active;
};

/**
 * struct be_r4_state - bounded R4 authority and sequence state
 * @phase: one-way R4 phase
 * @error: sticky first terminal error
 * @decision: latest complete resume decision, or terminal after failure
 * @active: unchanged accepted management binding
 * @configuration_id: accepted configuration identity
 * @management_hgatp: accepted management HGATP
 * @protected_hgatp: accepted protected HGATP, retained for exact import
 * @fault_seen: one only after the denied load is serviced
 * @event_seen: one only after the private event is serviced
 * @trap_count: number of serviceable traps, bounded to two
 */
struct be_r4_state {
	enum be_r4_phase phase;
	enum be_r4_error error;
	enum be_r4_decision decision;
	struct be_r3_binding active;
	be_u64 configuration_id;
	be_u64 management_hgatp;
	be_u64 protected_hgatp;
	be_u32 fault_seen;
	be_u32 event_seen;
	be_u32 trap_count;
};

#define BE_R4_STATE_INITIALIZER { \
	.phase = BE_R4_PHASE_EMPTY, \
	.error = BE_R4_ERROR_NONE, \
	.decision = BE_R4_DECISION_NONE, \
}

/**
 * be_r4_begin - import the exact accepted R3 management-entry state
 * @state: fresh R4 state
 * @r3: accepted R3 state at ENTRY_ARMED
 *
 * Return: %BE_R4_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r4_error
be_r4_begin(struct be_r4_state *state, const struct be_r3_state *r3);

/**
 * be_r4_handle_trap - validate and service one fixed R4 trap
 * @state: active R4 sequence state
 * @frame: complete monitor-owned saved frame
 * @observation: exact current binding and backing observations
 * @result: decision written only after complete successful validation
 *
 * On success, only frame.sepc is deliberately changed. No failed validation
 * changes @frame or @result; the R4 state becomes terminal and loses authority.
 *
 * Return: %BE_R4_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r4_error
be_r4_handle_trap(struct be_r4_state *state, struct be_r4_frame *frame,
		  const struct be_r4_observation *observation,
		  struct be_r4_result *result);

/**
 * be_r4_fail - enter terminal R4 failure and remove sequence authority
 * @state: R4 state, if available
 * @error: nonzero first error to retain
 *
 * Return: retained terminal error.
 */
enum be_r4_error
be_r4_fail(struct be_r4_state *state, enum be_r4_error error);

/** be_r4_phase_name - return a stable phase name */
const char *be_r4_phase_name(enum be_r4_phase phase);
/** be_r4_error_name - return a stable error name */
const char *be_r4_error_name(enum be_r4_error error);
/** be_r4_trap_class_name - return a stable trap-class name */
const char *be_r4_trap_class_name(enum be_r4_trap_class trap_class);
/** be_r4_decision_name - return a stable decision name */
const char *be_r4_decision_name(enum be_r4_decision decision);

#endif
