// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host unit and adversarial coverage for R3 boot validation,
 *          accepted R1/R2 composition, HS-state checks, binding publication,
 *          terminal failure, and every host-testable bounded DBCN path.
 * Trust:   host evidence only. It executes no privileged instruction and
 *          supplies no Beryllium QEMU or hardware evidence.
 * Scope:   R3 only; no trap, context, switching, protected entry, or access
 *          isolation fixtures.
 */
#include <stdio.h>
#include <stdlib.h>

#include <be/r1-config.h>
#include <be/r3.h>

#include "../../arch/riscv/be/r0-layout.h"
#include "../../arch/riscv/be/r0-sbi.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			puts("BE_R3_CHECK: assertion failed: " #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

struct r3_fixture {
	struct be_runtime runtime;
	struct be_r2_output r2;
	struct be_r2_leaf_set leaves[BE_MAX_ROOTS];
	struct be_r3_boot_contract boot;
	struct be_r3_hs_state hs;
	struct be_r3_binding binding;
};

static void print_count(const char *label, unsigned long value)
{
	char digits[32];
	unsigned long count = 0U;

	fputs(label, stdout);
	do {
		digits[count] = (char)('0' + (value % 10U));
		value /= 10U;
		++count;
	} while (value != 0U);
	while (count != 0U) {
		--count;
		(void)putchar((int)digits[count]);
	}
	(void)putchar('\n');
}

static be_u8 management_pool[BE_SV39X4_POOL_SIZE]
	__attribute__((aligned(16384)));
static be_u8 protected_pool[BE_SV39X4_POOL_SIZE]
	__attribute__((aligned(16384)));

static struct be_r3_image_layout valid_layout(void)
{
	return (struct be_r3_image_layout) {
		.entry = BE_R0_IMAGE_ENTRY,
		.monitor_code_start = BE_R0_PA_MONITOR_CODE,
		.monitor_code_end = BE_U64_C(0x80204000),
		.monitor_data_start = BE_R0_PA_MONITOR_DATA,
		.monitor_data_end = BE_R3_DIAGNOSTIC_END,
		.input_start = BE_R0_PA_MONITOR_DATA,
		.input_end = BE_U64_C(0x80209000),
		.bss_start = BE_U64_C(0x8020a000),
		.bss_end = BE_U64_C(0x8020e000),
		.diagnostic_start = BE_R3_DIAGNOSTIC_BASE,
		.diagnostic_end = BE_R3_DIAGNOSTIC_END,
		.root_management_start = BE_R0_PA_ROOT_POOL_MANAGEMENT,
		.root_management_end = BE_U64_C(0x8021c000),
		.root_protected_start = BE_R0_PA_ROOT_POOL_PROTECTED,
		.root_protected_end = BE_U64_C(0x80224000),
		.stack_management_start = BE_R0_PA_STACK_MANAGEMENT,
		.stack_management_end = BE_R3_INITIAL_TRUSTED_SP,
		.stack_protected_start = BE_R0_PA_STACK_PROTECTED,
		.stack_protected_end = BE_U64_C(0x8022a000),
		.saved_management_start = BE_R0_PA_SAVED_MANAGEMENT,
		.saved_management_end = BE_U64_C(0x8022c000),
		.saved_protected_start = BE_R0_PA_SAVED_PROTECTED,
		.saved_protected_end = BE_U64_C(0x8022d000),
		.private_management_start = BE_R0_PA_PRIVATE_MANAGEMENT,
		.private_management_end = BE_U64_C(0x8022f000),
		.private_protected_start = BE_R0_PA_PRIVATE_PROTECTED,
		.private_protected_end = BE_U64_C(0x80230000),
		.shared_start = BE_R0_PA_SHARED,
		.shared_end = BE_U64_C(0x80231000),
		.guest_management_start = BE_R0_PA_GUEST_CODE_MANAGEMENT,
		.guest_management_end = BE_U64_C(0x80233000),
		.guest_protected_start = BE_R0_PA_GUEST_CODE_PROTECTED,
		.guest_protected_end = BE_U64_C(0x80234000),
		.trap_vector = BE_U64_C(0x80200100),
	};
}

static struct be_r3_boot_contract valid_boot(void)
{
	return (struct be_r3_boot_contract) {
		.entry = BE_R0_IMAGE_ENTRY,
		.hart_id = 0U,
		.firmware_pointer = BE_U64_C(0x87e00000),
		.sbi_spec_version = BE_R3_OPENSBI_SPEC_VERSION,
		.dbcn_probe = BE_R3_SBI_PROBE_AVAILABLE,
		.srst_probe = BE_R3_SBI_PROBE_AVAILABLE,
		.layout = valid_layout(),
	};
}

