// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the MVP payload checks: every link-time
 *          layout rule and budget, including both DTB offsets; each
 *          window's placement (the kernel span against the DTB slot, the
 *          staged image against both windows, the monitor's core, both
 *          pools, the hart region, the MVP region, and the shared pages,
 *          and the windows against each other); every byte of both kernel
 *          magics, the kernel's text_offset, endianness, and image_size
 *          rules; each DTB's magic, totalsize, version, and block rules; and
 *          both plans. It then runs the same checks on the staged payload
 *          the monitor is built for (KERNEL, DTB0, and DTB1, with the
 *          generated layout), with the payload variant's altered magic2,
 *          and with each variant DTB in each domain's slot.
 * Trust:   host evidence only. No CSR, copy into guest RAM, guest entry,
 *          QEMU, or hardware behaviour is exercised.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, "Memory and load
 *          paths"; planning/mvp-m1-plan.md and planning/mvp-m2-plan.md,
 *          "Memory and load paths").
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mvp-payload.h"
#include "mvp-payload-layout.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_PAYLOAD_CHECK: assertion failed: %s:%d: %s\n", \
			       __FILE__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define MIB			(BE_U64_C(1) << 20)
#define L_HPA			BE_U64_C(0x108000000)
/* The kernel follows the stub page and the 0xa4000-byte flat image. */
#define KERNEL_OFFSET		BE_U64_C(0xa5000)
#define SYNTH_KERNEL_BYTES	BE_U64_C(0x2345)
#define SYNTH_IMAGE_SIZE	BE_U64_C(0x10000)
#define SYNTH_DTB0_OFFSET	BE_U64_C(0xa8000)
#define SYNTH_DTB1_OFFSET	BE_U64_C(0xa9000)
#define SYNTH_IMAGE_BYTES	BE_U64_C(0xaa000)
#define ALL_ONES		(~BE_U64_C(0))

static be_u8 synthetic[SYNTH_IMAGE_BYTES];
static be_u8 *staged;
static be_u64 staged_bytes;
static struct be_mvp_gstage_map windows[2];

static void put_le(be_u8 *destination, be_u64 value, unsigned int bytes)
{
	unsigned int byte;

	for (byte = 0U; byte < bytes; ++byte)
		destination[byte] = (be_u8)(value >> (8U * byte));
}

static void put_be32(be_u8 *destination, be_u64 value)
{
	destination[0] = (be_u8)(value >> 24);
	destination[1] = (be_u8)(value >> 16);
	destination[2] = (be_u8)(value >> 8);
	destination[3] = (be_u8)value;
}

static struct be_mvp_payload_layout synthetic_layout(void)
{
	return (struct be_mvp_payload_layout) {
		.staging_hpa = L_HPA,
		.kernel_offset = KERNEL_OFFSET,
		.kernel_bytes = SYNTH_KERNEL_BYTES,
		.kernel_image_size = SYNTH_IMAGE_SIZE,
		.dtb_offset = { SYNTH_DTB0_OFFSET, SYNTH_DTB1_OFFSET },
		.dtb_bytes = BE_U64_C(0x1000),
		.image_bytes = SYNTH_IMAGE_BYTES,
	};
}

/* A well-formed FDT header. */
static void synthetic_dtb(be_u8 *dtb)
{
	put_be32(dtb, 0xd00dfeedU);
	put_be32(dtb + 4U, 0x1000U);
	put_be32(dtb + 8U, 0x38U);
	put_be32(dtb + 12U, 0x2f0U);
	put_be32(dtb + 16U, 0x28U);
	put_be32(dtb + 20U, 17U);
	put_be32(dtb + 24U, 16U);
	put_be32(dtb + 32U, 0x80U);
	put_be32(dtb + 36U, 0x2b8U);
}

/* A well-formed kernel header and two FDT headers in the synthetic image. */
static void synthetic_headers(void)
{
	be_u8 *kernel = synthetic + KERNEL_OFFSET;

	memset(synthetic, 0, sizeof(synthetic));
	put_le(kernel, 0x0000a0d1U, 4U);
	put_le(kernel + 8U, 0x200000U, 8U);
	put_le(kernel + 16U, SYNTH_IMAGE_SIZE, 8U);
	put_le(kernel + 32U, 2U, 4U);
	memcpy(kernel + 48U, "RISCV\0\0\0", 8U);
	memcpy(kernel + 56U, "RSC\x05", 4U);
	synthetic_dtb(synthetic + SYNTH_DTB0_OFFSET);
	synthetic_dtb(synthetic + SYNTH_DTB1_OFFSET);
}

