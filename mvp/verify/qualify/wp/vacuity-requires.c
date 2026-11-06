/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> */
/*
 * Purpose: WP qualification, vacuity (planning/mvp-m8-plan.md, D-7 item 2):
 *          a contradictory precondition, which -wp-smoke-tests must detect
 *          (its smoke goal, "the preconditions imply false", proves). The
 *          contradiction needs a quantifier instantiated (k = 1), which
 *          WP's simplifier does not do, so the solver must find it.
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
    requires \forall integer k; 0 <= k < SLOTS ==> table[k].bytes != 0;
    requires table[1].bytes == 0;
    assigns \nothing;
    ensures \result == 0;
*/
int first_used(const struct slot *table)
{
	return table[0].bytes != 0 ? 0 : -1;
}
