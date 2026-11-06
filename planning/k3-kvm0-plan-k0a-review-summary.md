<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# KVM0 K0-A plan review and acceptance record

This document began as the decision-neutral responsible-human review packet
for exact planning target `5227266ceddb664a1595e22e5a92da57a013652f`,
whose immediate parent is `8348b18a2c00c992e8fbf744f2004dfcd55500e6`
and whose Git tree is
`2a716a0ca69a7d0ada92b978bd77704fbfc8910b`, and now also records the
responsible-human decision taken on that target. The decision-support material
below is retained as the exact pre-decision review history and remains the
evidence the decision rests on. Except where a statement is explicitly marked
as current, sections 1 through 9 describe the state at packet preparation.

The target carries **Plan revision K0-A**, which corrects five material
independent-review findings in the first KVM0 proposal. Original plan target
`459184dd8fe9c5da20e27a9e277a076685a520cb` and first packet commit
`8348b18a2c00c992e8fbf744f2004dfcd55500e6` remain immutable historical,
superseded, and unaccepted objects.

## Decision record

Responsible-human review accepted exact KVM0 Plan revision K0-A target
`5227266ceddb664a1595e22e5a92da57a013652f` over parent
`8348b18a2c00c992e8fbf744f2004dfcd55500e6`, tree
`2a716a0ca69a7d0ada92b978bd77704fbfc8910b`, on September 25, 2026, by the
exact instruction `5227266ceddb664a1595e22e5a92da57a013652f is accepted exactly`.

This decision applies only to that exact immutable plan target. Target
`5227266ceddb664a1595e22e5a92da57a013652f` remains byte unchanged, including
its frozen pre-decision `proposed-not-reviewed`,
`pending-exact-plan-decision`, and `none` fields. This record and the
maintained current-position documents carry the later decision; the immutable
plan file is not rewritten after review.

Packet commit `6369804904eb28554c65886db93f0d30be80fcab`
(`docs: add exact KVM0 K0-A review packet`) and this acceptance-record
follow-up are decision support. Neither is plan text, implementation,
execution, imported source evidence, a KVM0 result, Beryllium or R8 hardware
evidence, or an approved implementation base.

Status recorded by the K0-A plan decision before the later K0-I and K0-S
decisions was:

```text
kvm0_plan_revision=K0-A
kvm0_plan=accepted
kvm0_plan_target=5227266ceddb664a1595e22e5a92da57a013652f
kvm0_plan_acceptance_date=2026-09-25
kvm0_plan_review_record=planning/k3-kvm0-plan-k0a-review-summary.md
kvm0_gate_k0p=satisfied-by-exact-plan-acceptance
kvm0_gate_k0i=blocked-not-authorized
kvm0_gate_k0s=blocked-source-evidence-not-ready
kvm0_gate_k0x=blocked-not-authorized
kvm0_gate_k0r=blocked-no-result
kvm0_result=NOT-RUN
beryllium_k3_hardware=NOT-RUN
r8_k3_hardware=NOT-RUN
development_kernel_bsp=UNDECIDED
publication=blocked
```

K0-P acceptance does **not** authorize K0-I tooling, K0-S source
preparation or evidence import, K0-X native execution, K0-R result
acceptance, K3 access, B0, B1, an H0 successor, R8 H1-H4, BSP selection,
root integration, acceptance-pin or checker updates, push, tag, publication,
migration, release, or upstream work. It resolves no accepted H0 row and
supplies no Beryllium or R8 hardware result.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact planning commit `5227266ceddb664a1595e22e5a92da57a013652f` (`docs: propose KVM0 plan revision K0-A`), tree `2a716a0ca69a7d0ada92b978bd77704fbfc8910b` |
| Parent / comparison base | `8348b18a2c00c992e8fbf744f2004dfcd55500e6` (`docs: add exact KVM0 plan review packet`) |
| Superseded proposal | Original plan target `459184dd8fe9c5da20e27a9e277a076685a520cb` and packet commit `8348b18a2c00c992e8fbf744f2004dfcd55500e6`; preserved, unaccepted, and not amended |
| Branch and repository | `beryllium/single-hart-runtime-r0`; private repository `beryllium-project/beryllium-hypervisor` |
| Target publication state | Local-only, unpushed, and untagged at packet preparation; zero remote branches and zero tags contain the target |
| Status at the K0-A decision | Plan revision K0-A is **accepted at exact target `5227266ceddb664a1595e22e5a92da57a013652f` as of 2026-09-25**. The target's own proposed/pending fields remain frozen pre-decision content. At that decision, K0-P was satisfied while K0-I, K0-S, K0-X, and K0-R remained blocked. |
| Implementation / execution at the K0-A decision | Destination implementation, source-owner build/selftest preparation, evidence import, K3 access, and native execution were `not-authorized` |
| Hardware and result | KVM0 `NOT-RUN`; Beryllium K3 `NOT-RUN`; R8 hardware `NOT-RUN`; no H0 row resolved; development kernel/BSP `UNDECIDED` |
| Decision | Responsible-human acceptance of exact K0-A plan commit `5227266ceddb664a1595e22e5a92da57a013652f` on 2026-09-25 by the exact instruction quoted above |
| Successor status | No KVM0-B tooling, KVM0-A source preparation, KVM0-C through KVM0-G execution/result work, B0, B1, H0 successor, or R8 H1-H4 work is authorized or started |
| Publication status | Push, tag, publication, release, clean-repository migration, upstream submission, and any `pathfinder/publication-gate.conf` change remain blocked |

