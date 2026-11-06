// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the MVP's measurement log, the Beryllium log
 *          profile version 1 (mvp/docs/log-profile.md; planning/
 *          mvp-m9-plan.md, D-1 and M9-3): every offset and width of the
 *          header and of a record, every enumeration's number and name, the
 *          sequence, the per-stream numbers, and the count; the close's
 *          rule (written only when the count after it is the expected
 *          count; a page that cannot close); the reserved bytes and the
 *          slots after count zero; overflow when the 41st slot would hold a
 *          data record; the refused records; the launch gate; the register
 *          recurrence against mvp-sha256.c, stream 0 zero without R2; the
 *          console grants' four values (2.8); the profile's test vectors
 *          (2.10 and 5.4) verbatim: the te-poc page's SHA-256, its header,
 *          records 9 and 13, its registers, and every one of its lines;
 *          each line's bound; and the rendering's losslessness: a v2, a
 *          v3, a failed gate's, and an overflowed page rendered to lines,
 *          parsed back here, rebuilt, and compared with the page byte for
 *          byte.
 * Trust:   host evidence only; the expected values are the profile's, its
 *          names this file's own copy of section 2.4, and the others
 *          Python's hashlib.
 * Scope:   the MVP line (M9).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mvp-log.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_LOG_CHECK: assertion failed: " \
			       "%s:%d: %s\n", __FILE__, __LINE__, \
			       #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define PAGE_BYTES		BE_MVP_LOG_PAGE_BYTES
#define REGISTERS_BYTES		BE_MVP_LOG_REGISTERS_BYTES
#define DIGEST			BE_MVP_LOG_DIGEST_BYTES
#define LINE_MAX		(BE_MVP_LINE_CAPACITY - 1U)
#define LABEL			"beryllium-log-profile-v1 example: "

/* Section 2.4's names, by number: the profile's, not the module's. */
static const char *const types[] = { "", "measured", "informational",
				     "close" };
static const char *const objects[] = {
	"monitor-text", "monitor-rodata", "monitor-input", "mvp-text",
	"mvp-rodata", "core-identity", "console-grants",
	"configuration-identity", "policy-identity", "policy-absent",
	"kernel-image", "device-tree", "secret-page", "close",
};
static const char *const reprs[] = { "as-placed", "as-computed",
				     "build-recorded", "none" };
static const char *const outcomes[] = { "recorded", "gated-pass",
					"gated-fail", "none" };
static const char *const states[] = { "open", "closed", "overflow" };

static be_u8 page[PAGE_BYTES];
static be_u8 registers[REGISTERS_BYTES];
static be_u8 rebuilt[PAGE_BYTES];
static be_u8 snapshot[PAGE_BYTES];
static struct be_mvp_line line;
static char text[BE_MVP_LINE_CAPACITY + 1U];

/* The profile's 5.4 example: the te-poc lines. */
static const char *const example_lines[] = {
	"BE_MVP:19 LOG header magic=BEMVPLOG version=1 hlen=128 "
	"rlen=96 capacity=41 count=14 state=closed alg=0x000b scena"
	"rio=5c74d0dcde52a6a6c1ffcc50d176f51d74e7b669a8c7608b6d5c99"
	"55ee34a9ba config=9f6f6d940a41d7af494a1e4c1afe1b6edcf87939"
	"12b5755de37d57b9adb08849",
	"BE_MVP:19 LOG record seq=0 producer=0 type=measured "
	"stream=0 object=monitor-text repr=as-placed "
	"outcome=recorded base=0x0000000102000000 "
	"length=0x0000000000004540 dlen=32 srec=0 expected=0 digest"
	"=96704ef2f5b319b854004242adf83cea20e272e01697402d9d968650f"
	"0f0c392",
	"BE_MVP:19 LOG record seq=1 producer=0 type=measured "
	"stream=0 object=monitor-rodata repr=as-placed "
	"outcome=recorded base=0x0000000102008610 "
	"length=0x00000000000002e8 dlen=32 srec=1 expected=0 digest"
	"=ab1aea296cbff86a1cb5156562601b239f292db71c89b5399a222fe8c"
	"a6bdc73",
	"BE_MVP:19 LOG record seq=2 producer=0 type=measured "
	"stream=0 object=monitor-input repr=as-placed "
	"outcome=recorded base=0x0000000102008000 "
	"length=0x0000000000000610 dlen=32 srec=2 expected=0 digest"
	"=8b876a7e36e8161d6b2199a998d6213e1448cf46699dce4fbf80b277e"
	"b08564e",
	"BE_MVP:19 LOG record seq=3 producer=0 type=measured "
	"stream=0 object=mvp-text repr=as-placed outcome=recorded "
	"base=0x0000000102064000 length=0x0000000000006a40 dlen=32 "
	"srec=3 expected=0 digest=ec6d6ddf35da0c8bcd41de09b0e3c1e34"
	"e3aec6fc50c0835749797309d272039",
	"BE_MVP:19 LOG record seq=4 producer=0 type=measured "
	"stream=0 object=mvp-rodata repr=as-placed "
	"outcome=recorded base=0x000000010206aa40 "
	"length=0x0000000000001238 dlen=32 srec=4 expected=0 digest"
	"=06a35b4b92030141900fc59c7db016bb483c37ddd1962a4f8ee739c72"
	"279b5aa",
	"BE_MVP:19 LOG record seq=5 producer=0 type=measured "
	"stream=1 object=core-identity repr=as-computed "
	"outcome=recorded base=0x0000000000000000 "
	"length=0x0000000000000000 dlen=32 srec=0 expected=0 digest"
	"=f958c31fd593ea0db3bd787a5e45bf2383fdeb8f831d5a451c89a4c31"
	"71a933b",
	"BE_MVP:19 LOG record seq=6 producer=0 type=measured "
	"stream=1 object=console-grants repr=as-computed "
	"outcome=recorded base=0x0000000000000000 "
	"length=0x0000000000000000 dlen=32 srec=1 expected=0 digest"
	"=96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630"
	"a09cfc7",
	"BE_MVP:19 LOG record seq=7 producer=0 type=informational "
	"stream=1 object=configuration-identity "
	"repr=build-recorded outcome=recorded "
	"base=0x0000000000000000 length=0x0000000000000000 dlen=32 "
	"srec=2 expected=0 digest=9f6f6d940a41d7af494a1e4c1afe1b6ed"
	"cf8793912b5755de37d57b9adb08849",
	"BE_MVP:19 LOG record seq=8 producer=0 type=informational "
	"stream=1 object=policy-identity repr=build-recorded "
	"outcome=recorded base=0x0000000000000000 "
	"length=0x0000000000000000 dlen=32 srec=3 expected=0 digest"
	"=04687fe4d6177770e89b698f53d82ed52b266c793f5c46318bf8308f0"
	"20e01aa",
	"BE_MVP:19 LOG record seq=9 producer=0 type=measured "
	"stream=2 object=kernel-image repr=as-placed "
	"outcome=recorded base=0x0000000110200000 "
	"length=0x00000000001f7cc4 dlen=32 srec=0 expected=0 digest"
	"=11a3896e8a92b007f3ad6d26d521883dc719d08ff0fe112d1e4f7907f"
	"3bdce07",
	"BE_MVP:19 LOG record seq=10 producer=0 type=measured "
	"stream=2 object=device-tree repr=as-placed "
	"outcome=gated-pass base=0x0000000113e00000 "
	"length=0x0000000000001000 dlen=32 srec=1 expected=0 digest"
	"=acb0cc67e2c3326bd3ffaab74989b2e3d621a55dabb28fad3420669ab"
	"f3be755",
	"BE_MVP:19 LOG record seq=11 producer=0 type=measured "
	"stream=3 object=kernel-image repr=as-placed "
	"outcome=recorded base=0x0000000114200000 "
	"length=0x00000000001f7cc4 dlen=32 srec=0 expected=0 digest"
	"=11a3896e8a92b007f3ad6d26d521883dc719d08ff0fe112d1e4f7907f"
	"3bdce07",
	"BE_MVP:19 LOG record seq=12 producer=0 type=measured "
	"stream=3 object=device-tree repr=as-placed "
	"outcome=gated-pass base=0x0000000117e00000 "
	"length=0x0000000000001000 dlen=32 srec=1 expected=0 digest"
	"=03e25ec8838e5999d0806c526a6e41b6f51d990b1cd9f77d707ae7d68"
	"bfbf863",
	"BE_MVP:19 LOG record seq=13 producer=0 type=close "
	"stream=255 object=close repr=none outcome=none "
	"base=0x0000000000000000 length=0x0000000000000000 dlen=32 "
	"srec=0 expected=14 digest=00000000000000000000000000000000"
	"00000000000000000000000000000000",
	"BE_MVP:20 REGISTERS at=barrier r0=e0ea07e6f0a2a8cf3b014516"
	"11ad099709dd9a2e68cfb605310284e49e04fa33 r1=2241f9eb0370fc"
	"6e32abf6184d175ee4b738005126473678196ed06d8cc17bc1 r2=b89e"
	"71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b7"
	"92 r3=7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46"
	"a665564c8dc5 ticks=0x2a3f10",
	"BE_MVP:20 REGISTERS at=terminal r0=e0ea07e6f0a2a8cf3b01451"
	"611ad099709dd9a2e68cfb605310284e49e04fa33 r1=2241f9eb0370f"
	"c6e32abf6184d175ee4b738005126473678196ed06d8cc17bc1 r2=b89"
	"e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b"
	"792 r3=7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe4"
	"6a665564c8dc5",
};

