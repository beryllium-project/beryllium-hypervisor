/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: the M13-4 probe images' boot path
 *          (planning/mvp-m13-3-review-point.md, section 3): a RISC-V Image
 *          header for U-Boot's booti, B3's field for field
 *          (bringup/k3-b3/src/b3-shim.S); the entry and its hart check; the
 *          entry hart's trap vector; the one routine that touches a device;
 *          the SBI calls (Base, DBCN write-byte, SRST); the park loop.
 * Contract: entered in HS-mode with satp Bare, a0 the hart and a1 the FDT, as
 *          booti and QEMU's OpenSBI enter an Image. Every address of the
 *          image's own is formed PC-relatively (lla), so it runs wherever
 *          it is placed.
 * Trust:   a device is touched only by be_m13_access, whose three access
 *          instructions take their address, width, and written value from
 *          the linked table, by an index below its length; a fault there is
 *          recorded and passed over, and any other trap ends the run. The
 *          CSRs written here are sstatus.SIE (cleared), sie (0), stvec, and
 *          sepc. Each SBI call is one routine's, its EID and FID set by li.
 */
#include "m13.h"

	.option norvc
	.option norelax

#define SSTATUS_SIE		0x2
#define CAUSE_LOAD_ACCESS	5
#define CAUSE_STORE_ACCESS	7
#define SBI_EID_BASE		0x10
#define SBI_EID_DBCN		0x4442434e
#define SBI_DBCN_WRITE_BYTE	2
#define SBI_EID_SRST		0x53525354
#define SBI_SRST_RESET		0
#define SBI_SRST_SHUTDOWN	0
#define SBI_SRST_NO_REASON	0

	.section .head.text, "ax", @progbits
	.globl be_m13_head
	.type be_m13_head, @function
be_m13_head:
	/* code0: a jump to the entry; code1: zero. */
	j	be_m13_entry
	.word	0
	/* text_offset: booti places the image at its RAM base plus this. */
	.dword	0x200000
	/* image_size: every byte of the image, all of which booti moves. */
	.dword	__be_m13_image_size
	/* flags: little-endian. */
	.dword	0
	/* version 0.2, res1, res2. */
	.word	2
	.word	0
	.dword	0
	/* magic (deprecated) "RISCV\0\0\0" and magic2 "RSC\x05". */
	.ascii	"RISCV"
	.byte	0, 0, 0
	.ascii	"RSC"
	.byte	0x05
	/* res3: no PE/COFF header. */
	.word	0
	/* Where B3's descriptor was: zero. The entry follows, at 0x60. */
	.space	0x20
	.size be_m13_head, . - be_m13_head

	.section .text.be_m13_entry, "ax", @progbits
	.balign 4
	.globl be_m13_entry
	.type be_m13_entry, @function
be_m13_entry:
	/* No S-level interrupt is taken from here on (B0's head.S:49-51). */
	csrci	sstatus, SSTATUS_SIE
	csrw	sie, zero
	lla	t0, be_m13_trap
	csrw	stvec, t0
	lla	sp, __be_m13_stack_end
	/* a2: where the image runs, its header's own address. */
	lla	a2, be_m13_head
	/* Rule 6: on a hart above 2, one line and SRST, before any read. */
	li	t0, 2
	bgtu	a0, t0, 1f
	call	be_m13_main
	j	be_m13_park
1:	call	be_m13_refuse
	j	be_m13_park
	.size be_m13_entry, . - be_m13_entry

	/*
	 * The entry hart's trap vector. A load access fault at one of the two
	 * load sites, or a store access fault at the store site, is recorded
	 * in be_m13_fault and passed over: be_m13_access returns status 1.
	 * Anything else ends the run: the stack is reset and
	 * be_m13_trap_fail prints FAIL trap and requests SRST. Only t0 to t2
	 * are clobbered before either; be_m13_access_fault needs none of them.
	 */
	.section .text.be_m13_trap, "ax", @progbits
	.balign 4
	.globl be_m13_trap
	.type be_m13_trap, @function
be_m13_trap:
	csrr	t0, sepc
	csrr	t1, scause
	lla	t2, be_m13_site_lw
	beq	t0, t2, 1f
	lla	t2, be_m13_site_ld
	beq	t0, t2, 1f
	lla	t2, be_m13_site_sw
	bne	t0, t2, 3f
	li	t2, CAUSE_STORE_ACCESS
	bne	t1, t2, 3f
	j	2f
1:	li	t2, CAUSE_LOAD_ACCESS
	bne	t1, t2, 3f
2:	lla	t2, be_m13_fault
	sd	t1, 0(t2)
	csrr	t1, stval
	sd	t1, 8(t2)
	lla	t1, be_m13_access_fault
	csrw	sepc, t1
	sret
