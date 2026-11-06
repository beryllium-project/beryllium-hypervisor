/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: U-Boot booti wrapper for the accepted K3 B2 image. A 64-byte
 *          Linux RISC-V Image header (Documentation/arch/riscv/
 *          boot-image-header.rst, as Linux arch/riscv/kernel/head.S without
 *          EFI) lets booti relocate the image to its RAM base plus
 *          text_offset (0x1_0220_0000 on the COM260). The stub then copies
 *          the embedded, byte-identical B2 flat image to the address it is
 *          linked for, 0x1_0200_0000, and enters be_reset there with
 *          U-Boot's a0 (hart ID) and a1 (FDT).
 * Contract: entered in S/HS mode (V=0) with satp Bare, a0 = boot hart ID,
 *          a1 = FDT physical address, as U-Boot boot_jump_linux() calls the
 *          kernel. Every image address is computed PC-relatively, so the
 *          image runs wherever booti places it. The destination and length
 *          come from the descriptor at offset 0x40, which the build fills
 *          from the linker script and tests/check-b3-image.py checks.
 * Trust:   no stack, no trap vector, and no memory access before the hart
 *          check. sp, gp, and tp are left untouched, so an unexpected trap
 *          still reaches U-Boot's handler. The only SBI calls are DBCN
 *          console write and SRST shutdown.
 * Scope:   hart 0 copies, reports one line, and jumps. Any other hart parks
 *          in wfi. If the running image overlaps the destination, the stub
 *          reports the failure and requests SRST shutdown; it never jumps.
 */

	.option norvc
	.option norelax

#ifndef BE_B3_TEXT_OFFSET
#error "BE_B3_TEXT_OFFSET must be defined"
#endif
#ifndef BE_B3_PAYLOAD
#error "BE_B3_PAYLOAD must name the accepted B2 flat image"
#endif

/* B2 is linked at 0x1_0200_0000 (bringup/k3-b2/README.md). */
#define BE_B3_DEST		0x102000000
#define SSTATUS_SIE		0x2
#define SBI_EID_DBCN		0x4442434e
#define SBI_DBCN_WRITE		0
#define SBI_EID_SRST		0x53525354
#define SBI_SRST_RESET		0
#define SBI_SRST_SHUTDOWN	0
#define SBI_SRST_NO_REASON	0
#define DBCN_ATTEMPTS		64
#define ASCII_NEWLINE		0x0a
#define ASCII_ZERO		0x30
#define ASCII_A_MINUS_10	0x57

	.section .text.be_b3_head, "ax", @progbits
	.globl be_b3_head
	.type be_b3_head, @function
be_b3_head:
	/* code0: jump over the header and descriptor; code1: zero. */
	j	be_b3_entry
	.word	0
	/* text_offset: booti places the image at its RAM base plus this. */
	.dword	BE_B3_TEXT_OFFSET
	/* image_size: every byte of the image, all of which booti moves. */
	.dword	__be_b3_image_size
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
	.size be_b3_head, . - be_b3_head

	/* Descriptor: magic, destination, length, payload offset. */
	.balign 8
	.globl be_b3_descriptor
	.type be_b3_descriptor, @object
be_b3_descriptor:
	.ascii	"BEK3B3D1"
	.dword	BE_B3_DEST
	.dword	__be_b3_payload_size
	.dword	__be_b3_payload_offset
	.size be_b3_descriptor, . - be_b3_descriptor

	.balign 4
	.globl be_b3_entry
	.type be_b3_entry, @function
be_b3_entry:
	/* No supervisor interrupt is taken from here on. */
	csrci	sstatus, SSTATUS_SIE
	/* U-Boot's arguments, kept in callee-saved registers for be_reset. */
	mv	s2, a0
	mv	s3, a1
	/* Only hart 0 continues; any other hart parks without a data access. */
	bnez	s2, be_b3_park

	/* s4/s5: the running image; s6/s7: destination and length. */
	lla	s4, be_b3_head
	lla	s5, __be_b3_image_end
	lla	t0, be_b3_descriptor
	ld	s6, 8(t0)
	ld	s7, 16(t0)
	ld	t1, 24(t0)
	/* s8: the payload in the running image; s9: destination end. */
	add	s8, s4, t1
	add	s9, s6, s7

	/* Disjoint when start >= dest end or dest >= end; otherwise refuse. */
	bgeu	s4, s9, 1f
	bgeu	s6, s5, 1f
	j	be_b3_fail_overlap
1:
	/* Copy eight bytes at a time; the linker script fixes the alignment. */
	mv	t0, s8
	mv	t1, s6
2:
	bgeu	t1, s9, 3f
	ld	t2, 0(t0)
	sd	t2, 0(t1)
	addi	t0, t0, 8
	addi	t1, t1, 8
	j	2b