**Action taken:** the responsible human accepted exact K0-A plan target
`5227266ceddb664a1595e22e5a92da57a013652f`. That decision satisfies K0-P
only. It does not authorize K0-I, K0-S, K0-X, or K0-R.

## 2. Deliverables and exact inventory

With rename detection, the exact parent-to-target delta contains **96 changed
entries**:

- 79 modified entries;
- three added entries;
- three deleted entries;
- 11 renamed entries;
- six maintained planning/current-position/navigation paths; and
- 90 rename-aware generated planning-site entries under `docs/html/**`.

With rename detection disabled, the exact union is **107 paths**:

- six maintained paths; and
- 101 generated paths under `docs/html/**`.

The six maintained paths are exactly:

```text
planning/.vitepress/config.mts
planning/HANDOFF.md
planning/README.md
planning/k3-kvm0-plan.md
planning/project-orientation.md
planning/roadmap.md
```

| Deliverable | Paths | Purpose | Trust or privilege boundary | Primary human question |
| --- | --- | --- | --- | --- |
| K0-A plan correction | `planning/k3-kvm0-plan.md` | Preserve the first proposal, define K0-A, close the five findings, and keep the qualification profile and stop rules bounded | Planning text only; no source checkout, target runtime, board state, evidence result, or accepted R8 byte changed | Do the five corrections remove ambiguity without granting implementation or execution authority? |
| Controlling gates and current position | `planning/README.md`, `planning/roadmap.md`, `planning/project-orientation.md` | Make K0-P/K0-I/K0-S/K0-X/K0-R independently visible; split destination tooling, source build/selftest readiness, native execution, and result review; state the fixed three-session/48-case profile | Maintained status documentation only | Are the decision sequence, exact matrix, and non-authorization boundaries consistent and complete? |
| Operational handoff | `planning/HANDOFF.md` | At target-review time, record the superseded original proposal, proposed K0-A status, five unresolved gates, discovery-only live facts, and exact non-authorization | Handoff text only; no source repository or K3 host access occurred | Could a returning owner resume without treating discovery, a packet, or plan acceptance as authority to act? |
| Planning navigation | `planning/.vitepress/config.mts` | At target-review time, label the plan as K0-A proposed and the first packet as superseded historical review support | Navigation only; no browser-checker behavior changed in the plan target | Did navigation distinguish the current proposal from the historical first packet? |
| Generated planning site | `docs/html/**` | Render the authoritative Markdown and navigation | Generated derivative; Markdown remains authoritative and independent generated-byte reproducibility remains open | Does the rendered site preserve the corrected gates, findings, and claim limits? |

Reproduce the complete exact inventory with:

```sh
git diff --name-status -M \
  8348b18a2c00c992e8fbf744f2004dfcd55500e6 \
  5227266ceddb664a1595e22e5a92da57a013652f
git diff --name-only --no-renames \
  8348b18a2c00c992e8fbf744f2004dfcd55500e6 \
  5227266ceddb664a1595e22e5a92da57a013652f
```

The target changes no file under `model/`, `include/`, `virt/`, `arch/`,
`tests/r0/` through `tests/r8/`, root `Makefile`, `be`,
`scripts/check-be.sh`, `package.json`, `package-lock.json`,
`pathfinder/publication-gate.conf`, `pathfinder/docs/`, the private source
repository, or the K3 host. It changes no dependency, predecessor acceptance
pin, accepted R0-R8 mechanism/profile byte, or publication configuration.

## 3. Claim boundary

### What the exact target and separate decision record support saying

- K0-A is an exact immutable plan revision at
  `5227266ceddb664a1595e22e5a92da57a013652f`; the separate decision record
  above records its responsible-human acceptance on 2026-09-25.
