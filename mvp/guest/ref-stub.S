/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: OpenSBI's next stage in the MVP guests' QEMU reference boots
 *          (planning/mvp-m0-plan.md, Guest software; B7's guest/ref-stub.S
 *          with MVP names): enter the pinned Image at MVP_REF_KERNEL in S-mode
 *          with a0 = 0 (hart 0), a1 = MVP_REF_DTB (a guest's reference DTB),
 *          and satp = 0, in place of the MVP monitor's first entry. OpenSBI
 *          itself keeps QEMU's DTB for its console and reset devices. Both
 *          guests' reference DTBs load at the same address, so one stub
 *          serves G0 and G1.
 * Trust:   test scaffolding; no monitor runs in the reference boot.
 * Scope:   QEMU only. guest.mk builds it with the two addresses that
 *          scripts/gen-dts.py derives, and scripts/run-reference-boot.sh
 *          loads it with -kernel.
 */

#ifndef MVP_REF_KERNEL
#error "MVP_REF_KERNEL is not defined"
#endif
#ifndef MVP_REF_DTB
#error "MVP_REF_DTB is not defined"
#endif

	.section .text.ref_stub, "ax", @progbits
	.globl	_start
	.type	_start, @function
_start:
	csrw	sie, zero
	csrw	satp, zero
	li	a0, 0
	li	a1, MVP_REF_DTB
	li	t0, MVP_REF_KERNEL
	jr	t0
	.size	_start, . - _start
