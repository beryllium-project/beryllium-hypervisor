// SPDX-License-Identifier: GPL-3.0-only
/*
 * Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
 *
 * Purpose: host coverage for the MVP denial entry's decision,
 *          be_mvp_denial_decide (planning/mvp-m1-plan.md, "The denial
 *          path"), over te-poc's two roots, built and walked with their
 *          channel leaves as page 0 of each root's leaves, a root without
 *          one, and anchor's two roots with their leaves of the three
 *          declared pages (planning/mvp-m2-plan.md, Q1 and Q9): every cause
 *          on both sides of each region boundary (the window, the channel
 *          page or each declared page, and the neighbouring page), the
 *          declared denials of both roles, read-only for a store to a page
 *          the root maps without W and unmapped for a page it does not map;
 *          every hstatus SPV, SPVP, and GVA
 *          value; htval below 2^39 and each alias bit above it; the GPA
 *          from htval and stval's low bits; every htinst form (zero, a
 *          transformed load, store, and AMO, their compressed forms, each
 *          pseudoinstruction, a wrong opcode or cause, and a value of 2^32
 *          or more); every vstvec mode; an image that does not accept
 *          denials; the denial and the values it injects, the vsstatus
 *          transform for every SIE, SPIE, and SPP combination; that the
 *          decision writes nothing but its result; and the injection
 *          helper's words, readback comparison, and register names.
 * Trust:   host evidence only. No CSR, trap, injection, guest entry, QEMU,
 *          or hardware behaviour is exercised: the roots come from the MVP
 *          G-stage builder and walker, run in host memory.
 * Scope:   the MVP line (planning/mvp-m1-plan.md and
 *          planning/mvp-m2-plan.md).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mvp.h"

static unsigned long assertions;
static unsigned long scenarios;

#define CHECK(condition) \
	do { \
		++assertions; \
		if (!(condition)) { \
			printf("BE_MVP_DENY_CHECK: assertion failed: %s:%d: %s\n", \
			       __FILE__, __LINE__, #condition); \
			exit(1); \
		} \
	} while (0)

#define SCENARIO() \
	do { \
		++scenarios; \
	} while (0)

#define ALL_ONES		(~BE_U64_C(0))
#define FETCH			BE_MVP_SCAUSE_FETCH_GUEST_PAGE_FAULT
#define LOAD			BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT
#define STORE			BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT
#define UNMAPPED		BE_MVP_DENIAL_UNMAPPED
#define READ_ONLY		BE_MVP_DENIAL_READ_ONLY
#define REFUSED			ALL_ONES
#define WINDOW_GPA		BE_MVP_GUEST_GPA
#define WINDOW_END		(BE_MVP_GUEST_GPA + BE_MVP_GUEST_BYTES)
#define PAGE_GPA		BE_MVP_CHANNEL_GPA
#define PAGE_END		(BE_MVP_CHANNEL_GPA + BE_MVP_CHANNEL_BYTES)
#define PROBE_GPA		BE_U64_C(0x90000000)
#define GPA_TOP			((BE_MVP_HTVAL_LIMIT << 2) - 1U)
/* A VU exit as the vector saves it (QEMU and K3: VSXL 2; SPV, GVA). */
#define VU_HSTATUS		BE_U64_C(0x2000000c0)
#define VU_PC			BE_U64_C(0x10432)
#define VU_VA			BE_U64_C(0x3fffd5000)
#define VSTVEC			BE_U64_C(0xffffffff80a011c0)
#define VSSTATUS		(BE_MVP_VSSTATUS_UXL64 | \
				 BE_MVP_VSSTATUS_SPIE | BE_MVP_VSSTATUS_SIE)
#define EXIT_TIME		BE_U64_C(0x123456789)
/* Transformed loads (ld, lw), stores (sd, sw), and AMOs (amoswap.d,
 * amoadd.w), as M0's platform record and QEMU report them, and the
 * compressed forms (bit 1 clear). */
#define HTINST_LD		BE_U64_C(0x3303)
#define HTINST_LW		BE_U64_C(0x2283)
#define HTINST_SD		BE_U64_C(0x3023)
#define HTINST_SW		BE_U64_C(0x00a02023)
#define HTINST_AMOSWAP_D	BE_U64_C(0x08a0302f)
#define HTINST_AMOADD_W		BE_U64_C(0x00a0202f)
#define HTINST_C_LD		BE_U64_C(0x3301)
#define HTINST_C_SD		BE_U64_C(0x3021)
/* LOAD-FP and STORE-FP, MISC-MEM, and OP: valid transforms of other
 * opcodes. */
#define HTINST_FLD		BE_U64_C(0x3087)
#define HTINST_FSD		BE_U64_C(0x3027)
#define HTINST_FENCE		BE_U64_C(0x000f)
#define HTINST_OP		BE_U64_C(0x0033)

