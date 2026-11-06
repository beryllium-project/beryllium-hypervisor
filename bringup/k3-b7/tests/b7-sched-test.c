// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the K3 B7 scheduler: initialization and the
 *          first entry; every guest state with every event; round-robin
 *          order; the HS deadline as the earlier of now + slice and the
 *          other guest's wake time; the both-idle wait and its target;
 *          waits and decisions bounded by the run's time budget; the done
 *          state; switch counts by cause; saturating time arithmetic;
 *          invalid input, which fails closed and stays failed; and long
 *          pseudo-random runs checked step by step against an independent
 *          reference model of the plan's rules.
 * Trust:   host evidence only. No CSR, timer, wfi, switch, QEMU, or
 *          hardware behaviour is exercised.
 * Scope:   B7 only (planning/k3-b7-plan.md, "Scheduler").
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "b7-sched.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_B7_SCHED_CHECK: assertion failed: %s:%d: %s\n", \
			       __FILE__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define SLICE			BE_U64_C(240000)
#define BUDGET			BE_U64_C(0x100000000)
#define START			BE_U64_C(0x1000000)
#define ALL_ONES		(~BE_U64_C(0))
#define RUNNABLE		BE_B7_GUEST_RUNNABLE
#define IDLE			BE_B7_GUEST_IDLE
#define STOPPED			BE_B7_GUEST_STOPPED

static struct be_b7_sched sched;
static struct be_b7_decision decision;

/* A started scheduler: G0 running since START with the first deadline. */
static void started(void)
{
	be_b7_sched_init(&sched, SLICE, BUDGET);
	CHECK(be_b7_sched_start(&sched, START, &decision) == BE_B7_NEXT_RUN);
	CHECK(decision.guest == 0U && decision.switched == 0U);
	CHECK(decision.deadline == START + SLICE);
}

static int counts_zero(void)
{
	return sched.switches == 0U && sched.wfi_switches == 0U &&
	       sched.slice_switches == 0U && sched.stop_switches == 0U &&
	       sched.idle_waits == 0U && sched.idle_ticks == 0U;
}

static int counts_sum(void)
{
	return sched.switches == sched.wfi_switches + sched.slice_switches +
				 sched.stop_switches;
}

static void expect_run(be_u64 now, be_u32 guest, be_u32 switched,
		       be_u64 deadline)
{
	CHECK(be_b7_sched_next(&sched, now, &decision) == BE_B7_NEXT_RUN);
	CHECK(decision.next == BE_B7_NEXT_RUN);
	CHECK(decision.guest == guest && decision.switched == switched);
	CHECK(decision.deadline == deadline && sched.deadline == deadline);
	CHECK(sched.current == guest && sched.state[guest] == RUNNABLE);
	CHECK(sched.reason == BE_B7_EVENT_NONE && sched.failed == 0U);
	CHECK(counts_sum());
}

