// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for probe-platform's IPI probe (mvp-probe.c, which
 *          it includes as probe-platform builds it): hart 0's two IPI
 *          phases, ipis(), against a model of domain 0's hart that makes
 *          its receipts with the module's receipt(), publishes its phases
 *          with set_phase(), and takes its next probe call and its V=1
 *          IPIs through be_mvp_probe_exit(), each step at one of hart 0's
 *          calls into the executor or the runtime. In each schedule the
 *          domain hart's FID_IPI_VS call, the V=1 phase's start, comes a
 *          given number of hart 0's calls after the hundredth HS receipt,
 *          with one to four domain-hart steps at each call: from within
 *          hart 0's hundredth send, before hart 0 reads that receipt, to
 *          after its HS line. Every schedule's two lines must be a full
 *          run's, delivered=100 each, with no FAIL. Then an HS IPI lost:
 *          hart 0's line with the count it read, and FAIL ipi.
 * Trust:   host evidence only. No CSR, fence, IPI, second hart, QEMU, or
 *          hardware behaviour is exercised: the interleaving is the test's
 *          schedule at the calls hart 0 makes, and the domain hart's wait
 *          in HS (ipi_hs()'s loop: one receipt per IPI found pending, then
 *          PHASE_IPI_HS_DONE) is the model's.
 * Scope:   the probe's IPI phases (planning/mvp-m0-plan.md, "Platform
 *          record: probes and negative images") and the race M9-3 found
 *          (planning/mvp-m9-plan.md, stop 2): the V=1 phase's start reset
 *          the count hart 0 had still to read for its HS line.
 */
#include <setjmp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define BE_MVP_PROBE_IMAGE	BE_MVP_PROBE_PLATFORM
#include "mvp-probe.c"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_PROBE_CHECK: assertion failed: " \
			       "%s:%d: %s\n", __FILE__, __LINE__, \
			       #condition); \
			exit(1); \
		} \
	} while (0)

/* A run's check: on a failure, the schedule and hart 0's lines too. */
#define CHECK_RUN(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_PROBE_CHECK: assertion failed: " \
			       "%s:%d: %s\n", __FILE__, __LINE__, \
			       #condition); \
			print_run(); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

/*
 * The domain hart's receipt delays: a permutation of 0x40 to 0xa3 in HS
 * and of 0x80 to 0xe3 at V=1, so each line's min, median, and max are
 * known.
 */
#define DELTA_HS(index)		(BE_U64_C(0x40) + (index) * 37U % 100U)
#define DELTA_VS(index)		(BE_U64_C(0x80) + (index) * 71U % 100U)
/* Each of hart 0's time reads moves the clock 1/64 of an IPI's bound. */
#define CLOCK_STEP		(BE_MVP_PROBE_IPI_TICKS / 64U)
#define DELAYS			16U
#define BURSTS			4U
#define NEVER			(~BE_U64_C(0))
#define LOST			49U
#define LINES			2U
#define LINE_VALUES		6U

static const char line_hs[] = "BE_MVP:PROBE ipi mode=hs sent=100 "
	"delivered=100 min=0x40 median=0x72 max=0xa3 spv=100";
static const char line_vs[] = "BE_MVP:PROBE ipi mode=vs sent=100 "
	"delivered=100 min=0x80 median=0xb2 max=0xe3 spv=100";
static const char line_lost[] = "BE_MVP:PROBE ipi mode=hs sent=49 "
	"delivered=49 min=0x40 median=0x70 max=0xa3 spv=49";

/* The domain hart's place in the probe stub. */
enum stage {
	STAGE_HS,	/* in ipi_hs()'s loop */
	STAGE_HS_LAST,	/* the hundredth receipt made */
	STAGE_HS_DONE,	/* PHASE_IPI_HS_DONE published; FID_IPI_VS next */
	STAGE_VS,	/* spinning at V=1 */
	STAGE_DONE,
};

