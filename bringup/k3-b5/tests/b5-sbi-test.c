// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the K3 B5 guest SBI core: every row of the
 *          plan's SBI table, the DBCN range check at every leaf edge, the
 *          SRST type and reason grid, TIME values, exit classes and the exit
 *          budget, the frame return, the tagged console and its byte
 *          filter, and the monitor line builder.
 * Trust:   host evidence only. No CSR, guest entry, QEMU, or hardware
 *          behaviour is exercised. The management leaves come from the
 *          accepted R1/R2 pipeline as B2 and B5 port it, built in host memory.
 * Scope:   B5 only (planning/k3-b5-plan.md).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <be/r1-config.h>

#include "b5.h"
#include "r0-layout.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_B5_CHECK: assertion failed: %s:%d: %s\n", \
			       __FILE__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define ECALL_PC		BE_U64_C(0x40010040)
#define FRAME_PATTERN		BE_U64_C(0x5a5a000000000000)
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

static struct be_runtime runtime = BE_RUNTIME_INITIALIZER;
static struct be_r2_output r2_output;
static struct be_r2_leaf_set leaf_sets[BE_MAX_ROOTS];
static be_u8 management_pool[BE_SV39X4_POOL_SIZE]
	__attribute__((aligned(16384)));
static be_u8 protected_pool[BE_SV39X4_POOL_SIZE]
	__attribute__((aligned(16384)));
static const struct be_r2_leaf_set *management = &leaf_sets[0];

/* The expected management leaves: private RW, shared RW, code R-X. */
static const struct be_r2_leaf expected_leaves[3] = {
	{ BE_R0_GPA_MANAGEMENT_PRIVATE, BE_R0_PA_PRIVATE_MANAGEMENT,
	  BE_R0_RW },
	{ BE_R0_GPA_SHARED, BE_R0_PA_SHARED, BE_R0_RW },
	{ BE_R0_GPA_GUEST_CODE_MANAGEMENT, BE_R0_PA_GUEST_CODE_MANAGEMENT,
	  BE_R0_RX },
};

static void build_leaves(void)
{
	struct be_r2_pool_desc pools[BE_MAX_ROOTS] = {
		{ .base = BE_R0_PA_ROOT_POOL_MANAGEMENT,
		  .buf = management_pool, .buf_size = BE_SV39X4_POOL_SIZE },
		{ .base = BE_R0_PA_ROOT_POOL_PROTECTED,
		  .buf = protected_pool, .buf_size = BE_SV39X4_POOL_SIZE },
	};

	CHECK(be_runtime_copy_inventory(&runtime, be_r1_inventory()) ==
	      BE_RUNTIME_OK);
	CHECK(be_runtime_copy_proposal(&runtime, be_r1_proposal()) ==
	      BE_RUNTIME_OK);
	CHECK(be_runtime_validate(&runtime) == BE_RUNTIME_OK);
	CHECK(be_runtime_seal(&runtime) == BE_RUNTIME_OK);
	CHECK(be_runtime_derive(&runtime) == BE_RUNTIME_OK);
	CHECK(be_r2_build(&runtime, pools, &r2_output) == BE_CHECK_OK);
	CHECK(be_r2_walk_and_check(&runtime, pools, &r2_output, leaf_sets) ==
	      BE_CHECK_OK);
}

static struct be_r4_frame frame_with(be_u64 scause, be_u64 sepc)
{
	struct be_r4_frame frame;
	be_size index;

	memset(&frame, 0, sizeof(frame));
	for (index = 0U; index < BE_ARRAY_SIZE(frame.gpr); ++index)
		frame.gpr[index] = FRAME_PATTERN | index;
	frame.vstvec = FRAME_PATTERN | 0x100U;
	frame.vsepc = FRAME_PATTERN | 0x101U;
	frame.vscause = FRAME_PATTERN | 0x102U;
	frame.vstval = FRAME_PATTERN | 0x103U;
	frame.scause = scause;
	frame.sepc = sepc;
	frame.stval = FRAME_PATTERN | 0x104U;
	frame.htval = FRAME_PATTERN | 0x105U;
	frame.reserved = 0U;
	return frame;
}

static struct be_r4_frame ecall(be_u64 eid, be_u64 fid, be_u64 argument0,
				be_u64 argument1, be_u64 argument2)
{
	struct be_r4_frame frame = frame_with(BE_B5_SCAUSE_VS_ECALL, ECALL_PC);

	frame.gpr[BE_R4_GPR_A7] = eid;
	frame.gpr[BE_R4_GPR_A6] = fid;
	frame.gpr[BE_R4_GPR_A0] = argument0;
	frame.gpr[BE_R4_GPR_A1] = argument1;
	frame.gpr[BE_B5_GPR_A2] = argument2;
	return frame;
}

/* One exit on a fresh running state; checks the generic ecall properties. */
static struct be_b5_result decide(const struct be_r4_frame *frame)
{
	struct be_b5_state state = BE_B5_STATE_INITIALIZER;
	struct be_b5_result result;

	CHECK(be_b5_handle_exit(&state, management, frame, &result) ==
	      result.action);
	CHECK(state.exits == 1U);
	if (result.action != BE_B5_ACTION_TERMINAL)
		CHECK(result.resume_pc == frame->sepc + 4U);
	if (result.action == BE_B5_ACTION_RETURN ||
	    result.action == BE_B5_ACTION_CONSOLE_WRITE ||
	    result.action == BE_B5_ACTION_CONSOLE_BYTE ||
	    result.action == BE_B5_ACTION_SET_TIMER)
		CHECK(state.phase == BE_B5_PHASE_RUNNING);
	return result;
}

static void check_return(be_u64 eid, be_u64 fid, be_u64 argument0,
			 be_u64 argument1, be_u64 argument2, long error,
			 be_u64 value)
{
	struct be_r4_frame frame = ecall(eid, fid, argument0, argument1,
					 argument2);
	struct be_b5_result result = decide(&frame);

	CHECK(result.action == BE_B5_ACTION_RETURN);
	CHECK(result.error == error);
	CHECK(result.value == value);
	CHECK(result.failure == BE_B5_CLASS_NONE);
}

static void check_unsupported(be_u64 eid, be_u64 fid)
{
	check_return(eid, fid, 0U, 0U, 0U, BE_B5_SBI_ERR_NOT_SUPPORTED, 0U);
	check_return(eid, fid, ALL_ONES, ALL_ONES, ALL_ONES,
		     BE_B5_SBI_ERR_NOT_SUPPORTED, 0U);
}

static void check_dbcn_write(be_u64 length, be_u64 gpa, be_u64 high,
			     be_u64 expected_pa, be_u64 expected_length)
{
	struct be_r4_frame frame = ecall(BE_B5_SBI_EID_DBCN,
					 BE_B5_SBI_DBCN_WRITE, length, gpa,
					 high);
	struct be_b5_result result = decide(&frame);

	CHECK(result.action == BE_B5_ACTION_CONSOLE_WRITE);
	CHECK(result.error == BE_B5_SBI_SUCCESS);
	CHECK(result.source_pa == expected_pa);
	CHECK(result.length == expected_length);
	CHECK(result.value == expected_length);
}

