// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP guest SBI core: exit classification (SBI and the IPI), each
 *          domain's exit ceiling, per-hart counters, the bounded SBI
 *          subset, the DBCN window check, the per-hart line console and its
 *          LINE records, the IPI's PING and PONG, the denial entry's
 *          decision over the hart's walked pages and its injected values
 *          (planning/mvp-m1-plan.md, "The denial path"), the management
 *          extension (planning/mvp-m2-plan.md, "The management extension"):
 *          the domain hart's call and the records it takes while it waits,
 *          paused, or terminated, and hart 0's decision; since M7 the
 *          console read a domain whose sealed configuration grants console
 *          input is served, under the DBCN window check, and a paused or
 *          terminated domain's last partial line (planning/mvp-m7-plan.md,
 *          D-1 and Q9); the READY,
 *          ENTERED, SHUTDOWN, FAIL, DENIAL, and MGMT_REQUEST records, a
 *          failed domain hart's wait for hart 0's ACK (Q10, as Plan
 *          revision M1-B revises it), the per-domain CSR set written once
 *          at arming, the guest-control checks, the firmware HSM and IPI
 *          result checks with BE_MVP:02's census of the other harts, and
 *          the monitor line builder.
 * Trust:   restricted C with explicit bounded loops. No CSR, SBI call, I/O,
 *          or guest-address dereference: the runtime performs each action,
 *          and records reach hart 0 only through a ring view.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, planning/mvp-m1-plan.md,
 *          and planning/mvp-m2-plan.md); see mvp.h.
 */
#include "mvp.h"
#include "mvp-ring.h"
#include "mvp-sbi.h"

_Static_assert(sizeof(BE_MVP_G0_PREFIX) - 1U == BE_MVP_DOMAIN_PREFIX_LENGTH &&
	       sizeof(BE_MVP_G1_PREFIX) - 1U == BE_MVP_DOMAIN_PREFIX_LENGTH,
	       "domain prefix length differs");
_Static_assert(BE_MVP_PRINT_LINE_BYTES == 268U,
	       "a printed line is the prefix, 256 bytes, and LF");
_Static_assert(BE_MVP_HSTATUS_GUEST_CONTROLS == BE_U64_C(0x180),
	       "hstatus guest controls are SPV and SPVP, B6's value");
_Static_assert(BE_MVP_HSTATUS_RESUME_MASK == BE_U64_C(0x73f280) &&
	       BE_MVP_HSTATUS_RESUME_CONTROLS == BE_U64_C(0x80),
	       "hstatus resume controls are SPV, SPVP masked out");
_Static_assert(BE_MVP_SSTATUS_CONTROL_MASK == BE_U64_C(0xde722),
	       "sstatus guest mask is R3's plus VS");
_Static_assert(BE_MVP_SIE_SSIE == BE_U64_C(0x2) &&
	       BE_MVP_SIE_CONTROL == BE_U64_C(0x22),
	       "domain harts take SSIE; hart 0 SSIE and STIE");
_Static_assert(sizeof(struct be_mvp_exit) == 360U &&
	       sizeof(struct be_mvp_exit) <= BE_MVP_BLOCK_SAVED_BYTES,
	       "the exit record is the accepted frame and five words, inside "
	       "the saved page");
_Static_assert(__builtin_offsetof(struct be_mvp_exit, vsstatus) == 352U,
	       "the vector stores vsstatus at offset 352");
_Static_assert(BE_MVP_VCSR_COUNT == 11U, "the per-domain CSR set has 11 words");
_Static_assert(BE_MVP_SBI_IMPL_VERSION == 5U &&
	       BE_MVP_SBI_IMPL_VERSION_MGMT == 6U,
	       "the MVP is SBI implementation 5, and 6 in an image with the "
	       "management extension, since M7 serves DBCN read "
	       "(planning/mvp-m7-plan.md, D-10)");
_Static_assert(BE_MVP_SHUTDOWN_WORDS * 8U <= BE_MVP_RECORD_PAYLOAD_MAX &&
	       BE_MVP_READY_WORDS * 8U <= BE_MVP_RECORD_PAYLOAD_MAX &&
	       BE_MVP_FAIL_MAX_WORDS * 8U <= BE_MVP_RECORD_PAYLOAD_MAX &&
	       BE_MVP_DENIAL_WORDS * 8U <= BE_MVP_RECORD_PAYLOAD_MAX &&
	       BE_MVP_MGMT_REQUEST_WORDS * 8U <= BE_MVP_RECORD_PAYLOAD_MAX,
	       "every word record fits one payload");
_Static_assert(BE_MVP_PAUSED_WORDS == BE_MVP_TERMINATED_WORDS &&
	       BE_MVP_PAUSED_EXITS == BE_MVP_TERMINATED_EXITS &&
	       BE_MVP_PAUSED_BY == BE_MVP_TERMINATED_BY &&
	       BE_MVP_PAUSE_BY == BE_MVP_TERMINATE_BY &&
	       BE_MVP_PAUSE_WORDS == BE_MVP_TERMINATE_WORDS &&
	       BE_MVP_PAUSED_WORDS <= BE_MVP_PONG_WORDS,
	       "PAUSED and TERMINATED, and PAUSE and TERMINATE, share their "
	       "words, and one answer's buffer holds each");
_Static_assert(BE_MVP_MGMT_DELIVER > 0 &&
	       BE_MVP_SBI_ERR_INVALID_STATE < BE_MVP_SBI_SUCCESS,
	       "delivery is no SBI result");
_Static_assert(BE_MVP_RECORD_HEADER_BYTES + BE_MVP_DENIAL_WORDS * 8U == 112U,
	       "a DENIAL record is 112 bytes with its header");
_Static_assert(BE_MVP_HSTATUS_GVA == BE_U64_C(0x40) &&
	       BE_MVP_VSSTATUS_SIE == BE_U64_C(0x2) &&
	       BE_MVP_VSSTATUS_SPIE == BE_U64_C(0x20) &&
	       BE_MVP_VSSTATUS_SPP == BE_U64_C(0x100),
	       "hstatus.GVA and vsstatus SIE, SPIE, and SPP");
_Static_assert(BE_MVP_HTVAL_LIMIT << BE_MVP_HTVAL_SHIFT ==
	       BE_MVP_GSTAGE_GPA_LIMIT,
	       "an htval below 2^39 is a GPA below Sv39x4's 2^41");
_Static_assert(BE_MVP_CONSOLE_LINE_BYTES == BE_MVP_RECORD_PAYLOAD_MAX,
	       "a full line buffer is one LINE record");

static const char *const be_mvp_class_names[BE_MVP_CLASS_COUNT] = {
	[BE_MVP_CLASS_NONE] = "none",
	[BE_MVP_CLASS_BOOT] = "boot",
	[BE_MVP_CLASS_GSTAGE] = "gstage",
	[BE_MVP_CLASS_SSTC] = "sstc",
	[BE_MVP_CLASS_CONTROLS] = "controls",
	[BE_MVP_CLASS_PAYLOAD] = "payload",
	[BE_MVP_CLASS_INTERRUPT] = "interrupt",
	[BE_MVP_CLASS_GUEST_PAGE_FAULT] = "guest-page-fault",
	[BE_MVP_CLASS_VIRTUAL_INSTRUCTION] = "virtual-instruction",
	[BE_MVP_CLASS_ACCESS_FAULT] = "access-fault",
	[BE_MVP_CLASS_ILLEGAL_INSTRUCTION] = "illegal-instruction",
	[BE_MVP_CLASS_EXCEPTION] = "exception",
	[BE_MVP_CLASS_EXIT_BUDGET] = "exit-budget",
	[BE_MVP_CLASS_RUN_TIMEOUT] = "run-timeout",
	[BE_MVP_CLASS_RESUME] = "resume",
	[BE_MVP_CLASS_CONSOLE] = "console",
	[BE_MVP_CLASS_GUEST_FAILURE] = "guest-failure",
	[BE_MVP_CLASS_GUEST_REBOOT] = "guest-reboot",
	[BE_MVP_CLASS_SHUTDOWN_RETURNED] = "shutdown-returned",
	[BE_MVP_CLASS_FIRMWARE] = "firmware",
	[BE_MVP_CLASS_HART_START] = "hart-start",
	[BE_MVP_CLASS_HART_READY] = "hart-ready",
	[BE_MVP_CLASS_RING] = "ring",
	[BE_MVP_CLASS_IPI] = "ipi",
	[BE_MVP_CLASS_MEASUREMENT] = "measurement",
	[BE_MVP_CLASS_MGMT] = "mgmt",
	[BE_MVP_CLASS_LOG] = "log",
};

