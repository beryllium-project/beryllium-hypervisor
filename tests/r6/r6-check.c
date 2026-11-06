// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the seventeen R6 host adversarial fixtures over the accepted
 *          architecture-neutral R5 mechanism, their seventeen paired negative
 *          self-tests, and the host semantic checker with its ledger
 *          mutations.
 * Trust:   host evidence only. No CSR, fence, image, emulator, guest entry, or
 *          hardware behavior is exercised, and no accepted byte is modified.
 *          Every fixture world is built only through the accepted API
 *          sequence, and exactly one argument, or exactly one field of one
 *          otherwise accepted argument, is then malformed.
 * Scope:   R6 host partition (declared layer L11) only. No image, no QEMU, no
 *          production surface, and no R7 content.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <be/r5.h>

/*
 * The two firmware return encodings this driver needs are the architecture
 * neutral facts that SBI reports success as zero and every failure as a
 * negative value. The driver deliberately includes no RISC-V header: the
 * accepted classifier maps zero to "shutdown reported success but returned"
 * and every other value to "firmware rejected the allowlisted shutdown".
 */
#define HOST_SBI_SUCCESS		0L
#define HOST_SBI_FIRST_ERROR		(-1L)
#define HOST_SBI_LAST_ERROR		(-6L)

#define HOST_FIXTURES			17U
#define HOST_MAX_CLASSES		2U
#define HOST_CLASS_OUTCOMES		18U
#define HOST_PRIMARY_CLASSES		17U
#define HOST_SECONDARY_CLASSES		1U
#define HOST_MUTATIONS			8U
#define HOST_CASES			30U
#define HOST_LAYER			"L11"
/*
 * A forged class must never collide with a declared host class, or the
 * duplicate-primary-class rule would mask the comparison the paired self-test
 * is proving. `import` is produced by the accepted mechanism but is claimed by
 * no host fixture.
 */
#define HOST_FORGED_CLASS		"import"
#define HOST_FORGED_LAYER		"L6"

static unsigned long assertions;
static char reason_buffer[128];

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_R6:FAIL host assertion %s:%d: %s\n", \
			       __FILE__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (0)

/* One malformed argument, or one malformed field, per declared case. */
struct host_declaration {
	const char *id;
	const char *call;
	const char *argument;
	const char *field;
	const char *accepted;
	const char *malformed;
	const char *world;
	unsigned int cases;
	unsigned int class_count;
	const char *classes[HOST_MAX_CLASSES];
	const char *roles[HOST_MAX_CLASSES];
};

/*
 * What one malformed call actually produced.  Every member is read back from
 * the accepted mechanism after the call: `world` is the phase the mechanism
 * itself names for the state the call was made against, `observed` is the
 * enumerator the call returned, and `class` is the name the accepted
 * be_r5_error_name() gives that exact enumerator.  Nothing here is copied from
 * a declaration, so a fixture cannot assert one enumerator and publish
 * another.
 */
struct host_case {
	const char *call;
	const char *world;
	const char *class;
	enum be_r5_error observed;
	int sticky;
	int transactional;
};

/* What the driver actually observed for one fixture. */
struct host_result {
	const char *id;
	const char *layer;
	const char *call;
	const char *world;
	unsigned int cases;
	unsigned int class_count;
	const char *classes[HOST_MAX_CLASSES];
	const char *roles[HOST_MAX_CLASSES];
	int sticky;
	int transactional;
	int restored_none;
};

/*
 * BE_R6_HOST_TABLE begin
 *
 * tests/r6/catalogue-host.mjs parses this table and requires it to agree, row
 * for row, with each host fixture manifest under tests/r6/fixtures and with
 * the catalogue rows, so a fixture cannot drift in one place only.
 */
static const struct host_declaration host_declarations[HOST_FIXTURES] = {
	{
		.id = "H-01",
		.call = "be_r5_handle_exit",
		.argument = "state|frame|observation|result",
		.field = "pointer argument",
		.accepted = "non-null",
		.malformed = "NULL",
		.world = "protected-published-expect-load-fault",
		.cases = 4U,
		.class_count = 1U,
		.classes = { "null", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-02",
		.call = "be_r5_handle_exit",
		.argument = "state",
		.field = "pending.direction",
		.accepted = "BE_R5_DIRECTION_NONE",
		.malformed = "BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT",
		.world = "protected-published-expect-load-fault",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "pending", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-03",
		.call = "be_r5_handle_exit",
		.argument = "observation",
		.field = "active.vcpu_id",
		.accepted = "2",
		.malformed = "3",
		.world = "protected-published-expect-load-fault",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "binding", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-04",
		.call = "be_r5_publish_target",
		.argument = "entry",
		.field = "trusted_sp",
		.accepted = "0x8022a000",
		.malformed = "0x80227000",
		.world = "protected-fenced",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "trusted-stack", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-05",
		.call = "be_r5_publish_target",
		.argument = "entry",
		.field = "saved_state_pa",
		.accepted = "0x8022c000",
		.malformed = "0x8022d000",
		.world = "protected-fenced",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "saved-page", 0 },
		.roles = { "secondary", 0 },
	},
	{
		.id = "H-06",
		.call = "be_r5_handle_exit",
		.argument = "observation",
		.field = "hstatus",
		.accepted = "0x700180",
		.malformed = "0x700100",
		.world = "protected-published-expect-load-fault",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "vs-origin", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-07",
		.call = "be_r5_handle_exit",
		.argument = "observation",
		.field = "vsatp",
		.accepted = "0",
		.malformed = "0x8000000000080000",
		.world = "protected-published-expect-load-fault",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "vsatp", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-08",
		.call = "be_r5_handle_exit",
		.argument = "frame",
		.field = "reserved",
		.accepted = "0",
		.malformed = "1",
		.world = "protected-published-expect-load-fault",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "frame-reserved", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-09",
		.call = "be_r5_publish_target",
		.argument = "state",
		.field = "management_frame.gpr[BE_R4_GPR_A1]",
		.accepted = "34",
		.malformed = "35",
		.world = "management-fenced",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "frame-state", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-10",
		.call = "be_r5_publish_target",
		.argument = "entry",
		.field = "vstvec|vsepc|vscause|vstval",
		.accepted = "0",
		.malformed = "0x40011000",
		.world = "protected-fenced",
		.cases = 4U,
		.class_count = 1U,
		.classes = { "target-reset", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-11",
		.call = "be_r5_publish_target",
		.argument = "entry",
		.field = "sstatus|hstatus",
		.accepted = "0x100|0x700180",
		.malformed = "0x0|0x700100",
		.world = "protected-fenced",
		.cases = 2U,
		.class_count = 1U,
		.classes = { "entry-controls", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-12",
		.call = "be_r5_publish_target",
		.argument = "state",
		.field = "switch_count",
		.accepted = "0",
		.malformed = "1",
		.world = "protected-fenced",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "publication", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-13",
		.call = "be_r5_handle_exit",
		.argument = "observation",
		.field = "hart_id",
		.accepted = "0",
		.malformed = "1",
		.world = "protected-published-expect-load-fault",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "hart", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-14",
		.call = "be_r5_handle_exit",
		.argument = "frame",
		.field = "htval",
		.accepted = "0x10000000",
		.malformed = "0x4000000000000000",
		.world = "protected-published-expect-load-fault",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "htval-overflow", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-15",
		.call = "be_r5_handle_exit",
		.argument = "frame",
		.field = "htval",
		.accepted = "0x10000000",
		.malformed = "0x10000c00",
		.world = "protected-published-expect-load-fault",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "gpa", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-16",
		.call = "be_r5_handle_exit",
		.argument = "frame",
		.field = "stval",
		.accepted = "0",
		.malformed = "4",
		.world = "protected-expect-switch-event",
		.cases = 1U,
		.class_count = 1U,
		.classes = { "trap-metadata", 0 },
		.roles = { "primary", 0 },
	},
	{
		.id = "H-17",
		.call = "be_r5_note_shutdown_returned",
		.argument = "sbi_error",
		.field = "returned firmware result",
		.accepted = "never returns",
		.malformed = "0|-1|-2|-3|-4|-5|-6",
		.world = "complete",
		.cases = 7U,
		.class_count = 2U,
		.classes = { "shutdown-returned", "shutdown-rejected" },
		.roles = { "primary", "primary" },
	},
};
/* BE_R6_HOST_TABLE end */

static const struct host_declaration *declaration(const char *id)
{
	unsigned int index;

	for (index = 0U; index < HOST_FIXTURES; ++index) {
		if (strcmp(host_declarations[index].id, id) == 0)
			return &host_declarations[index];
	}
	printf("BE_R6:FAIL host declaration %s is absent\n", id);
	exit(1);
}

static struct be_r3_binding management_binding_value(be_u32 published)
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
		.published = published,
	};
}

