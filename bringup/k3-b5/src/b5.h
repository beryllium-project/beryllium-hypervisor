/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B5 guest SBI core contract: exit classification and the exit
 *          budget, the bounded B5-only SBI subset (Base, TIME, DBCN, SRST),
 *          the DBCN guest-range check against the management leaves R2
 *          re-walked and R3 checked, the tagged guest console, and the
 *          fixed-format monitor line builder.
 * Trust:   restricted-C mechanism only. It reads no CSR, issues no SBI call,
 *          performs no I/O, and dereferences no guest address: it returns an
 *          action, and the B5 runtime performs it.
 * Scope:   B5 only (planning/k3-b5-plan.md). It selects no SBI profile,
 *          hypercall ABI, stable guest ABI, or Linux guest interface, and no
 *          guest request is ever forwarded to M-mode.
 */

#ifndef BE_B5_H
#define BE_B5_H

#include <be/r4.h>

/* Extension and function identifiers, compared as exact 64-bit values. */
#define BE_B5_SBI_EID_BASE		BE_U64_C(0x10)
#define BE_B5_SBI_EID_TIME		BE_U64_C(0x54494d45)
#define BE_B5_SBI_EID_DBCN		BE_U64_C(0x4442434e)
#define BE_B5_SBI_EID_SRST		BE_U64_C(0x53525354)

#define BE_B5_SBI_BASE_GET_SPEC_VERSION	BE_U64_C(0)
#define BE_B5_SBI_BASE_GET_IMPL_ID	BE_U64_C(1)
#define BE_B5_SBI_BASE_GET_IMPL_VERSION	BE_U64_C(2)
#define BE_B5_SBI_BASE_PROBE_EXTENSION	BE_U64_C(3)
#define BE_B5_SBI_BASE_GET_MVENDORID	BE_U64_C(4)
#define BE_B5_SBI_BASE_GET_MARCHID	BE_U64_C(5)
#define BE_B5_SBI_BASE_GET_MIMPID	BE_U64_C(6)
#define BE_B5_SBI_TIME_SET_TIMER	BE_U64_C(0)
#define BE_B5_SBI_DBCN_WRITE		BE_U64_C(0)
#define BE_B5_SBI_DBCN_READ		BE_U64_C(1)
#define BE_B5_SBI_DBCN_WRITE_BYTE	BE_U64_C(2)
#define BE_B5_SBI_SRST_SYSTEM_RESET	BE_U64_C(0)

/* Base values: SBI 2.0 and the provisional, unregistered B5 identity. */
#define BE_B5_SBI_SPEC_VERSION		BE_U64_C(0x2000000)
#define BE_B5_SBI_IMPL_ID		BE_U64_C(0x4245)
#define BE_B5_SBI_IMPL_VERSION		BE_U64_C(1)

/* Standard SBI errors the subset returns. */
#define BE_B5_SBI_SUCCESS		0L
#define BE_B5_SBI_ERR_NOT_SUPPORTED	(-2L)
#define BE_B5_SBI_ERR_INVALID_PARAM	(-3L)
#define BE_B5_SBI_ERR_DENIED		(-4L)

/* SRST arguments: types 0-2 and reasons 0-1 are defined; others reserved. */
#define BE_B5_SRST_TYPE_SHUTDOWN	BE_U64_C(0)
#define BE_B5_SRST_TYPE_WARM_REBOOT	BE_U64_C(2)
#define BE_B5_SRST_REASON_NONE		BE_U64_C(0)
#define BE_B5_SRST_REASON_FAILURE	BE_U64_C(1)

/* Exit handling. */
#define BE_B5_EXIT_BUDGET		1024U
#define BE_B5_INSTRUCTION_SIZE		BE_U64_C(4)
#define BE_B5_SCAUSE_INTERRUPT		(BE_U64_C(1) << 63)
#define BE_B5_SCAUSE_ILLEGAL_INSTRUCTION	BE_U64_C(2)
#define BE_B5_SCAUSE_VS_ECALL		BE_U64_C(10)
#define BE_B5_SCAUSE_FETCH_GUEST_PAGE_FAULT	BE_U64_C(20)
#define BE_B5_SCAUSE_LOAD_GUEST_PAGE_FAULT	BE_U64_C(21)
#define BE_B5_SCAUSE_VIRTUAL_INSTRUCTION	BE_U64_C(22)
#define BE_B5_SCAUSE_STORE_GUEST_PAGE_FAULT	BE_U64_C(23)
#define BE_B5_GPR_A2			BE_R4_GPR_INDEX(12U)

