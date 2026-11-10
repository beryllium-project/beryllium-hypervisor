/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP guest SBI core contract: exit classification (the SBI path
 *          and the supervisor software interrupt), each domain hart's exit
 *          ceiling, per-hart exit counters, the bounded B7 SBI subset (Base,
 *          TIME, DBCN, SRST) whose shutdown stops only the calling domain,
 *          the DBCN guest-range check against the domain's re-walked window,
 *          which since M7 also bounds the console read a domain whose
 *          sealed configuration grants console input is served
 *          (planning/mvp-m7-plan.md, D-1: the write-authority rule), the
 *          per-hart line console whose lines leave as LINE records, the
 *          IPI class with its PING and PONG, the denial entry of a scenario
 *          that accepts denials (planning/mvp-m1-plan.md, "The denial
 *          path"): the decision, the values the monitor injects, and the
 *          DENIAL record; the management extension of a scenario that
 *          accepts it (planning/mvp-m2-plan.md, "The management
 *          extension"): the domain hart's request and its wait for hart
 *          0's answer, hart 0's decision against the sealed grants, and
 *          the target hart's PAUSE and TERMINATE; the record types and
 *          payloads that cross the rings, a failed domain hart's wait for
 *          hart 0's ACK, whose window restarts on hart 0's progress (Q10,
 *          Plan revision M1-B), the per-domain CSR set written once at
 *          arming, the guest-control checks, and the fixed-format monitor
 *          line builder.
 * Trust:   restricted-C mechanism only. It reads no CSR, issues no SBI call,
 *          performs no I/O, and dereferences no guest address: it returns an
 *          action, or writes records into a ring view it is given, and the
 *          MVP runtime performs every privileged effect.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, planning/mvp-m1-plan.md,
 *          and planning/mvp-m2-plan.md). It selects no SBI profile,
 *          hypercall ABI, stable guest ABI, Linux guest interface, console
 *          protocol, IPI mechanism, management interface, or
 *          fault-injection or denial-log format for Beryllium, and no guest
 *          request is ever forwarded to M-mode.
 */

#ifndef BE_MVP_H
#define BE_MVP_H

#include <be/r4.h>

#include "mvp-gstage.h"
#include "mvp-layout.h"

/* Extension and function identifiers, compared as exact 64-bit values. */
#define BE_MVP_SBI_EID_BASE		BE_U64_C(0x10)
#define BE_MVP_SBI_EID_TIME		BE_U64_C(0x54494d45)
#define BE_MVP_SBI_EID_DBCN		BE_U64_C(0x4442434e)
#define BE_MVP_SBI_EID_SRST		BE_U64_C(0x53525354)

#define BE_MVP_SBI_BASE_GET_SPEC_VERSION	BE_U64_C(0)
#define BE_MVP_SBI_BASE_GET_IMPL_ID	BE_U64_C(1)
#define BE_MVP_SBI_BASE_GET_IMPL_VERSION	BE_U64_C(2)
#define BE_MVP_SBI_BASE_PROBE_EXTENSION	BE_U64_C(3)
#define BE_MVP_SBI_BASE_GET_MVENDORID	BE_U64_C(4)
#define BE_MVP_SBI_BASE_GET_MARCHID	BE_U64_C(5)
#define BE_MVP_SBI_BASE_GET_MIMPID	BE_U64_C(6)
#define BE_MVP_SBI_TIME_SET_TIMER	BE_U64_C(0)
#define BE_MVP_SBI_DBCN_WRITE		BE_U64_C(0)
#define BE_MVP_SBI_DBCN_READ		BE_U64_C(1)
#define BE_MVP_SBI_DBCN_WRITE_BYTE	BE_U64_C(2)
#define BE_MVP_SBI_SRST_SYSTEM_RESET	BE_U64_C(0)

/*
 * The management extension (planning/mvp-m2-plan.md, Q3 and "The
 * management extension"): an EID in the SBI 2.0 experimental range, FID 0
 * pause(target) and FID 1 terminate(target), a0 the target domain index.
 * An image supports it only when its scenario accepts it.
 */
#define BE_MVP_SBI_EID_MGMT		BE_U64_C(0x08004245)
#define BE_MVP_SBI_MGMT_PAUSE		BE_U64_C(0)
#define BE_MVP_SBI_MGMT_TERMINATE	BE_U64_C(1)

/*
 * Base values: SBI 2.0 and the provisional, unregistered MVP identity
 * BE_MVP_SBI_IMPL_ID (0x4245) and BE_MVP_SBI_IMPL_VERSION (5 since M7,
 * which serves DBCN read, mvp-layout.h) in an image without the
 * management extension; an image whose scenario accepts the extension
 * reports BE_MVP_SBI_IMPL_VERSION_MGMT (6; 4 before M7;
 * planning/mvp-m2-plan.md, Q3; planning/mvp-m7-plan.md, D-10 and Q11;
 * MVP plan D8).
 */
#define BE_MVP_SBI_SPEC_VERSION		BE_U64_C(0x2000000)
#define BE_MVP_SBI_IMPL_VERSION_MGMT	BE_U64_C(6)

/* Standard SBI errors the subset returns. */
#define BE_MVP_SBI_SUCCESS		0L
#define BE_MVP_SBI_ERR_NOT_SUPPORTED	(-2L)
#define BE_MVP_SBI_ERR_INVALID_PARAM	(-3L)
#define BE_MVP_SBI_ERR_DENIED		(-4L)
#define BE_MVP_SBI_ERR_INVALID_STATE	(-10L)

/* SRST arguments: types 0-2 and reasons 0-1 are defined; others reserved. */
#define BE_MVP_SRST_TYPE_SHUTDOWN	BE_U64_C(0)
#define BE_MVP_SRST_TYPE_COLD_REBOOT	BE_U64_C(1)
#define BE_MVP_SRST_TYPE_WARM_REBOOT	BE_U64_C(2)
#define BE_MVP_SRST_REASON_NONE		BE_U64_C(0)
#define BE_MVP_SRST_REASON_FAILURE	BE_U64_C(1)

/*
 * A management grant's permissions, as bits (planning/mvp-m2-plan.md,
 * "The management extension"): pause and terminate, the only verbs of the
 * sealed manifest's grants. The generated scenario header names them.
 */
#define BE_MVP_MGMT_PAUSE		BE_U64_C(1)
#define BE_MVP_MGMT_TERMINATE		BE_U64_C(2)
/* The most grants a table holds: one per ordered pair of domains. */
#define BE_MVP_MGMT_GRANTS_MAX		(BE_MVP_DOMAINS * BE_MVP_DOMAINS)
/*
 * be_mvp_mgmt_decide()'s answer for a request hart 0 delivers to its
 * target: a value no SBI error takes, so every other answer is the
 * request's result.
 */
#define BE_MVP_MGMT_DELIVER		1L

/*
 * Run limits: each domain's exit ceiling and the run's budget
 * (mvp-layout.h). The run budget is kept on hart 0's timer, not counted by
 * the domain harts. The QEMU-only negative variants exit-budget and
 * run-timeout lower one each with a compile-time switch, and anchor's
 * no-grant-check (planning/mvp-m2-plan.md, Q10) runs under 2^27 ticks,
 * the bound the positive run stays under, so that its timeout separates
 * the hang it declares from a completed run ("Budgets"); the state
 * carries the ceiling the core uses.
 */
#define BE_MVP_VARIANT_NO_GRANT_RUN_BUDGET	BE_U64_C(0x8000000)
#if defined(BE_MVP_VARIANT_EXIT_BUDGET)
#define BE_MVP_RUN_EXIT_CEILING		BE_MVP_VARIANT_EXIT_CEILING
#else
#define BE_MVP_RUN_EXIT_CEILING		BE_MVP_EXIT_CEILING
#endif
#if defined(BE_MVP_VARIANT_RUN_TIMEOUT)
#define BE_MVP_RUN_TIME_BUDGET		BE_MVP_VARIANT_RUN_BUDGET
#elif defined(BE_MVP_VARIANT_NO_GRANT_CHECK)
#define BE_MVP_RUN_TIME_BUDGET		BE_MVP_VARIANT_NO_GRANT_RUN_BUDGET
#else
#define BE_MVP_RUN_TIME_BUDGET		BE_MVP_RUN_BUDGET
#endif

/* Exit handling. */
#define BE_MVP_INSTRUCTION_SIZE		BE_U64_C(4)
#define BE_MVP_SCAUSE_INTERRUPT		(BE_U64_C(1) << 63)
/* The IPI: the supervisor software interrupt, the only interrupt a domain
 * hart takes at V=1. */
#define BE_MVP_SCAUSE_SUPERVISOR_SOFTWARE \
	(BE_MVP_SCAUSE_INTERRUPT | BE_U64_C(1))
#define BE_MVP_SCAUSE_FETCH_ACCESS_FAULT	BE_U64_C(1)
#define BE_MVP_SCAUSE_ILLEGAL_INSTRUCTION	BE_U64_C(2)
#define BE_MVP_SCAUSE_LOAD_ACCESS_FAULT	BE_U64_C(5)
#define BE_MVP_SCAUSE_STORE_ACCESS_FAULT	BE_U64_C(7)
#define BE_MVP_SCAUSE_VS_ECALL		BE_U64_C(10)
#define BE_MVP_SCAUSE_FETCH_GUEST_PAGE_FAULT	BE_U64_C(20)
#define BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT	BE_U64_C(21)
#define BE_MVP_SCAUSE_VIRTUAL_INSTRUCTION	BE_U64_C(22)
#define BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT	BE_U64_C(23)
#define BE_MVP_GPR_A2			BE_R4_GPR_INDEX(12U)

/*
 * Per-hart console: whole lines of at most 256 bytes, each leaving the hart
 * as one LINE record; hart 0 prints it with the domain's prefix and LF.
 */
#define BE_MVP_DBCN_MAX_BYTES		256U
#define BE_MVP_CONSOLE_LINE_BYTES	256U
#define BE_MVP_G0_PREFIX		"BE_MVP_G0: "
#define BE_MVP_G1_PREFIX		"BE_MVP_G1: "
#define BE_MVP_DOMAIN_PREFIX_LENGTH	11U
/* One printed domain line: the prefix, at most a full buffer, and LF. */
#define BE_MVP_PRINT_LINE_BYTES \
	(BE_MVP_DOMAIN_PREFIX_LENGTH + BE_MVP_CONSOLE_LINE_BYTES + 1U)
#define BE_MVP_CONSOLE_INVALID		(~BE_U64_C(0))
#define BE_MVP_CONSOLE_FULL		(~BE_U64_C(0) - 1U)

/* One monitor line, built from fixed text and formatted values. */
#define BE_MVP_LINE_CAPACITY		320U

/* Guest controls while a domain runs (planning/mvp-m0-plan.md). */
#define BE_MVP_HENVCFG_STCE		(BE_U64_C(1) << 63)
/*
 * The armed henvcfg, which the arm helper writes and the resume tail
 * requires: STCE only. beryllium-cheri: the three arming values
 * (BE_MVP_HENVCFG_ARMED, BE_MVP_HEDELEG, and BE_MVP_HEDELEG_REQUIRED)
 * are set per monitor variant; in the CHERI-aware monitor (BE_MVP_CHERI,
 * mvp/Makefile's MVP_MONITOR=cheri) the armed henvcfg also holds CHERI
 * v0.9.3's enable for VS-mode, henvcfg.CRE.
 */
#ifdef BE_MVP_CHERI
#define BE_MVP_HENVCFG_CRE		(BE_U64_C(1) << 28)
#define BE_MVP_HENVCFG_ARMED		(BE_MVP_HENVCFG_STCE | BE_MVP_HENVCFG_CRE)
#else
#define BE_MVP_HENVCFG_ARMED		BE_MVP_HENVCFG_STCE
#endif
/* VTVM, VTSR, and VTW stay clear, B6's value: a guest wfi runs natively. */
#define BE_MVP_HSTATUS_CLEARED_TRAPS \
	(BE_R3_HSTATUS_VTVM | BE_R3_HSTATUS_VTSR | BE_R3_HSTATUS_VTW)
#define BE_MVP_HSTATUS_GUEST_CONTROLS \
	(BE_R3_HSTATUS_CONTROL_VALUE & ~BE_MVP_HSTATUS_CLEARED_TRAPS)
/*
 * At a resume, SPVP is the guest's own mode at its exit (VS or VU), so it
 * is masked out, and the tail sets SPP from the saved SPVP.
 */
#define BE_MVP_HSTATUS_RESUME_MASK \
	(BE_R3_HSTATUS_CONTROL_MASK & ~BE_R3_HSTATUS_SPVP)
#define BE_MVP_HSTATUS_RESUME_CONTROLS \
	(BE_MVP_HSTATUS_GUEST_CONTROLS & ~BE_R3_HSTATUS_SPVP)
/* Causes 0, 2, 3, 4, 6, 8, 12, 13, and 15 go to the guest, as in B6. */
#if defined(BE_MVP_CHERI) && !defined(BE_MVP_VARIANT_CHERI_FAULT_HS)
/*
 * beryllium-cheri: and cause 28, CHERI v0.9.3's CHERI fault. The CHERI
 * Linux guest's te-poc variant cheri-fault-hs (planning/
 * cheri-enforcement-plan.md, section 6, C3) leaves it out of both values,
 * so that the guest's own CHERI fault reaches HS and ends the run.
 */
#define BE_MVP_HEDELEG			BE_U64_C(0x1000b15d)
#else
#define BE_MVP_HEDELEG			BE_U64_C(0xb15d)
#endif
/*
 * hedeleg is WARL, as in B6 and B7 (responsible-human direction fix-warl,
 * 2026-10-08): the readback may lack causes 0, 4, and 6; causes 2, 3, 8,
 * 12, 13, and 15 must stick, and no other bit may appear. The resume tail
 * then requires the armed readback. beryllium-cheri: in the CHERI-aware
 * monitor cause 28 must stick too, since a CHERI guest takes its own CHERI
 * faults; a hart that cannot delegate it is refused at arming, not failed
 * at the guest's first fault.
 */
#if defined(BE_MVP_CHERI) && !defined(BE_MVP_VARIANT_CHERI_FAULT_HS)
#define BE_MVP_HEDELEG_REQUIRED		BE_U64_C(0x1000b10c)
#else
#define BE_MVP_HEDELEG_REQUIRED		BE_U64_C(0xb10c)
#endif
#define BE_MVP_HIDELEG_VSTI		(BE_U64_C(1) << 6)
#define BE_MVP_HIE_VSTIE		(BE_U64_C(1) << 6)
/*
 * Only VSSIP, VSTIP, and VSEIP are tested in hvip: QEMU's hvip read also
 * shows a pending HS interrupt in the low bits, which the specification
 * makes zero.
 */
#define BE_MVP_HVIP_VS_BITS		BE_U64_C(0x444)
#define BE_MVP_HCOUNTEREN_TM		(BE_U64_C(1) << 1)
/* The IPI: sie.SSIE, with sstatus.SIE 0, so a domain hart takes it only at
 * V=1; hart 0 also enables STIE for its budget, in its wait only. */
#define BE_MVP_SIE_SSIE			(BE_U64_C(1) << 1)
#define BE_MVP_SIE_STIE			(BE_U64_C(1) << 5)
#define BE_MVP_SIE_CONTROL		(BE_MVP_SIE_SSIE | BE_MVP_SIE_STIE)
#define BE_MVP_VSTIMECMP_DISARMED	(~BE_U64_C(0))
#define BE_MVP_HSTATUS_SPV		BE_R3_HSTATUS_SPV
#define BE_MVP_HSTATUS_SPVP		BE_R3_HSTATUS_SPVP
#define BE_MVP_SSTATUS_SPP		BE_R3_SSTATUS_SPP
#define BE_MVP_SSTATUS_VS_MASK		(BE_U64_C(3) << 9)
/* The R3 sstatus control mask, plus VS, which the R3 mask omits. */
#define BE_MVP_SSTATUS_CONTROL_MASK \
	(BE_R3_SSTATUS_CONTROL_MASK | BE_MVP_SSTATUS_VS_MASK)
/* vsstatus.UXL = 2 (64-bit U-mode), as an RV64 hart reads it back. */
#define BE_MVP_VSSTATUS_UXL64		(BE_U64_C(2) << 32)

/*
 * The denial entry (planning/mvp-m1-plan.md, "The denial path", Q4 and Q5):
 * a guest-page fault from VU mode (hstatus SPV 1, SPVP 0, GVA 1) with an
 * htval below 2^39, an htinst that is zero or the transformed load (cause
 * 21) or store or AMO (cause 23) whose bit 0 is set and whose bits 6:2 are
 * the major opcode, a vstvec in Direct or Vectored mode, and a GPA the
 * hart's root does not map or, for a store, a page whose leaf in the
 * hart's root lacks W: M1's channel page, or a declared page of a scenario
 * with pages (planning/mvp-m2-plan.md). vsstatus has sstatus's layout.
 */
#define BE_MVP_HSTATUS_GVA		BE_R3_HSTATUS_GVA
#define BE_MVP_VSSTATUS_SIE		BE_R3_SSTATUS_SIE
#define BE_MVP_VSSTATUS_SPIE		BE_R3_SSTATUS_SPIE
#define BE_MVP_VSSTATUS_SPP		BE_R3_SSTATUS_SPP
#define BE_MVP_HTVAL_LIMIT		(BE_U64_C(1) << 39)
#define BE_MVP_GPA_LOW_MASK		BE_U64_C(3)
#define BE_MVP_HTVAL_SHIFT		2U
#define BE_MVP_HTINST_LIMIT		(BE_U64_C(1) << 32)
#define BE_MVP_HTINST_TRANSFORMED	BE_U64_C(1)
#define BE_MVP_HTINST_OPCODE_SHIFT	2U
#define BE_MVP_HTINST_OPCODE_MASK	BE_U64_C(0x1f)
#define BE_MVP_OPCODE_LOAD		BE_U64_C(0x00)
#define BE_MVP_OPCODE_STORE		BE_U64_C(0x08)
#define BE_MVP_OPCODE_AMO		BE_U64_C(0x0b)
#define BE_MVP_VSTVEC_MODE_MASK		BE_U64_C(3)
#define BE_MVP_VSTVEC_VECTORED		BE_U64_C(1)
/* The kinds a DENIAL record names: no mapping, or a page whose leaf lacks
 * W. */
#define BE_MVP_DENIAL_UNMAPPED		BE_U64_C(0)
#define BE_MVP_DENIAL_READ_ONLY		BE_U64_C(1)

/**
 * struct be_mvp_controls - guest-control readback after arming a hart
 * @hip: hip read right after vstimecmp was disarmed
 * @hstatus: hstatus
 * @hedeleg: hedeleg
 * @hideleg: hideleg
 * @hie: hie
 * @hvip: hvip
 * @hcounteren: hcounteren
 * @htimedelta: htimedelta
 * @henvcfg: henvcfg
 * @hgeie: hgeie
 * @vstimecmp: vstimecmp
 * @sie: sie
 * @sstatus: sstatus
 * @hgatp: hgatp
 * @vsatp: vsatp
 * @sscratch: sscratch, the hart's trusted-stack top the exit vector swaps in
 *
 * Only assembly reads these CSRs; C validates this monitor-owned copy.
 */
struct be_mvp_controls {
	be_u64 hip;
	be_u64 hstatus;
	be_u64 hedeleg;
	be_u64 hideleg;
	be_u64 hie;
	be_u64 hvip;
	be_u64 hcounteren;
	be_u64 htimedelta;
	be_u64 henvcfg;
	be_u64 hgeie;
	be_u64 vstimecmp;
	be_u64 sie;
	be_u64 sstatus;
	be_u64 hgatp;
	be_u64 vsatp;
	be_u64 sscratch;
};

/**
 * struct be_mvp_exit - one VS exit as the vector saved it
 * @frame: the accepted 320-byte struct be_r4_frame
 * @hstatus: hstatus at the exit (SPV, SPVP, GVA)
 * @htinst: htinst at the exit
 * @vsatp: the guest's vsatp at the exit
 * @time: the time CSR at the exit
 * @vsstatus: the guest's vsstatus at the exit, which a denial's injection
 *            starts from
 *
 * The vector writes it to the hart's saved page, at its trusted-stack top;
 * every entry and resume restores sepc and the GPRs from @frame, and sets
 * SPP from the SPVP bit of @hstatus.
 */
struct be_mvp_exit {
	struct be_r4_frame frame;
	be_u64 hstatus;
	be_u64 htinst;
	be_u64 vsatp;
	be_u64 time;
	be_u64 vsstatus;
};

/**
 * enum be_mvp_vcsr - the per-domain CSR set, in the arm helper's word order
 * @BE_MVP_VCSR_VSSTATUS: vsstatus
 * @BE_MVP_VCSR_VSIE: vsie (hie.VSTIE, with hideleg VSTI only)
 * @BE_MVP_VCSR_VSTVEC: vstvec
 * @BE_MVP_VCSR_VSSCRATCH: vsscratch
 * @BE_MVP_VCSR_VSEPC: vsepc
 * @BE_MVP_VCSR_VSCAUSE: vscause
 * @BE_MVP_VCSR_VSTVAL: vstval
 * @BE_MVP_VCSR_VSATP: vsatp
 * @BE_MVP_VCSR_VSTIMECMP: vstimecmp, the guest's own Sstc timer
 * @BE_MVP_VCSR_SCOUNTEREN: scounteren, which has no VS copy
 * @BE_MVP_VCSR_SENVCFG: senvcfg, which has no VS copy
 * @BE_MVP_VCSR_COUNT: number of CSRs, not a CSR
 *
 * Each domain hart writes the initial set once, at arming, and reads it
 * back; after that only TIME writes vstimecmp, and, in an image whose
 * scenario accepts denials, the injection helper vscause, vstval, vsepc,
 * and vsstatus, once per accepted denial.
 */
enum be_mvp_vcsr {
	BE_MVP_VCSR_VSSTATUS = 0,
	BE_MVP_VCSR_VSIE,
	BE_MVP_VCSR_VSTVEC,
	BE_MVP_VCSR_VSSCRATCH,
	BE_MVP_VCSR_VSEPC,
	BE_MVP_VCSR_VSCAUSE,
	BE_MVP_VCSR_VSTVAL,
	BE_MVP_VCSR_VSATP,
	BE_MVP_VCSR_VSTIMECMP,
	BE_MVP_VCSR_SCOUNTEREN,
	BE_MVP_VCSR_SENVCFG,
	BE_MVP_VCSR_COUNT,
};

/**
 * enum be_mvp_class - stable MVP terminal classes, printed as
 *                     BE_MVP:FAIL <name>
 * @BE_MVP_CLASS_NONE: no failure
 * @BE_MVP_CLASS_BOOT: boot contract, R1, R2, R3 check, binding, or install
 * @BE_MVP_CLASS_GSTAGE: an MVP root was refused, the two roots are not
 *                       disjoint, or an install read back another value
 * @BE_MVP_CLASS_SSTC: henvcfg.STCE reads back 0
 * @BE_MVP_CLASS_CONTROLS: a guest control did not read back as written
 * @BE_MVP_CLASS_PAYLOAD: the staged payload's layout or shape was refused
 * @BE_MVP_CLASS_INTERRUPT: an interrupt other than the IPI reached HS at V=1
 * @BE_MVP_CLASS_GUEST_PAGE_FAULT: fetch, load, or store guest-page fault
 * @BE_MVP_CLASS_VIRTUAL_INSTRUCTION: virtual-instruction exception
 * @BE_MVP_CLASS_ACCESS_FAULT: fetch, load, or store access fault
 * @BE_MVP_CLASS_ILLEGAL_INSTRUCTION: illegal-instruction exception
 * @BE_MVP_CLASS_EXCEPTION: any other exit, or one the core cannot accept
 * @BE_MVP_CLASS_EXIT_BUDGET: a domain took more exits than its ceiling
 * @BE_MVP_CLASS_RUN_TIMEOUT: hart 0's run budget expired, or its clock read
 *                            before the start
 * @BE_MVP_CLASS_RESUME: a resume check failed
 * @BE_MVP_CLASS_CONSOLE: a firmware console write failed
 * @BE_MVP_CLASS_GUEST_FAILURE: a guest requested shutdown with reason 1
 * @BE_MVP_CLASS_GUEST_REBOOT: a guest requested a cold or warm reboot
 * @BE_MVP_CLASS_SHUTDOWN_RETURNED: the monitor's SRST shutdown returned
 * @BE_MVP_CLASS_FIRMWARE: HSM or IPI is missing, or a hart is not STOPPED
 * @BE_MVP_CLASS_HART_START: a hart_start failed or its hart did not start
 * @BE_MVP_CLASS_HART_READY: a started hart posted no READY in time
 * @BE_MVP_CLASS_RING: a ring was full, malformed, or out of protocol
 * @BE_MVP_CLASS_IPI: an IPI found no PING or another record; or a PONG
 *                    came unasked, twice, or not before SHUTDOWN
 * @BE_MVP_CLASS_MEASUREMENT: a domain's launch register differs from the
 *                            image's expected launch register, its gate
 *                            (mvp/docs/log-profile.md, 2.9; before M9,
 *                            hart 0's measurement of the protected domain,
 *                            planning/mvp-m2-plan.md, "The measurement")
 * @BE_MVP_CLASS_MGMT: a domain hart's wait for hart 0's answer to its
 *                     management request saw neither hart 0's progress
 *                     on its outbound ring nor the answer for 2^24 ticks
 *                     (planning/mvp-m2-plan.md, Q14)
 * @BE_MVP_CLASS_LOG: the measurement log overflowed, refused a record,
 *                    or cannot close with the image's expected count
 *                    (mvp/docs/log-profile.md, 2.5; planning/
 *                    mvp-m9-plan.md, D-1)
 * @BE_MVP_CLASS_COUNT: number of classes, not a class
 */
enum be_mvp_class {
	BE_MVP_CLASS_NONE = 0,
	BE_MVP_CLASS_BOOT,
	BE_MVP_CLASS_GSTAGE,
	BE_MVP_CLASS_SSTC,
	BE_MVP_CLASS_CONTROLS,
	BE_MVP_CLASS_PAYLOAD,
	BE_MVP_CLASS_INTERRUPT,
	BE_MVP_CLASS_GUEST_PAGE_FAULT,
	BE_MVP_CLASS_VIRTUAL_INSTRUCTION,
	BE_MVP_CLASS_ACCESS_FAULT,
	BE_MVP_CLASS_ILLEGAL_INSTRUCTION,
	BE_MVP_CLASS_EXCEPTION,
	BE_MVP_CLASS_EXIT_BUDGET,
	BE_MVP_CLASS_RUN_TIMEOUT,
	BE_MVP_CLASS_RESUME,
	BE_MVP_CLASS_CONSOLE,
	BE_MVP_CLASS_GUEST_FAILURE,
	BE_MVP_CLASS_GUEST_REBOOT,
	BE_MVP_CLASS_SHUTDOWN_RETURNED,
	BE_MVP_CLASS_FIRMWARE,
	BE_MVP_CLASS_HART_START,
	BE_MVP_CLASS_HART_READY,
	BE_MVP_CLASS_RING,
	BE_MVP_CLASS_IPI,
	BE_MVP_CLASS_MEASUREMENT,
	BE_MVP_CLASS_MGMT,
	BE_MVP_CLASS_LOG,
	BE_MVP_CLASS_COUNT,
};

/**
 * enum be_mvp_phase - one-way phase of one domain hart
 * @BE_MVP_PHASE_RUNNING: exits are accepted
 * @BE_MVP_PHASE_STOPPED: the guest requested shutdown with reason 0
 * @BE_MVP_PHASE_FAILED: terminal failure; the class is sticky
 * @BE_MVP_PHASE_PAUSED: the hart took hart 0's PAUSE and parked: the
 *                       guest's state stays in the saved page, never
 *                       restored (planning/mvp-m2-plan.md, Q4 and Q15);
 *                       only a TERMINATE moves it on
 * @BE_MVP_PHASE_TERMINATED: the hart took hart 0's TERMINATE and parked
 *                           for the run
 */
enum be_mvp_phase {
	BE_MVP_PHASE_RUNNING = 0,
	BE_MVP_PHASE_STOPPED,
	BE_MVP_PHASE_FAILED,
	BE_MVP_PHASE_PAUSED,
	BE_MVP_PHASE_TERMINATED,
};

/**
 * enum be_mvp_action - what the runtime must do for one exit
 * @BE_MVP_ACTION_NONE: no decision
 * @BE_MVP_ACTION_RETURN: return the error and value to the guest
 * @BE_MVP_ACTION_CONSOLE_WRITE: copy the bytes at the HS physical source
 *                               through the hart's console, then return
 * @BE_MVP_ACTION_CONSOLE_BYTE: feed one byte to the hart's console, then
 *                              return
 * @BE_MVP_ACTION_CONSOLE_READ: a granted domain's DBCN read
 *                              (planning/mvp-m7-plan.md, D-1): copy at
 *                              most the result's length of the bytes
 *                              hart 0 routed to the domain into the guest
 *                              buffer at the HS physical target
 *                              (be_mvp_input_serve()), then return the
 *                              count
 * @BE_MVP_ACTION_SET_TIMER: write the timer value to vstimecmp, then return
 * @BE_MVP_ACTION_IPI: the IPI: clear sip.SSIP, serve the inbound ring
 *                     (be_mvp_ipi_serve()), then resume at the same sepc
 * @BE_MVP_ACTION_DENY: an accepted denial: inject the result's access
 *                      fault, read it back, post DENIAL, tell hart 0, and
 *                      resume in VS mode at the guest's trap vector
 * @BE_MVP_ACTION_MGMT: a management call (planning/mvp-m2-plan.md, "The
 *                      management extension"): post MGMT_REQUEST
 *                      (be_mvp_post_mgmt_request()), tell hart 0, wait in
 *                      HS for its MGMT_RESULT (be_mvp_wait_serve()), and
 *                      return its result in a0 after the ecall
 * @BE_MVP_ACTION_SHUTDOWN: guest shutdown, reason 0: flush the line, post
 *                          SHUTDOWN with the counters, and park the hart
 * @BE_MVP_ACTION_GUEST_FAILURE: guest shutdown, reason 1: fail and shut down
 * @BE_MVP_ACTION_GUEST_REBOOT: guest reboot request: fail and shut down
 * @BE_MVP_ACTION_TERMINAL: fail closed with the result's class
 */
enum be_mvp_action {
	BE_MVP_ACTION_NONE = 0,
	BE_MVP_ACTION_RETURN,
	BE_MVP_ACTION_CONSOLE_WRITE,
	BE_MVP_ACTION_CONSOLE_BYTE,
	BE_MVP_ACTION_CONSOLE_READ,
	BE_MVP_ACTION_SET_TIMER,
	BE_MVP_ACTION_IPI,
	BE_MVP_ACTION_DENY,
	BE_MVP_ACTION_MGMT,
	BE_MVP_ACTION_SHUTDOWN,
	BE_MVP_ACTION_GUEST_FAILURE,
	BE_MVP_ACTION_GUEST_REBOOT,
	BE_MVP_ACTION_TERMINAL,
};

/**
 * enum be_mvp_record_type - the records that cross the rings
 * @BE_MVP_RECORD_NONE: never a record
 * @BE_MVP_RECORD_READY: outbound: the hart's armed readbacks, before entry
 * @BE_MVP_RECORD_ENTERED: outbound: the first entry's pc, a0, and a1
 * @BE_MVP_RECORD_LINE: outbound: one console line, without prefix or LF
 * @BE_MVP_RECORD_PONG: outbound: the answer to a PING
 * @BE_MVP_RECORD_SHUTDOWN: outbound: the domain's counters at shutdown
 * @BE_MVP_RECORD_FAIL: outbound: the hart's terminal class and detail
 * @BE_MVP_RECORD_PING: inbound: hart 0's IPI probe
 * @BE_MVP_RECORD_ACK: inbound: hart 0's acknowledgement of a FAIL
 * @BE_MVP_RECORD_DENIAL: outbound: one accepted denial, posted before the
 *                        guest resumes
 * @BE_MVP_RECORD_MGMT_REQUEST: outbound: one management request, posted
 *                              before the hart waits for its answer
 * @BE_MVP_RECORD_PAUSED: outbound: the hart took hart 0's PAUSE and parked
 * @BE_MVP_RECORD_TERMINATED: outbound: the hart took hart 0's TERMINATE
 *                            and parked for the run
 * @BE_MVP_RECORD_MGMT_RESULT: inbound: hart 0's answer to the hart's
 *                             management request
 * @BE_MVP_RECORD_PAUSE: inbound: hart 0's delivery of a granted pause
 * @BE_MVP_RECORD_TERMINATE: inbound: hart 0's delivery of a granted
 *                           terminate
 * @BE_MVP_RECORD_INPUT: input: console bytes hart 0 routed to the domain
 *                       (planning/mvp-m7-plan.md, D-1), 1 to 256 of them,
 *                       which the domain hart copies to its guest at its
 *                       DBCN-read exits
 * @BE_MVP_RECORD_COUNT: number of types, not a type
 *
 * The record's header time is the writer's time CSR when it posted the
 * record. Payloads are little-endian 64-bit words in the order of the
 * BE_MVP_<TYPE>_* indices below, or a LINE's text.
 */
enum be_mvp_record_type {
	BE_MVP_RECORD_NONE = 0,
	BE_MVP_RECORD_READY,
	BE_MVP_RECORD_ENTERED,
	BE_MVP_RECORD_LINE,
	BE_MVP_RECORD_PONG,
	BE_MVP_RECORD_SHUTDOWN,
	BE_MVP_RECORD_FAIL,
	BE_MVP_RECORD_PING,
	BE_MVP_RECORD_ACK,
	BE_MVP_RECORD_DENIAL,
	BE_MVP_RECORD_MGMT_REQUEST,
	BE_MVP_RECORD_PAUSED,
	BE_MVP_RECORD_TERMINATED,
	BE_MVP_RECORD_MGMT_RESULT,
	BE_MVP_RECORD_PAUSE,
	BE_MVP_RECORD_TERMINATE,
	BE_MVP_RECORD_INPUT,
	BE_MVP_RECORD_COUNT,
};

/*
 * The record types each ring carries, as masks of 1 << type: the outbound
 * ring's, the inbound ring's, and the input ring's, which carries INPUT
 * alone and no control record (planning/mvp-m7-plan.md, D-1).
 */
#define BE_MVP_RECORD_BIT(type)		(BE_U64_C(1) << (type))
#define BE_MVP_RECORDS_OUTBOUND \
	(BE_MVP_RECORD_BIT(BE_MVP_RECORD_READY) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_ENTERED) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_LINE) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_PONG) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_SHUTDOWN) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_FAIL) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_DENIAL) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_MGMT_REQUEST) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_PAUSED) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_TERMINATED))
