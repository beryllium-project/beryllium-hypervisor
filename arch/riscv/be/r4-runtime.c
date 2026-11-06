/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: run the accepted R3 construction sequence, import exactly its
 *          ENTRY_ARMED management binding, and orchestrate R4 trap decisions.
 * Trust:   privileged restricted-C orchestration. CSR transfer remains in the
 *          explicit assembly boundary and all observed backing is diagnostic.
 * Scope:   two same-management exits only; no root write, fence, switch, or
 *          protected execution is authorized after the initial R3 entry.
 */
#include "r4-platform.h"

#include <be/r1-config.h>

#include "r0-layout.h"
#include "r0-sbi.h"

static struct be_runtime be_r4_runtime = BE_RUNTIME_INITIALIZER;
static struct be_r2_output be_r4_r2_output;
static struct be_r2_leaf_set be_r4_leaf_sets[BE_MAX_ROOTS];
static struct be_r3_state be_r4_r3_control = BE_R3_STATE_INITIALIZER;
static struct be_r4_state be_r4_control = BE_R4_STATE_INITIALIZER;
static struct be_r3_image_layout be_r4_layout;
static struct be_r3_hs_state be_r4_hs;

static const char marker_boot[] = "BE_R3:01 BOOT_VALIDATED\n";
static const char marker_r1[] = "BE_R3:02 R1_DERIVED\n";
static const char marker_r2[] = "BE_R3:03 R2_BUILT_REWALKED\n";
static const char marker_hs[] = "BE_R3:04 HS_VS_STATE_VERIFIED\n";
static const char marker_binding[] = "BE_R3:05 BINDING_PREPARED\n";
static const char marker_fence[] = "BE_R3:06 HGATP_FENCED_PUBLISHED\n";
static const char marker_entry[] =
	"BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000\n";
static const char marker_r4_begin[] = "BE_R4:01 ENTRY_ARMED_IMPORTED\n";
static const char marker_fault[] =
	"BE_R4:02 EXPECTED_DENIED_LOAD pc=0x40010014 resume=0x40010018\n";
static const char marker_event[] =
	"BE_R4:03 PRIVATE_EVENT pc=0x40010030 resume=0x40010034\n";
static const char marker_failure[] = "BE_R4:FAIL ";
static const char marker_srst[] = "BE_R4:SRST_RETURNED\n";
static const char marker_newline[] = "\n";

static be_u64 symbol_address(const be_u8 *symbol)
{
	return (be_u64)symbol;
}

static void build_image_layout(struct be_r3_image_layout *layout)
{
	*layout = (struct be_r3_image_layout) {
		.entry = symbol_address(be_reset),
		.monitor_code_start = symbol_address(__be_monitor_code_start),
		.monitor_code_end = symbol_address(__be_monitor_code_end),
		.monitor_data_start = symbol_address(__be_monitor_data_start),
		.monitor_data_end = symbol_address(__be_monitor_data_end),
		.input_start = symbol_address(__be_input_start),
		.input_end = symbol_address(__be_input_end),
		.bss_start = symbol_address(__be_bss_start),
		.bss_end = symbol_address(__be_bss_end),
		.diagnostic_start = symbol_address(__be_diagnostic_start),
		.diagnostic_end = symbol_address(__be_diagnostic_end),
		.root_management_start = symbol_address(__be_root_management_start),
		.root_management_end = symbol_address(__be_root_management_end),
		.root_protected_start = symbol_address(__be_root_protected_start),
		.root_protected_end = symbol_address(__be_root_protected_end),
		.stack_management_start =
			symbol_address(__be_stack_management_start),
		.stack_management_end = symbol_address(__be_stack_management_end),
		.stack_protected_start =
			symbol_address(__be_stack_protected_start),
		.stack_protected_end = symbol_address(__be_stack_protected_end),
		.saved_management_start =
			symbol_address(__be_saved_management_start),
		.saved_management_end = symbol_address(__be_saved_management_end),
		.saved_protected_start =
			symbol_address(__be_saved_protected_start),
		.saved_protected_end = symbol_address(__be_saved_protected_end),
		.private_management_start =
			symbol_address(__be_private_management_start),
		.private_management_end =
			symbol_address(__be_private_management_end),
		.private_protected_start =
			symbol_address(__be_private_protected_start),
		.private_protected_end =
			symbol_address(__be_private_protected_end),
		.shared_start = symbol_address(__be_shared_start),
		.shared_end = symbol_address(__be_shared_end),
		.guest_management_start =
			symbol_address(__be_guest_management_start),
		.guest_management_end =
			symbol_address(__be_guest_management_end),
		.guest_protected_start =
			symbol_address(__be_guest_protected_start),
		.guest_protected_end =
			symbol_address(__be_guest_protected_end),
		.trap_vector = symbol_address(be_r4_trap_entry),
	};
}