static struct be_r3_binding protected_binding_value(be_u32 published)
{
	return (struct be_r3_binding) {
		.domain = BE_DOMAIN_PROTECTED,
		.vcpu_id = BE_R5_PROTECTED_VCPU_ID,
		.root_id = BE_R5_PROTECTED_ROOT_ID,
		.vmid = 0U,
		.hgatp = BE_R3_PROTECTED_HGATP,
		.guest_pc = BE_R5_PROTECTED_ENTRY_PC,
		.guest_sp = BE_R5_PROTECTED_GUEST_SP,
		.trusted_sp = BE_R5_PROTECTED_TRUSTED_SP,
		.saved_state_id = BE_R5_PROTECTED_SAVED_STATE_ID,
		.saved_state_pa = BE_R5_PROTECTED_SAVED_PA,
		.vsatp = 0U,
		.published = published,
	};
}

static int binding_is_zero(const struct be_r3_binding *binding)
{
	struct be_r3_binding zero = { 0 };

	return memcmp(binding, &zero, sizeof(zero)) == 0;
}

/* struct be_r4_frame is exactly forty be_u64 words, so memcmp is exact. */
static int frames_equal(const struct be_r4_frame *left,
			const struct be_r4_frame *right)
{
	return memcmp(left, right, sizeof(*left)) == 0;
}

static int frame_is_zero(const struct be_r4_frame *frame)
{
	struct be_r4_frame zero = { 0 };

	return frames_equal(frame, &zero);
}

static int pending_is_zero(const struct be_r5_pending *pending)
{
	struct be_r5_pending zero = { 0 };

	return memcmp(pending, &zero, sizeof(zero)) == 0;
}

static struct be_r4_state valid_r4(void)
{
	return (struct be_r4_state) {
		.phase = BE_R4_PHASE_COMPLETE,
		.error = BE_R4_ERROR_NONE,
		.decision = BE_R4_DECISION_RESUME_SAME_MANAGEMENT_FULL_FRAME,
		.active = management_binding_value(1U),
		.configuration_id = BE_R3_CONFIGURATION_ID,
		.management_hgatp = BE_R3_MANAGEMENT_HGATP,
		.protected_hgatp = BE_R3_PROTECTED_HGATP,
		.fault_seen = 1U,
		.event_seen = 1U,
		.trap_count = 2U,
	};
}

/* Exact advanced management frame the accepted R4 event trap leaves behind. */
static struct be_r4_frame imported_frame(void)
{
	struct be_r4_frame frame;
	be_size index;

	memset(&frame, 0, sizeof(frame));
	for (index = 0U; index < BE_ARRAY_SIZE(frame.gpr); ++index)
		frame.gpr[index] = BE_U64_C(0x1000) + index;
	frame.vstvec = BE_U64_C(0x2001);
	frame.vsepc = BE_U64_C(0x2002);
	frame.vscause = BE_U64_C(0x2003);
	frame.vstval = BE_U64_C(0x2004);
	frame.gpr[BE_R5_GPR_SP] = BE_R3_INITIAL_GUEST_SP;
	frame.gpr[BE_R5_GPR_S0] = BE_R4_PRIVATE_VALUE;
	frame.gpr[BE_R4_GPR_A0] = BE_R4_PRIVATE_VALUE;
	frame.gpr[BE_R4_GPR_A1] = BE_R4_SHARED_VALUE;
	frame.gpr[BE_R4_GPR_A6] = BE_R4_EVENT_VERSION_FUNCTION;
	frame.gpr[BE_R4_GPR_A7] = BE_R4_EVENT_ID;
	frame.scause = BE_R4_SCAUSE_VS_ECALL;
	frame.sepc = BE_R5_MANAGEMENT_RESTORE_PC;
	return frame;
}

static struct be_r4_frame final_event_frame(void)
{
	struct be_r4_frame frame = imported_frame();

	frame.gpr[BE_R4_GPR_A7] = BE_R5_FINAL_EVENT_ID;
	frame.sepc = BE_R5_MANAGEMENT_FINAL_EVENT_PC;
	return frame;
}

static struct be_r4_frame protected_frame(void)
{
	struct be_r4_frame frame;

	memset(&frame, 0, sizeof(frame));
	frame.gpr[BE_R5_GPR_SP] = BE_R5_PROTECTED_GUEST_SP;
	frame.gpr[BE_R5_GPR_S0] = BE_R5_PROTECTED_PRIVATE_VALUE;
	return frame;
}

static struct be_r4_frame protected_load_fault_frame(void)
{
	struct be_r4_frame frame = protected_frame();

	frame.scause = BE_R4_SCAUSE_LOAD_GUEST_PAGE_FAULT;
	frame.sepc = BE_R5_PROTECTED_LOAD_FAULT_PC;
	frame.stval = BE_R5_PROTECTED_LOAD_DENIED_GVA;
	frame.htval = BE_R5_PROTECTED_LOAD_DENIED_HTVAL;
	return frame;
}

static struct be_r4_frame protected_store_fault_frame(void)
{
	struct be_r4_frame frame = protected_frame();

	frame.scause = BE_R5_SCAUSE_STORE_GUEST_PAGE_FAULT;
	frame.sepc = BE_R5_PROTECTED_STORE_FAULT_PC;
	frame.stval = BE_R5_SHARED_STORE_DENIED_GVA;
	frame.htval = BE_R5_SHARED_STORE_DENIED_HTVAL;
	frame.gpr[BE_R4_GPR_A0] = BE_R5_DENIED_STORE_CANDIDATE;
	return frame;
}

static struct be_r4_frame protected_event_frame(void)
{
	struct be_r4_frame frame = protected_frame();

	frame.scause = BE_R4_SCAUSE_VS_ECALL;
	frame.sepc = BE_R5_PROTECTED_EVENT_PC;
	frame.gpr[BE_R4_GPR_A0] = BE_R5_PROTECTED_PRIVATE_VALUE;
	frame.gpr[BE_R4_GPR_A1] = BE_R4_SHARED_VALUE;
	frame.gpr[BE_R4_GPR_A6] = BE_R4_EVENT_VERSION_FUNCTION;
	frame.gpr[BE_R4_GPR_A7] = BE_R5_PROTECTED_EVENT_ID;
	return frame;
}

static struct be_r5_observation import_observation(void)
{
	return (struct be_r5_observation) {
		.hart_id = BE_CONFIGURATION_HART_ID,
		.active = management_binding_value(1U),
		.current_hgatp = BE_R3_MANAGEMENT_HGATP,
		.hstatus = BE_R3_HSTATUS_CONTROL_VALUE,
		.vsatp = 0U,
		.trusted_sp = BE_R3_INITIAL_TRUSTED_SP,
		.saved_state_pa = BE_R3_MANAGEMENT_SAVED_PA,
		.management_private_value = BE_R4_PRIVATE_VALUE,
		.protected_private_value = 0U,
		.shared_value = BE_R4_SHARED_VALUE,
	};
}

static struct be_r5_observation protected_observation(void)
{
	return (struct be_r5_observation) {
		.hart_id = BE_CONFIGURATION_HART_ID,
		.active = protected_binding_value(1U),
		.current_hgatp = BE_R3_PROTECTED_HGATP,
		.hstatus = BE_R3_HSTATUS_CONTROL_VALUE,
		.vsatp = 0U,
		.trusted_sp = BE_R5_PROTECTED_TRUSTED_SP,
		.saved_state_pa = BE_R5_PROTECTED_SAVED_PA,
		.management_private_value = BE_R4_PRIVATE_VALUE,
		.protected_private_value = BE_R5_PROTECTED_PRIVATE_VALUE,
		.shared_value = BE_R4_SHARED_VALUE,
	};
}

static struct be_r5_observation management_observation(void)
{
	struct be_r5_observation observation = import_observation();

	observation.protected_private_value = BE_R5_PROTECTED_PRIVATE_VALUE;
	return observation;
}

static struct be_r5_fence_ack protected_fence_ack(void)
{
	return (struct be_r5_fence_ack) {
		.source_hgatp = BE_R3_MANAGEMENT_HGATP,
		.hgatp_written = BE_R3_PROTECTED_HGATP,
		.hgatp_readback = BE_R3_PROTECTED_HGATP,
		.virtualization_off = 1U,
		.fence_completed = 1U,
	};
}

static struct be_r5_fence_ack management_fence_ack(void)
{
	return (struct be_r5_fence_ack) {
		.source_hgatp = BE_R3_PROTECTED_HGATP,
		.hgatp_written = BE_R3_MANAGEMENT_HGATP,
		.hgatp_readback = BE_R3_MANAGEMENT_HGATP,
		.virtualization_off = 1U,
		.fence_completed = 1U,
	};
}

static struct be_r5_entry_state protected_entry_state(void)
{
	return (struct be_r5_entry_state) {
		.hgatp = BE_R3_PROTECTED_HGATP,
		.hstatus = BE_R3_HSTATUS_CONTROL_VALUE,
		.sstatus = BE_R3_SSTATUS_SPP,
		.vsatp = 0U,
		.vstvec = 0U,
		.vsepc = 0U,
		.vscause = 0U,
		.vstval = 0U,
		.trusted_sp = BE_R5_PROTECTED_TRUSTED_SP,
		.saved_state_pa = BE_R5_PROTECTED_SAVED_PA,
	};
}

