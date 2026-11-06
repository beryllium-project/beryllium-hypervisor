/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B7 guest SBI core contract: exit classification (the SBI
 *          path, an idling wfi, and the HS slice), the per-guest exit
 *          ceiling and the run's guest-time budget, per-guest exit
 *          counters, the bounded B7 SBI subset (Base, TIME, DBCN, SRST)
 *          whose shutdown stops only the calling guest, the DBCN guest-range
 *          check against the calling guest's re-walked window, the
 *          per-guest line-buffered console, the per-guest vCPU record and
 *          CSR set a switch saves and restores, the guest-control checks,
 *          and the fixed-format monitor line builder.
 * Trust:   restricted-C mechanism only. It reads no CSR, issues no SBI call,
 *          performs no I/O, and dereferences no guest address: it returns an
 *          action, and the B7 runtime performs it.
 * Scope:   B7 only (planning/k3-b7-plan.md). It selects no SBI profile,
 *          hypercall ABI, stable guest ABI, Linux guest interface, or
 *          console protocol, and no guest request is ever forwarded to
 *          M-mode.
 */

#ifndef BE_B7_H
#define BE_B7_H

#include <be/r4.h>

#include "b7-gstage.h"
#include "b7-layout.h"

/* Extension and function identifiers, compared as exact 64-bit values. */
#define BE_B7_SBI_EID_BASE		BE_U64_C(0x10)
#define BE_B7_SBI_EID_TIME		BE_U64_C(0x54494d45)
#define BE_B7_SBI_EID_DBCN		BE_U64_C(0x4442434e)
#define BE_B7_SBI_EID_SRST		BE_U64_C(0x53525354)

#define BE_B7_SBI_BASE_GET_SPEC_VERSION	BE_U64_C(0)
#define BE_B7_SBI_BASE_GET_IMPL_ID	BE_U64_C(1)
#define BE_B7_SBI_BASE_GET_IMPL_VERSION	BE_U64_C(2)
#define BE_B7_SBI_BASE_PROBE_EXTENSION	BE_U64_C(3)
#define BE_B7_SBI_BASE_GET_MVENDORID	BE_U64_C(4)
#define BE_B7_SBI_BASE_GET_MARCHID	BE_U64_C(5)
#define BE_B7_SBI_BASE_GET_MIMPID	BE_U64_C(6)
#define BE_B7_SBI_TIME_SET_TIMER	BE_U64_C(0)
#define BE_B7_SBI_DBCN_WRITE		BE_U64_C(0)
#define BE_B7_SBI_DBCN_READ		BE_U64_C(1)
#define BE_B7_SBI_DBCN_WRITE_BYTE	BE_U64_C(2)
#define BE_B7_SBI_SRST_SYSTEM_RESET	BE_U64_C(0)

/*
 * Base values: SBI 2.0 and the provisional, unregistered B7 identity
 * BE_B7_SBI_IMPL_ID (0x4245) and BE_B7_SBI_IMPL_VERSION (3), b7-layout.h.
 */
#define BE_B7_SBI_SPEC_VERSION		BE_U64_C(0x2000000)

/* Standard SBI errors the subset returns. */
#define BE_B7_SBI_SUCCESS		0L
#define BE_B7_SBI_ERR_NOT_SUPPORTED	(-2L)
#define BE_B7_SBI_ERR_INVALID_PARAM	(-3L)
#define BE_B7_SBI_ERR_DENIED		(-4L)

/* SRST arguments: types 0-2 and reasons 0-1 are defined; others reserved. */
#define BE_B7_SRST_TYPE_SHUTDOWN	BE_U64_C(0)
#define BE_B7_SRST_TYPE_COLD_REBOOT	BE_U64_C(1)
#define BE_B7_SRST_TYPE_WARM_REBOOT	BE_U64_C(2)
#define BE_B7_SRST_REASON_NONE		BE_U64_C(0)
#define BE_B7_SRST_REASON_FAILURE	BE_U64_C(1)

/*
 * Run limits: each guest's exit ceiling and the run's guest-time budget
 * (b7-layout.h). The QEMU-only negative variants exit-budget and
 * guest-timeout lower one each with a compile-time switch; the state
 * carries the values the core uses.
 */