static void check_dbcn_refused(be_u64 length, be_u64 gpa, be_u64 high)
{
	check_return(BE_B5_SBI_EID_DBCN, BE_B5_SBI_DBCN_WRITE, length, gpa,
		     high, BE_B5_SBI_ERR_INVALID_PARAM, 0U);
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(BE_B5_SBI_EID_BASE == 0x10U);
	CHECK(BE_B5_SBI_EID_TIME == 0x54494d45U);
	CHECK(BE_B5_SBI_EID_DBCN == 0x4442434eU);
	CHECK(BE_B5_SBI_EID_SRST == 0x53525354U);
	CHECK(BE_B5_SBI_SPEC_VERSION == 0x2000000U);
	CHECK(BE_B5_SBI_IMPL_ID == ((be_u64)'B' << 8 | (be_u64)'E'));
	CHECK(BE_B5_SBI_IMPL_VERSION == 1U);
	CHECK(BE_B5_EXIT_BUDGET == 1024U);
	CHECK(BE_B5_DBCN_MAX_BYTES == 256U);
	CHECK(strcmp(BE_B5_GUEST_PREFIX, "BE_B5_GUEST: ") == 0);
	CHECK(strlen(BE_B5_GUEST_PREFIX) == BE_B5_GUEST_PREFIX_LENGTH);
	CHECK(BE_B5_TAGGED_CAPACITY == 3584U);
	CHECK(BE_B5_TAGGED_CAPACITY <= BE_PAGE_SIZE);
	CHECK(BE_B5_GPR_A2 == 11U);
	CHECK(BE_R4_GPR_A0 == 9U && BE_R4_GPR_A1 == 10U);
	CHECK(BE_R4_GPR_A6 == 15U && BE_R4_GPR_A7 == 16U);
	CHECK(sizeof(struct be_r4_frame) == 320U);
}

static void test_class_names(void)
{
	static const char *const names[] = {
		"none", "boot", "sstc", "controls", "interrupt",
		"guest-page-fault", "virtual-instruction",
		"illegal-instruction", "exception", "exit-budget", "resume",
		"console", "guest-failure", "shutdown-returned",
	};
	unsigned int index;

	SCENARIO();
	CHECK(BE_ARRAY_SIZE(names) == (be_size)BE_B5_CLASS_COUNT);
	for (index = 0U; index < BE_ARRAY_SIZE(names); ++index)
		CHECK(strcmp(be_b5_class_name((enum be_b5_class)index),
			     names[index]) == 0);
	CHECK(strcmp(be_b5_class_name(BE_B5_CLASS_COUNT), "invalid") == 0);
	CHECK(strcmp(be_b5_class_name((enum be_b5_class)99), "invalid") == 0);
}

static struct be_b5_controls armed_controls(void)
{
	return (struct be_b5_controls) {
		.hip = 0U,
		.hstatus = BE_U64_C(0x200300180),
		.hedeleg = 0U,
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
		.hgatp = BE_R3_MANAGEMENT_HGATP,
		.vsatp = 0U,
	};
}

static void test_controls(void)
{
	struct be_b5_controls controls = armed_controls();
	be_u64 *fields = (be_u64 *)(void *)&controls;
	be_size index;

	SCENARIO();
	CHECK(BE_B5_HSTATUS_GUEST_CONTROLS == 0x300180U);
	CHECK(BE_B5_HIDELEG_VSTI == 0x40U && BE_B5_HIE_VSTIE == 0x40U);
	CHECK(BE_B5_HCOUNTEREN_TM == 0x2U);
	CHECK(BE_B5_HENVCFG_STCE == BE_U64_C(0x8000000000000000));
	CHECK(BE_R3_MANAGEMENT_HGATP == BE_U64_C(0x8000000000102014));
	CHECK(sizeof(controls) == 15U * sizeof(be_u64));
	CHECK(be_b5_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP) == 1);
	CHECK(be_b5_controls_valid(&controls, BE_R3_PROTECTED_HGATP) == 0);
	CHECK(be_b5_controls_valid((const struct be_b5_controls *)0,
				   BE_R3_MANAGEMENT_HGATP) == 0);
	/* Any single field off its guest-run value fails. */
	for (index = 0U; index < sizeof(controls) / sizeof(be_u64); ++index) {
		unsigned int bit = 2U;

		if (index == 1U)
			bit = 22U;
		else if (index == 12U)
			bit = 1U;
		controls = armed_controls();
		fields[index] ^= BE_U64_C(1) << bit;
		CHECK(be_b5_controls_valid(&controls,
					   BE_R3_MANAGEMENT_HGATP) == 0);
	}
	/* hstatus is compared under the R3 control mask only. */
	controls = armed_controls();
	controls.hstatus |= BE_R3_HSTATUS_GVA;
	CHECK(be_b5_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP) == 1);
	controls.hstatus |= BE_R3_HSTATUS_VTSR;
	CHECK(be_b5_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP) == 0);
	controls = armed_controls();
	controls.hstatus &= ~BE_R3_HSTATUS_VTW;
	CHECK(be_b5_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP) == 0);
	controls = armed_controls();
	controls.hstatus |= BE_R3_HSTATUS_HU;
	CHECK(be_b5_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP) == 0);
	controls = armed_controls();
	controls.hstatus |= BE_U64_C(1) << 12;
	CHECK(be_b5_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP) == 0);
	/* Only VSTI is delegated, and only TM is opened. */
	controls = armed_controls();
	controls.hideleg = 0x444U;
	CHECK(be_b5_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP) == 0);
	controls = armed_controls();
	controls.hcounteren = 0x7U;
	CHECK(be_b5_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP) == 0);
	controls = armed_controls();
	controls.henvcfg |= 0x80U;
	CHECK(be_b5_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP) == 0);
	controls = armed_controls();
	controls.sstatus |= BE_R3_SSTATUS_SIE;
	CHECK(be_b5_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP) == 0);

	CHECK(be_b5_stce_class(BE_B5_HENVCFG_STCE) == BE_B5_CLASS_NONE);
	CHECK(be_b5_stce_class(0U) == BE_B5_CLASS_SSTC);
	CHECK(be_b5_stce_class(1U) == BE_B5_CLASS_SSTC);
	CHECK(be_b5_stce_class(ALL_ONES >> 1) == BE_B5_CLASS_SSTC);
	CHECK(be_b5_stce_class(BE_B5_HENVCFG_STCE | 1U) ==
	      BE_B5_CLASS_CONTROLS);
	CHECK(be_b5_stce_class(ALL_ONES) == BE_B5_CLASS_CONTROLS);
}