enum domain_root {
	ROOT_WRITER = 0,	/* G0: the channel leaf with W */
	ROOT_READER,		/* G1: the channel leaf without W */
	ROOT_NONE,		/* G0 without a channel: two-guests */
	ROOT_HOST,		/* anchor's G0: request RW, response R */
	ROOT_PROT,		/* anchor's G1: request R, response RW,
				 * secret R */
	ROOT_COUNT,
};
/* te-poc's and two-guests' roots, which M1's cases cover. */
#define CHANNEL_ROOTS		ROOT_HOST

/* anchor's three pages (planning/mvp-m2-plan.md, Q1): request, response,
 * and secret, directly above the windows. */
#define REQUEST_GPA		BE_MVP_CHANNEL_GPA
#define RESPONSE_GPA		(BE_MVP_CHANNEL_GPA + BE_U64_C(0x1000))
#define SECRET_GPA		(BE_MVP_CHANNEL_GPA + BE_U64_C(0x2000))
#define PAGES_END		(BE_MVP_CHANNEL_GPA + BE_U64_C(0x3000))
#define RW			(BE_MVP_GSTAGE_RIGHT_READ | \
				 BE_MVP_GSTAGE_RIGHT_WRITE)
#define RO			BE_MVP_GSTAGE_RIGHT_READ
static const struct be_mvp_gstage_page anchor_pages[3] = {
	{ REQUEST_GPA, BE_MVP_CHANNEL_HPA, 0x1000U, BE_MVP_PAGE_CHANNEL, 0U,
	  1U, { RW, RO } },
	{ RESPONSE_GPA, BE_MVP_CHANNEL_HPA + 0x1000U, 0x1000U,
	  BE_MVP_PAGE_CHANNEL, 1U, 0U, { RO, RW } },
	{ SECRET_GPA, BE_MVP_CHANNEL_HPA + 0x2000U, 0x1000U,
	  BE_MVP_PAGE_SECRET, BE_MVP_PAGE_NONE, 1U, { 0U, RO } },
};

static be_u8 pool[BE_MVP_GSTAGE_POOL_BYTES];
static struct be_mvp_gstage_map maps[ROOT_COUNT];
static struct be_mvp_gstage_leaves leaves[ROOT_COUNT];
static struct be_mvp_state accepting;
static struct be_mvp_denial denial;

static void build_roots(void)
{
	static const struct be_mvp_gstage_desc desc[ROOT_COUNT] = {
		{ BE_MVP_GUEST_GPA, BE_MVP_G0_HPA, BE_MVP_GUEST_BYTES,
		  BE_MVP_G0_ROOT_HPA, BE_MVP_G0_VMID, BE_MVP_DOMAIN0_HART },
		{ BE_MVP_GUEST_GPA, BE_MVP_G1_HPA, BE_MVP_GUEST_BYTES,
		  BE_MVP_G1_ROOT_HPA, BE_MVP_G1_VMID, BE_MVP_DOMAIN1_HART },
		{ BE_MVP_GUEST_GPA, BE_MVP_G0_HPA, BE_MVP_GUEST_BYTES,
		  BE_MVP_G0_ROOT_HPA, BE_MVP_G0_VMID, BE_MVP_DOMAIN0_HART },
		{ BE_MVP_GUEST_GPA, BE_MVP_G0_HPA, BE_MVP_GUEST_BYTES,
		  BE_MVP_G0_ROOT_HPA, BE_MVP_G0_VMID, BE_MVP_DOMAIN0_HART },
		{ BE_MVP_GUEST_GPA, BE_MVP_G1_HPA, BE_MVP_GUEST_BYTES,
		  BE_MVP_G1_ROOT_HPA, BE_MVP_G1_VMID, BE_MVP_DOMAIN1_HART },
	};
	static const struct be_mvp_gstage_root_page page[CHANNEL_ROOTS] = {
		{ BE_MVP_CHANNEL_GPA, BE_MVP_CHANNEL_HPA, BE_MVP_CHANNEL_BYTES,
		  BE_MVP_GSTAGE_RIGHT_READ | BE_MVP_GSTAGE_RIGHT_WRITE },
		{ BE_MVP_CHANNEL_GPA, BE_MVP_CHANNEL_HPA, BE_MVP_CHANNEL_BYTES,
		  BE_MVP_GSTAGE_RIGHT_READ },
		{ 0U, 0U, 0U, 0U },
	};
	unsigned int root;

	/* M1's channel leaf, as the runtime publishes it: page 0. */
	for (root = 0U; root < CHANNEL_ROOTS; ++root) {
		CHECK(be_mvp_gstage_build_channel(&desc[root], &page[root],
						  pool, sizeof(pool)) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk_channel(&desc[root], &page[root],
						 pool, sizeof(pool),
						 &maps[root],
						 &leaves[root].page[0]) ==
		      BE_MVP_GSTAGE_OK);
	}
	/* anchor's roots, the host's G0 and the protected domain's G1. */
	for (root = CHANNEL_ROOTS; root < ROOT_COUNT; ++root) {
		CHECK(be_mvp_gstage_build_pages(&desc[root], anchor_pages, 3U,
						root - CHANNEL_ROOTS, pool,
						sizeof(pool)) ==
		      BE_MVP_GSTAGE_OK);
		CHECK(be_mvp_gstage_walk_pages(&desc[root], anchor_pages, 3U,
					       pool, sizeof(pool), &maps[root],
					       &leaves[root]) ==
		      BE_MVP_GSTAGE_OK);
	}
	CHECK(leaves[ROOT_WRITER].page[0].pte == BE_U64_C(0x460000d7) &&
	      leaves[ROOT_READER].page[0].pte == BE_U64_C(0x46000053) &&
	      leaves[ROOT_NONE].page[0].bytes == 0U &&
	      leaves[ROOT_NONE].page[0].pte == 0U);
	CHECK(leaves[ROOT_HOST].page[0].pte == BE_U64_C(0x460000d7) &&
	      leaves[ROOT_HOST].page[1].pte == BE_U64_C(0x46000453) &&
	      leaves[ROOT_HOST].page[2].bytes == 0U &&
	      leaves[ROOT_PROT].page[0].pte == BE_U64_C(0x46000053) &&
	      leaves[ROOT_PROT].page[1].pte == BE_U64_C(0x460004d7) &&
	      leaves[ROOT_PROT].page[2].pte == BE_U64_C(0x46000853));
	accepting = (struct be_mvp_state)BE_MVP_STATE_INITIALIZER(
		BE_MVP_EXIT_CEILING);
	accepting.accept_denial = 1U;
}