#define BE_MVP_RECORDS_INBOUND \
	(BE_MVP_RECORD_BIT(BE_MVP_RECORD_PING) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_ACK) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_MGMT_RESULT) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_PAUSE) | \
	 BE_MVP_RECORD_BIT(BE_MVP_RECORD_TERMINATE))
#define BE_MVP_RECORDS_INPUT		BE_MVP_RECORD_BIT(BE_MVP_RECORD_INPUT)

/* READY: the armed readbacks hart 0 prints in BE_MVP:09. */
#define BE_MVP_READY_HGATP		0U
#define BE_MVP_READY_HSTATUS		1U
#define BE_MVP_READY_HEDELEG		2U
#define BE_MVP_READY_HIDELEG		3U
#define BE_MVP_READY_HCOUNTEREN		4U
#define BE_MVP_READY_SIE		5U
#define BE_MVP_READY_HENVCFG		6U
#define BE_MVP_READY_VSTIMECMP		7U
#define BE_MVP_READY_WORDS		8U
/* ENTERED: the first entry's frame, printed in BE_MVP:10. */
#define BE_MVP_ENTERED_PC		0U
#define BE_MVP_ENTERED_A0		1U
#define BE_MVP_ENTERED_A1		2U
#define BE_MVP_ENTERED_WORDS		3U
/* PONG: the PING's time, the IPI exit's time, and hstatus.SPV then; the
 * header time is when the answer was posted (BE_MVP:11). */
