// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP domain hart runtime (planning/mvp-m0-plan.md, "Domain hart
 *          entry and fast path" and "Failure paths"): a started hart's check
 *          of its published block, its arming, the install of its domain's
 *          root, READY and ENTERED, and the first entry; then the service of
 *          each exit through the pure-C SBI core: SBI calls, the console's
 *          LINE records, the IPI's PING and PONG, in an image that accepts
 *          denials an accepted denial's injection and DENIAL record
 *          (planning/mvp-m1-plan.md, "The denial path"), in an image that
 *          accepts the management extension a management call's request
 *          and its wait in HS for hart 0's answer, and hart 0's PAUSE and
 *          TERMINATE with the paused and terminated parks
 *          (planning/mvp-m2-plan.md, "The management extension"), the
 *          domain's shutdown, and the hart's FAIL, with its own lines when
 *          hart 0 makes no progress on its ring and does not acknowledge
 *          it (Q10 as revised by Plan revision M1-B); since M7, a granted
 *          DBCN read served from the hart's input ring through its stage
 *          (planning/mvp-m7-plan.md, D-1), and a paused or terminated
 *          domain's partial line flushed before it parks (Q9).
 * Trust:   privileged restricted-C orchestration on a domain hart. Every CSR
 *          access, fence, and the SRET tail stay in assembly; the hart's one
 *          hgatp write and hfence.gvma are the accepted R3 install
 *          function's, called here once. This runtime reaches each of these
 *          effects, and each SBI call, only through the executor
 *          (mvp-executor.c; planning/mvp-m6-plan.md, D-5) and performs none
 *          itself. Its fast path reads and writes only its own block: its
 *          state page, its saved page, the outbound ring it writes, and the
 *          inbound and input rings it reads; it takes no lock and no atomic
 *          read-modify-write, only fences. Guest bytes are read, and since
 *          M7 written, only through a translation the SBI core derived from
 *          its domain's walked window for the guest's whole range. It names
 *          none of hart 0's own state: not the measurement, the grants, the
 *          management state, or the console input's routing, which hart 0
 *          alone decides with (the image checker's rule).
 * Scope:   the MVP line's domain harts. Hart IDs and domain indices are
 *          identifiers, not authority (S1 H03); the block hart 0 published
 *          and the root installed once are the hart's authority. In the
 *          probe images, the probe handler (mvp-probe.c) serves every exit.
 */
#include "mvp-platform.h"

#include "mvp-executor.h"
#include "mvp-input.h"
#include "mvp-ring.h"
#include "mvp-sbi.h"
#if defined(BE_MVP_PROBE_IMAGE)
#include "mvp-probe.h"
#endif

/* A domain hart's own console lines when hart 0 cannot print its FAIL. */
#define BE_MVP_FALLBACK_ATTEMPTS	64U

static const char hart_failure[] = "BE_MVP:FAIL ";
static const char hart_newline[] = "\n";

static be_u64 symbol_address(const be_u8 *symbol)
{
	return (be_u64)symbol;
}

/* The state page of the block at @block, when it is one of the region's. */
static struct be_mvp_hart_page *hart_page(be_u64 block)
{
	be_u64 domain;

	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		if (block == be_mvp_block_hpa(domain))
			return (struct be_mvp_hart_page *)(void *)(block +
				BE_MVP_BLOCK_STATE_OFFSET);
	return (struct be_mvp_hart_page *)0;
}

/* Writer: the records' bytes before the head that admits them. */
static int publish(struct be_mvp_hart_page *page)
{
	be_mvp_exec_fence_w_w();
	return be_mvp_ring_publish(&page->outbound);
}

/* The domain hart's records wait in its ring; one IPI wakes hart 0. */
static void tell_control_hart(void)
{
	(void)be_mvp_send_ipi(BE_MVP_CONTROL_HART);
}

/*
 * Whether hart 0's ACK is in the inbound ring. Nothing is released: the
 * hart parks either way.
 */
static int acknowledged(struct be_mvp_hart_page *page)
{
	struct be_mvp_record record;
	be_u64 index;

	if (be_mvp_ring_acquire(&page->inbound) == 0U)
		return 0;
	/* Reader: the head, then the records it admits. */
	be_mvp_exec_fence_r_r();
	for (index = 0U; index <= page->inbound.capacity /
			 BE_MVP_RECORD_HEADER_BYTES; ++index) {
		if (be_mvp_ring_take(&page->inbound, &record) !=
		    BE_MVP_RING_RECORD)
			return 0;
		if (record.type == BE_MVP_RECORD_ACK)
			return 1;
	}
	return 0;
}

/*
 * One fallback line through DBCN from this hart's own stack, never the
 * diagnostic page hart 0 writes; each line is one call when the firmware
 * takes it whole.
 */
static void fallback_write(const struct be_mvp_line *line)
{
	be_u64 offset = 0U;
	be_u64 attempt;

	if (line->overflow != 0U)
		return;
	for (attempt = 0U; attempt < BE_MVP_FALLBACK_ATTEMPTS &&
			   offset < line->length; ++attempt) {
		be_u64 address = (be_u64)(const void *)&line->text[offset];
		be_u64 written = 0U;

		if (be_mvp_exec_dbcn_write(line->length - offset, address,
					   &written) != BE_MVP_SBI_SUCCESS ||
		    written > line->length - offset)
			return;
		offset += written;
	}
}

/*
 * The domain hart's terminal path (Q10, as Plan revision M1-B revises it):
 * its partial line, then FAIL with its detail and one IPI, then the wait
 * for hart 0's ACK, which parks the hart. The wait's 2^24-tick window
 * restarts each time hart 0 takes a record from the hart's outbound ring
 * (be_mvp_ack_wait_step()), so it measures hart 0's progress, not its
 * latency behind a slow console. A ring that cannot carry the FAIL, a
 * window with neither an ACK nor a record taken, or a malformed tail, and
 * the hart prints its own FAIL and DETAIL lines and requests SRST, so a
 * wedged hart 0 cannot hide the failure.
 */
static void hart_fail(struct be_mvp_hart_page *page, enum be_mvp_class failure,
		      const be_u64 *detail, be_u64 words)
	__attribute__((noreturn));
static void hart_fail(struct be_mvp_hart_page *page, enum be_mvp_class failure,
		      const be_u64 *detail, be_u64 words)
{
	struct be_mvp_state *state = &page->page.state;
	struct be_mvp_ack_wait wait;
	enum be_mvp_ack_step step;
	struct be_mvp_line line;

	failure = be_mvp_fail(state, failure);
	(void)be_mvp_console_flush(state, &page->outbound,
				   be_mvp_exec_read_time());
	if (be_mvp_post_fail(state, &page->outbound, detail, words,
			     be_mvp_exec_read_time()) && publish(page)) {
		tell_control_hart();
		be_mvp_ack_wait_start(&wait, be_mvp_exec_read_time(),
				      be_mvp_ring_taken(&page->outbound));
		do {
			int ack = acknowledged(page);

			step = be_mvp_ack_wait_step(&wait,
				be_mvp_exec_read_time(),
				be_mvp_ring_taken(&page->outbound),
				be_mvp_ring_published(&page->outbound), ack);
			if (step == BE_MVP_ACK_PARK)
				be_mvp_exec_park();
		} while (step == BE_MVP_ACK_WAIT);
	}
	be_mvp_line_reset(&line);
	be_mvp_line_text(&line, hart_failure);
	be_mvp_line_text(&line, be_mvp_class_name(failure));
	be_mvp_line_text(&line, hart_newline);
	fallback_write(&line);
	be_mvp_detail_line(&line, failure, page->page.desc.domain,
			   page->page.desc.hart, detail, words);
	fallback_write(&line);
	(void)be_mvp_exec_system_reset();
	be_mvp_exec_park();
}

/* One register that did not read back as written. */
static void register_fail(struct be_mvp_hart_page *page,
			  enum be_mvp_class failure, be_u64 id, be_u64 wanted,
			  be_u64 readback) __attribute__((noreturn));
static void register_fail(struct be_mvp_hart_page *page,
			  enum be_mvp_class failure, be_u64 id, be_u64 wanted,
			  be_u64 readback)
{
	be_u64 detail[BE_MVP_DETAIL_REGISTER_WORDS] = { id, wanted, readback };

	hart_fail(page, failure, detail, BE_MVP_DETAIL_REGISTER_WORDS);
}

/* A failure decided on an exit names the exit. */
static void exit_fail(struct be_mvp_hart_page *page,
		      const struct be_mvp_exit *record,
		      enum be_mvp_class failure) __attribute__((noreturn));
static void exit_fail(struct be_mvp_hart_page *page,
		      const struct be_mvp_exit *record,
		      enum be_mvp_class failure)
{
	be_u64 detail[BE_MVP_DETAIL_EXIT_WORDS] = {
		record->frame.scause, record->frame.sepc, record->frame.stval,
		record->frame.htval, record->htinst,
		be_mvp_record_spp(record) != 0U ? 1U : 0U, record->vsatp,
		page->page.state.counts.exits,
	};

	hart_fail(page, failure, detail, BE_MVP_DETAIL_EXIT_WORDS);
}

void be_mvp_hart_terminal(struct be_mvp_exit *record,
			  enum be_mvp_class failure)
{
	struct be_mvp_hart_page *page =
		hart_page((be_u64)(void *)record - BE_MVP_BLOCK_SAVED_OFFSET);

	if (page == (struct be_mvp_hart_page *)0)
		be_mvp_exec_park();
	exit_fail(page, record, failure);
}

#if defined(BE_MVP_PROBE_IMAGE)
/* In the probe images, the probe handler serves the VS probe stub. */
void be_mvp_dispatch(struct be_mvp_exit *record)
{
	struct be_mvp_hart_page *page =
		hart_page((be_u64)(void *)record - BE_MVP_BLOCK_SAVED_OFFSET);

	if (page == (struct be_mvp_hart_page *)0)
		be_mvp_exec_park();
	be_mvp_probe_exit(page, record);
}
#else
/* The domain's bytes, as LINE records; one IPI when a line ended. */
static void console(struct be_mvp_hart_page *page,
		    const struct be_mvp_exit *record, const be_u8 *bytes,
		    be_u64 length)
{
	be_u64 posted = be_mvp_console_feed(&page->page.state, &page->outbound,
					    bytes, length,
					    be_mvp_exec_read_time());

	if (posted == BE_MVP_CONSOLE_INVALID || posted == BE_MVP_CONSOLE_FULL)
		exit_fail(page, record, BE_MVP_CLASS_CONSOLE);
	if (posted == 0U)
		return;
	if (!publish(page))
		exit_fail(page, record, BE_MVP_CLASS_RING);
	tell_control_hart();
}

/* Copy DBCN bytes from the domain's window; firmware never sees them. */
static void console_write(struct be_mvp_hart_page *page,
			  const struct be_mvp_exit *record,
			  const struct be_mvp_result *result)
{
	const volatile be_u8 *source =
		(const volatile be_u8 *)(void *)result->source_pa;
	be_u8 bytes[BE_MVP_DBCN_MAX_BYTES];
	be_u64 index;

	if (result->length > BE_MVP_DBCN_MAX_BYTES)
		exit_fail(page, record, BE_MVP_CLASS_CONSOLE);
	for (index = 0U; index < result->length; ++index)
		bytes[index] = source[index];
	console(page, record, bytes, result->length);
}

/*
 * A granted DBCN read (planning/mvp-m7-plan.md, D-1), after
 * be_mvp_handle_exit() checked a2 and the guest's whole buffer inside the
 * window (the write-authority rule): the hart's staged input, then INPUT
 * records from its input ring, copied through the window's HS physical
 * address, at most the result's length, min(a0, 256); the count becomes
 * the guest's a1. The reader's fences, as for the inbound ring; no record
 * posted, no IPI. A malformed ring or record fails the hart as ring.
 */
static void console_read(struct be_mvp_hart_page *page,
			 const struct be_mvp_exit *record,
			 struct be_mvp_result *result)
{
	be_u64 copied;

	(void)be_mvp_ring_acquire(&page->input);
	/* Reader: the head, then the records it admits. */
	be_mvp_exec_fence_r_r();
	copied = be_mvp_input_serve(&page->stage, &page->input,
				    (be_u8 *)(void *)result->target_pa,
				    result->length);
	if (copied == BE_MVP_INPUT_FAILED)
		exit_fail(page, record, BE_MVP_CLASS_RING);
	/* Reader: every copy out before the tail that frees the bytes. */
	be_mvp_exec_fence_r_w();
	if (!be_mvp_ring_release(&page->input))
		exit_fail(page, record, BE_MVP_CLASS_RING);
	result->value = copied;
}

#if BE_MVP_RUN_ACCEPT_MGMT
/*
 * The inbound ring read in HS, outside an exit (be_mvp_wait_serve()), with
 * the reader's fences: a waiting hart's PING and MGMT_RESULT, a paused
 * hart's TERMINATE; then any answer published, and hart 0 told.
 */
static void wait_serve(struct be_mvp_hart_page *page,
		       const struct be_mvp_exit *record)
{
	be_u64 posted = 0U;
	int served;

	(void)be_mvp_ring_acquire(&page->inbound);
	/* Reader: the head, then the records it admits. */
	be_mvp_exec_fence_r_r();
	served = be_mvp_wait_serve(&page->page.state, &page->inbound,
				   &page->outbound, be_mvp_exec_read_time(),
				   &posted);
	if (!served)
		exit_fail(page, record, BE_MVP_CLASS_IPI);
	/* Reader: every copy out before the tail that frees the bytes. */
	be_mvp_exec_fence_r_w();
	if (!be_mvp_ring_release(&page->inbound) ||
	    (posted != 0U && !publish(page)))
		exit_fail(page, record, BE_MVP_CLASS_RING);
	if (posted != 0U)
		tell_control_hart();
}

/*
 * A paused or terminated domain (planning/mvp-m2-plan.md, Q4 and Q15): its
 * guest's state stays in the saved page, never restored. The hart waits in
 * HS for each IPI, clears it, and reads its inbound ring: a paused hart
 * takes a TERMINATE, answered with TERMINATED, and parks on as terminated;
 * any other record, or any record once terminated, fails the hart as ipi;
 * a wake that finds the ring empty waits again.
 */
static void parked(struct be_mvp_hart_page *page,
		   const struct be_mvp_exit *record) __attribute__((noreturn));
static void parked(struct be_mvp_hart_page *page,
		   const struct be_mvp_exit *record)
{
	for (;;) {
		(void)be_mvp_exec_wait(BE_MVP_SIE_SSIE);
		(void)be_mvp_exec_clear_ssip();
		wait_serve(page, record);
	}
}
#endif

/*
 * The IPI: clear SSIP before reading the inbound ring, so a later IPI is
 * never lost; answer each PING with a PONG, and in an image that accepts
 * the management extension a PAUSE or TERMINATE with PAUSED or TERMINATED;
 * release, publish, and tell hart 0. A hart that hart 0 has now paused or
 * terminated parks.
 */
static void ipi(struct be_mvp_hart_page *page, const struct be_mvp_exit *record)
{
	(void)be_mvp_exec_clear_ssip();
	(void)be_mvp_ring_acquire(&page->inbound);
	/* Reader: the head, then the records it admits. */
	be_mvp_exec_fence_r_r();
	if (be_mvp_ipi_serve(&page->page.state, &page->inbound,
			     &page->outbound, record,
			     be_mvp_exec_read_time()) == 0U)
		exit_fail(page, record, BE_MVP_CLASS_IPI);
	/* Reader: every copy out before the tail that frees the bytes. */
	be_mvp_exec_fence_r_w();
	if (!be_mvp_ring_release(&page->inbound) || !publish(page))
		exit_fail(page, record, BE_MVP_CLASS_RING);
	tell_control_hart();
#if BE_MVP_RUN_ACCEPT_MGMT
	if (page->page.state.phase == BE_MVP_PHASE_PAUSED ||
	    page->page.state.phase == BE_MVP_PHASE_TERMINATED)
		parked(page, record);
#endif
}

/* The domain's shutdown: its partial line, SHUTDOWN, and the park. */
static void stopped(struct be_mvp_hart_page *page,
		    const struct be_mvp_exit *record) __attribute__((noreturn));
static void stopped(struct be_mvp_hart_page *page,
		    const struct be_mvp_exit *record)
{
	be_u64 now = be_mvp_exec_read_time();
	be_u64 flushed = be_mvp_console_flush(&page->page.state,
					      &page->outbound, now);

	if (flushed == BE_MVP_CONSOLE_INVALID ||
	    flushed == BE_MVP_CONSOLE_FULL ||
	    !be_mvp_post_shutdown(&page->page.state, &page->outbound,
				  page->page.entered, now) ||
	    !publish(page))
		exit_fail(page, record, BE_MVP_CLASS_RING);
	tell_control_hart();
	be_mvp_exec_park();
}

#if BE_MVP_RUN_ACCEPT_MGMT
/*
 * A management call (planning/mvp-m2-plan.md, "The management extension"
 * and Q14), after be_mvp_handle_exit() counted it: MGMT_REQUEST posted,
 * published, and announced to hart 0 by one IPI (else ring); then the
 * wait in HS for its MGMT_RESULT. The inbound ring is read only once the
 * SSIP helper's readback shows an IPI arrived, and hart 0 sends one after
 * each record it publishes, so every record read here has had its IPI
 * consumed, and none reaches the guest after its record; a PING found
 * meanwhile is answered with its PONG. The wait's 2^24-tick window
 * restarts each time hart 0 takes a record from the hart's outbound ring
 * (be_mvp_ack_wait_step(), M1-B's), so it measures hart 0's progress, not
 * its latency behind a slow console; a window with neither progress nor
 * the answer fails the hart as mgmt. The answer becomes the result's a0,
 * which the dispatch writes into the frame before it resumes the guest
 * after the ecall; no CSR is written but sip's SSIP clear.
 */
static void mgmt_call(struct be_mvp_hart_page *page,
		      const struct be_mvp_exit *record,
		      struct be_mvp_result *result)
{
	struct be_mvp_state *state = &page->page.state;
	struct be_mvp_ack_wait wait;
	enum be_mvp_ack_step step;

	if (!be_mvp_post_mgmt_request(state, &page->outbound, result,
				      be_mvp_exec_read_time()) ||
	    !publish(page))
		exit_fail(page, record, BE_MVP_CLASS_RING);
	tell_control_hart();
	be_mvp_ack_wait_start(&wait, be_mvp_exec_read_time(),
			      be_mvp_ring_taken(&page->outbound));
	do {
		if ((be_mvp_exec_clear_ssip() & BE_MVP_SIE_SSIE) != 0U)
			wait_serve(page, record);
		if (state->awaiting == 0U) {
			result->error = (long)state->answer;
			result->value = 0U;
			return;
		}
		step = be_mvp_ack_wait_step(&wait, be_mvp_exec_read_time(),
			be_mvp_ring_taken(&page->outbound),
			be_mvp_ring_published(&page->outbound), 0);
	} while (step == BE_MVP_ACK_WAIT);
	exit_fail(page, record, BE_MVP_CLASS_MGMT);
}
#endif

#if BE_MVP_RUN_ACCEPT_DENIAL
/*
 * An accepted denial (planning/mvp-m1-plan.md, "The denial path"), in the
 * plan's order, after be_mvp_handle_exit() counted the exit and the denial:
 * the injection helper writes vscause, vstval, vsepc, and vsstatus and
 * reads each back, and every readback must equal its value (else controls,
 * with a register DETAIL); one DENIAL record is posted, published, and
 * announced to hart 0 by one IPI (else ring, by M0's fallback path); then
 * the frame's sepc becomes the guest's trap vector and the saved SPVP VS,
 * so that M0's resume tail enters VS mode there. No hgatp write, no fence
 * beyond the publish, no lock, and no other hart's block.
 */
static void deny(struct be_mvp_hart_page *page, struct be_mvp_exit *record,
		 const struct be_mvp_denial *denial)
{
	be_u64 written[BE_MVP_INJECT_WORDS];
	be_u64 readback[BE_MVP_INJECT_WORDS];
	be_u32 index;

	be_mvp_inject_words(denial, written);
	be_mvp_exec_inject(written[BE_MVP_INJECT_VSCAUSE],
			   written[BE_MVP_INJECT_VSTVAL],
			   written[BE_MVP_INJECT_VSEPC],
			   written[BE_MVP_INJECT_VSSTATUS], readback);
	index = be_mvp_inject_mismatch(written, readback);
	if (index != BE_MVP_INJECT_WORDS)
		register_fail(page, BE_MVP_CLASS_CONTROLS,
			      BE_MVP_REGISTER_VCSR + be_mvp_inject_vcsr(index),
			      written[index], readback[index]);
	if (!be_mvp_post_denial(&page->page.state, &page->outbound, denial,
				be_mvp_exec_read_time()) ||
	    !publish(page))
		exit_fail(page, record, BE_MVP_CLASS_RING);
	tell_control_hart();
	record->frame.sepc = denial->resume_pc;
	record->hstatus |= BE_MVP_HSTATUS_SPVP;
}
#endif

void be_mvp_dispatch(struct be_mvp_exit *record)
{
	struct be_mvp_hart_page *page =
		hart_page((be_u64)(void *)record - BE_MVP_BLOCK_SAVED_OFFSET);
	struct be_mvp_result result;

	if (page == (struct be_mvp_hart_page *)0)
		be_mvp_exec_park();
	switch (be_mvp_handle_exit(&page->page.state, &page->map,
				   &page->leaves, record, &result)) {
	case BE_MVP_ACTION_RETURN:
		break;
	case BE_MVP_ACTION_CONSOLE_WRITE:
		console_write(page, record, &result);
		break;
	case BE_MVP_ACTION_CONSOLE_BYTE:
		console(page, record, &result.byte, 1U);
		break;
	case BE_MVP_ACTION_CONSOLE_READ:
		console_read(page, record, &result);
		break;
	case BE_MVP_ACTION_SET_TIMER:
		be_mvp_exec_set_timer(result.timer);
		break;
	case BE_MVP_ACTION_IPI:
		ipi(page, record);
		break;
#if BE_MVP_RUN_ACCEPT_DENIAL
	case BE_MVP_ACTION_DENY:
		deny(page, record, &result.denial);
		break;
#endif
#if BE_MVP_RUN_ACCEPT_MGMT
	case BE_MVP_ACTION_MGMT:
		mgmt_call(page, record, &result);
		break;
#endif
	case BE_MVP_ACTION_SHUTDOWN:
		stopped(page, record);
	case BE_MVP_ACTION_GUEST_FAILURE:
	case BE_MVP_ACTION_GUEST_REBOOT:
	case BE_MVP_ACTION_NONE:
	case BE_MVP_ACTION_TERMINAL:
	default:
		exit_fail(page, record, result.failure);
	}
	be_mvp_apply_return(&record->frame, &result);
	be_mvp_exec_resume(record, page->page.desc.hgatp,
			   page->page.controls.hedeleg);
}
#endif

/* The armed readbacks READY would have carried, for a controls FAIL. */
static void controls_fail(struct be_mvp_hart_page *page)
	__attribute__((noreturn));
static void controls_fail(struct be_mvp_hart_page *page)
{
	const struct be_mvp_controls *controls = &page->page.controls;
	be_u64 detail[BE_MVP_DETAIL_EXIT_WORDS] = {
		controls->hgatp,
		controls->hstatus & BE_R3_HSTATUS_CONTROL_MASK,
		controls->hedeleg, controls->hideleg, controls->hcounteren,
		controls->sie, controls->henvcfg, controls->vstimecmp,
	};

	hart_fail(page, BE_MVP_CLASS_CONTROLS, detail,
		  BE_MVP_DETAIL_EXIT_WORDS);
}

void be_mvp_hart_main(be_u64 hart_id, be_u64 block)
{
	struct be_mvp_hart_page *page = hart_page(block);
	struct be_mvp_exit *record = (struct be_mvp_exit *)(void *)(block +
		BE_MVP_BLOCK_SAVED_OFFSET);
	be_u64 top = block + BE_MVP_BLOCK_STACK_TOP_OFFSET;
	struct be_mvp_state_page *state;
	struct be_r3_hs_state hs;
	be_u64 vcsr[BE_MVP_VCSR_COUNT];
	be_u64 readback[BE_MVP_VCSR_COUNT];
	enum be_mvp_class failure;
	be_u64 value;
	be_u32 index;

	/* Before the console exists, a block that fails its check parks. */
	if (page == (struct be_mvp_hart_page *)0)
		be_mvp_exec_park();
	state = &page->page;
	/* The barrier: the generation word first, then what it publishes. */
	if (*(volatile be_u64 *)&state->desc.generation != BE_MVP_GENERATION)
		be_mvp_exec_park();
	be_mvp_exec_fence_r_r();
	/* The SBI core's state and this hart's ring views are hart 0's work
	 * before the barrier; from here on they are this hart's. */
	if (be_mvp_block_check(&state->desc, hart_id, block, be_mvp_bindings,
			       BE_MVP_DOMAINS) != BE_MVP_BLOCK_OK ||
	    state->state.phase != BE_MVP_PHASE_RUNNING ||
	    page->inbound.failed != 0U || page->outbound.failed != 0U ||
	    page->input.failed != 0U)
		be_mvp_exec_park();

	be_mvp_exec_reset_hs_state(symbol_address(be_mvp_trap_vector), &hs);
	value = be_mvp_exec_arm_stce();
	failure = be_mvp_stce_class(value);
	if (failure != BE_MVP_CLASS_NONE)
		register_fail(page, failure, BE_MVP_REGISTER_HENVCFG,
			      BE_MVP_HENVCFG_STCE, value);
	/* The hart's one install: its domain's root, fenced and read back. */
	value = be_mvp_exec_install_hgatp(state->desc.hgatp);
	if (value != state->desc.hgatp)
		register_fail(page, BE_MVP_CLASS_GSTAGE, BE_MVP_REGISTER_HGATP,
			      state->desc.hgatp, value);
	be_mvp_vcsr_initial(vcsr);
	be_mvp_exec_arm_controls(&state->controls, top, vcsr, readback);
	if (!be_mvp_controls_valid(&state->controls, state->desc.hgatp, top))
		controls_fail(page);
	index = be_mvp_vcsr_mismatch(vcsr, readback);
	if (index != BE_MVP_VCSR_COUNT)
		register_fail(page, BE_MVP_CLASS_CONTROLS,
			      BE_MVP_REGISTER_VCSR + index, vcsr[index],
			      readback[index]);
	be_mvp_exec_fence_i();

	value = be_mvp_exec_read_time();
	state->entered = value;
	if (!be_mvp_post_ready(&page->outbound, &state->controls, value) ||
	    !be_mvp_post_entered(&page->outbound, &state->entry, value) ||
	    !publish(page))
		hart_fail(page, BE_MVP_CLASS_RING, (const be_u64 *)0, 0U);
	tell_control_hart();
	*record = state->entry;
	be_mvp_exec_resume(record, state->desc.hgatp, state->controls.hedeleg);
}
