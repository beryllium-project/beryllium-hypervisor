<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 Linux/KVM qualification plan (KVM0)

## Status and authority

KVM0 is a proposed, decision-neutral qualification stage for one exact Linux
KVM host and one exact minimal RV64 guest on one exact SpacemiT K3 CoM260
profile. It is separate from Beryllium R8-H0 through R8-H4 and is not a
Beryllium hardware run.

The first proposed plan is preserved at exact commit
`459184dd8fe9c5da20e27a9e277a076685a520cb`, with its first decision-neutral
packet at descendant commit
`8348b18a2c00c992e8fbf744f2004dfcd55500e6`. Independent review found five
material planning defects. **Plan revision K0-A** supersedes that first
proposal for current review while preserving both exact objects as historical,
unaccepted decision support. Neither the first proposal nor K0-A is accepted.

This file is planning text only. Its immutable pre-decision status is:

```text
kvm0_original_plan_target=459184dd8fe9c5da20e27a9e277a076685a520cb
kvm0_original_plan_packet=8348b18a2c00c992e8fbf744f2004dfcd55500e6
kvm0_original_plan_status=superseded-unaccepted
kvm0_plan_revision=K0-A
kvm0_plan_revision_k0a=proposed-not-reviewed
kvm0_plan=proposed-not-reviewed
kvm0_plan_target=none
kvm0_gate_k0p=pending-exact-plan-decision
kvm0_gate_k0i=blocked-not-authorized
kvm0_gate_k0s=blocked-source-evidence-not-ready
kvm0_gate_k0x=blocked-not-authorized
kvm0_gate_k0r=blocked-no-result
kvm0_implementation_authorization=not-authorized
kvm0_execution_authorization=not-authorized
kvm0_result=NOT-RUN
kvm0_hardware_claim=none
kvm0_source_evidence=discovery-only-not-importable
development_kernel_bsp=UNDECIDED
r8_h0_row_resolution=none
r8_h1_h4=not-started-unauthorized
r8_k3_hardware=NOT-RUN
beryllium_k3_hardware=NOT-RUN
publication=blocked
```

The responsible human must make separate decisions for:

1. **K0-P:** acceptance, revision, or deferral of one exact KVM0 plan commit;
2. **K0-I:** authorization of any destination-side KVM0 checker or report
   tooling;
3. **K0-S:** authorization and readiness of any source-owner build, exact
   selftest preparation, or immutable evidence package;
4. **K0-X:** authorization of the exact attended three-session K3 execution
   profile; and
5. **K0-R:** acceptance, revision, or deferral of one exact KVM0 result
   commit.

Acceptance of this plan would satisfy only item 1. It would not authorize
implementation, build, board access, boot, reset, power control, serial
input, KVM execution, evidence import, B0, B1, an H0 successor, H1-H4, a
development kernel/BSP selection, push, publication, or release.

## Plan revision K0-A: independent-review corrections

**Status: proposed, not reviewed.** K0-A makes five bounded planning
corrections and grants no implementation, source-owner, execution, result,
successor, or publication authority:

1. It replaces the report's impossible self-digest requirement with a
   cycle-free digest order: the report names its checksum-manifest location,
   `checksums.sha256` hashes every other retained member, and the final archive
   digest exists only outside the archive.
2. It separates the future KVM0-B implementation inventory from an exact
   KVM0-G documentation/review inventory containing only the required evidence
   and packet Markdown, maintained status/HANDOFF pages, planning navigation,
   the shared planning-page browser inventory, and generated `docs/html/**`.
3. It makes K0-P, K0-I, K0-S, K0-X, and K0-R separately visible and keeps
   source-owner build/selftest preparation distinct from destination tooling
   and from the three attended native execution sessions.
4. It transcribes the supplied live-board and evidence-gap facts explicitly as
   uncommitted, externally supplied, non-evidentiary discovery that is neither
   a Beryllium run nor retained R8 evidence.
5. It replaces public human-readable source-owner and patch-author fields with
   stable opaque provenance identifiers while requiring a separate restricted,
   hash-bound mapping that preserves auditable human provenance and is excluded
   from ordinary reports and publication.

The first proposed plan target and packet remain immutable historical objects.
Review of K0-A must name the new exact plan commit; no decision on the first
proposal transfers to K0-A.

## Relationship to accepted R8-H0/R8-C

The accepted non-privileged H0/R8-C target is:

```text
target=1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4
parent=d18b1c9c6ca8a0f2285f820ec960258620ae4b50
tree=7a9d80d08d0abb771d43cf76a4a297d9d668b375
```

KVM0 must preserve that exact target and its accepted evidence boundary:

- KVM0 edits no accepted H0, R0-R7, runtime, proof, checker, profile, or
  acceptance byte.
- KVM0 does not resolve, replace, reinterpret, or reduce any of H0's 147
  rows, 118 `UNKNOWN` values, 80 H0-acceptance blockers, 33 H1-completion
  blockers, three H2-entry blockers, `BLOCKED-NOT-READY`, or
  `r8_h0_exit=not-met`.
- A KVM0 PASS would establish only the exact Linux/KVM qualification result
  defined here. It would not be retained R8 evidence and would not authorize
  H1, H2, H3, or H4.
- K3 remains `NOT RUN` for Beryllium and hardware remains `NOT RUN` for R8.
- The development kernel/BSP remains `UNDECIDED`.
- If a later proposal needs any KVM0 fact in H0 or R8, it must define a new
  reviewed H0-successor plan, exact accepted base, exact relation, path
  boundary, evidence transfer rule, and separate implementation
  authorization. KVM0 acceptance alone supplies none of those.

## Objective

KVM0 asks one bounded prerequisite question:

> On one exact K3 CoM260 board, boot chain, Linux host, KVM source target,
> QEMU build, minimal guest, and attended recovery profile, can three native
> boot sessions each complete one fixed KVM selftest set and two fixed
> eight-case guest matrices using hardware KVM acceleration, deterministic
> pass markers, bounded timeouts, and retained exact provenance?

The result is a **Linux KVM qualification result on K3 CoM260**. It is not:

- a Beryllium boot or Beryllium hardware result;
- an R8 H0, H1, or H2 result;
- a general K3 Linux-support claim;
- a development-kernel/BSP selection;
- a KVM correctness or isolation proof;
- a production, performance, endurance, thermal, device-assignment, or
  nested-virtualization qualification; or
- authority to start B0, B1, retained R8 work, or a public release.

## Discovery-only source input

The following facts were reported from a private source workspace on
2026-09-25. They are retained here only to explain the proposed profile and
its missing evidence. They are **uncommitted discovery**, not plan evidence,
not imported KVM0 evidence, and not a source-owner acceptance record.

