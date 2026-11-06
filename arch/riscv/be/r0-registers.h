/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: frozen R0 VS/HS architectural register-state matrix for the fixed
 *          single-hart Beryllium runtime, as a machine-checkable enumeration.
 * Trust:   reviewable non-authoritative declaration. R0 implements no save,
 *          restore, or reset; the authoritative matrix with rationale lives in
 *          planning/single-hart-runtime-r0-freeze.md.
 * Scope:   R0 freeze only. Every accessible architectural element has exactly
 *          one disposition: saved/restored, reset+verified, denied under a
 *          checked control, a constant trusted assumption, or explicitly
 *          excluded. F, D, and V are absent from the pinned CPU profile
 *          (verified base ISA rv64imach), not merely cleared.
 */

#ifndef BE_R0_REGISTERS_H
#define BE_R0_REGISTERS_H

#include <be/manifest.h>

/**
 * enum be_r0_disposition - the only permitted R0 register dispositions
 * @BE_R0_SAVED: saved and restored for the exact domain
 * @BE_R0_RESET: reset to a domain-independent value and verified per entry
 * @BE_R0_DENIED: inaccessible under a checked architecture control
 * @BE_R0_CONSTANT: constant trusted platform assumption, not written by HS
 * @BE_R0_EXCLUDED: explicitly excluded from the isolation claim or absent
 */
enum be_r0_disposition {
	BE_R0_SAVED = 0,
	BE_R0_RESET,
	BE_R0_DENIED,
	BE_R0_CONSTANT,
	BE_R0_EXCLUDED,
};

/**
 * enum be_r0_reg_group - register-matrix coverage groups from the plan
 * @BE_R0_GROUP_INTEGER: integer x0-x31, guest PC, and guest stack
 * @BE_R0_GROUP_VS_CSR: VS-level supervisor CSRs
 * @BE_R0_GROUP_HS_HYP: HS hypervisor/delegation/virtualization CSRs
 * @BE_R0_GROUP_HS_TRAP: HS supervisor trap-metadata and control CSRs
 * @BE_R0_GROUP_BINDING: active HGATP/root/VMID/stack/saved-state identity
 * @BE_R0_GROUP_COUNTER: counters, PMU, and their access gates
 * @BE_R0_GROUP_FPV: floating-point and vector state
 * @BE_R0_GROUP_OPTIONAL: AIA, Sstc, Smstateen, Sdtrig, and debug/trace
 * @BE_R0_GROUP_MACHINE: M-mode, PMP/ePMP, and firmware assumptions
 */
enum be_r0_reg_group {
	BE_R0_GROUP_INTEGER = 0,
	BE_R0_GROUP_VS_CSR,
	BE_R0_GROUP_HS_HYP,
	BE_R0_GROUP_HS_TRAP,
	BE_R0_GROUP_BINDING,
	BE_R0_GROUP_COUNTER,
	BE_R0_GROUP_FPV,
	BE_R0_GROUP_OPTIONAL,
	BE_R0_GROUP_MACHINE,
	BE_R0_GROUP_COUNT,
};

/**
 * struct be_r0_register - one frozen register-matrix entry
 * @name: architectural element name
 * @group: coverage group
 * @disposition: the single R0 disposition for this element
 */
struct be_r0_register {
	const char *name;
	enum be_r0_reg_group group;
	enum be_r0_disposition disposition;
};

