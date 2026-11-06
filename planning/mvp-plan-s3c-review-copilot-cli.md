<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

<!-- Review input, added unedited to the tree on 2026-11-01 under the responsible human's direction
     `also now process the claude cli and codex reviews and iterate as appropriate`.
     Source: the Copilot CLI session's report `s3c-independent-steering-review-2026-11-01.md` in its session files (SHA-256 e6b755f4591f5c5b5184d24f42a96a2b1161e8fe43be2be60a2590677381856d),
     written on 2026-11-01 under the S3-C packet's section 8 brief before the other two reviews were read.
     The body below is the report byte for byte after this comment block; the reconciliation is
     `mvp-plan-s3c-review-reconciliation.md`. -->

# Independent S3-C design review: steering input

**Recommendation: request a revised S3-C before accepting its defaults,
while retaining the proposed MVP 1.0 cut.** The principal problems are
authority/console contracts, conflated proof layers, measurement provenance
and artifact ordering, and a claim-change gate that contradicts M8's goal.

Review date: November 1, 2026 UTC (October 31 in the request's UTC-07:00
timezone). This is an AI-assisted technical assessment for the responsible
human and the project owner agent, not acceptance, implementation authority,
an implementation security audit, or a hardware assessment.

## 1. Decision summary

| Field | Evidence-bound status |
| --- | --- |
| Exact design target | `95c9ab24ba2846eea6d102639abb3482c97989ec` |
| Exact parent | `8b7559d2cc85640172a0f731b86d6ef0eecee2a6` |
| Target change | Only `planning/mvp-plan.md`: 414 added lines; S3-C starts at line 1142 |
| Checkout inspected | Clean `beryllium/mvp-s3c-plan`, HEAD `8a81f1fcc50d81ff00dbb0af0d8825632ad80f5a`; the plan is byte-identical to the target |
| Current design status | Proposed, not accepted; M7-M10 have no implementation in this review |
| Review brief | Only section 8, lines 108-150, of `planning/mvp-plan-s3c-review-summary.md` |
| Independence | The revision was read on its own first, then its specified source inputs. No other S3-C reviews or session histories were consulted |
| Publication/backup boundary | This design is local-only according to the handoff and local refs; no remote-tracking ref or tag contains it. Remote servers were not queried |
| Requested decision | None is made by this report. Its recommendations are steering for a revised proposal and the human's subsequent exact-commit decision |

The direction is worth retaining: a bounded, interactive security-research
platform, a first result about actual C, and inspectable launch identities.
Those benefits do not require devices, dynamic management, a second board,
or attestation in MVP 1.0. The critical question is whether the new console,
proof, and measurement contracts are made explicit without weakening the
existing isolation and evidence boundaries.

| ID | Priority | Steering issue | Primary disposition |
| --- | --- | --- | --- |
| F01 | High | The new console object lacks a defined policy-to-enforcement relation | Make the semantic boundary explicit; bound it in M7 |
| F02 | Medium | Focus, session lifetime, buffering and transcript evidence are incomplete | Fix Q28's premise; specify/test the full M7 protocol |
| F03 | Medium | A protected debug shell is the wrong canonical-anchor default | Change Q27; separate any debug profile |
| F04 | High | M8 conflates contracts, refinement, concurrency and compiled-image evidence | Change Q34 and the proof/qualification wording |
| F05 | Medium | The concrete model's relation and cross-lane invalidation are missing | Reuse the binding model and require final-source applicability |
| F06 | High | Pre-link authority and post-link measurement references are conflated | Separate per-image reference artifacts; name identities precisely |
| F07 | High | One monitor-owned log cannot honestly contain all proposed observations | Separate record origins and correct per-platform attribution |
| F08 | High | M8's new evidence would contradict the unchanged required limit | Add a narrow, conditional limit amendment and supersession entries |

High means a load-bearing design/evidence contract needs revision before
implementation, not that an exploitable implementation defect was found.
Medium items are concrete bounded-plan requirements or owner decisions.
No issue is assigned a CVSS or implementation-vulnerability severity.

## 2. Deliverables and the ladder

### A useful and defensible MVP 1.0 cut

Define usefulness through four reproducible researcher activities, rather
than through the presence of a shell alone:

1. Build and boot a named configuration, then deliberately exercise the
   writer/reader channel and paired denial evidence.
2. Drive the untrusted side of `anchor` while the protected payload retains
   its narrower interface and known computation.
3. Change an authorized scenario/policy input and see either a meaningful
   offline refusal or the corresponding change in authority and behavior,
   without editing the trusted core.
4. Inspect a source-bound C assurance result and a launch-evidence record
   whose assumptions, actual observations, and expected values are distinct.

These are proposed acceptance stories, not claims that RC3 already supports
them interactively. The relevant existing contracts are
`planning/mvp-plan.md:107-139,340-510` and
`planning/project-snapshot-mvp-1.0-rc2.md:101-235`.

| Deliverable | Keep | Boundary to settle |
| --- | --- | --- |
| M7 | Hart 0 as sole physical-console owner; per-domain delivery; a small pinned userland; QEMU scripted sessions | Logical input authority, operator trust, framing/focus, guest lifetime, and semantic rather than merely textual evidence |
| M8 | A separate concrete Rocq development, preservation of accepted proofs, and a bounded C pilot | The exact property, C-to-model relation, concurrency assumptions, source identity, and what constitutes pilot success |
| M9 | Local measurements of launch artifacts and configuration; explicit firmware assumptions; no IMA | Actual policy binding, byte representations, event provenance/completeness, and absence of a hardware-rooted trust chain |
| M10 | An exact integrated candidate and one final board campaign | Final-source proof applicability, final-userland measurements, and no inheritance of stale milestone results |

### The later rungs

**Keep dynamic management in 2.0 (Q33).** A statically bound guest can have
an interactive, bounded session without domain creation, restart, memory
reassignment, or a scheduler. M7 does need an explicit session start/end
contract; that is not a reason to import the whole dynamic control plane.

**Device and service-domain work belongs in 2.0.** Its internal ordering
should be explicit: device/fabric characterization and ownership; interrupt
and DMA containment; a bounded shared-buffer protocol; quiescence and reset;
then restart and authority reuse. These are dependencies, not independent
features that can simply be merged. The existing implementation-plan
milestone 5 already names DMA containment, reset safety, and bounded parsing
as its gate (`planning/implementation-plan.md:2072-2078`).

**Keep implementation of MPT/CHERI experiments in 3.0, but do compatibility
analysis before calling 2.0's architecture final.** MPT changes the physical
protection and M-mode ownership boundary; CoVE is an architecture and ABI,
with several deployment models, not merely another ISA bit to add beside
CHERI. Its HS-only deployment model does not require MPT. A small early
crosswalk of identity, ownership, measurement and ABI boundaries is prudent;
implementing CoVE or a new M-mode component in 1.0 is not. [E06, E07]

**Make general guests dependency-driven, not dependent on experimental
hardware.** Storage/network delivery and a supported guest CPU/ABI profile
can enable useful general Linux workloads independently of CHERI or MPT.
Clarify that the ordinal 3.0/4.0 labels do not make hardware-dependent
experiments a release prerequisite for otherwise ready guest support.
The plan already allows some earlier parallel work; preserve that allowance.

Across the ladder, explicitly allocate these obligations without moving
their implementations into 1.0: safe memory/VMID/object reuse; device reset
and DMA quiescence; update/rollback and attestation-reference policy;
measurement-to-verifier trust and key provisioning; proof invalidation;
supported guest state, including FP/vector decisions; and security
maintenance/disclosure ownership. Retain the separate assurance-release
and upstream gates. A simulated attestation experiment is not that
assurance release.