/* 2.10: the example page's header, its records 9 and 13, and its digest. */
static const char example_header[] =
	"42454d56504c4f4701008000600029000e0001000b000000"
	"00000000000000005c74d0dcde52a6a6c1ffcc50d176f51d"
	"74e7b669a8c7608b6d5c9955ee34a9ba9f6f6d940a41d7af"
	"494a1e4c1afe1b6edcf8793912b5755de37d57b9adb08849"
	"000000000000000000000000000000000000000000000000"
	"0000000000000000";
static const char example_record9[] =
	"09000001020a00000000201001000000c47c1f0000000000"
	"200000000000000011a3896e8a92b007f3ad6d26d521883d"
	"c719d08ff0fe112d1e4f7907f3bdce070000000000000000"
	"000000000000000000000000000000000000000000000000";
static const char example_record13[] =
	"0d000003ff0d030300000000000000000000000000000000"
	"200000000e00000000000000000000000000000000000000"
	"000000000000000000000000000000000000000000000000"
	"000000000000000000000000000000000000000000000000";
static const char example_page_sha256[] =
	"4435113d8276c4444630b2be8fd3ff60929f68723a121b8c6574f049488b1184";
static const char *const example_registers[BE_MVP_LOG_STREAMS] = {
	"e0ea07e6f0a2a8cf3b01451611ad099709dd9a2e68cfb605310284e49e04fa33",
	"2241f9eb0370fc6e32abf6184d175ee4b738005126473678196ed06d8cc17bc1",
	"b89e71c193a2e04957a903a7c6bbf39b7f277a6b25ee822a0138c2f73191b792",
	"7f68367be55d51972af9e85145ad30396b36d4832fd2bf73fe46a665564c8dc5",
};
#define EXAMPLE_TICKS		0x2a3f10U

/* One record of a page this test builds; label NULL: the digest given. */
struct entry {
	enum be_mvp_log_type type;
	be_u32 stream;
	enum be_mvp_log_object object;
	enum be_mvp_log_repr repr;
	be_u64 base;
	be_u64 length;
	const char *label;
	int gate;
};

#define R2_ENTRIES \
	{ BE_MVP_LOG_MEASURED, 0U, BE_MVP_LOG_MONITOR_TEXT, \
	  BE_MVP_LOG_AS_PLACED, 0x102000000U, 0x4540U, "monitor-text", 0 }, \
	{ BE_MVP_LOG_MEASURED, 0U, BE_MVP_LOG_MONITOR_RODATA, \
	  BE_MVP_LOG_AS_PLACED, 0x102008610U, 0x2e8U, "monitor-rodata", 0 }, \
	{ BE_MVP_LOG_MEASURED, 0U, BE_MVP_LOG_MONITOR_INPUT, \
	  BE_MVP_LOG_AS_PLACED, 0x102008000U, 0x610U, "monitor-input", 0 }, \
	{ BE_MVP_LOG_MEASURED, 0U, BE_MVP_LOG_MVP_TEXT, \
	  BE_MVP_LOG_AS_PLACED, 0x102064000U, 0x6a40U, "mvp-text", 0 }, \
	{ BE_MVP_LOG_MEASURED, 0U, BE_MVP_LOG_MVP_RODATA, \
	  BE_MVP_LOG_AS_PLACED, 0x10206aa40U, 0x1238U, "mvp-rodata", 0 }

/* The example's v2 sequence (3.1), R2 kept: 13 data records. */
static const struct entry example[] = {
	R2_ENTRIES,
	{ BE_MVP_LOG_MEASURED, 1U, BE_MVP_LOG_CORE_IDENTITY,
	  BE_MVP_LOG_AS_COMPUTED, 0U, 0U, "core-identity", 0 },
	{ BE_MVP_LOG_MEASURED, 1U, BE_MVP_LOG_CONSOLE_GRANTS,
	  BE_MVP_LOG_AS_COMPUTED, 0U, 0U, (const char *)0, 0 },
	{ BE_MVP_LOG_INFORMATIONAL, 1U, BE_MVP_LOG_CONFIGURATION_IDENTITY,
	  BE_MVP_LOG_BUILD_RECORDED, 0U, 0U, "configuration-identity", 0 },
	{ BE_MVP_LOG_INFORMATIONAL, 1U, BE_MVP_LOG_POLICY_IDENTITY,
	  BE_MVP_LOG_BUILD_RECORDED, 0U, 0U, "policy-identity", 0 },
	{ BE_MVP_LOG_MEASURED, 2U, BE_MVP_LOG_KERNEL_IMAGE,
	  BE_MVP_LOG_AS_PLACED, 0x110200000U, 0x1f7cc4U, "kernel-image", 0 },
	{ BE_MVP_LOG_MEASURED, 2U, BE_MVP_LOG_DEVICE_TREE,
	  BE_MVP_LOG_AS_PLACED, 0x113e00000U, 0x1000U, "device-tree d0", 1 },
	{ BE_MVP_LOG_MEASURED, 3U, BE_MVP_LOG_KERNEL_IMAGE,
	  BE_MVP_LOG_AS_PLACED, 0x114200000U, 0x1f7cc4U, "kernel-image", 0 },
	{ BE_MVP_LOG_MEASURED, 3U, BE_MVP_LOG_DEVICE_TREE,
	  BE_MVP_LOG_AS_PLACED, 0x117e00000U, 0x1000U, "device-tree d1", 1 },
};