static void expect_invalid(void)
{
	CHECK(sched.failed != 0U);
	CHECK(be_b7_sched_next(&sched, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	CHECK(decision.next == BE_B7_NEXT_INVALID);
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 0);
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(BE_B7_SLICE_TICKS == SLICE);
	CHECK(BE_B7_SLICE_TICKS == 0x3a980U);
	CHECK(BE_B7_GUEST_TIME_BUDGET == BUDGET);
	CHECK(BE_B7_VARIANT_GUEST_TIME_BUDGET == BE_U64_C(0x100000));
	CHECK(BE_B7_TIMEBASE_HZ == 24000000U);
	CHECK(BE_B7_GUESTS == 2U);
	CHECK(BE_B7_GUEST_RUNNABLE == 0 && BE_B7_EVENT_NONE == 0 &&
	      BE_B7_NEXT_INVALID == 0);
}

static void test_init_start(void)
{
	SCENARIO();
	memset(&sched, 0x5a, sizeof(sched));
	be_b7_sched_init(&sched, SLICE, BUDGET);
	CHECK(sched.state[0] == RUNNABLE && sched.state[1] == RUNNABLE);
	CHECK(sched.current == 0U && sched.failed == 0U && sched.started == 0U);
	CHECK(sched.reason == BE_B7_EVENT_NONE);
	CHECK(sched.slice == SLICE && sched.budget == BUDGET);
	CHECK(sched.wake[0] == 0U && sched.wake[1] == 0U);
	CHECK(sched.deadline == 0U && sched.start == 0U && counts_zero());
	/* No event or decision before the first entry. */
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 0);
	CHECK(sched.failed != 0U);
	be_b7_sched_init(&sched, SLICE, BUDGET);
	CHECK(be_b7_sched_next(&sched, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	CHECK(sched.failed != 0U);
	/* The first entry: G0, no switch, deadline now + slice. */
	started();
	CHECK(sched.started != 0U && sched.start == START);
	CHECK(sched.deadline == START + SLICE && counts_zero());
	/* Only once. */
	CHECK(be_b7_sched_start(&sched, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	CHECK(decision.next == BE_B7_NEXT_INVALID);
	expect_invalid();
	/* A zero slice or budget, and absent arguments. */
	be_b7_sched_init(&sched, 0U, BUDGET);
	CHECK(sched.failed != 0U);
	CHECK(be_b7_sched_start(&sched, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	be_b7_sched_init(&sched, SLICE, 0U);
	CHECK(sched.failed != 0U);
	CHECK(be_b7_sched_start(&sched, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	be_b7_sched_init((struct be_b7_sched *)0, SLICE, BUDGET);
	be_b7_sched_init(&sched, SLICE, BUDGET);
	CHECK(be_b7_sched_start(&sched, START, (struct be_b7_decision *)0) ==
	      BE_B7_NEXT_INVALID);
	CHECK(sched.failed != 0U);
	CHECK(be_b7_sched_start((struct be_b7_sched *)0, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	CHECK(decision.next == BE_B7_NEXT_INVALID);
}

/* Each event from a runnable guest, and every event from a parked one. */
static void test_events(void)
{
	static const enum be_b7_event events[] = {
		BE_B7_EVENT_NONE, BE_B7_EVENT_WFI, BE_B7_EVENT_SLICE,
		BE_B7_EVENT_STOP,
	};
	be_size index;

	SCENARIO();
	/* NONE: an SBI call; nothing changes and no decision is due. */
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_NONE, 0x1234U) == 1);
	CHECK(sched.state[0] == RUNNABLE && sched.wake[0] == 0U);
	CHECK(sched.reason == BE_B7_EVENT_NONE && sched.failed == 0U);
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_NONE, 0U) == 1);
	/* A decision with no pending event is invalid. */
	CHECK(be_b7_sched_next(&sched, START + 1U, &decision) ==
	      BE_B7_NEXT_INVALID);
	expect_invalid();
	/* WFI parks the guest with its wake time. */
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, START + 77U) == 1);
	CHECK(sched.state[0] == IDLE && sched.wake[0] == START + 77U);
	CHECK(sched.reason == BE_B7_EVENT_WFI);
	/* A second event before the decision is invalid. */
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 0);
	expect_invalid();
	/* SLICE leaves the guest runnable. */
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 99U) == 1);
	CHECK(sched.state[0] == RUNNABLE && sched.wake[0] == 0U);
	CHECK(sched.reason == BE_B7_EVENT_SLICE);
	/* STOP stops it. */
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_STOP, 99U) == 1);
	CHECK(sched.state[0] == STOPPED && sched.reason == BE_B7_EVENT_STOP);
	/* No event from a guest that is not runnable. */
	for (index = 0U; index < BE_ARRAY_SIZE(events); ++index) {
		started();
		sched.state[0] = IDLE;
		CHECK(be_b7_sched_event(&sched, events[index], 0U) == 0);
		expect_invalid();
		started();
		sched.state[0] = STOPPED;
		CHECK(be_b7_sched_event(&sched, events[index], 0U) == 0);
		expect_invalid();
	}
	/* Unknown events. */
	started();
	CHECK(be_b7_sched_event(&sched, (enum be_b7_event)4, 0U) == 0);
	expect_invalid();
	started();
	CHECK(be_b7_sched_event(&sched, (enum be_b7_event)-1, 0U) == 0);
	expect_invalid();
	CHECK(be_b7_sched_event((struct be_b7_sched *)0, BE_B7_EVENT_WFI,
				0U) == 0);
}

/* Round-robin: the other guest whenever it is ready. */
static void test_round_robin(void)
{
	be_u64 now = START;
	be_u32 expected = 0U;
	unsigned int step;

	SCENARIO();
	started();
	for (step = 0U; step < 64U; ++step) {
		now += SLICE;
		CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
		expected ^= 1U;
		expect_run(now, expected, 1U, now + SLICE);
	}
	CHECK(sched.switches == 64U && sched.slice_switches == 64U);
	CHECK(sched.wfi_switches == 0U && sched.stop_switches == 0U);
	/* A WFI hands over to a runnable other guest at once. */
	now += 5U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, now + 1000U) == 1);
	expect_run(now, 1U, 1U, now + 1000U);
	CHECK(sched.state[0] == IDLE && sched.wfi_switches == 1U);
	CHECK(sched.switches == 65U);
}

