// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host-testable R3 validation, one-way publication, and bounded DBCN
 *          progress mechanism for the accepted boot-and-first-entry package.
 * Trust:   restricted-C mechanism only. It never issues an SBI call, accesses
 *          a CSR, executes a fence, or enters VS mode.
 * Scope:   R3 only. The mechanism stops after arming the first management
 *          SRET and contains no trap, context, switch, or protected-entry
 *          behavior.
 */
#include <be/r3.h>

#include "../../arch/riscv/be/r0-layout.h"
#include "../../arch/riscv/be/r0-sbi.h"

#define BE_R3_MONITOR_CODE_END		BE_U64_C(0x80208000)
#define BE_R3_MONITOR_DATA_END		BE_U64_C(0x80210000)
#define BE_R3_ROOT_MANAGEMENT_END	BE_U64_C(0x8021c000)
#define BE_R3_ROOT_PROTECTED_END	BE_U64_C(0x80224000)
#define BE_R3_STACK_MANAGEMENT_END	BE_U64_C(0x80227000)
#define BE_R3_STACK_PROTECTED_END	BE_U64_C(0x8022a000)
#define BE_R3_SAVED_MANAGEMENT_END	BE_U64_C(0x8022c000)
#define BE_R3_SAVED_PROTECTED_END	BE_U64_C(0x8022d000)
#define BE_R3_PRIVATE_MANAGEMENT_END	BE_U64_C(0x8022f000)
#define BE_R3_PRIVATE_PROTECTED_END	BE_U64_C(0x80230000)
#define BE_R3_SHARED_END		BE_U64_C(0x80231000)
#define BE_R3_GUEST_MANAGEMENT_END	BE_U64_C(0x80233000)
#define BE_R3_GUEST_PROTECTED_END	BE_U64_C(0x80234000)

_Static_assert(BE_R3_DBCN_MAX_ITERATIONS ==
	       BE_R0_SBI_DBCN_MAX_ITERATIONS,
	       "R3 DBCN cap must preserve the accepted R0 value");
_Static_assert(BE_R3_DBCN_MAX_ITERATIONS <= 256U,
	       "R3 DBCN retry cap must remain bounded to 256");

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

static int expected_management_binding(const struct be_r3_binding *binding,
				       be_u32 published)
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
	       binding->published == published;
}

static int range_within(be_u64 base, be_u64 length,
			be_u64 container_base, be_u64 container_end)
{
	be_u64 end;

	if (base < container_base || base >= container_end)
		return 0;
	if (length > container_end - base)
		return 0;
	end = base + length;
	if (end < base || end > container_end)
		return 0;
	return 1;
}