static int plan_empty(const struct be_mvp_payload_plan *plan)
{
	return plan->kernel_source == 0U && plan->kernel_target == 0U &&
	       plan->kernel_gpa == 0U && plan->kernel_bytes == 0U &&
	       plan->image_size == 0U && plan->dtb_source == 0U &&
	       plan->dtb_target == 0U && plan->dtb_gpa == 0U &&
	       plan->dtb_bytes == 0U;
}

static enum be_mvp_payload_error check(const struct be_mvp_payload_layout *layout,
				      const struct be_mvp_gstage_map *maps,
				      const be_u8 *image)
{
	struct be_mvp_payload_plan plans[2];
	enum be_mvp_payload_error error;

	memset(plans, 0x5a, sizeof(plans));
	error = be_mvp_payload_check(layout, maps, image, plans);
	/* A refusal leaves both plans empty. */
	if (error != BE_MVP_PAYLOAD_OK)
		CHECK(plan_empty(&plans[0]) && plan_empty(&plans[1]));
	return error;
}

static void build_windows(void)
{
	static be_u8 pool[BE_MVP_GSTAGE_POOL_BYTES];
	struct be_mvp_gstage_desc desc[2] = {
		{ BE_MVP_GUEST_GPA, BE_MVP_G0_HPA, BE_MVP_GUEST_BYTES,
		  BE_MVP_G0_ROOT_HPA, BE_MVP_G0_VMID, BE_MVP_DOMAIN0_HART },
		{ BE_MVP_GUEST_GPA, BE_MVP_G1_HPA, BE_MVP_GUEST_BYTES,
		  BE_MVP_G1_ROOT_HPA, BE_MVP_G1_VMID, BE_MVP_DOMAIN1_HART },
	};
	unsigned int guest;

	for (guest = 0U; guest < 2U; ++guest) {
		CHECK(be_mvp_gstage_build(&desc[guest], pool, sizeof(pool)) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk(&desc[guest], pool, sizeof(pool),
					&windows[guest]) == BE_MVP_GSTAGE_OK);
	}
	CHECK(be_mvp_gstage_pair_check(&windows[0], &windows[1]) ==
	      BE_MVP_GSTAGE_OK);
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(BE_MVP_STAGING_HPA == L_HPA);
	CHECK(BE_MVP_BOOT_KERNEL_OFFSET == KERNEL_OFFSET);
	CHECK(BE_MVP_IMAGE_BYTES == KERNEL_OFFSET - 0x1000U);
	CHECK(BE_MVP_KERNEL_FILE_MAX == 4U * MIB);
	CHECK(BE_MVP_KERNEL_IMAGE_SIZE_MAX == 8U * MIB);
	CHECK(BE_MVP_BOOT_IMAGE_MAX == 4U * MIB);
	CHECK(BE_MVP_DTB_BYTES == 0x1000U);
	CHECK(BE_MVP_KERNEL_GPA == BE_U64_C(0x80200000));
	CHECK(BE_MVP_DTB_GPA == BE_U64_C(0x83e00000));
	CHECK(BE_MVP_G0_HPA == BE_U64_C(0x110000000));
	CHECK(BE_MVP_G1_HPA == BE_U64_C(0x114000000));
	CHECK(sizeof(struct be_mvp_payload_layout) == 8U * sizeof(be_u64));
	CHECK(sizeof(struct be_mvp_payload_plan) == 9U * sizeof(be_u64));
	/* The generated layout holds the rules the monitor checks again. */
	CHECK(BE_MVP_PAYLOAD_KERNEL_BYTES >= 64U &&
	      BE_MVP_PAYLOAD_KERNEL_BYTES <= BE_MVP_KERNEL_FILE_MAX);
	CHECK(BE_MVP_PAYLOAD_KERNEL_IMAGE_SIZE >= BE_MVP_PAYLOAD_KERNEL_BYTES &&
	      BE_MVP_PAYLOAD_KERNEL_IMAGE_SIZE <= BE_MVP_KERNEL_IMAGE_SIZE_MAX);
	CHECK(BE_MVP_PAYLOAD_DTB0_OFFSET ==
	      ((KERNEL_OFFSET + BE_MVP_PAYLOAD_KERNEL_BYTES + 0xfffU) &
	       ~0xfffUL));
	CHECK(BE_MVP_PAYLOAD_DTB1_OFFSET == BE_MVP_PAYLOAD_DTB0_OFFSET + 0x1000U);
	CHECK(BE_MVP_PAYLOAD_IMAGE_BYTES == BE_MVP_PAYLOAD_DTB1_OFFSET + 0x1000U);
	CHECK(BE_MVP_PAYLOAD_IMAGE_BYTES <= BE_MVP_BOOT_IMAGE_MAX);
}

