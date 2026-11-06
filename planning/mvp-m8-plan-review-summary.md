<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M8 plan review summary

This packet presents one decision: the [M8 plan](mvp-m8-plan.md), the
first verification plan, at exact commit
`7a0c74ae329c09282c5cf159076f5e99934ac4c2` (parent `1b3f2e10`, the M7
result's acceptance record, a linear descendant of the development
branch's tip `f5dc770b`) on local branch `beryllium/mvp-m8-plan`. The
plan bounds the milestone S3-C.4 defines, under S3-C's Q34 to Q38, Q41,
Q42, and Q46 at their defaults, D22, and stops (d), (e), and (i). It
recorded the decision below after it was given.

## Decision record

The responsible human accepted exact commit
`7a0c74ae329c09282c5cf159076f5e99934ac4c2` (parent `1b3f2e10`) as the
M8 plan on 2026-11-02 (13:09 in the human's time zone) by the
instruction `accept 7a0c74ae wuth CN, go for m9`, the reply to this
packet's request; the abbreviation was checked to resolve uniquely
(`git rev-parse --disambiguate=7a0c74ae`). `wuth CN` is read as `with
CN`, the answer to Q10: the CN arm is attempted (the default's substance
confirmed; the recorded `not qualified` fallback stands if its offline
build does not succeed within its time box). Q1 to Q9 and Q11 to Q17
apply at their defaults. `go for m9` directs the M9 plan.

- **Scope:** acceptance covers exactly the plan text at that commit and
  this packet's claim boundary (section 3). Sections 1 to 9 are the
  packet as presented, apart from the status rows of section 1 and the
  closing lines of section 9, which now show the outcome.
- **What it authorizes:** M8-2 to M8-7 on branch `beryllium/mvp-m8` from
  the acceptance-record commit (stage 1's target), under the plan's
  twelve stop conditions and its soft limits per lane; the specification
  document as its own exact commit for the human's review of record
  when written; item 103's two sentence corrections; the verifier image.
  Nothing else: no board, monitor change, accepted-byte or
  accepted-model change, push, merge, tag, publication, snapshot
  refresh, or kexec use; no claim change but D-11's fixed sentence on a
  positive result; nothing of M10.
- **Not directed:** a fast-forward or push. The development branch
  `beryllium/single-hart-runtime-r0` stays at `6105c34d` (the M7 push
  record), which this branch took by merge before the acceptance record;
  `beryllium/mvp-m8-plan` is local.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `7a0c74ae329c09282c5cf159076f5e99934ac4c2` (parent `1b3f2e10`) on local branch `beryllium/mvp-m8-plan`; it adds `planning/mvp-m8-plan.md` and nothing else. The commit after it adds this packet and the registrations (the sidebar, the planning README, the roadmap, the handoff, the repository instructions, the development log). |
| Current status | Documentation only; **responsible-human accepted as of 2026-11-02** (the decision record above; Q10 answered `with CN`, the rest at their defaults); local, unpushed. No code, model text, claim text, or tool changes. |
| Decision requested | None outstanding; the decision was `accept 7a0c74ae wuth CN, go for m9`. |
| Successor status | M8-2 to M8-7 are authorized on `beryllium/mvp-m8` from the acceptance-record commit and start on the same day; the M9 plan is directed by the same instruction (`go for m9`) and is written on its own branch; M10's plan waits for M7's, M8's, and M9's results. |
| Publication status | Private repository (the internal one). As presented: the development branch was at `f5dc770b` and `beryllium/mvp-m7` unpushed; on `ff + push M7` (2026-11-02, before the decision) the development branch moved to `6105c34d` and `beryllium/mvp-m7` and `beryllium/mvp-m7-plan` were pushed; this branch is unpushed. The public review snapshot is at `36e2590c`. No tag, publication, release step, or snapshot refresh. |

The action this section asked of the human, the decision on
`7a0c74ae`, is taken; what follows it is in the decision record above
and in section 9.

### What the plan is, in one paragraph

A bounded first result about the monitor's own C, and a decided vehicle
for proving more, in two stages under one registered decision rule.
Stage 1 is a concrete operational model of harts 0 to 2 in Rocq beside
M3's accepted modules, importing `Binding.v` and `Policy.v` unedited: the
hart blocks with their generation words, the three single-writer rings
per domain hart with 64-bit indices, the boot barrier, the denial path,
`pause` and `terminate`, and the measure-before-entry gate; two first
obligations (every concrete step's writes within `Binding.v`'s footprint,
so H3 carries over; the roots, rights, and decisions computed from the
generated instance, so A8 and A6 apply); a property-lineage table against
Model 0.2's and M3's theorems; the layout constants generated from
`mvp-layout.h` with a drift check, every reading at the target commit by
symbol (item 101); and the memory semantics stated as sequentially
consistent interleaving, labelled and not promoted, with the five
orderings the protocol needs stated as theorem premises and discharged by
litmus tests on the compiled sequences under RVWMO. Stage 2 is a pilot:
Frama-C/WP and CN on `be_mvp_denial_decide` with its four static helpers
(113 pure lines), CBMC bounded model checking on `mvp-ring.c`, every arm
qualified with known-pass, known-fail, vacuity, and wrong-implementation
cases, time-boxed equally, run against a seeded mutant set chosen in
advance, with Z3 and cvc5 as the solver pair, in a separate verifier
image built with the evaluator's closure discipline from Fedora 44's
packaged tools and pinned sources for the rest. The specifications are
drafted from the plans and the claim, not from the C, frozen by hash,
and presented to the human as reviewer of record. The outcome is one of
three recorded results, each accepted by the human; the claim changes
only on a positive result, by the one sentence S3-C.7 pre-authorizes,
fixed in words in the plan. RC4 waits on M8 accepted, not successful.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Review question |
| --- | --- | --- | --- | --- |
| The M8 plan | `planning/mvp-m8-plan.md` | the milestone's design (D-1 to D-13), the stage-1 property list, the decision rule, the fixed claim sentence, the H38 and H41 resolution, seven work packages, soft limits per lane, twelve stops, Q1 to Q17 | planning text only; authorizes nothing until accepted | Does every design choice trace to S3-C.4 or to one of the plan's own open questions with a default? |
| This packet | `planning/mvp-m8-plan-review-summary.md` | the decision support | decision support only | — |
| Registrations | `planning/README.md`, `planning/roadmap.md`, `planning/HANDOFF.md`, `planning/.vitepress/config.mts`, `.github/copilot-instructions.md`, `mvp/README.md` | the plan's place in the maintained navigation and status | status text | — |

## 3. Claim boundary

**What the commit supports saying:** a bounded plan exists for M8 whose
every design choice traces to S3-C.4's shape or to one of its own open
questions with a default; its facts were read in the tree at `1b3f2e10`
with line numbers, by two read-only fact sheets re-checked where cited.
Four facts the design turns on hold at that commit: the first leaf is
113 lines, pure over `const` inputs, with one bounded loop and no
volatile, asm, union, bit-field, or pointer cast; the ring's shared words
are two volatile index lines and a buffer, its indices free-running
64-bit counts, its fences the callers'; `Binding.v`'s numeric constants
agree with `mvp-layout.h` while its source-line citations are M3's;
Fedora 44 packages Frama-C 33.0, Why3 1.8.2, Alt-Ergo 2.4.3 under
`CECILL-C`, Z3 4.16.0, cvc5 1.3.4, and CBMC 6.8.0, and packages neither
CN, Cerberus, `herdtools7`, `isla`, CompCert, VST, nor RefinedC.

**What it does not do:** no code, no model text, no claim change (the
sentence is fixed here and takes effect only through the result's
acceptance and only on a positive pilot result), no board command, no
push. The plan does not promise that any arm will close its goals: an
inconclusive or negative result is a valid outcome (S3-C.4), and the
CN arm's offline build is named as the pilot's known risk with its
recorded fallback (D-10, Q10). It does not promise refinement: a contract
proof with a realization or a reviewed transcription to stage 1 is
recorded as a contract proof, the relation an assumption (D-11).

**What stays trusted or assumed in the design:** the tools' own
soundness and their memory and integer models (recorded per arm in the
assumption inventory; the LP64 machdep against the target checked
through the sources' `_Static_assert`s, Q14); the solvers (two
independent ones per goal); the locked compilers and the executor
(compiled execution is class (d), assumed); RVWMO as `herd7`'s `riscv.cat`
states it, for the litmus discharge of the premises; the firmware's HSM
and IPI semantics, the harts never started, and M9's measurement content,
which stage 1 does not model.

## 4. Load-bearing decisions

| Decision | Content | Why this way |
| --- | --- | --- |
| D-1 | stage 1 as six new modules importing `Binding.v` and `Policy.v` unedited; the two first obligations; the lineage table; an additive gate runner | S3-C.4's shape and Q35's default; stop (e) enumerates the additions; `Model.v`'s closed inductives make an MVP instance non-additive |
| D-2 | the target commit is the acceptance record; readings by symbol; the layout generated with a drift check | Q46's default; item 101's lesson (hand-copied lines went stale) |
| D-3 | sequentially consistent interleaving, labelled and not promoted; premises L1 to L5 as hypotheses, discharged by litmus tests | S3-C.4's memory-semantics clause; the honest shape of what a Rocq interleaving model shows and what RVWMO adds |
| D-4 | Leaf A `be_mvp_denial_decide` for the two C arms; Leaf B `mvp-ring.c` for CBMC, a WP contract arm only if budget | Q34's and Q36's defaults; the leaf is pure, small, behind U-08 and C-15 |
| D-5 | annotations beside the source: WP through the importer with a gated-copy fallback; CN in a gated copy | Q37's default; no monitor byte changes (stop (e)) |
| D-6 | specifications from the plans and the claim, frozen by hash, the human reviewer of record; drafting starts at the freeze | D22; H41 stage 4 adapted; Q12 keeps the review off the critical path with a re-freeze rule |
| D-7 | the decision rule registered in the plan: pins, qualification, the leaf by digest, an assumption inventory, all goals closed, an equal time box, mutants and vacuity, the solver pair | S3-C.4's "registered before any arm starts"; H41 stages 3, 5, 6 |
| D-8 | CBMC on the fourteen public ring functions at two capacities with a nondeterministic peer index; never called proof | Q36's default and H42's lesson |
| D-9 | litmus tests whose instructions mirror the compiled symbols at the target commit, under `herd7` built from a pinned tarball; `isla` or `not run` as fallbacks | S3-C.4 names both tools; neither is packaged, so the build is pinned by source |
| D-10 | a separate verifier image with its own closure; CN and Cerberus from pinned sources with an offline time box and a `not qualified` fallback | the accepted evaluator's digest stays; M0-B's discipline; S3-C.4's "more than the pattern of the closure" |
| D-11 | stage-1 ledger rows under the existing method term; on a positive result only, the two new terms and the fixed sentence | S3-C.7's pre-authorization, no wider |
| D-12 | the H41 table adopted stage by stage with each stage's deliverable named; H38 as adapted bounded checking per named claim | S3-C.4's table; H42's constraints |

## 5. Review history and resolved findings

The plan was written on the session model from the accepted S3-C text
and two read-only fact sheets of the tree at `1b3f2e10` (explore agents
on `claude-opus-5.5`, 2026-11-02; their facts re-checked where cited).
Four things the writing settled:

1. **The plan's base.** S3-C says each milestone plan is written "on its
   own branch from the development branch"; the development branch is
   at `f5dc770b` because no `ff + push` has been directed since M7's
   acceptance, while S3-C.7 says M7 changes the ring layout and record
   grammar M8 models and the headers its leaves include. The plan is
   therefore based on the M7 acceptance record `1b3f2e10`, a linear
   descendant of `f5dc770b`, and says so (Q1); `ff + push` makes the
   letter and the base agree.
2. **The toolchain the pilot can pin.** Fedora 44 packages every
   C-arm tool but CN (Frama-C 33.0 requires `why3` and `alt-ergo`;
   Alt-Ergo 2.4.3 is under `CECILL-C`, so S3-C.4's free-licence rule is
   met by the packaged release); CN, Cerberus, Lem, `herdtools7`, and
   `isla` need pinned-source builds without `opam`, which the plan
   time-boxes with recorded fallbacks rather than assuming.
3. **The leaf is as S3-C described it, and smaller than the layer table
   suggests**: 113 lines with its helpers, no volatile, one bounded loop;
   the translation unit's header closure (2,880 in-tree lines plus the
   port's six accepted headers) is what the proof's digests must bind.
4. **`Binding.v`'s numbers hold and its lines do not** (item 101): the
   plan generates the layout and cites symbols, and keeps `Binding.v`
   unedited.

Open for your judgement, beyond the defaults: the base (Q1); the time
box (Q6) and the mutant floor (Q7); whether CN should be attempted at
all in M8 given its build cost (Q10's default attempts it once); whether
item 103's two sentences are corrected under this plan (Q13); and whether
to ask for a steering review of this plan (the SOP says none; S3-C's
Q42).

## 6. Validation and retained evidence

Documentation checks only: `node scripts/check-doc-sources.mjs` PASS at
the plan commit (`7a0c74ae`) and at the packet commit, `git diff --check`
clean, `git status` clean; `git diff --stat 1b3f2e10 7a0c74ae` lists one
file, `planning/mvp-m8-plan.md`. Nothing was built or run; no tool was
installed. The fact sheets are session artifacts, not repository content.

## 7. Recommended human review sequence

```sh
git worktree add --detach /tmp/be-m8-plan 7a0c74ae329c09282c5cf159076f5e99934ac4c2
cd /tmp/be-m8-plan
git --no-pager diff --stat 1b3f2e10..HEAD
```

1. `planning/mvp-m8-plan.md`: "Purpose", then D-7 (the decision rule)
   and D-11 (the fixed claim sentence and the ledger's terms), then D-6
   (the property list and the specifications' ownership), then D-3 (the
   memory semantics and the premises), then the stops and Q1 to Q17.
2. `planning/mvp-plan.md` S3-C.4 (L1487-L1654) beside it, to confirm the
   plan stays inside the shape; S3-C.7's M8 pre-authorization
   (L1889-L1905).
3. The facts section, if you want to check a citation.

## 8. Human decision checklist

- [ ] The plan stays within S3-C.4 and its defaults: no board, no
      monitor change, no claim change but the pre-authorized sentence on
      a positive result, no tool selected "for the proof-bearing subset".
- [ ] The decision rule (D-7) is the one you want the arms judged by,
      and the three outcomes are acceptable as recorded results.
- [ ] The specifications' ownership (drafted from the plans and the
      claim, frozen by hash, you as reviewer of record) and Q12's flow
      are acceptable.
- [ ] The fixed claim sentence (D-11) is the one you would want published
      on a positive result.
- [ ] The soft limits per lane and the stops are acceptable.
- [ ] Q1 to Q17 at their defaults, or answered.
- [ ] Successor work stays excluded (M9's plan is separate; M10's waits).
- [ ] Exact commit `7a0c74ae329c09282c5cf159076f5e99934ac4c2` is accepted
      (authorizing M8-2 to M8-7), revisions are requested, or the review
      is deferred.

## 9. After the decision

- **Accept:** an acceptance record names `7a0c74ae329c09282c5cf159076f5e99934ac4c2`
  and the date; M8-2 to M8-7 run on `beryllium/mvp-m8` from the
  acceptance-record commit, which is stage 1's target commit, under the
  plan's stops; the specification document is presented as its own exact
  commit when written; the fast-forward and push of the development
  branch stay on your instruction.
- **Request revisions:** a second candidate on the same branch; this
  packet updated; the first marked superseded.
- **Defer:** the branch stays as it is; nothing starts.

**Status:** the M8 plan is **responsible-human accepted as of
2026-11-02** at exact commit `7a0c74ae` (`accept 7a0c74ae wuth CN, go
for m9`; Q10 answered `with CN`, Q1 to Q9 and Q11 to Q17 at their
defaults); M8-2 to M8-7 are authorized on `beryllium/mvp-m8` from the
acceptance-record commit; the development branch is not moved and this
branch is not pushed.
**Next:** M8-2 (the specification document as its own exact commit for
your review of record; the layout generator and drift check; the mutant
generator; item 103's corrections), then M8-3 and M8-5 in parallel on
`claude-opus-5.5` sub-agents in worktrees, reviewed line by line; the M9
plan on its own branch, as directed.
**Action required from you:** none on this commit; the specification
document will come to you as its own exact commit.