static struct be_r5_entry_state management_entry_state(void)
{
	return (struct be_r5_entry_state) {
		.hgatp = BE_R3_MANAGEMENT_HGATP,
		.hstatus = BE_R3_HSTATUS_CONTROL_VALUE,
		.sstatus = BE_R3_SSTATUS_SPP,
		.vsatp = 0U,
		.vstvec = 0U,
		.vsepc = 0U,
		.vscause = 0U,
		.vstval = 0U,
		.trusted_sp = BE_R3_INITIAL_TRUSTED_SP,
		.saved_state_pa = BE_R3_MANAGEMENT_SAVED_PA,
	};
}

/*
 * The two monitor saved pages are carried with the state so every accepted
 * stage keeps the exact frame bytes the assembly boundary would have written.
 */
struct world {
	struct be_r5_state state;
	struct be_r4_frame management_page;
	struct be_r4_frame protected_page;
	struct be_r5_pending pending;
	struct be_r5_transition transition;
	struct be_r5_result result;
};

static struct world fresh_world(void)
{
	struct be_r5_state initial = BE_R5_STATE_INITIALIZER;
	struct world world;

	memset(&world, 0, sizeof(world));
	world.state = initial;
	world.management_page = imported_frame();
	return world;
}

static struct world imported_world(void)
{
	struct world world = fresh_world();
	struct be_r4_state r4 = valid_r4();
	struct be_r4_frame frame = imported_frame();
	struct be_r5_observation observation = import_observation();

	CHECK(be_r5_import_r4_complete(&world.state, &r4, &frame,
				       &observation) == BE_R5_ERROR_NONE);
	return world;
}

static struct world pending_protected_world(void)
{
	struct world world = imported_world();

	CHECK(be_r5_prepare_pending(&world.state,
				    BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
				    &world.pending) == BE_R5_ERROR_NONE);
	return world;
}

/* Declared world of H-04, H-05, H-10, H-11, and H-12. */
static struct world fenced_protected_world(void)
{
	struct world world = pending_protected_world();
	struct be_r5_fence_ack ack = protected_fence_ack();

	CHECK(be_r5_note_target_fenced(&world.state, &ack) ==
	      BE_R5_ERROR_NONE);
	CHECK(world.state.phase == BE_R5_PHASE_PROTECTED_FENCED);
	return world;
}

/* Declared world of H-01, H-02, H-03, H-06, H-07, H-08, H-13, H-14, H-15. */
static struct world protected_running_world(void)
{
	struct world world = fenced_protected_world();
	struct be_r5_entry_state entry = protected_entry_state();

	CHECK(be_r5_publish_target(&world.state, &entry, &world.protected_page,
				   &world.transition) == BE_R5_ERROR_NONE);
	CHECK(world.state.phase ==
	      BE_R5_PHASE_PROTECTED_PUBLISHED_EXPECT_LOAD_FAULT);
	memset(&world.transition, 0, sizeof(world.transition));
	return world;
}

static struct world protected_store_world(void)
{
	struct world world = protected_running_world();
	struct be_r5_observation observation = protected_observation();

