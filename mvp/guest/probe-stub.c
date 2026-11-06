// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP VS probe stub (planning/mvp-m0-plan.md, Platform record:
 *          probes), a bare-metal VS program in B5's guest style. It asks the
 *          probe image which probe it is; probe-platform's stub takes three
 *          guest-page faults, lets the probe handler wait for 100 IPIs in
 *          HS, spins through 100 more at V=1, and lets the handler run the
 *          ordering probe; a VMID image's stub runs the VMID sequence.
 *          Either ends with the probe's FINISH, after which the hart parks.
 * Trust:   untrusted VS code. Every exit is the probe handler's to decide;
 *          the stub's calls use mvp/src/mvp-probe.h's extension, functions,
 *          and probe numbers, and a mismatch fails the probe run closed.
 * Scope:   probe images only; no SBI call, console, or timer.
 */

#define STUB_EID		0x08424550UL
#define STUB_FID_KIND		0UL
#define STUB_FID_FAULTS_DONE	1UL
#define STUB_FID_IPI_HS		2UL
#define STUB_FID_ORDER		4UL
#define STUB_FID_FINISH		7UL
#define STUB_KIND_PLATFORM	1UL

void stub_main(void) __attribute__((noreturn));
void stub_fault_load(void);
void stub_fault_store(void);
void stub_fault_fetch(void);
void stub_spin_ipis(void);
void stub_vmid(void) __attribute__((noreturn));

/* One probe call: a7 the extension, a6 the function; a0 the answer. */
static unsigned long probe(unsigned long fid)
{
	register unsigned long a0 __asm__("a0") = 0UL;
	register unsigned long a1 __asm__("a1") = 0UL;
	register unsigned long a6 __asm__("a6") = fid;
	register unsigned long a7 __asm__("a7") = STUB_EID;

	__asm__ __volatile__("ecall"
			     : "+r"(a0), "+r"(a1)
			     : "r"(a6), "r"(a7)
			     : "memory");
	return a0;
}

void stub_main(void)
{
	if (probe(STUB_FID_KIND) != STUB_KIND_PLATFORM)
		stub_vmid();
	stub_fault_load();
	stub_fault_store();
	stub_fault_fetch();
	(void)probe(STUB_FID_FAULTS_DONE);
	(void)probe(STUB_FID_IPI_HS);
	stub_spin_ipis();
	(void)probe(STUB_FID_ORDER);
	/* FINISH parks the hart; it does not return. */
	for (;;)
		(void)probe(STUB_FID_FINISH);
}
