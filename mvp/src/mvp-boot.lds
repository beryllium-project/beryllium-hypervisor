/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: layout of the MVP boot image: the MVP shim's header,
 *          descriptor, and stub text; the report lines; the MVP monitor
 *          flat image; and the guest payload, the kernel Image, then G0's
 *          DTB and G1's DTB.
 * Contract: BE_B3_LINK_BASE is supplied with --defsym. The build links the
 *          same objects at two bases and requires byte-identical flat
 *          images, so the loaded bytes carry no absolute image address.
 * Scope:   the stub page, the 0xa4000-byte monitor flat image at offset
 *          0x1000, and the guest payload at offset 0xa5000, at most 4 MiB
 *          in all (planning/mvp-m0-plan.md, "Memory and load paths", and
 *          Plan revision M0-A.1). A counted copy of
 *          bringup/k3-b7/src/b7-boot.lds: MVP names and the MVP flat
 *          image.
 */

OUTPUT_ARCH(riscv)
ENTRY(be_b3_head)

PHDRS
{
	text PT_LOAD FLAGS(5);
	data PT_LOAD FLAGS(6);
	payload PT_LOAD FLAGS(4);
	guest PT_LOAD FLAGS(4);
}

SECTIONS
{
	. = BE_B3_LINK_BASE;
	__be_b3_image_start = .;

	.text :
	{
		KEEP(*(.text.be_b3_head))
		*(.text .text.*)
	} :text

	.data : ALIGN(8)
	{
		KEEP(*(.data.be_b3))
		*(.data .data.* .sdata .sdata.*)
	} :data

	.payload : ALIGN(4096)
	{
		__be_b3_payload_start = .;
		KEEP(*(.payload.be_b3))
		__be_b3_payload_end = .;
	} :payload

	.guest : ALIGN(4096)
	{
		__be_mvp_guest_start = .;
		KEEP(*(.guest.be_mvp))
		__be_mvp_guest_end = .;
	} :guest

	__be_b3_image_end = .;
	__be_b3_image_size = __be_b3_image_end - __be_b3_image_start;
	__be_b3_payload_size = __be_b3_payload_end - __be_b3_payload_start;
	__be_b3_payload_offset = __be_b3_payload_start - __be_b3_image_start;

	/DISCARD/ :
	{
		*(.note .note.* .comment .eh_frame)
	}
}

ASSERT((BE_B3_LINK_BASE & 0xfff) == 0, "B3 link base must be 4 KiB aligned")
ASSERT(be_b3_head == __be_b3_image_start, "B3 header must start the image")
ASSERT(be_b3_descriptor == __be_b3_image_start + 0x40,
	"B3 descriptor must follow the 64-byte header")
ASSERT(be_b3_payload == __be_b3_payload_start, "B3 payload label moved")
ASSERT(__be_b3_payload_offset == 0x1000, "B3 stub must fit in one page")
ASSERT(__be_b3_payload_size == 0xa4000,
	"B3 payload must be the MVP flat image")
ASSERT(__be_mvp_guest_start - __be_b3_image_start == 0xa5000 &&
	be_mvp_guest_kernel == __be_mvp_guest_start,
	"MVP kernel must follow the monitor image at 0xa5000")
ASSERT(be_mvp_guest_kernel_end - be_mvp_guest_kernel >= 0x40 &&
	be_mvp_guest_kernel_end - be_mvp_guest_kernel <= 0x400000,
	"MVP kernel must hold its header and fit 4 MiB")
ASSERT((be_mvp_guest_dtb0 & 0xfff) == 0 &&
	be_mvp_guest_dtb0 >= be_mvp_guest_kernel_end &&
	be_mvp_guest_dtb0 - be_mvp_guest_kernel_end < 0x1000,
	"MVP G0 DTB must start at the kernel's next 4 KiB boundary")
ASSERT(be_mvp_guest_dtb0_end - be_mvp_guest_dtb0 == 0x1000,
	"MVP G0 DTB must be exactly 4 KiB")
ASSERT(be_mvp_guest_dtb1 == be_mvp_guest_dtb0_end &&
	be_mvp_guest_dtb1_end - be_mvp_guest_dtb1 == 0x1000,
	"MVP G1 DTB must follow G0's and be exactly 4 KiB")
ASSERT(__be_mvp_guest_end == be_mvp_guest_dtb1_end &&
	__be_b3_image_end == __be_mvp_guest_end,
	"MVP G1 DTB must end the boot image")
ASSERT(__be_b3_image_size <= 0x400000, "MVP boot image must fit 4 MiB")