Do not reopen accepted policy semantics under the label "resolve H06/H07
in 2.0." Security model v1 already defines permission aggregation as union
across rules and conjunction across requested permissions
(`planning/security-model-v1.md:241-257`), and its instances make concrete
type distinctions. Carry those answers forward; evaluate new implications
when new object classes and lifecycle operations appear.

## 3. Claim boundary

This review supports a design recommendation, not a new Beryllium security
claim. RC3's recorded unit tests, emulation, diagnostic board evidence, and
abstract-model results remain at their own exact targets.

Keep these distinctions explicit:

- A shell is an interface, not evidence that arbitrary guests are contained.
- The monitor does not trust either guest for cross-domain isolation.
  Protecting the secret-holding application also depends on what that
  application's own guest kernel, processes, and administrators can do.
- A proved operational model is not a proof of the C that implements it.
  A sequential C contract result is not a concurrent ring proof or a
  GCC/Clang binary-correspondence result.
- A digest and a signature over a digest are not evidence that an untrusted
  measurer actually observed the running object.
- Loader MD5, a host staging SHA-256, self-measurement, and a human debug-state
  observation have different origins and strengths.
- The unmodified accepted R-series/Model/Helium claims do not transfer to
  M7-M10 through reuse, matching test output, or a refreshed hash pin.

No board access, kexec, proof-tool installation, implementation change,
acceptance, merge, push, publication, or release step is part of this review.

## 4. Load-bearing invariants

| Invariant | Existing contract | Required new evidence or decision |
| --- | --- | --- |
| All newly granted authority is explicit and bounded by policy | Security model v1 I8-I11; A3, A6, A8; `planning/security-model-v1.md:118-138,406-463` | M7's logical endpoint representation and its derivation into a sealed per-domain permission; no guest mapping of the monitor transport |
| Input cannot be retargeted across domains or boots | S3-C `planning/mvp-plan.md:1228-1245`; existing static binding | Defined parser, focus and lifecycle state; destination-range and stale-input negative tests |
| Domain output never becomes monitor authority or trusted evidence merely by its text | `mvp/docs/guide.md:404-450` | Preserve stream attribution; test forged success/focus/prelude strings and terminal control data |
| A failed or partial operation publishes no authority | Security model v1 I6/I9; S1 H22 | No dequeue/copy side effects on invalid input; atomic boot/measurement publication under stated assumptions |
| Every advertised proof is about its named source and assumptions | `planning/implementation-plan.md:294-331,1047-1136` | Function/contract/model/source/configuration binding and invalidation at integration |
| Measured identity names the bytes actually consumed | S3-C `planning/mvp-plan.md:1337-1411`; existing M2 measurement contract | Byte/range/phase specification, policy provenance, stage-specific mismatch behavior, complete per-run evidence |
| Historical evidence and current authorization stay separate | Accepted plan release path and S3-C authorization paragraph | A new exact proposal after revisions; no report-generated acceptance |

## 5. Findings and steering recommendations

The priorities below are design/evidence priorities, not vulnerability
severities. A finding describes an under-specified or conflicting proposed
contract; it does not claim an exploit in code that does not exist.

### F01. Console authority needs a semantic design, not just a declared object

**Priority: high. Confidence: high.**
Target: `planning/mvp-plan.md:1232-1245,1498-1502`.
Supporting contract: `planning/security-model-v1.md:95-113,267-283,406-446`.

M7 says console input is an inventory/policy object, derived and sealed like
the existing resources, with no other notation change. That is the right
intent, but it does not supply the representation or enforcement relation.
V1's channel analysis connects channel permissions to matching memory rules
and equates declared flows with shared-storage flows. The proposed transport
is monitor-owned memory, read by a domain's HS handler and copied into that
domain's private guest RAM; it is not a guest-mapped shared page.

The bounded plan must decide whether this is a logical console endpoint
class or a precisely defined adaptation of existing classes. Preserving the
surface grammar is quite possible; preserving all existing *semantics*
without explanation is not established by saying the grammar is unchanged.
Giving a guest a mapping of its HS input ring to satisfy a storage-based
analysis would be the wrong solution.

**Steering:** keep the transport inaccessible to every guest root; derive
an explicit input permission and endpoint binding at seal time; identify
the trusted input source; specify how the offline report and analyses
represent that mediated flow. An SBI handler can consult an already derived
permission without introducing a runtime TE policy interpreter. If the
representation changes security-model semantics, present a narrow additive
revision for human decision rather than bypassing the accepted-document stop.

Also decide which scenarios opt in. `two-guests` is explicitly the policy-free
control in `mvp/docs/claim.md:46-48`; "every domain's console input is written
in the policy" should not silently alter that control's meaning.

### F02. M7 needs a complete console/session contract

**Priority: medium; required before M7 implementation. Confidence: high.**
Target: `planning/mvp-plan.md:1220-1264,1512-1515`.
Supporting contracts: `planning/mvp-plan.md:347-395,543-558`;
`mvp/docs/guide.md:404-450`; the `limits`, `accepted_exits`, and `expect`
objects in `mvp/scenarios/te-poc/scenario.json` and
`mvp/scenarios/anchor/scenario.json`.

The proposed hart-0 input path is a sensible small architecture. One
physical console does not require a second UART, guest interrupt injection,
or a driver stack in HS. Linux v7.2's HVC SBI driver already has a DBCN read
handler, and OpenSBI v1.6 implements that function; neither fact establishes
that this board's physical console supplies input. Keep the planned
characterization. [E01-E03]

What is missing is the contract around that path:

| Boundary | Requirement to fix in the M7 plan |
| --- | --- |
| Firmware read | Nonblocking/empty/partial/error behavior; bounded polling; HS-owned scratch, not a forwarded guest pointer |
| Guest destination | Full-width address and length validation, overflow and end-boundary cases, checked GPA-to-HPA conversion, writable own-window restriction, and no consumption on a refused request |
| Input rings | Capacity, one writer/reader, publication/consumption ordering, wraparound, backpressure/drop accounting, and no overwrite of unread data |
| Focus | Reserved control grammar plus escaping, malformed/partial-sequence behavior, explicit acknowledgement, and rules for bytes already queued or partly typed |
| Lifecycle | A session-ready point, bounded interactive lifetime, explicit finish/abort, behavior on pause/termination, and no delivery across reboot or run boundaries |
| Scheduling of console work | Input polling must not make console output, management acknowledgements, or terminal processing unbounded; no new availability claim is required |
| Guest-side demonstration | Name the helper commands and their accepted fault behavior; a random shell command or arbitrary fault must not be assumed to satisfy the old exact-exit contract |
| Presentation | Prompts without newline, partial lines, echo, CR/LF, editing/control characters, and interleaved domain output |
| Automation | Each send tied to the current run/domain/step; abort on reset, unexpected boot banner, timeout, disconnect, or loss of routing state |

"A sequence no guest shell uses" is not a protocol definition. Arbitrary
input/pastes can contain any chosen sequence; shells and terminal clients
also have control conventions. Reserve and escape a sequence, or start with
a deliberately limited line-oriented interface and specify that limitation.
Do not put a general terminal emulator or line editor in HS.

Guest output is untrusted. Terminal controls can change the display and
elicit input-side replies; a domain prefix alone is not a trusted UI if
the data after it can control the terminal. [E04] Preserve the current
printable, source-attributed evidence boundary, or define explicit escaping
and a trusted host-side renderer before widening it for BusyBox.

The current finite fixtures also compute, report, and shut down by
themselves. "The shell is in addition" does not define how the researcher
gets time to interact or how a successful session ends. Use an explicit
interactive scenario/profile with bounded helper commands and build-time
limits; retain the existing finite fixtures as regression controls. This
does not require dynamic domain management.