/* A v3 sequence (3.1), R2 kept: the secret page ends domain 1's launch. */
static const struct entry anchor[] = {
	R2_ENTRIES,
	{ BE_MVP_LOG_MEASURED, 1U, BE_MVP_LOG_CORE_IDENTITY,
	  BE_MVP_LOG_AS_COMPUTED, 0U, 0U, "core-identity", 0 },
	{ BE_MVP_LOG_MEASURED, 1U, BE_MVP_LOG_CONSOLE_GRANTS,
	  BE_MVP_LOG_AS_COMPUTED, 0U, 0U, (const char *)0, 0 },
	{ BE_MVP_LOG_INFORMATIONAL, 1U, BE_MVP_LOG_CONFIGURATION_IDENTITY,
	  BE_MVP_LOG_BUILD_RECORDED, 0U, 0U, "configuration-identity", 0 },
	{ BE_MVP_LOG_INFORMATIONAL, 1U, BE_MVP_LOG_POLICY_IDENTITY,
	  BE_MVP_LOG_BUILD_RECORDED, 0U, 0U, "policy-identity", 0 },
	{ BE_MVP_LOG_MEASURED, 2U, BE_MVP_LOG_KERNEL_IMAGE,
	  BE_MVP_LOG_AS_PLACED, 0x110200000U, 0x1f7cc4U, "kernel-image", 0 },
	{ BE_MVP_LOG_MEASURED, 2U, BE_MVP_LOG_DEVICE_TREE,
	  BE_MVP_LOG_AS_PLACED, 0x113e00000U, 0x1000U, "device-tree d0", 1 },
	{ BE_MVP_LOG_MEASURED, 3U, BE_MVP_LOG_KERNEL_IMAGE,
	  BE_MVP_LOG_AS_PLACED, 0x114200000U, 0x1f7cc4U, "kernel-image", 0 },
	{ BE_MVP_LOG_MEASURED, 3U, BE_MVP_LOG_DEVICE_TREE,
	  BE_MVP_LOG_AS_PLACED, 0x117e00000U, 0x1000U, "device-tree d1", 0 },
	{ BE_MVP_LOG_MEASURED, 3U, BE_MVP_LOG_SECRET_PAGE,
	  BE_MVP_LOG_AS_PLACED, 0x118002000U, 0x1000U, "secret-page", 1 },
};

/* A v1 sequence (3.1) without R2: stream 0 stays zero. */
static const struct entry two_guests[] = {
	{ BE_MVP_LOG_MEASURED, 1U, BE_MVP_LOG_CORE_IDENTITY,
	  BE_MVP_LOG_AS_COMPUTED, 0U, 0U, "core-identity", 0 },
	{ BE_MVP_LOG_MEASURED, 1U, BE_MVP_LOG_CONSOLE_GRANTS,
	  BE_MVP_LOG_AS_COMPUTED, 0U, 0U, (const char *)0, 0 },
	{ BE_MVP_LOG_INFORMATIONAL, 1U, BE_MVP_LOG_POLICY_ABSENT,
	  BE_MVP_LOG_BUILD_RECORDED, 0U, 0U, (const char *)0, 0 },
	{ BE_MVP_LOG_MEASURED, 2U, BE_MVP_LOG_KERNEL_IMAGE,
	  BE_MVP_LOG_AS_PLACED, 0x110200000U, 0x1f7cc4U, "kernel-image", 0 },
	{ BE_MVP_LOG_MEASURED, 2U, BE_MVP_LOG_DEVICE_TREE,
	  BE_MVP_LOG_AS_PLACED, 0x113e00000U, 0x1000U, "device-tree d0", 1 },
	{ BE_MVP_LOG_MEASURED, 3U, BE_MVP_LOG_KERNEL_IMAGE,
	  BE_MVP_LOG_AS_PLACED, 0x114200000U, 0x1f7cc4U, "kernel-image", 0 },
	{ BE_MVP_LOG_MEASURED, 3U, BE_MVP_LOG_DEVICE_TREE,
	  BE_MVP_LOG_AS_PLACED, 0x117e00000U, 0x1000U, "device-tree d1", 1 },
};

#define ENTRIES(array)		(sizeof(array) / sizeof((array)[0]))

static void label_digest(const char *label, be_u8 *digest)
{
	char message[128];
	int length = snprintf(message, sizeof(message), LABEL "%s", label);

	CHECK(length > 0 && (size_t)length < sizeof(message));
	be_mvp_sha256((const be_u8 *)message, (be_u64)length, digest);
}

static int hex_value(char digit)
{
	if (digit >= '0' && digit <= '9')
		return digit - '0';
	if (digit >= 'a' && digit <= 'f')
		return digit - 'a' + 10;
	return -1;
}

/* @hex, exactly 2 * @count lower-case digits, into @bytes; 0 if not. */
static int from_hex(const char *hex, size_t length, be_u8 *bytes,
		    size_t count)
{
	size_t index;

	if (length != 2U * count)
		return 0;
	for (index = 0U; index < count; ++index) {
		int high = hex_value(hex[2U * index]);
		int low = hex_value(hex[2U * index + 1U]);

		if (high < 0 || low < 0)
			return 0;
		bytes[index] = (be_u8)(high << 4 | low);
	}
	return 1;
}

static int bytes_are(const be_u8 *bytes, size_t count, const char *hex)
{
	be_u8 wanted[PAGE_BYTES];

	return from_hex(hex, strlen(hex), wanted, count) &&
	       memcmp(bytes, wanted, count) == 0;
}

static be_u64 le(const be_u8 *at, size_t width)
{
	be_u64 value = 0U;
	size_t index;

	for (index = width; index > 0U; --index)
		value = value << 8 | at[index - 1U];
	return value;
}

static const be_u8 *slot_of(const be_u8 *of, be_u64 index)
{
	return of + BE_MVP_LOG_HEADER_BYTES + index * BE_MVP_LOG_RECORD_BYTES;
}

static int all_zero(const be_u8 *bytes, size_t count)
{
	size_t index;

	for (index = 0U; index < count; ++index)
		if (bytes[index] != 0U)
			return 0;
	return 1;
}

/* The line as text, after checking it is usable and within its bound. */
static const char *rendered(void)
{
	CHECK(line.overflow == 0U && line.length <= LINE_MAX);
	memcpy(text, line.text, line.length);
	text[line.length] = '\0';
	CHECK(strlen(text) == line.length);
	return text;
}

static void record_of_entry(const struct entry *at, struct be_mvp_log_record
			    *record)
{
	memset(record, 0, sizeof(*record));
	record->type = at->type;
	record->stream = at->stream;
	record->object = at->object;
	record->representation = at->repr;
	record->base = at->base;
	record->length = at->length;
	if (at->object == BE_MVP_LOG_CONSOLE_GRANTS)
		be_mvp_log_console_grants(0U, record->digest);
	else if (at->label != (const char *)0)
		label_digest(at->label, record->digest);
}

/*
 * Build a page from @entries: the header's scenario and configuration
 * the example's (or zero), each record appended, each gate given
 * @expected's register for its stream (its own register, so passing, when
 * NULL), and the close when @close. Returns the last gate's result.
 */
