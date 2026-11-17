/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: the hostile-monitor hook's privileged helpers (M11-7;
 *          planning/mvp-m11-plan.md, D-10): its entry, which saves the
 *          registers the attempts change and installs the hook's vector;
 *          the translation an attempt runs under; one attempt; the leave,
 *          which restores what the entry saved; and the hook's vector,
 *          which records an attempt's trap in its slot and resumes after
 *          it.
 * Trust:   test code, linked into the breach images alone; each helper is
 *          called only by its executor function (mvp-executor.c's
 *          be_mvp_exec_breach_*), and holds every instruction of its kind
 *          that the hook makes (tests/check-image.py's breach rule set).
 *          An attempt uses t3 to t6 and a3 to a7; the vector uses t0 to t2
 *          alone, so an attempt's slot (t4), frame (t5), and value (t6)
 *          survive its trap.
 * Scope:   the breach images (BE_MVP_BREACH); in the control role
 *          (BE_MVP_BREACH_CONTROL, M11-8), in a section of their own, which
 *          mvp-monitor.lds places in the MVP control text.
 */

#include "mvp-breach.h"

	.attribute arch, "rv64imach_zicsr_zifencei"
	.option norvc

	.equ MVP_BREACH_HSTATUS_SPVP, 0x100

#if defined(BE_MVP_BREACH_CONTROL)
	.section .text.mvp.breach.control, "ax"
#else
	.section .text.mvp.breach, "ax"
#endif

/* be_mvp_breach_arch_enter(saved a0, frame a1) */
	.align 2
	.globl be_mvp_breach_arch_enter
	.type be_mvp_breach_arch_enter, @function
be_mvp_breach_arch_enter:
	csrr	t0, stvec
	sd	t0, BE_MVP_BREACH_SAVED_STVEC(a0)
	csrr	t0, sscratch
	sd	t0, BE_MVP_BREACH_SAVED_SSCRATCH(a0)
	csrr	t0, sepc
	sd	t0, BE_MVP_BREACH_SAVED_SEPC(a0)
	csrr	t0, sstatus
	sd	t0, BE_MVP_BREACH_SAVED_SSTATUS(a0)
	csrr	t0, satp
	sd	t0, BE_MVP_BREACH_SAVED_SATP(a0)
	.option push
	.option arch, +h
	csrr	t0, hstatus
	sd	t0, BE_MVP_BREACH_SAVED_HSTATUS(a0)
	csrr	t0, hgatp
	sd	t0, BE_MVP_BREACH_SAVED_HGATP(a0)
	csrr	t0, vsatp
	sd	t0, BE_MVP_BREACH_SAVED_VSATP(a0)
	/* An H load or store acts as VS mode. */
	li	t0, MVP_BREACH_HSTATUS_SPVP
	csrs	hstatus, t0
	.option pop
	csrw	sscratch, a1
	la	t0, be_mvp_breach_arch_vector
	csrw	stvec, t0
	ret
	.size be_mvp_breach_arch_enter, . - be_mvp_breach_arch_enter

/* be_mvp_breach_arch_translate(satp a0, hgatp a1, vsatp a2) */
	.align 2
	.globl be_mvp_breach_arch_translate
	.type be_mvp_breach_arch_translate, @function
be_mvp_breach_arch_translate:
	csrw	satp, a0
	.option push
	.option arch, +h
	csrw	hgatp, a1
	csrw	vsatp, a2
	sfence.vma	zero, zero
	hfence.gvma	zero, zero
	hfence.vvma	zero, zero
	.option pop
	ret
	.size be_mvp_breach_arch_translate, . - be_mvp_breach_arch_translate

/*
 * be_mvp_breach_arch_attempt(row a0, slot a1, frame a2): the row's one
 * access or call. The slot's value word holds the sentinel on entry; it
 * keeps the value an access read, which a trapped access leaves as it
 * was. The frame names the slot and the continuation before the attempt,
 * and no continuation after it.
 */
	.align 2
	.globl be_mvp_breach_arch_attempt
	.type be_mvp_breach_arch_attempt, @function
be_mvp_breach_arch_attempt:
	mv	t4, a1
	mv	t5, a2
	ld	t6, BE_MVP_BREACH_SLOT_VALUE(t4)
	ld	a3, BE_MVP_BREACH_ROW_ADDRESS(a0)
	ld	a4, BE_MVP_BREACH_ROW_VALUE(a0)
	ld	a5, BE_MVP_BREACH_ROW_EXTRA(a0)
	ld	a6, BE_MVP_BREACH_ROW_CALL(a0)
	ld	t3, BE_MVP_BREACH_ROW_KIND(a0)
	sd	t4, BE_MVP_BREACH_FRAME_SLOT(t5)
	la	a7, .Lattempt_done
	sd	a7, BE_MVP_BREACH_FRAME_CONTINUE(t5)
	srli	a7, t3, 16
	andi	a7, a7, 0xff
	andi	t3, t3, 0xff
	li	a0, BE_MVP_BREACH_OP_LOAD
	beq	a7, a0, .Lload
	li	a0, BE_MVP_BREACH_OP_STORE
	beq	a7, a0, .Lstore
	li	a0, BE_MVP_BREACH_OP_JUMP
	beq	a7, a0, .Ljump
	li	a0, BE_MVP_BREACH_OP_AMOADD
	beq	a7, a0, .Lamoadd
	li	a0, BE_MVP_BREACH_OP_LRSC
	beq	a7, a0, .Llrsc
	li	a0, BE_MVP_BREACH_OP_CBO_ZERO
	beq	a7, a0, .Lcbo_zero
	li	a0, BE_MVP_BREACH_OP_CBO_INVAL
	beq	a7, a0, .Lcbo_inval
	li	a0, BE_MVP_BREACH_OP_HLV
	beq	a7, a0, .Lhlv
	li	a0, BE_MVP_BREACH_OP_HSV
	beq	a7, a0, .Lhsv
	li	a0, BE_MVP_BREACH_OP_ECALL
	beq	a7, a0, .Lecall
	/* An operation the table cannot hold: its slot says so. */
	sd	a7, BE_MVP_BREACH_SLOT_ERROR(t4)
	j	.Lattempt_done
.Lload:
	li	a0, 1
	beq	t3, a0, .Lload_byte
	li	a0, 4
	beq	t3, a0, .Lload_word
	ld	t6, 0(a3)
	j	.Lattempt_done
.Lload_byte:
	lbu	t6, 0(a3)
	j	.Lattempt_done
.Lload_word:
	lwu	t6, 0(a3)
	j	.Lattempt_done
.Lstore:
	li	a0, 1
	beq	t3, a0, .Lstore_byte
	li	a0, 4
	beq	t3, a0, .Lstore_word
	sd	a4, 0(a3)
	j	.Lattempt_done
.Lstore_byte:
	sb	a4, 0(a3)
	j	.Lattempt_done
.Lstore_word:
	sw	a4, 0(a3)
	j	.Lattempt_done
.Ljump:
	/* The only link register an attempt names: t3. */
	jalr	t3, 0(a3)
	j	.Lattempt_done
.Lamoadd:
	amoadd.d	t6, a4, (a3)
	j	.Lattempt_done
.Llrsc:
	lr.d	t6, (a3)
	sc.d	t3, a4, (a3)
	sd	t3, BE_MVP_BREACH_SLOT_ERROR(t4)
	j	.Lattempt_done
.Lcbo_zero:
	/* cbo.zero (a3) */
	.insn	i 0x0f, 2, x0, a3, 4
	j	.Lattempt_done
.Lcbo_inval:
	/* cbo.inval (a3) */
	.insn	i 0x0f, 2, x0, a3, 0
	j	.Lattempt_done
.Lhlv:
	.option push
	.option arch, +h
	hlv.d	t6, (a3)
	.option pop
	j	.Lattempt_done
.Lhsv:
	.option push
	.option arch, +h
	hsv.d	a4, (a3)
	.option pop
	j	.Lattempt_done
.Lecall:
	mv	a0, a3
	mv	a1, a4
	mv	a2, a5
	srli	a7, a6, 32
	slli	a6, a6, 32
	srli	a6, a6, 32
	ecall
	sd	a0, BE_MVP_BREACH_SLOT_ERROR(t4)
	mv	t6, a1
.Lattempt_done:
	sd	t6, BE_MVP_BREACH_SLOT_VALUE(t4)
	sd	zero, BE_MVP_BREACH_FRAME_CONTINUE(t5)
	ret
	.size be_mvp_breach_arch_attempt, . - be_mvp_breach_arch_attempt

/* be_mvp_breach_arch_leave(saved a0): the registers enter saved. */
	.align 2
	.globl be_mvp_breach_arch_leave
	.type be_mvp_breach_arch_leave, @function
be_mvp_breach_arch_leave:
	ld	t0, BE_MVP_BREACH_SAVED_STVEC(a0)
	csrw	stvec, t0
	ld	t0, BE_MVP_BREACH_SAVED_SSCRATCH(a0)
	csrw	sscratch, t0
	ld	t0, BE_MVP_BREACH_SAVED_SEPC(a0)
	csrw	sepc, t0
	ld	t0, BE_MVP_BREACH_SAVED_SSTATUS(a0)
	csrw	sstatus, t0
	.option push
	.option arch, +h
	ld	t0, BE_MVP_BREACH_SAVED_HSTATUS(a0)
	csrw	hstatus, t0
	.option pop
	ret
	.size be_mvp_breach_arch_leave, . - be_mvp_breach_arch_leave

/*
 * The hook's vector, through sscratch's frame: a trap with a continuation
 * keeps its cause and stval in the frame's slot and resumes there, in HS
 * mode (the trap set SPP, and SPV to V's 0); a trap with none is
 * unexpected: its cause, sepc, and stval go into the frame, and the hart
 * parks here, so that its run fails.
 */
	.align 2
	.globl be_mvp_breach_arch_vector
	.type be_mvp_breach_arch_vector, @function
be_mvp_breach_arch_vector:
	csrr	t0, sscratch
	ld	t2, BE_MVP_BREACH_FRAME_CONTINUE(t0)
	beqz	t2, .Lvector_unexpected
	ld	t1, BE_MVP_BREACH_FRAME_SLOT(t0)
	csrw	sepc, t2
	csrr	t2, scause
	sd	t2, BE_MVP_BREACH_SLOT_CAUSE(t1)
	csrr	t2, stval
	sd	t2, BE_MVP_BREACH_SLOT_STVAL(t1)
	sret
.Lvector_unexpected:
	csrr	t2, scause
	sd	t2, BE_MVP_BREACH_FRAME_CAUSE(t0)
	csrr	t2, sepc
	sd	t2, BE_MVP_BREACH_FRAME_SEPC(t0)
	csrr	t2, stval
	sd	t2, BE_MVP_BREACH_FRAME_STVAL(t0)
1:
	wfi
	j	1b
	.size be_mvp_breach_arch_vector, . - be_mvp_breach_arch_vector
