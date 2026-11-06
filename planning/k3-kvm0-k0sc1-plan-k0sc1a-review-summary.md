<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# KVM0 K0-SC1-A plan revision review and acceptance record

This document began as the decision-neutral responsible-human review packet
for exact Plan revision K0-SC1-A target
`c00f4d000c845a7c3d62921c1d7939fc158744e2` and now also records the later
responsible-human decision on that immutable commit. The target remains byte
unchanged.

Packet commit `8a24fa4a33d5e0c94583e85d478c51a4cea624af` is the direct
child of the target and remains decision support. Neither the packet nor this
acceptance-record follow-up is revision content, implementation, custody,
selection, source evidence, hardware evidence, or package authority.

Except where a statement is explicitly marked current or post-decision,
sections 1 through 8 preserve the pre-decision review history. The 12
unchecked section 8 items remain that historical review instrument.

## Decision record

At `2026-10-05T08:35:30.800+02:00`, the responsible human supplied:

```text
accept c00f4
```

The abbreviation was checked against the local Git object database and
resolved uniquely to exact target
`c00f4d000c845a7c3d62921c1d7939fc158744e2`, whose parent is
`0c8a625df9d49254332b2105ae4b3c9cbe60a982` and whose tree is
`3607cf100677f75aaba0c2d03339b979bcbb3be3`.

The responsible human accepted that exact target as **planning corrections
only**. K0SC1-F1, K0SC1-F2, and K0SC1-F3 are addressed by the accepted
revision text. Acceptance does not claim those corrections have been
exercised by custody, ref, network, board, runtime, or hardware evidence.

K0SC-R1, K0SC-R2, and K0SC-R3 remain unresolved and unwaived. K0SC-R2 remains
open for K0-SC2 and K0-SC3 path maxima; K0SC-R3 remains open until authorized
custody is completed.

Acceptance does not authorize K0-SC1 implementation, custody copying,
selection, remote-ref checking, board access, K0-SC2, K0-SC3, package or
archive assembly, destination import, K0-S readiness, K0-X, K0-R, push,
publication, or release.

The target's own `proposed-not-reviewed`, `none`, `pending`, and
`not-authorized` fields remain frozen pre-decision content. This record and
the maintained current-position pages carry the later acceptance decision.
This acceptance-record follow-up remains unaccepted bookkeeping.

## 1. Decision summary

| Field | Review value |
| --- | --- |
| Review target | Exact commit `c00f4d000c845a7c3d62921c1d7939fc158744e2` (`docs: propose K0-SC1-A plan revision`) |
| Parent / comparison base | `0c8a625df9d49254332b2105ae4b3c9cbe60a982` |
| Git tree | `3607cf100677f75aaba0c2d03339b979bcbb3be3` |
| Accepted predecessor | Original K0-SC1 target `9b9923f8a58fe7102a108cb2a976ea09979427a1`, accepted as planning text only; its target, packet, and acceptance record remain immutable history |
| Current status | **Responsible-human accepted as planning corrections only** at the exact target above; the immutable target retains frozen pre-decision status fields |
| Automated review disposition | F1/F2/F3 are addressed by the accepted revision text; no significant new plan defect was found |
| Decision | Accepted by exact instruction `accept c00f4` at `2026-10-05T08:35:30.800+02:00` |
| Implementation / execution | K0-SC1 implementation, custody, selection, and remote-ref checking remain unauthorized or `NOT RUN`; K0-S remains `not-ready` |
| Successor / hardware status | K0-SC2 and K0-SC3 remain unauthorized; K0-SC3 and Beryllium/R8 K3 hardware remain `NOT RUN`; K0-X/K0-R remain blocked |
| Repository / branch | Current private Beryllium repository; `beryllium/single-hart-runtime-r0` |
| Push / tag state | Target is the clean local branch tip, 15 commits ahead of the last-fetched tracking ref, untagged; no network recheck was performed |
| Publication status | Push, tag, public migration, publication, release, paper submission, collaboration commitment, and upstream submission remain blocked |

**Action taken:** the responsible human accepted exact target
`c00f4d000c845a7c3d62921c1d7939fc158744e2` as planning corrections only.

This acceptance-record follow-up is unaccepted bookkeeping. It is not the
revision target and cannot authorize implementation.

## 2. Deliverables

The exact parent-to-target delta is five modified mode-`100644` planning
paths:

```text
M planning/HANDOFF.md
M planning/README.md
M planning/k3-kvm0-k0sc1-plan.md
M planning/project-orientation.md
M planning/roadmap.md
```

The target contains 236 insertions and 47 deletions.