| Discovery field | Reported value | KVM0 treatment |
| --- | --- | --- |
| Source branch and HEAD | `main` at `796862989c06762a1bf18acda6d56dbdb913c930` | Discovery identity only. It is not an immutable evidence target. |
| Source worktree state | 10 tracked modifications and 36 untracked entries | Dirty state is disqualifying for evidence import. |
| Source collaboration ledger | No root `COLLAB.md` | The source remained read-only; no guest ledger write was possible or attempted. |
| Direct KVM result in tracked source HEAD | None | No KVM result may be inferred from tracked source HEAD. |
| Direct KVM evidence tracking | Reported direct KVM evidence is untracked | Untracked material is mutable discovery only and cannot enter KVM0 evidence. |
| Candidate host release | `7.3.0-rc4-k3-kvm-host-a1` | Proposed exact host release string, pending immutable source-owner evidence. |
| KVM base | `a5f72fd298f6bd02e6d30599dafb43cfa16576b6` | Proposed exact base, pending source-owner relation evidence. |
| Prepared candidate | commit `c1c7e254143f99d4ad3cdbf25021a76364d6d75a`, tree `a5f77b5acef26d8975fe756512edbd2413fa1239` | Proposed first eligible host-source target. A different target requires review before execution. |
| Board-enablement delta | 14 patches | Exact order, subjects, blobs, and patch IDs remain unavailable and are required. |
| QEMU | 10.2.2 | Proposed exact version; source, configuration, binary, and dependency provenance remain required. |
| Guest matrices | Two eight-case matrices | Shape is retained and strengthened below; discovery outputs do not count. |
| KVM selftests | 15 passed, one skipped | Discovery count only. Exact test names, commands, skip reason, outputs, and source target are required. |
| Candidate Image SHA-256 | `f72cbc683b2919c17ecfa8f8379b74ee0b9f65b9bcb25319f7cd499ce5048853` | Must match an immutable source-owner artifact manifest or execution stops. |
| Candidate config SHA-256 | `a063191962b26c2782081b1267abb53bfc79660318d9b2468afa0b2a307faa4d` | Must match an immutable source-owner artifact manifest or execution stops. |
| Candidate DTB SHA-256 | `dc338c5c92966f84ab6494cc4a3a1fdef70a0296e8d4ec8a26f9f212aaf18575` | Must match an immutable source-owner artifact manifest or execution stops. |
| Exact live FDT SHA-256 | Missing | The static DTB artifact hash does not substitute for the live FDT; this is a K0-S/K0-X blocker. |
| Exact live initramfs SHA-256 | Missing | The live initramfs identity is a K0-S/K0-X blocker. |
| Firmware/OpenSBI provenance | Missing | Hard blocker before execution authorization. |
| Guest H / nested virtualization | Guest H absent; nested virtualization not tested | Guest H remains absent in KVM0; nested virtualization remains an explicit non-claim. |
| Missing evidence | No endurance, performance, thermal, VFIO, DMA, libvirt, UEFI, or persistent Fedora guest evidence | Preserved as explicit non-claims. |
| Recovery observation | In-band reboot failed | Discovery only. KVM0 must not depend on in-band host reboot. |
| Current board control kernel | `7.1.5-201.0.riscv64.omni.fc44.riscv64` | The board was reported back on this Fedora control kernel; it is not the KVM0 candidate, a selected BSP, or evidence. |

None of the discovery counts, hashes, outputs, or candidate identities count
as KVM0 evidence until one immutable source-owner target or one explicitly
approved immutable bundle satisfies the import contract below.

The following live facts were also supplied externally. They are uncommitted,
externally supplied, non-evidentiary discovery only. They are not a Beryllium
run, not retained R8 evidence, and not a substitute for exact K0-S/K0-X
manifests or repeated execution:

| Live discovery field | Externally supplied value | KVM0 treatment |
| --- | --- | --- |
| Board identification | `CoM260 IFX` | Discovery label only; exact board/SKU/revision provenance remains required. |
| Hart population | Eight X100 harts | Discovery only; exact present/possible/online masks and parked-state treatment remain required. |
| Virtualization extension | `H` | Discovery only; exact ISA and KVM capability evidence remain required. |
| G-stage mode | `Sv39x4` | Discovery only; no Beryllium or KVM0 translation claim follows. |
| VMID width | `VMID14` | Discovery only; exact KVM extension and host evidence remain required. |
| Interrupt virtualization | `AIA7` | Discovery-only reported label; exact topology and command-manifest treatment remain required. |
| Host KVM configuration | Built-in KVM | Discovery only; exact config, source, boot, and live API evidence remain required. |
| `/dev/kvm` access | User-openable | Discovery only; exact type, owner class, mode, API version, and session facts remain required. |
| Live QEMU | `10.2.2` | Discovery only; exact source, configuration, dependency closure, binary hash, and feature query remain required. |

## Cross-repository usage and governance

This plan is the bounded destination usage report required because the source
workspace has no root `COLLAB.md` and grants no guest-ledger write surface.

| Item | Destination treatment |
| --- | --- |
| Guest role | Beryllium destination consumer preparing planning text only |
| Source access | Read-only discovery already supplied to this task; no source repository access or write by this work |
| Source ledger | Absent; no `COLLAB.md` was created, appended, or inferred |
| Adopted input | Candidate identities, artifact hashes, matrix shape, selftest count, missing-provenance facts, and recovery limits, all labeled discovery-only |
| Rejected inference | No KVM PASS, source cleanliness, provenance closure, BSP selection, hardware qualification, or Beryllium/R8 result follows |
| Destination path | `planning/k3-kvm0-plan.md` and its later exact review packet |
| Stale-assumption rule | Any source target, artifact, firmware, command, board profile, or result difference is surfaced explicitly; it is never silently normalized |

No private source code, raw capture, private remote, credential, device
identifier, or sensitive absolute path belongs in committed Beryllium
documentation.

## Decision gates

### Gate K0-P: exact plan decision

The responsible human may accept one exact immutable KVM0 plan commit,
request revisions, or defer. Acceptance approves only the planning boundary.

### Gate K0-I: implementation authorization

After plan acceptance, a separate instruction must authorize an exact
destination-side implementation relation and path inventory for offline
bundle checking and deterministic report generation. No implementation may
begin from plan acceptance alone.

### Gate K0-S: source-owner build and evidence readiness

Plan acceptance and K0-I do not authorize source-side build, selftest
selection, artifact preparation, or evidence capture. A separate
responsible-human instruction must authorize that bounded source-owner work.
Before any imported result can count, the source owner must then supply
either:

1. one exact clean immutable Git target and tree containing or binding the
   complete KVM0 source, build, command, artifact, and result manifests; or
2. one explicitly responsible-human-approved immutable bundle identified by
   exact SHA-256 and complete member manifest when a Git target cannot contain
   the retained artifacts.