#define BE_MVP_PONG_SENT		0U
#define BE_MVP_PONG_RECEIVED		1U
#define BE_MVP_PONG_SPV			2U
#define BE_MVP_PONG_WORDS		3U
/* SHUTDOWN: the domain's counters (BE_MVP:12), the outbound ring's
 * high-water mark, the time of its first entry, its accepted denials,
 * which hart 0 reconciles with the DENIAL records it drained, and its
 * management requests (planning/mvp-m2-plan.md), which hart 0 reconciles
 * with the MGMT_REQUEST records it drained; and, since M7, its served
 * console reads (planning/mvp-m7-plan.md, D-1), an SBI call class that
 * BE_MVP:12's sbi= counts. */
#define BE_MVP_SHUTDOWN_EXITS		0U
#define BE_MVP_SHUTDOWN_BASE		1U
#define BE_MVP_SHUTDOWN_TIME		2U
#define BE_MVP_SHUTDOWN_DBCN_WRITE	3U
#define BE_MVP_SHUTDOWN_DBCN_READ	4U
#define BE_MVP_SHUTDOWN_DBCN_BYTE	5U
#define BE_MVP_SHUTDOWN_SRST		6U
#define BE_MVP_SHUTDOWN_REFUSED		7U
#define BE_MVP_SHUTDOWN_IPI		8U
#define BE_MVP_SHUTDOWN_LINES		9U
#define BE_MVP_SHUTDOWN_RING_PEAK	10U
#define BE_MVP_SHUTDOWN_ENTERED		11U
#define BE_MVP_SHUTDOWN_DENIALS		12U
#define BE_MVP_SHUTDOWN_MGMT		13U
#define BE_MVP_SHUTDOWN_DBCN_INPUT	14U
#define BE_MVP_SHUTDOWN_WORDS		15U
/* FAIL: the class, then up to BE_MVP_FAIL_DETAIL_WORDS words of detail
 * that the hart's FAIL kind defines (M0-3's DETAIL formats). */
