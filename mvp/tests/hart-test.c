// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the MVP hart blocks and hart 0's control loop:
 *          the Sv39x4 hgatp value; the bindings and their every malformed
 *          field; block descriptors as hart 0 fills them and every check a
 *          domain hart makes at entry (generation word, domain, hart, block,
 *          offsets, rings, hgatp) in its order; the state page's index
 *          lines; the control loop's every record type in every domain
 *          phase, out-of-order records included; payload sizes, times that
 *          go back, and SHUTDOWN's consistency words, its denial word
 *          included; FAIL; the PING and PONG of the IPI probe; the DENIAL
 *          step (planning/mvp-m1-plan.md, "Control loop and failure
 *          paths"): its phases, sequence numbers, the cause and injected
 *          cause, the GPA against htval and stval, the exit time, and the
 *          kind against the walked windows and the sealed channel record,
 *          with and without a channel, and against a scenario's declared
 *          pages (planning/mvp-m2-plan.md); the management requests
 *          (planning/mvp-m2-plan.md, "Control loop and failure paths"):
 *          Instance 3's sequence, each decision answered at once, each
 *          delivery pending until its target's PAUSED or TERMINATED, a
 *          second request while one is pending, requests to a paused, a
 *          terminated, and a shut-down domain, a target that shuts down
 *          first, the no-grant-check variant, SHUTDOWN's management word,
 *          and every malformed request and transition; done, a terminated
 *          domain counting as ended and a paused one not; the READY wait
 *          and the run budget, a clock behind the start included; hart 0's
 *          round-robin drain of two rings (Plan revision M0-C.1): one take
 *          from each in turn,
 *          empty and held rings skipped, its end, and its bound against
 *          writers as fast as the drain; the overlap and Q5's floor at
 *          its edges (disjoint, touching, nested, exactly half, odd
 *          lengths, extremes); saturating counters; invalid input, which
 *          fails closed and stays failed; the printed form of a LINE; and
 *          pseudo-random interleavings of two domains checked record by
 *          record against an independent model.
 * Trust:   host evidence only. No CSR, fence, IPI, second hart, QEMU, or
 *          hardware behaviour is exercised.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, "Hart region" and
 *          "Control loop"; planning/mvp-m1-plan.md; planning/mvp-m2-plan.md).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mvp-hart.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_HART_CHECK: assertion failed: %s:%d: %s\n", \
			       __FILE__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define START			BE_U64_C(0x1000)
#define BUDGET			BE_MVP_RUN_BUDGET
#define READY_WAIT		BE_MVP_READY_TICKS
#define ALL_ONES		(~BE_U64_C(0))
#define WORD			8U

#define STEP_INVALID		BE_MVP_STEP_INVALID
#define CLASS_NONE		BE_MVP_CLASS_NONE
#define CLASS_RING		BE_MVP_CLASS_RING
#define CLASS_IPI		BE_MVP_CLASS_IPI

static const struct be_mvp_binding defaults[BE_MVP_DOMAINS] =
	BE_MVP_BINDINGS_INITIALIZER;
static struct be_mvp_binding bindings[BE_MVP_DOMAINS];
static struct be_mvp_block_desc desc;
static struct be_mvp_control ctl;
static struct be_mvp_step_result result;
static struct be_mvp_record record;
/* Each domain's next record time and the LINE and DENIAL records it
 * sent. */
static be_u64 domain_time[BE_MVP_DOMAINS];
static be_u64 domain_lines[BE_MVP_DOMAINS];
static be_u64 domain_entered[BE_MVP_DOMAINS];
static be_u64 domain_denials[BE_MVP_DOMAINS];
/* Each domain's MGMT_REQUEST records sent (planning/mvp-m2-plan.md). */
static be_u64 domain_requests[BE_MVP_DOMAINS];
/*
 * What the loop checks a DENIAL against: each domain's walked window (only
 * its GPA and size matter) and te-poc's sealed channel record, G0 the
 * writer and G1 the reader (planning/mvp-m1-plan.md, Q1).
 */
static const struct be_mvp_gstage_map maps[BE_MVP_DOMAINS] = {
	{ .gpa_base = BE_MVP_GUEST_GPA, .hpa_base = BE_MVP_G0_HPA,
	  .size = BE_MVP_GUEST_BYTES, .hart = BE_MVP_DOMAIN0_HART },
	{ .gpa_base = BE_MVP_GUEST_GPA, .hpa_base = BE_MVP_G1_HPA,
	  .size = BE_MVP_GUEST_BYTES, .hart = BE_MVP_DOMAIN1_HART },
};
static const struct be_mvp_gstage_channel channel = {
	BE_MVP_CHANNEL_GPA, BE_MVP_CHANNEL_HPA, BE_MVP_CHANNEL_BYTES, 0U, 1U,
	BE_MVP_GSTAGE_RIGHT_READ | BE_MVP_GSTAGE_RIGHT_WRITE,
	BE_MVP_GSTAGE_RIGHT_READ,
};
static const struct be_mvp_gstage_channel no_channel;

#define FETCH			BE_MVP_SCAUSE_FETCH_GUEST_PAGE_FAULT
#define LOAD			BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT
#define STORE			BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT
#define UNMAPPED		BE_MVP_DENIAL_UNMAPPED
#define READ_ONLY		BE_MVP_DENIAL_READ_ONLY
#define PAGE_GPA		BE_MVP_CHANNEL_GPA
#define PAGE_LAST	(BE_MVP_CHANNEL_GPA + BE_MVP_CHANNEL_BYTES - 1U)
#define BESIDE_GPA		(BE_MVP_CHANNEL_GPA + BE_MVP_CHANNEL_BYTES)
#define WINDOW_LAST		(BE_MVP_GUEST_GPA + BE_MVP_GUEST_BYTES - 1U)
#define PROBE_GPA		BE_U64_C(0x90000000)
#define DENY_VA			BE_U64_C(0x3fffd5000)

static void set_word(struct be_mvp_record *entry, be_u64 index, be_u64 value)
{
	be_u64 byte;

	for (byte = 0U; byte < WORD; ++byte)
		entry->payload[index * WORD + byte] =
			(be_u8)((value >> (8U * byte)) & 0xffU);
}

/* A record of @words words, each word its index plus a marker. */
static void make(be_u32 type, be_u32 domain, be_u64 time, be_u64 words)
{
	be_u64 index;

	memset(&record, 0, sizeof(record));
	record.type = type;
	record.domain = domain;
	record.time = time;
	record.length = words * WORD;
	for (index = 0U; index < words; ++index)
		set_word(&record, index, BE_U64_C(0x5100) + index);
}

static void make_line(be_u32 domain, be_u64 time, const char *text)
{
	memset(&record, 0, sizeof(record));
	record.type = BE_MVP_RECORD_LINE;
	record.domain = domain;
	record.time = time;
	record.length = strlen(text);
	memcpy(record.payload, text, record.length);
}

static void make_pong(be_u32 domain, be_u64 time, be_u64 spv)
{
	make(BE_MVP_RECORD_PONG, domain, time, BE_MVP_PONG_WORDS);
	set_word(&record, BE_MVP_PONG_SENT, time - 2U);
	set_word(&record, BE_MVP_PONG_RECEIVED, time - 1U);
	set_word(&record, BE_MVP_PONG_SPV, spv);
}

/* SHUTDOWN, its denial and management words the DENIAL and MGMT_REQUEST
 * records the domain sent. */
static void make_shutdown(be_u32 domain, be_u64 time, be_u64 entered,
			  be_u64 lines, be_u64 peak)
{
	make(BE_MVP_RECORD_SHUTDOWN, domain, time, BE_MVP_SHUTDOWN_WORDS);
	set_word(&record, BE_MVP_SHUTDOWN_LINES, lines);
	set_word(&record, BE_MVP_SHUTDOWN_RING_PEAK, peak);
	set_word(&record, BE_MVP_SHUTDOWN_ENTERED, entered);
	set_word(&record, BE_MVP_SHUTDOWN_DENIALS,
		 domain < BE_MVP_DOMAINS ? domain_denials[domain] : 0U);
	set_word(&record, BE_MVP_SHUTDOWN_MGMT,
		 domain < BE_MVP_DOMAINS ? domain_requests[domain] : 0U);
}

/* The access fault each guest-page fault is injected as, or 0. */
static be_u64 injected(be_u64 cause)
{
	return cause == FETCH ? 1U : cause == LOAD ? 5U :
	       cause == STORE ? 7U : 0U;
}

/*
 * A DENIAL from @domain, posted at @time: @seq, @cause and its injected
 * cause, @kind, and @gpa with the htval and stval it came from; its exit
 * at the post. Its other words (htinst, sepc, vsstatus, vstvec) are logged
 * only, and keep make()'s markers.
 */
static void make_denial(be_u32 domain, be_u64 time, be_u64 seq, be_u64 cause,
			be_u64 kind, be_u64 gpa)
{
	make(BE_MVP_RECORD_DENIAL, domain, time, BE_MVP_DENIAL_WORDS);
	set_word(&record, BE_MVP_DENIAL_SEQ, seq);
	set_word(&record, BE_MVP_DENIAL_CAUSE, cause);
	set_word(&record, BE_MVP_DENIAL_KIND, kind);
	set_word(&record, BE_MVP_DENIAL_GPA, gpa);
	set_word(&record, BE_MVP_DENIAL_HTVAL, gpa >> 2);
	set_word(&record, BE_MVP_DENIAL_STVAL, DENY_VA | (gpa & 0xfffU));
	set_word(&record, BE_MVP_DENIAL_INJECTED, injected(cause));
	set_word(&record, BE_MVP_DENIAL_EXIT, time);
}

static void make_fail(be_u32 domain, be_u64 time, be_u64 failure,
		      be_u64 detail)
{
	make(BE_MVP_RECORD_FAIL, domain, time, 1U + detail);
	set_word(&record, BE_MVP_FAIL_CLASS, failure);
}

/* A MGMT_REQUEST from @domain at @time (planning/mvp-m2-plan.md). */
static void make_request(be_u32 domain, be_u64 time, be_u64 seq, be_u64 fid,
			 be_u64 target)
{
	make(BE_MVP_RECORD_MGMT_REQUEST, domain, time,
	     BE_MVP_MGMT_REQUEST_WORDS);
	set_word(&record, BE_MVP_MGMT_REQUEST_FID, fid);
	set_word(&record, BE_MVP_MGMT_REQUEST_TARGET, target);
	set_word(&record, BE_MVP_MGMT_REQUEST_SEQ, seq);
}

/* PAUSED or TERMINATED from @domain at @time, naming @by. */
static void make_transition(be_u32 type, be_u32 domain, be_u64 time,
			    be_u64 by, be_u64 exits)
{
	make(type, domain, time, BE_MVP_PAUSED_WORDS);
	set_word(&record, BE_MVP_PAUSED_EXITS, exits);
	set_word(&record, BE_MVP_PAUSED_BY, by);
}

static enum be_mvp_step apply(be_u64 domain)
{
	return be_mvp_control_record(&ctl, domain, &record, &result);
}

static void expect_step(enum be_mvp_step expected, be_u32 ping, be_u32 done,
			enum be_mvp_class failure)
{
	CHECK(apply(record.domain) == expected);
	CHECK(result.step == expected && result.ping == ping &&
	      result.done == done && result.failure == failure);
}

/* A failed loop: every later call returns its class and changes nothing. */
static void expect_failed(enum be_mvp_class failure)
{
	struct be_mvp_control before;

	CHECK(ctl.failed == 1U && ctl.failure == failure);
	CHECK(be_mvp_control_wake(&ctl, START) == failure);
	memcpy(&before, &ctl, sizeof(ctl));
	make(BE_MVP_RECORD_READY, 0U, ALL_ONES, BE_MVP_READY_WORDS);
	CHECK(apply(0U) == STEP_INVALID);
	CHECK(result.step == STEP_INVALID && result.failure == failure);
	CHECK(be_mvp_control_started(&ctl, 0U, 5U) == 0);
	CHECK(be_mvp_control_wake(&ctl, START + 1U) == failure);
	CHECK(memcmp(&before, &ctl, sizeof(ctl)) == 0);
}

static void fresh(void)
{
	be_u32 domain;

	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_channel(&ctl, maps, &channel) == 1);
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		domain_time[domain] = START + 0x100U * (domain + 1U);
		domain_lines[domain] = 0U;
		domain_entered[domain] = 0U;
		domain_denials[domain] = 0U;
		domain_requests[domain] = 0U;
	}
}

static be_u64 tick(be_u32 domain)
{
	domain_time[domain] += 0x10U;
	return domain_time[domain];
}

/* Phases a domain can be driven to before the record under test. */
enum target {
	TARGET_NONE = 0,
	TARGET_STARTED,
	TARGET_READY,
	TARGET_ENTERED,
	TARGET_PINGED,
	TARGET_PONGED,
	TARGET_SHUTDOWN,
	TARGET_COUNT,
};

static void drive(be_u32 domain, enum target target)
{
	if (target >= TARGET_STARTED)
		CHECK(be_mvp_control_started(&ctl, domain,
					     defaults[domain].hart) == 1);
	if (target >= TARGET_READY) {
		make(BE_MVP_RECORD_READY, domain, tick(domain),
		     BE_MVP_READY_WORDS);
		expect_step(BE_MVP_STEP_READY, 0U, 0U, CLASS_NONE);
	}
	if (target >= TARGET_ENTERED) {
		domain_entered[domain] = tick(domain);
		make(BE_MVP_RECORD_ENTERED, domain, domain_entered[domain],
		     BE_MVP_ENTERED_WORDS);
		expect_step(BE_MVP_STEP_ENTERED, 0U, 0U, CLASS_NONE);
	}
	if (target >= TARGET_PINGED) {
		make_line(domain, tick(domain), "first");
		expect_step(BE_MVP_STEP_LINE, 1U, 0U, CLASS_NONE);
		++domain_lines[domain];
	}
	if (target >= TARGET_PONGED) {
		make_pong(domain, tick(domain), 1U);
		expect_step(BE_MVP_STEP_PONG, 0U, 0U, CLASS_NONE);
	}
	if (target >= TARGET_SHUTDOWN) {
		make_shutdown(domain, tick(domain), domain_entered[domain],
			      domain_lines[domain], 0x1000U);
		expect_step(BE_MVP_STEP_SHUTDOWN, 0U,
			    ctl.domain[1U - domain].phase ==
				    BE_MVP_DOMAIN_SHUTDOWN ? 1U : 0U,
			    CLASS_NONE);
	}
	CHECK(ctl.failed == 0U);
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(BE_MVP_HGATP_SV39X4 == BE_U64_C(0x8000000000000000));
	CHECK(BE_MVP_HGATP_VMID_SHIFT == 44U &&
	      BE_MVP_HGATP_VMID_LIMIT == 0x4000U);
	CHECK(BE_MVP_HGATP_ROOT_ALIGN == 0x4000U &&
	      BE_MVP_HGATP_ROOT_LIMIT == BE_U64_C(0x100000000000000));
	CHECK(defaults[0].hart == 1U && defaults[0].vmid == 1U &&
	      defaults[0].root == BE_U64_C(0x102034000));
	CHECK(defaults[1].hart == 2U && defaults[1].vmid == 2U &&
	      defaults[1].root == BE_U64_C(0x10203c000));
	CHECK(BE_MVP_CONTROL_HART == 0U && BE_MVP_HARTS == 8U);
	CHECK(BE_MVP_G0_BLOCK_HPA == BE_U64_C(0x102044000) &&
	      BE_MVP_G1_BLOCK_HPA == BE_U64_C(0x102054000));
	CHECK(BE_MVP_HART_REGION_HPA == BE_U64_C(0x102044000) &&
	      BE_MVP_HART_REGION_BYTES == 0x20000U);
	CHECK(BE_MVP_GENERATION == 1U);
	CHECK(sizeof(struct be_mvp_block_desc) == 14U * WORD);
	CHECK(sizeof(struct be_mvp_state_page) <= BE_MVP_BLOCK_STATE_BYTES);
	CHECK(__builtin_offsetof(struct be_mvp_state_page, desc) == 256U);
	CHECK(BE_MVP_BLOCK_OK == 0 && BE_MVP_DOMAIN_NONE == 0 &&
	      BE_MVP_STEP_INVALID == 0);
	CHECK(BE_MVP_READY_WORDS == 8U && BE_MVP_ENTERED_WORDS == 3U &&
	      BE_MVP_PONG_WORDS == 3U && BE_MVP_SHUTDOWN_WORDS == 15U &&
	      BE_MVP_FAIL_MAX_WORDS == 9U && BE_MVP_DENIAL_WORDS == 12U);
	CHECK(BE_MVP_SHUTDOWN_MGMT == 13U &&
	      BE_MVP_MGMT_REQUEST_WORDS == 3U &&
	      BE_MVP_MGMT_RESULT_WORDS == 2U && BE_MVP_PAUSE_WORDS == 1U &&
	      BE_MVP_TERMINATE_WORDS == 1U && BE_MVP_PAUSED_WORDS == 2U &&
	      BE_MVP_TERMINATED_WORDS == 2U);
	CHECK(BE_MVP_DOMAIN_PAUSED == 6 && BE_MVP_DOMAIN_TERMINATED == 7 &&
	      BE_MVP_STEP_DENIAL == 7 && BE_MVP_STEP_TERMINATED == 11);
}

