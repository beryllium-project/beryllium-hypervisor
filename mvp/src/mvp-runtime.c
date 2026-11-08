// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP hart 0 runtime: the MVP region's check and the clear of its
 *          BSS; the accepted R3 boot check (BE_MVP:00 BOOT_VALIDATED); the
 *          MVP core profile copied, validated, sealed, and derived through
 *          the ported R1 mechanism, the G-stage builder's inputs taken from
 *          the derived roots and checked against what the image links
 *          (BE_MVP:00 CONFIG_SEALED; planning/mvp-m6-plan.md, D-1 to D-3);
 *          hart 0's HS and VS state reset through the accepted function;
 *          then the scenario line, the firmware probes (HSM, IPI,
 *          both domain harts and every other hart STOPPED but at most one
 *          STARTED, the start rule's), the Sstc probe, both
 *          MVP-owned G-stage roots (built with the sealed channel record's
 *          leaf, re-walked, and checked to share exactly the declared
 *          channel page: planning/mvp-m1-plan.md, "Boot sequence additions
 *          on hart 0"), the payload checks, both domain RAM clears and the
 *          channel page's, the kernel and DTB placement in both windows,
 *          and the data fence; then both domain harts' blocks, each with
 *          its walked window and channel leaf, published behind the
 *          generation word, hart 0's run budget, both hart starts, the
 *          READY wait, and the control loop that drains both domains' rings
 *          round-robin, at most one record from each ring in turn (Plan
 *          revision M0-C.1), prints their lines and their DENIAL records'
 *          BE_MVP:DENY lines, probes each with one PING, and ends the run;
 *          and the formatting shared with the domain harts' runtime
 *          (mvp-hartmain.c). A scenario with pages (planning/mvp-m2-plan.md,
 *          "Boot sequence additions on hart 0") builds both roots with
 *          their leaves for the declared pages in place of the channel
 *          record's, checks every page's leaf in both, clears each channel
 *          page and writes the secret into the secret page after the window
 *          clears; each domain hart's block carries its root's walked
 *          leaves for the declared pages, and the control loop checks
 *          DENIAL records against the sealed pages. A scenario with the
 *          management extension (planning/mvp-m2-plan.md, "The management
 *          extension") gives the control loop the sealed grants and hart
 *          0's management state: each request is decided there, a denial
 *          answered at once with MGMT_RESULT and one IPI, a granted request
 *          delivered to its target's hart as PAUSE or TERMINATE with one
 *          IPI and answered when the target's PAUSED or TERMINATED is
 *          drained, each request logged as one BE_MVP:MGMT line, each
 *          transition as BE_MVP:12 DOMAIN_PAUSED or DOMAIN_TERMINATED, the
 *          latter with the terminated domain's launch register. Since M7
 *          (planning/mvp-m7-plan.md, D-1, D-3, D-4, and D-5), each block
 *          also carries an input ring and each domain hart its grant of
 *          console input, both from the sealed configuration; in an image
 *          that grants console input to a domain, hart 0 arms console
 *          input after the barrier (BE_MVP:15, BE_MVP:16 FOCUS none, and a
 *          first poll that discards what the firmware held), and then,
 *          after each drain, polls the firmware console, routes each byte
 *          through the focus parser to the focused domain's input ring,
 *          reports each focus and each reason's first drop (BE_MVP:16 and
 *          :17), re-arms its timer for the next poll, never past the
 *          budget's end, and prints the run's input accounting
 *          (BE_MVP:18) before BE_MVP:13. Any other image never reads the
 *          firmware console. Since M9 (planning/mvp-m9-plan.md, D-1 and
 *          D-2; mvp/docs/log-profile.md, the Beryllium log profile version
 *          1), every image keeps the measurement log after the placement
 *          (a probe image after its stub's): hart 0 records, in the
 *          profile's order, the five ranges of its own text and constants
 *          as loaded (R2, a self-report, gating nothing), the sealed
 *          configuration's core identity and console grants and the
 *          image's configuration and policy identities or policy-absent
 *          (R3), and each domain's kernel and device tree as placed, and
 *          anchor's secret page (R4), extending one register per stream
 *          with the measured records' digests; after each domain's last
 *          launch record it compares the domain's register with the
 *          image's expected launch register (the gate, BE_MVP:06 LAUNCH);
 *          then it closes the log with the image's expected count, prints
 *          the page (BE_MVP:19 LOG) and the registers (BE_MVP:20
 *          REGISTERS), and only then publishes the blocks; a failed gate
 *          prints the block and fails measurement, an overflow or a page
 *          that cannot close prints it and fails log, and no domain hart
 *          starts. The registers are printed again before the run's
 *          terminal line.
 * Trust:   privileged restricted-C orchestration. Every CSR access, the
 *          fences, the HS wfi, and the SRET tail stay in assembly; every
 *          hgatp write and hfence.gvma stays in the accepted R3 functions,
 *          which hart 0 calls only to reset its own state, writing hgatp
 *          Bare (no root is published on hart 0); the HS-to-M SBI calls
 *          go only through the accepted platform helpers and
 *          be_mvp_fw_call, both through the accepted be_r3_arch_sbi_call.
 *          This runtime reaches each of these effects only through the
 *          executor (mvp-executor.c; planning/mvp-m6-plan.md, D-5) and
 *          performs none itself.
 *          After the barrier, hart 0 writes a domain hart's block only
 *          through its own three ring views: the inbound and input rings'
 *          bytes and heads, and the outbound ring's tail; nothing else.
 *          The log page, its registers, and the secret's source stay in
 *          hart 0's data in the MVP region, which no root maps; no domain
 *          hart's code names them, nor the sealed grants, the management
 *          state, or the console input's routing; hart 0 alone writes the
 *          page and the registers, and only before the barrier (I19).
 * Scope:   two Linux domains, each on its own hart under static ownership,
 *          hart 0 the control hart (planning/mvp-m0-plan.md). R4/R5 are not
 *          linked, nor, since M6, the fixed profile, the accepted R2
 *          backend, its fixture roots, or the fixture guest code: no
 *          management binding is prepared or published. In the probe
 *          images (mvp-probe.h),
 *          the probe module replaces the payload checks, the placement, and
 *          the control loop, and only domain 0's hart is started.
 */
#include "mvp-platform.h"

#include "mvp-core.h"
#include "mvp-executor.h"
#include "mvp-log.h"
#include "mvp-payload-layout.h"
#include "mvp-ring.h"
#include "mvp-sbi.h"
#include "mvp-scenario.h"
#include "mvp-sha256.h"
#include "r0-layout.h"
#include "r0-sbi.h"
#if defined(BE_MVP_PROBE_IMAGE)
#include "mvp-probe.h"
#if BE_MVP_PROBE_IMAGE == BE_MVP_PROBE_PLATFORM
#define BE_MVP_RUN_PROBE_PLATFORM	1
#endif
#endif

/*
 * The scenario's header (planning/mvp-m2-plan.md, Q12): a v3 header
 * declares pages, BE_MVP_SCENARIO_PAGES, in place of a v2 header's
 * channel; a v1 header declares no channel.
 */
#if defined(BE_MVP_SCENARIO_PAGES)
#define BE_MVP_RUN_PAGES		1
#define BE_MVP_RUN_CHANNELS		0
#else
#define BE_MVP_RUN_PAGES		0
#define BE_MVP_RUN_CHANNELS		BE_MVP_SCENARIO_CHANNELS
#endif

_Static_assert(sizeof(struct be_mvp_controls) == 128U,
	       "assembly controls size mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_controls, hip) == 0U,
	       "assembly controls hip offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_controls, hstatus) == 8U,
	       "assembly controls hstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_controls, hedeleg) == 16U,
	       "assembly controls hedeleg offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_controls, henvcfg) == 64U,
	       "assembly controls henvcfg offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_controls, vstimecmp) == 80U,
	       "assembly controls vstimecmp offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_controls, sstatus) == 96U,
	       "assembly controls sstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_controls, vsatp) == 112U,
	       "assembly controls vsatp offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_controls, sscratch) == 120U,
	       "assembly controls sscratch offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_exit, hstatus) == 320U,
	       "assembly exit hstatus offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_exit, htinst) == 328U,
	       "assembly exit htinst offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_exit, vsatp) == 336U,
	       "assembly exit vsatp offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_exit, time) == 344U,
	       "assembly exit time offset mismatch");
_Static_assert(__builtin_offsetof(struct be_mvp_exit, vsstatus) == 352U,
	       "assembly exit vsstatus offset mismatch");
_Static_assert(BE_MVP_INJECT_VSCAUSE == 0U && BE_MVP_INJECT_VSTVAL == 1U &&
	       BE_MVP_INJECT_VSEPC == 2U && BE_MVP_INJECT_VSSTATUS == 3U &&
	       BE_MVP_INJECT_WORDS == 4U,
	       "assembly injection readback order mismatch");
_Static_assert(BE_MVP_VCSR_COUNT == 11U && BE_MVP_VCSR_VSSTATUS == 0 &&
	       BE_MVP_VCSR_VSTIMECMP == 8 && BE_MVP_VCSR_SENVCFG == 10,
	       "assembly per-domain CSR order mismatch");
_Static_assert(BE_MVP_CLASS_EXCEPTION == 11, "assembly class moved");
_Static_assert(BE_MVP_CLASS_RESUME == 14, "assembly class moved");
_Static_assert(BE_MVP_HSTATUS_GUEST_CONTROLS == BE_U64_C(0x180),
	       "assembly hstatus guest controls mismatch");
_Static_assert(BE_MVP_HSTATUS_CLEARED_TRAPS == BE_U64_C(0x700000),
	       "assembly hstatus virtual traps mismatch");
_Static_assert(BE_MVP_HSTATUS_RESUME_MASK == BE_U64_C(0x73f280) &&
	       BE_MVP_HSTATUS_RESUME_CONTROLS == BE_U64_C(0x80),
	       "assembly hstatus resume controls mismatch");
_Static_assert(BE_R3_HSTATUS_CONTROL_MASK == BE_U64_C(0x73f380),
	       "assembly hstatus mask mismatch");
_Static_assert(BE_MVP_SSTATUS_CONTROL_MASK == BE_U64_C(0xde722),
	       "assembly sstatus mask mismatch");
_Static_assert(BE_MVP_SSTATUS_SPP == BE_MVP_HSTATUS_SPVP,
	       "the tail sets SPP from SPVP in the same bit");
#if defined(BE_MVP_CHERI) && !defined(BE_MVP_VARIANT_CHERI_FAULT_HS)
/* beryllium-cheri: the CHERI-aware monitor's arming values. */
_Static_assert(BE_MVP_HEDELEG == BE_U64_C(0x1000b15d),
	       "assembly hedeleg mismatch");
_Static_assert(BE_MVP_HENVCFG_ARMED == BE_U64_C(0x8000000010000000),
	       "assembly armed henvcfg mismatch");
#else
_Static_assert(BE_MVP_HEDELEG == BE_U64_C(0xb15d),
	       "assembly hedeleg mismatch");
#endif
_Static_assert(BE_MVP_SIE_SSIE == BE_U64_C(0x2) &&
	       BE_MVP_SIE_CONTROL == BE_U64_C(0x22) &&
	       BE_MVP_HVIP_VS_BITS == BE_U64_C(0x444),
	       "assembly sie and hvip mismatch");
/* mvp-trap.S and mvp-hartentry.S test an offset from the region's start
 * by these shifts. */
_Static_assert(BE_MVP_HART_REGION_BYTES == BE_U64_C(1) << 17 &&
	       BE_MVP_BLOCK_BYTES == BE_U64_C(1) << 16,
	       "assembly hart-region shifts mismatch");
_Static_assert(sizeof(struct be_mvp_hart_page) <= BE_MVP_BLOCK_STATE_BYTES,
	       "a domain hart's state page holds its views");
_Static_assert(sizeof(struct be_mvp_exit) <= BE_MVP_BLOCK_SAVED_BYTES,
	       "the exit record fits the saved page");
/* tests/check-image.py reads these from the linked image. */
_Static_assert(sizeof(struct be_mvp_payload_layout) == 64U,
	       "image checker payload layout size mismatch");
_Static_assert(sizeof(struct be_mvp_binding) == 24U,
	       "image checker binding size mismatch");
/* The generated payload layout keeps every budget (stop condition 3). */
_Static_assert(BE_MVP_PAYLOAD_KERNEL_BYTES >= BE_MVP_KERNEL_HEADER_BYTES &&
	       BE_MVP_PAYLOAD_KERNEL_BYTES <= BE_MVP_KERNEL_FILE_MAX,
	       "kernel file outside its budget");
_Static_assert(BE_MVP_PAYLOAD_KERNEL_IMAGE_SIZE >=
	       BE_MVP_PAYLOAD_KERNEL_BYTES &&
	       BE_MVP_PAYLOAD_KERNEL_IMAGE_SIZE <= BE_MVP_KERNEL_IMAGE_SIZE_MAX,
	       "kernel image_size outside its budget");
_Static_assert(BE_MVP_KERNEL_GPA + BE_MVP_PAYLOAD_KERNEL_IMAGE_SIZE <=
	       BE_MVP_DTB_GPA, "kernel span reaches the DTB slot");
_Static_assert(BE_MVP_PAYLOAD_DTB0_OFFSET ==
	       ((BE_MVP_BOOT_KERNEL_OFFSET + BE_MVP_PAYLOAD_KERNEL_BYTES +
		 BE_MVP_PAYLOAD_ALIGN - 1U) & ~(BE_MVP_PAYLOAD_ALIGN - 1U)),
	       "G0's DTB does not follow the kernel at 4 KiB");
_Static_assert(BE_MVP_PAYLOAD_DTB1_OFFSET ==
	       BE_MVP_PAYLOAD_DTB0_OFFSET + BE_MVP_DTB_BYTES,
	       "G1's DTB does not follow G0's");
_Static_assert(BE_MVP_PAYLOAD_IMAGE_BYTES ==
	       BE_MVP_PAYLOAD_DTB1_OFFSET + BE_MVP_DTB_BYTES,
	       "G1's DTB does not end the boot image");
_Static_assert(BE_MVP_PAYLOAD_IMAGE_BYTES <= BE_MVP_BOOT_IMAGE_MAX,
	       "boot image outside its budget");
_Static_assert(BE_MVP_POOL_HPA + BE_MVP_POOL_BYTES <= BE_MVP_STAGING_HPA,
	       "the pool ends below the staged image");

/*
 * The QEMU-only variants' compile-time switches (planning/mvp-m0-plan.md,
 * Negative images): ring-full shrinks both outbound rings and delays hart
 * 0's first LINE drain (Plan revision M0-A.3); hart-start names hart 9,
 * which the platform lacks, for domain 1. mvp.h holds the exit-budget and
 * run-timeout switches.
 */
#if defined(BE_MVP_VARIANT_RING_FULL)
#define BE_MVP_RUN_OUTBOUND_BYTES	BE_MVP_VARIANT_OUTBOUND_RING_BYTES
#else
#define BE_MVP_RUN_OUTBOUND_BYTES	BE_MVP_OUTBOUND_RING_BYTES
#endif
#define BE_MVP_RUN_DOMAIN0_HART		BE_MVP_SCENARIO_DOMAIN0_HART
/*
 * The probe images (planning/mvp-m0-plan.md, Platform record) start domain
 * 0's hart only, for the VS probe stub; both roots are built and both
 * blocks published, as in the scenario.
 */
#if defined(BE_MVP_PROBE_IMAGE)
#define BE_MVP_RUN_DOMAINS		1U
#else
#define BE_MVP_RUN_DOMAINS		BE_MVP_DOMAINS
#endif
#if defined(BE_MVP_VARIANT_HART_START)
#define BE_MVP_RUN_DOMAIN1_HART		BE_MVP_VARIANT_HART_START_HART
#else
#define BE_MVP_RUN_DOMAIN1_HART		BE_MVP_SCENARIO_DOMAIN1_HART
#endif
/*
 * anchor's no-grant-check variant (planning/mvp-m2-plan.md, Q10): hart 0
 * decides each management request without consulting the sealed grants,
 * so it delivers every well-formed one whose target's state allows it;
 * its run budget is mvp.h's.
 */
#if defined(BE_MVP_VARIANT_NO_GRANT_CHECK)
#define BE_MVP_RUN_GRANT_CHECK		0
#else
#define BE_MVP_RUN_GRANT_CHECK		1
#endif

/* The staged payload, as generated from the pinned payload files. */
const struct be_mvp_payload_layout be_mvp_payload_layout = {
	.staging_hpa = BE_MVP_STAGING_HPA,
	.kernel_offset = BE_MVP_BOOT_KERNEL_OFFSET,
	.kernel_bytes = BE_MVP_PAYLOAD_KERNEL_BYTES,
	.kernel_image_size = BE_MVP_PAYLOAD_KERNEL_IMAGE_SIZE,
	.dtb_offset = { BE_MVP_PAYLOAD_DTB0_OFFSET, BE_MVP_PAYLOAD_DTB1_OFFSET },
	.dtb_bytes = BE_MVP_DTB_BYTES,
	.image_bytes = BE_MVP_PAYLOAD_IMAGE_BYTES,
};

/* Each domain's hart, VMID, and root: the scenario's (mvp-scenario.h). */
const struct be_mvp_binding be_mvp_bindings[BE_MVP_DOMAINS] = {
	{ BE_MVP_RUN_DOMAIN0_HART, BE_MVP_SCENARIO_DOMAIN0_VMID,
	  BE_MVP_SCENARIO_DOMAIN0_ROOT },
	{ BE_MVP_RUN_DOMAIN1_HART, BE_MVP_SCENARIO_DOMAIN1_VMID,
	  BE_MVP_SCENARIO_DOMAIN1_ROOT },
};

/* Each domain's window, pool, VMID, and hart (mvp-layout.h). */
static const struct be_mvp_gstage_desc be_mvp_descs[BE_MVP_DOMAINS] = {
	{ .gpa_base = BE_MVP_GUEST_GPA, .hpa_base = BE_MVP_G0_HPA,
	  .size = BE_MVP_GUEST_BYTES, .pool_pa = BE_MVP_G0_ROOT_HPA,
	  .vmid = BE_MVP_G0_VMID, .hart = BE_MVP_RUN_DOMAIN0_HART },
	{ .gpa_base = BE_MVP_GUEST_GPA, .hpa_base = BE_MVP_G1_HPA,
	  .size = BE_MVP_GUEST_BYTES, .pool_pa = BE_MVP_G1_ROOT_HPA,
	  .vmid = BE_MVP_G1_VMID, .hart = BE_MVP_RUN_DOMAIN1_HART },
};
static const be_u64 be_mvp_hgatps[BE_MVP_DOMAINS] = {
	BE_MVP_G0_HGATP, BE_MVP_G1_HGATP,
};
/*
 * The sealed channel record (mvp-scenario.h; planning/mvp-m1-plan.md, Q1),
 * all zero in a scenario without a channel, and the configuration identity
 * tools/policy-check.py computed (Q9), which is not a measurement. The
 * image checker matches both to the scenario's authority report.
 */
#if BE_MVP_RUN_PAGES
/*
 * A scenario with pages (planning/mvp-m2-plan.md, Q1) links no channel
 * record: each domain hart's block carries its root's walked leaves for
 * every declared page, and hart 0's control loop checks DENIAL records
 * against the sealed pages.
 */
_Static_assert(BE_MVP_SCENARIO_PAGES >= 1 &&
	       BE_MVP_SCENARIO_PAGES <= BE_MVP_PAGES_MAX,
	       "the scenario declares one to three pages");
/*
 * The secret page ends the measured domain's launch records, stream 3
 * (mvp/docs/log-profile.md, 2.7 and 3.1): the measured domain is domain 1.
 */
_Static_assert(BE_MVP_SCENARIO_SECRET_PAGE < BE_MVP_SCENARIO_PAGES &&
	       BE_MVP_SCENARIO_MEASURED_DOMAIN == 1U,
	       "the secret page is a declared page and the measured domain "
	       "domain 1");
/*
 * The sealed pages; and the secret hart 0 writes into the secret page,
 * the rest of the page zero. The image checker finds both, and the
 * configuration identity, in .mvp.rodata.
 */
static const struct be_mvp_gstage_page be_mvp_pages[BE_MVP_SCENARIO_PAGES] =
	BE_MVP_SCENARIO_PAGE_INITIALIZER;
static const be_u8 be_mvp_secret[BE_MVP_SECRET_BYTES] =
	BE_MVP_SCENARIO_SECRET;
#else
static const struct be_mvp_gstage_channel be_mvp_channel =
	BE_MVP_SCENARIO_CHANNEL_INITIALIZER;
#endif
#if BE_MVP_RUN_CHANNELS || BE_MVP_RUN_PAGES
static const be_u8 be_mvp_config_identity[32] =
	BE_MVP_SCENARIO_CONFIG_IDENTITY;
#endif
/*
 * The measurement log (mvp/docs/log-profile.md; planning/mvp-m9-plan.md,
 * D-1 to D-3). The image's pre-link constants, tools/gen-scenario.py's
 * (the scenario's digest, the configuration and policy identities, each
 * domain's expected launch register, the expected count, the sequence,
 * and the R2 switch), in .mvp.rodata, where the image checker finds and
 * matches them; the record sequence (3.1) the image's scenario gives, a
 * probe image's its own.
 */
static const struct be_mvp_log_constants be_mvp_log_constants = {
	.scenario = BE_MVP_LOG_SCENARIO_SHA256,
	.configuration = BE_MVP_LOG_CONFIGURATION_SHA256,
	.policy = BE_MVP_LOG_POLICY_SHA256,
	.launch = { BE_MVP_LAUNCH_REGISTER_0, BE_MVP_LAUNCH_REGISTER_1 },
	.count = BE_MVP_LOG_EXPECTED_COUNT,
	.sequence = BE_MVP_LOG_SEQUENCE,
	.r2 = BE_MVP_LOG_R2,
};
#if defined(BE_MVP_PROBE_IMAGE)
#define BE_MVP_RUN_LOG_SEQUENCE		4U
#define BE_MVP_RUN_LOG_POLICY		0
#elif BE_MVP_RUN_PAGES
#define BE_MVP_RUN_LOG_SEQUENCE		3U
#define BE_MVP_RUN_LOG_POLICY		1
#elif BE_MVP_RUN_CHANNELS
#define BE_MVP_RUN_LOG_SEQUENCE		2U
#define BE_MVP_RUN_LOG_POLICY		1
#else
#define BE_MVP_RUN_LOG_SEQUENCE		1U
#define BE_MVP_RUN_LOG_POLICY		0
#endif
_Static_assert(BE_MVP_LOG_SEQUENCE == BE_MVP_RUN_LOG_SEQUENCE &&
	       (BE_MVP_LOG_R2 == 0U || BE_MVP_LOG_R2 == 1U) &&
	       BE_MVP_LOG_EXPECTED_COUNT <= 15U &&
	       BE_MVP_LOG_EXPECTED_COUNT < BE_MVP_LOG_CAPACITY,
	       "the generator's sequence is the image's, and its expected "
	       "count at most fifteen (planning/mvp-m9-plan.md, stop 6)");
/*
 * The page and the registers (2.1, 2.6): hart 0's own, in the MVP
 * region's BSS, zero from clear_mvp_bss(), the page 4 KiB aligned;
 * written only by measure_log() before any domain hart starts, read by
 * hart 0 alone (I19), and named by no code a domain hart runs (the image
 * checker's rule). Beside them, the hashing total and the terminal
 * registers line, rendered once at the barrier, which hart 0's terminal
 * path prints and the domain harts' reach only as text.
 */
static be_u8 be_mvp_log[BE_MVP_LOG_PAGE_BYTES]
	__attribute__((aligned(BE_MVP_LOG_PAGE_BYTES)));
static be_u8 be_mvp_log_registers[BE_MVP_LOG_REGISTERS_BYTES];
static be_u64 be_mvp_log_ticks;
static struct be_mvp_line be_mvp_log_terminal;
/* The core identity seal_config() computed and CONFIG_SEALED printed. */
static be_u8 be_mvp_sealed_identity[BE_MVP_SHA256_BYTES];
#if BE_MVP_RUN_ACCEPT_MGMT
/*
 * The management extension (planning/mvp-m2-plan.md, "The management
 * extension"): the sealed manifest's grants, which the image checker
 * matches to the scenario's authority report, and hart 0's management
 * state, the pending requests, in the MVP region's BSS. Hart 0 alone reads
 * the grants and writes and reads the state, through its control loop; no
 * code a domain hart runs names either (the image checker's rule).
 */
static const struct be_mvp_mgmt_grant be_mvp_grants[BE_MVP_SCENARIO_GRANTS] =
	BE_MVP_SCENARIO_GRANT_INITIALIZER;
static struct be_mvp_mgmt_state be_mvp_mgmt_state;
_Static_assert(BE_MVP_SCENARIO_GRANTS <= BE_MVP_MGMT_GRANTS_MAX,
	       "the scenario's grants fit hart 0's table");
#endif

static struct be_runtime be_mvp_runtime = BE_RUNTIME_INITIALIZER;
/*
 * The G-stage builder's inputs, from the derived roots alone (mvp-core.c;
 * planning/mvp-m6-plan.md, D-2): each domain's window, pool, VMID, and
 * hart, and the pages with each domain's rights, or M1's channel record
 * made of its one page; checked at the seal to be what the image links,
 * and from then the only records the builder, its checks, the pages' and
 * channel page's placement, the measurement, and the control loop take.
 */
static struct be_mvp_gstage_desc be_mvp_sealed_descs[BE_MVP_DOMAINS];
static struct be_mvp_gstage_page be_mvp_sealed_pages[BE_MVP_PAGES_MAX];
#if !BE_MVP_RUN_PAGES
static struct be_mvp_gstage_channel be_mvp_sealed_channel;
#endif
static struct be_r3_state be_mvp_r3_control = BE_R3_STATE_INITIALIZER;
static struct be_r3_image_layout be_mvp_layout;
static struct be_r3_hs_state be_mvp_hs;
static struct be_mvp_gstage_map be_mvp_maps[BE_MVP_DOMAINS];
/*
 * Each root's walked leaves of its pages, which each domain hart's block
 * carries for the denial decision: the declared pages' in a scenario with
 * pages; else M1's channel leaf as page 0, all zero without a channel.
 */
static struct be_mvp_gstage_leaves be_mvp_page_leaves[BE_MVP_DOMAINS];
#if !BE_MVP_RUN_PAGES
static struct be_mvp_gstage_leaf be_mvp_leaves[BE_MVP_DOMAINS];
#endif
static struct be_mvp_payload_plan be_mvp_plans[BE_MVP_DOMAINS];
/* Hart 0's control loop and its own views of each domain's three rings. */
static struct be_mvp_control be_mvp_ctl;
static struct be_mvp_ring be_mvp_inbound[BE_MVP_DOMAINS];
static struct be_mvp_ring be_mvp_outbound[BE_MVP_DOMAINS];
static struct be_mvp_ring be_mvp_input_rings[BE_MVP_DOMAINS];
#if !defined(BE_MVP_PROBE_IMAGE)
/*
 * Console input (planning/mvp-m7-plan.md, D-1, D-3, and D-4): hart 0's
 * routing and accounting, and the buffer it reads the firmware console
 * into, in the MVP region's BSS. Hart 0 alone names them, and arms them
 * only in an image whose sealed configuration grants console input.
 */
static struct be_mvp_input be_mvp_console_in;
static be_u8 be_mvp_console_in_buffer[BE_MVP_INPUT_READ_BYTES];
#endif
static struct be_mvp_record be_mvp_record;
static struct be_mvp_line be_mvp_line;
static struct be_mvp_line be_mvp_detail;
#if !defined(BE_MVP_PROBE_IMAGE)
static char be_mvp_console_out[BE_MVP_PRINT_LINE_BYTES];
#endif
static be_u32 be_mvp_terminal_entered;

/* The MVP's boot (planning/mvp-m6-plan.md, D-3, Q2): the accepted boot
 * check, then the sealed configuration, its identity's first eight bytes
 * following as 16 hex digits. */
static const char marker_boot[] = "BE_MVP:00 BOOT_VALIDATED\n";
static const char marker_sealed[] = "BE_MVP:00 CONFIG_SEALED inventory=%d "
	"authorities=%d roots=%d harts=%d,%d,%d identity=";
/* The MVP lines (planning/mvp-m0-plan.md, Markers), one format each. */
#if defined(BE_MVP_PROBE_IMAGE)
static const char marker_scenario[] = "BE_MVP:01 SCENARIO name="
	BE_MVP_PROBE_NAME " domains=%d harts=%d,%d of=%d ring_bytes=%x "
	"mvp_region=%x mvp_bytes=%x image_bytes=%x";
#if defined(BE_MVP_RUN_PROBE_PLATFORM)
static const char marker_probe_hsm[] = "BE_MVP:PROBE hsm status=";
#endif
#else
static const char marker_scenario[] = "BE_MVP:01 SCENARIO name="
	BE_MVP_SCENARIO_NAME " domains=%d harts=%d,%d,%d of=%d ring_bytes=%x "
	"mvp_region=%x mvp_bytes=%x image_bytes=%x";
#endif
static const char marker_firmware[] =
	"BE_MVP:02 FIRMWARE_PROBED hsm=%d ipi=%d status=";
static const char marker_gstage[] = "BE_MVP:03 GSTAGE_BUILT_REWALKED "
	"domain=%d hart=%d gpa=%x hpa=%x size=%x leaves=%d root=%x vmid=%d";
static const char marker_cleared[] =
	"BE_MVP:05 DOMAIN_RAM_CLEARED domain=%d gpa=%x size=%x ticks=%x";
#if BE_MVP_RUN_CHANNELS
/* The channel's lines (planning/mvp-m1-plan.md, Markers), once per
 * declared channel; the identity follows as 64 hex digits. */
static const char marker_channel[] = "BE_MVP:03 CHANNEL_CHECKED channel=0 "
	"writer=%d reader=%d gpa=%x hpa=%x bytes=%x level0=%x,%x "
	"writer_pte=%x reader_pte=%x config=";
static const char marker_channel_cleared[] =
	"BE_MVP:05 CHANNEL_CLEARED channel=0 hpa=%x bytes=%x ticks=%x";
static const char marker_detail_channel[] = "BE_MVP:DETAIL channel=0 "
	"domain=%d hart=%d walked=%x declared=%x";
#endif
#if BE_MVP_RUN_PAGES
/*
 * The pages' lines (planning/mvp-m2-plan.md, Markers): one PAGE_CHECKED
 * per page, a channel's in CHANNEL_CHECKED's form, a secret page's with
 * its one endpoint, the identity following as 64 hex digits; and one
 * PAGE_CLEARED per channel page and SECRET_PLACED for the secret page,
 * its address and size only.
 */
static const char marker_page_channel[] = "BE_MVP:03 PAGE_CHECKED page=%d "
	"kind=channel writer=%d reader=%d gpa=%x hpa=%x bytes=%x level0=%x,%x "
	"writer_pte=%x reader_pte=%x config=";
static const char marker_page_secret[] = "BE_MVP:03 PAGE_CHECKED page=%d "
	"kind=secret reader=%d gpa=%x hpa=%x bytes=%x level0=%x,%x "
	"reader_pte=%x config=";
static const char marker_page_cleared[] =
	"BE_MVP:05 PAGE_CLEARED page=%d hpa=%x bytes=%x ticks=%x";
static const char marker_secret_placed[] =
	"BE_MVP:05 SECRET_PLACED page=%d hpa=%x bytes=%x ticks=%x";
static const char marker_detail_page[] = "BE_MVP:DETAIL page=%d domain=%d "
	"hart=%d walked=%x declared=%x";
#endif
#if !defined(BE_MVP_PROBE_IMAGE)
/*
 * Each domain's gate (mvp/docs/log-profile.md, 4.8): LAUNCH with its
 * launch register as 64 hex digits and its hashing ticks; or a failed
 * gate's DETAIL, the register computed and the image's expected value.
 */
static const char marker_launch[] =
	"BE_MVP:06 LAUNCH domain=%d hart=%d register=";
static const char marker_launch_match[] = " expected=match ticks=%x";
static const char marker_detail_measurement[] =
	"BE_MVP:DETAIL domain=%d hart=%d computed=";
static const char marker_detail_expected[] = " expected=";
static const char marker_payload[] =
	"BE_MVP:04 PAYLOAD_CHECKED kernel_bytes=%x image_size=%x";
static const char marker_placed[] = "BE_MVP:06 PAYLOAD_PLACED domain=%d "
	"kernel=%x kernel_bytes=%x image_size=%x dtb=%x dtb_bytes=%x ticks=%x";
#endif
static const char marker_published[] = "BE_MVP:07 BLOCKS_PUBLISHED "
	"region=%x bytes=%x generation=%d budget_ticks=%x";
static const char marker_started[] = "BE_MVP:08 HART_STARTED hart=%d "
	"domain=%d result=%i status=%i ticks=%x";
static const char marker_ready[] = "BE_MVP:09 HART_READY hart=%d domain=%d "
	"hgatp=%x hstatus_controls=%x hedeleg=%x hideleg=%x hcounteren=%x "
	"sie=%x henvcfg=%x vstimecmp=%x";
static const char marker_entered[] = "BE_MVP:10 DOMAIN_ENTERED hart=%d "
	"domain=%d pc=%x a0=%x a1=%x ticks=%x";
#if !defined(BE_MVP_PROBE_IMAGE)
static const char marker_ipi[] = "BE_MVP:11 IPI_PROBE hart=%d domain=%d "
	"sent=%x received=%x answered=%x spv=%d";
static const char marker_domain_shutdown[] = "BE_MVP:12 DOMAIN_SHUTDOWN "
	"hart=%d domain=%d exits=%d sbi=%d ipi=%d base=%d time=%d "
	"dbcn_write=%d dbcn_read=%d dbcn_byte=%d srst=%d refused=%d lines=%d "
	"ring_peak=%x entered=%x ticks=%x";
static const char marker_complete[] = "BE_MVP:13 RUN_COMPLETE domains=%d "
	"records=%d wakes=%d idle_ticks=%x overlap_ticks=%x ticks=%x";
/*
 * Console input's lines (planning/mvp-m7-plan.md, D-4), only in an image
 * that grants console input: armed, with the granted domains and the
 * prefix; each focus; each reason's first drop; and, before BE_MVP:13,
 * the bytes read, each domain's delivered bytes and their SHA-256's first
 * 16 hex digits, and each reason's drops, or none.
 */
static const char marker_input_armed[] = "BE_MVP:15 INPUT_ARMED grants=";
static const char marker_input_grant[] = "g%d";
static const char marker_input_grant_next[] = ",g%d";
static const char marker_input_prefix[] = " prefix=%x";
static const char marker_focus[] = "BE_MVP:16 FOCUS g%d";
static const char marker_focus_none[] = "BE_MVP:16 FOCUS none\n";
static const char marker_input_drop[] = "BE_MVP:17 INPUT_DROP ";
static const char marker_input[] = "BE_MVP:18 INPUT read=%d";
static const char marker_input_domain[] = " g%d=%d:";
static const char marker_input_dropped[] = " dropped=";
static const char marker_input_count[] = ":%d";
static const char marker_input_next[] = ",";
static const char marker_input_none[] = "none";
#if BE_MVP_RUN_ACCEPT_DENIAL
/* One accepted denial (planning/mvp-m1-plan.md, Markers): the kind's name
 * follows the sequence number. */
static const char marker_denial[] =
	"BE_MVP:DENY hart=%d domain=%d seq=%d kind=";
static const char marker_denial_values[] = " cause=%x injected=%x gpa=%x "
	"htval=%x htinst=%x stval=%x sepc=%x vsstatus=%x vstvec=%x ticks=%x "
	"service=%x";
static const char marker_kind_unmapped[] = "unmapped";
static const char marker_kind_read_only[] = "read-only";
#endif
#if BE_MVP_RUN_ACCEPT_MGMT
/*
 * One management request (planning/mvp-m2-plan.md, Markers): the
 * requester's hart and domain, its sequence number, the function by name,
 * the target as the guest named it, the signed result, the target's state
 * after the transition the request caused, or - for none, the request's
 * ticks since the barrier, and the service, the answer's time minus the
 * request's; and each transition of a domain, the terminated one's with
 * its launch register (planning/mvp-m9-plan.md, D-9).
 */
static const char marker_mgmt[] =
	"BE_MVP:MGMT hart=%d domain=%d seq=%d fid=";
static const char marker_mgmt_values[] = " target=%d result=%i target_state=";
static const char marker_mgmt_ticks[] = " ticks=%x service=%x";
static const char marker_fid_pause[] = "pause";
static const char marker_fid_terminate[] = "terminate";
static const char *const marker_target_state[BE_MVP_TARGET_COUNT + 1U] = {
	[BE_MVP_TARGET_RUNNING] = "running",
	[BE_MVP_TARGET_PAUSED] = "paused",
	[BE_MVP_TARGET_TERMINATED] = "terminated",
	[BE_MVP_TARGET_SHUTDOWN] = "shutdown",
	[BE_MVP_TARGET_PENDING] = "pending",
	[BE_MVP_TARGET_COUNT] = "-",
};
static const char marker_domain_paused[] = "BE_MVP:12 DOMAIN_PAUSED "
	"hart=%d domain=%d by=%d exits=%d ticks=%x";
static const char marker_domain_terminated[] = "BE_MVP:12 DOMAIN_TERMINATED "
	"hart=%d domain=%d by=%d exits=%d sha256=";
static const char marker_terminated_ticks[] = " ticks=%x";
#endif
#endif
static const char marker_shutdown[] = "BE_MVP:14 SHUTDOWN type=0 reason=0\n";
static const char marker_failure[] = "BE_MVP:FAIL ";
/* Hart 0's own DETAIL lines; a domain's come from be_mvp_detail_line(). */
static const char marker_status_first[] = "%d:%i";
static const char marker_status_next[] = ",%d:%i";
static const char marker_started_hart[] = " started=%d";
static const char marker_started_none[] = " started=none";
static const char marker_detail_henvcfg[] = "BE_MVP:DETAIL henvcfg=%x";
static const char marker_detail_domain[] = "BE_MVP:DETAIL domain=%d hart=%d";
static const char marker_detail_start[] = "BE_MVP:DETAIL domain=%d hart=%d "
	"result=%i status=%i ticks=%x";
static const char marker_detail_waited[] =
	"BE_MVP:DETAIL domain=%d hart=%d ticks=%x";
static const char marker_detail_record[] =
	"BE_MVP:DETAIL domain=%d hart=%d record=%d";
static const char marker_detail_ticks[] = "BE_MVP:DETAIL ticks=%x";
/* A domain's DETAIL forms, by the length of its FAIL detail. */
static const char marker_detail_exit[] = " cause=%x pc=%x tval=%x htval=%x "
	"htinst=%x spvp=%d vsatp=%x exits=%d";
static const char marker_detail_controls[] = " hgatp=%x "
	"hstatus_controls=%x hedeleg=%x hideleg=%x hcounteren=%x sie=%x "
	"henvcfg=%x vstimecmp=%x";
static const char marker_detail_register[] = " register=";
static const char marker_detail_values[] = " wanted=%x readback=%x";
static const char marker_register_henvcfg[] = "henvcfg";
static const char marker_register_hgatp[] = "hgatp";
static const char marker_srst[] = "BE_MVP:SRST_RETURNED\n";
static const char marker_newline[] = "\n";

/*
 * What each drained record prints after its hart and domain: one byte per
 * value, a payload word's index, the record's time, or the sum of the SBI
 * call classes, each as ticks since the barrier when marked.
 */
#define VALUE_TIME			0x20U
#define VALUE_SBI			0x21U
#define VALUE_SINCE			0x40U
#define VALUE_END			0xffU
static const be_u8 values_ready[] = {
	BE_MVP_READY_HGATP, BE_MVP_READY_HSTATUS, BE_MVP_READY_HEDELEG,
	BE_MVP_READY_HIDELEG, BE_MVP_READY_HCOUNTEREN, BE_MVP_READY_SIE,
	BE_MVP_READY_HENVCFG, BE_MVP_READY_VSTIMECMP, VALUE_END,
};
static const be_u8 values_entered[] = {
	BE_MVP_ENTERED_PC, BE_MVP_ENTERED_A0, BE_MVP_ENTERED_A1,
	VALUE_TIME | VALUE_SINCE, VALUE_END,
};
#if !defined(BE_MVP_PROBE_IMAGE)
static const be_u8 values_pong[] = {
	BE_MVP_PONG_SENT | VALUE_SINCE, BE_MVP_PONG_RECEIVED | VALUE_SINCE,
	VALUE_TIME | VALUE_SINCE, BE_MVP_PONG_SPV, VALUE_END,
};
static const be_u8 values_shutdown[] = {
	BE_MVP_SHUTDOWN_EXITS, VALUE_SBI, BE_MVP_SHUTDOWN_IPI,
	BE_MVP_SHUTDOWN_BASE, BE_MVP_SHUTDOWN_TIME, BE_MVP_SHUTDOWN_DBCN_WRITE,
	BE_MVP_SHUTDOWN_DBCN_READ, BE_MVP_SHUTDOWN_DBCN_BYTE,
	BE_MVP_SHUTDOWN_SRST, BE_MVP_SHUTDOWN_REFUSED, BE_MVP_SHUTDOWN_LINES,
	BE_MVP_SHUTDOWN_RING_PEAK, BE_MVP_SHUTDOWN_ENTERED | VALUE_SINCE,
	VALUE_TIME | VALUE_SINCE, VALUE_END,
};
#if BE_MVP_RUN_ACCEPT_MGMT
static const be_u8 values_paused[] = {
	BE_MVP_PAUSED_BY, BE_MVP_PAUSED_EXITS, VALUE_TIME | VALUE_SINCE,
	VALUE_END,
};
#endif
#endif
_Static_assert(BE_MVP_SHUTDOWN_BASE == 1U && BE_MVP_SHUTDOWN_REFUSED == 7U &&
	       BE_MVP_SHUTDOWN_MGMT == 13U && BE_MVP_SHUTDOWN_DBCN_INPUT == 14U,
	       "the SBI call classes are SHUTDOWN's words 1 to 7, 13, and 14");

static be_u64 symbol_address(const be_u8 *symbol)
{
	return (be_u64)symbol;
}

/* The boot check's view of the image: its code, data, R1 input, BSS, and
 * diagnostic page, and the vector; the accepted fixture extents, which the
 * MVP's linker script no longer places, stay zero, and the ported check no
 * longer reads them (planning/mvp-m6-plan.md, D-3 and D-4). */
static void build_image_layout(struct be_r3_image_layout *layout)
{
	*layout = (struct be_r3_image_layout) {
		.entry = symbol_address(be_reset),
		.monitor_code_start = symbol_address(__be_monitor_code_start),
		.monitor_code_end = symbol_address(__be_monitor_code_end),
		.monitor_data_start = symbol_address(__be_monitor_data_start),
		.monitor_data_end = symbol_address(__be_monitor_data_end),
		.input_start = symbol_address(__be_input_start),
		.input_end = symbol_address(__be_input_end),
		.bss_start = symbol_address(__be_bss_start),
		.bss_end = symbol_address(__be_bss_end),
		.diagnostic_start = symbol_address(__be_diagnostic_start),
		.diagnostic_end = symbol_address(__be_diagnostic_end),
		.trap_vector = symbol_address(be_mvp_trap_vector),
	};
}

/*
 * The one formatter: fixed text with "%x" (hex), "%d" (decimal), and "%i"
 * (signed decimal) directives, each taking the next value.
 */
void be_mvp_line_format(struct be_mvp_line *line, const char *format,
			const be_u64 *values)
{
	char literal[2] = { '\0', '\0' };
	be_u64 index;

	for (index = 0U; index < BE_MVP_LINE_CAPACITY &&
			 format[index] != '\0'; ++index) {
		char kind = format[index + 1U];
		be_u64 value;

		if (format[index] != '%' ||
		    (kind != 'x' && kind != 'd' && kind != 'i')) {
			literal[0] = format[index];
			be_mvp_line_text(line, literal);
			continue;
		}
		value = *values++;
		++index;
		if (kind == 'x') {
			be_mvp_line_hex(line, value);
			continue;
		}
		if (kind == 'i' && (value >> 63) != 0U) {
			be_mvp_line_text(line, "-");
			value = 0U - value;
		}
		be_mvp_line_decimal(line, value);
	}
}

void be_mvp_detail_line(struct be_mvp_line *line, enum be_mvp_class failure,
			be_u64 domain, be_u64 hart, const be_u64 *detail,
			be_u64 words)
{
	be_u64 values[2] = { domain, hart };

	be_mvp_line_reset(line);
	be_mvp_line_format(line, marker_detail_domain, values);
	if (words == BE_MVP_DETAIL_REGISTER_WORDS) {
		be_mvp_line_text(line, marker_detail_register);
		if (detail[0] == BE_MVP_REGISTER_HENVCFG)
			be_mvp_line_text(line, marker_register_henvcfg);
		else if (detail[0] == BE_MVP_REGISTER_HGATP)
			be_mvp_line_text(line, marker_register_hgatp);
		else
			be_mvp_line_text(line, be_mvp_vcsr_name(
				(be_u32)(detail[0] - BE_MVP_REGISTER_VCSR)));
		be_mvp_line_format(line, marker_detail_values, &detail[1]);
	} else if (words == BE_MVP_DETAIL_EXIT_WORDS) {
		be_mvp_line_format(line, failure == BE_MVP_CLASS_CONTROLS ?
				   marker_detail_controls :
				   marker_detail_exit, detail);
	}
	be_mvp_line_text(line, marker_newline);
}

long be_mvp_send_ipi(be_u64 hart)
{
	be_u64 mask;
	be_u64 base;

	if (!be_mvp_ipi_target(hart, &mask, &base))
		return BE_MVP_SBI_ERR_INVALID_PARAM;
	return be_mvp_exec_send_ipi(mask, base);
}

/*
 * Monitor lines go straight to the firmware console: hart 0 is its only
 * steady-state writer, and each domain line is written whole.
 */
static enum be_r3_error write_text(const char *text)
{
	be_u64 length = be_r3_text_length(text);

	if (length > BE_PAGE_SIZE)
		return BE_R3_ERROR_DBCN_RANGE;
	return be_mvp_exec_console_write(text, length);
}

static enum be_r3_error write_line(struct be_mvp_line *line)
{
	if (line->overflow != 0U)
		return BE_R3_ERROR_DBCN_RANGE;
	return be_mvp_exec_console_write(line->text, line->length);
}

/* Ticks since the barrier, when hart 0's run budget started. */
static be_u64 since(be_u64 time)
{
	return time >= be_mvp_ctl.start ? time - be_mvp_ctl.start : 0U;
}

/*
 * The terminal registers line (mvp/docs/log-profile.md, 4.5), which
 * measure_log() rendered at the barrier: printed once, immediately before
 * hart 0's terminal line, BE_MVP:14 or its first BE_MVP:FAIL, and never
 * before the barrier's, when it is still empty.
 */
static void log_terminal(void)
{
	if (be_mvp_log_terminal.length != 0U)
		(void)write_line(&be_mvp_log_terminal);
	be_mvp_log_terminal.length = 0U;
}

/*
 * The single terminal path: report, request the accepted SRST shutdown
 * once, and halt. A failure while already terminal halts at once. A
 * failure that names a domain hart, or a firmware fact, adds the DETAIL
 * line its caller prepared. After the barrier, the terminal registers
 * line precedes the FAIL line.
 */
static void terminal(enum be_mvp_class failure, int request_reset)
	__attribute__((noreturn));
static void terminal(enum be_mvp_class failure, int request_reset)
{
	if (be_mvp_terminal_entered != 0U)
		be_mvp_exec_halt();
	be_mvp_terminal_entered = 1U;
	log_terminal();
	be_mvp_line_reset(&be_mvp_line);
	be_mvp_line_text(&be_mvp_line, marker_failure);
	be_mvp_line_text(&be_mvp_line, be_mvp_class_name(failure));
	be_mvp_line_text(&be_mvp_line, marker_newline);
	(void)write_line(&be_mvp_line);
	if (be_mvp_detail.length != 0U)
		(void)write_line(&be_mvp_detail);
	if (request_reset != 0)
		(void)be_mvp_exec_system_reset();
	(void)write_text(marker_srst);
	be_mvp_exec_halt();
}

void be_mvp_runtime_terminal(enum be_mvp_class failure)
{
	terminal(failure, 1);
}

/* A failure with one DETAIL line of hart 0's own. */
static void fail_detail(enum be_mvp_class failure, const char *format,
			const be_u64 *values) __attribute__((noreturn));
static void fail_detail(enum be_mvp_class failure, const char *format,
			const be_u64 *values)
{
	be_mvp_line_reset(&be_mvp_detail);
	be_mvp_line_format(&be_mvp_detail, format, values);
	be_mvp_line_text(&be_mvp_detail, marker_newline);
	terminal(failure, 1);
}

/* A domain's ring or IPI protocol broken, as hart 0 saw it. */
static void fail_domain(enum be_mvp_class failure, be_u32 domain,
			be_u64 type) __attribute__((noreturn));
static void fail_domain(enum be_mvp_class failure, be_u32 domain,
			be_u64 type)
{
	be_u64 values[3] = { domain, be_mvp_bindings[domain].hart, type };

	fail_detail(failure, marker_detail_record, values);
}

static void emit_text(const char *text)
{
	if (write_text(text) != BE_R3_ERROR_NONE)
		be_mvp_runtime_terminal(BE_MVP_CLASS_CONSOLE);
}

static void emit_line(void)
{
	be_mvp_line_text(&be_mvp_line, marker_newline);
	if (write_line(&be_mvp_line) != BE_R3_ERROR_NONE)
		be_mvp_runtime_terminal(BE_MVP_CLASS_CONSOLE);
}

static void line_start(const char *format, const be_u64 *values)
{
	be_mvp_line_reset(&be_mvp_line);
	be_mvp_line_format(&be_mvp_line, format, values);
}

static void emit(const char *format, const be_u64 *values)
{
	line_start(format, values);
	emit_line();
}

static void boot_fail(void) __attribute__((noreturn));
static void boot_fail(void)
{
	be_mvp_runtime_terminal(BE_MVP_CLASS_BOOT);
}

/*
 * The MVP region (Plan revision M0-A.1) holds every MVP static. The accepted
 * entry clears only the accepted BSS, so hart 0 first checks that the linked
 * region is the layout's and clears the region's BSS, before any MVP static
 * is used and long before the barrier publishes anything a domain hart
 * reads; a region other than the layout's fails closed.
 */
static void clear_mvp_bss(void)
{
	volatile be_u64 *word = (volatile be_u64 *)(void *)__be_mvp_bss_start;
	be_u64 start = symbol_address(__be_mvp_bss_start);
	be_u64 end = symbol_address(__be_mvp_bss_end);
	be_u64 region_end = symbol_address(__be_mvp_region_end);
	be_u64 index;

	if (symbol_address(__be_mvp_region_start) != BE_MVP_REGION_HPA ||
	    region_end > BE_MVP_REGION_HPA + BE_MVP_REGION_BYTES ||
	    start < BE_MVP_REGION_HPA || end < start || end > region_end ||
	    ((start | end) & (sizeof(be_u64) - 1U)) != 0U)
		boot_fail();
	for (index = 0U; index < (end - start) / sizeof(be_u64); ++index)
		word[index] = 0U;
}

static void line_hex(struct be_mvp_line *line, const be_u8 *bytes,
		     be_u64 count);

/*
 * The MVP core profile (planning/mvp-m6-plan.md, D-1 to D-3): the image's
 * inventory and proposal copied, validated, sealed, and derived through
 * the ported R1 mechanism; the G-stage builder's inputs taken from the
 * derived roots alone, which must be what the image links (each domain's
 * window, pool, VMID, and hart, its binding, and the pages or the
 * channel), and each derived root's console input grant 0 or 1
 * (planning/mvp-m7-plan.md, D-5); then BE_MVP:00 CONFIG_SEALED with the
 * inventory's and the sealed authorities' counts, the derived roots, the
 * control hart and the domains', and the identity (Q6), which hart 0
 * keeps for the log's core-identity record. Any failure fails closed,
 * boot, before any hart starts.
 */
static void seal_config(void)
{
	struct be_runtime *runtime = &be_mvp_runtime;
	be_u64 values[6];
	be_u64 count = 0U;
	be_u64 grants = 0U;
	be_u32 domain;
	int agree;

	if (be_runtime_copy_inventory(runtime, &be_mvp_inventory) !=
		    BE_RUNTIME_OK ||
	    be_runtime_copy_proposal(runtime, &be_mvp_proposal) !=
		    BE_RUNTIME_OK ||
	    be_runtime_validate(runtime) != BE_RUNTIME_OK ||
	    be_runtime_seal(runtime) != BE_RUNTIME_OK ||
	    be_runtime_derive(runtime) != BE_RUNTIME_OK ||
	    !be_mvp_core_gstage(&runtime->canonical, &runtime->enforcement,
				be_mvp_sealed_descs, be_mvp_sealed_pages,
				&count) ||
	    !be_mvp_core_console(&runtime->enforcement, &grants))
		boot_fail();
	agree = be_mvp_core_same(be_mvp_sealed_descs, be_mvp_descs,
				 sizeof(be_mvp_descs));
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		agree &= be_mvp_bindings[domain].hart ==
				 be_mvp_sealed_descs[domain].hart &&
			 be_mvp_bindings[domain].vmid ==
				 be_mvp_sealed_descs[domain].vmid &&
			 be_mvp_bindings[domain].root ==
				 be_mvp_sealed_descs[domain].pool_pa;
#if BE_MVP_RUN_PAGES
	agree &= count == BE_MVP_SCENARIO_PAGES &&
		 be_mvp_core_same(be_mvp_sealed_pages, be_mvp_pages,
				  sizeof(be_mvp_pages));
#else
	if (count == 1U && be_mvp_sealed_pages[0].kind == BE_MVP_PAGE_CHANNEL &&
	    be_mvp_sealed_pages[0].writer < BE_MVP_DOMAINS &&
	    be_mvp_sealed_pages[0].reader < BE_MVP_DOMAINS) {
		const struct be_mvp_gstage_page *page = &be_mvp_sealed_pages[0];

		be_mvp_sealed_channel = (struct be_mvp_gstage_channel){
			page->gpa, page->hpa, page->bytes, page->writer,
			page->reader, page->rights[page->writer],
			page->rights[page->reader],
		};
	}
	agree &= count <= 1U &&
		 be_mvp_core_same(&be_mvp_sealed_channel, &be_mvp_channel,
				  sizeof(be_mvp_channel));
#endif
	if (!agree)
		boot_fail();
	be_mvp_core_identity(&runtime->inventory, &runtime->proposal,
			     be_mvp_sealed_identity);
	values[0] = runtime->inventory.resource_count;
	values[1] = runtime->canonical.authority_count;
	values[2] = runtime->enforcement.root_count;
	values[3] = runtime->canonical.hart_id;
	values[4] = runtime->canonical.domains[0].hart_id;
	values[5] = runtime->canonical.domains[1].hart_id;
	line_start(marker_sealed, values);
	line_hex(&be_mvp_line, be_mvp_sealed_identity, sizeof(be_u64));
	emit_line();
}

/*
 * The scenario: its name, binding, and outbound ring (mvp-scenario.h); and
 * the MVP region and the flat image (mvp-layout.h).
 */
static void scenario_line(void)
{
#if defined(BE_MVP_PROBE_IMAGE)
	be_u64 values[8] = {
		BE_MVP_RUN_DOMAINS, BE_MVP_CONTROL_HART,
		be_mvp_bindings[0].hart, BE_MVP_SCENARIO_HARTS,
		BE_MVP_RUN_OUTBOUND_BYTES, BE_MVP_REGION_HPA,
		BE_MVP_REGION_BYTES, BE_MVP_IMAGE_BYTES,
	};
#else
	be_u64 values[9] = {
		BE_MVP_DOMAINS, BE_MVP_CONTROL_HART, be_mvp_bindings[0].hart,
		be_mvp_bindings[1].hart, BE_MVP_SCENARIO_HARTS,
		BE_MVP_RUN_OUTBOUND_BYTES, BE_MVP_REGION_HPA,
		BE_MVP_REGION_BYTES, BE_MVP_IMAGE_BYTES,
	};
#endif

	emit(marker_scenario, values);
}

/*
 * The firmware's HSM and IPI through the accepted probe helper, and every
 * other hart's state (BE_MVP:02, each status or error as found, then the
 * one STARTED hart or none; Plan revision M0-A.2): both domain harts
 * STOPPED, and every other hart STOPPED but for at most one STARTED hart,
 * the boot hart the shim's start rule left parked. The domain harts are
 * the run's, as BE_MVP:01 names them: domain 0's alone in the probe
 * images, which start no other. A missing extension, an
 * error, any other state, a STARTED domain hart, or a second STARTED hart
 * then fails closed. Whether a domain's hart exists is the firmware's to
 * say, at its start; a domain hart beyond the platform's harts is not
 * among the statuses.
 */
static void probe_firmware(void)
{
	struct be_mvp_hsm_census census;
	be_u64 values[2] = { 0U, 0U };
	be_u64 hart;
	int ok;

	ok = be_mvp_exec_sbi_probe(BE_MVP_FW_EID_HSM, &values[0]) ==
		     BE_R0_SBI_SUCCESS &&
	     be_mvp_exec_sbi_probe(BE_MVP_FW_EID_IPI, &values[1]) ==
		     BE_R0_SBI_SUCCESS &&
	     values[0] != 0U && values[1] != 0U;
	be_mvp_hsm_census_init(&census, be_mvp_bindings[0].hart,
			       BE_MVP_RUN_DOMAINS > 1U ?
			       be_mvp_bindings[1].hart : BE_MVP_HSM_NONE);
	line_start(marker_firmware, values);
#if defined(BE_MVP_RUN_PROBE_PLATFORM)
	/* probe-platform's hsm line: the same statuses, a fact either way. */
	be_mvp_line_reset(&be_mvp_detail);
	be_mvp_line_text(&be_mvp_detail, marker_probe_hsm);
#endif
	for (hart = 1U; hart < BE_MVP_SCENARIO_HARTS; ++hart) {
		be_u64 pair[2] = { hart, ~BE_U64_C(0) };
		long error = be_mvp_exec_hart_status(hart, &pair[1]);

		if (!be_mvp_hsm_census_add(&census, hart, error, pair[1]))
			ok = 0;
		if (error != BE_MVP_SBI_SUCCESS)
			pair[1] = (be_u64)error;
		be_mvp_line_format(&be_mvp_line, hart == 1U ?
				   marker_status_first : marker_status_next,
				   pair);
#if defined(BE_MVP_RUN_PROBE_PLATFORM)
		be_mvp_line_format(&be_mvp_detail, hart == 1U ?
				   marker_status_first : marker_status_next,
				   pair);
#endif
	}
	if (census.started == BE_MVP_HSM_NONE)
		be_mvp_line_text(&be_mvp_line, marker_started_none);
	else
		be_mvp_line_format(&be_mvp_line, marker_started_hart,
				   &census.started);
	emit_line();
#if defined(BE_MVP_RUN_PROBE_PLATFORM)
	be_mvp_line_text(&be_mvp_detail, marker_newline);
	if (write_line(&be_mvp_detail) != BE_R3_ERROR_NONE)
		be_mvp_runtime_terminal(BE_MVP_CLASS_CONSOLE);
	be_mvp_line_reset(&be_mvp_detail);
#endif
	if (!ok)
		be_mvp_runtime_terminal(BE_MVP_CLASS_FIRMWARE);
}

/*
 * henvcfg first: a CPU without Sstc fails closed before any domain hart is
 * armed or hart 0's budget is written.
 */
static void probe_sstc(void)
{
	be_u64 henvcfg = be_mvp_exec_arm_stce();
	enum be_mvp_class failure = be_mvp_stce_class(henvcfg);

	if (failure != BE_MVP_CLASS_NONE)
		fail_detail(failure, marker_detail_henvcfg, &henvcfg);
}

#if !BE_MVP_RUN_PAGES
/* One root's channel page, as the record the derived roots give declares
 * it for that domain: all zero without a channel. */
static struct be_mvp_gstage_root_page channel_page(be_u32 domain)
{
	struct be_mvp_gstage_root_page page = { 0U, 0U, 0U, 0U };

	if (be_mvp_sealed_channel.bytes == 0U)
		return page;
	page.gpa = be_mvp_sealed_channel.gpa;
	page.hpa = be_mvp_sealed_channel.hpa;
	page.bytes = be_mvp_sealed_channel.bytes;
	if (domain == be_mvp_sealed_channel.writer_domain)
		page.rights = be_mvp_sealed_channel.writer_rights;
	else if (domain == be_mvp_sealed_channel.reader_domain)
		page.rights = be_mvp_sealed_channel.reader_rights;
	return page;
}
#endif

/* Bytes as lower-case hex digits, two per byte: the configuration
 * identity, or a digest. */
static void line_hex(struct be_mvp_line *line, const be_u8 *bytes,
		     be_u64 count)
{
	static const char digits[] = "0123456789abcdef";
	char pair[3] = { '\0', '\0', '\0' };
	be_u64 index;

	for (index = 0U; index < count; ++index) {
		pair[0] = digits[bytes[index] >> 4];
		pair[1] = digits[bytes[index] & 0xfU];
		be_mvp_line_text(line, pair);
	}
}

#if !BE_MVP_RUN_PAGES
/*
 * The channel check (planning/mvp-m1-plan.md, "G-stage and VMIDs") in place
 * of M0's pair check, whose rules it applies: every page the two walked
 * roots share is the declared channel page with its declared rights, and
 * nothing else. With a channel, BE_MVP:03 CHANNEL_CHECKED then shows the
 * walked page, both level-0 pages and leaves, and the configuration
 * identity; a refusal that names a root adds its DETAIL line.
 */
static void check_channel(void)
{
	struct be_mvp_gstage_refusal refusal;
#if BE_MVP_RUN_CHANNELS
	const struct be_mvp_gstage_leaf *writer;
	const struct be_mvp_gstage_leaf *reader;
	be_u64 values[9];
#endif

	if (be_mvp_gstage_channel_check(be_mvp_maps, be_mvp_leaves,
					&be_mvp_sealed_channel, &refusal) !=
	    BE_MVP_GSTAGE_OK) {
#if BE_MVP_RUN_CHANNELS
		if (refusal.domain < BE_MVP_DOMAINS) {
			be_u64 detail[4] = { refusal.domain, refusal.hart,
					     refusal.walked,
					     refusal.declared };

			fail_detail(BE_MVP_CLASS_GSTAGE, marker_detail_channel,
				    detail);
		}
#endif
		be_mvp_runtime_terminal(BE_MVP_CLASS_GSTAGE);
	}
#if BE_MVP_RUN_CHANNELS
	writer = &be_mvp_leaves[be_mvp_sealed_channel.writer_domain];
	reader = &be_mvp_leaves[be_mvp_sealed_channel.reader_domain];
	values[0] = be_mvp_sealed_channel.writer_domain;
	values[1] = be_mvp_sealed_channel.reader_domain;
	values[2] = writer->gpa;
	values[3] = writer->hpa;
	values[4] = writer->bytes;
	values[5] = be_mvp_leaves[0].l0_pa;
	values[6] = be_mvp_leaves[1].l0_pa;
	values[7] = writer->pte;
	values[8] = reader->pte;
	line_start(marker_channel, values);
	line_hex(&be_mvp_line, be_mvp_config_identity,
		 sizeof(be_mvp_config_identity));
	emit_line();
#endif
}
#else
/*
 * The page check (planning/mvp-m2-plan.md, "G-stage and VMIDs") in place
 * of M0's pair check, whose rules it applies: every page the two walked
 * roots map beside their windows is a declared page with its declared
 * rights in each, and a page a domain has no rights on has no leaf in its
 * root. A refusal fails gstage, with a DETAIL line when it names a root.
 * Then one BE_MVP:03 PAGE_CHECKED per page shows the walked page, both
 * roots' level-0 pages, its endpoints' leaves, and the configuration
 * identity. Each domain hart's denial path is given its root's walked
 * leaves of every page (publish_blocks()).
 */
static void check_pages(void)
{
	struct be_mvp_gstage_refusal refusal;
	be_u64 index;

	if (be_mvp_gstage_page_check(be_mvp_maps, be_mvp_page_leaves,
				     be_mvp_sealed_pages, BE_MVP_SCENARIO_PAGES,
				     &refusal) != BE_MVP_GSTAGE_OK) {
		if (refusal.domain < BE_MVP_DOMAINS) {
			be_u64 detail[5] = { refusal.page, refusal.domain,
					     refusal.hart, refusal.walked,
					     refusal.declared };

			fail_detail(BE_MVP_CLASS_GSTAGE, marker_detail_page,
				    detail);
		}
		be_mvp_runtime_terminal(BE_MVP_CLASS_GSTAGE);
	}
	for (index = 0U; index < BE_MVP_SCENARIO_PAGES; ++index) {
		const struct be_mvp_gstage_page *page =
			&be_mvp_sealed_pages[index];
		const struct be_mvp_gstage_leaf *reader =
			&be_mvp_page_leaves[page->reader].page[index];
		be_u64 values[11];
		be_u64 count = 0U;

		values[count++] = index;
		if (page->kind == BE_MVP_PAGE_CHANNEL)
			values[count++] = page->writer;
		values[count++] = page->reader;
		values[count++] = reader->gpa;
		values[count++] = reader->hpa;
		values[count++] = reader->bytes;
		values[count++] = be_mvp_maps[0].pool_pa +
				  BE_MVP_GSTAGE_L0_OFFSET;
		values[count++] = be_mvp_maps[1].pool_pa +
				  BE_MVP_GSTAGE_L0_OFFSET;
		if (page->kind == BE_MVP_PAGE_CHANNEL)
			values[count++] =
				be_mvp_page_leaves[page->writer].page[index]
					.pte;
		values[count] = reader->pte;
		line_start(page->kind == BE_MVP_PAGE_CHANNEL ?
			   marker_page_channel : marker_page_secret, values);
		line_hex(&be_mvp_line, be_mvp_config_identity,
			 sizeof(be_mvp_config_identity));
		emit_line();
	}
}
#endif

/*
 * Both MVP roots: build each in its own half of the NOLOAD pool from its
 * derived root alone (planning/mvp-m6-plan.md, D-2), its window and its
 * channel leaf or its leaves for the pages, re-walk every byte, and check
 * that the two walked roots share exactly the channel page, or map exactly
 * the pages, with the derived rights. Each is installed later, once, on
 * its own domain hart.
 */
static void build_gstage(void)
{
	be_u32 domain;

	if (symbol_address(__be_mvp_pool_start) != BE_MVP_POOL_HPA ||
	    symbol_address(__be_mvp_pool_end) !=
		    BE_MVP_POOL_HPA + BE_MVP_POOL_BYTES)
		be_mvp_runtime_terminal(BE_MVP_CLASS_GSTAGE);
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		be_u8 *pool = __be_mvp_pool_start +
			      domain * BE_MVP_GUEST_POOL_BYTES;
		const struct be_mvp_gstage_map *map = &be_mvp_maps[domain];
		const struct be_mvp_gstage_desc *desc =
			&be_mvp_sealed_descs[domain];
#if BE_MVP_RUN_PAGES
		be_u64 values[8];

		if (symbol_address(pool) != desc->pool_pa ||
		    be_mvp_gstage_build_pages(desc, be_mvp_sealed_pages,
					      BE_MVP_SCENARIO_PAGES, domain,
					      pool, BE_MVP_GUEST_POOL_BYTES) !=
			    BE_MVP_GSTAGE_OK ||
		    be_mvp_gstage_walk_pages(desc, be_mvp_sealed_pages,
					     BE_MVP_SCENARIO_PAGES, pool,
					     BE_MVP_GUEST_POOL_BYTES,
					     &be_mvp_maps[domain],
					     &be_mvp_page_leaves[domain]) !=
			    BE_MVP_GSTAGE_OK ||
#else
		struct be_mvp_gstage_root_page page = channel_page(domain);
		be_u64 values[8];

		if (symbol_address(pool) != desc->pool_pa ||
		    be_mvp_gstage_build_channel(desc, &page, pool,
						BE_MVP_GUEST_POOL_BYTES) !=
			    BE_MVP_GSTAGE_OK ||
		    be_mvp_gstage_walk_channel(desc, &page,
					       pool, BE_MVP_GUEST_POOL_BYTES,
					       &be_mvp_maps[domain],
					       &be_mvp_leaves[domain]) !=
			    BE_MVP_GSTAGE_OK ||
#endif
		    map->hgatp != be_mvp_hgatps[domain] ||
		    map->hgatp != be_mvp_hgatp(be_mvp_bindings[domain].vmid,
					       be_mvp_bindings[domain].root) ||
		    map->leaves != BE_MVP_GUEST_LEAVES)
			be_mvp_runtime_terminal(BE_MVP_CLASS_GSTAGE);
#if !BE_MVP_RUN_PAGES
		be_mvp_page_leaves[domain].page[0] = be_mvp_leaves[domain];
#endif
		values[0] = domain;
		values[1] = map->hart;
		values[2] = map->gpa_base;
		values[3] = map->hpa_base;
		values[4] = map->size;
		values[5] = map->leaves;
		values[6] = map->pool_pa;
		values[7] = map->vmid;
		emit(marker_gstage, values);
	}
#if BE_MVP_RUN_PAGES
	check_pages();
#else
	check_channel();
#endif
}

#if !defined(BE_MVP_PROBE_IMAGE)
/* Shape checks on the staged payload, before either window is touched. */
static void check_payload(void)
{
	const be_u8 *staged =
		(const be_u8 *)(void *)be_mvp_payload_layout.staging_hpa;
	be_u64 values[2] = { be_mvp_payload_layout.kernel_bytes,
			     be_mvp_payload_layout.kernel_image_size };

	if (be_mvp_payload_check(&be_mvp_payload_layout, be_mvp_maps, staged,
				 be_mvp_plans) != BE_MVP_PAYLOAD_OK)
		be_mvp_runtime_terminal(BE_MVP_CLASS_PAYLOAD);
	emit(marker_payload, values);
}
#endif

/* Zero one domain window through its HS backing, and read it back. */
static void clear_guest_ram(be_u32 domain)
{
	const struct be_mvp_gstage_map *map = &be_mvp_maps[domain];
	volatile be_u64 *window = (volatile be_u64 *)(void *)map->hpa_base;
	be_u64 words = map->size / sizeof(be_u64);
	be_u64 residue = 0U;
	be_u64 start = be_mvp_exec_read_time();
	be_u64 values[4];
	be_u64 index;

	for (index = 0U; index < words; ++index)
		window[index] = 0U;
	for (index = 0U; index < words; ++index)
		residue |= window[index];
	if (residue != 0U)
		boot_fail();
	values[0] = domain;
	values[1] = map->gpa_base;
	values[2] = map->size;
	values[3] = be_mvp_exec_read_time() - start;
	emit(marker_cleared, values);
}

#if BE_MVP_RUN_CHANNELS
/*
 * Zero the declared channel page through its HS backing, and read it back,
 * after both windows (BE_MVP:05), so that no byte from before the kexec
 * reaches either guest and the reader's first poll reads zero.
 */
static void clear_channel(void)
{
	volatile be_u64 *page =
		(volatile be_u64 *)(void *)be_mvp_sealed_channel.hpa;
	be_u64 words = be_mvp_sealed_channel.bytes / sizeof(be_u64);
	be_u64 residue = 0U;
	be_u64 start = be_mvp_exec_read_time();
	be_u64 values[3];
	be_u64 index;

	for (index = 0U; index < words; ++index)
		page[index] = 0U;
	for (index = 0U; index < words; ++index)
		residue |= page[index];
	if (residue != 0U)
		boot_fail();
	values[0] = be_mvp_sealed_channel.hpa;
	values[1] = be_mvp_sealed_channel.bytes;
	values[2] = be_mvp_exec_read_time() - start;
	emit(marker_channel_cleared, values);
}
#endif

#if BE_MVP_RUN_PAGES
/*
 * Each declared page through its HS backing, after both windows
 * (BE_MVP:05), each read back: a channel page zeroed (PAGE_CLEARED), so
 * that no byte from before the kexec reaches either guest; the secret page
 * the secret, then zeros (SECRET_PLACED, its address and the secret's
 * size, never its bytes). The secret page is the scenario's one, and no
 * other page is a secret page.
 */
static void place_pages(void)
{
	be_u64 index;

	for (index = 0U; index < BE_MVP_SCENARIO_PAGES; ++index) {
		const struct be_mvp_gstage_page *page =
			&be_mvp_sealed_pages[index];
		volatile be_u8 *bytes = (volatile be_u8 *)(void *)page->hpa;
		be_u64 secret = page->kind == BE_MVP_PAGE_SECRET ?
					sizeof(be_mvp_secret) : 0U;
		be_u64 start = be_mvp_exec_read_time();
		be_u64 residue = 0U;
		be_u64 values[4];
		be_u64 offset;

		if ((page->kind == BE_MVP_PAGE_SECRET) !=
		    (index == BE_MVP_SCENARIO_SECRET_PAGE) ||
		    page->bytes != BE_MVP_GSTAGE_PAGE_BYTES)
			boot_fail();
		for (offset = 0U; offset < page->bytes; ++offset)
			bytes[offset] = offset < secret ?
						be_mvp_secret[offset] : 0U;
		for (offset = 0U; offset < page->bytes; ++offset)
			residue |= (be_u64)(bytes[offset] ^
					    (offset < secret ?
						     be_mvp_secret[offset] :
						     0U));
		if (residue != 0U)
			boot_fail();
		values[0] = index;
		values[1] = page->hpa;
		values[2] = secret != 0U ? secret : page->bytes;
		values[3] = be_mvp_exec_read_time() - start;
		emit(secret != 0U ? marker_secret_placed : marker_page_cleared,
		     values);
	}
}
#endif

#if !defined(BE_MVP_PROBE_IMAGE)
/* Copy one staged object into a window, and compare the copy. */
static be_u64 place(be_u64 target, be_u64 source, be_u64 bytes)
{
	volatile be_u64 *to = (volatile be_u64 *)(void *)target;
	const volatile be_u64 *from =
		(const volatile be_u64 *)(const void *)source;
	volatile be_u8 *to_tail = (volatile be_u8 *)(void *)target;
	const volatile be_u8 *from_tail =
		(const volatile be_u8 *)(const void *)source;
	be_u64 words = bytes / sizeof(be_u64);
	be_u64 residue = 0U;
	be_u64 index;

	for (index = 0U; index < words; ++index)
		to[index] = from[index];
	for (index = words * sizeof(be_u64); index < bytes; ++index)
		to_tail[index] = from_tail[index];
	for (index = 0U; index < words; ++index)
		residue |= to[index] ^ from[index];
	for (index = words * sizeof(be_u64); index < bytes; ++index)
		residue |= (be_u64)(to_tail[index] ^ from_tail[index]);
	return residue;
}

/* The kernel into a domain's window, and that domain's own DTB. */
static void place_payload(be_u32 domain)
{
	const struct be_mvp_payload_plan *plan = &be_mvp_plans[domain];
	be_u64 start = be_mvp_exec_read_time();
	be_u64 values[7];

	if ((place(plan->kernel_target, plan->kernel_source,
		   plan->kernel_bytes) |
	     place(plan->dtb_target, plan->dtb_source, plan->dtb_bytes)) != 0U)
		boot_fail();
	values[0] = domain;
	values[1] = plan->kernel_gpa;
	values[2] = plan->kernel_bytes;
	values[3] = plan->image_size;
	values[4] = plan->dtb_gpa;
	values[5] = plan->dtb_bytes;
	values[6] = be_mvp_exec_read_time() - start;
	emit(marker_placed, values);
}
#endif

/*
 * The console input grants, bit d for domain d, read from the roots
 * derived from the sealed configuration (planning/mvp-m7-plan.md, D-5),
 * which seal_config() checked; anything else fails closed, boot.
 */
static be_u64 input_grants(void)
{
	be_u64 grants;

	if (!be_mvp_core_console(&be_mvp_runtime.enforcement, &grants))
		boot_fail();
	return grants;
}

/*
 * The measurement log (mvp/docs/log-profile.md; planning/mvp-m9-plan.md,
 * D-1 to D-3, D-9, and D-10). Hart 0 alone keeps it, after the placement
 * and before the barrier, so before any SBI HSM start and before the run
 * budget is armed; every record's ticks, its hashing and its append,
 * count toward the barrier's total, and a domain's launch records' toward
 * its LAUNCH line's.
 */

#if !defined(BE_MVP_PROBE_IMAGE)
/* A domain's launch register, r2 or r3 (2.6); a probe image has none. */
static const be_u8 *launch_register(be_u32 domain)
{
	return &be_mvp_log_registers[(BE_MVP_LOG_STREAM_DOMAIN0 + domain) *
				     BE_MVP_LOG_DIGEST_BYTES];
}
#endif

/* The block (4.5): the header line, then one line per record in order. */
static void log_block(void)
{
	be_u64 count = be_mvp_log_count(be_mvp_log);
	be_u64 index;

	be_mvp_log_render_header(&be_mvp_line, be_mvp_log);
	emit_line();
	for (index = 0U; index < count && index < BE_MVP_LOG_CAPACITY;
	     ++index) {
		be_mvp_log_render_record(&be_mvp_line, be_mvp_log, index);
		emit_line();
	}
}

/*
 * A log failure (2.5; 4.5, path 3): an overflow, a refused record, or a
 * page that cannot close: the block, then BE_MVP:FAIL log, no DETAIL.
 */
static void log_fail(void) __attribute__((noreturn));
static void log_fail(void)
{
	log_block();
	be_mvp_line_reset(&be_mvp_detail);
	be_mvp_runtime_terminal(BE_MVP_CLASS_LOG);
}

/*
 * One data record (2.7): an as-placed record's range hashed where it
 * lies, any other's digest the caller's; appended in sequence, which
 * extends its stream's register when it is measured. A refusal is the
 * log's failure. Returns the record's ticks.
 */
static be_u64 log_record(struct be_mvp_log_record *record)
{
	be_u64 start = be_mvp_exec_read_time();
	be_u64 ticks;

	if (record->representation == BE_MVP_LOG_AS_PLACED)
		be_mvp_sha256((const be_u8 *)(const void *)record->base,
			      record->length, record->digest);
	if (!be_mvp_log_append(be_mvp_log, be_mvp_log_registers, record))
		log_fail();
	ticks = be_mvp_exec_read_time() - start;
	be_mvp_log_ticks += ticks;
	return ticks;
}

#if BE_MVP_LOG_R2
/*
 * R2 (2.7, objects 0 to 4; planning/mvp-m9-plan.md, Q4): the monitor's
 * own text, constants, and R1 input, and the MVP region's text and
 * constants, as loaded, by the link's symbols; stream 0, a self-report
 * that gates nothing.
 */
static void log_self_report(void)
{
	static const struct {
		enum be_mvp_log_object object;
		const be_u8 *start;
		const be_u8 *end;
	} ranges[] = {
		{ BE_MVP_LOG_MONITOR_TEXT, __be_monitor_code_start,
		  __be_monitor_code_end },
		{ BE_MVP_LOG_MONITOR_RODATA, __be_monitor_rodata_start,
		  __be_monitor_rodata_end },
		{ BE_MVP_LOG_MONITOR_INPUT, __be_input_start, __be_input_end },
		{ BE_MVP_LOG_MVP_TEXT, __be_mvp_text_start, __be_mvp_text_end },
		{ BE_MVP_LOG_MVP_RODATA, __be_mvp_rodata_start,
		  __be_mvp_rodata_end },
	};
	be_u32 index;

	for (index = 0U; index < sizeof(ranges) / sizeof(ranges[0]);
	     ++index) {
		struct be_mvp_log_record record = {
			.type = BE_MVP_LOG_MEASURED,
			.stream = 0U,
			.object = ranges[index].object,
			.representation = BE_MVP_LOG_AS_PLACED,
			.base = symbol_address(ranges[index].start),
			.length = symbol_address(ranges[index].end) -
				  symbol_address(ranges[index].start),
		};

		(void)log_record(&record);
	}
}
#endif

/*
 * R3 (2.7, objects 5 to 9), stream 1: the sealed configuration's core
 * identity, which CONFIG_SEALED's prefix printed, as computed, and its
 * console grants (2.8), both measured; then, informational and as the
 * build recorded them, the image's configuration and policy identities
 * in a scenario with a report, or policy-absent, zero.
 */
static void log_configuration(void)
{
	struct be_mvp_log_record record = {
		.type = BE_MVP_LOG_MEASURED,
		.stream = 1U,
		.object = BE_MVP_LOG_CORE_IDENTITY,
		.representation = BE_MVP_LOG_AS_COMPUTED,
	};

	(void)memcpy(record.digest, be_mvp_sealed_identity,
		     sizeof(record.digest));
	(void)log_record(&record);
	record.object = BE_MVP_LOG_CONSOLE_GRANTS;
	be_mvp_log_console_grants(input_grants(), record.digest);
	(void)log_record(&record);
	record.type = BE_MVP_LOG_INFORMATIONAL;
	record.representation = BE_MVP_LOG_BUILD_RECORDED;
#if BE_MVP_RUN_LOG_POLICY
	record.object = BE_MVP_LOG_CONFIGURATION_IDENTITY;
	(void)memcpy(record.digest, be_mvp_log_constants.configuration,
		     sizeof(record.digest));
	(void)log_record(&record);
	record.object = BE_MVP_LOG_POLICY_IDENTITY;
	(void)memcpy(record.digest, be_mvp_log_constants.policy,
		     sizeof(record.digest));
#else
	record.object = BE_MVP_LOG_POLICY_ABSENT;
	(void)memset(record.digest, 0, sizeof(record.digest));
#endif
	(void)log_record(&record);
}

#if !defined(BE_MVP_PROBE_IMAGE)
/*
 * R4 for one domain (2.7, 2.9), its stream 2 + domain: its kernel, the
 * file's length, and its device tree, as its plan placed them, and, for
 * the measured domain of a scenario with pages, the secret page as
 * placed; then the domain's gate on its last record, against the image's
 * expected launch register. A passed gate prints BE_MVP:06 LAUNCH with
 * the register and the domain's ticks; a failed one prints the block,
 * its last record gated-fail, then fails measurement with the computed
 * and the expected values (4.5, path 2), and no domain hart starts.
 */
static void log_launch(be_u32 domain)
{
	const struct be_mvp_payload_plan *plan = &be_mvp_plans[domain];
	struct be_mvp_log_record record = {
		.type = BE_MVP_LOG_MEASURED,
		.stream = BE_MVP_LOG_STREAM_DOMAIN0 + domain,
		.object = BE_MVP_LOG_KERNEL_IMAGE,
		.representation = BE_MVP_LOG_AS_PLACED,
		.base = plan->kernel_target,
		.length = plan->kernel_bytes,
	};
	be_u64 values[3] = { domain, be_mvp_bindings[domain].hart, 0U };
	enum be_mvp_log_gate_result gate;

	values[2] = log_record(&record);
	record.object = BE_MVP_LOG_DEVICE_TREE;
	record.base = plan->dtb_target;
	record.length = plan->dtb_bytes;
	values[2] += log_record(&record);
#if BE_MVP_RUN_PAGES
	if (domain == BE_MVP_SCENARIO_MEASURED_DOMAIN) {
		const struct be_mvp_gstage_page *secret =
			&be_mvp_sealed_pages[BE_MVP_SCENARIO_SECRET_PAGE];

		record.object = BE_MVP_LOG_SECRET_PAGE;
		record.base = secret->hpa;
		record.length = secret->bytes;
		values[2] += log_record(&record);
	}
#endif
	gate = be_mvp_log_gate(be_mvp_log, be_mvp_log_registers,
			       be_mvp_log_constants.launch[domain]);
	if (gate == BE_MVP_LOG_GATE_INVALID)
		log_fail();
	if (gate != BE_MVP_LOG_GATE_PASS) {
		be_mvp_line_reset(&be_mvp_detail);
		be_mvp_line_format(&be_mvp_detail, marker_detail_measurement,
				   values);
		line_hex(&be_mvp_detail, launch_register(domain),
			 BE_MVP_LOG_DIGEST_BYTES);
		be_mvp_line_text(&be_mvp_detail, marker_detail_expected);
		line_hex(&be_mvp_detail, be_mvp_log_constants.launch[domain],
			 BE_MVP_LOG_DIGEST_BYTES);
		be_mvp_line_text(&be_mvp_detail, marker_newline);
		log_block();
		be_mvp_runtime_terminal(BE_MVP_CLASS_MEASUREMENT);
	}
	line_start(marker_launch, values);
	line_hex(&be_mvp_line, launch_register(domain),
		 BE_MVP_LOG_DIGEST_BYTES);
	be_mvp_line_format(&be_mvp_line, marker_launch_match, &values[2]);
	emit_line();
}
#endif

/*
 * The log, after the placement (a probe's after its stub's) and before
 * the barrier (4.5, path 1): started with the image's scenario digest
 * and, in a scenario with a report, its configuration identity; R2 when
 * the image keeps it, R3, and each domain's R4 with its gate; then the
 * close, which only the image's expected count admits. The block and the
 * barrier's registers line, with the hashing total, follow, then
 * BE_MVP:07; the terminal registers line is rendered now, for hart 0's
 * terminal path to print before its terminal line, and the domain harts'
 * code reaches it only as text.
 */
static void measure_log(void)
{
	const be_u8 *configuration = BE_MVP_RUN_LOG_POLICY ?
		be_mvp_log_constants.configuration : (const be_u8 *)0;
#if !defined(BE_MVP_PROBE_IMAGE)
	be_u32 domain;
#endif

	be_mvp_log_init(be_mvp_log, be_mvp_log_registers,
			be_mvp_log_constants.scenario, configuration);
#if BE_MVP_LOG_R2
	log_self_report();
#endif
	log_configuration();
#if !defined(BE_MVP_PROBE_IMAGE)
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		log_launch(domain);
#endif
	if (!be_mvp_log_close(be_mvp_log, be_mvp_log_constants.count))
		log_fail();
	log_block();
	be_mvp_log_render_registers(&be_mvp_line, be_mvp_log_registers, 1,
				    be_mvp_log_ticks);
	emit_line();
	be_mvp_log_render_registers(&be_mvp_log_terminal,
				    be_mvp_log_registers, 0, 0U);
	be_mvp_line_text(&be_mvp_log_terminal, marker_newline);
}

static struct be_mvp_hart_page *hart_page(be_u32 domain)
{
	return (struct be_mvp_hart_page *)(void *)(be_mvp_block_hpa(domain) +
						   BE_MVP_BLOCK_STATE_OFFSET);
}

/* One ring's two views: the writer's and the reader's, at zero indices. */
static int ring_views(struct be_mvp_ring *writer, struct be_mvp_ring *reader,
		      be_u64 buffer, be_u64 capacity,
		      volatile struct be_mvp_ring_index *head,
		      volatile struct be_mvp_ring_index *tail, be_u64 types,
		      be_u32 domain)
{
	be_mvp_ring_reset(head, tail);
	return be_mvp_ring_init(writer, (be_u8 *)(void *)buffer, capacity,
				head, tail, types, domain,
				BE_MVP_RING_WRITER) &&
	       be_mvp_ring_init(reader, (be_u8 *)(void *)buffer, capacity,
				head, tail, types, domain,
				BE_MVP_RING_READER);
}

/*
 * The boot barrier (BE_MVP:07): fill both blocks, each state page zeroed
 * first: the descriptor from the binding, the first-entry frame, the
 * walked window and its root's walked page leaves, the SBI core's state
 * with the domain's exit ceiling, the image's denial entry, whether the
 * image accepts the management extension, and whether the sealed
 * configuration grants the domain console input (M7, D-5), and zero ring
 * indices, with the views of the three rings, hart 0's and the domain
 * hart's; then a fence w, w, and the generation words last.
 */
static void publish_blocks(void)
{
	be_u64 values[4] = { BE_MVP_HART_REGION_HPA, BE_MVP_HART_REGION_BYTES,
			     BE_MVP_GENERATION, BE_MVP_RUN_TIME_BUDGET };
	be_u64 grants = input_grants();
	be_u32 domain;

	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		struct be_mvp_hart_page *page = hart_page(domain);
		be_u64 block = be_mvp_block_hpa(domain);

		(void)memset(page, 0, BE_MVP_BLOCK_STATE_BYTES);
		if (be_mvp_block_fill(&page->page.desc, domain,
				      be_mvp_bindings, BE_MVP_DOMAINS,
				      BE_MVP_RUN_OUTBOUND_BYTES) !=
		    BE_MVP_BLOCK_OK)
			boot_fail();
		be_mvp_entry_frame(&page->page.entry,
				   be_mvp_plans[domain].kernel_gpa,
				   BE_MVP_GUEST_HART,
				   be_mvp_plans[domain].dtb_gpa);
		(void)memcpy(&page->map, &be_mvp_maps[domain],
			     sizeof(page->map));
		(void)memcpy(&page->leaves, &be_mvp_page_leaves[domain],
			     sizeof(page->leaves));
		page->page.state.exit_ceiling = BE_MVP_RUN_EXIT_CEILING;
		page->page.state.accept_denial = BE_MVP_RUN_ACCEPT_DENIAL;
		page->page.state.accept_mgmt = BE_MVP_RUN_ACCEPT_MGMT;
		page->page.state.accept_input = (grants >> domain) & 1U;
		if (!ring_views(&be_mvp_inbound[domain], &page->inbound,
				block + BE_MVP_BLOCK_INBOUND_OFFSET,
				BE_MVP_INBOUND_RING_BYTES,
				&page->page.inbound_head,
				&page->page.inbound_tail,
				BE_MVP_RECORDS_INBOUND, domain) ||
		    !ring_views(&page->outbound, &be_mvp_outbound[domain],
				block + BE_MVP_BLOCK_OUTBOUND_OFFSET,
				BE_MVP_RUN_OUTBOUND_BYTES,
				&page->page.outbound_head,
				&page->page.outbound_tail,
				BE_MVP_RECORDS_OUTBOUND, domain) ||
		    !ring_views(&be_mvp_input_rings[domain], &page->input,
				block + BE_MVP_INPUT_RING_OFFSET,
				BE_MVP_INPUT_RING_BYTES,
				&page->page.input_head,
				&page->page.input_tail,
				BE_MVP_RECORDS_INPUT, domain))
			boot_fail();
	}
	be_mvp_exec_fence_w_w();
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		*(volatile be_u64 *)&hart_page(domain)->page.desc.generation =
			BE_MVP_GENERATION;
	emit(marker_published, values);
}

/*
 * Each domain hart, once: hart_start at the hart entry with its block, then
 * hart_get_status until STARTED, within the start wait (BE_MVP:08).
 */
static void start_harts(void)
{
	be_u32 domain;

	for (domain = 0U; domain < BE_MVP_RUN_DOMAINS; ++domain) {
		be_u64 hart = be_mvp_bindings[domain].hart;
		be_u64 begin = be_mvp_exec_read_time();
		be_u64 status = ~BE_U64_C(0);
		be_u64 values[5];
		long error;
		long result;

		result = be_mvp_exec_hart_start(hart,
						symbol_address(be_mvp_hart_entry),
						be_mvp_block_hpa(domain));
		error = result;
		while (result == BE_MVP_SBI_SUCCESS) {
			error = be_mvp_exec_hart_status(hart, &status);
			if (be_mvp_hsm_started(error, status) ||
			    be_mvp_exec_read_time() - begin >=
				    BE_MVP_HART_START_TICKS)
				break;
		}
		values[0] = hart;
		values[1] = domain;
		values[2] = (be_u64)result;
		values[3] = error != BE_MVP_SBI_SUCCESS ? (be_u64)error :
			status;
		values[4] = be_mvp_exec_read_time() - begin;
		if (result != BE_MVP_SBI_SUCCESS ||
		    !be_mvp_hsm_started(error, status)) {
			values[0] = domain;
			values[1] = hart;
			fail_detail(BE_MVP_CLASS_HART_START,
				    marker_detail_start, values);
		}
		emit(marker_started, values);
		if (!be_mvp_control_started(&be_mvp_ctl, domain, hart))
			be_mvp_runtime_terminal(BE_MVP_CLASS_EXCEPTION);
	}
}

#if !defined(BE_MVP_PROBE_IMAGE)
/*
 * One record into a domain's inbound ring at @now, published, then one IPI
 * to its hart: the record is visible before the IPI that announces it.
 */
static void post_inbound(be_u32 domain, enum be_mvp_record_type type,
			 be_u64 now, const be_u64 *words, be_u64 count)
{
	struct be_mvp_ring *inbound = &be_mvp_inbound[domain];

	if (!be_mvp_ring_post_words(inbound, type, now, words, count))
		fail_domain(BE_MVP_CLASS_RING, domain, type);
	/* Writer: the record's bytes before the head that admits them. */
	be_mvp_exec_fence_w_w();
	if (!be_mvp_ring_publish(inbound))
		fail_domain(BE_MVP_CLASS_RING, domain, type);
	if (be_mvp_send_ipi(be_mvp_bindings[domain].hart) !=
	    BE_MVP_SBI_SUCCESS)
		fail_domain(BE_MVP_CLASS_IPI, domain, type);
}

/* The PING of the IPI probe (Q4): one record, then one IPI. */
static void ping(be_u32 domain)
{
	post_inbound(domain, BE_MVP_RECORD_PING, be_mvp_exec_read_time(),
		     (const be_u64 *)0, 0U);
}

/* What one byte or flush of console input owes the console: BE_MVP:16
 * for a focus, BE_MVP:17 for a reason's first drop, else nothing. */
static void input_report(const struct be_mvp_input_event *event)
{
	be_u64 domain = event->domain;

	if (event->report == BE_MVP_INPUT_FOCUSED) {
		emit(marker_focus, &domain);
	} else if (event->report == BE_MVP_INPUT_FIRST_DROP) {
		be_mvp_line_reset(&be_mvp_line);
		be_mvp_line_text(&be_mvp_line, marker_input_drop);
		be_mvp_line_text(&be_mvp_line,
				 be_mvp_input_drop_name(event->reason));
		emit_line();
	}
}

/*
 * One poll of the firmware console (planning/mvp-m7-plan.md, D-1 and Q2):
 * DBCN console_read into hart 0's buffer, 64 bytes at a time, until the
 * firmware holds none or 256 were read; each byte through the focus
 * parser and the routing (mvp-input.h) against the domains running as
 * the drained records left them; then each domain's batch posted to its
 * input ring as one INPUT record, published, with no IPI: the domain hart
 * takes it at its guest's next read. An SBI error, or a count beyond the
 * request, fails the run as console; a malformed input ring as ring.
 */
static void poll_input(void)
{
	struct be_mvp_input *input = &be_mvp_console_in;
	struct be_mvp_input_event event;
	be_u64 running = be_mvp_control_running(&be_mvp_ctl);
	be_u64 total = 0U;
	be_u32 domain;

	be_mvp_input_poll_begin(input);
	while (total < BE_MVP_INPUT_POLL_MAX) {
		be_u64 want = BE_MVP_INPUT_POLL_MAX - total;
		be_u64 got = ~BE_U64_C(0);
		be_u64 index;

		if (want > BE_MVP_INPUT_READ_BYTES)
			want = BE_MVP_INPUT_READ_BYTES;
		if (be_mvp_exec_console_read(be_mvp_console_in_buffer, want,
					     &got) != BE_MVP_SBI_SUCCESS ||
		    got > want)
			be_mvp_runtime_terminal(BE_MVP_CLASS_CONSOLE);
		if (got == 0U)
			break;
		for (index = 0U; index < got; ++index) {
			be_mvp_input_byte(input,
					  be_mvp_console_in_buffer[index],
					  running, &event);
			input_report(&event);
		}
		total += got;
	}
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		struct be_mvp_ring *ring = &be_mvp_input_rings[domain];
		be_u64 posted = be_mvp_input_flush(input, domain, ring,
						   be_mvp_exec_read_time(),
						   &event);

		if (posted == BE_MVP_INPUT_FAILED)
			fail_domain(BE_MVP_CLASS_RING, domain,
				    BE_MVP_RECORD_INPUT);
		if (posted != 0U) {
			/* Writer: the record's bytes before its head. */
			be_mvp_exec_fence_w_w();
			if (!be_mvp_ring_publish(ring))
				fail_domain(BE_MVP_CLASS_RING, domain,
					    BE_MVP_RECORD_INPUT);
		}
		input_report(&event);
	}
	be_mvp_input_poll_end(input);
}

/*
 * The next wake while console input is armed (D-1): hart 0's timer, by
 * the budget helper, the image's one stimecmp writer, at the earlier of
 * the next poll and the budget's end, so the run still ends where its
 * budget ends. Without console input it is never re-armed.
 */
static void rearm_input(void)
{
	be_u64 deadline;

	if (!be_mvp_input_rearm(&be_mvp_console_in, be_mvp_ctl.start,
				be_mvp_ctl.budget, be_mvp_exec_read_time(),
				&deadline))
		return;
	if (be_mvp_exec_arm_budget(deadline,
				   symbol_address(__be_control_stack_end)) !=
	    BE_MVP_SIE_CONTROL)
		be_mvp_runtime_terminal(BE_MVP_CLASS_CONTROLS);
}

/*
 * Console input, armed right after the barrier (D-1 and D-4), only when
 * the sealed configuration grants it to a domain: BE_MVP:15 with the
 * granted domains and the prefix, BE_MVP:16 FOCUS none, and the first
 * poll, whose bytes the firmware held before arming, each dropped as
 * before-armed. In any other image hart 0 never reads the firmware
 * console, never re-arms its timer for a poll, and prints nothing here.
 */
static void arm_input(void)
{
	be_u64 grants = input_grants();
	be_u64 prefix = BE_MVP_INPUT_PREFIX;
	be_u64 domain;
	int first = 1;

	if (!be_mvp_input_arm(&be_mvp_console_in, grants))
		return;
	be_mvp_line_reset(&be_mvp_line);
	be_mvp_line_text(&be_mvp_line, marker_input_armed);
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain) {
		if (((grants >> domain) & 1U) == 0U)
			continue;
		be_mvp_line_format(&be_mvp_line, first != 0 ?
				   marker_input_grant :
				   marker_input_grant_next, &domain);
		first = 0;
	}
	be_mvp_line_format(&be_mvp_line, marker_input_prefix, &prefix);
	emit_line();
	emit_text(marker_focus_none);
	poll_input();
}

