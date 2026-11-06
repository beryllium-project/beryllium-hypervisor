// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP probe module (planning/mvp-m0-plan.md, "Platform record:
 *          probes and negative images"; mvp-probe.h): hart 0's hgatp probe,
 *          its placement of the VS probe stub in both windows, and its
 *          driver and printer; and domain 0's hart's service of the stub's
 *          exits: three guest-page faults, 100 IPIs waited for in HS and
 *          100 taken at V=1, the ordering probe without and with fences,
 *          and, in the VMID images, the raw switch from root A to root B.
 * Trust:   probe-only restricted C. The two harts meet in the probe's own
 *          words in the MVP region's BSS, which hart 0 clears before the
 *          barrier, never in a block: each is written by one hart at a
 *          time and published by a fence w, w before the phase that admits
 *          it, except the unfenced ordering run's payload and flag, whose
 *          missing fences are the measurement. Every wait is bounded by the
 *          time CSR but hart 1's wait for an IPI in HS, which hart 0's
 *          bound ends with the run. Anything the stub does outside the
 *          probe fails its hart closed. Every fence, time read, IPI, SSIP
 *          clear, wait, hgatp write, park, and resume is the executor's
 *          (mvp-executor.c; planning/mvp-m6-plan.md, D-5); the module
 *          performs none itself.
 * Scope:   probe images only; never linked into the MVP image. The lines
 *          are facts for the platform record, not claims. In
 *          probe-console-input (planning/mvp-m7-plan.md, D-12), hart 0
 *          alone reads the firmware console, on its own timer at M7's
 *          cadence, after the stub's VMID sequence, there without the
 *          switch, has parked domain 0's hart.
 */
#include "mvp-probe.h"

#include "mvp-executor.h"
#include "mvp-input.h"
#include "mvp-sha256.h"

#if !defined(BE_MVP_PROBE_IMAGE)
#error "the probe module is linked only into the probe images"
#endif

/* Hart 1's progress, in order; hart 0 waits for each. */
#define PHASE_FAULTS			1U
#define PHASE_IPI_HS			2U
#define PHASE_IPI_HS_DONE		3U
#define PHASE_IPI_VS			4U
#define PHASE_IPI_VS_DONE		5U
#define PHASE_ORDER			6U
#define PHASE_ORDER_FENCED		7U
#define PHASE_ORDER_DONE		8U
#define PHASE_FINISHED			9U
/* One fault: scause, stval, htval, htinst, sepc, and hstatus.GVA. */
#define FAULT_WORDS			6U
#define HSTATUS_GVA_SHIFT		6U
#define HGATP_MODE_SHIFT		60U
#define HGATP_MODE_SV39X4		BE_U64_C(8)
#define HGATP_MODE_SV48X4		BE_U64_C(9)
#define HGATP_MODE_SV57X4		BE_U64_C(10)
#define HGATP_VMID_SHIFT		44U
#define HGATP_VMID_BITS			14U
#define HGATP_VMID_MAX			BE_U64_C(0x3fff)
#define HGATP_PPN_MASK			((BE_U64_C(1) << HGATP_VMID_SHIFT) - 1U)
/* The stub names its next label in t6. */
#define GPR_T6				BE_R4_GPR_INDEX(31U)

/*
 * The probe's shared words. Hart 0 writes sent, payload, flag, and, before
 * the barrier, hgatp_a and hgatp; hart 1 writes the rest, and hgatp at the
 * VMID switch. Each IPI phase counts its receipts in its own word, as it
 * keeps its own delta and spv. One count for both phases was a race
 * (M9-3; planning/mvp-m9-plan.md, stop 2, fixed in M9 on the responsible
 * human's decision "fix now" of 2026-11-03): hart 1's FID_IPI_VS call
 * zeroed it as soon as its hundredth HS receipt let it leave ipi_hs(), so
 * hart 0, reading it after PHASE_IPI_HS_DONE for its HS line, could print
 * delivered=0 and fail ipi though all 100 were delivered. Hart 0 reading
 * it sooner cannot close the race, since hart 1 can reach that call
 * between hart 0's hundredth send and its first read; nothing writes
 * received[0] after hart 1's hundredth HS receipt.
 */