	world.protected_page = protected_load_fault_frame();
	CHECK(be_r5_handle_exit(&world.state, &world.protected_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	return world;
}

/* Declared world of H-16. */
static struct world protected_event_world(void)
{
	struct world world = protected_store_world();
	struct be_r5_observation observation = protected_observation();

	world.protected_page = protected_store_fault_frame();
	CHECK(be_r5_handle_exit(&world.state, &world.protected_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	CHECK(world.state.phase == BE_R5_PHASE_PROTECTED_EXPECT_SWITCH_EVENT);
	memset(&world.result, 0, sizeof(world.result));
	return world;
}

static struct world switch_requested_world(void)
{
	struct world world = protected_event_world();
	struct be_r5_observation observation = protected_observation();

	world.protected_page = protected_event_frame();
	CHECK(be_r5_handle_exit(&world.state, &world.protected_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	return world;
}

static struct world pending_management_world(void)
{
	struct world world = switch_requested_world();

	CHECK(be_r5_prepare_pending(&world.state,
				    BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
				    &world.pending) == BE_R5_ERROR_NONE);
	return world;
}

/* Declared world of H-09. */
static struct world fenced_management_world(void)
{
	struct world world = pending_management_world();
	struct be_r5_fence_ack ack = management_fence_ack();

	CHECK(be_r5_note_target_fenced(&world.state, &ack) ==
	      BE_R5_ERROR_NONE);
	CHECK(world.state.phase == BE_R5_PHASE_MANAGEMENT_FENCED);
	return world;
}

static struct world management_running_world(void)
{
	struct world world = fenced_management_world();
	struct be_r5_entry_state entry = management_entry_state();

	CHECK(be_r5_publish_target(&world.state, &entry,
				   &world.management_page,
				   &world.transition) == BE_R5_ERROR_NONE);
	return world;
}

/* Declared world of H-17. */
static struct world complete_world(void)
{
	struct world world = management_running_world();
	struct be_r5_observation observation = management_observation();

	world.management_page = final_event_frame();
	CHECK(be_r5_handle_exit(&world.state, &world.management_page,
				&observation, &world.result) ==
	      BE_R5_ERROR_NONE);
	CHECK(world.state.phase == BE_R5_PHASE_COMPLETE);
	CHECK(world.state.action == BE_R5_ACTION_SHUTDOWN);
	return world;
}

/*
 * The whole-state scrub the accepted mechanism performs on failure. This is a
 * measured invariant of the state the call was made against, so a caller can
 * never report a partially scrubbed state as a transactional rejection.
 */
static int state_scrubbed(const struct be_r5_state *state,
			  enum be_r5_error error)
{
	return state->phase == BE_R5_PHASE_FAILED && state->error == error &&
	       state->action == BE_R5_ACTION_TERMINAL &&
	       binding_is_zero(&state->active) &&
	       pending_is_zero(&state->pending) &&
	       frame_is_zero(&state->management_frame) &&
	       state->configuration_id == 0U &&
	       state->management_hgatp == 0U &&
	       state->protected_hgatp == 0U &&
	       state->protected_saved_pc == 0U &&
	       state->switch_requested == 0U && state->exit_count == 0U &&
	       state->switch_count == 0U;
}

/*
 * Sticky failure is computed, never assumed: the retained first error must
 * survive every public entry point, and no authority may survive with it.
 */
static int sticky_after(struct be_r5_state *state, enum be_r5_error error)
{
	struct be_r4_state r4 = valid_r4();
	struct be_r4_frame frame = imported_frame();
	struct be_r4_frame frame_before = imported_frame();
	struct be_r4_frame target;
	struct be_r5_observation observation = import_observation();
	struct be_r5_fence_ack ack = protected_fence_ack();
	struct be_r5_entry_state entry = protected_entry_state();
	struct be_r5_pending pending;
	struct be_r5_transition transition;
	struct be_r5_result result;
	int intact;

	memset(&target, 0, sizeof(target));
	memset(&pending, 0, sizeof(pending));
	memset(&transition, 0, sizeof(transition));
	memset(&result, 0, sizeof(result));

	intact = state_scrubbed(state, error);
	intact = intact &&
		 be_r5_import_r4_complete(state, &r4, &frame, &observation) ==
			 error &&
		 be_r5_prepare_pending(
			 state, BE_R5_DIRECTION_MANAGEMENT_TO_PROTECTED,
			 &pending) == error &&
		 be_r5_prepare_pending(
			 state, BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT,
			 &pending) == error &&
		 be_r5_note_target_fenced(state, &ack) == error &&
		 be_r5_publish_target(state, &entry, &target, &transition) ==
			 error &&
		 be_r5_handle_exit(state, &frame, &observation, &result) ==
			 error &&
		 be_r5_note_shutdown_returned(state, HOST_SBI_SUCCESS) ==
			 error &&
		 be_r5_fail(state, BE_R5_ERROR_NULL) == error &&
		 be_r5_fail(state, BE_R5_ERROR_NONE) == error;
	return intact && pending_is_zero(&pending) && frame_is_zero(&target) &&
	       transition.action == BE_R5_ACTION_NONE &&
	       result.action == BE_R5_ACTION_NONE &&
	       frames_equal(&frame, &frame_before) &&
	       state->phase == BE_R5_PHASE_FAILED && state->error == error;
}

/*
 * One malformed exit call.
 *
 * The world name is read from the accepted mechanism before the call and the
 * class name is read from the accepted mechanism after it, so the enumerator a
 * fixture asserts and the class its ledger row carries are the same value by
 * construction. Transactional means the caller's frame and result really were
 * left untouched.
 */
static struct host_case malformed_exit(struct world *world,
				       struct be_r4_frame *frame,
				       const struct be_r5_observation *observation,
				       enum be_r5_error expected)
{
	struct be_r4_frame before = *frame;
	struct be_r5_result result;
	struct host_case observed;

	memset(&result, 0, sizeof(result));
	memset(&observed, 0, sizeof(observed));
	observed.call = "be_r5_handle_exit";
	observed.world = be_r5_phase_name(world->state.phase);
	observed.observed = be_r5_handle_exit(&world->state, frame,
					      observation, &result);
	observed.class = be_r5_error_name(observed.observed);
	CHECK(observed.observed == expected);
	CHECK(strcmp(observed.class, be_r5_error_name(expected)) == 0);
	observed.transactional = frames_equal(frame, &before) &&
				 result.action == BE_R5_ACTION_NONE &&
				 result.exit_class == BE_R5_EXIT_NONE &&
				 result.advanced_pc == 0U;
	observed.sticky = sticky_after(&world->state, observed.observed);
	return observed;
}

/*
 * H-01 is the only fixture that passes a null pointer, so it is the only one
 * whose transactional evidence has to be measured from whichever arguments are
 * actually present. The world is still the accepted mechanism's own name for
 * the state the call was made against, and the class is still its own name for
 * the enumerator it returned. When the state itself is null there is nowhere
 * to retain the error, so stickiness there is the repeated identical rejection
 * together with a world that was never touched.
 */
static struct host_case null_pointer_exit(struct world *world,
					  struct be_r5_state *state,
					  struct be_r4_frame *frame,
					  const struct be_r5_observation *observation,
					  struct be_r5_result *result,
					  enum be_r5_error expected)
{
	struct be_r4_frame before;
	struct host_case observed;
	enum be_r5_phase phase_before = world->state.phase;
	int untouched = 1;

	memset(&before, 0, sizeof(before));
	memset(&observed, 0, sizeof(observed));
	if (frame != (struct be_r4_frame *)0)
		before = *frame;
	observed.call = "be_r5_handle_exit";
	observed.world = be_r5_phase_name(phase_before);
	observed.observed = be_r5_handle_exit(state, frame, observation,
					      result);
	observed.class = be_r5_error_name(observed.observed);
	CHECK(observed.observed == expected);
	CHECK(strcmp(observed.class, be_r5_error_name(expected)) == 0);
	if (frame != (struct be_r4_frame *)0)
		untouched = untouched && frames_equal(frame, &before);
	if (result != (struct be_r5_result *)0)
		untouched = untouched &&
			    result->action == BE_R5_ACTION_NONE &&
			    result->exit_class == BE_R5_EXIT_NONE &&
			    result->advanced_pc == 0U;
	observed.transactional = untouched;
	if (state == (struct be_r5_state *)0)
		observed.sticky = be_r5_handle_exit(state, frame, observation,
						    result) ==
					  observed.observed &&
				  world->state.phase == phase_before &&
				  world->state.error == BE_R5_ERROR_NONE;
	else
		observed.sticky = sticky_after(&world->state,
					       observed.observed);
	return observed;
}

/*
 * One malformed publication, observed the same way: pre-call world, post-call
 * enumerator, and the accepted mechanism's own name for that enumerator.
 */
static struct host_case malformed_publish(struct world *world,
					  const struct be_r5_entry_state *entry,
					  struct be_r4_frame *target_frame,
					  enum be_r5_error expected)
{
	struct be_r4_frame before = *target_frame;
	struct be_r5_transition transition;
	struct host_case observed;

	memset(&transition, 0, sizeof(transition));
	memset(&observed, 0, sizeof(observed));
	observed.call = "be_r5_publish_target";
	observed.world = be_r5_phase_name(world->state.phase);
	observed.observed = be_r5_publish_target(&world->state, entry,
						 target_frame, &transition);
	observed.class = be_r5_error_name(observed.observed);
	CHECK(observed.observed == expected);
	CHECK(strcmp(observed.class, be_r5_error_name(expected)) == 0);
	observed.transactional = frames_equal(target_frame, &before) &&
				 transition.action == BE_R5_ACTION_NONE &&
				 transition.entry_pc == 0U &&
				 binding_is_zero(&transition.active);
	observed.sticky = sticky_after(&world->state, observed.observed);
	return observed;
}

/*
 * One malformed shutdown return. Both H-17 outcomes are observed rather than
 * declared: the firmware result decides which enumerator the mechanism
 * returns, and that enumerator names the class. There is no caller-visible
 * output parameter here, so transactional is the measured whole-state scrub.
 */
static struct host_case malformed_shutdown(struct world *world, long sbi_error,
					   enum be_r5_error expected)
{
	struct host_case observed;

	memset(&observed, 0, sizeof(observed));
	observed.call = "be_r5_note_shutdown_returned";
	CHECK(state_scrubbed(&world->state, BE_R5_ERROR_NONE) == 0);
	observed.world = be_r5_phase_name(world->state.phase);
	observed.observed = be_r5_note_shutdown_returned(&world->state,
							 sbi_error);
	observed.class = be_r5_error_name(observed.observed);
	CHECK(observed.observed == expected);
	CHECK(strcmp(observed.class, be_r5_error_name(expected)) == 0);
	observed.transactional = state_scrubbed(&world->state,
						observed.observed);
	observed.sticky = sticky_after(&world->state, observed.observed);
	return observed;
}

/* The accepted exit of the declared world, with nothing malformed. */
static int restored_exit(struct world *world, struct be_r4_frame *frame,
			 const struct be_r5_observation *observation)
{
	struct be_r5_result result;

	memset(&result, 0, sizeof(result));
	CHECK(be_r5_handle_exit(&world->state, frame, observation, &result) ==
	      BE_R5_ERROR_NONE);
	CHECK(world->state.error == BE_R5_ERROR_NONE);
	CHECK(world->state.phase != BE_R5_PHASE_FAILED);
	return result.action != BE_R5_ACTION_NONE;
}

/* The accepted publication of the declared world, with nothing malformed. */
static int restored_publish(struct world *world,
			    const struct be_r5_entry_state *entry,
			    struct be_r4_frame *target_frame)
{
	struct be_r5_transition transition;

	memset(&transition, 0, sizeof(transition));
	CHECK(be_r5_publish_target(&world->state, entry, target_frame,
				   &transition) == BE_R5_ERROR_NONE);
	CHECK(world->state.error == BE_R5_ERROR_NONE);
	CHECK(world->state.phase != BE_R5_PHASE_FAILED);
	return transition.action == BE_R5_ACTION_ENTER_TARGET;
}

/* An empty ledger row. Nothing is copied from the declaration table here. */
static struct host_result begin_fixture(const char *id)
{
	struct host_result row;

	memset(&row, 0, sizeof(row));
	row.id = declaration(id)->id;
	row.layer = HOST_LAYER;
	row.sticky = 1;
	row.transactional = 1;
	return row;
}

/*
 * Accumulate exactly what the accepted mechanism produced. Every case of one
 * fixture must report the same call and the same world, and each newly
 * observed class is appended in first-observation order, so the published
 * class list is the mechanism's own naming of its own return values.
 */
static void record_case(struct host_result *row, struct host_case observed)
{
	unsigned int index;

	CHECK(observed.call != (const char *)0);
	CHECK(observed.world != (const char *)0);
	CHECK(observed.class != (const char *)0);
	if (row->call == (const char *)0)
		row->call = observed.call;
	if (row->world == (const char *)0)
		row->world = observed.world;
	CHECK(strcmp(row->call, observed.call) == 0);
	CHECK(strcmp(row->world, observed.world) == 0);
	++row->cases;
	row->sticky = row->sticky && observed.sticky;
	row->transactional = row->transactional && observed.transactional;
	for (index = 0U; index < row->class_count; ++index) {
		if (strcmp(row->classes[index], observed.class) == 0)
			return;
	}
	CHECK(row->class_count < HOST_MAX_CLASSES);
	row->classes[row->class_count] = observed.class;
	++row->class_count;
}

/*
 * Compare the observed fixture against its declaration before anything is
 * published. Roles carry no observable value, so they are the only field taken
 * from the declaration, and they are taken only once the observed call, world,
 * case count, and ordered class list have all matched it exactly.
 */
static struct host_result finish_fixture(struct host_result row,
					 int restored_none)
{
	const struct host_declaration *declared = declaration(row.id);
	unsigned int index;

	CHECK(row.call != (const char *)0);
	CHECK(row.world != (const char *)0);
	CHECK(strcmp(row.call, declared->call) == 0);
	CHECK(strcmp(row.world, declared->world) == 0);
	CHECK(row.cases == declared->cases);
	CHECK(row.class_count == declared->class_count);
	for (index = 0U; index < row.class_count; ++index) {
		CHECK(strcmp(row.classes[index], declared->classes[index]) ==
		      0);
		row.roles[index] = declared->roles[index];
	}
	row.restored_none = restored_none;
	return row;
}

/*
 * H-01: be_r5_handle_exit takes exactly four pointers, and the fixture cycles
 * a NULL through each of them. There is no transition parameter here; that
 * name belongs to be_r5_publish_target.
 */
static struct host_result fixture_h01(void)
{
	struct host_result row = begin_fixture("H-01");
	struct world world = protected_running_world();
	struct be_r4_frame frame = protected_load_fault_frame();
	struct be_r5_observation observation = protected_observation();
	struct be_r5_result result;
	int restored;

	memset(&result, 0, sizeof(result));

	/* state is NULL: no state exists to retain the error. */
	record_case(&row, null_pointer_exit(&world, (struct be_r5_state *)0,
					    &frame, &observation, &result,
					    BE_R5_ERROR_NULL));

	/* frame is NULL. */
	world = protected_running_world();
	record_case(&row, null_pointer_exit(&world, &world.state,
					    (struct be_r4_frame *)0,
					    &observation, &result,
					    BE_R5_ERROR_NULL));

	/* observation is NULL. */
	world = protected_running_world();
	frame = protected_load_fault_frame();
	record_case(&row, null_pointer_exit(&world, &world.state, &frame,
					    (const struct be_r5_observation *)0,
					    &result, BE_R5_ERROR_NULL));

	/* result is NULL. */
	world = protected_running_world();
	frame = protected_load_fault_frame();
	record_case(&row, null_pointer_exit(&world, &world.state, &frame,
					    &observation,
					    (struct be_r5_result *)0,
					    BE_R5_ERROR_NULL));

	/* Restored: all four pointers present and the exit is accepted. */
	world = protected_running_world();
	frame = protected_load_fault_frame();
	restored = restored_exit(&world, &frame, &observation);
	CHECK(frame.sepc == BE_R5_PROTECTED_LOAD_RESUME_PC);
	return finish_fixture(row, restored);
}

/*
 * H-02: exactly one field of an otherwise cleared pending record, in a running
 * protected world. pending_clear is evaluated after the phase switch, the
 * three remaining null checks, and identities_intact, and strictly before the
 * active-binding check, so `pending` is the first failure.
 */
static struct host_result fixture_h02(void)
{
	struct host_result row = begin_fixture("H-02");
	struct world world = protected_running_world();
	struct be_r4_frame frame = protected_load_fault_frame();
	struct be_r5_observation observation = protected_observation();
	int restored;

	CHECK(pending_is_zero(&world.state.pending));
	world.state.pending.direction =
		BE_R5_DIRECTION_PROTECTED_TO_MANAGEMENT;
	CHECK(world.state.pending.frame_mode == BE_R5_FRAME_MODE_NONE);
	CHECK(binding_is_zero(&world.state.pending.source));
	CHECK(binding_is_zero(&world.state.pending.target));
	record_case(&row, malformed_exit(&world, &frame, &observation,
					 BE_R5_ERROR_PENDING));

	world = protected_running_world();
	frame = protected_load_fault_frame();
	restored = restored_exit(&world, &frame, &observation);
	return finish_fixture(row, restored);
}

/* H-03: wrong active binding in the observation. */
static struct host_result fixture_h03(void)
{
	struct host_result row = begin_fixture("H-03");
	struct world world = protected_running_world();
	struct be_r4_frame frame = protected_load_fault_frame();
	struct be_r5_observation observation = protected_observation();
	int restored;

	CHECK(observation.active.vcpu_id == BE_R5_PROTECTED_VCPU_ID);
	observation.active.vcpu_id = 3U;
	record_case(&row, malformed_exit(&world, &frame, &observation,
					 BE_R5_ERROR_BINDING));

	world = protected_running_world();
	frame = protected_load_fault_frame();
	observation = protected_observation();
	restored = restored_exit(&world, &frame, &observation);
	return finish_fixture(row, restored);
}

/*
 * H-04: validate_entry_state checks hgatp, entry controls, vsatp, the reset
 * CSRs, trusted_sp, then saved_state_pa, so a trusted stack that belongs to
 * the management domain is the first failure for the protected target.
 */
static struct host_result fixture_h04(void)
{
	struct host_result row = begin_fixture("H-04");
	struct world world = fenced_protected_world();
	struct be_r5_entry_state entry = protected_entry_state();
	int restored;

	CHECK(entry.trusted_sp == BE_R5_PROTECTED_TRUSTED_SP);
	entry.trusted_sp = BE_R3_INITIAL_TRUSTED_SP;
	record_case(&row, malformed_publish(&world, &entry,
					    &world.protected_page,
					    BE_R5_ERROR_TRUSTED_STACK));

	world = fenced_protected_world();
	entry = protected_entry_state();
	restored = restored_publish(&world, &entry, &world.protected_page);
	return finish_fixture(row, restored);
}

/*
 * H-05: deliberate secondary coverage of saved-page inside
 * validate_entry_state. D-14 is the primary saved-page fixture, at the
 * switch_domain check, so this claim is never counted toward completeness.
 */
static struct host_result fixture_h05(void)
{
	struct host_result row = begin_fixture("H-05");
	struct world world = fenced_protected_world();
	struct be_r5_entry_state entry = protected_entry_state();
	int restored;

	CHECK(entry.saved_state_pa == BE_R5_PROTECTED_SAVED_PA);
	entry.saved_state_pa = BE_R5_PROTECTED_SAVED_PA + BE_U64_C(0x1000);
	record_case(&row, malformed_publish(&world, &entry,
					    &world.protected_page,
					    BE_R5_ERROR_SAVED_PAGE));

	world = fenced_protected_world();
	entry = protected_entry_state();
	restored = restored_publish(&world, &entry, &world.protected_page);
	return finish_fixture(row, restored);
}

/* H-06: the exit did not originate in VS mode under the fixed controls. */
static struct host_result fixture_h06(void)
{
	struct host_result row = begin_fixture("H-06");
	struct world world = protected_running_world();
	struct be_r4_frame frame = protected_load_fault_frame();
	struct be_r5_observation observation = protected_observation();
	int restored;

	CHECK(observation.hstatus == BE_R3_HSTATUS_CONTROL_VALUE);
	observation.hstatus = BE_R3_HSTATUS_CONTROL_VALUE &
			      ~BE_R3_HSTATUS_SPV;
	record_case(&row, malformed_exit(&world, &frame, &observation,
					 BE_R5_ERROR_VS_ORIGIN));

	world = protected_running_world();
	frame = protected_load_fault_frame();
	observation = protected_observation();
	restored = restored_exit(&world, &frame, &observation);
	return finish_fixture(row, restored);
}

/* H-07: VS-stage translation is not Bare. */
static struct host_result fixture_h07(void)
{
	struct host_result row = begin_fixture("H-07");
	struct world world = protected_running_world();
	struct be_r4_frame frame = protected_load_fault_frame();
	struct be_r5_observation observation = protected_observation();
	int restored;

	CHECK(observation.vsatp == 0U);
	observation.vsatp = BE_U64_C(0x8000000000080000);
	record_case(&row, malformed_exit(&world, &frame, &observation,
					 BE_R5_ERROR_VSATP));

	world = protected_running_world();
	frame = protected_load_fault_frame();
	observation = protected_observation();
	restored = restored_exit(&world, &frame, &observation);
	return finish_fixture(row, restored);
}

/*
 * H-08: struct be_r4_frame carries gpr[31], vstvec, vsepc, vscause, vstval,
 * scause, sepc, stval, htval, and reserved in 320 bytes, and deliberately has
 * no htinst. A nonzero reserved word is rejected before the observation.
 */
static struct host_result fixture_h08(void)
{
	struct host_result row = begin_fixture("H-08");
	struct world world = protected_running_world();
	struct be_r4_frame frame = protected_load_fault_frame();
	struct be_r5_observation observation = protected_observation();
	int restored;

	CHECK(sizeof(struct be_r4_frame) == 320U);
	CHECK(frame.reserved == 0U);
	frame.reserved = BE_U64_C(1);
	record_case(&row, malformed_exit(&world, &frame, &observation,
					 BE_R5_ERROR_FRAME_RESERVED));

	world = protected_running_world();
	frame = protected_load_fault_frame();
	restored = restored_exit(&world, &frame, &observation);
	return finish_fixture(row, restored);
}

/*
 * H-09: frame-state is not produced by be_r5_handle_exit at all.
 * validate_management_frame returns an internal event-argument verdict and
 * be_r5_publish_target rewrites every internal frame verdict to frame-state
 * before returning. state->management_frame is examined by none of the earlier
 * checks, so one mutated shared-value register is reached by construction.
 */
static struct host_result fixture_h09(void)
{
	struct host_result row = begin_fixture("H-09");
	struct world world = fenced_management_world();
	struct be_r5_entry_state entry = management_entry_state();
	int restored;

	CHECK(world.state.management_frame.gpr[BE_R4_GPR_A1] ==
	      BE_R4_SHARED_VALUE);
	CHECK(BE_R4_SHARED_VALUE == BE_U64_C(34));
	world.state.management_frame.gpr[BE_R4_GPR_A1] =
		BE_R4_SHARED_VALUE + BE_U64_C(1);
	record_case(&row, malformed_publish(&world, &entry,
					    &world.management_page,
					    BE_R5_ERROR_FRAME_STATE));

	world = fenced_management_world();
	entry = management_entry_state();
	restored = restored_publish(&world, &entry, &world.management_page);
	return finish_fixture(row, restored);
}

/*
 * H-10: target-reset is produced only when one of the four reset CSRs of the
 * entry state is nonzero. A nonzero GPR does not produce it, which keeps H-10
 * disjoint from H-08 and H-09. The fixture cycles all four fields.
 */
static struct host_result fixture_h10(void)
{
	struct host_result row = begin_fixture("H-10");
	struct be_r5_entry_state entry;
	struct world world;
	unsigned int index;
	int restored;

	for (index = 0U; index < 4U; ++index) {
		world = fenced_protected_world();
		entry = protected_entry_state();
		CHECK(entry.vstvec == 0U && entry.vsepc == 0U &&
		      entry.vscause == 0U && entry.vstval == 0U);
		if (index == 0U)
			entry.vstvec = BE_R5_PROTECTED_ENTRY_PC;
		else if (index == 1U)
			entry.vsepc = BE_R5_PROTECTED_ENTRY_PC;
		else if (index == 2U)
			entry.vscause = BE_R5_PROTECTED_ENTRY_PC;
		else
			entry.vstval = BE_R5_PROTECTED_ENTRY_PC;
		record_case(&row,
			    malformed_publish(&world, &entry,
					      &world.protected_page,
					      BE_R5_ERROR_TARGET_RESET));
	}

	world = fenced_protected_world();
	entry = protected_entry_state();
	restored = restored_publish(&world, &entry, &world.protected_page);
	return finish_fixture(row, restored);
}

/*
 * H-11: entry controls precede vsatp and the reset CSRs in
 * validate_entry_state, so a cleared SPP and a cleared SPV each fail there
 * first. Each case malforms exactly one field.
 */
static struct host_result fixture_h11(void)
{
	struct host_result row = begin_fixture("H-11");
	struct world world = fenced_protected_world();
	struct be_r5_entry_state entry = protected_entry_state();
	int restored;

	CHECK(entry.sstatus == BE_R3_SSTATUS_SPP);
	entry.sstatus = BE_R3_SSTATUS_SPP & ~BE_R3_SSTATUS_SPP;
	record_case(&row, malformed_publish(&world, &entry,
					    &world.protected_page,
					    BE_R5_ERROR_ENTRY_CONTROLS));

	world = fenced_protected_world();
	entry = protected_entry_state();
	CHECK(entry.hstatus == BE_R3_HSTATUS_CONTROL_VALUE);
	entry.hstatus = BE_R3_HSTATUS_CONTROL_VALUE & ~BE_R3_HSTATUS_SPV;
	record_case(&row, malformed_publish(&world, &entry,
					    &world.protected_page,
					    BE_R5_ERROR_ENTRY_CONTROLS));

	world = fenced_protected_world();
	entry = protected_entry_state();
	restored = restored_publish(&world, &entry, &world.protected_page);
	return finish_fixture(row, restored);
}

/*
 * H-12: publication has exactly one producer, and of the three fields its
 * guard reads only switch_count is reachable by a single mutation. A cleared
 * active.published yields binding and a published pending target yields
 * pending, both through earlier checks.
 */
static struct host_result fixture_h12(void)
{
	struct host_result row = begin_fixture("H-12");
	struct world world = fenced_protected_world();
	struct be_r5_entry_state entry = protected_entry_state();
	int restored;

	CHECK(world.state.switch_count == 0U);
	CHECK(world.state.active.published == 1U);
	CHECK(world.state.pending.target.published == 0U);
	world.state.switch_count = 1U;
	record_case(&row, malformed_publish(&world, &entry,
					    &world.protected_page,
					    BE_R5_ERROR_PUBLICATION));

	world = fenced_protected_world();
	entry = protected_entry_state();
	restored = restored_publish(&world, &entry, &world.protected_page);
	return finish_fixture(row, restored);
}

/* H-13: the observation is not for the fixed single hart. */
static struct host_result fixture_h13(void)
{
	struct host_result row = begin_fixture("H-13");
	struct world world = protected_running_world();
	struct be_r4_frame frame = protected_load_fault_frame();
	struct be_r5_observation observation = protected_observation();
	int restored;

	CHECK(observation.hart_id == BE_CONFIGURATION_HART_ID);
	CHECK(BE_CONFIGURATION_HART_ID == 0U);
	observation.hart_id = BE_U64_C(1);
	record_case(&row, malformed_exit(&world, &frame, &observation,
					 BE_R5_ERROR_HART));

	world = protected_running_world();
	frame = protected_load_fault_frame();
	observation = protected_observation();
	restored = restored_exit(&world, &frame, &observation);
	return finish_fixture(row, restored);
}

/*
 * H-14: trap metadata belongs to struct be_r4_frame, not to
 * struct be_r5_observation. An htval that cannot be shifted safely is rejected
 * before any reconstruction is attempted.
 */
static struct host_result fixture_h14(void)
{
	struct host_result row = begin_fixture("H-14");
	struct world world = protected_running_world();
	struct be_r4_frame frame = protected_load_fault_frame();
	struct be_r5_observation observation = protected_observation();
	int restored;

	CHECK(frame.htval == BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.htval = BE_U64_C(0x4000000000000000);
	record_case(&row, malformed_exit(&world, &frame, &observation,
					 BE_R5_ERROR_HTVAL_OVERFLOW));

	world = protected_running_world();
	frame = protected_load_fault_frame();
	restored = restored_exit(&world, &frame, &observation);
	return finish_fixture(row, restored);
}

/*
 * H-15: validate_denied_access checks scause, then sepc, then stval, then the
 * htval reconstruction, so stval stays correct or gva would fire first and the
 * fixture would be a layer shift.
 */
static struct host_result fixture_h15(void)
{
	struct host_result row = begin_fixture("H-15");
	struct world world = protected_running_world();
	struct be_r4_frame frame = protected_load_fault_frame();
	struct be_r5_observation observation = protected_observation();
	int restored;

	CHECK(frame.stval == BE_R5_PROTECTED_LOAD_DENIED_GVA);
	CHECK(frame.htval == BE_R5_PROTECTED_LOAD_DENIED_HTVAL);
	frame.htval = BE_U64_C(0x10000c00);
	CHECK((frame.htval << 2) == BE_U64_C(0x40003000));
	CHECK(BE_U64_C(0x40003000) != BE_R5_PROTECTED_LOAD_DENIED_GPA);
	record_case(&row, malformed_exit(&world, &frame, &observation,
					 BE_R5_ERROR_GPA));

	world = protected_running_world();
	frame = protected_load_fault_frame();
	restored = restored_exit(&world, &frame, &observation);
	return finish_fixture(row, restored);
}

/* H-16: nonzero event-path trap metadata on the protected switch event. */
static struct host_result fixture_h16(void)
{
	struct host_result row = begin_fixture("H-16");
	struct world world = protected_event_world();
	struct be_r4_frame frame = protected_event_frame();
	struct be_r5_observation observation = protected_observation();
	int restored;

	CHECK(frame.scause == BE_R4_SCAUSE_VS_ECALL);
	CHECK(frame.stval == 0U);
	frame.stval = BE_U64_C(4);
	record_case(&row, malformed_exit(&world, &frame, &observation,
					 BE_R5_ERROR_TRAP_METADATA));

	world = protected_event_world();
	frame = protected_event_frame();
	restored = restored_exit(&world, &frame, &observation);
	CHECK(frame.sepc == BE_R5_PROTECTED_SAVED_PC);
	return finish_fixture(row, restored);
}

/*
 * H-17: both shutdown classes at the host layer. Producing them under QEMU
 * would require forging the digest-pinned firmware, which R6 forbids, so R6
 * claims no dynamic coverage of these two classes. Neither outcome is
 * declared: the firmware result decides which enumerator the accepted
 * mechanism returns and that enumerator names its own class. The restored case
 * is the successful shutdown that never returns, so the call is never made.
 */
static struct host_result fixture_h17(void)
{
	struct host_result row = begin_fixture("H-17");
	struct world world = complete_world();
	struct host_case returned;
	long sbi_error;
	int restored;

	returned = malformed_shutdown(&world, HOST_SBI_SUCCESS,
				      BE_R5_ERROR_SHUTDOWN_RETURNED);
	record_case(&row, returned);
	/*
	 * transactional is the measured scrub, so un-scrubbing one field of
	 * the very state just measured has to change the verdict.
	 */
	CHECK(returned.transactional == 1);
	world.state.switch_count = 1U;
	CHECK(state_scrubbed(&world.state, returned.observed) == 0);

	for (sbi_error = HOST_SBI_FIRST_ERROR;
	     sbi_error >= HOST_SBI_LAST_ERROR; --sbi_error) {
		world = complete_world();
		record_case(&row,
			    malformed_shutdown(&world, sbi_error,
					       BE_R5_ERROR_SHUTDOWN_REJECTED));
	}
	CHECK(row.class_count == 2U);
	CHECK(strcmp(row.classes[0],
		     be_r5_error_name(BE_R5_ERROR_SHUTDOWN_RETURNED)) == 0);
	CHECK(strcmp(row.classes[1],
		     be_r5_error_name(BE_R5_ERROR_SHUTDOWN_REJECTED)) == 0);

	/* The accepted shutdown never returns, so nothing is asked of it. */
	world = complete_world();
	restored = world.state.phase == BE_R5_PHASE_COMPLETE &&
		   world.state.error == BE_R5_ERROR_NONE &&
		   world.state.action == BE_R5_ACTION_SHUTDOWN;
	CHECK(restored == 1);
	return finish_fixture(row, restored);
}

/*
 * The host semantic checker.
 *
 * It compares an observed host ledger against the declaration table and
 * returns the exact rejection reason, or a null pointer when the ledger is
 * accepted. Rule order is fixed so every mutation below is rejected under its
 * own name rather than under an earlier rule's name.
 */
static const char *check_host_ledger(const struct host_result *observed,
				     unsigned int count)
{
	unsigned int index;
	unsigned int other;
	unsigned int matches;
	unsigned int outcomes = 0U;
	unsigned int primary = 0U;
	unsigned int secondary = 0U;
	const struct host_result *row;
	const struct host_declaration *declared;

	/* 1. every declared fixture is present exactly once */
	for (index = 0U; index < HOST_FIXTURES; ++index) {
		declared = &host_declarations[index];
		matches = 0U;
		for (other = 0U; other < count; ++other) {
			if (observed[other].id != (const char *)0 &&
			    strcmp(observed[other].id, declared->id) == 0)
				++matches;
		}
		if (matches == 0U) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "missing-fixture:%s", declared->id);
			return reason_buffer;
		}
		if (matches > 1U) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "duplicate-fixture:%s", declared->id);
			return reason_buffer;
		}
	}
	/* 2. no undeclared fixture is present */
	if (count != HOST_FIXTURES) {
		snprintf(reason_buffer, sizeof(reason_buffer),
			 "unexpected-fixture:count-%u", count);
		return reason_buffer;
	}
	/* 3. no fixture reports that the accepted mechanism accepted it */
	for (index = 0U; index < count; ++index) {
		row = &observed[index];
		for (other = 0U; other < row->class_count; ++other) {
			if (strcmp(row->classes[other], "none") != 0)
				continue;
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "unexpected-pass:%s", row->id);
			return reason_buffer;
		}
	}
	/* 4. no primary class is claimed by two fixtures */
	for (index = 0U; index < count; ++index) {
		for (other = 0U; other < observed[index].class_count; ++other) {
			unsigned int later;

			if (strcmp(observed[index].roles[other],
				   "primary") != 0)
				continue;
			for (later = index + 1U; later < count; ++later) {
				unsigned int slot;

				for (slot = 0U;
				     slot < observed[later].class_count;
				     ++slot) {
					if (strcmp(observed[later].roles[slot],
						   "primary") != 0)
						continue;
					if (strcmp(observed[index]
							   .classes[other],
						   observed[later]
							   .classes[slot]) != 0)
						continue;
					snprintf(reason_buffer,
						 sizeof(reason_buffer),
						 "duplicate-primary-class:%s",
						 observed[index]
							 .classes[other]);
					return reason_buffer;
				}
			}
		}
	}
	/* 5. every fixture matches its declaration exactly */
	for (index = 0U; index < HOST_FIXTURES; ++index) {
		declared = &host_declarations[index];
		row = (const struct host_result *)0;
		for (other = 0U; other < count; ++other) {
			if (strcmp(observed[other].id, declared->id) == 0)
				row = &observed[other];
		}
		if (row == (const struct host_result *)0) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "missing-fixture:%s", declared->id);
			return reason_buffer;
		}
		if (row->layer == (const char *)0 ||
		    strcmp(row->layer, HOST_LAYER) != 0) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "wrong-layer:%s", declared->id);
			return reason_buffer;
		}
		if (row->world == (const char *)0 ||
		    strcmp(row->world, declared->world) != 0) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "wrong-world:%s", declared->id);
			return reason_buffer;
		}
		if (row->call == (const char *)0 ||
		    strcmp(row->call, declared->call) != 0) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "wrong-call:%s", declared->id);
			return reason_buffer;
		}
		if (row->cases != declared->cases) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "wrong-case-count:%s", declared->id);
			return reason_buffer;
		}
		if (row->class_count != declared->class_count) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "wrong-class-count:%s", declared->id);
			return reason_buffer;
		}
		for (other = 0U; other < declared->class_count; ++other) {
			if (row->classes[other] == (const char *)0 ||
			    strcmp(row->classes[other],
				   declared->classes[other]) != 0) {
				snprintf(reason_buffer, sizeof(reason_buffer),
					 "wrong-error-class:%s", declared->id);
				return reason_buffer;
			}
			if (row->roles[other] == (const char *)0 ||
			    strcmp(row->roles[other],
				   declared->roles[other]) != 0) {
				snprintf(reason_buffer, sizeof(reason_buffer),
					 "wrong-role:%s", declared->id);
				return reason_buffer;
			}
		}
		/* 6. rejection integrity for that fixture */
		if (row->sticky != 1) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "non-sticky-failure:%s", declared->id);
			return reason_buffer;
		}
		if (row->transactional != 1) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "non-transactional-failure:%s", declared->id);
			return reason_buffer;
		}
		if (row->restored_none != 1) {
			snprintf(reason_buffer, sizeof(reason_buffer),
				 "restored-case-not-accepted:%s",
				 declared->id);
			return reason_buffer;
		}
	}
	/* 7. the coverage arithmetic is recomputed, never restated */
	for (index = 0U; index < count; ++index) {
		for (other = 0U; other < observed[index].class_count; ++other) {
			++outcomes;
			if (strcmp(observed[index].roles[other],
				   "primary") == 0)
				++primary;
			else
				++secondary;
		}
	}
	if (outcomes != HOST_CLASS_OUTCOMES || primary != HOST_PRIMARY_CLASSES ||
	    secondary != HOST_SECONDARY_CLASSES) {
		snprintf(reason_buffer, sizeof(reason_buffer),
			 "class-outcome-count:%u-%u-%u", outcomes, primary,
			 secondary);
		return reason_buffer;
	}
	return (const char *)0;
}

