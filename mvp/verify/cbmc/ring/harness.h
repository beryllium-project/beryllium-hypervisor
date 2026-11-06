/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the shared part of Leaf B's CBMC harnesses (planning/mvp-m8-plan.md,
 *          D-8, work package M8-6): the per-call properties of mvp-ring.c's
 *          public functions as section 5 of the specification states them
 *          in its Revision 1 (planning/mvp-m8-specifications.md, accepted
 *          at 93a8d136, SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b;
 *          the clauses it corrected, [R1-4] to [R1-9], are in init.c,
 *          post.c, post_words.c, room.c, acquire.c, taken.c, and
 *          sequence.c; the first run's harnesses, against the accepted text
 *          of 004f31ae, are those of commit 0b45698e, their records in
 *          mvp/results/20261103-verify/leaf-b/),
 *          checked by bounded model checking: a bounded model check, never a
 *          proof. Each harness builds its views with be_mvp_ring_init on a
 *          buffer of BE_CBMC_CAPACITY bytes (512 or 4096), makes the peer's
 *          index an arbitrary u64 at the call, and asserts the row's
 *          conclusions; the common safety properties are CBMC's bounds,
 *          pointer, signed-overflow, and unwinding checks on the leaf, and,
 *          in configuration A, its unsigned-overflow check.
 * Trust:   harness code, never linked into the monitor; the leaf and its
 *          headers are compiled unchanged (verify/target-digests.txt). The
 *          harness's own arithmetic is the specification's u64 arithmetic,
 *          so CBMC's unsigned-overflow check is disabled for the harness
 *          files only (the pragma below); the leaf's translation unit keeps
 *          it. Section 5 names a record's header fields but not their
 *          bytes: the harnesses read type at byte 0, domain at 1, length as
 *          a little-endian 16-bit field at 2, reserved as a 32-bit one at 4,
 *          and time as a 64-bit one at 8, the encoding mvp-ring.c's HEADER_*
 *          offsets define (a recorded assumption).
 * Scope:   the M8 pilot's Leaf B (mvp/verify/cbmc/ring/), run by
 *          mvp/verify/tools/cbmc-ring.py; nothing here is evidence about the
 *          rings as the monitor runs them (U-04, U-11) or about compiled
 *          execution.
 *
 * Build switches: BE_CBMC_CAPACITY (512 or 4096); BE_CBMC_POSITION, when
 * defined, a multiple of 8 below the capacity: the low bits of the own
 * index (its position in the buffer), the run being one class of a case
 * split over every position whose union is every own index, so that CBMC
 * sees the buffer positions as constants; BE_CBMC_PART_SCALAR and
 * BE_CBMC_PART_BUFFER, which of a buffer-writing harness's conclusions the
 * run asserts; BE_CBMC_READER_TAKE, whether a reader's earlier calls may
 * include a take (its reads at arbitrary positions of a 4,096-byte buffer
 * exceed the budget: the runner sets it at 512); BE_CBMC_VACUITY, which
 * drops every assertion and keeps one assert(0) after the assumptions,
 * which must fail.
 */
#ifndef BE_CBMC_RING_HARNESS_H
#define BE_CBMC_RING_HARNESS_H

#include "mvp-ring.h"

#pragma CPROVER check push
#pragma CPROVER check disable "unsigned-overflow"

#ifndef BE_CBMC_CAPACITY
#error "BE_CBMC_CAPACITY: the ring's capacity in bytes"
#endif
#define CAPACITY		((be_u64)BE_CBMC_CAPACITY)
#define MASK			(CAPACITY - 1U)
#define HEADER			16U
#define PAYLOAD_MAX		256U
#define WORDS_MAX		32U
#define RECORD_MAX		(HEADER + PAYLOAD_MAX)
#define LINE_PAD		(BE_MVP_RING_INDEX_BYTES - 8U)

_Static_assert((CAPACITY & MASK) == 0U && CAPACITY >= 512U &&
	       CAPACITY <= 32768U, "a capacity section 5 admits");
#ifdef BE_CBMC_POSITION
_Static_assert(((be_u64)BE_CBMC_POSITION & 7U) == 0U &&
	       (be_u64)BE_CBMC_POSITION < CAPACITY,
	       "a position class is an aligned buffer position");
#endif

be_u64 nondet_u64(void);
be_u32 nondet_u32(void);
be_u8 nondet_u8(void);
_Bool nondet_bool(void);

#ifdef BE_CBMC_VACUITY
#define PROPERTY(condition, text)	((void)0)
#define VACUITY_PROBE() \
	__CPROVER_assert(0, "vacuity: the assumptions are jointly satisfiable")