static void test_hgatp(void)
{
	SCENARIO();
	CHECK(be_mvp_hgatp(1U, BE_U64_C(0x102034000)) == BE_MVP_G0_HGATP);
	CHECK(be_mvp_hgatp(2U, BE_U64_C(0x10203c000)) == BE_MVP_G1_HGATP);
	CHECK(BE_MVP_G0_HGATP == BE_U64_C(0x8000100000102034));
	CHECK(BE_MVP_G1_HGATP == BE_U64_C(0x800020000010203c));
	CHECK(be_mvp_hgatp(0U, BE_U64_C(0x4000)) ==
	      BE_U64_C(0x8000000000000004));
	CHECK(be_mvp_hgatp(0x3fffU, BE_U64_C(0xffffffffffc000)) ==
	      BE_U64_C(0x83fffffffffffffc));
	CHECK(be_mvp_hgatp(0x4000U, BE_U64_C(0x102034000)) == 0U);
	CHECK(be_mvp_hgatp(ALL_ONES, BE_U64_C(0x102034000)) == 0U);
	CHECK(be_mvp_hgatp(1U, BE_U64_C(0x102035000)) == 0U);
	CHECK(be_mvp_hgatp(1U, BE_U64_C(0x102036000)) == 0U);
	CHECK(be_mvp_hgatp(1U, BE_U64_C(0x102034008)) == 0U);
	CHECK(be_mvp_hgatp(1U, BE_U64_C(0x100000000000000)) == 0U);
	CHECK(be_mvp_hgatp(1U, ALL_ONES & ~BE_U64_C(0x3fff)) == 0U);
}

static void expect_bindings(int valid)
{
	CHECK(be_mvp_bindings_valid(bindings, BE_MVP_DOMAINS) == valid);
	memset(&desc, 0x5a, sizeof(desc));
	CHECK(be_mvp_block_fill(&desc, 0U, bindings, BE_MVP_DOMAINS,
				BE_MVP_OUTBOUND_RING_BYTES) ==
	      (valid ? BE_MVP_BLOCK_OK : BE_MVP_BLOCK_BINDING));
	if (!valid)
		CHECK(desc.hart == 0U && desc.hgatp == 0U && desc.block == 0U &&
		      desc.generation == 0U && desc.outbound_bytes == 0U);
	memcpy(bindings, defaults, sizeof(bindings));
}

static void test_bindings(void)
{
	SCENARIO();
	memcpy(bindings, defaults, sizeof(bindings));
	expect_bindings(1);
	CHECK(be_mvp_bindings_valid((const struct be_mvp_binding *)0, 2U) == 0);
	CHECK(be_mvp_bindings_valid(defaults, 0U) == 0);
	CHECK(be_mvp_bindings_valid(defaults, 1U) == 0);
	CHECK(be_mvp_bindings_valid(defaults, 3U) == 0);
	/* Harts: never the control hart, ~0, or shared. */
	bindings[0].hart = BE_MVP_CONTROL_HART;
	expect_bindings(0);
	bindings[1].hart = BE_MVP_CONTROL_HART;
	expect_bindings(0);
	bindings[1].hart = ALL_ONES;
	expect_bindings(0);
	bindings[1].hart = bindings[0].hart;
	expect_bindings(0);
	/* A hart the platform may lack is the firmware's to refuse. */
	bindings[1].hart = BE_MVP_VARIANT_HART_START_HART;
	expect_bindings(1);
	bindings[0].hart = 7U;
	bindings[1].hart = 3U;
	expect_bindings(1);
	bindings[0].hart = ALL_ONES - 1U;
	expect_bindings(1);
	/* VMIDs: nonzero, 14 bits, distinct. */
	bindings[0].vmid = 0U;
	expect_bindings(0);
	bindings[1].vmid = 0x4000U;
	expect_bindings(0);
	bindings[1].vmid = bindings[0].vmid;
	expect_bindings(0);
	bindings[1].vmid = 0x3fffU;
	expect_bindings(1);
	/* Roots: nonzero, aligned, in reach, distinct. */
	bindings[0].root = 0U;
	expect_bindings(0);
	bindings[0].root = BE_U64_C(0x102036000);
	expect_bindings(0);
	bindings[1].root = BE_U64_C(0x100000000000000);
	expect_bindings(0);
	bindings[1].root = bindings[0].root;
	expect_bindings(0);
	bindings[1].root = BE_U64_C(0x4000);
	expect_bindings(1);
}

static void expect_fill(be_u64 domain, be_u64 outbound_bytes)
{
	be_u64 block = BE_MVP_G0_BLOCK_HPA + domain * BE_MVP_BLOCK_BYTES;

	memset(&desc, 0x5a, sizeof(desc));
	CHECK(be_mvp_block_fill(&desc, domain, bindings, BE_MVP_DOMAINS,
				outbound_bytes) == BE_MVP_BLOCK_OK);
	CHECK(be_mvp_block_hpa(domain) == block);
	CHECK(desc.hart == bindings[domain].hart && desc.domain == domain);
	CHECK(desc.hgatp == be_mvp_hgatp(bindings[domain].vmid,
					 bindings[domain].root));
	CHECK(desc.block == block && desc.stack_top == block + 0x2000U);
	CHECK(desc.saved == block + 0x2000U && desc.state == block + 0x3000U);
	CHECK(desc.inbound == block + 0x4000U &&
	      desc.inbound_bytes == 0x1000U);
	CHECK(desc.outbound == block + 0x5000U &&
	      desc.outbound_bytes == outbound_bytes);
	/* The input ring fills its slot (planning/mvp-m7-plan.md, D-1). */
	CHECK(desc.input == block + 0xd000U && desc.input_bytes == 0x1000U);
	CHECK(desc.generation == 0U);
}

static void expect_fill_refused(be_u64 domain, be_u64 outbound_bytes,
				enum be_mvp_block_error error)
{
	memset(&desc, 0x5a, sizeof(desc));
	CHECK(be_mvp_block_fill(&desc, domain, bindings, BE_MVP_DOMAINS,
				outbound_bytes) == error);
	CHECK(desc.hart == 0U && desc.domain == 0U && desc.hgatp == 0U &&
	      desc.block == 0U && desc.stack_top == 0U && desc.saved == 0U &&
	      desc.state == 0U && desc.inbound == 0U &&
	      desc.inbound_bytes == 0U && desc.outbound == 0U &&
	      desc.outbound_bytes == 0U && desc.input == 0U &&
	      desc.input_bytes == 0U && desc.generation == 0U);
}

static void test_block_fill(void)
{
	SCENARIO();
	memcpy(bindings, defaults, sizeof(bindings));
	expect_fill(0U, BE_MVP_OUTBOUND_RING_BYTES);
	CHECK(desc.hgatp == BE_MVP_G0_HGATP && desc.hart == 1U);
	CHECK(desc.block == BE_U64_C(0x102044000));
	expect_fill(1U, BE_MVP_OUTBOUND_RING_BYTES);
	CHECK(desc.hgatp == BE_MVP_G1_HGATP && desc.hart == 2U);
	CHECK(desc.block == BE_U64_C(0x102054000));
	CHECK(desc.outbound == BE_U64_C(0x102059000));
	CHECK(desc.outbound + desc.outbound_bytes ==
	      BE_U64_C(0x102054000) + BE_MVP_INPUT_RING_OFFSET);
	CHECK(desc.input == BE_U64_C(0x102061000) &&
	      desc.input + desc.input_bytes ==
	      BE_U64_C(0x102054000) + BE_MVP_BLOCK_UNUSED_OFFSET);
	/* The ring-full variant's ring, and the smallest. */
	expect_fill(1U, BE_MVP_VARIANT_OUTBOUND_RING_BYTES);
	expect_fill(0U, BE_MVP_RING_MIN_BYTES);
	/* The hart-start variant's hart. */
	bindings[1].hart = BE_MVP_VARIANT_HART_START_HART;
	expect_fill(1U, BE_MVP_OUTBOUND_RING_BYTES);
	CHECK(desc.hart == 9U);
	memcpy(bindings, defaults, sizeof(bindings));

	SCENARIO();
	CHECK(be_mvp_block_fill((struct be_mvp_block_desc *)0, 0U, bindings,
				BE_MVP_DOMAINS, BE_MVP_OUTBOUND_RING_BYTES) ==
	      BE_MVP_BLOCK_NULL);
	memset(&desc, 0x5a, sizeof(desc));
	CHECK(be_mvp_block_fill(&desc, 0U, (const struct be_mvp_binding *)0,
				BE_MVP_DOMAINS, BE_MVP_OUTBOUND_RING_BYTES) ==
	      BE_MVP_BLOCK_NULL);
	CHECK(desc.hart == 0U && desc.generation == 0U);
	CHECK(be_mvp_block_fill(&desc, 0U, bindings, 1U,
				BE_MVP_OUTBOUND_RING_BYTES) ==
	      BE_MVP_BLOCK_BINDING);
	expect_fill_refused(2U, BE_MVP_OUTBOUND_RING_BYTES,
			    BE_MVP_BLOCK_DOMAIN);
	expect_fill_refused(ALL_ONES, BE_MVP_OUTBOUND_RING_BYTES,
			    BE_MVP_BLOCK_DOMAIN);
	expect_fill_refused(0U, 0U, BE_MVP_BLOCK_RINGS);
	expect_fill_refused(0U, 0x100U, BE_MVP_BLOCK_RINGS);
	expect_fill_refused(0U, 0x6000U, BE_MVP_BLOCK_RINGS);
	expect_fill_refused(0U, 0x8008U, BE_MVP_BLOCK_RINGS);
	expect_fill_refused(1U, 0x10000U, BE_MVP_BLOCK_RINGS);
	expect_fill_refused(1U, ALL_ONES, BE_MVP_BLOCK_RINGS);
	CHECK(be_mvp_block_hpa(2U) == 0U && be_mvp_block_hpa(ALL_ONES) == 0U);
}

/* A published descriptor for @domain: filled, then the generation word. */
static void published(be_u64 domain, be_u64 outbound_bytes)
{
	CHECK(be_mvp_block_fill(&desc, domain, bindings, BE_MVP_DOMAINS,
				outbound_bytes) == BE_MVP_BLOCK_OK);
	desc.generation = BE_MVP_GENERATION;
}

static enum be_mvp_block_error check_at(be_u64 hart_id, be_u64 block)
{
	return be_mvp_block_check(&desc, hart_id, block, bindings,
				  BE_MVP_DOMAINS);
}

static enum be_mvp_block_error check_own(void)
{
	return check_at(desc.hart, desc.block);
}

static void test_block_check(void)
{
	be_u64 domain;

	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		be_u64 block = be_mvp_block_hpa(domain);
		be_u64 other = be_mvp_block_hpa(1U - domain);

		SCENARIO();
		memcpy(bindings, defaults, sizeof(bindings));
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		CHECK(check_at(domain + 1U, block) == BE_MVP_BLOCK_OK);
		/* Before the barrier the word is 0; any other is refused. */
		desc.generation = 0U;
		CHECK(check_own() == BE_MVP_BLOCK_GENERATION);
		desc.generation = 2U;
		CHECK(check_own() == BE_MVP_BLOCK_GENERATION);
		desc.generation = ALL_ONES;
		CHECK(check_own() == BE_MVP_BLOCK_GENERATION);
		/* Every later error waits for the generation word. */
		desc.hart = 6U;
		desc.hgatp = 0U;
		CHECK(check_own() == BE_MVP_BLOCK_GENERATION);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.domain = 2U;
		CHECK(check_own() == BE_MVP_BLOCK_DOMAIN);
		desc.domain = ALL_ONES;
		CHECK(check_own() == BE_MVP_BLOCK_DOMAIN);
		/* The hart: the binding's, and the hart that was started. */
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		CHECK(check_at(domain + 2U, block) == BE_MVP_BLOCK_HART);
		CHECK(check_at(BE_MVP_CONTROL_HART, block) ==
		      BE_MVP_BLOCK_HART);
		desc.hart = 6U;
		CHECK(check_at(6U, block) == BE_MVP_BLOCK_HART);
		desc.hart = defaults[1U - domain].hart;
		CHECK(check_at(desc.hart, block) == BE_MVP_BLOCK_HART);
		/* The other domain's descriptor, at the other hart's entry. */
		published(1U - domain, BE_MVP_OUTBOUND_RING_BYTES);
		CHECK(check_at(domain + 1U, block) == BE_MVP_BLOCK_HART);
		CHECK(check_at(desc.hart, other) == BE_MVP_BLOCK_OK);
		/* The block: the domain's, and a1. */
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		CHECK(check_at(desc.hart, other) == BE_MVP_BLOCK_ADDRESS);
		CHECK(check_at(desc.hart, block + 0x1000U) ==
		      BE_MVP_BLOCK_ADDRESS);
		desc.block = other;
		CHECK(check_at(desc.hart, other) == BE_MVP_BLOCK_ADDRESS);
		CHECK(check_at(desc.hart, block) == BE_MVP_BLOCK_ADDRESS);
		/* Each page and ring at its offset. */
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.stack_top += 8U;
		CHECK(check_own() == BE_MVP_BLOCK_OFFSETS);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.stack_top = block + BE_MVP_BLOCK_STACK_BYTES - 0x1000U;
		CHECK(check_own() == BE_MVP_BLOCK_OFFSETS);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.saved = block + BE_MVP_BLOCK_STATE_OFFSET;
		CHECK(check_own() == BE_MVP_BLOCK_OFFSETS);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.state = other + BE_MVP_BLOCK_STATE_OFFSET;
		CHECK(check_own() == BE_MVP_BLOCK_OFFSETS);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.inbound = desc.outbound;
		CHECK(check_own() == BE_MVP_BLOCK_OFFSETS);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.outbound -= 0x1000U;
		CHECK(check_own() == BE_MVP_BLOCK_OFFSETS);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.input += 0x1000U;
		CHECK(check_own() == BE_MVP_BLOCK_OFFSETS);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.input = desc.inbound;
		CHECK(check_own() == BE_MVP_BLOCK_OFFSETS);
		/* Rings: powers of two of at least 512 that fit their slots. */
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.inbound_bytes = 0x800U;
		CHECK(check_own() == BE_MVP_BLOCK_OK);
		desc.inbound_bytes = 0x2000U;
		CHECK(check_own() == BE_MVP_BLOCK_RINGS);
		desc.inbound_bytes = 0xc00U;
		CHECK(check_own() == BE_MVP_BLOCK_RINGS);
		desc.inbound_bytes = 0x100U;
		CHECK(check_own() == BE_MVP_BLOCK_RINGS);
		desc.inbound_bytes = 0U;
		CHECK(check_own() == BE_MVP_BLOCK_RINGS);
		/* The input ring is exactly its slot. */
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.input_bytes = 0x800U;
		CHECK(check_own() == BE_MVP_BLOCK_RINGS);
		desc.input_bytes = 0x2000U;
		CHECK(check_own() == BE_MVP_BLOCK_RINGS);
		desc.input_bytes = 0U;
		CHECK(check_own() == BE_MVP_BLOCK_RINGS);
		published(domain, BE_MVP_VARIANT_OUTBOUND_RING_BYTES);
		CHECK(check_own() == BE_MVP_BLOCK_OK);
		desc.outbound_bytes = 0x10000U;
		CHECK(check_own() == BE_MVP_BLOCK_RINGS);
		desc.outbound_bytes = 0x7000U;
		CHECK(check_own() == BE_MVP_BLOCK_RINGS);
		desc.outbound_bytes = ALL_ONES;
		CHECK(check_own() == BE_MVP_BLOCK_RINGS);
		/* hgatp: Sv39x4 with the binding's VMID and root. */
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.hgatp = be_mvp_hgatp(defaults[1U - domain].vmid,
					  defaults[1U - domain].root);
		CHECK(check_own() == BE_MVP_BLOCK_HGATP);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.hgatp ^= BE_U64_C(1) << 60;
		CHECK(check_own() == BE_MVP_BLOCK_HGATP);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.hgatp ^= BE_U64_C(4) << BE_MVP_HGATP_VMID_SHIFT;
		CHECK(check_own() == BE_MVP_BLOCK_HGATP);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.hgatp += 4U;
		CHECK(check_own() == BE_MVP_BLOCK_HGATP);
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		desc.hgatp = 0U;
		CHECK(check_own() == BE_MVP_BLOCK_HGATP);
		/* The bindings themselves, and absent pointers. */
		published(domain, BE_MVP_OUTBOUND_RING_BYTES);
		CHECK(be_mvp_block_check(&desc, desc.hart, desc.block, bindings,
					 1U) == BE_MVP_BLOCK_BINDING);
		bindings[domain].vmid = bindings[1U - domain].vmid;
		CHECK(check_own() == BE_MVP_BLOCK_BINDING);
		memcpy(bindings, defaults, sizeof(bindings));
		CHECK(be_mvp_block_check((const struct be_mvp_block_desc *)0,
					 desc.hart, desc.block, bindings,
					 BE_MVP_DOMAINS) == BE_MVP_BLOCK_NULL);
		CHECK(be_mvp_block_check(&desc, desc.hart, desc.block,
					 (const struct be_mvp_binding *)0,
					 BE_MVP_DOMAINS) == BE_MVP_BLOCK_NULL);
		CHECK(check_own() == BE_MVP_BLOCK_OK);
	}

	/* The hart-start variant: hart 9 runs G1 if the firmware starts it. */
	SCENARIO();
	memcpy(bindings, defaults, sizeof(bindings));
	bindings[1].hart = BE_MVP_VARIANT_HART_START_HART;
	published(1U, BE_MVP_OUTBOUND_RING_BYTES);
	CHECK(check_at(9U, BE_MVP_G1_BLOCK_HPA) == BE_MVP_BLOCK_OK);
	CHECK(check_at(2U, BE_MVP_G1_BLOCK_HPA) == BE_MVP_BLOCK_HART);
	/* A descriptor filled for one binding, checked against another. */
	memcpy(bindings, defaults, sizeof(bindings));
	CHECK(check_at(9U, BE_MVP_G1_BLOCK_HPA) == BE_MVP_BLOCK_HART);
	bindings[1].root = BE_U64_C(0x102040000);
	published(1U, BE_MVP_OUTBOUND_RING_BYTES);
	memcpy(bindings, defaults, sizeof(bindings));
	CHECK(check_own() == BE_MVP_BLOCK_HGATP);
}

