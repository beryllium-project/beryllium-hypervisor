// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: execute the separately authorized R3 boot-and-first-management-
 *          entry sequence over the accepted R1 and R2 mechanisms.
 * Trust:   privileged orchestration in restricted C. Linker symbols, SBI
 *          results, R1/R2 output, CSR readback, binding publication, and
 *          HGATP readback are all checked before SRET.
 * Scope:   stops at the first management VS instruction. No trap protocol,
 *          context handling, second VS entry, access test, or switching.
 */
#include "r3-platform.h"

#include <be/r1-config.h>

#include "r0-layout.h"
#include "r0-sbi.h"

static struct be_runtime be_r3_runtime = BE_RUNTIME_INITIALIZER;
static struct be_r2_output be_r3_r2_output;
static struct be_r2_leaf_set be_r3_leaf_sets[BE_MAX_ROOTS];
static struct be_r3_state be_r3_control = BE_R3_STATE_INITIALIZER;
static struct be_r3_image_layout be_r3_layout;
static struct be_r3_hs_state be_r3_hs;

static const char marker_boot[] = "BE_R3:01 BOOT_VALIDATED\n";
static const char marker_r1[] = "BE_R3:02 R1_DERIVED\n";
static const char marker_r2[] = "BE_R3:03 R2_BUILT_REWALKED\n";
static const char marker_hs[] = "BE_R3:04 HS_VS_STATE_VERIFIED\n";
static const char marker_binding[] = "BE_R3:05 BINDING_PREPARED\n";
static const char marker_fence[] = "BE_R3:06 HGATP_FENCED_PUBLISHED\n";
static const char marker_entry[] =
	"BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000\n";
static const char marker_failure[] = "BE_R3:FAIL ";
static const char marker_newline[] = "\n";

static be_u64 symbol_address(const be_u8 *symbol)
{
	return (be_u64)symbol;
}

static void build_image_layout(struct be_r3_image_layout *layout)
{
	*layout = (struct be_r3_image_layout) {
		.entry = symbol_address(be_reset),
		.monitor_code_start =
			symbol_address(__be_monitor_code_start),
		.monitor_code_end = symbol_address(__be_monitor_code_end),
		.monitor_data_start =
			symbol_address(__be_monitor_data_start),
		.monitor_data_end = symbol_address(__be_monitor_data_end),
		.input_start = symbol_address(__be_input_start),
		.input_end = symbol_address(__be_input_end),
		.bss_start = symbol_address(__be_bss_start),
		.bss_end = symbol_address(__be_bss_end),
		.diagnostic_start =
			symbol_address(__be_diagnostic_start),
		.diagnostic_end = symbol_address(__be_diagnostic_end),
		.root_management_start =
			symbol_address(__be_root_management_start),
		.root_management_end =
			symbol_address(__be_root_management_end),
		.root_protected_start =
			symbol_address(__be_root_protected_start),
		.root_protected_end =
			symbol_address(__be_root_protected_end),
		.stack_management_start =
			symbol_address(__be_stack_management_start),
		.stack_management_end =
			symbol_address(__be_stack_management_end),
		.stack_protected_start =
			symbol_address(__be_stack_protected_start),
		.stack_protected_end =
			symbol_address(__be_stack_protected_end),
		.saved_management_start =
			symbol_address(__be_saved_management_start),
		.saved_management_end =
			symbol_address(__be_saved_management_end),
		.saved_protected_start =
			symbol_address(__be_saved_protected_start),
		.saved_protected_end =
			symbol_address(__be_saved_protected_end),
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
		.trap_vector = symbol_address(be_r3_unexpected_trap),
	};
}

static enum be_r3_error write_text(const char *text)
{
	be_u64 length = be_r3_text_length(text);

	if (length > BE_PAGE_SIZE)
		return BE_R3_ERROR_DBCN_RANGE;
	return be_r3_platform_write(text, length);
}

static void write_failure_marker(enum be_r3_error error)
{
	(void)write_text(marker_failure);
	(void)write_text(be_r3_error_name(error));
	(void)write_text(marker_newline);
}

static void runtime_fail(enum be_r3_error error) __attribute__((noreturn));

static void runtime_fail(enum be_r3_error error)
{
	enum be_r3_error reset_error;

	if (be_r3_control.phase == BE_R3_PHASE_FAILED)
		error = be_r3_control.error;
	else
		error = be_r3_fail(&be_r3_control, error);
	write_failure_marker(error);
	reset_error = be_r3_platform_reset();
	write_failure_marker(reset_error);
	be_r3_arch_halt();
}

static void emit_marker(const char *marker)
{
	enum be_r3_error error = write_text(marker);

	if (error != BE_R3_ERROR_NONE)
		runtime_fail(error);
}

