/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC sequence harness for mvp-ring.c (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, accepted at 93a8d136,
 *          SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "For a writer and a reader view on one buffer: post, publish;
 *          acquire, take, release, across a wrap of the positions (a start
 *          index near 2^64 - 256 and one near C), returns the posted record
 *          byte for byte, and after release the writer's free bytes,
 *          C - (cursor - tail), grow by the released record's size (room
 *          itself is the payload a next record may carry, counted after its
 *          16-byte header and capped at 256, so it grows by the released
 *          size only until the cap) [R1-9]." Transcribed as the row states
 *          it: the free bytes are C - (cursor - tail) with the writer
 *          view's cursor and the tail's index line, just before and just
 *          after the release (the parenthesis on room explains it and adds
 *          no property). A bounded model check, never a proof.
 * Trust:   harness code (harness.h). Both views are built by
 *          be_mvp_ring_init on one buffer with one type set and domain and
 *          the ring empty (head = tail = the start index); both accepted
 *          (the row's subject: a writer and a reader view). The start
 *          index's position is a class of the window [C - 512, C)
 *          (BE_CBMC_POSITION, one run per class) and its other bits are
 *          arbitrary, so the start indices run over both of the row's
 *          windows, 2^64 - 512 to 2^64 - 8 and C - 512 to C - 8, and every
 *          lap between: records that end before, at, and across the wrap of
 *          the positions, and across 2^64. The record: a type in the set,
 *          a length of at most 256, LENGTH valid payload bytes or none, any
 *          time.
 * Scope:   Leaf B of the M8 pilot (planning/mvp-m8-plan.md, D-8).
 */
#include "harness.h"

#ifdef BE_CBMC_POSITION
_Static_assert((be_u64)BE_CBMC_POSITION + 512U >= CAPACITY,
	       "the sequence's start positions are the window [C - 512, C)");
#endif

int main(void)
{
	be_u8 buffer[BE_CBMC_CAPACITY];
	be_u8 payload[PAYLOAD_MAX];
	struct be_mvp_ring_index head;
	struct be_mvp_ring_index tail;
	struct be_mvp_ring writer;
	struct be_mvp_ring reader;
	struct be_mvp_record record;
	be_u64 start = own_index();
	be_u64 types = nondet_u64();
	be_u32 domain = nondet_u32();
	be_u64 type = nondet_u32();
	be_u64 time = nondet_u64();
	be_u64 length = nondet_u64();
	const be_u8 *data = (length == 0U && nondet_bool()) ? (const be_u8 *)0 :
							     payload;
	be_u64 size = spec_record_bytes(length);
	be_u64 free_before;
	be_u64 free_after;
	be_u64 offset;
	enum be_mvp_ring_status status;
	int writer_ok;
	int reader_ok;

	head.value = start;
	tail.value = start;
	writer_ok = be_mvp_ring_init(&writer, buffer, CAPACITY, &head, &tail,
				     types, domain, BE_MVP_RING_WRITER);
	__CPROVER_assume(writer_ok == 1);
	restate(&writer, buffer, &head, &tail, start);
	reader_ok = be_mvp_ring_init(&reader, buffer, CAPACITY, &head, &tail,
				     types, domain, BE_MVP_RING_READER);
	__CPROVER_assume(reader_ok == 1);
	restate(&reader, buffer, &head, &tail, start);
	__CPROVER_assume(spec_in_set(types, type) && length <= PAYLOAD_MAX);

	(void)be_mvp_ring_post(&writer, (enum be_mvp_record_type)type, time,
			       data, length);
	(void)be_mvp_ring_publish(&writer);
	(void)be_mvp_ring_acquire(&reader);
	status = be_mvp_ring_take(&reader, &record);
	free_before = CAPACITY - (writer.cursor - tail.value);
	(void)be_mvp_ring_release(&reader);
	free_after = CAPACITY - (writer.cursor - tail.value);

#ifdef BE_CBMC_COVER
	/* The wraps the row names are reached: the record crosses the end of
	 * the buffer, and its indices cross 2^64. */
	__CPROVER_cover(OWN_POSITION(start) + size > CAPACITY);
	__CPROVER_cover(start + size < start);
#endif
	PROPERTY(status == BE_MVP_RING_RECORD && record.type == type &&
		 record.domain == domain && record.length == length &&
		 record.time == time,
		 "sequence: take returns the posted record (type, domain, length, time)");
	for (offset = 0U; offset < PAYLOAD_MAX; ++offset)
		if (offset < length)
			PROPERTY(record.payload[offset] == payload[offset],
				 "sequence: take returns the posted record's payload byte for byte");
	PROPERTY(free_after == free_before + size,
		 "sequence: after release the writer's free bytes, C - (cursor - tail), grow by the released record's size");
	VACUITY_PROBE();
	return 0;
}
