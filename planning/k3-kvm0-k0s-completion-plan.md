<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# KVM0 K0-S completion plan (K0-SC)

## Status and authority

This is a proposed, decision-neutral completion plan for the still-open KVM0
K0-S source-evidence readiness gate. It does not revise or replace accepted
KVM0 Plan revision K0-A. It defines three additional, independently gated
packages needed because the already authorized readiness-completion work
reached its fail-closed missing-byte and missing-provenance stop.

The responsible human authorized drafting this plan at
`2026-10-04T16:27:42.687+02:00` with:

```text
proceed, although k3 device will be offline for a few hours
```

The instruction authorizes planning only. The K3 board's temporary offline
state is operational scheduling input, not hardware evidence and not
authorization to use it when it returns.

This plan's immutable pre-decision status is:

```text
k0sc_plan_identity=K0-SC
k0sc_plan=proposed-not-reviewed
k0sc_plan_target=none
k0sc_plan_base=ffb75f193b4697d14252341cdb1459c7812b873a
k0sc_drafting_authorization=authorized
k0sc_drafting_authorization_timestamp=2026-10-04T16:27:42.687+02:00
k0sc1=not-authorized
k0sc2=not-authorized
k0sc3=NOT-RUN-not-authorized-board-offline
k0s_readiness_completion_authority=paused-at-missing-input-stop
k0s_readiness_completion_authority_consumed=no
k0s_readiness_completion_authority_revoked=no
k0s_readiness=not-ready
k0x=blocked-not-authorized
k0r=blocked-no-result
beryllium_k3_hardware=NOT-RUN
r8_k3_hardware=NOT-RUN
development_kernel_bsp=UNDECIDED
publication=blocked
```

Plan acceptance would approve only this planning boundary. It would not
authorize K0-SC1, K0-SC2, K0-SC3, copying, selection, rebuilding, recapture,
board access, package assembly, destination import, K0-S readiness, K0-X,
K0-R, B0, B1, an R8 successor, push, publication, or release.

## Controlling accepted history

K0-SC preserves these exact boundaries:

| Boundary | Exact identity and effect |
| --- | --- |
| KVM0 Plan revision K0-A | Accepted target `5227266ceddb664a1595e22e5a92da57a013652f`; defines K0-P/K0-I/K0-S/K0-X/K0-R, the 15-control bundle, privacy, serial safety, digest order, K0-X shape, and non-claims |
| K0-I destination tooling | Accepted target `abd092a1f2734c720a205803c29496fe2245b0ef`; offline importer, generator, checker, and rejection tests only |
| K0-S status record | Accepted documentation target `c65705582c243dd908ff47d3189df07601167400`; accurate status only, not readiness or source acceptance |
| Project-status roadmap | Accepted documentation target `a9bb91df94f7e1df2b0e7f2d3ca057f6516ea511`; current status and future gates only |
| Current planning base | Unaccepted bookkeeping HEAD `ffb75f193b4697d14252341cdb1459c7812b873a` |
| October 4 readiness-completion authority | Bound to Beryllium base `a8e137ebbbeeff2a5475050b047a8ec6109d22e0`; already-retained offline payload and external archive only, with rebuild, board, live-capture, import, K0-X, push, and publication excluded |

K0-SC neither widens, consumes, nor revokes the October 4
readiness-completion authority. That authority remains paused at its explicit
stop because required bytes and provenance were unavailable. Recovered
metadata, newly custodied bytes, rebuilt outputs, or board observations do not
become "already-retained payload bytes" under that earlier instruction.

## Preserved source relation

The selected exact-Git route remains unchanged:

```text
kvm_base=a5f72fd298f6bd02e6d30599dafb43cfa16576b6
prepared_candidate_commit=c1c7e254143f99d4ad3cdbf25021a76364d6d75a
prepared_candidate_tree=a5f77b5acef26d8975fe756512edbd2413fa1239
board_enablement_patch_count=14
host_release=7.3.0-rc4-k3-kvm-host-a1
source_relation_status=recorded-not-accepted
```

