/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: R4-only privileged transition declarations around the accepted R3
 *          platform boundary.
 * Trust:   assembly performs CSR and frame transfer; C supplies only checked,
 *          monitor-owned state and cannot authorize a root switch.
 * Scope:   one management VS resume path. No protected entry or R5 switch.
 */

#ifndef BE_R4_PLATFORM_H
#define BE_R4_PLATFORM_H

#include "r3-platform.h"

#include <be/r4.h>

/**
 * be_r4_runtime_main - execute R3 boot then the bounded R4 management sequence
 * @hart_id: OpenSBI a0 hart identifier
 * @firmware_pointer: opaque OpenSBI a1 handoff value
 */
void be_r4_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
	__attribute__((noreturn));

/**
 * be_r4_runtime_terminal - report a stable R4 failure, request SRST, and halt
 * @error: stable terminal R4 error
 */
void be_r4_runtime_terminal(enum be_r4_error error)
	__attribute__((noreturn));

/**
 * be_r4_trap_dispatch - classify a complete monitor-owned VS-exit frame
 * @frame: fixed saved-management frame written by the trap entry
 * @current_hgatp: CSR readback captured by assembly before C execution
 *
 * Return: only after a complete same-management restore decision.
 */
void be_r4_trap_dispatch(struct be_r4_frame *frame, be_u64 current_hgatp);

/**
 * be_r4_arch_reset_state - reset and read back the bounded initial HS/VS state
 * @trap_vector: direct R4 VS-exit vector
 * @state: complete reset CSR readback
 */
void be_r4_arch_reset_state(be_u64 trap_vector, struct be_r3_hs_state *state);

/**
 * be_r4_arch_restore_management - reset, verify, and restore one R4 frame
 * @frame: validated frame at the fixed management saved-state page
 *
 * This never returns: reset/readback failure is terminal, while success
 * performs the final SPP=1 SRET to the unchanged management binding.
 */
void be_r4_arch_restore_management(struct be_r4_frame *frame)
	__attribute__((noreturn));

/** be_r4_arch_halt - disable asynchronous paths and halt fail closed. */
void be_r4_arch_halt(void) __attribute__((noreturn));

extern be_u8 be_r4_trap_entry[];
extern be_u8 be_r4_management_guest_start[];
extern be_u8 be_r4_protected_guest_unentered[];

#endif
