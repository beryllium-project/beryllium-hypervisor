/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP guest init's guest-ID rule (planning/mvp-m0-plan.md,
 *          Guest software; B7's rule). Linux hands everything after "--" on
 *          its command line to init as arguments, so "-- be.guest=<g>" in a
 *          guest's bootargs reaches /init as argv[1]. The ID is the value
 *          of the one argument that starts "be.guest=", and that value must
 *          be exactly one digit below MVP_GUEST_IDS. No such argument, two
 *          of them, or any other value is malformed, which the init reports
 *          as RESULT fail.
 *          And its role rule (planning/mvp-m1-plan.md, Guest software and
 *          Scenarios and the harness): "be.role=writer" or "be.role=reader",
 *          "be.channel=<gpa>", and "be.deny=<access>@<gpa>[,<access>@<gpa>]",
 *          each at most once, <access> load or store. A GPA is "0x" and
 *          one to sixteen lower-case hex digits without a leading zero, as
 *          tools/gen-dts.py writes it; the channel's is a nonzero 4 KiB
 *          page, each denied access's a doubleword, and a store's in the
 *          channel page, the one page the init maps writable. None of the
 *          three is M0's init (MVP_ROLE_ABSENT); be.role or be.channel
 *          without the other, a repeated argument, more than
 *          MVP_DENY_CHANNEL_MAX accesses, or any other form is malformed,
 *          which the init also reports as RESULT fail. be.deny may be
 *          absent: no denial.
 *          And M2's roles (planning/mvp-m2-plan.md, Guest software, Q8 and
 *          Q9): "be.role=host" or "be.role=prot" with
 *          "be.pages=<request>,<response>,<secret>", exactly MVP_PAGES
 *          distinct nonzero 4 KiB page GPAs in this order, in place of
 *          be.channel, and be.deny with at most MVP_DENY_MAX accesses, a
 *          store's in the request or response page, the two pages the init
 *          maps writable. be.pages with M1's roles, be.channel with M2's,
 *          or be.pages without a role is malformed.
 * Trust:   untrusted guest user space. Pure C with no library call, so the
 *          nolibc init (guest/mvp-init.c) and its host test
 *          (guest/mvp-guest-id-test.c) share it.
 * Scope:   the MVP line.
 */

#ifndef MVP_GUEST_ID_H
#define MVP_GUEST_ID_H

/* G0 and G1 (src/mvp-layout.h: BE_MVP_DOMAINS), and the malformed result. */
#define MVP_GUEST_IDS		2
#define MVP_GUEST_ID_NONE	(-1)

/*
 * The guest ID in argv[1..argc-1], or MVP_GUEST_ID_NONE. argv[0], the
 * name the kernel ran, is never read.
 */
static inline int mvp_guest_id(int argc, char *const *argv)
{
	static const char key[] = "be.guest=";
	int id = MVP_GUEST_ID_NONE;
	int arg_index;

	if (argv == 0)
		return MVP_GUEST_ID_NONE;
	for (arg_index = 1; arg_index < argc; ++arg_index) {
		const char *arg = argv[arg_index];
		unsigned long length = 0;

		if (arg == 0)
			return MVP_GUEST_ID_NONE;
		while (key[length] != '\0' && arg[length] == key[length])
			++length;
		if (key[length] != '\0')
			continue;
		arg += length;
		if (id != MVP_GUEST_ID_NONE || arg[0] < '0' ||
		    arg[0] >= '0' + MVP_GUEST_IDS || arg[1] != '\0')
			return MVP_GUEST_ID_NONE;
		id = arg[0] - '0';
	}
	return id;
}

/* The roles, the accesses, and mvp_role_args()'s three results. */
#define MVP_ROLE_NONE		0
#define MVP_ROLE_WRITER		1
#define MVP_ROLE_READER		2
#define MVP_ROLE_HOST		3
#define MVP_ROLE_PROT		4
#define MVP_ACCESS_LOAD		1
#define MVP_ACCESS_STORE	2
#define MVP_ROLE_ABSENT		0
#define MVP_ROLE_VALID		1
#define MVP_ROLE_MALFORMED	(-1)
/* be.deny's form holds one or two accesses for M1's roles, four for M2's. */
#define MVP_DENY_CHANNEL_MAX	2UL
#define MVP_DENY_MAX		4UL
/*
 * be.pages names the request, response, and secret pages; the init maps
 * the first two read-write.
 */
#define MVP_PAGES		3UL
#define MVP_PAGES_WRITABLE	2UL
#define MVP_PAGE_BYTES		0x1000UL

struct mvp_denial {
	int access;
	unsigned long gpa;
};

/* M1's roles set channel, M2's pages and page[]. */
struct mvp_role {
	int role;
	unsigned long channel;
	unsigned long denials;
	struct mvp_denial deny[MVP_DENY_MAX];
	unsigned long pages;
	unsigned long page[MVP_PAGES];
};

/* The text after KEY when TEXT starts with it, else 0. */
static inline const char *mvp_after(const char *text, const char *key)
{
	while (*key != '\0' && *text == *key) {
		++text;
		++key;
	}
	return *key == '\0' ? text : 0;
}

/* Whether TEXT is exactly WORD. */
static inline int mvp_is(const char *text, const char *word)
{
	const char *rest = mvp_after(text, word);

	return rest != 0 && *rest == '\0';
}

/*
 * A GPA at TEXT ("0x", lower-case hex, no leading zero) into *VALUE; the
 * text after it, or 0.
 */
