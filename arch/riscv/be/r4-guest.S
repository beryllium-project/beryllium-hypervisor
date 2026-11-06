/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: fixed R4 management access/event fixture and unentered protected
 *          fixture.
 * Trust:   untrusted VS instructions. The monitor validates exits and backing
 *          observations; neither fixture has authority beyond its G-stage map.
 * Scope:   exactly one denied load and one private event; no SBI or switching.
 */

	.option norvc

	.section .guest.r4.management, "ax"
	.align 4
	.globl be_r4_management_guest_start
	.type be_r4_management_guest_start, @function
be_r4_management_guest_start:
	/* Each listed slot is deliberately one non-compressed four-byte opcode. */
	lui	t0, 0x40000			/* +0x00 management private */
	addi	t1, zero, 17			/* +0x04 */
	sw	t1, 0(t0)			/* +0x08 */
	lw	s0, 0(t0)			/* +0x0c */
	lui	t2, 0x40001			/* +0x10 protected private */
	lw	s1, 0(t2)			/* +0x14 denied: 0x40001000 */
	lui	t2, 0x40002			/* +0x18 shared */
	addi	t1, zero, 34			/* +0x1c */
	sw	t1, 0(t2)			/* +0x20 */
	lw	a1, 0(t2)			/* +0x24 */
	addi	a0, s0, 0			/* +0x28 */
	addi	a7, zero, 1			/* +0x2c; a6 stays zero */
	ecall					/* +0x30 */
1:
	j	1b				/* +0x34 */
	.size be_r4_management_guest_start, . - be_r4_management_guest_start

	.section .guest.r4.protected, "ax"
	.align 4
	.globl be_r4_protected_guest_unentered
	.type be_r4_protected_guest_unentered, @function
be_r4_protected_guest_unentered:
2:
	j	2b
	.size be_r4_protected_guest_unentered, . - be_r4_protected_guest_unentered