struct probe_shared {
	volatile be_u64 phase;
	volatile be_u64 sent;
	volatile be_u64 received[2];
	volatile be_u64 payload;
	volatile be_u64 flag;
	volatile be_u64 ack;
	be_u64 hgatp_a;
	be_u64 hgatp;
	be_u64 faults;
	be_u64 fault[BE_MVP_PROBE_FAULTS][FAULT_WORDS];
	be_u64 delta[2][BE_MVP_PROBE_IPIS];
	be_u64 spv[2];
	be_u64 stale[2];
	be_u64 before;
	be_u64 after;
};

static struct probe_shared probe;

static const char marker_wait[] =
	"BE_MVP:DETAIL probe_phase=%d reached=%d";
#if BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_PLATFORM
static const char marker_hgatp[] = "BE_MVP:PROBE hgatp vmid=0x3fff "
	"sv48x4=%x sv57x4=%x sv39x4=%x vmid_bits=%d restored=%x";
static const char marker_restore[] =
	"BE_MVP:DETAIL register=hgatp wanted=%x readback=%x";
static const char *const marker_gpf[BE_MVP_PROBE_FAULTS] = {
	"BE_MVP:PROBE gpf access=load gpa=%x scause=%x stval=%x htval=%x "
	"htinst=%x sepc=%x gva=%d",
	"BE_MVP:PROBE gpf access=store gpa=%x scause=%x stval=%x htval=%x "
	"htinst=%x sepc=%x gva=%d",
	"BE_MVP:PROBE gpf access=fetch gpa=%x scause=%x stval=%x htval=%x "
	"htinst=%x sepc=%x gva=%d",
};
static const char *const marker_ipi[2] = {
	"BE_MVP:PROBE ipi mode=hs sent=%d delivered=%d min=%x median=%x "
	"max=%x spv=%d",
	"BE_MVP:PROBE ipi mode=vs sent=%d delivered=%d min=%x median=%x "
	"max=%x spv=%d",
};
static const char *const marker_order[2] = {
	"BE_MVP:PROBE order mode=unfenced iterations=%d stale=%d",
	"BE_MVP:PROBE order mode=fenced iterations=%d stale=%d",
};
static const char marker_missed[] =
	"BE_MVP:DETAIL probe_ipis=%d answered=%d";
static const char marker_unacked[] =
	"BE_MVP:DETAIL probe_order=%d ack=%d";
#elif BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_CONSOLE_INPUT
/*
 * Hart 0's record of the firmware console: the SHA-256 of every byte in
 * the order given, the bytes of the line not yet printed, and the counts;
 * and a line's text, its head and the bytes as hex pairs, which holds no
 * '%' but its head's.
 */
static struct {
	struct be_mvp_sha256 digest;
	be_u8 buffer[BE_MVP_INPUT_READ_BYTES];
	be_u8 line[BE_MVP_PROBE_INPUT_LINE_BYTES];
	be_u64 pending;
	be_u64 total;
	be_u64 polls;
	be_u64 nonzero;
	be_u64 most;
	be_u64 errors;
} input;
static char input_text[BE_MVP_LINE_CAPACITY];
static const char marker_window[] = "BE_MVP:PROBE console-input "
	"window_ticks=%x prefix=none";
static const char marker_bytes[] =
	"BE_MVP:PROBE console-input bytes=%d hex=";
static const char marker_total[] = "BE_MVP:PROBE console-input total=%d "
	"polls=%d nonzero_polls=%d max_per_poll=%d errors=%d sha256=";
#else
static const char marker_vmid[] = "BE_MVP:PROBE vmid mode="
#if BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_VMID_SHARED
	"shared"
