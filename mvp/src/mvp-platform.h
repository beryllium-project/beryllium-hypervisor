/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP privileged boundary: the VS-exit vector, the resume tail,
 *          the arm, budget, wait, SSIP, timer, fence, time, and park helpers
 *          in mvp-trap.S, the hart entry and the fence.i in mvp-hartentry.S,
 *          and the C entry points that assembly calls; hart 0's runtime
 *          (mvp-runtime.c) and the domain hart's (mvp-hartmain.c).
 * Trust:   assembly owns every CSR access, the frame transfer, the fence.i,
 *          the HS wfi, and the no-call resume tail; C sees only monitor-owned
 *          copies and never runs with guest-restored registers.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, planning/mvp-m1-plan.md,
 *          and planning/mvp-m2-plan.md). After the R3 reset: no hgatp
 *          write or fence but the accepted install function's, no vs* write
 *          but the arm helper's (and vstimecmp by the TIME helper, and
 *          vscause, vstval, vsepc, and vsstatus by the injection helper,
 *          once per accepted denial), no stimecmp write but hart 0's
 *          budget helper's (since M7 also re-armed at each wake for the
 *          console input poll, never past the budget's end, in an image
 *          that grants console input), no hvip injection, and no HS
 *          interrupt but the IPI at V=1 and, in hart 0's wait, the IPI and
 *          the budget timer;
 *          a domain hart waiting in HS for hart 0's answer, or paused or
 *          terminated, finds the IPI pending in sip, never as a trap.
 */

#ifndef BE_MVP_PLATFORM_H
#define BE_MVP_PLATFORM_H

#include "r3-platform.h"

#include "mvp.h"
#include "mvp-hart.h"
#include "mvp-input.h"
#include "mvp-payload.h"
#include "mvp-scenario.h"

/*
 * Whether this image accepts the denial entry (planning/mvp-m1-plan.md,
 * Q4): its scenario's accepted-exit set names denial, and the QEMU and
 * board negative variant no-inject removes it. Hart 0 writes it into each
 * domain hart's state; the domain hart's runtime links the denial action's
 * executor, the injection helper's one call site, only when it is 1.
 */
#if defined(BE_MVP_VARIANT_NO_INJECT)
#define BE_MVP_RUN_ACCEPT_DENIAL	0
#else
#define BE_MVP_RUN_ACCEPT_DENIAL	BE_MVP_SCENARIO_ACCEPT_DENIAL
#endif

/*
 * Whether this image accepts the management extension
 * (planning/mvp-m2-plan.md, Q3): its scenario's header says so, as a v3
 * header's accepted-exit set does (BE_MVP_SCENARIO_ACCEPT_MGMT); a v1 or
 * v2 header says nothing, and the extension is not supported. Hart 0
 * writes it into each domain hart's state, and the SBI implementation
 * version the image reports follows it: BE_MVP_SBI_IMPL_VERSION_MGMT (6
 * since M7, 4 before) with the extension, else BE_MVP_SBI_IMPL_VERSION (5
 * since M7, 3 before). The domain hart's
 * runtime links the management call's wait and the paused and terminated
 * parks only when it is 1.
 */
#if defined(BE_MVP_SCENARIO_ACCEPT_MGMT)
#define BE_MVP_RUN_ACCEPT_MGMT		BE_MVP_SCENARIO_ACCEPT_MGMT
#else
#define BE_MVP_RUN_ACCEPT_MGMT		0
#endif

/*
 * A domain hart's state page as its runtime uses it: M0-2's state page,
 * then the walked window and the walked leaves of its root's pages hart 0
 * copies in before the barrier (the hart's private state for the denial
 * decision: M1's channel leaf as page 0, or a scenario's declared pages),
 * and the hart's own views of its two rings; since M7 its view of its
 * input ring and its staged input (planning/mvp-m7-plan.md, D-1), the
 * domain hart's alone after the barrier.
 */
struct be_mvp_hart_page {
	struct be_mvp_state_page page;
	struct be_mvp_gstage_map map;
	struct be_mvp_gstage_leaves leaves;
	struct be_mvp_ring inbound;
	struct be_mvp_ring outbound;
	struct be_mvp_ring input;
	struct be_mvp_input_stage stage;
};

/*
 * A domain hart's FAIL detail (mvp-hart.h records it in up to eight words):
 * an exit (cause, pc, tval, htval, htinst, spvp, vsatp, exits); the armed
 * readbacks READY carries, for the controls class; or one register (its
 * BE_MVP_REGISTER_* number, the value wanted, and the readback).
 */
#define BE_MVP_DETAIL_EXIT_WORDS	8U
#define BE_MVP_DETAIL_REGISTER_WORDS	3U
#define BE_MVP_REGISTER_HENVCFG		0U
#define BE_MVP_REGISTER_HGATP		1U
#define BE_MVP_REGISTER_VCSR		2U

/**
 * be_mvp_runtime_main - accepted R3 prelude, then hart 0's run
 * @hart_id: firmware a0 hart identifier
 * @firmware_pointer: firmware a1 value, recorded but never dereferenced
 */
void be_mvp_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
	__attribute__((noreturn));

