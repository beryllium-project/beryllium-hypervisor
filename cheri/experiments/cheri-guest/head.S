/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * The CHERI test guest's assembly: a Linux Image header that Beryllium's
 * payload check accepts, the entry, a trap handler that recovers at an
 * address a probe arms, and the probes that must hold capabilities in
 * registers across a trap or write ddc. CHERI v0.9.3, Zcherihybrid; the
 * guest runs in Integer Pointer Mode except where a probe switches.
 */
	.option norvc

	.section .head, "ax"
	.globl	_start
_start:
	j	real_start		/* code0 */
	.word	0			/* code1 */
	.dword	0x200000		/* text_offset */
	.dword	_image_size		/* image_size */
	.dword	0			/* flags: little endian */
	.word	2			/* version */
	.word	0			/* res1 */
	.dword	0			/* res2 */
	.ascii	"RISCV\0\0\0"		/* magic */
	.ascii	"RSC\x05"		/* magic2 */
	.word	0			/* res3 */

	.text
real_start:
	lla	sp, stack_top
	mv	s0, a0
	mv	s1, a1
	lla	t0, __bss_start
	lla	t1, __bss_end
1:	bgeu	t0, t1, 2f
	sd	zero, 0(t0)
	addi	t0, t0, 8
	j	1b
2:	lla	t0, trap_entry
	csrw	stvec, t0
	mv	a0, s0
	mv	a1, s1
	call	guest_main
3:	wfi
	j	3b

/*
 * struct trap_info (guest.c): t1 spill, scause, stval, sepc, the armed
 * recovery address, and the trap count. A trap with a recovery address
 * armed resumes there, once; any other trap is reported and stops.
 */
	.align	4
trap_entry:
	csrw	sscratch, t0
	lla	t0, trap_info
	sd	t1, 0(t0)
	csrr	t1, scause
	sd	t1, 8(t0)
	csrr	t1, stval
	sd	t1, 16(t0)
	csrr	t1, sepc
	sd	t1, 24(t0)
	ld	t1, 40(t0)
	addi	t1, t1, 1
	sd	t1, 40(t0)
	ld	t1, 32(t0)
	beqz	t1, 1f
	sd	zero, 32(t0)
	csrw	sepc, t1
	ld	t1, 0(t0)
	csrr	t0, sscratch
	sret
1:	lla	sp, fatal_stack_top
	call	guest_trap_fatal
2:	wfi
	j	2b

	.macro	ARM label
	lla	t0, trap_info
	lla	t1, \label
	sd	t1, 32(t0)
	.endm
	.macro	DISARM
	lla	t0, trap_info
	sd	zero, 32(t0)
	.endm

/* u64 probe_cheri(void): ddc's tag, or ~0 if reading ddc traps. */
	.globl	probe_cheri
probe_cheri:
	ARM	1f
	csrrc	a0, 0x416, zero
	gctag	a0, ca0
	DISARM
	ret
1:	li	a0, -1
	ret

/*
 * struct pair probe_reg_across_call(u64 addr): cs1 holds a capability
 * bounded to 64 bytes at addr across one SBI call (Base,
 * get_spec_version), which the monitor serves. Returns a = tag before |
 * tag after << 1, b = cs1's address after.
 */
	.globl	probe_reg_across_call
probe_reg_across_call:
	addi	sp, sp, -32
	sc	cs1, 0(sp)
	sd	ra, 16(sp)
	csrrc	t0, 0x416, zero
	scaddr	ct0, ct0, a0
	li	t1, 64
	scbndsr	cs1, ct0, t1
	gctag	t2, cs1
	li	a7, 0x10
	li	a6, 0
	ecall
	gctag	t3, cs1
	slli	t3, t3, 1
	or	a0, t2, t3
	mv	a1, s1
	ld	ra, 16(sp)
	lc	cs1, 0(sp)
	addi	sp, sp, 32
	ret

/*
 * u64 probe_bounds_fault(u64 addr): loads through a capability bounded to
 * the 16 bytes at addr, at addr + 32, in Capability Pointer Mode (this
 * QEMU's v0.9.3 target has no capability-based load in Integer Pointer
 * Mode). Returns 1 if the guest's own handler took the fault, 0 if the
 * load completed. A recovered fault resumes in Capability Pointer Mode.
 */
	.globl	probe_bounds_fault
probe_bounds_fault:
	ARM	1f
	csrrc	t0, 0x416, zero
	scaddr	ct0, ct0, a0
	li	t1, 16
	scbndsr	ct0, ct0, t1
	addi	t1, a0, 32
	scaddr	ct0, ct0, t1
	modesw.cap
	ld	t1, 0(t0)
	modesw.int
	DISARM
	li	a0, 0
	ret
1:	modesw.int
	li	a0, 1
	ret

/* u64 load_via_cap(void *__capability c): an 8-byte load through c. */
	.globl	load_via_cap
load_via_cap:
	modesw.cap
	ld	a0, 0(a0)
	modesw.int
	ret

/*
 * u64 probe_ddc_restrict(u64 target, u64 w0, u64 w1): bounds ddc to the
 * 4 KiB page holding target, sets sp = target + 16, t0 = w0 and t1 = w1,
 * and makes one SBI call (Base, get_spec_version). ddc is shared by every
 * mode, so the monitor's trap vector runs with the guest's ddc. Returns 0
 * only if the monitor returns to the guest.
 */
	.globl	probe_ddc_restrict
probe_ddc_restrict:
	addi	sp, sp, -48
	sd	ra, 0(sp)
	sd	s0, 8(sp)
	sc	cs1, 16(sp)
	sc	cs2, 32(sp)
	mv	s0, sp
	csrrc	t2, 0x416, zero
	cmv	cs1, ct2
	srli	t3, a0, 12
	slli	t3, t3, 12
	scaddr	ct2, ct2, t3
	lui	t4, 1
	scbndsr	cs2, ct2, t4
	addi	sp, a0, 16
	mv	t0, a1
	mv	t1, a2
	modesw.cap
	csrrw	cnull, ddc, cs2
	modesw.int
	li	a7, 0x10
	li	a6, 0
	ecall
	modesw.cap
	csrrw	cnull, ddc, cs1
	modesw.int
	mv	sp, s0
	ld	ra, 0(sp)
	ld	s0, 8(sp)
	lc	cs1, 16(sp)
	lc	cs2, 32(sp)
	addi	sp, sp, 48
	li	a0, 0
	ret

	.bss
	.align	4
	.space	16384
stack_top:
	.space	4096
fatal_stack_top:
