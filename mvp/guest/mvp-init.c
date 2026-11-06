// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP guests' init (planning/mvp-m0-plan.md, Guest software
 *          and Markers, Q3; B7's init with the MVPINIT tag): one static
 *          nolibc program that G0 and G1 both run as /init, each on its own
 *          domain hart. It takes its guest ID from argv ("-- be.guest=<g>"
 *          in bootargs; guest/mvp-guest-id.h) and prints these lines on
 *          /dev/console, each with one write(2) where the console takes it
 *          whole:
 *            MVPINIT 01 START guest=<g> pid=<pid>
 *            MVPINIT 02 UNAME release=<release> machine=<machine>
 *            MVPINIT 03 STEP n=<i>/8 rounds=<r> t_ms=<t>   (i = 1 to 8)
 *            MVPINIT 04 SLEEP requested_ms=1000 elapsed_ms=<e> ok=<0|1>
 *            MVPINIT 05 RESULT <pass|fail>
 *            MVPINIT 06 POWER_OFF
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
 *          the cycle counter in U-mode, which the MVP does not open to the
 *          guest (hcounteren.CY = 0).
 *          M1's roles (planning/mvp-m1-plan.md, Guest software and
 *          Markers): with be.role=, be.channel=, and be.deny= after "--"
 *          (guest/mvp-guest-id.h), the init runs its role's steps after
 *          line 02 and before the first STEP; without them it runs exactly
 *          the lines above. Through /dev/mem (O_RDWR | O_SYNC, MAP_SHARED),
 *          the writer maps the channel page read-write, writes 4,088 bytes
 *          of xorshift64 from CHANNEL_SEED at offsets 0x8-0xfff, executes
 *          fence w, w, writes CHANNEL_FLAG at offset 0, and reads the
 *          pattern back; the reader maps the page read-write too, so that
 *          its store reaches the G-stage, polls the flag for at most 10 s
 *          of CLOCK_MONOTONIC, 1 ms apart, executes fence r, r, and reads
 *          the pattern. Each prints its 64-bit FNV-1a digest:
 *            MVPINIT 07 CHANNEL role=writer gpa=<c> bytes=4088 digest=<x> flag=<f>
 *            MVPINIT 07 CHANNEL role=reader gpa=<c> bytes=4088 digest=<x> polls=<n> match=<0|1>
 *          match=1 when the digest is the seed's pattern's, which the init
 *          computes. Then the init forks once (Plan revision M1-A.1, which
 *          revises the plan's Guest software text, M1-A.2): Linux v7.2
 *          reports a handled fault of pid 1 as an unhandled signal
 *          (kernel/signal.c:536-538), so a child installs a SIGSEGV
 *          handler with a raw rt_sigaction (nolibc has no sigaction) and
 *          makes each denied access, in be.deny's order: a load maps its
 *          page read-only and loads one doubleword; a store, in the
 *          channel page, stores zero through the inherited read-write
 *          mapping and reads the word back. Each access is one 4-byte
 *          instruction at a global label; the handler records si_signo,
 *          si_code, si_addr, and the ucontext's pc, and moves pc past that
 *          instruction alone (any other fault restores SIGSEGV's default,
 *          so the fault again ends the child). The child prints each line
 *          08 and exits with its failure count:
 *            MVPINIT 08 DENIED n=<i> kind=<load|store> gpa=<g> va=<v> pc=<p> signo=<s> code=<c> observed=<0|1>[ unchanged=<0|1>]
 *          observed=1 when the handler ran once, with SIGSEGV, SEGV_ACCERR,
 *          and si_addr and pc both the label; unchanged=1, for a store,
 *          when the word still holds the writer's. No mapping is executable,
 *          and nothing is fetched from one ("No fetch"). RESULT pass also
 *          needs valid role arguments, the writer's digest and flag, the
 *          reader's flag within 10 s and match=1, every denial observed
 *          (and unchanged), and the child's exit with status 0: a fork
 *          failure or an abnormal exit fails the run.
 *          M2's roles (planning/mvp-m2-plan.md, Guest software, Q2, Q8, and
 *          Q9): with be.role=host or prot, be.pages=, and be.deny= after
 *          "--", the init loads /be-mgmt.ko with finit_module and opens
 *          /dev/be-mgmt (guest/mgmt/be-mgmt.c), maps through /dev/mem the
 *          request and response pages read-write and, for prot, the secret
 *          page read-only, and forks the child for be.deny as M1's roles
 *          do; in these roles a store's word is unchanged=1 when it holds
 *          after the store what it held before. A failure prints its own
 *          line 07, MODULE, DEVICE, or PAGES with error=<errno>; then:
 *            MVPINIT 07 PAGES role=<host|prot> count=<2|3>
 *          The host follows host_script: requests 1 to 4, each the 64-byte
 *          message "BE-MVP-M2-REQ-<n>", zero-padded, at the request page's
 *          offset 64, a fence, and n at its offset 0, then polls 1 ms
 *          apart, for at most one second of CLOCK_MONOTONIC time, of the
 *          response page's offset 0 for n and the 32-byte digest at its
 *          offset 64; then its management calls,
 *          each one ioctl on the device: pause 0, terminate 0, pause 2,
 *          FID 7 on 1, and a burst of eight terminate 0, on one line, its
 *          results as <r>x8 when all eight are equal and listed otherwise;
 *          then pause 1, request 5, which must go unanswered, and
 *          terminate 1. A call whose ioctl fails prints error=<errno>:
 *            MVPINIT 09 REQUEST n=<n> digest=<64 hex>
 *            MVPINIT 09 REQUEST n=<n> timeout=1
 *            MVPINIT 10 MGMT fid=<pause|terminate|f> target=<t> result=<r>
 *            MVPINIT 10 MGMT burst=8 fid=terminate target=0 results=<r>x8
 *          then M0's steps. RESULT pass also needs the module, the device,
 *          both pages, every denial observed and unchanged with the
 *          child's exit status 0, and each request and call as
 *          host_script expects it. prot makes its two calls (prot_script),
 *          reads the 32-byte secret, which it never prints, and serves
 *          for ever: for each request whose sequence number is above the
 *          last it served, HMAC-SHA-256 keyed by the secret over n's eight
 *          little-endian bytes and the 64-byte message (src/mvp-sha256.c),
 *          the digest at the response page's offset 64, a fence, and n at
 *          its offset 0:
 *            MVPINIT 09 RESPONSE n=<n> digest=<64 hex>
 *          It prints no RESULT and never powers off: the monitor pauses and
 *          terminates it.
 *          M7's shell (planning/mvp-m7-plan.md, D-9, Q4): /init-shell, a
 *          further rdinit= variant, prints lines 01 and 02 as M0's init
 *          does and checks the role arguments as the roles do, but runs no
 *          role and no step. It puts its be.* arguments, in order and
 *          separated by single spaces, in BE_ARGS, the one source of the
 *          verbs' addresses, prints line 11, and forks once: the child
 *          starts a session, opens /dev/hvc0 (the console's tty) as its
 *          controlling terminal and its three standard descriptors, and
 *          executes /bin/sh, BusyBox's ash, with HOME=/, PATH=/bin,
 *          PS1="# ", and BE_ARGS. The init reaps every child until the
 *          shell exits and prints line 11 again; RESULT pass needs a valid
 *          guest ID, pid 1, the pinned kernel, role arguments absent or
 *          valid, and the shell's exit with status 0 (`exit 0` ends a
 *          session whose last command failed); then it powers off:
 *            MVPINIT 11 SHELL tty=/dev/hvc0 role=<role|none|malformed>
 *            MVPINIT 11 SHELL exit=<status>
 *            MVPINIT 11 SHELL signal=<signal>
 *            MVPINIT 11 SHELL error=<errno> step=<step>
 *          The helper verbs are this program run from the shell with
 *          argv[0] be-chan, be-deny, or be-anchor (a link in /bin); they
 *          print no line 01, take the role from BE_ARGS by the roles'
 *          rules (guest/mvp-guest-id.h), print their lines, and exit 0,
 *          1 when the action fails, or 2, with a usage line on stderr, for
 *          an argument the verb or the domain's role does not admit:
 *            be-chan write TEXT...   M1's writer: 1 to 64 printable bytes,
 *                                    the words joined by single spaces,
 *                                    into the channel page through
 *                                    /dev/mem: the flag word cleared,
 *                                    fence w, w, the length at offset 8
 *                                    and the text at offset 16, fence w,
 *                                    w, and the flag (ASCII BEM7TEXT) at 0
 *            be-chan read            M1's writer or reader: the flag, fence
 *                                    r, r, and the text
 *              MVPINIT 12 CHAN write gpa=<c> bytes=<n> text=<text>
 *              MVPINIT 12 CHAN read gpa=<c> bytes=<n> text=<text>
 *              MVPINIT 12 CHAN read gpa=<c> empty=1
 *              MVPINIT 12 CHAN <write|read> gpa=<c> error=<errno>
 *            be-deny load-unmapped   be.deny's first load, or
 *            be-deny store-shared    its first store, made in a forked
 *                                    child by the roles' handler, as its
 *                                    line 08 with be.deny's n; a store's
 *                                    word unchanged=1 when it holds what
 *                                    it held before
 *            be-anchor request N     the host's request N (1 to 999999999)
 *                                    through the request and response
 *                                    pages, as M2's host makes it: line 09
 *            be-anchor pause         the host's call of pause or terminate
 *            be-anchor terminate     on the other domain (M7-4), through
 *                                    the module, loaded once, and its
 *                                    device, as M2's host makes it: line
 *                                    10, and the status 0 for success
 *          No verb uses BusyBox's devmem, whose fault no handler takes.
 *          M7-4's hostile guest (planning/mvp-m7-plan.md, D-4): /init-
 *          hostile, a QEMU-only rdinit= variant, prints line 01, then what
 *          a hostile guest could print, each line with one write(2): every
 *          byte value in eight lines of 32 after a printable head, a
 *          look-alike of hart 0's BE_MVP:13 line, a line that begins with
 *          the other domain's prefix, a terminal query and a window-title
 *          sequence, and a line of 300 bytes; then RESULT and the power-off:
 *            MVPINIT 13 HOSTILE bytes=<k> <the values 32k to 32k + 31, raw>
 *            BE_MVP:13 RUN_COMPLETE forged
 *            BE_MVP_G1: forged
 *            MVPINIT 13 HOSTILE query=<ESC>[6n title=<ESC>]0;forged<BEL>
 *            MVPINIT 13 HOSTILE long=300 xxx...x
 * Trust:   untrusted guest user space. The MVP monitor buffers and tags each
 *          guest's lines, and the run tools judge them.
 * Scope:   the MVP line. Built by GCC alone against the pinned tree's
 *          tools/include/nolibc and UAPI headers, with src/mvp-sha256.c and
 *          guest/be/types.h (tools/build-guest.sh), and embedded in the
 *          guest kernel's initramfs (guest/initramfs.list.in).
 */

