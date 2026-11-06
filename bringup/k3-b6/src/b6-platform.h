/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B6 privileged boundary: the VS-exit vector, the resume tail,
 *          the arm, timer, time, and fence.i helpers in b6-trap.S, and the C
 *          entry points that assembly calls.
 * Trust:   assembly owns every CSR access, the frame transfer, the fence.i,
 *          and the no-call resume tail; C sees only monitor-owned copies and
 *          never runs with guest-restored registers.
 * Scope:   B6 only (planning/k3-b6-plan.md). After the R3 reset: no hgatp
 *          write or fence but the accepted install function's, no vs* write
 *          but vstimecmp, no hvip injection, and no HS interrupt path.
 */

#ifndef BE_B6_PLATFORM_H
#define BE_B6_PLATFORM_H

#include "r3-platform.h"

#include "b6.h"
#include "b6-payload.h"

/**
 * be_b6_runtime_main - accepted R3 prelude, then the B6 root and guest entry
 * @hart_id: firmware a0 hart identifier
 * @firmware_pointer: firmware a1 value, recorded but never dereferenced
 */
void be_b6_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
	__attribute__((noreturn));

/**
 * be_b6_dispatch - service one VS exit the vector saved
 * @record: the management saved page, as the vector selected it
 *
 * This never returns: it resumes the guest through be_b6_arch_resume, shuts
 * down, or fails closed.
 */
void be_b6_dispatch(struct be_b6_exit *record) __attribute__((noreturn));

/**
 * be_b6_runtime_terminal - print BE_B6:FAIL, request SRST, and halt
 * @failure: terminal class
 */
void be_b6_runtime_terminal(enum be_b6_class failure)
	__attribute__((noreturn));

/**
 * be_b6_exit_terminal - fail closed on an exit that is not from V=1
 * @record: the saved record, for BE_B6:DETAIL
 */
void be_b6_exit_terminal(struct be_b6_exit *record) __attribute__((noreturn));

/**
 * be_b6_arch_arm_stce - write henvcfg = STCE only and read it back
 *
 * Return: the henvcfg readback.
 */
be_u64 be_b6_arch_arm_stce(void);

/**
 * be_b6_arch_arm_controls - arm the guest controls and read them back
 * @controls: readback output
 * @trusted_top: the management trusted-stack top, for sscratch
 *
 * Writes vstimecmp = ~0 and samples hip, then writes hedeleg = 0xb15d,
 * hideleg = VSTI, hcounteren = TM, and sscratch = @trusted_top, and clears
 * hstatus VTVM, VTW, and VTSR.
 */
void be_b6_arch_arm_controls(struct be_b6_controls *controls,
			     be_u64 trusted_top);

/**
 * be_b6_arch_set_timer - serve SBI TIME set_timer
 * @deadline: the guest's absolute deadline, written to vstimecmp
 */
void be_b6_arch_set_timer(be_u64 deadline);

/**
 * be_b6_arch_read_time - read the time CSR
 *
 * Return: the time CSR.
 */
be_u64 be_b6_arch_read_time(void);

/**
 * be_b6_arch_fence_i - order the placed guest bytes before guest fetches
 *
 * The image's one fence.i.
 */
void be_b6_arch_fence_i(void);

/**
 * be_b6_arch_resume - check the controls and enter or return to the guest
 * @record: the management saved page
 * @expected_hgatp: the installed B6 hgatp
 * @expected_hedeleg: the hedeleg readback checked at arming (WARL)
 *
 * Checks every guest control, the B6 hgatp, satp, stvec, sscratch, sie, and
 * sstatus, then sets SPP, restores sepc and every GPR from @record, and
 * executes one SRET. A failed check is terminal (resume). It writes no vs*
 * CSR, hgatp, or fence.
 */
void be_b6_arch_resume(struct be_b6_exit *record, be_u64 expected_hgatp,
		       be_u64 expected_hedeleg) __attribute__((noreturn));

extern be_u8 be_b6_trap_vector[];
extern be_u8 __be_b6_pool_start[];
extern be_u8 __be_b6_pool_end[];
extern const struct be_b6_payload_layout be_b6_payload_layout;

#endif
