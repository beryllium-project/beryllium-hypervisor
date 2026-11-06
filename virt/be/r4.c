// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: transactional R4 trap classification and same-management
 *          full-frame resume decisions for the fixed two-trap sequence.
 * Trust:   restricted-C mechanism only. It accesses no CSR, issues no fence,
 *          switches no root, and enters no guest.
 * Scope:   R4 only. Protected execution and every R5 behavior are excluded.
 */
#include <be/r4.h>

#define BE_R4_HTVAL_SHIFT_MAX	BE_U64_C(0x3fffffffffffffff)

static int binding_equal(const struct be_r3_binding *left,
			 const struct be_r3_binding *right)
{
	return left->domain == right->domain &&
	       left->vcpu_id == right->vcpu_id &&
	       left->root_id == right->root_id &&
	       left->vmid == right->vmid &&
	       left->hgatp == right->hgatp &&
	       left->guest_pc == right->guest_pc &&
	       left->guest_sp == right->guest_sp &&
	       left->trusted_sp == right->trusted_sp &&
	       left->saved_state_id == right->saved_state_id &&
	       left->saved_state_pa == right->saved_state_pa &&
	       left->vsatp == right->vsatp &&
	       left->published == right->published;
}

static int binding_zero(const struct be_r3_binding *binding)
{
	return binding->domain == BE_DOMAIN_INVALID &&
	       binding->vcpu_id == 0U &&
	       binding->root_id == 0U &&
	       binding->vmid == 0U &&
	       binding->hgatp == 0U &&
	       binding->guest_pc == 0U &&
	       binding->guest_sp == 0U &&
	       binding->trusted_sp == 0U &&
	       binding->saved_state_id == 0U &&
	       binding->saved_state_pa == 0U &&
	       binding->vsatp == 0U &&
	       binding->published == 0U;
}

static int exact_management_binding(const struct be_r3_binding *binding)
{
	return binding->domain == BE_DOMAIN_MANAGEMENT &&
	       binding->vcpu_id == 1U &&
	       binding->root_id == 101U &&
	       binding->vmid == 0U &&
	       binding->hgatp == BE_R3_MANAGEMENT_HGATP &&
	       binding->guest_pc == BE_R3_INITIAL_GUEST_PC &&
	       binding->guest_sp == BE_R3_INITIAL_GUEST_SP &&
	       binding->trusted_sp == BE_R3_INITIAL_TRUSTED_SP &&
	       binding->saved_state_id == 1U &&
	       binding->saved_state_pa == BE_R3_MANAGEMENT_SAVED_PA &&
	       binding->vsatp == 0U &&
	       binding->published == 1U;
}

static int exact_r3_state(const struct be_r3_state *r3)
{
	return r3->phase == BE_R3_PHASE_ENTRY_ARMED &&
	       r3->error == BE_R3_ERROR_NONE &&
	       r3->configuration_id == BE_R3_CONFIGURATION_ID &&
	       r3->management_hgatp == BE_R3_MANAGEMENT_HGATP &&
	       r3->protected_hgatp == BE_R3_PROTECTED_HGATP &&
	       binding_zero(&r3->pending) &&
	       exact_management_binding(&r3->active);
}

enum be_r4_error
be_r4_fail(struct be_r4_state *state, enum be_r4_error error)
{
	if (state != (struct be_r4_state *)0 &&
	    state->phase == BE_R4_PHASE_FAILED)
		return state->error;
	if (error == BE_R4_ERROR_NONE)
		error = BE_R4_ERROR_INVALID_PHASE;
	if (state != (struct be_r4_state *)0) {
		state->active = (struct be_r3_binding){ 0 };
		state->configuration_id = 0U;
		state->management_hgatp = 0U;
		state->protected_hgatp = 0U;
		state->fault_seen = 0U;
		state->event_seen = 0U;
		state->trap_count = 0U;
		state->decision = BE_R4_DECISION_TERMINAL;
		state->phase = BE_R4_PHASE_FAILED;
		state->error = error;
	}
	return error;
}

enum be_r4_error
be_r4_begin(struct be_r4_state *state, const struct be_r3_state *r3)
{
	if (state == (struct be_r4_state *)0)
		return BE_R4_ERROR_NULL;
	if (state->phase == BE_R4_PHASE_FAILED)
		return state->error;
	if (state->phase != BE_R4_PHASE_EMPTY)
		return be_r4_fail(state, BE_R4_ERROR_INVALID_PHASE);
	if (r3 == (const struct be_r3_state *)0)
		return be_r4_fail(state, BE_R4_ERROR_NULL);
	if (!exact_r3_state(r3))
		return be_r4_fail(state, BE_R4_ERROR_R3_STATE);

	state->active = r3->active;
	state->configuration_id = r3->configuration_id;
	state->management_hgatp = r3->management_hgatp;
	state->protected_hgatp = r3->protected_hgatp;
	state->fault_seen = 0U;
	state->event_seen = 0U;
	state->trap_count = 0U;
	state->error = BE_R4_ERROR_NONE;
	state->decision = BE_R4_DECISION_NONE;
	state->phase = BE_R4_PHASE_EXPECT_FAULT;
	return BE_R4_ERROR_NONE;
}

