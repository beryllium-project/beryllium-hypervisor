/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP hart blocks and hart 0's control loop (planning/mvp-m0-plan.md,
 *          "Hart region", "Boot sequence on hart 0", "Domain hart entry and
 *          fast path", and "Control loop"): the state page and the block
 *          descriptor hart 0 publishes in it for each domain hart before the
 *          boot barrier; the check the domain hart makes of the descriptor
 *          at entry (generation word, hart, domain, block, offsets, rings,
 *          and the Sv39x4 hgatp of its binding); the control loop's state
 *          machine over the records hart 0 drains (per domain STARTED,
 *          READY, ENTERED, LINE records, the IPI probe's PONG, the DENIAL
 *          records of accepted denials (planning/mvp-m1-plan.md, "Control
 *          loop and failure paths"), checked against the sealed channel or
 *          pages, the management requests, PAUSED, and TERMINATED of a
 *          scenario with the management extension (planning/mvp-m2-plan.md,
 *          "Control loop and failure paths"), with each request's decision
 *          against the sealed grants and the pending requests, then
 *          SHUTDOWN or FAIL; done when every domain shut down or was
 *          terminated; the run budget and the READY wait); since M7 the
 *          block's input ring (planning/mvp-m7-plan.md, D-1) and which
 *          domains hart 0 holds running, the only ones console input
 *          reaches (D-3); the order
 *          in which hart 0 drains the rings,
 *          round-robin, at most one record from each ring in turn, within
 *          a bound (Plan revision M0-C.1); the concurrency check of Q5 (the
 *          two domains' entry-to-shutdown intervals overlap by at least
 *          half the shorter); the loop's counters; and the printed form of
 *          a LINE.
 * Trust:   restricted C with no CSR, fence, SBI call, or I/O: the runtime
 *          reads the time, starts the harts, waits, drains the rings, and
 *          prints. Counters saturate; a time before the start fails closed;
 *          invalid input fails closed and stays failed.
 * Scope:   the MVP line (M0). Hart IDs, domain indices, and VMIDs are
 *          identifiers, not authority (S1 H03); the binding of domains to
 *          harts is scenario data the checks are given.
 */

#ifndef BE_MVP_HART_H
#define BE_MVP_HART_H

#include <be/types.h>

#include "mvp.h"
#include "mvp-ring.h"

/* hgatp: Sv39x4 mode, a 14-bit VMID, and the 16 KiB-aligned root's PPN. */
#define BE_MVP_HGATP_SV39X4		(BE_U64_C(8) << 60)
#define BE_MVP_HGATP_VMID_SHIFT		44U
#define BE_MVP_HGATP_VMID_LIMIT		(BE_U64_C(1) << 14)
#define BE_MVP_HGATP_ROOT_ALIGN		BE_U64_C(0x4000)
#define BE_MVP_HGATP_ROOT_LIMIT		(BE_U64_C(1) << 56)
#define BE_MVP_HGATP_PAGE_SHIFT		12U

/**
 * struct be_mvp_binding - one domain's hart, VMID, and root
 * @hart: the domain hart: never the control hart or another domain's, and
 *        never ~0, the all-harts IPI base; the firmware decides whether it
 *        exists, is STOPPED, and starts
 * @vmid: the domain's VMID, nonzero, below 2^14, and its own
 * @root: the domain's own Sv39x4 root, nonzero, 16 KiB aligned, and below
 *        2^56
 */
struct be_mvp_binding {
	be_u64 hart;
	be_u64 vmid;
	be_u64 root;
};

/* The default binding (Q12): G0 on hart 1, G1 on hart 2. */
#define BE_MVP_BINDINGS_INITIALIZER { \
	{ BE_MVP_DOMAIN0_HART, BE_MVP_G0_VMID, BE_MVP_G0_ROOT_HPA }, \
	{ BE_MVP_DOMAIN1_HART, BE_MVP_G1_VMID, BE_MVP_G1_ROOT_HPA }, \
}