3:	mv	a0, t1
	mv	a1, t0
	csrr	a2, stval
	lla	sp, __be_m13_stack_end
	call	be_m13_trap_fail
	j	be_m13_park
	.size be_m13_trap, . - be_m13_trap

	/*
	 * be_m13_access(index): the table's entry INDEX made, if it is a read
	 * or a write. Returns a0 = 0 (made), 1 (a fault at the site, its
	 * scause and stval in be_m13_fault), or 2 (refused: no such entry, an
	 * address not aligned to its width, another op, or a write of another
	 * width than 4), and a1 = the value read or written. The address and
	 * the value written are the table's; the caller gives the index alone.
	 */
	.section .text.be_m13_access, "ax", @progbits
	.balign 4
	.globl be_m13_access
	.type be_m13_access, @function
be_m13_access:
	lla	t0, be_m13_table
	lla	t1, be_m13_table_end
	sub	t1, t1, t0
	srli	t1, t1, BE_M13_ENTRY_SHIFT
	bgeu	a0, t1, 9f
	slli	t1, a0, BE_M13_ENTRY_SHIFT
	add	t0, t0, t1
	ld	t2, 0(t0)
	lbu	t3, 16(t0)
	lbu	t4, 17(t0)
	addi	t5, t4, -1
	and	t5, t5, t2
	bnez	t5, 9f
	li	t5, BE_M13_OP_READ
	beq	t3, t5, 1f
	li	t5, BE_M13_OP_WRITE
	bne	t3, t5, 9f
	li	t5, 4
	bne	t4, t5, 9f
	ld	a1, 8(t0)
	fence	iorw, iorw
be_m13_site_sw:
	sw	a1, 0(t2)
	fence	iorw, iorw
	li	a0, BE_M13_MADE
	ret
1:	li	t5, 8
	beq	t4, t5, 2f
	li	t5, 4
	bne	t4, t5, 9f
	fence	iorw, iorw
be_m13_site_lw:
	lwu	a1, 0(t2)
	fence	iorw, iorw
	li	a0, BE_M13_MADE
	ret
2:	fence	iorw, iorw
be_m13_site_ld:
	ld	a1, 0(t2)
	fence	iorw, iorw
	li	a0, BE_M13_MADE
	ret
be_m13_access_fault:
	li	a0, BE_M13_FAULTED
	li	a1, 0
	ret
9:	li	a0, BE_M13_REFUSED_INDEX
	li	a1, 0
	ret
	.size be_m13_access, . - be_m13_access

	.section .text.be_m13_sbi, "ax", @progbits
	/* be_m13_sbi_base(fid, arg): a Base query; a0 error, a1 value. */
	.balign 4
	.globl be_m13_sbi_base
	.type be_m13_sbi_base, @function
be_m13_sbi_base:
	mv	a6, a0
	mv	a0, a1
	li	a7, SBI_EID_BASE
be_m13_ecall_base:
	ecall
	ret
	.size be_m13_sbi_base, . - be_m13_sbi_base

	/* be_m13_putc(byte): DBCN write-byte; a0 error. No memory is read. */
	.balign 4
	.globl be_m13_putc
	.type be_m13_putc, @function
be_m13_putc:
	andi	a0, a0, 0xff
	li	a6, SBI_DBCN_WRITE_BYTE
	li	a7, SBI_EID_DBCN
be_m13_ecall_dbcn:
	ecall
	ret
	.size be_m13_putc, . - be_m13_putc

	/* be_m13_srst(): SRST shutdown. If it returns, park, printing nothing. */
	.balign 4
	.globl be_m13_srst
	.type be_m13_srst, @function
be_m13_srst:
	li	a0, SBI_SRST_SHUTDOWN
	li	a1, SBI_SRST_NO_REASON
	li	a6, SBI_SRST_RESET
	li	a7, SBI_EID_SRST
be_m13_ecall_srst:
	ecall
	j	be_m13_park
	.size be_m13_srst, . - be_m13_srst

	.balign 4
	.globl be_m13_park
	.type be_m13_park, @function
be_m13_park:
	wfi
	j	be_m13_park
	.size be_m13_park, . - be_m13_park

	.balign 4
	.globl be_m13_read_satp
	.type be_m13_read_satp, @function
be_m13_read_satp:
	csrr	a0, satp
	ret
	.size be_m13_read_satp, . - be_m13_read_satp

	.section .data.be_m13_fault, "aw", @progbits
	.balign 8
	.globl be_m13_fault
	.type be_m13_fault, @object
be_m13_fault:
	.dword	0, 0
	.size be_m13_fault, . - be_m13_fault

	/* The entry hart's stack, 8 KiB, which ends the image (m13.lds). */
	.section .be_m13_stack, "aw", @progbits
	.balign 4096
	.space	0x2000