/* The deadline: the earlier of now + slice and an idle other's wake. */
static void test_deadline(void)
{
	be_u64 now = START + 1000U;

	SCENARIO();
	/* Other idle, wake before the slice ends: the wake time. */
	started();
	sched.state[1] = IDLE;
	sched.wake[1] = now + SLICE - 1U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(now, 0U, 0U, now + SLICE - 1U);
	/* Wake exactly at the slice's end: either way the same value. */
	sched.wake[1] = now + SLICE;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(now, 0U, 0U, now + SLICE);
	/* Wake after the slice's end: the slice. */
	sched.wake[1] = now + SLICE + 1U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(now, 0U, 0U, now + SLICE);
	/* Wake one tick ahead: the next tick. */
	sched.wake[1] = now + 1U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(now, 0U, 0U, now + 1U);
	/* Wake never (vstimecmp ~0): the slice. */
	sched.wake[1] = ALL_ONES;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(now, 0U, 0U, now + SLICE);
	CHECK(sched.switches == 0U);
	/* The idle other's wake time comes: the slice hands over. */
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	sched.wake[1] = now + 10U;
	expect_run(now + 10U, 1U, 1U, now + 10U + SLICE);
	CHECK(sched.slice_switches == 1U);
	/* Other stopped: the slice. */
	started();
	sched.state[1] = STOPPED;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(now, 0U, 0U, now + SLICE);
	/* Other runnable: the slice, and a switch. */
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(now, 1U, 1U, now + SLICE);
}

/* Both idle: wait for the earliest wake, then run its guest. */
static void test_wait(void)
{
	be_u64 now = START + 500U;

	SCENARIO();
	/* G0 idles until +300; G1 is idle until +200: wait until +200. */
	started();
	sched.state[1] = IDLE;
	sched.wake[1] = now + 200U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, now + 300U) == 1);
	CHECK(be_b7_sched_next(&sched, now, &decision) == BE_B7_NEXT_WAIT);
	CHECK(decision.next == BE_B7_NEXT_WAIT &&
	      decision.deadline == now + 200U);
	/* The reason survives the wait; the scheduler did not change. */
	CHECK(sched.reason == BE_B7_EVENT_WFI && sched.current == 0U);
	CHECK(sched.state[0] == IDLE && sched.state[1] == IDLE);
	be_b7_sched_waited(&sched, 200U);
	CHECK(sched.idle_waits == 1U && sched.idle_ticks == 200U);
	/* An early wake decides to wait again, for the same target. */
	CHECK(be_b7_sched_next(&sched, now + 199U, &decision) ==
	      BE_B7_NEXT_WAIT);
	CHECK(decision.deadline == now + 200U);
	/* G1's wake comes: switch, counted as a wfi switch; the deadline is
	 * G0's wake, before the slice ends. */
	expect_run(now + 200U, 1U, 1U, now + 300U);
	CHECK(sched.wfi_switches == 1U && sched.switches == 1U);
	CHECK(sched.state[0] == IDLE && sched.wake[0] == now + 300U);
	/* G0's own wake first: wait, then resume G0 with no switch. */
	started();
	sched.state[1] = IDLE;
	sched.wake[1] = now + 900U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, now + 100U) == 1);
	CHECK(be_b7_sched_next(&sched, now, &decision) == BE_B7_NEXT_WAIT);
	CHECK(decision.deadline == now + 100U);
	expect_run(now + 100U, 0U, 0U, now + 900U);
	CHECK(sched.switches == 0U);
	/* Both wakes come at once: the other guest first. */
	started();
	sched.state[1] = IDLE;
	sched.wake[1] = now + 50U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, now + 50U) == 1);
	CHECK(be_b7_sched_next(&sched, now, &decision) == BE_B7_NEXT_WAIT);
	CHECK(decision.deadline == now + 50U);
	expect_run(now + 50U, 1U, 1U, now + 50U);
	/* A wfi whose wake already passed, with the other guest runnable:
	 * the other guest runs, with the due wake as its deadline, so the
	 * HS timer hands the hart straight back. */
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, now - 1U) == 1);
	expect_run(now, 1U, 1U, now - 1U);
	CHECK(sched.state[0] == IDLE);
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(now + 1U, 0U, 1U, now + 1U + SLICE);
	CHECK(sched.wfi_switches == 1U && sched.slice_switches == 1U);
	/* A wfi whose wake already passed: the guest stays ready. */
	started();
	sched.state[1] = IDLE;
	sched.wake[1] = now + 5000U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, now - 1U) == 1);
	expect_run(now, 0U, 0U, now + 5000U);
	/* One guest stopped, the other idle: wait for it, then a stop switch. */
	started();
	sched.state[1] = IDLE;
	sched.wake[1] = now + 4000U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_STOP, 0U) == 1);
	CHECK(be_b7_sched_next(&sched, now, &decision) == BE_B7_NEXT_WAIT);
	CHECK(decision.deadline == now + 4000U);
	expect_run(now + 4000U, 1U, 1U, now + 4000U + SLICE);
	CHECK(sched.stop_switches == 1U && sched.switches == 1U);
	/* The last guest idles alone: wait for itself, no switch. */
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, now + 4100U) == 1);
	CHECK(be_b7_sched_next(&sched, now + 4001U, &decision) ==
	      BE_B7_NEXT_WAIT);
	CHECK(decision.deadline == now + 4100U);
	expect_run(now + 4100U, 1U, 0U, now + 4100U + SLICE);
}

