// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B7 payload checks: the staged boot image's link-time layout,
 *          the kernel's RISC-V Image header, each DTB's FDT header, and the
 *          placement plan inside each walked guest window.
 * Trust:   restricted C with fixed-size header reads. No CSR, SBI call, or
 *          I/O; the runtime zeroes and copies by the returned plans.
 * Scope:   B7 only (planning/k3-b7-plan.md); see b7-payload.h.
 */
#include "b7-payload.h"

#define PAGE_MASK		BE_U64_C(0xfff)

_Static_assert(BE_B7_KERNEL_HEADER_BYTES == 64U,
	       "the RISC-V Image header is 64 bytes");
_Static_assert(BE_B7_KERNEL_MAGIC2_AT + 4U <= BE_B7_KERNEL_HEADER_BYTES,
	       "magic2 lies inside the header");
_Static_assert(BE_B7_FDT_SIZE_STRUCT_AT + 4U == BE_B7_FDT_HEADER_BYTES,
	       "the FDT header ends with size_dt_struct");
_Static_assert(BE_B7_KERNEL_GPA == BE_B7_GUEST_GPA + BE_B7_KERNEL_TEXT_OFFSET,
	       "the kernel GPA is the window base plus text_offset");

static be_u64 load_le(const be_u8 *source, unsigned int bytes)
{
	be_u64 value = 0U;
	unsigned int byte;

	for (byte = 0U; byte < bytes; ++byte)
		value |= (be_u64)source[byte] << (8U * byte);
	return value;
}

static be_u64 load_be32(const be_u8 *source)
{
	return (be_u64)source[0] << 24 | (be_u64)source[1] << 16 |
	       (be_u64)source[2] << 8 | (be_u64)source[3];
}

static int overlaps(be_u64 first, be_u64 first_size, be_u64 second,
		    be_u64 second_size)
{
	return first < second + second_size && second < first + first_size;
}

/* The link-time layout: offsets, sizes, and budgets. */
static int layout_valid(const struct be_b7_payload_layout *layout)
{
	be_u64 kernel_end;

	if (layout->kernel_offset != BE_B7_BOOT_KERNEL_OFFSET ||
	    layout->kernel_bytes < BE_B7_KERNEL_HEADER_BYTES ||
	    layout->kernel_bytes > BE_B7_KERNEL_FILE_MAX ||
	    layout->kernel_image_size < layout->kernel_bytes ||
	    layout->kernel_image_size > BE_B7_KERNEL_IMAGE_SIZE_MAX ||
	    layout->dtb_bytes != BE_B7_DTB_BYTES ||
	    (layout->staging_hpa & PAGE_MASK) != 0U)
		return 0;
	kernel_end = layout->kernel_offset + layout->kernel_bytes;
	return layout->dtb_offset[0] == ((kernel_end + PAGE_MASK) & ~PAGE_MASK) &&
	       layout->dtb_offset[1] ==
		       layout->dtb_offset[0] + layout->dtb_bytes &&
	       layout->image_bytes == layout->dtb_offset[1] + layout->dtb_bytes &&
	       layout->image_bytes <= BE_B7_BOOT_IMAGE_MAX &&
	       layout->staging_hpa <= ~layout->image_bytes;
}

/*
 * The window holds the kernel span from text_offset and the DTB in its last
 * 2 MiB, and the staged image lies outside the window, the monitor image,
 * and the window's G-stage pool.
 */
static int window_valid(const struct be_b7_payload_layout *layout,
			const struct be_b7_gstage_map *map,
			struct be_b7_payload_plan *plan)
{
	be_u64 kernel_gpa;
	be_u64 dtb_gpa;

	if (map->size < 2U * BE_B7_GSTAGE_LEAF_BYTES ||
	    map->gpa_base > ~map->size ||
	    overlaps(layout->staging_hpa, layout->image_bytes, map->hpa_base,
		     map->size) ||
	    overlaps(layout->staging_hpa, layout->image_bytes,
		     BE_B7_MONITOR_HPA, BE_B7_MONITOR_BYTES) ||
	    overlaps(layout->staging_hpa, layout->image_bytes, map->pool_pa,
		     BE_B7_GSTAGE_POOL_BYTES))
		return 0;
	kernel_gpa = map->gpa_base + BE_B7_KERNEL_TEXT_OFFSET;
	dtb_gpa = map->gpa_base + map->size - BE_B7_GSTAGE_LEAF_BYTES;
	if (layout->kernel_image_size > dtb_gpa - kernel_gpa ||
	    !be_b7_gstage_translate(map, kernel_gpa, layout->kernel_image_size,
				    &plan->kernel_target) ||
	    !be_b7_gstage_translate(map, dtb_gpa, layout->dtb_bytes,
				    &plan->dtb_target))
		return 0;
	plan->kernel_gpa = kernel_gpa;
	plan->dtb_gpa = dtb_gpa;
	return 1;
}

