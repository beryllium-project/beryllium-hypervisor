// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B7 runtime: the accepted R3 boot sequence in R5's order
 *          through BE_R3:06; then both B7-owned G-stage roots (built,
 *          re-walked, checked disjoint, and installed through the accepted
 *          R3 install function), the guest controls and the initial
 *          per-guest CSR set, the payload checks, both guest RAM clears, the
 *          kernel and DTB placement in both windows, and G0's first entry;
 *          then the service of each guest exit through the pure-C SBI core
 *          and scheduler: SBI calls, idling wfi, HS slices, the switch
 *          between the guests, the HS wait when both idle, each guest's
 *          shutdown, and the run's summary.
 * Trust:   privileged restricted-C orchestration. Every CSR access, the
 *          fence.i, the HS wfi, the frame transfer, and the SRET tail stay
 *          in assembly; every hgatp write and hfence.gvma stays in the
 *          accepted R3 install function, called here from R3's sequence
 *          and from install_root() alone; the HS-to-M SBI calls go only
 *          through the accepted platform helpers. Guest bytes are read only
 *          through a translation the SBI core derived from the calling
 *          guest's re-walked window.
 * Scope:   two Linux guests time-shared on hart 0 (planning/k3-b7-plan.md).
 *          R4/R5 are not linked; the accepted roots are built and re-walked
 *          but never installed for an entry, and the management binding is
 *          published but never armed or entered.
 */
#include "b7-platform.h"

#include <be/r1-config.h>

#include "b7-payload-layout.h"
#include "b7-sched.h"
#include "r0-layout.h"
#include "r0-sbi.h"

/* install_root() stays one function: its call is the second install site. */
#if defined(__clang__)
#define BE_B7_ONE_COPY			__attribute__((noinline))
#else
#define BE_B7_ONE_COPY			__attribute__((noinline, noclone))
#endif

_Static_assert(sizeof(struct be_b7_controls) == 128U,
	       "assembly controls size mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_controls, hip) == 0U,
	       "assembly controls hip offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_controls, hstatus) == 8U,
	       "assembly controls hstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_controls, hedeleg) == 16U,
	       "assembly controls hedeleg offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_controls, henvcfg) == 64U,
	       "assembly controls henvcfg offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_controls, vstimecmp) == 80U,
	       "assembly controls vstimecmp offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_controls, sstatus) == 96U,
	       "assembly controls sstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_controls, vsatp) == 112U,
	       "assembly controls vsatp offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_controls, sscratch) == 120U,
	       "assembly controls sscratch offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_exit, hstatus) == 320U,
	       "assembly exit hstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_exit, htinst) == 328U,
	       "assembly exit htinst offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_exit, vsatp) == 336U,
	       "assembly exit vsatp offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_exit, time) == 344U,
	       "assembly exit time offset mismatch");
_Static_assert(BE_B7_VCSR_COUNT == 11U && BE_B7_VCSR_VSSTATUS == 0 &&
	       BE_B7_VCSR_VSTIMECMP == 8 && BE_B7_VCSR_SENVCFG == 10,
	       "assembly per-guest CSR order mismatch");
_Static_assert(BE_B7_CLASS_EXCEPTION == 11, "assembly class moved");
_Static_assert(BE_B7_CLASS_RESUME == 14, "assembly class moved");
_Static_assert(BE_B7_HSTATUS_GUEST_CONTROLS == BE_U64_C(0x200180),
	       "assembly hstatus guest controls mismatch");
_Static_assert(BE_B7_HSTATUS_CLEARED_TRAPS == BE_U64_C(0x500000) &&
	       BE_B7_HSTATUS_VTW == BE_U64_C(0x200000),
	       "assembly hstatus virtual traps mismatch");
_Static_assert(BE_B7_HSTATUS_RESUME_MASK == BE_U64_C(0x73f280) &&
	       BE_B7_HSTATUS_RESUME_CONTROLS == BE_U64_C(0x200080),
	       "assembly hstatus resume controls mismatch");
_Static_assert(BE_R3_HSTATUS_CONTROL_MASK == BE_U64_C(0x73f380),
	       "assembly hstatus mask mismatch");
_Static_assert(BE_B7_SSTATUS_CONTROL_MASK == BE_U64_C(0xde722),
	       "assembly sstatus mask mismatch");
_Static_assert(BE_B7_SSTATUS_SPP == BE_B7_HSTATUS_SPVP,
	       "the tail sets SPP from SPVP in the same bit");
_Static_assert(BE_B7_HEDELEG == BE_U64_C(0xb15d),
	       "assembly hedeleg mismatch");
_Static_assert(BE_B7_SIE_STIE == BE_U64_C(0x20) &&
	       BE_B7_HVIP_VS_BITS == BE_U64_C(0x444),
	       "assembly sie and hvip mismatch");
_Static_assert(BE_R3_INITIAL_TRUSTED_SP == BE_U64_C(0x102027000),
	       "the trusted-stack top moved");
/* tests/check-b7-image.py reads these from the linked image. */
_Static_assert(sizeof(struct be_b7_payload_layout) == 64U,
	       "image checker payload layout size mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_state, exit_ceiling) == 0U,
	       "image checker exit ceiling offset mismatch");
_Static_assert(__builtin_offsetof(struct be_b7_state, time_budget) == 8U,
	       "image checker guest-time budget offset mismatch");
/* The generated payload layout keeps every budget (stop condition 3). */
_Static_assert(BE_B7_PAYLOAD_KERNEL_BYTES >= BE_B7_KERNEL_HEADER_BYTES &&
	       BE_B7_PAYLOAD_KERNEL_BYTES <= BE_B7_KERNEL_FILE_MAX,
	       "kernel file outside its budget");
