// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the K3 B5 test guest. A bare-metal VS program that prints guest
 *          lines 01-09 of the plan's markers through DBCN, exercising every
 *          function of the B5-only SBI subset, its refusals, and the
 *          hardware-delivered Sstc VS timer, then requests SRST shutdown:
 *          reason 0 when every check passed, reason 1 otherwise.
 * Trust:   untrusted VS code. The monitor decides every call and prefixes
 *          every line this guest writes.
 * Scope:   B5 only (planning/k3-b5-plan.md). Exactly one compile-time switch
 *          BE_B5_GUEST_<VARIANT> may add one action after line 01 for the
 *          QEMU negative variants; without one, this is the pass run.
 */
#include "sbi.h"

#define GUEST_PRIVATE		0x40000000UL
#define GUEST_UNMAPPED		0x40001000UL
#define GUEST_CODE		0x40010000UL
#define SCAUSE_SUPERVISOR_TIMER	(0x8000000000000000UL | 5UL)
#define SIE_STIE		(1UL << 5)
#define SIP_STIP		(1UL << 5)
#define SSTATUS_SIE		(1UL << 1)
#define TIMER_DELAY		0x10000UL
#define TIMER_POLL_BOUND	(1UL << 20)
#define LINE_CAPACITY		128U
#define WRITE_ATTEMPTS		16U

/* One out-of-line copy of each helper keeps both builds inside one page. */
#define GUEST_HELPER		static __attribute__((noinline))

static char line[LINE_CAPACITY];
static unsigned long line_length;
static int failed;
static volatile unsigned long timer_cause;
static volatile unsigned long timer_at;
static volatile int timer_fired;
static volatile int timer_cleared;

void guest_main(unsigned long hart, unsigned long dtb)
	__attribute__((noreturn));
void guest_trap(unsigned long cause);

GUEST_HELPER void expect(int condition)
{
	if (!condition)
		failed = 1;
}

static unsigned long read_time(void)
{
	unsigned long value;

	__asm__ __volatile__("csrr %0, time" : "=r"(value));
	return value;
}

static void stop(unsigned long reason) __attribute__((noreturn));
static void stop(unsigned long reason)
{
	(void)sbi_call(SBI_EID_SRST, SBI_SRST_SYSTEM_RESET,
		       SBI_SRST_TYPE_SHUTDOWN, reason, 0UL);
	/* SRST never returns to the guest; an illegal instruction ends it. */
	__asm__ __volatile__("unimp");
	__builtin_unreachable();
}

GUEST_HELPER void put_char(char byte)
{
	if (line_length < LINE_CAPACITY)
		line[line_length++] = byte;
	else
		failed = 1;
}

GUEST_HELPER void put_text(const char *text)
{
	while (*text != '\0')
		put_char(*text++);
}

GUEST_HELPER void put_hex(unsigned long value)
{
	static const char digits[] = "0123456789abcdef";
	unsigned int shift = 60U;

	put_text("0x");
	while (shift > 0U && ((value >> shift) & 0xfUL) == 0UL)
		shift -= 4U;
	for (;;) {
		put_char(digits[(value >> shift) & 0xfUL]);
		if (shift == 0U)
			break;
		shift -= 4U;
	}
}

GUEST_HELPER void put_decimal(long value)
{
	char digits[20];
	unsigned int count = 0U;
	unsigned long magnitude = (unsigned long)value;

	if (value < 0) {
		put_char('-');
		magnitude = 0UL - magnitude;
	}
	do {
		digits[count++] = (char)('0' + (int)(magnitude % 10UL));
		magnitude /= 10UL;
	} while (magnitude != 0UL && count < sizeof(digits));
	while (count > 0U)
		put_char(digits[--count]);
}

/* Write the line and its LF through DBCN, accepting partial progress. */
GUEST_HELPER void end_line(void)
{
	unsigned long offset = 0UL;
	unsigned int attempt;

	put_char('\n');
	for (attempt = 0U; attempt < WRITE_ATTEMPTS && offset < line_length;
	     ++attempt) {
		struct sbiret ret = sbi_call(SBI_EID_DBCN, SBI_DBCN_WRITE,
					     line_length - offset,
					     (unsigned long)&line[offset], 0UL);

		if (ret.error != 0L || ret.value > line_length - offset)
			break;
		offset += ret.value;
	}
	expect(offset == line_length);
	line_length = 0UL;
}

