/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B7 scheduler: the state machine that time-shares hart 0
 *          between G0 and G1. Each guest is RUNNABLE, IDLE until a wake
 *          time (its saved vstimecmp), or STOPPED. One event per exit of
 *          the running guest (an idling wfi, an HS slice, or a shutdown)
 *          leads to the next decision: run the other guest if it is ready,
 *          else the same guest if it is ready, else wait in HS until the
 *          earliest wake time, or finish when both have stopped. A running
 *          guest's HS deadline is the earlier of now + slice and the other
 *          guest's wake time, if the other is idle. Every wait ends at the
 *          run's time budget at the latest, which then fails the run.
 * Trust:   restricted C with no loop, CSR, SBI call, or I/O: the runtime
 *          reads the time, programs the deadline, waits, and switches.
 *          Invalid input fails closed and stays failed.
 * Scope:   B7 only (planning/k3-b7-plan.md, "Scheduler" and "Timers and
 *          wfi"). It selects no scheduler design for Beryllium.
 */

#ifndef BE_B7_SCHED_H
#define BE_B7_SCHED_H

#include <be/types.h>

#include "b7-layout.h"

/**
 * enum be_b7_guest_state - one guest's scheduling state
 * @BE_B7_GUEST_RUNNABLE: ready to run at any time
 * @BE_B7_GUEST_IDLE: parked after a wfi until its wake time
 * @BE_B7_GUEST_STOPPED: shut down; never runs again
 */
enum be_b7_guest_state {
	BE_B7_GUEST_RUNNABLE = 0,
	BE_B7_GUEST_IDLE,
	BE_B7_GUEST_STOPPED,
};

/**
 * enum be_b7_event - what the running guest's exit means for scheduling
 * @BE_B7_EVENT_NONE: no event: an SBI call was served, and the same guest
 *                    resumes without a new decision
 * @BE_B7_EVENT_WFI: the guest idles in wfi until its wake time
 * @BE_B7_EVENT_SLICE: the HS timer fired: the slice ended, or the other
 *                     guest's wake time came
 * @BE_B7_EVENT_STOP: the guest shut down
 */
enum be_b7_event {
	BE_B7_EVENT_NONE = 0,
	BE_B7_EVENT_WFI,
	BE_B7_EVENT_SLICE,
	BE_B7_EVENT_STOP,
};

/**
 * enum be_b7_next - the scheduler's decision
 * @BE_B7_NEXT_INVALID: invalid input or state; the run must fail closed
 * @BE_B7_NEXT_RUN: run (resume or first-enter) the decision's guest
 * @BE_B7_NEXT_WAIT: no guest is ready: wait in HS until the decision's
 *                   deadline, then decide again
 * @BE_B7_NEXT_DONE: both guests have stopped
 * @BE_B7_NEXT_TIMEOUT: the run's time budget is spent
 */
enum be_b7_next {
	BE_B7_NEXT_INVALID = 0,
	BE_B7_NEXT_RUN,
	BE_B7_NEXT_WAIT,
	BE_B7_NEXT_DONE,
	BE_B7_NEXT_TIMEOUT,
};

/**
 * struct be_b7_sched - scheduler state
 * @state: each guest's state
 * @wake: each idle guest's wake time
 * @current: the guest that runs, or ran last
 * @failed: nonzero once invalid input was seen; sticky
 * @started: nonzero once G0's first entry was decided
 * @reason: the event a pending decision follows, consumed by a run
 * @slice: slice length in ticks
 * @start: the time of G0's first entry
 * @budget: ticks after @start that the run may last
 * @deadline: the current guest's HS deadline, rewritten before each resume
 * @switches: switches between the guests
 * @wfi_switches: switches that followed a wfi
 * @slice_switches: switches that followed a slice
 * @stop_switches: switches that followed a shutdown
 * @idle_waits: HS waits with both guests idle or stopped
 * @idle_ticks: ticks spent in those waits
 */
struct be_b7_sched {
	enum be_b7_guest_state state[BE_B7_GUESTS];
	be_u64 wake[BE_B7_GUESTS];
	be_u32 current;
	be_u32 failed;
	be_u32 started;
	enum be_b7_event reason;
	be_u64 slice;
	be_u64 start;
	be_u64 budget;
	be_u64 deadline;
	be_u64 switches;
	be_u64 wfi_switches;
	be_u64 slice_switches;
	be_u64 stop_switches;
	be_u64 idle_waits;
	be_u64 idle_ticks;
};

/**
 * struct be_b7_decision - one decision
 * @next: what the runtime must do
 * @guest: for %BE_B7_NEXT_RUN, the guest to run
 * @switched: for %BE_B7_NEXT_RUN, nonzero when @guest is not the guest that
 *            ran last, so the runtime must switch
 * @deadline: for %BE_B7_NEXT_RUN, the HS stimecmp value before the resume;
 *            for %BE_B7_NEXT_WAIT, the time the wait lasts until
 */
struct be_b7_decision {
	enum be_b7_next next;
	be_u32 guest;
	be_u32 switched;
	be_u64 deadline;
};

/**
 * be_b7_sched_init - both guests runnable, G0 current, nothing counted
 * @sched: scheduler state
 * @slice: slice length in ticks, nonzero
 * @budget: run time budget in ticks, nonzero
 *
 * A zero slice or budget leaves the scheduler failed.
 */
void be_b7_sched_init(struct be_b7_sched *sched, be_u64 slice,
		      be_u64 budget);

/**
 * be_b7_sched_start - decide G0's first entry
 * @sched: an initialized scheduler, not yet started
 * @now: the time just before G0's first entry, which starts the budget
 * @decision: run G0 with the deadline now + slice
 *
 * Return: %BE_B7_NEXT_RUN, or %BE_B7_NEXT_INVALID.
 */
enum be_b7_next be_b7_sched_start(struct be_b7_sched *sched, be_u64 now,
				  struct be_b7_decision *decision);

/**
 * be_b7_sched_event - apply the running guest's event
 * @sched: scheduler state
 * @event: the event; the running guest must be RUNNABLE
 * @wake: for %BE_B7_EVENT_WFI, the guest's wake time (its vstimecmp)
 *
 * WFI parks the guest until @wake, SLICE leaves it runnable, STOP stops
 * it, and NONE changes nothing. Each but NONE needs a decision next.
 *
 * Return: 1, or 0 for invalid input, which leaves the scheduler failed.
 */
int be_b7_sched_event(struct be_b7_sched *sched, enum be_b7_event event,
		      be_u64 wake);

/**
 * be_b7_sched_next - decide what runs next after an event or a wait
 * @sched: scheduler state with a pending event
 * @now: the current time
 * @decision: the decision
 *
 * DONE when both guests have stopped; TIMEOUT once @now is at least the
 * budget after the start; RUN the other guest when it is ready (runnable,
 * or idle with its wake time at or before @now), else the same guest when
 * it is ready; otherwise WAIT until the earliest wake time, but never past
 * the budget's end. A run sets the HS deadline and counts a switch by the
 * pending event; a run after an SBI call (no pending event) is invalid.
 *
 * Return: the decision's @next.
 */
enum be_b7_next be_b7_sched_next(struct be_b7_sched *sched, be_u64 now,
				 struct be_b7_decision *decision);

/**
 * be_b7_sched_waited - count one HS wait
 * @sched: scheduler state
 * @ticks: the wait's length; the total saturates
 */
void be_b7_sched_waited(struct be_b7_sched *sched, be_u64 ticks);

#endif