_Static_assert(BE_B7_PAYLOAD_KERNEL_IMAGE_SIZE >= BE_B7_PAYLOAD_KERNEL_BYTES &&
	       BE_B7_PAYLOAD_KERNEL_IMAGE_SIZE <= BE_B7_KERNEL_IMAGE_SIZE_MAX,
	       "kernel image_size outside its budget");
_Static_assert(BE_B7_KERNEL_GPA + BE_B7_PAYLOAD_KERNEL_IMAGE_SIZE <=
	       BE_B7_DTB_GPA, "kernel span reaches the DTB slot");
_Static_assert(BE_B7_PAYLOAD_DTB0_OFFSET ==
	       ((BE_B7_BOOT_KERNEL_OFFSET + BE_B7_PAYLOAD_KERNEL_BYTES +
		 BE_B7_PAYLOAD_ALIGN - 1U) & ~(BE_B7_PAYLOAD_ALIGN - 1U)),
	       "G0's DTB does not follow the kernel at 4 KiB");
_Static_assert(BE_B7_PAYLOAD_DTB1_OFFSET ==
	       BE_B7_PAYLOAD_DTB0_OFFSET + BE_B7_DTB_BYTES,
	       "G1's DTB does not follow G0's");
_Static_assert(BE_B7_PAYLOAD_IMAGE_BYTES ==
	       BE_B7_PAYLOAD_DTB1_OFFSET + BE_B7_DTB_BYTES,
	       "G1's DTB does not end the boot image");
_Static_assert(BE_B7_PAYLOAD_IMAGE_BYTES <= BE_B7_BOOT_IMAGE_MAX,
	       "boot image outside its budget");
_Static_assert(BE_B7_POOL_HPA + BE_B7_POOL_BYTES <= BE_B7_STAGING_HPA,
	       "the pool ends below the staged image");

/* The staged payload, as generated from the pinned payload files. */
const struct be_b7_payload_layout be_b7_payload_layout = {
	.staging_hpa = BE_B7_STAGING_HPA,
	.kernel_offset = BE_B7_BOOT_KERNEL_OFFSET,
	.kernel_bytes = BE_B7_PAYLOAD_KERNEL_BYTES,
	.kernel_image_size = BE_B7_PAYLOAD_KERNEL_IMAGE_SIZE,
	.dtb_offset = { BE_B7_PAYLOAD_DTB0_OFFSET, BE_B7_PAYLOAD_DTB1_OFFSET },
	.dtb_bytes = BE_B7_DTB_BYTES,
	.image_bytes = BE_B7_PAYLOAD_IMAGE_BYTES,
};

/* Each guest's window, pool, and VMID (b7-layout.h). */
static const struct be_b7_gstage_desc be_b7_descs[BE_B7_GUESTS] = {
	{ .gpa_base = BE_B7_GUEST_GPA, .hpa_base = BE_B7_G0_HPA,
	  .size = BE_B7_GUEST_BYTES, .pool_pa = BE_B7_G0_ROOT_HPA,
	  .vmid = BE_B7_G0_VMID },
	{ .gpa_base = BE_B7_GUEST_GPA, .hpa_base = BE_B7_G1_HPA,
	  .size = BE_B7_GUEST_BYTES, .pool_pa = BE_B7_G1_ROOT_HPA,
	  .vmid = BE_B7_G1_VMID },
};
static const be_u64 be_b7_hgatps[BE_B7_GUESTS] = {
	BE_B7_G0_HGATP, BE_B7_G1_HGATP,
};

static struct be_runtime be_b7_runtime = BE_RUNTIME_INITIALIZER;
static struct be_r2_output be_b7_r2_output;
static struct be_r2_leaf_set be_b7_leaf_sets[BE_MAX_ROOTS];
static struct be_r3_state be_b7_r3_control = BE_R3_STATE_INITIALIZER;
static struct be_r3_image_layout be_b7_layout;
static struct be_r3_hs_state be_b7_hs;
static struct be_b7_gstage_map be_b7_maps[BE_B7_GUESTS];
static struct be_b7_payload_plan be_b7_plans[BE_B7_GUESTS];
static struct be_b7_state be_b7_control = BE_B7_STATE_INITIALIZER(
	BE_B7_RUN_EXIT_CEILING, BE_B7_RUN_GUEST_TIME_BUDGET);
static struct be_b7_sched be_b7_sched;
static struct be_b7_vcpu be_b7_vcpus[BE_B7_GUESTS];
static struct be_b7_console be_b7_consoles[BE_B7_GUESTS];
static struct be_b7_controls be_b7_armed;
static be_u32 be_b7_controls_read;
static be_u32 be_b7_entered[BE_B7_GUESTS];
static be_u64 be_b7_readback[BE_B7_VCSR_COUNT];
static struct be_b7_line be_b7_line;
static be_u8 be_b7_guest_bytes[BE_B7_DBCN_MAX_BYTES];
static char be_b7_console_out[BE_B7_CONSOLE_CAPACITY];
static be_u32 be_b7_terminal_entered;
/* A switch readback mismatch, for its DETAIL line. */
static struct {
	be_u32 pending;
	be_u32 guest;
	const char *name;
	be_u64 wanted;
	be_u64 readback;
} be_b7_switch_fault;

