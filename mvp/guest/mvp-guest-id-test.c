// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host test of the MVP init's guest-ID rule (guest/mvp-guest-id.h;
 *          planning/mvp-m0-plan.md, Guest software): the argv the kernel
 *          gives each guest's /init, every variant's argv, and each way an
 *          ID can be missing or malformed; and of its role rule
 *          (planning/mvp-m1-plan.md, Guest software): te-poc's two argv,
 *          M0's, and each way a role argument can be absent, repeated, or
 *          malformed, with the parsed role, channel, and denials; and of
 *          M2's roles (planning/mvp-m2-plan.md, Guest software): anchor's
 *          two argv and each way be.pages or an M2 role can be malformed,
 *          with the parsed pages. Prints one line per failing case and a
 *          summary; exits 0 only if every case passes.
 * Trust:   test code; it runs on the build host, never in a guest.
 * Scope:   the MVP line. guest.mk builds and runs it with the host GCC and
 *          Clang (guest-self-test) and requires identical output.
 */

#include <stdio.h>

#include "mvp-guest-id.h"

#define MAX_ARGS 7

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
	{ "argv[0] is never read", 1, { "be.guest=0" }, MVP_GUEST_ID_NONE },
	{ "no arguments", 1, { "/init" }, MVP_GUEST_ID_NONE },
	{ "argc 0", 0, { "/init", "be.guest=0" }, MVP_GUEST_ID_NONE },
	{ "another argument", 2, { "/init", "auto" }, MVP_GUEST_ID_NONE },
	{ "empty value", 2, { "/init", "be.guest=" }, MVP_GUEST_ID_NONE },
	{ "third guest", 2, { "/init", "be.guest=2" }, MVP_GUEST_ID_NONE },
	{ "two digits", 2, { "/init", "be.guest=01" }, MVP_GUEST_ID_NONE },
	{ "trailing text", 2, { "/init", "be.guest=0x" }, MVP_GUEST_ID_NONE },
	{ "sign", 2, { "/init", "be.guest=-1" }, MVP_GUEST_ID_NONE },
	{ "space", 2, { "/init", "be.guest= 0" }, MVP_GUEST_ID_NONE },
	{ "letter", 2, { "/init", "be.guest=a" }, MVP_GUEST_ID_NONE },
	{ "below '0'", 2, { "/init", "be.guest=/" }, MVP_GUEST_ID_NONE },
	{ "no '='", 2, { "/init", "be.guest" }, MVP_GUEST_ID_NONE },
	{ "prefix", 2, { "/init", "xbe.guest=0" }, MVP_GUEST_ID_NONE },
	{ "other key", 2, { "/init", "be.guests=0" }, MVP_GUEST_ID_NONE },
	{ "case", 2, { "/init", "BE.GUEST=0" }, MVP_GUEST_ID_NONE },
	{ "two IDs", 3, { "/init", "be.guest=0", "be.guest=1" },
	  MVP_GUEST_ID_NONE },
	{ "one ID twice", 3, { "/init", "be.guest=1", "be.guest=1" },
	  MVP_GUEST_ID_NONE },
	{ "malformed then valid", 3, { "/init", "be.guest=9", "be.guest=0" },
	  MVP_GUEST_ID_NONE },
	{ "valid then malformed", 3, { "/init", "be.guest=0", "be.guest=" },
	  MVP_GUEST_ID_NONE },
	{ "null argument", 3, { "/init", 0, "be.guest=0" }, MVP_GUEST_ID_NONE },
};

#define W "be.role=writer"
#define R "be.role=reader"
#define C "be.channel=0x84000000"
#define D0 "be.deny=load@0x84001000"
#define D1 "be.deny=store@0x84000ff8,load@0x90000000"
#define H "be.role=host"
#define P "be.role=prot"
#define PAGES "be.pages=0x84000000,0x84001000,0x84002000"
#define HOST_DENY "be.deny=store@0x84001ff8,load@0x84002000," \
	"load@0x114000000,load@0x102064000"
