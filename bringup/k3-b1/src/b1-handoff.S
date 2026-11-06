/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 handoff quiesce in front of the unchanged accepted R4 entry.
 *          The accepted R3 reset check requires every S-mode interrupt
 *          pending bit to read zero (sip == 0). The accepted QEMU profile
 *          has no Sstc or AIA, so nothing is pending there. On the COM260
 *          (Sstc, Ssaia/IMSIC) a firmware or Linux kexec handoff can leave:
 *            - STIP: the Sstc compare stimecmp at or below time;
 *            - SSIP or LCOFIP: writable pending bits;
 *            - SEIP: a pending identity in the S-level IMSIC file.
 *          be_reset calls this function first (one port.py substitution in
 *          r4-entry.S). It disarms those sources, leaves a fail-closed trap
 *          vector, and returns with a0 (hart) and a1 (FDT) untouched. It
 *          writes no memory and makes no SBI call.
 * Trust:   HS-mode CSR writes only. The optional writes (stimecmp,
 *          siselect/sireg) are skipped through a local trap on harts that
 *          lack Sstc or AIA. The accepted R3 checks still validate the
 *          resulting state.
 * Scope:   B1 only. All instructions are four bytes (norvc), so the skip
 *          handler can advance sepc by 4.
 */

	.option norvc

#define CSR_STIMECMP	0x14d
#define CSR_SISELECT	0x150
#define CSR_SIREG	0x151
#define IMSIC_EIDELIVERY 0x70

	.section .text.b1.handoff, "ax"
	.align 4
	.globl be_b1_quiesce
	.type be_b1_quiesce, @function
be_b1_quiesce:
	csrci	sstatus, 0x2
	csrw	sie, zero
	lla	t0, be_b1_skip
	csrw	stvec, t0
	li	t1, -1
	csrw	CSR_STIMECMP, t1
	li	t1, IMSIC_EIDELIVERY
	csrw	CSR_SISELECT, t1
	csrw	CSR_SIREG, zero
	csrw	sip, zero
	lla	t0, be_b1_halt
	csrw	stvec, t0
	ret
	.size be_b1_quiesce, . - be_b1_quiesce

	/* Skip one faulting optional CSR access and return to HS. */
	.align 4
	.type be_b1_skip, @function
be_b1_skip:
	csrr	t2, sepc
	addi	t2, t2, 4
	csrw	sepc, t2
	sret
	.size be_b1_skip, . - be_b1_skip

	/* Fail closed: any trap before R3 installs its own vector halts. */
	.align 4
	.type be_b1_halt, @function
be_b1_halt:
	csrci	sstatus, 0x2
	csrw	sie, zero
1:
	wfi
	j	1b
	.size be_b1_halt, . - be_b1_halt
