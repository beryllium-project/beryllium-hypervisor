// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the K3 B7 guest SBI core: every row of the
 *          plan's SBI table (version 3), the DBCN range check at each
 *          window's edges and leaf boundaries, the SRST type and reason grid
 *          with a shutdown that stops only the calling guest and terminal
 *          reboots, TIME values, exit classes, the idling wfi and HS slice
 *          classes (stval match and mismatch, SPVP 0 and 1, other
 *          interrupts), each guest's exit ceiling and the run's guest-time
 *          budget, per-guest counters, the frame return and the first-entry
 *          frame, the guest controls, the per-guest line console (its CR
 *          drop, byte filter, full-buffer split, flush, and interleaved
 *          guests that never form a mixed line), the switch's vCPU record
 *          and CSR-set logic, the monitor line builder, and replays of the
 *          research reference boot's SBI call census for each guest.
 * Trust:   host evidence only. No CSR, guest entry, QEMU, or hardware
 *          behaviour is exercised. The windows come from the B7 G-stage
 *          builder and walker, run in host memory.
 * Scope:   B7 only (planning/k3-b7-plan.md).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "b7.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_B7_CHECK: assertion failed: %s:%d: %s\n", \
			       __FILE__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define MIB			(BE_U64_C(1) << 20)
#define ECALL_PC		BE_U64_C(0x80201040)
#define ENTRY_TIME		BE_U64_C(0x123456789)
#define EXIT_TIME		(ENTRY_TIME + BE_U64_C(0x1000))
#define FRAME_PATTERN		BE_U64_C(0x5a5a000000000000)
#define WINDOW_GPA		BE_U64_C(0x80000000)
#define WINDOW_HPA		BE_U64_C(0x110000000)
#define WINDOW_G1_HPA		BE_U64_C(0x114000000)
#define WINDOW_BYTES		(64U * MIB)
#define WFI			BE_U64_C(0x10500073)
#define STI			(BE_U64_C(1) << 63 | 5U)
#define EID_HSM			BE_U64_C(0x48534d)
#define EID_IPI			BE_U64_C(0x735049)
#define EID_RFENCE		BE_U64_C(0x52464e43)
#define EID_PMU			BE_U64_C(0x504d55)
#define EID_SUSP		BE_U64_C(0x53555350)
#define EID_CPPC		BE_U64_C(0x43505043)
#define EID_NACL		BE_U64_C(0x4e41434c)
#define EID_STA			BE_U64_C(0x535441)
#define EID_SSE			BE_U64_C(0x535345)
#define EID_FWFT		BE_U64_C(0x46574654)
#define EID_DBTR		BE_U64_C(0x44425452)
#define EID_MPXY		BE_U64_C(0x4d505859)
#define EID_UNASSIGNED		BE_U64_C(0x42453535)
#define HIGH_BIT		(BE_U64_C(1) << 32)
#define ALL_ONES		(~BE_U64_C(0))

static be_u8 pool[BE_B7_GSTAGE_POOL_BYTES];
static struct be_b7_gstage_map windows[2];
/* G0's window; most single-guest cases run as G0. */
#define window windows[0]

static void build_window(void)
{
	struct be_b7_gstage_desc desc[2] = {
		{ BE_B7_GUEST_GPA, BE_B7_G0_HPA, BE_B7_GUEST_BYTES,
		  BE_B7_G0_ROOT_HPA, BE_B7_G0_VMID },
		{ BE_B7_GUEST_GPA, BE_B7_G1_HPA, BE_B7_GUEST_BYTES,
		  BE_B7_G1_ROOT_HPA, BE_B7_G1_VMID },
	};
	unsigned int guest;

	for (guest = 0U; guest < 2U; ++guest) {
		CHECK(be_b7_gstage_build(&desc[guest], pool, sizeof(pool)) ==
		      BE_B7_GSTAGE_OK);
		CHECK(be_b7_gstage_walk(&desc[guest], pool, sizeof(pool),
					&windows[guest]) == BE_B7_GSTAGE_OK);
	}
}

static struct be_b7_state fresh_state(void)
{
	struct be_b7_state state = BE_B7_STATE_INITIALIZER(
		BE_B7_EXIT_CEILING, BE_B7_GUEST_TIME_BUDGET);

	state.entry_time = ENTRY_TIME;
	return state;
}

static struct be_b7_exit exit_with(be_u64 scause, be_u64 sepc)
{
	struct be_b7_exit record;
	be_size index;

	memset(&record, 0, sizeof(record));
	for (index = 0U; index < BE_ARRAY_SIZE(record.frame.gpr); ++index)
		record.frame.gpr[index] = FRAME_PATTERN | index;
	record.frame.vstvec = FRAME_PATTERN | 0x100U;
	record.frame.vsepc = FRAME_PATTERN | 0x101U;
	record.frame.vscause = FRAME_PATTERN | 0x102U;
	record.frame.vstval = FRAME_PATTERN | 0x103U;
	record.frame.scause = scause;
	record.frame.sepc = sepc;
	record.frame.stval = FRAME_PATTERN | 0x104U;
	record.frame.htval = FRAME_PATTERN | 0x105U;
	record.frame.reserved = 0U;
	record.hstatus = BE_U64_C(0x200000180);
	record.htinst = FRAME_PATTERN | 0x106U;
	record.vsatp = BE_U64_C(0x8000000000080e00);
	record.time = EXIT_TIME;
	return record;
}

static struct be_b7_exit ecall(be_u64 eid, be_u64 fid, be_u64 argument0,
			       be_u64 argument1, be_u64 argument2)
{
	struct be_b7_exit record = exit_with(BE_B7_SCAUSE_VS_ECALL, ECALL_PC);

	record.frame.gpr[BE_R4_GPR_A7] = eid;
	record.frame.gpr[BE_R4_GPR_A6] = fid;
	record.frame.gpr[BE_R4_GPR_A0] = argument0;
	record.frame.gpr[BE_R4_GPR_A1] = argument1;
	record.frame.gpr[BE_B7_GPR_A2] = argument2;
	return record;
}

static be_u64 call_sum(const struct be_b7_counts *counts)
{
	return counts->base + counts->time + counts->dbcn_write +
	       counts->dbcn_read + counts->dbcn_byte + counts->srst +
	       counts->refused;
}

/* One exit on a fresh running state; checks the generic ecall properties. */
static struct be_b7_result decide(const struct be_b7_exit *record)
{
	struct be_b7_state state = fresh_state();
	struct be_b7_result result;

	CHECK(be_b7_handle_exit(&state, 0U, &window, record, &result) ==
	      result.action);
	CHECK(state.guest[0].counts.exits == 1U);
	if (result.action != BE_B7_ACTION_TERMINAL) {
		CHECK(result.resume_pc == record->frame.sepc + 4U);
		CHECK(call_sum(&state.guest[0].counts) == 1U);
	}
	if (result.action == BE_B7_ACTION_RETURN ||
	    result.action == BE_B7_ACTION_CONSOLE_WRITE ||
	    result.action == BE_B7_ACTION_CONSOLE_BYTE ||
	    result.action == BE_B7_ACTION_SET_TIMER)
		CHECK(state.phase == BE_B7_PHASE_RUNNING &&
		      state.guest[0].phase == BE_B7_PHASE_RUNNING);
	/* The other guest's counts never move. */
	CHECK(state.guest[1].counts.exits == 0U &&
	      call_sum(&state.guest[1].counts) == 0U);
	if (result.error == BE_B7_SBI_ERR_NOT_SUPPORTED ||
	    result.error == BE_B7_SBI_ERR_INVALID_PARAM)
		CHECK(state.guest[0].counts.refused == 1U);
	return result;
}

static void check_return(be_u64 eid, be_u64 fid, be_u64 argument0,
			 be_u64 argument1, be_u64 argument2, long error,
			 be_u64 value)
{
	struct be_b7_exit record = ecall(eid, fid, argument0, argument1,
				       argument2);
	struct be_b7_result result = decide(&record);

	CHECK(result.action == BE_B7_ACTION_RETURN);
	CHECK(result.error == error);
	CHECK(result.value == value);
	CHECK(result.failure == BE_B7_CLASS_NONE);
}

static void check_unsupported(be_u64 eid, be_u64 fid)
{
	check_return(eid, fid, 0U, 0U, 0U, BE_B7_SBI_ERR_NOT_SUPPORTED, 0U);
	check_return(eid, fid, ALL_ONES, ALL_ONES, ALL_ONES,
		     BE_B7_SBI_ERR_NOT_SUPPORTED, 0U);
}

static void check_dbcn_write(be_u64 length, be_u64 gpa, be_u64 high,
			     be_u64 expected_pa, be_u64 expected_length)
{
	struct be_b7_exit record = ecall(BE_B7_SBI_EID_DBCN,
				       BE_B7_SBI_DBCN_WRITE, length, gpa,
				       high);
	struct be_b7_result result = decide(&record);

	CHECK(result.action == BE_B7_ACTION_CONSOLE_WRITE);
	CHECK(result.error == BE_B7_SBI_SUCCESS);
	CHECK(result.source_pa == expected_pa);
	CHECK(result.length == expected_length);
	CHECK(result.value == expected_length);
}

static void check_dbcn_refused(be_u64 length, be_u64 gpa, be_u64 high)
{
	check_return(BE_B7_SBI_EID_DBCN, BE_B7_SBI_DBCN_WRITE, length, gpa,
		     high, BE_B7_SBI_ERR_INVALID_PARAM, 0U);
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(BE_B7_SBI_EID_BASE == 0x10U);
	CHECK(BE_B7_SBI_EID_TIME == 0x54494d45U);
	CHECK(BE_B7_SBI_EID_DBCN == 0x4442434eU);
	CHECK(BE_B7_SBI_EID_SRST == 0x53525354U);
	CHECK(BE_B7_SBI_SPEC_VERSION == 0x2000000U);
	CHECK(BE_B7_SBI_IMPL_ID == ((be_u64)'B' << 8 | (be_u64)'E'));
	CHECK(BE_B7_SBI_IMPL_VERSION == 3U);
	CHECK(BE_B7_EXIT_CEILING == BE_U64_C(1) << 20);
	CHECK(BE_B7_GUEST_TIME_BUDGET == BE_U64_C(1) << 32);
	CHECK(BE_B7_VARIANT_EXIT_CEILING == 64U);
	CHECK(BE_B7_VARIANT_GUEST_TIME_BUDGET == BE_U64_C(1) << 20);
	CHECK(BE_B7_RUN_EXIT_CEILING == BE_B7_EXIT_CEILING);
	CHECK(BE_B7_RUN_GUEST_TIME_BUDGET == BE_B7_GUEST_TIME_BUDGET);
	CHECK(BE_B7_DBCN_MAX_BYTES == 256U);
	CHECK(BE_B7_CONSOLE_LINE_BYTES == 256U);
	CHECK(strcmp(BE_B7_G0_PREFIX, "BE_B7_G0: ") == 0);
	CHECK(strcmp(BE_B7_G1_PREFIX, "BE_B7_G1: ") == 0);
	CHECK(strlen(BE_B7_G0_PREFIX) == BE_B7_GUEST_PREFIX_LENGTH);
	CHECK(strlen(BE_B7_G1_PREFIX) == BE_B7_GUEST_PREFIX_LENGTH);
	CHECK(BE_B7_CONSOLE_CAPACITY == 3339U);
	CHECK(BE_B7_CONSOLE_CAPACITY <= BE_PAGE_SIZE);
	CHECK(BE_B7_WFI_INSTRUCTION == WFI);
	CHECK(BE_B7_SCAUSE_SUPERVISOR_TIMER == STI);
	CHECK(BE_B7_VCSR_COUNT == 11U);
	CHECK(sizeof(struct be_b7_vcpu) == 352U + 11U * sizeof(be_u64));
	CHECK(BE_B7_GPR_A2 == 11U);
	CHECK(BE_R4_GPR_A0 == 9U && BE_R4_GPR_A1 == 10U);
	CHECK(BE_R4_GPR_A6 == 15U && BE_R4_GPR_A7 == 16U);
	CHECK(sizeof(struct be_r4_frame) == 320U);
	CHECK(sizeof(struct be_b7_exit) == 352U);
	CHECK(__builtin_offsetof(struct be_b7_exit, hstatus) == 320U);
	CHECK(__builtin_offsetof(struct be_b7_exit, htinst) == 328U);
	CHECK(__builtin_offsetof(struct be_b7_exit, vsatp) == 336U);
	CHECK(__builtin_offsetof(struct be_b7_exit, time) == 344U);
	CHECK(sizeof(struct be_b7_counts) == 10U * sizeof(be_u64));
	/* The image checker reads both run limits at the state's start. */
	CHECK(__builtin_offsetof(struct be_b7_state, exit_ceiling) == 0U);
	CHECK(__builtin_offsetof(struct be_b7_state, time_budget) == 8U);
}

static void test_class_names(void)
{
	static const char *const names[] = {
		"none", "boot", "gstage", "sstc", "controls", "payload",
		"interrupt", "guest-page-fault", "virtual-instruction",
		"access-fault", "illegal-instruction", "exception",
		"exit-budget", "guest-timeout", "resume", "console",
		"guest-failure", "guest-reboot", "shutdown-returned",
		"switch", "scheduler",
	};
	unsigned int index;

	SCENARIO();
	CHECK(BE_ARRAY_SIZE(names) == (be_size)BE_B7_CLASS_COUNT);
	for (index = 0U; index < BE_ARRAY_SIZE(names); ++index)
		CHECK(strcmp(be_b7_class_name((enum be_b7_class)index),
			     names[index]) == 0);
	CHECK(strcmp(be_b7_class_name(BE_B7_CLASS_COUNT), "invalid") == 0);
	CHECK(strcmp(be_b7_class_name((enum be_b7_class)99), "invalid") == 0);
}

