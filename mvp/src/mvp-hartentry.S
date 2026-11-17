/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP hart entry, where HSM hart_start delivers each domain hart,
 *          and the image's one fence.i, which each domain hart executes
 *          after its install readback (planning/mvp-m0-plan.md, "Domain
 *          hart entry and fast path").
 * Contract: entered in HS (V=0) with satp Bare, sstatus.SIE 0, sie 0, and
 *          stvec here, as OpenSBI's hart_start leaves a started hart, with
 *          a0 = the hart's ID and a1 = the opaque word hart 0 passed: its
 *          block in the hart region.
 * Trust:   no memory access before sp holds the block's trusted-stack top,
 *          and a1 must name one of the region's blocks first, by arithmetic
 *          alone; anything else parks the hart without a stack. C then
 *          checks the published block before the hart touches anything else.
 * Scope:   the MVP line's domain harts. Hart 0 never comes here.
 *
 * In a boundary-on image (M11-7; planning/mvp-m11-plan.md, D-6 step 5)
 * hart 0 starts each VS-domain hart at be_mvp_confine_entry instead, in the
 * boot OpenSBI domain, with the same a1. It checks a1 and sets sp exactly
 * as the hart entry does, then makes the domain commit extension's confine
 * call, which on success enters the hart's narrow OpenSBI domain at its
 * confined entry, be_mvp_hart_entry, with the same a0 and a1, and does not
 * return. A refused or failed call, or a block that is not one of the two,
 * parks the hart in HS mode, having entered no guest.
 */

#include "mvp-layout.h"

	.option norvc

	.section .text.mvp.domain, "ax"
	.align 4
	.globl be_mvp_hart_entry
	.type be_mvp_hart_entry, @function
be_mvp_hart_entry:
	/* a1 must be exactly one of the two private-state extent bases. */
	li	t0, BE_MVP_G0_BLOCK_HPA
	beq	a1, t0, 2f
	li	t0, BE_MVP_G1_BLOCK_HPA
	bne	a1, t0, 1f
2:
	/* The trusted stack grows down from the saved page. */
	li	t2, BE_MVP_BLOCK_STACK_TOP_OFFSET
	add	sp, a1, t2
	call	be_mvp_hart_main
1:
	/* No block, or a return the hart's C never makes. */
	tail	be_mvp_arch_park
	.size be_mvp_hart_entry, . - be_mvp_hart_entry

	/*
	 * The image's one fence.i: after hart 0's data fence and the barrier's
	 * publication, and this hart's acquisition of it, this hart's fetches
	 * through the G-stage observe the kernel hart 0 placed.
	 */
	.align 4
	.globl be_mvp_arch_fence_i
	.type be_mvp_arch_fence_i, @function
be_mvp_arch_fence_i:
	fence.i
	ret
	.size be_mvp_arch_fence_i, . - be_mvp_arch_fence_i

	.section .text.mvp.boot, "ax"
	.align 4
	.globl be_mvp_park_entry
	.type be_mvp_park_entry, @function
be_mvp_park_entry:
1:
	wfi
	j	1b
	.size be_mvp_park_entry, . - be_mvp_park_entry

#if defined(BE_MVP_BOUNDARY)
	.section .text.mvp.confine, "ax"
	.align 4
	.globl be_mvp_confine_entry
	.type be_mvp_confine_entry, @function
be_mvp_confine_entry:
	/* a1 must be exactly one of the two private-state extent bases. */
	li	t0, BE_MVP_G0_BLOCK_HPA
	beq	a1, t0, 2f
	li	t0, BE_MVP_G1_BLOCK_HPA
	bne	a1, t0, 1f
2:
	/* The block's trusted stack, as the hart entry sets it. */
	li	t2, BE_MVP_BLOCK_STACK_TOP_OFFSET
	add	sp, a1, t2
	call	be_mvp_exec_confine
1:
	/* Refused, or no block: park in HS mode, having entered no guest. */
	tail	be_mvp_arch_park
	.size be_mvp_confine_entry, . - be_mvp_confine_entry
#endif
