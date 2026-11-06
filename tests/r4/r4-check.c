// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: focused host coverage for the bounded R4 frame, exact R3 import,
 *          denied-load classification, private event, transactionality, and
 *          sticky terminal failure.
 * Trust:   host evidence only. No CSR, fence, guest entry, QEMU, or hardware
 *          behavior is exercised.
 * Scope:   R4 only. No switching, protected entry, or R5 behavior.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <be/r4.h>

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			puts("BE_R4_CHECK: assertion failed: " #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

static struct be_r3_binding valid_binding(void)
{
	return (struct be_r3_binding) {
		.domain = BE_DOMAIN_MANAGEMENT,
		.vcpu_id = 1U,
		.root_id = 101U,
		.vmid = 0U,
		.hgatp = BE_R3_MANAGEMENT_HGATP,
		.guest_pc = BE_R3_INITIAL_GUEST_PC,
		.guest_sp = BE_R3_INITIAL_GUEST_SP,
		.trusted_sp = BE_R3_INITIAL_TRUSTED_SP,
		.saved_state_id = 1U,
		.saved_state_pa = BE_R3_MANAGEMENT_SAVED_PA,
		.vsatp = 0U,
		.published = 1U,
	};
}

static struct be_r3_state valid_r3(void)
{
	return (struct be_r3_state) {
		.phase = BE_R3_PHASE_ENTRY_ARMED,
		.error = BE_R3_ERROR_NONE,
		.firmware_pointer = BE_U64_C(0x87e00000),
		.configuration_id = BE_R3_CONFIGURATION_ID,
		.management_hgatp = BE_R3_MANAGEMENT_HGATP,
		.protected_hgatp = BE_R3_PROTECTED_HGATP,
		.pending = { 0 },
		.active = valid_binding(),
	};
}

static struct be_r4_observation fault_observation(void)
{
	return (struct be_r4_observation) {
		.hart_id = BE_CONFIGURATION_HART_ID,
		.active = valid_binding(),
		.current_hgatp = BE_R3_MANAGEMENT_HGATP,
		.private_value = BE_R4_PRIVATE_VALUE,
		.protected_value = 0U,
		.shared_value = 0U,
	};
}

static struct be_r4_observation event_observation(void)
{
	struct be_r4_observation observation = fault_observation();

	observation.shared_value = BE_R4_SHARED_VALUE;
	return observation;
}

static struct be_r4_frame patterned_frame(void)
{
	struct be_r4_frame frame;
	be_size index;

	for (index = 0U; index < BE_ARRAY_SIZE(frame.gpr); ++index)
		frame.gpr[index] = BE_U64_C(0x1000) + index;
	frame.vstvec = BE_U64_C(0x2001);
	frame.vsepc = BE_U64_C(0x2002);
	frame.vscause = BE_U64_C(0x2003);
	frame.vstval = BE_U64_C(0x2004);
	frame.scause = 0U;
	frame.sepc = 0U;
	frame.stval = 0U;
	frame.htval = 0U;
	frame.reserved = 0U;
	return frame;
}

static struct be_r4_frame fault_frame(be_u64 htval)
{
	struct be_r4_frame frame = patterned_frame();

	frame.scause = BE_R4_SCAUSE_LOAD_GUEST_PAGE_FAULT;
	frame.sepc = BE_R4_FAULT_PC;
	frame.stval = BE_R4_DENIED_GVA;
	frame.htval = htval;
	return frame;
}

static struct be_r4_frame event_frame(void)
{
	struct be_r4_frame frame = patterned_frame();

	frame.scause = BE_R4_SCAUSE_VS_ECALL;
	frame.sepc = BE_R4_EVENT_PC;
	frame.stval = 0U;
	frame.htval = 0U;
	frame.gpr[BE_R4_GPR_A7] = BE_R4_EVENT_ID;
	frame.gpr[BE_R4_GPR_A6] = BE_R4_EVENT_VERSION_FUNCTION;
	frame.gpr[BE_R4_GPR_A0] = BE_R4_PRIVATE_VALUE;
	frame.gpr[BE_R4_GPR_A1] = BE_R4_SHARED_VALUE;
	return frame;
}

static struct be_r4_state begun_state(void)
{
	struct be_r3_state r3 = valid_r3();
	struct be_r4_state state = BE_R4_STATE_INITIALIZER;

	CHECK(be_r4_begin(&state, &r3) == BE_R4_ERROR_NONE);
	return state;
}

static void service_fault(struct be_r4_state *state)
{
	struct be_r4_frame frame = fault_frame(BE_R4_DENIED_HTVAL);
	struct be_r4_observation observation = fault_observation();
	struct be_r4_result result = { 0 };

	CHECK(be_r4_handle_trap(state, &frame, &observation, &result) ==
	      BE_R4_ERROR_NONE);
}

static int bindings_equal(const struct be_r3_binding *left,
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

static int binding_is_zero(const struct be_r3_binding *binding)
{
	struct be_r3_binding zero = { 0 };

	return bindings_equal(binding, &zero);
}

static void check_terminal(const struct be_r4_state *state,
			   enum be_r4_error error)
{
	CHECK(state->phase == BE_R4_PHASE_FAILED);
	CHECK(state->error == error);
	CHECK(state->decision == BE_R4_DECISION_TERMINAL);
	CHECK(binding_is_zero(&state->active));
	CHECK(state->configuration_id == 0U);
	CHECK(state->management_hgatp == 0U);
	CHECK(state->protected_hgatp == 0U);
	CHECK(state->fault_seen == 0U);
	CHECK(state->event_seen == 0U);
	CHECK(state->trap_count == 0U);
}

static void expect_begin_rejected(struct be_r3_state r3)
{
	struct be_r4_state state = BE_R4_STATE_INITIALIZER;

	CHECK(be_r4_begin(&state, &r3) == BE_R4_ERROR_R3_STATE);
	check_terminal(&state, BE_R4_ERROR_R3_STATE);
}

static void test_layout_and_names(void)
{
	SCENARIO();
	CHECK(sizeof(struct be_r4_frame) == 320U);
	CHECK(_Alignof(struct be_r4_frame) == 8U);
	CHECK(__builtin_offsetof(struct be_r4_frame, gpr) == 0U);
	CHECK(__builtin_offsetof(struct be_r4_frame, vstvec) == 248U);
	CHECK(__builtin_offsetof(struct be_r4_frame, vsepc) == 256U);
	CHECK(__builtin_offsetof(struct be_r4_frame, vscause) == 264U);
	CHECK(__builtin_offsetof(struct be_r4_frame, vstval) == 272U);
	CHECK(__builtin_offsetof(struct be_r4_frame, scause) == 280U);
	CHECK(__builtin_offsetof(struct be_r4_frame, sepc) == 288U);
	CHECK(__builtin_offsetof(struct be_r4_frame, stval) == 296U);
	CHECK(__builtin_offsetof(struct be_r4_frame, htval) == 304U);
	CHECK(__builtin_offsetof(struct be_r4_frame, reserved) == 312U);
	CHECK(strcmp(be_r4_phase_name(BE_R4_PHASE_EXPECT_FAULT),
		     "expect-fault") == 0);
	CHECK(strcmp(be_r4_error_name(BE_R4_ERROR_GPA), "gpa") == 0);
	CHECK(strcmp(be_r4_trap_class_name(BE_R4_TRAP_PRIVATE_EVENT),
		     "private-event") == 0);
	CHECK(strcmp(be_r4_decision_name(
		     BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME),
		     "resume-same-management-full-frame") == 0);
	CHECK(strcmp(be_r4_phase_name((enum be_r4_phase)99), "invalid") == 0);
	CHECK(strcmp(be_r4_error_name((enum be_r4_error)99), "invalid") == 0);
}

static void test_begin_acceptance(void)
{
	struct be_r3_state r3 = valid_r3();
	struct be_r4_state state = BE_R4_STATE_INITIALIZER;

	SCENARIO();
	CHECK(be_r4_begin((struct be_r4_state *)0, &r3) ==
	      BE_R4_ERROR_NULL);
	CHECK(be_r4_begin(&state, &r3) == BE_R4_ERROR_NONE);
	CHECK(state.phase == BE_R4_PHASE_EXPECT_FAULT);
	CHECK(state.error == BE_R4_ERROR_NONE);
	CHECK(state.decision == BE_R4_DECISION_NONE);
	CHECK(bindings_equal(&state.active, &r3.active));
	CHECK(state.configuration_id == BE_R3_CONFIGURATION_ID);
	CHECK(state.management_hgatp == BE_R3_MANAGEMENT_HGATP);
	CHECK(state.protected_hgatp == BE_R3_PROTECTED_HGATP);
	CHECK(state.fault_seen == 0U && state.event_seen == 0U);
	CHECK(state.trap_count == 0U);
	CHECK(be_r4_begin(&state, &r3) == BE_R4_ERROR_INVALID_PHASE);
	check_terminal(&state, BE_R4_ERROR_INVALID_PHASE);

	state = (struct be_r4_state)BE_R4_STATE_INITIALIZER;
	CHECK(be_r4_begin(&state, (const struct be_r3_state *)0) ==
	      BE_R4_ERROR_NULL);
	check_terminal(&state, BE_R4_ERROR_NULL);
}

static void test_r3_mutations(void)
{
	struct be_r3_state r3;

	SCENARIO();
#define REJECT_R3(field, value) \
	do { \
		r3 = valid_r3(); \
		r3.field = (value); \
		expect_begin_rejected(r3); \
	} while (0)

	REJECT_R3(phase, BE_R3_PHASE_BINDING_PUBLISHED);
	REJECT_R3(error, BE_R3_ERROR_BINDING);
	REJECT_R3(configuration_id, 0U);
	REJECT_R3(management_hgatp, 0U);
	REJECT_R3(protected_hgatp, 0U);

#define REJECT_PENDING(field, value) \
	do { \
		r3 = valid_r3(); \
		r3.pending.field = (value); \
		expect_begin_rejected(r3); \
	} while (0)

	REJECT_PENDING(domain, BE_DOMAIN_MANAGEMENT);
	REJECT_PENDING(vcpu_id, 1U);
	REJECT_PENDING(root_id, 101U);
	REJECT_PENDING(vmid, 1U);
	REJECT_PENDING(hgatp, BE_R3_MANAGEMENT_HGATP);
	REJECT_PENDING(guest_pc, BE_R3_INITIAL_GUEST_PC);
	REJECT_PENDING(guest_sp, BE_R3_INITIAL_GUEST_SP);
	REJECT_PENDING(trusted_sp, BE_R3_INITIAL_TRUSTED_SP);
	REJECT_PENDING(saved_state_id, 1U);
	REJECT_PENDING(saved_state_pa, BE_R3_MANAGEMENT_SAVED_PA);
	REJECT_PENDING(vsatp, 1U);
	REJECT_PENDING(published, 1U);

#define REJECT_ACTIVE(field, value) \
	do { \
		r3 = valid_r3(); \
		r3.active.field = (value); \
		expect_begin_rejected(r3); \
	} while (0)

	REJECT_ACTIVE(domain, BE_DOMAIN_PROTECTED);
	REJECT_ACTIVE(vcpu_id, 2U);
	REJECT_ACTIVE(root_id, 102U);
	REJECT_ACTIVE(vmid, 1U);
	REJECT_ACTIVE(hgatp, BE_R3_PROTECTED_HGATP);
	REJECT_ACTIVE(guest_pc, BE_R3_INITIAL_GUEST_PC + 4U);
	REJECT_ACTIVE(guest_sp, BE_R3_INITIAL_GUEST_SP - 8U);
	REJECT_ACTIVE(trusted_sp, BE_R3_INITIAL_TRUSTED_SP - 8U);
	REJECT_ACTIVE(saved_state_id, 2U);
	REJECT_ACTIVE(saved_state_pa, BE_R3_MANAGEMENT_SAVED_PA + 4096U);
	REJECT_ACTIVE(vsatp, 1U);
	REJECT_ACTIVE(published, 0U);

#undef REJECT_ACTIVE
#undef REJECT_PENDING
#undef REJECT_R3

	r3 = valid_r3();
	r3.firmware_pointer = 0U;
	{
		struct be_r4_state state = BE_R4_STATE_INITIALIZER;

		CHECK(be_r4_begin(&state, &r3) == BE_R4_ERROR_NONE);
	}
}

static void check_frame_only_sepc_changed(const struct be_r4_frame *before,
					  const struct be_r4_frame *after,
					  be_u64 expected_sepc)
{
	struct be_r4_frame expected = *before;

	expected.sepc = expected_sepc;
	CHECK(memcmp(&expected, after, sizeof(expected)) == 0);
}

static void test_fault_positive(be_u64 htval)
{
	struct be_r4_state state = begun_state();
	struct be_r4_frame frame = fault_frame(htval);
	struct be_r4_frame before = frame;
	struct be_r4_observation observation = fault_observation();
	struct be_r4_result result = { 0 };

	SCENARIO();
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      BE_R4_ERROR_NONE);
	CHECK(state.phase == BE_R4_PHASE_EXPECT_EVENT);
	CHECK(state.error == BE_R4_ERROR_NONE);
	CHECK(state.decision ==
	      BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME);
	CHECK(state.fault_seen == 1U);
	CHECK(state.event_seen == 0U);
	CHECK(state.trap_count == 1U);
	CHECK(result.decision ==
	      BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME);
	CHECK(result.trap_class == BE_R4_TRAP_EXPECTED_DENIED_LOAD);
	CHECK(result.resume_pc == BE_R4_FAULT_PC + 4U);
	CHECK(bindings_equal(&result.active, &observation.active));
	CHECK(bindings_equal(&state.active, &observation.active));
	check_frame_only_sepc_changed(&before, &frame, BE_R4_FAULT_PC + 4U);
}

static void test_event_positive(void)
{
	struct be_r4_state state = begun_state();
	struct be_r4_frame frame = event_frame();
	struct be_r4_frame before = frame;
	struct be_r4_observation observation = event_observation();
	struct be_r4_result result = { 0 };

	SCENARIO();
	service_fault(&state);
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      BE_R4_ERROR_NONE);
	CHECK(state.phase == BE_R4_PHASE_COMPLETE);
	CHECK(state.decision ==
	      BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME);
	CHECK(state.fault_seen == 1U);
	CHECK(state.event_seen == 1U);
	CHECK(state.trap_count == 2U);
	CHECK(result.decision ==
	      BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME);
	CHECK(result.trap_class == BE_R4_TRAP_PRIVATE_EVENT);
	CHECK(result.resume_pc == BE_R4_EVENT_PC + 4U);
	CHECK(bindings_equal(&result.active, &state.active));
	check_frame_only_sepc_changed(&before, &frame, BE_R4_EVENT_PC + 4U);

	before = frame;
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      BE_R4_ERROR_INVALID_PHASE);
	CHECK(memcmp(&frame, &before, sizeof(frame)) == 0);
	check_terminal(&state, BE_R4_ERROR_INVALID_PHASE);
}

