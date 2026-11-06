// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP hart blocks and hart 0's control loop: the Sv39x4 hgatp
 *          value, the binding and block checks, the block descriptor hart 0
 *          fills, the per-domain protocol state machine over drained
 *          records, DENIAL records against the walked windows and the
 *          sealed channel record or pages included (planning/mvp-m1-plan.md,
 *          "Control loop and failure paths"), the management requests,
 *          their decisions, the pending requests, and the PAUSED and
 *          TERMINATED transitions (planning/mvp-m2-plan.md, "Control loop
 *          and failure paths"), the completion rule, the wake and wait
 *          accounting, the round-robin order and bound of hart 0's drain
 *          (Plan revision M0-C.1), the overlap and Q5's concurrency floor,
 *          and the printed form of a LINE; since M7 the input ring in the
 *          block and the domains console input may reach
 *          (planning/mvp-m7-plan.md, D-1 and D-3).
 * Trust:   restricted C with explicit bounded loops; no CSR, fence, SBI
 *          call, or I/O. Counters saturate; invalid input fails closed and
 *          stays failed.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, planning/mvp-m1-plan.md,
 *          and planning/mvp-m2-plan.md); see mvp-hart.h.
 */
#include "mvp-hart.h"

#define WORD_BYTES		8U

_Static_assert(BE_MVP_DOMAINS == 2U, "the control loop tracks two domains");
_Static_assert(sizeof(struct be_mvp_state_page) <= BE_MVP_BLOCK_STATE_BYTES,
	       "the state page holds its contents");
_Static_assert(__builtin_offsetof(struct be_mvp_state_page, inbound_head) ==
	       0U &&
	       __builtin_offsetof(struct be_mvp_state_page, inbound_tail) ==
	       BE_MVP_RING_INDEX_BYTES &&
	       __builtin_offsetof(struct be_mvp_state_page, outbound_head) ==
	       2U * BE_MVP_RING_INDEX_BYTES &&
	       __builtin_offsetof(struct be_mvp_state_page, outbound_tail) ==
	       3U * BE_MVP_RING_INDEX_BYTES &&
	       __builtin_offsetof(struct be_mvp_state_page, input_head) %
	       BE_MVP_RING_INDEX_BYTES == 0U &&
	       __builtin_offsetof(struct be_mvp_state_page, input_tail) ==
	       __builtin_offsetof(struct be_mvp_state_page, input_head) +
	       BE_MVP_RING_INDEX_BYTES,
	       "each ring index fills its own 64-byte line");
_Static_assert(__builtin_offsetof(struct be_mvp_block_desc, generation) ==
	       sizeof(struct be_mvp_block_desc) - WORD_BYTES,
	       "the generation word ends the descriptor");
_Static_assert(BE_MVP_G0_HGATP == (BE_MVP_HGATP_SV39X4 |
				   (BE_MVP_G0_VMID <<
				    BE_MVP_HGATP_VMID_SHIFT) |
				   (BE_MVP_G0_ROOT_HPA >>
				    BE_MVP_HGATP_PAGE_SHIFT)) &&
	       BE_MVP_G1_HGATP == (BE_MVP_HGATP_SV39X4 |
				   (BE_MVP_G1_VMID <<
				    BE_MVP_HGATP_VMID_SHIFT) |
				   (BE_MVP_G1_ROOT_HPA >>
				    BE_MVP_HGATP_PAGE_SHIFT)),
	       "the layout's hgatp values are the hart module's");
_Static_assert(BE_MVP_INBOUND_RING_BYTES >= BE_MVP_RING_MIN_BYTES &&
	       BE_MVP_VARIANT_OUTBOUND_RING_BYTES >= BE_MVP_RING_MIN_BYTES &&
	       BE_MVP_INPUT_RING_BYTES >= BE_MVP_RING_MIN_BYTES,
	       "every layout ring passes the block check");

static be_u64 add_saturating(be_u64 value, be_u64 addend)
{
	if (addend > ~BE_U64_C(0) - value)
		return ~BE_U64_C(0);
	return value + addend;
}

static int ring_bytes_valid(be_u64 bytes, be_u64 slot)
{
	return bytes >= BE_MVP_RING_MIN_BYTES && bytes <= slot &&
	       (bytes & (bytes - 1U)) == 0U;
}

be_u64 be_mvp_hgatp(be_u64 vmid, be_u64 root)
{
	if (vmid >= BE_MVP_HGATP_VMID_LIMIT ||
	    (root & (BE_MVP_HGATP_ROOT_ALIGN - 1U)) != 0U ||
	    root >= BE_MVP_HGATP_ROOT_LIMIT)
		return 0U;
	return BE_MVP_HGATP_SV39X4 | (vmid << BE_MVP_HGATP_VMID_SHIFT) |
	       (root >> BE_MVP_HGATP_PAGE_SHIFT);
}

int be_mvp_bindings_valid(const struct be_mvp_binding *bindings,
			  be_u64 count)
{
	be_u64 index;

	if (bindings == (const struct be_mvp_binding *)0 ||
	    count != BE_MVP_DOMAINS)
		return 0;
	for (index = 0U; index < BE_MVP_DOMAINS; ++index) {
		const struct be_mvp_binding *binding = &bindings[index];

		if (binding->hart == BE_MVP_CONTROL_HART ||
		    binding->hart == ~BE_U64_C(0) || binding->vmid == 0U ||
		    binding->root == 0U ||
		    be_mvp_hgatp(binding->vmid, binding->root) == 0U)
			return 0;
	}
	return bindings[0].hart != bindings[1].hart &&
	       bindings[0].vmid != bindings[1].vmid &&
	       bindings[0].root != bindings[1].root;
}

