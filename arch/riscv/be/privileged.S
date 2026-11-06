/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: sole privileged R3 CSR, SBI ECALL, HFENCE.GVMA, SRET, and halt
 *          implementation.
 * Trust:   explicit privileged-instruction boundary. The image checker
 *          inspects instruction ordering; R7 exact-byte proof is not claimed.
 * Scope:   first management entry only. The trap sink classifies nothing,
 *          saves nothing, and halts fail closed.
 */

	/*
	 * The global build remains the accepted rv64imac_zicsr_zifencei profile.
	 * This object alone truthfully advertises H because it contains the
	 * explicit H CSR/fence boundary enabled below with local .option scopes.
	 */
	.attribute arch, "rv64imach_zicsr_zifencei"

	.equ BE_R3_HSTATUS_CONTROL_MASK, 0x000000000073f380
	.equ BE_R3_HSTATUS_CONTROL_VALUE, 0x0000000000700180
	.equ BE_R3_SSTATUS_SPP, 0x0000000000000100

	/* struct be_r3_hs_state byte offsets, checked against C at build time. */
	.equ HS_SATP,		0
	.equ HS_SSTATUS,		8
	.equ HS_STVEC,		16
	.equ HS_SSCRATCH,	24
	.equ HS_SEPC,		32
	.equ HS_SCAUSE,		40
	.equ HS_STVAL,		48
	.equ HS_SIE,		56
	.equ HS_SIP,		64
	.equ HS_SENVCFG,	72
	.equ HS_SCOUNTEREN,	80
	.equ HS_HSTATUS,	88
	.equ HS_HEDELEG,	96
	.equ HS_HIDELEG,	104
	.equ HS_HIE,		112
	.equ HS_HIP,		120
	.equ HS_HVIP,		128
	.equ HS_HCOUNTEREN,	136
	.equ HS_HTIMEDELTA,	144
	.equ HS_HENVCFG,	152
	.equ HS_HGEIE,		160
	.equ HS_HGEIP,		168
	.equ HS_HTVAL,		176
	.equ HS_HGATP,		184
	.equ HS_VSSTATUS,	192
	.equ HS_VSIE,		200
	.equ HS_VSTVEC,		208
	.equ HS_VSSCRATCH,	216
	.equ HS_VSEPC,		224
	.equ HS_VSCAUSE,	232
	.equ HS_VSTVAL,		240
	.equ HS_VSIP,		248
	.equ HS_VSATP,		256

	.section .text, "ax"
	.align 4
	.globl be_r3_arch_sbi_call
	.type be_r3_arch_sbi_call, @function
be_r3_arch_sbi_call:
	/*
	 * C arguments are result, EID, FID, a0, a1, a2. Move the allowlisted
	 * call into the SBI binary convention and retain both return registers.
	 */
	mv	t0, a0
	mv	a7, a1
	mv	a6, a2
	mv	a0, a3
	mv	a1, a4
	mv	a2, a5
	ecall
	sd	a0, 0(t0)
	sd	a1, 8(t0)
	ret
	.size be_r3_arch_sbi_call, . - be_r3_arch_sbi_call

	.align 4
	.globl be_r3_arch_reset_state
	.type be_r3_arch_reset_state, @function