static struct be_b7_controls armed_controls(void)
{
	return (struct be_b7_controls) {
		.hip = 0U,
		.hstatus = BE_U64_C(0x200200180),
		.hedeleg = 0xb15dU,
		.hideleg = 0x40U,
		.hie = 0U,
		.hvip = 0U,
		.hcounteren = 0x2U,
		.htimedelta = 0U,
		.henvcfg = BE_U64_C(0x8000000000000000),
		.hgeie = 0U,
		.vstimecmp = ALL_ONES,
		.sie = 0x20U,
		.sstatus = BE_U64_C(0x200000000),
		.hgatp = BE_U64_C(0x8000100000102034),
		.vsatp = 0U,
		.sscratch = BE_U64_C(0x102027000),
	};
}

static int armed_valid(const struct be_b7_controls *controls)
{
	return be_b7_controls_valid(controls, BE_B7_G0_HGATP,
				    BE_U64_C(0x102027000));
}

static void test_controls(void)
{
	struct be_b7_controls controls = armed_controls();
	be_u64 *fields = (be_u64 *)(void *)&controls;
	be_size index;
	unsigned int bit;

	SCENARIO();
	CHECK(BE_B7_HSTATUS_GUEST_CONTROLS == 0x200180U);
	CHECK(BE_B7_HSTATUS_CLEARED_TRAPS == 0x500000U);
	CHECK(BE_B7_HSTATUS_VTW == 0x200000U);
	CHECK(BE_B7_HSTATUS_RESUME_MASK == 0x73f280U);
	CHECK(BE_B7_HSTATUS_RESUME_CONTROLS == 0x200080U);
	CHECK(BE_B7_SIE_STIE == 0x20U);
	CHECK(BE_B7_HVIP_VS_BITS == 0x444U);
	CHECK(BE_B7_HEDELEG == 0xb15dU);
	CHECK(BE_B7_HIDELEG_VSTI == 0x40U && BE_B7_HIE_VSTIE == 0x40U);
	CHECK(BE_B7_HCOUNTEREN_TM == 0x2U);
	CHECK(BE_B7_HENVCFG_STCE == BE_U64_C(0x8000000000000000));
	CHECK(BE_B7_SSTATUS_CONTROL_MASK == 0xde722U);
	CHECK(BE_R3_INITIAL_TRUSTED_SP == BE_U64_C(0x102027000));
	CHECK(sizeof(controls) == 16U * sizeof(be_u64));
	CHECK(armed_valid(&controls) == 1);
	CHECK(be_b7_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP,
				   BE_U64_C(0x102027000)) == 0);
	CHECK(be_b7_controls_valid(&controls, BE_B7_G1_HGATP,
				   BE_U64_C(0x102027000)) == 0);
	CHECK(be_b7_controls_valid(&controls, BE_B7_G0_HGATP,
				   BE_U64_C(0x102029000)) == 0);
	CHECK(be_b7_controls_valid((const struct be_b7_controls *)0,
				   BE_B7_G0_HGATP, BE_U64_C(0x102027000)) == 0);
	/* Any single field off its guest-run value fails. */
	for (index = 0U; index < sizeof(controls) / sizeof(be_u64); ++index) {
		bit = 2U;
		if (index == 1U)
			bit = 22U;
		else if (index == 12U)
			bit = 1U;
		controls = armed_controls();
		fields[index] ^= BE_U64_C(1) << bit;
		CHECK(armed_valid(&controls) == 0);
	}
	/*
	 * hedeleg is WARL: clearing cause 0, 4, or 6 (read-only zero on some
	 * hardware) still passes; any other flip, a missing guest-owned cause
	 * or an extra bit, fails.
	 */
	for (bit = 0U; bit < 64U; ++bit) {
		controls = armed_controls();
		controls.hedeleg ^= BE_U64_C(1) << bit;
		CHECK(armed_valid(&controls) ==
		      (bit == 0U || bit == 4U || bit == 6U ? 1 : 0));
	}
	{
		static const be_u64 warl_good[] = {
			0xb15dU, 0xb15cU, 0xb14dU, 0xb14cU,
			0xb11dU, 0xb11cU, 0xb10dU, 0xb10cU,
		};
		static const be_u64 warl_bad[] = {
			0xb17dU, 0xb15fU, 0x315dU, 0xa15dU, 0x915dU,
			0xb05dU, 0xb155U, 0xb159U, 0xb10bU, 0U,
			ALL_ONES,
		};

		CHECK(BE_B7_HEDELEG_REQUIRED == 0xb10cU);
		CHECK((BE_B7_HEDELEG & BE_B7_HEDELEG_REQUIRED) ==
		      BE_B7_HEDELEG_REQUIRED);
		for (index = 0U; index < BE_ARRAY_SIZE(warl_good); ++index) {
			controls = armed_controls();
			controls.hedeleg = warl_good[index];
			CHECK(armed_valid(&controls) == 1);
		}
		for (index = 0U; index < BE_ARRAY_SIZE(warl_bad); ++index) {
			controls = armed_controls();
			controls.hedeleg = warl_bad[index];
			CHECK(armed_valid(&controls) == 0);
		}
	}
	/* hstatus is compared under the R3 control mask only. */
	controls = armed_controls();
	controls.hstatus |= BE_R3_HSTATUS_GVA;
	CHECK(armed_valid(&controls) == 1);
	controls.hstatus |= BE_U64_C(1) << 5;
	CHECK(armed_valid(&controls) == 1);
	controls = armed_controls();
	controls.hstatus |= BE_R3_HSTATUS_VTSR;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.hstatus &= ~BE_R3_HSTATUS_VTW;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.hstatus |= BE_R3_HSTATUS_VTVM;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.hstatus &= ~BE_R3_HSTATUS_SPVP;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.hstatus |= BE_R3_HSTATUS_HU;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.hstatus |= BE_U64_C(1) << 12;
	CHECK(armed_valid(&controls) == 0);
	/* Only VSTI is delegated, only TM is opened, only STCE is set. */
	controls = armed_controls();
	controls.hideleg = 0x444U;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.hcounteren = 0x7U;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.henvcfg |= 0x80U;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.hie = BE_B7_HIE_VSTIE;
	CHECK(armed_valid(&controls) == 0);
	/* hvip: only VSSIP, VSTIP, and VSEIP are tested; QEMU's view of a
	 * pending HS STIP (bit 5) and other bits do not count. */
	for (bit = 0U; bit < 64U; ++bit) {
		controls = armed_controls();
		controls.hvip = BE_U64_C(1) << bit;
		CHECK(armed_valid(&controls) ==
		      (bit == 2U || bit == 6U || bit == 10U ? 0 : 1));
	}
	/* sie: exactly STIE, the HS slice. */
	for (bit = 0U; bit < 64U; ++bit) {
		controls = armed_controls();
		controls.sie ^= BE_U64_C(1) << bit;
		CHECK(armed_valid(&controls) == 0);
	}
	/* HS sstatus: SIE, SPIE, SPP, FS, VS, XS, SUM, and MXR all clear. */
	for (bit = 0U; bit < 64U; ++bit) {
		controls = armed_controls();
		controls.sstatus |= BE_U64_C(1) << bit;
		CHECK(armed_valid(&controls) ==
		      ((BE_B7_SSTATUS_CONTROL_MASK >> bit) & 1U ? 0 : 1));
	}
	controls = armed_controls();
	controls.sstatus |= BE_U64_C(1) << 9;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.sstatus |= BE_U64_C(1) << 10;
	CHECK(armed_valid(&controls) == 0);

	CHECK(be_b7_stce_class(BE_B7_HENVCFG_STCE) == BE_B7_CLASS_NONE);
	CHECK(be_b7_stce_class(0U) == BE_B7_CLASS_SSTC);
	CHECK(be_b7_stce_class(1U) == BE_B7_CLASS_SSTC);
	CHECK(be_b7_stce_class(ALL_ONES >> 1) == BE_B7_CLASS_SSTC);
	CHECK(be_b7_stce_class(BE_B7_HENVCFG_STCE | 1U) ==
	      BE_B7_CLASS_CONTROLS);
	CHECK(be_b7_stce_class(ALL_ONES) == BE_B7_CLASS_CONTROLS);
}

static void test_classify(void)
{
	be_u64 cause;

	SCENARIO();
	for (cause = 0U; cause < 64U; ++cause) {
		enum be_b7_class expected = BE_B7_CLASS_EXCEPTION;

		if (cause == 10U)
			expected = BE_B7_CLASS_NONE;
		else if (cause == 20U || cause == 21U || cause == 23U)
			expected = BE_B7_CLASS_GUEST_PAGE_FAULT;
		else if (cause == 22U)
			expected = BE_B7_CLASS_VIRTUAL_INSTRUCTION;
		else if (cause == 1U || cause == 5U || cause == 7U)
			expected = BE_B7_CLASS_ACCESS_FAULT;
		else if (cause == 2U)
			expected = BE_B7_CLASS_ILLEGAL_INSTRUCTION;
		CHECK(be_b7_classify_cause(cause) == expected);
		CHECK(be_b7_classify_cause(BE_B7_SCAUSE_INTERRUPT | cause) ==
		      BE_B7_CLASS_INTERRUPT);
	}
	CHECK(be_b7_classify_cause(ALL_ONES) == BE_B7_CLASS_INTERRUPT);
	CHECK(be_b7_classify_cause(ALL_ONES >> 1) == BE_B7_CLASS_EXCEPTION);
	CHECK(be_b7_classify_cause(HIGH_BIT | 10U) == BE_B7_CLASS_EXCEPTION);
	CHECK(be_b7_classify_cause(HIGH_BIT | 5U) == BE_B7_CLASS_EXCEPTION);
}

static void test_window(void)
{
	SCENARIO();
	CHECK(window.gpa_base == WINDOW_GPA);
	CHECK(window.hpa_base == WINDOW_HPA);
	CHECK(window.size == WINDOW_BYTES);
	CHECK(window.leaves == 32U);
	CHECK(window.hgatp == BE_B7_G0_HGATP);
	CHECK(windows[1].hgatp == BE_B7_G1_HGATP);
	CHECK(windows[1].hpa_base == WINDOW_G1_HPA);
	CHECK(windows[1].gpa_base == WINDOW_GPA &&
	      windows[1].size == WINDOW_BYTES);
	CHECK(window.pool_pa == BE_U64_C(0x102034000));
}

static void test_base(void)
{
	static const be_u64 available[] = {
		BE_B7_SBI_EID_BASE, BE_B7_SBI_EID_TIME, BE_B7_SBI_EID_DBCN,
		BE_B7_SBI_EID_SRST,
	};
	static const be_u64 absent[] = {
		EID_HSM, EID_IPI, EID_RFENCE, EID_PMU, EID_SUSP, EID_CPPC,
		EID_NACL, EID_STA, EID_SSE, EID_FWFT, EID_DBTR, EID_MPXY,
		EID_UNASSIGNED, 0U, ALL_ONES, HIGH_BIT | BE_B7_SBI_EID_BASE,
		HIGH_BIT | BE_B7_SBI_EID_DBCN, BE_U64_C(0x08000000),
		BE_U64_C(0x09000000), BE_U64_C(0x0a000000),
	};
	be_size index;
	be_u64 legacy;

	SCENARIO();
	check_return(BE_B7_SBI_EID_BASE, 0U, 0U, 0U, 0U, 0, 0x2000000U);
	check_return(BE_B7_SBI_EID_BASE, 0U, ALL_ONES, 7U, 9U, 0, 0x2000000U);
	check_return(BE_B7_SBI_EID_BASE, 1U, 0U, 0U, 0U, 0, 0x4245U);
	/* Version 3, not B6's 2: a shutdown stops only its guest (Q7). */
	check_return(BE_B7_SBI_EID_BASE, 2U, 0U, 0U, 0U, 0, 3U);
	check_return(BE_B7_SBI_EID_BASE, 4U, 0U, 0U, 0U, 0, 0U);
	check_return(BE_B7_SBI_EID_BASE, 5U, 0U, 0U, 0U, 0, 0U);
	check_return(BE_B7_SBI_EID_BASE, 6U, ALL_ONES, 0U, 0U, 0, 0U);
	for (index = 0U; index < BE_ARRAY_SIZE(available); ++index)
		check_return(BE_B7_SBI_EID_BASE, 3U, available[index], 0U, 0U,
			     0, 1U);
	for (index = 0U; index < BE_ARRAY_SIZE(absent); ++index)
		check_return(BE_B7_SBI_EID_BASE, 3U, absent[index], 0U, 0U, 0,
			     0U);
	for (legacy = 0U; legacy <= 0xfU; ++legacy)
		check_return(BE_B7_SBI_EID_BASE, 3U, legacy, 0U, 0U, 0, 0U);
	check_unsupported(BE_B7_SBI_EID_BASE, 7U);
	check_unsupported(BE_B7_SBI_EID_BASE, 8U);
	check_unsupported(BE_B7_SBI_EID_BASE, 0xffffffffU);
	check_unsupported(BE_B7_SBI_EID_BASE, HIGH_BIT);
	check_unsupported(BE_B7_SBI_EID_BASE, ALL_ONES);
}

