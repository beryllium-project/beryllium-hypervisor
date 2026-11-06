/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B6 guest SBI core contract: exit classification, the exit
 *          ceiling and the guest-time budget, per-class exit counters, the
 *          bounded B6 SBI subset (Base, TIME, DBCN, SRST), the DBCN guest-
 *          range check against the re-walked B6 window, the tagged guest
 *          console, the first-entry frame, the guest-control checks, and the
 *          fixed-format monitor line builder.
 * Trust:   restricted-C mechanism only. It reads no CSR, issues no SBI call,
 *          performs no I/O, and dereferences no guest address: it returns an
 *          action, and the B6 runtime performs it.
 * Scope:   B6 only (planning/k3-b6-plan.md). It selects no SBI profile,
 *          hypercall ABI, stable guest ABI, or Linux guest interface, and no
 *          guest request is ever forwarded to M-mode.
 */

#ifndef BE_B6_H
#define BE_B6_H

#include <be/r4.h>

#include "b6-gstage.h"
#include "b6-layout.h"

/* Extension and function identifiers, compared as exact 64-bit values. */
#define BE_B6_SBI_EID_BASE		BE_U64_C(0x10)
#define BE_B6_SBI_EID_TIME		BE_U64_C(0x54494d45)
#define BE_B6_SBI_EID_DBCN		BE_U64_C(0x4442434e)
#define BE_B6_SBI_EID_SRST		BE_U64_C(0x53525354)

#define BE_B6_SBI_BASE_GET_SPEC_VERSION	BE_U64_C(0)
#define BE_B6_SBI_BASE_GET_IMPL_ID	BE_U64_C(1)
#define BE_B6_SBI_BASE_GET_IMPL_VERSION	BE_U64_C(2)
#define BE_B6_SBI_BASE_PROBE_EXTENSION	BE_U64_C(3)
#define BE_B6_SBI_BASE_GET_MVENDORID	BE_U64_C(4)
#define BE_B6_SBI_BASE_GET_MARCHID	BE_U64_C(5)
#define BE_B6_SBI_BASE_GET_MIMPID	BE_U64_C(6)
#define BE_B6_SBI_TIME_SET_TIMER	BE_U64_C(0)
#define BE_B6_SBI_DBCN_WRITE		BE_U64_C(0)
#define BE_B6_SBI_DBCN_READ		BE_U64_C(1)
#define BE_B6_SBI_DBCN_WRITE_BYTE	BE_U64_C(2)
#define BE_B6_SBI_SRST_SYSTEM_RESET	BE_U64_C(0)

/*
 * Base values: SBI 2.0 and the provisional, unregistered B6 identity
 * BE_B6_SBI_IMPL_ID (0x4245) and BE_B6_SBI_IMPL_VERSION (2), b6-layout.h.
 */
#define BE_B6_SBI_SPEC_VERSION		BE_U64_C(0x2000000)

/* Standard SBI errors the subset returns. */
#define BE_B6_SBI_SUCCESS		0L
#define BE_B6_SBI_ERR_NOT_SUPPORTED	(-2L)
#define BE_B6_SBI_ERR_INVALID_PARAM	(-3L)
#define BE_B6_SBI_ERR_DENIED		(-4L)

/* SRST arguments: types 0-2 and reasons 0-1 are defined; others reserved. */
#define BE_B6_SRST_TYPE_SHUTDOWN	BE_U64_C(0)
#define BE_B6_SRST_TYPE_COLD_REBOOT	BE_U64_C(1)
#define BE_B6_SRST_TYPE_WARM_REBOOT	BE_U64_C(2)
#define BE_B6_SRST_REASON_NONE		BE_U64_C(0)
#define BE_B6_SRST_REASON_FAILURE	BE_U64_C(1)

/*
 * Run limits: the exit ceiling and the guest-time budget (b6-layout.h). The
 * QEMU-only negative variants exit-budget and guest-timeout lower one each
 * with a compile-time switch; the state carries the values the core uses.
 */
