// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the Beryllium log profile version 1 (mvp/docs/log-profile.md;
 *          mvp-log.h): the page's fields by width at their offsets, the
 *          append, the gate, the close, the registers' recurrence, the
 *          console grants' serialization, and the BE_MVP:19 and
 *          BE_MVP:20 lines.
 * Trust:   restricted C with explicit bounded loops; no CSR, SBI call, or
 *          I/O. Every byte of the page is written by one of these
 *          functions, little-endian, at its fixed offset.
 * Scope:   the MVP line (M9); see mvp-log.h.
 */
#include "mvp-log.h"

#define PAGE		BE_MVP_LOG_PAGE_BYTES
#define DIGEST		BE_MVP_LOG_DIGEST_BYTES

/* Inert: in its own section, which src/mvp-monitor.lds keeps. */
const be_u8 be_mvp_log_canary[BE_MVP_LOG_CANARY_BYTES]
	__attribute__((section(".rodata.be_mvp_log_canary"))) = {
	0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
	0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
};

static const char *const type_names[BE_MVP_LOG_CLOSE + 1] = {
	[BE_MVP_LOG_MEASURED] = "measured",
	[BE_MVP_LOG_INFORMATIONAL] = "informational",
	[BE_MVP_LOG_CLOSE] = "close",
};
static const char *const object_names[BE_MVP_LOG_OBJECTS] = {
	[BE_MVP_LOG_MONITOR_TEXT] = "monitor-text",
	[BE_MVP_LOG_MONITOR_RODATA] = "monitor-rodata",
	[BE_MVP_LOG_MONITOR_INPUT] = "monitor-input",
	[BE_MVP_LOG_MVP_TEXT] = "mvp-text",
	[BE_MVP_LOG_MVP_RODATA] = "mvp-rodata",
	[BE_MVP_LOG_CORE_IDENTITY] = "core-identity",
	[BE_MVP_LOG_CONSOLE_GRANTS] = "console-grants",
	[BE_MVP_LOG_CONFIGURATION_IDENTITY] = "configuration-identity",
	[BE_MVP_LOG_POLICY_IDENTITY] = "policy-identity",
	[BE_MVP_LOG_POLICY_ABSENT] = "policy-absent",
	[BE_MVP_LOG_KERNEL_IMAGE] = "kernel-image",
	[BE_MVP_LOG_DEVICE_TREE] = "device-tree",
	[BE_MVP_LOG_SECRET_PAGE] = "secret-page",
	[BE_MVP_LOG_OBJECT_CLOSE] = "close",
};
static const char *const repr_names[BE_MVP_LOG_REPRS] = {
	[BE_MVP_LOG_AS_PLACED] = "as-placed",
	[BE_MVP_LOG_AS_COMPUTED] = "as-computed",
	[BE_MVP_LOG_BUILD_RECORDED] = "build-recorded",
	[BE_MVP_LOG_REPR_NONE] = "none",
};
static const char *const outcome_names[BE_MVP_LOG_OUTCOMES] = {
	[BE_MVP_LOG_RECORDED] = "recorded",
	[BE_MVP_LOG_GATED_PASS] = "gated-pass",
	[BE_MVP_LOG_GATED_FAIL] = "gated-fail",
	[BE_MVP_LOG_OUTCOME_NONE] = "none",
};
static const char *const state_names[BE_MVP_LOG_STATES] = {
	[BE_MVP_LOG_OPEN] = "open",
	[BE_MVP_LOG_CLOSED] = "closed",
	[BE_MVP_LOG_OVERFLOW] = "overflow",
};

/* Little-endian fields of 1, 2, and 8 bytes at a fixed offset. */
static void put(be_u8 *at, be_u64 value, be_u64 width)
{
	be_u64 index;

	for (index = 0U; index < width; ++index)
		at[index] = (be_u8)(value >> (8U * index));
}

static be_u64 get(const be_u8 *at, be_u64 width)
{
	be_u64 value = 0U;
	be_u64 index;

	for (index = width; index > 0U; --index)
		value = (value << 8) | at[index - 1U];
	return value;
}

