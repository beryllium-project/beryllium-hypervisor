/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP console input (planning/mvp-m7-plan.md, D-1, D-3, and D-4;
 *          Q1, Q2): the focus parser, a pure function over bytes with
 *          three states whose table is the specification; hart 0's routing
 *          of the bytes it reads from the firmware console to the focused
 *          domain's input ring, with the focus, the drops by reason, and
 *          the per-run accounting (bytes read, and per domain the bytes
 *          delivered and their SHA-256); the next deadline of hart 0's
 *          poll; and a domain hart's service of its guest's DBCN read from
 *          its input ring through a staging buffer of its own.
 * Trust:   restricted C with explicit bounded loops: no CSR, fence, SBI
 *          call, I/O, or mutable global. Every function reads only its
 *          arguments and writes only what they name; the runtimes read the
 *          firmware console, publish the rings, copy into a guest window,
 *          and print the lines. Routing never depends on arrival timing,
 *          and a byte reaches only the focused domain holding the grant.
 * Scope:   the MVP line from M7. Console input is monitor mechanism
 *          outside the policy (D-5): which domains may receive it is a
 *          configuration fact hart 0 reads from the sealed configuration.
 */

#ifndef BE_MVP_INPUT_H
#define BE_MVP_INPUT_H

#include <be/types.h>

#include "mvp.h"
#include "mvp-ring.h"
#include "mvp-sha256.h"

/* The focus prefix byte (Q1): `~0` and `~1` select a domain, `~~` is `~`. */
#define BE_MVP_INPUT_PREFIX		0x7eU
/* Hart 0's firmware read buffer, and the most bytes one poll reads (Q2). */
#define BE_MVP_INPUT_READ_BYTES		64U
#define BE_MVP_INPUT_POLL_MAX		256U
/* A domain hart's staging buffer: one INPUT record's largest payload. */
#define BE_MVP_INPUT_STAGE_BYTES	BE_MVP_RECORD_PAYLOAD_MAX
/* The focus before the first selection: no domain's index. */
#define BE_MVP_INPUT_NO_FOCUS		((be_u32)BE_MVP_DOMAINS)
/* be_mvp_input_flush()'s and be_mvp_input_serve()'s answer on failure. */
#define BE_MVP_INPUT_FAILED		(~BE_U64_C(0))

/**
 * enum be_mvp_focus_state - the focus parser's state
 * @BE_MVP_FOCUS_LINE_START: at the start of a typed line, where the prefix
 *                           byte begins a focus sequence
 * @BE_MVP_FOCUS_AFTER_PREFIX: after a prefix byte at the start of a line
 * @BE_MVP_FOCUS_IN_LINE: inside a typed line, where every byte is input
 * @BE_MVP_FOCUS_STATES: number of states, not a state
 */
enum be_mvp_focus_state {
	BE_MVP_FOCUS_LINE_START = 0,
	BE_MVP_FOCUS_AFTER_PREFIX,
	BE_MVP_FOCUS_IN_LINE,
	BE_MVP_FOCUS_STATES,
};

/**
 * enum be_mvp_input_drop - why hart 0 dropped a byte (D-3, D-4)
 * @BE_MVP_DROP_NO_FOCUS: input before any domain was selected
 * @BE_MVP_DROP_NO_GRANT: a focus sequence naming a domain without the
 *                        console-input grant; the focus is unchanged
 * @BE_MVP_DROP_NOT_RUNNING: input for a domain that is paused, terminated,
 *                           shut down, or about to stop
 * @BE_MVP_DROP_RING_FULL: input that did not fit the domain's input ring
 * @BE_MVP_DROP_BAD_SEQUENCE: a byte after the prefix that is neither a
 *                            domain's digit nor the prefix
 * @BE_MVP_DROP_BEFORE_ARMED: a byte the firmware held before hart 0 armed
 *                            console input, which its first poll discards
 * @BE_MVP_DROP_REASONS: number of reasons, not a reason
 */