#if defined(BE_B6_VARIANT_EXIT_BUDGET)
#define BE_B6_RUN_EXIT_CEILING		BE_B6_VARIANT_EXIT_CEILING
#else
#define BE_B6_RUN_EXIT_CEILING		BE_B6_EXIT_CEILING
#endif
#if defined(BE_B6_VARIANT_GUEST_TIMEOUT)
#define BE_B6_RUN_GUEST_TIME_BUDGET	BE_B6_VARIANT_GUEST_TIME_BUDGET
#else
#define BE_B6_RUN_GUEST_TIME_BUDGET	BE_B6_GUEST_TIME_BUDGET
#endif

/* Exit handling. */
#define BE_B6_INSTRUCTION_SIZE		BE_U64_C(4)
#define BE_B6_SCAUSE_INTERRUPT		(BE_U64_C(1) << 63)
#define BE_B6_SCAUSE_FETCH_ACCESS_FAULT	BE_U64_C(1)
#define BE_B6_SCAUSE_ILLEGAL_INSTRUCTION	BE_U64_C(2)
#define BE_B6_SCAUSE_LOAD_ACCESS_FAULT	BE_U64_C(5)
#define BE_B6_SCAUSE_STORE_ACCESS_FAULT	BE_U64_C(7)
#define BE_B6_SCAUSE_VS_ECALL		BE_U64_C(10)
#define BE_B6_SCAUSE_FETCH_GUEST_PAGE_FAULT	BE_U64_C(20)
#define BE_B6_SCAUSE_LOAD_GUEST_PAGE_FAULT	BE_U64_C(21)
#define BE_B6_SCAUSE_VIRTUAL_INSTRUCTION	BE_U64_C(22)
#define BE_B6_SCAUSE_STORE_GUEST_PAGE_FAULT	BE_U64_C(23)
#define BE_B6_GPR_A2			BE_R4_GPR_INDEX(12U)

/* Tagged console: at most 256 guest bytes per call, each line prefixed. */
#define BE_B6_DBCN_MAX_BYTES		256U
#define BE_B6_GUEST_PREFIX		"BE_B6_GUEST: "
#define BE_B6_GUEST_PREFIX_LENGTH	13U
#define BE_B6_TAGGED_CAPACITY \
	((BE_B6_GUEST_PREFIX_LENGTH + 1U) * BE_B6_DBCN_MAX_BYTES)
#define BE_B6_TAG_INVALID		(~BE_U64_C(0))

/* One monitor line, built from fixed text and formatted values. */
#define BE_B6_LINE_CAPACITY		320U

/* Guest controls while the guest runs (planning/k3-b6-plan.md). */
#define BE_B6_HENVCFG_STCE		(BE_U64_C(1) << 63)
#define BE_B6_HSTATUS_VIRTUAL_TRAPS \
	(BE_R3_HSTATUS_VTVM | BE_R3_HSTATUS_VTW | BE_R3_HSTATUS_VTSR)
#define BE_B6_HSTATUS_GUEST_CONTROLS \
	(BE_R3_HSTATUS_CONTROL_VALUE & ~BE_B6_HSTATUS_VIRTUAL_TRAPS)
/* Causes 0, 2, 3, 4, 6, 8, 12, 13, and 15 go to the guest (Q5). */
#define BE_B6_HEDELEG			BE_U64_C(0xb15d)
/*
 * hedeleg is WARL (responsible-human direction fix-warl, 2026-10-08): B6
 * writes BE_B6_HEDELEG, and the readback may lack causes 0, 4, and 6. Bit
 * 0 may be read-only zero when IALIGN=16, and K3 performs misaligned
 * accesses in hardware. Causes 2, 3, 8, 12, 13, and 15 must stick, and no
 * other bit may appear. The resume tail then requires the armed readback.
 */
