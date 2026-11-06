// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B5 guest SBI core: exit classification and budget, the
 *          bounded SBI subset, the DBCN range check, the tagged guest
 *          console, and the monitor line builder.
 * Trust:   restricted C with explicit bounded loops. No CSR, SBI call, I/O,
 *          or guest-address dereference: the runtime performs each action.
 * Scope:   B5 only (planning/k3-b5-plan.md); see b5.h.
 */
#include "b5.h"

_Static_assert(BE_B5_TAGGED_CAPACITY <= BE_PAGE_SIZE,
	       "a tagged DBCN chunk must fit the HS diagnostic page");
_Static_assert(sizeof(BE_B5_GUEST_PREFIX) - 1U == BE_B5_GUEST_PREFIX_LENGTH,
	       "guest prefix length differs");

static const char *const be_b5_class_names[BE_B5_CLASS_COUNT] = {
	[BE_B5_CLASS_NONE] = "none",
	[BE_B5_CLASS_BOOT] = "boot",
	[BE_B5_CLASS_SSTC] = "sstc",
	[BE_B5_CLASS_CONTROLS] = "controls",
	[BE_B5_CLASS_INTERRUPT] = "interrupt",
	[BE_B5_CLASS_GUEST_PAGE_FAULT] = "guest-page-fault",
	[BE_B5_CLASS_VIRTUAL_INSTRUCTION] = "virtual-instruction",
	[BE_B5_CLASS_ILLEGAL_INSTRUCTION] = "illegal-instruction",
	[BE_B5_CLASS_EXCEPTION] = "exception",
	[BE_B5_CLASS_EXIT_BUDGET] = "exit-budget",
	[BE_B5_CLASS_RESUME] = "resume",
	[BE_B5_CLASS_CONSOLE] = "console",
	[BE_B5_CLASS_GUEST_FAILURE] = "guest-failure",
	[BE_B5_CLASS_SHUTDOWN_RETURNED] = "shutdown-returned",
};

const char *be_b5_class_name(enum be_b5_class failure)
{
	if ((unsigned int)failure >= (unsigned int)BE_B5_CLASS_COUNT)
		return "invalid";
	return be_b5_class_names[failure];
}

enum be_b5_class be_b5_stce_class(be_u64 henvcfg)
{
	if ((henvcfg & BE_B5_HENVCFG_STCE) == 0U)
		return BE_B5_CLASS_SSTC;
	if (henvcfg != BE_B5_HENVCFG_STCE)
		return BE_B5_CLASS_CONTROLS;
	return BE_B5_CLASS_NONE;
}

int be_b5_controls_valid(const struct be_b5_controls *controls,
			 be_u64 expected_hgatp)
{
	if (controls == (const struct be_b5_controls *)0)
		return 0;
	return controls->hip == 0U &&
	       (controls->hstatus & BE_R3_HSTATUS_CONTROL_MASK) ==
		       BE_B5_HSTATUS_GUEST_CONTROLS &&
	       controls->hedeleg == 0U &&
	       controls->hideleg == BE_B5_HIDELEG_VSTI &&
	       controls->hie == 0U && controls->hvip == 0U &&
	       controls->hcounteren == BE_B5_HCOUNTEREN_TM &&
	       controls->htimedelta == 0U &&
	       controls->henvcfg == BE_B5_HENVCFG_STCE &&
	       controls->hgeie == 0U &&
	       controls->vstimecmp == BE_B5_VSTIMECMP_DISARMED &&
	       controls->sie == 0U &&
	       (controls->sstatus & BE_R3_SSTATUS_SIE) == 0U &&
	       controls->hgatp == expected_hgatp && controls->vsatp == 0U;
}

enum be_b5_class be_b5_classify_cause(be_u64 scause)
{
	if ((scause & BE_B5_SCAUSE_INTERRUPT) != 0U)
		return BE_B5_CLASS_INTERRUPT;
	switch (scause) {
	case BE_B5_SCAUSE_VS_ECALL:
		return BE_B5_CLASS_NONE;
	case BE_B5_SCAUSE_FETCH_GUEST_PAGE_FAULT:
	case BE_B5_SCAUSE_LOAD_GUEST_PAGE_FAULT:
	case BE_B5_SCAUSE_STORE_GUEST_PAGE_FAULT:
		return BE_B5_CLASS_GUEST_PAGE_FAULT;
	case BE_B5_SCAUSE_VIRTUAL_INSTRUCTION:
		return BE_B5_CLASS_VIRTUAL_INSTRUCTION;
	case BE_B5_SCAUSE_ILLEGAL_INSTRUCTION:
		return BE_B5_CLASS_ILLEGAL_INSTRUCTION;
	default:
		return BE_B5_CLASS_EXCEPTION;
	}
}