static struct be_r3_hs_state valid_hs(void)
{
	struct be_r3_hs_state hs = { 0 };

	hs.stvec = BE_U64_C(0x80200100);
	hs.hstatus = BE_R3_HSTATUS_CONTROL_VALUE;
	return hs;
}

static struct be_r3_binding valid_binding(void)
{
	return (struct be_r3_binding) {
		.domain = BE_DOMAIN_MANAGEMENT,
		.vcpu_id = 1U,
		.root_id = 101U,
		.vmid = 0U,
		.hgatp = BE_R3_MANAGEMENT_HGATP,
		.guest_pc = BE_R3_INITIAL_GUEST_PC,
		.guest_sp = BE_R3_INITIAL_GUEST_SP,
		.trusted_sp = BE_R3_INITIAL_TRUSTED_SP,
		.saved_state_id = 1U,
		.saved_state_pa = BE_R3_MANAGEMENT_SAVED_PA,
		.vsatp = 0U,
		.published = 0U,
	};
}

static void build_r1(struct be_runtime *runtime)
{
	*runtime = (struct be_runtime)BE_RUNTIME_INITIALIZER;
	CHECK(be_runtime_copy_inventory(runtime, be_r1_inventory()) ==
	      BE_RUNTIME_OK);
	CHECK(be_runtime_copy_proposal(runtime, be_r1_proposal()) ==
	      BE_RUNTIME_OK);
	CHECK(be_runtime_validate(runtime) == BE_RUNTIME_OK);
	CHECK(be_runtime_seal(runtime) == BE_RUNTIME_OK);
	CHECK(be_runtime_derive(runtime) == BE_RUNTIME_OK);
}

static void build_r2(struct be_runtime *runtime,
		     struct be_r2_output *output,
		     struct be_r2_leaf_set leaves[BE_MAX_ROOTS])
{
	struct be_r2_pool_desc pools[BE_MAX_ROOTS] = {
		{
			.base = BE_R0_PA_ROOT_POOL_MANAGEMENT,
			.buf = management_pool,
			.buf_size = BE_SV39X4_POOL_SIZE,
		},
		{
			.base = BE_R0_PA_ROOT_POOL_PROTECTED,
			.buf = protected_pool,
			.buf_size = BE_SV39X4_POOL_SIZE,
		},
	};

	*output = (struct be_r2_output){ 0 };
	CHECK(be_r2_build(runtime, pools, output) == BE_CHECK_OK);
	CHECK(be_r2_walk_and_check(runtime, pools, output, leaves) ==
	      BE_CHECK_OK);
}

static struct r3_fixture valid_fixture(void)
{
	struct r3_fixture fixture = { 0 };

	build_r1(&fixture.runtime);
	build_r2(&fixture.runtime, &fixture.r2, fixture.leaves);
	fixture.boot = valid_boot();
	fixture.hs = valid_hs();
	fixture.binding = valid_binding();
	return fixture;
}

static void advance_to_r1(struct be_r3_state *state,
			  const struct r3_fixture *fixture)
{
	*state = (struct be_r3_state)BE_R3_STATE_INITIALIZER;
	CHECK(be_r3_validate_boot(state, &fixture->boot) ==
	      BE_R3_ERROR_NONE);
	CHECK(be_r3_note_r1_derived(state, &fixture->runtime) ==
	      BE_R3_ERROR_NONE);
}

static void advance_to_r2(struct be_r3_state *state,
			  const struct r3_fixture *fixture)
{
	advance_to_r1(state, fixture);
	CHECK(be_r3_note_r2_built(state, &fixture->runtime, &fixture->r2,
				  fixture->leaves) == BE_R3_ERROR_NONE);
}

static void advance_to_hs(struct be_r3_state *state,
			  const struct r3_fixture *fixture)
{
	advance_to_r2(state, fixture);
	CHECK(be_r3_note_hs_ready(state, &fixture->hs,
				  &fixture->boot.layout) ==
	      BE_R3_ERROR_NONE);
}

static void advance_to_prepared(struct be_r3_state *state,
				const struct r3_fixture *fixture)
{
	advance_to_hs(state, fixture);
	CHECK(be_r3_prepare_management_binding(state, &fixture->binding) ==
	      BE_R3_ERROR_NONE);
}

