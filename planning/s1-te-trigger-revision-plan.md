<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Plan: revise S1 and Model 0.1's TE trigger

## Decision record

The responsible human accepted this plan at exact commit
`07541c59426865ce8b1eef3c409913923cd5e64b` (parent
`65fc52e0b06fc60691669f75d44a1cc9356ac4c0`) on 2026-10-18. The
instruction, given in reply to the [review packet](project-review-2026-10-17-review-summary.md)'s
request to decide first on the project review and then on this plan, was
`approve 480d 07541`. The abbreviations were checked to resolve uniquely to
the project review at `480dab72de7a74f8b84c64c2fefee8190cb87b70` and to
this commit, in that order.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted; only this section
  and the acceptance fields in the status record below were added
  afterwards.
- **Authorized:** the three documentation work packages RP-1, RP-2, and
  RP-3 below, in order, each ending in its own exact commit, presented as
  ordered decisions in one review packet (Q6). No code, no S2 content
  beyond the scope statement RP-3 proposes, no change to any accepted
  R0-R7 or B0-B7 byte, no change to Model 0.1's Rocq model, no board run,
  and no push. Each [stop condition](#stop-conditions) returns the work to
  the responsible human.
- **Open questions:** none was answered, so the defaults apply: Q1 the
  Helium pin `1c9e526` as evidence only; Q2 the practice-confirmation rows
  condensed into one table; Q3 "a central, declarative policy in the Type
  Enforcement family"; Q4 the capability trigger's wording stands; Q5 S2
  chooses the specification language form; Q6 one packet with three
  ordered exact targets.
- **Not decided:** S2 and S3 stay unauthorized; the S1 draft `0fbca0fd`
  stays unaccepted until RP-1 replaces it by its own exact commit; Model
  0.1 stays accepted at its target, and M01-A becomes a revision only when
  its own exact commit is accepted.

## Status

Proposed for responsible-human review; not accepted. This is the second of
two ordered decisions: the [project review](project-review-2026-10-17.md)
comes first, and this plan rests on its findings F-01 to F-04. Accepting this
plan would authorize only the three documentation work packages below, each
ending in an exact commit for a separate decision. It authorizes no code, no
S2 content beyond the scope statement RP-3 proposes, no change to any
accepted R0-R7 or B0-B7 byte, and no change to Model 0.1's Rocq model.

On 2026-10-17 the responsible human chose the direction for the S1 revision
(`revise-adopt`): adopt a central TE-style declarative policy as the
specification against which the system's security properties are stated,
analyzed, and verified, with enforcement still derived from it. This plan
turns that choice into bounded work.

## Problem

The S1 draft at `0fbca0fd` argued from B2's K3 result that the Helium TE PoC
scenario does not show the TE trigger fires. The argument is wrong: the
result shows that one fixed configuration's denials can be expressed as
G-stage mappings, not how the system's security properties are specified,
analyzed, or verified. The error is inherited from Model 0.1's "TE trigger",
which defines TE as an extra runtime denial, and from the pathfinder
comparison, which priced TE by lines. Meanwhile the implementation plan
expects a static policy that is "deterministic, analyzable, measurable, and
attestable", names FLASK as the key precedent, lists policy proof targets,
and planned a pipeline from policy source to the Rocq configuration. No step
owns that layer, and S2 as defined would not produce it.

## Approach

Three documentation-only work packages, in order, each a separate exact
commit:

| Package | Deliverable | Replaces or changes |
| --- | --- | --- |
| RP-1 | A revised S1 synthesis | Replaces the unaccepted `0fbca0fd`; `planning/he-to-be-synthesis.md` on the S1 branch |
| RP-2 | Model 0.1 plan revision M01-A: the TE trigger rewritten | A narrow text revision of [`architecture-model-0.1.md`](architecture-model-0.1.md), "TE trigger"; the Rocq model and the accepted exact target are untouched |
| RP-3 | A revised S2 scope statement | The S2 rows and paragraphs in the [roadmap](roadmap.md), the [implementation plan](implementation-plan.md), the [orientation guide](project-orientation.md), the [planning README](README.md), and the [glossary](glossary.md) |

RP-1 and RP-2 may be drafted in parallel; RP-3 follows RP-2, because it
depends on the revised trigger wording. One review packet presents all three
exact targets as ordered decisions.

## RP-1: revise S1

Base: the S1 branch at `2256101c`; the result replaces `0fbca0fd` and keeps
its inputs, including the Helium pin `1c9e526` (see Q1).

Changes:

1. Remove the E03 argument wherever it appears: the "Findings" bullet that
   says the scenario "does not show that the TE trigger fires"; the basis of
   rows H02, H08, and H55; and S2 hand-off item 1. E03 stays in the evidence
   table as what it is: two denials expressed by derived mappings under
   ownership and an explicit read-only channel.
2. Add one row, classified **Adopt**: a central, declarative policy in the
   Type Enforcement family as the specification against which the system's
   security properties are stated, analyzed, and verified, with enforcement
   derived from it, so that the canonical manifest is checked against the
   policy at validation and the derived roots follow from the manifest. Its
   basis cites the implementation plan (L401, L416-L417, L734, L740,
   L931-L940), the research inputs (extensional versus intensional policy;
   seL4's proofs relative to configured authority; the FLASK split), and
   Helium's own definition of TE and its questions for "the next Be stage".
   Its hand-off names RP-2 and RP-3.
3. Reclassify H02 from Adopt to **Adapt**: keep ownership plus explicit
   channels as the enforcement baseline and keep the composition rule; note
   that the TE trigger is being revised by RP-2 to separate specification
   from runtime check.
4. Reword H08 as the **runtime** TE check, meaning a policy decision
   consulted on an access path beyond the derived mappings, and keep it
   **Defer** to S2 under the revised trigger.
5. Reclassify H10 from Reject to **Defer**: do not transfer Helium's
   representation, but policy compilation, lookup, and analysis belong to
   S2, and dynamic update and caching stay conditional.
6. Reword H56 so that "TE should not lead the initial core" is recorded as
   the comparison's precedent reading, not as a lesson S1 carries forward.
7. Reword "Purpose and boundary" and "Non-claims": S1 recommends a
   specification role for a TE-style policy and selects no runtime
   mechanism; the capability trigger and the runtime-check trigger stay with
   S2.
8. Update the summary counts and the status block; add a status line that
   the revision replaces `0fbca0fd` under the 2026-10-17 critique and the
   `revise-adopt` answer.
9. Optionally (Q2), move the rows that only confirm existing practice (H25,
   H28, H30, H33, H35, H37, H39, H44, H45, H47-H49, H52, H53) into one
   compact table.

Exit: one commit on the S1 branch, with the fast source checks passing, and
the old target recorded as superseded and unaccepted in the packet.

## RP-2: Model 0.1 plan revision M01-A

Base: the development branch. Scope: the "TE trigger" section of
[`architecture-model-0.1.md`](architecture-model-0.1.md) (L266-L282 at
`2256101c`) and a decision-record note. Nothing else in Model 0.1 changes;
the Rocq model under `model/` is untouched, and the accepted exact target
stays accepted as history. This follows the project's narrow-plan-revision
pattern (R6-A, R6-B, R7-A, R8-A, R8-C).

The revised section separates two things the current text conflates:

- **TE as specification.** The system's security policy is stated as a
  central, declarative policy over types or labels, object classes,
  permissions, and rules, with deterministic and total semantics. The
  canonical manifest must be shown to conform to it, and the policy proof
  targets of the implementation plan apply to it. This is not trigger-gated:
  it is how properties are specified, and S2 produces it (RP-3). Enforcement
  stays derived, so no runtime decision function is implied by this part.
- **TE as a runtime check.** A policy decision consulted on an access path
  beyond the derived mappings. This stays trigger-gated with the existing
  two-case observability condition, which is a test of composition with
  designation, not a test of whether a policy is needed.
- **The dynamic case.** Once an untrusted management domain creates domains
  or channels at runtime, the policy is what bounds what it may create: the
  "immutable authority ceiling" the implementation plan already describes
  (L890-L901). The revised text says so, and routes the design to S2 and the
  first protected-domain milestone.

The revision also notes, without changing it, that the capability trigger's
wording stands (Q4), and that the comparison's "Cost separation" is a
measurement of mechanism lines, not of the specification role.

Exit: one commit with a decision-neutral review packet, following the pattern
of the earlier plan revisions; acceptance by exact commit.

## RP-3: the S2 scope statement

Base: the development branch, after RP-2 is accepted. Scope: the sentences
that define S2 in the roadmap's "Planned sequence", the implementation
plan's section 2.16 and "Immediate decision gates", the orientation guide,
the planning README's decision gates, and the glossary's S2 entry. RP-3
changes the definition of S2; it does not write S2.

The proposed definition: S2, security model v1, produces one accepted
document containing:

1. objects, invariants, the threat model, and the trusted computing base, as
   now;
2. the policy specification: a declarative policy in the Type Enforcement
   family (types or labels, object classes, permissions, rules) with
   deterministic and total semantics, default deny, and explicit conflict
   resolution;
3. the analyses the policy proof targets name: unreachable, contradictory,
   over-broad, and non-revocable authority; information flow modulo the
   declared channels; and authority non-amplification;
4. the relation from the policy to the canonical manifest (compile or
   validate), restoring the implementation plan's pipeline as a goal, with
   the Rocq configuration as its intended consumer;
5. the capability trigger and the runtime-check trigger, evaluated against
   the platform's use cases under the revised M01-A wording;
6. the authority ceiling for the dynamic management case; and
7. which of Model 0.2's seam, fixtures, or proofs change, if any.

The form of the specification language (Rocq-embedded, a typed intermediate
representation, or a Cedar-like surface language compiled offline) is S2's
choice, not RP-3's (Q5). S2 itself stays separately authorized.

Exit: one commit; the fast source checks pass; the roadmap and orientation
reflect the revised definition without claiming S2 has started.

## Stop conditions

Each returns the work to the responsible human:

1. RP-2 would need to change Model 0.1's Rocq model, Model 0.2, or any
   accepted R0-R7 or B0-B7 byte.
2. Any package would select a runtime mechanism, a policy language, or a
   protected service, rather than a specification role.
3. RP-3 would start writing S2 content rather than its scope.
4. A disagreement about the Helium pin that Q1 does not settle.
5. The fast source checks fail for a reason that needs a change outside the
   three scopes.

## Open questions and defaults

The defaults apply unless the responsible human answers otherwise.

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | Which Helium commit does the revised S1 read? | `1c9e526`, evidence only, as the draft | `f928aac5`, the `for-review` ref; rows citing release-line content are narrowed |
| Q2 | Condense the practice-confirmation rows? | Yes, into one compact table | Keep all 58 rows as separate entries |
| Q3 | How is the specification policy named? | "a central, declarative policy in the Type Enforcement family" | "mandatory access-control policy", or "TE policy" without qualification |
| Q4 | Does M01-A also revise the capability trigger? | No; its wording stands | Revise it in the same package |
| Q5 | Does RP-3 name the specification language form? | No; S2 chooses | Name a default form in RP-3 |
| Q6 | One packet for all three targets, or one each? | One packet, three ordered exact targets | One packet per target |

## Non-claims

- This plan is a proposal. It accepts, authorizes, and selects nothing by
  itself.
- Accepting it would authorize documentation work only; it would not
  authorize S2, S3, any implementation, any board run, or any push.
- It does not transfer any Helium result, select a runtime mechanism, or
  change any accepted exact target. Model 0.1 stays accepted at its target;
  M01-A, if accepted, is a later revision recorded against it.
- It does not assert that the TE trigger as written was wrong for the fixed
  synthetic profile it governed; it asserts that the trigger does not cover
  the specification role, which S2 needs.

## Status record

```text
revision_plan_status=accepted
revision_plan_target=07541c59426865ce8b1eef3c409913923cd5e64b
revision_plan_acceptance_instruction=approve-480d-07541
revision_plan_acceptance_date=2026-10-18
revision_plan_date=2026-10-17
revision_plan_depends_on=project-review-2026-10-17.md
revision_plan_direction=revise-adopt
revision_plan_packages=RP-1,RP-2,RP-3
rp1_replaces=0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef
rp2_scope=architecture-model-0.1.md-te-trigger-text-only
rp2_rocq_model_change=none
rp3_scope=s2-definition-text-only
s2_authorization=none
s3_authorization=none
```