static void test_good(void)
{
	struct be_mvp_payload_layout layout = synthetic_layout();
	struct be_mvp_payload_plan plans[2];
	struct be_mvp_gstage_map swapped[2] = { windows[1], windows[0] };

	SCENARIO();
	synthetic_headers();
	CHECK(be_mvp_payload_check(&layout, windows, synthetic, plans) ==
	      BE_MVP_PAYLOAD_OK);
	/* One kernel source, copied into each window; one DTB each. */
	CHECK(plans[0].kernel_source == L_HPA + KERNEL_OFFSET);
	CHECK(plans[1].kernel_source == L_HPA + KERNEL_OFFSET);
	CHECK(plans[0].kernel_target == BE_U64_C(0x110200000));
	CHECK(plans[1].kernel_target == BE_U64_C(0x114200000));
	CHECK(plans[0].kernel_gpa == BE_MVP_KERNEL_GPA &&
	      plans[1].kernel_gpa == BE_MVP_KERNEL_GPA);
	CHECK(plans[0].kernel_bytes == SYNTH_KERNEL_BYTES &&
	      plans[1].kernel_bytes == SYNTH_KERNEL_BYTES);
	CHECK(plans[0].image_size == SYNTH_IMAGE_SIZE &&
	      plans[1].image_size == SYNTH_IMAGE_SIZE);
	CHECK(plans[0].dtb_source == L_HPA + SYNTH_DTB0_OFFSET);
	CHECK(plans[1].dtb_source == L_HPA + SYNTH_DTB1_OFFSET);
	CHECK(plans[0].dtb_target == BE_U64_C(0x113e00000));
	CHECK(plans[1].dtb_target == BE_U64_C(0x117e00000));
	CHECK(plans[0].dtb_gpa == BE_MVP_DTB_GPA &&
	      plans[1].dtb_gpa == BE_MVP_DTB_GPA);
	CHECK(plans[0].dtb_bytes == 0x1000U && plans[1].dtb_bytes == 0x1000U);
	/* The maps' order is the domains' order: G0's DTB goes to map 0. */
	CHECK(be_mvp_payload_check(&layout, swapped, synthetic, plans) ==
	      BE_MVP_PAYLOAD_OK);
	CHECK(plans[0].kernel_target == BE_U64_C(0x114200000) &&
	      plans[0].dtb_source == L_HPA + SYNTH_DTB0_OFFSET);
	/* Null arguments. */
	CHECK(be_mvp_payload_check(&layout, windows, synthetic,
				  (struct be_mvp_payload_plan *)0) ==
	      BE_MVP_PAYLOAD_NULL);
	CHECK(check((const struct be_mvp_payload_layout *)0, windows,
		    synthetic) == BE_MVP_PAYLOAD_NULL);
	CHECK(check(&layout, (const struct be_mvp_gstage_map *)0, synthetic) ==
	      BE_MVP_PAYLOAD_NULL);
	CHECK(check(&layout, windows, (const be_u8 *)0) == BE_MVP_PAYLOAD_NULL);
}

