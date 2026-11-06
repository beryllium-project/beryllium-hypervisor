/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: frozen R1 full-profile configuration accessors for the bounded
 *          single-hart Beryllium runtime. These declarations expose the
 *          thirteen-resource review fixture so a host-side checker can trace
 *          every frozen constant to the accepted R0 layout.
 * Trust:   non-authoritative reviewable input. R1 adds no privileged runtime
 *          code; these constants are copied and checked offline.
 * Scope:   R1 fixture only. The full thirteen-resource runtime profile is
 *          reviewable data, not enforcement, and remains separate from any
 *          later mechanism implementation.
 */

#ifndef BE_R1_CONFIG_H
#define BE_R1_CONFIG_H

#include <be/manifest.h>

/**
 * be_r1_inventory - frozen thirteen-resource fixed-profile inventory
 *
 * Return: immutable normalized platform inventory for the R1 fixture.
 */
const struct be_platform_inventory *be_r1_inventory(void);

/**
 * be_r1_proposal - frozen copied proposal for the fixed R1 profile
 *
 * Return: immutable non-authoritative proposal for the R1 fixture.
 */
const struct be_proposal *be_r1_proposal(void);

#endif
