/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: separate one-page R-X synthetic VS stubs for the fixed R3 image.
 * Trust:   untrusted guest code. QEMU tracing must observe the first
 *          management instruction; the protected page is linked but unentered.
 * Scope:   infinite loops only. No event protocol, access test, trap, context,
 *          root switch, or protected-domain execution is implemented.
 */

	.option norvc

	.section .guest.management, "ax"
	.align 4
	.globl be_r3_management_guest_start
	.type be_r3_management_guest_start, @function
be_r3_management_guest_start:
1:
	j	1b
	.size be_r3_management_guest_start, . - be_r3_management_guest_start

	.section .guest.protected, "ax"
	.align 4
	.globl be_r3_protected_guest_unentered
	.type be_r3_protected_guest_unentered, @function
be_r3_protected_guest_unentered:
2:
	j	2b
	.size be_r3_protected_guest_unentered, . - be_r3_protected_guest_unentered
