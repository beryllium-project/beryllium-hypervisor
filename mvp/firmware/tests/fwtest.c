/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jmorris@namei.org> */
/*
 * Purpose: the firmware tests' payload: an S-mode interpreter of the step
 *          list of each hart (fwtest.h). Each entry into the payload is
 *          recorded; a step whose call does not return (a commit, a
 *          non-retentive suspend) is marked entered when the hart comes
 *          back in at its entry.
 * Trust:   test-only. It has no data or bss: everything it writes is in
 *          its hart's state area, and every step runs in a protected call,
 *          so a trap ends the step, never the hart.
 * Scope:   the operations of fwtest.h, in HS-mode, VS-mode, or VU-mode.
 */
#include "fwtest.h"

typedef unsigned long u64;

extern long fwt_protected(void (*fn)(u64 *), u64 *job);
extern u64 fwt_probe(u64 op, u64 addr, u64 arg);
extern void fwt_guest(u64 op, u64 addr, u64 arg, u64 mode);
extern char fwt_guest_done[];
extern char _start[];

#define WORDS(address)	((volatile u64 *)(address))
#define CSR_READ(csr)	({ u64 __v; __asm__ __volatile__( \
			   "csrr %0, " #csr : "=r"(__v)); __v; })
#define CSR_WRITE(csr, v) __asm__ __volatile__("csrw " #csr ", %0" \
						 :: "r"((u64)(v)))

#define SBI_EXT_HSM		0x48534d
#define SBI_EXT_DBCN		0x4442434e
#define SBI_HSM_SUSPEND		3
#define SIE_STIE		0x20

struct sbiret {
	long error;
	long value;
};

static struct sbiret sbi(u64 ext, u64 fid, u64 a0, u64 a1, u64 a2)
{
	register u64 r0 __asm__("a0") = a0;
	register u64 r1 __asm__("a1") = a1;
	register u64 r2 __asm__("a2") = a2;
	register u64 r6 __asm__("a6") = fid;
	register u64 r7 __asm__("a7") = ext;
	struct sbiret ret;

	__asm__ __volatile__("ecall" : "+r"(r0), "+r"(r1)
			     : "r"(r2), "r"(r6), "r"(r7) : "memory");
	ret.error = (long)r0;
	ret.value = (long)r1;
	return ret;
}

static u64 now(void)
{
	return CSR_READ(time);
}

static u64 csr_read_by_number(u64 csr, int *ok)
{
	*ok = 1;
	switch (csr) {
	case FWT_CSR_STIMECMP: return CSR_READ(0x14d);
	case FWT_CSR_HGATP: return CSR_READ(0x680);
	case FWT_CSR_VSATP: return CSR_READ(0x280);
	case FWT_CSR_SIE: return CSR_READ(sie);
	case FWT_CSR_SSTATUS: return CSR_READ(sstatus);
	}
	*ok = 0;
	return 0;
}

static int csr_write_by_number(u64 csr, u64 value)
{
	switch (csr) {
	case FWT_CSR_STIMECMP: CSR_WRITE(0x14d, value); return 1;
	case FWT_CSR_HGATP: CSR_WRITE(0x680, value); return 1;
	case FWT_CSR_VSATP: CSR_WRITE(0x280, value); return 1;
	}
	return 0;
}

/*
 * job: [0] op, [1] mode, [2..8] the step's operands; on return, [9]
 * error, [10] value, [11] status (done or timeout).
 */
#define JOB_ERROR	9
#define JOB_VALUE	10
#define JOB_STATUS	11
#define JOB_WORDS	12

static void run_step(u64 *job)
{
	u64 op = job[0], mode = job[1], *x = &job[2];
	struct sbiret ret;
	u64 deadline;
	int ok;

	job[JOB_STATUS] = FWT_S_DONE;
	switch (op) {
	case FWT_OP_SBI:
		ret = sbi(x[0], x[1], x[2], x[3], x[4]);
		job[JOB_ERROR] = ret.error;
		job[JOB_VALUE] = ret.value;
		return;
	case FWT_OP_CONSOLE:
		ret = sbi(SBI_EXT_DBCN, 0, x[0], x[1], x[2]);
		job[JOB_ERROR] = ret.error;
		job[JOB_VALUE] = ret.value;
		return;
	case FWT_OP_LOAD:
	case FWT_OP_STORE:
	case FWT_OP_FETCH:
	case FWT_OP_CBO:
	case FWT_OP_AMO:
	case FWT_OP_ILL32:
	case FWT_OP_ILL16:
		if (mode == FWT_MODE_HS)
			job[JOB_VALUE] = fwt_probe(op, x[0], x[1]);
		else
			fwt_guest(op, x[0], x[1], mode);
		return;
	case FWT_OP_CSRW:
		job[JOB_ERROR] = csr_write_by_number(x[0], x[1]) ? 0 : -1;
		return;
	case FWT_OP_CSRR:
		job[JOB_VALUE] = csr_read_by_number(x[0], &ok);
		job[JOB_ERROR] = ok ? 0 : -1;
		return;
	case FWT_OP_WAIT:
		deadline = now() + x[2];
		while (WORDS(x[0])[0] != x[1]) {
			if (now() > deadline) {
				job[JOB_STATUS] = FWT_S_TIMEOUT;
				return;
			}
		}
		return;
	case FWT_OP_DELAY:
		deadline = now() + x[0];
		while (now() < deadline)
			;
		return;
	case FWT_OP_SUSPEND:
		CSR_WRITE(0x14d, now() + x[1]);
		__asm__ __volatile__("csrs sie, %0" :: "r"((u64)SIE_STIE));
		ret = sbi(SBI_EXT_HSM, SBI_HSM_SUSPEND, x[0], (u64)_start, 0);
		__asm__ __volatile__("csrc sie, %0" :: "r"((u64)SIE_STIE));
		CSR_WRITE(0x14d, -1UL);
		job[JOB_ERROR] = ret.error;
		job[JOB_VALUE] = ret.value;
		return;
	}
	job[JOB_ERROR] = -1;
}

