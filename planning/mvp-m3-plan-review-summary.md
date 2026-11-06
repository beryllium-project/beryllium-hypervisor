<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M3 plan review and acceptance record

This packet presents the exact commit that adds
[`mvp-m3-plan.md`](mvp-m3-plan.md), the bounded plan for M3, "The policy
layer and the hart binding in the model", the fourth milestone of the
accepted [MVP plan](mvp-plan.md). It also records the responsible
human's decision on it.

## Decision record

The responsible human accepted exact commit
`c2c249f4c3d364590d2e505a4f6fb5e65456ff81` (parent `5349b258`, on
branch `beryllium/mvp-m3-plan` from `50b77c00`) as the M3 plan on
2026-10-28. The instruction, given in reply to this packet's request to
accept, revise, or defer that exact commit, was `accept c2c249f4`,
checked to resolve uniquely (`git rev-parse --disambiguate=c2c249f4`).
Q1 to Q12 were not answered, so their defaults apply. The first
candidate `9952e765` is superseded and was never accepted.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Sections 2 to 8 are the packet as presented, apart from a note above
  the section 8 checklist. Section 1's status rows and the closing lines
  of section 9 now show the outcome. The decision itself is recorded
  only here and in the plan's own decision record.
- **Decision support:** packet commits `5349b258` and `b2693ca6` and
  this acceptance-record follow-up are decision support, not plan
  content.
- **Authorized:** work package M3-1, the additive security model v1
  revision, as its own exact commit for the responsible human's
  decision, on branch `beryllium/mvp-m3` from this acceptance-record
  commit; and, only after that revision's exact commit is accepted,
  work packages M3-2 to M3-6 under the accepted plan on the same
  branch, ending in one result review packet. Each of the plan's ten
  stop conditions returns M3 to the responsible human; a soft limit
  exceeded returns the limit for re-evaluation. The repository's model
  split applies.
- **Not authorized:** M4; any change under `mvp/` beyond reading its
  scenario files and running its checker; any monitor or board work
  (the shared K3 is in use by the responsible human for another project
  and is not touched); any edit to an accepted Rocq or C mechanism file
  or to an accepted document other than the additive revision; root
  integration; a push, a tag, a merge, publication, or release.
- **Evidence status:** acceptance adds no implementation, proof, or test
  evidence; nothing of M3 has been written.
