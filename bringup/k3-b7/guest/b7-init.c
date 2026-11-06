// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the K3 B7 guests' init (planning/k3-b7-plan.md, Guest software
 *          and Markers, Q6): one static nolibc program that G0 and G1 both
 *          run as /init. It takes its guest ID from argv ("-- be.guest=<g>"
 *          in bootargs; guest/b7-guest-id.h) and prints these lines on
 *          /dev/console, each with one write(2) where the console takes it
 *          whole:
 *            B7INIT 01 START guest=<g> pid=<pid>
 *            B7INIT 02 UNAME release=<release> machine=<machine>
 *            B7INIT 03 STEP n=<i>/8 rounds=<r> t_ms=<t>   (i = 1 to 8)
 *            B7INIT 04 SLEEP requested_ms=1000 elapsed_ms=<e> ok=<0|1>
 *            B7INIT 05 RESULT <pass|fail>
 *            B7INIT 06 POWER_OFF
 *          <g> is 0 or 1, or "none" for a missing or malformed ID. Each step
 *          computes rounds of xorshift until at least 25 ms of
 *          CLOCK_MONOTONIC time have passed (or a round cap ends it), prints
 *          its line, and sleeps 50 ms. <r> counts the step's rounds, and
 *          <t> is a timestamp, not a duration: the CLOCK_MONOTONIC
 *          milliseconds when the step's compute ended. So <t> rises by at
 *          least 75 ms from one step to the next. The result is pass only
 *          if the guest ID is valid, init runs as pid 1 on a 7.2.0 riscv64
 *          kernel, every step computed for 25 ms, every clock read and sleep
 *          succeeded, and the 1 s sleep took 1000-1999 ms. Then
 *          reboot(LINUX_REBOOT_CMD_POWER_OFF), which Linux turns into an SBI
 *          SRST shutdown.
 *          B6's two QEMU-only variants keep their roles. DTBs whose bootargs
 *          name them with rdinit= (before "--") select them, and they
 *          dispatch on argv[0] after line 01: /init-exit exits, so that
 *          Linux panics ("Attempted to kill init"), and /init-rdcycle reads
 *          the cycle counter in U-mode, which B7 does not open to the guest
 *          (hcounteren.CY = 0).
 * Trust:   untrusted guest user space. The B7 monitor buffers and tags each
 *          guest's lines, and the run tools judge them.
 * Scope:   B7 only. Built by GCC alone against the pinned tree's
 *          tools/include/nolibc and UAPI headers (scripts/build-guest.sh),
 *          and embedded in the guest kernel's initramfs
 *          (guest/initramfs.list.in).
 */

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/reboot.h>
#include <sys/utsname.h>
#include <linux/reboot.h>

#include "b7-guest-id.h"

/* The pinned guest kernel (Linux v7.2), and the plan's steps and sleep. */
#define EXPECTED_RELEASE	"7.2.0"
#define EXPECTED_MACHINE	"riscv64"
#define STEPS			8UL
#define STEP_COMPUTE_NS		25000000UL
#define STEP_SLEEP_MS		50UL
#define SLEEP_MS		1000UL
#define SLEEP_MS_MAX		1999UL
/*
 * One round is ROUND_SHIFTS xorshift64 steps. The cap ends a step whose
 * clock does not advance; planning research measured about 8,300 rounds
 * per 50 ms of guest time under QEMU.
 */
#define ROUND_SHIFTS		4096UL
#define ROUND_CAP		65536UL
#define NS_PER_MS		1000000UL
#define NS_PER_S		1000000000UL
#define LINE_CAPACITY		128UL

static char line[LINE_CAPACITY];
static struct utsname uts;
static unsigned long xorshift_state = 0x9e3779b97f4a7c15UL;
static int failed;

/*
 * Format one line, end it, and write it whole, in as few write(2) calls as
 * it takes. Text beyond the line's capacity is dropped; the newline always
 * fits.
 */
static void say(const char *format, ...) __attribute__((format(printf, 1, 2)));
static void say(const char *format, ...)
{
	unsigned long length = 0;
	unsigned long done = 0;
	va_list args;
	int count;

	va_start(args, format);
	count = vsnprintf(line, LINE_CAPACITY - 1UL, format, args);
	va_end(args);
	if (count > 0)
		length = (unsigned long)count;
	if (length > LINE_CAPACITY - 2UL)
		length = LINE_CAPACITY - 2UL;
	line[length++] = '\n';
	while (done < length) {
		ssize_t written = write(STDOUT_FILENO, line + done, length - done);

		if (written <= 0)
			break;
		done += (unsigned long)written;
	}
}

