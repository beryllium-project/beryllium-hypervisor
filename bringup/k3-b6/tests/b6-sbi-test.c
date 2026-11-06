// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the K3 B6 guest SBI core: every row of the
 *          plan's SBI table, the DBCN range check at the window's edges and
 *          leaf boundaries, the SRST type and reason grid with terminal
 *          reboots, TIME values, exit classes, the exit ceiling and the
 *          guest-time budget, the per-class counters, the frame return and
 *          the first-entry frame, the guest controls, the tagged console
 *          with its CR drop and byte filter, the monitor line builder, and a
 *          replay of the research reference boot's SBI call census.
 * Trust:   host evidence only. No CSR, guest entry, QEMU, or hardware
 *          behaviour is exercised. The window comes from the B6 G-stage
 *          builder and walker, run in host memory.
 * Scope:   B6 only (planning/k3-b6-plan.md).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "b6.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_B6_CHECK: assertion failed: %s:%d: %s\n", \
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
#define WINDOW_BYTES		(64U * MIB)
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

static be_u8 pool[BE_B6_GSTAGE_POOL_BYTES];
static struct be_b6_gstage_map window;

static void build_window(void)
{
	struct be_b6_gstage_desc desc = { BE_B6_GUEST_GPA, BE_B6_GUEST_HPA,
					  BE_B6_GUEST_BYTES, BE_B6_POOL_HPA };

	CHECK(be_b6_gstage_build(&desc, pool, sizeof(pool)) ==
	      BE_B6_GSTAGE_OK);
	CHECK(be_b6_gstage_walk(&desc, pool, sizeof(pool), &window) ==
	      BE_B6_GSTAGE_OK);
}

static struct be_b6_state fresh_state(void)
{
	struct be_b6_state state = BE_B6_STATE_INITIALIZER(
		BE_B6_EXIT_CEILING, BE_B6_GUEST_TIME_BUDGET);

	state.entry_time = ENTRY_TIME;
	return state;
}

static struct be_b6_exit exit_with(be_u64 scause, be_u64 sepc)
{
	struct be_b6_exit record;
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

static struct be_b6_exit ecall(be_u64 eid, be_u64 fid, be_u64 argument0,
			       be_u64 argument1, be_u64 argument2)
{
	struct be_b6_exit record = exit_with(BE_B6_SCAUSE_VS_ECALL, ECALL_PC);

	record.frame.gpr[BE_R4_GPR_A7] = eid;
	record.frame.gpr[BE_R4_GPR_A6] = fid;
	record.frame.gpr[BE_R4_GPR_A0] = argument0;
	record.frame.gpr[BE_R4_GPR_A1] = argument1;
	record.frame.gpr[BE_B6_GPR_A2] = argument2;
	return record;
}

static be_u64 call_sum(const struct be_b6_counts *counts)
{
	return counts->base + counts->time + counts->dbcn_write +
	       counts->dbcn_read + counts->dbcn_byte + counts->srst +
	       counts->refused;
}

/* One exit on a fresh running state; checks the generic ecall properties. */
static struct be_b6_result decide(const struct be_b6_exit *record)
{
	struct be_b6_state state = fresh_state();
	struct be_b6_result result;

	CHECK(be_b6_handle_exit(&state, &window, record, &result) ==
	      result.action);
	CHECK(state.counts.exits == 1U);
	if (result.action != BE_B6_ACTION_TERMINAL) {
		CHECK(result.resume_pc == record->frame.sepc + 4U);
		CHECK(call_sum(&state.counts) == 1U);
	}
	if (result.action == BE_B6_ACTION_RETURN ||
	    result.action == BE_B6_ACTION_CONSOLE_WRITE ||
	    result.action == BE_B6_ACTION_CONSOLE_BYTE ||
	    result.action == BE_B6_ACTION_SET_TIMER)
		CHECK(state.phase == BE_B6_PHASE_RUNNING);
	if (result.error == BE_B6_SBI_ERR_NOT_SUPPORTED ||
	    result.error == BE_B6_SBI_ERR_INVALID_PARAM)
		CHECK(state.counts.refused == 1U);
	return result;
}

static void check_return(be_u64 eid, be_u64 fid, be_u64 argument0,
			 be_u64 argument1, be_u64 argument2, long error,
			 be_u64 value)
{
	struct be_b6_exit record = ecall(eid, fid, argument0, argument1,
				       argument2);
	struct be_b6_result result = decide(&record);

	CHECK(result.action == BE_B6_ACTION_RETURN);
	CHECK(result.error == error);
	CHECK(result.value == value);
	CHECK(result.failure == BE_B6_CLASS_NONE);
}

static void check_unsupported(be_u64 eid, be_u64 fid)
{
	check_return(eid, fid, 0U, 0U, 0U, BE_B6_SBI_ERR_NOT_SUPPORTED, 0U);
	check_return(eid, fid, ALL_ONES, ALL_ONES, ALL_ONES,
		     BE_B6_SBI_ERR_NOT_SUPPORTED, 0U);
}

static void check_dbcn_write(be_u64 length, be_u64 gpa, be_u64 high,
			     be_u64 expected_pa, be_u64 expected_length)
{
	struct be_b6_exit record = ecall(BE_B6_SBI_EID_DBCN,
				       BE_B6_SBI_DBCN_WRITE, length, gpa,
				       high);
	struct be_b6_result result = decide(&record);

	CHECK(result.action == BE_B6_ACTION_CONSOLE_WRITE);
	CHECK(result.error == BE_B6_SBI_SUCCESS);
	CHECK(result.source_pa == expected_pa);
	CHECK(result.length == expected_length);
	CHECK(result.value == expected_length);
}

static void check_dbcn_refused(be_u64 length, be_u64 gpa, be_u64 high)
{
	check_return(BE_B6_SBI_EID_DBCN, BE_B6_SBI_DBCN_WRITE, length, gpa,
		     high, BE_B6_SBI_ERR_INVALID_PARAM, 0U);
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(BE_B6_SBI_EID_BASE == 0x10U);
	CHECK(BE_B6_SBI_EID_TIME == 0x54494d45U);
	CHECK(BE_B6_SBI_EID_DBCN == 0x4442434eU);
	CHECK(BE_B6_SBI_EID_SRST == 0x53525354U);
	CHECK(BE_B6_SBI_SPEC_VERSION == 0x2000000U);
	CHECK(BE_B6_SBI_IMPL_ID == ((be_u64)'B' << 8 | (be_u64)'E'));
	CHECK(BE_B6_SBI_IMPL_VERSION == 2U);
	CHECK(BE_B6_EXIT_CEILING == BE_U64_C(1) << 20);
	CHECK(BE_B6_GUEST_TIME_BUDGET == BE_U64_C(1) << 32);
	CHECK(BE_B6_VARIANT_EXIT_CEILING == 64U);
	CHECK(BE_B6_VARIANT_GUEST_TIME_BUDGET == BE_U64_C(1) << 20);
	CHECK(BE_B6_RUN_EXIT_CEILING == BE_B6_EXIT_CEILING);
	CHECK(BE_B6_RUN_GUEST_TIME_BUDGET == BE_B6_GUEST_TIME_BUDGET);
	CHECK(BE_B6_DBCN_MAX_BYTES == 256U);
	CHECK(strcmp(BE_B6_GUEST_PREFIX, "BE_B6_GUEST: ") == 0);
	CHECK(strlen(BE_B6_GUEST_PREFIX) == BE_B6_GUEST_PREFIX_LENGTH);
	CHECK(BE_B6_TAGGED_CAPACITY == 3584U);
	CHECK(BE_B6_TAGGED_CAPACITY <= BE_PAGE_SIZE);
	CHECK(BE_B6_GPR_A2 == 11U);
	CHECK(BE_R4_GPR_A0 == 9U && BE_R4_GPR_A1 == 10U);
	CHECK(BE_R4_GPR_A6 == 15U && BE_R4_GPR_A7 == 16U);
	CHECK(sizeof(struct be_r4_frame) == 320U);
	CHECK(sizeof(struct be_b6_exit) == 352U);
	CHECK(__builtin_offsetof(struct be_b6_exit, hstatus) == 320U);
	CHECK(__builtin_offsetof(struct be_b6_exit, htinst) == 328U);
	CHECK(__builtin_offsetof(struct be_b6_exit, vsatp) == 336U);
	CHECK(__builtin_offsetof(struct be_b6_exit, time) == 344U);
	CHECK(sizeof(struct be_b6_counts) == 8U * sizeof(be_u64));
}

static void test_class_names(void)
{
	static const char *const names[] = {
		"none", "boot", "gstage", "sstc", "controls", "payload",
		"interrupt", "guest-page-fault", "virtual-instruction",
		"access-fault", "illegal-instruction", "exception",
		"exit-budget", "guest-timeout", "resume", "console",
		"guest-failure", "guest-reboot", "shutdown-returned",
	};
	unsigned int index;

	SCENARIO();
	CHECK(BE_ARRAY_SIZE(names) == (be_size)BE_B6_CLASS_COUNT);
	for (index = 0U; index < BE_ARRAY_SIZE(names); ++index)
		CHECK(strcmp(be_b6_class_name((enum be_b6_class)index),
			     names[index]) == 0);
	CHECK(strcmp(be_b6_class_name(BE_B6_CLASS_COUNT), "invalid") == 0);
	CHECK(strcmp(be_b6_class_name((enum be_b6_class)99), "invalid") == 0);
}

static struct be_b6_controls armed_controls(void)
{
	return (struct be_b6_controls) {
		.hip = 0U,
		.hstatus = BE_U64_C(0x200000180),
		.hedeleg = 0xb15dU,
		.hideleg = 0x40U,
		.hie = 0U,
		.hvip = 0U,
		.hcounteren = 0x2U,
		.htimedelta = 0U,
		.henvcfg = BE_U64_C(0x8000000000000000),
		.hgeie = 0U,
		.vstimecmp = ALL_ONES,
		.sie = 0U,
		.sstatus = BE_U64_C(0x200000000),
		.hgatp = BE_U64_C(0x8000000000102034),
		.vsatp = 0U,
		.sscratch = BE_U64_C(0x102027000),
	};
}

static int armed_valid(const struct be_b6_controls *controls)
{
	return be_b6_controls_valid(controls, BE_B6_HGATP,
				    BE_U64_C(0x102027000));
}

static void test_controls(void)
{
	struct be_b6_controls controls = armed_controls();
	be_u64 *fields = (be_u64 *)(void *)&controls;
	be_size index;
	unsigned int bit;

	SCENARIO();
	CHECK(BE_B6_HSTATUS_GUEST_CONTROLS == 0x180U);
	CHECK(BE_B6_HSTATUS_VIRTUAL_TRAPS == 0x700000U);
	CHECK(BE_B6_HEDELEG == 0xb15dU);
	CHECK(BE_B6_HIDELEG_VSTI == 0x40U && BE_B6_HIE_VSTIE == 0x40U);
	CHECK(BE_B6_HCOUNTEREN_TM == 0x2U);
	CHECK(BE_B6_HENVCFG_STCE == BE_U64_C(0x8000000000000000));
	CHECK(BE_B6_SSTATUS_CONTROL_MASK == 0xde722U);
	CHECK(BE_R3_INITIAL_TRUSTED_SP == BE_U64_C(0x102027000));
	CHECK(sizeof(controls) == 16U * sizeof(be_u64));
	CHECK(armed_valid(&controls) == 1);
	CHECK(be_b6_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP,
				   BE_U64_C(0x102027000)) == 0);
	CHECK(be_b6_controls_valid(&controls, BE_B6_HGATP,
				   BE_U64_C(0x102029000)) == 0);
	CHECK(be_b6_controls_valid((const struct be_b6_controls *)0,
				   BE_B6_HGATP, BE_U64_C(0x102027000)) == 0);
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