- The first plan and packet are preserved as superseded, unaccepted exact
  objects; no commit was amended or rewritten.
- Report hashing is cycle-free: the report names its entry in
  `checksums.sha256`, that checksum file hashes every other retained member
  but not itself, and the completed archive digest exists only in an external
  approval/import record.
- KVM0-B implementation paths and KVM0-G documentation/review paths are
  separately finite. KVM0-G includes only the two KVM0 result Markdown files,
  four maintained status/HANDOFF pages, planning navigation, the shared
  planning-page browser inventory, and generated `docs/html/**`.
- K0-P, K0-I, K0-S, K0-X, and K0-R are separate. Plan acceptance can satisfy
  only K0-P.
- The fixed execution proposal is exactly three attended native boot
  sessions, one exact 16-command KVM selftest set per session, and C01-C08
  plus N01-N08 per session, totaling three selftest-suite runs and 48 guest
  cases.
- Reported direct KVM evidence is untracked; exact live FDT and initramfs
  hashes are missing; the board is reported back on Fedora control kernel
  `7.1.5-201.0.riscv64.omni.fc44.riscv64`.
- Externally supplied live facts — `CoM260 IFX`, eight X100 harts, `H`,
  `Sv39x4`, `VMID14`, `AIA7`, built-in KVM, user-openable `/dev/kvm`, and
  QEMU `10.2.2` — remain uncommitted, non-evidentiary, not a Beryllium run,
  and not retained R8 evidence.
- Ordinary provenance uses stable opaque identifiers. A complete hash-bound
  human-readable mapping remains in a separate restricted artifact through
  K0-R and is excluded from ordinary reports and publication-safe exports.
