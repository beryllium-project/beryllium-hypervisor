/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP VS-exit vector, no-call resume tail (also every first
 *          entry), the domain hart's arm helpers, the SBI TIME vstimecmp
 *          write, the denial's injection helper, hart 0's budget and wait
 *          helpers, the SSIP clear, the time read, the ring and placement
 *          fences, and the domain park.
 * Trust:   sole MVP CSR boundary after the accepted R3 reset. The vector
 *          saves the accepted 320-byte struct be_r4_frame, then hstatus,
 *          htinst, vsatp, time, and vsstatus, to the saved page at the
 *          hart's trusted-stack top, which it derives from sscratch and
 *          requires to be a block's 0x2000 offset in the hart region; it
 *          writes neither hie nor hvip. The resume tail checks every guest
 *          control, this hart's sscratch and hgatp, sets SPP from the
 *          record's saved SPVP, and writes no vs* CSR, hgatp, or fence.
 *          Only the arm helper writes the per-domain CSRs (vstimecmp also
 *          the TIME helper, and vscause, vstval, vsepc, and vsstatus also
 *          the injection helper, once per accepted denial), only the budget
 *          helper writes stimecmp, only the arm and budget helpers write
 *          sie, and only the SSIP helper clears sip. VTW is never set.
 *          Nothing here dereferences a guest address.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, planning/mvp-m1-plan.md,
 *          and planning/mvp-m2-plan.md). A domain hart takes only the IPI
 *          as an HS interrupt, while V=1; hart 0 waits on the IPI and its
 *          budget timer with sstatus.SIE 0, and a paused or terminated
 *          domain hart on the IPI alone; no hvip injection; hstateen0,
 *          hvictl, hvien, and hviprio* are never accessed.
 */

#include "mvp-layout.h"

	.attribute arch, "rv64imach_zicsr_zifencei"
	.option norvc

	.equ MVP_HSTATUS_CONTROL_MASK, 0x000000000073f380
	.equ MVP_HSTATUS_SPV, 0x80
	.equ MVP_HSTATUS_SPVP, 0x100
	/* VTVM, VTW, and VTSR stay clear, B6's value: Linux writes satp and
	 * runs sfence.vma, sret, and wfi natively. */
	.equ MVP_HSTATUS_CLEARED_TRAPS, 0x700000
	/* At a resume SPVP is the guest's own; only SPV is fixed. */
	.equ MVP_HSTATUS_RESUME_MASK, 0x000000000073f280
	.equ MVP_HSTATUS_RESUME_CONTROLS, 0x0000000000000080
	/* BE_R3_SSTATUS_CONTROL_MASK plus VS; non-control WARL fields may read
	 * nonzero. */
	.equ MVP_SSTATUS_CONTROL_MASK, 0x00000000000de722
	.equ MVP_SSTATUS_SPP, 0x100
	/* Causes 0, 2, 3, 4, 6, 8, 12, 13, and 15 go to the guest, as in B6. */
	.equ MVP_HEDELEG, 0xb15d
	.equ MVP_HIDELEG_VSTI, 0x40
	.equ MVP_HIE_VSTIE, 0x40
	/* VSSIP, VSTIP, and VSEIP: QEMU also shows a pending HS STIP. */
	.equ MVP_HVIP_VS_BITS, 0x444
	.equ MVP_HCOUNTEREN_TM, 0x2
	.equ MVP_HENVCFG_STCE, 0x8000000000000000
	/* The IPI: the supervisor software interrupt, taken only while V=1. */
	.equ MVP_SIE_SSIE, 0x2
	/* Hart 0's wait: the IPI and its budget timer. */
	.equ MVP_SIE_CONTROL, 0x22
	/* Sstc vstimecmp and stimecmp, and senvcfg, by number. */
	.equ MVP_CSR_VSTIMECMP, 0x24d
	.equ MVP_CSR_STIMECMP, 0x14d
	.equ MVP_CSR_SENVCFG, 0x10a
	/* The hart region: 2^17 bytes of 2^16-byte blocks; mvp-runtime.c
	 * asserts both against mvp-layout.h. */
	.equ MVP_REGION_SHIFT, 17
	.equ MVP_BLOCK_SHIFT, 16

	/* enum be_mvp_class values; mvp-runtime.c asserts them. */
	.equ MVP_CLASS_EXCEPTION, 11
	.equ MVP_CLASS_RESUME, 14

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
	/* struct be_mvp_exit words after the frame (mvp.h). */
	.equ EX_HSTATUS, 320
	.equ EX_HTINST, 328
	.equ EX_VSATP, 336
	.equ EX_TIME, 344
	.equ EX_VSSTATUS, 352

	/* struct be_mvp_controls offsets (mvp.h). */
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

	/* enum be_mvp_vcsr word offsets (mvp.h). */
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

	/* The injection helper's readback words, BE_MVP_INJECT_* (mvp.h). */
	.equ IJ_VSCAUSE, 0
	.equ IJ_VSTVAL, 8
	.equ IJ_VSEPC, 16
	.equ IJ_VSSTATUS, 24

	.section .text, "ax"

	/*
	 * Arm helper: henvcfg = STCE only. STCE reads back 1 only when Sstc
	 * exists and M-mode set menvcfg.STCE, so this probe cannot trap. Hart 0
	 * runs it as its Sstc probe; each domain hart, before its arming.
	 */
	.align 2
	.globl be_mvp_arch_arm_stce
	.type be_mvp_arch_arm_stce, @function
