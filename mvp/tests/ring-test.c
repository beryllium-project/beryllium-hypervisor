// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the MVP rings: the index lines and record
 *          sizes; view setup and every refused setup; posting at every fill
 *          level of the smallest ring and of each layout ring, with the
 *          exact refusal of a full ring, which never overwrites; records
 *          that wrap the buffer at every 8-byte offset, and free-running
 *          indices across 2^64; visibility only after publication and room
 *          only after release; the writer's high-water mark; the writer's
 *          reads of the reader's tail and of its own published head (Plan
 *          revision M1-B); the reader's header validation (type, ring,
 *          domain, length, reserved word, padding, records that cross the
 *          head, and malformed heads); the writer's tail checks; calls on
 *          the other side's view; failures that stay failed; and long
 *          pseudo-random runs checked record by record, and index by index,
 *          against an independent queue model.
 * Trust:   host evidence only. No fence, cache, second hart, QEMU, or
 *          hardware behaviour is exercised: the memory ordering the ring
 *          needs is the caller's (mvp-ring.h).
 * Scope:   the MVP line (planning/mvp-m0-plan.md, "Hart region", Rings).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mvp-ring.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_RING_CHECK: assertion failed: %s:%d: %s\n", \
			       __FILE__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define SMALL			BE_MVP_RING_MIN_BYTES
#define OUT			BE_MVP_RECORDS_OUTBOUND
#define IN			BE_MVP_RECORDS_INBOUND
#define WRITER			BE_MVP_RING_WRITER
#define READER			BE_MVP_RING_READER
#define ALL_ONES		(~BE_U64_C(0))
#define LINE			BE_MVP_RECORD_LINE
#define PAYLOAD_MAX		BE_MVP_RECORD_PAYLOAD_MAX

static be_u8 buffer[BE_MVP_OUTBOUND_RING_BYTES];
static be_u8 snapshot[BE_MVP_OUTBOUND_RING_BYTES];
static struct be_mvp_ring_index ring_head;
static struct be_mvp_ring_index ring_tail;
static struct be_mvp_ring writer;
static struct be_mvp_ring reader;
static struct be_mvp_record record;
static be_u64 ring_capacity;

static void fill_payload(be_u8 *bytes, be_u64 length, be_u64 seed)
{
	be_u64 index;

	for (index = 0U; index < length; ++index)
		bytes[index] = (be_u8)((seed * 131U + index * 7U + 1U) & 0xffU);
}

/* Both views of one ring whose indices both start at @start. */
static void setup(be_u64 capacity, be_u64 start, be_u64 types, be_u32 domain)
{
	memset(buffer, 0xa5, sizeof(buffer));
	ring_capacity = capacity;
	ring_head.value = start;
	ring_tail.value = start;
	CHECK(be_mvp_ring_init(&writer, buffer, capacity, &ring_head,
			       &ring_tail, types, domain, WRITER) == 1);
	CHECK(be_mvp_ring_init(&reader, buffer, capacity, &ring_head,
			       &ring_tail, types, domain, READER) == 1);
}

static int post(be_u32 type, be_u64 time, be_u64 length, be_u64 seed)
{
	be_u8 bytes[2U * PAYLOAD_MAX];

	fill_payload(bytes, length < sizeof(bytes) ? length : sizeof(bytes),
		     seed);
	return be_mvp_ring_post(&writer, (enum be_mvp_record_type)type, time,
				bytes, length);
}

static int record_zero(void)
{
	be_u64 index;

	if (record.type != 0U || record.domain != 0U || record.length != 0U ||
	    record.time != 0U)
		return 0;
	for (index = 0U; index < PAYLOAD_MAX; ++index)
		if (record.payload[index] != 0U)
			return 0;
	return 1;
}

static void expect_record(be_u32 type, be_u64 time, be_u64 length,
			  be_u64 seed)
{
	be_u8 bytes[PAYLOAD_MAX];
	be_u64 index;

	fill_payload(bytes, length, seed);
	CHECK(be_mvp_ring_take(&reader, &record) == BE_MVP_RING_RECORD);
	CHECK(record.type == type && record.domain == reader.domain);
	CHECK(record.length == length && record.time == time);
	CHECK(memcmp(record.payload, bytes, length) == 0);
	for (index = length; index < PAYLOAD_MAX; ++index)
		if (record.payload[index] != 0U)
			break;
	CHECK(index == PAYLOAD_MAX);
}

static void expect_empty(void)
{
	CHECK(be_mvp_ring_take(&reader, &record) == BE_MVP_RING_EMPTY);
	CHECK(record_zero());
}

static void expect_writer_failed(void)
{
	be_u64 head = ring_head.value;
	be_u64 tail = ring_tail.value;

	CHECK(writer.failed == 1U);
	CHECK(post(LINE, 0U, 0U, 0U) == 0);
	CHECK(be_mvp_ring_post_words(&writer, BE_MVP_RECORD_PONG, 0U,
				     (const be_u64 *)0, 0U) == 0);
	CHECK(be_mvp_ring_publish(&writer) == 0);
	CHECK(writer.failed == 1U);
	CHECK(ring_head.value == head && ring_tail.value == tail);
}

static void expect_reader_failed(void)
{
	be_u64 head = ring_head.value;
	be_u64 tail = ring_tail.value;

	CHECK(reader.failed == 1U);
	CHECK(be_mvp_ring_acquire(&reader) == 0U);
	CHECK(be_mvp_ring_take(&reader, &record) == BE_MVP_RING_INVALID);
	CHECK(record_zero());
	CHECK(be_mvp_ring_release(&reader) == 0);
	CHECK(reader.failed == 1U);
	CHECK(ring_head.value == head && ring_tail.value == tail);
}

static void raw_le(be_u64 position, be_u64 value, unsigned int bytes)
{
	unsigned int byte;

	for (byte = 0U; byte < bytes; ++byte)
		buffer[(position + byte) & (ring_capacity - 1U)] =
			(be_u8)((value >> (8U * byte)) & 0xffU);
}