		CHECK(BE_B6_HEDELEG_REQUIRED == 0xb10cU);
		CHECK((BE_B6_HEDELEG & BE_B6_HEDELEG_REQUIRED) ==
		      BE_B6_HEDELEG_REQUIRED);
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
	controls.hstatus |= BE_R3_HSTATUS_VTW;
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
	controls.hie = BE_B6_HIE_VSTIE;
	CHECK(armed_valid(&controls) == 0);
	/* HS sstatus: SIE, SPIE, SPP, FS, VS, XS, SUM, and MXR all clear. */
	for (bit = 0U; bit < 64U; ++bit) {
		controls = armed_controls();
		controls.sstatus |= BE_U64_C(1) << bit;
		CHECK(armed_valid(&controls) ==
		      ((BE_B6_SSTATUS_CONTROL_MASK >> bit) & 1U ? 0 : 1));
	}
	controls = armed_controls();
	controls.sstatus |= BE_U64_C(1) << 9;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.sstatus |= BE_U64_C(1) << 10;
	CHECK(armed_valid(&controls) == 0);

	CHECK(be_b6_stce_class(BE_B6_HENVCFG_STCE) == BE_B6_CLASS_NONE);
	CHECK(be_b6_stce_class(0U) == BE_B6_CLASS_SSTC);
	CHECK(be_b6_stce_class(1U) == BE_B6_CLASS_SSTC);
	CHECK(be_b6_stce_class(ALL_ONES >> 1) == BE_B6_CLASS_SSTC);
	CHECK(be_b6_stce_class(BE_B6_HENVCFG_STCE | 1U) ==
	      BE_B6_CLASS_CONTROLS);
	CHECK(be_b6_stce_class(ALL_ONES) == BE_B6_CLASS_CONTROLS);
}

static void test_classify(void)
{
	be_u64 cause;

	SCENARIO();
	for (cause = 0U; cause < 64U; ++cause) {
		enum be_b6_class expected = BE_B6_CLASS_EXCEPTION;

		if (cause == 10U)
			expected = BE_B6_CLASS_NONE;
		else if (cause == 20U || cause == 21U || cause == 23U)
			expected = BE_B6_CLASS_GUEST_PAGE_FAULT;
		else if (cause == 22U)
			expected = BE_B6_CLASS_VIRTUAL_INSTRUCTION;
		else if (cause == 1U || cause == 5U || cause == 7U)
			expected = BE_B6_CLASS_ACCESS_FAULT;
		else if (cause == 2U)
			expected = BE_B6_CLASS_ILLEGAL_INSTRUCTION;
		CHECK(be_b6_classify_cause(cause) == expected);
		CHECK(be_b6_classify_cause(BE_B6_SCAUSE_INTERRUPT | cause) ==
		      BE_B6_CLASS_INTERRUPT);
	}
	CHECK(be_b6_classify_cause(ALL_ONES) == BE_B6_CLASS_INTERRUPT);
	CHECK(be_b6_classify_cause(ALL_ONES >> 1) == BE_B6_CLASS_EXCEPTION);
	CHECK(be_b6_classify_cause(HIGH_BIT | 10U) == BE_B6_CLASS_EXCEPTION);
	CHECK(be_b6_classify_cause(HIGH_BIT | 5U) == BE_B6_CLASS_EXCEPTION);
}

