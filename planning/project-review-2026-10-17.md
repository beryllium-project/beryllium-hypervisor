<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Project review, 2026-10-17: the S1 draft and the project against its founding goals

## Decision record

The responsible human accepted this review at exact commit
`480dab72de7a74f8b84c64c2fefee8190cb87b70` (parent
`91d2c108c0326a77619c91b88a4e1c966aeb06bc`) on 2026-10-18. The instruction,
given in reply to the [review packet](project-review-2026-10-17-review-summary.md)'s
request to decide first on this review and then on the companion revision
plan, was `approve 480d 07541`. The abbreviations were checked to resolve
uniquely to this commit and to the revision plan at
`07541c59426865ce8b1eef3c409913923cd5e64b`, in that order. The first
candidate of this review, `65fc52e0`, is superseded and unaccepted.

- **Scope:** acceptance covers exactly the review text at that commit: the
  eighteen findings and their severities, the account of the second
  research run, and the non-claims stand as the project's recorded review.
  Everything after this section is the review as accepted; only this
  section and the acceptance fields in the status record below were added
  afterwards.
- **What it decides:** that the findings are accepted as the record. The
  eight options remain options. Option 1's first part is carried out by the
  separate acceptance of the
  [revision plan](s1-te-trigger-revision-plan.md); the other options are
  not selected by this acceptance and need their own direction.
- **Not decided:** S2 and S3 stay unauthorized; the S1 draft `0fbca0fd`
  stays unaccepted; no accepted R0-R7 or B0-B7 target changes; nothing is
  pushed.

## Status

Proposed for responsible-human review; not accepted. This review records
findings and options. It accepts nothing, authorizes nothing, and changes no
other document. Every decision it names belongs to the responsible human.

The responsible human requested it on 2026-10-17, after finding an error in
the S1 draft: the draft treated Type Enforcement (TE) only as a runtime
denial mechanism, when TE is a centrally administered, declarative policy, and
a system's security properties cannot be specified, analyzed, or verified
without such a policy. The request was to review that draft and its critique,
then the project as a whole against its founding design and goals.

**Model note.** The owner session that produced this review ran on
`claude-fable-5.1`, a deliberate choice by the responsible human; the
project's pinned model is `claude-opus-5.5`, and the 2026-10-06 process SOP
avoids different-model reviews as standard practice. The project's governance
hook (`PMD-20261006-001`) denied every non-pinned model for subagents, so the
four read-only research agents first ran on `claude-opus-5.5`, on 2026-10-17,
and nothing was changed to work around the hook. On 2026-10-18 the
responsible human directed that the pinning be overridden for this session
and the four agents re-run on `claude-fable-5.1`. For that run the hook's
required model was edited to `claude-fable-5.1` with the human's consent,
and it was restored to `claude-opus-5.5` from a backup when the run ended;
no other governance rule changed. Each second-run agent formed its own
reading of the same inputs first and then compared it with this review. The
corrections that followed are listed under "Second run (2026-10-18)" below
and were applied in place; the first run's statements that both runs support
stand unchanged.

## Scope and method

Angles, chosen by the responsible human: the security model and policy
direction; progress against the founding goals and the S1-S3 sequence;
process and documentation weight; the assurance strategy; and engineering
debt. Excluded: the Linux-upstream licensing question, and this session's
conduct beyond the S1 draft.

Inputs, all read at Beryllium commit `2256101c` (the S1 packet commit over
S1 target `0fbca0fd`), with Helium at `1c9e526` read as evidence only:

- the founding documents: the [implementation plan](implementation-plan.md),
  the [research synthesis](research-synthesis.md), the policy research
  ([isolation engine](isolation-engine-policy-research.md),
  [capability policy](capability-policy-architecture.md),
  [supervisory policy](supervisory-security-policy.md), and the
  [2026-07-20 session analysis](session-analysis-isolation-engine-2026-07-20.md)),
  the [open-tooling policy](open-tooling.md), the
  [CHERI alignment](cheri-alignment.md), the
  [hardware inventory](riscv-security-hardware.md), and the sidebars;
- the decision chain: the five pathfinder plans and evidence records, the
  [post-pathfinder comparison](pathfinder-comparison.md), Models
  [0.1](architecture-model-0.1.md) and [0.2](architecture-model-0.2.md) with
  their evidence, the [runtime plan](single-hart-runtime-plan.md), the R0-R7
  plans and records, and the R8 and KVM0 records as history;
- the current position: the B0-B7 plans and records, the
  [roadmap](roadmap.md), the [handoff](HANDOFF.md), the
  [orientation guide](project-orientation.md), and the
  [glossary](glossary.md);
- the S1 draft ([`he-to-be-synthesis.md`](he-to-be-synthesis.md) at
  `0fbca0fd`) and its [packet](he-to-be-synthesis-review-summary.md);
- the repository itself: the root `Makefile`, `be`, `scripts/check-be.sh`,
  the tool locks, the `bringup/` trees, and Git history.

Four research agents each produced a cited report (the goals ledger, the
decision chain, the B-series progress, and the assurance and debt audit);
the owner reviewed the S1 draft directly, measured the repository with Git
and `wc`, and wrote this synthesis. Line numbers are at `2256101c`. Nothing
was executed beyond read-only Git and file inspection; no test, build,
emulation, proof, or board run informs this review.

**Second run (2026-10-18).** The same four reports were produced again on
`claude-fable-5.1` against `91d2c108`, whose planning files differ from
`2256101c` only in the roadmap and the handoff, so every cited line number
is unchanged. Each agent was told to form its own view first and then report
what it contradicted, what it found missing, and which citations it could
not verify. Every line citation in the first run resolved. The owner
re-measured each disputed figure with Git and `wc` before changing it. The
corrections applied in place are:

1. The narrowing of TE to a cost question predates the TE PoC: the
   "concrete property" test and the "Not justified in the current core"
   verdict are in the first pathfinder evidence (2026-07-16), and commit
   `4a913842` removed Model 0.1's scheduled use-case and trigger review
   (Part 2; F-02).
2. The "boot-time mandatory policy ceiling" quotation is from the
   2026-07-20 session analysis, now cited and added to the inputs (Part 2;
   F-04).
3. F-03 overstated H10, which rejects Helium's six-rule scan as a basis for
   lookup, dispatch, caching, and update and says nothing about analysis;
   and the S1 sentence it criticizes applies Model 0.1's trigger text
   faithfully, so the defect is in the inherited premise (Part 1; F-03).
4. R7's five C cut points are `c-mechanism`, `c-trap-dispatch`,
   `c-pending-binding`, `c-validator`, and `c-pte-builder`; `fact-linkage`
   is a sixth, and R7 calls all fifteen unproved. R7 also substituted one
   plan obligation, and its `ISA.v` stands in for the ratified
   specification (Part 4; F-09).
5. "No bounded checker ever run" is scoped to Beryllium code; Helium's
   original pathfinder ran CBMC, Frama-C, and Cerberus (Summary; Part 4).
6. The tests tree is 123,177 tracked lines, not 102,240; `bringup/`
   excluding results is 68,936 lines, not 61,544; the commit count since
   2026-10-06 is stated with its method (Part 6; F-15).
7. VMID width is reported by Linux in the B6 and B7 preflights; what is
   missing is a Beryllium probe. The threat-model row, the B5 sealing
   statement, the S1-S3 ownership paragraph, two drift rows, and the B7
   line-count derivation are made precise (Part 3; F-05 to F-07).
8. Part 5 now records the R7 decision that keeps pre-decision status fields
   in `be`, the exact binutils and node pins, the R4-R7 lock chain, the
   tracked remains of `tests/r8` and `tests/kvm0`, and the source of the
   861 s figure.