static void test_classify(void)
{
	be_u64 cause;

	SCENARIO();
	for (cause = 0U; cause < 64U; ++cause) {
		enum be_b5_class expected = BE_B5_CLASS_EXCEPTION;

		if (cause == 10U)
			expected = BE_B5_CLASS_NONE;
		else if (cause == 20U || cause == 21U || cause == 23U)
			expected = BE_B5_CLASS_GUEST_PAGE_FAULT;
		else if (cause == 22U)
			expected = BE_B5_CLASS_VIRTUAL_INSTRUCTION;
		else if (cause == 2U)
			expected = BE_B5_CLASS_ILLEGAL_INSTRUCTION;
		CHECK(be_b5_classify_cause(cause) == expected);
		CHECK(be_b5_classify_cause(BE_B5_SCAUSE_INTERRUPT | cause) ==
		      BE_B5_CLASS_INTERRUPT);
	}
	CHECK(be_b5_classify_cause(ALL_ONES) == BE_B5_CLASS_INTERRUPT);
	CHECK(be_b5_classify_cause(ALL_ONES >> 1) == BE_B5_CLASS_EXCEPTION);
	CHECK(be_b5_classify_cause(HIGH_BIT | 10U) == BE_B5_CLASS_EXCEPTION);
}

static void test_leaves(void)
{
	be_size index;

	SCENARIO();
	CHECK(r2_output.state == BE_R2_STATE_BUILT);
	CHECK(r2_output.results[0].hgatp == BE_R3_MANAGEMENT_HGATP);
	CHECK(management->count == BE_ARRAY_SIZE(expected_leaves));
	for (index = 0U; index < BE_ARRAY_SIZE(expected_leaves); ++index) {
		CHECK(management->leaves[index].gpa ==
		      expected_leaves[index].gpa);
		CHECK(management->leaves[index].pa ==
		      expected_leaves[index].pa);
		CHECK(management->leaves[index].rights ==
		      expected_leaves[index].rights);
	}
	/* The K3 backing addresses the plan's memory table names. */
	CHECK(management->leaves[0].pa == BE_U64_C(0x10202e000));
	CHECK(management->leaves[1].pa == BE_U64_C(0x102030000));
	CHECK(management->leaves[2].pa == BE_U64_C(0x102032000));
	CHECK(management->leaves[0].gpa == BE_U64_C(0x40000000));
	CHECK(management->leaves[1].gpa == BE_U64_C(0x40002000));
	CHECK(management->leaves[2].gpa == BE_U64_C(0x40010000));
}

static void test_base(void)
{
	static const be_u64 available[] = {
		BE_B5_SBI_EID_BASE, BE_B5_SBI_EID_TIME, BE_B5_SBI_EID_DBCN,
		BE_B5_SBI_EID_SRST,
	};
	static const be_u64 absent[] = {
		EID_HSM, EID_IPI, EID_RFENCE, EID_PMU, EID_SUSP, EID_CPPC,
		EID_NACL, EID_STA, EID_SSE, EID_FWFT, EID_DBTR, EID_MPXY,
		EID_UNASSIGNED, 0U, ALL_ONES, HIGH_BIT | BE_B5_SBI_EID_BASE,
		HIGH_BIT | BE_B5_SBI_EID_DBCN, BE_U64_C(0x08000000),
		BE_U64_C(0x09000000), BE_U64_C(0x0a000000),
	};
	be_size index;
	be_u64 legacy;

	SCENARIO();
	check_return(BE_B5_SBI_EID_BASE, 0U, 0U, 0U, 0U, 0, 0x2000000U);
	check_return(BE_B5_SBI_EID_BASE, 0U, ALL_ONES, 7U, 9U, 0, 0x2000000U);
	check_return(BE_B5_SBI_EID_BASE, 1U, 0U, 0U, 0U, 0, 0x4245U);
	check_return(BE_B5_SBI_EID_BASE, 2U, 0U, 0U, 0U, 0, 1U);
	check_return(BE_B5_SBI_EID_BASE, 4U, 0U, 0U, 0U, 0, 0U);
	check_return(BE_B5_SBI_EID_BASE, 5U, 0U, 0U, 0U, 0, 0U);
	check_return(BE_B5_SBI_EID_BASE, 6U, ALL_ONES, 0U, 0U, 0, 0U);
	for (index = 0U; index < BE_ARRAY_SIZE(available); ++index)
		check_return(BE_B5_SBI_EID_BASE, 3U, available[index], 0U, 0U,
			     0, 1U);
	for (index = 0U; index < BE_ARRAY_SIZE(absent); ++index)
		check_return(BE_B5_SBI_EID_BASE, 3U, absent[index], 0U, 0U, 0,
			     0U);
	for (legacy = 0U; legacy <= 0xfU; ++legacy)
		check_return(BE_B5_SBI_EID_BASE, 3U, legacy, 0U, 0U, 0, 0U);
	check_unsupported(BE_B5_SBI_EID_BASE, 7U);
	check_unsupported(BE_B5_SBI_EID_BASE, 8U);
	check_unsupported(BE_B5_SBI_EID_BASE, 0xffffffffU);
	check_unsupported(BE_B5_SBI_EID_BASE, HIGH_BIT);
	check_unsupported(BE_B5_SBI_EID_BASE, ALL_ONES);
}

static void test_unsupported(void)
{
	static const be_u64 eids[] = {
		EID_HSM, EID_IPI, EID_RFENCE, EID_PMU, EID_SUSP, EID_CPPC,
		EID_NACL, EID_STA, EID_SSE, EID_FWFT, EID_DBTR, EID_MPXY,
		EID_UNASSIGNED, BE_U64_C(0x08000000), BE_U64_C(0x09000000),
		BE_U64_C(0x0a000000), BE_U64_C(0x10) | HIGH_BIT,
		BE_B5_SBI_EID_TIME | HIGH_BIT, BE_B5_SBI_EID_DBCN | HIGH_BIT,
		BE_B5_SBI_EID_SRST | HIGH_BIT, ALL_ONES,
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
			     BE_B5_SBI_ERR_NOT_SUPPORTED, 0U);
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
		struct be_r4_frame frame = ecall(BE_B5_SBI_EID_TIME, 0U,
						 values[index], 5U, 6U);
		struct be_b5_result result = decide(&frame);

		CHECK(result.action == BE_B5_ACTION_SET_TIMER);
		CHECK(result.timer == values[index]);
		CHECK(result.error == BE_B5_SBI_SUCCESS);
		CHECK(result.value == 0U);
	}
	check_unsupported(BE_B5_SBI_EID_TIME, 1U);
	check_unsupported(BE_B5_SBI_EID_TIME, 2U);
	check_unsupported(BE_B5_SBI_EID_TIME, HIGH_BIT);
	check_unsupported(BE_B5_SBI_EID_TIME, ALL_ONES);
}