static void test_layout(void)
{
	static const struct {
		unsigned int field;
		be_u64 value;
	} cases[] = {
		{ 0U, L_HPA + 0x800U },
		{ 1U, KERNEL_OFFSET - 0x1000U },
		{ 1U, KERNEL_OFFSET + 0x1000U }, { 1U, 0U },
		{ 2U, 0U }, { 2U, 63U }, { 2U, SYNTH_KERNEL_BYTES + 0x1000U },
		{ 2U, 4U * MIB + 1U }, { 2U, ALL_ONES },
		{ 3U, SYNTH_KERNEL_BYTES - 1U }, { 3U, 8U * MIB + 1U },
		{ 3U, ALL_ONES },
		{ 4U, SYNTH_DTB0_OFFSET - 0x1000U },
		{ 4U, SYNTH_DTB0_OFFSET + 0x1000U },
		{ 4U, SYNTH_DTB0_OFFSET + 8U },
		{ 4U, KERNEL_OFFSET + SYNTH_KERNEL_BYTES },
		{ 4U, SYNTH_DTB1_OFFSET },
		{ 5U, SYNTH_DTB0_OFFSET }, { 5U, SYNTH_DTB1_OFFSET + 0x1000U },
		{ 5U, SYNTH_DTB1_OFFSET - 8U }, { 5U, SYNTH_DTB1_OFFSET + 8U },
		{ 5U, 0U },
		{ 6U, 0U }, { 6U, 0x800U }, { 6U, 0x2000U },
		{ 7U, SYNTH_IMAGE_BYTES - 0x1000U },
		{ 7U, SYNTH_IMAGE_BYTES + 0x1000U }, { 7U, 0U },
	};
	struct be_mvp_payload_layout layout;
	be_u64 *fields = (be_u64 *)(void *)&layout;
	be_size index;

	SCENARIO();
	synthetic_headers();
	for (index = 0U; index < BE_ARRAY_SIZE(cases); ++index) {
		layout = synthetic_layout();
		fields[cases[index].field] = cases[index].value;
		CHECK(check(&layout, windows, synthetic) ==
		      BE_MVP_PAYLOAD_LAYOUT);
	}
	/* The largest kernel file the 4 MiB boot image admits; the header's
	 * image_size then differs, which stops the check before the DTB. */
	layout = synthetic_layout();
	layout.kernel_bytes = 4U * MIB - KERNEL_OFFSET - 0x2000U;
	layout.kernel_image_size = layout.kernel_bytes;
	layout.dtb_offset[0] = 4U * MIB - 0x2000U;
	layout.dtb_offset[1] = 4U * MIB - 0x1000U;
	layout.image_bytes = 4U * MIB;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_SIZE);
	layout.kernel_bytes += 1U;
	layout.kernel_image_size += 1U;
	layout.dtb_offset[0] += 0x1000U;
	layout.dtb_offset[1] += 0x1000U;
	layout.image_bytes += 0x1000U;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_LAYOUT);
	/* image_size up to 8 MiB is admitted. */
	layout = synthetic_layout();
	layout.kernel_image_size = 8U * MIB;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_SIZE);
	/* The staged image must not wrap. */
	layout = synthetic_layout();
	layout.staging_hpa = ALL_ONES - 0xfffU;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_LAYOUT);
	layout.staging_hpa = (ALL_ONES - SYNTH_IMAGE_BYTES + 1U) & ~0xfffUL;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_LAYOUT);
	layout.staging_hpa = (ALL_ONES - SYNTH_IMAGE_BYTES) & ~0xfffUL;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_OK);
}

