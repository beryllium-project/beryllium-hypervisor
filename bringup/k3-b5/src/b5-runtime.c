// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B5 runtime: the accepted R3 boot and first-entry sequence in
 *          R5's order, then the B5 guest controls, the guest RAM clear, the
 *          entry into the separately built guest, and the service of each
 *          guest exit through the pure-C SBI core.
 * Trust:   privileged restricted-C orchestration. Every CSR access, the
 *          fence, the frame transfer, and the SRET tails stay in assembly;
 *          the HS-to-M SBI calls go only through the accepted platform
 *          helpers. Guest bytes are read only through a translation the
 *          SBI core derived from the re-walked management leaves.
 * Scope:   one management guest on hart 0 (planning/k3-b5-plan.md). R4/R5
 *          are not linked; the protected root is built and re-walked but
 *          never installed or entered.
 */
#include "b5-platform.h"

#include <be/r1-config.h>

#include "r0-layout.h"
#include "r0-sbi.h"

_Static_assert(sizeof(struct be_b5_controls) == 120U,
	       "assembly controls size mismatch");
_Static_assert(__builtin_offsetof(struct be_b5_controls, hip) == 0U,
	       "assembly controls hip offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b5_controls, hstatus) == 8U,
	       "assembly controls hstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b5_controls, henvcfg) == 64U,
	       "assembly controls henvcfg offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b5_controls, vstimecmp) == 80U,
	       "assembly controls vstimecmp offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b5_controls, sstatus) == 96U,
	       "assembly controls sstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b5_controls, vsatp) == 112U,
	       "assembly controls vsatp offset mismatch");
_Static_assert(BE_B5_CLASS_EXCEPTION == 8, "assembly class moved");
_Static_assert(BE_B5_CLASS_RESUME == 10, "assembly class moved");
_Static_assert(BE_B5_HSTATUS_GUEST_CONTROLS == BE_U64_C(0x300180),
	       "assembly hstatus guest controls mismatch");
_Static_assert(BE_R3_HSTATUS_CONTROL_MASK == BE_U64_C(0x73f380),
	       "assembly hstatus mask mismatch");
_Static_assert(BE_R3_SSTATUS_CONTROL_MASK == BE_U64_C(0xde122),
	       "assembly sstatus mask mismatch");

static struct be_runtime be_b5_runtime = BE_RUNTIME_INITIALIZER;
static struct be_r2_output be_b5_r2_output;
static struct be_r2_leaf_set be_b5_leaf_sets[BE_MAX_ROOTS];
static struct be_r3_state be_b5_r3_control = BE_R3_STATE_INITIALIZER;
static struct be_r3_image_layout be_b5_layout;
static struct be_r3_hs_state be_b5_hs;
static struct be_b5_state be_b5_control = BE_B5_STATE_INITIALIZER;
static struct be_b5_controls be_b5_armed;
static struct be_b5_console be_b5_console;
static struct be_b5_line be_b5_line;
static be_u8 be_b5_guest_bytes[BE_B5_DBCN_MAX_BYTES];
static char be_b5_tagged[BE_B5_TAGGED_CAPACITY];
static be_u32 be_b5_terminal_entered;

/* The accepted R3 lines, as accepted arch/riscv/be/r5-runtime.c prints them. */
static const char marker_boot[] = "BE_R3:01 BOOT_VALIDATED\n";
static const char marker_r1[] = "BE_R3:02 R1_DERIVED\n";
static const char marker_r2[] = "BE_R3:03 R2_BUILT_REWALKED\n";
static const char marker_hs[] = "BE_R3:04 HS_VS_STATE_VERIFIED\n";
static const char marker_binding[] = "BE_R3:05 BINDING_PREPARED\n";
static const char marker_fence[] = "BE_R3:06 HGATP_FENCED_PUBLISHED\n";
static const char marker_entry[] =
	"BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000\n";
/* The B5 lines; each value follows its fixed text. */
static const char marker_stce[] = "BE_B5:01 SSTC_STCE_READBACK henvcfg=";
static const char marker_controls[] =
	"BE_B5:02 GUEST_CONTROLS_CHECKED hstatus_controls=";