#else
	"distinct"
#endif
	" gpa=%x hgatp_a=%x hgatp_b=%x value_a=%x value_b=%x reads=%d "
	"before=%x after=%x";
#endif

/* Hart 1: everything before this phase, then the phase. */
static void set_phase(be_u64 phase)
{
	be_mvp_exec_fence_w_w();
	probe.phase = phase;
}

/* Hart 0: wait for hart 1's phase; a FAIL arrives through its ring. */
static void wait_phase(be_u64 phase)
{
	be_u64 start = be_mvp_exec_read_time();

	while (probe.phase < phase) {
		be_mvp_probe_poll();
		if (be_mvp_exec_read_time() - start >=
		    BE_MVP_PROBE_WAIT_TICKS) {
			be_u64 values[2] = { phase, probe.phase };

			be_mvp_probe_fail(BE_MVP_CLASS_RUN_TIMEOUT, marker_wait,
					  values);
		}
	}
	be_mvp_exec_fence_r_r();
}

void be_mvp_probe_place(const struct be_mvp_gstage_map *maps)
{
	be_u64 bytes = (be_u64)(be_mvp_probe_stub_end - be_mvp_probe_stub);
	be_u64 domain;

	if (bytes == 0U || bytes > BE_PAGE_SIZE)
		be_mvp_runtime_terminal(BE_MVP_CLASS_PAYLOAD);
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		be_u64 offset = maps[domain].hpa_base - maps[domain].gpa_base;

		(void)memcpy((void *)(BE_MVP_PROBE_STUB_GPA + offset),
			     be_mvp_probe_stub, bytes);
		*(volatile be_u64 *)(void *)(BE_MVP_PROBE_X_GPA + offset) =
			domain == 0U ? BE_MVP_PROBE_VALUE_A :
				       BE_MVP_PROBE_VALUE_B;
	}
	probe.hgatp_a = maps[0].hgatp;
	probe.hgatp = maps[0].hgatp;
}

#if BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_PLATFORM
void be_mvp_probe_hgatp(void)
{
	static const be_u64 modes[3] = {
		HGATP_MODE_SV48X4, HGATP_MODE_SV57X4, HGATP_MODE_SV39X4,
	};
	be_u64 values[5];
	be_u64 index;

	/* The probe's one call of the executor's install: each mode, then
	 * the restore. */
	for (index = 0U; index < 4U; ++index) {
		be_u64 hgatp = BE_R3_MANAGEMENT_HGATP;

		if (index < 3U)
			hgatp = (modes[index] << HGATP_MODE_SHIFT) |
				(HGATP_VMID_MAX << HGATP_VMID_SHIFT) |
				(BE_R3_MANAGEMENT_HGATP & HGATP_PPN_MASK);
		values[index < 3U ? index : 4U] =
			be_mvp_exec_install_hgatp(hgatp);
	}
	values[3] = 0U;
	for (index = 0U; index < HGATP_VMID_BITS; ++index)
		values[3] += (values[2] >> (HGATP_VMID_SHIFT + index)) & 1U;
	be_mvp_probe_emit(marker_hgatp, values);
	if (values[4] != BE_R3_MANAGEMENT_HGATP) {
		be_u64 detail[2] = { BE_R3_MANAGEMENT_HGATP, values[4] };

		be_mvp_probe_fail(BE_MVP_CLASS_GSTAGE, marker_restore, detail);
	}
}