/* The accepted R3 lines, as accepted arch/riscv/be/r5-runtime.c prints them. */
static const char marker_boot[] = "BE_R3:01 BOOT_VALIDATED\n";
static const char marker_r1[] = "BE_R3:02 R1_DERIVED\n";
static const char marker_r2[] = "BE_R3:03 R2_BUILT_REWALKED\n";
static const char marker_hs[] = "BE_R3:04 HS_VS_STATE_VERIFIED\n";
static const char marker_binding[] = "BE_R3:05 BINDING_PREPARED\n";
static const char marker_fence[] = "BE_R3:06 HGATP_FENCED_PUBLISHED\n";
/* The B7 lines; each value follows its fixed text. */
static const char marker_gstage[] = "BE_B7:01 GSTAGE_BUILT_REWALKED guest=";
static const char marker_gpa[] = " gpa=";
static const char marker_hpa[] = " hpa=";
static const char marker_size[] = " size=";
static const char marker_leaves[] = " leaves=";
static const char marker_root[] = " root=";
static const char marker_installed[] = "BE_B7:02 HGATP_INSTALLED g1=";
static const char marker_installed_g0[] = " g0=";
static const char marker_stce[] = "BE_B7:03 SSTC_STCE_READBACK henvcfg=";
static const char marker_controls[] =
	"BE_B7:04 GUEST_CONTROLS_CHECKED hstatus_controls=";
static const char marker_controls_hedeleg[] = " hedeleg=";
static const char marker_controls_hideleg[] = " hideleg=";
static const char marker_controls_hcounteren[] = " hcounteren=";
static const char marker_controls_sie[] = " sie=";
static const char marker_controls_fs[] = " fs=";
static const char marker_controls_vs[] = " vs=";
static const char marker_controls_vstimecmp[] = " vstimecmp=";
static const char marker_cleared[] = "BE_B7:05 GUEST_RAM_CLEARED guest=";
static const char marker_ticks[] = " ticks=";
static const char marker_placed[] = "BE_B7:06 PAYLOAD_PLACED guest=";
static const char marker_placed_kernel[] = " kernel=";
static const char marker_placed_kernel_bytes[] = " kernel_bytes=";
static const char marker_placed_image_size[] = " image_size=";
static const char marker_placed_dtb[] = " dtb=";
static const char marker_placed_dtb_bytes[] = " dtb_bytes=";
static const char marker_armed[] = "BE_B7:07 SCHEDULER_ARMED guests=";
static const char marker_armed_slice[] = " slice_ticks=";
static const char marker_armed_first[] = " first=";
static const char marker_enter[] = "BE_B7:08 ENTER_GUEST guest=";
static const char marker_enter_pc[] = " pc=";
static const char marker_enter_a0[] = " a0=";
static const char marker_enter_a1[] = " a1=";
static const char marker_guest_shutdown[] = "BE_B7:09 GUEST_SHUTDOWN guest=";
static const char marker_count_exits[] = " exits=";
static const char marker_count_sbi[] = " sbi=";
static const char marker_count_wfi[] = " wfi=";
static const char marker_count_slice[] = " slice=";
static const char marker_count_base[] = " base=";
static const char marker_count_time[] = " time=";
static const char marker_count_dbcn_write[] = " dbcn_write=";
static const char marker_count_dbcn_read[] = " dbcn_read=";
static const char marker_count_dbcn_byte[] = " dbcn_byte=";
static const char marker_count_srst[] = " srst=";
static const char marker_count_refused[] = " refused=";
static const char marker_complete[] = "BE_B7:10 RUN_COMPLETE switches=";
static const char marker_complete_wfi[] = " wfi_switches=";
static const char marker_complete_slice[] = " slice_switches=";
static const char marker_complete_stop[] = " stop_switches=";
static const char marker_complete_waits[] = " idle_waits=";
static const char marker_complete_idle[] = " idle_ticks=";
static const char marker_shutdown[] = "BE_B7:11 SHUTDOWN type=0 reason=0\n";
static const char marker_failure[] = "BE_B7:FAIL ";
static const char marker_detail[] = "BE_B7:DETAIL guest=";
static const char marker_detail_cause[] = " cause=";
static const char marker_detail_pc[] = " pc=";
static const char marker_detail_tval[] = " tval=";
static const char marker_detail_htval[] = " htval=";
static const char marker_detail_htinst[] = " htinst=";
static const char marker_detail_spvp[] = " spvp=";
static const char marker_detail_vsatp[] = " vsatp=";
static const char marker_detail_exits[] = " exits=";
/* A switch readback mismatch names the register and both values. */
static const char marker_switch_detail[] = "BE_B7:DETAIL switch guest=";
static const char marker_switch_register[] = " register=";
static const char marker_switch_wanted[] = " wanted=";
static const char marker_switch_readback[] = " readback=";
static const char marker_register_hgatp[] = "hgatp";
/* A controls failure after arming prints every readback, in two lines. */
static const char marker_controls_detail[] = "BE_B7:DETAIL controls hip=";
static const char marker_controls_detail_more[] =
	"BE_B7:DETAIL controls henvcfg=";
static const char marker_field_hstatus[] = " hstatus=";
static const char marker_field_hie[] = " hie=";
static const char marker_field_hvip[] = " hvip=";
static const char marker_field_htimedelta[] = " htimedelta=";
static const char marker_field_hgeie[] = " hgeie=";
static const char marker_field_sstatus[] = " sstatus=";
static const char marker_field_hgatp[] = " hgatp=";
static const char marker_field_sscratch[] = " sscratch=";
static const char marker_srst[] = "BE_B7:SRST_RETURNED\n";
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
		.trap_vector = symbol_address(be_b7_trap_vector),
	};
}

/*
 * Monitor lines go straight to the firmware console: guest lines are only
 * ever written whole, so a monitor line never splits one.
 */
static enum be_r3_error write_text(const char *text)
{
	be_u64 length = be_r3_text_length(text);

	if (length > BE_PAGE_SIZE)
		return BE_R3_ERROR_DBCN_RANGE;
	return be_r3_platform_write(text, length);
}

static enum be_r3_error write_line(void)
{
	be_b7_line_text(&be_b7_line, marker_newline);
	if (be_b7_line.overflow != 0U)
		return BE_R3_ERROR_DBCN_RANGE;
	return be_r3_platform_write(be_b7_line.text, be_b7_line.length);
}

