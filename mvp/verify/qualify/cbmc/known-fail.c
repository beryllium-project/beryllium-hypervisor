/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> */
/*
 * Purpose: CBMC qualification, known-fail (planning/mvp-m8-plan.md, D-7
 *          item 2): the same function with a false postcondition, which
 *          must fail: an empty table returns -1.
 * Trust:   a fixture, never linked; specification SHA-256
 *          ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
 * Scope:   the CBMC arm's qualification only; not the leaf.
 */

#define SLOTS 3

struct slot {
	unsigned long base;
	unsigned long bytes;
};

unsigned long nondet_ulong(void);

static int first_used(const struct slot *table)
{
	int index;

	for (index = 0; index < SLOTS; ++index)
		if (table[index].bytes != 0)
			return index;
	return -1;
}

int main(void)
{
	struct slot table[SLOTS];
	int index, result;

	for (index = 0; index < SLOTS; ++index) {
		table[index].base = nondet_ulong();
		table[index].bytes = nondet_ulong();
	}
	result = first_used(table);
	__CPROVER_assert(result >= 0 && result < SLOTS, "result in range");
	__CPROVER_assert(result < 0 || table[result].bytes != 0,
			 "a used slot");
	__CPROVER_assert(result != -1 || (table[0].bytes == 0 &&
					  table[1].bytes == 0 &&
					  table[2].bytes == 0), "none used");
	return 0;
}