#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/reboot.h>
#include <sys/syscall.h>
#include <sys/utsname.h>
#include <sys/wait.h>
#include <asm/ioctls.h>
#include <asm/sigcontext.h>
#include <asm/ucontext.h>
#include <linux/ioctl.h>
#include <linux/reboot.h>
#include <linux/types.h>

#include "mvp-guest-id.h"
#include "mvp-sha256.h"

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
/*
 * The channel protocol (planning/mvp-m1-plan.md, Guest software): the flag
 * (ASCII BEM1CHAN) in the page's first doubleword, the pattern in the other
 * 511 from the seed (ASCII BEM1SEED), and the reader's poll.
 */
#define CHANNEL_FLAG		0x42454d314348414eUL
#define CHANNEL_SEED		0x42454d3153454544UL
#define CHANNEL_WORDS		(MVP_PAGE_BYTES / sizeof(unsigned long))
#define PATTERN_BYTES		(MVP_PAGE_BYTES - sizeof(unsigned long))
#define POLL_NS_MAX		(10UL * NS_PER_S)
#define POLL_MS			1UL
#define FNV_OFFSET_BASIS	0xcbf29ce484222325UL
#define FNV_PRIME		0x100000001b3UL
/* rt_sigaction's sigsetsize: RISC-V's one-word sigset_t. */
#define SIGSET_BYTES		8UL
/*
 * The anchor protocol (planning/mvp-m2-plan.md, Q8): a 64-bit sequence
 * number in each page's first doubleword, the request's 64-byte message and
 * the response's 32-byte digest at offset 64, and the host's poll.
 */
#define SEQUENCE_WORD		0UL
#define BODY_WORD		(64UL / sizeof(unsigned long))
#define MESSAGE_BYTES		64UL
#define MESSAGE_WORDS		(MESSAGE_BYTES / sizeof(unsigned long))
#define MESSAGE_PREFIX		"BE-MVP-M2-REQ-"
#define DIGEST_WORDS		(BE_MVP_SHA256_BYTES / sizeof(unsigned long))
/*
 * The host's poll bound: Q8 says 2,000 polls 1 ms apart, meaning about
 * two seconds; the pinned kernel (CONFIG_HZ=250, no high-resolution
 * timers) rounds a 1 ms sleep up to a jiffy, so the bound is kept as a
 * deadline of CLOCK_MONOTONIC time between polls 1 ms apart, one second,
 * which keeps the run inside the budget the plan's negative variant
 * separates from a hang (2^27 ticks).
 */
#define REQUEST_DEADLINE_NS	(1UL * NS_PER_S)
#define SECRET_BYTES		32UL
#define SECRET_WORDS		(SECRET_BYTES / sizeof(unsigned long))
#define HOST_PAGES		2UL
/*
 * The management module's ABI (guest/mgmt/be-mgmt.c, which is GPL-2.0-only
 * and so defines it for itself: planning/mvp-m2-plan.md, Q2, Q3, and Q20):
 * one ioctl per call of the extension, the FID and the target in, the SBI
 * error code out; both pin the ioctl number.
 */
#define MGMT_MODULE		"/be-mgmt.ko"
#define MGMT_DEVICE		"/dev/be-mgmt"
#define MGMT_FID_PAUSE		0UL
#define MGMT_FID_TERMINATE	1UL
#define MGMT_BURST_MAX		8UL
#define SBI_SUCCESS		0L
#define SBI_ERR_NOT_SUPPORTED	(-2L)
#define SBI_ERR_INVALID_PARAM	(-3L)
#define SBI_ERR_DENIED		(-4L)

struct be_mgmt_call {
	__u64 fid;
	__u64 target;
	__s64 result;
};

#define BE_MGMT_IOC_CALL	_IOWR('B', 0x42, struct be_mgmt_call)

_Static_assert(sizeof(sigset_t) == SIGSET_BYTES, "sigset_t is one word");
_Static_assert(BE_MGMT_IOC_CALL == 0xc0184242UL,
	       "the management ioctl is be-mgmt.ko's");

/*
 * M7's shell and helper verbs (planning/mvp-m7-plan.md, D-9): the tty, the
 * shell, BE_ARGS's capacity and words, the channel text protocol (the flag,
 * ASCII BEM7TEXT, in word 0, the length in word 1, the text from word 2),
 * the highest request a verb makes, and the verbs' exit statuses.
 */
#define SHELL_TTY		"/dev/hvc0"
#define SHELL_PATH		"/bin/sh"
#define SHELL_FAILED		127
#define ARGS_KEY		"BE_ARGS="
#define ARGS_CAPACITY		512UL
#define ARGS_WORDS		16UL
#define TEXT_FLAG		0x42454d3754455854UL
#define TEXT_FLAG_WORD		0UL
#define TEXT_LENGTH_WORD	1UL
#define TEXT_WORD		2UL
#define TEXT_MAX		64UL
#define TEXT_WORDS		(TEXT_MAX / sizeof(unsigned long))
#define REQUEST_MAX		999999999UL
#define VERB_FAILED		1
#define VERB_USAGE		2
/*
 * /init-hostile's output (M7-4; planning/mvp-m7-plan.md, D-4): every byte
 * value in eight lines of 32, and a line of 300 bytes, beyond the
 * monitor's 256-byte line buffer.
 */
