/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: relocatable link layout for the K3 B0 boot image.
 * Contract: BE_B0_LINK_BASE is supplied with --defsym. The build links the
 *          same objects at several bases and requires byte-identical raw
 *          images, proving the loaded bytes carry no absolute address.
 * Scope:   one image: header, text, read-only data, BSS, and a private stack.
 */

OUTPUT_ARCH(riscv)
ENTRY(be_b0_head)

PHDRS
{
	text PT_LOAD FLAGS(5);
	rodata PT_LOAD FLAGS(4);
	data PT_LOAD FLAGS(6);
}

SECTIONS
{
	. = BE_B0_LINK_BASE;
	__be_b0_image_start = .;

	.head.text :
	{
		KEEP(*(.head.text))
	} :text

	.text : ALIGN(16)
	{
		KEEP(*(.text.be_b0_entry))
		*(.text .text.*)
	} :text

	. = ALIGN(4096);
	.rodata :
	{
		*(.rodata .rodata.* .srodata .srodata.*)
	} :rodata

	. = ALIGN(4096);
	.data :
	{
		*(.data .data.* .sdata .sdata.*)
	} :data

	.bss (NOLOAD) : ALIGN(16)
	{
		__be_b0_bss_start = .;
		*(.bss .bss.* .sbss .sbss.*)
		*(COMMON)
		. = ALIGN(16);
		__be_b0_bss_end = .;
	} :data

	.stack (NOLOAD) : ALIGN(4096)
	{
		__be_b0_stack_start = .;
		. += 0x4000;
		__be_b0_stack_end = .;
	} :data

	. = ALIGN(4096);
	__be_b0_image_end = .;
	__be_b0_image_size = __be_b0_image_end - __be_b0_image_start;

	/DISCARD/ :
	{
		*(.eh_frame .eh_frame_hdr .note .note.* .comment)
	}
}

ASSERT((BE_B0_LINK_BASE & 0xfff) == 0, "B0 link base must be 4 KiB aligned")
ASSERT(be_b0_head == __be_b0_image_start, "B0 header must start the image")
ASSERT(__be_b0_image_size <= 0x100000, "B0 footprint exceeds 1 MiB")
