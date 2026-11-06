// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the K3 B6 payload checks: every link-time
 *          layout rule and budget, the window placement (the kernel span
 *          against the DTB slot, the staged image against the window, the
 *          monitor, and the pool), every byte of both kernel magics, the
 *          kernel's text_offset, endianness, and image_size rules, the DTB's
 *          magic, totalsize, version, and block rules, and the plan. It then
 *          runs the same checks on the staged payload the monitor is built
 *          for (KERNEL and DTB, with the generated layout), with the
 *          payload variant's altered magic2, and with each DTB variant.
 * Trust:   host evidence only. No CSR, copy into guest RAM, guest entry,
 *          QEMU, or hardware behaviour is exercised.
 * Scope:   B6 only (planning/k3-b6-plan.md, "Guest-physical layout and
 *          payload checks").
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "b6-payload.h"
#include "b6-payload-layout.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_B6_PAYLOAD_CHECK: assertion failed: %s:%d: %s\n", \
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
#define SYNTH_KERNEL_BYTES	BE_U64_C(0x2345)
#define SYNTH_IMAGE_SIZE	BE_U64_C(0x10000)
#define SYNTH_DTB_OFFSET	BE_U64_C(0x38000)
#define SYNTH_IMAGE_BYTES	BE_U64_C(0x39000)
#define ALL_ONES		(~BE_U64_C(0))

static be_u8 synthetic[SYNTH_IMAGE_BYTES];
static be_u8 *staged;
static be_u64 staged_bytes;
static struct be_b6_gstage_map window;

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

static struct be_b6_payload_layout synthetic_layout(void)
{
	return (struct be_b6_payload_layout) {
		.staging_hpa = L_HPA,
		.kernel_offset = BE_U64_C(0x35000),
		.kernel_bytes = SYNTH_KERNEL_BYTES,
		.kernel_image_size = SYNTH_IMAGE_SIZE,
		.dtb_offset = SYNTH_DTB_OFFSET,
		.dtb_bytes = BE_U64_C(0x1000),
		.image_bytes = SYNTH_IMAGE_BYTES,
	};
}

/* A well-formed kernel header and FDT header in the synthetic image. */
static void synthetic_headers(void)
{
	be_u8 *kernel = synthetic + 0x35000U;
	be_u8 *dtb = synthetic + SYNTH_DTB_OFFSET;

	memset(synthetic, 0, sizeof(synthetic));
	put_le(kernel, 0x0000a0d1U, 4U);
	put_le(kernel + 8U, 0x200000U, 8U);
	put_le(kernel + 16U, SYNTH_IMAGE_SIZE, 8U);
	put_le(kernel + 32U, 2U, 4U);
	memcpy(kernel + 48U, "RISCV\0\0\0", 8U);
	memcpy(kernel + 56U, "RSC\x05", 4U);
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

static enum be_b6_payload_error check(const struct be_b6_payload_layout *layout,
				      const struct be_b6_gstage_map *map,
				      const be_u8 *image)
{
	struct be_b6_payload_plan plan;
	enum be_b6_payload_error error = be_b6_payload_check(layout, map,
							     image, &plan);

	/* A refusal leaves an empty plan. */
	if (error != BE_B6_PAYLOAD_OK)
		CHECK(plan.kernel_source == 0U && plan.kernel_target == 0U &&
		      plan.dtb_target == 0U && plan.image_size == 0U &&
		      plan.kernel_gpa == 0U && plan.dtb_gpa == 0U);
	return error;
}

static void build_window(void)
{
	static be_u8 pool[BE_B6_GSTAGE_POOL_BYTES];
	struct be_b6_gstage_desc desc = { BE_B6_GUEST_GPA, BE_B6_GUEST_HPA,
					  BE_B6_GUEST_BYTES, BE_B6_POOL_HPA };

	CHECK(be_b6_gstage_build(&desc, pool, sizeof(pool)) ==
	      BE_B6_GSTAGE_OK);
	CHECK(be_b6_gstage_walk(&desc, pool, sizeof(pool), &window) ==
	      BE_B6_GSTAGE_OK);
}

static void test_constants(void)
{
	SCENARIO();
	CHECK(BE_B6_STAGING_HPA == L_HPA);
	CHECK(BE_B6_BOOT_KERNEL_OFFSET == 0x35000U);
	CHECK(BE_B6_KERNEL_FILE_MAX == 4U * MIB);
	CHECK(BE_B6_KERNEL_IMAGE_SIZE_MAX == 8U * MIB);
	CHECK(BE_B6_BOOT_IMAGE_MAX == 4U * MIB);
	CHECK(BE_B6_DTB_BYTES == 0x1000U);
	CHECK(BE_B6_KERNEL_GPA == BE_U64_C(0x80200000));
	CHECK(BE_B6_DTB_GPA == BE_U64_C(0x83e00000));
	CHECK(sizeof(struct be_b6_payload_layout) == 7U * sizeof(be_u64));
	CHECK(sizeof(struct be_b6_payload_plan) == 9U * sizeof(be_u64));
	/* The generated layout holds the rules the monitor checks again. */
	CHECK(BE_B6_PAYLOAD_KERNEL_BYTES >= 64U &&
	      BE_B6_PAYLOAD_KERNEL_BYTES <= BE_B6_KERNEL_FILE_MAX);
	CHECK(BE_B6_PAYLOAD_KERNEL_IMAGE_SIZE >= BE_B6_PAYLOAD_KERNEL_BYTES &&
	      BE_B6_PAYLOAD_KERNEL_IMAGE_SIZE <= BE_B6_KERNEL_IMAGE_SIZE_MAX);
	CHECK(BE_B6_PAYLOAD_DTB_OFFSET ==
	      ((0x35000U + BE_B6_PAYLOAD_KERNEL_BYTES + 0xfffU) & ~0xfffUL));
	CHECK(BE_B6_PAYLOAD_IMAGE_BYTES == BE_B6_PAYLOAD_DTB_OFFSET + 0x1000U);
	CHECK(BE_B6_PAYLOAD_IMAGE_BYTES <= BE_B6_BOOT_IMAGE_MAX);
}

static void test_good(void)
{
	struct be_b6_payload_layout layout = synthetic_layout();
	struct be_b6_payload_plan plan;

	SCENARIO();
	synthetic_headers();
	CHECK(be_b6_payload_check(&layout, &window, synthetic, &plan) ==
	      BE_B6_PAYLOAD_OK);
	CHECK(plan.kernel_source == L_HPA + 0x35000U);
	CHECK(plan.kernel_target == BE_U64_C(0x110200000));
	CHECK(plan.kernel_gpa == BE_B6_KERNEL_GPA);
	CHECK(plan.kernel_bytes == SYNTH_KERNEL_BYTES);
	CHECK(plan.image_size == SYNTH_IMAGE_SIZE);
	CHECK(plan.dtb_source == L_HPA + SYNTH_DTB_OFFSET);
	CHECK(plan.dtb_target == BE_U64_C(0x113e00000));
	CHECK(plan.dtb_gpa == BE_B6_DTB_GPA);
	CHECK(plan.dtb_bytes == 0x1000U);
	/* Null arguments. */
	CHECK(be_b6_payload_check(&layout, &window, synthetic,
				  (struct be_b6_payload_plan *)0) ==
	      BE_B6_PAYLOAD_NULL);
	CHECK(check((const struct be_b6_payload_layout *)0, &window,
		    synthetic) == BE_B6_PAYLOAD_NULL);
	CHECK(check(&layout, (const struct be_b6_gstage_map *)0, synthetic) ==
	      BE_B6_PAYLOAD_NULL);
	CHECK(check(&layout, &window, (const be_u8 *)0) == BE_B6_PAYLOAD_NULL);
}

static void test_layout(void)
{
	static const struct {
		unsigned int field;
		be_u64 value;
	} cases[] = {
		{ 0U, L_HPA + 0x800U },
		{ 1U, 0x34000U }, { 1U, 0x36000U }, { 1U, 0U },
		{ 2U, 0U }, { 2U, 63U }, { 2U, SYNTH_KERNEL_BYTES + 0x1000U },
		{ 2U, 4U * MIB + 1U }, { 2U, ALL_ONES },
		{ 3U, SYNTH_KERNEL_BYTES - 1U }, { 3U, 8U * MIB + 1U },
		{ 3U, ALL_ONES },
		{ 4U, SYNTH_DTB_OFFSET - 0x1000U },
		{ 4U, SYNTH_DTB_OFFSET + 0x1000U },
		{ 4U, SYNTH_DTB_OFFSET + 8U }, { 4U, 0x35000U + 0x2345U },
		{ 5U, 0U }, { 5U, 0x800U }, { 5U, 0x2000U },
		{ 6U, SYNTH_IMAGE_BYTES - 0x1000U },
		{ 6U, SYNTH_IMAGE_BYTES + 0x1000U }, { 6U, 0U },
	};
	struct be_b6_payload_layout layout;
	be_u64 *fields = (be_u64 *)(void *)&layout;
	be_size index;

	SCENARIO();
	synthetic_headers();
	for (index = 0U; index < BE_ARRAY_SIZE(cases); ++index) {
		layout = synthetic_layout();
		fields[cases[index].field] = cases[index].value;
		CHECK(check(&layout, &window, synthetic) ==
		      BE_B6_PAYLOAD_LAYOUT);
	}
	/* The largest kernel file the 4 MiB boot image admits; the header's
	 * image_size then differs, which stops the check before the DTB. */
	layout = synthetic_layout();
	layout.kernel_bytes = 4U * MIB - 0x36000U;
	layout.kernel_image_size = layout.kernel_bytes;
	layout.dtb_offset = 4U * MIB - 0x1000U;
	layout.image_bytes = 4U * MIB;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_SIZE);
	layout.kernel_bytes += 1U;
	layout.kernel_image_size += 1U;
	layout.dtb_offset += 0x1000U;
	layout.image_bytes += 0x1000U;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_LAYOUT);
	/* image_size up to 8 MiB is admitted. */
	layout = synthetic_layout();
	layout.kernel_image_size = 8U * MIB;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_SIZE);
	/* The staged image must not wrap. */
	layout = synthetic_layout();
	layout.staging_hpa = ALL_ONES - 0xfffU;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_LAYOUT);
	layout.staging_hpa = (ALL_ONES - SYNTH_IMAGE_BYTES + 1U) & ~0xfffUL;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_LAYOUT);
	layout.staging_hpa = (ALL_ONES - SYNTH_IMAGE_BYTES) & ~0xfffUL;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_OK);
}

