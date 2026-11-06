/* SPDX-License-Identifier: GPL-3.0-only */
/* Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> */
/*
 * Purpose: the CN arm's annotated copy of Leaf A (planning/mvp-m8-plan.md,
 *          D-4, D-5, D-7, M8-6): access_fault, htinst_accepted, inside,
 *          leaf_at, and be_mvp_denial_decide as mvp/src/mvp-sbi.c holds
 *          them, with the contract of planning/mvp-m8-specifications.md
 *          section 4 as its Revision 1 states it (SHA-256
 *          aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b,
 *          accepted at 93a8d136; the clauses it corrected are marked
 *          [R1-n] below) in CN's magic comments. This run's round 0 is the
 *          first run's copy through its round 1 (against the accepted text
 *          of 004f31ae; mvp/results/20261103-verify/leaf-a/cn/) re-made
 *          against Revision 1: the helpers' clauses that run added in its
 *          round 1 are section 4.5's now [R1-3]; its round 1's three cases
 *          of D_complete are not restated (Revision 1's E7 and section 4.3
 *          exclude the first two, and the third is D_complete itself). The
 *          token gate (tools/token-equal.py --copy) shows the code is the
 *          source's: every comment dropped, the tokens equal the five
 *          functions', and only the source's own #include lines come
 *          first.
 * Trust:   every requires is section 4.3's or 4.5's; every ensures is a
 *          goal. A clause's first line carries a tag comment: `goal NAME`
 *          (tools/cn-arm.py proves each goal of a function in a run of
 *          its own, the function's other goals left out, its requires and
 *          ownership kept), and `rN` for an annotation round N's
 *          addition (round 0, the transcription, has none). The array of
 *          leaves has BE_MVP_PAGES_MAX = 3 entries (the type's): "some
 *          page" and "the lowest index" are written over indices 0 to 2.
 *          CN reserves `map` and `W` as keywords: tools/cn-arm.py runs CN
 *          with -Dmap=be_cn_map (the C identifier renamed everywhere, so
 *          the specification names the parameter be_cn_map), and the
 *          specification's W(p) is W_SET here. Each opening line of a
 *          specification is untagged, so no goal's run removes it.
 * Scope:   Leaf A only; this file is never compiled into the monitor.
 */
#include "mvp.h"
#include "mvp-ring.h"
#include "mvp-sbi.h"