/* Hart 0: 100 IPIs, each received before the next; then their numbers. */
static void ipis(be_u32 mode, be_u64 ready, be_u64 done)
{
	be_u64 sorted[BE_MVP_PROBE_IPIS];
	be_u64 values[6];
	be_u64 sent;
	be_u64 index;

	wait_phase(ready);
	for (sent = 0U; sent < BE_MVP_PROBE_IPIS; ++sent) {
		be_u64 start;

		probe.sent = be_mvp_exec_read_time();
		/* The send time before the IPI that admits its read. */
		be_mvp_exec_fence_w_w();
		if (be_mvp_send_ipi(be_mvp_bindings[0].hart) !=
		    BE_MVP_SBI_SUCCESS)
			break;
		start = be_mvp_exec_read_time();
		while (probe.received[mode] <= sent &&
		       be_mvp_exec_read_time() - start <
			       BE_MVP_PROBE_IPI_TICKS)
			be_mvp_probe_poll();
		if (probe.received[mode] <= sent)
			break;
	}
	if (sent == BE_MVP_PROBE_IPIS)
		wait_phase(done);
	be_mvp_exec_fence_r_r();
	values[0] = sent;
	values[1] = probe.received[mode];
	for (index = 0U; index < values[1] && index < BE_MVP_PROBE_IPIS;
	     ++index) {
		be_u64 value = probe.delta[mode][index];
		be_u64 at = index;

		/* Insertion sort: the median of at most 100 deltas. */
		while (at > 0U && sorted[at - 1U] > value) {
			sorted[at] = sorted[at - 1U];
			--at;
		}
		sorted[at] = value;
	}
	values[2] = index != 0U ? sorted[0] : 0U;
	values[3] = index != 0U ? sorted[index / 2U] : 0U;
	values[4] = index != 0U ? sorted[index - 1U] : 0U;
	values[5] = probe.spv[mode];
	be_mvp_probe_emit(marker_ipi[mode], values);
	if (values[1] != BE_MVP_PROBE_IPIS)
		be_mvp_probe_fail(BE_MVP_CLASS_IPI, marker_missed, values);
}

/*
 * Hart 0: write the payload, then the flag, 10,000 times, each after hart
 * 1's acknowledgement of the last; fence w, w between them when fenced.
 */
static void order(be_u32 mode, be_u64 ready)
{
	be_u64 base = mode * BE_MVP_PROBE_ORDER_ITERATIONS;
	be_u64 index;

	wait_phase(ready);
	for (index = base + 1U; index <= base + BE_MVP_PROBE_ORDER_ITERATIONS;
	     ++index) {
		be_u64 start;

		probe.payload = index;
		if (mode != 0U)
			be_mvp_exec_fence_w_w();
		probe.flag = index;
		start = be_mvp_exec_read_time();
		while (probe.ack != index) {
			be_mvp_probe_poll();
			if (be_mvp_exec_read_time() - start >=
			    BE_MVP_PROBE_WAIT_TICKS) {
				be_u64 values[2] = { index, probe.ack };

				be_mvp_probe_fail(BE_MVP_CLASS_RUN_TIMEOUT,
						  marker_unacked, values);
			}
		}
	}
}

void be_mvp_probe_run(void)
{
	be_u64 values[7];
	be_u64 index;

	wait_phase(PHASE_FAULTS);
	for (index = 0U; index < BE_MVP_PROBE_FAULTS; ++index) {
		be_u64 field;

		values[0] = BE_MVP_PROBE_OUTSIDE_GPA;
		for (field = 0U; field < FAULT_WORDS; ++field)
			values[1U + field] = probe.fault[index][field];
		be_mvp_probe_emit(marker_gpf[index], values);
	}
	ipis(0U, PHASE_IPI_HS, PHASE_IPI_HS_DONE);
	ipis(1U, PHASE_IPI_VS, PHASE_IPI_VS_DONE);
	order(0U, PHASE_ORDER);
	order(1U, PHASE_ORDER_FENCED);
	wait_phase(PHASE_ORDER_DONE);
	for (index = 0U; index < 2U; ++index) {
		values[0] = BE_MVP_PROBE_ORDER_ITERATIONS;
		values[1] = probe.stale[index];
		be_mvp_probe_emit(marker_order[index], values);
	}
	wait_phase(PHASE_FINISHED);
	be_mvp_probe_shutdown();
}