static void test_window(void)
{
	struct be_b6_payload_layout layout = synthetic_layout();
	struct be_b6_gstage_map small = window;
	struct be_b6_payload_plan plan;

	SCENARIO();
	synthetic_headers();
	/* An 8 MiB window: the kernel span may reach the DTB slot, no more. */
	small.size = 8U * MIB;
	small.leaves = 4U;
	layout.kernel_image_size = 4U * MIB;
	put_le(synthetic + 0x35000U + 16U, 4U * MIB, 8U);
	CHECK(be_b6_payload_check(&layout, &small, synthetic, &plan) ==
	      BE_B6_PAYLOAD_OK);
	CHECK(plan.dtb_gpa == BE_U64_C(0x80600000) &&
	      plan.dtb_target == BE_U64_C(0x110600000));
	layout.kernel_image_size = 4U * MIB + 1U;
	put_le(synthetic + 0x35000U + 16U, 4U * MIB + 1U, 8U);
	CHECK(check(&layout, &small, synthetic) == BE_B6_PAYLOAD_WINDOW);
	/* Too small for a kernel slot and a DTB slot. */
	layout = synthetic_layout();
	synthetic_headers();
	small.size = 4U * MIB;
	CHECK(check(&layout, &small, synthetic) == BE_B6_PAYLOAD_WINDOW);
	small.size = 2U * MIB;
	CHECK(check(&layout, &small, synthetic) == BE_B6_PAYLOAD_WINDOW);
	small.size = 0U;
	CHECK(check(&layout, &small, synthetic) == BE_B6_PAYLOAD_WINDOW);
	small = window;
	small.gpa_base = ALL_ONES - 32U * MIB;
	CHECK(check(&layout, &small, synthetic) == BE_B6_PAYLOAD_WINDOW);
	/* The staged image inside or touching the window, monitor, or pool. */
	layout.staging_hpa = BE_B6_GUEST_HPA;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_B6_GUEST_HPA + 64U * MIB - 0x1000U;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_B6_GUEST_HPA - SYNTH_IMAGE_BYTES + 0x1000U;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_B6_GUEST_HPA - SYNTH_IMAGE_BYTES;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_OK);
	layout.staging_hpa = BE_B6_GUEST_HPA + 64U * MIB;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_OK);
	layout.staging_hpa = BE_B6_MONITOR_HPA;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_B6_MONITOR_HPA - SYNTH_IMAGE_BYTES + 0x1000U;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_B6_POOL_HPA + 0x7000U;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_WINDOW);
	layout.staging_hpa = BE_B6_POOL_HPA + 0x8000U;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_OK);
	layout.staging_hpa = BE_B6_MONITOR_HPA - SYNTH_IMAGE_BYTES;
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_OK);
}

