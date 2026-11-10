// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the MVP guest SBI core: every row of the
 *          plan's SBI table (version 3), the DBCN range check at each
 *          window's edges and leaf boundaries, the SRST type and reason grid
 *          with a shutdown that stops only the calling domain and terminal
 *          reboots, TIME values, exit classes, the IPI class (the
 *          supervisor software interrupt, from VS or VU) and B7's wfi and
 *          slice exits now terminal, each domain's exit ceiling, per-hart
 *          counters, the frame return and the first-entry frame, the guest
 *          controls (SSIE, VTW clear), the per-hart line console and its
 *          LINE records (CR drop, byte filter, full-buffer split, flush, a
 *          full ring, and two harts whose lines never mix), the IPI's PING
 *          and PONG (empty inbound ring, unknown record, malformed ring, full
 *          outbound ring), the READY, ENTERED, SHUTDOWN, and FAIL records,
 *          a failed domain hart's wait for hart 0's ACK, whose window
 *          restarts on hart 0's progress through the outbound ring's tail
 *          (Q10, Plan revision M1-B), with the board's backlog replayed,
 *          the denial action in an image that accepts denials and the
 *          terminal guest-page fault in one that does not, the counters'
 *          sum (exits = sbi + ipi + denials), the DENIAL record, its
 *          refusals and a full ring, and hart 0's loop reconciling
 *          SHUTDOWN's denial word (planning/mvp-m1-plan.md, "The denial
 *          path"), the per-domain CSR set and SPP logic, the firmware HSM
 *          and IPI result checks, BE_MVP:02's census of the other harts
 *          (Plan revision M0-A.2), the monitor line builder, and replays of
 *          the research reference boot's SBI call census for each domain
 *          hart. The management extension (planning/mvp-m2-plan.md, Q3,
 *          Q14, and Q15): be_mvp_mgmt_decide() over every row of Instance
 *          3's grant in every target state, self-targets, targets and
 *          requesters that are no domain, other functions, and other
 *          tables; the extension absent, with version 3, from an image
 *          that does not accept it, and present, with version 4, in one
 *          that does; the calls counted in mgmt and the counters' sum; the
 *          MGMT_REQUEST, MGMT_RESULT, PAUSE, TERMINATE, PAUSED, and
 *          TERMINATED records and their refusals; the requester's wait in
 *          HS, serving PINGs; the paused and terminated waits; SHUTDOWN's
 *          management word; and hart 0's loop taking each record.
 * Trust:   host evidence only. No CSR, guest entry, IPI, second hart, QEMU,
 *          or hardware behaviour is exercised. The windows and channel
 *          leaves come from the MVP G-stage builder and walker, run in host
 *          memory; the rings and hart 0's records from the MVP ring and
 *          hart modules.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, planning/mvp-m1-plan.md,
 *          and planning/mvp-m2-plan.md).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mvp.h"
#include "mvp-hart.h"
#include "mvp-ring.h"
#include "mvp-sbi.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_SBI_CHECK: assertion failed: %s:%d: %s\n", \
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
#define SSI			(BE_U64_C(1) << 63 | 1U)
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
/*
 * The arming values the controls tests expect, per monitor variant, as
 * literals of their own, not mvp.h's: hedeleg 0xb15d holding 0xb10c
 * (WARL), a WARL reading 0xb15c, and the armed henvcfg STCE only.
 * beryllium-cheri: in the CHERI-aware monitor (BE_MVP_CHERI), hedeleg
 * delegates cause 28, CHERI v0.9.3's CHERI fault, too, and the armed
 * henvcfg holds CRE, CHERI's enable for VS-mode, beside STCE.
 */
#ifdef BE_MVP_CHERI
#define ARMED_HEDELEG		0x1000b15dU
#define ARMED_HEDELEG_REQUIRED	0x1000b10cU
#define ARMED_HEDELEG_WARL	0x1000b15cU
#define ARMED_HENVCFG		BE_U64_C(0x8000000010000000)
#else
#define ARMED_HEDELEG		0xb15dU
#define ARMED_HEDELEG_REQUIRED	0xb10cU
#define ARMED_HEDELEG_WARL	0xb15cU
#define ARMED_HENVCFG		BE_U64_C(0x8000000000000000)
#endif

static be_u8 pool[BE_MVP_GSTAGE_POOL_BYTES];
static struct be_mvp_gstage_map windows[2];
/* G0's window; most single-domain cases run as G0. */
#define window windows[0]
/* A root without a channel page: M0's, and every case that needs none. */
static const struct be_mvp_gstage_leaves no_leaf;
/*
 * te-poc's channel record (planning/mvp-m1-plan.md, Q1), and each domain's
 * walked leaf of it, as page 0 of its leaves: G0 writes, G1 reads.
 */
static const struct be_mvp_gstage_channel channel = {
	BE_MVP_CHANNEL_GPA, BE_MVP_CHANNEL_HPA, BE_MVP_CHANNEL_BYTES, 0U, 1U,
	BE_MVP_GSTAGE_RIGHT_READ | BE_MVP_GSTAGE_RIGHT_WRITE,
	BE_MVP_GSTAGE_RIGHT_READ,
};
static struct be_mvp_gstage_leaves leaves[2];

static void build_window(void)
{
	struct be_mvp_gstage_desc desc[2] = {
		{ BE_MVP_GUEST_GPA, BE_MVP_G0_HPA, BE_MVP_GUEST_BYTES,
		  BE_MVP_G0_ROOT_HPA, BE_MVP_G0_VMID, BE_MVP_DOMAIN0_HART },
		{ BE_MVP_GUEST_GPA, BE_MVP_G1_HPA, BE_MVP_GUEST_BYTES,
		  BE_MVP_G1_ROOT_HPA, BE_MVP_G1_VMID, BE_MVP_DOMAIN1_HART },
	};
	struct be_mvp_gstage_root_page page[2] = {
		{ channel.gpa, channel.hpa, channel.bytes,
		  channel.writer_rights },
		{ channel.gpa, channel.hpa, channel.bytes,
		  channel.reader_rights },
	};
	struct be_mvp_gstage_map map;
	unsigned int domain;

	for (domain = 0U; domain < 2U; ++domain) {
		CHECK(be_mvp_gstage_build(&desc[domain], pool, sizeof(pool)) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk(&desc[domain], pool, sizeof(pool),
					 &windows[domain]) == BE_MVP_GSTAGE_OK);
		/* The same window, with the channel leaf beside it. */
		CHECK(be_mvp_gstage_build_channel(&desc[domain], &page[domain],
						  pool, sizeof(pool)) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk_channel(&desc[domain], &page[domain],
						 pool, sizeof(pool), &map,
						 &leaves[domain].page[0]) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(memcmp(&map, &windows[domain], sizeof(map)) == 0);
	}
	CHECK(leaves[0].page[0].pte == BE_U64_C(0x460000d7) &&
	      leaves[1].page[0].pte == BE_U64_C(0x46000053));
}

static struct be_mvp_state fresh_state(void)
{
	struct be_mvp_state state = BE_MVP_STATE_INITIALIZER(
		BE_MVP_EXIT_CEILING);

	return state;
}

static struct be_mvp_exit exit_with(be_u64 scause, be_u64 sepc)
{
	struct be_mvp_exit record;
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

static struct be_mvp_exit ecall(be_u64 eid, be_u64 fid, be_u64 argument0,
				be_u64 argument1, be_u64 argument2)
{
	struct be_mvp_exit record = exit_with(BE_MVP_SCAUSE_VS_ECALL, ECALL_PC);

	record.frame.gpr[BE_R4_GPR_A7] = eid;
	record.frame.gpr[BE_R4_GPR_A6] = fid;
	record.frame.gpr[BE_R4_GPR_A0] = argument0;
	record.frame.gpr[BE_R4_GPR_A1] = argument1;
	record.frame.gpr[BE_MVP_GPR_A2] = argument2;
	return record;
}

static be_u64 call_sum(const struct be_mvp_counts *counts)
{
	return counts->base + counts->time + counts->dbcn_write +
	       counts->dbcn_read + counts->dbcn_byte + counts->srst +
	       counts->refused + counts->mgmt + counts->dbcn_input;
}

/* One exit on a fresh running state; checks the generic ecall properties. */
static struct be_mvp_result decide(const struct be_mvp_exit *record)
{
	struct be_mvp_state state = fresh_state();
	struct be_mvp_result result;

	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, record, &result) ==
	      result.action);
	CHECK(state.counts.exits == 1U);
	if (result.action != BE_MVP_ACTION_TERMINAL) {
		CHECK(result.resume_pc == record->frame.sepc + 4U);
		CHECK(call_sum(&state.counts) == 1U);
		CHECK(state.counts.ipi == 0U && state.counts.lines == 0U);
	}
	if (result.action == BE_MVP_ACTION_RETURN ||
	    result.action == BE_MVP_ACTION_CONSOLE_WRITE ||
	    result.action == BE_MVP_ACTION_CONSOLE_BYTE ||
	    result.action == BE_MVP_ACTION_SET_TIMER)
		CHECK(state.phase == BE_MVP_PHASE_RUNNING);
	if (result.error == BE_MVP_SBI_ERR_NOT_SUPPORTED ||
	    result.error == BE_MVP_SBI_ERR_INVALID_PARAM)
		CHECK(state.counts.refused == 1U);
	return result;
}

static void check_return(be_u64 eid, be_u64 fid, be_u64 argument0,
			 be_u64 argument1, be_u64 argument2, long error,
			 be_u64 value)
{
	struct be_mvp_exit record = ecall(eid, fid, argument0, argument1,
					  argument2);
	struct be_mvp_result result = decide(&record);

	CHECK(result.action == BE_MVP_ACTION_RETURN);
	CHECK(result.error == error);
	CHECK(result.value == value);
	CHECK(result.failure == BE_MVP_CLASS_NONE);
}

static void check_unsupported(be_u64 eid, be_u64 fid)
{
	check_return(eid, fid, 0U, 0U, 0U, BE_MVP_SBI_ERR_NOT_SUPPORTED, 0U);
	check_return(eid, fid, ALL_ONES, ALL_ONES, ALL_ONES,
		     BE_MVP_SBI_ERR_NOT_SUPPORTED, 0U);
}

static void check_dbcn_write(be_u64 length, be_u64 gpa, be_u64 high,
			     be_u64 expected_pa, be_u64 expected_length)
{
	struct be_mvp_exit record = ecall(BE_MVP_SBI_EID_DBCN,
					  BE_MVP_SBI_DBCN_WRITE, length, gpa,
					  high);
	struct be_mvp_result result = decide(&record);

	CHECK(result.action == BE_MVP_ACTION_CONSOLE_WRITE);
	CHECK(result.error == BE_MVP_SBI_SUCCESS);
	CHECK(result.source_pa == expected_pa);
	CHECK(result.length == expected_length);
	CHECK(result.value == expected_length);
}

static void check_dbcn_refused(be_u64 length, be_u64 gpa, be_u64 high)
{
	check_return(BE_MVP_SBI_EID_DBCN, BE_MVP_SBI_DBCN_WRITE, length, gpa,
		     high, BE_MVP_SBI_ERR_INVALID_PARAM, 0U);
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(BE_MVP_SBI_EID_BASE == 0x10U);
	CHECK(BE_MVP_SBI_EID_TIME == 0x54494d45U);
	CHECK(BE_MVP_SBI_EID_DBCN == 0x4442434eU);
	CHECK(BE_MVP_SBI_EID_SRST == 0x53525354U);
	CHECK(BE_MVP_SBI_SPEC_VERSION == 0x2000000U);
	CHECK(BE_MVP_SBI_IMPL_ID == ((be_u64)'B' << 8 | (be_u64)'E'));
	/* 5 and 6 since M7's console read (planning/mvp-m7-plan.md, D-10). */
	CHECK(BE_MVP_SBI_IMPL_VERSION == 5U);
	/* The management extension (planning/mvp-m2-plan.md, Q3). */
	CHECK(BE_MVP_SBI_IMPL_VERSION_MGMT == 6U);
	CHECK(BE_MVP_SBI_EID_MGMT == BE_U64_C(0x08004245));
	CHECK(BE_MVP_SBI_MGMT_PAUSE == 0U && BE_MVP_SBI_MGMT_TERMINATE == 1U);
	CHECK(BE_MVP_SBI_ERR_DENIED == -4 &&
	      BE_MVP_SBI_ERR_INVALID_STATE == -10);
	CHECK(BE_MVP_MGMT_PAUSE == 1U && BE_MVP_MGMT_TERMINATE == 2U &&
	      BE_MVP_MGMT_GRANTS_MAX == 4U && BE_MVP_MGMT_DELIVER == 1);
	CHECK(BE_MVP_VARIANT_NO_GRANT_RUN_BUDGET == BE_U64_C(1) << 27);
	CHECK(BE_MVP_EXIT_CEILING == BE_U64_C(1) << 20);
	CHECK(BE_MVP_RUN_BUDGET == BE_U64_C(1) << 32);
	CHECK(BE_MVP_VARIANT_EXIT_CEILING == 64U);
	CHECK(BE_MVP_VARIANT_RUN_BUDGET == BE_U64_C(1) << 20);
	CHECK(BE_MVP_RUN_EXIT_CEILING == BE_MVP_EXIT_CEILING);
	CHECK(BE_MVP_RUN_TIME_BUDGET == BE_MVP_RUN_BUDGET);
	CHECK(BE_MVP_DBCN_MAX_BYTES == 256U);
	CHECK(BE_MVP_CONSOLE_LINE_BYTES == 256U);
	CHECK(strcmp(BE_MVP_G0_PREFIX, "BE_MVP_G0: ") == 0);
	CHECK(strcmp(BE_MVP_G1_PREFIX, "BE_MVP_G1: ") == 0);
	CHECK(strlen(BE_MVP_G0_PREFIX) == BE_MVP_DOMAIN_PREFIX_LENGTH);
	CHECK(strlen(BE_MVP_G1_PREFIX) == BE_MVP_DOMAIN_PREFIX_LENGTH);
	CHECK(BE_MVP_PRINT_LINE_BYTES == 268U);
	CHECK(BE_MVP_SCAUSE_SUPERVISOR_SOFTWARE == SSI);
	CHECK(BE_MVP_VCSR_COUNT == 11U);
	CHECK(BE_MVP_GPR_A2 == 11U);
	CHECK(BE_R4_GPR_A0 == 9U && BE_R4_GPR_A1 == 10U);
	CHECK(BE_R4_GPR_A6 == 15U && BE_R4_GPR_A7 == 16U);
	CHECK(sizeof(struct be_r4_frame) == 320U);
	CHECK(sizeof(struct be_mvp_exit) == 360U);
	CHECK(__builtin_offsetof(struct be_mvp_exit, hstatus) == 320U);
	CHECK(__builtin_offsetof(struct be_mvp_exit, htinst) == 328U);
	CHECK(__builtin_offsetof(struct be_mvp_exit, vsatp) == 336U);
	CHECK(__builtin_offsetof(struct be_mvp_exit, time) == 344U);
	CHECK(__builtin_offsetof(struct be_mvp_exit, vsstatus) == 352U);
	/* Twelve counters, and M7's served console reads. */
	CHECK(sizeof(struct be_mvp_counts) == 13U * sizeof(be_u64));
	/* The image checker reads the exit ceiling at the state's start. */
	CHECK(__builtin_offsetof(struct be_mvp_state, exit_ceiling) == 0U);
	CHECK(sizeof(struct be_mvp_state) <= BE_MVP_BLOCK_STATE_BYTES);
	/* The monitor's own firmware calls (D15). */
	CHECK(BE_MVP_FW_EID_HSM == EID_HSM && BE_MVP_FW_EID_IPI == EID_IPI);
	CHECK(BE_MVP_FW_HSM_HART_START == 0U && BE_MVP_FW_HSM_HART_STOP == 1U &&
	      BE_MVP_FW_HSM_HART_GET_STATUS == 2U &&
	      BE_MVP_FW_IPI_SEND_IPI == 0U);
	CHECK(BE_MVP_HSM_STARTED == 0U && BE_MVP_HSM_STOPPED == 1U &&
	      BE_MVP_HSM_START_PENDING == 2U &&
	      BE_MVP_HSM_RESUME_PENDING == 6U);
}

static void test_class_names(void)
{
	static const char *const names[] = {
		"none", "boot", "gstage", "sstc", "controls", "payload",
		"interrupt", "guest-page-fault", "virtual-instruction",
		"access-fault", "illegal-instruction", "exception",
		"exit-budget", "run-timeout", "resume", "console",
		"guest-failure", "guest-reboot", "shutdown-returned",
		"firmware", "hart-start", "hart-ready", "ring", "ipi",
		"measurement", "mgmt", "log",
	};
	unsigned int index;

	SCENARIO();
	CHECK(BE_ARRAY_SIZE(names) == (be_size)BE_MVP_CLASS_COUNT);
	for (index = 0U; index < BE_ARRAY_SIZE(names); ++index)
		CHECK(strcmp(be_mvp_class_name((enum be_mvp_class)index),
			     names[index]) == 0);
	CHECK(strcmp(be_mvp_class_name(BE_MVP_CLASS_COUNT), "invalid") == 0);
	CHECK(strcmp(be_mvp_class_name((enum be_mvp_class)99), "invalid") == 0);
}

static struct be_mvp_controls armed_controls(void)
{
	return (struct be_mvp_controls) {
		.hip = 0U,
		.hstatus = BE_U64_C(0x200000180),
		.hedeleg = ARMED_HEDELEG,
		.hideleg = 0x40U,
		.hie = 0U,
		.hvip = 0U,
		.hcounteren = 0x2U,
		.htimedelta = 0U,
		.henvcfg = ARMED_HENVCFG,
		.hgeie = 0U,
		.vstimecmp = ALL_ONES,
		.sie = 0x2U,
		.sstatus = BE_U64_C(0x200000000),
		.hgatp = BE_U64_C(0x8000100000102034),
		.vsatp = 0U,
		.sscratch = BE_U64_C(0x102046000),
	};
}

static int armed_valid(const struct be_mvp_controls *controls)
{
	return be_mvp_controls_valid(controls, BE_MVP_G0_HGATP,
				     BE_U64_C(0x102046000));
}

static void test_controls(void)
{
	struct be_mvp_controls controls = armed_controls();
	be_u64 *fields = (be_u64 *)(void *)&controls;
	be_size index;
	unsigned int bit;

	SCENARIO();
	CHECK(BE_MVP_HSTATUS_GUEST_CONTROLS == 0x180U);
	CHECK(BE_MVP_HSTATUS_CLEARED_TRAPS == 0x700000U);
	CHECK(BE_MVP_HSTATUS_RESUME_MASK == 0x73f280U);
	CHECK(BE_MVP_HSTATUS_RESUME_CONTROLS == 0x80U);
	CHECK(BE_MVP_SIE_SSIE == 0x2U && BE_MVP_SIE_STIE == 0x20U);
	CHECK(BE_MVP_SIE_CONTROL == 0x22U);
	CHECK(BE_MVP_HVIP_VS_BITS == 0x444U);
	CHECK(BE_MVP_HEDELEG == ARMED_HEDELEG);
	CHECK(BE_MVP_HIDELEG_VSTI == 0x40U && BE_MVP_HIE_VSTIE == 0x40U);
	CHECK(BE_MVP_HCOUNTEREN_TM == 0x2U);
	CHECK(BE_MVP_HENVCFG_STCE == BE_U64_C(0x8000000000000000));
	CHECK(BE_MVP_SSTATUS_CONTROL_MASK == 0xde722U);
	/* Each domain hart's trusted-stack top is its block's. */
	CHECK(BE_MVP_G0_BLOCK_HPA + BE_MVP_BLOCK_STACK_TOP_OFFSET ==
	      BE_U64_C(0x102046000));
	CHECK(sizeof(controls) == 16U * sizeof(be_u64));
	CHECK(armed_valid(&controls) == 1);
	CHECK(be_mvp_controls_valid(&controls, BE_R3_MANAGEMENT_HGATP,
				    BE_U64_C(0x102046000)) == 0);
	CHECK(be_mvp_controls_valid(&controls, BE_MVP_G1_HGATP,
				    BE_U64_C(0x102046000)) == 0);
	CHECK(be_mvp_controls_valid(&controls, BE_MVP_G0_HGATP,
				    BE_R3_INITIAL_TRUSTED_SP) == 0);
	CHECK(be_mvp_controls_valid(&controls, BE_MVP_G0_HGATP,
				    BE_U64_C(0x102056000)) == 0);
	CHECK(be_mvp_controls_valid((const struct be_mvp_controls *)0,
				    BE_MVP_G0_HGATP,
				    BE_U64_C(0x102046000)) == 0);
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
#ifdef BE_MVP_CHERI
		/*
		 * beryllium-cheri: each with cause 28, which must stick; B6's
		 * 0xb15d, without it, fails.
		 */
		static const be_u64 warl_good[] = {
			0x1000b15dU, 0x1000b15cU, 0x1000b14dU, 0x1000b14cU,
			0x1000b11dU, 0x1000b11cU, 0x1000b10dU, 0x1000b10cU,
		};
		static const be_u64 warl_bad[] = {
			0x1000b17dU, 0x1000b15fU, 0x1000315dU, 0x1000a15dU,
			0x1000915dU, 0x1000b05dU, 0x1000b155U, 0x1000b159U,
			0x1000b10bU, 0xb15dU, 0U, ALL_ONES,
		};
#else
		static const be_u64 warl_good[] = {
			0xb15dU, 0xb15cU, 0xb14dU, 0xb14cU,
			0xb11dU, 0xb11cU, 0xb10dU, 0xb10cU,
		};
		static const be_u64 warl_bad[] = {
			0xb17dU, 0xb15fU, 0x315dU, 0xa15dU, 0x915dU,
			0xb05dU, 0xb155U, 0xb159U, 0xb10bU, 0U,
			ALL_ONES,
		};
#endif

		CHECK(BE_MVP_HEDELEG_REQUIRED == ARMED_HEDELEG_REQUIRED);
		CHECK((BE_MVP_HEDELEG & BE_MVP_HEDELEG_REQUIRED) ==
		      BE_MVP_HEDELEG_REQUIRED);
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
	/* hstatus is compared under the R3 control mask only; VTW, VTVM, and
	 * VTSR are all clear, B6's value. */
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
	controls.hie = BE_MVP_HIE_VSTIE;
	CHECK(armed_valid(&controls) == 0);
	/* hvip: only VSSIP, VSTIP, and VSEIP are tested; QEMU's view of a
	 * pending HS interrupt (bits 1 and 5) and other bits do not count. */
	for (bit = 0U; bit < 64U; ++bit) {
		controls = armed_controls();
		controls.hvip = BE_U64_C(1) << bit;
		CHECK(armed_valid(&controls) ==
		      (bit == 2U || bit == 6U || bit == 10U ? 0 : 1));
	}
	/* sie: exactly SSIE, the IPI; STIE is hart 0's alone. */
	for (bit = 0U; bit < 64U; ++bit) {
		controls = armed_controls();
		controls.sie ^= BE_U64_C(1) << bit;
		CHECK(armed_valid(&controls) == 0);
	}
	controls = armed_controls();
	controls.sie = BE_MVP_SIE_CONTROL;
	CHECK(armed_valid(&controls) == 0);
	/* HS sstatus: SIE, SPIE, SPP, FS, VS, XS, SUM, and MXR all clear. */
	for (bit = 0U; bit < 64U; ++bit) {
		controls = armed_controls();
		controls.sstatus |= BE_U64_C(1) << bit;
		CHECK(armed_valid(&controls) ==
		      ((BE_MVP_SSTATUS_CONTROL_MASK >> bit) & 1U ? 0 : 1));
	}
	controls = armed_controls();
	controls.sstatus |= BE_U64_C(1) << 9;
	CHECK(armed_valid(&controls) == 0);
	controls = armed_controls();
	controls.sstatus |= BE_U64_C(1) << 10;
	CHECK(armed_valid(&controls) == 0);

	CHECK(be_mvp_stce_class(ARMED_HENVCFG) == BE_MVP_CLASS_NONE);
#ifdef BE_MVP_CHERI
	/* beryllium-cheri: armed is STCE and CRE; STCE alone fails. */
	CHECK(be_mvp_stce_class(BE_MVP_HENVCFG_STCE) == BE_MVP_CLASS_CONTROLS);
#endif
	CHECK(be_mvp_stce_class(0U) == BE_MVP_CLASS_SSTC);
	CHECK(be_mvp_stce_class(1U) == BE_MVP_CLASS_SSTC);
	CHECK(be_mvp_stce_class(ALL_ONES >> 1) == BE_MVP_CLASS_SSTC);
	CHECK(be_mvp_stce_class(ARMED_HENVCFG | 1U) == BE_MVP_CLASS_CONTROLS);
	CHECK(be_mvp_stce_class(ALL_ONES) == BE_MVP_CLASS_CONTROLS);
}

static void test_classify(void)
{
	be_u64 cause;

	SCENARIO();
	for (cause = 0U; cause < 64U; ++cause) {
		enum be_mvp_class expected = BE_MVP_CLASS_EXCEPTION;

		if (cause == 10U)
			expected = BE_MVP_CLASS_NONE;
		else if (cause == 20U || cause == 21U || cause == 23U)
			expected = BE_MVP_CLASS_GUEST_PAGE_FAULT;
		else if (cause == 22U)
			expected = BE_MVP_CLASS_VIRTUAL_INSTRUCTION;
		else if (cause == 1U || cause == 5U || cause == 7U)
			expected = BE_MVP_CLASS_ACCESS_FAULT;
		else if (cause == 2U)
			expected = BE_MVP_CLASS_ILLEGAL_INSTRUCTION;
		CHECK(be_mvp_classify_cause(cause) == expected);
		CHECK(be_mvp_classify_cause(BE_MVP_SCAUSE_INTERRUPT | cause) ==
		      BE_MVP_CLASS_INTERRUPT);
	}
	CHECK(be_mvp_classify_cause(ALL_ONES) == BE_MVP_CLASS_INTERRUPT);
	CHECK(be_mvp_classify_cause(ALL_ONES >> 1) == BE_MVP_CLASS_EXCEPTION);
	CHECK(be_mvp_classify_cause(HIGH_BIT | 10U) == BE_MVP_CLASS_EXCEPTION);
	CHECK(be_mvp_classify_cause(HIGH_BIT | 5U) == BE_MVP_CLASS_EXCEPTION);
}