static void test_unsupported(void)
{
	static const be_u64 eids[] = {
		EID_HSM, EID_IPI, EID_RFENCE, EID_PMU, EID_SUSP, EID_CPPC,
		EID_NACL, EID_STA, EID_SSE, EID_FWFT, EID_DBTR, EID_MPXY,
		EID_UNASSIGNED, BE_U64_C(0x08000000), BE_U64_C(0x09000000),
		BE_U64_C(0x0a000000), BE_U64_C(0x10) | HIGH_BIT,
		BE_B7_SBI_EID_TIME | HIGH_BIT, BE_B7_SBI_EID_DBCN | HIGH_BIT,
		BE_B7_SBI_EID_SRST | HIGH_BIT, ALL_ONES,
	};
	be_size index;
	be_u64 legacy;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(eids); ++index) {
		check_unsupported(eids[index], 0U);
		check_unsupported(eids[index], 1U);
	}
	/* Legacy extensions 0x00-0x0F, including console putchar (0x01). */
	for (legacy = 0U; legacy <= 0xfU; ++legacy) {
		check_unsupported(legacy, 0U);
		check_return(legacy, 0U, 'x', 0U, 0U,
			     BE_B7_SBI_ERR_NOT_SUPPORTED, 0U);
	}
}

static void test_time(void)
{
	static const be_u64 values[] = {
		0U, 1U, 0x10000U, ALL_ONES >> 1, ALL_ONES - 1U, ALL_ONES,
	};
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(values); ++index) {
		struct be_b7_exit record = ecall(BE_B7_SBI_EID_TIME, 0U,
					       values[index], 5U, 6U);
		struct be_b7_state state = fresh_state();
		struct be_b7_result result;

		CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
		      BE_B7_ACTION_SET_TIMER);
		CHECK(result.timer == values[index]);
		CHECK(result.error == BE_B7_SBI_SUCCESS);
		CHECK(result.value == 0U);
		CHECK(state.guest[0].counts.time == 1U && call_sum(&state.guest[0].counts) == 1U);
	}
	check_unsupported(BE_B7_SBI_EID_TIME, 1U);
	check_unsupported(BE_B7_SBI_EID_TIME, 2U);
	check_unsupported(BE_B7_SBI_EID_TIME, HIGH_BIT);
	check_unsupported(BE_B7_SBI_EID_TIME, ALL_ONES);
}

static void test_dbcn_window(void)
{
	be_u64 leaf;

	SCENARIO();
	/* First and last byte, whole window, and the 256-byte cap. */
	check_dbcn_write(1U, WINDOW_GPA, 0U, WINDOW_HPA, 1U);
	check_dbcn_write(1U, WINDOW_GPA + WINDOW_BYTES - 1U, 0U,
			 WINDOW_HPA + WINDOW_BYTES - 1U, 1U);
	check_dbcn_write(16U, WINDOW_GPA + WINDOW_BYTES - 16U, 0U,
			 WINDOW_HPA + WINDOW_BYTES - 16U, 16U);
	check_dbcn_write(WINDOW_BYTES, WINDOW_GPA, 0U, WINDOW_HPA, 256U);
	check_dbcn_write(257U, WINDOW_GPA, 0U, WINDOW_HPA, 256U);
	check_dbcn_write(256U, WINDOW_GPA + 0xf00U, 0U, WINDOW_HPA + 0xf00U,
			 256U);
	check_dbcn_write(255U, WINDOW_GPA + 0x10U, 0U, WINDOW_HPA + 0x10U,
			 255U);
	/* Every 2 MiB leaf: its last page, and a range across its end. */
	for (leaf = 0U; leaf < 32U; ++leaf) {
		be_u64 end = (leaf + 1U) * 2U * MIB;

		check_dbcn_write(0x1000U, WINDOW_GPA + end - 0x1000U, 0U,
				 WINDOW_HPA + end - 0x1000U, 256U);
		if (leaf < 31U)
			check_dbcn_write(32U, WINDOW_GPA + end - 16U, 0U,
					 WINDOW_HPA + end - 16U, 32U);
	}
	/* The kernel's own pages and the DTB page. */
	check_dbcn_write(64U, BE_B7_KERNEL_GPA, 0U, BE_U64_C(0x110200000),
			 64U);
	check_dbcn_write(40U, BE_B7_DTB_GPA, 0U, BE_U64_C(0x113e00000), 40U);
	/* Crossing the end of the window, or starting before it. */
	check_dbcn_refused(2U, WINDOW_GPA + WINDOW_BYTES - 1U, 0U);
	check_dbcn_refused(WINDOW_BYTES + 1U, WINDOW_GPA, 0U);
	check_dbcn_refused(WINDOW_BYTES, WINDOW_GPA + 1U, 0U);
	check_dbcn_refused(32U, WINDOW_GPA + WINDOW_BYTES - 16U, 0U);
	check_dbcn_refused(2U, WINDOW_GPA - 1U, 0U);
	check_dbcn_refused(1U, WINDOW_GPA - 1U, 0U);
	check_dbcn_refused(1U, WINDOW_GPA + WINDOW_BYTES, 0U);
	/* A nonzero high address word refuses even a valid range. */
	check_dbcn_refused(1U, WINDOW_GPA, 1U);
	check_dbcn_refused(1U, WINDOW_GPA, ALL_ONES);
	check_dbcn_refused(1U, WINDOW_GPA, BE_U64_C(1) << 63);
	/* Host-physical addresses are not guest addresses. */
	check_dbcn_refused(1U, WINDOW_HPA, 0U);
	check_dbcn_refused(1U, BE_U64_C(0x102000000), 0U);
	check_dbcn_refused(1U, BE_U64_C(0x102034000), 0U);
	check_dbcn_refused(1U, BE_U64_C(0x108035000), 0U);
}

static void test_dbcn_refusals(void)
{
	static const be_u64 unmapped[] = {
		0U, BE_U64_C(0x40000000), BE_U64_C(0x40010000),
		BE_U64_C(0x7fe00000), BE_U64_C(0x7ffff000),
		BE_U64_C(0x84000000), BE_U64_C(0x88000000),
		BE_U64_C(0xc0000000), BE_U64_C(0x180000000),
		BE_U64_C(0x10200f000), ALL_ONES - 0xfffU,
	};
	struct be_b7_gstage_map empty = { 0U, 0U, 0U, 0U, 0U, 0U, 0U };
	struct be_b7_state state = fresh_state();
	struct be_b7_exit record;
	struct be_b7_result result;
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(unmapped); ++index) {
		check_dbcn_refused(1U, unmapped[index], 0U);
		check_dbcn_refused(8U, unmapped[index], 0U);
	}
	/* Wrapping ranges. */
	check_dbcn_refused(ALL_ONES, WINDOW_GPA, 0U);
	check_dbcn_refused(ALL_ONES - 0x7fffffffU, WINDOW_GPA, 0U);
	check_dbcn_refused(2U, ALL_ONES, 0U);
	check_dbcn_refused(1U, ALL_ONES, 0U);
	check_dbcn_refused(BE_U64_C(0x1000), ALL_ONES - 0xffeU, 0U);
	/* Zero length returns 0, 0 without a range check... */
	check_return(BE_B7_SBI_EID_DBCN, 0U, 0U, BE_U64_C(0x40001000), 0U, 0,
		     0U);
	check_return(BE_B7_SBI_EID_DBCN, 0U, 0U, ALL_ONES, 0U, 0, 0U);
	check_return(BE_B7_SBI_EID_DBCN, 0U, 0U, WINDOW_GPA, 0U, 0, 0U);
	/* ...but never with a nonzero high word. */
	check_dbcn_refused(0U, WINDOW_GPA, 1U);
	/* An unwalked (empty) window admits nothing. */
	record = ecall(BE_B7_SBI_EID_DBCN, 0U, 1U, WINDOW_GPA, 0U);
	CHECK(be_b7_handle_exit(&state, 0U, &empty, &record, &result) ==
	      BE_B7_ACTION_RETURN);
	CHECK(result.error == BE_B7_SBI_ERR_INVALID_PARAM);
	CHECK(state.guest[0].counts.refused == 1U && state.guest[0].counts.dbcn_write == 0U);
}

static void test_dbcn_other(void)
{
	struct be_b7_exit record;
	struct be_b7_result result;
	struct be_b7_state state;
	be_u64 byte;

	SCENARIO();
	/* Console read is denied whatever the range, and is not refused. */
	check_return(BE_B7_SBI_EID_DBCN, 1U, 4U, WINDOW_GPA, 0U,
		     BE_B7_SBI_ERR_DENIED, 0U);
	check_return(BE_B7_SBI_EID_DBCN, 1U, 0U, 0U, 0U,
		     BE_B7_SBI_ERR_DENIED, 0U);
	check_return(BE_B7_SBI_EID_DBCN, 1U, ALL_ONES, ALL_ONES, ALL_ONES,
		     BE_B7_SBI_ERR_DENIED, 0U);
	state = fresh_state();
	record = ecall(BE_B7_SBI_EID_DBCN, 1U, 16U, WINDOW_GPA, 0U);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_RETURN);
	CHECK(state.guest[0].counts.dbcn_read == 1U && state.guest[0].counts.refused == 0U);
	/* Write byte takes the low byte of a0. */
	for (byte = 0U; byte < 0x100U; ++byte) {
		record = ecall(BE_B7_SBI_EID_DBCN, 2U, byte | 0xab00U, 0U, 0U);
		state = fresh_state();
		CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
		      BE_B7_ACTION_CONSOLE_BYTE);
		CHECK(result.byte == byte);
		CHECK(result.error == BE_B7_SBI_SUCCESS);
		CHECK(result.value == 0U);
		CHECK(state.guest[0].counts.dbcn_byte == 1U &&
		      call_sum(&state.guest[0].counts) == 1U);
	}
	record = ecall(BE_B7_SBI_EID_DBCN, 2U, ALL_ONES, 1U, 2U);
	result = decide(&record);
	CHECK(result.action == BE_B7_ACTION_CONSOLE_BYTE);
	CHECK(result.byte == 0xffU);
	check_unsupported(BE_B7_SBI_EID_DBCN, 3U);
	check_unsupported(BE_B7_SBI_EID_DBCN, 4U);
	check_unsupported(BE_B7_SBI_EID_DBCN, HIGH_BIT);
	check_unsupported(BE_B7_SBI_EID_DBCN, ALL_ONES);
}

static void test_srst_grid(void)
{
	static const be_u64 types[] = {
		0U, 1U, 2U, 3U, 4U, BE_U64_C(0xf0000000),
		BE_U64_C(0xffffffff), HIGH_BIT, ALL_ONES,
	};
	static const be_u64 reasons[] = {
		0U, 1U, 2U, 3U, BE_U64_C(0xf0000000), HIGH_BIT, ALL_ONES,
	};
	be_size type_index;
	be_size reason_index;

	SCENARIO();
	for (type_index = 0U; type_index < BE_ARRAY_SIZE(types);
	     ++type_index) {
		for (reason_index = 0U; reason_index < BE_ARRAY_SIZE(reasons);
		     ++reason_index) {
			be_u64 type = types[type_index];
			be_u64 reason = reasons[reason_index];
			struct be_b7_state state = fresh_state();
			struct be_b7_exit record = ecall(BE_B7_SBI_EID_SRST, 0U,
						       type, reason, 0U);
			struct be_b7_result result;

			(void)be_b7_handle_exit(&state, 0U, &window, &record,
						&result);
			if (type > 2U || reason > 1U) {
				/* Reserved values are refused, as in B5. */
				CHECK(result.action == BE_B7_ACTION_RETURN);
				CHECK(result.error ==
				      BE_B7_SBI_ERR_INVALID_PARAM);
				CHECK(state.phase == BE_B7_PHASE_RUNNING);
				CHECK(state.guest[0].phase ==
				      BE_B7_PHASE_RUNNING);
				CHECK(state.guest[0].counts.refused == 1U);
			} else if (type != 0U) {
				/* A cold or warm reboot ends the run. */
				CHECK(result.action ==
				      BE_B7_ACTION_GUEST_REBOOT);
				CHECK(state.phase == BE_B7_PHASE_FAILED);
				CHECK(state.failure ==
				      BE_B7_CLASS_GUEST_REBOOT);
				CHECK(result.failure ==
				      BE_B7_CLASS_GUEST_REBOOT);
				CHECK(state.guest[0].counts.srst == 1U);
			} else if (reason == 0U) {
				/* Only the calling guest stops. */
				CHECK(result.action == BE_B7_ACTION_STOP);
				CHECK(state.guest[0].phase ==
				      BE_B7_PHASE_STOPPED);
				CHECK(state.phase == BE_B7_PHASE_RUNNING);
				CHECK(state.guest[1].phase ==
				      BE_B7_PHASE_RUNNING);
				CHECK(result.failure == BE_B7_CLASS_NONE);
				CHECK(state.guest[0].counts.srst == 1U);
			} else {
				CHECK(result.action ==
				      BE_B7_ACTION_GUEST_FAILURE);
				CHECK(state.phase == BE_B7_PHASE_FAILED);
				CHECK(state.failure ==
				      BE_B7_CLASS_GUEST_FAILURE);
				CHECK(result.failure ==
				      BE_B7_CLASS_GUEST_FAILURE);
				CHECK(state.guest[0].counts.srst == 1U);
			}
			CHECK(result.value == 0U);
			CHECK(state.guest[0].counts.exits == 1U);
			CHECK(call_sum(&state.guest[0].counts) == 1U);
		}
	}
	check_unsupported(BE_B7_SBI_EID_SRST, 1U);
	check_unsupported(BE_B7_SBI_EID_SRST, 2U);
	check_unsupported(BE_B7_SBI_EID_SRST, HIGH_BIT);
	check_unsupported(BE_B7_SBI_EID_SRST, ALL_ONES);
}

