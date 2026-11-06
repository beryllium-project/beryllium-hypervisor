<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Review input: written by a Codex CLI session into this directory on 2026-10-31 under the S3-C packet's
     section 8 brief (untracked until 2026-11-01; SHA-256 of the file as found 5ef3f835b9f455eceb0039ee3a9fbf64ba9f09a65dd1e265a23a067b960b59bb); added to the tree unedited
     but for this comment under the responsible human's direction `also now process the claude cli and codex
     reviews and iterate as appropriate`. The reconciliation is `mvp-plan-s3c-review-reconciliation.md`. -->

# Independent design review of MVP plan revision S3-C

**Review target:** `95c9ab24`, `planning/mvp-plan.md`, section "Plan
revision S3-C"

**Date:** 2026-10-31

**Purpose:** steering input for the responsible human and project-owner
agent; this report accepts, authorizes, and changes nothing.

## Review basis and overall judgment

This review followed section 8 of
`planning/mvp-plan-s3c-review-summary.md`. The S3-C revision was read on its
own first, followed by the comparison, snapshot sections 5, 6, and 8, the
accepted plan body named by the brief, `mvp/docs/claim.md`, and the specified
S1 rows. `mvp-ring.c` and its interface were inspected only to assess whether
they are a representative M8 pilot; this is not an implementation review. No
other review of S3-C was read or used.

**Recommendation: revise S3-C before accepting it.** Its main cut is
defensible if MVP 1.0 is explicitly a **security-research demonstrator**:
useful to show the isolation mechanisms and useful to inspect their bounded
evidence. It is not yet useful as a workload platform: it remains static,
device-less, and unable to run a normal networked or persistent guest. The
comparison itself distinguishes "useful to show," "useful to build on," and
"useful to trust" (`post-rc3-candidates-2026-10-31.md:L49-L66`). D19 should
name which of those meanings is being released.

No MVP 2.0 implementation item is a prerequisite for that narrow 1.0. Four
design obligations currently assigned or implied later must, however, be
resolved in 1.0:

1. M7 needs unambiguous input framing, static console-authority semantics,
   and a control-hart availability analysis.
2. M8 needs an explicit relation between Model 0.2, the new operational
   model, the tool contracts, and the production C.
3. M9 needs a stable event-log and replay specification that attestation can
   build on without changing the measured semantics.
4. The H57/H58 residual-risk analysis needs a 1.0 delta for the new console,
   proof, measurement, firmware, and evidence boundaries. The full scaling
   analysis can remain in 2.0.

The revision has five acceptance-blocking defects:

- A successful M8 contradicts the canonical claim, which says the rings are
  unproved and covered by tests and runs "and by nothing else"
  (`mvp/docs/claim.md:L52-L59`), while S3-C forbids an M8 claim change
  (`planning/mvp-plan.md:L1326-L1330`, `L1453-L1457`).
- M8 calls two contract developments "refinement" without requiring a common
  refinement relation or theorem (`planning/mvp-plan.md:L1297-L1310`,
  `L1332-L1335`).
- M9 combines a U-Boot serial observation, monitor self-reports, and a
  one-time JTAG fact into one "chain" even though they have different
  producers, protection, and freshness (`planning/mvp-plan.md:L1359-L1385`,
  `L1467`).
- M7's in-band focus sequence cannot be reserved from arbitrary shell input,
  and Q27 gives a root shell to the protected anchor domain without accounting
  for the new authority over its secret and computation
  (`planning/mvp-plan.md:L1237-L1255`, `L1511-L1512`).
- M8 models the rings and "the measurement" while the nominally parallel M7
  and M9 branches change those subjects (`planning/mvp-plan.md:L1288-L1299`,
  `L1425-L1440`). Replaying an unchanged proof gate after merging does not
  establish that the model covers the new input protocol or measurement
  events. There is no stable object for M8 to model.

## The release ladder

### MVP 1.0

M7, M8, and a correctly framed M9 form a coherent demonstrator release:

- M7 changes the artifact from fixed output to a live isolation experiment.
- M8 can establish one narrow result about production C and, equally
  valuable, decide how later results will be stated.
- M9 can establish reproducible launch/run identity records and the format
  later attestation will cover.

Measurement is useful in 1.0 as evidence plumbing, not as a new security
root. If schedule pressure forces a choice, the log schema and honest claim
matter more than calling U-Boot's MD5 part of a chain.

Devices, the I/O service domain, dynamic management, attestation, a second
board, and a non-Linux service runtime are not 1.0 preconditions. H06/H07 do
need a narrow 1.0 disposition: either define aggregation and authority without
a mapping for console resources, or make the M7 profile reject overlapping
console grants and policy-only authority. H08/H09 can stay trigger-gated in
2.0.

### MVP 2.0

The content is directionally right but too large to be one assessable gate
(`planning/mvp-plan.md:L1209-L1210`). Its plan should impose this dependency
order:

1. Characterize the IOMMU/IOPMP, interrupt, reset, and device-ownership facts.
2. Fix H06/H07 policy semantics and the device/DMA object model.
3. Build one static device path and Linux service-domain prototype.
4. Resolve H08/H09 before adding dynamic management, delegation, restart, or
   revocation.
5. Add the non-Linux runtime only after the service ABI is demonstrated; the
   runtime bake-off must not define that ABI accidentally.
6. Add attestation only after M9's event semantics, verifier trust boundary,
   key custody, nonce/freshness, and replay rules are fixed.

"Formalize" also needs a release gate. At minimum it should say which of the
snapshot's stages 2 through 5 must hold. Otherwise 2.0 can finish all its
runtime work while the compiler, assembly, and live-correspondence boundaries
remain merely listed.

### MVP 3.0 and MVP 4.0

MPT, CoVE, CHERI, and MCS/MLS are independent research tracks, not a natural
single release (`planning/mvp-plan.md:L1211`). Give each a trigger, hardware
precondition, threat-model delta, and individual exit; define the minimum set,
if any, that makes a 3.0 release.

"General guests" is not an exit criterion (`planning/mvp-plan.md:L1212`). A
4.0 profile needs a vCPU/SMP and scheduler model, interrupt virtualization,
boot ABI, device set, storage/network story, reset/recovery semantics, resource
and availability limits, and a compatibility target. An immutable image guest
is one guest profile, not a definition of generality.

Dynamic multicore, Arm, the assurance release, and upstream are explicitly
unplaced (`planning/mvp-plan.md:L1214-L1216`). Place them on the ladder or call
them cross-cutting tracks with gates and dependencies. In particular, the
assurance release and binary correspondence cannot remain unplaced while a
rung is named "formalize," and dynamic multicore must be resolved before a
general multiprocessor-guest claim.

## M7: interactive guests

### Console topology

Hart 0 as the sole firmware-console reader and one single-writer,
single-reader queue per destination is the smallest sound topology. A shared
multi-destination queue adds target parsing, head-of-line blocking, and a
cross-domain failure mode. Direct asynchronous writes by hart 0 into guest
memory would violate the existing ownership split.

The revision must say whether the input queue is new. The accepted design
already has one hart-0-to-domain ring carrying management results, `pause`, and
`terminate` (`planning/mvp-plan.md:L213-L217`, `L643-L644`). Reusing it for
unbounded shell traffic can delay control actions. The simplest design is a
dedicated, bounded input byte ring per domain, separate from the control ring;
that choice must supersede D15. If the existing ring is reused instead, the
M7 plan must prove reserved control capacity, priority, and bounded delay.

Require these queue and SBI properties:

- Hart-0 polling and posting are bounded and nonblocking. A full target ring
  drops according to a fixed policy and increments an exact counter; it never
  blocks another domain or the control path.
- Unread input has an explicit fate at focus change, domain termination, and
  reset. Tagging batches with a focus epoch is preferable to silently
  delivering stale bytes.
- The calling hart determines the destination. No guest-supplied domain ID
  selects a queue.
- `dbcn_read` validates the entire destination before consuming input:
  addition overflow, zero and maximum lengths, page/window crossing,
  writability, private ownership, and excluded monitor/shared ranges. A
  rejected call changes no guest byte and consumes no queued byte.
- Partial reads, wraparound, full/empty state, generation rollover, and reset
  initialization have specified results.

Console input is a deliberate channel from a trusted operator/tool, not merely
a domain-owned object. The policy and claim should state who may route input,
which domain may receive it, and that focus selects among already-authorized
endpoints rather than changing authority dynamically.

### Focus protocol

Q28's default is unsound. Any byte sequence can occur in a shell command,
paste, terminal-control stream, or scripted binary input. Picocom and tmux
passing it through does not reserve it.

Make the console tool the trusted multiplexer. Session files should contain
structured `focus(domain)` and `send(bytes)` actions. After an unambiguous
monitor-ready marker arms guest input, the on-wire protocol should use framed
and escaped control records with an allowed target, length, focus epoch, and
acknowledgment. Literal occurrences must be byte-stuffed. Partial frames,
unknown targets, reconnects, resets, U-Boot output, and loss of phase must
disarm transmission and require re-arming. Focus changes must produce a
trusted, source-distinct acknowledgment before later bytes may be sent.

This does not create a trustworthy shared terminal UI. Guest output can
mislead the operator or print strings that resemble evidence. Continue to tag
every output source, treat the operator and console tool as trusted inputs,
and require the checker to match source, run nonce, order, and cardinality,
not unqualified transcript regexes.

### BusyBox and the anchor

Change Q27 to **no protected-domain shell**. A root shell in the anchor domain
can inspect or alter its own secret page, signal or replace its fixed program,
and modify request/response state. That does not by itself defeat G-stage
isolation from the other guest, but it weakens the anchor experiment and makes
"protected computation" ambiguous. Give shells to both `te-poc` domains, the
`two-guests` domains, and the untrusted anchor domain. Keep the protected
anchor endpoint fixed and give it no console-input authority. If interactive
debugging is wanted, add a separate `anchor-debug` scenario without the
secret/integrity claim.

The M7 plan must also define how BusyBox and the existing `nolibc` PID 1
coexist. "Touch the other's private page" is not a shell `touch` operation;
use a fixed, reviewed memory-access helper or a narrow command interface to
the retained scenario program.

Q29 needs content hashes, an offline source/archive path, exact configs and
patches, compiler and build inputs, licenses, notices, and corresponding-source
handling in addition to tags and commits. The release path says the public
research release is GPL-3.0-only (`planning/mvp-plan.md:L677-L680`); the M7
plan must clarify whether that statement covers project-authored source or all
distributed guest artifacts, and account explicitly for a static
BusyBox-containing initramfs. The selected revisions' licenses must be checked;
upstream BusyBox is normally GPL-2.0-only and musl normally carries MIT terms.
An aggregate may contain those components, but every artifact in it cannot be
silently labelled GPL-3.0-only. If guest images migrate, M10 needs a
per-component SPDX/license manifest, notices, complete corresponding BusyBox
source and configuration, and an actual source-provision path.

### Scripted-session obligations

The session checker must prove at least:

1. Input begins unfocused; pre-focus bytes are dropped and the count matches.
2. Each domain consumes a fresh nonce only while focused; the other domain
   demonstrably consumes none.
3. Focus/control bytes never reach a guest; malformed, partial, repeated, and
   unknown-target controls fail closed.
4. Empty, full, wrap, delayed-reader, focus-change, reset, termination, and
   reconnect cases have exact drop/flush results and do not stall control.
5. `dbcn_read` zero/partial reads and invalid, overflowing, cross-boundary,
   shared, read-only, and monitor-range destinations reject without consuming
   input.
6. `te-poc` proves the allowed shared-page digest and pairs each forbidden
   access with the right guest `SIGSEGV`, exactly one monitor denial, the
   expected address/cause, and unchanged protected data.
7. `anchor` drives only the untrusted domain and proves the protected domain
   received no input, its computation/measurement remained unchanged, and
   management actions still completed.
8. Expected events are tied to source tags, a run nonce, exact order, and exact
   cardinality. A guest printing a look-alike marker cannot satisfy a monitor
   expectation.
9. The record contains the session hash, intended actions, bytes actually
   written, target/focus epoch, timestamps, transcript hash, drops, and the
   compiler/build identity. An uncertain partial write is never retried.

Run this matrix under GCC and Clang in QEMU for every affected scenario, plus
the bounded M7 board probe and the RC4 campaign. The fixed `nolibc` scenarios
remain the regression oracle; shell sessions add evidence rather than replace
it.

## M8: first bounded monitor-verification milestone

### Model structure

Keep Q35's separate operational model. Model 0.2 is an abstract
authority/policy model; forcing protocol state into its closed, accepted
inductives would mix abstraction levels and reopen accepted results. A
disconnected second model would be equally unsafe.

Make the following M8 exits:

- A projection/simulation relation from valid operational states to Model 0.2
  states.
- Related initial states and a forward-simulation theorem, with explicit
  stuttering for operational steps absent from Model 0.2.
- A property-lineage table: inherited, re-proved, strengthened, or
  inapplicable.
- Parameterized hart, address, frame, and profile components so a later Model
  0.3 can reuse this work.
- Stable function-level specifications shared by the operational model and
  the C proof.

Stop M8 if that bridge cannot be stated within the bound. Similar theorem
names in two models are not a relationship.

The CN/WP leaf pilot may begin against the existing generic ring in parallel.
Acceptance of the operational model must either wait for M7's input protocol
and M9's event transitions, or model parameterized interfaces and require
explicit post-merge coverage theorems. A green replay of proofs about the old
state space is not post-merge revalidation.

### Pilot leaf and theorem

`mvp-ring.c` is a good tool-evaluation leaf: it exercises fixed-width
arithmetic, bounded loops, framing, aliasing, mutation, volatile shared
indices, and wraparound. It is not by itself a proof of the ring protocol.
Publication/consumption fences, SPSC ownership, captured-input
correspondence, executor calls, and RVWMO assumptions live outside the leaf.

Keep Q34, but require one small caller/executor/fence obligation. The M8 claim
must distinguish a sequential function contract from an end-to-end protocol
result.

Use one common relational target. A result may be called refinement only if
it establishes the equivalent of:

> For every concrete C state related by `R` to model state `m`, terminating
> defined execution of the exact production function preserves the stated
> frame, returns the model result, and leaves a concrete state related by `R`
> to the model's next state.

If CN or WP proves only its translated contract, record a contract proof and
the remaining relation as an assumption. Do not relabel it refinement.

The current M8 exit requires only recorded goals, assumptions, and a tool
selection (`planning/mvp-plan.md:L1332-L1335`), so every C proof may fail while
the milestone still exits despite its "something proved about the monitor's
own C" goal. Require at least one named production-C contract/refinement result
under the common target. If learning that no candidate works is an acceptable
success, rename M8 as a tool-selection/model milestone and do not advertise a
C proof.

### Tool choice

| Tool | Use in M8 | Reason and limit |
| --- | --- | --- |
| Frama-C/WP | Primary pilot | Mature ACSL workflow, existing project experience, packaged replay, multiple provers. Its memory model and ACSL-to-Rocq meaning still need a bridge; multiple SMT backends share the same VC generator. |
| CN | Required cross-check | Closest fit to the selected Cerberus semantics and restricted C. It is less mature operationally, not packaged, and still does not create the Rocq relation automatically. |
| VST | Time-boxed one-function feasibility spike; fallback for the load-bearing relation | Native Rocq reasoning gives the clearest path to a kernel-checked relational theorem. Cost is high, and CompCert/Clight semantics do not establish correspondence to the pinned GCC/Clang binaries. |

Select WP for the bounded pilot, with CN as the semantics-aligned cross-check.
If neither closes the common relational target, preserve their results as
contract evidence and make VST the serious stage-2 candidate. Tool selection
must be based on the claim closed, trusted base, replay, and correspondence
gap, not on raw goal counts.

Fedora packaging is reproducibility support, not qualification. Record exact
tool/solver hashes and flags, trusted components, known warnings, treatment of
timeout/`unknown`, clean replay, and negative mutations.

### Bounded model checking, annotations, H38, and H41

Replace Q36. Use CBMC to find counterexamples and check undefined behavior,
bounds, overflow, aliasing, and exact finite capacities. A normative bounded
row must state bit widths, loop and object bounds, unwinding-completeness
checks, concurrency abstraction, and assumptions. Openness and qualification
do not make it an inductive proof or C-to-Rocq refinement. Adopt H38's useful
discipline—production C, independent specifications, staged and traceable
claims—without importing Helium's counts or treating CBMC as kernel-checked
proof.

Replace Q37's binary choice with three layers:

1. The authoritative semantic function and relation live in Rocq beside the
   model.
2. Tool contracts live where the tool can bind them to the exact production
   function; inline CN/WP annotations are preferable to an unchecked copy.
3. Any overlay or generated translation has a mechanical source/token/AST
   identity check and exact hashes.

Re-deriving pins is expected evidence work. Avoiding it does not justify a
sidecar that can drift from the C.

The specified review corpus does not enumerate H41's conditional
recommendations; S1 merely points to another document
(`planning/he-to-be-synthesis.md:L248`). Therefore no item-by-item adoption is
defensible from S3-C as written. Adopt H41's meta-rule—these are decision
gates, not an imported plan—and require the M8 plan to reproduce every item by
stable ID/text, trigger, disposition, and evidence. Adapt H22's pure-decision
function/one-executor seam, while adding its captured-input and live
correspondence obligation (`planning/he-to-be-synthesis.md:L223`).

### Claim correction

Pre-authorize a narrow M8 change to the Required limit. It should name exact
functions, source commit, theorem/contract, C semantics, tool versions, and
assumptions, then say that callers/executor and fences (unless covered), the
compiler and binaries, assembly, concurrency outside the proved relation, and
the remaining monitor are unproved. Preserve the no-whole-system claim. The
current "no claim change" rule makes an honest successful M8 impossible.

## M9: measurement and future attestation

### Keep the evidence; do not call it a rooted chain

U-Boot's MD5 is worth retaining as a captured loader observation. It detects
accidental staging/copy mismatches and associates a serial capture with the
MD5 independently computed for a SHA-256-identified build artifact. It is not
a cryptographic binding between MD5 and SHA-256, an authenticated first
measurement, or a root of trust. The comparison correctly described it as run
attribution and "not as a chain" (`post-rc3-candidates-2026-10-31.md:L96-L108`).

Separate three artifacts:

1. the raw U-Boot loader observation in the serial capture;
2. a monitor-produced binary event log for its self-report, configuration,
   policy, and domain events; and
3. a host-produced run bundle that links those two artifacts to an external
   reference manifest and checker result.

The monitor cannot place a prior U-Boot event that it never received into a
monitor-owned log. The lifecycle/debug observation is also separate: a dated
platform characterization, not a per-boot event or measured property unless
an independent component samples and binds it for that boot.

Suggested claim clause:

> For each recorded run, U-Boot printed an MD5 digest of the loaded MVP file.
> The monitor then self-reported SHA-256 digests of its specified in-memory
> read-only regions, the sealed configuration and compiled policy identity,
> and each independently loaded domain artifact at launch. The offline
> checker reproduced and compared those observations with the
> SHA-256-identified build outputs and checked their completeness and order.
> These are unauthenticated local run-attribution and consistency
> observations: no protected root, secret key, freshness challenge, or signed
> quote binds them; code able to alter the monitor can fabricate its records;
> and a record does not show that the bytes remained unchanged after the
> stated measurement point.

### Self-measurement

Retain it, labelled **self-reported runtime immutable-region digest**, if and
only if the build can reproduce the exact final loaded RX/R ranges. Define
assembly, padding, relocation, and excluded writable/log/configuration ranges;
measure before domain entry; compare against the final load representation;
and state that this says nothing about fetched instructions, a malicious
monitor, or continued integrity. It creates the range definition a later JTAG
verifier can recompute. Drop the record if the exact bytes and ranges cannot
be reproduced.

### Event-log format

`stage, object, algorithm, digest` and "ordered set" are inadequate
(`planning/mvp-plan.md:L1370-L1374`). Specify a canonical, bounded binary
append-only sequence; `BE_MVP` lines are a checked rendering, not the
normative log.

The header needs magic, major/minor version, profile/reference-manifest ID,
scenario/configuration ID, maximum/actual length, and completeness/overflow
state. Each length-delimited record needs sequence, producer, evidence/trust
class, event type, global or per-domain stream ID, stable object ID,
representation and exact byte range/length, TCG algorithm ID and digest list,
and outcome. The trailer needs record count, total length, an explicit complete
marker, and a transcript digest. Define endian/canonical encoding,
unknown-version/record handling, reset behavior, fail-closed overflow,
duplicate/omission/order rules, and domain-separation constants.

Define a replay function now, with separate platform/monitor, configuration,
and per-domain streams. Offline replay values must be labelled unprotected.
Keep the external expected-event manifest separate from observations and make
it build-variant aware.

Stock `systemd-pcrlock` expects TPM/PCR and event-log semantics; the authority
report alone is not directly consumable. M9 should produce a requirements
crosswalk among (a) a later minimal vTPM and standard TCG event log, (b) a
Beryllium PCR-like SBI interface requiring guest integration, and (c) a
lossless adapter from the Beryllium log profile to the TCG/systemd model. Use
TCG algorithm IDs and explicit replay semantics now, but do not claim stock
systemd compatibility until a TPM-facing interface and adapter exist.

### Simulated root of trust

For 2.0, prefer an external verifier that controls reset, provides a nonce,
halts all active harts for a coherent observation, reads memory through JTAG,
independently hashes the defined monitor/log/configuration regions, and signs
the nonce-bound result with a key outside the board. The ESP32 is useful as
key custody and, if capable, the JTAG/reset controller. Otherwise use the JTAG
host as the first lab verifier.

GPIO alone gives coordination, not measurement provenance. An ESP32 or
management chip that merely signs a monitor-supplied digest notarizes a
self-report. Use a carrier management chip only after establishing independent
read/reset access and key isolation. The resulting claim is an "external lab
verifier observation," with physical control and JTAG state explicit, not a
device-rooted identity.

### IMA boundary and board evidence

Nothing in M9 is IMA: it measures launch artifacts and static configuration at
the domain boundary, with no guest file-access hook, path/inode event stream,
signature appraisal, or file-based execution denial. A future opaque extend
service is PCR/vTPM plumbing. Preserve the boundary by keeping guest file
names and appraisal outside the monitor and official log profile.

Q31 is wrong for M9. QEMU cannot exercise U-Boot's digest/copy path or JTAG,
and S3-C simultaneously requires a platform probe while saying M9 has no
board-characterization need (`planning/mvp-plan.md:L1379-L1385`,
`L1438-L1444`). Require one bounded M9 board run correlating the U-Boot
observation, monitor log, loaded ranges, and reference manifest, plus the
separately reviewed read-only JTAG procedure. This need not be a full campaign.

Freeze M9's event/state-transition specification before M8 accepts a
measurement model. Model at least unique required events, deterministic order
per stream, no silent overflow, and no domain entry before required launch
measurements complete.

Clarify the NOR rule. S3-A permits a recorded `saveenv` transaction in the
NOR environment partition and its restoration (`planning/mvp-plan.md:L883-L893`),
while M9 says "Nothing writes ... the NOR" (`L1375-L1378`) and S3-C stops on a
need to "rewrite the NOR" (`L1471-L1474`). Say that M9 adds no NOR/firmware
writes and that the existing, bounded S3-A environment exception remains the
only write. Do not leave an absolute statement contradicted by every board
campaign.

## Disposition of Q27 through Q42

| Question | Steering disposition |
| --- | --- |
| Q27 | **Change:** no shell or console-input authority in the protected anchor domain; use a separate debug scenario if needed. |
| Q28 | **Change:** escaped/framed, phase-gated tool protocol with epochs and trusted acknowledgments; no supposedly unused raw sequence. |
| Q29 | **Refine:** immutable content hashes, offline closure, exact configs/toolchain/patches, licenses/notices, corresponding source, and reproducibility. |
| Q30 | **Refine:** mandatory affected-scenario matrix under both compilers, source-aware exact-cardinality checks, plus bounded board evidence; sessions do not replace fixed tests. |
| Q31 | **Change:** M7 read characterization, one bounded M9 board correlation run and read-only probe, then the RC4 campaign. A full campaign per milestone is unnecessary. |
| Q32 | **Keep:** do not wait for the Mini-ITX. |
| Q33 | **Keep with explicit framing:** dynamic management belongs in 2.0 if 1.0 is a demonstrator, not a platform to build workloads on. |
| Q34 | **Keep and strengthen:** ring leaf plus one caller/executor/fence correspondence slice. |
| Q35 | **Keep and strengthen:** separate operational model plus an explicit simulation/projection bridge to Model 0.2. |
| Q36 | **Change:** BMC is explicitly bounded evidence with completeness/bounds recorded; openness and qualification are necessary operational controls, not sufficient semantics. |
| Q37 | **Change:** Rocq semantics beside the model, tool contracts mechanically bound to exact C, and identity checks for any overlay; inline annotations and re-pinning are acceptable. |
| Q38 | **Keep the boot-path decision; change the meaning:** MD5 is an unauthenticated loader observation used for attribution only, excluded from any rooted/protected accumulator. Do not add a second U-Boot path. |
| Q39 | **Keep:** analysis and requirements crosswalk in M9; implementation from 2.0. |
| Q40 | **Refine:** human-executed, read-only, separately reviewed recipe; board/probe/tool identity, exact commands, raw capture hash, pre/post checks, date, and ambiguities recorded. |
| Q41 | **Refine:** per-milestone limits, but include state-machine/TCB complexity, functions/theorems/tools, assumptions, elapsed proof effort, and schema completeness; line count alone is weak. |
| Q42 | **Change:** require focused independent review of each milestone plan and its security-relevant result before claim/ledger changes. M8 needs formal-method review; M9 needs schema/claim review; M7 needs protocol/threat review. |

## Accepted text that S3-C must reconcile

Add explicit supersessions or amendments for:

- Scope's hart-0-to-domain ring description and D15 if M7 adds the recommended
  dedicated input ring (`planning/mvp-plan.md:L213-L217`, `L643-L644`).
- Scope's measurement, which currently names only the protected domain and
  configuration (`planning/mvp-plan.md:L234-L235`).
- Scope's model work, which currently ends with M3/Model 0.2
  (`planning/mvp-plan.md:L237-L238`).
- Scope's release candidate, which still names M4 (`planning/mvp-plan.md:L239`),
  while D21 makes M10/RC4 the release candidate.
- The assurance-release non-goal, narrowed to allow M8's one-leaf source
  contract/refinement pilot while retaining binary correspondence and broad
  assurance for later (`planning/mvp-plan.md:L252`).
- D7's statement that "the model work is M3"
  (`planning/mvp-plan.md:L635`).
- S3-C's absolute no-NOR-write wording, reconciled with S3-A's already accepted
  saved-environment exception (`planning/mvp-plan.md:L883-L893`,
  `L1375-L1378`).
- The claim's RC2 metadata and `nolibc`-only guest description
  (`mvp/docs/claim.md:L6-L13`, `L49-L51`).
- The claim's categorical unproved-rings language
  (`mvp/docs/claim.md:L52-L59`).
- The claim's measurement limit (`mvp/docs/claim.md:L66-L70`) and evidence
  description, using the three-artifact distinction above.

The earlier S3-A supersessions already reconcile the base Scope's kexec text
and release-path step 1; S3-C need not repeat them. M10 nonetheless cannot
literally "change no claim text": RC4 metadata/evidence and the M7/M8/M9
limits must be rendered into the canonical claim. Replace the blanket rule
with a bounded list of exact semantic and metadata amendments.

## Missing stop conditions

Add stops for the following.

**M7**

- Firmware reads are blocking or unbounded, or input traffic can starve
  control work, logging, another domain, `pause`, or `terminate`.
- Focus framing is ambiguous, cannot quote arbitrary payload, loses phase, or
  leaves stale bytes across focus/reset/termination.
- The complete writable-private DBCN destination cannot be validated before
  dequeue, or a rejected call has partial effects.
- The checker cannot prove source-specific causality or distinguish
  guest-forged look-alike output from monitor evidence.
- Console authority cannot be represented without unresolved policy
  aggregation/authority semantics.
- The protected anchor shell can inspect or alter the secret/computation.
- BusyBox/musl inputs, licenses, corresponding source, or reproducibility
  cannot be closed in the release bundle.

**M8**

- The Model 0.2 bridge or common C/model relation cannot be stated/proved
  within scope; a tool proves a weakened/different contract; or copied C lacks
  mechanical identity to production source.
- Required undefined, implementation-defined, volatile, concurrency, fence,
  or memory-model behavior is absent from the semantics/assumptions.
- Any target source/model/tool/solver changes after proof without invalidating
  and replaying the evidence.
- New admits or unapproved axioms, solver `unknown`/timeout counted as success,
  non-reproducible replay, or exceeded proof budget.
- The canonical claim cannot be reconciled with the actual result.

**M9**

- Any event lacks exact producer, measured bytes/representation/range,
  measurement point, expected manifest entry, or mismatch behavior.
- Silent overflow, omission, duplication, reorder, parse ambiguity, or
  binary-log/console-rendering disagreement is possible.
- MD5, a monitor self-report, or a one-time JTAG observation is described as
  authenticated, fresh, protected, or rooted.
- The self-measurement bytes cannot be reproduced from the final loaded
  representation.
- The JTAG procedure cannot be shown read-only or returns ambiguous lifecycle
  state.
- M8 accepts a ring/measurement model before the M7 and M9 transition schemas
  are frozen, or the merged features fall outside the proved state space.

Negatives for M9 must cover omission, duplication, reorder, wrong producer,
object, algorithm and range, unsupported version, truncation/overflow, wrong
build/scenario manifest, and binary/rendered-log disagreement—not only a wrong
digest at each stage.

## Proposed steering sequence

1. Amend S3-C's framing, supersession table, Q defaults, claim authorization,
   and stop conditions.
2. Specify M7's input transition interface and M9's event/state-transition
   schema before M8 freezes the operational model; the tool pilots may proceed
   independently against parameterized interfaces.
3. Write and independently review the M7, M8, and M9 plans against the exact
   obligations above.
4. Run M7's board read characterization and M9's bounded board/JTAG work before
   accepting their results.
5. Merge accepted milestones, rederive every pin, replay proofs/checkers after
   integration, then run M10/RC4 and its campaign.

This preserves the proposed architecture while preventing the release from
overstating console isolation, C refinement, or measurement trust.