static void test_window(void)
{
	SCENARIO();
	CHECK(window.gpa_base == WINDOW_GPA);
	CHECK(window.hpa_base == WINDOW_HPA);
	CHECK(window.size == WINDOW_BYTES);
	CHECK(window.leaves == 32U);
	CHECK(window.hgatp == BE_MVP_G0_HGATP);
	CHECK(windows[1].hgatp == BE_MVP_G1_HGATP);
	CHECK(windows[1].hpa_base == WINDOW_G1_HPA);
	CHECK(windows[1].gpa_base == WINDOW_GPA &&
	      windows[1].size == WINDOW_BYTES);
	CHECK(window.pool_pa == BE_U64_C(0x102034000));
	CHECK(window.vmid == 1U && windows[1].vmid == 2U);
	CHECK(window.hart == 1U && windows[1].hart == 2U);
}

static void test_base(void)
{
	static const be_u64 available[] = {
		BE_MVP_SBI_EID_BASE, BE_MVP_SBI_EID_TIME, BE_MVP_SBI_EID_DBCN,
		BE_MVP_SBI_EID_SRST,
	};
	static const be_u64 absent[] = {
		EID_HSM, EID_IPI, EID_RFENCE, EID_PMU, EID_SUSP, EID_CPPC,
		EID_NACL, EID_STA, EID_SSE, EID_FWFT, EID_DBTR, EID_MPXY,
		EID_UNASSIGNED, 0U, ALL_ONES, HIGH_BIT | BE_MVP_SBI_EID_BASE,
		HIGH_BIT | BE_MVP_SBI_EID_DBCN, BE_U64_C(0x08000000),
		BE_U64_C(0x09000000), BE_U64_C(0x0a000000),
	};
	be_size index;
	be_u64 legacy;

	SCENARIO();
	check_return(BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, 0U, 0, 0x2000000U);
	check_return(BE_MVP_SBI_EID_BASE, 0U, ALL_ONES, 7U, 9U, 0, 0x2000000U);
	check_return(BE_MVP_SBI_EID_BASE, 1U, 0U, 0U, 0U, 0, 0x4245U);
	/* Version 5 since M7 (3 before, B7's): the guest sees no new
	 * extension through SBI (Q3); the served console read is DBCN's
	 * (planning/mvp-m7-plan.md, D-10). */
	check_return(BE_MVP_SBI_EID_BASE, 2U, 0U, 0U, 0U, 0, 5U);
	check_return(BE_MVP_SBI_EID_BASE, 4U, 0U, 0U, 0U, 0, 0U);
	check_return(BE_MVP_SBI_EID_BASE, 5U, 0U, 0U, 0U, 0, 0U);
	check_return(BE_MVP_SBI_EID_BASE, 6U, ALL_ONES, 0U, 0U, 0, 0U);
	for (index = 0U; index < BE_ARRAY_SIZE(available); ++index)
		check_return(BE_MVP_SBI_EID_BASE, 3U, available[index], 0U,
			     0U, 0, 1U);
	/* The monitor's own HSM and IPI calls are not the guest's. */
	for (index = 0U; index < BE_ARRAY_SIZE(absent); ++index)
		check_return(BE_MVP_SBI_EID_BASE, 3U, absent[index], 0U, 0U, 0,
			     0U);
	for (legacy = 0U; legacy <= 0xfU; ++legacy)
		check_return(BE_MVP_SBI_EID_BASE, 3U, legacy, 0U, 0U, 0, 0U);
	check_unsupported(BE_MVP_SBI_EID_BASE, 7U);
	check_unsupported(BE_MVP_SBI_EID_BASE, 8U);
	check_unsupported(BE_MVP_SBI_EID_BASE, 0xffffffffU);
	check_unsupported(BE_MVP_SBI_EID_BASE, HIGH_BIT);
	check_unsupported(BE_MVP_SBI_EID_BASE, ALL_ONES);
}

static void test_unsupported(void)
{
	static const be_u64 eids[] = {
		EID_HSM, EID_IPI, EID_RFENCE, EID_PMU, EID_SUSP, EID_CPPC,
		EID_NACL, EID_STA, EID_SSE, EID_FWFT, EID_DBTR, EID_MPXY,
		EID_UNASSIGNED, BE_U64_C(0x08000000), BE_U64_C(0x09000000),
		BE_U64_C(0x0a000000), BE_U64_C(0x10) | HIGH_BIT,
		BE_MVP_SBI_EID_TIME | HIGH_BIT, BE_MVP_SBI_EID_DBCN | HIGH_BIT,
		BE_MVP_SBI_EID_SRST | HIGH_BIT, ALL_ONES,
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
			     BE_MVP_SBI_ERR_NOT_SUPPORTED, 0U);
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
		struct be_mvp_exit record = ecall(BE_MVP_SBI_EID_TIME, 0U,
						  values[index], 5U, 6U);
		struct be_mvp_state state = fresh_state();
		struct be_mvp_result result;

		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) ==
		      BE_MVP_ACTION_SET_TIMER);
		CHECK(result.timer == values[index]);
		CHECK(result.error == BE_MVP_SBI_SUCCESS);
		CHECK(result.value == 0U);
		CHECK(state.counts.time == 1U && call_sum(&state.counts) == 1U);
	}
	check_unsupported(BE_MVP_SBI_EID_TIME, 1U);
	check_unsupported(BE_MVP_SBI_EID_TIME, 2U);
	check_unsupported(BE_MVP_SBI_EID_TIME, HIGH_BIT);
	check_unsupported(BE_MVP_SBI_EID_TIME, ALL_ONES);
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
	check_dbcn_write(64U, BE_MVP_KERNEL_GPA, 0U, BE_U64_C(0x110200000),
			 64U);
	check_dbcn_write(40U, BE_MVP_DTB_GPA, 0U, BE_U64_C(0x113e00000), 40U);
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
	/* Host-physical addresses are not guest addresses: the windows, the
	 * monitor, the pool, the hart region, and the staged image. */
	check_dbcn_refused(1U, WINDOW_HPA, 0U);
	check_dbcn_refused(1U, BE_U64_C(0x102000000), 0U);
	check_dbcn_refused(1U, BE_U64_C(0x102034000), 0U);
	check_dbcn_refused(1U, BE_MVP_HART_REGION_HPA, 0U);
	check_dbcn_refused(1U, BE_MVP_G1_BLOCK_HPA +
			   BE_MVP_BLOCK_OUTBOUND_OFFSET, 0U);
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
	struct be_mvp_gstage_map empty = { 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U };
	struct be_mvp_state state = fresh_state();
	struct be_mvp_exit record;
	struct be_mvp_result result;
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
	check_return(BE_MVP_SBI_EID_DBCN, 0U, 0U, BE_U64_C(0x40001000), 0U, 0,
		     0U);
	check_return(BE_MVP_SBI_EID_DBCN, 0U, 0U, ALL_ONES, 0U, 0, 0U);
	check_return(BE_MVP_SBI_EID_DBCN, 0U, 0U, WINDOW_GPA, 0U, 0, 0U);
	/* ...but never with a nonzero high word. */
	check_dbcn_refused(0U, WINDOW_GPA, 1U);
	/* An unwalked (empty) window admits nothing. */
	record = ecall(BE_MVP_SBI_EID_DBCN, 0U, 1U, WINDOW_GPA, 0U);
	CHECK(be_mvp_handle_exit(&state, &empty, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_RETURN);
	CHECK(result.error == BE_MVP_SBI_ERR_INVALID_PARAM);
	CHECK(state.counts.refused == 1U && state.counts.dbcn_write == 0U);
}

static void test_dbcn_other(void)
{
	struct be_mvp_exit record;
	struct be_mvp_result result;
	struct be_mvp_state state;
	be_u64 byte;

	SCENARIO();
	/* Console read is denied whatever the range, and is not refused. */
	check_return(BE_MVP_SBI_EID_DBCN, 1U, 4U, WINDOW_GPA, 0U,
		     BE_MVP_SBI_ERR_DENIED, 0U);
	check_return(BE_MVP_SBI_EID_DBCN, 1U, 0U, 0U, 0U,
		     BE_MVP_SBI_ERR_DENIED, 0U);
	check_return(BE_MVP_SBI_EID_DBCN, 1U, ALL_ONES, ALL_ONES, ALL_ONES,
		     BE_MVP_SBI_ERR_DENIED, 0U);
	state = fresh_state();
	record = ecall(BE_MVP_SBI_EID_DBCN, 1U, 16U, WINDOW_GPA, 0U);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_RETURN);
	CHECK(state.counts.dbcn_read == 1U && state.counts.refused == 0U);
	/* Write byte takes the low byte of a0. */
	for (byte = 0U; byte < 0x100U; ++byte) {
		record = ecall(BE_MVP_SBI_EID_DBCN, 2U, byte | 0xab00U, 0U, 0U);
		state = fresh_state();
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) ==
		      BE_MVP_ACTION_CONSOLE_BYTE);
		CHECK(result.byte == byte);
		CHECK(result.error == BE_MVP_SBI_SUCCESS);
		CHECK(result.value == 0U);
		CHECK(state.counts.dbcn_byte == 1U &&
		      call_sum(&state.counts) == 1U);
	}
	record = ecall(BE_MVP_SBI_EID_DBCN, 2U, ALL_ONES, 1U, 2U);
	result = decide(&record);
	CHECK(result.action == BE_MVP_ACTION_CONSOLE_BYTE);
	CHECK(result.byte == 0xffU);
	check_unsupported(BE_MVP_SBI_EID_DBCN, 3U);
	check_unsupported(BE_MVP_SBI_EID_DBCN, 4U);
	check_unsupported(BE_MVP_SBI_EID_DBCN, HIGH_BIT);
	check_unsupported(BE_MVP_SBI_EID_DBCN, ALL_ONES);
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
			struct be_mvp_state state = fresh_state();
			struct be_mvp_exit record = ecall(BE_MVP_SBI_EID_SRST,
							  0U, type, reason,
							  0U);
			struct be_mvp_result result;

			(void)be_mvp_handle_exit(&state, &window, &no_leaf,
						 &record, &result);
			if (type > 2U || reason > 1U) {
				/* Reserved values are refused, as in B5. */
				CHECK(result.action == BE_MVP_ACTION_RETURN);
				CHECK(result.error ==
				      BE_MVP_SBI_ERR_INVALID_PARAM);
				CHECK(state.phase == BE_MVP_PHASE_RUNNING);
				CHECK(state.counts.refused == 1U);
			} else if (type != 0U) {
				/* A cold or warm reboot ends the run. */
				CHECK(result.action ==
				      BE_MVP_ACTION_GUEST_REBOOT);
				CHECK(state.phase == BE_MVP_PHASE_FAILED);
				CHECK(state.failure ==
				      BE_MVP_CLASS_GUEST_REBOOT);
				CHECK(result.failure ==
				      BE_MVP_CLASS_GUEST_REBOOT);
				CHECK(state.counts.srst == 1U);
			} else if (reason == 0U) {
				/* Only the calling domain stops: it posts
				 * SHUTDOWN and parks its hart. */
				CHECK(result.action == BE_MVP_ACTION_SHUTDOWN);
				CHECK(state.phase == BE_MVP_PHASE_STOPPED);
				CHECK(state.failure == BE_MVP_CLASS_NONE);
				CHECK(result.failure == BE_MVP_CLASS_NONE);
				CHECK(state.counts.srst == 1U);
			} else {
				CHECK(result.action ==
				      BE_MVP_ACTION_GUEST_FAILURE);
				CHECK(state.phase == BE_MVP_PHASE_FAILED);
				CHECK(state.failure ==
				      BE_MVP_CLASS_GUEST_FAILURE);
				CHECK(result.failure ==
				      BE_MVP_CLASS_GUEST_FAILURE);
				CHECK(state.counts.srst == 1U);
			}
			CHECK(result.value == 0U);
			CHECK(state.counts.exits == 1U);
			CHECK(call_sum(&state.counts) == 1U);
		}
	}
	check_unsupported(BE_MVP_SBI_EID_SRST, 1U);
	check_unsupported(BE_MVP_SBI_EID_SRST, 2U);
	check_unsupported(BE_MVP_SBI_EID_SRST, HIGH_BIT);
	check_unsupported(BE_MVP_SBI_EID_SRST, ALL_ONES);
}

static void test_after_shutdown(void)
{
	struct be_mvp_state state = fresh_state();
	struct be_mvp_state other = fresh_state();
	struct be_mvp_exit record = ecall(BE_MVP_SBI_EID_SRST, 0U, 0U, 0U, 0U);
	struct be_mvp_exit base = ecall(BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_mvp_exit ipi = exit_with(SSI, ECALL_PC);
	struct be_mvp_result result;

	SCENARIO();
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_SHUTDOWN);
	/* The other domain's hart runs on, and stops in turn. */
	CHECK(be_mvp_handle_exit(&other, &windows[1], &no_leaf, &base,
				 &result) ==
	      BE_MVP_ACTION_RETURN);
	CHECK(be_mvp_handle_exit(&other, &windows[1], &no_leaf, &record,
				 &result) ==
	      BE_MVP_ACTION_SHUTDOWN);
	CHECK(other.phase == BE_MVP_PHASE_STOPPED);
	CHECK(other.counts.exits == 2U && other.counts.srst == 1U);
	/* An exit of a stopped domain, an IPI included, fails its hart. */
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &base, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXCEPTION);
	CHECK(state.phase == BE_MVP_PHASE_FAILED);
	CHECK(state.counts.exits == 1U);
	CHECK(be_mvp_handle_exit(&other, &windows[1], &no_leaf, &ipi,
				 &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXCEPTION);
	CHECK(other.counts.ipi == 0U);

	state = fresh_state();
	record = ecall(BE_MVP_SBI_EID_SRST, 0U, 0U, 1U, 0U);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_GUEST_FAILURE);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &base, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_GUEST_FAILURE);
	CHECK(state.failure == BE_MVP_CLASS_GUEST_FAILURE);

	state = fresh_state();
	record = ecall(BE_MVP_SBI_EID_SRST, 0U, 2U, 0U, 0U);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_GUEST_REBOOT);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &base, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_GUEST_REBOOT);
	CHECK(state.counts.exits == 1U);
}

/* The ceiling counts every exit, whatever its class or outcome. */
static void check_ceiling(be_u64 ceiling)
{
	struct be_mvp_state state = BE_MVP_STATE_INITIALIZER(ceiling);
	struct be_mvp_state other = BE_MVP_STATE_INITIALIZER(ceiling);
	struct be_mvp_exit record = ecall(BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_mvp_exit unknown = ecall(EID_UNASSIGNED, 0U, 0U, 0U, 0U);
	struct be_mvp_result result;
	be_u64 count;
	be_u64 good = 0U;

	for (count = 1U; count <= ceiling; ++count) {
		const struct be_mvp_exit *next = (count & 1U) ? &record :
							       &unknown;

		if (be_mvp_handle_exit(&state, &window, &no_leaf, next,
				       &result) ==
		    BE_MVP_ACTION_RETURN)
			++good;
	}
	CHECK(good == ceiling);
	CHECK(state.counts.exits == ceiling);
	CHECK(state.counts.base == (ceiling + 1U) / 2U);
	CHECK(state.counts.refused == ceiling / 2U);
	CHECK(call_sum(&state.counts) == ceiling);
	CHECK(state.phase == BE_MVP_PHASE_RUNNING);
	/* Each domain hart has its own ceiling: G1's first exit passes. */
	CHECK(be_mvp_handle_exit(&other, &windows[1], &no_leaf, &record,
				 &result) ==
	      BE_MVP_ACTION_RETURN);
	CHECK(other.counts.exits == 1U);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXIT_BUDGET);
	CHECK(state.phase == BE_MVP_PHASE_FAILED);
	CHECK(state.counts.exits == ceiling + 1U);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXIT_BUDGET);
	CHECK(state.counts.exits == ceiling + 1U);
	CHECK(other.phase == BE_MVP_PHASE_RUNNING);

	/* A terminal exit at the ceiling reports the ceiling. */
	state = (struct be_mvp_state)BE_MVP_STATE_INITIALIZER(ceiling);
	state.counts.exits = ceiling;
	record = exit_with(BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT, ECALL_PC);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXIT_BUDGET);
	/* So does an IPI at the ceiling. */
	state = (struct be_mvp_state)BE_MVP_STATE_INITIALIZER(ceiling);
	state.counts.exits = ceiling;
	record = exit_with(SSI, ECALL_PC);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXIT_BUDGET);
	CHECK(state.counts.ipi == 0U);
}

static void test_exit_ceiling(void)
{
	SCENARIO();
	check_ceiling(BE_MVP_VARIANT_EXIT_CEILING);
	check_ceiling(BE_MVP_EXIT_CEILING);
	/* The run budget is hart 0's (mvp-hart.h); 2^32 ticks is about
	 * 179 s at the board's 24 MHz timebase. */
	CHECK(BE_MVP_RUN_BUDGET / BE_MVP_TIMEBASE_HZ == 178U);
}

static void test_terminal_exits(void)
{
	static const struct {
		be_u64 scause;
		enum be_mvp_class failure;
	} exits[] = {
		{ BE_MVP_SCAUSE_INTERRUPT | 1U | HIGH_BIT,
		  BE_MVP_CLASS_INTERRUPT },
		{ BE_MVP_SCAUSE_INTERRUPT | 2U, BE_MVP_CLASS_INTERRUPT },
		{ BE_MVP_SCAUSE_INTERRUPT | 4U, BE_MVP_CLASS_INTERRUPT },
		{ BE_MVP_SCAUSE_INTERRUPT | 13U, BE_MVP_CLASS_INTERRUPT },
		{ BE_MVP_SCAUSE_INTERRUPT | 5U, BE_MVP_CLASS_INTERRUPT },
		{ BE_MVP_SCAUSE_INTERRUPT | 5U | HIGH_BIT,
		  BE_MVP_CLASS_INTERRUPT },
		{ BE_MVP_SCAUSE_INTERRUPT | 6U, BE_MVP_CLASS_INTERRUPT },
		{ BE_MVP_SCAUSE_INTERRUPT | 9U, BE_MVP_CLASS_INTERRUPT },
		{ BE_MVP_SCAUSE_INTERRUPT | 10U, BE_MVP_CLASS_INTERRUPT },
		{ BE_MVP_SCAUSE_INTERRUPT | 12U, BE_MVP_CLASS_INTERRUPT },
		{ 20U, BE_MVP_CLASS_GUEST_PAGE_FAULT },
		{ 21U, BE_MVP_CLASS_GUEST_PAGE_FAULT },
		{ 23U, BE_MVP_CLASS_GUEST_PAGE_FAULT },
		{ 22U, BE_MVP_CLASS_VIRTUAL_INSTRUCTION },
		{ 1U, BE_MVP_CLASS_ACCESS_FAULT },
		{ 5U, BE_MVP_CLASS_ACCESS_FAULT },
		{ 7U, BE_MVP_CLASS_ACCESS_FAULT },
		{ 2U, BE_MVP_CLASS_ILLEGAL_INSTRUCTION },
		{ 0U, BE_MVP_CLASS_EXCEPTION },
		{ 3U, BE_MVP_CLASS_EXCEPTION },
		{ 4U, BE_MVP_CLASS_EXCEPTION },
		{ 6U, BE_MVP_CLASS_EXCEPTION },
		{ 8U, BE_MVP_CLASS_EXCEPTION },
		{ 9U, BE_MVP_CLASS_EXCEPTION },
		{ 11U, BE_MVP_CLASS_EXCEPTION },
		{ 12U, BE_MVP_CLASS_EXCEPTION },
		{ 13U, BE_MVP_CLASS_EXCEPTION },
		{ 15U, BE_MVP_CLASS_EXCEPTION },
		{ 18U, BE_MVP_CLASS_EXCEPTION },
		{ 19U, BE_MVP_CLASS_EXCEPTION },
		{ 24U, BE_MVP_CLASS_EXCEPTION },
	};
	be_size index;
	unsigned int spvp;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(exits); ++index) {
		/* VS-origin (SPVP = 1) and VU-origin (SPVP = 0) alike. */
		for (spvp = 0U; spvp < 2U; ++spvp) {
			struct be_mvp_state state = fresh_state();
			struct be_mvp_exit record = exit_with(
				exits[index].scause, ECALL_PC);
			struct be_mvp_exit base = ecall(BE_MVP_SBI_EID_BASE, 0U,
							0U, 0U, 0U);
			struct be_mvp_result result;

			if (spvp == 0U)
				record.hstatus &= ~BE_MVP_HSTATUS_SPVP;
			/* The registers of an SBI call do not matter here. */
			record.frame.gpr[BE_R4_GPR_A7] = BE_MVP_SBI_EID_BASE;
			record.frame.gpr[BE_R4_GPR_A6] = 0U;
			CHECK(be_mvp_handle_exit(&state, &window, &no_leaf,
						 &record, &result) ==
			      BE_MVP_ACTION_TERMINAL);
			CHECK(result.failure == exits[index].failure);
			CHECK(state.phase == BE_MVP_PHASE_FAILED);
			CHECK(state.failure == exits[index].failure);
			CHECK(state.counts.exits == 1U);
			CHECK(call_sum(&state.counts) == 0U);
			CHECK(state.counts.ipi == 0U);
			CHECK(be_mvp_handle_exit(&state, &window, &no_leaf,
						 &base, &result) ==
			      BE_MVP_ACTION_TERMINAL);
			CHECK(result.failure == exits[index].failure);
			CHECK(state.counts.exits == 1U);
		}
	}
}

static void test_frame_integrity(void)
{
	struct be_mvp_state state = fresh_state();
	struct be_mvp_exit record = ecall(BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_mvp_result result;

	SCENARIO();
	record.frame.reserved = 1U;
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXCEPTION);

	/* Only an exit from V=1 (SPV = 1) is a guest exit, the IPI too. */
	state = fresh_state();
	record = ecall(BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	record.hstatus &= ~BE_MVP_HSTATUS_SPV;
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXCEPTION);
	state = fresh_state();
	record.hstatus = BE_MVP_HSTATUS_SPV;
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_RETURN);
	state = fresh_state();
	record = exit_with(SSI, ECALL_PC);
	record.hstatus &= ~BE_MVP_HSTATUS_SPV;
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXCEPTION);
	CHECK(state.counts.ipi == 0U);

	state = fresh_state();
	record = ecall(BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	record.frame.sepc = ALL_ONES - 3U;
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_RESUME);

	state = fresh_state();
	record.frame.sepc = ALL_ONES - 4U;
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_RETURN);
	CHECK(result.resume_pc == ALL_ONES);

	state = fresh_state();
	CHECK(be_mvp_handle_exit(&state, (const struct be_mvp_gstage_map *)0,
				 &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXCEPTION);
	state = fresh_state();
	CHECK(be_mvp_handle_exit(&state, &window,
				 (const struct be_mvp_gstage_leaves *)0,
				 &record, &result) == BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXCEPTION &&
	      state.counts.exits == 0U);
	state = fresh_state();
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf,
				 (const struct be_mvp_exit *)0, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(state.phase == BE_MVP_PHASE_FAILED);
	state = fresh_state();
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
				 (struct be_mvp_result *)0) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(state.phase == BE_MVP_PHASE_FAILED);
	CHECK(be_mvp_handle_exit((struct be_mvp_state *)0, &window, &no_leaf,
				 &record, &result) == BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXCEPTION);

	/* The sticky class: the first failure is kept. */
	state = fresh_state();
	CHECK(be_mvp_fail(&state, BE_MVP_CLASS_SSTC) == BE_MVP_CLASS_SSTC);
	CHECK(be_mvp_fail(&state, BE_MVP_CLASS_CONSOLE) == BE_MVP_CLASS_SSTC);
	state = fresh_state();
	CHECK(be_mvp_fail(&state, BE_MVP_CLASS_NONE) == BE_MVP_CLASS_EXCEPTION);
	CHECK(be_mvp_fail((struct be_mvp_state *)0, BE_MVP_CLASS_BOOT) ==
	      BE_MVP_CLASS_BOOT);
	state = fresh_state();
	CHECK(be_mvp_fail(&state, BE_MVP_CLASS_COUNT) ==
	      BE_MVP_CLASS_EXCEPTION);
}

static void test_apply_return(void)
{
	struct be_mvp_exit record = ecall(BE_MVP_SBI_EID_BASE, 7U, 1U, 2U, 3U);
	struct be_mvp_exit before = record;
	struct be_mvp_result result = decide(&record);
	be_size index;

	SCENARIO();
	CHECK(result.error == BE_MVP_SBI_ERR_NOT_SUPPORTED);
	be_mvp_apply_return(&record.frame, &result);
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
	CHECK(record.hstatus == before.hstatus &&
	      record.htinst == before.htinst &&
	      record.vsatp == before.vsatp && record.time == before.time);
	be_mvp_apply_return((struct be_r4_frame *)0, &result);
	be_mvp_apply_return(&record.frame, (const struct be_mvp_result *)0);
	CHECK(record.frame.sepc == ECALL_PC + 4U);
	/* The IPI, a shutdown, and terminal decisions change nothing: the
	 * IPI resumes exactly where it struck. */
	{
		static const enum be_mvp_action untouched[] = {
			BE_MVP_ACTION_NONE, BE_MVP_ACTION_IPI,
			BE_MVP_ACTION_SHUTDOWN, BE_MVP_ACTION_GUEST_FAILURE,
			BE_MVP_ACTION_GUEST_REBOOT, BE_MVP_ACTION_TERMINAL,
		};

		for (index = 0U; index < BE_ARRAY_SIZE(untouched); ++index) {
			record = exit_with(SSI, ECALL_PC);
			before = record;
			result = (struct be_mvp_result){
				.action = untouched[index], .error = -9,
				.value = 9U, .resume_pc = 0x1000U };
			be_mvp_apply_return(&record.frame, &result);
			CHECK(memcmp(&record, &before, sizeof(record)) == 0);
		}
	}
}

/* The first entry: sepc, a0 = hart, a1 = DTB; every other word 0. */
static void test_entry_frame(void)
{
	struct be_mvp_exit record;
	const be_u64 *words = (const be_u64 *)(const void *)&record;
	be_size index;

	SCENARIO();
	memset(&record, 0xa5, sizeof(record));
	be_mvp_entry_frame(&record, BE_MVP_KERNEL_GPA, BE_MVP_GUEST_HART,
			   BE_MVP_DTB_GPA);
	CHECK(record.frame.sepc == BE_U64_C(0x80200000));
	CHECK(record.frame.gpr[BE_R4_GPR_A0] == 0U);
	CHECK(record.frame.gpr[BE_R4_GPR_A1] == BE_U64_C(0x83e00000));
	/* The entry is into VS mode: SPV and SPVP. */
	CHECK(record.hstatus == 0x180U);
	CHECK(be_mvp_record_spp(&record) == 0x100U);
	for (index = 0U; index < sizeof(record) / sizeof(be_u64); ++index) {
		if (index == BE_R4_GPR_A1 ||
		    index == __builtin_offsetof(struct be_r4_frame, sepc) /
				     sizeof(be_u64) ||
		    index == __builtin_offsetof(struct be_mvp_exit, hstatus) /
				     sizeof(be_u64))
			continue;
		CHECK(words[index] == 0U);
	}
	be_mvp_entry_frame(&record, 1U, 2U, 3U);
	CHECK(record.frame.sepc == 1U && record.frame.gpr[BE_R4_GPR_A0] == 2U &&
	      record.frame.gpr[BE_R4_GPR_A1] == 3U);
	be_mvp_entry_frame((struct be_mvp_exit *)0, 1U, 2U, 3U);
}

