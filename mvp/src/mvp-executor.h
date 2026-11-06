/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP's executor (planning/mvp-m6-plan.md, D-5 and Q5; S1
 *          H22): the one place the MVP's C performs a privileged effect,
 *          one function per effect: each SBI call (the firmware's version
 *          and extensions, HSM hart_start and hart_get_status, the IPI,
 *          hart 0's console write and, since M7, its console read, a
 *          domain hart's own DBCN write, and the SRST shutdown), a hart's
 *          accepted HS and VS reset, the hgatp
 *          install, each CSR write and read the C asks for (henvcfg's STCE,
 *          a domain hart's controls, hart 0's budget, the TIME deadline, a
 *          denial's injection, SSIP's clear, the time CSR, and the VMID
 *          probes' raw hgatp switch), each fence, the wait, the park, the
 *          resume, and the halt.
 * Trust:   each function calls one assembly helper (mvp-trap.S,
 *          mvp-hartentry.S, mvp-probe-arch.S) or one accepted ported helper
 *          (r3-platform.h), or be_mvp_fw_call, with its own arguments, and
 *          returns what that returns: no decision is made here. The
 *          decision code (hart 0's runtime, the domain harts', and the
 *          probe module) calls these and performs no privileged effect of
 *          its own; the trap assembly is unchanged.
 * Scope:   the MVP line. No contract is written yet: that is the first
 *          verification plan's.
 */

#ifndef BE_MVP_EXECUTOR_H
#define BE_MVP_EXECUTOR_H

#include "mvp-platform.h"

/*
 * The SBI calls. Each goes through the accepted be_r3_arch_sbi_call, the
 * image's one ecall: by the accepted platform helpers, or by
 * be_mvp_fw_call (mvp-platform.h), which this file defines.
 */

/**
 * be_mvp_exec_sbi_version - Base get_spec_version, the accepted helper's
 * @version: the version
 *
 * Return: the SBI error.
 */
long be_mvp_exec_sbi_version(be_u64 *version);

/**
 * be_mvp_exec_sbi_probe - Base probe_extension, the accepted helper's
 * @eid: the extension
 * @value: the probe's value
 *
 * Return: the SBI error.
 */
long be_mvp_exec_sbi_probe(be_u64 eid, be_u64 *value);

/**
 * be_mvp_exec_hart_start - HSM hart_start
 * @hart: the hart
 * @entry: its start address
 * @opaque: its a1
 *
 * Return: the SBI error; the call's value is not used.
 */
long be_mvp_exec_hart_start(be_u64 hart, be_u64 entry, be_u64 opaque);

/**
 * be_mvp_exec_hart_status - HSM hart_get_status
 * @hart: the hart
 * @status: the call's value, its state on success
 *
 * Return: the SBI error.
 */
long be_mvp_exec_hart_status(be_u64 hart, be_u64 *status);

/**
 * be_mvp_exec_send_ipi - IPI send_ipi
 * @mask: the hart mask
 * @base: the mask's base hart
 *
 * Return: the SBI error.
 */
long be_mvp_exec_send_ipi(be_u64 mask, be_u64 base);

/**
 * be_mvp_exec_console_write - hart 0's DBCN write, the accepted helper's,
 *                             through its diagnostic page
 * @text: the bytes
 * @length: their count
 *
 * Return: %BE_R3_ERROR_NONE, or the DBCN error.
 */
enum be_r3_error be_mvp_exec_console_write(const char *text, be_u64 length);

/**
 * be_mvp_exec_console_read - hart 0's DBCN console_read, by be_mvp_fw_call
 *                            (planning/mvp-m7-plan.md, D-1)
 * @buffer: hart 0's own read buffer in its HS data, physical in HS
 * @bytes: the most bytes to read, at most the buffer's size
 * @read: the count the firmware wrote, 0 when it held none
 *
 * Hart 0 alone calls it, and only in an image whose sealed configuration
 * grants console input; no code a domain hart runs reaches it.
 *
 * Return: the SBI error.
 */
long be_mvp_exec_console_read(be_u8 *buffer, be_u64 bytes, be_u64 *read);

/**
 * be_mvp_exec_dbcn_write - a domain hart's own DBCN write, from its stack
 * @bytes: the count
 * @address: the bytes' address
 * @written: the count the firmware took
 *
 * Return: the SBI error.
 */
long be_mvp_exec_dbcn_write(be_u64 bytes, be_u64 address, be_u64 *written);

/**
 * be_mvp_exec_system_reset - the accepted SRST shutdown
 *
 * Return: the SRST failure, when the firmware returns.
 */
enum be_r3_error be_mvp_exec_system_reset(void);

/* A hart's state: the accepted reset and install, and the MVP's helpers. */

/**
 * be_mvp_exec_reset_hs_state - the accepted reset of a hart's HS and VS
 *                              state, hgatp Bare
 * @trap_vector: its stvec
 * @state: the readback
 */
void be_mvp_exec_reset_hs_state(be_u64 trap_vector,
				struct be_r3_hs_state *state);

/**
 * be_mvp_exec_install_hgatp - the accepted install: hgatp, the local
 *                             hfence.gvma, and the readback
 * @hgatp: the value
 *
 * Return: the readback.
 */
be_u64 be_mvp_exec_install_hgatp(be_u64 hgatp);

/**
 * be_mvp_exec_arm_stce - be_mvp_arch_arm_stce(): henvcfg = STCE
 *
 * Return: the henvcfg readback.
 */
be_u64 be_mvp_exec_arm_stce(void);

/**
 * be_mvp_exec_arm_controls - be_mvp_arch_arm_controls()
 * @controls: the controls read back
 * @trusted_top: sscratch
 * @vcsr: the per-domain CSR set
 * @readback: the set read back
 */
void be_mvp_exec_arm_controls(struct be_mvp_controls *controls,
			      be_u64 trusted_top, const be_u64 *vcsr,
			      be_u64 *readback);

/**
 * be_mvp_exec_arm_budget - be_mvp_arch_arm_budget()
 * @deadline: stimecmp
 * @trusted_top: sscratch
 *
 * Return: sie.
 */
be_u64 be_mvp_exec_arm_budget(be_u64 deadline, be_u64 trusted_top);

/**
 * be_mvp_exec_set_timer - be_mvp_arch_set_timer()
 * @deadline: vstimecmp
 */
void be_mvp_exec_set_timer(be_u64 deadline);

/**
 * be_mvp_exec_inject - be_mvp_arch_inject(), in an image that accepts
 *                      denials
 * @vscause: the access fault's cause
 * @vstval: the faulting guest virtual address
 * @vsepc: the faulting instruction
 * @vsstatus: the guest's vsstatus as a trap into VS mode sets it
 * @readback: the four read back
 */
void be_mvp_exec_inject(be_u64 vscause, be_u64 vstval, be_u64 vsepc,
			be_u64 vsstatus, be_u64 *readback);

/**
 * be_mvp_exec_clear_ssip - be_mvp_arch_clear_ssip(): sip.SSIP cleared
 *
 * Return: sip before the clear.
 */
be_u64 be_mvp_exec_clear_ssip(void);

/**
 * be_mvp_exec_read_time - be_mvp_arch_read_time()
 *
 * Return: the time CSR.
 */
be_u64 be_mvp_exec_read_time(void);

/**
 * be_mvp_exec_switch_hgatp - be_mvp_probe_arch_switch_hgatp(), in the two
 *                            VMID probe images only
 * @hgatp: root B's hgatp
 *
 * Return: the readback.
 */
be_u64 be_mvp_exec_switch_hgatp(be_u64 hgatp);

/** be_mvp_exec_fence_w_w - be_mvp_arch_fence_w_w(): fence w, w. */
void be_mvp_exec_fence_w_w(void);

/** be_mvp_exec_fence_r_r - be_mvp_arch_fence_r_r(): fence r, r. */
void be_mvp_exec_fence_r_r(void);

/** be_mvp_exec_fence_r_w - be_mvp_arch_fence_r_w(): fence r, w. */
void be_mvp_exec_fence_r_w(void);

/** be_mvp_exec_fence_rw_rw - be_mvp_arch_fence_rw_rw(): fence rw, rw. */
void be_mvp_exec_fence_rw_rw(void);

/** be_mvp_exec_fence_i - be_mvp_arch_fence_i(): the image's one fence.i. */
void be_mvp_exec_fence_i(void);

/**
 * be_mvp_exec_wait - be_mvp_arch_wait()
 * @pending: the sip bits that end the wait
 *
 * Return: the time CSR after the wait.
 */
be_u64 be_mvp_exec_wait(be_u64 pending);

/** be_mvp_exec_park - be_mvp_arch_park(): HS wfi, forever. */
void be_mvp_exec_park(void) __attribute__((noreturn));

/**
 * be_mvp_exec_resume - be_mvp_arch_resume(): the checked SRET
 * @record: the hart's saved page
 * @expected_hgatp: the hart's installed hgatp
 * @expected_hedeleg: the hedeleg readback checked at arming
 */
void be_mvp_exec_resume(struct be_mvp_exit *record, be_u64 expected_hgatp,
			be_u64 expected_hedeleg) __attribute__((noreturn));

/** be_mvp_exec_halt - be_r3_arch_halt(): the accepted fail-closed halt. */
void be_mvp_exec_halt(void) __attribute__((noreturn));

#endif