static void test_window(void)
{
	SCENARIO();
	CHECK(window.gpa_base == WINDOW_GPA);
	CHECK(window.hpa_base == WINDOW_HPA);
	CHECK(window.size == WINDOW_BYTES);
	CHECK(window.leaves == 32U);
	CHECK(window.hgatp == BE_B6_HGATP);
	CHECK(window.pool_pa == BE_U64_C(0x102034000));
}

static void test_base(void)
{
	static const be_u64 available[] = {
		BE_B6_SBI_EID_BASE, BE_B6_SBI_EID_TIME, BE_B6_SBI_EID_DBCN,
		BE_B6_SBI_EID_SRST,
	};
	static const be_u64 absent[] = {
		EID_HSM, EID_IPI, EID_RFENCE, EID_PMU, EID_SUSP, EID_CPPC,
		EID_NACL, EID_STA, EID_SSE, EID_FWFT, EID_DBTR, EID_MPXY,
		EID_UNASSIGNED, 0U, ALL_ONES, HIGH_BIT | BE_B6_SBI_EID_BASE,
		HIGH_BIT | BE_B6_SBI_EID_DBCN, BE_U64_C(0x08000000),
		BE_U64_C(0x09000000), BE_U64_C(0x0a000000),
	};
	be_size index;
	be_u64 legacy;

	SCENARIO();
	check_return(BE_B6_SBI_EID_BASE, 0U, 0U, 0U, 0U, 0, 0x2000000U);
	check_return(BE_B6_SBI_EID_BASE, 0U, ALL_ONES, 7U, 9U, 0, 0x2000000U);
	check_return(BE_B6_SBI_EID_BASE, 1U, 0U, 0U, 0U, 0, 0x4245U);
	/* Version 2, not B5's 1: reboot requests and DBCN changed (Q6). */
	check_return(BE_B6_SBI_EID_BASE, 2U, 0U, 0U, 0U, 0, 2U);
	check_return(BE_B6_SBI_EID_BASE, 4U, 0U, 0U, 0U, 0, 0U);
	check_return(BE_B6_SBI_EID_BASE, 5U, 0U, 0U, 0U, 0, 0U);
	check_return(BE_B6_SBI_EID_BASE, 6U, ALL_ONES, 0U, 0U, 0, 0U);
	for (index = 0U; index < BE_ARRAY_SIZE(available); ++index)
		check_return(BE_B6_SBI_EID_BASE, 3U, available[index], 0U, 0U,
			     0, 1U);
	for (index = 0U; index < BE_ARRAY_SIZE(absent); ++index)
		check_return(BE_B6_SBI_EID_BASE, 3U, absent[index], 0U, 0U, 0,
			     0U);
	for (legacy = 0U; legacy <= 0xfU; ++legacy)
		check_return(BE_B6_SBI_EID_BASE, 3U, legacy, 0U, 0U, 0, 0U);
	check_unsupported(BE_B6_SBI_EID_BASE, 7U);
	check_unsupported(BE_B6_SBI_EID_BASE, 8U);
	check_unsupported(BE_B6_SBI_EID_BASE, 0xffffffffU);
	check_unsupported(BE_B6_SBI_EID_BASE, HIGH_BIT);
	check_unsupported(BE_B6_SBI_EID_BASE, ALL_ONES);
}

static void test_unsupported(void)
{
	static const be_u64 eids[] = {
		EID_HSM, EID_IPI, EID_RFENCE, EID_PMU, EID_SUSP, EID_CPPC,
		EID_NACL, EID_STA, EID_SSE, EID_FWFT, EID_DBTR, EID_MPXY,
		EID_UNASSIGNED, BE_U64_C(0x08000000), BE_U64_C(0x09000000),
		BE_U64_C(0x0a000000), BE_U64_C(0x10) | HIGH_BIT,
		BE_B6_SBI_EID_TIME | HIGH_BIT, BE_B6_SBI_EID_DBCN | HIGH_BIT,
		BE_B6_SBI_EID_SRST | HIGH_BIT, ALL_ONES,
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
			     BE_B6_SBI_ERR_NOT_SUPPORTED, 0U);
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
		struct be_b6_exit record = ecall(BE_B6_SBI_EID_TIME, 0U,
					       values[index], 5U, 6U);
		struct be_b6_state state = fresh_state();
		struct be_b6_result result;

		CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
		      BE_B6_ACTION_SET_TIMER);
		CHECK(result.timer == values[index]);
		CHECK(result.error == BE_B6_SBI_SUCCESS);
		CHECK(result.value == 0U);
		CHECK(state.counts.time == 1U && call_sum(&state.counts) == 1U);
	}
	check_unsupported(BE_B6_SBI_EID_TIME, 1U);
	check_unsupported(BE_B6_SBI_EID_TIME, 2U);
	check_unsupported(BE_B6_SBI_EID_TIME, HIGH_BIT);
	check_unsupported(BE_B6_SBI_EID_TIME, ALL_ONES);
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
	check_dbcn_write(64U, BE_B6_KERNEL_GPA, 0U, BE_U64_C(0x110200000),
			 64U);
	check_dbcn_write(40U, BE_B6_DTB_GPA, 0U, BE_U64_C(0x113e00000), 40U);
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
	struct be_b6_gstage_map empty = { 0U, 0U, 0U, 0U, 0U, 0U };
	struct be_b6_state state = fresh_state();
	struct be_b6_exit record;
	struct be_b6_result result;
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
	check_return(BE_B6_SBI_EID_DBCN, 0U, 0U, BE_U64_C(0x40001000), 0U, 0,
		     0U);
	check_return(BE_B6_SBI_EID_DBCN, 0U, 0U, ALL_ONES, 0U, 0, 0U);
	check_return(BE_B6_SBI_EID_DBCN, 0U, 0U, WINDOW_GPA, 0U, 0, 0U);
	/* ...but never with a nonzero high word. */
	check_dbcn_refused(0U, WINDOW_GPA, 1U);
	/* An unwalked (empty) window admits nothing. */
	record = ecall(BE_B6_SBI_EID_DBCN, 0U, 1U, WINDOW_GPA, 0U);
	CHECK(be_b6_handle_exit(&state, &empty, &record, &result) ==
	      BE_B6_ACTION_RETURN);
	CHECK(result.error == BE_B6_SBI_ERR_INVALID_PARAM);
	CHECK(state.counts.refused == 1U && state.counts.dbcn_write == 0U);
}

