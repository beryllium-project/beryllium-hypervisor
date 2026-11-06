// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B6 runtime: the accepted R3 boot sequence in R5's order
 *          through BE_R3:06, then the B6-owned G-stage root (built,
 *          re-walked, and installed by a second call to the accepted R3
 *          install function), the guest controls, the payload checks, the
 *          guest RAM clear, the kernel and DTB placement, the first entry
 *          into the Linux guest, and the service of each guest exit through
 *          the pure-C SBI core.
 * Trust:   privileged restricted-C orchestration. Every CSR access, the
 *          fence.i, the frame transfer, and the SRET tail stay in assembly;
 *          every hgatp write and hfence.gvma stays in the accepted R3
 *          functions; the HS-to-M SBI calls go only through the accepted
 *          platform helpers. Guest bytes are read only through a
 *          translation the SBI core derived from the re-walked B6 window.
 * Scope:   one Linux guest on hart 0 (planning/k3-b6-plan.md). R4/R5 are
 *          not linked; the accepted roots are built and re-walked but never
 *          installed for an entry, and the management binding is published
 *          but never armed or entered.
 */
#include "b6-platform.h"

#include <be/r1-config.h>

#include "b6-payload-layout.h"
#include "r0-layout.h"
#include "r0-sbi.h"

_Static_assert(sizeof(struct be_b6_controls) == 128U,
	       "assembly controls size mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_controls, hip) == 0U,
	       "assembly controls hip offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_controls, hstatus) == 8U,
	       "assembly controls hstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_controls, hedeleg) == 16U,
	       "assembly controls hedeleg offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_controls, henvcfg) == 64U,
	       "assembly controls henvcfg offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_controls, vstimecmp) == 80U,
	       "assembly controls vstimecmp offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_controls, sstatus) == 96U,
	       "assembly controls sstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_controls, vsatp) == 112U,
	       "assembly controls vsatp offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_controls, sscratch) == 120U,
	       "assembly controls sscratch offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_exit, hstatus) == 320U,
	       "assembly exit hstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_exit, htinst) == 328U,
	       "assembly exit htinst offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_exit, vsatp) == 336U,
	       "assembly exit vsatp offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_exit, time) == 344U,
	       "assembly exit time offset mismatch");
_Static_assert(BE_B6_CLASS_EXCEPTION == 11, "assembly class moved");
_Static_assert(BE_B6_CLASS_RESUME == 14, "assembly class moved");
_Static_assert(BE_B6_HSTATUS_GUEST_CONTROLS == BE_U64_C(0x180),
	       "assembly hstatus guest controls mismatch");
_Static_assert(BE_B6_HSTATUS_VIRTUAL_TRAPS == BE_U64_C(0x700000),
	       "assembly hstatus virtual traps mismatch");
_Static_assert(BE_R3_HSTATUS_CONTROL_MASK == BE_U64_C(0x73f380),
	       "assembly hstatus mask mismatch");
_Static_assert(BE_B6_SSTATUS_CONTROL_MASK == BE_U64_C(0xde722),
	       "assembly sstatus mask mismatch");
_Static_assert(BE_B6_HEDELEG == BE_U64_C(0xb15d),
	       "assembly hedeleg mismatch");
_Static_assert(BE_R3_INITIAL_TRUSTED_SP == BE_U64_C(0x102027000),
	       "the trusted-stack top moved");
/* tests/check-b6-image.py reads these from the linked image. */
_Static_assert(sizeof(struct be_b6_payload_layout) == 56U,
	       "image checker payload layout size mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_state, exit_ceiling) == 72U,
	       "image checker exit ceiling offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b6_state, time_budget) == 80U,
	       "image checker guest-time budget offset mismatch");
/* The generated payload layout keeps every budget (stop condition 3). */
_Static_assert(BE_B6_PAYLOAD_KERNEL_BYTES >= BE_B6_KERNEL_HEADER_BYTES &&
	       BE_B6_PAYLOAD_KERNEL_BYTES <= BE_B6_KERNEL_FILE_MAX,
	       "kernel file outside its budget");
