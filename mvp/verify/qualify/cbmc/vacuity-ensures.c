/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> */
/*
 * Purpose: CBMC qualification, vacuity (planning/mvp-m8-plan.md, D-7 item
 *          2): `ensures \false` under a satisfiable precondition, asserted
 *          as assert(false) after the call, which must fail.
 * Trust:   a fixture, never linked; specification SHA-256
 *          ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
 * Scope:   the CBMC arm's qualification only; not the leaf.
 */

unsigned long nondet_ulong(void);

static unsigned long excess(unsigned long bytes)
{
	return bytes - 512UL;
}

int main(void)
{
	unsigned long bytes = nondet_ulong();
	unsigned long result;

	__CPROVER_assume(bytes >= 512UL && bytes <= 4096UL);
	result = excess(bytes);
	__CPROVER_assert(result <= 3584UL, "a true postcondition");
	__CPROVER_assert(0, "ensures false");
	return 0;
}