#define HOSTILE_BLOCKS		8UL
#define HOSTILE_BLOCK_BYTES	32UL
#define HOSTILE_LONG_BYTES	300UL

_Static_assert(TEXT_WORD + TEXT_WORDS <= CHANNEL_WORDS,
	       "the channel text fits the page");

/*
 * One step of a role's script (planning/mvp-m2-plan.md, Q9): a request, or
 * a management call made count times; expected is the call's SBI result,
 * or whether the request is answered.
 */
struct mvp_step {
	unsigned long fid;
	unsigned long target;
	unsigned long count;
	long expected;
};

#define STEP_REQUEST		(~0UL)
#define ANSWERED		1L
#define UNANSWERED		0L

/*
 * The host's: the four requests, the calls it is not granted (on itself,
 * on no domain, an unknown FID, and the burst), pause, the fifth request,
 * which the paused domain cannot answer, and terminate.
 */
static const struct mvp_step host_script[] = {
	{ STEP_REQUEST, 1UL, 1UL, ANSWERED },
	{ STEP_REQUEST, 2UL, 1UL, ANSWERED },
	{ STEP_REQUEST, 3UL, 1UL, ANSWERED },
	{ STEP_REQUEST, 4UL, 1UL, ANSWERED },
	{ MGMT_FID_PAUSE, 0UL, 1UL, SBI_ERR_DENIED },
	{ MGMT_FID_TERMINATE, 0UL, 1UL, SBI_ERR_DENIED },
	{ MGMT_FID_PAUSE, 2UL, 1UL, SBI_ERR_INVALID_PARAM },
	{ 7UL, 1UL, 1UL, SBI_ERR_NOT_SUPPORTED },
	{ MGMT_FID_TERMINATE, 0UL, MGMT_BURST_MAX, SBI_ERR_DENIED },
	{ MGMT_FID_PAUSE, 1UL, 1UL, SBI_SUCCESS },
	{ STEP_REQUEST, 5UL, 1UL, UNANSWERED },
	{ MGMT_FID_TERMINATE, 1UL, 1UL, SBI_SUCCESS },
};

/* The protected domain's: the two calls it is not granted. */
static const struct mvp_step prot_script[] = {
	{ MGMT_FID_TERMINATE, 0UL, 1UL, SBI_ERR_DENIED },
	{ MGMT_FID_PAUSE, 0UL, 1UL, SBI_ERR_DENIED },
};

/* A request's message, a digest, the secret, and the HMAC's input. */
union mvp_message {
	unsigned long word[MESSAGE_WORDS];
	unsigned char byte[MESSAGE_BYTES];
};

union mvp_digest {
	unsigned long word[DIGEST_WORDS];
	unsigned char byte[BE_MVP_SHA256_BYTES];
};

union mvp_secret {
	unsigned long word[SECRET_WORDS];
	unsigned char byte[SECRET_BYTES];
};

union mvp_hmac_input {
	unsigned long word[1UL + MESSAGE_WORDS];
	unsigned char byte[sizeof(unsigned long) + MESSAGE_BYTES];
};

static char line[LINE_CAPACITY];
static struct utsname uts;
static unsigned long xorshift_state = 0x9e3779b97f4a7c15UL;
static int failed;
/* say()'s descriptor: standard output, but for a verb's usage line. */
static int say_fd = STDOUT_FILENO;
/* The shell's BE_ARGS= entry (M7). */
static char args_env[sizeof(ARGS_KEY) - 1UL + ARGS_CAPACITY];
/* The role's pattern (word 0 unused), its digest, and the mappings. */
static unsigned long pattern[CHANNEL_WORDS];
static unsigned long pattern_digest;
static int mem_fd = -1;
static volatile unsigned long *channel_page;
/* M2's pages (request, response, secret) and the management device. */
static volatile unsigned long *anchor_page[MVP_PAGES];
static int mgmt_fd = -1;
/* One denied access's signal, as the handler saw it. */
static volatile unsigned long armed_pc;
static volatile unsigned long seen_count;
static volatile int seen_signo;
static volatile int seen_code;
static volatile unsigned long seen_addr;
static volatile unsigned long seen_pc;

/*
 * The denied accesses: each one 4-byte instruction at a global label,
 * assembled without the compressed extension, so that the handler's pc + 4
 * is exact and its pc compares with the label. A faulting load leaves t1,
 * and so the result, the fallback. The transformed encodings (htinst) of
 * ld t1, 0(a0) and sd zero, 0(a0) are 0x3303 and 0x3023.
 */
extern const char mvp_load_insn[];
extern const char mvp_store_insn[];
unsigned long mvp_load(const volatile unsigned long *address,
		       unsigned long fallback);
void mvp_store_zero(volatile unsigned long *address);
__asm__("	.pushsection .text.mvp_denied, \"ax\", @progbits\n"
	"	.option push\n"
	"	.option norvc\n"
	"	.balign 4\n"
	"	.globl mvp_load, mvp_load_insn\n"
	"	.type mvp_load, @function\n"
	"mvp_load:\n"
	"	mv t1, a1\n"
	"mvp_load_insn:\n"
	"	ld t1, 0(a0)\n"
	"	mv a0, t1\n"
	"	ret\n"
	"	.size mvp_load, . - mvp_load\n"
	"	.globl mvp_store_zero, mvp_store_insn\n"
	"	.type mvp_store_zero, @function\n"
	"mvp_store_zero:\n"
	"mvp_store_insn:\n"
	"	sd zero, 0(a0)\n"
	"	ret\n"
	"	.size mvp_store_zero, . - mvp_store_zero\n"
	"	.option pop\n"
	"	.popsection\n");

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
		ssize_t written = write(say_fd, line + done, length - done);

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
	say("MVPINIT 03 STEP n=%lu/%lu rounds=%lu t_ms=%lu", n, STEPS, rounds,
	    now / NS_PER_MS);
	sleep_ms(STEP_SLEEP_MS);
}

/* The seed's pattern: words 1 to 511, each one xorshift64 step on the last. */
static void make_pattern(void)
{
	unsigned long word = CHANNEL_SEED;
	unsigned long index;

	for (index = 1; index < CHANNEL_WORDS; ++index) {
		word ^= word << 13;
		word ^= word >> 7;
		word ^= word << 17;
		pattern[index] = word;
	}
}

/* 64-bit FNV-1a over a page's pattern bytes (words 1 to 511), in order. */
static unsigned long digest_of(const volatile unsigned long *page)
{
	unsigned long hash = FNV_OFFSET_BASIS;
	unsigned long index, shift;

	for (index = 1; index < CHANNEL_WORDS; ++index) {
		unsigned long word = page[index];

		for (shift = 0; shift < 64UL; shift += 8UL) {
			hash ^= (word >> shift) & 0xffUL;
			hash *= FNV_PRIME;
		}
	}
	return hash;
}

/* The page that holds GPA, through /dev/mem, or NULL. */
static volatile unsigned long *map_page(unsigned long gpa, int protection)
{
	void *page;

	if (mem_fd < 0)
		mem_fd = open("/dev/mem", O_RDWR | O_SYNC);
	if (mem_fd < 0)
		return NULL;
	page = mmap(NULL, MVP_PAGE_BYTES, protection, MAP_SHARED, mem_fd,
		    (off_t)(gpa & ~(MVP_PAGE_BYTES - 1UL)));
	return page == MAP_FAILED ? NULL : (volatile unsigned long *)page;
}

