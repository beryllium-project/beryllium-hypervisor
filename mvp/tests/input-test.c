// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the MVP's console input
 *          (planning/mvp-m7-plan.md, D-1, D-3, and D-4; mvp-input.h): the
 *          focus parser over every byte value in every state, and in no
 *          state, against an oracle written here from the plan's text, not
 *          from the parser's table; hart 0's routing of a scripted byte
 *          stream for two domains, one of them granted, into their input
 *          rings, with the focus reports, the bytes delivered and their
 *          SHA-256, and the drops by reason, the no-grant and not-running
 *          drops among them; the input ring's drop rule, under which a
 *          full ring drops and counts the bytes and never fails the
 *          writer's view; the poll's next deadline, never past the
 *          budget's end, and none when input is not armed; the domains
 *          hart 0 holds running; and a domain hart's served DBCN read: the
 *          SBI core's write-authority rule (a2, a zero count, an
 *          overflowing range, a range across the window's end, on the
 *          channel page or a declared page, an ungranted domain's DENIED)
 *          and the service's copy through the stage (a count above the
 *          queue, a count below a staged record, whose rest stays staged),
 *          with no guest byte written and no queued byte taken on a
 *          refusal.
 * Trust:   host evidence only: no fence, second hart, firmware console,
 *          QEMU, or hardware behaviour is exercised.
 * Scope:   the MVP line from M7.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mvp-gstage.h"
#include "mvp-hart.h"
#include "mvp-input.h"
#include "mvp-layout.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_INPUT_CHECK: assertion failed: " \
			       "%s:%d: %s\n", __FILE__, __LINE__, \
			       #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define ALL_ONES		(~BE_U64_C(0))
#define TICKS			BE_MVP_INPUT_POLL_TICKS
#define WINDOW_GPA		BE_MVP_GUEST_GPA
#define WINDOW_BYTES		BE_MVP_GUEST_BYTES
#define WINDOW_HPA		BE_MVP_G0_HPA
#define ECALL_PC		BE_U64_C(0x80200400)
#define FAKE_BYTES		BE_U64_C(0x1000)

/* The oracle's states and kinds, by the plan's names (D-3). */
enum oracle_state { AT_LINE_START = 0, AT_AFTER_PREFIX = 1, AT_IN_LINE = 2 };

struct oracle {
	enum be_mvp_focus_kind kind;
	be_u32 domain;
	enum be_mvp_input_drop reason;
	be_u8 byte;
	enum oracle_state next;
};

/*
 * D-3's text, rule by rule: at line start the prefix enters after-prefix;
 * there a domain digit sets the focus and returns to line start, a second
 * prefix delivers one literal prefix and enters in-line, and any other
 * byte is dropped as a bad sequence and returns to line start; any other
 * byte at line start or in a line is delivered, and CR or LF returns to
 * line start. The prefix at line start is held: no output of the three.
 */
static struct oracle expect_step(enum oracle_state state, unsigned int byte)
{
	struct oracle out = { BE_MVP_FOCUS_DELIVER, 0U, BE_MVP_DROP_NO_FOCUS,
			      0U, AT_IN_LINE };
	int ends_line = byte == 13U || byte == 10U;

	if (state == AT_AFTER_PREFIX) {
		if (byte == 48U || byte == 49U) {
			out.kind = BE_MVP_FOCUS_SELECT;
			out.domain = byte - 48U;
			out.next = AT_LINE_START;
		} else if (byte == 126U) {
			out.byte = 126U;
			out.next = AT_IN_LINE;
		} else {
			out.kind = BE_MVP_FOCUS_DROP;
			out.reason = BE_MVP_DROP_BAD_SEQUENCE;
			out.next = AT_LINE_START;
		}
		return out;
	}
	if (state == AT_LINE_START && byte == 126U) {
		out.kind = BE_MVP_FOCUS_HOLD;
		out.next = AT_AFTER_PREFIX;
		return out;
	}
	out.byte = (be_u8)byte;
	out.next = ends_line ? AT_LINE_START : AT_IN_LINE;
	return out;
}

static void test_parser(void)
{
	static const unsigned int bad_states[] = {
		3U, 4U, 7U, 0x7fffffffU,
	};
	struct be_mvp_focus_out out;
	unsigned int state;
	unsigned int byte;
	unsigned int index;

	/* Every byte in every state: the output and the next state. */
	for (state = 0U; state < 3U; ++state) {
		SCENARIO();
		for (byte = 0U; byte < 256U; ++byte) {
			struct oracle want = expect_step(
				(enum oracle_state)state, byte);
			enum be_mvp_focus_state next;

			memset(&out, 0xa5, sizeof(out));
			next = be_mvp_focus_step(
				(enum be_mvp_focus_state)state, (be_u8)byte,
				&out);
			CHECK((unsigned int)next == (unsigned int)want.next);
			CHECK(out.kind == want.kind);
			CHECK(out.domain == want.domain);
			CHECK(out.reason == want.reason);
			CHECK(out.byte == want.byte);
			/* Without an output, the same next state. */
			CHECK(be_mvp_focus_step((enum be_mvp_focus_state)state,
						(be_u8)byte,
						(struct be_mvp_focus_out *)0) ==
			      next);
		}
	}
	/* No state but the three: a bad sequence, and a line starts. */
	SCENARIO();
	for (index = 0U; index < sizeof(bad_states) / sizeof(bad_states[0]);
	     ++index) {
		for (byte = 0U; byte < 256U; byte += 17U) {
			memset(&out, 0xa5, sizeof(out));
			CHECK(be_mvp_focus_step(
				      (enum be_mvp_focus_state)bad_states[index],
				      (be_u8)byte, &out) ==
			      BE_MVP_FOCUS_LINE_START);
			CHECK(out.kind == BE_MVP_FOCUS_DROP &&
			      out.reason == BE_MVP_DROP_BAD_SEQUENCE &&
			      out.domain == 0U && out.byte == 0U);
		}
	}
	/* The reasons' names, as BE_MVP:17 and :18 print them. */
	SCENARIO();
	CHECK(strcmp(be_mvp_input_drop_name(BE_MVP_DROP_NO_FOCUS),
		     "no-focus") == 0);
	CHECK(strcmp(be_mvp_input_drop_name(BE_MVP_DROP_NO_GRANT),
		     "no-grant") == 0);
	CHECK(strcmp(be_mvp_input_drop_name(BE_MVP_DROP_NOT_RUNNING),
		     "not-running") == 0);
	CHECK(strcmp(be_mvp_input_drop_name(BE_MVP_DROP_RING_FULL),
		     "ring-full") == 0);
	CHECK(strcmp(be_mvp_input_drop_name(BE_MVP_DROP_BAD_SEQUENCE),
		     "bad-sequence") == 0);
	CHECK(strcmp(be_mvp_input_drop_name(BE_MVP_DROP_BEFORE_ARMED),
		     "before-armed") == 0);
	CHECK(strcmp(be_mvp_input_drop_name(BE_MVP_DROP_REASONS),
		     "invalid") == 0);
	CHECK(strcmp(be_mvp_input_drop_name((enum be_mvp_input_drop)99),
		     "invalid") == 0);
}