**What scripted sessions should prove:** a byte/command reaches only its
selected, authorized domain; malformed destinations and control sequences
are rejected without cross-domain effects; empty/partial/full-ring cases
have their declared outcomes; and focus switches, pause, termination and
reset do not leak stale input. Check prompts without newlines and an idle
session, not only pre-scripted fast commands.

For the isolation demonstrations, correlate the command, domain, trusted
monitor denial, guest signal report, address/cause, and unchanged data.
Retain the existing semantic checker. A transcript regex that matches an
echo or a guest's fabricated `RESULT pass` is not sufficient. Include
deliberately wrong-focus, forged-marker, missing-event, duplicate-event,
and unexpected-reboot tests.

### F03. Do not make the canonical protected anchor a debug shell by default

**Priority: medium; an explicit Q27 decision is needed. Confidence: high.**
Target: `planning/mvp-plan.md:1250-1255,1511`.
Supporting contract: `planning/mvp-plan.md:403-466`;
`planning/security-model-v1.md:145-198`.

A shell in the protected domain does not by itself defeat G-stage isolation.
Nor is a physical lab operator necessarily an attacker in the selected
threat model. The problem is the default: placing the secret and computation
in a `nolibc` process does not isolate them from another sufficiently
privileged process in the same Linux guest. It enlarges the interface and
software involved in the protected application's behavior, and creates an
administrative input path whose trust must be stated.

**Steering:** change Q27 to its alternative for the canonical anchor:
shells in `te-poc` and the untrusted anchor domain, no general shell in the
protected anchor. If useful, provide a separately named debug-anchor profile
with test-only material, an explicitly trusted operator, a distinct measured
configuration, and no claim that it has the canonical payload's narrow
interface. Do not frame this as a need to redesign Linux process isolation or
add another hart in MVP 1.0.

This distinguishes the monitor's isolation TCB from the protected
application's own software and administrator assumptions. It does not
reclassify every Linux guest as trusted by HS.

### F04. M8 must separate four proof layers and choose a better first leaf

**Priority: high. Confidence: high for the boundary problem; medium for
the preferred tool selection until the pilot runs.**
Target: `planning/mvp-plan.md:1288-1310,1332-1335,1518-1521`.
Supporting contracts:
`planning/project-snapshot-mvp-1.0-rc2.md:273-304`,
`planning/implementation-plan.md:1047-1136`.

The central sentence promises that `mvp-ring.c` is refined to its stage-1
function by CN and Frama-C/WP. The same paragraph correctly asks about the
gap between a contract proof and refinement, but its promise presumes the
answer. Four separate obligations are involved:

| Layer | What must actually be established |
| --- | --- |
| Per-call C contract | Preconditions, result, memory footprint, rejection behavior and relevant runtime-error obligations in the named tool's C semantics |
| C-to-Rocq relation | The contract/model correspondence and observable behavior relation; not merely two specifications with similar prose |
| Concurrent protocol | What interleavings and memory ordering are modeled, who owns each word at each phase, and why callers satisfy the per-call assumptions |
| Compiled execution | How the locked compiler/assembly/executor preserve the accesses and ordering; explicitly assumed where no binary correspondence exists |

No assessed candidate supplies all four merely by accepting a leaf.
Exporting a verification condition to Rocq does not automatically connect
production C to the project's operational model. Two SMT backends can
cross-check solver answers, not the shared frontend, memory model, or
specification.

The ring is particularly awkward as the *first tool-comparison leaf*.
It accesses shared `volatile` index words; ordering is explicitly its
callers' responsibility (`mvp/src/mvp-ring.h:12-20,82-85`), not a property
implemented solely inside the leaf. GCC documents that ordinary memory
accesses are not ordered merely by a `volatile` access. [E14] The snapshot
explicitly named RVWMO/fence assumptions; S3-C's stage-1 description no
longer says whether its ring/barrier model is sequentially consistent
or accounts for those assumptions.

**Steering:** choose Q34's existing alternative,
`be_mvp_denial_decide` and its necessary static helpers
(`mvp/src/mvp-sbi.c:195-318`; contract in `mvp/src/mvp.h:920-922`).
It reads captured/private inputs, writes a result, has bounded iteration,
and avoids shared volatile state. This is a security-significant leaf,
not an artificial arithmetic exercise.

Keep the ring/barrier protocol in the concrete-model lane. State the memory
model explicitly. An SC model is a useful first result only if labeled SC
and not promoted into an RVWMO implementation claim. If using RVWMO
assumptions, enumerate the publication, acquisition, reuse and compiler
correspondence obligations; small ISA-level litmus checks can challenge
them, but are not a C refinement proof or general hardware validation.
Do not change working monitor semantics merely to make the pilot easier. [E21]

#### Tool choice and annotations

| Candidate | Recommendation and rationale | Boundary that must remain visible |
| --- | --- | --- |
| Frama-C/WP | First practical candidate for the pure leaf's sequential contracts; ACSL and the open annotation importer support sidecar specifications | Frontend/VC generation, selected memory/arithmetic model, runtime-error obligations, solver/Why3 chain, and any assumptions in exported proofs |
| CN | Keep the same-leaf comparison, but initially non-load-bearing under the existing promotion rule; strong alignment with the Cerberus direction | Sequential ownership assumptions; exact supported subset; no inference that its current Rocq proof-log path independently checks every SMT obligation |
| VST | Valuable for a Rocq-native Clight contract/proof route, not an automatic production-C-to-project-model bridge | A fully open source-to-Clight path must be established; the proof library's license alone does not establish that |
| CBMC | Bounded complement and shared-mutant cross-check, not the refinement vehicle | Harness assumptions, reachability/vacuity, bounds/unwinding, intentional arithmetic wrap, and the modeled environment |

These are proposed roles, not tool qualification results. The tools'
handling of shared/volatile accesses differs; neither removing qualifiers
nor disabling interference modeling is an acceptable way to make them agree.
Some frontend behavior in the research memo was inferred from source, not
tested. Qualifying that behavior on discriminating examples is an M8 task,
not a result of this review.

There are concrete reasons not to promise a turnkey Rocq route. The assessed
CN commit's proof-log code still defines an unrestricted placeholder for
SMT provability; that does **not** make CN's ordinary solver checks
meaningless, but it is not independent certificate replay. [E16] The WP
support library includes axioms/admitted facts; whether a particular
exported goal depends on them must be shown by its assumption report.
No WP export or project proof-gate failure was executed in this review.
[E17]

The **current** local model lock is `proof_assistant=rocq-9.3`
(`model/toolchain.conf:7-14`), not the historical 9.2 profile in the old
evidence document. The assessed Frama-C 33.0/Why3 upstream version
constraints do not establish a supported export path to that lock.
Downstream patches may change the outcome; it must be qualified in the
actual evaluator. Do not downgrade the accepted model environment or
weaken its assumption checks to get an experiment through. [E17, E18]

For VST, the assessed conventional `clightgen` route calls `SimplExpr`
and `SimplLocals`; these passes are outside the inspected CompCert
license's LGPL exception list. Therefore a BSD-licensed proof library
does not clear the project's fully-open-tool gate for that whole route.
Do not select it normatively without resolving the extraction dependency
under the existing policy. This does not rule out another fully open
frontend or proof route. [E19]

**Keep Q37's sidecar default, with a per-tool method.** WP's importer can
attach contracts/loop annotations, so tie positional annotations to the
source hash and test that they bind the intended loop. VST specifications
live in Rocq. CN can keep some specifications outside the body but may
need injected loop/ghost annotations: use a pinned transformation in
scratch, prove correspondence to the exact production/preprocessed input,
and compare emitted executable code/data under the locked compilers.
If that cannot be made reliable, the explicit in-source-comment
alternative is better than a hand-maintained duplicate implementation.