/*
 * BE_MVP:18 INPUT (D-4), before BE_MVP:13 in an image with console input
 * armed: the bytes read, each domain's delivered bytes and the first 16
 * hex digits of their SHA-256, and each reason's drops in the reasons'
 * order, or none.
 */
static void input_summary(void)
{
	const struct be_mvp_input *input = &be_mvp_console_in;
	be_u8 digest[BE_MVP_SHA256_BYTES];
	be_u64 values[2];
	be_u32 reason;
	int any = 0;

	if (input->armed != 1U)
		return;
	line_start(marker_input, &input->read);
	for (values[0] = 0U; values[0] < BE_MVP_DOMAINS; ++values[0]) {
		values[1] = input->delivered[values[0]];
		be_mvp_line_format(&be_mvp_line, marker_input_domain, values);
		be_mvp_input_digest(input, (be_u32)values[0], digest);
		line_hex(&be_mvp_line, digest, sizeof(be_u64));
	}
	be_mvp_line_text(&be_mvp_line, marker_input_dropped);
	for (reason = 0U; reason < BE_MVP_DROP_REASONS; ++reason) {
		if (input->dropped[reason] == 0U)
			continue;
		if (any != 0)
			be_mvp_line_text(&be_mvp_line, marker_input_next);
		be_mvp_line_text(&be_mvp_line, be_mvp_input_drop_name(
			(enum be_mvp_input_drop)reason));
		be_mvp_line_format(&be_mvp_line, marker_input_count,
				   &input->dropped[reason]);
		any = 1;
	}
	if (any == 0)
		be_mvp_line_text(&be_mvp_line, marker_input_none);
	emit_line();
}