#define BE_MVP_FAIL_CLASS		0U
#define BE_MVP_FAIL_DETAIL_WORDS	8U
#define BE_MVP_FAIL_MAX_WORDS		(1U + BE_MVP_FAIL_DETAIL_WORDS)
/* DENIAL (planning/mvp-m1-plan.md, "The denial path"): the domain's denial
 * sequence number from 1, the cause, the kind, the GPA, htval, htinst,
 * stval, sepc, the guest's vsstatus and vstvec at the exit, the injected
 * vscause, and the exit's time; the header time is the post (BE_MVP:DENY). */
#define BE_MVP_DENIAL_SEQ		0U
#define BE_MVP_DENIAL_CAUSE		1U
#define BE_MVP_DENIAL_KIND		2U
#define BE_MVP_DENIAL_GPA		3U
#define BE_MVP_DENIAL_HTVAL		4U
#define BE_MVP_DENIAL_HTINST		5U
#define BE_MVP_DENIAL_STVAL		6U
#define BE_MVP_DENIAL_SEPC		7U
#define BE_MVP_DENIAL_VSSTATUS		8U
#define BE_MVP_DENIAL_VSTVEC		9U
#define BE_MVP_DENIAL_INJECTED		10U
#define BE_MVP_DENIAL_EXIT		11U
#define BE_MVP_DENIAL_WORDS		12U
/* MGMT_REQUEST (planning/mvp-m2-plan.md, "The management extension"): the
 * function (pause or terminate), the target domain as the guest named it,
 * and the domain's request sequence number from 1; the header time is the
 * request's (BE_MVP:MGMT). */