/**
 * struct be_mvp_block_desc - what hart 0 publishes in a block's state page
 * @hart: the domain hart; hart_start passes it in a0
 * @domain: the domain the hart runs
 * @hgatp: the domain's hgatp, which the hart installs once
 * @block: the block's HPA; hart_start passes it in a1
 * @stack_top: the trusted-stack top, the hart's sscratch
 * @saved: the saved page, at the stack top
 * @state: the state page
 * @inbound: the inbound ring's buffer
 * @inbound_bytes: its capacity
 * @outbound: the outbound ring's buffer
 * @outbound_bytes: its capacity
 * @input: the input ring's buffer (M7, D-1)
 * @input_bytes: its capacity
 * @generation: written last, after a fence w, w: the boot barrier
 */
struct be_mvp_block_desc {
	be_u64 hart;
	be_u64 domain;
	be_u64 hgatp;
	be_u64 block;
	be_u64 stack_top;
	be_u64 saved;
	be_u64 state;
	be_u64 inbound;
	be_u64 inbound_bytes;
	be_u64 outbound;
	be_u64 outbound_bytes;
	be_u64 input;
	be_u64 input_bytes;
	be_u64 generation;
};

/**
 * struct be_mvp_state_page - one domain hart's state page
 * @inbound_head: the inbound ring's head, hart 0's
 * @inbound_tail: the inbound ring's tail, the domain hart's
 * @outbound_head: the outbound ring's head, the domain hart's
 * @outbound_tail: the outbound ring's tail, hart 0's
 * @desc: the block descriptor, hart 0's before the barrier
 * @entry: the first-entry frame, hart 0's before the barrier
 * @controls: the armed readbacks, the domain hart's
 * @state: the SBI core's state, counters and line buffer, the domain hart's
 * @entered: the time of the first entry, the domain hart's
 * @input_head: the input ring's head, hart 0's (M7, D-1)
 * @input_tail: the input ring's tail, the domain hart's
 *
 * Each ring index fills its own 64-byte line. After the barrier hart 0
 * writes only the inbound and input rings' heads and the outbound ring's
 * tail. The input ring's indices follow the rest, so that every earlier
 * field keeps its offset.
 */
struct be_mvp_state_page {
	struct be_mvp_ring_index inbound_head;
	struct be_mvp_ring_index inbound_tail;
	struct be_mvp_ring_index outbound_head;
	struct be_mvp_ring_index outbound_tail;
	struct be_mvp_block_desc desc;
	struct be_mvp_exit entry;
	struct be_mvp_controls controls;
	struct be_mvp_state state;
	be_u64 entered;
	struct be_mvp_ring_index input_head;
	struct be_mvp_ring_index input_tail;
};

/**
 * enum be_mvp_block_error - stable block results
 * @BE_MVP_BLOCK_OK: success
 * @BE_MVP_BLOCK_NULL: a required pointer is absent
 * @BE_MVP_BLOCK_BINDING: the bindings are malformed: not one per domain, a
 *                        hart that is the control hart, ~0, or another
 *                        domain's, a VMID that is zero, too wide, or
 *                        another domain's, or a root that is zero,
 *                        misaligned, beyond Sv39x4's reach, or another
 *                        domain's
 * @BE_MVP_BLOCK_GENERATION: the generation word is not the published one
 * @BE_MVP_BLOCK_DOMAIN: the domain is not one of the bindings
 * @BE_MVP_BLOCK_HART: the hart is not the binding's, or not a0
 * @BE_MVP_BLOCK_ADDRESS: the block is not the domain's, or not a1
 * @BE_MVP_BLOCK_OFFSETS: the stack top, saved page, state page, or a ring
 *                        is not at its offset in the block
 * @BE_MVP_BLOCK_RINGS: a ring capacity is not a power of two of at least
 *                      512 bytes that fits its slot
 * @BE_MVP_BLOCK_HGATP: hgatp is not Sv39x4 with the binding's VMID and root
 */
enum be_mvp_block_error {
	BE_MVP_BLOCK_OK = 0,
	BE_MVP_BLOCK_NULL,
	BE_MVP_BLOCK_BINDING,
	BE_MVP_BLOCK_GENERATION,
	BE_MVP_BLOCK_DOMAIN,
	BE_MVP_BLOCK_HART,
	BE_MVP_BLOCK_ADDRESS,
	BE_MVP_BLOCK_OFFSETS,
	BE_MVP_BLOCK_RINGS,
	BE_MVP_BLOCK_HGATP,
};