be_u64 be_mvp_block_hpa(be_u64 domain)
{
	if (domain >= BE_MVP_DOMAINS)
		return 0U;
	return BE_MVP_G0_BLOCK_HPA + domain * BE_MVP_BLOCK_BYTES;
}

enum be_mvp_block_error
be_mvp_block_fill(struct be_mvp_block_desc *desc, be_u64 domain,
		  const struct be_mvp_binding *bindings, be_u64 count,
		  be_u64 outbound_bytes)
{
	be_u64 block;

	if (desc == (struct be_mvp_block_desc *)0)
		return BE_MVP_BLOCK_NULL;
	*desc = (struct be_mvp_block_desc){ 0 };
	if (bindings == (const struct be_mvp_binding *)0)
		return BE_MVP_BLOCK_NULL;
	if (!be_mvp_bindings_valid(bindings, count))
		return BE_MVP_BLOCK_BINDING;
	if (domain >= count)
		return BE_MVP_BLOCK_DOMAIN;
	if (!ring_bytes_valid(outbound_bytes, BE_MVP_OUTBOUND_RING_BYTES))
		return BE_MVP_BLOCK_RINGS;
	block = be_mvp_block_hpa(domain);
	desc->hart = bindings[domain].hart;
	desc->domain = domain;
	desc->hgatp = be_mvp_hgatp(bindings[domain].vmid,
				   bindings[domain].root);
	desc->block = block;
	desc->stack_top = block + BE_MVP_BLOCK_STACK_TOP_OFFSET;
	desc->saved = block + BE_MVP_BLOCK_SAVED_OFFSET;
	desc->state = block + BE_MVP_BLOCK_STATE_OFFSET;
	desc->inbound = block + BE_MVP_BLOCK_INBOUND_OFFSET;
	desc->inbound_bytes = BE_MVP_INBOUND_RING_BYTES;
	desc->outbound = block + BE_MVP_BLOCK_OUTBOUND_OFFSET;
	desc->outbound_bytes = outbound_bytes;
	desc->input = block + BE_MVP_INPUT_RING_OFFSET;
	desc->input_bytes = BE_MVP_INPUT_RING_BYTES;
	return BE_MVP_BLOCK_OK;
}

enum be_mvp_block_error
be_mvp_block_check(const struct be_mvp_block_desc *desc, be_u64 hart_id,
		   be_u64 block, const struct be_mvp_binding *bindings,
		   be_u64 count)
{
	const struct be_mvp_binding *binding;
	be_u64 expected;

	if (desc == (const struct be_mvp_block_desc *)0 ||
	    bindings == (const struct be_mvp_binding *)0)
		return BE_MVP_BLOCK_NULL;
	if (!be_mvp_bindings_valid(bindings, count))
		return BE_MVP_BLOCK_BINDING;
	if (desc->generation != BE_MVP_GENERATION)
		return BE_MVP_BLOCK_GENERATION;
	if (desc->domain >= count)
		return BE_MVP_BLOCK_DOMAIN;
	binding = &bindings[desc->domain];
	if (desc->hart != binding->hart || hart_id != desc->hart)
		return BE_MVP_BLOCK_HART;
	expected = be_mvp_block_hpa(desc->domain);
	if (desc->block != expected || block != expected)
		return BE_MVP_BLOCK_ADDRESS;
	if (desc->stack_top != expected + BE_MVP_BLOCK_STACK_TOP_OFFSET ||
	    desc->saved != expected + BE_MVP_BLOCK_SAVED_OFFSET ||
	    desc->state != expected + BE_MVP_BLOCK_STATE_OFFSET ||
	    desc->inbound != expected + BE_MVP_BLOCK_INBOUND_OFFSET ||
	    desc->outbound != expected + BE_MVP_BLOCK_OUTBOUND_OFFSET ||
	    desc->input != expected + BE_MVP_INPUT_RING_OFFSET)
		return BE_MVP_BLOCK_OFFSETS;
	if (!ring_bytes_valid(desc->inbound_bytes,
			      BE_MVP_INBOUND_RING_BYTES) ||
	    !ring_bytes_valid(desc->outbound_bytes,
			      BE_MVP_OUTBOUND_RING_BYTES) ||
	    desc->input_bytes != BE_MVP_INPUT_RING_BYTES)
		return BE_MVP_BLOCK_RINGS;
	if (desc->hgatp != be_mvp_hgatp(binding->vmid, binding->root))
		return BE_MVP_BLOCK_HGATP;
	return BE_MVP_BLOCK_OK;
}

/* The first failure stays; NONE or an unknown class is recorded as
 * exception. */
static enum be_mvp_class control_fail(struct be_mvp_control *ctl,
				      enum be_mvp_class failure)
{
	if (ctl->failed != 0U)
		return ctl->failure;
	if (failure == BE_MVP_CLASS_NONE ||
	    (unsigned int)failure >= (unsigned int)BE_MVP_CLASS_COUNT)
		failure = BE_MVP_CLASS_EXCEPTION;
	ctl->failed = 1U;
	ctl->failure = failure;
	return failure;
}

