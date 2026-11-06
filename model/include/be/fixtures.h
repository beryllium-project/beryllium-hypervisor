/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

#ifndef BE_FIXTURES_H
#define BE_FIXTURES_H

#include <be/manifest.h>

/**
 * enum be_fixture_id - neutral Model 0.2 proposal instances
 * @BE_FIXTURE_INVALID: fail-closed sentinel
 * @BE_FIXTURE_SOURCE_A: canonical-order relation vocabulary
 * @BE_FIXTURE_SOURCE_B: reordered equivalent relation vocabulary
 * @BE_FIXTURE_COUNT: upper bound for range checks
 */
enum be_fixture_id {
	BE_FIXTURE_INVALID = 0,
	BE_FIXTURE_SOURCE_A,
	BE_FIXTURE_SOURCE_B,
	BE_FIXTURE_COUNT,
};

/**
 * be_fixture_inventory - return the immutable bounded platform inventory
 *
 * Return: fixed inventory shared by both proposal fixtures.
 */
const struct be_platform_inventory *be_fixture_inventory(void);

/**
 * be_fixture_proposal - look up one immutable neutral proposal fixture
 * @fixture: fixture identifier
 *
 * Return: proposal pointer, or NULL for an invalid identifier.
 */
const struct be_proposal *be_fixture_proposal(enum be_fixture_id fixture);

/**
 * be_fixture_name - stable report name for a fixture
 * @fixture: fixture identifier
 *
 * Return: constant name, or "invalid".
 */
const char *be_fixture_name(enum be_fixture_id fixture);

#endif
