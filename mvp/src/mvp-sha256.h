/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: SHA-256 (FIPS 180-4) and HMAC-SHA-256 (RFC 2104) for the MVP
 *          (planning/mvp-m2-plan.md, Q6, Q7, and "The measurement"): an
 *          incremental hash, so that hart 0 can measure several regions in
 *          one order, a one-shot helper, and the keyed digest the protected
 *          domain's program computes on top of it.
 * Trust:   restricted C with explicit bounded loops: no CSR, SBI call, I/O,
 *          or libc. The one table is the 64 round constants; the hash reads
 *          only the bytes it is given and writes only its context and its
 *          digest.
 * Scope:   the MVP line (M2): compiled into the monitor and the guest
 *          program. The measurement it computes is local identity, not
 *          attestation; no key is held here.
 */

#ifndef BE_MVP_SHA256_H
#define BE_MVP_SHA256_H

#include <be/types.h>

/* A digest, and the block the compression function takes. */
#define BE_MVP_SHA256_BYTES		32U
#define BE_MVP_SHA256_BLOCK_BYTES	64U

/**
 * struct be_mvp_sha256 - one incremental SHA-256
 * @state: the eight working hash words, H0 to H7
 * @length: message bytes taken so far, fewer than 2^61; the bytes of the
 *          partial block are its remainder modulo 64
 * @block: the partial block, its first (@length % 64) bytes in use
 */
struct be_mvp_sha256 {
	be_u32 state[8];
	be_u64 length;
	be_u8 block[BE_MVP_SHA256_BLOCK_BYTES];
};

/**
 * be_mvp_sha256_init - start a hash
 * @context: the context, set to FIPS 180-4's initial hash value and an
 *           empty message
 */
void be_mvp_sha256_init(struct be_mvp_sha256 *context);

/**
 * be_mvp_sha256_update - hash more message bytes, in order
 * @context: a started context
 * @data: the bytes; read only when @bytes is nonzero
 * @bytes: how many
 */
void be_mvp_sha256_update(struct be_mvp_sha256 *context, const be_u8 *data,
			  be_u64 bytes);

/**
 * be_mvp_sha256_final - pad, finish, and write the digest
 * @context: a started context, spent afterwards: start it again to reuse it
 * @digest: %BE_MVP_SHA256_BYTES bytes, big-endian H0 to H7
 */
void be_mvp_sha256_final(struct be_mvp_sha256 *context, be_u8 *digest);

/**
 * be_mvp_sha256 - one message's digest
 * @data: the message; read only when @bytes is nonzero
 * @bytes: its length, fewer than 2^61
 * @digest: %BE_MVP_SHA256_BYTES bytes
 */
void be_mvp_sha256(const be_u8 *data, be_u64 bytes, be_u8 *digest);

/**
 * be_mvp_hmac_sha256 - HMAC-SHA-256 (RFC 2104) of one message
 * @key: the key; a key longer than one block is hashed first, a shorter
 *       one padded with zeros to the block
 * @key_bytes: its length
 * @message: the message; read only when @message_bytes is nonzero
 * @message_bytes: its length
 * @mac: %BE_MVP_SHA256_BYTES bytes, SHA-256((K0 ^ opad) ||
 *       SHA-256((K0 ^ ipad) || message)); it may not overlap @key or
 *       @message
 */
void be_mvp_hmac_sha256(const be_u8 *key, be_u64 key_bytes,
			const be_u8 *message, be_u64 message_bytes,
			be_u8 *mac);

#endif
