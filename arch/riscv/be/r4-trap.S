/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: R4 direct VS-exit entry, complete fixed-frame transfer, checked
 *          reset, and same-management SRET restoration.
 * Trust:   sole HS frame/CSR transition boundary. It never dereferences a
 *          guest address or guest stack and never writes HGATP or HFENCE.
 * Scope:   two validated exits from the unchanged management binding only.
 */

	.attribute arch, "rv64imach_zicsr_zifencei"
	.option norvc

	.equ R4_HSTATUS_CONTROL_MASK, 0x000000000073f380
	.equ R4_HSTATUS_CONTROL_VALUE, 0x0000000000700180
	.equ R4_HSTATUS_SPV, 0x80
	.equ R4_HSTATUS_SPVP, 0x100
	/* BE_R3_SSTATUS_CONTROL_MASK; non-control WARL fields may read nonzero. */
	.equ R4_SSTATUS_CONTROL_MASK, 0x00000000000de122
	.equ R4_SSTATUS_SPP, 0x100
	/*
	 * Keep these in lockstep with enum be_r4_error.  Assembly can reach
	 * terminal reporting only after a transition failure, so its values must
	 * retain the C-visible stable error identity.
	 */
	.equ R4_ERROR_R3_STATE, 3
	.equ R4_ERROR_HGATP, 9

	/* struct be_r3_hs_state offsets; R3 validates this initial readback. */
	.equ HS_SATP, 0
	.equ HS_SSTATUS, 8
	.equ HS_STVEC, 16
	.equ HS_SSCRATCH, 24
	.equ HS_SEPC, 32
	.equ HS_SCAUSE, 40
	.equ HS_STVAL, 48
	.equ HS_SIE, 56
	.equ HS_SIP, 64
	.equ HS_SENVCFG, 72
	.equ HS_SCOUNTEREN, 80
	.equ HS_HSTATUS, 88
	.equ HS_HEDELEG, 96
	.equ HS_HIDELEG, 104
	.equ HS_HIE, 112
	.equ HS_HIP, 120
	.equ HS_HVIP, 128
	.equ HS_HCOUNTEREN, 136
	.equ HS_HTIMEDELTA, 144
	.equ HS_HENVCFG, 152
	.equ HS_HGEIE, 160
	.equ HS_HGEIP, 168
	.equ HS_HTVAL, 176
	.equ HS_HGATP, 184
	.equ HS_VSSTATUS, 192
	.equ HS_VSIE, 200
	.equ HS_VSTVEC, 208
	.equ HS_VSSCRATCH, 216
	.equ HS_VSEPC, 224
	.equ HS_VSCAUSE, 232
	.equ HS_VSTVAL, 240
	.equ HS_VSIP, 248
	.equ HS_VSATP, 256

	.section .text, "ax"
	.align 4
	.globl be_r4_arch_reset_state
	.type be_r4_arch_reset_state, @function