_Static_assert(BE_B6_PAYLOAD_KERNEL_IMAGE_SIZE >= BE_B6_PAYLOAD_KERNEL_BYTES &&
	       BE_B6_PAYLOAD_KERNEL_IMAGE_SIZE <= BE_B6_KERNEL_IMAGE_SIZE_MAX,
	       "kernel image_size outside its budget");
_Static_assert(BE_B6_KERNEL_GPA + BE_B6_PAYLOAD_KERNEL_IMAGE_SIZE <=
	       BE_B6_DTB_GPA, "kernel span reaches the DTB slot");
_Static_assert(BE_B6_PAYLOAD_DTB_OFFSET ==
	       ((BE_B6_BOOT_KERNEL_OFFSET + BE_B6_PAYLOAD_KERNEL_BYTES +
		 BE_B6_PAYLOAD_ALIGN - 1U) & ~(BE_B6_PAYLOAD_ALIGN - 1U)),
	       "DTB does not follow the kernel at 4 KiB");
_Static_assert(BE_B6_PAYLOAD_IMAGE_BYTES ==
	       BE_B6_PAYLOAD_DTB_OFFSET + BE_B6_DTB_BYTES,
	       "the DTB does not end the boot image");
_Static_assert(BE_B6_PAYLOAD_IMAGE_BYTES <= BE_B6_BOOT_IMAGE_MAX,
	       "boot image outside its budget");

/* The staged payload, as generated from the pinned payload files. */
const struct be_b6_payload_layout be_b6_payload_layout = {
	.staging_hpa = BE_B6_STAGING_HPA,
	.kernel_offset = BE_B6_BOOT_KERNEL_OFFSET,
	.kernel_bytes = BE_B6_PAYLOAD_KERNEL_BYTES,
	.kernel_image_size = BE_B6_PAYLOAD_KERNEL_IMAGE_SIZE,
	.dtb_offset = BE_B6_PAYLOAD_DTB_OFFSET,
	.dtb_bytes = BE_B6_DTB_BYTES,
	.image_bytes = BE_B6_PAYLOAD_IMAGE_BYTES,
};

static struct be_runtime be_b6_runtime = BE_RUNTIME_INITIALIZER;
static struct be_r2_output be_b6_r2_output;
static struct be_r2_leaf_set be_b6_leaf_sets[BE_MAX_ROOTS];
static struct be_r3_state be_b6_r3_control = BE_R3_STATE_INITIALIZER;
static struct be_r3_image_layout be_b6_layout;
static struct be_r3_hs_state be_b6_hs;
static struct be_b6_gstage_map be_b6_map;
static struct be_b6_payload_plan be_b6_plan;
static struct be_b6_state be_b6_control = BE_B6_STATE_INITIALIZER(
	BE_B6_RUN_EXIT_CEILING, BE_B6_RUN_GUEST_TIME_BUDGET);
static struct be_b6_controls be_b6_armed;
static be_u32 be_b6_controls_read;
static struct be_b6_console be_b6_console;
static struct be_b6_line be_b6_line;
static be_u8 be_b6_guest_bytes[BE_B6_DBCN_MAX_BYTES];
static char be_b6_tagged[BE_B6_TAGGED_CAPACITY];
static be_u32 be_b6_terminal_entered;