#if defined(BE_B7_VARIANT_EXIT_BUDGET)
#define BE_B7_RUN_EXIT_CEILING		BE_B7_VARIANT_EXIT_CEILING
#else
#define BE_B7_RUN_EXIT_CEILING		BE_B7_EXIT_CEILING
#endif
#if defined(BE_B7_VARIANT_GUEST_TIMEOUT)
#define BE_B7_RUN_GUEST_TIME_BUDGET	BE_B7_VARIANT_GUEST_TIME_BUDGET
#else
#define BE_B7_RUN_GUEST_TIME_BUDGET	BE_B7_GUEST_TIME_BUDGET
#endif

/* Exit handling. */
#define BE_B7_INSTRUCTION_SIZE		BE_U64_C(4)
#define BE_B7_SCAUSE_INTERRUPT		(BE_U64_C(1) << 63)
/* The HS slice: the supervisor timer, the only interrupt HS takes. */
#define BE_B7_SCAUSE_SUPERVISOR_TIMER	(BE_B7_SCAUSE_INTERRUPT | BE_U64_C(5))
#define BE_B7_SCAUSE_FETCH_ACCESS_FAULT	BE_U64_C(1)
#define BE_B7_SCAUSE_ILLEGAL_INSTRUCTION	BE_U64_C(2)
#define BE_B7_SCAUSE_LOAD_ACCESS_FAULT	BE_U64_C(5)
#define BE_B7_SCAUSE_STORE_ACCESS_FAULT	BE_U64_C(7)
#define BE_B7_SCAUSE_VS_ECALL		BE_U64_C(10)
#define BE_B7_SCAUSE_FETCH_GUEST_PAGE_FAULT	BE_U64_C(20)
#define BE_B7_SCAUSE_LOAD_GUEST_PAGE_FAULT	BE_U64_C(21)
#define BE_B7_SCAUSE_VIRTUAL_INSTRUCTION	BE_U64_C(22)
#define BE_B7_SCAUSE_STORE_GUEST_PAGE_FAULT	BE_U64_C(23)
/* The wfi encoding, which stval holds on its virtual-instruction trap. */
#define BE_B7_WFI_INSTRUCTION		BE_U64_C(0x10500073)
#define BE_B7_GPR_A2			BE_R4_GPR_INDEX(12U)

/*
 * Per-guest console: whole lines of at most 256 bytes, each with its
 * guest's prefix. One feed writes at most the buffered line and then one
 * line per input byte, each with its prefix and LF.
 */
#define BE_B7_DBCN_MAX_BYTES		256U
#define BE_B7_CONSOLE_LINE_BYTES	256U
#define BE_B7_G0_PREFIX			"BE_B7_G0: "
#define BE_B7_G1_PREFIX			"BE_B7_G1: "
#define BE_B7_GUEST_PREFIX_LENGTH	10U
#define BE_B7_CONSOLE_CAPACITY \
	((BE_B7_GUEST_PREFIX_LENGTH + 1U) * (BE_B7_DBCN_MAX_BYTES + 1U) + \
	 2U * BE_B7_CONSOLE_LINE_BYTES)
#define BE_B7_CONSOLE_INVALID		(~BE_U64_C(0))

/* One monitor line, built from fixed text and formatted values. */
#define BE_B7_LINE_CAPACITY		320U

/* Guest controls while a guest runs (planning/k3-b7-plan.md). */
#define BE_B7_HENVCFG_STCE		(BE_U64_C(1) << 63)
/* VTVM and VTSR stay clear; VTW is set, so a guest wfi traps. */
#define BE_B7_HSTATUS_CLEARED_TRAPS	(BE_R3_HSTATUS_VTVM | BE_R3_HSTATUS_VTSR)
#define BE_B7_HSTATUS_VTW		BE_R3_HSTATUS_VTW
#define BE_B7_HSTATUS_GUEST_CONTROLS \
	((BE_R3_HSTATUS_CONTROL_VALUE & ~BE_B7_HSTATUS_CLEARED_TRAPS) | \
	 BE_B7_HSTATUS_VTW)
