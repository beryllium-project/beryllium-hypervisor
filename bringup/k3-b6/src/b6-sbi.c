// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B6 guest SBI core: exit classification, the exit ceiling and
 *          the guest-time budget, per-class counters, the bounded SBI
 *          subset, the DBCN window check, the tagged guest console, the
 *          first-entry frame, the guest-control checks, and the monitor
 *          line builder.
 * Trust:   restricted C with explicit bounded loops. No CSR, SBI call, I/O,
 *          or guest-address dereference: the runtime performs each action.
 * Scope:   B6 only (planning/k3-b6-plan.md); see b6.h.
 */
#include "b6.h"

_Static_assert(BE_B6_TAGGED_CAPACITY <= BE_PAGE_SIZE,
	       "a tagged DBCN chunk must fit the HS diagnostic page");
_Static_assert(sizeof(BE_B6_GUEST_PREFIX) - 1U == BE_B6_GUEST_PREFIX_LENGTH,
	       "guest prefix length differs");
_Static_assert(BE_B6_HSTATUS_GUEST_CONTROLS == BE_U64_C(0x180),
	       "hstatus guest controls are SPV and SPVP");
_Static_assert(BE_B6_SSTATUS_CONTROL_MASK == BE_U64_C(0xde722),
	       "sstatus guest mask is R3's plus VS");
_Static_assert(sizeof(struct be_b6_exit) == 352U,
	       "the exit record is the accepted frame and four words");

static const char *const be_b6_class_names[BE_B6_CLASS_COUNT] = {
	[BE_B6_CLASS_NONE] = "none",
	[BE_B6_CLASS_BOOT] = "boot",
	[BE_B6_CLASS_GSTAGE] = "gstage",
	[BE_B6_CLASS_SSTC] = "sstc",
	[BE_B6_CLASS_CONTROLS] = "controls",
	[BE_B6_CLASS_PAYLOAD] = "payload",
	[BE_B6_CLASS_INTERRUPT] = "interrupt",
	[BE_B6_CLASS_GUEST_PAGE_FAULT] = "guest-page-fault",
	[BE_B6_CLASS_VIRTUAL_INSTRUCTION] = "virtual-instruction",
	[BE_B6_CLASS_ACCESS_FAULT] = "access-fault",
	[BE_B6_CLASS_ILLEGAL_INSTRUCTION] = "illegal-instruction",
	[BE_B6_CLASS_EXCEPTION] = "exception",
	[BE_B6_CLASS_EXIT_BUDGET] = "exit-budget",
	[BE_B6_CLASS_GUEST_TIMEOUT] = "guest-timeout",
	[BE_B6_CLASS_RESUME] = "resume",
	[BE_B6_CLASS_CONSOLE] = "console",
	[BE_B6_CLASS_GUEST_FAILURE] = "guest-failure",
	[BE_B6_CLASS_GUEST_REBOOT] = "guest-reboot",
	[BE_B6_CLASS_SHUTDOWN_RETURNED] = "shutdown-returned",
};

const char *be_b6_class_name(enum be_b6_class failure)
{
	if ((unsigned int)failure >= (unsigned int)BE_B6_CLASS_COUNT)
		return "invalid";
	return be_b6_class_names[failure];
}

enum be_b6_class be_b6_stce_class(be_u64 henvcfg)
{
	if ((henvcfg & BE_B6_HENVCFG_STCE) == 0U)
		return BE_B6_CLASS_SSTC;
	if (henvcfg != BE_B6_HENVCFG_STCE)
		return BE_B6_CLASS_CONTROLS;
	return BE_B6_CLASS_NONE;
}

