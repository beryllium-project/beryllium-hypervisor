// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B7 guest SBI core: exit classification (SBI, idling wfi,
 *          HS slice), each guest's exit ceiling and the run's guest-time
 *          budget, per-guest counters, the bounded SBI subset, the DBCN
 *          window check, the per-guest line console, the vCPU record and
 *          CSR-set logic of a switch, the guest-control checks, and the
 *          monitor line builder.
 * Trust:   restricted C with explicit bounded loops. No CSR, SBI call, I/O,
 *          or guest-address dereference: the runtime performs each action.
 * Scope:   B7 only (planning/k3-b7-plan.md); see b7.h.
 */
#include "b7.h"

_Static_assert(BE_B7_CONSOLE_CAPACITY <= BE_PAGE_SIZE,
	       "one console feed must fit the HS diagnostic page");
_Static_assert(sizeof(BE_B7_G0_PREFIX) - 1U == BE_B7_GUEST_PREFIX_LENGTH &&
	       sizeof(BE_B7_G1_PREFIX) - 1U == BE_B7_GUEST_PREFIX_LENGTH,
	       "guest prefix length differs");
_Static_assert(BE_B7_HSTATUS_GUEST_CONTROLS == BE_U64_C(0x200180),
	       "hstatus guest controls are VTW, SPV, and SPVP");
_Static_assert(BE_B7_HSTATUS_RESUME_MASK == BE_U64_C(0x73f280) &&
	       BE_B7_HSTATUS_RESUME_CONTROLS == BE_U64_C(0x200080),
	       "hstatus resume controls are VTW and SPV, SPVP masked out");
_Static_assert(BE_B7_SSTATUS_CONTROL_MASK == BE_U64_C(0xde722),
	       "sstatus guest mask is R3's plus VS");
_Static_assert(sizeof(struct be_b7_exit) == 352U,
	       "the exit record is the accepted frame and four words");
_Static_assert(BE_B7_VCSR_COUNT == 11U, "the per-guest CSR set has 11 words");
_Static_assert(BE_B7_SBI_IMPL_VERSION == 3U, "B7 is SBI implementation 3");

static const char *const be_b7_class_names[BE_B7_CLASS_COUNT] = {
	[BE_B7_CLASS_NONE] = "none",
	[BE_B7_CLASS_BOOT] = "boot",
	[BE_B7_CLASS_GSTAGE] = "gstage",
	[BE_B7_CLASS_SSTC] = "sstc",
	[BE_B7_CLASS_CONTROLS] = "controls",
	[BE_B7_CLASS_PAYLOAD] = "payload",
	[BE_B7_CLASS_INTERRUPT] = "interrupt",
	[BE_B7_CLASS_GUEST_PAGE_FAULT] = "guest-page-fault",
	[BE_B7_CLASS_VIRTUAL_INSTRUCTION] = "virtual-instruction",
	[BE_B7_CLASS_ACCESS_FAULT] = "access-fault",
	[BE_B7_CLASS_ILLEGAL_INSTRUCTION] = "illegal-instruction",
	[BE_B7_CLASS_EXCEPTION] = "exception",
	[BE_B7_CLASS_EXIT_BUDGET] = "exit-budget",
	[BE_B7_CLASS_GUEST_TIMEOUT] = "guest-timeout",
	[BE_B7_CLASS_RESUME] = "resume",
	[BE_B7_CLASS_CONSOLE] = "console",
	[BE_B7_CLASS_GUEST_FAILURE] = "guest-failure",
	[BE_B7_CLASS_GUEST_REBOOT] = "guest-reboot",
	[BE_B7_CLASS_SHUTDOWN_RETURNED] = "shutdown-returned",
	[BE_B7_CLASS_SWITCH] = "switch",
	[BE_B7_CLASS_SCHEDULER] = "scheduler",
};

