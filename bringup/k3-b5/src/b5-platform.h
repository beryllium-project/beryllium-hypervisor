/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B5 privileged boundary: the VS-exit vector, the resume tail,
 *          and the arm and timer helpers in b5-trap.S, and the C entry
 *          points that assembly calls.
 * Trust:   assembly owns every CSR access, the frame transfer, and the
 *          no-call resume tail; C sees only monitor-owned copies and never
 *          runs with guest-restored registers.
 * Scope:   B5 only (planning/k3-b5-plan.md). No hgatp write, fence, vs*
 *          write, hvip injection, or HS interrupt path after the R3 reset.
 */

#ifndef BE_B5_PLATFORM_H
#define BE_B5_PLATFORM_H

#include "r3-platform.h"

#include "b5.h"

/**
 * be_b5_runtime_main - accepted R3 boot and first entry into the B5 guest
 * @hart_id: firmware a0 hart identifier
 * @firmware_pointer: firmware a1 value, recorded but never dereferenced
 */
void be_b5_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
	__attribute__((noreturn));

/**
 * be_b5_dispatch - service one VS exit the vector saved
 * @frame: the management saved page, as the vector selected it
 *
 * This never returns: it resumes the guest through be_b5_arch_resume, shuts
 * down, or fails closed.
 */
void be_b5_dispatch(struct be_r4_frame *frame) __attribute__((noreturn));

/**
 * be_b5_runtime_terminal - print BE_B5:FAIL, request SRST, and halt
 * @failure: terminal class
 */
void be_b5_runtime_terminal(enum be_b5_class failure)
	__attribute__((noreturn));

/**
 * be_b5_exit_terminal - fail closed on an exit that is not from VS
 * @frame: the saved frame, for BE_B5:DETAIL
 */
void be_b5_exit_terminal(struct be_r4_frame *frame) __attribute__((noreturn));

/**
 * be_b5_arch_arm_stce - write henvcfg = STCE only and read it back
 *
 * Return: the henvcfg readback.
 */
be_u64 be_b5_arch_arm_stce(void);

/**
 * be_b5_arch_arm_controls - arm the guest controls and read them back
 * @controls: readback output
 *
 * Writes vstimecmp = ~0 and samples hip, then writes hideleg = VSTI,
 * hcounteren = TM, and clears hstatus.VTSR.
 */
void be_b5_arch_arm_controls(struct be_b5_controls *controls);

/**
 * be_b5_arch_set_timer - serve SBI TIME set_timer
 * @deadline: the guest's absolute deadline, written to vstimecmp
 */
void be_b5_arch_set_timer(be_u64 deadline);

/**
 * be_b5_arch_resume - check the controls and return to the guest
 * @frame: the management saved page
 * @expected_hgatp: the published management hgatp
 *
 * Checks every guest control, the management hgatp, and Bare vsatp, then
 * restores sepc and every GPR from @frame and executes one SRET. A failed
 * check is terminal (resume). It writes no vs* CSR, hgatp, or fence.
 */
void be_b5_arch_resume(struct be_r4_frame *frame, be_u64 expected_hgatp)
	__attribute__((noreturn));

extern be_u8 be_b5_trap_vector[];
extern be_u8 be_b5_payload[];
extern be_u8 be_b5_payload_end[];

#endif
