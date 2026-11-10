// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * The CHERI test guest: one bare-metal program for both of te-poc's
 * domains. It learns its role from the boot arguments in its device tree,
 * prints CHERIGUEST lines through SBI DBCN, and ends with an SBI SRST
 * shutdown, which stops only its own domain. It is built once per test set
 * (TEST_SET_BASIC, TEST_SET_FAULT, TEST_SET_DDC), so that a test that may
 * end its domain runs in an image of its own. Hybrid CHERI v0.9.3: integer
 * pointers, with capabilities only where a test makes one.
 */

typedef unsigned long u64;
typedef void *__capability cap_t;

#define SBI_EXT_BASE	0x10UL
#define SBI_EXT_DBCN	0x4442434eUL
#define SBI_EXT_SRST	0x53525354UL

#define DTB_BYTES	4096UL
/* QEMU's virt timebase; the device trees name the board's 24 MHz. */
#define TICKS_PER_S	10000000UL

/* te-poc (mvp/scenarios/te-poc/scenario.json): one channel page that G0
 * maps read-write and G1 read-only. Its declared denials are not tested:
 * the monitor accepts a denial only from guest user mode, and this guest
 * runs in guest supervisor mode. */
#define CHANNEL_GPA	0x84000000UL
#define CHANNEL_FLAG	(CHANNEL_GPA + 0x10UL)
#define CHANNEL_MAGIC	0x4245434845524931UL

/* A page of G1's window above its device tree slot: G1's window is
 * host-physical 0x114000000 at GPA 0x80000000. */
#define DDC_TARGET_GPA	0x83f00800UL
#define DDC_TARGET_HPA	(0x114000000UL + (DDC_TARGET_GPA - 0x80000000UL))
#define DDC_WORD0	0xdd0c0ffee0000001UL
#define DDC_WORD1	0xdd0c0ffee0000002UL

#if defined(TEST_SET_BASIC)
#define SET_NAME "basic"
#elif defined(TEST_SET_FAULT)
#define SET_NAME "fault"
#elif defined(TEST_SET_DDC)
#define SET_NAME "ddc"
#else
#error "no test set"
#endif

struct trap_info {
	u64 t1;
	u64 cause;
	u64 tval;
	u64 epc;
	u64 recover;
	u64 count;
};

struct pair {
	u64 a;
	u64 b;
};

struct trap_info trap_info;

u64 probe_cheri(void);
struct pair probe_reg_across_call(u64 addr);
u64 probe_bounds_fault(u64 addr);
u64 load_via_cap(cap_t c);
u64 probe_ddc_restrict(u64 target, u64 w0, u64 w1);
void guest_main(u64 hartid, u64 dtb);
void guest_trap_fatal(void);

/* The compiler may emit these for loops; volatile stops it calling them. */
void *memset(void *d, int c, unsigned long n)
{
	volatile unsigned char *p = d;

	while (n--)
		*p++ = (unsigned char)c;
	return d;
}

void *memcpy(void *d, const void *s, unsigned long n)
{
	volatile unsigned char *p = d;
	const volatile unsigned char *q = s;

	while (n--)
		*p++ = *q++;
	return d;
}

static struct pair sbi(u64 eid, u64 fid, u64 a0, u64 a1, u64 a2)
{
	register u64 r0 __asm__("a0") = a0;
	register u64 r1 __asm__("a1") = a1;
	register u64 r2 __asm__("a2") = a2;
	register u64 r6 __asm__("a6") = fid;
	register u64 r7 __asm__("a7") = eid;

	__asm__ volatile("ecall"
			 : "+r"(r0), "+r"(r1)
			 : "r"(r2), "r"(r6), "r"(r7)
			 : "memory");
	return (struct pair){ r0, r1 };
}

static char line[256] __attribute__((aligned(16)));
static u64 line_len;

static void flush(void)
{
	if (line_len)
		sbi(SBI_EXT_DBCN, 0, line_len, (u64)line, 0);
	line_len = 0;
}

static void put(char c)
{
	line[line_len++] = c;
	if (c == '\n' || line_len == sizeof(line))
		flush();
}

static void say(const char *s)
{
	while (*s)
		put(*s++);
}