#### A bounded, non-vacuous pilot

Before running a verifier, freeze the function/helper set, headers,
configuration, bounds, contracts, failure behavior, expected claim and
explicit exclusions. Independently review the specification; the producer
of the implementation must not be its sole approving authority.

Require meaningful valid/invalid examples and mutations that distinguish
the intended contract from plausible wrong implementations. Check
runtime-error obligations, reachable postconditions and consistent
preconditions. For CBMC retain unwinding assertions, justify every
assumption, model shared observations explicitly if a later ring harness
is added, and do not use partial-loop behavior as a substitute for
completed bounded checking. Treat intended unsigned wrap explicitly.
[E20]

The result must say **contract-only**, **refinement relation established
under named assumptions**, or **unsupported/incomplete** as appropriate.
Do not require two successful tools if one fails its qualification test;
record that failure and withhold that tool's claim. Conversely, if neither
can meet M8's chosen proof goal, a negative feasibility result is valuable
but does not mean the milestone's positive exit or RC4 prerequisite has
been met. Return that outcome for a human rescope decision.

### F05. A separate concrete model is right; an unrelated model is not

**Priority: medium. Confidence: high.**
Target: `planning/mvp-plan.md:1288-1296,1415-1423,1433-1439,1519`.

Keep Q35's separate-model direction. Model 0.2's fixed enumerations and
single-hart state are the wrong place to force in an MVP runtime instance.
But there is already reusable MVP-shaped abstraction:
`model/proof/Binding.v` defines ring ownership, barrier phases, transition
footprints and H3. It explicitly excludes the concurrent implementation.
Do not build a second, unrelated abstraction and call a list of similarly
named theorems a transfer.

The new development should import the accepted modules unchanged and state
an abstraction/simulation relation: how concrete states project to the
binding/policy view, which concrete writes are permitted by each abstract
transition, and which old properties follow. List properties that do not
transfer. In particular, formal model results plus agreement tests do not
prove the runtime's policy-to-root connection.

Use concrete extents and bounded parameterized representations where they
fit, rather than another closed enumeration copied from the current image.
That preserves the option of a later generalized model without requiring
a Model 0.2 rewrite now. Explicitly supersede the accepted ledger's U-13
statement assigning generalization to the first verification plan
(`mvp/docs/claim-ledger.md:92`); Q35 instead assigns it to 2.0.

**The lanes are parallel, not independent.** Today's inbound ring already
carries control records from hart 0 to the domain hart. M7 either adds a
record kind or a separate input ring; either changes the record grammar,
layout, or ownership footprint used by M8. The precise choice also affects
whether input backpressure can interfere with management acknowledgements.
M9 changes the measurement that M8 proposes to model. These are semantic
dependencies, not solved by re-rendering the ledger.

Narrow M8's first operational work to the ring/barrier and the selected
decision relation. Defer the full M9 measurement protocol or model only
its abstract measure-before-entry gate, explicitly withholding a proof of
M9's implementation. Freeze a small shared contract set before the lanes
diverge.

For each proof, bind the exact function, headers, record grammar, layout,
configuration, model, contracts and compiler assumptions. A changed input
invalidates applicability until it is re-established. M10 already re-runs
M8's gates; add the requirement that those gates consume the **final
integrated source**, or demonstrate the exact equivalence on which the
retained proof depends. Passing an old isolated model while building a new
monitor must not count as final-source evidence.

#### Disposition of H41's actual conditional recommendations

The source was read at Helium commit
`1c9e52693abe0072ac9b8ce4e0a3ecb5f8bb9489`,
`docs/fv-pathfinder-lessons.md`, blob
`fcbe54b27bdc0fb7802e55762e500e1b90598589`.
These are proposed dispositions for Beryllium, not new Helium status.

| H41 stage and source lines | Disposition for M8 |
| --- | --- |
| 1, 464-476: choose a security-significant seam without deleting its meaning | Adopt; use the pure denial decision for the first C pilot and keep the live caller/effect relation explicit |
| 2, 478-491: contract/admission checklist before harness construction | Adopt; pin source, bounds, I/O, rejection and non-mutation, non-goals, examples and the exact successful claim |
| 3, 493-504: qualified, pinned tool use with good/bad/vacuity/unsupported-feature probes | Adapt to all selected deductive/bounded tools and their dependency chains, not only CBMC |
| 4, 506-515: structurally independent specification and recorded specification review | Adopt; no copying production helpers into the oracle and no sole implementer approval |
| 5, 517-532: named mutation taxonomy and disposition of survivors | Adapt to the selected MVP leaf/protocol and use the same meaningful mutants across candidate tools |
| 6, 534-548: machine-readable source-bound evidence | Adopt; artifact consistency is not an independent proof replay |
| 7, 550-565: clean reproducible evaluator without obscuring the security question | Adopt; keep the qualifier and proof artifacts no larger or more indirect than necessary |
| 8, 567-580: separate automation, exact commit, review and human approval | Adopt; this report grants no gate |
| 9, 582-598: explicit success/stop criteria and valid negative feasibility outcomes | Adapt to deductive obligations and assumptions; a useful negative result does not silently satisfy M8's positive proof exit |

Resolve H38 as **adapted bounded checking per named claim**, not adoption
of Helium's complete suite or a transfer of its results. Keep H22's
captured-input correspondence obligation and H40's warning that correct
pure modules do not prove correct integration.

### F06. Separate identity kinds and break the pre-link/post-link dependency

**Priority: high for the reference-artifact design; medium for identity
naming. Confidence: high.**
Target: `planning/mvp-plan.md:1362-1374`.

**A suspected missing policy binding was ruled out.** The existing policy
report's `configuration_identity` already hashes the manifest, policy, and
labeling identities. `policy_identity` hashes the actual policy file bytes.
The composite is linked into the image and included in `anchor`'s M2
measurement. The research lane checked this with an in-memory comment-only
policy mutation in both policy scenarios: the checks still passed, the
policy and composite identities changed, and `core_identity` did not.
Do not report that the current policy is simply unbound.

The real ambiguity is that M6's `core_identity` is a different value: the
SHA-256 of the canonical inventory/proposal words. It is deliberately
policy-independent, computed at boot, and currently printed in abbreviated
form. The older `configuration_identity` is a build-derived linked constant.
Calling either one "the policy's" digest obscures what was measured and what
was asserted by the build.

The source trace is `mvp/tools/policy-check.py:35-41,641-649,687-784`,
`mvp/src/mvp-core.h:29-46`, and
`mvp/src/mvp-runtime.c:271-316,377-378,1380-1423`. Image/capture checks bind
the report and linked value; this is not a new runtime-proof claim.

**Steering:** name at least:

| Identity | Origin and interpretation |
| --- | --- |
| `core_identity` | Monitor-computed digest of the canonical enforced configuration; log all 32 bytes |
| `configuration_identity` | Recorded build composite binding manifest, policy and labeling; do not relabel it a runtime policy measurement |
| `policy_identity` / `labeling_identity` | Explicit source identities in the reference evidence, checked against those source artifacts |
| Image/self-region digests | Values for the exact linked image, toolchain and variant, not a generic per-scenario value |

For `two-guests`, record policy absence explicitly rather than inventing a
policy identity or silently using a default. Keep policy parsing out of HS.
The checker should bind the two configuration identities through the
scenario/reference record; it must not compare them as if they were the
same hash.

**The post-link dependency needs an explicit solution.** Today's authority
report is produced before monitor compilation and is shared by the GCC and
Clang builds. M9 proposes putting the expected self-measurement in that
report, but the value depends on the final image, including toolchain and
negative variant. Moreover, an expected self-digest cannot be fed back into
the very bytes it hashes without a circular definition.