static void test_window(void)
{
	struct be_mvp_payload_layout layout = synthetic_layout();
	struct be_mvp_gstage_map maps[2] = { windows[0], windows[1] };
	struct be_mvp_payload_plan plans[2];
	unsigned int guest;

	SCENARIO();
	for (guest = 0U; guest < 2U; ++guest) {
		layout = synthetic_layout();
		synthetic_headers();
		maps[0] = windows[0];
		maps[1] = windows[1];
		/* An 8 MiB window: the kernel span may reach its DTB slot. */
		maps[guest].size = 8U * MIB;
		maps[guest].leaves = 4U;
		layout.kernel_image_size = 4U * MIB;
		put_le(synthetic + KERNEL_OFFSET + 16U, 4U * MIB, 8U);
		CHECK(be_mvp_payload_check(&layout, maps, synthetic, plans) ==
		      BE_MVP_PAYLOAD_OK);
		CHECK(plans[guest].dtb_gpa == BE_U64_C(0x80600000) &&
		      plans[guest].dtb_target ==
			      windows[guest].hpa_base + 6U * MIB);
		layout.kernel_image_size = 4U * MIB + 1U;
		put_le(synthetic + KERNEL_OFFSET + 16U, 4U * MIB + 1U, 8U);
		CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
		/* Too small for a kernel slot and a DTB slot. */
		layout = synthetic_layout();
		synthetic_headers();
		maps[guest].size = 4U * MIB;
		CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
		maps[guest].size = 2U * MIB;
		CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
		maps[guest].size = 0U;
		CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
		maps[guest] = windows[guest];
		maps[guest].gpa_base = ALL_ONES - 32U * MIB;
		CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
		maps[guest] = windows[guest];
		/* The staged image inside or touching this window or its pool. */
		layout.staging_hpa = windows[guest].hpa_base;
		CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
		layout.staging_hpa = windows[guest].hpa_base + 64U * MIB -
				     0x1000U;
		CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
		layout.staging_hpa = windows[guest].hpa_base -
				     SYNTH_IMAGE_BYTES + 0x1000U;
		CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
		layout.staging_hpa = windows[guest].pool_pa + 0x7000U;
		CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
		layout.staging_hpa = windows[guest].pool_pa -
				     SYNTH_IMAGE_BYTES + 0x1000U;
		CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	}
	layout = synthetic_layout();
	/* Just below G0's window, just above the shared pages beyond G1's,
	 * and between the MVP region's end and the staging slot: outside
	 * everything. */
	layout.staging_hpa = BE_MVP_G0_HPA - SYNTH_IMAGE_BYTES;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_OK);
	layout.staging_hpa = BE_MVP_SHARED_PAGES_HPA +
			     BE_MVP_SHARED_PAGES_BYTES;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_OK);
	layout.staging_hpa = BE_MVP_REGION_HPA + BE_MVP_REGION_BYTES;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_OK);
	/* The channel page (planning/mvp-m1-plan.md, "Memory and load
	 * paths"), which G1's window's end starts, and the shared pages'
	 * last (planning/mvp-m2-plan.md), which the channel page's end
	 * starts. */
	layout.staging_hpa = BE_MVP_G1_HPA + 64U * MIB;
	CHECK(layout.staging_hpa == BE_MVP_CHANNEL_HPA);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_MVP_CHANNEL_HPA + BE_MVP_CHANNEL_BYTES;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_MVP_SHARED_PAGES_HPA +
			     BE_MVP_SHARED_PAGES_BYTES - 0x1000U;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	/* The MVP region, which the hart region's end starts: its start, its
	 * last page, and a page inside it. */
	layout.staging_hpa = BE_MVP_HART_REGION_HPA + BE_MVP_HART_REGION_BYTES;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_MVP_REGION_HPA + BE_MVP_REGION_BYTES - 0x1000U;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_MVP_REGION_HPA + 0x1000U;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	/* The hart region: the pools' end is its start; either block, its
	 * rings, and an image that reaches into it from below. */
	layout.staging_hpa = BE_MVP_POOL_HPA + BE_MVP_POOL_BYTES;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_MVP_G1_BLOCK_HPA + BE_MVP_BLOCK_OUTBOUND_OFFSET;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_MVP_HART_REGION_HPA +
			     BE_MVP_HART_REGION_BYTES - 0x1000U;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_MVP_HART_REGION_HPA - SYNTH_IMAGE_BYTES +
			     0x1000U;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	/* The monitor's core. */
	layout.staging_hpa = BE_MVP_MONITOR_HPA;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_MVP_MONITOR_HPA - SYNTH_IMAGE_BYTES + 0x1000U;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_MVP_MONITOR_HPA - SYNTH_IMAGE_BYTES;
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_OK);
	/* Windows that overlap, in either order, or are the same window. */
	layout = synthetic_layout();
	maps[0] = windows[0];
	maps[1] = windows[1];
	maps[1].hpa_base = windows[0].hpa_base + 62U * MIB;
	CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	maps[0] = windows[1];
	maps[1] = windows[1];
	CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
	maps[0] = windows[1];
	maps[1] = windows[0];
	maps[1].hpa_base = windows[1].hpa_base + 62U * MIB;
	CHECK(check(&layout, maps, synthetic) == BE_MVP_PAYLOAD_WINDOW);
}