/**
 * enum be_mvp_domain_phase - one domain in hart 0's control loop
 * @BE_MVP_DOMAIN_NONE: its hart is not started
 * @BE_MVP_DOMAIN_STARTED: its hart started; no record yet
 * @BE_MVP_DOMAIN_READY: READY drained
 * @BE_MVP_DOMAIN_ENTERED: ENTERED drained; the guest runs
 * @BE_MVP_DOMAIN_SHUTDOWN: SHUTDOWN drained; the hart is parked
 * @BE_MVP_DOMAIN_FAILED: FAIL drained; the run ends
 * @BE_MVP_DOMAIN_PAUSED: PAUSED drained; the hart is parked, its domain
 *                        never resumed, and the run does not end on it
 * @BE_MVP_DOMAIN_TERMINATED: TERMINATED drained; the hart is parked, and
 *                            the domain has ended, as a shut-down one
 */
enum be_mvp_domain_phase {
	BE_MVP_DOMAIN_NONE = 0,
	BE_MVP_DOMAIN_STARTED,
	BE_MVP_DOMAIN_READY,
	BE_MVP_DOMAIN_ENTERED,
	BE_MVP_DOMAIN_SHUTDOWN,
	BE_MVP_DOMAIN_FAILED,
	BE_MVP_DOMAIN_PAUSED,
	BE_MVP_DOMAIN_TERMINATED,
};

/**
 * struct be_mvp_domain_track - one domain as hart 0 sees it
 * @phase: its phase
 * @pinged: nonzero once hart 0 was told to send its one PING
 * @ponged: nonzero once its PONG was drained
 * @hart: the hart it was started on
 * @last: the latest record time drained from it
 * @entered: its ENTERED record's time
 * @shutdown: its SHUTDOWN or TERMINATED record's time, when it ended
 * @lines: LINE records drained
 * @records: records drained
 * @ring_peak: its outbound ring's high-water mark, from SHUTDOWN
 * @denials: DENIAL records drained, the latest one's sequence number
 * @requests: MGMT_REQUEST records drained, the latest one's sequence
 *            number
 */
struct be_mvp_domain_track {
	enum be_mvp_domain_phase phase;
	be_u32 pinged;
	be_u32 ponged;
	be_u64 hart;
	be_u64 last;
	be_u64 entered;
	be_u64 shutdown;
	be_u64 lines;
	be_u64 records;
	be_u64 ring_peak;
	be_u64 denials;
	be_u64 requests;
};

/**
 * struct be_mvp_mgmt_domain - one domain's management requests, as hart 0
 *                             holds them (planning/mvp-m2-plan.md, Q14)
 * @pending: nonzero while a request hart 0 delivered to this domain
 *           awaits its PAUSED or TERMINATED
 * @awaiting: nonzero while this domain's own request awaits its answer:
 *            its hart waits in HS, so it makes no other
 * @by: the pending request's requester
 * @fid: the pending request's function
 * @seq: the pending request's sequence number, its requester's
 * @time: the pending request's time, its MGMT_REQUEST's
 */
struct be_mvp_mgmt_domain {
	be_u32 pending;
	be_u32 awaiting;
	be_u64 by;
	be_u64 fid;
	be_u64 seq;
	be_u64 time;
};

/**
 * struct be_mvp_mgmt_state - hart 0's management state
 * @grants: the sealed manifest's grants, read only by hart 0
 * @count: how many, at most %BE_MVP_MGMT_GRANTS_MAX
 * @checked: 1 to decide each request against @grants; 0 in the
 *           no-grant-check variant (planning/mvp-m2-plan.md, Q10), which
 *           delivers every well-formed request whose target's state allows
 *           it, without consulting @grants
 * @domain: each domain's requests
 *
 * Hart 0 alone writes and reads it, through its control loop; no code a
 * domain hart runs names it (planning/mvp-m2-plan.md, "The measurement").
 */
struct be_mvp_mgmt_state {
	const struct be_mvp_mgmt_grant *grants;
	be_u64 count;
	be_u32 checked;
	struct be_mvp_mgmt_domain domain[BE_MVP_DOMAINS];
};