static const char *const be_mvp_vcsr_names[BE_MVP_VCSR_COUNT] = {
	[BE_MVP_VCSR_VSSTATUS] = "vsstatus",
	[BE_MVP_VCSR_VSIE] = "vsie",
	[BE_MVP_VCSR_VSTVEC] = "vstvec",
	[BE_MVP_VCSR_VSSCRATCH] = "vsscratch",
	[BE_MVP_VCSR_VSEPC] = "vsepc",
	[BE_MVP_VCSR_VSCAUSE] = "vscause",
	[BE_MVP_VCSR_VSTVAL] = "vstval",
	[BE_MVP_VCSR_VSATP] = "vsatp",
	[BE_MVP_VCSR_VSTIMECMP] = "vstimecmp",
	[BE_MVP_VCSR_SCOUNTEREN] = "scounteren",
	[BE_MVP_VCSR_SENVCFG] = "senvcfg",
};

const char *be_mvp_class_name(enum be_mvp_class failure)
{
	if ((unsigned int)failure >= (unsigned int)BE_MVP_CLASS_COUNT)
		return "invalid";
	return be_mvp_class_names[failure];
}

enum be_mvp_class be_mvp_stce_class(be_u64 henvcfg)
{
	if ((henvcfg & BE_MVP_HENVCFG_STCE) == 0U)
		return BE_MVP_CLASS_SSTC;
	if (henvcfg != BE_MVP_HENVCFG_ARMED)
		return BE_MVP_CLASS_CONTROLS;
	return BE_MVP_CLASS_NONE;
}

int be_mvp_controls_valid(const struct be_mvp_controls *controls,
			  be_u64 expected_hgatp, be_u64 trusted_top)
{
	if (controls == (const struct be_mvp_controls *)0)
		return 0;
	return controls->hip == 0U &&
	       (controls->hstatus & BE_R3_HSTATUS_CONTROL_MASK) ==
		       BE_MVP_HSTATUS_GUEST_CONTROLS &&
	       controls->hedeleg == (controls->hedeleg & BE_MVP_HEDELEG) &&
	       (controls->hedeleg & BE_MVP_HEDELEG_REQUIRED) ==
		       BE_MVP_HEDELEG_REQUIRED &&
	       controls->hideleg == BE_MVP_HIDELEG_VSTI &&
	       controls->hie == 0U &&
	       (controls->hvip & BE_MVP_HVIP_VS_BITS) == 0U &&
	       controls->hcounteren == BE_MVP_HCOUNTEREN_TM &&
	       controls->htimedelta == 0U &&
	       controls->henvcfg == BE_MVP_HENVCFG_ARMED &&
	       controls->hgeie == 0U &&
	       controls->vstimecmp == BE_MVP_VSTIMECMP_DISARMED &&
	       controls->sie == BE_MVP_SIE_SSIE &&
	       (controls->sstatus & BE_MVP_SSTATUS_CONTROL_MASK) == 0U &&
	       controls->hgatp == expected_hgatp && controls->vsatp == 0U &&
	       controls->sscratch == trusted_top;
}

enum be_mvp_class be_mvp_classify_cause(be_u64 scause)
{
	if ((scause & BE_MVP_SCAUSE_INTERRUPT) != 0U)
		return BE_MVP_CLASS_INTERRUPT;
	switch (scause) {
	case BE_MVP_SCAUSE_VS_ECALL:
		return BE_MVP_CLASS_NONE;
	case BE_MVP_SCAUSE_FETCH_GUEST_PAGE_FAULT:
	case BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT:
	case BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT:
		return BE_MVP_CLASS_GUEST_PAGE_FAULT;
	case BE_MVP_SCAUSE_VIRTUAL_INSTRUCTION:
		return BE_MVP_CLASS_VIRTUAL_INSTRUCTION;
	case BE_MVP_SCAUSE_FETCH_ACCESS_FAULT:
	case BE_MVP_SCAUSE_LOAD_ACCESS_FAULT:
	case BE_MVP_SCAUSE_STORE_ACCESS_FAULT:
		return BE_MVP_CLASS_ACCESS_FAULT;
	case BE_MVP_SCAUSE_ILLEGAL_INSTRUCTION:
		return BE_MVP_CLASS_ILLEGAL_INSTRUCTION;
	default:
		return BE_MVP_CLASS_EXCEPTION;
	}
}

/* The access fault a guest-page fault is delivered as (Q5), or 0. */
static be_u64 access_fault(be_u64 scause)
{
	if (scause == BE_MVP_SCAUSE_FETCH_GUEST_PAGE_FAULT)
		return BE_MVP_SCAUSE_FETCH_ACCESS_FAULT;
	if (scause == BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT)
		return BE_MVP_SCAUSE_LOAD_ACCESS_FAULT;
	if (scause == BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT)
		return BE_MVP_SCAUSE_STORE_ACCESS_FAULT;
	return 0U;
}

/*
 * htinst: zero; or a transformed load (cause 21) or store or AMO (cause
 * 23), whose bit 0 is set and whose bits 6:2 are the major opcode. A
 * pseudoinstruction (bits 1:0 clear: an implicit VS-stage access), a
 * custom value, a fetch's nonzero value, and any other opcode are refused.
 */
static int htinst_accepted(be_u64 scause, be_u64 htinst)
{
	be_u64 opcode = (htinst >> BE_MVP_HTINST_OPCODE_SHIFT) &
			BE_MVP_HTINST_OPCODE_MASK;

	if (htinst == 0U)
		return 1;
	if (htinst >= BE_MVP_HTINST_LIMIT ||
	    (htinst & BE_MVP_HTINST_TRANSFORMED) == 0U)
		return 0;
	if (scause == BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT)
		return opcode == BE_MVP_OPCODE_LOAD;
	if (scause == BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT)
		return opcode == BE_MVP_OPCODE_STORE ||
		       opcode == BE_MVP_OPCODE_AMO;
	return 0;
}

static int inside(be_u64 address, be_u64 base, be_u64 bytes)
{
	return bytes != 0U && address >= base && address - base < bytes;
}

/* The walked leaf of the root's page that holds @gpa, or none. */
static const struct be_mvp_gstage_leaf *
leaf_at(const struct be_mvp_gstage_leaves *leaves, be_u64 gpa)
{
	be_u64 index;

	for (index = 0U; index < BE_MVP_PAGES_MAX; ++index)
		if (inside(gpa, leaves->page[index].gpa,
			   leaves->page[index].bytes))
			return &leaves->page[index];
	return (const struct be_mvp_gstage_leaf *)0;
}

int be_mvp_denial_decide(const struct be_mvp_state *state,
			 const struct be_mvp_gstage_map *map,
			 const struct be_mvp_gstage_leaves *leaves,
			 const struct be_mvp_exit *record,
			 struct be_mvp_denial *out)
{
	const struct be_r4_frame *frame;
	const struct be_mvp_gstage_leaf *leaf;
	be_u64 origin = BE_MVP_HSTATUS_SPV | BE_MVP_HSTATUS_SPVP |
			BE_MVP_HSTATUS_GVA;
	be_u64 vscause;
	be_u64 gpa;
	be_u64 kind;