/* The accepted R3 lines, as accepted arch/riscv/be/r5-runtime.c prints them. */
static const char marker_boot[] = "BE_R3:01 BOOT_VALIDATED\n";
static const char marker_r1[] = "BE_R3:02 R1_DERIVED\n";
static const char marker_r2[] = "BE_R3:03 R2_BUILT_REWALKED\n";
static const char marker_hs[] = "BE_R3:04 HS_VS_STATE_VERIFIED\n";
static const char marker_binding[] = "BE_R3:05 BINDING_PREPARED\n";
static const char marker_fence[] = "BE_R3:06 HGATP_FENCED_PUBLISHED\n";
/* The B6 lines; each value follows its fixed text. */
static const char marker_gstage[] = "BE_B6:01 GSTAGE_BUILT_REWALKED gpa=";
static const char marker_gstage_hpa[] = " hpa=";
static const char marker_size[] = " size=";
static const char marker_gstage_leaves[] = " leaves=";
static const char marker_gstage_pool[] = " pool=";
static const char marker_installed[] = "BE_B6:02 HGATP_INSTALLED hgatp=";
static const char marker_stce[] = "BE_B6:03 SSTC_STCE_READBACK henvcfg=";
static const char marker_controls[] =
	"BE_B6:04 GUEST_CONTROLS_CHECKED hstatus_controls=";
static const char marker_controls_hedeleg[] = " hedeleg=";
static const char marker_controls_hideleg[] = " hideleg=";
static const char marker_controls_hcounteren[] = " hcounteren=";
static const char marker_controls_fs[] = " fs=";
static const char marker_controls_vs[] = " vs=";
static const char marker_controls_vstimecmp[] = " vstimecmp=";
static const char marker_cleared[] = "BE_B6:05 GUEST_RAM_CLEARED gpa=";
static const char marker_ticks[] = " ticks=";
static const char marker_placed[] = "BE_B6:06 PAYLOAD_PLACED kernel=";
static const char marker_placed_kernel_bytes[] = " kernel_bytes=";
static const char marker_placed_image_size[] = " image_size=";
static const char marker_placed_dtb[] = " dtb=";
static const char marker_placed_dtb_bytes[] = " dtb_bytes=";
static const char marker_enter[] = "BE_B6:07 ENTER_GUEST pc=";
static const char marker_enter_a0[] = " a0=";
static const char marker_enter_a1[] = " a1=";
static const char marker_guest_shutdown[] =
	"BE_B6:08 GUEST_SHUTDOWN type=0 reason=0 exits=";
static const char marker_count_base[] = " base=";
static const char marker_count_time[] = " time=";
static const char marker_count_dbcn_write[] = " dbcn_write=";
static const char marker_count_dbcn_read[] = " dbcn_read=";
static const char marker_count_dbcn_byte[] = " dbcn_byte=";
static const char marker_count_srst[] = " srst=";
static const char marker_count_refused[] = " refused=";
static const char marker_shutdown[] = "BE_B6:09 SHUTDOWN type=0 reason=0\n";
static const char marker_failure[] = "BE_B6:FAIL ";
static const char marker_detail[] = "BE_B6:DETAIL cause=";
static const char marker_detail_pc[] = " pc=";
static const char marker_detail_tval[] = " tval=";
static const char marker_detail_htval[] = " htval=";
static const char marker_detail_htinst[] = " htinst=";
static const char marker_detail_spvp[] = " spvp=";
static const char marker_detail_vsatp[] = " vsatp=";
static const char marker_detail_exits[] = " exits=";
/* A controls failure after arming prints every readback, in two lines. */
static const char marker_controls_detail[] = "BE_B6:DETAIL controls hip=";
static const char marker_controls_detail_more[] =
	"BE_B6:DETAIL controls henvcfg=";
static const char marker_field_hstatus[] = " hstatus=";
static const char marker_field_hie[] = " hie=";
static const char marker_field_hvip[] = " hvip=";
static const char marker_field_htimedelta[] = " htimedelta=";
static const char marker_field_hgeie[] = " hgeie=";
static const char marker_field_sie[] = " sie=";
static const char marker_field_sstatus[] = " sstatus=";
static const char marker_field_hgatp[] = " hgatp=";
static const char marker_field_sscratch[] = " sscratch=";
static const char marker_srst[] = "BE_B6:SRST_RETURNED\n";
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
		.trap_vector = symbol_address(be_b6_trap_vector),
	};
}