static void run_r1(void)
{
	if (be_runtime_copy_inventory(&be_r3_runtime,
				      be_r1_inventory()) != BE_RUNTIME_OK)
		runtime_fail(BE_R3_ERROR_R1_STATE);
	if (be_runtime_copy_proposal(&be_r3_runtime,
				     be_r1_proposal()) != BE_RUNTIME_OK)
		runtime_fail(BE_R3_ERROR_R1_STATE);
	if (be_runtime_validate(&be_r3_runtime) != BE_RUNTIME_OK)
		runtime_fail(BE_R3_ERROR_R1_STATE);
	if (be_runtime_seal(&be_r3_runtime) != BE_RUNTIME_OK)
		runtime_fail(BE_R3_ERROR_R1_STATE);
	if (be_runtime_derive(&be_r3_runtime) != BE_RUNTIME_OK)
		runtime_fail(BE_R3_ERROR_R1_STATE);
	if (be_r3_note_r1_derived(&be_r3_control,
				   &be_r3_runtime) != BE_R3_ERROR_NONE)
		runtime_fail(be_r3_control.error);
}

static void run_r2(void)
{
	struct be_r2_pool_desc pools[BE_MAX_ROOTS] = {
		{
			.base = BE_R0_PA_ROOT_POOL_MANAGEMENT,
			.buf = __be_root_management_start,
			.buf_size = BE_SV39X4_POOL_SIZE,
		},
		{
			.base = BE_R0_PA_ROOT_POOL_PROTECTED,
			.buf = __be_root_protected_start,
			.buf_size = BE_SV39X4_POOL_SIZE,
		},
	};

	if (be_r2_build(&be_r3_runtime, pools,
			&be_r3_r2_output) != BE_CHECK_OK)
		runtime_fail(BE_R3_ERROR_R2_STATE);
	if (be_r2_walk_and_check(&be_r3_runtime, pools,
				 &be_r3_r2_output,
				 be_r3_leaf_sets) != BE_CHECK_OK)
		runtime_fail(BE_R3_ERROR_R2_STATE);
	if (be_r3_note_r2_built(&be_r3_control, &be_r3_runtime,
				 &be_r3_r2_output,
				 be_r3_leaf_sets) != BE_R3_ERROR_NONE)
		runtime_fail(be_r3_control.error);
}

void be_r3_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
{
	struct be_r3_boot_contract boot = { 0 };
	struct be_r3_binding binding = {
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
		.published = 0U,
	};
	be_u64 hgatp_readback;
	long sbi_error;

	build_image_layout(&be_r3_layout);
	boot.entry = symbol_address(be_reset);
	boot.hart_id = hart_id;
	boot.firmware_pointer = firmware_pointer;
	boot.layout = be_r3_layout;

	sbi_error = be_r3_platform_get_spec_version(
		&boot.sbi_spec_version);
	if (sbi_error != BE_R0_SBI_SUCCESS)
		runtime_fail(BE_R3_ERROR_SBI_SPEC);
	sbi_error = be_r3_platform_probe_extension(
		BE_R0_SBI_EID_DBCN, &boot.dbcn_probe);
	if (sbi_error != BE_R0_SBI_SUCCESS)
		runtime_fail(BE_R3_ERROR_SBI_DBCN_PROBE);
	sbi_error = be_r3_platform_probe_extension(
		BE_R0_SBI_EID_SRST, &boot.srst_probe);
	if (sbi_error != BE_R0_SBI_SUCCESS)
		runtime_fail(BE_R3_ERROR_SBI_SRST_PROBE);

	if (be_r3_validate_boot(&be_r3_control,
				 &boot) != BE_R3_ERROR_NONE)
		runtime_fail(be_r3_control.error);
	emit_marker(marker_boot);

	run_r1();
	emit_marker(marker_r1);

	run_r2();
	emit_marker(marker_r2);

	be_r3_arch_reset_state(be_r3_layout.trap_vector, &be_r3_hs);
	if (be_r3_note_hs_ready(&be_r3_control, &be_r3_hs,
				 &be_r3_layout) != BE_R3_ERROR_NONE)
		runtime_fail(be_r3_control.error);
	emit_marker(marker_hs);

	if (be_r3_prepare_management_binding(&be_r3_control,
					      &binding) !=
	    BE_R3_ERROR_NONE)
		runtime_fail(be_r3_control.error);
	emit_marker(marker_binding);

	hgatp_readback = be_r3_arch_install_management(binding.hgatp);
	if (be_r3_publish_management_binding(&be_r3_control,
					      hgatp_readback, 1U) !=
	    BE_R3_ERROR_NONE)
		runtime_fail(be_r3_control.error);
	emit_marker(marker_fence);

	if (be_r3_arm_management_entry(&be_r3_control,
					&be_r3_control.active) !=
	    BE_R3_ERROR_NONE)
		runtime_fail(be_r3_control.error);
	emit_marker(marker_entry);

	be_r3_arch_enter_management(be_r3_control.active.guest_pc,
				    be_r3_control.active.guest_sp,
				    be_r3_control.active.trusted_sp);
}