/*
 * At a resume, SPVP is the guest's own mode at its exit (VS or VU), so it
 * is masked out, and the tail sets SPP from the saved SPVP.
 */
#define BE_B7_HSTATUS_RESUME_MASK \
	(BE_R3_HSTATUS_CONTROL_MASK & ~BE_R3_HSTATUS_SPVP)
#define BE_B7_HSTATUS_RESUME_CONTROLS \
	(BE_B7_HSTATUS_GUEST_CONTROLS & ~BE_R3_HSTATUS_SPVP)
/* Causes 0, 2, 3, 4, 6, 8, 12, 13, and 15 go to the guest, as in B6. */
#define BE_B7_HEDELEG			BE_U64_C(0xb15d)
/*
 * hedeleg is WARL, as in B6 (responsible-human direction fix-warl,
 * 2026-10-08): the readback may lack causes 0, 4, and 6; causes 2, 3, 8,
 * 12, 13, and 15 must stick, and no other bit may appear. The resume tail
 * then requires the armed readback.
 */
#define BE_B7_HEDELEG_REQUIRED		BE_U64_C(0xb10c)
#define BE_B7_HIDELEG_VSTI		(BE_U64_C(1) << 6)
#define BE_B7_HIE_VSTIE			(BE_U64_C(1) << 6)
/*
 * Only VSSIP, VSTIP, and VSEIP are tested in hvip: QEMU's hvip read also
 * shows a pending HS STIP as bit 5, which the specification makes zero.
 */
#define BE_B7_HVIP_VS_BITS		BE_U64_C(0x444)
#define BE_B7_HCOUNTEREN_TM		(BE_U64_C(1) << 1)
/* The HS slice: sie.STIE, with sstatus.SIE 0, so HS takes it only at V=1. */
#define BE_B7_SIE_STIE			(BE_U64_C(1) << 5)
#define BE_B7_VSTIMECMP_DISARMED	(~BE_U64_C(0))
#define BE_B7_HSTATUS_SPV		BE_R3_HSTATUS_SPV
#define BE_B7_HSTATUS_SPVP		BE_R3_HSTATUS_SPVP
#define BE_B7_SSTATUS_SPP		BE_R3_SSTATUS_SPP
#define BE_B7_SSTATUS_VS_MASK		(BE_U64_C(3) << 9)
/* The R3 sstatus control mask, plus VS, which the R3 mask omits. */
#define BE_B7_SSTATUS_CONTROL_MASK \
	(BE_R3_SSTATUS_CONTROL_MASK | BE_B7_SSTATUS_VS_MASK)
/* vsstatus.UXL = 2 (64-bit U-mode), as an RV64 hart reads it back. */
#define BE_B7_VSSTATUS_UXL64		(BE_U64_C(2) << 32)

/**
 * struct be_b7_controls - guest-control readback after arming
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
 * @sscratch: sscratch, the trusted-stack top the exit vector swaps in
 *
 * Only assembly reads these CSRs; C validates this monitor-owned copy.
 */
