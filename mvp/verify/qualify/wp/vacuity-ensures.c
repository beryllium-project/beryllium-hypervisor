/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> */
/*
 * Purpose: WP qualification, vacuity (planning/mvp-m8-plan.md, D-7 item 2):
 *          `ensures \false` under a satisfiable precondition, which must
 *          not prove.
 * Trust:   a fixture, never linked; specification SHA-256
 *          ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
 * Scope:   the WP arm's qualification only; not the leaf.
 */

/*@ requires 512 <= bytes <= 4096;
    assigns \nothing;
    ensures \false;
*/
unsigned long excess(unsigned long bytes)
{
	return bytes - 512UL;
}
