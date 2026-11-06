/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: frozen R0 fixed-profile configuration accessors for the bounded
 *          single-hart Beryllium runtime. These declarations expose the
 *          eleven-resource Model 0.2 core projection so a host-side checker
 *          can trace every frozen constant to the accepted abstract model.
 * Trust:   non-authoritative reviewable input. R0 adds no privileged runtime
 *          code; these constants are checked offline, never installed.
 * Scope:   R0 freeze only. The full thirteen-resource runtime profile and its
 *          two R-X guest-code overlays live in arch/riscv/be/r0-layout.h and
 *          are deliberately outside this Model 0.2 core projection.
 */

#ifndef BE_R0_CONFIG_H
#define BE_R0_CONFIG_H

#include <be/manifest.h>

/*
 * Frozen guest-physical addresses shared with Model 0.2. The fixed VS-stage is
 * Bare, so guest-virtual and guest-physical addresses are equal for the fixed
 * fixtures; the plan does not generalize that identity.
 */
#define BE_R0_GPA_MANAGEMENT_PRIVATE	BE_U64_C(0x40000000)
#define BE_R0_GPA_PROTECTED_PRIVATE	BE_U64_C(0x40001000)
#define BE_R0_GPA_SHARED		BE_U64_C(0x40002000)

/*
 * Frozen physical bases of the eleven Model 0.2 core-projection resources. The
 * Beryllium image begins at BE_R0_PA_MONITOR_CODE, immediately above the
 * OpenSBI-reserved region [0x80000000, 0x80200000).
 */
#define BE_R0_PA_MONITOR_CODE		BE_U64_C(0x80200000)
#define BE_R0_PA_MONITOR_DATA		BE_U64_C(0x80208000)
#define BE_R0_PA_ROOT_POOL_MANAGEMENT	BE_U64_C(0x80214000)
#define BE_R0_PA_ROOT_POOL_PROTECTED	BE_U64_C(0x8021c000)
#define BE_R0_PA_STACK_MANAGEMENT	BE_U64_C(0x80225000)
#define BE_R0_PA_STACK_PROTECTED	BE_U64_C(0x80228000)
#define BE_R0_PA_SAVED_MANAGEMENT	BE_U64_C(0x8022b000)
#define BE_R0_PA_SAVED_PROTECTED	BE_U64_C(0x8022c000)
#define BE_R0_PA_PRIVATE_MANAGEMENT	BE_U64_C(0x8022e000)
#define BE_R0_PA_PRIVATE_PROTECTED	BE_U64_C(0x8022f000)
#define BE_R0_PA_SHARED			BE_U64_C(0x80230000)

/* Sizes of the eleven core-projection resources. */
#define BE_R0_SIZE_MONITOR_CODE		BE_U64_C(0x8000)
#define BE_R0_SIZE_MONITOR_DATA		BE_U64_C(0x8000)
#define BE_R0_SIZE_ROOT_POOL		BE_U64_C(0x8000)
#define BE_R0_SIZE_TRUSTED_STACK	BE_U64_C(0x2000)
#define BE_R0_SIZE_SAVED_STATE		BE_PAGE_SIZE
#define BE_R0_SIZE_PAGE			BE_PAGE_SIZE

/**
 * be_r0_core_inventory - frozen eleven-resource Model 0.2 core projection
 *
 * Return: immutable normalized platform inventory for the R0 core projection.
 */
const struct be_platform_inventory *be_r0_core_inventory(void);

/**
 * be_r0_core_proposal - frozen copied proposal for the R0 core projection
 *
 * Return: immutable non-authoritative proposal for the R0 core projection.
 */
const struct be_proposal *be_r0_core_proposal(void);

#endif