static void test_kernel(void)
{
	struct be_b6_payload_layout layout = synthetic_layout();
	be_u8 *kernel = synthetic + 0x35000U;
	unsigned int index;
	unsigned int bit;

	SCENARIO();
	/* Every bit of both magics. */
	for (index = 0U; index < 12U; ++index) {
		for (bit = 0U; bit < 8U; ++bit) {
			synthetic_headers();
			kernel[48U + index] ^= (be_u8)(1U << bit);
			CHECK(check(&layout, &window, synthetic) ==
			      (index < 8U ? BE_B6_PAYLOAD_KERNEL_MAGIC :
					    BE_B6_PAYLOAD_KERNEL_MAGIC2));
		}
	}
	/* text_offset: only 0x200000. */
	synthetic_headers();
	put_le(kernel + 8U, 0U, 8U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_OFFSET);
	put_le(kernel + 8U, 0x400000U, 8U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_OFFSET);
	put_le(kernel + 8U, 0x200000U | (BE_U64_C(1) << 63), 8U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_OFFSET);
	/* flags bit 0 is big-endian; the other bits are not checked. */
	synthetic_headers();
	put_le(kernel + 24U, 1U, 8U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_ENDIAN);
	put_le(kernel + 24U, ALL_ONES, 8U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_ENDIAN);
	put_le(kernel + 24U, 2U, 8U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_OK);
	/* image_size: at least the file and exactly the layout's. */
	synthetic_headers();
	put_le(kernel + 16U, SYNTH_KERNEL_BYTES - 1U, 8U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_SIZE);
	put_le(kernel + 16U, SYNTH_IMAGE_SIZE + 1U, 8U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_SIZE);
	put_le(kernel + 16U, 0U, 8U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_SIZE);
	put_le(kernel + 16U, ALL_ONES, 8U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_KERNEL_SIZE);
	/* The code words, version, and reserved words are content, not shape. */
	synthetic_headers();
	memset(kernel, 0xff, 8U);
	memset(kernel + 32U, 0xff, 16U);
	memset(kernel + 60U, 0xff, 4U);
	CHECK(check(&layout, &window, synthetic) == BE_B6_PAYLOAD_OK);
}

