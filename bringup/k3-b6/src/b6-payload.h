/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: K3 B6 payload contract: the staged boot image's link-time layout
 *          (the monitor image, then the kernel Image, then the DTB), the
 *          shape checks on the kernel's RISC-V Image header and the DTB's
 *          FDT header, and the placement plan the runtime copies by.
 * Trust:   restricted C. No CSR, SBI call, or I/O. It reads only the two
 *          headers inside the staged bytes it is given and returns host-
 *          physical addresses; the runtime performs the zero and copy. It
 *          checks shape, not content: the pins, the loaders' file checks,
 *          and the pinned banner bind the content.
 * Scope:   B6 only (planning/k3-b6-plan.md, "Guest-physical layout and
 *          payload checks"; Documentation/arch/riscv/boot-image-header.rst
 *          and the devicetree specification's FDT header at Linux v7.2).
 */

#ifndef BE_B6_PAYLOAD_H
#define BE_B6_PAYLOAD_H

#include <be/types.h>

#include "b6-gstage.h"
#include "b6-layout.h"

/* RISC-V Image header (64 bytes, little endian) field offsets. */
#define BE_B6_KERNEL_HEADER_BYTES	64U
#define BE_B6_KERNEL_TEXT_OFFSET_AT	8U
#define BE_B6_KERNEL_IMAGE_SIZE_AT	16U
#define BE_B6_KERNEL_FLAGS_AT		24U
#define BE_B6_KERNEL_MAGIC_AT		48U
#define BE_B6_KERNEL_MAGIC2_AT		56U
#define BE_B6_KERNEL_MAGIC2		0x05435352U
#define BE_B6_KERNEL_FLAG_BIG_ENDIAN	BE_U64_C(1)

/* FDT header (40 bytes, big endian) field offsets. */
#define BE_B6_FDT_HEADER_BYTES		40U
#define BE_B6_FDT_MAGIC			0xd00dfeedU
#define BE_B6_FDT_VERSION		17U
#define BE_B6_FDT_TOTALSIZE_AT		4U
#define BE_B6_FDT_OFF_STRUCT_AT		8U
#define BE_B6_FDT_OFF_STRINGS_AT	12U
#define BE_B6_FDT_OFF_RSVMAP_AT		16U
#define BE_B6_FDT_VERSION_AT		20U
#define BE_B6_FDT_SIZE_STRINGS_AT	32U
#define BE_B6_FDT_SIZE_STRUCT_AT	36U

/**
 * struct be_b6_payload_layout - the staged boot image, as linked
 * @staging_hpa: L, where every loader places the boot image
 * @kernel_offset: kernel Image offset in the boot image (0x35000)
 * @kernel_bytes: kernel Image file size
 * @kernel_image_size: the kernel header's image_size
 * @dtb_offset: DTB offset: the kernel's end rounded up to 4 KiB
 * @dtb_bytes: DTB size, exactly 4 KiB
 * @image_bytes: the whole boot image, which the DTB ends
 *
 * The monitor holds one instance, generated from the pinned payload files;
 * the image checker compares it with the boot image it is linked into.
 */
struct be_b6_payload_layout {
	be_u64 staging_hpa;
	be_u64 kernel_offset;
	be_u64 kernel_bytes;
	be_u64 kernel_image_size;
	be_u64 dtb_offset;
	be_u64 dtb_bytes;
	be_u64 image_bytes;
};

/**
 * struct be_b6_payload_plan - the checked placement
 * @kernel_source: HPA of the staged kernel
 * @kernel_target: HPA of the kernel GPA (window base + text_offset)
 * @kernel_gpa: the kernel GPA, the first guest PC
 * @kernel_bytes: kernel bytes to copy
 * @image_size: the kernel's checked image_size, its span from @kernel_gpa
 * @dtb_source: HPA of the staged DTB
 * @dtb_target: HPA of the DTB GPA (the start of the window's last 2 MiB)
 * @dtb_gpa: the DTB GPA, the guest's a1
 * @dtb_bytes: DTB bytes to copy
 *
 * All zero unless the check succeeded.
 */
struct be_b6_payload_plan {
	be_u64 kernel_source;
	be_u64 kernel_target;
	be_u64 kernel_gpa;
	be_u64 kernel_bytes;
	be_u64 image_size;
	be_u64 dtb_source;
	be_u64 dtb_target;
	be_u64 dtb_gpa;
	be_u64 dtb_bytes;
};

/**
 * enum be_b6_payload_error - stable payload results
 * @BE_B6_PAYLOAD_OK: success
 * @BE_B6_PAYLOAD_NULL: a required pointer is absent
 * @BE_B6_PAYLOAD_LAYOUT: the link-time layout breaks a size or offset rule
 * @BE_B6_PAYLOAD_WINDOW: the window cannot hold the kernel span and DTB, or
 *                        the staged image overlaps the window or monitor
 * @BE_B6_PAYLOAD_KERNEL_MAGIC: magic is not "RISCV\0\0\0"
 * @BE_B6_PAYLOAD_KERNEL_MAGIC2: magic2 is not "RSC\x05"
 * @BE_B6_PAYLOAD_KERNEL_OFFSET: text_offset is not 0x200000
 * @BE_B6_PAYLOAD_KERNEL_ENDIAN: flags marks a big-endian kernel
 * @BE_B6_PAYLOAD_KERNEL_SIZE: image_size is below the file size, differs
 *                             from the layout, exceeds its budget, or ends
 *                             at or above the DTB slot
 * @BE_B6_PAYLOAD_DTB_MAGIC: the FDT magic is wrong
 * @BE_B6_PAYLOAD_DTB_SIZE: totalsize is not the layout's DTB size
 * @BE_B6_PAYLOAD_DTB_VERSION: version is not 17
 * @BE_B6_PAYLOAD_DTB_BLOCKS: a block offset or size leaves the DTB
 */
enum be_b6_payload_error {
	BE_B6_PAYLOAD_OK = 0,
	BE_B6_PAYLOAD_NULL,
	BE_B6_PAYLOAD_LAYOUT,
	BE_B6_PAYLOAD_WINDOW,
	BE_B6_PAYLOAD_KERNEL_MAGIC,
	BE_B6_PAYLOAD_KERNEL_MAGIC2,
	BE_B6_PAYLOAD_KERNEL_OFFSET,
	BE_B6_PAYLOAD_KERNEL_ENDIAN,
	BE_B6_PAYLOAD_KERNEL_SIZE,
	BE_B6_PAYLOAD_DTB_MAGIC,
	BE_B6_PAYLOAD_DTB_SIZE,
	BE_B6_PAYLOAD_DTB_VERSION,
	BE_B6_PAYLOAD_DTB_BLOCKS,
};

/**
 * be_b6_payload_check - check the layout and both headers, then plan
 * @layout: the link-time layout
 * @map: the walked G-stage window
 * @staged: the staged boot image's bytes as HS reads them, at
 *          @layout->staging_hpa in the monitor; only the kernel's 64-byte
 *          and the DTB's 40-byte headers are read
 * @plan: zeroed first; filled only on success
 *
 * The layout must place the kernel at 0x35000, hold 64 bytes to 4 MiB of
 * kernel, put the 4 KiB DTB at the next 4 KiB boundary, and end the image
 * there, at most 4 MiB in all, outside the window and the monitor. The
 * kernel must carry both magics, text_offset 0x200000, little endian, and
 * the layout's image_size, at least its file size and at most 8 MiB, ending
 * below the DTB slot. The DTB must carry its magic, the layout's totalsize,
 * version 17, and blocks inside it.
 *
 * Return: %BE_B6_PAYLOAD_OK or the first error found.
 */
enum be_b6_payload_error
be_b6_payload_check(const struct be_b6_payload_layout *layout,
		    const struct be_b6_gstage_map *map, const be_u8 *staged,
		    struct be_b6_payload_plan *plan);

#endif