The current dirty source `main` HEAD does not satisfy this gate.

### Gate K0-X: execution authorization

After K0-P, K0-I, and K0-S, a separate responsible-human instruction must
authorize:

- the exact board profile;
- the exact source target or bundle;
- the exact firmware/U-Boot/OpenSBI chain;
- the exact host and guest artifacts;
- the exact command-manifest SHA-256;
- exactly three attended native boot sessions;
- one exact 16-command KVM selftest set in each session;
- compatibility cases C01-C08 and native cases N01-N08 in each session,
  totaling 48 guest cases;
- the permitted human-only boot/reset/recovery actions; and
- the fixed selftest and guest matrices below.

No broad authorization such as "run KVM0" substitutes for these exact inputs.

### Gate K0-R: exact result decision

After all authorized runs and offline checks, a decision-neutral review packet
must name one exact KVM0 result commit and parent. The responsible human may
accept that result, request revisions, or defer. A passing report cannot
accept itself.

## Ordered phases and deliverables

| Phase | Deliverable | Entry gate | Exit condition |
| --- | --- | --- | --- |
| KVM0-A: source freeze | Immutable source-owner target or approved immutable bundle, complete source/patch/tool/firmware/artifact/command manifests | Accepted plan and separate source-owner work authority | Every required member exists, hashes match, worktree or bundle is immutable, and no discovery-only state is promoted |
| KVM0-B: offline import | Destination-side safe importer, schema checker, mutation tests, and bounded `build/kvm0/` reconstruction | Separate K0-I authorization | Network/SSH/serial-free exact import passes twice with identical deterministic output |
| KVM0-C: attended boot preflight | Exact board, boot medium, U-Boot/OpenSBI, capture, known-good fallback, `/proc/cmdline`, live FDT, and KVM-host facts | Separate K0-X authorization | Session is exact, capture is continuous and output-only, KVM is available, and no persistent boot state changed |
| KVM0-D: host qualification | Exact KVM selftest set on each of three native boot sessions | KVM0-C for the current session | Each session has exactly 15 PASS and one approved SKIP from the immutable manifest |
| KVM0-E: guest matrices | Compatibility and native CPU-profile matrices, eight cases each, once per boot session | KVM0-D for the current session | 48 total cases complete with exact markers, expected exits, no fallback, and no unauthorized retry |
| KVM0-F: recovery and closeout | Failure, timeout, recovery, and post-run host-state record | Completion or first failure | Every failed/not-run case and every human action is explicit; no success-shaped recovery |
| KVM0-G: report and review | Deterministic report, bounded evidence manifest, evidence page, and exact-commit review packet | Complete checked inputs | Exact result is presented decision-neutrally; no acceptance or successor authority is inferred |

Each phase may stop the package. No phase automatically authorizes the next.

## Proposed destination path boundary

This K0-A planning revision and its maintained current-position integration
may change only:

```text
planning/k3-kvm0-plan.md
planning/HANDOFF.md
planning/project-orientation.md
planning/roadmap.md
planning/README.md
planning/.vitepress/config.mts
pathfinder/tests/check-docs-render.mjs
docs/html/**
```

The later K0-A decision-neutral packet is not part of the plan target. Its
maximum follow-up inventory is:

```text
planning/k3-kvm0-plan-k0a-review-summary.md
planning/HANDOFF.md
planning/project-orientation.md
planning/roadmap.md
planning/README.md
planning/.vitepress/config.mts
pathfinder/tests/check-docs-render.mjs
docs/html/**
```

That packet follow-up may record the exact K0-A target and validation only. It
may not rewrite the immutable plan target or infer acceptance.

If K0-I is later granted, the maximum proposed maintained destination-side
KVM0-B implementation inventory is:

```text
100644 tests/kvm0/Makefile
100644 tests/kvm0/README.md
100644 tests/kvm0/check-bundle.mjs
100644 tests/kvm0/check-contract.mjs
100644 tests/kvm0/check-report.mjs
100644 tests/kvm0/generate-report.mjs
100644 tests/kvm0/kvm0-contract-v1.json
100644 tests/kvm0/kvm0-source-boundary-v1.json
100755 tests/kvm0/run-make.sh
100644 tests/kvm0/test-rejections.mjs
```

That list is a proposed maximum, not current authorization. A later
implementation instruction must name the exact accepted plan, base, relation,
paths, and modes. Any additional maintained path requires a reviewed plan
revision before it is edited.

KVM0-G has a separate maximum documentation and review inventory:

```text
100644 planning/k3-kvm0-evidence.md
100644 planning/k3-kvm0-review-summary.md
100644 planning/README.md
100644 planning/HANDOFF.md
100644 planning/project-orientation.md
100644 planning/roadmap.md
100644 planning/.vitepress/config.mts
100644 pathfinder/tests/check-docs-render.mjs
100644 docs/html/**
```

The two KVM0-G Markdown files are the only new authoritative planning sources.
The four maintained status/HANDOFF files may change only to report the exact
result boundary and gates. The VitePress configuration and shared renderer may
change only by the KVM0 evidence/review navigation, path, and title entries.
`docs/html/**` contains generated regular-file derivatives only. No root
README, `.github` instruction, glossary, implementation-plan, hardware-roadmap,
unrelated planning page, Helium documentation, or generated Helium path is in
this inventory.

Generated, uncommitted outputs may exist only below:

```text
build/kvm0/
```

Root `Makefile`, `be`, `scripts/check-be.sh`, `package.json`,
`package-lock.json`, dependencies, acceptance pins, and root integration are
not authorized by this plan.

## Prohibited paths and operations

KVM0 must not modify:

```text
model/
include/
virt/
arch/
tests/r0/
tests/r1/
tests/r2/
tests/r3/
tests/r4/
tests/r5/
tests/r6/
tests/r7/
tests/r8/
pathfinder/publication-gate.conf
```

It must not:

- touch the private source repository or K3 host during this planning task;
- create, append, or infer a source `COLLAB.md`;
- commit imported source, raw private workspace state, or K3 captures;
- select a development kernel/BSP;
- edit accepted H0/R0-R7 bytes or claim an H0 row is resolved;
- add Beryllium target code, Linux integration, B0, B1, H1-H4, devices, DMA,
  VFIO, libvirt, UEFI, nested virtualization, or a persistent Fedora guest;
- change persistent U-Boot environment, firmware, flash, lifecycle, debug, or
  board configuration;
- automate a reboot, power cycle, physical reset, or serial-console input;
- use network, SSH, or serial access from destination offline tooling;
- write outside `build/kvm0/` from destination offline tooling;
- add a hosted-only or proprietary normative tool;
- push, tag, publish, release, migrate, or change a publication gate; or
- add a human `Signed-off-by`.