static void line_start(const char *text)
{
	be_b7_line_reset(&be_b7_line);
	be_b7_line_text(&be_b7_line, text);
}

static void line_hex(const char *text, be_u64 value)
{
	be_b7_line_text(&be_b7_line, text);
	be_b7_line_hex(&be_b7_line, value);
}

static void line_decimal(const char *text, be_u64 value)
{
	be_b7_line_text(&be_b7_line, text);
	be_b7_line_decimal(&be_b7_line, value);
}

/* A guest's partial line, ended, before its shutdown or a FAIL line. */
static enum be_r3_error flush_console(be_u32 guest)
{
	be_u64 bytes = be_b7_console_flush(&be_b7_consoles[guest], guest,
					   be_b7_console_out,
					   sizeof(be_b7_console_out));

	if (bytes == BE_B7_CONSOLE_INVALID)
		return BE_R3_ERROR_DBCN_RANGE;
	if (bytes == 0U)
		return BE_R3_ERROR_NONE;
	return be_r3_platform_write(be_b7_console_out, bytes);
}

/* Every guest-control readback, so a board mismatch names its field. */
static void controls_detail(void)
{
	line_start(marker_controls_detail);
	be_b7_line_hex(&be_b7_line, be_b7_armed.hip);
	line_hex(marker_field_hstatus, be_b7_armed.hstatus);
	line_hex(marker_controls_hedeleg, be_b7_armed.hedeleg);
	line_hex(marker_controls_hideleg, be_b7_armed.hideleg);
	line_hex(marker_field_hie, be_b7_armed.hie);
	line_hex(marker_field_hvip, be_b7_armed.hvip);
	line_hex(marker_controls_hcounteren, be_b7_armed.hcounteren);
	line_hex(marker_field_htimedelta, be_b7_armed.htimedelta);
	(void)write_line();
	line_start(marker_controls_detail_more);
	be_b7_line_hex(&be_b7_line, be_b7_armed.henvcfg);
	line_hex(marker_field_hgeie, be_b7_armed.hgeie);
	line_hex(marker_controls_vstimecmp, be_b7_armed.vstimecmp);
	line_hex(marker_controls_sie, be_b7_armed.sie);
	line_hex(marker_field_sstatus, be_b7_armed.sstatus);
	line_hex(marker_field_hgatp, be_b7_armed.hgatp);
	line_hex(marker_detail_vsatp, be_b7_armed.vsatp);
	line_hex(marker_field_sscratch, be_b7_armed.sscratch);
	(void)write_line();
}

/*
 * The single terminal path: end both guests' partial lines, report,
 * request the accepted SRST shutdown once, and halt. A failure while
 * already terminal halts at once. A failure decided on a guest exit adds
 * its DETAIL line, naming the guest that ran.
 */
static void terminal(enum be_b7_class failure, const struct be_b7_exit *record,
		     int request_reset) __attribute__((noreturn));
static void terminal(enum be_b7_class failure, const struct be_b7_exit *record,
		     int request_reset)
{
	be_u32 guest = be_b7_sched.current;
	be_u32 index;

	if (be_b7_terminal_entered != 0U)
		be_r3_arch_halt();
	be_b7_terminal_entered = 1U;
	failure = be_b7_fail(&be_b7_control, failure);
	for (index = 0U; index < BE_B7_GUESTS; ++index)
		(void)flush_console(index);
	line_start(marker_failure);
	be_b7_line_text(&be_b7_line, be_b7_class_name(failure));
	(void)write_line();
	if (failure == BE_B7_CLASS_CONTROLS && be_b7_controls_read != 0U)
		controls_detail();
	if (failure == BE_B7_CLASS_SWITCH && be_b7_switch_fault.pending != 0U) {
		line_start(marker_switch_detail);
		be_b7_line_decimal(&be_b7_line, be_b7_switch_fault.guest);
		be_b7_line_text(&be_b7_line, marker_switch_register);
		be_b7_line_text(&be_b7_line, be_b7_switch_fault.name);
		line_hex(marker_switch_wanted, be_b7_switch_fault.wanted);
		line_hex(marker_switch_readback, be_b7_switch_fault.readback);
		(void)write_line();
	}
	if (record != (const struct be_b7_exit *)0 && guest < BE_B7_GUESTS) {
		line_start(marker_detail);
		be_b7_line_decimal(&be_b7_line, guest);
		line_hex(marker_detail_cause, record->frame.scause);
		line_hex(marker_detail_pc, record->frame.sepc);
		line_hex(marker_detail_tval, record->frame.stval);
		line_hex(marker_detail_htval, record->frame.htval);
		line_hex(marker_detail_htinst, record->htinst);
		line_decimal(marker_detail_spvp,
			     be_b7_record_spp(record) != 0U ? 1U : 0U);
		line_hex(marker_detail_vsatp, record->vsatp);
		line_decimal(marker_detail_exits,
			     be_b7_control.guest[guest].counts.exits);
		(void)write_line();
	}
	if (request_reset != 0)
		(void)be_r3_platform_reset();
	(void)write_text(marker_srst);
	be_r3_arch_halt();
}

void be_b7_runtime_terminal(enum be_b7_class failure)
{
	terminal(failure, (const struct be_b7_exit *)0, 1);
}

void be_b7_exit_terminal(struct be_b7_exit *record)
{
	terminal(BE_B7_CLASS_EXCEPTION, record, 1);
}

static void switch_fail(be_u32 guest, const char *name, be_u64 wanted,
			be_u64 readback) __attribute__((noreturn));
