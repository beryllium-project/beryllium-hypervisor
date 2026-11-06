// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: focused host coverage for the bounded R5 import gate, one-way phase
 *          machine, fence/publication acceptance, exit classification, state
 *          separation, transactionality, and sticky terminal failure.
 * Trust:   host evidence only. No CSR, fence, guest entry, QEMU, or hardware
 *          behavior is exercised.
 * Scope:   R5 only. No privileged runtime, image, or R6 behavior.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <be/r5.h>

#include "../../arch/riscv/be/r0-sbi.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_R5_CHECK: assertion failed: %s:%d: %s\n", \
			       __FILE__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

static struct be_r3_binding management_binding_value(be_u32 published)
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
		.published = published,
	};
}

static struct be_r3_binding protected_binding_value(be_u32 published)
{
	return (struct be_r3_binding) {
		.domain = BE_DOMAIN_PROTECTED,
		.vcpu_id = BE_R5_PROTECTED_VCPU_ID,
		.root_id = BE_R5_PROTECTED_ROOT_ID,
		.vmid = 0U,
		.hgatp = BE_R3_PROTECTED_HGATP,
		.guest_pc = BE_R5_PROTECTED_ENTRY_PC,
		.guest_sp = BE_R5_PROTECTED_GUEST_SP,
		.trusted_sp = BE_R5_PROTECTED_TRUSTED_SP,
		.saved_state_id = BE_R5_PROTECTED_SAVED_STATE_ID,
		.saved_state_pa = BE_R5_PROTECTED_SAVED_PA,
		.vsatp = 0U,
		.published = published,
	};
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

static int is_management_binding(const struct be_r3_binding *binding,
				 be_u32 published)
{
	struct be_r3_binding expected = management_binding_value(published);

	return bindings_equal(binding, &expected);
}

static int is_protected_binding(const struct be_r3_binding *binding,
				be_u32 published)
{
	struct be_r3_binding expected = protected_binding_value(published);

	return bindings_equal(binding, &expected);
}

/* struct be_r4_frame is exactly forty be_u64 words, so memcmp is exact. */
static int frames_equal(const struct be_r4_frame *left,
			const struct be_r4_frame *right)
{
	return memcmp(left, right, sizeof(*left)) == 0;
}

static int frame_is_zero(const struct be_r4_frame *frame)
{
	struct be_r4_frame zero = { 0 };

	return frames_equal(frame, &zero);
}

static int pending_is_zero(const struct be_r5_pending *pending)
{
	return pending->direction == BE_R5_DIRECTION_NONE &&
	       pending->frame_mode == BE_R5_FRAME_MODE_NONE &&
	       binding_is_zero(&pending->source) &&
	       binding_is_zero(&pending->target);
}

static struct be_r4_state valid_r4(void)
{
	return (struct be_r4_state) {
		.phase = BE_R4_PHASE_COMPLETE,
		.error = BE_R4_ERROR_NONE,
		.decision = BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME,
		.active = management_binding_value(1U),
		.configuration_id = BE_R3_CONFIGURATION_ID,
		.management_hgatp = BE_R3_MANAGEMENT_HGATP,
		.protected_hgatp = BE_R3_PROTECTED_HGATP,
		.fault_seen = 1U,
		.event_seen = 1U,
		.trap_count = 2U,
	};
}

static struct be_r4_frame patterned_frame(void)
{
	struct be_r4_frame frame;
	be_size index;

	memset(&frame, 0, sizeof(frame));
	for (index = 0U; index < BE_ARRAY_SIZE(frame.gpr); ++index)
		frame.gpr[index] = BE_U64_C(0x1000) + index;
	frame.vstvec = BE_U64_C(0x2001);
	frame.vsepc = BE_U64_C(0x2002);
	frame.vscause = BE_U64_C(0x2003);
	frame.vstval = BE_U64_C(0x2004);
	return frame;
}

/* Exact advanced management frame the accepted R4 event trap leaves behind. */
static struct be_r4_frame imported_frame(void)
{
	struct be_r4_frame frame = patterned_frame();

	frame.gpr[BE_R5_GPR_SP] = BE_R3_INITIAL_GUEST_SP;
	frame.gpr[BE_R5_GPR_S0] = BE_R4_PRIVATE_VALUE;
	frame.gpr[BE_R4_GPR_A0] = BE_R4_PRIVATE_VALUE;
	frame.gpr[BE_R4_GPR_A1] = BE_R4_SHARED_VALUE;
	frame.gpr[BE_R4_GPR_A6] = BE_R4_EVENT_VERSION_FUNCTION;
	frame.gpr[BE_R4_GPR_A7] = BE_R4_EVENT_ID;
	frame.scause = BE_R4_SCAUSE_VS_ECALL;
	frame.sepc = BE_R5_MANAGEMENT_RESTORE_PC;
	return frame;
}

static struct be_r4_frame final_event_frame(void)
{
	struct be_r4_frame frame = imported_frame();

	frame.gpr[BE_R4_GPR_A7] = BE_R5_FINAL_EVENT_ID;
	frame.sepc = BE_R5_MANAGEMENT_FINAL_EVENT_PC;
	return frame;
}

static struct be_r4_frame protected_frame(void)
{
	struct be_r4_frame frame;

	memset(&frame, 0, sizeof(frame));
	frame.gpr[BE_R5_GPR_SP] = BE_R5_PROTECTED_GUEST_SP;
	frame.gpr[BE_R5_GPR_S0] = BE_R5_PROTECTED_PRIVATE_VALUE;
	return frame;
}

static struct be_r4_frame protected_load_fault_frame(be_u64 htval)
{
	struct be_r4_frame frame = protected_frame();

	frame.scause = BE_R4_SCAUSE_LOAD_GUEST_PAGE_FAULT;
	frame.sepc = BE_R5_PROTECTED_LOAD_FAULT_PC;
	frame.stval = BE_R5_PROTECTED_LOAD_DENIED_GVA;
	frame.htval = htval;
	return frame;
}

static struct be_r4_frame protected_store_fault_frame(be_u64 htval)
{
	struct be_r4_frame frame = protected_frame();

	frame.scause = BE_R5_SCAUSE_STORE_GUEST_PAGE_FAULT;
	frame.sepc = BE_R5_PROTECTED_STORE_FAULT_PC;
	frame.stval = BE_R5_SHARED_STORE_DENIED_GVA;
	frame.htval = htval;
	frame.gpr[BE_R4_GPR_A0] = BE_R5_DENIED_STORE_CANDIDATE;
	return frame;
}

static struct be_r4_frame protected_event_frame(void)
{
	struct be_r4_frame frame = protected_frame();

	frame.scause = BE_R4_SCAUSE_VS_ECALL;
	frame.sepc = BE_R5_PROTECTED_EVENT_PC;
	frame.gpr[BE_R4_GPR_A0] = BE_R5_PROTECTED_PRIVATE_VALUE;
	frame.gpr[BE_R4_GPR_A1] = BE_R4_SHARED_VALUE;
	frame.gpr[BE_R4_GPR_A6] = BE_R4_EVENT_VERSION_FUNCTION;
	frame.gpr[BE_R4_GPR_A7] = BE_R5_PROTECTED_EVENT_ID;
	return frame;
}

static struct be_r5_observation import_observation(void)
{
	return (struct be_r5_observation) {
		.hart_id = BE_CONFIGURATION_HART_ID,
		.active = management_binding_value(1U),
		.current_hgatp = BE_R3_MANAGEMENT_HGATP,
		.hstatus = BE_R3_HSTATUS_CONTROL_VALUE,
		.vsatp = 0U,
		.trusted_sp = BE_R3_INITIAL_TRUSTED_SP,
		.saved_state_pa = BE_R3_MANAGEMENT_SAVED_PA,
		.management_private_value = BE_R4_PRIVATE_VALUE,
		.protected_private_value = 0U,
		.shared_value = BE_R4_SHARED_VALUE,
	};
}

static struct be_r5_observation protected_observation(void)
{
	return (struct be_r5_observation) {
		.hart_id = BE_CONFIGURATION_HART_ID,
		.active = protected_binding_value(1U),
		.current_hgatp = BE_R3_PROTECTED_HGATP,
		.hstatus = BE_R3_HSTATUS_CONTROL_VALUE,
		.vsatp = 0U,
		.trusted_sp = BE_R5_PROTECTED_TRUSTED_SP,
		.saved_state_pa = BE_R5_PROTECTED_SAVED_PA,
		.management_private_value = BE_R4_PRIVATE_VALUE,
		.protected_private_value = BE_R5_PROTECTED_PRIVATE_VALUE,
		.shared_value = BE_R4_SHARED_VALUE,
	};
}

static struct be_r5_observation management_observation(void)
{
	struct be_r5_observation observation = import_observation();

	observation.protected_private_value = BE_R5_PROTECTED_PRIVATE_VALUE;
	return observation;
}

static struct be_r5_fence_ack protected_fence_ack(void)
{
	return (struct be_r5_fence_ack) {
		.source_hgatp = BE_R3_MANAGEMENT_HGATP,
		.hgatp_written = BE_R3_PROTECTED_HGATP,
		.hgatp_readback = BE_R3_PROTECTED_HGATP,
		.virtualization_off = 1U,
		.fence_completed = 1U,
	};
}

static struct be_r5_fence_ack management_fence_ack(void)
{
	return (struct be_r5_fence_ack) {
		.source_hgatp = BE_R3_PROTECTED_HGATP,
		.hgatp_written = BE_R3_MANAGEMENT_HGATP,
		.hgatp_readback = BE_R3_MANAGEMENT_HGATP,
		.virtualization_off = 1U,
		.fence_completed = 1U,
	};
}

static struct be_r5_entry_state protected_entry_state(void)
{
	return (struct be_r5_entry_state) {
		.hgatp = BE_R3_PROTECTED_HGATP,
		.hstatus = BE_R3_HSTATUS_CONTROL_VALUE,
		.sstatus = BE_R3_SSTATUS_SPP,
		.vsatp = 0U,
		.vstvec = 0U,
		.vsepc = 0U,
		.vscause = 0U,
		.vstval = 0U,
		.trusted_sp = BE_R5_PROTECTED_TRUSTED_SP,
		.saved_state_pa = BE_R5_PROTECTED_SAVED_PA,
	};
}

static struct be_r5_entry_state management_entry_state(void)
{
	return (struct be_r5_entry_state) {
		.hgatp = BE_R3_MANAGEMENT_HGATP,
		.hstatus = BE_R3_HSTATUS_CONTROL_VALUE,
		.sstatus = BE_R3_SSTATUS_SPP,
		.vsatp = 0U,
		.vstvec = 0U,
		.vsepc = 0U,
		.vscause = 0U,
		.vstval = 0U,
		.trusted_sp = BE_R3_INITIAL_TRUSTED_SP,
		.saved_state_pa = BE_R3_MANAGEMENT_SAVED_PA,
	};
}

/*
 * The two monitor saved pages are carried with the state so every stage keeps
 * the exact frame bytes the assembly boundary would have written.
 */
struct world {
	struct be_r5_state state;
	struct be_r4_frame management_page;
	struct be_r4_frame protected_page;
	struct be_r5_pending pending;
	struct be_r5_transition transition;
	struct be_r5_result result;
};

static struct world fresh_world(void)
{
	struct be_r5_state initial = BE_R5_STATE_INITIALIZER;
	struct world world;

	memset(&world, 0, sizeof(world));
	world.state = initial;
	world.management_page = imported_frame();
	return world;
}

static struct world imported_world(void)
{
	struct world world = fresh_world();
	struct be_r4_state r4 = valid_r4();
	struct be_r4_frame frame = imported_frame();
	struct be_r5_observation observation = import_observation();

	CHECK(be_r5_import_r4_complete(&world.state, &r4, &frame,
				       &observation) == BE_R5_ERROR_NONE);
	return world;
}

static struct world pending_protected_world(void)
{
	struct world world = imported_world();

	CHECK(be_r5_prepare_pending(&world.state,
				    BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				    &world.pending) == BE_R5_ERROR_NONE);
	return world;
}

static struct world fenced_protected_world(void)
{
	struct world world = pending_protected_world();
	struct be_r5_fence_ack ack = protected_fence_ack();

