/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: bounded R3 boot-and-first-entry contract for the accepted
 *          single-hart Beryllium runtime. It validates the pinned handoff,
 *          linked layout, SBI discovery, accepted R1/R2 state, reset HS/VS
 *          state, initial management binding, and bounded DBCN progress.
 * Trust:   public R3 mechanism contract. Privileged CSR, fence, SBI, and SRET
 *          operations remain in the explicit RISC-V platform boundary.
 * Scope:   R3 only. No trap classification, context save/restore, root
 *          switching, protected VS entry, access test, or R4+ behavior.
 */

#ifndef BE_R3_H
#define BE_R3_H

#include <be/r2.h>

/** @BE_R3_REPORT_SCHEMA: deterministic R3 report schema */
#define BE_R3_REPORT_SCHEMA		"be-r3-boot-entry-v1"

/** @BE_R3_CONFIGURATION_ID: accepted R1 reporting/equivalence identity */
#define BE_R3_CONFIGURATION_ID		BE_U64_C(0x771e1e75110201ac)

/** @BE_R3_OPENSBI_SPEC_VERSION: pinned firmware SBI specification version 3.0 */
#define BE_R3_OPENSBI_SPEC_VERSION	BE_U64_C(0x03000000)
/** @BE_R3_SBI_PROBE_AVAILABLE: exact successful extension-probe value */
#define BE_R3_SBI_PROBE_AVAILABLE	BE_U64_C(1)

/** @BE_R3_MANAGEMENT_HGATP: exact management Sv39x4/VMID-zero value */
#define BE_R3_MANAGEMENT_HGATP		BE_U64_C(0x8000000000080214)
/** @BE_R3_PROTECTED_HGATP: exact protected Sv39x4/VMID-zero value */
#define BE_R3_PROTECTED_HGATP		BE_U64_C(0x800000000008021c)

/** @BE_R3_INITIAL_GUEST_PC: first management VS instruction GPA */
#define BE_R3_INITIAL_GUEST_PC		BE_U64_C(0x40010000)
/** @BE_R3_INITIAL_GUEST_SP: exclusive top of management private page */
#define BE_R3_INITIAL_GUEST_SP		BE_U64_C(0x40001000)
/** @BE_R3_INITIAL_TRUSTED_SP: exclusive top of management trusted stack */
#define BE_R3_INITIAL_TRUSTED_SP	BE_U64_C(0x80227000)
/** @BE_R3_MANAGEMENT_SAVED_PA: management saved-state physical base */
#define BE_R3_MANAGEMENT_SAVED_PA	BE_U64_C(0x8022b000)

/** @BE_R3_DIAGNOSTIC_BASE: HS-only DBCN physical buffer page */
#define BE_R3_DIAGNOSTIC_BASE		BE_U64_C(0x8020f000)
/** @BE_R3_DIAGNOSTIC_END: exclusive end of the HS-only DBCN buffer */
#define BE_R3_DIAGNOSTIC_END		BE_U64_C(0x80210000)
/** @BE_R3_DBCN_MAX_ITERATIONS: fixed bounded partial/zero progress cap */
#define BE_R3_DBCN_MAX_ITERATIONS	256U

/* hstatus fields controlled for every R3 VS entry. */
#define BE_R3_HSTATUS_GVA		(BE_U64_C(1) << 6)
#define BE_R3_HSTATUS_SPV		(BE_U64_C(1) << 7)
#define BE_R3_HSTATUS_SPVP		(BE_U64_C(1) << 8)
#define BE_R3_HSTATUS_HU		(BE_U64_C(1) << 9)
#define BE_R3_HSTATUS_VGEIN_MASK	(BE_U64_C(0x3f) << 12)
#define BE_R3_HSTATUS_VTVM		(BE_U64_C(1) << 20)
#define BE_R3_HSTATUS_VTW		(BE_U64_C(1) << 21)
#define BE_R3_HSTATUS_VTSR		(BE_U64_C(1) << 22)
#define BE_R3_HSTATUS_CONTROL_MASK \
	(BE_R3_HSTATUS_SPV | BE_R3_HSTATUS_SPVP | BE_R3_HSTATUS_HU | \
	 BE_R3_HSTATUS_VGEIN_MASK | BE_R3_HSTATUS_VTVM | \
	 BE_R3_HSTATUS_VTW | BE_R3_HSTATUS_VTSR)
