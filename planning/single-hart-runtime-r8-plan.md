<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R8 K3 core-validation plan

## Status and authority

The responsible-human instruction `r7 reviewed, proceed to r8` on 2026-08-07
selected an R8 successor-planning phase after acceptance of exact R7
implementation target `9bf22913d67e9b72286813cd5f7993a9ad3857a8`. Follow-up
responsible-human direction selected the **combined K3 core-validation plan**
rather than Linux/OS support or an evidence-reproducibility-only package.

The original bounded plan is responsible-human accepted at exact Git commit
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` on 2026-08-07. Its accepted
bytes remain identified exactly as
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5:planning/single-hart-runtime-r8-plan.md`;
this later revision does not rewrite or move that historical acceptance
boundary. The
[R8 plan review and acceptance record](single-hart-runtime-r8-plan-review-summary.md)
carries that decision. A later separate responsible-human instruction,
`Authorize R8 implementation under accepted plan 7d0f0cbf…; proceed with
R8-H0`, authorizes only the non-privileged H0 freeze under that exact plan.

Local H0 work then exposed a defect in the accepted location and
candidate-identity rules. Plan revision R8-A repaired that defect and is
responsible-human accepted at exact target
`8fa9d672cfcfb81ab68d9ed9553a5af48b884932` (parent
`cb0ac2a0f818ac57f2866cb7815767145608cf58`) as of 2026-08-07. The
[R8-A review and acceptance record](single-hart-runtime-r8-plan-r8a-review-summary.md)
carries that decision. Its acceptance-record commit
`1f6109f0d0371eb3707e296c3416e8c55235683e` is the accepted H0
implementation base.

PMR-080 later produced exact H0 candidate
`6e93461f6ea097cb095e31558f6956dc6c0c2708` (parent
`1f6109f0d0371eb3707e296c3416e8c55235683e`, tree
`b9fe2f7bdc6077651db550ed070930f45e21f58d`). Its standalone H0 and
documentation gates pass, but the complete repository gate exposes a false
retired-parent namespace match in a non-text static ELF. The candidate remains
blocked, not reviewed, and unaccepted. It must remain byte unchanged.

Repository-wide Git history already assigns the R8-B label to exact plan
object `c6e0da62f99a5bf0cb3435f7495129962a3be21b` on a separate branch that is
not an ancestor of this planning line. This revision does not import that
branch, its plan semantics, or any authority from it. The next unused revision
label is therefore **R8-C**.

Resolved PMR-081 tasking is identified by source commit
`35f0f20037f85109bebd1cd24d6d0d3b141989a1` and request-table blob
`6276caeb69869a2a47508498e9b2fc86db387013`. It authorizes preparation of a
planning-only narrow revision; it does not authorize the checker change or a
successor H0 candidate.

The current planning state is:

```text
r8_direction=combined-k3-core-validation
r8_planning_authorization=authorized
r8_plan=accepted-exact-target
r8_accepted_plan_commit=7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5
r8_plan_revision_r8a=accepted-exact-target
r8_plan_revision_r8a_target=8fa9d672cfcfb81ab68d9ed9553a5af48b884932
r8_r8a_acceptance_record_base=1f6109f0d0371eb3707e296c3416e8c55235683e
r8_plan_revision_r8c=proposed-not-reviewed
r8_r8c_implementation_authorization=none
r8_implementation=authorized-h0-only-under-accepted-r8-r8a
r8_h0_implementation_authorization=authorized-existing
r8_h0_candidate=6e93461f6ea097cb095e31558f6956dc6c0c2708-blocked-unaccepted
r8_h0_successor=not-authorized
r8_hardware_execution=NOT-RUN
```

