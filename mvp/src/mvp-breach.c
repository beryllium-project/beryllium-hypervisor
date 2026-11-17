// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: the hostile-monitor hook of the breach images (M11-7;
 *          planning/mvp-m11-plan.md, D-10's VS-domain column): at the
 *          hooked VS domain's first exit, after its activation, HS code on
 *          that hart attempts each access and call of the generated table
 *          (mvp-breach-table.h, from scenarios/anchor/breach.json) and
 *          records each one's trap in its own hart mailbox, which the
 *          harness reads at the end of the run (tests/check-boundary.py
 *          breach).
 * Trust:   test code. Every privileged effect is an executor function's
 *          (be_mvp_exec_breach_*). The hook writes only its own hart
 *          mailbox's tail beyond its rings (its record, its control rows'
 *          words, and its two roots), and the registers it saves and
 *          restores; every other effect is an attempt's.
 * Scope:   the breach images (BE_MVP_BREACH, BE_MVP_BREACH_DOMAIN).
 */
#include "mvp-breach.h"

#include "mvp-executor.h"
#include "mvp-hart.h"
#include "mvp-breach-table.h"

#define BE_MVP_BREACH_MAILBOX_HPA \
	(BE_MVP_BREACH_DOMAIN == 0 ? BE_MVP_G0_HART_MAILBOX_HPA : \
	 BE_MVP_G1_HART_MAILBOX_HPA)
/* A gigapage leaf: V, R, W, X, A, and D, and U for a G-stage leaf. */
#define BE_MVP_BREACH_LEAF		0xcfUL
#define BE_MVP_BREACH_LEAF_U		0x10UL
#define BE_MVP_BREACH_GIGAPAGE_SHIFT	30U
#define BE_MVP_BREACH_PTE_SHIFT		10U
#define BE_MVP_BREACH_PAGE_SHIFT	12U

_Static_assert(BE_MVP_BREACH_ROWS <= BE_MVP_BREACH_SLOTS,
	       "a slot for every row");

/*
 * The hook's three 64-bit values, read from its own constants through a
 * volatile lvalue so that no compiler folds them into a pooled literal: a
 * pool's mergeable section is merged with the control role's and placed
 * in its constants, which this hart may not read once confined.
 */
enum { BREACH_MAGIC, BREACH_SENTINEL, BREACH_FILL, BREACH_VALUES };
static const be_u64 breach_values[BREACH_VALUES] = {
	[BREACH_MAGIC] = BE_MVP_BREACH_MAGIC,
	[BREACH_SENTINEL] = BE_MVP_BREACH_SENTINEL,
	[BREACH_FILL] = BE_MVP_BREACH_FILL,
};

static be_u64 breach_value(unsigned int which)
{
	return ((const volatile be_u64 *)breach_values)[which];
}

static struct be_mvp_breach_record *breach_record(void)
{
	return (struct be_mvp_breach_record *)(void *)
		(BE_MVP_BREACH_MAILBOX_HPA + BE_MVP_BREACH_RECORD_OFFSET);
}

static volatile be_u64 *breach_words(be_u64 offset)
{
	return (volatile be_u64 *)(void *)(BE_MVP_BREACH_MAILBOX_HPA + offset);
}

/* One root, every entry zero but the gigapage leaves at @first, @second. */
static void build_root(be_u64 offset, be_u64 entries, be_u64 first,
		       be_u64 second, be_u64 leaf)
{
	volatile be_u64 *root = breach_words(offset);
	be_u64 index;

	for (index = 0U; index < entries; ++index)
		root[index] = 0U;
	root[first] = leaf;
	root[second] = leaf;
}

/*
 * The hook's two roots: an Sv39 root mapping BE_MVP_BREACH_GIGAPAGE at
 * itself and at BE_MVP_BREACH_ALIAS_VA, so that the hook's code, stack,
 * and record stay mapped; and a forged Sv39x4 root mapping it at
 * BE_MVP_BREACH_FORGED_GPA. Then its control rows' block and words, each
 * its fill.
 */
