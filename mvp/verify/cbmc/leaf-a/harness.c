/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> */
/*
 * Purpose: CBMC's bounded model check of Leaf A (planning/mvp-m8-plan.md,
 *          D-8's last sentence, D-7 item 6; specification
 *          planning/mvp-m8-specifications.md sections 4 and 6 as its
 *          Revision 1 states them, SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b,
 *          accepted at 93a8d136; the clauses it corrected are marked
 *          [R1-n] below; the first run's harness, against the accepted
 *          text of 004f31ae, is in mvp/results/20261103-verify/leaf-a/cbmc/
 *          by its digest): the leaf's translation unit is included
 *          whole (LEAF, the path of mvp/src/mvp-sbi.c or of a mutant of
 *          it, given with -D), so the static helpers can be called; every
 *          input is nondeterministic, constrained only by section 4.3 (or
 *          4.5) with __CPROVER_assume; section 4.4's and 4.5's clauses are
 *          assertions named after the WP and CN arms' goals. Entry points
 *          (cbmc --function): check_decide, check_frame,
 *          check_helpers; the vacuity
 *          checks reach_NAME (an assert(0) after the call, which must
 *          fail) and contradiction_NAME (a contradictory assumption, after
 *          which assert(0) must hold), and cover_decide (--cover cover:
 *          every case of the contract must be reachable).
 * Trust:   a bounded model check, never proof: leaf_at's loop runs three
 *          times and --unwinding-assertions checks that bound; the
 *          specification's arithmetic is done in unsigned __int128, so no
 *          sum or shift of it wraps. tools/cbmc-leaf-a.py runs it.
 * Scope:   Leaf A only; never linked into the monitor.
 */
#include LEAF

typedef unsigned __int128 wide;

int memcmp(const void *left, const void *right, unsigned long bytes);

struct be_mvp_state nondet_state(void);
struct be_mvp_gstage_map nondet_map(void);
struct be_mvp_gstage_leaves nondet_leaves(void);
struct be_mvp_exit nondet_exit(void);
struct be_mvp_denial nondet_denial(void);
be_u64 nondet_u64(void);

/* Section 4.1. */
static wide bit(wide v, unsigned int n)
{
	return (v >> n) & 1U;
}

static wide gpa_of(const struct be_mvp_exit *r)
{
	return ((wide)r->frame.htval << 2) | (r->frame.stval & 3U);
}

static wide opcode(wide i)
{
	return (i >> 2) & 0x1fU;
}

static int htinst_ok(be_u64 scause, wide i)
{
	return i == 0U ||
	       (i < ((wide)1 << 32) && (i & 1U) == 1U &&
		((scause == 21U && opcode(i) == 0x00U) ||
		 (scause == 23U && (opcode(i) == 0x08U ||
				    opcode(i) == 0x0bU))));
}

static int inside_spec(wide a, wide base, wide n)
{
	return base <= a && a < base + n;
}

static int in_page(const struct be_mvp_gstage_leaves *l, int i, wide gpa)
{
	return l->page[i].bytes > 0U &&
	       inside_spec(gpa, l->page[i].gpa, l->page[i].bytes);
}

static int has_page(const struct be_mvp_gstage_leaves *l, wide gpa)
{
	return in_page(l, 0, gpa) || in_page(l, 1, gpa) || in_page(l, 2, gpa);
}

/* PAGE(gpa)'s index, or -1. */
static int page_index(const struct be_mvp_gstage_leaves *l, wide gpa)
{
	return in_page(l, 0, gpa) ? 0 : in_page(l, 1, gpa) ? 1 :
	       in_page(l, 2, gpa) ? 2 : -1;
}

/* 1, 5, 7 for 20, 21, 23, and 0 for any other cause [R1-3]. (MAPPED,
 * which E7 no longer uses [R1-1], is not needed here.) */
static be_u64 access_fault_spec(be_u64 scause)
{
	return scause == 20U ? 1U : scause == 21U ? 5U : scause == 23U ? 7U :
	       0U;
}

/* Section 4.2. */
static int e2(const struct be_mvp_exit *r)
{
	return r->frame.scause == 20U || r->frame.scause == 21U ||
	       r->frame.scause == 23U;
}

static int e3(const struct be_mvp_exit *r)
{
	return bit(r->hstatus, 7) == 1U && bit(r->hstatus, 8) == 0U &&
	       bit(r->hstatus, 6) == 1U;
}

