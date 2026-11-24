// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: the M13-4 probe images' program
 *          (planning/mvp-m13-3-review-point.md, sections 2 and 3): the SBI
 *          requirements, then the image's table walked from entry 0, a line
 *          printed for each access, guard, and started hart, then END and
 *          SRST.
 * Contract: be_m13_main, be_m13_refuse, and be_m13_trap_fail are called
 *          from head.S on the entry hart, and never return. Built twice:
 *          BE_M13_HARTS=1 (image 1, which links harts.S) and 0.
 * Trust:   no device is touched here: each access is be_m13_access(index),
 *          which takes its address, width, and written value from the table
 *          itself. An entry that the program cannot make ends the run with
 *          FAIL table. The console takes one byte for each SBI call
 *          (DBCN write-byte), so the firmware reads no memory of ours.
 * Scope:   one line at a time, from b0-format.c's bounded builder; only the
 *          entry hart prints.
 */
#include "m13.h"
#include "b0-format.h"

#ifndef BE_M13_HARTS
#error "BE_M13_HARTS must be defined (0 or 1)"
#endif

#define SBI_BASE_GET_SPEC_VERSION	0UL
#define SBI_BASE_GET_IMPL_ID		1UL
#define SBI_BASE_GET_IMPL_VERSION	2UL
#define SBI_BASE_PROBE_EXTENSION	3UL
#define SBI_EXT_DBCN			0x4442434eUL
#define SBI_EXT_SRST			0x53525354UL
#define SBI_EXT_HSM			0x48534dUL

#define BE_M13_CSR_HGEIE		0x607UL
#define BE_M13_HARTS_MAX		3UL
#define BE_M13_NAME_MAX			23UL
/* An entry's result, for the guards. */
#define BE_M13_NOT_MADE			0U
#define BE_M13_RESULT_MADE		1U
#define BE_M13_RESULT_FAULTED		2U

static char be_m13_text[BE_B0_LINE_CAPACITY];
static struct be_b0_line be_m13_line;
static unsigned long be_m13_console;
static unsigned long be_m13_failing;
static unsigned long be_m13_hart;
static unsigned long be_m13_accesses;
static unsigned long be_m13_faults;
static unsigned char be_m13_result[BE_M13_ENTRIES_MAX];
static unsigned long be_m13_value[BE_M13_ENTRIES_MAX];

static void begin(const char *words)
{
	be_b0_line_init(&be_m13_line, be_m13_text, sizeof(be_m13_text));
	be_b0_line_text(&be_m13_line, "BE_K3_M13: ");
	be_b0_line_text(&be_m13_line, words);
}

static void text(const char *words)
{
	be_b0_line_text(&be_m13_line, words);
}

/* " KEY=HEX" */
static void field(const char *key, unsigned long value)
{
	be_b0_line_text(&be_m13_line, " ");
	be_b0_line_text(&be_m13_line, key);
	be_b0_line_text(&be_m13_line, "=");
	be_b0_line_hex(&be_m13_line, value);
}

/* One character, a digit or a letter of the grammar's. */
static void character(char value)
{
	char one[2];

	one[0] = value;
	one[1] = '\0';
	be_b0_line_text(&be_m13_line, one);
}

/* The line, then a newline, a byte at a time. A line cannot overflow the
 * builder (the longest is 119 characters); one that did is not printed. */
static void emit(void)
{
	unsigned long index;

	if (be_m13_console == 0UL || be_m13_line.overflow != 0UL)
		return;
	for (index = 0UL; index < be_m13_line.length; ++index)
		(void)be_m13_putc((unsigned char)be_m13_text[index]);
	(void)be_m13_putc('\n');
}

static unsigned long probe_extension(unsigned long extension)
{
	struct be_m13_ret probe;

	probe = be_m13_sbi_base(SBI_BASE_PROBE_EXTENSION, extension);
	return probe.status == 0L && probe.value != 0UL ? 1UL : 0UL;
}