## Immutable source-owner evidence contract

### Exact Git-target route

An exact source-owner Git target is eligible only when:

1. it resolves to one full commit and tree;
2. its worktree and index were clean when the result was captured;
3. zero untracked result inputs exist outside the committed source contract;
4. the exact KVM base, prepared candidate relation, 14-patch order, source
   files, configuration, toolchain, commands, and artifact hashes are
   retained;
5. result artifacts are bound by the external immutable transport-archive
   SHA-256 even when they are not committed to Git;
6. the source owner supplies an exact changed-path and mode inventory; and
7. the target or bundle contains a decision-neutral source-owner evidence
   statement rather than a self-acceptance.

The first proposed eligible host relation is:

```text
kvm_base=a5f72fd298f6bd02e6d30599dafb43cfa16576b6
prepared_candidate_commit=c1c7e254143f99d4ad3cdbf25021a76364d6d75a
prepared_candidate_tree=a5f77b5acef26d8975fe756512edbd2413fa1239
board_enablement_patch_count=14
host_release=7.3.0-rc4-k3-kvm-host-a1
```

The immutable source evidence must prove that exact relation. A replacement
base, candidate, tree, patch count, or release string requires explicit
review before K0-X.

### Explicitly approved bundle route

If retained artifacts cannot live in the source Git target, the responsible
human may explicitly approve one immutable bundle. The approval must name:

- external archive SHA-256 and byte size, recorded outside the archive;
- exact member list, type, mode, size, and SHA-256;
- source commit and tree;
- source-owner provenance identifier, restricted-map coverage, and creation
  date;
- reason the Git-target route is insufficient; and
- the same source, command, tool, firmware, artifact, matrix, and result
  contracts required by the Git-target route.

The importer must reject:

- absolute paths, `..`, duplicate normalized names, case-colliding names, or
  NUL bytes;
- symlinks, hard links, devices, sockets, FIFOs, setuid/setgid bits, or
  executables not present in the manifest;
- decompression outside `build/kvm0/`;
- total expanded size above 4 GiB;
- any individual raw serial capture above 128 MiB;
- any individual command log above 32 MiB;
- any manifest or report above 4 MiB; and
- missing, extra, mode-different, size-different, or hash-different members.

An approved bundle is evidence transport, not source acceptance or KVM0
acceptance.

## Required imported bundle structure

The immutable source target or approved bundle must supply exactly one
versioned instance of:

```text
bundle-manifest-v1.json
source-manifest-v1.json
patch-manifest-v1.json
tool-manifest-v1.json
firmware-manifest-v1.json
artifact-manifest-v1.json
command-manifest-v1.json
board-manifest-v1.json
capture-manifest-v1.json
selftest-manifest-v1.json
provenance-manifest-v1.json
matrix-manifest-v1.json
result-manifest-v1.json
recovery-manifest-v1.json
checksums.sha256
```

Retained artifacts live under manifest-enumerated `artifacts/`, `captures/`,
`logs/`, and `results/` prefixes only. No file outside the complete manifest
may influence a result.

### Cycle-free digest order

All bundle and report hashing is directed and non-self-referential:

1. Finalize every retained member except `checksums.sha256` and the transport
   archive. The fixed report path is
   `results/kvm0-qualification-report-v1.json`.
2. The report records only
   `report_digest_manifest=checksums.sha256` and
   `report_digest_entry=results/kvm0-qualification-report-v1.json`. It does
   not contain its own digest, the digest of `checksums.sha256`, or the final
   archive digest.
3. Generate `checksums.sha256` last. It contains lower-case SHA-256, two ASCII
   spaces, and the normalized relative path for every regular retained member
   except `checksums.sha256` itself, sorted by raw UTF-8 path bytes with LF
   endings. It therefore includes the report and every JSON manifest.
4. Assemble the deterministic transport archive only after
   `checksums.sha256` is final. Compute the archive SHA-256 over the completed
   archive and record it only in the external approval/import record.

`bundle-manifest-v1.json` may identify `checksums.sha256` as the fixed checksum
control file by path, but no retained bundle member may embed the checksum
file's digest or the final archive digest. The external approval/import record
may record the checksum-file digest and archive digest because it is not a
member of the object it hashes. Any cycle, omitted member, duplicate path, or
digest disagreement is a hard failure.

## Source, patch, and artifact provenance

The source and artifact manifests must retain:

- source repository identity without a private URL;
- exact source commit, tree, parents, branch label, and clean-state proof;
- exact KVM base and candidate relation;
- all 14 board-enablement patches in order, with subject, opaque author
  provenance identifier, commit, patch ID, touched-path inventory, and
  SHA-256;
- complete kernel configuration bytes and SHA-256;
- compiler, assembler, linker, build utilities, command argv, environment,
  working directory, and output identities;
- QEMU 10.2.2 source commit/tag, tree, configure arguments, build commands,
  dependency closure, binary SHA-256, and feature query output;
- minimal guest kernel, configuration, initramfs, root/block seed, launcher,
  and marker-source identities;
- exact board DTB source and artifact identity;
- U-Boot, OpenSBI or other M-mode runtime, firmware, and first mutable stage
  source/configuration/binary identities;
- host root filesystem or image provenance and package closure;
- every final artifact byte size, mode, and SHA-256; and
- exact replacement rules for any source, tool, firmware, or artifact drift.

The discovery artifact expectations are:

```text
Image_sha256=f72cbc683b2919c17ecfa8f8379b74ee0b9f65b9bcb25319f7cd499ce5048853
config_sha256=a063191962b26c2782081b1267abb53bfc79660318d9b2468afa0b2a307faa4d
dtb_sha256=dc338c5c92966f84ab6494cc4a3a1fdef70a0296e8d4ec8a26f9f212aaf18575
```

A mismatch is not automatically a defect in the new artifact, but it is a
profile change. KVM0 execution must stop until the responsible human reviews
the changed identity and either revises the plan or explicitly approves a new
exact profile.

Missing exact firmware, U-Boot, or OpenSBI provenance is a hard stop. A banner,
installed filename, package name, or generic board documentation is not
sufficient provenance.

### Provenance identity and privacy

The ordinary importable bundle, deterministic report, planning evidence, and
any future publication-safe export must not copy human-readable source-owner,
patch-author, committer, or signature identities. They use stable
profile-local identifiers of the form:

```text
kvm0-prov-v1-<32-lower-hex>
```

Each identifier is the first 128 bits of HMAC-SHA-256 over the canonical
UTF-8 identity record, keyed by one 256-bit profile-local provenance key. The
key and canonical identity records exist only in the restricted
`restricted/provenance-map-v1.json` artifact. The ordinary
`provenance-manifest-v1.json` records every identifier, role, source object,
patch or signature reference, restricted-map SHA-256 and byte size, mapping
coverage status, and redaction/export disposition. It never records the key,
name, email address, or other human-readable identity.