static enum be_r4_error
validate_common(const struct be_r4_state *state,
		const struct be_r4_frame *frame,
		const struct be_r4_observation *observation)
{
	if (frame->reserved != 0U)
		return BE_R4_ERROR_FRAME_RESERVED;
	if (observation->hart_id != BE_CONFIGURATION_HART_ID)
		return BE_R4_ERROR_HART;
	if (state->configuration_id != BE_R3_CONFIGURATION_ID ||
	    state->management_hgatp != BE_R3_MANAGEMENT_HGATP ||
	    state->protected_hgatp != BE_R3_PROTECTED_HGATP)
		return BE_R4_ERROR_R3_STATE;
	if (!exact_management_binding(&state->active) ||
	    !binding_equal(&state->active, &observation->active))
		return BE_R4_ERROR_BINDING;
	if (observation->current_hgatp != state->active.hgatp)
		return BE_R4_ERROR_HGATP;
	if ((frame->scause & BE_R4_INTERRUPT_BIT) != 0U)
		return BE_R4_ERROR_INTERRUPT;
	return BE_R4_ERROR_NONE;
}

static enum be_r4_error
validate_fault(const struct be_r4_frame *frame,
	       const struct be_r4_observation *observation)
{
	be_u64 reconstructed;
	be_u64 low_bits;

	if (frame->scause != BE_R4_SCAUSE_LOAD_GUEST_PAGE_FAULT)
		return BE_R4_ERROR_CAUSE;
	if (frame->sepc != BE_R4_FAULT_PC)
		return BE_R4_ERROR_PC;
	if (frame->stval != BE_R4_DENIED_GVA)
		return BE_R4_ERROR_GVA;
	if (frame->htval != 0U) {
		if (frame->htval > BE_R4_HTVAL_SHIFT_MAX)
			return BE_R4_ERROR_HTVAL_OVERFLOW;
		reconstructed = frame->htval << 2;
		low_bits = frame->stval & BE_U64_C(3);
		if (reconstructed > (~BE_U64_C(0)) - low_bits)
			return BE_R4_ERROR_HTVAL_OVERFLOW;
		reconstructed += low_bits;
		if (reconstructed != BE_R4_DENIED_GPA)
			return BE_R4_ERROR_GPA;
	}
	if (observation->private_value != BE_R4_PRIVATE_VALUE ||
	    observation->protected_value != 0U ||
	    observation->shared_value != 0U)
		return BE_R4_ERROR_BACKING;
	return BE_R4_ERROR_NONE;
}

static enum be_r4_error
validate_event(const struct be_r4_frame *frame,
	       const struct be_r4_observation *observation)
{
	if (frame->scause != BE_R4_SCAUSE_VS_ECALL)
		return BE_R4_ERROR_CAUSE;
	if (frame->sepc != BE_R4_EVENT_PC)
		return BE_R4_ERROR_PC;
	if (frame->stval != 0U || frame->htval != 0U)
		return BE_R4_ERROR_TRAP_METADATA;
	if (frame->gpr[BE_R4_GPR_A7] != BE_R4_EVENT_ID ||
	    frame->gpr[BE_R4_GPR_A6] != BE_R4_EVENT_VERSION_FUNCTION ||
	    frame->gpr[BE_R4_GPR_A0] != BE_R4_PRIVATE_VALUE ||
	    frame->gpr[BE_R4_GPR_A1] != BE_R4_SHARED_VALUE)
		return BE_R4_ERROR_EVENT_ARGS;
	if (observation->private_value != BE_R4_PRIVATE_VALUE ||
	    observation->protected_value != 0U ||
	    observation->shared_value != BE_R4_SHARED_VALUE)
		return BE_R4_ERROR_BACKING;
	return BE_R4_ERROR_NONE;
}

enum be_r4_error
be_r4_handle_trap(struct be_r4_state *state, struct be_r4_frame *frame,
		  const struct be_r4_observation *observation,
		  struct be_r4_result *result)
{
	struct be_r4_result next_result;
	enum be_r4_error error;
	enum be_r4_trap_class trap_class;
	enum be_r4_phase next_phase;
	be_u64 resume_pc;