static void test_dbcn_other(void)
{
	struct be_b6_exit record;
	struct be_b6_result result;
	struct be_b6_state state;
	be_u64 byte;

	SCENARIO();
	/* Console read is denied whatever the range, and is not refused. */
	check_return(BE_B6_SBI_EID_DBCN, 1U, 4U, WINDOW_GPA, 0U,
		     BE_B6_SBI_ERR_DENIED, 0U);
	check_return(BE_B6_SBI_EID_DBCN, 1U, 0U, 0U, 0U,
		     BE_B6_SBI_ERR_DENIED, 0U);
	check_return(BE_B6_SBI_EID_DBCN, 1U, ALL_ONES, ALL_ONES, ALL_ONES,
		     BE_B6_SBI_ERR_DENIED, 0U);
	state = fresh_state();
	record = ecall(BE_B6_SBI_EID_DBCN, 1U, 16U, WINDOW_GPA, 0U);
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_RETURN);
	CHECK(state.counts.dbcn_read == 1U && state.counts.refused == 0U);
	/* Write byte takes the low byte of a0. */
	for (byte = 0U; byte < 0x100U; ++byte) {
		record = ecall(BE_B6_SBI_EID_DBCN, 2U, byte | 0xab00U, 0U, 0U);
		state = fresh_state();
		CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
		      BE_B6_ACTION_CONSOLE_BYTE);
		CHECK(result.byte == byte);
		CHECK(result.error == BE_B6_SBI_SUCCESS);
		CHECK(result.value == 0U);
		CHECK(state.counts.dbcn_byte == 1U &&
		      call_sum(&state.counts) == 1U);
	}
	record = ecall(BE_B6_SBI_EID_DBCN, 2U, ALL_ONES, 1U, 2U);
	result = decide(&record);
	CHECK(result.action == BE_B6_ACTION_CONSOLE_BYTE);
	CHECK(result.byte == 0xffU);
	check_unsupported(BE_B6_SBI_EID_DBCN, 3U);
	check_unsupported(BE_B6_SBI_EID_DBCN, 4U);
	check_unsupported(BE_B6_SBI_EID_DBCN, HIGH_BIT);
	check_unsupported(BE_B6_SBI_EID_DBCN, ALL_ONES);
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
			struct be_b6_state state = fresh_state();
			struct be_b6_exit record = ecall(BE_B6_SBI_EID_SRST, 0U,
						       type, reason, 0U);
			struct be_b6_result result;

			(void)be_b6_handle_exit(&state, &window, &record,
						&result);
			if (type > 2U || reason > 1U) {
				/* Reserved values are refused, as in B5. */
				CHECK(result.action == BE_B6_ACTION_RETURN);
				CHECK(result.error ==
				      BE_B6_SBI_ERR_INVALID_PARAM);
				CHECK(state.phase == BE_B6_PHASE_RUNNING);
				CHECK(state.counts.refused == 1U);
			} else if (type != 0U) {
				/* A cold or warm reboot ends the run. */
				CHECK(result.action ==
				      BE_B6_ACTION_GUEST_REBOOT);
				CHECK(state.phase == BE_B6_PHASE_FAILED);
				CHECK(state.failure ==
				      BE_B6_CLASS_GUEST_REBOOT);
				CHECK(result.failure ==
				      BE_B6_CLASS_GUEST_REBOOT);
				CHECK(state.counts.srst == 1U);
			} else if (reason == 0U) {
				CHECK(result.action == BE_B6_ACTION_SHUTDOWN);
				CHECK(state.phase == BE_B6_PHASE_SHUTDOWN);
				CHECK(result.failure == BE_B6_CLASS_NONE);
				CHECK(state.counts.srst == 1U);
			} else {
				CHECK(result.action ==
				      BE_B6_ACTION_GUEST_FAILURE);
				CHECK(state.phase == BE_B6_PHASE_FAILED);
				CHECK(state.failure ==
				      BE_B6_CLASS_GUEST_FAILURE);
				CHECK(result.failure ==
				      BE_B6_CLASS_GUEST_FAILURE);
				CHECK(state.counts.srst == 1U);
			}
			CHECK(result.value == 0U);
			CHECK(state.counts.exits == 1U);
			CHECK(call_sum(&state.counts) == 1U);
		}
	}
	check_unsupported(BE_B6_SBI_EID_SRST, 1U);
	check_unsupported(BE_B6_SBI_EID_SRST, 2U);
	check_unsupported(BE_B6_SBI_EID_SRST, HIGH_BIT);
	check_unsupported(BE_B6_SBI_EID_SRST, ALL_ONES);
}

static void test_after_shutdown(void)
{
	struct be_b6_state state = fresh_state();
	struct be_b6_exit record = ecall(BE_B6_SBI_EID_SRST, 0U, 0U, 0U, 0U);
	struct be_b6_exit base = ecall(BE_B6_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b6_result result;

	SCENARIO();
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_SHUTDOWN);
	CHECK(be_b6_handle_exit(&state, &window, &base, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_EXCEPTION);
	CHECK(state.phase == BE_B6_PHASE_FAILED);
	CHECK(state.counts.exits == 1U);

	state = fresh_state();
	record = ecall(BE_B6_SBI_EID_SRST, 0U, 0U, 1U, 0U);
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_GUEST_FAILURE);
	CHECK(be_b6_handle_exit(&state, &window, &base, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_GUEST_FAILURE);
	CHECK(state.failure == BE_B6_CLASS_GUEST_FAILURE);

	state = fresh_state();
	record = ecall(BE_B6_SBI_EID_SRST, 0U, 2U, 0U, 0U);
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_GUEST_REBOOT);
	CHECK(be_b6_handle_exit(&state, &window, &base, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_GUEST_REBOOT);
	CHECK(state.counts.exits == 1U);
}

/* The ceiling counts every exit, whatever its class or outcome. */
static void check_ceiling(be_u64 ceiling)
{
	struct be_b6_state state = BE_B6_STATE_INITIALIZER(
		ceiling, BE_B6_GUEST_TIME_BUDGET);
	struct be_b6_exit record = ecall(BE_B6_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b6_exit unknown = ecall(EID_UNASSIGNED, 0U, 0U, 0U, 0U);
	struct be_b6_result result;
	be_u64 count;
	be_u64 good = 0U;

	state.entry_time = ENTRY_TIME;
	for (count = 1U; count <= ceiling; ++count) {
		const struct be_b6_exit *next = (count & 1U) ? &record : &unknown;

		if (be_b6_handle_exit(&state, &window, next, &result) ==
		    BE_B6_ACTION_RETURN)
			++good;
	}
	CHECK(good == ceiling);
	CHECK(state.counts.exits == ceiling);
	CHECK(state.counts.base == (ceiling + 1U) / 2U);
	CHECK(state.counts.refused == ceiling / 2U);
	CHECK(call_sum(&state.counts) == ceiling);
	CHECK(state.phase == BE_B6_PHASE_RUNNING);
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_EXIT_BUDGET);
	CHECK(state.phase == BE_B6_PHASE_FAILED);
	CHECK(state.counts.exits == ceiling + 1U);
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_EXIT_BUDGET);
	CHECK(state.counts.exits == ceiling + 1U);

	/* A terminal exit at the ceiling reports the ceiling. */
	state = (struct be_b6_state)BE_B6_STATE_INITIALIZER(
		ceiling, BE_B6_GUEST_TIME_BUDGET);
	state.counts.exits = ceiling;
	record = exit_with(BE_B6_SCAUSE_LOAD_GUEST_PAGE_FAULT, ECALL_PC);
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_EXIT_BUDGET);
}

static void test_exit_ceiling(void)
{
	SCENARIO();
	check_ceiling(BE_B6_VARIANT_EXIT_CEILING);
	check_ceiling(BE_B6_EXIT_CEILING);
}