be_r4_arch_reset_state:
	/* Initial reset is R3-equivalent except that R4 owns the direct vector. */
	csrw satp, zero
	sfence.vma zero, zero
	csrw sstatus, zero
	csrw stvec, a0
	csrw sscratch, zero
	csrw sepc, zero
	csrw scause, zero
	csrw stval, zero
	csrw sie, zero
	csrw senvcfg, zero
	csrw scounteren, zero
	.option push
	.option arch, +h
	csrr t0, hstatus
	li t1, R4_HSTATUS_CONTROL_MASK
	not t1, t1
	and t0, t0, t1
	li t1, R4_HSTATUS_CONTROL_VALUE
	or t0, t0, t1
	csrw hstatus, t0
	csrw hedeleg, zero
	csrw hideleg, zero
	csrw hie, zero
	csrw hvip, zero
	csrw hcounteren, zero
	csrw htimedelta, zero
	csrw henvcfg, zero
	csrw hgeie, zero
	csrw htval, zero
	csrw hgatp, zero
	hfence.gvma zero, zero
	csrw vsstatus, zero
	csrw vsie, zero
	csrw vstvec, zero
	csrw vsscratch, zero
	csrw vsepc, zero
	csrw vscause, zero
	csrw vstval, zero
	csrw vsip, zero
	csrw vsatp, zero
	csrr t0, satp
	sd t0, HS_SATP(a1)
	csrr t0, sstatus
	sd t0, HS_SSTATUS(a1)
	csrr t0, stvec
	sd t0, HS_STVEC(a1)
	csrr t0, sscratch
	sd t0, HS_SSCRATCH(a1)
	csrr t0, sepc
	sd t0, HS_SEPC(a1)
	csrr t0, scause
	sd t0, HS_SCAUSE(a1)
	csrr t0, stval
	sd t0, HS_STVAL(a1)
	csrr t0, sie
	sd t0, HS_SIE(a1)
	csrr t0, sip
	sd t0, HS_SIP(a1)
	csrr t0, senvcfg
	sd t0, HS_SENVCFG(a1)
	csrr t0, scounteren
	sd t0, HS_SCOUNTEREN(a1)
	csrr t0, hstatus
	sd t0, HS_HSTATUS(a1)
	csrr t0, hedeleg
	sd t0, HS_HEDELEG(a1)
	csrr t0, hideleg
	sd t0, HS_HIDELEG(a1)
	csrr t0, hie
	sd t0, HS_HIE(a1)
	csrr t0, hip
	sd t0, HS_HIP(a1)
	csrr t0, hvip
	sd t0, HS_HVIP(a1)
	csrr t0, hcounteren
	sd t0, HS_HCOUNTEREN(a1)
	csrr t0, htimedelta
	sd t0, HS_HTIMEDELTA(a1)
	csrr t0, henvcfg
	sd t0, HS_HENVCFG(a1)
	csrr t0, hgeie
	sd t0, HS_HGEIE(a1)
	csrr t0, hgeip
	sd t0, HS_HGEIP(a1)
	csrr t0, htval
	sd t0, HS_HTVAL(a1)
	csrr t0, hgatp
	sd t0, HS_HGATP(a1)
	csrr t0, vsstatus
	sd t0, HS_VSSTATUS(a1)
	csrr t0, vsie
	sd t0, HS_VSIE(a1)
	csrr t0, vstvec
	sd t0, HS_VSTVEC(a1)
	csrr t0, vsscratch
	sd t0, HS_VSSCRATCH(a1)
	csrr t0, vsepc
	sd t0, HS_VSEPC(a1)
	csrr t0, vscause
	sd t0, HS_VSCAUSE(a1)
	csrr t0, vstval
	sd t0, HS_VSTVAL(a1)
	csrr t0, vsip
	sd t0, HS_VSIP(a1)
	csrr t0, vsatp
	sd t0, HS_VSATP(a1)
	.option pop
	ret
	.size be_r4_arch_reset_state, . - be_r4_arch_reset_state

	.align 4
	.globl be_r4_trap_entry
	.type be_r4_trap_entry, @function
