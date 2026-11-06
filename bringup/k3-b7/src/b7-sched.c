// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B7 scheduler state machine: guest states, events, the
 *          next-guest choice, the HS deadline, the both-idle wait target,
 *          and the run's time-budget guard.
 * Trust:   restricted C with no loop, CSR, SBI call, or I/O; saturating
 *          time arithmetic; invalid input fails closed and stays failed.
 * Scope:   B7 only (planning/k3-b7-plan.md); see b7-sched.h.
 */
#include "b7-sched.h"

#define ALL_ONES		(~BE_U64_C(0))

_Static_assert(BE_B7_GUESTS == 2U, "the scheduler alternates two guests");

static be_u32 other_guest(be_u32 guest)
{
	return guest ^ 1U;
}

static be_u64 add_saturating(be_u64 value, be_u64 addend)
{
	return value > ALL_ONES - addend ? ALL_ONES : value + addend;
}

static int state_valid(enum be_b7_guest_state state)
{
	return state == BE_B7_GUEST_RUNNABLE || state == BE_B7_GUEST_IDLE ||
	       state == BE_B7_GUEST_STOPPED;
}

static int event_valid(enum be_b7_event event)
{
	return event == BE_B7_EVENT_NONE || event == BE_B7_EVENT_WFI ||
	       event == BE_B7_EVENT_SLICE || event == BE_B7_EVENT_STOP;
}

/* Every field in range, and no earlier failure. */
static int sound(const struct be_b7_sched *sched)
{
	return sched->failed == 0U && sched->current < BE_B7_GUESTS &&
	       state_valid(sched->state[0]) && state_valid(sched->state[1]) &&
	       event_valid(sched->reason) && sched->slice != 0U &&
	       sched->budget != 0U;
}

/* Runnable, or idle with its wake time come. */
static int ready(const struct be_b7_sched *sched, be_u32 guest, be_u64 now)
{
	return sched->state[guest] == BE_B7_GUEST_RUNNABLE ||
	       (sched->state[guest] == BE_B7_GUEST_IDLE &&
		sched->wake[guest] <= now);
}

static enum be_b7_next invalid(struct be_b7_sched *sched)
{
	sched->failed = 1U;
	return BE_B7_NEXT_INVALID;
}

/* The earlier of now + slice and the other guest's wake time, if idle. */
static be_u64 deadline(const struct be_b7_sched *sched, be_u32 guest,
		       be_u64 now)
{
	be_u32 other = other_guest(guest);
	be_u64 value = add_saturating(now, sched->slice);

	if (sched->state[other] == BE_B7_GUEST_IDLE &&
	    sched->wake[other] < value)
		value = sched->wake[other];
	return value;
}

void be_b7_sched_init(struct be_b7_sched *sched, be_u64 slice, be_u64 budget)
{
	if (sched == (struct be_b7_sched *)0)
		return;
	*sched = (struct be_b7_sched){
		.state = { BE_B7_GUEST_RUNNABLE, BE_B7_GUEST_RUNNABLE },
		.reason = BE_B7_EVENT_NONE,
		.slice = slice,
		.budget = budget,
	};
	if (slice == 0U || budget == 0U)
		sched->failed = 1U;
}

enum be_b7_next be_b7_sched_start(struct be_b7_sched *sched, be_u64 now,
				  struct be_b7_decision *decision)
{
	if (decision == (struct be_b7_decision *)0) {
		if (sched != (struct be_b7_sched *)0)
			sched->failed = 1U;
		return BE_B7_NEXT_INVALID;
	}
	*decision = (struct be_b7_decision){ BE_B7_NEXT_INVALID, 0U, 0U, 0U };
	if (sched == (struct be_b7_sched *)0)
		return BE_B7_NEXT_INVALID;
	if (!sound(sched) || sched->started != 0U || sched->current != 0U ||
	    sched->reason != BE_B7_EVENT_NONE ||
	    sched->state[0] != BE_B7_GUEST_RUNNABLE ||
	    sched->state[1] != BE_B7_GUEST_RUNNABLE)
		return invalid(sched);
	sched->started = 1U;
	sched->start = now;
	sched->deadline = deadline(sched, 0U, now);
	decision->next = BE_B7_NEXT_RUN;
	decision->deadline = sched->deadline;
	return BE_B7_NEXT_RUN;
}