static enum be_mvp_log_gate_result build(const struct entry *entries,
					 size_t count, int configured,
					 const char *const *expected,
					 int close)
{
	enum be_mvp_log_gate_result result = BE_MVP_LOG_GATE_INVALID;
	be_u8 scenario[DIGEST];
	be_u8 configuration[DIGEST];
	size_t index;

	label_digest("scenario te-poc", scenario);
	label_digest("configuration-identity", configuration);
	be_mvp_log_init(page, registers, scenario,
			configured ? configuration : (const be_u8 *)0);
	for (index = 0U; index < count; ++index) {
		struct be_mvp_log_record record;

		record_of_entry(&entries[index], &record);
		CHECK(be_mvp_log_append(page, registers, &record) == 1);
		if (entries[index].gate != 0) {
			be_u8 wanted[DIGEST];
			be_u32 stream = entries[index].stream;

			if (expected != (const char *const *)0)
				CHECK(from_hex(expected[stream],
					       strlen(expected[stream]),
					       wanted, DIGEST));
			else
				memcpy(wanted, registers + stream * DIGEST,
				       DIGEST);
			result = be_mvp_log_gate(page, registers, wanted);
			CHECK(result != BE_MVP_LOG_GATE_INVALID);
		}
	}
	if (close)
		CHECK(be_mvp_log_close(page, count + 1U) == 1);
	return result;
}

/* ------------------------------------------- the lines parsed back (4.6) */

/*
 * The next field of a line at @cursor: " @name=" (no space before the
 * first), its value up to the next space or the end, into @value.
 */
static int field(const char **cursor, const char *name, int first,
		 char *value, size_t size)
{
	const char *at = *cursor;
	size_t length = 0U;

	if (!first) {
		if (*at != ' ')
			return 0;
		++at;
	}
	if (strncmp(at, name, strlen(name)) != 0 || at[strlen(name)] != '=')
		return 0;
	at += strlen(name) + 1U;
	while (at[length] != '\0' && at[length] != ' ')
		++length;
	if (length == 0U || length >= size)
		return 0;
	memcpy(value, at, length);
	value[length] = '\0';
	*cursor = at + length;
	return 1;
}

/* A decimal of 4.1: 0, or a nonzero digit and digits, at most @limit. */
static int decimal(const char *value, be_u64 limit, be_u64 *out)
{
	be_u64 number = 0U;
	size_t index;

	if (value[0] == '\0' || (value[0] == '0' && value[1] != '\0'))
		return 0;
	for (index = 0U; value[index] != '\0'; ++index) {
		if (value[index] < '0' || value[index] > '9' || index > 5U)
			return 0;
		number = number * 10U + (be_u64)(value[index] - '0');
	}
	*out = number;
	return number <= limit;
}

/* A fixed-width "0x" hex of @digits digits. */
static int fixed_hex(const char *value, size_t digits, be_u64 *out)
{
	be_u64 number = 0U;
	size_t index;

	if (strlen(value) != digits + 2U || value[0] != '0' || value[1] != 'x')
		return 0;
	for (index = 2U; index < digits + 2U; ++index) {
		int digit = hex_value(value[index]);

		if (digit < 0)
			return 0;
		number = number << 4 | (be_u64)digit;
	}
	*out = number;
	return 1;
}

static int named(const char *value, const char *const *names, size_t count,
		 be_u64 *out)
{
	size_t index;

	for (index = 0U; index < count; ++index) {
		if (names[index][0] != '\0' && strcmp(value, names[index]) == 0) {
			*out = index;
			return 1;
		}
	}
	return 0;
}

static void put_le(be_u8 *at, be_u64 value, size_t width)
{
	size_t index;

	for (index = 0U; index < width; ++index)
		at[index] = (be_u8)(value >> (8U * index));
}

/* The header line into @out's header; 0 if it is not 4.2's form. */
static int parse_header(const char *line_text, be_u8 *out)
{
	static const char *const numbers[] = { "version", "hlen", "rlen",
					       "capacity", "count" };
	static const be_u64 at[] = { 8U, 10U, 12U, 14U, 16U };
	const char *cursor = line_text;
	char value[80];
	be_u64 number;
	size_t index;

	if (strncmp(cursor, "BE_MVP:19 LOG header ", 21U) != 0)
		return 0;
	cursor += 21;
	if (!field(&cursor, "magic", 1, value, sizeof(value)) ||
	    strlen(value) != 8U)
		return 0;
	memcpy(out, value, 8U);
	for (index = 0U; index < 5U; ++index) {
		if (!field(&cursor, numbers[index], 0, value, sizeof(value)) ||
		    !decimal(value, 0xffffU, &number))
			return 0;
		put_le(out + at[index], number, 2U);
	}
	if (!field(&cursor, "state", 0, value, sizeof(value)) ||
	    !named(value, states, 3U, &number))
		return 0;
	out[18] = (be_u8)number;
	if (!field(&cursor, "alg", 0, value, sizeof(value)) ||
	    !fixed_hex(value, 4U, &number))
		return 0;
	put_le(out + 20, number, 2U);
	if (!field(&cursor, "scenario", 0, value, sizeof(value)) ||
	    !from_hex(value, strlen(value), out + 32, DIGEST) ||
	    !field(&cursor, "config", 0, value, sizeof(value)) ||
	    !from_hex(value, strlen(value), out + 64, DIGEST))
		return 0;
	return *cursor == '\0';
}

/* One record line into its slot of @out; 0 if it is not 4.3's form. */
static int parse_record(const char *line_text, be_u8 *out)
{
	const char *cursor = line_text;
	char value[80];
	be_u64 seq, producer, type, stream, object, repr, outcome;
	be_u64 base, length, dlen, srec, expected;
	be_u8 *slot;

	if (strncmp(cursor, "BE_MVP:19 LOG record ", 21U) != 0)
		return 0;
	cursor += 21;
	if (!field(&cursor, "seq", 1, value, sizeof(value)) ||
	    !decimal(value, BE_MVP_LOG_CAPACITY - 1U, &seq) ||
	    !field(&cursor, "producer", 0, value, sizeof(value)) ||
	    !decimal(value, 0xffU, &producer) ||
	    !field(&cursor, "type", 0, value, sizeof(value)) ||
	    !named(value, types, 4U, &type) ||
	    !field(&cursor, "stream", 0, value, sizeof(value)) ||
	    !decimal(value, 0xffU, &stream) ||
	    !field(&cursor, "object", 0, value, sizeof(value)) ||
	    !named(value, objects, 14U, &object) ||
	    !field(&cursor, "repr", 0, value, sizeof(value)) ||
	    !named(value, reprs, 4U, &repr) ||
	    !field(&cursor, "outcome", 0, value, sizeof(value)) ||
	    !named(value, outcomes, 4U, &outcome) ||
	    !field(&cursor, "base", 0, value, sizeof(value)) ||
	    !fixed_hex(value, 16U, &base) ||
	    !field(&cursor, "length", 0, value, sizeof(value)) ||
	    !fixed_hex(value, 16U, &length) ||
	    !field(&cursor, "dlen", 0, value, sizeof(value)) ||
	    !decimal(value, 0xffffU, &dlen) ||
	    !field(&cursor, "srec", 0, value, sizeof(value)) ||
	    !decimal(value, 0xffffU, &srec) ||
	    !field(&cursor, "expected", 0, value, sizeof(value)) ||
	    !decimal(value, 0xffffU, &expected))
		return 0;
	slot = out + BE_MVP_LOG_HEADER_BYTES + seq * BE_MVP_LOG_RECORD_BYTES;
	put_le(slot, seq, 2U);
	slot[2] = (be_u8)producer;
	slot[3] = (be_u8)type;
	slot[4] = (be_u8)stream;
	slot[5] = (be_u8)object;
	slot[6] = (be_u8)repr;
	slot[7] = (be_u8)outcome;
	put_le(slot + 8, base, 8U);
	put_le(slot + 16, length, 8U);
	put_le(slot + 24, dlen, 2U);
	put_le(slot + 26, srec, 2U);
	put_le(slot + 28, expected, 2U);
	if (!field(&cursor, "digest", 0, value, sizeof(value)) ||
	    !from_hex(value, strlen(value), slot + 32, DIGEST))
		return 0;
	return *cursor == '\0';
}