	CHECK(be_r5_note_target_fenced(&world.state, &ack) ==
	      BE_R5_ERROR_NONE);
	return world;
}

static struct world protected_running_world(void)
{
	struct world world = fenced_protected_world();
	struct be_r5_entry_state entry = protected_entry_state();

	CHECK(be_r5_publish_target(&world.state, &entry, &world.protected_page,
				   &world.transition) == BE_R5_ERROR_NONE);
	return world;
}

static struct world protected_store_world(void)
{
	struct world world = protected_running_world();
	struct be_r5_observation observation = protected_observation();

	world.protected_page =
		protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	CHECK(be_r5_handle_exit(&world.state, &world.protected_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	return world;
}

static struct world protected_event_world(void)
{
	struct world world = protected_store_world();
	struct be_r5_observation observation = protected_observation();

	world.protected_page =
		protected_store_fault_frame(BE_R5_SHARED_STORE_DENIED_HTVAL);
	CHECK(be_r5_handle_exit(&world.state, &world.protected_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	return world;
}

static struct world switch_requested_world(void)
{
	struct world world = protected_event_world();
	struct be_r5_observation observation = protected_observation();

	world.protected_page = protected_event_frame();
	CHECK(be_r5_handle_exit(&world.state, &world.protected_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	return world;
}

static struct world pending_management_world(void)
{
	struct world world = switch_requested_world();

	CHECK(be_r5_prepare_pending(&world.state,
				    BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				    &world.pending) == BE_R5_ERROR_NONE);
	return world;
}

static struct world fenced_management_world(void)
{
	struct world world = pending_management_world();
	struct be_r5_fence_ack ack = management_fence_ack();

	CHECK(be_r5_note_target_fenced(&world.state, &ack) ==
	      BE_R5_ERROR_NONE);
	return world;
}

static struct world management_running_world(void)
{
	struct world world = fenced_management_world();
	struct be_r5_entry_state entry = management_entry_state();

	CHECK(be_r5_publish_target(&world.state, &entry,
				   &world.management_page,
				   &world.transition) == BE_R5_ERROR_NONE);
	return world;
}

static struct world complete_world(void)
{
	struct world world = management_running_world();
	struct be_r5_observation observation = management_observation();

	world.management_page = final_event_frame();
	CHECK(be_r5_handle_exit(&world.state, &world.management_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	return world;
}

/* Every public entry point must keep returning the retained first error. */
static void check_sticky(struct be_r5_state *state, enum be_r5_error error)
{
	struct be_r4_state r4 = valid_r4();
	struct be_r4_frame frame = imported_frame();
	struct be_r4_frame frame_before = imported_frame();
	struct be_r4_frame target;
	struct be_r5_observation observation = import_observation();
	struct be_r5_fence_ack ack = protected_fence_ack();
	struct be_r5_entry_state entry = protected_entry_state();
	struct be_r5_pending pending;
	struct be_r5_transition transition;
	struct be_r5_result result;

	memset(&target, 0, sizeof(target));
	memset(&pending, 0, sizeof(pending));
	memset(&transition, 0, sizeof(transition));
	memset(&result, 0, sizeof(result));

	CHECK(be_r5_import_r4_complete(state, &r4, &frame, &observation) ==
	      error);
	CHECK(be_r5_prepare_pending(state,
				    BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				    &pending) == error);
	CHECK(be_r5_prepare_pending(state,
				    BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				    &pending) == error);
	CHECK(be_r5_note_target_fenced(state, &ack) == error);
	CHECK(be_r5_publish_target(state, &entry, &target, &transition) ==
	      error);
	CHECK(be_r5_handle_exit(state, &frame, &observation, &result) ==
	      error);
	CHECK(be_r5_note_shutdown_returned(state, 0L) == error);
	CHECK(be_r5_fail(state, BE_R5_ERROR_NULL) == error);
	CHECK(be_r5_fail(state, BE_R5_ERROR_NONE) == error);

	CHECK(state->phase == BE_R5_PHASE_FAILED);
	CHECK(state->error == error);
	CHECK(pending_is_zero(&pending));
	CHECK(frame_is_zero(&target));
	CHECK(transition.action == BE_R5_ACTION_NONE);
	CHECK(result.action == BE_R5_ACTION_NONE);
	CHECK(frames_equal(&frame, &frame_before));
}

static void check_terminal(struct be_r5_state *state, enum be_r5_error error)
{
	CHECK(state->phase == BE_R5_PHASE_FAILED);
	CHECK(state->error == error);
	CHECK(state->action == BE_R5_ACTION_TERMINAL);
	CHECK(binding_is_zero(&state->active));
	CHECK(pending_is_zero(&state->pending));
	CHECK(frame_is_zero(&state->management_frame));
	CHECK(state->configuration_id == 0U);
	CHECK(state->management_hgatp == 0U);
	CHECK(state->protected_hgatp == 0U);
	CHECK(state->protected_saved_pc == 0U);
	CHECK(state->switch_requested == 0U);
	CHECK(state->exit_count == 0U);
	CHECK(state->switch_count == 0U);
	check_sticky(state, error);
}

static void test_frozen_constants(void)
{
	SCENARIO();
	CHECK(sizeof(struct be_r4_frame) == 320U);
	CHECK(BE_R5_GPR_SP == 1U);
	CHECK(BE_R5_GPR_S0 == 7U);

	CHECK(BE_R5_MANAGEMENT_FINAL_EVENT_PC ==
	      BE_R5_MANAGEMENT_RESTORE_PC + BE_R4_INSTRUCTION_SIZE);
	CHECK(BE_R5_MANAGEMENT_LOOP_PC ==
	      BE_R5_MANAGEMENT_FINAL_EVENT_PC + BE_R4_INSTRUCTION_SIZE);
	CHECK(BE_R5_MANAGEMENT_RESTORE_PC ==
	      BE_R4_EVENT_PC + BE_R4_INSTRUCTION_SIZE);

	CHECK(BE_R5_PROTECTED_LOAD_RESUME_PC ==
	      BE_R5_PROTECTED_LOAD_FAULT_PC + BE_R4_INSTRUCTION_SIZE);
	CHECK(BE_R5_PROTECTED_STORE_RESUME_PC ==
	      BE_R5_PROTECTED_STORE_FAULT_PC + BE_R4_INSTRUCTION_SIZE);
	CHECK(BE_R5_PROTECTED_SAVED_PC ==
	      BE_R5_PROTECTED_EVENT_PC + BE_R4_INSTRUCTION_SIZE);
	CHECK(BE_R5_PROTECTED_ENTRY_PC < BE_R5_PROTECTED_LOAD_FAULT_PC);
	CHECK(BE_R5_PROTECTED_LOAD_RESUME_PC < BE_R5_PROTECTED_STORE_FAULT_PC);
	CHECK(BE_R5_PROTECTED_STORE_RESUME_PC < BE_R5_PROTECTED_EVENT_PC);

	/* htval is the ratified GPA shifted right by two. */
	CHECK(BE_R5_PROTECTED_LOAD_DENIED_HTVAL ==
	      (BE_R5_PROTECTED_LOAD_DENIED_GPA >> 2));
	CHECK(BE_R5_SHARED_STORE_DENIED_HTVAL ==
	      (BE_R5_SHARED_STORE_DENIED_GPA >> 2));
	CHECK(BE_R4_DENIED_HTVAL == (BE_R4_DENIED_GPA >> 2));

	/* The protected fixture is disjoint from every management identity. */
	CHECK(BE_R5_PROTECTED_VCPU_ID != 1U);
	CHECK(BE_R5_PROTECTED_ROOT_ID != 101U);
	CHECK(BE_R5_PROTECTED_SAVED_STATE_ID != 1U);
	CHECK(BE_R5_PROTECTED_TRUSTED_SP != BE_R3_INITIAL_TRUSTED_SP);
	CHECK(BE_R5_PROTECTED_SAVED_PA != BE_R3_MANAGEMENT_SAVED_PA);
	CHECK(BE_R3_PROTECTED_HGATP != BE_R3_MANAGEMENT_HGATP);
	CHECK(BE_R5_PROTECTED_PRIVATE_VALUE != BE_R4_PRIVATE_VALUE);
	CHECK(BE_R5_DENIED_STORE_CANDIDATE != BE_R4_SHARED_VALUE);
	CHECK(BE_R5_PROTECTED_EVENT_ID != BE_R4_EVENT_ID);
	CHECK(BE_R5_FINAL_EVENT_ID != BE_R5_PROTECTED_EVENT_ID);
	CHECK(BE_R5_SHUTDOWN_TYPE == 0U && BE_R5_SHUTDOWN_REASON == 0U);
	CHECK(strcmp(BE_R5_REPORT_SCHEMA, "be-r5-checked-switch-v1") == 0);
}

static void test_names(void)
{
	struct be_r5_state initial = BE_R5_STATE_INITIALIZER;

	SCENARIO();
	CHECK(initial.phase == BE_R5_PHASE_FRESH);
	CHECK(initial.error == BE_R5_ERROR_NONE);
	CHECK(initial.action == BE_R5_ACTION_NONE);
	CHECK(initial.shutdown_detail == BE_R3_ERROR_NONE);

	CHECK(strcmp(be_r5_phase_name(BE_R5_PHASE_FRESH), "fresh") == 0);
	CHECK(strcmp(be_r5_phase_name(BE_R5_PHASE_IMPORT_R4_COMPLETE),
		     "import-r4-complete") == 0);
	CHECK(strcmp(be_r5_phase_name(BE_R5_PHASE_PENDING_PROTECTED),
		     "pending-protected") == 0);
	CHECK(strcmp(be_r5_phase_name(BE_R5_PHASE_PROTECTED_FENCED),
		     "protected-fenced") == 0);
	CHECK(strcmp(be_r5_phase_name(
		     BE_R5_PHASE_PROTECTED_PUBLISHED_EXPECT_LOAD_FAULT),
		     "protected-published-expect-load-fault") == 0);
	CHECK(strcmp(be_r5_phase_name(
		     BE_R5_PHASE_PROTECTED_EXPECT_SHARED_STORE_FAULT),
		     "protected-expect-shared-store-fault") == 0);
	CHECK(strcmp(be_r5_phase_name(
		     BE_R5_PHASE_PROTECTED_EXPECT_SWITCH_EVENT),
		     "protected-expect-switch-event") == 0);
	CHECK(strcmp(be_r5_phase_name(BE_R5_PHASE_PENDING_MANAGEMENT),
		     "pending-management") == 0);
	CHECK(strcmp(be_r5_phase_name(BE_R5_PHASE_MANAGEMENT_FENCED),
		     "management-fenced") == 0);
	CHECK(strcmp(be_r5_phase_name(
		     BE_R5_PHASE_MANAGEMENT_PUBLISHED_EXPECT_FINAL_EVENT),
		     "management-published-expect-final-event") == 0);
	CHECK(strcmp(be_r5_phase_name(BE_R5_PHASE_COMPLETE), "complete") == 0);
	CHECK(strcmp(be_r5_phase_name(BE_R5_PHASE_FAILED), "failed") == 0);
	CHECK(strcmp(be_r5_phase_name((enum be_r5_phase)99), "invalid") == 0);

	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_NONE), "none") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_NULL), "null") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_INVALID_PHASE),
		     "invalid-phase") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_IMPORT), "import") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_BINDING), "binding") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_PENDING), "pending") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_TRUSTED_STACK),
		     "trusted-stack") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_SAVED_PAGE),
		     "saved-page") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_HGATP), "hgatp") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_VS_ORIGIN),
		     "vs-origin") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_VSATP), "vsatp") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_FRAME_RESERVED),
		     "frame-reserved") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_FRAME_STATE),
		     "frame-state") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_FENCE), "fence") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_TARGET_READBACK),
		     "target-readback") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_TARGET_RESET),
		     "target-reset") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_ENTRY_CONTROLS),
		     "entry-controls") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_PUBLICATION),
		     "publication") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_HART), "hart") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_INTERRUPT),
		     "interrupt") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_CAUSE), "cause") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_PC), "pc") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_GVA), "gva") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_HTVAL_OVERFLOW),
		     "htval-overflow") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_GPA), "gpa") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_TRAP_METADATA),
		     "trap-metadata") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_EVENT_ARGS),
		     "event-args") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_BACKING), "backing") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_SHUTDOWN_RETURNED),
		     "shutdown-returned") == 0);
	CHECK(strcmp(be_r5_error_name(BE_R5_ERROR_SHUTDOWN_REJECTED),
		     "shutdown-rejected") == 0);
	CHECK(strcmp(be_r5_error_name((enum be_r5_error)99), "invalid") == 0);

	CHECK(strcmp(be_r5_direction_name(BE_R5_DIRECTION_NONE), "none") == 0);
	CHECK(strcmp(be_r5_direction_name(
		     BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED),
		     "management-to-protected") == 0);
	CHECK(strcmp(be_r5_direction_name(
		     BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT),
		     "protected-to-management") == 0);
	CHECK(strcmp(be_r5_direction_name((enum be_r5_direction)99),
		     "invalid") == 0);

	CHECK(strcmp(be_r5_frame_mode_name(BE_R5_FRAME_MODE_NONE),
		     "none") == 0);
	CHECK(strcmp(be_r5_frame_mode_name(BE_R5_FRAME_MODE_INITIAL),
		     "initial") == 0);
	CHECK(strcmp(be_r5_frame_mode_name(BE_R5_FRAME_MODE_SAVED),
		     "saved") == 0);
	CHECK(strcmp(be_r5_frame_mode_name((enum be_r5_frame_mode)99),
		     "invalid") == 0);

	CHECK(strcmp(be_r5_exit_class_name(BE_R5_EXIT_NONE), "none") == 0);
	CHECK(strcmp(be_r5_exit_class_name(BE_R5_EXIT_PROTECTED_DENIED_LOAD),
		     "protected-denied-load") == 0);
	CHECK(strcmp(be_r5_exit_class_name(
		     BE_R5_EXIT_PROTECTED_DENIED_SHARED_STORE),
		     "protected-denied-shared-store") == 0);
	CHECK(strcmp(be_r5_exit_class_name(BE_R5_EXIT_PROTECTED_SWITCH_EVENT),
		     "protected-switch-event") == 0);
	CHECK(strcmp(be_r5_exit_class_name(
		     BE_R5_EXIT_MANAGEMENT_FINAL_EVENT),
		     "management-final-event") == 0);
	CHECK(strcmp(be_r5_exit_class_name((enum be_r5_exit_class)99),
		     "invalid") == 0);

	CHECK(strcmp(be_r5_action_name(BE_R5_ACTION_NONE), "none") == 0);
	CHECK(strcmp(be_r5_action_name(
		     BE_R5_ACTION_RESUME_SAME_DOMAIN_FULL_FRAME),
		     "resume-same-domain-full-frame") == 0);
	CHECK(strcmp(be_r5_action_name(BE_R5_ACTION_SWITCH_TO_MANAGEMENT),
		     "switch-to-management") == 0);
	CHECK(strcmp(be_r5_action_name(BE_R5_ACTION_ENTER_TARGET),
		     "enter-target") == 0);
	CHECK(strcmp(be_r5_action_name(BE_R5_ACTION_SHUTDOWN),
		     "shutdown") == 0);
	CHECK(strcmp(be_r5_action_name(BE_R5_ACTION_TERMINAL),
		     "terminal") == 0);
	CHECK(strcmp(be_r5_action_name((enum be_r5_action)99), "invalid") == 0);
}