/* The writer: the pattern, fence w, w, the flag, the readback; line 07. */
static void write_channel(unsigned long gpa)
{
	volatile unsigned long *page = map_page(gpa, PROT_READ | PROT_WRITE);
	unsigned long index, flag, digest;

	if (page == NULL) {
		failed = 1;
		say("MVPINIT 07 CHANNEL role=writer gpa=0x%lx error=%d", gpa,
		    errno);
		return;
	}
	channel_page = page;
	for (index = 1; index < CHANNEL_WORDS; ++index)
		page[index] = pattern[index];
	__asm__ __volatile__("fence w, w" ::: "memory");
	page[0] = CHANNEL_FLAG;
	flag = page[0];
	digest = digest_of(page);
	say("MVPINIT 07 CHANNEL role=writer gpa=0x%lx bytes=%lu "
	    "digest=0x%016lx flag=0x%lx", gpa, PATTERN_BYTES, digest, flag);
	if (digest != pattern_digest || flag != CHANNEL_FLAG)
		failed = 1;
}

/* The reader: the flag within 10 s, fence r, r, the pattern; line 07. */
static void read_channel(unsigned long gpa)
{
	volatile unsigned long *page = map_page(gpa, PROT_READ | PROT_WRITE);
	unsigned long start, now, digest, polls = 0;
	int flagged = 0, match;

	if (page == NULL) {
		failed = 1;
		say("MVPINIT 07 CHANNEL role=reader gpa=0x%lx error=%d", gpa,
		    errno);
		return;
	}
	channel_page = page;
	start = monotonic_ns();
	for (;;) {
		++polls;
		if (page[0] == CHANNEL_FLAG) {
			flagged = 1;
			break;
		}
		now = monotonic_ns();
		if (now < start || now - start >= POLL_NS_MAX)
			break;
		sleep_ms(POLL_MS);
	}
	__asm__ __volatile__("fence r, r" ::: "memory");
	digest = digest_of(page);
	match = digest == pattern_digest;
	say("MVPINIT 07 CHANNEL role=reader gpa=0x%lx bytes=%lu "
	    "digest=0x%016lx polls=%lu match=%d", gpa, PATTERN_BYTES, digest,
	    polls, match);
	if (!flagged || !match)
		failed = 1;
}

/*
 * SIGSEGV's action through a raw rt_sigaction (no restorer on RISC-V), by
 * nolibc's _syscall(), its syscall() without the errno conversion: 0, or a
 * negative errno.
 */
static long set_segv(__sighandler_t handler, unsigned long flags)
{
	struct sigaction action;

	memset(&action, 0, sizeof(action));
	action.sa_handler = handler;
	action.sa_flags = flags;
	return _syscall(__NR_rt_sigaction, SIGSEGV, &action, NULL, SIGSET_BYTES);
}

/*
 * The handler: record the signal; step over the armed instruction alone,
 * on its first fault. Any other fault restores the default action, so the
 * instruction faults again and ends the child.
 */
static void on_segv(int signo, siginfo_t *info, void *context)
{
	struct ucontext *frame = context;
	unsigned long pc = frame->uc_mcontext.sc_regs.pc;

	seen_count = seen_count + 1UL;
	seen_signo = info->si_signo;
	seen_code = info->si_code;
	seen_addr = (unsigned long)info->si_addr;
	seen_pc = pc;
	if (signo == SIGSEGV && pc == armed_pc && seen_count == 1UL)
		frame->uc_mcontext.sc_regs.pc = pc + 4UL;
	else
		(void)set_segv(SIG_DFL, 0UL);
}

/*
 * The read-write mapping that holds a store's GPA (guest/mvp-guest-id.h's
 * rule): M1's channel page, or M2's request or response page; NULL when
 * that page is not mapped.
 */
static volatile unsigned long *store_page(const struct mvp_role *role,
					  unsigned long gpa)
{
	unsigned long index;

	if (role->pages == 0UL)
		return channel_page;
	for (index = 0; index < MVP_PAGES_WRITABLE; ++index)
		if (gpa >= role->page[index] &&
		    gpa - role->page[index] < MVP_PAGE_BYTES)
			return anchor_page[index];
	return NULL;
}

/*
 * In the child, with the handler installed: be.deny's access INDEX, then
 * its line 08; 1 when the denial failed, else 0. A store is unchanged when
 * its word still holds M1's writer's pattern word, or, with AS_FOUND (M2's
 * roles and M7's verbs), what it held before the store.
 */
static unsigned long deny_one(const struct mvp_role *role, unsigned long index,
			      int as_found)
{
	const struct mvp_denial *entry = &role->deny[index];
	int store = entry->access == MVP_ACCESS_STORE;
	unsigned long label = (unsigned long)(store ? mvp_store_insn :
						      mvp_load_insn);
	unsigned long offset = entry->gpa & (MVP_PAGE_BYTES - 1UL);
	volatile unsigned long *page, *word;
	unsigned long before = 0;
	int observed, unchanged = 0;

	page = store ? store_page(role, entry->gpa) :
		       map_page(entry->gpa, PROT_READ);
	if (page == NULL) {
		say("MVPINIT 08 DENIED n=%lu kind=%s gpa=0x%lx error=%d",
		    index + 1UL, store ? "store" : "load", entry->gpa, errno);
		return 1UL;
	}
	word = page + offset / sizeof(unsigned long);
	if (store && !as_found)
		before = offset == 0UL ? CHANNEL_FLAG :
			 pattern[offset / sizeof(unsigned long)];
	else if (store)
		before = *word;
	seen_count = 0;
	seen_signo = 0;
	seen_code = 0;
	seen_addr = 0;
	seen_pc = 0;
	armed_pc = label;
	if (store) {
		mvp_store_zero(word);
		unchanged = *word == before;
	} else {
		(void)mvp_load(word, 0UL);
	}
	armed_pc = 0;
	observed = seen_count == 1UL && seen_signo == SIGSEGV &&
		   seen_code == SEGV_ACCERR && seen_addr == label &&
		   seen_pc == label;
	if (store)
		say("MVPINIT 08 DENIED n=%lu kind=store gpa=0x%lx va=0x%lx "
		    "pc=0x%lx signo=%d code=%d observed=%d unchanged=%d",
		    index + 1UL, entry->gpa, (unsigned long)word, seen_pc,
		    seen_signo, seen_code, observed, unchanged);
	else
		say("MVPINIT 08 DENIED n=%lu kind=load gpa=0x%lx va=0x%lx "
		    "pc=0x%lx signo=%d code=%d observed=%d", index + 1UL,
		    entry->gpa, (unsigned long)word, seen_pc, seen_signo,
		    seen_code, observed);
	return !observed || (store && !unchanged) ? 1UL : 0UL;
}

/*
 * In the child: each denied access in be.deny's order (deny_one); the
 * number of denials that failed (all of them when the handler cannot be
 * installed). M1's stores are judged by the writer's pattern, M2's by
 * what the word held.
 */
static unsigned long make_denials(const struct mvp_role *role)
{
	unsigned long index, failures = 0;

	if (role->denials != 0UL &&
	    set_segv((__sighandler_t)(void (*)(void))on_segv, SA_SIGINFO) != 0)
		return role->denials;
	for (index = 0; index < role->denials; ++index)
		failures += deny_one(role, index, role->pages != 0UL);
	return failures;
}

/*
 * M2's roles, after line 02 (planning/mvp-m2-plan.md, Guest software and
 * Q2): load the management module and open its device, then map the
 * role's pages through /dev/mem, the request and response pages read-write
 * and, for prot, the secret page read-only; line 07. Each failure prints
 * its own line 07 and fails the run. finit_module has no nolibc wrapper:
 * a raw call, as rt_sigaction's, gives 0 or a negative errno.
 */