/* A monitor line first ends any open guest line, so it starts a line. */
static enum be_r3_error write_monitor(const char *text, be_u64 length)
{
	enum be_r3_error error = BE_R3_ERROR_NONE;

	if (be_b6_console_close(&be_b6_console) != 0U)
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
	be_b6_line_text(&be_b6_line, marker_newline);
	if (be_b6_line.overflow != 0U)
		return BE_R3_ERROR_DBCN_RANGE;
	return write_monitor(be_b6_line.text, be_b6_line.length);
}

static void line_start(const char *text)
{
	be_b6_line_reset(&be_b6_line);
	be_b6_line_text(&be_b6_line, text);
}

static void line_hex(const char *text, be_u64 value)
{
	be_b6_line_text(&be_b6_line, text);
	be_b6_line_hex(&be_b6_line, value);
}

static void line_decimal(const char *text, be_u64 value)
{
	be_b6_line_text(&be_b6_line, text);
	be_b6_line_decimal(&be_b6_line, value);
}

/* Every guest-control readback, so a board mismatch names its field. */
static void controls_detail(void)
{
	line_start(marker_controls_detail);
	be_b6_line_hex(&be_b6_line, be_b6_armed.hip);
	line_hex(marker_field_hstatus, be_b6_armed.hstatus);
	line_hex(marker_controls_hedeleg, be_b6_armed.hedeleg);
	line_hex(marker_controls_hideleg, be_b6_armed.hideleg);
	line_hex(marker_field_hie, be_b6_armed.hie);
	line_hex(marker_field_hvip, be_b6_armed.hvip);
	line_hex(marker_controls_hcounteren, be_b6_armed.hcounteren);
	line_hex(marker_field_htimedelta, be_b6_armed.htimedelta);
	(void)write_line();
	line_start(marker_controls_detail_more);
	be_b6_line_hex(&be_b6_line, be_b6_armed.henvcfg);
	line_hex(marker_field_hgeie, be_b6_armed.hgeie);
	line_hex(marker_controls_vstimecmp, be_b6_armed.vstimecmp);
	line_hex(marker_field_sie, be_b6_armed.sie);
	line_hex(marker_field_sstatus, be_b6_armed.sstatus);
	line_hex(marker_field_hgatp, be_b6_armed.hgatp);
	line_hex(marker_detail_vsatp, be_b6_armed.vsatp);
	line_hex(marker_field_sscratch, be_b6_armed.sscratch);
	(void)write_line();
}

/*
 * The single terminal path: report, request the accepted SRST shutdown
 * once, and halt. A failure while already terminal halts at once. An exit
 * failure adds the exit's DETAIL line.
 */
static void terminal(enum be_b6_class failure, const struct be_b6_exit *record,
		     int request_reset) __attribute__((noreturn));
static void terminal(enum be_b6_class failure, const struct be_b6_exit *record,
		     int request_reset)
{
	if (be_b6_terminal_entered != 0U)
		be_r3_arch_halt();
	be_b6_terminal_entered = 1U;
	failure = be_b6_fail(&be_b6_control, failure);
	line_start(marker_failure);
	be_b6_line_text(&be_b6_line, be_b6_class_name(failure));
	(void)write_line();
	if (failure == BE_B6_CLASS_CONTROLS && be_b6_controls_read != 0U)
		controls_detail();
	if (record != (const struct be_b6_exit *)0) {
		line_start(marker_detail);
		be_b6_line_hex(&be_b6_line, record->frame.scause);
		line_hex(marker_detail_pc, record->frame.sepc);
		line_hex(marker_detail_tval, record->frame.stval);
		line_hex(marker_detail_htval, record->frame.htval);
		line_hex(marker_detail_htinst, record->htinst);
		line_decimal(marker_detail_spvp,
			     (record->hstatus & BE_B6_HSTATUS_SPVP) != 0U ?
			     1U : 0U);
		line_hex(marker_detail_vsatp, record->vsatp);
		line_decimal(marker_detail_exits, be_b6_control.counts.exits);
		(void)write_line();
	}
	if (request_reset != 0)
		(void)be_r3_platform_reset();
	(void)write_text(marker_srst);
	be_r3_arch_halt();
}