#define PROT_DENY "be.deny=store@0x84000ff8"
#define LOAD MVP_ACCESS_LOAD
#define STORE MVP_ACCESS_STORE
#define MALFORMED MVP_ROLE_MALFORMED
/*
 * M0's and M1's roles set no page; anchor's set three, as tools/gen-dts.py
 * writes them.
 */
#define NO_PAGES 0UL, { 0 }
#define ANCHOR_PAGES 3UL, { 0x84000000UL, 0x84001000UL, 0x84002000UL }

struct role_case {
	const char *name;
	int argc;
	char *argv[MAX_ARGS];
	int expected;
	struct mvp_role role;
};

static const struct role_case role_cases[] = {
	{ "te-poc G0", 5, { "/init", "be.guest=0", W, C, D0 }, MVP_ROLE_VALID,
	  { MVP_ROLE_WRITER, 0x84000000UL, 1, { { LOAD, 0x84001000UL } },
	    NO_PAGES } },
	{ "te-poc G1", 5, { "/init", "be.guest=1", R, C, D1 }, MVP_ROLE_VALID,
	  { MVP_ROLE_READER, 0x84000000UL, 2,
	    { { STORE, 0x84000ff8UL }, { LOAD, 0x90000000UL } }, NO_PAGES } },
	{ "any order, other arguments", 6,
	  { "/init", D0, "x=y", C, W, "be.guest=0" }, MVP_ROLE_VALID,
	  { MVP_ROLE_WRITER, 0x84000000UL, 1, { { LOAD, 0x84001000UL } },
	    NO_PAGES } },
	{ "no be.deny", 4, { "/init", "be.guest=0", W, C }, MVP_ROLE_VALID,
	  { MVP_ROLE_WRITER, 0x84000000UL, 0, { { 0, 0 } }, NO_PAGES } },
	{ "a store at the page's first word", 4,
	  { "/init", R, C, "be.deny=store@0x84000000" }, MVP_ROLE_VALID,
	  { MVP_ROLE_READER, 0x84000000UL, 1, { { STORE, 0x84000000UL } },
	    NO_PAGES } },
	{ "two loads", 4,
	  { "/init", R, C, "be.deny=load@0x84001000,load@0x90000000" },
	  MVP_ROLE_VALID, { MVP_ROLE_READER, 0x84000000UL, 2,
	    { { LOAD, 0x84001000UL }, { LOAD, 0x90000000UL } }, NO_PAGES } },
	{ "a load in the channel page", 4,
	  { "/init", R, C, "be.deny=load@0x84000ff8" }, MVP_ROLE_VALID,
	  { MVP_ROLE_READER, 0x84000000UL, 1, { { LOAD, 0x84000ff8UL } },
	    NO_PAGES } },
	{ "sixteen digits", 4,
	  { "/init", W, "be.channel=0xfffffffffffff000",
	    "be.deny=store@0xfffffffffffffff8" }, MVP_ROLE_VALID,
	  { MVP_ROLE_WRITER, 0xfffffffffffff000UL, 1,
	    { { STORE, 0xfffffffffffffff8UL } }, NO_PAGES } },
	{ "M0's G0", 2, { "/init", "be.guest=0" }, MVP_ROLE_ABSENT, { 0, 0, 0,
	  { { 0, 0 } }, NO_PAGES } },
	{ "no arguments", 1, { "/init" }, MVP_ROLE_ABSENT, { 0, 0, 0,
	  { { 0, 0 } }, NO_PAGES } },
	{ "argv[0] is never read", 1, { W }, MVP_ROLE_ABSENT, { 0, 0, 0,
	  { { 0, 0 } }, NO_PAGES } },
	{ "other keys", 5, { "/init", "be.roles=writer",
	  "be.channels=0x84000000", "be.denial=load@0x84001000", "be.role" },
	  MVP_ROLE_ABSENT, { 0, 0, 0, { { 0, 0 } }, NO_PAGES } },
	{ "a role without a channel", 2, { "/init", W }, MALFORMED, { 0 } },
	{ "a channel without a role", 2, { "/init", C }, MALFORMED, { 0 } },
	{ "be.deny alone", 2, { "/init", D0 }, MALFORMED, { 0 } },
	{ "be.deny without a channel", 3, { "/init", W, D0 }, MALFORMED, { 0 } },
	{ "another role", 3, { "/init", "be.role=owner", C }, MALFORMED, { 0 } },
	{ "the role's case", 3, { "/init", "be.role=Writer", C }, MALFORMED,
	  { 0 } },
	{ "text after the role", 3, { "/init", "be.role=writer,", C }, MALFORMED,
	  { 0 } },
	{ "an empty role", 3, { "/init", "be.role=", C }, MALFORMED, { 0 } },
	{ "two roles", 4, { "/init", W, W, C }, MALFORMED, { 0 } },
	{ "two channels", 4, { "/init", W, C, C }, MALFORMED, { 0 } },
	{ "two be.deny", 5, { "/init", W, C, D0, D0 }, MALFORMED, { 0 } },
	{ "a channel without 0x", 3, { "/init", W, "be.channel=84000000" },
	  MALFORMED, { 0 } },
	{ "0X", 3, { "/init", W, "be.channel=0X84000000" }, MALFORMED, { 0 } },
	{ "a leading zero", 3, { "/init", W, "be.channel=0x084000000" },
	  MALFORMED, { 0 } },
	{ "an upper-case digit", 3, { "/init", W, "be.channel=0x8400F000" },
	  MALFORMED, { 0 } },
	{ "a channel not page-aligned", 3, { "/init", W,
	  "be.channel=0x84000800" }, MALFORMED, { 0 } },
	{ "channel zero", 3, { "/init", W, "be.channel=0x0" }, MALFORMED,
	  { 0 } },
	{ "seventeen digits", 3, { "/init", W,
	  "be.channel=0x10000000000000000" }, MALFORMED, { 0 } },
	{ "no digit", 3, { "/init", W, "be.channel=0x" }, MALFORMED, { 0 } },
	{ "text after the channel", 3, { "/init", W, "be.channel=0x84000000x" },
	  MALFORMED, { 0 } },
	{ "an empty be.deny", 4, { "/init", W, C, "be.deny=" }, MALFORMED,
	  { 0 } },
	{ "a fetch", 4, { "/init", W, C, "be.deny=fetch@0x84001000" },
	  MALFORMED, { 0 } },
	{ "an access without a GPA", 4, { "/init", W, C, "be.deny=load@" },
	  MALFORMED, { 0 } },
	{ "an access without @", 4, { "/init", W, C, "be.deny=load0x84001000" },
	  MALFORMED, { 0 } },
	{ "a GPA not doubleword-aligned", 4, { "/init", W, C,
	  "be.deny=load@0x84001004" }, MALFORMED, { 0 } },
	{ "a GPA with a leading zero", 4, { "/init", W, C,
	  "be.deny=load@0x084001000" }, MALFORMED, { 0 } },
	{ "three accesses", 4, { "/init", R, C,
	  "be.deny=load@0x84001000,load@0x84001008,load@0x84001010" },
	  MALFORMED, { 0 } },
	{ "a trailing comma", 4, { "/init", W, C, "be.deny=load@0x84001000," },
	  MALFORMED, { 0 } },
	{ "a leading comma", 4, { "/init", W, C, "be.deny=,load@0x84001000" },
	  MALFORMED, { 0 } },
	{ "another separator", 4, { "/init", R, C,
	  "be.deny=load@0x84001000;load@0x90000000" }, MALFORMED, { 0 } },
	{ "a store outside the channel page", 4, { "/init", R, C,
	  "be.deny=store@0x90000000" }, MALFORMED, { 0 } },
	{ "a store in the next page", 4, { "/init", R, C,
	  "be.deny=store@0x84001000" }, MALFORMED, { 0 } },
	{ "a store below the page", 4, { "/init", R, C,
	  "be.deny=store@0x83fffff8" }, MALFORMED, { 0 } },
	{ "a null argument", 4, { "/init", 0, W, C }, MALFORMED, { 0 } },
	{ "anchor G0", 5, { "/init", "be.guest=0", H, PAGES, HOST_DENY },
	  MVP_ROLE_VALID, { MVP_ROLE_HOST, 0, 4,
	    { { STORE, 0x84001ff8UL }, { LOAD, 0x84002000UL },
	      { LOAD, 0x114000000UL }, { LOAD, 0x102064000UL } },
	    ANCHOR_PAGES } },
	{ "anchor G1", 5, { "/init", "be.guest=1", P, PAGES, PROT_DENY },
	  MVP_ROLE_VALID, { MVP_ROLE_PROT, 0, 1, { { STORE, 0x84000ff8UL } },
	    ANCHOR_PAGES } },
	{ "a host without be.deny", 3, { "/init", PAGES, H }, MVP_ROLE_VALID,
	  { MVP_ROLE_HOST, 0, 0, { { 0, 0 } }, ANCHOR_PAGES } },
	{ "a store in the response page", 4,
	  { "/init", P, PAGES, "be.deny=store@0x84001000,load@0x84003000" },
	  MVP_ROLE_VALID, { MVP_ROLE_PROT, 0, 2,
	    { { STORE, 0x84001000UL }, { LOAD, 0x84003000UL } },
	    ANCHOR_PAGES } },
	{ "pages not ascending", 4,
	  { "/init", H, "be.pages=0x84002000,0x90000000,0x84000000",
	    "be.deny=store@0x90000ff8" }, MVP_ROLE_VALID,
	  { MVP_ROLE_HOST, 0, 1, { { STORE, 0x90000ff8UL } },
	    3UL, { 0x84002000UL, 0x90000000UL, 0x84000000UL } } },
	{ "a host without pages", 2, { "/init", H }, MALFORMED, { 0 } },
	{ "a prot with a deny, no pages", 3, { "/init", P, PROT_DENY },
	  MALFORMED, { 0 } },
	{ "be.pages alone", 2, { "/init", PAGES }, MALFORMED, { 0 } },
	{ "be.pages without a role", 3, { "/init", PAGES, PROT_DENY },
	  MALFORMED, { 0 } },
	{ "a host with a channel", 4, { "/init", H, PAGES, C }, MALFORMED,
	  { 0 } },
	{ "a host with only a channel", 3, { "/init", H, C }, MALFORMED,
	  { 0 } },
	{ "a writer with pages", 4, { "/init", W, C, PAGES }, MALFORMED,
	  { 0 } },
	{ "a reader with only pages", 3, { "/init", R, PAGES }, MALFORMED,
	  { 0 } },
	{ "the host's case", 3, { "/init", "be.role=Host", PAGES }, MALFORMED,
	  { 0 } },
	{ "two be.pages", 4, { "/init", P, PAGES, PAGES }, MALFORMED, { 0 } },
	{ "two pages", 3, { "/init", H, "be.pages=0x84000000,0x84001000" },
	  MALFORMED, { 0 } },
	{ "four pages", 3, { "/init", H,
	  "be.pages=0x84000000,0x84001000,0x84002000,0x84003000" }, MALFORMED,
	  { 0 } },
	{ "an empty page list", 3, { "/init", H, "be.pages=" }, MALFORMED,
	  { 0 } },
	{ "a page not page-aligned", 3, { "/init", H,
	  "be.pages=0x84000000,0x84001008,0x84002000" }, MALFORMED, { 0 } },
	{ "page zero", 3, { "/init", H, "be.pages=0x0,0x84001000,0x84002000" },
	  MALFORMED, { 0 } },
	{ "a repeated page", 3, { "/init", P,
	  "be.pages=0x84000000,0x84001000,0x84000000" }, MALFORMED, { 0 } },
	{ "a trailing comma in be.pages", 3, { "/init", H,
	  "be.pages=0x84000000,0x84001000,0x84002000," }, MALFORMED, { 0 } },
	{ "another page separator", 3, { "/init", H,
	  "be.pages=0x84000000;0x84001000;0x84002000" }, MALFORMED, { 0 } },
	{ "a page with a leading zero", 3, { "/init", H,
	  "be.pages=0x084000000,0x84001000,0x84002000" }, MALFORMED, { 0 } },
	{ "five accesses", 4, { "/init", H, PAGES,
	  "be.deny=store@0x84001ff8,load@0x84002000,load@0x114000000,"
	  "load@0x102064000,load@0x90000000" }, MALFORMED, { 0 } },
	{ "a store in the secret page", 4, { "/init", P, PAGES,
	  "be.deny=store@0x84002000" }, MALFORMED, { 0 } },
	{ "a store outside the pages", 4, { "/init", H, PAGES,
	  "be.deny=store@0x90000000" }, MALFORMED, { 0 } },
	{ "a store below the request page", 4, { "/init", H, PAGES,
	  "be.deny=store@0x83fffff8" }, MALFORMED, { 0 } },
	{ "a GPA not doubleword-aligned in M2's", 4, { "/init", H, PAGES,
	  "be.deny=load@0x84002004" }, MALFORMED, { 0 } },
};