/* A record written by hand at @position: header, then zero padding. */
static void raw_record(be_u64 position, be_u64 type, be_u64 domain,
		       be_u64 length, be_u64 reserved, be_u64 time)
{
	be_u64 index;

	raw_le(position, type, 1U);
	raw_le(position + 1U, domain, 1U);
	raw_le(position + 2U, length, 2U);
	raw_le(position + 4U, reserved, 4U);
	raw_le(position + 8U, time, 8U);
	for (index = 0U; index < ((length + 7U) & ~BE_U64_C(7)) &&
			 index < PAYLOAD_MAX; ++index)
		raw_le(position + 16U + index, 0U, 1U);
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(sizeof(struct be_mvp_ring_index) == 64U);
	CHECK(_Alignof(struct be_mvp_ring_index) == 64U);
	CHECK(BE_MVP_RECORD_HEADER_BYTES == 16U && PAYLOAD_MAX == 256U);
	CHECK(BE_MVP_RECORD_MAX_BYTES == 272U && SMALL == 512U);
	CHECK(be_mvp_ring_record_bytes(0U) == 16U);
	CHECK(be_mvp_ring_record_bytes(1U) == 24U);
	CHECK(be_mvp_ring_record_bytes(7U) == 24U);
	CHECK(be_mvp_ring_record_bytes(8U) == 24U);
	CHECK(be_mvp_ring_record_bytes(9U) == 32U);
	CHECK(be_mvp_ring_record_bytes(255U) == 272U);
	CHECK(be_mvp_ring_record_bytes(256U) == 272U);
	CHECK(be_mvp_ring_record_bytes(257U) == 0U);
	CHECK(be_mvp_ring_record_bytes(ALL_ONES) == 0U);
	CHECK(BE_MVP_RECORD_NONE == 0 && BE_MVP_RECORD_READY == 1 &&
	      BE_MVP_RECORD_ENTERED == 2 && BE_MVP_RECORD_LINE == 3 &&
	      BE_MVP_RECORD_PONG == 4 && BE_MVP_RECORD_SHUTDOWN == 5 &&
	      BE_MVP_RECORD_FAIL == 6 && BE_MVP_RECORD_PING == 7 &&
	      BE_MVP_RECORD_ACK == 8 && BE_MVP_RECORD_DENIAL == 9);
	/* The management extension's (planning/mvp-m2-plan.md): three each
	 * way, after M1's. */
	CHECK(BE_MVP_RECORD_MGMT_REQUEST == 10 && BE_MVP_RECORD_PAUSED == 11 &&
	      BE_MVP_RECORD_TERMINATED == 12 &&
	      BE_MVP_RECORD_MGMT_RESULT == 13 && BE_MVP_RECORD_PAUSE == 14 &&
	      BE_MVP_RECORD_TERMINATE == 15);
	/* Console input's (planning/mvp-m7-plan.md, D-1): one type, in a
	 * third set of its own. */
	CHECK(BE_MVP_RECORD_INPUT == 16 && BE_MVP_RECORD_COUNT == 17);
	CHECK(OUT == BE_U64_C(0x1e7e) && IN == BE_U64_C(0xe180) &&
	      BE_MVP_RECORDS_INPUT == BE_U64_C(0x10000));
	CHECK((OUT & IN) == 0U && (OUT & 1U) == 0U && (IN & 1U) == 0U &&
	      (BE_MVP_RECORDS_INPUT & (OUT | IN | 1U)) == 0U);
	CHECK(BE_MVP_INBOUND_RING_BYTES == 0x1000U &&
	      BE_MVP_OUTBOUND_RING_BYTES == 0x8000U &&
	      BE_MVP_VARIANT_OUTBOUND_RING_BYTES == 0x400U);
	CHECK(BE_MVP_RING_PEAK_BUDGET == BE_MVP_OUTBOUND_RING_BYTES / 2U);
}

static void test_reset(void)
{
	SCENARIO();
	ring_head.value = 123U;
	ring_tail.value = 456U;
	be_mvp_ring_reset(&ring_head, &ring_tail);
	CHECK(ring_head.value == 0U && ring_tail.value == 0U);
	ring_head.value = 8U;
	ring_tail.value = 16U;
	be_mvp_ring_reset((volatile struct be_mvp_ring_index *)0, &ring_tail);
	CHECK(ring_head.value == 8U && ring_tail.value == 0U);
	be_mvp_ring_reset(&ring_head, (volatile struct be_mvp_ring_index *)0);
	CHECK(ring_head.value == 0U && ring_tail.value == 0U);
	be_mvp_ring_reset((volatile struct be_mvp_ring_index *)0,
			  (volatile struct be_mvp_ring_index *)0);
	CHECK(ring_head.value == 0U && ring_tail.value == 0U);
}

static void expect_init_refused(be_u8 *bytes, be_u64 capacity,
				volatile struct be_mvp_ring_index *head,
				volatile struct be_mvp_ring_index *tail,
				be_u64 types, be_u32 domain,
				enum be_mvp_ring_role role)
{
	struct be_mvp_ring view;
	be_u64 head_value = ring_head.value;
	be_u64 tail_value = ring_tail.value;

	memset(&view, 0x5a, sizeof(view));
	CHECK(be_mvp_ring_init(&view, bytes, capacity, head, tail, types,
			       domain, role) == 0);
	CHECK(view.failed == 1U && view.buffer == (be_u8 *)0 &&
	      view.capacity == 0U && view.types == 0U && view.cursor == 0U &&
	      view.peak == 0U);
	/* A refused view refuses every call and writes no index. */
	CHECK(be_mvp_ring_post(&view, LINE, 0U, (const be_u8 *)0, 0U) == 0);
	CHECK(be_mvp_ring_publish(&view) == 0);
	CHECK(be_mvp_ring_acquire(&view) == 0U);
	CHECK(be_mvp_ring_take(&view, &record) == BE_MVP_RING_INVALID);
	CHECK(be_mvp_ring_release(&view) == 0);
	CHECK(view.failed == 1U);
	CHECK(ring_head.value == head_value && ring_tail.value == tail_value);
}

