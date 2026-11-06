/* SPDX-License-Identifier: GPL-3.0-only */
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: the MVP's measurement log, the Beryllium log profile version 1
 *          (mvp/docs/log-profile.md, sections 2 and 4; planning/
 *          mvp-m9-plan.md, D-1): the 4 KiB log page hart 0 keeps, its
 *          128-byte header and 41 records of 96 bytes, each field written
 *          and read by its width at its fixed offset, little-endian, never
 *          a C structure's native layout; the four 32-byte registers
 *          beside it, one per stream, each extended R := SHA-256(R ||
 *          digest) by its stream's measured records only; the close, which
 *          only the image's expected count admits; each domain's launch
 *          gate on its last launch record; the console grants'
 *          serialization (2.8); and the rendering of the page and the
 *          registers as the BE_MVP:19 LOG and BE_MVP:20 REGISTERS lines
 *          into hart 0's line builder (section 4).
 *          What the registers bind (2.6): each register commits, under the
 *          hash assumption, to its stream's ordered sequence of measured
 *          digests and to nothing else: not to a record's object, range,
 *          type, or outcome, not to the header or the informational
 *          records, and not to the interleaving across streams; those are
 *          bound by the capture checker's field-by-field comparison with
 *          the image's reference manifest, and the close is structural,
 *          not cryptographic. They are registers in hart 0's memory, never
 *          PCRs, and the log is a local identity, not attestation.
 * Trust:   restricted C with explicit bounded loops: no CSR, SBI call, or
 *          I/O; it reads and writes only the page, the registers, and the
 *          line it is given. Hart 0 alone calls it, before any domain hart
 *          starts (I19).
 * Scope:   the MVP line (M9): two domains, four streams, SHA-256 only.
 */

#ifndef BE_MVP_LOG_H
#define BE_MVP_LOG_H

#include "mvp.h"
#include "mvp-sha256.h"

/* The page (2.2, 2.3): version 1, its sizes, and its one algorithm. */
#define BE_MVP_LOG_VERSION		1U
#define BE_MVP_LOG_PAGE_BYTES		4096U
#define BE_MVP_LOG_HEADER_BYTES		128U
#define BE_MVP_LOG_RECORD_BYTES		96U
#define BE_MVP_LOG_CAPACITY		41U
#define BE_MVP_LOG_ALGORITHM		0x000bU
#define BE_MVP_LOG_DIGEST_BYTES		32U
#define BE_MVP_LOG_MAGIC		"BEMVPLOG"
#define BE_MVP_LOG_MAGIC_BYTES		8U
/* The registers (2.6): one per stream, r0 to r3, in 128 bytes. */
#define BE_MVP_LOG_STREAMS		4U
#define BE_MVP_LOG_REGISTERS_BYTES	128U
/* The close's stream (2.4), and the first domain stream (2 + domain). */
#define BE_MVP_LOG_STREAM_CLOSE		0xffU
#define BE_MVP_LOG_STREAM_DOMAIN0	2U

/* The header's fields (2.2): offset, then width in the comment. */
#define BE_MVP_LOG_AT_MAGIC		0U	/* 8, ASCII */
#define BE_MVP_LOG_AT_VERSION		8U	/* 2 */
#define BE_MVP_LOG_AT_HLEN		10U	/* 2 */
#define BE_MVP_LOG_AT_RLEN		12U	/* 2 */
#define BE_MVP_LOG_AT_CAPACITY		14U	/* 2 */
#define BE_MVP_LOG_AT_COUNT		16U	/* 2 */
#define BE_MVP_LOG_AT_STATE		18U	/* 1 */
#define BE_MVP_LOG_AT_ALGORITHM		20U	/* 2 */
#define BE_MVP_LOG_AT_SCENARIO		32U	/* 32 */
#define BE_MVP_LOG_AT_CONFIG		64U	/* 32 */
/* A record's fields (2.3), from the record's own offset 128 + 96 i. */
#define BE_MVP_LOG_AT_SEQ		0U	/* 2 */
#define BE_MVP_LOG_AT_PRODUCER		2U	/* 1 */
#define BE_MVP_LOG_AT_TYPE		3U	/* 1 */
#define BE_MVP_LOG_AT_STREAM		4U	/* 1 */
#define BE_MVP_LOG_AT_OBJECT		5U	/* 1 */
#define BE_MVP_LOG_AT_REPR		6U	/* 1 */
#define BE_MVP_LOG_AT_OUTCOME		7U	/* 1 */
#define BE_MVP_LOG_AT_BASE		8U	/* 8 */
#define BE_MVP_LOG_AT_LENGTH		16U	/* 8 */
#define BE_MVP_LOG_AT_DLEN		24U	/* 2 */
#define BE_MVP_LOG_AT_SREC		26U	/* 2 */
#define BE_MVP_LOG_AT_EXPECTED		28U	/* 2 */
#define BE_MVP_LOG_AT_DIGEST		32U	/* 32 */