#define BE_B6_HEDELEG_REQUIRED		BE_U64_C(0xb10c)
#define BE_B6_HIDELEG_VSTI		(BE_U64_C(1) << 6)
#define BE_B6_HIE_VSTIE			(BE_U64_C(1) << 6)
#define BE_B6_HCOUNTEREN_TM		(BE_U64_C(1) << 1)
#define BE_B6_VSTIMECMP_DISARMED	(~BE_U64_C(0))
#define BE_B6_HSTATUS_SPV		BE_R3_HSTATUS_SPV
#define BE_B6_HSTATUS_SPVP		BE_R3_HSTATUS_SPVP
#define BE_B6_SSTATUS_VS_MASK		(BE_U64_C(3) << 9)
/* The R3 sstatus control mask, plus VS, which the R3 mask omits. */
#define BE_B6_SSTATUS_CONTROL_MASK \
	(BE_R3_SSTATUS_CONTROL_MASK | BE_B6_SSTATUS_VS_MASK)

/**
 * struct be_b6_controls - guest-control readback after arming
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
struct be_b6_controls {
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
 * struct be_b6_exit - one VS exit as the vector saved it
 * @frame: the accepted 320-byte struct be_r4_frame
 * @hstatus: hstatus at the exit (SPV, SPVP, GVA)
 * @htinst: htinst at the exit
 * @vsatp: the guest's vsatp at the exit
 * @time: the time CSR at the exit
 *
 * The vector writes it to the management saved page; the first entry and
 * every resume restore sepc and the GPRs from @frame.
 */
struct be_b6_exit {
	struct be_r4_frame frame;
	be_u64 hstatus;
	be_u64 htinst;
	be_u64 vsatp;
	be_u64 time;
};

/**
 * enum be_b6_class - stable B6 terminal classes, printed as BE_B6:FAIL <name>
 * @BE_B6_CLASS_NONE: no failure
 * @BE_B6_CLASS_BOOT: boot contract, R1, R2, R3 check, binding, or install
 * @BE_B6_CLASS_GSTAGE: the B6 root was refused, or its install read back
 *                      another value
 * @BE_B6_CLASS_SSTC: henvcfg.STCE reads back 0
 * @BE_B6_CLASS_CONTROLS: a guest control did not read back as written
 * @BE_B6_CLASS_PAYLOAD: the staged payload's layout or shape was refused
 * @BE_B6_CLASS_INTERRUPT: an interrupt reached HS
 * @BE_B6_CLASS_GUEST_PAGE_FAULT: fetch, load, or store guest-page fault
 * @BE_B6_CLASS_VIRTUAL_INSTRUCTION: virtual-instruction exception
 * @BE_B6_CLASS_ACCESS_FAULT: fetch, load, or store access fault
 * @BE_B6_CLASS_ILLEGAL_INSTRUCTION: illegal-instruction exception
 * @BE_B6_CLASS_EXCEPTION: any other exit, or one the core cannot accept
 * @BE_B6_CLASS_EXIT_BUDGET: more exits than the ceiling
 * @BE_B6_CLASS_GUEST_TIMEOUT: an exit after the guest-time budget
 * @BE_B6_CLASS_RESUME: a resume check failed
 * @BE_B6_CLASS_CONSOLE: a firmware console write failed
 * @BE_B6_CLASS_GUEST_FAILURE: the guest requested shutdown with reason 1
 * @BE_B6_CLASS_GUEST_REBOOT: the guest requested a cold or warm reboot
 * @BE_B6_CLASS_SHUTDOWN_RETURNED: the monitor's SRST shutdown returned
 * @BE_B6_CLASS_COUNT: number of classes, not a class
 */