	if (out == (struct be_mvp_denial *)0)
		return 0;
	*out = (struct be_mvp_denial){ 0 };
	if (state == (const struct be_mvp_state *)0 ||
	    map == (const struct be_mvp_gstage_map *)0 ||
	    leaves == (const struct be_mvp_gstage_leaves *)0 ||
	    record == (const struct be_mvp_exit *)0 ||
	    state->accept_denial != 1U || map->size == 0U)
		return 0;
	frame = &record->frame;
	vscause = access_fault(frame->scause);
	/* From VU mode, stval a guest virtual address; no alias bit. */
	if (vscause == 0U ||
	    (record->hstatus & origin) !=
		    (BE_MVP_HSTATUS_SPV | BE_MVP_HSTATUS_GVA) ||
	    frame->htval >= BE_MVP_HTVAL_LIMIT ||
	    !htinst_accepted(frame->scause, record->htinst) ||
	    (frame->vstvec & BE_MVP_VSTVEC_MODE_MASK) >
		    BE_MVP_VSTVEC_VECTORED)
		return 0;
	gpa = frame->htval << BE_MVP_HTVAL_SHIFT |
	      (frame->stval & BE_MVP_GPA_LOW_MASK);
	/* The place: no mapping, or a page whose leaf lacks W. */
	if (inside(gpa, map->gpa_base, map->size))
		return 0;
	leaf = leaf_at(leaves, gpa);
	if (leaf == (const struct be_mvp_gstage_leaf *)0)
		kind = BE_MVP_DENIAL_UNMAPPED;
	else if (frame->scause == BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT &&
		 (leaf->pte & BE_MVP_PTE_W) == 0U)
		kind = BE_MVP_DENIAL_READ_ONLY;
	else
		return 0;
	out->cause = frame->scause;
	out->kind = kind;
	out->gpa = gpa;
	out->htval = frame->htval;
	out->htinst = record->htinst;
	out->stval = frame->stval;
	out->sepc = frame->sepc;
	out->vsstatus = record->vsstatus;
	out->vstvec = frame->vstvec;
	out->time = record->time;
	/* The trap into VS mode the guest would take (Q5). */
	out->inject_vscause = vscause;
	out->inject_vstval = frame->stval;
	out->inject_vsepc = frame->sepc;
	out->inject_vsstatus = (record->vsstatus &
				~(BE_MVP_VSSTATUS_SPP | BE_MVP_VSSTATUS_SPIE |
				  BE_MVP_VSSTATUS_SIE)) |
			       ((record->hstatus & BE_MVP_HSTATUS_SPVP) != 0U ?
				BE_MVP_VSSTATUS_SPP : 0U) |
			       ((record->vsstatus & BE_MVP_VSSTATUS_SIE) != 0U ?
				BE_MVP_VSSTATUS_SPIE : 0U);
	out->resume_pc = frame->vstvec & ~BE_MVP_VSTVEC_MODE_MASK;
	return 1;
}

enum be_mvp_class be_mvp_fail(struct be_mvp_state *state,
			      enum be_mvp_class failure)
{
	if (failure == BE_MVP_CLASS_NONE ||
	    (unsigned int)failure >= (unsigned int)BE_MVP_CLASS_COUNT)
		failure = BE_MVP_CLASS_EXCEPTION;
	if (state == (struct be_mvp_state *)0)
		return failure;
	if (state->phase == BE_MVP_PHASE_FAILED)
		return state->failure;
	state->phase = BE_MVP_PHASE_FAILED;
	state->failure = failure;
	return failure;
}

static enum be_mvp_action terminal(struct be_mvp_state *state,
				   struct be_mvp_result *result,
				   enum be_mvp_class failure)
{
	result->action = BE_MVP_ACTION_TERMINAL;
	result->failure = be_mvp_fail(state, failure);
	return result->action;
}

static void sbi_return(struct be_mvp_result *result, enum be_mvp_action action,
		       long error, be_u64 value)
{
	result->action = action;
	result->error = error;
	result->value = value;
}

/* Whether the image accepts the management extension: exactly 1. */
static int accepts_mgmt(const struct be_mvp_state *state)
{
	return state->accept_mgmt == 1U;
}

/* Whether the sealed configuration grants the domain console input
 * (planning/mvp-m7-plan.md, D-5): exactly 1. */
static int accepts_input(const struct be_mvp_state *state)
{
	return state->accept_input == 1U;
}

static int probe_available(const struct be_mvp_state *state, be_u64 eid)
{
	return eid == BE_MVP_SBI_EID_BASE || eid == BE_MVP_SBI_EID_TIME ||
	       eid == BE_MVP_SBI_EID_DBCN || eid == BE_MVP_SBI_EID_SRST ||
	       (eid == BE_MVP_SBI_EID_MGMT && accepts_mgmt(state));
}

static void sbi_base(const struct be_mvp_state *state, be_u64 fid,
		     be_u64 argument0, struct be_mvp_result *result)
{
	if (fid == BE_MVP_SBI_BASE_GET_SPEC_VERSION)
		sbi_return(result, BE_MVP_ACTION_RETURN, BE_MVP_SBI_SUCCESS,
			   BE_MVP_SBI_SPEC_VERSION);
	else if (fid == BE_MVP_SBI_BASE_GET_IMPL_ID)
		sbi_return(result, BE_MVP_ACTION_RETURN, BE_MVP_SBI_SUCCESS,
			   BE_MVP_SBI_IMPL_ID);
	else if (fid == BE_MVP_SBI_BASE_GET_IMPL_VERSION)
		sbi_return(result, BE_MVP_ACTION_RETURN, BE_MVP_SBI_SUCCESS,
			   accepts_mgmt(state) ?
			   BE_MVP_SBI_IMPL_VERSION_MGMT :
			   BE_MVP_SBI_IMPL_VERSION);
	else if (fid == BE_MVP_SBI_BASE_PROBE_EXTENSION)
		sbi_return(result, BE_MVP_ACTION_RETURN, BE_MVP_SBI_SUCCESS,
			   probe_available(state, argument0) ? 1U : 0U);
	else if (fid == BE_MVP_SBI_BASE_GET_MVENDORID ||
		 fid == BE_MVP_SBI_BASE_GET_MARCHID ||
		 fid == BE_MVP_SBI_BASE_GET_MIMPID)
		sbi_return(result, BE_MVP_ACTION_RETURN, BE_MVP_SBI_SUCCESS, 0U);
	else
		sbi_return(result, BE_MVP_ACTION_RETURN,
			   BE_MVP_SBI_ERR_NOT_SUPPORTED, 0U);
}

/*
 * DBCN: write within the window, a byte, and, for a domain the sealed
 * configuration grants console input, read (planning/mvp-m7-plan.md, D-1):
 * a2 0, then a count of 0 at once, then the whole buffer [a1, a1 + a0)
 * inside the window, the write-authority rule, before the runtime takes a
 * queued byte or writes a guest byte. Every other domain's read is
 * refused, as before M7.
 */
static void sbi_dbcn(const struct be_mvp_state *state,
		     const struct be_mvp_gstage_map *map, be_u64 fid,
		     const struct be_r4_frame *frame,
		     struct be_mvp_result *result)
{
	be_u64 length = frame->gpr[BE_R4_GPR_A0];
	be_u64 address = frame->gpr[BE_R4_GPR_A1];
	be_u64 address_high = frame->gpr[BE_MVP_GPR_A2];