/*
 * The page rendered to its block, each line within its bound, and the
 * block parsed back into a zeroed page: the page again, byte for byte.
 */
static void check_lossless(void)
{
	be_u64 count = be_mvp_log_count(page);
	be_u64 index;

	SCENARIO();
	memset(rebuilt, 0, sizeof(rebuilt));
	be_mvp_log_render_header(&line, page);
	CHECK(parse_header(rendered(), rebuilt));
	for (index = 0U; index < count; ++index) {
		be_mvp_log_render_record(&line, page, index);
		CHECK(parse_record(rendered(), rebuilt));
	}
	CHECK(memcmp(rebuilt, page, sizeof(page)) == 0);
}

/* ------------------------------------------------------------ the tests */

/* 2.2 and 2.3: every field at its offset, by its width, little-endian. */
static void test_encoding(void)
{
	static const char magic[] = "BEMVPLOG";
	struct be_mvp_log_record record;
	be_u8 scenario[DIGEST];
	be_u8 configuration[DIGEST];
	const be_u8 *slot;
	size_t index;

	SCENARIO();
	memset(page, 0xa5, sizeof(page));
	memset(registers, 0xa5, sizeof(registers));
	for (index = 0U; index < DIGEST; ++index) {
		scenario[index] = (be_u8)(0x10U + index);
		configuration[index] = (be_u8)(0x80U + index);
	}
	be_mvp_log_init(page, registers, scenario, configuration);
	CHECK(memcmp(page, magic, 8U) == 0);
	CHECK(le(page + 8, 2U) == 1U && le(page + 10, 2U) == 128U &&
	      le(page + 12, 2U) == 96U && le(page + 14, 2U) == 41U &&
	      le(page + 16, 2U) == 0U && page[18] == 0U && page[19] == 0U &&
	      le(page + 20, 2U) == 0x000bU);
	CHECK(all_zero(page + 22, 10U));
	CHECK(memcmp(page + 32, scenario, DIGEST) == 0 &&
	      memcmp(page + 64, configuration, DIGEST) == 0);
	CHECK(all_zero(page + 96, 32U) &&
	      all_zero(page + 128, PAGE_BYTES - 128U) &&
	      all_zero(registers, sizeof(registers)));
	CHECK(be_mvp_log_count(page) == 0U &&
	      be_mvp_log_state(page) == BE_MVP_LOG_OPEN);
	/* No configuration: zero (a log with policy-absent). */
	SCENARIO();
	memset(page, 0xa5, sizeof(page));
	be_mvp_log_init(page, registers, scenario, (const be_u8 *)0);
	CHECK(all_zero(page + 64, 64U) && all_zero(page + 22, 10U));
	/* A record with a value in every byte it may hold. */
	SCENARIO();
	memset(&record, 0, sizeof(record));
	record.type = BE_MVP_LOG_MEASURED;
	record.stream = 3U;
	record.object = BE_MVP_LOG_SECRET_PAGE;
	record.representation = BE_MVP_LOG_AS_PLACED;
	record.base = 0x1122334455667788U;
	record.length = 0x99aabbccddeeff01U;
	for (index = 0U; index < DIGEST; ++index)
		record.digest[index] = (be_u8)(0xe0U ^ index);
	CHECK(be_mvp_log_append(page, registers, &record) == 1);
	slot = slot_of(page, 0U);
	CHECK(le(slot + 0, 2U) == 0U && slot[2] == 0U && slot[3] == 1U &&
	      slot[4] == 3U && slot[5] == 12U && slot[6] == 0U &&
	      slot[7] == 0U);
	CHECK(bytes_are(slot + 8, 16U, "8877665544332211"
			"01ffeeddccbbaa99"));
	CHECK(le(slot + 24, 2U) == 32U && le(slot + 26, 2U) == 0U &&
	      le(slot + 28, 2U) == 0U && le(slot + 30, 2U) == 0U);
	CHECK(memcmp(slot + 32, record.digest, DIGEST) == 0 &&
	      all_zero(slot + 64, 32U));
	CHECK(be_mvp_log_count(page) == 1U && le(page + 16, 2U) == 1U &&
	      all_zero(slot_of(page, 1U), PAGE_BYTES - 128U - 96U));
	/* The sequence and each stream's own numbering (srec). */
	SCENARIO();
	record.type = BE_MVP_LOG_INFORMATIONAL;
	record.object = BE_MVP_LOG_POLICY_ABSENT;
	record.representation = BE_MVP_LOG_BUILD_RECORDED;
	record.base = record.length = 0U;
	for (index = 1U; index < 9U; ++index) {
		record.stream = (be_u32)(index % 3U);
		CHECK(be_mvp_log_append(page, registers, &record) == 1);
		slot = slot_of(page, index);
		CHECK(le(slot, 2U) == index && slot[4] == index % 3U);
	}
	/* Streams: 3 0 1 2 0 1 2 0 1; each slot counts its stream's earlier. */
	CHECK(le(slot_of(page, 1U) + 26, 2U) == 0U &&
	      le(slot_of(page, 3U) + 26, 2U) == 0U &&
	      le(slot_of(page, 4U) + 26, 2U) == 1U &&
	      le(slot_of(page, 7U) + 26, 2U) == 2U &&
	      le(slot_of(page, 8U) + 26, 2U) == 2U);
	CHECK(be_mvp_log_count(page) == 9U &&
	      all_zero(slot_of(page, 9U), PAGE_BYTES - 128U - 9U * 96U));
}

