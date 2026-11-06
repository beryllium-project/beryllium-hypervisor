// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP rings: views, posting and publishing, acquiring, taking, and
 *          releasing records, header validation, the writer's high-water
 *          mark, the writer's reads of the reader's tail and of its own
 *          published head (Plan revision M1-B), and the room the writer's
 *          next record has (planning/mvp-m7-plan.md, D-4).
 * Trust:   restricted C with explicit bounded loops; no CSR, fence, SBI
 *          call, I/O, lock, or atomic read-modify-write. Every shared byte
 *          is reached through bounded little-endian helpers, and each view
 *          writes only its own index. Invalid input fails closed and stays
 *          failed.
 * Scope:   the MVP line (planning/mvp-m0-plan.md); see mvp-ring.h.
 */
#include "mvp-ring.h"

#define ALIGN_MASK		((be_u64)BE_MVP_RECORD_ALIGN - 1U)
#define WORD_BYTES		8U
#define MAX_WORDS		(BE_MVP_RECORD_PAYLOAD_MAX / WORD_BYTES)
#define RING_MAX_BYTES		BE_MVP_OUTBOUND_RING_BYTES
#define HEADER_TYPE		0U
#define HEADER_DOMAIN		1U
#define HEADER_LENGTH		2U
#define HEADER_RESERVED		4U
#define HEADER_TIME		8U

_Static_assert(sizeof(struct be_mvp_ring_index) == BE_MVP_RING_INDEX_BYTES,
	       "a ring index fills one 64-byte line");
_Static_assert(_Alignof(struct be_mvp_ring_index) == BE_MVP_RING_INDEX_BYTES,
	       "a ring index starts its 64-byte line");
_Static_assert(BE_MVP_RECORD_MAX_BYTES <= BE_MVP_RING_MIN_BYTES,
	       "the smallest ring holds the largest record");
_Static_assert(BE_MVP_INBOUND_RING_BYTES >= BE_MVP_RING_MIN_BYTES &&
	       BE_MVP_OUTBOUND_RING_BYTES <= RING_MAX_BYTES &&
	       BE_MVP_VARIANT_OUTBOUND_RING_BYTES >= BE_MVP_RING_MIN_BYTES &&
	       BE_MVP_INPUT_RING_BYTES >= BE_MVP_RING_MIN_BYTES &&
	       BE_MVP_INPUT_RING_BYTES <= RING_MAX_BYTES,
	       "every layout ring is a capacity the ring accepts");
_Static_assert((BE_MVP_RECORDS_OUTBOUND & BE_MVP_RECORDS_INBOUND) == 0 &&
	       (BE_MVP_RECORDS_OUTBOUND & BE_MVP_RECORDS_INPUT) == 0 &&
	       (BE_MVP_RECORDS_INBOUND & BE_MVP_RECORDS_INPUT) == 0,
	       "no record type crosses two rings");
_Static_assert(BE_MVP_RECORD_COUNT <= 64U, "record types fit one mask");
_Static_assert(BE_MVP_RECORD_PAYLOAD_MAX % WORD_BYTES == 0U &&
	       BE_MVP_RECORD_HEADER_BYTES % BE_MVP_RECORD_ALIGN == 0U,
	       "records stay 8-byte aligned");

static void store_le(be_u8 *buffer, be_u64 mask, be_u64 position,
		     be_u64 value, unsigned int bytes)
{
	unsigned int byte;

	for (byte = 0U; byte < bytes; ++byte)
		buffer[(position + byte) & mask] =
			(be_u8)((value >> (8U * byte)) & 0xffU);
}

static be_u64 load_le(const be_u8 *buffer, be_u64 mask, be_u64 position,
		      unsigned int bytes)
{
	be_u64 value = 0U;
	unsigned int byte;

	for (byte = 0U; byte < bytes; ++byte)
		value |= (be_u64)buffer[(position + byte) & mask] <<
			 (8U * byte);
	return value;
}