static const struct be_r0_register be_r0_registers[] = {
	/* Integer, guest PC, and guest stack. */
	{ "x0", BE_R0_GROUP_INTEGER, BE_R0_EXCLUDED },
	{ "x1-x31-general", BE_R0_GROUP_INTEGER, BE_R0_SAVED },
	{ "x2-sp-via-sscratch", BE_R0_GROUP_INTEGER, BE_R0_SAVED },
	{ "guest-pc-vsepc", BE_R0_GROUP_INTEGER, BE_R0_SAVED },
	{ "guest-stack-page", BE_R0_GROUP_INTEGER, BE_R0_SAVED },
	/* VS-level CSRs. */
	{ "vsstatus", BE_R0_GROUP_VS_CSR, BE_R0_RESET },
	{ "vsie", BE_R0_GROUP_VS_CSR, BE_R0_RESET },
	{ "vstvec", BE_R0_GROUP_VS_CSR, BE_R0_SAVED },
	{ "vsscratch", BE_R0_GROUP_VS_CSR, BE_R0_RESET },
	{ "vsepc", BE_R0_GROUP_VS_CSR, BE_R0_SAVED },
	{ "vscause", BE_R0_GROUP_VS_CSR, BE_R0_SAVED },
	{ "vstval", BE_R0_GROUP_VS_CSR, BE_R0_SAVED },
	{ "vsip", BE_R0_GROUP_VS_CSR, BE_R0_RESET },
	{ "vsatp-bare-verified", BE_R0_GROUP_VS_CSR, BE_R0_RESET },
	/* HS hypervisor CSRs. */
	{ "hstatus-vtvm-set", BE_R0_GROUP_HS_HYP, BE_R0_RESET },
	{ "hedeleg", BE_R0_GROUP_HS_HYP, BE_R0_RESET },
	{ "hideleg", BE_R0_GROUP_HS_HYP, BE_R0_RESET },
	{ "hie", BE_R0_GROUP_HS_HYP, BE_R0_RESET },
	{ "hip", BE_R0_GROUP_HS_HYP, BE_R0_DENIED },
	{ "hvip", BE_R0_GROUP_HS_HYP, BE_R0_RESET },
	{ "hcounteren", BE_R0_GROUP_HS_HYP, BE_R0_RESET },
	{ "htimedelta", BE_R0_GROUP_HS_HYP, BE_R0_RESET },
	{ "henvcfg", BE_R0_GROUP_HS_HYP, BE_R0_RESET },
	{ "hgeie", BE_R0_GROUP_HS_HYP, BE_R0_DENIED },
	{ "hgeip", BE_R0_GROUP_HS_HYP, BE_R0_DENIED },
	{ "hvip-virtual-interrupt", BE_R0_GROUP_HS_HYP, BE_R0_RESET },
	/* HS supervisor trap metadata and control. */
	{ "scause", BE_R0_GROUP_HS_TRAP, BE_R0_SAVED },
	{ "sepc", BE_R0_GROUP_HS_TRAP, BE_R0_SAVED },
	{ "stval", BE_R0_GROUP_HS_TRAP, BE_R0_SAVED },
	{ "htval", BE_R0_GROUP_HS_TRAP, BE_R0_SAVED },
	{ "htinst-may-be-zero", BE_R0_GROUP_HS_TRAP, BE_R0_EXCLUDED },
	{ "sstatus", BE_R0_GROUP_HS_TRAP, BE_R0_RESET },
	{ "stvec", BE_R0_GROUP_HS_TRAP, BE_R0_RESET },
	{ "sscratch", BE_R0_GROUP_HS_TRAP, BE_R0_RESET },
	{ "sie", BE_R0_GROUP_HS_TRAP, BE_R0_RESET },
	{ "sip", BE_R0_GROUP_HS_TRAP, BE_R0_DENIED },
	{ "satp-hs-bare", BE_R0_GROUP_HS_TRAP, BE_R0_CONSTANT },
	{ "senvcfg", BE_R0_GROUP_HS_TRAP, BE_R0_RESET },
	{ "scounteren", BE_R0_GROUP_HS_TRAP, BE_R0_RESET },
	/* Active binding identity. */
	{ "hgatp-active", BE_R0_GROUP_BINDING, BE_R0_SAVED },
	{ "vmid-zero", BE_R0_GROUP_BINDING, BE_R0_CONSTANT },
	{ "trusted-stack-identity", BE_R0_GROUP_BINDING, BE_R0_SAVED },
	{ "saved-state-identity", BE_R0_GROUP_BINDING, BE_R0_SAVED },
	/* Counters and PMU. */
	{ "cycle-time-instret-vs-view", BE_R0_GROUP_COUNTER, BE_R0_DENIED },
	{ "hpmcounters-vs-view", BE_R0_GROUP_COUNTER, BE_R0_DENIED },
	{ "mcounteren-mcountinhibit", BE_R0_GROUP_COUNTER, BE_R0_CONSTANT },
	/* Floating-point and vector: absent from the pinned CPU profile. */
	{ "f0-f31-fcsr", BE_R0_GROUP_FPV, BE_R0_EXCLUDED },
	{ "v0-v31-vcsr-vl-vtype", BE_R0_GROUP_FPV, BE_R0_EXCLUDED },
	/* Optional architectural state: absent or excluded. */
	{ "aia-ssaia-imsic-aplic", BE_R0_GROUP_OPTIONAL, BE_R0_EXCLUDED },
	{ "sstc-stimecmp-vstimecmp", BE_R0_GROUP_OPTIONAL, BE_R0_EXCLUDED },
	{ "smstateen-hstateen-sstateen", BE_R0_GROUP_OPTIONAL, BE_R0_EXCLUDED },
	{ "sdtrig-triggers-hcontext", BE_R0_GROUP_OPTIONAL, BE_R0_EXCLUDED },
	{ "debug-trace-dcsr", BE_R0_GROUP_OPTIONAL, BE_R0_EXCLUDED },
	/* Machine mode and firmware assumptions. */
	{ "pmp-epmp-mseccfg", BE_R0_GROUP_MACHINE, BE_R0_CONSTANT },
	{ "misa-medeleg-mideleg", BE_R0_GROUP_MACHINE, BE_R0_CONSTANT },
	{ "iommu-iopmp-absent", BE_R0_GROUP_MACHINE, BE_R0_EXCLUDED },
};

#endif