static void test_init(void)
{
	SCENARIO();
	CHECK(be_mvp_ring_init((struct be_mvp_ring *)0, buffer, SMALL,
			       &ring_head, &ring_tail, OUT, 0U, WRITER) == 0);
	ring_head.value = 64U;
	ring_tail.value = 32U;
	memset(&writer, 0x5a, sizeof(writer));
	CHECK(be_mvp_ring_init(&writer, buffer, SMALL, &ring_head, &ring_tail,
			       OUT, 1U, WRITER) == 1);
	CHECK(writer.buffer == buffer && writer.capacity == SMALL);
	CHECK(writer.head == &ring_head && writer.tail == &ring_tail);
	CHECK(writer.types == OUT && writer.domain == 1U);
	CHECK(writer.role == WRITER && writer.failed == 0U);
	CHECK(writer.cursor == 64U && writer.limit == 64U &&
	      writer.peak == 32U);
	CHECK(be_mvp_ring_init(&reader, buffer, SMALL, &ring_head, &ring_tail,
			       OUT, 1U, READER) == 1);
	CHECK(reader.cursor == 32U && reader.limit == 32U &&
	      reader.peak == 32U);
	CHECK(reader.role == READER && reader.failed == 0U);
	CHECK(ring_head.value == 64U && ring_tail.value == 32U);
	/* A full ring is a valid start; an inbound ring takes IN types. */
	ring_head.value = SMALL + 8U;
	ring_tail.value = 8U;
	CHECK(be_mvp_ring_init(&writer, buffer, SMALL, &ring_head, &ring_tail,
			       OUT, 0U, WRITER) == 1);
	CHECK(writer.peak == SMALL);
	CHECK(be_mvp_ring_init(&reader, buffer, BE_MVP_OUTBOUND_RING_BYTES,
			       &ring_head, &ring_tail,
			       BE_MVP_RECORD_BIT(BE_MVP_RECORD_PING), 1U,
			       READER) == 1);
	CHECK(be_mvp_ring_init(&reader, buffer, BE_MVP_INBOUND_RING_BYTES,
			       &ring_head, &ring_tail, IN, 0U, READER) == 1);

	ring_head.value = 0U;
	ring_tail.value = 0U;
	expect_init_refused((be_u8 *)0, SMALL, &ring_head, &ring_tail, OUT, 0U,
			    WRITER);
	expect_init_refused(buffer, SMALL,
			    (volatile struct be_mvp_ring_index *)0,
			    &ring_tail, OUT, 0U, WRITER);
	expect_init_refused(buffer, SMALL, &ring_head,
			    (volatile struct be_mvp_ring_index *)0, OUT, 0U,
			    READER);
	expect_init_refused(buffer, 0U, &ring_head, &ring_tail, OUT, 0U,
			    WRITER);
	expect_init_refused(buffer, 256U, &ring_head, &ring_tail, OUT, 0U,
			    WRITER);
	expect_init_refused(buffer, 511U, &ring_head, &ring_tail, OUT, 0U,
			    WRITER);
	expect_init_refused(buffer, 513U, &ring_head, &ring_tail, OUT, 0U,
			    WRITER);
	expect_init_refused(buffer, 768U, &ring_head, &ring_tail, OUT, 0U,
			    READER);
	expect_init_refused(buffer, 0x10000U, &ring_head, &ring_tail, OUT, 0U,
			    WRITER);
	expect_init_refused(buffer, ALL_ONES, &ring_head, &ring_tail, OUT, 0U,
			    WRITER);
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail, 0U, 0U,
			    WRITER);
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail, OUT | IN,
			    0U, WRITER);
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail,
			    OUT | BE_MVP_RECORD_BIT(BE_MVP_RECORD_NONE), 0U,
			    WRITER);
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail,
			    IN | BE_MVP_RECORD_BIT(BE_MVP_RECORD_READY), 0U,
			    READER);
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail,
			    BE_MVP_RECORD_BIT(BE_MVP_RECORD_COUNT), 0U, WRITER);
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail,
			    BE_MVP_RECORD_BIT(63U), 0U, WRITER);
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail, OUT, 2U,
			    WRITER);
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail, OUT,
			    0xffffffffU, READER);
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail, OUT, 0U,
			    (enum be_mvp_ring_role)0);
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail, OUT, 0U,
			    (enum be_mvp_ring_role)3);
	/* Indices: aligned, the head no more than a capacity ahead. */
	ring_head.value = 4U;
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail, OUT, 0U,
			    WRITER);
	ring_head.value = 16U;
	ring_tail.value = 12U;
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail, OUT, 0U,
			    READER);
	ring_head.value = SMALL + 8U;
	ring_tail.value = 0U;
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail, OUT, 0U,
			    WRITER);
	ring_head.value = 0U;
	ring_tail.value = 8U;
	expect_init_refused(buffer, SMALL, &ring_head, &ring_tail, OUT, 0U,
			    READER);
}

/*
 * Fill an empty ring with records of one payload length: the writer's
 * high-water mark and the reader's view at every fill level, then the
 * exact refusal, which leaves every buffer byte and both indices alone
 * and fails the writer; then the reader drains every record intact.
 */
static void fill(be_u64 capacity, be_u64 length)
{
	be_u64 size = be_mvp_ring_record_bytes(length);
	be_u64 count = capacity / size;
	be_u64 index;

	SCENARIO();
	setup(capacity, 0U, OUT, 0U);
	for (index = 0U; index < count; ++index) {
		CHECK(post(LINE, index, length, index) == 1);
		CHECK(writer.cursor == (index + 1U) * size);
		CHECK(be_mvp_ring_peak(&writer) == (index + 1U) * size);
		CHECK(be_mvp_ring_publish(&writer) == 1);
		CHECK(ring_head.value == (index + 1U) * size);
		CHECK(be_mvp_ring_acquire(&reader) == (index + 1U) * size);
	}
	memcpy(snapshot, buffer, sizeof(buffer));
	CHECK(capacity - count * size < size);
	CHECK(post(LINE, count, length, count) == 0);
	CHECK(memcmp(snapshot, buffer, sizeof(buffer)) == 0);
	expect_writer_failed();
	CHECK(be_mvp_ring_peak(&writer) == count * size);
	for (index = 0U; index < count; ++index)
		expect_record(LINE, index, length, index);
	expect_empty();
	CHECK(be_mvp_ring_release(&reader) == 1);
	CHECK(ring_tail.value == count * size);
	CHECK(reader.failed == 0U && writer.failed == 1U);
}

static void test_fill_levels(void)
{
	static const be_u64 capacities[] = {
		SMALL, BE_MVP_VARIANT_OUTBOUND_RING_BYTES,
		BE_MVP_INBOUND_RING_BYTES, BE_MVP_OUTBOUND_RING_BYTES,
	};
	static const be_u64 lengths[] = {
		0U, 1U, 8U, 13U, 100U, 240U, 248U, 256U,
	};
	be_size capacity;
	be_size length;

	for (capacity = 0U; capacity < BE_ARRAY_SIZE(capacities); ++capacity)
		for (length = 0U; length < BE_ARRAY_SIZE(lengths); ++length)
			fill(capacities[capacity], lengths[length]);
}

