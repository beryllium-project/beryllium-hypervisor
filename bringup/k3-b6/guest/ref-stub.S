/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: OpenSBI's next stage in the K3 B6 guest's QEMU reference boot
 *          (planning/k3-b6-plan.md, Build, pins, and reproducibility;
 *          platform research section 1f): enter the pinned Image at
 *          B6_REF_KERNEL in S-mode with a0 = 0 (hart 0), a1 = B6_REF_DTB
 *          (the reference DTB), and satp = 0, in place of the B6 monitor's
 *          first entry. OpenSBI itself keeps QEMU's DTB for its console and
 *          reset devices.
 * Trust:   test scaffolding; no monitor runs in the reference boot.
 * Scope:   QEMU only. guest.mk builds it with the two addresses that
 *          scripts/gen-dts.py derives, and tests/run-reference-boot.sh
 *          loads it with -kernel.
 */

#ifndef B6_REF_KERNEL
#error "B6_REF_KERNEL is not defined"
#endif
#ifndef B6_REF_DTB
#error "B6_REF_DTB is not defined"
#endif

	.section .text.ref_stub, "ax", @progbits
	.globl	_start
	.type	_start, @function
_start:
	csrw	sie, zero
	csrw	satp, zero
	li	a0, 0
	li	a1, B6_REF_DTB
	li	t0, B6_REF_KERNEL
	jr	t0
	.size	_start, . - _start