static void prepare(void)
{
	be_u64 pte = (BE_MVP_BREACH_GIGAPAGE >> BE_MVP_BREACH_PAGE_SHIFT) <<
		BE_MVP_BREACH_PTE_SHIFT;
	volatile be_u64 *control = breach_words(BE_MVP_BREACH_CONTROL_OFFSET);
	be_u64 fill = breach_value(BREACH_FILL), index;

	build_root(BE_MVP_BREACH_SV39_OFFSET, 512U,
		   BE_MVP_BREACH_GIGAPAGE >> BE_MVP_BREACH_GIGAPAGE_SHIFT,
		   BE_MVP_BREACH_ALIAS_VA >> BE_MVP_BREACH_GIGAPAGE_SHIFT,
		   pte | BE_MVP_BREACH_LEAF);
	build_root(BE_MVP_BREACH_SV39X4_OFFSET, 2048U,
		   BE_MVP_BREACH_FORGED_GPA >> BE_MVP_BREACH_GIGAPAGE_SHIFT,
		   BE_MVP_BREACH_FORGED_GPA >> BE_MVP_BREACH_GIGAPAGE_SHIFT,
		   pte | BE_MVP_BREACH_LEAF | BE_MVP_BREACH_LEAF_U);
	for (index = 0U; index < BE_MVP_BREACH_BLOCK_BYTES / 8U + 2U; ++index)
		control[index] = fill |
			(BE_MVP_BREACH_CONTROL_OFFSET + 8U * index);
}

/* A mode's satp, hgatp, and vsatp, each the saved value where it keeps. */
static void translate(be_u64 mode, const struct be_mvp_breach_saved *saved)
{
	const be_u64 *wanted = be_mvp_breach_modes[mode];

	be_mvp_exec_breach_translate(
		wanted[0] == BE_MVP_BREACH_KEEP ? saved->satp : wanted[0],
		wanted[1] == BE_MVP_BREACH_KEEP ? saved->hgatp : wanted[1],
		wanted[2] == BE_MVP_BREACH_KEEP ? saved->vsatp : wanted[2]);
}

void be_mvp_breach_hook(be_u64 block, be_u64 exits)
{
	struct be_mvp_breach_record *record = breach_record();
	struct be_mvp_breach_saved saved;
	be_u64 index, mode = BE_MVP_BREACH_MODE_BARE, sentinel;

	if (block != be_mvp_block_hpa(BE_MVP_BREACH_DOMAIN) || exits != 0U)
		return;
	if (record->state != BE_MVP_BREACH_STATE_CLEAR) {
		record->state = BE_MVP_BREACH_STATE_AGAIN;
		return;
	}
	record->magic = breach_value(BREACH_MAGIC);
	record->state = BE_MVP_BREACH_STATE_RUNNING;
	record->rows = 0U;
	record->domain = BE_MVP_BREACH_DOMAIN;
	record->slot = 0U;
	record->resume = 0U;
	record->abort_cause = 0U;
	record->abort_sepc = 0U;
	record->abort_stval = 0U;
	prepare();
	sentinel = breach_value(BREACH_SENTINEL);
	be_mvp_exec_breach_enter(&saved, (be_u64)(void *)&record->slot);
	for (index = 0U; index < BE_MVP_BREACH_ROWS; ++index) {
		const struct be_mvp_breach_attempt *row =
			&be_mvp_breach_attempts[index];
		struct be_mvp_breach_slot *slot = &record->slots[index];
		be_u64 wanted = (row->kind >> 8) & 0xffU;

		if (wanted >= BE_MVP_BREACH_MODES)
			break;
		if (wanted != mode) {
			translate(wanted, &saved);
			mode = wanted;
		}
		slot->cause = BE_MVP_BREACH_NO_TRAP;
		slot->stval = 0U;
		slot->value = sentinel;
		slot->error = sentinel;
		be_mvp_exec_breach_attempt(row, slot,
					   (be_u64)(void *)&record->slot);
		record->rows = index + 1U;
	}
	if (mode != BE_MVP_BREACH_MODE_BARE)
		translate(BE_MVP_BREACH_MODE_BARE, &saved);
	be_mvp_exec_breach_leave(&saved);
	record->state = BE_MVP_BREACH_STATE_DONE;
}
