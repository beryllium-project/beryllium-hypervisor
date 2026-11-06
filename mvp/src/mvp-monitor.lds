/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP monitor's image layout (planning/mvp-m6-plan.md, D-4):
 *          a counted copy of the MVP port's r5-beryllium.lds (mvp/README.md)
 *          without the accepted fixture roots, stacks, saved, private, and
 *          shared pages and guest code. The core's first 0x8000 bytes are
 *          the monitor code; then the monitor data: the MVP core profile's
 *          inventory and proposal (mvp-config.o, the R1 input section), the
 *          constants, data, and BSS, and the diagnostic page; then hart 0's
 *          stack; the core's rest is unused, zero in the flat image. The
 *          MVP pool, hart region, and MVP region follow as before.
 * Trust:   load-bearing placement and W^X boundary checked independently
 *          (tests/check-image.py).
 * Scope:   the MVP line's images; no dynamic loading.
 */

OUTPUT_ARCH(riscv)
ENTRY(be_reset)

PHDRS
{
	monitor_text PT_LOAD FLAGS(5);
	monitor_ro PT_LOAD FLAGS(4);
	monitor_data PT_LOAD FLAGS(6);
	mvp_pool PT_LOAD FLAGS(6);
	mvp_text PT_LOAD FLAGS(5);
	mvp_ro PT_LOAD FLAGS(4);
	mvp_data PT_LOAD FLAGS(6);
}