enum be_mvp_input_drop {
	BE_MVP_DROP_NO_FOCUS = 0,
	BE_MVP_DROP_NO_GRANT,
	BE_MVP_DROP_NOT_RUNNING,
	BE_MVP_DROP_RING_FULL,
	BE_MVP_DROP_BAD_SEQUENCE,
	BE_MVP_DROP_BEFORE_ARMED,
	BE_MVP_DROP_REASONS,
};

/**
 * enum be_mvp_focus_kind - what one byte means to the focus parser
 * @BE_MVP_FOCUS_DELIVER: deliver the output's byte to the focus
 * @BE_MVP_FOCUS_SELECT: select the output's domain as the focus
 * @BE_MVP_FOCUS_DROP: drop the byte, %BE_MVP_DROP_BAD_SEQUENCE
 * @BE_MVP_FOCUS_HOLD: the prefix byte at the start of a line, held: the
 *                     next byte decides what the pair means, so the
 *                     prefix itself is neither delivered nor dropped
 */
enum be_mvp_focus_kind {
	BE_MVP_FOCUS_DELIVER = 0,
	BE_MVP_FOCUS_SELECT,
	BE_MVP_FOCUS_DROP,
	BE_MVP_FOCUS_HOLD,
};

/**
 * struct be_mvp_focus_out - the parser's output for one byte
 * @kind: what the byte means
 * @domain: for %BE_MVP_FOCUS_SELECT, the domain its digit names
 * @reason: for %BE_MVP_FOCUS_DROP, %BE_MVP_DROP_BAD_SEQUENCE
 * @byte: for %BE_MVP_FOCUS_DELIVER, the byte to deliver: the input byte,
 *        or the prefix for a doubled prefix
 */
struct be_mvp_focus_out {
	enum be_mvp_focus_kind kind;
	be_u32 domain;
	enum be_mvp_input_drop reason;
	be_u8 byte;
};

/**
 * be_mvp_focus_step - one byte through the focus parser
 * @state: the parser's state
 * @byte: the byte
 * @out: zeroed first; the byte's meaning
 *
 * The table is the specification (D-3): at the start of a line, the prefix
 * is held and starts a sequence; there, `0` or `1` selects that domain and
 * a line starts again, a second prefix delivers one literal prefix and the
 * line goes on, and any other byte, CR and LF among them, is dropped as a
 * bad sequence and a line starts again; at the start of a line or inside
 * one, any other byte is delivered, and CR or LF is delivered and starts a
 * line. There is no timeout. A state that is not one of the three is
 * refused as a bad sequence, and a line starts again.
 *
 * Return: the parser's next state.
 */
enum be_mvp_focus_state be_mvp_focus_step(enum be_mvp_focus_state state,
					  be_u8 byte,
					  struct be_mvp_focus_out *out);

/**
 * be_mvp_input_drop_name - a drop reason's name, as BE_MVP:17 and :18
 *                          print it
 * @reason: the reason
 *
 * Return: "no-focus", "no-grant", "not-running", "ring-full",
 *         "bad-sequence", or "before-armed"; or "invalid".
 */
const char *be_mvp_input_drop_name(enum be_mvp_input_drop reason);

/**
 * struct be_mvp_input - hart 0's console input: the routing and the run's
 *                       accounting
 * @armed: 1 once be_mvp_input_arm() armed it, else 0
 * @discard: 1 until the end of the first poll after arming, whose bytes
 *           the firmware held before arming: each is dropped
 *           %BE_MVP_DROP_BEFORE_ARMED
 * @grants: the sealed configuration's console-input grants, bit d for
 *          domain d; only these may be the focus
 * @state: the focus parser's state
 * @focus: the focused domain, or %BE_MVP_INPUT_NO_FOCUS
 * @read: bytes read from the firmware console since arming; saturates
 * @delivered: per domain, bytes posted to its input ring; saturates
 * @dropped: per reason, bytes dropped; saturates
 * @announced: bit r once the first drop of reason r was reported
 * @digest: per domain, the running SHA-256 of the bytes delivered to it
 * @pending: per domain, bytes of the current poll waiting for its flush
 * @batch: per domain, those bytes, in order
 *
 * Hart 0 alone holds and writes it; no code a domain hart runs names it.
 */