static void copy_ledger(struct host_result *destination,
			const struct host_result *source, unsigned int count)
{
	unsigned int index;

	for (index = 0U; index < count; ++index)
		destination[index] = source[index];
}

/* Exactly one rejection reason, compared in full. */
static void expect_rejection(const struct host_result *ledger,
			     unsigned int count, const char *expected)
{
	const char *reason = check_host_ledger(ledger, count);

	CHECK(reason != (const char *)0);
	CHECK(strcmp(reason, expected) == 0);
}

/*
 * The seventeen paired negative self-tests. Each proves that the accepted
 * class was caused by the declared defect, and that the checker is a real
 * comparison: a forged class, a forged world, and a forged layer for the same
 * fixture are each rejected under their own name. Every class of a
 * multi-class fixture is forged in turn, so H-17's second observed outcome is
 * covered as well as its first.
 */
static void host_self_tests(const struct host_result *truth)
{
	struct host_result forged[HOST_FIXTURES];
	char expected[128];
	const char *forged_world = be_r5_phase_name(BE_R5_PHASE_FRESH);
	unsigned int index;

	for (index = 0U; index < HOST_FIXTURES; ++index) {
		const char *secondary = "none";
		unsigned int slot;

		CHECK(truth[index].restored_none == 1);
		CHECK(truth[index].world != (const char *)0);
		CHECK(strcmp(truth[index].world, forged_world) != 0);
		snprintf(expected, sizeof(expected), "wrong-error-class:%s",
			 truth[index].id);
		for (slot = 0U; slot < truth[index].class_count; ++slot) {
			if (slot == 1U)
				secondary = truth[index].classes[1];
			copy_ledger(forged, truth, HOST_FIXTURES);
			forged[index].classes[slot] = HOST_FORGED_CLASS;
			expect_rejection(forged, HOST_FIXTURES, expected);
		}

		copy_ledger(forged, truth, HOST_FIXTURES);
		forged[index].world = forged_world;
		snprintf(expected, sizeof(expected), "wrong-world:%s",
			 truth[index].id);
		expect_rejection(forged, HOST_FIXTURES, expected);

		copy_ledger(forged, truth, HOST_FIXTURES);
		forged[index].layer = HOST_FORGED_LAYER;
		snprintf(expected, sizeof(expected), "wrong-layer:%s",
			 truth[index].id);
		expect_rejection(forged, HOST_FIXTURES, expected);

		CHECK(check_host_ledger(truth, HOST_FIXTURES) ==
		      (const char *)0);
		printf("BE_R6_HOST_SELFTEST: PASS id=%s world=%s restored=none "
		       "forged-class=wrong-error-class forged-secondary=%s "
		       "forged-world=wrong-world forged-layer=wrong-layer\n",
		       truth[index].id, truth[index].world, secondary);
	}
}