/*
 * The import gate is exercised against a state produced by the accepted R4
 * mechanism itself, not only against a hand-built fixture.
 */
static void test_import_from_live_r4(void)
{
	struct be_r3_state r3;
	struct be_r4_state r4 = BE_R4_STATE_INITIALIZER;
	struct be_r4_frame frame;
	struct be_r4_frame expected_frame = imported_frame();
	struct be_r4_observation r4_observation;
	struct be_r4_result r4_result;
	struct be_r5_state state = BE_R5_STATE_INITIALIZER;
	struct be_r5_observation observation = import_observation();

	SCENARIO();
	memset(&r3, 0, sizeof(r3));
	r3.phase = BE_R3_PHASE_ENTRY_ARMED;
	r3.error = BE_R3_ERROR_NONE;
	r3.firmware_pointer = BE_U64_C(0x87e00000);
	r3.configuration_id = BE_R3_CONFIGURATION_ID;
	r3.management_hgatp = BE_R3_MANAGEMENT_HGATP;
	r3.protected_hgatp = BE_R3_PROTECTED_HGATP;
	r3.active = management_binding_value(1U);
	CHECK(be_r4_begin(&r4, &r3) == BE_R4_ERROR_NONE);

	memset(&r4_observation, 0, sizeof(r4_observation));
	r4_observation.hart_id = BE_CONFIGURATION_HART_ID;
	r4_observation.active = management_binding_value(1U);
	r4_observation.current_hgatp = BE_R3_MANAGEMENT_HGATP;
	r4_observation.private_value = BE_R4_PRIVATE_VALUE;
	r4_observation.protected_value = 0U;
	r4_observation.shared_value = 0U;

	frame = imported_frame();
	frame.scause = BE_R4_SCAUSE_LOAD_GUEST_PAGE_FAULT;
	frame.sepc = BE_R4_FAULT_PC;
	frame.stval = BE_R4_DENIED_GVA;
	frame.htval = BE_R4_DENIED_HTVAL;
	memset(&r4_result, 0, sizeof(r4_result));
	CHECK(be_r4_handle_trap(&r4, &frame, &r4_observation, &r4_result) ==
	      BE_R4_ERROR_NONE);
	CHECK(r4_result.trap_class == BE_R4_TRAP_EXPECTED_DENIED_LOAD);

	r4_observation.shared_value = BE_R4_SHARED_VALUE;
	frame = imported_frame();
	frame.sepc = BE_R4_EVENT_PC;
	memset(&r4_result, 0, sizeof(r4_result));
	CHECK(be_r4_handle_trap(&r4, &frame, &r4_observation, &r4_result) ==
	      BE_R4_ERROR_NONE);
	CHECK(r4_result.trap_class == BE_R4_TRAP_PRIVATE_EVENT);
	CHECK(r4.phase == BE_R4_PHASE_COMPLETE);
	CHECK(frame.sepc == BE_R5_MANAGEMENT_RESTORE_PC);
	CHECK(frames_equal(&frame, &expected_frame));

	CHECK(be_r5_import_r4_complete(&state, &r4, &frame, &observation) ==
	      BE_R5_ERROR_NONE);
	CHECK(state.phase == BE_R5_PHASE_IMPORT_R4_COMPLETE);
	CHECK(frames_equal(&state.management_frame, &frame));
}

static void test_happy_path(void)
{
	struct world world = fresh_world();
	struct be_r4_state r4 = valid_r4();
	struct be_r4_frame frame = imported_frame();
	struct be_r4_frame initial_protected;
	struct be_r5_observation observation = import_observation();
	struct be_r5_fence_ack ack = protected_fence_ack();
	struct be_r5_entry_state entry = protected_entry_state();

	SCENARIO();
	CHECK(be_r5_import_r4_complete(&world.state, &r4, &frame,
				       &observation) == BE_R5_ERROR_NONE);
	CHECK(world.state.phase == BE_R5_PHASE_IMPORT_R4_COMPLETE);
	CHECK(world.state.error == BE_R5_ERROR_NONE);
	CHECK(world.state.action == BE_R5_ACTION_NONE);
	CHECK(is_management_binding(&world.state.active, 1U));
	CHECK(frames_equal(&world.state.management_frame, &frame));
	CHECK(world.state.configuration_id == BE_R3_CONFIGURATION_ID);
	CHECK(world.state.management_hgatp == BE_R3_MANAGEMENT_HGATP);
	CHECK(world.state.protected_hgatp == BE_R3_PROTECTED_HGATP);
	CHECK(world.state.exit_count == 0U);
	CHECK(world.state.switch_count == 0U);
	CHECK(world.state.switch_requested == 0U);
	CHECK(world.state.protected_saved_pc == 0U);
	CHECK(pending_is_zero(&world.state.pending));

	/* 1. outbound pending record */
	CHECK(be_r5_prepare_pending(&world.state,
				    BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				    &world.pending) == BE_R5_ERROR_NONE);
	CHECK(world.state.phase == BE_R5_PHASE_PENDING_PROTECTED);
	CHECK(world.pending.direction ==
	      BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED);
	CHECK(world.pending.frame_mode == BE_R5_FRAME_MODE_INITIAL);
	CHECK(is_management_binding(&world.pending.source, 1U));
	CHECK(is_protected_binding(&world.pending.target, 0U));
	CHECK(world.state.switch_count == 0U);

	/* 2. ordered write, fence, and readback */
	CHECK(be_r5_note_target_fenced(&world.state, &ack) ==
	      BE_R5_ERROR_NONE);
	CHECK(world.state.phase == BE_R5_PHASE_PROTECTED_FENCED);
	CHECK(is_management_binding(&world.state.active, 1U));

	/* 3. publication */
	CHECK(be_r5_publish_target(&world.state, &entry, &world.protected_page,
				   &world.transition) == BE_R5_ERROR_NONE);
	CHECK(world.state.phase ==
	      BE_R5_PHASE_PROTECTED_PUBLISHED_EXPECT_LOAD_FAULT);
	CHECK(world.state.action == BE_R5_ACTION_ENTER_TARGET);
	CHECK(world.state.switch_count == 1U);
	CHECK(pending_is_zero(&world.state.pending));
	CHECK(is_protected_binding(&world.state.active, 1U));
	CHECK(world.transition.action == BE_R5_ACTION_ENTER_TARGET);
	CHECK(world.transition.direction ==
	      BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED);
	CHECK(world.transition.frame_mode == BE_R5_FRAME_MODE_INITIAL);
	CHECK(world.transition.entry_pc == BE_R5_PROTECTED_ENTRY_PC);
	CHECK(world.transition.entry_sp == BE_R5_PROTECTED_GUEST_SP);
	CHECK(world.transition.trusted_sp == BE_R5_PROTECTED_TRUSTED_SP);
	CHECK(world.transition.saved_state_pa == BE_R5_PROTECTED_SAVED_PA);
	CHECK(is_protected_binding(&world.transition.active, 1U));

	/* The monitor-created initial protected frame carries no source state. */
	memset(&initial_protected, 0, sizeof(initial_protected));
	initial_protected.gpr[BE_R5_GPR_SP] = BE_R5_PROTECTED_GUEST_SP;
	initial_protected.sepc = BE_R5_PROTECTED_ENTRY_PC;
	CHECK(frames_equal(&world.protected_page, &initial_protected));
	CHECK(frames_equal(&world.management_page, &frame));
	CHECK(frames_equal(&world.state.management_frame, &frame));
}