static void test_dtb(void)
{
	static const struct {
		unsigned int offset;
		be_u64 value;
		enum be_b6_payload_error error;
	} cases[] = {
		{ 0U, 0xedfe0dd0U, BE_B6_PAYLOAD_DTB_MAGIC },
		{ 0U, 0U, BE_B6_PAYLOAD_DTB_MAGIC },
		{ 4U, 0xfffU, BE_B6_PAYLOAD_DTB_SIZE },
		{ 4U, 0x1001U, BE_B6_PAYLOAD_DTB_SIZE },
		{ 4U, 0x10000U, BE_B6_PAYLOAD_DTB_SIZE },
		{ 20U, 16U, BE_B6_PAYLOAD_DTB_VERSION },
		{ 20U, 18U, BE_B6_PAYLOAD_DTB_VERSION },
		{ 20U, 0U, BE_B6_PAYLOAD_DTB_VERSION },
		/* Reserve map: after the header, 8-byte aligned, inside. */
		{ 16U, 0x20U, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 16U, 0x2cU, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 16U, 0xff8U, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 16U, 0x1000U, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 16U, 0xffffffffU, BE_B6_PAYLOAD_DTB_BLOCKS },
		/* Structure block: after the header, 4-byte aligned, inside. */
		{ 8U, 0x24U, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 8U, 0x3aU, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 8U, 0xd4cU, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 8U, 0xffffffffU, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 36U, 0xfc9U, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 36U, 0xffffffffU, BE_B6_PAYLOAD_DTB_BLOCKS },
		/* Strings block: after the header, inside. */
		{ 12U, 0x27U, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 12U, 0xf81U, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 32U, 0xd11U, BE_B6_PAYLOAD_DTB_BLOCKS },
		{ 32U, 0xffffffffU, BE_B6_PAYLOAD_DTB_BLOCKS },
		/* Exact fits pass. */
		{ 16U, 0xff0U, BE_B6_PAYLOAD_OK },
		{ 8U, 0xd48U, BE_B6_PAYLOAD_OK },
		{ 36U, 0xfc8U, BE_B6_PAYLOAD_OK },
		{ 12U, 0xf80U, BE_B6_PAYLOAD_OK },
		{ 32U, 0xd10U, BE_B6_PAYLOAD_OK },
		{ 24U, 17U, BE_B6_PAYLOAD_OK },
		{ 28U, 0xffffffffU, BE_B6_PAYLOAD_OK },
	};
	struct be_b6_payload_layout layout = synthetic_layout();
	be_size index;

	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(cases); ++index) {
		synthetic_headers();
		put_be32(synthetic + SYNTH_DTB_OFFSET + cases[index].offset,
			 cases[index].value);
		CHECK(check(&layout, &window, synthetic) == cases[index].error);
	}
	/* The kernel is checked first: a bad kernel hides a bad DTB. */
	synthetic_headers();
	synthetic[0x35000U + 56U] = 0U;
	synthetic[SYNTH_DTB_OFFSET] = 0U;
	CHECK(check(&layout, &window, synthetic) ==
	      BE_B6_PAYLOAD_KERNEL_MAGIC2);
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