#define BE_R3_HSTATUS_CONTROL_VALUE \
	(BE_R3_HSTATUS_SPV | BE_R3_HSTATUS_SPVP | BE_R3_HSTATUS_VTVM | \
	 BE_R3_HSTATUS_VTW | BE_R3_HSTATUS_VTSR)

/* Supervisor status fields reset before the first entry. */
#define BE_R3_SSTATUS_SIE		(BE_U64_C(1) << 1)
#define BE_R3_SSTATUS_SPIE		(BE_U64_C(1) << 5)
#define BE_R3_SSTATUS_SPP		(BE_U64_C(1) << 8)
#define BE_R3_SSTATUS_FS_MASK		(BE_U64_C(3) << 13)
#define BE_R3_SSTATUS_XS_MASK		(BE_U64_C(3) << 15)
#define BE_R3_SSTATUS_SUM		(BE_U64_C(1) << 18)
#define BE_R3_SSTATUS_MXR		(BE_U64_C(1) << 19)
#define BE_R3_SSTATUS_CONTROL_MASK \
	(BE_R3_SSTATUS_SIE | BE_R3_SSTATUS_SPIE | BE_R3_SSTATUS_SPP | \
	 BE_R3_SSTATUS_FS_MASK | BE_R3_SSTATUS_XS_MASK | \
	 BE_R3_SSTATUS_SUM | BE_R3_SSTATUS_MXR)

/**
 * enum be_r3_phase - one-way R3 boot-and-entry phase
 * @BE_R3_PHASE_EMPTY: no R3 validation has run
 * @BE_R3_PHASE_BOOT_VALIDATED: handoff, image, and required SBI state accepted
 * @BE_R3_PHASE_R1_DERIVED: accepted R1 flow completed and independently checked
 * @BE_R3_PHASE_R2_BUILT: both physical-pool R2 trees built and re-walked
 * @BE_R3_PHASE_HS_READY: bounded HS/VS architectural state reset and verified
 * @BE_R3_PHASE_BINDING_PREPARED: exact management binding is pending
 * @BE_R3_PHASE_BINDING_PUBLISHED: fenced HGATP binding is authoritative
 * @BE_R3_PHASE_ENTRY_ARMED: exact published binding approved for SRET
 * @BE_R3_PHASE_FAILED: terminal R3 failure; no retry or recovery
 */
enum be_r3_phase {
	BE_R3_PHASE_EMPTY = 0,
	BE_R3_PHASE_BOOT_VALIDATED,
	BE_R3_PHASE_R1_DERIVED,
	BE_R3_PHASE_R2_BUILT,
	BE_R3_PHASE_HS_READY,
	BE_R3_PHASE_BINDING_PREPARED,
	BE_R3_PHASE_BINDING_PUBLISHED,
	BE_R3_PHASE_ENTRY_ARMED,
	BE_R3_PHASE_FAILED,
};

/**
 * enum be_r3_error - stable R3 failure and DBCN result classes
 * @BE_R3_ERROR_NONE: no failure
 * @BE_R3_ERROR_NULL: required pointer is absent
 * @BE_R3_ERROR_INVALID_PHASE: operation is invalid in the current phase
 * @BE_R3_ERROR_HANDOFF: OpenSBI entry address or hart identity is wrong
 * @BE_R3_ERROR_IMAGE_LAYOUT: linked security-sensitive extent is wrong
 * @BE_R3_ERROR_SBI_SPEC: SBI Base version call/result is wrong
 * @BE_R3_ERROR_SBI_DBCN_PROBE: DBCN is absent or probe result is malformed
 * @BE_R3_ERROR_SBI_SRST_PROBE: SRST is absent or probe result is malformed
 * @BE_R3_ERROR_R1_STATE: accepted R1 derived/sealed state is invalid
 * @BE_R3_ERROR_R2_STATE: R2 state, HGATP, root, or leaf set is invalid
 * @BE_R3_ERROR_HS_STATE: bounded HS/VS reset state is invalid
 * @BE_R3_ERROR_BINDING: pending or active management binding is invalid
 * @BE_R3_ERROR_PUBLICATION: HGATP readback/fence/publication state is invalid
 * @BE_R3_ERROR_DBCN_RANGE: diagnostic physical range escaped the HS page
 * @BE_R3_ERROR_DBCN_FAILED: SBI_ERR_FAILED from DBCN
 * @BE_R3_ERROR_DBCN_NOT_SUPPORTED: SBI_ERR_NOT_SUPPORTED from DBCN
 * @BE_R3_ERROR_DBCN_INVALID_PARAM: SBI_ERR_INVALID_PARAM from DBCN
 * @BE_R3_ERROR_DBCN_DENIED: SBI_ERR_DENIED from DBCN
 * @BE_R3_ERROR_DBCN_INVALID_ADDRESS: SBI_ERR_INVALID_ADDRESS from DBCN
 * @BE_R3_ERROR_DBCN_MALFORMED: undefined error or impossible progress value
 * @BE_R3_ERROR_DBCN_RETRY_EXHAUSTED: bytes remain after the fixed retry cap
 * @BE_R3_ERROR_SRST_FAILED: SBI_ERR_FAILED from SRST
 * @BE_R3_ERROR_SRST_NOT_SUPPORTED: SBI_ERR_NOT_SUPPORTED from SRST
 * @BE_R3_ERROR_SRST_INVALID_PARAM: SBI_ERR_INVALID_PARAM from SRST
 * @BE_R3_ERROR_SRST_DENIED: SBI_ERR_DENIED from SRST
 * @BE_R3_ERROR_SRST_INVALID_ADDRESS: SBI_ERR_INVALID_ADDRESS from SRST
 * @BE_R3_ERROR_SRST_RETURNED: SRST reported success but returned
 * @BE_R3_ERROR_SRST_MALFORMED: undefined SRST error value
 */
