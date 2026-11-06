/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B7 VS-exit vector, no-call resume tail (also every first
 *          entry), guest-control arm helpers, the per-guest CSR save and
 *          load helpers, the SBI TIME vstimecmp write, the HS deadline
 *          writer, the HS wait, the time read, and the image's one
 *          fence.i.
 * Trust:   sole B7 CSR boundary after the accepted R3 reset. The vector
 *          saves the accepted 320-byte struct be_r4_frame, then hstatus,
 *          htinst, vsatp, and time, to the management saved page, selected
 *          by the trusted-stack identity alone, and writes neither hie nor
 *          hvip. The resume tail checks every guest control and the running
 *          guest's hgatp, sets SPP from the record's saved SPVP, and writes
 *          no vs* CSR, hgatp, or fence. Only the load helper writes the
 *          per-guest CSRs (vstimecmp also the arm and TIME helpers), only
 *          the deadline helper writes stimecmp, and only the arm helper
 *          sets hstatus.VTW and sie.STIE. Nothing here dereferences a guest
 *          address.
 * Scope:   two Linux guests time-shared on hart 0 (planning/k3-b7-plan.md).
 *          The only HS interrupt is the supervisor timer, taken while V=1;
 *          no hvip injection; hstateen0, hvictl, hvien, and hviprio* are
 *          never accessed.
 */

	.attribute arch, "rv64imach_zicsr_zifencei"
	.option norvc

	.equ B7_HSTATUS_CONTROL_MASK, 0x000000000073f380
	.equ B7_HSTATUS_SPV, 0x80
	.equ B7_HSTATUS_SPVP, 0x100
	/* VTVM and VTSR stay clear: Linux writes satp and runs sfence.vma
	 * and sret. VTW is set: a guest wfi traps, so the guest can idle. */
	.equ B7_HSTATUS_CLEARED_TRAPS, 0x500000
	.equ B7_HSTATUS_VTW, 0x200000
	/* At a resume SPVP is the guest's own; only VTW and SPV are fixed. */
	.equ B7_HSTATUS_RESUME_MASK, 0x000000000073f280
	.equ B7_HSTATUS_RESUME_CONTROLS, 0x0000000000200080
	/* BE_R3_SSTATUS_CONTROL_MASK plus VS; non-control WARL fields may read
	 * nonzero. */
	.equ B7_SSTATUS_CONTROL_MASK, 0x00000000000de722
	.equ B7_SSTATUS_SPP, 0x100
	/* Causes 0, 2, 3, 4, 6, 8, 12, 13, and 15 go to the guest, as in B6. */
	.equ B7_HEDELEG, 0xb15d
	.equ B7_HIDELEG_VSTI, 0x40
	.equ B7_HIE_VSTIE, 0x40
	/* VSSIP, VSTIP, and VSEIP: QEMU also shows a pending HS STIP. */
	.equ B7_HVIP_VS_BITS, 0x444
	.equ B7_HCOUNTEREN_TM, 0x2
	.equ B7_HENVCFG_STCE, 0x8000000000000000
	/* The HS slice: the supervisor timer, taken only while V=1. */
	.equ B7_SIE_STIE, 0x20
	/* Sstc vstimecmp and stimecmp, and senvcfg, by number. */
	.equ B7_CSR_VSTIMECMP, 0x24d
	.equ B7_CSR_STIMECMP, 0x14d
	.equ B7_CSR_SENVCFG, 0x10a

	/* enum be_b7_class values; b7-runtime.c asserts them. */
	.equ B7_CLASS_EXCEPTION, 11
	.equ B7_CLASS_RESUME, 14

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
	/* struct be_b7_exit words after the frame (b7.h). */
	.equ EX_HSTATUS, 320
	.equ EX_HTINST, 328
	.equ EX_VSATP, 336
	.equ EX_TIME, 344

	/* struct be_b7_controls offsets (b7.h). */
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
	.equ CTL_SSCRATCH, 120

	/* enum be_b7_vcsr word offsets (b7.h). */
	.equ VC_VSSTATUS, 0
	.equ VC_VSIE, 8
	.equ VC_VSTVEC, 16
	.equ VC_VSSCRATCH, 24
	.equ VC_VSEPC, 32
	.equ VC_VSCAUSE, 40
	.equ VC_VSTVAL, 48
	.equ VC_VSATP, 56
	.equ VC_VSTIMECMP, 64
	.equ VC_SCOUNTEREN, 72
	.equ VC_SENVCFG, 80

	.section .text, "ax"

	/*
	 * Arm helper: henvcfg = STCE only. STCE reads back 1 only when Sstc
	 * exists and M-mode set menvcfg.STCE, so this probe cannot trap.
	 */
	.align 4
	.globl be_b7_arch_arm_stce
	.type be_b7_arch_arm_stce, @function