static struct {
	jmp_buf hart0;		/* hart 0's FAIL ends its phase here */
	jmp_buf hart1;		/* the domain hart's resume ends its exit */
	be_u64 clock;
	be_u64 delay;
	be_u64 burst;
	be_u64 countdown;
	be_u64 lost;		/* the first HS IPI never delivered */
	be_u64 sends;
	be_u64 receipts;
	be_u64 lines;
	be_u64 values[LINES][LINE_VALUES];
	struct be_mvp_line line[LINES];
	enum be_mvp_class failure;
	enum stage stage;
	be_u32 mode;
	be_u32 pending;		/* sip.SSIP on the domain hart */
	be_u32 domain;		/* the model is running the domain hart */
	be_u32 sending;		/* inside hart 0's send of an IPI */
	be_u32 failed;
	be_u32 domain_failed;
	be_u32 unexpected;
	be_u32 call_before_line;
	be_u32 call_in_send;
} model;

static struct be_mvp_hart_page hart_page;
static struct be_mvp_exit exit_record;

const struct be_mvp_binding be_mvp_bindings[BE_MVP_DOMAINS] =
	BE_MVP_BINDINGS_INITIALIZER;
const be_u8 be_mvp_probe_stub[4] = { 0U };
const be_u8 be_mvp_probe_stub_end[4] = { 0U };

static void print_run(void)
{
	char lost[24];
	be_u64 index;

	(void)snprintf(lost, sizeof(lost), "%lu", model.lost);
	printf("BE_MVP_PROBE_CHECK: schedule delay=%lu burst=%lu lost=%s "
	       "call_before_line=%u call_in_send=%u failure=%s\n",
	       model.delay, model.burst, model.lost == NEVER ? "none" : lost,
	       model.call_before_line, model.call_in_send,
	       model.failed != 0U ? be_mvp_class_name(model.failure) : "none");
	for (index = 0U; index < model.lines && index < LINES; ++index)
		printf("BE_MVP_PROBE_CHECK: line %lu: %.*s\n", index,
		       (int)model.line[index].length, model.line[index].text);
}

static int line_is(const struct be_mvp_line *line, const char *wanted)
{
	return line->overflow == 0U && line->length == strlen(wanted) &&
	       memcmp(line->text, wanted, strlen(wanted)) == 0;
}

/* The line as hart 0's formatter (mvp-runtime.c) builds it; its values. */
static void render(struct be_mvp_line *line, be_u64 *kept,
		   const char *format, const be_u64 *values)
{
	char literal[2] = { '\0', '\0' };
	be_u64 used = 0U;
	be_u64 index;

	be_mvp_line_reset(line);
	for (index = 0U; format[index] != '\0'; ++index) {
		char kind = format[index + 1U];

		if (format[index] != '%' || (kind != 'x' && kind != 'd')) {
			literal[0] = format[index];
			be_mvp_line_text(line, literal);
			continue;
		}
		++index;
		if (used < LINE_VALUES)
			kept[used] = values[used];
		if (kind == 'x')
			be_mvp_line_hex(line, values[used]);
		else
			be_mvp_line_decimal(line, values[used]);
		++used;
	}
}

/* One exit of the stub: its probe call @fid, or an IPI at V=1. */
static void domain_exit(be_u64 scause, be_u64 fid, be_u64 time)
{
	memset(&exit_record, 0, sizeof(exit_record));
	exit_record.frame.scause = scause;
	if (scause == BE_MVP_SCAUSE_VS_ECALL)
		exit_record.frame.gpr[BE_R4_GPR_A7] = BE_MVP_PROBE_EID;
	exit_record.frame.gpr[BE_R4_GPR_A6] = fid;
	exit_record.hstatus = BE_MVP_HSTATUS_SPV;
	exit_record.time = time;
	if (setjmp(model.hart1) == 0)
		be_mvp_probe_exit(&hart_page, &exit_record);
}