static void test_protected_run_and_return(void)
{
	struct world world = protected_running_world();
	struct be_r4_frame retained = imported_frame();
	struct be_r5_observation observation = protected_observation();
	struct be_r5_fence_ack ack = management_fence_ack();
	struct be_r5_entry_state entry = management_entry_state();

	SCENARIO();
	/* 4. denied management-private load, resumed in the same domain */
	world.protected_page =
		protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	CHECK(be_r5_handle_exit(&world.state, &world.protected_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	CHECK(world.result.action ==
	      BE_R5_ACTION_RESUME_SAME_DOMAIN_FULL_FRAME);
	CHECK(world.result.exit_class == BE_R5_EXIT_PROTECTED_DENIED_LOAD);
	CHECK(world.result.advanced_pc == BE_R5_PROTECTED_LOAD_RESUME_PC);
	CHECK(world.result.shutdown_type == 0U);
	CHECK(world.result.shutdown_reason == 0U);
	CHECK(is_protected_binding(&world.result.active, 1U));
	CHECK(world.protected_page.sepc == BE_R5_PROTECTED_LOAD_RESUME_PC);
	CHECK(world.state.phase ==
	      BE_R5_PHASE_PROTECTED_EXPECT_SHARED_STORE_FAULT);
	CHECK(world.state.exit_count == 1U);
	CHECK(world.state.switch_count == 1U);
	CHECK(world.state.switch_requested == 0U);

	/* 5. denied shared store, resumed in the same domain */
	world.protected_page =
		protected_store_fault_frame(BE_R5_SHARED_STORE_DENIED_HTVAL);
	CHECK(be_r5_handle_exit(&world.state, &world.protected_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	CHECK(world.result.action ==
	      BE_R5_ACTION_RESUME_SAME_DOMAIN_FULL_FRAME);
	CHECK(world.result.exit_class ==
	      BE_R5_EXIT_PROTECTED_DENIED_SHARED_STORE);
	CHECK(world.result.advanced_pc == BE_R5_PROTECTED_STORE_RESUME_PC);
	CHECK(world.protected_page.sepc == BE_R5_PROTECTED_STORE_RESUME_PC);
	CHECK(world.state.phase == BE_R5_PHASE_PROTECTED_EXPECT_SWITCH_EVENT);
	CHECK(world.state.exit_count == 2U);
	CHECK(world.state.switch_requested == 0U);
	/* the denied store never commits to the shared observation */
	CHECK(observation.shared_value == BE_R4_SHARED_VALUE);
	CHECK(observation.shared_value != BE_R5_DENIED_STORE_CANDIDATE);

	/* 6. protected switch event */
	world.protected_page = protected_event_frame();
	CHECK(be_r5_handle_exit(&world.state, &world.protected_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	CHECK(world.result.action == BE_R5_ACTION_SWITCH_TO_MANAGEMENT);
	CHECK(world.result.exit_class == BE_R5_EXIT_PROTECTED_SWITCH_EVENT);
	CHECK(world.result.advanced_pc == BE_R5_PROTECTED_SAVED_PC);
	CHECK(world.protected_page.sepc == BE_R5_PROTECTED_SAVED_PC);
	CHECK(world.state.phase == BE_R5_PHASE_PROTECTED_EXPECT_SWITCH_EVENT);
	CHECK(world.state.exit_count == 3U);
	CHECK(world.state.switch_requested == 1U);
	CHECK(world.state.protected_saved_pc == BE_R5_PROTECTED_SAVED_PC);
	CHECK(is_protected_binding(&world.state.active, 1U));

	/* 7. return pending record */
	CHECK(be_r5_prepare_pending(&world.state,
				    BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				    &world.pending) == BE_R5_ERROR_NONE);
	CHECK(world.state.phase == BE_R5_PHASE_PENDING_MANAGEMENT);
	CHECK(world.pending.direction ==
	      BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT);
	CHECK(world.pending.frame_mode == BE_R5_FRAME_MODE_SAVED);
	CHECK(is_protected_binding(&world.pending.source, 1U));
	CHECK(is_management_binding(&world.pending.target, 0U));

	/* 8. ordered write, fence, and readback back to management */
	CHECK(be_r5_note_target_fenced(&world.state, &ack) ==
	      BE_R5_ERROR_NONE);
	CHECK(world.state.phase == BE_R5_PHASE_MANAGEMENT_FENCED);

	/* 9. publication of the exact retained management frame */
	CHECK(be_r5_publish_target(&world.state, &entry,
				   &world.management_page,
				   &world.transition) == BE_R5_ERROR_NONE);
	CHECK(world.state.phase ==
	      BE_R5_PHASE_MANAGEMENT_PUBLISHED_EXPECT_FINAL_EVENT);
	CHECK(world.state.switch_count == 2U);
	CHECK(world.state.exit_count == 3U);
	CHECK(world.state.switch_requested == 1U);
	CHECK(is_management_binding(&world.state.active, 1U));
	CHECK(world.transition.direction ==
	      BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT);
	CHECK(world.transition.frame_mode == BE_R5_FRAME_MODE_SAVED);
	CHECK(world.transition.entry_pc == BE_R5_MANAGEMENT_RESTORE_PC);
	CHECK(world.transition.entry_sp == BE_R3_INITIAL_GUEST_SP);
	CHECK(world.transition.trusted_sp == BE_R3_INITIAL_TRUSTED_SP);
	CHECK(world.transition.saved_state_pa == BE_R3_MANAGEMENT_SAVED_PA);
	CHECK(is_management_binding(&world.transition.active, 1U));
	/* the saved management page is verified, never rewritten */
	CHECK(frames_equal(&world.management_page, &retained));
	CHECK(frames_equal(&world.state.management_frame, &retained));
}

static void test_completion_and_shutdown(void)
{
	struct world world = management_running_world();
	struct be_r4_frame expected = final_event_frame();
	struct be_r5_observation observation = management_observation();

	SCENARIO();
	world.management_page = final_event_frame();
	CHECK(be_r5_handle_exit(&world.state, &world.management_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	CHECK(world.state.phase == BE_R5_PHASE_COMPLETE);
	CHECK(world.state.error == BE_R5_ERROR_NONE);
	CHECK(world.state.action == BE_R5_ACTION_SHUTDOWN);
	CHECK(world.state.exit_count == 4U);
	CHECK(world.state.switch_count == 2U);
	CHECK(world.result.action == BE_R5_ACTION_SHUTDOWN);
	CHECK(world.result.exit_class == BE_R5_EXIT_MANAGEMENT_FINAL_EVENT);
	CHECK(world.result.shutdown_type == BE_R5_SHUTDOWN_TYPE);
	CHECK(world.result.shutdown_reason == BE_R5_SHUTDOWN_REASON);
	CHECK(is_management_binding(&world.result.active, 1U));
	/* no guest entry follows completion, so the frame is left untouched */
	CHECK(world.result.advanced_pc == 0U);
	CHECK(frames_equal(&world.management_page, &expected));
	CHECK(world.management_page.sepc != BE_R5_MANAGEMENT_LOOP_PC);
}

static void expect_import_rejected(struct be_r4_state r4,
				   struct be_r4_frame frame,
				   struct be_r5_observation observation,
				   enum be_r5_error error)
{
	struct be_r5_state state = BE_R5_STATE_INITIALIZER;

	CHECK(be_r5_import_r4_complete(&state, &r4, &frame, &observation) ==
	      error);
	check_terminal(&state, error);
}

static void test_import_r4_state_rejections(void)
{
	struct be_r4_state r4;
	struct be_r4_frame frame = imported_frame();
	struct be_r5_observation observation = import_observation();

	SCENARIO();
	r4 = valid_r4();
	r4.phase = BE_R4_PHASE_EMPTY;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.phase = BE_R4_PHASE_EXPECT_FAULT;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.phase = BE_R4_PHASE_EXPECT_EVENT;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.phase = BE_R4_PHASE_FAILED;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);

	r4 = valid_r4();
	r4.error = BE_R4_ERROR_BINDING;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.decision = BE_R4_DECISION_NONE;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.decision = BE_R4_DECISION_TERMINAL;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);

	r4 = valid_r4();
	r4.configuration_id = BE_R3_CONFIGURATION_ID + 1U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.management_hgatp = BE_R3_PROTECTED_HGATP;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.protected_hgatp = BE_R3_MANAGEMENT_HGATP;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);

	r4 = valid_r4();
	r4.fault_seen = 0U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.event_seen = 0U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.trap_count = 1U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.trap_count = 3U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
}

static void test_import_binding_rejections(void)
{
	struct be_r4_state r4;
	struct be_r4_frame frame = imported_frame();
	struct be_r5_observation observation = import_observation();

	SCENARIO();
	r4 = valid_r4();
	r4.active.domain = BE_DOMAIN_PROTECTED;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.vcpu_id = BE_R5_PROTECTED_VCPU_ID;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.root_id = BE_R5_PROTECTED_ROOT_ID;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.vmid = 1U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.hgatp = BE_R3_PROTECTED_HGATP;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.guest_pc = BE_R5_PROTECTED_ENTRY_PC;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.guest_sp = BE_R5_PROTECTED_GUEST_SP;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.trusted_sp = BE_R5_PROTECTED_TRUSTED_SP;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.saved_state_id = BE_R5_PROTECTED_SAVED_STATE_ID;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.saved_state_pa = BE_R5_PROTECTED_SAVED_PA;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.vsatp = 1U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
	r4 = valid_r4();
	r4.active.published = 0U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_IMPORT);
}

static void test_import_observation_rejections(void)
{
	struct be_r4_state r4 = valid_r4();
	struct be_r4_frame frame = imported_frame();
	struct be_r5_observation observation;
	struct be_r5_state state = BE_R5_STATE_INITIALIZER;

	SCENARIO();
	observation = import_observation();
	observation.hart_id = BE_CONFIGURATION_HART_ID + 1U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_HART);

	observation = import_observation();
	observation.active.root_id = BE_R5_PROTECTED_ROOT_ID;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_BINDING);
	observation = import_observation();
	observation.active.published = 0U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_BINDING);

	observation = import_observation();
	observation.current_hgatp = BE_R3_PROTECTED_HGATP;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_HGATP);

	observation = import_observation();
	observation.hstatus =
		BE_R3_HSTATUS_CONTROL_VALUE & ~BE_R3_HSTATUS_SPV;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_VS_ORIGIN);
	observation = import_observation();
	observation.hstatus =
		BE_R3_HSTATUS_CONTROL_VALUE & ~BE_R3_HSTATUS_VTVM;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_VS_ORIGIN);
	observation = import_observation();
	observation.hstatus = BE_R3_HSTATUS_CONTROL_VALUE | BE_R3_HSTATUS_HU;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_VS_ORIGIN);
	observation = import_observation();
	observation.hstatus =
		BE_R3_HSTATUS_CONTROL_VALUE | BE_R3_HSTATUS_VGEIN_MASK;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_VS_ORIGIN);

	/* GVA is outside the control mask and never rejects a valid exit */
	observation = import_observation();
	observation.hstatus = BE_R3_HSTATUS_CONTROL_VALUE | BE_R3_HSTATUS_GVA;
	CHECK(be_r5_import_r4_complete(&state, &r4, &frame, &observation) ==
	      BE_R5_ERROR_NONE);
	CHECK(state.phase == BE_R5_PHASE_IMPORT_R4_COMPLETE);

	observation = import_observation();
	observation.vsatp = 1U;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_VSATP);

	observation = import_observation();
	observation.trusted_sp = BE_R5_PROTECTED_TRUSTED_SP;
	expect_import_rejected(r4, frame, observation,
			       BE_R5_ERROR_TRUSTED_STACK);
	observation = import_observation();
	observation.saved_state_pa = BE_R5_PROTECTED_SAVED_PA;
	expect_import_rejected(r4, frame, observation,
			       BE_R5_ERROR_SAVED_PAGE);

	observation = import_observation();
	observation.management_private_value = BE_R5_PROTECTED_PRIVATE_VALUE;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_BACKING);
	observation = import_observation();
	observation.protected_private_value = BE_R5_PROTECTED_PRIVATE_VALUE;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_BACKING);
	observation = import_observation();
	observation.shared_value = BE_R5_DENIED_STORE_CANDIDATE;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_BACKING);
}