/*
 * Each domain hart's outbound ring, as its writer and as hart 0's reader,
 * and hart 0's printed lines: be_mvp_line_output() of each LINE drained.
 */
static be_u8 ring_bytes[2][BE_MVP_OUTBOUND_RING_BYTES];
static struct be_mvp_ring_index ring_index[2][2];
static struct be_mvp_ring outbound[2];
static struct be_mvp_ring drain_view[2];
static struct be_mvp_record taken;
static struct be_mvp_state harts[2];
static char console_output[BE_MVP_PRINT_LINE_BYTES * 260U];

static void open_outbound(unsigned int domain, be_u64 capacity)
{
	be_mvp_ring_reset(&ring_index[domain][0], &ring_index[domain][1]);
	CHECK(be_mvp_ring_init(&outbound[domain], ring_bytes[domain], capacity,
			       &ring_index[domain][0], &ring_index[domain][1],
			       BE_MVP_RECORDS_OUTBOUND, domain,
			       BE_MVP_RING_WRITER) == 1);
	CHECK(be_mvp_ring_init(&drain_view[domain], ring_bytes[domain],
			       capacity, &ring_index[domain][0],
			       &ring_index[domain][1], BE_MVP_RECORDS_OUTBOUND,
			       domain, BE_MVP_RING_READER) == 1);
}

/* Hart 0's side: publish, then drain every LINE as it would print it. */
static be_u64 drain(unsigned int domain, be_u64 posted)
{
	be_u64 length = 0U;
	be_u64 lines = 0U;

	CHECK(be_mvp_ring_publish(&outbound[domain]) == 1);
	(void)be_mvp_ring_acquire(&drain_view[domain]);
	while (be_mvp_ring_take(&drain_view[domain], &taken) ==
	       BE_MVP_RING_RECORD) {
		be_u64 out;

		CHECK(taken.type == BE_MVP_RECORD_LINE &&
		      taken.domain == domain && taken.time == EXIT_TIME);
		out = be_mvp_line_output(&taken, console_output + length,
					 sizeof(console_output) - length);
		CHECK(out != BE_MVP_CONSOLE_INVALID);
		length += out;
		++lines;
	}
	CHECK(drain_view[domain].failed == 0U && lines == posted);
	CHECK(be_mvp_ring_release(&drain_view[domain]) == 1);
	return length;
}

static be_u64 feed_bytes(unsigned int domain, const be_u8 *bytes,
			 be_u64 length)
{
	be_u64 before = harts[domain].counts.lines;
	be_u64 posted = be_mvp_console_feed(&harts[domain], &outbound[domain],
					    bytes, length, EXIT_TIME);

	CHECK(posted != BE_MVP_CONSOLE_INVALID &&
	      posted != BE_MVP_CONSOLE_FULL);
	CHECK(harts[domain].counts.lines == before + posted);
	return drain(domain, posted);
}

static be_u64 feed(unsigned int domain, const char *text)
{
	return feed_bytes(domain, (const be_u8 *)text, strlen(text));
}

static int output_is(be_u64 length, const char *text)
{
	return length == strlen(text) &&
	       memcmp(console_output, text, strlen(text)) == 0;
}

static void open_harts(void)
{
	harts[0] = fresh_state();
	harts[1] = fresh_state();
	open_outbound(0U, BE_MVP_OUTBOUND_RING_BYTES);
	open_outbound(1U, BE_MVP_OUTBOUND_RING_BYTES);
}

static void test_console(void)
{
	struct be_mvp_state copy;
	be_u8 input[BE_MVP_DBCN_MAX_BYTES + 1U];
	be_u64 length;
	be_size index;

	SCENARIO();
	open_harts();
	CHECK(strcmp(be_mvp_domain_prefix(0U), "BE_MVP_G0: ") == 0);
	CHECK(strcmp(be_mvp_domain_prefix(1U), "BE_MVP_G1: ") == 0);
	CHECK(be_mvp_domain_prefix(2U) == (const char *)0);
	/* A whole line: one LINE record; hart 0 adds the prefix and LF. */
	length = feed(0U, "[    0.000000] Linux version 7.2.0\n");
	CHECK(output_is(length,
			"BE_MVP_G0: [    0.000000] Linux version 7.2.0\n"));
	CHECK(harts[0].console.length == 0U && harts[0].counts.lines == 1U);
	/* hvc sends CR before LF: the CR is dropped. */
	length = feed(1U, "MVPINIT 05 RESULT pass\r\n");
	CHECK(output_is(length, "BE_MVP_G1: MVPINIT 05 RESULT pass\n"));
	/* CR alone posts nothing and buffers nothing. */
	length = feed(0U, "\r");
	CHECK(length == 0U && harts[0].console.length == 0U);
	length = feed(0U, "\r\r\n");
	CHECK(output_is(length, "BE_MVP_G0: \n"));
	length = feed(0U, "a\rb\n");
	CHECK(output_is(length, "BE_MVP_G0: ab\n"));
	/* A line split across calls is posted once, whole, at its LF. */
	length = feed(0U, "MVPINIT 01 ST");
	CHECK(length == 0U && harts[0].console.length == 13U);
	length = feed(0U, "ART guest=0 pid=1\r");
	CHECK(length == 0U && harts[0].console.length == 30U);
	length = feed(0U, "\n");
	CHECK(output_is(length, "BE_MVP_G0: MVPINIT 01 START guest=0 pid=1\n"));
	CHECK(harts[0].console.length == 0U);
	/* A bare newline is an empty domain line. */
	length = feed(1U, "\n");
	CHECK(output_is(length, "BE_MVP_G1: \n"));
	/* Several lines in one call; the partial line waits. */
	length = feed(1U, "one\ntwo\nthr");
	CHECK(output_is(length, "BE_MVP_G1: one\nBE_MVP_G1: two\n"));
	CHECK(harts[1].console.length == 3U);
	length = feed(1U, "ee\n");
	CHECK(output_is(length, "BE_MVP_G1: three\n"));
	CHECK(harts[0].counts.lines == 4U && harts[1].counts.lines == 5U);
	/* Forged evidence and forged tags stay inside a domain line. */
	length = feed(0U, "x\nBE_R3:01 BOOT_VALIDATED\n");
	CHECK(output_is(length,
			"BE_MVP_G0: x\nBE_MVP_G0: BE_R3:01 BOOT_VALIDATED\n"));
	length = feed(0U, "\tBE_MVP:14 SHUTDOWN type=0 reason=0\n");
	CHECK(output_is(length,
			"BE_MVP_G0: ?BE_MVP:14 SHUTDOWN type=0 reason=0\n"));
	length = feed(1U, "BE_MVP_G0: forged\n");
	CHECK(output_is(length, "BE_MVP_G1: BE_MVP_G0: forged\n"));
	/* Every byte value: printable ASCII and LF pass, CR vanishes, the
	 * rest is '?'. */
	for (index = 0U; index < 256U; ++index) {
		be_u8 byte = (be_u8)index;

		harts[0].console.length = 1U;
		harts[0].console.text[0] = 'k';
		length = feed_bytes(0U, &byte, 1U);
		if (byte == '\r') {
			CHECK(length == 0U && harts[0].console.length == 1U);
		} else if (byte == '\n') {
			CHECK(output_is(length, "BE_MVP_G0: k\n"));
			CHECK(harts[0].console.length == 0U);
		} else {
			CHECK(length == 0U && harts[0].console.length == 2U);
			CHECK(harts[0].console.text[1] ==
			      (byte >= 0x20U && byte <= 0x7eU ? (char)byte :
								'?'));
		}
	}
	/* A full buffer is posted as its own line when one more byte
	 * comes; a full line that its LF ends is one line. */
	harts[1].console.length = 0U;
	memset(input, 'y', sizeof(input));
	length = feed_bytes(1U, input, 256U);
	CHECK(length == 0U && harts[1].console.length == 256U);
	length = feed(1U, "z\n");
	CHECK(length == 11U + 256U + 1U + 11U + 2U);
	CHECK(memcmp(console_output, "BE_MVP_G1: ", 11U) == 0);
	for (index = 0U; index < 256U; ++index)
		CHECK(console_output[11U + index] == 'y');
	CHECK(memcmp(console_output + 267U, "\nBE_MVP_G1: z\n", 14U) == 0);
	harts[0].console.length = 0U;
	length = feed_bytes(0U, input, 256U);
	CHECK(length == 0U && harts[0].console.length == 256U);
	length = feed(0U, "\n");
	CHECK(length == 268U && console_output[267] == '\n');
	CHECK(harts[0].console.length == 0U);
	/* The worst case, a full buffer, one more byte, then 255 LFs: 256
	 * LINE records from one call. */
	length = feed_bytes(0U, input, 256U);
	memset(input, '\n', sizeof(input));
	input[0] = 'q';
	length = feed_bytes(0U, input, 256U);
	CHECK(length == 256U * 12U + 257U);
	CHECK(memcmp(console_output + 268U, "BE_MVP_G0: q\n", 13U) == 0);
	for (index = 0U; index < 254U; ++index)
		CHECK(memcmp(console_output + 281U + index * 12U,
			     "BE_MVP_G0: \n", 12U) == 0);
	/* A chunk of CRs posts nothing. */
	memset(input, '\r', sizeof(input));
	CHECK(feed_bytes(0U, input, 256U) == 0U);
	CHECK(harts[0].console.length == 0U);
	/* Flush: the partial line, ended; nothing buffered posts nothing. */
	CHECK(be_mvp_console_flush(&harts[0], &outbound[0], EXIT_TIME) == 0U);
	(void)feed(1U, "partial");
	CHECK(be_mvp_console_flush(&harts[1], &outbound[1], EXIT_TIME) == 1U);
	length = drain(1U, 1U);
	CHECK(output_is(length, "BE_MVP_G1: partial\n"));
	CHECK(harts[1].console.length == 0U);
	CHECK(be_mvp_console_flush(&harts[1], &outbound[1], EXIT_TIME) == 0U);
	/* A stopped or failed hart flushes its partial line too. */
	(void)feed(1U, "last words");
	harts[1].phase = BE_MVP_PHASE_STOPPED;
	CHECK(be_mvp_console_flush(&harts[1], &outbound[1], EXIT_TIME) == 1U);
	length = drain(1U, 1U);
	CHECK(output_is(length, "BE_MVP_G1: last words\n"));
	harts[1].phase = BE_MVP_PHASE_RUNNING;
	/* Invalid requests change nothing. */
	memset(input, 'x', sizeof(input));
	(void)feed(0U, "kept");
	copy = harts[0];
	CHECK(be_mvp_console_feed(&harts[0], &outbound[0], input, 257U,
				  EXIT_TIME) == BE_MVP_CONSOLE_INVALID);
	CHECK(be_mvp_console_feed((struct be_mvp_state *)0, &outbound[0],
				  input, 1U, EXIT_TIME) ==
	      BE_MVP_CONSOLE_INVALID);
	CHECK(be_mvp_console_feed(&harts[0], (struct be_mvp_ring *)0, input,
				  1U, EXIT_TIME) == BE_MVP_CONSOLE_INVALID);
	CHECK(be_mvp_console_feed(&harts[0], &outbound[0], (const be_u8 *)0,
				  1U, EXIT_TIME) == BE_MVP_CONSOLE_INVALID);
	CHECK(be_mvp_console_flush((struct be_mvp_state *)0, &outbound[0],
				   EXIT_TIME) == BE_MVP_CONSOLE_INVALID);
	CHECK(be_mvp_console_flush(&harts[0], (struct be_mvp_ring *)0,
				   EXIT_TIME) == BE_MVP_CONSOLE_INVALID);
	CHECK(memcmp(&copy, &harts[0], sizeof(copy)) == 0);
	/* Only a running hart takes bytes. */
	harts[0].phase = BE_MVP_PHASE_STOPPED;
	CHECK(be_mvp_console_feed(&harts[0], &outbound[0], input, 1U,
				  EXIT_TIME) == BE_MVP_CONSOLE_INVALID);
	harts[0].phase = BE_MVP_PHASE_FAILED;
	CHECK(be_mvp_console_feed(&harts[0], &outbound[0], input, 1U,
				  EXIT_TIME) == BE_MVP_CONSOLE_INVALID);
	harts[0].phase = BE_MVP_PHASE_RUNNING;
	CHECK(memcmp(&copy, &harts[0], sizeof(copy)) == 0);
	harts[0].console.length = 257U;
	CHECK(be_mvp_console_feed(&harts[0], &outbound[0], input, 1U,
				  EXIT_TIME) == BE_MVP_CONSOLE_INVALID);
	CHECK(be_mvp_console_flush(&harts[0], &outbound[0], EXIT_TIME) ==
	      BE_MVP_CONSOLE_INVALID);
	CHECK(harts[0].console.length == 257U);
	harts[0].console.length = 0U;
	CHECK(be_mvp_console_feed(&harts[0], &outbound[0], input, 0U,
				  EXIT_TIME) == 0U);
	CHECK(outbound[0].failed == 0U && outbound[1].failed == 0U);

	/* A full ring: the line is refused, never overwritten, and the hart
	 * fails as ring; a later flush cannot post either. */
	SCENARIO();
	harts[0] = fresh_state();
	open_outbound(0U, BE_MVP_RING_MIN_BYTES);
	memset(input, 'f', sizeof(input));
	input[100] = '\n';
	for (index = 0U; index < 4U; ++index) {
		CHECK(be_mvp_console_feed(&harts[0], &outbound[0], input, 101U,
					  EXIT_TIME) == 1U);
		CHECK(be_mvp_ring_publish(&outbound[0]) == 1);
	}
	CHECK(harts[0].counts.lines == 4U &&
	      ring_index[0][0].value == 4U * 120U);
	CHECK(be_mvp_console_feed(&harts[0], &outbound[0], input, 101U,
				  EXIT_TIME) == BE_MVP_CONSOLE_FULL);
	CHECK(harts[0].phase == BE_MVP_PHASE_FAILED &&
	      harts[0].failure == BE_MVP_CLASS_RING);
	CHECK(harts[0].counts.lines == 4U && outbound[0].failed == 1U);
	CHECK(be_mvp_console_feed(&harts[0], &outbound[0], input, 1U,
				  EXIT_TIME) == BE_MVP_CONSOLE_INVALID);
	harts[0].console.length = 3U;
	CHECK(be_mvp_console_flush(&harts[0], &outbound[0], EXIT_TIME) ==
	      BE_MVP_CONSOLE_FULL);
	CHECK(harts[0].failure == BE_MVP_CLASS_RING);
	CHECK(ring_index[0][0].value == 4U * 120U);
	/* Hart 0 still drains the four lines the ring took. */
	CHECK(be_mvp_ring_acquire(&drain_view[0]) == 4U * 120U);
	for (index = 0U; index < 4U; ++index) {
		CHECK(be_mvp_ring_take(&drain_view[0], &taken) ==
		      BE_MVP_RING_RECORD);
		CHECK(taken.type == BE_MVP_RECORD_LINE && taken.length == 100U);
	}
	CHECK(be_mvp_ring_take(&drain_view[0], &taken) == BE_MVP_RING_EMPTY);
}

/*
 * Two domain harts' output, fed in pseudo-random chunks as their DBCN
 * calls arrive and drained by hart 0 in pseudo-random order, never forms a
 * mixed line: every printed line holds one domain's prefix and exactly one
 * of that domain's lines, in order.
 */
#define TRANSCRIPT_BYTES	65536U

static char transcript[TRANSCRIPT_BYTES];

static void guest_text(unsigned int domain, char *text, be_u64 *length)
{
	be_u64 used = 0U;
	unsigned int line;
	unsigned int column;

	for (line = 0U; line < 40U; ++line) {
		unsigned int width = (line * 37U + domain * 11U) % 200U;

		used += (be_u64)sprintf(text + used, "G%u line %02u:", domain,
					line);
		for (column = 0U; column < width; ++column)
			text[used++] = (char)('a' + (column + line + domain) %
					      26U);
		if (line % 5U == 0U)
			text[used++] = '\r';
		text[used++] = '\n';
	}
	*length = used;
}

static void test_console_interleave(void)
{
	static char text[2][16384];
	be_u64 lengths[2];
	be_u64 offsets[2] = { 0U, 0U };
	be_u64 pending[2] = { 0U, 0U };
	be_u64 written = 0U;
	be_u64 seed = BE_U64_C(0x2545f4914f6cdd1d);
	unsigned int domain;
	unsigned int lines[2] = { 0U, 0U };
	char *line;
	char *next;

	SCENARIO();
	open_harts();
	for (domain = 0U; domain < 2U; ++domain)
		guest_text(domain, text[domain], &lengths[domain]);
	while (offsets[0] < lengths[0] || offsets[1] < lengths[1] ||
	       pending[0] != 0U || pending[1] != 0U) {
		be_u64 chunk;
		be_u64 posted;

		seed ^= seed << 13;
		seed ^= seed >> 7;
		seed ^= seed << 17;
		domain = (unsigned int)(seed >> 40) & 1U;
		/* Hart 0 drains one domain's ring now and then. */
		if ((seed >> 20) % 4U == 0U ||
		    (offsets[0] == lengths[0] && offsets[1] == lengths[1])) {
			be_u64 out = drain(domain, pending[domain]);

			CHECK(written + out < TRANSCRIPT_BYTES);
			memcpy(transcript + written, console_output,
			       (size_t)out);
			written += out;
			pending[domain] = 0U;
			continue;
		}
		if (offsets[domain] == lengths[domain])
			domain ^= 1U;
		chunk = 1U + (seed % BE_MVP_DBCN_MAX_BYTES);
		if (chunk > lengths[domain] - offsets[domain])
			chunk = lengths[domain] - offsets[domain];
		posted = be_mvp_console_feed(&harts[domain], &outbound[domain],
					     (const be_u8 *)text[domain] +
						     offsets[domain],
					     chunk, EXIT_TIME);
		CHECK(posted != BE_MVP_CONSOLE_INVALID &&
		      posted != BE_MVP_CONSOLE_FULL);
		pending[domain] += posted;
		offsets[domain] += chunk;
	}
	CHECK(harts[0].console.length == 0U && harts[1].console.length == 0U);
	CHECK(harts[0].counts.lines == 40U && harts[1].counts.lines == 40U);
	transcript[written] = '\0';
	/* Parse the transcript back: one domain per line, lines in order. */
	for (line = transcript; *line != '\0'; line = next + 1) {
		char expected[64];
		be_u64 width;

		next = strchr(line, '\n');
		CHECK(next != (char *)0);
		*next = '\0';
		CHECK(strncmp(line, "BE_MVP_G", 8U) == 0);
		domain = (unsigned int)(line[8] - '0');
		CHECK(domain < 2U && strncmp(line + 9, ": ", 2U) == 0);
		(void)sprintf(expected, "G%u line %02u:", domain,
			      lines[domain]);
		CHECK(strncmp(line + 11, expected, strlen(expected)) == 0);
		/* No other domain's text inside the line. */
		CHECK(strstr(line + 11, "BE_MVP_G") == (char *)0);
		CHECK(strchr(line + 11, '\r') == (char *)0);
		width = (be_u64)strlen(line + 11) - strlen(expected);
		CHECK(width == (lines[domain] * 37U + domain * 11U) % 200U);
		++lines[domain];
	}
	CHECK(lines[0] == 40U && lines[1] == 40U);
}

/* The per-domain CSR set, SPP, and the readback compare. */
static void test_vcsr(void)
{
	static const char *const names[] = {
		"vsstatus", "vsie", "vstvec", "vsscratch", "vsepc", "vscause",
		"vstval", "vsatp", "vstimecmp", "scounteren", "senvcfg",
	};
	static const unsigned int bits[] = { 0U, 5U, 32U, 63U };
	struct be_mvp_exit record;
	be_u64 csr[BE_MVP_VCSR_COUNT];
	be_u64 readback[BE_MVP_VCSR_COUNT];
	be_u32 index;
	be_size slot;
	unsigned int bit;

	SCENARIO();
	/* The initial set: zero, but vsstatus.UXL = 2 and vstimecmp ~0. */
	memset(csr, 0xa5, sizeof(csr));
	be_mvp_vcsr_initial(csr);
	for (index = 0U; index < BE_MVP_VCSR_COUNT; ++index)
		CHECK(csr[index] == (index == BE_MVP_VCSR_VSSTATUS ?
				     BE_U64_C(0x200000000) :
				     index == BE_MVP_VCSR_VSTIMECMP ?
				     ALL_ONES : 0U));
	be_mvp_vcsr_initial((be_u64 *)0);
	/* SPP follows SPVP alone: an IPI that struck VU code resumes in VU
	 * mode. */
	record = exit_with(SSI, ECALL_PC);
	record.hstatus = BE_U64_C(0x200000080);
	CHECK(be_mvp_record_spp(&record) == 0U);
	record.hstatus = BE_U64_C(0x200000180);
	CHECK(be_mvp_record_spp(&record) == 0x100U);
	for (bit = 0U; bit < 64U; ++bit) {
		record.hstatus = BE_U64_C(1) << bit;
		CHECK(be_mvp_record_spp(&record) == (bit == 8U ? 0x100U : 0U));
		record.hstatus = ~(BE_U64_C(1) << bit);
		CHECK(be_mvp_record_spp(&record) == (bit == 8U ? 0U : 0x100U));
	}
	CHECK(be_mvp_record_spp((const struct be_mvp_exit *)0) == 0U);
	/* The readback compare names the first CSR that differs. */
	memcpy(readback, csr, sizeof(csr));
	CHECK(be_mvp_vcsr_mismatch(csr, readback) == BE_MVP_VCSR_COUNT);
	for (index = 0U; index < BE_MVP_VCSR_COUNT; ++index) {
		for (slot = 0U; slot < BE_ARRAY_SIZE(bits); ++slot) {
			memcpy(readback, csr, sizeof(csr));
			readback[index] ^= BE_U64_C(1) << bits[slot];
			CHECK(be_mvp_vcsr_mismatch(csr, readback) == index);
			if (index + 1U < BE_MVP_VCSR_COUNT) {
				readback[index + 1U] ^= 1U;
				CHECK(be_mvp_vcsr_mismatch(csr, readback) ==
				      index);
			}
		}
	}
	CHECK(be_mvp_vcsr_mismatch((const be_u64 *)0, readback) == 0U);
	CHECK(be_mvp_vcsr_mismatch(csr, (const be_u64 *)0) == 0U);
	/* The names an arming DETAIL line prints. */
	CHECK(BE_ARRAY_SIZE(names) == BE_MVP_VCSR_COUNT);
	for (index = 0U; index < BE_MVP_VCSR_COUNT; ++index)
		CHECK(strcmp(be_mvp_vcsr_name(index), names[index]) == 0);
	CHECK(strcmp(be_mvp_vcsr_name(BE_MVP_VCSR_COUNT), "invalid") == 0);
	CHECK(strcmp(be_mvp_vcsr_name(99U), "invalid") == 0);
}

/* The IPI exit, and B7's slice and idling wfi, now terminal. */
static void test_ipi_exit(void)
{
	struct be_mvp_state state;
	struct be_mvp_exit record;
	struct be_mvp_result result;
	unsigned int spvp;

	SCENARIO();
	/* The supervisor software interrupt at V=1: the IPI, from VS or VU,
	 * at any PC; it resumes where it struck. */
	for (spvp = 0U; spvp < 2U; ++spvp) {
		state = fresh_state();
		record = exit_with(SSI, ECALL_PC);
		if (spvp == 0U)
			record.hstatus &= ~BE_MVP_HSTATUS_SPVP;
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_IPI);
		CHECK(result.resume_pc == ECALL_PC && result.error == 0 &&
		      result.value == 0U &&
		      result.failure == BE_MVP_CLASS_NONE);
		CHECK(state.counts.ipi == 1U && state.counts.exits == 1U &&
		      call_sum(&state.counts) == 0U);
		CHECK(state.phase == BE_MVP_PHASE_RUNNING);
	}
	state = fresh_state();
	record = exit_with(SSI, ALL_ONES);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_IPI);
	CHECK(result.resume_pc == ALL_ONES);
	/* The registers of an SBI call do not make an IPI a call. */
	state = fresh_state();
	record = exit_with(SSI, ECALL_PC);
	record.frame.gpr[BE_R4_GPR_A7] = BE_MVP_SBI_EID_SRST;
	record.frame.gpr[BE_R4_GPR_A6] = 0U;
	record.frame.gpr[BE_R4_GPR_A0] = 0U;
	record.frame.gpr[BE_R4_GPR_A1] = 0U;
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_IPI);
	CHECK(state.phase == BE_MVP_PHASE_RUNNING && state.counts.srst == 0U);
	/* B7's HS slice, the supervisor timer at V=1, is terminal: domain
	 * harts never enable STIE. */
	for (spvp = 0U; spvp < 2U; ++spvp) {
		state = fresh_state();
		record = exit_with(STI, ECALL_PC);
		if (spvp == 0U)
			record.hstatus &= ~BE_MVP_HSTATUS_SPVP;
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_TERMINAL);
		CHECK(result.failure == BE_MVP_CLASS_INTERRUPT);
		CHECK(state.counts.ipi == 0U);
	}
	/* B7's idling wfi: with VTW clear a guest wfi runs natively, so a
	 * virtual-instruction exit for one is terminal, from VS or VU. */
	for (spvp = 0U; spvp < 2U; ++spvp) {
		state = fresh_state();
		record = exit_with(BE_MVP_SCAUSE_VIRTUAL_INSTRUCTION, ECALL_PC);
		record.frame.stval = WFI;
		if (spvp == 0U)
			record.hstatus &= ~BE_MVP_HSTATUS_SPVP;
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_TERMINAL);
		CHECK(result.failure == BE_MVP_CLASS_VIRTUAL_INSTRUCTION);
	}
	/* IPIs count against the ceiling. */
	state = (struct be_mvp_state)BE_MVP_STATE_INITIALIZER(2U);
	record = exit_with(SSI, ECALL_PC);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_IPI);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_IPI);
	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record, &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXIT_BUDGET);
	CHECK(state.counts.exits == 3U && state.counts.ipi == 2U);
}

/* Hart 0's inbound ring to a domain hart, both views. */
static be_u8 inbound_bytes[BE_MVP_INBOUND_RING_BYTES];
static struct be_mvp_ring_index inbound_index[2];
static struct be_mvp_ring inbound_writer;
static struct be_mvp_ring inbound;