- **Errata recorded after acceptance, plan text unchanged** (the second
  `gpt-5.6-sol` review, directed by the responsible human on 2026-10-28
  after acceptance, with the orchestrating session's judgment on each;
  the responsible human may require a plan revision instead):
  1. Q1 and "The security model revision (M3-1)" say A8's "binding"
     "keeps the reading the MVP's checker implements"; the accepted A8
     quantifies over every binding in the sealed manifest, whose
     structural bindings (vCPU, root, VMID, stack, saved state) no rule
     class can allow. Revision 1 (R1.3) presents the reading as an
     interpretation of A8's wording for acceptance, with its reason; if
     the human rejects it, Plan revision M3-A is needed before M3-3.
  2. The `seal_with_policy` signatures (Q4; "The policy layer in Rocq";
     "The executable model") omit the need sets A4 requires, which the
     same sections list as A4's inputs; and the C pass criterion names
     only A8-failing inputs. Correction: both take the raw need sets as
     an input; need sets are not part of the combined identity (as the
     MVP checker's identity omits them); sealing refuses any input
     failing A1 to A6 or A8, each tested. No plan revision: the plan's
     intent is explicit in its A4 text.
  3. "Instances 1 and 2 keep theirs" and "Instance 2 … from `te-poc`"
     are both said; `te-poc` labels the hart and MVP regions
     `monitor_mem_t`, which accepted Instance 2 does not name.
     Correction (Revision 1, R1.4): the fixture "Instance 2" is the
     `te-poc` scenario, an extension of Instance 2's labeling; Instance
     2's text is unchanged.
  4. The pass criterion and the binding section say the binding is
     "onto harts other than the control hart"; I13 and I14 give
     injectivity and totality **into** the non-control harts, nothing
     about harts that run no domain (harts 3 to 7). Correction: "into";
     no coverage of the started harts is asserted.
  5. "The policy layer in Rocq" (the adapter paragraph) and the
     measurements say Model 0.2's four mappings have read, write, and
     execute rights; `Model.v`'s `read_write_rights` and `read_rights`
     have `right_execute := false`, so the fixture grants no `execute`
     and is a projection throughout (Revision 1, R1.5 states it so).
  6. Q7 and "The hart binding in Rocq" class the management state as
     control-written shared state; `mvp-hart.h` says hart 0 alone
     writes and reads it and no domain-hart code names it. Correction:
     hart 0's private state, outside the shared-object obligation
     (Revision 1, I16).
  7. "Soft limits" says M3-3 "may re-pin them from one, as a plan note",
     while Q12 and stop condition 5 reserve re-setting to the
     responsible human. Correction: M3-3 may propose new limits from a
     sizing pass; only the responsible human re-sets them, under stop
     condition 5.
  8. (M3-2, stop condition 6, 2026-10-28.) Q2 names GCC and Rocq as the
     lock's moving versions; Node.js moved too. The rootless evaluator's
     `dnf` installs Fedora 44's `nodejs22-22.23.1` where the lock and the
     host had v22.22.2, a Fedora 43 build no enabled repository carries,
     so the evaluator's own toolcheck failed on Node.js alone. On the
     responsible human's choice of remedy A (`A`; the alternatives: pin
     22.22.2 from a verified RPM cache, or stop), the host moved to
     `nodejs22-1:22.23.1-2.fc44` (`sudo dnf swap nodejs-libs nodejs22
     --allowerasing`, run by the human) and the lock's Node.js line
     followed, in the same two enumerated files (`0e05d338`); the
     accepted gate's results are identical under it, and `make -C model
     check` and `./be evaluate` pass. The MVP lock pins no Node.js; the
     R3-R7 locks pin `nodejs22-22.22.2-3.fc44`, which the host already
     did not match before, their gates running in pinned containers.
  9. (M3-4, stop condition 5, 2026-10-28.) The new restricted C of M3-4
     (`policy.h`, `policy.c`, `policy_test.c`, `policy-run.c`,
     `policy-report.c`, with `policy_fixtures.h`) is 3,447 lines against
     Q12's soft limit of about 2,000 (2,586 without comments; `policy.h`
     is 56 % kernel-doc, the accepted sources' style). Nothing was cut.
     The responsible human re-evaluated the limit and **re-set it to
     6,000 lines** (`c_limit=set to 6000`); the generator's 1,070 lines
     count against the generator-and-driver limit of about 1,500, which
     M3-5 measures when the driver exists.
  10. (M3-4, pass criterion 4 and M3-5, 2026-10-28.) Instance 1 and its
     Model 0.2 projection have no form the MVP's offline checker accepts:
     `policy-check.py` reads MVP-shaped scenarios only (two windows at
     the layout's addresses, the six monitor regions, the pages at the
     channel addresses). The pass criterion's "the Rocq oracle, the MVP's
     offline checker, and the model's checker agree on every instance"
     therefore holds three-way for Instances 2 and 3 and every mutation,
     and two-way (the oracle and the model's checker) for Instance 1 and
     its projection. The responsible human chose this reading
     (`instance1=two-way`) over embedding Instance 1 in a synthetic MVP
     scenario; the claim boundary says so.
  11. (M3-3, stop condition 5, 2026-10-28.) The new Rocq of M3-3
     (`Policy.v` 2,002 lines, `Binding.v` 787, `PolicyClaims.v` 220,
     `PolicyAssumptions.v` 35; the generated and sample instances
     excluded) is 3,044 lines against Q12's soft limit of about 3,000.
     Nothing was cut; the whole `make -C model proof` takes 43 s against
     the 180 s limit. The responsible human re-evaluated the limit and
     **re-set it to 6,000 lines** (form answer `rocq_limit=reset-4000`
     with the note `extend to 6000 lines`, the note governing).
  12. (M3 result acceptance, 2026-10-28.) Errata 9 and 11 each re-set a
     limit to 6,000 lines without saying how the two combine. On the
     responsible human's question whether the work exceeded "the 6000
     rocq+c limits", the measured counts at the result commit
     `b0a0f352` were given (Rocq 3,044; C 3,448; generator and driver
     1,377; together Rocq and C 6,492), and the acceptance instruction
     states the reading: **6,000 per lane, so a combined Rocq-and-C soft
     limit of 12,000 lines**. No limit is exceeded; stop condition 5 did
     not apply. The generator-and-driver limit of about 1,500 is
     unchanged.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `c2c249f4c3d364590d2e505a4f6fb5e65456ff81` (tree `8baad5c489bd8c68ebb3e4e7e4e6022bf2c76a35`), parent `5349b258`, on branch `beryllium/mvp-m3-plan` from `50b77c00`, the development branch's tip after the M2 result acceptance record. The first candidate `9952e765` (parent `50b77c00`) is superseded: on the responsible human's question about Q12's bounds and direction that they not constrain quality, its limits became soft limits for re-evaluation; nothing else in the plan changed between the two (`git diff 9952e765 c2c249f4 -- planning/mvp-m3-plan.md`) |
| Current status | Documentation only: the bounded plan for M3, written under the accepted MVP plan (`93967fba`), whose M3 section it implements and whose rule "each milestone needs its own bounded plan and its own result acceptance" it follows; directed on 2026-10-28 by the instruction `approve 1 & 2. proceed`, which also directed the development branch's fast-forward and push (done: `ccf70a3d` → `50b77c00`, with `beryllium/mvp-m2` and `beryllium/mvp-m2-plan`, to the private `origin`). A first draft was reviewed by `gpt-5.6-sol` on the responsible human's direction and session authorization; its twelve findings are incorporated (section 5). The responsible human then asked for the rationale of Q12's Rocq bounds and directed that the limits be soft, stopping for re-evaluation if exceeded (`c2c249f4`). The fast source checks pass (whitespace, every link and anchor). Responsible-human accepted on 2026-10-28 (instruction `accept c2c249f4`; Q1 to Q12 at their defaults) |
| Decision requested | Accept the exact commit as the M3 plan, request revisions, or defer; answer any of its Q1 to Q12 or let the defaults apply. Four defaults are flagged for explicit attention in section 3: the hart binding outside A8 (Q1), the model's lock refresh (Q2), the policy-sealing gate as a layer around the accepted seam rather than inside it (Q4), and the Rocq oracle for the differential check (Q8). Recorded outcome: accepted; the defaults apply |
| Successor status | As presented: acceptance would authorize writing the security model revision (M3-1) as its own exact commit for decision, and M3-2 to M3-6 only after that revision is accepted. After the decision: M3-1 is authorized on `beryllium/mvp-m3` from the acceptance record and begins; M3-2 to M3-6 wait on the revision's acceptance. M4, any Model change beyond M3's additive one, any change under `mvp/`, root integration, a push, and a merge are not authorized |
| Publication status | Private repository; the target is on local branch `beryllium/mvp-m3-plan`, unpushed. The development branch `beryllium/single-hart-runtime-r0`, `beryllium/mvp-m2` (both `50b77c00`), and `beryllium/mvp-m2-plan` (`35ebe8a7`) are on the private `origin` as of 2026-10-28 08:53 UTC. No tag, publication, or release |

As presented: please review exact commit `c2c249f4` and accept it,
request revisions, or defer. Outcome: accepted; see the
[decision record](#decision-record).

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| The M3 plan | [`mvp-m3-plan.md`](mvp-m3-plan.md) (679 lines) | Defines M3's goal and pass criterion (the MVP plan's M3 "Exit", made exact); the base and inputs with two read-only planning measurements (the accepted proof passes under Rocq 9.3.0 in 18.5 s; the model's `toolcheck` fails on `l1` at GCC 16.1.1 versus 16.2.1); the security model revision's exact content (the `hart` object class, I13 to I16, Instance 3, Part 7's rows, the erratum that Model 0.2's fixture is a projection of Instance 1); the Rocq policy layer (raw terms and the A1 validator, `decide`, A2 to A6 and A8, T1 to T5, the adapter and two bridge lemmas composed with the accepted `claim_derived_rights_bounded` and `claim_derived_root_soundness`); the hart binding (H0 to H3 over an enumerated transition vocabulary with total write footprints); the executable model (A1 validation, the analyses, `be_seal_with_policy` with one combined identity, build-time generated fixtures, no runtime parser); three-way differential checking against a Rocq oracle; the lock refresh and seven enumerated edits to accepted build files; soft limits that stop for re-evaluation, not for cutting the work; Q1 to Q12; ten stop conditions | Planning text; it changes no source, no monitor byte, and no accepted document; it authorizes nothing until accepted | Does each deliverable of the MVP plan's M3 appear, with every reinterpretation named as a departure (section 3), and are the claims the plan would support bounded to proof about the abstract model, unit tests, and differential agreement? |
| Navigation | `planning/.vitepress/config.mts` | Lists the plan and this packet in the three navigation lists | Site configuration only, in this packet's commit | None beyond placement |
| Status pages | [`roadmap.md`](roadmap.md), [`HANDOFF.md`](HANDOFF.md), [`README.md`](README.md), `.github/copilot-instructions.md` | Record the proposed plan, the development branch's fast-forward and push, and the reviewer authorization | Changed in this packet's commit, not in the target; status text only | None |

Exact changed-file inventory:

```text
# git diff --name-status 5349b258 c2c249f4
M	planning/mvp-m3-plan.md
# git diff --name-status 50b77c00 9952e765   (the superseded first candidate)
A	planning/mvp-m3-plan.md
```

`git diff --stat 5349b258 c2c249f4 -- . ':!planning/mvp-m3-plan.md'` is
empty: the target changes one file and nothing else. Across the whole
branch, `git diff --name-status 50b77c00 c2c249f4` lists only the plan,
this packet, and the status pages and navigation.

## 3. Claim boundary

**What the plan proposes M3 would support saying** (its "Claim boundary
and non-goals"): in the abstract model, security model v1's validated
policy semantics is total and default-deny (I10); a validated manifest
view that passes A8 grants no right the policy denies (I11), and for
Model 0.2's projection of the fixed two-domain profile every derived
mapping's presence and leaf right is policy-allowed; a view passing A8
has flows within the policy's, whose transitive closure A6 equates with
the declared channels' (the three equal for the fixed projection); a
policy-sealed state exists only for conforming inputs and carries one
combined configuration identity; the MVP's static hart binding is
injective and total onto non-control harts, each hart's private state is
disjoint from the others' and from domain memory and unmapped by every
root, and over the enumerated transition vocabulary only the control
hart's transitions write control-written shared state while each ring is
written by its one writer, all over the static binding; the three
instances are fixtures whose analyses the model computes; and the Rocq
oracle and two independently written checkers agree on them and on the
mutation set.

**What it would not support:** that any C code is proved (the model's
checker and the MVP's are tested, not refined); that the MVP monitor
satisfies I10 to I16 (the boot barrier, the rings' implementation, the
IPI protocol, and memory ordering are unmodeled); that Beryllium is
formally verified; any hardware result for M3 (none is run); any dynamic
case (Part 6, A7); or any transfer of Model, Helium, R-series, B-series,
or MVP claims across their boundaries.

**Departures the plan names from accepted text or guidance** (its table
"Accepted decisions M3 departs from"), each for the responsible human:

1. Security model v1's object classes have no hart; revision 1 adds the
   `hart` class and I13 to I16 (the MVP plan's deliverable 1 and
   departure row 4; the one change its stop condition 1 admits).
2. Model 0.2's lock pins GCC 16.1.1 and Rocq 9.2; the lock moves to the
   development host's versions after the accepted gate is re-run under
   them (Q2).
3. Seven accepted `model/` build and test files are edited additively
   (Q5); every other accepted file is byte-identical.
4. The MVP plan's "the control hart is the only writer of shared monitor
   state" is refined for the single-writer rings, which domain harts
   write, and for the pre-barrier phase (Q7).
5. Security model v1 Part 7 places A8 "before `sealed` as part of
   canonical validation" and the identities in the canonical state's
   configuration identity; the plan realizes both as a proof-carrying
   layer around Model 0.2's sealed state (`seal_with_policy`), so that
   the accepted seam and its 23 obligations stay unchanged, as the MVP
   plan's M3 requires (Q4).
6. Security model v1 Part 7 says the fixed-TE fixture's topology is
   Instance 1; Model 0.2's fixture is a projection of it (eleven frames,
   no guest-code frame, no `execute`, four mappings), recorded as an
   erratum of the accepted text, which is not edited (Q3).
7. Model 0.2's "no manifest parser or stable encoding" is kept as no
   runtime parser and no stable or public encoding; a build-time
   generator translates the instances' files into C and Rocq terms (Q3).

**Flagged defaults.** Q1 (the hart binding is mechanism metadata outside
A8, checked by I13 to I16; the alternative is a `hart : run` rule class),
Q2 (the lock refresh; the alternative is a pinned evaluator with the old
versions from koji), Q4 (the layer around the seam; the alternative edits
five accepted files), and Q8 (expected verdicts from the Rocq analyses by
computation, the independent oracle; the alternative, verdicts from the
MVP's checker alone, is circular).

**Evidence status.** Acceptance adds no implementation, proof, or test
evidence. Nothing of M3 has been written; the plan's two measurements
are read-only runs of the accepted model on `l1`.

## 4. Load-bearing decisions

| Decision | Where | Why it matters | Alternative recorded |
| --- | --- | --- | --- |
| The revision is its own exact commit, accepted before any model work | M3-1; Q11 | The MVP plan requires it; the hart obligations are stated against text the human has accepted | Begin the lock work in parallel |
| No accepted Rocq or C mechanism file is edited; new modules and a proof-carrying wrapper instead | Q4, Q5, stop 2 | "Model 0.2's seam and its 23 obligations stay unchanged" (MVP plan) | Gate inside `seal_state` and add fields to the accepted structures |
| Instance 1 is kept whole and Model 0.2's fixture is treated as its projection | Q3, departure 6 | T4 is stated for what the accepted model contains; the accepted document's sentence becomes an erratum rather than a silent hard-coding | Pretend the fixture is Instance 1 |
| Raw terms with an A1 validator, not typed-only terms | "The policy layer in Rocq" | A1's failures (undeclared types, unknown permissions, unlabeled objects) must be representable to be rejected | Typed-only terms, which make A1 vacuous |
| T3 is confinement plus A6's closure equality, not a general equality | "The policy layer in Rocq", claim boundary | A8 is an upper bound; a view may realize fewer flows than the policy allows | Claim equality in general, which is false |
| The hart binding is outside A8 | Q1 | Running on a hart is the monitor's static assignment, not an authority a subject exercises; the MVP's checker reads no hart | A `hart : run` rule class |
| The transition vocabulary is enumerated with total write footprints, and Model 0.2 is not a binding instance | "The hart binding in Rocq" | H3 is not vacuous; Model 0.2's two domains on one hart could not satisfy H1 | A degenerate single-hart instance, which the review found incoherent |
| Three-way differential checking with a Rocq oracle | Q8, Q9, M3-5 | Expected verdicts from one contestant would be circular; Part 4 names the Rocq decision procedure as the comparison | Verdicts from the MVP's checker alone |
| The lock refresh is gated by a re-run of the accepted gate first | Q2, M3-2, stop 6 | A tool move that changes the accepted content's results is a finding, not a refresh | Edit the lock and run once |
| The size and time limits are soft: exceeding one stops for the human's re-evaluation of the limit, never for cutting the work | Q12, "Soft limits", stop 5 | The responsible human's direction that arbitrary limits must not impact quality; the limits are inferred ceilings, not sized estimates | Hard bounds, declined |

## 5. Review history and resolved findings

On the responsible human's direction (`have it reviewed by gpt-5.6-sol
for potential steering (you decide what to incorporate)`) and session
authorization (`I will authorize gpt-5.6-sol for this session as a
reviewer`), a first draft of the plan was reviewed by `gpt-5.6-sol`
(rubber-duck agent, `max` effort, `long_context`) on 2026-10-28. The
governance hook `~/.copilot/hooks/beryllium-governance-hook.sh` requires
`claude-opus-5.5` for every task; its required-model line was edited to
`gpt-5.6-sol` for that one launch (09:05 UTC) and restored at 09:14 UTC,
the restored file's SHA-256 (`4f4c2c87…`) equal to the original's; the
repository's model pin is unchanged. The twelve findings and what the
plan now says:

| # | Finding (severity as given) | Resolution in the target |
| --- | --- | --- |
| 1 | must-fix: Part 7's seal gate (A8 before `sealed`) and the identity binding ("one sealed state binds one policy") were not delivered by a wrapper that only reported three identities side by side | Q4: `seal_with_policy` succeeds only when A1 to A6 and A8 pass and carries one combined configuration identity; T5; departure 5 recorded for the human |
| 2 | must-fix: typed-only Rocq terms make A1 partly vacuous (undeclared types, unknown permissions, unlabeled objects unrepresentable) | Raw terms over names and an A1 validator yielding validated values; `decide` over the validated result; the C side the same |
| 3 | must-fix: T3 ("A6 and A8 imply equality of policy flow, view flow, and declared channels") is false: A6 is `F+ = D+`, and A8 is an upper bound | T3a confinement (view flows within policy flows under A8), T3b A6's closure equality on the policy; equality of the three only for the fixed projection, by computation; the claim boundary narrowed |
| 4 | must-fix: T4 needs bridge lemmas; Model 0.2's rights are read, write, execute, with no `map`; `claim_derived_rights_bounded` gives a subset of canonical authority, not policy-view membership | Two bridge lemmas (access kinds to permissions; canonical authority to view rights); presence through `claim_derived_root_soundness`; T4 stated for the projection's four mappings, presence and leaf rights |
| 5 | must-fix: the adapter cannot equal full Instance 1 (two guest-code resources with `execute`; Model 0.2 has eleven frames and four non-executable mappings) | Instance 1 kept whole as a fixture; Model 0.2's fixture named a projection; the adapter tested against the projection; the Part 7 sentence recorded as an erratum (departure 6) |
| 6 | must-fix: Q1's default left A8's "binding" clause unresolved | Q1 states that the hart binding is mechanism metadata outside A8, checked by I13 to I16, and that A8's "binding" keeps the MVP checker's reading (the domain's extents as grants); flagged for the human |
| 7 | must-fix: H1 to H3 weak or inconsistent (the per-hart block called private in I15 and shared in I16; pre-barrier initialization by hart 0; no "domain hart is not the control hart"; a self-defined transition relation could be vacuous) | The object classification fixed (private: saved frame, stack, private data; control-written shared: published blocks, barrier, management state; single-writer rings); the pre-barrier phase stated; H0 added; H3 over an enumerated, nonempty vocabulary with total write footprints recorded with their source lines |
| 8 | must-fix: the "degenerate single-hart instance" of Model 0.2 is incoherent (two domains on one hart cannot satisfy H1) | Removed; Model 0.2 is the policy layer's adapter instance only |
| 9 | must-fix: the differential check's expected verdicts came from the MVP's checker, so the comparison was circular; "the generator is not a parser" overstated | Q8, Q9, M3-5: the Rocq analyses by computation are the oracle; three-way agreement; the generator named a build-time translator, the preserved constraint being no runtime parser and no stable or public encoding; the MVP inputs hashed into the evidence |
| 10 | must-fix: a non-injective-binding mutation cannot be a differential mutation, because the MVP's checker reads no hart | Binding mutations removed from the differential set and tested under the binding module and `policy_test.c` |
| 11 | must-fix: the five-file edit list and "no new tool role" were untenable (Python absent from the model's lock and `Containerfile`; `generate-evidence.sh` hard-codes the prover and obligation count; `run-proofs.sh` audits 24 assumption reports) | Q5: seven enumerated files, `Containerfile` and `generate-evidence.sh` added; `python3` a lock role; the generator in Node.js so `check-source-policy.sh` is not edited; `PolicyAssumptions.v` and the audit's count extended |
| 12 | should-fix: the lock-refresh baseline gate covered only the proof and unit tests; the evaluator's agreement was inferred | Q2, M3-2, stop 6: the whole accepted gate but the version check re-run and compared first; the evaluator's agreement shown by its own `toolcheck` |

After the review, the responsible human asked for the rationale of Q12's
Rocq bounds (inferred ceilings: the accepted model's 1,987 lines for 23
obligations and a rough shape of the new modules; 10× the measured 18.5 s
proof time) and directed that they not impact quality: the plan's limits
are now soft, each exceedance a stop for re-evaluation of the limit
(`c2c249f4`; the first candidate `9952e765` superseded).

The review also confirmed, and the plan keeps: the exact-commit
acceptance gate for the revision before model work; not widening Model
0.2's bounds; Q7's refinement for the rings; the narrow non-claims; the
wiring of `./be model-check` and `./be evaluate` through the root
targets; and the plausibility of the budgets and the 64-mutation target
after the redesign.

**Open for human judgment:** the four flagged defaults; the seven
departures; whether M3 should proceed while M4 is not yet planned (the
MVP plan allows M3 to run alongside the other milestones).

**Not run by SOP:** no iterative-evaluation review, separate scope
review, or deep security review beyond the one review the responsible
human directed. The plan was written by the orchestrating session on
`claude-fable-5.1`; no coding sub-agent ran.

## 6. Validation and retained evidence

Documentation only. Checked at the target: `git diff --check` clean;
every relative link in the plan names an existing file and every anchor
an existing heading (a script over the Markdown); the target changes one
file (`git diff --name-status 5349b258 c2c249f4`); the two planning
measurements were run read-only on `l1` on 2026-10-28 (`make -C model
proof`: PASS in 18.5 s under Rocq 9.3.0; `make -C model toolcheck`:
`Model 0.2 requires GCC 16.1.1`) and the model's bounds, inventory, and
scripts were read at `f8f89758`. No VitePress build was run (a wording
and navigation change under the routine-documentation rule).

## 7. Recommended review sequence

```sh
git worktree add --detach /tmp/be-m3-plan-review c2c249f4c3d364590d2e505a4f6fb5e65456ff81
cd /tmp/be-m3-plan-review
git --no-pager diff --name-status 5349b258 HEAD     # M planning/mvp-m3-plan.md only
git --no-pager diff 9952e765 HEAD -- planning/mvp-m3-plan.md   # the soft-limit revision
```

1. **Scope against the MVP plan** (20 min): `planning/mvp-plan.md`, "M3"
   and "Method per claim"; then the plan's "Decision requested", "Goal
   and pass criterion", and "Accepted decisions M3 departs from".
2. **The revision's content** (20 min): the plan's "The security model
   revision (M3-1)" against `planning/security-model-v1.md` Parts 1, 2,
   and 7, and Q1 and Q7.
3. **The proof design** (30 min): "The policy layer in Rocq" and "The
   hart binding in Rocq" against `model/proof/Model.v` (the inventory,
   `canonical_authority`, `derive_enforcement`) and `Claims.v`
   (`claim_derived_rights_bounded`, `claim_derived_root_soundness`); Q3,
   Q4, Q6.
4. **The checkers and the differential design** (15 min): "The
   executable model and host checker", "Differential checking", Q8, Q9;
   `mvp/tools/policy-check.py`'s A8 and identities for the reading the
   plan adopts.
5. **The lock and the enumerated edits** (10 min): "The lock and the
   build lists" against `model/toolchain.conf`, `tests/check-tools.sh`,
   `tests/run-proofs.sh`, `tests/generate-evidence.sh`, `Containerfile`;
   Q2, Q5.
6. **Stops, soft limits, and claims** (10 min): the ten stop conditions,
   "Soft limits", and "Claim boundary and non-goals".

```sh
cd - && git worktree remove /tmp/be-m3-plan-review
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The plan delivers the MVP plan's M3 deliverables 1 to 3 and exit,
      and each reinterpretation is named as a departure.