be_b7_arch_arm_stce:
	.option push
	.option arch, +h
	li	t0, B7_HENVCFG_STCE
	csrw	henvcfg, t0
	csrr	a0, henvcfg
	.option pop
	ret
	.size be_b7_arch_arm_stce, . - be_b7_arch_arm_stce

	/*
	 * Arm helper: disarm the guest timer before it can be delegated, then
	 * delegate the guest's own exceptions and VSTI, open time only, clear
	 * VTVM and VTSR, set VTW, enable the HS supervisor timer (sstatus.SIE
	 * stays 0, so HS takes it only while V=1), and name the trusted-stack
	 * top in sscratch. HS stimecmp is still ~0 from B1's quiesce, so no
	 * slice is pending yet. Every control the guest run depends on is read
	 * back for C to check.
	 */
	.align 4
	.globl be_b7_arch_arm_controls
	.type be_b7_arch_arm_controls, @function
be_b7_arch_arm_controls:
	.option push
	.option arch, +h
	li	t0, -1
	csrw	B7_CSR_VSTIMECMP, t0
	csrr	t0, hip
	sd	t0, CTL_HIP(a0)
	li	t0, B7_HEDELEG
	csrw	hedeleg, t0
	li	t0, B7_HIDELEG_VSTI
	csrw	hideleg, t0
	li	t0, B7_HCOUNTEREN_TM
	csrw	hcounteren, t0
	li	t0, B7_HSTATUS_CLEARED_TRAPS
	csrc	hstatus, t0
	li	t0, B7_HSTATUS_VTW
	csrs	hstatus, t0
	li	t0, B7_SIE_STIE
	csrs	sie, t0
	csrw	sscratch, a1
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
	csrr	t0, B7_CSR_VSTIMECMP
	sd	t0, CTL_VSTIMECMP(a0)
	csrr	t0, sie
	sd	t0, CTL_SIE(a0)
	csrr	t0, sstatus
	sd	t0, CTL_SSTATUS(a0)
	csrr	t0, hgatp
	sd	t0, CTL_HGATP(a0)
	csrr	t0, vsatp
	sd	t0, CTL_VSATP(a0)
	csrr	t0, sscratch
	sd	t0, CTL_SSCRATCH(a0)
	.option pop
	ret
	.size be_b7_arch_arm_controls, . - be_b7_arch_arm_controls

	/*
	 * Save helper: read the running guest's eleven per-guest CSRs into a
	 * be_u64[11] in enum be_b7_vcsr order. It writes no CSR.
	 */
	.align 4
	.globl be_b7_arch_save_vcsr
	.type be_b7_arch_save_vcsr, @function
be_b7_arch_save_vcsr:
	.option push
	.option arch, +h
	csrr	t0, vsstatus
	sd	t0, VC_VSSTATUS(a0)
	csrr	t0, vsie
	sd	t0, VC_VSIE(a0)
	csrr	t0, vstvec
	sd	t0, VC_VSTVEC(a0)
	csrr	t0, vsscratch
	sd	t0, VC_VSSCRATCH(a0)
	csrr	t0, vsepc
	sd	t0, VC_VSEPC(a0)
	csrr	t0, vscause
	sd	t0, VC_VSCAUSE(a0)
	csrr	t0, vstval
	sd	t0, VC_VSTVAL(a0)
	csrr	t0, vsatp
	sd	t0, VC_VSATP(a0)
	csrr	t0, B7_CSR_VSTIMECMP
	sd	t0, VC_VSTIMECMP(a0)
	csrr	t0, scounteren
	sd	t0, VC_SCOUNTEREN(a0)
	csrr	t0, B7_CSR_SENVCFG
	sd	t0, VC_SENVCFG(a0)
	.option pop
	ret
	.size be_b7_arch_save_vcsr, . - be_b7_arch_save_vcsr

	/*
	 * Load helper: write the incoming guest's eleven per-guest CSRs from a
	 * be_u64[11], then read all eleven back into a second array, which C
	 * compares word for word. The only writer of these CSRs but for the
	 * arm and TIME helpers' vstimecmp.
	 */
	.align 4
	.globl be_b7_arch_load_vcsr
	.type be_b7_arch_load_vcsr, @function
