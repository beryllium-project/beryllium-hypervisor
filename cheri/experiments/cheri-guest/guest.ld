/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> */
/*
 * The CHERI test guest at Beryllium's guest kernel address, GPA 0x80200000
 * (mvp/src/mvp-layout.h, BE_MVP_KERNEL_GPA), as a Linux Image would be.
 */
OUTPUT_ARCH(riscv)
ENTRY(_start)

SECTIONS
{
	. = 0x80200000;
	__image_start = .;
	.head : { KEEP(*(.head)) }
	.text : { *(.text .text.*) }
	.rodata : { *(.rodata .rodata.* .srodata .srodata.*) }
	.data : { *(.data .data.* .sdata .sdata.*) }
	. = ALIGN(16);
	.bss (NOLOAD) : {
		__bss_start = .;
		*(.bss .bss.* .sbss .sbss.* COMMON)
		. = ALIGN(16);
		__bss_end = .;
	}
	. = ALIGN(4096);
	__image_end = .;
	_image_size = __image_end - __image_start;
	/DISCARD/ : { *(.comment) *(.note .note.*) *(.eh_frame .eh_frame_hdr) *(.riscv.attributes) }
}
