/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_ring_peak (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, this row unchanged by
 *          it, accepted at 93a8d136, SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "Returns the writer view's peak; writes nothing." A bounded model
 *          check, never a proof.
 * Trust:   harness code (harness.h). The view: a writer's, built by
 *          be_mvp_ring_init (or refused by it), after perhaps an empty record
 *          posted and published, perhaps failed since, the reader's tail any
 *          u64 at the call.
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
	be_u64 result;

	(void)build(&view, buffer, &head, &tail, BE_MVP_RING_WRITER,
		    own_index());
	writer_prefix(&view);
	fail_maybe(&view);
	havoc_peer(&head, &tail, BE_MVP_RING_WRITER);
	before = view;
	LINES_RECORD(head, tail);
	PROBE_RECORD(buffer);

	result = be_mvp_ring_peak(&view);

	PROPERTY(result == before.peak, "peak: returns the writer view's peak");
	PROPERTY(view_unchanged(&before, &view) &&
		 LINES_UNCHANGED(head, tail) &&
		 PROBE_UNCHANGED(buffer), "peak: writes nothing");
	VACUITY_PROBE();
	return 0;
}