static const char *const be_b7_vcsr_names[BE_B7_VCSR_COUNT] = {
	[BE_B7_VCSR_VSSTATUS] = "vsstatus",
	[BE_B7_VCSR_VSIE] = "vsie",
	[BE_B7_VCSR_VSTVEC] = "vstvec",
	[BE_B7_VCSR_VSSCRATCH] = "vsscratch",
	[BE_B7_VCSR_VSEPC] = "vsepc",
	[BE_B7_VCSR_VSCAUSE] = "vscause",
	[BE_B7_VCSR_VSTVAL] = "vstval",
	[BE_B7_VCSR_VSATP] = "vsatp",
	[BE_B7_VCSR_VSTIMECMP] = "vstimecmp",
	[BE_B7_VCSR_SCOUNTEREN] = "scounteren",
	[BE_B7_VCSR_SENVCFG] = "senvcfg",
};

const char *be_b7_class_name(enum be_b7_class failure)
{
	if ((unsigned int)failure >= (unsigned int)BE_B7_CLASS_COUNT)
		return "invalid";
	return be_b7_class_names[failure];
}

enum be_b7_class be_b7_stce_class(be_u64 henvcfg)
{
	if ((henvcfg & BE_B7_HENVCFG_STCE) == 0U)
		return BE_B7_CLASS_SSTC;
	if (henvcfg != BE_B7_HENVCFG_STCE)
		return BE_B7_CLASS_CONTROLS;
	return BE_B7_CLASS_NONE;
}

int be_b7_controls_valid(const struct be_b7_controls *controls,
			 be_u64 expected_hgatp, be_u64 trusted_top)
{
	if (controls == (const struct be_b7_controls *)0)
		return 0;
	return controls->hip == 0U &&
	       (controls->hstatus & BE_R3_HSTATUS_CONTROL_MASK) ==
		       BE_B7_HSTATUS_GUEST_CONTROLS &&
	       controls->hedeleg == (controls->hedeleg & BE_B7_HEDELEG) &&
	       (controls->hedeleg & BE_B7_HEDELEG_REQUIRED) ==
		       BE_B7_HEDELEG_REQUIRED &&
	       controls->hideleg == BE_B7_HIDELEG_VSTI &&
	       controls->hie == 0U &&
	       (controls->hvip & BE_B7_HVIP_VS_BITS) == 0U &&
	       controls->hcounteren == BE_B7_HCOUNTEREN_TM &&
	       controls->htimedelta == 0U &&
	       controls->henvcfg == BE_B7_HENVCFG_STCE &&
	       controls->hgeie == 0U &&
	       controls->vstimecmp == BE_B7_VSTIMECMP_DISARMED &&
	       controls->sie == BE_B7_SIE_STIE &&
	       (controls->sstatus & BE_B7_SSTATUS_CONTROL_MASK) == 0U &&
	       controls->hgatp == expected_hgatp && controls->vsatp == 0U &&
	       controls->sscratch == trusted_top;
}

enum be_b7_class be_b7_classify_cause(be_u64 scause)
{
	if ((scause & BE_B7_SCAUSE_INTERRUPT) != 0U)
		return BE_B7_CLASS_INTERRUPT;
	switch (scause) {
	case BE_B7_SCAUSE_VS_ECALL:
		return BE_B7_CLASS_NONE;
	case BE_B7_SCAUSE_FETCH_GUEST_PAGE_FAULT:
	case BE_B7_SCAUSE_LOAD_GUEST_PAGE_FAULT:
	case BE_B7_SCAUSE_STORE_GUEST_PAGE_FAULT:
		return BE_B7_CLASS_GUEST_PAGE_FAULT;
	case BE_B7_SCAUSE_VIRTUAL_INSTRUCTION:
		return BE_B7_CLASS_VIRTUAL_INSTRUCTION;
	case BE_B7_SCAUSE_FETCH_ACCESS_FAULT:
	case BE_B7_SCAUSE_LOAD_ACCESS_FAULT:
	case BE_B7_SCAUSE_STORE_ACCESS_FAULT:
		return BE_B7_CLASS_ACCESS_FAULT;
	case BE_B7_SCAUSE_ILLEGAL_INSTRUCTION:
		return BE_B7_CLASS_ILLEGAL_INSTRUCTION;
	default:
		return BE_B7_CLASS_EXCEPTION;
	}
}

