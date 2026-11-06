/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the scalar types src/mvp-sha256.{h,c} take
 *          (planning/mvp-m2-plan.md, Q6), for the guest init, which
 *          compiles that SHA-256 against the pinned tree's nolibc and UAPI
 *          headers alone (tools/build-guest.sh), while the monitor's
 *          <be/types.h> is the accepted include/be/types.h in its generated
 *          port: the same three typedefs under the same guard, so that the
 *          two can never both define them.
 * Trust:   untrusted guest user space.
 * Scope:   the MVP line (M2); tools/build-guest.sh puts guest/ on the
 *          init's include path.
 */

#ifndef BE_TYPES_H
#define BE_TYPES_H

typedef unsigned char be_u8;
typedef unsigned int be_u32;
typedef unsigned long be_u64;

_Static_assert(sizeof(be_u8) == 1U, "be_u8 requires 8 bits");
_Static_assert(sizeof(be_u32) == 4U, "be_u32 requires 32 bits");
_Static_assert(sizeof(be_u64) == 8U, "be_u64 requires 64 bits");

#endif /* BE_TYPES_H */