/* A guest-page fault of @cause at @gpa from VU mode, as the vector saves
 * it: stval a guest virtual address with the GPA's page offset. */
static struct be_mvp_exit fault(be_u64 cause, be_u64 gpa)
{
	struct be_mvp_exit record;
	be_size index;

	memset(&record, 0, sizeof(record));
	for (index = 0U; index < BE_ARRAY_SIZE(record.frame.gpr); ++index)
		record.frame.gpr[index] = BE_U64_C(0x5a5a000000000000) | index;
	record.frame.vstvec = VSTVEC;
	record.frame.vsepc = BE_U64_C(0xffffffff80001234);
	record.frame.vscause = 8U;
	record.frame.vstval = 0U;
	record.frame.scause = cause;
	record.frame.sepc = VU_PC;
	record.frame.stval = VU_VA | (gpa & 0xfffU);
	record.frame.htval = gpa >> 2;
	record.hstatus = VU_HSTATUS;
	record.htinst = 0U;
	record.vsatp = BE_U64_C(0x8000000000080e00);
	record.time = EXIT_TIME;
	record.vsstatus = VSSTATUS;
	return record;
}

static be_u64 access_fault(be_u64 cause)
{
	return cause == FETCH ? BE_MVP_SCAUSE_FETCH_ACCESS_FAULT :
	       cause == LOAD ? BE_MVP_SCAUSE_LOAD_ACCESS_FAULT :
	       BE_MVP_SCAUSE_STORE_ACCESS_FAULT;
}

/*
 * One decision on @root for @record by @state: it reads only its inputs,
 * and a refusal leaves the denial zero. Return: the kind, or REFUSED.
 */
static be_u64 decide_as(const struct be_mvp_state *state, unsigned int root,
			const struct be_mvp_exit *record)
{
	static const struct be_mvp_denial zero;
	struct be_mvp_state state_before = *state;
	struct be_mvp_gstage_map map_before = maps[root];
	struct be_mvp_gstage_leaves leaf_before = leaves[root];
	struct be_mvp_exit record_before = *record;
	int accepted;

	memset(&denial, 0x5a, sizeof(denial));
	accepted = be_mvp_denial_decide(state, &maps[root], &leaves[root],
					record, &denial);
	CHECK(accepted == 0 || accepted == 1);
	CHECK(memcmp(&state_before, state, sizeof(*state)) == 0 &&
	      memcmp(&map_before, &maps[root], sizeof(map_before)) == 0 &&
	      memcmp(&leaf_before, &leaves[root], sizeof(leaf_before)) == 0 &&
	      memcmp(&record_before, record, sizeof(*record)) == 0);
	if (!accepted) {
		CHECK(memcmp(&denial, &zero, sizeof(zero)) == 0);
		return REFUSED;
	}
	/* Logged as the vector saved them; injected as Q5 states. */
	CHECK(denial.cause == record->frame.scause &&
	      denial.gpa == (record->frame.htval << 2 |
			     (record->frame.stval & 3U)) &&
	      denial.htval == record->frame.htval &&
	      denial.htinst == record->htinst &&
	      denial.stval == record->frame.stval &&
	      denial.sepc == record->frame.sepc &&
	      denial.vsstatus == record->vsstatus &&
	      denial.vstvec == record->frame.vstvec &&
	      denial.time == record->time);
	CHECK(denial.inject_vscause == access_fault(record->frame.scause) &&
	      denial.inject_vstval == record->frame.stval &&
	      denial.inject_vsepc == record->frame.sepc &&
	      denial.resume_pc == (record->frame.vstvec & ~BE_U64_C(3)));
	CHECK(denial.kind == UNMAPPED || denial.kind == READ_ONLY);
	return denial.kind;
}

static be_u64 decide(unsigned int root, const struct be_mvp_exit *record)
{
	return decide_as(&accepting, root, record);
}