/**
 * struct be_mvp_control - hart 0's control loop
 * @domain: each domain
 * @start: the boot barrier's time, when the run budget starts
 * @budget: ticks after @start that the run may last
 * @ready_ticks: ticks after @start by which every started hart is READY
 * @records: records drained, of both domains; saturates
 * @wakes: wakes counted; saturates
 * @idle_ticks: ticks spent waiting; saturates
 * @failed: nonzero once the run failed; sticky
 * @done: nonzero once both domains shut down
 * @failure: the class that failed the run, or NONE
 * @sealed: nonzero once be_mvp_control_channel() or
 *          be_mvp_control_pages() gave the windows and the sealed channel
 *          or pages, without which every DENIAL is refused
 * @window_gpa: each domain's walked window's first GPA
 * @window_bytes: each domain's walked window's size
 * @channel: the sealed channel record, all zero for none or for pages
 * @pages: the sealed pages a DENIAL is checked against: the channel
 *         record's page, or a scenario's declared pages
 * @page_count: how many, at most %BE_MVP_PAGES_MAX
 * @mgmt: hart 0's management state, once be_mvp_control_mgmt() gave it;
 *        absent in an image without the management extension, whose loop
 *        refuses every management record as ring
 */
struct be_mvp_control {
	struct be_mvp_domain_track domain[BE_MVP_DOMAINS];
	be_u64 start;
	be_u64 budget;
	be_u64 ready_ticks;
	be_u64 records;
	be_u64 wakes;
	be_u64 idle_ticks;
	be_u32 failed;
	be_u32 done;
	enum be_mvp_class failure;
	be_u32 sealed;
	be_u64 window_gpa[BE_MVP_DOMAINS];
	be_u64 window_bytes[BE_MVP_DOMAINS];
	struct be_mvp_gstage_channel channel;
	struct be_mvp_gstage_page pages[BE_MVP_PAGES_MAX];
	be_u64 page_count;
	struct be_mvp_mgmt_state *mgmt;
};

/**
 * enum be_mvp_step - what one drained record means
 * @BE_MVP_STEP_INVALID: invalid input, or a record out of protocol; the
 *                       run fails with the result's class
 * @BE_MVP_STEP_READY: print BE_MVP:09
 * @BE_MVP_STEP_ENTERED: print BE_MVP:10
 * @BE_MVP_STEP_LINE: print the line; when the result's @ping is set, then
 *                    post one PING to the domain's inbound ring and send
 *                    its hart one IPI
 * @BE_MVP_STEP_PONG: print BE_MVP:11
 * @BE_MVP_STEP_SHUTDOWN: print BE_MVP:12; when the result's @done is set,
 *                        the run is complete
 * @BE_MVP_STEP_FAIL: the domain failed with the result's class: print its
 *                    FAIL and DETAIL lines, acknowledge, and end the run
 * @BE_MVP_STEP_DENIAL: print BE_MVP:DENY
 * @BE_MVP_STEP_MGMT: a management request decided at once: answer it
 *                    (the result's @answer)
 * @BE_MVP_STEP_DELIVER: a management request delivered: post PAUSE or
 *                       TERMINATE (the result's @fid), naming its
 *                       requester, to the result's @target's inbound ring
 *                       and send its hart one IPI; its answer waits for
 *                       the target's transition
 * @BE_MVP_STEP_PAUSED: print BE_MVP:12 DOMAIN_PAUSED, then answer the
 *                      request that paused the domain
 * @BE_MVP_STEP_TERMINATED: print BE_MVP:12 DOMAIN_TERMINATED, then answer
 *                          the request that terminated the domain; when
 *                          the result's @done is set, the run is complete
 */
enum be_mvp_step {
	BE_MVP_STEP_INVALID = 0,
	BE_MVP_STEP_READY,
	BE_MVP_STEP_ENTERED,
	BE_MVP_STEP_LINE,
	BE_MVP_STEP_PONG,
	BE_MVP_STEP_SHUTDOWN,
	BE_MVP_STEP_FAIL,
	BE_MVP_STEP_DENIAL,
	BE_MVP_STEP_MGMT,
	BE_MVP_STEP_DELIVER,
	BE_MVP_STEP_PAUSED,
	BE_MVP_STEP_TERMINATED,
};