static void test_dbcn_leaf_edges(void)
{
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(expected_leaves); ++index) {
		be_u64 gpa = expected_leaves[index].gpa;
		be_u64 pa = expected_leaves[index].pa;

		/* First and last byte, whole page, and the 256-byte cap. */
		check_dbcn_write(1U, gpa, 0U, pa, 1U);
		check_dbcn_write(1U, gpa + 0xfffU, 0U, pa + 0xfffU, 1U);
		check_dbcn_write(16U, gpa + 0xff0U, 0U, pa + 0xff0U, 16U);
		check_dbcn_write(0x1000U, gpa, 0U, pa, 256U);
		check_dbcn_write(257U, gpa, 0U, pa, 256U);
		check_dbcn_write(256U, gpa + 0xf00U, 0U, pa + 0xf00U, 256U);
		check_dbcn_write(255U, gpa + 0x10U, 0U, pa + 0x10U, 255U);
		/* Crossing the end of the leaf. */
		check_dbcn_refused(2U, gpa + 0xfffU, 0U);
		check_dbcn_refused(0x1001U, gpa, 0U);
		check_dbcn_refused(0x1000U, gpa + 1U, 0U);
		check_dbcn_refused(32U, gpa + 0xff0U, 0U);
		/* Starting just before the leaf. */
		check_dbcn_refused(2U, gpa - 1U, 0U);
		check_dbcn_refused(1U, gpa - 1U, 0U);
		/* A nonzero high address word refuses even a valid range. */
		check_dbcn_refused(1U, gpa, 1U);
		check_dbcn_refused(1U, gpa, ALL_ONES);
		check_dbcn_refused(1U, gpa, BE_U64_C(1) << 63);
		/* The backing physical address is not a guest address. */
		check_dbcn_refused(1U, pa, 0U);
	}
}

static void test_dbcn_refusals(void)
{
	static const be_u64 unmapped[] = {
		BE_U64_C(0x40001000), BE_U64_C(0x40001ff8),
		BE_U64_C(0x40003000), BE_U64_C(0x40011000),
		BE_U64_C(0x3ffff000), BE_U64_C(0x40200000), 0U,
		BE_U64_C(0x102027000), BE_U64_C(0x10202b000),
		BE_U64_C(0x10200f000), ALL_ONES - 0xfffU,
	};
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(unmapped); ++index) {
		check_dbcn_refused(1U, unmapped[index], 0U);
		check_dbcn_refused(8U, unmapped[index], 0U);
	}
	/* The guest's crossing case: the end of the private page. */
	check_dbcn_refused(32U, BE_U64_C(0x40000ff0), 0U);
	/* Wrapping ranges. */
	check_dbcn_refused(ALL_ONES, BE_U64_C(0x40000000), 0U);
	check_dbcn_refused(ALL_ONES - 0x3fffffffU, BE_U64_C(0x40000000), 0U);
	check_dbcn_refused(2U, ALL_ONES, 0U);
	check_dbcn_refused(1U, ALL_ONES, 0U);
	check_dbcn_refused(BE_U64_C(0x1000), ALL_ONES - 0xffeU, 0U);
	/* Zero length returns 0, 0 without a range check... */
	check_return(BE_B5_SBI_EID_DBCN, 0U, 0U, BE_U64_C(0x40001000), 0U, 0,
		     0U);
	check_return(BE_B5_SBI_EID_DBCN, 0U, 0U, ALL_ONES, 0U, 0, 0U);
	check_return(BE_B5_SBI_EID_DBCN, 0U, 0U, BE_U64_C(0x40000000), 0U, 0,
		     0U);
	/* ...but never with a nonzero high word. */
	check_dbcn_refused(0U, BE_U64_C(0x40000000), 1U);
}

static void test_dbcn_leaf_sets(void)
{
	struct be_r2_leaf_set synthetic = { 0 };
	be_u64 pa = 0U;

	SCENARIO();
	CHECK(be_b5_translate_read(management, BE_U64_C(0x40000010), 4U,
				   &pa) == 1);
	CHECK(pa == BE_U64_C(0x10202e010));
	pa = 7U;
	CHECK(be_b5_translate_read(management, BE_U64_C(0x40001000), 4U,
				   &pa) == 0);
	CHECK(pa == 7U);
	CHECK(be_b5_translate_read(management, BE_U64_C(0x40000000), 0U,
				   &pa) == 0);
	CHECK(be_b5_translate_read((const struct be_r2_leaf_set *)0,
				   BE_U64_C(0x40000000), 4U, &pa) == 0);
	CHECK(be_b5_translate_read(management, BE_U64_C(0x40000000), 4U,
				   (be_u64 *)0) == 0);

	/* Write-only and execute-only leaves are not readable. */
	synthetic.count = 2U;
	synthetic.leaves[0] = (struct be_r2_leaf){ BE_U64_C(0x40000000),
		BE_U64_C(0x10202e000), BE_RIGHT_WRITE };
	synthetic.leaves[1] = (struct be_r2_leaf){ BE_U64_C(0x40010000),
		BE_U64_C(0x102032000), BE_RIGHT_EXECUTE };
	CHECK(be_b5_translate_read(&synthetic, BE_U64_C(0x40000000), 1U,
				   &pa) == 0);
	CHECK(be_b5_translate_read(&synthetic, BE_U64_C(0x40010000), 1U,
				   &pa) == 0);
	/* Read-only is readable. */
	synthetic.leaves[1].rights = BE_RIGHT_READ;
	CHECK(be_b5_translate_read(&synthetic, BE_U64_C(0x40010ffc), 4U,
				   &pa) == 1);
	CHECK(pa == BE_U64_C(0x102032ffc));
	/* A misaligned leaf is never trusted. */
	synthetic.leaves[1].gpa = BE_U64_C(0x40010800);
	CHECK(be_b5_translate_read(&synthetic, BE_U64_C(0x40010800), 4U,
				   &pa) == 0);
	synthetic.leaves[1].gpa = BE_U64_C(0x40010000);
	synthetic.leaves[1].pa = BE_U64_C(0x102032010);
	CHECK(be_b5_translate_read(&synthetic, BE_U64_C(0x40010000), 4U,
				   &pa) == 0);
	/* An over-long leaf set fails closed. */
	synthetic.leaves[1].pa = BE_U64_C(0x102032000);
	synthetic.count = BE_MAX_MAPPINGS + 1U;
	CHECK(be_b5_translate_read(&synthetic, BE_U64_C(0x40010000), 4U,
				   &pa) == 0);
	synthetic.count = 0U;
	CHECK(be_b5_translate_read(&synthetic, BE_U64_C(0x40010000), 4U,
				   &pa) == 0);
}

