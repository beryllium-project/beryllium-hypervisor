/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: R5-only privileged transition declarations around the accepted R3
 *          platform boundary and the unchanged R4 frame.
 * Trust:   assembly owns every CSR write, the local G-stage fence, frame
 *          transfer, and the no-call restore/SRET tail; C supplies only
 *          checked monitor-owned state and never runs with guest-restored
 *          general-purpose registers.
 * Scope:   management -> protected -> management -> shutdown only. No
 *          scheduling, rollback, dynamic binding, root or PTE edit, guest SBI,
 *          policy, multicore, or R6+ behavior.
 */

#ifndef BE_R5_PLATFORM_H
#define BE_R5_PLATFORM_H

#include "r3-platform.h"

#include <be/r5.h>

/**
 * struct be_r5_controls - CSR-derived facts sampled for one R5 exit
 * @hgatp: G-stage root actually selected when the exit was taken
 * @hstatus: hypervisor controls proving VS origin and the fixed profile
 * @vsatp: VS-stage translation readback, required Bare
 * @sscratch: trusted-stack identity the vector re-armed before C was reachable
 *
 * Only assembly reads these CSRs. Every field is monitor-owned: no guest
 * pointer, guest register, or fault address may select monitor context.
 */
struct be_r5_controls {
	be_u64 hgatp;
	be_u64 hstatus;
	be_u64 vsatp;
	be_u64 sscratch;
};

/**
 * be_r5_runtime_main - execute R3 boot, the in-image R4 prelude, and R5
 * @hart_id: OpenSBI a0 hart identifier
 * @firmware_pointer: opaque OpenSBI a1 handoff value
 */
void be_r5_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
	__attribute__((noreturn));

/**
 * be_r5_runtime_terminal - report a stable R5 failure, request SRST, and halt
 * @error: stable terminal R5 error
 */
void be_r5_runtime_terminal(enum be_r5_error error)
	__attribute__((noreturn));

/**
 * be_r5_trap_dispatch - service exactly one complete monitor-owned VS exit
 * @frame: fixed 320-byte frame the trap vector wrote to the monitor saved page
 *
 * This never returns: it either fails closed, tail-calls the same-domain
 * restore, tail-calls the published no-call switch tail, or shuts down.
 */
void be_r5_trap_dispatch(struct be_r4_frame *frame) __attribute__((noreturn));

/**
 * be_r5_arch_reset_state - reset and read back the bounded initial HS/VS state
 * @trap_vector: direct R5 VS-exit vector
 * @state: complete reset CSR readback
 */
void be_r5_arch_reset_state(be_u64 trap_vector, struct be_r3_hs_state *state);

/**
 * be_r5_arch_read_controls - sample the CSR-derived facts for one exit
 * @controls: complete readback output
 */
void be_r5_arch_read_controls(struct be_r5_controls *controls);

/**
 * be_r5_arch_install_root - write, fence, and read back one target root
 * @ack: ordered write/fence/readback evidence written by assembly
 * @target_hgatp: exact unpublished target Sv39x4/VMID-zero value
 *
 * The HGATP write is an HS-only operation: reaching the following instruction
 * without a virtual-instruction trap is what establishes that the write
 * happened with V=0. The local all-GPA/all-VMID fence is issued before the
 * readback, and an HGATP write alone supplies no ordering.
 */
void be_r5_arch_install_root(struct be_r5_fence_ack *ack, be_u64 target_hgatp);

/**
 * be_r5_arch_reset_target - reset, verify, and read back target entry state
 * @entry: verified reset state and entry controls
 * @trusted_sp: exact monitor-owned trusted stack the target domain owns
 *
 * The already installed and fenced target root is deliberately not rewritten.
 * The monitor saved page is derived from the checked trusted-stack identity
 * alone and reported back for independent comparison with the binding.
 */
void be_r5_arch_reset_target(struct be_r5_entry_state *entry,
			     be_u64 trusted_sp);

/**
 * be_r5_arch_restore_active - reset, verify, and resume the unchanged domain
 * @frame: validated frame at the active domain's monitor saved page
 * @expected_hgatp: active root that must still be selected
 * @trusted_sp: active trusted stack that must be re-armed in sscratch
 *
 * This never returns: reset or readback failure is terminal, while success
 * performs the SPP=1 SRET back into the unchanged binding.
 */
void be_r5_arch_restore_active(struct be_r4_frame *frame,
			       be_u64 expected_hgatp, be_u64 trusted_sp)
	__attribute__((noreturn));

/**
 * be_r5_switch_tail - published no-call restore and SRET into the target
 * @frame: prepared target frame at the target's monitor saved page
 * @expected_hgatp: published target root
 * @trusted_sp: published target trusted stack
 *
 * This runs only after publication. It verifies the prepared target state,
 * restores the complete frame, and executes SRET without calling C.
 */
void be_r5_switch_tail(struct be_r4_frame *frame, be_u64 expected_hgatp,
		       be_u64 trusted_sp) __attribute__((noreturn));

/** be_r5_arch_halt - disable asynchronous paths and halt fail closed. */
void be_r5_arch_halt(void) __attribute__((noreturn));

extern be_u8 be_r5_trap_vector[];
extern be_u8 be_r5_management_fixture[];
extern be_u8 be_r5_management_fixture_end[];
extern be_u8 be_r5_protected_fixture[];
extern be_u8 be_r5_protected_fixture_end[];

#endif