/* The state page: the four index lines, then the descriptor. */
static void test_state_page(void)
{
	static struct be_mvp_state_page page __attribute__((aligned(4096)));
	static be_u8 inbound[BE_MVP_INBOUND_RING_BYTES];
	struct be_mvp_ring hart0;
	struct be_mvp_ring hart;
	const char *base = (const char *)&page;

	SCENARIO();
	CHECK((const char *)&page.inbound_head == base);
	CHECK((const char *)&page.inbound_tail == base + 64);
	CHECK((const char *)&page.outbound_head == base + 128);
	CHECK((const char *)&page.outbound_tail == base + 192);
	CHECK((const char *)&page.desc == base + 256);
	CHECK((be_u64)((const char *)(&page + 1) - base) <= 4096U);
	be_mvp_ring_reset(&page.inbound_head, &page.inbound_tail);
	be_mvp_ring_reset(&page.outbound_head, &page.outbound_tail);
	CHECK(be_mvp_ring_init(&hart0, inbound, BE_MVP_INBOUND_RING_BYTES,
			       &page.inbound_head, &page.inbound_tail,
			       BE_MVP_RECORDS_INBOUND, 0U,
			       BE_MVP_RING_WRITER) == 1);
	CHECK(be_mvp_ring_init(&hart, inbound, BE_MVP_INBOUND_RING_BYTES,
			       &page.inbound_head, &page.inbound_tail,
			       BE_MVP_RECORDS_INBOUND, 0U,
			       BE_MVP_RING_READER) == 1);
	CHECK(be_mvp_ring_post(&hart0, BE_MVP_RECORD_PING, 7U,
			       (const be_u8 *)0, 0U) == 1);
	CHECK(be_mvp_ring_publish(&hart0) == 1);
	CHECK(page.inbound_head.value == 16U && page.inbound_tail.value == 0U);
	CHECK(page.outbound_head.value == 0U &&
	      page.outbound_tail.value == 0U);
	CHECK(be_mvp_ring_acquire(&hart) == 16U);
	CHECK(be_mvp_ring_take(&hart, &record) == BE_MVP_RING_RECORD);
	CHECK(be_mvp_ring_release(&hart) == 1);
	CHECK(page.inbound_tail.value == 16U);
	/* The descriptor in place, published and checked. */
	memcpy(bindings, defaults, sizeof(bindings));
	CHECK(be_mvp_block_fill(&page.desc, 0U, bindings, BE_MVP_DOMAINS,
				BE_MVP_OUTBOUND_RING_BYTES) ==
	      BE_MVP_BLOCK_OK);
	page.desc.generation = BE_MVP_GENERATION;
	CHECK(be_mvp_block_check(&page.desc, 1U, BE_MVP_G0_BLOCK_HPA,
				 bindings, BE_MVP_DOMAINS) == BE_MVP_BLOCK_OK);
	CHECK(page.inbound_head.value == 16U);
}

static void test_control_init(void)
{
	SCENARIO();
	memset(&ctl, 0x5a, sizeof(ctl));
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(ctl.start == START && ctl.budget == BUDGET &&
	      ctl.ready_ticks == READY_WAIT);
	CHECK(ctl.records == 0U && ctl.wakes == 0U && ctl.idle_ticks == 0U);
	CHECK(ctl.failed == 0U && ctl.done == 0U && ctl.failure == CLASS_NONE);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_NONE &&
	      ctl.domain[1].phase == BE_MVP_DOMAIN_NONE);
	CHECK(ctl.domain[0].pinged == 0U && ctl.domain[1].ponged == 0U &&
	      ctl.domain[0].lines == 0U && ctl.domain[1].records == 0U &&
	      ctl.domain[0].last == 0U && ctl.domain[1].ring_peak == 0U);
	CHECK(ctl.domain[0].denials == 0U && ctl.domain[1].denials == 0U &&
	      ctl.sealed == 0U && ctl.window_bytes[0] == 0U &&
	      ctl.channel.bytes == 0U);
	/* The run-timeout variant's budget is below the READY wait. */
	be_mvp_control_init(&ctl, START, BE_MVP_VARIANT_RUN_BUDGET,
			    READY_WAIT);
	CHECK(ctl.failed == 0U && ctl.budget == 0x100000U);
	be_mvp_control_init(&ctl, START, 0U, READY_WAIT);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	be_mvp_control_init(&ctl, START, BUDGET, 0U);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	be_mvp_control_init((struct be_mvp_control *)0, START, BUDGET,
			    READY_WAIT);
}