enum be_b6_class {
	BE_B6_CLASS_NONE = 0,
	BE_B6_CLASS_BOOT,
	BE_B6_CLASS_GSTAGE,
	BE_B6_CLASS_SSTC,
	BE_B6_CLASS_CONTROLS,
	BE_B6_CLASS_PAYLOAD,
	BE_B6_CLASS_INTERRUPT,
	BE_B6_CLASS_GUEST_PAGE_FAULT,
	BE_B6_CLASS_VIRTUAL_INSTRUCTION,
	BE_B6_CLASS_ACCESS_FAULT,
	BE_B6_CLASS_ILLEGAL_INSTRUCTION,
	BE_B6_CLASS_EXCEPTION,
	BE_B6_CLASS_EXIT_BUDGET,
	BE_B6_CLASS_GUEST_TIMEOUT,
	BE_B6_CLASS_RESUME,
	BE_B6_CLASS_CONSOLE,
	BE_B6_CLASS_GUEST_FAILURE,
	BE_B6_CLASS_GUEST_REBOOT,
	BE_B6_CLASS_SHUTDOWN_RETURNED,
	BE_B6_CLASS_COUNT,
};

/**
 * enum be_b6_phase - one-way guest-run phase
 * @BE_B6_PHASE_RUNNING: exits are accepted
 * @BE_B6_PHASE_SHUTDOWN: the guest requested shutdown with reason 0
 * @BE_B6_PHASE_FAILED: terminal failure; the class is sticky
 */
enum be_b6_phase {
	BE_B6_PHASE_RUNNING = 0,
	BE_B6_PHASE_SHUTDOWN,
	BE_B6_PHASE_FAILED,
};

/**
 * enum be_b6_action - what the runtime must do for one exit
 * @BE_B6_ACTION_NONE: no decision
 * @BE_B6_ACTION_RETURN: return the error and value to the guest
 * @BE_B6_ACTION_CONSOLE_WRITE: copy the bytes at the HS physical source
 *                              through the tagged console, then return
 * @BE_B6_ACTION_CONSOLE_BYTE: write one byte through the tagged console,
 *                             then return
 * @BE_B6_ACTION_SET_TIMER: write the timer value to vstimecmp, then return
 * @BE_B6_ACTION_SHUTDOWN: guest shutdown, reason 0: report and shut down
 * @BE_B6_ACTION_GUEST_FAILURE: guest shutdown, reason 1: fail and shut down
 * @BE_B6_ACTION_GUEST_REBOOT: guest reboot request: fail and shut down
 * @BE_B6_ACTION_TERMINAL: fail closed with the result's class
 */
enum be_b6_action {
	BE_B6_ACTION_NONE = 0,
	BE_B6_ACTION_RETURN,
	BE_B6_ACTION_CONSOLE_WRITE,
	BE_B6_ACTION_CONSOLE_BYTE,
	BE_B6_ACTION_SET_TIMER,
	BE_B6_ACTION_SHUTDOWN,
	BE_B6_ACTION_GUEST_FAILURE,
	BE_B6_ACTION_GUEST_REBOOT,
	BE_B6_ACTION_TERMINAL,
};

/**
 * struct be_b6_counts - exits taken, and SBI calls by class
 * @exits: every exit, counted against the ceiling
 * @base: Base calls answered with success
 * @time: TIME set_timer calls
 * @dbcn_write: DBCN write calls answered with success
 * @dbcn_read: DBCN read calls (each refused with SBI_ERR_DENIED)
 * @dbcn_byte: DBCN write-byte calls
 * @srst: SRST calls that ended the run (shutdown or reboot request)
 * @refused: calls answered with SBI_ERR_NOT_SUPPORTED or _INVALID_PARAM
 *
 * Every accepted VS ecall adds one to exactly one call class, so in a run
 * whose every exit is an ecall, @exits is the sum of the call classes.
 */
struct be_b6_counts {
	be_u64 exits;
	be_u64 base;
	be_u64 time;
	be_u64 dbcn_write;
	be_u64 dbcn_read;
	be_u64 dbcn_byte;
	be_u64 srst;
	be_u64 refused;
};