/* The guest-time budget counts from the first entry, at every exit. */
static void check_budget(be_u64 budget)
{
	struct be_b6_state state = BE_B6_STATE_INITIALIZER(
		BE_B6_EXIT_CEILING, budget);
	struct be_b6_exit record = ecall(BE_B6_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b6_result result;

	state.entry_time = ENTRY_TIME;
	record.time = ENTRY_TIME;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_RETURN);
	record.time = ENTRY_TIME + budget - 1U;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_RETURN);
	record.time = ENTRY_TIME + budget;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_GUEST_TIMEOUT);
	CHECK(state.phase == BE_B6_PHASE_FAILED);
	CHECK(state.counts.exits == 3U && call_sum(&state.counts) == 2U);
	/* A time before the entry is out of budget too. */
	state = (struct be_b6_state)BE_B6_STATE_INITIALIZER(
		BE_B6_EXIT_CEILING, budget);
	state.entry_time = ENTRY_TIME;
	record.time = ENTRY_TIME - 1U;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_GUEST_TIMEOUT);
	/* The budget is checked before the cause: a late fault times out. */
	state = (struct be_b6_state)BE_B6_STATE_INITIALIZER(
		BE_B6_EXIT_CEILING, budget);
	state.entry_time = ENTRY_TIME;
	record = exit_with(BE_B6_SCAUSE_VIRTUAL_INSTRUCTION, ECALL_PC);
	record.time = ENTRY_TIME + budget + 1U;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_GUEST_TIMEOUT);
	/* The ceiling is checked before the budget. */
	state = (struct be_b6_state)BE_B6_STATE_INITIALIZER(1U, budget);
	state.entry_time = ENTRY_TIME;
	state.counts.exits = 1U;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_EXIT_BUDGET);
}

static void test_time_budget(void)
{
	SCENARIO();
	check_budget(BE_B6_VARIANT_GUEST_TIME_BUDGET);
	check_budget(BE_B6_GUEST_TIME_BUDGET);
	/* 2^32 ticks is about 179 s at the board's 24 MHz timebase. */
	CHECK(BE_B6_GUEST_TIME_BUDGET / BE_B6_TIMEBASE_HZ == 178U);
}

static void test_terminal_exits(void)
{
	static const struct {
		be_u64 scause;
		enum be_b6_class failure;
	} exits[] = {
		{ BE_B6_SCAUSE_INTERRUPT | 1U, BE_B6_CLASS_INTERRUPT },
		{ BE_B6_SCAUSE_INTERRUPT | 2U, BE_B6_CLASS_INTERRUPT },
		{ BE_B6_SCAUSE_INTERRUPT | 5U, BE_B6_CLASS_INTERRUPT },
		{ BE_B6_SCAUSE_INTERRUPT | 6U, BE_B6_CLASS_INTERRUPT },
		{ BE_B6_SCAUSE_INTERRUPT | 9U, BE_B6_CLASS_INTERRUPT },
		{ BE_B6_SCAUSE_INTERRUPT | 10U, BE_B6_CLASS_INTERRUPT },
		{ BE_B6_SCAUSE_INTERRUPT | 12U, BE_B6_CLASS_INTERRUPT },
		{ 20U, BE_B6_CLASS_GUEST_PAGE_FAULT },
		{ 21U, BE_B6_CLASS_GUEST_PAGE_FAULT },
		{ 23U, BE_B6_CLASS_GUEST_PAGE_FAULT },
		{ 22U, BE_B6_CLASS_VIRTUAL_INSTRUCTION },
		{ 1U, BE_B6_CLASS_ACCESS_FAULT },
		{ 5U, BE_B6_CLASS_ACCESS_FAULT },
		{ 7U, BE_B6_CLASS_ACCESS_FAULT },
		{ 2U, BE_B6_CLASS_ILLEGAL_INSTRUCTION },
		{ 0U, BE_B6_CLASS_EXCEPTION },
		{ 3U, BE_B6_CLASS_EXCEPTION },
		{ 4U, BE_B6_CLASS_EXCEPTION },
		{ 6U, BE_B6_CLASS_EXCEPTION },
		{ 8U, BE_B6_CLASS_EXCEPTION },
		{ 9U, BE_B6_CLASS_EXCEPTION },
		{ 11U, BE_B6_CLASS_EXCEPTION },
		{ 12U, BE_B6_CLASS_EXCEPTION },
		{ 13U, BE_B6_CLASS_EXCEPTION },
		{ 15U, BE_B6_CLASS_EXCEPTION },
		{ 18U, BE_B6_CLASS_EXCEPTION },
		{ 19U, BE_B6_CLASS_EXCEPTION },
		{ 24U, BE_B6_CLASS_EXCEPTION },
	};
	be_size index;
	unsigned int spvp;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(exits); ++index) {
		/* VS-origin (SPVP = 1) and VU-origin (SPVP = 0) alike. */
		for (spvp = 0U; spvp < 2U; ++spvp) {
			struct be_b6_state state = fresh_state();
			struct be_b6_exit record = exit_with(exits[index].scause,
							   ECALL_PC);
			struct be_b6_exit base = ecall(BE_B6_SBI_EID_BASE, 0U,
						       0U, 0U, 0U);
			struct be_b6_result result;

			if (spvp == 0U)
				record.hstatus &= ~BE_B6_HSTATUS_SPVP;
			/* The registers of an SBI call do not matter here. */
			record.frame.gpr[BE_R4_GPR_A7] = BE_B6_SBI_EID_BASE;
			record.frame.gpr[BE_R4_GPR_A6] = 0U;
			CHECK(be_b6_handle_exit(&state, &window, &record,
						&result) ==
			      BE_B6_ACTION_TERMINAL);
			CHECK(result.failure == exits[index].failure);
			CHECK(state.phase == BE_B6_PHASE_FAILED);
			CHECK(state.failure == exits[index].failure);
			CHECK(state.counts.exits == 1U);
			CHECK(call_sum(&state.counts) == 0U);
			CHECK(be_b6_handle_exit(&state, &window, &base,
						&result) ==
			      BE_B6_ACTION_TERMINAL);
			CHECK(result.failure == exits[index].failure);
			CHECK(state.counts.exits == 1U);
		}
	}
}

static void test_frame_integrity(void)
{
	struct be_b6_state state = fresh_state();
	struct be_b6_exit record = ecall(BE_B6_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b6_result result;

	SCENARIO();
	record.frame.reserved = 1U;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_EXCEPTION);

	/* Only an exit from V=1 (SPV = 1) is a guest exit. */
	state = fresh_state();
	record = ecall(BE_B6_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	record.hstatus &= ~BE_B6_HSTATUS_SPV;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_EXCEPTION);
	state = fresh_state();
	record.hstatus = BE_B6_HSTATUS_SPV;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_RETURN);

	state = fresh_state();
	record = ecall(BE_B6_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	record.frame.sepc = ALL_ONES - 3U;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_RESUME);

	state = fresh_state();
	record.frame.sepc = ALL_ONES - 4U;
	CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
	      BE_B6_ACTION_RETURN);
	CHECK(result.resume_pc == ALL_ONES);

	state = fresh_state();
	CHECK(be_b6_handle_exit(&state, (const struct be_b6_gstage_map *)0,
				&record, &result) == BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_EXCEPTION);
	state = fresh_state();
	CHECK(be_b6_handle_exit(&state, &window,
				(const struct be_b6_exit *)0, &result) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(state.phase == BE_B6_PHASE_FAILED);
	state = fresh_state();
	CHECK(be_b6_handle_exit(&state, &window, &record,
				(struct be_b6_result *)0) ==
	      BE_B6_ACTION_TERMINAL);
	CHECK(state.phase == BE_B6_PHASE_FAILED);
	CHECK(be_b6_handle_exit((struct be_b6_state *)0, &window, &record,
				&result) == BE_B6_ACTION_TERMINAL);
	CHECK(result.failure == BE_B6_CLASS_EXCEPTION);

	/* The sticky class: the first failure is kept. */
	state = fresh_state();
	CHECK(be_b6_fail(&state, BE_B6_CLASS_SSTC) == BE_B6_CLASS_SSTC);
	CHECK(be_b6_fail(&state, BE_B6_CLASS_CONSOLE) == BE_B6_CLASS_SSTC);
	state = fresh_state();
	CHECK(be_b6_fail(&state, BE_B6_CLASS_NONE) == BE_B6_CLASS_EXCEPTION);
	CHECK(be_b6_fail((struct be_b6_state *)0, BE_B6_CLASS_BOOT) ==
	      BE_B6_CLASS_BOOT);
	state = fresh_state();
	CHECK(be_b6_fail(&state, BE_B6_CLASS_COUNT) == BE_B6_CLASS_EXCEPTION);
}