| Deliverable | Paths | Purpose | Trust or privilege boundary | Highest-value human question |
| --- | --- | --- | --- | --- |
| K0-SC1-A revision | `planning/k3-kvm0-k0sc1-plan.md` | Correct the original plan's selftest ownership, finite-directory, and ref/stop-binding findings | Planning text only; accepted original remains immutable history | Do the three corrections resolve K0SC1-F1/F2/F3 without consuming K0-SC2, widening custody, or authorizing implementation? |
| Current-position placemat | `planning/roadmap.md` | Record the accepted original, proposed revision, pending decision, and unchanged gates | Status only | Are original acceptance and proposed-revision state visibly separate? |
| Returning-human guide | `planning/project-orientation.md` | Explain the proposed corrections and unchanged implementation/hardware boundary | Re-entry guidance only | Could a returning owner distinguish original acceptance, revision review, and package authorization? |
| Planning index | `planning/README.md` | Link and summarize the proposed revision | Navigation-level status only | Does discoverability avoid implying revision acceptance or implementation readiness? |
| Operational handoff | `planning/HANDOFF.md` | Preserve the exact base, proposed corrections, residual findings, and non-authorizations | Handoff only | Could a later session resume without starting custody, board, or remote work? |

No accepted original K0-SC1 plan/packet/record, K0-A/K0-I/K0-S/K0-SC
record, KVM0 destination tool, runtime, model, proof, dependency, policy,
instruction, generated page, or publication-gate byte changes in the target.

## 3. Claim boundary

### Supported by the exact target

The target supports saying:

- accepted original K0-SC1 target
  `9b9923f8a58fe7102a108cb2a976ea09979427a1` remains immutable accepted
  planning history with K0SC1-F1/F2/F3 unresolved and unwaived;
- K0-SC1-A proposes exact bounded corrections to those three findings;
- C5 now selects only ST01-ST16 IDs/names, order, argv, cwd, environment,
  timeouts, limits, exits, and markers;
- K0-SC2 explicitly retains ownership of selftest binaries and hashes, the
  runner/controller/16-binary install tree, the 18-entry install manifest, and
  the final structured command manifest;
- ordinary/root directory mode is `0755`, restricted directory mode is
  `0700`, maximum path depth is 64, ordinary directory count is at most 4,096,
  and `FILES.modes` rows are at most 6,191;
- the original regular-file, member, path-byte, control-size, expanded-byte,
  restricted-map, and zero-output caps remain;
- an exact ref-binding attachment and all mandatory stops `I1-I7,A1-A9` are
  required by the authorization template and validation; and
- revision acceptance would approve planning corrections only and would not
  authorize implementation.

### Trusted or assumed inputs

K0-SC1-A changes no draft-time aggregate identity. The original K0-SC1 plan's
12-record, 2,030-row, 46/53/45 profile, restricted-map, source-relation, and
ref-class values remain unrederived planning inputs. This packet did not
access private inputs or rederive them.

The branch's ahead state is a last-fetched local-ref observation. No remote
server, board, or hardware state was queried.

### Unavailable or `NOT RUN`

- no ref-binding attachment exists;
- no local/tracking record arrays or remote observation exist as K0-SC1
  candidate evidence;
- no custody root, custody copy, host selection, ST01-ST16 selection, ST16
  skip decision, or source-ref report exists;
- no directory closure or exact `FILES.modes` candidate has been measured
  against the new maxima;
- K0-SC1 implementation remains unauthorized;
- K0-SC2, K0-SC3, board characterization, hardware validation, package
  assembly, import, readiness, K0-X, and K0-R remain `NOT RUN` or blocked; and
- no push, tag, publication, or release occurred.

### Explicit non-claims

The target does not:

- resolve or waive K0SC-R1, K0SC-R2, or K0SC-R3;
- establish custody, preservation, source relation acceptance, ref
  verification, host/selftest/skip selection, or package acceptance;
- claim the 4,096-directory or 6,191-row maxima have been exercised;
- authorize copying, network, board access, QEMU, guest execution, real KVM
  selftests, import, readiness, or successors;
- establish KVM0 execution, K3 qualification, Beryllium hardware validation,
  retained-R8 evidence, Linux/BSP selection, B0/B1, services, devices, DMA,
  multicore, policy, attestation, or an MVP; or
- authorize push, tag, publication, release, migration, paper submission,
  collaboration outreach, venue selection, or upstream submission.

## 4. Security and correctness invariants