int be_b6_controls_valid(const struct be_b6_controls *controls,
			 be_u64 expected_hgatp, be_u64 trusted_top)
{
	if (controls == (const struct be_b6_controls *)0)
		return 0;
	return controls->hip == 0U &&
	       (controls->hstatus & BE_R3_HSTATUS_CONTROL_MASK) ==
		       BE_B6_HSTATUS_GUEST_CONTROLS &&
	       controls->hedeleg == (controls->hedeleg & BE_B6_HEDELEG) &&
	       (controls->hedeleg & BE_B6_HEDELEG_REQUIRED) ==
		       BE_B6_HEDELEG_REQUIRED &&
	       controls->hideleg == BE_B6_HIDELEG_VSTI &&
	       controls->hie == 0U && controls->hvip == 0U &&
	       controls->hcounteren == BE_B6_HCOUNTEREN_TM &&
	       controls->htimedelta == 0U &&
	       controls->henvcfg == BE_B6_HENVCFG_STCE &&
	       controls->hgeie == 0U &&
	       controls->vstimecmp == BE_B6_VSTIMECMP_DISARMED &&
	       controls->sie == 0U &&
	       (controls->sstatus & BE_B6_SSTATUS_CONTROL_MASK) == 0U &&
	       controls->hgatp == expected_hgatp && controls->vsatp == 0U &&
	       controls->sscratch == trusted_top;
}

enum be_b6_class be_b6_classify_cause(be_u64 scause)
{
	if ((scause & BE_B6_SCAUSE_INTERRUPT) != 0U)
		return BE_B6_CLASS_INTERRUPT;
	switch (scause) {
	case BE_B6_SCAUSE_VS_ECALL:
		return BE_B6_CLASS_NONE;
	case BE_B6_SCAUSE_FETCH_GUEST_PAGE_FAULT:
	case BE_B6_SCAUSE_LOAD_GUEST_PAGE_FAULT:
	case BE_B6_SCAUSE_STORE_GUEST_PAGE_FAULT:
		return BE_B6_CLASS_GUEST_PAGE_FAULT;
	case BE_B6_SCAUSE_VIRTUAL_INSTRUCTION:
		return BE_B6_CLASS_VIRTUAL_INSTRUCTION;
	case BE_B6_SCAUSE_FETCH_ACCESS_FAULT:
	case BE_B6_SCAUSE_LOAD_ACCESS_FAULT:
	case BE_B6_SCAUSE_STORE_ACCESS_FAULT:
		return BE_B6_CLASS_ACCESS_FAULT;
	case BE_B6_SCAUSE_ILLEGAL_INSTRUCTION:
		return BE_B6_CLASS_ILLEGAL_INSTRUCTION;
	default:
		return BE_B6_CLASS_EXCEPTION;
	}
}

enum be_b6_class be_b6_fail(struct be_b6_state *state,
			    enum be_b6_class failure)
{
	if (failure == BE_B6_CLASS_NONE ||
	    (unsigned int)failure >= (unsigned int)BE_B6_CLASS_COUNT)
		failure = BE_B6_CLASS_EXCEPTION;
	if (state == (struct be_b6_state *)0)
		return failure;
	if (state->phase == BE_B6_PHASE_FAILED)
		return state->failure;
	state->phase = BE_B6_PHASE_FAILED;
	state->failure = failure;
	return failure;
}

static enum be_b6_action terminal(struct be_b6_state *state,
				  struct be_b6_result *result,
				  enum be_b6_class failure)
{
	result->action = BE_B6_ACTION_TERMINAL;
	result->failure = be_b6_fail(state, failure);
	return result->action;
}

static void sbi_return(struct be_b6_result *result, enum be_b6_action action,
		       long error, be_u64 value)
{
	result->action = action;
	result->error = error;
	result->value = value;
}

static int probe_available(be_u64 eid)
{
	return eid == BE_B6_SBI_EID_BASE || eid == BE_B6_SBI_EID_TIME ||
	       eid == BE_B6_SBI_EID_DBCN || eid == BE_B6_SBI_EID_SRST;
}