static void run(u64 hart, u64 state)
{
	u64 script = FWT_SCRIPT_BASE + hart * FWT_SCRIPT_STRIDE;
	volatile u64 *ctx = WORDS(state + FWT_CTX_BYTE_OFF);
	u64 count = WORDS(script)[0], job[JOB_WORDS];
	volatile u64 *step, *res;
	u64 i, j, cause;

	if (count > FWT_STEPS_MAX)
		count = FWT_STEPS_MAX;
	for (i = WORDS(state)[FWT_ST_CUR]; i < count;
	     i = ++WORDS(state)[FWT_ST_CUR]) {
		step = WORDS(script) + FWT_STEP_OFF + i * FWT_STEP_WORDS;
		res = WORDS(state) + FWT_RES_OFF + i * FWT_RES_WORDS;
		if ((step[0] & 0xff) == FWT_OP_STOP)
			break;
		for (j = 0; j < JOB_WORDS; j++)
			job[j] = 0;
		job[0] = step[0] & 0xff;
		job[1] = step[0] >> 8;
		for (j = 0; j < 7; j++)
			job[2 + j] = step[1 + j];
		res[FWT_RES_STATUS] = FWT_S_RUNNING;
		__asm__ __volatile__("fence rw, rw" ::: "memory");
		if (!fwt_protected(run_step, job)) {
			res[FWT_RES_ERROR] = job[JOB_ERROR];
			res[FWT_RES_VALUE] = job[JOB_VALUE];
			res[FWT_RES_EXTRA] = now();
			res[FWT_RES_STATUS] = job[JOB_STATUS];
			continue;
		}
		cause = ctx[FWT_CTX_CAUSE / 8];
		if ((cause == 8 || cause == 10) &&
		    ctx[FWT_CTX_EPC / 8] == (u64)fwt_guest_done) {
			/* The guest ran to its end */
			res[FWT_RES_VALUE] = ctx[FWT_CTX_A0 / 8];
			res[FWT_RES_EXTRA] = now();
			res[FWT_RES_STATUS] = FWT_S_DONE;
			continue;
		}
		res[FWT_RES_CAUSE] = cause;
		res[FWT_RES_TVAL] = ctx[FWT_CTX_TVAL / 8];
		res[FWT_RES_VALUE] = ctx[FWT_CTX_EPC / 8];
		res[FWT_RES_EXTRA] = ctx[FWT_CTX_HSTATUS / 8];
		res[FWT_RES_STATUS] = FWT_S_TRAPPED;
	}
	__asm__ __volatile__("fence rw, rw" ::: "memory");
	WORDS(state)[FWT_ST_DONE] = 1;
	__asm__ __volatile__("fence rw, rw" ::: "memory");
	for (;;)
		__asm__ __volatile__("wfi");
}

void fwt_main(u64 hart, u64 opaque, u64 stvec, u64 sscratch, u64 sie,
	      u64 satp)
{
	u64 state = FWT_STATE_BASE + hart * FWT_STATE_STRIDE;
	volatile u64 *st = WORDS(state), *en, *res;
	u64 n = st[FWT_ST_ENTRIES];
	const char *msg = "fwtest: console\n";
	volatile char *buf = (volatile char *)(state + FWT_MSG_BYTE_OFF);
	u64 i;

	en = st + FWT_ENTRY_OFF +
	     (n < FWT_ENTRIES_MAX ? n : FWT_ENTRIES_MAX - 1) * FWT_ENTRY_WORDS;
	en[FWT_EN_A0] = hart;
	en[FWT_EN_A1] = opaque;
	en[FWT_EN_TIME] = now();
	en[FWT_EN_STVEC] = stvec;
	en[FWT_EN_SSCRATCH] = sscratch;
	en[FWT_EN_SIE] = sie;
	en[FWT_EN_SATP] = satp;
	en[FWT_EN_SSTATUS] = CSR_READ(sstatus);
	en[FWT_EN_HGATP] = CSR_READ(0x680);
	en[FWT_EN_VSATP] = CSR_READ(0x280);
	en[FWT_EN_STIMECMP] = CSR_READ(0x14d);
	en[FWT_EN_HSTATUS] = CSR_READ(0x600);
	st[FWT_ST_ENTRIES] = n + 1;

	/* Every guest trap comes back to HS-mode */
	CSR_WRITE(0x602, 0);
	CSR_WRITE(0x603, 0);

	if (st[FWT_ST_MAGIC] != FWT_MAGIC) {
		for (i = 0; msg[i]; i++)
			buf[i] = msg[i];
		st[FWT_ST_CUR] = 0;
		st[FWT_ST_MAGIC] = FWT_MAGIC;
	} else {
		/* The step in progress did not return: it brought us here */
		res = st + FWT_RES_OFF + st[FWT_ST_CUR] * FWT_RES_WORDS;
		res[FWT_RES_VALUE] = n;
		res[FWT_RES_EXTRA] = en[FWT_EN_TIME];
		res[FWT_RES_STATUS] = FWT_S_ENTERED;
		st[FWT_ST_CUR] = st[FWT_ST_CUR] + 1;
	}
	run(hart, state);
}
