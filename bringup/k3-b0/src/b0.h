/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: shared declarations for the K3 B0 / BE-K3-L0BOOT boot image.
 * Scope:   assembly/C boundary and linker-provided layout symbols only.
 */

#ifndef BE_B0_H
#define BE_B0_H

/* Linker-provided layout; addresses are taken PC-relatively at run time. */
extern char __be_b0_bss_start[];
extern char __be_b0_bss_end[];
extern char __be_b0_stack_start[];
extern char __be_b0_stack_end[];
extern char __be_b0_image_end[];

/* head.S */
void be_b0_halt(void) __attribute__((noreturn));

/* b0.c, called from head.S */
void be_b0_main(unsigned long hart, unsigned long fdt, unsigned long base)
	__attribute__((noreturn));
void be_b0_trap(unsigned long scause, unsigned long sepc, unsigned long stval)
	__attribute__((noreturn));

#endif
