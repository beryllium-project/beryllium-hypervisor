/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> */
/*
 * Purpose: CN qualification, vacuity (planning/mvp-m8-plan.md, D-7 item 2):
 *          `ensures false` under a satisfiable precondition, which must
 *          fail.
 * Trust:   a fixture, never linked; specification SHA-256
 *          ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d.
 * Scope:   the CN arm's qualification only; not the leaf.
 */

struct slot {
	unsigned long base;
	unsigned long bytes;
};

unsigned long slot_end(struct slot *slot)
/*@ requires take S = RW<struct slot>(slot);
             S.base <= 4096;
             S.bytes <= 4096;
    ensures take T = RW<struct slot>(slot);
            false; @*/
{
	return slot->base + slot->bytes;
}
