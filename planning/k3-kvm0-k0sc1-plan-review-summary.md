<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# KVM0 K0-SC1 plan review and acceptance record

This document began as the decision-neutral responsible-human review packet
for exact planning target
`9b9923f8a58fe7102a108cb2a976ea09979427a1` and now also records the later
responsible-human decision on that immutable commit. The target remains byte
unchanged.

Packet commit `695ab65770303ee09ebe863f179bdffea73b9c64` is the direct
child of the target and remains decision support. Neither the packet nor this
acceptance-record follow-up is plan content, implementation, custody,
selection, source evidence, hardware evidence, or package authority.

Except where a statement is explicitly marked current or post-decision,
sections 1 through 8 preserve the pre-decision review history. The 15
unchecked section 8 items remain that historical review instrument.

## Decision record

At `2026-10-04T23:27:22.401+02:00`, the responsible human supplied:

```text
accept 9b9923
```

The abbreviation was checked against the local Git object database and
resolved uniquely to exact target
`9b9923f8a58fe7102a108cb2a976ea09979427a1`, whose parent is
`b36190352d270ce9ed70a6ddab8f4c7e7030f4e6` and whose tree is
`5ee896df14c016b33ff43ff10e8e4e69596054c0`.

The responsible human accepted that exact target as **planning text only**.
Acceptance does not authorize K0-SC1 implementation, custody copying,
selection, remote-ref access, board access, K0-SC2, K0-SC3, package or archive
assembly, destination import, K0-S readiness, K0-X, K0-R, push, publication,
or release.

Findings K0SC1-F1, K0SC1-F2, K0SC1-F3 and residuals K0SC-R1, K0SC-R2,
K0SC-R3 remain unresolved and unwaived. Acceptance does not fix their target
wording or constitute separate risk acceptance.

The target's own `proposed-not-reviewed`, `none`, `not-authorized`, and
`NOT-RUN` fields remain frozen pre-decision content. This record and the
maintained current-position pages carry the later acceptance decision.

Later steering remains separate:

- at `2026-10-04T23:28:16.538+02:00`, the responsible human supplied
  `continue as far as you can overnight`; and
- later on October 4, the responsible human supplied
  `I approve access to k3 board if needed for read only access`. An exact
  event timestamp was not available in retained local turn history when this
  record was prepared.

Neither instruction was consumed as K0-SC1 or K0-SC3 authorization. Accepted
sequencing, unresolved findings, and exact-authorization requirements still
block board access and package work.

## 1. Decision summary

| Field | Review value |
| --- | --- |
| Review target | Exact commit `9b9923f8a58fe7102a108cb2a976ea09979427a1` (`docs: propose K0-SC1 custody plan`) |
| Parent / comparison base | `b36190352d270ce9ed70a6ddab8f4c7e7030f4e6` |
| Git tree | `5ee896df14c016b33ff43ff10e8e4e69596054c0` |
| Current status | **Responsible-human accepted as planning text only** at the exact target above; the immutable target retains frozen pre-decision status fields |
| Automated review disposition | Pre-decision review recommended revisions; the one high and two medium-high findings remain unresolved and unwaived after acceptance |
| Decision | Accepted by exact instruction `accept 9b9923` at `2026-10-04T23:27:22.401+02:00` |
| Implementation / execution | K0-SC1 implementation, custody, selection, and remote-ref check are unauthorized or `NOT RUN`; K0-S remains `not-ready` |
| Successor / hardware status | K0-SC2 and K0-SC3 remain unauthorized; K0-SC3 and Beryllium/R8 K3 hardware remain `NOT RUN`; K0-X/K0-R remain blocked |
| Repository / branch | Current private Beryllium repository; `beryllium/single-hart-runtime-r0` |
| Push / tag state | Target is the clean local branch tip, 12 commits ahead of the last-fetched tracking ref, contained by one local branch, untagged, and absent from local remote-tracking containment; no network recheck was performed |
| Publication status | Push, tag, public migration, publication, release, paper submission, collaboration commitment, and upstream submission remain blocked |

**Action taken:** the responsible human accepted exact target
`9b9923f8a58fe7102a108cb2a976ea09979427a1` as planning text only.