No K0-SC package may rewrite that commit, move its selected ref, change the
base/tree/patch count/release, or silently substitute another source relation.
A changed relation requires a new reviewed plan revision.

## Draft-time diagnostic input

The following observations were derived during plan drafting. They are
diagnostic planning input, not accepted evidence. Every load-bearing value
must be rederived at the exact future package target under its separately
authorized gate:

- the current 46-file, 53-path, 45-checksum preparation profile passed all 12
  documented local-only checks;
- 45 profile tests and 17 output-only-capture tests passed;
- the network-dependent source remote-ref check was `NOT RUN`;
- all 12 profile-named discovery records were recovered from the original
  private owner-session artifact-storage class and matched their profile
  SHA-256 identities;
- the profile's `discovery-closure-v1.json` SHA-256 was
  `d7d48d43686960e06e25750f2da0965fe0514e7c399b29afbc41baf623aee5f4`;
- the sorted `basename<TAB>sha256<LF>` identity of its 12 discovery inputs was
  `3fc33b42c2b4ce4727ecc869fb38aeba1ad23f1bf1b394a384c6d1781d627a83`;
- all 2,030 rows of the multi-origin host-artifact manifest, whose file
  SHA-256 is
  `015f53fe41ab689736116ce8fae64ef0466cd4327b7d575b30379e8977f60b2a`,
  matched current mode, size, and SHA-256; and
- a 77-role diagnostic matrix remained `not-ready`.

The records and byte paths remain private. This plan retains only bounded
identities, counts, and dispositions. It contains no private locator, remote
URL, human-readable restricted provenance, host/device identifier, or
sensitive absolute path.

## Objective

K0-SC asks:

> Can K0-S reach one reviewable source-evidence readiness candidate through
> separately authorized custody and selection, offline replacement-input
> construction, and read-only board characterization, while preserving K0-A,
> preventing historical-identity impersonation, and leaving K0-X separately
> gated?

The answer remains unknown. K0-SC provides an ordered method; it is not a
readiness claim.

## Gate model

The three packages are ordered but independently authorized:

```text
accepted K0-SC plan
  -> separate K0-SC1 authorization
  -> K0-SC1 exact decision
  -> separate K0-SC2 authorization
  -> K0-SC2 exact decision
  -> separate K0-SC3 authorization after the board is online
  -> K0-SC3 exact decision
  -> separately planned reconciliation and package assembly
  -> separate K0-I destination import
  -> separate K0-S readiness review
```

Each gate requires an exact responsible-human instruction naming:

- the full Beryllium base SHA;
- the source/profile/recovered-input relation;
- the complete path and mode inventory;
- the permitted tools and command classes;
- output and retention boundaries;
- stop conditions; and
- explicit exclusions.

No broad `proceed with K0-SC` instruction substitutes for a package-specific
authorization.

## Blocker assignment

Every known load-bearing blocker is assigned once:

| Blocker | Assigned package or successor | Required disposition |
| --- | --- | --- |
| Stable private custody for the 12 recovered discovery records | K0-SC1 | Exact immutable member inventory and external identity under separately approved package-specific custody; no general evidence-store design |
| Stable custody for the 2,030-row multi-origin host set | K0-SC1 | Reverify exact bytes at the future target and bind each selected object to one origin and immutable identity |
| Fresh local/tracking/remote source-ref relation | K0-SC1 | Recheck local and tracking refs; perform the separately authorized read-only remote check or retain `NOT RUN` |
| Host build/stage artifact selection | K0-SC1 | Responsible-human select, revise, or defer one exact existing host candidate set |
| Exact 16-test set and proposed single skip | K0-SC1 | Human approve, revise, or defer the exact ST01-ST16 set and ST16 skip identity/marker/reason |
| Restricted provenance custody | K0-SC1 | Keep mode `0600`, outside Git/ordinary bundle/archive/import; bind only exact size, SHA-256, opaque IDs, and coverage |
| Exact host initramfs bytes for the future package | K0-SC2 | Construct a new replacement input from pinned sources/tools or stop; never claim recovery of the unavailable historical bytes |
| Native QEMU 10.2.2 binary/source/build/dependency closure | K0-SC2 | Supply pinned open source, exact build environment/argv, binary identity, configuration, and dependency closure under a new identity |
| Exact minimal guest kernel/initramfs target | K0-SC2 | Produce one immutable new guest target with source, tool, package, marker, and artifact closure |
| Exact K0-A launcher and marker source | K0-SC2 | Implement and retain the reviewed structured argv/marker contract without executing guests |
| Immutable non-empty block seed and overlay recipe | K0-SC2 | Produce new exact bytes, manifest, immutable-seed rule, fresh-overlay construction, and pre/post hash contract |
| Complete compatibility/native CPU profiles and guest-H absence evidence | K0-SC2 | Retain exact profile definitions and offline query/source basis; do not infer from prior runs |
| Complete host rootfs package/repository closure | K0-SC2 | Retain exact package inventory, dependency closure, repository snapshot identity, configuration, and rootfs artifact relation |
| Exact selftest binaries and 18-entry install manifest | K0-SC2 | Bind runner, controller, 16 binaries, modes, sizes, SHA-256, source/build provenance, and relocation-safe install manifest |
| Exact build/hash/archive/capture/git/make/node/shell/compiler/linker records | K0-SC2 | Complete the K0-A tool manifest with open, immutable provenance; archive and capture tools may remain prospective until their later use |
| Exact structured command manifest | K0-SC2 | Complete argv arrays, environment allowlists, timeouts, exits, markers, and evidence paths; no evaluable shell strings |
| Exact live FDT bytes | K0-SC3 | Read-only capture from the running board under an exact command/transport authorization; static DTB is not a substitute |
| Current board initramfs identity and relation to the K0-SC2 replacement | K0-SC3 | Read-only hash/metadata capture; mismatch is explicit and does not overwrite either identity |
| Firmware chain and exact firmware-set selection | K0-SC3 | Read-only ROM/first-mutable/U-Boot/OpenSBI facts and accessible byte/config identities; inaccessible facts remain `UNKNOWN` |
| Current board/host/KVM facts needed for readiness | K0-SC3 | Read-only bounded capture only; no qualification run and no K0-X session |
| Final 15-control payload, checksum file, report placeholder, and external archive | Later separately planned reconciliation and package assembly | Reconcile K0-SC1/2/3 without silent substitution; finalize payload before checksum and archive identities |
| Destination safe import and deterministic double derivation | Existing K0-I successor gate | Separate import authorization; no board/network/SSH/serial access |
| K0-S readiness decision | Existing K0-S review gate | Exact decision-neutral target and packet; checks cannot accept themselves |

Any newly discovered blocker must be assigned through a reviewed plan revision.
It must not be silently folded into another package.

## K0-SC1: custody and exact selection

### Purpose

K0-SC1 prepares one reviewable decision about stable package-specific custody
and exact selection of currently available inputs. It does not choose a
general evidence-retention architecture and does not implement Option A Phase
2.

### Maximum input classes

- the 12 profile-named recovered discovery records at their exact historical
  hashes;
- the exact 2,030-row multi-origin host manifest and currently matching bytes;
- the current preparation profile and its restricted provenance binding;
- the exact source relation and selected local/tracking ref records; and
- the exact retained selftest-selection inputs.

### Deliverables

1. one decision-neutral custody inventory naming every ordinary record by
   opaque ID, type, mode, size, SHA-256, origin class, and privacy class;
2. one separate restricted-map custody statement carrying only mode, size,
   SHA-256, coverage, access policy, and exclusion rules;