void be_b6_runtime_terminal(enum be_b6_class failure)
{
	terminal(failure, (const struct be_b6_exit *)0, 1);
}

void be_b6_exit_terminal(struct be_b6_exit *record)
{
	terminal(BE_B6_CLASS_EXCEPTION, record, 1);
}

static void emit_text(const char *text)
{
	if (write_text(text) != BE_R3_ERROR_NONE)
		be_b6_runtime_terminal(BE_B6_CLASS_CONSOLE);
}

static void emit_line(void)
{
	if (write_line() != BE_R3_ERROR_NONE)
		be_b6_runtime_terminal(BE_B6_CLASS_CONSOLE);
}

static void boot_fail(void) __attribute__((noreturn));
static void boot_fail(void)
{
	be_b6_runtime_terminal(BE_B6_CLASS_BOOT);
}

static void run_r1(void)
{
	if (be_runtime_copy_inventory(&be_b6_runtime,
				      be_r1_inventory()) != BE_RUNTIME_OK ||
	    be_runtime_copy_proposal(&be_b6_runtime,
				     be_r1_proposal()) != BE_RUNTIME_OK ||
	    be_runtime_validate(&be_b6_runtime) != BE_RUNTIME_OK ||
	    be_runtime_seal(&be_b6_runtime) != BE_RUNTIME_OK ||
	    be_runtime_derive(&be_b6_runtime) != BE_RUNTIME_OK ||
	    be_r3_note_r1_derived(&be_b6_r3_control,
				  &be_b6_runtime) != BE_R3_ERROR_NONE)
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

	if (be_r2_build(&be_b6_runtime, pools, &be_b6_r2_output) !=
		    BE_CHECK_OK ||
	    be_r2_walk_and_check(&be_b6_runtime, pools, &be_b6_r2_output,
				 be_b6_leaf_sets) != BE_CHECK_OK ||
	    be_r3_note_r2_built(&be_b6_r3_control, &be_b6_runtime,
				&be_b6_r2_output,
				be_b6_leaf_sets) != BE_R3_ERROR_NONE)
		boot_fail();
}

/*
 * The B6 root: build it in the NOLOAD pool, re-walk every pool byte, and
 * install the walked hgatp with a second call to the accepted R3 install
 * function, which writes hgatp, fences, and reads back.
 */
static void build_gstage(void)
{
	struct be_b6_gstage_desc desc = {
		.gpa_base = BE_B6_GUEST_GPA, .hpa_base = BE_B6_GUEST_HPA,
		.size = BE_B6_GUEST_BYTES, .pool_pa = BE_B6_POOL_HPA,
	};
	be_u64 hgatp_readback;

	if (symbol_address(__be_b6_pool_start) != BE_B6_POOL_HPA ||
	    symbol_address(__be_b6_pool_end) !=
		    BE_B6_POOL_HPA + BE_B6_POOL_BYTES ||
	    be_b6_gstage_build(&desc, __be_b6_pool_start,
			       BE_B6_POOL_BYTES) != BE_B6_GSTAGE_OK ||
	    be_b6_gstage_walk(&desc, __be_b6_pool_start, BE_B6_POOL_BYTES,
			      &be_b6_map) != BE_B6_GSTAGE_OK ||
	    be_b6_map.hgatp != BE_B6_HGATP ||
	    be_b6_map.leaves != BE_B6_GUEST_LEAVES)
		be_b6_runtime_terminal(BE_B6_CLASS_GSTAGE);
	line_start(marker_gstage);
	be_b6_line_hex(&be_b6_line, be_b6_map.gpa_base);
	line_hex(marker_gstage_hpa, be_b6_map.hpa_base);
	line_hex(marker_size, be_b6_map.size);
	line_decimal(marker_gstage_leaves, be_b6_map.leaves);
	line_hex(marker_gstage_pool, be_b6_map.pool_pa);
	emit_line();

	hgatp_readback = be_r3_arch_install_management(be_b6_map.hgatp);
	if (hgatp_readback != be_b6_map.hgatp)
		be_b6_runtime_terminal(BE_B6_CLASS_GSTAGE);
	line_start(marker_installed);
	be_b6_line_hex(&be_b6_line, hgatp_readback);
	emit_line();
}

