// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP's executor (mvp-executor.h; planning/mvp-m6-plan.md,
 *          D-5): one function per privileged effect, each calling one
 *          assembly helper or one accepted ported helper; and
 *          be_mvp_fw_call, the MVP's one HS-to-M call beyond the accepted
 *          platform helpers', moved here from hart 0's runtime unchanged.
 * Trust:   no decision: each function passes its arguments through and
 *          returns its helper's result. The injection's function is built
 *          only into an image that accepts denials, and the raw hgatp
 *          switch's only into the two VMID probe images, so each image
 *          links the helper calls it linked before.
 * Scope:   the MVP line, built for each monitor with its scenario and
 *          variant, as hart 0's and the domain harts' runtimes are.
 */
#include "mvp-executor.h"

#include "mvp-sbi.h"
#include "r0-sbi.h"
#if defined(BE_MVP_PROBE_IMAGE)
#include "mvp-probe.h"
#endif

long be_mvp_fw_call(be_u64 eid, be_u64 fid, be_u64 argument0,
		    be_u64 argument1, be_u64 argument2, be_u64 *value)
{
	struct be_r3_sbi_return result = { BE_R0_SBI_ERR_FAILED, 0U };

	be_r3_arch_sbi_call(&result, eid, fid, argument0, argument1,
			    argument2);
	*value = result.value;
	return result.error;
}

long be_mvp_exec_sbi_version(be_u64 *version)
{
	return be_r3_platform_get_spec_version(version);
}

long be_mvp_exec_sbi_probe(be_u64 eid, be_u64 *value)
{
	return be_r3_platform_probe_extension(eid, value);
}

long be_mvp_exec_hart_start(be_u64 hart, be_u64 entry, be_u64 opaque)
{
	be_u64 value;

	return be_mvp_fw_call(BE_MVP_FW_EID_HSM, BE_MVP_FW_HSM_HART_START,
			      hart, entry, opaque, &value);
}

long be_mvp_exec_hart_status(be_u64 hart, be_u64 *status)
{
	return be_mvp_fw_call(BE_MVP_FW_EID_HSM,
			      BE_MVP_FW_HSM_HART_GET_STATUS, hart, 0U, 0U,
			      status);
}

long be_mvp_exec_send_ipi(be_u64 mask, be_u64 base)
{
	be_u64 value;

	return be_mvp_fw_call(BE_MVP_FW_EID_IPI, BE_MVP_FW_IPI_SEND_IPI, mask,
			      base, 0U, &value);
}

enum be_r3_error be_mvp_exec_console_write(const char *text, be_u64 length)
{
	return be_r3_platform_write(text, length);
}

long be_mvp_exec_console_read(be_u8 *buffer, be_u64 bytes, be_u64 *read)
{
	return be_mvp_fw_call(BE_R0_SBI_EID_DBCN, BE_MVP_FW_DBCN_READ, bytes,
			      (be_u64)(unsigned long)buffer, 0U, read);
}

long be_mvp_exec_dbcn_write(be_u64 bytes, be_u64 address, be_u64 *written)
{
	return be_mvp_fw_call(BE_R0_SBI_EID_DBCN, BE_R0_SBI_DBCN_FID_WRITE,
			      bytes, address, 0U, written);
}

enum be_r3_error be_mvp_exec_system_reset(void)
{
	return be_r3_platform_reset();
}

void be_mvp_exec_reset_hs_state(be_u64 trap_vector,
				struct be_r3_hs_state *state)
{
	be_r3_arch_reset_state(trap_vector, state);
}

be_u64 be_mvp_exec_install_hgatp(be_u64 hgatp)
{
	return be_r3_arch_install_management(hgatp);
}

be_u64 be_mvp_exec_arm_stce(void)
{
	return be_mvp_arch_arm_stce();
}

void be_mvp_exec_arm_controls(struct be_mvp_controls *controls,
			      be_u64 trusted_top, const be_u64 *vcsr,
			      be_u64 *readback)
{
	be_mvp_arch_arm_controls(controls, trusted_top, vcsr, readback);
}

be_u64 be_mvp_exec_arm_budget(be_u64 deadline, be_u64 trusted_top)
{
	return be_mvp_arch_arm_budget(deadline, trusted_top);
}

void be_mvp_exec_set_timer(be_u64 deadline)
{
	be_mvp_arch_set_timer(deadline);
}

#if BE_MVP_RUN_ACCEPT_DENIAL
void be_mvp_exec_inject(be_u64 vscause, be_u64 vstval, be_u64 vsepc,
			be_u64 vsstatus, be_u64 *readback)
{
	be_mvp_arch_inject(vscause, vstval, vsepc, vsstatus, readback);
}
#endif

be_u64 be_mvp_exec_clear_ssip(void)
{
	return be_mvp_arch_clear_ssip();
}

be_u64 be_mvp_exec_read_time(void)
{
	return be_mvp_arch_read_time();
}

#if defined(BE_MVP_PROBE_IMAGE)
#if BE_MVP_PROBE_IMAGE != BE_MVP_PROBE_PLATFORM
be_u64 be_mvp_exec_switch_hgatp(be_u64 hgatp)
{
	return be_mvp_probe_arch_switch_hgatp(hgatp);
}
#endif
#endif

void be_mvp_exec_fence_w_w(void)
{
	be_mvp_arch_fence_w_w();
}

void be_mvp_exec_fence_r_r(void)
{
	be_mvp_arch_fence_r_r();
}

void be_mvp_exec_fence_r_w(void)
{
	be_mvp_arch_fence_r_w();
}

void be_mvp_exec_fence_rw_rw(void)
{
	be_mvp_arch_fence_rw_rw();
}

void be_mvp_exec_fence_i(void)
{
	be_mvp_arch_fence_i();
}

be_u64 be_mvp_exec_wait(be_u64 pending)
{
	return be_mvp_arch_wait(pending);
}

void be_mvp_exec_park(void)
{
	be_mvp_arch_park();
}

void be_mvp_exec_resume(struct be_mvp_exit *record, be_u64 expected_hgatp,
			be_u64 expected_hedeleg)
{
	be_mvp_arch_resume(record, expected_hgatp, expected_hedeleg);
}

void be_mvp_exec_halt(void)
{
	be_r3_arch_halt();
}