#define BE_MVP_MGMT_REQUEST_FID		0U
#define BE_MVP_MGMT_REQUEST_TARGET	1U
#define BE_MVP_MGMT_REQUEST_SEQ		2U
#define BE_MVP_MGMT_REQUEST_WORDS	3U
/* MGMT_RESULT: the request's result, an SBI error as a two's-complement
 * word, and its sequence number; the header time is hart 0's answer. */
#define BE_MVP_MGMT_RESULT_CODE		0U
#define BE_MVP_MGMT_RESULT_SEQ		1U
#define BE_MVP_MGMT_RESULT_WORDS	2U
/* PAUSE and TERMINATE: the requester domain. */
#define BE_MVP_PAUSE_BY			0U
#define BE_MVP_PAUSE_WORDS		1U
#define BE_MVP_TERMINATE_BY		0U
#define BE_MVP_TERMINATE_WORDS		1U
/* PAUSED and TERMINATED: the domain's exits when it took the order, and
 * the requester the order named; the header time is the transition's
 * (BE_MVP:12 DOMAIN_PAUSED and DOMAIN_TERMINATED). */
#define BE_MVP_PAUSED_EXITS		0U
#define BE_MVP_PAUSED_BY		1U
#define BE_MVP_PAUSED_WORDS		2U
#define BE_MVP_TERMINATED_EXITS		0U
#define BE_MVP_TERMINATED_BY		1U
#define BE_MVP_TERMINATED_WORDS		2U

/**
 * struct be_mvp_counts - one domain's exits, by kind and SBI call class
 * @exits: every exit, counted against the domain's ceiling
 * @base: Base calls answered with success
 * @time: TIME set_timer calls
 * @dbcn_write: DBCN write calls answered with success
 * @dbcn_read: DBCN read calls refused with SBI_ERR_DENIED: every one of a
 *             domain without the console-input grant
 * @dbcn_byte: DBCN write-byte calls
 * @srst: SRST calls that stopped the domain or ended the run
 * @refused: calls answered with SBI_ERR_NOT_SUPPORTED or _INVALID_PARAM
 * @ipi: IPI exits (supervisor software interrupts)
 * @lines: LINE records the hart's console posted
 * @denials: accepted denials, each a DENIAL record
 * @mgmt: management calls made (the extension's pause or terminate), each
 *        a MGMT_REQUEST record whose sequence number is this count
 * @dbcn_input: DBCN read calls served with success, 0 or more bytes, to a
 *              domain whose sealed configuration grants console input
 *              (planning/mvp-m7-plan.md, D-1)
 *
 * Every accepted exit adds one to exactly one of the call classes (@base
 * to @refused, @mgmt, and @dbcn_input), @ipi, and @denials, so in a run
 * that ends without failure @exits is their sum; @lines counts records,
 * not exits.
 */
struct be_mvp_counts {
	be_u64 exits;
	be_u64 base;
	be_u64 time;
	be_u64 dbcn_write;
	be_u64 dbcn_read;
	be_u64 dbcn_byte;
	be_u64 srst;
	be_u64 refused;
	be_u64 ipi;
	be_u64 lines;
	be_u64 denials;
	be_u64 mgmt;
	be_u64 dbcn_input;
};

/**
 * struct be_mvp_console - one hart's console line buffer
 * @length: bytes buffered, at most %BE_MVP_CONSOLE_LINE_BYTES
 * @text: the buffered, already filtered bytes of the current line
 */
struct be_mvp_console {
	be_u64 length;
	char text[BE_MVP_CONSOLE_LINE_BYTES];
};

/**
 * struct be_mvp_state - one domain hart's SBI-core state
 * @exit_ceiling: most exits the domain may take
 * @accept_denial: 1 when the image's accepted-exit set names the denial
 *                 entry (its scenario's, but in the no-inject variant),
 *                 else 0; written by hart 0 before the barrier
 * @accept_mgmt: 1 when the image's scenario accepts the management
 *               extension (planning/mvp-m2-plan.md, Q3), else 0; written
 *               by hart 0 before the barrier
 * @accept_input: 1 when the image's sealed configuration grants the
 *                domain console input (planning/mvp-m7-plan.md, D-5),
 *                else 0; written by hart 0 before the barrier from the
 *                sealed canonical state: only then is DBCN read served
 * @phase: RUNNING; STOPPED after its shutdown; PAUSED or TERMINATED after
 *         hart 0's order; or FAILED
 * @failure: sticky terminal class once @phase is FAILED
 * @counts: the domain's exits and calls by class
 * @console: the hart's line buffer
 * @by: the requester named by the PAUSE or TERMINATE the hart took last
 * @awaiting: while the hart waits for the answer to its management
 *            request, the request's sequence number; else 0
 * @answer: the result of the hart's latest MGMT_RESULT, a two's-complement
 *          SBI error
 */
struct be_mvp_state {
	be_u64 exit_ceiling;
	be_u64 accept_denial;
	be_u64 accept_mgmt;
	be_u64 accept_input;
	enum be_mvp_phase phase;
	enum be_mvp_class failure;
	struct be_mvp_counts counts;
	struct be_mvp_console console;
	be_u64 by;
	be_u64 awaiting;
	be_u64 answer;
};

#define BE_MVP_STATE_INITIALIZER(ceiling) { \
	.exit_ceiling = (ceiling), \
	.accept_denial = 0U, \
	.accept_mgmt = 0U, \
	.accept_input = 0U, \
	.phase = BE_MVP_PHASE_RUNNING, \
	.failure = BE_MVP_CLASS_NONE, \
}

/**
 * struct be_mvp_mgmt_grant - one sealed management grant
 * @from: the domain that may make the request
 * @to: the domain the request may name as its target
 * @permissions: %BE_MVP_MGMT_PAUSE, %BE_MVP_MGMT_TERMINATE, or both
 *
 * The generated scenario header's BE_MVP_SCENARIO_GRANT_INITIALIZER lists
 * the sealed manifest's grants in this order (planning/mvp-m2-plan.md,
 * "The policy, the labeling, and the manifest"); only hart 0 reads them.
 */
struct be_mvp_mgmt_grant {
	be_u64 from;
	be_u64 to;
	be_u64 permissions;
};

/**
 * enum be_mvp_target_state - a request's target as hart 0 sees it
 * @BE_MVP_TARGET_RUNNING: its guest runs, and no request involves it
 * @BE_MVP_TARGET_PAUSED: paused, never resumed
 * @BE_MVP_TARGET_TERMINATED: terminated
 * @BE_MVP_TARGET_SHUTDOWN: its guest shut down
 * @BE_MVP_TARGET_PENDING: a request involves it: one delivered to it
 *                         awaits its PAUSED or TERMINATED, or its own
 *                         awaits its answer while its hart waits in HS
 * @BE_MVP_TARGET_COUNT: number of states, not a state
 */
enum be_mvp_target_state {
	BE_MVP_TARGET_RUNNING = 0,
	BE_MVP_TARGET_PAUSED,
	BE_MVP_TARGET_TERMINATED,
	BE_MVP_TARGET_SHUTDOWN,
	BE_MVP_TARGET_PENDING,
	BE_MVP_TARGET_COUNT,
};

/**
 * struct be_mvp_denial - one accepted denial: what the monitor logs and
 *                        what it injects (planning/mvp-m1-plan.md, "The
 *                        denial path")
 * @cause: scause: 20 (fetch), 21 (load), or 23 (store or AMO)
 * @kind: %BE_MVP_DENIAL_UNMAPPED, or %BE_MVP_DENIAL_READ_ONLY for a store
 *        to a page whose leaf in the hart's root lacks W
 * @gpa: the faulting GPA, (htval << 2) | (stval & 3)
 * @htval: htval at the exit, logged only
 * @htinst: htinst at the exit, logged only
 * @stval: stval at the exit, the faulting guest virtual address
 * @sepc: sepc at the exit, the faulting instruction
 * @vsstatus: the guest's vsstatus at the exit
 * @vstvec: the guest's vstvec at the exit
 * @time: the exit's time
 * @inject_vscause: 1, 5, or 7 for @cause 20, 21, or 23: the corresponding
 *                  access fault
 * @inject_vstval: @stval
 * @inject_vsepc: @sepc
 * @inject_vsstatus: @vsstatus with SPP the guest's mode at the fault (VU,
 *                   so 0), SPIE its SIE, and SIE 0, every other bit kept
 * @resume_pc: @vstvec's BASE, where the guest resumes in VS mode
 */
