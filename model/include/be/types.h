/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 */

#ifndef BE_TYPES_H
#define BE_TYPES_H

/*
 * Fixed host-model scalar types.
 *
 * Model 0.2 is a host-side architecture model, not runtime code. Keeping the
 * core independent of libc and dynamically allocated state makes its bounds
 * and future restricted-C cut points explicit.
 */
/** typedef be_u8 - unsigned 8-bit scalar */
typedef unsigned char be_u8;

/** typedef be_u32 - unsigned 32-bit scalar */
typedef unsigned int be_u32;

/** typedef be_u64 - unsigned 64-bit LP64 scalar */
typedef unsigned long be_u64;

/** typedef be_size - bounded host-model array and count type */
typedef unsigned long be_size;

#define BE_U64_C(value) value##UL
#define BE_ARRAY_SIZE(array) (sizeof(array) / sizeof((array)[0]))

_Static_assert(sizeof(be_u8) == 1U, "be_u8 requires an 8-bit byte");
_Static_assert(sizeof(be_u32) == 4U, "be_u32 requires 32 bits");
_Static_assert(sizeof(be_u64) == 8U, "be_u64 requires LP64");

#endif