#if BE_MVP_RUN_ACCEPT_MGMT
/*
 * The answer to one management request (planning/mvp-m2-plan.md, Q14):
 * MGMT_RESULT (the result as a two's-complement word, and the request's
 * sequence number) in the requester's inbound ring with one IPI; then its
 * BE_MVP:MGMT line, whose service is the answer's time minus the
 * request's.
 */
static void answer(const struct be_mvp_step_result *result)
{
	be_u32 requester = (be_u32)result->requester;
	be_u64 now = be_mvp_exec_read_time();
	be_u64 words[BE_MVP_MGMT_RESULT_WORDS];
	be_u64 head[3] = { be_mvp_bindings[requester].hart, requester,
			   result->seq };
	be_u64 values[2] = { result->target, (be_u64)result->result };
	be_u64 ticks[2] = { since(result->requested),
			    now - result->requested };

	words[BE_MVP_MGMT_RESULT_CODE] = (be_u64)result->result;
	words[BE_MVP_MGMT_RESULT_SEQ] = result->seq;
	post_inbound(requester, BE_MVP_RECORD_MGMT_RESULT, now, words,
		     BE_MVP_MGMT_RESULT_WORDS);
	line_start(marker_mgmt, head);
	be_mvp_line_text(&be_mvp_line,
			 result->fid == BE_MVP_SBI_MGMT_PAUSE ?
			 marker_fid_pause : marker_fid_terminate);
	be_mvp_line_format(&be_mvp_line, marker_mgmt_values, values);
	be_mvp_line_text(&be_mvp_line,
			 marker_target_state[(unsigned int)result->shown <=
					     BE_MVP_TARGET_COUNT ?
					     result->shown :
					     BE_MVP_TARGET_COUNT]);
	be_mvp_line_format(&be_mvp_line, marker_mgmt_ticks, ticks);
	emit_line();
}