static void switch_fail(be_u32 guest, const char *name, be_u64 wanted,
			be_u64 readback)
{
	be_b7_switch_fault.pending = 1U;
	be_b7_switch_fault.guest = guest;
	be_b7_switch_fault.name = name;
	be_b7_switch_fault.wanted = wanted;
	be_b7_switch_fault.readback = readback;
	be_b7_runtime_terminal(BE_B7_CLASS_SWITCH);
}

static void emit_text(const char *text)
{
	if (write_text(text) != BE_R3_ERROR_NONE)
		be_b7_runtime_terminal(BE_B7_CLASS_CONSOLE);
}

static void emit_line(void)
{
	if (write_line() != BE_R3_ERROR_NONE)
		be_b7_runtime_terminal(BE_B7_CLASS_CONSOLE);
}

static void boot_fail(void) __attribute__((noreturn));
static void boot_fail(void)
{
	be_b7_runtime_terminal(BE_B7_CLASS_BOOT);
}

static void run_r1(void)
{
	if (be_runtime_copy_inventory(&be_b7_runtime,
				      be_r1_inventory()) != BE_RUNTIME_OK ||
	    be_runtime_copy_proposal(&be_b7_runtime,
				     be_r1_proposal()) != BE_RUNTIME_OK ||
	    be_runtime_validate(&be_b7_runtime) != BE_RUNTIME_OK ||
	    be_runtime_seal(&be_b7_runtime) != BE_RUNTIME_OK ||
	    be_runtime_derive(&be_b7_runtime) != BE_RUNTIME_OK ||
	    be_r3_note_r1_derived(&be_b7_r3_control,
				  &be_b7_runtime) != BE_R3_ERROR_NONE)
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

	if (be_r2_build(&be_b7_runtime, pools, &be_b7_r2_output) !=
		    BE_CHECK_OK ||
	    be_r2_walk_and_check(&be_b7_runtime, pools, &be_b7_r2_output,
				 be_b7_leaf_sets) != BE_CHECK_OK ||
	    be_r3_note_r2_built(&be_b7_r3_control, &be_b7_runtime,
				&be_b7_r2_output,
				be_b7_leaf_sets) != BE_R3_ERROR_NONE)
		boot_fail();
}

/*
 * The second install site: write the guest's walked hgatp through the
 * accepted R3 install function, which fences and reads back, and require
 * the readback. At boot a mismatch is the gstage class; at a switch it is
 * the switch class, with a DETAIL line.
 */
static be_u64 install_root(be_u32 guest, enum be_b7_class failure)
	BE_B7_ONE_COPY;
static be_u64 install_root(be_u32 guest, enum be_b7_class failure)
{
	be_u64 hgatp = be_b7_maps[guest].hgatp;
	be_u64 readback = be_r3_arch_install_management(hgatp);

	if (readback != hgatp) {
		if (failure == BE_B7_CLASS_SWITCH)
			switch_fail(guest, marker_register_hgatp, hgatp,
				    readback);
		be_b7_runtime_terminal(failure);
	}
	return readback;
}

/*
 * Both B7 roots: build each in its own half of the NOLOAD pool, re-walk
 * every byte, require the two walked roots to be disjoint, and install
 * G1's root and then G0's, each read back.
 */
static void build_gstage(void)
{
	be_u64 readback[BE_B7_GUESTS];
	be_u32 guest;

	if (symbol_address(__be_b7_pool_start) != BE_B7_POOL_HPA ||
	    symbol_address(__be_b7_pool_end) !=
		    BE_B7_POOL_HPA + BE_B7_POOL_BYTES)
		be_b7_runtime_terminal(BE_B7_CLASS_GSTAGE);
	for (guest = 0U; guest < BE_B7_GUESTS; ++guest) {
		be_u8 *pool = __be_b7_pool_start +
			      guest * BE_B7_GUEST_POOL_BYTES;

		if (symbol_address(pool) != be_b7_descs[guest].pool_pa ||
		    be_b7_gstage_build(&be_b7_descs[guest], pool,
				       BE_B7_GUEST_POOL_BYTES) !=
			    BE_B7_GSTAGE_OK ||
		    be_b7_gstage_walk(&be_b7_descs[guest], pool,
				      BE_B7_GUEST_POOL_BYTES,
				      &be_b7_maps[guest]) != BE_B7_GSTAGE_OK ||
		    be_b7_maps[guest].hgatp != be_b7_hgatps[guest] ||
		    be_b7_maps[guest].leaves != BE_B7_GUEST_LEAVES)
			be_b7_runtime_terminal(BE_B7_CLASS_GSTAGE);
		line_start(marker_gstage);
		be_b7_line_decimal(&be_b7_line, guest);
		line_hex(marker_gpa, be_b7_maps[guest].gpa_base);
		line_hex(marker_hpa, be_b7_maps[guest].hpa_base);
		line_hex(marker_size, be_b7_maps[guest].size);
		line_decimal(marker_leaves, be_b7_maps[guest].leaves);
		line_hex(marker_root, be_b7_maps[guest].pool_pa);
		emit_line();
	}
	if (be_b7_gstage_pair_check(&be_b7_maps[0], &be_b7_maps[1]) !=
	    BE_B7_GSTAGE_OK)
		be_b7_runtime_terminal(BE_B7_CLASS_GSTAGE);

	readback[1] = install_root(1U, BE_B7_CLASS_GSTAGE);
	readback[0] = install_root(0U, BE_B7_CLASS_GSTAGE);
	line_start(marker_installed);
	be_b7_line_hex(&be_b7_line, readback[1]);
	line_hex(marker_installed_g0, readback[0]);
	emit_line();
}

/*
 * Load one guest's CSR set through the load helper, which reads every CSR
 * back, and require each readback to equal the value written.
 */