static void test_started(void)
{
	SCENARIO();
	fresh();
	CHECK(be_mvp_control_started(&ctl, 0U, 1U) == 1);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_STARTED &&
	      ctl.domain[0].hart == 1U);
	CHECK(ctl.domain[1].phase == BE_MVP_DOMAIN_NONE);
	CHECK(be_mvp_control_started(&ctl, 1U, 2U) == 1);
	CHECK(ctl.domain[1].phase == BE_MVP_DOMAIN_STARTED &&
	      ctl.domain[1].hart == 2U && ctl.failed == 0U);
	/* Either order; any hart but the control hart. */
	fresh();
	CHECK(be_mvp_control_started(&ctl, 1U, 9U) == 1);
	CHECK(be_mvp_control_started(&ctl, 0U, 7U) == 1);
	CHECK(ctl.failed == 0U);

	SCENARIO();
	fresh();
	CHECK(be_mvp_control_started(&ctl, 0U, 1U) == 1);
	CHECK(be_mvp_control_started(&ctl, 0U, 1U) == 0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	fresh();
	CHECK(be_mvp_control_started(&ctl, 0U, 1U) == 1);
	CHECK(be_mvp_control_started(&ctl, 1U, 1U) == 0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	fresh();
	CHECK(be_mvp_control_started(&ctl, 1U, BE_MVP_CONTROL_HART) == 0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	fresh();
	CHECK(be_mvp_control_started(&ctl, 2U, 3U) == 0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	CHECK(be_mvp_control_started((struct be_mvp_control *)0, 0U, 1U) == 0);
}

/* The two-guest run: both domains through every phase, interleaved. */
static void test_protocol(void)
{
	be_u64 overlap = ALL_ONES;

	SCENARIO();
	fresh();
	drive(0U, TARGET_STARTED);
	drive(1U, TARGET_STARTED);
	CHECK(be_mvp_control_wake(&ctl, START + 1U) == CLASS_NONE);
	make(BE_MVP_RECORD_READY, 1U, 0x500U, BE_MVP_READY_WORDS);
	expect_step(BE_MVP_STEP_READY, 0U, 0U, CLASS_NONE);
	make(BE_MVP_RECORD_READY, 0U, 0x400U, BE_MVP_READY_WORDS);
	expect_step(BE_MVP_STEP_READY, 0U, 0U, CLASS_NONE);
	make(BE_MVP_RECORD_ENTERED, 0U, 0x1000U, BE_MVP_ENTERED_WORDS);
	expect_step(BE_MVP_STEP_ENTERED, 0U, 0U, CLASS_NONE);
	CHECK(ctl.domain[0].entered == 0x1000U);
	make(BE_MVP_RECORD_ENTERED, 1U, 0x1100U, BE_MVP_ENTERED_WORDS);
	expect_step(BE_MVP_STEP_ENTERED, 0U, 0U, CLASS_NONE);
	CHECK(ctl.domain[1].phase == BE_MVP_DOMAIN_ENTERED);
	/* The first LINE of each domain asks for its one PING. */
	make_line(0U, 0x2000U, "[    0.000000] Linux version 7.2.0");
	expect_step(BE_MVP_STEP_LINE, 1U, 0U, CLASS_NONE);
	make_line(1U, 0x2010U, "[    0.000000] Linux version 7.2.0");
	expect_step(BE_MVP_STEP_LINE, 1U, 0U, CLASS_NONE);
	make_line(0U, 0x2020U, "");
	expect_step(BE_MVP_STEP_LINE, 0U, 0U, CLASS_NONE);
	CHECK(ctl.domain[0].pinged == 1U && ctl.domain[0].ponged == 0U);
	make_pong(0U, 0x2030U, 1U);
	expect_step(BE_MVP_STEP_PONG, 0U, 0U, CLASS_NONE);
	make_line(1U, 0x2040U, "MVPINIT 01 START guest=1 pid=1");
	expect_step(BE_MVP_STEP_LINE, 0U, 0U, CLASS_NONE);
	make_pong(1U, 0x2050U, 1U);
	expect_step(BE_MVP_STEP_PONG, 0U, 0U, CLASS_NONE);
	CHECK(ctl.domain[0].ponged == 1U && ctl.domain[1].ponged == 1U);
	make_line(0U, 0x2060U, "MVPINIT 06 POWER_OFF");
	expect_step(BE_MVP_STEP_LINE, 0U, 0U, CLASS_NONE);
	make_shutdown(0U, 0x9000U, 0x1000U, 3U, 0x2a8U);
	expect_step(BE_MVP_STEP_SHUTDOWN, 0U, 0U, CLASS_NONE);
	CHECK(ctl.done == 0U && ctl.domain[0].ring_peak == 0x2a8U);
	CHECK(be_mvp_control_overlap(&ctl, &overlap) == 0 && overlap == 0U);
	CHECK(be_mvp_control_wake(&ctl, 0x9001U) == CLASS_NONE);
	make_line(1U, 0x9100U, "[    1.5] reboot: Power down");
	expect_step(BE_MVP_STEP_LINE, 0U, 0U, CLASS_NONE);
	make_shutdown(1U, 0xa000U, 0x1100U, 3U, 0x1f0U);
	expect_step(BE_MVP_STEP_SHUTDOWN, 0U, 1U, CLASS_NONE);
	CHECK(ctl.done == 1U && ctl.failed == 0U);
	/* Counters: records per domain and in all, lines, peaks, times. */
	CHECK(ctl.records == 14U);
	CHECK(ctl.domain[0].records == 7U && ctl.domain[1].records == 7U);
	CHECK(ctl.domain[0].lines == 3U && ctl.domain[1].lines == 3U);
	CHECK(ctl.domain[0].shutdown == 0x9000U &&
	      ctl.domain[1].shutdown == 0xa000U);
	CHECK(ctl.domain[1].ring_peak == 0x1f0U && ctl.wakes == 2U);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_SHUTDOWN &&
	      ctl.domain[1].phase == BE_MVP_DOMAIN_SHUTDOWN);
	/* [0x1000, 0x9000] and [0x1100, 0xa000]: 0x7f00 of 0x8000. */
	CHECK(be_mvp_control_overlap(&ctl, &overlap) == 1);
	CHECK(overlap == 0x7f00U);
	/* Done: no more records or wakes. */
	make_line(0U, 0xb000U, "late");
	CHECK(apply(0U) == STEP_INVALID && result.failure == CLASS_RING);
	expect_failed(CLASS_RING);
	CHECK(be_mvp_control_overlap(&ctl, &overlap) == 0 && overlap == 0U);

	SCENARIO();
	fresh();
	drive(0U, TARGET_SHUTDOWN);
	drive(1U, TARGET_SHUTDOWN);
	CHECK(ctl.done == 1U);
	CHECK(be_mvp_control_wake(&ctl, START + 1U) ==
	      BE_MVP_CLASS_EXCEPTION);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
}

/* The record under test, well formed for its type, from domain 0. */
static void make_typed(be_u32 type)
{
	be_u64 time = tick(0U);

	switch (type) {
	case BE_MVP_RECORD_READY:
		make(type, 0U, time, BE_MVP_READY_WORDS);
		break;
	case BE_MVP_RECORD_ENTERED:
		make(type, 0U, time, BE_MVP_ENTERED_WORDS);
		break;
	case BE_MVP_RECORD_LINE:
		make_line(0U, time, "x");
		break;
	case BE_MVP_RECORD_PONG:
		make_pong(0U, time, 1U);
		break;
	case BE_MVP_RECORD_SHUTDOWN:
		make_shutdown(0U, time, domain_entered[0], domain_lines[0],
			      0x100U);
		break;
	case BE_MVP_RECORD_FAIL:
		make_fail(0U, time, BE_MVP_CLASS_CONTROLS, 2U);
		break;
	case BE_MVP_RECORD_DENIAL:
		make_denial(0U, time, ctl.domain[0].denials + 1U, LOAD,
			    UNMAPPED, BESIDE_GPA);
		break;
	case BE_MVP_RECORD_MGMT_REQUEST:
		make_request(0U, time, ctl.domain[0].requests + 1U,
			     BE_MVP_SBI_MGMT_PAUSE, 1U);
		break;
	case BE_MVP_RECORD_PAUSED:
	case BE_MVP_RECORD_TERMINATED:
		make_transition(type, 0U, time, 1U, 0x40U);
		break;
	default:
		make(type, 0U, time, 0U);
		break;
	}
}

struct expected {
	enum be_mvp_step step;
	enum be_mvp_class failure;
	be_u32 ping;
};

#define RING_	{ BE_MVP_STEP_INVALID, BE_MVP_CLASS_RING, 0U }
#define IPI_	{ BE_MVP_STEP_INVALID, BE_MVP_CLASS_IPI, 0U }
#define FAIL_	{ BE_MVP_STEP_FAIL, BE_MVP_CLASS_CONTROLS, 0U }
#define OK_(s)	{ BE_MVP_STEP_##s, BE_MVP_CLASS_NONE, 0U }
#define ALL_RING_ { RING_, RING_, RING_, RING_, RING_, RING_, RING_ }

/*
 * The management records come last: without be_mvp_control_mgmt() every
 * one is refused as ring, in every phase (planning/mvp-m2-plan.md).
 */
static const be_u32 table_types[] = {
	BE_MVP_RECORD_NONE, BE_MVP_RECORD_READY, BE_MVP_RECORD_ENTERED,
	BE_MVP_RECORD_LINE, BE_MVP_RECORD_PONG, BE_MVP_RECORD_SHUTDOWN,
	BE_MVP_RECORD_FAIL, BE_MVP_RECORD_PING, BE_MVP_RECORD_ACK,
	BE_MVP_RECORD_DENIAL, BE_MVP_RECORD_COUNT, 0xffU,
	BE_MVP_RECORD_MGMT_REQUEST, BE_MVP_RECORD_PAUSED,
	BE_MVP_RECORD_TERMINATED, BE_MVP_RECORD_MGMT_RESULT,
	BE_MVP_RECORD_PAUSE, BE_MVP_RECORD_TERMINATE,
};

/* Every record type in every phase of the domain it comes from. */
static const struct expected table[BE_ARRAY_SIZE(table_types)]
				  [TARGET_COUNT] = {
	ALL_RING_,
	{ RING_, OK_(READY), RING_, RING_, RING_, RING_, RING_ },
	{ RING_, RING_, OK_(ENTERED), RING_, RING_, RING_, RING_ },
	{ RING_, RING_, RING_, { BE_MVP_STEP_LINE, BE_MVP_CLASS_NONE, 1U },
	  OK_(LINE), OK_(LINE), RING_ },
	{ RING_, RING_, RING_, IPI_, OK_(PONG), IPI_, RING_ },
	{ RING_, RING_, RING_, IPI_, IPI_, OK_(SHUTDOWN), RING_ },
	{ RING_, FAIL_, FAIL_, FAIL_, FAIL_, FAIL_, RING_ },
	ALL_RING_,
	ALL_RING_,
	{ RING_, RING_, RING_, OK_(DENIAL), OK_(DENIAL), OK_(DENIAL), RING_ },
	ALL_RING_,
	ALL_RING_,
	ALL_RING_,
	ALL_RING_,
	ALL_RING_,
	ALL_RING_,
	ALL_RING_,
	ALL_RING_,
};

static void test_order(void)
{
	be_size type;
	unsigned int target;

	for (type = 0U; type < BE_ARRAY_SIZE(table_types); ++type) {
		for (target = 0U; target < TARGET_COUNT; ++target) {
			const struct expected *want = &table[type][target];
			be_u64 records;

			SCENARIO();
			fresh();
			drive(0U, (enum target)target);
			records = ctl.records;
			make_typed(table_types[type]);
			expect_step(want->step, want->ping, 0U, want->failure);
			if (want->step == BE_MVP_STEP_INVALID ||
			    want->step == BE_MVP_STEP_FAIL) {
				CHECK(ctl.records == records +
				      (want->step == BE_MVP_STEP_FAIL ? 1U :
				       0U));
				expect_failed(want->failure);
				continue;
			}
			CHECK(ctl.failed == 0U && ctl.records == records + 1U);
			CHECK(ctl.domain[0].last == record.time);
			CHECK(ctl.domain[1].phase == BE_MVP_DOMAIN_NONE);
		}
	}
	/* The phase each accepted record leads to. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_STARTED);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_STARTED);
	make_typed(BE_MVP_RECORD_READY);
	CHECK(apply(0U) == BE_MVP_STEP_READY);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_READY);
	make_typed(BE_MVP_RECORD_ENTERED);
	CHECK(apply(0U) == BE_MVP_STEP_ENTERED);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_ENTERED &&
	      ctl.domain[0].entered == record.time);
	domain_entered[0] = record.time;
	make_typed(BE_MVP_RECORD_LINE);
	CHECK(apply(0U) == BE_MVP_STEP_LINE && result.ping == 1U);
	CHECK(ctl.domain[0].pinged == 1U && ctl.domain[0].lines == 1U);
	domain_lines[0] = 1U;
	make_typed(BE_MVP_RECORD_PONG);
	CHECK(apply(0U) == BE_MVP_STEP_PONG && ctl.domain[0].ponged == 1U);
	make_typed(BE_MVP_RECORD_DENIAL);
	CHECK(apply(0U) == BE_MVP_STEP_DENIAL && ctl.domain[0].denials == 1U);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_ENTERED);
	domain_denials[0] = 1U;
	make_typed(BE_MVP_RECORD_SHUTDOWN);
	CHECK(apply(0U) == BE_MVP_STEP_SHUTDOWN && result.done == 0U);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_SHUTDOWN &&
	      ctl.domain[0].shutdown == record.time &&
	      ctl.domain[0].ring_peak == 0x100U);

	/* A record from one domain's ring that names the other. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_STARTED);
	drive(1U, TARGET_STARTED);
	make(BE_MVP_RECORD_READY, 1U, tick(1U), BE_MVP_READY_WORDS);
	CHECK(apply(0U) == STEP_INVALID && result.failure == CLASS_RING);
	expect_failed(CLASS_RING);
	/* Absent inputs and a domain with no ring. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_STARTED);
	CHECK(be_mvp_control_record(&ctl, 0U,
				    (const struct be_mvp_record *)0,
				    &result) == STEP_INVALID);
	CHECK(result.failure == BE_MVP_CLASS_EXCEPTION);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	fresh();
	drive(0U, TARGET_STARTED);
	make(BE_MVP_RECORD_READY, 0U, tick(0U), BE_MVP_READY_WORDS);
	CHECK(apply(2U) == STEP_INVALID);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	fresh();
	drive(0U, TARGET_STARTED);
	make(BE_MVP_RECORD_READY, 0U, tick(0U), BE_MVP_READY_WORDS);
	CHECK(be_mvp_control_record(&ctl, 0U, &record,
				    (struct be_mvp_step_result *)0) ==
	      STEP_INVALID);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	memset(&result, 0x5a, sizeof(result));
	CHECK(be_mvp_control_record((struct be_mvp_control *)0, 0U, &record,
				    &result) == STEP_INVALID);
	CHECK(result.step == STEP_INVALID && result.ping == 0U &&
	      result.done == 0U && result.failure == BE_MVP_CLASS_EXCEPTION);
	CHECK(be_mvp_control_record((struct be_mvp_control *)0, 0U, &record,
				    (struct be_mvp_step_result *)0) ==
	      STEP_INVALID);
}

/* The record under test from domain 0: its step, then the loop's. */
static void expect_at(enum be_mvp_step step, enum be_mvp_class failure)
{
	CHECK(apply(0U) == step);
	CHECK(result.step == step && result.failure == failure);
	if (step == STEP_INVALID || step == BE_MVP_STEP_FAIL)
		expect_failed(failure);
	else
		CHECK(ctl.failed == 0U);
}

static void at(enum target target)
{
	SCENARIO();
	fresh();
	drive(0U, target);
}

static void test_payloads(void)
{
	be_u64 index;

	/* Word payloads: exactly their type's size. */
	at(TARGET_STARTED);
	make(BE_MVP_RECORD_READY, 0U, tick(0U), BE_MVP_READY_WORDS - 1U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_STARTED);
	make(BE_MVP_RECORD_READY, 0U, tick(0U), BE_MVP_READY_WORDS + 1U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_READY);
	make(BE_MVP_RECORD_ENTERED, 0U, tick(0U), 2U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_READY);
	make(BE_MVP_RECORD_ENTERED, 0U, tick(0U), 4U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_READY);
	make(BE_MVP_RECORD_ENTERED, 0U, tick(0U), 3U);
	record.length = 23U;
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_PINGED);
	make(BE_MVP_RECORD_PONG, 0U, tick(0U), 2U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_PINGED);
	make(BE_MVP_RECORD_PONG, 0U, tick(0U), 4U);
	expect_at(STEP_INVALID, CLASS_RING);
	/* PONG's spv is 0 or 1; the checker requires 1. */
	at(TARGET_PINGED);
	make_pong(0U, tick(0U), 0U);
	expect_at(BE_MVP_STEP_PONG, CLASS_NONE);
	at(TARGET_PINGED);
	make_pong(0U, tick(0U), 2U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_PINGED);
	make_pong(0U, tick(0U), ALL_ONES);
	expect_at(STEP_INVALID, CLASS_RING);
	/* SHUTDOWN: its size, then the ENTERED time and the lines drained. */
	at(TARGET_PONGED);
	make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0], 0U);
	record.length -= WORD;
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_PONGED);
	make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0], 0U);
	record.length += WORD;
	expect_at(STEP_INVALID, CLASS_RING);
	/* DENIAL: exactly twelve words. */
	at(TARGET_ENTERED);
	make_denial(0U, tick(0U), 1U, LOAD, UNMAPPED, BESIDE_GPA);
	record.length -= WORD;
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_denial(0U, tick(0U), 1U, LOAD, UNMAPPED, BESIDE_GPA);
	record.length += WORD;
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_denial(0U, tick(0U), 1U, LOAD, UNMAPPED, BESIDE_GPA);
	record.length -= 1U;
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_PONGED);
	make_shutdown(0U, tick(0U), domain_entered[0] + 1U, domain_lines[0],
		      0U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_PONGED);
	make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0] + 1U,
		      0U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_PONGED);
	make_shutdown(0U, tick(0U), domain_entered[0], 0U, 0U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_PONGED);
	make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0],
		      ALL_ONES);
	expect_at(BE_MVP_STEP_SHUTDOWN, CLASS_NONE);
	CHECK(ctl.domain[0].ring_peak == ALL_ONES);
	/* FAIL: the class word and at most eight detail words. */
	at(TARGET_ENTERED);
	make(BE_MVP_RECORD_FAIL, 0U, tick(0U), 0U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_fail(0U, tick(0U), BE_MVP_CLASS_IPI, 9U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_fail(0U, tick(0U), BE_MVP_CLASS_IPI, 1U);
	record.length = 12U;
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_fail(0U, tick(0U), BE_MVP_CLASS_NONE, 0U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_fail(0U, tick(0U), BE_MVP_CLASS_COUNT, 0U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_fail(0U, tick(0U), ALL_ONES, 0U);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_fail(0U, tick(0U), BE_MVP_CLASS_IPI, 0U);
	expect_at(BE_MVP_STEP_FAIL, BE_MVP_CLASS_IPI);
	at(TARGET_ENTERED);
	make_fail(0U, tick(0U), BE_MVP_CLASS_EXIT_BUDGET, 8U);
	expect_at(BE_MVP_STEP_FAIL, BE_MVP_CLASS_EXIT_BUDGET);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_FAILED);
	/* LINE: at most 256 printable bytes; an empty line is a line. */
	at(TARGET_ENTERED);
	make_line(0U, tick(0U), "");
	expect_at(BE_MVP_STEP_LINE, CLASS_NONE);
	at(TARGET_ENTERED);
	make_line(0U, tick(0U), "");
	for (index = 0U; index < BE_MVP_CONSOLE_LINE_BYTES; ++index)
		record.payload[index] = (be_u8)(0x20U + index % 0x5fU);
	record.length = BE_MVP_CONSOLE_LINE_BYTES;
	expect_at(BE_MVP_STEP_LINE, CLASS_NONE);
	at(TARGET_ENTERED);
	make_line(0U, tick(0U), "");
	memset(record.payload, 'a', sizeof(record.payload));
	record.length = BE_MVP_CONSOLE_LINE_BYTES + 1U;
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_line(0U, tick(0U), "");
	record.length = ALL_ONES;
	expect_at(STEP_INVALID, CLASS_RING);
}

static void line_byte(be_u8 byte, enum be_mvp_step step)
{
	at(TARGET_ENTERED);
	make_line(0U, tick(0U), "ab_d");
	record.payload[2] = byte;
	expect_at(step, step == STEP_INVALID ? CLASS_RING : CLASS_NONE);
}

static void test_line_bytes(void)
{
	line_byte(0x20U, BE_MVP_STEP_LINE);
	line_byte(0x7eU, BE_MVP_STEP_LINE);
	line_byte('?', BE_MVP_STEP_LINE);
	line_byte(0x00U, STEP_INVALID);
	line_byte(0x09U, STEP_INVALID);
	line_byte(0x0aU, STEP_INVALID);
	line_byte(0x0dU, STEP_INVALID);
	line_byte(0x1fU, STEP_INVALID);
	line_byte(0x7fU, STEP_INVALID);
	line_byte(0x80U, STEP_INVALID);
	line_byte(0xffU, STEP_INVALID);
}

static void test_times(void)
{
	/* Within a domain, a record never goes back in time. */
	at(TARGET_ENTERED);
	make_line(0U, domain_time[0] - 1U, "late");
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_line(0U, domain_time[0], "same time");
	expect_at(BE_MVP_STEP_LINE, CLASS_NONE);
	make_line(0U, domain_time[0], "same time again");
	CHECK(apply(0U) == BE_MVP_STEP_LINE && result.ping == 0U);
	at(TARGET_PONGED);
	make_fail(0U, 0U, BE_MVP_CLASS_IPI, 0U);
	expect_at(STEP_INVALID, CLASS_RING);
	/* Across domains, drain order sets no time order. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_PONGED);
	drive(1U, TARGET_STARTED);
	make(BE_MVP_RECORD_READY, 1U, START, BE_MVP_READY_WORDS);
	CHECK(START < ctl.domain[0].last);
	expect_step(BE_MVP_STEP_READY, 0U, 0U, CLASS_NONE);
	/* A domain that shuts down at its entry time: done, no overlap. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_SHUTDOWN);
	drive(1U, TARGET_STARTED);
	make(BE_MVP_RECORD_READY, 1U, 0x7000U, BE_MVP_READY_WORDS);
	expect_step(BE_MVP_STEP_READY, 0U, 0U, CLASS_NONE);
	make(BE_MVP_RECORD_ENTERED, 1U, 0x7000U, BE_MVP_ENTERED_WORDS);
	expect_step(BE_MVP_STEP_ENTERED, 0U, 0U, CLASS_NONE);
	make_line(1U, 0x7000U, "");
	expect_step(BE_MVP_STEP_LINE, 1U, 0U, CLASS_NONE);
	make_pong(1U, 0x7000U, 1U);
	expect_step(BE_MVP_STEP_PONG, 0U, 0U, CLASS_NONE);
	make_shutdown(1U, 0x7000U, 0x7000U, 1U, 0U);
	expect_step(BE_MVP_STEP_SHUTDOWN, 0U, 1U, CLASS_NONE);
	{
		be_u64 overlap = ALL_ONES;

		CHECK(be_mvp_control_overlap(&ctl, &overlap) == 0);
		CHECK(overlap == 0U);
	}
}

static void test_fail_paths(void)
{
	/* A domain hart fails before READY: its arming failed. */
	at(TARGET_STARTED);
	make_fail(0U, tick(0U), BE_MVP_CLASS_SSTC, 2U);
	expect_step(BE_MVP_STEP_FAIL, 0U, 0U, BE_MVP_CLASS_SSTC);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_FAILED &&
	      ctl.domain[0].records == 1U);
	expect_failed(BE_MVP_CLASS_SSTC);
	/* G1 fails while G0 runs: the run ends; G0's records are refused. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_PONGED);
	drive(1U, TARGET_ENTERED);
	make_fail(1U, tick(1U), BE_MVP_CLASS_GUEST_REBOOT, 1U);
	expect_step(BE_MVP_STEP_FAIL, 0U, 0U, BE_MVP_CLASS_GUEST_REBOOT);
	make_line(0U, tick(0U), "still running");
	CHECK(apply(0U) == STEP_INVALID);
	CHECK(result.failure == BE_MVP_CLASS_GUEST_REBOOT);
	make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0], 0U);
	CHECK(apply(0U) == STEP_INVALID);
	CHECK(result.failure == BE_MVP_CLASS_GUEST_REBOOT);
	expect_failed(BE_MVP_CLASS_GUEST_REBOOT);
	CHECK(ctl.domain[0].phase == BE_MVP_DOMAIN_ENTERED);
	{
		be_u64 overlap = ALL_ONES;

		CHECK(be_mvp_control_overlap(&ctl, &overlap) == 0);
		CHECK(overlap == 0U);
	}
	/* After one domain shut down, the other may still fail. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_SHUTDOWN);
	drive(1U, TARGET_PINGED);
	make_fail(1U, tick(1U), BE_MVP_CLASS_VIRTUAL_INSTRUCTION, 3U);
	expect_step(BE_MVP_STEP_FAIL, 0U, 0U,
		    BE_MVP_CLASS_VIRTUAL_INSTRUCTION);
	CHECK(ctl.done == 0U);
	expect_failed(BE_MVP_CLASS_VIRTUAL_INSTRUCTION);
}

/* One DENIAL from @domain once it ENTERED: its step, then the loop's. */
static void expect_denial(be_u32 domain, be_u64 cause, be_u64 kind,
			  be_u64 gpa, enum be_mvp_step step)
{
	SCENARIO();
	fresh();
	drive(domain, TARGET_ENTERED);
	make_denial(domain, tick(domain), 1U, cause, kind, gpa);
	CHECK(apply(domain) == step);
	CHECK(result.step == step && result.ping == 0U && result.done == 0U);
	if (step == STEP_INVALID) {
		CHECK(result.failure == CLASS_RING);
		expect_failed(CLASS_RING);
		return;
	}
	CHECK(result.failure == CLASS_NONE && ctl.failed == 0U);
	CHECK(ctl.domain[domain].denials == 1U &&
	      ctl.domain[domain].records == 3U &&
	      ctl.domain[domain].phase == BE_MVP_DOMAIN_ENTERED);
}

/* The DENIAL record under test, from domain 0 once it ENTERED. */
static void denial_record(void)
{
	at(TARGET_ENTERED);
	make_denial(0U, tick(0U), 1U, LOAD, UNMAPPED, BESIDE_GPA);
}

/*
 * The DENIAL step (planning/mvp-m1-plan.md, "Control loop and failure
 * paths"): the kind against the walked windows and the sealed record, the
 * cause and injected cause, the GPA, the sequence, the exit time, a loop
 * without the record, and SHUTDOWN's reconciliation.
 */
static void test_denial(void)
{
	static const be_u64 causes[3] = { FETCH, LOAD, STORE };
	be_u64 index;

	/* Unmapped: outside the domain's window and the page, any cause. */
	for (index = 0U; index < 3U; ++index) {
		expect_denial(0U, causes[index], UNMAPPED, BESIDE_GPA,
			      BE_MVP_STEP_DENIAL);
		expect_denial(1U, causes[index], UNMAPPED, PROBE_GPA,
			      BE_MVP_STEP_DENIAL);
	}
	expect_denial(0U, LOAD, UNMAPPED, BE_MVP_GUEST_GPA - 1U,
		      BE_MVP_STEP_DENIAL);
	expect_denial(1U, STORE, UNMAPPED, 0U, BE_MVP_STEP_DENIAL);
	expect_denial(0U, LOAD, UNMAPPED, (BE_MVP_HTVAL_LIMIT << 2) - 1U,
		      BE_MVP_STEP_DENIAL);
	/* Not unmapped: the window's edges and the page's. */
	expect_denial(0U, LOAD, UNMAPPED, BE_MVP_GUEST_GPA, STEP_INVALID);
	expect_denial(1U, STORE, UNMAPPED, WINDOW_LAST, STEP_INVALID);
	expect_denial(0U, LOAD, UNMAPPED, PAGE_GPA, STEP_INVALID);
	expect_denial(1U, STORE, UNMAPPED, PAGE_LAST, STEP_INVALID);
	/* Read-only: a store to the page by the reader, never the writer. */
	expect_denial(1U, STORE, READ_ONLY, PAGE_GPA, BE_MVP_STEP_DENIAL);
	expect_denial(1U, STORE, READ_ONLY, PAGE_LAST, BE_MVP_STEP_DENIAL);
	expect_denial(0U, STORE, READ_ONLY, PAGE_GPA, STEP_INVALID);
	expect_denial(1U, LOAD, READ_ONLY, PAGE_GPA, STEP_INVALID);
	expect_denial(1U, FETCH, READ_ONLY, PAGE_GPA, STEP_INVALID);
	expect_denial(1U, STORE, READ_ONLY, BESIDE_GPA, STEP_INVALID);
	expect_denial(1U, STORE, READ_ONLY, WINDOW_LAST, STEP_INVALID);
	/* No other kind. */
	expect_denial(0U, LOAD, 2U, BESIDE_GPA, STEP_INVALID);
	expect_denial(1U, STORE, ALL_ONES, PAGE_GPA, STEP_INVALID);

	/* Without a channel (two-guests' record): no page, so no read-only,
	 * and the page's GPA is unmapped. */
	SCENARIO();
	fresh();
	CHECK(be_mvp_control_channel(&ctl, maps, &no_channel) == 1);
	drive(1U, TARGET_ENTERED);
	make_denial(1U, tick(1U), 1U, STORE, READ_ONLY, PAGE_GPA);
	CHECK(apply(1U) == STEP_INVALID && result.failure == CLASS_RING);
	SCENARIO();
	fresh();
	CHECK(be_mvp_control_channel(&ctl, maps, &no_channel) == 1);
	drive(1U, TARGET_ENTERED);
	make_denial(1U, tick(1U), 1U, LOAD, UNMAPPED, PAGE_GPA);
	CHECK(apply(1U) == BE_MVP_STEP_DENIAL);
	/* Without be_mvp_control_channel(), every DENIAL is refused. */
	SCENARIO();
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	drive(0U, TARGET_ENTERED);
	make_denial(0U, tick(0U), 1U, LOAD, UNMAPPED, BESIDE_GPA);
	CHECK(apply(0U) == STEP_INVALID && result.failure == CLASS_RING);

	/* The injected cause is the cause's access fault: 1, 5, 7. */
	for (index = 0U; index < 3U; ++index) {
		denial_record();
		set_word(&record, BE_MVP_DENIAL_CAUSE, causes[index]);
		set_word(&record, BE_MVP_DENIAL_INJECTED,
			 injected(causes[(index + 1U) % 3U]));
		expect_at(STEP_INVALID, CLASS_RING);
		denial_record();
		set_word(&record, BE_MVP_DENIAL_CAUSE, causes[index]);
		set_word(&record, BE_MVP_DENIAL_INJECTED, causes[index]);
		expect_at(STEP_INVALID, CLASS_RING);
	}
	/* Only guest-page faults: a load page fault, a virtual-instruction
	 * exception, an access fault. */
	denial_record();
	set_word(&record, BE_MVP_DENIAL_CAUSE, 13U);
	set_word(&record, BE_MVP_DENIAL_INJECTED, 5U);
	expect_at(STEP_INVALID, CLASS_RING);
	denial_record();
	set_word(&record, BE_MVP_DENIAL_CAUSE, 22U);
	set_word(&record, BE_MVP_DENIAL_INJECTED, 0U);
	expect_at(STEP_INVALID, CLASS_RING);
	denial_record();
	set_word(&record, BE_MVP_DENIAL_CAUSE, 5U);
	set_word(&record, BE_MVP_DENIAL_INJECTED, 5U);
	expect_at(STEP_INVALID, CLASS_RING);

	/* The GPA is htval's shifted left by 2 with stval's low bits. */
	for (index = 0U; index < 4U; ++index) {
		denial_record();
		set_word(&record, BE_MVP_DENIAL_GPA, BESIDE_GPA + index);
		set_word(&record, BE_MVP_DENIAL_STVAL, DENY_VA | index);
		expect_at(BE_MVP_STEP_DENIAL, CLASS_NONE);
		denial_record();
		set_word(&record, BE_MVP_DENIAL_GPA, BESIDE_GPA + index);
		set_word(&record, BE_MVP_DENIAL_STVAL,
			 DENY_VA | ((index + 1U) & 3U));
		expect_at(STEP_INVALID, CLASS_RING);
	}
	denial_record();
	set_word(&record, BE_MVP_DENIAL_HTVAL, (BESIDE_GPA >> 2) + 1U);
	expect_at(STEP_INVALID, CLASS_RING);
	/* An htval with an alias bit, whose shifted value is the GPA. */
	denial_record();
	set_word(&record, BE_MVP_DENIAL_HTVAL,
		 BE_U64_C(1) << 62 | BESIDE_GPA >> 2);
	expect_at(STEP_INVALID, CLASS_RING);
	denial_record();
	set_word(&record, BE_MVP_DENIAL_HTVAL, BE_MVP_HTVAL_LIMIT);
	set_word(&record, BE_MVP_DENIAL_GPA, BE_MVP_HTVAL_LIMIT << 2);
	set_word(&record, BE_MVP_DENIAL_STVAL, DENY_VA);
	expect_at(STEP_INVALID, CLASS_RING);

	/* The exit: at or after the domain's entry, at or before the post. */
	denial_record();
	set_word(&record, BE_MVP_DENIAL_EXIT, domain_entered[0]);
	expect_at(BE_MVP_STEP_DENIAL, CLASS_NONE);
	denial_record();
	set_word(&record, BE_MVP_DENIAL_EXIT, domain_entered[0] - 1U);
	expect_at(STEP_INVALID, CLASS_RING);
	denial_record();
	set_word(&record, BE_MVP_DENIAL_EXIT, record.time + 1U);
	expect_at(STEP_INVALID, CLASS_RING);

	/* The sequence: 1, 2, 3 ..., never repeated, skipped, or wrapped. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_PONGED);
	for (index = 1U; index <= 3U; ++index) {
		make_denial(0U, tick(0U), index, index == 2U ? STORE : LOAD,
			    UNMAPPED, index == 3U ? PROBE_GPA : BESIDE_GPA);
		expect_step(BE_MVP_STEP_DENIAL, 0U, 0U, CLASS_NONE);
		CHECK(ctl.domain[0].denials == index);
	}
	make_denial(0U, tick(0U), 3U, LOAD, UNMAPPED, BESIDE_GPA);
	CHECK(apply(0U) == STEP_INVALID && result.failure == CLASS_RING);
	at(TARGET_ENTERED);
	make_denial(0U, tick(0U), 0U, LOAD, UNMAPPED, BESIDE_GPA);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	make_denial(0U, tick(0U), 2U, LOAD, UNMAPPED, BESIDE_GPA);
	expect_at(STEP_INVALID, CLASS_RING);
	at(TARGET_ENTERED);
	ctl.domain[0].denials = ALL_ONES;
	make_denial(0U, tick(0U), 0U, LOAD, UNMAPPED, BESIDE_GPA);
	expect_at(STEP_INVALID, CLASS_RING);
	/* Each domain counts its own. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_ENTERED);
	drive(1U, TARGET_ENTERED);
	make_denial(1U, tick(1U), 1U, STORE, READ_ONLY, PAGE_GPA);
	expect_step(BE_MVP_STEP_DENIAL, 0U, 0U, CLASS_NONE);
	make_denial(0U, tick(0U), 1U, LOAD, UNMAPPED, BESIDE_GPA);
	expect_step(BE_MVP_STEP_DENIAL, 0U, 0U, CLASS_NONE);
	make_denial(1U, tick(1U), 2U, LOAD, UNMAPPED, PROBE_GPA);
	expect_step(BE_MVP_STEP_DENIAL, 0U, 0U, CLASS_NONE);
	CHECK(ctl.domain[0].denials == 1U && ctl.domain[1].denials == 2U &&
	      ctl.records == 7U);

	/* SHUTDOWN's denial word is the DENIAL records drained. */
	for (index = 0U; index < 4U; ++index) {
		SCENARIO();
		fresh();
		drive(1U, TARGET_PONGED);
		make_denial(1U, tick(1U), 1U, STORE, READ_ONLY, PAGE_GPA);
		expect_step(BE_MVP_STEP_DENIAL, 0U, 0U, CLASS_NONE);
		make_denial(1U, tick(1U), 2U, LOAD, UNMAPPED, PROBE_GPA);
		expect_step(BE_MVP_STEP_DENIAL, 0U, 0U, CLASS_NONE);
		domain_denials[1] = index;
		make_shutdown(1U, tick(1U), domain_entered[1], domain_lines[1],
			      0x100U);
		CHECK(apply(1U) == (index == 2U ? BE_MVP_STEP_SHUTDOWN :
				    STEP_INVALID));
		if (index != 2U)
			expect_failed(CLASS_RING);
	}
	SCENARIO();
	fresh();
	drive(0U, TARGET_PONGED);
	domain_denials[0] = 1U;
	make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0], 0U);
	CHECK(apply(0U) == STEP_INVALID && result.failure == CLASS_RING);
	/* Once the run failed, no DENIAL. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_ENTERED);
	drive(1U, TARGET_ENTERED);
	make_fail(1U, tick(1U), BE_MVP_CLASS_GUEST_PAGE_FAULT, 8U);
	expect_step(BE_MVP_STEP_FAIL, 0U, 0U, BE_MVP_CLASS_GUEST_PAGE_FAULT);
	make_denial(0U, tick(0U), 1U, LOAD, UNMAPPED, BESIDE_GPA);
	CHECK(apply(0U) == STEP_INVALID &&
	      result.failure == BE_MVP_CLASS_GUEST_PAGE_FAULT);

	/* be_mvp_control_channel(): absent input fails the loop. */
	SCENARIO();
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_channel(&ctl, maps, &channel) == 1);
	CHECK(ctl.sealed == 1U && ctl.window_gpa[1] == BE_MVP_GUEST_GPA &&
	      ctl.window_bytes[0] == BE_MVP_GUEST_BYTES &&
	      memcmp(&ctl.channel, &channel, sizeof(channel)) == 0);
	CHECK(be_mvp_control_channel(&ctl,
				     (const struct be_mvp_gstage_map *)0,
				     &channel) == 0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	CHECK(be_mvp_control_channel(&ctl, maps, &channel) == 0);
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_channel(&ctl, maps,
				     (const struct be_mvp_gstage_channel *)0) ==
	      0);
	CHECK(ctl.sealed == 0U);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	CHECK(be_mvp_control_channel((struct be_mvp_control *)0, maps,
				     &channel) == 0);
}

