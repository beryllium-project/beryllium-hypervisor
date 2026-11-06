/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_ring_init (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, accepted at 93a8d136,
 *          SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "Returns 1 iff buffer, head, and tail are non-null, C is a power
 *          of two in [512, 32768], types is a non-empty subset of the
 *          inbound set, the outbound set, or the input set, domain in
 *          {0, 1} [R1-4], role is writer or reader, and the two index
 *          values are multiples of 8 with head - tail <= C in u64; on 1 the
 *          view's cursor is its own index's value (a writer's the head, a
 *          reader's the tail), limit = cursor (the view's own index, not
 *          the peer's ...) [R1-5], peak = head - tail, failed = 0; on 0 the
 *          view is failed. Writes no index and no buffer byte."
 *          Transcribed as the row states it, every argument arbitrary but
 *          the view, which is valid; the buffer and each index line either
 *          absent or valid and distinct. A bounded model check, never a
 *          proof.
 * Trust:   harness code (harness.h); the capacity is an argument here, any
 *          u64, and the buffer either absent or BE_CBMC_CAPACITY bytes.
 * Scope:   Leaf B of the M8 pilot (planning/mvp-m8-plan.md, D-8).
 */
#include "harness.h"

int main(void)
{
	be_u8 buffer[BE_CBMC_CAPACITY];
	struct be_mvp_ring_index head;
	struct be_mvp_ring_index tail;
	struct be_mvp_ring view;
	LINES_DECLARE();
	PROBE_DECLARE();
	be_u8 *given = nondet_bool() ? buffer : (be_u8 *)0;
	struct be_mvp_ring_index *head_given = nondet_bool() ? &head :
		(struct be_mvp_ring_index *)0;
	struct be_mvp_ring_index *tail_given = nondet_bool() ? &tail :
		(struct be_mvp_ring_index *)0;
	be_u64 capacity = nondet_u64();
	be_u64 types = nondet_u64();
	be_u32 domain = nondet_u32();
	enum be_mvp_ring_role role = (enum be_mvp_ring_role)nondet_u32();
	int writer = role == BE_MVP_RING_WRITER;
	int accepted;
	int result;

	LINES_RECORD(head, tail);
	PROBE_RECORD(buffer);
	accepted = given != (be_u8 *)0 &&
		   head_given != (struct be_mvp_ring_index *)0 &&
		   tail_given != (struct be_mvp_ring_index *)0 &&
		   capacity >= 512U && capacity <= 32768U &&
		   (capacity & (capacity - 1U)) == 0U &&
		   spec_types_valid(types) && domain <= 1U &&
		   (role == BE_MVP_RING_WRITER || role == BE_MVP_RING_READER) &&
		   (lines_head & 7U) == 0U && (lines_tail & 7U) == 0U &&
		   lines_head - lines_tail <= capacity;

	result = be_mvp_ring_init(&view, given, capacity, head_given,
				  tail_given, types, domain, role);

	PROPERTY(result == (accepted ? 1 : 0),
		 "init: returns 1 iff the row's conditions (buffer, head, and tail non-null, a domain of 0 or 1), else 0");
	if (result == 1) {
		PROPERTY(view.cursor == (writer ? lines_head : lines_tail),
			 "init: on 1 the cursor is the own index's value");
		PROPERTY(view.limit == view.cursor,
			 "init: on 1 the limit is the cursor, the view's own index");
		PROPERTY(view.peak == lines_head - lines_tail,
			 "init: on 1 the peak is head - tail");
		PROPERTY(view.failed == 0U, "init: on 1 the view is not failed");
	} else {
		PROPERTY(view.failed != 0U, "init: on 0 the view is failed");
	}
	PROPERTY(LINES_UNCHANGED(head, tail),
		 "init: writes no index");
	PROPERTY(PROBE_UNCHANGED(buffer), "init: writes no buffer byte");
	VACUITY_PROBE();
	return 0;
}