static void test_after_shutdown(void)
{
	struct be_b7_state state = fresh_state();
	struct be_b7_exit record = ecall(BE_B7_SBI_EID_SRST, 0U, 0U, 0U, 0U);
	struct be_b7_exit base = ecall(BE_B7_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b7_result result;

	SCENARIO();
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_STOP);
	/* The other guest runs on, and stops in turn. */
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &base, &result) ==
	      BE_B7_ACTION_RETURN);
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &record, &result) ==
	      BE_B7_ACTION_STOP);
	CHECK(state.phase == BE_B7_PHASE_RUNNING);
	CHECK(state.guest[1].phase == BE_B7_PHASE_STOPPED);
	CHECK(state.guest[1].counts.exits == 2U &&
	      state.guest[1].counts.srst == 1U);
	/* An exit of a stopped guest fails the run. */
	CHECK(be_b7_handle_exit(&state, 0U, &window, &base, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXCEPTION);
	CHECK(state.phase == BE_B7_PHASE_FAILED);
	CHECK(state.guest[0].counts.exits == 1U);

	state = fresh_state();
	record = ecall(BE_B7_SBI_EID_SRST, 0U, 0U, 1U, 0U);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_GUEST_FAILURE);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &base, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_GUEST_FAILURE);
	CHECK(state.failure == BE_B7_CLASS_GUEST_FAILURE);

	state = fresh_state();
	record = ecall(BE_B7_SBI_EID_SRST, 0U, 2U, 0U, 0U);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_GUEST_REBOOT);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &base, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_GUEST_REBOOT);
	CHECK(state.guest[0].counts.exits == 1U);
}

/* The ceiling counts every exit, whatever its class or outcome. */
static void check_ceiling(be_u64 ceiling)
{
	struct be_b7_state state = BE_B7_STATE_INITIALIZER(
		ceiling, BE_B7_GUEST_TIME_BUDGET);
	struct be_b7_exit record = ecall(BE_B7_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b7_exit unknown = ecall(EID_UNASSIGNED, 0U, 0U, 0U, 0U);
	struct be_b7_result result;
	be_u64 count;
	be_u64 good = 0U;

	state.entry_time = ENTRY_TIME;
	for (count = 1U; count <= ceiling; ++count) {
		const struct be_b7_exit *next = (count & 1U) ? &record : &unknown;

		if (be_b7_handle_exit(&state, 0U, &window, next, &result) ==
		    BE_B7_ACTION_RETURN)
			++good;
	}
	CHECK(good == ceiling);
	CHECK(state.guest[0].counts.exits == ceiling);
	CHECK(state.guest[0].counts.base == (ceiling + 1U) / 2U);
	CHECK(state.guest[0].counts.refused == ceiling / 2U);
	CHECK(call_sum(&state.guest[0].counts) == ceiling);
	CHECK(state.phase == BE_B7_PHASE_RUNNING);
	/* Each guest has its own ceiling: G1's first exit still passes. */
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &record, &result) ==
	      BE_B7_ACTION_RETURN);
	CHECK(state.guest[1].counts.exits == 1U);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXIT_BUDGET);
	CHECK(state.phase == BE_B7_PHASE_FAILED);
	CHECK(state.guest[0].counts.exits == ceiling + 1U);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXIT_BUDGET);
	CHECK(state.guest[0].counts.exits == ceiling + 1U);

	/* A terminal exit at the ceiling reports the ceiling. */
	state = (struct be_b7_state)BE_B7_STATE_INITIALIZER(
		ceiling, BE_B7_GUEST_TIME_BUDGET);
	state.guest[0].counts.exits = ceiling;
	record = exit_with(BE_B7_SCAUSE_LOAD_GUEST_PAGE_FAULT, ECALL_PC);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXIT_BUDGET);
}

static void test_exit_ceiling(void)
{
	SCENARIO();
	check_ceiling(BE_B7_VARIANT_EXIT_CEILING);
	check_ceiling(BE_B7_EXIT_CEILING);
}

/* The guest-time budget counts from the first entry, at every exit. */
static void check_budget(be_u64 budget)
{
	struct be_b7_state state = BE_B7_STATE_INITIALIZER(
		BE_B7_EXIT_CEILING, budget);
	struct be_b7_exit record = ecall(BE_B7_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b7_result result;

	state.entry_time = ENTRY_TIME;
	record.time = ENTRY_TIME;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_RETURN);
	record.time = ENTRY_TIME + budget - 1U;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_RETURN);
	record.time = ENTRY_TIME + budget;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_GUEST_TIMEOUT);
	CHECK(state.phase == BE_B7_PHASE_FAILED);
	CHECK(state.guest[0].counts.exits == 3U && call_sum(&state.guest[0].counts) == 2U);
	/* A time before the entry is out of budget too. */
	state = (struct be_b7_state)BE_B7_STATE_INITIALIZER(
		BE_B7_EXIT_CEILING, budget);
	state.entry_time = ENTRY_TIME;
	record.time = ENTRY_TIME - 1U;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_GUEST_TIMEOUT);
	/* The budget is checked before the cause: a late fault times out. */
	state = (struct be_b7_state)BE_B7_STATE_INITIALIZER(
		BE_B7_EXIT_CEILING, budget);
	state.entry_time = ENTRY_TIME;
	record = exit_with(BE_B7_SCAUSE_VIRTUAL_INSTRUCTION, ECALL_PC);
	record.time = ENTRY_TIME + budget + 1U;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_GUEST_TIMEOUT);
	/* The ceiling is checked before the budget. */
	state = (struct be_b7_state)BE_B7_STATE_INITIALIZER(1U, budget);
	state.entry_time = ENTRY_TIME;
	state.guest[0].counts.exits = 1U;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXIT_BUDGET);
}

static void test_time_budget(void)
{
	SCENARIO();
	check_budget(BE_B7_VARIANT_GUEST_TIME_BUDGET);
	check_budget(BE_B7_GUEST_TIME_BUDGET);
	/* 2^32 ticks is about 179 s at the board's 24 MHz timebase. */
	CHECK(BE_B7_GUEST_TIME_BUDGET / BE_B7_TIMEBASE_HZ == 178U);
}

static void test_terminal_exits(void)
{
	static const struct {
		be_u64 scause;
		enum be_b7_class failure;
	} exits[] = {
		{ BE_B7_SCAUSE_INTERRUPT | 1U, BE_B7_CLASS_INTERRUPT },
		{ BE_B7_SCAUSE_INTERRUPT | 2U, BE_B7_CLASS_INTERRUPT },
		{ BE_B7_SCAUSE_INTERRUPT | 4U, BE_B7_CLASS_INTERRUPT },
		{ BE_B7_SCAUSE_INTERRUPT | 13U, BE_B7_CLASS_INTERRUPT },
		{ BE_B7_SCAUSE_INTERRUPT | 5U | HIGH_BIT,
		  BE_B7_CLASS_INTERRUPT },
		{ BE_B7_SCAUSE_INTERRUPT | 6U, BE_B7_CLASS_INTERRUPT },
		{ BE_B7_SCAUSE_INTERRUPT | 9U, BE_B7_CLASS_INTERRUPT },
		{ BE_B7_SCAUSE_INTERRUPT | 10U, BE_B7_CLASS_INTERRUPT },
		{ BE_B7_SCAUSE_INTERRUPT | 12U, BE_B7_CLASS_INTERRUPT },
		{ 20U, BE_B7_CLASS_GUEST_PAGE_FAULT },
		{ 21U, BE_B7_CLASS_GUEST_PAGE_FAULT },
		{ 23U, BE_B7_CLASS_GUEST_PAGE_FAULT },
		{ 22U, BE_B7_CLASS_VIRTUAL_INSTRUCTION },
		{ 1U, BE_B7_CLASS_ACCESS_FAULT },
		{ 5U, BE_B7_CLASS_ACCESS_FAULT },
		{ 7U, BE_B7_CLASS_ACCESS_FAULT },
		{ 2U, BE_B7_CLASS_ILLEGAL_INSTRUCTION },
		{ 0U, BE_B7_CLASS_EXCEPTION },
		{ 3U, BE_B7_CLASS_EXCEPTION },
		{ 4U, BE_B7_CLASS_EXCEPTION },
		{ 6U, BE_B7_CLASS_EXCEPTION },
		{ 8U, BE_B7_CLASS_EXCEPTION },
		{ 9U, BE_B7_CLASS_EXCEPTION },
		{ 11U, BE_B7_CLASS_EXCEPTION },
		{ 12U, BE_B7_CLASS_EXCEPTION },
		{ 13U, BE_B7_CLASS_EXCEPTION },
		{ 15U, BE_B7_CLASS_EXCEPTION },
		{ 18U, BE_B7_CLASS_EXCEPTION },
		{ 19U, BE_B7_CLASS_EXCEPTION },
		{ 24U, BE_B7_CLASS_EXCEPTION },
	};
	be_size index;
	unsigned int spvp;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(exits); ++index) {
		/* VS-origin (SPVP = 1) and VU-origin (SPVP = 0) alike. */
		for (spvp = 0U; spvp < 2U; ++spvp) {
			struct be_b7_state state = fresh_state();
			struct be_b7_exit record = exit_with(exits[index].scause,
							   ECALL_PC);
			struct be_b7_exit base = ecall(BE_B7_SBI_EID_BASE, 0U,
						       0U, 0U, 0U);
			struct be_b7_result result;

			if (spvp == 0U)
				record.hstatus &= ~BE_B7_HSTATUS_SPVP;
			/* The registers of an SBI call do not matter here. */
			record.frame.gpr[BE_R4_GPR_A7] = BE_B7_SBI_EID_BASE;
			record.frame.gpr[BE_R4_GPR_A6] = 0U;
			CHECK(be_b7_handle_exit(&state, 0U, &window, &record,
						&result) ==
			      BE_B7_ACTION_TERMINAL);
			CHECK(result.failure == exits[index].failure);
			CHECK(state.phase == BE_B7_PHASE_FAILED);
			CHECK(state.failure == exits[index].failure);
			CHECK(state.guest[0].counts.exits == 1U);
			CHECK(call_sum(&state.guest[0].counts) == 0U);
			CHECK(be_b7_handle_exit(&state, 0U, &window, &base,
						&result) ==
			      BE_B7_ACTION_TERMINAL);
			CHECK(result.failure == exits[index].failure);
			CHECK(state.guest[0].counts.exits == 1U);
		}
	}
}

static void test_frame_integrity(void)
{
	struct be_b7_state state = fresh_state();
	struct be_b7_exit record = ecall(BE_B7_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b7_result result;

	SCENARIO();
	record.frame.reserved = 1U;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXCEPTION);

	/* Only an exit from V=1 (SPV = 1) is a guest exit. */
	state = fresh_state();
	record = ecall(BE_B7_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	record.hstatus &= ~BE_B7_HSTATUS_SPV;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXCEPTION);
	state = fresh_state();
	record.hstatus = BE_B7_HSTATUS_SPV;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_RETURN);

	state = fresh_state();
	record = ecall(BE_B7_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	record.frame.sepc = ALL_ONES - 3U;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_RESUME);

	state = fresh_state();
	record.frame.sepc = ALL_ONES - 4U;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_RETURN);
	CHECK(result.resume_pc == ALL_ONES);

	state = fresh_state();
	CHECK(be_b7_handle_exit(&state, 0U, (const struct be_b7_gstage_map *)0,
				&record, &result) == BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXCEPTION);
	state = fresh_state();
	CHECK(be_b7_handle_exit(&state, 0U, &window,
				(const struct be_b7_exit *)0, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(state.phase == BE_B7_PHASE_FAILED);
	state = fresh_state();
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record,
				(struct be_b7_result *)0) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(state.phase == BE_B7_PHASE_FAILED);
	CHECK(be_b7_handle_exit((struct be_b7_state *)0, 0U, &window, &record,
				&result) == BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXCEPTION);

	/* The sticky class: the first failure is kept. */
	state = fresh_state();
	CHECK(be_b7_fail(&state, BE_B7_CLASS_SSTC) == BE_B7_CLASS_SSTC);
	CHECK(be_b7_fail(&state, BE_B7_CLASS_CONSOLE) == BE_B7_CLASS_SSTC);
	state = fresh_state();
	CHECK(be_b7_fail(&state, BE_B7_CLASS_NONE) == BE_B7_CLASS_EXCEPTION);
	CHECK(be_b7_fail((struct be_b7_state *)0, BE_B7_CLASS_BOOT) ==
	      BE_B7_CLASS_BOOT);
	state = fresh_state();
	CHECK(be_b7_fail(&state, BE_B7_CLASS_COUNT) == BE_B7_CLASS_EXCEPTION);
}

static void test_apply_return(void)
{
	struct be_b7_exit record = ecall(BE_B7_SBI_EID_BASE, 7U, 1U, 2U, 3U);
	struct be_b7_exit before = record;
	struct be_b7_result result = decide(&record);
	be_size index;

	SCENARIO();
	CHECK(result.error == BE_B7_SBI_ERR_NOT_SUPPORTED);
	be_b7_apply_return(&record.frame, &result);
	CHECK(record.frame.gpr[BE_R4_GPR_A0] == (be_u64)-2L);
	CHECK(record.frame.gpr[BE_R4_GPR_A1] == 0U);
	CHECK(record.frame.sepc == ECALL_PC + 4U);
	for (index = 0U; index < BE_ARRAY_SIZE(record.frame.gpr); ++index) {
		if (index == BE_R4_GPR_A0 || index == BE_R4_GPR_A1)
			continue;
		CHECK(record.frame.gpr[index] == before.frame.gpr[index]);
	}
	CHECK(record.frame.vstvec == before.frame.vstvec &&
	      record.frame.vsepc == before.frame.vsepc);
	CHECK(record.frame.vscause == before.frame.vscause &&
	      record.frame.vstval == before.frame.vstval);
	CHECK(record.frame.scause == before.frame.scause &&
	      record.frame.stval == before.frame.stval);
	CHECK(record.frame.htval == before.frame.htval &&
	      record.frame.reserved == before.frame.reserved);
	CHECK(record.hstatus == before.hstatus && record.htinst == before.htinst &&
	      record.vsatp == before.vsatp && record.time == before.time);
	be_b7_apply_return((struct be_r4_frame *)0, &result);
	be_b7_apply_return(&record.frame, (const struct be_b7_result *)0);
	CHECK(record.frame.sepc == ECALL_PC + 4U);
	/* An idling wfi steps sepc past the wfi and nothing else. */
	record = exit_with(BE_B7_SCAUSE_VIRTUAL_INSTRUCTION, ECALL_PC);
	record.frame.stval = WFI;
	before = record;
	result = (struct be_b7_result){ .action = BE_B7_ACTION_WFI,
					.error = -9, .value = 9U,
					.resume_pc = ECALL_PC + 4U };
	be_b7_apply_return(&record.frame, &result);
	CHECK(record.frame.sepc == ECALL_PC + 4U);
	before.frame.sepc = ECALL_PC + 4U;
	CHECK(memcmp(&record, &before, sizeof(record)) == 0);
	/* A slice, a stop, and terminal decisions change nothing. */
	{
		static const enum be_b7_action untouched[] = {
			BE_B7_ACTION_NONE, BE_B7_ACTION_SLICE,
			BE_B7_ACTION_STOP, BE_B7_ACTION_GUEST_FAILURE,
			BE_B7_ACTION_GUEST_REBOOT, BE_B7_ACTION_TERMINAL,
		};

		for (index = 0U; index < BE_ARRAY_SIZE(untouched); ++index) {
			record = exit_with(STI, ECALL_PC);
			before = record;
			result = (struct be_b7_result){
				.action = untouched[index], .error = -9,
				.value = 9U, .resume_pc = 0x1000U };
			be_b7_apply_return(&record.frame, &result);
			CHECK(memcmp(&record, &before, sizeof(record)) == 0);
		}
	}
}

