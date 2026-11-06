// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the K3 B6 guest's init (planning/k3-b6-plan.md, Guest software
 *          and Markers), after B0's kexec-rehearsal init: one static program
 *          with raw Linux system calls and no libc. As /init it prints
 *          B6INIT lines 01-05 on /dev/console, checks that it runs as pid 1
 *          on a 7.2.0 riscv64 kernel and that a 1 s nanosleep takes
 *          1000-1999 ms of CLOCK_MONOTONIC time, and then powers off with
 *          reboot(2), which Linux turns into an SBI SRST shutdown.
 *          Two QEMU-only variants, selected by DTBs whose bootargs name
 *          them with rdinit=, dispatch on argv[0] after line 01:
 *          /init-exit exits, so that Linux panics ("Attempted to kill
 *          init"), and /init-rdcycle reads the cycle counter in U-mode,
 *          which B6 does not open to the guest (hcounteren.CY = 0).
 * Trust:   untrusted guest user space. The B6 monitor tags every line it
 *          writes, and the run tools judge the lines.
 * Scope:   B6 only. Built by GCC alone (scripts/build-guest.sh) and
 *          embedded in the guest kernel's initramfs (guest/initramfs.list.in).
 */

#define SYS_WRITE		64L
#define SYS_EXIT		93L
#define SYS_NANOSLEEP		101L
#define SYS_CLOCK_GETTIME	113L
#define SYS_REBOOT		142L
#define SYS_UNAME		160L
#define SYS_GETPID		172L
#define CLOCK_MONOTONIC		1L
#define REBOOT_MAGIC1		0xfee1deadL
#define REBOOT_MAGIC2		672274793L
#define REBOOT_CMD_POWER_OFF	0x4321fedcL

/* The pinned guest kernel (Q4: Linux v7.2) and the plan's sleep window. */
#define EXPECTED_RELEASE	"7.2.0"
#define EXPECTED_MACHINE	"riscv64"
#define SLEEP_MS		1000UL
#define SLEEP_MS_MAX		1999UL
#define NANOSECONDS_PER_SECOND	1000000000L
#define NANOSECONDS_PER_MS	1000000UL
#define UTS_FIELD		65UL
#define LINE_CAPACITY		192UL

struct kernel_timespec {
	long tv_sec;
	long tv_nsec;
};

struct kernel_utsname {
	char sysname[UTS_FIELD];
	char nodename[UTS_FIELD];
	char release[UTS_FIELD];
	char version[UTS_FIELD];
	char machine[UTS_FIELD];
	char domainname[UTS_FIELD];
};

void init_main(const long *stack) __attribute__((noreturn));

/*
 * Linux starts init with sp at argc, followed by the argv pointers; pass
 * that address to init_main.
 */
__asm__(".section .text._start, \"ax\", @progbits\n"
	".globl _start\n"
	".type _start, @function\n"
	"_start:\n"
	"	mv	a0, sp\n"
	"	call	init_main\n"
	"	unimp\n"
	".size _start, . - _start\n"
	".previous\n");

static char line[LINE_CAPACITY];
static unsigned long line_length;
static struct kernel_utsname uts;

static long syscall4(long number, long arg0, long arg1, long arg2, long arg3)
{
	register long a0 __asm__("a0") = arg0;
	register long a1 __asm__("a1") = arg1;
	register long a2 __asm__("a2") = arg2;
	register long a3 __asm__("a3") = arg3;
	register long a7 __asm__("a7") = number;

	__asm__ __volatile__("ecall"
			     : "+r"(a0)
			     : "r"(a1), "r"(a2), "r"(a3), "r"(a7)
			     : "memory");
	return a0;
}

/* Text beyond the line's capacity is dropped; the newline always fits. */
static void put_char(char byte)
{
	if (line_length < LINE_CAPACITY - 1UL)
		line[line_length++] = byte;
}

static void put_text(const char *text)
{
	while (*text != '\0')
		put_char(*text++);
}

/* A utsname field, which the kernel NUL-terminates within UTS_FIELD bytes. */
static void put_field(const char *field)
{
	unsigned long index;

	for (index = 0; index < UTS_FIELD && field[index] != '\0'; ++index)
		put_char(field[index]);
}

static void put_decimal(unsigned long value)
{
	char digits[20];
	unsigned int count = 0;

	do {
		digits[count++] = (char)('0' + value % 10UL);
		value /= 10UL;
	} while (value != 0UL);
	while (count > 0U)
		put_char(digits[--count]);
}

/* End the line and write it whole, in as few write(2) calls as it takes. */
static void end_line(void)
{
	unsigned long done = 0;

	line[line_length++] = '\n';
	while (done < line_length) {
		long count = syscall4(SYS_WRITE, 1L, (long)(line + done),
				      (long)(line_length - done), 0L);

		if (count <= 0)
			break;
		done += (unsigned long)count;
	}
	line_length = 0;
}

static int same_text(const char *left, const char *right)
{
	while (*left != '\0' && *left == *right) {
		++left;
		++right;
	}
	return *left == *right;
}

static int same_field(const char *field, const char *expected)
{
	unsigned long index;

	for (index = 0; index < UTS_FIELD; ++index) {
		if (field[index] != expected[index])
			return 0;
		if (field[index] == '\0')
			return 1;
	}
	return 0;
}

static long monotonic_now(struct kernel_timespec *now)
{
	return syscall4(SYS_CLOCK_GETTIME, CLOCK_MONOTONIC, (long)now, 0L, 0L);
}

/* Milliseconds from start to end, rounded down; 0 if end precedes start. */
static unsigned long elapsed_ms(const struct kernel_timespec *start,
				const struct kernel_timespec *end)
{
	long seconds = end->tv_sec - start->tv_sec;
	long nanoseconds = end->tv_nsec - start->tv_nsec;

	if (nanoseconds < 0) {
		--seconds;
		nanoseconds += NANOSECONDS_PER_SECOND;
	}
	if (seconds < 0 || nanoseconds < 0)
		return 0;
	return (unsigned long)seconds * 1000UL +
	       (unsigned long)nanoseconds / NANOSECONDS_PER_MS;
}

static void finish(int failed) __attribute__((noreturn));
static void finish(int failed)
{
	put_text(failed ? "B6INIT 04 RESULT fail" : "B6INIT 04 RESULT pass");
	end_line();
	put_text("B6INIT 05 POWER_OFF");
	end_line();
	(void)syscall4(SYS_REBOOT, REBOOT_MAGIC1, REBOOT_MAGIC2,
		       REBOOT_CMD_POWER_OFF, 0L);
	for (;;)
		__asm__ __volatile__("" ::: "memory");
}

void init_main(const long *stack)
{
	const char *name = stack[0] > 0 ? (const char *)stack[1] : 0;
	struct kernel_timespec request = { (long)(SLEEP_MS / 1000UL), 0L };
	struct kernel_timespec start = { 0L, 0L };
	struct kernel_timespec end = { 0L, 0L };
	unsigned long elapsed;
	long pid;
	int failed = 0;
	int ok;

	pid = syscall4(SYS_GETPID, 0L, 0L, 0L, 0L);
	put_text("B6INIT 01 START pid=");
	put_decimal(pid > 0 ? (unsigned long)pid : 0UL);
	end_line();
	if (pid != 1L)
		failed = 1;

	if (name != 0 && same_text(name, "/init-exit")) {
		(void)syscall4(SYS_EXIT, 0L, 0L, 0L, 0L);
		finish(1);
	}
	if (name != 0 && same_text(name, "/init-rdcycle")) {
		unsigned long cycles;

		/* rdcycle: B6 makes it a terminal virtual-instruction exit. */
		__asm__ __volatile__("csrr %0, 0xc00" : "=r"(cycles));
		(void)cycles;
		finish(1);
	}

	if (syscall4(SYS_UNAME, (long)&uts, 0L, 0L, 0L) != 0L)
		failed = 1;
	put_text("B6INIT 02 UNAME release=");
	put_field(uts.release);
	put_text(" machine=");
	put_field(uts.machine);
	end_line();
	if (!same_field(uts.release, EXPECTED_RELEASE) ||
	    !same_field(uts.machine, EXPECTED_MACHINE))
		failed = 1;

	if (monotonic_now(&start) != 0L)
		failed = 1;
	if (syscall4(SYS_NANOSLEEP, (long)&request, 0L, 0L, 0L) != 0L)
		failed = 1;
	if (monotonic_now(&end) != 0L)
		failed = 1;
	elapsed = elapsed_ms(&start, &end);
	ok = elapsed >= SLEEP_MS && elapsed <= SLEEP_MS_MAX;
	put_text("B6INIT 03 SLEEP requested_ms=");
	put_decimal(SLEEP_MS);
	put_text(" elapsed_ms=");
	put_decimal(elapsed);
	put_text(ok ? " ok=1" : " ok=0");
	end_line();
	if (!ok)
		failed = 1;

	finish(failed);
}