Retain the pre-link authority report as an input. Generate a separate
**post-link, per-image reference manifest** binding that report's hash,
the exact source/configuration/toolchain, the ELF and boot-image hashes,
the measured range table, and expected results. A human-facing assembled
report can link both. Do not solve the dependency by silently excluding
arbitrary bytes from measurement or by treating a pre-link hash as a
measurement of the final image.

Define the runtime objects by the bytes the monitor actually places and
uses. Currently the initramfs is embedded in the Linux `Image`; placement
handles the Image and DTB, and M2 additionally measures the secret page and
the linked composite identity (`mvp/src/mvp-payload.h:75-98`,
`mvp/tools/policy-check.py:757-767`). Either retain that representation or
name an exact separately identifiable initramfs range. Do not add a cpio
parser to HS just to produce a second digest of already covered bytes.
Specify ordering relative to decompression, relocation, DTB modification,
page placement, sealing and first entry.

**Keep self-measurement, but keep it modest.** It is useful as a post-link
consistency diagnostic if the measuring/reporting path works; it is not an
independent check of an adversarial or arbitrarily corrupted monitor.
Prefer recording it for the external checker rather than adding an in-image
self-approval mechanism. Name every text/readonly/input range and any
exclusions. The reference value stays outside the measured image.

### F07. M9's log conflates observations with different producers and trust

**Priority: high. Confidence: high.**
Target: `planning/mvp-plan.md:1359-1374,1379-1398,1409-1411,1473-1476`.

The loader digest is read from the capture, but the proposed combined log
is in a monitor-owned page. No current handoff supplies that digest to the
monitor. It covers the **whole boot-image file**, including payloads, not
just monitor code. More importantly, the three execution paths differ:
the board supplies MD5, the U-Boot rehearsal supplies CRC-32, and direct
QEMU boot supplies no loader digest.

Those are source facts, not newly assessed board behavior:
`mvp/tools/k3-env.sh:91-93`, `mvp/shim/mvp-shim.S:5-19`,
`mvp/tools/k3-stage.sh:19-39`, `mvp/tests/uboot-rehearsal.sh:22-26`,
and `mvp/tests/run-qemu.sh:231-232`.

**Do not add a new trusted handoff merely to make the diagram look like a
chain.** Keep three classes in the run's evidence envelope:

| Class | Producer and checking rule |
| --- | --- |
| Monitor log | Hart 0's measured values and explicitly labeled build-recorded constants; checked against final-image references |
| Loader observation | Host-captured loader line, algorithm or explicit absence, byte count, staged-file SHA-256, and capture/staging provenance |
| Platform observation | Human/tool observation of a named board at a stated time, with raw evidence and an explicit unchanged-state assumption |

MD5 remains useful for selecting among honestly staged, distinct files.
Binding that selector to a host-computed SHA-256 does **not** upgrade the
loader's MD5 to collision-resistant authentication. A malicious loader or
untrusted evidence producer is not excluded by that binding. Retain the
trusted-firmware/lab-host assumptions and call this provenance-linked local
launch evidence, not a hardware-rooted chain of trust. [E08, E09]

The Q40 observation is likewise not reproducible from build inputs.
Clarify stop (c): build-derived digest/reference mismatches are one class;
unavailable or contradicted platform observations are another. Permit
`not determinable` as an honest observation requiring disposition, not a
fabricated security state or a reason to write a fuse. A human observation
does not establish that a lifecycle/debug state remains unchanged forever.

**Suggested claim shape, for the later plan to fix:** the monitor records
local launch identities for named artifacts; the checker compares them
with final-build references; loader attribution is MD5 on the board,
CRC-32 in the U-Boot rehearsal, and absent in direct QEMU. Nothing below
the observed loader is measured by this work, and no authentic root,
cryptographic freshness, or adversarial self-measurement guarantee follows.
Keep the current firmware and non-attestation limits.

#### A minimal format with a credible upgrade path

Use a bounded, versioned monitor record format and an offline JSON
representation inspired by the TCG CEL information model. Do not claim CEL
or systemd conformance until an actual adapter and its tests exist. JSON
need not be parsed or generated in HS. [E10, E11]

The bounded plan should fix:

1. A header: schema/version, platform and scenario identity, run/boot
   context, record count/capacity, and algorithm namespace.
2. Each record: monotonically ordered record number; origin
   (`monitor-computed`, `build-recorded`, or later `guest-asserted`);
   phase; domain and object identity; algorithm and full digest; exact
   byte count and measured representation/ranges.
3. Canonical encoding and independent vectors for any event digest.
   Distinguish a payload digest from a digest that also commits to its
   object/domain/phase metadata. Do not leave authoritative labels
   unauthenticated in a future quote merely because the payload hash matches.
4. A boot-log close record before first entry, with the expected count.
   No unexplained duplicates, missing records, trailing events, truncation,
   or runtime overflow; no silent dropping. Static capacity is checked at
   build time and runtime still fails closed on an exceeded bound.
5. A zero-initialized, monitor-only storage region with one writer and a
   defined publication/read-consistency rule. Reset is not assumed to erase
   old RAM. Host observation of that page is a separate operation.
6. A per-path host envelope for loader and platform observations. Preserve
   their real provenance; do not promote them into monitor-origin records.
7. Explicit mismatch handling: which values fail closed before entry,
   which are rejected by image checks, and which can only invalidate a run
   in the external checker.

A replayable hash accumulator can be a small optional experiment; a purely
software accumulator writable by its own measurer adds no root of trust.
Do not add PCR reset/extend or a vTPM interface to M9 merely to imitate one.
Sequence numbers and close records give useful completeness checks, not
cryptographic replay resistance.

Required negatives include wrong/missing/duplicate/out-of-order records,
swapped domain/object labels, altered lengths, incomplete logs, a wrong
reference image/toolchain/variant, absent loader evidence on a path where
it is required, and a false platform-fact binding. Keep M2's actual
pre-entry measurement refusal; do not pretend every diagnostic-only
measurement has a monitor-enforced golden value.

The present secret is a public test value. Preserve that disclosure and
do not label hashing it a confidentiality defect. Before real secret
provisioning, separately decide whether public digests/commitments reveal
information or permit guessing, how secrets enter the domain, and what
measurement may include. No new secret-management mechanism is needed in
MVP 1.0.

#### systemd, Amutable, and the simulated root

The useful systemd precedents are canonical image/section identities,
precalculated reference values, component variants, phase separation,
event-log replay, and separation of evidence from policy and verifier
results. `pcrlock` is more than an expected-digest file: its TPM-backed
work includes reconciling events with PCR state and constructing an
authorization policy. `systemd-measure` is the closer reference for
offline prediction. A custom SBI extension is not a TPM protocol and
stock TPM-dependent guest paths will not automatically consume it.
UEFI `systemd-stub` also does not become part of the present boot chain
by adopting its terminology. [E10-E12]

Keep Q39 analysis-only. A future interface must separate guest-asserted
events from monitor-observed launch identities, bound its buffers and
quotas, define reset/epoch semantics, and preserve hart 0's log ownership.
Whole-image/configuration/policy measurements at the domain boundary do
not reintroduce IMA. Do not ship a per-file guest measurement agent, add
file-access measurement semantics, or portray arbitrary guest assertions
as trusted monitor observations.

The company's own name is **Amutable**, with one middle `m`. Correct the
proposal's references, without rewriting historical human quotations.
Its published image/configuration-as-artifact and predicted-state
approach is useful design input; its product assurances do not transfer
to Beryllium. [E15]