/*@
function (integer) BIT(integer v, integer n) { shift_right(v, n) & 1 }
function (integer) SPV(integer h) { BIT(h, 7) }
function (integer) SPVP(integer h) { BIT(h, 8) }
function (integer) GVA(integer h) { BIT(h, 6) }
function (integer) GPA(integer htval, integer stval) {
  shift_left(htval, 2) | (stval & 3) }
function (integer) OPCODE(integer i) { shift_right(i, 2) & 31 }
function (boolean) HTINST_OK(integer scause, integer i) {
  i == 0 ||
  (i < 4294967296 && (i & 1) == 1 &&
   ((scause == 21 && OPCODE(i) == 0) ||
    (scause == 23 && (OPCODE(i) == 8 || OPCODE(i) == 11)))) }
function (boolean) INSIDE(integer a, integer base, integer n) {
  base <= a && a < base + n }
function (boolean) IN_PAGE(struct be_mvp_gstage_leaves l, integer i,
                           integer gpa) {
  l.page[i].bytes > 0 && INSIDE(gpa, l.page[i].gpa, l.page[i].bytes) }
function (boolean) HAS_PAGE(struct be_mvp_gstage_leaves l, integer gpa) {
  IN_PAGE(l, 0, gpa) || IN_PAGE(l, 1, gpa) || IN_PAGE(l, 2, gpa) }
// MAPPED, kept as section 4.1 keeps it; E7 does not use it [R1-1].
function (boolean) MAPPED(struct be_mvp_gstage_map m,
                          struct be_mvp_gstage_leaves l, integer gpa) {
  INSIDE(gpa, m.gpa_base, m.size) || HAS_PAGE(l, gpa) }
function (boolean) PAGE_IS(struct be_mvp_gstage_leaves l, integer i,
                           integer gpa) {
  (i == 0 && IN_PAGE(l, 0, gpa)) ||
  (i == 1 && !IN_PAGE(l, 0, gpa) && IN_PAGE(l, 1, gpa)) ||
  (i == 2 && !IN_PAGE(l, 0, gpa) && !IN_PAGE(l, 1, gpa) &&
   IN_PAGE(l, 2, gpa)) }
function (boolean) W_SET(integer pte) { BIT(pte, 2) == 1 }
function (boolean) PAGE_READ_ONLY(struct be_mvp_gstage_leaves l,
                                  integer gpa) {
  (PAGE_IS(l, 0, gpa) && !W_SET(l.page[0].pte)) ||
  (PAGE_IS(l, 1, gpa) && !W_SET(l.page[1].pte)) ||
  (PAGE_IS(l, 2, gpa) && !W_SET(l.page[2].pte)) }
// 1, 5, 7 for 20, 21, 23; access_fault is 0 elsewhere [R1-3].
function (integer) ACCESS_FAULT(integer scause) {
  scause == 20 ? 1 : (scause == 21 ? 5 : (scause == 23 ? 7 : 0)) }
function (integer) VSTVEC_MODE(integer v) { v & 3 }
function (integer) GPA_OF(struct be_mvp_exit r) {
  GPA(r.frame.htval, r.frame.stval) }
function (boolean) E1(struct be_mvp_state s) { s.accept_denial == 1 }
function (boolean) E2(struct be_mvp_exit r) {
  r.frame.scause == 20 || r.frame.scause == 21 || r.frame.scause == 23 }
function (boolean) E3(struct be_mvp_exit r) {
  SPV(r.hstatus) == 1 && SPVP(r.hstatus) == 0 && GVA(r.hstatus) == 1 }
function (boolean) E4(struct be_mvp_exit r) {
  r.frame.htval < 549755813888 }
function (boolean) E5(struct be_mvp_exit r) {
  HTINST_OK(r.frame.scause, r.htinst) }
function (boolean) E6(struct be_mvp_exit r) {
  VSTVEC_MODE(r.frame.vstvec) == 0 || VSTVEC_MODE(r.frame.vstvec) == 1 }
function (boolean) IN_WINDOW(struct be_mvp_gstage_map m,
                             struct be_mvp_exit r) {
  INSIDE(GPA_OF(r), m.gpa_base, m.size) }
// E7's unmapped case: PAGE(GPA) does not exist [R1-1].
function (boolean) UNMAPPED(struct be_mvp_gstage_leaves l,
                            struct be_mvp_exit r) {
  !HAS_PAGE(l, GPA_OF(r)) }
// E7's read-only case: cause 23, PAGE(GPA) exists and lacks W.
function (boolean) READ_ONLY(struct be_mvp_gstage_leaves l,
                             struct be_mvp_exit r) {
  r.frame.scause == 23 && PAGE_READ_ONLY(l, GPA_OF(r)) }
// The GPA outside the window first, for every cause, then either case
// [R1-1].
function (boolean) E7(struct be_mvp_gstage_map m,
                      struct be_mvp_gstage_leaves l, struct be_mvp_exit r) {
  !IN_WINDOW(m, r) && (UNMAPPED(l, r) || READ_ONLY(l, r)) }
function (boolean) ENTRY(struct be_mvp_state s, struct be_mvp_gstage_map m,
                         struct be_mvp_gstage_leaves l,
                         struct be_mvp_exit r) {
  E1(s) && E2(r) && E3(r) && E4(r) && E5(r) && E6(r) && E7(m, l, r) }
@*/

/* The access fault a guest-page fault is delivered as (Q5), or 0. */
static be_u64 access_fault(be_u64 scause)
/*@ ensures true;
            (scause == 20 || scause == 21 || scause == 23) implies // goal AF_cause
              return == ACCESS_FAULT(scause);
            !(scause == 20 || scause == 21 || scause == 23) implies // goal AF_other
              return == 0;
@*/
{
	if (scause == BE_MVP_SCAUSE_FETCH_GUEST_PAGE_FAULT)
		return BE_MVP_SCAUSE_FETCH_ACCESS_FAULT;
	if (scause == BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT)
		return BE_MVP_SCAUSE_LOAD_ACCESS_FAULT;
	if (scause == BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT)
		return BE_MVP_SCAUSE_STORE_ACCESS_FAULT;
	return 0U;
}