/* Tagged console: at most 256 guest bytes per call, each line prefixed. */
#define BE_B5_DBCN_MAX_BYTES		256U
#define BE_B5_GUEST_PREFIX		"BE_B5_GUEST: "
#define BE_B5_GUEST_PREFIX_LENGTH	13U
#define BE_B5_TAGGED_CAPACITY \
	((BE_B5_GUEST_PREFIX_LENGTH + 1U) * BE_B5_DBCN_MAX_BYTES)
#define BE_B5_TAG_INVALID		(~BE_U64_C(0))

/* One monitor line, built from fixed text and formatted values. */
#define BE_B5_LINE_CAPACITY		160U

/* Guest controls while the guest runs (planning/k3-b5-plan.md). */
#define BE_B5_HENVCFG_STCE		(BE_U64_C(1) << 63)
#define BE_B5_HSTATUS_GUEST_CONTROLS \
	(BE_R3_HSTATUS_CONTROL_VALUE & ~BE_R3_HSTATUS_VTSR)
#define BE_B5_HIDELEG_VSTI		(BE_U64_C(1) << 6)
#define BE_B5_HIE_VSTIE			(BE_U64_C(1) << 6)
#define BE_B5_HCOUNTEREN_TM		(BE_U64_C(1) << 1)
#define BE_B5_VSTIMECMP_DISARMED	(~BE_U64_C(0))

/**
 * struct be_b5_controls - guest-control readback after arming
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
 *
 * Only assembly reads these CSRs; C validates this monitor-owned copy.
 */
struct be_b5_controls {
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
};

/**
 * enum be_b5_class - stable B5 terminal classes, printed as BE_B5:FAIL <name>
 * @BE_B5_CLASS_NONE: no failure
 * @BE_B5_CLASS_BOOT: boot contract, R1, R2, R3 check, binding, install, or arm
 * @BE_B5_CLASS_SSTC: henvcfg.STCE reads back 0
 * @BE_B5_CLASS_CONTROLS: a guest control did not read back as written
 * @BE_B5_CLASS_INTERRUPT: an interrupt reached HS
 * @BE_B5_CLASS_GUEST_PAGE_FAULT: fetch, load, or store guest-page fault
 * @BE_B5_CLASS_VIRTUAL_INSTRUCTION: virtual-instruction exception
 * @BE_B5_CLASS_ILLEGAL_INSTRUCTION: illegal-instruction exception
 * @BE_B5_CLASS_EXCEPTION: any other exit, or one the core cannot accept
 * @BE_B5_CLASS_EXIT_BUDGET: more than %BE_B5_EXIT_BUDGET exits
 * @BE_B5_CLASS_RESUME: a resume check failed
 * @BE_B5_CLASS_CONSOLE: a firmware console write failed
 * @BE_B5_CLASS_GUEST_FAILURE: the guest requested shutdown with reason 1
 * @BE_B5_CLASS_SHUTDOWN_RETURNED: the monitor's SRST shutdown returned
 * @BE_B5_CLASS_COUNT: number of classes, not a class
 */
enum be_b5_class {
	BE_B5_CLASS_NONE = 0,
	BE_B5_CLASS_BOOT,
	BE_B5_CLASS_SSTC,
	BE_B5_CLASS_CONTROLS,
	BE_B5_CLASS_INTERRUPT,
	BE_B5_CLASS_GUEST_PAGE_FAULT,
	BE_B5_CLASS_VIRTUAL_INSTRUCTION,
	BE_B5_CLASS_ILLEGAL_INSTRUCTION,
	BE_B5_CLASS_EXCEPTION,
	BE_B5_CLASS_EXIT_BUDGET,
	BE_B5_CLASS_RESUME,
	BE_B5_CLASS_CONSOLE,
	BE_B5_CLASS_GUEST_FAILURE,
	BE_B5_CLASS_SHUTDOWN_RETURNED,
	BE_B5_CLASS_COUNT,
};

/**
 * enum be_b5_phase - one-way guest-run phase
 * @BE_B5_PHASE_RUNNING: exits are accepted
 * @BE_B5_PHASE_SHUTDOWN: the guest requested shutdown with reason 0
 * @BE_B5_PHASE_FAILED: terminal failure; the class is sticky
 */