/* Each domain's input ring: hart 0's writer view and the domain's reader. */
static be_u8 ring_bytes[BE_MVP_DOMAINS][BE_MVP_INPUT_RING_BYTES];
static struct be_mvp_ring_index ring_index[BE_MVP_DOMAINS][2];
static struct be_mvp_ring writers[BE_MVP_DOMAINS];
static struct be_mvp_ring readers[BE_MVP_DOMAINS];
static struct be_mvp_record taken;
static struct be_mvp_input input;

static void open_ring(be_u32 domain, be_u64 capacity)
{
	memset(ring_bytes[domain], 0, sizeof(ring_bytes[domain]));
	be_mvp_ring_reset(&ring_index[domain][0], &ring_index[domain][1]);
	CHECK(be_mvp_ring_init(&writers[domain], ring_bytes[domain], capacity,
			       &ring_index[domain][0], &ring_index[domain][1],
			       BE_MVP_RECORDS_INPUT, domain,
			       BE_MVP_RING_WRITER) == 1);
	CHECK(be_mvp_ring_init(&readers[domain], ring_bytes[domain], capacity,
			       &ring_index[domain][0], &ring_index[domain][1],
			       BE_MVP_RECORDS_INPUT, domain,
			       BE_MVP_RING_READER) == 1);
}

/* One report, as the event says, for the scripted stream's log. */
struct report {
	enum be_mvp_input_report report;
	be_u32 domain;
	enum be_mvp_input_drop reason;
};

static struct report reports[64];
static unsigned int report_count;

static void log_event(const struct be_mvp_input_event *event)
{
	if (event->report == BE_MVP_INPUT_QUIET)
		return;
	CHECK(report_count < sizeof(reports) / sizeof(reports[0]));
	reports[report_count].report = event->report;
	reports[report_count].domain = event->domain;
	reports[report_count].reason = event->reason;
	++report_count;
}

/*
 * One poll, as hart 0's runtime runs it: every byte of @text routed with
 * @running, then each domain's batch flushed into its ring at @now and
 * published, every report logged.
 */
static void poll(const char *text, be_u64 length, be_u64 running, be_u64 now)
{
	struct be_mvp_input_event event;
	be_u64 index;
	be_u32 domain;

	be_mvp_input_poll_begin(&input);
	for (index = 0U; index < length; ++index) {
		be_mvp_input_byte(&input, (be_u8)text[index], running, &event);
		log_event(&event);
	}
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		be_u64 posted = be_mvp_input_flush(&input, domain,
						   &writers[domain], now,
						   &event);

		CHECK(posted != BE_MVP_INPUT_FAILED);
		if (posted != 0U)
			CHECK(be_mvp_ring_publish(&writers[domain]) == 1);
		log_event(&event);
	}
	be_mvp_input_poll_end(&input);
}

static int report_is(unsigned int index, enum be_mvp_input_report report,
		     be_u32 domain, enum be_mvp_input_drop reason)
{
	return index < report_count && reports[index].report == report &&
	       (report != BE_MVP_INPUT_FOCUSED ||
		reports[index].domain == domain) &&
	       (report != BE_MVP_INPUT_FIRST_DROP ||
		reports[index].reason == reason);
}

/* The next INPUT record in @domain's ring holds exactly @text. */
static void expect_input(be_u32 domain, const char *text, be_u64 time)
{
	be_u64 length = strlen(text);

	CHECK(be_mvp_ring_take(&readers[domain], &taken) ==
	      BE_MVP_RING_RECORD);
	CHECK(taken.type == BE_MVP_RECORD_INPUT && taken.domain == domain &&
	      taken.length == length && taken.time == time);
	CHECK(memcmp(taken.payload, text, length) == 0);
}

static int hex_is(const be_u8 *digest, const char *hex)
{
	char text[2U * BE_MVP_SHA256_BYTES + 1U];
	be_u32 index;

	for (index = 0U; index < BE_MVP_SHA256_BYTES; ++index)
		snprintf(&text[2U * index], 3U, "%02x", digest[index]);
	return strcmp(text, hex) == 0;
}

static void test_arm(void)
{
	be_u64 grants;

	SCENARIO();
	/* No grant, or a grant naming a domain that does not exist: not
	 * armed, and zeroed. */
	memset(&input, 0x5a, sizeof(input));
	CHECK(be_mvp_input_arm(&input, 0U) == 0);
	CHECK(input.armed == 0U && input.grants == 0U && input.read == 0U);
	CHECK(be_mvp_input_arm(&input, 4U) == 0 && input.armed == 0U);
	CHECK(be_mvp_input_arm(&input, 5U) == 0 && input.armed == 0U);
	CHECK(be_mvp_input_arm(&input, ALL_ONES) == 0 && input.armed == 0U);
	CHECK(be_mvp_input_arm((struct be_mvp_input *)0, 1U) == 0);
	for (grants = 1U; grants <= 3U; ++grants) {
		memset(&input, 0x5a, sizeof(input));
		CHECK(be_mvp_input_arm(&input, grants) == 1);
		CHECK(input.armed == 1U && input.discard == 1U &&
		      input.grants == grants &&
		      input.state == BE_MVP_FOCUS_LINE_START &&
		      input.focus == BE_MVP_INPUT_NO_FOCUS &&
		      input.read == 0U && input.announced == 0U &&
		      input.delivered[0] == 0U && input.delivered[1] == 0U &&
		      input.pending[0] == 0U && input.pending[1] == 0U);
	}
	/* A byte for an input never armed is not even counted. */
	{
		struct be_mvp_input_event event;

		memset(&input, 0, sizeof(input));
		be_mvp_input_byte(&input, 'a', 3U, &event);
		CHECK(event.report == BE_MVP_INPUT_QUIET && input.read == 0U);
		be_mvp_input_byte((struct be_mvp_input *)0, 'a', 3U, &event);
		CHECK(event.report == BE_MVP_INPUT_QUIET);
		be_mvp_input_byte(&input, 'a', 3U,
				  (struct be_mvp_input_event *)0);
	}
}

