/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jmorris@namei.org> */
/* The firmware tests' payload: text and read-only data only. */
OUTPUT_ARCH(riscv)
ENTRY(_start)
SECTIONS
{
	. = 0x80200000;
	.text : {
		*(.text.entry)
		*(.text .text.*)
		*(.rodata .rodata.* .srodata .srodata.*)
	}
	/DISCARD/ : { *(.data .data.* .sdata .sdata.* .bss .bss.* .sbss .sbss.* .comment .note.* .riscv.attributes .eh_frame*) }
}