enum be_r3_error {
	BE_R3_ERROR_NONE = 0,
	BE_R3_ERROR_NULL,
	BE_R3_ERROR_INVALID_PHASE,
	BE_R3_ERROR_HANDOFF,
	BE_R3_ERROR_IMAGE_LAYOUT,
	BE_R3_ERROR_SBI_SPEC,
	BE_R3_ERROR_SBI_DBCN_PROBE,
	BE_R3_ERROR_SBI_SRST_PROBE,
	BE_R3_ERROR_R1_STATE,
	BE_R3_ERROR_R2_STATE,
	BE_R3_ERROR_HS_STATE,
	BE_R3_ERROR_BINDING,
	BE_R3_ERROR_PUBLICATION,
	BE_R3_ERROR_DBCN_RANGE,
	BE_R3_ERROR_DBCN_FAILED,
	BE_R3_ERROR_DBCN_NOT_SUPPORTED,
	BE_R3_ERROR_DBCN_INVALID_PARAM,
	BE_R3_ERROR_DBCN_DENIED,
	BE_R3_ERROR_DBCN_INVALID_ADDRESS,
	BE_R3_ERROR_DBCN_MALFORMED,
	BE_R3_ERROR_DBCN_RETRY_EXHAUSTED,
	BE_R3_ERROR_SRST_FAILED,
	BE_R3_ERROR_SRST_NOT_SUPPORTED,
	BE_R3_ERROR_SRST_INVALID_PARAM,
	BE_R3_ERROR_SRST_DENIED,
	BE_R3_ERROR_SRST_INVALID_ADDRESS,
	BE_R3_ERROR_SRST_RETURNED,
	BE_R3_ERROR_SRST_MALFORMED,
};

/**
 * enum be_r3_dbcn_state - bounded progress state for one DBCN write
 * @BE_R3_DBCN_EMPTY: fresh progress object
 * @BE_R3_DBCN_ACTIVE: range accepted; bytes remain
 * @BE_R3_DBCN_COMPLETE: all bytes consumed
 * @BE_R3_DBCN_FAILED: terminal DBCN failure
 */
enum be_r3_dbcn_state {
	BE_R3_DBCN_EMPTY = 0,
	BE_R3_DBCN_ACTIVE,
	BE_R3_DBCN_COMPLETE,
	BE_R3_DBCN_FAILED,
};