static int e6(const struct be_mvp_exit *r)
{
	return (r->frame.vstvec & 3U) <= 1U;
}

/* The GPA inside the window. */
static int in_window(const struct be_mvp_gstage_map *m,
		     const struct be_mvp_exit *r)
{
	return inside_spec(gpa_of(r), m->gpa_base, m->size);
}

/* E7's unmapped case: PAGE(GPA) does not exist [R1-1]. */
static int unmapped(const struct be_mvp_gstage_leaves *l,
		    const struct be_mvp_exit *r)
{
	return !has_page(l, gpa_of(r));
}

/* E7's read-only case: cause 23, PAGE(GPA) exists and lacks W. */
static int read_only(const struct be_mvp_gstage_leaves *l,
		     const struct be_mvp_exit *r)
{
	int i = page_index(l, gpa_of(r));

	return r->frame.scause == 23U && i >= 0 &&
	       bit(l->page[i].pte, 2) == 0U;
}

/* E7: the GPA outside the window first, for every cause, and then either
 * case [R1-1]. */
static int e7(const struct be_mvp_gstage_map *m,
	      const struct be_mvp_gstage_leaves *l, const struct be_mvp_exit *r)
{
	return !in_window(m, r) && (unmapped(l, r) || read_only(l, r));
}

static int entry(const struct be_mvp_state *s, const struct be_mvp_gstage_map *m,
		 const struct be_mvp_gstage_leaves *l,
		 const struct be_mvp_exit *r)
{
	return s->accept_denial == 1U && e2(r) && e3(r) &&
	       r->frame.htval < ((be_u64)1 << 39) &&
	       htinst_ok(r->frame.scause, r->htinst) && e6(r) && e7(m, l, r);
}

/* Sections 4.3 and 4.5 (leaf_at's): no page's sum wraps. */
static void pages_nowrap(const struct be_mvp_gstage_leaves *l)
{
	int i;

	for (i = 0; i < 3; ++i)
		__CPROVER_assume(l->page[i].bytes <= ~(be_u64)0 - l->page[i].gpa);
}

/* Section 4.3: a walked window, size > 0 [R1-2], whose sum does not wrap,
 * and the pages'. */
static void preconditions(const struct be_mvp_gstage_map *m,
			  const struct be_mvp_gstage_leaves *l)
{
	__CPROVER_assume(m->size > 0U);
	__CPROVER_assume(m->size <= ~(be_u64)0 - m->gpa_base);
	pages_nowrap(l);
}

#define IMPLIES(a, b) (!(a) || (b))
#define ON1(name, condition) __CPROVER_assert(IMPLIES(result == 1, condition), name)
#define ON0(field) __CPROVER_assert(IMPLIES(result == 0, out.field == 0U), "D_zero_" #field)

/* Section 4.4's frame: the inputs are not written (memcmp's loop is
 * unwound over each structure, cbmc-leaf-a.py's --unwindset). */
void check_frame(void)
{
	struct be_mvp_state state = nondet_state();
	struct be_mvp_gstage_map map = nondet_map();
	struct be_mvp_gstage_leaves leaves = nondet_leaves();
	struct be_mvp_exit record = nondet_exit();
	struct be_mvp_denial out = nondet_denial();
	struct be_mvp_state state_before;
	struct be_mvp_gstage_map map_before;
	struct be_mvp_gstage_leaves leaves_before;
	struct be_mvp_exit record_before;

	preconditions(&map, &leaves);
	state_before = state;
	map_before = map;
	leaves_before = leaves;
	record_before = record;
	(void)be_mvp_denial_decide(&state, &map, &leaves, &record, &out);
	__CPROVER_assert(memcmp(&state, &state_before, sizeof(state)) == 0 &&
			 memcmp(&map, &map_before, sizeof(map)) == 0 &&
			 memcmp(&leaves, &leaves_before, sizeof(leaves)) == 0 &&
			 memcmp(&record, &record_before, sizeof(record)) == 0,
			 "D_frame");
}