void be_mvp_control_init(struct be_mvp_control *ctl, be_u64 start,
			 be_u64 budget, be_u64 ready_ticks)
{
	if (ctl == (struct be_mvp_control *)0)
		return;
	*ctl = (struct be_mvp_control){ 0 };
	ctl->start = start;
	ctl->budget = budget;
	ctl->ready_ticks = ready_ticks;
	if (budget == 0U || ready_ticks == 0U)
		(void)control_fail(ctl, BE_MVP_CLASS_EXCEPTION);
}

int be_mvp_control_started(struct be_mvp_control *ctl, be_u64 domain,
			   be_u64 hart)
{
	if (ctl == (struct be_mvp_control *)0 || ctl->failed != 0U)
		return 0;
	if (domain >= BE_MVP_DOMAINS || hart == BE_MVP_CONTROL_HART ||
	    ctl->domain[domain].phase != BE_MVP_DOMAIN_NONE ||
	    (ctl->domain[1U - domain].phase != BE_MVP_DOMAIN_NONE &&
	     ctl->domain[1U - domain].hart == hart)) {
		(void)control_fail(ctl, BE_MVP_CLASS_EXCEPTION);
		return 0;
	}
	ctl->domain[domain].phase = BE_MVP_DOMAIN_STARTED;
	ctl->domain[domain].hart = hart;
	return 1;
}

static void seal_windows(struct be_mvp_control *ctl,
			 const struct be_mvp_gstage_map *maps)
{
	be_u64 domain;

	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		ctl->window_gpa[domain] = maps[domain].gpa_base;
		ctl->window_bytes[domain] = maps[domain].size;
	}
	ctl->sealed = 1U;
}

/*
 * M1's channel record as the one page a DENIAL is checked against: each
 * endpoint's rights, and none for a domain the record does not name; no
 * page without a channel.
 */
int be_mvp_control_channel(struct be_mvp_control *ctl,
			   const struct be_mvp_gstage_map *maps,
			   const struct be_mvp_gstage_channel *channel)
{
	struct be_mvp_gstage_page *page;
	be_u64 domain;

	if (ctl == (struct be_mvp_control *)0 || ctl->failed != 0U)
		return 0;
	if (maps == (const struct be_mvp_gstage_map *)0 ||
	    channel == (const struct be_mvp_gstage_channel *)0) {
		(void)control_fail(ctl, BE_MVP_CLASS_EXCEPTION);
		return 0;
	}
	ctl->channel = *channel;
	ctl->page_count = 0U;
	if (channel->bytes != 0U) {
		page = &ctl->pages[0];
		*page = (struct be_mvp_gstage_page){ 0 };
		page->gpa = channel->gpa;
		page->hpa = channel->hpa;
		page->bytes = channel->bytes;
		page->kind = BE_MVP_PAGE_CHANNEL;
		page->writer = channel->writer_domain;
		page->reader = channel->reader_domain;
		for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
			page->rights[domain] =
				domain == channel->writer_domain ?
				channel->writer_rights :
				domain == channel->reader_domain ?
				channel->reader_rights : 0U;
		ctl->page_count = 1U;
	}
	seal_windows(ctl, maps);
	return 1;
}

int be_mvp_control_pages(struct be_mvp_control *ctl,
			 const struct be_mvp_gstage_map *maps,
			 const struct be_mvp_gstage_page *pages, be_u64 count)
{
	be_u64 index;

	if (ctl == (struct be_mvp_control *)0 || ctl->failed != 0U)
		return 0;
	if (maps == (const struct be_mvp_gstage_map *)0 ||
	    pages == (const struct be_mvp_gstage_page *)0 || count == 0U ||
	    count > BE_MVP_PAGES_MAX) {
		(void)control_fail(ctl, BE_MVP_CLASS_EXCEPTION);
		return 0;
	}
	ctl->channel = (struct be_mvp_gstage_channel){ 0 };
	for (index = 0U; index < count; ++index)
		ctl->pages[index] = pages[index];
	ctl->page_count = count;
	seal_windows(ctl, maps);
	return 1;
}

int be_mvp_control_mgmt(struct be_mvp_control *ctl,
			struct be_mvp_mgmt_state *mgmt,
			const struct be_mvp_mgmt_grant *grants, be_u64 count,
			int checked)
{
	if (ctl == (struct be_mvp_control *)0 || ctl->failed != 0U)
		return 0;
	if (mgmt == (struct be_mvp_mgmt_state *)0 ||
	    count > BE_MVP_MGMT_GRANTS_MAX ||
	    (grants == (const struct be_mvp_mgmt_grant *)0 && count != 0U) ||
	    (checked != 0 && checked != 1)) {
		(void)control_fail(ctl, BE_MVP_CLASS_EXCEPTION);
		return 0;
	}
	*mgmt = (struct be_mvp_mgmt_state){ 0 };
	mgmt->grants = grants;
	mgmt->count = count;
	mgmt->checked = (be_u32)checked;
	ctl->mgmt = mgmt;
	return 1;
}

static enum be_mvp_step invalid(struct be_mvp_control *ctl,
				struct be_mvp_step_result *result,
				enum be_mvp_class failure)
{
	result->step = BE_MVP_STEP_INVALID;
	result->failure = control_fail(ctl, failure);
	return result->step;
}

static int words_are(const struct be_mvp_record *record, be_u64 words)
{
	return record->length == words * WORD_BYTES;
}

