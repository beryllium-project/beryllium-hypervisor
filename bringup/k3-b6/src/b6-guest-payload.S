/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the K3 B6 guest payload of the boot image: the pinned Linux
 *          kernel Image at boot-image offset 0x35000, then the 4 KiB guest
 *          DTB at the next 4 KiB boundary, which ends the image. Every
 *          loader stages the boot image at L = 0x1_0800_0000, where the
 *          monitor reads both and copies them into the guest window.
 * Trust:   untrusted guest bytes, never executed in place. The monitor
 *          checks their shape against link-time constants generated from
 *          these files (src/b6-payload.h); the pins and
 *          tests/check-b6-image.py bind their content.
 * Scope:   B6 only (planning/k3-b6-plan.md, "One boot image at a fixed
 *          address"). BE_B6_GUEST_KERNEL and BE_B6_GUEST_DTB name the files.
 */

#ifndef BE_B6_GUEST_KERNEL
#error "BE_B6_GUEST_KERNEL must name the guest kernel Image"
#endif
#ifndef BE_B6_GUEST_DTB
#error "BE_B6_GUEST_DTB must name the guest DTB"
#endif

	.section .guest.be_b6, "a", @progbits
	.balign 4096
	.globl be_b6_guest_kernel
	.type be_b6_guest_kernel, @object
be_b6_guest_kernel:
	.incbin	BE_B6_GUEST_KERNEL
	.globl be_b6_guest_kernel_end
be_b6_guest_kernel_end:
	.size be_b6_guest_kernel, . - be_b6_guest_kernel

	.balign 4096
	.globl be_b6_guest_dtb
	.type be_b6_guest_dtb, @object
be_b6_guest_dtb:
	.incbin	BE_B6_GUEST_DTB
	.globl be_b6_guest_dtb_end
be_b6_guest_dtb_end:
	.size be_b6_guest_dtb, . - be_b6_guest_dtb