/**
 * struct be_mvp_step_result - one record's step
 * @step: the step
 * @ping: for a LINE, nonzero when it is the domain's first
 * @done: for a SHUTDOWN or TERMINATED, nonzero when every domain has shut
 *        down or been terminated
 * @failure: for INVALID or FAIL, the class that ends the run
 * @answer: nonzero when a management request is answered now: post
 *          MGMT_RESULT (@result, @seq) to @requester's inbound ring, send
 *          its hart one IPI, and print its BE_MVP:MGMT line; set for MGMT,
 *          PAUSED, and TERMINATED, and for a SHUTDOWN of a domain a
 *          delivered request still awaited
 * @requester: the request's requester
 * @seq: the request's sequence number
 * @fid: the request's function
 * @target: the request's target, as its requester named it
 * @result: the request's result, an SBI error
 * @shown: the target's state the BE_MVP:MGMT line prints: PAUSED,
 *         TERMINATED, or SHUTDOWN after the transition the request
 *         awaited, or %BE_MVP_TARGET_COUNT for a request decided at once
 * @requested: the request's time, its MGMT_REQUEST's
 */
struct be_mvp_step_result {
	enum be_mvp_step step;
	be_u32 ping;
	be_u32 done;
	enum be_mvp_class failure;
	be_u32 answer;
	be_u64 requester;
	be_u64 seq;
	be_u64 fid;
	be_u64 target;
	long result;
	enum be_mvp_target_state shown;
	be_u64 requested;
};

/* be_mvp_drain_next()'s answer once a drain is over: no domain's index. */
#define BE_MVP_DRAIN_DONE		((be_u32)BE_MVP_DOMAINS)

/**
 * struct be_mvp_drain - one round-robin drain of the outbound rings
 * @rings: the rings it visits, domain 0's first: 1 in the probe images,
 *         else %BE_MVP_DOMAINS; 0 once refused
 * @next: the domain whose ring the next visit is to
 * @idle: visits in a row that took no record
 * @visits: visits left
 *
 * Plan revision M0-C.1: on each wake hart 0 takes at most one record from
 * domain 0's ring, then at most one from domain 1's, and again, until a
 * visit to each ring in turn has taken none, so the printed order follows
 * the order in which records became visible to hart 0, however slowly the
 * console prints them. Each visit acquires the ring's head and releases
 * its tail around its one take, as the reader's protocol has it.
 */
struct be_mvp_drain {
	be_u32 rings;
	be_u32 next;
	be_u32 idle;
	be_u64 visits;
};

/**
 * be_mvp_hgatp - an Sv39x4 hgatp value
 * @vmid: below 2^14
 * @root: 16 KiB aligned, below 2^56
 *
 * Return: mode 8, @vmid, and @root's PPN; or 0 for a VMID or root outside
 *         those rules.
 */
be_u64 be_mvp_hgatp(be_u64 vmid, be_u64 root);

/**
 * be_mvp_bindings_valid - check every domain's binding
 * @bindings: the bindings
 * @count: how many; must be %BE_MVP_DOMAINS
 *
 * Return: 1 when each binding is well formed and no two share a hart, a
 *         VMID, or a root, else 0.
 */
int be_mvp_bindings_valid(const struct be_mvp_binding *bindings,
			  be_u64 count);

/**
 * be_mvp_block_hpa - a domain's block in the hart region
 * @domain: the domain
 *
 * Return: the block's HPA, or 0 for a domain the region has no block for.
 */
be_u64 be_mvp_block_hpa(be_u64 domain);

/**
 * be_mvp_block_fill - fill a block descriptor before the boot barrier
 * @desc: the descriptor in the block's state page
 * @domain: the domain
 * @bindings: every domain's binding
 * @count: how many, %BE_MVP_DOMAINS
 * @outbound_bytes: the outbound ring's capacity
 *
 * Fills every field from the layout and the domain's binding, with a
 * generation word of 0: hart 0 writes %BE_MVP_GENERATION last, after a
 * fence w, w. The input ring fills its slot (M7, D-1).
 *
 * Return: %BE_MVP_BLOCK_OK; or the first error, with @desc zeroed.
 */