static inline const char *mvp_gpa(const char *text, unsigned long *value)
{
	unsigned long result = 0;
	int digits = 0;

	if (text[0] != '0' || text[1] != 'x')
		return 0;
	for (text += 2;; ++text) {
		unsigned long nibble;

		if (*text >= '0' && *text <= '9')
			nibble = (unsigned long)(*text - '0');
		else if (*text >= 'a' && *text <= 'f')
			nibble = (unsigned long)(*text - 'a' + 10);
		else
			break;
		if (++digits > 16 || (digits == 2 && result == 0))
			return 0;
		result = result << 4 | nibble;
	}
	if (digits == 0)
		return 0;
	*value = result;
	return text;
}

/*
 * be.pages's value at TEXT into ROLE: MVP_PAGES distinct nonzero 4 KiB page
 * GPAs, separated by commas, and nothing after them; 1, or 0 for any other
 * form.
 */
static inline int mvp_pages(const char *text, struct mvp_role *role)
{
	unsigned long index, other;

	for (index = 0; index < MVP_PAGES; ++index) {
		if (index != 0 && *text++ != ',')
			return 0;
		text = mvp_gpa(text, &role->page[index]);
		if (text == 0 || role->page[index] == 0 ||
		    role->page[index] % MVP_PAGE_BYTES != 0)
			return 0;
		for (other = 0; other < index; ++other)
			if (role->page[other] == role->page[index])
				return 0;
	}
	if (*text != '\0')
		return 0;
	role->pages = MVP_PAGES;
	return 1;
}

/*
 * Whether GPA is in a page the role's init maps read-write: M1's channel
 * page, or M2's request or response page.
 */
static inline int mvp_writable(const struct mvp_role *role, unsigned long gpa)
{
	unsigned long index;

	if (role->pages == 0)
		return gpa >= role->channel &&
		       gpa - role->channel < MVP_PAGE_BYTES;
	for (index = 0; index < MVP_PAGES_WRITABLE; ++index)
		if (gpa >= role->page[index] &&
		    gpa - role->page[index] < MVP_PAGE_BYTES)
			return 1;
	return 0;
}

/*
 * The role in argv[1..argc-1] into *ROLE: MVP_ROLE_ABSENT, MVP_ROLE_VALID,
 * or MVP_ROLE_MALFORMED. argv[0] is never read.
 */
static inline int mvp_role_args(int argc, char *const *argv,
				struct mvp_role *role)
{
	const char *kind = 0, *channel = 0, *pages = 0, *deny = 0, *rest;
	unsigned long limit;
	int arg_index;

	role->role = MVP_ROLE_NONE;
	role->channel = 0;
	role->denials = 0;
	role->pages = 0;
	if (argv == 0)
		return MVP_ROLE_MALFORMED;
	for (arg_index = 1; arg_index < argc; ++arg_index) {
		const char *arg = argv[arg_index];
		const char **slot;

		if (arg == 0)
			return MVP_ROLE_MALFORMED;
		if ((rest = mvp_after(arg, "be.role=")) != 0)
			slot = &kind;
		else if ((rest = mvp_after(arg, "be.channel=")) != 0)
			slot = &channel;
		else if ((rest = mvp_after(arg, "be.pages=")) != 0)
			slot = &pages;
		else if ((rest = mvp_after(arg, "be.deny=")) != 0)
			slot = &deny;
		else
			continue;
		if (*slot != 0)
			return MVP_ROLE_MALFORMED;
		*slot = rest;
	}
	if (kind == 0 && channel == 0 && pages == 0 && deny == 0)
		return MVP_ROLE_ABSENT;
	if (kind == 0)
		return MVP_ROLE_MALFORMED;
	if (mvp_is(kind, "writer"))
		role->role = MVP_ROLE_WRITER;
	else if (mvp_is(kind, "reader"))
		role->role = MVP_ROLE_READER;
	else if (mvp_is(kind, "host"))
		role->role = MVP_ROLE_HOST;
	else if (mvp_is(kind, "prot"))
		role->role = MVP_ROLE_PROT;
	else
		return MVP_ROLE_MALFORMED;
	if (role->role == MVP_ROLE_WRITER || role->role == MVP_ROLE_READER) {
		if (channel == 0 || pages != 0)
			return MVP_ROLE_MALFORMED;
		rest = mvp_gpa(channel, &role->channel);
		if (rest == 0 || *rest != '\0' || role->channel == 0 ||
		    role->channel % MVP_PAGE_BYTES != 0)
			return MVP_ROLE_MALFORMED;
		limit = MVP_DENY_CHANNEL_MAX;
	} else {
		if (pages == 0 || channel != 0 || !mvp_pages(pages, role))
			return MVP_ROLE_MALFORMED;
		limit = MVP_DENY_MAX;
	}
	for (rest = deny; rest != 0;) {
		struct mvp_denial *entry;
		const char *gpa;

		if (role->denials == limit)
			return MVP_ROLE_MALFORMED;
		entry = &role->deny[role->denials++];
		if ((gpa = mvp_after(rest, "load@")) != 0)
			entry->access = MVP_ACCESS_LOAD;
		else if ((gpa = mvp_after(rest, "store@")) != 0)
			entry->access = MVP_ACCESS_STORE;
		else
			return MVP_ROLE_MALFORMED;
		rest = mvp_gpa(gpa, &entry->gpa);
		if (rest == 0 || entry->gpa % 8UL != 0 ||
		    (entry->access == MVP_ACCESS_STORE &&
		     !mvp_writable(role, entry->gpa)))
			return MVP_ROLE_MALFORMED;
		if (*rest == '\0')
			rest = 0;
		else if (*rest++ != ',')
			return MVP_ROLE_MALFORMED;
	}
	return MVP_ROLE_VALID;
}

#endif /* MVP_GUEST_ID_H */