	if (fid == BE_MVP_SBI_DBCN_WRITE) {
		if (address_high != 0U)
			sbi_return(result, BE_MVP_ACTION_RETURN,
				   BE_MVP_SBI_ERR_INVALID_PARAM, 0U);
		else if (length == 0U)
			sbi_return(result, BE_MVP_ACTION_RETURN,
				   BE_MVP_SBI_SUCCESS, 0U);
		else if (!be_mvp_gstage_translate(map, address, length,
						  &result->source_pa))
			sbi_return(result, BE_MVP_ACTION_RETURN,
				   BE_MVP_SBI_ERR_INVALID_PARAM, 0U);
		else {
			result->length = length < BE_MVP_DBCN_MAX_BYTES ?
				length : BE_MVP_DBCN_MAX_BYTES;
			sbi_return(result, BE_MVP_ACTION_CONSOLE_WRITE,
				   BE_MVP_SBI_SUCCESS, result->length);
		}
	} else if (fid == BE_MVP_SBI_DBCN_READ) {
		if (!accepts_input(state))
			sbi_return(result, BE_MVP_ACTION_RETURN,
				   BE_MVP_SBI_ERR_DENIED, 0U);
		else if (address_high != 0U)
			sbi_return(result, BE_MVP_ACTION_RETURN,
				   BE_MVP_SBI_ERR_INVALID_PARAM, 0U);
		else if (length == 0U)
			sbi_return(result, BE_MVP_ACTION_RETURN,
				   BE_MVP_SBI_SUCCESS, 0U);
		else if (!be_mvp_gstage_translate(map, address, length,
						  &result->target_pa))
			sbi_return(result, BE_MVP_ACTION_RETURN,
				   BE_MVP_SBI_ERR_INVALID_PARAM, 0U);
		else {
			result->length = length < BE_MVP_DBCN_MAX_BYTES ?
				length : BE_MVP_DBCN_MAX_BYTES;
			sbi_return(result, BE_MVP_ACTION_CONSOLE_READ,
				   BE_MVP_SBI_SUCCESS, 0U);
		}
	} else if (fid == BE_MVP_SBI_DBCN_WRITE_BYTE) {
		result->byte = (be_u8)(length & 0xffU);
		sbi_return(result, BE_MVP_ACTION_CONSOLE_BYTE,
			   BE_MVP_SBI_SUCCESS, 0U);
	} else {
		sbi_return(result, BE_MVP_ACTION_RETURN,
			   BE_MVP_SBI_ERR_NOT_SUPPORTED, 0U);
	}
}

static void sbi_srst(struct be_mvp_state *state, be_u64 fid,
		     const struct be_r4_frame *frame,
		     struct be_mvp_result *result)
{
	be_u64 type = frame->gpr[BE_R4_GPR_A0];
	be_u64 reason = frame->gpr[BE_R4_GPR_A1];

	if (fid != BE_MVP_SBI_SRST_SYSTEM_RESET)
		sbi_return(result, BE_MVP_ACTION_RETURN,
			   BE_MVP_SBI_ERR_NOT_SUPPORTED, 0U);
	else if (type > BE_MVP_SRST_TYPE_WARM_REBOOT ||
		 reason > BE_MVP_SRST_REASON_FAILURE)
		sbi_return(result, BE_MVP_ACTION_RETURN,
			   BE_MVP_SBI_ERR_INVALID_PARAM, 0U);
	else if (type != BE_MVP_SRST_TYPE_SHUTDOWN) {
		/* A reboot request (panic=-1 included) ends the run. */
		result->failure = be_mvp_fail(state, BE_MVP_CLASS_GUEST_REBOOT);
		sbi_return(result, BE_MVP_ACTION_GUEST_REBOOT,
			   BE_MVP_SBI_SUCCESS, 0U);
	} else if (reason == BE_MVP_SRST_REASON_NONE) {
		/* Only the calling domain stops; the run goes on. */
		state->phase = BE_MVP_PHASE_STOPPED;
		sbi_return(result, BE_MVP_ACTION_SHUTDOWN, BE_MVP_SBI_SUCCESS,
			   0U);
	} else {
		result->failure = be_mvp_fail(state, BE_MVP_CLASS_GUEST_FAILURE);
		sbi_return(result, BE_MVP_ACTION_GUEST_FAILURE,
			   BE_MVP_SBI_SUCCESS, 0U);
	}
}

/*
 * The management extension (planning/mvp-m2-plan.md, Q3): pause or
 * terminate of the domain a0 names is a request for hart 0, which the
 * runtime posts and waits for; any other function is not supported, on
 * this hart, without a request.
 */
static void sbi_mgmt(be_u64 fid, const struct be_r4_frame *frame,
		     struct be_mvp_result *result)
{
	if (fid != BE_MVP_SBI_MGMT_PAUSE && fid != BE_MVP_SBI_MGMT_TERMINATE) {
		sbi_return(result, BE_MVP_ACTION_RETURN,
			   BE_MVP_SBI_ERR_NOT_SUPPORTED, 0U);
		return;
	}
	result->fid = fid;
	result->target = frame->gpr[BE_R4_GPR_A0];
	sbi_return(result, BE_MVP_ACTION_MGMT, BE_MVP_SBI_SUCCESS, 0U);
}

/* Each accepted ecall adds one to exactly one call class: a read refused
 * with DENIED to dbcn_read, a served one to dbcn_input. */
static void count_call(struct be_mvp_counts *counts, be_u64 eid, be_u64 fid,
		       const struct be_mvp_result *result)
{
	if (result->error == BE_MVP_SBI_ERR_NOT_SUPPORTED ||
	    result->error == BE_MVP_SBI_ERR_INVALID_PARAM)
		++counts->refused;
	else if (result->action == BE_MVP_ACTION_MGMT)
		++counts->mgmt;
	else if (eid == BE_MVP_SBI_EID_BASE)
		++counts->base;
	else if (eid == BE_MVP_SBI_EID_TIME)
		++counts->time;
	else if (eid == BE_MVP_SBI_EID_SRST)
		++counts->srst;
	else if (fid == BE_MVP_SBI_DBCN_WRITE)
		++counts->dbcn_write;
	else if (fid == BE_MVP_SBI_DBCN_READ &&
		 result->error == BE_MVP_SBI_ERR_DENIED)
		++counts->dbcn_read;
	else if (fid == BE_MVP_SBI_DBCN_READ)
		++counts->dbcn_input;
	else
		++counts->dbcn_byte;
}

enum be_mvp_action be_mvp_handle_exit(struct be_mvp_state *state,
				      const struct be_mvp_gstage_map *map,
				      const struct be_mvp_gstage_leaves *leaves,
				      const struct be_mvp_exit *record,
				      struct be_mvp_result *result)
{
	const struct be_r4_frame *frame;
	struct be_mvp_counts *counts;
	enum be_mvp_class failure;
	be_u64 eid;
	be_u64 fid;

	if (result == (struct be_mvp_result *)0) {
		(void)be_mvp_fail(state, BE_MVP_CLASS_EXCEPTION);
		return BE_MVP_ACTION_TERMINAL;
	}
	*result = (struct be_mvp_result){ 0 };
	if (state == (struct be_mvp_state *)0 ||
	    map == (const struct be_mvp_gstage_map *)0 ||
	    leaves == (const struct be_mvp_gstage_leaves *)0 ||
	    record == (const struct be_mvp_exit *)0 ||
	    state->phase != BE_MVP_PHASE_RUNNING)
		return terminal(state, result, BE_MVP_CLASS_EXCEPTION);
	counts = &state->counts;
	if (counts->exits >= state->exit_ceiling) {
		counts->exits = state->exit_ceiling + 1U;
		return terminal(state, result, BE_MVP_CLASS_EXIT_BUDGET);
	}
	++counts->exits;
	frame = &record->frame;
	if (frame->reserved != 0U ||
	    (record->hstatus & BE_MVP_HSTATUS_SPV) == 0U)
		return terminal(state, result, BE_MVP_CLASS_EXCEPTION);
	/* The IPI: the PING waits in the inbound ring; resume where it hit. */
	if (frame->scause == BE_MVP_SCAUSE_SUPERVISOR_SOFTWARE) {
		++counts->ipi;
		result->resume_pc = frame->sepc;
		result->action = BE_MVP_ACTION_IPI;
		return result->action;
	}
	failure = be_mvp_classify_cause(frame->scause);
	/* A guest-page fault the denial entry accepts is a denial. */
	if (failure == BE_MVP_CLASS_GUEST_PAGE_FAULT &&
	    be_mvp_denial_decide(state, map, leaves, record,
				 &result->denial)) {
		++counts->denials;
		result->action = BE_MVP_ACTION_DENY;
		return result->action;
	}
	if (failure != BE_MVP_CLASS_NONE)
		return terminal(state, result, failure);
	if (frame->sepc > ~BE_U64_C(0) - BE_MVP_INSTRUCTION_SIZE)
		return terminal(state, result, BE_MVP_CLASS_RESUME);
	result->resume_pc = frame->sepc + BE_MVP_INSTRUCTION_SIZE;