/* One record at every 8-byte offset of the smallest ring, every length. */
static void test_wrap(void)
{
	static const be_u64 lengths[] = {
		0U, 1U, 7U, 8U, 9U, 100U, 247U, 255U, 256U,
	};
	be_u64 offset;
	be_size length;

	for (offset = 0U; offset < SMALL; offset += 8U) {
		SCENARIO();
		for (length = 0U; length < BE_ARRAY_SIZE(lengths); ++length) {
			be_u64 start = 3U * SMALL + offset;
			be_u64 size = be_mvp_ring_record_bytes(lengths[length]);

			setup(SMALL, start, OUT, 1U);
			CHECK(post(BE_MVP_RECORD_FAIL, start, lengths[length],
				   offset + length) == 1);
			CHECK(buffer[offset] == BE_MVP_RECORD_FAIL);
			CHECK(buffer[(offset + 1U) % SMALL] == 1U);
			CHECK(be_mvp_ring_publish(&writer) == 1);
			CHECK(be_mvp_ring_acquire(&reader) == size);
			expect_record(BE_MVP_RECORD_FAIL, start,
				      lengths[length], offset + length);
			expect_empty();
			CHECK(be_mvp_ring_release(&reader) == 1);
			CHECK(ring_tail.value == start + size);
			CHECK(ring_head.value == ring_tail.value);
		}
	}

	/* The free-running indices cross 2^64. */
	SCENARIO();
	setup(SMALL, ALL_ONES - 31U, OUT, 0U);
	CHECK(post(BE_MVP_RECORD_READY, 1U, 16U, 1U) == 1);
	CHECK(writer.cursor == 0U);
	CHECK(post(BE_MVP_RECORD_ENTERED, 2U, 16U, 2U) == 1);
	CHECK(post(BE_MVP_RECORD_PONG, 3U, 16U, 3U) == 1);
	CHECK(writer.cursor == 64U && be_mvp_ring_peak(&writer) == 96U);
	CHECK(be_mvp_ring_publish(&writer) == 1 && ring_head.value == 64U);
	CHECK(be_mvp_ring_acquire(&reader) == 96U);
	expect_record(BE_MVP_RECORD_READY, 1U, 16U, 1U);
	expect_record(BE_MVP_RECORD_ENTERED, 2U, 16U, 2U);
	CHECK(be_mvp_ring_release(&reader) == 1 && ring_tail.value == 32U);
	expect_record(BE_MVP_RECORD_PONG, 3U, 16U, 3U);
	expect_empty();
	CHECK(be_mvp_ring_release(&reader) == 1 && ring_tail.value == 64U);
	/* A view may start with indices on either side of 2^64. */
	ring_head.value = 8U;
	ring_tail.value = ALL_ONES - 7U;
	CHECK(be_mvp_ring_init(&writer, buffer, SMALL, &ring_head, &ring_tail,
			       OUT, 0U, WRITER) == 1);
	CHECK(writer.peak == 16U && writer.cursor == 8U);
}

/* Records are visible only once published, and room only once released. */
static void test_visibility(void)
{
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(post(LINE, 10U, 5U, 1U) == 1);
	CHECK(be_mvp_ring_acquire(&reader) == 0U);
	expect_empty();
	CHECK(ring_head.value == 0U);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(post(LINE, 11U, 6U, 2U) == 1);
	CHECK(be_mvp_ring_acquire(&reader) == 24U);
	expect_record(LINE, 10U, 5U, 1U);
	expect_empty();
	CHECK(be_mvp_ring_publish(&writer) == 1);
	/* The reader sees the second record only after acquiring again. */
	expect_empty();
	CHECK(be_mvp_ring_acquire(&reader) == 24U);
	expect_record(LINE, 11U, 6U, 2U);
	CHECK(ring_tail.value == 0U);
	CHECK(be_mvp_ring_release(&reader) == 1 && ring_tail.value == 48U);
	CHECK(be_mvp_ring_release(&reader) == 1 && ring_tail.value == 48U);
	/* Publishing nothing new changes nothing. */
	CHECK(be_mvp_ring_publish(&writer) == 1 && ring_head.value == 48U);
	CHECK(be_mvp_ring_acquire(&reader) == 0U);
	expect_empty();

	/* A taken record frees no room until it is released. */
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(post(LINE, 1U, 240U, 1U) == 1);
	CHECK(post(LINE, 2U, 240U, 2U) == 1);
	CHECK(be_mvp_ring_peak(&writer) == SMALL);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(be_mvp_ring_acquire(&reader) == SMALL);
	expect_record(LINE, 1U, 240U, 1U);
	CHECK(post(LINE, 3U, 0U, 3U) == 0);
	expect_writer_failed();

	/* Once released, the room is the writer's: the record wraps to 0. */
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(post(LINE, 1U, 240U, 1U) == 1);
	CHECK(post(LINE, 2U, 240U, 2U) == 1);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(be_mvp_ring_acquire(&reader) == SMALL);
	expect_record(LINE, 1U, 240U, 1U);
	CHECK(be_mvp_ring_release(&reader) == 1 && ring_tail.value == 256U);
	CHECK(post(LINE, 3U, 240U, 3U) == 1);
	CHECK(buffer[0] == LINE && writer.cursor == 768U);
	CHECK(be_mvp_ring_peak(&writer) == SMALL);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(be_mvp_ring_acquire(&reader) == SMALL);
	expect_record(LINE, 2U, 240U, 2U);
	expect_record(LINE, 3U, 240U, 3U);
	expect_empty();
	CHECK(be_mvp_ring_release(&reader) == 1 && ring_tail.value == 768U);
	CHECK(writer.failed == 0U && reader.failed == 0U);
}