static void __attribute__((noreturn)) table_fail(unsigned long index)
{
	begin("FAIL table");
	field("index", index);
	emit();
	be_m13_srst();
}

static unsigned long table_count(void)
{
	return ((unsigned long)be_m13_table_end - (unsigned long)be_m13_table)
	       >> BE_M13_ENTRY_SHIFT;
}

static int name_char(char value)
{
	return (value >= 'A' && value <= 'Z') ||
	       (value >= 'a' && value <= 'z') ||
	       (value >= '0' && value <= '9') ||
	       value == '_' || value == '.' || value == '(' || value == ')' ||
	       value == '[' || value == ']';
}

/* Entry INDEX's probe and name are of the grammar: P1 to P7; a name of 1
 * to 23 characters of the name form, NUL-padded to its 32 bytes. */
static void check_entry(unsigned long index)
{
	const struct be_m13_entry *entry = &be_m13_table[index];
	unsigned long length = 0UL;
	unsigned long position;

	if (entry->probe < 1U || entry->probe > 7U)
		table_fail(index);
	while (length < BE_M13_NAME_SIZE && entry->name[length] != '\0')
		length += 1UL;
	if (length == 0UL || length > BE_M13_NAME_MAX)
		table_fail(index);
	for (position = 0UL; position < BE_M13_NAME_SIZE; ++position) {
		if (position < length ? !name_char(entry->name[position])
				      : entry->name[position] != '\0')
			table_fail(index);
	}
}

/* "Pn NAME " */
static void begin_entry(const struct be_m13_entry *entry)
{
	begin("P");
	character((char)('0' + entry->probe));
	text(" ");
	text(entry->name);
	text(" ");
}

/* " a=HEX w=N" */
static void where(const struct be_m13_entry *entry)
{
	field("a", entry->address);
	text(" w=");
	character((char)('0' + entry->width));
}

/* Entry INDEX, a read or a write, made by be_m13_access and printed. */
static void make_access(unsigned long index)
{
	const struct be_m13_entry *entry = &be_m13_table[index];
	struct be_m13_ret made;

	if (entry->width != 4U && entry->width != 8U)
		table_fail(index);
	made = be_m13_access(index);
	if (made.status != BE_M13_MADE && made.status != BE_M13_FAULTED)
		table_fail(index);
	begin_entry(entry);
	text(entry->op == BE_M13_OP_READ ? "read" : "write");
	where(entry);
	be_m13_accesses += 1UL;
	if (made.status == BE_M13_FAULTED) {
		be_m13_result[index] = BE_M13_RESULT_FAULTED;
		be_m13_faults += 1UL;
		field("fault", be_m13_fault[0]);
		field("tval", be_m13_fault[1]);
	} else {
		be_m13_result[index] = BE_M13_RESULT_MADE;
		be_m13_value[index] = made.value;
		field(entry->op == BE_M13_OP_READ ? "value" : "wrote",
		      made.value);
	}
	emit();
}

/* A guard: passes if its read was made, did not fault, and read the
 * guard's value. Its read is an earlier read of the same probe. */
static int guard(unsigned long index)
{
	const struct be_m13_entry *entry = &be_m13_table[index];
	const struct be_m13_entry *source;
	int pass;

	if (entry->ref >= index || entry->width != 0U)
		table_fail(index);
	source = &be_m13_table[entry->ref];
	if (source->op != BE_M13_OP_READ || source->probe != entry->probe)
		table_fail(index);
	pass = be_m13_result[entry->ref] == BE_M13_RESULT_MADE &&
	       be_m13_value[entry->ref] == entry->value;
	begin_entry(entry);
	text("guard");
	field("expect", entry->value);
	text(pass ? " pass" : " fail");
	emit();
	return pass;
}