static void load_csrs(be_u32 guest)
{
	const be_u64 *wanted = be_b7_vcpus[guest].csr;
	be_u32 index;

	be_b7_arch_load_vcsr(wanted, be_b7_readback);
	index = be_b7_vcsr_mismatch(wanted, be_b7_readback);
	if (index != BE_B7_VCSR_COUNT)
		switch_fail(guest, be_b7_vcsr_name(index), wanted[index],
			    be_b7_readback[index]);
}

/*
 * Henvcfg first: a CPU without Sstc fails closed before vstimecmp exists.
 * Then the shared controls, and both guests' initial CSR set, loaded once
 * here for G0's first entry and read back.
 */
static void arm_guest_controls(void)
{
	be_u64 henvcfg = be_b7_arch_arm_stce();
	enum be_b7_class failure = be_b7_stce_class(henvcfg);
	be_u32 guest;

	if (failure != BE_B7_CLASS_NONE)
		be_b7_runtime_terminal(failure);
	line_start(marker_stce);
	be_b7_line_hex(&be_b7_line, henvcfg);
	emit_line();

	be_b7_arch_arm_controls(&be_b7_armed,
				symbol_address(__be_stack_management_end));
	be_b7_controls_read = 1U;
	if (!be_b7_controls_valid(&be_b7_armed, be_b7_maps[0].hgatp,
				  symbol_address(__be_stack_management_end)))
		be_b7_runtime_terminal(BE_B7_CLASS_CONTROLS);
	line_start(marker_controls);
	be_b7_line_hex(&be_b7_line,
		       be_b7_armed.hstatus & BE_R3_HSTATUS_CONTROL_MASK);
	line_hex(marker_controls_hedeleg, be_b7_armed.hedeleg);
	line_hex(marker_controls_hideleg, be_b7_armed.hideleg);
	line_hex(marker_controls_hcounteren, be_b7_armed.hcounteren);
	line_hex(marker_controls_sie, be_b7_armed.sie);
	line_hex(marker_controls_fs,
		 (be_b7_armed.sstatus & BE_R3_SSTATUS_FS_MASK) >> 13);
	line_hex(marker_controls_vs,
		 (be_b7_armed.sstatus & BE_B7_SSTATUS_VS_MASK) >> 9);
	line_hex(marker_controls_vstimecmp, be_b7_armed.vstimecmp);
	emit_line();

	for (guest = 0U; guest < BE_B7_GUESTS; ++guest)
		be_b7_vcsr_initial(be_b7_vcpus[guest].csr);
	load_csrs(0U);
}

/* Shape checks on the staged payload, before either window is touched. */
static void check_payload(void)
{
	const be_u8 *staged =
		(const be_u8 *)(void *)be_b7_payload_layout.staging_hpa;

	if (be_b7_payload_check(&be_b7_payload_layout, be_b7_maps, staged,
				be_b7_plans) != BE_B7_PAYLOAD_OK)
		be_b7_runtime_terminal(BE_B7_CLASS_PAYLOAD);
}

/* Zero one guest window through its HS backing, and read it back. */
static void clear_guest_ram(be_u32 guest)
{
	const struct be_b7_gstage_map *map = &be_b7_maps[guest];
	volatile be_u64 *window = (volatile be_u64 *)(void *)map->hpa_base;
	be_u64 words = map->size / sizeof(be_u64);
	be_u64 residue = 0U;
	be_u64 start = be_b7_arch_read_time();
	be_u64 index;

	for (index = 0U; index < words; ++index)
		window[index] = 0U;
	for (index = 0U; index < words; ++index)
		residue |= window[index];
	if (residue != 0U)
		boot_fail();
	line_start(marker_cleared);
	be_b7_line_decimal(&be_b7_line, guest);
	line_hex(marker_gpa, map->gpa_base);
	line_hex(marker_size, map->size);
	line_hex(marker_ticks, be_b7_arch_read_time() - start);
	emit_line();
}

/* Copy one staged object into a window, and compare the copy. */
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

/* The kernel into a guest's window, and that guest's own DTB. */
static void place_payload(be_u32 guest)
{
	const struct be_b7_payload_plan *plan = &be_b7_plans[guest];
	be_u64 start = be_b7_arch_read_time();

	if ((place(plan->kernel_target, plan->kernel_source,
		   plan->kernel_bytes) |
	     place(plan->dtb_target, plan->dtb_source, plan->dtb_bytes)) != 0U)
		boot_fail();
	line_start(marker_placed);
	be_b7_line_decimal(&be_b7_line, guest);
	line_hex(marker_placed_kernel, plan->kernel_gpa);
	line_hex(marker_placed_kernel_bytes, plan->kernel_bytes);
	line_hex(marker_placed_image_size, plan->image_size);
	line_hex(marker_placed_dtb, plan->dtb_gpa);
	line_hex(marker_placed_dtb_bytes, plan->dtb_bytes);
	line_hex(marker_ticks, be_b7_arch_read_time() - start);
	emit_line();
}

/* BE_B7:08, once per guest, at its first entry. */
static void entered(be_u32 guest, const struct be_b7_exit *record)
{
	be_b7_entered[guest] = 1U;
	line_start(marker_enter);
	be_b7_line_decimal(&be_b7_line, guest);
	line_hex(marker_enter_pc, record->frame.sepc);
	line_hex(marker_enter_a0, record->frame.gpr[BE_R4_GPR_A0]);
	line_hex(marker_enter_a1, record->frame.gpr[BE_R4_GPR_A1]);
	emit_line();
}

/* Feed a guest's bytes to its console; whole lines go to the firmware. */
static void guest_console(be_u32 guest, be_u64 length)
{
	be_u64 bytes = be_b7_console_feed(&be_b7_consoles[guest], guest,
					  be_b7_guest_bytes, length,
					  be_b7_console_out,
					  sizeof(be_b7_console_out));

	if (bytes == BE_B7_CONSOLE_INVALID ||
	    (bytes != 0U && be_r3_platform_write(be_b7_console_out, bytes) !=
				    BE_R3_ERROR_NONE))
		be_b7_runtime_terminal(BE_B7_CLASS_CONSOLE);
}