The restricted provenance map:

- is retained in an access-controlled source-owner evidence location, separate
  from the ordinary bundle and outside every publication or clean-repository
  export;
- maps every opaque identifier to the exact human-readable identity, role,
  source basis, and relevant upstream object or signature;
- is hash-bound by the ordinary provenance manifest and reviewed under K0-S;
- is retained unchanged through K0-R and until the responsible human records a
  later retention or destruction decision; automation must not delete it;
- may contain personal data only to the minimum needed for provenance review;
  unrelated personal data is prohibited; and
- must be available to the responsible human for audit even though destination
  offline tooling consumes only the ordinary bundle.

The opaque identifiers are captured manifest inputs, not values generated from
the current clock or report-generation environment.

An immutable upstream commit or signature may be referenced by repository
identity, exact commit ID, signature object, and verification result without
copying its human-readable author or signer fields into ordinary manifests or
reports. No provenance fact is silently discarded: a missing identifier,
missing restricted mapping, mapping hash/size mismatch, uncovered source-owner
or patch-author role, or publication export containing a prohibited identity
blocks K0-S/K0-X.

## Tool and environment locks

Every normative executable must have:

- an absolute command path;
- resolved regular-file path;
- version output;
- byte size and SHA-256;
- source or owning open package;
- license;
- configuration and required environment; and
- an independent cross-check where the result is security- or
  evidence-critical.

The normative source/build/execution closure must include, when used:

- GCC and GNU binutils/linker;
- Clang/LLVM/lld;
- GNU Make and shell;
- Git;
- QEMU 10.2.2;
- KVM selftest build tools;
- guest/initramfs construction tools;
- hashing and archive tools;
- journal and FDT capture tools;
- the passive serial capture tool; and
- destination Node.js and Git for offline checking.

No normative command may download a dependency or use a mutable package
repository during build, execution, or import.

Destination offline checking must run with:

```text
network=disabled
ssh=forbidden
serial=forbidden
stdin=/dev/null
HOME=build/kvm0/home
TMPDIR=build/kvm0/tmp
XDG_CACHE_HOME=build/kvm0/cache
all_writes=build/kvm0/**
```

Offline tooling may consume only the supplied immutable bundle and the exact
Beryllium checker source. It may not inspect the private source checkout, K3
host, board, serial device, network, or another workspace.

## Command-manifest contract

The plan deliberately does not invent private source-side shell commands.
Before K0-X, the immutable source evidence must provide every exact command as
a structured argv array. The command manifest is part of the human-reviewed
execution profile.

Each command entry must contain:

```text
id
phase
absolute_executable
argv[]
cwd_relative_to_immutable_root
environment_allowlist{}
stdin_policy
stdout_artifact
stderr_artifact
timeout_seconds
expected_exit_codes[]
required_markers[]
forbidden_markers[]
produced_artifacts[]
```

Rules:

- No command is represented as an evaluable shell string.
- No `eval`, command substitution, wildcard expansion, caller alias, caller
  function, ambient `PATH` lookup, or unbounded environment inheritance is
  allowed.
- No source-side command may use the network during a normative run.
- No destination command may use network, SSH, or serial at all.
- Every exact command, timeout, expected exit, and marker is reviewed before
  execution authorization.
- A missing command entry is `NOT RUN`, never an invitation to improvise.

## Board, boot, and serial safety

KVM0 uses the proposed native U-Boot/NVMe path only. UEFI is not selected.
Kexec may not satisfy or corroborate KVM0.

Automation must never:

- reboot or power-cycle the K3;
- issue a physical reset;
- change persistent U-Boot environment;
- send any serial-console byte, including a newline or break;
- flash firmware or alter boot media;
- change lifecycle, debug, trace, or security state; or
- attempt recovery through an undocumented side channel.

Each of the three native boot sessions requires an attended, human-only boot
action separately covered by K0-X. Any physical reset or recovery action is
also attended, human-only, and explicitly authorized. The action, reason,
start/end times, and resulting boot-session disposition are retained.

The serial path is output-only. The capture mechanism must prove that it
cannot write to the serial endpoint. If the selected tool or adapter opens a
writable path or cannot demonstrate output-only behavior, KVM0 stops.

In-band host reboot is not part of the procedure. The reported discovery that
in-band reboot failed remains a non-evidentiary warning and cannot be turned
into a retry mechanism.

## Capture semantics

For each boot session:

1. create a new empty capture destination below the source-owner evidence
   root;
2. start passive serial capture before the attended boot action;
3. record capture-tool identity, arguments, monotonic and wall-clock start
   times, byte limit, and timeout;
4. never append to or reuse a prior capture;
5. retain every byte until the session ends or reaches the hard limit;
6. record exact byte count and SHA-256;
7. derive a canonical UTF-8/LF view without discarding undecodable raw bytes;
8. retain bounded excerpts around boot, KVM, selftest, matrix, failure, and
   shutdown markers; and
9. end capture only after the session result and any attended recovery action
   are recorded.

Serial timing is evidence metadata, not a performance result.

The capture must start before firmware output. If early output is missing,
stale, appended, truncated, over the byte limit, or not attributable to the
current attended boot, the entire session is invalid.

## Privacy and redaction

The evidence bundle and committed reports must not contain:

- credentials, keys, tokens, secrets, or device private material;
- private repository URLs or remotes;
- personal names beyond existing project attribution;
- host usernames, home directories, or sensitive absolute paths;
- board serial numbers, adapter serial numbers, MAC addresses, filesystem
  UUIDs, hostnames, routable IP addresses, or unrelated journal data; or
- raw environment variables outside the exact allowlist.

Use stable project-local identifiers such as `k3-com260-1`,
`capture-host-1`, and `boot-session-1`.

The separately retained `restricted/provenance-map-v1.json` is the sole
human-identity exception to the ordinary-bundle rule. It may contain the
minimum human-readable mapping and the profile-local provenance key required
by the provenance contract above, but it is not part of the ordinary bundle,
committed report, planning HTML, or publication-safe export.

`/proc/cmdline` and other required artifacts must be reviewed before
retention. If a required artifact contains a prohibited value:

1. retain the raw byte count and SHA-256 in the restricted local bundle;
2. retain a deterministic field-level redacted representation;
3. retain the exact redaction rule and affected field names; and
4. stop if redaction would remove a security-relevant fact.

No prohibited raw value may be committed to Git.

## Fixed native boot and repeatability profile

KVM0 requires exactly three attended native boot sessions:

```text
boot-session-1
boot-session-2
boot-session-3
```

Each session must:

- use the same exact board, boot medium, one-shot U-Boot/NVMe selection,
  firmware/U-Boot/OpenSBI bytes, host Image, config, DTB, initramfs/rootfs,
  QEMU binary, guest artifacts, command manifest, and capture profile;
- leave persistent U-Boot environment and known-good fallback unchanged;
- reach the exact host-ready marker within 600 seconds of the attended boot
  action;
- collect the pre-run host/KVM facts below;
- run the complete selftest set once;
- run compatibility cases C01-C08 in order;
- run native cases N01-N08 in order;
- collect post-run host/KVM facts; and
- end with an explicit session PASS, FAIL, or NOT-RUN disposition.

There is no automatic retry. A failed case terminates the current session and
marks all remaining cases in that session `NOT-RUN`.

## Required host and KVM facts

Each boot session must retain:

- exact `uname -a` and kernel release;
- exact `/proc/cmdline` under the privacy rule above;
- exact `/proc/version`, `/etc/os-release`, and boot ID pseudonym;
- exact live FDT bytes or an explicitly documented unavailable result, plus
  byte count and SHA-256;
- exact static DTB artifact hash;
- `/dev/kvm` type, owner class, mode, and availability;
- KVM API version and exact extension-query results used by the harness;
- loaded KVM module identities, parameters, and source target;
- CPU count and online/possible/present masks;
- relevant `lscpu` or equivalent RISC-V ISA/virtualization facts;
- exact QEMU version and accelerator query;
- bounded KVM-related kernel journal facts from the current boot only;
- kernel warning, oops, BUG, panic, lockup, RCU stall, and machine-check scan;
- memory-pressure and OOM facts relevant to the runs;
- pre/post hashes of every immutable artifact; and
- any recovery or operator action.

The journal capture must use an exact command, current boot identifier,
bounded time range, bounded byte limit, and KVM-focused filter. A full
unbounded system journal is prohibited.

## Fixed KVM selftest set

The immutable source evidence must define exactly 16 RISC-V KVM selftest
commands from the exact source target. The plan preserves the discovery
expectation:

```text
expected_PASS=15
expected_SKIP=1
expected_FAIL=0
expected_ERROR=0
```

The single allowed SKIP must have:

- one exact test identifier;
- exact argv and timeout;
- exit code `4`;
- one exact stable skip marker and reason;
- an explanation of why the skipped behavior is outside KVM0; and
- the same outcome in all three boot sessions.

Every PASS must exit `0`. Each selftest command has a maximum timeout of 120
seconds, and the complete set has a maximum wall-clock budget of 1,800
seconds per boot session. Any additional skip, timeout, nonzero non-skip
exit, missing marker, source mismatch, or cross-session difference fails the
session.

The exact 16 test names and commands are currently unavailable. This is an
explicit K0-S/K0-X blocker, not permission to select tests at run time.

## Fixed guest test matrices

Every case requires:

- QEMU 10.2.2 from the immutable tool manifest;
- hardware KVM acceleration with fail-on-unavailable behavior;
- the exact same minimal RV64 guest kernel and initramfs;
- guest H absent and nested virtualization untested;
- no graphical device;
- no host file sharing;
- no bridge, tap, vhost-user, host forwarding, guest forwarding, TFTP, SMB,
  or external network access;
- one exact console;
- one exact command-manifest entry;
- a guest PASS marker by 240 seconds;
- QEMU exit `0` by 300 seconds; and
- no host kernel or KVM error marker.

The exact case order is fixed.

### Compatibility CPU-profile matrix

The compatibility profile is one exact conservative QEMU/KVM CPU property
set supplied by the immutable command manifest. It is not inferred from a
mutable default.

| Case | vCPUs | Interrupt model | Block | Network | Required additional result |
| --- | ---: | --- | --- | --- | --- |
| C01 | 1 | PLIC | none | none | Basic boot, KVM API use, deterministic marker, clean poweroff |
| C02 | 2 | PLIC | none | none | Both vCPUs online and bounded SMP marker |
| C03 | 8 | PLIC | none | none | All eight vCPUs online and bounded SMP marker |
| C04 | 1 | AIA/APLIC/IMSIC | none | none | Exact AIA topology marker and clean boot |
| C05 | 2 | AIA/APLIC/IMSIC | none | none | Both vCPUs online under AIA |
| C06 | 8 | AIA/APLIC/IMSIC | none | none | All eight vCPUs online under AIA |
| C07 | 2 | PLIC | deterministic virtio block | restricted user networking | Block read/write-overlay check, internal DHCP/link marker, external-access denial |
| C08 | 8 | AIA/APLIC/IMSIC | deterministic virtio block | restricted user networking | Eight-vCPU AIA plus block and restricted-network checks |

### Native host CPU-profile matrix

The native profile is one exact host-derived QEMU/KVM CPU property set
supplied by the immutable command manifest. Every exposed property is retained
and compared across sessions.

| Case | vCPUs | Interrupt model | Block | Network | Required additional result |
| --- | ---: | --- | --- | --- | --- |
| N01 | 1 | PLIC | none | none | Basic boot, KVM API use, deterministic marker, clean poweroff |
| N02 | 2 | PLIC | none | none | Both vCPUs online and bounded SMP marker |
| N03 | 8 | PLIC | none | none | All eight vCPUs online and bounded SMP marker |
| N04 | 1 | AIA/APLIC/IMSIC | none | none | Exact AIA topology marker and clean boot |
| N05 | 2 | AIA/APLIC/IMSIC | none | none | Both vCPUs online under AIA |
| N06 | 8 | AIA/APLIC/IMSIC | none | none | All eight vCPUs online under AIA |
| N07 | 2 | PLIC | deterministic virtio block | restricted user networking | Block read/write-overlay check, internal DHCP/link marker, external-access denial |
| N08 | 8 | AIA/APLIC/IMSIC | deterministic virtio block | restricted user networking | Eight-vCPU AIA plus block and restricted-network checks |

The complete qualification therefore contains:

```text
boot_sessions=3
selftest_suite_runs=3
guest_cases_per_session=16
total_guest_cases=48
compatibility_case_repetitions=3
native_case_repetitions=3
```

This bounded repetition is not an endurance, performance, thermal, or
reliability test.

## Block-device and network semantics

For C07, C08, N07, and N08:

- the immutable block seed is read-only and hash-checked before every case;
- each case receives a fresh bounded writable overlay below the source-owner
  result directory;
- the guest reads one fixed seed value, writes one fixed overlay value,
  rereads it, and emits both in the PASS marker;
- the seed hash must remain unchanged;
- the overlay pre/post byte size and SHA-256 are retained; and
- an overlay is never reused across cases.

Restricted user networking must use QEMU user-mode networking with the
equivalent of `restrict=on`, no host or guest forwarding, and no external
route. The exact argv is supplied by the command manifest. The guest must:

- enumerate the expected virtual NIC;
- obtain only the internal test configuration;
- emit one internal link/configuration marker;
- prove the fixed external-access attempt is denied; and
- emit no claim of general networking, throughput, or Internet access.

Any unexpected external connectivity is a FAIL and a stop.

## Exact markers and exits

The immutable guest and launcher sources must emit ASCII markers matching this
grammar:

```text
KVM0:HOST:READY session=<1|2|3> kernel=7.3.0-rc4-k3-kvm-host-a1
KVM0:SELFTEST:PASS session=<1|2|3> pass=15 skip=1 fail=0
KVM0:GUEST:PASS session=<1|2|3> case=<C01..C08|N01..N08> cpu=<compat|native> irq=<plic|aia> vcpus=<1|2|8> block=<none|overlay> net=<none|restricted>
KVM0:CASE:PASS session=<1|2|3> case=<C01..C08|N01..N08> qemu_exit=0
KVM0:SESSION:PASS session=<1|2|3> cases=16
```

The command manifest may add exact value fields but may not remove or
reinterpret these fields. Required markers must occur exactly once and in
order. Duplicate, missing, malformed, stale-session, or reordered markers are
FAIL.

Forbidden markers include kernel panic/oops/BUG, KVM initialization failure,
TCG fallback, QEMU fatal error, guest panic, timeout, unexpected reboot,
unexpected host shutdown, nested-virtualization enablement, or external
network success.

## Negative-path handling

The harness and offline checker must treat each of the following as FAIL:

- KVM unavailable or QEMU falls back to TCG;
- host release, source, firmware, artifact, command, or tool identity drift;
- missing or changed `/proc/cmdline` or live FDT disposition;
- missing exact KVM selftest list;
- any selftest result other than 15 PASS and the one approved SKIP;
- guest H present or a nested-virtualization test attempted;
- a matrix case exits nonzero, times out, loses output, or misses a marker;
- unexpected network connectivity;
- block seed mutation or overlay reuse;
- host kernel warning/oops/BUG/panic/lockup/RCU stall/OOM attributable to the
  qualification;
- serial capture that is writable, late, stale, truncated, appended, or over
  its limit;
- an automation attempt to reboot, power-cycle, reset, flash, or send serial
  input;
- persistent boot-state drift;
- an unrecorded human action or recovery;
- evidence outside the manifest or write outside the bounded output root;
- privacy/redaction failure;
- report nondeterminism; or
- an attempt to represent KVM0 as Beryllium or R8 hardware evidence.

There is no broad catch, automatic retry, test removal, expectation
relaxation, fallback command, cached transcript substitution, or
success-shaped skip.

## Recovery contract

The known-good native boot path must remain selectable without persistent
environment change.

On a host, QEMU, capture, or board failure:

1. stop the current case and session;
2. retain all available output, process exit state, timestamps, hashes, and
   failure markers;
3. terminate only exact known process IDs under the source-owner procedure;
4. perform no automated reboot, reset, power cycle, or serial input;
5. if board safety requires recovery, use only one attended human action
   explicitly allowed by K0-X;
6. record the action as a recovery event;
7. restore the known-good boot for safety, not to resume or convert the failed
   session into PASS; and
8. mark all remaining cases in the failed session `NOT-RUN`.

Resuming qualification after a failed session requires a new explicitly
reviewed execution attempt or a plan/result revision. Recovery is not a retry.

## Retained artifacts

The local immutable result bundle must retain, at minimum:

- source commit, tree, parents, base relation, and clean-state evidence;
- 14-patch ordered manifest and exact patch identities;
- firmware, U-Boot, OpenSBI/M-mode, host rootfs, kernel, config, DTB,
  initramfs, QEMU, guest, block seed, launcher, and checker identities;
- exact Image, config, DTB, initramfs, QEMU, guest, block seed, and report
  hashes;
- complete command manifest and exact environment allowlists;
- `/proc/cmdline` under the privacy contract;
- exact live FDT byte count and SHA-256, with bytes retained when policy
  permits;
- KVM API, extension-query, module, parameter, `/dev/kvm`, CPU, and QEMU
  facts;
- bounded current-boot KVM journal facts;
- one complete raw serial capture per boot session;
- canonical serial records and bounded excerpts;
- selftest stdout/stderr, TAP or equivalent result, exit, duration, and skip
  reason;
- all 48 matrix stdout/stderr/console records, exits, durations, markers, and
  case parameters;
- block seed and overlay pre/post hashes;
- restricted-network configuration and denial results;
- every failure, timeout, human action, and recovery event;
- pre/post host warning scans;
- report regeneration logs;
- evidence member list, modes, sizes, and SHA-256 values for every member
  hashed by `checksums.sha256`, plus the externally recorded checksum-file and
  archive identities and total size; and
- claim, assumption, trusted-boundary, non-claim, and unavailable-evidence
  ledgers.

The complete expanded bundle must remain at or below 4 GiB. Exceeding the cap
is a stop requiring a reviewed retention revision, not permission to discard
failed evidence selectively.

## Deterministic reporting

The fixed report schema is:

```text
be-k3-kvm0-qualification-v1
```

For a fixed checked input bundle, report generation must be byte-identical
across two clean offline runs. The report uses:

- UTF-8;
- LF line endings;
- sorted object keys and arrays where order is not semantic;
- decimal integers without locale formatting;
- exact lower-case hexadecimal SHA-256;
- explicit `PASS`, `FAIL`, `SKIP`, `NOT-RUN`, `UNKNOWN`, and
  `NOT-APPLICABLE` tokens;
- timestamps only when they are captured input facts; and
- no current clock, random identifier, absolute private path, ambient
  hostname, username, or mutable environment value.

The report must include:

| Field group | Required content |
| --- | --- |
| Identity | schema, exact source target/bundle, board profile ID, three boot-session IDs, `checksums.sha256` path, and exact report entry path |
| Source | base, candidate commit/tree, patch count/order/hashes, clean-state proof |
| Firmware | ROM availability, first mutable stage, U-Boot, OpenSBI/M-mode, firmware config and hashes |
| Host artifacts | kernel release, Image/config/DTB/initramfs/rootfs identities and hashes |
| QEMU/guest | QEMU source/binary/config, guest kernel/config/initramfs, guest H absence, block seed, launcher |
| Host facts | `/proc/cmdline`, live FDT hash, CPU/KVM API/extensions, `/dev/kvm`, modules/parameters |
| Capture | serial tool, output-only proof, settings, start/end, byte count, SHA-256, excerpts |
| Selftests | exact 16 commands, 15 PASS, one approved SKIP, exits, timeouts, outputs |
| Matrices | all 48 case inputs, markers, exits, duration, block/network results, cross-session comparison |
| Journal | bounded KVM-related facts and warning/error scan |
| Failures | failed/not-run cases, timeouts, unexpected output, reason and disposition |
| Recovery | every attended human action and proof it did not convert failure to PASS |
| Claims | exact supportable claim and evidence boundary |
| Non-claims | Beryllium/R8, BSP, nested, endurance, performance, thermal, VFIO, DMA, libvirt, UEFI, persistent guest, production, proof, publication |

