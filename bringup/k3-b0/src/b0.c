// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B0 / BE-K3-L0BOOT boot checkpoint. Prove that a RAM-loaded
 *          Beryllium image reaches HS-mode C code with zeroed BSS and a
 *          private stack, reports its handoff through SBI DBCN, and ends in
 *          terminal SRST shutdown.
 * Trust:   HS boot code. SBI calls are limited to Base, DBCN console write,
 *          and SRST, as in the accepted R0/R3 allowlist. DBCN receives only
 *          the physical range of this image's own console buffer; satp is
 *          verified Bare, so its address is its physical address.
 * Scope:   entering hart only. No VS entry, G-stage, device, DMA, timer, IPI,
 *          secondary hart, or persistent platform change.
 */
#include "b0.h"
#include "b0-format.h"

#define SBI_EXT_BASE			0x10UL
#define SBI_EXT_HSM			0x48534dUL
#define SBI_EXT_SRST			0x53525354UL
#define SBI_EXT_DBCN			0x4442434eUL

#define SBI_BASE_GET_SPEC_VERSION	0UL
#define SBI_BASE_GET_IMPL_ID		1UL
#define SBI_BASE_GET_IMPL_VERSION	2UL
#define SBI_BASE_PROBE_EXTENSION	3UL
#define SBI_DBCN_CONSOLE_WRITE		0UL
#define SBI_SRST_SYSTEM_RESET		0UL
#define SBI_SRST_TYPE_SHUTDOWN		0UL
#define SBI_SRST_REASON_NONE		0UL

#define BE_B0_DBCN_MAX_ITERATIONS	256UL
#define BE_B0_FDT_MAGIC			0xd00dfeedUL

struct be_b0_sbiret {
	long error;
	unsigned long value;
};

static char be_b0_console[BE_B0_LINE_CAPACITY] __attribute__((aligned(64)));
static unsigned long be_b0_console_ready;
static unsigned long be_b0_trap_depth;

static struct be_b0_sbiret be_b0_sbi(unsigned long eid, unsigned long fid,
				     unsigned long arg0, unsigned long arg1,
				     unsigned long arg2)
{
	register unsigned long a0 __asm__("a0") = arg0;
	register unsigned long a1 __asm__("a1") = arg1;
	register unsigned long a2 __asm__("a2") = arg2;
	register unsigned long a6 __asm__("a6") = fid;
	register unsigned long a7 __asm__("a7") = eid;
	struct be_b0_sbiret result;

	__asm__ __volatile__("ecall"
			     : "+r"(a0), "+r"(a1)
			     : "r"(a2), "r"(a6), "r"(a7)
			     : "memory");
	result.error = (long)a0;
	result.value = a1;
	return result;
}

static struct be_b0_sbiret be_b0_sbi_base(unsigned long fid,
					  unsigned long arg0)
{
	return be_b0_sbi(SBI_EXT_BASE, fid, arg0, 0UL, 0UL);
}

static unsigned long be_b0_probe(unsigned long extension)
{
	struct be_b0_sbiret result =
		be_b0_sbi_base(SBI_BASE_PROBE_EXTENSION, extension);

	return result.error == 0L && result.value != 0UL ? 1UL : 0UL;
}

static unsigned long be_b0_read_satp(void)
{
	unsigned long value;

	__asm__ __volatile__("csrr %0, satp" : "=r"(value));
	return value;
}

static unsigned long be_b0_read_sstatus(void)
{
	unsigned long value;

	__asm__ __volatile__("csrr %0, sstatus" : "=r"(value));
	return value;
}

/* hstatus (CSR 0x600) exists only with the H extension; absence traps. */
static unsigned long be_b0_read_hstatus(void)
{
	unsigned long value;

	__asm__ __volatile__("csrr %0, 0x600" : "=r"(value));
	return value;
}

static unsigned long be_b0_read_sp(void)
{
	unsigned long value;

	__asm__ __volatile__("mv %0, sp" : "=r"(value));
	return value;
}