enum be_b7_class be_b7_fail(struct be_b7_state *state,
			    enum be_b7_class failure)
{
	if (failure == BE_B7_CLASS_NONE ||
	    (unsigned int)failure >= (unsigned int)BE_B7_CLASS_COUNT)
		failure = BE_B7_CLASS_EXCEPTION;
	if (state == (struct be_b7_state *)0)
		return failure;
	if (state->phase == BE_B7_PHASE_FAILED)
		return state->failure;
	state->phase = BE_B7_PHASE_FAILED;
	state->failure = failure;
	return failure;
}

static enum be_b7_action terminal(struct be_b7_state *state,
				  struct be_b7_result *result,
				  enum be_b7_class failure)
{
	result->action = BE_B7_ACTION_TERMINAL;
	result->failure = be_b7_fail(state, failure);
	return result->action;
}

static void sbi_return(struct be_b7_result *result, enum be_b7_action action,
		       long error, be_u64 value)
{
	result->action = action;
	result->error = error;
	result->value = value;
}

static int probe_available(be_u64 eid)
{
	return eid == BE_B7_SBI_EID_BASE || eid == BE_B7_SBI_EID_TIME ||
	       eid == BE_B7_SBI_EID_DBCN || eid == BE_B7_SBI_EID_SRST;
}

static void sbi_base(be_u64 fid, be_u64 argument0,
		     struct be_b7_result *result)
{
	if (fid == BE_B7_SBI_BASE_GET_SPEC_VERSION)
		sbi_return(result, BE_B7_ACTION_RETURN, BE_B7_SBI_SUCCESS,
			   BE_B7_SBI_SPEC_VERSION);
	else if (fid == BE_B7_SBI_BASE_GET_IMPL_ID)
		sbi_return(result, BE_B7_ACTION_RETURN, BE_B7_SBI_SUCCESS,
			   BE_B7_SBI_IMPL_ID);
	else if (fid == BE_B7_SBI_BASE_GET_IMPL_VERSION)
		sbi_return(result, BE_B7_ACTION_RETURN, BE_B7_SBI_SUCCESS,
			   BE_B7_SBI_IMPL_VERSION);
	else if (fid == BE_B7_SBI_BASE_PROBE_EXTENSION)
		sbi_return(result, BE_B7_ACTION_RETURN, BE_B7_SBI_SUCCESS,
			   probe_available(argument0) ? 1U : 0U);
	else if (fid == BE_B7_SBI_BASE_GET_MVENDORID ||
		 fid == BE_B7_SBI_BASE_GET_MARCHID ||
		 fid == BE_B7_SBI_BASE_GET_MIMPID)
		sbi_return(result, BE_B7_ACTION_RETURN, BE_B7_SBI_SUCCESS, 0U);
	else
		sbi_return(result, BE_B7_ACTION_RETURN,
			   BE_B7_SBI_ERR_NOT_SUPPORTED, 0U);
}

static void sbi_dbcn(const struct be_b7_gstage_map *map, be_u64 fid,
		     const struct be_r4_frame *frame,
		     struct be_b7_result *result)
{
	be_u64 length = frame->gpr[BE_R4_GPR_A0];
	be_u64 address = frame->gpr[BE_R4_GPR_A1];
	be_u64 address_high = frame->gpr[BE_B7_GPR_A2];

