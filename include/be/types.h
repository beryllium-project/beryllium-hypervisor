/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: restricted-C scalar and count types for the accepted Beryllium R1
 *          non-privileged mechanism.
 * Trust:   public runtime contract only. These typedefs describe bounded
 *          runtime state and grant no authority on their own.
 * Scope:   fixed single-hart R1 mechanism only.
 */

#ifndef BE_TYPES_H
#define BE_TYPES_H

/*
 * Restricted-C runtime scalar types.
 *
 * These names describe the bounded runtime contract, not host-model-only test
 * types. The accepted R1 mechanism is RV64-oriented and keeps all state in
 * fixed-width scalars and bounded arrays with no libc dependency.
 */
/** typedef be_u8 - unsigned 8-bit runtime scalar */
typedef unsigned char be_u8;

/** typedef be_u32 - unsigned 32-bit runtime scalar */
typedef unsigned int be_u32;

/** typedef be_u64 - unsigned 64-bit runtime scalar */
typedef unsigned long be_u64;

/** typedef be_size - bounded runtime array and count type */
typedef unsigned long be_size;

#define BE_U64_C(value)		value##UL
#define BE_ARRAY_SIZE(array)	(sizeof(array) / sizeof((array)[0]))

_Static_assert(sizeof(be_u8) == 1U, "be_u8 requires 8 bits");
_Static_assert(sizeof(be_u32) == 4U, "be_u32 requires 32 bits");
_Static_assert(sizeof(be_u64) == 8U, "be_u64 requires 64 bits");
_Static_assert(sizeof(be_size) == 8U, "be_size requires 64-bit counts");

#endif