SECTIONS
{
	. = 0x102000000;
	.monitor.text : ALIGN(16)
	{
		__be_monitor_code_start = .;
		KEEP(*(.text.be.r5.entry))
		/* MVP: not the MVP layer's C objects, which the MVP region
		 * holds; one EXCLUDE_FILE before each section pattern, the
		 * form GNU ld and lld read alike. */
		*(EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o
			       *mvp-input.o *mvp-log.o) .text
		  EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o
			       *mvp-input.o *mvp-log.o) .text.*)
		. = ALIGN(16);
		__be_monitor_code_end = .;
	} :monitor_text

	. = 0x102008000;
	__be_monitor_data_start = .;
	.monitor.input : ALIGN(16)
	{
		__be_input_start = .;
		*mvp-config.o(.rodata .rodata.*)
		__be_input_end = .;
	} :monitor_ro
	.monitor.rodata : ALIGN(16)
	{
		/* MVP: the log's monitor-rodata range (M9;
		 * mvp/docs/log-profile.md, 2.7) is this section. */
		__be_monitor_rodata_start = .;
		/* MVP: not the MVP layer's C objects, which the MVP region
		 * holds; one EXCLUDE_FILE before each section pattern, the
		 * form GNU ld and lld read alike. */
		*(EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o
			       *mvp-input.o *mvp-log.o) .rodata
		  EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o
			       *mvp-input.o *mvp-log.o) .rodata.*)
		__be_monitor_rodata_end = .;
	} :monitor_ro
	.monitor.data : ALIGN(16)
	{
		/* MVP: not the MVP layer's C objects, which the MVP region
		 * holds; one EXCLUDE_FILE before each section pattern, the
		 * form GNU ld and lld read alike. */
		*(EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o
			       *mvp-input.o *mvp-log.o) .data
		  EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o
			       *mvp-input.o *mvp-log.o) .data.*)
		. = ALIGN(8);
		__be_bss_start = .;
		*(EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o
			       *mvp-input.o *mvp-log.o) .bss
		  EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o
			       *mvp-input.o *mvp-log.o) .bss.*)
		*(EXCLUDE_FILE(*mvp-runtime.o *mvp-hartmain.o *mvp-sbi.o
			       *mvp-hart.o *mvp-ring.o *mvp-gstage.o
			       *mvp-payload.o *mvp-probe.o *mvp-sha256.o
			       *mvp-core.o *mvp-executor.o
			       *mvp-input.o *mvp-log.o) COMMON)
		. = ALIGN(8);
		__be_bss_end = .;
	} :monitor_data

	. = 0x10200f000;
	.diagnostic (NOLOAD) : ALIGN(4096)
	{
		__be_diagnostic_start = .;
		. += 0x1000;
		__be_diagnostic_end = .;
		__be_monitor_data_end = .;
	} :monitor_data

	/* MVP: hart 0's stack, the control hart's trusted stack, after the
	 * monitor data; the core's rest is unused. */
	. = 0x102010000;
	.stack.control (NOLOAD) : ALIGN(4096)
	{
		__be_control_stack_start = .; . += 0x2000;
		__be_control_stack_end = .;
	} :monitor_data

	/* MVP: the MVP-owned G-stage pool, domain 0's 32 KiB pool then
	 * domain 1's, each a 16 KiB root and one level-1 page, the rest
	 * zero; outside every accepted extent. */
	. = 0x102034000;
	.gstage.root.mvp (NOLOAD) : ALIGN(0x4000)
	{
		__be_mvp_pool_start = .; . += 0x10000;
		__be_mvp_pool_end = .;
	} :mvp_pool

	ASSERT(__be_mvp_pool_start == 0x102034000 &&
	       __be_mvp_pool_end == 0x102044000, "MVP G-stage pool moved")
	ASSERT((__be_mvp_pool_start & 0x3fff) == 0,
	       "MVP G-stage pool alignment")
	ASSERT(__be_control_stack_end <= __be_mvp_pool_start,
	       "MVP G-stage pool overlaps hart 0's stack")

	/* MVP: the hart region, one 64 KiB block per domain hart (its
	 * trusted stack, saved page, state page, and rings), written only
	 * at run time; after the pool, in its read-write segment. */
	. = 0x102044000;
	.hart.mvp (NOLOAD) : ALIGN(0x4000)
	{
		__be_mvp_hart_region_start = .; . += 0x20000;
		__be_mvp_hart_region_end = .;
	} :mvp_pool

	ASSERT(__be_mvp_hart_region_start == 0x102044000 &&
	       __be_mvp_hart_region_end == 0x102064000,
	       "MVP hart region moved")
	ASSERT((__be_mvp_hart_region_start & 0x3fff) == 0,
	       "MVP hart region alignment")
	ASSERT(__be_mvp_pool_end <= __be_mvp_hart_region_start,
	       "MVP hart region overlaps the G-stage pool")

	/* MVP: the MVP region, after the hart region and outside every
	 * accepted extent: the MVP layer's C objects' code, constants,
	 * data, and BSS, named object by object. The flat image loads it;
	 * hart 0 clears its BSS before it uses any of it. */
	. = 0x102064000;
	.mvp.text : ALIGN(0x4000)
	{
		__be_mvp_region_start = .;
		__be_mvp_text_start = .;
		*mvp-runtime.o(.text .text.*)
		*mvp-hartmain.o(.text .text.*)
		*mvp-sbi.o(.text .text.*)
		*mvp-hart.o(.text .text.*)
		*mvp-ring.o(.text .text.*)
		*mvp-gstage.o(.text .text.*)
		*mvp-payload.o(.text .text.*)
		*mvp-probe.o(.text .text.*)
		*mvp-sha256.o(.text .text.*)
		*mvp-core.o(.text .text.*)
		*mvp-executor.o(.text .text.*)
		*mvp-input.o(.text .text.*)
		*mvp-log.o(.text .text.*)
		. = ALIGN(16);
		__be_mvp_text_end = .;
	} :mvp_text
	.mvp.rodata : ALIGN(16)
	{
		/* M9: the log's mvp-rodata range is this section. */
		__be_mvp_rodata_start = .;
		*mvp-runtime.o(.rodata .rodata.*)
		*mvp-hartmain.o(.rodata .rodata.*)
		*mvp-sbi.o(.rodata .rodata.*)
		*mvp-hart.o(.rodata .rodata.*)
		*mvp-ring.o(.rodata .rodata.*)
		*mvp-gstage.o(.rodata .rodata.*)
		*mvp-payload.o(.rodata .rodata.*)
		*mvp-probe.o(.rodata .rodata.*)
		*mvp-sha256.o(.rodata .rodata.*)
		*mvp-core.o(.rodata .rodata.*)
		*mvp-executor.o(.rodata .rodata.*)
		*mvp-input.o(.rodata .rodata.*)
		/* M9: the inert canary, which nothing refers to, kept for the
		 * self-report-flip variant (planning/mvp-m9-plan.md, D-4),
		 * inside the range but at neither of its ends. */
		KEEP(*mvp-log.o(.rodata.be_mvp_log_canary))
		*mvp-log.o(.rodata .rodata.*)
		__be_mvp_rodata_end = .;
	} :mvp_ro
	.mvp.data : ALIGN(16)
	{
		*mvp-runtime.o(.data .data.*)
		*mvp-hartmain.o(.data .data.*)
		*mvp-sbi.o(.data .data.*)
		*mvp-hart.o(.data .data.*)
		*mvp-ring.o(.data .data.*)
		*mvp-gstage.o(.data .data.*)
		*mvp-payload.o(.data .data.*)
		*mvp-probe.o(.data .data.*)
		*mvp-sha256.o(.data .data.*)
		*mvp-core.o(.data .data.*)
		*mvp-executor.o(.data .data.*)
		*mvp-input.o(.data .data.*)
		*mvp-log.o(.data .data.*)
		. = ALIGN(8);
		__be_mvp_bss_start = .;
		*mvp-runtime.o(.bss .bss.* COMMON)
		*mvp-hartmain.o(.bss .bss.* COMMON)
		*mvp-sbi.o(.bss .bss.* COMMON)
		*mvp-hart.o(.bss .bss.* COMMON)
		*mvp-ring.o(.bss .bss.* COMMON)
		*mvp-gstage.o(.bss .bss.* COMMON)
		*mvp-payload.o(.bss .bss.* COMMON)
		*mvp-probe.o(.bss .bss.* COMMON)
		*mvp-sha256.o(.bss .bss.* COMMON)
		*mvp-core.o(.bss .bss.* COMMON)
		*mvp-executor.o(.bss .bss.* COMMON)
		*mvp-input.o(.bss .bss.* COMMON)
		*mvp-log.o(.bss .bss.* COMMON)
		. = ALIGN(8);
		__be_mvp_bss_end = .;
		__be_mvp_region_end = .;
	} :mvp_data

	ASSERT(__be_mvp_region_start == 0x102064000 &&
	       __be_mvp_region_end <= 0x1020a4000,
	       "MVP region moved or overflowed")
	ASSERT((__be_mvp_region_start & 0x3fff) == 0,
	       "MVP region alignment")
	ASSERT(__be_mvp_hart_region_end <= __be_mvp_region_start,
	       "MVP region overlaps the hart region")

	ASSERT(be_reset == 0x102000000, "R5 entry moved")
	ASSERT(__be_monitor_code_start == 0x102000000, "R5 monitor code moved")
	ASSERT(__be_monitor_code_end <= 0x102008000, "R5 monitor code overflow")
	ASSERT(__be_monitor_data_start == 0x102008000, "R5 monitor data moved")
	ASSERT(__be_input_end > __be_input_start, "R5 input section is empty")
	ASSERT(__be_input_start >= __be_monitor_data_start &&
	       __be_input_end <= __be_bss_start, "R5 input escaped rodata")
	ASSERT(__be_bss_end <= 0x10200f000, "R5 monitor data overflow")
	ASSERT(__be_diagnostic_start == 0x10200f000 &&
	       __be_diagnostic_end == 0x102010000, "R5 diagnostic moved")
	ASSERT(__be_monitor_data_end == 0x102010000, "R5 monitor data extent moved")
	ASSERT(__be_control_stack_start == 0x102010000 &&
	       __be_control_stack_end == 0x102012000, "MVP hart 0 stack moved")
	ASSERT(__be_monitor_data_end <= __be_control_stack_start,
	       "MVP hart 0 stack overlaps monitor data")

	/* The vector must be direct-mode legal and inside monitor code. */
	ASSERT((be_mvp_trap_vector & 0x3) == 0, "R5 trap vector misaligned")
	ASSERT(be_mvp_trap_vector >= __be_monitor_code_start &&
	       be_mvp_trap_vector < __be_monitor_code_end,
	       "R5 trap vector escaped monitor code")

	/DISCARD/ :
	{
		*(.comment) *(.eh_frame .eh_frame.*) *(.note .note.*) *(.interp)
		*(.dynamic) *(.dynsym) *(.dynstr) *(.gnu.hash) *(.hash)
		*(.got .got.*) *(.plt .plt.*) *(.rela .rela.*) *(.rel .rel.*)
	}
}