struct be_mvp_input {
	be_u32 armed;
	be_u32 discard;
	be_u64 grants;
	enum be_mvp_focus_state state;
	be_u32 focus;
	be_u64 read;
	be_u64 delivered[BE_MVP_DOMAINS];
	be_u64 dropped[BE_MVP_DROP_REASONS];
	be_u64 announced;
	struct be_mvp_sha256 digest[BE_MVP_DOMAINS];
	be_u64 pending[BE_MVP_DOMAINS];
	be_u8 batch[BE_MVP_DOMAINS][BE_MVP_INPUT_POLL_MAX];
};

/**
 * enum be_mvp_input_report - what hart 0 prints after one byte or flush
 * @BE_MVP_INPUT_QUIET: nothing
 * @BE_MVP_INPUT_FOCUSED: BE_MVP:16 FOCUS for the event's domain
 * @BE_MVP_INPUT_FIRST_DROP: BE_MVP:17 INPUT_DROP for the event's reason,
 *                           the first drop of that reason in the run
 */
enum be_mvp_input_report {
	BE_MVP_INPUT_QUIET = 0,
	BE_MVP_INPUT_FOCUSED,
	BE_MVP_INPUT_FIRST_DROP,
};

/**
 * struct be_mvp_input_event - one report hart 0 owes the console
 * @report: what to print
 * @domain: for %BE_MVP_INPUT_FOCUSED, the domain now focused
 * @reason: for %BE_MVP_INPUT_FIRST_DROP, the reason
 */
struct be_mvp_input_event {
	enum be_mvp_input_report report;
	be_u32 domain;
	enum be_mvp_input_drop reason;
};

/**
 * be_mvp_input_arm - arm console input after the boot barrier
 * @input: hart 0's console input, zeroed first
 * @grants: the sealed configuration's grants, bit d for domain d
 *
 * Arms only when at least one domain holds the grant and no bit names a
 * domain that does not exist: the focus none, the parser at the start of
 * a line, the digests started, and the first poll's bytes discarded.
 *
 * Return: 1 when armed; 0, with @input zeroed and not armed, otherwise.
 */
int be_mvp_input_arm(struct be_mvp_input *input, be_u64 grants);

/**
 * be_mvp_input_poll_begin - start one poll: no byte batched for any domain
 * @input: hart 0's console input
 */
void be_mvp_input_poll_begin(struct be_mvp_input *input);

/**
 * be_mvp_input_byte - route one byte hart 0 read
 * @input: hart 0's console input, armed
 * @byte: the byte
 * @running: bit d when hart 0 holds domain d running (be_mvp_control_
 *           running()): not paused, terminated, shut down, failed, or
 *           about to stop
 * @event: zeroed first; the report hart 0 owes, if any
 *
 * Counts the byte as read. During the first poll after arming it is
 * dropped as before-armed and the parser is not stepped. Otherwise the
 * parser decides: a selection of a domain holding the grant becomes the
 * focus and is reported, whether or not it changes the focus; one of a
 * domain without the grant is dropped as no-grant, the focus unchanged; a
 * delivery is batched for the focus, unless there is none (no-focus), or
 * the focus is not running (not-running); a bad sequence is dropped; a
 * held prefix is only counted as read. Each reason's first drop is
 * reported. A byte is never batched for any domain but the focus holding
 * the grant (S3-C's stop (g)), and at most %BE_MVP_INPUT_POLL_MAX per
 * domain per poll, past which a byte is dropped as ring-full.
 */
void be_mvp_input_byte(struct be_mvp_input *input, be_u8 byte,
		       be_u64 running, struct be_mvp_input_event *event);