For 2.0, prefer a **lab observer with independent measurement access**, if
the human's read-only characterization establishes it, over a signer that
merely accepts monitor-provided hashes:

| Candidate | Honest experimental role and limitation |
| --- | --- |
| JTAG observer | Read named memory ranges/state at a verifier-chosen point; document halt and cache/system-bus coherence, exact range selection, and the open-debug bypass assumption. This is a lab-observed snapshot, not proof of continuous execution or boot history |
| ESP32 dongle | A reset/freshness controller, or a separately implemented transcript witness if wired to observe output. Reset alone does not measure the target |
| ESP32/management chip signing monitor data | An attestation-protocol rehearsal under trust in the reporting software; a signature does not make the measurements independently observed |
| GPIO | A transport/control mechanism, not a root of measurement |

A point-in-time external observation requires its own trust assumptions,
challenge/session binding, key custody and verifier policy. Debug system-bus
access is not automatically coherent; a halt changes live execution state.
Neither the debug path nor the management chip's capabilities have been
established here. [E08, E13] Keep those experiments in 2.0 and revisit
stop (a)'s blanket "debug state" wording there rather than silently bypass
it.
M9 should record the human's Q40 observation, not implement an attestation
key/quote protocol or automated debug access.

### F08. The claim-change gate contradicts the intended new evidence

**Priority: high. Confidence: high.**
Target: `planning/mvp-plan.md:1326-1329,1453-1457,1471-1481`.
Supporting contract: `mvp/docs/claim.md:49-59`.

M8 is supposed to establish something about actual monitor C, but it may
change no claim text. The current required limit expressly says the rings
and the rest of the implementation are covered by tests and checks "and by
nothing else." Adding a source-bound C proof to the ledger while retaining
that universal sentence makes the release surfaces inconsistent. M7's
one-sentence addition also needs to account for the changed userland and
operator boundary in the required limit.

**Steering:** pre-authorize only the necessary evidence-accurate amendments
to the required limit, fixed in the corresponding bounded plans. Name the
proved functions, proof kind, exact source and assumptions, and leave the
remainder explicitly unproved. Keep every forbidden umbrella claim and the
compiler/assembly/firmware/hardware exclusions. This is not authorization to
say that the hypervisor as a whole has been verified.

The supersession table must also reconcile D7 and the method-per-claim
table (`planning/mvp-plan.md:566-589,635`), and distinguish M8's pilot from
the still-excluded assurance release/C-refinement program at line 252.
State explicitly that CN/WP promotion, if proposed, must meet or deliberately
revise the existing qualification gates in
`planning/implementation-plan.md:1101-1155`; it does not follow from a
packaged tool or a successful pilot alone.

### Q27-Q42: complete default disposition

| Question | Recommendation | Reason or condition |
| --- | --- | --- |
| Q27 | **Change** to no shell in the canonical protected anchor | F03; any debug-anchor profile is separate and measured as such |
| Q28 | **Replace the premise** with a reserved, escaped control grammar | F02; no universally unused input sequence, and focus/lifecycle acknowledgements must be specified |
| Q29 | **Keep**, complete the build contract | Pin BusyBox, musl, configurations, compiler/runtime dependencies and initramfs construction; check the existing no-FP/no-vector ABI and image limits. musl supports soft-float variants; compatibility of the actual build is still to be established [E05] |
| Q30 | **Keep** QEMU for both compilers plus the board campaign | F02; require state/denial/data correlation and hostile transcript/routing cases, not pattern matches alone |
| Q31 | **Keep with an early characterization gate** | Do the unknown firmware-input probe when the board is free, before depending on that capability; do not call pending board behavior established by QEMU |
| Q32 | **Keep**: COM260 only for 1.0 | A second platform is not required for the bounded claim; adding it later requires its own evidence |
| Q33 | **Keep** dynamic management in 2.0 | M7 needs bounded session lifecycle, not dynamic domain lifecycle |
| Q34 | **Change** first C pilot to `be_mvp_denial_decide` | F04; model ring ordering separately. A second leaf is an explicitly bounded extension, not automatically added because time remains |
| Q35 | **Keep**, add a relation to accepted binding/policy abstractions | F05; supersede U-13 explicitly and do not duplicate a disconnected fixed model |
| Q36 | **Keep**, define qualification and the ledger role | F04; source/options/bounds/assumptions/mutations/vacuity all recorded, with no concurrency/refinement claim from bounded checking |
| Q37 | **Keep with tool-specific mechanics** | Sidecars are feasible for WP; CN may need checked annotation injection; preserve exact source correspondence |
| Q38 | **Keep the firmware unchanged**, change attribution wording | F07; MD5 is the board loader observation, not a SHA-256 trust anchor; other paths differ |
| Q39 | **Keep analysis-only** | No guest PCR/vTPM/quote interface in 1.0 just because it appears small; separate guest assertions from monitor observations in 2.0 |
| Q40 | **Keep human-only/read-only**, clarify record class | F07; time-bound platform observations, allow inability to determine state, and never infer continued debug security from one probe |
| Q41 | **Keep per-plan soft limits**, narrow M8's mandatory result | Historical line counts are not a concurrency/refinement estimate. Count model, contracts/bridge and tool glue separately; reevaluate a limit rather than cut correctness |
| Q42 | **Keep** this separate steering review and the existing SOP | No blanket new review bureaucracy; do record who independently assessed the specification and assumptions used for the new proof claim |

### Additional stop/decision conditions worth stating

Do not make every ordinary failing unit test a new human authorization
request. Normal in-scope bugs should be fixed. Stop when the remedy would
change a load-bearing boundary, or when a board session loses its
execution/evidence state:

- The console design requires guest access to monitor transport memory,
  undeclared input authority, a weakened buffer check, or unexplained
  cross-domain/run input delivery.
- A scripted send loses its current run/domain/phase binding or observes
  an unexpected boot/reset; never finish a buffered script using old
  prelude markers.
- The selected userland needs new guest architectural state or a boot/
  memory-layout change outside the bounded M7 plan.
- A verifier silently changes the meaning of an accepted construct,
  succeeds only under unjustified/vacuous assumptions, or cannot preserve
  correspondence to the production input.
- A proof-to-source or cross-lane contract changes without renewed
  applicability evidence; an old model passing is not a waiver.
- A reference artifact becomes self-referential, an event cannot be
  assigned an honest origin/representation, or the measurement log loses
  completeness or exceeds its declared capacity.
- A real secret, persistent debug/lifecycle change, guest measurement
  service, key provisioning or quote protocol is needed outside the plan.

The existing shared-board, no-kexec, firmware, accepted-byte, and public
release gates already cover their subjects. Preserve them rather than
inventing replacement permissions in this report.

## 6. Evidence, independence, and limitations

The coordinating assessment is by GPT-6 Astra, assisted by two read-only
Claude Opus 5.5 research agents at maximum effort: one for M8's formal
methods/tool feasibility and one for M9's measurement/attestation design.
They are supporting research lanes, not three independent votes or human
reviewers. Neither was allowed to inspect other S3-C reviews.

The specified comparison, snapshot sections 5/6/8, accepted plan body, claim,
and named S1 rows were used as source inputs, not as substitute verdicts.
Additional narrowly relevant source contracts and primary upstream
documentation were consulted. Existing implementation declarations were
used only to calibrate the proposed interfaces and proof boundaries, not to
conduct an unrequested code-vulnerability audit.

### Provenance and checks performed

The workspace anchor was read through the mandated logical path; `pwd` and
`pwd -P` agreed. The tasking resolver returned no open Project Manager
requests. Its `workspace://SOT.md` SHA-256,
`7fa17e4eaf4fb37096f4bd2aef853e399b025e4d3271d88db5cee6ac02284552`,
matched the actual anchor. No PM task was adopted or changed.

