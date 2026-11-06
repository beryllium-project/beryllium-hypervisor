/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP probe module (planning/mvp-m0-plan.md, "Platform
 *          record: probes and negative images"): the three probe images'
 *          hart 0 driver and domain hart handler, which replace the payload
 *          placement and the Linux domains. probe-platform reports each
 *          other hart's HSM status, the hgatp modes and VMID width, three
 *          guest-page faults from the VS probe stub, IPI delivery to a hart
 *          waiting in HS and to one spinning at V=1, and cross-hart
 *          ordering without and with fences; probe-vmid-distinct and
 *          probe-vmid-shared report what the stub reads at one GPA before
 *          and after a raw hgatp switch from root A to root B, with a
 *          distinct or the same VMID. probe-console-input
 *          (planning/mvp-m7-plan.md, D-12 and Q14) has hart 0 poll the
 *          firmware console for a fixed window, with no parser and no
 *          routing, and print every byte it receives.
 * Trust:   probe-only code, linked only into the probe images. The raw
 *          hgatp write without a fence (mvp-probe-arch.S) exists only in the
 *          two VMID images; the probe's mode writes go through the
 *          executor's install of the accepted function, from one call site
 *          (mvp-executor.h). The probe's shared words are probe data;
 *          nothing here is the substrate's.
 * Scope:   facts for the platform record, printed as BE_MVP:PROBE lines in
 *          a fixed order and ended by BE_MVP:14; nothing here is a claim.
 */

#ifndef BE_MVP_PROBE_H
#define BE_MVP_PROBE_H

#include "mvp-platform.h"

/* BE_MVP_PROBE_IMAGE: which probe image the build is. */
#define BE_MVP_PROBE_PLATFORM		1U
#define BE_MVP_PROBE_VMID_DISTINCT	2U
#define BE_MVP_PROBE_VMID_SHARED	3U
#define BE_MVP_PROBE_CONSOLE_INPUT	4U

/*
 * The stub's calls (guest/probe-stub.c names the same values): an SBI
 * experimental-range extension that only the probe images serve.
 */
#define BE_MVP_PROBE_EID		BE_U64_C(0x08424550)
#define BE_MVP_PROBE_FID_KIND		BE_U64_C(0)
#define BE_MVP_PROBE_FID_FAULTS_DONE	BE_U64_C(1)
#define BE_MVP_PROBE_FID_IPI_HS		BE_U64_C(2)
#define BE_MVP_PROBE_FID_IPI_VS		BE_U64_C(3)
#define BE_MVP_PROBE_FID_ORDER		BE_U64_C(4)
#define BE_MVP_PROBE_FID_VMID_BEFORE	BE_U64_C(5)
#define BE_MVP_PROBE_FID_VMID_AFTER	BE_U64_C(6)
#define BE_MVP_PROBE_FID_FINISH		BE_U64_C(7)

/* The probe's guest addresses: the stub, a GPA no root maps, and X. */
#define BE_MVP_PROBE_STUB_GPA		BE_MVP_KERNEL_GPA
#define BE_MVP_PROBE_OUTSIDE_GPA	BE_U64_C(0x90000000)
#define BE_MVP_PROBE_X_GPA		BE_U64_C(0x80100000)
#define BE_MVP_PROBE_VALUE_A		BE_U64_C(0xa5a5a5a5a5a5a5a5)
#define BE_MVP_PROBE_VALUE_B		BE_U64_C(0x5a5a5a5a5a5a5a5a)
#define BE_MVP_PROBE_FAULTS		3U
#define BE_MVP_PROBE_IPIS		100U
#define BE_MVP_PROBE_ORDER_ITERATIONS	10000U
#define BE_MVP_PROBE_VMID_READS		10U
/* The probe's own waits: each step on either hart, and each IPI's answer. */
#define BE_MVP_PROBE_WAIT_TICKS		BE_MVP_READY_TICKS
#define BE_MVP_PROBE_IPI_TICKS		BE_MVP_HART_START_TICKS
/*
 * probe-console-input's window: 2^29 ticks, 22 s at the board's 24 MHz
 * (54 s at QEMU's 10 MHz), polled every BE_MVP_INPUT_POLL_TICKS on hart
 * 0's own timer; each line of received bytes holds at most 64.
 */
#define BE_MVP_PROBE_INPUT_TICKS	BE_U64_C(0x20000000)
#define BE_MVP_PROBE_INPUT_LINE_BYTES	64U

#if defined(BE_MVP_PROBE_IMAGE)
#if BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_PLATFORM
#define BE_MVP_PROBE_NAME		"probe-platform"
#elif BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_VMID_DISTINCT
#define BE_MVP_PROBE_NAME		"probe-vmid-distinct"
#elif BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_VMID_SHARED
#define BE_MVP_PROBE_NAME		"probe-vmid-shared"
#elif BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_CONSOLE_INPUT
#define BE_MVP_PROBE_NAME		"probe-console-input"
#else
#error "BE_MVP_PROBE_IMAGE names no probe image"
#endif
#endif

/**
 * be_mvp_probe_hgatp - hart 0: the hgatp modes and the VMID width
 *
 * Writes Sv48x4, Sv57x4, and Sv39x4 with VMID 0x3fff at the management
 * root's PPN through the executor's install, from the probe's one call
 * site, reads each back, restores the management root, and prints
 * BE_MVP:PROBE hgatp.
 */
void be_mvp_probe_hgatp(void);

/**
 * be_mvp_probe_place - hart 0: the stub in both windows, and X's values
 * @maps: both domains' walked windows
 */
void be_mvp_probe_place(const struct be_mvp_gstage_map *maps);

/**
 * be_mvp_probe_run - hart 0: drive the probes, print them, and shut down
 *
 * Runs after domain 0's READY and ENTERED; prints the BE_MVP:PROBE lines
 * in their fixed order, then BE_MVP:14, and requests the accepted SRST.
 * probe-console-input's, after the stub's FINISH: the window's line, a
 * line per 64 bytes received and one for the rest, then the counts.
 */
void be_mvp_probe_run(void) __attribute__((noreturn));

/**
 * be_mvp_probe_exit - the domain hart: serve one exit of the probe stub
 * @page: the hart's state page
 * @record: the exit
 *
 * Records the stub's guest-page faults and IPIs, serves its probe calls,
 * and resumes it, or parks the hart when the stub finishes; anything else
 * fails the hart.
 */
void be_mvp_probe_exit(struct be_mvp_hart_page *page,
		       struct be_mvp_exit *record) __attribute__((noreturn));

/* hart 0's runtime, for the probe module (mvp-runtime.c). */
void be_mvp_probe_emit(const char *format, const be_u64 *values);
void be_mvp_probe_poll(void);
void be_mvp_probe_fail(enum be_mvp_class failure, const char *format,
		       const be_u64 *values) __attribute__((noreturn));
void be_mvp_probe_shutdown(void) __attribute__((noreturn));

/**
 * be_mvp_probe_arch_switch_hgatp - the VMID probes' raw hgatp write
 * @hgatp: root B's hgatp
 *
 * Writes hgatp with no fence and reads it back: the one exception to the
 * install-function rule, in the two VMID probe images only, called only
 * through the executor (be_mvp_exec_switch_hgatp()).
 *
 * Return: the hgatp readback.
 */
be_u64 be_mvp_probe_arch_switch_hgatp(be_u64 hgatp);

extern const be_u8 be_mvp_probe_stub[];
extern const be_u8 be_mvp_probe_stub_end[];

#endif
