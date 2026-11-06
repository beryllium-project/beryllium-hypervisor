/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B7 privileged boundary: the VS-exit vector, the resume tail,
 *          the arm, CSR save and load, timer, deadline, wait, time, and
 *          fence.i helpers in b7-trap.S, and the C entry points that
 *          assembly calls.
 * Trust:   assembly owns every CSR access, the frame transfer, the fence.i,
 *          the HS wfi, and the no-call resume tail; C sees only monitor-owned
 *          copies and never runs with guest-restored registers.
 * Scope:   B7 only (planning/k3-b7-plan.md). After the R3 reset: no hgatp
 *          write or fence but the accepted install function's, no vs* write
 *          but the load helper's (and vstimecmp by the arm and TIME
 *          helpers), no stimecmp write but the deadline helper's, no hvip
 *          injection, and no HS interrupt but the supervisor timer at V=1.
 */

#ifndef BE_B7_PLATFORM_H
#define BE_B7_PLATFORM_H

#include "r3-platform.h"

#include "b7.h"
#include "b7-payload.h"

/**
 * be_b7_runtime_main - accepted R3 prelude, then both roots and the run
 * @hart_id: firmware a0 hart identifier
 * @firmware_pointer: firmware a1 value, recorded but never dereferenced
 */
void be_b7_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
	__attribute__((noreturn));

/**
 * be_b7_dispatch - service one VS exit the vector saved
 * @record: the management saved page, as the vector selected it
 *
 * This never returns: it resumes a guest through be_b7_arch_resume,
 * finishes the run, or fails closed.
 */
void be_b7_dispatch(struct be_b7_exit *record) __attribute__((noreturn));

/**
 * be_b7_runtime_terminal - print BE_B7:FAIL, request SRST, and halt
 * @failure: terminal class
 */
void be_b7_runtime_terminal(enum be_b7_class failure)
	__attribute__((noreturn));

/**
 * be_b7_exit_terminal - fail closed on an exit that is not from V=1
 * @record: the saved record, for BE_B7:DETAIL
 */
void be_b7_exit_terminal(struct be_b7_exit *record) __attribute__((noreturn));

/**
 * be_b7_arch_arm_stce - write henvcfg = STCE only and read it back
 *
 * Return: the henvcfg readback.
 */
be_u64 be_b7_arch_arm_stce(void);

/**
 * be_b7_arch_arm_controls - arm the guest controls and read them back
 * @controls: readback output
 * @trusted_top: the management trusted-stack top, for sscratch
 *
 * Writes vstimecmp = ~0 and samples hip, then writes hedeleg = 0xb15d,
 * hideleg = VSTI, hcounteren = TM, and sscratch = @trusted_top, clears
 * hstatus VTVM and VTSR, sets hstatus VTW, and sets sie.STIE.
 */
void be_b7_arch_arm_controls(struct be_b7_controls *controls,
			     be_u64 trusted_top);

/**
 * be_b7_arch_save_vcsr - read the running guest's per-guest CSR set
 * @csr: %BE_B7_VCSR_COUNT words, in &enum be_b7_vcsr order
 */
void be_b7_arch_save_vcsr(be_u64 *csr);

/**
 * be_b7_arch_load_vcsr - write a guest's CSR set and read it all back
 * @csr: %BE_B7_VCSR_COUNT words to write
 * @readback: %BE_B7_VCSR_COUNT words read back after every write
 */
void be_b7_arch_load_vcsr(const be_u64 *csr, be_u64 *readback);

/**
 * be_b7_arch_set_timer - serve SBI TIME set_timer
 * @deadline: the guest's absolute deadline, written to vstimecmp
 */
void be_b7_arch_set_timer(be_u64 deadline);

/**
 * be_b7_arch_set_deadline - program the HS supervisor timer
 * @deadline: the absolute time written to stimecmp
 */
void be_b7_arch_set_deadline(be_u64 deadline);

/**
 * be_b7_arch_wait - wait in HS until a time, the deadline set to it
 * @target: the time to wait until
 *
 * Return: the time at the end of the wait, at least @target.
 */
be_u64 be_b7_arch_wait(be_u64 target);

/**
 * be_b7_arch_read_time - read the time CSR
 *
 * Return: the time CSR.
 */
be_u64 be_b7_arch_read_time(void);

/**
 * be_b7_arch_fence_i - order the placed guest bytes before guest fetches
 *
 * The image's one fence.i.
 */
void be_b7_arch_fence_i(void);

/**
 * be_b7_arch_resume - check the controls and enter or return to a guest
 * @record: the management saved page
 * @expected_hgatp: the running guest's installed hgatp
 * @expected_hedeleg: the hedeleg readback checked at arming (WARL)
 *
 * Checks every guest control, @expected_hgatp, satp, stvec, sscratch, sie,
 * and sstatus, sets SPP from the record's saved SPVP, restores sepc and
 * every GPR from @record, and executes one SRET. A failed check is
 * terminal (resume). It writes no vs* CSR, hgatp, or fence.
 */
void be_b7_arch_resume(struct be_b7_exit *record, be_u64 expected_hgatp,
		       be_u64 expected_hedeleg) __attribute__((noreturn));

extern be_u8 be_b7_trap_vector[];
extern be_u8 __be_b7_pool_start[];
extern be_u8 __be_b7_pool_end[];
extern const struct be_b7_payload_layout be_b7_payload_layout;

#endif