static void test_kernel(void)
{
	struct be_mvp_payload_layout layout = synthetic_layout();
	be_u8 *kernel = synthetic + KERNEL_OFFSET;
	unsigned int index;
	unsigned int bit;

	SCENARIO();
	/* Every bit of both magics. */
	for (index = 0U; index < 12U; ++index) {
		for (bit = 0U; bit < 8U; ++bit) {
			synthetic_headers();
			kernel[48U + index] ^= (be_u8)(1U << bit);
			CHECK(check(&layout, windows, synthetic) ==
			      (index < 8U ? BE_MVP_PAYLOAD_KERNEL_MAGIC :
					    BE_MVP_PAYLOAD_KERNEL_MAGIC2));
		}
	}
	/* text_offset: only 0x200000. */
	synthetic_headers();
	put_le(kernel + 8U, 0U, 8U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_OFFSET);
	put_le(kernel + 8U, 0x400000U, 8U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_OFFSET);
	put_le(kernel + 8U, 0x200000U | (BE_U64_C(1) << 63), 8U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_OFFSET);
	/* flags bit 0 is big-endian; the other bits are not checked. */
	synthetic_headers();
	put_le(kernel + 24U, 1U, 8U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_ENDIAN);
	put_le(kernel + 24U, ALL_ONES, 8U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_ENDIAN);
	put_le(kernel + 24U, 2U, 8U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_OK);
	/* image_size: at least the file and exactly the layout's. */
	synthetic_headers();
	put_le(kernel + 16U, SYNTH_KERNEL_BYTES - 1U, 8U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_SIZE);
	put_le(kernel + 16U, SYNTH_IMAGE_SIZE + 1U, 8U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_SIZE);
	put_le(kernel + 16U, 0U, 8U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_SIZE);
	put_le(kernel + 16U, ALL_ONES, 8U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_KERNEL_SIZE);
	/* The code words, version, and reserved words are content, not shape. */
	synthetic_headers();
	memset(kernel, 0xff, 8U);
	memset(kernel + 32U, 0xff, 16U);
	memset(kernel + 60U, 0xff, 4U);
	CHECK(check(&layout, windows, synthetic) == BE_MVP_PAYLOAD_OK);
}

static void test_dtb(void)
{
	static const struct {
		unsigned int offset;
		be_u64 value;
		enum be_mvp_payload_error error;
	} cases[] = {
		{ 0U, 0xedfe0dd0U, BE_MVP_PAYLOAD_DTB_MAGIC },
		{ 0U, 0U, BE_MVP_PAYLOAD_DTB_MAGIC },
		{ 4U, 0xfffU, BE_MVP_PAYLOAD_DTB_SIZE },
		{ 4U, 0x1001U, BE_MVP_PAYLOAD_DTB_SIZE },
		{ 4U, 0x10000U, BE_MVP_PAYLOAD_DTB_SIZE },
		{ 20U, 16U, BE_MVP_PAYLOAD_DTB_VERSION },
		{ 20U, 18U, BE_MVP_PAYLOAD_DTB_VERSION },
		{ 20U, 0U, BE_MVP_PAYLOAD_DTB_VERSION },
		/* Reserve map: after the header, 8-byte aligned, inside. */
		{ 16U, 0x20U, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 16U, 0x2cU, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 16U, 0xff8U, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 16U, 0x1000U, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 16U, 0xffffffffU, BE_MVP_PAYLOAD_DTB_BLOCKS },
		/* Structure block: after the header, 4-byte aligned, inside. */
		{ 8U, 0x24U, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 8U, 0x3aU, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 8U, 0xd4cU, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 8U, 0xffffffffU, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 36U, 0xfc9U, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 36U, 0xffffffffU, BE_MVP_PAYLOAD_DTB_BLOCKS },
		/* Strings block: after the header, inside. */
		{ 12U, 0x27U, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 12U, 0xf81U, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 32U, 0xd11U, BE_MVP_PAYLOAD_DTB_BLOCKS },
		{ 32U, 0xffffffffU, BE_MVP_PAYLOAD_DTB_BLOCKS },
		/* Exact fits pass. */
		{ 16U, 0xff0U, BE_MVP_PAYLOAD_OK },
		{ 8U, 0xd48U, BE_MVP_PAYLOAD_OK },
		{ 36U, 0xfc8U, BE_MVP_PAYLOAD_OK },
		{ 12U, 0xf80U, BE_MVP_PAYLOAD_OK },
		{ 32U, 0xd10U, BE_MVP_PAYLOAD_OK },
		{ 24U, 17U, BE_MVP_PAYLOAD_OK },
		{ 28U, 0xffffffffU, BE_MVP_PAYLOAD_OK },
	};
	static const be_u64 offsets[2] = { SYNTH_DTB0_OFFSET, SYNTH_DTB1_OFFSET };
	struct be_mvp_payload_layout layout = synthetic_layout();
	be_size index;
	unsigned int guest;

	SCENARIO();
	for (guest = 0U; guest < 2U; ++guest) {
		for (index = 0U; index < BE_ARRAY_SIZE(cases); ++index) {
			synthetic_headers();
			put_be32(synthetic + offsets[guest] +
					 cases[index].offset,
				 cases[index].value);
			CHECK(check(&layout, windows, synthetic) ==
			      cases[index].error);
		}
	}
	/* The kernel is checked first: a bad kernel hides a bad DTB. */
	synthetic_headers();
	synthetic[KERNEL_OFFSET + 56U] = 0U;
	synthetic[SYNTH_DTB0_OFFSET] = 0U;
	synthetic[SYNTH_DTB1_OFFSET] = 0U;
	CHECK(check(&layout, windows, synthetic) ==
	      BE_MVP_PAYLOAD_KERNEL_MAGIC2);
	/* G0's DTB is checked before G1's. */
	synthetic_headers();
	synthetic[SYNTH_DTB0_OFFSET + 23U] = 16U;
	synthetic[SYNTH_DTB1_OFFSET] = 0U;
	CHECK(check(&layout, windows, synthetic) ==
	      BE_MVP_PAYLOAD_DTB_VERSION);
}