enum be_mvp_block_error
be_mvp_block_fill(struct be_mvp_block_desc *desc, be_u64 domain,
		  const struct be_mvp_binding *bindings, be_u64 count,
		  be_u64 outbound_bytes);

/**
 * be_mvp_block_check - a domain hart's check of its block at entry
 * @desc: the published descriptor, read after a fence r, r
 * @hart_id: the hart's a0
 * @block: the hart's a1
 * @bindings: every domain's binding
 * @count: how many, %BE_MVP_DOMAINS
 *
 * Requires well-formed bindings, the published generation word, a domain
 * with a binding whose hart is the descriptor's and @hart_id, the domain's
 * block at @block, every page and ring at its offset, ring capacities that
 * are powers of two of at least 512 bytes and fit their slots (the input
 * ring's exactly its slot), and the binding's hgatp.
 *
 * Return: %BE_MVP_BLOCK_OK or the first error, in that order.
 */
enum be_mvp_block_error
be_mvp_block_check(const struct be_mvp_block_desc *desc, be_u64 hart_id,
		   be_u64 block, const struct be_mvp_binding *bindings,
		   be_u64 count);

/**
 * be_mvp_control_init - both domains not started, nothing counted
 * @ctl: the control loop
 * @start: the boot barrier's time
 * @budget: the run budget in ticks, nonzero
 * @ready_ticks: the READY wait in ticks, nonzero
 *
 * A zero budget or wait leaves the loop failed as exception.
 */
void be_mvp_control_init(struct be_mvp_control *ctl, be_u64 start,
			 be_u64 budget, be_u64 ready_ticks);

/**
 * be_mvp_control_started - a domain's hart reached STARTED
 * @ctl: the control loop
 * @domain: the domain
 * @hart: its hart
 *
 * Return: 1; or 0 for a failed loop or invalid input (a domain started
 *         twice, or two domains on one hart), which fails it as exception.
 */
int be_mvp_control_started(struct be_mvp_control *ctl, be_u64 domain,
			   be_u64 hart);

/**
 * be_mvp_control_channel - give the loop what it checks DENIAL records
 *                          against
 * @ctl: the control loop, after be_mvp_control_init()
 * @maps: both domains' walked maps, indexed by domain
 * @channel: the sealed channel record, all zero for none
 *
 * Copies each domain's walked window and the sealed record: a DENIAL's
 * kind must fit its GPA against them (planning/mvp-m1-plan.md, "Control
 * loop and failure paths").
 *
 * Return: 1; or 0 for a failed loop or absent input, which fails it as
 *         exception.
 */
int be_mvp_control_channel(struct be_mvp_control *ctl,
			   const struct be_mvp_gstage_map *maps,
			   const struct be_mvp_gstage_channel *channel);

/**
 * be_mvp_control_pages - give the loop what it checks DENIAL records
 *                        against, in a scenario with pages
 * @ctl: the control loop, after be_mvp_control_init()
 * @maps: both domains' walked maps, indexed by domain
 * @pages: the sealed pages (planning/mvp-m2-plan.md, Q1)
 * @count: how many, 1 to %BE_MVP_PAGES_MAX
 *
 * Copies each domain's walked window and the sealed pages: a DENIAL's kind
 * must fit its GPA against them, as against M1's one channel page.
 *
 * Return: 1; or 0 for a failed loop or absent or invalid input, which
 *         fails it as exception.
 */
int be_mvp_control_pages(struct be_mvp_control *ctl,
			 const struct be_mvp_gstage_map *maps,
			 const struct be_mvp_gstage_page *pages, be_u64 count);

/**
 * be_mvp_control_mgmt - give the loop its management state and grants
 * @ctl: the control loop, after be_mvp_control_init()
 * @mgmt: hart 0's management state, zeroed and kept by the loop
 * @grants: the sealed manifest's grants
 * @count: how many, at most %BE_MVP_MGMT_GRANTS_MAX
 * @checked: 1 to decide each request against @grants, or 0 (the
 *           no-grant-check variant) to decide it as if every pair of
 *           domains held both permissions
 *
 * Without it, the loop refuses every MGMT_REQUEST, PAUSED, and TERMINATED
 * record as ring.
 *
 * Return: 1; or 0 for a failed loop or absent or invalid input, which
 *         fails it as exception.
 */