static int image_layout_valid(const struct be_r3_image_layout *layout)
{
	if (layout->entry != BE_R0_IMAGE_ENTRY ||
	    layout->monitor_code_start != BE_R0_PA_MONITOR_CODE ||
	    layout->monitor_code_end < layout->monitor_code_start ||
	    layout->monitor_code_end > BE_R3_MONITOR_CODE_END ||
	    layout->monitor_data_start != BE_R0_PA_MONITOR_DATA ||
	    layout->monitor_data_end < layout->monitor_data_start ||
	    layout->monitor_data_end > BE_R3_MONITOR_DATA_END)
		return 0;

	if (layout->input_start < layout->monitor_data_start ||
	    layout->input_end < layout->input_start ||
	    layout->input_end > layout->monitor_data_end ||
	    layout->bss_start < layout->monitor_data_start ||
	    layout->bss_end < layout->bss_start ||
	    layout->bss_end > layout->diagnostic_start)
		return 0;

	if (layout->diagnostic_start != BE_R3_DIAGNOSTIC_BASE ||
	    layout->diagnostic_end != BE_R3_DIAGNOSTIC_END ||
	    layout->root_management_start !=
		    BE_R0_PA_ROOT_POOL_MANAGEMENT ||
	    layout->root_management_end != BE_R3_ROOT_MANAGEMENT_END ||
	    layout->root_protected_start != BE_R0_PA_ROOT_POOL_PROTECTED ||
	    layout->root_protected_end != BE_R3_ROOT_PROTECTED_END)
		return 0;

	if (layout->stack_management_start != BE_R0_PA_STACK_MANAGEMENT ||
	    layout->stack_management_end != BE_R3_STACK_MANAGEMENT_END ||
	    layout->stack_protected_start != BE_R0_PA_STACK_PROTECTED ||
	    layout->stack_protected_end != BE_R3_STACK_PROTECTED_END ||
	    layout->saved_management_start != BE_R0_PA_SAVED_MANAGEMENT ||
	    layout->saved_management_end != BE_R3_SAVED_MANAGEMENT_END ||
	    layout->saved_protected_start != BE_R0_PA_SAVED_PROTECTED ||
	    layout->saved_protected_end != BE_R3_SAVED_PROTECTED_END)
		return 0;

	if (layout->private_management_start !=
		    BE_R0_PA_PRIVATE_MANAGEMENT ||
	    layout->private_management_end !=
		    BE_R3_PRIVATE_MANAGEMENT_END ||
	    layout->private_protected_start !=
		    BE_R0_PA_PRIVATE_PROTECTED ||
	    layout->private_protected_end != BE_R3_PRIVATE_PROTECTED_END ||
	    layout->shared_start != BE_R0_PA_SHARED ||
	    layout->shared_end != BE_R3_SHARED_END)
		return 0;

	if (layout->guest_management_start !=
		    BE_R0_PA_GUEST_CODE_MANAGEMENT ||
	    layout->guest_management_end != BE_R3_GUEST_MANAGEMENT_END ||
	    layout->guest_protected_start != BE_R0_PA_GUEST_CODE_PROTECTED ||
	    layout->guest_protected_end != BE_R3_GUEST_PROTECTED_END)
		return 0;

	if ((layout->root_management_start &
	     (BE_R0_SV39X4_ROOT_ALIGN - 1U)) != 0U ||
	    (layout->root_protected_start &
	     (BE_R0_SV39X4_ROOT_ALIGN - 1U)) != 0U)
		return 0;
	if (layout->trap_vector < layout->monitor_code_start ||
	    layout->trap_vector >= layout->monitor_code_end ||
	    (layout->trap_vector & 0x3U) != 0U)
		return 0;
	return 1;
}

static int r1_state_valid(const struct be_runtime *runtime)
{
	if (runtime->phase != BE_RUNTIME_PHASE_DERIVED ||
	    runtime->check_result != BE_CHECK_OK ||
	    runtime->sealed == 0U ||
	    runtime->validated_identity != BE_R3_CONFIGURATION_ID ||
	    runtime->sealed_identity != BE_R3_CONFIGURATION_ID ||
	    runtime->canonical.configuration_id != BE_R3_CONFIGURATION_ID ||
	    runtime->enforcement.configuration_id != BE_R3_CONFIGURATION_ID)
		return 0;
	if (be_check_canonical(&runtime->canonical) != BE_CHECK_OK ||
	    be_check_enforcement(&runtime->canonical,
				 &runtime->enforcement) != BE_CHECK_OK)
		return 0;
	if (be_configuration_identity(&runtime->canonical) !=
	    BE_R3_CONFIGURATION_ID)
		return 0;
	return 1;
}

static int leaf_equal(const struct be_r2_leaf *leaf, be_u64 gpa,
		      be_u64 pa, be_u32 rights)
{
	return leaf->gpa == gpa && leaf->pa == pa && leaf->rights == rights;
}