static void test_apply_return(void)
{
	struct be_b6_exit record = ecall(BE_B6_SBI_EID_BASE, 7U, 1U, 2U, 3U);
	struct be_b6_exit before = record;
	struct be_b6_result result = decide(&record);
	be_size index;

	SCENARIO();
	CHECK(result.error == BE_B6_SBI_ERR_NOT_SUPPORTED);
	be_b6_apply_return(&record.frame, &result);
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
	be_b6_apply_return((struct be_r4_frame *)0, &result);
	be_b6_apply_return(&record.frame, (const struct be_b6_result *)0);
	CHECK(record.frame.sepc == ECALL_PC + 4U);
}

/* The first entry: sepc, a0 = hart, a1 = DTB; every other word 0. */
static void test_entry_frame(void)
{
	struct be_b6_exit record;
	const be_u64 *words = (const be_u64 *)(const void *)&record;
	be_size index;

	SCENARIO();
	memset(&record, 0xa5, sizeof(record));
	be_b6_entry_frame(&record, BE_B6_KERNEL_GPA, BE_B6_GUEST_HART,
			  BE_B6_DTB_GPA);
	CHECK(record.frame.sepc == BE_U64_C(0x80200000));
	CHECK(record.frame.gpr[BE_R4_GPR_A0] == 0U);
	CHECK(record.frame.gpr[BE_R4_GPR_A1] == BE_U64_C(0x83e00000));
	for (index = 0U; index < sizeof(record) / sizeof(be_u64); ++index) {
		if (index == BE_R4_GPR_A1 ||
		    index == __builtin_offsetof(struct be_r4_frame, sepc) /
				     sizeof(be_u64))
			continue;
		CHECK(words[index] == 0U);
	}
	be_b6_entry_frame(&record, 1U, 2U, 3U);
	CHECK(record.frame.sepc == 1U && record.frame.gpr[BE_R4_GPR_A0] == 2U &&
	      record.frame.gpr[BE_R4_GPR_A1] == 3U);
	be_b6_entry_frame((struct be_b6_exit *)0, 1U, 2U, 3U);
}

static be_u64 tag(struct be_b6_console *console, const char *text,
		  char *output)
{
	return be_b6_console_tag(console, (const be_u8 *)text, strlen(text),
				 output, BE_B6_TAGGED_CAPACITY);
}

static void test_console_tag(void)
{
	static char output[BE_B6_TAGGED_CAPACITY + 16U];
	struct be_b6_console console = { 0 };
	be_u8 input[BE_B6_DBCN_MAX_BYTES + 1U];
	be_u64 length;
	be_size index;

	SCENARIO();
	length = tag(&console, "[    0.000000] Linux version 7.2.0\n", output);
	CHECK(length == 13U + 35U);
	CHECK(memcmp(output,
		     "BE_B6_GUEST: [    0.000000] Linux version 7.2.0\n",
		     (size_t)length) == 0);
	CHECK(console.line_open == 0U);

	/* hvc sends CR before LF: the CR is dropped. */
	length = tag(&console, "B6INIT 04 RESULT pass\r\n", output);
	CHECK(length == 13U + 22U);
	CHECK(memcmp(output, "BE_B6_GUEST: B6INIT 04 RESULT pass\n",
		     (size_t)length) == 0);
	CHECK(console.line_open == 0U);
	/* CR alone writes nothing and opens no line. */
	length = tag(&console, "\r", output);
	CHECK(length == 0U && console.line_open == 0U);
	length = tag(&console, "\r\r\n", output);
	CHECK(length == 14U);
	CHECK(memcmp(output, "BE_B6_GUEST: \n", 14U) == 0);
	length = tag(&console, "a\rb\n", output);
	CHECK(length == 13U + 3U);
	CHECK(memcmp(output, "BE_B6_GUEST: ab\n", (size_t)length) == 0);

	/* A line split across calls has one prefix. */
	length = tag(&console, "B6INIT 01 ST", output);
	CHECK(length == 13U + 12U);
	CHECK(memcmp(output, "BE_B6_GUEST: B6INIT 01 ST", (size_t)length) ==
	      0);
	CHECK(console.line_open == 1U);
	length = tag(&console, "ART pid=1\r", output);
	CHECK(length == 9U);
	CHECK(memcmp(output, "ART pid=1", 9U) == 0);
	CHECK(console.line_open == 1U);
	length = tag(&console, "\n", output);
	CHECK(length == 1U && output[0] == '\n');
	CHECK(console.line_open == 0U);

	/* A bare newline is an empty guest line. */
	length = tag(&console, "\n", output);
	CHECK(length == 14U);
	CHECK(memcmp(output, "BE_B6_GUEST: \n", 14U) == 0);

	/* Forged evidence lines stay guest lines. */
	length = tag(&console, "x\nBE_R3:01 BOOT_VALIDATED\n", output);
	CHECK(length == 13U + 2U + 13U + 24U);
	CHECK(memcmp(output,
		     "BE_B6_GUEST: x\nBE_B6_GUEST: BE_R3:01 BOOT_VALIDATED\n",
		     (size_t)length) == 0);
	length = tag(&console, "\tBE_B6:09 SHUTDOWN type=0 reason=0\n",
		     output);
	CHECK(memcmp(output,
		     "BE_B6_GUEST: ?BE_B6:09 SHUTDOWN type=0 reason=0\n",
		     (size_t)length) == 0);

	/* Every byte value: printable ASCII and LF pass, CR vanishes, the
	 * rest is '?'. */
	for (index = 0U; index < 256U; ++index) {
		be_u8 byte = (be_u8)index;

		console.line_open = 1U;
		length = be_b6_console_tag(&console, &byte, 1U, output,
					   BE_B6_TAGGED_CAPACITY);
		if (byte == '\r') {
			CHECK(length == 0U && console.line_open == 1U);
			continue;
		}
		CHECK(length == 1U);
		if (byte == '\n')
			CHECK(output[0] == '\n' && console.line_open == 0U);
		else if (byte >= 0x20U && byte <= 0x7eU)
			CHECK(output[0] == (char)byte &&
			      console.line_open == 1U);
		else
			CHECK(output[0] == '?' && console.line_open == 1U);
	}

	/* The worst case fills exactly the tagged capacity. */
	memset(input, '\n', sizeof(input));
	console.line_open = 0U;
	length = be_b6_console_tag(&console, input, BE_B6_DBCN_MAX_BYTES,
				   output, BE_B6_TAGGED_CAPACITY);
	CHECK(length == BE_B6_TAGGED_CAPACITY);
	for (index = 0U; index < BE_B6_DBCN_MAX_BYTES; ++index)
		CHECK(memcmp(output + index * 14U, "BE_B6_GUEST: \n", 14U) ==
		      0);
	/* A chunk of CRs writes nothing. */
	memset(input, '\r', sizeof(input));
	CHECK(be_b6_console_tag(&console, input, BE_B6_DBCN_MAX_BYTES, output,
				BE_B6_TAGGED_CAPACITY) == 0U);
	CHECK(console.line_open == 0U);

	/* Invalid requests change nothing. */
	memset(input, 'x', sizeof(input));
	console.line_open = 0U;
	CHECK(be_b6_console_tag(&console, input, BE_B6_DBCN_MAX_BYTES + 1U,
				output, BE_B6_TAGGED_CAPACITY) ==
	      BE_B6_TAG_INVALID);
	CHECK(be_b6_console_tag(&console, input, 1U, output,
				BE_B6_TAGGED_CAPACITY - 1U) ==
	      BE_B6_TAG_INVALID);
	CHECK(be_b6_console_tag((struct be_b6_console *)0, input, 1U, output,
				BE_B6_TAGGED_CAPACITY) == BE_B6_TAG_INVALID);
	CHECK(be_b6_console_tag(&console, (const be_u8 *)0, 1U, output,
				BE_B6_TAGGED_CAPACITY) == BE_B6_TAG_INVALID);
	CHECK(be_b6_console_tag(&console, input, 1U, (char *)0,
				BE_B6_TAGGED_CAPACITY) == BE_B6_TAG_INVALID);
	CHECK(console.line_open == 0U);
	CHECK(be_b6_console_tag(&console, input, 0U, output,
				BE_B6_TAGGED_CAPACITY) == 0U);
	CHECK(console.line_open == 0U);

	/* A monitor line first ends an open guest line. */
	CHECK(be_b6_console_close(&console) == 0U);
	(void)tag(&console, "partial", output);
	CHECK(be_b6_console_close(&console) == 1U);
	CHECK(console.line_open == 0U);
	CHECK(be_b6_console_close(&console) == 0U);
	CHECK(be_b6_console_close((struct be_b6_console *)0) == 0U);
	length = tag(&console, "next\n", output);
	CHECK(memcmp(output, "BE_B6_GUEST: next\n", (size_t)length) == 0);
}