Material the second run added and the first had not: the two other original
immediate gates removed at `3b316566` and milestone 1's use-case gate, the
B1 port's SBI pin change and reset quiesce, Linux's change of role, the
accepted-tool-fixes precedent, the LPC venue of the B1 and B2 runs, the guest
SBI version change between B6 and B7, the Rust-first tooling preference, and
the Stage-1 Sail commitment. Each is placed in the part it belongs to. The
second run disagreed with no finding's direction or severity.

## Summary

1. The founding plan expects an analyzable policy. It says "Static boot
   policy should be deterministic, analyzable, measurable, and attestable",
   names FLASK as "the key policy/mechanism precedent", lists policy proof
   targets, and planned a pipeline from policy source to "the Rocq
   configuration used to instantiate integrity and noninterference
   theorems". No step since has built, scheduled, or owned that layer.
2. The narrowing is traceable to July 2026: a cost verdict on TE and a
   "concrete property" test written on 2026-07-16, before the TE PoC
   existed; TE priced by lines once the PoC had run (2026-07-20); a
   composition test turned into an adoption trigger that defines TE as an
   extra runtime denial (the same day); and the core declared
   "policy-neutral" (2026-07-22), in the same commit that removed Model
   0.1's scheduled use-case and trigger review. Each document also contains
   sentences that expect the specification later. It never came.
3. The S1 draft inherited that framing and, applying Model 0.1's trigger
   faithfully to B2's K3 result, concluded that the TE PoC scenario does
   not show the TE trigger fires. The premise is wrong, so the conclusion
   would have misdirected S2. The draft is otherwise sound and should be
   revised, not discarded.
4. The project is on track on the mechanism axis and behind on everything
   the threat model protects beyond private memory: no sharing, channels,
   revocation, devices, DMA, measurement, or management domain exists; the
   Linux guests are test payloads; B7's isolation is "by construction only".
5. B5-B7 were built first and are to be specified later: their guest SBI,
   HS interrupt, scheduler, and roots sit outside Model 0.2 and R1 sealing,
   with no proof, and S2 is expected to write their invariants afterwards.
6. The assurance position is narrower than the founding commitments: abstract
   Rocq over one fixed instance, a bounded exact-byte proof of eleven
   wrapper symbols behind fifteen unproved cut points (five of them C), no C
   refinement, no Sail, and no bounded checker ever run on Beryllium code.
   Helium's release line shows bounded model checking of the same class of
   restricted C is tractable, with explicit limits on what that can claim.
7. Documentation outweighs code 4.6 to 1; the handoff has grown from 182 to
   4,327 lines and is touched by 63% of all commits; status is replicated
   across about seven files per change and is now stale in at least a dozen
   places. R8 and KVM0 were dropped without a recorded rationale.
8. Engineering debt concentrates in three places: `bringup/` outside the root
   build and `./be`, which still carry dropped-R8 text; six acceptance-pin
   constants embedded in root files; and tool locks that fail on the
   development host while bring-up uses unpinned tools.

## Part 1: the S1 draft and the critique

The S1 draft at `0fbca0fd` classifies 58 Helium elements (34 adopt, 14
adapt, 3 reject, 7 defer) against the B0-B7 evidence. Its packet at
`2256101c` is accurate about what it did and did not do.

**The error (S1-F1).** The draft's "Findings" bullet 2, rows H02, H08, and
H55, and S2 hand-off item 1 argue from E03 (B2's K3 result: a denied
cross-private load and a denied store to a read-only shared page, with
"enforcement is ownership and an explicit read-only channel") that "The
scenario alone therefore does not show that the TE trigger fires." E03 shows
that one fixed configuration's two denials can be expressed as G-stage
mappings. It says nothing about how the system's security properties are
specified, analyzed, or verified. A sealed manifest of grants is an
extensional record of the authority that exists
([capability policy](capability-policy-architecture.md), "Core conclusion");
it gives no language in which to state a system-wide property, no types to
analyze, and it trusts the manifest's author by definition. Once the
untrusted management domain of threat model v0 creates guests and channels
at runtime, ownership plus channels is discretionary: the owner decides what
to share. A central mandatory policy is what bounds that, which is the role
XSM/FLASK plays over Xen's dom0 in the comparison's own precedent table. The
seL4 integrity and information-flow theorems that the research cites are
stated against an access-control policy abstracted from the capability
state, not against the capability state itself.

**It is inherited.** The sentence the draft wrote is a faithful application
of Model 0.1's accepted trigger text; the defect is in the premise the
draft inherited and did not test against the research inputs already in the
repository. The chain is: the first pathfinder evidence's cost verdict and
"concrete property" test (2026-07-16); the comparison's "Cost separation",
which prices TE by lines and KiB; its "Authority sequence" and Model 0.1's
"TE trigger", which define TE as a denial "despite valid designation and
capability rights"; and the implementation plan's "Pathfinder policy
result", which says TE "adds state, lifecycle, proof, and usability
obligations". Part 2 traces it.

**Helium's own framing was captured but not applied (S1-F2).** Rows H06 and
H07 record Helium's questions for "the next Be stage" (type granularity,
permission aggregation, policy-only `open`), and Helium's FAQ defines TE as
"a centrally administered, declarative access-control model". The draft
filed these as object-model details for S2 rather than as evidence that a
declarative policy layer is the specification.

**H10 closes a door S2 needs open (S1-F3).** Rejecting Helium's six-rule
scan as a basis for policy lookup, dispatch, caching, and update is right
as "do not transfer Helium's representation", but any policy richer than
six rules needs compilation, analysis, and, if dynamic, generations and
invalidation. The row should defer to S2 with the specification role stated.

**Bulk (S1-F4).** About fifteen rows confirm practices Beryllium already
follows (H25, H28, H30, H33, H35, H37, H39, H44, H45, H47-H49, H52, H53).
They add review burden without decision value.

**What the draft got right (S1-F6).** The E01-E12 evidence table with the
records' claim wording; the three K3 gaps (no shared page or denial test
between Linux guests; `htval` unrecorded; VMID tagging untested); the Helium
verification lessons H38-H43, including the "lessons not to transfer" and
the evidence-method table; the entry-state defect lesson (H17); the
cardinality lesson mapped to open finding S6 (H26); the evaluator read-write
mount (H31); and the observations about stale numbering and figures. The S3
hand-off list is sound.

**Process (S1-F7).** The owner's same-session review did not catch the
error; the responsible human did, from domain expertise. The draft's policy
premise was never checked against the research inputs already in the
repository. The pin lineage was misstated in conversation before S1 was
authorized and corrected with Git before any commit; the lesson is to verify
ref lineage with Git before summarizing it.

The responsible human has already chosen the revision direction
(`revise-adopt`, 2026-10-17): adopt a central TE-style declarative policy as
the specification against which system properties are stated, analyzed, and
verified, with enforcement still derived from it. The companion revision
plan, `s1-te-trigger-revision-plan.md`, proposed separately, proposes how.

## Part 2: the security model and policy direction

### What the founding documents expect

| Statement | Where |
| --- | --- |
| "Static boot policy should be deterministic, analyzable, measurable, and attestable." | implementation plan L740 |
| "FLASK is the key policy/mechanism precedent: object managers enforce, a security server decides, opaque labels identify subjects and objects, and generation-aware caches accelerate decisions." | L734 |
| "Policy/mechanism separation is a first-class architectural and formal-assurance goal, not an optional afterthought." | L844 |
| Policy proof targets: "Deterministic and total policy semantics", "Default-deny and explicit conflict resolution", "Compiler preservation from source policy to the compact artifact", "Static checks for unreachable, contradictory, over-broad, or non-revocable authority", "Authority non-amplification across every delegation chain" | L931-L940 |
| An offline pipeline: "system source + board Device Tree/description + policy source -> typed IR -> ... canonical security manifest + Rocq configuration + authority graph + audit report + measurement inputs"; "Generate the Rocq configuration used to instantiate integrity and noninterference theorems" | L401, L416-L417 |
| "Keep an executable formal model of both the mechanism and policy semantics." | L944 |
| "The measured boot policy and initial authority graph define an immutable authority ceiling for a running configuration." | L890-L901 |