static be_u8 *read_file(const char *path, be_u64 *bytes)
{
	FILE *file = fopen(path, "rb");
	be_u8 *data;
	long length;

	CHECK(file != (FILE *)0);
	CHECK(fseek(file, 0L, SEEK_END) == 0);
	length = ftell(file);
	CHECK(length > 0 && length <= (long)(8U * MIB));
	CHECK(fseek(file, 0L, SEEK_SET) == 0);
	data = malloc((size_t)length);
	CHECK(data != (be_u8 *)0);
	CHECK(fread(data, 1U, (size_t)length, file) == (size_t)length);
	CHECK(fclose(file) == 0);
	*bytes = (be_u64)length;
	return data;
}

static const struct be_mvp_payload_layout generated = {
	.staging_hpa = BE_MVP_STAGING_HPA,
	.kernel_offset = BE_MVP_BOOT_KERNEL_OFFSET,
	.kernel_bytes = BE_MVP_PAYLOAD_KERNEL_BYTES,
	.kernel_image_size = BE_MVP_PAYLOAD_KERNEL_IMAGE_SIZE,
	.dtb_offset = { BE_MVP_PAYLOAD_DTB0_OFFSET, BE_MVP_PAYLOAD_DTB1_OFFSET },
	.dtb_bytes = BE_MVP_DTB_BYTES,
	.image_bytes = BE_MVP_PAYLOAD_IMAGE_BYTES,
};