/* The first entry: sepc, a0 = hart, a1 = DTB; every other word 0. */
static void test_entry_frame(void)
{
	struct be_b7_exit record;
	const be_u64 *words = (const be_u64 *)(const void *)&record;
	be_size index;

	SCENARIO();
	memset(&record, 0xa5, sizeof(record));
	be_b7_entry_frame(&record, BE_B7_KERNEL_GPA, BE_B7_GUEST_HART,
			  BE_B7_DTB_GPA);
	CHECK(record.frame.sepc == BE_U64_C(0x80200000));
	CHECK(record.frame.gpr[BE_R4_GPR_A0] == 0U);
	CHECK(record.frame.gpr[BE_R4_GPR_A1] == BE_U64_C(0x83e00000));
	/* The entry is into VS mode: SPV and SPVP. */
	CHECK(record.hstatus == 0x180U);
	CHECK(be_b7_record_spp(&record) == 0x100U);
	for (index = 0U; index < sizeof(record) / sizeof(be_u64); ++index) {
		if (index == BE_R4_GPR_A1 ||
		    index == __builtin_offsetof(struct be_r4_frame, sepc) /
				     sizeof(be_u64) ||
		    index == __builtin_offsetof(struct be_b7_exit, hstatus) /
				     sizeof(be_u64))
			continue;
		CHECK(words[index] == 0U);
	}
	be_b7_entry_frame(&record, 1U, 2U, 3U);
	CHECK(record.frame.sepc == 1U && record.frame.gpr[BE_R4_GPR_A0] == 2U &&
	      record.frame.gpr[BE_R4_GPR_A1] == 3U);
	be_b7_entry_frame((struct be_b7_exit *)0, 1U, 2U, 3U);
}

static char console_output[BE_B7_CONSOLE_CAPACITY + 16U];

static be_u64 feed(struct be_b7_console *console, be_u32 guest,
		   const char *text)
{
	return be_b7_console_feed(console, guest, (const be_u8 *)text,
				  strlen(text), console_output,
				  BE_B7_CONSOLE_CAPACITY);
}

static int output_is(be_u64 length, const char *text)
{
	return length == strlen(text) &&
	       memcmp(console_output, text, strlen(text)) == 0;
}