struct be_b7_controls {
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
 * struct be_b7_exit - one VS exit as the vector saved it
 * @frame: the accepted 320-byte struct be_r4_frame
 * @hstatus: hstatus at the exit (SPV, SPVP, GVA)
 * @htinst: htinst at the exit
 * @vsatp: the guest's vsatp at the exit
 * @time: the time CSR at the exit
 *
 * The vector writes it to the management saved page; every entry and
 * resume restores sepc and the GPRs from @frame, and sets SPP from the
 * SPVP bit of @hstatus.
 */
struct be_b7_exit {
	struct be_r4_frame frame;
	be_u64 hstatus;
	be_u64 htinst;
	be_u64 vsatp;
	be_u64 time;
};

/**
 * enum be_b7_vcsr - the per-guest CSR set, in the helpers' word order
 * @BE_B7_VCSR_VSSTATUS: vsstatus
 * @BE_B7_VCSR_VSIE: vsie (hie.VSTIE, with hideleg VSTI only)
 * @BE_B7_VCSR_VSTVEC: vstvec
 * @BE_B7_VCSR_VSSCRATCH: vsscratch
 * @BE_B7_VCSR_VSEPC: vsepc
 * @BE_B7_VCSR_VSCAUSE: vscause
 * @BE_B7_VCSR_VSTVAL: vstval
 * @BE_B7_VCSR_VSATP: vsatp
 * @BE_B7_VCSR_VSTIMECMP: vstimecmp, the guest's own Sstc timer
 * @BE_B7_VCSR_SCOUNTEREN: scounteren, which has no VS copy
 * @BE_B7_VCSR_SENVCFG: senvcfg, which has no VS copy
 * @BE_B7_VCSR_COUNT: number of CSRs, not a CSR
 */
enum be_b7_vcsr {
	BE_B7_VCSR_VSSTATUS = 0,
	BE_B7_VCSR_VSIE,
	BE_B7_VCSR_VSTVEC,
	BE_B7_VCSR_VSSCRATCH,
	BE_B7_VCSR_VSEPC,
	BE_B7_VCSR_VSCAUSE,
	BE_B7_VCSR_VSTVAL,
	BE_B7_VCSR_VSATP,
	BE_B7_VCSR_VSTIMECMP,
	BE_B7_VCSR_SCOUNTEREN,
	BE_B7_VCSR_SENVCFG,
	BE_B7_VCSR_COUNT,
};

/**
 * struct be_b7_vcpu - one guest's state while the other guest runs
 * @record: a copy of the guest's last exit record, or its first-entry
 *          record before it ever ran
 * @csr: the guest's CSR set, in &enum be_b7_vcsr order
 */
struct be_b7_vcpu {
	struct be_b7_exit record;
	be_u64 csr[BE_B7_VCSR_COUNT];
};

/**
 * enum be_b7_class - stable B7 terminal classes, printed as BE_B7:FAIL <name>
 * @BE_B7_CLASS_NONE: no failure
 * @BE_B7_CLASS_BOOT: boot contract, R1, R2, R3 check, binding, or install
 * @BE_B7_CLASS_GSTAGE: a B7 root was refused, the two roots are not
 *                      disjoint, or an install read back another value
 * @BE_B7_CLASS_SSTC: henvcfg.STCE reads back 0
 * @BE_B7_CLASS_CONTROLS: a guest control did not read back as written
 * @BE_B7_CLASS_PAYLOAD: the staged payload's layout or shape was refused
 * @BE_B7_CLASS_INTERRUPT: an interrupt other than the HS timer reached HS
 * @BE_B7_CLASS_GUEST_PAGE_FAULT: fetch, load, or store guest-page fault
 * @BE_B7_CLASS_VIRTUAL_INSTRUCTION: virtual-instruction exception other
 *                                   than a VS-mode wfi
 * @BE_B7_CLASS_ACCESS_FAULT: fetch, load, or store access fault
 * @BE_B7_CLASS_ILLEGAL_INSTRUCTION: illegal-instruction exception
 * @BE_B7_CLASS_EXCEPTION: any other exit, or one the core cannot accept
 * @BE_B7_CLASS_EXIT_BUDGET: a guest took more exits than its ceiling
 * @BE_B7_CLASS_GUEST_TIMEOUT: an exit or a decision after the run's budget
 * @BE_B7_CLASS_RESUME: a resume check failed
 * @BE_B7_CLASS_CONSOLE: a firmware console write failed
 * @BE_B7_CLASS_GUEST_FAILURE: a guest requested shutdown with reason 1
 * @BE_B7_CLASS_GUEST_REBOOT: a guest requested a cold or warm reboot
 * @BE_B7_CLASS_SHUTDOWN_RETURNED: the monitor's SRST shutdown returned
 * @BE_B7_CLASS_SWITCH: a switch's hgatp or per-guest CSR readback differed
 * @BE_B7_CLASS_SCHEDULER: the scheduler refused an event or a decision
 * @BE_B7_CLASS_COUNT: number of classes, not a class
 */
enum be_b7_class {
	BE_B7_CLASS_NONE = 0,
	BE_B7_CLASS_BOOT,
	BE_B7_CLASS_GSTAGE,
	BE_B7_CLASS_SSTC,
	BE_B7_CLASS_CONTROLS,
	BE_B7_CLASS_PAYLOAD,
	BE_B7_CLASS_INTERRUPT,
	BE_B7_CLASS_GUEST_PAGE_FAULT,
	BE_B7_CLASS_VIRTUAL_INSTRUCTION,
	BE_B7_CLASS_ACCESS_FAULT,
	BE_B7_CLASS_ILLEGAL_INSTRUCTION,
	BE_B7_CLASS_EXCEPTION,
	BE_B7_CLASS_EXIT_BUDGET,
	BE_B7_CLASS_GUEST_TIMEOUT,
	BE_B7_CLASS_RESUME,
	BE_B7_CLASS_CONSOLE,
	BE_B7_CLASS_GUEST_FAILURE,
	BE_B7_CLASS_GUEST_REBOOT,
	BE_B7_CLASS_SHUTDOWN_RETURNED,
	BE_B7_CLASS_SWITCH,
	BE_B7_CLASS_SCHEDULER,
	BE_B7_CLASS_COUNT,
};

/**
 * enum be_b7_phase - one-way phase of the run or of one guest
 * @BE_B7_PHASE_RUNNING: exits are accepted
 * @BE_B7_PHASE_STOPPED: (guest) the guest requested shutdown with reason 0
 * @BE_B7_PHASE_FAILED: (run) terminal failure; the class is sticky
 */
enum be_b7_phase {
	BE_B7_PHASE_RUNNING = 0,
	BE_B7_PHASE_STOPPED,
	BE_B7_PHASE_FAILED,
};

/**
 * enum be_b7_action - what the runtime must do for one exit
 * @BE_B7_ACTION_NONE: no decision
 * @BE_B7_ACTION_RETURN: return the error and value to the guest
 * @BE_B7_ACTION_CONSOLE_WRITE: copy the bytes at the HS physical source
 *                              through the guest's console, then return
 * @BE_B7_ACTION_CONSOLE_BYTE: feed one byte to the guest's console, then
 *                             return
 * @BE_B7_ACTION_SET_TIMER: write the timer value to vstimecmp, then return
 * @BE_B7_ACTION_WFI: the guest idles: step past its wfi, then schedule
 * @BE_B7_ACTION_SLICE: the HS timer fired: schedule
 * @BE_B7_ACTION_STOP: guest shutdown, reason 0: report, stop the guest,
 *                     and schedule
 * @BE_B7_ACTION_GUEST_FAILURE: guest shutdown, reason 1: fail and shut down
 * @BE_B7_ACTION_GUEST_REBOOT: guest reboot request: fail and shut down
 * @BE_B7_ACTION_TERMINAL: fail closed with the result's class
 */
enum be_b7_action {
	BE_B7_ACTION_NONE = 0,
	BE_B7_ACTION_RETURN,
	BE_B7_ACTION_CONSOLE_WRITE,
	BE_B7_ACTION_CONSOLE_BYTE,
	BE_B7_ACTION_SET_TIMER,
	BE_B7_ACTION_WFI,
	BE_B7_ACTION_SLICE,
	BE_B7_ACTION_STOP,
	BE_B7_ACTION_GUEST_FAILURE,
	BE_B7_ACTION_GUEST_REBOOT,
	BE_B7_ACTION_TERMINAL,
};

/**
 * struct be_b7_counts - one guest's exits, by kind and SBI call class
 * @exits: every exit, counted against the guest's ceiling
 * @base: Base calls answered with success
 * @time: TIME set_timer calls
 * @dbcn_write: DBCN write calls answered with success
 * @dbcn_read: DBCN read calls (each refused with SBI_ERR_DENIED)
 * @dbcn_byte: DBCN write-byte calls
 * @srst: SRST calls that stopped the guest or ended the run
 * @refused: calls answered with SBI_ERR_NOT_SUPPORTED or _INVALID_PARAM
 * @wfi: idling wfi exits
 * @slice: HS timer exits
 *
 * Every accepted exit adds one to exactly one of the call classes, @wfi,
 * and @slice, so in a run that ends without failure @exits is their sum.
 */
struct be_b7_counts {
	be_u64 exits;
	be_u64 base;
	be_u64 time;
	be_u64 dbcn_write;
	be_u64 dbcn_read;
	be_u64 dbcn_byte;
	be_u64 srst;
	be_u64 refused;
	be_u64 wfi;
	be_u64 slice;
};

/**
 * struct be_b7_guest - one guest's SBI-core state
 * @phase: RUNNING, or STOPPED after its shutdown
 * @counts: its exits and calls by class
 */
struct be_b7_guest {
	enum be_b7_phase phase;
	struct be_b7_counts counts;
};

/**
 * struct be_b7_state - run state
 * @exit_ceiling: most exits each guest may take
 * @time_budget: ticks after @entry_time from which an exit is terminal
 * @entry_time: the time CSR just before G0's first entry
 * @phase: RUNNING, or FAILED
 * @failure: sticky terminal class once @phase is FAILED
 * @guest: each guest's state
 */
struct be_b7_state {
	be_u64 exit_ceiling;
	be_u64 time_budget;
	be_u64 entry_time;
	enum be_b7_phase phase;
	enum be_b7_class failure;
	struct be_b7_guest guest[BE_B7_GUESTS];
};

#define BE_B7_STATE_INITIALIZER(ceiling, budget) { \
	.exit_ceiling = (ceiling), \
	.time_budget = (budget), \
	.phase = BE_B7_PHASE_RUNNING, \
	.failure = BE_B7_CLASS_NONE, \
}