void check_decide(void)
{
	struct be_mvp_state state = nondet_state();
	struct be_mvp_gstage_map map = nondet_map();
	struct be_mvp_gstage_leaves leaves = nondet_leaves();
	struct be_mvp_exit record = nondet_exit();
	struct be_mvp_denial out = nondet_denial();
	be_u64 expect;
	int ok;
	int result;

	preconditions(&map, &leaves);
	ok = entry(&state, &map, &leaves, &record);
	result = be_mvp_denial_decide(&state, &map, &leaves, &record, &out);
	__CPROVER_assert(result == 0 || result == 1, "D_result");
	ON1("D_E1", state.accept_denial == 1U);
	ON1("D_E2", e2(&record));
	ON1("D_E3", e3(&record));
	ON1("D_E4", record.frame.htval < ((be_u64)1 << 39));
	ON1("D_E5", htinst_ok(record.frame.scause, record.htinst));
	ON1("D_E6", e6(&record));
	ON1("D_E7", e7(&map, &leaves, &record));
	__CPROVER_assert(IMPLIES(ok, result == 1), "D_complete");
	ON1("D_cause", out.cause == record.frame.scause);
	ON1("D_kind_unmapped", IMPLIES(unmapped(&leaves, &record),
				       out.kind == 0U));
	ON1("D_kind_read_only", IMPLIES(read_only(&leaves, &record),
					out.kind == 1U));
	ON1("D_gpa", out.gpa == gpa_of(&record));
	ON1("D_htval", out.htval == record.frame.htval);
	ON1("D_htinst", out.htinst == record.htinst);
	ON1("D_stval", out.stval == record.frame.stval);
	ON1("D_sepc", out.sepc == record.frame.sepc);
	ON1("D_vsstatus", out.vsstatus == record.vsstatus);
	ON1("D_vstvec", out.vstvec == record.frame.vstvec);
	ON1("D_time", out.time == record.time);
	ON1("D_inject_vscause",
	    out.inject_vscause == access_fault_spec(record.frame.scause));
	ON1("D_inject_vstval", out.inject_vstval == record.frame.stval);
	ON1("D_inject_vsepc", out.inject_vsepc == record.frame.sepc);
	ON1("D_inject_vsstatus_spp",
	    bit(out.inject_vsstatus, 8) == bit(record.hstatus, 8));
	ON1("D_inject_vsstatus_spie",
	    bit(out.inject_vsstatus, 5) == bit(record.vsstatus, 1));
	ON1("D_inject_vsstatus_sie", bit(out.inject_vsstatus, 1) == 0U);
	expect = record.vsstatus & ~(be_u64)0x122;
	ON1("D_inject_vsstatus_rest",
	    (out.inject_vsstatus & ~(be_u64)0x122) == expect);
	ON1("D_resume_pc", out.resume_pc == (record.frame.vstvec & ~(be_u64)3));
	ON0(cause);
	ON0(kind);
	ON0(gpa);
	ON0(htval);
	ON0(htinst);
	ON0(stval);
	ON0(sepc);
	ON0(vsstatus);
	ON0(vstvec);
	ON0(time);
	ON0(inject_vscause);
	ON0(inject_vstval);
	ON0(inject_vsepc);
	ON0(inject_vsstatus);
	ON0(resume_pc);
}

void check_helpers(void)
{
	struct be_mvp_gstage_leaves leaves = nondet_leaves();
	be_u64 scause = nondet_u64();
	be_u64 value = nondet_u64();
	be_u64 base = nondet_u64();
	be_u64 bytes = nondet_u64();
	const struct be_mvp_gstage_leaf *leaf;
	int index;

	__CPROVER_assert(IMPLIES(scause == 20U || scause == 21U ||
				 scause == 23U,
				 access_fault(scause) ==
				 access_fault_spec(scause)), "AF_cause");
	__CPROVER_assert(IMPLIES(!(scause == 20U || scause == 21U ||
				   scause == 23U), access_fault(scause) == 0U),
			 "AF_other");
	__CPROVER_assert((htinst_accepted(scause, value) == 1) ==
			 htinst_ok(scause, value), "HI_iff");
	__CPROVER_assert(htinst_accepted(scause, value) == 0 ||
			 htinst_accepted(scause, value) == 1, "HI_bool");
	__CPROVER_assume(bytes <= ~(be_u64)0 - base);
	__CPROVER_assert((inside(value, base, bytes) == 1) ==
			 inside_spec(value, base, bytes), "IN_iff");
	__CPROVER_assert(inside(value, base, bytes) == 0 ||
			 inside(value, base, bytes) == 1, "IN_bool");
	pages_nowrap(&leaves);
	leaf = leaf_at(&leaves, value);
	index = page_index(&leaves, value);
	__CPROVER_assert(IMPLIES(index >= 0, leaf == &leaves.page[index]),
			 "LA_page");
	__CPROVER_assert(IMPLIES(!has_page(&leaves, value),
				 leaf == (const struct be_mvp_gstage_leaf *)0),
			 "LA_none");
}