/* The high-water mark: the most bytes in use after any post. */
static void test_peak(void)
{
	be_u64 index;

	SCENARIO();
	setup(BE_MVP_INBOUND_RING_BYTES, 0U, IN, 1U);
	CHECK(be_mvp_ring_peak(&writer) == 0U);
	CHECK(be_mvp_ring_peak(&reader) == 0U);
	CHECK(be_mvp_ring_peak((const struct be_mvp_ring *)0) == 0U);
	for (index = 0U; index < 4U; ++index)
		CHECK(post(BE_MVP_RECORD_PING, index, 64U, index) == 1);
	CHECK(be_mvp_ring_peak(&writer) == 320U);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(be_mvp_ring_acquire(&reader) == 320U);
	for (index = 0U; index < 4U; ++index)
		expect_record(BE_MVP_RECORD_PING, index, 64U, index);
	CHECK(be_mvp_ring_release(&reader) == 1);
	/* Less in use than before leaves the mark where it was. */
	CHECK(post(BE_MVP_RECORD_ACK, 9U, 0U, 0U) == 1);
	CHECK(post(BE_MVP_RECORD_ACK, 9U, 0U, 0U) == 1);
	CHECK(be_mvp_ring_peak(&writer) == 320U);
	for (index = 0U; index < 18U; ++index)
		CHECK(post(BE_MVP_RECORD_ACK, 10U, 0U, 0U) == 1);
	CHECK(be_mvp_ring_peak(&writer) == 320U);
	CHECK(post(BE_MVP_RECORD_ACK, 10U, 8U, 0U) == 1);
	CHECK(be_mvp_ring_peak(&writer) == 344U);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(be_mvp_ring_peak(&reader) == 0U);
	/* A writer view starting on a ring in use counts what it found. */
	CHECK(be_mvp_ring_init(&writer, buffer, BE_MVP_INBOUND_RING_BYTES,
			       &ring_head, &ring_tail, IN, 1U, WRITER) == 1);
	CHECK(be_mvp_ring_peak(&writer) == 344U);
}

/*
 * The writer's reads (Plan revision M1-B): the reader's tail moves only
 * when the reader releases, the published head only when the writer
 * publishes; neither read changes the view. A reader's view, a failed
 * one, and no view read 0.
 */
static void test_writer_reads(void)
{
	be_u64 size = be_mvp_ring_record_bytes(8U);

	SCENARIO();
	setup(SMALL, 64U, OUT, 0U);
	CHECK(be_mvp_ring_taken(&writer) == 64U);
	CHECK(be_mvp_ring_published(&writer) == 64U);
	CHECK(post(LINE, 1U, 8U, 1U) == 1);
	CHECK(be_mvp_ring_published(&writer) == 64U);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(be_mvp_ring_published(&writer) == 64U + size);
	CHECK(be_mvp_ring_taken(&writer) == 64U);
	CHECK(be_mvp_ring_acquire(&reader) == size);
	expect_record(LINE, 1U, 8U, 1U);
	CHECK(be_mvp_ring_taken(&writer) == 64U);
	CHECK(be_mvp_ring_release(&reader) == 1);
	CHECK(be_mvp_ring_taken(&writer) == 64U + size);
	CHECK(be_mvp_ring_published(&writer) == 64U + size);
	CHECK(writer.failed == 0U && writer.cursor == 64U + size &&
	      writer.limit == 64U + size && writer.peak == size);

	/* Free-running indices across 2^64, as the ring counts them. */
	SCENARIO();
	setup(SMALL, ALL_ONES - 7U, OUT, 1U);
	CHECK(be_mvp_ring_taken(&writer) == ALL_ONES - 7U);
	CHECK(be_mvp_ring_published(&writer) == ALL_ONES - 7U);
	CHECK(post(LINE, 2U, 8U, 2U) == 1);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(be_mvp_ring_published(&writer) == size - 8U);
	CHECK(be_mvp_ring_acquire(&reader) == size);
	expect_record(LINE, 2U, 8U, 2U);
	CHECK(be_mvp_ring_release(&reader) == 1);
	CHECK(be_mvp_ring_taken(&writer) == size - 8U);

	/* A reader's view, a failed writer's, and no view read 0. */
	SCENARIO();
	setup(SMALL, 64U, OUT, 0U);
	CHECK(be_mvp_ring_taken(&reader) == 0U);
	CHECK(be_mvp_ring_published(&reader) == 0U);
	CHECK(be_mvp_ring_taken((const struct be_mvp_ring *)0) == 0U);
	CHECK(be_mvp_ring_published((const struct be_mvp_ring *)0) == 0U);
	CHECK(post(LINE, 0U, PAYLOAD_MAX + 1U, 0U) == 0);
	expect_writer_failed();
	CHECK(be_mvp_ring_taken(&writer) == 0U);
	CHECK(be_mvp_ring_published(&writer) == 0U);
	CHECK(ring_head.value == 64U && ring_tail.value == 64U);
}

/*
 * A malformed record written by hand: the reader refuses it, zeroes the
 * record, writes no tail, and stays failed.
 */
static void expect_take_refused(be_u64 position, be_u64 head)
{
	ring_head.value = head;
	CHECK(be_mvp_ring_acquire(&reader) == head - position);
	CHECK(be_mvp_ring_take(&reader, &record) == BE_MVP_RING_INVALID);
	CHECK(record_zero());
	expect_reader_failed();
	CHECK(ring_tail.value == 0U);
}

static void malformed(be_u64 types, be_u32 domain, be_u64 type,
		      be_u64 record_domain, be_u64 length, be_u64 reserved,
		      be_u64 head)
{
	SCENARIO();
	setup(SMALL, 0U, types, domain);
	raw_record(0U, type, record_domain, length, reserved, 7U);
	expect_take_refused(0U, head);
}

