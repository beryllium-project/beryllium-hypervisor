/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> */
/*
 * Purpose: CN qualification, vacuity (planning/mvp-m8-plan.md, D-7 item 2):
 *          a contradictory precondition must be detected. CN has no smoke
 *          test, so the check is an explicit reachability one: a CN `assert
 *          (false)` after entry verifies (pass) only if no state satisfies
 *          the precondition, which here means detected.
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
             S.bytes > 4096;
             S.bytes < 512;
    ensures take T = RW<struct slot>(slot);
            T == S; @*/
{
	/*@ assert (false); @*/
	return slot->bytes;
}