static int refuse(struct be_mvp_ring *ring)
{
	ring->failed = 1U;
	return 0;
}

/* A call on a failed view, or on the other side's, fails the view. */
static int usable(struct be_mvp_ring *ring, enum be_mvp_ring_role role)
{
	if (ring == (struct be_mvp_ring *)0)
		return 0;
	if (ring->failed == 0U && ring->role == role)
		return 1;
	ring->failed = 1U;
	return 0;
}

/* One ring's types: a subset of exactly one of the three rings' sets. */
static int types_valid(be_u64 types)
{
	return types != 0U && ((types & ~BE_MVP_RECORDS_OUTBOUND) == 0U ||
			       (types & ~BE_MVP_RECORDS_INBOUND) == 0U ||
			       (types & ~BE_MVP_RECORDS_INPUT) == 0U);
}

void be_mvp_ring_reset(volatile struct be_mvp_ring_index *head,
		       volatile struct be_mvp_ring_index *tail)
{
	if (head != (volatile struct be_mvp_ring_index *)0)
		head->value = 0U;
	if (tail != (volatile struct be_mvp_ring_index *)0)
		tail->value = 0U;
}

int be_mvp_ring_init(struct be_mvp_ring *ring, be_u8 *buffer, be_u64 capacity,
		     volatile struct be_mvp_ring_index *head,
		     volatile struct be_mvp_ring_index *tail, be_u64 types,
		     be_u32 domain, enum be_mvp_ring_role role)
{
	be_u64 head_value;
	be_u64 tail_value;

	if (ring == (struct be_mvp_ring *)0)
		return 0;
	*ring = (struct be_mvp_ring){ .failed = 1U };
	if (buffer == (be_u8 *)0 ||
	    head == (volatile struct be_mvp_ring_index *)0 ||
	    tail == (volatile struct be_mvp_ring_index *)0 ||
	    capacity < BE_MVP_RING_MIN_BYTES || capacity > RING_MAX_BYTES ||
	    (capacity & (capacity - 1U)) != 0U || !types_valid(types) ||
	    domain >= BE_MVP_DOMAINS ||
	    (role != BE_MVP_RING_WRITER && role != BE_MVP_RING_READER))
		return 0;
	head_value = head->value;
	tail_value = tail->value;
	if ((head_value & ALIGN_MASK) != 0U ||
	    (tail_value & ALIGN_MASK) != 0U ||
	    head_value - tail_value > capacity)
		return 0;
	ring->buffer = buffer;
	ring->capacity = capacity;
	ring->head = head;
	ring->tail = tail;
	ring->types = types;
	ring->domain = domain;
	ring->role = role;
	ring->cursor = role == BE_MVP_RING_WRITER ? head_value : tail_value;
	ring->limit = ring->cursor;
	ring->peak = head_value - tail_value;
	ring->failed = 0U;
	return 1;
}

be_u64 be_mvp_ring_record_bytes(be_u64 length)
{
	if (length > BE_MVP_RECORD_PAYLOAD_MAX)
		return 0U;
	return BE_MVP_RECORD_HEADER_BYTES +
	       ((length + ALIGN_MASK) & ~ALIGN_MASK);
}