be_mvp_arch_arm_stce:
	.option push
	.option arch, +h
	li	t0, MVP_HENVCFG_STCE
	csrw	henvcfg, t0
	csrr	a0, henvcfg
	.option pop
	ret
	.size be_mvp_arch_arm_stce, . - be_mvp_arch_arm_stce

	/*
	 * Arm helper: disarm the guest timer before it can be delegated, then
	 * delegate the guest's own exceptions and VSTI, open time only, clear
	 * VTVM, VTW, and VTSR, enable the IPI (sstatus.SIE stays 0, so HS takes
	 * it only while V=1), name the trusted-stack top in sscratch, and write
	 * the per-domain CSR set once from a2's eleven words. Every control the
	 * domain's run depends on is read back for C to check, and the set into
	 * a3's eleven words. This domain hart's stimecmp is never written: sie
	 * holds no STIE, so its timer never reaches HS.
	 */
	.align 2
	.globl be_mvp_arch_arm_controls
	.type be_mvp_arch_arm_controls, @function
be_mvp_arch_arm_controls:
	.option push
	.option arch, +h
	li	t0, -1
	csrw	MVP_CSR_VSTIMECMP, t0
	csrr	t0, hip
	sd	t0, CTL_HIP(a0)
	li	t0, MVP_HEDELEG
	csrw	hedeleg, t0
	li	t0, MVP_HIDELEG_VSTI
	csrw	hideleg, t0
	li	t0, MVP_HCOUNTEREN_TM
	csrw	hcounteren, t0
	li	t0, MVP_HSTATUS_CLEARED_TRAPS
	csrc	hstatus, t0
	li	t0, MVP_SIE_SSIE
	csrs	sie, t0
	csrw	sscratch, a1
	ld	t0, VC_VSSTATUS(a2)
	csrw	vsstatus, t0
	ld	t0, VC_VSIE(a2)
	csrw	vsie, t0
	ld	t0, VC_VSTVEC(a2)
	csrw	vstvec, t0
	ld	t0, VC_VSSCRATCH(a2)
	csrw	vsscratch, t0
	ld	t0, VC_VSEPC(a2)
	csrw	vsepc, t0
	ld	t0, VC_VSCAUSE(a2)
	csrw	vscause, t0
	ld	t0, VC_VSTVAL(a2)
	csrw	vstval, t0
	ld	t0, VC_VSATP(a2)
	csrw	vsatp, t0
	ld	t0, VC_VSTIMECMP(a2)
	csrw	MVP_CSR_VSTIMECMP, t0
	ld	t0, VC_SCOUNTEREN(a2)
	csrw	scounteren, t0
	ld	t0, VC_SENVCFG(a2)
	csrw	MVP_CSR_SENVCFG, t0
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
	csrr	t0, MVP_CSR_VSTIMECMP
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
	csrr	t0, vsstatus
	sd	t0, VC_VSSTATUS(a3)
	csrr	t0, vsie
	sd	t0, VC_VSIE(a3)
	csrr	t0, vstvec
	sd	t0, VC_VSTVEC(a3)
	csrr	t0, vsscratch
	sd	t0, VC_VSSCRATCH(a3)
	csrr	t0, vsepc
	sd	t0, VC_VSEPC(a3)
	csrr	t0, vscause
	sd	t0, VC_VSCAUSE(a3)
	csrr	t0, vstval
	sd	t0, VC_VSTVAL(a3)
	csrr	t0, vsatp
	sd	t0, VC_VSATP(a3)
	csrr	t0, MVP_CSR_VSTIMECMP
	sd	t0, VC_VSTIMECMP(a3)
	csrr	t0, scounteren
	sd	t0, VC_SCOUNTEREN(a3)
	csrr	t0, MVP_CSR_SENVCFG
	sd	t0, VC_SENVCFG(a3)
	.option pop
	ret
	.size be_mvp_arch_arm_controls, . - be_mvp_arch_arm_controls

	/*
	 * Timer helper: SBI TIME set_timer. A future deadline clears a pending
	 * VS timer and ~0 disarms it; hardware raises VSTIP at the deadline.
	 */
	.align 2
	.globl be_mvp_arch_set_timer
	.type be_mvp_arch_set_timer, @function