int be_b5_translate_read(const struct be_r2_leaf_set *leaves, be_u64 gpa,
			 be_u64 length, be_u64 *pa)
{
	be_size index;

	if (leaves == (const struct be_r2_leaf_set *)0 ||
	    pa == (be_u64 *)0 || leaves->count > BE_MAX_MAPPINGS ||
	    length == 0U || length > ~gpa)
		return 0;
	for (index = 0U; index < leaves->count; ++index) {
		const struct be_r2_leaf *leaf = &leaves->leaves[index];
		be_u64 offset;

		if ((leaf->rights & BE_RIGHT_READ) == 0U ||
		    (leaf->gpa & (BE_PAGE_SIZE - 1U)) != 0U ||
		    (leaf->pa & (BE_PAGE_SIZE - 1U)) != 0U ||
		    gpa < leaf->gpa)
			continue;
		offset = gpa - leaf->gpa;
		if (offset >= BE_PAGE_SIZE || length > BE_PAGE_SIZE - offset)
			continue;
		*pa = leaf->pa + offset;
		return 1;
	}
	return 0;
}

enum be_b5_class be_b5_fail(struct be_b5_state *state,
			    enum be_b5_class failure)
{
	if (failure == BE_B5_CLASS_NONE ||
	    (unsigned int)failure >= (unsigned int)BE_B5_CLASS_COUNT)
		failure = BE_B5_CLASS_EXCEPTION;
	if (state == (struct be_b5_state *)0)
		return failure;
	if (state->phase == BE_B5_PHASE_FAILED)
		return state->failure;
	state->phase = BE_B5_PHASE_FAILED;
	state->failure = failure;
	return failure;
}

static enum be_b5_action terminal(struct be_b5_state *state,
				  struct be_b5_result *result,
				  enum be_b5_class failure)
{
	result->action = BE_B5_ACTION_TERMINAL;
	result->failure = be_b5_fail(state, failure);
	return result->action;
}

static void sbi_return(struct be_b5_result *result, enum be_b5_action action,
		       long error, be_u64 value)
{
	result->action = action;
	result->error = error;
	result->value = value;
}

static int probe_available(be_u64 eid)
{
	return eid == BE_B5_SBI_EID_BASE || eid == BE_B5_SBI_EID_TIME ||
	       eid == BE_B5_SBI_EID_DBCN || eid == BE_B5_SBI_EID_SRST;
}

static void sbi_base(be_u64 fid, be_u64 argument0,
		     struct be_b5_result *result)
{
	if (fid == BE_B5_SBI_BASE_GET_SPEC_VERSION)
		sbi_return(result, BE_B5_ACTION_RETURN, BE_B5_SBI_SUCCESS,
			   BE_B5_SBI_SPEC_VERSION);
	else if (fid == BE_B5_SBI_BASE_GET_IMPL_ID)
		sbi_return(result, BE_B5_ACTION_RETURN, BE_B5_SBI_SUCCESS,
			   BE_B5_SBI_IMPL_ID);
	else if (fid == BE_B5_SBI_BASE_GET_IMPL_VERSION)
		sbi_return(result, BE_B5_ACTION_RETURN, BE_B5_SBI_SUCCESS,
			   BE_B5_SBI_IMPL_VERSION);
	else if (fid == BE_B5_SBI_BASE_PROBE_EXTENSION)
		sbi_return(result, BE_B5_ACTION_RETURN, BE_B5_SBI_SUCCESS,
			   probe_available(argument0) ? 1U : 0U);
	else if (fid == BE_B5_SBI_BASE_GET_MVENDORID ||
		 fid == BE_B5_SBI_BASE_GET_MARCHID ||
		 fid == BE_B5_SBI_BASE_GET_MIMPID)
		sbi_return(result, BE_B5_ACTION_RETURN, BE_B5_SBI_SUCCESS, 0U);
	else
		sbi_return(result, BE_B5_ACTION_RETURN,
			   BE_B5_SBI_ERR_NOT_SUPPORTED, 0U);
}