/**
 * struct be_r3_image_layout - runtime view of every linked R3 boundary
 * @entry: linked ELF entry symbol
 * @monitor_code_start: exact monitor R-X extent start
 * @monitor_code_end: actual used monitor R-X end
 * @monitor_data_start: exact monitor data extent start
 * @monitor_data_end: actual used monitor data end
 * @input_start: start of the distinct fixed R1 input section
 * @input_end: exclusive end of the fixed R1 input section
 * @bss_start: zero-initialized monitor state start
 * @bss_end: zero-initialized monitor state end
 * @diagnostic_start: exact DBCN page start
 * @diagnostic_end: exact DBCN page end
 * @root_management_start: management 32 KiB physical pool start
 * @root_management_end: management pool end
 * @root_protected_start: protected 32 KiB physical pool start
 * @root_protected_end: protected pool end
 * @stack_management_start: management trusted-stack start
 * @stack_management_end: management trusted-stack exclusive top
 * @stack_protected_start: protected trusted-stack start
 * @stack_protected_end: protected trusted-stack end
 * @saved_management_start: management saved-state page start
 * @saved_management_end: management saved-state page end
 * @saved_protected_start: protected saved-state page start
 * @saved_protected_end: protected saved-state page end
 * @private_management_start: management private backing start
 * @private_management_end: management private backing end
 * @private_protected_start: protected private backing start
 * @private_protected_end: protected private backing end
 * @shared_start: shared backing start
 * @shared_end: shared backing end
 * @guest_management_start: management guest-code page start
 * @guest_management_end: management guest-code page end
 * @guest_protected_start: protected guest-code page start
 * @guest_protected_end: protected guest-code page end
 * @trap_vector: minimal unexpected-trap sink address
 */
struct be_r3_image_layout {
	be_u64 entry;
	be_u64 monitor_code_start;
	be_u64 monitor_code_end;
	be_u64 monitor_data_start;
	be_u64 monitor_data_end;
	be_u64 input_start;
	be_u64 input_end;
	be_u64 bss_start;
	be_u64 bss_end;
	be_u64 diagnostic_start;
	be_u64 diagnostic_end;
	be_u64 root_management_start;
	be_u64 root_management_end;
	be_u64 root_protected_start;
	be_u64 root_protected_end;
	be_u64 stack_management_start;
	be_u64 stack_management_end;
	be_u64 stack_protected_start;
	be_u64 stack_protected_end;
	be_u64 saved_management_start;
	be_u64 saved_management_end;
	be_u64 saved_protected_start;
	be_u64 saved_protected_end;
	be_u64 private_management_start;
	be_u64 private_management_end;
	be_u64 private_protected_start;
	be_u64 private_protected_end;
	be_u64 shared_start;
	be_u64 shared_end;
	be_u64 guest_management_start;
	be_u64 guest_management_end;
	be_u64 guest_protected_start;
	be_u64 guest_protected_end;
	be_u64 trap_vector;
};

/**
 * struct be_r3_boot_contract - pinned OpenSBI handoff and discovery inputs
 * @entry: actual OpenSBI next-stage entry address
 * @hart_id: OpenSBI a0 hart identifier
 * @firmware_pointer: OpenSBI a1 value, recorded but never dereferenced
 * @sbi_spec_version: successful SBI Base get-spec-version value
 * @dbcn_probe: successful SBI Base probe-extension value for DBCN
 * @srst_probe: successful SBI Base probe-extension value for SRST
 * @layout: actual linker symbol values
 */
struct be_r3_boot_contract {
	be_u64 entry;
	be_u64 hart_id;
	be_u64 firmware_pointer;
	be_u64 sbi_spec_version;
	be_u64 dbcn_probe;
	be_u64 srst_probe;
	struct be_r3_image_layout layout;
};

/**
 * struct be_r3_hs_state - bounded post-reset HS/VS CSR readback
 * @satp: HS-stage translation mode, required Bare
 * @sstatus: HS supervisor status readback
 * @stvec: direct minimal trap-sink address
 * @sscratch: required zero before binding publication
 * @sepc: required zero before initial entry is armed
 * @scause: reset HS trap cause
 * @stval: reset HS trap value
 * @sie: disabled HS interrupt-enable state
 * @sip: no pending HS interrupt in the frozen profile
 * @senvcfg: disabled HS environment configuration
 * @scounteren: disabled lower-privilege counter access
 * @hstatus: required virtualization-control fields
 * @hedeleg: no delegated VS exception
 * @hideleg: no delegated VS interrupt
 * @hie: disabled hypervisor interrupt enables
 * @hip: no pending hypervisor interrupt
 * @hvip: no pending virtual interrupt injection
 * @hcounteren: disabled VS/VU counter access
 * @htimedelta: zero virtual time delta
 * @henvcfg: disabled hypervisor environment configuration
 * @hgeie: disabled guest external interrupt enables
 * @hgeip: no pending guest external interrupt
 * @htval: reset hypervisor trap value
 * @hgatp: required Bare/VMID-zero before publication
 * @vsstatus: reset VS supervisor status
 * @vsie: disabled VS interrupt enables
 * @vstvec: reset VS trap vector
 * @vsscratch: reset VS scratch
 * @vsepc: reset VS saved PC; not the initial HS SRET target
 * @vscause: reset VS trap cause
 * @vstval: reset VS trap value
 * @vsip: reset VS pending interrupts
 * @vsatp: required VS-stage Bare
 */
