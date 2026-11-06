// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: SHA-256 as FIPS 180-4 section 6.2 states it, with the message
 *          schedule kept in a 16-word ring, and HMAC-SHA-256 as RFC 2104
 *          states it (planning/mvp-m2-plan.md, Q6 and Q7).
 * Trust:   restricted C with explicit bounded loops; no CSR, SBI call, I/O,
 *          or libc. The round constants are the one table.
 * Scope:   the MVP line (M2); see mvp-sha256.h.
 */
#include "mvp-sha256.h"

#define BLOCK_BYTES		BE_MVP_SHA256_BLOCK_BYTES
#define BLOCK_MASK		((be_u64)BLOCK_BYTES - 1U)
/* The last eight bytes of the final block hold the message's bit count. */
#define LENGTH_AT		(BLOCK_BYTES - 8U)
#define ROUNDS			64U
#define SCHEDULE_WORDS		16U
#define SCHEDULE_MASK		(SCHEDULE_WORDS - 1U)
#define STATE_WORDS		8U
#define HMAC_IPAD		0x36U
#define HMAC_OPAD		0x5cU

_Static_assert(BLOCK_BYTES == 64U && BE_MVP_SHA256_BYTES == 32U,
	       "SHA-256 takes 512-bit blocks and gives a 256-bit digest");
_Static_assert(sizeof(be_u32) == 4U && sizeof(be_u64) == 8U,
	       "SHA-256 works on 32-bit words and a 64-bit length");

/* FIPS 180-4 section 4.2.2: the first 32 bits of the fractional parts of
 * the cube roots of the first 64 primes. */
static const be_u32 round_constants[ROUNDS] = {
	0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U,
	0x3956c25bU, 0x59f111f1U, 0x923f82a4U, 0xab1c5ed5U,
	0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
	0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U,
	0xe49b69c1U, 0xefbe4786U, 0x0fc19dc6U, 0x240ca1ccU,
	0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
	0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U,
	0xc6e00bf3U, 0xd5a79147U, 0x06ca6351U, 0x14292967U,
	0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
	0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U,
	0xa2bfe8a1U, 0xa81a664bU, 0xc24b8b70U, 0xc76c51a3U,
	0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
	0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U,
	0x391c0cb3U, 0x4ed8aa4aU, 0x5b9cca4fU, 0x682e6ff3U,
	0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
	0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U,
};

static be_u32 rotate_right(be_u32 value, unsigned int count)
{
	return (value >> count) | (value << (32U - count));
}

static be_u32 load_be32(const be_u8 *source)
{
	return ((be_u32)source[0] << 24) | ((be_u32)source[1] << 16) |
	       ((be_u32)source[2] << 8) | (be_u32)source[3];
}

static void store_be32(be_u8 *destination, be_u32 value)
{
	destination[0] = (be_u8)(value >> 24);
	destination[1] = (be_u8)(value >> 16);
	destination[2] = (be_u8)(value >> 8);
	destination[3] = (be_u8)value;
}

/* FIPS 180-4 section 4.1.2's functions. */
static be_u32 choose(be_u32 x, be_u32 y, be_u32 z)
{
	return (x & y) ^ (~x & z);
}

static be_u32 majority(be_u32 x, be_u32 y, be_u32 z)
{
	return (x & y) ^ (x & z) ^ (y & z);
}

static be_u32 big_sigma0(be_u32 x)
{
	return rotate_right(x, 2U) ^ rotate_right(x, 13U) ^
	       rotate_right(x, 22U);
}

static be_u32 big_sigma1(be_u32 x)
{
	return rotate_right(x, 6U) ^ rotate_right(x, 11U) ^
	       rotate_right(x, 25U);
}

static be_u32 small_sigma0(be_u32 x)
{
	return rotate_right(x, 7U) ^ rotate_right(x, 18U) ^ (x >> 3);
}

static be_u32 small_sigma1(be_u32 x)
{
	return rotate_right(x, 17U) ^ rotate_right(x, 19U) ^ (x >> 10);
}

/*
 * One block (FIPS 180-4 section 6.2.2). The schedule word W[t] for t of 16
 * and more replaces W[t - 16] in a ring of 16: W[t - 15] is the next slot,
 * W[t - 7] nine slots on, and W[t - 2] fourteen slots on.
 */
static void compress(be_u32 *state, const be_u8 *block)
{
	be_u32 schedule[SCHEDULE_WORDS];
	be_u32 work[STATE_WORDS];
	unsigned int round;

	for (round = 0U; round < SCHEDULE_WORDS; ++round)
		schedule[round] = load_be32(block + 4U * round);
	for (round = 0U; round < STATE_WORDS; ++round)
		work[round] = state[round];
	for (round = 0U; round < ROUNDS; ++round) {
		be_u32 word = schedule[round & SCHEDULE_MASK];
		be_u32 first;
		be_u32 second;
		unsigned int index;

		if (round >= SCHEDULE_WORDS) {
			word += small_sigma0(schedule[(round + 1U) &
						      SCHEDULE_MASK]) +
				schedule[(round + 9U) & SCHEDULE_MASK] +
				small_sigma1(schedule[(round + 14U) &
						      SCHEDULE_MASK]);
			schedule[round & SCHEDULE_MASK] = word;
		}
		first = work[7] + big_sigma1(work[4]) +
			choose(work[4], work[5], work[6]) +
			round_constants[round] + word;
		second = big_sigma0(work[0]) +
			 majority(work[0], work[1], work[2]);
		for (index = STATE_WORDS - 1U; index > 0U; --index)
			work[index] = work[index - 1U];
		work[4] += first;
		work[0] = first + second;
	}
	for (round = 0U; round < STATE_WORDS; ++round)
		state[round] += work[round];
}