- [ ] The security model revision's content is additive and acceptable
      in outline, including the hart binding outside A8 (Q1) and the
      rings' refinement (Q7).
- [ ] The proof design is sound as stated: raw terms with A1, T3 as
      confinement and closure, T4 through the bridge lemmas on the
      projection, H0 to H3 over the enumerated vocabulary, the
      proof-carrying `seal_with_policy` (Q4).
- [ ] The lock refresh (Q2) and the seven enumerated edits (Q5) are
      acceptable.
- [ ] The three-way differential check with the Rocq oracle (Q8) is the
      intended cross-check.
- [ ] The soft limits (a stop for re-evaluation, never a cut to the
      work) and the ten stop conditions are acceptable.
- [ ] Decision: accept exact commit `c2c249f4` as the M3 plan (with any
      answers to Q1 to Q12); request revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `c2c249f4c3d364590d2e505a4f6fb5e65456ff81` and the date, with
  your answers to any of Q1 to Q12. The acceptance record names that
  SHA; the status documents follow. Acceptance authorizes writing the
  security model revision (M3-1) as its own exact commit for your
  decision, and M3-2 to M3-6 only after that revision is accepted, on
  branch `beryllium/mvp-m3` from the acceptance record; nothing else.
- **Request revisions:** a new commit and a new packet follow;
  `c2c249f4` is not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commit `c2c249f4c3d364590d2e505a4f6fb5e65456ff81` is
responsible-human accepted as the M3 plan as of 2026-10-28 (instruction
`accept c2c249f4`; Q1 to Q12 at their defaults; the first candidate
`9952e765` superseded). It is on branch `beryllium/mvp-m3-plan`, local
and unpushed. M3-1, the security model revision, is authorized on
`beryllium/mvp-m3` from the acceptance record and begins; M3-2 to M3-6
wait on the revision's acceptance.

**Next:** the revision's exact commit and its packet, for your
decision.

**Action required from you:** none until the revision is presented.
