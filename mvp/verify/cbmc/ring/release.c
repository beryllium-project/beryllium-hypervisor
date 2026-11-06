/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_ring_release (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, this row unchanged by
 *          it, accepted at 93a8d136, SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "For a reader view not failed: sets the tail to cursor and returns
 *          1; else 0 and the view is failed." A bounded model check, never a
 *          proof.
 * Trust:   harness code (harness.h). The view: either side's, built by
 *          be_mvp_ring_init (or refused by it), a reader's perhaps after an
 *          acquire and, with BE_CBMC_READER_TAKE (the runner's, at 512), a
 *          take (so its cursor may lead its tail), perhaps failed since, the
 *          peer's index any u64.
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

	result = be_mvp_ring_release(&view);

	if (before.role == BE_MVP_RING_READER && before.failed == 0U)
		PROPERTY(result == 1 && tail.value == before.cursor,
			 "release: a reader view not failed: the tail set to cursor, 1");
	else
		PROPERTY(result == 0 && view.failed != 0U,
			 "release: otherwise 0 and the view failed");
	VACUITY_PROBE();
	return 0;
}