This acceptance-record follow-up is unaccepted bookkeeping. It is not the
plan target, does not resolve or waive any finding, and cannot authorize
K0-SC1.

## 2. Deliverables

The exact parent-to-target delta is five mode-`100644` planning paths:

```text
M planning/HANDOFF.md
M planning/README.md
A planning/k3-kvm0-k0sc1-plan.md
M planning/project-orientation.md
M planning/roadmap.md
```

The target contains 615 insertions and six deletions.

| Deliverable | Paths | Purpose | Trust or privilege boundary | Highest-value review question |
| --- | --- | --- | --- | --- |
| Standalone K0-SC1 plan | `planning/k3-kvm0-k0sc1-plan.md` | Define package-specific custody and selection planning under accepted K0-SC | Planning text only; no custody byte, selection, remote observation, board fact, import, or runtime change | Do the six classes and finite custody envelope remain inside K0-SC1 rather than consuming K0-SC2 work? |
| Current-position placemat | `planning/roadmap.md` | Record the proposed plan and human-reported board availability without evidence or authority transfer | Status only | Does board availability remain visibly separate from K0-SC3 and hardware evidence? |
| Returning-human guide | `planning/project-orientation.md` | Explain that K0-SC1 is the next proposed plan decision while all package and board gates remain separate | Re-entry guidance only | Can a returning owner distinguish drafting, plan acceptance, package authorization, selection, and execution? |
| Planning index | `planning/README.md` | Link the proposed plan and summarize its six-class/non-authorization boundary | Navigation-level status only | Does discoverability avoid implying acceptance or implementation readiness? |
| Operational handoff | `planning/HANDOFF.md` | Preserve the exact human statement, its drafting-only interpretation, and unchanged blocks | Handoff only | Could a later session resume without treating the online board as authority to act? |

No accepted K0-A/K0-I/K0-S/K0-SC record, KVM0 destination tool, runtime,
model, proof, dependency, policy, generated page, or publication-gate byte
changes in the target.

## 3. Claim boundary

### Supported by the exact target

The target supports saying:

- one bounded K0-SC1 custody/selection plan is proposed;
- exactly six disposition classes are proposed;
- ordinary custody has a hard maximum of 2,095 regular files, restricted
  custody has exactly one regular file, and the combined maximum is 2,096,
  below the K0-I member cap of 4,096;
- ordinary and restricted custody are separate, and the restricted map is
  excluded from ordinary checksums, Git, ordinary archives, K0-I import,
  reports, and publication;
- custody, host selection, ST01-ST16 selection, ST16 skip selection, and
  source-ref report disposition remain human-only decisions;
- a later K0-SC1 implementation instruction must name a full base, relations,
  inventory/formulas, tools, structured commands, output/retention bounds,
  caps, stops, and exclusions;
- all seven inherited K0-SC1 stops and additional safety/privacy/drift stops
  remain fail-closed; and
- the board is human-reported online, but the statement is non-evidentiary
  and does not authorize K0-SC3 or hardware work.

### Trusted or assumed planning inputs

The target carries these values only as **unrederived draft-time expected
inputs**:

- 12 recovered discovery records and their aggregate identities;
- 2,030 host-manifest rows and their manifest identity;
- the current 46-file, 53-path, 45-checksum preparation profile;
- one restricted map at its recorded mode, size, hash, and coverage;
- three retained selftest-selection profile members; and
- the recorded, not accepted, source relation and ref-record classes.

The packet did not access private records or rerun these identities. Any
future K0-SC1 candidate must rederive every load-bearing value under a
separate exact authorization.

The current upstream/ahead state is also a last-fetched local-ref observation,
not a remote-server fact. Remote checking remains `NOT RUN`.

### Unavailable or `NOT RUN`

- no ordinary or restricted custody root is selected;
- no custody copy, origin closure, duplicate disposition, or stable retention
  exists as a K0-SC1 result;