static void test_positive_flow(void)
{
	struct r3_fixture fixture = valid_fixture();
	struct be_r3_state state = BE_R3_STATE_INITIALIZER;
	struct be_r3_binding active;

	SCENARIO();
	CHECK(be_r3_validate_boot(&state, &fixture.boot) ==
	      BE_R3_ERROR_NONE);
	CHECK(state.phase == BE_R3_PHASE_BOOT_VALIDATED);
	CHECK(state.firmware_pointer == fixture.boot.firmware_pointer);
	CHECK(be_r3_note_r1_derived(&state, &fixture.runtime) ==
	      BE_R3_ERROR_NONE);
	CHECK(be_r3_note_r2_built(&state, &fixture.runtime, &fixture.r2,
				  fixture.leaves) == BE_R3_ERROR_NONE);
	CHECK(be_r3_note_hs_ready(&state, &fixture.hs,
				  &fixture.boot.layout) ==
	      BE_R3_ERROR_NONE);
	CHECK(be_r3_prepare_management_binding(&state, &fixture.binding) ==
	      BE_R3_ERROR_NONE);
	CHECK(be_r3_publish_management_binding(
		      &state, BE_R3_MANAGEMENT_HGATP, 1U) ==
	      BE_R3_ERROR_NONE);
	active = state.active;
	CHECK(active.published == 1U);
	CHECK(be_r3_arm_management_entry(&state, &active) ==
	      BE_R3_ERROR_NONE);
	CHECK(state.phase == BE_R3_PHASE_ENTRY_ARMED);
	CHECK(state.error == BE_R3_ERROR_NONE);
}