/**
 * be_mvp_runtime_terminal - print BE_MVP:FAIL, request SRST, and halt
 * @failure: terminal class
 *
 * Hart 0's terminal path, also reached from the vector by an HS exception
 * on hart 0.
 */
void be_mvp_runtime_terminal(enum be_mvp_class failure)
	__attribute__((noreturn));

/**
 * be_mvp_hart_main - a started domain hart, from the hart entry
 * @hart_id: HSM a0, the hart's ID
 * @block: HSM a1, the hart's block, already checked to be one of the
 *         region's blocks; sp is its trusted-stack top
 *
 * Checks the published block, arms the hart, installs its root, posts
 * READY and ENTERED, and enters the domain; a block that fails its check
 * parks the hart.
 */
void be_mvp_hart_main(be_u64 hart_id, be_u64 block) __attribute__((noreturn));

/**
 * be_mvp_dispatch - service one VS exit the vector saved
 * @record: the hart's saved page, at its trusted-stack top
 *
 * This never returns: it resumes the domain through be_mvp_arch_resume,
 * parks the hart after its shutdown, or fails closed.
 */
void be_mvp_dispatch(struct be_mvp_exit *record) __attribute__((noreturn));

/**
 * be_mvp_hart_terminal - a domain hart's terminal path
 * @record: the hart's saved page
 * @failure: terminal class
 *
 * Posts FAIL with the record's detail and waits for hart 0's ACK, or prints
 * its own FAIL lines and requests SRST.
 */
void be_mvp_hart_terminal(struct be_mvp_exit *record,
			  enum be_mvp_class failure) __attribute__((noreturn));

/**
 * be_mvp_fw_call - one HS-to-M call beyond R3's: HSM or IPI, or a domain
 *                  hart's own DBCN write
 * @eid: extension
 * @fid: function
 * @argument0: a0
 * @argument1: a1
 * @argument2: a2
 * @value: the call's value
 *
 * Every call goes through the accepted be_r3_arch_sbi_call, the image's one
 * ecall, from this one out-of-line function, which the image checker holds
 * to its caller table.
 *
 * Return: the SBI error.
 */
long be_mvp_fw_call(be_u64 eid, be_u64 fid, be_u64 argument0,
		    be_u64 argument1, be_u64 argument2, be_u64 *value)
	__attribute__((noinline));

/**
 * be_mvp_send_ipi - send one hart the supervisor software interrupt
 * @hart: the target
 *
 * Return: the SBI error, or %BE_MVP_SBI_ERR_INVALID_PARAM for the all-harts
 *         base.
 */
long be_mvp_send_ipi(be_u64 hart);

/**
 * be_mvp_line_format - append a formatted line
 * @line: the line
 * @format: fixed text; "%x" appends the next value in hex, "%d" in decimal,
 *          "%i" as a signed decimal
 * @values: one value per directive
 */
void be_mvp_line_format(struct be_mvp_line *line, const char *format,
			const be_u64 *values);

/**
 * be_mvp_detail_line - a domain's DETAIL line, from its FAIL detail
 * @line: the line, reset first and ending in LF
 * @failure: the domain's class
 * @domain: the domain
 * @hart: its hart
 * @detail: the detail words
 * @words: 0, %BE_MVP_DETAIL_REGISTER_WORDS, or %BE_MVP_DETAIL_EXIT_WORDS
 */
void be_mvp_detail_line(struct be_mvp_line *line, enum be_mvp_class failure,
			be_u64 domain, be_u64 hart, const be_u64 *detail,
			be_u64 words);

/**
 * be_mvp_arch_arm_stce - write henvcfg = STCE only and read it back
 *
 * Return: the henvcfg readback.
 */
be_u64 be_mvp_arch_arm_stce(void);

/**
 * be_mvp_arch_arm_controls - arm a domain hart and read it all back
 * @controls: readback output
 * @trusted_top: the hart's trusted-stack top, for sscratch
 * @vcsr: the initial per-domain CSR set, %BE_MVP_VCSR_COUNT words
 * @readback: %BE_MVP_VCSR_COUNT words, the set read back
 *
 * Writes vstimecmp = ~0 and samples hip, then writes hedeleg = 0xb15d,
 * hideleg = VSTI, and hcounteren = TM, clears hstatus VTVM, VTW, and VTSR,
 * sets sie.SSIE, writes sscratch = @trusted_top and the per-domain CSR set
 * once, and reads every control and the set back. The only writer of the
 * per-domain CSRs but for the TIME helper's vstimecmp.
 */
void be_mvp_arch_arm_controls(struct be_mvp_controls *controls,
			      be_u64 trusted_top, const be_u64 *vcsr,
			      be_u64 *readback);

/**
 * be_mvp_arch_set_timer - serve SBI TIME set_timer
 * @deadline: the domain's absolute deadline, written to vstimecmp
 */
void be_mvp_arch_set_timer(be_u64 deadline);