	eid = frame->gpr[BE_R4_GPR_A7];
	fid = frame->gpr[BE_R4_GPR_A6];
	if (eid == BE_MVP_SBI_EID_BASE)
		sbi_base(state, fid, frame->gpr[BE_R4_GPR_A0], result);
	else if (eid == BE_MVP_SBI_EID_TIME &&
		 fid == BE_MVP_SBI_TIME_SET_TIMER) {
		result->timer = frame->gpr[BE_R4_GPR_A0];
		sbi_return(result, BE_MVP_ACTION_SET_TIMER, BE_MVP_SBI_SUCCESS,
			   0U);
	} else if (eid == BE_MVP_SBI_EID_DBCN)
		sbi_dbcn(state, map, fid, frame, result);
	else if (eid == BE_MVP_SBI_EID_SRST)
		sbi_srst(state, fid, frame, result);
	else if (eid == BE_MVP_SBI_EID_MGMT && accepts_mgmt(state))
		sbi_mgmt(fid, frame, result);
	else
		sbi_return(result, BE_MVP_ACTION_RETURN,
			   BE_MVP_SBI_ERR_NOT_SUPPORTED, 0U);
	count_call(counts, eid, fid, result);
	return result->action;
}

/* serve_record()'s and serve()'s answer when the hart failed. */
#define SERVE_FAILED			(~BE_U64_C(0))

static be_u64 refuse(struct be_mvp_state *state, enum be_mvp_class failure)
{
	(void)be_mvp_fail(state, failure);
	return SERVE_FAILED;
}

/* A result hart 0 answers a request with (Q3): another function's is the
 * domain hart's own. */
static int answerable(be_u64 code)
{
	return code == (be_u64)BE_MVP_SBI_SUCCESS ||
	       code == (be_u64)BE_MVP_SBI_ERR_INVALID_PARAM ||
	       code == (be_u64)BE_MVP_SBI_ERR_DENIED ||
	       code == (be_u64)BE_MVP_SBI_ERR_INVALID_STATE;
}

/*
 * One record from the hart's inbound ring, by the hart's phase: a PING
 * while running, answered with a PONG; the MGMT_RESULT the hart waits for,
 * whose result it keeps (planning/mvp-m2-plan.md, Q14); and, in an image
 * that accepts the management extension, a PAUSE while running and not
 * waiting, answered with PAUSED, and a TERMINATE then or while paused,
 * answered with TERMINATED (Q15), each naming the hart's exits and the
 * order's requester. Anything else fails the hart as ipi.
 *
 * Return: 1 when it posted an answer, 0 when it took the MGMT_RESULT, or
 *         SERVE_FAILED with the hart FAILED.
 */
static be_u64 serve_record(struct be_mvp_state *state,
			   struct be_mvp_ring *outbound,
			   const struct be_mvp_record *record, be_u64 received,
			   be_u64 spv, be_u64 now)
{
	be_u64 answer[BE_MVP_PONG_WORDS];
	enum be_mvp_record_type type = BE_MVP_RECORD_PONG;
	be_u64 words = BE_MVP_PONG_WORDS;
	int running = state->phase == BE_MVP_PHASE_RUNNING;
	int ordered = accepts_mgmt(state) &&
		      record->length == BE_MVP_PAUSE_WORDS * 8U &&
		      be_mvp_record_word(record, BE_MVP_PAUSE_BY) <
			      BE_MVP_DOMAINS;

	if (record->type == BE_MVP_RECORD_PING) {
		if (!running || record->length != 0U)
			return refuse(state, BE_MVP_CLASS_IPI);
		answer[BE_MVP_PONG_SENT] = record->time;
		answer[BE_MVP_PONG_RECEIVED] = received;
		answer[BE_MVP_PONG_SPV] = spv;
	} else if (record->type == BE_MVP_RECORD_MGMT_RESULT) {
		if (!running || state->awaiting == 0U ||
		    record->length != BE_MVP_MGMT_RESULT_WORDS * 8U ||
		    be_mvp_record_word(record, BE_MVP_MGMT_RESULT_SEQ) !=
			    state->awaiting ||
		    !answerable(be_mvp_record_word(record,
						   BE_MVP_MGMT_RESULT_CODE)))
			return refuse(state, BE_MVP_CLASS_IPI);
		state->answer = be_mvp_record_word(record,
						   BE_MVP_MGMT_RESULT_CODE);
		state->awaiting = 0U;
		return 0U;
	} else if (record->type == BE_MVP_RECORD_PAUSE) {
		if (!ordered || !running || state->awaiting != 0U)
			return refuse(state, BE_MVP_CLASS_IPI);
		state->phase = BE_MVP_PHASE_PAUSED;
		type = BE_MVP_RECORD_PAUSED;
	} else if (record->type == BE_MVP_RECORD_TERMINATE) {
		if (!ordered || ((!running || state->awaiting != 0U) &&
				 state->phase != BE_MVP_PHASE_PAUSED))
			return refuse(state, BE_MVP_CLASS_IPI);
		state->phase = BE_MVP_PHASE_TERMINATED;
		type = BE_MVP_RECORD_TERMINATED;
	} else {
		return refuse(state, BE_MVP_CLASS_IPI);
	}
	if (type != BE_MVP_RECORD_PONG) {
		be_u64 flushed;

		/* The domain's unterminated line, with its prefix, before
		 * the transition (planning/mvp-m7-plan.md, Q9). */
		flushed = be_mvp_console_flush(state, outbound, now);
		if (flushed == BE_MVP_CONSOLE_INVALID ||
		    flushed == BE_MVP_CONSOLE_FULL)
			return refuse(state, BE_MVP_CLASS_RING);
		state->by = be_mvp_record_word(record, BE_MVP_PAUSE_BY);
		answer[BE_MVP_PAUSED_EXITS] = state->counts.exits;
		answer[BE_MVP_PAUSED_BY] = state->by;
		words = BE_MVP_PAUSED_WORDS;
	}
	if (!be_mvp_ring_post_words(outbound, type, now, answer, words))
		return refuse(state, BE_MVP_CLASS_RING);
	return 1U;
}

/*
 * Every record up to the acquired head, each by serve_record(); a ring
 * holds at most capacity / 16 records, so the last take of this bounded
 * loop finds it empty.
 *
 * Return: the answers posted, with @taken the records taken; or
 *         SERVE_FAILED with the hart FAILED.
 */
static be_u64 serve(struct be_mvp_state *state, struct be_mvp_ring *inbound,
		    struct be_mvp_ring *outbound, be_u64 received, be_u64 spv,
		    be_u64 now, be_u64 *taken)
{
	struct be_mvp_record record;
	be_u64 posted = 0U;
	be_u64 index;

	*taken = 0U;
	for (index = 0U; index <= inbound->capacity /
			 BE_MVP_RECORD_HEADER_BYTES; ++index) {
		enum be_mvp_ring_status status = be_mvp_ring_take(inbound,
								  &record);
		be_u64 answered;

		if (status == BE_MVP_RING_EMPTY)
			break;
		if (status != BE_MVP_RING_RECORD)
			return refuse(state, BE_MVP_CLASS_RING);
		answered = serve_record(state, outbound, &record, received,
					spv, now);
		if (answered == SERVE_FAILED)
			return SERVE_FAILED;
		posted += answered;
		++*taken;
	}
	return posted;
}