struct be_r3_hs_state {
	be_u64 satp;
	be_u64 sstatus;
	be_u64 stvec;
	be_u64 sscratch;
	be_u64 sepc;
	be_u64 scause;
	be_u64 stval;
	be_u64 sie;
	be_u64 sip;
	be_u64 senvcfg;
	be_u64 scounteren;
	be_u64 hstatus;
	be_u64 hedeleg;
	be_u64 hideleg;
	be_u64 hie;
	be_u64 hip;
	be_u64 hvip;
	be_u64 hcounteren;
	be_u64 htimedelta;
	be_u64 henvcfg;
	be_u64 hgeie;
	be_u64 hgeip;
	be_u64 htval;
	be_u64 hgatp;
	be_u64 vsstatus;
	be_u64 vsie;
	be_u64 vstvec;
	be_u64 vsscratch;
	be_u64 vsepc;
	be_u64 vscause;
	be_u64 vstval;
	be_u64 vsip;
	be_u64 vsatp;
};

/**
 * struct be_r3_binding - exact initial management execution binding
 * @domain: management domain
 * @vcpu_id: management vCPU identity
 * @root_id: management root identity
 * @vmid: fixed VMID zero
 * @hgatp: exact management Sv39x4 value
 * @guest_pc: first management VS instruction
 * @guest_sp: exclusive management private-page top
 * @trusted_sp: exclusive management trusted-stack top
 * @saved_state_id: management saved-state identity
 * @saved_state_pa: management saved-state physical page
 * @vsatp: VS-stage Bare
 * @published: zero while pending, one only after HGATP/fence/readback
 */
struct be_r3_binding {
	enum be_domain_id domain;
	be_u32 vcpu_id;
	be_u32 root_id;
	be_u32 vmid;
	be_u64 hgatp;
	be_u64 guest_pc;
	be_u64 guest_sp;
	be_u64 trusted_sp;
	be_u32 saved_state_id;
	be_u64 saved_state_pa;
	be_u64 vsatp;
	be_u32 published;
};

/**
 * struct be_r3_state - complete host-testable R3 publication state
 * @phase: one-way R3 phase
 * @error: sticky terminal error
 * @firmware_pointer: recorded OpenSBI a1 value; never dereferenced
 * @configuration_id: accepted R1 reporting/equivalence identity
 * @management_hgatp: re-walked management value
 * @protected_hgatp: re-walked protected value
 * @pending: unpublished management binding
 * @active: published management binding
 */
struct be_r3_state {
	enum be_r3_phase phase;
	enum be_r3_error error;
	be_u64 firmware_pointer;
	be_u64 configuration_id;
	be_u64 management_hgatp;
	be_u64 protected_hgatp;
	struct be_r3_binding pending;
	struct be_r3_binding active;
};

/**
 * struct be_r3_dbcn_progress - bounded state for one physical DBCN write
 * @state: one-way DBCN progress state
 * @error: terminal error, if any
 * @base: validated HS diagnostic physical base
 * @length: total requested byte count
 * @offset: bytes consumed so far
 * @iterations: SBI calls consumed, bounded by BE_R3_DBCN_MAX_ITERATIONS
 */
struct be_r3_dbcn_progress {
	enum be_r3_dbcn_state state;
	enum be_r3_error error;
	be_u64 base;
	be_u64 length;
	be_u64 offset;
	be_u32 iterations;
};

#define BE_R3_STATE_INITIALIZER { \
	.phase = BE_R3_PHASE_EMPTY, \
	.error = BE_R3_ERROR_NONE, \
}

#define BE_R3_DBCN_INITIALIZER { \
	.state = BE_R3_DBCN_EMPTY, \
	.error = BE_R3_ERROR_NONE, \
}