static be_u64 decide_at(unsigned int root, be_u64 cause, be_u64 gpa)
{
	struct be_mvp_exit record = fault(cause, gpa);

	return decide(root, &record);
}

/* Each cause on both sides of each region boundary, on each root. */
static void test_places(void)
{
	static const be_u64 causes[3] = { FETCH, LOAD, STORE };
	static const be_u64 outside[] = {
		0U, 3U, WINDOW_GPA - 4U, WINDOW_GPA - 1U, PAGE_END,
		PAGE_END + 3U, PAGE_END + 0xff8U, PROBE_GPA,
		BE_MVP_GSTAGE_GIB, BE_MVP_GSTAGE_GPA_LIMIT - 0x1000U,
		GPA_TOP,
	};
	static const be_u64 window[] = {
		WINDOW_GPA, WINDOW_GPA + 3U, BE_MVP_KERNEL_GPA,
		BE_MVP_DTB_GPA, WINDOW_END - 8U, WINDOW_END - 1U,
	};
	static const be_u64 page[] = {
		PAGE_GPA, PAGE_GPA + 3U, PAGE_GPA + 0x800U, PAGE_END - 8U,
		PAGE_END - 1U,
	};
	unsigned int root;
	unsigned int index;
	unsigned int cause;

	for (root = 0U; root < CHANNEL_ROOTS; ++root) {
		for (cause = 0U; cause < 3U; ++cause) {
			SCENARIO();
			/* No root maps it: unmapped, any cause. */
			for (index = 0U; index < BE_ARRAY_SIZE(outside);
			     ++index)
				CHECK(decide_at(root, causes[cause],
						outside[index]) == UNMAPPED);
			/* The window is mapped RWX: never a denial. */
			for (index = 0U; index < BE_ARRAY_SIZE(window);
			     ++index)
				CHECK(decide_at(root, causes[cause],
						window[index]) == REFUSED);
			/* The page: unmapped without a channel; a store by
			 * the reader is read-only; the rest is refused. */
			for (index = 0U; index < BE_ARRAY_SIZE(page);
			     ++index)
				CHECK(decide_at(root, causes[cause],
						page[index]) ==
				      (root == ROOT_NONE ? UNMAPPED :
				       root == ROOT_READER &&
				       causes[cause] == STORE ? READ_ONLY :
				       REFUSED));
		}
	}
	/* te-poc's three denials (Q3) and M0's load of the probe GPA. */
	SCENARIO();
	CHECK(decide_at(ROOT_WRITER, LOAD, PAGE_END) == UNMAPPED);
	CHECK(denial.htval == BE_U64_C(0x21000400) &&
	      denial.inject_vscause == 5U);
	CHECK(decide_at(ROOT_READER, STORE, PAGE_GPA + 0xff8U) == READ_ONLY);
	CHECK(denial.htval == BE_U64_C(0x210003fe) &&
	      denial.inject_vscause == 7U);
	CHECK(decide_at(ROOT_READER, LOAD, PROBE_GPA) == UNMAPPED);
	CHECK(denial.htval == BE_U64_C(0x24000000) &&
	      denial.inject_vscause == 5U);
}

/*
 * anchor's roots (planning/mvp-m2-plan.md, Q1): on both sides of each
 * page's edges and in its middle, each cause gets the kind its root's
 * leaf gives it: none, unmapped (the host's secret page); a leaf without
 * W, read-only for a store and refused otherwise; a leaf with W, refused.
 * Then the declared denials of both roles (Q9).
 */
static be_u64 expected_kind(unsigned int root, be_u64 cause, be_u64 gpa)
{
	be_u64 index;

	if (gpa >= WINDOW_GPA && gpa < WINDOW_END)
		return REFUSED;
	for (index = 0U; index < 3U; ++index) {
		be_u64 rights = anchor_pages[index].rights[root -
							   CHANNEL_ROOTS];

		if (gpa < anchor_pages[index].gpa ||
		    gpa - anchor_pages[index].gpa >= 0x1000U)
			continue;
		if (rights == 0U)
			return UNMAPPED;
		return cause == STORE && (rights & BE_MVP_GSTAGE_RIGHT_WRITE)
		       == 0U ? READ_ONLY : REFUSED;
	}
	return UNMAPPED;
}