static void hex(u64 v)
{
	say("0x");
	for (int s = 60; s >= 0; s -= 4)
		put("0123456789abcdef"[(v >> s) & 15]);
}

static void dec(u64 v)
{
	char b[20];
	int n = 0;

	do {
		b[n++] = (char)('0' + v % 10);
		v /= 10;
	} while (v);
	while (n)
		put(b[--n]);
}

static void kv(const char *k, u64 v)
{
	put(' ');
	say(k);
	put('=');
	dec(v);
}

static void kx(const char *k, u64 v)
{
	put(' ');
	say(k);
	put('=');
	hex(v);
}

static u64 now(void)
{
	u64 t;

	__asm__ volatile("rdtime %0" : "=r"(t));
	return t;
}

static int has(const char *hay, u64 n, const char *needle)
{
	u64 m = 0;

	while (needle[m])
		m++;
	for (u64 i = 0; i + m <= n; i++) {
		u64 j = 0;

		while (j < m && hay[i + j] == needle[j])
			j++;
		if (j == m)
			return 1;
	}
	return 0;
}

static void __attribute__((noreturn)) finish(void)
{
	u64 start = now();

	/* The monitor requires its IPI probe, sent within milliseconds of
	 * entry, to be answered before a domain shuts down. */
	while (now() - start < 2 * TICKS_PER_S)
		;
	say("CHERIGUEST 99 END\n");
	sbi(SBI_EXT_SRST, 0, 0, 0, 0);
	for (;;)
		__asm__ volatile("wfi");
}

void guest_trap_fatal(void)
{
	say("CHERIGUEST FATAL");
	kx("scause", trap_info.cause);
	kx("stval", trap_info.tval);
	kx("sepc", trap_info.epc);
	put('\n');
	finish();
}

static char role;

#ifdef TEST_SET_BASIC
static u64 register_buf[8] __attribute__((aligned(64)));
static u64 channel_buf[8] __attribute__((aligned(64)));

/* A capability in a callee-saved register across one SBI call. */
static void test_register(void)
{
	struct pair r = probe_reg_across_call((u64)register_buf);

	say("CHERIGUEST 03 REGISTER");
	kv("tag_before", r.a & 1);
	kv("tag_after", (r.a >> 1) & 1);
	kv("address_kept", r.b == (u64)register_buf);
	put('\n');
}

/* The writer stores a capability to its own object in the channel page. */
static void test_channel_send(void)
{
	cap_t root = __builtin_cheri_global_data_get();
	cap_t c = __builtin_cheri_bounds_set(
		__builtin_cheri_address_set(root, (u64)channel_buf),
		sizeof(channel_buf));
	u64 tag_sent, tag_page;

	channel_buf[0] = 0x6730c0deUL;
	*(volatile cap_t *)CHANNEL_GPA = c;
	__asm__ volatile("fence w, w" ::: "memory");
	*(volatile u64 *)CHANNEL_FLAG = CHANNEL_MAGIC;
	tag_sent = __builtin_cheri_tag_get(c);
	tag_page = __builtin_cheri_tag_get(*(volatile cap_t *)CHANNEL_GPA);
	say("CHERIGUEST 04 CHANNEL sent");
	kv("tag", tag_sent);
	kv("tag_in_page", tag_page);
	kx("address", (u64)channel_buf);
	kv("length", sizeof(channel_buf));
	kx("own_value", channel_buf[0]);
	put('\n');
}

/* The reader loads it and uses it. */
static void test_channel_receive(void)
{
	u64 start = now(), seen = 0;
	u64 tag, addr, base, length, perms, via = 0, own = 0;
	cap_t c;

	channel_buf[0] = 0x6731c0deUL;
	while (now() - start < 20 * TICKS_PER_S) {
		if (*(volatile u64 *)CHANNEL_FLAG == CHANNEL_MAGIC) {
			seen = 1;
			break;
		}
	}
	if (!seen) {
		say("CHERIGUEST 04 CHANNEL received=0\n");
		return;
	}
	__asm__ volatile("fence r, r" ::: "memory");
	c = *(volatile cap_t *)CHANNEL_GPA;
	tag = __builtin_cheri_tag_get(c);
	addr = __builtin_cheri_address_get(c);
	base = __builtin_cheri_base_get(c);
	length = __builtin_cheri_length_get(c);
	perms = __builtin_cheri_perms_get(c);
	if (tag) {
		own = *(volatile u64 *)addr;
		via = load_via_cap(c);
	}
	say("CHERIGUEST 04 CHANNEL received=1");
	kv("tag", tag);
	kx("address", addr);
	kx("base", base);
	kv("length", length);
	kx("perms", perms);
	put('\n');
	if (tag) {
		say("CHERIGUEST 04 CHANNEL use");
		kx("via_capability", via);
		kx("own_value", own);
		kv("same", via == own);
		put('\n');
	}
}
#endif