static int line_is(const struct be_b6_line *line, const char *text)
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
	struct be_b6_line line;
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(values); ++index) {
		be_b6_line_reset(&line);
		be_b6_line_hex(&line, values[index].value);
		CHECK(line_is(&line, values[index].hex));
		be_b6_line_reset(&line);
		be_b6_line_decimal(&line, values[index].value);
		CHECK(line_is(&line, values[index].decimal));
	}

	/* Plan markers composed from fixed text and values. */
	be_b6_line_reset(&line);
	be_b6_line_text(&line, "BE_B6:01 GSTAGE_BUILT_REWALKED gpa=");
	be_b6_line_hex(&line, WINDOW_GPA);
	be_b6_line_text(&line, " hpa=");
	be_b6_line_hex(&line, WINDOW_HPA);
	be_b6_line_text(&line, " size=");
	be_b6_line_hex(&line, WINDOW_BYTES);
	be_b6_line_text(&line, " leaves=");
	be_b6_line_decimal(&line, 32U);
	be_b6_line_text(&line, " pool=");
	be_b6_line_hex(&line, BE_B6_POOL_HPA);
	be_b6_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_B6:01 GSTAGE_BUILT_REWALKED gpa=0x80000000 "
		      "hpa=0x110000000 size=0x4000000 leaves=32 "
		      "pool=0x102034000\n"));
	be_b6_line_reset(&line);
	be_b6_line_text(&line,
			"BE_B6:04 GUEST_CONTROLS_CHECKED hstatus_controls=");
	be_b6_line_hex(&line, 0x180U);
	be_b6_line_text(&line, " hedeleg=");
	be_b6_line_hex(&line, 0xb15dU);
	be_b6_line_text(&line, " hideleg=");
	be_b6_line_hex(&line, 0x40U);
	be_b6_line_text(&line, " hcounteren=");
	be_b6_line_hex(&line, 0x2U);
	be_b6_line_text(&line, " fs=");
	be_b6_line_hex(&line, 0U);
	be_b6_line_text(&line, " vs=");
	be_b6_line_hex(&line, 0U);
	be_b6_line_text(&line, " vstimecmp=");
	be_b6_line_hex(&line, ALL_ONES);
	be_b6_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_B6:04 GUEST_CONTROLS_CHECKED "
		      "hstatus_controls=0x180 hedeleg=0xb15d hideleg=0x40 "
		      "hcounteren=0x2 fs=0x0 vs=0x0 "
		      "vstimecmp=0xffffffffffffffff\n"));
	/* The worst-case DETAIL and GUEST_SHUTDOWN lines fit. */
	be_b6_line_reset(&line);
	be_b6_line_text(&line, "BE_B6:DETAIL cause=");
	be_b6_line_hex(&line, ALL_ONES);
	for (index = 0U; index < 4U; ++index) {
		be_b6_line_text(&line, " htinst=");
		be_b6_line_hex(&line, ALL_ONES);
	}
	be_b6_line_text(&line, " spvp=");
	be_b6_line_decimal(&line, 1U);
	be_b6_line_text(&line, " vsatp=");
	be_b6_line_hex(&line, ALL_ONES);
	be_b6_line_text(&line, " exits=");
	be_b6_line_decimal(&line, ALL_ONES);
	be_b6_line_text(&line, "\n");
	CHECK(line.overflow == 0U && line.length < 220U);
	be_b6_line_reset(&line);
	be_b6_line_text(&line, "BE_B6:08 GUEST_SHUTDOWN type=0 reason=0 exits=");
	for (index = 0U; index < 7U; ++index) {
		be_b6_line_decimal(&line, ALL_ONES);
		be_b6_line_text(&line, " dbcn_write=");
	}
	be_b6_line_decimal(&line, ALL_ONES);
	be_b6_line_text(&line, " ticks=");
	be_b6_line_hex(&line, ALL_ONES);
	be_b6_line_text(&line, "\n");
	CHECK(line.overflow == 0U && line.length < BE_B6_LINE_CAPACITY);

	/* Overflow is sticky and makes the line unusable. */
	be_b6_line_reset(&line);
	for (index = 0U; index < BE_B6_LINE_CAPACITY; ++index)
		be_b6_line_text(&line, "x");
	CHECK(line.length == BE_B6_LINE_CAPACITY && line.overflow == 0U);
	be_b6_line_text(&line, "y");
	CHECK(line.overflow == 1U);
	CHECK(line.length == BE_B6_LINE_CAPACITY);
	be_b6_line_reset(&line);
	CHECK(line.length == 0U && line.overflow == 0U);
	be_b6_line_text(&line, (const char *)0);
	CHECK(line.overflow == 1U);
	be_b6_line_reset(&line);
	for (index = 0U; index < 17U; ++index)
		be_b6_line_hex(&line, ALL_ONES);
	CHECK(line.length == 17U * 18U && line.overflow == 0U);
	be_b6_line_hex(&line, ALL_ONES);
	CHECK(line.overflow == 1U);
	CHECK(line.length == BE_B6_LINE_CAPACITY);
	be_b6_line_reset((struct be_b6_line *)0);
	be_b6_line_text((struct be_b6_line *)0, "x");
	be_b6_line_hex((struct be_b6_line *)0, 1U);
	be_b6_line_decimal((struct be_b6_line *)0, 1U);
}

/* One SBI call of a replay; checks the decision and, for returns, the
 * values the guest receives. */
static void replay(struct be_b6_state *state, be_u64 eid, be_u64 fid,
		   be_u64 argument0, be_u64 argument1,
		   enum be_b6_action action, long error, be_u64 value)
{
	struct be_b6_exit record = ecall(eid, fid, argument0, argument1, 0U);
	struct be_b6_result result;