static void test_import_frame_rejections(void)
{
	struct be_r4_state r4 = valid_r4();
	struct be_r4_frame frame;
	struct be_r5_observation observation = import_observation();

	SCENARIO();
	frame = imported_frame();
	frame.reserved = 1U;
	expect_import_rejected(r4, frame, observation,
			       BE_R5_ERROR_FRAME_RESERVED);

	frame = imported_frame();
	frame.scause |= BE_R4_INTERRUPT_BIT;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_INTERRUPT);
	frame = imported_frame();
	frame.scause = BE_R4_SCAUSE_LOAD_GUEST_PAGE_FAULT;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_CAUSE);
	frame = imported_frame();
	frame.scause = BE_R4_SCAUSE_VIRTUAL_INSTRUCTION;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_CAUSE);

	frame = imported_frame();
	frame.sepc = BE_R4_EVENT_PC;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_PC);
	frame = imported_frame();
	frame.sepc = BE_R5_MANAGEMENT_FINAL_EVENT_PC;
	expect_import_rejected(r4, frame, observation, BE_R5_ERROR_PC);

	frame = imported_frame();
	frame.stval = BE_R4_DENIED_GVA;
	expect_import_rejected(r4, frame, observation,
			       BE_R5_ERROR_TRAP_METADATA);
	frame = imported_frame();
	frame.htval = BE_R4_DENIED_HTVAL;
	expect_import_rejected(r4, frame, observation,
			       BE_R5_ERROR_TRAP_METADATA);

	frame = imported_frame();
	frame.gpr[BE_R4_GPR_A7] = BE_R5_PROTECTED_EVENT_ID;
	expect_import_rejected(r4, frame, observation,
			       BE_R5_ERROR_EVENT_ARGS);
	frame = imported_frame();
	frame.gpr[BE_R4_GPR_A6] = 1U;
	expect_import_rejected(r4, frame, observation,
			       BE_R5_ERROR_EVENT_ARGS);
	frame = imported_frame();
	frame.gpr[BE_R4_GPR_A0] = BE_R5_PROTECTED_PRIVATE_VALUE;
	expect_import_rejected(r4, frame, observation,
			       BE_R5_ERROR_EVENT_ARGS);
	frame = imported_frame();
	frame.gpr[BE_R4_GPR_A1] = BE_R5_DENIED_STORE_CANDIDATE;
	expect_import_rejected(r4, frame, observation,
			       BE_R5_ERROR_EVENT_ARGS);
	frame = imported_frame();
	frame.gpr[BE_R5_GPR_S0] = 0U;
	expect_import_rejected(r4, frame, observation,
			       BE_R5_ERROR_EVENT_ARGS);
}

static void test_import_nulls_and_replay(void)
{
	struct be_r4_state r4 = valid_r4();
	struct be_r4_frame frame = imported_frame();
	struct be_r5_observation observation = import_observation();
	struct be_r5_state state = BE_R5_STATE_INITIALIZER;

	SCENARIO();
	CHECK(be_r5_import_r4_complete((struct be_r5_state *)0, &r4, &frame,
				       &observation) == BE_R5_ERROR_NULL);

	CHECK(be_r5_import_r4_complete(&state, (const struct be_r4_state *)0,
				       &frame, &observation) ==
	      BE_R5_ERROR_NULL);
	check_terminal(&state, BE_R5_ERROR_NULL);

	state = (struct be_r5_state)BE_R5_STATE_INITIALIZER;
	CHECK(be_r5_import_r4_complete(&state, &r4,
				       (const struct be_r4_frame *)0,
				       &observation) == BE_R5_ERROR_NULL);
	check_terminal(&state, BE_R5_ERROR_NULL);

	state = (struct be_r5_state)BE_R5_STATE_INITIALIZER;
	CHECK(be_r5_import_r4_complete(&state, &r4, &frame,
				       (const struct be_r5_observation *)0) ==
	      BE_R5_ERROR_NULL);
	check_terminal(&state, BE_R5_ERROR_NULL);

	/* exactly one import is admitted */
	state = (struct be_r5_state)BE_R5_STATE_INITIALIZER;
	CHECK(be_r5_import_r4_complete(&state, &r4, &frame, &observation) ==
	      BE_R5_ERROR_NONE);
	CHECK(be_r5_import_r4_complete(&state, &r4, &frame, &observation) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&state, BE_R5_ERROR_INVALID_PHASE);
}

static void expect_prepare_rejected(struct world world,
				    enum be_r5_direction direction,
				    enum be_r5_error error)
{
	struct be_r5_pending pending;

	memset(&pending, 0, sizeof(pending));
	CHECK(be_r5_prepare_pending(&world.state, direction, &pending) ==
	      error);
	CHECK(pending_is_zero(&pending));
	check_terminal(&world.state, error);
}

static void test_prepare_wrong_phase(void)
{
	SCENARIO();
	expect_prepare_rejected(fresh_world(),
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(pending_protected_world(),
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(fenced_protected_world(),
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(protected_running_world(),
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(protected_store_world(),
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(pending_management_world(),
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(fenced_management_world(),
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(management_running_world(),
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(complete_world(),
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
}

static void test_prepare_wrong_direction_and_witness(void)
{
	struct world world;

	SCENARIO();
	expect_prepare_rejected(imported_world(), BE_R5_DIRECTION_NONE,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(imported_world(),
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(imported_world(),
				(enum be_r5_direction)99,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(switch_requested_world(),
				BE_R5_DIRECTION_NONE,
				BE_R5_ERROR_INVALID_PHASE);
	expect_prepare_rejected(switch_requested_world(),
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_INVALID_PHASE);

	world = imported_world();
	world.state.exit_count = 1U;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_INVALID_PHASE);
	world = imported_world();
	world.state.switch_count = 1U;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_INVALID_PHASE);
	world = imported_world();
	world.state.switch_requested = 1U;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_INVALID_PHASE);
	world = imported_world();
	world.state.protected_saved_pc = BE_R5_PROTECTED_SAVED_PC;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_INVALID_PHASE);

	world = switch_requested_world();
	world.state.protected_saved_pc = 0U;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
	world = switch_requested_world();
	world.state.protected_saved_pc = BE_R5_PROTECTED_EVENT_PC;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
	world = switch_requested_world();
	world.state.switch_requested = 0U;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
	world = switch_requested_world();
	world.state.exit_count = 2U;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
	world = switch_requested_world();
	world.state.switch_count = 2U;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_INVALID_PHASE);
}

static void test_prepare_corruption(void)
{
	struct world world;
	struct be_r5_pending pending;

	SCENARIO();
	memset(&pending, 0, sizeof(pending));
	world = imported_world();
	CHECK(be_r5_prepare_pending(&world.state,
				    BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				    (struct be_r5_pending *)0) ==
	      BE_R5_ERROR_NULL);
	check_terminal(&world.state, BE_R5_ERROR_NULL);
	CHECK(be_r5_prepare_pending((struct be_r5_state *)0,
				    BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				    &pending) == BE_R5_ERROR_NULL);

	world = imported_world();
	world.state.configuration_id = 0U;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_IMPORT);
	world = imported_world();
	world.state.management_hgatp = BE_R3_PROTECTED_HGATP;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_IMPORT);
	world = imported_world();
	world.state.protected_hgatp = BE_R3_MANAGEMENT_HGATP;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_IMPORT);

	world = imported_world();
	world.state.pending.direction =
		BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_PENDING);
	world = imported_world();
	world.state.pending.target = protected_binding_value(0U);
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_PENDING);
	world = switch_requested_world();
	world.state.pending.frame_mode = BE_R5_FRAME_MODE_SAVED;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_PENDING);

	world = imported_world();
	world.state.active.root_id = BE_R5_PROTECTED_ROOT_ID;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				BE_R5_ERROR_BINDING);
	world = switch_requested_world();
	world.state.active.saved_state_pa = BE_R3_MANAGEMENT_SAVED_PA;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_BINDING);

	/* the retained management frame is revalidated at every use */
	world = switch_requested_world();
	world.state.management_frame.sepc = BE_R5_MANAGEMENT_FINAL_EVENT_PC;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_FRAME_STATE);
	world = switch_requested_world();
	world.state.management_frame.reserved = 1U;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_FRAME_STATE);
	world = switch_requested_world();
	world.state.management_frame.gpr[BE_R5_GPR_S0] = 0U;
	expect_prepare_rejected(world,
				BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				BE_R5_ERROR_FRAME_STATE);
}

static void expect_fence_rejected(struct world world,
				  struct be_r5_fence_ack ack,
				  enum be_r5_error error)
{
	CHECK(be_r5_note_target_fenced(&world.state, &ack) == error);
	check_terminal(&world.state, error);
}

