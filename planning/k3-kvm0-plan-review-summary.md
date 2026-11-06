<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 Linux/KVM qualification plan (KVM0) responsible-human review summary

This is the decision-neutral responsible-human review packet for exact
planning target `459184dd8fe9c5da20e27a9e277a076685a520cb`, whose immediate
parent is `80345e18df94eb9e58b1b7861b3f12856832b1b2` and whose Git tree is
`834e8f6c961469d7756c8278597e822da7e60f2f`.

The target proposes one bounded Linux/KVM qualification plan for the K3
CoM260. It is not a KVM0 implementation, execution, or result; it is not a
Beryllium hardware run; and it records no responsible-human decision.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact planning commit `459184dd8fe9c5da20e27a9e277a076685a520cb` (`docs: propose bounded K3 KVM0 qualification plan`), tree `834e8f6c961469d7756c8278597e822da7e60f2f` |
| Parent / comparison base | `80345e18df94eb9e58b1b7861b3f12856832b1b2` (`docs: clarify source header identity scope`) |
| Branch and repository | `beryllium/single-hart-runtime-r0`; private repository `beryllium-project/beryllium-hypervisor` |
| Target publication state | Local-only, unpushed, and untagged at packet preparation; zero remote branches and zero tags contain the target |
| Current status | Plan source, directly related current-position sources, navigation, browser inventory, and generated planning HTML are committed and documentation-tested. The plan remains `proposed-not-reviewed`; implementation and execution remain `not-authorized`; result and hardware state remain `NOT-RUN` |
| Source evidence caveat | The private source discovery is not an immutable evidence target: reported source `main` HEAD `796862989c06762a1bf18acda6d56dbdb913c930` had 10 tracked modifications and 36 untracked entries, no root `COLLAB.md`, and no direct KVM result in HEAD |
| Decision requested | Accept exact plan commit `459184dd8fe9c5da20e27a9e277a076685a520cb`, request revisions, or defer |
| Successor status | No destination checker implementation, source-owner build, K3 execution, KVM0 result, B0, B1, H0 successor, or R8 H1-H4 work is authorized or started |
| Hardware state | KVM0 `NOT-RUN`; Beryllium K3 `NOT-RUN`; R8 hardware `NOT-RUN` |
| Publication status | Push, tag, publication, release, clean-repository migration, upstream submission, and any `pathfinder/publication-gate.conf` change remain blocked |

**Action expected from the responsible human:** choose only whether to accept
this exact plan commit, request revisions, or defer. Plan acceptance would not
authorize implementation or execution.

## 2. Deliverables and exact inventory

With rename detection, the exact parent-to-target delta contains **91 changed
entries**:

- 76 modified entries;
- five added entries;
- one deleted entry;
- nine renamed entries;
- six maintained planning/navigation/browser-inventory paths; and
- 85 generated planning-site entries under `docs/html/**`.

The six maintained paths are exactly:

```text
pathfinder/tests/check-docs-render.mjs
planning/.vitepress/config.mts
planning/README.md
planning/k3-kvm0-plan.md
planning/project-orientation.md
planning/roadmap.md
```

| Deliverable | Paths | Purpose | Trust or privilege boundary | Primary human question |
| --- | --- | --- | --- | --- |
| Bounded KVM0 plan | `planning/k3-kvm0-plan.md` | Define the source-evidence gate, fixed three-boot qualification profile, 16-test selftest contract, two eight-case matrices per boot, capture/privacy/recovery rules, deterministic report, stop rules, and explicit non-claims | Planning text only; no source repository, K3 host, target runtime, result, or board state changed | Is the plan exact enough to review and safe enough to accept without granting implementation or execution authority? |
| Current-position integration | `planning/project-orientation.md`, `planning/roadmap.md`, `planning/README.md` | Replace stale “no plan exists” wording with an exact proposed-plan status while preserving all authorization, H0, R8, BSP, hardware, and publication blocks | Documentation only | Do the maintained status pages distinguish a proposed plan from acceptance, implementation authority, execution, result, and hardware evidence? |
| Navigation and browser inventory | `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs` | Add the KVM0 plan to the generated planning site and mandatory browser/direct-file page inventory | Documentation tooling only; no Helium claim or behavior change | Is the one-page planning integration complete without widening implementation scope? |
| Generated planning site | 85 exact entries under `docs/html/**` | Render the source plan and updated status/navigation | Derivative and non-authoritative; generated-byte reproducibility remains an open repository finding | Does the rendered plan preserve status, tables, links, and claim boundaries? |