| Invariant | Target location | Revision control | Evidence or review boundary |
| --- | --- | --- | --- |
| Original accepted plan remains historical | `Plan revision K0-SC1-A`; `Controlling accepted history` | Exact accepted target/record named; revision has separate status/base/decision | Exact Git history and unchanged old packet/record path |
| C5 does not consume K0-SC2 | C5 row; `Selftest and skip decisions`; `Relationship to later packages` | Nine selection fields only; binaries/install/final manifest explicitly assigned to K0-SC2 | Textual invariant; no selftest selection exists |
| Directory/path/mode envelope is finite | `Ordinary input paths`; `Hard maxima and deterministic formulas` | Modes `0755/0700`; depth 64; directories 4,096; rows 6,191; existing caps retained | Arithmetic/text checks only; no custody candidate measured |
| Ref evidence is exact or `NOT RUN` | `Source-ref report disposition`; authorization template | Closed ref attachment, count/array/hash/relation/remote/governance/drift rules | No attachment or remote check exists |
| All stops are mandatory | `Stop conditions`; authorization template | Stable IDs `I1-I7,A1-A9`, exact ordered literal, no disable/rename/substitution | Textual invariant; no implementation authorization exists |
| Human decisions cannot be self-approved | Original selection/exit sections retained | Decision packets remain pending human decision | No decision packet exists |
| Board availability grants no hardware authority | Revision status/current pages | Board remains non-evidentiary; K0-SC3/hardware stay `NOT RUN` | No board contact occurred |

## 5. Review history and findings

### Findings addressed by the proposed revision

| Finding | Proposed disposition in K0-SC1-A | Review result |
| --- | --- | --- |
| K0SC1-F1: C5 crossed the K0-SC2 binary/install boundary | C5 is limited to nine selection fields; binaries, install tree/manifest, and final command manifest explicitly remain K0-SC2 | Textually addressed within scope |
| K0SC1-F2: no numeric directory/mode/row maximum | Adds directory modes, depth 64, directory maximum 4,096, row maximum 6,191, and existing-stop mapping A1/A2/A6 | Textually addressed within scope |
| K0SC1-F3: incomplete ref and stop binding | Adds closed ref attachment, mandatory ref rules, stable IDs for all 16 stops, exact authorization literal, and validation requirements | Textually addressed within scope |

No significant new plan defect was found in exact target
`c00f4d000c845a7c3d62921c1d7939fc158744e2`.

These dispositions remain **proposed, not resolved or waived**, until a
responsible human decides the exact revision target. K0SC-R1/R2/R3 remain
unresolved and unwaived. K0SC-R2 remains open for K0-SC2/K0-SC3 path maxima,
and K0SC-R3 remains open until authorized custody is completed.

## 6. Validation and retained evidence

### Pre-commit equivalent-content validation

Before commit, the equivalent five-path revision content passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

The source check reported:

```text
site_markdown=96
policy_markdown=5
rendered_references=916
configured_routes=221
tracked_html=0
network_events=0
generated_tree_changes=0
adversarial_cases=34
```

Additional checks covered exact F1 field ownership, F2 numeric/mode bounds,
F3 ref schema and stop IDs, five-path scope, privacy, and unchanged accepted
history.

### Exact-clean-target validation

On October 4, 2026, with exact target
`c00f4d000c845a7c3d62921c1d7939fc158744e2` as clean `HEAD`, these checks
passed:

```text
git diff --check \
  0c8a625df9d49254332b2105ae4b3c9cbe60a982 \
  c00f4d000c845a7c3d62921c1d7939fc158744e2
umask 0022 && npm run docs:source-check
```

The exact-target source check reported the same `96/5/916/221` source counts,
zero tracked HTML, zero network events, zero generated-tree changes, and 34
adversarial cases. The worktree remained clean.

Exact-target audit also confirmed:

- five modified mode-`100644` planning paths;
- target tree `3607cf100677f75aaba0c2d03339b979bcbb3be3`;
- unchanged accepted original plan/packet/record, K0-A/K0-I/K0-S/K0-SC
  records, KVM0 tooling, runtime/model/pathfinder, dependencies, policies,
  instructions, and publication gate; and
- last-fetched local branch state: 15 ahead, zero behind, untagged.

### Packet-follow-up pre-commit validation

On October 4, 2026, this packet and its four minimal status links passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

The source check reported:

```text
site_markdown=97
policy_markdown=5
rendered_references=920
configured_routes=221
dot_sources=10
public_assets=10
tracked_html=0
network_events=0
generated_tree_changes=0
adversarial_cases=34
```

Additional checks confirmed the exact five-path packet boundary, sections
1-9, unchanged revision-plan blob, F1/F2/F3 dispositions, unchecked human
checklist, privacy, and no change to accepted history, KVM0 tooling,
runtime/model/pathfinder content, dependencies, policies, instructions, or
publication gate.

Packet validation covers decision support and status integration only. It
cannot accept the revision or authorize implementation.

## 7. Recommended human review sequence

1. Confirm target, parent, tree, five-path inventory, accepted predecessor,
   and proposed/not-reviewed revision status.