struct be_mvp_denial {
	be_u64 cause;
	be_u64 kind;
	be_u64 gpa;
	be_u64 htval;
	be_u64 htinst;
	be_u64 stval;
	be_u64 sepc;
	be_u64 vsstatus;
	be_u64 vstvec;
	be_u64 time;
	be_u64 inject_vscause;
	be_u64 inject_vstval;
	be_u64 inject_vsepc;
	be_u64 inject_vsstatus;
	be_u64 resume_pc;
};

/*
 * The injection helper's four words (be_mvp_arch_inject()), in its argument
 * and readback order.
 */
#define BE_MVP_INJECT_VSCAUSE		0U
#define BE_MVP_INJECT_VSTVAL		1U
#define BE_MVP_INJECT_VSEPC		2U
#define BE_MVP_INJECT_VSSTATUS		3U
#define BE_MVP_INJECT_WORDS		4U

/**
 * struct be_mvp_result - the decision for one exit
 * @action: what the runtime must do
 * @failure: terminal class for %BE_MVP_ACTION_TERMINAL
 * @error: SBI error the guest receives in a0
 * @value: SBI value the guest receives in a1
 * @source_pa: HS physical address of the first DBCN byte
 * @length: DBCN bytes to copy, at most %BE_MVP_DBCN_MAX_BYTES
 * @target_pa: for %BE_MVP_ACTION_CONSOLE_READ, HS physical address of the
 *             guest buffer's first byte, inside the domain's window
 * @timer: vstimecmp value for %BE_MVP_ACTION_SET_TIMER
 * @resume_pc: guest PC after the ecall, or the interrupted PC
 * @byte: the DBCN write-byte argument
 * @denial: for %BE_MVP_ACTION_DENY, the accepted denial
 * @fid: for %BE_MVP_ACTION_MGMT, the function: pause or terminate
 * @target: for %BE_MVP_ACTION_MGMT, the target domain, the guest's a0
 *
 * For %BE_MVP_ACTION_MGMT, @error is the answer the hart waits for; the
 * runtime writes the MGMT_RESULT's result there before it returns.
 */
struct be_mvp_result {
	enum be_mvp_action action;
	enum be_mvp_class failure;
	long error;
	be_u64 value;
	be_u64 source_pa;
	be_u64 length;
	be_u64 target_pa;
	be_u64 timer;
	be_u64 resume_pc;
	be_u8 byte;
	struct be_mvp_denial denial;
	be_u64 fid;
	be_u64 target;
};

/**
 * struct be_mvp_line - one bounded monitor line
 * @text: line bytes, not NUL-terminated
 * @length: bytes used
 * @overflow: nonzero once any append did not fit; the line is then unusable
 */
struct be_mvp_line {
	char text[BE_MVP_LINE_CAPACITY];
	be_u64 length;
	be_u32 overflow;
};

/* A view of one ring (mvp-ring.h). */
struct be_mvp_ring;

/**
 * be_mvp_stce_class - classify the henvcfg readback after writing STCE only
 * @henvcfg: henvcfg readback
 *
 * Return: NONE when it reads back exactly STCE, SSTC when STCE reads 0
 *         (no Sstc, or M-mode left menvcfg.STCE clear), otherwise CONTROLS.
 *         beryllium-cheri: the helper writes the armed henvcfg
 *         (BE_MVP_HENVCFG_ARMED), so in the CHERI-aware monitor NONE needs
 *         exactly STCE and CRE.
 */
enum be_mvp_class be_mvp_stce_class(be_u64 henvcfg);

/**
 * be_mvp_controls_valid - check a domain hart's controls before its entry
 * @controls: readback after arming
 * @expected_hgatp: the hgatp the hart installed, its domain's
 * @trusted_top: the hart's trusted-stack top
 *
 * Return: 1 when every control holds its guest-run value: hip 0 after the
 *         timer was disarmed; hstatus controls 0x180 (SPV, SPVP; VTW, VTVM,
 *         and VTSR clear); hedeleg within 0xb15d and holding 0xb10c (WARL);
 *         hideleg VSTI only; hie, htimedelta, and hgeie 0; hvip's VS bits
 *         0; hcounteren TM only; henvcfg STCE only; vstimecmp ~0; sie SSIE
 *         only; sstatus SIE, SPIE, SPP, FS, VS, XS, SUM, and MXR 0;
 *         @expected_hgatp; Bare vsatp; and sscratch the trusted top.
 *         Otherwise 0. beryllium-cheri: in the CHERI-aware monitor,
 *         hedeleg within 0x1000b15d and holding 0x1000b10c, and henvcfg
 *         STCE and CRE only (BE_MVP_HEDELEG, BE_MVP_HEDELEG_REQUIRED, and
 *         BE_MVP_HENVCFG_ARMED).
 */
int be_mvp_controls_valid(const struct be_mvp_controls *controls,
			  be_u64 expected_hgatp, be_u64 trusted_top);

/**
 * be_mvp_class_name - stable class name printed after BE_MVP:FAIL
 * @failure: class to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_mvp_class_name(enum be_mvp_class failure);

/**
 * be_mvp_classify_cause - classify an exit that is not the IPI
 * @scause: HS scause captured on the exit
 *
 * Return: %BE_MVP_CLASS_NONE for a VS ecall (cause 10), the SBI path;
 *         otherwise the terminal class of the exit, as in B7. A guest-page
 *         fault is guest-page-fault here: be_mvp_handle_exit() first offers
 *         it to the denial entry.
 */
enum be_mvp_class be_mvp_classify_cause(be_u64 scause);

/**
 * be_mvp_denial_decide - decide one guest-page fault against the denial
 *                        entry
 * @state: the hart's state, whose @accept_denial says whether the image
 *         accepts denials
 * @map: the hart's walked window
 * @leaves: the hart's walked leaves of its root's pages, by page index:
 *          M1's channel leaf as page 0, or a scenario's declared pages
 *          (planning/mvp-m2-plan.md); all zero for none
 * @record: the exit record the vector saved
 * @out: zeroed first; on accept, the denial and the values to inject
 *
 * A pure function of the record and the hart's private state: it consults
 * no type, rule, or policy, only the root the hart installed (its walked
 * window and leaves). It accepts exactly the plan's entry: @accept_denial
 * 1; scause 20, 21, or 23; hstatus SPV 1, SPVP 0, and GVA 1; htval below
 * 2^39; htinst zero, or below 2^32 with bit 0 set and bits 6:2 the LOAD
 * opcode for cause 21 or the STORE or AMO opcode for cause 23 (never a
 * pseudoinstruction, whose bits 1:0 are clear); vstvec in Direct or
 * Vectored mode; and a GPA, (htval << 2) | (stval & 3), outside the window
 * and every page the root maps (unmapped, any of the three causes), or,
 * for cause 23, inside a page whose leaf lacks W (read-only). A fetch from
 * or a load of a mapped page, a store to a writable one, any fault inside
 * the window, and a fault from VS mode are refused.
 *
 * Return: 1 to accept, with @out filled; 0 to refuse, with @out zero.
 */
int be_mvp_denial_decide(const struct be_mvp_state *state,
			 const struct be_mvp_gstage_map *map,
			 const struct be_mvp_gstage_leaves *leaves,
			 const struct be_mvp_exit *record,
			 struct be_mvp_denial *out);

/**
 * be_mvp_handle_exit - count and classify one exit, and decide it
 * @state: the hart's state
 * @map: its domain's walked window
 * @leaves: its domain's walked page leaves, all zero for none
 * @record: the monitor-owned exit record the vector saved
 * @result: the decision
 *
 * Counts the exit against the domain's ceiling, then decides. The
 * supervisor software interrupt is the IPI; a VS ecall is an SBI call,
 * the management extension's pause or terminate among them in an image
 * that accepts it (%BE_MVP_ACTION_MGMT, counted in @mgmt), and a DBCN read
 * (planning/mvp-m7-plan.md, D-1): refused with SBI_ERR_DENIED, counted in
 * @dbcn_read, unless @state's @accept_input grants the domain console
 * input; then a2 other than 0 or a range [a1, a1 + a0) that
 * be_mvp_gstage_translate() refuses against @map (an addition that
 * overflows, a range past the window's end, the channel page or a
 * declared page, all outside the window) is SBI_ERR_INVALID_PARAM,
 * counted in @refused, a count of 0 returns 0 at once, and any other is
 * %BE_MVP_ACTION_CONSOLE_READ with the buffer's HS address and at most
 * %BE_MVP_DBCN_MAX_BYTES, each counted in @dbcn_input; a guest-page
 * fault that be_mvp_denial_decide() accepts is a denial, counted in
 * @denials, with the result's @denial filled. Every other exit, and every
 * exit after the hart failed, its domain stopped, or hart 0 paused or
 * terminated it, is terminal. A terminal decision moves the hart to
 * FAILED; a guest shutdown with reason 0 moves it to STOPPED.
 *
 * Return: the decided action.
 */
enum be_mvp_action be_mvp_handle_exit(struct be_mvp_state *state,
				      const struct be_mvp_gstage_map *map,
				      const struct be_mvp_gstage_leaves *leaves,
				      const struct be_mvp_exit *record,
				      struct be_mvp_result *result);