	if (fid == BE_B7_SBI_DBCN_WRITE) {
		if (address_high != 0U)
			sbi_return(result, BE_B7_ACTION_RETURN,
				   BE_B7_SBI_ERR_INVALID_PARAM, 0U);
		else if (length == 0U)
			sbi_return(result, BE_B7_ACTION_RETURN,
				   BE_B7_SBI_SUCCESS, 0U);
		else if (!be_b7_gstage_translate(map, address, length,
						 &result->source_pa))
			sbi_return(result, BE_B7_ACTION_RETURN,
				   BE_B7_SBI_ERR_INVALID_PARAM, 0U);
		else {
			result->length = length < BE_B7_DBCN_MAX_BYTES ?
				length : BE_B7_DBCN_MAX_BYTES;
			sbi_return(result, BE_B7_ACTION_CONSOLE_WRITE,
				   BE_B7_SBI_SUCCESS, result->length);
		}
	} else if (fid == BE_B7_SBI_DBCN_READ) {
		sbi_return(result, BE_B7_ACTION_RETURN, BE_B7_SBI_ERR_DENIED,
			   0U);
	} else if (fid == BE_B7_SBI_DBCN_WRITE_BYTE) {
		result->byte = (be_u8)(length & 0xffU);
		sbi_return(result, BE_B7_ACTION_CONSOLE_BYTE, BE_B7_SBI_SUCCESS,
			   0U);
	} else {
		sbi_return(result, BE_B7_ACTION_RETURN,
			   BE_B7_SBI_ERR_NOT_SUPPORTED, 0U);
	}
}

static void sbi_srst(struct be_b7_state *state, be_u32 guest, be_u64 fid,
		     const struct be_r4_frame *frame,
		     struct be_b7_result *result)
{
	be_u64 type = frame->gpr[BE_R4_GPR_A0];
	be_u64 reason = frame->gpr[BE_R4_GPR_A1];

	if (fid != BE_B7_SBI_SRST_SYSTEM_RESET)
		sbi_return(result, BE_B7_ACTION_RETURN,
			   BE_B7_SBI_ERR_NOT_SUPPORTED, 0U);
	else if (type > BE_B7_SRST_TYPE_WARM_REBOOT ||
		 reason > BE_B7_SRST_REASON_FAILURE)
		sbi_return(result, BE_B7_ACTION_RETURN,
			   BE_B7_SBI_ERR_INVALID_PARAM, 0U);
	else if (type != BE_B7_SRST_TYPE_SHUTDOWN) {
		/* A reboot request (panic=-1 included) ends the run. */
		result->failure = be_b7_fail(state, BE_B7_CLASS_GUEST_REBOOT);
		sbi_return(result, BE_B7_ACTION_GUEST_REBOOT,
			   BE_B7_SBI_SUCCESS, 0U);
	} else if (reason == BE_B7_SRST_REASON_NONE) {
		/* Only the calling guest stops; the run goes on. */
		state->guest[guest].phase = BE_B7_PHASE_STOPPED;
		sbi_return(result, BE_B7_ACTION_STOP, BE_B7_SBI_SUCCESS, 0U);
	} else {
		result->failure = be_b7_fail(state, BE_B7_CLASS_GUEST_FAILURE);
		sbi_return(result, BE_B7_ACTION_GUEST_FAILURE,
			   BE_B7_SBI_SUCCESS, 0U);
	}
}

/* Each accepted ecall adds one to exactly one call class. */
static void count_call(struct be_b7_counts *counts, be_u64 eid, be_u64 fid,
		       const struct be_b7_result *result)
{
	if (result->error == BE_B7_SBI_ERR_NOT_SUPPORTED ||
	    result->error == BE_B7_SBI_ERR_INVALID_PARAM)
		++counts->refused;
	else if (eid == BE_B7_SBI_EID_BASE)
		++counts->base;
	else if (eid == BE_B7_SBI_EID_TIME)
		++counts->time;
	else if (eid == BE_B7_SBI_EID_SRST)
		++counts->srst;
	else if (fid == BE_B7_SBI_DBCN_WRITE)
		++counts->dbcn_write;
	else if (fid == BE_B7_SBI_DBCN_READ)
		++counts->dbcn_read;
	else
		++counts->dbcn_byte;
}

enum be_b7_action be_b7_handle_exit(struct be_b7_state *state, be_u32 guest,
				    const struct be_b7_gstage_map *map,
				    const struct be_b7_exit *record,
				    struct be_b7_result *result)
{
	const struct be_r4_frame *frame;
	struct be_b7_counts *counts;
	enum be_b7_class failure;
	be_u64 eid;
	be_u64 fid;