The accepted original plan, accepted R8-A, and existing H0 implementation
authorization do not cover
[Plan revision R8-C](#plan-revision-r8-c-content-based-retired-parent-scan)
or any change to `pathfinder/tests/check-source-policy.sh`. A responsible human
must first accept one exact clean R8-C plan target and then separately
authorize implementation from an approved exact base and relation. Any
successor H0 candidate must freshly derive every path, mode, blob, tree,
semantic projection, count, and report identity. Exact H0 acceptance remains
required before privileged R8-H1 or later work.

The accepted R0-R7 targets remain immutable evidence boundaries. The R7 review
and acceptance record, not the retained pre-decision R7 status fields, carries
the 2026-08-05 R7 decision. This plan does not rewrite that evidence.

Public push, tag, publication, release, and any clean-repository migration
remain blocked. `pathfinder/publication-gate.conf` is outside this plan.

## Plan revision R8-A: H0 documentation boundary and candidate identity

**Status: proposed, not reviewed.** R8-A is a narrow repair to the accepted
H0 package-location and exact-candidate rules. It changes no board, firmware,
memory, feature, tool, hardware, claim, H1-H4, runtime, proof, or predecessor
mechanism requirement.

Until a responsible human accepts an exact commit containing this revision:

- the existing non-privileged H0 implementation authorization remains
  recorded but paused;
- no paused implementation path, source, mode, hash, count, or base identity
  becomes plan evidence;
- no H0 candidate may be committed or presented for review; and
- K3 execution remains `NOT RUN`.

Acceptance of R8-A would authorize only the support-path boundary and
candidate-identity semantics below so that the already authorized H0 work may
resume. It would not accept H0, authorize H1 or K3 execution, permit root
integration or an acceptance-pin refresh, authorize publication, or start a
successor.

### Defect in the accepted plan

The accepted
[package-location table](#ordered-r8-package-graph) names only
`planning/single-hart-runtime-r8-h0-freeze.md` and host-only checks under
`tests/r8/` for H0, and requires a plan revision before adding a path outside
the accepted inventory. A reviewable H0 freeze is also a planning Markdown
page automatically consumed by the VitePress site. Its exact planning-page
inventory, navigation label, direct-file renderer check, and maintained
current-position statements necessarily touch additional documentation and
integration paths.

Without an enumerated support boundary, either the documentation gate rejects
or omits the H0 page and current position, or the H0 source-boundary checker
rejects the documentation changes needed to make that gate pass. The accepted
plan therefore requires documentation integration while withholding the path
authority needed to perform it.

The accepted plan also does not define one H0 candidate identity that works
both before and after the candidate is committed. Pinning the development
base or a transient index count observed during local work would make the
checker self-inconsistent at the exact committed candidate. The remedy is a
future accepted base plus explicit development and committed-candidate modes,
not a copied diagnostic value.

### Status of the paused discovery

The paused local work established only the two plan defects above. It is
unaccepted implementation discovery, not H0 output, retained evidence, or a
measurement of the future candidate. This revision deliberately records no
current H0 result, file inventory below `tests/r8/`, path count, source hash,
tree hash, report digest, or implementation-base value.

After exact R8-A acceptance, implementation must restart from the accepted
base and independently re-derive every maintained source, path, mode, hash,
tree, count, and report input. No value or conclusion from the paused
diagnostic may be copied merely because it appears plausible.

### Exact H0 support-path boundary

The accepted H0 authority families remain:

- `planning/single-hart-runtime-r8-h0-freeze.md`, as the authoritative H0
  freeze Markdown; and
- host-only profile, parser, tool, fixture, report, and checker sources under
  `tests/r8/`, with the exact candidate inventory and modes derived by H0.

R8-A adds exactly the following support paths. All listed source files are
currently Git regular files with mode `100644`, and that mode must remain
unchanged in an H0 candidate.

| Path | Classification | Required Git mode |
| --- | --- | --- |
| `.github/copilot-instructions.md` | maintained current-position and automation instruction support | `100644` |
| `README.md` | repository onboarding and current-position support | `100644` |
| `planning/README.md` | planning index and current-position support | `100644` |
| `planning/HANDOFF.md` | handoff and restart-boundary support | `100644` |
| `planning/implementation-plan.md` | maintained implementation-stage and gate support | `100644` |
| `planning/roadmap.md` | maintained one-page current-position support | `100644` |
| `planning/riscv-security-hardware.md` | K3 inventory, deferral, and hardware-boundary support | `100644` |
| `planning/.vitepress/config.mts` | planning navigation and page-label integration only | `100644` |
| `pathfinder/tests/check-docs-render.mjs` | shared direct-file planning-page inventory only; no Helium behavior or claim change | `100644` |
| `docs/html/**` | generated VitePress derivatives only | tracked generated files must remain regular `100644` files |

This is the complete H0 support set. No other root or support path is
authorized. In particular:

- root `package.json` and `package-lock.json` remain excluded;
- a third-party H0 parser or tool source must be vendored under `tests/r8/`
  with its license and provenance, not added through a root dependency;
- root `Makefile`, `be`, and `scripts/check-be.sh` remain excluded;
- no predecessor acceptance pin or acceptance checker may be refreshed;
- no runtime source, proof source, or accepted R0-R7 mechanism or evidence
  input may change; and
- generated derivatives may exist only below `docs/html/`; a generated
  symlink, executable, or output elsewhere is a boundary failure.

The current-position files and navigation/render integration are
documentation support. They do not define H0 authority, establish a hardware
fact, strengthen an isolation claim, or become K3 evidence.

### Exact pre-commit and post-commit identity

The H0 checker must implement the following two modes and reject every other
repository relation.

1. **Future accepted base.** After a responsible human accepts one exact
   R8-A target, the later commit that records that acceptance becomes the H0
   implementation base. The checker must pin that full commit identity only
   after it exists. The base is currently unknown: no current HEAD,
   development commit, stash, diagnostic, abbreviated object name, or
   placeholder value may be copied into the future pin.
2. **Development mode.** `HEAD` must equal the pinned H0 base, and the normal
   repository index must equal `HEAD`. The candidate exists only as worktree
   additions, modifications, or deletions within the two accepted H0
   authority families, the exact support table above, and the generated
   `docs/html/` prefix. The checker must derive the complete candidate path
   set from repository state and reject any other path; it must not rely on a
   staged index or a hardcoded changed-path count.
3. **Committed-candidate mode.** The worktree and index must be clean, `HEAD`
   must be exactly one child of the pinned base, and the base-to-`HEAD`
   changed-path set must be contained in the same complete enumeration.
   Reports must record the exact full target commit, its exact parent, and
   its exact Git tree. Any merge, extra intermediate commit, unrelated path,
   or different parent relation is a failure unless a later accepted revision
   names one different exact relation.
4. **Prospective/post-commit equivalence.** In development mode, the checker
   must construct the prospective Git target tree from the pinned base plus
   the enumerated worktree candidate without mutating the normal index. It
   must also derive a deterministic semantic projection over all maintained
   non-generated candidate paths and derive that projection's path count.
   In committed-candidate mode, it must derive the same full tree,
   non-generated semantic projection, and path count from `HEAD`. The
   pre-commit and post-commit values must match exactly. No transient index
   entry count, remembered diagnostic count, or manually maintained constant
   may substitute for that derivation.
5. **Identity versus semantic evidence.** The full Git tree binds every
   committed path, including generated documentation. H0 authority and
   configuration digests bind only the H0 inputs defined by the accepted
   freeze and `tests/r8/`; current-position support files remain integration
   metadata, not authority or hardware evidence.

The exact target commit cannot exist before commit, so development-mode
reports may label it `prospective-uncommitted` while recording the pinned
parent and prospective tree. The committed-candidate report must replace that
label with the exact target/parent/tree identity. This identity envelope is
separate from the deterministic H0 semantic content and digest.

### Generated-documentation exclusion

Changes under `docs/html/` must not alter deterministic H0 report content,
authority/configuration digests, or semantic comparison. The report may carry
only bounded status fields stating that planning documentation was generated
and that its check passed. Generated filenames, file counts, byte counts,
hashes, and churn are excluded from H0 semantics and must not be copied into a
stable report.

This exclusion does not weaken the exact Git candidate identity: generated
files remain part of the committed Git tree and must remain confined to the
authorized prefix and mode. It only prevents derivative site churn from
changing the H0 security meaning.

### H0 candidate gates after R8-A acceptance

The exact H0 candidate must pass:

1. the standalone checked H0 gate under `tests/r8/`;
2. `./be docs-check`; and
3. `make check`, the complete existing repository gate.

Those gates must be run both against the prospective development candidate
where applicable and against the exact clean committed candidate. Root
`./be r8-*`, root `Makefile`, `be`, `scripts/check-be.sh`, and acceptance-pin
integration remain deferred and unauthorized.

## Plan revision R8-C: content-based retired-parent scan

**Status: proposed, not reviewed.** R8-C defines only the minimum future
correction to the repository-wide retired-parent namespace scan and the
automated regression coverage needed to keep that correction fail-closed. It
does not implement the correction, alter the blocked H0 candidate, authorize a
successor H0 candidate, or change any R8 hardware or runtime boundary.

The R8-C suffix follows repository convention rather than PMR-081 wording.
The R8-B label is already present in repository history at exact object
`c6e0da62f99a5bf0cb3435f7495129962a3be21b` on a non-ancestor branch. R8-C
does not merge, adopt, supersede, or derive authority from that object.

Until a responsible human accepts one exact R8-C target and separately
authorizes its implementation:

- `pathfinder/tests/check-source-policy.sh` must remain unchanged;
- exact blocked candidate `6e93461f6ea097cb095e31558f6956dc6c0c2708`
  must remain unchanged;
- no successor H0 candidate may be started or presented for review;
- the accepted R8 and R8-A objects, predecessor pins, and accepted R0-R7
  mechanisms remain immutable; and
- H1-H4 and K3 execution remain blocked or `NOT RUN`.

### Defect and exact diagnostic evidence

The affected command is only the repository-wide `git grep` guarded by the
existing `former_parent` regular expression in
`pathfinder/tests/check-source-policy.sh`. It scans tracked repository content
while excluding generated documentation, the checker itself, and the exact
historical transcript allowance.

Git 2.55.0 treats a tracked binary as a binary match when its arbitrary
instruction bytes happen to satisfy the text regular expression. The exact
blocked evidence is:

| Field | Exact value |
| --- | --- |
| H0 candidate | `6e93461f6ea097cb095e31558f6956dc6c0c2708` |
| Candidate parent | `1f6109f0d0371eb3707e296c3416e8c55235683e` |
| Candidate tree | `b9fe2f7bdc6077651db550ed070930f45e21f58d` |
| Affected path | `tests/r8/run-make.sh` |
| Git mode | `100755` |
| Git blob | `3e5d242fa474be70a708b44b38a155a9a325a562` |
| Blob size | `750384` bytes |
| Matching bytes | `83 78 68 00` at zero-based offsets `298230` and `306332` |
| Printable retired-name string | none |
| Git diagnostic | binary match followed by the checker's existing retired-parent failure |

`tests/r8/run-make.sh` is a static ELF despite its `.sh` suffix. A filename,
suffix, path allowlist, executable bit, or H0-specific exception therefore
cannot determine whether the namespace policy applies. The decision must be
based on content.

The maintained PMR-080 descriptions in `planning/HANDOFF.md` and
`planning/roadmap.md` are genuine text evidence about this failure. Their
retired spelling must be represented with byte or hexadecimal notation in the
R8-C review integration. They must not create a new checker exception or be
removed as if the diagnostic had not occurred.

### Required text-versus-binary semantics

The future implementation must preserve the current policy while changing
only how the repository-wide retired-parent scan treats binary content:

1. Add Git's content-based binary exclusion to that one `git grep` operation,
   using `git grep -I` semantics with the existing line-number and extended
   regular-expression behavior.
2. Let Git classify text versus binary from content. Do not classify by
   filename, suffix, path, mode, generated-file list, or H0 inventory.
3. Continue scanning every tracked text path selected by the current
   repository-wide pathspec, including a text file with a misleading binary
   suffix or no suffix.
4. Preserve the existing `former_parent` regular expression byte-for-byte.
   R8-C does not weaken, rewrite, or narrow any of its alternatives.
5. Preserve every existing pathspec exclusion byte-for-byte, including the
   exact historical transcript allowance at
   `planning/session-analysis-isolation-engine-2026-07-20.md`.
6. Add no exception for `tests/r8/run-make.sh`, `tests/r8/**`, executable
   files, ELF files, or the blocked candidate.
7. Leave every other source-policy check, diagnostic, path, and publication
   rule unchanged.

The intended result is narrow: arbitrary non-text bytes cannot create a
retired-parent failure, while a genuine text spelling still produces the same
failure under the same regular expression and path boundary.

### Exact future implementation path inventory

After exact R8-C acceptance and separate implementation authorization, the
complete new path authority for this correction is exactly:

| Path | Required Git mode | Authorized change |
| --- | --- | --- |
| `pathfinder/tests/check-source-policy.sh` | `100755` | Add content-based binary exclusion only to the repository-wide `former_parent` scan and keep its comments synchronized with the unchanged policy boundary |
| `pathfinder/tests/check-source-policy-regression.mjs` | `100644` | Add one bounded, dependency-free regression driver that exercises the real checker in disposable local Git fixtures |
| `pathfinder/Makefile` | `100644` | Add exactly one `toolcheck` invocation for the regression driver; change no target dependency or other command |

No fourth implementation path is authorized. In particular:

- no predecessor acceptance pin or acceptance checker may change;
- no `tests/r8/` source, H0 contract, H0 report, generated evidence, runtime,
  image, assembly, linker, hardware, H1-H4, root integration, dependency, or
  publication path may change for this correction;
- no separate shell test driver is authorized;
- no root `Makefile`, `be`, or `scripts/check-be.sh` change is authorized;
- no Helium documentation source under `pathfinder/docs/` is required because
  the command, policy contract, diagnostics, and user-facing workflow remain
  unchanged; and
- no generated path under `pathfinder/docs/html/` is authorized.

The existing Helium documentation already states that the complete gate
includes source-policy checks. The future source comment and regression driver
must document the content-classification detail. If implementation discovers
that a standalone documentation source or generated derivative must change,
work must stop for another reviewed revision that enumerates every such path
exactly before it is edited.

### Required regression coverage

The regression driver must use only repository-standard Node.js and Git. It
must create disposable local fixtures, clean them on every exit, and exercise
the real `pathfinder/tests/check-source-policy.sh`; a reimplementation of the
regular expression is not sufficient evidence.

The driver must generate test bytes at run time from numeric byte values.
It must not permanently embed a forbidden text spelling in tracked source,
add a fixture path to the checker's exclusions, or retain a generated fixture.
At minimum it must prove:

1. **Binary regression:** a tracked mode-`100755` file with a `.sh` suffix,
   at least one NUL byte, and the byte sequence `83 78 68 00` does not cause
   the checker to fail.
2. **Filename neutrality:** binary exclusion follows content rather than the
   `.sh` suffix, and a tracked text file with a misleading `.bin` suffix is
   still scanned.
3. **Genuine text rejection:** generated text cases containing byte sequences
   `78 68`, `78 68 5f`, and `58 48 5f` in the contexts covered by the
   unchanged regular expression each cause the real checker to fail with its
   existing retired-parent diagnostic.
4. **Historical allowance preservation:** the unchanged baseline repository
   continues to permit only the existing exact transcript allowance.
5. **No policy drift:** a source inspection assertion binds the production
   scan to content-based binary exclusion while confirming that the regular
   expression and pathspec exclusions remain unchanged.

`pathfinder/Makefile` must run this driver from the existing `toolcheck`
target after the live source-policy check. The existing `node --check
tests/*.mjs` syntax gate remains in place. No new package, downloaded tool,
network access, environment override, or success-shaped skip is permitted.

### Successor H0 base and identity boundary

R8-C acceptance alone grants no implementation authority. A later,
responsible-human implementation instruction must name the full approved base
and direct-child relation. Following the accepted R8-A identity model, the
R8-C acceptance-record commit is the only eligible default base, and a
successor H0 candidate must be exactly one clean child of that base unless a
later accepted revision names a different relation.

That one child may contain:

- the complete H0 and R8-A path sets already authorized by accepted R8 and
  R8-A, freshly reconstructed under their existing checks; and
- exactly the three R8-C implementation paths enumerated above.

The R8-C paths are repository-gate support, not H0 authority, configuration,
hardware evidence, or claim inputs. They remain bound by the candidate's full
Git tree but must not enter the existing 33-path H0 semantic projection or
change its claim boundary merely by being added.

The successor must freshly derive every maintained path, Git mode, blob,
candidate tree, semantic projection, path count, report identity, and
base-to-target relation. It must rerun the standalone H0 gate,
`./be docs-check`, the R8-C regression driver, and `make check` against both
prospective content where applicable and the exact clean committed target.

Blocked candidate `6e93461f6ea097cb095e31558f6956dc6c0c2708`
remains immutable diagnostic evidence. It is not the future base, is not
amended, is not byte-ground to evade the match, and does not supply a trusted
path, hash, tree, count, projection, or report value to the successor.

### Effect and non-goals

If an exact R8-C plan target is accepted, it only makes the three-path
correction eligible for a later separate implementation authorization. It
does not itself:

- modify or accept the checker implementation;
- accept, unblock, amend, or supersede the blocked H0 candidate;
- authorize a successor H0 candidate or choose its exact base commit;
- reduce the 80 unresolved H0 facts or establish any board, firmware, tool,
  memory, hart, capture, or hardware value;
- authorize H1-H4, K3 execution, root integration, an acceptance-pin refresh,
  Linux, multicore, device, DMA, policy, or successor work;
- close the generated-asset reproducibility finding; or
- authorize push, tag, publication, release, or migration.

Any implementation need outside the exact three-path inventory, any change to
the regular expression or historical allowance, any H0 semantic-projection
change, or any different candidate relation is a stop requiring another
reviewed plan revision.

## Selected ordering

R8 puts core-hypervisor correctness and one-board K3 validation before OS
support. It deliberately does not make the previously discussed assurance
cleanup the successor milestone.

Closing R7 acceptance-status reporting or generated-documentation byte
reproducibility would improve evidence hygiene, exact-commit comparison, and
supply-chain auditability. It would not validate G-stage behavior, trap and
switch semantics, optional architectural state, firmware handoff, PMP/Smepmp,
cache behavior, or the core/platform split on hardware. Those open
reproducibility findings remain recorded and may be handled by a separately
bounded tooling package; they are not silently folded into R8.

Linux and a protected service remain deferred until the core design and K3
results have been reviewed. R8 does not select a guest ABI, guest SBI surface,
service decomposition, policy framework, device model, or MVP.

## Phase question

> What is the smallest single-hart SpacemiT K3 X100 experiment that can test
> the accepted Beryllium ownership/channel mechanism and exact transition
> spine on real hardware, expose every material firmware and platform
> assumption, and inform the still-open core design without importing an OS,
> multicore execution, devices, DMA, policy, or a broader assurance claim?

## Objective

R8 must produce an exact, reviewable answer to four narrower questions:

1. **Platform reality:** which K3 X100, firmware, boot, CSR, PMP/Smepmp,
   interrupt, timer, optional-state, cache, debug, and external-master facts
   are actually observed on one delivered board?
2. **Core portability:** can the accepted single-hart synthetic
   management-to-protected-to-management scenario execute with the common
   policy-neutral mechanism unchanged and only a bounded K3 platform/profile
   boundary added?
3. **Semantic agreement:** do QEMU and K3 produce the same canonical
   access/fault/switch outcomes where the ratified architecture requires
   agreement, with every permitted hardware-specific difference enumerated?
4. **Design consequence:** which core assumptions survive, which remain
   trusted, and which require a separately reviewed design or plan revision?

R8 is a validation and design-information milestone. It is not an OS bring-up,
production board-support package, hardware certification, or general K3
hypervisor port.

## Supportable completion claim

If every accepted package and evidence gate below passes, the strongest
planned statement is:

> On one exact SpacemiT K3 X100 board, firmware, boot, and single-active-hart
> profile, repeated GCC and Clang Beryllium images execute the fixed synthetic
> management-to-protected-to-management scenario: the monitor validates and
> seals the fixed configuration, derives and installs two Sv39x4 roots, admits
> the tested private and directional-shared accesses, denies the tested
> cross-private and shared-write accesses with the expected architectural
> fault classes, and completes each tested root switch only after the required
> local-hart invalidation. Canonical K3 outcomes agree with the bounded QEMU
> baseline for the fields the ratified architecture fixes.

Required limit:

> This is bounded functional and conformance evidence for one board and one
> fixed lab profile. It does not prove the C core, compiler, linker, firmware,
> OpenSBI, bootloader, hardware, cache hierarchy, debug state, DMA isolation,
> arbitrary guests, arbitrary page tables, multicore behavior, whole-system
> noninterference, production readiness, or formal verification of Beryllium.

The final statement must be regenerated from exact retained evidence. A failed
or incomplete hardware package leaves the corresponding result `NOT RUN` or
`FAIL`; it never degrades the requirement into a success-shaped claim.

## Fixed R8 scope

| Axis | Fixed R8 choice | Boundary |
| --- | --- | --- |
| SoC execution target | One X100 RV64 core on one exact SpacemiT K3 board | A100 AI cores are excluded because they do not provide the H extension |
| Hart count | One active X100 hart; every other X100 hart must be checked as parked or unavailable under the exact firmware contract | No multicore Beryllium execution, IPI, remote fence, or concurrency claim |
| Privilege chain | Exact recorded and hash-identified board boot chain, then a pinned M-mode firmware/OpenSBI handoff to Beryllium HS | H0 must freeze the actual chain; no architecture-wide OpenSBI selection |
| VS payload | The two role-neutral synthetic stubs from the accepted runtime scenario | No Linux, RTOS, service runtime, shell, VMM, or guest-visible SBI |
| Configuration | One bounded K3 inventory and proposal compiled from an offline normalized profile | No in-core Device Tree parser, stable manifest encoding, or runtime policy |
| Authority | Immutable private ownership plus one explicit directional shared page | No capability, TE, policy service, grant, revoke, or relabeling |
| Translation | Sv39x4, 4 KiB leaves, two roots, VMID zero, local `HFENCE.GVMA x0,x0` | No huge pages, runtime root edits, allocator, or selective-fence optimization |
| Interrupts and timers | Disabled, cleared, not delegated, and supplied by no enabled source | AIA/Sstc are characterized, not used for payload service |
| Devices and DMA | No assigned device and no DMA | External masters must be quiesced or the claim is reduced to CPU-originated accesses |
| Debug profile | Lab profile only, with exact debug/trace state recorded | External debug remains a trusted/excluded bypass; no security-profile claim |
| Output | Bounded firmware console or separately reviewed one-way diagnostic path | Output is evidence only and never carries authority |

The guest GPAs, event sequence, ownership relations, channel direction,
mapping rights, and semantic expectations remain identical to the accepted R5
scenario. K3 system physical addresses, image placement, firmware state, and
platform feature values must come from the accepted H0 freeze; QEMU physical
constants must not be copied merely because they are convenient.

## Predecessor and immutability boundary

R8 depends on the complete accepted R0-R7 history but does not make any
predecessor result a hardware result:

- R1 supplies the accepted policy-neutral copy/validate/seal/derive mechanism;
- R2 supplies the accepted Sv39x4 builder and independent walker;
- R3-R5 supply the accepted QEMU boot, trap, context, and checked-switch
  mechanism;
- R6 supplies adversarial QEMU-only evidence; and
- R7 supplies bounded exact-byte and fixed-configuration proof evidence.

The accepted runtime mechanism, proof, and evidence-input paths for R0-R7 must
remain byte- and mode-identical during R8 implementation. R8 must not edit:

```text
model/
tests/r0/
tests/r1/
tests/r2/
tests/r3/
tests/r4/
tests/r5/
tests/r6/
tests/r7/
include/be/r0-config.h
include/be/r1-config.h
include/be/r2.h
include/be/r3.h
include/be/r4.h
include/be/r5.h
virt/be/r0-config.c
virt/be/r1-config.c
virt/be/manifest.c
virt/be/state.c
virt/be/r3.c
virt/be/r4.c
virt/be/r5.c
arch/riscv/be/r0-*
arch/riscv/be/r3-*
arch/riscv/be/r4-*
arch/riscv/be/r5-*
arch/riscv/be/sv39x4.c
```

The glob notation above describes the accepted families and does not itself
authorize an unenumerated file. H0 must record the exact immutable predecessor
inventory by path, mode, and SHA-256.

The planning package may update maintained current-position documentation,
generated `docs/html/`, VitePress navigation, and only the planning-page
inventory entry in `pathfinder/tests/check-docs-render.mjs`. That shared
renderer change does not alter Helium pages, claims, commands, or component
behavior. No other `pathfinder/` change belongs to R8.

If K3 work reveals that an accepted common-core file must change, all
privileged R8 work stops. The finding must identify the violated assumption,
the smallest proposed common-core change, affected proofs and tests, and the
predecessor acceptance impact in a plan revision. A platform port must not
smuggle a core redesign into an architecture file or acceptance-pin refresh.

## Ordered R8 package graph

R8 is split into five reviewable packages:

| Package | Scope | Depends on | Separate gate |
| --- | --- | --- | --- |
| R8-H0: K3 profile freeze | Non-privileged exact board, firmware, boot, tool, capture, memory, hart, feature, and claim profile | accepted R7; accepted R8 plan; separate R8 implementation authorization | responsible-human acceptance of exact H0 freeze |
| R8-H1: platform characterization | Minimal privileged/read-only probes and retained board observations; no VS entry | accepted H0 | responsible-human acceptance of exact H1 evidence |
| R8-H2: synthetic runtime validation | Additive K3 profile/platform boundary executing the fixed two-domain sequence | accepted H1 | responsible-human authorization after reviewing H1 design consequences |
| R8-H3: differential and negative evidence | Repeated GCC/Clang K3 runs, canonical QEMU comparison, and bounded hardware-safe negative cases | accepted H2 candidate | no relaxed expectation; any new defect stops for revision |
| R8-H4: evidence and review | Deterministic report, bounded bundle, evaluator guidance, exact-target review packet | complete H0-H3 | explicit acceptance of one exact R8 implementation target |

Acceptance of one package does not authorize the next unless the table and a
separate responsible-human instruction both permit it. H0 and H1 may expose a
plan defect or core design issue; in that case the correct result is a paused
R8 with an exact plan revision, not an improvised implementation.

The initial package-location boundary is:

| Package | Planned maintained locations |
| --- | --- |
| H0 | `planning/single-hart-runtime-r8-h0-freeze.md` and host-only profile/tool checks under `tests/r8/` |
| H1 | additive characterization-only entry/linker/platform sources under `arch/riscv/be/r8-h1-*`, plus `tests/r8/` checks and retained H1 evidence |
| H2 | the exact additive path family defined below and finalized by accepted H0 |
| H3-H4 | `tests/r8/`, `planning/single-hart-runtime-r8-evidence.md`, and generated evidence under `build/r8/` |

H0 must replace wildcards with an exact path/mode inventory before privileged
implementation. It may narrow these locations. Adding a new top-level
directory, modifying an accepted file, or adding a path outside the accepted
inventory requires a plan revision.

## R8-H0: exact K3 profile freeze

H0 is documentation, host tooling, and checked input only. It adds no
privileged target behavior and performs no K3 execution presented as R8
evidence.

### Board and silicon identity

The freeze must record:

- board vendor, product, SKU, and revision;
- SoC and X100 stepping/revision identifiers exposed by authoritative means;
- installed DRAM size and relevant memory topology;
- boot medium and board configuration straps;
- serial/console interface and electrical adapter identity;
- board power/reset procedure;
- whether external debug or trace is physically connected; and
- a stable lab inventory identifier that contains no secret or personal data.

One delivered board is the complete hardware population for the R8 claim.
Results must not be generalized to all K3 boards, steppings, firmware builds,
or lifecycle configurations.

### Boot and firmware identity

The freeze must name and hash:

- immutable ROM-reported version or the explicit absence of one;
- first mutable boot stage;
- bootloader;
- OpenSBI or other M-mode runtime;
- firmware configuration;
- the exact board Device Tree blob supplied by firmware;
- Beryllium load and entry addresses;
- initial `a0` hart identity and `a1` firmware-pointer treatment;
- the complete HS-facing SBI allowlist and returned capability probes; and
- the mechanism that parks every non-participating X100 hart.

The accepted synthetic profile's DBCN and SRST assumptions are not copied by
default. H0 must establish whether the exact firmware provides them. If it
does not, R8 stops for a plan revision that defines one bounded diagnostic or
termination boundary. No legacy or direct-MMIO fallback is selected
implicitly.

The firmware pointer remains non-authoritative. R8 may hash and retain the
supplied DTB for provenance, but the core does not parse it. Open host tooling
may produce a normalized descriptor whose complete contents are independently
validated before privileged use.

### Tool and capture identity

The freeze must pin:

- GCC, GNU binutils, and GNU linker;
- Clang, LLVM binary utilities, and lld;
- GNU Make, Node.js, shell, hashing, and ELF-inspection tools;
- OpenOCD/GDB only if they are used;
- the open serial capture tool and exact arguments;
- the host OS/container profile used for normative builds;
- any board flashing tool, including source/license and a local-open
  replacement if the vendor path is not open; and
- every script that resets, loads, captures, canonicalizes, or checks a run.

A proprietary flashing, debug, power-control, or hosted service may be used
for exploratory bring-up only under the blocker policy. Its result is
non-normative and cannot satisfy H0-H4.

### Memory and image profile

H0 must freeze:

- complete usable DRAM and reserved-memory extents;
- firmware, bootloader, DTB, monitor, diagnostic, root-pool, trusted-stack,
  saved-state, guest-code, private-page, and shared-page extents;
- the exact linker script plan and all alignment/non-overlap assertions;
- Sv39x4 guest-physical-width constraints;
- root-table alignment and pool sizes;
- cacheability and memory-type assumptions;
- the offline normalized platform inventory;
- the fixed proposal and expected canonical state; and
- the expected two roots with exactly three mappings each.

Every extent has one owner and one mutation phase. Firmware-reserved or
uncertain memory is excluded. A K3 address is not accepted merely because a
Device Tree node names it.

### Feature and security-state matrix

H0 must define how H1 will observe each item without claiming a result:

- `misa`/ISA identity available to HS and the H extension;
- supported `hgatp` modes and VMID width;
- `henvcfg`, `hstateen*`, counter, and state-enable behavior;
- F, D, V, crypto, and other optional register-state exposure;
- AIA/IMSIC/APLIC topology, `GEILEN`, and pending virtual-interrupt state;
- Sstc and timer delegation;
- PMP and Smepmp/ePMP entries, permissions, lock state, and ownership;
- secure-boot and lifecycle state;
- debug/trace enablement and system-bus access;
- cache hierarchy, coherency, and cache-block-management behavior;
- IOMMU and nine documented IOPMP instances, firmware ownership, and defaults;
- TRNG and crypto-engine visibility;
- PMU/counter filtering;
- RAS/RERI routing; and
- every known bus master that could access experiment DRAM.

Each row must have one disposition: required and tested, disabled and checked,
observed assumption, explicitly excluded, deferred, or stop condition.

### H0 exit gate

H0 is reviewable only when:

1. every identity and expected value is exact or explicitly `UNKNOWN`;
2. every `UNKNOWN` has a fail-closed H1 observation plan;
3. no unknown physical extent is assigned to a domain;
4. no closed or hosted-only tool is normative;
5. every non-participating hart has a planned parked-state check;
6. every possible external master has a quiescence/default-deny disposition;
7. optional architectural state has an exclusion, reset, save/restore, or stop
   disposition;
8. the planned claim remains single-board, single-hart, CPU-originated, and
   synthetic; and
9. responsible-human review accepts one exact H0 commit before H1 begins.

## R8-H1: platform characterization

H1 uses the smallest separately built characterization image or images needed
to measure the accepted H0 matrix. It must not enter VS mode, install a
domain root for execution, or present any observation as isolation evidence.

Facts unavailable to HS, including PMP/Smepmp or machine state-enable values,
may be emitted only by an exact H1 M-mode firmware build whose source,
configuration, and bytes are retained. H2 must use those same firmware bytes
or repeat H1 against the replacement before any runtime claim. A vendor
statement or observation from different firmware is not a substitute.

### Entry and hart state

H1 must establish:

- actual entry privilege and virtualization state;
- exact participating hart ID;
- that every other X100 hart remains parked throughout the observation;
- initial delegation, interrupt, timer, counter, translation, and environment
  controls visible to HS;
- the firmware-provided pointer's provenance without treating it as authority;
  and
- deterministic terminal behavior.

If another hart executes unbounded code against experiment memory, R8 stops.
Parking is a trusted firmware property unless independently enforced and
measured; it is not called Beryllium multicore support.

### H-extension and CSR behavior

H1 must characterize:

- `hgatp.MODE` WARL behavior for Bare and Sv39x4;
- implemented VMID width without relying only on documentation;
- required `hstatus`, `hedeleg`, `hideleg`, `hie`, `hip`, `hvip`,
  `hcounteren`, `htimedelta`, `henvcfg`, and state-enable behavior;
- `vsstatus`, `vsie`, `vstvec`, `vsscratch`, `vsepc`, `vscause`, `vstval`,
  `vsip`, and `vsatp` reset/readback behavior;
- local `HFENCE.GVMA x0,x0` execution and architectural availability;
- guest-page-fault metadata behavior permitted by the ratified specification;
  and
- unsupported or vendor-specific behavior encountered by the profile.

H1 is not an exhaustive ISA conformance suite. Where mainline Sail lacks the
required H semantics, the ratified specification and the bounded R7 Rocq model
remain explicit references, not a claim that K3 refines either.

### Optional state stop rule

The accepted QEMU profile excludes F, D, V, and other unmodeled register files.
K3 may expose them. Before H2 VS entry, every guest-accessible optional state
element must be:

1. absent or disabled by the exact firmware profile and checked from HS;
2. inaccessible through checked state-enable and privilege controls; or
3. fully added to the save/reset/restore matrix under an accepted plan
   revision.

H2 must not proceed by clearing a summary status bit once or by declaring
unused instructions out of scope. If the existing frame is incomplete for
accessible hardware state, that is a core-design finding and a stop.

### Firmware, PMP, Smepmp, and lifecycle

H1 must retain the complete observable PMP/Smepmp state and classify:

- monitor and experiment DRAM reachability from HS and lower modes;
- locked entries and who can change them;
- whether firmware leaves a broader executable/writable region than H0
  assumed;
- whether the M-mode runtime can access all experiment state;
- secure-boot/lifecycle indications available through documented interfaces;
  and
- debug or system-bus paths that bypass CPU privilege checks.

M-mode firmware remains trusted in the first K3 lab profile. Recording PMP or
secure-boot state does not prove firmware integrity, measured launch, or
anti-rollback.

### Interrupts, timers, counters, and state-enable

H1 must inventory AIA/Sstc/state-enable behavior but keep the H2 payload
quiescent:

- no enabled interrupt source;
- no delegated or pending VS interrupt;
- no guest timer;
- no counter or PMU access from VS;
- no AIA guest-file use; and
- no asynchronous path in the checked transition sequence.

An interrupt, timer, or external event that cannot be disabled and checked is
a stop condition. R8 does not add interrupt or timer virtualization merely to
keep the payload running.

### Cache, external masters, IOMMU, and IOPMP

H1 must:

- establish the CPU cacheability and ordering properties needed for private
  and shared pages;
- establish instruction visibility at the firmware-to-HS handoff, including
  any required `FENCE.I` or platform cache operation;
- identify any required CPU-side fence or cache-maintenance operation;
- enumerate active or potentially active non-CPU bus masters;
- locate documented IOMMU and IOPMP instances;
- record firmware ownership, access restrictions, lock state, and
  default mappings where observable; and
- verify that no R8 payload relies on DMA or a device interrupt.

R8 does not configure a device protection domain. If external-master
quiescence or default-deny behavior cannot be established, H2 may support only
the explicitly narrower CPU-originated access claim, and the limitation must
be visible in every report. It may not claim whole-memory isolation.

### H1 exit gate

H1 is reviewable only when the exact H0 matrix is complete, all raw
observations are integrity-hashed, every unexpected value has a disposition,
and the design-consequence ledger says one of:

- `compatible-with-additive-h2`;
- `plan-revision-required`; or
- `r8-blocked`.

Only the first result is eligible for H2 authorization.

## R8-H2: fixed synthetic runtime validation

H2 may begin only after accepted H0 and H1 exact targets and a separate
responsible-human instruction. It adds no OS and preserves the fixed
two-domain scenario.

### Required execution sequence

The hardware sequence remains the accepted runtime sequence:

1. pinned M-mode firmware enters Beryllium in HS on the one participating hart;
2. Beryllium validates the H0 handoff, image layout, feature profile, and
   single-hart condition;
3. it binds the normalized K3 inventory and copies the fixed proposal;
4. it validates inventory closure, non-overlap, monitor exclusion, ownership,
   bindings, channel direction, and rights;
5. it seals canonical state exactly once;
6. it derives and independently re-walks two complete Sv39x4 roots;
7. it installs and verifies the management root before the first VS entry;
8. management reads/writes its private page, is denied the protected private
   page, and writes the shared page;
9. management emits the exact private test event;
10. HS performs the checked management-to-protected switch;
11. protected reads/writes its private page, is denied the management private
    page, reads the shared value, and is denied a shared-page write;
12. protected emits the exact return-switch event;
13. HS performs the checked protected-to-management switch and verifies
    management state restoration; and
14. management emits the exact completion event before bounded termination.

Every positive access is a real VS load/store. Every denial is a real
guest-page fault checked for exact cause, PC, active binding, GVA, available
GPA reconstruction, and unchanged denied backing. Hardware-permitted optional
metadata is compared according to an H0-enumerated rule, never ignored
dynamically.

### Additive implementation boundary

The initial H2 candidate may add only:

```text
include/be/r8.h
virt/be/r8-config.c
virt/be/r8.c
arch/riscv/be/r8-platform.h
arch/riscv/be/r8-entry.S
arch/riscv/be/r8-trap.S
arch/riscv/be/r8-guest.S
arch/riscv/be/r8-runtime.c
arch/riscv/be/r8-beryllium.lds
tests/r8/
planning/single-hart-runtime-r8-evidence.md
```

This is a planned maximum family, not permission to create every file. H0 must
replace it with an exact path inventory before H2 implementation is
authorized. Reuse of unchanged generic implementation objects is preferred to
copying accepted code. R8-specific configuration, physical layout, platform
entry, linker, and evidence code must remain visibly separate from the
architecture-neutral mechanism.

The root `Makefile`, `be`, and `scripts/check-be.sh` are not part of initial H2
implementation. Root integration and every resulting predecessor
acceptance-pin refresh must be enumerated in an accepted plan revision after a
standalone R8 package passes. No diagnostic hash or scratch value may be
copied into an acceptance checker.

### Core-design stop rule

H2 must stop before a prospective change that:

- alters an accepted architecture-neutral state or authority invariant;
- changes the R1/R2 canonical or root result rather than instantiating it with
  a K3 profile;
- widens the trap, event, SBI, interrupt, timer, or failure surface;
- adds optional-state save/restore not enumerated by accepted H0/H1;
- weakens an exact fault, binding, fence, or publication expectation;
- adds a parser, allocator, scheduler, runtime root edit, or policy callback;
- changes another accepted package's source or acceptance checker; or
- requires a second active hart, device, DMA, or guest-visible SBI.

Such a finding is useful R8 design evidence. It is not permission to fix the
core in place.

## R8-H3: differential and negative evidence

H3 compares canonical semantics, not raw UART timing or unspecified metadata.

### Repeated execution

The minimum retained matrix is:

| Build | QEMU regression | K3 runs | Required result |
| --- | ---: | ---: | --- |
| GCC/GNU ld | accepted predecessor gates plus a separately built R8 QEMU profile if required | 3 cold boots | exact canonical PASS sequence |
| Clang/lld | accepted predecessor gates plus a separately built R8 QEMU profile if required | 3 cold boots | exact canonical PASS sequence |

Cold boot must mean the H0-defined reset/power sequence. Warm reset may be a
separate observation but cannot substitute for the required matrix.

H0 must choose the QEMU comparison input exactly. It may reuse the accepted R5
canonical semantic record only if every compared field has the same meaning
under the K3 profile. If layout or platform inputs prevent that mapping, H0
must require an additive R8 QEMU profile and enumerate its source boundary
before H2. “If required” is not a run-time choice.

### Canonical comparison

The checker must compare at least:

- accepted configuration identity and complete canonical authority;
- root count, mapping count, GPA/frame/right tuples, and each profile's
  independently expected HGATP mode/VMID/root PPN; numeric HGATP values need
  not equal when system physical root addresses differ;
- entry, fault, event, switch, and termination order;
- active domain, vCPU, root, VMID, stack, and saved-state identity;
- exact mandatory `scause` and `sepc` values;
- `stval`, `htval`, and `htinst` under the ratified permitted-value matrix;
- source save and target restore observations;
- backing-memory values before and after each denied access;
- root-write, local-fence, readback, and publication acknowledgements; and
- absence of interrupts, timers, unexpected harts, devices, and DMA.

QEMU and K3 need not emit byte-identical raw traces. Canonicalization may
remove only fields explicitly classified as non-semantic or
architecture-permitted in accepted H0. The raw record, rule, and canonical
record are all retained and hashed.

### Negative coverage

H3 must include:

- host mutation tests for every K3 profile and report rejection;
- image/layout checks for every monitor, root, stack, saved-state, guest,
  private, and shared extent;
- wrong hart, handoff, feature, PMP-profile, optional-state, binding, root,
  event, PC, and backing-state rejection before guest entry where practical;
- real protected-private, management-private, and shared-write access denials;
- proof that a checker rejects removed or reordered fence/publication
  acknowledgements without executing a deliberately unsafe hardware image;
  and
- terminal handling for every safely injectable unexpected event.

R8 must not intentionally execute a skipped-fence or partially published image
on K3 merely to seek a fault. R6's QEMU-only adversarial result does not become
hardware evidence.

## R8-H4: report, evidence, and review

H4 must produce:

- one deterministic `be-r8-k3-core-validation-v1` report for a fixed checked
  input set;
- exact source, tool, board, firmware, boot, DTB, image, ELF, allocated-image,
  linker-map, configuration, and checker identities;
- H0 and H1 matrices with every required/disabled/assumed/excluded/deferred/
  stop disposition;
- complete GCC/Clang run manifests;
- raw serial digests, byte counts, and bounded retained records;
- canonical QEMU/K3 comparisons;
- a core-design consequence ledger;
- a claim, assumption, trusted-boundary, and non-claim ledger;
- independent report and evidence mutation tests;
- an evidence bundle below a hard 512 MiB limit;
- evaluator guidance that can be followed with fully open local tools; and
- an exact-target responsible-human review packet.

The evidence bundle must never contain secrets, device keys, private serial
numbers, credentials, or unredacted personal data. Redaction rules must be
defined before capture and must not remove a security-relevant value.

No report accepts its own target. R8 acceptance requires a later explicit
responsible-human decision naming one exact clean implementation commit.

## Hardware disposition matrix

| K3/RISC-V feature | R8 disposition | Planned evidence | Stop or later boundary |
| --- | --- | --- | --- |
| RVH 1.0 | Required | H1 CSR/WARL observations plus H2 VS execution | missing or incompatible H behavior blocks R8 |
| Sv39x4 | Required | H1 mode/width probe; H2 roots and real faults | no fallback translation mode |
| VMID | Measure width; use zero in H2 | WARL probe and HGATP readback | optimization or nonzero allocation is later |
| Local `HFENCE.GVMA` | Required | exact instruction evidence and checked readback order | no skipped-fence hardware fixture |
| F/D/V and optional state | Exclude/inhibit or stop | state-enable and access observations | full context support requires revision |
| AIA/IMSIC/APLIC | Characterize and quiesce | topology, GEILEN, pending/enable state | injection and routing are later |
| Sstc/timers | Characterize and disable | delegation and enable-state observations | guest timer support is later |
| Counters/PMU | Deny and verify | counter/state-enable readback and negative access | performance work is later |
| PMP/Smepmp | Record exact handoff | complete observable entry/lock matrix | reprogramming or firmware replacement is later |
| Cache/coherency | Test CPU-side requirement | shared-page ordering observations | DMA coherency is later |
| IOMMU/IOPMP | Locate and characterize only | ownership/access/default-state record | no device domain or DMA claim |
| Secure boot/lifecycle | Record assumption | documented state and firmware provenance | measured launch/attestation is later |
| Debug/trace | Record lab state and exclude | connection, enable, auth/lock observations | security-profile lockdown is later |
| TRNG/crypto | Inventory only | documented visibility or `NOT RUN` | no cryptographic dependency |
| RAS/RERI | Inventory/routing only | documented state or `NOT RUN` | no containment claim |
| A100 cluster | Excluded | board inventory | never an H2 execution target |

## Core-design question ledger

R8 must not answer an open design question by accident. The report must carry
one explicit disposition for each row:

| Question | R8 test | Possible consequence |
| --- | --- | --- |
| Is the architecture-neutral mechanism free of QEMU physical-layout assumptions? | instantiate one K3 inventory/layout without editing accepted common-core bytes | retain split, or stop for a common-core revision |
| Is the saved-state matrix complete for real K3 exposure? | H1 optional-state and state-enable characterization | proceed, or add a separately planned complete context |
| Is OpenSBI below HS an acceptable first hardware dependency? | exact firmware/SBI/PMP handoff record | retain as lab assumption, replace later, or stop |
| Can one active hart be established honestly on an eight-core SoC? | retained parked-hart evidence throughout H1-H3 | keep single-hart claim or move to a later multicore plan |
| Are G-stage fault metadata checks portable? | compare ratified mandatory and permitted fields across QEMU/K3 | keep exact common checks and isolate permitted variance |
| Is the root-write/fence/readback/publication contract sufficient on K3? | exact H2 transition sequence and real access outcomes | retain or revise the architecture boundary |
| Does the fixed CPU-side shared channel need cache maintenance beyond existing ordering? | repeated shared-value and ordering observations | add a bounded platform primitive or stop |
| Can DMA be excluded from the claim honestly? | inventory/quiescence/default-deny evidence for external masters | CPU-only claim or later IOMMU/IOPMP plan |
| Is the diagnostic/termination dependency narrow and fail-closed? | exact SBI or revised one-way boundary tests | retain, revise, or stop |
| Which proof cut points remain unconnected? | map H1-H3 observations to the R7 ledger | preserve assumptions; no proof transfer |

The ledger informs later architecture decisions. R8 acceptance does not by
itself select a new M-mode runtime, interrupt model, device model, manifest
encoding, or production hardware profile.

## M-mode, SBI, and diagnostic boundary

R8 retains the architectural separation among:

1. the M-mode firmware used to enter HS;
2. the bounded HS-to-M calls used by the experiment; and
3. a future guest-visible SBI interface.

Only the first two exist in R8. The VS stubs use the private fixed event
protocol, not SBI. No guest request is forwarded to M-mode.

H0 must freeze the exact SBI extension/function allowlist and all failure
behavior. Every call must use bounded monitor-owned arguments, handle partial
progress or errors explicitly where applicable, and be unable to change
authority. Missing functionality fails the profile.

R8 does not decide whether a future Beryllium-owned M-mode component, minimal
independent runtime, or OpenSBI remains the production boundary.

## Normalized platform input

The board DTB and firmware tables are offline evidence inputs only. Open host
tooling may extract a bounded K3 profile into restricted-C declarations, but:

- the original input and normalized output are both hashed;
- extraction grants no authority;
- Beryllium independently validates every extent and feature requirement;
- the fixed proposal remains separate from inventory;
- canonical state remains the only trusted authority after sealing; and
- no general FDT parser enters the R8 core.

The H0 representation is an internal fixed profile, not a stable encoding,
attested manifest, public ABI, or Linux interface.

## Tool, trust, and evidence boundary

All normative R8 tools must satisfy
[Open tooling](open-tooling.md). The initial candidates are:

- pinned GCC/GNU binutils and Clang/LLVM;
- GNU Make and the existing checked launcher pattern;
- open ELF/disassembly utilities with an independent cross-check;
- open serial, OpenOCD, and GDB tools only where actually required;
- Node.js for deterministic host-side checking;
- Rocq only for rechecking retained R7 prerequisites, not for a new hardware
  refinement claim; and
- QEMU as the accepted functional comparison platform.

R8 trusts or leaves unverified:

- the exact K3 CPU/SoC and board implementation;
- ROM, bootloader, firmware, and OpenSBI;
- the firmware configuration and hart-parking behavior;
- compilers, linkers, ELF tools, capture host, and physical cabling;
- the correctness and completeness of observed CSR/debug/security state;
- the canonicalizer and report/evidence checkers;
- the ratified specification and bounded R7 model at their stated cut points;
  and
- human review and lab procedure.

Independent checking should reduce but cannot erase those boundaries.

## Planned command surface

No command is created or promised by this proposed plan. If the accepted H0
path and implementation authorization later establish the package, the
planned standalone interfaces are:

```sh
./tests/r8/run-make.sh r8-toolcheck
./tests/r8/run-make.sh r8-profile-check
./tests/r8/run-make.sh r8-characterize
./tests/r8/run-make.sh r8-host-test
./tests/r8/run-make.sh r8-image
./tests/r8/run-make.sh r8-image-check
./tests/r8/run-make.sh r8-qemu
./tests/r8/run-make.sh r8-k3
./tests/r8/run-make.sh r8-compare
./tests/r8/run-make.sh r8-report
./tests/r8/run-make.sh r8-evidence
./tests/r8/run-make.sh r8-check
```

`r8-k3` must require an explicit exact-board profile and must never silently
substitute QEMU or a cached transcript. Hardware-unavailable execution reports
`NOT RUN`, not PASS.

Root `./be r8-*` integration is deferred until a separately accepted
enumeration covers the root files and every predecessor acceptance pin.

## Acceptance gates

An R8 implementation candidate is reviewable only when:

1. the exact R8 plan and exact H0/H1 packages were separately accepted;
2. implementation and H2 execution were separately authorized;
3. the exact board/firmware/tool/profile identities are retained;
4. every non-participating hart remains parked for every normative run;
5. every optional architectural state element has the accepted disposition;
6. every accepted R0-R7 mechanism, proof, and evidence-input byte in the H0
   immutable inventory remains unchanged;
7. all R0-R7 acceptance interfaces still report their accepted boundaries;
8. the R8 common-core reuse boundary and exact additive path inventory pass;
9. GCC and Clang host/image checks pass;
10. at least three cold K3 runs per compiler produce the exact canonical PASS
    sequence;
11. required canonical QEMU/K3 fields compare exactly and every permitted
    variance is accepted-plan data;
12. real private/channel positive accesses and cross-private/shared-write
    denials pass;
13. no interrupt, timer, unexpected hart, device, or DMA enters the scenario;
14. all report/evidence mutation and stale-artifact tests pass;
15. raw and canonical evidence is integrity-hashed and stays below 512 MiB;
16. `./be r7-check`, `./be docs-check`, and the complete existing repository
    gate pass from the exact candidate as applicable;
17. hardware, firmware, proof, C-refinement, OS, multicore, DMA, security-
    profile, and production claims remain no stronger than retained evidence;
18. a decision-neutral exact-commit review packet is prepared; and
19. the responsible human explicitly accepts one exact R8 implementation
    commit.

Passing gates 1-18 does not satisfy gate 19 automatically.

## Explicit non-goals

R8 does not add or authorize:

- Linux, another OS, a VMM, protected service, or service runtime;
- a guest-visible SBI, hypercall ABI, UAPI, stable manifest encoding, or
  in-core Device Tree parser;
- multicore Beryllium execution, IPIs, remote fences, scheduling, migration,
  or concurrency;
- interrupt injection, guest timers, AIA guest files, or performance tuning;
- a device, DMA, IOMMU/IOPMP programming, driver domain, or queue protocol;
- runtime domain creation, allocation, root edits, grants, revocation, or
  policy updates;
- capabilities, CHERI, TE, CAP+TE, VBS/VTL, attestation, key sealing, or
  measured launch;
- a complete C refinement, whole-image proof, whole-system noninterference,
  formal verification, certification, or production assurance claim;
- general K3 board support, all steppings, all firmware, or a security-profile
  debug-lockdown result;
- R7 acceptance-status tooling, generated-documentation reproducibility
  closure, or report/bundle/`.vo` byte-reproducibility work;
- public push, tag, publication, release, upstream submission, or migration
  to a clean public repository; or
- R9 or any later successor.

## Planning deliverables

This planning package must contain:

1. this bounded R8 contract;
2. maintained current-position updates in `README.md`, `planning/README.md`,
   `planning/HANDOFF.md`, `planning/implementation-plan.md`, and
   `planning/roadmap.md`;
3. a K3 hardware-roadmap update preserving the single-hart-before-OS order;
4. documentation navigation and generated HTML;
5. no production, test-runtime, proof, root-wrapper, or acceptance-pin change;
   the shared renderer changes only by one planning-page inventory entry;
6. successful documentation and repository consistency checks; and
7. after the plan is committed, a separate decision-neutral exact-commit
   review packet.

## Current state with proposed Plan revision R8-C

```text
r7_acceptance=accepted-by-review-record
r7_accepted_commit=9bf22913d67e9b72286813cd5f7993a9ad3857a8
r8_direction=combined-k3-core-validation
r8_planning_authorization=authorized
r8_planning_authorization_source=responsible-human-instruction-2026-08-07
r8_plan=accepted
r8_accepted_plan_commit=7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5
r8_plan_revision_r8a=accepted-exact-target
r8_plan_revision_r8a_target=8fa9d672cfcfb81ab68d9ed9553a5af48b884932
r8_r8a_acceptance_record_base=1f6109f0d0371eb3707e296c3416e8c55235683e
r8_plan_revision_r8c=proposed-not-reviewed
r8_r8c_implementation_authorization=none
r8_implementation=authorized-h0-only-under-accepted-r8-r8a
r8_h0_implementation_authorization=authorized-existing
r8_h0_candidate=6e93461f6ea097cb095e31558f6956dc6c0c2708-blocked-unaccepted
r8_h0_successor=not-authorized
r8_h1=not-started
r8_h2=not-started
r8_h3=not-started
r8_h4=not-started
r8_hardware_execution=NOT-RUN
r8_os_scope=excluded
r8_multicore_scope=excluded
r8_device_dma_scope=excluded
r8_publication_scope=blocked
```

## Primary references

Project decisions and evidence:

- [R7 review and acceptance record](single-hart-runtime-r7-review-summary.md)
- [R7 bounded proof and evidence plan](single-hart-runtime-r7-plan.md)
- [R7 bounded exact-proof evidence](single-hart-runtime-r7-evidence.md)
- [Bounded single-hart runtime plan](single-hart-runtime-plan.md)
- [Architecture Model 0.2](architecture-model-0.2.md)
- [Architecture Model 0.2 evidence](architecture-model-0.2-evidence.md)
- [Post-pathfinder architecture decision](pathfinder-comparison.md)
- [RISC-V and K3 security-hardware roadmap](riscv-security-hardware.md)
- [M-mode, SBI, and VS decomposition](beryllium-hypervisor-notes.md)
- [Open tooling policy](open-tooling.md)
- [CHERI alignment](cheri-alignment.md)
- repository-root `LLM_POLICY_ALIGNMENT.md`

External primary sources already tracked by the project:

- RISC-V International, Hypervisor Extension:
  <https://docs.riscv.org/reference/isa/priv/hypervisor.html>
- RISC-V International, Privileged Architecture:
  <https://docs.riscv.org/reference/isa/priv/priv-index.html>
- RISC-V SBI specification:
  <https://github.com/riscv-non-isa/riscv-sbi-doc>
- OpenSBI:
  <https://github.com/riscv-software-src/opensbi>
- SpacemiT K3 datasheet and security documentation:
  <https://github.com/spacemit-com/docs-chip>
- upstream K3 Device Tree series:
  <https://lore.kernel.org/linux-riscv/20260115-k3-basic-dt-v5-0-6990ac9f4308@riscstar.com/>
- mainline Sail RISC-V H-extension status:
  <https://github.com/riscv/sail-riscv/wiki/Hypervisor-Implementation-Status>

H0 must recheck and pin every load-bearing external source it uses. This
proposed plan does not convert a public datasheet statement into measured K3
evidence.