/*
 * A granted request's delivery: PAUSE or TERMINATE, naming its requester,
 * in the target's inbound ring with one IPI; its answer waits for the
 * target's PAUSED or TERMINATED.
 */
static void deliver(const struct be_mvp_step_result *result)
{
	be_u64 by = result->requester;

	post_inbound((be_u32)result->target,
		     result->fid == BE_MVP_SBI_MGMT_PAUSE ?
		     BE_MVP_RECORD_PAUSE : BE_MVP_RECORD_TERMINATE,
		     be_mvp_exec_read_time(), &by, BE_MVP_PAUSE_WORDS);
}

/*
 * BE_MVP:12 DOMAIN_TERMINATED: the domain, its requester, its exits, its
 * launch register, read again from hart 0's own memory (planning/
 * mvp-m9-plan.md, D-9; mvp/docs/log-profile.md, 4.8), and the
 * transition's ticks since the barrier.
 */
static void emit_terminated(be_u32 domain, const struct be_mvp_record *record)
{
	be_u64 values[4] = {
		be_mvp_bindings[domain].hart, domain,
		be_mvp_record_word(record, BE_MVP_TERMINATED_BY),
		be_mvp_record_word(record, BE_MVP_TERMINATED_EXITS),
	};
	be_u64 ticks = since(record->time);

	line_start(marker_domain_terminated, values);
	line_hex(&be_mvp_line, launch_register(domain),
		 BE_MVP_LOG_DIGEST_BYTES);
	be_mvp_line_format(&be_mvp_line, marker_terminated_ticks, &ticks);
	emit_line();
}
#endif