be_u64 be_mvp_ipi_serve(struct be_mvp_state *state,
			struct be_mvp_ring *inbound,
			struct be_mvp_ring *outbound,
			const struct be_mvp_exit *record, be_u64 now)
{
	be_u64 taken;

	if (state == (struct be_mvp_state *)0)
		return 0U;
	if (inbound == (struct be_mvp_ring *)0 ||
	    outbound == (struct be_mvp_ring *)0 ||
	    record == (const struct be_mvp_exit *)0 ||
	    state->phase != BE_MVP_PHASE_RUNNING) {
		(void)be_mvp_fail(state, BE_MVP_CLASS_IPI);
		return 0U;
	}
	/* The receipt is the IPI exit's, at V=1 or not. */
	if (serve(state, inbound, outbound, record->time,
		  (record->hstatus & BE_MVP_HSTATUS_SPV) != 0U ? 1U : 0U, now,
		  &taken) == SERVE_FAILED)
		return 0U;
	if (taken == 0U)
		(void)be_mvp_fail(state, BE_MVP_CLASS_IPI);
	return taken;
}

int be_mvp_wait_serve(struct be_mvp_state *state, struct be_mvp_ring *inbound,
		      struct be_mvp_ring *outbound, be_u64 now,
		      be_u64 *posted)
{
	be_u64 answers;
	be_u64 taken;

	if (posted == (be_u64 *)0)
		return 0;
	*posted = 0U;
	if (state == (struct be_mvp_state *)0)
		return 0;
	if (inbound == (struct be_mvp_ring *)0 ||
	    outbound == (struct be_mvp_ring *)0 ||
	    !((state->phase == BE_MVP_PHASE_RUNNING && state->awaiting != 0U) ||
	      state->phase == BE_MVP_PHASE_PAUSED ||
	      state->phase == BE_MVP_PHASE_TERMINATED)) {
		(void)be_mvp_fail(state, BE_MVP_CLASS_IPI);
		return 0;
	}
	/* In HS: the receipt is now, and the IPI did not arrive at V=1. */
	answers = serve(state, inbound, outbound, now, 0U, now, &taken);
	if (answers == SERVE_FAILED)
		return 0;
	*posted = answers;
	return 1;
}

be_u64 be_mvp_counts_sbi(const struct be_mvp_counts *counts)
{
	if (counts == (const struct be_mvp_counts *)0)
		return 0U;
	return counts->base + counts->time + counts->dbcn_write +
	       counts->dbcn_read + counts->dbcn_byte + counts->srst +
	       counts->refused + counts->mgmt + counts->dbcn_input;
}

long be_mvp_mgmt_decide(const struct be_mvp_mgmt_grant *grants, be_u64 count,
			be_u64 requester, be_u64 fid, be_u64 target,
			enum be_mvp_target_state state)
{
	be_u64 permission;
	be_u64 index;
	int granted = 0;

	if (fid == BE_MVP_SBI_MGMT_PAUSE)
		permission = BE_MVP_MGMT_PAUSE;
	else if (fid == BE_MVP_SBI_MGMT_TERMINATE)
		permission = BE_MVP_MGMT_TERMINATE;
	else
		return BE_MVP_SBI_ERR_NOT_SUPPORTED;
	if (target >= BE_MVP_DOMAINS)
		return BE_MVP_SBI_ERR_INVALID_PARAM;
	/* Only a grant names a pair: the requester itself included. */
	if (grants != (const struct be_mvp_mgmt_grant *)0 &&
	    count <= BE_MVP_MGMT_GRANTS_MAX && requester < BE_MVP_DOMAINS)
		for (index = 0U; index < count; ++index)
			if (grants[index].from == requester &&
			    grants[index].to == target &&
			    (grants[index].permissions & permission) != 0U)
				granted = 1;
	if (!granted)
		return BE_MVP_SBI_ERR_DENIED;
	if (state != BE_MVP_TARGET_RUNNING &&
	    !(state == BE_MVP_TARGET_PAUSED &&
	      fid == BE_MVP_SBI_MGMT_TERMINATE))
		return BE_MVP_SBI_ERR_INVALID_STATE;
	return BE_MVP_MGMT_DELIVER;
}

void be_mvp_inject_words(const struct be_mvp_denial *denial, be_u64 *words)
{
	if (denial == (const struct be_mvp_denial *)0 ||
	    words == (be_u64 *)0)
		return;
	words[BE_MVP_INJECT_VSCAUSE] = denial->inject_vscause;
	words[BE_MVP_INJECT_VSTVAL] = denial->inject_vstval;
	words[BE_MVP_INJECT_VSEPC] = denial->inject_vsepc;
	words[BE_MVP_INJECT_VSSTATUS] = denial->inject_vsstatus;
}

be_u32 be_mvp_inject_mismatch(const be_u64 *written, const be_u64 *readback)
{
	be_u32 index;

	if (written == (const be_u64 *)0 || readback == (const be_u64 *)0)
		return 0U;
	for (index = 0U; index < BE_MVP_INJECT_WORDS; ++index)
		if (readback[index] != written[index])
			return index;
	return BE_MVP_INJECT_WORDS;
}

be_u32 be_mvp_inject_vcsr(be_u32 index)
{
	static const be_u32 vcsr[BE_MVP_INJECT_WORDS] = {
		[BE_MVP_INJECT_VSCAUSE] = BE_MVP_VCSR_VSCAUSE,
		[BE_MVP_INJECT_VSTVAL] = BE_MVP_VCSR_VSTVAL,
		[BE_MVP_INJECT_VSEPC] = BE_MVP_VCSR_VSEPC,
		[BE_MVP_INJECT_VSSTATUS] = BE_MVP_VCSR_VSSTATUS,
	};

	if (index >= BE_MVP_INJECT_WORDS)
		return BE_MVP_VCSR_COUNT;
	return vcsr[index];
}

void be_mvp_apply_return(struct be_r4_frame *frame,
			 const struct be_mvp_result *result)
{
	if (frame == (struct be_r4_frame *)0 ||
	    result == (const struct be_mvp_result *)0)
		return;
	switch (result->action) {
	case BE_MVP_ACTION_RETURN:
	case BE_MVP_ACTION_CONSOLE_WRITE:
	case BE_MVP_ACTION_CONSOLE_BYTE:
	case BE_MVP_ACTION_CONSOLE_READ:
	case BE_MVP_ACTION_SET_TIMER:
	case BE_MVP_ACTION_MGMT:
		frame->gpr[BE_R4_GPR_A0] = (be_u64)result->error;
		frame->gpr[BE_R4_GPR_A1] = result->value;
		frame->sepc = result->resume_pc;
		break;
	default:
		break;
	}
}

void be_mvp_entry_frame(struct be_mvp_exit *record, be_u64 pc, be_u64 hart,
			be_u64 dtb)
{
	if (record == (struct be_mvp_exit *)0)
		return;
	*record = (struct be_mvp_exit){ 0 };
	record->frame.sepc = pc;
	record->frame.gpr[BE_R4_GPR_A0] = hart;
	record->frame.gpr[BE_R4_GPR_A1] = dtb;
	record->hstatus = BE_MVP_HSTATUS_SPV | BE_MVP_HSTATUS_SPVP;
}

be_u64 be_mvp_record_spp(const struct be_mvp_exit *record)
{
	if (record == (const struct be_mvp_exit *)0 ||
	    (record->hstatus & BE_MVP_HSTATUS_SPVP) == 0U)
		return 0U;
	return BE_MVP_SSTATUS_SPP;
}

