/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_ring_acquire (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, accepted at 93a8d136,
 *          SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "For a reader view not failed, the released tail r (the view's
 *          own index line as it stands), and a head h that is a multiple of
 *          8 with h - r <= C and cursor - r <= h - r in u64 (at or past
 *          what this reader has taken, and at most a capacity past the tail
 *          it released) [R1-7]: sets limit := h and returns h - cursor; a
 *          head behind the cursor, more than C past the released tail, or
 *          unaligned returns 0 and fails the view; a writer's or failed
 *          view returns 0. Writes no index and no buffer byte." A bounded
 *          model check, never a proof.
 * Trust:   harness code (harness.h). r is the reader's index line's value
 *          at the call, h the writer's. The view: either side's, built by
 *          be_mvp_ring_init (or refused by it), a reader's perhaps after an
 *          acquire and, with BE_CBMC_READER_TAKE (the runner's, at 512), a
 *          take (so its cursor may lead its released tail), perhaps failed
 *          since; the head h, the writer's index, any u64.
 * Scope:   Leaf B of the M8 pilot (planning/mvp-m8-plan.md, D-8).
 */
#include "harness.h"

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
	be_u64 h;
	be_u64 r;

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
	h = head.value;
	r = lines_tail;

	result = be_mvp_ring_acquire(&view);

	if (before.role == BE_MVP_RING_READER && before.failed == 0U) {
		/* One property, asserted as two cases of the view so that a
		 * failure names its case: the cursor at the released tail, or
		 * past it (a record taken and not released). */
		if ((h & 7U) == 0U && h - r <= CAPACITY &&
		    before.cursor - r <= h - r && before.cursor == r)
			PROPERTY(view.limit == h && result == h - before.cursor,
				 "acquire: an aligned head at or past the cursor, within C of the released tail: limit := h, h - cursor (the cursor at the released tail)");
#ifdef BE_CBMC_READER_TAKE
		/* Only a take moves the cursor past the released tail. */
		else if ((h & 7U) == 0U && h - r <= CAPACITY &&
			 before.cursor - r <= h - r)
			PROPERTY(view.limit == h && result == h - before.cursor,
				 "acquire: an aligned head at or past the cursor, within C of the released tail: limit := h, h - cursor (the cursor past the released tail)");
#endif
		else
			PROPERTY(result == 0U && view.failed != 0U,
				 "acquire: a head behind the cursor, more than C past the released tail, or unaligned: 0 and the view failed");
	} else {
		PROPERTY(result == 0U, "acquire: a writer's or failed view: 0");
	}
	PROPERTY(LINES_UNCHANGED(head, tail),
		 "acquire: writes no index");
	PROPERTY(PROBE_UNCHANGED(buffer),
		 "acquire: writes no buffer byte");
	VACUITY_PROBE();
	return 0;
}