static void copy(be_u8 *to, const be_u8 *from, be_u64 bytes)
{
	be_u64 index;

	for (index = 0U; index < bytes; ++index)
		to[index] = from != (const be_u8 *)0 ? from[index] : 0U;
}

static be_u8 *record_at(be_u8 *page, be_u64 index)
{
	return page + BE_MVP_LOG_HEADER_BYTES + index * BE_MVP_LOG_RECORD_BYTES;
}

static const be_u8 *record_of(const be_u8 *page, be_u64 index)
{
	return page + BE_MVP_LOG_HEADER_BYTES + index * BE_MVP_LOG_RECORD_BYTES;
}

void be_mvp_log_init(be_u8 *page, be_u8 *registers, const be_u8 *scenario,
		     const be_u8 *configuration)
{
	static const char magic[] = BE_MVP_LOG_MAGIC;
	be_u64 index;

	copy(page, (const be_u8 *)0, PAGE);
	copy(registers, (const be_u8 *)0, BE_MVP_LOG_REGISTERS_BYTES);
	for (index = 0U; index < BE_MVP_LOG_MAGIC_BYTES; ++index)
		page[BE_MVP_LOG_AT_MAGIC + index] = (be_u8)magic[index];
	put(page + BE_MVP_LOG_AT_VERSION, BE_MVP_LOG_VERSION, 2U);
	put(page + BE_MVP_LOG_AT_HLEN, BE_MVP_LOG_HEADER_BYTES, 2U);
	put(page + BE_MVP_LOG_AT_RLEN, BE_MVP_LOG_RECORD_BYTES, 2U);
	put(page + BE_MVP_LOG_AT_CAPACITY, BE_MVP_LOG_CAPACITY, 2U);
	put(page + BE_MVP_LOG_AT_COUNT, 0U, 2U);
	put(page + BE_MVP_LOG_AT_STATE, BE_MVP_LOG_OPEN, 1U);
	put(page + BE_MVP_LOG_AT_ALGORITHM, BE_MVP_LOG_ALGORITHM, 2U);
	copy(page + BE_MVP_LOG_AT_SCENARIO, scenario, DIGEST);
	copy(page + BE_MVP_LOG_AT_CONFIG, configuration, DIGEST);
}

void be_mvp_log_extend(be_u8 *value, const be_u8 *digest)
{
	be_u8 both[2U * DIGEST];

	copy(both, value, DIGEST);
	copy(both + DIGEST, digest, DIGEST);
	be_mvp_sha256(both, sizeof(both), value);
}

be_u64 be_mvp_log_count(const be_u8 *page)
{
	return get(page + BE_MVP_LOG_AT_COUNT, 2U);
}

be_u64 be_mvp_log_state(const be_u8 *page)
{
	return get(page + BE_MVP_LOG_AT_STATE, 1U);
}

/* The earlier records of @stream before slot @count (2.3, srec). */
static be_u64 stream_records(const be_u8 *page, be_u64 count, be_u64 stream)
{
	be_u64 found = 0U;
	be_u64 index;

	for (index = 0U; index < count && index < BE_MVP_LOG_CAPACITY; ++index)
		found += get(record_of(page, index) + BE_MVP_LOG_AT_STREAM,
			     1U) == stream;
	return found;
}