static void test_console(void)
{
	struct be_b7_console console = { 0 };
	struct be_b7_console copy;
	be_u8 input[BE_B7_DBCN_MAX_BYTES + 1U];
	be_u64 length;
	be_size index;

	SCENARIO();
	CHECK(strcmp(be_b7_guest_prefix(0U), "BE_B7_G0: ") == 0);
	CHECK(strcmp(be_b7_guest_prefix(1U), "BE_B7_G1: ") == 0);
	CHECK(be_b7_guest_prefix(2U) == (const char *)0);
	/* A whole line: the guest's prefix, the line, and LF. */
	length = feed(&console, 0U, "[    0.000000] Linux version 7.2.0\n");
	CHECK(output_is(length,
			"BE_B7_G0: [    0.000000] Linux version 7.2.0\n"));
	CHECK(console.length == 0U);
	/* hvc sends CR before LF: the CR is dropped. */
	length = feed(&console, 1U, "B7INIT 05 RESULT pass\r\n");
	CHECK(output_is(length, "BE_B7_G1: B7INIT 05 RESULT pass\n"));
	/* CR alone writes nothing and buffers nothing. */
	length = feed(&console, 0U, "\r");
	CHECK(length == 0U && console.length == 0U);
	length = feed(&console, 0U, "\r\r\n");
	CHECK(output_is(length, "BE_B7_G0: \n"));
	length = feed(&console, 0U, "a\rb\n");
	CHECK(output_is(length, "BE_B7_G0: ab\n"));
	/* A line split across calls is written once, whole, at its LF. */
	length = feed(&console, 0U, "B7INIT 01 ST");
	CHECK(length == 0U && console.length == 12U);
	length = feed(&console, 0U, "ART guest=0 pid=1\r");
	CHECK(length == 0U && console.length == 29U);
	length = feed(&console, 0U, "\n");
	CHECK(output_is(length, "BE_B7_G0: B7INIT 01 START guest=0 pid=1\n"));
	CHECK(console.length == 0U);
	/* A bare newline is an empty guest line. */
	length = feed(&console, 1U, "\n");
	CHECK(output_is(length, "BE_B7_G1: \n"));
	/* Several lines in one call; the partial line waits. */
	length = feed(&console, 1U, "one\ntwo\nthr");
	CHECK(output_is(length, "BE_B7_G1: one\nBE_B7_G1: two\n"));
	CHECK(console.length == 3U);
	length = feed(&console, 1U, "ee\n");
	CHECK(output_is(length, "BE_B7_G1: three\n"));
	/* Forged evidence and forged tags stay inside a guest line. */
	length = feed(&console, 0U, "x\nBE_R3:01 BOOT_VALIDATED\n");
	CHECK(output_is(length,
			"BE_B7_G0: x\nBE_B7_G0: BE_R3:01 BOOT_VALIDATED\n"));
	length = feed(&console, 0U, "\tBE_B7:11 SHUTDOWN type=0 reason=0\n");
	CHECK(output_is(length,
			"BE_B7_G0: ?BE_B7:11 SHUTDOWN type=0 reason=0\n"));
	length = feed(&console, 1U, "BE_B7_G0: forged\n");
	CHECK(output_is(length, "BE_B7_G1: BE_B7_G0: forged\n"));
	/* Every byte value: printable ASCII and LF pass, CR vanishes, the
	 * rest is '?'. */
	for (index = 0U; index < 256U; ++index) {
		be_u8 byte = (be_u8)index;

		console.length = 1U;
		console.text[0] = 'k';
		length = be_b7_console_feed(&console, 0U, &byte, 1U,
					    console_output,
					    BE_B7_CONSOLE_CAPACITY);
		if (byte == '\r') {
			CHECK(length == 0U && console.length == 1U);
		} else if (byte == '\n') {
			CHECK(output_is(length, "BE_B7_G0: k\n"));
			CHECK(console.length == 0U);
		} else {
			CHECK(length == 0U && console.length == 2U);
			CHECK(console.text[1] ==
			      (byte >= 0x20U && byte <= 0x7eU ? (char)byte :
								'?'));
		}
	}
	/* A full buffer is written as its own line when one more byte
	 * comes; a full line that its LF ends is one line. */
	console.length = 0U;
	memset(input, 'y', sizeof(input));
	length = be_b7_console_feed(&console, 1U, input, 256U, console_output,
				    BE_B7_CONSOLE_CAPACITY);
	CHECK(length == 0U && console.length == 256U);
	length = feed(&console, 1U, "z\n");
	CHECK(length == 10U + 256U + 1U + 10U + 2U);
	CHECK(memcmp(console_output, "BE_B7_G1: ", 10U) == 0);
	for (index = 0U; index < 256U; ++index)
		CHECK(console_output[10U + index] == 'y');
	CHECK(memcmp(console_output + 266U, "\nBE_B7_G1: z\n", 13U) == 0);
	length = be_b7_console_feed(&console, 0U, input, 256U, console_output,
				    BE_B7_CONSOLE_CAPACITY);
	CHECK(length == 0U && console.length == 256U);
	length = feed(&console, 0U, "\n");
	CHECK(length == 267U && console_output[266] == '\n');
	CHECK(console.length == 0U);
	/* The worst case, a full buffer, one more byte, then 255 LFs. */
	length = be_b7_console_feed(&console, 0U, input, 256U, console_output,
				    BE_B7_CONSOLE_CAPACITY);
	memset(input, '\n', sizeof(input));
	input[0] = 'q';
	length = be_b7_console_feed(&console, 0U, input, 256U, console_output,
				    BE_B7_CONSOLE_CAPACITY);
	CHECK(length == 256U * 11U + 257U);
	CHECK(length <= BE_B7_CONSOLE_CAPACITY);
	CHECK(memcmp(console_output + 267U, "BE_B7_G0: q\n", 12U) == 0);
	for (index = 0U; index < 254U; ++index)
		CHECK(memcmp(console_output + 279U + index * 11U,
			     "BE_B7_G0: \n", 11U) == 0);
	/* A chunk of CRs writes nothing. */
	memset(input, '\r', sizeof(input));
	CHECK(be_b7_console_feed(&console, 0U, input, 256U, console_output,
				 BE_B7_CONSOLE_CAPACITY) == 0U);
	CHECK(console.length == 0U);
	/* Flush: the partial line, ended; nothing buffered writes nothing. */
	CHECK(be_b7_console_flush(&console, 0U, console_output,
				  BE_B7_CONSOLE_CAPACITY) == 0U);
	(void)feed(&console, 1U, "partial");
	length = be_b7_console_flush(&console, 1U, console_output,
				     BE_B7_CONSOLE_CAPACITY);
	CHECK(output_is(length, "BE_B7_G1: partial\n"));
	CHECK(console.length == 0U);
	CHECK(be_b7_console_flush(&console, 1U, console_output,
				  BE_B7_CONSOLE_CAPACITY) == 0U);
	/* Invalid requests change nothing. */
	memset(input, 'x', sizeof(input));
	(void)feed(&console, 0U, "kept");
	copy = console;
	CHECK(be_b7_console_feed(&console, 0U, input, 257U, console_output,
				 BE_B7_CONSOLE_CAPACITY) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(be_b7_console_feed(&console, 0U, input, 1U, console_output,
				 BE_B7_CONSOLE_CAPACITY - 1U) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(be_b7_console_feed(&console, 2U, input, 1U, console_output,
				 BE_B7_CONSOLE_CAPACITY) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(be_b7_console_feed((struct be_b7_console *)0, 0U, input, 1U,
				 console_output, BE_B7_CONSOLE_CAPACITY) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(be_b7_console_feed(&console, 0U, (const be_u8 *)0, 1U,
				 console_output, BE_B7_CONSOLE_CAPACITY) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(be_b7_console_feed(&console, 0U, input, 1U, (char *)0,
				 BE_B7_CONSOLE_CAPACITY) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(be_b7_console_flush(&console, 2U, console_output,
				  BE_B7_CONSOLE_CAPACITY) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(be_b7_console_flush(&console, 0U, (char *)0,
				  BE_B7_CONSOLE_CAPACITY) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(be_b7_console_flush(&console, 0U, console_output,
				  BE_B7_CONSOLE_CAPACITY - 1U) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(be_b7_console_flush((struct be_b7_console *)0, 0U,
				  console_output, BE_B7_CONSOLE_CAPACITY) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(memcmp(&copy, &console, sizeof(console)) == 0);
	console.length = 257U;
	CHECK(be_b7_console_feed(&console, 0U, input, 1U, console_output,
				 BE_B7_CONSOLE_CAPACITY) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(be_b7_console_flush(&console, 0U, console_output,
				  BE_B7_CONSOLE_CAPACITY) ==
	      BE_B7_CONSOLE_INVALID);
	CHECK(console.length == 257U);
	console.length = 0U;
	CHECK(be_b7_console_feed(&console, 0U, input, 0U, console_output,
				 BE_B7_CONSOLE_CAPACITY) == 0U);
}

/*
 * Two guests' output, fed in alternating pseudo-random chunks as their
 * DBCN calls arrive, never forms a mixed line: every written line holds one
 * guest's prefix and exactly one of that guest's lines, in order.
 */
#define TRANSCRIPT_BYTES	65536U

static char transcript[TRANSCRIPT_BYTES];

static void guest_text(unsigned int guest, char *text, be_u64 *length)
{
	be_u64 used = 0U;
	unsigned int line;
	unsigned int column;

	for (line = 0U; line < 40U; ++line) {
		unsigned int width = (line * 37U + guest * 11U) % 200U;

		used += (be_u64)sprintf(text + used, "G%u line %02u:", guest,
					line);
		for (column = 0U; column < width; ++column)
			text[used++] = (char)('a' + (column + line + guest) % 26U);
		if (line % 5U == 0U)
			text[used++] = '\r';
		text[used++] = '\n';
	}
	*length = used;
}

static void test_console_interleave(void)
{
	static char text[2][16384];
	struct be_b7_console consoles[2] = { { 0 }, { 0 } };
	be_u64 lengths[2];
	be_u64 offsets[2] = { 0U, 0U };
	be_u64 written = 0U;
	be_u64 seed = BE_U64_C(0x2545f4914f6cdd1d);
	unsigned int guest;
	unsigned int lines[2] = { 0U, 0U };
	char *line;
	char *next;

	SCENARIO();
	for (guest = 0U; guest < 2U; ++guest)
		guest_text(guest, text[guest], &lengths[guest]);
	while (offsets[0] < lengths[0] || offsets[1] < lengths[1]) {
		be_u64 chunk;
		be_u64 out;

		seed ^= seed << 13;
		seed ^= seed >> 7;
		seed ^= seed << 17;
		guest = (unsigned int)(seed >> 40) & 1U;
		if (offsets[guest] == lengths[guest])
			guest ^= 1U;
		chunk = 1U + (seed % BE_B7_DBCN_MAX_BYTES);
		if (chunk > lengths[guest] - offsets[guest])
			chunk = lengths[guest] - offsets[guest];
		out = be_b7_console_feed(&consoles[guest], guest,
					 (const be_u8 *)text[guest] +
						 offsets[guest],
					 chunk, console_output,
					 BE_B7_CONSOLE_CAPACITY);
		CHECK(out != BE_B7_CONSOLE_INVALID);
		CHECK(written + out < TRANSCRIPT_BYTES);
		memcpy(transcript + written, console_output, (size_t)out);
		written += out;
		offsets[guest] += chunk;
	}
	CHECK(consoles[0].length == 0U && consoles[1].length == 0U);
	transcript[written] = '\0';
	/* Parse the transcript back: one guest per line, lines in order. */
	for (line = transcript; *line != '\0'; line = next + 1) {
		char expected[64];
		be_u64 width;

		next = strchr(line, '\n');
		CHECK(next != (char *)0);
		*next = '\0';
		CHECK(strncmp(line, "BE_B7_G", 7U) == 0);
		guest = (unsigned int)(line[7] - '0');
		CHECK(guest < 2U && strncmp(line + 8, ": ", 2U) == 0);
		(void)sprintf(expected, "G%u line %02u:", guest,
			      lines[guest]);
		CHECK(strncmp(line + 10, expected, strlen(expected)) == 0);
		/* No other guest's text inside the line. */
		CHECK(strstr(line + 10, "BE_B7_G") == (char *)0);
		CHECK(strchr(line + 10, '\r') == (char *)0);
		width = (be_u64)strlen(line + 10) - strlen(expected);
		CHECK(width == (lines[guest] * 37U + guest * 11U) % 200U);
		++lines[guest];
	}
	CHECK(lines[0] == 40U && lines[1] == 40U);
}

/* The switch: vCPU records, the CSR set, SPP, and the readback compare. */
static void test_switch_record(void)
{
	static const char *const names[] = {
		"vsstatus", "vsie", "vstvec", "vsscratch", "vsepc", "vscause",
		"vstval", "vsatp", "vstimecmp", "scounteren", "senvcfg",
	};
	static const unsigned int bits[] = { 0U, 5U, 32U, 63U };
	struct be_b7_vcpu vcpu[2];
	struct be_b7_exit record;
	struct be_b7_exit saved;
	const be_u64 *words;
	be_u64 csr[BE_B7_VCSR_COUNT];
	be_u64 readback[BE_B7_VCSR_COUNT];
	be_u32 index;
	be_size slot;
	unsigned int bit;

	SCENARIO();
	/* The initial set: zero, but vsstatus.UXL = 2 and vstimecmp ~0. */
	memset(csr, 0xa5, sizeof(csr));
	be_b7_vcsr_initial(csr);
	for (index = 0U; index < BE_B7_VCSR_COUNT; ++index)
		CHECK(csr[index] == (index == BE_B7_VCSR_VSSTATUS ?
				     BE_U64_C(0x200000000) :
				     index == BE_B7_VCSR_VSTIMECMP ?
				     ALL_ONES : 0U));
	be_b7_vcsr_initial((be_u64 *)0);
	/* A first entry: Linux's boot protocol in VS mode, initial CSRs. */
	memset(vcpu, 0x5a, sizeof(vcpu));
	be_b7_vcpu_init(&vcpu[1], BE_B7_KERNEL_GPA, BE_B7_GUEST_HART,
			BE_B7_DTB_GPA);
	CHECK(vcpu[1].record.frame.sepc == BE_U64_C(0x80200000));
	CHECK(vcpu[1].record.frame.gpr[BE_R4_GPR_A0] == 0U);
	CHECK(vcpu[1].record.frame.gpr[BE_R4_GPR_A1] == BE_U64_C(0x83e00000));
	CHECK(vcpu[1].record.hstatus == 0x180U);
	CHECK(memcmp(vcpu[1].csr, csr, sizeof(csr)) == 0);
	words = (const be_u64 *)(const void *)&vcpu[1].record;
	for (slot = 0U; slot < sizeof(record) / sizeof(be_u64); ++slot)
		if (slot != BE_R4_GPR_A1 && slot != 36U && slot != 40U)
			CHECK(words[slot] == 0U);
	be_b7_vcpu_init((struct be_b7_vcpu *)0, 1U, 2U, 3U);
	/* Switch out of G0 at a slice that preempted VU code. */
	record = exit_with(STI, ECALL_PC);
	record.hstatus = BE_U64_C(0x200000080);
	saved = record;
	be_b7_vcpu_save(&vcpu[0], &record);
	CHECK(memcmp(&vcpu[0].record, &record, sizeof(record)) == 0);
	CHECK(memcmp(&record, &saved, sizeof(record)) == 0);
	/* The CSR set is the save helper's, not the record copy's. */
	words = (const be_u64 *)(const void *)vcpu[0].csr;
	for (index = 0U; index < BE_B7_VCSR_COUNT; ++index)
		CHECK(words[index] == BE_U64_C(0x5a5a5a5a5a5a5a5a));
	/* Switch into G1's first entry. */
	be_b7_vcpu_restore(&vcpu[1], &record);
	CHECK(memcmp(&record, &vcpu[1].record, sizeof(record)) == 0);
	CHECK(record.frame.sepc == BE_U64_C(0x80200000));
	CHECK(be_b7_record_spp(&record) == 0x100U);
	/* G1 exits at a wfi in VS mode; G0 resumes exactly as it left, in
	 * VU mode. */
	record.frame.scause = BE_B7_SCAUSE_VIRTUAL_INSTRUCTION;
	record.frame.stval = WFI;
	be_b7_vcpu_save(&vcpu[1], &record);
	be_b7_vcpu_restore(&vcpu[0], &record);
	CHECK(memcmp(&record, &saved, sizeof(record)) == 0);
	CHECK(be_b7_record_spp(&record) == 0U);
	be_b7_vcpu_restore(&vcpu[1], &record);
	CHECK(record.frame.stval == WFI && be_b7_record_spp(&record) == 0x100U);
	/* Absent arguments change nothing. */
	be_b7_vcpu_save((struct be_b7_vcpu *)0, &record);
	be_b7_vcpu_save(&vcpu[0], (const struct be_b7_exit *)0);
	be_b7_vcpu_restore((const struct be_b7_vcpu *)0, &record);
	be_b7_vcpu_restore(&vcpu[0], (struct be_b7_exit *)0);
	CHECK(record.frame.stval == WFI);
	CHECK(memcmp(&vcpu[0].record, &saved, sizeof(saved)) == 0);
	/* SPP follows SPVP alone. */
	for (bit = 0U; bit < 64U; ++bit) {
		record.hstatus = BE_U64_C(1) << bit;
		CHECK(be_b7_record_spp(&record) == (bit == 8U ? 0x100U : 0U));
		record.hstatus = ~(BE_U64_C(1) << bit);
		CHECK(be_b7_record_spp(&record) == (bit == 8U ? 0U : 0x100U));
	}
	CHECK(be_b7_record_spp((const struct be_b7_exit *)0) == 0U);
	/* The readback compare names the first CSR that differs. */
	memcpy(readback, csr, sizeof(csr));
	CHECK(be_b7_vcsr_mismatch(csr, readback) == BE_B7_VCSR_COUNT);
	for (index = 0U; index < BE_B7_VCSR_COUNT; ++index) {
		for (slot = 0U; slot < BE_ARRAY_SIZE(bits); ++slot) {
			memcpy(readback, csr, sizeof(csr));
			readback[index] ^= BE_U64_C(1) << bits[slot];
			CHECK(be_b7_vcsr_mismatch(csr, readback) == index);
			if (index + 1U < BE_B7_VCSR_COUNT) {
				readback[index + 1U] ^= 1U;
				CHECK(be_b7_vcsr_mismatch(csr, readback) ==
				      index);
			}
		}
	}
	CHECK(be_b7_vcsr_mismatch((const be_u64 *)0, readback) == 0U);
	CHECK(be_b7_vcsr_mismatch(csr, (const be_u64 *)0) == 0U);
	/* The names a switch DETAIL line prints. */
	CHECK(BE_ARRAY_SIZE(names) == BE_B7_VCSR_COUNT);
	for (index = 0U; index < BE_B7_VCSR_COUNT; ++index)
		CHECK(strcmp(be_b7_vcsr_name(index), names[index]) == 0);
	CHECK(strcmp(be_b7_vcsr_name(BE_B7_VCSR_COUNT), "invalid") == 0);
	CHECK(strcmp(be_b7_vcsr_name(99U), "invalid") == 0);
}

/* The HS slice and an idling wfi. */
static void test_wfi_slice(void)
{
	static const be_u64 other_tval[] = {
		0U, BE_U64_C(0xc0002573), BE_U64_C(0x10200073),
		BE_U64_C(0x12000073), BE_U64_C(0x10500072),
		BE_U64_C(0x10500077), BE_U64_C(0x10400073),
		BE_U64_C(0x110500073), WFI | (BE_U64_C(1) << 63), ALL_ONES,
	};
	struct be_b7_state state;
	struct be_b7_exit record;
	struct be_b7_result result;
	be_size index;
	unsigned int spvp;

	SCENARIO();
	/* The supervisor timer at V=1: a slice, from VS or VU, at any PC. */
	for (spvp = 0U; spvp < 2U; ++spvp) {
		state = fresh_state();
		record = exit_with(STI, ECALL_PC);
		if (spvp == 0U)
			record.hstatus &= ~BE_B7_HSTATUS_SPVP;
		CHECK(be_b7_handle_exit(&state, 0U, &window, &record,
					&result) == BE_B7_ACTION_SLICE);
		CHECK(result.resume_pc == ECALL_PC && result.error == 0 &&
		      result.value == 0U && result.failure == BE_B7_CLASS_NONE);
		CHECK(state.guest[0].counts.slice == 1U &&
		      state.guest[0].counts.exits == 1U &&
		      state.guest[0].counts.wfi == 0U &&
		      call_sum(&state.guest[0].counts) == 0U);
		CHECK(state.phase == BE_B7_PHASE_RUNNING &&
		      state.guest[0].phase == BE_B7_PHASE_RUNNING);
	}
	state = fresh_state();
	record = exit_with(STI, ALL_ONES);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_SLICE);
	CHECK(result.resume_pc == ALL_ONES);
	/* A VS-mode wfi idles; its resume PC steps past it. */
	state = fresh_state();
	record = exit_with(BE_B7_SCAUSE_VIRTUAL_INSTRUCTION, ECALL_PC);
	record.frame.stval = WFI;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_WFI);
	CHECK(result.resume_pc == ECALL_PC + 4U && result.error == 0 &&
	      result.failure == BE_B7_CLASS_NONE);
	CHECK(state.guest[0].counts.wfi == 1U &&
	      state.guest[0].counts.exits == 1U &&
	      state.guest[0].counts.slice == 0U &&
	      call_sum(&state.guest[0].counts) == 0U);
	/* A wfi at the top of the address space cannot step. */
	state = fresh_state();
	record.frame.sepc = ALL_ONES - 3U;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_RESUME);
	state = fresh_state();
	record.frame.sepc = ALL_ONES - 4U;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_WFI);
	CHECK(result.resume_pc == ALL_ONES);
	/* A VU-mode wfi is terminal. */
	state = fresh_state();
	record = exit_with(BE_B7_SCAUSE_VIRTUAL_INSTRUCTION, ECALL_PC);
	record.frame.stval = WFI;
	record.hstatus &= ~BE_B7_HSTATUS_SPVP;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_VIRTUAL_INSTRUCTION);
	CHECK(state.guest[0].counts.wfi == 0U);
	/* Any other stval is terminal, from VS or VU: rdcycle, sret,
	 * sfence.vma, one-bit neighbours of wfi, and wide values. */
	for (index = 0U; index < BE_ARRAY_SIZE(other_tval); ++index) {
		for (spvp = 0U; spvp < 2U; ++spvp) {
			state = fresh_state();
			record = exit_with(BE_B7_SCAUSE_VIRTUAL_INSTRUCTION,
					   ECALL_PC);
			record.frame.stval = other_tval[index];
			if (spvp == 0U)
				record.hstatus &= ~BE_B7_HSTATUS_SPVP;
			CHECK(be_b7_handle_exit(&state, 0U, &window, &record,
						&result) ==
			      BE_B7_ACTION_TERMINAL);
			CHECK(result.failure ==
			      BE_B7_CLASS_VIRTUAL_INSTRUCTION);
			CHECK(state.guest[0].counts.wfi == 0U);
		}
	}
	/* The wfi encoding as another cause's stval is that cause's. */
	state = fresh_state();
	record = exit_with(BE_B7_SCAUSE_ILLEGAL_INSTRUCTION, ECALL_PC);
	record.frame.stval = WFI;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_ILLEGAL_INSTRUCTION);
	/* Not from V=1: an exception, even for the timer or a wfi. */
	state = fresh_state();
	record = exit_with(STI, ECALL_PC);
	record.hstatus &= ~BE_B7_HSTATUS_SPV;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXCEPTION);
	/* Slices and wfi count against the ceiling and the budget. */
	state = (struct be_b7_state)BE_B7_STATE_INITIALIZER(
		2U, BE_B7_GUEST_TIME_BUDGET);
	state.entry_time = ENTRY_TIME;
	record = exit_with(STI, ECALL_PC);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_SLICE);
	record = exit_with(BE_B7_SCAUSE_VIRTUAL_INSTRUCTION, ECALL_PC);
	record.frame.stval = WFI;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_WFI);
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXIT_BUDGET);
	CHECK(state.guest[0].counts.exits == 3U);
	state = fresh_state();
	record = exit_with(STI, ECALL_PC);
	record.time = ENTRY_TIME + BE_B7_GUEST_TIME_BUDGET;
	CHECK(be_b7_handle_exit(&state, 0U, &window, &record, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_GUEST_TIMEOUT);
}

/* Each guest has its own counters, window, and phase; failure is shared. */
static void test_per_guest(void)
{
	struct be_b7_state state = fresh_state();
	struct be_b7_exit base = ecall(BE_B7_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b7_exit write = ecall(BE_B7_SBI_EID_DBCN, 0U, 16U,
					WINDOW_GPA + 0x1000U, 0U);
	struct be_b7_exit slice = exit_with(STI, ECALL_PC);
	struct be_b7_exit idle = exit_with(BE_B7_SCAUSE_VIRTUAL_INSTRUCTION,
					   ECALL_PC);
	struct be_b7_exit fault = exit_with(BE_B7_SCAUSE_LOAD_GUEST_PAGE_FAULT,
					    ECALL_PC);
	struct be_b7_result result;
	unsigned int guest;

	SCENARIO();
	idle.frame.stval = WFI;
	CHECK(be_b7_handle_exit(&state, 0U, &windows[0], &base, &result) ==
	      BE_B7_ACTION_RETURN);
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &slice, &result) ==
	      BE_B7_ACTION_SLICE);
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &slice, &result) ==
	      BE_B7_ACTION_SLICE);
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &idle, &result) ==
	      BE_B7_ACTION_WFI);
	/* DBCN reads the calling guest's own window. */
	CHECK(be_b7_handle_exit(&state, 0U, &windows[0], &write, &result) ==
	      BE_B7_ACTION_CONSOLE_WRITE);
	CHECK(result.source_pa == WINDOW_HPA + 0x1000U && result.length == 16U);
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &write, &result) ==
	      BE_B7_ACTION_CONSOLE_WRITE);
	CHECK(result.source_pa == WINDOW_G1_HPA + 0x1000U);
	CHECK(state.guest[0].counts.exits == 2U &&
	      state.guest[0].counts.base == 1U &&
	      state.guest[0].counts.dbcn_write == 1U &&
	      state.guest[0].counts.slice == 0U &&
	      state.guest[0].counts.wfi == 0U);
	CHECK(state.guest[1].counts.exits == 4U &&
	      state.guest[1].counts.slice == 2U &&
	      state.guest[1].counts.wfi == 1U &&
	      state.guest[1].counts.dbcn_write == 1U &&
	      state.guest[1].counts.base == 0U);
	for (guest = 0U; guest < 2U; ++guest)
		CHECK(state.guest[guest].counts.exits ==
		      be_b7_counts_sbi(&state.guest[guest].counts) +
			      state.guest[guest].counts.wfi +
			      state.guest[guest].counts.slice);
	CHECK(be_b7_counts_sbi((const struct be_b7_counts *)0) == 0U);
	/* A guest index other than 0 or 1 fails the run closed. */
	CHECK(be_b7_handle_exit(&state, 2U, &windows[1], &base, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXCEPTION);
	CHECK(state.phase == BE_B7_PHASE_FAILED);
	/* One guest's terminal exit fails the whole run (Q8): the other
	 * guest's next exit is terminal with the first class. */
	state = fresh_state();
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &fault, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_GUEST_PAGE_FAULT);
	CHECK(be_b7_handle_exit(&state, 0U, &windows[0], &base, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_GUEST_PAGE_FAULT);
	CHECK(state.guest[0].counts.exits == 0U);
	/* The budget is the run's: G1's late exit times out too. */
	state = fresh_state();
	slice.time = ENTRY_TIME + BE_B7_GUEST_TIME_BUDGET + 1U;
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &slice, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_GUEST_TIMEOUT);
	/* G0's ceiling does not limit G1. */
	state = (struct be_b7_state)BE_B7_STATE_INITIALIZER(
		1U, BE_B7_GUEST_TIME_BUDGET);
	state.entry_time = ENTRY_TIME;
	CHECK(be_b7_handle_exit(&state, 0U, &windows[0], &base, &result) ==
	      BE_B7_ACTION_RETURN);
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &base, &result) ==
	      BE_B7_ACTION_RETURN);
	CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &base, &result) ==
	      BE_B7_ACTION_TERMINAL);
	CHECK(result.failure == BE_B7_CLASS_EXIT_BUDGET);
	CHECK(state.guest[1].counts.exits == 2U &&
	      state.guest[0].counts.exits == 1U);
}

