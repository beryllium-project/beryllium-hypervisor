/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B5 VS-exit vector, no-call resume tail, guest-control arm
 *          helpers, and the SBI TIME vstimecmp write.
 * Trust:   sole B5 CSR boundary after the accepted R3 reset. The vector
 *          saves the accepted 320-byte struct be_r4_frame to the management
 *          saved page, selected by the trusted-stack identity alone, and
 *          writes neither hie nor hvip (hie.VSTIE is the guest's vsie.STIE).
 *          The resume tail checks every guest control and writes no vs* CSR,
 *          hgatp, or fence. Nothing here dereferences a guest address.
 * Scope:   one management guest on hart 0 (planning/k3-b5-plan.md). No HS
 *          interrupt path, hvip injection, root switch, or second domain.
 */

	.attribute arch, "rv64imach_zicsr_zifencei"
	.option norvc

	.equ B5_HSTATUS_CONTROL_MASK, 0x000000000073f380
	.equ B5_HSTATUS_GUEST_CONTROLS, 0x0000000000300180
	.equ B5_HSTATUS_SPV, 0x80
	.equ B5_HSTATUS_SPVP, 0x100
	.equ B5_HSTATUS_VTSR, 0x400000
	/* BE_R3_SSTATUS_CONTROL_MASK; non-control WARL fields may read nonzero. */
	.equ B5_SSTATUS_CONTROL_MASK, 0x00000000000de122
	.equ B5_SSTATUS_SPP, 0x100
	.equ B5_HIDELEG_VSTI, 0x40
	.equ B5_HIE_VSTIE, 0x40
	.equ B5_HCOUNTEREN_TM, 0x2
	.equ B5_HENVCFG_STCE, 0x8000000000000000
	/* Sstc vstimecmp, by number as B1 writes stimecmp. */
	.equ B5_CSR_VSTIMECMP, 0x24d

	/* enum be_b5_class values; b5-runtime.c asserts them. */
	.equ B5_CLASS_EXCEPTION, 8
	.equ B5_CLASS_RESUME, 10

	/* struct be_r4_frame offsets (include/be/r4.h). */
	.equ FR_VSTVEC, 248
	.equ FR_VSEPC, 256
	.equ FR_VSCAUSE, 264
	.equ FR_VSTVAL, 272
	.equ FR_SCAUSE, 280
	.equ FR_SEPC, 288
	.equ FR_STVAL, 296
	.equ FR_HTVAL, 304
	.equ FR_RESERVED, 312

	/* struct be_b5_controls offsets (b5.h). */
	.equ CTL_HIP, 0
	.equ CTL_HSTATUS, 8
	.equ CTL_HEDELEG, 16
	.equ CTL_HIDELEG, 24
	.equ CTL_HIE, 32
	.equ CTL_HVIP, 40
	.equ CTL_HCOUNTEREN, 48
	.equ CTL_HTIMEDELTA, 56
	.equ CTL_HENVCFG, 64
	.equ CTL_HGEIE, 72
	.equ CTL_VSTIMECMP, 80
	.equ CTL_SIE, 88
	.equ CTL_SSTATUS, 96
	.equ CTL_HGATP, 104
	.equ CTL_VSATP, 112

	.section .text, "ax"

	/*
	 * Arm helper: henvcfg = STCE only. STCE reads back 1 only when Sstc
	 * exists and M-mode set menvcfg.STCE, so this probe cannot trap.
	 */
	.align 4
	.globl be_b5_arch_arm_stce
	.type be_b5_arch_arm_stce, @function
be_b5_arch_arm_stce:
	.option push
	.option arch, +h
	li	t0, B5_HENVCFG_STCE
	csrw	henvcfg, t0
	csrr	a0, henvcfg
	.option pop
	ret
	.size be_b5_arch_arm_stce, . - be_b5_arch_arm_stce

	/*
	 * Arm helper: disarm the guest timer before it can be delegated, then
	 * delegate VSTI only, open time only, and clear VTSR only. Every
	 * control the guest run depends on is read back for C to check.
	 */
	.align 4
	.globl be_b5_arch_arm_controls
	.type be_b5_arch_arm_controls, @function
be_b5_arch_arm_controls:
	.option push
	.option arch, +h
	li	t0, -1
	csrw	B5_CSR_VSTIMECMP, t0
	csrr	t0, hip
	sd	t0, CTL_HIP(a0)
	li	t0, B5_HIDELEG_VSTI
	csrw	hideleg, t0
	li	t0, B5_HCOUNTEREN_TM
	csrw	hcounteren, t0
	li	t0, B5_HSTATUS_VTSR
	csrc	hstatus, t0
	csrr	t0, hstatus
	sd	t0, CTL_HSTATUS(a0)
	csrr	t0, hedeleg
	sd	t0, CTL_HEDELEG(a0)
	csrr	t0, hideleg
	sd	t0, CTL_HIDELEG(a0)
	csrr	t0, hie
	sd	t0, CTL_HIE(a0)
	csrr	t0, hvip
	sd	t0, CTL_HVIP(a0)
	csrr	t0, hcounteren
	sd	t0, CTL_HCOUNTEREN(a0)
	csrr	t0, htimedelta
	sd	t0, CTL_HTIMEDELTA(a0)
	csrr	t0, henvcfg
	sd	t0, CTL_HENVCFG(a0)
	csrr	t0, hgeie
	sd	t0, CTL_HGEIE(a0)
	csrr	t0, B5_CSR_VSTIMECMP
	sd	t0, CTL_VSTIMECMP(a0)
	csrr	t0, sie
	sd	t0, CTL_SIE(a0)
	csrr	t0, sstatus
	sd	t0, CTL_SSTATUS(a0)
	csrr	t0, hgatp
	sd	t0, CTL_HGATP(a0)
	csrr	t0, vsatp
	sd	t0, CTL_VSATP(a0)
	.option pop
	ret
	.size be_b5_arch_arm_controls, . - be_b5_arch_arm_controls

	/*
	 * Timer helper: SBI TIME set_timer. A future deadline clears a pending
	 * VS timer and ~0 disarms it; hardware raises VSTIP at the deadline.
	 */
	.align 4
	.globl be_b5_arch_set_timer
	.type be_b5_arch_set_timer, @function
be_b5_arch_set_timer:
	csrw	B5_CSR_VSTIMECMP, a0
	ret
	.size be_b5_arch_set_timer, . - be_b5_arch_set_timer

	.align 4
	.globl be_b5_trap_vector
	.type be_b5_trap_vector, @function
be_b5_trap_vector:
	/* First instruction exchanges untrusted guest sp before any stack access. */
	csrrw	sp, sscratch, sp
	/*
	 * The trusted-stack top is exclusive but not writable. Reserve a
	 * 16-byte-aligned spill frame before preserving t0/t1 for frame setup.
	 */
	addi	sp, sp, -16
	sd	t0, 0(sp)
	sd	t1, 8(sp)
	/* Only the management trusted stack exists; anything else is terminal. */
	addi	t0, sp, 16
	la	t1, __be_stack_management_end
	bne	t0, t1, .Lb5_bad_stack
	la	t0, __be_saved_management_start
	sd	ra, 0(t0)
	csrr	t1, sscratch
	sd	t1, 8(t0)
	/* sscratch names trusted storage again before C is reachable. */
	addi	t1, sp, 16
	csrw	sscratch, t1
	sd	gp, 16(t0)
	sd	tp, 24(t0)
	ld	t1, 0(sp)
	sd	t1, 32(t0)
	ld	t1, 8(sp)
	sd	t1, 40(t0)
	sd	t2, 48(t0)
	sd	s0, 56(t0)
	sd	s1, 64(t0)
	sd	a0, 72(t0)
	sd	a1, 80(t0)
	sd	a2, 88(t0)
	sd	a3, 96(t0)
	sd	a4, 104(t0)
	sd	a5, 112(t0)
	sd	a6, 120(t0)
	sd	a7, 128(t0)
	sd	s2, 136(t0)
	sd	s3, 144(t0)
	sd	s4, 152(t0)
	sd	s5, 160(t0)
	sd	s6, 168(t0)
	sd	s7, 176(t0)
	sd	s8, 184(t0)
	sd	s9, 192(t0)
	sd	s10, 200(t0)
	sd	s11, 208(t0)
	sd	t3, 216(t0)
	sd	t4, 224(t0)
	sd	t5, 232(t0)
	sd	t6, 240(t0)
	.option push
	.option arch, +h
	csrr	t1, vstvec
	sd	t1, FR_VSTVEC(t0)
	csrr	t1, vsepc
	sd	t1, FR_VSEPC(t0)
	csrr	t1, vscause
	sd	t1, FR_VSCAUSE(t0)
	csrr	t1, vstval
	sd	t1, FR_VSTVAL(t0)
	csrr	t1, scause
	sd	t1, FR_SCAUSE(t0)
	csrr	t1, sepc
	sd	t1, FR_SEPC(t0)
	csrr	t1, stval
	sd	t1, FR_STVAL(t0)
	csrr	t1, htval
	sd	t1, FR_HTVAL(t0)
	sd	zero, FR_RESERVED(t0)
	/* Only an exit from VS (SPV = SPVP = 1) reaches the dispatcher. */
	csrr	t1, hstatus
	li	t2, B5_HSTATUS_SPV | B5_HSTATUS_SPVP
	and	t1, t1, t2
	.option pop
	mv	a0, t0
	bne	t1, t2, .Lb5_bad_origin
	/* C is entered with monitor values only; no guest GPR is live. */
	call	be_b5_dispatch
	/* The dispatch is terminal or tail-calls the resume tail. */
	li	a0, B5_CLASS_RESUME
	tail	be_b5_runtime_terminal

.Lb5_bad_stack:
	la	sp, __be_stack_management_end
	li	a0, B5_CLASS_EXCEPTION
	tail	be_b5_runtime_terminal

.Lb5_bad_origin:
	tail	be_b5_exit_terminal
	.size be_b5_trap_vector, . - be_b5_trap_vector

	.align 4
	.globl be_b5_arch_resume
	.type be_b5_arch_resume, @function
be_b5_arch_resume:
	/*
	 * No-call tail: check every control the guest run depends on, then
	 * restore sepc and the GPRs and execute the single B5 SRET. t6 stays
	 * the monitor frame pointer to the last load.
	 */
	mv	t6, a0
	mv	t5, a1
	la	t0, __be_saved_management_start
	bne	t6, t0, .Lb5_resume_bad
	csrr	t0, satp
	bnez	t0, .Lb5_resume_bad
	csrr	t0, stvec
	la	t1, be_b5_trap_vector
	bne	t0, t1, .Lb5_resume_bad
	csrr	t0, sscratch
	la	t1, __be_stack_management_end
	bne	t0, t1, .Lb5_resume_bad
	csrr	t0, sie
	bnez	t0, .Lb5_resume_bad
	/* SPP is the only sstatus control the return may carry. */
	li	t1, B5_SSTATUS_SPP
	csrs	sstatus, t1
	csrr	t0, sstatus
	li	t1, B5_SSTATUS_CONTROL_MASK
	and	t0, t0, t1
	li	t1, B5_SSTATUS_SPP
	bne	t0, t1, .Lb5_resume_bad
	.option push
	.option arch, +h
	csrr	t0, hstatus
	li	t1, B5_HSTATUS_CONTROL_MASK
	and	t0, t0, t1
	li	t1, B5_HSTATUS_GUEST_CONTROLS
	bne	t0, t1, .Lb5_resume_bad
	csrr	t0, hedeleg
	bnez	t0, .Lb5_resume_bad
	csrr	t0, hideleg
	li	t1, B5_HIDELEG_VSTI
	bne	t0, t1, .Lb5_resume_bad
	/* hie may hold only VSTIE, the guest's own vsie.STIE. */
	csrr	t0, hie
	andi	t0, t0, ~B5_HIE_VSTIE
	bnez	t0, .Lb5_resume_bad
	csrr	t0, hvip
	bnez	t0, .Lb5_resume_bad
	csrr	t0, hcounteren
	li	t1, B5_HCOUNTEREN_TM
	bne	t0, t1, .Lb5_resume_bad
	csrr	t0, htimedelta
	bnez	t0, .Lb5_resume_bad
	csrr	t0, henvcfg
	li	t1, B5_HENVCFG_STCE
	bne	t0, t1, .Lb5_resume_bad
	csrr	t0, hgeie
	bnez	t0, .Lb5_resume_bad
	/* The management root is still selected and VS-stage is Bare. */
	csrr	t0, hgatp
	bne	t0, t5, .Lb5_resume_bad
	csrr	t0, vsatp
	bnez	t0, .Lb5_resume_bad
	.option pop
	ld	t0, FR_SEPC(t6)
	csrw	sepc, t0
	ld	ra, 0(t6)
	ld	gp, 16(t6)
	ld	tp, 24(t6)
	ld	t0, 32(t6)
	ld	t1, 40(t6)
	ld	t2, 48(t6)
	ld	s0, 56(t6)
	ld	s1, 64(t6)
	ld	a0, 72(t6)
	ld	a1, 80(t6)
	ld	a2, 88(t6)
	ld	a3, 96(t6)
	ld	a4, 104(t6)
	ld	a5, 112(t6)
	ld	a6, 120(t6)
	ld	a7, 128(t6)
	ld	s2, 136(t6)
	ld	s3, 144(t6)
	ld	s4, 152(t6)
	ld	s5, 160(t6)
	ld	s6, 168(t6)
	ld	s7, 176(t6)
	ld	s8, 184(t6)
	ld	s9, 192(t6)
	ld	s10, 200(t6)
	ld	s11, 208(t6)
	ld	t3, 216(t6)
	ld	t4, 224(t6)
	ld	t5, 232(t6)
	ld	sp, 8(t6)
	ld	t6, 240(t6)
	sret

.Lb5_resume_bad:
	li	a0, B5_CLASS_RESUME
	tail	be_b5_runtime_terminal
	.size be_b5_arch_resume, . - be_b5_arch_resume
