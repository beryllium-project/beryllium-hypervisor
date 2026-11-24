/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: the M13-4 probe images' shared declarations
 *          (planning/mvp-m13-3-review-point.md, sections 2 and 3): the
 *          table's layout and ops, a started hart's slot, the assembly
 *          boundary, and the macros that write a table.
 * Scope:   C (m13.c, the host test) and assembly (head.S, harts.S, the
 *          tables); the tables use only portable data directives, so that
 *          the host's assembler builds them for the host test.
 */
#ifndef BE_M13_H
#define BE_M13_H

/* A table entry's op. */
#define BE_M13_OP_READ		1
#define BE_M13_OP_WRITE		2
#define BE_M13_OP_CSRR		3
#define BE_M13_OP_CSRW		4
#define BE_M13_OP_GUARD_END	5
#define BE_M13_OP_GUARD_ELSE	6
/* A table entry is 64 bytes, its name at most 23 characters. */
#define BE_M13_ENTRY_SHIFT	6
#define BE_M13_NAME_SIZE	32
#define BE_M13_ENTRIES_MAX	128
/* be_m13_access's status. */
#define BE_M13_MADE		0
#define BE_M13_FAULTED		1
#define BE_M13_REFUSED_INDEX	2
/* A slot's state (harts.S). */
#define BE_M13_STARTING		1
#define BE_M13_DONE		2
#define BE_M13_REFUSED		3
#define BE_M13_TRAPPED		4
/* The wait for a started hart's report: 2^27 ticks of time. */
#define BE_M13_WAIT_TICKS	0x8000000

#ifdef __ASSEMBLER__

	.macro be_m13_begin image
	.section .rodata.be_m13_table, "a", @progbits
	.globl be_m13_image
	.type be_m13_image, @object
be_m13_image:
	.byte	0x30 + \image
	.size be_m13_image, 1
	.balign 64
	.globl be_m13_table
	.type be_m13_table, @object
be_m13_table:
	.set	be_m13_index, 0
	.endm

	/* address, value, op, width, probe, hart, ref, 0, 0, name */
	.macro be_m13_entry op, probe, hart, width, address, value, ref, name
	.quad	\address
	.quad	\value
	.byte	\op, \width, \probe, \hart
	.short	\ref, 0
	.quad	0
.Lbe_m13_name\@:
	.ascii	"\name"
	.space	BE_M13_NAME_SIZE - (. - .Lbe_m13_name\@)
	.set	be_m13_index, be_m13_index + 1
	.endm

	.macro be_m13_read probe, address, width, name
	be_m13_entry BE_M13_OP_READ, \probe, 0, \width, \address, 0, 0, \name
	.endm

	.macro be_m13_write probe, address, width, value, name
	be_m13_entry BE_M13_OP_WRITE, \probe, 0, \width, \address, \value, 0, \name
	.endm

	.macro be_m13_csrr probe, hart, name
	be_m13_entry BE_M13_OP_CSRR, \probe, \hart, 8, 0x607, 0, 0, \name
	.endm

	.macro be_m13_csrw probe, hart, value, name
	be_m13_entry BE_M13_OP_CSRW, \probe, \hart, 8, 0x607, \value, 0, \name
	.endm

	/* A guard's read is named by its index, a symbol .set after it. */
	.macro be_m13_guard_end probe, ref, value, name
	be_m13_entry BE_M13_OP_GUARD_END, \probe, 0, 0, 0, \value, \ref, \name
	.endm

	.macro be_m13_guard_else probe, ref, value, name
	be_m13_entry BE_M13_OP_GUARD_ELSE, \probe, 0, 0, 0, \value, \ref, \name
	.endm

	.macro be_m13_end
	.globl be_m13_table_end
	.type be_m13_table_end, @object
be_m13_table_end:
	.size be_m13_table, be_m13_table_end - be_m13_table
	.size be_m13_table_end, 0
	.endm

#else

struct be_m13_entry {
	unsigned long address;
	unsigned long value;
	unsigned char op;
	unsigned char width;
	unsigned char probe;
	unsigned char hart;
	unsigned short ref;
	unsigned short zero16;
	unsigned long zero64;
	char name[BE_M13_NAME_SIZE];
};

/* Two words, returned in a0 and a1: an SBI call's error and value; an
 * access's status and value; a started hart's HSM error and state. */
struct be_m13_ret {
	long status;
	unsigned long value;
};

/* A started hart's report (harts.S): its state; hgeie as booted, after all
 * ones, and after 0; the a0 that it saw; a trap's scause, sepc, stval. */
struct be_m13_slot {
	unsigned long state;
	unsigned long read[3];
	unsigned long a0;
	unsigned long scause;
	unsigned long sepc;
	unsigned long stval;
};

/* The image's table (table-N.S) and its number, an ASCII digit. */
extern const struct be_m13_entry be_m13_table[];
extern const struct be_m13_entry be_m13_table_end[];
extern const char be_m13_image;
/* head.S: the last fault at an access site, its scause and stval. */
extern unsigned long be_m13_fault[2];
/* harts.S (image 1): harts 0 to 2, and one that only a mask reaches. */
extern struct be_m13_slot be_m13_slots[4];

/* head.S */
struct be_m13_ret be_m13_sbi_base(unsigned long fid, unsigned long arg);
long be_m13_putc(unsigned long byte);
void be_m13_srst(void) __attribute__((noreturn));
void be_m13_park(void) __attribute__((noreturn));
unsigned long be_m13_read_satp(void);
struct be_m13_ret be_m13_access(unsigned long index);
/* harts.S, image 1 alone */
void be_m13_p1(unsigned long hart);
struct be_m13_ret be_m13_hart_run(unsigned long hart);
/* m13.c, called from head.S */
void be_m13_main(unsigned long hart, unsigned long fdt, unsigned long base)
	__attribute__((noreturn));
void be_m13_refuse(unsigned long hart) __attribute__((noreturn));
void be_m13_trap_fail(unsigned long scause, unsigned long sepc,
		      unsigned long stval) __attribute__((noreturn));

#endif
#endif
