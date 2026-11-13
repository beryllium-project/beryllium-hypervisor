/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jmorris@namei.org> */
/*
 * Purpose: the firmware tests' payload: its entry, its trap vector, the
 *          protected call that every step runs in, the entry to a guest
 *          (VS-mode or VU-mode), and the probe operations, the only code
 *          of the payload that runs in a guest.
 * Trust:   test-only. Every trap, from HS-mode or from a guest, ends the
 *          step in progress: the vector keeps the trap's CSRs in the
 *          hart's context and returns from the protected call with 1.
 * Scope:   RV64. A guest runs with hgatp and vsatp as the step left them
 *          (Bare in every test that enters one) and ends with an ecall.
 */
#include "fwtest.h"

#define CSR_HSTATUS	0x600
#define CSR_HTVAL	0x643
#define HSTATUS_SPV	0x80
#define HSTATUS_SPVP	0x100
#define SSTATUS_SPP	0x100

	.section .text.entry, "ax"
	.globl	_start
_start:
	/* a0: hart ID, a1: opaque. Keep four CSRs as the firmware left them */
	csrr	a2, stvec
	csrr	a3, sscratch
	csrr	a4, sie
	csrr	a5, satp
	li	t0, FWT_STATE_STRIDE
	mul	t0, a0, t0
	li	t1, FWT_STATE_BASE
	add	t0, t0, t1
	li	t1, FWT_STATE_STRIDE
	add	sp, t0, t1
	li	t1, FWT_CTX_BYTE_OFF
	add	t1, t0, t1
	csrw	sscratch, t1
	la	t1, fwt_trap
	csrw	stvec, t1
	call	fwt_main
1:	wfi
	j	1b

	.text
	.align	2
fwt_trap:
	csrrw	t6, sscratch, t6
	sd	a0, FWT_CTX_A0(t6)
	csrr	t0, scause
	sd	t0, FWT_CTX_CAUSE(t6)
	csrr	t0, stval
	sd	t0, FWT_CTX_TVAL(t6)
	csrr	t0, sepc
	sd	t0, FWT_CTX_EPC(t6)
	csrr	t0, CSR_HSTATUS
	sd	t0, FWT_CTX_HSTATUS(t6)
	csrr	t0, CSR_HTVAL
	sd	t0, FWT_CTX_HTVAL(t6)
	/* Back to the caller of fwt_protected, in HS-mode */
	ld	sp, FWT_CTX_SP(t6)
	ld	ra, FWT_CTX_RA(t6)
	ld	s0, FWT_CTX_S0 + 0(t6)
	ld	s1, FWT_CTX_S0 + 8(t6)
	ld	s2, FWT_CTX_S0 + 16(t6)
	ld	s3, FWT_CTX_S0 + 24(t6)
	ld	s4, FWT_CTX_S0 + 32(t6)
	ld	s5, FWT_CTX_S0 + 40(t6)
	ld	s6, FWT_CTX_S0 + 48(t6)
	ld	s7, FWT_CTX_S0 + 56(t6)
	ld	s8, FWT_CTX_S0 + 64(t6)
	ld	s9, FWT_CTX_S0 + 72(t6)
	ld	s10, FWT_CTX_S0 + 80(t6)
	ld	s11, FWT_CTX_S0 + 88(t6)
	li	t0, HSTATUS_SPV
	csrc	CSR_HSTATUS, t0
	li	t0, SSTATUS_SPP
	csrs	sstatus, t0
	la	t0, fwt_trapped
	csrw	sepc, t0
	csrw	sscratch, t6
	sret

fwt_trapped:
	li	a0, 1
	ret

	/* long fwt_protected(void (*fn)(u64 *), u64 *job): 0, or 1 on a trap */
	.globl	fwt_protected
fwt_protected:
	csrr	t0, sscratch
	sd	sp, FWT_CTX_SP(t0)
	sd	ra, FWT_CTX_RA(t0)
	sd	s0, FWT_CTX_S0 + 0(t0)
	sd	s1, FWT_CTX_S0 + 8(t0)
	sd	s2, FWT_CTX_S0 + 16(t0)
	sd	s3, FWT_CTX_S0 + 24(t0)
	sd	s4, FWT_CTX_S0 + 32(t0)
	sd	s5, FWT_CTX_S0 + 40(t0)
	sd	s6, FWT_CTX_S0 + 48(t0)
	sd	s7, FWT_CTX_S0 + 56(t0)
	sd	s8, FWT_CTX_S0 + 64(t0)
	sd	s9, FWT_CTX_S0 + 72(t0)
	sd	s10, FWT_CTX_S0 + 80(t0)
	sd	s11, FWT_CTX_S0 + 88(t0)
	addi	sp, sp, -16
	sd	ra, 0(sp)
	mv	t1, a0
	mv	a0, a1
	jalr	t1
	ld	ra, 0(sp)
	addi	sp, sp, 16
	li	a0, 0
	ret

	/*
	 * void fwt_guest(u64 op, u64 addr, u64 arg, u64 mode): run fwt_probe
	 * in VS-mode or VU-mode. The guest's ecall at fwt_guest_done, or any
	 * trap on the way, returns from the enclosing fwt_protected.
	 */
	.globl	fwt_guest
fwt_guest:
	li	t0, HSTATUS_SPVP
	csrc	CSR_HSTATUS, t0
	li	t0, HSTATUS_SPV
	csrs	CSR_HSTATUS, t0
	li	t0, SSTATUS_SPP
	csrc	sstatus, t0
	li	t1, FWT_MODE_VS
	bne	a3, t1, 1f
	li	t0, HSTATUS_SPVP
	csrs	CSR_HSTATUS, t0
	li	t0, SSTATUS_SPP
	csrs	sstatus, t0
1:	la	t0, fwt_probe
	csrw	sepc, t0
	la	ra, fwt_guest_done
	sret

	.globl	fwt_guest_done
fwt_guest_done:
	ecall
1:	j	1b

	/* u64 fwt_probe(u64 op, u64 addr, u64 arg): one operation */
	.globl	fwt_probe
fwt_probe:
	li	t0, FWT_OP_LOAD
	beq	a0, t0, .Lload
	li	t0, FWT_OP_STORE
	beq	a0, t0, .Lstore
	li	t0, FWT_OP_FETCH
	beq	a0, t0, .Lfetch
	li	t0, FWT_OP_CBO
	beq	a0, t0, .Lcbo
	li	t0, FWT_OP_AMO
	beq	a0, t0, .Lamo
	li	t0, FWT_OP_ILL32
	beq	a0, t0, .Lill32
	li	t0, FWT_OP_ILL16
	beq	a0, t0, .Lill16
	li	a0, -1
	ret
.Lload:
	li	t0, 4
	beq	a2, t0, 1f
	ld	a0, 0(a1)
	ret
1:	lw	a0, 0(a1)
	ret
.Lstore:
	sd	a2, 0(a1)
	li	a0, 0
	ret
.Lfetch:
	jr	a1
.Lcbo:
	/* cbo.inval (a1) */
	.insn	i 0x0f, 2, x0, 0(a1)
	li	a0, 0
	ret
.Lamo:
	amoadd.w a0, a2, (a1)
	ret
.Lill32:
	/* A 32-bit encoding in the custom-0 space, which this hart lacks */
	.word	0x0000000b
	ret
.Lill16:
	/* c.unimp */
	.hword	0x0000
	ret