static void test_reader_validation(void)
{
	be_u64 size;

	/* The header: type, ring, domain, length, and reserved word. */
	malformed(OUT, 0U, BE_MVP_RECORD_NONE, 0U, 0U, 0U, 16U);
	malformed(OUT, 0U, BE_MVP_RECORD_COUNT, 0U, 0U, 0U, 16U);
	malformed(OUT, 0U, 0xffU, 0U, 0U, 0U, 16U);
	malformed(OUT, 0U, BE_MVP_RECORD_PING, 0U, 0U, 0U, 16U);
	malformed(OUT, 0U, BE_MVP_RECORD_ACK, 0U, 0U, 0U, 16U);
	malformed(IN, 1U, BE_MVP_RECORD_READY, 1U, 0U, 0U, 16U);
	malformed(IN, 1U, BE_MVP_RECORD_FAIL, 1U, 8U, 0U, 24U);
	malformed(BE_MVP_RECORD_BIT(LINE), 0U, BE_MVP_RECORD_PONG, 0U, 0U, 0U,
		  16U);
	malformed(OUT, 0U, LINE, 1U, 0U, 0U, 16U);
	malformed(OUT, 1U, LINE, 0U, 0U, 0U, 16U);
	malformed(OUT, 0U, LINE, 0xffU, 0U, 0U, 16U);
	malformed(OUT, 0U, LINE, 0U, 257U, 0U, SMALL);
	malformed(OUT, 0U, LINE, 0U, 0xffffU, 0U, SMALL);
	malformed(OUT, 0U, LINE, 0U, 0U, 1U, 16U);
	malformed(OUT, 0U, LINE, 0U, 0U, 0x80000000U, 16U);
	malformed(OUT, 0U, LINE, 0U, 0U, 0x00ff0000U, 16U);
	/* Records that cross the acquired head, or a head inside a header. */
	malformed(OUT, 0U, LINE, 0U, 16U, 0U, 16U);
	malformed(OUT, 0U, LINE, 0U, 8U, 0U, 16U);
	malformed(OUT, 0U, LINE, 0U, 256U, 0U, 264U);
	malformed(OUT, 0U, LINE, 0U, 0U, 0U, 8U);

	/* Padding past the payload must be zero. */
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	raw_record(0U, LINE, 0U, 1U, 0U, 7U);
	raw_le(16U, 'x', 1U);
	raw_le(23U, 0x20U, 1U);
	expect_take_refused(0U, 24U);
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	raw_record(0U, LINE, 0U, 9U, 0U, 7U);
	raw_le(16U + 15U, 1U, 1U);
	expect_take_refused(0U, 32U);

	/* A good record, then a bad one: the first is kept, then the view
	 * fails before its tail moves. */
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(post(LINE, 5U, 3U, 9U) == 1);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	size = be_mvp_ring_record_bytes(3U);
	raw_record(size, BE_MVP_RECORD_PING, 0U, 0U, 0U, 6U);
	ring_head.value = size + 16U;
	CHECK(be_mvp_ring_acquire(&reader) == size + 16U);
	expect_record(LINE, 5U, 3U, 9U);
	CHECK(be_mvp_ring_take(&reader, &record) == BE_MVP_RING_INVALID);
	CHECK(record_zero());
	expect_reader_failed();
	CHECK(ring_tail.value == 0U);

	/* Malformed heads: misaligned, beyond a capacity, behind the
	 * reader, or behind the tail. */
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	ring_head.value = 4U;
	CHECK(be_mvp_ring_acquire(&reader) == 0U);
	expect_reader_failed();
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	ring_head.value = SMALL + 8U;
	CHECK(be_mvp_ring_acquire(&reader) == 0U);
	expect_reader_failed();
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	ring_head.value = SMALL;
	CHECK(be_mvp_ring_acquire(&reader) == SMALL);
	CHECK(reader.failed == 0U);
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(post(LINE, 1U, 8U, 1U) == 1);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(be_mvp_ring_acquire(&reader) == 24U);
	expect_record(LINE, 1U, 8U, 1U);
	ring_head.value = 16U;
	CHECK(be_mvp_ring_acquire(&reader) == 0U);
	expect_reader_failed();
	SCENARIO();
	setup(SMALL, 64U, OUT, 0U);
	ring_head.value = 32U;
	CHECK(be_mvp_ring_acquire(&reader) == 0U);
	expect_reader_failed();

	/* No record to fill: the call fails the view. */
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_take(&reader, (struct be_mvp_record *)0) ==
	      BE_MVP_RING_INVALID);
	expect_reader_failed();
	CHECK(be_mvp_ring_take((struct be_mvp_ring *)0, &record) ==
	      BE_MVP_RING_INVALID);
	CHECK(be_mvp_ring_take((struct be_mvp_ring *)0,
			       (struct be_mvp_record *)0) ==
	      BE_MVP_RING_INVALID);
}

static void test_writer_validation(void)
{
	static const be_u64 words[3] = {
		BE_U64_C(0x0102030405060708), BE_U64_C(0x1112131415161718),
		ALL_ONES,
	};
	be_u64 index;

	/* Types the ring does not carry. */
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(post(BE_MVP_RECORD_NONE, 0U, 0U, 0U) == 0);
	expect_writer_failed();
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(post(BE_MVP_RECORD_COUNT, 0U, 0U, 0U) == 0);
	expect_writer_failed();
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(post(200U, 0U, 0U, 0U) == 0);
	expect_writer_failed();
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(post(BE_MVP_RECORD_PING, 0U, 0U, 0U) == 0);
	expect_writer_failed();
	SCENARIO();
	setup(SMALL, 0U, IN, 1U);
	CHECK(post(BE_MVP_RECORD_READY, 0U, 0U, 0U) == 0);
	expect_writer_failed();

	/* Lengths and payloads. */
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(post(LINE, 0U, 257U, 0U) == 0);
	expect_writer_failed();
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_post(&writer, LINE, 0U, (const be_u8 *)0, 1U) == 0);
	expect_writer_failed();
	SCENARIO();
	setup(SMALL, 0U, OUT, 1U);
	CHECK(be_mvp_ring_post(&writer, LINE, 4U, (const be_u8 *)0, 0U) == 1);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(be_mvp_ring_acquire(&reader) == 16U);
	expect_record(LINE, 4U, 0U, 0U);

	/* Words: little-endian, at most 32, present when counted. */
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_post_words(&writer, BE_MVP_RECORD_PONG, 3U, words,
				     3U) == 1);
	CHECK(be_mvp_ring_post_words(&writer, BE_MVP_RECORD_PONG, 4U,
				     (const be_u64 *)0, 0U) == 1);
	CHECK(be_mvp_ring_publish(&writer) == 1);
	CHECK(be_mvp_ring_acquire(&reader) == 56U);
	CHECK(be_mvp_ring_take(&reader, &record) == BE_MVP_RING_RECORD);
	CHECK(record.type == BE_MVP_RECORD_PONG && record.length == 24U);
	for (index = 0U; index < 8U; ++index)
		CHECK(record.payload[index] == 8U - index);
	CHECK(be_mvp_record_word(&record, 0U) == words[0]);
	CHECK(be_mvp_record_word(&record, 1U) == words[1]);
	CHECK(be_mvp_record_word(&record, 2U) == words[2]);
	CHECK(be_mvp_record_word(&record, 3U) == 0U);
	CHECK(be_mvp_ring_take(&reader, &record) == BE_MVP_RING_RECORD);
	CHECK(record.length == 0U && record.time == 4U);
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_post_words(&writer, BE_MVP_RECORD_PONG, 0U, words,
				     33U) == 0);
	expect_writer_failed();
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_post_words(&writer, BE_MVP_RECORD_PONG, 0U,
				     (const be_u64 *)0, 1U) == 0);
	expect_writer_failed();

	/* The reader's tail: aligned, at or behind the published head, by at
	 * most a capacity. */
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	ring_tail.value = 4U;
	CHECK(post(LINE, 0U, 0U, 0U) == 0);
	expect_writer_failed();
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	ring_tail.value = 64U;
	CHECK(post(LINE, 0U, 0U, 0U) == 0);
	expect_writer_failed();
	SCENARIO();
	setup(SMALL, 1024U, OUT, 0U);
	ring_tail.value = 1024U - SMALL - 8U;
	CHECK(post(LINE, 0U, 0U, 0U) == 0);
	expect_writer_failed();
	SCENARIO();
	setup(SMALL, 1024U, OUT, 0U);
	ring_tail.value = 1024U - SMALL;
	CHECK(post(LINE, 0U, 0U, 0U) == 0);
	expect_writer_failed();
}