/* Henvcfg first: a CPU without Sstc fails closed before vstimecmp exists. */
static void arm_guest_controls(void)
{
	be_u64 henvcfg = be_b6_arch_arm_stce();
	enum be_b6_class failure = be_b6_stce_class(henvcfg);

	if (failure != BE_B6_CLASS_NONE)
		be_b6_runtime_terminal(failure);
	line_start(marker_stce);
	be_b6_line_hex(&be_b6_line, henvcfg);
	emit_line();

	be_b6_arch_arm_controls(&be_b6_armed,
				symbol_address(__be_stack_management_end));
	be_b6_controls_read = 1U;
	if (!be_b6_controls_valid(&be_b6_armed, be_b6_map.hgatp,
				  symbol_address(__be_stack_management_end)))
		be_b6_runtime_terminal(BE_B6_CLASS_CONTROLS);
	line_start(marker_controls);
	be_b6_line_hex(&be_b6_line,
		       be_b6_armed.hstatus & BE_R3_HSTATUS_CONTROL_MASK);
	line_hex(marker_controls_hedeleg, be_b6_armed.hedeleg);
	line_hex(marker_controls_hideleg, be_b6_armed.hideleg);
	line_hex(marker_controls_hcounteren, be_b6_armed.hcounteren);
	line_hex(marker_controls_fs,
		 (be_b6_armed.sstatus & BE_R3_SSTATUS_FS_MASK) >> 13);
	line_hex(marker_controls_vs,
		 (be_b6_armed.sstatus & BE_B6_SSTATUS_VS_MASK) >> 9);
	line_hex(marker_controls_vstimecmp, be_b6_armed.vstimecmp);
	emit_line();
}

/* Shape checks on the staged payload, before the window is touched. */
static void check_payload(void)
{
	const be_u8 *staged =
		(const be_u8 *)(void *)be_b6_payload_layout.staging_hpa;

	if (be_b6_payload_check(&be_b6_payload_layout, &be_b6_map, staged,
				&be_b6_plan) != BE_B6_PAYLOAD_OK)
		be_b6_runtime_terminal(BE_B6_CLASS_PAYLOAD);
}

/* Zero the whole guest window through its HS backing, and read it back. */
static void clear_guest_ram(void)
{
	volatile be_u64 *window = (volatile be_u64 *)(void *)be_b6_map.hpa_base;
	be_u64 words = be_b6_map.size / sizeof(be_u64);
	be_u64 residue = 0U;
	be_u64 start = be_b6_arch_read_time();
	be_u64 index;

	for (index = 0U; index < words; ++index)
		window[index] = 0U;
	for (index = 0U; index < words; ++index)
		residue |= window[index];
	if (residue != 0U)
		boot_fail();
	line_start(marker_cleared);
	be_b6_line_hex(&be_b6_line, be_b6_map.gpa_base);
	line_hex(marker_size, be_b6_map.size);
	line_hex(marker_ticks, be_b6_arch_read_time() - start);
	emit_line();
}