/**
 * struct be_b7_result - the decision for one exit
 * @action: what the runtime must do
 * @failure: terminal class for %BE_B7_ACTION_TERMINAL
 * @error: SBI error the guest receives in a0
 * @value: SBI value the guest receives in a1
 * @source_pa: HS physical address of the first DBCN byte
 * @length: DBCN bytes to copy, at most %BE_B7_DBCN_MAX_BYTES
 * @timer: vstimecmp value for %BE_B7_ACTION_SET_TIMER
 * @resume_pc: guest PC after the ecall or the wfi
 * @byte: the DBCN write-byte argument
 */
struct be_b7_result {
	enum be_b7_action action;
	enum be_b7_class failure;
	long error;
	be_u64 value;
	be_u64 source_pa;
	be_u64 length;
	be_u64 timer;
	be_u64 resume_pc;
	be_u8 byte;
};

/**
 * struct be_b7_console - one guest's console line buffer
 * @length: bytes buffered, at most %BE_B7_CONSOLE_LINE_BYTES
 * @text: the buffered, already filtered bytes of the current line
 */
struct be_b7_console {
	be_u64 length;
	char text[BE_B7_CONSOLE_LINE_BYTES];
};

/**
 * struct be_b7_line - one bounded monitor line
 * @text: line bytes, not NUL-terminated
 * @length: bytes used
 * @overflow: nonzero once any append did not fit; the line is then unusable
 */