static unsigned long be_b0_bss_is_zero(void)
{
	const volatile unsigned long *word =
		(const volatile unsigned long *)__be_b0_bss_start;
	const volatile unsigned long *end =
		(const volatile unsigned long *)__be_b0_bss_end;

	for (; word < end; ++word) {
		if (*word != 0UL)
			return 0UL;
	}
	return 1UL;
}

static unsigned long be_b0_read_be32(unsigned long address)
{
	const volatile unsigned char *byte =
		(const volatile unsigned char *)address;

	return ((unsigned long)byte[0] << 24) |
		((unsigned long)byte[1] << 16) |
		((unsigned long)byte[2] << 8) |
		(unsigned long)byte[3];
}

/*
 * Bounded DBCN write of the console buffer. A conforming SBI may consume
 * fewer bytes than requested, including zero; progress accumulates up to a
 * fixed iteration cap. Any SBI error or over-report ends the write.
 */
static long be_b0_dbcn_write(unsigned long length)
{
	unsigned long base = (unsigned long)be_b0_console;
	unsigned long offset = 0UL;
	unsigned long iteration;

	for (iteration = 0UL; offset < length; ++iteration) {
		struct be_b0_sbiret result;

		if (iteration >= BE_B0_DBCN_MAX_ITERATIONS)
			return -1L;
		result = be_b0_sbi(SBI_EXT_DBCN, SBI_DBCN_CONSOLE_WRITE,
				   length - offset, base + offset, 0UL);
		if (result.error != 0L)
			return result.error;
		if (result.value > length - offset)
			return -1L;
		offset += result.value;
	}
	return 0L;
}

static void be_b0_emit(struct be_b0_line *line)
{
	be_b0_line_text(line, "\n");
	if (be_b0_console_ready != 0UL && line->overflow == 0UL)
		(void)be_b0_dbcn_write(line->length);
}

static struct be_b0_line be_b0_begin(const char *marker)
{
	struct be_b0_line line;

	be_b0_line_init(&line, be_b0_console, BE_B0_LINE_CAPACITY);
	be_b0_line_text(&line, marker);
	return line;
}

static void be_b0_shutdown_and_halt(void) __attribute__((noreturn));

static void be_b0_shutdown_and_halt(void)
{
	struct be_b0_sbiret result;
	struct be_b0_line line;

	result = be_b0_sbi(SBI_EXT_SRST, SBI_SRST_SYSTEM_RESET,
			   SBI_SRST_TYPE_SHUTDOWN, SBI_SRST_REASON_NONE, 0UL);
	line = be_b0_begin("BE_B0:FAIL SRST_RETURNED error=");
	be_b0_line_hex(&line, (unsigned long)result.error);
	be_b0_emit(&line);
	be_b0_halt();
}

static void be_b0_fail(const char *reason, unsigned long value)
	__attribute__((noreturn));

static void be_b0_fail(const char *reason, unsigned long value)
{
	struct be_b0_line line = be_b0_begin("BE_B0:FAIL ");

	be_b0_line_text(&line, reason);
	be_b0_line_text(&line, " value=");
	be_b0_line_hex(&line, value);
	be_b0_emit(&line);
	be_b0_shutdown_and_halt();
}

void be_b0_trap(unsigned long scause, unsigned long sepc, unsigned long stval)
{
	struct be_b0_line line;

	if (be_b0_trap_depth != 0UL)
		be_b0_halt();
	be_b0_trap_depth = 1UL;

	line = be_b0_begin("BE_B0:FAIL TRAP scause=");
	be_b0_line_hex(&line, scause);
	be_b0_line_text(&line, " sepc=");
	be_b0_line_hex(&line, sepc);
	be_b0_line_text(&line, " stval=");
	be_b0_line_hex(&line, stval);
	be_b0_emit(&line);
	be_b0_shutdown_and_halt();
}