be_mvp_arch_set_timer:
	csrw	MVP_CSR_VSTIMECMP, a0
	ret
	.size be_mvp_arch_set_timer, . - be_mvp_arch_set_timer

	/*
	 * Injection helper (planning/mvp-m1-plan.md, "The denial path"): one
	 * accepted denial's trap into VS mode, as the access fault the guest
	 * would take, written from a0 to a3: vscause, vstval, vsepc, and
	 * vsstatus; each is then read back into a4's four words, in the same
	 * order, for C to compare with the values written. After arming it is
	 * the only writer of the four, and it touches no other CSR.
	 */
	.align 2
	.globl be_mvp_arch_inject
	.type be_mvp_arch_inject, @function
be_mvp_arch_inject:
	.option push
	.option arch, +h
	csrw	vscause, a0
	csrw	vstval, a1
	csrw	vsepc, a2
	csrw	vsstatus, a3
	csrr	t0, vscause
	sd	t0, IJ_VSCAUSE(a4)
	csrr	t0, vstval
	sd	t0, IJ_VSTVAL(a4)
	csrr	t0, vsepc
	sd	t0, IJ_VSEPC(a4)
	csrr	t0, vsstatus
	sd	t0, IJ_VSSTATUS(a4)
	.option pop
	ret
	.size be_mvp_arch_inject, . - be_mvp_arch_inject

	/*
	 * Budget helper: hart 0's run budget, the image's one stimecmp writer
	 * after B1's quiesce, written at the barrier and, only while console
	 * input is armed (M7), again at each wake of hart 0 for the next
	 * poll, never past the budget's end; then SSIE and STIE for hart 0's
	 * wait (sstatus.SIE stays 0, so neither traps), and hart 0's
	 * trusted-stack top in sscratch, so that an HS exception on hart 0
	 * reaches its terminal path. Returns the sie readback.
	 */
	.align 2
	.globl be_mvp_arch_arm_budget
	.type be_mvp_arch_arm_budget, @function
be_mvp_arch_arm_budget:
	csrw	MVP_CSR_STIMECMP, a0
	li	t0, MVP_SIE_CONTROL
	csrs	sie, t0
	csrw	sscratch, a1
	csrr	a0, sie
	ret
	.size be_mvp_arch_arm_budget, . - be_mvp_arch_arm_budget

	/*
	 * Wait helper: wfi until one of a0's sip bits is pending. sstatus.SIE
	 * is 0, so an enabled pending interrupt wakes the wfi without a trap;
	 * a wake with none of a0's bits pending loops. Returns the time.
	 * Hart 0's wait, and a paused or terminated domain hart's.
	 */
	.align 2
	.globl be_mvp_arch_wait
	.type be_mvp_arch_wait, @function
be_mvp_arch_wait:
1:
	csrr	t0, sip
	and	t0, t0, a0
	bnez	t0, 2f
	wfi
	j	1b
2:
	rdtime	a0
	ret
	.size be_mvp_arch_wait, . - be_mvp_arch_wait

	/*
	 * SSIP helper: the only clear of sip.SSIP, the IPI's pending bit, in
	 * one csrrc that returns sip as it was, so that a domain hart waiting
	 * in HS for hart 0 reads its inbound ring only after an IPI arrived
	 * (planning/mvp-m2-plan.md, Q14).
	 */
	.align 2
	.globl be_mvp_arch_clear_ssip
	.type be_mvp_arch_clear_ssip, @function
be_mvp_arch_clear_ssip:
	csrrci	a0, sip, MVP_SIE_SSIE
	ret
	.size be_mvp_arch_clear_ssip, . - be_mvp_arch_clear_ssip

	/* Time helper: the time CSR, for the tick counts and the budget. */
	.align 2
	.globl be_mvp_arch_read_time
	.type be_mvp_arch_read_time, @function
be_mvp_arch_read_time:
	rdtime	a0
	ret
	.size be_mvp_arch_read_time, . - be_mvp_arch_read_time

	/*
	 * Ring fences (mvp-ring.h): a writer copies its records, executes
	 * fence w, w, and then publishes the head; a reader acquires the head,
	 * executes fence r, r, and then copies records out; a reader executes
	 * fence r, w before it releases the tail, so the writer cannot reuse a
	 * slot before the reader's copy of it completes.
	 */
	.align 2
	.globl be_mvp_arch_fence_w_w
	.type be_mvp_arch_fence_w_w, @function