/* The domain hart's next step: 1 if it took one, 0 if it waits. */
static int domain_step(void)
{
	switch (model.stage) {
	case STAGE_HS:
		if (model.pending == 0U)
			return 0;
		/* ipi_hs()'s loop: the receipt of the IPI found pending. */
		receipt(0U, probe.sent + DELTA_HS(model.receipts),
			BE_MVP_HSTATUS_SPV);
		if (++model.receipts == BE_MVP_PROBE_IPIS)
			model.stage = STAGE_HS_LAST;
		return 1;
	case STAGE_HS_LAST:
		/* ipi_hs()'s end. */
		set_phase(PHASE_IPI_HS_DONE);
		model.stage = STAGE_HS_DONE;
		return 1;
	case STAGE_HS_DONE:
		if (model.countdown != 0U) {
			--model.countdown;
			return 0;
		}
		/* The stub's next call: the V=1 phase's start. */
		model.call_before_line = model.lines == 0U;
		model.call_in_send = model.sending;
		domain_exit(BE_MVP_SCAUSE_VS_ECALL, BE_MVP_PROBE_FID_IPI_VS,
			    0U);
		model.stage = STAGE_VS;
		model.receipts = 0U;
		return 1;
	case STAGE_VS:
		if (model.pending == 0U)
			return 0;
		domain_exit(BE_MVP_SCAUSE_SUPERVISOR_SOFTWARE, 0U,
			    probe.sent + DELTA_VS(model.receipts));
		if (++model.receipts == BE_MVP_PROBE_IPIS)
			model.stage = STAGE_DONE;
		return 1;
	case STAGE_DONE:
	default:
		return 0;
	}
}

/* One of hart 0's calls: the domain hart takes up to burst steps. */
static void schedule(void)
{
	be_u64 step;

	if (model.domain != 0U)
		return;
	model.domain = 1U;
	for (step = 0U; step < model.burst; ++step)
		if (domain_step() == 0)
			break;
	model.domain = 0U;
}

be_u64 be_mvp_exec_read_time(void)
{
	schedule();
	model.clock += CLOCK_STEP;
	return model.clock;
}

void be_mvp_exec_fence_w_w(void)
{
	schedule();
}

void be_mvp_exec_fence_r_r(void)
{
	schedule();
}

void be_mvp_exec_fence_r_w(void)
{
	schedule();
}

long be_mvp_send_ipi(be_u64 hart)
{
	if (hart != be_mvp_bindings[0].hart)
		++model.unexpected;
	if (model.sends++ < model.lost)
		model.pending = 1U;
	model.sending = 1U;
	schedule();
	model.sending = 0U;
	return BE_MVP_SBI_SUCCESS;
}

be_u64 be_mvp_exec_clear_ssip(void)
{
	be_u64 sip = model.pending != 0U ? BE_MVP_SIE_SSIE : 0U;

	model.pending = 0U;
	return sip;
}

void be_mvp_probe_poll(void)
{
	schedule();
}

void be_mvp_probe_emit(const char *format, const be_u64 *values)
{
	schedule();
	if (model.lines < LINES)
		render(&model.line[model.lines], model.values[model.lines],
		       format, values);
	++model.lines;
}

void be_mvp_probe_fail(enum be_mvp_class failure, const char *format,
		       const be_u64 *values)
{
	(void)format;
	(void)values;
	model.failed = 1U;
	model.failure = failure;
	longjmp(model.hart0, 1);
}

/* The calls the model never makes; each would count as unexpected. */
be_u64 be_mvp_exec_wait(be_u64 pending)
{
	(void)pending;
	++model.unexpected;
	return model.clock;
}

be_u64 be_mvp_exec_install_hgatp(be_u64 hgatp)
{
	++model.unexpected;
	return hgatp;
}

void be_mvp_exec_park(void)
{
	++model.unexpected;
	longjmp(model.hart1, 1);
}

void be_mvp_probe_shutdown(void)
{
	++model.unexpected;
	longjmp(model.hart0, 1);
}

void be_mvp_runtime_terminal(enum be_mvp_class failure)
{
	++model.unexpected;
	model.failed = 1U;
	model.failure = failure;
	longjmp(model.hart0, 1);
}

void be_mvp_exec_resume(struct be_mvp_exit *record, be_u64 expected_hgatp,
			be_u64 expected_hedeleg)
{
	(void)record;
	(void)expected_hgatp;
	(void)expected_hedeleg;
	longjmp(model.hart1, 1);
}