#else
#define PROPERTY(condition, text)	__CPROVER_assert((condition), text)
#define VACUITY_PROBE()			((void)0)
#endif

#if defined(BE_CBMC_PART_SCALAR) || !defined(BE_CBMC_PART_BUFFER)
#define SCALAR_PART			1
#else
#define SCALAR_PART			0
#endif
#if defined(BE_CBMC_PART_BUFFER) || !defined(BE_CBMC_PART_SCALAR)
#define BUFFER_PART			1
#else
#define BUFFER_PART			0
#endif

/* ------------------------------------------------- the specification's terms */

/* record_bytes(length) as section 5 defines it. */
static be_u64 spec_record_bytes(be_u64 length)
{
	return length <= PAYLOAD_MAX ? HEADER + ((length + 7U) & ~(be_u64)7U) :
				       0U;
}

/* A non-empty subset of the inbound, the outbound, or the input set. */
static int spec_types_valid(be_u64 types)
{
	return types != 0U && ((types & ~BE_MVP_RECORDS_INBOUND) == 0U ||
			       (types & ~BE_MVP_RECORDS_OUTBOUND) == 0U ||
			       (types & ~BE_MVP_RECORDS_INPUT) == 0U);
}

/* TYPE is in the view's type set. */
static int spec_in_set(be_u64 types, be_u64 type)
{
	return type < 64U && ((types >> type) & 1U) != 0U;
}

/* The byte at offset OFFSET of a record's 16-byte header. */
static be_u8 spec_header_byte(be_u64 offset, be_u64 type, be_u64 domain,
			      be_u64 length, be_u64 time)
{
	if (offset == 0U)
		return (be_u8)type;
	if (offset == 1U)
		return (be_u8)domain;
	if (offset < 4U)
		return (be_u8)(length >> (8U * (offset - 2U)));
	if (offset < 8U)
		return 0U;
	return (be_u8)(time >> (8U * (offset - 8U)));
}

/* A ring position: the count masked by C - 1. */
static be_u64 spec_position(be_u64 count)
{
	return count & MASK;
}

/* The own index's position in the buffer: in a position-class run the
 * class's constant (equal to the computed one by construction, so that CBMC
 * folds what is derived from it), else computed. */
#ifdef BE_CBMC_POSITION
#define OWN_POSITION(own)	((be_u64)BE_CBMC_POSITION)
#else
#define OWN_POSITION(own)	spec_position(own)
#endif

/* ------------------------------------------------------------ the state */

/* The own index's starting value: a multiple of 8, near 2^64 included; in a
 * position-class run, its low bits are the class's and the rest arbitrary. */
static be_u64 own_index(void)
{
#ifdef BE_CBMC_POSITION
	return (nondet_u64() & ~MASK) | (be_u64)BE_CBMC_POSITION;
#else
	return nondet_u64() & ~(be_u64)7U;
#endif
}

static enum be_mvp_ring_role any_side(void)
{
	return nondet_bool() ? BE_MVP_RING_WRITER : BE_MVP_RING_READER;
}

/*
 * One view of a ring of CAPACITY bytes built by be_mvp_ring_init: ROLE's
 * own index at OWN, the peer's a multiple of 8 within a capacity of it, as
 * init requires; the types and the domain arbitrary (init refuses what it
 * refuses). The two index lines' pads are arbitrary. Returns init's result.
 */
static int build(struct be_mvp_ring *view, be_u8 *buffer,
		 struct be_mvp_ring_index *head,
		 struct be_mvp_ring_index *tail, enum be_mvp_ring_role role,
		 be_u64 own)
{
	be_u64 peer = nondet_u64();

	__CPROVER_assume((own & 7U) == 0U && (peer & 7U) == 0U);
	head->value = role == BE_MVP_RING_WRITER ? own : peer;
	tail->value = role == BE_MVP_RING_WRITER ? peer : own;
	__CPROVER_assume(head->value - tail->value <= CAPACITY);
	return be_mvp_ring_init(view, buffer, CAPACITY, head, tail, nondet_u64(),
				nondet_u32(), role);
}

/*
 * On a view init accepted: the premise that it holds the buffer, the
 * capacity, and the index lines it was given, and its own index as its
 * cursor (section 5's init row states the cursor), assumed and then
 * restated as constants, so that CBMC's symbolic execution does not carry
 * init's refused paths into the call under test. A view init refused is
 * checked on its own path.
 */
