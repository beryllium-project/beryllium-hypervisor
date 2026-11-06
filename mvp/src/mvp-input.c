// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP console input (mvp-input.h; planning/mvp-m7-plan.md, D-1,
 *          D-3, and D-4): the focus parser's table, hart 0's routing,
 *          drops, accounting, and flush into a domain's input ring, the
 *          poll's next deadline, and a domain hart's served DBCN read.
 * Trust:   restricted C with explicit bounded loops; no CSR, fence, SBI
 *          call, I/O, or mutable global. Invalid input routes nothing and
 *          copies nothing.
 * Scope:   the MVP line from M7; see mvp-input.h.
 */
#include "mvp-input.h"

/* The parser's byte classes: the prefix, the two domains' digits, CR or
 * LF, and every other byte. */
enum focus_class {
	CLASS_PREFIX = 0,
	CLASS_DIGIT0,
	CLASS_DIGIT1,
	CLASS_END,
	CLASS_OTHER,
	CLASS_COUNT,
};

/* One cell of the parser's table: the byte's meaning and the next state. */
struct focus_cell {
	enum be_mvp_focus_kind kind;
	enum be_mvp_focus_state next;
};

#define LINE_START	BE_MVP_FOCUS_LINE_START
#define AFTER_PREFIX	BE_MVP_FOCUS_AFTER_PREFIX
#define IN_LINE		BE_MVP_FOCUS_IN_LINE
#define DELIVER		BE_MVP_FOCUS_DELIVER
#define SELECT		BE_MVP_FOCUS_SELECT
#define DROP		BE_MVP_FOCUS_DROP
#define HOLD		BE_MVP_FOCUS_HOLD

_Static_assert(BE_MVP_DOMAINS == 2U, "two domains, digits 0 and 1");
_Static_assert(BE_MVP_INPUT_PREFIX == (be_u8)'~',
	       "the prefix is the tilde (Q1)");
_Static_assert(BE_MVP_INPUT_STAGE_BYTES == BE_MVP_DBCN_MAX_BYTES &&
	       BE_MVP_INPUT_POLL_MAX == BE_MVP_RECORD_PAYLOAD_MAX &&
	       BE_MVP_INPUT_READ_BYTES <= BE_MVP_INPUT_POLL_MAX,
	       "one poll's bytes for a domain fit one INPUT record, and one "
	       "record the domain hart's stage");
_Static_assert(BE_MVP_DROP_REASONS <= 64U, "the reasons fit one mask");

/*
 * The table (D-3), the specification: rows are the states, columns the
 * classes.
 */
static const struct focus_cell focus_table[BE_MVP_FOCUS_STATES][CLASS_COUNT] = {
	[LINE_START] = {
		[CLASS_PREFIX] = { HOLD, AFTER_PREFIX },
		[CLASS_DIGIT0] = { DELIVER, IN_LINE },
		[CLASS_DIGIT1] = { DELIVER, IN_LINE },
		[CLASS_END] = { DELIVER, LINE_START },
		[CLASS_OTHER] = { DELIVER, IN_LINE },
	},
	[AFTER_PREFIX] = {
		[CLASS_PREFIX] = { DELIVER, IN_LINE },
		[CLASS_DIGIT0] = { SELECT, LINE_START },
		[CLASS_DIGIT1] = { SELECT, LINE_START },
		[CLASS_END] = { DROP, LINE_START },
		[CLASS_OTHER] = { DROP, LINE_START },
	},
	[IN_LINE] = {
		[CLASS_PREFIX] = { DELIVER, IN_LINE },
		[CLASS_DIGIT0] = { DELIVER, IN_LINE },
		[CLASS_DIGIT1] = { DELIVER, IN_LINE },
		[CLASS_END] = { DELIVER, LINE_START },
		[CLASS_OTHER] = { DELIVER, IN_LINE },
	},
};

static const char *const drop_names[BE_MVP_DROP_REASONS] = {
	[BE_MVP_DROP_NO_FOCUS] = "no-focus",
	[BE_MVP_DROP_NO_GRANT] = "no-grant",
	[BE_MVP_DROP_NOT_RUNNING] = "not-running",
	[BE_MVP_DROP_RING_FULL] = "ring-full",
	[BE_MVP_DROP_BAD_SEQUENCE] = "bad-sequence",
	[BE_MVP_DROP_BEFORE_ARMED] = "before-armed",
};

static enum focus_class classify(be_u8 byte)
{
	if (byte == (be_u8)BE_MVP_INPUT_PREFIX)
		return CLASS_PREFIX;
	if (byte == (be_u8)'0')
		return CLASS_DIGIT0;
	if (byte == (be_u8)'1')
		return CLASS_DIGIT1;
	if (byte == (be_u8)'\r' || byte == (be_u8)'\n')
		return CLASS_END;
	return CLASS_OTHER;
}