static void open_inbound(be_u32 domain)
{
	be_mvp_ring_reset(&inbound_index[0], &inbound_index[1]);
	CHECK(be_mvp_ring_init(&inbound_writer, inbound_bytes,
			       BE_MVP_INBOUND_RING_BYTES, &inbound_index[0],
			       &inbound_index[1], BE_MVP_RECORDS_INBOUND,
			       domain, BE_MVP_RING_WRITER) == 1);
	CHECK(be_mvp_ring_init(&inbound, inbound_bytes,
			       BE_MVP_INBOUND_RING_BYTES, &inbound_index[0],
			       &inbound_index[1], BE_MVP_RECORDS_INBOUND,
			       domain, BE_MVP_RING_READER) == 1);
}

/* Hart 0 posts @count PINGs at @time, publishes; the hart acquires. */
static void ping(be_u64 count, be_u64 time)
{
	be_u64 index;

	for (index = 0U; index < count; ++index)
		CHECK(be_mvp_ring_post(&inbound_writer, BE_MVP_RECORD_PING,
				       time + index, (const be_u8 *)0, 0U) ==
		      1);
	CHECK(be_mvp_ring_publish(&inbound_writer) == 1);
	(void)be_mvp_ring_acquire(&inbound);
}

/* The domain hart's IPI exit, and its service at @now. */
static be_u64 serve(be_u64 now)
{
	struct be_mvp_exit record = exit_with(SSI, ECALL_PC);
	struct be_mvp_result result;

	record.time = now - 5U;
	CHECK(be_mvp_handle_exit(&harts[1], &windows[1], &no_leaf, &record,
				 &result) ==
	      BE_MVP_ACTION_IPI);
	return be_mvp_ipi_serve(&harts[1], &inbound, &outbound[1], &record,
				now);
}

static void expect_ipi_failed(enum be_mvp_class failure)
{
	CHECK(harts[1].phase == BE_MVP_PHASE_FAILED &&
	      harts[1].failure == failure);
}

static void test_ipi_serve(void)
{
	struct be_mvp_exit record = exit_with(SSI, ECALL_PC);
	be_u64 index;

	/* One PING: one PONG with the PING's time, the receipt, and SPV. */
	SCENARIO();
	open_harts();
	open_inbound(1U);
	ping(1U, 0x1000U);
	CHECK(serve(0x2000U) == 1U);
	CHECK(harts[1].phase == BE_MVP_PHASE_RUNNING &&
	      harts[1].counts.ipi == 1U);
	CHECK(be_mvp_ring_release(&inbound) == 1 &&
	      inbound_index[1].value == 16U);
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[1]) == 40U);
	CHECK(be_mvp_ring_take(&drain_view[1], &taken) == BE_MVP_RING_RECORD);
	CHECK(taken.type == BE_MVP_RECORD_PONG && taken.domain == 1U &&
	      taken.time == 0x2000U && taken.length == 24U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_PONG_SENT) == 0x1000U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_PONG_RECEIVED) == 0x2000U - 5U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_PONG_SPV) == 1U);
	/* Two PINGs before one IPI: two PONGs, in order. */
	ping(2U, 0x3000U);
	CHECK(serve(0x4000U) == 2U);
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[1]) == 80U);
	for (index = 0U; index < 2U; ++index) {
		CHECK(be_mvp_ring_take(&drain_view[1], &taken) ==
		      BE_MVP_RING_RECORD);
		CHECK(be_mvp_record_word(&taken, BE_MVP_PONG_SENT) ==
		      0x3000U + index);
	}
	CHECK(harts[1].counts.ipi == 2U && harts[1].counts.exits == 2U);
	/* A PONG reports SPV as the record has it. */
	ping(1U, 0x5000U);
	record.hstatus &= ~BE_MVP_HSTATUS_SPV;
	CHECK(be_mvp_ipi_serve(&harts[1], &inbound, &outbound[1], &record,
			       0x6000U) == 1U);
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[1]) == 40U);
	CHECK(be_mvp_ring_take(&drain_view[1], &taken) == BE_MVP_RING_RECORD);
	CHECK(be_mvp_record_word(&taken, BE_MVP_PONG_SPV) == 0U);

	/* An IPI with no PING: FAIL ipi. */
	SCENARIO();
	open_harts();
	open_inbound(1U);
	(void)be_mvp_ring_acquire(&inbound);
	CHECK(serve(0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	CHECK(outbound[1].cursor == 0U);
	/* Unacquired PINGs are not there yet. */
	SCENARIO();
	open_harts();
	open_inbound(1U);
	CHECK(be_mvp_ring_post(&inbound_writer, BE_MVP_RECORD_PING, 1U,
			       (const be_u8 *)0, 0U) == 1);
	CHECK(be_mvp_ring_publish(&inbound_writer) == 1);
	CHECK(serve(0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	/* A record other than PING: FAIL ipi, even after a PING. */
	SCENARIO();
	open_harts();
	open_inbound(1U);
	CHECK(be_mvp_ring_post(&inbound_writer, BE_MVP_RECORD_ACK, 1U,
			       (const be_u8 *)0, 0U) == 1);
	ping(0U, 0U);
	CHECK(serve(0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	SCENARIO();
	open_harts();
	open_inbound(1U);
	CHECK(be_mvp_ring_post(&inbound_writer, BE_MVP_RECORD_PING, 1U,
			       (const be_u8 *)0, 0U) == 1);
	CHECK(be_mvp_ring_post(&inbound_writer, BE_MVP_RECORD_ACK, 2U,
			       (const be_u8 *)0, 0U) == 1);
	ping(0U, 0U);
	CHECK(serve(0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	/* A PING with a payload is not a PING. */
	SCENARIO();
	open_harts();
	open_inbound(1U);
	CHECK(be_mvp_ring_post(&inbound_writer, BE_MVP_RECORD_PING, 1U,
			       (const be_u8 *)"x", 1U) == 1);
	ping(0U, 0U);
	CHECK(serve(0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	/* A malformed inbound ring: FAIL ring. */
	SCENARIO();
	open_harts();
	open_inbound(1U);
	ping(1U, 0x1000U);
	inbound_bytes[1] = 0U;
	CHECK(serve(0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_RING);
	/* A full outbound ring: FAIL ring. */
	SCENARIO();
	open_harts();
	open_inbound(1U);
	open_outbound(1U, BE_MVP_RING_MIN_BYTES);
	for (index = 0U; index < 12U; ++index)
		CHECK(be_mvp_ring_post(&outbound[1], BE_MVP_RECORD_LINE, 1U,
				       (const be_u8 *)"0123456789abcdef",
				       16U) == 1);
	CHECK(outbound[1].cursor == 384U);
	ping(4U, 0x1000U);
	CHECK(serve(0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_RING);
	CHECK(outbound[1].cursor == 384U + 3U * 40U);
	/* A hart that is not running, and absent arguments. */
	SCENARIO();
	open_harts();
	open_inbound(1U);
	ping(1U, 0x1000U);
	harts[1].phase = BE_MVP_PHASE_STOPPED;
	CHECK(be_mvp_ipi_serve(&harts[1], &inbound, &outbound[1], &record,
			       0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	harts[1] = fresh_state();
	CHECK(be_mvp_ipi_serve(&harts[1], (struct be_mvp_ring *)0,
			       &outbound[1], &record, 0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	harts[1] = fresh_state();
	CHECK(be_mvp_ipi_serve(&harts[1], &inbound, (struct be_mvp_ring *)0,
			       &record, 0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	harts[1] = fresh_state();
	CHECK(be_mvp_ipi_serve(&harts[1], &inbound, &outbound[1],
			       (const struct be_mvp_exit *)0, 0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	CHECK(be_mvp_ipi_serve((struct be_mvp_state *)0, &inbound,
			       &outbound[1], &record, 0x2000U) == 0U);
	/* The PING is still there for a hart that can serve it. */
	harts[1] = fresh_state();
	CHECK(be_mvp_ipi_serve(&harts[1], &inbound, &outbound[1], &record,
			       0x2000U) == 1U);
}

static void take_from(unsigned int domain, enum be_mvp_record_type type,
		      be_u64 length, be_u64 time)
{
	CHECK(be_mvp_ring_take(&drain_view[domain], &taken) ==
	      BE_MVP_RING_RECORD);
	CHECK(taken.type == type && taken.domain == domain &&
	      taken.length == length && taken.time == time);
}

/*
 * The domain hart's READY, ENTERED, SHUTDOWN, and FAIL records, as hart 0
 * drains them, and as its control loop accepts them.
 */
static void test_records(void)
{
	struct be_mvp_controls controls = armed_controls();
	struct be_mvp_control control;
	struct be_mvp_step_result step;
	struct be_mvp_exit entry;
	be_u64 detail[BE_MVP_FAIL_DETAIL_WORDS + 1U];
	be_u64 index;

	SCENARIO();
	open_harts();
	be_mvp_control_init(&control, ENTRY_TIME - 0x100U, BE_MVP_RUN_BUDGET,
			    BE_MVP_READY_TICKS);
	CHECK(be_mvp_control_started(&control, 0U, 1U) == 1);
	controls.hedeleg = ARMED_HEDELEG_WARL;
	CHECK(be_mvp_post_ready(&outbound[0], &controls, ENTRY_TIME) == 1);
	be_mvp_entry_frame(&entry, BE_MVP_KERNEL_GPA, BE_MVP_GUEST_HART,
			   BE_MVP_DTB_GPA);
	CHECK(be_mvp_post_entered(&outbound[0], &entry, ENTRY_TIME + 1U) == 1);
	CHECK(be_mvp_ring_publish(&outbound[0]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[0]) == 16U + 64U + 16U + 24U);
	take_from(0U, BE_MVP_RECORD_READY, BE_MVP_READY_WORDS * 8U,
		  ENTRY_TIME);
	CHECK(be_mvp_record_word(&taken, BE_MVP_READY_HGATP) ==
	      BE_MVP_G0_HGATP);
	CHECK(be_mvp_record_word(&taken, BE_MVP_READY_HSTATUS) == 0x180U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_READY_HEDELEG) ==
	      ARMED_HEDELEG_WARL);
	CHECK(be_mvp_record_word(&taken, BE_MVP_READY_HIDELEG) == 0x40U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_READY_HCOUNTEREN) == 0x2U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_READY_SIE) == 0x2U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_READY_HENVCFG) ==
	      ARMED_HENVCFG);
	CHECK(be_mvp_record_word(&taken, BE_MVP_READY_VSTIMECMP) == ALL_ONES);
	CHECK(be_mvp_control_record(&control, 0U, &taken, &step) ==
	      BE_MVP_STEP_READY);
	take_from(0U, BE_MVP_RECORD_ENTERED, BE_MVP_ENTERED_WORDS * 8U,
		  ENTRY_TIME + 1U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_ENTERED_PC) ==
	      BE_U64_C(0x80200000));
	CHECK(be_mvp_record_word(&taken, BE_MVP_ENTERED_A0) == 0U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_ENTERED_A1) ==
	      BE_U64_C(0x83e00000));
	CHECK(be_mvp_control_record(&control, 0U, &taken, &step) ==
	      BE_MVP_STEP_ENTERED);
	/* The first line asks for the PING; the IPI answers it. */
	(void)be_mvp_console_feed(&harts[0], &outbound[0],
				  (const be_u8 *)"hello\n", 6U,
				  ENTRY_TIME + 2U);
	CHECK(be_mvp_ring_post_words(&outbound[0], BE_MVP_RECORD_PONG,
				     ENTRY_TIME + 3U, detail, 0U) == 1);
	CHECK(be_mvp_ring_publish(&outbound[0]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[0]) == 24U + 16U);
	take_from(0U, BE_MVP_RECORD_LINE, 5U, ENTRY_TIME + 2U);
	CHECK(be_mvp_control_record(&control, 0U, &taken, &step) ==
	      BE_MVP_STEP_LINE && step.ping == 1U);
	take_from(0U, BE_MVP_RECORD_PONG, 0U, ENTRY_TIME + 3U);
	/* A PONG of the wrong size is refused by hart 0; a real one comes
	 * from be_mvp_ipi_serve(). */
	{
		struct be_mvp_control copy = control;

		CHECK(be_mvp_control_record(&copy, 0U, &taken, &step) ==
		      BE_MVP_STEP_INVALID);
		CHECK(step.failure == BE_MVP_CLASS_RING);
	}
	open_inbound(0U);
	ping(1U, ENTRY_TIME + 3U);
	entry = exit_with(SSI, ECALL_PC);
	entry.time = ENTRY_TIME + 4U;
	CHECK(be_mvp_handle_exit(&harts[0], &window, &no_leaf, &entry,
				 &(struct be_mvp_result){ 0 }) ==
	      BE_MVP_ACTION_IPI);
	CHECK(be_mvp_ipi_serve(&harts[0], &inbound, &outbound[0], &entry,
			       ENTRY_TIME + 5U) == 1U);
	/* The guest shuts down: SRST, flush, then SHUTDOWN. */
	entry = ecall(BE_MVP_SBI_EID_SRST, 0U, 0U, 0U, 0U);
	CHECK(be_mvp_handle_exit(&harts[0], &window, &no_leaf, &entry,
				 &(struct be_mvp_result){ 0 }) ==
	      BE_MVP_ACTION_SHUTDOWN);
	harts[0].console.length = 3U;
	memcpy(harts[0].console.text, "bye", 3U);
	CHECK(be_mvp_console_flush(&harts[0], &outbound[0], ENTRY_TIME + 6U) ==
	      1U);
	CHECK(be_mvp_post_shutdown(&harts[0], &outbound[0], ENTRY_TIME + 1U,
				   ENTRY_TIME + 7U) == 1);
	CHECK(be_mvp_ring_publish(&outbound[0]) == 1);
	/* SHUTDOWN: 15 words since M7's console reads served. */
	CHECK(be_mvp_ring_acquire(&drain_view[0]) == 40U + 24U + 136U);
	take_from(0U, BE_MVP_RECORD_PONG, BE_MVP_PONG_WORDS * 8U,
		  ENTRY_TIME + 5U);
	CHECK(be_mvp_control_record(&control, 0U, &taken, &step) ==
	      BE_MVP_STEP_PONG);
	take_from(0U, BE_MVP_RECORD_LINE, 3U, ENTRY_TIME + 6U);
	CHECK(memcmp(taken.payload, "bye", 3U) == 0);
	CHECK(be_mvp_control_record(&control, 0U, &taken, &step) ==
	      BE_MVP_STEP_LINE && step.ping == 0U);
	take_from(0U, BE_MVP_RECORD_SHUTDOWN, BE_MVP_SHUTDOWN_WORDS * 8U,
		  ENTRY_TIME + 7U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_EXITS) == 2U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_BASE) == 0U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_SRST) == 1U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_IPI) == 1U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_LINES) == 2U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_RING_PEAK) ==
	      16U + 64U + 16U + 24U + 24U + 16U + 40U + 24U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_ENTERED) ==
	      ENTRY_TIME + 1U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_DENIALS) == 0U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_MGMT) == 0U);
	CHECK(be_mvp_control_record(&control, 0U, &taken, &step) ==
	      BE_MVP_STEP_SHUTDOWN && step.done == 0U);
	CHECK(control.domain[0].lines == 2U &&
	      control.domain[0].ring_peak == 224U);
	/* SHUTDOWN only from a stopped hart. */
	harts[1] = fresh_state();
	CHECK(be_mvp_post_shutdown(&harts[1], &outbound[1], 0U, 0U) == 0);
	CHECK(be_mvp_post_shutdown((struct be_mvp_state *)0, &outbound[1], 0U,
				   0U) == 0);
	CHECK(be_mvp_post_shutdown(&harts[0], (struct be_mvp_ring *)0, 0U,
				   0U) == 0);
	CHECK(be_mvp_post_ready(&outbound[1],
				(const struct be_mvp_controls *)0, 0U) == 0);
	CHECK(be_mvp_post_entered(&outbound[1], (const struct be_mvp_exit *)0,
				  0U) == 0);
	CHECK(outbound[1].cursor == 0U);

	/* FAIL: the class, then up to eight words of detail. */
	SCENARIO();
	open_harts();
	for (index = 0U; index < BE_ARRAY_SIZE(detail); ++index)
		detail[index] = BE_U64_C(0xd0) + index;
	CHECK(be_mvp_post_fail(&harts[1], &outbound[1], detail, 1U, 9U) == 0);
	(void)be_mvp_fail(&harts[1], BE_MVP_CLASS_VIRTUAL_INSTRUCTION);
	CHECK(be_mvp_post_fail(&harts[1], &outbound[1], detail,
			       BE_MVP_FAIL_DETAIL_WORDS + 1U, 9U) == 0);
	CHECK(be_mvp_post_fail(&harts[1], &outbound[1], (const be_u64 *)0, 1U,
			       9U) == 0);
	CHECK(be_mvp_post_fail((struct be_mvp_state *)0, &outbound[1], detail,
			       1U, 9U) == 0);
	CHECK(outbound[1].cursor == 0U);
	CHECK(be_mvp_post_fail(&harts[1], &outbound[1], detail,
			       BE_MVP_FAIL_DETAIL_WORDS, 9U) == 1);
	CHECK(be_mvp_post_fail(&harts[1], &outbound[1], (const be_u64 *)0, 0U,
			       10U) == 1);
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[1]) == 16U + 72U + 16U + 8U);
	take_from(1U, BE_MVP_RECORD_FAIL, BE_MVP_FAIL_MAX_WORDS * 8U, 9U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_FAIL_CLASS) ==
	      BE_MVP_CLASS_VIRTUAL_INSTRUCTION);
	for (index = 0U; index < BE_MVP_FAIL_DETAIL_WORDS; ++index)
		CHECK(be_mvp_record_word(&taken, 1U + index) ==
		      BE_U64_C(0xd0) + index);
	be_mvp_control_init(&control, 0U, BE_MVP_RUN_BUDGET,
			    BE_MVP_READY_TICKS);
	CHECK(be_mvp_control_started(&control, 1U, 2U) == 1);
	CHECK(be_mvp_control_record(&control, 1U, &taken, &step) ==
	      BE_MVP_STEP_FAIL);
	CHECK(step.failure == BE_MVP_CLASS_VIRTUAL_INSTRUCTION);
	take_from(1U, BE_MVP_RECORD_FAIL, 8U, 10U);
}

/*
 * A failed domain hart's wait for hart 0's ACK (Q10, as Plan revision M1-B
 * revises it): the window measures hart 0's progress through the outbound
 * ring's tail; a still tail, a malformed one, or no wait record falls
 * back, and the ACK parks the hart.
 */
#define ACK_WINDOW		BE_MVP_FAIL_ACK_TICKS
#define ACK_START		BE_U64_C(0x40000000)
#define ACK_TAIL		BE_U64_C(0x1000)
#define ACK_HEAD		BE_U64_C(0x2000)
/* The board's console: 115200 baud, 8N1, so 11,520 bytes a second. */
#define CONSOLE_BYTES_PER_SECOND	BE_U64_C(11520)
/*
 * A replayed backlog of lines of the board's mean length: the 89 guest
 * lines the stopped no-inject run printed before its first FAIL hold 73
 * bytes each on average (Plan revision M1-B); 64 a domain, so that hart 0
 * prints for longer than the window.
 */
#define BACKLOG_LINES		64U
#define BACKLOG_BYTES		73U

static enum be_mvp_ack_step ack_step(struct be_mvp_ack_wait *wait,
				     be_u64 now, be_u64 tail,
				     int acknowledged)
{
	return be_mvp_ack_wait_step(wait, now, tail, ACK_HEAD, acknowledged);
}

/* The first step of a wait started at ACK_START with the tail ACK_TAIL. */
static enum be_mvp_ack_step first_step(be_u64 now, be_u64 tail, be_u64 head,
				       int acknowledged)
{
	struct be_mvp_ack_wait wait;

	be_mvp_ack_wait_start(&wait, ACK_START, ACK_TAIL);
	return be_mvp_ack_wait_step(&wait, now, tail, head, acknowledged);
}

/*
 * The ticks hart 0 takes to print one domain line of @length bytes through
 * the board's console: the prefix, the line, and its end, CR and LF as the
 * board's capture shows it.
 */
static be_u64 print_ticks(be_u64 length)
{
	return (BE_MVP_DOMAIN_PREFIX_LENGTH + length + 2U) *
	       BE_MVP_TIMEBASE_HZ / CONSOLE_BYTES_PER_SECOND;
}

/* The domain hart's step on its own outbound ring, domain 0's. */
static enum be_mvp_ack_step ring_step(struct be_mvp_ack_wait *wait,
				      be_u64 now, int acknowledged)
{
	return be_mvp_ack_wait_step(wait, now, be_mvp_ring_taken(&outbound[0]),
				    be_mvp_ring_published(&outbound[0]),
				    acknowledged);
}

/*
 * Domain 0's hart fails behind BACKLOG_LINES LINE records: its FAIL is
 * posted and published, and its wait starts, at @now.
 */
static void fail_behind_backlog(struct be_mvp_ack_wait *wait, be_u64 now)
{
	be_u64 detail[BE_MVP_FAIL_DETAIL_WORDS] = { 0 };
	be_u8 text[BACKLOG_BYTES];
	be_u64 index;

	open_harts();
	memset(text, 'x', sizeof(text));
	for (index = 0U; index < BACKLOG_LINES; ++index)
		CHECK(be_mvp_ring_post(&outbound[0], BE_MVP_RECORD_LINE, now,
				       text, sizeof(text)) == 1);
	(void)be_mvp_fail(&harts[0], BE_MVP_CLASS_GUEST_PAGE_FAULT);
	CHECK(be_mvp_post_fail(&harts[0], &outbound[0], detail,
			       BE_MVP_FAIL_DETAIL_WORDS, now) == 1);
	CHECK(be_mvp_ring_publish(&outbound[0]) == 1);
	be_mvp_ack_wait_start(wait, now, be_mvp_ring_taken(&outbound[0]));
	CHECK(wait->since == now && wait->taken == 0U);
	CHECK(be_mvp_ring_published(&outbound[0]) ==
	      BACKLOG_LINES * be_mvp_ring_record_bytes(BACKLOG_BYTES) +
	      be_mvp_ring_record_bytes(BE_MVP_FAIL_MAX_WORDS * 8U));
}

/*
 * Hart 0's visit to domain 0's ring (M0-C.1): acquire, take one record,
 * release the tail, and only then print it.
 */
static void take_one(void)
{
	CHECK(be_mvp_ring_acquire(&drain_view[0]) != 0U);
	CHECK(be_mvp_ring_take(&drain_view[0], &taken) == BE_MVP_RING_RECORD);
	CHECK(be_mvp_ring_release(&drain_view[0]) == 1);
}

static void test_ack_wait(void)
{
	struct be_mvp_ack_wait wait;
	be_u64 start;
	be_u64 now;
	be_u64 index;

	/* The ACK parks the hart, at once or after progress, before every
	 * other rule: a window long past, or a malformed tail. */
	SCENARIO();
	be_mvp_ack_wait_start(&wait, ACK_START, ACK_TAIL);
	CHECK(wait.since == ACK_START && wait.taken == ACK_TAIL);
	CHECK(ack_step(&wait, ACK_START, ACK_TAIL, 1) == BE_MVP_ACK_PARK);
	CHECK(first_step(ACK_START + 4U * ACK_WINDOW, ACK_TAIL, ACK_HEAD, -1) ==
	      BE_MVP_ACK_PARK);
	CHECK(first_step(ACK_START, ACK_TAIL - 8U, ACK_HEAD, 1) ==
	      BE_MVP_ACK_PARK);
	CHECK(first_step(ACK_START, ACK_HEAD + 8U, ACK_HEAD, 1) ==
	      BE_MVP_ACK_PARK);
	be_mvp_ack_wait_start(&wait, ACK_START, ACK_TAIL);
	CHECK(ack_step(&wait, ACK_START + 1U, ACK_TAIL + 24U, 0) ==
	      BE_MVP_ACK_WAIT);
	CHECK(wait.since == ACK_START + 1U && wait.taken == ACK_TAIL + 24U);
	CHECK(ack_step(&wait, ACK_START + 2U, ACK_TAIL + 24U, 2) ==
	      BE_MVP_ACK_PARK);

	/* A still tail: the window's last tick waits, the window falls back;
	 * a time before the window's start reads as a window long past. */
	SCENARIO();
	be_mvp_ack_wait_start(&wait, ACK_START, ACK_TAIL);
	CHECK(ack_step(&wait, ACK_START, ACK_TAIL, 0) == BE_MVP_ACK_WAIT);
	CHECK(ack_step(&wait, ACK_START + ACK_WINDOW - 1U, ACK_TAIL, 0) ==
	      BE_MVP_ACK_WAIT);
	CHECK(wait.since == ACK_START && wait.taken == ACK_TAIL);
	CHECK(ack_step(&wait, ACK_START + ACK_WINDOW, ACK_TAIL, 0) ==
	      BE_MVP_ACK_FALLBACK);
	CHECK(ack_step(&wait, ACK_START + ACK_WINDOW + 1U, ACK_TAIL, 0) ==
	      BE_MVP_ACK_FALLBACK);
	CHECK(first_step(ACK_START - 1U, ACK_TAIL, ACK_HEAD, 0) ==
	      BE_MVP_ACK_FALLBACK);

	/* Progress restarts the window, even when seen at its end. */
	SCENARIO();
	be_mvp_ack_wait_start(&wait, ACK_START, ACK_TAIL);
	now = ACK_START + ACK_WINDOW / 2U;
	CHECK(ack_step(&wait, now, ACK_TAIL + 16U, 0) == BE_MVP_ACK_WAIT);
	CHECK(wait.since == now && wait.taken == ACK_TAIL + 16U);
	CHECK(ack_step(&wait, ACK_START + ACK_WINDOW, ACK_TAIL + 16U, 0) ==
	      BE_MVP_ACK_WAIT);
	CHECK(ack_step(&wait, now + ACK_WINDOW - 1U, ACK_TAIL + 16U, 0) ==
	      BE_MVP_ACK_WAIT);
	now += ACK_WINDOW;
	CHECK(ack_step(&wait, now, ACK_TAIL + 32U, 0) == BE_MVP_ACK_WAIT);
	CHECK(ack_step(&wait, now + ACK_WINDOW - 1U, ACK_TAIL + 32U, 0) ==
	      BE_MVP_ACK_WAIT);
	CHECK(ack_step(&wait, now + ACK_WINDOW, ACK_TAIL + 32U, 0) ==
	      BE_MVP_ACK_FALLBACK);

	/* A hundred records, each taken at the window's last tick, keep the
	 * hart waiting for nearly a hundred windows; then a still tail falls
	 * back one window after the last. */
	SCENARIO();
	be_mvp_ack_wait_start(&wait, ACK_START, 0U);
	now = ACK_START;
	for (index = 1U; index <= 100U; ++index) {
		now += ACK_WINDOW - 1U;
		CHECK(be_mvp_ack_wait_step(&wait, now, (index - 1U) * 24U,
					   2400U, 0) == BE_MVP_ACK_WAIT);
		CHECK(be_mvp_ack_wait_step(&wait, now, index * 24U, 2400U,
					   0) == BE_MVP_ACK_WAIT);
	}
	CHECK(now - ACK_START == 100U * (ACK_WINDOW - 1U));
	CHECK(be_mvp_ack_wait_step(&wait, now + ACK_WINDOW - 1U, 2400U, 2400U,
				   0) == BE_MVP_ACK_WAIT);
	CHECK(be_mvp_ack_wait_step(&wait, now + ACK_WINDOW, 2400U, 2400U, 0) ==
	      BE_MVP_ACK_FALLBACK);

	/* A malformed tail falls back at once: behind the one the wait
	 * holds, or beyond the published head, where the head itself is
	 * every record taken; so does a wait started beyond the head, at its
	 * first step. The indices are 64-bit values, so a tail that wrapped
	 * past 2^64 reads as behind. */
	SCENARIO();
	CHECK(first_step(ACK_START, ACK_TAIL - 8U, ACK_HEAD, 0) ==
	      BE_MVP_ACK_FALLBACK);
	CHECK(first_step(ACK_START, 0U, ACK_HEAD, 0) == BE_MVP_ACK_FALLBACK);
	CHECK(first_step(ACK_START, ACK_HEAD + 8U, ACK_HEAD, 0) ==
	      BE_MVP_ACK_FALLBACK);
	CHECK(first_step(ACK_START, ALL_ONES, ACK_HEAD, 0) ==
	      BE_MVP_ACK_FALLBACK);
	CHECK(first_step(ACK_START, ACK_TAIL, ACK_TAIL - 8U, 0) ==
	      BE_MVP_ACK_FALLBACK);
	CHECK(first_step(ACK_START, ACK_TAIL, ACK_TAIL, 0) == BE_MVP_ACK_WAIT);
	CHECK(first_step(ACK_START, ACK_HEAD, ACK_HEAD, 0) == BE_MVP_ACK_WAIT);
	be_mvp_ack_wait_start(&wait, ACK_START, ACK_TAIL);
	CHECK(ack_step(&wait, ACK_START + 1U, ACK_HEAD, 0) == BE_MVP_ACK_WAIT);
	CHECK(wait.taken == ACK_HEAD);
	CHECK(ack_step(&wait, ACK_START + 2U, ACK_HEAD - 16U, 0) ==
	      BE_MVP_ACK_FALLBACK);
	be_mvp_ack_wait_start(&wait, ACK_START, ALL_ONES - 15U);
	CHECK(be_mvp_ack_wait_step(&wait, ACK_START, 8U, 24U, 0) ==
	      BE_MVP_ACK_FALLBACK);

	/* The time CSR's wrap: a window across 2^64 is measured as any
	 * other, and so is one restarted just before it. */
	SCENARIO();
	be_mvp_ack_wait_start(&wait, ALL_ONES - 99U, ACK_TAIL);
	CHECK(ack_step(&wait, 5U, ACK_TAIL, 0) == BE_MVP_ACK_WAIT);
	CHECK(ack_step(&wait, ACK_WINDOW - 101U, ACK_TAIL, 0) ==
	      BE_MVP_ACK_WAIT);
	CHECK(ack_step(&wait, ACK_WINDOW - 100U, ACK_TAIL, 0) ==
	      BE_MVP_ACK_FALLBACK);
	be_mvp_ack_wait_start(&wait, ALL_ONES - ACK_WINDOW, ACK_TAIL);
	CHECK(ack_step(&wait, ALL_ONES - 9U, ACK_TAIL + 8U, 0) ==
	      BE_MVP_ACK_WAIT);
	CHECK(wait.since == ALL_ONES - 9U);
	CHECK(ack_step(&wait, ACK_WINDOW - 11U, ACK_TAIL + 8U, 0) ==
	      BE_MVP_ACK_WAIT);
	CHECK(ack_step(&wait, ACK_WINDOW - 10U, ACK_TAIL + 8U, 0) ==
	      BE_MVP_ACK_FALLBACK);

	/* No wait record falls back, ACK or not; starting none does
	 * nothing. */
	SCENARIO();
	be_mvp_ack_wait_start((struct be_mvp_ack_wait *)0, ACK_START, ACK_TAIL);
	CHECK(be_mvp_ack_wait_step((struct be_mvp_ack_wait *)0, ACK_START,
				   ACK_TAIL, ACK_HEAD, 0) ==
	      BE_MVP_ACK_FALLBACK);
	CHECK(be_mvp_ack_wait_step((struct be_mvp_ack_wait *)0, ACK_START,
				   ACK_TAIL, ACK_HEAD, 1) ==
	      BE_MVP_ACK_FALLBACK);

	/* The normal end: hart 0 took every record, the FAIL last, then
	 * posted the ACK. Without the ACK the window still ends the wait. */
	SCENARIO();
	be_mvp_ack_wait_start(&wait, ACK_START, ACK_HEAD);
	CHECK(ack_step(&wait, ACK_START + 1U, ACK_HEAD, 0) == BE_MVP_ACK_WAIT);
	CHECK(ack_step(&wait, ACK_START + 2U, ACK_HEAD, 1) == BE_MVP_ACK_PARK);
	CHECK(ack_step(&wait, ACK_START + ACK_WINDOW, ACK_HEAD, 0) ==
	      BE_MVP_ACK_FALLBACK);

	/* The board's no-inject run, replayed through domain 0's ring: hart
	 * 0 takes one record of each domain per pass, and prints both lines
	 * behind the console, so the backlog outlasts the window measured
	 * from the FAIL (M0's); but each record taken restarts the window,
	 * the FAIL is taken last, and the ACK parks the hart. */
	SCENARIO();
	start = ACK_START;
	fail_behind_backlog(&wait, start);
	now = start;
	for (index = 0U; index <= BACKLOG_LINES; ++index) {
		CHECK(ring_step(&wait, now, 0) == BE_MVP_ACK_WAIT);
		take_one();
		CHECK(ring_step(&wait, now, 0) == BE_MVP_ACK_WAIT);
		CHECK(wait.since == now &&
		      wait.taken == be_mvp_ring_taken(&outbound[0]));
		if (taken.type == BE_MVP_RECORD_FAIL)
			break;
		CHECK(taken.type == BE_MVP_RECORD_LINE);
		now += print_ticks(taken.length) + print_ticks(BACKLOG_BYTES);
	}
	CHECK(index == BACKLOG_LINES && now - start >= ACK_WINDOW);
	CHECK(be_mvp_ring_taken(&outbound[0]) ==
	      be_mvp_ring_published(&outbound[0]));
	CHECK(ring_step(&wait, now + 1U, 1) == BE_MVP_ACK_PARK);

	/* A hart 0 that stops after half the backlog: one window after the
	 * last record it took, the hart falls back. */
	SCENARIO();
	fail_behind_backlog(&wait, start);
	now = start;
	for (index = 0U; index < BACKLOG_LINES / 2U; ++index) {
		take_one();
		CHECK(ring_step(&wait, now, 0) == BE_MVP_ACK_WAIT);
		now += 2U * print_ticks(BACKLOG_BYTES);
	}
	now -= 2U * print_ticks(BACKLOG_BYTES);
	CHECK(ring_step(&wait, now + ACK_WINDOW - 1U, 0) == BE_MVP_ACK_WAIT);
	CHECK(ring_step(&wait, now + ACK_WINDOW, 0) == BE_MVP_ACK_FALLBACK);
}

/*
 * The denial entry on a domain hart (planning/mvp-m1-plan.md, "The denial
 * path"): a guest-page fault from VU mode (hstatus VSXL 2, SPV, GVA; SPVP
 * 0), at a GPA no root maps or, for the reader's store, the channel page,
 * with the guest's vsstatus as Linux leaves it in U-mode.
 */
#define DENY_PC			BE_U64_C(0x10432)
#define DENY_VA			BE_U64_C(0x3fffd5000)
#define DENY_VSTVEC		BE_U64_C(0xffffffff80a011c0)
#define DENY_HSTATUS		BE_U64_C(0x2000000c0)
#define DENY_VSSTATUS		(BE_MVP_VSSTATUS_UXL64 | \
				 BE_MVP_VSSTATUS_SPIE | BE_MVP_VSSTATUS_SIE)
