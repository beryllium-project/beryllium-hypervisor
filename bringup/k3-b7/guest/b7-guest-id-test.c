// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host test of the K3 B7 init's guest-ID rule (guest/b7-guest-id.h;
 *          planning/k3-b7-plan.md, Guest software, Q6): the argv the kernel
 *          gives each guest's /init, every variant's argv, and each way an
 *          ID can be missing or malformed. Prints one line per failing case
 *          and a summary; exits 0 only if every case passes.
 * Trust:   test code; it runs on the build host, never in a guest.
 * Scope:   B7 only. guest.mk builds and runs it with the host GCC and Clang
 *          (guest-self-test) and requires identical output.
 */

#include <stdio.h>

#include "b7-guest-id.h"

#define MAX_ARGS 5

struct id_case {
	const char *name;
	int argc;
	char *argv[MAX_ARGS];
	int expected;
};

static const struct id_case cases[] = {
	{ "G0", 2, { "/init", "be.guest=0" }, 0 },
	{ "G1", 2, { "/init", "be.guest=1" }, 1 },
	{ "G1 init-exit", 2, { "/init-exit", "be.guest=1" }, 1 },
	{ "G0 rdcycle", 2, { "/init-rdcycle", "be.guest=0" }, 0 },
	{ "other arguments", 4, { "/init", "x", "be.guest=1", "y=z" }, 1 },
	{ "argv[0] is never read", 1, { "be.guest=0" }, B7_GUEST_ID_NONE },
	{ "no arguments", 1, { "/init" }, B7_GUEST_ID_NONE },
	{ "argc 0", 0, { "/init", "be.guest=0" }, B7_GUEST_ID_NONE },
	{ "another argument", 2, { "/init", "auto" }, B7_GUEST_ID_NONE },
	{ "empty value", 2, { "/init", "be.guest=" }, B7_GUEST_ID_NONE },
	{ "third guest", 2, { "/init", "be.guest=2" }, B7_GUEST_ID_NONE },
	{ "two digits", 2, { "/init", "be.guest=01" }, B7_GUEST_ID_NONE },
	{ "trailing text", 2, { "/init", "be.guest=0x" }, B7_GUEST_ID_NONE },
	{ "sign", 2, { "/init", "be.guest=-1" }, B7_GUEST_ID_NONE },
	{ "space", 2, { "/init", "be.guest= 0" }, B7_GUEST_ID_NONE },
	{ "letter", 2, { "/init", "be.guest=a" }, B7_GUEST_ID_NONE },
	{ "below '0'", 2, { "/init", "be.guest=/" }, B7_GUEST_ID_NONE },
	{ "no '='", 2, { "/init", "be.guest" }, B7_GUEST_ID_NONE },
	{ "prefix", 2, { "/init", "xbe.guest=0" }, B7_GUEST_ID_NONE },
	{ "other key", 2, { "/init", "be.guests=0" }, B7_GUEST_ID_NONE },
	{ "case", 2, { "/init", "BE.GUEST=0" }, B7_GUEST_ID_NONE },
	{ "two IDs", 3, { "/init", "be.guest=0", "be.guest=1" },
	  B7_GUEST_ID_NONE },
	{ "one ID twice", 3, { "/init", "be.guest=1", "be.guest=1" },
	  B7_GUEST_ID_NONE },
	{ "malformed then valid", 3, { "/init", "be.guest=9", "be.guest=0" },
	  B7_GUEST_ID_NONE },
	{ "valid then malformed", 3, { "/init", "be.guest=0", "be.guest=" },
	  B7_GUEST_ID_NONE },
	{ "null argument", 3, { "/init", 0, "be.guest=0" }, B7_GUEST_ID_NONE },
};

int main(void)
{
	unsigned long index;
	unsigned long failures = 0;
	unsigned long count = sizeof(cases) / sizeof(cases[0]);

	for (index = 0; index < count; ++index) {
		const struct id_case *test = &cases[index];
		int got = b7_guest_id(test->argc, test->argv);

		if (got != test->expected) {
			printf("BE_B7_GUEST_ID_TEST: FAIL %s: got %d, expected %d\n",
			       test->name, got, test->expected);
			++failures;
		}
	}
	if (b7_guest_id(2, 0) != B7_GUEST_ID_NONE) {
		printf("BE_B7_GUEST_ID_TEST: FAIL null argv\n");
		++failures;
	}
	printf("BE_B7_GUEST_ID_TEST: %s cases=%lu\n", failures ? "FAIL" : "PASS",
	       count + 1UL);
	return failures ? 1 : 0;
}