/*
 * A scripted stream for two domains, domain 0 alone granted: what the
 * firmware held before arming; input with no focus; a selection of the
 * domain without the grant; the granted domain's selection, a line, a
 * doubled prefix, a bad sequence, and a second selection; input while
 * the focused domain is not running; and a last line.
 */
static void test_routing(void)
{
	static const char held[] = "ab~0\n";
	static const char typed[] = "x\n~1~0hi\n~~\n~q~0ok\n";
	be_u8 digest[BE_MVP_SHA256_BYTES];

	SCENARIO();
	open_ring(0U, BE_MVP_INPUT_RING_BYTES);
	open_ring(1U, BE_MVP_INPUT_RING_BYTES);
	report_count = 0U;
	CHECK(be_mvp_input_arm(&input, 1U) == 1);
	/* The first poll: what the firmware held, dropped, the parser not
	 * stepped; one report. */
	poll(held, sizeof(held) - 1U, 3U, 0x100U);
	CHECK(input.read == 5U && input.discard == 0U &&
	      input.dropped[BE_MVP_DROP_BEFORE_ARMED] == 5U &&
	      input.state == BE_MVP_FOCUS_LINE_START &&
	      input.focus == BE_MVP_INPUT_NO_FOCUS);
	CHECK(report_count == 1U &&
	      report_is(0U, BE_MVP_INPUT_FIRST_DROP, 0U,
			BE_MVP_DROP_BEFORE_ARMED));
	CHECK(be_mvp_ring_acquire(&readers[0]) == 0U &&
	      be_mvp_ring_acquire(&readers[1]) == 0U);

	poll(typed, sizeof(typed) - 1U, 3U, 0x200U);
	CHECK(input.read == 24U && input.focus == 0U);
	CHECK(input.delivered[0] == 8U && input.delivered[1] == 0U);
	CHECK(input.dropped[BE_MVP_DROP_NO_FOCUS] == 2U &&
	      input.dropped[BE_MVP_DROP_NO_GRANT] == 1U &&
	      input.dropped[BE_MVP_DROP_BAD_SEQUENCE] == 1U &&
	      input.dropped[BE_MVP_DROP_NOT_RUNNING] == 0U &&
	      input.dropped[BE_MVP_DROP_RING_FULL] == 0U);
	/* Five prefixes held and two selections: 19 = 8 + 4 + 5 + 2. */
	CHECK(report_count == 6U &&
	      report_is(1U, BE_MVP_INPUT_FIRST_DROP, 0U,
			BE_MVP_DROP_NO_FOCUS) &&
	      report_is(2U, BE_MVP_INPUT_FIRST_DROP, 0U,
			BE_MVP_DROP_NO_GRANT) &&
	      report_is(3U, BE_MVP_INPUT_FOCUSED, 0U, BE_MVP_DROP_NO_FOCUS) &&
	      report_is(4U, BE_MVP_INPUT_FIRST_DROP, 0U,
			BE_MVP_DROP_BAD_SEQUENCE) &&
	      report_is(5U, BE_MVP_INPUT_FOCUSED, 0U, BE_MVP_DROP_NO_FOCUS));
	CHECK(be_mvp_ring_acquire(&readers[0]) != 0U);
	expect_input(0U, "hi\n~\nok\n", 0x200U);
	CHECK(be_mvp_ring_take(&readers[0], &taken) == BE_MVP_RING_EMPTY);
	CHECK(be_mvp_ring_release(&readers[0]) == 1);
	CHECK(be_mvp_ring_acquire(&readers[1]) == 0U);

	/* The focused domain not running (paused): dropped, reported once;
	 * the parser still steps, so the line ends. */
	poll("zz\n", 3U, 2U, 0x300U);
	CHECK(input.dropped[BE_MVP_DROP_NOT_RUNNING] == 3U &&
	      input.delivered[0] == 8U && report_count == 7U &&
	      report_is(6U, BE_MVP_INPUT_FIRST_DROP, 0U,
			BE_MVP_DROP_NOT_RUNNING));
	CHECK(be_mvp_ring_acquire(&readers[0]) == 0U);
	/* Running again: the ungranted selection again, reported no more,
	 * the focus kept, and the last line delivered. */
	poll("~1end\n", 6U, 3U, 0x400U);
	CHECK(input.read == 33U && input.focus == 0U &&
	      input.delivered[0] == 12U && input.delivered[1] == 0U &&
	      input.dropped[BE_MVP_DROP_NO_GRANT] == 2U && report_count == 7U);
	CHECK(be_mvp_ring_acquire(&readers[0]) != 0U);
	expect_input(0U, "end\n", 0x400U);
	CHECK(be_mvp_ring_release(&readers[0]) == 1);
	CHECK(be_mvp_ring_acquire(&readers[1]) == 0U &&
	      writers[1].failed == 0U && readers[1].failed == 0U);
	/* The accounting: read 33 = delivered 12 + dropped 13 + six held
	 * prefixes + two selections; each domain's digest of what it was
	 * given. */
	CHECK(input.dropped[BE_MVP_DROP_NO_FOCUS] +
	      input.dropped[BE_MVP_DROP_NO_GRANT] +
	      input.dropped[BE_MVP_DROP_NOT_RUNNING] +
	      input.dropped[BE_MVP_DROP_RING_FULL] +
	      input.dropped[BE_MVP_DROP_BAD_SEQUENCE] +
	      input.dropped[BE_MVP_DROP_BEFORE_ARMED] == 13U);
	be_mvp_input_digest(&input, 0U, digest);
	CHECK(hex_is(digest, "1cb59fb9c53ca7eab4897e1d778030be"
		     "3826abc45caa5ee25d9ff96e5ba8b586"));
	/* The running digest goes on after a read of it. */
	be_mvp_input_digest(&input, 0U, digest);
	CHECK(hex_is(digest, "1cb59fb9c53ca7eab4897e1d778030be"
		     "3826abc45caa5ee25d9ff96e5ba8b586"));
	be_mvp_input_digest(&input, 1U, digest);
	CHECK(hex_is(digest, "e3b0c44298fc1c149afbf4c8996fb924"
		     "27ae41e4649b934ca495991b7852b855"));
	/* Another domain, or no input: all zero. */
	memset(digest, 0xa5, sizeof(digest));
	be_mvp_input_digest(&input, 2U, digest);
	CHECK(digest[0] == 0U && digest[31] == 0U);
	memset(digest, 0xa5, sizeof(digest));
	be_mvp_input_digest((const struct be_mvp_input *)0, 0U, digest);
	CHECK(digest[0] == 0U && digest[31] == 0U);
	be_mvp_input_digest(&input, 0U, (be_u8 *)0);

	/* Both domains granted: each selection takes its own bytes, and no
	 * byte reaches the other domain. */
	SCENARIO();
	open_ring(0U, BE_MVP_INPUT_RING_BYTES);
	open_ring(1U, BE_MVP_INPUT_RING_BYTES);
	report_count = 0U;
	CHECK(be_mvp_input_arm(&input, 3U) == 1);
	poll("", 0U, 3U, 0x10U);
	CHECK(report_count == 0U && input.discard == 0U);
	poll("~0ab\n~1cd\n~0e", 13U, 3U, 0x20U);
	CHECK(report_count == 3U &&
	      report_is(0U, BE_MVP_INPUT_FOCUSED, 0U, BE_MVP_DROP_NO_FOCUS) &&
	      report_is(1U, BE_MVP_INPUT_FOCUSED, 1U, BE_MVP_DROP_NO_FOCUS) &&
	      report_is(2U, BE_MVP_INPUT_FOCUSED, 0U, BE_MVP_DROP_NO_FOCUS));
	CHECK(input.delivered[0] == 4U && input.delivered[1] == 3U);
	CHECK(be_mvp_ring_acquire(&readers[0]) != 0U &&
	      be_mvp_ring_acquire(&readers[1]) != 0U);
	expect_input(0U, "ab\ne", 0x20U);
	expect_input(1U, "cd\n", 0x20U);
	/* Domain 1 shut down: its bytes dropped as not running; a focus on
	 * it still taken, the configuration granting it. */
	poll("\n~1zz\n", 6U, 1U, 0x30U);
	CHECK(input.focus == 1U && input.delivered[0] == 5U &&
	      input.delivered[1] == 3U &&
	      input.dropped[BE_MVP_DROP_NOT_RUNNING] == 3U);
}