int be_mvp_ring_post(struct be_mvp_ring *ring, enum be_mvp_record_type type,
		     be_u64 time, const be_u8 *payload, be_u64 length)
{
	be_u64 mask;
	be_u64 tail;
	be_u64 used;
	be_u64 size;
	be_u64 index;

	if (!usable(ring, BE_MVP_RING_WRITER))
		return 0;
	if ((unsigned int)type >= (unsigned int)BE_MVP_RECORD_COUNT ||
	    (ring->types & BE_MVP_RECORD_BIT(type)) == 0U ||
	    length > BE_MVP_RECORD_PAYLOAD_MAX ||
	    (payload == (const be_u8 *)0 && length != 0U))
		return refuse(ring);
	/* The tail is the reader's: aligned, and at or behind the head the
	 * writer published, by at most a capacity. */
	tail = ring->tail->value;
	if ((tail & ALIGN_MASK) != 0U || ring->limit - tail > ring->capacity)
		return refuse(ring);
	used = ring->cursor - tail;
	size = be_mvp_ring_record_bytes(length);
	if (used > ring->capacity || size > ring->capacity - used)
		return refuse(ring);
	mask = ring->capacity - 1U;
	store_le(ring->buffer, mask, ring->cursor + HEADER_TYPE,
		 (be_u64)type, 1U);
	store_le(ring->buffer, mask, ring->cursor + HEADER_DOMAIN,
		 ring->domain, 1U);
	store_le(ring->buffer, mask, ring->cursor + HEADER_LENGTH, length, 2U);
	store_le(ring->buffer, mask, ring->cursor + HEADER_RESERVED, 0U, 4U);
	store_le(ring->buffer, mask, ring->cursor + HEADER_TIME, time, 8U);
	for (index = 0U; index < size - BE_MVP_RECORD_HEADER_BYTES; ++index) {
		be_u64 position = ring->cursor + BE_MVP_RECORD_HEADER_BYTES +
				  index;
		be_u8 byte = 0U;

		if (index < length)
			byte = payload[index];
		ring->buffer[position & mask] = byte;
	}
	ring->cursor += size;
	if (used + size > ring->peak)
		ring->peak = used + size;
	return 1;
}

be_u64 be_mvp_ring_room(struct be_mvp_ring *ring)
{
	be_u64 tail;
	be_u64 free;

	if (!usable(ring, BE_MVP_RING_WRITER))
		return 0U;
	/* The tail, as be_mvp_ring_post() reads it. */
	tail = ring->tail->value;
	if ((tail & ALIGN_MASK) != 0U || ring->limit - tail > ring->capacity ||
	    ring->cursor - tail > ring->capacity) {
		(void)refuse(ring);
		return 0U;
	}
	free = ring->capacity - (ring->cursor - tail);
	if (free <= BE_MVP_RECORD_HEADER_BYTES)
		return 0U;
	free -= BE_MVP_RECORD_HEADER_BYTES;
	return free < BE_MVP_RECORD_PAYLOAD_MAX ? free & ~ALIGN_MASK :
						  BE_MVP_RECORD_PAYLOAD_MAX;
}

int be_mvp_ring_post_words(struct be_mvp_ring *ring,
			   enum be_mvp_record_type type, be_u64 time,
			   const be_u64 *words, be_u64 count)
{
	be_u8 bytes[BE_MVP_RECORD_PAYLOAD_MAX];
	be_u64 index;

	if (!usable(ring, BE_MVP_RING_WRITER))
		return 0;
	if (count > MAX_WORDS || (words == (const be_u64 *)0 && count != 0U))
		return refuse(ring);
	for (index = 0U; index < count; ++index)
		store_le(bytes, ~BE_U64_C(0), index * WORD_BYTES, words[index],
			 WORD_BYTES);
	return be_mvp_ring_post(ring, type, time, bytes, count * WORD_BYTES);
}

int be_mvp_ring_publish(struct be_mvp_ring *ring)
{
	if (!usable(ring, BE_MVP_RING_WRITER))
		return 0;
	ring->head->value = ring->cursor;
	ring->limit = ring->cursor;
	return 1;
}

be_u64 be_mvp_ring_acquire(struct be_mvp_ring *ring)
{
	be_u64 head;
	be_u64 released;

	if (!usable(ring, BE_MVP_RING_READER))
		return 0U;
	/* The head is the writer's: aligned, at or past what this reader has
	 * taken, and at most a capacity past the tail it released. */
	head = ring->head->value;
	released = ring->tail->value;
	if ((head & ALIGN_MASK) != 0U || head - released > ring->capacity ||
	    ring->cursor - released > head - released) {
		(void)refuse(ring);
		return 0U;
	}
	ring->limit = head;
	return head - ring->cursor;
}