static void sbi_dbcn(const struct be_r2_leaf_set *leaves, be_u64 fid,
		     const struct be_r4_frame *frame,
		     struct be_b5_result *result)
{
	be_u64 length = frame->gpr[BE_R4_GPR_A0];
	be_u64 address = frame->gpr[BE_R4_GPR_A1];
	be_u64 address_high = frame->gpr[BE_B5_GPR_A2];

	if (fid == BE_B5_SBI_DBCN_WRITE) {
		if (address_high != 0U)
			sbi_return(result, BE_B5_ACTION_RETURN,
				   BE_B5_SBI_ERR_INVALID_PARAM, 0U);
		else if (length == 0U)
			sbi_return(result, BE_B5_ACTION_RETURN,
				   BE_B5_SBI_SUCCESS, 0U);
		else if (!be_b5_translate_read(leaves, address, length,
					       &result->source_pa))
			sbi_return(result, BE_B5_ACTION_RETURN,
				   BE_B5_SBI_ERR_INVALID_PARAM, 0U);
		else {
			result->length = length < BE_B5_DBCN_MAX_BYTES ?
				length : BE_B5_DBCN_MAX_BYTES;
			sbi_return(result, BE_B5_ACTION_CONSOLE_WRITE,
				   BE_B5_SBI_SUCCESS, result->length);
		}
	} else if (fid == BE_B5_SBI_DBCN_READ) {
		sbi_return(result, BE_B5_ACTION_RETURN, BE_B5_SBI_ERR_DENIED,
			   0U);
	} else if (fid == BE_B5_SBI_DBCN_WRITE_BYTE) {
		result->byte = (be_u8)(length & 0xffU);
		sbi_return(result, BE_B5_ACTION_CONSOLE_BYTE, BE_B5_SBI_SUCCESS,
			   0U);
	} else {
		sbi_return(result, BE_B5_ACTION_RETURN,
			   BE_B5_SBI_ERR_NOT_SUPPORTED, 0U);
	}
}

static void sbi_srst(struct be_b5_state *state, be_u64 fid,
		     const struct be_r4_frame *frame,
		     struct be_b5_result *result)
{
	be_u64 type = frame->gpr[BE_R4_GPR_A0];
	be_u64 reason = frame->gpr[BE_R4_GPR_A1];

	if (fid != BE_B5_SBI_SRST_SYSTEM_RESET)
		sbi_return(result, BE_B5_ACTION_RETURN,
			   BE_B5_SBI_ERR_NOT_SUPPORTED, 0U);
	else if (type > BE_B5_SRST_TYPE_WARM_REBOOT ||
		 reason > BE_B5_SRST_REASON_FAILURE)
		sbi_return(result, BE_B5_ACTION_RETURN,
			   BE_B5_SBI_ERR_INVALID_PARAM, 0U);
	else if (type != BE_B5_SRST_TYPE_SHUTDOWN)
		sbi_return(result, BE_B5_ACTION_RETURN,
			   BE_B5_SBI_ERR_NOT_SUPPORTED, 0U);
	else if (reason == BE_B5_SRST_REASON_NONE) {
		state->phase = BE_B5_PHASE_SHUTDOWN;
		sbi_return(result, BE_B5_ACTION_SHUTDOWN, BE_B5_SBI_SUCCESS,
			   0U);
	} else {
		result->failure = be_b5_fail(state, BE_B5_CLASS_GUEST_FAILURE);
		sbi_return(result, BE_B5_ACTION_GUEST_FAILURE,
			   BE_B5_SBI_SUCCESS, 0U);
	}
}

enum be_b5_action be_b5_handle_exit(struct be_b5_state *state,
				    const struct be_r2_leaf_set *leaves,
				    const struct be_r4_frame *frame,
				    struct be_b5_result *result)
{
	enum be_b5_class failure;
	be_u64 eid;
	be_u64 fid;

	if (result == (struct be_b5_result *)0) {
		(void)be_b5_fail(state, BE_B5_CLASS_EXCEPTION);
		return BE_B5_ACTION_TERMINAL;
	}
	*result = (struct be_b5_result){ 0 };
	if (state == (struct be_b5_state *)0 ||
	    leaves == (const struct be_r2_leaf_set *)0 ||
	    frame == (const struct be_r4_frame *)0 ||
	    state->phase != BE_B5_PHASE_RUNNING)
		return terminal(state, result, BE_B5_CLASS_EXCEPTION);
	if (state->exits >= BE_B5_EXIT_BUDGET) {
		state->exits = BE_B5_EXIT_BUDGET + 1U;
		return terminal(state, result, BE_B5_CLASS_EXIT_BUDGET);
	}
	++state->exits;
	if (frame->reserved != 0U)
		return terminal(state, result, BE_B5_CLASS_EXCEPTION);
	failure = be_b5_classify_cause(frame->scause);
	if (failure != BE_B5_CLASS_NONE)
		return terminal(state, result, failure);
	if (frame->sepc > ~BE_U64_C(0) - BE_B5_INSTRUCTION_SIZE)
		return terminal(state, result, BE_B5_CLASS_RESUME);
	result->resume_pc = frame->sepc + BE_B5_INSTRUCTION_SIZE;