static void open_anchor(const struct mvp_role *role)
{
	int host = role->role == MVP_ROLE_HOST;
	const char *name = host ? "host" : "prot";
	unsigned long count = host ? HOST_PAGES : MVP_PAGES;
	unsigned long index;
	long loaded;
	int fd;

	fd = open(MGMT_MODULE, O_RDONLY);
	if (fd < 0) {
		loaded = -(long)errno;
	} else {
		loaded = _syscall(__NR_finit_module, fd, "", 0);
		(void)close(fd);
	}
	if (loaded != 0) {
		failed = 1;
		say("MVPINIT 07 MODULE role=%s error=%ld", name, -loaded);
	}
	mgmt_fd = open(MGMT_DEVICE, O_RDWR);
	if (mgmt_fd < 0) {
		failed = 1;
		say("MVPINIT 07 DEVICE role=%s error=%d", name, errno);
	}
	for (index = 0; index < count; ++index) {
		int protection = index < MVP_PAGES_WRITABLE ?
				 PROT_READ | PROT_WRITE : PROT_READ;

		anchor_page[index] = map_page(role->page[index], protection);
		if (anchor_page[index] == NULL) {
			failed = 1;
			say("MVPINIT 07 PAGES role=%s gpa=0x%lx error=%d", name,
			    role->page[index], errno);
			return;
		}
	}
	say("MVPINIT 07 PAGES role=%s count=%lu", name, count);
}

/* A digest as 64 lower-case hex digits and a NUL in TEXT. */
static void hex_of(const unsigned char *digest, char *text)
{
	static const char digits[] = "0123456789abcdef";
	unsigned long index;

	for (index = 0; index < BE_MVP_SHA256_BYTES; ++index) {
		text[2UL * index] = digits[digest[index] >> 4];
		text[2UL * index + 1UL] = digits[digest[index] & 0xfU];
	}
	text[2UL * BE_MVP_SHA256_BYTES] = '\0';
}

/*
 * The host's request n (Q8): the message, a fence, and n in the request
 * page; then the response page's sequence number, polled 1 ms apart until
 * REQUEST_DEADLINE_NS of CLOCK_MONOTONIC time have passed, and once it is
 * n, a fence and the digest; line 09. Whether the request was answered.
 */
static int request(unsigned long n)
{
	volatile unsigned long *request_page = anchor_page[0];
	volatile unsigned long *response_page = anchor_page[1];
	union mvp_message message;
	union mvp_digest digest;
	char text[2UL * BE_MVP_SHA256_BYTES + 1UL];
	unsigned long index, start, now;

	memset(&message, 0, sizeof(message));
	(void)snprintf((char *)message.byte, sizeof(message.byte),
		       MESSAGE_PREFIX "%lu", n);
	for (index = 0; index < MESSAGE_WORDS; ++index)
		request_page[BODY_WORD + index] = message.word[index];
	__sync_synchronize();
	request_page[SEQUENCE_WORD] = n;
	start = monotonic_ns();
	for (;;) {
		if (response_page[SEQUENCE_WORD] == n) {
			__sync_synchronize();
			for (index = 0; index < DIGEST_WORDS; ++index)
				digest.word[index] =
					response_page[BODY_WORD + index];
			hex_of(digest.byte, text);
			say("MVPINIT 09 REQUEST n=%lu digest=%s", n, text);
			return 1;
		}
		now = monotonic_ns();
		if (failed || now < start || now - start >= REQUEST_DEADLINE_NS)
			break;
		sleep_ms(POLL_MS);
	}
	say("MVPINIT 09 REQUEST n=%lu timeout=1", n);
	return 0;
}

/*
 * A step's management call, made step->count times, each one ioctl on the
 * device (Q2, Q3) by a raw call, which gives 0 or a negative errno; one
 * line 10. A failed ioctl, or a result other than the step's, fails the
 * run.
 */
static void call_step(const struct mvp_step *step)
{
	char number[24], list[96];
	const char *fid = number;
	long result[MGMT_BURST_MAX], error = 0;
	unsigned long index, used = 0, count = step->count;
	int same = 1;

	if (step->fid == MGMT_FID_PAUSE)
		fid = "pause";
	else if (step->fid == MGMT_FID_TERMINATE)
		fid = "terminate";
	else
		(void)snprintf(number, sizeof(number), "%lu", step->fid);
	if (count > MGMT_BURST_MAX)
		count = MGMT_BURST_MAX;
	for (index = 0; index < count; ++index) {
		struct be_mgmt_call call;
		long done;

		call.fid = step->fid;
		call.target = step->target;
		call.result = 0;
		done = _syscall(__NR_ioctl, mgmt_fd, BE_MGMT_IOC_CALL, &call);
		if (done != 0) {
			if (error == 0)
				error = -done;
			result[index] = 0;
			continue;
		}
		result[index] = (long)call.result;
		same = same && result[index] == result[0];
	}
	if (error != 0 || count != step->count) {
		failed = 1;
		if (count == 1UL)
			say("MVPINIT 10 MGMT fid=%s target=%lu error=%ld", fid,
			    step->target, error);
		else
			say("MVPINIT 10 MGMT burst=%lu fid=%s target=%lu "
			    "error=%ld", step->count, fid, step->target, error);
		return;
	}
	for (index = 0; index < count; ++index)
		if (result[index] != step->expected)
			failed = 1;
	if (count == 1UL) {
		say("MVPINIT 10 MGMT fid=%s target=%lu result=%ld", fid,
		    step->target, result[0]);
		return;
	}
	if (same) {
		say("MVPINIT 10 MGMT burst=%lu fid=%s target=%lu "
		    "results=%ldx%lu", count, fid, step->target, result[0],
		    count);
		return;
	}
	list[0] = '\0';
	for (index = 0; index < count && used < sizeof(list); ++index) {
		int length = snprintf(list + used, sizeof(list) - used, "%s%ld",
				      index == 0UL ? "" : ",", result[index]);

		if (length < 0)
			break;
		used += (unsigned long)length;
	}
	say("MVPINIT 10 MGMT burst=%lu fid=%s target=%lu results=%s", count,
	    fid, step->target, list);
}

/*
 * A role's script, in order: each request, unless the role's pages are
 * not mapped, and each call; a request answered or unanswered other than
 * as the step expects fails the run.
 */
static void run_script(const struct mvp_step *steps, unsigned long count)
{
	unsigned long index;

	for (index = 0; index < count; ++index) {
		const struct mvp_step *step = &steps[index];

		if (step->fid != STEP_REQUEST)
			call_step(step);
		else if (anchor_page[0] == NULL || anchor_page[1] == NULL)
			failed = 1;
		else if ((long)request(step->target) != step->expected)
			failed = 1;
	}
}

/*
 * The protected domain's answer to request n (Q6, Q8): HMAC-SHA-256 keyed
 * by the secret over n's eight little-endian bytes and the request's
 * 64-byte message, the digest in the response page, a fence, and n; line
 * 09.
 */
static void answer(unsigned long n, const union mvp_secret *secret)
{
	volatile unsigned long *request_page = anchor_page[0];
	volatile unsigned long *response_page = anchor_page[1];
	union mvp_hmac_input input;
	union mvp_digest digest;
	char text[2UL * BE_MVP_SHA256_BYTES + 1UL];
	unsigned long index;

	for (index = 0; index < sizeof(unsigned long); ++index)
		input.byte[index] = (unsigned char)(n >> (8UL * index));
	for (index = 0; index < MESSAGE_WORDS; ++index)
		input.word[1UL + index] = request_page[BODY_WORD + index];
	be_mvp_hmac_sha256(secret->byte, SECRET_BYTES, input.byte,
			   sizeof(input.byte), digest.byte);
	for (index = 0; index < DIGEST_WORDS; ++index)
		response_page[BODY_WORD + index] = digest.word[index];
	__sync_synchronize();
	response_page[SEQUENCE_WORD] = n;
	hex_of(digest.byte, text);
	say("MVPINIT 09 RESPONSE n=%lu digest=%s", n, text);
}

/*
 * The protected domain's service (Q8), for ever: the secret, read once and
 * never printed; then the request page's sequence number, polled 1 ms
 * apart, and an answer to each one above the last answered. Without its
 * pages it only sleeps.
 */
