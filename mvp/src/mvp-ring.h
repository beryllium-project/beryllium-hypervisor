/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP rings (planning/mvp-m0-plan.md, "Hart region", Rings): one
 *          single-writer, single-reader byte ring per direction between hart
 *          0 and each domain hart, and, since M7, each domain hart's input
 *          ring, which hart 0 writes (planning/mvp-m7-plan.md, D-1). The
 *          buffer's capacity is a power of two;
 *          the writer owns the head and the reader the tail, each in its own
 *          64-byte line of the hart's state page; a record is a 16-byte
 *          header (type, domain, length, reserved, the writer's time) and at
 *          most 256 payload bytes, padded to 8.
 * Trust:   restricted C with explicit bounded loops: no CSR, fence, SBI
 *          call, I/O, lock, or atomic read-modify-write. The memory ordering
 *          the protocol needs is the caller's, at the places this API
 *          splits: the writer posts records, executes fence w, w, then
 *          publishes the head; the reader acquires the head, executes
 *          fence r, r, takes records, executes fence r, w, then releases
 *          the tail. A writer that finds no room fails closed and never
 *          overwrites, but a writer may first ask how much room the next
 *          record has (be_mvp_ring_room()), as hart 0 does for the input
 *          ring, whose bytes that do not fit are dropped and counted
 *          (planning/mvp-m7-plan.md, D-4); malformed input or ring contents
 *          fail a view and it stays failed.
 * Scope:   the MVP line. Each side keeps its own view (struct be_mvp_ring)
 *          in its own memory; only the buffer and the two index lines are
 *          shared.
 */

#ifndef BE_MVP_RING_H
#define BE_MVP_RING_H

#include <be/types.h>

#include "mvp.h"

#define BE_MVP_RECORD_HEADER_BYTES	16U
#define BE_MVP_RECORD_PAYLOAD_MAX	256U
#define BE_MVP_RECORD_ALIGN		8U
#define BE_MVP_RECORD_MAX_BYTES \
	(BE_MVP_RECORD_HEADER_BYTES + BE_MVP_RECORD_PAYLOAD_MAX)
/* The smallest ring holds one largest record. */
#define BE_MVP_RING_MIN_BYTES		BE_U64_C(512)
#define BE_MVP_RING_INDEX_BYTES		64U

/**
 * struct be_mvp_ring_index - one ring index, alone in its 64-byte line
 * @value: the byte count written so far (head) or taken so far (tail),
 *         free-running and a multiple of 8
 * @pad: the rest of the line, never written
 */
struct be_mvp_ring_index {
	be_u64 value;
	be_u8 pad[BE_MVP_RING_INDEX_BYTES - sizeof(be_u64)];
} __attribute__((aligned(BE_MVP_RING_INDEX_BYTES)));

/**
 * enum be_mvp_ring_role - which side a view is
 * @BE_MVP_RING_WRITER: posts records and publishes the head
 * @BE_MVP_RING_READER: acquires the head, takes records, releases the tail
 */
enum be_mvp_ring_role {
	BE_MVP_RING_WRITER = 1,
	BE_MVP_RING_READER,
};

/**
 * struct be_mvp_ring - one side's view of one ring
 * @buffer: the ring's bytes, shared
 * @capacity: bytes in @buffer, a power of two of at least
 *            %BE_MVP_RING_MIN_BYTES
 * @head: the writer's index line, shared
 * @tail: the reader's index line, shared
 * @types: the record types this ring carries, as %BE_MVP_RECORD_BIT masks
 * @domain: the domain every record's header names
 * @role: writer or reader
 * @failed: nonzero once a call was refused, the other side's calls
 *          included; sticky
 * @cursor: the writer's next record, or the reader's next record
 * @limit: the reader's acquired head
 * @peak: the writer's high-water mark: the most bytes it has seen in use
 *
 * A view never writes the other side's index.
 */
struct be_mvp_ring {
	be_u8 *buffer;
	be_u64 capacity;
	volatile struct be_mvp_ring_index *head;
	volatile struct be_mvp_ring_index *tail;
	be_u64 types;
	be_u32 domain;
	enum be_mvp_ring_role role;
	be_u32 failed;
	be_u64 cursor;
	be_u64 limit;
	be_u64 peak;
};

/**
 * struct be_mvp_record - one record, as a reader takes it
 * @type: an &enum be_mvp_record_type
 * @domain: the domain the ring belongs to
 * @length: payload bytes, at most %BE_MVP_RECORD_PAYLOAD_MAX
 * @time: the writer's time CSR when it posted the record
 * @payload: the payload; bytes past @length are zero
 */
struct be_mvp_record {
	be_u32 type;
	be_u32 domain;
	be_u64 length;
	be_u64 time;
	be_u8 payload[BE_MVP_RECORD_PAYLOAD_MAX];
};

/**
 * enum be_mvp_ring_status - what one take found
 * @BE_MVP_RING_INVALID: a refused call, or a malformed ring; the view has
 *                       failed
 * @BE_MVP_RING_EMPTY: no record before the acquired head
 * @BE_MVP_RING_RECORD: one record, taken
 */
enum be_mvp_ring_status {
	BE_MVP_RING_INVALID = 0,
	BE_MVP_RING_EMPTY,
	BE_MVP_RING_RECORD,
};

/**
 * be_mvp_ring_reset - empty a ring before either side uses it
 * @head: the writer's index line
 * @tail: the reader's index line
 *
 * Hart 0 calls it for both of a block's rings before the boot barrier.
 */
void be_mvp_ring_reset(volatile struct be_mvp_ring_index *head,
		       volatile struct be_mvp_ring_index *tail);

/**
 * be_mvp_ring_init - set up one side's view of a ring
 * @ring: the view
 * @buffer: the ring's bytes
 * @capacity: a power of two, at least %BE_MVP_RING_MIN_BYTES
 * @head: the writer's index line
 * @tail: the reader's index line
 * @types: the record types the ring carries; none outside one of
 *         %BE_MVP_RECORDS_OUTBOUND, %BE_MVP_RECORDS_INBOUND, and
 *         %BE_MVP_RECORDS_INPUT
 * @domain: 0 or 1
 * @role: writer or reader
 *
 * The view starts at the side's own index: a writer at the head, a reader
 * at the tail. Invalid arguments, or indices that are not aligned or not
 * within a capacity of each other, leave the view failed.
 *
 * Return: 1, or 0 when the view failed.
 */
int be_mvp_ring_init(struct be_mvp_ring *ring, be_u8 *buffer, be_u64 capacity,
		     volatile struct be_mvp_ring_index *head,
		     volatile struct be_mvp_ring_index *tail, be_u64 types,
		     be_u32 domain, enum be_mvp_ring_role role);

/**
 * be_mvp_ring_record_bytes - the bytes one record takes in a ring
 * @length: payload bytes, at most %BE_MVP_RECORD_PAYLOAD_MAX
 *
 * Return: 16 plus @length rounded up to 8, or 0 for a longer payload.
 */
be_u64 be_mvp_ring_record_bytes(be_u64 length);

/**
 * be_mvp_ring_post - write one record after the writer's last
 * @ring: a writer view
 * @type: a type the ring carries
 * @time: the writer's time CSR
 * @payload: @length bytes, or absent when @length is 0
 * @length: at most %BE_MVP_RECORD_PAYLOAD_MAX
 *
 * Copies the header, the payload, and zero padding into the buffer, past
 * the records already posted, reading the reader's tail to find room. The
 * record is not visible to the reader until be_mvp_ring_publish().
 *
 * Return: 1; or 0 when there is no room (the ring is never overwritten),
 *         the arguments are invalid, or the tail is malformed, any of which
 *         fails the view.
 */
int be_mvp_ring_post(struct be_mvp_ring *ring, enum be_mvp_record_type type,
		     be_u64 time, const be_u8 *payload, be_u64 length);

/**
 * be_mvp_ring_room - the payload bytes the next record can carry
 * @ring: a writer view
 *
 * Reads the reader's tail and checks it as be_mvp_ring_post() does, but
 * posts nothing: a writer that drops what does not fit (hart 0's view of
 * an input ring; planning/mvp-m7-plan.md, D-1 and D-4) asks first, so
 * that a full ring never fails its view. A record whose payload is at
 * most the answer fits.
 *
 * Return: the most payload bytes the next record may carry, at most
 *         %BE_MVP_RECORD_PAYLOAD_MAX and 0 when no record with a payload
 *         fits; or 0 for a failed view, a reader's, or a malformed tail,
 *         each of which fails the view.
 */
be_u64 be_mvp_ring_room(struct be_mvp_ring *ring);

/**
 * be_mvp_ring_post_words - post one record whose payload is words
 * @ring: a writer view
 * @type: a type the ring carries
 * @time: the writer's time CSR
 * @words: @count little-endian 64-bit words, or absent when @count is 0
 * @count: at most 32
 *
 * Return: as be_mvp_ring_post().
 */
int be_mvp_ring_post_words(struct be_mvp_ring *ring,
			   enum be_mvp_record_type type, be_u64 time,
			   const be_u64 *words, be_u64 count);

/**
 * be_mvp_ring_publish - make every posted record visible
 * @ring: a writer view
 *
 * The caller executes fence w, w first, so the records' bytes are visible
 * before the head that admits them.
 *
 * Return: 1, or 0 for a failed view or a reader's, which fails it.
 */
int be_mvp_ring_publish(struct be_mvp_ring *ring);

/**
 * be_mvp_ring_acquire - read the writer's head
 * @ring: a reader view
 *
 * The caller executes fence r, r next, before any be_mvp_ring_take(), so
 * the records' bytes are read after the head that admits them.
 *
 * Return: the bytes available to take; 0 when there are none, or for a
 *         failed view, a writer's, or a malformed head (not aligned, behind
 *         the reader, or more than a capacity ahead), which fail the view.
 */
be_u64 be_mvp_ring_acquire(struct be_mvp_ring *ring);

/**
 * be_mvp_ring_take - copy out the next record before the acquired head
 * @ring: a reader view
 * @record: zeroed first; filled for %BE_MVP_RING_RECORD
 *
 * Validates the header: a type the ring carries, the ring's domain, a
 * payload of at most 256 bytes, a reserved word of 0, zero padding, and a
 * record that ends at or before the acquired head. The record's bytes stay
 * the reader's until be_mvp_ring_release().
 *
 * Return: %BE_MVP_RING_RECORD, %BE_MVP_RING_EMPTY, or %BE_MVP_RING_INVALID
 *         (the view has failed).
 */
enum be_mvp_ring_status be_mvp_ring_take(struct be_mvp_ring *ring,
					 struct be_mvp_record *record);

/**
 * be_mvp_ring_release - give every taken record's bytes back to the writer
 * @ring: a reader view
 *
 * The caller executes fence r, w first, so the records' bytes are read
 * before the tail that frees them.
 *
 * Return: 1, or 0 for a failed view or a writer's, which fails it.
 */
int be_mvp_ring_release(struct be_mvp_ring *ring);

/**
 * be_mvp_ring_peak - the writer's high-water mark
 * @ring: a writer view
 *
 * Return: the most bytes in use the writer has seen after a post.
 */
be_u64 be_mvp_ring_peak(const struct be_mvp_ring *ring);

/**
 * be_mvp_ring_taken - the reader's tail, as a writer view reads it
 * @ring: a writer view
 *
 * The bytes the reader has taken and released so far, read from its index
 * line as it stands: no validation, no fence, and no change to the view.
 * A failed domain hart waits on it for hart 0's progress (Plan revision
 * M1-B).
 *
 * Return: the tail; or 0 for an absent view, a failed one, or a reader's,
 *         which then never reads as progress.
 */
be_u64 be_mvp_ring_taken(const struct be_mvp_ring *ring);

/**
 * be_mvp_ring_published - the head a writer view has published
 * @ring: a writer view
 *
 * The bytes the writer has made visible so far, read from its own index
 * line, with no change to the view; posted records count only once
 * be_mvp_ring_publish() has made them visible.
 *
 * Return: the head; or 0 for an absent view, a failed one, or a reader's.
 */
be_u64 be_mvp_ring_published(const struct be_mvp_ring *ring);

/**
 * be_mvp_record_word - one 64-bit word of a record's payload
 * @record: a taken record
 * @index: the word's index
 *
 * Return: the little-endian word, or 0 when it lies past the payload.
 */
be_u64 be_mvp_record_word(const struct be_mvp_record *record, be_u64 index);

#endif