static int line_printable(const struct be_mvp_record *record)
{
	be_u64 index;

	for (index = 0U; index < record->length; ++index)
		if (record->payload[index] < 0x20U ||
		    record->payload[index] > 0x7eU)
			return 0;
	return 1;
}

/*
 * The completion rule (planning/mvp-m2-plan.md, Q15): every domain shut
 * down or terminated; a paused one has not ended.
 */
static void complete(struct be_mvp_control *ctl,
		     struct be_mvp_step_result *result)
{
	be_u64 domain;

	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		if (ctl->domain[domain].phase != BE_MVP_DOMAIN_SHUTDOWN &&
		    ctl->domain[domain].phase != BE_MVP_DOMAIN_TERMINATED)
			return;
	ctl->done = 1U;
	result->done = 1U;
}

/*
 * The answer to the request pending on @target, which its transition or
 * its shutdown ends: @code, with the target's state @shown; the requester
 * waits no longer.
 */
static void settle(struct be_mvp_mgmt_state *mgmt, be_u64 target,
		   long code, enum be_mvp_target_state shown,
		   struct be_mvp_step_result *result)
{
	struct be_mvp_mgmt_domain *pending = &mgmt->domain[target];

	result->answer = 1U;
	result->requester = pending->by;
	result->seq = pending->seq;
	result->fid = pending->fid;
	result->target = target;
	result->result = code;
	result->shown = shown;
	result->requested = pending->time;
	mgmt->domain[pending->by].awaiting = 0U;
	pending->pending = 0U;
	pending->by = 0U;
	pending->fid = 0U;
	pending->seq = 0U;
	pending->time = 0U;
}

/*
 * SHUTDOWN: needs the PONG; names the ENTERED time, the lines drained, the
 * denials drained, and the management requests drained. A domain whose
 * own request awaits its answer cannot shut down: its hart waits for the
 * answer in HS. A request delivered to it that it shut down before taking
 * is answered invalid state, its target shut down.
 */
static enum be_mvp_step domain_shutdown(struct be_mvp_control *ctl,
					be_u64 domain,
					const struct be_mvp_record *record,
					struct be_mvp_step_result *result)
{
	struct be_mvp_domain_track *track = &ctl->domain[domain];
	struct be_mvp_mgmt_state *mgmt = ctl->mgmt;

	if (track->phase != BE_MVP_DOMAIN_ENTERED ||
	    !words_are(record, BE_MVP_SHUTDOWN_WORDS))
		return invalid(ctl, result, BE_MVP_CLASS_RING);
	if (track->ponged == 0U)
		return invalid(ctl, result, BE_MVP_CLASS_IPI);
	if (be_mvp_record_word(record, BE_MVP_SHUTDOWN_ENTERED) !=
		    track->entered ||
	    be_mvp_record_word(record, BE_MVP_SHUTDOWN_LINES) != track->lines ||
	    be_mvp_record_word(record, BE_MVP_SHUTDOWN_DENIALS) !=
		    track->denials ||
	    be_mvp_record_word(record, BE_MVP_SHUTDOWN_MGMT) !=
		    track->requests ||
	    (mgmt != (struct be_mvp_mgmt_state *)0 &&
	     mgmt->domain[domain].awaiting != 0U))
		return invalid(ctl, result, BE_MVP_CLASS_RING);
	track->phase = BE_MVP_DOMAIN_SHUTDOWN;
	track->shutdown = record->time;
	track->ring_peak = be_mvp_record_word(record,
					      BE_MVP_SHUTDOWN_RING_PEAK);
	if (mgmt != (struct be_mvp_mgmt_state *)0 &&
	    mgmt->domain[domain].pending != 0U)
		settle(mgmt, domain, BE_MVP_SBI_ERR_INVALID_STATE,
		       BE_MVP_TARGET_SHUTDOWN, result);
	complete(ctl, result);
	result->step = BE_MVP_STEP_SHUTDOWN;
	return result->step;
}

/* FAIL: any point after the start and before SHUTDOWN, with a class. */
static enum be_mvp_step domain_fail(struct be_mvp_control *ctl,
				    struct be_mvp_domain_track *track,
				    const struct be_mvp_record *record,
				    struct be_mvp_step_result *result)
{
	be_u64 failure = be_mvp_record_word(record, BE_MVP_FAIL_CLASS);

	if (track->phase == BE_MVP_DOMAIN_SHUTDOWN ||
	    record->length < WORD_BYTES ||
	    record->length > BE_MVP_FAIL_MAX_WORDS * WORD_BYTES ||
	    record->length % WORD_BYTES != 0U ||
	    failure == (be_u64)BE_MVP_CLASS_NONE ||
	    failure >= (be_u64)BE_MVP_CLASS_COUNT)
		return invalid(ctl, result, BE_MVP_CLASS_RING);
	track->phase = BE_MVP_DOMAIN_FAILED;
	result->step = BE_MVP_STEP_FAIL;
	result->failure = control_fail(ctl, (enum be_mvp_class)failure);
	return result->step;
}

/* The access fault a guest-page fault is delivered as, or 0: hart 0's own
 * statement of the mapping (planning/mvp-m1-plan.md, Q5). */
static be_u64 injected_cause(be_u64 cause)
{
	if (cause == BE_MVP_SCAUSE_FETCH_GUEST_PAGE_FAULT)
		return BE_MVP_SCAUSE_FETCH_ACCESS_FAULT;
	if (cause == BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT)
		return BE_MVP_SCAUSE_LOAD_ACCESS_FAULT;
	if (cause == BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT)
		return BE_MVP_SCAUSE_STORE_ACCESS_FAULT;
	return 0U;
}