## Supportable future result claim

Only after K0-R accepts one exact result may the project say:

> On one exact K3 CoM260 board and exact retained firmware, U-Boot/OpenSBI,
> Linux host, QEMU 10.2.2, minimal guest, and tool profile, three attended
> native boot sessions each completed the exact 16-test KVM selftest set with
> 15 PASS and one approved SKIP, then completed all compatibility and native
> CPU-profile guest cases C01-C08 and N01-N08 using KVM acceleration, the
> fixed PLIC and AIA/APLIC/IMSIC configurations, 1/2/8 vCPUs, deterministic
> block checks, restricted user networking where selected, exact pass
> markers, and expected zero exits.

Required limit:

> This is a bounded Linux/KVM qualification result for one exact board and
> profile. It is not Beryllium execution or hardware validation, not retained
> R8 evidence, not H0 row resolution, not H1-H4 authorization, not a
> development-kernel/BSP selection, and not evidence for nested
> virtualization, endurance, performance, thermal behavior, VFIO, DMA,
> libvirt, UEFI, a persistent Fedora guest, general K3 support, KVM
> correctness, production readiness, formal verification, publication, or
> release.

Until K0-R, the result is `NOT-RUN` and no such claim is supportable.

## Explicit non-claims

KVM0 does not claim or authorize:

- any Beryllium code executing on K3;
- any Beryllium isolation, G-stage, trap, context, switch, proof, or hardware
  property;
- R8 H0 exit readiness or resolution of any accepted H0 row;
- R8 H1-H4;
- B0, B1, Linux as a Beryllium management domain, guest SBI, or services;
- selection of the installed kernel, candidate kernel, or another tree as the
  Beryllium development kernel/BSP;
- nested virtualization or guest H;
- endurance, stress, availability, latency, throughput, power, thermal, or
  side-channel behavior;
- VFIO, IOMMU, IOPMP, DMA, device assignment, libvirt, UEFI, kexec evidence,
  or a persistent Fedora guest;
- secure boot, measured boot, firmware integrity, attestation, debug
  lockdown, rollback protection, or lifecycle assurance;
- general K3, all CoM260 units, all firmware, all steppings, or production
  Linux/KVM support;
- KVM, Linux, QEMU, firmware, hardware, or guest correctness;
- formal verification, certification, or assurance release;
- source publication, push, tag, migration, release, or upstream submission.

## Stop rules

Stop before implementation or execution if:

- the exact plan is not accepted;
- K0-I, K0-S, or K0-X is missing;
- the source target is dirty, mutable, unavailable, or not tied to an
  approved immutable bundle;
- the source commit/tree/base/14-patch relation differs;
- an artifact hash differs from the approved profile;
- firmware, U-Boot, or OpenSBI/M-mode provenance is missing;
- an exact command, timeout, expected exit, marker, selftest name, or skip
  reason is missing;
- an offline tool requires network, SSH, serial, or a write outside
  `build/kvm0/`;
- automation would reboot, power-cycle, reset, flash, or write serial;
- the native boot path would alter persistent state or lacks a known-good
  fallback;
- the serial path is not provably output-only;
- the board, host release, `/proc/cmdline`, live FDT, KVM API, or QEMU profile
  differs;
- KVM acceleration is unavailable or TCG fallback is possible;
- guest H is present or nested virtualization enters the matrix;
- a selftest, guest case, negative check, privacy check, report regeneration,
  or evidence mutation test fails;
- a recovery action is unapproved or used as a retry;
- the bundle exceeds a bound or omits failed evidence;
- any accepted H0/R0-R7 byte or prohibited path must change;
- a development kernel/BSP selection is attempted;
- a source ledger write is proposed despite the absent source `COLLAB.md`; or
- a KVM0 fact is presented as Beryllium or R8 hardware evidence.

The correct output is `FAIL`, `NOT-RUN`, `UNKNOWN`, a revision request, or a
blocked result. Requirements are never relaxed at run time.

## Plan exit criteria

This planning package is ready for responsible-human review only when:

1. the exact plan target is committed and clean;
2. changed paths are limited to the planning/navigation/generated boundary;
3. the current dirty private source and missing KVM result remain
   discovery-only;
4. accepted H0/R0-R7 bytes remain unchanged;
5. K0-P, K0-I, K0-S, K0-X, and K0-R remain separately visible and blocked
   until their exact conditions are satisfied;
6. the source-target/bundle contract, privacy rules, output-only serial rule,
   human-only reset/recovery rule, offline no-network rule, matrix, timeouts,
   markers, expected exits, retention, report, and stop rules are explicit;
7. report, checksum-manifest, and archive hashing are cycle-free and have one
   exact generation order;
8. the KVM0-B implementation inventory and KVM0-G documentation/review
   inventory are separately finite;
9. discovery-only live facts and missing hashes remain explicitly
   non-evidentiary and do not change Beryllium or R8 status;
10. ordinary provenance stays pseudonymous while the restricted map remains
    complete, hash-bound, retained, reviewable, and publication-excluded;
11. K3 and Beryllium hardware remain `NOT RUN`;
12. H0 rows and development-kernel/BSP status remain unchanged;
13. documentation builds and browser/link/direct-file gates pass; and
14. a separate exact-commit review packet requests only accept, revise, or
    defer for the plan target.

Passing these criteria does not accept the plan or authorize implementation.

## After a plan decision

- **Accept:** record acceptance of the exact plan SHA only. Keep
  implementation and execution `not-authorized` until separate explicit
  decisions.
- **Request revisions:** create a new exact plan commit and a new review
  packet. The superseded target is not silently accepted.
- **Defer:** preserve `proposed-not-reviewed`, `NOT-RUN`, and every current
  block. Do not start implementation or execution.

## Primary project references

- [Project orientation](project-orientation.md)
- [Beryllium roadmap](roadmap.md)
- [R8 K3 core-validation plan](single-hart-runtime-r8-plan.md)
- [R8-H0/R8-C review and acceptance record](single-hart-runtime-r8-h0-review-summary.md)
- [RISC-V and K3 security hardware roadmap](riscv-security-hardware.md)
- [Provisional implementation and upstream plan](implementation-plan.md)
- [Open tooling and high-assurance evidence policy](open-tooling.md)
- Repository-root `LLM_POLICY_ALIGNMENT.md`