/*
 * htinst: zero; or a transformed load (cause 21) or store or AMO (cause
 * 23), whose bit 0 is set and whose bits 6:2 are the major opcode. A
 * pseudoinstruction (bits 1:0 clear: an implicit VS-stage access), a
 * custom value, a fetch's nonzero value, and any other opcode are refused.
 */
static int htinst_accepted(be_u64 scause, be_u64 htinst)
/*@ ensures true;
            (return == 1) == HTINST_OK(scause, htinst); // goal HI_iff
            return == 0 || return == 1; // goal HI_bool
@*/
{
	be_u64 opcode = (htinst >> BE_MVP_HTINST_OPCODE_SHIFT) &
			BE_MVP_HTINST_OPCODE_MASK;

	if (htinst == 0U)
		return 1;
	if (htinst >= BE_MVP_HTINST_LIMIT ||
	    (htinst & BE_MVP_HTINST_TRANSFORMED) == 0U)
		return 0;
	if (scause == BE_MVP_SCAUSE_LOAD_GUEST_PAGE_FAULT)
		return opcode == BE_MVP_OPCODE_LOAD;
	if (scause == BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT)
		return opcode == BE_MVP_OPCODE_STORE ||
		       opcode == BE_MVP_OPCODE_AMO;
	return 0;
}

static int inside(be_u64 address, be_u64 base, be_u64 bytes)
/*@ requires base + bytes < 18446744073709551616;
    ensures true;
            (return == 1) == INSIDE(address, base, bytes); // goal IN_iff
            return == 0 || return == 1; // goal IN_bool
@*/
{
	return bytes != 0U && address >= base && address - base < bytes;
}

/* The walked leaf of the root's page that holds @gpa, or none. */
static const struct be_mvp_gstage_leaf *
leaf_at(const struct be_mvp_gstage_leaves *leaves, be_u64 gpa)
/*@ requires take L = RW<struct be_mvp_gstage_leaves>(leaves);
             L.page[0].gpa + L.page[0].bytes < 18446744073709551616;
             L.page[1].gpa + L.page[1].bytes < 18446744073709551616;
             L.page[2].gpa + L.page[2].bytes < 18446744073709551616;
    ensures take L2 = RW<struct be_mvp_gstage_leaves>(leaves);
            L2 == L; // goal LA_frame
            PAGE_IS(L, 0, gpa) implies ptr_eq(return, // goal LA_page_0
              array_shift<struct be_mvp_gstage_leaf>(member_shift<struct be_mvp_gstage_leaves>(leaves, page), 0));
            PAGE_IS(L, 1, gpa) implies ptr_eq(return, // goal LA_page_1
              array_shift<struct be_mvp_gstage_leaf>(member_shift<struct be_mvp_gstage_leaves>(leaves, page), 1));
            PAGE_IS(L, 2, gpa) implies ptr_eq(return, // goal LA_page_2
              array_shift<struct be_mvp_gstage_leaf>(member_shift<struct be_mvp_gstage_leaves>(leaves, page), 2));
            !HAS_PAGE(L, gpa) implies is_null(return); // goal LA_none
@*/
{
	be_u64 index;

	for (index = 0U; index < BE_MVP_PAGES_MAX; ++index)
		/*@ inv take Li = RW<struct be_mvp_gstage_leaves>(leaves);
		        Li == L;
		        {leaves} unchanged; {gpa} unchanged;
		        index <= 3;
		        index <= 0 || !IN_PAGE(L, 0, gpa);
		        index <= 1 || !IN_PAGE(L, 1, gpa);
		        index <= 2 || !IN_PAGE(L, 2, gpa);
		@*/
		if (inside(gpa, leaves->page[index].gpa,
			   leaves->page[index].bytes))
			return &leaves->page[index];
	return (const struct be_mvp_gstage_leaf *)0;
}