static int within(be_u64 address, be_u64 base, be_u64 bytes)
{
	return bytes != 0U && address >= base && address - base < bytes;
}

/*
 * The rights the sealed pages give @domain at @gpa: those of the page that
 * holds it, 0 for a page the domain holds none of, as for no page.
 */
static be_u64 page_rights(const struct be_mvp_control *ctl, be_u64 domain,
			  be_u64 gpa)
{
	be_u64 index;

	for (index = 0U; index < ctl->page_count &&
			 index < BE_MVP_PAGES_MAX; ++index)
		if (within(gpa, ctl->pages[index].gpa,
			   ctl->pages[index].bytes))
			return ctl->pages[index].rights[domain];
	return 0U;
}

/*
 * DENIAL: between ENTERED and SHUTDOWN, once the loop has the windows and
 * the sealed channel or pages; the domain's next sequence number; the
 * injected cause its cause's access fault; the GPA its htval's and
 * stval's; its exit after the domain's entry and no later than its post;
 * and its kind the sealed pages' for its GPA.
 */
static enum be_mvp_step domain_denial(struct be_mvp_control *ctl,
				      be_u64 domain,
				      const struct be_mvp_record *record,
				      struct be_mvp_step_result *result)
{
	struct be_mvp_domain_track *track = &ctl->domain[domain];
	be_u64 cause = be_mvp_record_word(record, BE_MVP_DENIAL_CAUSE);
	be_u64 kind = be_mvp_record_word(record, BE_MVP_DENIAL_KIND);
	be_u64 gpa = be_mvp_record_word(record, BE_MVP_DENIAL_GPA);
	be_u64 htval = be_mvp_record_word(record, BE_MVP_DENIAL_HTVAL);
	be_u64 exit = be_mvp_record_word(record, BE_MVP_DENIAL_EXIT);
	be_u64 rights;
	int fits;

	if (ctl->sealed == 0U || track->phase != BE_MVP_DOMAIN_ENTERED ||
	    !words_are(record, BE_MVP_DENIAL_WORDS) ||
	    track->denials == ~BE_U64_C(0) ||
	    be_mvp_record_word(record, BE_MVP_DENIAL_SEQ) !=
		    track->denials + 1U ||
	    injected_cause(cause) == 0U ||
	    be_mvp_record_word(record, BE_MVP_DENIAL_INJECTED) !=
		    injected_cause(cause) ||
	    htval >= BE_MVP_HTVAL_LIMIT ||
	    gpa != (htval << BE_MVP_HTVAL_SHIFT |
		    (be_mvp_record_word(record, BE_MVP_DENIAL_STVAL) &
		     BE_MVP_GPA_LOW_MASK)) ||
	    exit < track->entered || exit > record->time)
		return invalid(ctl, result, BE_MVP_CLASS_RING);
	rights = page_rights(ctl, domain, gpa);
	/* Read-only: a store to a page the domain holds without write;
	 * unmapped: outside the domain's window and every page it holds. */
	if (kind == BE_MVP_DENIAL_READ_ONLY)
		fits = rights != 0U &&
		       cause == BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT &&
		       (rights & BE_MVP_GSTAGE_RIGHT_WRITE) == 0U;
	else
		fits = kind == BE_MVP_DENIAL_UNMAPPED && rights == 0U &&
		       !within(gpa, ctl->window_gpa[domain],
			       ctl->window_bytes[domain]);
	if (!fits)
		return invalid(ctl, result, BE_MVP_CLASS_RING);
	track->denials += 1U;
	result->step = BE_MVP_STEP_DENIAL;
	return result->step;
}

/*
 * A request's target as hart 0 sees it (planning/mvp-m2-plan.md, Q3):
 * ended, then pending while a request involves it, then paused, else
 * running.
 */
static enum be_mvp_target_state target_state(const struct be_mvp_control *ctl,
					     be_u64 target)
{
	const struct be_mvp_mgmt_domain *requests = &ctl->mgmt->domain[target];
	enum be_mvp_domain_phase phase = ctl->domain[target].phase;

	if (phase == BE_MVP_DOMAIN_SHUTDOWN)
		return BE_MVP_TARGET_SHUTDOWN;
	if (phase == BE_MVP_DOMAIN_TERMINATED)
		return BE_MVP_TARGET_TERMINATED;
	if (requests->pending != 0U || requests->awaiting != 0U)
		return BE_MVP_TARGET_PENDING;
	if (phase == BE_MVP_DOMAIN_PAUSED)
		return BE_MVP_TARGET_PAUSED;
	return BE_MVP_TARGET_RUNNING;
}

/*
 * MGMT_REQUEST (planning/mvp-m2-plan.md, "The management extension" and
 * Q14): from a running domain, pause or terminate, its next sequence
 * number, and none of its own outstanding. The request is outstanding
 * from here, so a request to the requester itself finds it pending. The
 * decision is be_mvp_mgmt_decide()'s, against the sealed grants, or, in
 * the no-grant-check variant, against a grant of both permissions from
 * the requester to the target; a decision is answered at once, a delivery
 * waits on its target.
 */