3:
	fence	rw, rw
	fence.i

	/* One line: the handoff values, the running base, and the copy. */
	mv	a0, s2
	lla	a1, be_b3_shim_hart
	jal	be_b3_hex64
	mv	a0, s4
	lla	a1, be_b3_shim_base
	jal	be_b3_hex64
	mv	a0, s3
	lla	a1, be_b3_shim_fdt
	jal	be_b3_hex64
	mv	a0, s6
	lla	a1, be_b3_shim_dest
	jal	be_b3_hex64
	mv	a0, s7
	lla	a1, be_b3_shim_bytes
	jal	be_b3_hex64
	lla	a0, be_b3_shim_line
	lla	a1, be_b3_shim_line_end
	jal	be_b3_print

	/* Enter the accepted B2 be_reset with U-Boot's arguments. */
	mv	a0, s2
	mv	a1, s3
	jr	s6
	.size be_b3_entry, . - be_b3_entry

	.type be_b3_fail_overlap, @function
be_b3_fail_overlap:
	mv	a0, s4
	lla	a1, be_b3_fail_base
	jal	be_b3_hex64
	lla	a0, be_b3_fail_line
	lla	a1, be_b3_fail_line_end
	jal	be_b3_print
	li	a0, SBI_SRST_SHUTDOWN
	li	a1, SBI_SRST_NO_REASON
	li	a6, SBI_SRST_RESET
	li	a7, SBI_EID_SRST
	ecall
	/* SRST returned: fall through and park like a secondary hart. */
	.size be_b3_fail_overlap, . - be_b3_fail_overlap

	.type be_b3_park, @function
be_b3_park:
	wfi
	j	be_b3_park
	.size be_b3_park, . - be_b3_park

	/*
	 * be_b3_hex64: write a0 as 16 lowercase hex digits at a1.
	 * Clobbers a0, a1, t0-t3.
	 */
	.type be_b3_hex64, @function
be_b3_hex64:
	li	t0, 16
	li	t3, 10
1:
	srli	t1, a0, 60
	bltu	t1, t3, 2f
	addi	t1, t1, ASCII_A_MINUS_10
	j	3f
2:
	addi	t1, t1, ASCII_ZERO
3:
	sb	t1, 0(a1)
	slli	a0, a0, 4
	addi	a1, a1, 1
	addi	t0, t0, -1
	bnez	t0, 1b
	ret
	.size be_b3_hex64, . - be_b3_hex64

	/*
	 * be_b3_print: write [a0, a1) with SBI DBCN console write, accepting
	 * partial progress for at most DBCN_ATTEMPTS calls. An SBI error or a
	 * malformed count ends the line early, which fails the capture check.
	 * Clobbers a0-a2, a6, a7, t0-t2. SBI preserves every other register.
	 */
	.type be_b3_print, @function
be_b3_print:
	mv	t0, a0
	sub	t1, a1, a0
	li	t2, DBCN_ATTEMPTS
1:
	beqz	t1, 2f
	beqz	t2, 2f
	addi	t2, t2, -1
	mv	a0, t1
	mv	a1, t0
	li	a2, 0
	li	a6, SBI_DBCN_WRITE
	li	a7, SBI_EID_DBCN
	ecall
	bnez	a0, 2f
	bgtu	a1, t1, 2f
	add	t0, t0, a1
	sub	t1, t1, a1
	j	1b
2:
	ret
	.size be_b3_print, . - be_b3_print

	/* Report lines, formatted in place; '?' marks an unformatted digit. */
	.section .data.be_b3, "aw", @progbits
	.balign 8
be_b3_shim_line:
	.ascii	"BE_K3_B3: SHIM hart=0x"
be_b3_shim_hart:
	.ascii	"????????????????"
	.ascii	" shim=0x"
be_b3_shim_base:
	.ascii	"????????????????"
	.ascii	" fdt=0x"
be_b3_shim_fdt:
	.ascii	"????????????????"
	.ascii	" dest=0x"
be_b3_shim_dest:
	.ascii	"????????????????"
	.ascii	" bytes=0x"
be_b3_shim_bytes:
	.ascii	"????????????????"
	.byte	ASCII_NEWLINE
be_b3_shim_line_end:

be_b3_fail_line:
	.ascii	"BE_K3_B3: FAIL overlap shim=0x"
be_b3_fail_base:
	.ascii	"????????????????"
	.byte	ASCII_NEWLINE
be_b3_fail_line_end:

	/* The accepted B2 flat image, byte for byte. */
	.section .payload.be_b3, "a", @progbits
	.balign 4096
	.globl be_b3_payload
be_b3_payload:
	.incbin	BE_B3_PAYLOAD