static void serve(void) __attribute__((noreturn));
static void serve(void)
{
	volatile unsigned long *request_page = anchor_page[0];
	volatile unsigned long *secret_page = anchor_page[2];
	union mvp_secret secret;
	unsigned long index, n, last = 0;

	if (request_page == NULL || anchor_page[1] == NULL ||
	    secret_page == NULL)
		for (;;)
			sleep_ms(SLEEP_MS);
	for (index = 0; index < SECRET_WORDS; ++index)
		secret.word[index] = secret_page[index];
	for (;;) {
		n = request_page[SEQUENCE_WORD];
		if (n > last) {
			__sync_synchronize();
			answer(n, &secret);
			last = n;
		} else {
			sleep_ms(POLL_MS);
		}
	}
}

/*
 * The role's steps, after line 02 (planning/mvp-m1-plan.md, Guest software
 * and Plan revision M1-A.1): M1's channel, or M2's module and pages, in the
 * init, then the denials in one child, which the init waits for; a fork
 * failure, an abnormal exit, or a nonzero status fails the run. Then M2's
 * scripts: the host's, after which the init goes on to M0's steps, and the
 * protected domain's, after which it serves and never returns.
 */
static void run_role(const struct mvp_role *role)
{
	pid_t child;
	int status = 0;

	if (role->pages != 0UL) {
		open_anchor(role);
	} else {
		make_pattern();
		pattern_digest = digest_of(pattern);
		if (role->role == MVP_ROLE_WRITER)
			write_channel(role->channel);
		else
			read_channel(role->channel);
	}
	child = fork();
	if (child == 0)
		_exit((int)make_denials(role));
	if (child < 0 || waitpid(child, &status, 0) != child ||
	    !WIFEXITED(status) || WEXITSTATUS(status) != 0)
		failed = 1;
	if (role->role == MVP_ROLE_HOST) {
		run_script(host_script,
			   sizeof(host_script) / sizeof(host_script[0]));
	} else if (role->role == MVP_ROLE_PROT) {
		run_script(prot_script,
			   sizeof(prot_script) / sizeof(prot_script[0]));
		serve();
	}
}

static void finish(void) __attribute__((noreturn));
static void finish(void)
{
	say("MVPINIT 05 RESULT %s", failed ? "fail" : "pass");
	say("MVPINIT 06 POWER_OFF");
	(void)reboot(LINUX_REBOOT_CMD_POWER_OFF);
	for (;;)
		__asm__ __volatile__("" ::: "memory");
}

/*
 * BE_ARGS= and the init's be.* arguments, in order, separated by single
 * spaces, into args_env (M7, D-9); 0, or -1 when they do not fit.
 */
static int make_args_env(int argc, char *const *argv)
{
	unsigned long used = sizeof(ARGS_KEY) - 1UL;
	int arg_index;

	memcpy(args_env, ARGS_KEY, used);
	for (arg_index = 1; arg_index < argc; ++arg_index) {
		const char *arg = argv[arg_index];
		unsigned long length;

		if (arg == NULL || strncmp(arg, "be.", 3) != 0)
			continue;
		length = strlen(arg);
		if (used + 1UL + length >= sizeof(args_env))
			return -1;
		if (used != sizeof(ARGS_KEY) - 1UL)
			args_env[used++] = ' ';
		memcpy(args_env + used, arg, length);
		used += length;
	}
	args_env[used] = '\0';
	return 0;
}

/* In the shell's child: a step failed with ERROR (a positive errno). */
static void shell_failed(const char *step, long error) __attribute__((noreturn));
static void shell_failed(const char *step, long error)
{
	say("MVPINIT 11 SHELL error=%ld step=%s", error, step);
	_exit(SHELL_FAILED);
}

/*
 * In the shell's child: a new session, /dev/hvc0 as its controlling
 * terminal and its standard descriptors, and /bin/sh. Raw ioctl, as the
 * management call's, gives 0 or a negative errno.
 */
static void start_shell(void) __attribute__((noreturn));
static void start_shell(void)
{
	static char *const shell_argv[] = { "sh", NULL };
	static char *const shell_env[] = { "HOME=/", "PATH=/bin", "PS1=# ",
					   args_env, NULL };
	long done;
	int fd, target;

	if (setsid() < 0)
		shell_failed("setsid", errno);
	fd = open(SHELL_TTY, O_RDWR);
	if (fd < 0)
		shell_failed("open", errno);
	done = _syscall(__NR_ioctl, fd, TIOCSCTTY, 0);
	if (done != 0)
		shell_failed("ctty", -done);
	for (target = STDIN_FILENO; target <= STDERR_FILENO; ++target)
		if (dup2(fd, target) != target)
			shell_failed("dup", errno);
	if (fd > STDERR_FILENO)
		(void)close(fd);
	(void)execve(SHELL_PATH, shell_argv, shell_env);
	shell_failed("exec", errno);
}

/*
 * /init-shell, after line 02 (planning/mvp-m7-plan.md, D-9 and Q4): BE_ARGS,
 * line 11, the shell in one child, every child reaped until the shell's
 * exit, line 11 with its status, and finish(). ROLES is mvp_role_args()'s
 * result for ROLE.
 */
static void run_shell(int argc, char *const *argv, int roles,
		      const struct mvp_role *role) __attribute__((noreturn));
static void run_shell(int argc, char *const *argv, int roles,
		      const struct mvp_role *role)
{
	static const char *const names[] = { "none", "writer", "reader", "host",
					     "prot" };
	const char *kind = roles == MVP_ROLE_MALFORMED ? "malformed" :
			   roles == MVP_ROLE_VALID ? names[role->role] : "none";
	pid_t child, reaped;
	int status = 0;

	if (make_args_env(argc, argv) != 0) {
		failed = 1;
		say("MVPINIT 11 SHELL error=%d step=args", E2BIG);
		finish();
	}
	say("MVPINIT 11 SHELL tty=%s role=%s", SHELL_TTY, kind);
	child = fork();
	if (child == 0)
		start_shell();
	if (child < 0) {
		failed = 1;
		say("MVPINIT 11 SHELL error=%d step=fork", errno);
		finish();
	}
	do {
		reaped = waitpid(-1, &status, 0);
	} while (reaped > 0 && reaped != child);
	if (reaped != child) {
		failed = 1;
		say("MVPINIT 11 SHELL error=%d step=wait", errno);
	} else if (WIFEXITED(status)) {
		say("MVPINIT 11 SHELL exit=%d", WEXITSTATUS(status));
		if (WEXITSTATUS(status) != 0)
			failed = 1;
	} else {
		failed = 1;
		say("MVPINIT 11 SHELL signal=%d", WTERMSIG(status));
	}
	finish();
}

/* A verb's refusal: TEXT on standard error; the usage status. */
static int refuse(const char *text)
{
	say_fd = STDERR_FILENO;
	say("%s", text);
	say_fd = STDOUT_FILENO;
	return VERB_USAGE;
}

/*
 * A verb's role: BE_ARGS's words as the init's arguments, by
 * guest/mvp-guest-id.h's rules; mvp_role_args()'s result, and
 * MVP_ROLE_MALFORMED without BE_ARGS or when it holds too much. GUEST,
 * when not NULL, takes the guest ID the words name (mvp_guest_id()).
 */
static int verb_role(struct mvp_role *role, int *guest)
{
	static char copy[ARGS_CAPACITY];
	static char key[] = "BE_ARGS";
	char *words[1UL + ARGS_WORDS];
	const char *value = getenv(key);
	unsigned long length, count = 1;
	char *cursor;

	if (value == NULL)
		return MVP_ROLE_MALFORMED;
	length = strlen(value);
	if (length >= sizeof(copy))
		return MVP_ROLE_MALFORMED;
	memcpy(copy, value, length + 1UL);
	words[0] = key;
	cursor = copy;
	while (*cursor != '\0') {
		if (*cursor == ' ') {
			*cursor++ = '\0';
			continue;
		}
		if (count == 1UL + ARGS_WORDS)
			return MVP_ROLE_MALFORMED;
		words[count++] = cursor;
		while (*cursor != '\0' && *cursor != ' ')
			++cursor;
	}
	if (guest != NULL)
		*guest = mvp_guest_id((int)count, words);
	return mvp_role_args((int)count, words, role);
}