static enum be_r3_error write_text(const char *text)
{
	be_u64 length = be_r3_text_length(text);

	if (length > BE_PAGE_SIZE)
		return BE_R3_ERROR_DBCN_RANGE;
	return be_r3_platform_write(text, length);
}

static void emit_marker(const char *marker)
{
	if (write_text(marker) != BE_R3_ERROR_NONE)
		be_r4_runtime_terminal(BE_R4_ERROR_R3_STATE);
}

void be_r4_runtime_terminal(enum be_r4_error error)
{
	(void)be_r4_fail(&be_r4_control, error);
	(void)write_text(marker_failure);
	(void)write_text(be_r4_error_name(be_r4_control.error));
	(void)write_text(marker_newline);
	(void)be_r3_platform_reset();
	(void)write_text(marker_srst);
	be_r4_arch_halt();
}

static void r3_fail(void)
{
	be_r4_runtime_terminal(BE_R4_ERROR_R3_STATE);
}

static void run_r1(void)
{
	if (be_runtime_copy_inventory(&be_r4_runtime,
				      be_r1_inventory()) != BE_RUNTIME_OK ||
	    be_runtime_copy_proposal(&be_r4_runtime,
				     be_r1_proposal()) != BE_RUNTIME_OK ||
	    be_runtime_validate(&be_r4_runtime) != BE_RUNTIME_OK ||
	    be_runtime_seal(&be_r4_runtime) != BE_RUNTIME_OK ||
	    be_runtime_derive(&be_r4_runtime) != BE_RUNTIME_OK ||
	    be_r3_note_r1_derived(&be_r4_r3_control,
				  &be_r4_runtime) != BE_R3_ERROR_NONE)
		r3_fail();
}

static void run_r2(void)
{
	struct be_r2_pool_desc pools[BE_MAX_ROOTS] = {
		{ .base = BE_R0_PA_ROOT_POOL_MANAGEMENT,
		  .buf = __be_root_management_start,
		  .buf_size = BE_SV39X4_POOL_SIZE },
		{ .base = BE_R0_PA_ROOT_POOL_PROTECTED,
		  .buf = __be_root_protected_start,
		  .buf_size = BE_SV39X4_POOL_SIZE },
	};

	if (be_r2_build(&be_r4_runtime, pools, &be_r4_r2_output) != BE_CHECK_OK ||
	    be_r2_walk_and_check(&be_r4_runtime, pools, &be_r4_r2_output,
				 be_r4_leaf_sets) != BE_CHECK_OK ||
	    be_r3_note_r2_built(&be_r4_r3_control, &be_r4_runtime,
				&be_r4_r2_output,
				be_r4_leaf_sets) != BE_R3_ERROR_NONE)
		r3_fail();
}

static void initialise_backing(void)
{
	volatile be_u64 *management =
		(volatile be_u64 *)__be_private_management_start;
	volatile be_u64 *protected =
		(volatile be_u64 *)__be_private_protected_start;
	volatile be_u64 *shared = (volatile be_u64 *)__be_shared_start;

	/*
	 * The fixture's first store must establish 17.  Preseeding it would
	 * make the denied-load observation non-evidentiary.
	 */
	*management = 0U;
	*protected = 0U;
	*shared = 0U;
	if (*management != 0U || *protected != 0U ||
	    *shared != 0U)
		be_r4_runtime_terminal(BE_R4_ERROR_BACKING);
}