/*
 * anchor's three declared pages as hart 0 seals them (planning/mvp-m2-plan.md,
 * Q1): the request page G0 writes and G1 reads, the response page G1
 * writes and G0 reads, and the secret page only G1 reads.
 */
#define RO			BE_MVP_GSTAGE_RIGHT_READ
#define RW			(RO | BE_MVP_GSTAGE_RIGHT_WRITE)
#define REQUEST_GPA		BE_U64_C(0x84000000)
#define RESPONSE_GPA		BE_U64_C(0x84001000)
#define SECRET_GPA		BE_U64_C(0x84002000)
static const struct be_mvp_gstage_page anchor_pages[3] = {
	{ REQUEST_GPA, BE_U64_C(0x118000000), 0x1000U, BE_MVP_PAGE_CHANNEL,
	  0U, 1U, { RW, RO } },
	{ RESPONSE_GPA, BE_U64_C(0x118001000), 0x1000U, BE_MVP_PAGE_CHANNEL,
	  1U, 0U, { RO, RW } },
	{ SECRET_GPA, BE_U64_C(0x118002000), 0x1000U, BE_MVP_PAGE_SECRET,
	  BE_MVP_PAGE_NONE, 1U, { 0U, RO } },
};

/* One DENIAL against anchor's sealed pages, as expect_denial(). */
static void expect_page_denial(be_u32 domain, be_u64 cause, be_u64 kind,
			       be_u64 gpa, enum be_mvp_step step)
{
	SCENARIO();
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_pages(&ctl, maps, anchor_pages, 3U) == 1);
	domain_time[domain] = START + 0x100U;
	domain_denials[domain] = 0U;
	drive(domain, TARGET_ENTERED);
	make_denial(domain, tick(domain), 1U, cause, kind, gpa);
	CHECK(apply(domain) == step);
	if (step == STEP_INVALID) {
		CHECK(result.failure == CLASS_RING);
		expect_failed(CLASS_RING);
		return;
	}
	CHECK(result.failure == CLASS_NONE && ctl.domain[domain].denials == 1U);
}

/*
 * DENIAL records against a scenario's declared pages (M2-2's gap, closed
 * at M2-3): read-only for a store to a page the domain holds without
 * write, unmapped for an access to a page it holds nothing of or outside
 * every page and its window; and be_mvp_control_pages()'s input.
 */
static void test_pages(void)
{
	be_u64 index;

	/* The plan's declared denials: G0's store to the response page and
	 * its loads of the secret page, of G1's memory, and of the monitor;
	 * G1's store to the request page. */
	expect_page_denial(0U, STORE, READ_ONLY, RESPONSE_GPA + 0xff8U,
			   BE_MVP_STEP_DENIAL);
	expect_page_denial(0U, LOAD, UNMAPPED, SECRET_GPA, BE_MVP_STEP_DENIAL);
	expect_page_denial(0U, LOAD, UNMAPPED, BE_U64_C(0x114000000),
			   BE_MVP_STEP_DENIAL);
	expect_page_denial(0U, LOAD, UNMAPPED, BE_U64_C(0x102064000),
			   BE_MVP_STEP_DENIAL);
	expect_page_denial(1U, STORE, READ_ONLY, REQUEST_GPA + 0xff8U,
			   BE_MVP_STEP_DENIAL);
	/* Each page's edges, by its rights in each root. */
	for (index = 0U; index < 3U; ++index) {
		be_u64 first = anchor_pages[index].gpa;
		be_u64 last = first + anchor_pages[index].bytes - 1U;
		be_u32 domain;

		for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
			be_u64 rights = anchor_pages[index].rights[domain];
			enum be_mvp_step store = rights == RO ?
				BE_MVP_STEP_DENIAL : STEP_INVALID;
			enum be_mvp_step none = rights == 0U ?
				BE_MVP_STEP_DENIAL : STEP_INVALID;

			expect_page_denial(domain, STORE, READ_ONLY, first,
					   store);
			expect_page_denial(domain, STORE, READ_ONLY, last,
					   store);
			expect_page_denial(domain, LOAD, READ_ONLY, first,
					   STEP_INVALID);
			expect_page_denial(domain, LOAD, UNMAPPED, last, none);
			expect_page_denial(domain, FETCH, UNMAPPED, first,
					   none);
		}
	}
	/* Beside the pages: unmapped for both; never read-only. */
	expect_page_denial(0U, LOAD, UNMAPPED, SECRET_GPA + 0x1000U,
			   BE_MVP_STEP_DENIAL);
	expect_page_denial(1U, STORE, UNMAPPED, SECRET_GPA + 0x1000U,
			   BE_MVP_STEP_DENIAL);
	expect_page_denial(1U, STORE, READ_ONLY, SECRET_GPA + 0x1000U,
			   STEP_INVALID);
	expect_page_denial(0U, LOAD, UNMAPPED, WINDOW_LAST, STEP_INVALID);

	/* be_mvp_control_pages(): the windows and pages, or exception. */
	SCENARIO();
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_pages(&ctl, maps, anchor_pages, 3U) == 1);
	CHECK(ctl.sealed == 1U && ctl.page_count == 3U &&
	      ctl.window_bytes[1] == BE_MVP_GUEST_BYTES &&
	      ctl.channel.bytes == 0U &&
	      memcmp(ctl.pages, anchor_pages, sizeof(anchor_pages)) == 0);
	CHECK(be_mvp_control_pages(&ctl, maps, anchor_pages, 0U) == 0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_pages(&ctl, maps, anchor_pages,
				   BE_MVP_PAGES_MAX + 1U) == 0);
	CHECK(ctl.sealed == 0U);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_pages(&ctl, (const struct be_mvp_gstage_map *)0,
				   anchor_pages, 3U) == 0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_pages(&ctl, maps,
				   (const struct be_mvp_gstage_page *)0, 3U) ==
	      0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	CHECK(be_mvp_control_pages((struct be_mvp_control *)0, maps,
				   anchor_pages, 3U) == 0);
	/* M1's channel record is the same check as one page. */
	SCENARIO();
	fresh();
	CHECK(ctl.page_count == 1U && ctl.pages[0].gpa == PAGE_GPA &&
	      ctl.pages[0].rights[0] == RW && ctl.pages[0].rights[1] == RO);
}

/* Instance 3's one grant: G0, the host, may pause and terminate G1. */
static const struct be_mvp_mgmt_grant anchor_grants[1] = {
	{ 0U, 1U, BE_MVP_MGMT_PAUSE | BE_MVP_MGMT_TERMINATE },
};
static struct be_mvp_mgmt_state mgmt;

#define PAUSE			BE_MVP_SBI_MGMT_PAUSE
#define TERMINATE		BE_MVP_SBI_MGMT_TERMINATE
#define DENIED			BE_MVP_SBI_ERR_DENIED
#define NO_DOMAIN		BE_MVP_SBI_ERR_INVALID_PARAM
#define INVALID_STATE		BE_MVP_SBI_ERR_INVALID_STATE
#define DECIDED			BE_MVP_TARGET_COUNT

/*
 * Both domains running, past their PONG, with the management state:
 * @checked 1 decides against anchor's grant, 0 as no-grant-check.
 */
static void mgmt_both(int checked)
{
	SCENARIO();
	fresh();
	CHECK(be_mvp_control_mgmt(&ctl, &mgmt, anchor_grants, 1U, checked) ==
	      1);
	drive(0U, TARGET_PONGED);
	drive(1U, TARGET_PONGED);
}

/* @domain's next MGMT_REQUEST, applied: @fid on @target. */
static enum be_mvp_step ask(be_u32 domain, be_u64 fid, be_u64 target)
{
	make_request(domain, tick(domain), domain_requests[domain] + 1U, fid,
		     target);
	if (apply(domain) != STEP_INVALID)
		++domain_requests[domain];
	return result.step;
}

static void expect_answer(be_u64 requester, be_u64 seq, be_u64 fid,
			  be_u64 target, long code,
			  enum be_mvp_target_state shown)
{
	CHECK(result.answer == 1U && result.requester == requester &&
	      result.seq == seq && result.fid == fid &&
	      result.target == target && result.result == code &&
	      result.shown == shown && result.failure == CLASS_NONE);
	CHECK(mgmt.domain[requester].awaiting == 0U && ctl.failed == 0U);
}

/* @domain's request, answered at once with @code. */
static void expect_decided(be_u32 domain, be_u64 fid, be_u64 target,
			   long code)
{
	CHECK(ask(domain, fid, target) == BE_MVP_STEP_MGMT);
	expect_answer(domain, domain_requests[domain], fid, target, code,
		      DECIDED);
	CHECK(result.requested == record.time && result.done == 0U &&
	      ctl.domain[domain].requests == domain_requests[domain]);
}

/* @domain's request, delivered and pending on @target. */
static void expect_delivered(be_u32 domain, be_u64 fid, be_u64 target)
{
	CHECK(ask(domain, fid, target) == BE_MVP_STEP_DELIVER);
	CHECK(result.answer == 0U && result.requester == domain &&
	      result.seq == domain_requests[domain] && result.fid == fid &&
	      result.target == target && result.requested == record.time);
	CHECK(mgmt.domain[target].pending == 1U &&
	      mgmt.domain[target].by == domain &&
	      mgmt.domain[target].fid == fid &&
	      mgmt.domain[target].seq == domain_requests[domain] &&
	      mgmt.domain[target].time == record.time &&
	      mgmt.domain[domain].awaiting == 1U);
}

/* @domain's PAUSED or TERMINATED, naming @by; its step and done. */
static void expect_transition(be_u32 type, be_u32 domain, be_u64 by,
			      be_u32 done)
{
	enum be_mvp_step step = type == BE_MVP_RECORD_PAUSED ?
		BE_MVP_STEP_PAUSED : BE_MVP_STEP_TERMINATED;
	be_u64 seq = mgmt.domain[domain].seq;
	be_u64 fid = mgmt.domain[domain].fid;

	make_transition(type, domain, tick(domain), by, 0x40U);
	expect_step(step, 0U, done, CLASS_NONE);
	expect_answer(by, seq, fid, domain, BE_MVP_SBI_SUCCESS,
		      step == BE_MVP_STEP_PAUSED ? BE_MVP_TARGET_PAUSED :
		      BE_MVP_TARGET_TERMINATED);
	CHECK(mgmt.domain[domain].pending == 0U &&
	      ctl.domain[domain].phase == (step == BE_MVP_STEP_PAUSED ?
					   BE_MVP_DOMAIN_PAUSED :
					   BE_MVP_DOMAIN_TERMINATED));
}

/* One record under test refused as ring. */
static void expect_ring(be_u32 domain)
{
	CHECK(apply(domain) == STEP_INVALID && result.failure == CLASS_RING);
	expect_failed(CLASS_RING);
}