int be_b7_sched_event(struct be_b7_sched *sched, enum be_b7_event event,
		      be_u64 wake)
{
	be_u32 guest;

	if (sched == (struct be_b7_sched *)0)
		return 0;
	if (!sound(sched) || sched->started == 0U ||
	    sched->reason != BE_B7_EVENT_NONE || !event_valid(event) ||
	    sched->state[sched->current] != BE_B7_GUEST_RUNNABLE) {
		sched->failed = 1U;
		return 0;
	}
	guest = sched->current;
	if (event == BE_B7_EVENT_WFI) {
		sched->state[guest] = BE_B7_GUEST_IDLE;
		sched->wake[guest] = wake;
	} else if (event == BE_B7_EVENT_STOP) {
		sched->state[guest] = BE_B7_GUEST_STOPPED;
	}
	sched->reason = event;
	return 1;
}

enum be_b7_next be_b7_sched_next(struct be_b7_sched *sched, be_u64 now,
				 struct be_b7_decision *decision)
{
	be_u32 current;
	be_u32 other;
	be_u32 guest;
	be_u64 target;

	if (decision == (struct be_b7_decision *)0) {
		if (sched != (struct be_b7_sched *)0)
			sched->failed = 1U;
		return BE_B7_NEXT_INVALID;
	}
	*decision = (struct be_b7_decision){ BE_B7_NEXT_INVALID, 0U, 0U, 0U };
	if (sched == (struct be_b7_sched *)0)
		return BE_B7_NEXT_INVALID;
	if (!sound(sched) || sched->started == 0U ||
	    sched->reason == BE_B7_EVENT_NONE)
		return invalid(sched);
	current = sched->current;
	other = other_guest(current);
	if (sched->state[0] == BE_B7_GUEST_STOPPED &&
	    sched->state[1] == BE_B7_GUEST_STOPPED) {
		decision->next = BE_B7_NEXT_DONE;
		return BE_B7_NEXT_DONE;
	}
	/* A time before the start wraps above the budget: fail closed. */
	if (now - sched->start >= sched->budget) {
		decision->next = BE_B7_NEXT_TIMEOUT;
		return BE_B7_NEXT_TIMEOUT;
	}
	if (ready(sched, other, now)) {
		guest = other;
	} else if (ready(sched, current, now)) {
		guest = current;
	} else {
		/* No guest is ready, so at least one is idle until the future. */
		target = add_saturating(sched->start, sched->budget);
		if (sched->state[current] == BE_B7_GUEST_IDLE &&
		    sched->wake[current] < target)
			target = sched->wake[current];
		if (sched->state[other] == BE_B7_GUEST_IDLE &&
		    sched->wake[other] < target)
			target = sched->wake[other];
		decision->next = BE_B7_NEXT_WAIT;
		decision->deadline = target;
		return BE_B7_NEXT_WAIT;
	}
	sched->state[guest] = BE_B7_GUEST_RUNNABLE;
	if (guest != current) {
		++sched->switches;
		if (sched->reason == BE_B7_EVENT_WFI)
			++sched->wfi_switches;
		else if (sched->reason == BE_B7_EVENT_SLICE)
			++sched->slice_switches;
		else
			++sched->stop_switches;
		sched->current = guest;
		decision->switched = 1U;
	}
	sched->reason = BE_B7_EVENT_NONE;
	sched->deadline = deadline(sched, guest, now);
	decision->next = BE_B7_NEXT_RUN;
	decision->guest = guest;
	decision->deadline = sched->deadline;
	return BE_B7_NEXT_RUN;
}

void be_b7_sched_waited(struct be_b7_sched *sched, be_u64 ticks)
{
	if (sched == (struct be_b7_sched *)0)
		return;
	sched->idle_waits = add_saturating(sched->idle_waits, 1U);
	sched->idle_ticks = add_saturating(sched->idle_ticks, ticks);
}