#define BESIDE_GPA		(BE_MVP_CHANNEL_GPA + BE_MVP_CHANNEL_BYTES)
#define PROBE_GPA		BE_U64_C(0x90000000)
#define LOAD_FAULT		BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT
#define STORE_FAULT		BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT

static struct be_mvp_state accepting_state(void)
{
	struct be_mvp_state state = fresh_state();

	state.accept_denial = 1U;
	return state;
}

static struct be_mvp_exit denied(be_u64 scause, be_u64 gpa)
{
	struct be_mvp_exit record = exit_with(scause, DENY_PC);

	record.hstatus = DENY_HSTATUS;
	record.frame.htval = gpa >> 2;
	record.frame.stval = DENY_VA | (gpa & 0xfffU);
	record.frame.vstvec = DENY_VSTVEC;
	record.htinst = 0U;
	record.vsstatus = DENY_VSSTATUS;
	return record;
}

static int denial_is_zero(const struct be_mvp_denial *denial)
{
	static const struct be_mvp_denial zero;

	return memcmp(denial, &zero, sizeof(zero)) == 0;
}

/* The denial action and the counters: exits = sbi + ipi + denials. */
static void test_denials(void)
{
	static const be_u64 causes[3] = {
		BE_MVP_SCAUSE_FETCH_GUEST_PAGE_FAULT, LOAD_FAULT, STORE_FAULT,
	};
	static const be_u64 injected[3] = {
		BE_MVP_SCAUSE_FETCH_ACCESS_FAULT,
		BE_MVP_SCAUSE_LOAD_ACCESS_FAULT,
		BE_MVP_SCAUSE_STORE_ACCESS_FAULT,
	};
	struct be_mvp_state state = accepting_state();
	struct be_mvp_exit record = denied(LOAD_FAULT, BESIDE_GPA);
	struct be_mvp_exit before = record;
	struct be_mvp_result result;
	enum be_mvp_action action;
	unsigned int index;

	/* Accepted: DENY with its denial, the record untouched. */
	SCENARIO();
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_DENY);
	CHECK(result.action == BE_MVP_ACTION_DENY &&
	      result.failure == BE_MVP_CLASS_NONE && result.error == 0 &&
	      result.value == 0U && result.resume_pc == 0U);
	CHECK(result.denial.cause == LOAD_FAULT &&
	      result.denial.kind == BE_MVP_DENIAL_UNMAPPED &&
	      result.denial.gpa == BESIDE_GPA &&
	      result.denial.time == EXIT_TIME &&
	      result.denial.inject_vscause ==
		      BE_MVP_SCAUSE_LOAD_ACCESS_FAULT &&
	      result.denial.inject_vstval == record.frame.stval &&
	      result.denial.inject_vsepc == DENY_PC &&
	      result.denial.inject_vsstatus ==
		      (BE_MVP_VSSTATUS_UXL64 | BE_MVP_VSSTATUS_SPIE) &&
	      result.denial.resume_pc == DENY_VSTVEC);
	CHECK(state.phase == BE_MVP_PHASE_RUNNING &&
	      state.counts.exits == 1U && state.counts.denials == 1U &&
	      state.counts.ipi == 0U && be_mvp_counts_sbi(&state.counts) == 0U);
	CHECK(memcmp(&record, &before, sizeof(record)) == 0);
	/* The executor, not the SBI return, moves the guest. */
	be_mvp_apply_return(&record.frame, &result);
	CHECK(memcmp(&record, &before, sizeof(record)) == 0);

	/* A store to the page: the reader's is read-only, the writer's
	 * terminal, as is a fault inside the window. */
	SCENARIO();
	state = accepting_state();
	record = denied(STORE_FAULT, BE_MVP_CHANNEL_GPA + 0xff8U);
	CHECK(be_mvp_handle_exit(&state, &windows[1], &leaves[1], &record,
				 &result) == BE_MVP_ACTION_DENY);
	CHECK(result.denial.kind == BE_MVP_DENIAL_READ_ONLY &&
	      result.denial.inject_vscause ==
		      BE_MVP_SCAUSE_STORE_ACCESS_FAULT);
	state = accepting_state();
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_GUEST_PAGE_FAULT &&
	      state.phase == BE_MVP_PHASE_FAILED &&
	      state.counts.exits == 1U && state.counts.denials == 0U &&
	      denial_is_zero(&result.denial));
	state = accepting_state();
	record = denied(LOAD_FAULT, WINDOW_GPA + WINDOW_BYTES - 8U);
	CHECK(be_mvp_handle_exit(&state, &windows[1], &leaves[1], &record,
				 &result) == BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_GUEST_PAGE_FAULT);

	/* An image that does not accept denials (two-guests, no-inject):
	 * every guest-page fault is terminal, as in M0. */
	for (index = 0U; index < 3U; ++index) {
		SCENARIO();
		state = fresh_state();
		record = denied(causes[index], BESIDE_GPA);
		CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0],
					 &record, &result) ==
		      BE_MVP_ACTION_TERMINAL);
		CHECK(result.failure == BE_MVP_CLASS_GUEST_PAGE_FAULT &&
		      state.counts.denials == 0U &&
		      denial_is_zero(&result.denial));
		state = accepting_state();
		CHECK(be_mvp_handle_exit(&state, &windows[0], &no_leaf,
					 &record, &result) ==
		      BE_MVP_ACTION_DENY);
		CHECK(result.denial.cause == causes[index] &&
		      result.denial.inject_vscause == injected[index]);
	}

	/* A mixed run: SBI calls, IPIs, and denials. */
	SCENARIO();
	state = accepting_state();
	for (index = 0U; index < 30U; ++index) {
		if (index % 3U == 0U)
			record = ecall(BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, 0U);
		else if (index % 3U == 1U)
			record = exit_with(SSI, ECALL_PC);
		else
			record = denied(STORE_FAULT, PROBE_GPA);
		action = be_mvp_handle_exit(&state, &windows[1], &leaves[1],
					    &record, &result);
		CHECK(action == (index % 3U == 0U ? BE_MVP_ACTION_RETURN :
				 index % 3U == 1U ? BE_MVP_ACTION_IPI :
				 BE_MVP_ACTION_DENY));
		CHECK(state.counts.exits == be_mvp_counts_sbi(&state.counts) +
		      state.counts.ipi + state.counts.denials);
	}
	CHECK(state.counts.exits == 30U && state.counts.base == 10U &&
	      state.counts.ipi == 10U && state.counts.denials == 10U);

	/* The ceiling counts denials as exits. */
	SCENARIO();
	state = accepting_state();
	state.exit_ceiling = 2U;
	record = denied(LOAD_FAULT, BESIDE_GPA);
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_DENY);
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_DENY);
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXIT_BUDGET &&
	      state.counts.exits == 3U && state.counts.denials == 2U);

	/* After the domain stopped, a denial is terminal. */
	SCENARIO();
	state = accepting_state();
	record = ecall(BE_MVP_SBI_EID_SRST, 0U, 0U, 0U, 0U);
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_SHUTDOWN);
	record = denied(LOAD_FAULT, BESIDE_GPA);
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_TERMINAL);
	CHECK(state.counts.denials == 0U && denial_is_zero(&result.denial));
}

static void take_denial(unsigned int domain, be_u64 time)
{
	CHECK(be_mvp_ring_publish(&outbound[domain]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[domain]) ==
	      BE_MVP_RECORD_HEADER_BYTES + BE_MVP_DENIAL_WORDS * 8U);
	take_from(domain, BE_MVP_RECORD_DENIAL, BE_MVP_DENIAL_WORDS * 8U,
		  time);
}

/*
 * The DENIAL record: its twelve words as the hart posts them, its
 * refusals and a full ring, and hart 0's loop taking each record and
 * reconciling SHUTDOWN's denial word with them.
 */
static void test_denial_records(void)
{
	struct be_mvp_controls controls = armed_controls();
	struct be_mvp_control control;
	struct be_mvp_step_result step;
	struct be_mvp_exit record;
	struct be_mvp_result result;
	struct be_mvp_denial denial;
	be_u64 pong[BE_MVP_PONG_WORDS] = { 0U, 0U, 1U };
	be_u64 index;

	/* Twelve words in the plan's order; the header time is the post. */
	SCENARIO();
	open_harts();
	harts[0].accept_denial = 1U;
	record = denied(LOAD_FAULT, BESIDE_GPA + 3U);
	record.htinst = BE_U64_C(0x3303);
	CHECK(be_mvp_handle_exit(&harts[0], &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_DENY);
	CHECK(be_mvp_post_denial(&harts[0], &outbound[0], &result.denial,
				 EXIT_TIME + 9U) == 1);
	take_denial(0U, EXIT_TIME + 9U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_SEQ) == 1U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_CAUSE) == LOAD_FAULT);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_KIND) ==
	      BE_MVP_DENIAL_UNMAPPED);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_GPA) ==
	      BESIDE_GPA + 3U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_HTVAL) ==
	      BESIDE_GPA >> 2);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_HTINST) == 0x3303U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_STVAL) ==
	      (DENY_VA | 3U));
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_SEPC) == DENY_PC);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_VSSTATUS) ==
	      DENY_VSSTATUS);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_VSTVEC) == DENY_VSTVEC);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_INJECTED) ==
	      BE_MVP_SCAUSE_LOAD_ACCESS_FAULT);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_EXIT) == EXIT_TIME);
	/* The domain's next denial is numbered 2. */
	record = denied(STORE_FAULT, PROBE_GPA);
	CHECK(be_mvp_handle_exit(&harts[0], &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_DENY);
	CHECK(be_mvp_post_denial(&harts[0], &outbound[0], &result.denial,
				 EXIT_TIME + 10U) == 1);
	take_denial(0U, EXIT_TIME + 10U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_DENIAL_SEQ) == 2U &&
	      be_mvp_record_word(&taken, BE_MVP_DENIAL_CAUSE) == STORE_FAULT &&
	      be_mvp_record_word(&taken, BE_MVP_DENIAL_INJECTED) ==
		      BE_MVP_SCAUSE_STORE_ACCESS_FAULT);
	denial = result.denial;

	/* Refused, with the ring untouched: no denial counted, a hart that
	 * is not running, and absent input. */
	SCENARIO();
	open_harts();
	harts[1].accept_denial = 1U;
	CHECK(be_mvp_post_denial(&harts[1], &outbound[1], &denial, 1U) == 0);
	harts[1].counts.denials = 1U;
	CHECK(be_mvp_post_denial((const struct be_mvp_state *)0, &outbound[1],
				 &denial, 1U) == 0);
	CHECK(be_mvp_post_denial(&harts[1], &outbound[1],
				 (const struct be_mvp_denial *)0, 1U) == 0);
	CHECK(be_mvp_post_denial(&harts[1], (struct be_mvp_ring *)0, &denial,
				 1U) == 0);
	harts[1].phase = BE_MVP_PHASE_STOPPED;
	CHECK(be_mvp_post_denial(&harts[1], &outbound[1], &denial, 1U) == 0);
	harts[1].phase = BE_MVP_PHASE_FAILED;
	CHECK(be_mvp_post_denial(&harts[1], &outbound[1], &denial, 1U) == 0);
	CHECK(outbound[1].cursor == 0U && outbound[1].failed == 0U);

	/* A full ring refuses the record and fails its view (FAIL ring). */
	SCENARIO();
	open_outbound(1U, BE_MVP_VARIANT_OUTBOUND_RING_BYTES);
	harts[1] = accepting_state();
	harts[1].counts.denials = 1U;
	for (index = 0U; index < BE_MVP_VARIANT_OUTBOUND_RING_BYTES / 112U;
	     ++index)
		CHECK(be_mvp_post_denial(&harts[1], &outbound[1], &denial,
					 index) == 1);
	CHECK(be_mvp_post_denial(&harts[1], &outbound[1], &denial, index) ==
	      0);
	CHECK(outbound[1].failed == 1U && outbound[1].cursor == index * 112U);

	/* Hart 0's loop: the reader's two denials, then its SHUTDOWN. */
	SCENARIO();
	open_harts();
	harts[1].accept_denial = 1U;
	be_mvp_control_init(&control, ENTRY_TIME - 0x100U, BE_MVP_RUN_BUDGET,
			    BE_MVP_READY_TICKS);
	CHECK(be_mvp_control_started(&control, 1U, 2U) == 1);
	CHECK(be_mvp_control_channel(&control, windows, &channel) == 1);
	CHECK(be_mvp_post_ready(&outbound[1], &controls, ENTRY_TIME) == 1);
	be_mvp_entry_frame(&record, BE_MVP_KERNEL_GPA, BE_MVP_GUEST_HART,
			   BE_MVP_DTB_GPA);
	CHECK(be_mvp_post_entered(&outbound[1], &record, ENTRY_TIME + 1U) ==
	      1);
	(void)be_mvp_console_feed(&harts[1], &outbound[1],
				  (const be_u8 *)"reader\n", 7U,
				  ENTRY_TIME + 2U);
	CHECK(be_mvp_ring_post_words(&outbound[1], BE_MVP_RECORD_PONG,
				     ENTRY_TIME + 3U, pong,
				     BE_MVP_PONG_WORDS) == 1);
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	(void)be_mvp_ring_acquire(&drain_view[1]);
	for (index = 0U; index < 4U; ++index) {
		static const enum be_mvp_step steps[4] = {
			BE_MVP_STEP_READY, BE_MVP_STEP_ENTERED,
			BE_MVP_STEP_LINE, BE_MVP_STEP_PONG,
		};

		CHECK(be_mvp_ring_take(&drain_view[1], &taken) ==
		      BE_MVP_RING_RECORD);
		CHECK(be_mvp_control_record(&control, 1U, &taken, &step) ==
		      steps[index]);
	}
	record = denied(STORE_FAULT, BE_MVP_CHANNEL_GPA + 0xff8U);
	CHECK(be_mvp_handle_exit(&harts[1], &windows[1], &leaves[1], &record,
				 &result) == BE_MVP_ACTION_DENY);
	CHECK(be_mvp_post_denial(&harts[1], &outbound[1], &result.denial,
				 EXIT_TIME + 1U) == 1);
	take_denial(1U, EXIT_TIME + 1U);
	CHECK(be_mvp_control_record(&control, 1U, &taken, &step) ==
	      BE_MVP_STEP_DENIAL && control.domain[1].denials == 1U);
	record = denied(LOAD_FAULT, PROBE_GPA);
	record.time = EXIT_TIME + 2U;
	CHECK(be_mvp_handle_exit(&harts[1], &windows[1], &leaves[1], &record,
				 &result) == BE_MVP_ACTION_DENY);
	CHECK(be_mvp_post_denial(&harts[1], &outbound[1], &result.denial,
				 EXIT_TIME + 2U) == 1);
	take_denial(1U, EXIT_TIME + 2U);
	CHECK(be_mvp_control_record(&control, 1U, &taken, &step) ==
	      BE_MVP_STEP_DENIAL && control.domain[1].denials == 2U);
	record = ecall(BE_MVP_SBI_EID_SRST, 0U, 0U, 0U, 0U);
	CHECK(be_mvp_handle_exit(&harts[1], &windows[1], &leaves[1], &record,
				 &result) == BE_MVP_ACTION_SHUTDOWN);
	CHECK(be_mvp_post_shutdown(&harts[1], &outbound[1], ENTRY_TIME + 1U,
				   EXIT_TIME + 3U) == 1);
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	(void)be_mvp_ring_acquire(&drain_view[1]);
	take_from(1U, BE_MVP_RECORD_SHUTDOWN, BE_MVP_SHUTDOWN_WORDS * 8U,
		  EXIT_TIME + 3U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_EXITS) == 3U &&
	      be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_DENIALS) == 2U);
	/* A denial word that is not the records drained fails the run. */
	for (index = 1U; index <= 3U; index += 2U) {
		struct be_mvp_control copy = control;
		struct be_mvp_record changed = taken;

		changed.payload[BE_MVP_SHUTDOWN_DENIALS * 8U] = (be_u8)index;
		CHECK(be_mvp_control_record(&copy, 1U, &changed, &step) ==
		      BE_MVP_STEP_INVALID && step.failure == BE_MVP_CLASS_RING);
	}
	CHECK(be_mvp_control_record(&control, 1U, &taken, &step) ==
	      BE_MVP_STEP_SHUTDOWN && control.domain[1].records == 7U);
}

/*
 * The management extension (planning/mvp-m2-plan.md, Q3 and Q14): Instance
 * 3's one grant, the host (domain 0) on the protected domain (domain 1),
 * and the results be_mvp_mgmt_decide() owes for it, by requester,
 * function, and target, in each of the target's states.
 */
#define MGMT_PAUSE		BE_MVP_SBI_MGMT_PAUSE
#define MGMT_TERMINATE		BE_MVP_SBI_MGMT_TERMINATE
#define DELIVER			BE_MVP_MGMT_DELIVER
#define DENIED			BE_MVP_SBI_ERR_DENIED
#define NO_DOMAIN		BE_MVP_SBI_ERR_INVALID_PARAM
#define BAD_STATE		BE_MVP_SBI_ERR_INVALID_STATE
#define ALL_DENIED		{ DENIED, DENIED, DENIED, DENIED, DENIED }
#define ALL_NO_DOMAIN		{ NO_DOMAIN, NO_DOMAIN, NO_DOMAIN, NO_DOMAIN, \
				  NO_DOMAIN }
#define PAUSE_RESULTS		{ DELIVER, BAD_STATE, BAD_STATE, BAD_STATE, \
				  BAD_STATE }
#define TERMINATE_RESULTS	{ DELIVER, DELIVER, BAD_STATE, BAD_STATE, \
				  BAD_STATE }

static const struct be_mvp_mgmt_grant anchor_grant[1] = {
	{ 0U, 1U, BE_MVP_MGMT_PAUSE | BE_MVP_MGMT_TERMINATE },
};
static const long pause_results[BE_MVP_TARGET_COUNT] = PAUSE_RESULTS;
static const long terminate_results[BE_MVP_TARGET_COUNT] = TERMINATE_RESULTS;

/*
 * One request and its result in each target state: running, paused,
 * terminated, shut down, and pending.
 */
struct decide_row {
	be_u64 requester;
	be_u64 fid;
	be_u64 target;
	long result[BE_MVP_TARGET_COUNT];
};