/* 2.4: each enumeration's numbers, and its names as a line prints them. */
static void test_enumerations(void)
{
	struct be_mvp_log_record record;
	char wanted[64];
	unsigned int object;

	SCENARIO();
	CHECK(BE_MVP_LOG_MEASURED == 1 && BE_MVP_LOG_INFORMATIONAL == 2 &&
	      BE_MVP_LOG_CLOSE == 3);
	CHECK(BE_MVP_LOG_MONITOR_TEXT == 0 && BE_MVP_LOG_MONITOR_RODATA == 1 &&
	      BE_MVP_LOG_MONITOR_INPUT == 2 && BE_MVP_LOG_MVP_TEXT == 3 &&
	      BE_MVP_LOG_MVP_RODATA == 4 && BE_MVP_LOG_CORE_IDENTITY == 5 &&
	      BE_MVP_LOG_CONSOLE_GRANTS == 6 &&
	      BE_MVP_LOG_CONFIGURATION_IDENTITY == 7 &&
	      BE_MVP_LOG_POLICY_IDENTITY == 8 && BE_MVP_LOG_POLICY_ABSENT == 9 &&
	      BE_MVP_LOG_KERNEL_IMAGE == 10 && BE_MVP_LOG_DEVICE_TREE == 11 &&
	      BE_MVP_LOG_SECRET_PAGE == 12 && BE_MVP_LOG_OBJECT_CLOSE == 13 &&
	      BE_MVP_LOG_OBJECTS == 14);
	CHECK(BE_MVP_LOG_AS_PLACED == 0 && BE_MVP_LOG_AS_COMPUTED == 1 &&
	      BE_MVP_LOG_BUILD_RECORDED == 2 && BE_MVP_LOG_REPR_NONE == 3);
	CHECK(BE_MVP_LOG_RECORDED == 0 && BE_MVP_LOG_GATED_PASS == 1 &&
	      BE_MVP_LOG_GATED_FAIL == 2 && BE_MVP_LOG_OUTCOME_NONE == 3);
	CHECK(BE_MVP_LOG_OPEN == 0 && BE_MVP_LOG_CLOSED == 1 &&
	      BE_MVP_LOG_OVERFLOW == 2 && BE_MVP_LOG_STREAM_CLOSE == 255U &&
	      BE_MVP_LOG_ALGORITHM == 0x000bU);
	/* Every data object's name, the close's by be_mvp_log_close(). */
	be_mvp_log_init(page, registers, registers, (const be_u8 *)0);
	memset(&record, 0, sizeof(record));
	record.type = BE_MVP_LOG_MEASURED;
	record.representation = BE_MVP_LOG_AS_COMPUTED;
	for (object = 0U; object < 13U; ++object) {
		SCENARIO();
		record.object = (enum be_mvp_log_object)object;
		CHECK(be_mvp_log_append(page, registers, &record) == 1);
		be_mvp_log_render_record(&line, page, object);
		snprintf(wanted, sizeof(wanted), " object=%s repr=as-computed ",
			 objects[object]);
		CHECK(strstr(rendered(), wanted) != (char *)0);
		CHECK(strstr(text, " type=measured stream=0 ") != (char *)0 &&
		      strstr(text, " outcome=recorded ") != (char *)0);
	}
	CHECK(be_mvp_log_close(page, 14U) == 1);
	be_mvp_log_render_record(&line, page, 13U);
	CHECK(strstr(rendered(), " type=close stream=255 object=close "
		     "repr=none outcome=none ") != (char *)0 &&
	      strstr(text, " expected=14 digest=0000") != (char *)0);
	be_mvp_log_render_header(&line, page);
	CHECK(strstr(rendered(), " count=14 state=closed alg=0x000b ") !=
	      (char *)0);
	/* A number outside its enumeration, or a corrupt magic: no line. */
	SCENARIO();
	memcpy(snapshot, page, sizeof(page));
	page[128 + 5] = 14U;
	be_mvp_log_render_record(&line, page, 0U);
	CHECK(line.overflow != 0U);
	page[128 + 5] = 0U;
	page[128 + 3] = 0U;
	be_mvp_log_render_record(&line, page, 0U);
	CHECK(line.overflow != 0U);
	page[128 + 3] = 4U;
	be_mvp_log_render_record(&line, page, 0U);
	CHECK(line.overflow != 0U);
	memcpy(page, snapshot, sizeof(page));
	page[128 + 6] = 4U;
	be_mvp_log_render_record(&line, page, 0U);
	CHECK(line.overflow != 0U);
	page[128 + 6] = 1U;
	page[128 + 7] = 4U;
	be_mvp_log_render_record(&line, page, 0U);
	CHECK(line.overflow != 0U);
	memcpy(page, snapshot, sizeof(page));
	page[18] = 3U;
	be_mvp_log_render_header(&line, page);
	CHECK(line.overflow != 0U);
	page[18] = 1U;
	page[3] = ' ';
	be_mvp_log_render_header(&line, page);
	CHECK(line.overflow != 0U);
	memcpy(page, snapshot, sizeof(page));
	be_mvp_log_render_record(&line, page, 14U);
	CHECK(line.overflow != 0U);
}

/* 2.5: the close only at the expected count; after it, nothing. */
static void test_close(void)
{
	struct be_mvp_log_record record;

	memset(&record, 0, sizeof(record));
	record.type = BE_MVP_LOG_MEASURED;
	record.stream = 1U;
	record.object = BE_MVP_LOG_CORE_IDENTITY;
	record.representation = BE_MVP_LOG_AS_COMPUTED;
	SCENARIO();
	be_mvp_log_init(page, registers, registers, (const be_u8 *)0);
	CHECK(be_mvp_log_append(page, registers, &record) == 1 &&
	      be_mvp_log_append(page, registers, &record) == 1 &&
	      be_mvp_log_append(page, registers, &record) == 1);
	memcpy(snapshot, page, sizeof(page));
	/* A count after the close other than the expected: cannot close. */
	CHECK(be_mvp_log_close(page, 5U) == 0 && be_mvp_log_close(page, 3U) ==
	      0 && be_mvp_log_close(page, 0U) == 0 &&
	      be_mvp_log_close(page, 42U) == 0);
	CHECK(memcmp(snapshot, page, sizeof(page)) == 0 &&
	      be_mvp_log_state(page) == BE_MVP_LOG_OPEN &&
	      be_mvp_log_count(page) == 3U);
	SCENARIO();
	CHECK(be_mvp_log_close(page, 4U) == 1);
	CHECK(be_mvp_log_count(page) == 4U &&
	      be_mvp_log_state(page) == BE_MVP_LOG_CLOSED);
	CHECK(bytes_are(slot_of(page, 3U), 32U,
			"03000003ff0d0303000000000000000000000000000000002000"
			"000004000000"));
	CHECK(all_zero(slot_of(page, 3U) + 32, 64U) &&
	      all_zero(slot_of(page, 4U), PAGE_BYTES - 128U - 4U * 96U));
	/* After the close: no record, no second close, no register. */
	SCENARIO();
	memcpy(snapshot, page, sizeof(page));
	memcpy(rebuilt, registers, sizeof(registers));
	CHECK(be_mvp_log_append(page, registers, &record) == 0 &&
	      be_mvp_log_close(page, 5U) == 0);
	CHECK(memcmp(snapshot, page, sizeof(page)) == 0 &&
	      memcmp(rebuilt, registers, sizeof(registers)) == 0 &&
	      be_mvp_log_state(page) == BE_MVP_LOG_CLOSED);
}

/* 2.5: the 41st slot holds only the close; a data record there overflows. */
static void test_overflow(void)
{
	struct be_mvp_log_record record;
	be_u64 index;

	memset(&record, 0, sizeof(record));
	record.type = BE_MVP_LOG_INFORMATIONAL;
	record.stream = 1U;
	record.object = BE_MVP_LOG_POLICY_ABSENT;
	record.representation = BE_MVP_LOG_BUILD_RECORDED;
	SCENARIO();
	be_mvp_log_init(page, registers, registers, (const be_u8 *)0);
	for (index = 0U; index < 40U; ++index)
		CHECK(be_mvp_log_append(page, registers, &record) == 1);
	CHECK(be_mvp_log_count(page) == 40U);
	memcpy(snapshot, page, sizeof(page));
	CHECK(be_mvp_log_append(page, registers, &record) == 0);
	CHECK(be_mvp_log_state(page) == BE_MVP_LOG_OVERFLOW &&
	      be_mvp_log_count(page) == 40U && page[18] == 2U);
	snapshot[18] = 2U;
	CHECK(memcmp(snapshot, page, sizeof(page)) == 0 &&
	      all_zero(slot_of(page, 40U), 96U + 32U));
	CHECK(be_mvp_log_close(page, 41U) == 0 &&
	      be_mvp_log_append(page, registers, &record) == 0 &&
	      be_mvp_log_state(page) == BE_MVP_LOG_OVERFLOW);
	check_lossless();
	/* A full page: 40 data records and the close in slot 40. */
	SCENARIO();
	be_mvp_log_init(page, registers, registers, (const be_u8 *)0);
	for (index = 0U; index < 40U; ++index)
		CHECK(be_mvp_log_append(page, registers, &record) == 1);
	CHECK(be_mvp_log_close(page, 41U) == 1 &&
	      be_mvp_log_count(page) == 41U &&
	      be_mvp_log_state(page) == BE_MVP_LOG_CLOSED);
	CHECK(le(slot_of(page, 40U) + 28, 2U) == 41U &&
	      all_zero(page + 4064, 32U));
	CHECK(be_mvp_log_append(page, registers, &record) == 0 &&
	      be_mvp_log_state(page) == BE_MVP_LOG_CLOSED);
	check_lossless();
}