int be_mvp_log_append(be_u8 *page, be_u8 *registers,
		      const struct be_mvp_log_record *record)
{
	be_u64 count = be_mvp_log_count(page);
	be_u8 *slot;

	if (be_mvp_log_state(page) != BE_MVP_LOG_OPEN ||
	    record == (const struct be_mvp_log_record *)0 ||
	    (record->type != BE_MVP_LOG_MEASURED &&
	     record->type != BE_MVP_LOG_INFORMATIONAL) ||
	    record->stream >= BE_MVP_LOG_STREAMS ||
	    (unsigned int)record->object >=
		    (unsigned int)BE_MVP_LOG_OBJECT_CLOSE ||
	    (unsigned int)record->representation >=
		    (unsigned int)BE_MVP_LOG_REPR_NONE)
		return 0;
	if (count >= BE_MVP_LOG_CAPACITY - 1U) {
		put(page + BE_MVP_LOG_AT_STATE, BE_MVP_LOG_OVERFLOW, 1U);
		return 0;
	}
	slot = record_at(page, count);
	copy(slot, (const be_u8 *)0, BE_MVP_LOG_RECORD_BYTES);
	put(slot + BE_MVP_LOG_AT_SEQ, count, 2U);
	put(slot + BE_MVP_LOG_AT_PRODUCER, 0U, 1U);
	put(slot + BE_MVP_LOG_AT_TYPE, (be_u64)record->type, 1U);
	put(slot + BE_MVP_LOG_AT_STREAM, record->stream, 1U);
	put(slot + BE_MVP_LOG_AT_OBJECT, (be_u64)record->object, 1U);
	put(slot + BE_MVP_LOG_AT_REPR, (be_u64)record->representation, 1U);
	put(slot + BE_MVP_LOG_AT_OUTCOME, BE_MVP_LOG_RECORDED, 1U);
	put(slot + BE_MVP_LOG_AT_BASE, record->base, 8U);
	put(slot + BE_MVP_LOG_AT_LENGTH, record->length, 8U);
	put(slot + BE_MVP_LOG_AT_DLEN, DIGEST, 2U);
	put(slot + BE_MVP_LOG_AT_SREC,
	    stream_records(page, count, record->stream), 2U);
	put(slot + BE_MVP_LOG_AT_EXPECTED, 0U, 2U);
	copy(slot + BE_MVP_LOG_AT_DIGEST, record->digest, DIGEST);
	put(page + BE_MVP_LOG_AT_COUNT, count + 1U, 2U);
	if (record->type == BE_MVP_LOG_MEASURED)
		be_mvp_log_extend(registers + record->stream * DIGEST,
				  record->digest);
	return 1;
}

enum be_mvp_log_gate_result be_mvp_log_gate(be_u8 *page,
					    const be_u8 *registers,
					    const be_u8 *expected)
{
	be_u64 count = be_mvp_log_count(page);
	be_u64 differ = 0U;
	be_u64 stream;
	be_u64 object;
	be_u64 index;
	be_u8 *slot;

	if (be_mvp_log_state(page) != BE_MVP_LOG_OPEN || count == 0U ||
	    count > BE_MVP_LOG_CAPACITY)
		return BE_MVP_LOG_GATE_INVALID;
	slot = record_at(page, count - 1U);
	stream = get(slot + BE_MVP_LOG_AT_STREAM, 1U);
	object = get(slot + BE_MVP_LOG_AT_OBJECT, 1U);
	if (get(slot + BE_MVP_LOG_AT_TYPE, 1U) != BE_MVP_LOG_MEASURED ||
	    get(slot + BE_MVP_LOG_AT_OUTCOME, 1U) != BE_MVP_LOG_RECORDED ||
	    stream < BE_MVP_LOG_STREAM_DOMAIN0 ||
	    stream >= BE_MVP_LOG_STREAMS || object < BE_MVP_LOG_KERNEL_IMAGE ||
	    object > BE_MVP_LOG_SECRET_PAGE)
		return BE_MVP_LOG_GATE_INVALID;
	for (index = 0U; index < DIGEST; ++index)
		differ |= (be_u64)(registers[stream * DIGEST + index] ^
				   expected[index]);
	put(slot + BE_MVP_LOG_AT_OUTCOME, differ == 0U ?
	    BE_MVP_LOG_GATED_PASS : BE_MVP_LOG_GATED_FAIL, 1U);
	return differ == 0U ? BE_MVP_LOG_GATE_PASS : BE_MVP_LOG_GATE_FAIL;
}