be_r4_trap_entry:
	/* First instruction exchanges untrusted guest sp before any stack access. */
	csrrw sp, sscratch, sp
	csrw sie, zero
	.option push
	.option arch, +h
	csrw hie, zero
	csrw hvip, zero
	.option pop
	/*
	 * The trusted-stack top is exclusive but not writable. Reserve a
	 * 16-byte-aligned spill frame before preserving t0/t1 for frame setup.
	 */
	addi sp, sp, -16
	sd t0, 0(sp)
	sd t1, 8(sp)
	la t0, __be_saved_management_start
	sd ra, 0(t0)
	csrr t1, sscratch
	sd t1, 8(t0)
	/*
	 * sscratch must again name trusted storage before C is reachable: a
	 * nested or partial HS trap then cannot exchange onto guest memory.
	 */
	la t1, __be_stack_management_end
	csrw sscratch, t1
	sd gp, 16(t0)
	sd tp, 24(t0)
	ld t1, 0(sp)
	sd t1, 32(t0)
	ld t1, 8(sp)
	sd t1, 40(t0)
	sd t2, 48(t0)
	sd s0, 56(t0)
	sd s1, 64(t0)
	sd a0, 72(t0)
	sd a1, 80(t0)
	sd a2, 88(t0)
	sd a3, 96(t0)
	sd a4, 104(t0)
	sd a5, 112(t0)
	sd a6, 120(t0)
	sd a7, 128(t0)
	sd s2, 136(t0)
	sd s3, 144(t0)
	sd s4, 152(t0)
	sd s5, 160(t0)
	sd s6, 168(t0)
	sd s7, 176(t0)
	sd s8, 184(t0)
	sd s9, 192(t0)
	sd s10, 200(t0)
	sd s11, 208(t0)
	sd t3, 216(t0)
	sd t4, 224(t0)
	sd t5, 232(t0)
	sd t6, 240(t0)
	.option push
	.option arch, +h
	csrr t1, vstvec
	sd t1, 248(t0)
	csrr t1, vsepc
	sd t1, 256(t0)
	csrr t1, vscause
	sd t1, 264(t0)
	csrr t1, vstval
	sd t1, 272(t0)
	csrr t1, scause
	sd t1, 280(t0)
	csrr t1, sepc
	sd t1, 288(t0)
	csrr t1, stval
	sd t1, 296(t0)
	csrr t1, htval
	sd t1, 304(t0)
	sd zero, 312(t0)
	csrr t1, hstatus
	li t2, R4_HSTATUS_SPV | R4_HSTATUS_SPVP
	and t1, t1, t2
	bne t1, t2, .Lbad_r3_state
	csrr a1, hgatp
	.option pop
	mv a0, t0
	call be_r4_trap_dispatch
	la a0, __be_saved_management_start
	tail be_r4_arch_restore_management

.Lbad_r3_state:
	li a0, R4_ERROR_R3_STATE
	tail be_r4_runtime_terminal
	.size be_r4_trap_entry, . - be_r4_trap_entry

	.align 4
	.globl be_r4_arch_restore_management
	.type be_r4_arch_restore_management, @function