/* Vacuity: section 4.3's inputs reach each function's end... */
void reach_be_mvp_denial_decide(void)
{
	struct be_mvp_state state = nondet_state();
	struct be_mvp_gstage_map map = nondet_map();
	struct be_mvp_gstage_leaves leaves = nondet_leaves();
	struct be_mvp_exit record = nondet_exit();
	struct be_mvp_denial out;

	preconditions(&map, &leaves);
	(void)be_mvp_denial_decide(&state, &map, &leaves, &record, &out);
	__CPROVER_assert(0, "reach");
}

void reach_access_fault(void)
{
	(void)access_fault(nondet_u64());
	__CPROVER_assert(0, "reach");
}

void reach_htinst_accepted(void)
{
	(void)htinst_accepted(nondet_u64(), nondet_u64());
	__CPROVER_assert(0, "reach");
}

void reach_inside(void)
{
	be_u64 base = nondet_u64();
	be_u64 bytes = nondet_u64();

	__CPROVER_assume(bytes <= ~(be_u64)0 - base);
	(void)inside(nondet_u64(), base, bytes);
	__CPROVER_assert(0, "reach");
}

void reach_leaf_at(void)
{
	struct be_mvp_gstage_leaves leaves = nondet_leaves();

	pages_nowrap(&leaves);
	(void)leaf_at(&leaves, nondet_u64());
	__CPROVER_assert(0, "reach");
}

/* ... and a contradictory assumption is detected: assert(0) holds. */
void contradiction_be_mvp_denial_decide(void)
{
	struct be_mvp_gstage_map map = nondet_map();

	__CPROVER_assume(map.size < 1U && map.size > 1U);
	__CPROVER_assert(0, "contradiction");
}

void contradiction_access_fault(void)
{
	be_u64 scause = nondet_u64();

	__CPROVER_assume(scause < 20U && scause > 23U);
	(void)access_fault(scause);
	__CPROVER_assert(0, "contradiction");
}

void contradiction_htinst_accepted(void)
{
	be_u64 htinst = nondet_u64();

	__CPROVER_assume(htinst < 1U && htinst > 1U);
	(void)htinst_accepted(nondet_u64(), htinst);
	__CPROVER_assert(0, "contradiction");
}

void contradiction_inside(void)
{
	be_u64 bytes = nondet_u64();

	__CPROVER_assume(bytes < 1U && bytes > 1U);
	(void)inside(nondet_u64(), nondet_u64(), bytes);
	__CPROVER_assert(0, "contradiction");
}

void contradiction_leaf_at(void)
{
	struct be_mvp_gstage_leaves leaves = nondet_leaves();

	__CPROVER_assume(leaves.page[0].bytes < 1U && leaves.page[0].bytes > 1U);
	(void)leaf_at(&leaves, nondet_u64());
	__CPROVER_assert(0, "contradiction");
}

/* Every case the contract names is reachable (cbmc --cover cover). */
void cover_decide(void)
{
	struct be_mvp_state state = nondet_state();
	struct be_mvp_gstage_map map = nondet_map();
	struct be_mvp_gstage_leaves leaves = nondet_leaves();
	struct be_mvp_exit record = nondet_exit();
	struct be_mvp_denial out;
	int result;

	preconditions(&map, &leaves);
	result = be_mvp_denial_decide(&state, &map, &leaves, &record, &out);
	__CPROVER_cover(result == 1 && out.kind == 0U);
	__CPROVER_cover(result == 1 && out.kind == 1U);
	__CPROVER_cover(result == 0);
	/* A store to a declared read-only page inside the window, every other
	 * condition of the entry met: refused [R1-1]. */
	__CPROVER_cover(result == 0 && state.accept_denial == 1U &&
			e2(&record) && e3(&record) &&
			record.frame.htval < ((be_u64)1 << 39) &&
			htinst_ok(record.frame.scause, record.htinst) &&
			e6(&record) && in_window(&map, &record) &&
			read_only(&leaves, &record));
	__CPROVER_cover(result == 0 && state.accept_denial == 1U && e2(&record) &&
			e3(&record) && map.size != 0U);
	__CPROVER_cover(result == 1 && (record.hstatus & 0x100U) == 0U &&
			(record.vsstatus & 2U) != 0U);
}