static void expect_fault_failure(struct be_r4_frame frame,
				 struct be_r4_observation observation,
				 enum be_r4_error expected)
{
	struct be_r4_state state = begun_state();
	struct be_r4_frame before = frame;
	struct be_r4_result result = {
		.decision = BE_R4_DECISION_TERMINAL,
		.trap_class = BE_R4_TRAP_PRIVATE_EVENT,
		.resume_pc = BE_U64_C(0xfeed),
		.active = valid_binding(),
	};
	struct be_r4_result result_before = result;

	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      expected);
	CHECK(memcmp(&frame, &before, sizeof(frame)) == 0);
	CHECK(memcmp(&result, &result_before, sizeof(result)) == 0);
	check_terminal(&state, expected);
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      expected);
	CHECK(be_r4_fail(&state, BE_R4_ERROR_NULL) == expected);
	CHECK(state.error == expected);
}

static void test_fault_failures(void)
{
	struct be_r4_frame frame;
	struct be_r4_observation observation;

	SCENARIO();
	frame = event_frame();
	observation = fault_observation();
	expect_fault_failure(frame, observation, BE_R4_ERROR_CAUSE);

	frame = fault_frame(BE_R4_DENIED_HTVAL);
	frame.scause |= BE_R4_INTERRUPT_BIT;
	expect_fault_failure(frame, observation, BE_R4_ERROR_INTERRUPT);

	frame = fault_frame(BE_R4_DENIED_HTVAL);
	frame.scause = BE_R4_SCAUSE_VIRTUAL_INSTRUCTION;
	expect_fault_failure(frame, observation, BE_R4_ERROR_CAUSE);

	frame = fault_frame(BE_R4_DENIED_HTVAL);
	frame.sepc += 4U;
	expect_fault_failure(frame, observation, BE_R4_ERROR_PC);

	frame = fault_frame(BE_R4_DENIED_HTVAL);
	frame.stval += 1U;
	expect_fault_failure(frame, observation, BE_R4_ERROR_GVA);

	frame = fault_frame(BE_R4_DENIED_HTVAL + 1U);
	expect_fault_failure(frame, observation, BE_R4_ERROR_GPA);

	frame = fault_frame(BE_U64_C(0x4000000000000000));
	expect_fault_failure(frame, observation, BE_R4_ERROR_HTVAL_OVERFLOW);

	frame = fault_frame(BE_R4_DENIED_HTVAL);
	frame.reserved = 1U;
	expect_fault_failure(frame, observation, BE_R4_ERROR_FRAME_RESERVED);

	frame = fault_frame(BE_R4_DENIED_HTVAL);
	observation = fault_observation();
	observation.hart_id = 1U;
	expect_fault_failure(frame, observation, BE_R4_ERROR_HART);

	observation = fault_observation();
	observation.current_hgatp = BE_R3_PROTECTED_HGATP;
	expect_fault_failure(frame, observation, BE_R4_ERROR_HGATP);

#define BAD_OBS_BINDING(field, value) \
	do { \
		observation = fault_observation(); \
		observation.active.field = (value); \
		expect_fault_failure(frame, observation, BE_R4_ERROR_BINDING); \
	} while (0)

	BAD_OBS_BINDING(domain, BE_DOMAIN_PROTECTED);
	BAD_OBS_BINDING(vcpu_id, 2U);
	BAD_OBS_BINDING(root_id, 102U);
	BAD_OBS_BINDING(vmid, 1U);
	BAD_OBS_BINDING(hgatp, BE_R3_PROTECTED_HGATP);
	BAD_OBS_BINDING(guest_pc, BE_R3_INITIAL_GUEST_PC + 4U);
	BAD_OBS_BINDING(guest_sp, BE_R3_INITIAL_GUEST_SP - 8U);
	BAD_OBS_BINDING(trusted_sp, BE_R3_INITIAL_TRUSTED_SP - 8U);
	BAD_OBS_BINDING(saved_state_id, 2U);
	BAD_OBS_BINDING(saved_state_pa, BE_R3_MANAGEMENT_SAVED_PA + 4096U);
	BAD_OBS_BINDING(vsatp, 1U);
	BAD_OBS_BINDING(published, 0U);

#undef BAD_OBS_BINDING

	observation = fault_observation();
	observation.private_value = 16U;
	expect_fault_failure(frame, observation, BE_R4_ERROR_BACKING);
	observation = fault_observation();
	observation.protected_value = 1U;
	expect_fault_failure(frame, observation, BE_R4_ERROR_BACKING);
	observation = fault_observation();
	observation.shared_value = 1U;
	expect_fault_failure(frame, observation, BE_R4_ERROR_BACKING);
}