GUEST_HELPER long call_error(unsigned long eid, unsigned long fid,
			     unsigned long argument0, unsigned long argument1,
			     unsigned long argument2)
{
	return sbi_call(eid, fid, argument0, argument1, argument2).error;
}

GUEST_HELPER unsigned long base_value(unsigned long fid,
				      unsigned long argument0)
{
	struct sbiret ret = sbi_call(SBI_EID_BASE, fid, argument0, 0UL, 0UL);

	expect(ret.error == 0L);
	return ret.value;
}

#if defined(BE_B5_GUEST_DENIED_LOAD)
static void variant(void)
{
	/* GPA 0x4000_1000 is unmapped: load guest-page fault, cause 21. */
	(void)*(volatile const unsigned long *)GUEST_UNMAPPED;
}
#elif defined(BE_B5_GUEST_CODE_STORE)
static void variant(void)
{
	/* The code page is R-X: store guest-page fault, cause 23. */
	*(volatile unsigned int *)GUEST_CODE = 0U;
}
#elif defined(BE_B5_GUEST_SATP_WRITE)
static void variant(void)
{
	/* hstatus.VTVM: virtual-instruction exception, cause 22. */
	__asm__ __volatile__("csrw satp, zero" ::: "memory");
}
#elif defined(BE_B5_GUEST_FP)
static void variant(void)
{
	/* FS is Off at both levels: illegal-instruction exception. */
	__asm__ __volatile__(".option push\n\t.option arch, +f\n\t"
			     "fmv.w.x ft0, zero\n\t.option pop" ::: "memory");
}
#elif defined(BE_B5_GUEST_WFI)
static void variant(void)
{
	/* hstatus.VTW: virtual-instruction exception (QEMU traps at once). */
	__asm__ __volatile__("wfi" ::: "memory");
}
#elif defined(BE_B5_GUEST_EXIT_BUDGET)
static void variant(void)
{
	/* Every call is an exit; the monitor stops after 1024. */
	for (;;)
		(void)base_value(SBI_BASE_GET_SPEC_VERSION, 0UL);
}
#elif defined(BE_B5_GUEST_GUEST_FAIL)
static void variant(void)
{
	/* Report failure: RESULT fail, then SRST reason 1. */
	failed = 1;
}
#else
static void variant(void)
{
}
#endif

static void base_line(void)
{
	unsigned long spec = base_value(SBI_BASE_GET_SPEC_VERSION, 0UL);
	unsigned long impl = base_value(SBI_BASE_GET_IMPL_ID, 0UL);
	unsigned long version = base_value(SBI_BASE_GET_IMPL_VERSION, 0UL);
	unsigned long mvendorid = base_value(SBI_BASE_GET_MVENDORID, 0UL);
	unsigned long marchid = base_value(SBI_BASE_GET_MARCHID, 0UL);
	unsigned long mimpid = base_value(SBI_BASE_GET_MIMPID, 0UL);

	expect(spec == 0x2000000UL && impl == 0x4245UL && version == 1UL &&
	       mvendorid == 0UL && marchid == 0UL && mimpid == 0UL);
	put_text("02 BASE spec=");
	put_hex(spec);
	put_text(" impl=");
	put_hex(impl);
	put_text(" version=");
	put_hex(version);
	put_text(" mvendorid=");
	put_hex(mvendorid);
	put_text(" marchid=");
	put_hex(marchid);
	put_text(" mimpid=");
	put_hex(mimpid);
	end_line();
}