/* Ledger mutations. Each must be rejected under its own name. */
static void host_mutations(const struct host_result *truth)
{
	struct host_result forged[HOST_FIXTURES];
	struct world world;
	struct be_r4_frame frame;
	struct be_r5_observation observation;
	struct be_r5_entry_state entry;
	struct host_case elsewhere;
	unsigned int index;

	CHECK(check_host_ledger(truth, HOST_FIXTURES) == (const char *)0);

	/* an omitted fixture */
	copy_ledger(forged, truth, HOST_FIXTURES);
	for (index = 8U; index + 1U < HOST_FIXTURES; ++index)
		forged[index] = forged[index + 1U];
	expect_rejection(forged, HOST_FIXTURES - 1U, "missing-fixture:H-09");
	printf("BE_R6_HOST_MUTATION: PASS case=omitted-fixture "
	       "rejected=missing-fixture:H-09\n");

	/* two fixtures claiming one primary class */
	copy_ledger(forged, truth, HOST_FIXTURES);
	forged[3].classes[0] = truth[2].classes[0];
	expect_rejection(forged, HOST_FIXTURES,
			 "duplicate-primary-class:binding");
	printf("BE_R6_HOST_MUTATION: PASS case=duplicate-primary-class "
	       "rejected=duplicate-primary-class:binding\n");

	/* a class attributed to the wrong identifier */
	copy_ledger(forged, truth, HOST_FIXTURES);
	forged[2].classes[0] = truth[3].classes[0];
	forged[3].classes[0] = truth[2].classes[0];
	expect_rejection(forged, HOST_FIXTURES, "wrong-error-class:H-03");
	printf("BE_R6_HOST_MUTATION: PASS case=swapped-id-class "
	       "rejected=wrong-error-class:H-03\n");

	/* a fixture the accepted mechanism did not reject */
	copy_ledger(forged, truth, HOST_FIXTURES);
	forged[8].classes[0] = "none";
	expect_rejection(forged, HOST_FIXTURES, "unexpected-pass:H-09");
	printf("BE_R6_HOST_MUTATION: PASS case=unexpected-pass "
	       "rejected=unexpected-pass:H-09\n");

	/* a rejection that did not retain its first error */
	copy_ledger(forged, truth, HOST_FIXTURES);
	forged[11].sticky = 0;
	expect_rejection(forged, HOST_FIXTURES, "non-sticky-failure:H-12");
	printf("BE_R6_HOST_MUTATION: PASS case=non-sticky-failure "
	       "rejected=non-sticky-failure:H-12\n");

	/*
	 * A different defect really run in H-03's declared world. The
	 * enumerator the accepted mechanism returns names the published class,
	 * so a row that keeps its declared identity but observed something
	 * else is rejected. `interrupt` is claimed by no host fixture, so this
	 * is a class comparison and not a duplicate-class comparison.
	 */
	copy_ledger(forged, truth, HOST_FIXTURES);
	world = protected_running_world();
	frame = protected_load_fault_frame();
	observation = protected_observation();
	frame.scause = frame.scause | BE_R4_INTERRUPT_BIT;
	elsewhere = malformed_exit(&world, &frame, &observation,
				   BE_R5_ERROR_INTERRUPT);
	CHECK(strcmp(elsewhere.world, truth[2].world) == 0);
	CHECK(strcmp(elsewhere.class, truth[2].classes[0]) != 0);
	forged[2].classes[0] = elsewhere.class;
	expect_rejection(forged, HOST_FIXTURES, "wrong-error-class:H-03");
	printf("BE_R6_HOST_MUTATION: PASS case=observed-class-not-declared "
	       "rejected=wrong-error-class:H-03\n");

	/*
	 * H-04's declared defect really run in another world. The world is the
	 * accepted mechanism's own name for the state the call was made
	 * against, so a row that reports the wrong world is rejected even when
	 * its class is right.
	 */
	copy_ledger(forged, truth, HOST_FIXTURES);
	world = fenced_management_world();
	entry = management_entry_state();
	CHECK(entry.trusted_sp == BE_R3_INITIAL_TRUSTED_SP);
	entry.trusted_sp = BE_R5_PROTECTED_TRUSTED_SP;
	elsewhere = malformed_publish(&world, &entry, &world.management_page,
				      BE_R5_ERROR_TRUSTED_STACK);
	CHECK(strcmp(elsewhere.class, truth[3].classes[0]) == 0);
	CHECK(strcmp(elsewhere.world, truth[3].world) != 0);
	forged[3].world = elsewhere.world;
	expect_rejection(forged, HOST_FIXTURES, "wrong-world:H-04");
	printf("BE_R6_HOST_MUTATION: PASS case=observed-world-not-declared "
	       "rejected=wrong-world:H-04\n");

	/*
	 * A partially scrubbed H-17 shutdown state. transactional is measured
	 * from the state the accepted mechanism left behind, so one surviving
	 * counter is enough to withdraw the claim.
	 */
	copy_ledger(forged, truth, HOST_FIXTURES);
	world = complete_world();
	elsewhere = malformed_shutdown(&world, HOST_SBI_SUCCESS,
				       BE_R5_ERROR_SHUTDOWN_RETURNED);
	CHECK(elsewhere.transactional == 1);
	world.state.switch_count = 1U;
	forged[16].transactional = state_scrubbed(&world.state,
						  elsewhere.observed);
	CHECK(forged[16].transactional == 0);
	expect_rejection(forged, HOST_FIXTURES,
			 "non-transactional-failure:H-17");
	printf("BE_R6_HOST_MUTATION: PASS case=partial-state-h17 "
	       "rejected=non-transactional-failure:H-17\n");

	CHECK(check_host_ledger(truth, HOST_FIXTURES) == (const char *)0);
}

