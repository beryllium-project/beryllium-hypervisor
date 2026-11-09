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
 *
 * beryllium-cheri: two monitor variants assemble from this file
 * (planning/cheri-platform.md). Without BE_MVP_CHERI it is the RISC-V
 * monitor, instruction for instruction the development line's. With
 * BE_MVP_CHERI (mvp/Makefile's MVP_MONITOR=cheri) it is the CHERI-aware
 * monitor, for CHERI v0.9.3 (Zcherihybrid): six routines carry
 * conditional blocks, as CHERI Alliance Linux's arch/riscv/kernel/entry.S
 * carries its CHERI blocks, and the vector and the resume tail keep the
 * guest's registers through the register macros below. The vector enters
 * Capability Pointer Mode first, saves every guest register whole in a
 * capability frame after struct be_mvp_exit, and switches ddc (CSR 0x416)
 * to the monitor's, which the resume tail switches back, restoring every
 * register whole; the three arm helpers write the armed henvcfg with CRE,
 * delegate cause 28, and name the trusted top in sscratchc, the arm
 * helper also clearing the capability frame and passing the device tree
 * as a capability; and the injection helper moves sepcc and vstvecc
 * whole, so it writes sepc too.
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
#if defined(BE_MVP_CHERI) && !defined(BE_MVP_VARIANT_CHERI_FAULT_HS)
	/* beryllium-cheri: and cause 28, CHERI v0.9.3's CHERI fault, but in
	 * cheri-fault-hs (src/mvp.h). */
	.equ MVP_HEDELEG, 0x1000b15d
#else
	.equ MVP_HEDELEG, 0xb15d
#endif
	.equ MVP_HIDELEG_VSTI, 0x40
	.equ MVP_HIE_VSTIE, 0x40
	/* VSSIP, VSTIP, and VSEIP: QEMU also shows a pending HS STIP. */
	.equ MVP_HVIP_VS_BITS, 0x444
	.equ MVP_HCOUNTEREN_TM, 0x2
	.equ MVP_HENVCFG_STCE, 0x8000000000000000
	/* The armed henvcfg, which the arm helper writes and the resume tail
	 * requires: STCE only. */
#ifdef BE_MVP_CHERI
	/* beryllium-cheri: STCE and CHERI v0.9.3's VS-mode enable, CRE. */
	.equ MVP_HENVCFG_ARMED, 0x8000000010000000
#else
	/* beryllium-cheri: a preprocessor name, not an assembler symbol, so
	 * that the plain monitor's ELF keeps MVP 1.0's symbol table, which
	 * M8's sequences record (verify/litmus/sequences.txt) pins. */
#define MVP_HENVCFG_ARMED MVP_HENVCFG_STCE
#endif
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

#ifdef BE_MVP_CHERI
	/*
	 * beryllium-cheri: CHERI v0.9.3 (Zcherihybrid). Beryllium's
	 * assemblers lack the extension, so its instructions are encoded:
	 * MODESW.CAP and MODESW.INT whole; SC (store capability) as
	 * .insn s 0x23, 4; LC (load capability) as .insn i 0x0f, 4; and
	 * SCADDR as .insn r 0x33, 1, 0x06. In Capability Pointer Mode a
	 * load or store takes its base register's capability as its
	 * authority, and a CSRRW of sscratch or ddc moves a whole
	 * capability. ddc (CSR 0x416) is one register for every mode.
	 * The capability frame follows struct be_mvp_exit in the saved
	 * page: slot 0 the guest's ddc, slot N (1 to 31) the guest's cN,
	 * 16 bytes each; then the monitor's ddc.
	 */
	.equ MVP_INSN_MODESW_CAP, 0x12001033
	.equ MVP_INSN_MODESW_INT, 0x14001033
	.equ CF, 368
	.equ CF_MON_DDC, 880
	.equ CF_END, 896
#endif

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

	/*
	 * The register macros of the vector and the resume tail, in the manner
	 * of CHERI Alliance Linux's CREG_S and CREG_L (arch/riscv/include/asm/
	 * asm.h), which are REG_S and REG_L without CHERI: MVP_SAVE_GPR stores
	 * the guest's xN, held in reg, in xN's slot of the saved page, and
	 * MVP_RESTORE_GPR loads reg from it. The RISC-V monitor's slot is the
	 * accepted frame's word at (N - 1) * 8, through t0 in the vector and t6
	 * in the resume tail. beryllium-cheri: the CHERI-aware monitor's is the
	 * capability frame's slot at CF + 16 * N, through csp in the vector and
	 * ct6 in the resume tail, by SC and LC, whole; MVP_RECORD_GPR then
	 * copies xN's address from that slot into the accepted frame's word,
	 * for the dispatch.
	 */
#ifdef BE_MVP_CHERI
	.macro MVP_SAVE_GPR reg, n
	.insn	s 0x23, 4, \reg, CF + 16 * \n(sp)
	.endm
	.macro MVP_RESTORE_GPR reg, n
	.insn	i 0x0f, 4, \reg, t6, CF + 16 * \n
	.endm
	.macro MVP_RECORD_GPR n
	ld	t0, CF + 16 * \n(sp)
	sd	t0, \n * 8 - 8(sp)
	.endm
#else
	.macro MVP_SAVE_GPR reg, n
	sd	\reg, \n * 8 - 8(t0)
	.endm
	.macro MVP_RESTORE_GPR reg, n
	ld	\reg, \n * 8 - 8(t6)
	.endm
#endif

	.section .text, "ax"

	/*
	 * Arm helper: henvcfg = the armed value, STCE only (beryllium-cheri:
	 * STCE and CRE in the CHERI-aware monitor). STCE reads back 1 only when
	 * Sstc exists and M-mode set menvcfg.STCE, so this probe cannot trap.
	 * Hart 0 runs it as its Sstc probe; each domain hart, before its arming.
	 */
	.align 2
	.globl be_mvp_arch_arm_stce
	.type be_mvp_arch_arm_stce, @function
be_mvp_arch_arm_stce:
	.option push
	.option arch, +h
	li	t0, MVP_HENVCFG_ARMED
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
#ifdef BE_MVP_CHERI
	/*
	 * beryllium-cheri: sscratchc is the trusted top as a capability from
	 * the monitor's ddc. The capability frame is cleared; the monitor's
	 * ddc is kept for the vector and is the guest's first ddc. a1's
	 * slot holds the device tree as a capability, the monitor's ddc at
	 * BE_MVP_DTB_GPA bounded to BE_MVP_DTB_BYTES (SCBNDSR is .insn r
	 * 0x33, 1, 0x07): a CHERI kernel takes its device tree from ca1, as
	 * CHERI firmware passes it, and the first entry's a1 equals its
	 * address, so the resume tail keeps the capability.
	 */
	csrrs	t0, 0x416, zero
	.insn	r 0x33, 1, 0x06, t1, t0, a1
	li	t2, BE_MVP_DTB_GPA
	.insn	r 0x33, 1, 0x06, t3, t0, t2
	li	t2, BE_MVP_DTB_BYTES
	.insn	r 0x33, 1, 0x07, t3, t3, t2
	/* The frame cleared, straight-line (no loop), each slot a null
	 * capability: CF to CF_END is 33 slots. */
	.insn	s 0x23, 4, zero, CF + 16 * 0(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 1(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 2(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 3(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 4(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 5(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 6(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 7(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 8(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 9(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 10(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 11(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 12(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 13(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 14(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 15(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 16(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 17(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 18(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 19(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 20(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 21(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 22(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 23(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 24(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 25(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 26(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 27(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 28(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 29(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 30(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 31(a1)
	.insn	s 0x23, 4, zero, CF + 16 * 32(a1)
	.4byte	MVP_INSN_MODESW_CAP
	csrrw	zero, sscratch, t1
	.insn	s 0x23, 4, t0, CF_MON_DDC(t1)
	.insn	s 0x23, 4, t0, CF(t1)
	.insn	s 0x23, 4, t3, CF + 16 * 11(t1)
	.4byte	MVP_INSN_MODESW_INT
#endif
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
	 *
	 * beryllium-cheri: with CHERI on, the guest's pc at the denied access
	 * is sepcc, a capability, and the guest's handler is vstvecc. In
	 * Capability Pointer Mode vsepcc becomes the former and sepcc the
	 * latter, whole, so that the guest's handler runs with its own
	 * capability and its sepcc is the faulting code's own. The integer
	 * writes that follow set only addresses: vsepc's to a2, sepcc's own,
	 * and the resume tail's sepc to the handler's. So this helper also
	 * writes sepc, which the resume tail writes again.
	 */
	.align 2
	.globl be_mvp_arch_inject
	.type be_mvp_arch_inject, @function
be_mvp_arch_inject:
	.option push
	.option arch, +h
	csrw	vscause, a0
	csrw	vstval, a1
#ifdef BE_MVP_CHERI
	.4byte	MVP_INSN_MODESW_CAP
	csrrs	t0, sepc, zero
	csrrw	zero, vsepc, t0
	csrrs	t0, vstvec, zero
	csrrw	zero, sepc, t0
	.4byte	MVP_INSN_MODESW_INT
#endif
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
#ifdef BE_MVP_CHERI
	/* beryllium-cheri: sscratchc is hart 0's top as a capability, as
	 * the vector's Capability Pointer Mode entry needs. */
	csrrs	t0, 0x416, zero
	.insn	r 0x33, 1, 0x06, t0, t0, a1
	.4byte	MVP_INSN_MODESW_CAP
	csrrw	zero, sscratch, t0
	.4byte	MVP_INSN_MODESW_INT
#endif
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
#ifdef BE_MVP_CHERI
	/*
	 * beryllium-cheri: enter Capability Pointer Mode first, so that every
	 * access before ddc is switched takes the monitor's trusted-top
	 * capability as its authority, never the guest's ddc. The swap is
	 * then whole: csp is the trusted top and sscratchc the guest's csp.
	 */
	.4byte	MVP_INSN_MODESW_CAP
	csrrw	sp, sscratch, sp
	/* The guest's ct0 and ct1, spilled below the top. */
	.insn	s 0x23, 4, t0, -32(sp)
	.insn	s 0x23, 4, t1, -16(sp)
	/*
	 * The top must be a block's 0x2000 offset in the hart region; the
	 * saved page starts there. Anything else is terminal.
	 */
	mv	t0, sp
#else
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
#endif
	la	t1, __be_mvp_hart_region_start
	sub	t0, t0, t1
	srli	t1, t0, MVP_REGION_SHIFT
	bnez	t1, .Lmvp_vector_bad_stack
	slli	t0, t0, 64 - MVP_BLOCK_SHIFT
	srli	t0, t0, 64 - MVP_BLOCK_SHIFT
	li	t1, BE_MVP_BLOCK_STACK_TOP_OFFSET
	bne	t0, t1, .Lmvp_vector_bad_stack
#ifdef BE_MVP_CHERI
	/* Every guest capability register into the capability frame. */
	.insn	i 0x0f, 4, t0, sp, -32
	MVP_SAVE_GPR t0, 5
	.insn	i 0x0f, 4, t0, sp, -16
	MVP_SAVE_GPR t0, 6
	MVP_SAVE_GPR ra, 1
	MVP_SAVE_GPR gp, 3
	MVP_SAVE_GPR tp, 4
#else
	addi	t0, sp, 16
	MVP_SAVE_GPR ra, 1
	csrr	t1, sscratch
	MVP_SAVE_GPR t1, 2
	/* sscratch names trusted storage again before C is reachable. */
	addi	t1, sp, 16
	csrw	sscratch, t1
	MVP_SAVE_GPR gp, 3
	MVP_SAVE_GPR tp, 4
	ld	t1, 0(sp)
	MVP_SAVE_GPR t1, 5
	ld	t1, 8(sp)
	MVP_SAVE_GPR t1, 6
#endif
	MVP_SAVE_GPR t2, 7
	MVP_SAVE_GPR s0, 8
	MVP_SAVE_GPR s1, 9
	MVP_SAVE_GPR a0, 10
	MVP_SAVE_GPR a1, 11
	MVP_SAVE_GPR a2, 12
	MVP_SAVE_GPR a3, 13
	MVP_SAVE_GPR a4, 14
	MVP_SAVE_GPR a5, 15
	MVP_SAVE_GPR a6, 16
	MVP_SAVE_GPR a7, 17
	MVP_SAVE_GPR s2, 18
	MVP_SAVE_GPR s3, 19
	MVP_SAVE_GPR s4, 20
	MVP_SAVE_GPR s5, 21
	MVP_SAVE_GPR s6, 22
	MVP_SAVE_GPR s7, 23
	MVP_SAVE_GPR s8, 24
	MVP_SAVE_GPR s9, 25
	MVP_SAVE_GPR s10, 26
	MVP_SAVE_GPR s11, 27
	MVP_SAVE_GPR t3, 28
	MVP_SAVE_GPR t4, 29
	MVP_SAVE_GPR t5, 30
	MVP_SAVE_GPR t6, 31
#ifdef BE_MVP_CHERI
	csrrs	t0, sscratch, zero
	MVP_SAVE_GPR t0, 2
	/* sscratch names trusted storage again before C is reachable. */
	csrrw	zero, sscratch, sp
	/* The guest's ddc into slot 0; the monitor's ddc back. */
	csrrs	t0, 0x416, zero
	.insn	s 0x23, 4, t0, CF(sp)
	.insn	i 0x0f, 4, t0, sp, CF_MON_DDC
	csrrw	zero, 0x416, t0
	/* The accepted integer frame: each register's address. */
	MVP_RECORD_GPR 1
	MVP_RECORD_GPR 2
	MVP_RECORD_GPR 3
	MVP_RECORD_GPR 4
	MVP_RECORD_GPR 5
	MVP_RECORD_GPR 6
	MVP_RECORD_GPR 7
	MVP_RECORD_GPR 8
	MVP_RECORD_GPR 9
	MVP_RECORD_GPR 10
	MVP_RECORD_GPR 11
	MVP_RECORD_GPR 12
	MVP_RECORD_GPR 13
	MVP_RECORD_GPR 14
	MVP_RECORD_GPR 15
	MVP_RECORD_GPR 16
	MVP_RECORD_GPR 17
	MVP_RECORD_GPR 18
	MVP_RECORD_GPR 19
	MVP_RECORD_GPR 20
	MVP_RECORD_GPR 21
	MVP_RECORD_GPR 22
	MVP_RECORD_GPR 23
	MVP_RECORD_GPR 24
	MVP_RECORD_GPR 25
	MVP_RECORD_GPR 26
	MVP_RECORD_GPR 27
	MVP_RECORD_GPR 28
	MVP_RECORD_GPR 29
	MVP_RECORD_GPR 30
	MVP_RECORD_GPR 31
	.4byte	MVP_INSN_MODESW_INT
	mv	t0, sp
#endif
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

.Lmvp_vector_bad_stack:
#ifdef BE_MVP_CHERI
	/* beryllium-cheri: back to Integer Pointer Mode, with sp 16 below
	 * the top, as the RISC-V monitor's vector leaves it. */
	.4byte	MVP_INSN_MODESW_INT
	addi	sp, sp, -16
	j	.Lmvp_bad_stack
#endif

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
	li	t1, MVP_HENVCFG_ARMED
	bne	t0, t1, .Lmvp_resume_bad
	csrr	t0, hgeie
	bnez	t0, .Lmvp_resume_bad
	/* This hart's domain root and VMID are selected. */
	csrr	t0, hgatp
	bne	t0, t5, .Lmvp_resume_bad
	.option pop
	ld	t0, FR_SEPC(t6)
	csrw	sepc, t0
#ifdef BE_MVP_CHERI
	/*
	 * beryllium-cheri: a register the dispatch changed (its frame word
	 * no longer equals its capability's address) returns as that
	 * integer, untagged; every other register returns as the guest's
	 * capability. Integer stores clear a slot's tag.
	 */
	li	t0, 1
	mv	t1, t6
	addi	t2, t6, CF + 16
1:
	ld	t3, 0(t1)
	ld	t4, 0(t2)
	beq	t3, t4, 2f
	sd	t3, 0(t2)
	sd	zero, 8(t2)
2:
	addi	t0, t0, 1
	addi	t1, t1, 8
	addi	t2, t2, 16
	li	t3, 32
	bltu	t0, t3, 1b
	/* Capability Pointer Mode; ct6 is the trusted top, from sscratchc. */
	.4byte	MVP_INSN_MODESW_CAP
	csrrs	t6, sscratch, zero
	.insn	i 0x0f, 4, t0, t6, CF
	csrrw	zero, 0x416, t0
#endif
	MVP_RESTORE_GPR ra, 1
#ifdef BE_MVP_CHERI
	/* beryllium-cheri: csp in its order; ct6, not csp, is the base. */
	MVP_RESTORE_GPR sp, 2
#endif
	MVP_RESTORE_GPR gp, 3
	MVP_RESTORE_GPR tp, 4
	MVP_RESTORE_GPR t0, 5
	MVP_RESTORE_GPR t1, 6
	MVP_RESTORE_GPR t2, 7
	MVP_RESTORE_GPR s0, 8
	MVP_RESTORE_GPR s1, 9
	MVP_RESTORE_GPR a0, 10
	MVP_RESTORE_GPR a1, 11
	MVP_RESTORE_GPR a2, 12
	MVP_RESTORE_GPR a3, 13
	MVP_RESTORE_GPR a4, 14
	MVP_RESTORE_GPR a5, 15
	MVP_RESTORE_GPR a6, 16
	MVP_RESTORE_GPR a7, 17
	MVP_RESTORE_GPR s2, 18
	MVP_RESTORE_GPR s3, 19
	MVP_RESTORE_GPR s4, 20
	MVP_RESTORE_GPR s5, 21
	MVP_RESTORE_GPR s6, 22
	MVP_RESTORE_GPR s7, 23
	MVP_RESTORE_GPR s8, 24
	MVP_RESTORE_GPR s9, 25
	MVP_RESTORE_GPR s10, 26
	MVP_RESTORE_GPR s11, 27
	MVP_RESTORE_GPR t3, 28
	MVP_RESTORE_GPR t4, 29
	MVP_RESTORE_GPR t5, 30
#ifndef BE_MVP_CHERI
	/* sp last but t6, the record's base. */
	MVP_RESTORE_GPR sp, 2
#endif
	MVP_RESTORE_GPR t6, 31
	sret

.Lmvp_resume_bad:
	mv	a0, t6
	li	a1, MVP_CLASS_RESUME
	tail	be_mvp_hart_terminal
	.size be_mvp_arch_resume, . - be_mvp_arch_resume