static const struct decide_row anchor_rows[] = {
	/* The host on itself: no grant names the pair. */
	{ 0U, MGMT_PAUSE, 0U, ALL_DENIED },
	{ 0U, MGMT_TERMINATE, 0U, ALL_DENIED },
	/* The host on the protected domain: its grant, then the state. */
	{ 0U, MGMT_PAUSE, 1U, PAUSE_RESULTS },
	{ 0U, MGMT_TERMINATE, 1U, TERMINATE_RESULTS },
	/* No such domain, before any grant. */
	{ 0U, MGMT_PAUSE, 2U, ALL_NO_DOMAIN },
	{ 0U, MGMT_TERMINATE, 2U, ALL_NO_DOMAIN },
	{ 0U, MGMT_PAUSE, ALL_ONES, ALL_NO_DOMAIN },
	/* The protected domain holds no grant, on itself or the host. */
	{ 1U, MGMT_PAUSE, 0U, ALL_DENIED },
	{ 1U, MGMT_TERMINATE, 0U, ALL_DENIED },
	{ 1U, MGMT_PAUSE, 1U, ALL_DENIED },
	{ 1U, MGMT_TERMINATE, 1U, ALL_DENIED },
	{ 1U, MGMT_PAUSE, 2U, ALL_NO_DOMAIN },
	{ 1U, MGMT_TERMINATE, HIGH_BIT, ALL_NO_DOMAIN },
	/* A requester that is no domain holds none either. */
	{ 2U, MGMT_PAUSE, 1U, ALL_DENIED },
	{ ALL_ONES, MGMT_TERMINATE, 1U, ALL_DENIED },
	{ 2U, MGMT_TERMINATE, 2U, ALL_NO_DOMAIN },
};

static long decide_mgmt(const struct be_mvp_mgmt_grant *grants, be_u64 count,
			be_u64 requester, be_u64 fid, be_u64 target,
			enum be_mvp_target_state state)
{
	return be_mvp_mgmt_decide(grants, count, requester, fid, target, state);
}

static void test_mgmt_decide(void)
{
	static const be_u64 other_fids[] = {
		2U, 3U, 7U, 0xffffffffU, HIGH_BIT, ALL_ONES,
	};
	static const be_u64 targets[] = { 0U, 1U, 2U, ALL_ONES };
	struct be_mvp_mgmt_grant table[BE_MVP_MGMT_GRANTS_MAX + 1U];
	be_size row;
	be_size index;
	be_size named;
	be_u64 requester;
	be_u64 target;
	unsigned int state;

	/* Instance 3's table, every row in every state. */
	SCENARIO();
	for (row = 0U; row < BE_ARRAY_SIZE(anchor_rows); ++row)
		for (state = 0U; state < BE_MVP_TARGET_COUNT; ++state)
			CHECK(decide_mgmt(anchor_grant, 1U,
					  anchor_rows[row].requester,
					  anchor_rows[row].fid,
					  anchor_rows[row].target,
					  (enum be_mvp_target_state)state) ==
			      anchor_rows[row].result[state]);
	/* Another function is not supported, before anything else. */
	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(other_fids); ++index)
		for (named = 0U; named < BE_ARRAY_SIZE(targets) * 3U;
		     ++named)
			for (state = 0U; state < BE_MVP_TARGET_COUNT; ++state)
				CHECK(decide_mgmt(anchor_grant, 1U, named / 4U,
						  other_fids[index],
						  targets[named % 4U],
						  (enum be_mvp_target_state)
							  state) ==
				      BE_MVP_SBI_ERR_NOT_SUPPORTED);
	/* A state that is none of the five delivers nothing. */
	SCENARIO();
	CHECK(decide_mgmt(anchor_grant, 1U, 0U, MGMT_PAUSE, 1U,
			  BE_MVP_TARGET_COUNT) == BAD_STATE);
	CHECK(decide_mgmt(anchor_grant, 1U, 0U, MGMT_TERMINATE, 1U,
			  (enum be_mvp_target_state)99) == BAD_STATE);

	/* No table, an empty one, a count beyond the table's bound, or a
	 * table with no permission grants nothing. */
	SCENARIO();
	for (target = 0U; target < 2U; ++target) {
		for (requester = 0U; requester < 2U; ++requester) {
			CHECK(decide_mgmt((const struct be_mvp_mgmt_grant *)0,
					  0U, requester, MGMT_PAUSE, target,
					  BE_MVP_TARGET_RUNNING) == DENIED);
			CHECK(decide_mgmt((const struct be_mvp_mgmt_grant *)0,
					  1U, requester, MGMT_TERMINATE,
					  target, BE_MVP_TARGET_RUNNING) ==
			      DENIED);
			CHECK(decide_mgmt(anchor_grant, 0U, requester,
					  MGMT_PAUSE, target,
					  BE_MVP_TARGET_RUNNING) == DENIED);
		}
		CHECK(decide_mgmt((const struct be_mvp_mgmt_grant *)0, 0U, 0U,
				  MGMT_PAUSE, target + 2U,
				  BE_MVP_TARGET_RUNNING) == NO_DOMAIN);
	}
	for (index = 0U; index < BE_ARRAY_SIZE(table); ++index)
		table[index] = anchor_grant[0];
	CHECK(decide_mgmt(table, BE_MVP_MGMT_GRANTS_MAX, 0U, MGMT_PAUSE, 1U,
			  BE_MVP_TARGET_RUNNING) == DELIVER);
	CHECK(decide_mgmt(table, BE_MVP_MGMT_GRANTS_MAX + 1U, 0U, MGMT_PAUSE,
			  1U, BE_MVP_TARGET_RUNNING) == DENIED);
	CHECK(decide_mgmt(table, ALL_ONES, 0U, MGMT_TERMINATE, 1U,
			  BE_MVP_TARGET_RUNNING) == DENIED);
	table[0].permissions = 0U;
	table[1].permissions = BE_U64_C(4) | HIGH_BIT;
	CHECK(decide_mgmt(table, 2U, 0U, MGMT_PAUSE, 1U,
			  BE_MVP_TARGET_RUNNING) == DENIED);
	CHECK(decide_mgmt(table, 2U, 0U, MGMT_TERMINATE, 1U,
			  BE_MVP_TARGET_RUNNING) == DENIED);
	/* Each permission grants its own function only. */
	SCENARIO();
	table[0] = anchor_grant[0];
	table[0].permissions = BE_MVP_MGMT_PAUSE;
	CHECK(decide_mgmt(table, 1U, 0U, MGMT_PAUSE, 1U,
			  BE_MVP_TARGET_RUNNING) == DELIVER);
	CHECK(decide_mgmt(table, 1U, 0U, MGMT_TERMINATE, 1U,
			  BE_MVP_TARGET_RUNNING) == DENIED);
	CHECK(decide_mgmt(table, 1U, 0U, MGMT_TERMINATE, 1U,
			  BE_MVP_TARGET_PAUSED) == DENIED);
	table[0].permissions = BE_MVP_MGMT_TERMINATE;
	CHECK(decide_mgmt(table, 1U, 0U, MGMT_PAUSE, 1U,
			  BE_MVP_TARGET_RUNNING) == DENIED);
	CHECK(decide_mgmt(table, 1U, 0U, MGMT_TERMINATE, 1U,
			  BE_MVP_TARGET_PAUSED) == DELIVER);
	/* The grant's direction: the protected domain on the host. */
	table[0].from = 1U;
	table[0].to = 0U;
	table[0].permissions = BE_MVP_MGMT_PAUSE | BE_MVP_MGMT_TERMINATE;
	CHECK(decide_mgmt(table, 1U, 1U, MGMT_TERMINATE, 0U,
			  BE_MVP_TARGET_RUNNING) == DELIVER);
	CHECK(decide_mgmt(table, 1U, 0U, MGMT_TERMINATE, 1U,
			  BE_MVP_TARGET_RUNNING) == DENIED);
	/* A requester has a grant on itself only when a table says so; its
	 * own request makes it pending (hart 0's state), so invalid state. */
	SCENARIO();
	table[0].from = 0U;
	table[0].to = 0U;
	CHECK(decide_mgmt(table, 1U, 0U, MGMT_PAUSE, 0U,
			  BE_MVP_TARGET_RUNNING) == DELIVER);
	CHECK(decide_mgmt(table, 1U, 0U, MGMT_PAUSE, 0U,
			  BE_MVP_TARGET_PENDING) == BAD_STATE);
	CHECK(decide_mgmt(table, 1U, 1U, MGMT_PAUSE, 1U,
			  BE_MVP_TARGET_RUNNING) == DENIED);
	/* Every pair granted: each decision is the state's alone. */
	SCENARIO();
	for (index = 0U; index < BE_MVP_MGMT_GRANTS_MAX; ++index) {
		table[index].from = index / BE_MVP_DOMAINS;
		table[index].to = index % BE_MVP_DOMAINS;
		table[index].permissions = BE_MVP_MGMT_PAUSE |
					   BE_MVP_MGMT_TERMINATE;
	}
	for (requester = 0U; requester < BE_MVP_DOMAINS; ++requester)
		for (target = 0U; target < BE_MVP_DOMAINS; ++target)
			for (state = 0U; state < BE_MVP_TARGET_COUNT;
			     ++state) {
				CHECK(decide_mgmt(table,
						  BE_MVP_MGMT_GRANTS_MAX,
						  requester, MGMT_PAUSE, target,
						  (enum be_mvp_target_state)
							  state) ==
				      pause_results[state]);
				CHECK(decide_mgmt(table,
						  BE_MVP_MGMT_GRANTS_MAX,
						  requester, MGMT_TERMINATE,
						  target,
						  (enum be_mvp_target_state)
							  state) ==
				      terminate_results[state]);
			}
}

/* A hart in an image whose scenario accepts the extension. */
static struct be_mvp_state mgmt_state(void)
{
	struct be_mvp_state state = fresh_state();

	state.accept_mgmt = 1U;
	return state;
}

/*
 * The domain hart's dispatch of the extension: absent, as an unknown
 * extension, from an image whose scenario does not accept it; in one that
 * does, probe 1, version 4, pause and terminate as requests counted in
 * mgmt, any other function refused on the hart; the answer's return; and
 * the counters' sum with management calls among them.
 */
static void test_mgmt_calls(void)
{
	static const be_u64 other_fids[] = {
		2U, 3U, 7U, 0xffffffffU, HIGH_BIT, ALL_ONES,
	};
	static const be_u64 targets[] = { 0U, 1U, 2U, ALL_ONES };
	static const long answers[] = { 0, DENIED, NO_DOMAIN, BAD_STATE };
	struct be_mvp_state state;
	struct be_mvp_exit record;
	struct be_mvp_result result;
	struct be_r4_frame frame;
	be_size index;
	be_size target;
	be_u64 fid;

	/* Without the extension (te-poc, two-guests): every function not
	 * supported and refused, probe 0, version 5 (3 before M7). */
	SCENARIO();
	for (fid = 0U; fid < 2U; ++fid)
		check_unsupported(BE_MVP_SBI_EID_MGMT, fid);
	for (index = 0U; index < BE_ARRAY_SIZE(other_fids); ++index)
		check_unsupported(BE_MVP_SBI_EID_MGMT, other_fids[index]);
	check_return(BE_MVP_SBI_EID_BASE, 3U, BE_MVP_SBI_EID_MGMT, 0U, 0U, 0,
		     0U);
	check_return(BE_MVP_SBI_EID_BASE, 2U, 0U, 0U, 0U, 0, 5U);
	/* With it (anchor): probe 1, version 6 (4 before M7), the rest
	 * unchanged. Only an accept word of exactly 1 accepts it. */
	for (index = 0U; index < 3U; ++index) {
		be_u64 accept = index == 0U ? 1U : index == 1U ? 2U : ALL_ONES;
		be_u64 version = accept == 1U ? 6U : 5U;

		SCENARIO();
		state = fresh_state();
		state.accept_mgmt = accept;
		record = ecall(BE_MVP_SBI_EID_BASE, 2U, 0U, 0U, 0U);
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_RETURN);
		CHECK(result.error == 0 && result.value == version);
		record = ecall(BE_MVP_SBI_EID_BASE, 3U, BE_MVP_SBI_EID_MGMT,
			       0U, 0U);
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_RETURN);
		CHECK(result.error == 0 &&
		      result.value == (accept == 1U ? 1U : 0U));
		record = ecall(BE_MVP_SBI_EID_BASE, 3U,
			       BE_MVP_SBI_EID_MGMT | HIGH_BIT, 0U, 0U);
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_RETURN);
		CHECK(result.value == 0U);
		record = ecall(BE_MVP_SBI_EID_BASE, 3U, BE_MVP_SBI_EID_DBCN, 0U,
			       0U);
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_RETURN);
		CHECK(result.value == 1U);
		record = ecall(BE_MVP_SBI_EID_MGMT, MGMT_PAUSE, 1U, 0U, 0U);
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) ==
		      (accept == 1U ? BE_MVP_ACTION_MGMT :
		       BE_MVP_ACTION_RETURN));
		CHECK(state.counts.base == 4U && state.counts.exits == 5U &&
		      state.counts.mgmt == (accept == 1U ? 1U : 0U) &&
		      state.counts.refused == (accept == 1U ? 0U : 1U));
	}

	/* pause and terminate: one request each, the target a0 as the guest
	 * named it, counted in mgmt; the hart waits before it answers. */
	for (fid = 0U; fid < 2U; ++fid) {
		for (target = 0U; target < BE_ARRAY_SIZE(targets); ++target) {
			SCENARIO();
			state = mgmt_state();
			record = ecall(BE_MVP_SBI_EID_MGMT, fid,
				       targets[target], ALL_ONES, 0x66U);
			CHECK(be_mvp_handle_exit(&state, &window, &no_leaf,
						 &record, &result) ==
			      BE_MVP_ACTION_MGMT);
			CHECK(result.fid == fid &&
			      result.target == targets[target] &&
			      result.error == 0 && result.value == 0U &&
			      result.resume_pc == ECALL_PC + 4U &&
			      result.failure == BE_MVP_CLASS_NONE);
			CHECK(state.counts.mgmt == 1U &&
			      state.counts.exits == 1U &&
			      state.counts.refused == 0U &&
			      call_sum(&state.counts) == 1U &&
			      be_mvp_counts_sbi(&state.counts) == 1U);
			CHECK(state.phase == BE_MVP_PHASE_RUNNING &&
			      state.awaiting == 0U);
		}
	}
	/* Another function: not supported, on the hart, without a request. */
	for (index = 0U; index < BE_ARRAY_SIZE(other_fids); ++index) {
		SCENARIO();
		state = mgmt_state();
		record = ecall(BE_MVP_SBI_EID_MGMT, other_fids[index], 1U, 0U,
			       0U);
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_RETURN);
		CHECK(result.error == BE_MVP_SBI_ERR_NOT_SUPPORTED &&
		      result.value == 0U && result.resume_pc == ECALL_PC + 4U);
		CHECK(state.counts.refused == 1U && state.counts.mgmt == 0U &&
		      state.counts.exits == 1U);
	}

	/* The answer returns in a0 as a two's-complement word, a1 0, and the
	 * guest resumes after the ecall. */
	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(answers); ++index) {
		state = mgmt_state();
		record = ecall(BE_MVP_SBI_EID_MGMT, MGMT_TERMINATE, 1U, 0U, 0U);
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_MGMT);
		result.error = answers[index];
		frame = record.frame;
		be_mvp_apply_return(&frame, &result);
		CHECK(frame.gpr[BE_R4_GPR_A0] == (be_u64)answers[index] &&
		      frame.gpr[BE_R4_GPR_A1] == 0U &&
		      frame.sepc == ECALL_PC + 4U);
		CHECK(frame.gpr[BE_R4_GPR_A7] == BE_MVP_SBI_EID_MGMT &&
		      frame.gpr[BE_R4_GPR_A6] == MGMT_TERMINATE);
	}
	CHECK(frame.gpr[BE_R4_GPR_A0] == BE_U64_C(0xfffffffffffffff6));

	/* exits = sbi + ipi + denials, with mgmt among the SBI calls. */
	SCENARIO();
	state = mgmt_state();
	state.accept_denial = 1U;
	record = ecall(BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_RETURN);
	for (fid = 0U; fid < 2U; ++fid) {
		record = ecall(BE_MVP_SBI_EID_MGMT, fid, 1U, 0U, 0U);
		CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0],
					 &record, &result) ==
		      BE_MVP_ACTION_MGMT);
	}
	record = ecall(BE_MVP_SBI_EID_MGMT, 7U, 1U, 0U, 0U);
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_RETURN);
	record = exit_with(SSI, ECALL_PC);
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_IPI);
	record = denied(LOAD_FAULT, BESIDE_GPA);
	CHECK(be_mvp_handle_exit(&state, &windows[0], &leaves[0], &record,
				 &result) == BE_MVP_ACTION_DENY);
	CHECK(state.counts.exits == 6U && state.counts.mgmt == 2U &&
	      state.counts.refused == 1U && state.counts.base == 1U &&
	      state.counts.ipi == 1U && state.counts.denials == 1U);
	CHECK(be_mvp_counts_sbi(&state.counts) == 4U &&
	      call_sum(&state.counts) == 4U);
	CHECK(be_mvp_counts_sbi(&state.counts) + state.counts.ipi +
	      state.counts.denials == state.counts.exits);
	CHECK(be_mvp_counts_sbi((const struct be_mvp_counts *)0) == 0U);
}

/* Hart 0's record in the inbound ring, published; the hart acquires. */
static void to_hart(enum be_mvp_record_type type, be_u64 time,
		    const be_u64 *words, be_u64 count)
{
	CHECK(be_mvp_ring_post_words(&inbound_writer, type, time, words,
				     count) == 1);
	CHECK(be_mvp_ring_publish(&inbound_writer) == 1);
	(void)be_mvp_ring_acquire(&inbound);
}

static void result_to_hart(long code, be_u64 seq, be_u64 time)
{
	be_u64 words[BE_MVP_MGMT_RESULT_WORDS];

	words[BE_MVP_MGMT_RESULT_CODE] = (be_u64)code;
	words[BE_MVP_MGMT_RESULT_SEQ] = seq;
	to_hart(BE_MVP_RECORD_MGMT_RESULT, time, words,
		BE_MVP_MGMT_RESULT_WORDS);
}

static void order_to_hart(enum be_mvp_record_type type, be_u64 by,
			  be_u64 time)
{
	to_hart(type, time, &by, 1U);
}

/* Domain @domain's call @fid on @target, its request posted at @now. */
static void call_mgmt(unsigned int domain, be_u64 fid, be_u64 target,
		      be_u64 now)
{
	struct be_mvp_exit record = ecall(BE_MVP_SBI_EID_MGMT, fid, target, 0U,
					  0U);
	struct be_mvp_result result;

	CHECK(be_mvp_handle_exit(&harts[domain], &windows[domain], &no_leaf,
				 &record, &result) == BE_MVP_ACTION_MGMT);
	CHECK(be_mvp_post_mgmt_request(&harts[domain], &outbound[domain],
				       &result, now) == 1);
	CHECK(harts[domain].awaiting == harts[domain].counts.mgmt &&
	      harts[domain].answer == 0U);
}

/* Domain 1's wait, served once at @now: the answers it posted. */
static be_u64 wait_once(be_u64 now)
{
	be_u64 posted = ALL_ONES;

	CHECK(be_mvp_wait_serve(&harts[1], &inbound, &outbound[1], now,
				&posted) == 1);
	return posted;
}

static void expect_wait_failed(be_u64 now, enum be_mvp_class failure)
{
	be_u64 posted = ALL_ONES;

	CHECK(be_mvp_wait_serve(&harts[1], &inbound, &outbound[1], now,
				&posted) == 0);
	CHECK(posted == 0U);
	expect_ipi_failed(failure);
}

/* @count 32-byte LINE records into domain 1's outbound ring. */
static void fill(be_u64 count)
{
	be_u64 index;

	for (index = 0U; index < count; ++index)
		CHECK(be_mvp_ring_post(&outbound[1], BE_MVP_RECORD_LINE, 1U,
				       (const be_u8 *)"0123456789abcdef",
				       16U) == 1);
}

/* Domain 1 waiting for the answer to its request 1, pause of domain 0. */
static void waiting(void)
{
	open_harts();
	harts[1] = mgmt_state();
	open_inbound(1U);
	call_mgmt(1U, MGMT_PAUSE, 0U, EXIT_TIME + 1U);
}

/* Domain 1 running, its IPI's exit taken, the order at hand. */
static be_u64 ipi_with(enum be_mvp_record_type type, be_u64 by)
{
	open_harts();
	harts[1] = mgmt_state();
	open_inbound(1U);
	order_to_hart(type, by, 0x1000U);
	return serve(0x2000U);
}

/* The next record in domain 1's outbound ring: @type with its words. */
static void take_answer(enum be_mvp_record_type type, be_u64 words,
			be_u64 time)
{
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	(void)be_mvp_ring_acquire(&drain_view[1]);
	take_from(1U, type, words * 8U, time);
}

/*
 * The extension's records (planning/mvp-m2-plan.md, Q14 and Q15):
 * MGMT_REQUEST as the requester posts it, and its refusals; the
 * requester's wait in HS for MGMT_RESULT, serving PINGs, and every record
 * it refuses; the target's PAUSE and TERMINATE through the IPI, PAUSED and
 * TERMINATED, the paused and terminated waits, and every record they
 * refuse; SHUTDOWN's management word; and hart 0's loop taking each.
 */
