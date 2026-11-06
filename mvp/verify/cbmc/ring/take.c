/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_ring_take (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, this row unchanged by
 *          it, accepted at 93a8d136, SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "For a reader view not failed: if limit - cursor = 0 returns EMPTY
 *          and record is zero; else reads the header at cursor, and if its
 *          type is in the view's set, its domain the view's, its length
 *          <= 256, its reserved word 0, its padding zero, and
 *          record_bytes(length) <= limit - cursor, copies type, domain,
 *          length, time, and payload into record, advances cursor by the
 *          record's size, and returns RECORD; otherwise returns INVALID,
 *          fails the view, and record is zero. Reads only positions in
 *          [cursor, limit); writes no buffer byte and no index."
 *          A bounded model check, never a proof.
 * Trust:   harness code (harness.h). Two parts, a case split on the view
 *          before the call whose union is every view: the scalar part, the
 *          own index wholly arbitrary, the views that read no buffer byte
 *          (a view init refused, a failed or a writer's view, a reader's
 *          with limit = cursor); the buffer part, one run per position
 *          class (BE_CBMC_POSITION), a reader's view not failed after an
 *          acquire of any head with limit != cursor. The buffer part's
 *          model computes every conclusion from the bytes at positions
 *          [cursor, limit) alone (the header only when 16 bytes are
 *          there, the payload and padding only when the record is): the
 *          result, the record, and the view being equal to it for every
 *          buffer is "reads only positions in [cursor, limit)" as a check
 *          can state it (CBMC has no read hook: a read whose value goes
 *          unused would not show). The record is zero means each of its
 *          fields and every payload byte.
 * Scope:   Leaf B of the M8 pilot (planning/mvp-m8-plan.md, D-8).
 */
#include "harness.h"

static int record_zero(const struct be_mvp_record *record, be_u64 j)
{
	return record->type == 0U && record->domain == 0U &&
	       record->length == 0U && record->time == 0U &&
	       record->payload[j] == 0U;
}

int main(void)
{
	be_u8 buffer[BE_CBMC_CAPACITY];
	struct be_mvp_ring_index head;
	struct be_mvp_ring_index tail;
	struct be_mvp_ring view;
	struct be_mvp_ring before;
	struct be_mvp_record record;
	LINES_DECLARE();
	PROBE_DECLARE();
	be_u64 own = own_index();
	be_u64 j = nondet_u64();
	enum be_mvp_ring_status status;
#if BUFFER_PART
	enum be_mvp_ring_role role = BE_MVP_RING_READER;
	be_u64 base = OWN_POSITION(own);
	be_u64 avail, type, domain, length, reserved, time, size, offset;
	int valid;
	int padding_zero = 1;
#else
	enum be_mvp_ring_role role = any_side();
	int ok;
#endif

	__CPROVER_assume(j < PAYLOAD_MAX);
#if BUFFER_PART
	if (!build(&view, buffer, &head, &tail, role, own))
		return 0;
	restate(&view, buffer, &head, &tail, own);
	head.value = nondet_u64();
	(void)be_mvp_ring_acquire(&view);
	__CPROVER_assume(view.failed == 0U && view.limit != view.cursor);
#else
	ok = build(&view, buffer, &head, &tail, role, own);
	if (ok && role == BE_MVP_RING_READER)
		reader_prefix(&view, &head);
	fail_maybe(&view);
	__CPROVER_assume(!(view.role == BE_MVP_RING_READER &&
			   view.failed == 0U && view.limit != view.cursor));
#endif
	havoc_peer(&head, &tail, role);
	before = view;
	LINES_RECORD(head, tail);
	PROBE_RECORD(buffer);

#if BUFFER_PART
	/* The model, from the window [cursor, limit) only. */
#define WINDOW(o)	buffer[spec_position(base + (o))]
	avail = before.limit - before.cursor;
	type = avail >= HEADER ? WINDOW(0U) : 0U;
	domain = avail >= HEADER ? WINDOW(1U) : 0U;
	length = avail >= HEADER ?
		 ((be_u64)WINDOW(2U) | (be_u64)WINDOW(3U) << 8) : 0U;
	reserved = avail >= HEADER ?
		   ((be_u64)WINDOW(4U) | (be_u64)WINDOW(5U) << 8 |
		    (be_u64)WINDOW(6U) << 16 | (be_u64)WINDOW(7U) << 24) : 0U;
	time = 0U;
	for (offset = 8U; offset < HEADER; ++offset)
		if (avail >= HEADER)
			time |= (be_u64)WINDOW(offset) << (8U * (offset - 8U));
	size = spec_record_bytes(length);
	for (offset = HEADER; offset < RECORD_MAX; ++offset)
		if (offset - HEADER >= length && offset < size &&
		    size <= avail && WINDOW(offset) != 0U)
			padding_zero = 0;
	valid = avail >= HEADER && spec_in_set(before.types, type) &&
		domain == before.domain && length <= PAYLOAD_MAX &&
		reserved == 0U && size != 0U && size <= avail && padding_zero;
#endif

	status = be_mvp_ring_take(&view, &record);

#if SCALAR_PART
	if (before.role == BE_MVP_RING_READER && before.failed == 0U)
		PROPERTY(status == BE_MVP_RING_EMPTY && record_zero(&record, j),
			 "take: limit - cursor = 0: EMPTY, the record zero");
#endif
#if BUFFER_PART
	PROPERTY(status == (valid ? BE_MVP_RING_RECORD : BE_MVP_RING_INVALID),
		 "take: limit - cursor != 0: RECORD iff the header and padding are well formed and the record fits, else INVALID");
	if (status == BE_MVP_RING_RECORD) {
		PROPERTY(record.type == type && record.domain == before.domain &&
			 record.length == length && record.time == time,
			 "take: on RECORD, type, domain, length, and time copied");
		for (offset = 0U; offset < PAYLOAD_MAX; ++offset)
			if (offset < length)
				PROPERTY(record.payload[offset] ==
					 WINDOW(HEADER + offset),
					 "take: on RECORD, the payload copied");
		PROPERTY(view.cursor == before.cursor + size,
			 "take: on RECORD, cursor advanced by the record's size");
	} else {
		PROPERTY(view.failed != 0U && record_zero(&record, j),
			 "take: on INVALID, the view failed and the record zero");
	}
#undef WINDOW
#endif
	PROPERTY(LINES_UNCHANGED(head, tail), "take: writes no index");
	PROPERTY(PROBE_UNCHANGED(buffer), "take: writes no buffer byte");
	VACUITY_PROBE();
	return 0;
}