/* Shutdowns: one stop switch, then done when both have stopped. */
static void test_stop_done(void)
{
	be_u64 now = START + 7U;

	SCENARIO();
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_STOP, 0U) == 1);
	expect_run(now, 1U, 1U, now + SLICE);
	CHECK(sched.stop_switches == 1U && sched.state[0] == STOPPED);
	/* The last guest's slices never switch. */
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(now + SLICE, 1U, 0U, now + 2U * SLICE);
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_STOP, 0U) == 1);
	CHECK(be_b7_sched_next(&sched, now + 3U * SLICE, &decision) ==
	      BE_B7_NEXT_DONE);
	CHECK(decision.next == BE_B7_NEXT_DONE);
	CHECK(sched.switches == 1U && sched.stop_switches == 1U);
	/* Done is final, even after the budget. */
	CHECK(be_b7_sched_next(&sched, START + BUDGET + 1U, &decision) ==
	      BE_B7_NEXT_DONE);
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 0);
}

/* The run's time budget bounds decisions and waits. */
static void test_budget(void)
{
	be_u64 end = START + BUDGET;

	SCENARIO();
	/* One tick before the end runs; at the end it times out. */
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(end - 1U, 1U, 1U, end - 1U + SLICE);
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	CHECK(be_b7_sched_next(&sched, end, &decision) == BE_B7_NEXT_TIMEOUT);
	CHECK(decision.next == BE_B7_NEXT_TIMEOUT);
	CHECK(be_b7_sched_next(&sched, ALL_ONES, &decision) ==
	      BE_B7_NEXT_TIMEOUT);
	/* A time before the start wraps above the budget. */
	CHECK(be_b7_sched_next(&sched, START - 1U, &decision) ==
	      BE_B7_NEXT_TIMEOUT);
	/* A wait never runs past the end of the budget. */
	started();
	sched.state[1] = IDLE;
	sched.wake[1] = ALL_ONES;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, end + 5U) == 1);
	CHECK(be_b7_sched_next(&sched, end - 100U, &decision) ==
	      BE_B7_NEXT_WAIT);
	CHECK(decision.deadline == end);
	CHECK(be_b7_sched_next(&sched, end, &decision) == BE_B7_NEXT_TIMEOUT);
	/* A wake before the end is the target. */
	started();
	sched.state[1] = IDLE;
	sched.wake[1] = end - 1U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, ALL_ONES) == 1);
	CHECK(be_b7_sched_next(&sched, end - 100U, &decision) ==
	      BE_B7_NEXT_WAIT);
	CHECK(decision.deadline == end - 1U);
	/* A small budget, as in the guest-timeout variant. */
	be_b7_sched_init(&sched, SLICE, BE_B7_VARIANT_GUEST_TIME_BUDGET);
	CHECK(be_b7_sched_start(&sched, START, &decision) == BE_B7_NEXT_RUN);
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	CHECK(be_b7_sched_next(&sched, START + 0x100000U, &decision) ==
	      BE_B7_NEXT_TIMEOUT);
}