/* Documentation/arch/riscv/boot-image-header.rst (Linux v7.2). */
static enum be_b7_payload_error
kernel_check(const struct be_b7_payload_layout *layout, const be_u8 *header)
{
	static const be_u8 magic[8] = { 'R', 'I', 'S', 'C', 'V', 0, 0, 0 };
	be_u64 image_size = load_le(header + BE_B7_KERNEL_IMAGE_SIZE_AT, 8U);
	unsigned int index;

	for (index = 0U; index < sizeof(magic); ++index)
		if (header[BE_B7_KERNEL_MAGIC_AT + index] != magic[index])
			return BE_B7_PAYLOAD_KERNEL_MAGIC;
	if (load_le(header + BE_B7_KERNEL_MAGIC2_AT, 4U) != BE_B7_KERNEL_MAGIC2)
		return BE_B7_PAYLOAD_KERNEL_MAGIC2;
	if (load_le(header + BE_B7_KERNEL_TEXT_OFFSET_AT, 8U) !=
	    BE_B7_KERNEL_TEXT_OFFSET)
		return BE_B7_PAYLOAD_KERNEL_OFFSET;
	if ((load_le(header + BE_B7_KERNEL_FLAGS_AT, 8U) &
	     BE_B7_KERNEL_FLAG_BIG_ENDIAN) != 0U)
		return BE_B7_PAYLOAD_KERNEL_ENDIAN;
	if (image_size < layout->kernel_bytes ||
	    image_size != layout->kernel_image_size)
		return BE_B7_PAYLOAD_KERNEL_SIZE;
	return BE_B7_PAYLOAD_OK;
}

/* A block [offset, offset + size) inside the DTB and after its header. */
static int block_valid(be_u64 offset, be_u64 size, be_u64 total,
		       be_u64 alignment)
{
	return offset >= BE_B7_FDT_HEADER_BYTES && offset <= total &&
	       size <= total - offset && (offset & (alignment - 1U)) == 0U;
}

/* The FDT header, as libfdt's fdt_check_header() reads it. */
static enum be_b7_payload_error
dtb_check(const struct be_b7_payload_layout *layout, const be_u8 *header)
{
	be_u64 total = load_be32(header + BE_B7_FDT_TOTALSIZE_AT);

	if (load_be32(header) != BE_B7_FDT_MAGIC)
		return BE_B7_PAYLOAD_DTB_MAGIC;
	if (total != layout->dtb_bytes)
		return BE_B7_PAYLOAD_DTB_SIZE;
	if (load_be32(header + BE_B7_FDT_VERSION_AT) != BE_B7_FDT_VERSION)
		return BE_B7_PAYLOAD_DTB_VERSION;
	if (!block_valid(load_be32(header + BE_B7_FDT_OFF_RSVMAP_AT), 16U,
			 total, 8U) ||
	    !block_valid(load_be32(header + BE_B7_FDT_OFF_STRUCT_AT),
			 load_be32(header + BE_B7_FDT_SIZE_STRUCT_AT), total,
			 4U) ||
	    !block_valid(load_be32(header + BE_B7_FDT_OFF_STRINGS_AT),
			 load_be32(header + BE_B7_FDT_SIZE_STRINGS_AT), total,
			 1U))
		return BE_B7_PAYLOAD_DTB_BLOCKS;
	return BE_B7_PAYLOAD_OK;
}

enum be_b7_payload_error
be_b7_payload_check(const struct be_b7_payload_layout *layout,
		    const struct be_b7_gstage_map *maps, const be_u8 *staged,
		    struct be_b7_payload_plan *plans)
{
	struct be_b7_payload_plan candidate[BE_B7_GUESTS] = { { 0 }, { 0 } };
	enum be_b7_payload_error error;
	be_u64 guest;

	if (plans == (struct be_b7_payload_plan *)0)
		return BE_B7_PAYLOAD_NULL;
	for (guest = 0U; guest < BE_B7_GUESTS; ++guest)
		plans[guest] = candidate[guest];
	if (layout == (const struct be_b7_payload_layout *)0 ||
	    maps == (const struct be_b7_gstage_map *)0 ||
	    staged == (const be_u8 *)0)
		return BE_B7_PAYLOAD_NULL;
	if (!layout_valid(layout))
		return BE_B7_PAYLOAD_LAYOUT;
	if (overlaps(maps[0].hpa_base, maps[0].size, maps[1].hpa_base,
		     maps[1].size))
		return BE_B7_PAYLOAD_WINDOW;
	for (guest = 0U; guest < BE_B7_GUESTS; ++guest)
		if (!window_valid(layout, &maps[guest], &candidate[guest]))
			return BE_B7_PAYLOAD_WINDOW;
	error = kernel_check(layout, staged + layout->kernel_offset);
	for (guest = 0U; guest < BE_B7_GUESTS && error == BE_B7_PAYLOAD_OK;
	     ++guest)
		error = dtb_check(layout, staged + layout->dtb_offset[guest]);
	if (error != BE_B7_PAYLOAD_OK)
		return error;
	for (guest = 0U; guest < BE_B7_GUESTS; ++guest) {
		candidate[guest].kernel_source =
			layout->staging_hpa + layout->kernel_offset;
		candidate[guest].kernel_bytes = layout->kernel_bytes;
		candidate[guest].image_size = layout->kernel_image_size;
		candidate[guest].dtb_source =
			layout->staging_hpa + layout->dtb_offset[guest];
		candidate[guest].dtb_bytes = layout->dtb_bytes;
	}
	for (guest = 0U; guest < BE_B7_GUESTS; ++guest)
		plans[guest] = candidate[guest];
	return BE_B7_PAYLOAD_OK;
}