Read-only Git checks established the target, parent, changed-file inventory,
clean checkout, relevant source equivalence, and local refs. The plan's
SHA-256 was
`e96020b1052a78ae6a5d799d1f1df6dc6062e62c7c0b282025ae9699c605fb92`.
The development branch was at
`8b7559d2cc85640172a0f731b86d6ef0eecee2a6`; its last-fetched origin ref was
`30cab19832033def79a89cde2bea1e96fe33cf99`, six commits behind and none
ahead. These are local-ref observations, not a live remote backup check.

The measurement research lane additionally ran a read-only, in-memory
policy-comment mutation using the existing checker functions for `te-poc`
and `anchor`. It established the identity dependency described in F06,
including a changed anchor composite digest with dummy kernel/DTB inputs.
That check rebuts a proposed missing-binding finding; it is not an image,
hardware, or runtime measurement test.

No implementation build, QEMU run, proof replay, C-verifier qualification
experiment, or hardware operation was performed. The report must not be
used as evidence that any proposed M7-M10 behavior works.

Two research assertions were deliberately narrowed before consolidation:
the current model lock was re-read and corrected from historical Rocq 9.2
to `rocq-9.3`; and a prediction that WP exports would fail the project's
gate was withdrawn as untested. The retained finding is the need to qualify
the actual version/assumption chain. The missing-policy-binding hypothesis
was rejected by the source trace and in-memory mutation. These corrections
are part of this review, not consultations of other reviews.

### Primary external references

URLs are recorded as source identifiers for reproducibility; unversioned
pages are observations at review time, not dependency pins.

- **E01:** RISC-V SBI specification v2.0, Debug Console and shared-memory
  physical-address-range requirements.
  `https://raw.githubusercontent.com/riscv-non-isa/riscv-sbi-doc/v2.0/src/ext-debug-console.adoc`
  and
  `https://raw.githubusercontent.com/riscv-non-isa/riscv-sbi-doc/v2.0/src/binary-encoding.adoc`.
  Supports nonblocking reads, count/error results, and permission/range checks.
- **E02:** Linux v7.2, `drivers/tty/hvc/hvc_riscv_sbi.c`.
  `https://raw.githubusercontent.com/torvalds/linux/v7.2/drivers/tty/hvc/hvc_riscv_sbi.c`.
  Supports the existing HVC DBCN get/put integration, not board input behavior.
- **E03:** OpenSBI v1.6, `lib/sbi/sbi_ecall_dbcn.c`.
  `https://raw.githubusercontent.com/riscv-software-src/opensbi/v1.6/lib/sbi/sbi_ecall_dbcn.c`.
  Supports implementation of DBCN read and console-dependent registration.
- **E04:** XTerm maintainer's control-sequence reference, accessed during this
  review.
  `https://invisible-island.net/xterm/ctlseqs/ctlseqs.txt`.
  Supports display-control and terminal-reply behavior; it is not evidence
  of a demonstrated attack on the project's terminal.
- **E05:** musl v1.2.5 `configure`.
  `https://git.musl-libc.org/cgit/musl/plain/configure?h=v1.2.5`.
  Recognizes RISC-V soft-float variants and compiler runtime libraries.
  This rebuts treating musl as necessarily requiring FP; it does not establish
  that the project's toolchain can already build the selected userland.
- **E06:** RISC-V CoVE reference architecture, the upstream `main` text
  accessed during this review.
  `https://raw.githubusercontent.com/riscv-non-isa/riscv-ap-tee/main/src/refarch.adoc`.
  Supports the distinction between the architecture/ABI and its MPT, HS-only,
  and M-mode deployment models.
- **E07:** Supervisor Domain Access Protection, `riscv-smmtt` v0.9.0,
  introduction.
  `https://raw.githubusercontent.com/riscv/riscv-smmtt/v0.9.0/intro.adoc`.
  Supports the M-mode RDSM/physical-permission boundary and its relation to
  G-stage isolation; no K3 implementation support is inferred.
- **E08:** IETF RFC 9334, Remote ATtestation procedureS (RATS) Architecture,
  January 2023, especially layered attestation, reference values, verifier
  results and freshness.
  `https://www.rfc-editor.org/rfc/rfc9334.html`.
- **E09:** IETF RFC 6151, Updated Security Considerations for the MD5
  Message-Digest and the HMAC-MD5 Algorithms, March 2011.
  `https://www.rfc-editor.org/rfc/rfc6151.html`.
  Supports distinguishing MD5 attribution from collision-resistant security.
- **E10:** UAPI Group Unified Kernel Images specification and systemd's
  measurement description.
  `https://uapi-group.org/specifications/specs/unified_kernel_image/`
  and `https://systemd.io/TPM2_PCR_MEASUREMENTS/`.
  Supports explicit section ordering/identity and phase-separated measurement;
  no UKI boot support is inferred for the MVP.
- **E11:** TCG Canonical Event Log Format, v1.1 revision 11, dated
  October 9, 2025, accessed by the measurement research lane.
  `https://trustedcomputinggroup.org/resource/canonical-event-log-format/`.
  Supports event metadata, record ordering and critical versus informative
  content; adopting some fields is not a conformance claim.
- **E12:** systemd manuals as accessed during the review, not a selected
  dependency release:
  `https://www.freedesktop.org/software/systemd/man/latest/systemd-pcrlock.html`,
  `https://www.freedesktop.org/software/systemd/man/latest/systemd.pcrlock.html`,
  `https://www.freedesktop.org/software/systemd/man/latest/systemd-measure.html`,
  `https://www.freedesktop.org/software/systemd/man/latest/systemd-pcrphase.service.html`,
  `https://www.freedesktop.org/software/systemd/man/latest/systemd-stub.html`.
  Supports the distinctions between offline prediction, events, PCR state,
  TPM authorization, and the UEFI stub.
- **E13:** RISC-V Debug Specification 1.0, ratified February 20, 2025,
  `debug_module.adoc`, security and system-bus access/coherence sections.
  `https://github.com/riscv/riscv-debug-spec/blob/1.0/debug_module.adoc`.
  Supports the assumptions required for a JTAG observer, not K3 capabilities.
- **E14:** GCC manual, "When is a Volatile Object Accessed?", section 6.10,
  accessed during this review.
  `https://gcc.gnu.org/onlinedocs/gcc/Volatiles.html`.
  Supports the distinction between volatile access and memory ordering.
- **E15:** Amutable, "Introducing Amutable" (January 27, 2026) and
  "Introducing Amutable Foundations" (October 22, 2026).
  `https://amutable.com/blog/introducing-amutable`
  and `https://amutable.com/blog/introducing-amutable-foundations`.
  Primary sources for spelling and the company's stated artifact-oriented
  design; their marketing/assurance claims were not adopted or assessed.
- **E16:** CN at `cbe879c74190b7e09323527b55abf7248f81c033`;
  manual/grammar, source translation and proof-log files, especially:
  `https://github.com/rems-project/cn/tree/cbe879c74190b7e09323527b55abf7248f81c033`
  and
  `https://raw.githubusercontent.com/rems-project/cn/cbe879c74190b7e09323527b55abf7248f81c033/coq/Reasoning/ResourceInference.v`.
  Supports the assessed annotation and proof-log boundary. Its Cerberus
  dependency is `68bdc84bfadba203ecd465a09d5e9fced46b7ac0`; neither is
  a dependency selected for Beryllium by this report.
