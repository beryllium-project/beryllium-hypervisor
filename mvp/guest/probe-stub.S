/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: entry, trap stub, and access primitives of the MVP VS probe stub
 *          (planning/mvp-m0-plan.md, Platform record: probes): a load, a
 *          store, and a fetch at a GPA outside the root, each naming its
 *          next label in t6 for the probe handler's re-entry; the spin that
 *          the VS-mode IPIs interrupt, also naming its exit in t6; and the
 *          VMID sequence, which touches no memory but X around the probe's
 *          raw hgatp switch, so nothing depends on the window behind it.
 * Contract: the monitor enters at GPA 0x8020_0000 in VS mode with a0 = 0,
 *          a1 = 0, every other GPR zero, vsstatus = 0, and Bare vsatp. The
 *          probe calls use mvp/src/mvp-probe.h's extension and functions;
 *          a mismatch fails the probe run closed.
 * Trust:   untrusted VS code; the probe handler decides every exit.
 * Scope:   probe images only; B5's guest style (bringup/k3-b5/guest/).
 */

	.equ STUB_EID, 0x08424550
	.equ STUB_FID_IPI_VS, 3
	.equ STUB_FID_VMID_BEFORE, 5
	.equ STUB_FID_VMID_AFTER, 6
	.equ STUB_FID_FINISH, 7
	/* No probe function: the probe handler fails the hart. */
	.equ STUB_FID_TRAP, 0xff
	.equ STUB_OUTSIDE_GPA, 0x90000000
	.equ STUB_X_GPA, 0x80100000
	.equ STUB_X_READS, 10
	.equ STUB_STACK_TOP, 0x80080000

	.section .text.entry, "ax"
	.globl _start
	.type _start, @function
_start:
	li	sp, STUB_STACK_TOP
	la	t0, stub_trap
	csrw	stvec, t0
	call	stub_main
	/* stub_main ends with the probe's FINISH; reaching here is terminal. */
	j	stub_trap
	.size _start, . - _start

	/*
	 * Any trap the monitor delegates to the stub: none is expected, so
	 * the probe handler fails the hart.
	 */
	.text
	.align 2
	.globl stub_trap
	.type stub_trap, @function
stub_trap:
	li	a7, STUB_EID
	li	a6, STUB_FID_TRAP
	ecall
	j	stub_trap
	.size stub_trap, . - stub_trap

	/* A load from outside the root; the handler re-enters at 1f. */
	.globl stub_fault_load
	.type stub_fault_load, @function
stub_fault_load:
	la	t6, 1f
	li	t0, STUB_OUTSIDE_GPA
	ld	t1, 0(t0)
1:
	ret
	.size stub_fault_load, . - stub_fault_load

	/* A store to outside the root; the handler re-enters at 1f. */
	.globl stub_fault_store
	.type stub_fault_store, @function
stub_fault_store:
	la	t6, 1f
	li	t0, STUB_OUTSIDE_GPA
	sd	zero, 0(t0)
1:
	ret
	.size stub_fault_store, . - stub_fault_store

	/* A fetch from outside the root; the handler re-enters at 1f. */
	.globl stub_fault_fetch
	.type stub_fault_fetch, @function
stub_fault_fetch:
	la	t6, 1f
	li	t0, STUB_OUTSIDE_GPA
	jr	t0
1:
	ret
	.size stub_fault_fetch, . - stub_fault_fetch

	/*
	 * The VS-mode IPIs: name the exit, start the probe, and spin; the
	 * handler resumes the spin after each IPI and re-enters at 1f after
	 * the hundredth.
	 */
	.globl stub_spin_ipis
	.type stub_spin_ipis, @function
stub_spin_ipis:
	la	t6, 1f
	li	a7, STUB_EID
	li	a6, STUB_FID_IPI_VS
	ecall
2:
	j	2b
1:
	ret
	.size stub_spin_ipis, . - stub_spin_ipis

	/*
	 * The VMID probes: read X ten times under root A, report the last
	 * read (the probe switches hgatp to root B with no fence), read X
	 * once more, report it, and finish. Registers only: the stack is
	 * root A's.
	 */
	.globl stub_vmid
	.type stub_vmid, @function
stub_vmid:
	li	t0, STUB_X_GPA
	li	t1, STUB_X_READS
1:
	ld	a0, 0(t0)
	addi	t1, t1, -1
	bnez	t1, 1b
	li	a7, STUB_EID
	li	a6, STUB_FID_VMID_BEFORE
	ecall
	li	t0, STUB_X_GPA
	ld	a0, 0(t0)
	li	a7, STUB_EID
	li	a6, STUB_FID_VMID_AFTER
	ecall
	li	a7, STUB_EID
	li	a6, STUB_FID_FINISH
	ecall
	j	stub_trap
	.size stub_vmid, . - stub_vmid
