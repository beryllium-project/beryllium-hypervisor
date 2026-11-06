<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M8 plan: the first verification plan

This plan bounds milestone **M8**, the first verification plan, which the
accepted
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
(`27d2e557`) of the [MVP plan](mvp-plan.md) defines in its section
S3-C.4 and authorizes writing. It is proposed on local branch
`beryllium/mvp-m8-plan` from `1b3f2e10`, the M7 result's acceptance
record, a linear descendant of the development branch's tip `f5dc770b`
(Q1). It is written on the orchestrating model under the standing split
(S3-C's D22); nothing in it is implementation.

## Decision record

The responsible human accepted this plan at exact commit
`7a0c74ae329c09282c5cf159076f5e99934ac4c2` (parent `1b3f2e10`, the M7
result's acceptance record, on branch `beryllium/mvp-m8-plan`) on
2026-11-02 (13:09 in the human's time zone) by the instruction `accept
7a0c74ae wuth CN, go for m9`, the reply to the
[review packet](mvp-m8-plan-review-summary.md)'s request; the
abbreviation resolves uniquely. `wuth CN` is read as `with CN`: the
answer to Q10 that the CN arm **is attempted** (the default's substance,
confirmed: a pinned Cerberus commit with Lem and each dependency pinned,
built offline in M8-5 within its time box; the recorded `not qualified`
fallback stands if the build does not succeed, the human having said
nothing against it). Q1 to Q9 and Q11 to Q17 apply at their defaults.
`go for m9` directs the M9 plan, written separately on its own branch.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted; only this
  section and the status block's trailing lines were set afterwards.
- **Authorization:** M8-2 to M8-7 on branch `beryllium/mvp-m8` from the
  acceptance-record commit, which is stage 1's target commit (Q2, Q46),
  coding and proof drafts on `claude-opus-5.5` sub-agents at the pinned
  effort and context tier under the session's orchestrating model, with
  the open questions as above, under the stop conditions; the
  specification document as its own exact commit for the human's review
  of record (D-6); item 103's two sentence corrections (Q13); the verifier
  image and `./mvp/mvp verify`; the ledger's stage-1 rows and, only on a
  positive pilot result, the two method terms and the fixed claim
  sentence. Nothing else: no board command, monitor change,
  accepted-byte or accepted-model change, push, merge, tag, publication,
  snapshot refresh, or kexec use. The instruction directed no
  fast-forward or push: the development branch stays at `6105c34d` (the
  M7 push record, which this branch took by merge before the acceptance
  record) and this branch is local.
- **The specification accepted (2026-11-02, 19:38 in the human's time
  zone):** `planning/mvp-m8-specifications.md` at exact commit
  `004f31ae0a44d74f4d46b87107843d9e96091758` (SHA-256
  `ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d`,
  frozen at `3c08c90e`) is accepted by the responsible human as reviewer
  of record (D-6) by the instruction `accept 004f31ae 004f31ae , ff +
  push m8 line, proceed`, the SHA repeated once and read as one
  acceptance. The document's bytes and hash are unchanged; the modules
  and the arms keep citing that hash. Three readings stage 1's proofs
  found before the acceptance are recorded here as **errata of the
  accepted specification**, not edits to it (an edit would re-freeze the
  hash and re-run every proof; the human may direct a Revision 1):
  - **S-1 (P1, `barrier_publication`):** "every word hart 0 wrote in
    `publish(d)`" includes the inbound ring's index words, which that ring's
    writer (hart 0) may write after the barrier and before `hart(d)`'s
    `ready(d)` (in `anchor`, a PAUSE delivered into domain 1's inbound ring
    before hart 2's `ready(1)`: the head reads 24, not the 0 `publish(1)`
    wrote). P1 holds for the block's immutable published words (the
    descriptor and its generation word, the first-entry frame, the walked
    map and leaves, the configuration), which is what I16's "immutable
    published data" names; the theorem is `barrier_publication_block`.
  - **S-2 (P5, `denial_iff_entry`):** "denied exactly when `Entry(e, d)`
    holds" omits the M0 plan's exit ceiling: an exit that satisfies
    `Entry` taken at the ceiling fails the domain instead of being denied,
    as the plans design. P5 holds below the ceiling; the theorem is
    `denial_iff_entry_below_ceiling`. Leaf A's contract (section 4) is
    unaffected: the ceiling is the caller's, not the decision function's.
  - **S-3 (P6, `parked_never_resumes`):** "takes no further step but
    `fail` or `end`'s observation" is too strong: a paused domain still
    takes TERMINATE from its inbound ring and posts TERMINATED (the M2
    plan's design). The theorem proves that a parked domain never exits or
    re-enters its guest and only serves its inbound ring or fails.
  - **S-4 (P6, `mgmt_answered_once`; found after the acceptance, M8-3's
    last commit):** "answered or refused exactly once" needs, for a
    delivered request, the target hart's progress (its park or shutdown
    produces the result to the requester), a liveness fact the finite SC
    traces do not give. The theorem keeps the name and proves the safety
    reading: each request has at most one decision (its answer or
    refusal) in every trace, and exactly one once the trace contains its
    `decide_mgmt` step; that a delivered request's later result is sent
    at most once is not claimed.
- **Erratum 1 (2026-11-02, stop condition 6):** by the plan's counting
  rule the model lane counts M8-2's tools (the generator 552, the drift
  check 377, the tools gate 61) beside the proof modules, so with
  `Concrete.v` (2,267) and `ConcreteRings.v` (3,021) committed it stood at
  6,278 of the 6,000 soft limit with three modules and the runner to
  come; the responsible human re-set the model lane to **12,000** (form
  answer `12000`), under the standing rule that a soft limit is
  re-evaluated, never cut. The "Soft limits" table is as accepted; this
  erratum governs.
- **Erratum 2 (2026-11-02, foreseen stop condition 6):** the bridge and
  contracts lane stood at 2,793 of 3,000 after M8-5's qualification
  fixtures and tools, before M8-4's litmus tests and M8-6's harnesses and
  annotations; asked once rather than stopped mid-work, the human re-set
  the lane to **6,000** (form answer `bridge_lane_limit=6000`). The
  table is as accepted; this erratum governs.
- **Stop 5, the WP arm's solver pair (2026-11-02):** M8-5's
  qualification found WP with Z3 `4.16.0` through why3 `1.8.2` unsound on
  WP's own integer prelude (Z3 answers `unsat` with no goal, so it
  "proves" `ensures \false`; the reproducer is kept) and WP with cvc5
  `1.3.4` not terminating under WP's default memory limit, so the WP arm
  cannot form D-7 item 7's Z3 and cvc5 pair; CN qualified with both and
  CBMC with its SAT solver and cvc5. The human chose **A** (form answer
  `wp_arm=A`): WP runs with Alt-Ergo `2.4.3` alone as a **recorded arm
  that cannot meet item 7**, CN is the arm that can give a positive
  result, and the plan is unchanged; D-7 stands as accepted.
- **Stop 2, the specification against the leaves (2026-11-03):** the
  pilot's arms, run against the accepted specification `004f31ae`, found
  nine clauses where its text disagrees with the leaves (two on Leaf A:
  E7's read-only case did not exclude the window; the preconditions
  admitted `map.size = 0`; seven on Leaf B: `init`'s domain and `limit`,
  the tail bounded by the published head in `post` and `room`, the head
  bounded by the released tail in `acquire`, `taken` as a writer view,
  the sequence property's `room`). In every case the leaf does what the
  accepted M1 plan's "The accepted entry" or the ring header's contract
  says and the host tests pin: the session's reading, which the human
  took, is **nine specification errata, no code defect**. The human
  decided (form answer `spec_mismatches=revision_1_rerun`): the clauses
  are corrected in the specification's **Revision 1**, exact commit
  `93a8d136` (SHA-256
  `aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b`),
  re-frozen and presented for acceptance (**accepted 2026-11-03**,
  instruction `accept 93a8d136`; the
  [Revision 1 review packet](mvp-m8-specifications-revision-1-review-summary.md)
  is its review and acceptance record), and the three arms (WP, CN, CBMC
  on both leaves) are re-run against it; the arms' records against the
  accepted first text are retained under
  `mvp/results/20261103-verify/` as the finding's evidence. Stage 1's
  modules keep citing the accepted hash (their sections 1 to 3 are
  unchanged by Revision 1). No monitor source changes.
- **Erratum 3 (2026-11-03, stop condition 6):** the bridge and contracts
  lane stood at about 9,250 of the 6,000 erratum 2 set (Leaf A's
  annotations, harness, and runners 3,388; Leaf B's harnesses and runner
  3,066; the litmus tests' code 1,357 and records 626; M8-5's 2,793): the
  plan's estimate for the harnesses and runners undershot by about four
  times. The human re-set the lane to **12,000** (form answer
  `bridge_limit=12000`); the table is as accepted, this erratum governs.
- **The arms' recorded results against the accepted text (2026-11-03),
  before the re-run:** WP on Leaf A OPEN (123 of 132 goals; Alt-Ergo
  alone; the open goals the two errata and five true goals Alt-Ergo did
  not finish in 60 s, which CBMC confirms); CN on Leaf A OPEN (5 of 58;
  the pair formed; tool limits: the compound literal's resource is never
  released, `leaf_at` needs a `focus` a braceless loop cannot hold,
  bitwise operators are uninterpreted); CBMC on Leaf A FAILED (333 of
  336; the three failures the two errata); CBMC on Leaf B OPEN (13,546
  of 15,037 checked; coverage and vacuity ok; the open rows the seven
  errata, the index-advance wrap sites the wording omitted, and the
  4,096-byte buffer parts' 3 of 512 position classes within the budget).
  Q17: WP's Rocq export is not qualified (why3 1.8.2 knows `coqtop` 8.16
  to 8.20; the image has `rocq` 9.3.0). Q8: the ACSL importer placed
  every annotation Leaf A needed; no annotated copy for WP.
- **The arms' re-run against Revision 1 (2026-11-03; records
  `mvp/results/20261103-verify-r1/`; merged `2e298c3a`):** every arm
  re-transcribed to R1-1 to R1-9 and run in the verifier (3 h 44 min).
  WP on Leaf A OPEN (130 of 134; round 1 a ladder of assertions closes
  `D_resume_pc`; the four `vsstatus` goals are true, as CBMC shows, and
  time out in Alt-Ergo; a tried round 2 slowed other goals past the
  budget and was not adopted); CN on Leaf A OPEN (5 of 55; the same tool
  limits); CBMC on Leaf A **SUCCESSFUL** (336 of 336 at unwind 4, the
  `sat` and `cvc5` solvers; 22 mutants killed, 1 unobservable, 1 contract
  finding: m12's null test on `out`, which the host test exercises outside
  the contract's domain; vacuity ok; two dead code paths under the
  contract: the `SPVP` arm under E3 and the `map->size == 0` test under
  R1-2); CBMC on Leaf B OPEN (13,547 of 14,931 checked; the open rows the
  4,096-byte buffer parts' 3 of 512 classes within the budget; the first
  run's seven errata closed; the 20 wrap sites intended under R1-9).
  `digests.py` hashes the host's export of the pinned specification
  inside the image, which has no git (`b2f40b1d`).
- **Stop 2, the second time (2026-11-03), decided erratum S-5:** the
  ring's `room` property fails against Revision 1 on both solvers at both
  capacities: `be_mvp_ring_room` also treats a tail more than a capacity
  behind the **cursor** as malformed and fails the view, as its header
  contract says (a malformed tail fails the view), where R1-6's `room`
  row defines "well formed" by the published head alone (`limit − t ≤
  C`); a host reproducer confirms four contradictions (a record posted
  and not published, the tail at `C` and `C − 8` behind the head); the
  state needs a tail value no release writes, which the row's "for any
  peer index value" admits. A specification erratum, not a code defect.
  The human chose **A** (form answer `room_row=erratum_s5`): recorded
  here as **erratum S-5** (the `room` row's well-formedness includes
  `cursor − t ≤ C`), no Revision 2 and no re-run, since the ring arm's
  outcome is OPEN at its bound either way; the document's text stays
  Revision 1's.
- **The outcome (D-7; 2026-11-03, the human's `outcome_reading=true`):
  inconclusive** for a C-level contract proof of Leaf A in M8's box: no
  arm met items 1 to 7 (WP: four true goals time out, and Alt-Ergo alone
  cannot meet item 7 since stop 5's decision A; CN: tool limits, the
  compound literal's resource, `leaf_at`'s liveness, uninterpreted bitwise
  operators; CBMC: bounded by construction at unwind 4 and the `sat` and
  `cvc5` pair rather than Z3 and cvc5, Z3 having been non-terminating on
  CBMC's vacuity case in qualification). Not "no vehicle fits": CN's
  grounds are tool limits a later toolchain may lift, not structural. The
  recommendation per claim class, non-load-bearing until the promotion
  gates hold: (a) pure decision functions: CN remains the vehicle that
  can give a proof, with WP under Alt-Ergo as the specification-debugging
  arm and CBMC's bounded check beside them; (b) ring-class code: CBMC's
  bounded per-call checks with the protocol's obligations in stage 1;
  (c) the cross-hart protocol: stage 1 with its litmus premises; (d)
  compiled execution: assumed, the locked compilers and the executor. The
  claim is unchanged, the ledger gains the stage-1 rows and the review
  item (D-11), and the pre-authorized sentence is not added.
- **The result (2026-11-04):** the responsible human accepted the M8
  result at exact commit `12b0e71b908e36041745601d214c03a5be34ad1e`
  (over the gates' commit `f1813841`, which holds the re-run's merge, the
  ledger's rows, and item 93's dry-run fix cherry-picked from M9's
  accepted line) by the instruction `accept 12b0e71b`
  ([the result review summary](mvp-m8-result-review-summary.md) is its
  review and acceptance record; [the evidence record](mvp-m8-evidence.md)
  the evidence), with the outcome above as recorded, the fourteen
  specification errata as errata, and items 124 (the per-lane ledger IDs)
  and 125 (the tool limits met) as presented. No fast-forward, push, or
  successor was directed; M10's plan may be written on the human's `go`,
  M7's, M8's, and M9's results being accepted.

## Status

```text
m8_status=accepted
m8_plan_target=7a0c74ae329c09282c5cf159076f5e99934ac4c2
m8_plan_parent=1b3f2e10
m8_acceptance_instruction=accept-7a0c74ae-wuth-CN-go-for-m9;read-as-with-CN
m8_acceptance_date=2026-11-02
m8_acceptance_record=mvp-m8-plan-review-summary.md
m8_open_questions_answered=Q10-with-CN-attempted-fallback-stands;Q1-Q9-Q11-Q17-defaults
m8_authorization=M8-2..M8-7-on-beryllium/mvp-m8-from-the-acceptance-record;2026-11-02;specifications-as-own-commit-for-review-of-record;no-ff-no-push-directed
m8_implementation_branch=beryllium/mvp-m8
m8_specifications=accepted;planning/mvp-m8-specifications.md;commit-004f31ae;sha256-ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d;frozen-2026-11-02;accepted-2026-11-02-instruction-accept-004f31ae;revision-1-accepted-2026-11-03-at-93a8d136-sha256-aeb75682-the-arms'-hash;stage-1-cites-the-first-hash
m8_specification_errata=S-1-P1-block-immutable-words-only;S-2-P5-below-the-exit-ceiling;S-3-P6-parked-still-takes-terminate;S-4-P6-answered-once-as-safety-decisions-counted;recorded-in-the-decision-record-not-the-document
m8_stage1=complete;merged-5f02a5f3;theorems-26-closed-26;citations-92;model-lane-8425-of-12000;make-proof-115s
m8_erratum_1=model-lane-soft-limit-re-set-6000-to-12000;2026-11-02;form-answer-12000;6278-with-two-of-five-modules
m8_erratum_2=bridge-lane-soft-limit-re-set-3000-to-6000;2026-11-02;form-answer-6000;2793-after-M8-5
m8_erratum_3=bridge-lane-soft-limit-re-set-6000-to-12000;2026-11-03;form-answer-12000;about-9250-after-M8-6
m8_specifications_revision_1=accepted-93a8d136d38547a8c581197315f7607b5eef7bad;sha256-aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b;2026-11-03;instruction-accept-93a8d136;R1-1..R1-9;nine-errata-no-code-defect;stop-2-decision-revision_1_rerun;arms-re-run-directed;record-mvp-m8-specifications-revision-1-review-summary.md
m8_m8_6_first_run=against-004f31ae;WP-OPEN-123-of-132;CN-OPEN-5-of-58;CBMC-leaf-A-FAILED-333-of-336;CBMC-ring-OPEN-13546-of-15037;records-mvp/results/20261103-verify;merged-bc98a875-0b45698e
m8_stops_fired=6-model-lane-re-set-by-erratum-1;6-bridge-lane-re-set-in-advance-by-erratum-2;5-WP-solver-pair-decision-A;2-nine-specification-errata-revision-1;6-bridge-lane-re-set-by-erratum-3
m8_wp_arm=recorded-arm-cannot-meet-D-7-item-7;Alt-Ergo-alone;decision-A-2026-11-02;CN-the-arm-that-can-give-a-positive-result
m8_development_branch=fast-forwarded-and-pushed-with-the-M8-line-on-ff-+-push-m8-line-2026-11-02
m8_plan_branch=beryllium/mvp-m8-plan
m8_plan_base=1b3f2e10;the-M7-acceptance-record;descendant-of-dev-tip-f5dc770b
m8_governing_text=mvp-plan.md-S3-C.4;S3-C.7-M8-lane-and-pre-authorization;S3-C.8-D22-stops-d-e-i;Q34-Q38-Q41-Q42-Q46-defaults
m8_work_packages=M8-1..M8-7
m8_open_questions=Q1-Q17-defaults
m8_soft_limits=model-6000-rocq-lines;bridge-and-contracts-3000;tool-glue-2500;proof-time-600s;tools-at-most-10
m8_target_commit=this-plan's-acceptance-record-commit;Q46-default
m8_board=none
m8_claim_change=only-on-a-positive-pilot-result;the-fixed-sentence-below
m8_authorization_if_accepted=M8-2..M8-7-on-beryllium/mvp-m8-from-the-acceptance-record;the-specifications-as-their-own-exact-commit-for-the-human's-review-of-record;item-103's-two-document-corrections
m8_m8_6_rerun=against-93a8d136;WP-OPEN-130-of-134;CN-OPEN-5-of-55;CBMC-leaf-A-SUCCESSFUL-336-of-336-unwind-4-sat-cvc5;CBMC-ring-OPEN-13547-of-14931;records-mvp/results/20261103-verify-r1;merged-2e298c3a;wall-13462s
m8_erratum_s5=room-row-R1-6-well-formedness-includes-cursor-minus-t-le-C;2026-11-03;form-answer-room_row=erratum_s5;no-revision-2-no-re-run;host-reproducer-contradictions-4
m8_outcome=inconclusive;no-arm-met-D-7-items-1-7-on-Leaf-A;2026-11-03;outcome_reading=true;claim-unchanged;stage-1-rows-and-review-item;pre-authorized-sentence-not-added
m8_recommendation=a-pure-decision-functions-CN-with-WP-alt-ergo-debugging-and-CBMC-bounded;b-ring-class-CBMC-bounded-plus-stage-1;c-cross-hart-stage-1-with-litmus;d-compiled-execution-assumed;non-load-bearing
m8_result=accepted-12b0e71b908e36041745601d214c03a5be34ad1e;parent-9af19d81;gates-commit-f181384192bd4a79df52ba7cdb5dfbed55ab3307;2026-11-04;instruction-accept-12b0e71b;record-mvp-m8-result-review-summary.md;evidence-mvp-m8-evidence.md
m8_result_gates=seven-PASS-at-f1813841;standalone-clean-clone;2026-11-04-01:50-06:00-UTC;verify-wall-13480s;evaluate-315-of-315-identical
m8_result_lanes=model-8544-of-12000;bridge-11811-of-12000;glue-1473-of-2500;tools-9-of-10;model-gate-131s-of-600
m8_result_departures=item-93-fix-cherry-picked-f1813841;item-124-ledger-ids-per-lane;item-125-tool-limits;erratum-S-5
m8_result_push=none-directed;dev-at-55047781;branch-pushed-through-55047781
```

## Purpose

Say something bounded and true about the monitor's own C, and learn which
tool, if any, fits before committing more. Today every statement about
the implementation is a test, a check, an emulation, or a board run: the
claim's required limit says the barrier, the rings, the IPI protocol, the
control loop, the G-stage builder, the denial path, the management
decision, and the measurement "are covered by host tests, image and
capture checks, emulation, and the board runs, and by nothing else"
(`mvp/docs/claim.md`, the required limit), and the ledger's U-04, U-08,
U-11, and U-13 say where the model stops. M8 adds two things. **Stage 1**
is a concrete operational model of harts 0 to 2 in Rocq, beside M3's
accepted modules and importing them unedited: the hart blocks and their
generation words, the three single-writer rings per domain hart, the boot
barrier, the denial path, `pause` and `terminate`, and the measurement's
abstract measure-before-entry gate, with the memory-ordering premises
stated as theorem premises and checked as litmus tests on the compiled
sequences. **Stage 2** is a pilot: two C verification tools on one leaf,
`be_mvp_denial_decide` with its static helpers, and bounded model
checking on a second, `mvp-ring.c`, under a decision rule registered here
before any arm starts, with every arm qualified, time-boxed, and tested
against mutants. The outcome is one of three recorded results, each
accepted by the human: a vehicle recommended per claim class, inconclusive,
or no vehicle fits. Release candidate 4 waits on M8 **accepted**, not on
M8 successful (S3-C.4). The claim changes only on a positive pilot result,
and then only by the sentence S3-C.7 pre-authorizes, fixed in words below;
"formally verified" and every umbrella phrasing stay forbidden.

## Inputs

| Input | Exact commit | Role |
| --- | --- | --- |
| MVP plan with Plan revisions S3-A, S3-B, S3-C | `93967fba`; `0d134bbc`, `f8b77ac9`, `27d2e557` | M8's definition (S3-C.4), the lanes and the M8 pre-authorization (S3-C.7), D22 and stops (d), (e), (i) (S3-C.8), Q34 to Q38, Q41, Q42, Q46 at their defaults |
| M0 plan with Plan revisions M0-A to M0-C | `4d129808`; `30c5e1a8`, `77559def`, `260ceba6` | the hart region and blocks, the generation word, the single-writer rings, the boot barrier, the drain order (M0-C.1) |
| M1 plan and result | `7b2c055c`, `ff84533c` | the denial path's entry and injection; the channel page |
| M2 plan and result | `854a5415`, `18d552bc` | the management extension (`pause`, `terminate`, hart 0 decides), the measurement |
| M3 plan and result | `c2c249f4`, `b0a0f352` | `Policy.v` (A1 to A8), `Binding.v` (H0 to H3, `mvp_binding`, the footprints), `PolicyClaims.v`, the gate and its closed-assumption discipline |
| M6 result (release candidate 3) | `89ef04e9` | the executor and the seams, the layer table ("No contract is written yet; that is the first verification plan's") |
| M7 result | `e1a6395e` | the input ring, `InputRing.v`, the SBI version, the headers the leaves include |
| Security model v1 with Revisions 1 and 2 | `0e3eec8b`, `019cca64`, `afd395b8` | I13 to I18; the TCB; Part 5's triggers |
| S1 synthesis | `fd670dcd` | H22 (pure decision functions, host-tested), H38 and H41 (deferred to S3, resolved here), H42 (lessons not to transfer), H43 (the scope guard) |
| Project snapshot (release candidate 2) | `2c80835c`, `cd9cfa5f` | section 8: the stages, the stage-1 row, the Frama-C/WP evaluation note |
| Open tooling; implementation plan; research synthesis | maintained planning documents | the tool roles, CN's promotion gates, the VST route (item 103) |
| Debt sweep 4 | `d162c60d` | the escape-hatch pattern's plural keywords (item 102) |

## Facts the design rests on (read-only findings, 2026-11-02)

Every fact was read in the tree at `1b3f2e10`; the line numbers are that
tree's.

- **The first leaf is small and pure.** `be_mvp_denial_decide`
  (`mvp/src/mvp-sbi.c` L253-L323, declared and documented in
  `mvp/src/mvp.h` L948-L979) and its four static helpers `access_fault`
  (L200-L209), `htinst_accepted` (L217-L233), `inside` (L235-L238), and
  `leaf_at` (L241-L251) are 113 lines. Every parameter is a `const`
  pointer but `out`; the only writes are through `out` (L269,
  L300-L321); no helper reads a volatile object or calls outside the
  file; the one loop is `leaf_at`'s over `BE_MVP_PAGES_MAX` = 3
  (`mvp-layout.h` L186); there is no inline assembly, builtin, bit-field,
  union, or cast between pointer types (the casts are null-pointer
  constants). The parameter types (`struct be_mvp_state`, `mvp.h`
  L741-L753; `struct be_mvp_gstage_map`, `mvp-gstage.h` L133-L142;
  `struct be_mvp_gstage_leaves`, L219-L221; `struct be_mvp_exit`,
  `mvp.h` L312-L319, with `struct be_r4_frame`, `include/be/r4.h`
  L57-L68; `struct be_mvp_denial`, `mvp.h` L823-L839) have fixed-size
  arrays and no volatile, pointer-to-pointer, flexible, union, or
  bit-field member. Its callers are `be_mvp_handle_exit` (L586-L588) and
  `mvp/tests/deny-test.c` (38 scenarios, 2,933 assertions, `mvp/Makefile`
  L223-L224). The translation unit `mvp-sbi.c` (1,321 lines) includes
  `mvp.h`, `mvp-ring.h`, and `mvp-sbi.h` (L30-L32); the in-tree quoted
  closure is five headers, 2,880 lines, and the angle-bracket chain
  `<be/r4.h>` to `<be/types.h>` comes from the generated port directory
  (`-I$(PORT)/include`, `mvp/Makefile` L99), where `r4.h`, `r2.h`,
  `state.h`, and `types.h` equal the in-tree files and `r3.h` and
  `manifest.h` are the port's rewrites.
- **The second leaf is the ring.** `mvp/src/mvp-ring.c` (374 lines) and
  `mvp-ring.h` (315) hold twenty functions; the shared words are the two
  index lines (`volatile struct be_mvp_ring_index *head`, `*tail`,
  `mvp-ring.h` L89-L90; each alone in a 64-byte line, `mvp-ring.c`
  L29-L32) and the buffer; the indices are free-running byte counts,
  multiples of 8, compared by unsigned 64-bit differences (L129, L172,
  L174, L260-L261) and masked per byte by `capacity - 1` (L178, L289); the
  capacity is a power of two between 512 and `BE_MVP_OUTBOUND_RING_BYTES`
  (L120-L121); the loops are bounded by 8, 256, and 32 (L55, L66, L186,
  L234, L309); the file has no fence, atomic, or asm, and says so
  (L10-L14): the fences are the callers', through the executor
  (`mvp-executor.c` L152-L165; `mvp-trap.S` L375-L406, `fence w, w`,
  `fence r, r`, `fence r, w`, `fence rw, rw`), in the order the header's
  contract fixes (`mvp-ring.h` L5-L27): post, `fence w, w`, publish;
  acquire, `fence r, r`, take, `fence r, w`, release. Hart 0's and the
  domain harts' call sites are listed in the M8 fact sheet from
  `mvp-runtime.c` and `mvp-hartmain.c`. `mvp/tests/ring-test.c` has 160
  scenarios and 409,415 assertions, including a 4-capacity random
  single-threaded simulation with start indices near 2^64 (L993,
  L1091).
- **The accepted model is the foundation, and its readings are stale by
  line.** `model/proof/` holds 13 modules, 5,731 lines: Model 0.2's six
  (24 closed theorems), M3's four (`Policy.v` 2,002 lines, `Binding.v`
  787, `PolicyClaims.v` 220, `PolicyAssumptions.v` 35; 22 closed), the
  generated `Instances.v` stand-in, and M7's `InputRing.v` (386) with its
  4. `Binding.v` imports no project module; it defines `ring` as
  `InboundRing | OutboundRing` (L95-L97), the hart objects (L125-L142),
  `binding_instance` (L152-L162), the twenty transitions (L266-L286),
  the write `footprint` per transition (L362-L441), H3 as the
  single-writer obligation (L521-L544) with its executable `h3_check`
  (L596-L598) proved for `mvp_binding` (L782); `object_extents` gives
  ring objects no extent (L236). Every numeric constant `Binding.v`
  hard-codes agrees with `mvp/src/mvp-layout.h` at this commit (the
  block, region, window, and shared-page addresses and sizes; the hart
  ids), but its source-line citations are M3's: `publish_blocks` is
  cited at L1465-L1511 and is at L1544; `post_inbound` at L1568-L1582 and
  is at L1651; the binding table at L244 and is at L266; the
  control-stack note names `0x102027000`, which no source holds (item
  101). `InputRing.v` holds the three ring offsets and sizes (L159,
  L164-L165) and they agree with `mvp-layout.h` L112-L117.
- **The gate's shape.** `model/tests/run-proofs.sh` compiles the modules
  in explicit lists, checks them with `rocq check`, and counts "Closed
  under the global context" lines (24 and 22, L76 and L107); a new module
  is added either to those lists or, as M7 did, by its own runner
  appended to `model/Makefile`'s `proof` (L77-L79), which
  `run-input-ring.sh` does with its own escape-pattern grep, compile,
  check, and theorem-to-report equality (L28-L79). The escape pattern
  (`run-proofs.sh` L23) has its plural keywords since debt sweep 4
  (`check-escape-pattern.sh`); `generate-evidence.sh` hashes
  `find model -type f` (L32) and lists only `build/model/proof/checked/*.vo`
  and two logs as artifacts (L65-L71). The model's lock is Rocq 9.3,
  GCC 16.2.1, Clang 22.1.8, Node 22.23.1, Python 3.14.8
  (`model/toolchain.conf` L7-L14); the rootless evaluator builds
  `model/Containerfile` (Fedora by digest, `dnf install … rocq`) and runs
  `make -C model clean check` with `--network none` and the tree at
  `/work` (`run-rootless.sh` L46-L56); a linked worktree fails there
  (`gitfile` outside the mount) and the `.vo` files embed `/work`, so the
  evaluator's PASS lines, not byte identity, are its claim.
- **The tools Fedora 44 packages, and those it does not.** In the
  configured repositories: `frama-c-33.0-1.fc44` (`updates`; requires
  `why3`, `alt-ergo`, `gcc`), `why3-1.8.2-11.fc44`, `alt-ergo-2.4.3-1.fc44`
  (licence `CECILL-C`, a free licence), `z3-4.16.0-1.fc44` (`MIT`),
  `cvc5-1.3.4-1.fc44` (`BSD-3-Clause AND MIT`), `cbmc-6.8.0-1.fc44` with
  `cbmc-utils` (`BSD-4-Clause`), `rocq-core-9.3.0-1.fc44` and
  `rocq-stdlib`; `ocaml-5.4.0` is installed. **Not packaged:** CN and
  Cerberus, `herdtools7`, `isla`, CompCert, VST, RefinedC; `opam` is not
  installed. None of the pilot's tools is installed from an RPM on the
  workstation today: an unpackaged `cbmc` 6.8.0 and `z3` 4.15.4 sit in
  the user's `~/.local/bin` (Helium's), which no M8 run may use.
- **The evaluator's closure discipline.** The MVP evaluator image is
  built from a verified RPM cache of 259 NEVRAs with their SHA-256
  (`mvp/tools/lock/closure.txt`, bound by `MVP_CLOSURE_SHA256`), from a
  Fedora base by digest, with repositories disabled and no network at run
  time (`mvp/tools/evaluator/Containerfile` L36, L55-L61; `evaluate.sh`
  L143-L147, L189-L198); `tool-lock.py refresh` resolves the roles' owners
  and their requirements against the host's installed packages
  (L575-L604) and `fetch-closure.py --record` derives the digests from
  Fedora's repositories, the updates archive, or koji. The lock has no
  Rocq role; the model's evaluator is separate.
- **The protocol the plans state, and the gap the ledger names.** The M0
  plan fixes the block (L317-L330), the rings ("a head the writer owns
  and a tail the reader owns, each in its own 64-byte line … The writer
  copies a record, executes `fence w, w`, and advances the head; the
  reader reads the head, executes `fence r, r`, copies the record, and
  advances the tail", L340-L353; the code adds `fence r, w` before the
  tail, `mvp-ring.h` L15-L19), the generation word written last after
  `fence w, w` (L384-L388), the domain hart's check after `fence r, r`
  (L410-L412), and M0-C.1's round-robin drain. Security model v1's I15
  and I16 bind the writers per word and phase, with the scope note "they
  say nothing about concurrent execution, memory ordering, the IPI
  protocol, or the barrier's implementation" (L807-L810); I17 and I18 are
  M7's. U-11 is `not run`: "No host test exercises a fence, a cache, a
  second hart, or an IPI, and M3 does not model memory ordering".
- **The management path and the measurement gate.** `pause` and
  `terminate` are FIDs 0 and 1 of EID `0x08004245`; the domain hart posts
  one `MGMT_REQUEST`, sends one IPI, and waits in HS; hart 0 decides with
  `be_mvp_mgmt_decide` against the sealed grants (`INVALID_PARAM`,
  `DENIED`, `INVALID_STATE`, or delivered), delivers by the inbound ring
  with one IPI, and answers on the target's `PAUSED` or `TERMINATED`
  record (M2 plan L382-L406). The measurement precedes entry: in every
  retained `anchor` record `BE_MVP:06 MEASURED domain=1 … expected=match`
  prints before any `:08 HART_STARTED` and `:10 DOMAIN_ENTERED`
  (`mvp/results/20261031-com260-rc3/20261031T042103Z/handoff-excerpt.log`
  L45-L52), and a mismatch fails closed before any hart starts
  (`wrong-measurement`); M9 redefines the measurement's content, so stage
  1 models only the gate.
- **What the layer table says.** `mvp/README.md`'s "The monitor's layers
  (M6-3)" classifies `mvp-ring.h`/`.c` as proof-bearing, `mvp-sbi.c` as
  mixed (1,147 proof-bearing, 122 support), `mvp-runtime.c` and
  `mvp-hartmain.c` likewise, and totals 6,285 proof-bearing code lines;
  it is a reading at the M6-3 content (every file has grown since;
  `mvp-input.c` is absent from it) and says "No contract is written yet;
  that is the first verification plan's" (L1387-L1389).
- **The claim's slots.** The claim's forbidden phrasings (40 literals, 3
  conditionals, 2 review items; `mvp/docs/claim.md` L87-L148) include
  "formally verified", "verified hypervisor", "proven secure", and
  "audited"; the ledger's method vocabulary is ten terms with no C-level
  term (`claim-ledger.json` L8-L19); the required limit's sentence M8 may
  narrow on a positive result is at L70-L74.

## Design

### D-1 Stage 1: the concrete operational model, on M3's modules

A new family of modules under `model/proof/`, importing `Binding.v` and
`Policy.v` (and `InputRing.v`) unedited:

- **`Concrete.v`**: the state of harts 0 to 2 as the words of the two hart
  blocks and hart 0's control state, typed by `Binding.v`'s
  `hart_object` where one exists (the three index lines of each ring, the
  descriptors with their generation words, the first-entry frame, the
  walked map and leaves, the configuration, the control data) and by new
  objects for what `Binding.v` leaves without extent (the ring buffers'
  bytes, the state page's counters and phase); each hart's program as a
  labelled transition system whose steps are the plans' protocol steps
  refined to word reads and writes: the barrier's publication and the
  domain hart's check, each ring operation (post, publish, acquire, take,
  release, room, and the input ring's drop), hart 0's round-robin drain,
  the exit path (the exit record, the denial decision and its DENIAL
  record and injection), the management request, decision, delivery,
  park, and answer, the run's end; and the three harts' interleaving as
  the system's traces.
- **`ConcreteLayout.v`**, **generated** from `mvp/src/mvp-layout.h` by a
  small tool (`model/tools/gen-concrete-layout.py`: every `BE_MVP_*`
  macro of the form `BE_MVP_C(value)` becomes a Rocq definition with the
  header's SHA-256 in a comment), so that no layout constant is
  hand-copied again (item 101); a gate check regenerates it and requires
  byte equality, as `policy-fixtures-check` does for the instances.
- **`ConcreteRings.v`**: the ring protocol's invariants and the
  single-writer, no-overrun, FIFO-integrity, and fail-closed/drop
  properties for the three rings (P3, P4), with indices as 64-bit words
  (Q5) so that the wraparound the C relies on is modelled, and the
  capacity a parameter (any power of two in the C's range).
- **`ConcreteBridge.v`**: the **two first obligations** S3-C.4 names,
  proved: (1) every concrete step's write set lies within `Binding.v`'s
  `footprint mvp_binding` of the transition it refines, so H3
  (single-writer) carries over to the concrete model (P2); (2) the
  concrete roots, leaf rights, denial decision, and management decision
  are computed from the generated `Instances.v` and agree with `Policy.v`'s
  derived authorization, so A8 and A6 apply to them (P5, P6).
- **`ConcreteClaims.v`** and **`ConcreteAssumptions.v`**: the property
  list's theorems (P1 to P9 below, as the frozen specification states
  them) and one `Print Assumptions` per theorem, each required "Closed
  under the global context"; no axiom, parameter, or admitted term (stop
  (e)).

The **property-lineage table** (inherited, re-proved, strengthened,
inapplicable) is written for each of Model 0.2's 24 theorems and M3's 22
against stage 1's, in the evidence record and as an index comment at the
head of `ConcreteClaims.v`; `Model.v` stays as accepted (its closed
inductives describe the fixed single-hart profile; Q35), so a simulation
to it is not attempted and the table says so per property. The gate is
extended **additively** (stop (e)'s enumeration): `model/tests/run-concrete.sh`
beside `run-input-ring.sh`, with the escape-pattern grep, the compile and
`rocq check`, the theorem-to-report equality, and the layout drift check;
one line in `model/Makefile`'s `proof` runs it; `generate-evidence.sh` is
not edited (its `find` already hashes the new files). The stage-1 result
is a proof about the concrete model under the stated memory semantics
(D-3): a model of the implementation's protocol, not the implementation.

### D-2 The target commit, the readings, and the drift check (Q46)

Stage 1's **target commit** is this plan's acceptance-record commit, the
base of `beryllium/mvp-m8` (Q46's default): every source reading the
modules record is made there, cites **symbols** (`mvp-runtime.c`'s
`publish_blocks`, `post_inbound`, `drain`; `mvp-hartmain.c`'s
`be_mvp_hart_main`, `publish`; `mvp-sbi.c`'s `be_mvp_denial_decide`,
`be_mvp_mgmt_decide`, `serve`; `mvp-ring.c`'s API) and never lines, and
is checked by `model/tests/check-concrete-readings.sh`: every cited
symbol exists in the named file at the checkout, `mvp-layout.h`'s SHA-256
equals the one `ConcreteLayout.v` records, and the generated file is byte
equal. `Binding.v` is not edited (item 101's stale lines stay as M3's
reading; the evidence record lists each with its symbol at the target
commit, and C-06's note is re-read in the ledger). Under the **re-proof
rule** (S3-C.4) M10's gates run stage 1 and every pilot arm again at
RC4's exact tree before any pin is re-derived; a merge that changes a
proved translation unit, its headers, its flags, or a pin without the
re-run first is stop (i).

### D-3 Memory semantics: stated, with the premises as litmus tests

Stage 1's traces are **interleavings of the three harts' steps at word
granularity**, each read seeing the latest write in the trace: a
sequentially consistent model, labelled as such in every theorem's
statement and in the ledger row, and **not promoted** (S3-C.4). The
orderings the protocol needs beyond that, which the hardware's RVWMO
does not give for free, are stated as **ordering premises** on the
compiled code, never as axioms, and each is discharged by a **litmus
test** on the compiled instruction sequence (D-9, M8-4):

| Premise | Where the protocol needs it | Litmus pattern |
| --- | --- | --- |
| L1 | the barrier: a domain hart that reads the published generation word reads every block word hart 0 wrote before its `fence w, w` | message passing with `fence w, w` / `fence r, r` |
| L2 | ring publish: a reader that acquires the head and fences reads the records' bytes the writer posted before its `fence w, w` | message passing (the same fences) |
| L3 | ring release: a writer that reads the tail reads no record byte before the reader has read it, because the reader's `fence r, w` precedes its tail store | load buffering with `fence r, w` |
| L4 | buffer reuse: a writer that finds room by reading the tail stores into the freed slot only after that read, by the control dependency on the room check | load-to-store control dependency |
| L5 | the input ring's drop: a writer that asks `room` and posts within it never overwrites | as L3 and L4 |

The theorems of `ConcreteRings.v` and the barrier theorem take L1 to L5
as hypotheses where the SC model would otherwise make them vacuous
(stated as "the trace respects L_i"), so that the dependency is visible;
the litmus results are recorded beside them. A `Sometimes` on a premise
under RVWMO is stop 2's defect protocol. Nothing is claimed about caches,
IPIs' delivery timing, or the firmware's HSM.

### D-4 Stage 2: the pilot's leaves and arms (Q34, Q36)

- **Leaf A, `be_mvp_denial_decide` with its static helpers** (113 lines;
  the fact above): the arms **Frama-C/WP** (primary) and **CN** (second),
  each proving the same frozen contract (D-6) under the same decision
  rule (D-7).
- **Leaf B, `mvp-ring.c`**: **CBMC** bounded per-call properties for the
  public API (D-8), as the complement; a **WP contract arm** on the ring
  only if Leaf A's two arms end within their time boxes with budget left
  (Q16), with a claim per call that holds for any value of the peer's
  index and names its ownership premise, nothing for U-04 or U-11.
- **Bounded model checking** also serves every arm for specification
  debugging, mutation, and vacuity checks; it is never called proof and
  gets its own ledger method term only on a positive result (S3-C.7).
- **Excluded**: VST for the project's own C (`clightgen` needs CompCert
  files outside the open licence; item 103's correction is M8-2's);
  RefinedC (no release pinned to the project's Rocq; not packaged); Alt-Ergo
  other than Fedora's `2.4.3` under `CECILL-C` (a free licence; the
  current upstream releases are non-commercial, S3-C.4).

### D-5 Where the annotations live (Q37)

Beside the source, by default: WP's ACSL in `mvp/verify/wp/<leaf>.acsl`
imported by Frama-C's ACSL importer plug-in as Fedora's `frama-c 33.0`
ships it; if the plug-in is absent from that build or cannot place an
annotation the leaf needs (the loop invariant of `leaf_at`), WP's arm uses
an **annotated copy** under the same gate as CN's. CN's annotations, which
sit inside function bodies, live in an annotated copy
`mvp/verify/cn/mvp-sbi-leaf.c`, gated in the verifier by a check that the
copy's comment-stripped token stream equals the source's extract
(`mvp/verify/tools/token-equal.py`, with a self-test that a changed token
is refused) and by recorded digests of the source, every header of its
translation unit (the five in-tree headers and the six port headers),
the preprocessor flags, and the tool pins. No monitor source changes, not
even a comment, in M8 (stop (e)).

### D-6 Specifications: drafted from the plans and the claim, frozen by hash (D22)

`planning/mvp-m8-specifications.md` states, in prose with a formal
reading for each: the **stage-1 property list** P1 to P9; the **contract
of Leaf A** (precondition: valid, non-aliased inputs, `accept_denial`
as the image's; result 1 exactly for the M1 plan's denial entry, a
guest-page fault from VU mode with the recorded causes, `hstatus` bits,
`htval` and `htinst` bounds, `vstvec` mode, and a GPA outside the window
and every mapped page or a store to a read-only page; on 1, `out`
carrying the cause, kind, GPA, the injected `vscause`, `vstval`, `vsepc`,
`vsstatus`, and the resume PC the M1 plan fixes; on 0, `out` zero; the
frame `assigns *out`; no runtime error for any input values), the
contracts of its four helpers; and the **ring's per-call properties** for
CBMC (memory safety within the buffer under the mask; the index
invariants; each function's result as `mvp-ring.h`'s contract states it,
for any peer index value; the ownership premise named). It is drafted
from the M0, M1, M2 plans, security model v1, and the claim, **not from
the C** (the drafter does not open `mvp-sbi.c` or `mvp-ring.c`; the
fact sheet's type readings are the one exception, recorded), committed as
**its own exact commit**, its SHA-256 recorded in the plan's status block
and in every proof module's and arm's header, and presented to the human
as **reviewer of record**; proof drafting may start against the frozen
hash (Q12), and a change from the review re-freezes the hash and re-runs
every proof that cites it. A property that cannot be stated from the
plans and the claim without reading the C is stop 4.

- P1 Barrier publication: a domain hart that observes the published
  generation word observes every published word of its block (under L1).
- P2 Single writer per word per phase: I15 and I16 over every concrete
  step (obligation 1; H3 carried over).
- P3 Ring safety: no overrun, no take of an unpublished byte, indices
  monotone and within a capacity of each other, a full control ring fails
  closed and a full input ring drops and counts (under L2 to L5).
- P4 Ring integrity: every record taken equals a record posted, in FIFO
  order, with the writer's type set.
- P5 Denial: an accepted guest-page fault is denied exactly when the GPA
  lies outside the domain's window and every mapped page, or a store hits
  a read-only page; the rights are the sealed instance's (obligation 2;
  A8, A6); every denial is recorded and injected; no fault outside the
  entry is accepted.
- P6 Management: only hart 0 decides, against the sealed grants (A6, A8);
  a delivered `pause` or `terminate` parks the target, which never
  resumes; at most one request is pending per domain; every request is
  answered or refused.
- P7 Measure before entry: no domain is entered before its measurement
  step has run and compared (the abstract gate; M9's content unproved).
- P8 Drain: hart 0 takes outbound records round-robin, one per domain per
  pass, each ring's records in order.
- P9 Input routing: I17 as `InputRing.v` proves it (inherited; the
  lineage table's row).

### D-7 The decision rule, registered here (before any arm starts)

Every arm states the frozen contract (D-6) and is judged by the same
rule:

1. **Tools**: open tools at pinned versions, Fedora RPMs by NEVRA and
   SHA-256 in the verifier's closure, source-built tools by release
   tarball or commit and SHA-256 in a verified source cache; nothing from
   `~/.local`, `opam`, or the network at build or run time.
2. **Qualification** (H41 stage 3) before the leaf: a known-pass case, a
   known-fail case, a vacuity case (a contradictory precondition must be
   detected, `ensures \false` must not prove), and a wrong-implementation
   case (a planted defect must fail), per arm, per solver, recorded.
3. **The leaf unchanged**: the translation unit's, headers', flags', and
   pins' digests equal the target commit's record.
4. **An assumption inventory** per arm: the tool's memory model and
   integer model (the LP64 machdep against the RISC-V target's
   `_Static_assert`s), axiomatics, solver trust, the ownership premise,
   and what the result does not cover.
5. **All goals closed**: `unknown`, a timeout, or an unproved goal is a
   non-result; the time box is the same for each arm (Q6): at most four
   annotation rounds after the freeze, a per-goal solver limit of 60 s,
   and a recorded wall-clock in the verifier, each round's goal counts
   logged.
6. **Mutants and vacuity**: a seeded single-defect mutant set chosen in
   advance (Q7: seed `0x4d38`, at least 24 mutants per leaf from the
   generator's operator, constant, and dropped-check rules), each killed
   (at least one goal fails) or shown unobservable by the leaf's host
   test (the equivalence oracle; recorded, never counted as killed); the
   vacuity checks of item 2 on the final annotations.
7. **Solvers**: Z3 and cvc5 as the independent pair for every SMT-backed
   goal; Alt-Ergo `2.4.3` beside them for WP; a goal counts as closed only
   if at least one solver closes it and no solver reports it false.

A **positive result** is an arm meeting items 1 to 7 on Leaf A. The
**outcome** names a recommended vehicle per **claim class**: (a) pure
decision functions over captured inputs (the denial decision, the
management decision, the G-stage derivation, the measurement gate);
(b) ring-class code with shared volatile indices (per-call contracts;
the protocol stage 1's); (c) the cross-hart protocol (stage 1 with its
litmus premises; no C tool); (d) compiled execution (assumed: the locked
compilers and the executor; no binary correspondence). "Inconclusive"
(no arm met the rule in its time box, with the reasons) and "no vehicle
fits" (every qualified arm failed on a structural ground) are valid
outcomes. The recommendation is **non-load-bearing** until the recorded
promotion gates hold (the implementation plan's for CN; an explicit
direction from the human for WP); the tool roles in the open-tooling and
implementation plans stand and change only by direction.

### D-8 Bounded model checking on the ring (Q11)

CBMC `6.8.0` with harnesses under `mvp/verify/cbmc/`: one per public
function (`init`, `post`, `room`, `post_words`, `publish`, `acquire`,
`take`, `release`, `record_bytes`, `record_word`, `peak`, `taken`,
`published`, `reset`) and one sequence harness (post, publish, acquire,
take, release across a wrap), at capacities 512 and 4,096 with payloads
to 256, loops fully unwound with `--unwinding-assertions`, bounds checks,
pointer checks, signed and unsigned overflow checks, the peer's index a
nondeterministic value (so the claim holds for any value of it), and the
own index's starting value nondeterministic including near 2^64. Its
record states the bit widths, bounds, unwinding checks, and assumptions
(Q36); it is reported as a bounded model check and never as proof; the
mutant set of D-7 item 6 runs through it too. The same CBMC run gives
every arm its specification-debugging and vacuity checks on Leaf A.

### D-9 Litmus tests on the compiled sequences (M8-4)

For each premise L1 to L5, a RISC-V litmus test whose instructions mirror
the compiled sequence of the exact symbols at the target commit (the
disassembly of `be_mvp_ring_publish` and its caller's fence helper, the
reader's acquire-fence-take-fence-release, `publish_blocks`'s generation
store, and the domain hart's check in `be_mvp_hart_main`; the ELF's and
each symbol's bytes recorded by digest), with the forbidden outcome
stated, run under `herd7`'s RVWMO model (`riscv.cat`) in the verifier;
`herdtools7` from a pinned release tarball by SHA-256, built offline with
Fedora's OCaml packages (`ocaml`, `ocaml-dune`, `ocaml-menhir`,
`ocaml-zarith` where packaged; else their pinned sources). `isla-axiomatic`
is the alternative if `herdtools7` cannot be built offline (Q3); if
neither can, the premises stay theorem premises with the litmus column
`not run` and the reason, and the stage-1 row says so.

### D-10 The verifier image and the tool pins (Q9, Q10)

A **separate** evaluator image, `localhost/beryllium-mvp-verifier`, built
by `mvp/tools/verifier/` with the MVP evaluator's discipline reused
(`fetch-closure.py`, the closure format, the base image by digest,
repositories disabled, `--network=none` at run time): its closure is the
build tools' subset plus `frama-c`, `why3`, `alt-ergo`, `z3`, `cvc5`,
`cbmc`, `cbmc-utils`, `rocq-core`, `rocq-stdlib`, and the OCaml packages
the source builds need, each by NEVRA and SHA-256; the **source-built
tools** (`herdtools7`; CN with Cerberus and Lem) come from a verified
source cache (release tarball or commit archive, SHA-256 pinned in
`mvp/tools/verifier/sources.txt`) and are built inside the image with no
network. `./mvp/mvp verify` runs the qualification suites, the litmus
tests, and the arms inside it and writes `build/mvp/verify/` records; the
accepted MVP evaluator image, its 259-NEVRA closure, and `./mvp/mvp
evaluate` are unchanged. The **CN arm's toolchain** is the pilot's known
risk: Cerberus publishes no releases, its build needs Lem and a dozen
OCaml libraries, and `opam` is not used; M8-5 pins a Cerberus commit and
each dependency, builds offline, and records the result; if the offline
reproducible build does not succeed within its time box (Q10), the CN
arm is recorded **not qualified** (`not run`) and the pilot proceeds with
WP and CBMC: a recorded outcome, never a loosened gate.

### D-11 The ledger, the claim, and the words (S3-C.7)

- **Stage 1**: new ledger rows with the method `proof about the abstract
  model`, each row's text saying "the concrete operational model (stage
  1) under sequentially consistent interleaving, with ordering premises
  L1 to L5 discharged by litmus tests", and a boundary row for what stage
  1 does not model; U-11's note gains the litmus results; U-13's text is
  superseded as Q35 states (Model 0.3 is 2.0's) and says so; C-06's note
  is re-read at the target commit (item 101).
- **The pilot, only on a positive result**: the method vocabulary gains
  exactly `C-level contract proof` and `bounded model check`; a claim row
  per proved function naming the tool, version, commit, assumptions, and
  mutant results; and the required limit's sentence is narrowed to these
  **fixed words**, the slots filled only from the recorded outcome:

  > The monitor's implementation is unproved but for `<the proved
  > functions>` in `<file>` at commit `<sha>`, for which a C-level
  > contract proof with `<tool and version>` holds under the assumptions
  > the ledger's `<rows>` list, the contract's relation to the model an
  > assumption and not a refinement: the boot barrier, the rings, the IPI
  > protocol, the control loop, the G-stage builder, the rest of the
  > denial path, the management decision, and the measurement are covered
  > by host tests, image and capture checks, emulation, and the board
  > runs, and by nothing else; R7's bounded proof covers the accepted R5
  > single-hart bytes only.

  "Refinement" is written only if S3-C.4's relational target is
  established, which this plan does not expect; a contract proof with a
  Rocq-checked realization or a named and reviewed transcription to stage
  1 is recorded as a **contract proof**. On an inconclusive or negative
  outcome the claim is unchanged and the ledger gains the stage-1 rows and
  a review item recording the outcome. Any other claim change is stop (d);
  the forbidden-phrasing check must pass.

### D-12 Resolving H38 and H41, and the lessons not to transfer

S3-C.4's table is adopted as written; this plan maps each stage to its
deliverable:

| Helium stage (H41) | Disposition | M8 deliverable |
| --- | --- | --- |
| 1 select a candidate seam | Adapt | Leaf A carries the selection; Leaf B admissible only with the cross-hart protocol as stage 1's obligation (D-4) |
| 2 entry criteria | Adopt | the exact source boundary (the leaf, its translation unit, its headers by digest) and the target commit (D-2) |
| 3 qualify the tool for the question | Adopt for every arm | D-7 item 2's four cases per arm and solver (M8-5) |
| 4 independent specification ownership | Adapt | D-6: drafted from the plans and the claim, frozen by hash, the human reviewer of record |
| 5 a mutation plan before acceptance | Adopt | D-7 item 6: the seeded set chosen in advance, plus vacuity |
| 6 exact evidence | Adopt | digests of the translation unit, flags, and pins; the re-proof rule (D-2) |
| 7 a clean evaluator workflow | Already practice | the verifier image (D-10) |
| 8 clean-commit and human gates | Already practice | the exact-commit decision on the result |
| 9 exit criteria | Adopt | the three recorded outcomes, "a negative feasibility result is a valid outcome" |

H38 is resolved as adapted bounded checking per named claim (D-8), never
Helium's suite or its counts transferred; H42's five lessons are
constraints here (no generalized bounds; CBMC never conflated with
kernel-checked proof; no synthetic model without correspondence work, so
stage 1 rests on the two obligations and the readings at the target
commit; evidence automation inside the soft limits, H43; no system or
hardware claim). The resolution is recorded in this plan, in the result's
evidence record, and in the MVP plan's status addendum; the synthesis's
text is not edited.

### D-13 What M8 does not do

No board command; no monitor source change, not a comment; no claim-text
change but the pre-authorized sentence on a positive result; no
whole-system, availability, microarchitectural, or compiled-execution
claim; no edit to an accepted model file or gate beyond D-1's
enumeration; no generalization of `Model.v` (Q35); no tool selected "for
the proof-bearing subset"; no push, merge, tag, publication, snapshot
refresh, or kexec use; nothing of M9 or M10. Item 103's two planning
sentences are corrected in M8-2 because this plan's acceptance is the
direction item 103 waits for (Q13).

## Work packages

| WP | Delivers | Exit |
| --- | --- | --- |
| M8-1 | This plan; the review packet | the plan accepted |
| M8-2 | `planning/mvp-m8-specifications.md` (P1 to P9, Leaf A's contract and its helpers', the ring's per-call properties) as its own exact commit, its SHA-256 recorded; `model/tools/gen-concrete-layout.py` and `ConcreteLayout.v`; `model/tests/check-concrete-readings.sh`; the mutant generator `mvp/verify/tools/mutate.py` with its seed and the equivalence oracle; item 103's two sentences corrected (`planning/open-tooling.md`, `planning/research-synthesis.md`) | the specification commit presented to the human as reviewer of record; the generator, the drift check, and the mutant generator's self-tests pass |
| M8-3 | Stage 1: `Concrete.v`, `ConcreteRings.v`, `ConcreteBridge.v` (the two obligations), `ConcreteClaims.v`, `ConcreteAssumptions.v`; `model/tests/run-concrete.sh` and the `model/Makefile` line; the lineage table | `make -C model proof` and `./be evaluate` PASS with every new theorem closed; the drift check PASS; the lineage table complete |
| M8-4 | The ordering premises as litmus tests (L1 to L5) on the compiled sequences at the target commit, under `herd7` (or `isla`) in the verifier; the premises table | every premise has a litmus test with a recorded outcome, or `not run` with its reason; no `Sometimes` |
| M8-5 | `mvp/tools/verifier/` (Containerfile, closure, `sources.txt`, the offline builds), `./mvp/mvp verify`; the qualification suites per arm and solver (known-pass, known-fail, vacuity, wrong-implementation); the token-stream gate; the digests record | the image builds offline from the verified caches; every arm qualified or recorded not qualified, with the reason |
| M8-6 | The pilot under D-7: WP on Leaf A (importer or gated copy), CN on Leaf A, CBMC on Leaf B and the debugging and vacuity checks for both, the WP ring contract arm if budget; the mutant runs; the Rocq export's qualification against `rocq-9.3` (Q17); each arm's record (goals, rounds, time, solvers, mutants, assumptions) | each arm's result recorded within its time box; the records in `build/mvp/verify/` and the retained excerpts under `mvp/results/<date>-verify/` |
| M8-7 | The outcome (the recommendation per claim class, or inconclusive, or no vehicle fits, with reasons); the ledger rows (stage 1; the pilot's on a positive result) and, on a positive result, the vocabulary terms and the fixed claim sentence; the H38 and H41 record; `planning/mvp-m8-evidence.md`; `mvp/README.md`; the result packet | the gates pass from a clean checkout (`./mvp/mvp check`, `evaluate`, `verify`, `claim-ledger check`; `./be model-check`, `./be evaluate`); the packet presented |

Order: M8-2 first (the freeze); M8-3 and M8-5 in parallel from the freeze
(the model needs no tool but Rocq; the image needs no model); M8-4 after
M8-5's image; M8-6 after M8-5's qualification; M8-7 last. Coding and
proof drafts run on `claude-opus-5.5` sub-agents in worktrees at the
pinned effort and context tier; the session model plans, reviews each
merge line by line, runs the gates, and writes the specification, the
records, and the packet (D22; the standing split). The specification is
presented to the human as soon as it is written.

## Soft limits (re-evaluation stops; Q41)

**Counting rule:** added lines by `git diff --numstat` from the M8 base
(this plan's acceptance record), per lane, generated files excluded and
reported: the **model lane** (`model/proof/*.v` new modules; `model/tests/*.sh`
and `model/tools/*` added; the one `Makefile` line), counting also
theorems and closed-assumption reports; the **bridge and contracts lane**
(`mvp/verify/**` but Markdown: ACSL, CN annotations, CBMC harnesses,
litmus tests, qualification fixtures, the mutant and token tools); the
**tool-glue lane** (`mvp/tools/verifier/**` but the closure's data lines,
`mvp/tools.mk`, `mvp/mvp`, `mvp/Makefile`), counting also the pinned
tools. Markdown and JSON are reported separately.

| Lane | Guide (re-derived) | Limit |
| --- | --- | --- |
| Model | M3's four modules were 3,044 lines for 22 theorems and `InputRing.v` 386 for 4; stage 1 adds a state of three harts, three rings with word indices, the barrier, the exit and management paths, two obligations, and the claims: 3,000 to 5,000 lines, 20 to 35 theorems | 6,000 lines (M3's per-lane precedent); every theorem with a closed report |
| Bridge and contracts | ACSL 150 to 300; CN 150 to 300; CBMC harnesses 400 to 700; litmus 100 to 200; qualification fixtures 300 to 500; the mutant and token tools 300 to 500: 1,400 to 2,500 | 3,000 lines |
| Tool glue | the verifier's Containerfile, closure tooling, source builds 400 to 800; `verify` and its records 300 to 500; gates and Make 200 to 400: 900 to 1,700 | 2,500 lines; at most 10 pinned tools |
| Proof time | M3's `make -C model proof` was 46 s on `l1` | 600 s |

A limit exceeded is a stop for re-evaluation of the limit, never a cut to
the work (the human's direction of 2026-10-28). The checker-to-monitor
size is reported against M7's 2.083 and not limited.

## Stop conditions (each returns to the human)

1. Any need to change monitor source beyond a comment, or any accepted
   model file or gate other than D-1's enumerated additions; a global
   axiom, parameter, or admitted term in any module; a theorem whose
   premise the deployed configuration violates; a footprint the sources
   contradict (S3-C's stop (e)).
2. **A defect found by a proof, a bounded check, or a litmus test**: the
   protocol is to record the counterexample and a failing host test in a
   scratch copy, freeze the specification, and stop; the human routes the
   fix before M10 and decides on a snapshot note.
3. The two first obligations fail: a concrete step's writes outside
   `Binding.v`'s footprint, or a decision the generated instance does not
   reproduce (a finding about the accepted model or the sources).
4. A property or contract that cannot be stated from the plans and the
   claim without reading the C (D22), or a specification change from the
   human's review that the proofs cannot absorb.
5. A tool that cannot be pinned (no free-licence release; no offline
   reproducible build within its time box, Q10) when it is the last
   qualified C arm; a solver pair that cannot be formed.
6. A soft limit exceeded (re-evaluation, never a cut).
7. The target commit moving under stage 1 (a merge into the M8 branch
   that changes a modelled file, a proved translation unit, its headers,
   flags, or pins) without the re-proof rule run first (stop (i)).
8. Any claim-text change other than D-11's fixed sentence on a positive
   result, or a ledger term other than the two (stop (d)).
9. Any need to model the firmware, harts 3 to 7, the hardware, or M9's
   measurement content to prove a listed property.
10. The model's rootless evaluator or the verifier image unable to
    install or build a pinned tool.
11. Any push, merge, tag, publication, snapshot refresh, release step,
    board command, or kexec use.
12. Any other finding that changes the plan's claim boundary.

## Open questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | The plan branch's base | `1b3f2e10`, the M7 acceptance record, a linear descendant of the development tip `f5dc770b`, so that stage 1's target includes M7's input ring and the headers the leaves include (S3-C.7's merge-order rule); the development branch's fast-forward to it is the human's `ff + push` | `f5dc770b` itself (stage 1 would model the pre-M7 layout and be stale on M7's merge) |
| Q2 | Stage 1's target commit (Q46) | this plan's acceptance-record commit, every reading made there with the drift check; the re-proof rule at RC4 | RC4's tree (stage 1 waiting for M9) |
| Q3 | The litmus tool | `herdtools7` from a pinned release tarball built offline with Fedora's OCaml packages; `isla-axiomatic` if it cannot be built; `not run` with the reason if neither | isla first |
| Q4 | The module set | `Concrete.v`, `ConcreteLayout.v` (generated), `ConcreteRings.v`, `ConcreteBridge.v`, `ConcreteClaims.v`, `ConcreteAssumptions.v`, run by `run-concrete.sh` | fewer, larger modules |
| Q5 | The ring indices in the model | 64-bit words (`N` modulo 2^64) so the wraparound is modelled; capacity a parameter | naturals (wraparound unmodelled, a stated gap) |
| Q6 | The time box per arm | four annotation rounds after the freeze; 60 s per goal; the wall-clock recorded; equal for every arm | fewer rounds; a shorter limit |
| Q7 | The mutant set | seed `0x4d38`; at least 24 single-defect mutants per leaf from operator, constant, and dropped-check rules; the leaf's host test as the equivalence oracle | more mutants |
| Q8 | WP's annotation placement | the ACSL importer; an annotated copy under the token-stream gate if the importer is absent or insufficient | the annotated copy from the start |
| Q9 | The verifier image | separate (`beryllium-mvp-verifier`), its own closure, the MVP evaluator unchanged | the one closure extended (every MVP evaluator digest moves) |
| Q10 | CN's offline build | a pinned Cerberus commit with Lem and each OCaml dependency pinned by SHA-256, built offline; its own time box of one M8-5 session; else CN `not qualified` and the pilot proceeds with WP and CBMC | skip CN from the start (rejected: S3-C.4 names two arms) |
| Q11 | CBMC's scope | the fourteen public ring functions and one sequence harness; capacities 512 and 4,096; full unwinding; the peer index nondeterministic | one capacity |
| Q12 | The specification's review flow | the commit presented at once; proof drafting starts against the frozen hash; a review change re-freezes and re-runs | drafting waits for the human's acceptance |
| Q13 | Item 103's two sentences | corrected in M8-2, this plan's acceptance being the direction | left for a separate instruction |
| Q14 | Machine models | Frama-C's LP64 machdep and CBMC's 64-bit LP64 model, checked against the sources' `_Static_assert`s (`sizeof(struct be_mvp_exit) == 360`) and recorded as assumptions | a RISC-V machdep if the tools ship one that passes the same checks |
| Q15 | The lineage table's home | the evidence record, with an index comment in `ConcreteClaims.v` | a separate planning document |
| Q16 | The WP contract arm on the ring | attempted only after Leaf A's two arms end within their time boxes with budget left; else `not run` | always attempted |
| Q17 | WP's Rocq export | qualified in M8-6 against `rocq-9.3` through Why3's driver; if it cannot target 9.3, the link to stage 1 is a named and reviewed transcription (a contract proof, the relation an assumption) | a Rocq-checked realization only |

A steering review of this plan by another model: none (the SOP; S3-C's
Q42); the human may direct one, as for S3-C.

## What acceptance authorizes

M8-2 to M8-7 on branch `beryllium/mvp-m8` from the acceptance-record
commit (stage 1's target commit), with Q1 to Q17 at their defaults unless
answered, under the stop conditions above; the specification document as
its own exact commit for the human's review of record; item 103's two
sentence corrections; the verifier image and `./mvp/mvp verify`; the
ledger's stage-1 rows, and, only on a positive pilot result, the two
method terms and the fixed claim sentence. Nothing else: no board
command, monitor change, accepted-byte or accepted-model change, push,
merge, tag, publication, snapshot refresh, or kexec use; nothing of M9 or
M10.