static int r2_state_valid(const struct be_runtime *runtime,
			  const struct be_r2_output *output,
			  const struct be_r2_leaf_set leaf_sets[BE_MAX_ROOTS])
{
	const struct be_root_image *management =
		&runtime->enforcement.roots[0];
	const struct be_root_image *protected =
		&runtime->enforcement.roots[1];

	if (!r1_state_valid(runtime) || output->state != BE_R2_STATE_BUILT)
		return 0;
	if (output->results[0].hgatp != BE_R3_MANAGEMENT_HGATP ||
	    output->results[1].hgatp != BE_R3_PROTECTED_HGATP ||
	    output->results[0].leaf_count != 3U ||
	    output->results[1].leaf_count != 3U)
		return 0;
	if (management->domain != BE_DOMAIN_MANAGEMENT ||
	    management->root_id != 101U || management->vmid != 0U ||
	    management->root_table_frame != 3U ||
	    management->trusted_stack_frame != 5U ||
	    management->saved_state_id != 1U ||
	    management->saved_state_frame != 7U ||
	    protected->domain != BE_DOMAIN_PROTECTED ||
	    protected->root_id != 102U || protected->vmid != 0U ||
	    protected->root_table_frame != 4U ||
	    protected->trusted_stack_frame != 6U ||
	    protected->saved_state_id != 2U ||
	    protected->saved_state_frame != 8U)
		return 0;
	if (leaf_sets[0].count != 3U || leaf_sets[1].count != 3U)
		return 0;

	if (!leaf_equal(&leaf_sets[0].leaves[0],
			BE_R0_GPA_MANAGEMENT_PRIVATE,
			BE_R0_PA_PRIVATE_MANAGEMENT, BE_R0_RW) ||
	    !leaf_equal(&leaf_sets[0].leaves[1], BE_R0_GPA_SHARED,
			BE_R0_PA_SHARED, BE_R0_RW) ||
	    !leaf_equal(&leaf_sets[0].leaves[2],
			BE_R0_GPA_GUEST_CODE_MANAGEMENT,
			BE_R0_PA_GUEST_CODE_MANAGEMENT, BE_R0_RX))
		return 0;
	if (!leaf_equal(&leaf_sets[1].leaves[0],
			BE_R0_GPA_PROTECTED_PRIVATE,
			BE_R0_PA_PRIVATE_PROTECTED, BE_R0_RW) ||
	    !leaf_equal(&leaf_sets[1].leaves[1], BE_R0_GPA_SHARED,
			BE_R0_PA_SHARED, BE_R0_RO) ||
	    !leaf_equal(&leaf_sets[1].leaves[2],
			BE_R0_GPA_GUEST_CODE_PROTECTED,
			BE_R0_PA_GUEST_CODE_PROTECTED, BE_R0_RX))
		return 0;
	return 1;
}

static int hs_state_valid(const struct be_r3_hs_state *hs,
			  const struct be_r3_image_layout *layout)
{
	if (hs->satp != 0U ||
	    (hs->sstatus & BE_R3_SSTATUS_CONTROL_MASK) != 0U ||
	    hs->stvec != layout->trap_vector || hs->sscratch != 0U ||
	    hs->sepc != 0U || hs->scause != 0U || hs->stval != 0U ||
	    hs->sie != 0U || hs->sip != 0U || hs->senvcfg != 0U ||
	    hs->scounteren != 0U)
		return 0;
	if ((hs->hstatus & BE_R3_HSTATUS_CONTROL_MASK) !=
	    BE_R3_HSTATUS_CONTROL_VALUE)
		return 0;
	if (hs->hedeleg != 0U || hs->hideleg != 0U || hs->hie != 0U ||
	    hs->hip != 0U || hs->hvip != 0U ||
	    hs->hcounteren != 0U || hs->htimedelta != 0U ||
	    hs->henvcfg != 0U || hs->hgeie != 0U || hs->hgeip != 0U ||
	    hs->htval != 0U || hs->hgatp != 0U)
		return 0;
	if ((hs->vsstatus & BE_R3_SSTATUS_CONTROL_MASK) != 0U ||
	    hs->vsie != 0U || hs->vstvec != 0U ||
	    hs->vsscratch != 0U || hs->vsepc != 0U ||
	    hs->vscause != 0U || hs->vstval != 0U ||
	    hs->vsip != 0U || hs->vsatp != 0U)
		return 0;
	return 1;
}

enum be_r3_error
be_r3_fail(struct be_r3_state *state, enum be_r3_error error)
{
	if (state != (struct be_r3_state *)0 &&
	    state->phase == BE_R3_PHASE_FAILED)
		return state->error;
	if (error == BE_R3_ERROR_NONE)
		error = BE_R3_ERROR_INVALID_PHASE;
	if (state != (struct be_r3_state *)0) {
		state->pending = (struct be_r3_binding){ 0 };
		state->active = (struct be_r3_binding){ 0 };
		state->phase = BE_R3_PHASE_FAILED;
		state->error = error;
	}
	return error;
}