be_r4_arch_restore_management:
	/* Reset all R-disposition controls; deliberately do not write HGATP/fence. */
	mv t6, a0
	csrw satp, zero
	sfence.vma zero, zero
	csrw sstatus, zero
	la t0, be_r4_trap_entry
	csrw stvec, t0
	la t0, __be_stack_management_end
	csrw sscratch, t0
	csrw sepc, zero
	csrw scause, zero
	csrw stval, zero
	csrw sie, zero
	csrw senvcfg, zero
	csrw scounteren, zero
	.option push
	.option arch, +h
	csrr t0, hstatus
	li t1, R4_HSTATUS_CONTROL_MASK
	not t1, t1
	and t0, t0, t1
	li t1, R4_HSTATUS_CONTROL_VALUE
	or t0, t0, t1
	csrw hstatus, t0
	csrw hedeleg, zero
	csrw hideleg, zero
	csrw hie, zero
	csrw hvip, zero
	csrw hcounteren, zero
	csrw htimedelta, zero
	csrw henvcfg, zero
	csrw hgeie, zero
	csrw htval, zero
	csrw vsstatus, zero
	csrw vsie, zero
	csrw vstvec, zero
	csrw vsscratch, zero
	csrw vsepc, zero
	csrw vscause, zero
	csrw vstval, zero
	csrw vsip, zero
	csrw vsatp, zero
	/* Read back every writable R-disposition control before frame restore. */
	csrr t0, satp
	bnez t0, .Lbad_r3_state
	csrr t0, sstatus
	li t1, R4_SSTATUS_CONTROL_MASK
	and t0, t0, t1
	bnez t0, .Lbad_r3_state
	csrr t0, stvec
	la t1, be_r4_trap_entry
	bne t0, t1, .Lbad_r3_state
	csrr t0, sscratch
	la t1, __be_stack_management_end
	bne t0, t1, .Lbad_r3_state
	csrr t0, sie
	bnez t0, .Lbad_r3_state
	csrr t0, senvcfg
	bnez t0, .Lbad_r3_state
	csrr t0, scounteren
	bnez t0, .Lbad_r3_state
	csrr t0, hstatus
	li t1, R4_HSTATUS_CONTROL_MASK
	and t0, t0, t1
	li t1, R4_HSTATUS_CONTROL_VALUE
	bne t0, t1, .Lbad_r3_state
	csrr t0, hedeleg
	bnez t0, .Lbad_r3_state
	csrr t0, hideleg
	bnez t0, .Lbad_r3_state
	csrr t0, hie
	bnez t0, .Lbad_r3_state
	csrr t0, hvip
	bnez t0, .Lbad_r3_state
	csrr t0, hcounteren
	bnez t0, .Lbad_r3_state
	csrr t0, htimedelta
	bnez t0, .Lbad_r3_state
	csrr t0, henvcfg
	bnez t0, .Lbad_r3_state
	csrr t0, hgeie
	bnez t0, .Lbad_r3_state
	csrr t0, htval
	bnez t0, .Lbad_r3_state
	csrr t0, vsstatus
	li t1, R4_SSTATUS_CONTROL_MASK
	and t0, t0, t1
	bnez t0, .Lbad_r3_state
	csrr t0, vsie
	bnez t0, .Lbad_r3_state
	csrr t0, vsscratch
	bnez t0, .Lbad_r3_state
	csrr t0, vsip
	bnez t0, .Lbad_r3_state
	csrr t0, vsatp
	bnez t0, .Lbad_r3_state
	csrr t0, hgatp
	li t1, 0x8000000000080214
	bne t0, t1, .Lbad_hgatp
	ld t0, 248(t6)
	csrw vstvec, t0
	ld t0, 256(t6)
	csrw vsepc, t0
	ld t0, 264(t6)
	csrw vscause, t0
	ld t0, 272(t6)
	csrw vstval, t0
	/*
	 * The frozen matrix classifies these as S fields.  Restore exactly the
	 * saved values; frame.sepc was deliberately advanced by C on success.
	 */
	ld t0, 280(t6)
	csrw scause, t0
	ld t0, 288(t6)
	csrw sepc, t0
	ld t0, 296(t6)
	csrw stval, t0
	ld t0, 304(t6)
	csrw htval, t0
	.option pop
	/*
	 * Set the return privilege before restoring x6.  No guest GPR is then
	 * clobbered by local restore setup; t6 remains the frame pointer last.
	 */
	li t1, R4_SSTATUS_SPP
	csrs sstatus, t1
	/* Restore all guest registers while retaining t6 as the frame pointer. */
	ld ra, 0(t6)
	ld gp, 16(t6)
	ld tp, 24(t6)
	ld t0, 32(t6)
	ld t1, 40(t6)
	ld t2, 48(t6)
	ld s0, 56(t6)
	ld s1, 64(t6)
	ld a0, 72(t6)
	ld a1, 80(t6)
	ld a2, 88(t6)
	ld a3, 96(t6)
	ld a4, 104(t6)
	ld a5, 112(t6)
	ld a6, 120(t6)
	ld a7, 128(t6)
	ld s2, 136(t6)
	ld s3, 144(t6)
	ld s4, 152(t6)
	ld s5, 160(t6)
	ld s6, 168(t6)
	ld s7, 176(t6)
	ld s8, 184(t6)
	ld s9, 192(t6)
	ld s10, 200(t6)
	ld s11, 208(t6)
	ld t3, 216(t6)
	ld t4, 224(t6)
	ld t5, 232(t6)
	ld sp, 8(t6)
	ld t6, 240(t6)
	sret

.Lbad_hgatp:
	li a0, R4_ERROR_HGATP
	tail be_r4_runtime_terminal
	.size be_r4_arch_restore_management, . - be_r4_arch_restore_management

	.align 4
	.globl be_r4_arch_halt
	.type be_r4_arch_halt, @function
be_r4_arch_halt:
	csrw sie, zero
	.option push
	.option arch, +h
	csrw hie, zero
	csrw hvip, zero
	.option pop
1:
	wfi
	j 1b
	.size be_r4_arch_halt, . - be_r4_arch_halt
