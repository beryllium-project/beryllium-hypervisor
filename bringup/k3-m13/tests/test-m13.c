// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jmorris@namei.org>
 *
 * Purpose: the host test of m13.c: the program, linked with a real table
 *          (table-N.S, by the host's assembler) and stand-ins for head.S's
 *          and harts.S's routines, run once for each scenario in a child
 *          process, so that m13.c's statics start fresh. Each capture goes
 *          to DIR/NAME.log, its every line checked printable ASCII and at
 *          most 120 characters, and DIR/manifest.txt names it with the end
 *          that tests/check-capture.py --mode host must find.
 */
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include <sys/wait.h>
#include <unistd.h>

#include "m13.h"

#define VALUE 0
#define FAULT 1
#define TRAP 2
#define RUN_DONE { 0L, BE_M13_DONE }

struct outcome {
	int kind;
	unsigned long value;
};

struct scenario {
	const char *name;
	const char *end;
	unsigned long hart;
	int refuse;
	unsigned long dbcn, srst, hsm, satp;
	struct be_m13_ret run[3];
	struct outcome access[BE_M13_ENTRIES_MAX];
};

#if BE_M13_HARTS
static const struct scenario scenarios[] = {
	{ "qemu-like", "end", 1, 0, 1, 1, 1, 0, { RUN_DONE, RUN_DONE, RUN_DONE },
	  { [15] = { FAULT, 0 }, [16] = { FAULT, 0 } } },
	{ "board-pass", "end", 0, 0, 1, 1, 1, 0, { RUN_DONE, RUN_DONE, RUN_DONE },
	  { [15] = { VALUE, 0x80000004 }, [20] = { VALUE, 1 } } },
	{ "board-else", "end", 0, 0, 1, 1, 1, 0, { RUN_DONE, RUN_DONE, RUN_DONE },
	  { [15] = { VALUE, 0x80000004 } } },
	{ "board-guard-2", "end", 2, 0, 1, 1, 1, 0, { RUN_DONE, RUN_DONE, RUN_DONE },
	  { [15] = { VALUE, 0x80000004 }, [16] = { VALUE, 3 } } },
	{ "hart-timeout", "end", 0, 0, 1, 1, 1, 0,
	  { RUN_DONE, { 0L, BE_M13_STARTING }, { -3L, 0 } }, { { 0, 0 } } },
	{ "hart-refused", "fail-hart", 0, 0, 1, 1, 1, 0,
	  { RUN_DONE, { 0L, BE_M13_REFUSED }, RUN_DONE }, { { 0, 0 } } },
	{ "hart-trapped", "fail-trap", 0, 0, 1, 1, 1, 0,
	  { RUN_DONE, RUN_DONE, { 0L, BE_M13_TRAPPED } }, { { 0, 0 } } },
	{ "entry-hart-5", "fail-entry", 5, 1, 1, 1, 1, 0,
	  { RUN_DONE, RUN_DONE, RUN_DONE }, { { 0, 0 } } },
	{ "no-srst", "fail-sbi", 0, 0, 1, 0, 1, 0,
	  { RUN_DONE, RUN_DONE, RUN_DONE }, { { 0, 0 } } },
	{ "no-hsm", "fail-sbi", 0, 0, 1, 1, 0, 0,
	  { RUN_DONE, RUN_DONE, RUN_DONE }, { { 0, 0 } } },
	{ "satp", "fail-sbi", 0, 0, 1, 1, 1, 0x8000000000080000UL,
	  { RUN_DONE, RUN_DONE, RUN_DONE }, { { 0, 0 } } },
	{ "trap-p7", "fail-trap", 0, 0, 1, 1, 1, 0,
	  { RUN_DONE, RUN_DONE, RUN_DONE }, { [16] = { TRAP, 0 } } },
	{ "no-dbcn", "none", 0, 0, 0, 1, 1, 0,
	  { RUN_DONE, RUN_DONE, RUN_DONE }, { { 0, 0 } } },
};
#else
static const struct scenario scenarios[] = {
	{ "values", "end", 0, 0, 1, 1, 0, 0, { RUN_DONE, RUN_DONE, RUN_DONE },
	  { [0] = { VALUE, 0x1 }, [65] = { VALUE, 0x10 } } },
	{ "bars-fault", "end", 0, 0, 1, 1, 1, 0, { RUN_DONE, RUN_DONE, RUN_DONE },
	  { [63] = { FAULT, 0 }, [64] = { FAULT, 0 } } },
};
#endif

static const struct scenario *now;
static jmp_buf out;
static char console[16384];
static unsigned long length;
unsigned long be_m13_fault[2];
struct be_m13_slot be_m13_slots[4];

struct be_m13_ret be_m13_sbi_base(unsigned long fid, unsigned long arg)
{
	struct be_m13_ret ret = { 0L, 0UL };

	if (fid == 0UL)
		ret.value = 0x2000000UL;
	else if (fid == 1UL)
		ret.value = 1UL;
	else if (fid == 2UL)
		ret.value = 0x10006UL;
	else if (fid == 3UL)
		ret.value = arg == 0x4442434eUL ? now->dbcn :
			    arg == 0x53525354UL ? now->srst :
			    arg == 0x48534dUL ? now->hsm : 0UL;
	return ret;
}

long be_m13_putc(unsigned long byte)
{
	if (length < sizeof(console))
		console[length++] = (char)byte;
	return 0L;
}

void be_m13_srst(void)
{
	longjmp(out, 1);
}

void be_m13_park(void)
{
	longjmp(out, 2);
}

unsigned long be_m13_read_satp(void)
{
	return now->satp;
}

/* As head.S's be_m13_access refuses, faults, and reads, by the script. */
struct be_m13_ret be_m13_access(unsigned long index)
{
	unsigned long count = (unsigned long)(be_m13_table_end - be_m13_table);
	const struct be_m13_entry *entry = &be_m13_table[index];
	struct be_m13_ret ret = { BE_M13_REFUSED_INDEX, 0UL };

	if (index >= count || (entry->op != BE_M13_OP_READ &&
			       entry->op != BE_M13_OP_WRITE) ||
	    (entry->address & (entry->width - 1UL)) != 0UL ||
	    (entry->width != 4U && entry->width != 8U) ||
	    (entry->op == BE_M13_OP_WRITE && entry->width != 4U))
		return ret;
	if (now->access[index].kind == TRAP)
		be_m13_trap_fail(5UL, 0x102200400UL, entry->address);
	if (now->access[index].kind == FAULT) {
		be_m13_fault[0] = entry->op == BE_M13_OP_READ ? 5UL : 7UL;
		be_m13_fault[1] = entry->address;
		ret.status = BE_M13_FAULTED;
		return ret;
	}
	ret.status = BE_M13_MADE;
	ret.value = entry->op == BE_M13_OP_WRITE ? entry->value :
						   now->access[index].value;
	return ret;
}

void be_m13_p1(unsigned long hart)
{
	be_m13_slots[hart].read[0] = 0UL;
	be_m13_slots[hart].read[1] = 0xfeUL;
	be_m13_slots[hart].read[2] = 0UL;
}

/* As harts.S's be_m13_hart_run: a done hart has made P1; a refused one
 * saw a0 = 7; a trapped one took an illegal instruction. */
struct be_m13_ret be_m13_hart_run(unsigned long hart)
{
	if (now->run[hart].status == 0L && now->run[hart].value == BE_M13_DONE)
		be_m13_p1(hart);
	be_m13_slots[hart].a0 = 7UL;
	be_m13_slots[hart].scause = 2UL;
	be_m13_slots[hart].sepc = 0x102200800UL;
	be_m13_slots[hart].stval = 0UL;
	return now->run[hart];
}

static void run_program(const struct scenario *scenario)
{
	now = scenario;
	if (setjmp(out) == 0) {
		if (scenario->refuse)
			be_m13_refuse(scenario->hart);
		be_m13_main(scenario->hart, 0x2fbd5d000UL, 0x102200000UL);
	}
}

static int run_one(const struct scenario *scenario, const char *directory)
{
	char path[4096];
	FILE *file;
	unsigned long index;
	unsigned long column = 0UL;

	run_program(scenario);
	for (index = 0UL; index < length; ++index) {
		if (console[index] == '\n') {
			column = 0UL;
		} else if (console[index] < 0x20 || console[index] > 0x7e ||
			   ++column > 120UL) {
			fprintf(stderr, "%s: a line not printable or too long\n",
				scenario->name);
			return 1;
		}
	}
	if (snprintf(path, sizeof(path), "%s/%s.log", directory,
		     scenario->name) >= (int)sizeof(path))
		return 1;
	file = fopen(path, "wx");
	if (file == NULL || fwrite(console, 1, length, file) != length ||
	    fclose(file) != 0)
		return 1;
	return 0;
}

int main(int argc, char **argv)
{
	char path[4096];
	FILE *manifest;
	unsigned long index;
	unsigned long count = sizeof(scenarios) / sizeof(scenarios[0]);

	if (argc != 2 || snprintf(path, sizeof(path), "%s/manifest.txt",
				  argv[1]) >= (int)sizeof(path))
		return 2;
	manifest = fopen(path, "wx");
	if (manifest == NULL)
		return 1;
	for (index = 0UL; index < count; ++index) {
		int status = 0;
		pid_t child = fork();

		if (child == 0)
			_exit(run_one(&scenarios[index], argv[1]));
		if (child < 0 || waitpid(child, &status, 0) != child ||
		    !WIFEXITED(status) || WEXITSTATUS(status) != 0) {
			printf("BE_K3_M13_HOST: FAIL %s\n", scenarios[index].name);
			return 1;
		}
		fprintf(manifest, "%s %s\n", scenarios[index].name,
			scenarios[index].end);
	}
	if (fclose(manifest) != 0)
		return 1;
	printf("BE_K3_M13_HOST: PASS image=%d scenarios=%lu\n",
	       BE_M13_HARTS ? 1 : 2, count);
	return 0;
}
