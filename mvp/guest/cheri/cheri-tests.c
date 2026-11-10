// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: beryllium-cheri: the CHERI Linux guest's own CHERI faults, which
 *          must occur (planning/cheri-enforcement-plan.md, CE-3; section 6,
 *          C1 and C2), made by te-poc's two roles after line 02 through
 *          guest/mvp-init.c's hook (Q3). The init mounts proc at /proc and
 *          writes 0 to the guest kernel's exception-trace sysctl, which
 *          otherwise prints a report, registers, and a call trace for a
 *          user CHERI fault even when the process handles it (Q2); maps one
 *          anonymous page at PROBE_VA, so that each address below is the
 *          same in every run; forks a child that, with a SA_SIGINFO handler
 *          for SIGSEGV, loads one byte past a capability to the page bounded
 *          to 16 bytes, its handler printing what it was given and exiting;
 *          writes 64 bytes to a pipe from that capability and from one
 *          bounded to 64; and writes 1 back. Each line is one say() of the
 *          init's:
 *            MVPINIT 14 CHERI exception-trace=<v>
 *            MVPINIT 14 CHERI bounds signo=<s> code=<c> base=<b> addr=<a>
 *            MVPINIT 14 CHERI write bound=16 bytes=64 result=<r> errno=<e>
 *            MVPINIT 14 CHERI write bound=64 bytes=64 result=<r> errno=<e>
 *            MVPINIT 14 CHERI exception-trace=<v>
 *          <v> is what the sysctl reads back after the write, <s> and <c>
 *          the handler's si_signo and si_code, <b> the bounded capability's
 *          base and <a> si_addr's address, in hex, and <r> and <e> each
 *          write's result and errno. The tests pass with exception-trace=0;
 *          signo=11 (SIGSEGV), code=12 (SEGV_CAPBOUNDSERR), base=PROBE_VA,
 *          and addr=PROBE_VA + 16, the child then exiting with status 0;
 *          the bounded write's -1 with errno 14 (EFAULT) and the whole
 *          write's 64 with errno 0; and exception-trace=1. A step that
 *          cannot be made prints its own line, which no expectation holds:
 *            MVPINIT 14 CHERI exception-trace error=<errno> step=<step>
 *            MVPINIT 14 CHERI probe error=<errno> addr=<a>
 *            MVPINIT 14 CHERI bounds no-fault
 *            MVPINIT 14 CHERI bounds error=<errno> step=<step>
 *            MVPINIT 14 CHERI write error=<errno>
 *          Then, in te-poc's cap-store image (CE-4; section 6, B3 and B4),
 *          whose G0, the writer, runs as /init-cap-store, a link to /init:
 *          the capability-store module (guest/cheri/be-cheri-store.c)
 *          loaded with the channel page's GPA, before the writer's pattern
 *          write, and its line, which the store's fault leaves unprinted:
 *            MVPINIT 14 CHERI cap-store gpa=<g> result=<r> errno=<e>
 *          <r> is finit_module's result and <e> its errno, 0 and 0 when the
 *          module loaded.
 * Trust:   untrusted guest user space; the capture checker judges the lines
 *          (tests/check-capture.py --monitor cheri).
 * Scope:   the CHERI platform branch's CHERI Linux guest only: linked into
 *          its purecap init by tools/build-guest-cheri.sh, never into the
 *          Linux guests' init.
 */

/* musl's program_invocation_name, the init's argv[0]. */
#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/mount.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>

#include "cheri-tests.h"

/*
 * The probe page's user address: above the init's image and the start of
 * its brk area, which the kernel randomizes within 1 GiB of the image's
 * end, and below the mmap base near the top of Sv39's user half. It is a
 * hint, a null-derived capability, which CHERI Alliance Linux takes where
 * no reservation holds it (mm/mmap.c, check_pcuabi_map_ptr_arg()).
 */
#define PROBE_VA		0x100000000UL
#define PROBE_BYTES		4096UL
#define BOUND_BYTES		16UL
#define WRITE_BYTES		64UL
#define TRACE_PATH		"/proc/sys/debug/exception-trace"
#define TRACE_TEXT		8L
#define STORE_INIT		"/init-cap-store"
#define STORE_MODULE		"/be-cheri-store.ko"
#define STORE_PARAMS		32UL

static mvp_cheri_print *print_line;
/* The bounded capability's base, which the child's handler prints. */
static volatile unsigned long probe_base;

/* A step of the exception-trace test that failed with ERROR: its line. */
static unsigned long trace_failed(int error, const char *step)
{
	print_line("MVPINIT 14 CHERI exception-trace error=%d step=%s", error,
		   step);
	return 1UL;
}

/* proc at /proc, which the initramfs does not hold. */
static unsigned long mount_proc(void)
{
	if (mkdir("/proc", 0555) != 0 && errno != EEXIST)
		return trace_failed(errno, "mkdir");
	if (mount("proc", "/proc", "proc", 0UL, NULL) != 0)
		return trace_failed(errno, "mount");
	return 0UL;
}

/*
 * VALUE, '0' or '1', written to the exception-trace sysctl, and its line
 * with what the sysctl then reads; 0 when that is VALUE.
 */