void be_mvp_sha256_init(struct be_mvp_sha256 *context)
{
	unsigned int index;

	/* FIPS 180-4 section 5.3.3: the initial hash value H(0). */
	context->state[0] = 0x6a09e667U;
	context->state[1] = 0xbb67ae85U;
	context->state[2] = 0x3c6ef372U;
	context->state[3] = 0xa54ff53aU;
	context->state[4] = 0x510e527fU;
	context->state[5] = 0x9b05688cU;
	context->state[6] = 0x1f83d9abU;
	context->state[7] = 0x5be0cd19U;
	for (index = 0U; index < BLOCK_BYTES; ++index)
		context->block[index] = 0U;
	context->length = 0U;
}

void be_mvp_sha256_update(struct be_mvp_sha256 *context, const be_u8 *data,
			  be_u64 bytes)
{
	be_u64 index = 0U;

	/* Fill the partial block; then whole blocks from @data; then the
	 * rest into the block. */
	while (index < bytes && (context->length & BLOCK_MASK) != 0U) {
		context->block[context->length & BLOCK_MASK] = data[index++];
		if ((++context->length & BLOCK_MASK) == 0U)
			compress(context->state, context->block);
	}
	while (bytes - index >= BLOCK_BYTES) {
		compress(context->state, data + index);
		index += BLOCK_BYTES;
		context->length += BLOCK_BYTES;
	}
	while (index < bytes)
		context->block[context->length++ & BLOCK_MASK] =
			data[index++];
}

void be_mvp_sha256_final(struct be_mvp_sha256 *context, be_u8 *digest)
{
	be_u64 bits = context->length << 3;
	be_u64 used = context->length & BLOCK_MASK;
	unsigned int index;

	/* FIPS 180-4 section 5.1.1: one bit, zeros, the 64-bit bit count. */
	context->block[used++] = 0x80U;
	if (used > LENGTH_AT) {
		while (used < BLOCK_BYTES)
			context->block[used++] = 0U;
		compress(context->state, context->block);
		used = 0U;
	}
	while (used < LENGTH_AT)
		context->block[used++] = 0U;
	for (index = 0U; index < 8U; ++index)
		context->block[LENGTH_AT + index] =
			(be_u8)(bits >> (56U - 8U * index));
	compress(context->state, context->block);
	for (index = 0U; index < STATE_WORDS; ++index)
		store_be32(digest + 4U * index, context->state[index]);
}

void be_mvp_sha256(const be_u8 *data, be_u64 bytes, be_u8 *digest)
{
	struct be_mvp_sha256 context;

	be_mvp_sha256_init(&context);
	be_mvp_sha256_update(&context, data, bytes);
	be_mvp_sha256_final(&context, digest);
}

void be_mvp_hmac_sha256(const be_u8 *key, be_u64 key_bytes,
			const be_u8 *message, be_u64 message_bytes,
			be_u8 *mac)
{
	struct be_mvp_sha256 context;
	be_u8 padded_key[BLOCK_BYTES];
	be_u8 pad[BLOCK_BYTES];
	be_u8 inner[BE_MVP_SHA256_BYTES];
	be_u64 index;

	/* K0 (RFC 2104 step 1): the key, or its digest, then zeros. */
	for (index = 0U; index < BLOCK_BYTES; ++index)
		padded_key[index] = 0U;
	if (key_bytes > BLOCK_BYTES)
		be_mvp_sha256(key, key_bytes, padded_key);
	else
		for (index = 0U; index < key_bytes; ++index)
			padded_key[index] = key[index];
	for (index = 0U; index < BLOCK_BYTES; ++index)
		pad[index] = (be_u8)(padded_key[index] ^ HMAC_IPAD);
	be_mvp_sha256_init(&context);
	be_mvp_sha256_update(&context, pad, BLOCK_BYTES);
	be_mvp_sha256_update(&context, message, message_bytes);
	be_mvp_sha256_final(&context, inner);
	for (index = 0U; index < BLOCK_BYTES; ++index)
		pad[index] = (be_u8)(padded_key[index] ^ HMAC_OPAD);
	be_mvp_sha256_init(&context);
	be_mvp_sha256_update(&context, pad, BLOCK_BYTES);
	be_mvp_sha256_update(&context, inner, BE_MVP_SHA256_BYTES);
	be_mvp_sha256_final(&context, mac);
}