	if (result == (struct be_b7_result *)0) {
		(void)be_b7_fail(state, BE_B7_CLASS_EXCEPTION);
		return BE_B7_ACTION_TERMINAL;
	}
	*result = (struct be_b7_result){ 0 };
	if (state == (struct be_b7_state *)0 ||
	    map == (const struct be_b7_gstage_map *)0 ||
	    record == (const struct be_b7_exit *)0 || guest >= BE_B7_GUESTS ||
	    state->phase != BE_B7_PHASE_RUNNING ||
	    state->guest[guest].phase != BE_B7_PHASE_RUNNING)
		return terminal(state, result, BE_B7_CLASS_EXCEPTION);
	counts = &state->guest[guest].counts;
	if (counts->exits >= state->exit_ceiling) {
		counts->exits = state->exit_ceiling + 1U;
		return terminal(state, result, BE_B7_CLASS_EXIT_BUDGET);
	}
	++counts->exits;
	if (record->time - state->entry_time >= state->time_budget)
		return terminal(state, result, BE_B7_CLASS_GUEST_TIMEOUT);
	frame = &record->frame;
	if (frame->reserved != 0U || (record->hstatus & BE_B7_HSTATUS_SPV) == 0U)
		return terminal(state, result, BE_B7_CLASS_EXCEPTION);
	if (frame->scause == BE_B7_SCAUSE_SUPERVISOR_TIMER) {
		++counts->slice;
		result->resume_pc = frame->sepc;
		result->action = BE_B7_ACTION_SLICE;
		return result->action;
	}
	/* Only a VS-mode wfi idles; a VU wfi or another stval is terminal. */
	if (frame->scause == BE_B7_SCAUSE_VIRTUAL_INSTRUCTION &&
	    frame->stval == BE_B7_WFI_INSTRUCTION &&
	    (record->hstatus & BE_B7_HSTATUS_SPVP) != 0U) {
		if (frame->sepc > ~BE_U64_C(0) - BE_B7_INSTRUCTION_SIZE)
			return terminal(state, result, BE_B7_CLASS_RESUME);
		++counts->wfi;
		result->resume_pc = frame->sepc + BE_B7_INSTRUCTION_SIZE;
		result->action = BE_B7_ACTION_WFI;
		return result->action;
	}
	failure = be_b7_classify_cause(frame->scause);
	if (failure != BE_B7_CLASS_NONE)
		return terminal(state, result, failure);
	if (frame->sepc > ~BE_U64_C(0) - BE_B7_INSTRUCTION_SIZE)
		return terminal(state, result, BE_B7_CLASS_RESUME);
	result->resume_pc = frame->sepc + BE_B7_INSTRUCTION_SIZE;

	eid = frame->gpr[BE_R4_GPR_A7];
	fid = frame->gpr[BE_R4_GPR_A6];
	if (eid == BE_B7_SBI_EID_BASE)
		sbi_base(fid, frame->gpr[BE_R4_GPR_A0], result);
	else if (eid == BE_B7_SBI_EID_TIME &&
		 fid == BE_B7_SBI_TIME_SET_TIMER) {
		result->timer = frame->gpr[BE_R4_GPR_A0];
		sbi_return(result, BE_B7_ACTION_SET_TIMER, BE_B7_SBI_SUCCESS,
			   0U);
	} else if (eid == BE_B7_SBI_EID_DBCN)
		sbi_dbcn(map, fid, frame, result);
	else if (eid == BE_B7_SBI_EID_SRST)
		sbi_srst(state, guest, fid, frame, result);
	else
		sbi_return(result, BE_B7_ACTION_RETURN,
			   BE_B7_SBI_ERR_NOT_SUPPORTED, 0U);
	count_call(counts, eid, fid, result);
	return result->action;
}