/* The first entry after INDEX's probe. */
static unsigned long probe_end(unsigned long index, unsigned long count)
{
	unsigned char probe = be_m13_table[index].probe;

	while (index < count && be_m13_table[index].probe == probe)
		index += 1UL;
	return index;
}

#if BE_M13_HARTS

/* P1's lines for HART, from its slot: entries FIRST to END - 1 of HART. */
static void p1_lines(unsigned long hart, unsigned long first,
		     unsigned long end)
{
	unsigned long index;
	unsigned long reads = 0UL;

	for (index = first; index < end; ++index) {
		const struct be_m13_entry *entry = &be_m13_table[index];

		if (entry->hart != hart)
			continue;
		begin_entry(entry);
		if (entry->op == BE_M13_OP_CSRR) {
			if (reads >= 3UL)
				table_fail(index);
			text("csrr");
			where(entry);
			field("value", be_m13_slots[hart].read[reads]);
			reads += 1UL;
		} else {
			text("csrw");
			where(entry);
			field("wrote", entry->value);
		}
		be_m13_accesses += 1UL;
		emit();
	}
}

static void __attribute__((noreturn)) slot_trap(unsigned long hart)
{
	begin("FAIL trap");
	field("hart", hart);
	field("scause", be_m13_slots[hart].scause);
	field("sepc", be_m13_slots[hart].sepc);
	field("stval", be_m13_slots[hart].stval);
	emit();
	be_m13_srst();
}

/*
 * P1 (section 2.4 of the design): on the entry hart, then on each other
 * hart of 0 to 2, started by HSM in increasing order; then, in hart order,
 * an HSM line for each started hart and P1's lines for each hart that
 * reported. Returns the first entry after P1's.
 */
static unsigned long p1_block(unsigned long first, unsigned long count)
{
	struct be_m13_ret started[BE_M13_HARTS_MAX];
	unsigned long end = first;
	unsigned long hart;

	while (end < count && (be_m13_table[end].op == BE_M13_OP_CSRR ||
			       be_m13_table[end].op == BE_M13_OP_CSRW)) {
		const struct be_m13_entry *entry = &be_m13_table[end];

		if (entry->probe != 1U || entry->hart >= BE_M13_HARTS_MAX ||
		    entry->width != 8U ||
		    entry->address != BE_M13_CSR_HGEIE)
			table_fail(end);
		end += 1UL;
	}
	be_m13_p1(be_m13_hart);
	for (hart = 0UL; hart < BE_M13_HARTS_MAX; ++hart) {
		started[hart].status = 0L;
		started[hart].value = BE_M13_DONE;
		if (hart != be_m13_hart)
			started[hart] = be_m13_hart_run(hart);
	}
	for (hart = 0UL; hart < BE_M13_HARTS_MAX; ++hart) {
		if (hart != be_m13_hart) {
			begin("HSM");
			field("hart", hart);
			field("error", (unsigned long)started[hart].status);
			if (started[hart].status != 0L)
				text(" state=not-started");
			else if (started[hart].value == BE_M13_DONE)
				text(" state=done");
			else if (started[hart].value == BE_M13_REFUSED)
				text(" state=refused");
			else if (started[hart].value == BE_M13_TRAPPED)
				text(" state=trapped");
			else
				text(" state=timeout");
			emit();
			if (started[hart].status != 0L)
				continue;
			if (started[hart].value == BE_M13_REFUSED) {
				begin("FAIL hart");
				field("hart", hart);
				field("a0", be_m13_slots[hart].a0);
				emit();
				be_m13_srst();
			}
			if (started[hart].value == BE_M13_TRAPPED)
				slot_trap(hart);
			if (started[hart].value != BE_M13_DONE)
				continue;
		}
		p1_lines(hart, first, end);
	}
	return end;
}

#endif