/* Both domains shut down: the summary, then the monitor's own shutdown. */
static void run_complete(void) __attribute__((noreturn));
static void run_complete(void)
{
	be_u64 values[6] = { BE_MVP_DOMAINS, be_mvp_ctl.records,
			     be_mvp_ctl.wakes, be_mvp_ctl.idle_ticks, 0U,
			     since(be_mvp_exec_read_time()) };

	(void)be_mvp_control_overlap(&be_mvp_ctl, &values[4]);
	input_summary();
	emit(marker_complete, values);
	log_terminal();
	emit_text(marker_shutdown);
	(void)be_mvp_exec_system_reset();
	/* A conforming shutdown does not return. */
	terminal(BE_MVP_CLASS_SHUTDOWN_RETURNED, 0);
}
#endif

/*
 * A domain's FAIL: its FAIL and DETAIL lines, its ACK, and the run's end.
 * The ACK spares the domain hart its own fallback lines.
 */
static void domain_failed(be_u32 domain, const struct be_mvp_record *record,
			  enum be_mvp_class failure) __attribute__((noreturn));
static void domain_failed(be_u32 domain, const struct be_mvp_record *record,
			  enum be_mvp_class failure)
{
	struct be_mvp_ring *inbound = &be_mvp_inbound[domain];
	be_u64 detail[BE_MVP_FAIL_DETAIL_WORDS];
	be_u64 words = record->length / sizeof(be_u64) - 1U;
	be_u64 index;