- no host artifact set, ST01-ST16 set, or ST16 skip is selected;
- no source-ref report has been produced and remote status is `NOT RUN`;
- no exact ordinary directory-count maximum has been established;
- no K0-SC1 implementation authorization or candidate exists;
- K0-SC2, K0-SC3, board characterization, hardware validation, payload/archive
  assembly, K0-I import, K0-S readiness, K0-X, and K0-R are not run; and
- no push, tag, publication, or release has occurred.

### Explicit non-claims

The target does not:

- resolve or waive K0SC-R1, K0SC-R2, or K0SC-R3;
- establish stable custody, a general evidence store, immutable preservation,
  encryption, replication, indexing, lifecycle, or restore policy;
- accept the source relation, host set, profile, test set, skip, package, or
  any draft diagnostic;
- authorize copying, selection, network access, board access, QEMU, guest
  execution, real KVM selftests, import, or readiness;
- establish KVM0 execution, K3 qualification, Beryllium hardware validation,
  retained-R8 evidence, Linux/BSP selection, B0/B1, an H0 successor, services,
  devices, DMA, multicore, policy, attestation, or an MVP; or
- authorize push, tag, publication, release, migration, paper submission,
  collaboration outreach, venue selection, or upstream submission.

## 4. Security and correctness invariants

| Invariant | Target location | Proposed control | Evidence or review boundary |
| --- | --- | --- | --- |
| Exactly six disposition classes | `Six disposition classes` | C1-C6 are named; changed-path inventory is cross-cutting; a seventh class stops the package | Textual invariant; see K0SC1-F1 for the accepted K0-SC relation |
| Finite regular-file envelope | `Hard maxima and deterministic formulas` | Ordinary `<=2095`; restricted `=1`; all `<=2096` and `<=4096` | Arithmetic is consistent; directory-count/mode gap remains K0SC1-F2 |
| Ordinary/restricted separation | `Restricted path`; `Generated ordinary control paths` | Separate roots, modes `0700/0600`, no restricted checksum or ordinary-surface exposure | Planning invariant; no custody exists |
| Human-only decisions | `Selection packets and human decisions`; `Exit condition` | Decision packets stay `pending-responsible-human`; checks cannot select or approve | Textual invariant; no packet has run |
| Source relation remains unaccepted | `Controlling accepted history`; `Source-ref report disposition` | Report disposition only; remote checked under exact authority or `NOT RUN` | No remote check; see K0SC1-F3 |
| Authorization must be exact and fail closed | `Separate implementation authorization` | Full base, relations, inventory, tools, commands, outputs, caps, stops, exclusions | Template exists but incompletely binds some target requirements; see K0SC1-F3 |
| Stops grant no recovery authority | `Stop conditions` | Seven inherited plus added stops; no repair, substitution, deletion, reconstruction, or expansion | Target text only; all added stops must be bound before implementation |
| Board availability grants no board authority | `Status and authority`; `Relationship to later packages` | Human report is non-evidentiary; K0-SC3 and hardware remain `NOT RUN` | No board contact occurred |

## 5. Review history and findings

### Resolved before the exact target

- A standalone plan was used instead of modifying accepted K0-SC.
- Six C1-C6 classes and eight generated controls were explicitly named.
- Ordinary/restricted custody, source-ref disposition, human-only decisions,
  an implementation-authorization template, and all seven inherited stops
  were made visible.
- The target was limited to exactly five mode-`100644` planning paths.
- Pre-commit equivalent-content source/privacy/path checks passed.

### Open findings

| ID | Significance | Confidence | Target location | Finding and human question |
| --- | --- | ---: | --- | --- |
| K0SC1-F1 | **High; revision recommended** | 9/10 | `Six disposition classes` C5; `Selftest and skip decisions` | C5 requires exact selftest binary identities, while accepted K0-SC assigns exact selftest binaries and the 18-entry install manifest to K0-SC2. Should K0-SC1 be limited to names/order/argv/timeouts/markers and leave binary/install identities to K0-SC2? |
| K0SC1-F2 | **Medium-high; revision recommended** | 9/10 | `Hard maxima and deterministic formulas`; `Validation for the proposed plan` | File arithmetic is consistent, but `ordinary_directory_count` has no numeric maximum and ordinary directory modes are not fixed, so `FILES.modes` has no hard row maximum. Is the claimed finite K0-SC1 path/count/mode boundary adequate? |
| K0SC1-F3 | **Medium-high; revision recommended** | 9/10 | `Separate implementation authorization`; `Validation for the proposed plan`; added stop list | The authorization template does not bind exact selected local/tracking ref records, uses a placeholder for stops that does not enumerate every added stop, and validation explicitly counts only the seven inherited stops. Must the template and validation bind all ref inputs and all added stops before acceptance? |

