/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the K3 B7 guest payload of the boot image: the pinned Linux
 *          kernel Image at boot-image offset 0x35000, then G0's 4 KiB DTB
 *          at the next 4 KiB boundary and G1's 4 KiB DTB right after it,
 *          which ends the image. Every loader stages the boot image at
 *          L = 0x1_0800_0000, where the monitor reads them and copies the
 *          kernel into both guest windows and each DTB into its own.
 * Trust:   untrusted guest bytes, never executed in place. The monitor
 *          checks their shape against link-time constants generated from
 *          these files (src/b7-payload.h); the pins and
 *          tests/check-b7-image.py bind their content.
 * Scope:   B7 only (planning/k3-b7-plan.md, "Memory and load paths").
 *          BE_B7_GUEST_KERNEL, BE_B7_GUEST_DTB0, and BE_B7_GUEST_DTB1 name
 *          the files.
 */

#ifndef BE_B7_GUEST_KERNEL
#error "BE_B7_GUEST_KERNEL must name the guest kernel Image"
#endif
#ifndef BE_B7_GUEST_DTB0
#error "BE_B7_GUEST_DTB0 must name G0's DTB"
#endif
#ifndef BE_B7_GUEST_DTB1
#error "BE_B7_GUEST_DTB1 must name G1's DTB"
#endif

	.section .guest.be_b7, "a", @progbits
	.balign 4096
	.globl be_b7_guest_kernel
	.type be_b7_guest_kernel, @object
be_b7_guest_kernel:
	.incbin	BE_B7_GUEST_KERNEL
	.globl be_b7_guest_kernel_end
be_b7_guest_kernel_end:
	.size be_b7_guest_kernel, . - be_b7_guest_kernel

	.balign 4096
	.globl be_b7_guest_dtb0
	.type be_b7_guest_dtb0, @object
be_b7_guest_dtb0:
	.incbin	BE_B7_GUEST_DTB0
	.globl be_b7_guest_dtb0_end
be_b7_guest_dtb0_end:
	.size be_b7_guest_dtb0, . - be_b7_guest_dtb0

	.globl be_b7_guest_dtb1
	.type be_b7_guest_dtb1, @object
be_b7_guest_dtb1:
	.incbin	BE_B7_GUEST_DTB1
	.globl be_b7_guest_dtb1_end
be_b7_guest_dtb1_end:
	.size be_b7_guest_dtb1, . - be_b7_guest_dtb1