static void test_pages(void)
{
	static const be_u64 causes[3] = { FETCH, LOAD, STORE };
	static const be_u64 places[] = {
		WINDOW_END - 8U, REQUEST_GPA, REQUEST_GPA + 0x800U,
		RESPONSE_GPA - 8U, RESPONSE_GPA, RESPONSE_GPA + 0xff8U,
		SECRET_GPA - 1U, SECRET_GPA, SECRET_GPA + 3U,
		PAGES_END - 8U, PAGES_END, PAGES_END + 0x1000U, PROBE_GPA,
		BE_U64_C(0x114000000), BE_U64_C(0x102064000), GPA_TOP,
	};
	unsigned int root;
	unsigned int cause;
	unsigned int index;

	for (root = CHANNEL_ROOTS; root < ROOT_COUNT; ++root) {
		for (cause = 0U; cause < 3U; ++cause) {
			SCENARIO();
			for (index = 0U; index < BE_ARRAY_SIZE(places);
			     ++index)
				CHECK(decide_at(root, causes[cause],
						places[index]) ==
				      expected_kind(root, causes[cause],
						    places[index]));
		}
	}
	/* The host's four (Q9): the response page read-only, the secret
	 * page, the protected window, and the MVP region unmapped. */
	SCENARIO();
	CHECK(decide_at(ROOT_HOST, STORE, RESPONSE_GPA + 0xff8U) ==
	      READ_ONLY);
	CHECK(denial.htval == BE_U64_C(0x210007fe) &&
	      denial.gpa == BE_U64_C(0x84001ff8) &&
	      denial.inject_vscause == 7U);
	CHECK(decide_at(ROOT_HOST, LOAD, SECRET_GPA) == UNMAPPED);
	CHECK(denial.htval == BE_U64_C(0x21000800) &&
	      denial.inject_vscause == 5U);
	CHECK(decide_at(ROOT_HOST, LOAD, BE_U64_C(0x114000000)) == UNMAPPED);
	CHECK(denial.htval == BE_U64_C(0x45000000));
	CHECK(decide_at(ROOT_HOST, LOAD, BE_U64_C(0x102064000)) == UNMAPPED);
	CHECK(denial.htval == BE_U64_C(0x40819000));
	/* The protected domain's one: the request page read-only. */
	CHECK(decide_at(ROOT_PROT, STORE, REQUEST_GPA + 0xff8U) ==
	      READ_ONLY);
	CHECK(denial.htval == BE_U64_C(0x210003fe) &&
	      denial.inject_vscause == 7U);
	/* What each root maps for reading, or writes, is no denial; a
	 * store to the secret page the protected domain reads is. */
	SCENARIO();
	CHECK(decide_at(ROOT_HOST, STORE, REQUEST_GPA + 0xff8U) == REFUSED);
	CHECK(decide_at(ROOT_HOST, LOAD, RESPONSE_GPA) == REFUSED);
	CHECK(decide_at(ROOT_PROT, LOAD, SECRET_GPA) == REFUSED);
	CHECK(decide_at(ROOT_PROT, STORE, SECRET_GPA) == READ_ONLY);
	CHECK(decide_at(ROOT_PROT, STORE, RESPONSE_GPA) == REFUSED);
	CHECK(decide_at(ROOT_PROT, FETCH, SECRET_GPA) == REFUSED);
	/* A store to the host's secret page: no leaf, so unmapped. */
	CHECK(decide_at(ROOT_HOST, STORE, SECRET_GPA + 0xff8U) == UNMAPPED);
	/* A page past the declared ones maps in neither root, and the
	 * host maps none of the secret page. */
	CHECK(decide_at(ROOT_PROT, STORE, PAGES_END) == UNMAPPED);
	CHECK(decide_at(ROOT_HOST, LOAD, PAGES_END - 1U) == UNMAPPED);
}

/* hstatus: only SPV 1, SPVP 0, GVA 1, whatever its other bits. */
static void test_origin(void)
{
	struct be_mvp_exit record;
	unsigned int bits;

	SCENARIO();
	for (bits = 0U; bits < 8U; ++bits) {
		be_u64 hstatus = BE_U64_C(0x200000000);

		if ((bits & 1U) != 0U)
			hstatus |= BE_MVP_HSTATUS_SPV;
		if ((bits & 2U) != 0U)
			hstatus |= BE_MVP_HSTATUS_SPVP;
		if ((bits & 4U) != 0U)
			hstatus |= BE_MVP_HSTATUS_GVA;
		record = fault(LOAD, PAGE_END);
		record.hstatus = hstatus;
		CHECK(decide(ROOT_WRITER, &record) ==
		      (bits == 5U ? UNMAPPED : REFUSED));
		record = fault(STORE, PAGE_GPA);
		record.hstatus = hstatus;
		CHECK(decide(ROOT_READER, &record) ==
		      (bits == 5U ? READ_ONLY : REFUSED));
	}
	SCENARIO();
	record = fault(LOAD, PAGE_END);
	record.hstatus = ALL_ONES & ~BE_MVP_HSTATUS_SPVP;
	CHECK(decide(ROOT_WRITER, &record) == UNMAPPED);
	record.hstatus = BE_MVP_HSTATUS_SPV | BE_MVP_HSTATUS_GVA;
	CHECK(decide(ROOT_WRITER, &record) == UNMAPPED);
	/* A fault from VS mode: the guest kernel's own access. */
	record.hstatus = VU_HSTATUS | BE_MVP_HSTATUS_SPVP;
	CHECK(decide(ROOT_WRITER, &record) == REFUSED);
}