/* Saturating arithmetic near the top of the time range. */
static void test_saturation(void)
{
	SCENARIO();
	be_b7_sched_init(&sched, SLICE, ALL_ONES);
	CHECK(be_b7_sched_start(&sched, ALL_ONES - 10U, &decision) ==
	      BE_B7_NEXT_RUN);
	CHECK(decision.deadline == ALL_ONES);
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	expect_run(ALL_ONES - 5U, 1U, 1U, ALL_ONES);
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, ALL_ONES) == 1);
	expect_run(ALL_ONES - 5U, 0U, 1U, ALL_ONES);
	/* Both idle forever: the wait target saturates at the budget end. */
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_WFI, ALL_ONES) == 1);
	CHECK(be_b7_sched_next(&sched, ALL_ONES - 4U, &decision) ==
	      BE_B7_NEXT_WAIT);
	CHECK(decision.deadline == ALL_ONES);
	/* The idle counters saturate. */
	be_b7_sched_waited(&sched, ALL_ONES - 1U);
	be_b7_sched_waited(&sched, 5U);
	CHECK(sched.idle_ticks == ALL_ONES && sched.idle_waits == 2U);
	sched.idle_waits = ALL_ONES;
	be_b7_sched_waited(&sched, 0U);
	CHECK(sched.idle_waits == ALL_ONES);
	be_b7_sched_waited((struct be_b7_sched *)0, 5U);
}

