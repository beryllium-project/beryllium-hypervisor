/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> */
/*
 * Purpose: WP qualification, known-pass (planning/mvp-m8-plan.md, D-7 item
 *          2): a correct function with a provable contract. Its loop
 *          invariant needs the solver, not only WP's simplifier.
 * Trust:   a fixture, never linked; specification SHA-256
 *          ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
 * Scope:   the WP arm's qualification only; not the leaf.
 */

#define SLOTS 3

struct slot {
	unsigned long base;
	unsigned long bytes;
};

/*@ requires \valid_read(table + (0 .. SLOTS - 1));
    assigns \nothing;
    ensures -1 <= \result < SLOTS;
    ensures \result >= 0 ==> table[\result].bytes != 0;
    ensures \result >= 0 ==>
      (\forall integer k; 0 <= k < \result ==> table[k].bytes == 0);
    ensures \result == -1 ==>
      (\forall integer k; 0 <= k < SLOTS ==> table[k].bytes == 0);
*/
int first_used(const struct slot *table)
{
	int index;

	/*@ loop invariant 0 <= index <= SLOTS;
	    loop invariant \forall integer k; 0 <= k < index ==>
	      table[k].bytes == 0;
	    loop assigns index;
	    loop variant SLOTS - index;
	*/
	for (index = 0; index < SLOTS; ++index)
		if (table[index].bytes != 0)
			return index;
	return -1;
}