static void probe_line(void)
{
	unsigned long base = base_value(SBI_BASE_PROBE_EXTENSION,
					SBI_EID_BASE);
	unsigned long time = base_value(SBI_BASE_PROBE_EXTENSION,
					SBI_EID_TIME);
	unsigned long dbcn = base_value(SBI_BASE_PROBE_EXTENSION,
					SBI_EID_DBCN);
	unsigned long srst = base_value(SBI_BASE_PROBE_EXTENSION,
					SBI_EID_SRST);
	unsigned long hsm = base_value(SBI_BASE_PROBE_EXTENSION, SBI_EID_HSM);
	unsigned long ipi = base_value(SBI_BASE_PROBE_EXTENSION, SBI_EID_IPI);
	unsigned long rfence = base_value(SBI_BASE_PROBE_EXTENSION,
					  SBI_EID_RFENCE);
	unsigned long legacy = base_value(SBI_BASE_PROBE_EXTENSION,
					  SBI_EID_LEGACY_PUTCHAR);

	expect(base == 1UL && time == 1UL && dbcn == 1UL && srst == 1UL &&
	       hsm == 0UL && ipi == 0UL && rfence == 0UL && legacy == 0UL);
	put_text("03 PROBE base=");
	put_decimal((long)base);
	put_text(" time=");
	put_decimal((long)time);
	put_text(" dbcn=");
	put_decimal((long)dbcn);
	put_text(" srst=");
	put_decimal((long)srst);
	put_text(" hsm=");
	put_decimal((long)hsm);
	put_text(" ipi=");
	put_decimal((long)ipi);
	put_text(" rfence=");
	put_decimal((long)rfence);
	put_text(" legacy=");
	put_decimal((long)legacy);
	end_line();
}

static void unsupported_line(void)
{
	long eid = call_error(SBI_EID_UNASSIGNED, 0UL, 0UL, 0UL, 0UL);
	long fid = call_error(SBI_EID_BASE, SBI_BASE_UNASSIGNED_FID, 0UL, 0UL,
			      0UL);
	long legacy_putchar = call_error(SBI_EID_LEGACY_PUTCHAR, 0UL, 'x',
					 0UL, 0UL);

	expect(eid == SBI_ERR_NOT_SUPPORTED && fid == SBI_ERR_NOT_SUPPORTED &&
	       legacy_putchar == SBI_ERR_NOT_SUPPORTED);
	put_text("04 UNSUPPORTED eid=");
	put_decimal(eid);
	put_text(" fid=");
	put_decimal(fid);
	put_text(" legacy_putchar=");
	put_decimal(legacy_putchar);
	end_line();
}

static void dbcn_refused_line(void)
{
	long unmapped = call_error(SBI_EID_DBCN, SBI_DBCN_WRITE, 8UL,
				   GUEST_UNMAPPED, 0UL);
	long cross = call_error(SBI_EID_DBCN, SBI_DBCN_WRITE, 32UL,
				GUEST_UNMAPPED - 16UL, 0UL);
	long high = call_error(SBI_EID_DBCN, SBI_DBCN_WRITE, 4UL,
			       GUEST_PRIVATE, 1UL);
	long wrap = call_error(SBI_EID_DBCN, SBI_DBCN_WRITE, ~0UL,
			       GUEST_PRIVATE, 0UL);
	long read = call_error(SBI_EID_DBCN, SBI_DBCN_READ, 4UL, GUEST_PRIVATE,
			       0UL);

	expect(unmapped == SBI_ERR_INVALID_PARAM &&
	       cross == SBI_ERR_INVALID_PARAM &&
	       high == SBI_ERR_INVALID_PARAM &&
	       wrap == SBI_ERR_INVALID_PARAM && read == SBI_ERR_DENIED);
	put_text("05 DBCN_REFUSED unmapped=");
	put_decimal(unmapped);
	put_text(" cross=");
	put_decimal(cross);
	put_text(" high=");
	put_decimal(high);
	put_text(" wrap=");
	put_decimal(wrap);
	put_text(" read=");
	put_decimal(read);
	end_line();
}

/* Line 06 goes out one console_write_byte call per byte. */
static void write_byte_line(void)
{
	static const char text[] = "06 WRITE_BYTE ok\n";
	unsigned int index;

	for (index = 0U; text[index] != '\0'; ++index) {
		struct sbiret ret = sbi_call(SBI_EID_DBCN, SBI_DBCN_WRITE_BYTE,
					     (unsigned char)text[index], 0UL,
					     0UL);

		expect(ret.error == 0L && ret.value == 0UL);
	}
}