static void expect_event_failure(struct be_r4_frame frame,
				 struct be_r4_observation observation,
				 enum be_r4_error expected)
{
	struct be_r4_state state = begun_state();
	struct be_r4_frame before = frame;
	struct be_r4_result result = {
		.decision = BE_R4_DECISION_TERMINAL,
		.trap_class = BE_R4_TRAP_EXPECTED_DENIED_LOAD,
		.resume_pc = BE_U64_C(0xbeef),
		.active = valid_binding(),
	};
	struct be_r4_result result_before = result;

	service_fault(&state);
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      expected);
	CHECK(memcmp(&frame, &before, sizeof(frame)) == 0);
	CHECK(memcmp(&result, &result_before, sizeof(result)) == 0);
	check_terminal(&state, expected);
}

static void test_event_failures(void)
{
	struct be_r4_frame frame;
	struct be_r4_observation observation = event_observation();

	SCENARIO();
	frame = fault_frame(BE_R4_DENIED_HTVAL);
	expect_event_failure(frame, observation, BE_R4_ERROR_CAUSE);

	frame = event_frame();
	frame.scause |= BE_R4_INTERRUPT_BIT;
	expect_event_failure(frame, observation, BE_R4_ERROR_INTERRUPT);

	frame = event_frame();
	frame.scause = BE_R4_SCAUSE_VIRTUAL_INSTRUCTION;
	expect_event_failure(frame, observation, BE_R4_ERROR_CAUSE);

	frame = event_frame();
	frame.sepc += 4U;
	expect_event_failure(frame, observation, BE_R4_ERROR_PC);

	frame = event_frame();
	frame.stval = 1U;
	expect_event_failure(frame, observation, BE_R4_ERROR_TRAP_METADATA);
	frame = event_frame();
	frame.htval = 1U;
	expect_event_failure(frame, observation, BE_R4_ERROR_TRAP_METADATA);

	frame = event_frame();
	frame.gpr[BE_R4_GPR_A7] = 2U;
	expect_event_failure(frame, observation, BE_R4_ERROR_EVENT_ARGS);
	frame = event_frame();
	frame.gpr[BE_R4_GPR_A6] = 1U;
	expect_event_failure(frame, observation, BE_R4_ERROR_EVENT_ARGS);
	frame = event_frame();
	frame.gpr[BE_R4_GPR_A0] = 16U;
	expect_event_failure(frame, observation, BE_R4_ERROR_EVENT_ARGS);
	frame = event_frame();
	frame.gpr[BE_R4_GPR_A1] = 33U;
	expect_event_failure(frame, observation, BE_R4_ERROR_EVENT_ARGS);

	frame = event_frame();
	frame.reserved = 1U;
	expect_event_failure(frame, observation, BE_R4_ERROR_FRAME_RESERVED);

	frame = event_frame();
	observation = event_observation();
	observation.private_value = 16U;
	expect_event_failure(frame, observation, BE_R4_ERROR_BACKING);
	observation = event_observation();
	observation.protected_value = 1U;
	expect_event_failure(frame, observation, BE_R4_ERROR_BACKING);
	observation = event_observation();
	observation.shared_value = 33U;
	expect_event_failure(frame, observation, BE_R4_ERROR_BACKING);

	observation = event_observation();
	observation.active.root_id = 102U;
	expect_event_failure(frame, observation, BE_R4_ERROR_BINDING);
	observation = event_observation();
	observation.hart_id = 1U;
	expect_event_failure(frame, observation, BE_R4_ERROR_HART);
	observation = event_observation();
	observation.active.domain = BE_DOMAIN_PROTECTED;
	expect_event_failure(frame, observation, BE_R4_ERROR_BINDING);
	observation = event_observation();
	observation.active.vcpu_id = 2U;
	expect_event_failure(frame, observation, BE_R4_ERROR_BINDING);
	observation = event_observation();
	observation.active.vmid = 1U;
	expect_event_failure(frame, observation, BE_R4_ERROR_BINDING);
	observation = event_observation();
	observation.current_hgatp = BE_R3_PROTECTED_HGATP;
	expect_event_failure(frame, observation, BE_R4_ERROR_HGATP);
}

