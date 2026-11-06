/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_ring_publish (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, this row unchanged by
 *          it, accepted at 93a8d136, SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "For a writer view not failed: sets the head to cursor and
 *          returns 1; else 0 and the view is failed; writes no buffer byte."
 *          A bounded model check, never a proof.
 * Trust:   harness code (harness.h). The view: either side's, built by
 *          be_mvp_ring_init (or refused by it), a writer's perhaps after an
 *          empty record posted (so its cursor may lead the head), perhaps
 *          failed since, the peer's index any u64.
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
	PROBE_DECLARE();
	enum be_mvp_ring_role role = any_side();
	int result;

	(void)build(&view, buffer, &head, &tail, role, own_index());
	if (role == BE_MVP_RING_WRITER)
		writer_prefix(&view);
	else
		reader_prefix(&view, &head);
	fail_maybe(&view);
	havoc_peer(&head, &tail, role);
	before = view;
	PROBE_RECORD(buffer);

	result = be_mvp_ring_publish(&view);

	if (before.role == BE_MVP_RING_WRITER && before.failed == 0U)
		PROPERTY(result == 1 && head.value == before.cursor,
			 "publish: a writer view not failed: the head set to cursor, 1");
	else
		PROPERTY(result == 0 && view.failed != 0U,
			 "publish: otherwise 0 and the view failed");
	PROPERTY(PROBE_UNCHANGED(buffer),
		 "publish: writes no buffer byte");
	VACUITY_PROBE();
	return 0;
}