/**
 * be_mvp_ipi_serve - serve one IPI from the hart's inbound ring
 * @state: the hart's state, RUNNING
 * @inbound: the hart's acquired reader view of its inbound ring
 * @outbound: the hart's writer view of its outbound ring
 * @record: the IPI's exit record: its time is the receipt, its hstatus.SPV
 *          says whether the IPI arrived at V=1
 * @now: the time CSR as the answers are posted
 *
 * Takes every record up to the acquired head and answers each at @now: a
 * PING with one PONG (the PING's time, the receipt, and SPV); and, in an
 * image that accepts the management extension (planning/mvp-m2-plan.md,
 * Q15), a PAUSE with PAUSED, which moves the hart to PAUSED, and a
 * TERMINATE, also after a PAUSE, with TERMINATED, which moves it to
 * TERMINATED; each names the domain's exits and the order's requester.
 * Before a running domain's PAUSED or TERMINATED, its unterminated
 * console line is posted as its last LINE (be_mvp_console_flush();
 * planning/mvp-m7-plan.md, Q9), so hart 0 prints it with its prefix.
 * Any other record, a PING after a PAUSE or TERMINATE, or a record after
 * a TERMINATE, is refused. The caller acquired the inbound ring and
 * ordered its loads (fence r, r) before, and releases it and publishes
 * the outbound ring after; a hart then PAUSED or TERMINATED parks.
 *
 * Return: the records taken, each answered, at least 1; or 0, with the
 *         hart FAILED as ipi (an empty inbound ring, or a record refused)
 *         or ring (a malformed inbound ring or a full outbound ring).
 */
be_u64 be_mvp_ipi_serve(struct be_mvp_state *state,
			struct be_mvp_ring *inbound,
			struct be_mvp_ring *outbound,
			const struct be_mvp_exit *record, be_u64 now);

/**
 * be_mvp_wait_serve - serve a domain hart's inbound ring outside an exit
 * @state: the hart's state: RUNNING and waiting for the answer to its
 *         management request, or PAUSED, or TERMINATED
 * @inbound: the hart's acquired reader view of its inbound ring
 * @outbound: the hart's writer view of its outbound ring
 * @now: the time CSR: the receipt of a PING and the time of each answer
 * @posted: the records posted to @outbound, which the caller publishes
 *
 * planning/mvp-m2-plan.md, Q14 and Q15: a hart waiting in HS for its
 * MGMT_RESULT takes a PING, answered with a PONG whose SPV is 0 (the IPI
 * arrived in HS), and the MGMT_RESULT of its request's sequence number,
 * whose result becomes @state's @answer and which ends the wait (@state's
 * @awaiting becomes 0); a PAUSED hart takes only a TERMINATE, answered
 * with TERMINATED; a TERMINATED hart takes nothing. Any other record is
 * refused, as be_mvp_ipi_serve() refuses one; an empty ring is not: the
 * hart looks whenever an IPI may have arrived. The caller's fences are
 * be_mvp_ipi_serve()'s.
 *
 * Return: 1, with @posted set; or 0, with the hart FAILED as ipi (a record
 *         refused, or a hart in no state to wait) or ring (a malformed
 *         inbound ring or a full outbound ring).
 */
int be_mvp_wait_serve(struct be_mvp_state *state, struct be_mvp_ring *inbound,
		      struct be_mvp_ring *outbound, be_u64 now,
		      be_u64 *posted);

/**
 * be_mvp_counts_sbi - one domain's SBI calls of every class
 * @counts: the domain's counts
 *
 * Return: base + time + dbcn_write + dbcn_read + dbcn_byte + srst + refused
 *         + mgmt + dbcn_input.
 */
be_u64 be_mvp_counts_sbi(const struct be_mvp_counts *counts);

/**
 * be_mvp_mgmt_decide - hart 0's decision on one management request
 * @grants: the sealed manifest's grants
 * @count: how many, at most %BE_MVP_MGMT_GRANTS_MAX
 * @requester: the domain whose ring the request came from
 * @fid: the function, %BE_MVP_SBI_MGMT_PAUSE or %BE_MVP_SBI_MGMT_TERMINATE
 * @target: the target domain the guest named
 * @state: the target's state, as hart 0 sees it
 *
 * planning/mvp-m2-plan.md, Q3 and Q14, in this order: another function is
 * %BE_MVP_SBI_ERR_NOT_SUPPORTED (a domain hart answers it before any
 * request); a target that is no domain, %BE_MVP_SBI_ERR_INVALID_PARAM; no
 * grant from @requester to @target with the function's permission, the
 * requester itself included unless a grant names it, %BE_MVP_SBI_ERR_DENIED
 * (absent grants, or more than %BE_MVP_MGMT_GRANTS_MAX, grant nothing); a
 * target terminated, shut down, or pending, or a pause of a paused one,
 * %BE_MVP_SBI_ERR_INVALID_STATE; and otherwise delivery, a terminate of a
 * paused target included. A pure function: it reads only its arguments.
 *
 * Return: %BE_MVP_MGMT_DELIVER, or the request's result, an SBI error.
 */
long be_mvp_mgmt_decide(const struct be_mvp_mgmt_grant *grants, be_u64 count,
			be_u64 requester, be_u64 fid, be_u64 target,
			enum be_mvp_target_state state);

/**
 * be_mvp_inject_words - the four values the injection helper writes
 * @denial: an accepted denial
 * @words: %BE_MVP_INJECT_WORDS words, in the helper's order: vscause,
 *         vstval, vsepc, vsstatus
 */
void be_mvp_inject_words(const struct be_mvp_denial *denial, be_u64 *words);

/**
 * be_mvp_inject_mismatch - compare the injection helper's readback
 * @written: the %BE_MVP_INJECT_WORDS values written
 * @readback: the values it read back, in the same order
 *
 * Return: the first index whose readback differs, or %BE_MVP_INJECT_WORDS
 *         when all four match; 0 when either pointer is absent.
 */
be_u32 be_mvp_inject_mismatch(const be_u64 *written, const be_u64 *readback);

/**
 * be_mvp_inject_vcsr - the per-domain CSR an injection word writes
 * @index: a BE_MVP_INJECT_* index
 *
 * Return: its &enum be_mvp_vcsr index, for a register DETAIL line, or
 *         %BE_MVP_VCSR_COUNT for another index.
 */
be_u32 be_mvp_inject_vcsr(be_u32 index);

/**
 * be_mvp_apply_return - write one decision into the saved frame
 * @frame: the monitor-owned frame
 * @result: a non-terminal decision
 *
 * An SBI decision writes a0, a1, and sepc (the resume PC), a management
 * call's once the runtime has its answer, and a served console read's
 * once the runtime has copied its bytes and set the count as the value
 * (planning/mvp-m7-plan.md, D-1); every other action, the IPI included,
 * changes nothing.
 */
void be_mvp_apply_return(struct be_r4_frame *frame,
			 const struct be_mvp_result *result);

/**
 * be_mvp_entry_frame - fill a first-entry exit record
 * @record: the record
 * @pc: the first guest PC (sepc)
 * @hart: the guest's a0, its own hart number, 0
 * @dtb: the guest's a1
 *
 * hstatus becomes SPV and SPVP, so the entry is into VS mode; every other
 * field, including every other GPR, becomes 0.
 */
void be_mvp_entry_frame(struct be_mvp_exit *record, be_u64 pc, be_u64 hart,
			be_u64 dtb);

/**
 * be_mvp_record_spp - the sstatus.SPP an entry or resume must carry
 * @record: an exit or first-entry record
 *
 * Return: SPP (0x100) when the record's SPVP is set (VS mode), else 0 (VU
 *         mode). The resume tail applies the same rule.
 */
be_u64 be_mvp_record_spp(const struct be_mvp_exit *record);

/**
 * be_mvp_vcsr_initial - fill a domain's initial CSR set
 * @csr: %BE_MVP_VCSR_COUNT words
 *
 * Every CSR is 0, but vsstatus holds UXL = 2 (RV64) and vstimecmp is ~0.
 */
void be_mvp_vcsr_initial(be_u64 *csr);

/**
 * be_mvp_vcsr_mismatch - compare a written CSR set's readback
 * @expected: the values the arm helper wrote
 * @readback: the values it read back
 *
 * Return: the first index whose readback differs, or %BE_MVP_VCSR_COUNT
 *         when every word matches; 0 when either pointer is absent.
 */
be_u32 be_mvp_vcsr_mismatch(const be_u64 *expected, const be_u64 *readback);

/**
 * be_mvp_vcsr_name - the CSR name a readback DETAIL line prints
 * @index: an &enum be_mvp_vcsr index
 *
 * Return: constant name, or "invalid".
 */
const char *be_mvp_vcsr_name(be_u32 index);

/**
 * be_mvp_fail - enter the sticky terminal state
 * @state: the hart's state, if available
 * @failure: class to retain; NONE is recorded as EXCEPTION
 *
 * Return: the retained class (the first one, if already FAILED).
 */
enum be_mvp_class be_mvp_fail(struct be_mvp_state *state,
			      enum be_mvp_class failure);

/**
 * be_mvp_domain_prefix - a domain's console prefix
 * @domain: 0 or 1
 *
 * Return: "BE_MVP_G0: " or "BE_MVP_G1: ", or 0 for another domain.
 */
const char *be_mvp_domain_prefix(be_u32 domain);