static enum be_mvp_step domain_request(struct be_mvp_control *ctl,
				       be_u64 domain,
				       const struct be_mvp_record *record,
				       struct be_mvp_step_result *result)
{
	struct be_mvp_domain_track *track = &ctl->domain[domain];
	struct be_mvp_mgmt_state *mgmt = ctl->mgmt;
	be_u64 fid = be_mvp_record_word(record, BE_MVP_MGMT_REQUEST_FID);
	be_u64 target = be_mvp_record_word(record, BE_MVP_MGMT_REQUEST_TARGET);
	be_u64 seq = be_mvp_record_word(record, BE_MVP_MGMT_REQUEST_SEQ);
	struct be_mvp_mgmt_grant all = {
		domain, target, BE_MVP_MGMT_PAUSE | BE_MVP_MGMT_TERMINATE,
	};
	enum be_mvp_target_state state = BE_MVP_TARGET_RUNNING;
	struct be_mvp_mgmt_domain *pending;
	long decision;

	if (mgmt == (struct be_mvp_mgmt_state *)0 ||
	    track->phase != BE_MVP_DOMAIN_ENTERED ||
	    !words_are(record, BE_MVP_MGMT_REQUEST_WORDS) ||
	    (fid != BE_MVP_SBI_MGMT_PAUSE &&
	     fid != BE_MVP_SBI_MGMT_TERMINATE) ||
	    track->requests == ~BE_U64_C(0) || seq != track->requests + 1U ||
	    mgmt->domain[domain].awaiting != 0U)
		return invalid(ctl, result, BE_MVP_CLASS_RING);
	track->requests = seq;
	mgmt->domain[domain].awaiting = 1U;
	if (target < BE_MVP_DOMAINS)
		state = target_state(ctl, target);
	if (mgmt->checked != 0U)
		decision = be_mvp_mgmt_decide(mgmt->grants, mgmt->count, domain,
					      fid, target, state);
	else
		decision = be_mvp_mgmt_decide(&all, 1U, domain, fid, target,
					      state);
	result->requester = domain;
	result->seq = seq;
	result->fid = fid;
	result->target = target;
	result->requested = record->time;
	if (decision != BE_MVP_MGMT_DELIVER) {
		mgmt->domain[domain].awaiting = 0U;
		result->answer = 1U;
		result->result = decision;
		result->shown = BE_MVP_TARGET_COUNT;
		result->step = BE_MVP_STEP_MGMT;
		return result->step;
	}
	pending = &mgmt->domain[target];
	pending->pending = 1U;
	pending->by = domain;
	pending->fid = fid;
	pending->seq = seq;
	pending->time = record->time;
	result->step = BE_MVP_STEP_DELIVER;
	return result->step;
}

/*
 * PAUSED or TERMINATED (planning/mvp-m2-plan.md, Q15): the answer to the
 * request pending on the domain, whose function it must be and whose
 * requester it must name; PAUSED from a running domain, TERMINATED from a
 * running or a paused one. Its requester is answered 0, the domain's state
 * shown; a terminated domain has ended.
 */
static enum be_mvp_step domain_transition(struct be_mvp_control *ctl,
					  be_u64 domain,
					  const struct be_mvp_record *record,
					  struct be_mvp_step_result *result)
{
	struct be_mvp_domain_track *track = &ctl->domain[domain];
	struct be_mvp_mgmt_state *mgmt = ctl->mgmt;
	int paused = record->type == BE_MVP_RECORD_PAUSED;
	const struct be_mvp_mgmt_domain *pending;

	if (mgmt == (struct be_mvp_mgmt_state *)0 ||
	    !words_are(record, BE_MVP_PAUSED_WORDS))
		return invalid(ctl, result, BE_MVP_CLASS_RING);
	pending = &mgmt->domain[domain];
	if (pending->pending == 0U ||
	    pending->fid != (paused ? BE_MVP_SBI_MGMT_PAUSE :
			     BE_MVP_SBI_MGMT_TERMINATE) ||
	    be_mvp_record_word(record, BE_MVP_PAUSED_BY) != pending->by ||
	    !(track->phase == BE_MVP_DOMAIN_ENTERED ||
	      (!paused && track->phase == BE_MVP_DOMAIN_PAUSED)))
		return invalid(ctl, result, BE_MVP_CLASS_RING);
	if (paused) {
		track->phase = BE_MVP_DOMAIN_PAUSED;
		settle(mgmt, domain, BE_MVP_SBI_SUCCESS, BE_MVP_TARGET_PAUSED,
		       result);
		result->step = BE_MVP_STEP_PAUSED;
		return result->step;
	}
	track->phase = BE_MVP_DOMAIN_TERMINATED;
	track->shutdown = record->time;
	settle(mgmt, domain, BE_MVP_SBI_SUCCESS, BE_MVP_TARGET_TERMINATED,
	       result);
	complete(ctl, result);
	result->step = BE_MVP_STEP_TERMINATED;
	return result->step;
}

static enum be_mvp_step apply(struct be_mvp_control *ctl, be_u64 domain,
			      const struct be_mvp_record *record,
			      struct be_mvp_step_result *result)
{
	struct be_mvp_domain_track *track = &ctl->domain[domain];