static void run(void)
{
	unsigned long count = table_count();
	unsigned long index = 0UL;

	if (count > BE_M13_ENTRIES_MAX)
		table_fail(BE_M13_ENTRIES_MAX);
	while (index < count) {
		const struct be_m13_entry *entry = &be_m13_table[index];

		check_entry(index);
		if (entry->op == BE_M13_OP_READ ||
		    entry->op == BE_M13_OP_WRITE) {
			make_access(index);
			index += 1UL;
		} else if (entry->op == BE_M13_OP_GUARD_END) {
			if (guard(index))
				index += 1UL;
			else
				index = probe_end(index, count);
		} else if (entry->op == BE_M13_OP_GUARD_ELSE) {
			unsigned long next = index + 1UL;

			if (guard(index)) {
				index += 2UL;
				continue;
			}
			if (next >= count)
				table_fail(index);
			check_entry(next);
			if (be_m13_table[next].op != BE_M13_OP_WRITE ||
			    be_m13_table[next].probe != entry->probe)
				table_fail(next);
			make_access(next);
			index = probe_end(next, count);
#if BE_M13_HARTS
		} else if (entry->op == BE_M13_OP_CSRR ||
			   entry->op == BE_M13_OP_CSRW) {
			if (index != 0UL)
				table_fail(index);
			index = p1_block(index, count);
#endif
		} else {
			table_fail(index);
		}
	}
}

void be_m13_main(unsigned long hart, unsigned long fdt, unsigned long base)
{
	struct be_m13_ret spec;
	struct be_m13_ret impl;
	struct be_m13_ret impl_version;
	unsigned long srst;
	unsigned long hsm;
	unsigned long satp;

	be_m13_hart = hart;
	spec = be_m13_sbi_base(SBI_BASE_GET_SPEC_VERSION, 0UL);
	if (probe_extension(SBI_EXT_DBCN) == 0UL)
		be_m13_srst();
	be_m13_console = 1UL;
	impl = be_m13_sbi_base(SBI_BASE_GET_IMPL_ID, 0UL);
	impl_version = be_m13_sbi_base(SBI_BASE_GET_IMPL_VERSION, 0UL);
	srst = probe_extension(SBI_EXT_SRST);
	hsm = probe_extension(SBI_EXT_HSM);
	satp = be_m13_read_satp();

	begin("ENTRY image=");
	character(be_m13_image);
	field("hart", hart);
	field("base", base);
	field("fdt", fdt);
	emit();
	begin("SBI");
	field("spec", spec.value);
	field("impl", impl.value);
	field("impl_version", impl_version.value);
	emit();
	begin("EXT dbcn=1 srst=");
	be_b0_line_flag(&be_m13_line, srst);
	text(" hsm=");
	be_b0_line_flag(&be_m13_line, hsm);
	field("satp", satp);
	emit();
	if (srst == 0UL || satp != 0UL || (BE_M13_HARTS && hsm == 0UL)) {
		begin("FAIL sbi srst=");
		be_b0_line_flag(&be_m13_line, srst);
		text(" hsm=");
		be_b0_line_flag(&be_m13_line, hsm);
		field("satp", satp);
		emit();
		be_m13_srst();
	}

	run();

	begin("END image=");
	character(be_m13_image);
	field("accesses", be_m13_accesses);
	field("faults", be_m13_faults);
	emit();
	be_m13_srst();
}

void be_m13_refuse(unsigned long hart)
{
	be_m13_failing = 1UL;
	if (probe_extension(SBI_EXT_DBCN) != 0UL) {
		be_m13_console = 1UL;
		begin("FAIL entry");
		field("hart", hart);
		emit();
	}
	be_m13_srst();
}

void be_m13_trap_fail(unsigned long scause, unsigned long sepc,
		      unsigned long stval)
{
	if (be_m13_failing != 0UL)
		be_m13_park();
	be_m13_failing = 1UL;
	begin("FAIL trap");
	field("hart", be_m13_hart);
	field("scause", scause);
	field("sepc", sepc);
	field("stval", stval);
	emit();
	be_m13_srst();
}