static void test_wrong_order_and_state_corruption(void)
{
	struct be_r4_state state = begun_state();
	struct be_r4_frame frame = event_frame();
	struct be_r4_observation observation = event_observation();
	struct be_r4_result result = { 0 };

	SCENARIO();
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      BE_R4_ERROR_CAUSE);
	check_terminal(&state, BE_R4_ERROR_CAUSE);

	state = begun_state();
	state.fault_seen = 1U;
	frame = fault_frame(BE_R4_DENIED_HTVAL);
	observation = fault_observation();
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      BE_R4_ERROR_INVALID_PHASE);
	check_terminal(&state, BE_R4_ERROR_INVALID_PHASE);

	state = begun_state();
	service_fault(&state);
	state.trap_count = 0U;
	frame = event_frame();
	observation = event_observation();
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      BE_R4_ERROR_INVALID_PHASE);
	check_terminal(&state, BE_R4_ERROR_INVALID_PHASE);

	state = begun_state();
	state.configuration_id = 0U;
	frame = fault_frame(BE_R4_DENIED_HTVAL);
	observation = fault_observation();
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      BE_R4_ERROR_R3_STATE);
	check_terminal(&state, BE_R4_ERROR_R3_STATE);

	state = begun_state();
	state.management_hgatp = 0U;
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      BE_R4_ERROR_R3_STATE);
	check_terminal(&state, BE_R4_ERROR_R3_STATE);

	state = begun_state();
	state.protected_hgatp = 0U;
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      BE_R4_ERROR_R3_STATE);
	check_terminal(&state, BE_R4_ERROR_R3_STATE);

	state = begun_state();
	state.active.root_id = 102U;
	observation.active.root_id = 102U;
	CHECK(be_r4_handle_trap(&state, &frame, &observation, &result) ==
	      BE_R4_ERROR_BINDING);
	check_terminal(&state, BE_R4_ERROR_BINDING);
}