/* CLOCK_MONOTONIC in nanoseconds; a failed read fails the run and gives 0. */
static unsigned long monotonic_ns(void)
{
	struct timespec now;

	if (clock_gettime(CLOCK_MONOTONIC, &now) != 0 || now.tv_sec < 0 ||
	    now.tv_nsec < 0 || now.tv_nsec >= (long)NS_PER_S) {
		failed = 1;
		return 0;
	}
	return (unsigned long)now.tv_sec * NS_PER_S +
	       (unsigned long)now.tv_nsec;
}

/* Sleep for ms milliseconds of CLOCK_MONOTONIC time. */
static void sleep_ms(unsigned long ms)
{
	struct timespec request;

	request.tv_sec = (time_t)(ms / 1000UL);
	request.tv_nsec = (long)(ms % 1000UL * NS_PER_MS);
	if (clock_nanosleep(CLOCK_MONOTONIC, 0, &request, NULL) != 0)
		failed = 1;
}

/* One round of xorshift64, which the compiler must not drop. */
static void compute_round(void)
{
	unsigned long x = xorshift_state;
	unsigned long shift;

	for (shift = 0; shift < ROUND_SHIFTS; ++shift) {
		x ^= x << 13;
		x ^= x >> 7;
		x ^= x << 17;
	}
	__asm__ __volatile__("" : "+r"(x));
	xorshift_state = x;
}

/*
 * Step n: compute for at least STEP_COMPUTE_NS (ROUND_CAP rounds at most;
 * a step that ends short fails the run), print line 03, and sleep.
 */
static void run_step(unsigned long n)
{
	unsigned long start = monotonic_ns();
	unsigned long rounds = 0;
	unsigned long now;

	do {
		compute_round();
		++rounds;
		now = monotonic_ns();
	} while (now >= start && now - start < STEP_COMPUTE_NS &&
		 rounds < ROUND_CAP);
	if (now < start || now - start < STEP_COMPUTE_NS)
		failed = 1;
	say("B7INIT 03 STEP n=%lu/%lu rounds=%lu t_ms=%lu", n, STEPS, rounds,
	    now / NS_PER_MS);
	sleep_ms(STEP_SLEEP_MS);
}

static void finish(void) __attribute__((noreturn));
static void finish(void)
{
	say("B7INIT 05 RESULT %s", failed ? "fail" : "pass");
	say("B7INIT 06 POWER_OFF");
	(void)reboot(LINUX_REBOOT_CMD_POWER_OFF);
	for (;;)
		__asm__ __volatile__("" ::: "memory");
}

int main(int argc, char **argv)
{
	const char *name = argc > 0 ? argv[0] : NULL;
	int guest = b7_guest_id(argc, argv);
	pid_t pid = getpid();
	unsigned long start, end, elapsed, n;
	int ok;

	if (guest == B7_GUEST_ID_NONE) {
		failed = 1;
		say("B7INIT 01 START guest=none pid=%d", pid);
	} else {
		say("B7INIT 01 START guest=%d pid=%d", guest, pid);
	}
	if (pid != 1)
		failed = 1;

	if (name != NULL && strcmp(name, "/init-exit") == 0)
		exit(0);
	if (name != NULL && strcmp(name, "/init-rdcycle") == 0) {
		unsigned long cycles;

		/* rdcycle: B7 makes it a terminal virtual-instruction exit. */
		__asm__ __volatile__("csrr %0, 0xc00" : "=r"(cycles));
		(void)cycles;
		failed = 1;
		finish();
	}

	if (uname(&uts) != 0)
		failed = 1;
	say("B7INIT 02 UNAME release=%s machine=%s", uts.release, uts.machine);
	if (strcmp(uts.release, EXPECTED_RELEASE) != 0 ||
	    strcmp(uts.machine, EXPECTED_MACHINE) != 0)
		failed = 1;

	for (n = 1; n <= STEPS; ++n)
		run_step(n);

	start = monotonic_ns();
	sleep_ms(SLEEP_MS);
	end = monotonic_ns();
	elapsed = end >= start ? (end - start) / NS_PER_MS : 0UL;
	ok = elapsed >= SLEEP_MS && elapsed <= SLEEP_MS_MAX;
	say("B7INIT 04 SLEEP requested_ms=%lu elapsed_ms=%lu ok=%d", SLEEP_MS,
	    elapsed, ok);
	if (!ok)
		failed = 1;

	finish();
}
