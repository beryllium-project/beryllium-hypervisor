/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: layout of the MVP VS probe stub (B5's guest.lds style): code and
 *          read-only data in one page at GPA 0x8020_0000, the kernel's GPA
 *          in every window, entry first; no data or BSS, and a stack below
 *          GPA 0x8008_0000, inside the window and away from X (0x8010_0000).
 * Trust:   the probe images embed only .text and .rodata; nothing writable
 *          is initialized.
 * Scope:   probe images only (planning/mvp-m0-plan.md, Platform record).
 */

OUTPUT_ARCH(riscv)
ENTRY(_start)

STUB_CODE_BASE = 0x80200000;
STUB_CODE_END = 0x80201000;

SECTIONS
{
	. = STUB_CODE_BASE;
	.text :
	{
		__stub_code_start = .;
		KEEP(*(.text.entry))
		*(.text .text.*)
	}
	.rodata : ALIGN(8)
	{
		*(.rodata .rodata.* .srodata .srodata.*)
		__stub_code_end = .;
	}
	.data :
	{
		*(.data .data.* .sdata .sdata.* .got .got.* .tdata .tdata.*)
	}
	.bss (NOLOAD) :
	{
		*(.bss .bss.* .sbss .sbss.* .tbss .tbss.* COMMON)
	}

	/DISCARD/ :
	{
		*(.comment) *(.note .note.*) *(.eh_frame .eh_frame.*)
		*(.interp) *(.dynamic) *(.dynsym) *(.dynstr) *(.hash)
		*(.gnu.hash) *(.rela .rela.*) *(.plt .plt.*)
	}
}

ASSERT(_start == STUB_CODE_BASE, "probe stub entry moved")
ASSERT(__stub_code_start == STUB_CODE_BASE, "probe stub code moved")
ASSERT(__stub_code_end <= STUB_CODE_END, "probe stub overflows its page")
ASSERT(SIZEOF(.data) == 0, "probe stub has initialized writable data")
ASSERT(SIZEOF(.bss) == 0, "probe stub has BSS")