static void test_dbcn_other(void)
{
	struct be_r4_frame frame;
	struct be_b5_result result;
	be_u64 byte;

	SCENARIO();
	/* Console read is refused whatever the range. */
	check_return(BE_B5_SBI_EID_DBCN, 1U, 4U, BE_U64_C(0x40000000), 0U,
		     BE_B5_SBI_ERR_DENIED, 0U);
	check_return(BE_B5_SBI_EID_DBCN, 1U, 0U, 0U, 0U,
		     BE_B5_SBI_ERR_DENIED, 0U);
	check_return(BE_B5_SBI_EID_DBCN, 1U, ALL_ONES, ALL_ONES, ALL_ONES,
		     BE_B5_SBI_ERR_DENIED, 0U);
	/* Write byte takes the low byte of a0. */
	for (byte = 0U; byte < 0x100U; ++byte) {
		frame = ecall(BE_B5_SBI_EID_DBCN, 2U, byte | 0xab00U, 0U, 0U);
		result = decide(&frame);
		CHECK(result.action == BE_B5_ACTION_CONSOLE_BYTE);
		CHECK(result.byte == byte);
		CHECK(result.error == BE_B5_SBI_SUCCESS);
		CHECK(result.value == 0U);
	}
	frame = ecall(BE_B5_SBI_EID_DBCN, 2U, ALL_ONES, 1U, 2U);
	result = decide(&frame);
	CHECK(result.action == BE_B5_ACTION_CONSOLE_BYTE);
	CHECK(result.byte == 0xffU);
	check_unsupported(BE_B5_SBI_EID_DBCN, 3U);
	check_unsupported(BE_B5_SBI_EID_DBCN, 4U);
	check_unsupported(BE_B5_SBI_EID_DBCN, HIGH_BIT);
	check_unsupported(BE_B5_SBI_EID_DBCN, ALL_ONES);
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
			struct be_b5_state state = BE_B5_STATE_INITIALIZER;
			struct be_r4_frame frame = ecall(BE_B5_SBI_EID_SRST,
							 0U, type, reason, 0U);
			struct be_b5_result result;

			(void)be_b5_handle_exit(&state, management, &frame,
						&result);
			if (type > 2U || reason > 1U) {
				CHECK(result.action == BE_B5_ACTION_RETURN);
				CHECK(result.error ==
				      BE_B5_SBI_ERR_INVALID_PARAM);
				CHECK(state.phase == BE_B5_PHASE_RUNNING);
			} else if (type != 0U) {
				CHECK(result.action == BE_B5_ACTION_RETURN);
				CHECK(result.error ==
				      BE_B5_SBI_ERR_NOT_SUPPORTED);
				CHECK(state.phase == BE_B5_PHASE_RUNNING);
			} else if (reason == 0U) {
				CHECK(result.action == BE_B5_ACTION_SHUTDOWN);
				CHECK(state.phase == BE_B5_PHASE_SHUTDOWN);
				CHECK(result.failure == BE_B5_CLASS_NONE);
			} else {
				CHECK(result.action ==
				      BE_B5_ACTION_GUEST_FAILURE);
				CHECK(state.phase == BE_B5_PHASE_FAILED);
				CHECK(state.failure ==
				      BE_B5_CLASS_GUEST_FAILURE);
				CHECK(result.failure ==
				      BE_B5_CLASS_GUEST_FAILURE);
			}
			CHECK(result.value == 0U);
			CHECK(state.exits == 1U);
		}
	}
	check_unsupported(BE_B5_SBI_EID_SRST, 1U);
	check_unsupported(BE_B5_SBI_EID_SRST, 2U);
	check_unsupported(BE_B5_SBI_EID_SRST, HIGH_BIT);
	check_unsupported(BE_B5_SBI_EID_SRST, ALL_ONES);
}

