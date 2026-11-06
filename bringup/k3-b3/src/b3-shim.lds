/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: layout of the K3 B3 booti image: header, descriptor, and stub
 *          text; the report lines; and the accepted B2 flat image.
 * Contract: BE_B3_LINK_BASE is supplied with --defsym. The build links the
 *          same object at two bases and requires byte-identical flat
 *          images, so the loaded bytes carry no absolute image address.
 * Scope:   one image of exactly 0x35000 bytes: the stub page, then the
 *          0x34000-byte payload at offset 0x1000.
 */

OUTPUT_ARCH(riscv)
ENTRY(be_b3_head)

PHDRS
{
	text PT_LOAD FLAGS(5);
	data PT_LOAD FLAGS(6);
	payload PT_LOAD FLAGS(4);
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
ASSERT(__be_b3_payload_size == 0x34000, "B3 payload must be the B2 image")
ASSERT(__be_b3_image_size == 0x35000, "B3 image must be 0x35000 bytes")