/* Copy DBCN bytes from the calling guest's window; firmware never sees it. */
static void guest_write(be_u32 guest, const struct be_b7_result *result)
{
	const volatile be_u8 *source =
		(const volatile be_u8 *)(void *)result->source_pa;
	be_u64 index;

	if (result->length > BE_B7_DBCN_MAX_BYTES)
		be_b7_runtime_terminal(BE_B7_CLASS_CONSOLE);
	for (index = 0U; index < result->length; ++index)
		be_b7_guest_bytes[index] = source[index];
	guest_console(guest, result->length);
}

static void guest_write_byte(be_u32 guest, const struct be_b7_result *result)
{
	be_b7_guest_bytes[0] = result->byte;
	guest_console(guest, 1U);
}

/* A guest's shutdown: its last partial line, then BE_B7:09. */
static void guest_stopped(be_u32 guest, const struct be_b7_exit *record)
{
	const struct be_b7_counts *counts = &be_b7_control.guest[guest].counts;

	if (flush_console(guest) != BE_R3_ERROR_NONE)
		be_b7_runtime_terminal(BE_B7_CLASS_CONSOLE);
	line_start(marker_guest_shutdown);
	be_b7_line_decimal(&be_b7_line, guest);
	line_decimal(marker_count_exits, counts->exits);
	line_decimal(marker_count_sbi, be_b7_counts_sbi(counts));
	line_decimal(marker_count_wfi, counts->wfi);
	line_decimal(marker_count_slice, counts->slice);
	line_decimal(marker_count_base, counts->base);
	line_decimal(marker_count_time, counts->time);
	line_decimal(marker_count_dbcn_write, counts->dbcn_write);
	line_decimal(marker_count_dbcn_read, counts->dbcn_read);
	line_decimal(marker_count_dbcn_byte, counts->dbcn_byte);
	line_decimal(marker_count_srst, counts->srst);
	line_decimal(marker_count_refused, counts->refused);
	line_hex(marker_ticks, record->time - be_b7_control.entry_time);
	emit_line();
}

/* Both guests stopped: the summary, then the monitor's own shutdown. */
static void run_complete(void) __attribute__((noreturn));
static void run_complete(void)
{
	line_start(marker_complete);
	be_b7_line_decimal(&be_b7_line, be_b7_sched.switches);
	line_decimal(marker_complete_wfi, be_b7_sched.wfi_switches);
	line_decimal(marker_complete_slice, be_b7_sched.slice_switches);
	line_decimal(marker_complete_stop, be_b7_sched.stop_switches);
	line_decimal(marker_complete_waits, be_b7_sched.idle_waits);
	line_hex(marker_complete_idle, be_b7_sched.idle_ticks);
	line_hex(marker_ticks,
		 be_b7_arch_read_time() - be_b7_control.entry_time);
	emit_line();
	emit_text(marker_shutdown);
	(void)be_r3_platform_reset();
	/* A conforming shutdown does not return. */
	terminal(BE_B7_CLASS_SHUTDOWN_RETURNED, (const struct be_b7_exit *)0,
		 0);
}

/*
 * A switch from guest @from to guest @to: the exit record and CSRs out,
 * the incoming root through the accepted install function with its
 * readback, the incoming CSRs with every readback, and the incoming record
 * into the exit record (R5's discipline: root, fence, readback, then the
 * checked state).
 */
static void switch_guest(be_u32 from, be_u32 to, struct be_b7_exit *record)
{
	be_b7_vcpu_save(&be_b7_vcpus[from], record);
	be_b7_arch_save_vcsr(be_b7_vcpus[from].csr);
	(void)install_root(to, BE_B7_CLASS_SWITCH);
	load_csrs(to);
	be_b7_vcpu_restore(&be_b7_vcpus[to], record);
	if (be_b7_entered[to] == 0U)
		entered(to, record);
}

/*
 * Decide and act until a guest runs: switch if needed, program its HS
 * deadline, and resume it; or wait in HS while both guests idle; or finish
 * when both have stopped. A wait never runs past the run's budget.
 */
static void schedule(struct be_b7_exit *record) __attribute__((noreturn));
static void schedule(struct be_b7_exit *record)
{
	struct be_b7_decision decision;
	be_u32 from = be_b7_sched.current;

	for (;;) {
		be_u64 now = be_b7_arch_read_time();

		switch (be_b7_sched_next(&be_b7_sched, now, &decision)) {
		case BE_B7_NEXT_RUN:
			if (decision.switched != 0U)
				switch_guest(from, decision.guest, record);
			be_b7_arch_set_deadline(decision.deadline);
			be_b7_arch_resume(record,
					  be_b7_maps[decision.guest].hgatp,
					  be_b7_armed.hedeleg);
		case BE_B7_NEXT_WAIT:
			be_b7_arch_set_deadline(decision.deadline);
			be_b7_sched_waited(&be_b7_sched,
					   be_b7_arch_wait(decision.deadline) -
						   now);
			break;
		case BE_B7_NEXT_DONE:
			run_complete();
		case BE_B7_NEXT_TIMEOUT:
			terminal(BE_B7_CLASS_GUEST_TIMEOUT, record, 1);
		case BE_B7_NEXT_INVALID:
		default:
			terminal(BE_B7_CLASS_SCHEDULER, record, 1);
		}
	}
}