/* A call on the other side's view, or with no view, is refused. */
static void test_roles(void)
{
	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_acquire(&writer) == 0U);
	expect_writer_failed();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_take(&writer, &record) == BE_MVP_RING_INVALID);
	expect_writer_failed();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_release(&writer) == 0);
	expect_writer_failed();
	CHECK(ring_tail.value == 0U);

	SCENARIO();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_post(&reader, LINE, 0U, (const be_u8 *)0, 0U) == 0);
	expect_reader_failed();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_post_words(&reader, LINE, 0U, (const be_u64 *)0,
				     0U) == 0);
	expect_reader_failed();
	setup(SMALL, 0U, OUT, 0U);
	CHECK(be_mvp_ring_publish(&reader) == 0);
	expect_reader_failed();
	CHECK(ring_head.value == 0U);

	SCENARIO();
	CHECK(be_mvp_ring_post((struct be_mvp_ring *)0, LINE, 0U,
			       (const be_u8 *)0, 0U) == 0);
	CHECK(be_mvp_ring_post_words((struct be_mvp_ring *)0, LINE, 0U,
				     (const be_u64 *)0, 0U) == 0);
	CHECK(be_mvp_ring_publish((struct be_mvp_ring *)0) == 0);
	CHECK(be_mvp_ring_acquire((struct be_mvp_ring *)0) == 0U);
	CHECK(be_mvp_ring_release((struct be_mvp_ring *)0) == 0);
}

static void test_record_word(void)
{
	SCENARIO();
	memset(&record, 0, sizeof(record));
	record.length = 12U;
	record.payload[0] = 0x11U;
	record.payload[7] = 0x88U;
	record.payload[8] = 0x99U;
	CHECK(be_mvp_record_word(&record, 0U) == BE_U64_C(0x8800000000000011));
	CHECK(be_mvp_record_word(&record, 1U) == 0U);
	record.length = 16U;
	CHECK(be_mvp_record_word(&record, 1U) == 0x99U);
	record.length = PAYLOAD_MAX;
	record.payload[PAYLOAD_MAX - 1U] = 0x77U;
	CHECK(be_mvp_record_word(&record, 31U) == BE_U64_C(0x7700000000000000));
	CHECK(be_mvp_record_word(&record, 32U) == 0U);
	CHECK(be_mvp_record_word(&record, ALL_ONES) == 0U);
	CHECK(be_mvp_record_word((const struct be_mvp_record *)0, 0U) == 0U);
}

/* The layout's rings, as hart 0 and a domain hart use them. */
static void test_layout_rings(void)
{
	static be_u8 inbound[BE_MVP_INBOUND_RING_BYTES];
	struct be_mvp_ring_index index[4];
	struct be_mvp_ring hart0_in;
	struct be_mvp_ring hart0_out;
	struct be_mvp_ring hart_in;
	struct be_mvp_ring hart_out;
	be_u64 sent;

	SCENARIO();
	memset(index, 0x5a, sizeof(index));
	be_mvp_ring_reset(&index[0], &index[1]);
	be_mvp_ring_reset(&index[2], &index[3]);
	CHECK(be_mvp_ring_init(&hart0_in, inbound, BE_MVP_INBOUND_RING_BYTES,
			       &index[0], &index[1], IN, 1U, WRITER) == 1);
	CHECK(be_mvp_ring_init(&hart_in, inbound, BE_MVP_INBOUND_RING_BYTES,
			       &index[0], &index[1], IN, 1U, READER) == 1);
	CHECK(be_mvp_ring_init(&hart_out, buffer, BE_MVP_OUTBOUND_RING_BYTES,
			       &index[2], &index[3], OUT, 1U, WRITER) == 1);
	CHECK(be_mvp_ring_init(&hart0_out, buffer, BE_MVP_OUTBOUND_RING_BYTES,
			       &index[2], &index[3], OUT, 1U, READER) == 1);
	/* hart 0: PING; the domain hart: PONG with its words. */
	CHECK(be_mvp_ring_post(&hart0_in, BE_MVP_RECORD_PING, 100U,
			       (const be_u8 *)0, 0U) == 1);
	CHECK(be_mvp_ring_publish(&hart0_in) == 1 && index[0].value == 16U);
	CHECK(be_mvp_ring_acquire(&hart_in) == 16U);
	CHECK(be_mvp_ring_take(&hart_in, &record) == BE_MVP_RING_RECORD);
	CHECK(record.type == BE_MVP_RECORD_PING && record.time == 100U &&
	      record.domain == 1U && record.length == 0U);
	sent = record.time;
	CHECK(be_mvp_ring_release(&hart_in) == 1 && index[1].value == 16U);
	CHECK(be_mvp_ring_take(&hart_in, &record) == BE_MVP_RING_EMPTY);
	CHECK(be_mvp_ring_post_words(&hart_out, BE_MVP_RECORD_PONG, 120U,
				     &sent, 1U) == 1);
	CHECK(be_mvp_ring_publish(&hart_out) == 1 && index[2].value == 24U);
	CHECK(be_mvp_ring_acquire(&hart0_out) == 24U);
	CHECK(be_mvp_ring_take(&hart0_out, &record) == BE_MVP_RING_RECORD);
	CHECK(record.type == BE_MVP_RECORD_PONG && record.time == 120U &&
	      be_mvp_record_word(&record, 0U) == 100U);
	CHECK(be_mvp_ring_release(&hart0_out) == 1 && index[3].value == 24U);
	CHECK(index[0].value == 16U && index[1].value == 16U);
	CHECK(be_mvp_ring_peak(&hart_out) == 24U &&
	      be_mvp_ring_peak(&hart0_in) == 16U);
	/* Each index sits alone in its own 64-byte line. */
	CHECK((be_u64)((const char *)&index[1] - (const char *)&index[0]) ==
	      64U);
	CHECK(((be_u64)(unsigned long)&index[0] & 63U) == 0U);
}