/**
 * be_mvp_console_feed - buffer a hart's bytes and post whole lines
 * @state: the hart's state, whose console and line count it updates
 * @outbound: the hart's writer view of its outbound ring
 * @input: guest bytes, already copied into monitor memory
 * @length: at most %BE_MVP_DBCN_MAX_BYTES
 * @now: the time CSR, each LINE record's time
 *
 * CR is dropped and every other byte outside 0x20-0x7e but LF becomes '?'.
 * Each LF ends the buffered line, and a byte that finds the buffer full
 * first ends the full line; each ended line is posted as one LINE record
 * holding the line without prefix or LF. Bytes after the last ended line
 * stay buffered. The caller publishes the ring afterwards.
 *
 * Return: LINE records posted (0 when no line ended);
 *         %BE_MVP_CONSOLE_INVALID for invalid input or a hart that is not
 *         RUNNING (nothing changed); or %BE_MVP_CONSOLE_FULL when the ring
 *         refused a line, which fails the hart as ring.
 */
be_u64 be_mvp_console_feed(struct be_mvp_state *state,
			   struct be_mvp_ring *outbound, const be_u8 *input,
			   be_u64 length, be_u64 now);

/**
 * be_mvp_console_flush - end a hart's partial line
 * @state: the hart's state, in any phase: the line is flushed at shutdown
 *         and before a FAIL
 * @outbound: the hart's writer view of its outbound ring
 * @now: the time CSR
 *
 * Return: 1 when the partial line was posted, 0 when nothing was buffered,
 *         or %BE_MVP_CONSOLE_INVALID or %BE_MVP_CONSOLE_FULL as for
 *         be_mvp_console_feed().
 */
be_u64 be_mvp_console_flush(struct be_mvp_state *state,
			    struct be_mvp_ring *outbound, be_u64 now);

/**
 * be_mvp_post_ready - post READY with the armed readbacks
 * @outbound: the hart's writer view of its outbound ring
 * @controls: the armed readback
 * @now: the time CSR
 *
 * Return: 1, or 0 when the ring refused it.
 */
int be_mvp_post_ready(struct be_mvp_ring *outbound,
		      const struct be_mvp_controls *controls, be_u64 now);

/**
 * be_mvp_post_entered - post ENTERED with the first entry's frame
 * @outbound: the hart's writer view of its outbound ring
 * @record: the first-entry record
 * @now: the time CSR, the domain's entry time
 *
 * Return: 1, or 0 when the ring refused it.
 */
int be_mvp_post_entered(struct be_mvp_ring *outbound,
			const struct be_mvp_exit *record, be_u64 now);

/**
 * be_mvp_post_shutdown - post SHUTDOWN with the domain's counters
 * @state: the hart's state, STOPPED
 * @outbound: the hart's writer view of its outbound ring
 * @entered: the time of the domain's first entry
 * @now: the time CSR, the domain's shutdown time
 *
 * The high-water mark is the outbound ring's over every record before this
 * one; then come the domain's accepted denials, its management calls, and
 * its served console reads (planning/mvp-m7-plan.md, D-1).
 *
 * Return: 1, or 0 when the hart is not STOPPED or the ring refused it.
 */
int be_mvp_post_shutdown(struct be_mvp_state *state,
			 struct be_mvp_ring *outbound, be_u64 entered,
			 be_u64 now);

/**
 * be_mvp_post_denial - post DENIAL for the latest accepted denial
 * @state: the hart's state, RUNNING, whose @denials counts this one
 * @outbound: the hart's writer view of its outbound ring
 * @denial: the denial be_mvp_handle_exit() accepted
 * @now: the time CSR, the post
 *
 * The record's sequence number is @state's @denials, so the domain's
 * first denial is 1.
 *
 * Return: 1, or 0 for absent or invalid input or when the ring refused it.
 */
int be_mvp_post_denial(const struct be_mvp_state *state,
		       struct be_mvp_ring *outbound,
		       const struct be_mvp_denial *denial, be_u64 now);

/**
 * be_mvp_post_mgmt_request - post MGMT_REQUEST and start the hart's wait
 * @state: the hart's state, RUNNING in an image that accepts the
 *         management extension, whose @mgmt counts this call
 * @outbound: the hart's writer view of its outbound ring
 * @result: the %BE_MVP_ACTION_MGMT decision be_mvp_handle_exit() made
 * @now: the time CSR, the request's time
 *
 * planning/mvp-m2-plan.md, "The management extension": the record names
 * the function, the target, and the sequence number, @state's @mgmt, so
 * the domain's first request is 1; @state's @awaiting becomes that number
 * until be_mvp_wait_serve() takes its answer.
 *
 * Return: 1, or 0 for absent or invalid input, a hart already waiting, or
 *         when the ring refused it.
 */
int be_mvp_post_mgmt_request(struct be_mvp_state *state,
			     struct be_mvp_ring *outbound,
			     const struct be_mvp_result *result, be_u64 now);

/**
 * be_mvp_post_fail - post FAIL with the hart's class and detail
 * @state: the hart's state, FAILED
 * @outbound: the hart's writer view of its outbound ring
 * @detail: up to %BE_MVP_FAIL_DETAIL_WORDS words, or absent
 * @words: how many
 * @now: the time CSR
 *
 * Return: 1, or 0 when the hart is not FAILED, the detail is too long, or
 *         the ring refused it (the hart then prints its own FAIL lines).
 */
int be_mvp_post_fail(struct be_mvp_state *state,
		     struct be_mvp_ring *outbound, const be_u64 *detail,
		     be_u64 words, be_u64 now);

/**
 * struct be_mvp_ack_wait - a domain hart's wait for hart 0: a failed
 *                          hart's for its ACK (Q10, Plan revision M1-B),
 *                          and a requester's for its MGMT_RESULT
 *                          (planning/mvp-m2-plan.md, Q14)
 * @since: the time CSR when the window last started or restarted
 * @taken: the outbound ring's tail when the window last started or
 *         restarted: the bytes hart 0 had taken from the ring
 */
struct be_mvp_ack_wait {
	be_u64 since;
	be_u64 taken;
};

/**
 * enum be_mvp_ack_step - what a failed domain hart does next
 * @BE_MVP_ACK_WAIT: wait on, and read the time, the tail, the head, and
 *                   the inbound ring again
 * @BE_MVP_ACK_PARK: hart 0 has acknowledged the FAIL: park
 * @BE_MVP_ACK_FALLBACK: print the hart's own FAIL and DETAIL lines and
 *                       request SRST
 */
enum be_mvp_ack_step {
	BE_MVP_ACK_WAIT = 0,
	BE_MVP_ACK_PARK,
	BE_MVP_ACK_FALLBACK,
};

/**
 * be_mvp_ack_wait_start - start a failed domain hart's wait for the ACK
 * @wait: the wait
 * @now: the time CSR, once the FAIL is published and hart 0 told
 * @taken: the outbound ring's tail then (be_mvp_ring_taken())
 *
 * An absent @wait is left alone, and be_mvp_ack_wait_step() falls back.
 */
void be_mvp_ack_wait_start(struct be_mvp_ack_wait *wait, be_u64 now,
			   be_u64 taken);

/**
 * be_mvp_ack_wait_step - one step of a failed domain hart's wait for the ACK
 * @wait: the wait, which a step that sees hart 0's progress restarts
 * @now: the time CSR
 * @taken: the outbound ring's tail (be_mvp_ring_taken())
 * @published: the outbound ring's published head (be_mvp_ring_published())
 * @acknowledged: nonzero when hart 0's ACK is in the inbound ring
 *
 * Q10, as Plan revision M1-B revises it: the %BE_MVP_FAIL_ACK_TICKS window
 * measures hart 0's progress, not its latency behind a slow console. In
 * this order: an ACK parks the hart; a malformed tail, behind the one @wait
 * holds or beyond @published, falls back at once; a tail past the one
 * @wait holds is hart 0's progress, and restarts the window at @now with
 * that tail; a window of %BE_MVP_FAIL_ACK_TICKS ticks or more falls back;
 * anything else waits. The window is @now minus @wait's start modulo 2^64,
 * so one across the time CSR's wrap is measured as any other, and a @now
 * before the start reads as a window long past. The indices are compared
 * as 64-bit values: hart 0 resets them to 0, and a run posts far fewer
 * than 2^64 bytes. The waiting hart publishes nothing, so @published is
 * fixed and the tail can restart the window only until it reaches it: the
 * wait ends. A pure function: it reads only its arguments and writes only
 * @wait. A requester waiting for its MGMT_RESULT steps the same window,
 * with @acknowledged 0, and stops waiting itself once the answer is taken;
 * it publishes only the PONG of a PING it serves meanwhile.
 *
 * Return: %BE_MVP_ACK_PARK, %BE_MVP_ACK_WAIT, or %BE_MVP_ACK_FALLBACK,
 *         which an absent @wait also gets.
 */
enum be_mvp_ack_step be_mvp_ack_wait_step(struct be_mvp_ack_wait *wait,
					  be_u64 now, be_u64 taken,
					  be_u64 published, int acknowledged);

/**
 * be_mvp_line_reset - empty one monitor line
 * @line: the line
 */
void be_mvp_line_reset(struct be_mvp_line *line);

/**
 * be_mvp_line_text - append fixed text
 * @line: the line
 * @text: NUL-terminated text
 */
void be_mvp_line_text(struct be_mvp_line *line, const char *text);

/**
 * be_mvp_line_hex - append a lower-case 0x-prefixed hex value, no leading
 *                   zeros
 * @line: the line
 * @value: value to format
 */
void be_mvp_line_hex(struct be_mvp_line *line, be_u64 value);

/**
 * be_mvp_line_decimal - append an unsigned decimal value
 * @line: the line
 * @value: value to format
 */
void be_mvp_line_decimal(struct be_mvp_line *line, be_u64 value);

#endif