/* htval: below 2^39; the GPA is its value shifted with stval's bits. */
static void test_htval(void)
{
	struct be_mvp_exit record;
	unsigned int bit;
	be_u64 low;

	SCENARIO();
	record = fault(LOAD, GPA_TOP);
	CHECK(record.frame.htval == BE_MVP_HTVAL_LIMIT - 1U);
	CHECK(decide(ROOT_WRITER, &record) == UNMAPPED &&
	      denial.gpa == GPA_TOP);
	/* Each alias bit, alone and with an otherwise denied GPA, also when
	 * the shifted value wraps to it. */
	for (bit = 39U; bit < 64U; ++bit) {
		record = fault(LOAD, PAGE_END);
		record.frame.htval |= BE_U64_C(1) << bit;
		CHECK(decide(ROOT_WRITER, &record) == REFUSED);
		record.frame.htval = BE_U64_C(1) << bit;
		CHECK(decide(ROOT_WRITER, &record) == REFUSED);
	}
	/* stval's low two bits complete the GPA: no other stval bit does. */
	SCENARIO();
	for (low = 0U; low < 4U; ++low) {
		record = fault(STORE, WINDOW_END - 4U);
		record.frame.stval = VU_VA | low;
		CHECK(decide(ROOT_READER, &record) == REFUSED);
		record = fault(STORE, PAGE_GPA);
		record.frame.stval = ALL_ONES - 3U + low;
		CHECK(decide(ROOT_READER, &record) == READ_ONLY &&
		      denial.gpa == PAGE_GPA + low);
		record = fault(LOAD, PAGE_GPA - 4U);
		record.frame.stval = VU_VA | low;
		CHECK(decide(ROOT_READER, &record) == REFUSED);
		record = fault(LOAD, PAGE_END - 4U);
		record.frame.stval = VU_VA | low;
		CHECK(decide(ROOT_WRITER, &record) == REFUSED);
		record = fault(LOAD, PAGE_END);
		record.frame.stval = VU_VA | low;
		CHECK(decide(ROOT_WRITER, &record) == UNMAPPED &&
		      denial.gpa == PAGE_END + low);
	}
}

static void htinst_case(be_u64 cause, be_u64 htinst, int accepted)
{
	struct be_mvp_exit record = fault(cause, PROBE_GPA);

	record.htinst = htinst;
	CHECK(decide(ROOT_READER, &record) ==
	      (accepted ? UNMAPPED : REFUSED));
	record = fault(cause, PAGE_GPA);
	record.htinst = htinst;
	CHECK(decide(ROOT_READER, &record) ==
	      (accepted && cause == STORE ? READ_ONLY : REFUSED));
}

/*
 * htinst: zero, or a transformed load (21) or store or AMO (23), never a
 * fetch's, a pseudoinstruction, another opcode, or 2^32 or more.
 */
static void test_htinst(void)
{
	static const be_u64 pseudo[] = {
		BE_U64_C(0x2000), BE_U64_C(0x3000), BE_U64_C(0x2020),
		BE_U64_C(0x3020), BE_U64_C(0x0004), BE_U64_C(0x3300),
	};
	static const be_u64 other[] = {
		HTINST_FLD, HTINST_FSD, HTINST_FENCE, HTINST_OP,
		BE_U64_C(0x3302), BE_U64_C(0x3022),
		BE_U64_C(0x0003) | BE_U64_C(0x1f) << 2,
	};
	unsigned int index;

	SCENARIO();
	htinst_case(FETCH, 0U, 1);
	htinst_case(LOAD, 0U, 1);
	htinst_case(STORE, 0U, 1);
	SCENARIO();
	htinst_case(LOAD, HTINST_LD, 1);
	htinst_case(LOAD, HTINST_LW, 1);
	htinst_case(LOAD, HTINST_C_LD, 1);
	htinst_case(STORE, HTINST_SD, 1);
	htinst_case(STORE, HTINST_SW, 1);
	htinst_case(STORE, HTINST_C_SD, 1);
	htinst_case(STORE, HTINST_AMOSWAP_D, 1);
	htinst_case(STORE, HTINST_AMOADD_W, 1);
	/* The least transformed load: a compressed one, every field 0. */
	htinst_case(LOAD, BE_U64_C(1), 1);
	htinst_case(STORE, BE_U64_C(1), 0);
	/* The wrong cause for the opcode; a fetch has none. */
	SCENARIO();
	htinst_case(LOAD, HTINST_SD, 0);
	htinst_case(LOAD, HTINST_C_SD, 0);
	htinst_case(LOAD, HTINST_AMOSWAP_D, 0);
	htinst_case(STORE, HTINST_LD, 0);
	htinst_case(STORE, HTINST_C_LD, 0);
	htinst_case(FETCH, HTINST_LD, 0);
	htinst_case(FETCH, HTINST_SD, 0);
	htinst_case(FETCH, BE_U64_C(1), 0);
	/* Pseudoinstructions (bits 1:0 clear), and custom values. */
	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(pseudo); ++index) {
		htinst_case(FETCH, pseudo[index], 0);
		htinst_case(LOAD, pseudo[index], 0);
		htinst_case(STORE, pseudo[index], 0);
	}
	/* Other opcodes, and bit 0 clear with bit 1 set. */
	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(other); ++index) {
		htinst_case(LOAD, other[index], 0);
		htinst_case(STORE, other[index], 0);
	}
	/* 2^32 and above, even with a transformed instruction's low bits. */
	SCENARIO();
	htinst_case(LOAD, BE_U64_C(1) << 32 | HTINST_LD, 0);
	htinst_case(STORE, BE_U64_C(1) << 32 | HTINST_SD, 0);
	htinst_case(LOAD, ALL_ONES, 0);
	htinst_case(STORE, BE_U64_C(0xffffffff), 0);
	htinst_case(LOAD, BE_U64_C(0xffffff83), 1);
}

