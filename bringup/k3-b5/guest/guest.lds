/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: layout of the K3 B5 test guest in the accepted management map:
 *          code and read-only data in the one R-X code page at GPA
 *          0x4001_0000, entry first; BSS at the bottom of the RW private
 *          page at GPA 0x4000_0000, below a stack topped at 0x4000_1000.
 * Trust:   the monitor embeds only .text and .rodata (the payload); the code
 *          page is R-X, so initialized writable data cannot exist.
 * Scope:   B5 guest only (planning/k3-b5-plan.md).
 */

OUTPUT_ARCH(riscv)
ENTRY(_start)

GUEST_CODE_BASE = 0x40010000;
GUEST_CODE_END = 0x40011000;
GUEST_PRIVATE_BASE = 0x40000000;
GUEST_STACK_TOP = 0x40001000;
GUEST_STACK_RESERVE = 0xc00;

SECTIONS
{
	. = GUEST_CODE_BASE;
	.text :
	{
		__guest_code_start = .;
		KEEP(*(.text.entry))
		*(.text .text.*)
	}
	.rodata : ALIGN(8)
	{
		*(.rodata .rodata.* .srodata .srodata.*)
		__guest_code_end = .;
	}
	.data :
	{
		*(.data .data.* .sdata .sdata.* .got .got.* .tdata .tdata.*)
	}

	. = GUEST_PRIVATE_BASE;
	.bss (NOLOAD) : ALIGN(16)
	{
		__bss_start = .;
		*(.bss .bss.* .sbss .sbss.* .tbss .tbss.* COMMON)
		. = ALIGN(8);
		__bss_end = .;
	}

	/DISCARD/ :
	{
		*(.comment) *(.note .note.*) *(.eh_frame .eh_frame.*)
		*(.interp) *(.dynamic) *(.dynsym) *(.dynstr) *(.hash)
		*(.gnu.hash) *(.rela .rela.*) *(.plt .plt.*)
	}
}

ASSERT(_start == GUEST_CODE_BASE, "B5 guest entry moved")
ASSERT(__guest_code_start == GUEST_CODE_BASE, "B5 guest code moved")
ASSERT(__guest_code_end <= GUEST_CODE_END, "B5 guest code overflows its page")
ASSERT(SIZEOF(.data) == 0, "B5 guest has initialized writable data")
ASSERT(__bss_start == GUEST_PRIVATE_BASE, "B5 guest BSS moved")
ASSERT(__bss_end <= GUEST_STACK_TOP - GUEST_STACK_RESERVE,
	"B5 guest BSS overlaps its stack reserve")