/*
 * The input ring's drop rule (D-1): a ring with no room for the whole
 * batch takes what fits as one record and the rest is dropped as
 * ring-full; a ring with no room drops it all; neither fails the writer's
 * view, which only a malformed ring does.
 */
static void test_ring_full(void)
{
	char text[300];
	struct be_mvp_input_event event;
	be_u64 index;

	for (index = 0U; index < sizeof(text); ++index)
		text[index] = (char)('a' + index % 26U);
	SCENARIO();
	open_ring(0U, BE_MVP_RING_MIN_BYTES);
	open_ring(1U, BE_MVP_INPUT_RING_BYTES);
	report_count = 0U;
	CHECK(be_mvp_input_arm(&input, 1U) == 1);
	poll("", 0U, 1U, 0U);
	poll("~0", 2U, 1U, 1U);
	/* One poll of 300 bytes: a batch holds 256, the rest ring-full. */
	poll(text, 300U, 1U, 2U);
	CHECK(input.delivered[0] == 256U &&
	      input.dropped[BE_MVP_DROP_RING_FULL] == 44U);
	CHECK(report_count == 2U &&
	      report_is(1U, BE_MVP_INPUT_FIRST_DROP, 0U,
			BE_MVP_DROP_RING_FULL));
	/* 512 bytes hold 272, so 224 more fit, aligned to 8; 32 dropped. */
	CHECK(be_mvp_ring_room(&writers[0]) == 224U);
	poll(text, 256U, 1U, 3U);
	CHECK(input.delivered[0] == 480U &&
	      input.dropped[BE_MVP_DROP_RING_FULL] == 76U);
	CHECK(writers[0].failed == 0U && be_mvp_ring_room(&writers[0]) == 0U);
	/* No room: every byte dropped, the view not failed, nothing posted. */
	poll("full\n", 5U, 1U, 4U);
	CHECK(input.delivered[0] == 480U &&
	      input.dropped[BE_MVP_DROP_RING_FULL] == 81U &&
	      writers[0].failed == 0U && report_count == 2U);
	/* The reader takes one record and frees its room; the next fits. */
	CHECK(be_mvp_ring_acquire(&readers[0]) != 0U);
	CHECK(be_mvp_ring_take(&readers[0], &taken) == BE_MVP_RING_RECORD &&
	      taken.length == 256U && memcmp(taken.payload, text, 256U) == 0);
	CHECK(be_mvp_ring_release(&readers[0]) == 1);
	poll("next\n", 5U, 1U, 5U);
	CHECK(input.delivered[0] == 485U && writers[0].failed == 0U);
	CHECK(be_mvp_ring_acquire(&readers[0]) != 0U);
	CHECK(be_mvp_ring_take(&readers[0], &taken) == BE_MVP_RING_RECORD &&
	      taken.length == 224U && memcmp(taken.payload, text, 224U) == 0);
	expect_input(0U, "next\n", 5U);
	/* An empty ring's room: one whole record. */
	open_ring(0U, BE_MVP_INPUT_RING_BYTES);
	CHECK(be_mvp_ring_room(&writers[0]) == BE_MVP_RECORD_PAYLOAD_MAX);
	/* Room on a reader's view, or on none, is 0. */
	CHECK(be_mvp_ring_room(&readers[0]) == 0U);
	CHECK(be_mvp_ring_room((struct be_mvp_ring *)0) == 0U);

	/* A malformed tail fails the view, and the flush, its batch kept. */
	SCENARIO();
	open_ring(0U, BE_MVP_INPUT_RING_BYTES);
	CHECK(be_mvp_input_arm(&input, 1U) == 1);
	poll("", 0U, 1U, 1U);
	poll("~0", 2U, 1U, 2U);
	be_mvp_input_poll_begin(&input);
	be_mvp_input_byte(&input, 'k', 1U, &event);
	ring_index[0][1].value = 3U;
	CHECK(be_mvp_input_flush(&input, 0U, &writers[0], 3U, &event) ==
	      BE_MVP_INPUT_FAILED);
	CHECK(writers[0].failed != 0U && input.pending[0] == 1U &&
	      input.delivered[0] == 0U);
	/* Absent or invalid input. */
	CHECK(be_mvp_input_flush(&input, 2U, &writers[0], 3U, &event) ==
	      BE_MVP_INPUT_FAILED);
	CHECK(be_mvp_input_flush(&input, 0U, (struct be_mvp_ring *)0, 3U,
				 &event) == BE_MVP_INPUT_FAILED);
	CHECK(be_mvp_input_flush((struct be_mvp_input *)0, 0U, &writers[0],
				 3U, &event) == BE_MVP_INPUT_FAILED);
	CHECK(be_mvp_input_flush(&input, 0U, &writers[0], 3U,
				 (struct be_mvp_input_event *)0) ==
	      BE_MVP_INPUT_FAILED);
	input.pending[0] = BE_MVP_INPUT_POLL_MAX + 1U;
	CHECK(be_mvp_input_flush(&input, 0U, &writers[0], 3U, &event) ==
	      BE_MVP_INPUT_FAILED);
	memset(&input, 0, sizeof(input));
	CHECK(be_mvp_input_flush(&input, 0U, &writers[0], 3U, &event) ==
	      BE_MVP_INPUT_FAILED);
}