void be_mvp_vcsr_initial(be_u64 *csr)
{
	be_u32 index;

	if (csr == (be_u64 *)0)
		return;
	for (index = 0U; index < BE_MVP_VCSR_COUNT; ++index)
		csr[index] = 0U;
	csr[BE_MVP_VCSR_VSSTATUS] = BE_MVP_VSSTATUS_UXL64;
	csr[BE_MVP_VCSR_VSTIMECMP] = BE_MVP_VSTIMECMP_DISARMED;
}

be_u32 be_mvp_vcsr_mismatch(const be_u64 *expected, const be_u64 *readback)
{
	be_u32 index;

	if (expected == (const be_u64 *)0 || readback == (const be_u64 *)0)
		return 0U;
	for (index = 0U; index < BE_MVP_VCSR_COUNT; ++index)
		if (readback[index] != expected[index])
			return index;
	return BE_MVP_VCSR_COUNT;
}

const char *be_mvp_vcsr_name(be_u32 index)
{
	if (index >= BE_MVP_VCSR_COUNT)
		return "invalid";
	return be_mvp_vcsr_names[index];
}

const char *be_mvp_domain_prefix(be_u32 domain)
{
	if (domain == 0U)
		return BE_MVP_G0_PREFIX;
	if (domain == 1U)
		return BE_MVP_G1_PREFIX;
	return (const char *)0;
}

/* One ended line: one LINE record of the buffered bytes; then empty. */
static int post_line(struct be_mvp_state *state, struct be_mvp_ring *outbound,
		     be_u64 now)
{
	if (!be_mvp_ring_post(outbound, BE_MVP_RECORD_LINE, now,
			      (const be_u8 *)state->console.text,
			      state->console.length)) {
		(void)be_mvp_fail(state, BE_MVP_CLASS_RING);
		return 0;
	}
	state->console.length = 0U;
	++state->counts.lines;
	return 1;
}

static int console_valid(const struct be_mvp_state *state,
			 const struct be_mvp_ring *outbound)
{
	return state != (const struct be_mvp_state *)0 &&
	       outbound != (const struct be_mvp_ring *)0 &&
	       state->console.length <= BE_MVP_CONSOLE_LINE_BYTES;
}

be_u64 be_mvp_console_feed(struct be_mvp_state *state,
			   struct be_mvp_ring *outbound, const be_u8 *input,
			   be_u64 length, be_u64 now)
{
	be_u64 posted = 0U;
	be_u64 index;

	if (!console_valid(state, outbound) || input == (const be_u8 *)0 ||
	    length > BE_MVP_DBCN_MAX_BYTES ||
	    state->phase != BE_MVP_PHASE_RUNNING)
		return BE_MVP_CONSOLE_INVALID;
	for (index = 0U; index < length; ++index) {
		be_u8 byte = input[index];

		/* hvc sends CR before LF; CR is dropped, not shown. */
		if (byte == (be_u8)'\r')
			continue;
		if (byte == (be_u8)'\n') {
			if (!post_line(state, outbound, now))
				return BE_MVP_CONSOLE_FULL;
			++posted;
			continue;
		}
		/* A full buffer is posted as its own line. */
		if (state->console.length == BE_MVP_CONSOLE_LINE_BYTES) {
			if (!post_line(state, outbound, now))
				return BE_MVP_CONSOLE_FULL;
			++posted;
		}
		state->console.text[state->console.length++] =
			byte >= 0x20U && byte <= 0x7eU ? (char)byte : '?';
	}
	return posted;
}

be_u64 be_mvp_console_flush(struct be_mvp_state *state,
			    struct be_mvp_ring *outbound, be_u64 now)
{
	if (!console_valid(state, outbound))
		return BE_MVP_CONSOLE_INVALID;
	if (state->console.length == 0U)
		return 0U;
	if (!post_line(state, outbound, now))
		return BE_MVP_CONSOLE_FULL;
	return 1U;
}

int be_mvp_post_ready(struct be_mvp_ring *outbound,
		      const struct be_mvp_controls *controls, be_u64 now)
{
	be_u64 words[BE_MVP_READY_WORDS];

	if (controls == (const struct be_mvp_controls *)0)
		return 0;
	words[BE_MVP_READY_HGATP] = controls->hgatp;
	words[BE_MVP_READY_HSTATUS] =
		controls->hstatus & BE_R3_HSTATUS_CONTROL_MASK;
	words[BE_MVP_READY_HEDELEG] = controls->hedeleg;
	words[BE_MVP_READY_HIDELEG] = controls->hideleg;
	words[BE_MVP_READY_HCOUNTEREN] = controls->hcounteren;
	words[BE_MVP_READY_SIE] = controls->sie;
	words[BE_MVP_READY_HENVCFG] = controls->henvcfg;
	words[BE_MVP_READY_VSTIMECMP] = controls->vstimecmp;
	return be_mvp_ring_post_words(outbound, BE_MVP_RECORD_READY, now, words,
				      BE_MVP_READY_WORDS);
}

int be_mvp_post_entered(struct be_mvp_ring *outbound,
			const struct be_mvp_exit *record, be_u64 now)
{
	be_u64 words[BE_MVP_ENTERED_WORDS];

	if (record == (const struct be_mvp_exit *)0)
		return 0;
	words[BE_MVP_ENTERED_PC] = record->frame.sepc;
	words[BE_MVP_ENTERED_A0] = record->frame.gpr[BE_R4_GPR_A0];
	words[BE_MVP_ENTERED_A1] = record->frame.gpr[BE_R4_GPR_A1];
	return be_mvp_ring_post_words(outbound, BE_MVP_RECORD_ENTERED, now,
				      words, BE_MVP_ENTERED_WORDS);
}

int be_mvp_post_shutdown(struct be_mvp_state *state,
			 struct be_mvp_ring *outbound, be_u64 entered,
			 be_u64 now)
{
	be_u64 words[BE_MVP_SHUTDOWN_WORDS];

	if (state == (struct be_mvp_state *)0 ||
	    outbound == (struct be_mvp_ring *)0 ||
	    state->phase != BE_MVP_PHASE_STOPPED)
		return 0;
	words[BE_MVP_SHUTDOWN_EXITS] = state->counts.exits;
	words[BE_MVP_SHUTDOWN_BASE] = state->counts.base;
	words[BE_MVP_SHUTDOWN_TIME] = state->counts.time;
	words[BE_MVP_SHUTDOWN_DBCN_WRITE] = state->counts.dbcn_write;
	words[BE_MVP_SHUTDOWN_DBCN_READ] = state->counts.dbcn_read;
	words[BE_MVP_SHUTDOWN_DBCN_BYTE] = state->counts.dbcn_byte;
	words[BE_MVP_SHUTDOWN_SRST] = state->counts.srst;
	words[BE_MVP_SHUTDOWN_REFUSED] = state->counts.refused;
	words[BE_MVP_SHUTDOWN_IPI] = state->counts.ipi;
	words[BE_MVP_SHUTDOWN_LINES] = state->counts.lines;
	/* The high-water mark of every record before this one. */
	words[BE_MVP_SHUTDOWN_RING_PEAK] = be_mvp_ring_peak(outbound);
	words[BE_MVP_SHUTDOWN_ENTERED] = entered;
	words[BE_MVP_SHUTDOWN_DENIALS] = state->counts.denials;
	words[BE_MVP_SHUTDOWN_MGMT] = state->counts.mgmt;
	words[BE_MVP_SHUTDOWN_DBCN_INPUT] = state->counts.dbcn_input;
	return be_mvp_ring_post_words(outbound, BE_MVP_RECORD_SHUTDOWN, now,
				      words, BE_MVP_SHUTDOWN_WORDS);
}