	for (index = 0U; index < words; ++index)
		detail[index] = be_mvp_record_word(record, 1U + index);
	be_mvp_detail_line(&be_mvp_detail, failure, domain,
			   be_mvp_bindings[domain].hart, detail, words);
	if (be_mvp_ring_post(inbound, BE_MVP_RECORD_ACK,
			     be_mvp_exec_read_time(), (const be_u8 *)0, 0U)) {
		be_mvp_exec_fence_w_w();
		(void)be_mvp_ring_publish(inbound);
	}
	terminal(failure, 1);
}

/* One record's control-hart line: its hart, domain, and @program's values. */
static void emit_record(const char *format, const be_u8 *program,
			be_u32 domain, const struct be_mvp_record *record)
{
	be_u64 values[16];
	be_u64 count;

	values[0] = be_mvp_bindings[domain].hart;
	values[1] = domain;
	for (count = 2U; count < 16U && *program != VALUE_END; ++program) {
		be_u64 source = *program & ~VALUE_SINCE;
		be_u64 value = 0U;
		be_u64 index;

		if (source == VALUE_TIME) {
			value = record->time;
		} else if (source != VALUE_SBI) {
			value = be_mvp_record_word(record, source);
		} else {
			/* sbi= counts the management calls too (M2), and the
			 * served console reads (M7). */
			for (index = BE_MVP_SHUTDOWN_BASE;
			     index <= BE_MVP_SHUTDOWN_REFUSED; ++index)
				value += be_mvp_record_word(record, index);
			value += be_mvp_record_word(record,
						    BE_MVP_SHUTDOWN_MGMT);
			value += be_mvp_record_word(record,
						    BE_MVP_SHUTDOWN_DBCN_INPUT);
		}
		values[count++] = (*program & VALUE_SINCE) != 0U ?
			since(value) : value;
	}
	emit(format, values);
}