enum be_r3_error
be_r3_validate_boot(struct be_r3_state *state,
		    const struct be_r3_boot_contract *contract)
{
	if (state == (struct be_r3_state *)0)
		return BE_R3_ERROR_NULL;
	if (state->phase == BE_R3_PHASE_FAILED)
		return state->error;
	if (state->phase != BE_R3_PHASE_EMPTY)
		return be_r3_fail(state, BE_R3_ERROR_INVALID_PHASE);
	if (contract == (const struct be_r3_boot_contract *)0)
		return be_r3_fail(state, BE_R3_ERROR_NULL);
	if (contract->entry != BE_R0_IMAGE_ENTRY ||
	    contract->hart_id != BE_CONFIGURATION_HART_ID)
		return be_r3_fail(state, BE_R3_ERROR_HANDOFF);
	if (!image_layout_valid(&contract->layout))
		return be_r3_fail(state, BE_R3_ERROR_IMAGE_LAYOUT);
	if (contract->sbi_spec_version != BE_R3_OPENSBI_SPEC_VERSION)
		return be_r3_fail(state, BE_R3_ERROR_SBI_SPEC);
	if (contract->dbcn_probe != BE_R3_SBI_PROBE_AVAILABLE)
		return be_r3_fail(state, BE_R3_ERROR_SBI_DBCN_PROBE);
	if (contract->srst_probe != BE_R3_SBI_PROBE_AVAILABLE)
		return be_r3_fail(state, BE_R3_ERROR_SBI_SRST_PROBE);

	state->firmware_pointer = contract->firmware_pointer;
	state->configuration_id = 0U;
	state->management_hgatp = 0U;
	state->protected_hgatp = 0U;
	state->pending = (struct be_r3_binding){ 0 };
	state->active = (struct be_r3_binding){ 0 };
	state->error = BE_R3_ERROR_NONE;
	state->phase = BE_R3_PHASE_BOOT_VALIDATED;
	return BE_R3_ERROR_NONE;
}

enum be_r3_error
be_r3_note_r1_derived(struct be_r3_state *state,
		      const struct be_runtime *runtime)
{
	if (state == (struct be_r3_state *)0)
		return BE_R3_ERROR_NULL;
	if (state->phase == BE_R3_PHASE_FAILED)
		return state->error;
	if (state->phase != BE_R3_PHASE_BOOT_VALIDATED)
		return be_r3_fail(state, BE_R3_ERROR_INVALID_PHASE);
	if (runtime == (const struct be_runtime *)0)
		return be_r3_fail(state, BE_R3_ERROR_NULL);
	if (!r1_state_valid(runtime))
		return be_r3_fail(state, BE_R3_ERROR_R1_STATE);

	state->configuration_id = runtime->sealed_identity;
	state->phase = BE_R3_PHASE_R1_DERIVED;
	return BE_R3_ERROR_NONE;
}

enum be_r3_error
be_r3_note_r2_built(struct be_r3_state *state,
		    const struct be_runtime *runtime,
		    const struct be_r2_output *output,
		    const struct be_r2_leaf_set leaf_sets[BE_MAX_ROOTS])
{
	if (state == (struct be_r3_state *)0)
		return BE_R3_ERROR_NULL;
	if (state->phase == BE_R3_PHASE_FAILED)
		return state->error;
	if (state->phase != BE_R3_PHASE_R1_DERIVED)
		return be_r3_fail(state, BE_R3_ERROR_INVALID_PHASE);
	if (runtime == (const struct be_runtime *)0 ||
	    output == (const struct be_r2_output *)0 ||
	    leaf_sets == (const struct be_r2_leaf_set *)0)
		return be_r3_fail(state, BE_R3_ERROR_NULL);
	if (!r2_state_valid(runtime, output, leaf_sets))
		return be_r3_fail(state, BE_R3_ERROR_R2_STATE);

	state->management_hgatp = output->results[0].hgatp;
	state->protected_hgatp = output->results[1].hgatp;
	state->phase = BE_R3_PHASE_R2_BUILT;
	return BE_R3_ERROR_NONE;
}

