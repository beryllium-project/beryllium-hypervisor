/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: frozen R0 HS-to-M SBI allowlist and error matrix for the fixed
 *          single-hart Beryllium runtime, as machine-checkable declarations.
 * Trust:   reviewable non-authoritative declaration. R0 issues no SBI call and
 *          adds no privileged code; the authoritative contract with argument,
 *          return, and error handling lives in
 *          planning/single-hart-runtime-r0-freeze.md.
 * Scope:   R0 freeze only. Exactly three extensions are allowed: SBI Base,
 *          Debug Console (DBCN), and System Reset (SRST). No legacy console or
 *          shutdown, no guest-facing SBI, and no timer, IPI, remote-fence,
 *          hart-state, PMU, suspend, or vendor extension.
 */

#ifndef BE_R0_SBI_H
#define BE_R0_SBI_H

#include <be/manifest.h>

/* Allowed extension identifiers. */
#define BE_R0_SBI_EID_BASE	BE_U64_C(0x10)
#define BE_R0_SBI_EID_DBCN	BE_U64_C(0x4442434e)
#define BE_R0_SBI_EID_SRST	BE_U64_C(0x53525354)

/* Allowed function identifiers. */
#define BE_R0_SBI_BASE_FID_GET_SPEC_VERSION	0U
#define BE_R0_SBI_BASE_FID_PROBE_EXTENSION	3U
#define BE_R0_SBI_DBCN_FID_WRITE		0U
#define BE_R0_SBI_SRST_FID_SYSTEM_RESET		0U

/* Frozen SRST arguments: shutdown, no reason. */
#define BE_R0_SBI_SRST_TYPE_SHUTDOWN		0U
#define BE_R0_SBI_SRST_REASON_NONE		0U

/*
 * Frozen bounded diagnostic write loop. The fixed diagnostic strings are short
 * and constant; a compliant non-blocking console drains within this cap. The
 * cap is a single constant, never data dependent. Exhaustion makes diagnostics
 * unavailable and enters the fixed failure path; it never advances progress or
 * produces a success-shaped result.
 */
#define BE_R0_SBI_DBCN_MAX_ITERATIONS		256U

/**
 * enum be_r0_sbi_error - standard SBI return errors handled deterministically
 */
enum be_r0_sbi_error {
	BE_R0_SBI_SUCCESS = 0,
	BE_R0_SBI_ERR_FAILED = -1,
	BE_R0_SBI_ERR_NOT_SUPPORTED = -2,
	BE_R0_SBI_ERR_INVALID_PARAM = -3,
	BE_R0_SBI_ERR_DENIED = -4,
	BE_R0_SBI_ERR_INVALID_ADDRESS = -5,
};

/**
 * enum be_r0_sbi_disposition - deterministic R0 handling of one SBI outcome
 * @BE_R0_SBI_ACCUMULATE: SUCCESS with 0..N bytes; advance and continue bounded
 * @BE_R0_SBI_TERMINAL: enter the fixed terminal failure path; never retry
 * @BE_R0_SBI_FAILS_CLOSED: required behavior missing; the profile fails closed
 * @BE_R0_SBI_TERMINUS: expected non-returning success (SRST shutdown)
 */
enum be_r0_sbi_disposition {
	BE_R0_SBI_ACCUMULATE = 0,
	BE_R0_SBI_TERMINAL,
	BE_R0_SBI_FAILS_CLOSED,
	BE_R0_SBI_TERMINUS,
};

/**
 * struct be_r0_sbi_call - one allowlisted SBI call
 * @name: reporting name
 * @eid: extension identifier
 * @fid: function identifier
 */
struct be_r0_sbi_call {
	const char *name;
	be_u64 eid;
	be_u32 fid;
};

/**
 * struct be_r0_sbi_outcome - one deterministic SBI return disposition
 * @name: reporting name
 * @error: standard SBI error value
 * @disposition: deterministic R0 handling
 */
struct be_r0_sbi_outcome {
	const char *name;
	enum be_r0_sbi_error error;
	enum be_r0_sbi_disposition disposition;
};

static const struct be_r0_sbi_call be_r0_sbi_calls[] = {
	{ "base-get-spec-version", BE_R0_SBI_EID_BASE,
	  BE_R0_SBI_BASE_FID_GET_SPEC_VERSION },
	{ "base-probe-extension", BE_R0_SBI_EID_BASE,
	  BE_R0_SBI_BASE_FID_PROBE_EXTENSION },
	{ "dbcn-console-write", BE_R0_SBI_EID_DBCN,
	  BE_R0_SBI_DBCN_FID_WRITE },
	{ "srst-system-reset", BE_R0_SBI_EID_SRST,
	  BE_R0_SBI_SRST_FID_SYSTEM_RESET },
};

static const struct be_r0_sbi_outcome be_r0_sbi_outcomes[] = {
	{ "dbcn-success-partial-or-zero", BE_R0_SBI_SUCCESS,
	  BE_R0_SBI_ACCUMULATE },
	{ "dbcn-invalid-param", BE_R0_SBI_ERR_INVALID_PARAM,
	  BE_R0_SBI_TERMINAL },
	{ "dbcn-invalid-address", BE_R0_SBI_ERR_INVALID_ADDRESS,
	  BE_R0_SBI_TERMINAL },
	{ "dbcn-denied", BE_R0_SBI_ERR_DENIED, BE_R0_SBI_TERMINAL },
	{ "dbcn-failed", BE_R0_SBI_ERR_FAILED, BE_R0_SBI_TERMINAL },
	{ "probe-not-supported", BE_R0_SBI_ERR_NOT_SUPPORTED,
	  BE_R0_SBI_FAILS_CLOSED },
	{ "srst-success-no-return", BE_R0_SBI_SUCCESS, BE_R0_SBI_TERMINUS },
	{ "srst-refused", BE_R0_SBI_ERR_FAILED, BE_R0_SBI_TERMINAL },
};

#endif