enum be_b5_phase {
	BE_B5_PHASE_RUNNING = 0,
	BE_B5_PHASE_SHUTDOWN,
	BE_B5_PHASE_FAILED,
};

/**
 * enum be_b5_action - what the runtime must do for one exit
 * @BE_B5_ACTION_NONE: no decision
 * @BE_B5_ACTION_RETURN: return the error and value to the guest
 * @BE_B5_ACTION_CONSOLE_WRITE: copy the bytes at the HS physical source
 *                              through the tagged console, then return
 * @BE_B5_ACTION_CONSOLE_BYTE: write one byte through the tagged console,
 *                             then return
 * @BE_B5_ACTION_SET_TIMER: write the timer value to vstimecmp, then return
 * @BE_B5_ACTION_SHUTDOWN: guest shutdown, reason 0: report and shut down
 * @BE_B5_ACTION_GUEST_FAILURE: guest shutdown, reason 1: fail and shut down
 * @BE_B5_ACTION_TERMINAL: fail closed with the result's class
 */
enum be_b5_action {
	BE_B5_ACTION_NONE = 0,
	BE_B5_ACTION_RETURN,
	BE_B5_ACTION_CONSOLE_WRITE,
	BE_B5_ACTION_CONSOLE_BYTE,
	BE_B5_ACTION_SET_TIMER,
	BE_B5_ACTION_SHUTDOWN,
	BE_B5_ACTION_GUEST_FAILURE,
	BE_B5_ACTION_TERMINAL,
};

/**
 * struct be_b5_state - guest-run state
 * @phase: one-way phase
 * @failure: sticky terminal class once @phase is FAILED
 * @exits: exits taken, each counted against %BE_B5_EXIT_BUDGET
 */
struct be_b5_state {
	enum be_b5_phase phase;
	enum be_b5_class failure;
	be_u32 exits;
};

#define BE_B5_STATE_INITIALIZER { \
	.phase = BE_B5_PHASE_RUNNING, \
	.failure = BE_B5_CLASS_NONE, \
	.exits = 0U, \
}

/**
 * struct be_b5_result - the decision for one exit
 * @action: what the runtime must do
 * @failure: terminal class for %BE_B5_ACTION_TERMINAL
 * @error: SBI error the guest receives in a0
 * @value: SBI value the guest receives in a1
 * @source_pa: HS physical address of the first DBCN byte
 * @length: DBCN bytes to copy, at most %BE_B5_DBCN_MAX_BYTES
 * @timer: vstimecmp value for %BE_B5_ACTION_SET_TIMER
 * @resume_pc: guest PC after the ecall
 * @byte: the DBCN write-byte argument
 */
struct be_b5_result {
	enum be_b5_action action;
	enum be_b5_class failure;
	long error;
	be_u64 value;
	be_u64 source_pa;
	be_u64 length;
	be_u64 timer;
	be_u64 resume_pc;
	be_u8 byte;
};

/**
 * struct be_b5_console - tagged guest console state
 * @line_open: nonzero while a guest line has its prefix but no newline yet
 */
struct be_b5_console {
	be_u32 line_open;
};

/**
 * struct be_b5_line - one bounded monitor line
 * @text: line bytes, not NUL-terminated
 * @length: bytes used
 * @overflow: nonzero once any append did not fit; the line is then unusable
 */
struct be_b5_line {
	char text[BE_B5_LINE_CAPACITY];
	be_u64 length;
	be_u32 overflow;
};

/**
 * be_b5_stce_class - classify the henvcfg readback after writing STCE only
 * @henvcfg: henvcfg readback
 *
 * Return: NONE when it reads back exactly STCE, SSTC when STCE reads 0
 *         (no Sstc, or M-mode left menvcfg.STCE clear), otherwise CONTROLS.
 */
enum be_b5_class be_b5_stce_class(be_u64 henvcfg);

/**
 * be_b5_controls_valid - check the guest controls before the first entry
 * @controls: readback after arming
 * @expected_hgatp: the published management hgatp
 *
 * Return: 1 when every control holds its guest-run value: hip 0 after the
 *         timer was disarmed; hstatus controls 0x300180; hedeleg 0; hideleg
 *         VSTI only; hie, hvip, htimedelta, hgeie, sie, and sstatus.SIE 0;
 *         hcounteren TM only; henvcfg STCE only; vstimecmp ~0; the
 *         management hgatp; and Bare vsatp. Otherwise 0.
 */