int be_mvp_control_mgmt(struct be_mvp_control *ctl,
			struct be_mvp_mgmt_state *mgmt,
			const struct be_mvp_mgmt_grant *grants, be_u64 count,
			int checked);

/**
 * be_mvp_control_record - apply one record drained from a domain's ring
 * @ctl: the control loop
 * @domain: the domain whose ring it came from
 * @record: the record
 * @result: the step
 *
 * Each domain's records must come in protocol order, at times that never
 * go back: READY after the start, ENTERED after READY, then LINE records,
 * one PONG after hart 0's PING (the domain's first LINE asks for it,
 * unless a request delivered to the domain is pending: the domain is
 * about to stop and is never asked), any DENIAL and MGMT_REQUEST records,
 * and SHUTDOWN, after the PONG and naming the ENTERED time, the LINE
 * count, the DENIAL count, and the MGMT_REQUEST count hart 0 drained; or
 * PAUSED, or TERMINATED, also after PAUSED, each answering a request
 * delivered to the domain; or FAIL, with a valid class, at any point after
 * the start and before SHUTDOWN. Each payload must have its type's size. A
 * DENIAL must come between ENTERED and SHUTDOWN, after
 * be_mvp_control_channel() or be_mvp_control_pages(), with the domain's
 * next sequence number from 1, the access fault of its cause as its
 * injected cause (1, 5, or 7 for 20, 21, or 23), its GPA its htval shifted
 * left by 2 with stval's low two bits, its exit no later than its post nor
 * before the domain's entry, and its kind the sealed pages': read-only
 * only for a store to a page the domain holds without write, unmapped
 * only outside the domain's window and every page it holds.
 *
 * With be_mvp_control_mgmt() (planning/mvp-m2-plan.md, "Control loop and
 * failure paths"): a MGMT_REQUEST from a running domain, with pause or
 * terminate and the domain's next sequence number from 1, while none of
 * its own awaits its answer (its hart waits for it), is decided by
 * be_mvp_mgmt_decide() against the target's state: shut down, terminated,
 * pending while a request delivered to it or its own awaits, paused, or
 * running; a request to itself is pending. A decision is answered at once
 * (MGMT); a delivery (DELIVER) leaves the request pending on its target
 * until the target's PAUSED or TERMINATED, which must answer it: the
 * pending function and its requester. That record, or a SHUTDOWN of the
 * target first, answers the requester: 0, or invalid state with the
 * target shut down. A domain cannot shut down while its own request
 * awaits its answer; a SHUTDOWN that claims to is INVALID as ring.
 *
 * A record out of order or malformed is INVALID as ring; a PONG not asked
 * for, or a SHUTDOWN still owing its PONG, as ipi. INVALID and FAIL fail
 * the run; once it failed or is done, every record is INVALID. The run is
 * done once every domain has shut down or been terminated; a paused one
 * has not ended.
 *
 * Return: the step.
 */
enum be_mvp_step be_mvp_control_record(struct be_mvp_control *ctl,
				       be_u64 domain,
				       const struct be_mvp_record *record,
				       struct be_mvp_step_result *result);

/**
 * be_mvp_control_wake - count one wake of hart 0 and check the clocks
 * @ctl: the control loop, with both domains started and the run not done
 * @now: the time CSR
 *
 * Return: NONE to drain and wait again; RUN_TIMEOUT for a time before
 *         the start, which cannot measure the budget; HART_READY once a
 *         hart that is started but not READY is at or past the READY wait;
 *         RUN_TIMEOUT once @now is at or past the budget; the sticky class
 *         of a failed loop; or EXCEPTION for invalid input. Each but NONE
 *         fails the run.
 */
enum be_mvp_class be_mvp_control_wake(struct be_mvp_control *ctl,
				      be_u64 now);