/*
 * Hart 1: one IPI received at @now with hstatus @hstatus; SSIP is cleared
 * first, so that the next IPI is never lost.
 */
static __attribute__((noinline)) void receipt(be_u32 mode, be_u64 now,
					       be_u64 hstatus)
{
	be_u64 index = probe.received[mode];

	(void)be_mvp_exec_clear_ssip();
	be_mvp_exec_fence_r_r();
	probe.delta[mode][index] = now - probe.sent;
	if ((hstatus & BE_MVP_HSTATUS_SPV) != 0U)
		++probe.spv[mode];
	be_mvp_exec_fence_w_w();
	probe.received[mode] = index + 1U;
}

/*
 * Hart 1 in HS, inside the stub's probe call: 100 IPIs, each found pending
 * after a wfi with sstatus.SIE 0. Nothing traps or writes hstatus after the
 * call's exit, so hstatus.SPV at each receipt is the exit's.
 */
static void ipi_hs(const struct be_mvp_exit *record)
{
	probe.received[0] = 0U;
	set_phase(PHASE_IPI_HS);
	while (probe.received[0] < BE_MVP_PROBE_IPIS)
		receipt(0U, be_mvp_exec_wait(BE_MVP_SIE_SSIE),
			record->hstatus);
	set_phase(PHASE_IPI_HS_DONE);
}

/*
 * Hart 1 in HS, inside the stub's probe call: wait for each flag, read its
 * payload, and acknowledge it, 10,000 times a mode. Fenced, fence r, r
 * orders the payload's read after the flag's, and fence r, w the read
 * before the acknowledgement that lets hart 0 write the next payload.
 */
static void order_reader(struct be_mvp_exit *record)
{
	be_u32 mode;

	for (mode = 0U; mode < 2U; ++mode) {
		be_u64 base = mode * BE_MVP_PROBE_ORDER_ITERATIONS;
		be_u64 index;

		set_phase(mode == 0U ? PHASE_ORDER : PHASE_ORDER_FENCED);
		for (index = base + 1U;
		     index <= base + BE_MVP_PROBE_ORDER_ITERATIONS; ++index) {
			be_u64 start = be_mvp_exec_read_time();

			while (probe.flag != index)
				if (be_mvp_exec_read_time() - start >=
				    BE_MVP_PROBE_WAIT_TICKS)
					be_mvp_hart_terminal(
						record, BE_MVP_CLASS_RUN_TIMEOUT);
			if (mode != 0U)
				be_mvp_exec_fence_r_r();
			if (probe.payload != index)
				++probe.stale[mode];
			if (mode != 0U)
				be_mvp_exec_fence_r_w();
			probe.ack = index;
		}
	}
	set_phase(PHASE_ORDER_DONE);
}
#elif BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_CONSOLE_INPUT
/* TEXT, then @bytes as lower-case hex pairs, into input_text. */
static void input_compose(const char *text, const be_u8 *bytes, be_u64 count)
{
	static const char digits[] = "0123456789abcdef";
	be_u64 at = 0U;
	be_u64 index;

	for (index = 0U; text[index] != '\0'; ++index)
		input_text[at++] = text[index];
	for (index = 0U; index < count; ++index) {
		input_text[at++] = digits[bytes[index] >> 4];
		input_text[at++] = digits[bytes[index] & 0xfU];
	}
	input_text[at] = '\0';
}

/* The bytes not yet printed, as one line, with the count so far. */
static void input_line(void)
{
	if (input.pending == 0U)
		return;
	input_compose(marker_bytes, input.line, input.pending);
	be_mvp_probe_emit(input_text, &input.total);
	input.pending = 0U;
}

/*
 * One poll, as hart 0's in an image with console input (mvp-runtime.c,
 * poll_input()): the firmware's console_read, 64 bytes at a time, until it
 * holds none or 256 were read; every byte recorded, a line printed per 64;
 * a failed read counted, and the poll ended.
 */