/* 2.4 and 2.7: a record outside the enumerations is refused, unwritten. */
static void test_refused(void)
{
	struct be_mvp_log_record record;
	struct be_mvp_log_record bad;

	memset(&record, 0, sizeof(record));
	record.type = BE_MVP_LOG_MEASURED;
	record.stream = 2U;
	record.object = BE_MVP_LOG_KERNEL_IMAGE;
	record.representation = BE_MVP_LOG_AS_PLACED;
	SCENARIO();
	be_mvp_log_init(page, registers, registers, (const be_u8 *)0);
	CHECK(be_mvp_log_append(page, registers, &record) == 1);
	memcpy(snapshot, page, sizeof(page));
	memcpy(rebuilt, registers, sizeof(registers));
	bad = record;
	bad.type = BE_MVP_LOG_CLOSE;
	CHECK(be_mvp_log_append(page, registers, &bad) == 0);
	bad = record;
	bad.type = (enum be_mvp_log_type)0;
	CHECK(be_mvp_log_append(page, registers, &bad) == 0);
	bad = record;
	bad.stream = 4U;
	CHECK(be_mvp_log_append(page, registers, &bad) == 0);
	bad.stream = BE_MVP_LOG_STREAM_CLOSE;
	CHECK(be_mvp_log_append(page, registers, &bad) == 0);
	bad = record;
	bad.object = BE_MVP_LOG_OBJECT_CLOSE;
	CHECK(be_mvp_log_append(page, registers, &bad) == 0);
	bad = record;
	bad.representation = BE_MVP_LOG_REPR_NONE;
	CHECK(be_mvp_log_append(page, registers, &bad) == 0);
	CHECK(be_mvp_log_append(page, registers,
				(const struct be_mvp_log_record *)0) == 0);
	CHECK(memcmp(snapshot, page, sizeof(page)) == 0 &&
	      memcmp(rebuilt, registers, sizeof(registers)) == 0 &&
	      be_mvp_log_state(page) == BE_MVP_LOG_OPEN);
}

/* 2.9: the gate on a domain's last launch record, and only there. */
static void test_gate(void)
{
	struct be_mvp_log_record record;
	be_u8 wanted[DIGEST];

	memset(&record, 0, sizeof(record));
	record.type = BE_MVP_LOG_MEASURED;
	record.stream = 1U;
	record.object = BE_MVP_LOG_CORE_IDENTITY;
	record.representation = BE_MVP_LOG_AS_COMPUTED;
	SCENARIO();
	be_mvp_log_init(page, registers, registers, (const be_u8 *)0);
	CHECK(be_mvp_log_gate(page, registers, wanted) ==
	      BE_MVP_LOG_GATE_INVALID);
	CHECK(be_mvp_log_append(page, registers, &record) == 1);
	CHECK(be_mvp_log_gate(page, registers, registers + DIGEST) ==
	      BE_MVP_LOG_GATE_INVALID);
	record.type = BE_MVP_LOG_INFORMATIONAL;
	record.stream = 2U;
	record.object = BE_MVP_LOG_KERNEL_IMAGE;
	CHECK(be_mvp_log_append(page, registers, &record) == 1 &&
	      be_mvp_log_gate(page, registers, registers + 2U * DIGEST) ==
	      BE_MVP_LOG_GATE_INVALID);
	record.type = BE_MVP_LOG_MEASURED;
	record.object = BE_MVP_LOG_POLICY_ABSENT;
	CHECK(be_mvp_log_append(page, registers, &record) == 1 &&
	      be_mvp_log_gate(page, registers, registers + 2U * DIGEST) ==
	      BE_MVP_LOG_GATE_INVALID);
	/* Equal: gated-pass; then not again. */
	SCENARIO();
	record.object = BE_MVP_LOG_DEVICE_TREE;
	CHECK(be_mvp_log_append(page, registers, &record) == 1);
	memcpy(wanted, registers + 2U * DIGEST, DIGEST);
	CHECK(be_mvp_log_gate(page, registers, wanted) == BE_MVP_LOG_GATE_PASS);
	CHECK(slot_of(page, 3U)[7] == 1U);
	CHECK(be_mvp_log_gate(page, registers, wanted) ==
	      BE_MVP_LOG_GATE_INVALID && slot_of(page, 3U)[7] == 1U);
	/* One bit off, in the first or the last byte: gated-fail. */
	SCENARIO();
	record.stream = 3U;
	record.object = BE_MVP_LOG_SECRET_PAGE;
	CHECK(be_mvp_log_append(page, registers, &record) == 1);
	memcpy(wanted, registers + 3U * DIGEST, DIGEST);
	wanted[0] ^= 1U;
	memcpy(snapshot, page, sizeof(page));
	CHECK(be_mvp_log_gate(page, registers, wanted) == BE_MVP_LOG_GATE_FAIL);
	CHECK(slot_of(page, 4U)[7] == 2U);
	snapshot[128 + 4 * 96 + 7] = 2U;
	CHECK(memcmp(snapshot, page, sizeof(page)) == 0);
	be_mvp_log_render_record(&line, page, 4U);
	CHECK(strstr(rendered(), " outcome=gated-fail ") != (char *)0);
	SCENARIO();
	CHECK(be_mvp_log_append(page, registers, &record) == 1);
	memcpy(wanted, registers + 3U * DIGEST, DIGEST);
	wanted[DIGEST - 1U] ^= 0x80U;
	CHECK(be_mvp_log_gate(page, registers, wanted) == BE_MVP_LOG_GATE_FAIL);
	/* A closed page has no gate. */
	SCENARIO();
	CHECK(be_mvp_log_append(page, registers, &record) == 1 &&
	      be_mvp_log_close(page, 8U) == 1);
	memcpy(wanted, registers + 3U * DIGEST, DIGEST);
	CHECK(be_mvp_log_gate(page, registers, wanted) ==
	      BE_MVP_LOG_GATE_INVALID);
}

