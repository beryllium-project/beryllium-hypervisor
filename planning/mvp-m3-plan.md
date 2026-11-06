<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M3 plan: the policy layer and the hart binding in the model

## Decision record

The responsible human accepted this plan at exact commit
`c2c249f4c3d364590d2e505a4f6fb5e65456ff81` (parent `5349b258`, on branch
`beryllium/mvp-m3-plan` from `50b77c00`, the development branch's tip
after the M2 result acceptance record) on 2026-10-28. The instruction,
given in reply to the [review packet](mvp-m3-plan-review-summary.md)'s
request to accept, revise, or defer that exact commit, was
`accept c2c249f4`. The abbreviation resolves uniquely to that commit
(`git rev-parse --disambiguate=c2c249f4`). The first candidate
`9952e765` is superseded and was never accepted.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted, including the
  pre-decision status text below; only this section and the acceptance
  fields in the status record were set afterwards.
- **Open questions:** Q1 to Q12 were not answered, so their defaults
  apply: the hart binding as a Part 1 object class outside A8 (Q1); the
  model's lock refreshed after the accepted gate is re-run (Q2); the
  instances as policy-layer fixtures with Model 0.2's fixture a
  projection of Instance 1 (Q3); the proof-carrying `seal_with_policy`
  around the accepted seam (Q4); the seven enumerated edits (Q5); the
  generic A8 soundness theorem with the bridge lemmas (Q6); the rings'
  refinement (Q7); the Rocq oracle for the differential check (Q8, Q9);
  the model split (Q10); no model work before the revision is accepted
  (Q11); and the soft limits (Q12).
