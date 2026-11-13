/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jmorris@namei.org> */
/*
 * Purpose: host tests of the patch series' two pure decisions, compiled
 *          from the patched OpenSBI header include/sbi/sbi_dcommit.h of
 *          the firmware build: the commit guard, sbi_dcommit_target(),
 *          against its four conditions written out here, over every
 *          combination of up to three views; and the SBI call filter,
 *          sbi_dcommit_call_allowed(), on matches, mismatches, each
 *          argument index, the no-check marker, 64-bit register values,
 *          an empty list, and the entry limit.
 * Trust:   test-only. It includes the very header the firmware compiles,
 *          with -D__riscv_xlen=64 and -std=gnu11 as the firmware has them,
 *          and no system header, since sbi_types.h defines its own types.
 * Scope:   the decisions alone; the firmware tests (fwtest.py) run them
 *          inside the firmware.
 */
#include <sbi/sbi_dcommit.h>

int printf(const char *format, ...);

static unsigned long checks, failures;

static void check(int ok, const char *what, unsigned long detail)
{
	checks++;
	if (!ok) {
		failures++;
		printf("host-decisions: FAIL %s (%lu)\n", what, detail);
	}
}

/*
 * The guard's four conditions, as stated, over any number of views: the
 * caller runs in one listed non-root domain (not root) whose order is
 * less than every other's (1); exactly one other non-root domain lists
 * the hart (2); that domain boots the hart (3) and has an allowlist (4).
 */
static int conditions(const struct sbi_dcommit_view *v, u32 n)
{
	int caller = -1, other = -1, callers = 0, others = 0;
	u32 i;

	for (i = 0; i < n; i++) {
		if (v[i].caller) {
			callers++;
			caller = (int)i;
		} else {
			others++;
			other = (int)i;
		}
	}
	if (callers != 1)
		return -1;
	for (i = 0; i < n; i++)
		if ((int)i != caller && v[i].order <= v[caller].order)
			return -1;
	if (others != 1 || !v[other].boots || !v[other].listed)
		return -1;
	return other;
}

static void guard(void)
{
	struct sbi_dcommit_view v[SBI_DCOMMIT_VIEWS_MAX];
	u32 n, i, code, combos, accepted = 0;

	for (n = 0; n <= SBI_DCOMMIT_VIEWS_MAX; n++) {
		/* Each view: caller, boots, listed, and an order of 1 to 3 */
		combos = 1;
		for (i = 0; i < n; i++)
			combos *= 24;
		for (code = 0; code < combos; code++) {
			u32 rest = code;

			for (i = 0; i < n; i++) {
				v[i].caller = rest & 1;
				v[i].boots = (rest >> 1) & 1;
				v[i].listed = (rest >> 2) & 1;
				v[i].order = 1 + (rest >> 3) % 3;
				rest /= 24;
			}
			check(sbi_dcommit_target(v, n) == conditions(v, n),
			      "the guard against its conditions",
			      n * 1000000UL + code);
			accepted += conditions(v, n) >= 0;
		}
	}
	/*
	 * The accepting combinations: two views, the caller's in either
	 * place, three pairs of orders with the caller's lower, and any
	 * values of the caller's own boots and listed flags.
	 */
	check(accepted == 2 * 3 * 4, "the guard's accepting combinations",
	      accepted);
}

#define EXT_DBCN	0x4442434eUL
#define EXT_SRST	0x53525354UL
#define EXT_HSM		0x48534dUL

static int allowed(const struct sbi_dcommit_ecall *list, u32 count,
		   unsigned long ext, unsigned long fid, unsigned long a0,
		   unsigned long a1, unsigned long a5)
{
	const unsigned long args[6] = { a0, a1, 0, 0, 0, a5 };

	return sbi_dcommit_call_allowed(list, count, ext, fid, args);
}