static void test_after_shutdown(void)
{
	struct be_b5_state state = BE_B5_STATE_INITIALIZER;
	struct be_r4_frame frame = ecall(BE_B5_SBI_EID_SRST, 0U, 0U, 0U, 0U);
	struct be_r4_frame base = ecall(BE_B5_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b5_result result;

	SCENARIO();
	CHECK(be_b5_handle_exit(&state, management, &frame, &result) ==
	      BE_B5_ACTION_SHUTDOWN);
	CHECK(be_b5_handle_exit(&state, management, &base, &result) ==
	      BE_B5_ACTION_TERMINAL);
	CHECK(result.failure == BE_B5_CLASS_EXCEPTION);
	CHECK(state.phase == BE_B5_PHASE_FAILED);
	CHECK(state.exits == 1U);

	state = (struct be_b5_state)BE_B5_STATE_INITIALIZER;
	frame = ecall(BE_B5_SBI_EID_SRST, 0U, 0U, 1U, 0U);
	CHECK(be_b5_handle_exit(&state, management, &frame, &result) ==
	      BE_B5_ACTION_GUEST_FAILURE);
	CHECK(be_b5_handle_exit(&state, management, &base, &result) ==
	      BE_B5_ACTION_TERMINAL);
	CHECK(result.failure == BE_B5_CLASS_GUEST_FAILURE);
	CHECK(state.failure == BE_B5_CLASS_GUEST_FAILURE);
}

static void test_exit_budget(void)
{
	struct be_b5_state state = BE_B5_STATE_INITIALIZER;
	struct be_r4_frame frame = ecall(BE_B5_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b5_result result;
	unsigned int count;

	SCENARIO();
	for (count = 1U; count <= BE_B5_EXIT_BUDGET; ++count) {
		CHECK(be_b5_handle_exit(&state, management, &frame, &result) ==
		      BE_B5_ACTION_RETURN);
		CHECK(state.exits == count);
	}
	CHECK(state.phase == BE_B5_PHASE_RUNNING);
	CHECK(be_b5_handle_exit(&state, management, &frame, &result) ==
	      BE_B5_ACTION_TERMINAL);
	CHECK(result.failure == BE_B5_CLASS_EXIT_BUDGET);
	CHECK(state.phase == BE_B5_PHASE_FAILED);
	CHECK(state.exits == BE_B5_EXIT_BUDGET + 1U);
	CHECK(be_b5_handle_exit(&state, management, &frame, &result) ==
	      BE_B5_ACTION_TERMINAL);
	CHECK(result.failure == BE_B5_CLASS_EXIT_BUDGET);
	CHECK(state.exits == BE_B5_EXIT_BUDGET + 1U);

	/* The budget counts every exit, whatever its class. */
	state = (struct be_b5_state)BE_B5_STATE_INITIALIZER;
	state.exits = BE_B5_EXIT_BUDGET;
	frame = frame_with(BE_B5_SCAUSE_LOAD_GUEST_PAGE_FAULT, ECALL_PC);
	CHECK(be_b5_handle_exit(&state, management, &frame, &result) ==
	      BE_B5_ACTION_TERMINAL);
	CHECK(result.failure == BE_B5_CLASS_EXIT_BUDGET);
}

static void test_terminal_exits(void)
{
	static const struct {
		be_u64 scause;
		enum be_b5_class failure;
	} exits[] = {
		{ BE_B5_SCAUSE_INTERRUPT | 5U, BE_B5_CLASS_INTERRUPT },
		{ BE_B5_SCAUSE_INTERRUPT | 6U, BE_B5_CLASS_INTERRUPT },
		{ BE_B5_SCAUSE_INTERRUPT | 9U, BE_B5_CLASS_INTERRUPT },
		{ BE_B5_SCAUSE_INTERRUPT | 10U, BE_B5_CLASS_INTERRUPT },
		{ 20U, BE_B5_CLASS_GUEST_PAGE_FAULT },
		{ 21U, BE_B5_CLASS_GUEST_PAGE_FAULT },
		{ 23U, BE_B5_CLASS_GUEST_PAGE_FAULT },
		{ 22U, BE_B5_CLASS_VIRTUAL_INSTRUCTION },
		{ 2U, BE_B5_CLASS_ILLEGAL_INSTRUCTION },
		{ 0U, BE_B5_CLASS_EXCEPTION },
		{ 3U, BE_B5_CLASS_EXCEPTION },
		{ 4U, BE_B5_CLASS_EXCEPTION },
		{ 8U, BE_B5_CLASS_EXCEPTION },
		{ 9U, BE_B5_CLASS_EXCEPTION },
		{ 12U, BE_B5_CLASS_EXCEPTION },
		{ 13U, BE_B5_CLASS_EXCEPTION },
		{ 15U, BE_B5_CLASS_EXCEPTION },
		{ 24U, BE_B5_CLASS_EXCEPTION },
	};
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(exits); ++index) {
		struct be_b5_state state = BE_B5_STATE_INITIALIZER;
		struct be_r4_frame frame = frame_with(exits[index].scause,
						      ECALL_PC);
		struct be_r4_frame base = ecall(BE_B5_SBI_EID_BASE, 0U, 0U, 0U,
						0U);
		struct be_b5_result result;

		/* The registers of an SBI call do not matter here. */
		frame.gpr[BE_R4_GPR_A7] = BE_B5_SBI_EID_BASE;
		frame.gpr[BE_R4_GPR_A6] = 0U;
		CHECK(be_b5_handle_exit(&state, management, &frame, &result) ==
		      BE_B5_ACTION_TERMINAL);
		CHECK(result.failure == exits[index].failure);
		CHECK(state.phase == BE_B5_PHASE_FAILED);
		CHECK(state.failure == exits[index].failure);
		CHECK(state.exits == 1U);
		CHECK(be_b5_handle_exit(&state, management, &base, &result) ==
		      BE_B5_ACTION_TERMINAL);
		CHECK(result.failure == exits[index].failure);
		CHECK(state.exits == 1U);
	}
}

static void test_frame_integrity(void)
{
	struct be_b5_state state = BE_B5_STATE_INITIALIZER;
	struct be_r4_frame frame = ecall(BE_B5_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_b5_result result;

	SCENARIO();
	frame.reserved = 1U;
	CHECK(be_b5_handle_exit(&state, management, &frame, &result) ==
	      BE_B5_ACTION_TERMINAL);
	CHECK(result.failure == BE_B5_CLASS_EXCEPTION);

	state = (struct be_b5_state)BE_B5_STATE_INITIALIZER;
	frame = ecall(BE_B5_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	frame.sepc = ALL_ONES - 3U;
	CHECK(be_b5_handle_exit(&state, management, &frame, &result) ==
	      BE_B5_ACTION_TERMINAL);
	CHECK(result.failure == BE_B5_CLASS_RESUME);

	state = (struct be_b5_state)BE_B5_STATE_INITIALIZER;
	frame.sepc = ALL_ONES - 4U;
	CHECK(be_b5_handle_exit(&state, management, &frame, &result) ==
	      BE_B5_ACTION_RETURN);
	CHECK(result.resume_pc == ALL_ONES);

	state = (struct be_b5_state)BE_B5_STATE_INITIALIZER;
	CHECK(be_b5_handle_exit(&state, (const struct be_r2_leaf_set *)0,
				&frame, &result) == BE_B5_ACTION_TERMINAL);
	CHECK(result.failure == BE_B5_CLASS_EXCEPTION);
	state = (struct be_b5_state)BE_B5_STATE_INITIALIZER;
	CHECK(be_b5_handle_exit(&state, management,
				(const struct be_r4_frame *)0, &result) ==
	      BE_B5_ACTION_TERMINAL);
	CHECK(state.phase == BE_B5_PHASE_FAILED);
	state = (struct be_b5_state)BE_B5_STATE_INITIALIZER;
	CHECK(be_b5_handle_exit(&state, management, &frame,
				(struct be_b5_result *)0) ==
	      BE_B5_ACTION_TERMINAL);
	CHECK(state.phase == BE_B5_PHASE_FAILED);
	CHECK(be_b5_handle_exit((struct be_b5_state *)0, management, &frame,
				&result) == BE_B5_ACTION_TERMINAL);
	CHECK(result.failure == BE_B5_CLASS_EXCEPTION);

	/* The sticky class: the first failure is kept. */
	state = (struct be_b5_state)BE_B5_STATE_INITIALIZER;
	CHECK(be_b5_fail(&state, BE_B5_CLASS_SSTC) == BE_B5_CLASS_SSTC);
	CHECK(be_b5_fail(&state, BE_B5_CLASS_CONSOLE) == BE_B5_CLASS_SSTC);
	state = (struct be_b5_state)BE_B5_STATE_INITIALIZER;
	CHECK(be_b5_fail(&state, BE_B5_CLASS_NONE) == BE_B5_CLASS_EXCEPTION);
	CHECK(be_b5_fail((struct be_b5_state *)0, BE_B5_CLASS_BOOT) ==
	      BE_B5_CLASS_BOOT);
	state = (struct be_b5_state)BE_B5_STATE_INITIALIZER;
	CHECK(be_b5_fail(&state, BE_B5_CLASS_COUNT) == BE_B5_CLASS_EXCEPTION);
}

static void test_apply_return(void)
{
	struct be_r4_frame frame = ecall(BE_B5_SBI_EID_BASE, 7U, 1U, 2U, 3U);
	struct be_r4_frame before = frame;
	struct be_b5_result result = decide(&frame);
	be_size index;

	SCENARIO();
	CHECK(result.error == BE_B5_SBI_ERR_NOT_SUPPORTED);
	be_b5_apply_return(&frame, &result);
	CHECK(frame.gpr[BE_R4_GPR_A0] == (be_u64)-2L);
	CHECK(frame.gpr[BE_R4_GPR_A1] == 0U);
	CHECK(frame.sepc == ECALL_PC + 4U);
	for (index = 0U; index < BE_ARRAY_SIZE(frame.gpr); ++index) {
		if (index == BE_R4_GPR_A0 || index == BE_R4_GPR_A1)
			continue;
		CHECK(frame.gpr[index] == before.gpr[index]);
	}
	CHECK(frame.vstvec == before.vstvec && frame.vsepc == before.vsepc);
	CHECK(frame.vscause == before.vscause &&
	      frame.vstval == before.vstval);
	CHECK(frame.scause == before.scause && frame.stval == before.stval);
	CHECK(frame.htval == before.htval &&
	      frame.reserved == before.reserved);
	be_b5_apply_return((struct be_r4_frame *)0, &result);
	be_b5_apply_return(&frame, (const struct be_b5_result *)0);
	CHECK(frame.sepc == ECALL_PC + 4U);
}

static be_u64 tag(struct be_b5_console *console, const char *text,
		  char *output)
{
	return be_b5_console_tag(console, (const be_u8 *)text, strlen(text),
				 output, BE_B5_TAGGED_CAPACITY);
}

static void test_console_tag(void)
{
	static char output[BE_B5_TAGGED_CAPACITY + 16U];
	struct be_b5_console console = { 0 };
	be_u8 input[BE_B5_DBCN_MAX_BYTES + 1U];
	be_u64 length;
	be_size index;

	SCENARIO();
	length = tag(&console, "01 START hart=0x0 dtb=0x0\n", output);
	CHECK(length == 13U + 26U);
	CHECK(memcmp(output, "BE_B5_GUEST: 01 START hart=0x0 dtb=0x0\n",
		     (size_t)length) == 0);
	CHECK(console.line_open == 0U);

	/* A line split across calls has one prefix. */
	length = tag(&console, "09 RES", output);
	CHECK(length == 13U + 6U);
	CHECK(memcmp(output, "BE_B5_GUEST: 09 RES", (size_t)length) == 0);
	CHECK(console.line_open == 1U);
	length = tag(&console, "ULT pass\n", output);
	CHECK(length == 9U);
	CHECK(memcmp(output, "ULT pass\n", 9U) == 0);
	CHECK(console.line_open == 0U);

	/* A bare newline is an empty guest line. */
	length = tag(&console, "\n", output);
	CHECK(length == 14U);
	CHECK(memcmp(output, "BE_B5_GUEST: \n", 14U) == 0);

	/* Forged evidence lines stay guest lines. */
	length = tag(&console, "x\nBE_R3:01 BOOT_VALIDATED\n", output);
	CHECK(length == 13U + 2U + 13U + 24U);
	CHECK(memcmp(output,
		     "BE_B5_GUEST: x\nBE_B5_GUEST: BE_R3:01 BOOT_VALIDATED\n",
		     (size_t)length) == 0);
	length = tag(&console, "\rBE_B5:06 SHUTDOWN type=0 reason=0\n",
		     output);
	CHECK(memcmp(output,
		     "BE_B5_GUEST: ?BE_B5:06 SHUTDOWN type=0 reason=0\n",
		     (size_t)length) == 0);

	/* Every byte value: printable ASCII and LF pass, the rest is '?'. */
	for (index = 0U; index < 256U; ++index) {
		be_u8 byte = (be_u8)index;

		console.line_open = 1U;
		length = be_b5_console_tag(&console, &byte, 1U, output,
					   BE_B5_TAGGED_CAPACITY);
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
	length = be_b5_console_tag(&console, input, BE_B5_DBCN_MAX_BYTES,
				   output, BE_B5_TAGGED_CAPACITY);
	CHECK(length == BE_B5_TAGGED_CAPACITY);
	for (index = 0U; index < BE_B5_DBCN_MAX_BYTES; ++index)
		CHECK(memcmp(output + index * 14U, "BE_B5_GUEST: \n", 14U) ==
		      0);

	/* Invalid requests change nothing. */
	console.line_open = 0U;
	CHECK(be_b5_console_tag(&console, input, BE_B5_DBCN_MAX_BYTES + 1U,
				output, BE_B5_TAGGED_CAPACITY) ==
	      BE_B5_TAG_INVALID);
	CHECK(be_b5_console_tag(&console, input, 1U, output,
				BE_B5_TAGGED_CAPACITY - 1U) ==
	      BE_B5_TAG_INVALID);
	CHECK(be_b5_console_tag((struct be_b5_console *)0, input, 1U, output,
				BE_B5_TAGGED_CAPACITY) == BE_B5_TAG_INVALID);
	CHECK(be_b5_console_tag(&console, (const be_u8 *)0, 1U, output,
				BE_B5_TAGGED_CAPACITY) == BE_B5_TAG_INVALID);
	CHECK(be_b5_console_tag(&console, input, 1U, (char *)0,
				BE_B5_TAGGED_CAPACITY) == BE_B5_TAG_INVALID);
	CHECK(console.line_open == 0U);
	CHECK(be_b5_console_tag(&console, input, 0U, output,
				BE_B5_TAGGED_CAPACITY) == 0U);
	CHECK(console.line_open == 0U);

	/* A monitor line first ends an open guest line. */
	CHECK(be_b5_console_close(&console) == 0U);
	(void)tag(&console, "partial", output);
	CHECK(be_b5_console_close(&console) == 1U);
	CHECK(console.line_open == 0U);
	CHECK(be_b5_console_close(&console) == 0U);
	CHECK(be_b5_console_close((struct be_b5_console *)0) == 0U);
	length = tag(&console, "next\n", output);
	CHECK(memcmp(output, "BE_B5_GUEST: next\n", (size_t)length) == 0);
}

static int line_is(const struct be_b5_line *line, const char *text)
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
		{ 0x40U, "0x40", "64" },
		{ 55U, "0x37", "55" },
		{ 1024U, "0x400", "1024" },
		{ 0x4245U, "0x4245", "16965" },
		{ 0x300180U, "0x300180", "3146112" },
		{ 0x2000000U, "0x2000000", "33554432" },
		{ 0x40010000U, "0x40010000", "1073807360" },
		{ BE_U64_C(0x8000000000000000), "0x8000000000000000",
		  "9223372036854775808" },
		{ BE_U64_C(0x8000000000000005), "0x8000000000000005",
		  "9223372036854775813" },
		{ ALL_ONES, "0xffffffffffffffff", "18446744073709551615" },
	};
	struct be_b5_line line;
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(values); ++index) {
		be_b5_line_reset(&line);
		be_b5_line_hex(&line, values[index].value);
		CHECK(line_is(&line, values[index].hex));
		be_b5_line_reset(&line);
		be_b5_line_decimal(&line, values[index].value);
		CHECK(line_is(&line, values[index].decimal));
	}

	/* Plan markers composed from fixed text and values. */
	be_b5_line_reset(&line);
	be_b5_line_text(&line, "BE_B5:01 SSTC_STCE_READBACK henvcfg=");
	be_b5_line_hex(&line, BE_U64_C(1) << 63);
	be_b5_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_B5:01 SSTC_STCE_READBACK "
		      "henvcfg=0x8000000000000000\n"));
	be_b5_line_reset(&line);
	be_b5_line_text(&line,
			"BE_B5:02 GUEST_CONTROLS_CHECKED hstatus_controls=");
	be_b5_line_hex(&line, 0x300180U);
	be_b5_line_text(&line, " hideleg=");
	be_b5_line_hex(&line, 0x40U);
	be_b5_line_text(&line, " hcounteren=");
	be_b5_line_hex(&line, 0x2U);
	be_b5_line_text(&line, " vstimecmp=");
	be_b5_line_hex(&line, ALL_ONES);
	be_b5_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_B5:02 GUEST_CONTROLS_CHECKED "
		      "hstatus_controls=0x300180 hideleg=0x40 "
		      "hcounteren=0x2 vstimecmp=0xffffffffffffffff\n"));
	be_b5_line_reset(&line);
	be_b5_line_text(&line, "BE_B5:05 GUEST_SHUTDOWN type=0 reason=0 "
			"exits=");
	be_b5_line_decimal(&line, 55U);
	CHECK(line_is(&line, "BE_B5:05 GUEST_SHUTDOWN type=0 reason=0 "
		      "exits=55"));

	/* Overflow is sticky and makes the line unusable. */
	be_b5_line_reset(&line);
	for (index = 0U; index < BE_B5_LINE_CAPACITY; ++index)
		be_b5_line_text(&line, "x");
	CHECK(line.length == BE_B5_LINE_CAPACITY && line.overflow == 0U);
	be_b5_line_text(&line, "y");
	CHECK(line.overflow == 1U);
	CHECK(line.length == BE_B5_LINE_CAPACITY);
	be_b5_line_reset(&line);
	CHECK(line.length == 0U && line.overflow == 0U);
	be_b5_line_text(&line, (const char *)0);
	CHECK(line.overflow == 1U);
	be_b5_line_reset(&line);
	for (index = 0U; index < 8U; ++index)
		be_b5_line_hex(&line, ALL_ONES);
	CHECK(line.length == 8U * 18U && line.overflow == 0U);
	be_b5_line_hex(&line, ALL_ONES);
	CHECK(line.overflow == 1U);
	CHECK(line.length == BE_B5_LINE_CAPACITY);
	be_b5_line_reset((struct be_b5_line *)0);
	be_b5_line_text((struct be_b5_line *)0, "x");
	be_b5_line_hex((struct be_b5_line *)0, 1U);
	be_b5_line_decimal((struct be_b5_line *)0, 1U);
}

