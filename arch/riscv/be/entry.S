/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: pinned OpenSBI S/HS handoff and freestanding C initialization for
 *          the bounded Beryllium R3 image.
 * Trust:   reset assembly boundary. OpenSBI supplies a0/a1; a1 is forwarded
 *          only as an opaque recorded scalar and is never dereferenced.
 * Scope:   R3 boot only. No secondary hart, parser, trap frame, or recovery.
 */

	.option norvc

	.section .text.be.entry, "ax"
	.align 4
	.globl be_reset
	.type be_reset, @function
be_reset:
	/* Preserve the OpenSBI handoff while zeroing the exact linked BSS. */
	mv	s0, a0
	mv	s1, a1
	la	t0, __be_bss_start
	la	t1, __be_bss_end
1:
	bgeu	t0, t1, 2f
	sd	zero, 0(t0)
	addi	t0, t0, 8
	j	1b
2:
	/* The initial trusted stack is the exclusive accepted management top. */
	la	sp, __be_stack_management_end
	mv	a0, s0
	mv	a1, s1
	call	be_r3_runtime_main

	/* A returning C entry violates the R3 terminal contract. */
	tail	be_r3_arch_halt
	.size be_reset, . - be_reset