be_b7_arch_load_vcsr:
	.option push
	.option arch, +h
	ld	t0, VC_VSSTATUS(a0)
	csrw	vsstatus, t0
	ld	t0, VC_VSIE(a0)
	csrw	vsie, t0
	ld	t0, VC_VSTVEC(a0)
	csrw	vstvec, t0
	ld	t0, VC_VSSCRATCH(a0)
	csrw	vsscratch, t0
	ld	t0, VC_VSEPC(a0)
	csrw	vsepc, t0
	ld	t0, VC_VSCAUSE(a0)
	csrw	vscause, t0
	ld	t0, VC_VSTVAL(a0)
	csrw	vstval, t0
	ld	t0, VC_VSATP(a0)
	csrw	vsatp, t0
	ld	t0, VC_VSTIMECMP(a0)
	csrw	B7_CSR_VSTIMECMP, t0
	ld	t0, VC_SCOUNTEREN(a0)
	csrw	scounteren, t0
	ld	t0, VC_SENVCFG(a0)
	csrw	B7_CSR_SENVCFG, t0
	.option pop
	mv	a0, a1
	tail	be_b7_arch_save_vcsr
	.size be_b7_arch_load_vcsr, . - be_b7_arch_load_vcsr

	/*
	 * Timer helper: SBI TIME set_timer. A future deadline clears a pending
	 * VS timer and ~0 disarms it; hardware raises VSTIP at the deadline.
	 */
	.align 4
	.globl be_b7_arch_set_timer
	.type be_b7_arch_set_timer, @function
be_b7_arch_set_timer:
	csrw	B7_CSR_VSTIMECMP, a0
	ret
	.size be_b7_arch_set_timer, . - be_b7_arch_set_timer

	/*
	 * Deadline helper: the image's one stimecmp writer after B1's
	 * quiesce. The HS supervisor timer fires at the deadline: while a
	 * guest runs, as the slice or the other guest's wake; in the HS wait,
	 * as its wake-up. A deadline at or before time is pending at once.
	 */
	.align 4
	.globl be_b7_arch_set_deadline
	.type be_b7_arch_set_deadline, @function
be_b7_arch_set_deadline:
	csrw	B7_CSR_STIMECMP, a0
	ret
	.size be_b7_arch_set_deadline, . - be_b7_arch_set_deadline

	/*
	 * Wait helper: with the deadline set to the target, wfi until time
	 * reaches it. sstatus.SIE is 0 and sie.STIE 1, so the pending timer
	 * wakes the wfi without a trap; an early wake loops. Returns the time.
	 */
	.align 4
	.globl be_b7_arch_wait
	.type be_b7_arch_wait, @function
be_b7_arch_wait:
1:
	rdtime	t0
	bgeu	t0, a0, 2f
	wfi
	j	1b
2:
	mv	a0, t0
	ret
	.size be_b7_arch_wait, . - be_b7_arch_wait

	/* Time helper: the time CSR, for the tick counts and the budget. */
	.align 4
	.globl be_b7_arch_read_time
	.type be_b7_arch_read_time, @function
be_b7_arch_read_time:
	rdtime	a0
	ret
	.size be_b7_arch_read_time, . - be_b7_arch_read_time

	/*
	 * Placement helper: the image's one fence.i, after the last guest
	 * byte of both windows is stored and before the first entry, so the
	 * hart's fetches through the G-stage observe the placed kernels.
	 */
	.align 4
	.globl be_b7_arch_fence_i
	.type be_b7_arch_fence_i, @function
be_b7_arch_fence_i:
	fence.i
	ret
	.size be_b7_arch_fence_i, . - be_b7_arch_fence_i

	.align 4
	.globl be_b7_trap_vector
	.type be_b7_trap_vector, @function
be_b7_trap_vector:
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
	bne	t0, t1, .Lb7_bad_stack
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
	/* After the accepted frame: htinst, vsatp, time, and hstatus. */
	csrr	t1, htinst
	sd	t1, EX_HTINST(t0)
	csrr	t1, vsatp
	sd	t1, EX_VSATP(t0)
	rdtime	t1
	sd	t1, EX_TIME(t0)
	csrr	t1, hstatus
	sd	t1, EX_HSTATUS(t0)
	/* Only an exit from V=1 (SPV = 1, from VS or VU) reaches the dispatcher. */
	andi	t1, t1, B7_HSTATUS_SPV
	.option pop
	mv	a0, t0
	beqz	t1, .Lb7_bad_origin
	/* C is entered with monitor values only; no guest GPR is live. */
	call	be_b7_dispatch
	/* The dispatch is terminal or tail-calls the resume tail. */
	li	a0, B7_CLASS_RESUME
	tail	be_b7_runtime_terminal