int be_mvp_log_close(be_u8 *page, be_u64 expected_count)
{
	be_u64 count = be_mvp_log_count(page);
	be_u8 *slot;

	if (be_mvp_log_state(page) != BE_MVP_LOG_OPEN ||
	    count >= BE_MVP_LOG_CAPACITY || count + 1U != expected_count)
		return 0;
	slot = record_at(page, count);
	copy(slot, (const be_u8 *)0, BE_MVP_LOG_RECORD_BYTES);
	put(slot + BE_MVP_LOG_AT_SEQ, count, 2U);
	put(slot + BE_MVP_LOG_AT_TYPE, BE_MVP_LOG_CLOSE, 1U);
	put(slot + BE_MVP_LOG_AT_STREAM, BE_MVP_LOG_STREAM_CLOSE, 1U);
	put(slot + BE_MVP_LOG_AT_OBJECT, BE_MVP_LOG_OBJECT_CLOSE, 1U);
	put(slot + BE_MVP_LOG_AT_REPR, BE_MVP_LOG_REPR_NONE, 1U);
	put(slot + BE_MVP_LOG_AT_OUTCOME, BE_MVP_LOG_OUTCOME_NONE, 1U);
	put(slot + BE_MVP_LOG_AT_DLEN, DIGEST, 2U);
	put(slot + BE_MVP_LOG_AT_EXPECTED, expected_count, 2U);
	put(page + BE_MVP_LOG_AT_COUNT, count + 1U, 2U);
	put(page + BE_MVP_LOG_AT_STATE, BE_MVP_LOG_CLOSED, 1U);
	return 1;
}

void be_mvp_log_console_grants(be_u64 grants, be_u8 *digest)
{
	be_u8 bytes[BE_MVP_DOMAINS];
	be_u64 domain;

	for (domain = 0U; domain < BE_MVP_DOMAINS; ++domain)
		bytes[domain] = (be_u8)((grants >> domain) & 1U);
	be_mvp_sha256(bytes, sizeof(bytes), digest);
}

/* ------------------------------------------------------------- the lines */

static const char hex_digits[] = "0123456789abcdef";

/* "0x" and exactly @digits lower-case hex digits of @value. */
static void put_hex(struct be_mvp_line *line, be_u64 value, be_u64 digits)
{
	char digit[2] = { '\0', '\0' };
	be_u64 index;

	be_mvp_line_text(line, "0x");
	for (index = digits; index > 0U; --index) {
		digit[0] = hex_digits[(value >> (4U * (index - 1U))) & 0xfU];
		be_mvp_line_text(line, digit);
	}
}

/* @bytes as lower-case hex digits, two per byte, in storage order. */
static void put_bytes(struct be_mvp_line *line, const be_u8 *bytes,
		      be_u64 count)
{
	char pair[3] = { '\0', '\0', '\0' };
	be_u64 index;

	for (index = 0U; index < count; ++index) {
		pair[0] = hex_digits[bytes[index] >> 4];
		pair[1] = hex_digits[bytes[index] & 0xfU];
		be_mvp_line_text(line, pair);
	}
}

/* " @name=" and a decimal. */
static void put_decimal(struct be_mvp_line *line, const char *name,
			be_u64 value)
{
	be_mvp_line_text(line, name);
	be_mvp_line_decimal(line, value);
}

/* @value's name from @names, or an unusable line for none. */
static void put_name(struct be_mvp_line *line, const char *name,
		     const char *const *names, be_u64 count, be_u64 value)
{
	be_mvp_line_text(line, name);
	be_mvp_line_text(line, value < count ? names[value] : (const char *)0);
}

void be_mvp_log_render_header(struct be_mvp_line *line, const be_u8 *page)
{
	char letter[2] = { '\0', '\0' };
	be_u64 index;

	be_mvp_line_reset(line);
	be_mvp_line_text(line, "BE_MVP:19 LOG header magic=");
	for (index = 0U; index < BE_MVP_LOG_MAGIC_BYTES; ++index) {
		letter[0] = (char)page[BE_MVP_LOG_AT_MAGIC + index];
		be_mvp_line_text(line, page[BE_MVP_LOG_AT_MAGIC + index] > 0x20U &&
				 page[BE_MVP_LOG_AT_MAGIC + index] < 0x7fU ?
				 letter : (const char *)0);
	}
	put_decimal(line, " version=", get(page + BE_MVP_LOG_AT_VERSION, 2U));
	put_decimal(line, " hlen=", get(page + BE_MVP_LOG_AT_HLEN, 2U));
	put_decimal(line, " rlen=", get(page + BE_MVP_LOG_AT_RLEN, 2U));
	put_decimal(line, " capacity=", get(page + BE_MVP_LOG_AT_CAPACITY, 2U));
	put_decimal(line, " count=", be_mvp_log_count(page));
	put_name(line, " state=", state_names, BE_MVP_LOG_STATES,
		 be_mvp_log_state(page));
	be_mvp_line_text(line, " alg=");
	put_hex(line, get(page + BE_MVP_LOG_AT_ALGORITHM, 2U), 4U);
	be_mvp_line_text(line, " scenario=");
	put_bytes(line, page + BE_MVP_LOG_AT_SCENARIO, DIGEST);
	be_mvp_line_text(line, " config=");
	put_bytes(line, page + BE_MVP_LOG_AT_CONFIG, DIGEST);
}