/* The poll's deadline (D-1): the earlier of the next poll and the end. */
static void test_rearm(void)
{
	be_u64 deadline;

	SCENARIO();
	memset(&input, 0, sizeof(input));
	deadline = 77U;
	CHECK(be_mvp_input_rearm(&input, 100U, BE_MVP_RUN_BUDGET, 200U,
				 &deadline) == 0 && deadline == 77U);
	CHECK(be_mvp_input_rearm((const struct be_mvp_input *)0, 0U, 1U, 0U,
				 &deadline) == 0 && deadline == 77U);
	CHECK(be_mvp_input_arm(&input, 2U) == 1);
	CHECK(be_mvp_input_rearm(&input, 100U, BE_MVP_RUN_BUDGET, 200U,
				 (be_u64 *)0) == 0);
	CHECK(TICKS == BE_U64_C(1) << 18);
	CHECK(be_mvp_input_rearm(&input, 100U, BE_MVP_RUN_BUDGET, 200U,
				 &deadline) == 1 && deadline == 200U + TICKS);
	/* At the barrier itself, as hart 0's first arming. */
	CHECK(be_mvp_input_rearm(&input, 100U, BE_MVP_RUN_BUDGET, 100U,
				 &deadline) == 1 && deadline == 100U + TICKS);
	/* Within one poll of the end, at the end, past it: the end. */
	CHECK(be_mvp_input_rearm(&input, 100U, BE_MVP_RUN_BUDGET,
				 100U + BE_MVP_RUN_BUDGET - TICKS, &deadline) ==
	      1 && deadline == 100U + BE_MVP_RUN_BUDGET);
	CHECK(be_mvp_input_rearm(&input, 100U, BE_MVP_RUN_BUDGET,
				 100U + BE_MVP_RUN_BUDGET - TICKS - 1U,
				 &deadline) == 1 &&
	      deadline == 100U + BE_MVP_RUN_BUDGET - 1U);
	CHECK(be_mvp_input_rearm(&input, 100U, BE_MVP_RUN_BUDGET,
				 100U + BE_MVP_RUN_BUDGET - 1U, &deadline) ==
	      1 && deadline == 100U + BE_MVP_RUN_BUDGET);
	CHECK(be_mvp_input_rearm(&input, 100U, BE_MVP_RUN_BUDGET,
				 ALL_ONES - 3U, &deadline) == 1 &&
	      deadline == 100U + BE_MVP_RUN_BUDGET);
	/* A budget shorter than one poll: its end. */
	CHECK(be_mvp_input_rearm(&input, 100U, 1000U, 100U, &deadline) == 1 &&
	      deadline == 1100U);
	/* Each sum saturates. */
	CHECK(be_mvp_input_rearm(&input, ALL_ONES - 10U, 100U,
				 ALL_ONES - 20U, &deadline) == 1 &&
	      deadline == ALL_ONES);
	CHECK(be_mvp_input_rearm(&input, ALL_ONES - 10U, 100U, 5U,
				 &deadline) == 1 && deadline == 5U + TICKS);
}

/* The domains hart 0 holds running, the only ones input reaches. */
static void test_running(void)
{
	static const enum be_mvp_domain_phase stopped[] = {
		BE_MVP_DOMAIN_NONE, BE_MVP_DOMAIN_SHUTDOWN,
		BE_MVP_DOMAIN_FAILED, BE_MVP_DOMAIN_PAUSED,
		BE_MVP_DOMAIN_TERMINATED,
	};
	static const enum be_mvp_domain_phase running[] = {
		BE_MVP_DOMAIN_STARTED, BE_MVP_DOMAIN_READY,
		BE_MVP_DOMAIN_ENTERED,
	};
	struct be_mvp_mgmt_state mgmt;
	struct be_mvp_control ctl;
	unsigned int index;

	SCENARIO();
	be_mvp_control_init(&ctl, 100U, 1000U, 500U);
	CHECK(be_mvp_control_running(&ctl) == 0U);
	for (index = 0U; index < sizeof(running) / sizeof(running[0]);
	     ++index) {
		ctl.domain[0].phase = running[index];
		ctl.domain[1].phase = stopped[index];
		CHECK(be_mvp_control_running(&ctl) == 1U);
		ctl.domain[1].phase = running[index];
		CHECK(be_mvp_control_running(&ctl) == 3U);
	}
	for (index = 0U; index < sizeof(stopped) / sizeof(stopped[0]);
	     ++index) {
		ctl.domain[0].phase = stopped[index];
		CHECK(be_mvp_control_running(&ctl) == 2U);
	}
	/* A delivered order pending: about to stop. */
	ctl.domain[0].phase = BE_MVP_DOMAIN_ENTERED;
	memset(&mgmt, 0, sizeof(mgmt));
	ctl.mgmt = &mgmt;
	CHECK(be_mvp_control_running(&ctl) == 3U);
	mgmt.domain[1].pending = 1U;
	CHECK(be_mvp_control_running(&ctl) == 1U);
	mgmt.domain[1].awaiting = 1U;
	mgmt.domain[1].pending = 0U;
	CHECK(be_mvp_control_running(&ctl) == 3U);
	/* A failed or done loop, or none. */
	ctl.done = 1U;
	CHECK(be_mvp_control_running(&ctl) == 0U);
	ctl.done = 0U;
	ctl.failed = 1U;
	CHECK(be_mvp_control_running(&ctl) == 0U);
	CHECK(be_mvp_control_running((const struct be_mvp_control *)0) == 0U);
}