/**
 * struct be_b6_state - guest-run state
 * @phase: one-way phase
 * @failure: sticky terminal class once @phase is FAILED
 * @counts: exits and calls by class
 * @exit_ceiling: most exits the run may take
 * @time_budget: ticks after @entry_time from which an exit is terminal
 * @entry_time: the time CSR just before the first entry
 */
struct be_b6_state {
	enum be_b6_phase phase;
	enum be_b6_class failure;
	struct be_b6_counts counts;
	be_u64 exit_ceiling;
	be_u64 time_budget;
	be_u64 entry_time;
};

#define BE_B6_STATE_INITIALIZER(ceiling, budget) { \
	.phase = BE_B6_PHASE_RUNNING, \
	.failure = BE_B6_CLASS_NONE, \
	.exit_ceiling = (ceiling), \
	.time_budget = (budget), \
}

/**
 * struct be_b6_result - the decision for one exit
 * @action: what the runtime must do
 * @failure: terminal class for %BE_B6_ACTION_TERMINAL
 * @error: SBI error the guest receives in a0
 * @value: SBI value the guest receives in a1
 * @source_pa: HS physical address of the first DBCN byte
 * @length: DBCN bytes to copy, at most %BE_B6_DBCN_MAX_BYTES
 * @timer: vstimecmp value for %BE_B6_ACTION_SET_TIMER
 * @resume_pc: guest PC after the ecall
 * @byte: the DBCN write-byte argument
 */
struct be_b6_result {
	enum be_b6_action action;
	enum be_b6_class failure;
	long error;
	be_u64 value;
	be_u64 source_pa;
	be_u64 length;
	be_u64 timer;
	be_u64 resume_pc;
	be_u8 byte;
};

/**
 * struct be_b6_console - tagged guest console state
 * @line_open: nonzero while a guest line has its prefix but no newline yet
 */
struct be_b6_console {
	be_u32 line_open;
};

/**
 * struct be_b6_line - one bounded monitor line
 * @text: line bytes, not NUL-terminated
 * @length: bytes used
 * @overflow: nonzero once any append did not fit; the line is then unusable
 */
struct be_b6_line {
	char text[BE_B6_LINE_CAPACITY];
	be_u64 length;
	be_u32 overflow;
};

/**
 * be_b6_stce_class - classify the henvcfg readback after writing STCE only
 * @henvcfg: henvcfg readback
 *
 * Return: NONE when it reads back exactly STCE, SSTC when STCE reads 0
 *         (no Sstc, or M-mode left menvcfg.STCE clear), otherwise CONTROLS.
 */
enum be_b6_class be_b6_stce_class(be_u64 henvcfg);

/**
 * be_b6_controls_valid - check the guest controls before the first entry
 * @controls: readback after arming
 * @expected_hgatp: the installed B6 hgatp
 * @trusted_top: the management trusted-stack top
 *
 * Return: 1 when every control holds its guest-run value: hip 0 after the
 *         timer was disarmed; hstatus controls 0x180; hedeleg within 0xb15d
 *         and holding 0xb10c (WARL); hideleg VSTI only; hie, hvip,
 *         htimedelta, hgeie, and sie 0; hcounteren TM only; henvcfg STCE
 *         only; vstimecmp ~0; sstatus SIE, SPIE, SPP, FS, VS, XS, SUM, and
 *         MXR 0; the B6 hgatp; Bare vsatp; and sscratch the trusted top.
 *         Otherwise 0.
 */
int be_b6_controls_valid(const struct be_b6_controls *controls,
			 be_u64 expected_hgatp, be_u64 trusted_top);

/**
 * be_b6_class_name - stable class name printed after BE_B6:FAIL
 * @failure: class to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_b6_class_name(enum be_b6_class failure);

/**
 * be_b6_classify_cause - classify one exit cause
 * @scause: HS scause captured on the exit
 *
 * Return: %BE_B6_CLASS_NONE for a VS ecall (cause 10), the SBI path;
 *         otherwise the terminal class of the exit.
 */
