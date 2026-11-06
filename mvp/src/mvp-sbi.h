/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP monitor's own firmware surface beyond the accepted four
 *          calls (planning/mvp-m0-plan.md, "Guest SBI subset and the
 *          firmware surface", MVP plan D15): the HSM and IPI extensions and
 *          their three functions, hart_start, hart_get_status, and
 *          send_ipi; since M7, hart 0's DBCN console read
 *          (planning/mvp-m7-plan.md, D-1); the HSM states; and the pure
 *          checks hart 0 applies to
 *          their results, BE_MVP:02's census of the other harts among them
 *          (Plan revision M0-A.2).
 * Trust:   constants and pure checks only. The calls themselves go through
 *          the accepted be_r3_arch_sbi_call helper, so the image keeps one
 *          ecall site; the accepted r0-sbi.h allowlist is unchanged.
 * Scope:   the MVP line. HSM hart_stop is named only for the QEMU-only
 *          shim-rule variant; no guest request reaches these calls.
 */

#ifndef BE_MVP_SBI_H
#define BE_MVP_SBI_H

#include <be/types.h>

#define BE_MVP_FW_EID_HSM		BE_U64_C(0x48534d)
#define BE_MVP_FW_EID_IPI		BE_U64_C(0x735049)
#define BE_MVP_FW_HSM_HART_START	BE_U64_C(0)
#define BE_MVP_FW_HSM_HART_STOP		BE_U64_C(1)
#define BE_MVP_FW_HSM_HART_GET_STATUS	BE_U64_C(2)
#define BE_MVP_FW_IPI_SEND_IPI		BE_U64_C(0)
/* DBCN console_read (SBI 2.0, section 12.2), hart 0's alone (M7, D-1). */
#define BE_MVP_FW_DBCN_READ		BE_U64_C(1)

/* HSM hart states (SBI 2.0, section 9). */
#define BE_MVP_HSM_STARTED		BE_U64_C(0)
#define BE_MVP_HSM_STOPPED		BE_U64_C(1)
#define BE_MVP_HSM_START_PENDING	BE_U64_C(2)
#define BE_MVP_HSM_STOP_PENDING		BE_U64_C(3)
#define BE_MVP_HSM_SUSPENDED		BE_U64_C(4)
#define BE_MVP_HSM_SUSPEND_PENDING	BE_U64_C(5)
#define BE_MVP_HSM_RESUME_PENDING	BE_U64_C(6)

/**
 * be_mvp_hsm_stopped - whether a hart_get_status result is STOPPED
 * @error: the call's SBI error
 * @value: the call's value
 *
 * Return: 1 only for success with STOPPED; an error (a hart the firmware
 *         does not have) or any other state is 0, which hart 0 refuses.
 */
int be_mvp_hsm_stopped(long error, be_u64 value);

/**
 * be_mvp_hsm_started - whether a hart_get_status result is STARTED
 * @error: the call's SBI error
 * @value: the call's value
 *
 * Return: 1 only for success with STARTED, else 0.
 */
int be_mvp_hsm_started(long error, be_u64 value);

/**
 * be_mvp_ipi_target - the send_ipi arguments for one hart
 * @hart: the target hart
 * @mask: the hart mask, 1
 * @base: the hart mask base, @hart
 *
 * Return: 1, or 0 for the all-harts base (~0) or an absent pointer.
 */
int be_mvp_ipi_target(be_u64 hart, be_u64 *mask, be_u64 *base);

/* A census's started field when no hart was found STARTED. */
#define BE_MVP_HSM_NONE			(~BE_U64_C(0))

/**
 * struct be_mvp_hsm_census - hart 0's firmware rule over every other hart
 * @domain_hart: the run's domains' harts, from the binding; the second is
 *               %BE_MVP_HSM_NONE when the run has one domain (the probe
 *               images)
 * @started: the hart found STARTED, or %BE_MVP_HSM_NONE
 * @refused: nonzero once a status broke the rule; sticky
 *
 * BE_MVP:02 (Plan revision M0-A.2): both domain harts STOPPED, and every
 * other hart but hart 0 STOPPED but for at most one STARTED hart, the boot
 * hart the shim's start rule leaves parked when it started hart 0.
 */
struct be_mvp_hsm_census {
	be_u64 domain_hart[2];
	be_u64 started;
	be_u32 refused;
};

/**
 * be_mvp_hsm_census_init - a census before any hart's status
 * @census: the census
 * @domain0_hart: domain 0's hart
 * @domain1_hart: domain 1's hart, or %BE_MVP_HSM_NONE for a one-domain run
 */
void be_mvp_hsm_census_init(struct be_mvp_hsm_census *census,
			    be_u64 domain0_hart, be_u64 domain1_hart);

/**
 * be_mvp_hsm_census_add - one other hart's hart_get_status result
 * @census: the census
 * @hart: the hart, never hart 0
 * @error: the call's SBI error
 * @value: the call's value
 *
 * STOPPED holds for any hart. STARTED holds once for a hart that is not a
 * domain's and records it in @census->started; a STARTED domain hart, a
 * second STARTED hart, any other state, an error (a hart the firmware does
 * not have), hart 0, or the %BE_MVP_HSM_NONE hart refuses the census. A
 * STARTED hart is recorded even when it refuses the census.
 *
 * Return: 1 while the census holds, else 0.
 */
int be_mvp_hsm_census_add(struct be_mvp_hsm_census *census, be_u64 hart,
			  long error, be_u64 value);

#endif
