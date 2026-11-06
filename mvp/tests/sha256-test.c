// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the MVP SHA-256 and HMAC-SHA-256
 *          (planning/mvp-m2-plan.md, Q6 and Q7): FIPS 180-4's examples (the
 *          empty message, "abc", the 448-bit and 896-bit messages, and one
 *          million "a"), messages on each side of the padding's block
 *          boundaries, the incremental hash against the one-shot at every
 *          split of a 300-byte message and byte by byte, and RFC 4231's
 *          HMAC-SHA-256 test cases 1 to 7 with keys either side of one
 *          block.
 * Trust:   host evidence only; the expected digests are the published
 *          ones, and the others Python's hashlib and hmac.
 * Scope:   the MVP line (M2).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mvp-sha256.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_SHA256_CHECK: assertion failed: " \
			       "%s:%d: %s\n", __FILE__, __LINE__, \
			       #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define MILLION			1000000U
#define PATTERN_BYTES		300U

static be_u8 million[MILLION];
static be_u8 pattern[PATTERN_BYTES];

/* Whether a digest, or its first @bytes, is the hex string @hex. */
static int digest_is(const be_u8 *digest, be_size bytes, const char *hex)
{
	char text[2U * BE_MVP_SHA256_BYTES + 1U];
	be_size index;

	if (strlen(hex) != 2U * bytes || bytes > BE_MVP_SHA256_BYTES)
		return 0;
	for (index = 0U; index < bytes; ++index)
		snprintf(&text[2U * index], 3U, "%02x", digest[index]);
	return memcmp(text, hex, 2U * bytes) == 0;
}

static void check_message(const char *message, const char *hex)
{
	be_u8 digest[BE_MVP_SHA256_BYTES];

	SCENARIO();
	be_mvp_sha256((const be_u8 *)message, strlen(message), digest);
	CHECK(digest_is(digest, sizeof(digest), hex));
}

/* FIPS 180-4's examples (the NIST example values for SHA-256). */
static void test_fips(void)
{
	struct be_mvp_sha256 context;
	be_u8 digest[BE_MVP_SHA256_BYTES];
	be_size index;

	check_message("", "e3b0c44298fc1c149afbf4c8996fb924"
		      "27ae41e4649b934ca495991b7852b855");
	check_message("abc", "ba7816bf8f01cfea414140de5dae2223"
		      "b00361a396177a9cb410ff61f20015ad");
	check_message("abcdbcdecdefdefgefghfghighijhijk"
		      "ijkljklmklmnlmnomnopnopq",
		      "248d6a61d20638b8e5c026930c3e6039"
		      "a33ce45964ff2167f6ecedd419db06c1");
	check_message("abcdefghbcdefghicdefghijdefghijk"
		      "efghijklfghijklmghijklmnhijklmno"
		      "ijklmnopjklmnopqklmnopqrlmnopqrs"
		      "mnopqrstnopqrstu",
		      "cf5b16a778af8380036ce59e7b049237"
		      "0b249b11e8f07a51afac45037afee9d1");
	/* One million "a": in one call, and in 1,000 calls of 1,000. */
	SCENARIO();
	memset(million, 'a', sizeof(million));
	be_mvp_sha256(million, sizeof(million), digest);
	CHECK(digest_is(digest, sizeof(digest),
			"cdc76e5c9914fb9281a1c7e284d73e67"
			"f1809a48a497200e046d39ccc7112cd0"));
	be_mvp_sha256_init(&context);
	for (index = 0U; index < 1000U; ++index)
		be_mvp_sha256_update(&context, million + index * 1000U, 1000U);
	CHECK(context.length == MILLION);
	be_mvp_sha256_final(&context, digest);
	CHECK(digest_is(digest, sizeof(digest),
			"cdc76e5c9914fb9281a1c7e284d73e67"
			"f1809a48a497200e046d39ccc7112cd0"));
}

/*
 * The padding's boundaries: 55 bytes end in one block, 56 need a second
 * for the length, 63, 64, and 65 straddle a whole block.
 */
static void test_boundaries(void)
{
	static const struct {
		be_size bytes;
		const char *hex;
	} cases[] = {
		{ 55U, "9f4390f8d30c2dd92ec9f095b65e2b9a"
		       "e9b0a925a5258e241c9f1e910f734318" },
		{ 56U, "b35439a4ac6f0948b6d6f9e3c6af0f5f"
		       "590ce20f1bde7090ef7970686ec6738a" },
		{ 57U, "f13b2d724659eb3bf47f2dd6af1accc8"
		       "7b81f09f59f2b75e5c0bed6589dfe8c6" },
		{ 63U, "7d3e74a05d7db15bce4ad9ec0658ea98"
		       "e3f06eeecf16b4c6fff2da457ddc2f34" },
		{ 64U, "ffe054fe7ae0cb6dc65c3af9b61d5209"
		       "f439851db43d0ba5997337df154668eb" },
		{ 65U, "635361c48bb9eab14198e76ea8ab7f1a"
		       "41685d6ad62aa9146d301d4f17eb0ae0" },
	};
	be_u8 digest[BE_MVP_SHA256_BYTES];
	be_size index;

	SCENARIO();
	memset(million, 'a', sizeof(million));
	for (index = 0U; index < sizeof(cases) / sizeof(cases[0]); ++index) {
		be_mvp_sha256(million, cases[index].bytes, digest);
		CHECK(digest_is(digest, sizeof(digest), cases[index].hex));
	}
}

