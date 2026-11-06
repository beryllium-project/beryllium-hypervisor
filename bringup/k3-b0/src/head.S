/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: Linux RISC-V Image header and position-independent HS entry for
 *          the K3 B0 / BE-K3-L0BOOT boot checkpoint.
 * Contract: entered in S/HS mode (V=0) with satp Bare, a0 = boot hart ID and
 *          a1 = FDT physical address, as provided by OpenSBI fw_dynamic,
 *          U-Boot booti, and Linux kexec. The image may be loaded at any
 *          4 KiB-aligned address: every reference here is PC-relative.
 * Scope:   entering hart only. Interrupt masking, fail-closed trap sink,
 *          BSS clearing, stack, C handoff, and halt. Ported from the accepted
 *          R3 entry (arch/riscv/be/entry.S), made relocatable for K3.
 */

	.option norvc

	.section .head.text, "ax"
	.globl be_b0_head
	.type be_b0_head, @function
be_b0_head:
	/* code0/code1: jump over the 64-byte header; no EFI stub. */
	j	be_b0_entry
	.word	0
	.balign 8
	/* text_offset: load 2 MiB above the start of RAM, as RV64 Linux. */
	.dword	0x200000
	/* image_size: full memory footprint including BSS and stack. */
	.dword	__be_b0_image_size
	/* flags: little-endian kernel. */
	.dword	0
	/* version 0.2, res1, res2 */
	.word	2
	.word	0
	.dword	0
	/* magic (deprecated) and magic2 */
	.ascii	"RISCV\0\0\0"
	.balign 4
	.ascii	"RSC\x05"
	/* res3: no PE/COFF header */
	.word	0
	.size be_b0_head, . - be_b0_head

	.section .text.be_b0_entry, "ax"
	.balign 4
	.globl be_b0_entry
	.type be_b0_entry, @function
be_b0_entry:
	/* Mask supervisor interrupts before anything else can run. */
	csrci	sstatus, 0x2
	csrw	sie, zero
	/* Replace any inherited trap vector with the fail-closed sink. */
	lla	t0, be_b0_trap_entry
	csrw	stvec, t0

	/* Preserve the handoff while zeroing the exact linked BSS. */
	mv	s0, a0
	mv	s1, a1
	lla	t0, __be_b0_bss_start
	lla	t1, __be_b0_bss_end
1:
	bgeu	t0, t1, 2f
	sd	zero, 0(t0)
	addi	t0, t0, 8
	j	1b
2:
	lla	sp, __be_b0_stack_end
	mv	a0, s0
	mv	a1, s1
	/* The runtime load base is the address of the image header. */
	lla	a2, be_b0_head
	call	be_b0_main

	/* be_b0_main is terminal; a return violates the B0 contract. */
	tail	be_b0_halt
	.size be_b0_entry, . - be_b0_entry

	.balign 4
	.globl be_b0_trap_entry
	.type be_b0_trap_entry, @function
be_b0_trap_entry:
	/*
	 * Any trap is terminal. Nothing is resumed, so the stack is reset to the
	 * exclusive top before the C reporter requests SRST shutdown.
	 */
	csrr	a0, scause
	csrr	a1, sepc
	csrr	a2, stval
	lla	sp, __be_b0_stack_end
	call	be_b0_trap
	tail	be_b0_halt
	.size be_b0_trap_entry, . - be_b0_trap_entry

	.balign 4
	.globl be_b0_halt
	.type be_b0_halt, @function
be_b0_halt:
	csrci	sstatus, 0x2
	csrw	sie, zero
1:
	wfi
	j	1b
	.size be_b0_halt, . - be_b0_halt