static const char marker_controls_hideleg[] = " hideleg=";
static const char marker_controls_hcounteren[] = " hcounteren=";
static const char marker_controls_vstimecmp[] = " vstimecmp=";
static const char marker_cleared[] = "BE_B5:03 GUEST_RAM_CLEARED private=";
static const char marker_cleared_shared[] = " shared=";
static const char marker_enter[] = "BE_B5:04 ENTER_GUEST pc=";
static const char marker_enter_sp[] = " sp=";
static const char marker_guest_shutdown[] =
	"BE_B5:05 GUEST_SHUTDOWN type=0 reason=0 exits=";
static const char marker_shutdown[] = "BE_B5:06 SHUTDOWN type=0 reason=0\n";
static const char marker_failure[] = "BE_B5:FAIL ";
static const char marker_detail[] = "BE_B5:DETAIL cause=";
static const char marker_detail_pc[] = " pc=";
static const char marker_detail_tval[] = " tval=";
static const char marker_detail_htval[] = " htval=";
static const char marker_srst[] = "BE_B5:SRST_RETURNED\n";
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
		.trap_vector = symbol_address(be_b5_trap_vector),
	};
}

/* A monitor line first ends any open guest line, so it starts a line. */
static enum be_r3_error write_monitor(const char *text, be_u64 length)
{
	enum be_r3_error error = BE_R3_ERROR_NONE;

	if (be_b5_console_close(&be_b5_console) != 0U)
		error = be_r3_platform_write(marker_newline, 1U);
	if (error == BE_R3_ERROR_NONE)
		error = be_r3_platform_write(text, length);
	return error;
}

static enum be_r3_error write_text(const char *text)
{
	be_u64 length = be_r3_text_length(text);

	if (length > BE_PAGE_SIZE)
		return BE_R3_ERROR_DBCN_RANGE;
	return write_monitor(text, length);
}

static enum be_r3_error write_line(void)
{
	be_b5_line_text(&be_b5_line, marker_newline);
	if (be_b5_line.overflow != 0U)
		return BE_R3_ERROR_DBCN_RANGE;
	return write_monitor(be_b5_line.text, be_b5_line.length);
}

static void line_start(const char *text)
{
	be_b5_line_reset(&be_b5_line);
	be_b5_line_text(&be_b5_line, text);
}

static void line_hex(const char *text, be_u64 value)
{
	be_b5_line_text(&be_b5_line, text);
	be_b5_line_hex(&be_b5_line, value);
}

/*
 * The single terminal path: report, request the accepted SRST shutdown
 * once, and halt. A failure while already terminal halts at once.
 */
static void terminal(enum be_b5_class failure, const struct be_r4_frame *frame,
		     int request_reset) __attribute__((noreturn));
static void terminal(enum be_b5_class failure, const struct be_r4_frame *frame,
		     int request_reset)
{
	if (be_b5_terminal_entered != 0U)
		be_r3_arch_halt();
	be_b5_terminal_entered = 1U;
	failure = be_b5_fail(&be_b5_control, failure);
	line_start(marker_failure);
	be_b5_line_text(&be_b5_line, be_b5_class_name(failure));
	(void)write_line();
	if (frame != (const struct be_r4_frame *)0) {
		line_start(marker_detail);
		be_b5_line_hex(&be_b5_line, frame->scause);
		line_hex(marker_detail_pc, frame->sepc);
		line_hex(marker_detail_tval, frame->stval);
		line_hex(marker_detail_htval, frame->htval);
		(void)write_line();
	}
	if (request_reset != 0)
		(void)be_r3_platform_reset();
	(void)write_text(marker_srst);
	be_r3_arch_halt();
}

void be_b5_runtime_terminal(enum be_b5_class failure)
{
	terminal(failure, (const struct be_r4_frame *)0, 1);
}

void be_b5_exit_terminal(struct be_r4_frame *frame)
{
	terminal(BE_B5_CLASS_EXCEPTION, frame, 1);
}

static void emit_text(const char *text)
{
	if (write_text(text) != BE_R3_ERROR_NONE)
		be_b5_runtime_terminal(BE_B5_CLASS_CONSOLE);
}

static void emit_line(void)
{
	if (write_line() != BE_R3_ERROR_NONE)
		be_b5_runtime_terminal(BE_B5_CLASS_CONSOLE);
}

static void boot_fail(void) __attribute__((noreturn));
static void boot_fail(void)
{
	be_b5_runtime_terminal(BE_B5_CLASS_BOOT);
}