static void test_fence_wrong_phase(void)
{
	struct be_r5_fence_ack ack = protected_fence_ack();
	struct world world = pending_protected_world();

	SCENARIO();
	expect_fence_rejected(fresh_world(), ack,
			      BE_R5_ERROR_INVALID_PHASE);
	expect_fence_rejected(imported_world(), ack,
			      BE_R5_ERROR_INVALID_PHASE);
	expect_fence_rejected(protected_running_world(), ack,
			      BE_R5_ERROR_INVALID_PHASE);
	expect_fence_rejected(protected_store_world(), ack,
			      BE_R5_ERROR_INVALID_PHASE);
	expect_fence_rejected(switch_requested_world(), ack,
			      BE_R5_ERROR_INVALID_PHASE);
	expect_fence_rejected(management_running_world(),
			      management_fence_ack(),
			      BE_R5_ERROR_INVALID_PHASE);
	expect_fence_rejected(complete_world(), management_fence_ack(),
			      BE_R5_ERROR_INVALID_PHASE);

	/* the acknowledgement may not be replayed once it has been accepted */
	CHECK(be_r5_note_target_fenced(&world.state, &ack) ==
	      BE_R5_ERROR_NONE);
	CHECK(be_r5_note_target_fenced(&world.state, &ack) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
}

static void test_fence_evidence_rejections(void)
{
	struct be_r5_fence_ack ack;
	struct world world;

	SCENARIO();
	world = pending_protected_world();
	CHECK(be_r5_note_target_fenced(&world.state,
				       (const struct be_r5_fence_ack *)0) ==
	      BE_R5_ERROR_NULL);
	check_terminal(&world.state, BE_R5_ERROR_NULL);
	ack = protected_fence_ack();
	CHECK(be_r5_note_target_fenced((struct be_r5_state *)0, &ack) ==
	      BE_R5_ERROR_NULL);

	ack = protected_fence_ack();
	ack.source_hgatp = BE_R3_PROTECTED_HGATP;
	expect_fence_rejected(pending_protected_world(), ack,
			      BE_R5_ERROR_HGATP);
	ack = protected_fence_ack();
	ack.virtualization_off = 0U;
	expect_fence_rejected(pending_protected_world(), ack,
			      BE_R5_ERROR_FENCE);
	ack = protected_fence_ack();
	ack.virtualization_off = 2U;
	expect_fence_rejected(pending_protected_world(), ack,
			      BE_R5_ERROR_FENCE);
	ack = protected_fence_ack();
	ack.fence_completed = 0U;
	expect_fence_rejected(pending_protected_world(), ack,
			      BE_R5_ERROR_FENCE);
	ack = protected_fence_ack();
	ack.fence_completed = 2U;
	expect_fence_rejected(pending_protected_world(), ack,
			      BE_R5_ERROR_FENCE);
	ack = protected_fence_ack();
	ack.hgatp_written = BE_R3_MANAGEMENT_HGATP;
	expect_fence_rejected(pending_protected_world(), ack,
			      BE_R5_ERROR_TARGET_READBACK);
	ack = protected_fence_ack();
	ack.hgatp_readback = BE_R3_MANAGEMENT_HGATP;
	expect_fence_rejected(pending_protected_world(), ack,
			      BE_R5_ERROR_TARGET_READBACK);
	ack = protected_fence_ack();
	ack.hgatp_readback = 0U;
	expect_fence_rejected(pending_protected_world(), ack,
			      BE_R5_ERROR_TARGET_READBACK);

	/* the same evidence rules hold for the return switch */
	ack = management_fence_ack();
	ack.source_hgatp = BE_R3_MANAGEMENT_HGATP;
	expect_fence_rejected(pending_management_world(), ack,
			      BE_R5_ERROR_HGATP);
	ack = management_fence_ack();
	ack.fence_completed = 0U;
	expect_fence_rejected(pending_management_world(), ack,
			      BE_R5_ERROR_FENCE);
	ack = management_fence_ack();
	ack.hgatp_written = BE_R3_PROTECTED_HGATP;
	expect_fence_rejected(pending_management_world(), ack,
			      BE_R5_ERROR_TARGET_READBACK);
	/* a protected acknowledgement cannot satisfy the return switch */
	expect_fence_rejected(pending_management_world(),
			      protected_fence_ack(), BE_R5_ERROR_HGATP);
}

static void test_fence_state_corruption(void)
{
	struct be_r5_fence_ack ack = protected_fence_ack();
	struct world world;

	SCENARIO();
	world = pending_protected_world();
	world.state.configuration_id = 0U;
	expect_fence_rejected(world, ack, BE_R5_ERROR_IMPORT);
	world = pending_protected_world();
	world.state.protected_hgatp = 0U;
	expect_fence_rejected(world, ack, BE_R5_ERROR_IMPORT);

	world = pending_protected_world();
	world.state.pending.frame_mode = BE_R5_FRAME_MODE_SAVED;
	expect_fence_rejected(world, ack, BE_R5_ERROR_PENDING);
	world = pending_protected_world();
	world.state.pending.target.vcpu_id = 1U;
	expect_fence_rejected(world, ack, BE_R5_ERROR_PENDING);
	world = pending_protected_world();
	world.state.pending.target.published = 1U;
	expect_fence_rejected(world, ack, BE_R5_ERROR_PENDING);
	world = pending_protected_world();
	world.state.pending.source.published = 0U;
	expect_fence_rejected(world, ack, BE_R5_ERROR_PENDING);

	/* a source that no longer matches the published active binding */
	world = pending_protected_world();
	world.state.active.vcpu_id = BE_R5_PROTECTED_VCPU_ID;
	world.state.pending.source.vcpu_id = BE_R5_PROTECTED_VCPU_ID;
	expect_fence_rejected(world, ack, BE_R5_ERROR_PENDING);
	world = pending_protected_world();
	world.state.active.guest_pc = BE_R5_PROTECTED_ENTRY_PC;
	expect_fence_rejected(world, ack, BE_R5_ERROR_BINDING);
}

static void expect_publish_rejected(struct world world,
				    struct be_r5_entry_state entry,
				    struct be_r4_frame frame,
				    enum be_r5_error error)
{
	struct be_r4_frame before = frame;
	struct be_r5_transition transition;

	memset(&transition, 0, sizeof(transition));
	CHECK(be_r5_publish_target(&world.state, &entry, &frame,
				   &transition) == error);
	CHECK(frames_equal(&frame, &before));
	CHECK(transition.action == BE_R5_ACTION_NONE);
	CHECK(transition.direction == BE_R5_DIRECTION_NONE);
	CHECK(binding_is_zero(&transition.active));
	check_terminal(&world.state, error);
}

static void test_publish_wrong_phase(void)
{
	struct be_r5_entry_state entry = protected_entry_state();
	struct be_r4_frame frame;
	struct be_r5_transition transition;
	struct world world;

	SCENARIO();
	memset(&frame, 0, sizeof(frame));
	expect_publish_rejected(fresh_world(), entry, frame,
				BE_R5_ERROR_INVALID_PHASE);
	expect_publish_rejected(imported_world(), entry, frame,
				BE_R5_ERROR_INVALID_PHASE);
	expect_publish_rejected(pending_protected_world(), entry, frame,
				BE_R5_ERROR_INVALID_PHASE);
	expect_publish_rejected(protected_running_world(), entry, frame,
				BE_R5_ERROR_INVALID_PHASE);
	expect_publish_rejected(protected_store_world(), entry, frame,
				BE_R5_ERROR_INVALID_PHASE);
	expect_publish_rejected(switch_requested_world(), entry, frame,
				BE_R5_ERROR_INVALID_PHASE);
	expect_publish_rejected(pending_management_world(),
				management_entry_state(), imported_frame(),
				BE_R5_ERROR_INVALID_PHASE);
	expect_publish_rejected(management_running_world(),
				management_entry_state(), imported_frame(),
				BE_R5_ERROR_INVALID_PHASE);
	expect_publish_rejected(complete_world(), management_entry_state(),
				imported_frame(), BE_R5_ERROR_INVALID_PHASE);

	/* publication is a single-shot step */
	world = fenced_protected_world();
	memset(&transition, 0, sizeof(transition));
	CHECK(be_r5_publish_target(&world.state, &entry, &frame,
				   &transition) == BE_R5_ERROR_NONE);
	CHECK(be_r5_publish_target(&world.state, &entry, &frame,
				   &transition) == BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
}

static void test_publish_nulls(void)
{
	struct be_r5_entry_state entry = protected_entry_state();
	struct be_r5_transition transition;
	struct be_r4_frame frame;
	struct world world;

	SCENARIO();
	memset(&frame, 0, sizeof(frame));
	memset(&transition, 0, sizeof(transition));
	CHECK(be_r5_publish_target((struct be_r5_state *)0, &entry, &frame,
				   &transition) == BE_R5_ERROR_NULL);

	world = fenced_protected_world();
	CHECK(be_r5_publish_target(&world.state,
				   (const struct be_r5_entry_state *)0,
				   &frame, &transition) == BE_R5_ERROR_NULL);
	check_terminal(&world.state, BE_R5_ERROR_NULL);

	world = fenced_protected_world();
	CHECK(be_r5_publish_target(&world.state, &entry,
				   (struct be_r4_frame *)0, &transition) ==
	      BE_R5_ERROR_NULL);
	check_terminal(&world.state, BE_R5_ERROR_NULL);

	world = fenced_protected_world();
	CHECK(be_r5_publish_target(&world.state, &entry, &frame,
				   (struct be_r5_transition *)0) ==
	      BE_R5_ERROR_NULL);
	check_terminal(&world.state, BE_R5_ERROR_NULL);
}

static void test_publish_entry_rejections(void)
{
	struct be_r5_entry_state entry;
	struct be_r4_frame frame;

	SCENARIO();
	memset(&frame, 0, sizeof(frame));

	entry = protected_entry_state();
	entry.hgatp = BE_R3_MANAGEMENT_HGATP;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_TARGET_READBACK);
	entry = protected_entry_state();
	entry.hgatp = 0U;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_TARGET_READBACK);
	entry = protected_entry_state();
	entry.hstatus = 0U;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_ENTRY_CONTROLS);
	entry = protected_entry_state();
	entry.hstatus &= ~(be_u64)BE_R3_HSTATUS_SPV;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_ENTRY_CONTROLS);
	entry = protected_entry_state();
	entry.sstatus &= ~(be_u64)BE_R3_SSTATUS_SPP;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_ENTRY_CONTROLS);
	entry = protected_entry_state();
	entry.vsatp = 1U;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_VSATP);
	entry = protected_entry_state();
	entry.vstvec = BE_R5_PROTECTED_ENTRY_PC;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_TARGET_RESET);
	entry = protected_entry_state();
	entry.vsepc = 1U;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_TARGET_RESET);
	entry = protected_entry_state();
	entry.vscause = 1U;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_TARGET_RESET);
	entry = protected_entry_state();
	entry.vstval = 1U;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_TARGET_RESET);
	entry = protected_entry_state();
	entry.trusted_sp = BE_R3_INITIAL_TRUSTED_SP;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_TRUSTED_STACK);
	entry = protected_entry_state();
	entry.saved_state_pa = BE_R3_MANAGEMENT_SAVED_PA;
	expect_publish_rejected(fenced_protected_world(), entry, frame,
				BE_R5_ERROR_SAVED_PAGE);

	/* the management entry state cannot satisfy the protected switch */
	expect_publish_rejected(fenced_protected_world(),
				management_entry_state(), frame,
				BE_R5_ERROR_TARGET_READBACK);
	expect_publish_rejected(fenced_management_world(),
				protected_entry_state(), imported_frame(),
				BE_R5_ERROR_TARGET_READBACK);

	/* the same entry rules hold for the return switch */
	entry = management_entry_state();
	entry.sstatus = 0U;
	expect_publish_rejected(fenced_management_world(), entry,
				imported_frame(),
				BE_R5_ERROR_ENTRY_CONTROLS);
	entry = management_entry_state();
	entry.vscause = BE_R5_SCAUSE_STORE_GUEST_PAGE_FAULT;
	expect_publish_rejected(fenced_management_world(), entry,
				imported_frame(), BE_R5_ERROR_TARGET_RESET);
	entry = management_entry_state();
	entry.trusted_sp = BE_R5_PROTECTED_TRUSTED_SP;
	expect_publish_rejected(fenced_management_world(), entry,
				imported_frame(),
				BE_R5_ERROR_TRUSTED_STACK);
	entry = management_entry_state();
	entry.saved_state_pa = BE_R5_PROTECTED_SAVED_PA;
	expect_publish_rejected(fenced_management_world(), entry,
				imported_frame(), BE_R5_ERROR_SAVED_PAGE);

	/* a GVA report from the recorded trap does not disturb entry */
	entry = protected_entry_state();
	entry.hstatus |= (be_u64)BE_R3_HSTATUS_GVA;
	{
		struct world world = fenced_protected_world();
		struct be_r5_transition transition;

		memset(&transition, 0, sizeof(transition));
		CHECK(be_r5_publish_target(&world.state, &entry, &frame,
					   &transition) == BE_R5_ERROR_NONE);
		CHECK(world.state.phase ==
		      BE_R5_PHASE_PROTECTED_PUBLISHED_EXPECT_LOAD_FAULT);
	}
}

static void test_publish_state_corruption(void)
{
	struct be_r5_entry_state entry = protected_entry_state();
	struct be_r4_frame frame;
	struct world world;

	SCENARIO();
	memset(&frame, 0, sizeof(frame));

	world = fenced_protected_world();
	world.state.configuration_id = 0U;
	expect_publish_rejected(world, entry, frame, BE_R5_ERROR_IMPORT);
	world = fenced_protected_world();
	world.state.management_hgatp = 0U;
	expect_publish_rejected(world, entry, frame, BE_R5_ERROR_IMPORT);

	world = fenced_protected_world();
	world.state.pending.frame_mode = BE_R5_FRAME_MODE_SAVED;
	expect_publish_rejected(world, entry, frame, BE_R5_ERROR_PENDING);
	world = fenced_protected_world();
	world.state.pending.direction =
		BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT;
	expect_publish_rejected(world, entry, frame, BE_R5_ERROR_PENDING);
	world = fenced_protected_world();
	world.state.pending.target.hgatp = BE_R3_MANAGEMENT_HGATP;
	expect_publish_rejected(world, entry, frame, BE_R5_ERROR_PENDING);
	world = fenced_management_world();
	world.state.pending.frame_mode = BE_R5_FRAME_MODE_INITIAL;
	expect_publish_rejected(world, management_entry_state(),
				imported_frame(), BE_R5_ERROR_PENDING);

	world = fenced_protected_world();
	world.state.active.guest_sp = 0U;
	expect_publish_rejected(world, entry, frame, BE_R5_ERROR_BINDING);

	world = fenced_protected_world();
	world.state.active.published = 0U;
	expect_publish_rejected(world, entry, frame, BE_R5_ERROR_BINDING);
	world = fenced_protected_world();
	world.state.pending.source.published = 0U;
	expect_publish_rejected(world, entry, frame, BE_R5_ERROR_PENDING);
	world = fenced_protected_world();
	world.state.switch_count = 1U;
	expect_publish_rejected(world, entry, frame,
				BE_R5_ERROR_PUBLICATION);
	world = fenced_management_world();
	world.state.switch_count = 0U;
	expect_publish_rejected(world, management_entry_state(),
				imported_frame(), BE_R5_ERROR_PUBLICATION);
	world = fenced_management_world();
	world.state.switch_count = 2U;
	expect_publish_rejected(world, management_entry_state(),
				imported_frame(), BE_R5_ERROR_PUBLICATION);
	world = fenced_management_world();
	world.state.pending.target.published = 1U;
	expect_publish_rejected(world, management_entry_state(),
				imported_frame(), BE_R5_ERROR_PENDING);
}

