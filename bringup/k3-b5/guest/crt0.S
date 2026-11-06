/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: entry and trap stub of the K3 B5 test guest.
 * Contract: the monitor enters at GPA 0x4001_0000 in VS mode with a0 = 0
 *          (hart 0), a1 = 0 (no device tree), sp = 0x4000_1000, every other
 *          GPR zero, vsstatus = 0, and Bare vsatp.
 * Trust:   untrusted VS code. The only trap the monitor delegates to it is
 *          the VS timer interrupt.
 * Scope:   B5 guest only (planning/k3-b5-plan.md).
 */

	.section .text.entry, "ax"
	.globl _start
	.type _start, @function
_start:
	/* Clear BSS, keeping a0/a1 for guest_main(hart, dtb). */
	la	t0, __bss_start
	la	t1, __bss_end
1:
	bgeu	t0, t1, 2f
	sd	zero, 0(t0)
	addi	t0, t0, 8
	j	1b
2:
	la	t0, guest_trap_entry
	csrw	stvec, t0
	call	guest_main
	/* guest_main ends with an SRST shutdown; reaching here is terminal. */
	unimp
	.size _start, . - _start

	/* Direct-mode stvec: four-byte aligned. */
	.text
	.align 2
	.globl guest_trap_entry
	.type guest_trap_entry, @function
guest_trap_entry:
	addi	sp, sp, -128
	sd	ra, 0(sp)
	sd	t0, 8(sp)
	sd	t1, 16(sp)
	sd	t2, 24(sp)
	sd	a0, 32(sp)
	sd	a1, 40(sp)
	sd	a2, 48(sp)
	sd	a3, 56(sp)
	sd	a4, 64(sp)
	sd	a5, 72(sp)
	sd	a6, 80(sp)
	sd	a7, 88(sp)
	sd	t3, 96(sp)
	sd	t4, 104(sp)
	sd	t5, 112(sp)
	sd	t6, 120(sp)
	csrr	a0, scause
	call	guest_trap
	ld	ra, 0(sp)
	ld	t0, 8(sp)
	ld	t1, 16(sp)
	ld	t2, 24(sp)
	ld	a0, 32(sp)
	ld	a1, 40(sp)
	ld	a2, 48(sp)
	ld	a3, 56(sp)
	ld	a4, 64(sp)
	ld	a5, 72(sp)
	ld	a6, 80(sp)
	ld	a7, 88(sp)
	ld	t3, 96(sp)
	ld	t4, 104(sp)
	ld	t5, 112(sp)
	ld	t6, 120(sp)
	addi	sp, sp, 128
	sret
	.size guest_trap_entry, . - guest_trap_entry