enum be_r3_error
be_r3_note_hs_ready(struct be_r3_state *state,
		    const struct be_r3_hs_state *hs,
		    const struct be_r3_image_layout *layout)
{
	if (state == (struct be_r3_state *)0)
		return BE_R3_ERROR_NULL;
	if (state->phase == BE_R3_PHASE_FAILED)
		return state->error;
	if (state->phase != BE_R3_PHASE_R2_BUILT)
		return be_r3_fail(state, BE_R3_ERROR_INVALID_PHASE);
	if (hs == (const struct be_r3_hs_state *)0 ||
	    layout == (const struct be_r3_image_layout *)0)
		return be_r3_fail(state, BE_R3_ERROR_NULL);
	if (!image_layout_valid(layout) || !hs_state_valid(hs, layout))
		return be_r3_fail(state, BE_R3_ERROR_HS_STATE);

	state->phase = BE_R3_PHASE_HS_READY;
	return BE_R3_ERROR_NONE;
}

enum be_r3_error
be_r3_prepare_management_binding(struct be_r3_state *state,
				 const struct be_r3_binding *binding)
{
	if (state == (struct be_r3_state *)0)
		return BE_R3_ERROR_NULL;
	if (state->phase == BE_R3_PHASE_FAILED)
		return state->error;
	if (state->phase != BE_R3_PHASE_HS_READY)
		return be_r3_fail(state, BE_R3_ERROR_INVALID_PHASE);
	if (binding == (const struct be_r3_binding *)0)
		return be_r3_fail(state, BE_R3_ERROR_NULL);
	if (state->configuration_id != BE_R3_CONFIGURATION_ID ||
	    state->management_hgatp != BE_R3_MANAGEMENT_HGATP ||
	    state->protected_hgatp != BE_R3_PROTECTED_HGATP ||
	    !expected_management_binding(binding, 0U))
		return be_r3_fail(state, BE_R3_ERROR_BINDING);

	state->pending = *binding;
	state->active = (struct be_r3_binding){ 0 };
	state->phase = BE_R3_PHASE_BINDING_PREPARED;
	return BE_R3_ERROR_NONE;
}

enum be_r3_error
be_r3_publish_management_binding(struct be_r3_state *state,
				 be_u64 hgatp_readback,
				 be_u32 fence_completed)
{
	if (state == (struct be_r3_state *)0)
		return BE_R3_ERROR_NULL;
	if (state->phase == BE_R3_PHASE_FAILED)
		return state->error;
	if (state->phase != BE_R3_PHASE_BINDING_PREPARED)
		return be_r3_fail(state, BE_R3_ERROR_INVALID_PHASE);
	if (!expected_management_binding(&state->pending, 0U) ||
	    state->active.published != 0U ||
	    hgatp_readback != state->pending.hgatp ||
	    fence_completed != 1U)
		return be_r3_fail(state, BE_R3_ERROR_PUBLICATION);

	state->active = state->pending;
	state->active.published = 1U;
	state->pending = (struct be_r3_binding){ 0 };
	state->phase = BE_R3_PHASE_BINDING_PUBLISHED;
	return BE_R3_ERROR_NONE;
}

enum be_r3_error
be_r3_arm_management_entry(struct be_r3_state *state,
			   const struct be_r3_binding *binding)
{
	if (state == (struct be_r3_state *)0)
		return BE_R3_ERROR_NULL;
	if (state->phase == BE_R3_PHASE_FAILED)
		return state->error;
	if (state->phase != BE_R3_PHASE_BINDING_PUBLISHED)
		return be_r3_fail(state, BE_R3_ERROR_INVALID_PHASE);
	if (binding == (const struct be_r3_binding *)0)
		return be_r3_fail(state, BE_R3_ERROR_NULL);
	if (!expected_management_binding(&state->active, 1U) ||
	    !binding_equal(&state->active, binding))
		return be_r3_fail(state, BE_R3_ERROR_BINDING);

	state->phase = BE_R3_PHASE_ENTRY_ARMED;
	return BE_R3_ERROR_NONE;
}

