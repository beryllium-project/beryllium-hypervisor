/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_ring_reset (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, this row unchanged by
 *          it, accepted at 93a8d136, SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "Both index values become 0; nothing else is written." A bounded
 *          model check, never a proof.
 * Trust:   harness code (harness.h); the two index lines are distinct, each
 *          its own 64-byte line (section 5), with arbitrary values and pads.
 * Scope:   Leaf B of the M8 pilot (planning/mvp-m8-plan.md, D-8).
 */
#include "harness.h"

int main(void)
{
	struct be_mvp_ring_index head;
	struct be_mvp_ring_index tail;
	LINES_DECLARE();

	LINES_RECORD(head, tail);
	be_mvp_ring_reset(&head, &tail);

	PROPERTY(head.value == 0U && tail.value == 0U,
		 "reset: both index values become 0");
	PROPERTY(PADS_UNCHANGED(head, tail),
		 "reset: nothing else is written");
	VACUITY_PROBE();
	return 0;
}