static void sbi_base(be_u64 fid, be_u64 argument0,
		     struct be_b6_result *result)
{
	if (fid == BE_B6_SBI_BASE_GET_SPEC_VERSION)
		sbi_return(result, BE_B6_ACTION_RETURN, BE_B6_SBI_SUCCESS,
			   BE_B6_SBI_SPEC_VERSION);
	else if (fid == BE_B6_SBI_BASE_GET_IMPL_ID)
		sbi_return(result, BE_B6_ACTION_RETURN, BE_B6_SBI_SUCCESS,
			   BE_B6_SBI_IMPL_ID);
	else if (fid == BE_B6_SBI_BASE_GET_IMPL_VERSION)
		sbi_return(result, BE_B6_ACTION_RETURN, BE_B6_SBI_SUCCESS,
			   BE_B6_SBI_IMPL_VERSION);
	else if (fid == BE_B6_SBI_BASE_PROBE_EXTENSION)
		sbi_return(result, BE_B6_ACTION_RETURN, BE_B6_SBI_SUCCESS,
			   probe_available(argument0) ? 1U : 0U);
	else if (fid == BE_B6_SBI_BASE_GET_MVENDORID ||
		 fid == BE_B6_SBI_BASE_GET_MARCHID ||
		 fid == BE_B6_SBI_BASE_GET_MIMPID)
		sbi_return(result, BE_B6_ACTION_RETURN, BE_B6_SBI_SUCCESS, 0U);
	else
		sbi_return(result, BE_B6_ACTION_RETURN,
			   BE_B6_SBI_ERR_NOT_SUPPORTED, 0U);
}

static void sbi_dbcn(const struct be_b6_gstage_map *map, be_u64 fid,
		     const struct be_r4_frame *frame,
		     struct be_b6_result *result)
{
	be_u64 length = frame->gpr[BE_R4_GPR_A0];
	be_u64 address = frame->gpr[BE_R4_GPR_A1];
	be_u64 address_high = frame->gpr[BE_B6_GPR_A2];

	if (fid == BE_B6_SBI_DBCN_WRITE) {
		if (address_high != 0U)
			sbi_return(result, BE_B6_ACTION_RETURN,
				   BE_B6_SBI_ERR_INVALID_PARAM, 0U);
		else if (length == 0U)
			sbi_return(result, BE_B6_ACTION_RETURN,
				   BE_B6_SBI_SUCCESS, 0U);
		else if (!be_b6_gstage_translate(map, address, length,
						 &result->source_pa))
			sbi_return(result, BE_B6_ACTION_RETURN,
				   BE_B6_SBI_ERR_INVALID_PARAM, 0U);
		else {
			result->length = length < BE_B6_DBCN_MAX_BYTES ?
				length : BE_B6_DBCN_MAX_BYTES;
			sbi_return(result, BE_B6_ACTION_CONSOLE_WRITE,
				   BE_B6_SBI_SUCCESS, result->length);
		}
	} else if (fid == BE_B6_SBI_DBCN_READ) {
		sbi_return(result, BE_B6_ACTION_RETURN, BE_B6_SBI_ERR_DENIED,
			   0U);
	} else if (fid == BE_B6_SBI_DBCN_WRITE_BYTE) {
		result->byte = (be_u8)(length & 0xffU);
		sbi_return(result, BE_B6_ACTION_CONSOLE_BYTE, BE_B6_SBI_SUCCESS,
			   0U);
	} else {
		sbi_return(result, BE_B6_ACTION_RETURN,
			   BE_B6_SBI_ERR_NOT_SUPPORTED, 0U);
	}
}

static void sbi_srst(struct be_b6_state *state, be_u64 fid,
		     const struct be_r4_frame *frame,
		     struct be_b6_result *result)
{
	be_u64 type = frame->gpr[BE_R4_GPR_A0];
	be_u64 reason = frame->gpr[BE_R4_GPR_A1];

	if (fid != BE_B6_SBI_SRST_SYSTEM_RESET)
		sbi_return(result, BE_B6_ACTION_RETURN,
			   BE_B6_SBI_ERR_NOT_SUPPORTED, 0U);
	else if (type > BE_B6_SRST_TYPE_WARM_REBOOT ||
		 reason > BE_B6_SRST_REASON_FAILURE)
		sbi_return(result, BE_B6_ACTION_RETURN,
			   BE_B6_SBI_ERR_INVALID_PARAM, 0U);
	else if (type != BE_B6_SRST_TYPE_SHUTDOWN) {
		/* A reboot request (panic=-1 included) ends the run. */
		result->failure = be_b6_fail(state, BE_B6_CLASS_GUEST_REBOOT);
		sbi_return(result, BE_B6_ACTION_GUEST_REBOOT,
			   BE_B6_SBI_SUCCESS, 0U);
	} else if (reason == BE_B6_SRST_REASON_NONE) {
		state->phase = BE_B6_PHASE_SHUTDOWN;
		sbi_return(result, BE_B6_ACTION_SHUTDOWN, BE_B6_SBI_SUCCESS,
			   0U);
	} else {
		result->failure = be_b6_fail(state, BE_B6_CLASS_GUEST_FAILURE);
		sbi_return(result, BE_B6_ACTION_GUEST_FAILURE,
			   BE_B6_SBI_SUCCESS, 0U);
	}
}