static void test_null_and_explicit_fail(void)
{
	struct be_r4_state state = begun_state();
	struct be_r4_frame frame = fault_frame(BE_R4_DENIED_HTVAL);
	struct be_r4_observation observation = fault_observation();
	struct be_r4_result result = { 0 };

	SCENARIO();
	CHECK(be_r4_handle_trap((struct be_r4_state *)0, &frame,
				&observation, &result) == BE_R4_ERROR_NULL);
	CHECK(be_r4_handle_trap(&state, (struct be_r4_frame *)0,
				&observation, &result) == BE_R4_ERROR_NULL);
	check_terminal(&state, BE_R4_ERROR_NULL);

	state = begun_state();
	CHECK(be_r4_handle_trap(&state, &frame,
				(const struct be_r4_observation *)0,
				&result) == BE_R4_ERROR_NULL);
	check_terminal(&state, BE_R4_ERROR_NULL);

	state = begun_state();
	CHECK(be_r4_handle_trap(&state, &frame, &observation,
				(struct be_r4_result *)0) ==
	      BE_R4_ERROR_NULL);
	check_terminal(&state, BE_R4_ERROR_NULL);

	state = begun_state();
	CHECK(be_r4_fail(&state, BE_R4_ERROR_NONE) ==
	      BE_R4_ERROR_INVALID_PHASE);
	check_terminal(&state, BE_R4_ERROR_INVALID_PHASE);
}

static void print_count(const char *label, unsigned long value)
{
	printf("%s%lu\n", label, value);
}

int main(void)
{
	test_layout_and_names();
	test_begin_acceptance();
	test_r3_mutations();
	test_fault_positive(BE_R4_DENIED_HTVAL);
	test_fault_positive(0U);
	test_event_positive();
	test_fault_failures();
	test_event_failures();
	test_wrong_order_and_state_corruption();
	test_null_and_explicit_fail();

	puts("BE_R4_CHECK: PASS");
	print_count("BE_R4_CHECK: scenarios=", scenarios);
	print_count("BE_R4_CHECK: assertions=", assertions);
	return 0;
}