Reproduce the complete exact inventory with:

```sh
git diff --name-status -M \
  80345e18df94eb9e58b1b7861b3f12856832b1b2 \
  459184dd8fe9c5da20e27a9e277a076685a520cb
```

The target changes no file under `model/`, `include/`, `virt/`, `arch/`,
`tests/r0/` through `tests/r8/`, `pathfinder/publication-gate.conf`, the
private source repository, or the K3 host.

## 3. Claim boundary

### What the exact target supports saying

- A bounded KVM0 plan exists at exact commit
  `459184dd8fe9c5da20e27a9e277a076685a520cb`.
- KVM0 is defined as a Linux KVM qualification result on one exact K3 CoM260
  profile, separate from Beryllium R8 H0-H4 and separate from a Beryllium
  hardware run.
- Accepted H0/R8-C target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` remains immutable, blocked, and
  not exit-ready; KVM0 cannot resolve its rows or authorize H1-H4.
- The plan requires one immutable source-owner Git target or one explicitly
  approved immutable bundle before imported Linux/KVM results can count.
- The current private source discovery is recorded only as dirty,
  non-importable discovery, including its candidate source/artifact facts and
  explicit evidence gaps.
- The proposed qualification profile contains exactly three attended native
  boot sessions, one exact 16-test selftest set per session, compatibility
  cases C01-C08, native cases N01-N08, and 48 total guest cases.
- Automation may never reboot, power-cycle, physically reset, flash, or send
  serial-console input. Physical reset or recovery is attended, human-only,
  and separately authorized.
- Destination offline tooling may consume only supplied artifacts, use no
  network/SSH/serial, and write only below `build/kvm0/`.
- The plan defines exact provenance, command-manifest, privacy, serial
  capture, negative-path, recovery, retention, deterministic-report, claim,
  and non-claim contracts.

### Trusted or assumed

- The discovery facts supplied to the planning task are accurately
  transcribed, but they remain unverified and non-evidentiary.
- Git commit, tree, path, mode, and diff semantics behave as used for the
  exact target inventory.
- VitePress, Node.js, Chromium, Graphviz, and repository documentation
  checkers behave as exercised by the validation record below.
- A future source owner can provide the immutable source, firmware, artifact,
  command, and result manifests the plan requires.
- Human review will decide whether the proposed 48-case profile, one allowed
  selftest skip, 4 GiB bundle cap, and recovery boundary are proportionate.

### Evidence unavailable or `NOT RUN`

- No immutable source-owner evidence target or approved immutable bundle
  exists in this destination repository.
- Exact firmware, U-Boot, OpenSBI/M-mode, command, selftest-name, skip-reason,
  initramfs, guest, and live-board provenance is unavailable.
- No destination-side `tests/kvm0/` tooling exists.
- No source-owner build or evidence package was prepared by this task.
- No K3 boot, reset, power, serial, KVM, selftest, guest, recovery, or report
  execution occurred.
- KVM0, Beryllium K3, and R8 hardware results remain `NOT-RUN`.
- The development kernel/BSP remains `UNDECIDED`.

### What the target does not implement, prove, or authorize

- No Beryllium source or runtime behavior.
- No H0 row resolution, H0 successor, H1-H4, B0, B1, or development-kernel
  selection.
- No Linux/KVM source modification, host image build, QEMU build, guest
  build, board boot, or evidence import.
- No nested virtualization, guest H, endurance, performance, thermal, VFIO,
  DMA, libvirt, UEFI, persistent Fedora guest, secure-boot, attestation,
  production, certification, or formal-verification result.
- No push, tag, publication, release, migration, or upstream authority.

## 4. Security and correctness invariants

These are plan obligations, not implemented or observed properties.

| Invariant | Contract in the target | Future enforcement or evidence point | Current status |
| --- | --- | --- | --- |
| KVM0 remains separate from Beryllium R8 | `Relationship to accepted R8-H0/R8-C`; claim and non-claim sections | Result report must keep Beryllium and R8 hardware `NOT-RUN` and resolve no H0 row | Preserved by planning text; no hardware work occurred |
| Plan acceptance does not authorize action | `Status and authority`; `Decision gates`; `After a plan decision` | Separate K0-I, K0-S, K0-X, and K0-R decisions | Unsatisfied by design |
| Dirty discovery cannot become evidence | `Discovery-only source input`; immutable source-owner evidence contract | Exact clean Git target or approved bundle with complete manifests | Current source discovery remains disqualified |
| Source governance remains read-only | `Cross-repository usage and governance` | No source `COLLAB.md` creation or guest write; destination-only usage report | Preserved |
| Automated board control is forbidden | `Board, boot, and serial safety`; recovery contract | Exact command review, passive output-only capture, attended human actions | No board access occurred |
| Offline checking is confined | `Tool and environment locks`; prohibited operations | Network/SSH/serial disabled, stdin closed, all writes below `build/kvm0/` | No implementation exists |
| Commands are exact structured argv | `Command-manifest contract` | Immutable command-manifest SHA, no shell-string evaluation or ambient environment | Exact commands remain a K0-S/K0-X blocker |
| Qualification shape is fixed | Native boot profile, selftest set, C01-C08 and N01-N08 matrices | Three boot sessions, 15 PASS/one approved SKIP, 48 guest cases | Planned only |
| Failure cannot become a retry-based PASS | Negative-path and recovery contracts | First failure ends the session; remaining cases `NOT-RUN`; recovery is safety-only | Planned only |
| Evidence is bounded and privacy-preserving | Bundle, capture, privacy, retention, and deterministic-report sections | Safe archive import, size limits, redaction ledger, two byte-identical report regenerations | Planned only |
| Kernel/BSP remains unselected | Status, relationship, claim and non-claim sections | Separate later responsible-human decision after a reviewed KVM0 result | `UNDECIDED` |

## 5. Review history and resolved findings

### Planning inputs that forced explicit gates

1. **Dirty private source state.** The reported source `main` HEAD had 10
   tracked modifications and 36 untracked entries. The plan therefore
   requires a clean immutable source target or explicitly approved immutable
   bundle before any result can count.
2. **No source ledger.** The source had no root `COLLAB.md`; the source
   remained read-only and this destination plan carries the bounded usage
   report instead of creating a ledger.
3. **No direct KVM result in source HEAD.** The plan forbids inferring a
   result from candidate artifacts, matrix counts, or source names.
4. **Missing firmware/OpenSBI provenance.** Exact firmware, U-Boot, and
   OpenSBI/M-mode provenance is a hard stop before execution authorization.
5. **In-band reboot failure.** The plan removes in-band reboot from the
   normative procedure and makes every physical reset or recovery attended,
   human-only, and separately authorized.
6. **Evidence-class confusion risk.** KVM0 is explicitly separate from
   accepted H0 and retained R8 so a Linux/KVM PASS cannot become Beryllium
   hardware evidence by implication.

### Documentation validation finding

The first plain `./be docs-check` on pre-commit content passed planning
generation and local-link validation, then stopped because the browser
renderer does not auto-discover the available PATH-local
`chromium-headless-shell`. No dependency was installed or changed. The
documented rerun:

```sh
HE_CHROMIUM=$(command -v chromium-headless-shell) ./be docs-check
```

passed the complete planning and Helium documentation/browser gate. This is
an environment-discovery limitation, not a KVM0 source defect.

### Open generated-asset finding

The exact detached plan target began clean and passed its documentation
commands. After the gate, the disposable worktree contained generated-only
drift:

```text
planning generated paths: 79
Helium generated paths: 31
```

No maintained source path drifted. This reproduces the existing open
generated-asset byte-reproducibility finding. The worktree was removed after
the drift boundary was recorded. Functional exact-target validation is
supportable; byte-identical independent regeneration is not claimed.

### Open questions for human judgment

- Is the proposed three-boot, 48-case matrix sufficiently strong and still
  bounded?
- Is exactly one named and reasoned selftest SKIP acceptable, provided it is
  stable across all sessions?
- Should any source target differing from candidate commit/tree
  `c1c7e254143f99d4ad3cdbf25021a76364d6d75a` /
  `a5f77b5acef26d8975fe756512edbd2413fa1239` force a plan revision, or may a
  later exact execution authorization approve a replacement profile?
- Is the immutable command-manifest gate sufficient even though exact private
  source-side commands are intentionally not invented in this plan?
- Is the output-only serial rule and prohibition on automated reboot/reset
  proportionate to the board risk?
- Are the 4 GiB bundle cap and per-capture/log limits sufficient?
- Are the privacy and redaction rules strong enough without removing required
  `/proc/cmdline`, live FDT, journal, or serial facts?
- Does the plan keep the development kernel/BSP decision sufficiently
  separate from KVM0?

## 6. Validation and retained evidence

Validation date: **2026-09-25**.

### Pre-commit content

| Command or check | Boundary | Result |
| --- | --- | --- |
| Starting Git verification | Clean branch `beryllium/single-hart-runtime-r0` at `80345e18df94eb9e58b1b7861b3f12856832b1b2` | PASS |
| `git diff --check` | Maintained and generated pre-commit content | PASS |
| Exact proposed-path whitelist | Planning sources, browser inventory, and `docs/html/**` only | PASS; no runtime, H0, R0-R7, source-repository, K3, or publication-gate path |
| `node --check pathfinder/tests/check-docs-render.mjs` | Browser inventory source | PASS |
| `npm run docs:build` | Pre-commit source content | PASS; VitePress 1.6.4, 70 planning Markdown sources |
| Plain `./be docs-check` | Pre-commit source content | Source/link build PASS; browser phase stopped only because Chromium was not auto-discovered |
| `HE_CHROMIUM=$(command -v chromium-headless-shell) ./be docs-check` | Pre-commit source content | PASS: 70 planning pages and 12 Helium pages rendered through Chromium `150.0.7871.186`; link and direct-file gates passed |
| Staged inventory and `git diff --cached --check` | Content committed as exact target | PASS: 91 entries, six maintained paths, 85 generated planning paths |

### Exact clean plan commit

The exact target was validated from a fresh detached worktree. Before any
validation command:

```text
HEAD=459184dd8fe9c5da20e27a9e277a076685a520cb
TREE=834e8f6c961469d7756c8278597e822da7e60f2f
STATUS=clean detached HEAD
```

| Command or check | Exact boundary | Result |
| --- | --- | --- |
| `git diff --check HEAD^ HEAD` | Exact immutable target | PASS |
| Exact target path whitelist | Exact immutable target | PASS: only six maintained planning/navigation paths and `docs/html/**` |
| `npm ci` | Exact detached target | PASS; pinned dependency closure installed. npm reported five existing audit findings (three moderate, two high); no manifest or dependency change was made |
| `npm run docs:build` | Exact detached target | PASS |
| `HE_CHROMIUM=$(command -v chromium-headless-shell) ./be docs-check` | Exact detached target | PASS: 70 planning pages, 12 Helium pages, link checks, HTTP rendering, and direct-file rendering |
| Post-gate status audit | Exact detached target after validation | Generated-only drift: 79 planning and 31 Helium paths; no maintained source drift |

These commands validate the exact target's functional documentation behavior
because the worktree began clean at that exact commit. They do not establish
byte-reproducible generated assets across independent builds.

No command accessed the private source repository or K3 host. No KVM0,
Beryllium, or R8 hardware command was run.

## 7. Recommended human review sequence

Create an isolated detached worktree:

```sh
git worktree add --detach \
  ../beryllium-kvm0-plan-review \
  459184dd8fe9c5da20e27a9e277a076685a520cb
cd ../beryllium-kvm0-plan-review
git status --short
git show --no-patch --format=fuller \
  459184dd8fe9c5da20e27a9e277a076685a520cb
git rev-parse HEAD HEAD^ HEAD^{tree}
```

1. Verify exact identity and inventory:

   ```sh
   git diff --check \
     80345e18df94eb9e58b1b7861b3f12856832b1b2 \
     459184dd8fe9c5da20e27a9e277a076685a520cb
   git diff --name-status -M \
     80345e18df94eb9e58b1b7861b3f12856832b1b2 \
     459184dd8fe9c5da20e27a9e277a076685a520cb
   ```

2. Read `Status and authority`, `Relationship to accepted R8-H0/R8-C`, and
   `Objective`. Confirm that plan acceptance cannot authorize action.
3. Review `Discovery-only source input` and
   `Cross-repository usage and governance`. Confirm that the dirty private
   source and absent ledger are handled without promoting discovery.
4. Review the K0-P/K0-I/K0-S/K0-X/K0-R gates, immutable source/bundle
   contract, source/artifact provenance, and exact command-manifest rules.
5. Review board/serial safety, capture, privacy, and recovery. Confirm that
   automation can neither control reset/power nor write serial.
6. Review the 16-test selftest contract, C01-C08 and N01-N08 matrices,
   repeats, timeouts, markers, expected exits, block/network semantics, and
   first-failure behavior.
7. Review retained artifacts, report fields, supportable future claim, and
   explicit non-claims.
8. Confirm that accepted H0 remains untouched and no development kernel/BSP
   is selected.
9. Optionally reproduce the functional documentation gates:

   ```sh
   npm ci
   npm run docs:build
   HE_CHROMIUM=$(command -v chromium-headless-shell) ./be docs-check
   ```

   Expect functional PASS. Generated planning and Helium assets may become
   dirty afterward; that is the recorded open reproducibility finding.

Remove the review worktree afterward:

```sh
cd ..
git worktree remove --force beryllium-kvm0-plan-review
```

## 8. Human decision checklist

### Technical review

- [ ] The exact target is
      `459184dd8fe9c5da20e27a9e277a076685a520cb` over parent
      `80345e18df94eb9e58b1b7861b3f12856832b1b2`.
- [ ] The target is planning/documentation only and changes no accepted H0,
      R0-R7, runtime, proof, source-repository, K3-host, dependency, root
      integration, or publication-gate path.
- [ ] KVM0 is correctly separated from Beryllium R8 and cannot resolve H0 or
      authorize H1-H4.
- [ ] Plan acceptance, destination implementation, source-owner preparation,
      K3 execution, and result acceptance remain separate gates.
- [ ] The dirty private source state and absent source `COLLAB.md` are handled
      conservatively and without a source write.
- [ ] The immutable Git-target or approved-bundle import contract is complete
      and fail closed.
- [ ] Missing firmware/U-Boot/OpenSBI provenance correctly blocks execution.
- [ ] The exact-command manifest requirement is acceptable even though
      private source-side argv is not invented in the plan.
- [ ] Three native boot sessions, three selftest-suite runs, and 48 guest
      cases are proportionate and sufficiently bounded.
- [ ] The one approved selftest SKIP rule is explicit enough to prevent
      success-shaped omission.
- [ ] PLIC, AIA/APLIC/IMSIC, 1/2/8-vCPU, block, restricted user networking,
      compatibility CPU, and native CPU coverage are adequate.
- [ ] Guest H remains absent and nested virtualization remains excluded.
- [ ] Automation is correctly forbidden from reboot, power-cycle, reset,
      flash, and serial-console input.
- [ ] Offline tooling is correctly confined to supplied artifacts and
      `build/kvm0/` without network, SSH, or serial.
- [ ] Capture, privacy, redaction, retention, negative-path, recovery, and
      deterministic-report rules preserve failures and required facts.
- [ ] The plan's supportable claim and non-claims match the proposed evidence.
- [ ] K3 and Beryllium hardware remain `NOT-RUN`, no H0 row is resolved, and
      the development kernel/BSP remains `UNDECIDED`.
- [ ] Implementation, execution, B0, B1, H0 successor, H1-H4, push,
      publication, and release remain excluded.

### Decision

- [ ] **Accept** exact KVM0 plan commit
      `459184dd8fe9c5da20e27a9e277a076685a520cb`.
- [ ] **Request revisions** and require a new exact plan target and packet.
- [ ] **Defer** review and preserve every current block.

No box is checked. This packet records no decision and generates no signature.

## 9. After the decision

### If the exact plan is accepted

- Record acceptance of exact commit
  `459184dd8fe9c5da20e27a9e277a076685a520cb` and date in a later
  responsible-human decision record.
- Leave the immutable target byte unchanged.
- Keep KVM0 implementation and execution `not-authorized`.
- Require separate K0-I, K0-S, and K0-X decisions before any implementation,
  source-owner preparation, import, or K3 action.
- Keep B0, B1, H0 successor, H1-H4, BSP selection, push, publication, and
  release blocked.

### If revisions are requested

- Create a new exact plan commit and new review packet.
- Preserve this target as superseded and unaccepted.
- Do not start implementation or execution.

### If review is deferred

- Preserve `proposed-not-reviewed`, `not-authorized`, and `NOT-RUN`.
- Do not change source, K3, H0, R8, BSP, successor, or publication state.

---

**Status:** exact KVM0 plan target
`459184dd8fe9c5da20e27a9e277a076685a520cb` is committed, documentation-tested,
local-only, unpushed, untagged, and **proposed-not-reviewed**. KVM0
implementation and execution are **not authorized**. KVM0, Beryllium K3, and
R8 hardware are `NOT-RUN`; no H0 row is resolved; the development kernel/BSP
is `UNDECIDED`.

**Next:** the responsible human may accept this exact plan commit, request
revisions, or defer. No other decision is requested by this packet.

**Action required from you:** select exactly one of those three plan-review
outcomes. Acceptance of the plan alone will not authorize implementation or
execution.