enum be_b6_class be_b6_classify_cause(be_u64 scause);

/**
 * be_b6_handle_exit - count and classify one exit, and decide its SBI call
 * @state: guest-run state
 * @map: the walked B6 window
 * @record: the monitor-owned exit record the vector saved
 * @result: the decision
 *
 * Counts the exit against the ceiling and the guest-time budget, then
 * decides. Only a VS ecall from V=1 can continue the run; every other exit,
 * and every exit after the run ended, is terminal. A terminal decision moves
 * @state to FAILED, a guest shutdown to SHUTDOWN or FAILED.
 *
 * Return: the decided action.
 */
enum be_b6_action be_b6_handle_exit(struct be_b6_state *state,
				    const struct be_b6_gstage_map *map,
				    const struct be_b6_exit *record,
				    struct be_b6_result *result);

/**
 * be_b6_apply_return - write one SBI return into the saved frame
 * @frame: the monitor-owned frame
 * @result: a non-terminal decision with its final error and value
 *
 * Only a0, a1, and sepc change: sepc becomes the result's resume PC.
 */
void be_b6_apply_return(struct be_r4_frame *frame,
			const struct be_b6_result *result);

/**
 * be_b6_entry_frame - fill the first-entry exit record
 * @record: the monitor-owned exit record
 * @pc: the first guest PC (sepc)
 * @hart: the guest's a0
 * @dtb: the guest's a1
 *
 * Every other field, including every other GPR, becomes 0.
 */
void be_b6_entry_frame(struct be_b6_exit *record, be_u64 pc, be_u64 hart,
		       be_u64 dtb);

/**
 * be_b6_fail - enter the sticky terminal state
 * @state: guest-run state, if available
 * @failure: class to retain; NONE is recorded as EXCEPTION
 *
 * Return: the retained class (the first one, if already FAILED).
 */
enum be_b6_class be_b6_fail(struct be_b6_state *state,
			    enum be_b6_class failure);

/**
 * be_b6_console_tag - tag and filter guest console bytes
 * @console: tagged console state
 * @input: guest bytes, already copied into monitor memory
 * @length: at most %BE_B6_DBCN_MAX_BYTES
 * @output: monitor buffer
 * @capacity: at least %BE_B6_TAGGED_CAPACITY
 *
 * Every guest line starts with %BE_B6_GUEST_PREFIX, CR is dropped, and
 * every other byte outside 0x20-0x7e but LF becomes '?'.
 *
 * Return: bytes written to @output, or %BE_B6_TAG_INVALID (state unchanged).
 */
be_u64 be_b6_console_tag(struct be_b6_console *console, const be_u8 *input,
			 be_u64 length, char *output, be_u64 capacity);

/**
 * be_b6_console_close - end an open guest line before a monitor line
 * @console: tagged console state
 *
 * Return: 1 when a guest line was open and the caller must write LF first.
 */
be_u32 be_b6_console_close(struct be_b6_console *console);

/**
 * be_b6_line_reset - empty one monitor line
 * @line: the line
 */
void be_b6_line_reset(struct be_b6_line *line);

/**
 * be_b6_line_text - append fixed text
 * @line: the line
 * @text: NUL-terminated text
 */
void be_b6_line_text(struct be_b6_line *line, const char *text);

/**
 * be_b6_line_hex - append a lower-case 0x-prefixed hex value, no leading zeros
 * @line: the line
 * @value: value to format
 */
void be_b6_line_hex(struct be_b6_line *line, be_u64 value);

/**
 * be_b6_line_decimal - append an unsigned decimal value
 * @line: the line
 * @value: value to format
 */
void be_b6_line_decimal(struct be_b6_line *line, be_u64 value);

#endif