#ifdef TEST_SET_FAULT
static u64 small_buf[2] __attribute__((aligned(16)));
#endif

void guest_main(u64 hartid, u64 dtb)
{
	const char *d = (const char *)dtb;
	u64 guest = has(d, DTB_BYTES, "be.guest=1") ? 1 : 0;
	u64 tag;

	role = has(d, DTB_BYTES, "be.role=writer") ? 'w' :
	       has(d, DTB_BYTES, "be.role=reader") ? 'r' : '?';
	say("CHERIGUEST 01 START");
	kv("guest", guest);
	say(role == 'w' ? " role=writer" : role == 'r' ? " role=reader" : " role=none");
	say(" set=" SET_NAME);
	kv("hart", hartid);
	put('\n');

	tag = probe_cheri();
	if (tag == ~0UL) {
		say("CHERIGUEST 02 CHERI available=0");
		kx("scause", trap_info.cause);
		put('\n');
		finish();
	} else {
		cap_t ddc = __builtin_cheri_global_data_get();
		cap_t pcc = __builtin_cheri_program_counter_get();
		u64 base = __builtin_cheri_base_get(ddc);
		u64 length = __builtin_cheri_length_get(ddc);
		u64 perms = __builtin_cheri_perms_get(ddc);
		u64 pcc_tag = __builtin_cheri_tag_get(pcc);

		say("CHERIGUEST 02 CHERI available=1");
		kv("ddc_tag", tag);
		kx("ddc_base", base);
		kx("ddc_length", length);
		kx("ddc_perms", perms);
		kv("pcc_tag", pcc_tag);
		put('\n');
	}

#ifdef TEST_SET_BASIC
	test_register();
	if (role == 'w')
		test_channel_send();
	else if (role == 'r')
		test_channel_receive();
#endif

#ifdef TEST_SET_FAULT
	{
		u64 took = probe_bounds_fault((u64)small_buf);

		say("CHERIGUEST 06 BOUNDS");
		kv("guest_took_fault", took);
		kx("scause", trap_info.cause);
		kx("stval", trap_info.tval);
		put('\n');
	}
#endif

#ifdef TEST_SET_DDC
	if (role == 'w') {
		u64 start = now(), r;

		while (now() - start < 2 * TICKS_PER_S)
			;
		say("CHERIGUEST 07 DDC restrict");
		kx("target_hpa", DDC_TARGET_HPA);
		kx("word0", DDC_WORD0);
		kx("word1", DDC_WORD1);
		put('\n');
		r = probe_ddc_restrict(DDC_TARGET_HPA, DDC_WORD0, DDC_WORD1);
		say("CHERIGUEST 07 DDC monitor_returned=1");
		kv("r", r);
		put('\n');
	} else if (role == 'r') {
		volatile u64 *w = (volatile u64 *)DDC_TARGET_GPA;
		u64 before0 = w[0], before1 = w[1];
		u64 start = now(), written = 0;

		while (now() - start < 30 * TICKS_PER_S) {
			if (w[0] == DDC_WORD0 && w[1] == DDC_WORD1) {
				written = 1;
				break;
			}
		}
		say("CHERIGUEST 07 DDC watch");
		kx("gpa", DDC_TARGET_GPA);
		kx("before0", before0);
		kx("before1", before1);
		kx("word0", w[0]);
		kx("word1", w[1]);
		kv("written_by_other_domain", written);
		put('\n');
	}
#endif
	finish();
}