be_mvp_arch_fence_w_w:
	fence	w, w
	ret
	.size be_mvp_arch_fence_w_w, . - be_mvp_arch_fence_w_w

	.align 2
	.globl be_mvp_arch_fence_r_r
	.type be_mvp_arch_fence_r_r, @function
be_mvp_arch_fence_r_r:
	fence	r, r
	ret
	.size be_mvp_arch_fence_r_r, . - be_mvp_arch_fence_r_r

	.align 2
	.globl be_mvp_arch_fence_r_w
	.type be_mvp_arch_fence_r_w, @function
be_mvp_arch_fence_r_w:
	fence	r, w
	ret
	.size be_mvp_arch_fence_r_w, . - be_mvp_arch_fence_r_w

	/*
	 * Placement fence: hart 0's data fence after the last guest byte of
	 * both windows is stored, before the blocks are published; each domain
	 * hart then executes the image's one fence.i before its first entry.
	 */
	.align 2
	.globl be_mvp_arch_fence_rw_rw
	.type be_mvp_arch_fence_rw_rw, @function
be_mvp_arch_fence_rw_rw:
	fence	rw, rw
	ret
	.size be_mvp_arch_fence_rw_rw, . - be_mvp_arch_fence_rw_rw

	/*
	 * Park: a domain hart after its domain's shutdown or a failed block
	 * check, in HS wfi forever. It writes no CSR; an IPI wakes it into the
	 * same wfi.
	 */
	.align 2
	.globl be_mvp_arch_park
	.type be_mvp_arch_park, @function
be_mvp_arch_park:
1:
	wfi
	j	1b
	.size be_mvp_arch_park, . - be_mvp_arch_park

	.align 2
	.globl be_mvp_trap_vector
	.type be_mvp_trap_vector, @function
be_mvp_trap_vector:
	/* First instruction exchanges untrusted guest sp before any stack access. */
	csrrw	sp, sscratch, sp
	/*
	 * The trusted-stack top is exclusive but not writable. Reserve a
	 * 16-byte-aligned spill frame before preserving t0/t1 for frame setup.
	 */
	addi	sp, sp, -16
	sd	t0, 0(sp)
	sd	t1, 8(sp)
	/*
	 * The top must be a block's 0x2000 offset in the hart region; the
	 * saved page starts there. Anything else is terminal.
	 */
	addi	t0, sp, 16
	la	t1, __be_mvp_hart_region_start
	sub	t0, t0, t1
	srli	t1, t0, MVP_REGION_SHIFT
	bnez	t1, .Lmvp_bad_stack
	slli	t0, t0, 64 - MVP_BLOCK_SHIFT
	srli	t0, t0, 64 - MVP_BLOCK_SHIFT
	li	t1, BE_MVP_BLOCK_STACK_TOP_OFFSET
	bne	t0, t1, .Lmvp_bad_stack
	addi	t0, sp, 16
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
	/* After the accepted frame: htinst, vsatp, time, hstatus, and the
	 * guest's vsstatus, which a denial's injection starts from. */
	csrr	t1, htinst
	sd	t1, EX_HTINST(t0)
	csrr	t1, vsatp
	sd	t1, EX_VSATP(t0)
	rdtime	t1
	sd	t1, EX_TIME(t0)
	csrr	t1, hstatus
	sd	t1, EX_HSTATUS(t0)
	csrr	t2, vsstatus
	sd	t2, EX_VSSTATUS(t0)
	/* Only an exit from V=1 (SPV = 1, from VS or VU) reaches the dispatcher. */
	andi	t1, t1, MVP_HSTATUS_SPV
	.option pop
	mv	a0, t0
	beqz	t1, .Lmvp_bad_origin
	/* C is entered with monitor values only; no guest GPR is live. */
	call	be_mvp_dispatch
	/* The dispatch parks, fails, or tail-calls the resume tail. */
	csrr	a0, sscratch
	li	a1, MVP_CLASS_RESUME
	tail	be_mvp_hart_terminal

.Lmvp_bad_stack:
	/*
	 * Hart 0's trusted top (its sscratch since the budget helper) means an
	 * HS exception on hart 0: its terminal path. Any other top halts.
	 */
	addi	t0, sp, 16
	la	t1, __be_control_stack_end
	bne	t0, t1, .Lmvp_halt
	li	a0, MVP_CLASS_EXCEPTION
	tail	be_mvp_runtime_terminal