static void input_poll(void)
{
	be_u64 total = 0U;

	++input.polls;
	while (total < BE_MVP_INPUT_POLL_MAX) {
		be_u64 want = BE_MVP_INPUT_POLL_MAX - total;
		be_u64 got = ~BE_U64_C(0);
		be_u64 index;

		if (want > BE_MVP_INPUT_READ_BYTES)
			want = BE_MVP_INPUT_READ_BYTES;
		if (be_mvp_exec_console_read(input.buffer, want, &got) !=
			    BE_MVP_SBI_SUCCESS || got > want) {
			++input.errors;
			break;
		}
		if (got == 0U)
			break;
		be_mvp_sha256_update(&input.digest, input.buffer, got);
		for (index = 0U; index < got; ++index) {
			input.line[input.pending++] = input.buffer[index];
			++input.total;
			if (input.pending == BE_MVP_PROBE_INPUT_LINE_BYTES)
				input_line();
		}
		total += got;
	}
	if (total != 0U)
		++input.nonzero;
	if (total > input.most)
		input.most = total;
}

/*
 * Hart 0, after the stub's FINISH: the window's line, then a poll every
 * BE_MVP_INPUT_POLL_TICKS on its own timer, armed through the budget
 * helper, as M7's hart 0 polls (D-1, Q2), and one more at the window's
 * end; then the rest of the bytes, the counts, and the first 16 hex
 * digits of every byte's SHA-256.
 */
void be_mvp_probe_run(void)
{
	be_u8 digest[BE_MVP_SHA256_BYTES];
	be_u64 values[5];
	be_u64 now;
	be_u64 end;

	wait_phase(PHASE_FINISHED);
	values[0] = BE_MVP_PROBE_INPUT_TICKS;
	be_mvp_probe_emit(marker_window, values);
	be_mvp_sha256_init(&input.digest);
	now = be_mvp_exec_read_time();
	end = now + BE_MVP_PROBE_INPUT_TICKS;
	while (now < end) {
		be_u64 next = now + BE_MVP_INPUT_POLL_TICKS;

		input_poll();
		if (next > end)
			next = end;
		if (be_mvp_exec_arm_budget(next, (be_u64)(unsigned long)
					   __be_control_stack_end) !=
		    BE_MVP_SIE_CONTROL)
			be_mvp_runtime_terminal(BE_MVP_CLASS_CONTROLS);
		do {
			now = be_mvp_exec_wait(BE_MVP_SIE_CONTROL);
			(void)be_mvp_exec_clear_ssip();
			be_mvp_probe_poll();
		} while (now < next);
	}
	input_poll();
	input_line();
	be_mvp_sha256_final(&input.digest, digest);
	values[0] = input.total;
	values[1] = input.polls;
	values[2] = input.nonzero;
	values[3] = input.most;
	values[4] = input.errors;
	input_compose(marker_total, digest, sizeof(be_u64));
	be_mvp_probe_emit(input_text, values);
	be_mvp_probe_shutdown();
}
#else
void be_mvp_probe_run(void)
{
	be_u64 values[8];

	wait_phase(PHASE_FINISHED);
	values[0] = BE_MVP_PROBE_X_GPA;
	values[1] = probe.hgatp_a;
	values[2] = probe.hgatp;
	values[3] = BE_MVP_PROBE_VALUE_A;
	values[4] = BE_MVP_PROBE_VALUE_B;
	values[5] = BE_MVP_PROBE_VMID_READS;
	values[6] = probe.before;
	values[7] = probe.after;
	be_mvp_probe_emit(marker_vmid, values);
	be_mvp_probe_shutdown();
}
#endif