/* The enumerations (2.4): the page holds the number, a line the name. */
enum be_mvp_log_type {
	BE_MVP_LOG_MEASURED = 1,
	BE_MVP_LOG_INFORMATIONAL = 2,
	BE_MVP_LOG_CLOSE = 3,
};

enum be_mvp_log_object {
	BE_MVP_LOG_MONITOR_TEXT = 0,
	BE_MVP_LOG_MONITOR_RODATA,
	BE_MVP_LOG_MONITOR_INPUT,
	BE_MVP_LOG_MVP_TEXT,
	BE_MVP_LOG_MVP_RODATA,
	BE_MVP_LOG_CORE_IDENTITY,
	BE_MVP_LOG_CONSOLE_GRANTS,
	BE_MVP_LOG_CONFIGURATION_IDENTITY,
	BE_MVP_LOG_POLICY_IDENTITY,
	BE_MVP_LOG_POLICY_ABSENT,
	BE_MVP_LOG_KERNEL_IMAGE,
	BE_MVP_LOG_DEVICE_TREE,
	BE_MVP_LOG_SECRET_PAGE,
	BE_MVP_LOG_OBJECT_CLOSE,
	BE_MVP_LOG_OBJECTS,
};

enum be_mvp_log_repr {
	BE_MVP_LOG_AS_PLACED = 0,
	BE_MVP_LOG_AS_COMPUTED,
	BE_MVP_LOG_BUILD_RECORDED,
	BE_MVP_LOG_REPR_NONE,
	BE_MVP_LOG_REPRS,
};

enum be_mvp_log_outcome {
	BE_MVP_LOG_RECORDED = 0,
	BE_MVP_LOG_GATED_PASS,
	BE_MVP_LOG_GATED_FAIL,
	BE_MVP_LOG_OUTCOME_NONE,
	BE_MVP_LOG_OUTCOMES,
};

enum be_mvp_log_state {
	BE_MVP_LOG_OPEN = 0,
	BE_MVP_LOG_CLOSED,
	BE_MVP_LOG_OVERFLOW,
	BE_MVP_LOG_STATES,
};

/**
 * enum be_mvp_log_gate_result - one domain's launch gate (2.9)
 * @BE_MVP_LOG_GATE_PASS: the register equals the expected value; the
 *                        record's outcome is now gated-pass
 * @BE_MVP_LOG_GATE_FAIL: they differ; the outcome is now gated-fail
 * @BE_MVP_LOG_GATE_INVALID: the page's last record is not an open log's
 *                           recorded measured launch record of a domain
 *                           stream; nothing is written
 */
enum be_mvp_log_gate_result {
	BE_MVP_LOG_GATE_PASS = 0,
	BE_MVP_LOG_GATE_FAIL,
	BE_MVP_LOG_GATE_INVALID,
};

/**
 * struct be_mvp_log_record - one data record to append (2.3, 2.7)
 * @type: measured or informational; the close is be_mvp_log_close()'s
 * @stream: 0 to 3
 * @object: an object of 2.4 other than the close
 * @representation: as-placed, as-computed, or build-recorded
 * @base: the HPA of the first byte hashed; 0 unless as-placed
 * @length: the bytes hashed; 0 unless as-placed
 * @digest: the record's digest; zero for policy-absent
 *
 * An argument only: the page's bytes are written field by field from it.
 */
struct be_mvp_log_record {
	enum be_mvp_log_type type;
	be_u32 stream;
	enum be_mvp_log_object object;
	enum be_mvp_log_repr representation;
	be_u64 base;
	be_u64 length;
	be_u8 digest[BE_MVP_LOG_DIGEST_BYTES];
};

