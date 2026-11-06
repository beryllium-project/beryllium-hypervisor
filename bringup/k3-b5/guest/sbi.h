/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: SBI calling convention and identifiers for the K3 B5 test guest.
 * Trust:   untrusted VS code. The monitor decides every call; nothing here
 *          grants authority.
 * Scope:   the B5-only subset (planning/k3-b5-plan.md) plus the identifiers
 *          the guest uses to test refusals. Not an SBI library or guest ABI.
 */

#ifndef BE_B5_GUEST_SBI_H
#define BE_B5_GUEST_SBI_H

#define SBI_EID_LEGACY_PUTCHAR	0x1UL
#define SBI_EID_BASE		0x10UL
#define SBI_EID_TIME		0x54494d45UL
#define SBI_EID_IPI		0x735049UL
#define SBI_EID_RFENCE		0x52464e43UL
#define SBI_EID_HSM		0x48534dUL
#define SBI_EID_SRST		0x53525354UL
#define SBI_EID_DBCN		0x4442434eUL
/* No SBI extension is assigned this EID ("BE55"). */
#define SBI_EID_UNASSIGNED	0x42453535UL

#define SBI_BASE_GET_SPEC_VERSION	0UL
#define SBI_BASE_GET_IMPL_ID		1UL
#define SBI_BASE_GET_IMPL_VERSION	2UL
#define SBI_BASE_PROBE_EXTENSION	3UL
#define SBI_BASE_GET_MVENDORID		4UL
#define SBI_BASE_GET_MARCHID		5UL
#define SBI_BASE_GET_MIMPID		6UL
/* Base defines FIDs 0-6 only. */
#define SBI_BASE_UNASSIGNED_FID		7UL
#define SBI_TIME_SET_TIMER		0UL
#define SBI_DBCN_WRITE			0UL
#define SBI_DBCN_READ			1UL
#define SBI_DBCN_WRITE_BYTE		2UL
#define SBI_SRST_SYSTEM_RESET		0UL

#define SBI_SRST_TYPE_SHUTDOWN		0UL
#define SBI_SRST_TYPE_COLD_REBOOT	1UL
#define SBI_SRST_TYPE_RESERVED		3UL
#define SBI_SRST_REASON_NONE		0UL
#define SBI_SRST_REASON_FAILURE		1UL
#define SBI_SRST_REASON_RESERVED	2UL

#define SBI_ERR_NOT_SUPPORTED		(-2L)
#define SBI_ERR_INVALID_PARAM		(-3L)
#define SBI_ERR_DENIED			(-4L)

/**
 * struct sbiret - SBI return pair
 * @error: a0
 * @value: a1
 */
struct sbiret {
	long error;
	unsigned long value;
};

/*
 * a7 is the EID, a6 the FID, a0-a2 the arguments; only a0 and a1 change.
 * The memory clobber orders guest buffers the monitor reads (DBCN write).
 */
static inline struct sbiret sbi_call(unsigned long eid, unsigned long fid,
				     unsigned long argument0,
				     unsigned long argument1,
				     unsigned long argument2)
{
	register unsigned long a0 __asm__("a0") = argument0;
	register unsigned long a1 __asm__("a1") = argument1;
	register unsigned long a2 __asm__("a2") = argument2;
	register unsigned long a6 __asm__("a6") = fid;
	register unsigned long a7 __asm__("a7") = eid;

	__asm__ __volatile__("ecall"
			     : "+r"(a0), "+r"(a1)
			     : "r"(a2), "r"(a6), "r"(a7)
			     : "memory");
	return (struct sbiret){ (long)a0, a1 };
}

#endif