- **Authorized:** writing the security model revision, work package
  M3-1, as its own exact commit for the responsible human's decision,
  on branch `beryllium/mvp-m3` from this acceptance-record commit; and,
  **only after that revision's exact commit is accepted**, work
  packages M3-2 to M3-6 under this plan on the same branch, ending in
  one result review packet. Each [stop condition](#stop-conditions)
  returns M3 to the responsible human; a soft limit exceeded returns
  the limit for re-evaluation (stop condition 5). The repository's
  model split applies.
- **Not authorized:** M4; any change under `mvp/` beyond reading its
  scenario files and running its checker; any monitor or board work;
  any edit to an accepted Rocq or C mechanism file or to an accepted
  document other than the additive revision; root
  `Makefile`/`be`/`scripts/check-be.sh` integration; a push, a tag, a
  merge, publication, or release.
- **Evidence status:** acceptance adds no implementation, proof, or test
  evidence. Nothing of M3 has been written; the plan's two measurements
  are read-only runs of the accepted model on `l1`.

## Decision requested

**Status:** accepted on 2026-10-28; see the
[decision record](#decision-record). As presented, the plan was
proposed and not accepted, as the paragraph below states.

**Status as presented:** proposed for responsible-human review; not
accepted. No M3
work has started: nothing under `model/` or `planning/security-model-v1.md`
has changed for M3, and nothing has been built for it. Facts below come
from the accepted documents, the accepted Model 0.2 sources at
`f8f89758` (unchanged since), the MVP line at the M2 result `18d552bc`,
and two read-only planning measurements on the workstation `l1` named in
[Base and inputs](#base-and-inputs). *Fact* marks what a record or source
shows, *inference* reasoning from facts.

The accepted [MVP plan](mvp-plan.md) (exact commit `93967fba`, accepted
2026-10-23) defines M3, "The policy layer in the model, with differential
checking": the policy-to-manifest relation proved in the abstract model
and checked by two independent implementations, and the static hart
binding of its revision 1 stated and proved in the same model. It makes
M3 depend only on [security model v1](security-model-v1.md), the
additive revision M3 plans, and the instances, so that M3 may run
alongside the other milestones, and it requires that revision to be
accepted at its own exact commit before any model work. The responsible
human accepted the M2 result at exact commit `18d552bc` on 2026-10-28
(instruction `accept 18d552bc`; record `50b77c00`) and then directed
(`approve 1 & 2. proceed`) the development branch's fast-forward to that
record and its push, and this plan as a proposal on a new branch from
that tip. `beryllium/mvp-m2` and the development branch
`beryllium/single-hart-runtime-r0` are both at `50b77c00`, locally and
on the private `origin`. This plan's branch, `beryllium/mvp-m3-plan`,
starts there.

M3 changes no monitor byte and runs on no board. It adds to the accepted
abstract model and its executable form, under `model/`, the layer that
security model v1 defined and did not implement: the notation's
semantics, the analyses A1 to A6 and A8 as functions, the proof that a
manifest passing A8 grants no right the policy denies, the proof that the
declared flows are invariant under the derived mappings, and the three
instances (the fixed two-domain profile, M1's `te-poc`, M2's `anchor`) as
fixtures; and, under the planned revision of the security model, the
static hart binding of the MVP and the invariants the MVP plan's revision
1 relies on, stated and proved over that binding. The MVP line's offline
checker, `mvp/tools/policy-check.py`, and the model's checker then run on
every instance and on a seeded single-defect mutation set and must agree.
The accepted 23 obligations, Model 0.2's seam, and every accepted `model/`
source file stay unchanged; M3 adds files and extends the build lists it
enumerates.

On the responsible human's direction (`have it reviewed by gpt-5.6-sol
for potential steering (you decide what to incorporate)`; `I will
authorize gpt-5.6-sol for this session as a reviewer`), a first draft of
this plan was reviewed by that model on 2026-10-28 through a
session-scoped edit of the governance hook's required model, restored
afterwards; its twelve findings and their resolutions are recorded in
this plan's review packet, and this text incorporates them. On the
responsible human's question about Q12's bounds and direction that they
not constrain quality, the first candidate `9952e765` is superseded by
this text, whose limits are soft ([Soft limits](#soft-limits)).

Acceptance of this plan would authorize **writing the security model
revision** (M3-1) as its own exact commit for the responsible human's
decision, and, **after that revision is accepted**, work packages M3-2 to
M3-6 under this plan, on branch `beryllium/mvp-m3` from this plan's
acceptance record. It would not authorize M4, any change to the MVP line
under `mvp/` beyond the read of its scenario files, any monitor or board
work, root `Makefile`/`be`/`scripts/check-be.sh` integration, a push, or
a merge. Each [stop condition](#stop-conditions) returns M3 to the
responsible human.

### Open questions

Each has a default this plan applies if the responsible human does not
answer it.

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | How does the revision express the hart binding? | A `hart` **object class** in Part 1 (monitor-owned; the control hart and the domain harts; authority recorded in the manifest's binding records), the `domain` class's binding record naming its one hart, and four new invariants; **no new rule class** in Part 2, because running on a hart is the monitor's static assignment of a resource, not an access a subject exercises, and the policy stays about authority. The revision states the consequence for A8 explicitly: the hart binding is mechanism metadata **outside A8**, checked by I13 to I16, and A8's "binding" keeps the reading the MVP's checker implements, the domain's binding to its own extents as grants; the accepted `vcpu_state` and `root` classes, monitor-owned and outside the rule classes, are the precedent | A `hart` rule class with a `run` permission, `allow(domain_t, hartN_t, hart, {run})`, so that the binding is also a policy statement A1 to A4 and A8 analyze; it makes hart identifiers look like authority, which S1 H03 warns against |
| Q2 | The model's tool lock no longer matches `l1` (GCC 16.1.1 → 16.2.1, Rocq 9.2 → 9.3.0); how does M3 run the model's gates? | **Refresh the lock** in M3-2: on the clean accepted `model/` content, every target of the accepted gate but the version check (`unit`, `run`, `report-check`, `proof`, `source-check`, `evidence`) is run under the host's tools and its outputs compared with the accepted evidence; then `model/toolchain.conf`, `tests/check-tools.sh`, `tests/generate-evidence.sh`'s version line, and `Containerfile` move to the development host's versions as enumerated edits, and the full host gate and the rootless evaluator run again, the evaluator's agreement shown by its own `toolcheck`, not inferred | Build a pinned evaluator from a verified RPM cache (M0-B's method) carrying `rocq-9.2.0` and `gcc-16.1.1` from koji, and run every model gate inside it; the host would still not pass the lock |
| Q3 | Where do Instances 1 to 3 live in the model? | As **policy-layer fixtures** over a bounded manifest view (ownerships, extent bindings, channels, rights, harts) in a new C module and new Rocq terms, generated at build time from the instances' sources (Instance 1 verbatim from the security model as a fixture file; Instances 2 and 3 from the MVP's `scenarios/<name>/{policy.te,scenario.json}`) by a host generator; Model 0.2's proposal and canonical structures, whose bounds hold the fixed profile only (`BE_MAX_CHANNELS 1`, `BE_MAX_RESOURCES 11`), are not widened. Model 0.2's fixed-TE fixture is a **projection** of Instance 1, not Instance 1 (fact: `Model.v`'s `platform_inventory` has eleven frames and no guest-code frame, and its rights are read, write, and execute on four mappings; Instance 1 has two guest-code resources, 12 and 13, with `execute`), so the adapter from the accepted canonical state yields that projection's view, tested against a documented projection fixture, and the security model's Part 7 sentence "the fixed-TE fixture's topology is Instance 1" is recorded as an erratum, not edited | Widen Model 0.2's bounds so that Instances 2 and 3 become full proposals through the accepted seam; it reopens the accepted structures and the fixed Rocq inventory, and is not needed for the claims M3 makes |
| Q4 | How do the policy and labeling identities enter the configuration identity, and where does Part 7's "A8 before sealing" gate live? | In a **proof-carrying wrapper around Model 0.2's sealed state**: `seal_with_policy : canonical_state -> policy -> labeling -> option sealed_with_policy` (Rocq) and `be_seal_with_policy()` (C) succeed only when A1 to A6 and A8 pass, and the resulting record carries **one combined configuration identity**, a deterministic function of the canonical identity, the policy identity, and the labeling identity in the form the MVP's checker already uses; the theorem is that a policy-sealed state exists only for conforming inputs (sealing with policy implies conformance). `canonical_state` in `Model.v`, `be_canonical_state`, and `seal_state` are untouched. This realizes Part 7's rows 1 and 3 as a layer around the accepted seam rather than inside it, a departure recorded in [Accepted decisions M3 departs from](#accepted-decisions-m3-departs-from) for the responsible human | Gate inside the seam: add the checks to `validate_proposal`/`seal_state` and the two identity fields to the accepted structures, which edits `Model.v`, `Transition.v`, `manifest.h`, `state.c`, and every fixture |
| Q5 | Which accepted `model/` files may M3 edit? | Exactly these seven, each additively, enumerated in [The lock and the build lists](#the-lock-and-the-build-lists-m3-2): `model/Makefile`, `model/tests/run-proofs.sh`, `model/tests/check-reports.mjs`, `model/tests/check-tools.sh`, `model/toolchain.conf`, `model/Containerfile`, `model/tests/generate-evidence.sh`; an eighth file is a stop. The generator is written in Node.js (`.mjs`), which the model's source policy and lock already cover, so `tests/check-source-policy.sh` is not edited; `python3` becomes a lock role because the differential check runs the MVP's Python checker | Also extend `tests/unit/test_main.c` and `src/fixtures.c` in place, which edits accepted mechanism and test sources |
| Q6 | The form of the A8 soundness theorem? | Generic over the policy layer: for every validated policy, labeling, and manifest view that A8 accepts, every right the view grants is allowed by the policy; then instantiated on Model 0.2's projection of Instance 1 by composing with the accepted `claim_derived_rights_bounded` (leaf rights) and `claim_derived_root_soundness` (presence, `map`) through the adapter and two bridge lemmas (access kinds to permissions; canonical authority to view rights), so that for the fixed profile's four derived mappings every presence and every leaf right is policy-allowed | The fixed instance only, by computation; it would not state the general property |
| Q7 | What does "only the control hart writes shared monitor state" mean for the rings? | The revision states it precisely: every monitor-owned object shared between harts is either written only by the control hart (the published blocks, the barrier, the management state) or a **single-writer ring** with exactly one writer hart and one reader hart named by the binding (a domain hart writes its outbound ring, the control hart its inbound one); the Rocq obligation is over that classification | Keep the MVP plan's sentence as written, which the outbound rings would falsify |
| Q8 | The mutation set for differential checking, and its oracle? | Seeded (S1 H39), at least 64 single-defect mutations of the three instances' policies, labelings, and views (a rule dropped, a permission added or removed, a label swapped, an undeclared type or unknown permission introduced, a need set narrowed, a channel without storage, storage without a channel, a secret page labeled readable, a grant without a rule), each with its expected per-analysis verdict computed by the **Rocq analyses** on the same terms (`Eval vm_compute`), the independent oracle the security model's Part 4 names; both host checkers are compared with the oracle and with each other; hart-binding mutations are outside this set, because the MVP's checker reads no hart, and are tested under the binding module and its C tests; the exact count and seed pinned at M3-5 | Expected verdicts from the MVP's checker alone, which would make the comparison circular |
| Q9 | Does the differential driver call the MVP checker across trees? | Yes: `model/tests/differential.sh` runs `mvp/tools/policy-check.py` from the same commit on the instance and mutation files the generator writes, the model's C checker on the C data the same generator emits, and the Rocq oracle on the terms it emits; the MVP inputs it reads (`mvp/tools/policy-check.py`, the two scenarios' files) are hashed into the model's evidence | Copy the MVP checker's rules into the model, which would make the two checkers one |
| Q10 | The model split? | The repository's: this plan, the revision, and the review on the orchestrating model; the Rocq, C, generator, and driver on `claude-opus-5.5` (`max`, `long_context`) | As the responsible human directs |
| Q11 | May M3 proceed before the revision is accepted? | No: M3-1 is written and presented; M3-2 to M3-6 start only after the revision's exact commit is accepted, as the MVP plan requires; the lock measurement of M3-2 is host-only and is not committed before then | Begin M3-2 (lock) in parallel with the revision's review |
| Q12 | Soft limits for the new code? | **Soft limits, for re-evaluation, not quality constraints** (the responsible human's direction, 2026-10-28): new Rocq about 3,000 lines and the whole proof, the oracle's evaluation included, about 180 s on `l1`; new restricted C about 2,000 lines; the generator and driver about 1,500 lines of Node.js and shell together; no monitor line changes (by construction). Exceeding one is stop condition 5, a return to the responsible human to re-evaluate the limit against the work it measures; it is never a reason to trim a theorem, a check, a fixture, or a mutation, and the limits are inferred ceilings (see [Soft limits](#soft-limits)), not sized estimates | Hard bounds, which the responsible human declined |

## Goal and pass criterion

**Goal.** Security model v1's policy layer, which the model defined and
did not implement, exists in the abstract model and in its executable
form, with its two new invariants proved in Rocq; the static hart binding
of the MVP is stated in the security model by an additive revision and
proved in the same model; and two independent checkers agree on every
instance and on a seeded mutation set.

**Pass criterion.** All of:

1. The security model revision (M3-1) is responsible-human accepted at
   its own exact commit, and it changes no accepted analysis, instance,
   or claim.
2. `make -C model proof` compiles the accepted modules and the new ones
   with no escape hatch, and the new claim set states and proves: the
   validated notation's semantics is a total function with deny as its
   default (I10); a validated manifest view that passes A8 grants no
   right the policy denies (I11), instantiated on Model 0.2's projection
   of Instance 1 through `claim_derived_rights_bounded` and
   `claim_derived_root_soundness`; a view passing A8 has a flow relation
   contained in the policy's, whose transitive closure A6 equates with
   the declared channels' (equality of the three for the fixed projection
   by computation); a policy-sealed state exists only for inputs passing
   A1 to A6 and A8; the binding maps domains to harts injectively and
   totally, onto harts other than the control hart; each hart's private
   state is disjoint from every other hart's and from every domain's
   memory, and no domain root maps it; and, over an enumerated
   transition vocabulary with total write footprints, only the control
   hart's transitions write control-written shared state and only a
   ring's writer writes it (Q7). The accepted 23 obligations are
   unchanged in statement and proof text, and the new claim bundle's
   `Print Assumptions` reports are closed.
3. The model's C checker validates the raw policies and labelings (A1)
   and runs A2 to A6 and A8 on the three instances with the results the
   security model states (Instances 1 and 2 pass every analysis;
   Instance 3 passes every analysis, A7 vacuous); `be_seal_with_policy`
   refuses every A8-failing input and reports one combined configuration
   identity; the unit tests pass with identical GCC and Clang output.
4. The Rocq oracle, the MVP's offline checker, and the model's checker
   agree on every instance and every mutation of the seeded set, and the
   set is at least Q8's size.
5. `make -C model check` passes on `l1` under the refreshed lock, and
   `./be evaluate` passes in the rootless evaluator.
6. Every soft limit of Q12 holds, or was re-evaluated and re-set by the
   responsible human under stop condition 5; every stop condition is
   clear.

## Base and inputs

**Base.** This plan's branch starts at `50b77c00`, the M2 result's
acceptance record, which the development branch holds. The
implementation branch `beryllium/mvp-m3` starts at this plan's acceptance
record.

**Accepted inputs, unchanged by M3:**

- [Security model v1](security-model-v1.md) at `0e3eec8b` (accepted
  2026-10-22): the notation (Part 2), I1 to I12, A1 to A8 (Part 3),
  validate over compile (Part 4), the Part 7 inventory of additive Model
  0.2 changes, Instances 1 and 2, V1 to V4 at their defaults. Its status
  record reads `security_model_v1_analyses=A1-A8-defined-not-implemented`
  and `security_model_v1_model_change=none`.
- [Architecture Model 0.2](architecture-model-0.2.md) and its
  [evidence](architecture-model-0.2-evidence.md), accepted 2026-07-24;
  `model/` at `f8f89758` (2026-07-23), unchanged since (fact: `git log
  -- model`). Rocq: `Assumptions.v` (35 lines), `Model.v` (542),
  `Initialization.v` (399), `Isolation.v` (280), `Transition.v` (443),
  `Claims.v` (288), 1,987 lines, with the 23-obligation record
  `architecture_model_0_2_claim_set` (`claim_inventory_closure` to
  `claim_terminal_fail_closed`). C: `src/manifest.c` (1,293 lines),
  `src/state.c` (665), `src/fixtures.c` (219; two neutral fixtures, the
  minimal-ownership and fixed-TE topologies), `tools/model-run.c`,
  `tools/model-report.c`, `tests/unit/test_main.c` (11 tests),
  `tests/check-reports.mjs` (262 lines). The bounded structures hold the
  fixed profile: `BE_MAX_DOMAINS 2`, `BE_MAX_RESOURCES 11`,
  `BE_MAX_AUTHORITIES 12`, `BE_MAX_ROOTS 2`, `BE_MAX_MAPPINGS 12`,
  `BE_MAX_SAVED_STATES 2`, `BE_MAX_CHANNELS 1` (`include/be/manifest.h`).
  The Rocq model enumerates the same fixed instance (`Model.v`: two
  domains, eleven frames, two GPAs). The model deliberately has no
  manifest parser or stable encoding; its configuration identity is for
  reporting and equivalence, not integrity.
- The [MVP plan](mvp-plan.md) at `93967fba`: M3's goal, deliverables 1 to
  3, exit, and evidence; "Method per claim" rows for I10, I11, and the
  per-hart state; stop condition 1's admission of the revision;
  departure row 4; D7.
- The MVP line at `18d552bc`: `mvp/tools/policy-check.py` (1,098 lines;
  A1 to A6 and A8, A7 vacuous for a fixed binding; 45 self-test cases;
  14 named mutations), the scenarios `mvp/scenarios/{te-poc,anchor}/
  {policy.te,scenario.json}` and their reports (`te-poc`: 2 subjects, 10
  objects, 6 grants, 1 flow, configuration identity `9cf02807…`;
  `anchor`: 2 subjects, 13 objects, 12 grants, 2 flows, identity
  `336bfddc…`), and the MVP's hart layout (M0 plan: the control hart 0,
  domain harts as scenario data, the hart region at `0x102044000` with
  per-hart blocks, two single-writer rings per domain).
- The fixed two-domain profile's policy, Instance 1, from security model
  v1 Part 2, whose topology is the fixed-TE fixture of `model/src/
  fixtures.c`.

**Planning measurements (read-only, `l1`, 2026-10-28).**

- Fact: `make -C model proof` passes under Rocq 9.3.0 (`rocq-9.3.0-1.fc44`,
  `rocq-stdlib-9.2.0-1.fc44`) in 18.5 s (`Beryllium Architecture Model
  0.2 proofs: PASS`), so the accepted proof compiles under the newer
  prover.
- Fact: `make -C model toolcheck` fails on `l1` at its first mismatch,
  `Model 0.2 requires GCC 16.1.1` (`l1` has GCC 16.2.1); the Rocq check,
  `version 9.2`, would fail next (`l1` has 9.3.0). Clang 22.1.8, Node.js
  v22.22.2, and GNU Make 4.4.1 match. So `make -C model check` and
  `./be model-check` cannot pass on `l1` without Q2's remedy, and the
  rootless evaluator's `Containerfile`, which installs `gcc` and `rocq`
  from Fedora's current repositories over the pinned base image, would
  install the same newer versions (inference from the package set).

**Tooling.** The model's lock after Q2, with `python3` as a new lock role
for `mvp/tools/policy-check.py` in the differential check; the generator
in Node.js, which the lock already covers.

## Architecture

### The security model revision (M3-1)

An additive section of `planning/security-model-v1.md`, "Revision 1
(2026): the hart binding and the third instance", with its own status
record, presented as its own exact commit. It makes exactly these
changes, each named as additive:

1. **Part 1, object classes:** a `hart` class (monitor-owned; the control
   hart and each domain hart; authority recorded in the manifest's
   binding records and the per-hart state's extents) and, in the `domain`
   row, the binding to its one hart. Q1's default: no Part 2 rule class.
2. **Part 1, invariants:** I13 to I16, numbered after I12, with their
   fixed-instance status (none proved; M3 is to prove them over the
   static binding):
   - I13 each hart runs at most one domain;
   - I14 each domain runs on exactly one hart;
   - I15 per-hart monitor state (the hart's saved frame, trusted stack,
     and private data) is private to its hart: mapped by no domain root
     and written by no other hart;
   - I16 every monitor-owned object shared between harts is either
     written only by the control hart (the published per-hart blocks,
     the barrier and generation, the management state) or a
     single-writer ring with exactly one writer hart and one reader hart
     named by the binding; before the barrier only the control hart
     writes shared state (Q7).
   The revision also states that the hart binding is mechanism metadata
   outside A8, checked by I13 to I16 (Q1). I5 and I7 are restated to
   apply to each hart's single entry and to M2's `pause` and `terminate`
   (MVP plan departure row 4); their text is quoted and not edited.
3. **Part 2, Instance 3:** M2's `anchor` policy and labeling verbatim from
   `mvp/scenarios/anchor/policy.te` and the scenario's labeling, with its
   need sets, as the third instance; its A1 to A8 results as the MVP's
   checker reports them (A7 vacuous).
4. **Part 7, inventory:** three rows added: the binding and the `hart`
   class (abstract model: a binding function and its obligations; C: a
   bounded binding view), the per-hart state as monitor-owned objects,
   and the rings as single-writer objects with declared writer and
   reader; and the "Fixtures" row extended by Instance 3. Beside the
   accepted "Fixtures" row, whose text says the fixed-TE fixture's
   topology is Instance 1, the revision records the erratum: Model 0.2's
   fixture is a projection of Instance 1 without the guest-code
   resources and `execute` (Q3); the accepted row is not edited.
5. **Status record:** `security_model_v1_revision_1=…`, the new
   invariants, classes, and instances; the v1 fields unchanged.

The revision changes no accepted analysis (A1 to A8 keep their text),
no instance (Instances 1 and 2 keep theirs), and no claim; it is the one
planned change that MVP plan stop condition 1 admits. Its own review
packet asks the responsible human to accept its exact commit before
M3-2 begins.

### The policy layer in Rocq (M3-3)

A new module, `model/proof/Policy.v`, defines the notation of security
model v1 Part 2 and its analyses as functions over finite types, in the
style of the accepted modules (no axioms, no admitted proofs; the
accepted `run-proofs.sh` escape-hatch grep applies to it):

- **Raw terms and validation (A1).** A raw policy is a list of `allow`
  rules over *names* (natural-number identifiers for subject types,
  object types, classes, and permissions), a raw labeling a list of
  (subject or object, type-name) pairs, and a raw view a record of
  ownerships (object, owner domain), extent bindings (domain, extents),
  channels (object, writer, reader), rights (subject, object, class,
  permission names), and the hart set with its control hart. `a1` is the
  validator: every type and class declared, every permission in its
  class, every rule's permission set nonempty, every subject and object
  labeled exactly once with a declared type. It yields a **validated**
  policy, labeling, and view (typed finite values with a total labeling)
  or a finding. Undeclared types, unknown permissions, and unlabeled
  objects are therefore representable and rejected, as the MVP checker's
  A1 mutations exercise.
- **Semantics (T1, I10).** `decide validated s t c p : bool`, true iff
  some rule allows it; T1 states that `decide` is a function on the whole
  of its domain and that with no rule every permission is denied.
- **Analyses.** `a2` to `a6` and `a8` as decidable functions over
  validated values with the definitions of Part 3, the need sets of A4 as
  inputs; `a7` a function that is vacuous for a view with no delegation,
  so that its absence of effect is a theorem.
- **T2 (I11, A8 soundness).** For every validated policy, labeling, and
  view, `a8 = true` implies that every right the view grants to a subject
  on an object is allowed by `decide`, and every channel endpoint in the
  view has its `send` or `receive` rule. A8 is an upper bound: a view may
  grant less than the policy allows and still pass.
- **T3 (A6 and the flows).** T3a, confinement: for every validated view
  passing A8, the flow relation computed from the view's rights (a write
  by one subject and a read by another on one object) is contained in
  the flow relation computed from the policy. T3b: for every validated
  policy passing A6, the transitive closure of the policy's flow relation
  equals the transitive closure of the declared channel relation, as
  Part 3 defines A6. Equality of the view's flows, the policy's flows,
  and the declared channels holds for the fixed projection and is shown
  by computation; it is not claimed in general, because A8 does not
  require the view to realize every allowed flow.
- **Sealing with policy (Part 7).** `seal_with_policy : canonical_state
  -> raw_policy -> raw_labeling -> option sealed_with_policy`, defined
  over the accepted `canonical_state` type, returns a record only when
  A1 to A6 and A8 pass on the canonical state's view; the record carries
  the canonical identity, the policy identity, the labeling identity,
  and **one combined configuration identity**, a deterministic function
  of the three in the form the MVP's checker uses; T5 states that a
  policy-sealed state exists only for conforming inputs.
- **Instance 1 and Model 0.2's projection.** `view_of_canonical :
  canonical_state -> raw_view`, over the accepted `Model.v` types, maps
  the fixed profile's `canonical_configuration` to its view: eleven
  frames, two GPAs, four mappings with read, write, and execute rights,
  no guest-code frame (fact: `Model.v` `platform_inventory`,
  `canonical_authority`). That view is Model 0.2's **projection** of
  Instance 1, whose full policy also labels the two guest-code resources
  with `execute`; both are terms (`instance1_*` and `instance1_m02_*`),
  and the adapter is tested against the projection. Two bridge lemmas
  connect the accepted model to the policy layer: the access kinds of
  `Model.v` (read, write, execute) to the policy's permissions, and
  membership in `canonical_authority` to a right of the view. **T4**
  composes T2 with the accepted `claim_derived_rights_bounded` (every
  derived leaf right is within canonical authority) and
  `claim_derived_root_soundness` (every derived mapping's presence is a
  canonical mapping, which the policy must allow as `map`): for the fixed
  projection, every derived mapping's presence and every leaf right of
  `derive_enforcement canonical_configuration` is allowed by `decide`.
  The accepted claims are used, not restated or re-proved.
- **Instances 2 and 3** are terms generated from the MVP's scenario files
  (`instance2_*`, `instance3_*`) with their views, and their analyses are
  evaluated by computation to the results the security model states.

### The hart binding in Rocq (M3-3)

A second new module, `model/proof/Binding.v`, states the MVP's static
binding and the revision's invariants over it:

- **Types.** Harts (an enumeration of the started harts: the control hart
  and the domain harts; the never-started harts are outside the model),
  domains (the instance's), the binding `hart_of : domain -> hart`, the
  control hart, and the monitor-owned objects classified by the
  revision: **per-hart private** objects (the hart's saved frame, trusted
  stack, and private data, as concrete extents of the hart region and
  the MVP region), **control-written shared** objects (the published
  per-hart blocks, the barrier and generation, the management state),
  and **single-writer rings** with `writer : ring -> hart` and `reader :
  ring -> hart`; a transition vocabulary enumerated from the MVP's
  control loop and fast path (publish, start, ready, enter, exit record,
  drain, PING and PONG, request, decide and deliver, answer, pause,
  terminate, park, shutdown, each labeled by the hart that takes it and
  by its phase, before or after the barrier) with a **total write
  footprint** per transition.
- **H0.** Every domain's hart is not the control hart.
- **H1 (I13, I14).** `hart_of` is injective and total: each hart has at
  most one domain and each domain exactly one hart.
- **H2 (I15).** Each hart's private objects are pairwise disjoint from
  every other hart's and from every domain's memory (the domain's private
  region and every channel's object), and no domain root maps them.
- **H3 (I16).** Before the barrier, every transition that writes a
  shared object is the control hart's. After the barrier, every
  transition that writes a control-written shared object is the control
  hart's, every transition that writes a ring is its writer's, and no
  transition of a domain hart writes another hart's private object.
- **The MVP instance.** A term for the three-hart layout (control hart 0,
  domains G0 and G1 on harts 1 and 2, two rings per domain: the outbound
  ring written by the domain hart and read by hart 0, the inbound ring
  the reverse) with H0 to H3 evaluated and proved for it; the hart
  identifiers are configuration data in the term, not authority.

The vocabulary is nonempty and exhaustive for the MVP's monitor as the
M0 to M2 plans describe it, so H3 is not vacuous; the footprints are the
plan's reading of the MVP sources, recorded in the module with their
source lines, and a footprint the sources contradict is stop condition 4.
The hart obligations are about the static binding and the labeling of
transitions by hart; they say nothing about concurrent execution, memory
ordering, the IPI protocol, or the barrier's implementation, which the
MVP plan names as unmodeled. `Transition.v`'s accepted transitions are
not re-labeled; Model 0.2 is the policy layer's adapter instance only,
not a binding instance, since its two domains on one hart could not
satisfy H1.

A third new module, `model/proof/PolicyClaims.v`, collects T1 to T5 and
H0 to H3 in a record `security_model_v1_claim_set` and proves it, as
`Claims.v` does for the 23; `Claims.v` is untouched, and the new record
does not include the accepted claims. A fourth, `PolicyAssumptions.v`,
prints the assumptions of each new theorem and of the record, and
`run-proofs.sh` checks that every report is closed, as it does for the
accepted 24.

### The executable model and host checker (M3-4)

- **`model/src/policy.c` and `model/include/be/policy.h`** (restricted
  C, the model's source policy): bounded raw and validated structures for
  a policy, a labeling, a manifest view, and need sets, with bounds that
  hold the three instances (`BE_POLICY_MAX_RULES`, `BE_POLICY_MAX_TYPES`,
  and so on, pinned at M3-4); `be_policy_validate` (A1, raw to
  validated or a finding), `be_policy_decide` (I10), `be_policy_a2` to
  `be_policy_a6` and `be_policy_a8` returning a per-analysis result and a
  bounded finding list; `be_policy_identity`, `be_labeling_identity`, and
  `be_seal_with_policy`, which fills a `struct be_sealed_with_policy`
  (the three identities and the combined one, by the accepted identity
  method re-declared in the new header rather than exported from the
  accepted file) only when A1 to A6 and A8 pass; and
  `be_view_of_canonical`, the C adapter from `struct be_canonical_state`
  to a raw view for Model 0.2's projection of Instance 1.
- **Generated fixtures, no runtime parser (Q3).**
  `model/tools/gen-policy-fixtures.mjs` reads Instance 1 (a fixture file
  under `model/fixtures/` in the notation, verbatim from the security
  model, with its labeling and need sets) and the MVP's `mvp/scenarios/
  {te-poc,anchor}/{policy.te,scenario.json}`, and writes
  `build/model/policy/fixtures.c` (the three instances and the mutation
  set as C data), `build/model/policy/Instances.v` (the same as Rocq
  terms, for the oracle), and `build/model/policy/mutations/<n>/
  {policy.te,scenario.json}` (the same for the MVP checker). The
  generator is a build-time translator of two file formats; what Model
  0.2's decision preserves is that the model's binaries read no file at
  run time and that no stable or public encoding is introduced. Its
  output is compared across GCC and Clang builds and across two runs
  (deterministic).
- **`model/tests/unit/policy_test.c`**, a new unit binary beside
  `test_main.c`: A1's refusals (an undeclared type, an unknown
  permission, an unlabeled object); the analyses on each instance against
  the security model's stated results; the adapter's view of the
  fixed-TE fixture equals the projection fixture; `be_seal_with_policy`
  refusing each A8-failing mutation and its combined identity's
  determinism; the binding checks for the MVP layout, including the
  non-injective and control-hart mutations Q8 excludes from the
  differential set; identical GCC and Clang output on pinned counts.
- **`model/tools/policy-run.c` and `model/tools/policy-report.c`**: the
  checker over the compiled fixtures with per-analysis verdicts in a
  stable text form the differential driver reads, and a deterministic
  report of the three instances' analyses and identities, which
  `tests/check-reports.mjs` learns to check beside the accepted report
  (an enumerated edit).

### Differential checking (M3-5)

`model/tests/differential.sh` runs, from one commit, three computations
of the analyses on the same instances and mutations and compares them
verdict by verdict: the **Rocq oracle**, `Eval vm_compute` of `Policy.v`'s
analyses on the generated `Instances.v` terms, whose printed verdicts the
driver reads; the **model's checker**, `policy-run` on the compiled C
data; and the **MVP's checker**, `mvp/tools/policy-check.py` on the
generated files, through its existing command line. The oracle is the
reference the security model's Part 4 names ("an offline tool and a Rocq
decision procedure ... compared"); the two host checkers must each agree
with it and with each other. The driver prints `BE_MODEL_DIFFERENTIAL:
PASS instances=3 mutations=<n> comparisons=<3*(3+n)>` or the first
disagreement with all three verdicts. The mutation set (Q8) is seeded,
single-defect, and at least 64, with each mutation mapped to the claim it
must fail (S1 H39) and the analysis that must fail it. Agreement is the
claim; neither host checker is thereby proved to be the Rocq function,
and the packet says so.

### The lock and the build lists (M3-2)

The accepted `model/` files M3 edits, each additively and each
enumerated here (Q5); an eighth is a stop:

| File | Edit | Why |
| --- | --- | --- |
| `model/toolchain.conf` | `gcc_version=16.1.1` → `16.2.1`; `proof_assistant=rocq-9.2` → `rocq-9.3`; a `python3_version` line | Q2: the development host's versions, after the accepted gate passes under them; the MVP checker's interpreter as a lock role |
| `model/tests/check-tools.sh` | The two version strings; a `python3` check | The same |
| `model/tests/run-proofs.sh` | The module list gains `Policy`, `Binding`, `PolicyClaims`, `PolicyAssumptions` after the accepted six, in that order; the generated `Instances.v` is compiled for the oracle; the closed-assumption count check covers the new reports beside the accepted 24 | The new modules compile and are checked by the same runner, with the same escape-hatch grep and the same assumption audit |
| `model/Makefile` | Targets for the generator, `policy_test`, `policy-run`, `policy-report`, `policy-oracle`, and `differential`, added to `unit`, `run`, `reports`, and `test` | The new work in the model's own gate, so that `make -C model check` and `./be model-check` cover it |
| `model/tests/check-reports.mjs` | The new report's checks | The report's determinism and content, as the accepted report's |
| `model/tests/generate-evidence.sh` | The `proof=` line's prover and obligation count; the new reports, the oracle's verdict table, the differential result, and the hashes of the MVP inputs the differential reads (`mvp/tools/policy-check.py`, the two scenarios' `policy.te` and `scenario.json`) in the evidence | The evidence names what the gate ran and what it read across trees |
| `model/Containerfile` | `python3` in the package list | The differential check runs in the rootless evaluator too |

No other accepted file under `model/` changes; `src/fixtures.c`,
`tests/unit/test_main.c`, `tools/model-run.c`, `tools/model-report.c`,
`tests/check-source-policy.sh` (the generator is `.mjs`, a type it
already covers), `tests/run-rootless.sh` (it delegates to `make check`),
and the six accepted Rocq modules are byte-identical before and after.
Root `Makefile`, `be`, and `scripts/check-be.sh` are untouched: `./be
model-check` and `./be evaluate` already call the model's `check` and
`evaluate` targets (fact: root `Makefile`).

The refresh itself is gated: first, on the clean accepted `model/`
content, `make -C model unit run report-check proof source-check
evidence` runs under GCC 16.2.1 and Rocq 9.3.0 and its reports and
evidence are compared with the accepted evidence record (the proof's 24
closed reports, the two reports' identity, the unit counts); only then
are the lock files edited and the full `make -C model check` and `./be
evaluate` run, the evaluator's agreement shown by its own `toolcheck`
inside the container. A difference in the accepted content's results
under the new tools is stop condition 6.

### What M3 does not do

No monitor source, image, scenario, or board run changes or happens; the
MVP line is read, not edited (its checker runs from the same commit). No
C refinement: neither checker is proved to be the Rocq function. No
proof about the implementation's rings, IPIs, barrier, or memory
ordering. No dynamic management, delegation, revocation, or A7 beyond its
vacuous form. No change to the 23 obligations or to any accepted Rocq or
C mechanism file. No claim ledger (M4).

## Soft limits

The limits below are soft (the responsible human's direction of
2026-10-28: "I don't want these somewhat arbitrary limits to impact the
quality of the project; make them soft limits that cause a stop for
reevaluation if exceeded"). Each is an inferred ceiling whose purpose is
to notice growth, not to constrain it: when one is exceeded, the work
stops (stop condition 5) and the responsible human re-evaluates the limit
against what the work needs, re-setting it or not; the deliverable, the
proof, the checks, and the mutation set are not cut to fit. The line
limits rest on the accepted model's 1,987 Rocq lines for 23 obligations
and a rough shape of the new modules; the time limit on the 18.5 s the
accepted proof takes under Rocq 9.3.0; neither is a sizing estimate, and
M3-3 may re-pin them from one, as a plan note.

| Item | Soft limit | Source |
| --- | --- | --- |
| New Rocq | about 3,000 lines across the four modules, the generated `Instances.v` excluded | Q12; inference from the accepted 1,987 lines for 23 obligations, plus the raw terms and validator |
| Proof time | the whole `make -C model proof` with the oracle's evaluation about 180 s on `l1` | Q12; measured 18.5 s today for the accepted modules |
| New restricted C | about 2,000 lines (`policy.c`, `policy.h`, `policy_test.c`, `policy-report.c`, `policy-run.c`), the generated fixtures excluded | Q12 |
| Generator and driver | about 1,500 lines of Node.js and shell | Q12 |
| Mutation set | at least 64 (Q8); every mutation rejected by the oracle and both checkers in the same analysis | S1 H39 |
| Monitor change | none | By construction |

## Tests and evidence

| Layer | Check | Pass criterion |
| --- | --- | --- |
| Revision | The revision's own review packet; `grep` that A1 to A8's and Instances 1 and 2's text is unchanged against `0e3eec8b` | Accepted at its exact commit |
| Proof | `make -C model proof` (the escape-hatch grep, compile, `rocq check`, the assumption audit) | PASS with the ten modules; every assumption report closed; the 23 accepted claims unchanged in text (`git diff` of the six modules empty) |
| Unit | `make -C model unit` (the accepted `test_main` and the new `policy_test`, GCC and Clang) | Identical output on pinned counts |
| Run and reports | `make -C model run report-check` | The accepted report unchanged; the new report deterministic and as the security model states |
| Differential | `make -C model differential` (the oracle, the model's checker, the MVP's checker) | `BE_MODEL_DIFFERENTIAL: PASS` with the pinned mutation count; three-way agreement |
| Lock and gate | `make -C model check`; `./be model-check`; `./be evaluate` | PASS on `l1` under the refreshed lock and in the rootless evaluator |

## Accepted decisions M3 departs from

| # | Accepted decision or recorded guidance | Departure | Accounted for by |
| --- | --- | --- | --- |
| 1 | Security model v1's object classes have no hart, and I5 and I7 are stated for switches on one hart | Revision 1 adds the `hart` class and I13 to I16 | MVP plan deliverable 1 and departure row 4; the one change stop condition 1 admits; its own exact commit |
| 2 | Model 0.2's tool lock pins GCC 16.1.1 and Rocq 9.2 | The lock moves to the development host's versions | Q2; the accepted proof and tests re-run under them first; the responsible human's `refresh the lock` direction for the MVP lock is precedent, not authority, so Q2 is asked |
| 3 | Model 0.2's accepted test and build files | Seven enumerated additive edits | Q5; everything else new |
| 4 | The MVP plan's "the control hart is the only writer of shared monitor state" | Refined for the single-writer rings, which domain harts write, and for the pre-barrier phase | Q7; the refinement is the MVP's design (M0 plan's rings), stated rather than changed |
| 5 | Security model v1 Part 7 places A8 "before `sealed` as part of canonical validation" and the identities "in the configuration identity" of the canonical state | The gate and the combined identity are a proof-carrying layer around Model 0.2's sealed state (`seal_with_policy`), not inside `validate_proposal`/`seal_state` | Q4; the accepted seam and its 23 obligations stay unchanged, which the MVP plan's M3 requires; the alternative edits five accepted files |
| 6 | Security model v1 Part 7: "the fixed-TE fixture's topology is Instance 1" | Model 0.2's fixture is a projection of Instance 1 (no guest-code frames, no `execute` right, four mappings) | Q3; recorded as an erratum of the accepted text, which is not edited; T4 is stated for the projection |
| 7 | Model 0.2's "no manifest parser or stable encoding" | A build-time generator translates the instances' files into C and Rocq terms | Q3; the model's binaries read no file at run time and no stable or public encoding is introduced |

## Risks

| Risk | Mitigation |
| --- | --- |
| Rocq 9.3.0 rejects a construct the new modules need, or a later Fedora update moves the prover again | The accepted modules already compile under 9.3.0; the lock pins the version the gate ran with; a further move is stop condition 6 |
| The generic A8 soundness theorem is hard to state over Model 0.2's `canonical_state` without editing `Model.v` | The adapter is a function over the accepted types, defined in the new module; if the fixed instance's view cannot be expressed that way, stop condition 2 |
| The oracle and a checker, or the two checkers, disagree on a mutation because the security model's definition admits two readings | The disagreement is a finding about the definition; it returns to the responsible human (stop condition 3) rather than being resolved by picking one reading |
| The generator becomes a runtime parser in disguise | It runs at build time only and writes C and Rocq terms; the model's binaries read no file; a unit case greps `model/src/` and `model/tools/policy-*.c` for file reads |
| The Rocq oracle's evaluation is slow on the mutation set | `vm_compute` over small finite instances; the proof-time soft limit includes it; a slow oracle is a re-evaluation stop, not a reason to drop it |
| The proof's size or time exceeds a soft limit | Stop condition 5: the responsible human re-evaluates the limit; the work is not cut to fit |

## Claim boundary and non-goals

M3's result would support saying: in the abstract model, security model
v1's validated policy semantics is total and default-deny (I10); a
validated manifest view that passes A8 grants no right the policy denies
(I11), and for Model 0.2's projection of the fixed two-domain profile
every derived mapping's presence and leaf right is policy-allowed; a view
passing A8 has flows within the policy's, whose transitive closure A6
equates with the declared channels' (the three equal for the fixed
projection); a policy-sealed state exists only for conforming inputs and
carries one combined configuration identity; the MVP's static hart
binding is injective and total onto non-control harts, each hart's
private state is disjoint from the others' and from domain memory and
unmapped by every root, and over the enumerated transition vocabulary
only the control hart's transitions write control-written shared state
while each ring is written by its one writer, all over the static
binding; the three instances are fixtures whose analyses the model
computes; and the Rocq oracle and two independently written checkers
agree on them and on the mutation set.

It would not support saying: that any C code is proved (the model's
checker and the MVP's are tested, not refined); that the MVP monitor
satisfies I10 to I16 (the proof is about the abstract model; the boot
barrier, the rings' implementation, the IPI protocol, and memory ordering
are unmodeled); that Beryllium is formally verified; that any hardware
result exists for M3 (none is run); or that any dynamic case (Part 6, A7)
is modeled.

Non-goals: M4; a runtime policy mechanism; Model 0.3; a Sail or Cerberus
integration; widening Model 0.2's bounds; a manifest encoding or parser;
root integration; any push or merge.

## Work packages

| Package | Delivers | Exit |
| --- | --- | --- |
| M3-1 The security model revision | The additive section of `planning/security-model-v1.md` (the `hart` class, I13 to I16, Instance 3, Part 7's rows, the status record) and its review packet, as one exact commit | Responsible-human acceptance of that exact commit; nothing else starts before it |
| M3-2 The lock and the build lists | The host-only re-run of the accepted gate (all but the version check) under GCC 16.2.1 and Rocq 9.3.0, compared with the accepted evidence and recorded; the seven enumerated edits; `make -C model check` and `./be evaluate` passing with the accepted content under the refreshed lock | The accepted gate passes under the refreshed lock on the host and in the evaluator; every other accepted file byte-identical |
| M3-3 The Rocq policy layer and the binding | `Policy.v`, `Binding.v`, `PolicyClaims.v`, `PolicyAssumptions.v`; T1 to T5 and H0 to H3; the three instances and the projection as terms | `make -C model proof` PASS with no escape hatch; the six accepted modules unchanged; the proof-time soft limit, or its re-evaluation |
| M3-4 The executable model and host checker | `policy.h`, `policy.c` (A1 validation, A2 to A6 and A8, `be_seal_with_policy`, the adapter), the generator (`.mjs`: C data, Rocq terms, the MVP checker's files), `policy_test.c`, `policy-run.c`, `policy-report.c`, the report check | `make -C model unit run report-check` PASS, GCC = Clang on pinned counts; the instances' results as the security model states |
| M3-5 Differential checking | The seeded mutation set; the Rocq oracle's verdict table; `differential.sh`; the make target | `BE_MODEL_DIFFERENTIAL: PASS`: three-way agreement on three instances and at least 64 mutations |
| M3-6 The record and the packet | The model's evidence (`make -C model evidence`), `./be model-check` and `./be evaluate` at the exact commit, a new evidence record `planning/mvp-m3-evidence.md` (the accepted Model 0.2 evidence document is not edited), the result review packet | The gates pass at the exact commit from a clean tree; the packet presents it |

## Stop conditions

Each returns M3 to the responsible human.

1. The revision cannot be written additively: any need to change the text
   of an accepted analysis, instance, invariant, or claim in security
   model v1, or any accepted document other than by the additive
   revision this plan names.
2. Any need to edit an accepted Rocq module (`Model.v`, `Initialization.v`,
   `Isolation.v`, `Transition.v`, `Claims.v`, `Assumptions.v`) or an
   accepted C mechanism or fixture file to state or prove a new
   obligation, including to express Instance 1's view.
3. The Rocq oracle and a host checker, or the two host checkers,
   disagree on an instance or a mutation for a reason the security
   model's text does not decide.
4. A new obligation is false as the revision states it: the proof attempt
   finds a counterexample in an instance (for example, a ring with two
   writers in the MVP layout, a private object shared, or a transition
   whose footprint the MVP sources contradict).
5. A soft limit of Q12 is exceeded, which returns the limit, not the
   deliverable, to the responsible human for re-evaluation; or the
   mutation set cannot reach Q8's size with single-defect mutations that
   the oracle and both checkers reject.
6. The accepted `model/` content gives a different result under the
   host's GCC 16.2.1 or Rocq 9.3.0 than its accepted evidence records;
   the pinned prover or compiler changes again on the development host
   before the exact commit; or the rootless evaluator cannot install the
   locked versions.
7. Any need for an eighth accepted-file edit under `model/` (Q5), a root
   file change, a change under `mvp/`, or a tool role beyond `python3`.
8. Any need to model concurrency, memory ordering, the IPI protocol, or
   the barrier to prove a hart obligation (they are out of M3's claim
   boundary by the MVP plan).
9. Any need to change an accepted R0-R7 or B0-B7 byte, a retained R8
   input, or M0's, M1's, or M2's retained records.
10. Any other finding that changes the plan's claim boundary or stop
    conditions.

## How M3 feeds M4

M4's claim ledger gets the I10 and I11 rows with "proof about the
abstract model" as their method and the new claim set as their artifact,
the per-hart-state row with the hart obligations, and the differential
agreement as the evidence that the MVP's offline checker computes what the
model defines, within the stated non-claim that it is not the proved
function. The three instances as fixtures and the generator are M4's
inputs for the researcher guide's "write a scenario" path.

## Status record

```text
mvp_m3_plan_status=accepted
mvp_m3_plan_target=c2c249f4c3d364590d2e505a4f6fb5e65456ff81
mvp_m3_plan_acceptance_instruction=accept-c2c249f4
mvp_m3_plan_acceptance_date=2026-10-28
mvp_m3_plan_first_candidate=9952e765-superseded
mvp_m3_plan_branch=beryllium/mvp-m3-plan
mvp_m3_plan_base=50b77c00
mvp_m3_governing_plan=93967fbac926b4fdfdfe636df4d07e8926b625b7
mvp_m3_security_model=0e3eec8b4fd74003f8cedbf2ca66871c31412624
mvp_m3_model_0_2=f8f89758;accepted-2026-07-24;23-obligations-unchanged
mvp_m3_m2_result=18d552bc4cf3a463bc4dc491e5e346989e5a521c
mvp_m3_m2_result_record=50b77c00
mvp_m3_open_questions=Q1-Q12-defaults
mvp_m3_limits=soft;stop-5-reevaluation-of-the-limit-not-the-work;human-direction-2026-10-28
mvp_m3_revision=additive;hart-class;I13-I16;instance-3;part-7-rows;own-exact-commit-before-model-work
mvp_m3_rocq_modules=Policy,Binding,PolicyClaims,PolicyAssumptions;T1-T5;H0-H3;generated-Instances.v-oracle
mvp_m3_c_modules=policy.h,policy.c,policy_test.c,policy-run.c,policy-report.c;generated-fixtures-no-runtime-parser;seal_with_policy-combined-identity
mvp_m3_differential=rocq-oracle-vs-model-checker-vs-mvp-policy-check;3-instances;>=64-seeded-mutations;binding-mutations-excluded
mvp_m3_lock=refresh-gcc-16.2.1-rocq-9.3-python3-role-after-accepted-gate-rerun;Q2
mvp_m3_accepted_model_files_edited=Makefile,tests/run-proofs.sh,tests/check-reports.mjs,tests/check-tools.sh,toolchain.conf,Containerfile,tests/generate-evidence.sh
mvp_m3_instance_1=full-policy-fixture;model-0.2-fixture-is-a-projection;part-7-sentence-erratum-recorded
mvp_m3_review=gpt-5.6-sol-2026-10-28-human-authorized;12-findings-incorporated;hook-edited-and-restored
mvp_m3_planning_measurements=proof-passes-under-rocq-9.3.0-in-18.5s;toolcheck-fails-gcc-16.1.1-vs-16.2.1;model-0.2-inventory-11-frames-no-code-frames
mvp_m3_board=none
mvp_m3_monitor_change=none
mvp_m3_work_packages=M3-1..M3-6
mvp_m3_implementation_authorization=M3-1-under-this-plan;M3-2..M3-6-after-revision-accepted
mvp_m3_implementation_branch=beryllium/mvp-m3
mvp_m3_implementation_status=M3-1-019cca64-accepted;M3-2-12e6fb06-0e05d338;M3-3-dadc6f63-cef9fad5;M3-4-83e850d0-6055b55a-6cfbc9ff;M3-5-d35813c7;M3-6-b0a0f352;gates-pass-at-d35813c7-clean-tree
mvp_m3_stops=stop-6-nodejs-remedy-A;stop-5-c-limit-6000;pass-criterion-4-instance-1-two-way;stop-5-rocq-limit-6000
mvp_m3_result=accepted-b0a0f352d7969a8f8cf28cf0d25b89fc372e70f2;parent-d35813c7;2026-10-28;instruction-accept-b0a0f352;record-mvp-m3-result-review-summary.md
mvp_m3_soft_limits=rocq-6000-at-3044;c-6000-at-3448;per-lane-combined-12000-at-6492-erratum-12;generator-driver-1500-at-1377;proof-180s-at-46s
mvp_m4_authorization=none
```