- **E17:** Frama-C 33.0 (Arsenic), source archive SHA-256
  `9c1cbffd28bb33c17a668107e39c96e4ae7378a3d8249f69b47afc7ee964e9b8`,
  WP/ACSL/importer manuals and the `coqwp` support library:
  `https://www.frama-c.com/download/frama-c-33.0-Arsenic.tar.gz`,
  `https://frama-c.com/download/frama-c-wp-manual.pdf`,
  `https://frama-c.com/download/frama-c-acsl-implementation.pdf`,
  `https://www.frama-c.com/download/frama-c-acsl-importer-manual.pdf`.
  Supports sidecar annotation mechanisms, WP's selected memory-model/
  volatile treatment and the distinction between goal export and
  assumption-free refinement.
- **E18:** Why3 change history and Frama-C 33.0's opam constraints,
  inspected by the assurance research lane:
  `https://gitlab.inria.fr/why3/why3/-/raw/master/CHANGES.md`
  and
  `https://github.com/ocaml/opam-repository/blob/master/packages/frama-c/frama-c.33.0/opam`.
  The inspected history declares Rocq support through 9.2 for Why3 1.9.0;
  the package constraint excludes Why3 1.9.0. This is an upstream-support
  mismatch to investigate, not an executed Fedora failure.
- **E19:** VST 2.17 and the assessed CompCert export dependency:
  `https://github.com/PrincetonUniversity/VST/tree/v2.17`,
  `https://raw.githubusercontent.com/AbsInt/CompCert/e26caf9fa6cd91665c9e8ee2b5194f413c796821/LICENSE`,
  `https://raw.githubusercontent.com/AbsInt/CompCert/e26caf9fa6cd91665c9e8ee2b5194f413c796821/export/ExportDriver.ml`.
  Supports separating the proof library from the complete production-C
  extraction route and its licensing gate.
- **E20:** CBMC 6.11.0, user-option manuals and memory-model implementation:
  `https://github.com/diffblue/cbmc/tree/cbmc-6.11.0`.
  Supports bounded-checking, unwinding and volatile/environment modeling
  requirements; no RVWMO or C-to-Rocq result is claimed.
- **E21:** RISC-V ISA memory-model source at
  `8fb3965fe4b501a6bfa00c34affffcdbdb2c552c` and herdtools7 at
  `9f90176bdd6fc2ec3b34a7989c2ba011f538d821`:
  `https://github.com/riscv/riscv-isa-manual/blob/8fb3965fe4b501a6bfa00c34affffcdbdb2c552c/src/unpriv/rvwmo.adoc`
  and
  `https://github.com/herd/herdtools7/blob/9f90176bdd6fc2ec3b34a7989c2ba011f538d821/herd/libdir/riscv.cat`.
  Supports explicit architecture-level ordering assumptions and a possible
  litmus-test complement. No litmus test was run in this review.

## 7. Suggested owner review sequence

**First action:** prepare a documentation-only revision/disposition against
F01-F08. In particular, settle the proof claim/limit and measurement-record
boundaries before delegating M7-M9 implementation. Do not start code from
this report.

1. Preserve the usefulness cut and decide Q27, Q28 and Q34 explicitly.
   Specify the console authority boundary and the first proof obligation.
2. Rewrite M8's four-layer contract, source relation and negative-outcome
   rule. Name the ledger rows that a successful pilot can change.
3. Rewrite M9 around a pre-link authority artifact, a post-link per-image
   reference, and separately sourced monitor/loader/platform records.
4. Add cross-lane semantic invalidation and final-source applicability to
   the RC4 gate. Then allocate details to each bounded milestone plan.
5. Present the resulting **new exact commit**, with the defaults answered
   and departures enumerated, for the human's decision.

### Supersession and readability repairs

Do not rewrite accepted history. Add clear current-scope exceptions or
supersession entries for the load-bearing statements below:

| Existing statement or ambiguity | Required clarification |
| --- | --- |
| `planning/mvp-plan.md:252,566-589,635`: assurance/C-refinement exclusion, old method-per-claim table, D7 | A named M8 pilot is an exception, not completion of the assurance release or transfer of model results |
| `mvp/docs/claim.md:49-59`: userland description and blanket unproved-implementation limit | M7's guest/operator profile and the conditional, exact M8 evidence exception |
| S3-C `1326-1328,1457,1476-1479,1536-1537` and the preauthorization status field | Allow the narrowly fixed M8 limit amendment only if its claimed result is achieved |
| `mvp/docs/claim-ledger.md:92`, U-13 | Separate operational model now; generalization later under Q35, with the relation obligation explicit |
| `planning/implementation-plan.md:1091-1136`: CN/WP/VST roles and promotion rules | A pilot recommendation is not automatic promotion or permission to use a non-open dependency |
| Accepted-document stop 1 at `planning/mvp-plan.md:692-696` | If M7 requires new console-class semantics, name its separately reviewed additive security-model change rather than implying grammar reuse authorizes it |
| M9 stage 1 and stop (c) | Per-platform loader attribution and separately evidenced platform facts; no fictitious monitor-origin record |
| S3-C's later "resolve H06/H07" wording | Preserve current accepted answers and reconsider only their new-context implications |

For standalone readability, add a compact definitions/authority box:
which texts are controlling; the two configuration identities; measured
versus build-recorded versus observed; proof versus contract versus bounded
checking; the intended console/operator profile; and what planning
acceptance does not authorize.

Smaller repairs: "rings with their generation words" should distinguish
ring indices from the hart-block publication generation; correct Amutable;
clarify that M8 delivers bounded verification artifacts as well as a plan;
and disambiguate the older implementation-plan "Milestone 8" binary
assurance sentence from the new MVP M8. The line-number references to the
old base should remain explicitly historical.

Useful read-only target commands:

```sh
git --no-pager show -s --format='%H%n%P%n%s' 95c9ab24ba2846eea6d102639abb3482c97989ec
git --no-pager diff 8b7559d2cc85640172a0f731b86d6ef0eecee2a6 95c9ab24ba2846eea6d102639abb3482c97989ec -- planning/mvp-plan.md
git --no-pager show 95c9ab24ba2846eea6d102639abb3482c97989ec:mvp/docs/claim.md
git --no-pager show 95c9ab24ba2846eea6d102639abb3482c97989ec:planning/security-model-v1.md
```

Any later execution-based assessment should use an isolated exact checkout.
It would be a separately scoped activity, not something this review
implicitly performed or authorized.

## 8. Human decision checklist

- [ ] The usefulness cut and the canonical anchor's operator trust are explicit.
- [ ] M7's console authority and evidence semantics fit a reviewed model.
- [ ] M8's precise proof target, assumptions, and C-to-model relation are named.
- [ ] M9's provenance, policy identity, and measurement claims match its evidence.
- [ ] The superseded lines and narrow claim-limit changes are enumerated.
- [ ] Negative tests cover the new boundaries, not only happy-path transcripts.
- [ ] RC4 re-establishes applicability at its final integrated source.
- [ ] A new exact proposal is considered, the present target is accepted by the
  responsible human with explicit decisions, or review is deferred.

## 9. After a decision

**Request revisions:** the owner records dispositions against the finding IDs
and produces a new exact proposal. Do not silently treat `95c9ab24` as
accepted, edit historical evidence to fit the proposal, or start M7-M10 code.

**Accept:** only the responsible human can accept an exact commit. S3-C's
stated effect is authorization to write the bounded plans, not to implement
them, access the shared board, merge, push, publish, or advance a release step.

**Defer:** preserve the proposed target and the accepted RC3 baseline; the
report creates no successor authority.

**Status:** independent technical review complete; S3-C remains proposed
and unaccepted. The report is a local session artifact; the repository's
tracked content and refs were not changed.

**Next:** the owner prepares a disposition and a revised exact S3-C proposal,
starting with the claim/proof and measurement provenance boundaries.

**Action required from the responsible human:** decide the exact proposal
and any changed defaults; no decision is presumed by this report.