/* Copy one staged object into the window, and compare the copy. */
static be_u64 place(be_u64 target, be_u64 source, be_u64 bytes)
{
	volatile be_u64 *to = (volatile be_u64 *)(void *)target;
	const volatile be_u64 *from =
		(const volatile be_u64 *)(const void *)source;
	volatile be_u8 *to_tail = (volatile be_u8 *)(void *)target;
	const volatile be_u8 *from_tail =
		(const volatile be_u8 *)(const void *)source;
	be_u64 words = bytes / sizeof(be_u64);
	be_u64 residue = 0U;
	be_u64 index;

	for (index = 0U; index < words; ++index)
		to[index] = from[index];
	for (index = words * sizeof(be_u64); index < bytes; ++index)
		to_tail[index] = from_tail[index];
	for (index = 0U; index < words; ++index)
		residue |= to[index] ^ from[index];
	for (index = words * sizeof(be_u64); index < bytes; ++index)
		residue |= (be_u64)(to_tail[index] ^ from_tail[index]);
	return residue;
}

static void place_payload(void)
{
	be_u64 start = be_b6_arch_read_time();

	if ((place(be_b6_plan.kernel_target, be_b6_plan.kernel_source,
		   be_b6_plan.kernel_bytes) |
	     place(be_b6_plan.dtb_target, be_b6_plan.dtb_source,
		   be_b6_plan.dtb_bytes)) != 0U)
		boot_fail();
	line_start(marker_placed);
	be_b6_line_hex(&be_b6_line, be_b6_plan.kernel_gpa);
	line_hex(marker_placed_kernel_bytes, be_b6_plan.kernel_bytes);
	line_hex(marker_placed_image_size, be_b6_plan.image_size);
	line_hex(marker_placed_dtb, be_b6_plan.dtb_gpa);
	line_hex(marker_placed_dtb_bytes, be_b6_plan.dtb_bytes);
	line_hex(marker_ticks, be_b6_arch_read_time() - start);
	emit_line();
	be_b6_arch_fence_i();
}

/* Copy, tag, and write guest bytes; firmware sees only the HS page. */
static void guest_console(be_u64 length)
{
	be_u64 tagged = be_b6_console_tag(&be_b6_console, be_b6_guest_bytes,
					  length, be_b6_tagged,
					  sizeof(be_b6_tagged));

	if (tagged == BE_B6_TAG_INVALID ||
	    be_r3_platform_write(be_b6_tagged, tagged) != BE_R3_ERROR_NONE)
		be_b6_runtime_terminal(BE_B6_CLASS_CONSOLE);
}

static void guest_write(const struct be_b6_result *result)
{
	const volatile be_u8 *source =
		(const volatile be_u8 *)(void *)result->source_pa;
	be_u64 index;

	if (result->length > BE_B6_DBCN_MAX_BYTES)
		be_b6_runtime_terminal(BE_B6_CLASS_CONSOLE);
	for (index = 0U; index < result->length; ++index)
		be_b6_guest_bytes[index] = source[index];
	guest_console(result->length);
}

static void guest_write_byte(const struct be_b6_result *result)
{
	be_b6_guest_bytes[0] = result->byte;
	guest_console(1U);
}

static void guest_shutdown(const struct be_b6_exit *record)
	__attribute__((noreturn));
static void guest_shutdown(const struct be_b6_exit *record)
{
	const struct be_b6_counts *counts = &be_b6_control.counts;

	line_start(marker_guest_shutdown);
	be_b6_line_decimal(&be_b6_line, counts->exits);
	line_decimal(marker_count_base, counts->base);
	line_decimal(marker_count_time, counts->time);
	line_decimal(marker_count_dbcn_write, counts->dbcn_write);
	line_decimal(marker_count_dbcn_read, counts->dbcn_read);
	line_decimal(marker_count_dbcn_byte, counts->dbcn_byte);
	line_decimal(marker_count_srst, counts->srst);
	line_decimal(marker_count_refused, counts->refused);
	line_hex(marker_ticks, record->time - be_b6_control.entry_time);
	emit_line();
	emit_text(marker_shutdown);
	(void)be_r3_platform_reset();
	/* A conforming shutdown does not return. */
	terminal(BE_B6_CLASS_SHUTDOWN_RETURNED, (const struct be_b6_exit *)0,
		 0);
}