/**
 * struct be_mvp_log_constants - an image's pre-link log constants
 * @scenario: the generator's scenario_sha256 (the header's scenario)
 * @configuration: the authority report's configuration identity, zero
 *                 for an image whose log holds policy-absent
 * @policy: the report's policy identity, zero likewise
 * @launch: each domain's expected launch register (2.6), zero in a probe
 * @count: the image's expected count, the close included (2.5, 3.1)
 * @sequence: the image's record sequence, 1 to 3 for v1 to v3, 4 for a
 *            probe (3.1)
 * @r2: 1 when the image logs the five R2 ranges, 0 when R2 is dropped
 *      (Q4)
 *
 * tools/gen-scenario.py writes every value into the scenario's header
 * before the link (planning/mvp-m9-plan.md, D-3); hart 0 reads them, and
 * tests/check-image.py finds them in .mvp.rodata and matches them to the
 * image's expectation. Its layout is fixed below; the image checker reads
 * it by these offsets.
 */
struct be_mvp_log_constants {
	be_u8 scenario[BE_MVP_LOG_DIGEST_BYTES];
	be_u8 configuration[BE_MVP_LOG_DIGEST_BYTES];
	be_u8 policy[BE_MVP_LOG_DIGEST_BYTES];
	be_u8 launch[BE_MVP_DOMAINS][BE_MVP_LOG_DIGEST_BYTES];
	be_u32 count;
	be_u32 sequence;
	be_u32 r2;
};

_Static_assert(__builtin_offsetof(struct be_mvp_log_constants, launch) ==
	       96U &&
	       __builtin_offsetof(struct be_mvp_log_constants, count) == 160U &&
	       __builtin_offsetof(struct be_mvp_log_constants, sequence) ==
	       164U &&
	       __builtin_offsetof(struct be_mvp_log_constants, r2) == 168U &&
	       sizeof(struct be_mvp_log_constants) == 172U,
	       "the image checker reads the log constants at these offsets");
_Static_assert(BE_MVP_LOG_HEADER_BYTES + BE_MVP_LOG_CAPACITY *
	       BE_MVP_LOG_RECORD_BYTES + 32U == BE_MVP_LOG_PAGE_BYTES,
	       "41 records fill the page but its last 32 bytes (2.3)");
_Static_assert(BE_MVP_DOMAINS == 2U &&
	       BE_MVP_LOG_STREAMS * BE_MVP_LOG_DIGEST_BYTES ==
	       BE_MVP_LOG_REGISTERS_BYTES &&
	       BE_MVP_LOG_DIGEST_BYTES == BE_MVP_SHA256_BYTES,
	       "four 32-byte registers: two domains, SHA-256");

/**
 * be_mvp_log_canary - an inert 16-byte constant in the MVP region's
 * constants (planning/mvp-m9-plan.md, D-4)
 *
 * No code refers to it, and nothing the run does depends on it. It lies
 * inside the log's mvp-rodata range, so that the self-report-flip variant
 * (tools/flip-canary.py), which flips one of its bits in the built image
 * after the link, changes that range's bytes and nothing else. The linker
 * script keeps it; the image checker requires it in .mvp.rodata and
 * referred to by nothing.
 */
#define BE_MVP_LOG_CANARY_BYTES		16U
extern const be_u8 be_mvp_log_canary[BE_MVP_LOG_CANARY_BYTES];

/**
 * be_mvp_log_init - start an empty open log (2.2)
 * @page: %BE_MVP_LOG_PAGE_BYTES bytes, every one written: the header's
 *        fields, count 0, state open, and every other byte zero
 * @registers: %BE_MVP_LOG_REGISTERS_BYTES bytes, set to zero
 * @scenario: the header's scenario digest, 32 bytes
 * @configuration: the header's configuration identity, 32 bytes, or a
 *                 null pointer for zero (a log with policy-absent)
 */
void be_mvp_log_init(be_u8 *page, be_u8 *registers, const be_u8 *scenario,
		     const be_u8 *configuration);

/**
 * be_mvp_log_extend - one register's extension (2.6)
 * @value: the register's 32 bytes, R, replaced by SHA-256(R || @digest)
 * @digest: 32 bytes
 */
void be_mvp_log_extend(be_u8 *value, const be_u8 *digest);

