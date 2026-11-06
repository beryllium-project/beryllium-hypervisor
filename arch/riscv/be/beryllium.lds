/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: executable R3 linker contract derived from the accepted R0 plan.
 * Trust:   load-bearing image boundary. Every security-sensitive physical
 *          extent is fixed and asserted; ELF semantic checks independently
 *          inspect placement, PHDR permissions, symbols, and W^X.
 * Scope:   one fixed QEMU/OpenSBI image only. No dynamic loading, relocation,
 *          Linux ABI, allocator, device, multicore, or R4+ section.
 */

OUTPUT_ARCH(riscv)
ENTRY(be_reset)

PHDRS
{
	monitor_text PT_LOAD FLAGS(5);
	monitor_ro PT_LOAD FLAGS(4);
	monitor_data PT_LOAD FLAGS(6);
	reserved PT_LOAD FLAGS(6);
	guest_management PT_LOAD FLAGS(5);
	guest_protected PT_LOAD FLAGS(5);
}

SECTIONS
{
	. = 0x80200000;
	.monitor.text : ALIGN(16)
	{
		__be_monitor_code_start = .;
		KEEP(*(.text.be.entry))
		*(.text .text.*)
		. = ALIGN(16);
		__be_monitor_code_end = .;
	} :monitor_text

	. = 0x80208000;
	__be_monitor_data_start = .;
	.monitor.input : ALIGN(16)
	{
		__be_input_start = .;
		*r1-config.o(.rodata .rodata.*)
		__be_input_end = .;
	} :monitor_ro

	.monitor.rodata : ALIGN(16)
	{
		*(.rodata .rodata.*)
	} :monitor_ro

	.monitor.data : ALIGN(16)
	{
		*(.data .data.*)
		. = ALIGN(8);
		__be_bss_start = .;
		*(.bss .bss.*)
		*(COMMON)
		. = ALIGN(8);
		__be_bss_end = .;
	} :monitor_data

	. = 0x8020f000;
	.diagnostic (NOLOAD) : ALIGN(4096)
	{
		__be_diagnostic_start = .;
		. += 0x1000;
		__be_diagnostic_end = .;
		__be_monitor_data_end = .;
	} :monitor_data

	. = 0x80214000;
	.gstage.root.management (NOLOAD) : ALIGN(0x4000)
	{
		__be_root_management_start = .;
		. += 0x8000;
		__be_root_management_end = .;
	} :reserved

	.gstage.root.protected (NOLOAD) : ALIGN(0x4000)
	{
		__be_root_protected_start = .;
		. += 0x8000;
		__be_root_protected_end = .;
	} :reserved

	. = 0x80225000;
	.stack.management (NOLOAD) : ALIGN(4096)
	{
		__be_stack_management_start = .;
		. += 0x2000;
		__be_stack_management_end = .;
	} :reserved

	. = 0x80228000;
	.stack.protected (NOLOAD) : ALIGN(4096)
	{
		__be_stack_protected_start = .;
		. += 0x2000;
		__be_stack_protected_end = .;
	} :reserved

	. = 0x8022b000;
	.saved.management (NOLOAD) : ALIGN(4096)
	{
		__be_saved_management_start = .;
		. += 0x1000;
		__be_saved_management_end = .;
	} :reserved

	.saved.protected (NOLOAD) : ALIGN(4096)
	{
		__be_saved_protected_start = .;
		. += 0x1000;
		__be_saved_protected_end = .;
	} :reserved

	. = 0x8022e000;
	.private.management (NOLOAD) : ALIGN(4096)
	{
		__be_private_management_start = .;
		. += 0x1000;
		__be_private_management_end = .;
	} :reserved

	.private.protected (NOLOAD) : ALIGN(4096)
	{
		__be_private_protected_start = .;
		. += 0x1000;
		__be_private_protected_end = .;
	} :reserved

	.shared (NOLOAD) : ALIGN(4096)
	{
		__be_shared_start = .;
		. += 0x1000;
		__be_shared_end = .;
	} :reserved

	. = 0x80232000;
	.guest.code.management : ALIGN(4096)
	{
		__be_guest_management_start = .;
		KEEP(*(.guest.management))
		. = __be_guest_management_start + 0x1000;
		__be_guest_management_end = .;
	} :guest_management

	.guest.code.protected : ALIGN(4096)
	{
		__be_guest_protected_start = .;
		KEEP(*(.guest.protected))
		. = __be_guest_protected_start + 0x1000;
		__be_guest_protected_end = .;
	} :guest_protected

	ASSERT(be_reset == 0x80200000, "R3 entry moved")
	ASSERT(__be_monitor_code_start == 0x80200000,
	       "monitor code start moved")
	ASSERT(__be_monitor_code_end <= 0x80208000,
	       "monitor code overflow")
	ASSERT(__be_monitor_data_start == 0x80208000,
	       "monitor data start moved")
	ASSERT(__be_input_end > __be_input_start,
	       "fixed input section is empty")
	ASSERT(__be_input_start >= __be_monitor_data_start &&
	       __be_input_end <= __be_bss_start,
	       "fixed input escaped read-only monitor data")
	ASSERT(__be_bss_end <= 0x8020f000,
	       "monitor data overflowed diagnostic page")
	ASSERT(__be_diagnostic_start == 0x8020f000 &&
	       __be_diagnostic_end == 0x80210000,
	       "diagnostic page moved")
	ASSERT(__be_monitor_data_end == 0x80210000,
	       "monitor data extent moved")

	ASSERT(__be_root_management_start == 0x80214000 &&
	       __be_root_management_end == 0x8021c000,
	       "management root pool moved")
	ASSERT(__be_root_protected_start == 0x8021c000 &&
	       __be_root_protected_end == 0x80224000,
	       "protected root pool moved")
	ASSERT((__be_root_management_start & 0x3fff) == 0 &&
	       (__be_root_protected_start & 0x3fff) == 0,
	       "Sv39x4 root pool lost 16 KiB alignment")

	ASSERT(__be_stack_management_start == 0x80225000 &&
	       __be_stack_management_end == 0x80227000,
	       "management trusted stack moved")
	ASSERT(__be_stack_protected_start == 0x80228000 &&
	       __be_stack_protected_end == 0x8022a000,
	       "protected trusted stack moved")
	ASSERT(__be_saved_management_start == 0x8022b000 &&
	       __be_saved_management_end == 0x8022c000,
	       "management saved state moved")
	ASSERT(__be_saved_protected_start == 0x8022c000 &&
	       __be_saved_protected_end == 0x8022d000,
	       "protected saved state moved")
	ASSERT(__be_private_management_start == 0x8022e000 &&
	       __be_private_management_end == 0x8022f000,
	       "management private page moved")
	ASSERT(__be_private_protected_start == 0x8022f000 &&
	       __be_private_protected_end == 0x80230000,
	       "protected private page moved")
	ASSERT(__be_shared_start == 0x80230000 &&
	       __be_shared_end == 0x80231000,
	       "shared page moved")
	ASSERT(__be_guest_management_start == 0x80232000 &&
	       __be_guest_management_end == 0x80233000,
	       "management guest page moved")
	ASSERT(__be_guest_protected_start == 0x80233000 &&
	       __be_guest_protected_end == 0x80234000,
	       "protected guest page moved")
	ASSERT(be_r3_management_guest_start == 0x80232000,
	       "management guest first instruction moved")
	ASSERT(be_r3_protected_guest_unentered == 0x80233000,
	       "protected guest page first instruction moved")

	/DISCARD/ :
	{
		*(.comment)
		*(.eh_frame .eh_frame.*)
		*(.note .note.*)
		*(.interp)
		*(.dynamic)
		*(.dynsym)
		*(.dynstr)
		*(.gnu.hash)
		*(.hash)
		*(.got .got.*)
		*(.plt .plt.*)
		*(.rela .rela.*)
		*(.rel .rel.*)
	}
}