/*
 * be-chan write TEXT... and be-chan read: M1's channel page, through
 * /dev/mem, as the text protocol (TEXT_*) holds it; line 12.
 */
static int verb_chan(int argc, char **argv)
{
	static const char usage[] = "usage: be-chan write TEXT... | be-chan read";
	union {
		unsigned long word[TEXT_WORDS];
		char byte[TEXT_MAX + 1UL];
	} text;
	volatile unsigned long *page;
	struct mvp_role role;
	unsigned long length = 0, index;
	int write_text, arg_index;

	if (argc < 2 || (strcmp(argv[1], "read") != 0 &&
			 (strcmp(argv[1], "write") != 0 || argc < 3)) ||
	    (strcmp(argv[1], "read") == 0 && argc != 2))
		return refuse(usage);
	write_text = strcmp(argv[1], "write") == 0;
	memset(&text, 0, sizeof(text));
	for (arg_index = 2; write_text && arg_index < argc; ++arg_index) {
		const char *word = argv[arg_index];

		if (arg_index > 2 && length < TEXT_MAX)
			text.byte[length++] = ' ';
		for (; *word != '\0'; ++word) {
			if (length == TEXT_MAX || *word < 0x20 || *word > 0x7e)
				return refuse("be-chan write: the text is 1 to "
					      "64 printable ASCII bytes");
			text.byte[length++] = *word;
		}
	}
	if (write_text && (length == 0UL || text.byte[length - 1UL] == ' '))
		return refuse("be-chan write: the text is 1 to 64 printable "
			      "ASCII bytes");
	if (verb_role(&role, NULL) != MVP_ROLE_VALID ||
	    (role.role != MVP_ROLE_WRITER &&
	     (write_text || role.role != MVP_ROLE_READER)))
		return refuse(write_text ? "be-chan write: BE_ARGS names no "
					   "channel writer (be.role=writer)" :
					   "be-chan read: BE_ARGS names no "
					   "channel role (be.role=writer or "
					   "reader)");
	page = map_page(role.channel, write_text ? PROT_READ | PROT_WRITE :
						   PROT_READ);
	if (page == NULL) {
		say("MVPINIT 12 CHAN %s gpa=0x%lx error=%d",
		    write_text ? "write" : "read", role.channel, errno);
		return VERB_FAILED;
	}
	if (write_text) {
		page[TEXT_FLAG_WORD] = 0;
		__asm__ __volatile__("fence w, w" ::: "memory");
		page[TEXT_LENGTH_WORD] = length;
		for (index = 0; index < TEXT_WORDS; ++index)
			page[TEXT_WORD + index] = text.word[index];
		__asm__ __volatile__("fence w, w" ::: "memory");
		page[TEXT_FLAG_WORD] = TEXT_FLAG;
		say("MVPINIT 12 CHAN write gpa=0x%lx bytes=%lu text=%s",
		    role.channel, length, text.byte);
		return 0;
	}
	if (page[TEXT_FLAG_WORD] != TEXT_FLAG) {
		say("MVPINIT 12 CHAN read gpa=0x%lx empty=1", role.channel);
		return VERB_FAILED;
	}
	__asm__ __volatile__("fence r, r" ::: "memory");
	length = page[TEXT_LENGTH_WORD];
	if (length == 0UL || length > TEXT_MAX) {
		say("MVPINIT 12 CHAN read gpa=0x%lx error=%d", role.channel,
		    EINVAL);
		return VERB_FAILED;
	}
	for (index = 0; index < TEXT_WORDS; ++index)
		text.word[index] = page[TEXT_WORD + index];
	text.byte[length] = '\0';
	for (index = 0; index < length; ++index)
		if (text.byte[index] < 0x20 || text.byte[index] > 0x7e)
			text.byte[index] = '?';
	say("MVPINIT 12 CHAN read gpa=0x%lx bytes=%lu text=%s", role.channel,
	    length, text.byte);
	return 0;
}

/*
 * be-deny load-unmapped and be-deny store-shared: be.deny's first access
 * of that kind, made in one forked child by the roles' handler
 * (deny_one); a store's page mapped read-write first, as the roles map it.
 */
static int verb_deny(int argc, char **argv)
{
	static const char usage[] = "usage: be-deny load-unmapped | "
				    "be-deny store-shared";
	struct mvp_role role;
	unsigned long index, slot;
	int kind, status = 0;
	pid_t child;

	if (argc != 2)
		return refuse(usage);
	if (strcmp(argv[1], "load-unmapped") == 0)
		kind = MVP_ACCESS_LOAD;
	else if (strcmp(argv[1], "store-shared") == 0)
		kind = MVP_ACCESS_STORE;
	else
		return refuse(usage);
	if (verb_role(&role, NULL) != MVP_ROLE_VALID)
		return refuse("be-deny: BE_ARGS names no role");
	for (index = 0; index < role.denials; ++index)
		if (role.deny[index].access == kind)
			break;
	if (index == role.denials)
		return refuse(kind == MVP_ACCESS_LOAD ?
			      "be-deny: be.deny names no load" :
			      "be-deny: be.deny names no store");
	if (kind == MVP_ACCESS_STORE && role.pages == 0UL) {
		channel_page = map_page(role.channel, PROT_READ | PROT_WRITE);
	} else if (kind == MVP_ACCESS_STORE) {
		for (slot = 0; slot < MVP_PAGES_WRITABLE; ++slot)
			if (role.deny[index].gpa - role.page[slot] <
			    MVP_PAGE_BYTES)
				anchor_page[slot] = map_page(
					role.page[slot],
					PROT_READ | PROT_WRITE);
	}
	child = fork();
	if (child == 0)
		_exit(set_segv((__sighandler_t)(void (*)(void))on_segv,
			       SA_SIGINFO) != 0 ? 1 :
		      (int)deny_one(&role, index, 1));
	if (child < 0 || waitpid(child, &status, 0) != child ||
	    !WIFEXITED(status) || WEXITSTATUS(status) != 0)
		return VERB_FAILED;
	return 0;
}

/* N, 1 to REQUEST_MAX in decimal without a leading zero; 0 if not one. */
static unsigned long request_number(const char *text)
{
	unsigned long value = 0;

	if (*text < '1' || *text > '9')
		return 0;
	for (; *text != '\0'; ++text) {
		if (*text < '0' || *text > '9')
			return 0;
		value = value * 10UL + (unsigned long)(*text - '0');
		if (value > REQUEST_MAX)
			return 0;
	}
	return value;
}

/*
 * be-anchor pause and be-anchor terminate (M7-4): the host's call of that
 * management function on the other domain, as M2's host makes it: the
 * module loaded (once: a module already loaded is no failure) and its
 * device opened, as open_anchor() does, then one ioctl and its line 10
 * (call_step()); the status 0 only for the call's success. A module or
 * device that fails prints line 10 with the errno.
 */
static int verb_manage(unsigned long fid)
{
	const char *name = fid == MGMT_FID_PAUSE ? "pause" : "terminate";
	struct mvp_role role;
	struct mvp_step step;
	long loaded;
	int guest = MVP_GUEST_ID_NONE, fd;

	if (verb_role(&role, &guest) != MVP_ROLE_VALID ||
	    role.role != MVP_ROLE_HOST || guest == MVP_GUEST_ID_NONE)
		return refuse("be-anchor: BE_ARGS names no host (be.role=host)");
	step.fid = fid;
	step.target = (unsigned long)(MVP_GUEST_IDS - 1 - guest);
	step.count = 1UL;
	step.expected = SBI_SUCCESS;
	fd = open(MGMT_MODULE, O_RDONLY);
	if (fd < 0) {
		loaded = -(long)errno;
	} else {
		loaded = _syscall(__NR_finit_module, fd, "", 0);
		(void)close(fd);
	}
	if (loaded != 0 && loaded != -(long)EEXIST) {
		say("MVPINIT 10 MGMT fid=%s target=%lu error=%ld", name,
		    step.target, -loaded);
		return VERB_FAILED;
	}
	mgmt_fd = open(MGMT_DEVICE, O_RDWR);
	if (mgmt_fd < 0) {
		say("MVPINIT 10 MGMT fid=%s target=%lu error=%d", name,
		    step.target, errno);
		return VERB_FAILED;
	}
	call_step(&step);
	return failed ? VERB_FAILED : 0;
}