void be_mvp_hart_terminal(struct be_mvp_exit *record,
			  enum be_mvp_class failure)
{
	(void)record;
	(void)failure;
	model.domain_failed = 1U;
	longjmp(model.hart1, 1);
}

/*
 * A fresh run: the probe's words zero, as hart 0 clears them before the
 * barrier, and the domain hart in ipi_hs() with PHASE_IPI_HS published.
 */
static void start(be_u64 delay, be_u64 burst, be_u64 lost)
{
	memset(&probe, 0, sizeof(probe));
	memset(&model, 0, sizeof(model));
	model.clock = BE_U64_C(0x1000);
	model.delay = delay;
	model.countdown = delay;
	model.burst = burst;
	model.lost = lost;
	model.stage = STAGE_HS;
	model.domain = 1U;
	set_phase(PHASE_IPI_HS);
	model.domain = 0U;
}

/* Hart 0's phase @mode: its line, or its FAIL. */
static void run_phase(be_u32 mode)
{
	model.mode = mode;
	if (setjmp(model.hart0) == 0)
		ipis(model.mode, model.mode == 0U ? PHASE_IPI_HS : PHASE_IPI_VS,
		     model.mode == 0U ? PHASE_IPI_HS_DONE : PHASE_IPI_VS_DONE);
}

/*
 * The race M9-3 found: the domain hart's FID_IPI_VS call, whose handler
 * restarts the V=1 count, comes @delay of hart 0's calls after
 * PHASE_IPI_HS_DONE, the domain hart taking up to @burst steps at each.
 * Hart 0's HS line must say delivered=100 wherever the call falls.
 */
static void test_schedules(void)
{
	be_u64 before = 0U;
	be_u64 after = 0U;
	be_u64 in_send = 0U;
	be_u64 burst;
	be_u64 delay;

	for (burst = 1U; burst <= BURSTS; ++burst) {
		for (delay = 0U; delay < DELAYS; ++delay) {
			SCENARIO();
			start(delay, burst, NEVER);
			run_phase(0U);
			CHECK_RUN(model.lines == 1U);
			CHECK_RUN(model.values[0][1] == BE_MVP_PROBE_IPIS);
			CHECK_RUN(line_is(&model.line[0], line_hs));
			CHECK_RUN(model.failed == 0U);
			run_phase(1U);
			CHECK_RUN(model.lines == 2U);
			CHECK_RUN(model.values[1][1] == BE_MVP_PROBE_IPIS);
			CHECK_RUN(line_is(&model.line[1], line_vs));
			CHECK_RUN(model.failed == 0U);
			CHECK_RUN(model.stage == STAGE_DONE);
			CHECK_RUN(probe.phase == PHASE_IPI_VS_DONE);
			CHECK_RUN(model.domain_failed == 0U);
			CHECK_RUN(model.unexpected == 0U);
			before += model.call_before_line;
			after += model.call_before_line == 0U;
			in_send += model.call_in_send;
		}
	}
	/* The call fell within the hundredth send, before the HS line, and
	 * after it. */
	CHECK(in_send != 0U);
	CHECK(before > in_send);
	CHECK(after != 0U);
}

/* An HS IPI lost: hart 0 stops at it, prints the count, and fails ipi. */
static void test_lost(void)
{
	SCENARIO();
	start(0U, 1U, LOST);
	run_phase(0U);
	CHECK_RUN(model.lines == 1U);
	CHECK_RUN(model.values[0][0] == LOST);
	CHECK_RUN(model.values[0][1] == LOST);
	CHECK_RUN(line_is(&model.line[0], line_lost));
	CHECK_RUN(model.failed == 1U);
	CHECK_RUN(model.failure == BE_MVP_CLASS_IPI);
	CHECK_RUN(model.stage == STAGE_HS);
	CHECK_RUN(model.unexpected == 0U);
}

int main(void)
{
	test_schedules();
	test_lost();
	printf("BE_MVP_PROBE_CHECK: PASS\n");
	printf("BE_MVP_PROBE_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_MVP_PROBE_CHECK: assertions=%lu\n", assertions);
	return 0;
}