These findings were not corrected in the packet because that would change the
immutable target under review. If revisions are required, create a new plan
target and new packet.

K0SC-R1/R2/R3 remain accepted-plan residuals. This target proposes K0-SC1
dispositions; it does not close or waive them. In particular, K0SC-R2 remains
open for K0-SC2 and K0-SC3, and K0SC-R3 loss risk persists until custody is
actually authorized and completed.

## 6. Validation and retained evidence

### Pre-commit equivalent-content validation

Before commit, equivalent five-path content passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

That gate reported:

```text
site_markdown=95
policy_markdown=5
rendered_references=911
configured_routes=221
tracked_html=0
network_events=0
generated_tree_changes=0
adversarial_cases=34
```

Additional pre-commit checks confirmed six classes, eight controls, seven
inherited stops, three retained selection paths, the `2095 + 1` envelope,
privacy, and exact five-path scope.

### Exact-clean-target validation

On October 4, 2026, with exact target
`9b9923f8a58fe7102a108cb2a976ea09979427a1` as clean `HEAD`, these checks
passed:

```text
git diff --check \
  b36190352d270ce9ed70a6ddab8f4c7e7030f4e6 \
  9b9923f8a58fe7102a108cb2a976ea09979427a1
umask 0022 && npm run docs:source-check
```

The exact-target source check reported the same `95/5/911/221` source counts,
zero tracked HTML, zero network events, zero generated-tree changes, and 34
adversarial cases. The worktree remained clean.

Exact-target audit also confirmed:

- five mode-`100644` changed planning paths;
- target tree `5ee896df14c016b33ff43ff10e8e4e69596054c0`;
- no target change to accepted K0-A/K0-I/K0-S/K0-SC records, `tests/kvm0/**`,
  runtime/model/pathfinder, dependencies, policies, instructions, or
  publication gate; and
- local-only branch state: 12 ahead, zero behind, one containing local branch,
  no containing local tag, and no containing local remote-tracking ref.

### Packet-follow-up pre-commit validation

On October 4, 2026, this packet and its four minimal status links passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

The source check reported:

```text
site_markdown=96
policy_markdown=5
rendered_references=915
configured_routes=221
dot_sources=10
public_assets=10
tracked_html=0
network_events=0
generated_tree_changes=0
adversarial_cases=34
```

Additional checks confirmed the exact five-path boundary, sections 1-9,
15 unchecked checklist items, the three open findings, validation attribution,
privacy, and no change to the target plan, accepted records, KVM0 tooling,
runtime/model/pathfinder content, dependencies, policies, instructions, or
publication gate.

Packet validation covers only decision support and status integration. It
cannot validate private inputs, close findings, or authorize implementation.

## 7. Recommended human review sequence

1. Confirm target, parent, tree, five-path inventory, and proposed/not-reviewed
   status.
2. Review claim/non-claim and board-online/non-evidentiary boundaries.
3. Review C1-C6 traceability and decide K0SC1-F1.
4. Review the `2095 + 1` arithmetic, directory closure, modes, caps, and decide
   K0SC1-F2.
5. Review ordinary/restricted separation and package-specific versus Phase 2
   boundaries.
6. Review custody, host, test-set, skip, and source-ref human decisions.
7. Review the exact authorization template, seven inherited stops, added
   stops, and decide K0SC1-F3.
8. Confirm residual K0SC-R1/R2/R3, validation attribution, and all successor
   exclusions.

Useful read-only commands:

```sh
git --no-pager show --stat --summary \
  9b9923f8a58fe7102a108cb2a976ea09979427a1
git --no-pager diff --find-renames \
  b36190352d270ce9ed70a6ddab8f4c7e7030f4e6 \
  9b9923f8a58fe7102a108cb2a976ea09979427a1 -- \
  planning/k3-kvm0-k0sc1-plan.md \
  planning/roadmap.md planning/project-orientation.md \
  planning/README.md planning/HANDOFF.md
git --no-pager show \
  9b9923f8a58fe7102a108cb2a976ea09979427a1:planning/k3-kvm0-k0sc1-plan.md
```

## 8. Human decision checklist

- [ ] The target is planning-only and leaves all implementation and successor
      gates separate.
- [ ] C1-C6 map all K0-SC1 inputs, blockers, deliverables, and decisions
      without a seventh class.
- [ ] K0SC1-F1 is acceptable as written or requires revision.
- [ ] Ordinary `<=2095`, restricted `=1`, total `<=2096`, directory closure,
      modes, checksums, and caps are sufficiently finite.
- [ ] K0SC1-F2 is acceptable as written or requires revision.
- [ ] Ordinary and restricted custody remain strictly separated and do not
      create a general evidence store.
- [ ] Custody, host, ST01-ST16, ST16 skip, and source-ref report dispositions
      remain human-only.
- [ ] The authorization template binds every required ref input, output,
      retention boundary, cap, stop, and exclusion.
- [ ] K0SC1-F3 is acceptable as written or requires revision.
- [ ] All seven inherited and added stops are preserved and grant no repair or
      expansion authority.
- [ ] K0SC-R1/R2/R3 remain unresolved and unwaived.
- [ ] Board availability is non-evidentiary; K0-SC3 and hardware remain
      unauthorized and `NOT RUN`.
- [ ] Draft-time identities are labeled unrederived and private.
- [ ] K0-SC1 implementation, custody, selection, network access, readiness,
      K0-X/K0-R, push, publication, and release remain excluded.
- [ ] Exact target `9b9923f8a58fe7102a108cb2a976ea09979427a1` is
      accepted, revisions are requested, or review is deferred.

## 9. After the decision

### Recorded outcome: accepted

The responsible human accepted exact target
`9b9923f8a58fe7102a108cb2a976ea09979427a1` at
`2026-10-04T23:27:22.401+02:00` by exact instruction `accept 9b9923`.
Acceptance approves planning text only. It does not resolve or waive
K0SC1-F1/F2/F3 or K0SC-R1/R2/R3, authorize K0-SC1 implementation, select any
input, permit custody copying, remote or board access, or start K0-SC2 or
K0-SC3. Implementation still requires a template-conforming exact
responsible-human instruction.

### Historical alternative: revisions requested

Had revisions been requested, a new exact plan target and review packet would
have been required. No revision request was recorded.

### Historical alternative: deferred

Had review been deferred, the target and packet would have remained
unaccepted decision support. No deferral was recorded.

## Post-decision validation

After the responsible-human decision was supplied, this acceptance-record
follow-up and its four current-status edits passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

The source check reported:

```text
site_markdown=96
policy_markdown=5
rendered_references=913
configured_routes=221
dot_sources=10
public_assets=10
tracked_html=0
network_events=0
generated_tree_changes=0
adversarial_cases=34
```

Additional checks confirmed unique target resolution, exact target/packet
lineage, unchanged target-plan blob, five-path acceptance-record boundary,
15 unchecked pre-decision checklist items, unresolved and unwaived findings,
privacy, and no change to accepted records, KVM0 tooling,
runtime/model/pathfinder content, dependencies, policies, instructions, or
publication gate.

**Status:** exact target
`9b9923f8a58fe7102a108cb2a976ea09979427a1` is responsible-human accepted
as planning text only. K0SC1-F1/F2/F3 and K0SC-R1/R2/R3 remain unresolved
and unwaived.

**Next:** before any implementation authorization, resolve the blocker-bearing
template fields or create a reviewed plan revision. K0-SC1 remains
not-authorized.

**Action required from you:** none for this recorded plan acceptance. Any plan
revision, implementation authorization, custody or selection decision, remote
or board access, readiness decision, successor, push, publication, or release
requires its own exact decision.