2. Review the exact K0SC1-F1 C5 field set and K0-SC2 ownership.
3. Review F2 modes, path-depth definition, 4,096-directory and 6,191-row
   bounds, retained caps, and A1/A2/A6 mappings.
4. Review the exact ref-binding attachment keys and remote `NOT RUN` coupling.
5. Compare all 16 stop IDs and wording between stop definitions,
   authorization template, and validation.
6. Confirm original acceptance, residual K0SC-R1/R2/R3, board non-evidence,
   and every implementation/successor exclusion remain explicit.
7. Review exact-clean-target validation and current status links.

Useful read-only commands:

```sh
git --no-pager show --stat --summary \
  c00f4d000c845a7c3d62921c1d7939fc158744e2
git --no-pager diff --find-renames \
  0c8a625df9d49254332b2105ae4b3c9cbe60a982 \
  c00f4d000c845a7c3d62921c1d7939fc158744e2 -- \
  planning/k3-kvm0-k0sc1-plan.md \
  planning/roadmap.md planning/project-orientation.md \
  planning/README.md planning/HANDOFF.md
git --no-pager show \
  c00f4d000c845a7c3d62921c1d7939fc158744e2:planning/k3-kvm0-k0sc1-plan.md
```

## 8. Human decision checklist

- [ ] The accepted original K0-SC1 target and record remain immutable history.
- [ ] K0-SC1-A changes only the three reviewed findings.
- [ ] C5 contains exactly the nine permitted selection fields.
- [ ] Exact binaries, install tree/manifest, and final command manifest remain
      K0-SC2 obligations.
- [ ] Directory modes, depth 64, directory maximum 4,096, row maximum 6,191,
      regular-file/member/path/control/byte caps, and A1/A2/A6 mappings are
      acceptable.
- [ ] The ref attachment has a closed exact schema and consistent remote
      `NOT RUN` behavior.
- [ ] Stop definitions and authorization contain exactly
      `I1-I7,A1-A9`, each mandatory and unchanged.
- [ ] Human selection, custody, and source-ref disposition remain outside
      checker authority.
- [ ] K0SC-R1/R2/R3 remain unresolved and unwaived outside the bounded
      K0-SC1-A corrections.
- [ ] Board availability remains non-evidentiary; K0-SC3/hardware remain
      unauthorized and `NOT RUN`.
- [ ] No implementation, custody, selection, network, board, readiness,
      successor, push, publication, or release authority follows.
- [ ] Exact target `c00f4d000c845a7c3d62921c1d7939fc158744e2` is
      accepted, revisions are requested, or review is deferred.

## 9. After the decision

### Recorded outcome: accepted

The responsible human accepted exact target
`c00f4d000c845a7c3d62921c1d7939fc158744e2` at
`2026-10-05T08:35:30.800+02:00` by exact instruction `accept c00f4`.
Acceptance approves the bounded planning corrections only. It does not
authorize K0-SC1 implementation, custody, selection, ref checking, network,
board access, K0-SC2/K0-SC3, import, readiness, K0-X/K0-R, push, publication,
or release. A template-conforming exact instruction is still required.

### Historical alternative: revisions requested

Had revisions been requested, a new exact revision target and packet would
have been required. No revision request was recorded.

### Historical alternative: deferred

Had review been deferred, the target and packet would have remained
unaccepted decision support. No deferral was recorded.

## Post-decision validation

On October 5, 2026, after the responsible-human decision was supplied, this
acceptance-record follow-up and its four current-status edits passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

The source check reported:

```text
site_markdown=97
policy_markdown=5
rendered_references=920
configured_routes=221
dot_sources=10
public_assets=10
tracked_html=0
network_events=0
generated_tree_changes=0
adversarial_cases=34
```

Additional checks confirmed unique target resolution, exact target/packet
lineage, unchanged revision-plan blob, five-path acceptance-record boundary,
12 unchecked pre-decision checklist items, F1/F2/F3 planning-only treatment,
unresolved and unwaived K0SC-R1/R2/R3, privacy, and no change to accepted
history, KVM0 tooling, runtime/model/pathfinder content, dependencies,
policies, instructions, or publication gate.

**Status:** exact target
`c00f4d000c845a7c3d62921c1d7939fc158744e2` is responsible-human accepted
as planning corrections only. K0SC-R1/R2/R3 remain unresolved and unwaived.

**Next:** K0-SC1 implementation remains separately gated and requires one
template-conforming exact responsible-human instruction.

**Action required from you:** none for this recorded revision acceptance. Any
implementation authorization, custody or selection decision, remote or board
access, readiness decision, successor, push, publication, or release requires
its own exact decision.