enum be_mvp_focus_state be_mvp_focus_step(enum be_mvp_focus_state state,
					  be_u8 byte,
					  struct be_mvp_focus_out *out)
{
	struct be_mvp_focus_out none = { BE_MVP_FOCUS_DROP, 0U,
					 BE_MVP_DROP_BAD_SEQUENCE, 0U };
	const struct focus_cell *cell;
	enum focus_class class = classify(byte);

	if ((unsigned int)state >= (unsigned int)BE_MVP_FOCUS_STATES) {
		if (out != (struct be_mvp_focus_out *)0)
			*out = none;
		return BE_MVP_FOCUS_LINE_START;
	}
	cell = &focus_table[state][class];
	if (out == (struct be_mvp_focus_out *)0)
		return cell->next;
	*out = (struct be_mvp_focus_out){ cell->kind, 0U, BE_MVP_DROP_NO_FOCUS,
					  0U };
	if (cell->kind == BE_MVP_FOCUS_DELIVER)
		out->byte = byte;
	else if (cell->kind == BE_MVP_FOCUS_SELECT)
		out->domain = class == CLASS_DIGIT1 ? 1U : 0U;
	else if (cell->kind == BE_MVP_FOCUS_DROP)
		out->reason = BE_MVP_DROP_BAD_SEQUENCE;
	return cell->next;
}

const char *be_mvp_input_drop_name(enum be_mvp_input_drop reason)
{
	if ((unsigned int)reason >= (unsigned int)BE_MVP_DROP_REASONS)
		return "invalid";
	return drop_names[reason];
}

static be_u64 add_saturating(be_u64 value, be_u64 addend)
{
	if (addend > ~BE_U64_C(0) - value)
		return ~BE_U64_C(0);
	return value + addend;
}

static be_u64 bit(be_u64 index)
{
	return BE_U64_C(1) << index;
}

/* Count @bytes dropped for @reason; report the reason's first drop. */
static void drop(struct be_mvp_input *input, enum be_mvp_input_drop reason,
		 be_u64 bytes, struct be_mvp_input_event *event)
{
	if (bytes == 0U)
		return;
	input->dropped[reason] = add_saturating(input->dropped[reason], bytes);
	if ((input->announced & bit(reason)) != 0U)
		return;
	input->announced |= bit(reason);
	event->report = BE_MVP_INPUT_FIRST_DROP;
	event->reason = reason;
}

int be_mvp_input_arm(struct be_mvp_input *input, be_u64 grants)
{
	be_u32 domain;

	if (input == (struct be_mvp_input *)0)
		return 0;
	*input = (struct be_mvp_input){ 0 };
	if (grants == 0U || (grants & ~(bit(BE_MVP_DOMAINS) - 1U)) != 0U)
		return 0;
	input->armed = 1U;
	input->discard = 1U;
	input->grants = grants;
	input->state = BE_MVP_FOCUS_LINE_START;
	input->focus = BE_MVP_INPUT_NO_FOCUS;
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		be_mvp_sha256_init(&input->digest[domain]);
	return 1;
}

void be_mvp_input_poll_begin(struct be_mvp_input *input)
{
	be_u32 domain;

	if (input == (struct be_mvp_input *)0)
		return;
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		input->pending[domain] = 0U;
}

void be_mvp_input_byte(struct be_mvp_input *input, be_u8 byte,
		       be_u64 running, struct be_mvp_input_event *event)
{
	struct be_mvp_focus_out out;
	be_u32 focus;

	if (event == (struct be_mvp_input_event *)0)
		return;
	*event = (struct be_mvp_input_event){ BE_MVP_INPUT_QUIET, 0U,
					      BE_MVP_DROP_NO_FOCUS };
	if (input == (struct be_mvp_input *)0 || input->armed != 1U)
		return;
	input->read = add_saturating(input->read, 1U);
	if (input->discard != 0U) {
		drop(input, BE_MVP_DROP_BEFORE_ARMED, 1U, event);
		return;
	}
	input->state = be_mvp_focus_step(input->state, byte, &out);
	focus = input->focus;
	switch (out.kind) {
	case BE_MVP_FOCUS_SELECT:
		if (out.domain >= BE_MVP_DOMAINS ||
		    (input->grants & bit(out.domain)) == 0U) {
			drop(input, BE_MVP_DROP_NO_GRANT, 1U, event);
			return;
		}
		input->focus = out.domain;
		event->report = BE_MVP_INPUT_FOCUSED;
		event->domain = out.domain;
		return;
	case BE_MVP_FOCUS_DELIVER:
		if (focus >= BE_MVP_DOMAINS ||
		    (input->grants & bit(focus)) == 0U) {
			drop(input, BE_MVP_DROP_NO_FOCUS, 1U, event);
			return;
		}
		if ((running & bit(focus)) == 0U) {
			drop(input, BE_MVP_DROP_NOT_RUNNING, 1U, event);
			return;
		}
		if (input->pending[focus] >= BE_MVP_INPUT_POLL_MAX) {
			drop(input, BE_MVP_DROP_RING_FULL, 1U, event);
			return;
		}
		input->batch[focus][input->pending[focus]++] = out.byte;
		return;
	case BE_MVP_FOCUS_DROP:
		drop(input, BE_MVP_DROP_BAD_SEQUENCE, 1U, event);
		return;
	case BE_MVP_FOCUS_HOLD:
	default:
		return;
	}
}

