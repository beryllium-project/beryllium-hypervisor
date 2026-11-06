/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: explicit RISC-V privileged/SBI boundary for the bounded R3
 *          boot-and-first-entry image.
 * Trust:   architecture boundary. CSR, ECALL, HFENCE.GVMA, WFI, and SRET
 *          behavior remains trusted and is inspected/tested but not proved.
 * Scope:   R3 only; no trap frame, context save/restore, root switch, or
 *          protected-domain entry.
 */

#ifndef BE_R3_PLATFORM_H
#define BE_R3_PLATFORM_H

#include <be/r3.h>

/**
 * struct be_r3_sbi_return - exact SBI a0/a1 return pair
 * @error: signed SBI error from a0
 * @value: SBI value from a1
 */
struct be_r3_sbi_return {
	long error;
	be_u64 value;
};

/**
 * be_r3_runtime_main - execute the complete bounded R3 boot sequence
 * @hart_id: OpenSBI a0 hart identifier
 * @firmware_pointer: OpenSBI a1 value, recorded but never dereferenced
 */
void be_r3_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
	__attribute__((noreturn));

/**
 * be_r3_arch_sbi_call - issue one allowlisted HS-to-M SBI call
 * @result: output return pair
 * @eid: extension identifier
 * @fid: function identifier
 * @argument0: SBI a0 input
 * @argument1: SBI a1 input
 * @argument2: SBI a2 input
 */
void be_r3_arch_sbi_call(struct be_r3_sbi_return *result,
			 be_u64 eid, be_u64 fid,
			 be_u64 argument0, be_u64 argument1,
			 be_u64 argument2);

/**
 * be_r3_arch_reset_state - reset and read back the bounded HS/VS state
 * @trap_vector: direct minimal unexpected-trap sink
 * @state: complete CSR readback output
 */
void be_r3_arch_reset_state(be_u64 trap_vector,
			    struct be_r3_hs_state *state);

/**
 * be_r3_arch_install_management - write, fence, and read management HGATP
 * @hgatp: exact management Sv39x4/VMID-zero value
 *
 * Return: HGATP readback after local HFENCE.GVMA x0,x0.
 */
be_u64 be_r3_arch_install_management(be_u64 hgatp);

/**
 * be_r3_arch_enter_management - clear guest GPRs and execute initial SRET
 * @entry: exact HS sepc target, management GPA 0x40010000
 * @guest_sp: exact management guest stack top
 * @trusted_sp: exact management trusted HS stack top retained in sscratch
 */
void be_r3_arch_enter_management(be_u64 entry, be_u64 guest_sp,
				 be_u64 trusted_sp)
	__attribute__((noreturn));

/** be_r3_arch_halt - disable bounded interrupt paths and halt fail closed. */
void be_r3_arch_halt(void) __attribute__((noreturn));

/**
 * be_r3_platform_get_spec_version - query the pinned SBI Base version
 * @value: version output on success
 *
 * Return: signed SBI error.
 */
long be_r3_platform_get_spec_version(be_u64 *value);

/**
 * be_r3_platform_probe_extension - query one required SBI extension
 * @eid: extension identifier to probe
 * @value: probe result on success
 *
 * Return: signed SBI error.
 */
long be_r3_platform_probe_extension(be_u64 eid, be_u64 *value);

/**
 * be_r3_platform_write - emit one bounded trusted diagnostic through DBCN
 * @text: trusted HS string bytes
 * @length: exact byte count, bounded to the diagnostic page
 *
 * Return: %BE_R3_ERROR_NONE on complete progress, otherwise exact DBCN error.
 */
enum be_r3_error
be_r3_platform_write(const char *text, be_u64 length);

/**
 * be_r3_platform_reset - request the only allowed SRST shutdown
 *
 * A conforming successful call does not return.
 *
 * Return: exact SRST failure when firmware returns.
 */
enum be_r3_error be_r3_platform_reset(void);

/**
 * be_r3_text_length - bounded length of one trusted constant diagnostic
 * @text: non-NULL trusted string
 *
 * Return: length up to one diagnostic page, or the page size plus one when
 *         no terminator exists inside the bound.
 */
be_u64 be_r3_text_length(const char *text);

/**
 * memcpy - freestanding byte copy used by compiler-lowered struct copies
 * @destination: writable destination
 * @source: readable source
 * @count: exact byte count
 *
 * Return: @destination.
 */
void *memcpy(void *destination, const void *source, be_size count);

/**
 * memset - freestanding byte fill used by compiler-lowered initialization
 * @destination: writable destination
 * @value: low byte is repeated
 * @count: exact byte count
 *
 * Return: @destination.
 */
void *memset(void *destination, int value, be_size count);

extern be_u8 __be_monitor_code_start[];
extern be_u8 __be_monitor_code_end[];
extern be_u8 __be_monitor_data_start[];
extern be_u8 __be_monitor_data_end[];
extern be_u8 __be_input_start[];
extern be_u8 __be_input_end[];
extern be_u8 __be_bss_start[];
extern be_u8 __be_bss_end[];
extern be_u8 __be_diagnostic_start[];
extern be_u8 __be_diagnostic_end[];
extern be_u8 __be_root_management_start[];
extern be_u8 __be_root_management_end[];
extern be_u8 __be_root_protected_start[];
extern be_u8 __be_root_protected_end[];
extern be_u8 __be_stack_management_start[];
extern be_u8 __be_stack_management_end[];
extern be_u8 __be_stack_protected_start[];
extern be_u8 __be_stack_protected_end[];
extern be_u8 __be_saved_management_start[];
extern be_u8 __be_saved_management_end[];
extern be_u8 __be_saved_protected_start[];
extern be_u8 __be_saved_protected_end[];
extern be_u8 __be_private_management_start[];
extern be_u8 __be_private_management_end[];
extern be_u8 __be_private_protected_start[];
extern be_u8 __be_private_protected_end[];
extern be_u8 __be_shared_start[];
extern be_u8 __be_shared_end[];
extern be_u8 __be_guest_management_start[];
extern be_u8 __be_guest_management_end[];
extern be_u8 __be_guest_protected_start[];
extern be_u8 __be_guest_protected_end[];
extern be_u8 be_reset[];
extern be_u8 be_r3_unexpected_trap[];

#endif