static int line_is(const struct be_b7_line *line, const char *text)
{
	return line->overflow == 0U && line->length == strlen(text) &&
	       memcmp(line->text, text, strlen(text)) == 0;
}

static void test_line_builder(void)
{
	static const struct {
		be_u64 value;
		const char *hex;
		const char *decimal;
	} values[] = {
		{ 0U, "0x0", "0" },
		{ 1U, "0x1", "1" },
		{ 0x2U, "0x2", "2" },
		{ 10U, "0xa", "10" },
		{ 32U, "0x20", "32" },
		{ 0x40U, "0x40", "64" },
		{ 139U, "0x8b", "139" },
		{ 0x180U, "0x180", "384" },
		{ 0x1000U, "0x1000", "4096" },
		{ 0xb15dU, "0xb15d", "45405" },
		{ 0x100000U, "0x100000", "1048576" },
		{ 0x1af628U, "0x1af628", "1766952" },
		{ 0x4000000U, "0x4000000", "67108864" },
		{ 0x80200000U, "0x80200000", "2149580800" },
		{ BE_U64_C(0x102034000), "0x102034000", "4328734720" },
		{ BE_U64_C(0x8000000000102034), "0x8000000000102034",
		  "9223372036855832628" },
		{ BE_U64_C(0x8000000000000000), "0x8000000000000000",
		  "9223372036854775808" },
		{ ALL_ONES, "0xffffffffffffffff", "18446744073709551615" },
	};
	struct be_b7_line line;
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(values); ++index) {
		be_b7_line_reset(&line);
		be_b7_line_hex(&line, values[index].value);
		CHECK(line_is(&line, values[index].hex));
		be_b7_line_reset(&line);
		be_b7_line_decimal(&line, values[index].value);
		CHECK(line_is(&line, values[index].decimal));
	}

	/* Plan markers composed from fixed text and values. */
	be_b7_line_reset(&line);
	be_b7_line_text(&line, "BE_B7:01 GSTAGE_BUILT_REWALKED guest=");
	be_b7_line_decimal(&line, 1U);
	be_b7_line_text(&line, " gpa=");
	be_b7_line_hex(&line, WINDOW_GPA);
	be_b7_line_text(&line, " hpa=");
	be_b7_line_hex(&line, WINDOW_G1_HPA);
	be_b7_line_text(&line, " size=");
	be_b7_line_hex(&line, WINDOW_BYTES);
	be_b7_line_text(&line, " leaves=");
	be_b7_line_decimal(&line, 32U);
	be_b7_line_text(&line, " root=");
	be_b7_line_hex(&line, BE_B7_G1_ROOT_HPA);
	be_b7_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_B7:01 GSTAGE_BUILT_REWALKED guest=1 "
		      "gpa=0x80000000 hpa=0x114000000 size=0x4000000 "
		      "leaves=32 root=0x10203c000\n"));
	be_b7_line_reset(&line);
	be_b7_line_text(&line, "BE_B7:02 HGATP_INSTALLED g1=");
	be_b7_line_hex(&line, BE_B7_G1_HGATP);
	be_b7_line_text(&line, " g0=");
	be_b7_line_hex(&line, BE_B7_G0_HGATP);
	be_b7_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_B7:02 HGATP_INSTALLED g1=0x800020000010203c "
		      "g0=0x8000100000102034\n"));
	be_b7_line_reset(&line);
	be_b7_line_text(&line,
			"BE_B7:04 GUEST_CONTROLS_CHECKED hstatus_controls=");
	be_b7_line_hex(&line, 0x200180U);
	be_b7_line_text(&line, " hedeleg=");
	be_b7_line_hex(&line, 0xb15dU);
	be_b7_line_text(&line, " hideleg=");
	be_b7_line_hex(&line, 0x40U);
	be_b7_line_text(&line, " hcounteren=");
	be_b7_line_hex(&line, 0x2U);
	be_b7_line_text(&line, " sie=");
	be_b7_line_hex(&line, 0x20U);
	be_b7_line_text(&line, " fs=");
	be_b7_line_hex(&line, 0U);
	be_b7_line_text(&line, " vs=");
	be_b7_line_hex(&line, 0U);
	be_b7_line_text(&line, " vstimecmp=");
	be_b7_line_hex(&line, ALL_ONES);
	be_b7_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_B7:04 GUEST_CONTROLS_CHECKED "
		      "hstatus_controls=0x200180 hedeleg=0xb15d hideleg=0x40 "
		      "hcounteren=0x2 sie=0x20 fs=0x0 vs=0x0 "
		      "vstimecmp=0xffffffffffffffff\n"));
	be_b7_line_reset(&line);
	be_b7_line_text(&line, "BE_B7:07 SCHEDULER_ARMED guests=");
	be_b7_line_decimal(&line, BE_B7_GUESTS);
	be_b7_line_text(&line, " slice_ticks=");
	be_b7_line_hex(&line, BE_B7_SLICE_TICKS);
	be_b7_line_text(&line, " first=");
	be_b7_line_decimal(&line, 0U);
	be_b7_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_B7:07 SCHEDULER_ARMED guests=2 "
		      "slice_ticks=0x3a980 first=0\n"));
	/* The worst-case DETAIL lines fit. */
	be_b7_line_reset(&line);
	be_b7_line_text(&line, "BE_B7:DETAIL guest=");
	be_b7_line_decimal(&line, 1U);
	be_b7_line_text(&line, " cause=");
	be_b7_line_hex(&line, ALL_ONES);
	for (index = 0U; index < 4U; ++index) {
		be_b7_line_text(&line, " htinst=");
		be_b7_line_hex(&line, ALL_ONES);
	}
	be_b7_line_text(&line, " spvp=");
	be_b7_line_decimal(&line, 1U);
	be_b7_line_text(&line, " vsatp=");
	be_b7_line_hex(&line, ALL_ONES);
	be_b7_line_text(&line, " exits=");
	be_b7_line_decimal(&line, ALL_ONES);
	be_b7_line_text(&line, "\n");
	CHECK(line.overflow == 0U && line.length < 230U);
	be_b7_line_reset(&line);
	be_b7_line_text(&line, "BE_B7:DETAIL switch guest=");
	be_b7_line_decimal(&line, 1U);
	be_b7_line_text(&line, " register=");
	be_b7_line_text(&line, be_b7_vcsr_name(BE_B7_VCSR_SCOUNTEREN));
	be_b7_line_text(&line, " wanted=");
	be_b7_line_hex(&line, ALL_ONES);
	be_b7_line_text(&line, " readback=");
	be_b7_line_hex(&line, ALL_ONES);
	be_b7_line_text(&line, "\n");
	CHECK(line.overflow == 0U && line.length < 120U);
	/* The longest count lines fit: every count at its ceiling's bound
	 * (a guest's exits are at most 2^20 + 1, a run's switches and waits
	 * at most twice that), every tick field all ones. */
	be_b7_line_reset(&line);
	be_b7_line_text(&line, "BE_B7:09 GUEST_SHUTDOWN guest=");
	be_b7_line_decimal(&line, 1U);
	for (index = 0U; index < 11U; ++index) {
		be_b7_line_text(&line, " dbcn_write=");
		be_b7_line_decimal(&line, BE_B7_EXIT_CEILING + 1U);
	}
	be_b7_line_text(&line, " ticks=");
	be_b7_line_hex(&line, ALL_ONES);
	be_b7_line_text(&line, "\n");
	CHECK(line.overflow == 0U && line.length < BE_B7_LINE_CAPACITY);
	be_b7_line_reset(&line);
	be_b7_line_text(&line, "BE_B7:10 RUN_COMPLETE switches=");
	for (index = 0U; index < 5U; ++index) {
		be_b7_line_decimal(&line, 2U * BE_B7_EXIT_CEILING + 2U);
		be_b7_line_text(&line, " slice_switches=");
	}
	be_b7_line_hex(&line, ALL_ONES);
	be_b7_line_text(&line, " ticks=");
	be_b7_line_hex(&line, ALL_ONES);
	be_b7_line_text(&line, "\n");
	CHECK(line.overflow == 0U && line.length < BE_B7_LINE_CAPACITY);

	/* Overflow is sticky and makes the line unusable. */
	be_b7_line_reset(&line);
	for (index = 0U; index < BE_B7_LINE_CAPACITY; ++index)
		be_b7_line_text(&line, "x");
	CHECK(line.length == BE_B7_LINE_CAPACITY && line.overflow == 0U);
	be_b7_line_text(&line, "y");
	CHECK(line.overflow == 1U);
	CHECK(line.length == BE_B7_LINE_CAPACITY);
	be_b7_line_reset(&line);
	CHECK(line.length == 0U && line.overflow == 0U);
	be_b7_line_text(&line, (const char *)0);
	CHECK(line.overflow == 1U);
	be_b7_line_reset(&line);
	for (index = 0U; index < 17U; ++index)
		be_b7_line_hex(&line, ALL_ONES);
	CHECK(line.length == 17U * 18U && line.overflow == 0U);
	be_b7_line_hex(&line, ALL_ONES);
	CHECK(line.overflow == 1U);
	CHECK(line.length == BE_B7_LINE_CAPACITY);
	be_b7_line_reset((struct be_b7_line *)0);
	be_b7_line_text((struct be_b7_line *)0, "x");
	be_b7_line_hex((struct be_b7_line *)0, 1U);
	be_b7_line_decimal((struct be_b7_line *)0, 1U);
}