static void run_r1(void)
{
	if (be_runtime_copy_inventory(&be_b5_runtime,
				      be_r1_inventory()) != BE_RUNTIME_OK ||
	    be_runtime_copy_proposal(&be_b5_runtime,
				     be_r1_proposal()) != BE_RUNTIME_OK ||
	    be_runtime_validate(&be_b5_runtime) != BE_RUNTIME_OK ||
	    be_runtime_seal(&be_b5_runtime) != BE_RUNTIME_OK ||
	    be_runtime_derive(&be_b5_runtime) != BE_RUNTIME_OK ||
	    be_r3_note_r1_derived(&be_b5_r3_control,
				  &be_b5_runtime) != BE_R3_ERROR_NONE)
		boot_fail();
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

	if (be_r2_build(&be_b5_runtime, pools, &be_b5_r2_output) !=
		    BE_CHECK_OK ||
	    be_r2_walk_and_check(&be_b5_runtime, pools, &be_b5_r2_output,
				 be_b5_leaf_sets) != BE_CHECK_OK ||
	    be_r3_note_r2_built(&be_b5_r3_control, &be_b5_runtime,
				&be_b5_r2_output,
				be_b5_leaf_sets) != BE_R3_ERROR_NONE)
		boot_fail();
}

/* Henvcfg first: a CPU without Sstc fails closed before vstimecmp exists. */
static void arm_guest_controls(void)
{
	be_u64 henvcfg = be_b5_arch_arm_stce();
	enum be_b5_class failure = be_b5_stce_class(henvcfg);

	if (failure != BE_B5_CLASS_NONE)
		be_b5_runtime_terminal(failure);
	line_start(marker_stce);
	be_b5_line_hex(&be_b5_line, henvcfg);
	emit_line();

	be_b5_arch_arm_controls(&be_b5_armed);
	if (!be_b5_controls_valid(&be_b5_armed,
				  be_b5_r3_control.active.hgatp))
		be_b5_runtime_terminal(BE_B5_CLASS_CONTROLS);
	line_start(marker_controls);
	be_b5_line_hex(&be_b5_line,
		       be_b5_armed.hstatus & BE_R3_HSTATUS_CONTROL_MASK);
	line_hex(marker_controls_hideleg, be_b5_armed.hideleg);
	line_hex(marker_controls_hcounteren, be_b5_armed.hcounteren);
	line_hex(marker_controls_vstimecmp, be_b5_armed.vstimecmp);
	emit_line();
}

/* Zero the guest's private and shared pages through their HS backing. */
static void clear_guest_ram(void)
{
	volatile be_u64 *private_page =
		(volatile be_u64 *)(void *)__be_private_management_start;
	volatile be_u64 *shared_page =
		(volatile be_u64 *)(void *)__be_shared_start;
	be_u64 residue = 0U;
	be_size index;

	for (index = 0U; index < BE_PAGE_SIZE / sizeof(be_u64); ++index) {
		private_page[index] = 0U;
		shared_page[index] = 0U;
	}
	for (index = 0U; index < BE_PAGE_SIZE / sizeof(be_u64); ++index)
		residue |= private_page[index] | shared_page[index];
	if (residue != 0U)
		boot_fail();
	line_start(marker_cleared);
	be_b5_line_hex(&be_b5_line, BE_R0_GPA_MANAGEMENT_PRIVATE);
	line_hex(marker_cleared_shared, BE_R0_GPA_SHARED);
	emit_line();
}

/* Copy, tag, and write guest bytes; firmware sees only the HS page. */
static void guest_console(be_u64 length)
{
	be_u64 tagged = be_b5_console_tag(&be_b5_console, be_b5_guest_bytes,
					  length, be_b5_tagged,
					  sizeof(be_b5_tagged));

	if (tagged == BE_B5_TAG_INVALID ||
	    be_r3_platform_write(be_b5_tagged, tagged) != BE_R3_ERROR_NONE)
		be_b5_runtime_terminal(BE_B5_CLASS_CONSOLE);
}