	switch (record->type) {
	case BE_MVP_RECORD_READY:
		if (track->phase != BE_MVP_DOMAIN_STARTED ||
		    !words_are(record, BE_MVP_READY_WORDS))
			return invalid(ctl, result, BE_MVP_CLASS_RING);
		track->phase = BE_MVP_DOMAIN_READY;
		result->step = BE_MVP_STEP_READY;
		return result->step;
	case BE_MVP_RECORD_ENTERED:
		if (track->phase != BE_MVP_DOMAIN_READY ||
		    !words_are(record, BE_MVP_ENTERED_WORDS))
			return invalid(ctl, result, BE_MVP_CLASS_RING);
		track->phase = BE_MVP_DOMAIN_ENTERED;
		track->entered = record->time;
		result->step = BE_MVP_STEP_ENTERED;
		return result->step;
	case BE_MVP_RECORD_LINE:
		if (track->phase != BE_MVP_DOMAIN_ENTERED ||
		    !line_printable(record))
			return invalid(ctl, result, BE_MVP_CLASS_RING);
		track->lines = add_saturating(track->lines, 1U);
		/* A domain a delivered request is about to stop is never
		 * asked: it may have parked before the PING. */
		if (track->pinged == 0U) {
			track->pinged = 1U;
			result->ping = 1U;
			if (ctl->mgmt != (struct be_mvp_mgmt_state *)0 &&
			    ctl->mgmt->domain[domain].pending != 0U)
				result->ping = 0U;
		}
		result->step = BE_MVP_STEP_LINE;
		return result->step;
	case BE_MVP_RECORD_PONG:
		if (track->phase != BE_MVP_DOMAIN_ENTERED ||
		    !words_are(record, BE_MVP_PONG_WORDS) ||
		    be_mvp_record_word(record, BE_MVP_PONG_SPV) > 1U)
			return invalid(ctl, result, BE_MVP_CLASS_RING);
		if (track->pinged == 0U || track->ponged != 0U)
			return invalid(ctl, result, BE_MVP_CLASS_IPI);
		track->ponged = 1U;
		result->step = BE_MVP_STEP_PONG;
		return result->step;
	case BE_MVP_RECORD_SHUTDOWN:
		return domain_shutdown(ctl, domain, record, result);
	case BE_MVP_RECORD_FAIL:
		return domain_fail(ctl, track, record, result);
	case BE_MVP_RECORD_DENIAL:
		return domain_denial(ctl, domain, record, result);
	case BE_MVP_RECORD_MGMT_REQUEST:
		return domain_request(ctl, domain, record, result);
	case BE_MVP_RECORD_PAUSED:
	case BE_MVP_RECORD_TERMINATED:
		return domain_transition(ctl, domain, record, result);
	default:
		return invalid(ctl, result, BE_MVP_CLASS_RING);
	}
}

enum be_mvp_step be_mvp_control_record(struct be_mvp_control *ctl,
				       be_u64 domain,
				       const struct be_mvp_record *record,
				       struct be_mvp_step_result *result)
{
	struct be_mvp_domain_track *track;
	enum be_mvp_step step;

	if (result == (struct be_mvp_step_result *)0) {
		if (ctl != (struct be_mvp_control *)0)
			(void)control_fail(ctl, BE_MVP_CLASS_EXCEPTION);
		return BE_MVP_STEP_INVALID;
	}
	*result = (struct be_mvp_step_result){ 0 };
	if (ctl == (struct be_mvp_control *)0) {
		result->failure = BE_MVP_CLASS_EXCEPTION;
		return BE_MVP_STEP_INVALID;
	}
	if (ctl->failed != 0U)
		return invalid(ctl, result, ctl->failure);
	if (record == (const struct be_mvp_record *)0 ||
	    domain >= BE_MVP_DOMAINS)
		return invalid(ctl, result, BE_MVP_CLASS_EXCEPTION);
	track = &ctl->domain[domain];
	if (ctl->done != 0U || record->domain != domain ||
	    record->length > BE_MVP_RECORD_PAYLOAD_MAX ||
	    track->phase == BE_MVP_DOMAIN_NONE || record->time < track->last)
		return invalid(ctl, result, BE_MVP_CLASS_RING);
	step = apply(ctl, domain, record, result);
	if (step == BE_MVP_STEP_INVALID)
		return step;
	track->last = record->time;
	track->records = add_saturating(track->records, 1U);
	ctl->records = add_saturating(ctl->records, 1U);
	return step;
}

enum be_mvp_class be_mvp_control_wake(struct be_mvp_control *ctl,
				      be_u64 now)
{
	be_u64 elapsed;
	be_u64 index;

	if (ctl == (struct be_mvp_control *)0)
		return BE_MVP_CLASS_EXCEPTION;
	if (ctl->failed != 0U)
		return ctl->failure;
	ctl->wakes = add_saturating(ctl->wakes, 1U);
	if (ctl->done != 0U ||
	    ctl->domain[0].phase == BE_MVP_DOMAIN_NONE ||
	    ctl->domain[1].phase == BE_MVP_DOMAIN_NONE)
		return control_fail(ctl, BE_MVP_CLASS_EXCEPTION);
	/* A clock behind the start cannot measure the budget. */
	if (now < ctl->start)
		return control_fail(ctl, BE_MVP_CLASS_RUN_TIMEOUT);
	elapsed = now - ctl->start;
	for (index = 0U; index < BE_MVP_DOMAINS; ++index)
		if (ctl->domain[index].phase == BE_MVP_DOMAIN_STARTED &&
		    elapsed >= ctl->ready_ticks)
			return control_fail(ctl, BE_MVP_CLASS_HART_READY);
	if (elapsed >= ctl->budget)
		return control_fail(ctl, BE_MVP_CLASS_RUN_TIMEOUT);
	return BE_MVP_CLASS_NONE;
}