/**
 * be_r3_validate_boot - validate pinned handoff, layout, and SBI discovery
 * @state: fresh R3 state
 * @contract: actual boot and linker observations
 *
 * Return: %BE_R3_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r3_error
be_r3_validate_boot(struct be_r3_state *state,
		    const struct be_r3_boot_contract *contract);

/**
 * be_r3_note_r1_derived - independently accept exact derived R1 state
 * @state: boot-validated R3 state
 * @runtime: accepted R1 runtime after copy/validate/seal/derive
 *
 * Return: %BE_R3_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r3_error
be_r3_note_r1_derived(struct be_r3_state *state,
		      const struct be_runtime *runtime);

/**
 * be_r3_note_r2_built - accept exact physical-pool R2 output and re-walk
 * @state: R1-derived R3 state
 * @runtime: accepted derived R1 runtime
 * @output: R2 output required in BUILT state
 * @leaf_sets: independent re-walked management and protected leaves
 *
 * Return: %BE_R3_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r3_error
be_r3_note_r2_built(struct be_r3_state *state,
		    const struct be_runtime *runtime,
		    const struct be_r2_output *output,
		    const struct be_r2_leaf_set leaf_sets[BE_MAX_ROOTS]);

/**
 * be_r3_note_hs_ready - validate reset and verified HS/VS state
 * @state: R2-built R3 state
 * @hs: complete bounded CSR readback
 * @layout: previously accepted linker layout
 *
 * Return: %BE_R3_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r3_error
be_r3_note_hs_ready(struct be_r3_state *state,
		    const struct be_r3_hs_state *hs,
		    const struct be_r3_image_layout *layout);

/**
 * be_r3_prepare_management_binding - validate the exact pending binding
 * @state: HS-ready R3 state
 * @binding: unpublished management binding candidate
 *
 * Return: %BE_R3_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r3_error
be_r3_prepare_management_binding(struct be_r3_state *state,
				 const struct be_r3_binding *binding);

/**
 * be_r3_publish_management_binding - publish only after fence and readback
 * @state: binding-prepared R3 state
 * @hgatp_readback: CSR value read after the local HFENCE.GVMA
 * @fence_completed: one only after the required local all-GPA/all-VMID fence
 *
 * Return: %BE_R3_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r3_error
be_r3_publish_management_binding(struct be_r3_state *state,
				 be_u64 hgatp_readback,
				 be_u32 fence_completed);

/**
 * be_r3_arm_management_entry - approve SRET for the exact active binding
 * @state: binding-published R3 state
 * @binding: caller's exact published binding view
 *
 * Return: %BE_R3_ERROR_NONE on success, otherwise a sticky terminal error.
 */
enum be_r3_error
be_r3_arm_management_entry(struct be_r3_state *state,
			   const struct be_r3_binding *binding);

/**
 * be_r3_fail - enter terminal failure without a recovery transition
 * @state: R3 state, if available
 * @error: nonzero error to retain
 *
 * Return: retained terminal error.
 */
enum be_r3_error
be_r3_fail(struct be_r3_state *state, enum be_r3_error error);

/**
 * be_r3_dbcn_begin - validate one bounded HS diagnostic range
 * @progress: fresh DBCN progress object
 * @base: physical start address
 * @length: byte count, including zero
 *
 * Return: %BE_R3_ERROR_NONE on accepted range, otherwise terminal error.
 */
enum be_r3_error
be_r3_dbcn_begin(struct be_r3_dbcn_progress *progress,
		 be_u64 base, be_u64 length);

/**
 * be_r3_dbcn_consume - consume one DBCN SBI result
 * @progress: active DBCN progress object
 * @sbi_error: signed SBI error returned in a0
 * @bytes_written: returned progress value in a1
 *
 * Zero and partial progress are accepted within the fixed call cap. Every
 * frozen SBI error is surfaced distinctly. Undefined errors, oversized
 * progress, and retry exhaustion fail terminally.
 *
 * Return: %BE_R3_ERROR_NONE while active or complete, otherwise error.
 */
enum be_r3_error
be_r3_dbcn_consume(struct be_r3_dbcn_progress *progress,
		   long sbi_error, be_u64 bytes_written);

/**
 * be_r3_srst_result - classify an SRST call that returned
 * @sbi_error: signed SBI error returned in a0
 *
 * A successful SRST is non-returning, so returned success is itself terminal.
 * Every frozen error is surfaced distinctly; undefined values are malformed.
 *
 * Return: terminal SRST error class.
 */
enum be_r3_error be_r3_srst_result(long sbi_error);

/**
 * be_r3_phase_name - return a stable R3 phase name
 * @phase: phase to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_r3_phase_name(enum be_r3_phase phase);

/**
 * be_r3_error_name - return a stable R3 error name
 * @error: error to name
 *
 * Return: constant name, or "invalid".
 */
const char *be_r3_error_name(enum be_r3_error error);

#endif