void be_b6_dispatch(struct be_b6_exit *record)
{
	struct be_b6_result result;

	if (record != (struct be_b6_exit *)(void *)__be_saved_management_start)
		be_b6_runtime_terminal(BE_B6_CLASS_EXCEPTION);
	switch (be_b6_handle_exit(&be_b6_control, &be_b6_map, record,
				  &result)) {
	case BE_B6_ACTION_RETURN:
		break;
	case BE_B6_ACTION_CONSOLE_WRITE:
		guest_write(&result);
		break;
	case BE_B6_ACTION_CONSOLE_BYTE:
		guest_write_byte(&result);
		break;
	case BE_B6_ACTION_SET_TIMER:
		be_b6_arch_set_timer(result.timer);
		break;
	case BE_B6_ACTION_SHUTDOWN:
		guest_shutdown(record);
	case BE_B6_ACTION_GUEST_FAILURE:
	case BE_B6_ACTION_GUEST_REBOOT:
	case BE_B6_ACTION_NONE:
	case BE_B6_ACTION_TERMINAL:
	default:
		terminal(result.failure, record, 1);
	}
	be_b6_apply_return(&record->frame, &result);
	be_b6_arch_resume(record, be_b6_map.hgatp, be_b6_armed.hedeleg);
}

/* The first entry: Linux's boot protocol through the same checked tail. */
static void enter_guest(void) __attribute__((noreturn));
static void enter_guest(void)
{
	struct be_b6_exit *record =
		(struct be_b6_exit *)(void *)__be_saved_management_start;

	be_b6_entry_frame(record, be_b6_plan.kernel_gpa, BE_B6_GUEST_HART,
			  be_b6_plan.dtb_gpa);
	line_start(marker_enter);
	be_b6_line_hex(&be_b6_line, record->frame.sepc);
	line_hex(marker_enter_a0, record->frame.gpr[BE_R4_GPR_A0]);
	line_hex(marker_enter_a1, record->frame.gpr[BE_R4_GPR_A1]);
	emit_line();
	be_b6_control.entry_time = be_b6_arch_read_time();
	be_b6_arch_resume(record, be_b6_map.hgatp, be_b6_armed.hedeleg);
}

void be_b6_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
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

	build_image_layout(&be_b6_layout);
	boot.entry = symbol_address(be_reset);
	boot.hart_id = hart_id;
	boot.firmware_pointer = firmware_pointer;
	boot.layout = be_b6_layout;
	if (be_r3_platform_get_spec_version(&boot.sbi_spec_version) !=
		    BE_R0_SBI_SUCCESS ||
	    be_r3_platform_probe_extension(BE_R0_SBI_EID_DBCN,
					 &boot.dbcn_probe) != BE_R0_SBI_SUCCESS ||
	    be_r3_platform_probe_extension(BE_R0_SBI_EID_SRST,
					 &boot.srst_probe) != BE_R0_SBI_SUCCESS ||
	    be_r3_validate_boot(&be_b6_r3_control, &boot) != BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_boot);
	run_r1();
	emit_text(marker_r1);
	run_r2();
	emit_text(marker_r2);

	be_r3_arch_reset_state(be_b6_layout.trap_vector, &be_b6_hs);
	if (be_r3_note_hs_ready(&be_b6_r3_control, &be_b6_hs,
				&be_b6_layout) != BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_hs);
	if (be_r3_prepare_management_binding(&be_b6_r3_control, &binding) !=
	    BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_binding);
	hgatp_readback = be_r3_arch_install_management(binding.hgatp);
	if (be_r3_publish_management_binding(&be_b6_r3_control, hgatp_readback,
					     1U) != BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_fence);

	build_gstage();
	arm_guest_controls();
	check_payload();
	clear_guest_ram();
	place_payload();
	enter_guest();
}
