/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: the layout of an M13-4 probe image (B0's b0.lds the model).
 * Contract: BE_M13_LINK_BASE is supplied with --defsym. The build links the
 *          same objects at the board's base and QEMU's and requires the two
 *          raw images byte-identical, so the bytes carry no absolute
 *          address of the image's own.
 * Scope:   one image whose every allocated section is PROGBITS: the raw
 *          image is the whole footprint, and so the header's image_size:
 *          header and text, read-only data (the table first), data, and the
 *          entry hart's stack, at most 64 KiB.
 */

OUTPUT_ARCH(riscv)
ENTRY(be_m13_head)

PHDRS
{
	text PT_LOAD FLAGS(5);
	rodata PT_LOAD FLAGS(4);
	data PT_LOAD FLAGS(6);
}

SECTIONS
{
	. = BE_M13_LINK_BASE;
	__be_m13_image_start = .;

	.head.text :
	{
		KEEP(*(.head.text))
	} :text

	.text :
	{
		KEEP(*(.text.be_m13_entry))
		*(.text .text.*)
	} :text

	. = ALIGN(4096);
	.rodata :
	{
		KEEP(*(.rodata.be_m13_table))
		*(.rodata .rodata.* .srodata .srodata.*)
	} :rodata

	. = ALIGN(4096);
	.data :
	{
		*(.data .data.* .sdata .sdata.*)
		*(.bss .bss.* .sbss .sbss.*)
		*(COMMON)
	} :data

	.stack : ALIGN(4096)
	{
		__be_m13_stack_start = .;
		KEEP(*(.be_m13_stack))
		__be_m13_stack_end = .;
	} :data

	__be_m13_image_end = .;
	__be_m13_image_size = __be_m13_image_end - __be_m13_image_start;

	/DISCARD/ :
	{
		*(.eh_frame .eh_frame_hdr .note .note.* .comment)
	}
}

ASSERT((BE_M13_LINK_BASE & 0xfff) == 0, "M13 link base must be 4 KiB aligned")
ASSERT(be_m13_head == __be_m13_image_start, "M13 header must start the image")
ASSERT(be_m13_entry == __be_m13_image_start + 0x60,
	"M13 entry must follow the header at 0x60")
ASSERT((be_m13_table & 0x3f) == 0, "M13 table must be 64-byte aligned")
ASSERT(__be_m13_stack_end - __be_m13_stack_start == 0x2000,
	"M13 stack must be 8 KiB")
ASSERT((__be_m13_image_end & 0xfff) == 0, "M13 image must end on a page")
ASSERT(__be_m13_image_size <= 0x10000, "M13 image exceeds 64 KiB")