/* 2.6: R := SHA-256(R || digest) per stream, measured records only. */
static void test_registers(void)
{
	be_u8 expected[REGISTERS_BYTES];
	be_u8 both[2U * DIGEST];
	be_u8 digest[DIGEST];
	size_t index;

	SCENARIO();
	build(two_guests, ENTRIES(two_guests), 0, (const char *const *)0, 1);
	memset(expected, 0, sizeof(expected));
	for (index = 0U; index < ENTRIES(two_guests); ++index) {
		const struct entry *at = &two_guests[index];
		be_u8 *value = expected + at->stream * DIGEST;

		if (at->type != BE_MVP_LOG_MEASURED)
			continue;
		if (at->object == BE_MVP_LOG_CONSOLE_GRANTS)
			be_mvp_log_console_grants(0U, digest);
		else
			label_digest(at->label, digest);
		memcpy(both, value, DIGEST);
		memcpy(both + DIGEST, digest, DIGEST);
		be_mvp_sha256(both, sizeof(both), value);
	}
	CHECK(memcmp(expected, registers, sizeof(expected)) == 0);
	/* Without R2 stream 0 stays zero; policy-absent extends nothing. */
	CHECK(all_zero(registers, DIGEST));
	CHECK(all_zero(slot_of(page, 2U) + 32, 32U) &&
	      slot_of(page, 2U)[5] == 9U && all_zero(page + 64, 32U));
	/* Two extensions by hand against the recurrence. */
	SCENARIO();
	memset(both, 0, sizeof(both));
	label_digest("kernel-image", digest);
	memset(expected, 0, DIGEST);
	be_mvp_log_extend(expected, digest);
	memcpy(both + DIGEST, digest, DIGEST);
	be_mvp_sha256(both, sizeof(both), digest);
	CHECK(memcmp(expected, digest, DIGEST) == 0);
	check_lossless();
}

/* 2.8: one byte per domain, then SHA-256; the profile's four values. */
static void test_console_grants(void)
{
	static const char *const values[4] = {
		"96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7",
		"47dc540c94ceb704a23875c11273e16bb0b8a87aed84de911f2133568115f254",
		"b413f47d13ee2fe6c845b2ee141af81de858df4ec549a58b7970bb96645bc8d2",
		"9dcf97a184f32623d11a73124ceb99a5709b083721e878a16d78f596718ba7b2",
	};
	be_u8 digest[DIGEST];
	be_u64 grants;

	for (grants = 0U; grants < 4U; ++grants) {
		SCENARIO();
		be_mvp_log_console_grants(grants, digest);
		CHECK(bytes_are(digest, DIGEST, values[grants]));
		be_mvp_log_console_grants(grants | 0x4U, digest);
		CHECK(bytes_are(digest, DIGEST, values[grants]));
	}
}

/* 2.10 and 5.4: the te-poc example's page, registers, and lines. */
static void test_vectors(void)
{
	be_u8 digest[DIGEST];
	be_u64 index;
	size_t stream;

	SCENARIO();
	CHECK(build(example, ENTRIES(example), 1, example_registers, 1) ==
	      BE_MVP_LOG_GATE_PASS);
	be_mvp_sha256(page, sizeof(page), digest);
	CHECK(bytes_are(digest, DIGEST, example_page_sha256));
	CHECK(bytes_are(page, 128U, example_header));
	CHECK(bytes_are(slot_of(page, 9U), 96U, example_record9));
	CHECK(bytes_are(slot_of(page, 13U), 96U, example_record13));
	for (stream = 0U; stream < BE_MVP_LOG_STREAMS; ++stream)
		CHECK(bytes_are(registers + stream * DIGEST, DIGEST,
				example_registers[stream]));
	CHECK(slot_of(page, 10U)[7] == 1U && slot_of(page, 12U)[7] == 1U &&
	      slot_of(page, 9U)[7] == 0U);
	/* Every line, verbatim, each within 319 characters. */
	SCENARIO();
	be_mvp_log_render_header(&line, page);
	CHECK(strcmp(rendered(), example_lines[0]) == 0);
	for (index = 0U; index < 14U; ++index) {
		be_mvp_log_render_record(&line, page, index);
		CHECK(strcmp(rendered(), example_lines[1U + index]) == 0);
	}
	be_mvp_log_render_registers(&line, registers, 1, EXAMPLE_TICKS);
	CHECK(strcmp(rendered(), example_lines[15]) == 0);
	be_mvp_log_render_registers(&line, registers, 0, EXAMPLE_TICKS);
	CHECK(strcmp(rendered(), example_lines[16]) == 0 &&
	      strlen(text) == 303U);
	/* The barrier's ticks: 302 characters before it, at most 319. */
	SCENARIO();
	be_mvp_log_render_registers(&line, registers, 1, 0U);
	CHECK(strlen(rendered()) == 302U + 10U &&
	      strcmp(text + 302, " ticks=0x0") == 0);
	be_mvp_log_render_registers(&line, registers, 1, 0xffffffffU);
	CHECK(strlen(rendered()) == 319U &&
	      strcmp(text + 302, " ticks=0xffffffff") == 0);
	be_mvp_log_render_registers(&line, registers, 1, 0x100000000U);
	CHECK(strlen(rendered()) == 319U &&
	      strcmp(text + 302, " ticks=0xffffffff") == 0);
	be_mvp_log_render_registers(&line, registers, 1, ~(be_u64)0);
	CHECK(strcmp(rendered() + 302, " ticks=0xffffffff") == 0);
	check_lossless();
}

/* 4.6: the block rebuilds the page: a v3 page, and a failed gate's. */
static void test_lossless(void)
{
	char nominal[BE_MVP_LOG_STREAMS][2U * DIGEST + 1U];
	const char *expected[BE_MVP_LOG_STREAMS];
	size_t stream;
	size_t index;

	SCENARIO();
	CHECK(build(anchor, ENTRIES(anchor), 1, (const char *const *)0, 1) ==
	      BE_MVP_LOG_GATE_PASS);
	CHECK(be_mvp_log_count(page) == 15U &&
	      be_mvp_log_state(page) == BE_MVP_LOG_CLOSED &&
	      slot_of(page, 12U)[7] == 0U && slot_of(page, 13U)[7] == 1U &&
	      slot_of(page, 13U)[5] == 12U && slot_of(page, 13U)[4] == 3U &&
	      le(slot_of(page, 13U) + 26, 2U) == 2U &&
	      le(slot_of(page, 14U) + 28, 2U) == 15U);
	for (stream = 0U; stream < BE_MVP_LOG_STREAMS; ++stream) {
		for (index = 0U; index < DIGEST; ++index)
			snprintf(&nominal[stream][2U * index], 3U, "%02x",
				 (unsigned int)registers[stream * DIGEST +
							 index]);
		expected[stream] = nominal[stream];
	}
	check_lossless();
	/* wrong-measurement: domain 1's expected value one bit off (Q16). */
	SCENARIO();
	nominal[3][1] = "0123456789abcdef"[hex_value(nominal[3][1]) ^ 1];
	CHECK(build(anchor, ENTRIES(anchor), 1, expected, 0) ==
	      BE_MVP_LOG_GATE_FAIL);
	CHECK(be_mvp_log_state(page) == BE_MVP_LOG_OPEN &&
	      be_mvp_log_count(page) == 14U && slot_of(page, 13U)[7] == 2U &&
	      slot_of(page, 10U)[7] == 1U && slot_of(page, 12U)[7] == 0U &&
	      all_zero(slot_of(page, 14U), PAGE_BYTES - 128U - 14U * 96U));
	be_mvp_log_render_header(&line, page);
	CHECK(strstr(rendered(), " count=14 state=open ") != (char *)0);
	check_lossless();
}

int main(void)
{
	test_encoding();
	test_enumerations();
	test_close();
	test_overflow();
	test_refused();
	test_gate();
	test_registers();
	test_console_grants();
	test_vectors();
	test_lossless();
	printf("BE_MVP_LOG_CHECK: PASS\n");
	printf("BE_MVP_LOG_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_MVP_LOG_CHECK: assertions=%lu\n", assertions);
	return 0;
}