static enum be_r3_error
fail_dbcn(struct be_r3_dbcn_progress *progress, enum be_r3_error error)
{
	progress->state = BE_R3_DBCN_FAILED;
	progress->error = error;
	return error;
}

enum be_r3_error
be_r3_dbcn_begin(struct be_r3_dbcn_progress *progress,
		 be_u64 base, be_u64 length)
{
	if (progress == (struct be_r3_dbcn_progress *)0)
		return BE_R3_ERROR_NULL;
	if (progress->state == BE_R3_DBCN_FAILED)
		return progress->error;
	if (progress->state != BE_R3_DBCN_EMPTY)
		return fail_dbcn(progress, BE_R3_ERROR_INVALID_PHASE);
	if (!range_within(base, length, BE_R3_DIAGNOSTIC_BASE,
			  BE_R3_DIAGNOSTIC_END))
		return fail_dbcn(progress, BE_R3_ERROR_DBCN_RANGE);

	progress->base = base;
	progress->length = length;
	progress->offset = 0U;
	progress->iterations = 0U;
	progress->error = BE_R3_ERROR_NONE;
	progress->state = length == 0U ?
		BE_R3_DBCN_COMPLETE : BE_R3_DBCN_ACTIVE;
	return BE_R3_ERROR_NONE;
}

enum be_r3_error
be_r3_dbcn_consume(struct be_r3_dbcn_progress *progress,
		   long sbi_error, be_u64 bytes_written)
{
	be_u64 remaining;

	if (progress == (struct be_r3_dbcn_progress *)0)
		return BE_R3_ERROR_NULL;
	if (progress->state == BE_R3_DBCN_FAILED)
		return progress->error;
	if (progress->state != BE_R3_DBCN_ACTIVE)
		return fail_dbcn(progress, BE_R3_ERROR_INVALID_PHASE);
	if (progress->iterations >= BE_R3_DBCN_MAX_ITERATIONS)
		return fail_dbcn(progress,
				 BE_R3_ERROR_DBCN_RETRY_EXHAUSTED);

	++progress->iterations;
	switch (sbi_error) {
	case BE_R0_SBI_SUCCESS:
		break;
	case BE_R0_SBI_ERR_FAILED:
		return fail_dbcn(progress, BE_R3_ERROR_DBCN_FAILED);
	case BE_R0_SBI_ERR_NOT_SUPPORTED:
		return fail_dbcn(progress,
				 BE_R3_ERROR_DBCN_NOT_SUPPORTED);
	case BE_R0_SBI_ERR_INVALID_PARAM:
		return fail_dbcn(progress,
				 BE_R3_ERROR_DBCN_INVALID_PARAM);
	case BE_R0_SBI_ERR_DENIED:
		return fail_dbcn(progress, BE_R3_ERROR_DBCN_DENIED);
	case BE_R0_SBI_ERR_INVALID_ADDRESS:
		return fail_dbcn(progress,
				 BE_R3_ERROR_DBCN_INVALID_ADDRESS);
	default:
		return fail_dbcn(progress, BE_R3_ERROR_DBCN_MALFORMED);
	}

	remaining = progress->length - progress->offset;
	if (bytes_written > remaining)
		return fail_dbcn(progress, BE_R3_ERROR_DBCN_MALFORMED);
	progress->offset += bytes_written;
	if (progress->offset == progress->length) {
		progress->state = BE_R3_DBCN_COMPLETE;
		return BE_R3_ERROR_NONE;
	}
	if (progress->iterations == BE_R3_DBCN_MAX_ITERATIONS)
		return fail_dbcn(progress,
				 BE_R3_ERROR_DBCN_RETRY_EXHAUSTED);
	return BE_R3_ERROR_NONE;
}

