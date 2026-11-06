/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the K3 B7 guest init's guest-ID rule (planning/k3-b7-plan.md,
 *          Guest software, Q6). Linux hands everything after "--" on its
 *          command line to init as arguments, so "-- be.guest=<g>" in a
 *          guest's bootargs reaches /init as argv[1]. The ID is the value
 *          of the one argument that starts "be.guest=", and that value must
 *          be exactly one digit below B7_GUEST_IDS. No such argument, two
 *          of them, or any other value is malformed, which the init reports
 *          as RESULT fail.
 * Trust:   untrusted guest user space. Pure C with no library call, so the
 *          nolibc init (guest/b7-init.c) and its host test
 *          (guest/b7-guest-id-test.c) share it.
 * Scope:   B7 only.
 */

#ifndef B7_GUEST_ID_H
#define B7_GUEST_ID_H

/* G0 and G1 (src/b7-layout.h: BE_B7_GUESTS), and the malformed result. */
#define B7_GUEST_IDS		2
#define B7_GUEST_ID_NONE	(-1)

/*
 * The guest ID in argv[1..argc-1], or B7_GUEST_ID_NONE. argv[0], the
 * name the kernel ran, is never read.
 */
static inline int b7_guest_id(int argc, char *const *argv)
{
	static const char key[] = "be.guest=";
	int id = B7_GUEST_ID_NONE;
	int arg_index;

	if (argv == 0)
		return B7_GUEST_ID_NONE;
	for (arg_index = 1; arg_index < argc; ++arg_index) {
		const char *arg = argv[arg_index];
		unsigned long length = 0;

		if (arg == 0)
			return B7_GUEST_ID_NONE;
		while (key[length] != '\0' && arg[length] == key[length])
			++length;
		if (key[length] != '\0')
			continue;
		arg += length;
		if (id != B7_GUEST_ID_NONE || arg[0] < '0' ||
		    arg[0] >= '0' + B7_GUEST_IDS || arg[1] != '\0')
			return B7_GUEST_ID_NONE;
		id = arg[0] - '0';
	}
	return id;
}

#endif /* B7_GUEST_ID_H */