/* Each accepted ecall adds one to exactly one call class. */
static void count_call(struct be_b6_counts *counts, be_u64 eid, be_u64 fid,
		       const struct be_b6_result *result)
{
	if (result->error == BE_B6_SBI_ERR_NOT_SUPPORTED ||
	    result->error == BE_B6_SBI_ERR_INVALID_PARAM)
		++counts->refused;
	else if (eid == BE_B6_SBI_EID_BASE)
		++counts->base;
	else if (eid == BE_B6_SBI_EID_TIME)
		++counts->time;
	else if (eid == BE_B6_SBI_EID_SRST)
		++counts->srst;
	else if (fid == BE_B6_SBI_DBCN_WRITE)
		++counts->dbcn_write;
	else if (fid == BE_B6_SBI_DBCN_READ)
		++counts->dbcn_read;
	else
		++counts->dbcn_byte;
}

enum be_b6_action be_b6_handle_exit(struct be_b6_state *state,
				    const struct be_b6_gstage_map *map,
				    const struct be_b6_exit *record,
				    struct be_b6_result *result)
{
	const struct be_r4_frame *frame;
	enum be_b6_class failure;
	be_u64 eid;
	be_u64 fid;

	if (result == (struct be_b6_result *)0) {
		(void)be_b6_fail(state, BE_B6_CLASS_EXCEPTION);
		return BE_B6_ACTION_TERMINAL;
	}
	*result = (struct be_b6_result){ 0 };
	if (state == (struct be_b6_state *)0 ||
	    map == (const struct be_b6_gstage_map *)0 ||
	    record == (const struct be_b6_exit *)0 ||
	    state->phase != BE_B6_PHASE_RUNNING)
		return terminal(state, result, BE_B6_CLASS_EXCEPTION);
	if (state->counts.exits >= state->exit_ceiling) {
		state->counts.exits = state->exit_ceiling + 1U;
		return terminal(state, result, BE_B6_CLASS_EXIT_BUDGET);
	}
	++state->counts.exits;
	if (record->time - state->entry_time >= state->time_budget)
		return terminal(state, result, BE_B6_CLASS_GUEST_TIMEOUT);
	frame = &record->frame;
	if (frame->reserved != 0U || (record->hstatus & BE_B6_HSTATUS_SPV) == 0U)
		return terminal(state, result, BE_B6_CLASS_EXCEPTION);
	failure = be_b6_classify_cause(frame->scause);
	if (failure != BE_B6_CLASS_NONE)
		return terminal(state, result, failure);
	if (frame->sepc > ~BE_U64_C(0) - BE_B6_INSTRUCTION_SIZE)
		return terminal(state, result, BE_B6_CLASS_RESUME);
	result->resume_pc = frame->sepc + BE_B6_INSTRUCTION_SIZE;

	eid = frame->gpr[BE_R4_GPR_A7];
	fid = frame->gpr[BE_R4_GPR_A6];
	if (eid == BE_B6_SBI_EID_BASE)
		sbi_base(fid, frame->gpr[BE_R4_GPR_A0], result);
	else if (eid == BE_B6_SBI_EID_TIME &&
		 fid == BE_B6_SBI_TIME_SET_TIMER) {
		result->timer = frame->gpr[BE_R4_GPR_A0];
		sbi_return(result, BE_B6_ACTION_SET_TIMER, BE_B6_SBI_SUCCESS,
			   0U);
	} else if (eid == BE_B6_SBI_EID_DBCN)
		sbi_dbcn(map, fid, frame, result);
	else if (eid == BE_B6_SBI_EID_SRST)
		sbi_srst(state, fid, frame, result);
	else
		sbi_return(result, BE_B6_ACTION_RETURN,
			   BE_B6_SBI_ERR_NOT_SUPPORTED, 0U);
	count_call(&state->counts, eid, fid, result);
	return result->action;
}