struct be_b7_line {
	char text[BE_B7_LINE_CAPACITY];
	be_u64 length;
	be_u32 overflow;
};

/**
 * be_b7_stce_class - classify the henvcfg readback after writing STCE only
 * @henvcfg: henvcfg readback
 *
 * Return: NONE when it reads back exactly STCE, SSTC when STCE reads 0
 *         (no Sstc, or M-mode left menvcfg.STCE clear), otherwise CONTROLS.
 */
enum be_b7_class be_b7_stce_class(be_u64 henvcfg);

/**
 * be_b7_controls_valid - check the guest controls before the first entry
 * @controls: readback after arming
 * @expected_hgatp: the installed hgatp, G0's
 * @trusted_top: the management trusted-stack top
 *
 * Return: 1 when every control holds its guest-run value: hip 0 after the
 *         timer was disarmed; hstatus controls 0x200180 (VTW, SPV, SPVP);
 *         hedeleg within 0xb15d and holding 0xb10c (WARL); hideleg VSTI
 *         only; hie, htimedelta, and hgeie 0; hvip's VS bits 0; hcounteren
 *         TM only; henvcfg STCE only; vstimecmp ~0; sie STIE only; sstatus
 *         SIE, SPIE, SPP, FS, VS, XS, SUM, and MXR 0; @expected_hgatp; Bare
 *         vsatp; and sscratch the trusted top. Otherwise 0.
 */