/*
 * Hart 0's management requests (planning/mvp-m2-plan.md, "Control loop
 * and failure paths", Q14, and Q15): Instance 3's sequence, each decision
 * answered at once, each delivery pending until its target's transition,
 * the pending and terminal states, the completion rule, the no-grant-check
 * variant, a target that shuts down first, and every malformed record.
 */
static void test_mgmt(void)
{
	static const be_u64 fids[3] = { 2U, 7U, ALL_ONES };
	be_u64 asked;
	be_u64 index;

	/* Instance 3: the protected domain's and the host's unauthorized
	 * calls, the burst, then pause and terminate of the protected
	 * domain; the host's shutdown completes the run. */
	mgmt_both(1);
	expect_decided(1U, TERMINATE, 0U, DENIED);
	expect_decided(1U, PAUSE, 0U, DENIED);
	expect_decided(0U, PAUSE, 0U, DENIED);
	expect_decided(0U, TERMINATE, 0U, DENIED);
	expect_decided(0U, PAUSE, 2U, NO_DOMAIN);
	for (index = 0U; index < 8U; ++index)
		expect_decided(0U, TERMINATE, 0U, DENIED);
	expect_delivered(0U, PAUSE, 1U);
	CHECK(mgmt.domain[1].seq == 12U);
	expect_transition(BE_MVP_RECORD_PAUSED, 1U, 0U, 0U);
	expect_delivered(0U, TERMINATE, 1U);
	expect_transition(BE_MVP_RECORD_TERMINATED, 1U, 0U, 0U);
	CHECK(ctl.domain[1].shutdown == record.time);
	CHECK(ctl.domain[0].requests == 13U && ctl.domain[1].requests == 2U);
	make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0],
		      0x100U);
	expect_step(BE_MVP_STEP_SHUTDOWN, 0U, 1U, CLASS_NONE);
	CHECK(result.answer == 0U && ctl.done == 1U);
	/* A paused domain: pause is invalid state, terminate delivered; a
	 * terminated one: both invalid state. */
	mgmt_both(1);
	expect_delivered(0U, PAUSE, 1U);
	expect_transition(BE_MVP_RECORD_PAUSED, 1U, 0U, 0U);
	expect_decided(0U, PAUSE, 1U, INVALID_STATE);
	expect_delivered(0U, TERMINATE, 1U);
	expect_transition(BE_MVP_RECORD_TERMINATED, 1U, 0U, 0U);
	expect_decided(0U, PAUSE, 1U, INVALID_STATE);
	expect_decided(0U, TERMINATE, 1U, INVALID_STATE);
	/* A paused domain does not end the run, which times out. */
	mgmt_both(1);
	expect_delivered(0U, PAUSE, 1U);
	expect_transition(BE_MVP_RECORD_PAUSED, 1U, 0U, 0U);
	make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0], 0U);
	expect_step(BE_MVP_STEP_SHUTDOWN, 0U, 0U, CLASS_NONE);
	CHECK(ctl.done == 0U);
	CHECK(be_mvp_control_wake(&ctl, START + BUDGET - 1U) == CLASS_NONE);
	CHECK(be_mvp_control_wake(&ctl, START + BUDGET) ==
	      BE_MVP_CLASS_RUN_TIMEOUT);
	/* A domain that has shut down: invalid state; the other's shutdown
	 * then completes the run. */
	mgmt_both(1);
	make_shutdown(1U, tick(1U), domain_entered[1], domain_lines[1], 0U);
	expect_step(BE_MVP_STEP_SHUTDOWN, 0U, 0U, CLASS_NONE);
	expect_decided(0U, PAUSE, 1U, INVALID_STATE);
	expect_decided(0U, TERMINATE, 1U, INVALID_STATE);
	make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0], 0U);
	expect_step(BE_MVP_STEP_SHUTDOWN, 0U, 1U, CLASS_NONE);
	/* A target that shuts down before it takes the delivered request:
	 * the requester is answered invalid state, the target shut down;
	 * a late transition is refused. */
	mgmt_both(1);
	expect_delivered(0U, TERMINATE, 1U);
	asked = record.time;
	make_shutdown(1U, tick(1U), domain_entered[1], domain_lines[1], 0U);
	expect_step(BE_MVP_STEP_SHUTDOWN, 0U, 0U, CLASS_NONE);
	expect_answer(0U, 1U, TERMINATE, 1U, INVALID_STATE,
		      BE_MVP_TARGET_SHUTDOWN);
	CHECK(result.requested == asked && mgmt.domain[1].pending == 0U &&
	      ctl.domain[1].phase == BE_MVP_DOMAIN_SHUTDOWN);
	make_transition(BE_MVP_RECORD_TERMINATED, 1U, tick(1U), 0U, 0x40U);
	expect_ring(1U);
	/* A requester cannot shut down while it waits for its answer (its
	 * hart waits in HS): a SHUTDOWN that claims to is ring. */
	mgmt_both(1);
	expect_delivered(0U, PAUSE, 1U);
	make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0], 0U);
	expect_ring(0U);
	/* Nor make a second request. */
	mgmt_both(1);
	expect_delivered(0U, PAUSE, 1U);
	make_request(0U, tick(0U), 2U, PAUSE, 1U);
	expect_ring(0U);

	/* Pending: a target with a delivered request, or a requester waiting
	 * for its answer; and a request to oneself, pending as it is made.
	 * The grant check decides first: denied with it, invalid state in
	 * the no-grant-check variant. */
	mgmt_both(0);
	expect_decided(0U, PAUSE, 0U, INVALID_STATE);
	expect_decided(1U, TERMINATE, 1U, INVALID_STATE);
	expect_decided(1U, PAUSE, 2U, NO_DOMAIN);
	expect_decided(0U, TERMINATE, ALL_ONES, NO_DOMAIN);
	expect_delivered(0U, PAUSE, 1U);
	expect_decided(1U, PAUSE, 1U, INVALID_STATE);
	expect_decided(1U, TERMINATE, 0U, INVALID_STATE);
	expect_transition(BE_MVP_RECORD_PAUSED, 1U, 0U, 0U);
	mgmt_both(1);
	expect_delivered(0U, PAUSE, 1U);
	expect_decided(1U, PAUSE, 1U, DENIED);
	expect_decided(1U, TERMINATE, 0U, DENIED);
	expect_transition(BE_MVP_RECORD_PAUSED, 1U, 0U, 0U);
	/* no-grant-check's declared outcome: the protected domain terminates
	 * the host, whose pause is then invalid state, and the run times
	 * out. */
	mgmt_both(0);
	expect_delivered(1U, TERMINATE, 0U);
	expect_transition(BE_MVP_RECORD_TERMINATED, 0U, 1U, 0U);
	expect_decided(1U, PAUSE, 0U, INVALID_STATE);
	CHECK(ctl.done == 0U && be_mvp_control_wake(&ctl, START + BUDGET) ==
	      BE_MVP_CLASS_RUN_TIMEOUT);

	/* A first LINE while a request is pending on its domain asks for no
	 * PONG: the domain may park before the PING. */
	SCENARIO();
	fresh();
	CHECK(be_mvp_control_mgmt(&ctl, &mgmt, anchor_grants, 1U, 1) == 1);
	drive(0U, TARGET_PONGED);
	drive(1U, TARGET_ENTERED);
	expect_delivered(0U, PAUSE, 1U);
	make_line(1U, tick(1U), "late");
	expect_step(BE_MVP_STEP_LINE, 0U, 0U, CLASS_NONE);
	CHECK(ctl.domain[1].pinged == 1U);
	expect_transition(BE_MVP_RECORD_PAUSED, 1U, 0U, 0U);

	/* SHUTDOWN's management word is the requests drained. */
	for (index = 0U; index < 4U; ++index) {
		mgmt_both(1);
		expect_decided(0U, PAUSE, 0U, DENIED);
		expect_decided(0U, TERMINATE, 0U, DENIED);
		domain_requests[0] = index;
		make_shutdown(0U, tick(0U), domain_entered[0], domain_lines[0],
			      0U);
		CHECK(apply(0U) == (index == 2U ? BE_MVP_STEP_SHUTDOWN :
				    STEP_INVALID));
		if (index != 2U)
			expect_failed(CLASS_RING);
	}

	/* Malformed requests: ring. Another function is the domain hart's
	 * own answer; the sequence runs 1, 2, 3 ...; the payload is three
	 * words; only a running domain asks. */
	for (index = 0U; index < 3U; ++index) {
		mgmt_both(1);
		make_request(0U, tick(0U), 1U, fids[index], 1U);
		expect_ring(0U);
	}
	mgmt_both(1);
	make_request(0U, tick(0U), 0U, PAUSE, 1U);
	expect_ring(0U);
	mgmt_both(1);
	make_request(0U, tick(0U), 2U, PAUSE, 1U);
	expect_ring(0U);
	mgmt_both(1);
	expect_decided(0U, PAUSE, 0U, DENIED);
	make_request(0U, tick(0U), 1U, PAUSE, 0U);
	expect_ring(0U);
	mgmt_both(1);
	ctl.domain[0].requests = ALL_ONES;
	make_request(0U, tick(0U), 0U, PAUSE, 1U);
	expect_ring(0U);
	for (index = 2U; index <= 4U; index += 2U) {
		mgmt_both(1);
		make_request(0U, tick(0U), 1U, PAUSE, 1U);
		record.length = index * WORD;
		expect_ring(0U);
	}
	SCENARIO();
	fresh();
	CHECK(be_mvp_control_mgmt(&ctl, &mgmt, anchor_grants, 1U, 1) == 1);
	drive(0U, TARGET_READY);
	make_request(0U, tick(0U), 1U, PAUSE, 1U);
	expect_ring(0U);
	mgmt_both(1);
	expect_delivered(0U, PAUSE, 1U);
	expect_transition(BE_MVP_RECORD_PAUSED, 1U, 0U, 0U);
	make_request(1U, tick(1U), 1U, TERMINATE, 0U);
	expect_ring(1U);
	/* Without be_mvp_control_mgmt(), a request is ring. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_PONGED);
	make_request(0U, tick(0U), 1U, PAUSE, 1U);
	expect_ring(0U);

	/* Malformed transitions: ring. One must answer the request pending
	 * on its domain: that function, that requester, two words. */
	mgmt_both(1);
	make_transition(BE_MVP_RECORD_PAUSED, 1U, tick(1U), 0U, 0x40U);
	expect_ring(1U);
	mgmt_both(1);
	expect_delivered(0U, TERMINATE, 1U);
	make_transition(BE_MVP_RECORD_PAUSED, 1U, tick(1U), 0U, 0x40U);
	expect_ring(1U);
	mgmt_both(1);
	expect_delivered(0U, PAUSE, 1U);
	make_transition(BE_MVP_RECORD_TERMINATED, 1U, tick(1U), 0U, 0x40U);
	expect_ring(1U);
	for (index = 1U; index <= 2U; ++index) {
		mgmt_both(1);
		expect_delivered(0U, PAUSE, 1U);
		make_transition(BE_MVP_RECORD_PAUSED, 1U, tick(1U), index,
				0x40U);
		expect_ring(1U);
	}
	for (index = 1U; index <= 3U; index += 2U) {
		mgmt_both(1);
		expect_delivered(0U, PAUSE, 1U);
		make_transition(BE_MVP_RECORD_PAUSED, 1U, tick(1U), 0U, 0x40U);
		record.length = index * WORD;
		expect_ring(1U);
	}
	/* A paused domain posts nothing else: no LINE, no second PAUSED. */
	mgmt_both(1);
	expect_delivered(0U, PAUSE, 1U);
	expect_transition(BE_MVP_RECORD_PAUSED, 1U, 0U, 0U);
	make_line(1U, tick(1U), "after");
	expect_ring(1U);
	mgmt_both(1);
	expect_delivered(0U, PAUSE, 1U);
	expect_transition(BE_MVP_RECORD_PAUSED, 1U, 0U, 0U);
	make_transition(BE_MVP_RECORD_PAUSED, 1U, tick(1U), 0U, 0x40U);
	expect_ring(1U);
	/* A terminated domain's records are refused. */
	mgmt_both(1);
	expect_delivered(0U, TERMINATE, 1U);
	expect_transition(BE_MVP_RECORD_TERMINATED, 1U, 0U, 0U);
	make_shutdown(1U, tick(1U), domain_entered[1], domain_lines[1], 0U);
	expect_ring(1U);

	/* be_mvp_control_mgmt()'s input: absent or invalid is exception. */
	SCENARIO();
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	memset(&mgmt, 0xa5, sizeof(mgmt));
	CHECK(be_mvp_control_mgmt(&ctl, &mgmt, anchor_grants, 1U, 1) == 1);
	CHECK(ctl.mgmt == &mgmt && mgmt.grants == anchor_grants &&
	      mgmt.count == 1U && mgmt.checked == 1U &&
	      mgmt.domain[0].pending == 0U && mgmt.domain[1].awaiting == 0U);
	CHECK(be_mvp_control_mgmt(&ctl, &mgmt,
				  (const struct be_mvp_mgmt_grant *)0, 0U, 0) ==
	      1);
	CHECK(mgmt.checked == 0U && mgmt.count == 0U);
	CHECK(be_mvp_control_mgmt(&ctl, &mgmt, anchor_grants,
				  BE_MVP_MGMT_GRANTS_MAX + 1U, 1) == 0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_mgmt(&ctl, (struct be_mvp_mgmt_state *)0,
				  anchor_grants, 1U, 1) == 0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_mgmt(&ctl, &mgmt,
				  (const struct be_mvp_mgmt_grant *)0, 1U, 1) ==
	      0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_mgmt(&ctl, &mgmt, anchor_grants, 1U, 2) == 0);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	CHECK(be_mvp_control_mgmt(&ctl, &mgmt, anchor_grants, 1U, 1) == 0);
	CHECK(be_mvp_control_mgmt((struct be_mvp_control *)0, &mgmt,
				  anchor_grants, 1U, 1) == 0);
}

static void test_saturation(void)
{
	SCENARIO();
	fresh();
	drive(0U, TARGET_PINGED);
	ctl.records = ALL_ONES - 1U;
	ctl.domain[0].records = ALL_ONES;
	ctl.domain[0].lines = ALL_ONES - 1U;
	make_line(0U, tick(0U), "a");
	CHECK(apply(0U) == BE_MVP_STEP_LINE);
	CHECK(ctl.records == ALL_ONES && ctl.domain[0].records == ALL_ONES);
	CHECK(ctl.domain[0].lines == ALL_ONES);
	make_line(0U, tick(0U), "b");
	CHECK(apply(0U) == BE_MVP_STEP_LINE);
	CHECK(ctl.records == ALL_ONES && ctl.domain[0].lines == ALL_ONES);
	make_pong(0U, tick(0U), 1U);
	CHECK(apply(0U) == BE_MVP_STEP_PONG);
	make_shutdown(0U, tick(0U), domain_entered[0], ALL_ONES, 0U);
	CHECK(apply(0U) == BE_MVP_STEP_SHUTDOWN);
	CHECK(ctl.failed == 0U && ctl.records == ALL_ONES);
	/* Waits and wakes saturate too. */
	SCENARIO();
	fresh();
	be_mvp_control_waited(&ctl, 10U);
	be_mvp_control_waited(&ctl, 20U);
	CHECK(ctl.idle_ticks == 30U);
	be_mvp_control_waited(&ctl, ALL_ONES - 31U);
	CHECK(ctl.idle_ticks == ALL_ONES - 1U);
	be_mvp_control_waited(&ctl, 5U);
	CHECK(ctl.idle_ticks == ALL_ONES);
	be_mvp_control_waited(&ctl, ALL_ONES);
	CHECK(ctl.idle_ticks == ALL_ONES);
	be_mvp_control_waited((struct be_mvp_control *)0, 1U);
	drive(0U, TARGET_STARTED);
	drive(1U, TARGET_STARTED);
	ctl.wakes = ALL_ONES - 1U;
	CHECK(be_mvp_control_wake(&ctl, START) == CLASS_NONE);
	CHECK(ctl.wakes == ALL_ONES);
	CHECK(be_mvp_control_wake(&ctl, START) == CLASS_NONE);
	CHECK(ctl.wakes == ALL_ONES);
}

static void both(enum target target)
{
	SCENARIO();
	fresh();
	drive(0U, target);
	drive(1U, target);
}