static const struct be_b6_payload_layout generated = {
	.staging_hpa = BE_B6_STAGING_HPA,
	.kernel_offset = BE_B6_BOOT_KERNEL_OFFSET,
	.kernel_bytes = BE_B6_PAYLOAD_KERNEL_BYTES,
	.kernel_image_size = BE_B6_PAYLOAD_KERNEL_IMAGE_SIZE,
	.dtb_offset = BE_B6_PAYLOAD_DTB_OFFSET,
	.dtb_bytes = BE_B6_DTB_BYTES,
	.image_bytes = BE_B6_PAYLOAD_IMAGE_BYTES,
};

/* The staged payload the monitor is built for, as the loaders place it. */
static void test_staged(const char *kernel_path, const char *dtb_path)
{
	struct be_b6_payload_plan plan;
	be_u64 kernel_bytes;
	be_u64 dtb_bytes;
	be_u8 *kernel = read_file(kernel_path, &kernel_bytes);
	be_u8 *dtb = read_file(dtb_path, &dtb_bytes);

	SCENARIO();
	CHECK(kernel_bytes == BE_B6_PAYLOAD_KERNEL_BYTES);
	CHECK(dtb_bytes == BE_B6_DTB_BYTES);
	staged_bytes = BE_B6_PAYLOAD_IMAGE_BYTES;
	staged = calloc(1U, (size_t)staged_bytes);
	CHECK(staged != (be_u8 *)0);
	memcpy(staged + BE_B6_BOOT_KERNEL_OFFSET, kernel, (size_t)kernel_bytes);
	memcpy(staged + BE_B6_PAYLOAD_DTB_OFFSET, dtb, (size_t)dtb_bytes);
	CHECK(be_b6_payload_check(&generated, &window, staged, &plan) ==
	      BE_B6_PAYLOAD_OK);
	CHECK(plan.kernel_source == BE_U64_C(0x108035000));
	CHECK(plan.kernel_target == BE_U64_C(0x110200000));
	CHECK(plan.kernel_gpa == BE_U64_C(0x80200000));
	CHECK(plan.kernel_bytes == kernel_bytes);
	CHECK(plan.image_size == BE_B6_PAYLOAD_KERNEL_IMAGE_SIZE);
	CHECK(plan.dtb_source == BE_U64_C(0x108000000) +
				BE_B6_PAYLOAD_DTB_OFFSET);
	CHECK(plan.dtb_target == BE_U64_C(0x113e00000));
	CHECK(plan.dtb_gpa == BE_U64_C(0x83e00000));
	CHECK(plan.dtb_bytes == 0x1000U);
	/* The span ends below the DTB slot, inside the window. */
	CHECK(plan.kernel_gpa + plan.image_size <= plan.dtb_gpa);
	/* The plan's payload variant: magic2 "RSC\0". */
	staged[BE_B6_BOOT_KERNEL_OFFSET + 0x3bU] = 0U;
	CHECK(check(&generated, &window, staged) ==
	      BE_B6_PAYLOAD_KERNEL_MAGIC2);
	staged[BE_B6_BOOT_KERNEL_OFFSET + 0x3bU] = 0x05U;
	CHECK(check(&generated, &window, staged) == BE_B6_PAYLOAD_OK);
	free(kernel);
	free(dtb);
}

/* Each DTB variant has the same shape; the guest tells them apart. */
static void test_dtb_variants(int count, char **paths)
{
	int index;

	SCENARIO();
	for (index = 0; index < count; ++index) {
		be_u64 bytes;
		be_u8 *dtb = read_file(paths[index], &bytes);

		CHECK(bytes == BE_B6_DTB_BYTES);
		memcpy(staged + BE_B6_PAYLOAD_DTB_OFFSET, dtb, (size_t)bytes);
		CHECK(check(&generated, &window, staged) == BE_B6_PAYLOAD_OK);
		free(dtb);
	}
	free(staged);
}

int main(int argc, char **argv)
{
	if (argc < 3) {
		printf("usage: %s KERNEL DTB [VARIANT_DTB ...]\n", argv[0]);
		return 2;
	}
	build_window();
	test_constants();
	test_good();
	test_layout();
	test_window();
	test_kernel();
	test_dtb();
	test_staged(argv[1], argv[2]);
	test_dtb_variants(argc - 3, argv + 3);
	printf("BE_B6_PAYLOAD_CHECK: PASS\n");
	printf("BE_B6_PAYLOAD_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_B6_PAYLOAD_CHECK: assertions=%lu\n", assertions);
	return 0;
}