int be_b5_controls_valid(const struct be_b5_controls *controls,
			 be_u64 expected_hgatp);

/**
 * be_b5_class_name - stable class name printed after BE_B5:FAIL
 * @failure: class to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_b5_class_name(enum be_b5_class failure);

/**
 * be_b5_classify_cause - classify one exit cause
 * @scause: HS scause captured on the exit
 *
 * Return: %BE_B5_CLASS_NONE for a VS ecall (cause 10), the SBI path;
 *         otherwise the terminal class of the exit.
 */
enum be_b5_class be_b5_classify_cause(be_u64 scause);

/**
 * be_b5_translate_read - translate one guest range for an HS read
 * @leaves: the re-walked management leaf set
 * @gpa: guest-physical start
 * @length: nonzero byte count
 * @pa: HS physical start on success
 *
 * The range must not wrap and must lie inside one readable 4 KiB leaf.
 *
 * Return: 1 on success, 0 otherwise (@pa is then unchanged).
 */
int be_b5_translate_read(const struct be_r2_leaf_set *leaves, be_u64 gpa,
			 be_u64 length, be_u64 *pa);

/**
 * be_b5_handle_exit - classify one exit and decide its SBI call
 * @state: guest-run state
 * @leaves: the re-walked management leaf set
 * @frame: the monitor-owned frame the vector saved
 * @result: the decision
 *
 * Counts the exit against the budget, then decides. Only a VS ecall can
 * continue the run; every other exit, and every exit after the run ended, is
 * terminal. A terminal decision moves @state to FAILED, a guest shutdown to
 * SHUTDOWN or FAILED.
 *
 * Return: the decided action.
 */
enum be_b5_action be_b5_handle_exit(struct be_b5_state *state,
				    const struct be_r2_leaf_set *leaves,
				    const struct be_r4_frame *frame,
				    struct be_b5_result *result);

/**
 * be_b5_apply_return - write one SBI return into the saved frame
 * @frame: the monitor-owned frame
 * @result: a non-terminal decision with its final error and value
 *
 * Only a0, a1, and sepc change: sepc becomes the result's resume PC.
 */
void be_b5_apply_return(struct be_r4_frame *frame,
			const struct be_b5_result *result);

/**
 * be_b5_fail - enter the sticky terminal state
 * @state: guest-run state, if available
 * @failure: class to retain; NONE is recorded as EXCEPTION
 *
 * Return: the retained class (the first one, if already FAILED).
 */
enum be_b5_class be_b5_fail(struct be_b5_state *state,
			    enum be_b5_class failure);

/**
 * be_b5_console_tag - tag and filter guest console bytes
 * @console: tagged console state
 * @input: guest bytes, already copied into monitor memory
 * @length: at most %BE_B5_DBCN_MAX_BYTES
 * @output: monitor buffer
 * @capacity: at least %BE_B5_TAGGED_CAPACITY
 *
 * Every guest line starts with %BE_B5_GUEST_PREFIX, and every byte outside
 * 0x20-0x7e other than LF becomes '?'.
 *
 * Return: bytes written to @output, or %BE_B5_TAG_INVALID (state unchanged).
 */
be_u64 be_b5_console_tag(struct be_b5_console *console, const be_u8 *input,
			 be_u64 length, char *output, be_u64 capacity);

/**
 * be_b5_console_close - end an open guest line before a monitor line
 * @console: tagged console state
 *
 * Return: 1 when a guest line was open and the caller must write LF first.
 */
be_u32 be_b5_console_close(struct be_b5_console *console);

/**
 * be_b5_line_reset - empty one monitor line
 * @line: the line
 */
void be_b5_line_reset(struct be_b5_line *line);

/**
 * be_b5_line_text - append fixed text
 * @line: the line
 * @text: NUL-terminated text
 */
void be_b5_line_text(struct be_b5_line *line, const char *text);

/**
 * be_b5_line_hex - append a lower-case 0x-prefixed hex value, no leading zeros
 * @line: the line
 * @value: value to format
 */
void be_b5_line_hex(struct be_b5_line *line, be_u64 value);

/**
 * be_b5_line_decimal - append an unsigned decimal value
 * @line: the line
 * @value: value to format
 */
void be_b5_line_decimal(struct be_b5_line *line, be_u64 value);

#endif