/**
 * be_mvp_log_append - append one data record (2.5)
 * @page: an initialized page
 * @registers: its registers
 * @record: the record: measured or informational, stream 0 to 3, an
 *          object other than the close, a representation other than none
 *
 * Writes slot count at offset 128 + 96 count, field by field: the
 * sequence (the slot), producer 0, the record's type, stream, object, and
 * representation, outcome recorded, its base and length, digest length
 * 32, the per-stream record number (the earlier records of its stream),
 * expected count 0, the digest, and the reserved bytes zero; then adds 1
 * to count, and extends @record's stream's register with its digest when
 * it is measured.
 *
 * Return: 1; or 0, writing nothing, for a page that is not open, a record
 *         outside the enumerations, or a count of capacity less one or
 *         more, where only the close may follow: the state then becomes
 *         overflow and count stays.
 */
int be_mvp_log_append(be_u8 *page, be_u8 *registers,
		      const struct be_mvp_log_record *record);

/**
 * be_mvp_log_gate - a domain's launch gate on its last launch record (2.9)
 * @page: an open page whose last record is the domain's last launch
 *        record: measured, recorded, a kernel image, device tree, or
 *        secret page of stream 2 or 3
 * @registers: its registers
 * @expected: the image's expected launch register for that stream, 32
 *            bytes
 *
 * Compares the stream's register with @expected over all 32 bytes and
 * sets the record's outcome to gated-pass or gated-fail.
 *
 * Return: %BE_MVP_LOG_GATE_PASS, %BE_MVP_LOG_GATE_FAIL, or
 *         %BE_MVP_LOG_GATE_INVALID, which writes nothing.
 */
enum be_mvp_log_gate_result be_mvp_log_gate(be_u8 *page,
					    const be_u8 *registers,
					    const be_u8 *expected);

/**
 * be_mvp_log_close - append the close (2.5)
 * @page: an initialized page
 * @expected_count: the image's expected count, the close included
 *
 * Only when the page is open and count + 1 equals @expected_count: writes
 * the close at slot count (type close, stream 255, object close,
 * representation and outcome none, base, length, per-stream number, and
 * digest zero, digest length 32, expected count @expected_count), adds 1
 * to count, and sets the state to closed. Otherwise the page cannot close
 * and nothing is written.
 *
 * Return: 1 when closed, else 0.
 */
int be_mvp_log_close(be_u8 *page, be_u64 expected_count);

/**
 * be_mvp_log_count - the page's count
 * @page: a page
 *
 * Return: the count field.
 */
be_u64 be_mvp_log_count(const be_u8 *page);

/**
 * be_mvp_log_state - the page's state
 * @page: a page
 *
 * Return: the state field.
 */
be_u64 be_mvp_log_state(const be_u8 *page);

/**
 * be_mvp_log_console_grants - the console-grants record's digest (2.8)
 * @grants: bit d set when the sealed configuration grants domain d
 *          console input
 * @digest: SHA-256 of one byte per domain in domain order, 0x01 for a
 *          grant and 0x00 otherwise
 */
void be_mvp_log_console_grants(be_u64 grants, be_u8 *digest);

/**
 * be_mvp_log_render_header - the block's first line (4.2)
 * @line: reset, then `BE_MVP:19 LOG header magic=... config=...`, no line
 *        feed; unusable (overflow) for a magic that is not printable
 * @page: the page
 */
void be_mvp_log_render_header(struct be_mvp_line *line, const be_u8 *page);

/**
 * be_mvp_log_render_record - one record's line (4.3)
 * @line: reset, then `BE_MVP:19 LOG record seq=... digest=...`, no line
 *        feed; unusable (overflow) for an index at or after count or a
 *        number outside its enumeration
 * @page: the page
 * @index: the record's sequence number
 */
void be_mvp_log_render_record(struct be_mvp_line *line, const be_u8 *page,
			      be_u64 index);

/**
 * be_mvp_log_render_registers - a registers line (4.4)
 * @line: reset, then `BE_MVP:20 REGISTERS at=barrier r0=... ticks=...`
 *        with @barrier, else `... at=terminal r0=... r3=...`, no line feed
 * @registers: the registers
 * @barrier: nonzero for the barrier's line, which carries @ticks
 * @ticks: the hashing total, printed as the smaller of it and 0xffffffff
 */
void be_mvp_log_render_registers(struct be_mvp_line *line,
				 const be_u8 *registers, int barrier,
				 be_u64 ticks);

#endif
