/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_ring_room (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, accepted at 93a8d136,
 *          SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "For a writer view not failed with a well-formed tail (as post
 *          reads it: aligned, with limit - t <= C) [R1-6]: returns the
 *          largest n <= 256 such that a record of payload n would fit, or 0
 *          if none fits; writes nothing and never fails the view for want
 *          of room; a malformed tail, a reader's view, or a failed view
 *          returns 0 and fails the view." A bounded model check, never a
 *          proof.
 * Trust:   harness code (harness.h). A well-formed tail t is the row's:
 *          aligned, and limit - t <= C in u64 (the published head, the
 *          view's limit, bounds the reader); a record of payload n fits
 *          when cursor - t <= C and cursor - t + record_bytes(n) <= C,
 *          post's conditions after its tail's. "The largest n" is asserted
 *          relationally: the answer fits when any record fits, and no
 *          n <= 256 that fits exceeds it (n arbitrary). The well-formed
 *          case's properties are asserted in two cases of the bytes in use,
 *          cursor - t at most C or more than C (with a record posted and
 *          not published, the cursor can be more than C past a tail that
 *          is well formed: then no record fits), so that a failure names
 *          its case. The view: either side's, built by
 *          be_mvp_ring_init (or refused by it), a writer's perhaps after an
 *          empty record posted and perhaps published, perhaps failed since,
 *          the peer's index any u64.
 * Scope:   Leaf B of the M8 pilot (planning/mvp-m8-plan.md, D-8).
 */
#include "harness.h"

static int fits(be_u64 used, be_u64 n)
{
	return used <= CAPACITY && used + spec_record_bytes(n) <= CAPACITY;
}

int main(void)
{
	be_u8 buffer[BE_CBMC_CAPACITY];
	struct be_mvp_ring_index head;
	struct be_mvp_ring_index tail;
	struct be_mvp_ring view;
	struct be_mvp_ring before;
	LINES_DECLARE();
	PROBE_DECLARE();
	enum be_mvp_ring_role role = any_side();
	be_u64 result;
	be_u64 used;
	be_u64 t;
	be_u64 n = nondet_u64();

	(void)build(&view, buffer, &head, &tail, role, own_index());
	if (role == BE_MVP_RING_WRITER)
		writer_prefix(&view);
	else
		reader_prefix(&view, &head);
	fail_maybe(&view);
	havoc_peer(&head, &tail, role);
	before = view;
	LINES_RECORD(head, tail);
	PROBE_RECORD(buffer);
	t = tail.value;
	used = before.cursor - t;

	result = be_mvp_ring_room(&view);

	if (before.role == BE_MVP_RING_WRITER && before.failed == 0U &&
	    (t & 7U) == 0U && before.limit - t <= CAPACITY &&
	    used > CAPACITY) {
		/* A well-formed tail the cursor is more than C past: no
		 * record fits. One property for this case, so that a failure
		 * names it. */
		PROPERTY(result <= PAYLOAD_MAX && (!fits(used, 0U) ||
						    fits(used, result)) &&
			 (fits(used, 0U) || result == 0U) &&
			 (n > PAYLOAD_MAX || !fits(used, n) || n <= result) &&
			 view_unchanged(&before, &view) &&
			 LINES_UNCHANGED(head, tail) && PROBE_UNCHANGED(buffer),
			 "room: a well-formed tail the cursor is more than C past (none fits): 0, writes nothing, the view not failed");
	} else if (before.role == BE_MVP_RING_WRITER && before.failed == 0U &&
		   (t & 7U) == 0U && before.limit - t <= CAPACITY) {
		PROPERTY(result <= PAYLOAD_MAX && (!fits(used, 0U) ||
						    fits(used, result)),
			 "room: a well-formed tail: at most 256, and a record of that payload fits when any does");
		PROPERTY(fits(used, 0U) || result == 0U,
			 "room: a well-formed tail: 0 if none fits");
		PROPERTY(n > PAYLOAD_MAX || !fits(used, n) || n <= result,
			 "room: a well-formed tail: no larger payload <= 256 fits");
		PROPERTY(view_unchanged(&before, &view) &&
			 LINES_UNCHANGED(head, tail) &&
			 PROBE_UNCHANGED(buffer),
			 "room: a well-formed tail: writes nothing, the view not failed");
	} else {
		PROPERTY(result == 0U && view.failed != 0U,
			 "room: a malformed tail, a reader's view, or a failed view: 0 and the view failed");
	}
	VACUITY_PROBE();
	return 0;
}