/* A domain hart's staging buffer, and its guest's buffer. */
static struct be_mvp_input_stage stage;
static be_u8 guest[FAKE_BYTES];
static be_u8 guest_copy[FAKE_BYTES];

/* Hart 0's side: @text as one INPUT record, published. */
static void queue(be_u32 domain, const char *text, be_u64 length)
{
	CHECK(be_mvp_ring_post(&writers[domain], BE_MVP_RECORD_INPUT, 1U,
			       (const be_u8 *)text, length) == 1);
	CHECK(be_mvp_ring_publish(&writers[domain]) == 1);
}

/* The domain hart's service, with its acquire and release. */
static be_u64 serve(be_u8 *to, be_u64 length)
{
	be_u64 copied;

	(void)be_mvp_ring_acquire(&readers[0]);
	copied = be_mvp_input_serve(&stage, &readers[0], to, length);
	if (copied != BE_MVP_INPUT_FAILED)
		CHECK(be_mvp_ring_release(&readers[0]) == 1);
	return copied;
}

static void test_serve(void)
{
	char full[BE_MVP_RECORD_PAYLOAD_MAX];
	struct be_mvp_ring other;
	be_u64 index;

	SCENARIO();
	open_ring(0U, BE_MVP_INPUT_RING_BYTES);
	memset(&stage, 0, sizeof(stage));
	memset(guest, 0xa5, sizeof(guest));
	/* Nothing queued: 0, nothing written. */
	CHECK(serve(guest, 16U) == 0U && guest[0] == 0xa5U);
	/* A count below the record: the rest stays staged, in order. */
	queue(0U, "hello", 5U);
	CHECK(serve(guest, 3U) == 3U && memcmp(guest, "hel", 3U) == 0 &&
	      guest[3] == 0xa5U);
	CHECK(stage.length == 5U && stage.offset == 3U);
	memset(guest, 0xa5, sizeof(guest));
	CHECK(serve(guest, 16U) == 2U && memcmp(guest, "lo", 2U) == 0 &&
	      guest[2] == 0xa5U);
	CHECK(stage.length == 0U && stage.offset == 0U);
	CHECK(serve(guest, 16U) == 0U);
	/* A count above the queue: every queued byte, across records. */
	memset(guest, 0xa5, sizeof(guest));
	queue(0U, "ab", 2U);
	queue(0U, "cde", 3U);
	CHECK(serve(guest, 100U) == 5U && memcmp(guest, "abcde", 5U) == 0 &&
	      guest[5] == 0xa5U && stage.length == 0U);
	/* Staged bytes first, then the next record. */
	queue(0U, "fgh", 3U);
	queue(0U, "ij", 2U);
	CHECK(serve(guest, 2U) == 2U && memcmp(guest, "fg", 2U) == 0);
	CHECK(serve(guest, 2U) == 2U && memcmp(guest, "hi", 2U) == 0 &&
	      stage.length == 2U && stage.offset == 1U);
	CHECK(serve(guest, 2U) == 1U && guest[0] == 'j' &&
	      stage.length == 0U);
	/* A whole record and the 256-byte cap. */
	for (index = 0U; index < sizeof(full); ++index)
		full[index] = (char)index;
	queue(0U, full, sizeof(full));
	queue(0U, "z", 1U);
	CHECK(serve(guest, BE_MVP_DBCN_MAX_BYTES) == 256U &&
	      memcmp(guest, full, 256U) == 0);
	CHECK(serve(guest, BE_MVP_DBCN_MAX_BYTES) == 1U && guest[0] == 'z');
	/* A zero count copies nothing and takes nothing. */
	queue(0U, "q", 1U);
	CHECK(serve(guest, 0U) == 0U && stage.length == 0U);
	CHECK(serve((be_u8 *)0, 0U) == 0U);
	CHECK(serve(guest, 1U) == 1U && guest[0] == 'q');

	/* Invalid input: nothing copied. */
	SCENARIO();
	memset(guest, 0xa5, sizeof(guest));
	queue(0U, "r", 1U);
	CHECK(serve(guest, BE_MVP_DBCN_MAX_BYTES + 1U) ==
	      BE_MVP_INPUT_FAILED);
	CHECK(serve((be_u8 *)0, 1U) == BE_MVP_INPUT_FAILED);
	stage.length = 2U;
	stage.offset = 3U;
	CHECK(serve(guest, 1U) == BE_MVP_INPUT_FAILED);
	stage.length = BE_MVP_INPUT_STAGE_BYTES + 1U;
	stage.offset = 0U;
	CHECK(serve(guest, 1U) == BE_MVP_INPUT_FAILED);
	memset(&stage, 0, sizeof(stage));
	CHECK(be_mvp_input_serve((struct be_mvp_input_stage *)0, &readers[0],
				 guest, 1U) == BE_MVP_INPUT_FAILED);
	CHECK(be_mvp_input_serve(&stage, (struct be_mvp_ring *)0, guest,
				 1U) == BE_MVP_INPUT_FAILED);
	CHECK(guest[0] == 0xa5U);
	CHECK(serve(guest, 1U) == 1U && guest[0] == 'r');
	/* An INPUT record without a payload fails the service. */
	queue(0U, "", 0U);
	CHECK(serve(guest, 4U) == BE_MVP_INPUT_FAILED);
	/* A record of another type, which the input ring never carries: the
	 * reader's view refuses it, and the service fails. */
	open_ring(0U, BE_MVP_INPUT_RING_BYTES);
	memset(&stage, 0, sizeof(stage));
	CHECK(be_mvp_ring_init(&other, ring_bytes[0], BE_MVP_INPUT_RING_BYTES,
			       &ring_index[0][0], &ring_index[0][1],
			       BE_MVP_RECORDS_OUTBOUND, 0U,
			       BE_MVP_RING_WRITER) == 1);
	CHECK(be_mvp_ring_post(&other, BE_MVP_RECORD_LINE, 1U,
			       (const be_u8 *)"x", 1U) == 1);
	CHECK(be_mvp_ring_publish(&other) == 1);
	memset(guest, 0xa5, sizeof(guest));
	CHECK(serve(guest, 4U) == BE_MVP_INPUT_FAILED && guest[0] == 0xa5U);
}

/* The SBI core's side of the served read (be_mvp_handle_exit()). */
static be_u8 pool[BE_MVP_GSTAGE_POOL_BYTES];
static struct be_mvp_gstage_map window;
static const struct be_mvp_gstage_leaves no_leaf;