.Lmvp_halt:
	tail	be_r3_arch_halt

.Lmvp_bad_origin:
	li	a1, MVP_CLASS_EXCEPTION
	tail	be_mvp_hart_terminal
	.size be_mvp_trap_vector, . - be_mvp_trap_vector

	.align 2
	.globl be_mvp_arch_resume
	.type be_mvp_arch_resume, @function
be_mvp_arch_resume:
	/*
	 * No-call tail, for every first entry and every resume: check every
	 * control the domain's run depends on, set SPP from the record's saved
	 * SPVP (the guest's mode at its exit, VS on a first entry), then
	 * restore sepc and the GPRs and execute the single MVP SRET. t6 stays
	 * the monitor record pointer to the last load; t5 holds this hart's
	 * hgatp and t4 the armed hedeleg readback (WARL) until their checks;
	 * t2 holds the SPP the return carries.
	 */
	mv	t6, a0
	mv	t5, a1
	mv	t4, a2
	/* The record is this hart's saved page, at its sscratch: a block's
	 * trusted-stack top. */
	csrr	t0, sscratch
	bne	t6, t0, .Lmvp_resume_bad
	la	t1, __be_mvp_hart_region_start
	sub	t0, t0, t1
	srli	t1, t0, MVP_REGION_SHIFT
	bnez	t1, .Lmvp_resume_bad
	slli	t0, t0, 64 - MVP_BLOCK_SHIFT
	srli	t0, t0, 64 - MVP_BLOCK_SHIFT
	li	t1, BE_MVP_BLOCK_STACK_TOP_OFFSET
	bne	t0, t1, .Lmvp_resume_bad
	csrr	t0, satp
	bnez	t0, .Lmvp_resume_bad
	csrr	t0, stvec
	la	t1, be_mvp_trap_vector
	bne	t0, t1, .Lmvp_resume_bad
	/* sie holds SSIE only: the IPI, taken only while V=1. */
	csrr	t0, sie
	li	t1, MVP_SIE_SSIE
	bne	t0, t1, .Lmvp_resume_bad
	/*
	 * SPP is the only sstatus control the return may carry, and it is
	 * the saved SPVP, VS or VU at the guest's exit: both are bit 8, so
	 * SPP is cleared and then set from the masked saved hstatus.
	 */
	ld	t2, EX_HSTATUS(t6)
	andi	t2, t2, MVP_HSTATUS_SPVP
	li	t1, MVP_SSTATUS_SPP
	csrc	sstatus, t1
	csrs	sstatus, t2
	csrr	t0, sstatus
	li	t1, MVP_SSTATUS_CONTROL_MASK
	and	t0, t0, t1
	bne	t0, t2, .Lmvp_resume_bad
	.option push
	.option arch, +h
	csrr	t0, hstatus
	li	t1, MVP_HSTATUS_RESUME_MASK
	and	t0, t0, t1
	li	t1, MVP_HSTATUS_RESUME_CONTROLS
	bne	t0, t1, .Lmvp_resume_bad
	/* hedeleg is WARL: it must still read as armed and checked. */
	csrr	t0, hedeleg
	bne	t0, t4, .Lmvp_resume_bad
	csrr	t0, hideleg
	li	t1, MVP_HIDELEG_VSTI
	bne	t0, t1, .Lmvp_resume_bad
	/* hie may hold only VSTIE, the guest's own vsie.STIE. */
	csrr	t0, hie
	andi	t0, t0, ~MVP_HIE_VSTIE
	bnez	t0, .Lmvp_resume_bad
	/* hvip: no VS interrupt is injected; only those bits are tested. */
	csrr	t0, hvip
	andi	t0, t0, MVP_HVIP_VS_BITS
	bnez	t0, .Lmvp_resume_bad
	csrr	t0, hcounteren
	li	t1, MVP_HCOUNTEREN_TM
	bne	t0, t1, .Lmvp_resume_bad
	csrr	t0, htimedelta
	bnez	t0, .Lmvp_resume_bad
	csrr	t0, henvcfg
	li	t1, MVP_HENVCFG_STCE
	bne	t0, t1, .Lmvp_resume_bad
	csrr	t0, hgeie
	bnez	t0, .Lmvp_resume_bad
	/* This hart's domain root and VMID are selected. */
	csrr	t0, hgatp
	bne	t0, t5, .Lmvp_resume_bad
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

.Lmvp_resume_bad:
	mv	a0, t6
	li	a1, MVP_CLASS_RESUME
	tail	be_mvp_hart_terminal
	.size be_mvp_arch_resume, . - be_mvp_arch_resume