/**
 * be_mvp_input_flush - post one domain's batch of the current poll
 * @input: hart 0's console input
 * @domain: the domain
 * @ring: hart 0's writer view of the domain's input ring
 * @now: the time CSR, the record's time
 * @event: zeroed first; the report hart 0 owes, if any
 *
 * Asks the ring for room (be_mvp_ring_room()) and posts the batch's first
 * bytes that fit as one INPUT record, which the caller publishes; their
 * count is added to the domain's delivered bytes and the bytes to its
 * digest; the rest are dropped as ring-full (D-4), and the first such
 * drop is reported. A full input ring never fails the view: only a
 * malformed one does. The batch is empty afterwards.
 *
 * Return: the bytes posted, 0 for none; or %BE_MVP_INPUT_FAILED for absent
 *         or invalid input, or a ring view that failed (a malformed tail),
 *         with the batch kept.
 */
be_u64 be_mvp_input_flush(struct be_mvp_input *input, be_u32 domain,
			  struct be_mvp_ring *ring, be_u64 now,
			  struct be_mvp_input_event *event);

/**
 * be_mvp_input_poll_end - end one poll
 * @input: hart 0's console input
 *
 * The first poll after arming has discarded what the firmware held.
 */
void be_mvp_input_poll_end(struct be_mvp_input *input);

/**
 * be_mvp_input_digest - a domain's delivered bytes' SHA-256 so far
 * @input: hart 0's console input
 * @domain: the domain
 * @digest: %BE_MVP_SHA256_BYTES bytes; all zero for an absent input or
 *          another domain
 *
 * Finishes a copy of the running digest, which goes on.
 */
void be_mvp_input_digest(const struct be_mvp_input *input, be_u32 domain,
			 be_u8 *digest);

/**
 * be_mvp_input_rearm - hart 0's next timer deadline while input is armed
 * @input: hart 0's console input
 * @start: the run budget's start, the boot barrier's time
 * @budget: the run budget in ticks
 * @now: the time CSR
 * @deadline: on success, the earlier of @now plus
 *            %BE_MVP_INPUT_POLL_TICKS and @start plus @budget, each sum
 *            saturating: the next poll, but never past the budget's end,
 *            so the run still ends where its budget ends
 *
 * Return: 1 to re-arm hart 0's timer at @deadline; 0, with @deadline
 *         unchanged, when input is not armed: the budget's one arming
 *         stands, and hart 0 never re-arms for polling.
 */
int be_mvp_input_rearm(const struct be_mvp_input *input, be_u64 start,
		       be_u64 budget, be_u64 now, be_u64 *deadline);

/**
 * struct be_mvp_input_stage - a domain hart's staged input
 * @length: bytes staged, at most %BE_MVP_INPUT_STAGE_BYTES
 * @offset: the next staged byte to copy, at most @length
 * @bytes: the staged bytes: one INPUT record's payload
 *
 * The domain hart alone holds it, in its state page.
 */
struct be_mvp_input_stage {
	be_u64 length;
	be_u64 offset;
	be_u8 bytes[BE_MVP_INPUT_STAGE_BYTES];
};

/**
 * be_mvp_input_serve - serve one granted DBCN read from the input ring
 * @stage: the domain hart's staging buffer
 * @ring: the domain hart's acquired reader view of its input ring
 * @to: the guest buffer, through its window's HS physical address, which
 *      be_mvp_handle_exit() checked for the whole requested range
 * @length: the bytes the guest may receive, at most
 *          %BE_MVP_DBCN_MAX_BYTES: min(a0, 256)
 *
 * Copies the staged bytes first, then takes INPUT records into the stage,
 * one at a time, while the guest can receive more: min(@length, the
 * bytes queued) bytes in order, the rest of a record staged for the next
 * read. The caller acquired the ring and ordered its loads (fence r, r)
 * before, and releases the records taken (fence r, w) after. Nothing is
 * written past @to plus the returned count.
 *
 * Return: the bytes copied, 0 when nothing is queued; or
 *         %BE_MVP_INPUT_FAILED for absent or invalid input, a malformed
 *         ring (the view failed), or an INPUT record without a payload,
 *         each of which fails the domain hart as ring.
 */
be_u64 be_mvp_input_serve(struct be_mvp_input_stage *stage,
			  struct be_mvp_ring *ring, be_u8 *to,
			  be_u64 length);

#endif