static void test_boot_failures(void)
{
	struct be_r3_boot_contract boot = valid_boot();
	struct be_r3_state state = BE_R3_STATE_INITIALIZER;
	struct be_r3_image_layout *layout = &boot.layout;

	SCENARIO();
	CHECK(be_r3_validate_boot((struct be_r3_state *)0, &boot) ==
	      BE_R3_ERROR_NULL);
	CHECK(be_r3_validate_boot(&state,
				 (const struct be_r3_boot_contract *)0) ==
	      BE_R3_ERROR_NULL);
	CHECK(state.phase == BE_R3_PHASE_FAILED);
	CHECK(be_r3_validate_boot(&state, &boot) == BE_R3_ERROR_NULL);

#define EXPECT_BOOT_ERROR(field, value, expected) \
	do { \
		boot = valid_boot(); \
		state = (struct be_r3_state)BE_R3_STATE_INITIALIZER; \
		boot.field = (value); \
		SCENARIO(); \
		CHECK(be_r3_validate_boot(&state, &boot) == (expected)); \
		CHECK(state.phase == BE_R3_PHASE_FAILED); \
	} while (0)

	EXPECT_BOOT_ERROR(entry, BE_R0_IMAGE_ENTRY + 4U,
			  BE_R3_ERROR_HANDOFF);
	EXPECT_BOOT_ERROR(hart_id, 1U, BE_R3_ERROR_HANDOFF);
	EXPECT_BOOT_ERROR(sbi_spec_version,
			  BE_R3_OPENSBI_SPEC_VERSION - 1U,
			  BE_R3_ERROR_SBI_SPEC);
	EXPECT_BOOT_ERROR(dbcn_probe, 0U, BE_R3_ERROR_SBI_DBCN_PROBE);
	EXPECT_BOOT_ERROR(srst_probe, 0U, BE_R3_ERROR_SBI_SRST_PROBE);

#define EXPECT_LAYOUT_ERROR(field, value) \
	do { \
		boot = valid_boot(); \
		state = (struct be_r3_state)BE_R3_STATE_INITIALIZER; \
		boot.layout.field = (value); \
		SCENARIO(); \
		CHECK(be_r3_validate_boot(&state, &boot) == \
		      BE_R3_ERROR_IMAGE_LAYOUT); \
	} while (0)

	EXPECT_LAYOUT_ERROR(entry, BE_R0_IMAGE_ENTRY + 4U);
	EXPECT_LAYOUT_ERROR(monitor_code_start, BE_R0_PA_MONITOR_CODE + 4U);
	EXPECT_LAYOUT_ERROR(monitor_code_end, BE_U64_C(0x80208001));
	EXPECT_LAYOUT_ERROR(monitor_data_start, BE_R0_PA_MONITOR_DATA + 4U);
	EXPECT_LAYOUT_ERROR(monitor_data_end, BE_R3_DIAGNOSTIC_END + 1U);
	EXPECT_LAYOUT_ERROR(input_start, BE_U64_C(0x80207000));
	EXPECT_LAYOUT_ERROR(input_end, BE_U64_C(0x80210001));
	EXPECT_LAYOUT_ERROR(bss_start, BE_U64_C(0x80207000));
	EXPECT_LAYOUT_ERROR(bss_end, BE_R3_DIAGNOSTIC_BASE + 1U);
	EXPECT_LAYOUT_ERROR(diagnostic_start, BE_R3_DIAGNOSTIC_BASE + 1U);
	EXPECT_LAYOUT_ERROR(diagnostic_end, BE_R3_DIAGNOSTIC_END - 1U);
	EXPECT_LAYOUT_ERROR(root_management_start,
			    BE_R0_PA_ROOT_POOL_MANAGEMENT + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(root_management_end, BE_U64_C(0x8021b000));
	EXPECT_LAYOUT_ERROR(root_protected_start,
			    BE_R0_PA_ROOT_POOL_PROTECTED + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(root_protected_end, BE_U64_C(0x80223000));
	EXPECT_LAYOUT_ERROR(stack_management_start,
			    BE_R0_PA_STACK_MANAGEMENT + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(stack_management_end,
			    BE_R3_INITIAL_TRUSTED_SP - BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(stack_protected_start,
			    BE_R0_PA_STACK_PROTECTED + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(stack_protected_end, BE_U64_C(0x80229000));
	EXPECT_LAYOUT_ERROR(saved_management_start,
			    BE_R0_PA_SAVED_MANAGEMENT + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(saved_management_end, BE_U64_C(0x8022b000));
	EXPECT_LAYOUT_ERROR(saved_protected_start,
			    BE_R0_PA_SAVED_PROTECTED + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(saved_protected_end, BE_U64_C(0x8022c000));
	EXPECT_LAYOUT_ERROR(private_management_start,
			    BE_R0_PA_PRIVATE_MANAGEMENT + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(private_management_end, BE_U64_C(0x8022e000));
	EXPECT_LAYOUT_ERROR(private_protected_start,
			    BE_R0_PA_PRIVATE_PROTECTED + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(private_protected_end, BE_U64_C(0x8022f000));
	EXPECT_LAYOUT_ERROR(shared_start, BE_R0_PA_SHARED + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(shared_end, BE_U64_C(0x80230000));
	EXPECT_LAYOUT_ERROR(guest_management_start,
			    BE_R0_PA_GUEST_CODE_MANAGEMENT + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(guest_management_end, BE_U64_C(0x80232000));
	EXPECT_LAYOUT_ERROR(guest_protected_start,
			    BE_R0_PA_GUEST_CODE_PROTECTED + BE_PAGE_SIZE);
	EXPECT_LAYOUT_ERROR(guest_protected_end, BE_U64_C(0x80233000));
	EXPECT_LAYOUT_ERROR(trap_vector, BE_U64_C(0x80208000));
	EXPECT_LAYOUT_ERROR(trap_vector, BE_U64_C(0x80200102));

	boot = valid_boot();
	state = (struct be_r3_state)BE_R3_STATE_INITIALIZER;
	layout = &boot.layout;
	layout->input_end = layout->input_start - 1U;
	SCENARIO();
	CHECK(be_r3_validate_boot(&state, &boot) ==
	      BE_R3_ERROR_IMAGE_LAYOUT);

#undef EXPECT_BOOT_ERROR
#undef EXPECT_LAYOUT_ERROR
}

static void test_r1_r2_failures(void)
{
	struct r3_fixture fixture = valid_fixture();
	struct be_r3_state state;
	struct be_runtime runtime;
	struct be_r2_output output;
	struct be_r2_leaf_set leaves[BE_MAX_ROOTS];

	SCENARIO();
	state = (struct be_r3_state)BE_R3_STATE_INITIALIZER;
	CHECK(be_r3_note_r1_derived(&state, &fixture.runtime) ==
	      BE_R3_ERROR_INVALID_PHASE);

	runtime = fixture.runtime;
	runtime.phase = BE_RUNTIME_PHASE_SEALED;
	state = (struct be_r3_state)BE_R3_STATE_INITIALIZER;
	CHECK(be_r3_validate_boot(&state, &fixture.boot) ==
	      BE_R3_ERROR_NONE);
	SCENARIO();
	CHECK(be_r3_note_r1_derived(&state, &runtime) ==
	      BE_R3_ERROR_R1_STATE);

	advance_to_r1(&state, &fixture);
	output = fixture.r2;
	output.state = BE_R2_STATE_FAILED;
	SCENARIO();
	CHECK(be_r3_note_r2_built(&state, &fixture.runtime, &output,
				  fixture.leaves) ==
	      BE_R3_ERROR_R2_STATE);

	advance_to_r1(&state, &fixture);
	output = fixture.r2;
	output.results[0].hgatp ^= 1U;
	SCENARIO();
	CHECK(be_r3_note_r2_built(&state, &fixture.runtime, &output,
				  fixture.leaves) ==
	      BE_R3_ERROR_R2_STATE);

	advance_to_r1(&state, &fixture);
	output = fixture.r2;
	output.results[1].hgatp ^= 1U;
	SCENARIO();
	CHECK(be_r3_note_r2_built(&state, &fixture.runtime, &output,
				  fixture.leaves) ==
	      BE_R3_ERROR_R2_STATE);

	runtime = fixture.runtime;
	runtime.enforcement.roots[0].domain = BE_DOMAIN_PROTECTED;
	advance_to_r1(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_note_r2_built(&state, &runtime, &fixture.r2,
				  fixture.leaves) ==
	      BE_R3_ERROR_R2_STATE);

	runtime = fixture.runtime;
	runtime.enforcement.roots[0].root_id = 102U;
	advance_to_r1(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_note_r2_built(&state, &runtime, &fixture.r2,
				  fixture.leaves) ==
	      BE_R3_ERROR_R2_STATE);

	runtime = fixture.runtime;
	runtime.enforcement.roots[0].vmid = 1U;
	advance_to_r1(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_note_r2_built(&state, &runtime, &fixture.r2,
				  fixture.leaves) ==
	      BE_R3_ERROR_R2_STATE);

	leaves[0] = fixture.leaves[0];
	leaves[1] = fixture.leaves[1];
	leaves[0].leaves[0].gpa ^= BE_PAGE_SIZE;
	advance_to_r1(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_note_r2_built(&state, &fixture.runtime, &fixture.r2,
				  leaves) == BE_R3_ERROR_R2_STATE);

	advance_to_r1(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_note_r2_built(&state,
				  (const struct be_runtime *)0,
				  &fixture.r2, fixture.leaves) ==
	      BE_R3_ERROR_NULL);
}

static void test_hs_failures(void)
{
	struct r3_fixture fixture = valid_fixture();
	struct be_r3_state state;
	struct be_r3_hs_state hs;
	be_u64 *fields;
	be_size index;

	advance_to_r2(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_note_hs_ready(&state,
				  (const struct be_r3_hs_state *)0,
				  &fixture.boot.layout) == BE_R3_ERROR_NULL);

	/*
	 * Every field other than hstatus/stvec is required zero. Mutate each
	 * independently so the accepted register matrix is covered directly.
	 */
	for (index = 0U;
	     index < sizeof(struct be_r3_hs_state) / sizeof(be_u64);
	     ++index) {
		if (index == 2U || index == 11U)
			continue;
		hs = fixture.hs;
		fields = (be_u64 *)&hs;
		fields[index] = (index == 1U || index == 24U) ?
			BE_R3_SSTATUS_SIE : 1U;
		advance_to_r2(&state, &fixture);
		SCENARIO();
		CHECK(be_r3_note_hs_ready(&state, &hs,
					  &fixture.boot.layout) ==
		      BE_R3_ERROR_HS_STATE);
	}

	hs = fixture.hs;
	hs.sstatus = BE_R3_SSTATUS_SPP;
	advance_to_r2(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_note_hs_ready(&state, &hs, &fixture.boot.layout) ==
	      BE_R3_ERROR_HS_STATE);

	hs = fixture.hs;
	hs.hstatus &= ~BE_R3_HSTATUS_VTVM;
	advance_to_r2(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_note_hs_ready(&state, &hs, &fixture.boot.layout) ==
	      BE_R3_ERROR_HS_STATE);

	hs = fixture.hs;
	hs.hstatus |= BE_R3_HSTATUS_HU;
	advance_to_r2(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_note_hs_ready(&state, &hs, &fixture.boot.layout) ==
	      BE_R3_ERROR_HS_STATE);

	hs = fixture.hs;
	hs.stvec += 4U;
	advance_to_r2(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_note_hs_ready(&state, &hs, &fixture.boot.layout) ==
	      BE_R3_ERROR_HS_STATE);
}

static void test_binding_failures(void)
{
	struct r3_fixture fixture = valid_fixture();
	struct be_r3_state state;
	struct be_r3_binding binding;

#define EXPECT_BINDING_ERROR(field, value) \
	do { \
		advance_to_hs(&state, &fixture); \
		binding = fixture.binding; \
		binding.field = (value); \
		SCENARIO(); \
		CHECK(be_r3_prepare_management_binding(&state, &binding) == \
		      BE_R3_ERROR_BINDING); \
		CHECK(state.phase == BE_R3_PHASE_FAILED); \
	} while (0)

	EXPECT_BINDING_ERROR(domain, BE_DOMAIN_PROTECTED);
	EXPECT_BINDING_ERROR(vcpu_id, 2U);
	EXPECT_BINDING_ERROR(root_id, 102U);
	EXPECT_BINDING_ERROR(vmid, 1U);
	EXPECT_BINDING_ERROR(hgatp, BE_R3_PROTECTED_HGATP);
	EXPECT_BINDING_ERROR(guest_pc, BE_R3_INITIAL_GUEST_PC + 4U);
	EXPECT_BINDING_ERROR(guest_sp, BE_R3_INITIAL_GUEST_SP - 16U);
	EXPECT_BINDING_ERROR(trusted_sp, BE_R3_INITIAL_TRUSTED_SP - 16U);
	EXPECT_BINDING_ERROR(saved_state_id, 2U);
	EXPECT_BINDING_ERROR(saved_state_pa, BE_R0_PA_SAVED_PROTECTED);
	EXPECT_BINDING_ERROR(vsatp, BE_U64_C(1) << 60);
	EXPECT_BINDING_ERROR(published, 1U);

#undef EXPECT_BINDING_ERROR

	advance_to_prepared(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_publish_management_binding(
		      &state, BE_R3_PROTECTED_HGATP, 1U) ==
	      BE_R3_ERROR_PUBLICATION);

	advance_to_prepared(&state, &fixture);
	SCENARIO();
	CHECK(be_r3_publish_management_binding(
		      &state, BE_R3_MANAGEMENT_HGATP, 0U) ==
	      BE_R3_ERROR_PUBLICATION);

	advance_to_prepared(&state, &fixture);
	state.pending.published = 1U;
	SCENARIO();
	CHECK(be_r3_publish_management_binding(
		      &state, BE_R3_MANAGEMENT_HGATP, 1U) ==
	      BE_R3_ERROR_PUBLICATION);

	advance_to_prepared(&state, &fixture);
	state.active = fixture.binding;
	state.active.published = 1U;
	SCENARIO();
	CHECK(be_r3_publish_management_binding(
		      &state, BE_R3_MANAGEMENT_HGATP, 1U) ==
	      BE_R3_ERROR_PUBLICATION);

	advance_to_prepared(&state, &fixture);
	CHECK(be_r3_publish_management_binding(
		      &state, BE_R3_MANAGEMENT_HGATP, 1U) ==
	      BE_R3_ERROR_NONE);
	binding = state.active;
	binding.guest_pc += 4U;
	SCENARIO();
	CHECK(be_r3_arm_management_entry(&state, &binding) ==
	      BE_R3_ERROR_BINDING);

	advance_to_prepared(&state, &fixture);
	CHECK(be_r3_publish_management_binding(
		      &state, BE_R3_MANAGEMENT_HGATP, 1U) ==
	      BE_R3_ERROR_NONE);
	state.active.published = 0U;
	SCENARIO();
	CHECK(be_r3_arm_management_entry(&state, &state.active) ==
	      BE_R3_ERROR_BINDING);
}

static void test_terminal_failure(void)
{
	struct r3_fixture fixture = valid_fixture();
	struct be_r3_state state = BE_R3_STATE_INITIALIZER;
	enum be_r3_error error;

	SCENARIO();
	error = be_r3_fail(&state, BE_R3_ERROR_IMAGE_LAYOUT);
	CHECK(error == BE_R3_ERROR_IMAGE_LAYOUT);
	CHECK(state.phase == BE_R3_PHASE_FAILED);
	CHECK(state.error == BE_R3_ERROR_IMAGE_LAYOUT);
	CHECK(be_r3_validate_boot(&state, &fixture.boot) ==
	      BE_R3_ERROR_IMAGE_LAYOUT);
	CHECK(be_r3_note_r1_derived(&state, &fixture.runtime) ==
	      BE_R3_ERROR_IMAGE_LAYOUT);
	CHECK(be_r3_prepare_management_binding(&state, &fixture.binding) ==
	      BE_R3_ERROR_IMAGE_LAYOUT);
	CHECK(be_r3_fail(&state, BE_R3_ERROR_NONE) ==
	      BE_R3_ERROR_IMAGE_LAYOUT);
	CHECK(state.error == BE_R3_ERROR_IMAGE_LAYOUT);
}

static void test_dbcn(void)
{
	struct be_r3_dbcn_progress progress;
	enum be_r3_error errors[] = {
		BE_R3_ERROR_DBCN_FAILED,
		BE_R3_ERROR_DBCN_NOT_SUPPORTED,
		BE_R3_ERROR_DBCN_INVALID_PARAM,
		BE_R3_ERROR_DBCN_DENIED,
		BE_R3_ERROR_DBCN_INVALID_ADDRESS,
	};
	long sbi_errors[] = {
		BE_R0_SBI_ERR_FAILED,
		BE_R0_SBI_ERR_NOT_SUPPORTED,
		BE_R0_SBI_ERR_INVALID_PARAM,
		BE_R0_SBI_ERR_DENIED,
		BE_R0_SBI_ERR_INVALID_ADDRESS,
	};
	be_size index;
	be_u32 iteration;

	SCENARIO();
	CHECK(be_r3_dbcn_begin((struct be_r3_dbcn_progress *)0,
			      BE_R3_DIAGNOSTIC_BASE, 1U) ==
	      BE_R3_ERROR_NULL);

	progress = (struct be_r3_dbcn_progress)BE_R3_DBCN_INITIALIZER;
	SCENARIO();
	CHECK(be_r3_dbcn_begin(&progress, BE_R3_DIAGNOSTIC_BASE, 0U) ==
	      BE_R3_ERROR_NONE);
	CHECK(progress.state == BE_R3_DBCN_COMPLETE);

	progress = (struct be_r3_dbcn_progress)BE_R3_DBCN_INITIALIZER;
	CHECK(be_r3_dbcn_begin(&progress, BE_R3_DIAGNOSTIC_BASE, 9U) ==
	      BE_R3_ERROR_NONE);
	SCENARIO();
	CHECK(be_r3_dbcn_consume(&progress, BE_R0_SBI_SUCCESS, 3U) ==
	      BE_R3_ERROR_NONE);
	CHECK(progress.offset == 3U);
	CHECK(be_r3_dbcn_consume(&progress, BE_R0_SBI_SUCCESS, 0U) ==
	      BE_R3_ERROR_NONE);
	CHECK(progress.offset == 3U);
	CHECK(be_r3_dbcn_consume(&progress, BE_R0_SBI_SUCCESS, 6U) ==
	      BE_R3_ERROR_NONE);
	CHECK(progress.state == BE_R3_DBCN_COMPLETE);
	CHECK(progress.iterations == 3U);

#define EXPECT_DBCN_RANGE(base_value, length_value) \
	do { \
		progress = (struct be_r3_dbcn_progress) \
			BE_R3_DBCN_INITIALIZER; \
		SCENARIO(); \
		CHECK(be_r3_dbcn_begin(&progress, (base_value), \
					 (length_value)) == \
		      BE_R3_ERROR_DBCN_RANGE); \
		CHECK(progress.state == BE_R3_DBCN_FAILED); \
	} while (0)

	EXPECT_DBCN_RANGE(BE_R3_DIAGNOSTIC_BASE - 1U, 1U);
	EXPECT_DBCN_RANGE(BE_R3_DIAGNOSTIC_END, 1U);
	EXPECT_DBCN_RANGE(BE_R3_DIAGNOSTIC_BASE, BE_PAGE_SIZE + 1U);
	EXPECT_DBCN_RANGE(BE_R3_DIAGNOSTIC_END - 1U, 2U);
	EXPECT_DBCN_RANGE(~BE_U64_C(0) - 1U, 4U);

#undef EXPECT_DBCN_RANGE

	for (index = 0U; index < BE_ARRAY_SIZE(errors); ++index) {
		progress = (struct be_r3_dbcn_progress)
			BE_R3_DBCN_INITIALIZER;
		CHECK(be_r3_dbcn_begin(&progress,
				      BE_R3_DIAGNOSTIC_BASE, 1U) ==
		      BE_R3_ERROR_NONE);
		SCENARIO();
		CHECK(be_r3_dbcn_consume(&progress, sbi_errors[index], 0U) ==
		      errors[index]);
		CHECK(progress.error == errors[index]);
		CHECK(be_r3_dbcn_consume(&progress, BE_R0_SBI_SUCCESS, 1U) ==
		      errors[index]);
	}

	progress = (struct be_r3_dbcn_progress)BE_R3_DBCN_INITIALIZER;
	CHECK(be_r3_dbcn_begin(&progress, BE_R3_DIAGNOSTIC_BASE, 1U) ==
	      BE_R3_ERROR_NONE);
	SCENARIO();
	CHECK(be_r3_dbcn_consume(&progress, -99L, 0U) ==
	      BE_R3_ERROR_DBCN_MALFORMED);

	progress = (struct be_r3_dbcn_progress)BE_R3_DBCN_INITIALIZER;
	CHECK(be_r3_dbcn_begin(&progress, BE_R3_DIAGNOSTIC_BASE, 1U) ==
	      BE_R3_ERROR_NONE);
	SCENARIO();
	CHECK(be_r3_dbcn_consume(&progress, BE_R0_SBI_SUCCESS, 2U) ==
	      BE_R3_ERROR_DBCN_MALFORMED);

	progress = (struct be_r3_dbcn_progress)BE_R3_DBCN_INITIALIZER;
	CHECK(be_r3_dbcn_begin(&progress, BE_R3_DIAGNOSTIC_BASE, 1U) ==
	      BE_R3_ERROR_NONE);
	SCENARIO();
	for (iteration = 0U;
	     iteration < BE_R3_DBCN_MAX_ITERATIONS - 1U;
	     ++iteration)
		CHECK(be_r3_dbcn_consume(&progress,
					 BE_R0_SBI_SUCCESS, 0U) ==
		      BE_R3_ERROR_NONE);
	CHECK(be_r3_dbcn_consume(&progress, BE_R0_SBI_SUCCESS, 0U) ==
	      BE_R3_ERROR_DBCN_RETRY_EXHAUSTED);
	CHECK(progress.iterations == BE_R3_DBCN_MAX_ITERATIONS);

	progress = (struct be_r3_dbcn_progress)BE_R3_DBCN_INITIALIZER;
	SCENARIO();
	CHECK(be_r3_dbcn_consume(&progress, BE_R0_SBI_SUCCESS, 0U) ==
	      BE_R3_ERROR_INVALID_PHASE);

	progress = (struct be_r3_dbcn_progress)BE_R3_DBCN_INITIALIZER;
	CHECK(be_r3_dbcn_begin(&progress, BE_R3_DIAGNOSTIC_BASE, 1U) ==
	      BE_R3_ERROR_NONE);
	SCENARIO();
	CHECK(be_r3_dbcn_begin(&progress, BE_R3_DIAGNOSTIC_BASE, 1U) ==
	      BE_R3_ERROR_INVALID_PHASE);
}

static void test_names(void)
{
	SCENARIO();
	CHECK(be_r3_phase_name(BE_R3_PHASE_ENTRY_ARMED)[0] == 'e');
	CHECK(be_r3_phase_name((enum be_r3_phase)99)[0] == 'i');
	CHECK(be_r3_error_name(BE_R3_ERROR_DBCN_INVALID_ADDRESS)[0] == 'd');
	CHECK(be_r3_error_name(BE_R3_ERROR_SRST_NOT_SUPPORTED)[0] == 's');
	CHECK(be_r3_error_name((enum be_r3_error)99)[0] == 'i');
}

static void test_srst(void)
{
	SCENARIO();
	CHECK(be_r3_srst_result(BE_R0_SBI_SUCCESS) ==
	      BE_R3_ERROR_SRST_RETURNED);
	CHECK(be_r3_srst_result(BE_R0_SBI_ERR_FAILED) ==
	      BE_R3_ERROR_SRST_FAILED);
	CHECK(be_r3_srst_result(BE_R0_SBI_ERR_NOT_SUPPORTED) ==
	      BE_R3_ERROR_SRST_NOT_SUPPORTED);
	CHECK(be_r3_srst_result(BE_R0_SBI_ERR_INVALID_PARAM) ==
	      BE_R3_ERROR_SRST_INVALID_PARAM);
	CHECK(be_r3_srst_result(BE_R0_SBI_ERR_DENIED) ==
	      BE_R3_ERROR_SRST_DENIED);
	CHECK(be_r3_srst_result(BE_R0_SBI_ERR_INVALID_ADDRESS) ==
	      BE_R3_ERROR_SRST_INVALID_ADDRESS);
	CHECK(be_r3_srst_result(-99L) == BE_R3_ERROR_SRST_MALFORMED);
}

int main(void)
{
	test_positive_flow();
	test_boot_failures();
	test_r1_r2_failures();
	test_hs_failures();
	test_binding_failures();
	test_terminal_failure();
	test_dbcn();
	test_srst();
	test_names();

	puts("BE_R3_CHECK: PASS");
	print_count("BE_R3_CHECK: scenarios=", scenarios);
	print_count("BE_R3_CHECK: assertions=", assertions);
	if (scenarios < 100U || assertions < 650U) {
		puts("BE_R3_CHECK: coverage counters below required floor");
		return 1;
	}
	return 0;
}