be_u64 be_b7_counts_sbi(const struct be_b7_counts *counts)
{
	if (counts == (const struct be_b7_counts *)0)
		return 0U;
	return counts->base + counts->time + counts->dbcn_write +
	       counts->dbcn_read + counts->dbcn_byte + counts->srst +
	       counts->refused;
}

void be_b7_apply_return(struct be_r4_frame *frame,
			const struct be_b7_result *result)
{
	if (frame == (struct be_r4_frame *)0 ||
	    result == (const struct be_b7_result *)0)
		return;
	switch (result->action) {
	case BE_B7_ACTION_RETURN:
	case BE_B7_ACTION_CONSOLE_WRITE:
	case BE_B7_ACTION_CONSOLE_BYTE:
	case BE_B7_ACTION_SET_TIMER:
		frame->gpr[BE_R4_GPR_A0] = (be_u64)result->error;
		frame->gpr[BE_R4_GPR_A1] = result->value;
		frame->sepc = result->resume_pc;
		break;
	case BE_B7_ACTION_WFI:
		frame->sepc = result->resume_pc;
		break;
	default:
		break;
	}
}

void be_b7_entry_frame(struct be_b7_exit *record, be_u64 pc, be_u64 hart,
		       be_u64 dtb)
{
	if (record == (struct be_b7_exit *)0)
		return;
	*record = (struct be_b7_exit){ 0 };
	record->frame.sepc = pc;
	record->frame.gpr[BE_R4_GPR_A0] = hart;
	record->frame.gpr[BE_R4_GPR_A1] = dtb;
	record->hstatus = BE_B7_HSTATUS_SPV | BE_B7_HSTATUS_SPVP;
}

be_u64 be_b7_record_spp(const struct be_b7_exit *record)
{
	if (record == (const struct be_b7_exit *)0 ||
	    (record->hstatus & BE_B7_HSTATUS_SPVP) == 0U)
		return 0U;
	return BE_B7_SSTATUS_SPP;
}

void be_b7_vcsr_initial(be_u64 *csr)
{
	be_u32 index;

	if (csr == (be_u64 *)0)
		return;
	for (index = 0U; index < BE_B7_VCSR_COUNT; ++index)
		csr[index] = 0U;
	csr[BE_B7_VCSR_VSSTATUS] = BE_B7_VSSTATUS_UXL64;
	csr[BE_B7_VCSR_VSTIMECMP] = BE_B7_VSTIMECMP_DISARMED;
}

void be_b7_vcpu_init(struct be_b7_vcpu *vcpu, be_u64 pc, be_u64 hart,
		     be_u64 dtb)
{
	if (vcpu == (struct be_b7_vcpu *)0)
		return;
	be_b7_entry_frame(&vcpu->record, pc, hart, dtb);
	be_b7_vcsr_initial(vcpu->csr);
}

void be_b7_vcpu_save(struct be_b7_vcpu *vcpu, const struct be_b7_exit *record)
{
	if (vcpu == (struct be_b7_vcpu *)0 ||
	    record == (const struct be_b7_exit *)0)
		return;
	vcpu->record = *record;
}

void be_b7_vcpu_restore(const struct be_b7_vcpu *vcpu,
			struct be_b7_exit *record)
{
	if (vcpu == (const struct be_b7_vcpu *)0 ||
	    record == (struct be_b7_exit *)0)
		return;
	*record = vcpu->record;
}

be_u32 be_b7_vcsr_mismatch(const be_u64 *expected, const be_u64 *readback)
{
	be_u32 index;

	if (expected == (const be_u64 *)0 || readback == (const be_u64 *)0)
		return 0U;
	for (index = 0U; index < BE_B7_VCSR_COUNT; ++index)
		if (readback[index] != expected[index])
			return index;
	return BE_B7_VCSR_COUNT;
}

const char *be_b7_vcsr_name(be_u32 index)
{
	if (index >= BE_B7_VCSR_COUNT)
		return "invalid";
	return be_b7_vcsr_names[index];
}

const char *be_b7_guest_prefix(be_u32 guest)
{
	if (guest == 0U)
		return BE_B7_G0_PREFIX;
	if (guest == 1U)
		return BE_B7_G1_PREFIX;
	return (const char *)0;
}