/* vstvec: Direct or Vectored; the guest resumes at its BASE. */
static void test_vstvec(void)
{
	struct be_mvp_exit record;
	be_u64 mode;

	SCENARIO();
	for (mode = 0U; mode < 4U; ++mode) {
		record = fault(LOAD, PROBE_GPA);
		record.frame.vstvec = VSTVEC | mode;
		CHECK(decide(ROOT_READER, &record) ==
		      (mode <= 1U ? UNMAPPED : REFUSED));
		if (mode <= 1U)
			CHECK(denial.resume_pc == VSTVEC &&
			      denial.vstvec == (VSTVEC | mode));
	}
	record = fault(STORE, PAGE_GPA);
	record.frame.vstvec = 1U;
	CHECK(decide(ROOT_READER, &record) == READ_ONLY &&
	      denial.resume_pc == 0U);
	record.frame.vstvec = ALL_ONES - 2U;
	CHECK(decide(ROOT_READER, &record) == READ_ONLY &&
	      denial.resume_pc == ALL_ONES - 3U);
	record.frame.vstvec = ALL_ONES;
	CHECK(decide(ROOT_READER, &record) == REFUSED);
}

/*
 * Only an image that accepts denials, a walked window, every input, and
 * a guest-page fault: anything else is M0's terminal path.
 */
static void test_inputs(void)
{
	static const be_u64 others[] = {
		0U, 1U, 5U, 7U, 8U, 10U, 12U, 13U, 15U, 22U, 24U,
		BE_U64_C(1) << 63 | 1U, BE_U64_C(1) << 63 | 21U,
	};
	struct be_mvp_exit record = fault(LOAD, PAGE_END);
	struct be_mvp_state state = accepting;
	struct be_mvp_gstage_map map;
	unsigned int index;

	SCENARIO();
	CHECK(decide_as(&state, ROOT_WRITER, &record) == UNMAPPED);
	state.accept_denial = 0U;
	CHECK(decide_as(&state, ROOT_WRITER, &record) == REFUSED);
	state.accept_denial = 2U;
	CHECK(decide_as(&state, ROOT_WRITER, &record) == REFUSED);
	state.accept_denial = ALL_ONES;
	CHECK(decide_as(&state, ROOT_WRITER, &record) == REFUSED);
	/* The decision does not ask the phase: the caller does. */
	state = accepting;
	state.phase = BE_MVP_PHASE_FAILED;
	CHECK(decide_as(&state, ROOT_WRITER, &record) == UNMAPPED);
	SCENARIO();
	for (index = 0U; index < BE_ARRAY_SIZE(others); ++index) {
		record = fault(others[index], PAGE_END);
		CHECK(decide(ROOT_WRITER, &record) == REFUSED);
	}
	SCENARIO();
	record = fault(LOAD, PAGE_END);
	map = maps[ROOT_WRITER];
	memset(&maps[ROOT_WRITER], 0, sizeof(map));
	CHECK(decide(ROOT_WRITER, &record) == REFUSED);
	maps[ROOT_WRITER] = map;
	memset(&denial, 0x5a, sizeof(denial));
	CHECK(be_mvp_denial_decide((const struct be_mvp_state *)0,
				   &maps[ROOT_WRITER], &leaves[ROOT_WRITER],
				   &record, &denial) == 0);
	CHECK(denial.cause == 0U && denial.resume_pc == 0U);
	CHECK(be_mvp_denial_decide(&accepting,
				   (const struct be_mvp_gstage_map *)0,
				   &leaves[ROOT_WRITER], &record,
				   &denial) == 0);
	CHECK(be_mvp_denial_decide(&accepting, &maps[ROOT_WRITER],
				   (const struct be_mvp_gstage_leaves *)0,
				   &record, &denial) == 0);
	CHECK(be_mvp_denial_decide(&accepting, &maps[ROOT_WRITER],
				   &leaves[ROOT_WRITER],
				   (const struct be_mvp_exit *)0,
				   &denial) == 0);
	CHECK(denial.cause == 0U && denial.gpa == 0U);
	CHECK(be_mvp_denial_decide(&accepting, &maps[ROOT_WRITER],
				   &leaves[ROOT_WRITER], &record,
				   (struct be_mvp_denial *)0) == 0);
}

/*
 * The injected vsstatus: SPP the guest's mode at the fault (VU, so 0),
 * SPIE its SIE, SIE 0, and every other bit as the vector read it.
 */