3. one host-artifact selection packet;
4. one selftest/single-skip selection packet;
5. one exact source-ref report, with remote status either checked under
   explicit authority or `NOT RUN`; and
6. one exact changed-path/mode inventory for the future K0-SC1 candidate.

### Exit condition

K0-SC1 exits only after the responsible human records exact decisions on
custody, host-artifact selection, the 16-test set, and the proposed skip. A
passing inventory does not select or accept its contents.

### Stop conditions

Stop on:

- any recovered-record or host-manifest hash/mode/size drift;
- missing or duplicated origin mapping;
- restricted material entering Git, the ordinary bundle, or an ordinary
  archive;
- a required general evidence-store design or Phase 2 decision;
- source-relation drift or candidate ref rewrite;
- a seventh artifact-selection class not enumerated here; or
- any need to access the board, rebuild bytes, or run a guest.

## K0-SC2: offline replacement inputs

### Purpose

K0-SC2 creates new, explicitly replacement-scoped offline inputs for facts
whose historical bytes or provenance are unavailable. New outputs receive new
IDs, hashes, timestamps, source relations, and claim boundaries. They never
reuse or impersonate historical identities.

### Entry gate

K0-SC1 must have an exact responsible-human decision. A separate K0-SC2
instruction must then name:

- the exact selected inputs;
- every source archive/commit/tree and package snapshot;
- the immutable offline tool/dependency set;
- every command and output path;
- the complete maintained and generated path inventory; and
- the replacement-versus-historical relation.

### Permitted classes

The future authorization may permit bounded offline:

- build, inspection, hashing, and static checking of a new host initramfs;
- build, inspection, hashing, and static checking of QEMU 10.2.2;
- build and static checking of the minimal guest and its initramfs;
- construction of the launcher, immutable block seed, and overlay recipe;
- generation of exact CPU profiles and guest-H absence evidence from pinned
  source/tool inputs;
- rootfs package/repository closure capture from an immutable offline source;
- construction and hashing of the exact selftest install tree; and
- completion of tool, artifact, and command manifests.

No K0-SC2 package may boot the board, access `/dev/kvm`, launch QEMU, run a
guest, run real KVM selftests, use a mutable package repository, or download a
dependency during normative work.

### Exit condition

K0-SC2 exits only with:

- all replacement bytes present and hash-bound;
- complete source/tool/dependency/command provenance;
- host-only negative and determinism checks;
- exact replacement-versus-historical non-claims; and
- a responsible-human decision on one exact K0-SC2 target.

Any new identity changes the K0-A profile inputs. Human review of those exact
changes is mandatory before K0-X can be considered.

## K0-SC3: read-only board characterization

### Current state

```text
k0sc3=NOT-RUN-not-authorized-board-offline
```

The board returning online does not change this state.

### Purpose

K0-SC3 captures only current read-only board facts that cannot be established
offline. It is not KVM0-C, not a K0-X boot session, not qualification, and not
Beryllium or retained-R8 hardware evidence.

### Separate authorization requirements

The exact future instruction must bind:

- one board-profile pseudonym and non-sensitive hardware class;
- the current boot/session pseudonym;
- the transport and its read-only or command-input boundary;
- the exact command manifest and output paths;
- the current host release and expected K0-SC2 identities;
- time, size, privacy, and failure bounds; and
- permitted human safety actions, if any.

### Permitted read-only facts

The future bounded run may collect:

- exact live FDT bytes, size, and SHA-256;
- current initramfs file identity and relation to the K0-SC2 replacement;
- accessible ROM, first mutable stage, U-Boot, and OpenSBI/M-mode identities
  and configuration facts;
- exact `/proc/cmdline`, kernel release/build identity, CPU/hart topology,
  KVM API/module/parameter facts, and `/dev/kvm` metadata/openability; and
- bounded current-boot facts required to distinguish selected from
  incompatible candidate sets.

### Prohibitions

Automation must not:

- reboot, reset, power-cycle, or invoke shutdown;
- write serial, send a newline or break, or alter termios;
- flash firmware or change U-Boot variables, boot order, boot media, or other
  persistent state;
- execute real KVM selftests, QEMU guests, C01-C08, or N01-N08;
- treat PMR-077, earlier boots, historical logs, or static DTBs as current
  capture; or
- convert inaccessible facts into defaults.

### Exit condition

K0-SC3 exits only with a complete checked read-only record or an explicit
failure/`UNKNOWN` ledger, followed by a responsible-human decision on one
exact target. It cannot satisfy KVM0-C or authorize K0-X.

## Later separately gated successors

K0-SC1 through K0-SC3 do not themselves create an importable package.
Separate later planning and authorization are required for:

1. reconciliation of selected, replacement, and board-observed identities;
2. final ordinary payload assembly while keeping restricted provenance
   separate;
3. final report-placeholder, `checksums.sha256`, external archive, and
   external approval-record construction in K0-A's cycle-free order;
4. K0-I destination import and two deterministic derivations; and
5. one exact K0-S readiness target, review packet, and responsible-human
   ready/revise/defer decision.

No successor is authorized by accepting this plan or any one K0-SC package.

## Path and mode boundary

This proposed plan target may change exactly:

```text
100644 planning/k3-kvm0-k0s-completion-plan.md
100644 planning/roadmap.md
100644 planning/project-orientation.md
100644 planning/README.md
100644 planning/HANDOFF.md
```

A sixth path, generated HTML, VitePress configuration, renderer/browser
inventory, glossary change, accepted-record edit, source/profile path,
runtime/tooling path, or private artifact is a stop requiring a revised plan.

The later decision-neutral review packet may change only:

```text
100644 planning/k3-kvm0-k0s-completion-plan-review-summary.md
100644 planning/roadmap.md
100644 planning/project-orientation.md
100644 planning/README.md
100644 planning/HANDOFF.md
```

That packet may review this plan target. It may not rewrite it or record a
decision on the human's behalf.

## Validation for the proposed plan

The proposed plan target requires:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

It additionally requires:

- exact five-path changed-file inventory from base
  `ffb75f193b4697d14252341cdb1459c7812b873a`;
- Markdown link and maintained-status consistency checks;
- no generated-tree changes;
- no private source/profile/session locator;
- no device serial, MAC address, filesystem UUID, hostname, routable address,
  credential, token, restricted human identity, or private remote URL;
- no non-home absolute path except literal future contract paths already
  accepted by K0-A, if any; and
- explicit audit that accepted K0-A, K0-I, K0-S, R0-R8, and publication-gate
  bytes remain unchanged.

Generated HTML and Chromium are deferred under the accepted source-first
documentation policy.

## Claim and non-claim boundary

This plan supports saying only:

- the missing-input problem has been decomposed into three bounded gates;
- recovered metadata and currently matching host bytes exist as draft-time
  diagnostic input;
- board-dependent work is explicitly deferred and `NOT RUN`; and
- exact later human decisions are required before every action.

It does not claim:

- K0-S readiness or completion;
- source-relation, artifact-set, firmware-set, selftest-set, skip, or profile
  acceptance;
- stable custody, immutability, preservation, or evidence-store deployment;
- historical-byte recovery for any rebuilt input;
- KVM0 execution, K3 qualification, Beryllium hardware validation, or
  retained-R8 evidence;
- Linux/BSP selection, B0/B1, an H0 successor, H1-H4, services, devices, DMA,
  multicore, policy, attestation, or an MVP;
- push, tag, publication, release, migration, paper submission, collaboration
  commitment, or upstream submission.

## Decision required

After an exact proposed-plan commit and decision-neutral review packet exist,
the responsible human may:

1. accept that exact K0-SC plan target;
2. request a revised plan target; or
3. defer K0-SC.

Acceptance would authorize no implementation. K0-SC1 would still require its
own exact instruction.