static void test_mgmt_records(void)
{
	static const long refused[] = {
		BE_MVP_SBI_ERR_NOT_SUPPORTED, -1, 1, -5, -9, -11,
		(long)(ALL_ONES >> 1),
	};
	static const long accepted[] = { 0, NO_DOMAIN, DENIED, BAD_STATE };
	static const be_u64 bad_words[4][3] = {
		{ 0U, 0U, 0U }, { 0U, 2U, 0U }, { 0U, 1U, 0U }, { 0U, 1U, 0U },
	};
	static const be_u64 bad_counts[4] = { 2U, 2U, 1U, 3U };
	struct be_mvp_controls controls = armed_controls();
	struct be_mvp_control control;
	struct be_mvp_mgmt_state mgmt;
	struct be_mvp_step_result step;
	struct be_mvp_exit record;
	struct be_mvp_result result;
	be_u64 pong[BE_MVP_PONG_WORDS] = { 0U, 0U, 1U };
	be_u64 index;
	be_u32 domain;

	/* MGMT_REQUEST: the function, the target as named, the sequence
	 * number from 1; the header time is the request's. */
	SCENARIO();
	waiting();
	take_answer(BE_MVP_RECORD_MGMT_REQUEST, BE_MVP_MGMT_REQUEST_WORDS,
		    EXIT_TIME + 1U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_MGMT_REQUEST_FID) ==
	      MGMT_PAUSE &&
	      be_mvp_record_word(&taken, BE_MVP_MGMT_REQUEST_TARGET) == 0U &&
	      be_mvp_record_word(&taken, BE_MVP_MGMT_REQUEST_SEQ) == 1U);
	/* Its answer ends the wait with the result. */
	result_to_hart(DENIED, 1U, EXIT_TIME + 2U);
	CHECK(wait_once(EXIT_TIME + 3U) == 0U);
	CHECK(harts[1].awaiting == 0U && harts[1].answer == (be_u64)DENIED &&
	      harts[1].phase == BE_MVP_PHASE_RUNNING);
	CHECK(be_mvp_ring_release(&inbound) == 1);
	/* The next request is 2, whatever target the guest names. */
	call_mgmt(1U, MGMT_TERMINATE, ALL_ONES, EXIT_TIME + 4U);
	take_answer(BE_MVP_RECORD_MGMT_REQUEST, BE_MVP_MGMT_REQUEST_WORDS,
		    EXIT_TIME + 4U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_MGMT_REQUEST_FID) ==
	      MGMT_TERMINATE &&
	      be_mvp_record_word(&taken, BE_MVP_MGMT_REQUEST_TARGET) ==
	      ALL_ONES &&
	      be_mvp_record_word(&taken, BE_MVP_MGMT_REQUEST_SEQ) == 2U);

	/* Refused, the ring untouched: a request already awaited, an image
	 * without the extension, no call counted, another action or
	 * function, a hart not running, absent input, and a full ring. */
	SCENARIO();
	waiting();
	result = (struct be_mvp_result){ 0 };
	result.action = BE_MVP_ACTION_MGMT;
	result.fid = MGMT_PAUSE;
	result.target = 0U;
	index = outbound[1].cursor;
	CHECK(be_mvp_post_mgmt_request(&harts[1], &outbound[1], &result,
				       1U) == 0);
	harts[1] = mgmt_state();
	harts[1].counts.mgmt = 1U;
	harts[1].accept_mgmt = 0U;
	CHECK(be_mvp_post_mgmt_request(&harts[1], &outbound[1], &result,
				       1U) == 0);
	harts[1].accept_mgmt = 1U;
	harts[1].counts.mgmt = 0U;
	CHECK(be_mvp_post_mgmt_request(&harts[1], &outbound[1], &result,
				       1U) == 0);
	harts[1].counts.mgmt = 1U;
	result.action = BE_MVP_ACTION_RETURN;
	CHECK(be_mvp_post_mgmt_request(&harts[1], &outbound[1], &result,
				       1U) == 0);
	result.action = BE_MVP_ACTION_MGMT;
	result.fid = 7U;
	CHECK(be_mvp_post_mgmt_request(&harts[1], &outbound[1], &result,
				       1U) == 0);
	result.fid = MGMT_TERMINATE;
	harts[1].phase = BE_MVP_PHASE_STOPPED;
	CHECK(be_mvp_post_mgmt_request(&harts[1], &outbound[1], &result,
				       1U) == 0);
	harts[1].phase = BE_MVP_PHASE_RUNNING;
	CHECK(be_mvp_post_mgmt_request((struct be_mvp_state *)0, &outbound[1],
				       &result, 1U) == 0);
	CHECK(be_mvp_post_mgmt_request(&harts[1], &outbound[1],
				       (const struct be_mvp_result *)0,
				       1U) == 0);
	CHECK(be_mvp_post_mgmt_request(&harts[1], (struct be_mvp_ring *)0,
				       &result, 1U) == 0);
	CHECK(outbound[1].cursor == index && harts[1].awaiting == 0U);
	open_outbound(1U, BE_MVP_RING_MIN_BYTES);
	for (index = 0U; index < BE_MVP_RING_MIN_BYTES / 40U; ++index)
		CHECK(be_mvp_ring_post_words(&outbound[1],
					     BE_MVP_RECORD_MGMT_REQUEST, index,
					     pong, 3U) == 1);
	CHECK(be_mvp_post_mgmt_request(&harts[1], &outbound[1], &result,
				       1U) == 0);
	CHECK(outbound[1].failed == 1U && harts[1].awaiting == 0U);
	CHECK(be_mvp_post_mgmt_request(&harts[1], &outbound[1], &result,
				       1U) == 0);

	/* The wait: a PING is answered with a PONG whose receipt is the
	 * wait's and whose SPV is 0 (the IPI found the hart in HS). */
	SCENARIO();
	waiting();
	ping(1U, EXIT_TIME + 2U);
	CHECK(wait_once(EXIT_TIME + 5U) == 1U);
	CHECK(harts[1].awaiting == 1U && harts[1].counts.ipi == 0U);
	CHECK(be_mvp_ring_release(&inbound) == 1);
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[1]) == 40U + 40U);
	take_from(1U, BE_MVP_RECORD_MGMT_REQUEST, 24U, EXIT_TIME + 1U);
	take_from(1U, BE_MVP_RECORD_PONG, 24U, EXIT_TIME + 5U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_PONG_SENT) == EXIT_TIME + 2U &&
	      be_mvp_record_word(&taken, BE_MVP_PONG_RECEIVED) ==
	      EXIT_TIME + 5U &&
	      be_mvp_record_word(&taken, BE_MVP_PONG_SPV) == 0U);
	/* An empty ring is a wake with nothing yet: the wait goes on. */
	CHECK(wait_once(EXIT_TIME + 6U) == 0U && harts[1].awaiting == 1U);
	/* A PING and the answer at one wake: both taken. */
	ping(1U, EXIT_TIME + 7U);
	result_to_hart(0, 1U, EXIT_TIME + 8U);
	CHECK(wait_once(EXIT_TIME + 9U) == 1U);
	CHECK(harts[1].awaiting == 0U && harts[1].answer == 0U);
	/* Every result hart 0 answers is taken; any other fails ipi. */
	for (index = 0U; index < BE_ARRAY_SIZE(accepted); ++index) {
		SCENARIO();
		waiting();
		result_to_hart(accepted[index], 1U, EXIT_TIME + 2U);
		CHECK(wait_once(EXIT_TIME + 3U) == 0U);
		CHECK(harts[1].answer == (be_u64)accepted[index]);
	}
	for (index = 0U; index < BE_ARRAY_SIZE(refused); ++index) {
		SCENARIO();
		waiting();
		result_to_hart(refused[index], 1U, EXIT_TIME + 2U);
		expect_wait_failed(EXIT_TIME + 3U, BE_MVP_CLASS_IPI);
	}
	/* Another request's answer (sequence 0 or 2), one of another size,
	 * or an order while it waits: ipi. */
	for (index = 0U; index < BE_ARRAY_SIZE(bad_counts); ++index) {
		SCENARIO();
		waiting();
		to_hart(BE_MVP_RECORD_MGMT_RESULT, EXIT_TIME + 2U,
			bad_words[index], bad_counts[index]);
		expect_wait_failed(EXIT_TIME + 3U, BE_MVP_CLASS_IPI);
	}
	for (index = 0U; index < 2U; ++index) {
		SCENARIO();
		waiting();
		order_to_hart(index == 0U ? BE_MVP_RECORD_PAUSE :
			      BE_MVP_RECORD_TERMINATE, 0U, EXIT_TIME + 2U);
		expect_wait_failed(EXIT_TIME + 3U, BE_MVP_CLASS_IPI);
	}
	/* A malformed inbound ring, or a full outbound one: ring. */
	SCENARIO();
	waiting();
	ping(1U, EXIT_TIME + 2U);
	inbound_bytes[1] = 0U;
	expect_wait_failed(EXIT_TIME + 3U, BE_MVP_CLASS_RING);
	SCENARIO();
	harts[1] = mgmt_state();
	open_inbound(1U);
	open_outbound(1U, BE_MVP_RING_MIN_BYTES);
	call_mgmt(1U, MGMT_PAUSE, 0U, 1U);
	fill(14U);
	ping(1U, EXIT_TIME + 2U);
	expect_wait_failed(EXIT_TIME + 3U, BE_MVP_CLASS_RING);
	CHECK(outbound[1].cursor == 40U + 14U * 32U);
	/* A hart in no state to wait, and absent input. */
	SCENARIO();
	open_harts();
	open_inbound(1U);
	harts[1] = mgmt_state();
	expect_wait_failed(1U, BE_MVP_CLASS_IPI);
	harts[1] = mgmt_state();
	harts[1].phase = BE_MVP_PHASE_STOPPED;
	expect_wait_failed(1U, BE_MVP_CLASS_IPI);
	waiting();
	CHECK(be_mvp_wait_serve(&harts[1], &inbound, &outbound[1], 1U,
				(be_u64 *)0) == 0);
	CHECK(harts[1].phase == BE_MVP_PHASE_RUNNING);
	CHECK(be_mvp_wait_serve((struct be_mvp_state *)0, &inbound,
				&outbound[1], 1U, &index) == 0);
	CHECK(be_mvp_wait_serve(&harts[1], (struct be_mvp_ring *)0,
				&outbound[1], 1U, &index) == 0);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	waiting();
	CHECK(be_mvp_wait_serve(&harts[1], &inbound, (struct be_mvp_ring *)0,
				1U, &index) == 0);
	expect_ipi_failed(BE_MVP_CLASS_IPI);
	/* An answer on the guest's IPI exit, with no request awaited: ipi. */
	SCENARIO();
	open_harts();
	harts[1] = mgmt_state();
	open_inbound(1U);
	result_to_hart(0, 1U, 0x1000U);
	CHECK(serve(0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_IPI);

	/* PAUSE through the IPI: PAUSED with the exits (the IPI's
	 * included) and the requester, at the answer's time; the hart is
	 * paused, and every later exit is terminal. */
	SCENARIO();
	CHECK(ipi_with(BE_MVP_RECORD_PAUSE, 0U) == 1U);
	CHECK(harts[1].phase == BE_MVP_PHASE_PAUSED && harts[1].by == 0U &&
	      harts[1].counts.ipi == 1U);
	take_answer(BE_MVP_RECORD_PAUSED, BE_MVP_PAUSED_WORDS, 0x2000U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_PAUSED_EXITS) == 1U &&
	      be_mvp_record_word(&taken, BE_MVP_PAUSED_BY) == 0U);
	CHECK(be_mvp_ring_release(&inbound) == 1);
	{
		struct be_mvp_state copy = harts[1];

		record = ecall(BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, 0U);
		CHECK(be_mvp_handle_exit(&copy, &windows[1], &no_leaf, &record,
					 &result) == BE_MVP_ACTION_TERMINAL);
		CHECK(copy.failure == BE_MVP_CLASS_EXCEPTION);
		/* Its parked wait, not the IPI exit, takes what follows. */
		copy = harts[1];
		record = exit_with(SSI, ECALL_PC);
		CHECK(be_mvp_ipi_serve(&copy, &inbound, &outbound[1], &record,
				       1U) == 0U);
		CHECK(copy.phase == BE_MVP_PHASE_FAILED &&
		      copy.failure == BE_MVP_CLASS_IPI);
	}
	/* Paused: a wake with nothing waits on; TERMINATE is taken. */
	CHECK(wait_once(0x3000U) == 0U);
	order_to_hart(BE_MVP_RECORD_TERMINATE, 0U, 0x4000U);
	CHECK(wait_once(0x5000U) == 1U);
	CHECK(harts[1].phase == BE_MVP_PHASE_TERMINATED);
	take_answer(BE_MVP_RECORD_TERMINATED, BE_MVP_TERMINATED_WORDS,
		    0x5000U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_TERMINATED_EXITS) == 1U &&
	      be_mvp_record_word(&taken, BE_MVP_TERMINATED_BY) == 0U);
	CHECK(be_mvp_ring_release(&inbound) == 1);
	/* Terminated: a wake with nothing waits on; any record is ipi. */
	CHECK(wait_once(0x6000U) == 0U);
	ping(1U, 0x7000U);
	expect_wait_failed(0x8000U, BE_MVP_CLASS_IPI);
	/* TERMINATE while running: TERMINATED at once. */
	SCENARIO();
	CHECK(ipi_with(BE_MVP_RECORD_TERMINATE, 0U) == 1U);
	CHECK(harts[1].phase == BE_MVP_PHASE_TERMINATED);
	take_answer(BE_MVP_RECORD_TERMINATED, BE_MVP_TERMINATED_WORDS,
		    0x2000U);
	/* Paused, anything but TERMINATE is ipi. */
	for (index = 0U; index < 3U; ++index) {
		SCENARIO();
		CHECK(ipi_with(BE_MVP_RECORD_PAUSE, 0U) == 1U);
		CHECK(be_mvp_ring_release(&inbound) == 1);
		if (index == 0U)
			ping(1U, 0x3000U);
		else if (index == 1U)
			order_to_hart(BE_MVP_RECORD_PAUSE, 0U, 0x3000U);
		else
			result_to_hart(0, 1U, 0x3000U);
		expect_wait_failed(0x4000U, BE_MVP_CLASS_IPI);
	}
	/* One IPI, several records: a PING before the order is answered,
	 * and a TERMINATE after a PAUSE; nothing after the order but a
	 * TERMINATE after a PAUSE. */
	SCENARIO();
	open_harts();
	harts[1] = mgmt_state();
	open_inbound(1U);
	CHECK(be_mvp_ring_post(&inbound_writer, BE_MVP_RECORD_PING, 0x1000U,
			       (const be_u8 *)0, 0U) == 1);
	order_to_hart(BE_MVP_RECORD_PAUSE, 0U, 0x1001U);
	order_to_hart(BE_MVP_RECORD_TERMINATE, 0U, 0x1002U);
	CHECK(serve(0x2000U) == 3U);
	CHECK(harts[1].phase == BE_MVP_PHASE_TERMINATED);
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[1]) == 40U + 32U + 32U);
	take_from(1U, BE_MVP_RECORD_PONG, 24U, 0x2000U);
	take_from(1U, BE_MVP_RECORD_PAUSED, 16U, 0x2000U);
	take_from(1U, BE_MVP_RECORD_TERMINATED, 16U, 0x2000U);
	for (index = 0U; index < 3U; ++index) {
		SCENARIO();
		open_harts();
		harts[1] = mgmt_state();
		open_inbound(1U);
		order_to_hart(index == 2U ? BE_MVP_RECORD_TERMINATE :
			      BE_MVP_RECORD_PAUSE, 0U, 0x1000U);
		if (index == 0U)
			CHECK(be_mvp_ring_post(&inbound_writer,
					       BE_MVP_RECORD_PING, 0x1001U,
					       (const be_u8 *)0, 0U) == 1);
		else
			order_to_hart(index == 1U ? BE_MVP_RECORD_PAUSE :
				      BE_MVP_RECORD_TERMINATE, 0U, 0x1001U);
		CHECK(be_mvp_ring_publish(&inbound_writer) == 1);
		(void)be_mvp_ring_acquire(&inbound);
		CHECK(serve(0x2000U) == 0U);
		expect_ipi_failed(BE_MVP_CLASS_IPI);
	}
	/* An order naming no domain, of another size, in an image without
	 * the extension, or to a full outbound ring. */
	for (index = 0U; index < 4U; ++index) {
		be_u64 words[2] = { 0U, 0U };

		SCENARIO();
		open_harts();
		harts[1] = mgmt_state();
		open_inbound(1U);
		if (index == 0U)
			order_to_hart(BE_MVP_RECORD_PAUSE, 2U, 0x1000U);
		else if (index < 3U)
			to_hart(BE_MVP_RECORD_TERMINATE, 0x1000U, words,
				(index - 1U) * 2U);
		else {
			harts[1].accept_mgmt = 0U;
			order_to_hart(BE_MVP_RECORD_PAUSE, 0U, 0x1000U);
		}
		CHECK(serve(0x2000U) == 0U);
		expect_ipi_failed(BE_MVP_CLASS_IPI);
		CHECK(harts[1].phase == BE_MVP_PHASE_FAILED);
	}
	SCENARIO();
	open_harts();
	harts[1] = mgmt_state();
	open_inbound(1U);
	open_outbound(1U, BE_MVP_RING_MIN_BYTES);
	fill(16U);
	order_to_hart(BE_MVP_RECORD_PAUSE, 0U, 0x1000U);
	CHECK(serve(0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_RING);
	CHECK(outbound[1].cursor == BE_MVP_RING_MIN_BYTES);

	/*
	 * A domain's unterminated line, with its prefix, before it parks
	 * (planning/mvp-m7-plan.md, Q9): one LINE before PAUSED, and
	 * before TERMINATED from running; none when paused, the pause
	 * having flushed it; a ring with no room for the line: ring.
	 */
	SCENARIO();
	open_harts();
	harts[1] = mgmt_state();
	open_inbound(1U);
	CHECK(be_mvp_console_feed(&harts[1], &outbound[1],
				  (const be_u8 *)"part\r", 5U, 0x800U) == 0U);
	order_to_hart(BE_MVP_RECORD_PAUSE, 0U, 0x1000U);
	CHECK(serve(0x2000U) == 1U);
	CHECK(harts[1].phase == BE_MVP_PHASE_PAUSED &&
	      harts[1].console.length == 0U && harts[1].counts.lines == 1U);
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[1]) == 24U + 32U);
	take_from(1U, BE_MVP_RECORD_LINE, 4U, 0x2000U);
	CHECK(memcmp(taken.payload, "part", 4U) == 0);
	take_from(1U, BE_MVP_RECORD_PAUSED, 16U, 0x2000U);
	CHECK(be_mvp_ring_release(&drain_view[1]) == 1);
	CHECK(be_mvp_ring_release(&inbound) == 1);
	order_to_hart(BE_MVP_RECORD_TERMINATE, 0U, 0x3000U);
	CHECK(wait_once(0x4000U) == 1U);
	CHECK(harts[1].phase == BE_MVP_PHASE_TERMINATED &&
	      harts[1].counts.lines == 1U);
	take_answer(BE_MVP_RECORD_TERMINATED, BE_MVP_TERMINATED_WORDS,
		    0x4000U);
	SCENARIO();
	open_harts();
	harts[1] = mgmt_state();
	open_inbound(1U);
	CHECK(be_mvp_console_feed(&harts[1], &outbound[1],
				  (const be_u8 *)"done\nrest", 9U, 0x800U) ==
	      1U);
	order_to_hart(BE_MVP_RECORD_TERMINATE, 1U, 0x1000U);
	CHECK(serve(0x2000U) == 1U);
	CHECK(harts[1].phase == BE_MVP_PHASE_TERMINATED &&
	      harts[1].counts.lines == 2U);
	CHECK(be_mvp_ring_publish(&outbound[1]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[1]) == 24U + 24U + 32U);
	take_from(1U, BE_MVP_RECORD_LINE, 4U, 0x800U);
	CHECK(memcmp(taken.payload, "done", 4U) == 0);
	take_from(1U, BE_MVP_RECORD_LINE, 4U, 0x2000U);
	CHECK(memcmp(taken.payload, "rest", 4U) == 0);
	take_from(1U, BE_MVP_RECORD_TERMINATED, 16U, 0x2000U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_TERMINATED_BY) == 1U);
	SCENARIO();
	open_harts();
	harts[1] = mgmt_state();
	open_inbound(1U);
	open_outbound(1U, BE_MVP_RING_MIN_BYTES);
	fill(16U);
	CHECK(be_mvp_console_feed(&harts[1], &outbound[1],
				  (const be_u8 *)"x", 1U, 0x800U) == 0U);
	order_to_hart(BE_MVP_RECORD_PAUSE, 0U, 0x1000U);
	CHECK(serve(0x2000U) == 0U);
	expect_ipi_failed(BE_MVP_CLASS_RING);
	CHECK(harts[1].counts.lines == 0U &&
	      outbound[1].cursor == BE_MVP_RING_MIN_BYTES);

	/* SHUTDOWN's word 13 is the requests made, and since M7 its word 14
	 * the console reads served (planning/mvp-m7-plan.md, D-1). */
	SCENARIO();
	open_harts();
	harts[0] = mgmt_state();
	harts[0].counts.mgmt = 13U;
	harts[0].counts.dbcn_input = 14U;
	harts[0].phase = BE_MVP_PHASE_STOPPED;
	CHECK(be_mvp_post_shutdown(&harts[0], &outbound[0], 1U, 2U) == 1);
	CHECK(be_mvp_ring_publish(&outbound[0]) == 1);
	CHECK(be_mvp_ring_acquire(&drain_view[0]) ==
	      16U + BE_MVP_SHUTDOWN_WORDS * 8U);
	take_from(0U, BE_MVP_RECORD_SHUTDOWN, BE_MVP_SHUTDOWN_WORDS * 8U, 2U);
	CHECK(be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_MGMT) == 13U &&
	      be_mvp_record_word(&taken, BE_MVP_SHUTDOWN_DBCN_INPUT) == 14U);

	/* Hart 0's loop on the records the harts post: the host's pause of
	 * the protected domain delivered, the protected domain's PAUSED,
	 * and the host's MGMT_RESULT, which its wait takes. */
	SCENARIO();
	open_harts();
	harts[0] = mgmt_state();
	harts[1] = mgmt_state();
	be_mvp_control_init(&control, ENTRY_TIME - 0x100U, BE_MVP_RUN_BUDGET,
			    BE_MVP_READY_TICKS);
	CHECK(be_mvp_control_mgmt(&control, &mgmt, anchor_grant, 1U, 1) == 1);
	for (domain = 0U; domain < 2U; ++domain) {
		CHECK(be_mvp_control_started(&control, domain, domain + 1U) ==
		      1);
		CHECK(be_mvp_post_ready(&outbound[domain], &controls,
					ENTRY_TIME) == 1);
		be_mvp_entry_frame(&record, BE_MVP_KERNEL_GPA,
				   BE_MVP_GUEST_HART, BE_MVP_DTB_GPA);
		CHECK(be_mvp_post_entered(&outbound[domain], &record,
					  ENTRY_TIME + 1U) == 1);
		(void)be_mvp_console_feed(&harts[domain], &outbound[domain],
					  (const be_u8 *)"up\n", 3U,
					  ENTRY_TIME + 2U);
		CHECK(be_mvp_ring_post_words(&outbound[domain],
					     BE_MVP_RECORD_PONG,
					     ENTRY_TIME + 3U, pong,
					     BE_MVP_PONG_WORDS) == 1);
		CHECK(be_mvp_ring_publish(&outbound[domain]) == 1);
		(void)be_mvp_ring_acquire(&drain_view[domain]);
		while (be_mvp_ring_take(&drain_view[domain], &taken) ==
		       BE_MVP_RING_RECORD)
			CHECK(be_mvp_control_record(&control, domain, &taken,
						    &step) !=
			      BE_MVP_STEP_INVALID);
	}
	/* The protected domain's terminate of the host: denied at once. */
	open_inbound(1U);
	call_mgmt(1U, MGMT_TERMINATE, 0U, EXIT_TIME);
	take_answer(BE_MVP_RECORD_MGMT_REQUEST, 3U, EXIT_TIME);
	CHECK(be_mvp_control_record(&control, 1U, &taken, &step) ==
	      BE_MVP_STEP_MGMT);
	CHECK(step.answer == 1U && step.requester == 1U && step.seq == 1U &&
	      step.result == DENIED);
	result_to_hart(step.result, step.seq, EXIT_TIME + 1U);
	CHECK(wait_once(EXIT_TIME + 2U) == 0U &&
	      harts[1].answer == (be_u64)DENIED);
	CHECK(be_mvp_ring_release(&inbound) == 1);
	/* The host's pause of it: delivered, PAUSED, answered 0. */
	call_mgmt(0U, MGMT_PAUSE, 1U, EXIT_TIME + 3U);
	CHECK(be_mvp_ring_publish(&outbound[0]) == 1);
	(void)be_mvp_ring_acquire(&drain_view[0]);
	take_from(0U, BE_MVP_RECORD_MGMT_REQUEST, 24U, EXIT_TIME + 3U);
	CHECK(be_mvp_control_record(&control, 0U, &taken, &step) ==
	      BE_MVP_STEP_DELIVER);
	CHECK(step.target == 1U && step.fid == MGMT_PAUSE &&
	      step.requester == 0U);
	order_to_hart(BE_MVP_RECORD_PAUSE, step.requester, EXIT_TIME + 4U);
	CHECK(serve(EXIT_TIME + 5U) == 1U);
	take_answer(BE_MVP_RECORD_PAUSED, 2U, EXIT_TIME + 5U);
	CHECK(be_mvp_control_record(&control, 1U, &taken, &step) ==
	      BE_MVP_STEP_PAUSED);
	CHECK(step.answer == 1U && step.requester == 0U && step.seq == 1U &&
	      step.result == 0 && step.shown == BE_MVP_TARGET_PAUSED &&
	      control.domain[1].phase == BE_MVP_DOMAIN_PAUSED);
	CHECK(be_mvp_record_word(&taken, BE_MVP_PAUSED_EXITS) ==
	      harts[1].counts.exits);
	open_inbound(0U);
	result_to_hart(step.result, step.seq, EXIT_TIME + 6U);
	CHECK(be_mvp_wait_serve(&harts[0], &inbound, &outbound[0],
				EXIT_TIME + 7U, &index) == 1);
	CHECK(index == 0U && harts[0].awaiting == 0U && harts[0].answer == 0U);
}

static void test_hsm(void)
{
	be_u64 mask = 0U;
	be_u64 base = 0U;
	be_u64 state;

	SCENARIO();
	for (state = 0U; state <= 7U; ++state) {
		CHECK(be_mvp_hsm_stopped(0, state) == (state == 1U ? 1 : 0));
		CHECK(be_mvp_hsm_started(0, state) == (state == 0U ? 1 : 0));
		CHECK(be_mvp_hsm_stopped(-3, state) == 0);
		CHECK(be_mvp_hsm_started(-2, state) == 0);
	}
	/* QEMU answers hart_get_status of a missing hart with -3. */
	CHECK(be_mvp_hsm_stopped(BE_MVP_SBI_ERR_INVALID_PARAM,
				 BE_MVP_HSM_STOPPED) == 0);
	CHECK(be_mvp_hsm_stopped(0, ALL_ONES) == 0);
	CHECK(be_mvp_ipi_target(2U, &mask, &base) == 1);
	CHECK(mask == 1U && base == 2U);
	CHECK(be_mvp_ipi_target(0U, &mask, &base) == 1);
	CHECK(mask == 1U && base == 0U);
	mask = 7U;
	base = 7U;
	CHECK(be_mvp_ipi_target(ALL_ONES, &mask, &base) == 0);
	CHECK(mask == 7U && base == 7U);
	CHECK(be_mvp_ipi_target(1U, (be_u64 *)0, &base) == 0);
	CHECK(be_mvp_ipi_target(1U, &mask, (be_u64 *)0) == 0);
}

/* Every other hart's state as hart 0 reads it, in hart order. */
static int census_of(struct be_mvp_hsm_census *census, be_u64 domain0,
		     be_u64 domain1, const long *errors, const be_u64 *states)
{
	be_u64 hart;
	int holds = 1;

	be_mvp_hsm_census_init(census, domain0, domain1);
	for (hart = 1U; hart < BE_MVP_HARTS; ++hart)
		holds = be_mvp_hsm_census_add(census, hart, errors[hart],
					      states[hart]);
	return holds;
}

/*
 * BE_MVP:02's census (Plan revision M0-A.2): both domain harts STOPPED,
 * and every other hart STOPPED but for at most one STARTED, the start
 * rule's boot hart; anything else refuses the census, which stays refused.
 */
static void test_hsm_census(void)
{
	long errors[BE_MVP_HARTS] = { 0 };
	be_u64 states[BE_MVP_HARTS];
	struct be_mvp_hsm_census census;
	be_u64 boot;
	be_u64 other;
	be_u64 state;

	SCENARIO();
	for (other = 0U; other < BE_MVP_HARTS; ++other)
		states[other] = BE_MVP_HSM_STOPPED;
	/* Every hart STOPPED, as Linux kexec leaves them: started=none. */
	CHECK(census_of(&census, 1U, 2U, errors, states) == 1);
	CHECK(census.started == BE_MVP_HSM_NONE && census.refused == 0U);
	CHECK(census.domain_hart[0] == 1U && census.domain_hart[1] == 2U);
	/* Each boot hart the start rule parks: the census holds for any but
	 * a domain's, and names it either way. */
	for (boot = 1U; boot < BE_MVP_HARTS; ++boot) {
		states[boot] = BE_MVP_HSM_STARTED;
		CHECK(census_of(&census, 1U, 2U, errors, states) ==
		      (boot == 1U || boot == 2U ? 0 : 1));
		CHECK(census.started == boot);
		/* A second STARTED hart, before or after it, refuses. */
		for (other = 1U; other < BE_MVP_HARTS; ++other) {
			if (other == boot)
				continue;
			states[other] = BE_MVP_HSM_STARTED;
			CHECK(census_of(&census, 1U, 2U, errors, states) == 0);
			CHECK(census.started == (other < boot ? other : boot));
			states[other] = BE_MVP_HSM_STOPPED;
		}
		states[boot] = BE_MVP_HSM_STOPPED;
	}
	/* Any other state, or an error, on any hart refuses. */
	for (other = 1U; other < BE_MVP_HARTS; ++other) {
		for (state = BE_MVP_HSM_START_PENDING;
		     state <= BE_MVP_HSM_RESUME_PENDING + 1U; ++state) {
			states[other] = state;
			CHECK(census_of(&census, 1U, 2U, errors, states) == 0);
			CHECK(census.started == BE_MVP_HSM_NONE);
		}
		states[other] = BE_MVP_HSM_STOPPED;
		errors[other] = BE_MVP_SBI_ERR_INVALID_PARAM;
		CHECK(census_of(&census, 1U, 2U, errors, states) == 0);
		/* An error's value is never read as a state. */
		states[other] = BE_MVP_HSM_STARTED;
		CHECK(census_of(&census, 1U, 2U, errors, states) == 0);
		CHECK(census.started == BE_MVP_HSM_NONE);
		errors[other] = 0;
		states[other] = BE_MVP_HSM_STOPPED;
	}
	/* The hart-start variant binds domain 1 to hart 9: hart 2 is then
	 * another hart, and may be the start rule's. */
	states[2] = BE_MVP_HSM_STARTED;
	CHECK(census_of(&census, 1U, BE_MVP_VARIANT_HART_START_HART, errors,
			states) == 1);
	CHECK(census.started == 2U);
	/* A one-domain run (the probe images) names no second domain hart:
	 * hart 2 may be the start rule's too, hart 1 still may not. */
	CHECK(census_of(&census, 1U, BE_MVP_HSM_NONE, errors, states) == 1);
	CHECK(census.started == 2U);
	states[2] = BE_MVP_HSM_STOPPED;
	states[1] = BE_MVP_HSM_STARTED;
	CHECK(census_of(&census, 1U, BE_MVP_HSM_NONE, errors, states) == 0);
	CHECK(census.started == 1U);
	states[1] = BE_MVP_HSM_STOPPED;
	/* A refusal is sticky; hart 0 and the none value are never others. */
	be_mvp_hsm_census_init(&census, 1U, 2U);
	CHECK(be_mvp_hsm_census_add(&census, 3U, 0, BE_MVP_HSM_STOPPED) == 1);
	CHECK(be_mvp_hsm_census_add(&census, 0U, 0, BE_MVP_HSM_STOPPED) == 0);
	CHECK(be_mvp_hsm_census_add(&census, 4U, 0, BE_MVP_HSM_STOPPED) == 0);
	be_mvp_hsm_census_init(&census, 1U, 2U);
	CHECK(be_mvp_hsm_census_add(&census, BE_MVP_HSM_NONE, 0,
				    BE_MVP_HSM_STARTED) == 0);
	CHECK(census.started == BE_MVP_HSM_NONE);
	CHECK(be_mvp_hsm_census_add((struct be_mvp_hsm_census *)0, 3U, 0,
				    BE_MVP_HSM_STOPPED) == 0);
	be_mvp_hsm_census_init((struct be_mvp_hsm_census *)0, 1U, 2U);
}