/**
 * be_mvp_control_running - the domains console input may reach (M7, D-3)
 * @ctl: the control loop
 *
 * A domain is running from its hart's start until its SHUTDOWN, FAIL,
 * PAUSED, or TERMINATED, and not while a PAUSE or TERMINATE hart 0
 * delivered to it is pending: it is about to stop.
 *
 * Return: bit d set for each running domain d; 0 for a failed or done loop
 *         or invalid input.
 */
be_u64 be_mvp_control_running(const struct be_mvp_control *ctl);

/**
 * be_mvp_control_waited - count ticks hart 0 spent waiting
 * @ctl: the control loop
 * @ticks: the wait; the total saturates
 */
void be_mvp_control_waited(struct be_mvp_control *ctl, be_u64 ticks);

/**
 * be_mvp_drain_begin - start one round-robin drain of the outbound rings
 * @drain: the drain
 * @rings: 1 or %BE_MVP_DOMAINS
 * @capacity: each ring's capacity in bytes, a power of two of at least
 *            %BE_MVP_RING_MIN_BYTES that fits the outbound slot
 *
 * A ring holds at most @capacity / %BE_MVP_RECORD_HEADER_BYTES records, so
 * the drain allows each ring that many visits and one more, the bound the
 * drain of one ring had before: every record a ring held when the drain
 * began is taken before the bound, however fast its writer posts more, and
 * the drain ends. Invalid arguments leave a drain that is over.
 */
void be_mvp_drain_begin(struct be_mvp_drain *drain, be_u32 rings,
			be_u64 capacity);

/**
 * be_mvp_drain_next - the ring a drain visits next
 * @drain: the drain
 *
 * Return: the domain whose ring to take at most one record from, in turn
 *         0, 1, 0, 1, ...; or %BE_MVP_DRAIN_DONE once the latest visit to
 *         each ring took no record, or the visits have run out.
 */
be_u32 be_mvp_drain_next(const struct be_mvp_drain *drain);

/**
 * be_mvp_drain_visited - count the visit be_mvp_drain_next() named
 * @drain: the drain
 * @took: nonzero when the visit took a record; zero when the ring was
 *        empty, or held (the ring-full variant)
 *
 * A drain that is over is left as it is.
 */
void be_mvp_drain_visited(struct be_mvp_drain *drain, int took);

/**
 * be_mvp_overlap - the overlap of two [entered, shutdown] intervals
 * @entered0: the first domain's entry time
 * @shutdown0: its shutdown time, after the entry
 * @entered1: the second domain's entry time
 * @shutdown1: its shutdown time, after the entry
 * @overlap: the ticks both intervals hold, on success
 * @shorter: the shorter interval's length, on success
 *
 * Return: 1, or 0 when an interval is empty or reversed.
 */
int be_mvp_overlap(be_u64 entered0, be_u64 shutdown0, be_u64 entered1,
		   be_u64 shutdown1, be_u64 *overlap, be_u64 *shorter);

/**
 * be_mvp_concurrent - Q5's concurrency floor
 * @overlap: the overlap in ticks
 * @shorter: the shorter interval's length
 *
 * Return: 1 when @overlap is at least half of a nonzero @shorter (exactly
 *         half passes) and no more than all of it, else 0.
 */
int be_mvp_concurrent(be_u64 overlap, be_u64 shorter);

/**
 * be_mvp_control_overlap - the overlap of a completed run
 * @ctl: the control loop, done
 * @overlap: the overlap in ticks, printed in BE_MVP:13; 0 when the run is
 *           not done
 *
 * Return: 1 when the run is done and the overlap meets Q5's floor, else 0.
 */
int be_mvp_control_overlap(const struct be_mvp_control *ctl,
			   be_u64 *overlap);

/**
 * be_mvp_line_output - format a drained LINE record for the console
 * @record: a LINE record of domain 0 or 1
 * @output: monitor buffer
 * @capacity: at least the bytes written
 *
 * Writes the domain's prefix, the line, and LF; every line byte must be
 * printable ASCII (0x20-0x7e), as the domain's console made it.
 *
 * Return: bytes written, at most %BE_MVP_PRINT_LINE_BYTES; or
 *         %BE_MVP_CONSOLE_INVALID, with nothing written.
 */
be_u64 be_mvp_line_output(const struct be_mvp_record *record, char *output,
			  be_u64 capacity);

#endif