#if defined(BE_MVP_PROBE_IMAGE)
/*
 * One drained record in a probe image: READY, ENTERED, or FAIL. The probe
 * stub prints nothing and is never pinged, so any other record fails the
 * run.
 */
static void step(be_u32 domain, const struct be_mvp_record *record)
{
	struct be_mvp_step_result result;

	switch (be_mvp_control_record(&be_mvp_ctl, domain, record, &result)) {
	case BE_MVP_STEP_READY:
		emit_record(marker_ready, values_ready, domain, record);
		return;
	case BE_MVP_STEP_ENTERED:
		emit_record(marker_entered, values_entered, domain, record);
		return;
	case BE_MVP_STEP_FAIL:
		domain_failed(domain, record, result.failure);
	default:
		fail_domain(BE_MVP_CLASS_RING, domain, record->type);
	}
}
#else
#if BE_MVP_RUN_ACCEPT_DENIAL
/*
 * One DENIAL's line (BE_MVP:DENY): its record's fields, the kind by name,
 * the exit's ticks since the barrier, and the service, the post's time
 * minus the exit's, which the control loop required to be no less.
 */
static void emit_denial(be_u32 domain, const struct be_mvp_record *record)
{
	be_u64 exit = be_mvp_record_word(record, BE_MVP_DENIAL_EXIT);
	be_u64 head[3] = {
		be_mvp_bindings[domain].hart, domain,
		be_mvp_record_word(record, BE_MVP_DENIAL_SEQ),
	};
	be_u64 values[11] = {
		be_mvp_record_word(record, BE_MVP_DENIAL_CAUSE),
		be_mvp_record_word(record, BE_MVP_DENIAL_INJECTED),
		be_mvp_record_word(record, BE_MVP_DENIAL_GPA),
		be_mvp_record_word(record, BE_MVP_DENIAL_HTVAL),
		be_mvp_record_word(record, BE_MVP_DENIAL_HTINST),
		be_mvp_record_word(record, BE_MVP_DENIAL_STVAL),
		be_mvp_record_word(record, BE_MVP_DENIAL_SEPC),
		be_mvp_record_word(record, BE_MVP_DENIAL_VSSTATUS),
		be_mvp_record_word(record, BE_MVP_DENIAL_VSTVEC),
		since(exit), record->time - exit,
	};

	line_start(marker_denial, head);
	be_mvp_line_text(&be_mvp_line,
			 be_mvp_record_word(record, BE_MVP_DENIAL_KIND) ==
				 BE_MVP_DENIAL_READ_ONLY ?
				 marker_kind_read_only : marker_kind_unmapped);
	be_mvp_line_format(&be_mvp_line, marker_denial_values, values);
	emit_line();
}
#endif

