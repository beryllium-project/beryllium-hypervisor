/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: MVP payload contract: the staged boot image's link-time layout
 *          (the monitor image, then the kernel Image, then G0's DTB and
 *          G1's DTB), the shape checks on the kernel's RISC-V Image header
 *          and each DTB's FDT header, and the placement plan per domain
 *          window the runtime copies by.
 * Trust:   restricted C. No CSR, SBI call, or I/O. It reads only the
 *          headers inside the staged bytes it is given and returns host-
 *          physical addresses; the runtime performs the zero and copy. It
 *          checks shape, not content: the pins, the loaders' file checks,
 *          and the pinned banner bind the content.
 * Scope:   the MVP line (planning/mvp-m0-plan.md, "Memory and load paths";
 *          Documentation/arch/riscv/boot-image-header.rst and the
 *          devicetree specification's FDT header at Linux v7.2).
 */

#ifndef BE_MVP_PAYLOAD_H
#define BE_MVP_PAYLOAD_H

#include <be/types.h>

#include "mvp-gstage.h"
#include "mvp-layout.h"

/* RISC-V Image header (64 bytes, little endian) field offsets. */
#define BE_MVP_KERNEL_HEADER_BYTES	64U
#define BE_MVP_KERNEL_TEXT_OFFSET_AT	8U
#define BE_MVP_KERNEL_IMAGE_SIZE_AT	16U
#define BE_MVP_KERNEL_FLAGS_AT		24U
#define BE_MVP_KERNEL_MAGIC_AT		48U
#define BE_MVP_KERNEL_MAGIC2_AT		56U
#define BE_MVP_KERNEL_MAGIC2		0x05435352U
#define BE_MVP_KERNEL_FLAG_BIG_ENDIAN	BE_U64_C(1)

/* FDT header (40 bytes, big endian) field offsets. */
#define BE_MVP_FDT_HEADER_BYTES		40U
#define BE_MVP_FDT_MAGIC		0xd00dfeedU
#define BE_MVP_FDT_VERSION		17U
#define BE_MVP_FDT_TOTALSIZE_AT		4U
#define BE_MVP_FDT_OFF_STRUCT_AT	8U
#define BE_MVP_FDT_OFF_STRINGS_AT	12U
#define BE_MVP_FDT_OFF_RSVMAP_AT	16U
#define BE_MVP_FDT_VERSION_AT		20U
#define BE_MVP_FDT_SIZE_STRINGS_AT	32U
#define BE_MVP_FDT_SIZE_STRUCT_AT	36U

/**
 * struct be_mvp_payload_layout - the staged boot image, as linked
 * @staging_hpa: L, where every loader places the boot image
 * @kernel_offset: kernel Image offset in the boot image (0xa5000)
 * @kernel_bytes: kernel Image file size
 * @kernel_image_size: the kernel header's image_size
 * @dtb_offset: each guest's DTB offset: G0's at the kernel's end rounded up
 *              to 4 KiB, G1's 4 KiB after it
 * @dtb_bytes: each DTB's size, exactly 4 KiB
 * @image_bytes: the whole boot image, which G1's DTB ends
 *
 * The monitor holds one instance, generated from the pinned payload files;
 * the image checker compares it with the boot image it is linked into.
 */
struct be_mvp_payload_layout {
	be_u64 staging_hpa;
	be_u64 kernel_offset;
	be_u64 kernel_bytes;
	be_u64 kernel_image_size;
	be_u64 dtb_offset[BE_MVP_DOMAINS];
	be_u64 dtb_bytes;
	be_u64 image_bytes;
};

/**
 * struct be_mvp_payload_plan - the checked placement in one guest's window
 * @kernel_source: HPA of the staged kernel, the same for both guests
 * @kernel_target: HPA of the kernel GPA (window base + text_offset)
 * @kernel_gpa: the kernel GPA, the first guest PC
 * @kernel_bytes: kernel bytes to copy
 * @image_size: the kernel's checked image_size, its span from @kernel_gpa
 * @dtb_source: HPA of the guest's staged DTB
 * @dtb_target: HPA of the DTB GPA (the start of the window's last 2 MiB)
 * @dtb_gpa: the DTB GPA, the guest's a1
 * @dtb_bytes: DTB bytes to copy
 *
 * All zero unless the check succeeded.
 */
struct be_mvp_payload_plan {
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
 * enum be_mvp_payload_error - stable payload results
 * @BE_MVP_PAYLOAD_OK: success
 * @BE_MVP_PAYLOAD_NULL: a required pointer is absent
 * @BE_MVP_PAYLOAD_LAYOUT: the link-time layout breaks a size or offset rule
 * @BE_MVP_PAYLOAD_WINDOW: a window cannot hold the kernel span and DTB, the
 *                         windows overlap, or the staged image overlaps a
 *                         window, the monitor's core, a G-stage pool, the
 *                         hart region, the MVP region, or the shared pages
 * @BE_MVP_PAYLOAD_KERNEL_MAGIC: magic is not "RISCV\0\0\0"
 * @BE_MVP_PAYLOAD_KERNEL_MAGIC2: magic2 is not "RSC\x05"
 * @BE_MVP_PAYLOAD_KERNEL_OFFSET: text_offset is not 0x200000
 * @BE_MVP_PAYLOAD_KERNEL_ENDIAN: flags marks a big-endian kernel
 * @BE_MVP_PAYLOAD_KERNEL_SIZE: image_size is below the file size, differs
 *                             from the layout, exceeds its budget, or ends
 *                             at or above the DTB slot
 * @BE_MVP_PAYLOAD_DTB_MAGIC: a DTB's FDT magic is wrong
 * @BE_MVP_PAYLOAD_DTB_SIZE: a DTB's totalsize is not the layout's DTB size
 * @BE_MVP_PAYLOAD_DTB_VERSION: a DTB's version is not 17
 * @BE_MVP_PAYLOAD_DTB_BLOCKS: a block offset or size leaves its DTB
 */
enum be_mvp_payload_error {
	BE_MVP_PAYLOAD_OK = 0,
	BE_MVP_PAYLOAD_NULL,
	BE_MVP_PAYLOAD_LAYOUT,
	BE_MVP_PAYLOAD_WINDOW,
	BE_MVP_PAYLOAD_KERNEL_MAGIC,
	BE_MVP_PAYLOAD_KERNEL_MAGIC2,
	BE_MVP_PAYLOAD_KERNEL_OFFSET,
	BE_MVP_PAYLOAD_KERNEL_ENDIAN,
	BE_MVP_PAYLOAD_KERNEL_SIZE,
	BE_MVP_PAYLOAD_DTB_MAGIC,
	BE_MVP_PAYLOAD_DTB_SIZE,
	BE_MVP_PAYLOAD_DTB_VERSION,
	BE_MVP_PAYLOAD_DTB_BLOCKS,
};

/**
 * be_mvp_payload_check - check the layout and every header, then plan
 * @layout: the link-time layout
 * @maps: the two walked G-stage windows, G0's then G1's
 * @staged: the staged boot image's bytes as HS reads them, at
 *          @layout->staging_hpa in the monitor; only the kernel's 64-byte
 *          and each DTB's 40-byte headers are read
 * @plans: two plans, G0's then G1's; zeroed first, filled only on success
 *
 * The layout must place the kernel at 0xa5000, hold 64 bytes to 4 MiB of
 * kernel, put G0's 4 KiB DTB at the next 4 KiB boundary and G1's right
 * after it, and end the image there, at most 4 MiB in all. The staged
 * image must lie outside both windows, the monitor's core, both pools, the
 * hart region, the MVP region, and the shared pages, M1's channel page
 * among them (planning/mvp-m2-plan.md, "Memory and load paths"), and the
 * windows must not overlap. The kernel must carry both magics, text_offset
 * 0x200000, little endian, and the layout's image_size, at least its file
 * size and at most 8 MiB, ending below each window's DTB slot. Each DTB
 * must carry its magic, the layout's totalsize, version 17, and blocks
 * inside it.
 *
 * Return: %BE_MVP_PAYLOAD_OK or the first error found.
 */
enum be_mvp_payload_error
be_mvp_payload_check(const struct be_mvp_payload_layout *layout,
		    const struct be_mvp_gstage_map *maps, const be_u8 *staged,
		    struct be_mvp_payload_plan *plans);

#endif