void be_b6_apply_return(struct be_r4_frame *frame,
			const struct be_b6_result *result)
{
	if (frame == (struct be_r4_frame *)0 ||
	    result == (const struct be_b6_result *)0)
		return;
	frame->gpr[BE_R4_GPR_A0] = (be_u64)result->error;
	frame->gpr[BE_R4_GPR_A1] = result->value;
	frame->sepc = result->resume_pc;
}

void be_b6_entry_frame(struct be_b6_exit *record, be_u64 pc, be_u64 hart,
		       be_u64 dtb)
{
	if (record == (struct be_b6_exit *)0)
		return;
	*record = (struct be_b6_exit){ 0 };
	record->frame.sepc = pc;
	record->frame.gpr[BE_R4_GPR_A0] = hart;
	record->frame.gpr[BE_R4_GPR_A1] = dtb;
}

be_u64 be_b6_console_tag(struct be_b6_console *console, const be_u8 *input,
			 be_u64 length, char *output, be_u64 capacity)
{
	static const char prefix[] = BE_B6_GUEST_PREFIX;
	be_u64 used = 0U;
	be_u64 index;
	be_u64 offset;

	if (console == (struct be_b6_console *)0 ||
	    input == (const be_u8 *)0 || output == (char *)0 ||
	    length > BE_B6_DBCN_MAX_BYTES || capacity < BE_B6_TAGGED_CAPACITY)
		return BE_B6_TAG_INVALID;
	for (index = 0U; index < length; ++index) {
		be_u8 byte = input[index];

		/* hvc sends CR before LF; CR is dropped, not shown. */
		if (byte == (be_u8)'\r')
			continue;
		if (console->line_open == 0U) {
			for (offset = 0U; offset < BE_B6_GUEST_PREFIX_LENGTH;
			     ++offset)
				output[used++] = prefix[offset];
			console->line_open = 1U;
		}
		if (byte == (be_u8)'\n') {
			output[used++] = '\n';
			console->line_open = 0U;
		} else if (byte >= 0x20U && byte <= 0x7eU) {
			output[used++] = (char)byte;
		} else {
			output[used++] = '?';
		}
	}
	return used;
}

be_u32 be_b6_console_close(struct be_b6_console *console)
{
	if (console == (struct be_b6_console *)0 || console->line_open == 0U)
		return 0U;
	console->line_open = 0U;
	return 1U;
}

void be_b6_line_reset(struct be_b6_line *line)
{
	if (line == (struct be_b6_line *)0)
		return;
	line->length = 0U;
	line->overflow = 0U;
}

static void line_byte(struct be_b6_line *line, char byte)
{
	if (line->overflow != 0U || line->length >= BE_B6_LINE_CAPACITY) {
		line->overflow = 1U;
		return;
	}
	line->text[line->length++] = byte;
}

void be_b6_line_text(struct be_b6_line *line, const char *text)
{
	be_u64 index;

	if (line == (struct be_b6_line *)0)
		return;
	if (text == (const char *)0) {
		line->overflow = 1U;
		return;
	}
	for (index = 0U; index <= BE_B6_LINE_CAPACITY && text[index] != '\0';
	     ++index)
		line_byte(line, text[index]);
}

void be_b6_line_hex(struct be_b6_line *line, be_u64 value)
{
	static const char digits[] = "0123456789abcdef";
	unsigned int shift = 60U;

	if (line == (struct be_b6_line *)0)
		return;
	line_byte(line, '0');
	line_byte(line, 'x');
	while (shift > 0U && ((value >> shift) & 0xfU) == 0U)
		shift -= 4U;
	for (;;) {
		line_byte(line, digits[(value >> shift) & 0xfU]);
		if (shift == 0U)
			break;
		shift -= 4U;
	}
}

void be_b6_line_decimal(struct be_b6_line *line, be_u64 value)
{
	char digits[20];
	unsigned int count = 0U;

	if (line == (struct be_b6_line *)0)
		return;
	do {
		digits[count++] = (char)('0' + (int)(value % 10U));
		value /= 10U;
	} while (value != 0U && count < sizeof(digits));
	while (count > 0U)
		line_byte(line, digits[--count]);
}