/*
 * One drained record: print its line, PING, finish, or fail the run; and,
 * with the management extension, answer or deliver a request, and log a
 * transition and answer the request that caused it.
 */
static void step(be_u32 domain, const struct be_mvp_record *record)
{
	struct be_mvp_step_result result;
	be_u64 bytes;

	switch (be_mvp_control_record(&be_mvp_ctl, domain, record, &result)) {
	case BE_MVP_STEP_READY:
		emit_record(marker_ready, values_ready, domain, record);
		return;
	case BE_MVP_STEP_ENTERED:
		emit_record(marker_entered, values_entered, domain, record);
		return;
	case BE_MVP_STEP_LINE:
		bytes = be_mvp_line_output(record, be_mvp_console_out,
					   sizeof(be_mvp_console_out));
		if (bytes == BE_MVP_CONSOLE_INVALID ||
		    be_mvp_exec_console_write(be_mvp_console_out, bytes) !=
			    BE_R3_ERROR_NONE)
			be_mvp_runtime_terminal(BE_MVP_CLASS_CONSOLE);
		if (result.ping != 0U)
			ping(domain);
		return;
	case BE_MVP_STEP_PONG:
		emit_record(marker_ipi, values_pong, domain, record);
		return;
#if BE_MVP_RUN_ACCEPT_DENIAL
	case BE_MVP_STEP_DENIAL:
		emit_denial(domain, record);
		return;
#endif
#if BE_MVP_RUN_ACCEPT_MGMT
	case BE_MVP_STEP_MGMT:
		answer(&result);
		return;
	case BE_MVP_STEP_DELIVER:
		deliver(&result);
		return;
	case BE_MVP_STEP_PAUSED:
		emit_record(marker_domain_paused, values_paused, domain,
			    record);
		answer(&result);
		return;
	case BE_MVP_STEP_TERMINATED:
		emit_terminated(domain, record);
		answer(&result);
		if (result.done != 0U)
			run_complete();
		return;
#endif
	case BE_MVP_STEP_SHUTDOWN:
		emit_record(marker_domain_shutdown, values_shutdown, domain,
			    record);
#if BE_MVP_RUN_ACCEPT_MGMT
		/* A request delivered to the domain before it shut down. */
		if (result.answer != 0U)
			answer(&result);
#endif
		if (result.done != 0U)
			run_complete();
		return;
	case BE_MVP_STEP_FAIL:
		domain_failed(domain, record, result.failure);
	case BE_MVP_STEP_INVALID:
	default:
		fail_domain(result.failure, domain, record->type);
	}
}
#endif

#if defined(BE_MVP_VARIANT_RING_FULL)
/*
 * The ring-full variant (Plan revision M0-A.3): after a domain's ENTERED,
 * hart 0's visits to its ring take none of its records until hart 0 has
 * seen both domains' ENTERED; then it waits the variant's delay once,
 * before its first LINE drain, so a domain hart fills its 1 KiB ring and
 * takes its fallback path while hart 0 waits. The hold applies to each
 * visit of the round-robin drain (Plan revision M0-C.1). The domain harts'
 * code is unchanged.
 */
static be_u32 be_mvp_drain_delayed;

static int drain_held(be_u32 domain)
{
	be_u64 start;

	if (be_mvp_drain_delayed != 0U)
		return 0;
	if (be_mvp_ctl.domain[0].phase < BE_MVP_DOMAIN_ENTERED ||
	    be_mvp_ctl.domain[1].phase < BE_MVP_DOMAIN_ENTERED)
		return be_mvp_ctl.domain[domain].phase >=
		       BE_MVP_DOMAIN_ENTERED;
	start = be_mvp_exec_read_time();
	while (be_mvp_exec_read_time() - start <
	       BE_MVP_VARIANT_DRAIN_DELAY_TICKS)
		;
	be_mvp_drain_delayed = 1U;
	return 0;
}
#endif

/*
 * One visit to a domain's outbound ring (Plan revision M0-C.1): acquire
 * its head, take at most one record, release the tail, then step the
 * record, whose copy is hart 0's, so the ring's bytes are free before the
 * console prints it. Hart 0's only post-barrier writes into the domain's
 * block are this tail and, in ping() and domain_failed(), the inbound
 * ring's bytes and head.
 *
 * Return: 1 when the visit took a record; 0 for an empty ring, or a held
 *         one in the ring-full variant.
 */
static int visit(be_u32 domain)
{
	struct be_mvp_ring *ring = &be_mvp_outbound[domain];
	enum be_mvp_ring_status status;

#if defined(BE_MVP_VARIANT_RING_FULL)
	if (drain_held(domain))
		return 0;
#endif
	if (be_mvp_ring_acquire(ring) == 0U) {
		if (ring->failed != 0U)
			fail_domain(BE_MVP_CLASS_RING, domain, 0U);
		return 0;
	}
	/* Reader: the head, then the record it admits. */
	be_mvp_exec_fence_r_r();
	status = be_mvp_ring_take(ring, &be_mvp_record);
	if (status != BE_MVP_RING_RECORD && status != BE_MVP_RING_EMPTY)
		fail_domain(BE_MVP_CLASS_RING, domain, 0U);
	/* Reader: the copy out before the tail that frees its bytes. */
	be_mvp_exec_fence_r_w();
	if (!be_mvp_ring_release(ring))
		fail_domain(BE_MVP_CLASS_RING, domain, 0U);
	if (status != BE_MVP_RING_RECORD)
		return 0;
	step(domain, &be_mvp_record);
	return 1;
}

/*
 * Drain the outbound rings round-robin (Plan revision M0-C.1): one visit
 * to domain 0's ring, then one to domain 1's, and again, until a visit to
 * each ring in turn takes nothing, so the printed order follows the order
 * in which records became visible to hart 0. The order and its bound, each
 * ring's capacity in record headers plus one visit, are those of
 * be_mvp_drain_begin(), be_mvp_drain_next(), and be_mvp_drain_visited()
 * (mvp-hart.h). The probe images visit domain 0's ring alone.
 */
static void drain(void)
{
	struct be_mvp_drain order;
	be_u32 domain;

	be_mvp_drain_begin(&order, BE_MVP_RUN_DOMAINS,
			   BE_MVP_RUN_OUTBOUND_BYTES);
	for (domain = be_mvp_drain_next(&order); domain < BE_MVP_DOMAINS;
	     domain = be_mvp_drain_next(&order))
		be_mvp_drain_visited(&order, visit(domain));
}

/*
 * A failed wake: a domain hart that never posted READY names itself;
 * the run budget names the run's ticks.
 */
static void wake_failed(enum be_mvp_class failure, be_u64 now)
	__attribute__((noreturn));
static void wake_failed(enum be_mvp_class failure, be_u64 now)
{
	be_u64 values[3] = { 0U, 0U, since(now) };
	be_u32 domain = be_mvp_ctl.domain[0].phase == BE_MVP_DOMAIN_STARTED ?
		0U : 1U;

	if (failure != BE_MVP_CLASS_HART_READY)
		fail_detail(failure, marker_detail_ticks, &values[2]);
	values[0] = domain;
	values[1] = be_mvp_bindings[domain].hart;
	fail_detail(failure, marker_detail_waited, values);
}

/*
 * The READY wait: poll both rings, without a second timer write, until
 * both domains are READY or the READY wait or the run budget has passed.
 */
static void wait_ready(void)
{
	for (;;) {
		be_u64 now;
		be_u64 elapsed;

		drain();
#if defined(BE_MVP_PROBE_IMAGE)
		if (be_mvp_ctl.domain[0].phase >= BE_MVP_DOMAIN_READY)
			return;
#else
		if (be_mvp_ctl.domain[0].phase >= BE_MVP_DOMAIN_READY &&
		    be_mvp_ctl.domain[1].phase >= BE_MVP_DOMAIN_READY)
			return;
#endif
		now = be_mvp_exec_read_time();
		elapsed = since(now);
		if (now < be_mvp_ctl.start ||
		    elapsed >= be_mvp_ctl.ready_ticks ||
		    elapsed >= be_mvp_ctl.budget)
#if defined(BE_MVP_PROBE_IMAGE)
			wake_failed(BE_MVP_CLASS_HART_READY, now);
#else
			wake_failed(be_mvp_control_wake(&be_mvp_ctl, now), now);
#endif
	}
}

#if !defined(BE_MVP_PROBE_IMAGE)
/*
 * The control loop: wait in wfi for the IPI or the budget timer, clear
 * SSIP, and drain both rings round-robin (Plan revision M0-C.1). A wake by
 * the budget timer at the budget's end is run-timeout. With console input
 * armed (planning/mvp-m7-plan.md, D-1), each wake then polls the firmware
 * console and re-arms the timer for the next poll.
 */
static void control_loop(void) __attribute__((noreturn));
static void control_loop(void)
{
	for (;;) {
		be_u64 before = be_mvp_exec_read_time();
		be_u64 now = be_mvp_exec_wait(BE_MVP_SIE_CONTROL);
		enum be_mvp_class failure;

		be_mvp_control_waited(&be_mvp_ctl, now - before);
		failure = be_mvp_control_wake(&be_mvp_ctl, now);
		if (failure != BE_MVP_CLASS_NONE)
			wake_failed(failure, now);
		(void)be_mvp_exec_clear_ssip();
		drain();
		if (be_mvp_console_in.armed != 0U) {
			poll_input();
			rearm_input();
		}
	}
}
#else
/* The probe module's view of hart 0's runtime (mvp-probe.h). */
void be_mvp_probe_emit(const char *format, const be_u64 *values)
{
	emit(format, values);
}

void be_mvp_probe_poll(void)
{
	drain();
}

void be_mvp_probe_fail(enum be_mvp_class failure, const char *format,
		       const be_u64 *values)
{
	fail_detail(failure, format, values);
}

void be_mvp_probe_shutdown(void)
{
	log_terminal();
	emit_text(marker_shutdown);
	(void)be_mvp_exec_system_reset();
	/* A conforming shutdown does not return. */
	terminal(BE_MVP_CLASS_SHUTDOWN_RETURNED, 0);
}
#endif

/*
 * After the barrier: hart 0's budget (stimecmp, SSIE and STIE; with
 * console input armed, the first poll's deadline, before the budget's
 * end), the control loop's clocks, both hart starts, the READY wait, and
 * the loop.
 */
static void start_run(void) __attribute__((noreturn));
static void start_run(void)
{
	be_u64 now = be_mvp_exec_read_time();
	be_u64 deadline = now + BE_MVP_RUN_TIME_BUDGET;

#if !defined(BE_MVP_PROBE_IMAGE)
	(void)be_mvp_input_rearm(&be_mvp_console_in, now,
				 BE_MVP_RUN_TIME_BUDGET, now, &deadline);
#endif
	if (be_mvp_exec_arm_budget(deadline,
				   symbol_address(__be_control_stack_end)) !=
	    BE_MVP_SIE_CONTROL)
		be_mvp_runtime_terminal(BE_MVP_CLASS_CONTROLS);
	be_mvp_control_init(&be_mvp_ctl, now, BE_MVP_RUN_TIME_BUDGET,
			    BE_MVP_READY_TICKS);
#if BE_MVP_RUN_ACCEPT_DENIAL
	/* What a DENIAL is checked against, the sealed pages or channel; an
	 * image that accepts no denial never gives it, so its loop refuses
	 * every DENIAL as ring. */
#if BE_MVP_RUN_PAGES
	if (!be_mvp_control_pages(&be_mvp_ctl, be_mvp_maps,
				  be_mvp_sealed_pages, BE_MVP_SCENARIO_PAGES))
		be_mvp_runtime_terminal(BE_MVP_CLASS_EXCEPTION);
#else
	if (!be_mvp_control_channel(&be_mvp_ctl, be_mvp_maps,
				    &be_mvp_sealed_channel))
		be_mvp_runtime_terminal(BE_MVP_CLASS_EXCEPTION);
#endif
#endif
#if BE_MVP_RUN_ACCEPT_MGMT
	/* The sealed grants and hart 0's management state; an image without
	 * the extension never gives them, so its loop refuses every
	 * management record as ring. */
	if (!be_mvp_control_mgmt(&be_mvp_ctl, &be_mvp_mgmt_state, be_mvp_grants,
				 BE_MVP_SCENARIO_GRANTS,
				 BE_MVP_RUN_GRANT_CHECK))
		be_mvp_runtime_terminal(BE_MVP_CLASS_EXCEPTION);
#endif
	start_harts();
	wait_ready();
#if defined(BE_MVP_PROBE_IMAGE)
	be_mvp_probe_run();
#else
	control_loop();
#endif
}

void be_mvp_runtime_main(be_u64 hart_id, be_u64 firmware_pointer)
{
	struct be_r3_boot_contract boot = { 0 };
	be_u32 domain;

	clear_mvp_bss();
	build_image_layout(&be_mvp_layout);
	boot.entry = symbol_address(be_reset);
	boot.hart_id = hart_id;
	boot.firmware_pointer = firmware_pointer;
	boot.layout = be_mvp_layout;
	if (be_mvp_exec_sbi_version(&boot.sbi_spec_version) !=
		    BE_R0_SBI_SUCCESS ||
	    be_mvp_exec_sbi_probe(BE_R0_SBI_EID_DBCN,
				  &boot.dbcn_probe) != BE_R0_SBI_SUCCESS ||
	    be_mvp_exec_sbi_probe(BE_R0_SBI_EID_SRST,
				  &boot.srst_probe) != BE_R0_SBI_SUCCESS ||
	    be_r3_validate_boot(&be_mvp_r3_control, &boot) != BE_R3_ERROR_NONE)
		boot_fail();
	emit_text(marker_boot);
	seal_config();
	/*
	 * Hart 0's HS and VS state, reset through the accepted function as each
	 * domain hart's is, with its stvec the vector, which sends its HS
	 * exceptions to its terminal, and hgatp Bare: hart 0 runs no guest, so
	 * no binding is prepared or published (D-3).
	 */
	be_mvp_exec_reset_hs_state(be_mvp_layout.trap_vector, &be_mvp_hs);

	scenario_line();
	probe_firmware();
	probe_sstc();
	build_gstage();
#if defined(BE_MVP_PROBE_IMAGE)
	/*
	 * The probe module replaces the payload checks and placement: the
	 * stub, entered at the kernel's GPA with a1 = 0, and X in each window.
	 */
#if defined(BE_MVP_RUN_PROBE_PLATFORM)
	be_mvp_probe_hgatp();
#endif
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		clear_guest_ram(domain);
	be_mvp_probe_place(be_mvp_maps);
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		be_mvp_plans[domain].kernel_gpa = BE_MVP_PROBE_STUB_GPA;
#else
	check_payload();
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		clear_guest_ram(domain);
#if BE_MVP_RUN_CHANNELS
	clear_channel();
#elif BE_MVP_RUN_PAGES
	place_pages();
#endif
	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		place_payload(domain);
#endif
	measure_log();
	be_mvp_exec_fence_rw_rw();
	publish_blocks();
#if !defined(BE_MVP_PROBE_IMAGE)
	arm_input();
#endif
	start_run();
}