/* Each domain hart has its own counters, window, phase, and failure. */
static void test_per_hart(void)
{
	struct be_mvp_exit base = ecall(BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, 0U);
	struct be_mvp_exit write = ecall(BE_MVP_SBI_EID_DBCN, 0U, 16U,
					 WINDOW_GPA + 0x1000U, 0U);
	struct be_mvp_exit ipi = exit_with(SSI, ECALL_PC);
	struct be_mvp_exit fault = exit_with(
		BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT, ECALL_PC);
	struct be_mvp_result result;
	unsigned int domain;

	SCENARIO();
	harts[0] = fresh_state();
	harts[1] = fresh_state();
	CHECK(be_mvp_handle_exit(&harts[0], &windows[0], &no_leaf, &base,
				 &result) ==
	      BE_MVP_ACTION_RETURN);
	CHECK(be_mvp_handle_exit(&harts[1], &windows[1], &no_leaf, &ipi,
				 &result) ==
	      BE_MVP_ACTION_IPI);
	CHECK(be_mvp_handle_exit(&harts[1], &windows[1], &no_leaf, &ipi,
				 &result) ==
	      BE_MVP_ACTION_IPI);
	/* DBCN reads the calling domain's own window. */
	CHECK(be_mvp_handle_exit(&harts[0], &windows[0], &no_leaf, &write,
				 &result) ==
	      BE_MVP_ACTION_CONSOLE_WRITE);
	CHECK(result.source_pa == WINDOW_HPA + 0x1000U && result.length == 16U);
	CHECK(be_mvp_handle_exit(&harts[1], &windows[1], &no_leaf, &write,
				 &result) ==
	      BE_MVP_ACTION_CONSOLE_WRITE);
	CHECK(result.source_pa == WINDOW_G1_HPA + 0x1000U);
	CHECK(harts[0].counts.exits == 2U && harts[0].counts.base == 1U &&
	      harts[0].counts.dbcn_write == 1U && harts[0].counts.ipi == 0U);
	CHECK(harts[1].counts.exits == 3U && harts[1].counts.ipi == 2U &&
	      harts[1].counts.dbcn_write == 1U && harts[1].counts.base == 0U);
	for (domain = 0U; domain < 2U; ++domain)
		CHECK(harts[domain].counts.exits ==
		      be_mvp_counts_sbi(&harts[domain].counts) +
			      harts[domain].counts.ipi);
	CHECK(be_mvp_counts_sbi((const struct be_mvp_counts *)0) == 0U);
	/* One hart's terminal exit fails that hart alone; hart 0 ends the
	 * run when its FAIL record arrives (Q10). */
	CHECK(be_mvp_handle_exit(&harts[1], &windows[1], &no_leaf, &fault,
				 &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_GUEST_PAGE_FAULT);
	CHECK(harts[1].phase == BE_MVP_PHASE_FAILED);
	CHECK(be_mvp_handle_exit(&harts[0], &windows[0], &no_leaf, &base,
				 &result) ==
	      BE_MVP_ACTION_RETURN);
	CHECK(harts[0].phase == BE_MVP_PHASE_RUNNING &&
	      harts[0].counts.exits == 3U);
	/* G0's ceiling does not limit G1. */
	harts[0] = (struct be_mvp_state)BE_MVP_STATE_INITIALIZER(1U);
	harts[1] = (struct be_mvp_state)BE_MVP_STATE_INITIALIZER(1U);
	CHECK(be_mvp_handle_exit(&harts[0], &windows[0], &no_leaf, &base,
				 &result) ==
	      BE_MVP_ACTION_RETURN);
	CHECK(be_mvp_handle_exit(&harts[1], &windows[1], &no_leaf, &base,
				 &result) ==
	      BE_MVP_ACTION_RETURN);
	CHECK(be_mvp_handle_exit(&harts[1], &windows[1], &no_leaf, &base,
				 &result) ==
	      BE_MVP_ACTION_TERMINAL);
	CHECK(result.failure == BE_MVP_CLASS_EXIT_BUDGET);
	CHECK(harts[1].counts.exits == 2U && harts[0].counts.exits == 1U);
	CHECK(harts[0].phase == BE_MVP_PHASE_RUNNING);
}

static int line_is(const struct be_mvp_line *line, const char *text)
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
	static const char *const counts[] = {
		" exits=", " sbi=", " ipi=", " base=", " time=",
		" dbcn_write=", " dbcn_read=", " dbcn_byte=", " srst=",
		" refused=", " lines=",
	};
	struct be_mvp_line line;
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(values); ++index) {
		be_mvp_line_reset(&line);
		be_mvp_line_hex(&line, values[index].value);
		CHECK(line_is(&line, values[index].hex));
		be_mvp_line_reset(&line);
		be_mvp_line_decimal(&line, values[index].value);
		CHECK(line_is(&line, values[index].decimal));
	}

	/* Plan markers composed from fixed text and values. */
	be_mvp_line_reset(&line);
	be_mvp_line_text(&line, "BE_MVP:03 GSTAGE_BUILT_REWALKED domain=");
	be_mvp_line_decimal(&line, 1U);
	be_mvp_line_text(&line, " hart=");
	be_mvp_line_decimal(&line, BE_MVP_DOMAIN1_HART);
	be_mvp_line_text(&line, " gpa=");
	be_mvp_line_hex(&line, WINDOW_GPA);
	be_mvp_line_text(&line, " hpa=");
	be_mvp_line_hex(&line, WINDOW_G1_HPA);
	be_mvp_line_text(&line, " size=");
	be_mvp_line_hex(&line, WINDOW_BYTES);
	be_mvp_line_text(&line, " leaves=");
	be_mvp_line_decimal(&line, 32U);
	be_mvp_line_text(&line, " root=");
	be_mvp_line_hex(&line, BE_MVP_G1_ROOT_HPA);
	be_mvp_line_text(&line, " vmid=");
	be_mvp_line_decimal(&line, BE_MVP_G1_VMID);
	be_mvp_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1 "
		      "hart=2 gpa=0x80000000 hpa=0x114000000 size=0x4000000 "
		      "leaves=32 root=0x10203c000 vmid=2\n"));
	be_mvp_line_reset(&line);
	be_mvp_line_text(&line, "BE_MVP:07 BLOCKS_PUBLISHED region=");
	be_mvp_line_hex(&line, BE_MVP_HART_REGION_HPA);
	be_mvp_line_text(&line, " bytes=");
	be_mvp_line_hex(&line, BE_MVP_HART_REGION_BYTES);
	be_mvp_line_text(&line, " generation=");
	be_mvp_line_decimal(&line, BE_MVP_GENERATION);
	be_mvp_line_text(&line, " budget_ticks=");
	be_mvp_line_hex(&line, BE_MVP_RUN_BUDGET);
	be_mvp_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_MVP:07 BLOCKS_PUBLISHED region=0x102044000 "
		      "bytes=0x20000 generation=1 "
		      "budget_ticks=0x100000000\n"));
	be_mvp_line_reset(&line);
	be_mvp_line_text(&line, "BE_MVP:09 HART_READY hart=");
	be_mvp_line_decimal(&line, 1U);
	be_mvp_line_text(&line, " domain=");
	be_mvp_line_decimal(&line, 0U);
	be_mvp_line_text(&line, " hgatp=");
	be_mvp_line_hex(&line, BE_MVP_G0_HGATP);
	be_mvp_line_text(&line, " hstatus_controls=");
	be_mvp_line_hex(&line, 0x180U);
	be_mvp_line_text(&line, " hedeleg=");
	be_mvp_line_hex(&line, 0xb15cU);
	be_mvp_line_text(&line, " hideleg=");
	be_mvp_line_hex(&line, 0x40U);
	be_mvp_line_text(&line, " hcounteren=");
	be_mvp_line_hex(&line, 0x2U);
	be_mvp_line_text(&line, " sie=");
	be_mvp_line_hex(&line, 0x2U);
	be_mvp_line_text(&line, " henvcfg=");
	be_mvp_line_hex(&line, BE_MVP_HENVCFG_STCE);
	be_mvp_line_text(&line, " vstimecmp=");
	be_mvp_line_hex(&line, ALL_ONES);
	be_mvp_line_text(&line, "\n");
	CHECK(line_is(&line, "BE_MVP:09 HART_READY hart=1 domain=0 "
		      "hgatp=0x8000100000102034 hstatus_controls=0x180 "
		      "hedeleg=0xb15c hideleg=0x40 hcounteren=0x2 sie=0x2 "
		      "henvcfg=0x8000000000000000 "
		      "vstimecmp=0xffffffffffffffff\n"));
	/* The worst-case DETAIL lines fit. */
	be_mvp_line_reset(&line);
	be_mvp_line_text(&line, "BE_MVP:DETAIL domain=");
	be_mvp_line_decimal(&line, 1U);
	be_mvp_line_text(&line, " hart=");
	be_mvp_line_decimal(&line, ALL_ONES);
	be_mvp_line_text(&line, " cause=");
	be_mvp_line_hex(&line, ALL_ONES);
	for (index = 0U; index < 4U; ++index) {
		be_mvp_line_text(&line, " htinst=");
		be_mvp_line_hex(&line, ALL_ONES);
	}
	be_mvp_line_text(&line, " spvp=");
	be_mvp_line_decimal(&line, 1U);
	be_mvp_line_text(&line, " vsatp=");
	be_mvp_line_hex(&line, ALL_ONES);
	be_mvp_line_text(&line, " exits=");
	be_mvp_line_decimal(&line, ALL_ONES);
	be_mvp_line_text(&line, "\n");
	CHECK(line.overflow == 0U && line.length < 260U);
	be_mvp_line_reset(&line);
	be_mvp_line_text(&line, "BE_MVP:DETAIL arm domain=");
	be_mvp_line_decimal(&line, 1U);
	be_mvp_line_text(&line, " hart=");
	be_mvp_line_decimal(&line, ALL_ONES);
	be_mvp_line_text(&line, " register=");
	be_mvp_line_text(&line, be_mvp_vcsr_name(BE_MVP_VCSR_SCOUNTEREN));
	be_mvp_line_text(&line, " wanted=");
	be_mvp_line_hex(&line, ALL_ONES);
	be_mvp_line_text(&line, " readback=");
	be_mvp_line_hex(&line, ALL_ONES);
	be_mvp_line_text(&line, "\n");
	CHECK(line.overflow == 0U && line.length < 150U);
	/* The longest count lines fit: every count at its ceiling's bound
	 * (a domain's exits are at most 2^20 + 1), a hart ID of 20 digits,
	 * and every tick field all ones. */
	be_mvp_line_reset(&line);
	be_mvp_line_text(&line, "BE_MVP:12 DOMAIN_SHUTDOWN hart=");
	be_mvp_line_decimal(&line, ALL_ONES);
	be_mvp_line_text(&line, " domain=");
	be_mvp_line_decimal(&line, 1U);
	for (index = 0U; index < BE_ARRAY_SIZE(counts); ++index) {
		be_mvp_line_text(&line, counts[index]);
		be_mvp_line_decimal(&line, BE_MVP_EXIT_CEILING + 1U);
	}
	be_mvp_line_text(&line, " ring_peak=");
	be_mvp_line_hex(&line, BE_MVP_OUTBOUND_RING_BYTES);
	be_mvp_line_text(&line, " entered=");
	be_mvp_line_hex(&line, ALL_ONES);
	be_mvp_line_text(&line, " ticks=");
	be_mvp_line_hex(&line, ALL_ONES);
	be_mvp_line_text(&line, "\n");
	CHECK(line.overflow == 0U && line.length < BE_MVP_LINE_CAPACITY);
	be_mvp_line_reset(&line);
	be_mvp_line_text(&line, "BE_MVP:13 RUN_COMPLETE domains=");
	be_mvp_line_decimal(&line, BE_MVP_DOMAINS);
	be_mvp_line_text(&line, " records=");
	be_mvp_line_decimal(&line, ALL_ONES);
	be_mvp_line_text(&line, " wakes=");
	be_mvp_line_decimal(&line, ALL_ONES);
	be_mvp_line_text(&line, " idle_ticks=");
	be_mvp_line_hex(&line, ALL_ONES);
	be_mvp_line_text(&line, " overlap_ticks=");
	be_mvp_line_hex(&line, ALL_ONES);
	be_mvp_line_text(&line, " ticks=");
	be_mvp_line_hex(&line, ALL_ONES);
	be_mvp_line_text(&line, "\n");
	CHECK(line.overflow == 0U && line.length < BE_MVP_LINE_CAPACITY);

	/* Overflow is sticky and makes the line unusable. */
	be_mvp_line_reset(&line);
	for (index = 0U; index < BE_MVP_LINE_CAPACITY; ++index)
		be_mvp_line_text(&line, "x");
	CHECK(line.length == BE_MVP_LINE_CAPACITY && line.overflow == 0U);
	be_mvp_line_text(&line, "y");
	CHECK(line.overflow == 1U);
	CHECK(line.length == BE_MVP_LINE_CAPACITY);
	be_mvp_line_reset(&line);
	CHECK(line.length == 0U && line.overflow == 0U);
	be_mvp_line_text(&line, (const char *)0);
	CHECK(line.overflow == 1U);
	be_mvp_line_reset(&line);
	for (index = 0U; index < 17U; ++index)
		be_mvp_line_hex(&line, ALL_ONES);
	CHECK(line.length == 17U * 18U && line.overflow == 0U);
	be_mvp_line_hex(&line, ALL_ONES);
	CHECK(line.overflow == 1U);
	CHECK(line.length == BE_MVP_LINE_CAPACITY);
	be_mvp_line_reset((struct be_mvp_line *)0);
	be_mvp_line_text((struct be_mvp_line *)0, "x");
	be_mvp_line_hex((struct be_mvp_line *)0, 1U);
	be_mvp_line_decimal((struct be_mvp_line *)0, 1U);
}

/* The domain a replay runs as, on its own hart with its own window. */
static be_u32 replay_domain;

/* One SBI call of a replay; checks the decision and, for returns, the
 * values the guest receives. */
static void replay(struct be_mvp_state *state, be_u64 eid, be_u64 fid,
		   be_u64 argument0, be_u64 argument1,
		   enum be_mvp_action action, long error, be_u64 value)
{
	struct be_mvp_exit record = ecall(eid, fid, argument0, argument1, 0U);
	struct be_mvp_result result;
	be_u32 domain = replay_domain;

	record.time = ENTRY_TIME + state->counts.exits * BE_U64_C(0x40000);
	CHECK(be_mvp_handle_exit(state, &windows[domain], &no_leaf, &record,
				 &result) ==
	      action);
	CHECK(result.error == error && result.value == value);
	if (action == BE_MVP_ACTION_CONSOLE_WRITE)
		CHECK(result.source_pa ==
		      argument1 - WINDOW_GPA + windows[domain].hpa_base);
	CHECK(state->phase == (action == BE_MVP_ACTION_SHUTDOWN ?
			       BE_MVP_PHASE_STOPPED :
			       action == BE_MVP_ACTION_TERMINAL ?
			       BE_MVP_PHASE_FAILED : BE_MVP_PHASE_RUNNING));
}

/* One IPI exit of a replay: hart 0's PING after the domain's first line. */
static void replay_ipi(struct be_mvp_state *state)
{
	struct be_mvp_exit record = exit_with(SSI, ECALL_PC);
	struct be_mvp_result result;

	record.time = ENTRY_TIME + state->counts.exits * BE_U64_C(0x40000);
	CHECK(be_mvp_handle_exit(state, &windows[replay_domain], &no_leaf,
				 &record, &result) == BE_MVP_ACTION_IPI);
	CHECK(result.resume_pc == ECALL_PC);
}

static void replay_write(struct be_mvp_state *state, be_u64 call)
{
	static const be_u64 lengths[] = { 57U, 120U, 16U, 16U, 300U, 4U, 16U,
					  200U };
	be_u64 length = lengths[call % BE_ARRAY_SIZE(lengths)];
	be_u64 gpa = BE_U64_C(0x81234000) + (call % 8U) * 0x100U;

	replay(state, BE_MVP_SBI_EID_DBCN, 0U, length, gpa,
	       BE_MVP_ACTION_CONSOLE_WRITE, BE_MVP_SBI_SUCCESS,
	       length < 256U ? length : 256U);
}

/* The Base calls a v7.2 uniprocessor boot makes before its first write. */
static void replay_base(struct be_mvp_state *state)
{
	replay(state, BE_MVP_SBI_EID_BASE, 0U, 0U, 0U, BE_MVP_ACTION_RETURN, 0,
	       0x2000000U);
	replay(state, BE_MVP_SBI_EID_BASE, 1U, 0U, 0U, BE_MVP_ACTION_RETURN, 0,
	       0x4245U);
	replay(state, BE_MVP_SBI_EID_BASE, 2U, 0U, 0U, BE_MVP_ACTION_RETURN, 0,
	       5U);
	replay(state, BE_MVP_SBI_EID_BASE, 3U, BE_MVP_SBI_EID_TIME, 0U,
	       BE_MVP_ACTION_RETURN, 0, 1U);
	replay(state, BE_MVP_SBI_EID_BASE, 3U, EID_IPI, 0U,
	       BE_MVP_ACTION_RETURN, 0, 0U);
	replay(state, BE_MVP_SBI_EID_BASE, 3U, EID_RFENCE, 0U,
	       BE_MVP_ACTION_RETURN, 0, 0U);
	replay(state, BE_MVP_SBI_EID_BASE, 3U, BE_MVP_SBI_EID_SRST, 0U,
	       BE_MVP_ACTION_RETURN, 0, 1U);
	replay(state, BE_MVP_SBI_EID_BASE, 3U, BE_MVP_SBI_EID_DBCN, 0U,
	       BE_MVP_ACTION_RETURN, 0, 1U);
}

/* The B6 research reference boot's 138 calls before its shutdown, with
 * the IPI probe's one IPI after the first write. */
static void replay_boot(struct be_mvp_state *state)
{
	be_u64 call;
	be_u64 writes = 0U;
	unsigned int round;

	replay_base(state);
	for (call = 0U; call < 12U; ++call) {
		replay_write(state, writes++);
		if (call == 0U)
			replay_ipi(state);
	}
	for (round = 0U; round < 2U; ++round) {
		replay(state, BE_MVP_SBI_EID_BASE, 4U, 0U, 0U,
		       BE_MVP_ACTION_RETURN, 0, 0U);
		replay(state, BE_MVP_SBI_EID_BASE, 5U, 0U, 0U,
		       BE_MVP_ACTION_RETURN, 0, 0U);
		replay(state, BE_MVP_SBI_EID_BASE, 6U, 0U, 0U,
		       BE_MVP_ACTION_RETURN, 0, 0U);
	}
	for (call = 0U; call < 45U; ++call)
		replay_write(state, writes++);
	/* From call 72, hvc polls for input between its writes. */
	for (call = 0U; call < 35U; ++call) {
		replay(state, BE_MVP_SBI_EID_DBCN, 1U, 16U,
		       BE_U64_C(0x81fff000), BE_MVP_ACTION_RETURN,
		       BE_MVP_SBI_ERR_DENIED, 0U);
		if (call < 32U)
			replay_write(state, writes++);
	}
}

/*
 * The B6 research reference boot's 139 SBI calls (B6 platform research
 * section 1c), for each domain on its own hart: 3 Base IDs; probes for
 * TIME, IPI, RFENCE, SRST, and DBCN answered 1, 0, 0, 1, 1; 6 machine-ID
 * reads; 89 DBCN writes; 35 DBCN reads denied with -4; and one SRST
 * shutdown, which stops only that domain; plus the IPI probe's one IPI.
 * The Base answers are B7's.
 */
static void test_census(void)
{
	struct be_mvp_state state;
	be_u64 call;
	unsigned int domain;

	SCENARIO();
	for (domain = 0U; domain < 2U; ++domain) {
		state = fresh_state();
		replay_domain = domain;
		replay_boot(&state);
		CHECK(state.counts.exits == 139U);
		replay(&state, BE_MVP_SBI_EID_SRST, 0U, 0U, 0U,
		       BE_MVP_ACTION_SHUTDOWN, 0, 0U);
		CHECK(state.phase == BE_MVP_PHASE_STOPPED);
		CHECK(state.counts.exits == 140U);
		CHECK(state.counts.base == 14U);
		CHECK(state.counts.time == 0U);
		CHECK(state.counts.dbcn_write == 89U);
		CHECK(state.counts.dbcn_read == 35U);
		CHECK(state.counts.dbcn_byte == 0U);
		CHECK(state.counts.srst == 1U);
		CHECK(state.counts.refused == 0U);
		CHECK(state.counts.ipi == 1U);
		CHECK(call_sum(&state.counts) == 139U);
		CHECK(state.counts.exits ==
		      be_mvp_counts_sbi(&state.counts) + state.counts.ipi);
		CHECK(state.counts.exits <= BE_MVP_EXIT_CEILING);
	}
	/* With the exit-budget variant's ceiling a boot stops at 65. */
	state = (struct be_mvp_state)BE_MVP_STATE_INITIALIZER(
		BE_MVP_VARIANT_EXIT_CEILING);
	replay_domain = 0U;
	replay_base(&state);
	for (call = 0U; call < 56U; ++call)
		replay_write(&state, call);
	CHECK(state.counts.exits == 64U && state.phase == BE_MVP_PHASE_RUNNING);
	replay(&state, BE_MVP_SBI_EID_DBCN, 0U, 16U, BE_U64_C(0x81234000),
	       BE_MVP_ACTION_TERMINAL, 0, 0U);
	CHECK(state.failure == BE_MVP_CLASS_EXIT_BUDGET);
	CHECK(state.counts.exits == 65U);
}

/*
 * Two domains at once, each on its own hart: their boots interleaved call
 * by call, each domain's IPI after its first write, then both shutdowns
 * in either order. Every exit lands in its own hart's counts, and each
 * hart's exits are its SBI calls and its IPI.
 */
static void test_census_two_harts(void)
{
	be_u64 call;
	unsigned int domain;

	SCENARIO();
	harts[0] = fresh_state();
	harts[1] = fresh_state();
	for (call = 0U; call < 40U; ++call) {
		for (domain = 0U; domain < 2U; ++domain) {
			replay_domain = domain;
			if (call < 8U && domain == 0U)
				replay_base(&harts[domain]);
			replay_write(&harts[domain], call);
			if (call == domain)
				replay_ipi(&harts[domain]);
		}
	}
	replay_domain = 1U;
	replay(&harts[1], BE_MVP_SBI_EID_SRST, 0U, 0U, 0U,
	       BE_MVP_ACTION_SHUTDOWN, 0, 0U);
	/* G0 runs on alone after G1 stopped. */
	replay_domain = 0U;
	replay_write(&harts[0], 40U);
	replay(&harts[0], BE_MVP_SBI_EID_SRST, 0U, 0U, 0U,
	       BE_MVP_ACTION_SHUTDOWN, 0, 0U);
	CHECK(harts[0].counts.base == 64U && harts[1].counts.base == 0U);
	CHECK(harts[0].counts.dbcn_write == 41U &&
	      harts[1].counts.dbcn_write == 40U);
	CHECK(harts[0].counts.ipi == 1U && harts[1].counts.ipi == 1U);
	CHECK(harts[0].counts.srst == 1U && harts[1].counts.srst == 1U);
	for (domain = 0U; domain < 2U; ++domain)
		CHECK(harts[domain].counts.exits ==
		      be_mvp_counts_sbi(&harts[domain].counts) +
			      harts[domain].counts.ipi);
	CHECK(harts[0].counts.exits == 64U + 41U + 1U + 1U);
	CHECK(harts[1].counts.exits == 40U + 1U + 1U);
}

/* The sbi-time variant: no sstc in the DT, so Linux arms through TIME. */
static void test_census_sbi_time(void)
{
	struct be_mvp_state state = fresh_state();
	be_u64 call;

	SCENARIO();
	replay_domain = 1U;
	replay_base(&state);
	for (call = 0U; call < 10U; ++call)
		replay_write(&state, call);
	for (call = 0U; call < 20U; ++call) {
		be_u64 deadline = (call & 1U) ? ALL_ONES :
			ENTRY_TIME + (call + 1U) * BE_U64_C(96000);
		struct be_mvp_exit record = ecall(BE_MVP_SBI_EID_TIME, 0U,
						  deadline, 0U, 0U);
		struct be_mvp_result result;

		record.time = ENTRY_TIME + call * BE_U64_C(48000);
		CHECK(be_mvp_handle_exit(&state, &windows[1], &no_leaf, &record,
					 &result) == BE_MVP_ACTION_SET_TIMER);
		CHECK(result.timer == deadline && result.error == 0 &&
		      result.value == 0U);
	}
	replay_ipi(&state);
	replay(&state, BE_MVP_SBI_EID_SRST, 0U, 0U, 0U, BE_MVP_ACTION_SHUTDOWN,
	       0, 0U);
	CHECK(state.counts.time == 20U && state.counts.base == 8U);
	CHECK(state.counts.dbcn_write == 10U && state.counts.srst == 1U);
	CHECK(state.counts.exits == 40U && state.counts.ipi == 1U &&
	      call_sum(&state.counts) == 39U);
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
	test_terminal_exits();
	test_frame_integrity();
	test_apply_return();
	test_entry_frame();
	test_ipi_exit();
	test_per_hart();
	test_vcsr();
	test_console();
	test_console_interleave();
	test_ipi_serve();
	test_records();
	test_ack_wait();
	test_denials();
	test_denial_records();
	test_mgmt_decide();
	test_mgmt_calls();
	test_mgmt_records();
	test_hsm();
	test_hsm_census();
	test_line_builder();
	test_census();
	test_census_two_harts();
	test_census_sbi_time();

	puts("BE_MVP_SBI_CHECK: PASS");
	print_count("BE_MVP_SBI_CHECK: scenarios=", scenarios);
	print_count("BE_MVP_SBI_CHECK: assertions=", assertions);
	return 0;
}