int be_mvp_denial_decide(const struct be_mvp_state *state,
			 const struct be_mvp_gstage_map *map,
			 const struct be_mvp_gstage_leaves *leaves,
			 const struct be_mvp_exit *record,
			 struct be_mvp_denial *out)
/*@ requires take S = RW<struct be_mvp_state>(state);
             take M = RW<struct be_mvp_gstage_map>(be_cn_map);
             take L = RW<struct be_mvp_gstage_leaves>(leaves);
             take R = RW<struct be_mvp_exit>(record);
             take O = W<struct be_mvp_denial>(out);
             M.size > 0; // [R1-2]
             M.gpa_base + M.size < 18446744073709551616;
             L.page[0].gpa + L.page[0].bytes < 18446744073709551616;
             L.page[1].gpa + L.page[1].bytes < 18446744073709551616;
             L.page[2].gpa + L.page[2].bytes < 18446744073709551616;
    ensures take S2 = RW<struct be_mvp_state>(state);
            take M2 = RW<struct be_mvp_gstage_map>(be_cn_map);
            take L2 = RW<struct be_mvp_gstage_leaves>(leaves);
            take R2 = RW<struct be_mvp_exit>(record);
            take O2 = RW<struct be_mvp_denial>(out);
            S2 == S && M2 == M && L2 == L && R2 == R; // goal D_frame
            return == 0 || return == 1; // goal D_result
            return == 1 implies E1(S); // goal D_E1
            return == 1 implies E2(R); // goal D_E2
            return == 1 implies E3(R); // goal D_E3
            return == 1 implies E4(R); // goal D_E4
            return == 1 implies E5(R); // goal D_E5
            return == 1 implies E6(R); // goal D_E6
            return == 1 implies E7(M, L, R); // goal D_E7
            ENTRY(S, M, L, R) implies return == 1; // goal D_complete
            return == 1 implies O2.cause == R.frame.scause; // goal D_cause
            (return == 1 && UNMAPPED(L, R)) implies O2.kind == 0; // goal D_kind_unmapped
            (return == 1 && READ_ONLY(L, R)) implies O2.kind == 1; // goal D_kind_read_only
            return == 1 implies O2.gpa == GPA_OF(R); // goal D_gpa
            return == 1 implies O2.htval == R.frame.htval; // goal D_htval
            return == 1 implies O2.htinst == R.htinst; // goal D_htinst
            return == 1 implies O2.stval == R.frame.stval; // goal D_stval
            return == 1 implies O2.sepc == R.frame.sepc; // goal D_sepc
            return == 1 implies O2.vsstatus == R.vsstatus; // goal D_vsstatus
            return == 1 implies O2.vstvec == R.frame.vstvec; // goal D_vstvec
            return == 1 implies O2.time == R.time; // goal D_time
            return == 1 implies O2.inject_vscause == ACCESS_FAULT(R.frame.scause); // goal D_inject_vscause
            return == 1 implies O2.inject_vstval == R.frame.stval; // goal D_inject_vstval
            return == 1 implies O2.inject_vsepc == R.frame.sepc; // goal D_inject_vsepc
            return == 1 implies // goal D_inject_vsstatus_spp
              BIT(O2.inject_vsstatus, 8) == SPVP(R.hstatus);
            return == 1 implies // goal D_inject_vsstatus_spie
              BIT(O2.inject_vsstatus, 5) == BIT(R.vsstatus, 1);
            return == 1 implies BIT(O2.inject_vsstatus, 1) == 0; // goal D_inject_vsstatus_sie
            return == 1 implies // goal D_inject_vsstatus_rest
              (O2.inject_vsstatus & ~290) == (R.vsstatus & ~290);
            return == 1 implies O2.resume_pc == (R.frame.vstvec & ~3); // goal D_resume_pc
            return == 0 implies O2.cause == 0; // goal D_zero_cause
            return == 0 implies O2.kind == 0; // goal D_zero_kind
            return == 0 implies O2.gpa == 0; // goal D_zero_gpa
            return == 0 implies O2.htval == 0; // goal D_zero_htval
            return == 0 implies O2.htinst == 0; // goal D_zero_htinst
            return == 0 implies O2.stval == 0; // goal D_zero_stval
            return == 0 implies O2.sepc == 0; // goal D_zero_sepc
            return == 0 implies O2.vsstatus == 0; // goal D_zero_vsstatus
            return == 0 implies O2.vstvec == 0; // goal D_zero_vstvec
            return == 0 implies O2.time == 0; // goal D_zero_time
            return == 0 implies O2.inject_vscause == 0; // goal D_zero_inject_vscause
            return == 0 implies O2.inject_vstval == 0; // goal D_zero_inject_vstval
            return == 0 implies O2.inject_vsepc == 0; // goal D_zero_inject_vsepc
            return == 0 implies O2.inject_vsstatus == 0; // goal D_zero_inject_vsstatus
            return == 0 implies O2.resume_pc == 0; // goal D_zero_resume_pc
@*/
{
	const struct be_r4_frame *frame;
	const struct be_mvp_gstage_leaf *leaf;
	be_u64 origin = BE_MVP_HSTATUS_SPV | BE_MVP_HSTATUS_SPVP |
			BE_MVP_HSTATUS_GVA;
	be_u64 vscause;
	be_u64 gpa;
	be_u64 kind;

	if (out == (struct be_mvp_denial *)0)
		return 0;
	*out = (struct be_mvp_denial){ 0 };
	if (state == (const struct be_mvp_state *)0 ||
	    map == (const struct be_mvp_gstage_map *)0 ||
	    leaves == (const struct be_mvp_gstage_leaves *)0 ||
	    record == (const struct be_mvp_exit *)0 ||
	    state->accept_denial != 1U || map->size == 0U)
		return 0;
	frame = &record->frame;
	vscause = access_fault(frame->scause);
	/* From VU mode, stval a guest virtual address; no alias bit. */
	if (vscause == 0U ||
	    (record->hstatus & origin) !=
		    (BE_MVP_HSTATUS_SPV | BE_MVP_HSTATUS_GVA) ||
	    frame->htval >= BE_MVP_HTVAL_LIMIT ||
	    !htinst_accepted(frame->scause, record->htinst) ||
	    (frame->vstvec & BE_MVP_VSTVEC_MODE_MASK) >
		    BE_MVP_VSTVEC_VECTORED)
		return 0;
	gpa = frame->htval << BE_MVP_HTVAL_SHIFT |
	      (frame->stval & BE_MVP_GPA_LOW_MASK);
	/* The place: no mapping, or a page whose leaf lacks W. */
	if (inside(gpa, map->gpa_base, map->size))
		return 0;
	leaf = leaf_at(leaves, gpa);
	if (leaf == (const struct be_mvp_gstage_leaf *)0)
		kind = BE_MVP_DENIAL_UNMAPPED;
	else if (frame->scause == BE_MVP_SCAUSE_STORE_GUEST_PAGE_FAULT &&
		 (leaf->pte & BE_MVP_PTE_W) == 0U)
		kind = BE_MVP_DENIAL_READ_ONLY;
	else
		return 0;
	out->cause = frame->scause;
	out->kind = kind;
	out->gpa = gpa;
	out->htval = frame->htval;
	out->htinst = record->htinst;
	out->stval = frame->stval;
	out->sepc = frame->sepc;
	out->vsstatus = record->vsstatus;
	out->vstvec = frame->vstvec;
	out->time = record->time;
	/* The trap into VS mode the guest would take (Q5). */
	out->inject_vscause = vscause;
	out->inject_vstval = frame->stval;
	out->inject_vsepc = frame->sepc;
	out->inject_vsstatus = (record->vsstatus &
				~(BE_MVP_VSSTATUS_SPP | BE_MVP_VSSTATUS_SPIE |
				  BE_MVP_VSSTATUS_SIE)) |
			       ((record->hstatus & BE_MVP_HSTATUS_SPVP) != 0U ?
				BE_MVP_VSSTATUS_SPP : 0U) |
			       ((record->vsstatus & BE_MVP_VSSTATUS_SIE) != 0U ?
				BE_MVP_VSSTATUS_SPIE : 0U);
	out->resume_pc = frame->vstvec & ~BE_MVP_VSTVEC_MODE_MASK;
	return 1;
}