void be_b7_dispatch(struct be_b7_exit *record)
{
	struct be_b7_result result;
	be_u32 guest = be_b7_sched.current;
	enum be_b7_event event = BE_B7_EVENT_NONE;
	be_u64 wake = 0U;

	if (record != (struct be_b7_exit *)(void *)__be_saved_management_start ||
	    guest >= BE_B7_GUESTS)
		be_b7_runtime_terminal(BE_B7_CLASS_EXCEPTION);
	switch (be_b7_handle_exit(&be_b7_control, guest, &be_b7_maps[guest],
				  record, &result)) {
	case BE_B7_ACTION_RETURN:
		break;
	case BE_B7_ACTION_CONSOLE_WRITE:
		guest_write(guest, &result);
		break;
	case BE_B7_ACTION_CONSOLE_BYTE:
		guest_write_byte(guest, &result);
		break;
	case BE_B7_ACTION_SET_TIMER:
		be_b7_arch_set_timer(result.timer);
		break;
	case BE_B7_ACTION_WFI:
		/* The guest idles until its own timer: its vstimecmp. */
		be_b7_arch_save_vcsr(be_b7_vcpus[guest].csr);
		wake = be_b7_vcpus[guest].csr[BE_B7_VCSR_VSTIMECMP];
		event = BE_B7_EVENT_WFI;
		break;
	case BE_B7_ACTION_SLICE:
		event = BE_B7_EVENT_SLICE;
		break;
	case BE_B7_ACTION_STOP:
		guest_stopped(guest, record);
		event = BE_B7_EVENT_STOP;
		break;
	case BE_B7_ACTION_GUEST_FAILURE:
	case BE_B7_ACTION_GUEST_REBOOT:
	case BE_B7_ACTION_NONE:
	case BE_B7_ACTION_TERMINAL:
	default:
		terminal(result.failure, record, 1);
	}
	be_b7_apply_return(&record->frame, &result);
	/* An SBI call resumes the same guest under its current deadline. */
	if (event == BE_B7_EVENT_NONE) {
		be_b7_arch_set_deadline(be_b7_sched.deadline);
		be_b7_arch_resume(record, be_b7_maps[guest].hgatp,
				  be_b7_armed.hedeleg);
	}
	if (be_b7_sched_event(&be_b7_sched, event, wake) == 0)
		terminal(BE_B7_CLASS_SCHEDULER, record, 1);
	schedule(record);
}

/*
 * Both guests' first-entry state, the scheduler, and G0's first entry
 * through the same checked tail: Linux's boot protocol in its window.
 */
static void start_run(void) __attribute__((noreturn));
static void start_run(void)
{
	struct be_b7_exit *record =
		(struct be_b7_exit *)(void *)__be_saved_management_start;
	struct be_b7_decision decision;
	be_u64 now;
	be_u32 guest;

	for (guest = 0U; guest < BE_B7_GUESTS; ++guest)
		be_b7_vcpu_init(&be_b7_vcpus[guest],
				be_b7_plans[guest].kernel_gpa,
				BE_B7_GUEST_HART, be_b7_plans[guest].dtb_gpa);
	be_b7_sched_init(&be_b7_sched, BE_B7_SLICE_TICKS,
			 be_b7_control.time_budget);
	line_start(marker_armed);
	be_b7_line_decimal(&be_b7_line, BE_B7_GUESTS);
	line_hex(marker_armed_slice, be_b7_sched.slice);
	line_decimal(marker_armed_first, be_b7_sched.current);
	emit_line();

	be_b7_vcpu_restore(&be_b7_vcpus[0], record);
	entered(0U, record);
	now = be_b7_arch_read_time();
	be_b7_control.entry_time = now;
	if (be_b7_sched_start(&be_b7_sched, now, &decision) !=
		    BE_B7_NEXT_RUN ||
	    decision.guest != 0U)
		be_b7_runtime_terminal(BE_B7_CLASS_SCHEDULER);
	be_b7_arch_set_deadline(decision.deadline);
	be_b7_arch_resume(record, be_b7_maps[0].hgatp, be_b7_armed.hedeleg);
}

void be_b7_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
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
	be_u32 guest;

	build_image_layout(&be_b7_layout);
	boot.entry = symbol_address(be_reset);
	boot.hart_id = hart_id;
	boot.firmware_pointer = firmware_pointer;
	boot.layout = be_b7_layout;
	if (be_r3_platform_get_spec_version(&boot.sbi_spec_version) !=
		    BE_R0_SBI_SUCCESS ||
	    be_r3_platform_probe_extension(BE_R0_SBI_EID_DBCN,
					 &boot.dbcn_probe) != BE_R0_SBI_SUCCESS ||
	    be_r3_platform_probe_extension(BE_R0_SBI_EID_SRST,
					 &boot.srst_probe) != BE_R0_SBI_SUCCESS ||
	    be_r3_validate_boot(&be_b7_r3_control, &boot) != BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_boot);
	run_r1();
	emit_text(marker_r1);
	run_r2();
	emit_text(marker_r2);

	be_r3_arch_reset_state(be_b7_layout.trap_vector, &be_b7_hs);
	if (be_r3_note_hs_ready(&be_b7_r3_control, &be_b7_hs,
				&be_b7_layout) != BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_hs);
	if (be_r3_prepare_management_binding(&be_b7_r3_control, &binding) !=
	    BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_binding);
	hgatp_readback = be_r3_arch_install_management(binding.hgatp);
	if (be_r3_publish_management_binding(&be_b7_r3_control, hgatp_readback,
					     1U) != BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_fence);

	build_gstage();
	arm_guest_controls();
	check_payload();
	for (guest = 0U; guest < BE_B7_GUESTS; ++guest)
		clear_guest_ram(guest);
	for (guest = 0U; guest < BE_B7_GUESTS; ++guest)
		place_payload(guest);
	be_b7_arch_fence_i();
	start_run();
}