/* Corrupt state fails closed, and stays failed. */
static void test_invalid(void)
{
	SCENARIO();
	started();
	sched.current = 2U;
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 0);
	expect_invalid();
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	sched.state[1] = (enum be_b7_guest_state)3;
	CHECK(be_b7_sched_next(&sched, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	expect_invalid();
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	sched.reason = (enum be_b7_event)9;
	CHECK(be_b7_sched_next(&sched, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	expect_invalid();
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	sched.slice = 0U;
	CHECK(be_b7_sched_next(&sched, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	expect_invalid();
	/* Failed is sticky: repairing the fields does not clear it. */
	sched.slice = SLICE;
	sched.reason = BE_B7_EVENT_SLICE;
	CHECK(be_b7_sched_next(&sched, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	/* Absent arguments. */
	started();
	CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_SLICE, 0U) == 1);
	CHECK(be_b7_sched_next(&sched, START, (struct be_b7_decision *)0) ==
	      BE_B7_NEXT_INVALID);
	CHECK(sched.failed != 0U);
	CHECK(be_b7_sched_next((struct be_b7_sched *)0, START, &decision) ==
	      BE_B7_NEXT_INVALID);
	CHECK(decision.next == BE_B7_NEXT_INVALID);
}

/*
 * An independent reference model of the plan's rules, written from the
 * plan's text rather than from b7-sched.c, and a deterministic generator.
 */
struct model {
	int state[2];
	be_u64 wake[2];
	be_u32 current;
	int reason;
	be_u64 start;
	be_u64 switches[4];
};

static be_u64 random_state = BE_U64_C(0x9e3779b97f4a7c15);

static be_u64 next_random(void)
{
	random_state ^= random_state << 13;
	random_state ^= random_state >> 7;
	random_state ^= random_state << 17;
	return random_state;
}

static int model_ready(const struct model *m, be_u32 guest, be_u64 now)
{
	return m->state[guest] == RUNNABLE ||
	       (m->state[guest] == IDLE && m->wake[guest] <= now);
}

static void check_against_model(struct model *m, be_u64 now)
{
	enum be_b7_next got = be_b7_sched_next(&sched, now, &decision);
	be_u32 other = m->current ^ 1U;
	be_u32 guest;
	be_u64 target;
	be_u64 deadline;

	if (m->state[0] == STOPPED && m->state[1] == STOPPED) {
		CHECK(got == BE_B7_NEXT_DONE);
		return;
	}
	if (now - m->start >= BUDGET) {
		CHECK(got == BE_B7_NEXT_TIMEOUT);
		return;
	}
	if (!model_ready(m, other, now) && !model_ready(m, m->current, now)) {
		target = m->start + BUDGET;
		for (guest = 0U; guest < 2U; ++guest)
			if (m->state[guest] == IDLE && m->wake[guest] < target)
				target = m->wake[guest];
		CHECK(got == BE_B7_NEXT_WAIT && decision.deadline == target);
		CHECK(target > now);
		return;
	}
	guest = model_ready(m, other, now) ? other : m->current;
	CHECK(got == BE_B7_NEXT_RUN && decision.guest == guest);
	CHECK(decision.switched == (guest != m->current ? 1U : 0U));
	if (guest != m->current)
		++m->switches[m->reason];
	m->state[guest] = RUNNABLE;
	m->current = guest;
	m->reason = BE_B7_EVENT_NONE;
	deadline = now + SLICE;
	if (m->state[guest ^ 1U] == IDLE && m->wake[guest ^ 1U] < deadline)
		deadline = m->wake[guest ^ 1U];
	/* An idle other guest whose wake time already passed (it idled
	 * with its timer due) makes the deadline due at once. */
	CHECK(decision.deadline == deadline);
	CHECK(sched.switches == m->switches[1] + m->switches[2] +
				m->switches[3]);
	CHECK(sched.wfi_switches == m->switches[BE_B7_EVENT_WFI]);
	CHECK(sched.slice_switches == m->switches[BE_B7_EVENT_SLICE]);
	CHECK(sched.stop_switches == m->switches[BE_B7_EVENT_STOP]);
}

/* One pseudo-random run: events, waits, and decisions, step by step. */
static void simulate(unsigned int steps, be_u64 seed)
{
	struct model m = { { RUNNABLE, RUNNABLE }, { 0U, 0U }, 0U,
			   BE_B7_EVENT_NONE, START, { 0U, 0U, 0U, 0U } };
	be_u64 now = START;
	unsigned int step;

	SCENARIO();
	random_state = seed;
	started();
	for (step = 0U; step < steps; ++step) {
		be_u64 roll = next_random() % 100U;
		be_u64 wake = now + 1U + next_random() % (3U * SLICE);
		int event;

		/* An SBI exit first, sometimes: no decision follows. */
		if (roll < 30U) {
			CHECK(be_b7_sched_event(&sched, BE_B7_EVENT_NONE,
						0U) == 1);
			now += next_random() % 1000U;
			continue;
		}
		if (roll < 70U) {
			event = BE_B7_EVENT_WFI;
		} else if (roll < 99U || step + 1U < steps / 2U) {
			event = BE_B7_EVENT_SLICE;
		} else {
			event = BE_B7_EVENT_STOP;
		}
		if (roll % 7U == 0U)
			wake = now - (next_random() % 100U);
		CHECK(be_b7_sched_event(&sched, (enum be_b7_event)event,
					wake) == 1);
		if (event == BE_B7_EVENT_WFI) {
			m.state[m.current] = IDLE;
			m.wake[m.current] = wake;
		} else if (event == BE_B7_EVENT_STOP) {
			m.state[m.current] = STOPPED;
		}
		m.reason = event;
		now += 1U + next_random() % 500U;
		for (;;) {
			check_against_model(&m, now);
			if (decision.next != BE_B7_NEXT_WAIT)
				break;
			be_b7_sched_waited(&sched, decision.deadline - now);
			now = decision.deadline + next_random() % 3U;
		}
		if (decision.next != BE_B7_NEXT_RUN)
			break;
		/* The guest runs until the deadline, or exits earlier. */
		if (decision.deadline > now)
			now += next_random() % (decision.deadline - now + 1U);
	}
	/* Each run covers every switch cause and waits, and ends done. */
	CHECK(decision.next == BE_B7_NEXT_DONE);
	CHECK(sched.wfi_switches != 0U && sched.slice_switches != 0U &&
	      sched.stop_switches == 1U && sched.idle_waits != 0U);
	CHECK(counts_sum());
}

static void test_simulation(void)
{
	static const be_u64 seeds[] = {
		BE_U64_C(0x1), BE_U64_C(0x5eed), BE_U64_C(0xb7b7b7b7),
		BE_U64_C(0x123456789abcdef), BE_U64_C(0xfeedfacecafebeef),
		BE_U64_C(0x2026100800000007),
	};
	be_size index;

	for (index = 0U; index < BE_ARRAY_SIZE(seeds); ++index)
		simulate(4000U, seeds[index]);
}

int main(void)
{
	test_constants();
	test_init_start();
	test_events();
	test_round_robin();
	test_deadline();
	test_wait();
	test_stop_done();
	test_budget();
	test_saturation();
	test_invalid();
	test_simulation();
	printf("BE_B7_SCHED_CHECK: PASS\n");
	printf("BE_B7_SCHED_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_B7_SCHED_CHECK: assertions=%lu\n", assertions);
	return 0;
}