The research inputs say the same in other words: a capability graph or
ownership table is an "extensional" record of current authority, while an
"intensional, system-wide language explaining why that authority should
exist or which future authority states are permitted" is a separate layer
([capability policy](capability-policy-architecture.md) L36-L44); the
proposed architecture is "High-level policy (TE / MLS / roles / attributes /
flow / administration) -> compile or validate -> Canonical authority state ->
refine -> Enforcement" (L361-L372); seL4 "compiles policy into an initial
capability graph and proves properties relative to that configured
authority" (L240); and the
[2026-07-20 session analysis](session-analysis-isolation-engine-2026-07-20.md)
itself proposed that "TE should initially be a boot-time mandatory policy
ceiling ... Compile the fixed labels/rules into a canonical manifest,
validate it in HS, and construct the roots" (L79). Two of these inputs also
ratified the narrowing they describe: the capability-policy research says
"The current Beryllium trigger-gated direction remains appropriate"
(L395-L410) and restates the runtime-denial test as its human question 8
(L304-L305), and the comparison carried seL4/capDL's "Define the static
system state once, validate it independently, and use it for
initialization, proof instantiation, and audit" (L105) and XSM/FLASK as a
caution (L107) into its precedent table without a schedule.

### Where the framing narrowed

1. **TE priced as a cost (2026-07-16, confirmed 2026-07-20).** The first
   pathfinder evidence, written before the TE PoC existed, already carries
   the verdict "Capabilities plus TE ... Highest; composition and usability
   risk ... Not justified in the current core" and the test "Evaluate
   whether a mandatory-flow layer adds a concrete property that cannot be
   expressed acceptably through ownership and bounded capabilities"
   ([pathfinder evidence](pathfinder-evidence.md) L345, L351-L352, at
   `94bfd2f7`); the original plan's P6 criteria had mixed cost axes with
   "Information-flow expressiveness" ([pathfinder plan](pathfinder-plan.md)
   L105-L123, the axis at L119). The TE PoC evidence then records "this
   branch adds 602-645 lines and one loaded 4 KiB region" and, to its
   credit, "Line count and binary size are not security proofs"
   ([TE evidence](type-enforcement-pathfinder-evidence.md) L217-L223); the
   TE plan itself expected "a later system-description compiler and
   validated initializer" ([TE plan](type-enforcement-pathfinder-plan.md)
   L126-L127). The comparison then binds adoption to cost: "introduce TE
   only when a concrete mandatory property justifies its independent cost"
   ([comparison](pathfinder-comparison.md) L19-L21, L73-L93), while also
   saying the project should "optimize for a small stable mechanism and a
   tractable proof/refinement boundary, not for the lowest source count
   alone" (L92-L93). The information-flow expressiveness axis is absent
   from the evidence table that fed the comparison. The minimal pathfinder
   had meanwhile deferred the only policy-analysis tooling considered,
   `cheriot-audit` and Rego, as "unnecessary dependencies here"
   ([minimal plan](minimal-pathfinder-plan.md) L87).
2. **A composition test became an adoption trigger (2026-07-20).** The
   isolation research describes a test that makes capability and TE
   "independently decisive": a subject may hold a right while TE denies, and
   TE may allow while no right exists
   ([isolation engine](isolation-engine-policy-research.md) L470-L480).
   Commit `9d8407f2` made that test the condition for adopting TE at all:
   "Add TE only if the selected use case contains a capability-valid or
   ownership-valid operation that must still be denied because of an
   independent mandatory source/target/class or flow rule"
   ([Model 0.1](architecture-model-0.1.md) L266-L276). The same commit
   scheduled the decision: Model 0.1's gates required the next planning
   review to "select one narrow motivating use case" and "decide whether
   that use case fires the capability or TE trigger" (`9d8407f2`, Model 0.1
   L314-L323). From then on, every decision about TE is taken through this
   trigger, that is, as a runtime denial that ownership cannot express; the
   specification role against which ownership itself would be judged stays
   visible in retained sentences and enters no decision.
3. **"Policy-neutral" (2026-07-22).** Commit `4a913842` introduced Model 0.2's
   phase question and planning principles 10 and 11 across many files at
   once, and removed the scheduled use-case and trigger review from Model
   0.1's gates, giving as its reason that selecting a use case first risked
   "embedding TE, capability, identity, role, or attestation assumptions"
   in the core and "confusing correct enforcement with correctness of the
   policy being enforced" ([Model 0.2](architecture-model-0.2.md) L43-L55).
   Model 0.2 is careful: "policy-neutral, not policy-free", and "The core
   cannot be free of all policy" (L67-L86). It also states the deferral
   exactly: the claim that an accepted configuration implements the
   operator's intended policy "requires a policy specification and a proof
   or analysis connecting that policy to the proposal. That evaluation
   belongs after Model 0.2" (L273-L274), and "A structurally valid but
   intentionally over-permissive proposal may still be a policy error"
   (L118-L120). Nothing after Model 0.2 scheduled that evaluation. The
   responsible human's 2026-07-24 feedback, "Revisit applying TE to
   capabilities", produced research only
   ([runtime plan](single-hart-runtime-plan.md) L57-L75). The runtime plan,
   R0-R7, R8, the B-series, and the step 3 re-baseline each list policy as
   a non-goal or defer it; the first place it reappears is S2's one-line
   scope.

### In what form the security properties exist today

No step provides a system-wide policy language or a policy analysis. The
properties that exist are:

- prose lists (threat model v0; Model 0.1's goal that "the only cross-domain
  storage channel is one explicitly declared directional shared region");
- Rocq invariants over one fixed two-domain instance: Model 0.1's nine
  obligations (`unique_private_ownership`, `monitor_exclusion`,
  `mapping_soundness`, `directional_channel_confinement`,
  `saved_state_separation`, `switch_freshness`,
  `terminal_fail_closed_behavior`, and two more) and Model 0.2's 23 theorems
  over one proposal shape, with "Full information-flow noninterference"
  deferred in both;
- C validator rejection rules (R1), an independent walker that confirms each
  leaf matches canonical authority (R2), fixture expectations and QEMU trace
  markers (R3-R5), a 29-class adversarial catalogue whose "denied access"
  family checks fault metadata rather than authority (R6), and R7's
  `Configuration.v`, which "proves only the finite access matrix implied by
  those generated facts" over 13 resources, with the link from C state to
  those facts an unproved cut point and one plan obligation, that the switch
  path "clears live guest GPR authority", substituted by the weaker record
  that saved guest GPRs "remain live in the trap frame across the C cut
  point" ([R7 evidence](single-hart-runtime-r7-evidence.md), "Plan-obligation
  substitution"); R0 records that even the delivered thirteen-resource
  profile "is **not** a Model 0.2 refinement"
  ([R0 freeze](single-hart-runtime-r0-freeze.md) L190-L197);
- for B5-B7, "load-bearing invariants" checked by host tests, with no model.

Every one of these is extensional and instance-bound. Reachability,
information flow, and over-broad authority relative to intent are checked
nowhere, and over-permissiveness is explicitly outside Model 0.2's claim.

### Consequence for S2

S2 is defined as "objects; authority from a sealed static manifest, with
ownership plus explicit channels; invariants; threat model; trusted computing
base; and whether the platform's use cases fire the capability or TE
triggers" ([roadmap](roadmap.md), "Planned sequence"). On the policy
dimension, S2 as written would evaluate the TE trigger of Model 0.1, that
is, whether a runtime denial is needed on top of ownership; its other items
(objects, invariants, threat model, TCB) are not at issue here. It would not,
by its definition, produce the specification layer the implementation plan
expects, nor the policy proof targets, nor the pipeline to the Rocq
configuration. Its recorded scope also omits four of the seven items the
plan's own decision gate says the use-case and trigger result must update
before a policy or protected-service plan is approved: the authorization
API, revocation, the audit schema, and the CHERI mapping (L970-L979). That
is the gap this review asks the responsible human to decide on; the
companion revision plan, `s1-te-trigger-revision-plan.md`, proposes one way
to close it.

## Part 3: progress against the founding goals

### The goals, grouped, with status

| Group | Goal (abridged) | Status at `2256101c` |
| --- | --- | --- |
| Purpose | A minimal RISC-V security monitor for Linux-oriented systems, "a trustworthy and experimentally useful substrate for security research" (plan L229) | In progress. R0-R7 accepted on QEMU; B0-B7 accepted on one K3 board. No research workload has run; the research-platform release is S3. |
| Core boundary | Small trusted core; drivers, I/O, orchestration, rich policy outside (L231, L746-L796) | Partly met. The R-series core has no drivers or policy. B5-B7 add HS-resident guest-SBI emulation, console, timer, and a scheduler; the B7 layer is 4,470 HS lines (4,621 with its linker script and guest-payload stub), outside the root build. |
| Identity and boot | Independent of KVM (L423-L434); Beryllium boots before Linux, Linux-first "optional for development" (L436-L450) | Identity met. Boot partly: B3, B5, and one B6 run used U-Boot; B0-B2, four B6 runs, and all B7 runs loaded through Fedora `kexec_load`. No measured artifact. |
| System description | Offline Device Tree plus a capDL-inspired manifest; fixed format, authenticated, measured; atomic activation; authority graph and Rocq configuration (L378-L421) | Partly met in R0-R7 (generated proposal, validated, sealed, derived). No encoding, parser, signature, or measurement. B6/B7 guest windows come from link-time constants: "no R1 or R2 claim covers it" (B6 plan L782). |
| Threat model | Linux untrusted "from its first instruction"; all domains mutually hostile; protected assets include private memory and vCPU state, page tables, IOMMU, capability and policy state, measurements; "Shared writable memory exists only through explicit, revocable grants" (L481-L524) | Partly met. R5 denies the fixed cross-domain accesses, including the store to the read-only channel, and R6 measures the mechanism with 47 single-defect fixtures while disclaiming "Universal containment of malicious or arbitrary guests" (R6 record L190-L191); B5 refused hostile guest SBI inputs on the board. On K3, Linux is "an untrusted test payload" (glossary L83), not a management domain; B7's "isolation is by construction only, with no denial test". No grants, revocation, DMA, interrupt ownership, or measurement. |
| Mandatory requirements | "small enough to audit and formally model" (L771); complete mediation; fail closed; non-ambient authority; CPU, memory, interrupt, DMA ownership; revocable sharing; measurable identity; bounded versioned interfaces; a QEMU path (L769-L782) | Mixed. Mediation, fail-closed, and the QEMU path are met in the R-series; B6's `hedeleg` readback failed closed on the board. Memory ownership on one hart only. Measurement not met. B5-B7 are "small" only relative to Linux and have no proof. |
| Policy and authority | Analyzable static policy; FLASK precedent; policy proof targets; immutable authority ceiling; dynamic policy in a separate domain (L734-L741, L890-L940) | Not started, apart from the mechanism half. See Part 2. |
| Language and proof | Restricted GNU C on GCC and Clang; a proof-bearing subset with a machine-checkable coding profile; Rocq primary; Sail for supported behavior; Cerberus reference; CN pilot; refinement to C (L1006-L1127) | Dual compilers met. No proof-bearing subset designated; no coding profile artifact; Rocq used for Models 0.1/0.2 and R7; Sail not used ("H path blocked"); CN "Not run"; no C refinement. |
| Tooling | Fully open and reproducible; pinned compilers trusted early; open source-to-binary correspondence by the assurance release (L1129-L1160) | Partly met; drifted in the B-series (unpinned tools). The R6/R7 locks fail on this host. |
| Sequence | QEMU first, then K3; verify on arrival "the H bit, `hgatp` modes and VMID width, AIA guest files, Sstc delegation, PMP state, IOMMU visibility, and OpenSBI handoff" (L560) | H, Sv39x4, Sstc, the OpenSBI handoff, and `hedeleg` WARL characterized. PMP, AIA guest files, and IOMMU not reported. VMID width appears only as Linux's `VMID 14 bits available` in the B6 and B7 preflights, not as a Beryllium probe. |
| Community | Publish the problem statement early; seek upstream feedback before interfaces harden; an October 2026 checkpoint (L2059-L2085) | Not met per the records: publication blocked, no maintainer contact recorded, and no checkpoint outcome recorded, although the B1 and B2 board runs took place "at the Linux Plumbers Conference venue" (handoff L79, L96). |
| Research platform | "The first usable system will run a protected security-research domain whose confidentiality and integrity remain enforced after host Linux is compromised" (L627); a secret and an integrity-sensitive computation in the protected domain (L639) | Deferred under a "Deferred ... hypothesis" heading. The expected first MVP milestone is instead the Helium TE PoC scenario on two Linux guests. |

### What B0-B7 settled

HS entry on K3 above OpenSBI 1.6 with H active (B0); the accepted R3/R4/R5
bytes running on K3 through counted, re-derivable generated ports, with the
R1 identity re-pinned, the SBI specification pin moved from 3.0 to 2.0, and
a quiesce of a pending Sstc timer interrupt inserted before `be_reset`
(B1, B2); real G-stage denials on K3, for synthetic domains only, where
"enforcement is ownership and an explicit read-only channel" (B2); a launch
path in which Linux does not run first (B3); R6 and R7 re-derived for the
K3 image bytes (B4); a bounded guest SBI subset emulated in HS, unregistered,
with Sstc reaching VS and HS, and the guest's hostile inputs refused on the
board (B5-B7); an unmodified uniprocessor Linux `v7.2` confined to a 64 MiB
window (B6); `hedeleg` WARL on K3, caught by a fail-closed readback (B6);
two Linux guests time-sliced on hart 0 under distinct VMIDs with identical
counts across four runs (B7); a RAM-only board procedure and fixed claim
wording; and reproducible guest inputs and a QEMU path per milestone.

### What remains unexercised against the threat model

Sharing or channels between Linux guests (B7's pair check "refuses shared
pages"); any denial or fault-injection test between Linux guests (B6's QEMU
`memory` variant tested a guest's out-of-window access in emulation only);
revocation, which appears in no B-series plan or record; interrupts beyond
the HS timer, devices, IOMMU, IOPMP, DMA; more than one hart ("Linux stopped
its other harts before each kexec"); measurement and attestation; a
management Linux domain, and a protected domain beside a Linux guest (B6:
"the protected root is built and re-walked but never entered"); guest
console input; proofs for B5-B7; root integration; pinned tools; hardware
validation, which "requires an accepted validation plan" and has none;
platform characterization (PMP/Smepmp, optional state, cold boot,
`htval`/`htinst`, a Beryllium VMID-width probe); the firmware/SBI boundary
comparison the plan requires; and per-exit and per-switch costs that the B7
plan promised to measure.

### Drift signals

| Signal | Founding statement | Current position | Acknowledged? |
| --- | --- | --- | --- |
| Out-of-tree bring-up | "Make every milestone useful before the next milestone exists" (L679) | Each milestone has its own QEMU path (`make -C bringup/k3-bN check`), so L782 is met per milestone; `bringup/` is outside the root build, `./be` reports K3 `NOT RUN`, and the roadmap lists "Bring-up copies drifting from the accepted core" | Yes; deferred to the MVP plan |
| Core changes in ports | "A platform port must not smuggle a core redesign into an architecture file or acceptance-pin refresh" (R8 plan L622-L626) | The accepted bytes "cannot run on K3 unchanged"; resolved by substitution ports and a re-pinned identity, including the SBI specification pin moved from 3.0 to 2.0 and `be_reset` calling a new quiesce of a pending Sstc interrupt (B1 record L84-L111) | As counted rules and a resolved finding, not as a boot-contract or firmware-boundary consequence; the comparison's "SBI and firmware boundary" decision has no successor |
| Linux's role | Boot chain "Beryllium -> Linux management/service domain and protected domains" (L440); "Linux is a stretch PoC outcome and later management-domain target" (L570) | Linux `v7.2` is "an external test input" and "test payload" with no devices; BSP selection "no longer gates the planned sequence, because the guests see no devices" (L211-L214) | The gate change is recorded; the change of role, from management domain to device-less payload, is not discussed |
| Build first, specify later | "Keep an executable formal model of both the mechanism and policy semantics" (L944); add "policy complexity ... and assurance claims only after an explicit evidence gate" (principle 9, L683) | B5-B7 add guest SBI, an HS interrupt, per-guest state, and a scheduler outside Model 0.2, with B6/B7 roots outside R1 sealing; "All RAM is RWX" (B6 plan L448); S2 writes the invariants afterwards | Each departure listed per milestone; the change of method not discussed |
| Pace | Principle 9, as above | B0-B7 plans, implementations, board runs, and acceptances all fall between 2026-10-06 and 2026-10-09; R0-R7 took ten weeks with plan-revision records | Not discussed |
| First MVP milestone | A protected research domain that survives host compromise, protecting a secret and a measurement (L627-L639); do not "define MVP 1.0 by extrapolating from one PoC" (handoff) | The Helium TE PoC scenario on two Linux guests, "after S2 defines channels" | Only "Reproducing that scenario does not select TE"; no reconciliation with L627-L639 |
| Formal K3 validation before an OS | "R8 puts core-hypervisor correctness and one-board K3 validation before OS support" (R8 plan L473) | R8 dropped (`r8=drop`); Linux guests run on diagnostic evidence | "The B-series results do not stand in for the evidence these workstreams planned"; no rationale recorded |
| Review practice | R5 acceptance included "an independent core/runtime review" (L72); the core must be "small enough to audit" (L771); "Independent output checks where possible" (open tooling L60) | The 2026-10-06 SOP: "no deep security reviews as standard practice"; B1 "no independent review ran"; B0-B4 authorized by instruction without plan documents | As an SOP; not weighed against L771 |
| Accepted bytes | Accepted targets are immutable; tool changes need enumerated pin refreshes | The 2026-10-07 tool fixes changed accepted R3/R4/R5 checkers and the R7 extractor under a pin refresh: the predecessors "stay accepted at their exact targets, with their results unchanged; none is re-accepted", and the corrected tools "are the maintained versions" (tool-fixes record L23-L27) | Explicitly, as a new precedent |
| Guest SBI | Linux-class guest SBI "deferred to a separate plan ... from first principles" (runtime plan L293-L315); interfaces "bounded and versioned" (L780-L782) | B5-B7 each declare themselves "that separate plan", for their own guest only; no SBI profile selected; the implementation version moved from 2 (B6) to 3 (B7) with no versioning policy | Explicitly, except the version change |
| Tooling | "All project tooling is fully open source and reproducible" (L1131); "Prefer Rust first for ... policy tooling, analysis tools, service domains, and test infrastructure" (L1237) | Unpinned workstation GCC 16.2.1, Clang 22.1.8, QEMU 10.2.2 in B4-B7; the tooling is JavaScript, shell, and Python, with no Rust | Pinning: yes, "pin tools before any assurance claim"; the language preference: no |
| CHERI | Every decision "must be evaluated for conceptual or technical alignment" (CHERI alignment L3-L14) | Zero CHERI mentions in the B5-B7 plans and the eight B records | No |

R8 and KVM0 were dropped on 2026-10-08 by instruction. No rationale is
recorded beyond the instructions, and there is no review packet for the step
3 re-baseline commit `ecad45d8` itself; its acceptance appears only in status
documents. The glossary is explicit about what the B-series is not: "B-series
board runs are not H1 characterization", B2 "is diagnostic bring-up evidence,
not H2", and B4 "is not H3".

### The S1-S3 sequence

S1 selects nothing and closes no open decision. S2, as defined, decides the
capability and TE triggers and the manifest semantics, and must define
channels before the first MVP milestone; the protected-service use case may
be selected "inside an accepted S2 or S3 scope" (decision gate 2,
L2106-L2107), so either step may own it. S3 selects from
implementation-plan milestones 3-10 and owns the BSP, root integration, the
richer userland, and the release path, and "may recreate a formal K3
evidence package" (L1985-L1987), which gives K3 firmware and PMP behavior an
optional owner rather than a committed one. Of the comparison's twelve open
decisions, the manifest encoding and the management ABI, CHERI feasibility,
and Kbuild placement have no owner in S1-S3.

## Part 4: the assurance strategy

**Commitments.** Restricted C in three layers, with a proof-bearing subset
and a machine-checkable coding profile; Rocq primary, Sail for the behavior
it supports, Cerberus as the C reference, CN as a pilot, refinement down to
C; differential testing of production code against the executable model;
pinned compilers trusted early and open source-to-binary correspondence by
the assurance release; an open tool-qualification evidence set and a
scorecard for every mandatory tool.

**What is proved today.** Model 0.1: nine bounded obligations for one fixed
abstract two-domain configuration; "does not establish a refinement relation
between Rocq and `model/src/*.c`". Model 0.2: 23 bounded obligations for one
proposal shape. R7: 135 theorems and 4 lemmas over the exact linked bytes of
eleven privileged-wrapper symbols in two images (1,420 words), with a
hand-written bounded `ISA.v` that stands in for the ratified specification
as R7's first trusted assumption; fifteen cut points, "each an explicit
unproved boundary", five of them C (`c-mechanism`, `c-trap-dispatch`,
`c-pending-binding`, `c-validator`, `c-pte-builder`) plus `fact-linkage`,
the link from C state to the generated configuration facts; ten trusted
boundaries; fourteen non-claims, among them
`formal_verification=bounded-not-whole-system`, `c_refinement=not-claimed`,
and `qemu_execution=not-re-run-in-r7`; and one plan obligation substituted,
since the switch path's clearing of live guest GPR authority is not proved
and the saved guest GPRs "remain live in the trap frame across the C cut
point". R6: a finite 47-entry adversarial catalogue over 29 error classes,
"not exhaustive", of whose eleven detection layers six are R6-owned and five
are accepted R5 stages observed, with "The accepted R0-R5 mechanism ...
trusted as the measurement instrument". B4 re-derived R6 and R7 for B2's K3
images under unpinned tools.

**Against the founding targets.** Of the mechanism proof targets,
fail-closed behavior and fixed-instance memory and saved-state separation are
covered abstractly; complete mediation has no theorem of that name;
non-forgeability and non-amplification are abstract; Stage-2 ownership is
abstract plus R7's install and fence bytes; IOMMU, grant and revoke,
policy-generation freshness, and architectural noninterference have nothing.
Of the policy proof targets, none is addressed. Differential testing against
the Model 0.2 executable model has not been done (B7's scheduler host test
checks six pseudo-random runs against its own reference model, and R7's
`Configuration.v` checks runtime constants against the accepted model's
access matrix; neither is the Cedar-style pattern the plan names). No
proof-bearing subset is designated, and no coding-profile artifact exists:
`tests/r5/check-sources.mjs` and `model/tests/check-source-policy.sh` guard
source boundaries (no hosted headers, no inline `asm` or CSR access in the
neutral core, one `sret`, linker `ASSERT`s), which is not the restricted-C
subset profile the plan promised. No bounded checker, sanitizer, or fuzzer
has run on Beryllium code; the original Helium pathfinder's "Sequential C
verifier pilot" did run CBMC 6.8.0 (123 checks), Frama-C 32.1 WP (91 of 91
goals), and Cerberus ([pathfinder evidence](pathfinder-evidence.md) L73,
L319-L320), and that result stayed in Helium. Sail is not used, although the
plan's Stage 1 was to "Validate the Sail-to-Rocq RISC-V H-extension path
during this stage" (L1207) and the open-tooling policy lists the RISC-V
Sail model (L124). There is no companion proof repository, which the plan
defers until the core enters Linux (L322).

**The B5-B7 gap.** B5 (1,759 HS lines), B6 (3,080 excluding its linker
script and guest-payload stub, 400 of them in `b6-trap.S`), and B7 (4,470
on the same basis, 557 in `b7-trap.S`) each state "has no proof";
R6/R7-style work is "not applicable"; B6 "adds unproven privileged
assembly". R7's scope includes `be_r3_arch_install_management`, which B6 and
B7 call, but no B5-B7 image was proved.

**The open verifier question.** The load-bearing C verifier is still open
("VST's open distribution, RefinedC, a direct Rocq development, or a
combination"), and CBMC is listed only as a complementary tool. Helium's
release line ran CBMC over production C against independent specifications
in eight tiers (18 checks, 152 named claims, 19,419 properties, 18 seeded
mutations each mapped to the claim that must fail), on the same class of
restricted C that R7 leaves as cut points. Helium also states the limits
exactly: "Do not conflate CBMC with proof-assistant/kernel verification";
"Do not verify synthetic models without correspondence work"; a bounded
model checker is not to be used to claim compiler, ISA, concurrency,
unbounded, noninterference, or hardware correctness; and the choice was "not
a claim that Rocq is unsuitable for future Be work". Helium's unproved list,
live capture and correspondence, is the same kind of link R7 records as its
`c-*` and `fact-linkage` cut points, and Helium states the consequence
plainly: "The conventional target compilers are not removed from the runtime
TCB because there is no source-to-binary refinement"
(`docs/security-and-limits.md` at the pin).

**Numbering.** The implementation plan (L1160) and the open-tooling policy
(L268) say "Milestone 8 cannot complete without an open binary-correspondence
result"; milestone 8 is now portability and the assurance release is 9.

## Part 5: engineering debt

| Item | Evidence | Origin | Cost |
| --- | --- | --- | --- |
| `bringup/` and `tests/unit` outside the root build and `./be` | Root `Makefile` `check` includes neither (nor `r2-check` and `r3-check`, which exist only in `be`); `bringup/` has 408 tracked files and 78,931 lines; `tests/unit` (187 cases) is unwired "because that would move the R7-A root pins" | The one-directory-per-milestone model; root integration listed as a separately directed successor at every acceptance | `make check` and `./be check` exercise no K3 artifact; milestone gates are heavy (the B4 gate took 861 s in the 2026-10-07 tool-fix run, "about 20 minutes" in B4's own record, and its R6 half writes and deletes about 43 GB) |
| Generated and copied code per milestone | `port.py` chains B1 -> B2 -> B5/B6/B7 with counted rules and SHA-256-pinned inputs; B7's monitor and tools are counted copies of B6's; B4 copies R7 with 59 rules | B1's generator method, reused unchanged | Any maintained change to accepted R3-R5 source breaks every port; fixes do not propagate (the extractor truncation was fixed separately in B4's copy and in the accepted tool); finding S10 open |
| Acceptance pins in root files | Six constants across `tests/r1/check-acceptance.sh`, `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs`, enumerated by `tests/r6/acceptance-pins.mjs`; every root `Makefile` commit since R1 also edited the R1 checker | R1's single successor-command-graph exception and the R3/R4 exact-approved-delta model; plan revision R7-A was needed just to enumerate them | Any edit to a root file, even help text, re-derives six constants in three accepted checkers; B4's first gate had to be decoupled from the R1 pin |
| Dropped R8 and KVM0 text in maintained interfaces | `be` help: "Beryllium execution remains NOT RUN", "Next gate ... H0 successor"; `be status` prints `stage=single-hart-runtime-r5`, `r7_acceptance=not-reviewed`, `r7_accepted_commit=none`, and `r8_authorization=not-authorized`; `scripts/check-be.sh` asserts those strings and "BLOCKED-NOT-READY with 80 H0 blockers"; `tests/r8` (23,121 lines) and `tests/kvm0` (14,617) remain tracked | Older than the drops: the R7 acceptance deliberately kept the pre-decision fields, since "Rewriting those retained fields would falsify exact-target evidence" (R7 record, "Retained pre-decision status fields"); the R8 and KVM0 text was then overlaid on the same frozen files, and the 2026-10-08 drops kept records as history; changing these files needs the six pins | Misleading operator interface, which contradicts the roadmap on R7's acceptance and on B0-B7; blocks root integration of B-series targets |
| Tool locks versus unpinned tools | R3-R7 locks bind node v22.22.2 from `nodejs22-22.22.2-3.fc44`, GCC 16.1.1, host binutils 2.46.1-1.fc44, and cross binutils 2.46-1.fc44; the R4-R7 locks bind the R3 lock by digest, so one pinned-tool change invalidates four dependent locks; this host has GCC 16.2.1, binutils 2.46.1, and node v22.22.2 from `nodejs-22.22.2-2.fc43` with a different digest; B-series records say "This workstation's unpinned tools" | The R3 normative lock; B2's choice of workstation tools | Accepted launchers fail outside the pinned container, which is a single-copy artifact, not byte-identical on rebuild, and lacks `npm` and `dot`; the open-tooling policy's source-revision and build-recipe recording is unmet |
| Open audit findings and drift | S5-S8 and S10 open; R8 inventory drift grew from 3 to 10 entries; `check-be.sh` fails on node digest drift; in a fresh clone R6 `--require` fails for want of a canonical report; `routine-evidence-check` needs retained `build/*/evidence` | The 2026-10-07 audit fixed S1-S4 only, at human direction | Latent validator weaknesses (S6 is the same class as Helium's REV-P2-01); a fresh clone cannot pass the root gate |
| R4's 3 s QEMU budget | `tests/r4/run-qemu.sh` is in R4's immutable paths; it fails in the pinned container at every commit tried | The accepted R4 runner | Root `check` fails on slow hosts; any fix needs an approved delta |
| Generated-asset reproducibility | VitePress byte identity open since R2; Option A covers 24 paths in one environment on an unintegrated branch; the whole-ELF digest depends on the build path (`-g3 -gdwarf-4`, no `-fdebug-prefix-map`); evidence-retention Phase 2 blocked with no store | Generator inputs never pinned | "The linked image and measured artifact are reproducible" holds only for the allocated-image identity |

**Stale documentation**, with exact statements:

1. Root `README.md`, "Current phase": "Current position (2026-10-08): the K3
   bring-up sprint under `bringup/k3-b0` to `bringup/k3-b6` is the active
   path. B0 to B6 are accepted". B7 was accepted 2026-10-09; S1 is authorized.
2. Root `README.md`, "Delivery stages": the R8 row says "K3 is `NOT RUN`"; the
   Linux milestone is "deferred until after R8 review"; no B0-B7 or S1-S3
   rows.
3. [`riscv-security-hardware.md`](riscv-security-hardware.md): "Current R8
   boundary"; "K3 remains `NOT RUN`"; "Do not start H1-H4 or K3 execution";
   no B-series reference at all.
4. [`research-synthesis.md`](research-synthesis.md), "Updated project focus":
   "R5, MVP 1.0, and every successor remain gated, not authorized, and not
   started".
5. [`HANDOFF.md`](HANDOFF.md): the heading "Current state: 2026-10-06
   re-baseline" (the re-baseline was 2026-10-08); "Validation and retained
   artifacts" stops at R5 and lists `docs/html/`, untracked since `ee1feaf9`;
   "Do not start R8-H1 through R8-H4"; "After R5 evidence, do not ... add
   Linux boot".
6. [`implementation-plan.md`](implementation-plan.md): header "Current
   position (2026-10-09)" beside an S1 authorization dated 2026-10-16; L209,
   L1353, and L2109 still say S1-S3 are "planned, not authorized"; L2115
   says "Approve a separate later plan before a second guest (B7)"; "Milestone
   8" at L1160.
7. [`planning/README.md`](README.md): no R4 row; "R6+ remain gated" and
   "R6/R7 remain gated" in exit columns; "H1-H4 remain unauthorized and K3
   remains `NOT RUN`".
8. [`project-orientation.md`](project-orientation.md) L140: S1-S3 "Planned,
   not authorized", against its own header.
9. [`glossary.md`](glossary.md): lists `k3-b0` to `k3-b6` only; still describes
   VMID zero; defines the management domain as "synthetic HS-side logic",
   which the runtime plan contradicts.
10. [`pathfinder-comparison.md`](pathfinder-comparison.md): "R0 next"; Helium
    at 2,253 lines and 16 KiB (now 4,598 lines and 20-24 KiB at the pin).
11. The roadmap's "Later phases" lists seven rows for milestones 3-10.
12. The `./be` help and `scripts/check-be.sh` text above.

The founding text has also been rewritten in place without a visible decision
trail: the problem statement's scope was narrowed from four architectures
(`3b316566`), which also replaced all three original immediate decision
gates, "Fully open C verifier, translation-validation, coverage,
traceability, and reproducibility baseline", "Profile-neutral assurance
artifact schema and deployment crosswalk format", and "Community validation
before implementation" (`30aefab7`, L977-L980), none of them met before
implementation began, and dropped milestone 1's gate, "demonstrate that the
model supports at least two real use cases" (`30aefab7`, L900); the anchor
use case was demoted to a "Deferred" heading while keeping the future tense
(`4a913842`); and the original unconditional milestone "Deliver
capability/label enforcement, measured static policy, offline tooling,
revocation, and audit records" became conditional on a trigger. The threat
model and the proof-bearing subset still assume capabilities and labels that
remain unselected.

## Part 6: process and documentation weight

Measured at `2256101c` with `ls`, `wc`, and `git`:

| Measure | Value |
| --- | --- |
| Planning Markdown | 101 files, 55,521 lines, 3,270,895 bytes |
| Review and acceptance packets | 41 |
| Plans and plan revisions | 37 |
| `planning/HANDOFF.md` | 4,327 lines, 310,742 bytes; touched by 192 of 303 commits |
| Handoff growth | 182 lines (2026-07-14) -> 992 (07-29) -> 1,641 (09-16) -> 3,195 (10-04) -> 3,472 (10-07) -> 4,327 (10-16) |
| `.github/copilot-instructions.md` | 963 lines, 79,285 bytes |
| Core source (`include/`, `virt/`, `arch/`) | 12,196 lines of `.c`, `.h`, `.S`, and `.lds` (11,555 without the three linker scripts) |
| `model/` (Rocq, C, tests) | 7,081 lines |
| `tests/` tracked text | 123,177 lines (108,574 without JSON; 85,439 without the dropped `tests/r8` and `tests/kvm0`) |
| `bringup/` excluding `results/` | 68,936 lines; B6 19,426; B7 23,392 (`results/` adds 9,995) |
| B7 monitor source versus tests and scripts | 4,621 versus 16,074 lines (3.5:1); B6 4.3:1 |
| Planning text to core source | 4.6:1 |
| Commits | 303; 120 authored on or after 2026-10-06 in their own time zone, of which 45 carry a `docs:` subject (92 and 32 by `git log --since=2026-10-06` in this host's Pacific time zone) |

Interpretation. The exact-commit acceptance model has real value: every claim
in this review could be traced to a cited line, and the B-series records are
unusually honest about limits. But its cost is now visible in three ways.
First, status is replicated across about seven files per change (the
instructions, roadmap, orientation, implementation plan, planning README,
glossary, handoff), which is why Part 5 lists a dozen stale statements:
replication without a single source of truth guarantees drift. Second, the
handoff is a 310 KB append-only log that serves as both current status and
history; it is touched by 63% of all commits. Third, the per-milestone
checkers in `bringup/` are three to four times the size of the monitors they
check, which is the pattern Helium named in its own retrospective:
"verification and evidence machinery can grow faster than the security
design it is meant to clarify." The 2026-10-06 SOP already points the right
way (efficiency, one packet per milestone, no scope creep) and also removed
independent review as standard practice; this review suggests the two should
be separated, since the specification error in S1 was caught by independent
human review and by nothing else.

## Findings

Severity: **high** means it would misdirect S2 or S3 if left as is;
**medium** means it should be decided before or within S3; **low** means it
is housekeeping or a record-keeping gap.

| ID | Area | Severity | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-01 | Security model | high | The policy-specification layer the founding plan expects has never been scheduled or owned; on the policy dimension, S2 as defined evaluates only Model 0.1's runtime-denial trigger. | Part 2; plan L401, L416-L417, L740, L844, L931-L940; Model 0.2 L273-L274 |
| F-02 | Security model | high | TE was priced as a cost from the first pathfinder evidence (2026-07-16), a composition test became the TE adoption trigger (2026-07-20), and the review that was to decide the trigger was removed from Model 0.1's gates (2026-07-22); TE's role as specification stayed in retained sentences and entered no later decision. | Pathfinder evidence L345, L351-L352; Model 0.1 L266-L276 and `9d8407f2` L314-L323; isolation research L470-L480; comparison L19-L21, L73-L93; `4a913842` |
| F-03 | S1 draft | high | The S1 draft applies Model 0.1's trigger faithfully and so concludes from E03 that the TE PoC scenario does not show the trigger fires, which would misdirect S2; H10 rejects Helium's scan as a basis for policy lookup, dispatch, caching, and update without stating the specification role S2 needs. | Part 1 |
| F-04 | Security model | medium | Research inputs were carried into decisions only in part: extensional versus intensional policy, the FLASK decision/enforcement split, seL4's proofs against a policy abstraction, the layered compile-to-canonical architecture, and the "boot-time mandatory policy ceiling" proposal reached no plan, while the comparison kept seL4/capDL's "define the static system state once" and the capability-policy research itself endorsed the trigger-gated direction. | Part 2; capability policy L36-L44, L117-L120, L240, L361-L372, L395-L410; comparison L105, L107; session analysis L79 |
| F-05 | Progress | medium | Against threat model v0, nothing beyond fixed-instance private memory, vCPU state, one directional read-only channel, and refused guest SBI inputs is enforced or tested; Linux is a test payload, not a management domain; B7's isolation is by construction only. | Part 3 |
| F-06 | Progress | medium | B5-B7's monitor layers sit outside Model 0.2, and B6/B7's roots outside R1 sealing (B5's guest runs in the R1-sealed management set), with no model or proof; S2 is expected to write their invariants afterwards. | B6 plan L448, L782; B5 plan L120-L126; Model 0.2 L365; B7 record "has no proof" |
| F-07 | Progress | medium | R8 and KVM0 were dropped without a recorded rationale; no accepted plan now leads to hardware validation; and PMP, optional state, cold boot, `htval`/`htinst`, and VMID width (beyond Linux's preflight report) are uncharacterized by Beryllium. | roadmap "Dropped workstreams"; glossary L28, L58-L60, L146, L149 |
| F-08 | Progress | medium | The expected first MVP milestone is not reconciled with the founding anchor use case; its only recorded rationale is sequencing. | plan L627-L639, L1972-L1976; roadmap "Planned sequence" |
| F-09 | Assurance | medium | Proof coverage is abstract and instance-bound, behind fifteen explicit unproved cut points (five in C) and one substituted plan obligation, with no C refinement, no Sail despite the Stage-1 commitment, no bounded checker ever run on Beryllium code, no coding-profile artifact, and 4,470 unproven HS lines in B7; none of the policy proof targets is addressed. | Part 4 |
| F-10 | Assurance, process | medium | The 2026-10-06 SOP removed independent and deep security review as standard practice without weighing it against the "small enough to audit" requirement; the S1 error was caught only by the responsible human. | handoff L41-L45; B1 record L189-L190; plan L771; open tooling L60 |
| F-11 | Debt | medium | `bringup/` and `tests/unit` are outside the root build; `./be` and `check-be.sh` still assert pre-R7-acceptance and dropped-R8 status; `tests/r8` and `tests/kvm0` (37,738 lines) remain tracked; six embedded pin constants make every root edit heavy. | Part 5 |
| F-12 | Debt | medium | Generated and copied code chains across milestones mean fixes do not propagate and any accepted-source change breaks every port. | Part 5 |
| F-13 | Debt | medium | Tool locks fail on the development host and chain on the R3 lock's digest, bring-up uses unpinned tools, the pinned container is a single copy, and findings S5-S8, S10, the R4 budget, R8 drift, and a failing fresh-clone root gate are open. | Part 5 |
| F-14 | Debt | low | At least twelve maintained statements are stale, including the root README, the hardware inventory, the research synthesis, and the implementation plan's own status lines. | Part 5, stale list |
| F-15 | Process | medium | Documentation is 4.6 times the core source; the handoff is a 310 KB log touched by 63% of commits; status is replicated across about seven files; B-series checkers are 3.5-4.3 times their monitors. | Part 6 |
| F-16 | Goals | low | Community and upstream goals are unmet per the records: no maintainer contact, publication blocked, and no recorded outcome of the October 2026 checkpoint, although the B1 and B2 board runs took place at the LPC venue. | plan L2059-L2085; handoff L79, L96 |
| F-17 | Goals | low | The CHERI alignment requirement is silent in the B-series, the Rust-first tooling preference is unfollowed and unacknowledged, and the K3 hardware inventory has no owner since R8 was dropped. | CHERI alignment L3-L14; plan L1237; hardware inventory |
| F-18 | Goals | low | Founding sections were rewritten in place without a visible decision trail, including all three original immediate gates and milestone 1's use-case gate, and the threat model still assumes unselected mechanisms. | Part 5; commits `3b316566`, `4a913842`; `30aefab7` L900, L977-L980 |

## Options for the responsible human

These are options, not recommendations ranked for you, and none is selected
by this review.

1. **Restore the specification layer (F-01, F-02, F-04).** Approve the
   companion revision plan, `s1-te-trigger-revision-plan.md`: revise S1,
   revise Model 0.1's TE trigger to separate TE as specification from TE as
   runtime check, and widen S2 so that it produces an intensional policy
   (types or labels, rules, and the analyses the policy proof targets name),
   compiled to the canonical manifest, with the pipeline to the Rocq
   configuration restored as a goal. The alternative is to leave S2 as
   defined and accept that the policy proof targets have no owner.
2. **Reconcile the first MVP milestone with the anchor use case (F-08).**
   Decide in S3, or before it, whether the first milestone is the TE PoC
   scenario on two Linux guests, the protected research domain surviving
   host compromise, or the former as a step toward the latter, and record
   why.
3. **Decide what replaces R8's characterization (F-07).** Either recreate a
   bounded K3 characterization package (PMP/Smepmp, VMID width, `htval` and
   `htinst`, AIA guest files, IOMMU visibility, cold boot) before any
   isolation claim between Linux guests, or record that the MVP will rest on
   diagnostic evidence and say so in its claim.
4. **Choose a verification method per claim (F-09).** Options include a
   bounded model checker over the restricted C that R7 leaves as cut points,
   following Helium's pattern and limits; a Rocq refinement for the inductive
   properties; both; or neither until S3. Decide whether B5-B7 are rewritten
   into the modeled seam or remain bring-up scaffolding that the MVP
   replaces.
5. **Separate efficiency from review (F-10).** Keep the SOP's efficiency
   rules and restore independent review for specification-bearing steps,
   starting with S2. A different-model review of exact commits, as this one
   was, is one form; a human domain review is another.
6. **Reduce replication and weight (F-14, F-15).** Make one page the status
   source of truth and have the others link to it; split the handoff into a
   short current-state page and an archived history; cap per-row acceptance
   bookkeeping to what a reviewer needs; fix the stale statements in one
   sweep, under one instruction.
7. **Schedule the debt (F-11 to F-13).** Under S3 or separately: root
   integration with a single pins manifest instead of six embedded constants;
   removal of dropped-R8 text from `be` and `check-be.sh`; a tool-pinning
   model that the development host can satisfy; the S5-S8 and S10 fixes; and
   the R4 budget.
8. **Record the drops and the rewrites (F-07, F-18).** Add a short decision
   record for the R8 and KVM0 drops and for each in-place change to the
   founding text, so the rationale is recoverable.

## Non-claims

- This review ran nothing: no test, build, emulation, proof, or board run.
  Its evidence is the repository's own records, read at `2256101c`, and
  measurements with Git and `wc`.
- It accepts, rejects, authorizes, or selects nothing. Model 0.1, Model 0.2,
  R0-R7, B0-B7, and the step 3 re-baseline stay accepted at their exact
  targets. The S1 draft stays proposed and unaccepted.
- No Helium result transfers to Beryllium. Helium's CBMC figures are as
  Helium's documents record them and were not rerun.
- Nothing here is formal verification or hardware validation of anything.
- The research agents' reports from both runs were checked by the owner
  where quoted, and every figure the second run disputed was re-measured by
  the owner with Git and `wc`; figures neither quoted nor disputed were not
  independently re-derived.
- The second run is a different-model re-read of the same inputs, not an
  independent human review, and it changes no finding's severity. The
  temporary edit to the governance hook was made and reversed for that run
  only, at the responsible human's direction, and is recorded here and in
  the review packet.

## Status record

```text
review_status=accepted
review_target=480dab72de7a74f8b84c64c2fefee8190cb87b70
review_acceptance_instruction=approve-480d-07541
review_acceptance_date=2026-10-18
review_superseded_candidate=65fc52e0b06fc60691669f75d44a1cc9356ac4c0
review_date=2026-10-17
review_requested_by=responsible-human
review_base=2256101c5fb790f3569055479049288ff2235d36
review_s1_target=0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef
review_helium_pin=1c9e52693abe0072ac9b8ce4e0a3ecb5f8bb9489
review_owner_model=claude-fable-5.1
review_agent_model=claude-opus-5.5
review_rerun_date=2026-10-18
review_rerun_agent_model=claude-fable-5.1
review_rerun_base=91d2c108c0326a77619c91b88a4e1c966aeb06bc
review_rerun_governance_hook=temporarily-edited-then-restored
review_rerun_corrections=8
review_findings=18
review_findings_high=3
review_findings_medium=11
review_findings_low=4
review_options=8
review_companion=s1-te-trigger-revision-plan.md
s2_authorization=none
s3_authorization=none
```