static unsigned long set_trace(char value)
{
	char text[TRACE_TEXT];
	ssize_t count;
	int error, fd;

	fd = open(TRACE_PATH, O_WRONLY);
	if (fd < 0)
		return trace_failed(errno, "open");
	count = write(fd, &value, 1UL);
	error = errno;
	(void)close(fd);
	if (count != 1)
		return trace_failed(count < 0 ? error : 0, "write");
	fd = open(TRACE_PATH, O_RDONLY);
	if (fd < 0)
		return trace_failed(errno, "reopen");
	count = read(fd, text, (size_t)(TRACE_TEXT - 1L));
	error = errno;
	(void)close(fd);
	if (count <= 0)
		return trace_failed(count < 0 ? error : 0, "read");
	text[count] = '\0';
	text[strcspn(text, "\n")] = '\0';
	print_line("MVPINIT 14 CHERI exception-trace=%s", text);
	return text[0] == value && text[1] == '\0' ? 0UL : 1UL;
}

/*
 * The child's handler: its line, then its exit, 0 for the bounds fault one
 * byte past the probe's 16 bytes.
 */
static void on_bounds(int signo, siginfo_t *info, void *context)
{
	unsigned long addr =
		(unsigned long)__builtin_cheri_address_get(info->si_addr);
	unsigned long base = probe_base;

	(void)signo;
	(void)context;
	print_line("MVPINIT 14 CHERI bounds signo=%d code=%d base=0x%lx "
		   "addr=0x%lx", info->si_signo, info->si_code, base, addr);
	_exit(info->si_signo == SIGSEGV && info->si_code == SEGV_CAPBOUNDSERR &&
	      base == PROBE_VA && addr == PROBE_VA + BOUND_BYTES ? 0 : 1);
}

/* In the child: the handler, then the load one byte past 16 bytes. */
static void bounds_child(char *page) __attribute__((noreturn));
static void bounds_child(char *page)
{
	struct sigaction action;
	char *bounded;

	memset(&action, 0, sizeof(action));
	action.sa_sigaction = on_bounds;
	action.sa_flags = SA_SIGINFO;
	if (sigaction(SIGSEGV, &action, NULL) != 0) {
		print_line("MVPINIT 14 CHERI bounds error=%d step=sigaction",
			   errno);
		_exit(1);
	}
	bounded = __builtin_cheri_bounds_set(page, BOUND_BYTES);
	probe_base = (unsigned long)__builtin_cheri_base_get(bounded);
	(void)*(volatile char *)(bounded + BOUND_BYTES);
	print_line("MVPINIT 14 CHERI bounds no-fault");
	_exit(1);
}

/* The bounds test: the child, and its exit; 0 when it exited with 0. */
static unsigned long bounds(char *page)
{
	pid_t child;
	int status = 0;

	child = fork();
	if (child == 0)
		bounds_child(page);
	if (child < 0) {
		print_line("MVPINIT 14 CHERI bounds error=%d step=fork", errno);
		return 1UL;
	}
	return waitpid(child, &status, 0) == child && WIFEXITED(status) &&
	       WEXITSTATUS(status) == 0 ? 0UL : 1UL;
}

/*
 * 64 bytes to the pipe FD from the probe through a capability bounded to
 * BOUND bytes, and its line; 0 for EFAULT from 16 bytes and all 64 from 64.
 */
static unsigned long write_from(int fd, char *page, unsigned long bound)
{
	ssize_t result;
	int error;

	errno = 0;
	result = write(fd, __builtin_cheri_bounds_set(page, bound), WRITE_BYTES);
	error = errno;
	print_line("MVPINIT 14 CHERI write bound=%lu bytes=%lu result=%ld "
		   "errno=%d", bound, WRITE_BYTES, (long)result, error);
	if (bound < WRITE_BYTES)
		return result == -1 && error == EFAULT ? 0UL : 1UL;
	return result == (ssize_t)WRITE_BYTES && error == 0 ? 0UL : 1UL;
}

unsigned long mvp_cheri_tests(mvp_cheri_print *print)
{
	unsigned long failures;
	char *page;
	int fds[2];

	print_line = print;
	failures = mount_proc();
	failures += set_trace('0');
	page = mmap((void *)(uintptr_t)PROBE_VA, PROBE_BYTES,
		    PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
	if (page == MAP_FAILED ||
	    (unsigned long)__builtin_cheri_address_get(page) != PROBE_VA) {
		print_line("MVPINIT 14 CHERI probe error=%d addr=0x%lx",
			   page == MAP_FAILED ? errno : 0, page == MAP_FAILED ?
			   0UL : (unsigned long)__builtin_cheri_address_get(page));
		if (page != MAP_FAILED)
			(void)munmap(page, PROBE_BYTES);
		return failures + 1UL + set_trace('1');
	}
	failures += bounds(page);
	if (pipe(fds) != 0) {
		print_line("MVPINIT 14 CHERI write error=%d", errno);
		++failures;
	} else {
		failures += write_from(fds[1], page, BOUND_BYTES);
		failures += write_from(fds[1], page, WRITE_BYTES);
		(void)close(fds[0]);
		(void)close(fds[1]);
	}
	(void)munmap(page, PROBE_BYTES);
	return failures + set_trace('1');
}

unsigned long mvp_cheri_store(mvp_cheri_print *print, unsigned long gpa)
{
	char params[STORE_PARAMS];
	long result = -1L;
	int error, fd;

	if (program_invocation_name == NULL ||
	    strcmp(program_invocation_name, STORE_INIT) != 0)
		return 0UL;
	(void)snprintf(params, sizeof(params), "gpa=%#lx", gpa);
	fd = open(STORE_MODULE, O_RDONLY);
	if (fd >= 0) {
		errno = 0;
		result = (long)syscall(SYS_finit_module, fd, params, 0);
	}
	error = errno;
	if (fd >= 0)
		(void)close(fd);
	print("MVPINIT 14 CHERI cap-store gpa=%#lx result=%ld errno=%d", gpa,
	      result, error);
	return result == 0L && error == 0 ? 0UL : 1UL;
}