enum be_r3_error be_r3_srst_result(long sbi_error)
{
	switch (sbi_error) {
	case BE_R0_SBI_SUCCESS:
		return BE_R3_ERROR_SRST_RETURNED;
	case BE_R0_SBI_ERR_FAILED:
		return BE_R3_ERROR_SRST_FAILED;
	case BE_R0_SBI_ERR_NOT_SUPPORTED:
		return BE_R3_ERROR_SRST_NOT_SUPPORTED;
	case BE_R0_SBI_ERR_INVALID_PARAM:
		return BE_R3_ERROR_SRST_INVALID_PARAM;
	case BE_R0_SBI_ERR_DENIED:
		return BE_R3_ERROR_SRST_DENIED;
	case BE_R0_SBI_ERR_INVALID_ADDRESS:
		return BE_R3_ERROR_SRST_INVALID_ADDRESS;
	default:
		return BE_R3_ERROR_SRST_MALFORMED;
	}
}

const char *be_r3_phase_name(enum be_r3_phase phase)
{
	switch (phase) {
	case BE_R3_PHASE_EMPTY:
		return "empty";
	case BE_R3_PHASE_BOOT_VALIDATED:
		return "boot-validated";
	case BE_R3_PHASE_R1_DERIVED:
		return "r1-derived";
	case BE_R3_PHASE_R2_BUILT:
		return "r2-built";
	case BE_R3_PHASE_HS_READY:
		return "hs-ready";
	case BE_R3_PHASE_BINDING_PREPARED:
		return "binding-prepared";
	case BE_R3_PHASE_BINDING_PUBLISHED:
		return "binding-published";
	case BE_R3_PHASE_ENTRY_ARMED:
		return "entry-armed";
	case BE_R3_PHASE_FAILED:
		return "failed";
	default:
		return "invalid";
	}
}

const char *be_r3_error_name(enum be_r3_error error)
{
	switch (error) {
	case BE_R3_ERROR_NONE:
		return "none";
	case BE_R3_ERROR_NULL:
		return "null";
	case BE_R3_ERROR_INVALID_PHASE:
		return "invalid-phase";
	case BE_R3_ERROR_HANDOFF:
		return "handoff";
	case BE_R3_ERROR_IMAGE_LAYOUT:
		return "image-layout";
	case BE_R3_ERROR_SBI_SPEC:
		return "sbi-spec";
	case BE_R3_ERROR_SBI_DBCN_PROBE:
		return "sbi-dbcn-probe";
	case BE_R3_ERROR_SBI_SRST_PROBE:
		return "sbi-srst-probe";
	case BE_R3_ERROR_R1_STATE:
		return "r1-state";
	case BE_R3_ERROR_R2_STATE:
		return "r2-state";
	case BE_R3_ERROR_HS_STATE:
		return "hs-state";
	case BE_R3_ERROR_BINDING:
		return "binding";
	case BE_R3_ERROR_PUBLICATION:
		return "publication";
	case BE_R3_ERROR_DBCN_RANGE:
		return "dbcn-range";
	case BE_R3_ERROR_DBCN_FAILED:
		return "dbcn-failed";
	case BE_R3_ERROR_DBCN_NOT_SUPPORTED:
		return "dbcn-not-supported";
	case BE_R3_ERROR_DBCN_INVALID_PARAM:
		return "dbcn-invalid-param";
	case BE_R3_ERROR_DBCN_DENIED:
		return "dbcn-denied";
	case BE_R3_ERROR_DBCN_INVALID_ADDRESS:
		return "dbcn-invalid-address";
	case BE_R3_ERROR_DBCN_MALFORMED:
		return "dbcn-malformed";
	case BE_R3_ERROR_DBCN_RETRY_EXHAUSTED:
		return "dbcn-retry-exhausted";
	case BE_R3_ERROR_SRST_FAILED:
		return "srst-failed";
	case BE_R3_ERROR_SRST_NOT_SUPPORTED:
		return "srst-not-supported";
	case BE_R3_ERROR_SRST_INVALID_PARAM:
		return "srst-invalid-param";
	case BE_R3_ERROR_SRST_DENIED:
		return "srst-denied";
	case BE_R3_ERROR_SRST_INVALID_ADDRESS:
		return "srst-invalid-address";
	case BE_R3_ERROR_SRST_RETURNED:
		return "srst-returned";
	case BE_R3_ERROR_SRST_MALFORMED:
		return "srst-malformed";
	default:
		return "invalid";
	}
}