/*
 * Pseudo-random runs against a queue model: random posts the model says
 * fit, publishes, acquires, takes, and releases, every record and index
 * checked; then posts until the model says the next does not fit, which
 * must be refused exactly there.
 */
#define MODEL_RECORDS		1024U

struct model_record {
	be_u32 type;
	be_u64 time;
	be_u64 length;
	be_u64 seed;
};

static struct model_record model[MODEL_RECORDS];
static be_u64 random_state;

static be_u64 next_random(void)
{
	random_state ^= random_state << 13;
	random_state ^= random_state >> 7;
	random_state ^= random_state << 17;
	return random_state;
}

static const be_u32 outbound_types[] = {
	BE_MVP_RECORD_READY, BE_MVP_RECORD_ENTERED, BE_MVP_RECORD_LINE,
	BE_MVP_RECORD_PONG, BE_MVP_RECORD_SHUTDOWN, BE_MVP_RECORD_FAIL,
};

static void simulate(be_u64 capacity, be_u64 start, be_u64 seed,
		     unsigned int steps)
{
	be_u64 posted = 0U;
	be_u64 published = 0U;
	be_u64 acquired = 0U;
	be_u64 taken = 0U;
	be_u64 cursor = 0U;
	be_u64 head = 0U;
	be_u64 limit = 0U;
	be_u64 reader_cursor = 0U;
	be_u64 tail = 0U;
	be_u64 peak = 0U;
	be_u64 time = 0U;
	be_u64 size;
	unsigned int step;

	SCENARIO();
	random_state = seed;
	setup(capacity, start, OUT, (be_u32)(seed & 1U));
	for (step = 0U; step < steps; ++step) {
		be_u64 choice = next_random() % 8U;

		if (choice <= 2U) {
			struct model_record *entry = &model[posted %
							   MODEL_RECORDS];

			entry->type = outbound_types[
				next_random() % BE_ARRAY_SIZE(outbound_types)];
			entry->length = next_random() % 2U == 0U ?
				next_random() % 33U : next_random() % 257U;
			entry->seed = next_random();
			time += next_random() % 100U;
			entry->time = time;
			size = be_mvp_ring_record_bytes(entry->length);
			if (size > capacity - (cursor - tail) ||
			    posted - taken >= MODEL_RECORDS)
				continue;
			CHECK(post(entry->type, entry->time, entry->length,
				   entry->seed) == 1);
			cursor += size;
			++posted;
			if (cursor - tail > peak)
				peak = cursor - tail;
			CHECK(be_mvp_ring_peak(&writer) == peak);
		} else if (choice == 3U) {
			CHECK(be_mvp_ring_publish(&writer) == 1);
			head = cursor;
			published = posted;
			CHECK(ring_head.value == start + head);
		} else if (choice == 4U) {
			CHECK(be_mvp_ring_acquire(&reader) ==
			      head - reader_cursor);
			limit = head;
			acquired = published;
		} else if (choice <= 6U) {
			if (taken == acquired) {
				CHECK(reader_cursor == limit);
				expect_empty();
				continue;
			}
			expect_record(model[taken % MODEL_RECORDS].type,
				      model[taken % MODEL_RECORDS].time,
				      model[taken % MODEL_RECORDS].length,
				      model[taken % MODEL_RECORDS].seed);
			reader_cursor += be_mvp_ring_record_bytes(
				model[taken % MODEL_RECORDS].length);
			++taken;
		} else {
			CHECK(be_mvp_ring_release(&reader) == 1);
			tail = reader_cursor;
			CHECK(ring_tail.value == start + tail);
		}
		CHECK(writer.failed == 0U && reader.failed == 0U);
		CHECK(be_mvp_ring_taken(&writer) == start + tail &&
		      be_mvp_ring_published(&writer) == start + head);
	}
	/* Fill to the model's last fit, then the refusal. */
	for (step = 0U; step <= capacity / BE_MVP_RECORD_HEADER_BYTES; ++step) {
		be_u64 length = next_random() % 257U;

		size = be_mvp_ring_record_bytes(length);
		if (size > capacity - (cursor - tail)) {
			memcpy(snapshot, buffer, sizeof(buffer));
			CHECK(post(LINE, time, length, step) == 0);
			CHECK(memcmp(snapshot, buffer, sizeof(buffer)) == 0);
			expect_writer_failed();
			CHECK(be_mvp_ring_peak(&writer) == peak);
			return;
		}
		CHECK(post(LINE, time, length, step) == 1);
		cursor += size;
		if (cursor - tail > peak)
			peak = cursor - tail;
	}
	CHECK(0);
}

static void test_simulation(void)
{
	simulate(SMALL, 0U, BE_U64_C(0x9e3779b97f4a7c15), 20000U);
	simulate(BE_MVP_VARIANT_OUTBOUND_RING_BYTES, ALL_ONES - 255U,
		 BE_U64_C(0x2545f4914f6cdd1d), 20000U);
	simulate(BE_MVP_INBOUND_RING_BYTES, BE_U64_C(0x40),
		 BE_U64_C(0xd1b54a32d192ed03), 20000U);
	simulate(BE_MVP_OUTBOUND_RING_BYTES, BE_U64_C(0x7ff8),
		 BE_U64_C(0x8cb92ba72f3d8dd7), 20000U);
}

int main(void)
{
	test_constants();
	test_reset();
	test_init();
	test_fill_levels();
	test_wrap();
	test_visibility();
	test_peak();
	test_writer_reads();
	test_reader_validation();
	test_writer_validation();
	test_roles();
	test_record_word();
	test_layout_rings();
	test_simulation();
	printf("BE_MVP_RING_CHECK: PASS\n");
	printf("BE_MVP_RING_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_MVP_RING_CHECK: assertions=%lu\n", assertions);
	return 0;
}