static void srst_refused_line(void)
{
	long type = call_error(SBI_EID_SRST, SBI_SRST_SYSTEM_RESET,
			       SBI_SRST_TYPE_RESERVED, SBI_SRST_REASON_NONE,
			       0UL);
	long reason = call_error(SBI_EID_SRST, SBI_SRST_SYSTEM_RESET,
				 SBI_SRST_TYPE_SHUTDOWN,
				 SBI_SRST_REASON_RESERVED, 0UL);
	long reboot = call_error(SBI_EID_SRST, SBI_SRST_SYSTEM_RESET,
				 SBI_SRST_TYPE_COLD_REBOOT,
				 SBI_SRST_REASON_NONE, 0UL);

	expect(type == SBI_ERR_INVALID_PARAM &&
	       reason == SBI_ERR_INVALID_PARAM &&
	       reboot == SBI_ERR_NOT_SUPPORTED);
	put_text("07 SRST_REFUSED type=");
	put_decimal(type);
	put_text(" reason=");
	put_decimal(reason);
	put_text(" reboot=");
	put_decimal(reboot);
	end_line();
}

/*
 * The VS timer: the monitor delegates only VSTI, so this handler sees only
 * the supervisor timer interrupt. Anything else fails the run at once.
 */
void guest_trap(unsigned long cause)
{
	struct sbiret ret;
	unsigned long pending;

	timer_cause = cause;
	if (cause != SCAUSE_SUPERVISOR_TIMER)
		stop(SBI_SRST_REASON_FAILURE);
	timer_at = read_time();
	ret = sbi_call(SBI_EID_TIME, SBI_TIME_SET_TIMER, ~0UL, 0UL, 0UL);
	__asm__ __volatile__("csrr %0, sip" : "=r"(pending));
	timer_cleared = ret.error == 0L && (pending & SIP_STIP) == 0UL;
	timer_fired = 1;
}

static void timer_line(void)
{
	unsigned long start;
	unsigned long deadline;
	int after_deadline;
	struct sbiret ret;

	__asm__ __volatile__("csrs sie, %0" : : "r"(SIE_STIE) : "memory");
	__asm__ __volatile__("csrs sstatus, %0" : : "r"(SSTATUS_SIE)
			     : "memory");
	start = read_time();
	deadline = start + TIMER_DELAY;
	ret = sbi_call(SBI_EID_TIME, SBI_TIME_SET_TIMER, deadline, 0UL, 0UL);
	expect(ret.error == 0L);
	/* Poll, without wfi, at most TIMER_POLL_BOUND ticks past the deadline. */
	while (timer_fired == 0 &&
	       read_time() - start < TIMER_DELAY + TIMER_POLL_BOUND)
		;
	__asm__ __volatile__("csrc sstatus, %0" : : "r"(SSTATUS_SIE)
			     : "memory");
	__asm__ __volatile__("csrc sie, %0" : : "r"(SIE_STIE) : "memory");
	after_deadline = timer_fired != 0 && timer_at >= deadline;
	expect(timer_fired != 0 && timer_cause == SCAUSE_SUPERVISOR_TIMER &&
	       after_deadline && timer_cleared != 0);
	put_text("08 TIMER cause=");
	put_hex(timer_cause);
	put_text(" after_deadline=");
	put_decimal(after_deadline);
	put_text(" cleared=");
	put_decimal(timer_cleared);
	end_line();
}

void guest_main(unsigned long hart, unsigned long dtb)
{
	expect(hart == 0UL && dtb == 0UL);
	put_text("01 START hart=");
	put_hex(hart);
	put_text(" dtb=");
	put_hex(dtb);
	end_line();
	variant();
	base_line();
	probe_line();
	unsupported_line();
	dbcn_refused_line();
	write_byte_line();
	srst_refused_line();
	timer_line();
	put_text(failed == 0 ? "09 RESULT pass" : "09 RESULT fail");
	end_line();
	stop(failed == 0 ? SBI_SRST_REASON_NONE : SBI_SRST_REASON_FAILURE);
}