/* Hart 1: one probe call from the stub; it resumes after the ecall. */
static void probe_call(struct be_mvp_exit *record)
{
	struct be_r4_frame *frame = &record->frame;
	be_u64 answer = 0U;

	switch (frame->gpr[BE_R4_GPR_A6]) {
	case BE_MVP_PROBE_FID_KIND:
		answer = BE_MVP_PROBE_IMAGE;
		break;
#if BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_PLATFORM
	case BE_MVP_PROBE_FID_FAULTS_DONE:
		if (probe.faults != BE_MVP_PROBE_FAULTS)
			be_mvp_hart_terminal(record, BE_MVP_CLASS_EXCEPTION);
		set_phase(PHASE_FAULTS);
		break;
	case BE_MVP_PROBE_FID_IPI_HS:
		ipi_hs(record);
		break;
	case BE_MVP_PROBE_FID_IPI_VS:
		probe.received[1] = 0U;
		set_phase(PHASE_IPI_VS);
		break;
	case BE_MVP_PROBE_FID_ORDER:
		order_reader(record);
		break;
#else
	case BE_MVP_PROBE_FID_VMID_BEFORE:
		probe.before = frame->gpr[BE_R4_GPR_A0];
#if BE_MVP_PROBE_IMAGE != BE_MVP_PROBE_CONSOLE_INPUT
		/* Root B, the other window's; the same VMID when shared. */
		probe.hgatp = be_mvp_exec_switch_hgatp(be_mvp_hgatp(
#if BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_VMID_SHARED
			be_mvp_bindings[0].vmid,
#else
			be_mvp_bindings[1].vmid,
#endif
			be_mvp_bindings[1].root));
#endif
		break;
	case BE_MVP_PROBE_FID_VMID_AFTER:
		probe.after = frame->gpr[BE_R4_GPR_A0];
		break;
#endif
	case BE_MVP_PROBE_FID_FINISH:
		set_phase(PHASE_FINISHED);
		be_mvp_exec_park();
	default:
		be_mvp_hart_terminal(record, BE_MVP_CLASS_EXCEPTION);
	}
	frame->gpr[BE_R4_GPR_A0] = answer;
	frame->gpr[BE_R4_GPR_A1] = 0U;
}

void be_mvp_probe_exit(struct be_mvp_hart_page *page,
		       struct be_mvp_exit *record)
{
	struct be_r4_frame *frame = &record->frame;
	be_u64 scause = frame->scause;

	if (scause == BE_MVP_SCAUSE_VS_ECALL &&
	    frame->gpr[BE_R4_GPR_A7] == BE_MVP_PROBE_EID) {
		probe_call(record);
		frame->sepc += BE_MVP_INSTRUCTION_SIZE;
#if BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_PLATFORM
	} else if ((scause == BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT ||
		    scause == BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT ||
		    scause == BE_MVP_SCAUSE_FETCH_GUEST_PAGE_FAULT) &&
		   probe.faults < BE_MVP_PROBE_FAULTS) {
		be_u64 *fault = probe.fault[probe.faults];

		++probe.faults;
		fault[0] = scause;
		fault[1] = frame->stval;
		fault[2] = frame->htval;
		fault[3] = record->htinst;
		fault[4] = frame->sepc;
		fault[5] = (record->hstatus >> HSTATUS_GVA_SHIFT) & 1U;
		frame->sepc = frame->gpr[GPR_T6];
	} else if (scause == BE_MVP_SCAUSE_SUPERVISOR_SOFTWARE &&
		   probe.phase == PHASE_IPI_VS &&
		   probe.received[1] < BE_MVP_PROBE_IPIS) {
		receipt(1U, record->time, record->hstatus);
		/* The hundredth ends the stub's spin at its named label. */
		if (probe.received[1] == BE_MVP_PROBE_IPIS) {
			set_phase(PHASE_IPI_VS_DONE);
			frame->sepc = frame->gpr[GPR_T6];
		}
#endif
	} else {
		be_mvp_hart_terminal(record, BE_MVP_CLASS_EXCEPTION);
	}
	be_mvp_exec_resume(record, probe.hgatp, page->page.controls.hedeleg);
}