/**
 * be_mvp_arch_inject - deliver one accepted denial as an access fault
 * @vscause: the access fault's cause, 1, 5, or 7
 * @vstval: the faulting guest virtual address
 * @vsepc: the faulting instruction
 * @vsstatus: the guest's vsstatus with SPP, SPIE, and SIE as a trap into
 *            VS mode sets them
 * @readback: %BE_MVP_INJECT_WORDS words: the four read back, in this order
 *
 * Writes vscause, vstval, vsepc, and vsstatus, in that order, then reads
 * each back. After arming, the only writer of the four; it touches no
 * other CSR. Called from one site, the denial action's executor, in an
 * image that accepts denials.
 */
void be_mvp_arch_inject(be_u64 vscause, be_u64 vstval, be_u64 vsepc,
			be_u64 vsstatus, be_u64 *readback);

/**
 * be_mvp_arch_arm_budget - arm hart 0's run budget and its wait
 * @deadline: the run's end, written to stimecmp, the image's one writer
 *            after B1's quiesce; while console input is armed (M7), the
 *            next poll's deadline, never past the run's end
 * @trusted_top: hart 0's trusted-stack top, for sscratch
 *
 * Also sets sie.SSIE and sie.STIE; sstatus.SIE stays 0, so either only
 * wakes hart 0's wait.
 *
 * Return: the sie readback.
 */
be_u64 be_mvp_arch_arm_budget(be_u64 deadline, be_u64 trusted_top);

/**
 * be_mvp_arch_wait - wait in HS until an enabled interrupt is pending
 * @pending: the sip bits that end the wait
 *
 * sstatus.SIE is 0, so a pending interrupt wakes the wfi without a trap:
 * hart 0's wait, and a paused or terminated domain hart's.
 *
 * Return: the time CSR after the wait.
 */
be_u64 be_mvp_arch_wait(be_u64 pending);

/**
 * be_mvp_arch_clear_ssip - clear sip.SSIP, the IPI's pending bit
 *
 * One csrrc: the clear and the read of sip as it was are one access, so
 * an IPI that arrives after it stays pending.
 *
 * Return: sip before the clear; its SSIP bit says whether an IPI had
 *         arrived.
 */
be_u64 be_mvp_arch_clear_ssip(void);

/**
 * be_mvp_arch_read_time - read the time CSR
 *
 * Return: the time CSR.
 */
be_u64 be_mvp_arch_read_time(void);

/** be_mvp_arch_fence_w_w - a ring writer's fence before publishing. */
void be_mvp_arch_fence_w_w(void);

/** be_mvp_arch_fence_r_r - a ring reader's fence after acquiring. */
void be_mvp_arch_fence_r_r(void);

/** be_mvp_arch_fence_r_w - a ring reader's fence before releasing. */
void be_mvp_arch_fence_r_w(void);

/** be_mvp_arch_fence_rw_rw - hart 0's data fence after the placement. */
void be_mvp_arch_fence_rw_rw(void);

/**
 * be_mvp_arch_fence_i - order the placed guest bytes before guest fetches
 *
 * The image's one fence.i, on each domain hart after its install readback.
 */
void be_mvp_arch_fence_i(void);

/** be_mvp_arch_park - a domain hart's park: HS wfi, forever. */
void be_mvp_arch_park(void) __attribute__((noreturn));

/**
 * be_mvp_arch_resume - check the controls and enter or return to the domain
 * @record: the hart's saved page, at its trusted-stack top
 * @expected_hgatp: the hart's installed hgatp
 * @expected_hedeleg: the hedeleg readback checked at arming (WARL)
 *
 * Checks that @record is sscratch, a block's trusted-stack top, every guest
 * control, @expected_hgatp, satp, stvec, sie, and sstatus, sets SPP from
 * the record's saved SPVP, restores sepc and every GPR from @record, and
 * executes one SRET. A failed check is terminal (resume). It writes no vs*
 * CSR, hgatp, or fence.
 */
void be_mvp_arch_resume(struct be_mvp_exit *record, be_u64 expected_hgatp,
			be_u64 expected_hedeleg) __attribute__((noreturn));

extern be_u8 be_mvp_trap_vector[];
extern be_u8 be_mvp_hart_entry[];
extern be_u8 __be_control_stack_end[];
extern be_u8 __be_mvp_pool_start[];
extern be_u8 __be_mvp_pool_end[];
extern be_u8 __be_mvp_hart_region_start[];
extern be_u8 __be_mvp_hart_region_end[];
extern be_u8 __be_mvp_region_start[];
extern be_u8 __be_mvp_region_end[];
extern be_u8 __be_mvp_bss_start[];
extern be_u8 __be_mvp_bss_end[];
/* The log's R2 ranges (mvp/docs/log-profile.md, 2.7): the monitor's and
 * the MVP region's text and constants, as src/mvp-monitor.lds bounds
 * them. */
extern be_u8 __be_monitor_rodata_start[];
extern be_u8 __be_monitor_rodata_end[];
extern be_u8 __be_mvp_text_start[];
extern be_u8 __be_mvp_text_end[];
extern be_u8 __be_mvp_rodata_start[];
extern be_u8 __be_mvp_rodata_end[];
extern const struct be_mvp_payload_layout be_mvp_payload_layout;
extern const struct be_mvp_binding be_mvp_bindings[BE_MVP_DOMAINS];

#endif