be_u64 be_mvp_input_flush(struct be_mvp_input *input, be_u32 domain,
			  struct be_mvp_ring *ring, be_u64 now,
			  struct be_mvp_input_event *event)
{
	be_u64 pending;
	be_u64 room;

	if (event == (struct be_mvp_input_event *)0)
		return BE_MVP_INPUT_FAILED;
	*event = (struct be_mvp_input_event){ BE_MVP_INPUT_QUIET, 0U,
					      BE_MVP_DROP_NO_FOCUS };
	if (input == (struct be_mvp_input *)0 || input->armed != 1U ||
	    domain >= BE_MVP_DOMAINS ||
	    input->pending[domain] > BE_MVP_INPUT_POLL_MAX ||
	    ring == (struct be_mvp_ring *)0)
		return BE_MVP_INPUT_FAILED;
	pending = input->pending[domain];
	if (pending == 0U)
		return 0U;
	room = be_mvp_ring_room(ring);
	if (ring->failed != 0U)
		return BE_MVP_INPUT_FAILED;
	if (room > pending)
		room = pending;
	if (room != 0U) {
		if (!be_mvp_ring_post(ring, BE_MVP_RECORD_INPUT, now,
				      input->batch[domain], room))
			return BE_MVP_INPUT_FAILED;
		be_mvp_sha256_update(&input->digest[domain],
				     input->batch[domain], room);
		input->delivered[domain] =
			add_saturating(input->delivered[domain], room);
	}
	drop(input, BE_MVP_DROP_RING_FULL, pending - room, event);
	input->pending[domain] = 0U;
	return room;
}

void be_mvp_input_poll_end(struct be_mvp_input *input)
{
	if (input == (struct be_mvp_input *)0)
		return;
	input->discard = 0U;
}

void be_mvp_input_digest(const struct be_mvp_input *input, be_u32 domain,
			 be_u8 *digest)
{
	struct be_mvp_sha256 copy;
	be_u32 index;

	if (digest == (be_u8 *)0)
		return;
	if (input == (const struct be_mvp_input *)0 ||
	    domain >= BE_MVP_DOMAINS) {
		for (index = 0U; index < BE_MVP_SHA256_BYTES; ++index)
			digest[index] = 0U;
		return;
	}
	copy = input->digest[domain];
	be_mvp_sha256_final(&copy, digest);
}

int be_mvp_input_rearm(const struct be_mvp_input *input, be_u64 start,
		       be_u64 budget, be_u64 now, be_u64 *deadline)
{
	be_u64 next;
	be_u64 end;

	if (input == (const struct be_mvp_input *)0 || input->armed != 1U ||
	    deadline == (be_u64 *)0)
		return 0;
	next = add_saturating(now, BE_MVP_INPUT_POLL_TICKS);
	end = add_saturating(start, budget);
	*deadline = next < end ? next : end;
	return 1;
}

be_u64 be_mvp_input_serve(struct be_mvp_input_stage *stage,
			  struct be_mvp_ring *ring, be_u8 *to,
			  be_u64 length)
{
	struct be_mvp_record record;
	be_u64 copied;
	be_u64 index;

	if (stage == (struct be_mvp_input_stage *)0 ||
	    ring == (struct be_mvp_ring *)0 ||
	    (to == (be_u8 *)0 && length != 0U) ||
	    length > BE_MVP_DBCN_MAX_BYTES ||
	    stage->length > BE_MVP_INPUT_STAGE_BYTES ||
	    stage->offset > stage->length)
		return BE_MVP_INPUT_FAILED;
	for (copied = 0U; copied < length; ++copied) {
		if (stage->offset == stage->length) {
			enum be_mvp_ring_status status =
				be_mvp_ring_take(ring, &record);

			if (status == BE_MVP_RING_EMPTY)
				break;
			if (status != BE_MVP_RING_RECORD ||
			    record.type != BE_MVP_RECORD_INPUT ||
			    record.length == 0U ||
			    record.length > BE_MVP_INPUT_STAGE_BYTES)
				return BE_MVP_INPUT_FAILED;
			for (index = 0U; index < record.length; ++index)
				stage->bytes[index] = record.payload[index];
			stage->length = record.length;
			stage->offset = 0U;
		}
		to[copied] = stage->bytes[stage->offset++];
	}
	if (stage->offset == stage->length) {
		stage->length = 0U;
		stage->offset = 0U;
	}
	return copied;
}
