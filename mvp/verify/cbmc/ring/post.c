/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_ring_post (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, accepted at 93a8d136,
 *          SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "For a writer view not failed, type in the view's type set,
 *          length <= 256, payload non-null when length > 0, and the peer's
 *          tail t well formed: a multiple of 8 with limit - t <= C (at or
 *          behind the head the writer has published, by at most a
 *          capacity) [R1-6], and cursor - t <= C and cursor - t +
 *          record_bytes(length) <= C: returns 1, writes exactly the
 *          record's record_bytes(length) bytes (header, payload, zero
 *          padding) at positions cursor .. cursor + size - 1 masked, writes
 *          no other buffer byte and no index, advances cursor by size, and
 *          updates peak to the most bytes in use seen; otherwise returns 0,
 *          writes no buffer byte, and the view is failed (a malformed tail,
 *          not aligned or more than C behind the published head, fails it
 *          too)." A bounded model check, never a proof.
 * Trust:   harness code (harness.h). The scalar part asserts the result,
 *          the cursor, the peak, the failed view, and the index lines, with
 *          the own index wholly arbitrary and a writer's view perhaps after
 *          an empty record posted and perhaps published; the buffer part
 *          asserts every buffer byte, one run per position class
 *          (BE_CBMC_POSITION), the classes together every own index, the
 *          view as init built it: the buffer bytes after a prefix's empty
 *          record are not asserted (a bound, recorded: CBMC did not answer
 *          one buffer byte at an arbitrary position there in 600 s). Each part asserts its conclusions
 *          on the code's result; the scalar part's first assertion equates
 *          that result with the row's conditions, so the parts together
 *          are the row. The payload is LENGTH valid bytes or absent,
 *          whatever LENGTH (the row's condition: non-null when length > 0).
 *          The view: either side's, built by be_mvp_ring_init (or refused
 *          by it), perhaps failed since; the peer's index any u64 at the
 *          call.
 * Scope:   Leaf B of the M8 pilot (planning/mvp-m8-plan.md, D-8).
 */
#include "harness.h"

/* The record's byte at OFFSET: its header, its payload, then zero. */
static be_u8 record_byte(be_u64 offset, be_u64 type, be_u64 domain,
			 be_u64 length, be_u64 time, const be_u8 *payload)
{
	if (offset < HEADER)
		return spec_header_byte(offset, type, domain, length, time);
	if (offset - HEADER < length)
		return payload[offset - HEADER];
	return 0U;
}

#if BUFFER_PART
/* Every buffer byte, the record's offsets counted from BASE, a constant:
 * on 1 the record's bytes, every other byte as SAVED; on 0 every byte. */
static void scan(const be_u8 *buffer, const be_u8 *saved, be_u64 base,
		 int result, be_u64 size, be_u64 type, be_u64 domain,
		 be_u64 length, be_u64 time, const be_u8 *payload)
{
	be_u64 position;

	for (position = 0U; position < CAPACITY; ++position) {
		be_u64 offset = (position - base) & MASK;

		if (result == 1 && offset < size)
			PROPERTY(buffer[position] == record_byte(offset, type,
								 domain, length,
								 time, payload),
				 "post: on 1, the record's bytes (header, payload, zero padding) at cursor .. cursor + size - 1, masked");
		else
			PROPERTY(buffer[position] == saved[position],
				 "post: no other buffer byte; on 0, none");
	}
}
#endif

int main(void)
{
	be_u8 buffer[BE_CBMC_CAPACITY];
#if BUFFER_PART
	be_u8 saved[BE_CBMC_CAPACITY];
#endif
	be_u8 payload[PAYLOAD_MAX];
	struct be_mvp_ring_index head;
	struct be_mvp_ring_index tail;
	struct be_mvp_ring view;
	struct be_mvp_ring before;
	LINES_DECLARE();
	PROBE_DECLARE();
	enum be_mvp_ring_role role = any_side();
	be_u64 own = own_index();
	be_u64 type = nondet_u32();
	be_u64 time = nondet_u64();
	be_u64 length = nondet_u64();
	const be_u8 *data = nondet_bool() ? (const be_u8 *)0 : payload;
	be_u64 size = spec_record_bytes(length);
	be_u64 used;
	be_u64 t;
	int expected;
	int result;

	if (!build(&view, buffer, &head, &tail, role, own)) {
		/* A view init refused is failed (the calls test the flag
		 * against 0): restated, so the call's refusal is a constant. */
		__CPROVER_assume(view.failed != 0U);
		view.failed = 1U;
		PROBE_RECORD(buffer);
		havoc_peer(&head, &tail, role);
		result = be_mvp_ring_post(&view, (enum be_mvp_record_type)type,
					  time, data, length);
#if SCALAR_PART
		PROPERTY(result == 0 && view.failed != 0U,
			 "post: a view init refused: 0, the view failed");
#endif
#if BUFFER_PART
		PROPERTY(PROBE_UNCHANGED(buffer),
			 "post: a view init refused: no buffer byte");
#endif
		return 0;
	}
	restate(&view, buffer, &head, &tail, own);
#if !BUFFER_PART
	if (role == BE_MVP_RING_WRITER)
		writer_prefix(&view);
#endif
	fail_maybe(&view);
	havoc_peer(&head, &tail, role);
	before = view;
	LINES_RECORD(head, tail);
#if BUFFER_PART
	copy_buffer(saved, buffer);
#endif
	t = tail.value;
	used = before.cursor - t;
	expected = before.role == BE_MVP_RING_WRITER && before.failed == 0U &&
		   spec_in_set(before.types, type) && length <= PAYLOAD_MAX &&
		   (data != (const be_u8 *)0 || length == 0U) &&
		   (t & 7U) == 0U && before.limit - t <= CAPACITY &&
		   used <= CAPACITY && used + size <= CAPACITY;

	result = be_mvp_ring_post(&view, (enum be_mvp_record_type)type, time,
				  data, length);

#if SCALAR_PART
	/* One property, asserted as two cases of the view so that a
	 * failure names its case: the cursor at the published head, or past
	 * it (a record posted and not published). */
	if (before.cursor == before.limit)
		PROPERTY(result == (expected ? 1 : 0),
			 "post: returns 1 iff the row's conditions, else 0 (the cursor at the published head)");
	else
		PROPERTY(result == (expected ? 1 : 0),
			 "post: returns 1 iff the row's conditions, else 0 (the cursor past the published head)");
	if (result == 1) {
		PROPERTY(view.cursor == before.cursor + size,
			 "post: on 1, cursor advanced by size");
		PROPERTY(view.peak == (before.peak > used + size ? before.peak :
								   used + size),
			 "post: on 1, peak the most bytes in use seen");
		PROPERTY(LINES_UNCHANGED(head, tail),
			 "post: on 1, writes no index");
	} else {
		PROPERTY(view.failed != 0U, "post: on 0, the view is failed");
	}
#endif
#if BUFFER_PART
	/* The cursor at the call is the own index: a constant position in a
	 * position-class run. */
	scan(buffer, saved, OWN_POSITION(own), result, size, type,
	     before.domain, length, time, payload);
#endif
	VACUITY_PROBE();
	return 0;
}
