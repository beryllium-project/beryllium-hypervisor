// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: bounded SBI Base/DBCN/SRST integration for the R3 RISC-V image.
 * Trust:   platform glue around the explicit assembly ECALL boundary. Only
 *          trusted HS bytes copied into the linker-reserved diagnostic page
 *          are ever supplied to DBCN as a physical range.
 * Scope:   R3 diagnostics and terminal shutdown only. No legacy SBI, guest
 *          SBI, forwarding, recovery, timer, IPI, or remote-fence behavior.
 */
#include "r3-platform.h"

#include "r0-sbi.h"

_Static_assert(__builtin_offsetof(struct be_r3_hs_state, satp) == 0U,
	       "assembly HS state offset mismatch");
_Static_assert(__builtin_offsetof(struct be_r3_hs_state, hstatus) == 88U,
	       "assembly HSTATUS offset mismatch");
_Static_assert(__builtin_offsetof(struct be_r3_hs_state, hgatp) == 184U,
	       "assembly HGATP offset mismatch");
_Static_assert(__builtin_offsetof(struct be_r3_hs_state, vsatp) == 256U,
	       "assembly VSATP offset mismatch");
_Static_assert(sizeof(struct be_r3_hs_state) == 264U,
	       "assembly HS state size mismatch");
_Static_assert(BE_R3_SSTATUS_SPP == BE_U64_C(0x100),
	       "assembly SPP mask mismatch");

static long sbi_value_call(be_u64 eid, be_u64 fid, be_u64 argument0,
			   be_u64 *value)
{
	struct be_r3_sbi_return result = { BE_R0_SBI_ERR_FAILED, 0U };

	if (value == (be_u64 *)0)
		return BE_R0_SBI_ERR_INVALID_PARAM;
	be_r3_arch_sbi_call(&result, eid, fid, argument0, 0U, 0U);
	*value = result.value;
	return result.error;
}

long be_r3_platform_get_spec_version(be_u64 *value)
{
	return sbi_value_call(BE_R0_SBI_EID_BASE,
			      BE_R0_SBI_BASE_FID_GET_SPEC_VERSION,
			      0U, value);
}

long be_r3_platform_probe_extension(be_u64 eid, be_u64 *value)
{
	return sbi_value_call(BE_R0_SBI_EID_BASE,
			      BE_R0_SBI_BASE_FID_PROBE_EXTENSION,
			      eid, value);
}

be_u64 be_r3_text_length(const char *text)
{
	be_u64 length;

	if (text == (const char *)0)
		return BE_PAGE_SIZE + 1U;
	for (length = 0U; length < BE_PAGE_SIZE; ++length) {
		if (text[length] == '\0')
			return length;
	}
	return BE_PAGE_SIZE + 1U;
}

enum be_r3_error
be_r3_platform_write(const char *text, be_u64 length)
{
	struct be_r3_dbcn_progress progress = BE_R3_DBCN_INITIALIZER;
	be_u8 *diagnostic = __be_diagnostic_start;
	be_u64 index;
	enum be_r3_error error;

	if (text == (const char *)0)
		return BE_R3_ERROR_NULL;
	if (length > BE_PAGE_SIZE)
		return BE_R3_ERROR_DBCN_RANGE;
	for (index = 0U; index < length; ++index)
		diagnostic[index] = (be_u8)text[index];

	error = be_r3_dbcn_begin(&progress, BE_R3_DIAGNOSTIC_BASE, length);
	if (error != BE_R3_ERROR_NONE)
		return error;
	while (progress.state == BE_R3_DBCN_ACTIVE) {
		struct be_r3_sbi_return result = {
			BE_R0_SBI_ERR_FAILED, 0U
		};
		be_u64 remaining = progress.length - progress.offset;
		be_u64 address = progress.base + progress.offset;

		be_r3_arch_sbi_call(&result, BE_R0_SBI_EID_DBCN,
				    BE_R0_SBI_DBCN_FID_WRITE,
				    remaining, address, 0U);
		error = be_r3_dbcn_consume(&progress, result.error,
					   result.value);
		if (error != BE_R3_ERROR_NONE)
			return error;
	}
	return progress.state == BE_R3_DBCN_COMPLETE ?
		BE_R3_ERROR_NONE : progress.error;
}

enum be_r3_error be_r3_platform_reset(void)
{
	struct be_r3_sbi_return result = { BE_R0_SBI_ERR_FAILED, 0U };

	be_r3_arch_sbi_call(&result, BE_R0_SBI_EID_SRST,
			    BE_R0_SBI_SRST_FID_SYSTEM_RESET,
			    BE_R0_SBI_SRST_TYPE_SHUTDOWN,
			    BE_R0_SBI_SRST_REASON_NONE, 0U);
	return be_r3_srst_result(result.error);
}
