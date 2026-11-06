// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host unit test for the B0 bounded line builder, compiled from the
 *          same source file the freestanding image links.
 */
#include <stdio.h>
#include <string.h>

#include "b0-format.h"

static int failures;

static void expect_text(const char *name, const struct be_b0_line *line,
			const char *expected, unsigned long overflow)
{
	if (strcmp(line->text, expected) != 0 ||
	    line->length != (unsigned long)strlen(expected) ||
	    line->overflow != overflow) {
		printf("FAIL %s: got \"%s\" length=%lu overflow=%lu, "
		       "expected \"%s\" overflow=%lu\n", name, line->text,
		       line->length, line->overflow, expected, overflow);
		++failures;
		return;
	}
	printf("ok   %s\n", name);
}

static void test_hex(void)
{
	char storage[BE_B0_LINE_CAPACITY];
	struct be_b0_line line;

	be_b0_line_init(&line, storage, sizeof storage);
	be_b0_line_hex(&line, 0UL);
	expect_text("hex zero", &line, "0x0000000000000000", 0UL);

	be_b0_line_init(&line, storage, sizeof storage);
	be_b0_line_hex(&line, 0x102200000UL);
	expect_text("hex k3 base", &line, "0x0000000102200000", 0UL);

	be_b0_line_init(&line, storage, sizeof storage);
	be_b0_line_hex(&line, ~0UL);
	expect_text("hex all ones", &line, "0xffffffffffffffff", 0UL);
}

static void test_composition(void)
{
	char storage[BE_B0_LINE_CAPACITY];
	struct be_b0_line line;

	be_b0_line_init(&line, storage, sizeof storage);
	be_b0_line_text(&line, "BE_B0:03 EXT dbcn=1 srst=");
	be_b0_line_flag(&line, 7UL);
	be_b0_line_text(&line, " hsm=");
	be_b0_line_flag(&line, 0UL);
	be_b0_line_text(&line, "\n");
	expect_text("marker composition", &line,
		    "BE_B0:03 EXT dbcn=1 srst=1 hsm=0\n", 0UL);
}

static void test_bounds(void)
{
	char tiny[4];
	char exact[19];
	struct be_b0_line line;

	be_b0_line_init(&line, tiny, sizeof tiny);
	be_b0_line_text(&line, "abcdef");
	expect_text("truncates at capacity", &line, "abc", 1UL);

	be_b0_line_init(&line, exact, sizeof exact);
	be_b0_line_hex(&line, 0x1234UL);
	expect_text("hex fills exact capacity", &line, "0x0000000000001234",
		    0UL);

	be_b0_line_text(&line, "x");
	expect_text("append past exact capacity", &line,
		    "0x0000000000001234", 1UL);

	be_b0_line_init(&line, (char *)0, 0UL);
	be_b0_line_text(&line, "ignored");
	be_b0_line_hex(&line, 1UL);
	if (line.overflow != 1UL || line.length != 0UL) {
		printf("FAIL null storage is not inert\n");
		++failures;
	} else {
		printf("ok   null storage is inert\n");
	}

	be_b0_line_init(&line, tiny, sizeof tiny);
	be_b0_line_text(&line, (const char *)0);
	expect_text("null text marks overflow", &line, "", 1UL);
}

int main(void)
{
	test_hex();
	test_composition();
	test_bounds();
	if (failures != 0) {
		printf("BE_B0_FORMAT_TEST: FAIL (%d)\n", failures);
		return 1;
	}
	printf("BE_B0_FORMAT_TEST: PASS\n");
	return 0;
}