enum be_mvp_ring_status be_mvp_ring_take(struct be_mvp_ring *ring,
					 struct be_mvp_record *record)
{
	be_u64 mask;
	be_u64 available;
	be_u64 type;
	be_u64 size;
	be_u64 index;

	if (record == (struct be_mvp_record *)0) {
		if (ring != (struct be_mvp_ring *)0)
			(void)refuse(ring);
		return BE_MVP_RING_INVALID;
	}
	*record = (struct be_mvp_record){ 0U, 0U, 0U, 0U, { 0U } };
	if (!usable(ring, BE_MVP_RING_READER))
		return BE_MVP_RING_INVALID;
	if (ring->cursor == ring->limit)
		return BE_MVP_RING_EMPTY;
	available = ring->limit - ring->cursor;
	mask = ring->capacity - 1U;
	if (available < BE_MVP_RECORD_HEADER_BYTES) {
		(void)refuse(ring);
		return BE_MVP_RING_INVALID;
	}
	type = load_le(ring->buffer, mask, ring->cursor + HEADER_TYPE, 1U);
	record->length = load_le(ring->buffer, mask,
				 ring->cursor + HEADER_LENGTH, 2U);
	size = be_mvp_ring_record_bytes(record->length);
	if (type >= BE_MVP_RECORD_COUNT ||
	    (ring->types & BE_MVP_RECORD_BIT(type)) == 0U ||
	    load_le(ring->buffer, mask, ring->cursor + HEADER_DOMAIN, 1U) !=
		    ring->domain ||
	    load_le(ring->buffer, mask, ring->cursor + HEADER_RESERVED, 4U) !=
		    0U ||
	    size == 0U || size > available) {
		*record = (struct be_mvp_record){ 0U, 0U, 0U, 0U, { 0U } };
		(void)refuse(ring);
		return BE_MVP_RING_INVALID;
	}
	for (index = 0U; index < size - BE_MVP_RECORD_HEADER_BYTES; ++index) {
		be_u8 byte = ring->buffer[(ring->cursor +
					   BE_MVP_RECORD_HEADER_BYTES + index) &
					  mask];

		if (index < record->length) {
			record->payload[index] = byte;
		} else if (byte != 0U) {
			*record = (struct be_mvp_record){ 0U, 0U, 0U, 0U,
							  { 0U } };
			(void)refuse(ring);
			return BE_MVP_RING_INVALID;
		}
	}
	record->type = (be_u32)type;
	record->domain = ring->domain;
	record->time = load_le(ring->buffer, mask, ring->cursor + HEADER_TIME,
			       8U);
	ring->cursor += size;
	return BE_MVP_RING_RECORD;
}

int be_mvp_ring_release(struct be_mvp_ring *ring)
{
	if (!usable(ring, BE_MVP_RING_READER))
		return 0;
	ring->tail->value = ring->cursor;
	return 1;
}

be_u64 be_mvp_ring_peak(const struct be_mvp_ring *ring)
{
	if (ring == (const struct be_mvp_ring *)0)
		return 0U;
	return ring->peak;
}

/* A writer view that has not failed: the one the reads below answer. */
static int writer_view(const struct be_mvp_ring *ring)
{
	return ring != (const struct be_mvp_ring *)0 && ring->failed == 0U &&
	       ring->role == BE_MVP_RING_WRITER;
}

be_u64 be_mvp_ring_taken(const struct be_mvp_ring *ring)
{
	if (!writer_view(ring))
		return 0U;
	return ring->tail->value;
}

be_u64 be_mvp_ring_published(const struct be_mvp_ring *ring)
{
	if (!writer_view(ring))
		return 0U;
	return ring->head->value;
}

be_u64 be_mvp_record_word(const struct be_mvp_record *record, be_u64 index)
{
	if (record == (const struct be_mvp_record *)0 || index >= MAX_WORDS ||
	    (index + 1U) * WORD_BYTES > record->length)
		return 0U;
	return load_le(record->payload, ~BE_U64_C(0), index * WORD_BYTES,
		       WORD_BYTES);
}