static void report_fixture(const struct host_result *row)
{
	char classes[64];
	char roles[64];

	if (row->class_count == 2U) {
		snprintf(classes, sizeof(classes), "%s,%s", row->classes[0],
			 row->classes[1]);
		snprintf(roles, sizeof(roles), "%s,%s", row->roles[0],
			 row->roles[1]);
	} else {
		snprintf(classes, sizeof(classes), "%s", row->classes[0]);
		snprintf(roles, sizeof(roles), "%s", row->roles[0]);
	}
	printf("BE_R6_HOST_FIXTURE: PASS id=%s layer=%s call=%s world=%s "
	       "cases=%u classes=%s roles=%s sticky=%s transactional=%s "
	       "restored=none\n",
	       row->id, row->layer, row->call, row->world, row->cases, classes,
	       roles, row->sticky == 1 ? "yes" : "no",
	       row->transactional == 1 ? "yes" : "no");
}

int main(void)
{
	struct host_result observed[HOST_FIXTURES];
	unsigned int index;
	unsigned int cases = 0U;

	observed[0] = fixture_h01();
	observed[1] = fixture_h02();
	observed[2] = fixture_h03();
	observed[3] = fixture_h04();
	observed[4] = fixture_h05();
	observed[5] = fixture_h06();
	observed[6] = fixture_h07();
	observed[7] = fixture_h08();
	observed[8] = fixture_h09();
	observed[9] = fixture_h10();
	observed[10] = fixture_h11();
	observed[11] = fixture_h12();
	observed[12] = fixture_h13();
	observed[13] = fixture_h14();
	observed[14] = fixture_h15();
	observed[15] = fixture_h16();
	observed[16] = fixture_h17();

	CHECK(check_host_ledger(observed, HOST_FIXTURES) == (const char *)0);
	for (index = 0U; index < HOST_FIXTURES; ++index) {
		CHECK(strcmp(observed[index].id,
			     host_declarations[index].id) == 0);
		cases += observed[index].cases;
		report_fixture(&observed[index]);
	}
	CHECK(cases == HOST_CASES);

	host_self_tests(observed);
	host_mutations(observed);

	printf("BE_R6_HOST_CHECK: PASS fixtures=%u class-outcomes=%u "
	       "primary=%u secondary=%u self-tests=%u mutations=%u cases=%u "
	       "assertions=%lu\n",
	       HOST_FIXTURES, HOST_CLASS_OUTCOMES, HOST_PRIMARY_CLASSES,
	       HOST_SECONDARY_CLASSES, HOST_FIXTURES, HOST_MUTATIONS, cases,
	       assertions);
	return 0;
}