be_r3_arch_reset_state:
	/*
	 * a0 is the direct trap sink and a1 is the complete readback object.
	 * HS stage remains Bare; all asynchronous, delegated, virtual-interrupt,
	 * counter, and optional-environment paths in the accepted matrix are
	 * disabled before the first VS instruction.
	 */
	csrw	satp, zero
	sfence.vma	zero, zero
	csrw	sstatus, zero
	csrw	stvec, a0
	csrw	sscratch, zero
	csrw	sepc, zero
	csrw	scause, zero
	csrw	stval, zero
	csrw	sie, zero
	csrw	senvcfg, zero
	csrw	scounteren, zero

	.option push
	.option arch, +h
	csrr	t0, hstatus
	li	t1, BE_R3_HSTATUS_CONTROL_MASK
	not	t1, t1
	and	t0, t0, t1
	li	t1, BE_R3_HSTATUS_CONTROL_VALUE
	or	t0, t0, t1
	csrw	hstatus, t0
	csrw	hedeleg, zero
	csrw	hideleg, zero
	csrw	hie, zero
	csrw	hvip, zero
	csrw	hcounteren, zero
	csrw	htimedelta, zero
	csrw	henvcfg, zero
	csrw	hgeie, zero
	csrw	htval, zero
	csrw	hgatp, zero
	hfence.gvma	zero, zero
	csrw	vsstatus, zero
	csrw	vsie, zero
	csrw	vstvec, zero
	csrw	vsscratch, zero
	csrw	vsepc, zero
	csrw	vscause, zero
	csrw	vstval, zero
	csrw	vsip, zero
	csrw	vsatp, zero

	csrr	t0, satp
	sd	t0, HS_SATP(a1)
	csrr	t0, sstatus
	sd	t0, HS_SSTATUS(a1)
	csrr	t0, stvec
	sd	t0, HS_STVEC(a1)
	csrr	t0, sscratch
	sd	t0, HS_SSCRATCH(a1)
	csrr	t0, sepc
	sd	t0, HS_SEPC(a1)
	csrr	t0, scause
	sd	t0, HS_SCAUSE(a1)
	csrr	t0, stval
	sd	t0, HS_STVAL(a1)
	csrr	t0, sie
	sd	t0, HS_SIE(a1)
	csrr	t0, sip
	sd	t0, HS_SIP(a1)
	csrr	t0, senvcfg
	sd	t0, HS_SENVCFG(a1)
	csrr	t0, scounteren
	sd	t0, HS_SCOUNTEREN(a1)
	csrr	t0, hstatus
	sd	t0, HS_HSTATUS(a1)
	csrr	t0, hedeleg
	sd	t0, HS_HEDELEG(a1)
	csrr	t0, hideleg
	sd	t0, HS_HIDELEG(a1)
	csrr	t0, hie
	sd	t0, HS_HIE(a1)
	csrr	t0, hip
	sd	t0, HS_HIP(a1)
	csrr	t0, hvip
	sd	t0, HS_HVIP(a1)
	csrr	t0, hcounteren
	sd	t0, HS_HCOUNTEREN(a1)
	csrr	t0, htimedelta
	sd	t0, HS_HTIMEDELTA(a1)
	csrr	t0, henvcfg
	sd	t0, HS_HENVCFG(a1)
	csrr	t0, hgeie
	sd	t0, HS_HGEIE(a1)
	csrr	t0, hgeip
	sd	t0, HS_HGEIP(a1)
	csrr	t0, htval
	sd	t0, HS_HTVAL(a1)
	csrr	t0, hgatp
	sd	t0, HS_HGATP(a1)
	csrr	t0, vsstatus
	sd	t0, HS_VSSTATUS(a1)
	csrr	t0, vsie
	sd	t0, HS_VSIE(a1)
	csrr	t0, vstvec
	sd	t0, HS_VSTVEC(a1)
	csrr	t0, vsscratch
	sd	t0, HS_VSSCRATCH(a1)
	csrr	t0, vsepc
	sd	t0, HS_VSEPC(a1)
	csrr	t0, vscause
	sd	t0, HS_VSCAUSE(a1)
	csrr	t0, vstval
	sd	t0, HS_VSTVAL(a1)
	csrr	t0, vsip
	sd	t0, HS_VSIP(a1)
	csrr	t0, vsatp
	sd	t0, HS_VSATP(a1)
	.option pop
	ret
	.size be_r3_arch_reset_state, . - be_r3_arch_reset_state

	.align 4
	.globl be_r3_arch_install_management
	.type be_r3_arch_install_management, @function
be_r3_arch_install_management:
	/*
	 * This exact order is load-bearing: publish the complete root, write the
	 * VMID-zero HGATP value, perform the local all-GPA/all-VMID fence, then
	 * read back before C may publish the active binding.
	 */
	.option push
	.option arch, +h
	csrw	hgatp, a0
	hfence.gvma	zero, zero
	csrr	a0, hgatp
	.option pop
	ret
	.size be_r3_arch_install_management, . - be_r3_arch_install_management

	.align 4
	.globl be_r3_arch_enter_management
	.type be_r3_arch_enter_management, @function
be_r3_arch_enter_management:
	/*
	 * sepc is the initial HS-to-VS SRET target. vsepc was separately reset
	 * to zero and is not used as the initial return target at the R3 cut.
	 * sscratch retains the exact trusted stack while every guest GPR except
	 * sp is made deterministic zero. SPP is set only at the final transition
	 * boundary so the separately checked post-reset state remains clear.
	 */
	csrw	sepc, a0
	csrw	sscratch, a2
	mv	t6, a1
	li	ra, 0
	li	gp, 0
	li	tp, 0
	li	t0, 0
	li	t1, 0
	li	t2, 0
	li	s0, 0
	li	s1, 0
	li	a0, 0
	li	a1, 0
	li	a2, 0
	li	a3, 0
	li	a4, 0
	li	a5, 0
	li	a6, 0
	li	a7, 0
	li	s2, 0
	li	s3, 0
	li	s4, 0
	li	s5, 0
	li	s6, 0
	li	s7, 0
	li	s8, 0
	li	s9, 0
	li	s10, 0
	li	s11, 0
	li	t3, 0
	li	t4, 0
	li	t5, 0
	mv	sp, t6
	li	t6, 0
	li	t0, BE_R3_SSTATUS_SPP
	csrs	sstatus, t0
	li	t0, 0
	sret
	.size be_r3_arch_enter_management, . - be_r3_arch_enter_management

	.align 4
	.globl be_r3_unexpected_trap
	.type be_r3_unexpected_trap, @function
be_r3_unexpected_trap:
	/*
	 * R3 has no trap classification or frame. A trap after first entry is
	 * therefore terminal and must not touch the guest-valued stack.
	 */
	csrw	sie, zero
	.option push
	.option arch, +h
	csrw	hie, zero
	csrw	hvip, zero
	.option pop
1:
	wfi
	j	1b
	.size be_r3_unexpected_trap, . - be_r3_unexpected_trap

	.align 4
	.globl be_r3_arch_halt
	.type be_r3_arch_halt, @function
be_r3_arch_halt:
	csrw	sie, zero
	.option push
	.option arch, +h
	csrw	hie, zero
	csrw	hvip, zero
	.option pop
2:
	wfi
	j	2b
	.size be_r3_arch_halt, . - be_r3_arch_halt