static void build_window(void)
{
	struct be_mvp_gstage_desc desc = {
		BE_MVP_GUEST_GPA, BE_MVP_G0_HPA, BE_MVP_GUEST_BYTES,
		BE_MVP_G0_ROOT_HPA, BE_MVP_G0_VMID, BE_MVP_DOMAIN0_HART,
	};

	CHECK(be_mvp_gstage_build(&desc, pool, sizeof(pool)) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(be_mvp_gstage_walk(&desc, pool, sizeof(pool), &window) ==
	      BE_MVP_GSTAGE_OK);
	CHECK(window.gpa_base == WINDOW_GPA && window.hpa_base == WINDOW_HPA &&
	      window.size == WINDOW_BYTES);
}

static struct be_mvp_state granted_state(be_u64 accept)
{
	struct be_mvp_state state = BE_MVP_STATE_INITIALIZER(
		BE_MVP_EXIT_CEILING);

	state.accept_input = accept;
	return state;
}

static struct be_mvp_exit read_call(be_u64 count, be_u64 gpa, be_u64 high)
{
	struct be_mvp_exit record;

	memset(&record, 0, sizeof(record));
	record.frame.scause = BE_MVP_SCAUSE_VS_ECALL;
	record.frame.sepc = ECALL_PC;
	record.frame.gpr[BE_R4_GPR_A7] = BE_MVP_SBI_EID_DBCN;
	record.frame.gpr[BE_R4_GPR_A6] = BE_MVP_SBI_DBCN_READ;
	record.frame.gpr[BE_R4_GPR_A0] = count;
	record.frame.gpr[BE_R4_GPR_A1] = gpa;
	record.frame.gpr[BE_MVP_GPR_A2] = high;
	record.hstatus = BE_U64_C(0x200000180);
	record.time = 0x1000U;
	return record;
}

/* A refused read: a2's or the range's INVALID_PARAM, counted refused. */
static void expect_refused(be_u64 count, be_u64 gpa, be_u64 high)
{
	struct be_mvp_state state = granted_state(1U);
	struct be_mvp_exit record = read_call(count, gpa, high);
	struct be_mvp_result result;

	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
				 &result) == BE_MVP_ACTION_RETURN);
	CHECK(result.error == BE_MVP_SBI_ERR_INVALID_PARAM &&
	      result.value == 0U && result.resume_pc == ECALL_PC + 4U);
	CHECK(state.counts.refused == 1U && state.counts.dbcn_input == 0U &&
	      state.counts.dbcn_read == 0U && be_mvp_counts_sbi(&state.counts) ==
	      1U && state.phase == BE_MVP_PHASE_RUNNING);
}

/* A served read: its window HPA and its length, min(a0, 256). */
static void expect_served(be_u64 count, be_u64 gpa, be_u64 length)
{
	struct be_mvp_state state = granted_state(1U);
	struct be_mvp_exit record = read_call(count, gpa, 0U);
	struct be_mvp_result result;

	CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
				 &result) == BE_MVP_ACTION_CONSOLE_READ);
	CHECK(result.error == BE_MVP_SBI_SUCCESS &&
	      result.target_pa == WINDOW_HPA + (gpa - WINDOW_GPA) &&
	      result.length == length && result.resume_pc == ECALL_PC + 4U);
	CHECK(state.counts.dbcn_input == 1U && state.counts.refused == 0U &&
	      state.counts.dbcn_read == 0U &&
	      be_mvp_counts_sbi(&state.counts) == 1U);
}

/*
 * The write-authority rule (D-1): a2 first, then a zero count at once,
 * then the guest's whole range [a1, a1 + a0) in the domain's own window,
 * however few bytes are queued; and a domain without the grant DENIED,
 * counted in dbcn_read, as before M7.
 */
static void test_read_authority(void)
{
	static const be_u64 outside[] = {
		BE_MVP_CHANNEL_GPA, BE_MVP_CHANNEL_GPA + 0x1000U,
		BE_MVP_CHANNEL_GPA + 0x2000U, BE_MVP_CHANNEL_GPA + 0xff8U,
		WINDOW_GPA - 1U, WINDOW_GPA + WINDOW_BYTES, 0U,
		BE_MVP_G0_HPA, BE_MVP_HART_REGION_HPA, ALL_ONES,
	};
	struct be_mvp_state state;
	struct be_mvp_exit record;
	struct be_mvp_result result;
	unsigned int index;

	SCENARIO();
	build_window();
	/* Served: the window's first and last byte, the cap, and the whole
	 * window as a range. */
	expect_served(1U, WINDOW_GPA, 1U);
	expect_served(1U, WINDOW_GPA + WINDOW_BYTES - 1U, 1U);
	expect_served(5U, WINDOW_GPA + 0x100U, 5U);
	expect_served(300U, WINDOW_GPA + 0x100U, 256U);
	expect_served(WINDOW_BYTES, WINDOW_GPA, 256U);
	expect_served(16U, WINDOW_GPA + WINDOW_BYTES - 16U, 16U);
	/* a2 nonzero, whatever the range. */
	expect_refused(1U, WINDOW_GPA, 1U);
	expect_refused(0U, WINDOW_GPA, 1U);
	expect_refused(1U, WINDOW_GPA, ALL_ONES);
	/* Across the window's end, or overflowing. */
	expect_refused(2U, WINDOW_GPA + WINDOW_BYTES - 1U, 0U);
	expect_refused(32U, WINDOW_GPA + WINDOW_BYTES - 16U, 0U);
	expect_refused(WINDOW_BYTES + 1U, WINDOW_GPA, 0U);
	expect_refused(ALL_ONES, WINDOW_GPA, 0U);
	expect_refused(16U, ALL_ONES - 7U, 0U);
	expect_refused(ALL_ONES - WINDOW_GPA + 2U, WINDOW_GPA, 0U);
	/* The channel page, the declared pages, and every other address
	 * outside the window. */
	for (index = 0U; index < sizeof(outside) / sizeof(outside[0]);
	     ++index) {
		expect_refused(1U, outside[index], 0U);
		expect_refused(8U, outside[index], 0U);
	}
	/* A zero count: 0 at once, without a range. */
	for (index = 0U; index < sizeof(outside) / sizeof(outside[0]);
	     ++index) {
		state = granted_state(1U);
		record = read_call(0U, outside[index], 0U);
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_RETURN);
		CHECK(result.error == BE_MVP_SBI_SUCCESS && result.value == 0U);
		CHECK(state.counts.dbcn_input == 1U &&
		      state.counts.refused == 0U);
	}
	/* Without the grant: DENIED, counted as before, whatever the
	 * arguments; a grant other than 1 is none. */
	SCENARIO();
	for (index = 0U; index < 3U; ++index) {
		static const be_u64 accept[] = { 0U, 2U, ALL_ONES };

		state = granted_state(accept[index]);
		record = read_call(16U, WINDOW_GPA, 0U);
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_RETURN);
		CHECK(result.error == BE_MVP_SBI_ERR_DENIED &&
		      result.value == 0U);
		CHECK(state.counts.dbcn_read == 1U &&
		      state.counts.dbcn_input == 0U &&
		      state.counts.refused == 0U);
		state = granted_state(accept[index]);
		record = read_call(ALL_ONES, ALL_ONES, ALL_ONES);
		CHECK(be_mvp_handle_exit(&state, &window, &no_leaf, &record,
					 &result) == BE_MVP_ACTION_RETURN);
		CHECK(result.error == BE_MVP_SBI_ERR_DENIED &&
		      state.counts.dbcn_read == 1U);
	}
}