/*
 * Whether ROLE is the expected result: the role, channel, denials, and
 * pages.
 */
static int same_role(const struct mvp_role *got, const struct mvp_role *want)
{
	unsigned long index;

	if (got->role != want->role || got->channel != want->channel ||
	    got->denials != want->denials || got->pages != want->pages)
		return 0;
	for (index = 0; index < got->denials; ++index)
		if (got->deny[index].access != want->deny[index].access ||
		    got->deny[index].gpa != want->deny[index].gpa)
			return 0;
	for (index = 0; index < got->pages; ++index)
		if (got->page[index] != want->page[index])
			return 0;
	return 1;
}

int main(void)
{
	unsigned long index;
	unsigned long failures = 0;
	unsigned long count = sizeof(cases) / sizeof(cases[0]);
	unsigned long roles = sizeof(role_cases) / sizeof(role_cases[0]);
	struct mvp_role role;

	for (index = 0; index < count; ++index) {
		const struct id_case *test = &cases[index];
		int got = mvp_guest_id(test->argc, test->argv);

		if (got != test->expected) {
			printf("BE_MVP_GUEST_ID_TEST: FAIL %s: got %d, expected %d\n",
			       test->name, got, test->expected);
			++failures;
		}
	}
	if (mvp_guest_id(2, 0) != MVP_GUEST_ID_NONE) {
		printf("BE_MVP_GUEST_ID_TEST: FAIL null argv\n");
		++failures;
	}
	for (index = 0; index < roles; ++index) {
		const struct role_case *test = &role_cases[index];
		int got = mvp_role_args(test->argc, test->argv, &role);

		if (got != test->expected ||
		    (got != MVP_ROLE_MALFORMED && !same_role(&role, &test->role))) {
			printf("BE_MVP_GUEST_ID_TEST: FAIL role %s: got %d, "
			       "expected %d\n", test->name, got, test->expected);
			++failures;
		}
	}
	if (mvp_role_args(2, 0, &role) != MVP_ROLE_MALFORMED) {
		printf("BE_MVP_GUEST_ID_TEST: FAIL role null argv\n");
		++failures;
	}
	printf("BE_MVP_GUEST_ID_TEST: %s cases=%lu\n", failures ? "FAIL" : "PASS",
	       count + roles + 2UL);
	return failures ? 1 : 0;
}