static void test_vsstatus(void)
{
	static const be_u64 rest[] = {
		0U, BE_MVP_VSSTATUS_UXL64,
		BE_MVP_VSSTATUS_UXL64 | BE_U64_C(0x46600),
		ALL_ONES & ~(BE_MVP_VSSTATUS_SPP | BE_MVP_VSSTATUS_SPIE |
			     BE_MVP_VSSTATUS_SIE),
	};
	struct be_mvp_exit record;
	unsigned int index;
	unsigned int bits;

	for (index = 0U; index < BE_ARRAY_SIZE(rest); ++index) {
		SCENARIO();
		for (bits = 0U; bits < 8U; ++bits) {
			be_u64 vsstatus = rest[index];
			be_u64 expected = rest[index];

			if ((bits & 1U) != 0U) {
				vsstatus |= BE_MVP_VSSTATUS_SIE;
				expected |= BE_MVP_VSSTATUS_SPIE;
			}
			if ((bits & 2U) != 0U)
				vsstatus |= BE_MVP_VSSTATUS_SPIE;
			if ((bits & 4U) != 0U)
				vsstatus |= BE_MVP_VSSTATUS_SPP;
			record = fault(STORE, PAGE_GPA + 0xff8U);
			record.vsstatus = vsstatus;
			CHECK(decide(ROOT_READER, &record) == READ_ONLY);
			CHECK(denial.vsstatus == vsstatus &&
			      denial.inject_vsstatus == expected);
			CHECK((denial.inject_vsstatus &
			       (BE_MVP_VSSTATUS_SPP | BE_MVP_VSSTATUS_SIE)) ==
			      0U);
		}
	}
}

/*
 * The injection helper's words in its order, the readback comparison,
 * and the per-domain CSR each word names in a register DETAIL.
 */
static void test_inject(void)
{
	static const be_u32 vcsrs[BE_MVP_INJECT_WORDS] = {
		BE_MVP_VCSR_VSCAUSE, BE_MVP_VCSR_VSTVAL, BE_MVP_VCSR_VSEPC,
		BE_MVP_VCSR_VSSTATUS,
	};
	static const char *const names[BE_MVP_INJECT_WORDS] = {
		"vscause", "vstval", "vsepc", "vsstatus",
	};
	be_u64 written[BE_MVP_INJECT_WORDS];
	be_u64 readback[BE_MVP_INJECT_WORDS];
	unsigned int index;

	SCENARIO();
	CHECK(decide_at(ROOT_READER, STORE, PAGE_GPA + 0xff8U) == READ_ONLY);
	memset(written, 0x5a, sizeof(written));
	be_mvp_inject_words(&denial, written);
	CHECK(written[BE_MVP_INJECT_VSCAUSE] == 7U &&
	      written[BE_MVP_INJECT_VSTVAL] == (VU_VA | 0xff8U) &&
	      written[BE_MVP_INJECT_VSEPC] == VU_PC &&
	      written[BE_MVP_INJECT_VSSTATUS] ==
		      (BE_MVP_VSSTATUS_UXL64 | BE_MVP_VSSTATUS_SPIE));
	memcpy(readback, written, sizeof(readback));
	CHECK(be_mvp_inject_mismatch(written, readback) ==
	      BE_MVP_INJECT_WORDS);
	for (index = 0U; index < BE_MVP_INJECT_WORDS; ++index) {
		readback[index] ^= BE_U64_C(1) << index;
		CHECK(be_mvp_inject_mismatch(written, readback) == index);
		readback[BE_MVP_INJECT_WORDS - 1U] ^= 1U;
		CHECK(be_mvp_inject_mismatch(written, readback) == index);
		readback[BE_MVP_INJECT_WORDS - 1U] ^= 1U;
		readback[index] ^= BE_U64_C(1) << index;
	}
	CHECK(be_mvp_inject_mismatch((const be_u64 *)0, readback) == 0U);
	CHECK(be_mvp_inject_mismatch(written, (const be_u64 *)0) == 0U);
	memset(readback, 0x5a, sizeof(readback));
	be_mvp_inject_words((const struct be_mvp_denial *)0, readback);
	be_mvp_inject_words(&denial, (be_u64 *)0);
	CHECK(readback[0] == BE_U64_C(0x5a5a5a5a5a5a5a5a));
	SCENARIO();
	for (index = 0U; index < BE_MVP_INJECT_WORDS; ++index) {
		be_u32 vcsr = be_mvp_inject_vcsr(index);

		CHECK(vcsr == vcsrs[index]);
		CHECK(strcmp(be_mvp_vcsr_name(vcsr), names[index]) == 0);
	}
	CHECK(be_mvp_inject_vcsr(BE_MVP_INJECT_WORDS) == BE_MVP_VCSR_COUNT);
	CHECK(be_mvp_inject_vcsr(~0U) == BE_MVP_VCSR_COUNT);
}

int main(void)
{
	build_roots();
	test_places();
	test_pages();
	test_origin();
	test_htval();
	test_htinst();
	test_vstvec();
	test_inputs();
	test_vsstatus();
	test_inject();
	printf("BE_MVP_DENY_CHECK: PASS\n");
	printf("BE_MVP_DENY_CHECK: scenarios=%lu\n", scenarios);
	printf("BE_MVP_DENY_CHECK: assertions=%lu\n", assertions);
	return 0;
}