static void test_wake(void)
{
	/* Both domains must have started. */
	SCENARIO();
	fresh();
	CHECK(be_mvp_control_wake(&ctl, START) == BE_MVP_CLASS_EXCEPTION);
	CHECK(ctl.wakes == 1U);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	fresh();
	drive(0U, TARGET_STARTED);
	CHECK(be_mvp_control_wake(&ctl, START) == BE_MVP_CLASS_EXCEPTION);
	expect_failed(BE_MVP_CLASS_EXCEPTION);
	CHECK(be_mvp_control_wake((struct be_mvp_control *)0, START) ==
	      BE_MVP_CLASS_EXCEPTION);

	/* The READY wait, counted from the start. */
	both(TARGET_STARTED);
	CHECK(be_mvp_control_wake(&ctl, START) == CLASS_NONE);
	CHECK(be_mvp_control_wake(&ctl, START + READY_WAIT - 1U) ==
	      CLASS_NONE);
	CHECK(ctl.wakes == 2U && ctl.failed == 0U);
	CHECK(be_mvp_control_wake(&ctl, START + READY_WAIT) ==
	      BE_MVP_CLASS_HART_READY);
	CHECK(ctl.wakes == 3U);
	expect_failed(BE_MVP_CLASS_HART_READY);
	/* One hart READY, the other not. */
	both(TARGET_STARTED);
	make(BE_MVP_RECORD_READY, 0U, tick(0U), BE_MVP_READY_WORDS);
	expect_step(BE_MVP_STEP_READY, 0U, 0U, CLASS_NONE);
	CHECK(be_mvp_control_wake(&ctl, START + READY_WAIT + 5U) ==
	      BE_MVP_CLASS_HART_READY);
	expect_failed(BE_MVP_CLASS_HART_READY);
	/* Once both are READY, only the budget counts. */
	both(TARGET_READY);
	CHECK(be_mvp_control_wake(&ctl, START + READY_WAIT) == CLASS_NONE);
	CHECK(be_mvp_control_wake(&ctl, START + BUDGET - 1U) == CLASS_NONE);
	CHECK(be_mvp_control_wake(&ctl, START + BUDGET) ==
	      BE_MVP_CLASS_RUN_TIMEOUT);
	expect_failed(BE_MVP_CLASS_RUN_TIMEOUT);
	both(TARGET_PONGED);
	CHECK(be_mvp_control_wake(&ctl, START + BUDGET + 5U) ==
	      BE_MVP_CLASS_RUN_TIMEOUT);
	expect_failed(BE_MVP_CLASS_RUN_TIMEOUT);
	both(TARGET_ENTERED);
	CHECK(be_mvp_control_wake(&ctl, ALL_ONES) ==
	      BE_MVP_CLASS_RUN_TIMEOUT);
	/* One domain shut down, the other running: the budget still counts. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_SHUTDOWN);
	drive(1U, TARGET_ENTERED);
	CHECK(be_mvp_control_wake(&ctl, START + BUDGET - 1U) == CLASS_NONE);
	CHECK(be_mvp_control_wake(&ctl, START + BUDGET) ==
	      BE_MVP_CLASS_RUN_TIMEOUT);

	/* A clock behind the start cannot measure the budget. */
	both(TARGET_READY);
	CHECK(be_mvp_control_wake(&ctl, START - 1U) ==
	      BE_MVP_CLASS_RUN_TIMEOUT);
	expect_failed(BE_MVP_CLASS_RUN_TIMEOUT);
	both(TARGET_STARTED);
	CHECK(be_mvp_control_wake(&ctl, 0U) == BE_MVP_CLASS_RUN_TIMEOUT);
	/* A start near 2^64: no wrap is mistaken for time. */
	SCENARIO();
	be_mvp_control_init(&ctl, ALL_ONES - 100U, 50U, 20U);
	CHECK(be_mvp_control_started(&ctl, 0U, 1U) == 1);
	CHECK(be_mvp_control_started(&ctl, 1U, 2U) == 1);
	CHECK(be_mvp_control_wake(&ctl, ALL_ONES - 81U) == CLASS_NONE);
	CHECK(be_mvp_control_wake(&ctl, ALL_ONES - 80U) ==
	      BE_MVP_CLASS_HART_READY);
	be_mvp_control_init(&ctl, ALL_ONES - 100U, 50U, 20U);
	CHECK(be_mvp_control_started(&ctl, 0U, 1U) == 1);
	CHECK(be_mvp_control_started(&ctl, 1U, 2U) == 1);
	make(BE_MVP_RECORD_READY, 0U, 1U, BE_MVP_READY_WORDS);
	expect_step(BE_MVP_STEP_READY, 0U, 0U, CLASS_NONE);
	make(BE_MVP_RECORD_READY, 1U, 1U, BE_MVP_READY_WORDS);
	expect_step(BE_MVP_STEP_READY, 0U, 0U, CLASS_NONE);
	CHECK(be_mvp_control_wake(&ctl, ALL_ONES - 51U) == CLASS_NONE);
	CHECK(be_mvp_control_wake(&ctl, ALL_ONES - 50U) ==
	      BE_MVP_CLASS_RUN_TIMEOUT);
	be_mvp_control_init(&ctl, ALL_ONES - 100U, 50U, 20U);
	CHECK(be_mvp_control_started(&ctl, 0U, 1U) == 1);
	CHECK(be_mvp_control_started(&ctl, 1U, 2U) == 1);
	CHECK(be_mvp_control_wake(&ctl, 5U) == BE_MVP_CLASS_RUN_TIMEOUT);

	/* The run-timeout variant: the budget runs out before the READY
	 * wait, so the class is run-timeout even with a hart not READY. */
	SCENARIO();
	be_mvp_control_init(&ctl, START, BE_MVP_VARIANT_RUN_BUDGET,
			    READY_WAIT);
	CHECK(be_mvp_control_started(&ctl, 0U, 1U) == 1);
	CHECK(be_mvp_control_started(&ctl, 1U, 2U) == 1);
	CHECK(be_mvp_control_wake(&ctl, START + 0xfffffU) == CLASS_NONE);
	CHECK(be_mvp_control_wake(&ctl, START + 0x100000U) ==
	      BE_MVP_CLASS_RUN_TIMEOUT);
	/* Both expired: the hart that never became READY is the cause. */
	SCENARIO();
	be_mvp_control_init(&ctl, START, 0x100U, 0x80U);
	CHECK(be_mvp_control_started(&ctl, 0U, 1U) == 1);
	CHECK(be_mvp_control_started(&ctl, 1U, 2U) == 1);
	CHECK(be_mvp_control_wake(&ctl, START + 0x100U) ==
	      BE_MVP_CLASS_HART_READY);
}

/*
 * Hart 0's round-robin drain (Plan revision M0-C.1), driven as the runtime
 * drives it: be_mvp_drain_next() names a ring, and the visit acquires its
 * head, takes at most one record, and releases its tail (here without the
 * fences), or takes nothing from a held ring. Each record's time is its
 * place in its ring, so the order of the takes is checked; a writer as
 * fast as hart 0 posts one more record after each take from its ring.
 */
#define DRAIN_RING_BYTES	BE_MVP_OUTBOUND_RING_BYTES
#define DRAIN_TAKES_MAX \
	(BE_MVP_DOMAINS * (DRAIN_RING_BYTES / BE_MVP_RECORD_HEADER_BYTES + 1U))

static be_u8 drain_buffer[BE_MVP_DOMAINS][DRAIN_RING_BYTES];
static struct be_mvp_ring_index drain_head[BE_MVP_DOMAINS];
static struct be_mvp_ring_index drain_tail[BE_MVP_DOMAINS];
static struct be_mvp_ring drain_writer[BE_MVP_DOMAINS];
static struct be_mvp_ring drain_reader[BE_MVP_DOMAINS];
static be_u64 drain_posted[BE_MVP_DOMAINS];
static be_u64 drain_expected[BE_MVP_DOMAINS];
static be_u32 drain_taken[DRAIN_TAKES_MAX];
static be_u64 drain_takes;
static be_u64 drain_visits;
static be_u32 drain_held_rings;
static be_u32 drain_fast_rings;

/* Empty rings of @capacity bytes, as the barrier leaves them. */
static void drain_rings(be_u64 capacity)
{
	be_u32 domain;

	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		be_mvp_ring_reset(&drain_head[domain], &drain_tail[domain]);
		CHECK(be_mvp_ring_init(&drain_writer[domain],
				       drain_buffer[domain], capacity,
				       &drain_head[domain], &drain_tail[domain],
				       BE_MVP_RECORDS_OUTBOUND, domain,
				       BE_MVP_RING_WRITER) == 1);
		CHECK(be_mvp_ring_init(&drain_reader[domain],
				       drain_buffer[domain], capacity,
				       &drain_head[domain], &drain_tail[domain],
				       BE_MVP_RECORDS_OUTBOUND, domain,
				       BE_MVP_RING_READER) == 1);
		drain_posted[domain] = 0U;
		drain_expected[domain] = 0U;
	}
	drain_takes = 0U;
	drain_visits = 0U;
	drain_held_rings = 0U;
	drain_fast_rings = 0U;
}

/* @count records, each a 16-byte LINE header, posted and published. */
static void drain_post(be_u32 domain, be_u64 count)
{
	be_u64 index;

	for (index = 0U; index < count; ++index)
		CHECK(be_mvp_ring_post(&drain_writer[domain],
				       BE_MVP_RECORD_LINE,
				       drain_posted[domain]++,
				       (const be_u8 *)0, 0U) == 1);
	CHECK(be_mvp_ring_publish(&drain_writer[domain]) == 1);
}

static int drain_visit(be_u32 domain)
{
	struct be_mvp_ring *reader = &drain_reader[domain];

	++drain_visits;
	if ((drain_held_rings & (1U << domain)) != 0U)
		return 0;
	if (be_mvp_ring_acquire(reader) == 0U) {
		CHECK(reader->failed == 0U);
		return 0;
	}
	CHECK(be_mvp_ring_take(reader, &record) == BE_MVP_RING_RECORD);
	CHECK(be_mvp_ring_release(reader) == 1);
	CHECK(record.domain == domain && record.type == BE_MVP_RECORD_LINE);
	/* Each ring's records come out in the order they were posted. */
	CHECK(record.time == drain_expected[domain]);
	++drain_expected[domain];
	CHECK(drain_takes < DRAIN_TAKES_MAX);
	drain_taken[drain_takes++] = domain;
	if ((drain_fast_rings & (1U << domain)) != 0U)
		drain_post(domain, 1U);
	return 1;
}

/* One drain, as the runtime's loop runs it. */
static void drain_run(be_u32 rings, be_u64 capacity)
{
	struct be_mvp_drain order;
	be_u32 domain;

	be_mvp_drain_begin(&order, rings, capacity);
	for (domain = be_mvp_drain_next(&order); domain < BE_MVP_DOMAINS;
	     domain = be_mvp_drain_next(&order)) {
		CHECK(domain < rings && drain_visits < DRAIN_TAKES_MAX);
		be_mvp_drain_visited(&order, drain_visit(domain));
	}
	CHECK(domain == BE_MVP_DRAIN_DONE);
}

/* The bytes a ring still holds. */
static be_u64 drain_left(be_u32 domain)
{
	return drain_head[domain].value - drain_tail[domain].value;
}

/*
 * A drain allows each ring its capacity in record headers and one more
 * visit: here every visit takes, from rings a writer keeps full.
 */
static void drain_bound(be_u32 rings, be_u64 capacity)
{
	be_u64 per_ring = capacity / BE_MVP_RECORD_HEADER_BYTES;
	be_u64 index;
	be_u32 domain;

	SCENARIO();
	drain_rings(capacity);
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		drain_post(domain, per_ring);
	drain_fast_rings = 3U;
	drain_run(rings, capacity);
	CHECK(drain_visits == rings * (per_ring + 1U));
	CHECK(drain_takes == drain_visits);
	for (index = 0U; index < drain_takes; ++index)
		CHECK(drain_taken[index] == (rings == 1U ? 0U : index % 2U));
	/* Every record the rings held at the start was taken. */
	for (domain = 0U; domain < rings; ++domain)
		CHECK(drain_expected[domain] == per_ring + 1U &&
		      drain_left(domain) == capacity);
	CHECK(rings == 2U || drain_expected[1] == 0U);
}

static void test_drain_order(void)
{
	static const be_u32 bad_rings[7] = { 0U, 3U, 2U, 2U, 2U, 2U, 1U };
	static const be_u64 bad_bytes[7] = {
		BE_MVP_RING_MIN_BYTES, BE_MVP_RING_MIN_BYTES, 0U,
		BE_MVP_RING_MIN_BYTES / 2U, BE_MVP_RING_MIN_BYTES + 256U,
		2U * BE_MVP_OUTBOUND_RING_BYTES, 0x3000U,
	};
	struct be_mvp_drain order;
	be_u64 index;
	be_u32 n0;
	be_u32 n1;

	/*
	 * Two rings holding n0 and n1 records: one take from each in turn
	 * while both hold one, then the rest of the longer; the drain ends at
	 * the first visit after which each ring's latest visit took nothing.
	 */
	for (n0 = 0U; n0 <= 8U; ++n0) {
		for (n1 = 0U; n1 <= 8U; ++n1) {
			be_u64 pairs = n0 < n1 ? n0 : n1;

			SCENARIO();
			drain_rings(BE_MVP_RING_MIN_BYTES);
			drain_post(0U, n0);
			drain_post(1U, n1);
			drain_run(BE_MVP_DOMAINS, BE_MVP_RING_MIN_BYTES);
			CHECK(drain_takes == n0 + n1);
			for (index = 0U; index < drain_takes; ++index)
				CHECK(drain_taken[index] ==
				      (index < 2U * pairs ? index % 2U :
				       n0 > n1 ? 0U : 1U));
			CHECK(drain_visits == (n0 > n1 ? 2U * n0 + 1U :
					       2U * n1 + 2U));
			CHECK(drain_left(0U) == 0U && drain_left(1U) == 0U);
		}
	}

	/* The probe images visit domain 0's ring alone. */
	SCENARIO();
	drain_rings(BE_MVP_RING_MIN_BYTES);
	drain_post(0U, 5U);
	drain_post(1U, 5U);
	drain_run(1U, BE_MVP_RING_MIN_BYTES);
	CHECK(drain_takes == 5U && drain_visits == 6U);
	for (index = 0U; index < drain_takes; ++index)
		CHECK(drain_taken[index] == 0U);
	CHECK(drain_left(0U) == 0U && drain_left(1U) == 5U * 16U);

	/* A held ring (ring-full) is visited without a take; the other is
	 * drained alone, and the held records wait for a later drain. */
	SCENARIO();
	drain_rings(BE_MVP_RING_MIN_BYTES);
	drain_post(0U, 3U);
	drain_post(1U, 4U);
	drain_held_rings = 1U;
	drain_run(BE_MVP_DOMAINS, BE_MVP_RING_MIN_BYTES);
	CHECK(drain_takes == 4U && drain_visits == 10U);
	for (index = 0U; index < drain_takes; ++index)
		CHECK(drain_taken[index] == 1U);
	CHECK(drain_left(0U) == 3U * 16U && drain_left(1U) == 0U);
	drain_held_rings = 0U;
	drain_run(BE_MVP_DOMAINS, BE_MVP_RING_MIN_BYTES);
	CHECK(drain_takes == 7U && drain_visits == 17U);
	for (index = 4U; index < drain_takes; ++index)
		CHECK(drain_taken[index] == 0U);
	CHECK(drain_left(0U) == 0U);

	/* A writer as fast as hart 0 on one ring: the other's records are
	 * still taken in turn, and the bound ends the drain. */
	SCENARIO();
	drain_rings(BE_MVP_RING_MIN_BYTES);
	drain_post(0U, 2U);
	drain_post(1U, 3U);
	drain_fast_rings = 1U;
	drain_run(BE_MVP_DOMAINS, BE_MVP_RING_MIN_BYTES);
	CHECK(drain_visits == 2U * (BE_MVP_RING_MIN_BYTES / 16U + 1U));
	CHECK(drain_takes == BE_MVP_RING_MIN_BYTES / 16U + 1U + 3U);
	for (index = 0U; index < 6U; ++index)
		CHECK(drain_taken[index] == index % 2U);
	for (index = 6U; index < drain_takes; ++index)
		CHECK(drain_taken[index] == 0U);
	CHECK(drain_left(0U) == 2U * 16U && drain_left(1U) == 0U);

	/* The bound for the smallest ring and each layout ring, rings full
	 * and kept full: the scenario's, ring-full's, and the probes'. */
	drain_bound(BE_MVP_DOMAINS, BE_MVP_RING_MIN_BYTES);
	drain_bound(BE_MVP_DOMAINS, BE_MVP_VARIANT_OUTBOUND_RING_BYTES);
	drain_bound(BE_MVP_DOMAINS, BE_MVP_OUTBOUND_RING_BYTES);
	drain_bound(1U, BE_MVP_OUTBOUND_RING_BYTES);

	/* Arguments the drain refuses leave it over at once. */
	SCENARIO();
	be_mvp_drain_begin((struct be_mvp_drain *)0, BE_MVP_DOMAINS,
			   BE_MVP_OUTBOUND_RING_BYTES);
	CHECK(be_mvp_drain_next((const struct be_mvp_drain *)0) ==
	      BE_MVP_DRAIN_DONE);
	be_mvp_drain_visited((struct be_mvp_drain *)0, 1);
	for (index = 0U; index < 7U; ++index) {
		memset(&order, 0x5a, sizeof(order));
		be_mvp_drain_begin(&order, bad_rings[index], bad_bytes[index]);
		CHECK(be_mvp_drain_next(&order) == BE_MVP_DRAIN_DONE);
		be_mvp_drain_visited(&order, 1);
		CHECK(order.rings == 0U && order.next == 0U &&
		      order.idle == 0U && order.visits == 0U);
		CHECK(be_mvp_drain_next(&order) == BE_MVP_DRAIN_DONE);
	}
	/* A drain whose next ring is not one of its rings is over. */
	be_mvp_drain_begin(&order, BE_MVP_DOMAINS, BE_MVP_RING_MIN_BYTES);
	order.next = 2U;
	CHECK(be_mvp_drain_next(&order) == BE_MVP_DRAIN_DONE);
	be_mvp_drain_begin(&order, 1U, BE_MVP_RING_MIN_BYTES);
	order.next = 1U;
	CHECK(be_mvp_drain_next(&order) == BE_MVP_DRAIN_DONE);
}

static void expect_overlap(be_u64 e0, be_u64 s0, be_u64 e1, be_u64 s1,
			   be_u64 overlap, be_u64 shorter, int concurrent)
{
	be_u64 got = ALL_ONES;
	be_u64 got_shorter = ALL_ONES;

	CHECK(be_mvp_overlap(e0, s0, e1, s1, &got, &got_shorter) == 1);
	CHECK(got == overlap && got_shorter == shorter);
	CHECK(be_mvp_concurrent(got, got_shorter) == concurrent);
	/* The order of the domains does not matter. */
	got = ALL_ONES;
	got_shorter = ALL_ONES;
	CHECK(be_mvp_overlap(e1, s1, e0, s0, &got, &got_shorter) == 1);
	CHECK(got == overlap && got_shorter == shorter);
}

static void expect_no_overlap(be_u64 e0, be_u64 s0, be_u64 e1, be_u64 s1)
{
	be_u64 got = 0x77U;
	be_u64 got_shorter = 0x77U;

	CHECK(be_mvp_overlap(e0, s0, e1, s1, &got, &got_shorter) == 0);
	CHECK(got == 0x77U && got_shorter == 0x77U);
}

