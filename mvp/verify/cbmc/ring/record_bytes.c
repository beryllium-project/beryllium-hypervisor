/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_ring_record_bytes
 *          (planning/mvp-m8-specifications.md, section 5 as its Revision 1
 *          states it, this row unchanged by it, accepted at 93a8d136,
 *          SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "Returns 16 + ((length + 7) & ~7) for length <= 256, else 0", for
 *          every u64 length. A bounded model check, never a proof.
 * Trust:   harness code (harness.h).
 * Scope:   Leaf B of the M8 pilot (planning/mvp-m8-plan.md, D-8).
 */
#include "harness.h"

int main(void)
{
	be_u64 length = nondet_u64();
	be_u64 result = be_mvp_ring_record_bytes(length);

	PROPERTY(result == spec_record_bytes(length),
		 "record_bytes: 16 + ((length + 7) & ~7) for length <= 256, else 0");
	VACUITY_PROBE();
	return 0;
}