- Accepted H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` remains immutable, blocked, and
  not exit-ready; KVM0 resolves no H0 row and authorizes no R8 successor.

### Trusted or assumed

- The externally supplied discovery facts are accurately transcribed, but
  they remain unverified and non-evidentiary.
- Git commit, tree, path, mode, rename, diff, and containment semantics behave
  as used for the exact inventory.
- VitePress, Node.js, Chromium, Graphviz, and the repository documentation
  checkers behave as exercised by the validation record.
- HMAC-SHA-256 and SHA-256 provide the intended opaque identifier and
  integrity properties when a future implementation follows the plan.
- A future source owner can provide the complete restricted provenance map,
  immutable manifests, exact selftest commands, firmware identities, live
  FDT/initramfs hashes, and evidence package required by K0-S.
- Human review will decide whether the pseudonym construction, KVM0-G path
  inventory, three-session profile, one approved selftest skip, and retention
  limits are proportionate.

### Evidence unavailable or `NOT RUN`

- At packet preparation no accepted KVM0 plan existed. The decision record
  above now accepts the exact K0-A plan only; it adds no implementation,
  execution, result, or hardware evidence.
- No K0-I destination tooling implementation or exact implementation base
  exists.
- No K0-S source-owner build/evidence authorization, clean source target,
  approved immutable bundle, exact selftest list, restricted provenance map,
  live FDT hash, live initramfs hash, or complete firmware provenance exists
  in this repository.
- No K0-X board authorization or K3 boot, reset, power, serial, selftest,
  guest, recovery, or report execution occurred.
- No KVM0 result commit exists, so K0-R is blocked.
- KVM0, Beryllium K3, and R8 hardware remain `NOT-RUN`.
- Generated documentation is functionally checked but is not claimed
  byte-reproducible across independent builds.

### What the target does not implement, prove, or authorize

- No KVM0 importer, schema checker, report generator, mutation test, source
  build, host image, QEMU build, guest build, or evidence bundle.
- No Beryllium runtime, Linux integration, B0, B1, H0 successor, H1-H4,
  device, DMA, multicore, service, policy, capability, TE, CHERI, VBS,
  attestation, or development-kernel/BSP selection.
- No KVM, Linux, QEMU, firmware, guest, board, security, isolation,
  correctness, performance, reliability, production, certification, or
  formal-verification result.
- No source access, K3 access, push, tag, publication, release, migration, or
  upstream submission.

## 4. Security and correctness invariants

These are plan obligations, not implemented or observed properties.

| Invariant | Contract in the exact target | Future enforcement or evidence point | Current status |
| --- | --- | --- | --- |
| Digest graph is acyclic | `Cycle-free digest order`; deterministic-report identity fields | Report omits its digest; checksum file omits itself; external record binds checksum file and final archive | Defined; no implementation exists |
| Path authority is finite | `Proposed destination path boundary`; separate KVM0-B and KVM0-G inventories | Exact base/relation and changed-path/mode checker | Defined; every implementation/review path remains unauthorized |
| Decisions cannot collapse | `Status and authority`; K0-P/K0-I/K0-S/K0-X/K0-R sections | Separate exact human decisions and readiness evidence | Preserved; only K0-P is currently requestable |
| Qualification shape is fixed | Objective, ordered phases, selftest and guest-matrix sections | Three sessions, three selftest-suite runs, 48 ordered guest cases | Planned only |
| Discovery cannot become evidence silently | Discovery tables and K0-S stop rules | Immutable source/bundle, exact live hashes, complete manifests, repeated authorized execution | Current live facts remain discovery only |
| Provenance is retained without public identity leakage | `Provenance identity and privacy`; privacy/redaction rules | Opaque IDs, restricted map, hash/size binding, coverage checks, publication export rejection | Defined; no map or bundle exists |
| Accepted R8 bytes and claims remain immutable | Relationship to H0/R8-C; prohibited paths and operations | Exact path inventory and Git object audit | Preserved by target |
| Board control remains human-only | Board/boot/serial and recovery contracts | Exact K0-X profile, output-only serial, no automated reboot/reset/power/input | No board action occurred |
| Failure cannot become PASS through retry | Negative-path and recovery contracts | First failure ends session; remaining cases `NOT-RUN`; recovery is safety-only | Planned only |
| Publication remains human-controlled | LLM policy reference, prohibited operations, non-claims | Exact later human review and publication gates | Blocked |

## 5. Review history and resolved findings

### Superseded first proposal

Original plan target `459184dd8fe9c5da20e27a9e277a076685a520cb`
and first packet commit `8348b18a2c00c992e8fbf744f2004dfcd55500e6`
remain immutable, unaccepted history. K0-A is a new child commit, not an
amendment. No plan decision is inferred for either target.

### Five material findings and K0-A resolutions

| Finding | Resolution in exact K0-A target | Status |
| --- | --- | --- |
| **HIGH — self-referential report digest** | The report records only the checksum-manifest path and its own entry path. `checksums.sha256` is generated afterward and omits itself. The final archive digest is computed last and recorded only outside the archive. The plan also forbids any member from embedding the checksum-file or archive digest. | Closed in plan text |
| **HIGH — path whitelist cannot complete documentation/review** | KVM0-B now contains only destination tooling. KVM0-G separately enumerates `planning/k3-kvm0-evidence.md`, `planning/k3-kvm0-review-summary.md`, `planning/README.md`, `planning/HANDOFF.md`, `planning/project-orientation.md`, `planning/roadmap.md`, `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs`, and generated `docs/html/**`, with explicit purpose limits and exclusions. | Closed in plan text |
| **HIGH — inconsistent authorization surfaces** | `planning/README.md` now controls K0-P/K0-I/K0-S/K0-X/K0-R separately. Roadmap and orientation split destination implementation, source-owner build/selftest readiness, native execution, and result review; both state three sessions, three selftest runs, and 48 guest cases. `planning/HANDOFF.md` carries the same proposed status and blocks. | Closed across maintained surfaces |
| **MEDIUM — incomplete discovery transcription** | The plan records untracked direct KVM evidence, missing live FDT/initramfs hashes, the Fedora control kernel, and all supplied CoM260/X100/H/Sv39x4/VMID14/AIA7/KVM/`/dev/kvm`/QEMU facts as externally supplied, uncommitted, non-evidentiary, not a Beryllium run, and not retained R8 evidence. | Closed in plan text |
| **MEDIUM — provenance/privacy conflict** | Ordinary manifests and reports use stable opaque HMAC-derived identifiers. A complete human-readable mapping and profile key live only in a restricted, hash-bound, access-controlled artifact retained through K0-R and excluded from ordinary bundles/publication. Upstream identities may be referenced by immutable commit/signature object without copying names. Missing mapping coverage blocks K0-S/K0-X. | Closed in plan text |

### Validation bookkeeping finding

After all exact-target documentation commands passed, the first local
post-gate status classifier omitted generated Helium SVG paths from its
generated-file allowlist and therefore exited nonzero. No source or validation
gate failed. A corrected read-only classification found exactly:

```text
planning_html_drift=80
helium_html_drift=26
helium_svg_drift=5
maintained_source_drift=0
```

This confirms the existing generated-asset byte-reproducibility limitation;
it is not a K0-A source defect and does not support a byte-identical
independent-regeneration claim.

### Open questions for human judgment

- Is the exact cycle-free digest order sufficiently simple and auditable?
- Is the KVM0-G documentation/review inventory complete without including an
  unrelated planning or root documentation surface?
- Are K0-I and K0-S correctly separated when destination tooling and
  source-owner build/selftest preparation may be performed by different
  owners?
- Is the fixed three-session, three-selftest-run, 48-case profile strong
  enough and still bounded?
- Is the HMAC-derived profile-local identifier scheme proportionate, and is
  retaining the restricted map through K0-R sufficient?
- Should the reported control kernel or any supplied live fact require a
  further plan revision rather than later exact K0-X authorization if it
  changes?
- Is functional documentation validation sufficient while generated-byte
  reproducibility remains unresolved?

## 6. Validation and retained evidence

Validation date: **2026-09-25**.

### Pre-commit content

| Command or check | Boundary | Result |
| --- | --- | --- |
| Starting Git verification | Clean `beryllium/single-hart-runtime-r0` at first packet commit `8348b18a2c00c992e8fbf744f2004dfcd55500e6`, two commits ahead of the last-fetched upstream | PASS |
| `git diff --check` | Maintained K0-A sources before generation and staged exact content | PASS |
| Exact changed-path whitelist | Six maintained planning/current-position/navigation paths plus generated `docs/html/**` only | PASS; no runtime, accepted R8, dependency, pin, root-integration, publication-gate, source-repository, or K3-host path |
| `npm run docs:build` | Pre-commit authoritative Markdown/navigation | PASS with VitePress 1.6.4; planning diagrams and site generated |
| `node docs/check-links.mjs` | Generated planning site | PASS: 71 Markdown sources, 72 HTML pages, no broken local targets |
| `node --check pathfinder/tests/check-docs-render.mjs` | Shared browser inventory source, unchanged by target | PASS |

### Exact clean K0-A plan commit

The exact target was validated from a fresh detached worktree. Before any
validation command:

```text
HEAD=5227266ceddb664a1595e22e5a92da57a013652f
PARENT=8348b18a2c00c992e8fbf744f2004dfcd55500e6
TREE=2a716a0ca69a7d0ada92b978bd77704fbfc8910b
STATUS=clean detached HEAD
```

| Command or check | Exact boundary | Result |
| --- | --- | --- |
| `git diff --check HEAD^ HEAD` | Exact immutable target | PASS |
| Exact target path inventory | Exact immutable target | PASS: 96 rename-aware entries; six maintained paths; 90 rename-aware generated entries; 107 no-rename paths; no forbidden path |
| `npm ci --no-audit --no-fund` | Exact detached target and pinned dependency closure | PASS |
| `npm run docs:build` | Exact detached target | PASS |
| `node docs/check-links.mjs` | Exact detached planning output | PASS: 71 Markdown sources, 72 HTML pages, no broken local targets |
| `node --check pathfinder/tests/check-docs-render.mjs` | Exact detached browser inventory source | PASS |
| `HE_CHROMIUM=$(command -v chromium-headless-shell) ./be docs-check` | Exact detached target | PASS: complete planning and Helium source/link, HTTP browser, and direct-file browser gates; Chromium `150.0.7871.186`; Helium reported 12 sources, 13 HTML pages, and 12 rendered pages |
| Post-gate status audit | Same exact detached worktree after validation | Generated-only drift: 80 planning HTML, 26 Helium HTML, and five Helium SVG paths; zero maintained source drift |

The worktree began clean at the exact target, so these results support the
target's functional documentation behavior. They do **not** establish
byte-identical generated assets across independent builds. The detached
validation worktree was removed after the boundary was recorded.

No command accessed the private source repository or K3 host. No KVM0,
Beryllium, or R8 hardware command was run.

## 7. Recommended human review sequence

Create an isolated detached worktree:

```sh
git worktree add --detach \
  ../beryllium-kvm0-k0a-plan-review \
  5227266ceddb664a1595e22e5a92da57a013652f
cd ../beryllium-kvm0-k0a-plan-review
git status --short
git show --no-patch --format=fuller \
  5227266ceddb664a1595e22e5a92da57a013652f
git rev-parse HEAD HEAD^ HEAD^{tree}
```

1. Verify exact identity and inventory:

   ```sh
   git diff --check \
     8348b18a2c00c992e8fbf744f2004dfcd55500e6 \
     5227266ceddb664a1595e22e5a92da57a013652f
   git diff --name-status -M \
     8348b18a2c00c992e8fbf744f2004dfcd55500e6 \
     5227266ceddb664a1595e22e5a92da57a013652f
   ```

2. Read `Status and authority` and `Plan revision K0-A`. Confirm that the
   first plan/packet remain unaccepted history and K0-A grants no authority.
3. Review `Cycle-free digest order` together with deterministic reporting and
   retained-artifact rules. Confirm that no report, checksum file, manifest,
   or archive hashes itself directly or indirectly.
4. Review `Proposed destination path boundary`. Confirm that KVM0-B and
   KVM0-G are finite, separate, and exclude runtime, accepted R8, root
   integration, dependencies, pins, publication configuration, and unrelated
   documentation.
5. Review K0-P/K0-I/K0-S/K0-X/K0-R in the plan, planning index, roadmap,
   orientation, and HANDOFF. Confirm that build/selftest preparation and
   native execution are not combined.
6. Review the discovery tables. Confirm that every live fact and missing hash
   remains externally supplied, uncommitted, non-evidentiary, and outside
   Beryllium/R8 claims.
7. Review `Provenance identity and privacy`. Confirm that ordinary artifacts
   remain pseudonymous while the restricted mapping preserves complete,
   auditable provenance and has an explicit retention/publication boundary.
8. Review the fixed selftest/matrix, safety, negative-path, recovery, claim,
   non-claim, and stop rules.
9. Optionally reproduce the functional documentation gates:

   ```sh
   npm ci --no-audit --no-fund
   npm run docs:build
   node docs/check-links.mjs
   HE_CHROMIUM=$(command -v chromium-headless-shell) ./be docs-check
   ```

   Expect functional PASS. Generated planning and Helium derivatives may
   become dirty afterward; that is the recorded open reproducibility finding.

Remove the review worktree afterward:

```sh
cd ..
git worktree remove --force beryllium-kvm0-k0a-plan-review
```

## 8. Human decision checklist

### Technical review

- [ ] The exact target is
      `5227266ceddb664a1595e22e5a92da57a013652f` over parent
      `8348b18a2c00c992e8fbf744f2004dfcd55500e6`, tree
      `2a716a0ca69a7d0ada92b978bd77704fbfc8910b`.
- [ ] Original target `459184dd8fe9c5da20e27a9e277a076685a520cb`
      and first packet commit `8348b18a2c00c992e8fbf744f2004dfcd55500e6`
      remain immutable, superseded, and unaccepted.
- [ ] The target is planning/documentation only and changes no accepted
      R0-R8, runtime, proof, source-repository, K3-host, dependency,
      root-integration, acceptance-pin, or publication-gate path.
- [ ] Report/checksum/archive hashing is exact, cycle-free, and fail closed.
- [ ] KVM0-B implementation and KVM0-G documentation/review inventories are
      separately complete and minimal.
- [ ] K0-P, K0-I, K0-S, K0-X, and K0-R remain separate, and broad
      authorization cannot collapse them.
- [ ] The three-session, three-selftest-run, 48-case matrix is accurate and
      proportionate.
- [ ] The supplied CoM260/X100/H/Sv39x4/VMID14/AIA7/KVM/`/dev/kvm`/QEMU and
      Fedora control-kernel facts remain discovery only.
- [ ] Untracked direct KVM evidence and missing live FDT/initramfs hashes
      correctly block K0-S/K0-X.
- [ ] Ordinary provenance is privacy-preserving without silently discarding
      source-owner, patch-author, committer, or signer accountability.
- [ ] The restricted provenance map's access, hash binding, retention,
      deletion, and publication exclusions are acceptable.
- [ ] Claims match evidence, trust assumptions are acceptable, and unavailable
      evidence remains explicit.
- [ ] Safety, negative-path, privacy, redaction, recovery, and stop rules cover
      the important failure paths without a success-shaped fallback.
- [ ] Accepted H0/R8-C bytes and claims remain unchanged; KVM0 cannot become
      retained R8 evidence without a separately reviewed successor relation.
- [ ] KVM0 implementation, source preparation, execution, result acceptance,
      B0/B1, H0 successor, H1-H4, BSP selection, push, tag, publication, and
      release remain excluded.

### Decision

- [x] **Decision:** accept exact K0-A plan commit
      `5227266ceddb664a1595e22e5a92da57a013652f` /
      ~~request revisions~~ / ~~defer~~.

Only the decision box above is checked because that decision was explicitly
supplied by the responsible human on 2026-09-25. The technical-review boxes
remain unchecked as retained pre-decision review history. No signature is
generated.

## 9. After the decision

### Recorded outcome: the exact K0-A plan is accepted

Exact K0-A plan target `5227266ceddb664a1595e22e5a92da57a013652f`
(parent `8348b18a2c00c992e8fbf744f2004dfcd55500e6`, tree
`2a716a0ca69a7d0ada92b978bd77704fbfc8910b`) was accepted on 2026-09-25 by
the exact instruction quoted above. Packet commit
`6369804904eb28554c65886db93f0d30be80fcab` and this acceptance-record
follow-up are decision support, not plan text, implementation, execution, or
result evidence.

The original plan target `459184dd8fe9c5da20e27a9e277a076685a520cb`
and first packet `8348b18a2c00c992e8fbf744f2004dfcd55500e6` remain
superseded and unaccepted. The accepted K0-A target remains immutable, and its
pre-decision fields remain historical target content rather than current
status.

### Prohibited until separate authorization or evidence

- No K0-I destination tooling or checker update.
- No K0-S source preparation, source-owner build/selftest work, evidence
  import, or private source-repository write.
- No K0-X K3 access, boot, reset, serial, native execution, or recovery.
- No K0-R result acceptance or KVM0 PASS claim.
- No B0, B1, H0 successor, R8 H1-H4, Linux, service, device, DMA, multicore,
  policy, TE, CHERI, VBS, attestation, or later successor work.
- No development-kernel/BSP selection, root integration, dependency change,
  acceptance-pin refresh, acceptance checker, or `be status` change.
- No push, tag, publication, clean-repository migration, release, upstream
  work, or `pathfinder/publication-gate.conf` change.
- No claim that K0-P resolves an accepted H0 row or supplies Beryllium/R8
  hardware evidence.

### Not taken: request revisions

Had revisions been requested, a new exact plan target and packet would have
been required, and K0-A would not have been treated as accepted.

### Not taken: defer

Had review been deferred, K0-A would have remained proposed, K0-P would have
remained pending, and every later gate would have remained blocked.

---

**Status at the K0-A decision:** exact K0-A plan target
`5227266ceddb664a1595e22e5a92da57a013652f` (parent
`8348b18a2c00c992e8fbf744f2004dfcd55500e6`, tree
`2a716a0ca69a7d0ada92b978bd77704fbfc8910b`) is **accepted** as of
2026-09-25. The immutable target retains its pre-decision fields. At that
decision, K0-P was satisfied; K0-I, K0-S, K0-X, and K0-R were blocked; KVM0,
Beryllium K3, and R8 hardware were `NOT-RUN`; no H0 row was resolved; the
development kernel/BSP was `UNDECIDED`; and publication was blocked.

**Next at the K0-A decision:** no implementation, source, execution, result,
successor, hardware, integration, or publication action was authorized by
this record. Each remained behind its separate gate.

**Action required at the K0-A decision:** none. K0-A plan acceptance was
recorded exactly; all later KVM0 and project gates remained blocked.

## 2026-09-26 K0-I current-status addendum

The responsible human later accepted exact K0-I destination-side
offline-tooling target `abd092a1f2734c720a205803c29496fe2245b0ef` (parent
`d490183d0177a5ba38276c572685f0c2e4ee3863`, tree
`f683c1b634e8cd07ba967960d9e00ef2c6a76efa`) on September 26, 2026, by the
exact instruction
`accept exact target abd092a1f2734c720a205803c29496fe2245b0ef`.

The authoritative implementation decision is recorded in
[KVM0 K0-I implementation review and acceptance record](k3-kvm0-k0i-review-summary.md).
Its authorized base is
`e4e0209f19596e0cbccbb6bb4de84c50bbd11f92`; accepted K0-A plan target
`5227266ceddb664a1595e22e5a92da57a013652f` and all K0-P history above remain
unchanged.

This addendum updates current status only. K0-I acceptance covers the exact
ten-path destination offline-tooling package and grants no K0-S, K0-X, K0-R,
K0-G, K3/private-source access, hardware, integration, dependency/pin,
B0/B1/R8-successor, persistent Fedora guest, push, tag, publication, release,
migration, or upstream authority. KVM0 and all Beryllium/R8 K3 hardware
results remain `NOT-RUN`.

```text
kvm0_gate_k0p=satisfied-by-exact-plan-acceptance
kvm0_gate_k0i=satisfied-by-explicit-authorization
kvm0_k0i_scope=offline-tooling-only
kvm0_k0i_implementation=accepted
kvm0_k0i_authorized_base=e4e0209f19596e0cbccbb6bb4de84c50bbd11f92
kvm0_k0i_accepted_target=abd092a1f2734c720a205803c29496fe2245b0ef
kvm0_k0i_accepted_parent=d490183d0177a5ba38276c572685f0c2e4ee3863
kvm0_k0i_accepted_tree=f683c1b634e8cd07ba967960d9e00ef2c6a76efa
kvm0_k0i_acceptance_date=2026-09-26
kvm0_k0i_review_record=planning/k3-kvm0-k0i-review-summary.md
kvm0_gate_k0s=blocked-source-evidence-not-ready
kvm0_gate_k0x=blocked-not-authorized
kvm0_gate_k0r=blocked-no-result
kvm0_result=NOT-RUN
beryllium_k3_hardware=NOT-RUN
r8_k3_hardware=NOT-RUN
development_kernel_bsp=UNDECIDED
publication=blocked
```

## 2026-09-28 K0-S current-status addendum

The responsible human later supplied the exact instruction
`Fleet deployed: proceed with K0-S per above` at
`2026-09-28T00:17:59.413Z`. The separate
[K0-S source-owner preparation authorization-record draft](k3-kvm0-k0s-authorization-record.md)
records that instruction under accepted K0-A target
`5227266ceddb664a1595e22e5a92da57a013652f` while preserving accepted K0-I
target `abd092a1f2734c720a205803c29496fe2245b0ef` as a separate destination
offline-tooling boundary.

The private locator for `k0s-source-owner-workspace-1` was supplied at
`2026-09-28T02:06:12.937Z` and is intentionally omitted under the accepted
privacy rule; `continue` followed at
`2026-09-28T02:07:09.427Z`, and `if repairable, proceed to repair` followed
at `2026-09-28T03:15:09.437Z`. Read-only audit, bounded repair, and
current-byte documentation integration are complete for mutable external
package `k0s-source-owner-profile-v1`: 35 files / 41 inventory paths,
34-entry `SHA256SUMS`, complete 43-of-43 restricted mapping coverage,
controller self-hash preflight, and 25 host-only fake tests pass. Restricted
provenance remains exact-minimum, access-controlled, hash-bound,
publication-excluded, and not printed. The K0-S record remains
draft/not-reviewed with no exact documentation target. Candidate containment
is zero checked local branches and zero checked tags, the current authorized
checkout is unrelated, and no clean immutable referenced source target
exists. It remains an unaccepted/unretained preparation input, not rejected
source. The future K0-I literals `branch_label=main` and
`source-ready-not-run` do not state current K0-S readiness. No source import,
destination install, selftest/K0-X execution, readiness, result, hardware,
BSP, successor, publication, or release authority follows.

```text
kvm0_gate_k0p=satisfied-by-exact-plan-acceptance
kvm0_gate_k0i=satisfied-by-explicit-authorization
kvm0_gate_k0s=authorization-satisfied-local-preparation-recorded-readiness-not-met
kvm0_k0s_authorization=authorized-by-session-instruction
kvm0_k0s_authorization_timestamp=2026-09-28T00:17:59.413Z
kvm0_k0s_authorization_record_status=draft-not-reviewed
kvm0_k0s_documentation_target=none
kvm0_k0s_source_workspace_id=k0s-source-owner-workspace-1
kvm0_k0s_source_workspace_locator_disposition=responsible-human-supplied-private-session-local-not-retained-in-committed-documentation
kvm0_k0s_source_workspace_supplied_at=2026-09-28T02:06:12.937Z
kvm0_k0s_source_preparation=completed-local-profile-package-current-bytes-not-reviewed
kvm0_k0s_source_import=not-performed
kvm0_k0s_profile_package_id=k0s-source-owner-profile-v1
kvm0_k0s_profile_package_inventory=35-files-41-paths
kvm0_k0s_profile_package_sha256sums_entries=34
kvm0_k0s_profile_package_restricted_mapping_coverage=complete-43-of-43
kvm0_k0s_profile_controller_self_hash_preflight=PASS
kvm0_k0s_profile_host_only_fake_tests=PASS-25
kvm0_k0s_destination_import=NOT-RUN
kvm0_k0s_destination_install=NOT-RUN
kvm0_k0s_selftests=NOT-RUN
kvm0_k0s_readiness=not-ready
kvm0_k0s_future_k0i_source_branch_label_literal=main
kvm0_k0s_future_k0i_not_run_profile_state_literal=source-ready-not-run
kvm0_k0s_future_k0i_literals_are_current_readiness=no
kvm0_k0s_candidate_ref_status=unreferenced-object
kvm0_k0s_candidate_containing_checked_local_branches=0
kvm0_k0s_candidate_containing_checked_tags=0
kvm0_k0s_authorized_checkout_relation=unrelated-to-discovery-candidate
kvm0_k0s_clean_immutable_referenced_source_target=none
kvm0_gate_k0x=blocked-not-authorized
kvm0_gate_k0r=blocked-no-result
kvm0_result=NOT-RUN
beryllium_k3_hardware=NOT-RUN
r8_k3_hardware=NOT-RUN
development_kernel_bsp=UNDECIDED
publication=blocked
```