int be_mvp_post_denial(const struct be_mvp_state *state,
		       struct be_mvp_ring *outbound,
		       const struct be_mvp_denial *denial, be_u64 now)
{
	be_u64 words[BE_MVP_DENIAL_WORDS];

	if (state == (const struct be_mvp_state *)0 ||
	    denial == (const struct be_mvp_denial *)0 ||
	    state->phase != BE_MVP_PHASE_RUNNING ||
	    state->counts.denials == 0U)
		return 0;
	words[BE_MVP_DENIAL_SEQ] = state->counts.denials;
	words[BE_MVP_DENIAL_CAUSE] = denial->cause;
	words[BE_MVP_DENIAL_KIND] = denial->kind;
	words[BE_MVP_DENIAL_GPA] = denial->gpa;
	words[BE_MVP_DENIAL_HTVAL] = denial->htval;
	words[BE_MVP_DENIAL_HTINST] = denial->htinst;
	words[BE_MVP_DENIAL_STVAL] = denial->stval;
	words[BE_MVP_DENIAL_SEPC] = denial->sepc;
	words[BE_MVP_DENIAL_VSSTATUS] = denial->vsstatus;
	words[BE_MVP_DENIAL_VSTVEC] = denial->vstvec;
	words[BE_MVP_DENIAL_INJECTED] = denial->inject_vscause;
	words[BE_MVP_DENIAL_EXIT] = denial->time;
	return be_mvp_ring_post_words(outbound, BE_MVP_RECORD_DENIAL, now,
				      words, BE_MVP_DENIAL_WORDS);
}

int be_mvp_post_mgmt_request(struct be_mvp_state *state,
			     struct be_mvp_ring *outbound,
			     const struct be_mvp_result *result, be_u64 now)
{
	be_u64 words[BE_MVP_MGMT_REQUEST_WORDS];

	if (state == (struct be_mvp_state *)0 ||
	    result == (const struct be_mvp_result *)0 ||
	    state->phase != BE_MVP_PHASE_RUNNING || !accepts_mgmt(state) ||
	    state->awaiting != 0U || state->counts.mgmt == 0U ||
	    result->action != BE_MVP_ACTION_MGMT ||
	    (result->fid != BE_MVP_SBI_MGMT_PAUSE &&
	     result->fid != BE_MVP_SBI_MGMT_TERMINATE))
		return 0;
	words[BE_MVP_MGMT_REQUEST_FID] = result->fid;
	words[BE_MVP_MGMT_REQUEST_TARGET] = result->target;
	words[BE_MVP_MGMT_REQUEST_SEQ] = state->counts.mgmt;
	if (!be_mvp_ring_post_words(outbound, BE_MVP_RECORD_MGMT_REQUEST, now,
				    words, BE_MVP_MGMT_REQUEST_WORDS))
		return 0;
	state->awaiting = state->counts.mgmt;
	state->answer = 0U;
	return 1;
}

int be_mvp_post_fail(struct be_mvp_state *state,
		     struct be_mvp_ring *outbound, const be_u64 *detail,
		     be_u64 words, be_u64 now)
{
	be_u64 payload[BE_MVP_FAIL_MAX_WORDS];
	be_u64 index;

	if (state == (struct be_mvp_state *)0 ||
	    state->phase != BE_MVP_PHASE_FAILED ||
	    words > BE_MVP_FAIL_DETAIL_WORDS ||
	    (detail == (const be_u64 *)0 && words != 0U))
		return 0;
	payload[BE_MVP_FAIL_CLASS] = (be_u64)state->failure;
	for (index = 0U; index < words; ++index)
		payload[BE_MVP_FAIL_CLASS + 1U + index] = detail[index];
	return be_mvp_ring_post_words(outbound, BE_MVP_RECORD_FAIL, now,
				      payload, 1U + words);
}

void be_mvp_ack_wait_start(struct be_mvp_ack_wait *wait, be_u64 now,
			   be_u64 taken)
{
	if (wait == (struct be_mvp_ack_wait *)0)
		return;
	wait->since = now;
	wait->taken = taken;
}

enum be_mvp_ack_step be_mvp_ack_wait_step(struct be_mvp_ack_wait *wait,
					  be_u64 now, be_u64 taken,
					  be_u64 published, int acknowledged)
{
	if (wait == (struct be_mvp_ack_wait *)0)
		return BE_MVP_ACK_FALLBACK;
	if (acknowledged != 0)
		return BE_MVP_ACK_PARK;
	/* Hart 0's tail never moves back, nor past the published head. */
	if (taken < wait->taken || taken > published)
		return BE_MVP_ACK_FALLBACK;
	/* A record taken: hart 0 is draining, however slowly it prints. */
	if (taken > wait->taken) {
		wait->taken = taken;
		wait->since = now;
		return BE_MVP_ACK_WAIT;
	}
	if (now - wait->since >= BE_MVP_FAIL_ACK_TICKS)
		return BE_MVP_ACK_FALLBACK;
	return BE_MVP_ACK_WAIT;
}

int be_mvp_hsm_stopped(long error, be_u64 value)
{
	return error == BE_MVP_SBI_SUCCESS && value == BE_MVP_HSM_STOPPED;
}

int be_mvp_hsm_started(long error, be_u64 value)
{
	return error == BE_MVP_SBI_SUCCESS && value == BE_MVP_HSM_STARTED;
}

int be_mvp_ipi_target(be_u64 hart, be_u64 *mask, be_u64 *base)
{
	if (mask == (be_u64 *)0 || base == (be_u64 *)0 ||
	    hart == ~BE_U64_C(0))
		return 0;
	*mask = 1U;
	*base = hart;
	return 1;
}

void be_mvp_hsm_census_init(struct be_mvp_hsm_census *census,
			    be_u64 domain0_hart, be_u64 domain1_hart)
{
	if (census == (struct be_mvp_hsm_census *)0)
		return;
	census->domain_hart[0] = domain0_hart;
	census->domain_hart[1] = domain1_hart;
	census->started = BE_MVP_HSM_NONE;
	census->refused = 0U;
}

int be_mvp_hsm_census_add(struct be_mvp_hsm_census *census, be_u64 hart,
			  long error, be_u64 value)
{
	if (census == (struct be_mvp_hsm_census *)0)
		return 0;
	if (hart == 0U || hart == BE_MVP_HSM_NONE) {
		census->refused = 1U;
	} else if (be_mvp_hsm_started(error, value)) {
		/* The one STARTED hart is the start rule's, not a domain's. */
		if (census->started != BE_MVP_HSM_NONE ||
		    hart == census->domain_hart[0] ||
		    hart == census->domain_hart[1])
			census->refused = 1U;
		if (census->started == BE_MVP_HSM_NONE)
			census->started = hart;
	} else if (!be_mvp_hsm_stopped(error, value)) {
		census->refused = 1U;
	}
	return census->refused == 0U;
}

void be_mvp_line_reset(struct be_mvp_line *line)
{
	if (line == (struct be_mvp_line *)0)
		return;
	line->length = 0U;
	line->overflow = 0U;
}

static void line_byte(struct be_mvp_line *line, char byte)
{
	if (line->overflow != 0U || line->length >= BE_MVP_LINE_CAPACITY) {
		line->overflow = 1U;
		return;
	}
	line->text[line->length++] = byte;
}

void be_mvp_line_text(struct be_mvp_line *line, const char *text)
{
	be_u64 index;

	if (line == (struct be_mvp_line *)0)
		return;
	if (text == (const char *)0) {
		line->overflow = 1U;
		return;
	}
	for (index = 0U; index <= BE_MVP_LINE_CAPACITY && text[index] != '\0';
	     ++index)
		line_byte(line, text[index]);
}

void be_mvp_line_hex(struct be_mvp_line *line, be_u64 value)
{
	static const char digits[] = "0123456789abcdef";
	unsigned int shift = 60U;

	if (line == (struct be_mvp_line *)0)
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

void be_mvp_line_decimal(struct be_mvp_line *line, be_u64 value)
{
	char digits[20];
	unsigned int count = 0U;

	if (line == (struct be_mvp_line *)0)
		return;
	do {
		digits[count++] = (char)('0' + (int)(value % 10U));
		value /= 10U;
	} while (value != 0U && count < sizeof(digits));
	while (count > 0U)
		line_byte(line, digits[--count]);
}