/* The staged payload the monitor is built for, as the loaders place it. */
static void test_staged(const char *kernel_path, const char *dtb0_path,
			const char *dtb1_path)
{
	static const be_u64 dtb_offsets[2] = { BE_MVP_PAYLOAD_DTB0_OFFSET,
					       BE_MVP_PAYLOAD_DTB1_OFFSET };
	struct be_mvp_payload_plan plans[2];
	be_u64 kernel_bytes;
	be_u64 dtb_bytes[2];
	be_u8 *kernel = read_file(kernel_path, &kernel_bytes);
	be_u8 *dtb[2] = { read_file(dtb0_path, &dtb_bytes[0]),
			  read_file(dtb1_path, &dtb_bytes[1]) };
	unsigned int guest;

	SCENARIO();
	CHECK(kernel_bytes == BE_MVP_PAYLOAD_KERNEL_BYTES);
	CHECK(dtb_bytes[0] == BE_MVP_DTB_BYTES && dtb_bytes[1] == BE_MVP_DTB_BYTES);
	/* The domains' DTBs are distinct files. */
	CHECK(memcmp(dtb[0], dtb[1], (size_t)BE_MVP_DTB_BYTES) != 0);
	staged_bytes = BE_MVP_PAYLOAD_IMAGE_BYTES;
	staged = calloc(1U, (size_t)staged_bytes);
	CHECK(staged != (be_u8 *)0);
	memcpy(staged + BE_MVP_BOOT_KERNEL_OFFSET, kernel, (size_t)kernel_bytes);
	for (guest = 0U; guest < 2U; ++guest)
		memcpy(staged + dtb_offsets[guest], dtb[guest],
		       (size_t)dtb_bytes[guest]);
	CHECK(be_mvp_payload_check(&generated, windows, staged, plans) ==
	      BE_MVP_PAYLOAD_OK);
	for (guest = 0U; guest < 2U; ++guest) {
		CHECK(plans[guest].kernel_source == BE_U64_C(0x1080a5000));
		CHECK(plans[guest].kernel_target ==
		      windows[guest].hpa_base + 0x200000U);
		CHECK(plans[guest].kernel_gpa == BE_U64_C(0x80200000));
		CHECK(plans[guest].kernel_bytes == kernel_bytes);
		CHECK(plans[guest].image_size ==
		      BE_MVP_PAYLOAD_KERNEL_IMAGE_SIZE);
		CHECK(plans[guest].dtb_source ==
		      BE_U64_C(0x108000000) + dtb_offsets[guest]);
		CHECK(plans[guest].dtb_target ==
		      windows[guest].hpa_base + 62U * MIB);
		CHECK(plans[guest].dtb_gpa == BE_U64_C(0x83e00000));
		CHECK(plans[guest].dtb_bytes == 0x1000U);
		/* The span ends below the DTB slot, inside the window. */
		CHECK(plans[guest].kernel_gpa + plans[guest].image_size <=
		      plans[guest].dtb_gpa);
	}
	CHECK(plans[0].kernel_target == BE_U64_C(0x110200000) &&
	      plans[1].kernel_target == BE_U64_C(0x114200000));
	CHECK(plans[0].dtb_target == BE_U64_C(0x113e00000) &&
	      plans[1].dtb_target == BE_U64_C(0x117e00000));
	/* The plan's payload variant: magic2 "RSC\0". */
	staged[BE_MVP_BOOT_KERNEL_OFFSET + 0x3bU] = 0U;
	CHECK(check(&generated, windows, staged) ==
	      BE_MVP_PAYLOAD_KERNEL_MAGIC2);
	staged[BE_MVP_BOOT_KERNEL_OFFSET + 0x3bU] = 0x05U;
	CHECK(check(&generated, windows, staged) == BE_MVP_PAYLOAD_OK);
	free(kernel);
	free(dtb[0]);
	free(dtb[1]);
}

/* Each variant DTB has the same shape in either domain's slot. */
static void test_dtb_variants(int count, char **paths)
{
	static const be_u64 dtb_offsets[2] = { BE_MVP_PAYLOAD_DTB0_OFFSET,
					       BE_MVP_PAYLOAD_DTB1_OFFSET };
	be_u8 original[2][BE_MVP_DTB_BYTES];
	unsigned int guest;
	int index;

	SCENARIO();
	for (guest = 0U; guest < 2U; ++guest)
		memcpy(original[guest], staged + dtb_offsets[guest],
		       sizeof(original[guest]));
	for (index = 0; index < count; ++index) {
		be_u64 bytes;
		be_u8 *dtb = read_file(paths[index], &bytes);

		CHECK(bytes == BE_MVP_DTB_BYTES);
		for (guest = 0U; guest < 2U; ++guest) {
			memcpy(staged + dtb_offsets[guest], dtb, (size_t)bytes);
			CHECK(check(&generated, windows, staged) ==
			      BE_MVP_PAYLOAD_OK);
			memcpy(staged + dtb_offsets[guest], original[guest],
			       sizeof(original[guest]));
		}
		free(dtb);
	}
	free(staged);
}

int main(int argc, char **argv)
{
	if (argc < 4) {
		printf("usage: %s KERNEL DTB0 DTB1 [VARIANT_DTB ...]\n", argv[0]);
		return 2;
	}
	build_windows();
	test_constants();
	test_good();
	test_layout();
	test_window();
	test_kernel();
	test_dtb();
	test_staged(argv[1], argv[2], argv[3]);
	test_dtb_variants(argc - 4, argv + 4);
	printf("BE_MVP_PAYLOAD_CHECK: PASS\n");
	printf("BE_MVP_PAYLOAD_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_MVP_PAYLOAD_CHECK: assertions=%lu\n", assertions);
	return 0;
}