/* The guest a replay runs as, with its own window. */
static be_u32 replay_guest;

/* One SBI call of a replay; checks the decision and, for returns, the
 * values the guest receives. */
static void replay(struct be_b7_state *state, be_u64 eid, be_u64 fid,
		   be_u64 argument0, be_u64 argument1,
		   enum be_b7_action action, long error, be_u64 value)
{
	struct be_b7_exit record = ecall(eid, fid, argument0, argument1, 0U);
	struct be_b7_result result;
	be_u32 guest = replay_guest;

	record.time = ENTRY_TIME +
		      state->guest[guest].counts.exits * BE_U64_C(0x40000);
	CHECK(be_b7_handle_exit(state, guest, &windows[guest], &record,
				&result) == action);
	CHECK(result.error == error && result.value == value);
	if (action == BE_B7_ACTION_CONSOLE_WRITE)
		CHECK(result.source_pa ==
		      argument1 - WINDOW_GPA + windows[guest].hpa_base);
	if (action != BE_B7_ACTION_TERMINAL)
		CHECK(state->phase == BE_B7_PHASE_RUNNING);
	CHECK(state->guest[guest].phase == (action == BE_B7_ACTION_STOP ?
					    BE_B7_PHASE_STOPPED :
					    BE_B7_PHASE_RUNNING));
}

/* One idling wfi or slice exit of a replay. */
static void replay_exit(struct be_b7_state *state, be_u64 scause,
			enum be_b7_action action)
{
	struct be_b7_exit record = exit_with(scause, ECALL_PC);
	struct be_b7_result result;
	be_u32 guest = replay_guest;

	record.frame.stval = WFI;
	record.time = ENTRY_TIME +
		      state->guest[guest].counts.exits * BE_U64_C(0x40000);
	CHECK(be_b7_handle_exit(state, guest, &windows[guest], &record,
				&result) == action);
}

static void replay_write(struct be_b7_state *state, be_u64 call)
{
	static const be_u64 lengths[] = { 57U, 120U, 16U, 16U, 300U, 4U, 16U,
					  200U };
	be_u64 length = lengths[call % BE_ARRAY_SIZE(lengths)];
	be_u64 gpa = BE_U64_C(0x81234000) + (call % 8U) * 0x100U;

	replay(state, BE_B7_SBI_EID_DBCN, 0U, length, gpa,
	       BE_B7_ACTION_CONSOLE_WRITE, BE_B7_SBI_SUCCESS,
	       length < 256U ? length : 256U);
}

/* The Base calls a v7.2 uniprocessor boot makes before its first write. */
static void replay_base(struct be_b7_state *state)
{
	replay(state, BE_B7_SBI_EID_BASE, 0U, 0U, 0U, BE_B7_ACTION_RETURN, 0,
	       0x2000000U);
	replay(state, BE_B7_SBI_EID_BASE, 1U, 0U, 0U, BE_B7_ACTION_RETURN, 0,
	       0x4245U);
	replay(state, BE_B7_SBI_EID_BASE, 2U, 0U, 0U, BE_B7_ACTION_RETURN, 0,
	       3U);
	replay(state, BE_B7_SBI_EID_BASE, 3U, BE_B7_SBI_EID_TIME, 0U,
	       BE_B7_ACTION_RETURN, 0, 1U);
	replay(state, BE_B7_SBI_EID_BASE, 3U, EID_IPI, 0U,
	       BE_B7_ACTION_RETURN, 0, 0U);
	replay(state, BE_B7_SBI_EID_BASE, 3U, EID_RFENCE, 0U,
	       BE_B7_ACTION_RETURN, 0, 0U);
	replay(state, BE_B7_SBI_EID_BASE, 3U, BE_B7_SBI_EID_SRST, 0U,
	       BE_B7_ACTION_RETURN, 0, 1U);
	replay(state, BE_B7_SBI_EID_BASE, 3U, BE_B7_SBI_EID_DBCN, 0U,
	       BE_B7_ACTION_RETURN, 0, 1U);
}

/* The B6 research reference boot's 138 calls before its shutdown. */
static void replay_boot(struct be_b7_state *state)
{
	be_u64 call;
	be_u64 writes = 0U;
	unsigned int round;

	replay_base(state);
	for (call = 0U; call < 12U; ++call)
		replay_write(state, writes++);
	for (round = 0U; round < 2U; ++round) {
		replay(state, BE_B7_SBI_EID_BASE, 4U, 0U, 0U,
		       BE_B7_ACTION_RETURN, 0, 0U);
		replay(state, BE_B7_SBI_EID_BASE, 5U, 0U, 0U,
		       BE_B7_ACTION_RETURN, 0, 0U);
		replay(state, BE_B7_SBI_EID_BASE, 6U, 0U, 0U,
		       BE_B7_ACTION_RETURN, 0, 0U);
	}
	for (call = 0U; call < 45U; ++call)
		replay_write(state, writes++);
	/* From call 72, hvc polls for input between its writes. */
	for (call = 0U; call < 35U; ++call) {
		replay(state, BE_B7_SBI_EID_DBCN, 1U, 16U,
		       BE_U64_C(0x81fff000), BE_B7_ACTION_RETURN,
		       BE_B7_SBI_ERR_DENIED, 0U);
		if (call < 32U)
			replay_write(state, writes++);
	}
}

/*
 * The B6 research reference boot's 139 SBI calls (B6 platform research
 * section 1c), for each guest in turn on one run: 3 Base IDs; probes for
 * TIME, IPI, RFENCE, SRST, and DBCN answered 1, 0, 0, 1, 1; 6 machine-ID
 * reads; 89 DBCN writes; 35 DBCN reads denied with -4; and one SRST
 * shutdown, which stops only that guest. The Base answers are B7's.
 */
static void test_census(void)
{
	struct be_b7_state state = fresh_state();
	be_u64 call;
	unsigned int guest;

	SCENARIO();
	for (guest = 0U; guest < 2U; ++guest) {
		replay_guest = guest;
		replay_boot(&state);
		CHECK(state.guest[guest].counts.exits == 138U);
		replay(&state, BE_B7_SBI_EID_SRST, 0U, 0U, 0U,
		       BE_B7_ACTION_STOP, 0, 0U);
		CHECK(state.guest[guest].phase == BE_B7_PHASE_STOPPED);
		CHECK(state.phase == BE_B7_PHASE_RUNNING);
		CHECK(state.guest[guest].counts.exits == 139U);
		CHECK(state.guest[guest].counts.base == 14U);
		CHECK(state.guest[guest].counts.time == 0U);
		CHECK(state.guest[guest].counts.dbcn_write == 89U);
		CHECK(state.guest[guest].counts.dbcn_read == 35U);
		CHECK(state.guest[guest].counts.dbcn_byte == 0U);
		CHECK(state.guest[guest].counts.srst == 1U);
		CHECK(state.guest[guest].counts.refused == 0U);
		CHECK(call_sum(&state.guest[guest].counts) ==
		      state.guest[guest].counts.exits);
		CHECK(state.guest[guest].counts.exits <= BE_B7_EXIT_CEILING);
	}
	/* With the exit-budget variant's ceiling a boot stops at 65. */
	state = (struct be_b7_state)BE_B7_STATE_INITIALIZER(
		BE_B7_VARIANT_EXIT_CEILING, BE_B7_GUEST_TIME_BUDGET);
	state.entry_time = ENTRY_TIME;
	replay_guest = 0U;
	replay_base(&state);
	for (call = 0U; call < 56U; ++call)
		replay_write(&state, call);
	CHECK(state.guest[0].counts.exits == 64U &&
	      state.phase == BE_B7_PHASE_RUNNING);
	replay(&state, BE_B7_SBI_EID_DBCN, 0U, 16U, BE_U64_C(0x81234000),
	       BE_B7_ACTION_TERMINAL, 0, 0U);
	CHECK(state.failure == BE_B7_CLASS_EXIT_BUDGET);
	CHECK(state.guest[0].counts.exits == 65U);
}

/*
 * Two guests at once: their boots interleaved call by call, with each
 * guest's idling wfi and slice exits between, then both shutdowns. Every
 * exit lands in its own guest's counts, and each guest's exits are its
 * SBI calls, wfi, and slices.
 */
static void test_census_two_guests(void)
{
	struct be_b7_state state = fresh_state();
	be_u64 call;
	unsigned int guest;

	SCENARIO();
	for (call = 0U; call < 40U; ++call) {
		for (guest = 0U; guest < 2U; ++guest) {
			replay_guest = guest;
			if (call < 8U && guest == 0U)
				replay_base(&state);
			replay_write(&state, call);
			if ((call + guest) % 3U == 0U)
				replay_exit(&state,
					    BE_B7_SCAUSE_VIRTUAL_INSTRUCTION,
					    BE_B7_ACTION_WFI);
			if ((call + guest) % 5U == 0U)
				replay_exit(&state, STI, BE_B7_ACTION_SLICE);
		}
	}
	replay_guest = 1U;
	replay(&state, BE_B7_SBI_EID_SRST, 0U, 0U, 0U, BE_B7_ACTION_STOP, 0,
	       0U);
	/* G0 runs on alone after G1 stopped. */
	replay_guest = 0U;
	replay_exit(&state, STI, BE_B7_ACTION_SLICE);
	replay(&state, BE_B7_SBI_EID_SRST, 0U, 0U, 0U, BE_B7_ACTION_STOP, 0,
	       0U);
	CHECK(state.phase == BE_B7_PHASE_RUNNING);
	CHECK(state.guest[0].counts.base == 64U &&
	      state.guest[1].counts.base == 0U);
	CHECK(state.guest[0].counts.dbcn_write == 40U &&
	      state.guest[1].counts.dbcn_write == 40U);
	CHECK(state.guest[0].counts.wfi == 14U &&
	      state.guest[1].counts.wfi == 13U);
	CHECK(state.guest[0].counts.slice == 9U &&
	      state.guest[1].counts.slice == 8U);
	CHECK(state.guest[0].counts.srst == 1U &&
	      state.guest[1].counts.srst == 1U);
	for (guest = 0U; guest < 2U; ++guest)
		CHECK(state.guest[guest].counts.exits ==
		      be_b7_counts_sbi(&state.guest[guest].counts) +
			      state.guest[guest].counts.wfi +
			      state.guest[guest].counts.slice);
	CHECK(state.guest[0].counts.exits == 64U + 40U + 14U + 9U + 1U);
	CHECK(state.guest[1].counts.exits == 40U + 13U + 8U + 1U);
}

/* The sbi-time variant: no sstc in the DT, so Linux arms through TIME. */
static void test_census_sbi_time(void)
{
	struct be_b7_state state = fresh_state();
	be_u64 call;

	SCENARIO();
	replay_guest = 1U;
	replay_base(&state);
	for (call = 0U; call < 10U; ++call)
		replay_write(&state, call);
	for (call = 0U; call < 20U; ++call) {
		be_u64 deadline = (call & 1U) ? ALL_ONES :
			ENTRY_TIME + (call + 1U) * BE_U64_C(96000);
		struct be_b7_exit record = ecall(BE_B7_SBI_EID_TIME, 0U,
					       deadline, 0U, 0U);
		struct be_b7_result result;

		record.time = ENTRY_TIME + call * BE_U64_C(48000);
		CHECK(be_b7_handle_exit(&state, 1U, &windows[1], &record,
					&result) == BE_B7_ACTION_SET_TIMER);
		CHECK(result.timer == deadline && result.error == 0 &&
		      result.value == 0U);
	}
	replay(&state, BE_B7_SBI_EID_SRST, 0U, 0U, 0U, BE_B7_ACTION_STOP, 0,
	       0U);
	CHECK(state.guest[1].counts.time == 20U &&
	      state.guest[1].counts.base == 8U);
	CHECK(state.guest[1].counts.dbcn_write == 10U &&
	      state.guest[1].counts.srst == 1U);
	CHECK(state.guest[1].counts.exits == 39U &&
	      call_sum(&state.guest[1].counts) ==
		      state.guest[1].counts.exits);
	CHECK(state.guest[0].counts.exits == 0U);
}

static void print_count(const char *label, unsigned long value)
{
	printf("%s%lu\n", label, value);
}

int main(void)
{
	build_window();
	test_constants();
	test_class_names();
	test_controls();
	test_classify();
	test_window();
	test_base();
	test_unsupported();
	test_time();
	test_dbcn_window();
	test_dbcn_refusals();
	test_dbcn_other();
	test_srst_grid();
	test_after_shutdown();
	test_exit_ceiling();
	test_time_budget();
	test_terminal_exits();
	test_frame_integrity();
	test_apply_return();
	test_entry_frame();
	test_wfi_slice();
	test_per_guest();
	test_switch_record();
	test_console();
	test_console_interleave();
	test_line_builder();
	test_census();
	test_census_two_guests();
	test_census_sbi_time();

	puts("BE_B7_CHECK: PASS");
	print_count("BE_B7_CHECK: scenarios=", scenarios);
	print_count("BE_B7_CHECK: assertions=", assertions);
	return 0;
}
