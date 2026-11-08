/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * beryllium-cheri: the CHERI Linux guest's own CHERI faults, which te-poc's
 * two roles make after their line 02 (planning/cheri-enforcement-plan.md,
 * CE-3; guest/cheri/cheri-tests.c), and CE-4's tagged store, which the
 * cap-store image's writer makes after them. The purecap init's hook calls
 * them with its say(), which writes each formatted line whole.
 */
#ifndef MVP_CHERI_TESTS_H
#define MVP_CHERI_TESTS_H

/* The init's say(): one formatted line, written whole. */
typedef void mvp_cheri_print(const char *format, ...)
	__attribute__((format(printf, 1, 2)));

/* The tests, their lines through PRINT; the number of tests that failed. */
unsigned long mvp_cheri_tests(mvp_cheri_print *print);

/*
 * CE-4's store: in an init run as /init-cap-store, the capability-store
 * module loaded with GPA, its line through PRINT; 1 when it did not load.
 */
unsigned long mvp_cheri_store(mvp_cheri_print *print, unsigned long gpa);

#endif