static void test_publish_frame_rejections(void)
{
	struct be_r4_frame frame;
	struct world world;

	SCENARIO();
	/* the saved management page must match the retained frame exactly */
	frame = imported_frame();
	frame.gpr[BE_R5_GPR_S0] = 0U;
	expect_publish_rejected(fenced_management_world(),
				management_entry_state(), frame,
				BE_R5_ERROR_FRAME_STATE);
	frame = imported_frame();
	frame.sepc = BE_R5_MANAGEMENT_FINAL_EVENT_PC;
	expect_publish_rejected(fenced_management_world(),
				management_entry_state(), frame,
				BE_R5_ERROR_FRAME_STATE);
	frame = imported_frame();
	frame.reserved = 1U;
	expect_publish_rejected(fenced_management_world(),
				management_entry_state(), frame,
				BE_R5_ERROR_FRAME_STATE);
	expect_publish_rejected(fenced_management_world(),
				management_entry_state(), patterned_frame(),
				BE_R5_ERROR_FRAME_STATE);

	/* a tampered retained frame is rejected before the page compare */
	world = fenced_management_world();
	world.state.management_frame.gpr[BE_R4_GPR_INDEX(10U)] = 0U;
	expect_publish_rejected(world, management_entry_state(),
				world.state.management_frame,
				BE_R5_ERROR_FRAME_STATE);
	world = fenced_management_world();
	world.state.management_frame.scause = 0U;
	expect_publish_rejected(world, management_entry_state(),
				world.state.management_frame,
				BE_R5_ERROR_FRAME_STATE);
}

static void expect_exit_rejected(struct world world, struct be_r4_frame frame,
				 struct be_r5_observation observation,
				 enum be_r5_error error)
{
	struct be_r4_frame before = frame;
	struct be_r5_result result;

	memset(&result, 0, sizeof(result));
	CHECK(be_r5_handle_exit(&world.state, &frame, &observation,
				&result) == error);
	CHECK(frames_equal(&frame, &before));
	CHECK(result.action == BE_R5_ACTION_NONE);
	CHECK(result.exit_class == BE_R5_EXIT_NONE);
	CHECK(result.advanced_pc == 0U);
	CHECK(binding_is_zero(&result.active));
	check_terminal(&world.state, error);
}

static void test_exit_wrong_phase(void)
{
	struct be_r4_frame frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	struct be_r5_observation observation = protected_observation();

	SCENARIO();
	expect_exit_rejected(fresh_world(), frame, observation,
			     BE_R5_ERROR_INVALID_PHASE);
	expect_exit_rejected(imported_world(), frame, observation,
			     BE_R5_ERROR_INVALID_PHASE);
	expect_exit_rejected(pending_protected_world(), frame, observation,
			     BE_R5_ERROR_INVALID_PHASE);
	expect_exit_rejected(fenced_protected_world(), frame, observation,
			     BE_R5_ERROR_INVALID_PHASE);
	expect_exit_rejected(pending_management_world(), final_event_frame(),
			     management_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
	expect_exit_rejected(fenced_management_world(), final_event_frame(),
			     management_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
	expect_exit_rejected(complete_world(), final_event_frame(),
			     management_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
}

static void test_exit_nulls(void)
{
	struct be_r5_observation observation = protected_observation();
	struct be_r4_frame frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	struct be_r5_result result;
	struct world world;

	SCENARIO();
	memset(&result, 0, sizeof(result));
	CHECK(be_r5_handle_exit((struct be_r5_state *)0, &frame, &observation,
				&result) == BE_R5_ERROR_NULL);

	world = protected_running_world();
	CHECK(be_r5_handle_exit(&world.state, (struct be_r4_frame *)0,
				&observation, &result) == BE_R5_ERROR_NULL);
	check_terminal(&world.state, BE_R5_ERROR_NULL);

	world = protected_running_world();
	CHECK(be_r5_handle_exit(&world.state, &frame,
				(const struct be_r5_observation *)0,
				&result) == BE_R5_ERROR_NULL);
	check_terminal(&world.state, BE_R5_ERROR_NULL);

	world = protected_running_world();
	CHECK(be_r5_handle_exit(&world.state, &frame, &observation,
				(struct be_r5_result *)0) ==
	      BE_R5_ERROR_NULL);
	check_terminal(&world.state, BE_R5_ERROR_NULL);
}

static void test_exit_denied_load_rejections(void)
{
	struct be_r5_observation observation;
	struct be_r4_frame frame;

	SCENARIO();
	frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.scause = BE_R5_SCAUSE_STORE_GUEST_PAGE_FAULT;
	expect_exit_rejected(protected_running_world(), frame,
			     protected_observation(), BE_R5_ERROR_CAUSE);
	frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.scause = BE_R4_SCAUSE_VS_ECALL;
	expect_exit_rejected(protected_running_world(), frame,
			     protected_observation(), BE_R5_ERROR_CAUSE);
	frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.scause |= BE_R4_INTERRUPT_BIT;
	expect_exit_rejected(protected_running_world(), frame,
			     protected_observation(), BE_R5_ERROR_INTERRUPT);
	frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.sepc = BE_R5_PROTECTED_STORE_FAULT_PC;
	expect_exit_rejected(protected_running_world(), frame,
			     protected_observation(), BE_R5_ERROR_PC);
	frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.stval = BE_R5_SHARED_STORE_DENIED_GVA;
	expect_exit_rejected(protected_running_world(), frame,
			     protected_observation(), BE_R5_ERROR_GVA);
	frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.htval = BE_U64_C(0x4000000000000000);
	expect_exit_rejected(protected_running_world(), frame,
			     protected_observation(),
			     BE_R5_ERROR_HTVAL_OVERFLOW);
	frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.htval = ~BE_U64_C(0);
	expect_exit_rejected(protected_running_world(), frame,
			     protected_observation(),
			     BE_R5_ERROR_HTVAL_OVERFLOW);
	frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.htval = BE_R5_SHARED_STORE_DENIED_GPA >> 2;
	expect_exit_rejected(protected_running_world(), frame,
			     protected_observation(), BE_R5_ERROR_GPA);
	frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.reserved = 1U;
	expect_exit_rejected(protected_running_world(), frame,
			     protected_observation(),
			     BE_R5_ERROR_FRAME_RESERVED);

	/* an unreported guest physical address is tolerated, not invented */
	{
		struct world world = protected_running_world();
		struct be_r5_result result;

		memset(&result, 0, sizeof(result));
		frame = protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
		frame.htval = 0U;
		observation = protected_observation();
		CHECK(be_r5_handle_exit(&world.state, &frame, &observation,
					&result) == BE_R5_ERROR_NONE);
		CHECK(result.exit_class == BE_R5_EXIT_PROTECTED_DENIED_LOAD);
		CHECK(frame.sepc == BE_R5_PROTECTED_LOAD_RESUME_PC);
	}
}

static void test_exit_denied_store_rejections(void)
{
	struct be_r4_frame frame;

	SCENARIO();
	frame = protected_store_fault_frame(BE_R5_SHARED_STORE_DENIED_HTVAL);
	frame.scause = BE_R4_SCAUSE_LOAD_GUEST_PAGE_FAULT;
	expect_exit_rejected(protected_store_world(), frame,
			     protected_observation(), BE_R5_ERROR_CAUSE);
	frame = protected_store_fault_frame(BE_R5_SHARED_STORE_DENIED_HTVAL);
	frame.sepc = BE_R5_PROTECTED_LOAD_FAULT_PC;
	expect_exit_rejected(protected_store_world(), frame,
			     protected_observation(), BE_R5_ERROR_PC);
	frame = protected_store_fault_frame(BE_R5_SHARED_STORE_DENIED_HTVAL);
	frame.stval = BE_R5_PROTECTED_LOAD_DENIED_GVA;
	expect_exit_rejected(protected_store_world(), frame,
			     protected_observation(), BE_R5_ERROR_GVA);
	frame = protected_store_fault_frame(BE_R5_SHARED_STORE_DENIED_HTVAL);
	frame.htval = BE_R5_PROTECTED_LOAD_DENIED_GPA >> 2;
	expect_exit_rejected(protected_store_world(), frame,
			     protected_observation(), BE_R5_ERROR_GPA);
	frame = protected_store_fault_frame(BE_R5_SHARED_STORE_DENIED_HTVAL);
	frame.reserved = ~BE_U64_C(0);
	expect_exit_rejected(protected_store_world(), frame,
			     protected_observation(),
			     BE_R5_ERROR_FRAME_RESERVED);

	/* the load-fault frame cannot satisfy the shared store step */
	expect_exit_rejected(protected_store_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     protected_observation(), BE_R5_ERROR_CAUSE);
	/* and the store-fault frame cannot satisfy the load step */
	expect_exit_rejected(protected_running_world(),
			     protected_store_fault_frame(BE_R5_SHARED_STORE_DENIED_HTVAL),
			     protected_observation(), BE_R5_ERROR_CAUSE);
}

static void test_exit_event_rejections(void)
{
	struct be_r4_frame frame;

	SCENARIO();
	frame = protected_event_frame();
	frame.scause = BE_R4_SCAUSE_LOAD_GUEST_PAGE_FAULT;
	expect_exit_rejected(protected_event_world(), frame,
			     protected_observation(), BE_R5_ERROR_CAUSE);
	frame = protected_event_frame();
	frame.sepc = BE_R5_PROTECTED_STORE_FAULT_PC;
	expect_exit_rejected(protected_event_world(), frame,
			     protected_observation(), BE_R5_ERROR_PC);
	frame = protected_event_frame();
	frame.stval = 1U;
	expect_exit_rejected(protected_event_world(), frame,
			     protected_observation(),
			     BE_R5_ERROR_TRAP_METADATA);
	frame = protected_event_frame();
	frame.htval = 1U;
	expect_exit_rejected(protected_event_world(), frame,
			     protected_observation(),
			     BE_R5_ERROR_TRAP_METADATA);
	frame = protected_event_frame();
	frame.gpr[BE_R4_GPR_A7] = BE_R5_FINAL_EVENT_ID;
	expect_exit_rejected(protected_event_world(), frame,
			     protected_observation(),
			     BE_R5_ERROR_EVENT_ARGS);
	frame = protected_event_frame();
	frame.gpr[BE_R4_GPR_A6] = 1U;
	expect_exit_rejected(protected_event_world(), frame,
			     protected_observation(),
			     BE_R5_ERROR_EVENT_ARGS);
	frame = protected_event_frame();
	frame.gpr[BE_R4_GPR_A0] = BE_R4_PRIVATE_VALUE;
	expect_exit_rejected(protected_event_world(), frame,
			     protected_observation(),
			     BE_R5_ERROR_EVENT_ARGS);
	frame = protected_event_frame();
	frame.gpr[BE_R4_GPR_A1] = BE_R5_DENIED_STORE_CANDIDATE;
	expect_exit_rejected(protected_event_world(), frame,
			     protected_observation(),
			     BE_R5_ERROR_EVENT_ARGS);

	/* the final management event has its own identity and witness */
	frame = final_event_frame();
	frame.gpr[BE_R4_GPR_A7] = BE_R5_PROTECTED_EVENT_ID;
	expect_exit_rejected(management_running_world(), frame,
			     management_observation(),
			     BE_R5_ERROR_EVENT_ARGS);
	frame = final_event_frame();
	frame.gpr[BE_R4_GPR_A0] = BE_R5_PROTECTED_PRIVATE_VALUE;
	expect_exit_rejected(management_running_world(), frame,
			     management_observation(),
			     BE_R5_ERROR_EVENT_ARGS);
	frame = final_event_frame();
	frame.gpr[BE_R5_GPR_S0] = BE_R5_PROTECTED_PRIVATE_VALUE;
	expect_exit_rejected(management_running_world(), frame,
			     management_observation(),
			     BE_R5_ERROR_EVENT_ARGS);
	frame = final_event_frame();
	frame.sepc = BE_R5_MANAGEMENT_RESTORE_PC;
	expect_exit_rejected(management_running_world(), frame,
			     management_observation(), BE_R5_ERROR_PC);
	frame = final_event_frame();
	frame.scause = BE_R5_SCAUSE_STORE_GUEST_PAGE_FAULT;
	expect_exit_rejected(management_running_world(), frame,
			     management_observation(), BE_R5_ERROR_CAUSE);
	expect_exit_rejected(management_running_world(),
			     protected_event_frame(),
			     management_observation(), BE_R5_ERROR_PC);
	expect_exit_rejected(protected_event_world(), final_event_frame(),
			     protected_observation(), BE_R5_ERROR_PC);
}

static void test_exit_observation_rejections(void)
{
	struct be_r5_observation observation;

	SCENARIO();
	observation = protected_observation();
	observation.hart_id = 1U;
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL), observation,
			     BE_R5_ERROR_HART);
	observation = protected_observation();
	observation.current_hgatp = BE_R3_MANAGEMENT_HGATP;
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL), observation,
			     BE_R5_ERROR_HGATP);
	observation = protected_observation();
	observation.hstatus = 0U;
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL), observation,
			     BE_R5_ERROR_VS_ORIGIN);
	observation = protected_observation();
	observation.vsatp = 1U;
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL), observation,
			     BE_R5_ERROR_VSATP);
	observation = protected_observation();
	observation.trusted_sp = BE_R3_INITIAL_TRUSTED_SP;
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL), observation,
			     BE_R5_ERROR_TRUSTED_STACK);
	observation = protected_observation();
	observation.saved_state_pa = BE_R3_MANAGEMENT_SAVED_PA;
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL), observation,
			     BE_R5_ERROR_SAVED_PAGE);
	observation = protected_observation();
	observation.active = management_binding_value(1U);
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL), observation,
			     BE_R5_ERROR_BINDING);
	/* the management observation cannot report a protected exit */
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     management_observation(),
			     BE_R5_ERROR_BINDING);

	observation = protected_observation();
	observation.protected_private_value = BE_R4_PRIVATE_VALUE;
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL), observation,
			     BE_R5_ERROR_BACKING);
	observation = protected_observation();
	observation.shared_value = BE_R5_DENIED_STORE_CANDIDATE;
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL), observation,
			     BE_R5_ERROR_BACKING);
	observation = protected_observation();
	observation.management_private_value = 0U;
	expect_exit_rejected(protected_running_world(),
			     protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL), observation,
			     BE_R5_ERROR_BACKING);
	observation = management_observation();
	observation.shared_value = BE_R5_DENIED_STORE_CANDIDATE;
	expect_exit_rejected(management_running_world(), final_event_frame(),
			     observation, BE_R5_ERROR_BACKING);
	observation = management_observation();
	observation.management_private_value = 0U;
	expect_exit_rejected(management_running_world(), final_event_frame(),
			     observation, BE_R5_ERROR_BACKING);
}