static void filter(void)
{
	struct sbi_dcommit_ecall list[SBI_DCOMMIT_ECALLS_MAX + 1] = {
		{ EXT_DBCN, 0, SBI_DCOMMIT_ECALL_ANY_ARG, 0 },
		{ EXT_SRST, 0, 0, 0 },
		{ EXT_HSM, 3, 0, 0x80000000 },
		{ 0x10, 3, 1, 0xffffffff },
		{ 0x11, 1, 5, 7 },
		{ 0x12, 2, 6, 0 },
	};
	unsigned long args[6] = { 0 };
	u32 k;

	/* No argument check */
	check(allowed(list, 6, EXT_DBCN, 0, 99, 99, 99), "listed call", 0);
	check(!allowed(list, 6, EXT_DBCN, 1, 0, 0, 0), "other function", 0);
	check(!allowed(list, 6, EXT_DBCN + 1, 0, 0, 0, 0), "other extension",
	      0);
	/* An argument limit is inclusive */
	check(allowed(list, 6, EXT_SRST, 0, 0, 0, 0), "shutdown", 0);
	check(!allowed(list, 6, EXT_SRST, 0, 1, 0, 0), "cold reboot", 1);
	check(allowed(list, 6, EXT_HSM, 3, 0x80000000, 0, 0), "limit", 0);
	check(!allowed(list, 6, EXT_HSM, 3, 0x80000001, 0, 0), "over", 0);
	check(allowed(list, 6, 0x11, 1, ~0UL, ~0UL, 7), "a5 at its limit", 7);
	check(!allowed(list, 6, 0x11, 1, 0, 0, 8), "a5 over its limit", 8);
	/* 64-bit registers never match a 32-bit value */
	check(allowed(list, 6, 0x10, 3, 0, 0xffffffffUL, 0), "a1 max", 0);
	check(!allowed(list, 6, 0x10, 3, 0, 0x100000000UL, 0), "a1 bit 32",
	      0);
	check(!allowed(list, 6, EXT_DBCN | 1UL << 32, 0, 0, 0, 0),
	      "extension bit 32", 0);
	check(!allowed(list, 6, EXT_DBCN, 1UL << 32, 0, 0, 0),
	      "function bit 32", 0);
	/* An index out of range never matches, and reads no register */
	check(!allowed(list, 6, 0x12, 2, 0, 0, 0), "argument index 6", 0);
	/* Each argument index checks its own register */
	for (k = 0; k < 6; k++) {
		struct sbi_dcommit_ecall one = { 0x20, 0, k, 3 };
		u32 i;

		for (i = 0; i < 6; i++)
			args[i] = (i == k) ? 3 : ~0UL;
		check(sbi_dcommit_call_allowed(&one, 1, 0x20, 0, args),
		      "argument index at its limit", k);
		args[k] = 4;
		check(!sbi_dcommit_call_allowed(&one, 1, 0x20, 0, args),
		      "argument index over its limit", k);
	}
	/* An empty list allows nothing */
	check(!allowed(list, 0, EXT_DBCN, 0, 0, 0, 0), "empty list", 0);
	/* Entries past the limit are never read */
	for (k = 0; k < SBI_DCOMMIT_ECALLS_MAX + 1; k++) {
		list[k].extid = 0x30 + k;
		list[k].funcid = 0;
		list[k].arg = SBI_DCOMMIT_ECALL_ANY_ARG;
		list[k].max = 0;
	}
	check(allowed(list, SBI_DCOMMIT_ECALLS_MAX,
		      0x30 + SBI_DCOMMIT_ECALLS_MAX - 1, 0, 0, 0, 0),
	      "the last entry", 0);
	check(!allowed(list, SBI_DCOMMIT_ECALLS_MAX + 1,
		       0x30 + SBI_DCOMMIT_ECALLS_MAX, 0, 0, 0, 0),
	      "an entry past the limit", 0);
}

int main(void)
{
	guard();
	filter();
	printf("BE_MVP_FIRMWARE_HOST: %s checks=%lu failures=%lu\n",
	       failures ? "FAIL" : "PASS", checks, failures);
	return failures ? 1 : 0;
}