	record.time = ENTRY_TIME + state->counts.exits * BE_U64_C(0x40000);
	CHECK(be_b6_handle_exit(state, &window, &record, &result) == action);
	CHECK(result.error == error && result.value == value);
	if (action == BE_B6_ACTION_CONSOLE_WRITE)
		CHECK(result.source_pa == argument1 - WINDOW_GPA + WINDOW_HPA);
	if (action != BE_B6_ACTION_SHUTDOWN && action != BE_B6_ACTION_TERMINAL)
		CHECK(state->phase == BE_B6_PHASE_RUNNING);
}

static void replay_write(struct be_b6_state *state, be_u64 call)
{
	static const be_u64 lengths[] = { 57U, 120U, 16U, 16U, 300U, 4U, 16U,
					  200U };
	be_u64 length = lengths[call % BE_ARRAY_SIZE(lengths)];
	be_u64 gpa = BE_U64_C(0x81234000) + (call % 8U) * 0x100U;

	replay(state, BE_B6_SBI_EID_DBCN, 0U, length, gpa,
	       BE_B6_ACTION_CONSOLE_WRITE, BE_B6_SBI_SUCCESS,
	       length < 256U ? length : 256U);
}

/* The Base calls a v7.2 uniprocessor boot makes before its first write. */
static void replay_base(struct be_b6_state *state)
{
	replay(state, BE_B6_SBI_EID_BASE, 0U, 0U, 0U, BE_B6_ACTION_RETURN, 0,
	       0x2000000U);
	replay(state, BE_B6_SBI_EID_BASE, 1U, 0U, 0U, BE_B6_ACTION_RETURN, 0,
	       0x4245U);
	replay(state, BE_B6_SBI_EID_BASE, 2U, 0U, 0U, BE_B6_ACTION_RETURN, 0,
	       2U);
	replay(state, BE_B6_SBI_EID_BASE, 3U, BE_B6_SBI_EID_TIME, 0U,
	       BE_B6_ACTION_RETURN, 0, 1U);
	replay(state, BE_B6_SBI_EID_BASE, 3U, EID_IPI, 0U,
	       BE_B6_ACTION_RETURN, 0, 0U);
	replay(state, BE_B6_SBI_EID_BASE, 3U, EID_RFENCE, 0U,
	       BE_B6_ACTION_RETURN, 0, 0U);
	replay(state, BE_B6_SBI_EID_BASE, 3U, BE_B6_SBI_EID_SRST, 0U,
	       BE_B6_ACTION_RETURN, 0, 1U);
	replay(state, BE_B6_SBI_EID_BASE, 3U, BE_B6_SBI_EID_DBCN, 0U,
	       BE_B6_ACTION_RETURN, 0, 1U);
}

/*
 * The research reference boot's 139 SBI calls (platform research section
 * 1c): 3 Base IDs; probes for TIME, IPI, RFENCE, SRST, and DBCN answered 1,
 * 0, 0, 1, 1; 6 machine-ID reads; 89 DBCN writes; 35 DBCN reads denied with
 * -4; and one SRST shutdown. The research run's own Base answers were
 * OpenSBI's; here they are B6's.
 */
static void test_census(void)
{
	struct be_b6_state state = fresh_state();
	be_u64 call;
	be_u64 writes = 0U;
	unsigned int round;

	SCENARIO();
	replay_base(&state);
	for (call = 0U; call < 12U; ++call)
		replay_write(&state, writes++);
	for (round = 0U; round < 2U; ++round) {
		replay(&state, BE_B6_SBI_EID_BASE, 4U, 0U, 0U,
		       BE_B6_ACTION_RETURN, 0, 0U);
		replay(&state, BE_B6_SBI_EID_BASE, 5U, 0U, 0U,
		       BE_B6_ACTION_RETURN, 0, 0U);
		replay(&state, BE_B6_SBI_EID_BASE, 6U, 0U, 0U,
		       BE_B6_ACTION_RETURN, 0, 0U);
	}
	for (call = 0U; call < 45U; ++call)
		replay_write(&state, writes++);
	/* From call 72, hvc polls for input between its writes. */
	for (call = 0U; call < 35U; ++call) {
		replay(&state, BE_B6_SBI_EID_DBCN, 1U, 16U,
		       BE_U64_C(0x81fff000), BE_B6_ACTION_RETURN,
		       BE_B6_SBI_ERR_DENIED, 0U);
		if (call < 32U)
			replay_write(&state, writes++);
	}
	CHECK(state.counts.exits == 138U);
	replay(&state, BE_B6_SBI_EID_SRST, 0U, 0U, 0U, BE_B6_ACTION_SHUTDOWN,
	       0, 0U);
	CHECK(state.phase == BE_B6_PHASE_SHUTDOWN);
	CHECK(state.counts.exits == 139U);
	CHECK(state.counts.base == 14U);
	CHECK(state.counts.time == 0U);
	CHECK(state.counts.dbcn_write == 89U);
	CHECK(state.counts.dbcn_read == 35U);
	CHECK(state.counts.dbcn_byte == 0U);
	CHECK(state.counts.srst == 1U);
	CHECK(state.counts.refused == 0U);
	CHECK(call_sum(&state.counts) == state.counts.exits);
	CHECK(state.counts.exits <= BE_B6_EXIT_CEILING);
	/* With the exit-budget variant's ceiling the same boot stops at 65. */
	state = (struct be_b6_state)BE_B6_STATE_INITIALIZER(
		BE_B6_VARIANT_EXIT_CEILING, BE_B6_GUEST_TIME_BUDGET);
	state.entry_time = ENTRY_TIME;
	replay_base(&state);
	for (call = 0U; call < 56U; ++call)
		replay_write(&state, call);
	CHECK(state.counts.exits == 64U && state.phase == BE_B6_PHASE_RUNNING);
	replay(&state, BE_B6_SBI_EID_DBCN, 0U, 16U, BE_U64_C(0x81234000),
	       BE_B6_ACTION_TERMINAL, 0, 0U);
	CHECK(state.failure == BE_B6_CLASS_EXIT_BUDGET);
	CHECK(state.counts.exits == 65U);
}

/* The sbi-time variant: no sstc in the DT, so Linux arms through TIME. */
static void test_census_sbi_time(void)
{
	struct be_b6_state state = fresh_state();
	be_u64 call;

	SCENARIO();
	replay_base(&state);
	for (call = 0U; call < 10U; ++call)
		replay_write(&state, call);
	for (call = 0U; call < 20U; ++call) {
		be_u64 deadline = (call & 1U) ? ALL_ONES :
			ENTRY_TIME + (call + 1U) * BE_U64_C(96000);
		struct be_b6_exit record = ecall(BE_B6_SBI_EID_TIME, 0U,
					       deadline, 0U, 0U);
		struct be_b6_result result;

		record.time = ENTRY_TIME + call * BE_U64_C(48000);
		CHECK(be_b6_handle_exit(&state, &window, &record, &result) ==
		      BE_B6_ACTION_SET_TIMER);
		CHECK(result.timer == deadline && result.error == 0 &&
		      result.value == 0U);
	}
	replay(&state, BE_B6_SBI_EID_SRST, 0U, 0U, 0U, BE_B6_ACTION_SHUTDOWN,
	       0, 0U);
	CHECK(state.counts.time == 20U && state.counts.base == 8U);
	CHECK(state.counts.dbcn_write == 10U && state.counts.srst == 1U);
	CHECK(state.counts.exits == 39U &&
	      call_sum(&state.counts) == state.counts.exits);
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
	test_console_tag();
	test_line_builder();
	test_census();
	test_census_sbi_time();

	puts("BE_B6_CHECK: PASS");
	print_count("BE_B6_CHECK: scenarios=", scenarios);
	print_count("BE_B6_CHECK: assertions=", assertions);
	return 0;
}