int be_b7_controls_valid(const struct be_b7_controls *controls,
			 be_u64 expected_hgatp, be_u64 trusted_top);

/**
 * be_b7_class_name - stable class name printed after BE_B7:FAIL
 * @failure: class to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_b7_class_name(enum be_b7_class failure);

/**
 * be_b7_classify_cause - classify an exit that is neither the HS slice nor
 *                        an idling VS-mode wfi
 * @scause: HS scause captured on the exit
 *
 * Return: %BE_B7_CLASS_NONE for a VS ecall (cause 10), the SBI path;
 *         otherwise the terminal class of the exit.
 */
enum be_b7_class be_b7_classify_cause(be_u64 scause);

/**
 * be_b7_handle_exit - count and classify one exit, and decide it
 * @state: run state
 * @guest: the guest that exited, 0 or 1
 * @map: that guest's walked window
 * @record: the monitor-owned exit record the vector saved
 * @result: the decision
 *
 * Counts the exit against the guest's ceiling and the run's time budget,
 * then decides. The supervisor timer is the slice; a virtual-instruction
 * exit from VS mode whose stval is the wfi encoding is an idling wfi; a VS
 * ecall is an SBI call. Every other exit, and every exit after the run
 * failed or of a stopped guest, is terminal. A terminal decision moves the
 * run to FAILED; a guest shutdown with reason 0 moves only the guest to
 * STOPPED.
 *
 * Return: the decided action.
 */
enum be_b7_action be_b7_handle_exit(struct be_b7_state *state, be_u32 guest,
				    const struct be_b7_gstage_map *map,
				    const struct be_b7_exit *record,
				    struct be_b7_result *result);

/**
 * be_b7_counts_sbi - one guest's SBI calls of every class
 * @counts: the guest's counts
 *
 * Return: base + time + dbcn_write + dbcn_read + dbcn_byte + srst + refused.
 */
be_u64 be_b7_counts_sbi(const struct be_b7_counts *counts);

/**
 * be_b7_apply_return - write one decision into the saved frame
 * @frame: the monitor-owned frame
 * @result: a non-terminal decision
 *
 * An SBI decision writes a0, a1, and sepc (the resume PC); an idling wfi
 * writes only sepc, past the wfi; every other action changes nothing.
 */
void be_b7_apply_return(struct be_r4_frame *frame,
			const struct be_b7_result *result);

/**
 * be_b7_entry_frame - fill a first-entry exit record
 * @record: the record
 * @pc: the first guest PC (sepc)
 * @hart: the guest's a0
 * @dtb: the guest's a1
 *
 * hstatus becomes SPV and SPVP, so the entry is into VS mode; every other
 * field, including every other GPR, becomes 0.
 */
void be_b7_entry_frame(struct be_b7_exit *record, be_u64 pc, be_u64 hart,
		       be_u64 dtb);

/**
 * be_b7_record_spp - the sstatus.SPP an entry or resume must carry
 * @record: an exit or first-entry record
 *
 * Return: SPP (0x100) when the record's SPVP is set (VS mode), else 0 (VU
 *         mode). The resume tail applies the same rule.
 */
be_u64 be_b7_record_spp(const struct be_b7_exit *record);

/**
 * be_b7_vcsr_initial - fill a guest's initial CSR set
 * @csr: %BE_B7_VCSR_COUNT words
 *
 * Every CSR is 0, but vsstatus holds UXL = 2 (RV64) and vstimecmp is ~0.
 */
void be_b7_vcsr_initial(be_u64 *csr);

/**
 * be_b7_vcpu_init - a guest's state before its first entry
 * @vcpu: the guest's vCPU state
 * @pc: the first guest PC
 * @hart: the guest's a0
 * @dtb: the guest's a1
 *
 * The record is be_b7_entry_frame()'s, and the CSR set is the initial set.
 */
void be_b7_vcpu_init(struct be_b7_vcpu *vcpu, be_u64 pc, be_u64 hart,
		     be_u64 dtb);