void be_r4_trap_dispatch(struct be_r4_frame *frame, be_u64 current_hgatp)
{
	volatile const be_u64 *management =
		(const volatile be_u64 *)__be_private_management_start;
	volatile const be_u64 *protected =
		(const volatile be_u64 *)__be_private_protected_start;
	volatile const be_u64 *shared =
		(const volatile be_u64 *)__be_shared_start;
	struct be_r4_observation observation = {
		.hart_id = BE_CONFIGURATION_HART_ID,
		.active = be_r4_control.active,
		.current_hgatp = current_hgatp,
		.private_value = *management,
		.protected_value = *protected,
		.shared_value = *shared,
	};
	struct be_r4_result result = { 0 };
	enum be_r4_error error;

	error = be_r4_handle_trap(&be_r4_control, frame, &observation, &result);
	if (error != BE_R4_ERROR_NONE ||
	    result.decision !=
		    BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME ||
	    result.active.hgatp != BE_R3_MANAGEMENT_HGATP)
		be_r4_runtime_terminal(error == BE_R4_ERROR_NONE ?
					BE_R4_ERROR_INVALID_PHASE : error);
	if (result.trap_class == BE_R4_TRAP_EXPECTED_DENIED_LOAD)
		emit_marker(marker_fault);
	else if (result.trap_class == BE_R4_TRAP_PRIVATE_EVENT)
		emit_marker(marker_event);
	else
		be_r4_runtime_terminal(BE_R4_ERROR_INVALID_PHASE);
}

void be_r4_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
{
	struct be_r3_boot_contract boot = { 0 };
	struct be_r3_binding binding = {
		.domain = BE_DOMAIN_MANAGEMENT, .vcpu_id = 1U, .root_id = 101U,
		.vmid = 0U, .hgatp = BE_R3_MANAGEMENT_HGATP,
		.guest_pc = BE_R3_INITIAL_GUEST_PC,
		.guest_sp = BE_R3_INITIAL_GUEST_SP,
		.trusted_sp = BE_R3_INITIAL_TRUSTED_SP,
		.saved_state_id = 1U,
		.saved_state_pa = BE_R3_MANAGEMENT_SAVED_PA,
		.vsatp = 0U, .published = 0U,
	};
	be_u64 hgatp_readback;

	build_image_layout(&be_r4_layout);
	boot.entry = symbol_address(be_reset);
	boot.hart_id = hart_id;
	boot.firmware_pointer = firmware_pointer;
	boot.layout = be_r4_layout;
	if (be_r3_platform_get_spec_version(&boot.sbi_spec_version) !=
		    BE_R0_SBI_SUCCESS ||
	    be_r3_platform_probe_extension(BE_R0_SBI_EID_DBCN,
					 &boot.dbcn_probe) != BE_R0_SBI_SUCCESS ||
	    be_r3_platform_probe_extension(BE_R0_SBI_EID_SRST,
					 &boot.srst_probe) != BE_R0_SBI_SUCCESS ||
	    be_r3_validate_boot(&be_r4_r3_control, &boot) != BE_R3_ERROR_NONE)
		r3_fail();
	emit_marker(marker_boot);
	run_r1();
	emit_marker(marker_r1);
	run_r2();
	emit_marker(marker_r2);

	be_r4_arch_reset_state(be_r4_layout.trap_vector, &be_r4_hs);
	if (be_r3_note_hs_ready(&be_r4_r3_control, &be_r4_hs,
				&be_r4_layout) != BE_R3_ERROR_NONE)
		r3_fail();
	emit_marker(marker_hs);
	if (be_r3_prepare_management_binding(&be_r4_r3_control, &binding) !=
	    BE_R3_ERROR_NONE)
		r3_fail();
	emit_marker(marker_binding);
	hgatp_readback = be_r3_arch_install_management(binding.hgatp);
	if (be_r3_publish_management_binding(&be_r4_r3_control, hgatp_readback,
					     1U) != BE_R3_ERROR_NONE)
		r3_fail();
	emit_marker(marker_fence);
	if (be_r3_arm_management_entry(&be_r4_r3_control,
				       &be_r4_r3_control.active) !=
	    BE_R3_ERROR_NONE)
		r3_fail();
	emit_marker(marker_entry);
	if (be_r4_begin(&be_r4_control, &be_r4_r3_control) != BE_R4_ERROR_NONE)
		be_r4_runtime_terminal(be_r4_control.error);
	initialise_backing();
	emit_marker(marker_r4_begin);
	be_r3_arch_enter_management(be_r4_control.active.guest_pc,
				    be_r4_control.active.guest_sp,
				    be_r4_control.active.trusted_sp);
}