/*
 * The served read end to end, as the domain hart runs it: the SBI core's
 * decision, then, only for CONSOLE_READ, the service into a guest buffer
 * through the map's HPA, the count the guest's a1. A small window over a
 * host buffer stands for the guest's.
 */
static struct be_mvp_result model_read(struct be_mvp_state *state,
				       const struct be_mvp_gstage_map *map,
				       be_u64 count, be_u64 gpa, be_u64 high)
{
	struct be_mvp_exit record = read_call(count, gpa, high);
	struct be_mvp_result result;
	be_u64 copied;

	if (be_mvp_handle_exit(state, map, &no_leaf, &record, &result) ==
	    BE_MVP_ACTION_CONSOLE_READ) {
		CHECK(result.target_pa >= map->hpa_base &&
		      result.target_pa + result.length <=
		      map->hpa_base + map->size);
		copied = serve((be_u8 *)(uintptr_t)result.target_pa,
			       result.length);
		CHECK(copied != BE_MVP_INPUT_FAILED);
		result.value = copied;
	}
	be_mvp_apply_return(&record.frame, &result);
	CHECK(record.frame.gpr[BE_R4_GPR_A0] == (be_u64)result.error &&
	      record.frame.gpr[BE_R4_GPR_A1] == result.value &&
	      record.frame.sepc == ECALL_PC + 4U);
	return result;
}

static void test_read_service(void)
{
	struct be_mvp_gstage_map map;
	struct be_mvp_state state;
	struct be_mvp_result result;
	be_u64 tail;

	SCENARIO();
	memset(&map, 0, sizeof(map));
	map.gpa_base = WINDOW_GPA;
	map.hpa_base = (be_u64)(uintptr_t)guest;
	map.size = FAKE_BYTES;
	open_ring(0U, BE_MVP_INPUT_RING_BYTES);
	memset(&stage, 0, sizeof(stage));
	memset(guest, 0xa5, sizeof(guest));
	state = granted_state(1U);
	/* Nothing queued: success, 0. */
	result = model_read(&state, &map, 64U, WINDOW_GPA + 0x10U, 0U);
	CHECK(result.action == BE_MVP_ACTION_CONSOLE_READ &&
	      result.error == BE_MVP_SBI_SUCCESS && result.value == 0U);
	queue(0U, "line one\n", 9U);
	queue(0U, "two\n", 4U);
	memcpy(guest_copy, guest, sizeof(guest));
	tail = ring_index[0][1].value;
	/* Each refusal: no guest byte written, no queued byte taken. */
	(void)model_read(&state, &map, 4U, WINDOW_GPA, 1U);
	(void)model_read(&state, &map, 4U, WINDOW_GPA + FAKE_BYTES - 2U, 0U);
	(void)model_read(&state, &map, FAKE_BYTES + 1U, WINDOW_GPA, 0U);
	(void)model_read(&state, &map, 4U, ALL_ONES - 1U, 0U);
	(void)model_read(&state, &map, 4U, BE_MVP_CHANNEL_GPA, 0U);
	(void)model_read(&state, &map, 4U, BE_MVP_CHANNEL_GPA + 0x2000U, 0U);
	CHECK(state.counts.refused == 6U);
	CHECK(memcmp(guest, guest_copy, sizeof(guest)) == 0 &&
	      ring_index[0][1].value == tail && stage.length == 0U);
	/* Without the grant: DENIED, nothing taken or written. */
	{
		struct be_mvp_state denied = granted_state(0U);

		result = model_read(&denied, &map, 4U, WINDOW_GPA, 0U);
		CHECK(result.error == BE_MVP_SBI_ERR_DENIED &&
		      denied.counts.dbcn_read == 1U);
		CHECK(memcmp(guest, guest_copy, sizeof(guest)) == 0 &&
		      ring_index[0][1].value == tail);
	}
	/* A count below the first record: its rest stays staged. */
	result = model_read(&state, &map, 4U, WINDOW_GPA + 0x20U, 0U);
	CHECK(result.error == BE_MVP_SBI_SUCCESS && result.value == 4U &&
	      memcmp(&guest[0x20], "line", 4U) == 0 && guest[0x24] == 0xa5U);
	/* A count above the queue: the rest of both records. */
	result = model_read(&state, &map, 200U, WINDOW_GPA + 0x40U, 0U);
	CHECK(result.value == 9U && memcmp(&guest[0x40], " one\ntwo\n", 9U) ==
	      0 && guest[0x49] == 0xa5U);
	/* At the window's last byte. */
	queue(0U, "!", 1U);
	result = model_read(&state, &map, 1U, WINDOW_GPA + FAKE_BYTES - 1U, 0U);
	CHECK(result.value == 1U && guest[FAKE_BYTES - 1U] == '!');
	CHECK(state.counts.dbcn_input == 4U && state.counts.refused == 6U &&
	      be_mvp_counts_sbi(&state.counts) == 10U);
}

int main(void)
{
	test_parser();
	test_arm();
	test_routing();
	test_ring_full();
	test_rearm();
	test_running();
	test_serve();
	test_read_authority();
	test_read_service();
	printf("BE_MVP_INPUT_CHECK: PASS\n");
	printf("BE_MVP_INPUT_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_MVP_INPUT_CHECK: assertions=%lu\n", assertions);
	return 0;
}