void be_mvp_log_render_record(struct be_mvp_line *line, const be_u8 *page,
			      be_u64 index)
{
	const be_u8 *slot;
	be_u64 type;

	be_mvp_line_reset(line);
	if (index >= be_mvp_log_count(page) || index >= BE_MVP_LOG_CAPACITY) {
		be_mvp_line_text(line, (const char *)0);
		return;
	}
	slot = record_of(page, index);
	type = get(slot + BE_MVP_LOG_AT_TYPE, 1U);
	be_mvp_line_text(line, "BE_MVP:19 LOG record");
	put_decimal(line, " seq=", get(slot + BE_MVP_LOG_AT_SEQ, 2U));
	put_decimal(line, " producer=",
		    get(slot + BE_MVP_LOG_AT_PRODUCER, 1U));
	put_name(line, " type=", type_names, BE_MVP_LOG_CLOSE + 1U,
		 type != 0U ? type : BE_MVP_LOG_CLOSE + 1U);
	put_decimal(line, " stream=", get(slot + BE_MVP_LOG_AT_STREAM, 1U));
	put_name(line, " object=", object_names, BE_MVP_LOG_OBJECTS,
		 get(slot + BE_MVP_LOG_AT_OBJECT, 1U));
	put_name(line, " repr=", repr_names, BE_MVP_LOG_REPRS,
		 get(slot + BE_MVP_LOG_AT_REPR, 1U));
	put_name(line, " outcome=", outcome_names, BE_MVP_LOG_OUTCOMES,
		 get(slot + BE_MVP_LOG_AT_OUTCOME, 1U));
	be_mvp_line_text(line, " base=");
	put_hex(line, get(slot + BE_MVP_LOG_AT_BASE, 8U), 16U);
	be_mvp_line_text(line, " length=");
	put_hex(line, get(slot + BE_MVP_LOG_AT_LENGTH, 8U), 16U);
	put_decimal(line, " dlen=", get(slot + BE_MVP_LOG_AT_DLEN, 2U));
	put_decimal(line, " srec=", get(slot + BE_MVP_LOG_AT_SREC, 2U));
	put_decimal(line, " expected=", get(slot + BE_MVP_LOG_AT_EXPECTED, 2U));
	be_mvp_line_text(line, " digest=");
	put_bytes(line, slot + BE_MVP_LOG_AT_DIGEST, DIGEST);
}

void be_mvp_log_render_registers(struct be_mvp_line *line,
				 const be_u8 *registers, int barrier,
				 be_u64 ticks)
{
	static const char *const names[BE_MVP_LOG_STREAMS] = {
		" r0=", " r1=", " r2=", " r3=",
	};
	be_u64 stream;

	be_mvp_line_reset(line);
	be_mvp_line_text(line, barrier != 0 ? "BE_MVP:20 REGISTERS at=barrier" :
			 "BE_MVP:20 REGISTERS at=terminal");
	for (stream = 0U; stream < BE_MVP_LOG_STREAMS; ++stream) {
		be_mvp_line_text(line, names[stream]);
		put_bytes(line, registers + stream * DIGEST, DIGEST);
	}
	if (barrier != 0) {
		be_mvp_line_text(line, " ticks=");
		be_mvp_line_hex(line, ticks > 0xffffffffU ? 0xffffffffU : ticks);
	}
}