/* One ended line: the prefix, the buffered bytes, and LF; then empty. */
static be_u64 emit_line(struct be_b7_console *console, const char *prefix,
			char *output, be_u64 used)
{
	be_u64 index;

	for (index = 0U; index < BE_B7_GUEST_PREFIX_LENGTH; ++index)
		output[used++] = prefix[index];
	for (index = 0U; index < console->length; ++index)
		output[used++] = console->text[index];
	output[used++] = '\n';
	console->length = 0U;
	return used;
}

be_u64 be_b7_console_feed(struct be_b7_console *console, be_u32 guest,
			  const be_u8 *input, be_u64 length, char *output,
			  be_u64 capacity)
{
	const char *prefix = be_b7_guest_prefix(guest);
	be_u64 used = 0U;
	be_u64 index;

	if (console == (struct be_b7_console *)0 ||
	    input == (const be_u8 *)0 || output == (char *)0 ||
	    prefix == (const char *)0 || length > BE_B7_DBCN_MAX_BYTES ||
	    capacity < BE_B7_CONSOLE_CAPACITY ||
	    console->length > BE_B7_CONSOLE_LINE_BYTES)
		return BE_B7_CONSOLE_INVALID;
	for (index = 0U; index < length; ++index) {
		be_u8 byte = input[index];

		/* hvc sends CR before LF; CR is dropped, not shown. */
		if (byte == (be_u8)'\r')
			continue;
		if (byte == (be_u8)'\n') {
			used = emit_line(console, prefix, output, used);
			continue;
		}
		/* A full buffer is written as its own line. */
		if (console->length == BE_B7_CONSOLE_LINE_BYTES)
			used = emit_line(console, prefix, output, used);
		console->text[console->length++] =
			byte >= 0x20U && byte <= 0x7eU ? (char)byte : '?';
	}
	return used;
}

be_u64 be_b7_console_flush(struct be_b7_console *console, be_u32 guest,
			   char *output, be_u64 capacity)
{
	const char *prefix = be_b7_guest_prefix(guest);

	if (console == (struct be_b7_console *)0 || output == (char *)0 ||
	    prefix == (const char *)0 || capacity < BE_B7_CONSOLE_CAPACITY ||
	    console->length > BE_B7_CONSOLE_LINE_BYTES)
		return BE_B7_CONSOLE_INVALID;
	if (console->length == 0U)
		return 0U;
	return emit_line(console, prefix, output, 0U);
}

void be_b7_line_reset(struct be_b7_line *line)
{
	if (line == (struct be_b7_line *)0)
		return;
	line->length = 0U;
	line->overflow = 0U;
}

static void line_byte(struct be_b7_line *line, char byte)
{
	if (line->overflow != 0U || line->length >= BE_B7_LINE_CAPACITY) {
		line->overflow = 1U;
		return;
	}
	line->text[line->length++] = byte;
}

void be_b7_line_text(struct be_b7_line *line, const char *text)
{
	be_u64 index;

	if (line == (struct be_b7_line *)0)
		return;
	if (text == (const char *)0) {
		line->overflow = 1U;
		return;
	}
	for (index = 0U; index <= BE_B7_LINE_CAPACITY && text[index] != '\0';
	     ++index)
		line_byte(line, text[index]);
}

void be_b7_line_hex(struct be_b7_line *line, be_u64 value)
{
	static const char digits[] = "0123456789abcdef";
	unsigned int shift = 60U;

	if (line == (struct be_b7_line *)0)
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

void be_b7_line_decimal(struct be_b7_line *line, be_u64 value)
{
	char digits[20];
	unsigned int count = 0U;

	if (line == (struct be_b7_line *)0)
		return;
	do {
		digits[count++] = (char)('0' + (int)(value % 10U));
		value /= 10U;
	} while (value != 0U && count < sizeof(digits));
	while (count > 0U)
		line_byte(line, digits[--count]);
}
