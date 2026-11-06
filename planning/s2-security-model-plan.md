<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Plan: S2, security model v1

## Decision record

The responsible human accepted this plan at exact commit
`5ce7827f9c2ffc6e0f88568692ab238e5feca49f` (parent
`0eb37570f9cb901ef994cc10aef8c7890c6134e9`) on 2026-10-19. The
instruction, given in reply to the
[review packet](s2-security-model-plan-review-summary.md)'s request to
accept, revise, or defer that exact commit, was `accept 5ce782`, which
resolves uniquely to that commit.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted; only this section
  and the acceptance fields in the status record below were added
  afterwards.
- **Authorized:** the documentation work packages S2-1 to S2-7 below, in
  order, ending in one exact commit of one document,
  `planning/security-model-v1.md`, on branch `beryllium/s2-security-model`,
  presented in a decision-neutral packet for a separate acceptance
  decision. No code, no change under `model/`, no change to any accepted
  R0-R7 or B0-B7 byte, no board run, no push, and no S3 work. Each
  [stop condition](#stop-conditions) returns S2 to the responsible human.
- **Open questions:** Q1 was answered on 2026-10-19 with `Let's go with
  (A)`, which selects the default: a small declarative notation defined in
  full in the document, with no parser or tool. Q2 to Q7 were not
  answered, so their defaults apply: worked instances for the fixed
  two-domain profile and the expected first MVP milestone (Q2); three use
  cases for the triggers (Q3); analyses defined and Model 0.2 changes
  inventoried, neither implemented (Q4); no independent review before the
  packet (Q5); Helium at `1c9e526` as evidence only (Q6); and the
  authority report schema defined in S2-4 (Q7).
- **Not decided:** the security model itself, which becomes accepted only
  when its own exact commit is; S3; any runtime mechanism, protected
  service, or specification tool; any push.

## Status

Proposed for responsible-human review; not accepted. The responsible human
directed this plan on 2026-10-18 with the instruction
`then proceed with S2 plan`, after accepting the revised S1 synthesis
(`fd670dcd`), Model 0.1 plan revision M01-A (`95ef0f6c`), and the revised
S2 definition (`1ac7080f`) with `I accept RP-1 RP-2 RP-3`. Drafting this
plan is the only thing that instruction authorized. Accepting this plan
would authorize the documentation work packages S2-1 to S2-7 below, ending
in one exact commit of one document, `planning/security-model-v1.md`, for a
separate acceptance decision. It would authorize no code, no change under
`model/`, no change to any accepted R0-R7 or B0-B7 byte, no board run, no
push, and no S3 work.

## Decision requested

Accept this plan at its exact commit, request revisions, or defer. The
[open questions](#open-questions-and-defaults) carry defaults that apply
unless answered otherwise.

## Goal

S2 produces security model v1: the one document that states what the
system's security properties are, in a form that can be analyzed and later
verified, and that S3 (the MVP plan) and the first MVP milestone build on.
Its definition is the accepted RP-3 text
([roadmap](roadmap.md#planned-sequence), "S2. Security model v1"): one
document containing

1. objects, invariants, the threat model, and the trusted computing base;
2. the policy specification: a central, declarative policy in the Type
   Enforcement family (types or labels, object classes, permissions, rules)
   with deterministic and total semantics, default deny, and explicit
   conflict resolution;
3. the analyses the implementation plan's policy proof targets name:
   unreachable, contradictory, over-broad, and non-revocable authority;
   information flow modulo the declared channels; and authority
   non-amplification;
4. the relation from the policy to the canonical manifest (compile or
   validate), restoring the implementation plan's offline pipeline as a
   goal, with the Rocq configuration as its intended consumer;
5. the capability trigger and the runtime-check trigger, evaluated against
   the platform's use cases under the M01-A wording;
6. the authority ceiling for the dynamic management case; and
7. which of Model 0.2's seam, fixtures, or proofs change, if any.

The pass criterion is that each of the seven parts is present, internally
consistent, consistent with the accepted inputs below, and bounded by the
[non-goals](#claim-boundary-and-non-goals), and that the fast source checks
pass at the exact commit.

## Base and inputs

Base: the development branch `beryllium/single-hart-runtime-r0` at
`0eb37570`, which holds every accepted input below. Work proceeds on branch
`beryllium/s2-security-model` from that commit.

| Input | Exact identity | Use |
| --- | --- | --- |
| S2 definition | RP-3 at `1ac7080f` (accepted 2026-10-18) | The seven parts above; S2 fills them and does not redefine them |
| Model 0.1 plan revision M01-A | `95ef0f6c` (accepted 2026-10-18), [Model 0.1](architecture-model-0.1.md), "TE trigger" | TE as specification (not trigger-gated), TE as a runtime check (the two-case trigger), and the dynamic case; the capability trigger's wording stands |
| S1 synthesis | `fd670dcd` (accepted 2026-10-18), [`he-to-be-synthesis.md`](he-to-be-synthesis.md) | Row H59 and the S2 hand-off items 1-8; every row S2 revisits is named |
| Project review | `480dab72` (accepted 2026-10-18), [`project-review-2026-10-17.md`](project-review-2026-10-17.md) | Part 2 (what the founding documents expect), F-01, F-02, F-04; the stale list is not S2's |
| Implementation plan | [`implementation-plan.md`](implementation-plan.md) at the base: the system-description split and pipeline (L378-L421), threat model v0 (L481-L532), the deferred anchor use case (L617-L639), the FLASK and analyzable-policy expectations (L734-L742), the authority ceiling (L890-L901), the proof targets (L918-L948), and the decision gate (L950-L979) | The properties the specification must be able to state; the pipeline S2 restores as a goal; the gate items S2 updates |
| Model 0.2 | [`architecture-model-0.2.md`](architecture-model-0.2.md) and its [evidence](architecture-model-0.2-evidence.md), accepted 2026-07-24 | The seam (proposal, canonical validation, sealed state, derived enforcement), the 23 obligations, the fixtures; S2 states where the policy sits against it |
| Research inputs | [capability policy](capability-policy-architecture.md), [isolation engine](isolation-engine-policy-research.md), [supervisory policy](supervisory-security-policy.md), the [2026-07-20 session analysis](session-analysis-isolation-engine-2026-07-20.md), [CHERI alignment](cheri-alignment.md) | Extensional versus intensional policy; the FLASK split; the composition test; the boot-time policy ceiling; the CHERI mapping gate item |
| K3 evidence | The B0-B7 records at the base | What exists and what is unexercised (S1's E01-E12); diagnostic bring-up evidence only |
| Helium | `../helium-te-poc` at `1c9e52693abe0072ac9b8ce4e0a3ecb5f8bb9489`, read as evidence only | Helium's TE definition and its policy questions (S1 rows H06, H07, H59); no Helium result transfers (Q6) |

## Work packages

Each package is a section of `planning/security-model-v1.md`. They are
written in order; S2-2 to S2-4 may be drafted together because each
constrains the others.

### S2-1. Objects, invariants, threat model, and TCB

- Enumerate the object classes the model governs: domains (management and
  protected), memory regions (private, shared, monitor-owned), vCPU and
  saved architectural state, G-stage roots, channels (directional shared
  memory, and notifications where the platform supports them), timers and
  the interrupt sources the B-series exercised, the manifest, the policy
  itself, and measurements as a named but unimplemented asset.
- State the invariants in prose with a reference to the Model 0.1 and 0.2
  obligations that already cover their fixed-instance form, and name each
  invariant that has no obligation yet.
- Restate threat model v0 for the K3 configuration: Linux as an untrusted
  payload today and the untrusted management domain later; the K3 trusted
  inputs (OpenSBI 1.6, SRST behavior, `hedeleg` WARL, Sstc, the timebase);
  and the deferred items unchanged.
- Give the TCB as a list with an evidence class per entry, following the
  B-series "trusted or assumed" tables.

### S2-2. The policy specification

- Define the policy's elements: types (or labels) on subjects and objects,
  object classes, permissions per class, and rules of the form
  `allow source_type target_type : class { permissions }`, with the
  default-deny rule that anything not allowed is denied.
- Define the semantics: a total function from (source type, target type,
  class, permission) to allow or deny; determinism; explicit conflict
  resolution (there are no conflicting rules under pure allow rules; if
  the specification admits any other rule form, S2 states the resolution
  order).
- Keep types as policy identities, not authority: a type names which rules
  apply; the manifest and the derived mappings carry the authority (S1
  H03, H59).
- State the policy for two instances as worked examples (Q2): the fixed
  two-domain profile that R0-R7 and B0-B4 run, and the expected first MVP
  milestone, two Linux guests sharing one page with a writer and a reader.
- Choose a notation that the document defines in full, in text, without a
  parser or tool (Q1). The form of the production specification language
  is recorded as a decision S2 makes in the document, with its
  alternatives.

### S2-3. The analyses

For each analysis the policy proof targets name, define it over the
specification of S2-2 as a decidable check on a finite policy and manifest,
state its inputs, and state what a failure means:

- unreachable authority: a rule no subject type can exercise under the
  manifest;
- contradictory authority: rules whose combined effect the resolution
  order does not define, or an allow that the invariants forbid;
- over-broad authority: an allow whose permissions exceed what the use
  case needs, stated as a check against a declared need set per type pair;
- non-revocable authority: an allow with no revocation path where the
  threat model requires one (shared writable memory);
- information flow modulo the declared channels: the flow relation the
  allows induce between types, and the check that it equals the declared
  channel set, so that any other flow is a specification error;
- authority non-amplification: no delegation or management operation
  yields a right not already allowed to the delegating type.

S2 defines the analyses; it does not implement them (Q4). It states which
of them Model 0.2's validator already performs in extensional form on the
fixed instance, and which have no implementation.

### S2-4. The policy-to-manifest relation and the pipeline

- Decide compile or validate: whether the canonical manifest is generated
  from the policy plus the platform description, or written separately and
  validated against the policy. S2 records the choice, the alternative,
  and the reason.
- Restore the implementation plan's offline pipeline (L401) as a goal:
  policy source and platform description to the canonical manifest, the
  Rocq configuration, the authority graph, and the audit report, with the
  Rocq configuration as the intended consumer and the existing Model 0.2
  seam as the point where the manifest enters.
- Define the authority report schema derived from the sealed manifest (S1
  hand-off item 8, H29) as the pipeline's audit output (Q7).
- State the attestation-binding obligation (policy source identity,
  compiled artifact, active generation) as a later milestone's, with
  measurement named as unimplemented.

### S2-5. The triggers

Evaluate, under M01-A's wording, against three use cases (Q3): the fixed
two-domain profile; the expected first MVP milestone; and the dynamic
management case, in which an untrusted management domain creates
protected domains and channels at run time.

- The capability trigger: does any use case require runtime designation
  plus delegation, attenuation, holder transfer, or revocation that static
  owner/channel records cannot express without ambient authority or
  per-caller special cases?
- The runtime-check trigger: does any use case contain an ownership-valid
  or capability-valid operation that must still be denied at run time by a
  rule the derived mappings do not express, with the two-case
  observability condition met?

Record each answer as fires, does not fire, or undecidable without a later
input, with the evidence. A result of "fires" selects nothing: it records
that a later plan must design the mechanism.

### S2-6. The dynamic authority ceiling

Define the ceiling for the dynamic management case as the implementation
plan states it (L890-L901): the policy and initial manifest bound every
domain, region, channel, and right that management may create; every
dynamic grant is a subset of authority the policy delegates to management;
anything outside fails closed; and the strict profile permits management
only to narrow or revoke. State which parts of the ceiling the policy of
S2-2 expresses directly and which need a management-request vocabulary
that a later plan designs.

### S2-7. Model 0.2 change inventory

List each Model 0.2 element (seam phase, required state, fixture,
obligation) that the specification would change, extend, or leave as is,
and whether the change is to the abstract model, the C validator, the Rocq
development, or the fixtures. S2 identifies the changes; it does not make
them (Q4). If the inventory is empty, say so.

## The decision-gate update

The implementation plan's decision gate (L970-L979) requires the selected
use case and trigger result to update seven items before a policy
architecture or protected-service plan is approved. S2 covers them as
follows: core object representation (S2-1), manifest semantics (S2-4),
formal properties (S2-2, S2-3), and the authority ceiling's bearing on
revocation (S2-6); it states the authorization API, the audit schema, and
the CHERI mapping as items a later plan designs, with S2's inputs to each
named. The protected-service selection stays outside S2 unless the
responsible human directs otherwise (stop condition 3).

## Claim boundary and non-goals

S2 supports saying: Beryllium has a stated security model v1, with a
declarative policy specification, defined analyses, a stated relation to
the canonical manifest, trigger evaluations, and a stated dynamic ceiling,
for the responsible human to accept.

S2 does not:

- implement anything: no code, no tool, no parser, no checker, no Rocq or C
  change under `model/`, and no change to any accepted R0-R7 or B0-B7 byte;
- select a runtime mechanism (a runtime TE check or software
  capabilities), a protected service, or an SBI or firmware boundary;
- select the production specification language's tooling; it records the
  language form it chose for the document and the alternatives;
- prove anything, run anything, or transfer any Helium, Model, R-series, or
  B-series result;
- claim that the fixed-instance obligations of Models 0.1 and 0.2 or R7's
  bounded proof establish the new model's properties; or
- authorize S3, the first MVP milestone, or any implementation.

## Stop conditions

Each returns S2 to the responsible human:

1. A property of threat model v0 that the policy of S2-2 cannot express in
   any form S2 can define without tooling.
2. A need to change any accepted byte, Model 0.2, or anything under
   `model/` before the specification can be stated.
3. A need to select a protected service, a runtime mechanism, or a
   specification tool to complete a part.
4. A disagreement with the accepted S1 rows or the M01-A text that S2
   cannot resolve by citing them as they stand; the remedy is a plan
   revision, not a silent reinterpretation.
5. The fast source checks fail for a reason that needs a change outside
   `planning/security-model-v1.md`, its navigation entry, and the status
   pages.

## Open questions and defaults

The defaults apply unless the responsible human answers otherwise.

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | How is the policy written in the document? | A small declarative notation defined in full in the document (abstract syntax and semantics in text), with no parser or tool | Rocq definitions embedded in the document, or a Cedar-like surface syntax; either is recorded as the production form only if S2 so decides |
| Q2 | Does S2 include worked instances? | Yes: the fixed two-domain profile and the expected first MVP milestone, each written in the notation | Definitions only |
| Q3 | Which use cases do the triggers face? | The fixed two-domain profile, the expected first MVP milestone, and the dynamic management case | Add the anchor protected-research-domain use case as a fourth, at the human's direction |
| Q4 | Does S2 implement any analysis or Model 0.2 change? | No: S2 defines the analyses and inventories the Model 0.2 changes; implementation is a later plan | S2 includes an executable check of the analyses on the two instances, which would need a separate authorization |
| Q5 | Does S2 get an independent review before its packet? | No, per the 2026-10-06 SOP | A different-model review of the exact S2 commit, as the project review's option 5 proposes for specification-bearing steps |
| Q6 | Which Helium commit does S2 read, if any? | `1c9e526`, evidence only, as S1 did | `f928aac5`, the `for-review` ref |
| Q7 | Does S2 define the authority report schema? | Yes, as the pipeline's audit output in S2-4 | Defer it to S3 |

## Exit

One commit on `beryllium/s2-security-model` adding
`planning/security-model-v1.md`, its navigation entry, and the status-page
updates, with the fast source checks passing, presented in a
decision-neutral review packet for acceptance by exact commit. Accepting
that document completes S2; it does not authorize S3, which needs its own
plan.

## Status record

```text
s2_plan_status=accepted
s2_plan_target=5ce7827f9c2ffc6e0f88568692ab238e5feca49f
s2_plan_acceptance_instruction=accept-5ce782
s2_plan_acceptance_date=2026-10-19
s2_plan_q1_answer=A-notation-defined-in-document
s2_plan_q2_to_q7=defaults
s2_plan_date=2026-10-18
s2_plan_direction_instruction=then-proceed-with-S2-plan
s2_definition=1ac7080f3375dfbfb8358706db767a8a89678a78
s2_inputs_s1=fd670dcd54ff4f2c66349d377be914698b9dda3b
s2_inputs_m01a=95ef0f6c0fc1fe457e93b7d34b48cde5a411e8ab
s2_inputs_review=480dab72de7a74f8b84c64c2fefee8190cb87b70
s2_base=0eb37570f9cb901ef994cc10aef8c7890c6134e9
s2_packages=S2-1,S2-2,S2-3,S2-4,S2-5,S2-6,S2-7
s2_deliverable=planning/security-model-v1.md
s2_code_change=none
s2_model_change=none
s2_authorization=authorized-by-this-plan-documentation-only
s2_document_status=not-started
s3_authorization=none
```