.Lb7_bad_stack:
	la	sp, __be_stack_management_end
	li	a0, B7_CLASS_EXCEPTION
	tail	be_b7_runtime_terminal

.Lb7_bad_origin:
	tail	be_b7_exit_terminal
	.size be_b7_trap_vector, . - be_b7_trap_vector

	.align 4
	.globl be_b7_arch_resume
	.type be_b7_arch_resume, @function
be_b7_arch_resume:
	/*
	 * No-call tail, for every first entry and every resume: check every
	 * control the guest run depends on, set SPP from the record's saved
	 * SPVP (the guest's mode at its exit, VS on a first entry), then
	 * restore sepc and the GPRs and execute the single B7 SRET. t6 stays
	 * the monitor record pointer to the last load; t5 holds the running
	 * guest's hgatp and t4 the armed hedeleg readback (WARL) until their
	 * checks; t2 holds the SPP the return carries.
	 */
	mv	t6, a0
	mv	t5, a1
	mv	t4, a2
	la	t0, __be_saved_management_start
	bne	t6, t0, .Lb7_resume_bad
	csrr	t0, satp
	bnez	t0, .Lb7_resume_bad
	csrr	t0, stvec
	la	t1, be_b7_trap_vector
	bne	t0, t1, .Lb7_resume_bad
	csrr	t0, sscratch
	la	t1, __be_stack_management_end
	bne	t0, t1, .Lb7_resume_bad
	/* sie holds STIE only: the HS slice, taken only while V=1. */
	csrr	t0, sie
	li	t1, B7_SIE_STIE
	bne	t0, t1, .Lb7_resume_bad
	/*
	 * SPP is the only sstatus control the return may carry, and it is
	 * the saved SPVP, VS or VU at the guest's exit: both are bit 8, so
	 * SPP is cleared and then set from the masked saved hstatus.
	 */
	ld	t2, EX_HSTATUS(t6)
	andi	t2, t2, B7_HSTATUS_SPVP
	li	t1, B7_SSTATUS_SPP
	csrc	sstatus, t1
	csrs	sstatus, t2
	csrr	t0, sstatus
	li	t1, B7_SSTATUS_CONTROL_MASK
	and	t0, t0, t1
	bne	t0, t2, .Lb7_resume_bad
	.option push
	.option arch, +h
	csrr	t0, hstatus
	li	t1, B7_HSTATUS_RESUME_MASK
	and	t0, t0, t1
	li	t1, B7_HSTATUS_RESUME_CONTROLS
	bne	t0, t1, .Lb7_resume_bad
	/* hedeleg is WARL: it must still read as armed and checked. */
	csrr	t0, hedeleg
	bne	t0, t4, .Lb7_resume_bad
	csrr	t0, hideleg
	li	t1, B7_HIDELEG_VSTI
	bne	t0, t1, .Lb7_resume_bad
	/* hie may hold only VSTIE, the guest's own vsie.STIE. */
	csrr	t0, hie
	andi	t0, t0, ~B7_HIE_VSTIE
	bnez	t0, .Lb7_resume_bad
	/* hvip: no VS interrupt is injected; only those bits are tested. */
	csrr	t0, hvip
	andi	t0, t0, B7_HVIP_VS_BITS
	bnez	t0, .Lb7_resume_bad
	csrr	t0, hcounteren
	li	t1, B7_HCOUNTEREN_TM
	bne	t0, t1, .Lb7_resume_bad
	csrr	t0, htimedelta
	bnez	t0, .Lb7_resume_bad
	csrr	t0, henvcfg
	li	t1, B7_HENVCFG_STCE
	bne	t0, t1, .Lb7_resume_bad
	csrr	t0, hgeie
	bnez	t0, .Lb7_resume_bad
	/* The running guest's root and VMID are selected. */
	csrr	t0, hgatp
	bne	t0, t5, .Lb7_resume_bad
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

.Lb7_resume_bad:
	li	a0, B7_CLASS_RESUME
	tail	be_b7_runtime_terminal
	.size be_b7_arch_resume, . - be_b7_arch_resume