/*
 * The incremental hash against the one-shot: a 300-byte message split in
 * two at every point, 0 to 300, each part one call; then byte by byte, and
 * with empty calls between.
 */
static void test_splits(void)
{
	struct be_mvp_sha256 context;
	be_u8 whole[BE_MVP_SHA256_BYTES];
	be_u8 digest[BE_MVP_SHA256_BYTES];
	be_size split;

	SCENARIO();
	for (split = 0U; split < PATTERN_BYTES; ++split)
		pattern[split] = (be_u8)(split * 7U + 3U);
	be_mvp_sha256(pattern, PATTERN_BYTES, whole);
	CHECK(digest_is(whole, sizeof(whole),
			"04773f8726c81cafcfa1a09a82664b98"
			"b00d2021031a1715bca1154f2dad3472"));
	for (split = 0U; split <= PATTERN_BYTES; ++split) {
		be_mvp_sha256_init(&context);
		be_mvp_sha256_update(&context, pattern, split);
		be_mvp_sha256_update(&context, pattern + split,
				     PATTERN_BYTES - split);
		CHECK(context.length == PATTERN_BYTES);
		be_mvp_sha256_final(&context, digest);
		CHECK(memcmp(digest, whole, sizeof(whole)) == 0);
	}
	be_mvp_sha256_init(&context);
	for (split = 0U; split < PATTERN_BYTES; ++split) {
		be_mvp_sha256_update(&context, pattern + split, 1U);
		be_mvp_sha256_update(&context, (const be_u8 *)0, 0U);
	}
	be_mvp_sha256_final(&context, digest);
	CHECK(memcmp(digest, whole, sizeof(whole)) == 0);
}

static void check_hmac(const be_u8 *key, be_size key_bytes,
		       const char *message, be_size digest_bytes,
		       const char *hex)
{
	be_u8 mac[BE_MVP_SHA256_BYTES];

	SCENARIO();
	be_mvp_hmac_sha256(key, key_bytes, (const be_u8 *)message,
			   strlen(message), mac);
	CHECK(digest_is(mac, digest_bytes, hex));
}

/*
 * RFC 4231 section 4's HMAC-SHA-256 values (test case 5's truncated to
 * 128 bits, as published), and keys of exactly one block, which is used
 * as it is, and one byte more, which is hashed first.
 */
static void test_hmac(void)
{
	be_u8 key[131];
	be_u8 data[50];
	be_u8 mac[BE_MVP_SHA256_BYTES];
	be_size index;

	memset(key, 0x0b, 20U);
	check_hmac(key, 20U, "Hi There", sizeof(mac),
		   "b0344c61d8db38535ca8afceaf0bf12b"
		   "881dc200c9833da726e9376c2e32cff7");
	check_hmac((const be_u8 *)"Jefe", 4U, "what do ya want for nothing?",
		   sizeof(mac), "5bdcc146bf60754e6a042426089575c7"
		   "5a003f089d2739839dec58b964ec3843");
	SCENARIO();
	memset(key, 0xaa, 20U);
	memset(data, 0xdd, sizeof(data));
	be_mvp_hmac_sha256(key, 20U, data, sizeof(data), mac);
	CHECK(digest_is(mac, sizeof(mac), "773ea91e36800e46854db8ebd09181a7"
			"2959098b3ef8c122d9635514ced565fe"));
	SCENARIO();
	for (index = 0U; index < 25U; ++index)
		key[index] = (be_u8)(index + 1U);
	memset(data, 0xcd, sizeof(data));
	be_mvp_hmac_sha256(key, 25U, data, sizeof(data), mac);
	CHECK(digest_is(mac, sizeof(mac), "82558a389a443c0ea4cc819899f2083a"
			"85f0faa3e578f8077a2e3ff46729665b"));
	memset(key, 0x0c, 20U);
	check_hmac(key, 20U, "Test With Truncation", 16U,
		   "a3b6167473100ee06e0c796c2955552b");
	memset(key, 0xaa, sizeof(key));
	check_hmac(key, sizeof(key),
		   "Test Using Larger Than Block-Size Key - Hash Key First",
		   sizeof(mac), "60e431591ee0b67f0d8a26aacbf5b77f"
		   "8e0bc6213728c5140546040f0ee37f54");
	check_hmac(key, sizeof(key),
		   "This is a test using a larger than block-size key and a "
		   "larger than block-size data. The key needs to be hashed "
		   "before being used by the HMAC algorithm.", sizeof(mac),
		   "9b09ffa71b942fcb27635fbcd5b0e944"
		   "bfdc63644f0713938a7f51535c3a35e2");
	for (index = 0U; index < 65U; ++index)
		key[index] = (be_u8)index;
	check_hmac(key, 64U, "key of one block", sizeof(mac),
		   "327981d2585862e2ff92acee16f7a548"
		   "f9002b21a3a05ea1f7799c57791b2b12");
	check_hmac(key, 65U, "key of one block", sizeof(mac),
		   "de5681c378ff6d294f34d50277dd8bf1"
		   "270e627afc9a574c75c83bab5ce0ad24");
}

int main(void)
{
	test_fips();
	test_boundaries();
	test_splits();
	test_hmac();
	printf("BE_MVP_SHA256_CHECK: PASS\n");
	printf("BE_MVP_SHA256_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_MVP_SHA256_CHECK: assertions=%lu\n", assertions);
	return 0;
}