/* The guest's pass run, call by call, as guest/guest.c makes it. */
static void test_guest_sequence(void)
{
	struct be_b5_state state = BE_B5_STATE_INITIALIZER;
	struct be_b5_result result;
	struct be_r4_frame frame;
	unsigned int count;
	unsigned int exits = 0U;

#define STEP(eid, fid, a0, a1, a2, action) \
	do { \
		frame = ecall(eid, fid, a0, a1, a2); \
		CHECK(be_b5_handle_exit(&state, management, &frame, \
					&result) == (action)); \
		++exits; \
	} while (0)
#define LINE() STEP(BE_B5_SBI_EID_DBCN, 0U, 40U, BE_U64_C(0x40000100), \
		    0U, BE_B5_ACTION_CONSOLE_WRITE)

	SCENARIO();
	LINE();
	for (count = 0U; count < 6U; ++count)
		STEP(BE_B5_SBI_EID_BASE, (be_u64)count == 3U ? 4U : count, 0U,
		     0U, 0U, BE_B5_ACTION_RETURN);
	LINE();
	for (count = 0U; count < 8U; ++count)
		STEP(BE_B5_SBI_EID_BASE, 3U, count, 0U, 0U,
		     BE_B5_ACTION_RETURN);
	LINE();
	STEP(EID_UNASSIGNED, 0U, 0U, 0U, 0U, BE_B5_ACTION_RETURN);
	STEP(BE_B5_SBI_EID_BASE, 7U, 0U, 0U, 0U, BE_B5_ACTION_RETURN);
	STEP(1U, 0U, 'x', 0U, 0U, BE_B5_ACTION_RETURN);
	LINE();
	STEP(BE_B5_SBI_EID_DBCN, 0U, 8U, BE_U64_C(0x40001000), 0U,
	     BE_B5_ACTION_RETURN);
	STEP(BE_B5_SBI_EID_DBCN, 0U, 32U, BE_U64_C(0x40000ff0), 0U,
	     BE_B5_ACTION_RETURN);
	STEP(BE_B5_SBI_EID_DBCN, 0U, 4U, BE_U64_C(0x40000000), 1U,
	     BE_B5_ACTION_RETURN);
	STEP(BE_B5_SBI_EID_DBCN, 0U, ALL_ONES, BE_U64_C(0x40000000), 0U,
	     BE_B5_ACTION_RETURN);
	STEP(BE_B5_SBI_EID_DBCN, 1U, 4U, BE_U64_C(0x40000000), 0U,
	     BE_B5_ACTION_RETURN);
	LINE();
	for (count = 0U; count < 17U; ++count)
		STEP(BE_B5_SBI_EID_DBCN, 2U, 'o', 0U, 0U,
		     BE_B5_ACTION_CONSOLE_BYTE);
	STEP(BE_B5_SBI_EID_SRST, 0U, 3U, 0U, 0U, BE_B5_ACTION_RETURN);
	STEP(BE_B5_SBI_EID_SRST, 0U, 0U, 2U, 0U, BE_B5_ACTION_RETURN);
	STEP(BE_B5_SBI_EID_SRST, 0U, 1U, 0U, 0U, BE_B5_ACTION_RETURN);
	LINE();
	STEP(BE_B5_SBI_EID_TIME, 0U, 0x10000U, 0U, 0U,
	     BE_B5_ACTION_SET_TIMER);
	STEP(BE_B5_SBI_EID_TIME, 0U, ALL_ONES, 0U, 0U,
	     BE_B5_ACTION_SET_TIMER);
	LINE();
	LINE();
	CHECK(state.phase == BE_B5_PHASE_RUNNING);
	STEP(BE_B5_SBI_EID_SRST, 0U, 0U, 0U, 0U, BE_B5_ACTION_SHUTDOWN);
	CHECK(state.phase == BE_B5_PHASE_SHUTDOWN);
	CHECK(state.exits == exits);
	CHECK(state.exits < BE_B5_EXIT_BUDGET);
#undef LINE
#undef STEP
}

static void print_count(const char *label, unsigned long value)
{
	printf("%s%lu\n", label, value);
}

int main(void)
{
	build_leaves();
	test_constants();
	test_class_names();
	test_controls();
	test_classify();
	test_leaves();
	test_base();
	test_unsupported();
	test_time();
	test_dbcn_leaf_edges();
	test_dbcn_refusals();
	test_dbcn_leaf_sets();
	test_dbcn_other();
	test_srst_grid();
	test_after_shutdown();
	test_exit_budget();
	test_terminal_exits();
	test_frame_integrity();
	test_apply_return();
	test_console_tag();
	test_line_builder();
	test_guest_sequence();

	puts("BE_B5_CHECK: PASS");
	print_count("BE_B5_CHECK: scenarios=", scenarios);
	print_count("BE_B5_CHECK: assertions=", assertions);
	return 0;
}