static void guest_write(const struct be_b5_result *result)
{
	const volatile be_u8 *source =
		(const volatile be_u8 *)(void *)result->source_pa;
	be_u64 index;

	if (result->length > BE_B5_DBCN_MAX_BYTES)
		be_b5_runtime_terminal(BE_B5_CLASS_CONSOLE);
	for (index = 0U; index < result->length; ++index)
		be_b5_guest_bytes[index] = source[index];
	guest_console(result->length);
}

static void guest_write_byte(const struct be_b5_result *result)
{
	be_b5_guest_bytes[0] = result->byte;
	guest_console(1U);
}

static void guest_shutdown(void) __attribute__((noreturn));
static void guest_shutdown(void)
{
	line_start(marker_guest_shutdown);
	be_b5_line_decimal(&be_b5_line, be_b5_control.exits);
	emit_line();
	emit_text(marker_shutdown);
	(void)be_r3_platform_reset();
	/* A conforming shutdown does not return. */
	terminal(BE_B5_CLASS_SHUTDOWN_RETURNED, (const struct be_r4_frame *)0,
		 0);
}

void be_b5_dispatch(struct be_r4_frame *frame)
{
	struct be_b5_result result;

	if (frame != (struct be_r4_frame *)(void *)__be_saved_management_start)
		be_b5_runtime_terminal(BE_B5_CLASS_EXCEPTION);
	switch (be_b5_handle_exit(&be_b5_control, &be_b5_leaf_sets[0], frame,
				  &result)) {
	case BE_B5_ACTION_RETURN:
		break;
	case BE_B5_ACTION_CONSOLE_WRITE:
		guest_write(&result);
		break;
	case BE_B5_ACTION_CONSOLE_BYTE:
		guest_write_byte(&result);
		break;
	case BE_B5_ACTION_SET_TIMER:
		be_b5_arch_set_timer(result.timer);
		break;
	case BE_B5_ACTION_SHUTDOWN:
		guest_shutdown();
	case BE_B5_ACTION_GUEST_FAILURE:
		be_b5_runtime_terminal(BE_B5_CLASS_GUEST_FAILURE);
	case BE_B5_ACTION_NONE:
	case BE_B5_ACTION_TERMINAL:
	default:
		terminal(result.failure, frame, 1);
	}
	be_b5_apply_return(frame, &result);
	be_b5_arch_resume(frame, be_b5_r3_control.active.hgatp);
}

void be_b5_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
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

	build_image_layout(&be_b5_layout);
	boot.entry = symbol_address(be_reset);
	boot.hart_id = hart_id;
	boot.firmware_pointer = firmware_pointer;
	boot.layout = be_b5_layout;
	if (be_r3_platform_get_spec_version(&boot.sbi_spec_version) !=
		    BE_R0_SBI_SUCCESS ||
	    be_r3_platform_probe_extension(BE_R0_SBI_EID_DBCN,
					 &boot.dbcn_probe) != BE_R0_SBI_SUCCESS ||
	    be_r3_platform_probe_extension(BE_R0_SBI_EID_SRST,
					 &boot.srst_probe) != BE_R0_SBI_SUCCESS ||
	    be_r3_validate_boot(&be_b5_r3_control, &boot) != BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_boot);
	run_r1();
	emit_text(marker_r1);
	run_r2();
	emit_text(marker_r2);

	be_r3_arch_reset_state(be_b5_layout.trap_vector, &be_b5_hs);
	if (be_r3_note_hs_ready(&be_b5_r3_control, &be_b5_hs,
				&be_b5_layout) != BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_hs);
	if (be_r3_prepare_management_binding(&be_b5_r3_control, &binding) !=
	    BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_binding);
	hgatp_readback = be_r3_arch_install_management(binding.hgatp);
	if (be_r3_publish_management_binding(&be_b5_r3_control, hgatp_readback,
					     1U) != BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_fence);
	if (be_r3_arm_management_entry(&be_b5_r3_control,
				       &be_b5_r3_control.active) !=
	    BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_entry);

	arm_guest_controls();
	clear_guest_ram();
	line_start(marker_enter);
	be_b5_line_hex(&be_b5_line, be_b5_r3_control.active.guest_pc);
	line_hex(marker_enter_sp, be_b5_r3_control.active.guest_sp);
	emit_line();
	be_r3_arch_enter_management(be_b5_r3_control.active.guest_pc,
				    be_b5_r3_control.active.guest_sp,
				    be_b5_r3_control.active.trusted_sp);
}
