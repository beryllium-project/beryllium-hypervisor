/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: preserve the fixed OpenSBI handoff and transfer control to R5.
 * Trust:   reset boundary; a0/a1 are retained as opaque scalar inputs only.
 * Scope:   one fixed image entry. No secondary hart or recovery path exists.
 */

	.option norvc

	.section .text.be.r5.entry, "ax"
	.align 4
	.globl be_reset
	.type be_reset, @function
be_reset:
	/* Preserve OpenSBI a0/a1 while clearing exactly the linked R5 BSS. */
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
	la	sp, __be_stack_management_end
	mv	a0, s0
	mv	a1, s1
	call	be_r5_runtime_main

	/* Returning would bypass the R5 terminal disposition. */
	tail	be_r5_arch_halt
	.size be_reset, . - be_reset