static void test_overlap(void)
{
	be_u64 overlap;
	be_u64 shorter;

	SCENARIO();
	/* Disjoint and touching: no overlap. */
	expect_overlap(0U, 10U, 20U, 30U, 0U, 10U, 0);
	expect_overlap(0U, 10U, 10U, 20U, 0U, 10U, 0);
	/* Nested and identical: all of the shorter. */
	expect_overlap(0U, 100U, 10U, 20U, 10U, 10U, 1);
	expect_overlap(5U, 15U, 5U, 15U, 10U, 10U, 1);
	expect_overlap(1U, 2U, 0U, ALL_ONES, 1U, 1U, 1);
	/* Exactly half passes; one tick less does not. */
	expect_overlap(0U, 10U, 5U, 15U, 5U, 10U, 1);
	expect_overlap(0U, 10U, 6U, 16U, 4U, 10U, 0);
	expect_overlap(0U, 10U, 5U, 1000U, 5U, 10U, 1);
	/* Odd lengths: at least half means the rounded-up half. */
	expect_overlap(0U, 5U, 2U, 7U, 3U, 5U, 1);
	expect_overlap(0U, 5U, 3U, 8U, 2U, 5U, 0);
	expect_overlap(0U, 1U, 0U, 1U, 1U, 1U, 1);
	/* Extremes. */
	expect_overlap(0U, ALL_ONES, 1U, ALL_ONES, ALL_ONES - 1U,
		       ALL_ONES - 1U, 1);
	expect_overlap(0U, ALL_ONES, 0U, ALL_ONES, ALL_ONES, ALL_ONES, 1);
	expect_overlap(ALL_ONES - 2U, ALL_ONES, ALL_ONES - 1U, ALL_ONES, 1U,
		       1U, 1);
	/* Empty or reversed intervals, and absent outputs. */
	expect_no_overlap(10U, 10U, 0U, 20U);
	expect_no_overlap(0U, 20U, 10U, 5U);
	expect_no_overlap(ALL_ONES, 0U, 0U, 1U);
	CHECK(be_mvp_overlap(0U, 1U, 0U, 1U, (be_u64 *)0, &shorter) == 0);
	CHECK(be_mvp_overlap(0U, 1U, 0U, 1U, &overlap, (be_u64 *)0) == 0);

	SCENARIO();
	CHECK(be_mvp_concurrent(0U, 0U) == 0);
	CHECK(be_mvp_concurrent(1U, 0U) == 0);
	CHECK(be_mvp_concurrent(0U, 1U) == 0);
	CHECK(be_mvp_concurrent(1U, 1U) == 1);
	CHECK(be_mvp_concurrent(1U, 2U) == 1);
	CHECK(be_mvp_concurrent(1U, 3U) == 0);
	CHECK(be_mvp_concurrent(2U, 3U) == 1);
	CHECK(be_mvp_concurrent(3U, 2U) == 0);
	CHECK(be_mvp_concurrent(BE_U64_C(0x8000000000000000), ALL_ONES) == 1);
	CHECK(be_mvp_concurrent(BE_U64_C(0x7fffffffffffffff), ALL_ONES) == 0);
	CHECK(be_mvp_concurrent(ALL_ONES, ALL_ONES) == 1);
	CHECK(be_mvp_concurrent(BE_U64_C(0x4000), BE_U64_C(0x8000)) == 1);
	CHECK(be_mvp_concurrent(BE_U64_C(0x3fff), BE_U64_C(0x8000)) == 0);

	/* A completed run: the overlap is printed even below the floor. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_SHUTDOWN);
	domain_time[1] = domain_time[0] - 0x18U;
	drive(1U, TARGET_SHUTDOWN);
	CHECK(ctl.done == 1U);
	CHECK(ctl.domain[0].entered == START + 0x120U &&
	      ctl.domain[0].shutdown == START + 0x150U);
	CHECK(ctl.domain[1].entered == START + 0x158U &&
	      ctl.domain[1].shutdown == START + 0x188U);
	overlap = ALL_ONES;
	CHECK(be_mvp_control_overlap(&ctl, &overlap) == 0);
	CHECK(overlap == 0U);
	SCENARIO();
	fresh();
	drive(0U, TARGET_SHUTDOWN);
	domain_time[1] = domain_time[0] - 0x48U;
	drive(1U, TARGET_SHUTDOWN);
	CHECK(ctl.domain[1].entered == START + 0x128U);
	CHECK(be_mvp_control_overlap(&ctl, &overlap) == 1);
	CHECK(overlap == 0x28U);
	/* Exactly half of 0x30 passes; 0x10 does not. */
	SCENARIO();
	fresh();
	drive(0U, TARGET_SHUTDOWN);
	domain_time[1] = domain_time[0] - 0x38U;
	drive(1U, TARGET_SHUTDOWN);
	CHECK(ctl.domain[1].entered == START + 0x138U);
	CHECK(be_mvp_control_overlap(&ctl, &overlap) == 1);
	CHECK(overlap == 0x18U);
	SCENARIO();
	fresh();
	drive(0U, TARGET_SHUTDOWN);
	domain_time[1] = domain_time[0] - 0x30U;
	drive(1U, TARGET_SHUTDOWN);
	CHECK(be_mvp_control_overlap(&ctl, &overlap) == 0);
	CHECK(overlap == 0x10U);
	CHECK(be_mvp_control_overlap(&ctl, (be_u64 *)0) == 0);
	CHECK(be_mvp_control_overlap((const struct be_mvp_control *)0,
				     &overlap) == 0 && overlap == 0U);
}

static void test_line_output(void)
{
	char output[BE_MVP_PRINT_LINE_BYTES + 8U];
	be_u64 index;

	SCENARIO();
	make_line(0U, 1U, "hello");
	memset(output, '#', sizeof(output));
	CHECK(be_mvp_line_output(&record, output, sizeof(output)) == 17U);
	CHECK(memcmp(output, "BE_MVP_G0: hello\n", 17U) == 0);
	CHECK(output[17] == '#');
	make_line(1U, 1U, "");
	CHECK(be_mvp_line_output(&record, output, sizeof(output)) == 12U);
	CHECK(memcmp(output, "BE_MVP_G1: \n", 12U) == 0);
	/* A full line: the prefix, 256 bytes, and LF, in exact capacity. */
	make_line(1U, 1U, "");
	for (index = 0U; index < BE_MVP_CONSOLE_LINE_BYTES; ++index)
		record.payload[index] = (be_u8)('a' + index % 26U);
	record.length = BE_MVP_CONSOLE_LINE_BYTES;
	CHECK(be_mvp_line_output(&record, output, BE_MVP_PRINT_LINE_BYTES) ==
	      BE_MVP_PRINT_LINE_BYTES);
	CHECK(memcmp(output, "BE_MVP_G1: abc", 14U) == 0);
	CHECK(output[BE_MVP_PRINT_LINE_BYTES - 2U] == 'v');
	CHECK(output[BE_MVP_PRINT_LINE_BYTES - 1U] == '\n');

	SCENARIO();
	memset(output, '#', sizeof(output));
	CHECK(be_mvp_line_output(&record, output,
				 BE_MVP_PRINT_LINE_BYTES - 1U) ==
	      BE_MVP_CONSOLE_INVALID);
	CHECK(output[0] == '#');
	make_line(0U, 1U, "hello");
	CHECK(be_mvp_line_output(&record, output, 16U) ==
	      BE_MVP_CONSOLE_INVALID);
	CHECK(be_mvp_line_output(&record, output, 17U) == 17U);
	memset(output, '#', sizeof(output));
	record.payload[1] = 0x7fU;
	CHECK(be_mvp_line_output(&record, output, sizeof(output)) ==
	      BE_MVP_CONSOLE_INVALID);
	make_line(0U, 1U, "hello");
	record.payload[4] = '\n';
	CHECK(be_mvp_line_output(&record, output, sizeof(output)) ==
	      BE_MVP_CONSOLE_INVALID);
	make_line(0U, 1U, "hello");
	record.type = BE_MVP_RECORD_PONG;
	CHECK(be_mvp_line_output(&record, output, sizeof(output)) ==
	      BE_MVP_CONSOLE_INVALID);
	make_line(2U, 1U, "hello");
	CHECK(be_mvp_line_output(&record, output, sizeof(output)) ==
	      BE_MVP_CONSOLE_INVALID);
	make_line(0U, 1U, "hello");
	record.length = BE_MVP_CONSOLE_LINE_BYTES + 1U;
	memset(record.payload, 'a', sizeof(record.payload));
	CHECK(be_mvp_line_output(&record, output, sizeof(output)) ==
	      BE_MVP_CONSOLE_INVALID);
	CHECK(be_mvp_line_output((const struct be_mvp_record *)0, output,
				 sizeof(output)) == BE_MVP_CONSOLE_INVALID);
	make_line(0U, 1U, "hello");
	CHECK(be_mvp_line_output(&record, (char *)0, sizeof(output)) ==
	      BE_MVP_CONSOLE_INVALID);
	CHECK(output[0] == '#');
}

/*
 * Pseudo-random runs: each domain's records in protocol order (READY,
 * ENTERED, its first LINE, more LINEs, the PONG, more LINEs, SHUTDOWN),
 * with a DENIAL after a quarter of its LINEs, at times that never go back,
 * merged in a random drain order. Each step is checked against the model,
 * and the run's counters and overlap against an independent computation.
 * Then the same run with one record dropped must fail or stay unfinished.
 */
#define SIM_RECORDS		64U

struct sim_record {
	be_u32 type;
	be_u32 domain;
	be_u64 time;
};

static struct sim_record sim[BE_MVP_DOMAINS][SIM_RECORDS];
static be_u64 sim_count[BE_MVP_DOMAINS];
static struct sim_record merged[2U * SIM_RECORDS];
static be_u64 merged_count;
static be_u64 sim_random;

static be_u64 next_random(void)
{
	sim_random ^= sim_random << 13;
	sim_random ^= sim_random >> 7;
	sim_random ^= sim_random << 17;
	return sim_random;
}

static void sim_push(be_u32 domain, be_u32 type, be_u64 *time)
{
	*time += next_random() % 4U == 0U ? 0U : next_random() % 0x1000U;
	sim[domain][sim_count[domain]].type = type;
	sim[domain][sim_count[domain]].domain = domain;
	sim[domain][sim_count[domain]].time = *time;
	++sim_count[domain];
}

/* A LINE, and after a quarter of them a DENIAL. */
static void sim_line(be_u32 domain, be_u64 *time)
{
	sim_push(domain, BE_MVP_RECORD_LINE, time);
	if (next_random() % 4U == 0U)
		sim_push(domain, BE_MVP_RECORD_DENIAL, time);
}

static void sim_build(void)
{
	be_u64 cursor[BE_MVP_DOMAINS] = { 0U, 0U };
	be_u32 domain;
	be_u64 index;

	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		be_u64 time = START + next_random() % 0x10000U;
		be_u64 before = next_random() % 6U;
		be_u64 after = next_random() % 24U;

		sim_count[domain] = 0U;
		sim_push(domain, BE_MVP_RECORD_READY, &time);
		sim_push(domain, BE_MVP_RECORD_ENTERED, &time);
		sim_line(domain, &time);
		for (index = 0U; index < before; ++index)
			sim_line(domain, &time);
		sim_push(domain, BE_MVP_RECORD_PONG, &time);
		for (index = 0U; index < after; ++index)
			sim_line(domain, &time);
		/* Entry to shutdown is never empty. */
		time += 1U;
		sim_push(domain, BE_MVP_RECORD_SHUTDOWN, &time);
	}
	merged_count = 0U;
	while (cursor[0] < sim_count[0] || cursor[1] < sim_count[1]) {
		domain = (be_u32)(next_random() & 1U);
		if (cursor[domain] == sim_count[domain])
			domain = 1U - domain;
		merged[merged_count++] = sim[domain][cursor[domain]++];
	}
}

/* The records of @type a domain sent, as its SHUTDOWN counts them. */
static be_u64 sim_sent(be_u32 domain, be_u32 type)
{
	be_u64 sent = 0U;
	be_u64 index;

	for (index = 0U; index < sim_count[domain]; ++index)
		if (sim[domain][index].type == type)
			++sent;
	return sent;
}

static be_u64 sim_lines(be_u32 domain)
{
	return sim_sent(domain, BE_MVP_RECORD_LINE);
}

/*
 * Replay the merged run, skipping record @skip (or none). Each SHUTDOWN
 * carries what its domain sent, whatever hart 0 drained.
 */
static void sim_replay(be_u64 skip)
{
	be_u64 lines[BE_MVP_DOMAINS] = { 0U, 0U };
	be_u64 denials[BE_MVP_DOMAINS] = { 0U, 0U };
	be_u64 index;

	be_mvp_control_init(&ctl, START, BUDGET, READY_WAIT);
	CHECK(be_mvp_control_channel(&ctl, maps, &channel) == 1);
	CHECK(be_mvp_control_started(&ctl, 0U, 1U) == 1);
	CHECK(be_mvp_control_started(&ctl, 1U, 2U) == 1);
	domain_denials[0] = sim_sent(0U, BE_MVP_RECORD_DENIAL);
	domain_denials[1] = sim_sent(1U, BE_MVP_RECORD_DENIAL);
	for (index = 0U; index < merged_count; ++index) {
		const struct sim_record *entry = &merged[index];
		be_u32 domain = entry->domain;
		enum be_mvp_step step;

		/* The domain numbers what it sent, whatever is drained. */
		if (entry->type == BE_MVP_RECORD_DENIAL)
			++denials[domain];
		if (index == skip)
			continue;
		switch (entry->type) {
		case BE_MVP_RECORD_READY:
			make(entry->type, domain, entry->time,
			     BE_MVP_READY_WORDS);
			break;
		case BE_MVP_RECORD_ENTERED:
			make(entry->type, domain, entry->time,
			     BE_MVP_ENTERED_WORDS);
			break;
		case BE_MVP_RECORD_LINE:
			make_line(domain, entry->time, "line");
			++lines[domain];
			break;
		case BE_MVP_RECORD_PONG:
			make_pong(domain, entry->time, 1U);
			break;
		case BE_MVP_RECORD_DENIAL:
			/* G0's load beside the page; G1's store to it, or
			 * its load of the probe's GPA. */
			if (domain == 0U)
				make_denial(domain, entry->time,
					    denials[domain], LOAD, UNMAPPED,
					    BESIDE_GPA);
			else if (denials[domain] % 2U == 1U)
				make_denial(domain, entry->time,
					    denials[domain], STORE, READ_ONLY,
					    PAGE_GPA + 0xff8U);
			else
				make_denial(domain, entry->time,
					    denials[domain], LOAD, UNMAPPED,
					    PROBE_GPA);
			break;
		default:
			make_shutdown(domain, entry->time, sim[domain][1].time,
				      sim_lines(domain),
				      0x40U * sim_lines(domain));
			break;
		}
		step = apply(domain);
		if (skip < merged_count) {
			if (step == STEP_INVALID)
				return;
			continue;
		}
		CHECK(step != STEP_INVALID);
		CHECK(result.ping == (entry->type == BE_MVP_RECORD_LINE &&
				      lines[domain] == 1U ? 1U : 0U));
		CHECK(result.done == (entry->type == BE_MVP_RECORD_SHUTDOWN &&
				      ctl.domain[1U - domain].phase ==
					      BE_MVP_DOMAIN_SHUTDOWN ?
				      1U : 0U));
		CHECK(ctl.domain[domain].lines == lines[domain]);
		CHECK(ctl.domain[domain].denials == denials[domain]);
	}
}

static void test_simulation(void)
{
	unsigned int run;

	sim_random = BE_U64_C(0x9e3779b97f4a7c15);
	for (run = 0U; run < 400U; ++run) {
		be_u64 e0;
		be_u64 s0;
		be_u64 e1;
		be_u64 s1;
		be_u64 low;
		be_u64 high;
		be_u64 shorter;
		be_u64 expected;
		be_u64 overlap = ALL_ONES;
		be_u64 skip;

		SCENARIO();
		sim_build();
		sim_replay(ALL_ONES);
		CHECK(ctl.done == 1U && ctl.failed == 0U);
		CHECK(ctl.records == merged_count);
		CHECK(ctl.domain[0].records == sim_count[0] &&
		      ctl.domain[1].records == sim_count[1]);
		e0 = sim[0][1].time;
		e1 = sim[1][1].time;
		s0 = sim[0][sim_count[0] - 1U].time;
		s1 = sim[1][sim_count[1] - 1U].time;
		CHECK(ctl.domain[0].entered == e0 &&
		      ctl.domain[1].entered == e1);
		CHECK(ctl.domain[0].shutdown == s0 &&
		      ctl.domain[1].shutdown == s1);
		low = e0 > e1 ? e0 : e1;
		high = s0 < s1 ? s0 : s1;
		expected = high > low ? high - low : 0U;
		shorter = s0 - e0 < s1 - e1 ? s0 - e0 : s1 - e1;
		CHECK(be_mvp_control_overlap(&ctl, &overlap) ==
		      (2U * expected >= shorter ? 1 : 0));
		CHECK(overlap == expected);
		/* Any one record dropped: the run fails or never finishes. */
		skip = next_random() % merged_count;
		sim_replay(skip);
		CHECK(ctl.failed == 1U || ctl.done == 0U);
	}
}

int main(void)
{
	test_constants();
	test_hgatp();
	test_bindings();
	test_block_fill();
	test_block_check();
	test_state_page();
	test_control_init();
	test_started();
	test_protocol();
	test_order();
	test_payloads();
	test_line_bytes();
	test_times();
	test_fail_paths();
	test_denial();
	test_pages();
	test_mgmt();
	test_saturation();
	test_wake();
	test_drain_order();
	test_overlap();
	test_line_output();
	test_simulation();
	printf("BE_MVP_HART_CHECK: PASS\n");
	printf("BE_MVP_HART_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_MVP_HART_CHECK: assertions=%lu\n", assertions);
	return 0;
}