void be_b0_main(unsigned long hart, unsigned long fdt, unsigned long base)
{
	struct be_b0_sbiret spec;
	struct be_b0_sbiret impl;
	struct be_b0_sbiret impl_version;
	struct be_b0_line line;
	unsigned long bss_zero = be_b0_bss_is_zero();
	unsigned long satp;
	unsigned long srst;
	unsigned long hsm;

	/* Without DBCN nothing can be reported: request shutdown and halt. */
	spec = be_b0_sbi_base(SBI_BASE_GET_SPEC_VERSION, 0UL);
	if (spec.error != 0L || be_b0_probe(SBI_EXT_DBCN) == 0UL)
		be_b0_shutdown_and_halt();
	be_b0_console_ready = 1UL;

	line = be_b0_begin("BE_B0:01 ENTRY hart=");
	be_b0_line_hex(&line, hart);
	be_b0_line_text(&line, " base=");
	be_b0_line_hex(&line, base);
	be_b0_line_text(&line, " fdt=");
	be_b0_line_hex(&line, fdt);
	be_b0_line_text(&line, " bss_zero=");
	be_b0_line_flag(&line, bss_zero);
	be_b0_emit(&line);
	if (bss_zero == 0UL)
		be_b0_fail("BSS_NOT_ZERO", (unsigned long)__be_b0_bss_start);

	impl = be_b0_sbi_base(SBI_BASE_GET_IMPL_ID, 0UL);
	impl_version = be_b0_sbi_base(SBI_BASE_GET_IMPL_VERSION, 0UL);
	line = be_b0_begin("BE_B0:02 SBI spec=");
	be_b0_line_hex(&line, spec.value);
	be_b0_line_text(&line, " impl=");
	be_b0_line_hex(&line, impl.value);
	be_b0_line_text(&line, " impl_version=");
	be_b0_line_hex(&line, impl_version.value);
	be_b0_emit(&line);

	srst = be_b0_probe(SBI_EXT_SRST);
	hsm = be_b0_probe(SBI_EXT_HSM);
	line = be_b0_begin("BE_B0:03 EXT dbcn=1 srst=");
	be_b0_line_flag(&line, srst);
	be_b0_line_text(&line, " hsm=");
	be_b0_line_flag(&line, hsm);
	be_b0_emit(&line);
	if (srst == 0UL)
		be_b0_fail("SRST_UNAVAILABLE", SBI_EXT_SRST);

	satp = be_b0_read_satp();
	line = be_b0_begin("BE_B0:04 HS satp=");
	be_b0_line_hex(&line, satp);
	be_b0_line_text(&line, " sstatus=");
	be_b0_line_hex(&line, be_b0_read_sstatus());
	be_b0_line_text(&line, " hstatus=");
	be_b0_line_hex(&line, be_b0_read_hstatus());
	be_b0_line_text(&line, " sp=");
	be_b0_line_hex(&line, be_b0_read_sp());
	be_b0_line_text(&line, " stack=");
	be_b0_line_hex(&line, (unsigned long)__be_b0_stack_start);
	be_b0_emit(&line);
	if (satp != 0UL)
		be_b0_fail("SATP_NOT_BARE", satp);

	if (fdt == 0UL || (fdt & 7UL) != 0UL) {
		line = be_b0_begin("BE_B0:05 FDT skipped");
		be_b0_emit(&line);
	} else {
		unsigned long magic = be_b0_read_be32(fdt);

		line = be_b0_begin("BE_B0:05 FDT magic=");
		be_b0_line_hex(&line, magic);
		be_b0_line_text(&line, " totalsize=");
		be_b0_line_hex(&line, be_b0_read_be32(fdt + 4UL));
		be_b0_emit(&line);
		if (magic != BE_B0_FDT_MAGIC)
			be_b0_fail("FDT_MAGIC", magic);
	}

	line = be_b0_begin("BE_B0:06 BE-K3-L0BOOT PASS image_end=");
	be_b0_line_hex(&line, (unsigned long)__be_b0_image_end);
	be_b0_emit(&line);

	line = be_b0_begin("BE_B0:07 SRST_SHUTDOWN");
	be_b0_emit(&line);
	be_b0_shutdown_and_halt();
}
