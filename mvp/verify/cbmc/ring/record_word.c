/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: CBMC harness for be_mvp_record_word (planning/mvp-m8-specifications.md,
 *          section 5 as its Revision 1 states it, this row unchanged by
 *          it, accepted at 93a8d136, SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b):
 *          "Returns the little-endian 64-bit word at payload offset 8*index if
 *          8*index + 8 <= length, else 0", for every record and index. A
 *          bounded model check, never a proof.
 * Trust:   harness code (harness.h). 8*index + 8 <= length is computed in
 *          the integers as index < length / 8. A record's payload has 256
 *          bytes (section 5: at most 256 payload bytes), so for a length
 *          above 256 and an index of 32 or more the row names a word the
 *          record does not have and states no value; that case alone is not
 *          asserted.
 * Scope:   Leaf B of the M8 pilot (planning/mvp-m8-plan.md, D-8).
 */
#include "harness.h"

static be_u64 payload_word(const struct be_mvp_record *record, be_u64 index)
{
	const be_u8 *bytes = &record->payload[8U * index];

	return (be_u64)bytes[0] | (be_u64)bytes[1] << 8 |
	       (be_u64)bytes[2] << 16 | (be_u64)bytes[3] << 24 |
	       (be_u64)bytes[4] << 32 | (be_u64)bytes[5] << 40 |
	       (be_u64)bytes[6] << 48 | (be_u64)bytes[7] << 56;
}

int main(void)
{
	struct be_mvp_record record;
	be_u64 index = nondet_u64();
	be_u64 result = be_mvp_record_word(&record, index);
	int within = index < record.length / 8U;

	if (within && index < WORDS_MAX)
		PROPERTY(result == payload_word(&record, index),
			 "record_word: the little-endian word at payload offset 8*index when 8*index + 8 <= length");
	if (!within)
		PROPERTY(result == 0U, "record_word: 0 when 8*index + 8 > length");
	VACUITY_PROBE();
	return 0;
}