/**
 * be_b7_vcpu_save - copy the exit record into the guest's vCPU state
 * @vcpu: the outgoing guest's vCPU state
 * @record: the exit record, unchanged
 */
void be_b7_vcpu_save(struct be_b7_vcpu *vcpu, const struct be_b7_exit *record);

/**
 * be_b7_vcpu_restore - copy the guest's saved record into the exit record
 * @vcpu: the incoming guest's vCPU state, unchanged
 * @record: the exit record the resume tail enters from
 */
void be_b7_vcpu_restore(const struct be_b7_vcpu *vcpu,
			struct be_b7_exit *record);

/**
 * be_b7_vcsr_mismatch - compare a loaded CSR set's readback
 * @expected: the values the load helper wrote
 * @readback: the values it read back
 *
 * Return: the first index whose readback differs, or %BE_B7_VCSR_COUNT
 *         when every word matches; 0 when either pointer is absent.
 */
be_u32 be_b7_vcsr_mismatch(const be_u64 *expected, const be_u64 *readback);

/**
 * be_b7_vcsr_name - the CSR name a switch DETAIL line prints
 * @index: an &enum be_b7_vcsr index
 *
 * Return: constant name, or "invalid".
 */
const char *be_b7_vcsr_name(be_u32 index);

/**
 * be_b7_fail - enter the sticky terminal state
 * @state: run state, if available
 * @failure: class to retain; NONE is recorded as EXCEPTION
 *
 * Return: the retained class (the first one, if already FAILED).
 */
enum be_b7_class be_b7_fail(struct be_b7_state *state,
			    enum be_b7_class failure);

/**
 * be_b7_guest_prefix - a guest's console prefix
 * @guest: 0 or 1
 *
 * Return: "BE_B7_G0: " or "BE_B7_G1: ", or 0 for another guest.
 */
const char *be_b7_guest_prefix(be_u32 guest);

/**
 * be_b7_console_feed - buffer one guest's bytes and emit whole lines
 * @console: the guest's console
 * @guest: 0 or 1, which selects the prefix
 * @input: guest bytes, already copied into monitor memory
 * @length: at most %BE_B7_DBCN_MAX_BYTES
 * @output: monitor buffer
 * @capacity: at least %BE_B7_CONSOLE_CAPACITY
 *
 * CR is dropped and every other byte outside 0x20-0x7e but LF becomes '?'.
 * Each LF ends the buffered line, and a byte that finds the buffer full
 * first ends the full line; each ended line goes to @output as the prefix,
 * the line, and LF. Bytes after the last ended line stay buffered.
 *
 * Return: bytes written to @output (0 when no line ended), or
 *         %BE_B7_CONSOLE_INVALID (state unchanged).
 */
be_u64 be_b7_console_feed(struct be_b7_console *console, be_u32 guest,
			  const be_u8 *input, be_u64 length, char *output,
			  be_u64 capacity);

/**
 * be_b7_console_flush - end a guest's partial line
 * @console: the guest's console
 * @guest: 0 or 1, which selects the prefix
 * @output: monitor buffer
 * @capacity: at least %BE_B7_CONSOLE_CAPACITY
 *
 * Return: bytes written to @output: 0 when nothing was buffered, else the
 *         prefix, the partial line, and LF; or %BE_B7_CONSOLE_INVALID.
 */
be_u64 be_b7_console_flush(struct be_b7_console *console, be_u32 guest,
			   char *output, be_u64 capacity);

/**
 * be_b7_line_reset - empty one monitor line
 * @line: the line
 */
void be_b7_line_reset(struct be_b7_line *line);

/**
 * be_b7_line_text - append fixed text
 * @line: the line
 * @text: NUL-terminated text
 */
void be_b7_line_text(struct be_b7_line *line, const char *text);

/**
 * be_b7_line_hex - append a lower-case 0x-prefixed hex value, no leading zeros
 * @line: the line
 * @value: value to format
 */
void be_b7_line_hex(struct be_b7_line *line, be_u64 value);

/**
 * be_b7_line_decimal - append an unsigned decimal value
 * @line: the line
 * @value: value to format
 */
void be_b7_line_decimal(struct be_b7_line *line, be_u64 value);

#endif