/*
 * be-anchor request N: the host's request N through the request and
 * response pages (request()), mapped read-write as the host maps them;
 * be-anchor pause and terminate, verb_manage().
 */
static int verb_anchor(int argc, char **argv)
{
	struct mvp_role role;
	unsigned long n, index;

	if (argc == 2 && strcmp(argv[1], "pause") == 0)
		return verb_manage(MGMT_FID_PAUSE);
	if (argc == 2 && strcmp(argv[1], "terminate") == 0)
		return verb_manage(MGMT_FID_TERMINATE);
	n = argc == 3 && strcmp(argv[1], "request") == 0 ?
		request_number(argv[2]) : 0UL;
	if (n == 0UL)
		return refuse("usage: be-anchor request N (1 to 999999999)");
	if (verb_role(&role, NULL) != MVP_ROLE_VALID ||
	    role.role != MVP_ROLE_HOST)
		return refuse("be-anchor: BE_ARGS names no host (be.role=host)");
	for (index = 0; index < MVP_PAGES_WRITABLE; ++index) {
		anchor_page[index] = map_page(role.page[index],
					      PROT_READ | PROT_WRITE);
		if (anchor_page[index] == NULL) {
			say("MVPINIT 09 REQUEST n=%lu gpa=0x%lx error=%d", n,
			    role.page[index], errno);
			return VERB_FAILED;
		}
	}
	return request(n) ? 0 : VERB_FAILED;
}

/* BYTES, LENGTH of them, on standard output; a short write fails the run. */
static void put_raw(const char *bytes, unsigned long length)
{
	unsigned long done = 0;

	while (done < length) {
		ssize_t written = write(STDOUT_FILENO, bytes + done,
					length - done);

		if (written <= 0) {
			failed = 1;
			return;
		}
		done += (unsigned long)written;
	}
}

/*
 * /init-hostile, after line 01 (M7-4; planning/mvp-m7-plan.md, D-4): a
 * QEMU-only guest that prints what a hostile guest could, each line with
 * one write(2): every byte value, 0x00 to 0xff, in eight lines of 32 after
 * a printable head (line 13 bytes=<k>, then the values 32k to 32k + 31
 * raw, so the first holds LF and CR); a look-alike of hart 0's run line
 * and a line that begins with the other domain's prefix; a terminal's
 * cursor-position query (ESC [ 6 n) and a window-title sequence (ESC ]
 * 0 ; ... BEL); and one line of 300 bytes. Then finish(). The monitor
 * must show each as this domain's, behind its own prefix, every byte
 * outside 0x20 to 0x7e as ?, CR not at all, an LF as the end of a line,
 * and the long line as a line of 256 bytes and one of the rest.
 */
static void run_hostile(void) __attribute__((noreturn));
static void run_hostile(void)
{
	static const char forged[] = "BE_MVP:13 RUN_COMPLETE forged\n"
				     "BE_MVP_G1: forged\n"
				     "MVPINIT 13 HOSTILE query=\x1b[6n "
				     "title=\x1b]0;forged\x07\n";
	static const char long_head[] = "MVPINIT 13 HOSTILE long=300 ";
	char text[HOSTILE_LONG_BYTES + 1UL];
	unsigned long block, index, length;
	int head;

	for (block = 0; block < HOSTILE_BLOCKS; ++block) {
		head = snprintf(text, sizeof(text), "MVPINIT 13 HOSTILE "
				"bytes=%lu ", block);
		length = head > 0 ? (unsigned long)head : 0UL;
		for (index = 0; index < HOSTILE_BLOCK_BYTES; ++index)
			text[length++] = (char)(block * HOSTILE_BLOCK_BYTES +
						index);
		text[length++] = '\n';
		put_raw(text, length);
	}
	put_raw(forged, sizeof(forged) - 1UL);
	memcpy(text, long_head, sizeof(long_head) - 1UL);
	for (index = sizeof(long_head) - 1UL; index < HOSTILE_LONG_BYTES;
	     ++index)
		text[index] = 'x';
	text[HOSTILE_LONG_BYTES] = '\n';
	put_raw(text, HOSTILE_LONG_BYTES + 1UL);
	finish();
}

/* A helper verb by its name, argv[0]'s last component. */
static int run_verb(const char *verb, int argc, char **argv)
{
	if (strcmp(verb, "be-chan") == 0)
		return verb_chan(argc, argv);
	if (strcmp(verb, "be-deny") == 0)
		return verb_deny(argc, argv);
	if (strcmp(verb, "be-anchor") == 0)
		return verb_anchor(argc, argv);
	return refuse("usage: be-chan, be-deny, or be-anchor");
}

int main(int argc, char **argv)
{
	const char *name = argc > 0 ? argv[0] : NULL;
	const char *verb = name != NULL ? strrchr(name, '/') : NULL;
	int guest = mvp_guest_id(argc, argv);
	pid_t pid = getpid();
	struct mvp_role role;
	unsigned long start, end, elapsed, n;
	int ok, roles, shell;

	/* A helper verb, run from the shell, prints no line 01 (M7, D-9). */
	verb = verb != NULL ? verb + 1 : name;
	if (verb != NULL && strncmp(verb, "be-", 3) == 0)
		return run_verb(verb, argc, argv);

	if (guest == MVP_GUEST_ID_NONE) {
		failed = 1;
		say("MVPINIT 01 START guest=none pid=%d", pid);
	} else {
		say("MVPINIT 01 START guest=%d pid=%d", guest, pid);
	}
	if (pid != 1)
		failed = 1;

	if (name != NULL && strcmp(name, "/init-exit") == 0)
		exit(0);
	if (name != NULL && strcmp(name, "/init-rdcycle") == 0) {
		unsigned long cycles;

		/* rdcycle: the MVP makes it a terminal virtual-instruction exit. */
		__asm__ __volatile__("csrr %0, 0xc00" : "=r"(cycles));
		(void)cycles;
		failed = 1;
		finish();
	}
	if (name != NULL && strcmp(name, "/init-hostile") == 0)
		run_hostile();
	shell = name != NULL && strcmp(name, "/init-shell") == 0;

	if (uname(&uts) != 0)
		failed = 1;
	say("MVPINIT 02 UNAME release=%s machine=%s", uts.release, uts.machine);
	if (strcmp(uts.release, EXPECTED_RELEASE) != 0 ||
	    strcmp(uts.machine, EXPECTED_MACHINE) != 0)
		failed = 1;

	roles = mvp_role_args(argc, argv, &role);
	if (roles == MVP_ROLE_MALFORMED)
		failed = 1;
	if (shell)
		run_shell(argc, argv, roles, &role);
	if (roles == MVP_ROLE_VALID)
		run_role(&role);

	for (n = 1; n <= STEPS; ++n)
		run_step(n);

	start = monotonic_ns();
	sleep_ms(SLEEP_MS);
	end = monotonic_ns();
	elapsed = end >= start ? (end - start) / NS_PER_MS : 0UL;
	ok = elapsed >= SLEEP_MS && elapsed <= SLEEP_MS_MAX;
	say("MVPINIT 04 SLEEP requested_ms=%lu elapsed_ms=%lu ok=%d", SLEEP_MS,
	    elapsed, ok);
	if (!ok)
		failed = 1;

	finish();
}
