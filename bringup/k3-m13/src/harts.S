/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: image 1's harts (planning/mvp-m13-3-review-point.md, sections 2
 *          and 3): P1's CSR accesses on a hart; the SBI HSM start of each
 *          other hart of 0 to 2 (the MVP shim's pattern,
 *          mvp/shim/mvp-shim.S:236-241) and the bounded wait for its
 *          report; the started harts' entry, which checks a0 again, and
 *          their trap vector.
 * Contract: be_m13_p1 and be_m13_hart_run are called from C on the entry
 *          hart. be_m13_secondary is HSM's start address, entered in
 *          S-mode with satp Bare, a0 the hart and a1 the opaque value, the
 *          hart that was started.
 * Trust:   an HSM start names a hart of 0 to 2 alone (the bound before its
 *          ecall). A started hart prints nothing and reads nothing but its
 *          own hgeie: it records into its slot and parks. Every store here
 *          is into a slot, at an index masked to 2 bits. The CSRs written
 *          are hgeie (all ones, then 0), sstatus.SIE (cleared), sie (0),
 *          and stvec.
 */
#include "m13.h"

	.option norvc
	.option norelax

#define SSTATUS_SIE		0x2
#define CSR_HGEIE		0x607
#define SBI_EID_HSM		0x48534d
#define SBI_HSM_HART_START	0
#define SBI_ERR_INVALID_PARAM	-3
/* A slot's words (struct be_m13_slot). */
#define SLOT_STATE		0
#define SLOT_BOOTED		8
#define SLOT_ONES		16
#define SLOT_ZERO		24
#define SLOT_A0			32
#define SLOT_SCAUSE		40
#define SLOT_SEPC		48
#define SLOT_STVAL		56

	.section .text.be_m13_harts, "ax", @progbits

	/*
	 * be_m13_p1(hart): P1 on this hart (section 2): hgeie as booted, all
	 * ones written and read back, 0 written and read back, the three reads
	 * into the slot of HART. A leaf: t0 to t2 alone, and no stack.
	 */
	.balign 4
	.globl be_m13_p1
	.type be_m13_p1, @function
be_m13_p1:
	andi	t0, a0, 3
	slli	t0, t0, 6
	lla	t1, be_m13_slots
	add	t1, t1, t0
	csrr	t2, CSR_HGEIE
	sd	t2, SLOT_BOOTED(t1)
	li	t2, -1
	csrw	CSR_HGEIE, t2
	csrr	t2, CSR_HGEIE
	sd	t2, SLOT_ONES(t1)
	csrw	CSR_HGEIE, zero
	csrr	t2, CSR_HGEIE
	sd	t2, SLOT_ZERO(t1)
	ret
	.size be_m13_p1, . - be_m13_p1

	/*
	 * be_m13_hart_run(hart): HART (0 to 2) started by HSM at
	 * be_m13_secondary, its slot STARTING first; then its slot polled until
	 * it changes, or until 2^27 ticks of time have passed. Returns a0 =
	 * HSM's error (SBI_ERR_INVALID_PARAM for a hart above 2, which is not
	 * started) and a1 = the slot's state (STARTING: no report in time).
	 */
	.balign 4
	.globl be_m13_hart_run
	.type be_m13_hart_run, @function
be_m13_hart_run:
	li	t0, 2
	bgtu	a0, t0, 2f
	andi	t1, a0, 3
	slli	t1, t1, 6
	lla	t5, be_m13_slots
	add	t5, t5, t1
	li	t1, BE_M13_STARTING
	sd	t1, SLOT_STATE(t5)
	fence	rw, rw
	mv	a2, a0
	lla	a1, be_m13_secondary
	li	a6, SBI_HSM_HART_START
	li	a7, SBI_EID_HSM
be_m13_ecall_hsm:
	ecall
	bnez	a0, 3f
	csrr	t2, time
	li	t3, BE_M13_WAIT_TICKS
	add	t2, t2, t3
1:	fence	rw, rw
	ld	a1, SLOT_STATE(t5)
	li	t3, BE_M13_STARTING
	bne	a1, t3, 3f
	csrr	t3, time
	bltu	t3, t2, 1b
	ret
2:	li	a0, SBI_ERR_INVALID_PARAM
	li	a1, 0
3:	fence	rw, rw
	ret
	.size be_m13_hart_run, . - be_m13_hart_run

	/*
	 * HSM's start address. a1 above 2 names no slot of ours: park, having
	 * touched nothing. Otherwise s0 is the slot of a1, for this path and
	 * for be_m13_secondary_trap, which stvec names from here on; the a0
	 * seen is recorded, and checked again (rule 6): a hart above 2, or not
	 * the hart started, is REFUSED before any read.
	 */
	.balign 4
	.globl be_m13_secondary
	.type be_m13_secondary, @function
be_m13_secondary:
	csrci	sstatus, SSTATUS_SIE
	csrw	sie, zero
	li	t0, 2
	bgtu	a1, t0, 2f
	andi	s0, a1, 3
	slli	s0, s0, 6
	lla	t0, be_m13_slots
	add	s0, s0, t0
	lla	t0, be_m13_secondary_trap
	csrw	stvec, t0
	sd	a0, SLOT_A0(s0)
	li	t0, 2
	bgtu	a0, t0, 1f
	bne	a0, a1, 1f
	call	be_m13_p1
	fence	rw, rw
	li	t0, BE_M13_DONE
	sd	t0, SLOT_STATE(s0)
	j	be_m13_park
1:	fence	rw, rw
	li	t0, BE_M13_REFUSED
	sd	t0, SLOT_STATE(s0)
2:	j	be_m13_park
	.size be_m13_secondary, . - be_m13_secondary

	/* Any trap of a started hart: recorded in its slot, then parked. */
	.balign 4
	.globl be_m13_secondary_trap
	.type be_m13_secondary_trap, @function
be_m13_secondary_trap:
	csrr	t0, scause
	sd	t0, SLOT_SCAUSE(s0)
	csrr	t0, sepc
	sd	t0, SLOT_SEPC(s0)
	csrr	t0, stval
	sd	t0, SLOT_STVAL(s0)
	fence	rw, rw
	li	t0, BE_M13_TRAPPED
	sd	t0, SLOT_STATE(s0)
	j	be_m13_park
	.size be_m13_secondary_trap, . - be_m13_secondary_trap

	.section .data.be_m13_slots, "aw", @progbits
	.balign 64
	.globl be_m13_slots
	.type be_m13_slots, @object
be_m13_slots:
	.space	256
	.size be_m13_slots, . - be_m13_slots
