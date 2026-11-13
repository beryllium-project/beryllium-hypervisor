/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jmorris@namei.org> */
/*
 * Purpose: the layout and the step codes shared by the firmware tests'
 *          S-mode payload (fwtest.c, fwtest.S) and their tool, fwtest.py,
 *          which reads every FWT_ definition of this file.
 * Trust:   test-only. The payload runs on the firmware under test; the tool
 *          judges the run from memory and registers read by the QEMU
 *          oracle with the machine stopped.
 * Scope:   one payload for every test: each hart runs its own list of
 *          steps from the script area and writes its results into its own
 *          state area.
 */
#ifndef FWTEST_H
#define FWTEST_H

/* Memory layout (QEMU virt, RAM at 0x80000000) */
#define FWT_TEXT_BASE		0x80200000
#define FWT_TEXT_ORDER		16
#define FWT_SCRIPT_BASE		0x80400000
#define FWT_SCRIPT_ORDER	15
#define FWT_SCRIPT_STRIDE	0x1000
#define FWT_STATE_BASE		0x80500000
#define FWT_STATE_STRIDE	0x2000
#define FWT_STATE_ORDER		13
#define FWT_WORK_BASE		0x80600000
#define FWT_HARTS		8

/* Script area of a hart: word 0 the step count, steps from word FWT_STEP_OFF */
#define FWT_STEP_OFF		8
#define FWT_STEP_WORDS		8
#define FWT_STEPS_MAX		60

/* State area of a hart: words of its first page, its stack above */
#define FWT_ST_MAGIC		0
#define FWT_ST_CUR		1
#define FWT_ST_ENTRIES		2
#define FWT_ST_DONE		3
#define FWT_ST_FLAG		4
#define FWT_ST_UNEXPECTED	5
#define FWT_MAGIC		0x6677746573740a01
#define FWT_ENTRY_OFF		8
#define FWT_ENTRY_WORDS		12
#define FWT_ENTRIES_MAX		4
#define FWT_RES_OFF		64
#define FWT_RES_WORDS		6
#define FWT_CTX_BYTE_OFF	0xe00
#define FWT_MSG_BYTE_OFF	0xf00

/* Entry record words: what a hart sees each time the payload is entered */
#define FWT_EN_A0		0
#define FWT_EN_A1		1
#define FWT_EN_TIME		2
#define FWT_EN_STVEC		3
#define FWT_EN_SSCRATCH		4
#define FWT_EN_SIE		5
#define FWT_EN_SATP		6
#define FWT_EN_SSTATUS		7
#define FWT_EN_HGATP		8
#define FWT_EN_VSATP		9
#define FWT_EN_STIMECMP		10
#define FWT_EN_HSTATUS		11

/* Result words of a step */
#define FWT_RES_STATUS		0
#define FWT_RES_ERROR		1
#define FWT_RES_VALUE		2
#define FWT_RES_CAUSE		3
#define FWT_RES_TVAL		4
#define FWT_RES_EXTRA		5

/* Step status */
#define FWT_S_NONE		0
#define FWT_S_RUNNING		1
#define FWT_S_DONE		2
#define FWT_S_TRAPPED		3
#define FWT_S_ENTERED		4
#define FWT_S_TIMEOUT		5

/* Step operations: word 0 of a step is op | mode << 8 */
#define FWT_OP_SBI		1	/* x0 ext, x1 fid, x2..x4 a0..a2 */
#define FWT_OP_LOAD		2	/* x0 address, x1 width 4 or 8 */
#define FWT_OP_STORE		3	/* x0 address, x1 value */
#define FWT_OP_FETCH		4	/* x0 address, x1 argument (a2 there) */
#define FWT_OP_CBO		5	/* x0 address */
#define FWT_OP_AMO		6	/* x0 address, x1 addend */
#define FWT_OP_ILL32		7
#define FWT_OP_ILL16		8
#define FWT_OP_CSRW		9	/* x0 CSR, x1 value */
#define FWT_OP_CSRR		10	/* x0 CSR */
#define FWT_OP_WAIT		11	/* x0 address, x1 value, x2 ticks */
#define FWT_OP_DELAY		12	/* x0 ticks */
#define FWT_OP_SUSPEND		13	/* x0 type, x1 ticks to the timer */
#define FWT_OP_STOP		14
#define FWT_OP_CONSOLE		15	/* x0 length, x1 address, x2 a2 */

#define FWT_MODE_HS		0
#define FWT_MODE_VS		1
#define FWT_MODE_VU		2

/* CSRs that FWT_OP_CSRW and FWT_OP_CSRR know */
#define FWT_CSR_STIMECMP	0x14d
#define FWT_CSR_HGATP		0x680
#define FWT_CSR_VSATP		0x280
#define FWT_CSR_SIE		0x104
#define FWT_CSR_SSTATUS		0x100

/* Context of the step in progress, at FWT_CTX_BYTE_OFF (bytes) */
#define FWT_CTX_SP		0
#define FWT_CTX_RA		8
#define FWT_CTX_S0		16	/* s0..s11: 12 words */
#define FWT_CTX_A0		112
#define FWT_CTX_CAUSE		120
#define FWT_CTX_TVAL		128
#define FWT_CTX_EPC		136
#define FWT_CTX_HSTATUS		144
#define FWT_CTX_HTVAL		152

#endif