be_u64 be_mvp_control_running(const struct be_mvp_control *ctl)
{
	be_u64 running = 0U;
	be_u64 index;

	if (ctl == (const struct be_mvp_control *)0 || ctl->failed != 0U ||
	    ctl->done != 0U)
		return 0U;
	for (index = 0U; index < BE_MVP_DOMAINS; ++index) {
		enum be_mvp_domain_phase phase = ctl->domain[index].phase;

		if (phase != BE_MVP_DOMAIN_STARTED &&
		    phase != BE_MVP_DOMAIN_READY &&
		    phase != BE_MVP_DOMAIN_ENTERED)
			continue;
		if (ctl->mgmt != (struct be_mvp_mgmt_state *)0 &&
		    ctl->mgmt->domain[index].pending != 0U)
			continue;
		running |= BE_U64_C(1) << index;
	}
	return running;
}

void be_mvp_control_waited(struct be_mvp_control *ctl, be_u64 ticks)
{
	if (ctl == (struct be_mvp_control *)0)
		return;
	ctl->idle_ticks = add_saturating(ctl->idle_ticks, ticks);
}

void be_mvp_drain_begin(struct be_mvp_drain *drain, be_u32 rings,
			be_u64 capacity)
{
	if (drain == (struct be_mvp_drain *)0)
		return;
	*drain = (struct be_mvp_drain){ 0 };
	if (rings == 0U || rings > BE_MVP_DOMAINS ||
	    !ring_bytes_valid(capacity, BE_MVP_OUTBOUND_RING_BYTES))
		return;
	drain->rings = rings;
	drain->visits = rings * (capacity / BE_MVP_RECORD_HEADER_BYTES + 1U);
}

be_u32 be_mvp_drain_next(const struct be_mvp_drain *drain)
{
	if (drain == (const struct be_mvp_drain *)0 || drain->visits == 0U ||
	    drain->idle >= drain->rings || drain->next >= drain->rings)
		return BE_MVP_DRAIN_DONE;
	return drain->next;
}

void be_mvp_drain_visited(struct be_mvp_drain *drain, int took)
{
	if (be_mvp_drain_next(drain) == BE_MVP_DRAIN_DONE)
		return;
	drain->visits -= 1U;
	drain->idle = took != 0 ? 0U : drain->idle + 1U;
	drain->next = drain->next + 1U < drain->rings ? drain->next + 1U : 0U;
}

int be_mvp_overlap(be_u64 entered0, be_u64 shutdown0, be_u64 entered1,
		   be_u64 shutdown1, be_u64 *overlap, be_u64 *shorter)
{
	be_u64 low;
	be_u64 high;
	be_u64 length0;
	be_u64 length1;

	if (overlap == (be_u64 *)0 || shorter == (be_u64 *)0 ||
	    shutdown0 <= entered0 || shutdown1 <= entered1)
		return 0;
	length0 = shutdown0 - entered0;
	length1 = shutdown1 - entered1;
	low = entered0 > entered1 ? entered0 : entered1;
	high = shutdown0 < shutdown1 ? shutdown0 : shutdown1;
	*overlap = high > low ? high - low : 0U;
	*shorter = length0 < length1 ? length0 : length1;
	return 1;
}

int be_mvp_concurrent(be_u64 overlap, be_u64 shorter)
{
	if (shorter == 0U || overlap > shorter)
		return 0;
	/* At least half: overlap >= ceil(shorter / 2), with no overflow. */
	return overlap >= shorter - shorter / 2U;
}

int be_mvp_control_overlap(const struct be_mvp_control *ctl,
			   be_u64 *overlap)
{
	be_u64 value;
	be_u64 shorter;

	if (overlap == (be_u64 *)0)
		return 0;
	*overlap = 0U;
	if (ctl == (const struct be_mvp_control *)0 || ctl->failed != 0U ||
	    ctl->done == 0U ||
	    !be_mvp_overlap(ctl->domain[0].entered, ctl->domain[0].shutdown,
			    ctl->domain[1].entered, ctl->domain[1].shutdown,
			    &value, &shorter))
		return 0;
	*overlap = value;
	return be_mvp_concurrent(value, shorter);
}

be_u64 be_mvp_line_output(const struct be_mvp_record *record, char *output,
			  be_u64 capacity)
{
	const char *prefix = BE_MVP_G0_PREFIX;
	be_u64 length = 0U;
	be_u64 index;

	if (record == (const struct be_mvp_record *)0 ||
	    output == (char *)0 || record->type != BE_MVP_RECORD_LINE ||
	    record->domain >= BE_MVP_DOMAINS ||
	    record->length > BE_MVP_CONSOLE_LINE_BYTES ||
	    capacity < BE_MVP_DOMAIN_PREFIX_LENGTH + record->length + 1U ||
	    !line_printable(record))
		return BE_MVP_CONSOLE_INVALID;
	if (record->domain == 1U)
		prefix = BE_MVP_G1_PREFIX;
	for (index = 0U; index < BE_MVP_DOMAIN_PREFIX_LENGTH; ++index)
		output[length++] = prefix[index];
	for (index = 0U; index < record->length; ++index)
		output[length++] = (char)record->payload[index];
	output[length++] = '\n';
	return length;
}