	if (state == (struct be_r4_state *)0)
		return BE_R4_ERROR_NULL;
	if (state->phase == BE_R4_PHASE_FAILED)
		return state->error;
	if (state->phase != BE_R4_PHASE_EXPECT_FAULT &&
	    state->phase != BE_R4_PHASE_EXPECT_EVENT)
		return be_r4_fail(state, BE_R4_ERROR_INVALID_PHASE);
	if (frame == (struct be_r4_frame *)0 ||
	    observation == (const struct be_r4_observation *)0 ||
	    result == (struct be_r4_result *)0)
		return be_r4_fail(state, BE_R4_ERROR_NULL);

	error = validate_common(state, frame, observation);
	if (error != BE_R4_ERROR_NONE)
		return be_r4_fail(state, error);

	if (state->phase == BE_R4_PHASE_EXPECT_FAULT) {
		if (state->fault_seen != 0U || state->event_seen != 0U ||
		    state->trap_count != 0U)
			return be_r4_fail(state, BE_R4_ERROR_INVALID_PHASE);
		error = validate_fault(frame, observation);
		trap_class = BE_R4_TRAP_EXPECTED_DENIED_LOAD;
		next_phase = BE_R4_PHASE_EXPECT_EVENT;
	} else {
		if (state->fault_seen != 1U || state->event_seen != 0U ||
		    state->trap_count != 1U)
			return be_r4_fail(state, BE_R4_ERROR_INVALID_PHASE);
		error = validate_event(frame, observation);
		trap_class = BE_R4_TRAP_PRIVATE_EVENT;
		next_phase = BE_R4_PHASE_COMPLETE;
	}
	if (error != BE_R4_ERROR_NONE)
		return be_r4_fail(state, error);
	if (frame->sepc > (~BE_U64_C(0)) - BE_R4_INSTRUCTION_SIZE)
		return be_r4_fail(state, BE_R4_ERROR_PC);

	resume_pc = frame->sepc + BE_R4_INSTRUCTION_SIZE;
	next_result = (struct be_r4_result) {
		.decision = BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME,
		.trap_class = trap_class,
		.resume_pc = resume_pc,
		.active = state->active,
	};

	frame->sepc = resume_pc;
	*result = next_result;
	if (next_phase == BE_R4_PHASE_EXPECT_EVENT)
		state->fault_seen = 1U;
	else
		state->event_seen = 1U;
	++state->trap_count;
	state->decision = BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME;
	state->phase = next_phase;
	return BE_R4_ERROR_NONE;
}

const char *be_r4_phase_name(enum be_r4_phase phase)
{
	switch (phase) {
	case BE_R4_PHASE_EMPTY:
		return "empty";
	case BE_R4_PHASE_EXPECT_FAULT:
		return "expect-fault";
	case BE_R4_PHASE_EXPECT_EVENT:
		return "expect-event";
	case BE_R4_PHASE_COMPLETE:
		return "complete";
	case BE_R4_PHASE_FAILED:
		return "failed";
	default:
		return "invalid";
	}
}

const char *be_r4_error_name(enum be_r4_error error)
{
	switch (error) {
	case BE_R4_ERROR_NONE:
		return "none";
	case BE_R4_ERROR_NULL:
		return "null";
	case BE_R4_ERROR_INVALID_PHASE:
		return "invalid-phase";
	case BE_R4_ERROR_R3_STATE:
		return "r3-state";
	case BE_R4_ERROR_BINDING:
		return "binding";
	case BE_R4_ERROR_FRAME_RESERVED:
		return "frame-reserved";
	case BE_R4_ERROR_INTERRUPT:
		return "interrupt";
	case BE_R4_ERROR_CAUSE:
		return "cause";
	case BE_R4_ERROR_HART:
		return "hart";
	case BE_R4_ERROR_HGATP:
		return "hgatp";
	case BE_R4_ERROR_PC:
		return "pc";
	case BE_R4_ERROR_GVA:
		return "gva";
	case BE_R4_ERROR_HTVAL_OVERFLOW:
		return "htval-overflow";
	case BE_R4_ERROR_GPA:
		return "gpa";
	case BE_R4_ERROR_TRAP_METADATA:
		return "trap-metadata";
	case BE_R4_ERROR_BACKING:
		return "backing";
	case BE_R4_ERROR_EVENT_ARGS:
		return "event-args";
	default:
		return "invalid";
	}
}

const char *be_r4_trap_class_name(enum be_r4_trap_class trap_class)
{
	switch (trap_class) {
	case BE_R4_TRAP_NONE:
		return "none";
	case BE_R4_TRAP_EXPECTED_DENIED_LOAD:
		return "expected-denied-load";
	case BE_R4_TRAP_PRIVATE_EVENT:
		return "private-event";
	default:
		return "invalid";
	}
}

const char *be_r4_decision_name(enum be_r4_decision decision)
{
	switch (decision) {
	case BE_R4_DECISION_NONE:
		return "none";
	case BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME:
		return "resume-same-management-full-frame";
	case BE_R4_DECISION_TERMINAL:
		return "terminal";
	default:
		return "invalid";
	}
}