static void restate(struct be_mvp_ring *view, be_u8 *buffer,
		    struct be_mvp_ring_index *head,
		    struct be_mvp_ring_index *tail, be_u64 own)
{
	__CPROVER_assume(view->buffer == buffer && view->capacity == CAPACITY &&
			 view->head == head && view->tail == tail &&
			 view->cursor == own);
	view->buffer = buffer;
	view->capacity = CAPACITY;
	view->head = head;
	view->tail = tail;
	view->cursor = own;
}

/* A writer's earlier calls: perhaps one empty record posted, perhaps then
 * published, so that its cursor may lead its published head. */
static void writer_prefix(struct be_mvp_ring *view)
{
	if (nondet_bool()) {
		(void)be_mvp_ring_post(view,
				       (enum be_mvp_record_type)nondet_u32(),
				       nondet_u64(), (const be_u8 *)0, 0U);
		if (nondet_bool())
			(void)be_mvp_ring_publish(view);
	}
}

/* A reader's earlier calls: perhaps an acquire of any head, perhaps then
 * (with BE_CBMC_READER_TAKE) a take, so that its limit and cursor may lead
 * its released tail. */
static void reader_prefix(struct be_mvp_ring *view,
			  struct be_mvp_ring_index *head)
{
	if (nondet_bool()) {
		head->value = nondet_u64();
		(void)be_mvp_ring_acquire(view);
#ifdef BE_CBMC_READER_TAKE
		if (nondet_bool()) {
			struct be_mvp_record scratch;

			(void)be_mvp_ring_take(view, &scratch);
		}
#endif
	}
}

/* A view an earlier refused call failed (its fields otherwise unchanged). */
static void fail_maybe(struct be_mvp_ring *view)
{
	if (nondet_bool())
		view->failed = 1U;
}

/* The peer's index at the call: any u64. */
static void havoc_peer(struct be_mvp_ring_index *head,
		       struct be_mvp_ring_index *tail,
		       enum be_mvp_ring_role role)
{
	if (role == BE_MVP_RING_WRITER)
		tail->value = nondet_u64();
	else
		head->value = nondet_u64();
}

/*
 * The two index lines, recorded before the call: their values and one pad
 * byte of each at an arbitrary offset (so every pad byte, for the check);
 * and one buffer byte at an arbitrary position (the calls that write no
 * buffer byte). They are macros over main's own variables, so that CBMC
 * compares a read with the same read (one array version, one index
 * symbol) and finds them equal without a case split over the buffer.
 */
#define LINES_DECLARE() \
	be_u64 lines_head, lines_tail, lines_at; \
	be_u8 lines_head_pad, lines_tail_pad
#define LINES_RECORD(head, tail) \
	do { \
		lines_head = (head).value; \
		lines_tail = (tail).value; \
		lines_at = nondet_u64(); \
		__CPROVER_assume(lines_at < LINE_PAD); \
		lines_head_pad = (head).pad[lines_at]; \
		lines_tail_pad = (tail).pad[lines_at]; \
	} while (0)
#define PADS_UNCHANGED(head, tail) \
	((head).pad[lines_at] == lines_head_pad && \
	 (tail).pad[lines_at] == lines_tail_pad)
#define LINES_UNCHANGED(head, tail) \
	((head).value == lines_head && (tail).value == lines_tail && \
	 PADS_UNCHANGED(head, tail))
#define PROBE_DECLARE() \
	be_u64 probe_at; \
	be_u8 probe_was
#define PROBE_RECORD(buffer) \
	do { \
		probe_at = nondet_u64(); \
		__CPROVER_assume(probe_at < CAPACITY); \
		probe_was = (buffer)[probe_at]; \
	} while (0)
#define PROBE_UNCHANGED(buffer)	((buffer)[probe_at] == probe_was)

/* The view's fields compared field by field (section 5's "writes
 * nothing"). */
static int view_unchanged(const struct be_mvp_ring *before,
			  const struct be_mvp_ring *view)
{
	return view->buffer == before->buffer &&
	       view->capacity == before->capacity &&
	       view->head == before->head && view->tail == before->tail &&
	       view->types == before->types && view->domain == before->domain &&
	       view->role == before->role && view->failed == before->failed &&
	       view->cursor == before->cursor && view->limit == before->limit &&
	       view->peak == before->peak;
}

/* A whole buffer's bytes, recorded before the call by constant positions
 * (the position-class runs compare every byte after it). */
static void copy_buffer(be_u8 *saved, const be_u8 *buffer)
{
	be_u64 position;

	for (position = 0U; position < CAPACITY; ++position)
		saved[position] = buffer[position];
}

#endif