static void test_exit_state_corruption(void)
{
	struct world world;

	SCENARIO();
	world = protected_running_world();
	world.state.configuration_id = 0U;
	expect_exit_rejected(world, protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     protected_observation(), BE_R5_ERROR_IMPORT);
	world = protected_running_world();
	world.state.protected_hgatp = 0U;
	expect_exit_rejected(world, protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     protected_observation(), BE_R5_ERROR_IMPORT);
	world = protected_running_world();
	world.state.pending.direction =
		BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT;
	expect_exit_rejected(world, protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     protected_observation(), BE_R5_ERROR_PENDING);
	world = protected_running_world();
	world.state.pending.target = management_binding_value(0U);
	expect_exit_rejected(world, protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     protected_observation(), BE_R5_ERROR_PENDING);
	world = protected_running_world();
	world.state.active = management_binding_value(1U);
	expect_exit_rejected(world, protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     protected_observation(), BE_R5_ERROR_BINDING);
	world = protected_running_world();
	world.state.active.published = 0U;
	expect_exit_rejected(world, protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     protected_observation(), BE_R5_ERROR_BINDING);
	world = management_running_world();
	world.state.active = protected_binding_value(1U);
	expect_exit_rejected(world, final_event_frame(),
			     management_observation(), BE_R5_ERROR_BINDING);

	/* the exit witnesses pin every step to its exact position */
	world = protected_running_world();
	world.state.exit_count = 1U;
	expect_exit_rejected(world, protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     protected_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
	world = protected_running_world();
	world.state.switch_count = 2U;
	expect_exit_rejected(world, protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     protected_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
	world = protected_running_world();
	world.state.switch_requested = 1U;
	expect_exit_rejected(world, protected_load_fault_frame(BE_R5_PROTECTED_LOAD_DENIED_HTVAL),
			     protected_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
	world = protected_store_world();
	world.state.exit_count = 0U;
	expect_exit_rejected(world, protected_store_fault_frame(BE_R5_SHARED_STORE_DENIED_HTVAL),
			     protected_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
	world = protected_event_world();
	world.state.exit_count = 3U;
	expect_exit_rejected(world, protected_event_frame(),
			     protected_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
	world = management_running_world();
	world.state.switch_requested = 0U;
	expect_exit_rejected(world, final_event_frame(),
			     management_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
	world = management_running_world();
	world.state.exit_count = 2U;
	expect_exit_rejected(world, final_event_frame(),
			     management_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
	world = management_running_world();
	world.state.switch_count = 1U;
	expect_exit_rejected(world, final_event_frame(),
			     management_observation(),
			     BE_R5_ERROR_INVALID_PHASE);
}

static void expect_shutdown_detail(long sbi_error, enum be_r5_error error,
				   enum be_r3_error detail)
{
	struct world world = complete_world();

	CHECK(be_r5_note_shutdown_returned(&world.state, sbi_error) == error);
	CHECK(world.state.phase == BE_R5_PHASE_FAILED);
	CHECK(world.state.error == error);
	CHECK(world.state.action == BE_R5_ACTION_TERMINAL);
	CHECK(world.state.shutdown_detail == detail);
	CHECK(binding_is_zero(&world.state.active));
	CHECK(pending_is_zero(&world.state.pending));
	CHECK(frame_is_zero(&world.state.management_frame));
	CHECK(world.state.configuration_id == 0U);
	CHECK(world.state.exit_count == 0U);
	CHECK(world.state.switch_count == 0U);
	check_sticky(&world.state, error);
}

static void test_shutdown_returned(void)
{
	struct world world;

	SCENARIO();
	/* a returning shutdown call is itself a bounded failure */
	expect_shutdown_detail(BE_R0_SBI_SUCCESS,
			       BE_R5_ERROR_SHUTDOWN_RETURNED,
			       BE_R3_ERROR_SRST_RETURNED);
	expect_shutdown_detail(BE_R0_SBI_ERR_FAILED,
			       BE_R5_ERROR_SHUTDOWN_REJECTED,
			       BE_R3_ERROR_SRST_FAILED);
	expect_shutdown_detail(BE_R0_SBI_ERR_NOT_SUPPORTED,
			       BE_R5_ERROR_SHUTDOWN_REJECTED,
			       BE_R3_ERROR_SRST_NOT_SUPPORTED);
	expect_shutdown_detail(BE_R0_SBI_ERR_INVALID_PARAM,
			       BE_R5_ERROR_SHUTDOWN_REJECTED,
			       BE_R3_ERROR_SRST_INVALID_PARAM);
	expect_shutdown_detail(BE_R0_SBI_ERR_DENIED,
			       BE_R5_ERROR_SHUTDOWN_REJECTED,
			       BE_R3_ERROR_SRST_DENIED);
	expect_shutdown_detail(BE_R0_SBI_ERR_INVALID_ADDRESS,
			       BE_R5_ERROR_SHUTDOWN_REJECTED,
			       BE_R3_ERROR_SRST_INVALID_ADDRESS);
	expect_shutdown_detail(-99, BE_R5_ERROR_SHUTDOWN_REJECTED,
			       BE_R3_ERROR_SRST_MALFORMED);
	expect_shutdown_detail(1, BE_R5_ERROR_SHUTDOWN_REJECTED,
			       BE_R3_ERROR_SRST_MALFORMED);

	/* the first recorded outcome is never replaced by a later report */
	world = complete_world();
	CHECK(be_r5_note_shutdown_returned(&world.state,
					   BE_R0_SBI_ERR_DENIED) ==
	      BE_R5_ERROR_SHUTDOWN_REJECTED);
	CHECK(be_r5_note_shutdown_returned(&world.state,
					   BE_R0_SBI_SUCCESS) ==
	      BE_R5_ERROR_SHUTDOWN_REJECTED);
	CHECK(world.state.shutdown_detail == BE_R3_ERROR_SRST_DENIED);
}

static void test_shutdown_wrong_phase(void)
{
	struct world world;

	SCENARIO();
	CHECK(be_r5_note_shutdown_returned((struct be_r5_state *)0, 0) ==
	      BE_R5_ERROR_NULL);

	world = fresh_world();
	CHECK(be_r5_note_shutdown_returned(&world.state, 0) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
	world = imported_world();
	CHECK(be_r5_note_shutdown_returned(&world.state, 0) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
	world = pending_protected_world();
	CHECK(be_r5_note_shutdown_returned(&world.state, 0) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
	world = fenced_protected_world();
	CHECK(be_r5_note_shutdown_returned(&world.state, 0) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
	world = protected_running_world();
	CHECK(be_r5_note_shutdown_returned(&world.state, 0) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
	world = protected_event_world();
	CHECK(be_r5_note_shutdown_returned(&world.state, 0) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
	world = switch_requested_world();
	CHECK(be_r5_note_shutdown_returned(&world.state, 0) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
	world = pending_management_world();
	CHECK(be_r5_note_shutdown_returned(&world.state, 0) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
	world = management_running_world();
	CHECK(be_r5_note_shutdown_returned(&world.state, 0) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);

	/* a completed run whose action was overwritten is not shutdown */
	world = complete_world();
	world.state.action = BE_R5_ACTION_ENTER_TARGET;
	CHECK(be_r5_note_shutdown_returned(&world.state, 0) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&world.state, BE_R5_ERROR_INVALID_PHASE);
}

static void test_explicit_failure(void)
{
	struct be_r5_state fresh = BE_R5_STATE_INITIALIZER;
	struct world world;

	SCENARIO();
	CHECK(be_r5_fail((struct be_r5_state *)0, BE_R5_ERROR_HGATP) ==
	      BE_R5_ERROR_HGATP);
	CHECK(be_r5_fail((struct be_r5_state *)0, BE_R5_ERROR_NONE) ==
	      BE_R5_ERROR_INVALID_PHASE);

	/* a caller cannot use the failure entry point to clear an error */
	CHECK(be_r5_fail(&fresh, BE_R5_ERROR_NONE) ==
	      BE_R5_ERROR_INVALID_PHASE);
	check_terminal(&fresh, BE_R5_ERROR_INVALID_PHASE);

	world = protected_running_world();
	CHECK(be_r5_fail(&world.state, BE_R5_ERROR_FENCE) ==
	      BE_R5_ERROR_FENCE);
	check_terminal(&world.state, BE_R5_ERROR_FENCE);
	CHECK(be_r5_fail(&world.state, BE_R5_ERROR_HART) ==
	      BE_R5_ERROR_FENCE);
	check_terminal(&world.state, BE_R5_ERROR_FENCE);

	world = complete_world();
	CHECK(be_r5_fail(&world.state, BE_R5_ERROR_BACKING) ==
	      BE_R5_ERROR_BACKING);
	check_terminal(&world.state, BE_R5_ERROR_BACKING);
}

static void print_count(const char *label, unsigned long value)
{
	printf("%s%lu\n", label, value);
}

int main(void)
{
	test_frozen_constants();
	test_names();
	test_import_from_live_r4();
	test_happy_path();
	test_protected_run_and_return();
	test_completion_and_shutdown();
	test_import_r4_state_rejections();
	test_import_binding_rejections();
	test_import_observation_rejections();
	test_import_frame_rejections();
	test_import_nulls_and_replay();
	test_prepare_wrong_phase();
	test_prepare_wrong_direction_and_witness();
	test_prepare_corruption();
	test_fence_wrong_phase();
	test_fence_evidence_rejections();
	test_fence_state_corruption();
	test_publish_wrong_phase();
	test_publish_nulls();
	test_publish_entry_rejections();
	test_publish_state_corruption();
	test_publish_frame_rejections();
	test_exit_wrong_phase();
	test_exit_nulls();
	test_exit_denied_load_rejections();
	test_exit_denied_store_rejections();
	test_exit_event_rejections();
	test_exit_observation_rejections();
	test_exit_state_corruption();
	test_shutdown_returned();
	test_shutdown_wrong_phase();
	test_explicit_failure();

	puts("BE_R5_CHECK: PASS");
	print_count("BE_R5_CHECK: scenarios=", scenarios);
	print_count("BE_R5_CHECK: assertions=", assertions);
	return 0;
}