	eid = frame->gpr[BE_R4_GPR_A7];
	fid = frame->gpr[BE_R4_GPR_A6];
	if (eid == BE_B5_SBI_EID_BASE)
		sbi_base(fid, frame->gpr[BE_R4_GPR_A0], result);
	else if (eid == BE_B5_SBI_EID_TIME &&
		 fid == BE_B5_SBI_TIME_SET_TIMER) {
		result->timer = frame->gpr[BE_R4_GPR_A0];
		sbi_return(result, BE_B5_ACTION_SET_TIMER, BE_B5_SBI_SUCCESS,
			   0U);
	} else if (eid == BE_B5_SBI_EID_DBCN)
		sbi_dbcn(leaves, fid, frame, result);
	else if (eid == BE_B5_SBI_EID_SRST)
		sbi_srst(state, fid, frame, result);
	else
		sbi_return(result, BE_B5_ACTION_RETURN,
			   BE_B5_SBI_ERR_NOT_SUPPORTED, 0U);
	return result->action;
}

void be_b5_apply_return(struct be_r4_frame *frame,
			const struct be_b5_result *result)
{
	if (frame == (struct be_r4_frame *)0 ||
	    result == (const struct be_b5_result *)0)
		return;
	frame->gpr[BE_R4_GPR_A0] = (be_u64)result->error;
	frame->gpr[BE_R4_GPR_A1] = result->value;
	frame->sepc = result->resume_pc;
}

be_u64 be_b5_console_tag(struct be_b5_console *console, const be_u8 *input,
			 be_u64 length, char *output, be_u64 capacity)
{
	static const char prefix[] = BE_B5_GUEST_PREFIX;
	be_u64 used = 0U;
	be_u64 index;
	be_u64 offset;

	if (console == (struct be_b5_console *)0 ||
	    input == (const be_u8 *)0 || output == (char *)0 ||
	    length > BE_B5_DBCN_MAX_BYTES || capacity < BE_B5_TAGGED_CAPACITY)
		return BE_B5_TAG_INVALID;
	for (index = 0U; index < length; ++index) {
		be_u8 byte = input[index];

		if (console->line_open == 0U) {
			for (offset = 0U; offset < BE_B5_GUEST_PREFIX_LENGTH;
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

be_u32 be_b5_console_close(struct be_b5_console *console)
{
	if (console == (struct be_b5_console *)0 || console->line_open == 0U)
		return 0U;
	console->line_open = 0U;
	return 1U;
}

void be_b5_line_reset(struct be_b5_line *line)
{
	if (line == (struct be_b5_line *)0)
		return;
	line->length = 0U;
	line->overflow = 0U;
}

static void line_byte(struct be_b5_line *line, char byte)
{
	if (line->overflow != 0U || line->length >= BE_B5_LINE_CAPACITY) {
		line->overflow = 1U;
		return;
	}
	line->text[line->length++] = byte;
}

void be_b5_line_text(struct be_b5_line *line, const char *text)
{
	be_u64 index;

	if (line == (struct be_b5_line *)0)
		return;
	if (text == (const char *)0) {
		line->overflow = 1U;
		return;
	}
	for (index = 0U; index <= BE_B5_LINE_CAPACITY && text[index] != '\0';
	     ++index)
		line_byte(line, text[index]);
}

void be_b5_line_hex(struct be_b5_line *line, be_u64 value)
{
	static const char digits[] = "0123456789abcdef";
	unsigned int shift = 60U;

	if (line == (struct be_b5_line *)0)
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

void be_b5_line_decimal(struct be_b5_line *line, be_u64 value)
{
	char digits[20];
	unsigned int count = 0U;

	if (line == (struct be_b5_line *)0)
		return;
	do {
		digits[count++] = (char)('0' + (int)(value % 10U));
		value /= 10U;
	} while (value != 0U && count < sizeof(digits));
	while (count > 0U)
		line_byte(line, digits[--count]);
}
