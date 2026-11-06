<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# KVM0 K0-S source-owner preparation review and acceptance record

This document began as the decision-neutral responsible-human review packet
for exact KVM0 K0-S preparation/status target
`c65705582c243dd908ff47d3189df07601167400`, whose immediate parent is
`478d5886e8dc261546e3373421e0ab428062f82a` and whose Git tree is
`a3f1f74c42d2c583aae8c6aa486f1f97f5379439`. It now also records the
responsible-human decision on that exact target. The target remains byte
unchanged.

Packet commit `d3499c3a7cd4b339fd5f24b145a651844a72d672` is the direct
child of the target and remains decision support. Neither the packet nor this
documentation-only acceptance-record follow-up is the accepted target,
source-owner source, an external package, readiness evidence, execution
evidence, or a KVM0 result.

Except where a statement is explicitly marked current or post-decision,
sections 1 through 8 preserve the target-review history and target-time
evidence boundary.

## Decision record

The responsible human accepted exact target
`c65705582c243dd908ff47d3189df07601167400` on September 29, 2026, by the
exact instruction:

```text
accept c65705582c243dd908ff47d3189df07601167400
```

Acceptance covers only the accuracy of that immutable target as a bounded
K0-S preparation/status documentation record. It does not make K0-S ready or
complete and does not accept source candidate
`c1c7e254143f99d4ad3cdbf25021a76364d6d75a`, the external package's current
or target-time bytes, an immutable route, a bundle, artifacts, missing inputs,
destination import or installation, real selftests, serial, K0-X, K0-R,
B0/B1, R8 successors/H1-H4, hardware, a development kernel/BSP, publication,
push, tag, or release.

The immutable target's `draft-not-reviewed`,
`kvm0_k0s_documentation_target=none`, old package hashes, and comparable
pre-decision fields remain frozen target-time evidence. Current acceptance is
carried by this later review and acceptance record, not by rewriting those
bytes.

The external package has evolved outside Git since the target. Those later
mutable bytes are not accepted by this decision. A later separate
responsible-human route decision selected an exact-Git-target direction, but
the route implementation remains blocked before protected private-ref
containment is proven; the external package therefore remains fail-closed at
its current route-neutral/unselected implementation state. That later route
decision and all later package work are separate from this acceptance and do
not alter its boundary.

Current decision status is:

```text
kvm0_k0s_documentation_target=c65705582c243dd908ff47d3189df07601167400
kvm0_k0s_documentation_parent=478d5886e8dc261546e3373421e0ab428062f82a
kvm0_k0s_documentation_tree=a3f1f74c42d2c583aae8c6aa486f1f97f5379439
kvm0_k0s_documentation_target_status=accepted
kvm0_k0s_acceptance_date=2026-09-29
kvm0_k0s_acceptance_instruction=accept-c65705582c243dd908ff47d3189df07601167400
kvm0_k0s_review_record=planning/k3-kvm0-k0s-review-summary.md
kvm0_k0s_packet_commit=d3499c3a7cd4b339fd5f24b145a651844a72d672
kvm0_k0s_target_frozen_predecision_fields=retained-target-time-evidence
kvm0_k0s_current_external_package=outside-git-mutable-evolved-not-accepted
kvm0_k0s_later_route_decision=separate-exact-git-target-direction
kvm0_k0s_route_implementation=blocked-private-ref-containment-not-proven
kvm0_k0s_current_package_route_state=route-neutral-unselected-fail-closed
kvm0_k0s_readiness=not-ready
kvm0_gate_k0x=blocked-not-authorized
kvm0_gate_k0r=blocked-no-result
kvm0_result=NOT-RUN
beryllium_k3_hardware=NOT-RUN
r8_k3_hardware=NOT-RUN
development_kernel_bsp=UNDECIDED
publication=blocked
```

## 1. Decision summary

| Field | Current value |
| --- | --- |
| Review target | Commit `c65705582c243dd908ff47d3189df07601167400`, parent `478d5886e8dc261546e3373421e0ab428062f82a`, tree `a3f1f74c42d2c583aae8c6aa486f1f97f5379439` |
| Packet | `d3499c3a7cd4b339fd5f24b145a651844a72d672`, direct child of the target; decision support only and not accepted by this decision |
| Current status | Exact target `c65705582c243dd908ff47d3189df07601167400` is responsible-human accepted as an accurate bounded K0-S preparation/status record as of 2026-09-29; K0-S readiness remains not met |
| Decision | Accepted by exact instruction `accept c65705582c243dd908ff47d3189df07601167400` |
| Successor status | K0-S readiness is not met; K0-X, K0-R, K0-G, B0, B1, R8 successors, and H1-H4 are not started or authorized by this target |
| Target containment | At packet preparation the target was local-only; it is now contained by the private tracked branch and remains untagged |
| Publication status | Private internal target and packet; this acceptance-record follow-up is local and unpushed; public push, tag, publication, and release remain blocked |

**Action taken:** the responsible human accepted only exact target
`c65705582c243dd908ff47d3189df07601167400` as the bounded
preparation/status record. No readiness, external-package, source-candidate,
route, import, execution, result, successor, hardware, BSP, or publication
gate is satisfied by that decision.

## 2. Deliverables

| Deliverable | Paths or identity | Purpose and boundary | Highest-value review question |
| --- | --- | --- | --- |
| K0-S authorization and preparation record | `planning/k3-kvm0-k0s-authorization-record.md` | Records the exact September 28, 2026 session authority, privacy-safe workspace/package identifiers, current package hashes, source relation, explicit blockers, and non-authorizations | Does the record interpret `proceed with K0-S per above`, `continue`, and `if repairable, proceed to repair` no more broadly than intended? |
| Maintained current-position integration | `planning/HANDOFF.md`, `planning/README.md`, `planning/glossary.md`, `planning/project-orientation.md`, `planning/roadmap.md` | Keeps the live project position consistent while preserving K0-I as a separate destination-tooling boundary | Are K0-S authorization, preparation, readiness, acceptance, and execution kept visibly separate? |
| Historical decision-record temporalization | `planning/k3-kvm0-plan-k0a-review-summary.md`, `planning/k3-kvm0-k0i-review-summary.md` | Scopes earlier blocked-state statements to the decisions they originally recorded, then adds a later-status addendum without changing accepted target bytes | Do the addenda preserve historical truth without implying that K0-A or K0-I granted K0-S authority? |
| Planning navigation and browser inventory | `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs` | Adds the K0-S record route and exact page title to the maintained planning site and browser gate | Does navigation expose the new record without changing any Helium claim or component boundary? |
| Generated planning site | `docs/html/**`; 102 rename-aware changed entries | Regenerated derivative of the ten maintained source paths; no Helium generated byte belongs to the target | Does generated output correspond to the reviewed Markdown and remain privacy-safe under HTTP and direct-file rendering? |
| External preparation package, not part of the Git target | Stable ID `k0s-source-owner-profile-v1`; 35 files and 41 path/type/mode rows | Non-executing source-owner profile preparation. Current bytes are bound by `FILES.modes`, `SHA256SUMS`, source-profile, and restricted-map hashes, but the package remains outside Git and mutable | Are the current-byte bindings and explicit not-ready status sufficient for a preparation record without being mistaken for immutable K0-S evidence? |

The exact target changes 112 rename-aware Git entries: ten maintained source
paths and 102 generated planning-site entries. No accepted KVM0 plan,
destination implementation, Beryllium runtime, R0-R8 mechanism, proof,
dependency, root integration, or publication-gate byte is changed.

## 3. Claim boundary

Exact target `c65705582c243dd908ff47d3189df07601167400`
supports saying:

- bounded K0-S source-owner preparation was separately authorized by the
  recorded September 28, 2026 session instructions;
- the private source-owner locator was supplied and is represented in
  committed documentation only by stable ID `k0s-source-owner-workspace-1`;
- local profile package `k0s-source-owner-profile-v1` was repaired and
  inspected at these current-byte identities:

  ```text
  files=35
  inventory_rows=41
  FILES.modes_sha256=f8f130dbcbddfa557298bab1a9bcac859a4ec8af8adb219d271e467c52ffa5db
  SHA256SUMS_entries=34
  SHA256SUMS_sha256=57d0753ab55333ca29198d894e176c5a270e52747e29303b6ad1d2bb8cd606b3
  source_profile_sha256=aaa4b83d216cd932fd77c32230dded6ff206f6224224670bcac2169bd5a36238
  restricted_map_mode=0600
  restricted_map_bytes=42570
  restricted_map_sha256=eb734dc9dad08a2ec5e73d4f5b50a4fe59ed9100580dcf0490687dfb2f8943c4
  restricted_mapping_coverage=43-of-43
  ```

- the proposed source relation contains 14 ordered commits and 11 changed
  mode-`100644` paths from base
  `a5f72fd298f6bd02e6d30599dafb43cfa16576b6` to candidate
  `c1c7e254143f99d4ad3cdbf25021a76364d6d75a`, tree
  `a5f77b5acef26d8975fe756512edbd2413fa1239`, parent
  `405a74dd4f1afc793b52f8589ccdcda5ee515f8e`;
- the candidate object is currently contained by zero checked local branches
  and zero checked tags, the authorized checkout is unrelated, and no clean
  immutable referenced source target exists;
- the package's static checks and 25 host-only fake-binary tests pass,
  including direct controller self-tamper rejection before session output,
  intermediate-symlink rejection, per-test and aggregate timeout handling,
  stream bounds, first-failure propagation, and deterministic regeneration;
  and
- maintained and generated planning documentation passes syntax, build, link,
  Chromium responsive, and direct-file checks without adding a private K0-S
  locator or restricted identity.

The target still trusts or assumes:

- the responsible-human session instructions are authentic and correctly
  time-bound;
- the supplied source-owner object database and Git object contents are the
  intended inputs for the recorded read-only audit;
- access control for the mode-`0600` restricted map is maintained outside
  Beryllium;
- the external package remains available at the current inspected bytes until
  the human decision; and
- VitePress, Chromium, Git, Python, and ordinary host utilities used by the
  bounded checks behave according to their observed versions.

Evidence that remains unavailable or `NOT-RUN` includes:

- retained `SUMMARY.tsv` and prior approved-skip output bytes;
- complete operational tool, firmware, artifact, guest-command, live FDT,
  and live initramfs identities;
- destination K0-I import or installation;
- real KVM selftest execution;
- serial endpoint selection, serial access, and output-only proof;
- K3 execution, Beryllium hardware validation, and retained R8 hardware
  evidence; and
- an immutable source ref or responsible-human-approved immutable bundle.

The target explicitly does not implement or claim K0-S readiness, candidate
acceptance, source import, installed runtime behavior, K0-X, K0-R, a KVM0
PASS, B0/B1, an R8 successor, H1-H4, development-kernel/BSP selection,
formal verification, production readiness, push, tag, publication, release,
migration, archival, or upstream submission.

The 2026-09-29 acceptance adds no evidence to that claim boundary. In
particular, the target-time package identities above remain historical
target evidence rather than acceptance of the package's later evolved bytes.
The later route selection and later package work have their own authority and
implementation status and do not retroactively change what this target says.

## 4. Security and correctness invariants

| Invariant | Contract or record | Implementation or data | Test or evidence |
| --- | --- | --- | --- |
| K0-I and K0-S authority remain separate | Accepted `planning/k3-kvm0-plan.md`; target K0-S record sections 1-4 | Maintained status fields use distinct K0-I and K0-S authority keys | Documentation diff review and current-position cross-check |
| Private locators and human provenance do not enter ordinary committed output | Accepted K0-A privacy rule; `LLM_POLICY_ALIGNMENT.md` | Stable IDs in planning; exact-minimum identities and one profile-local key only in the mode-`0600` restricted map | Added-line privacy scans; generated-site privacy scans; complete 43-of-43 ordinary/restricted ID match |
| The prospective controller verifies itself before producing session evidence | Profile install-integrity contract | `bin/k0-selftest-suite-controller` checks the closed 18-entry install manifest and its own bytes before creating a session directory | Direct controller-tamper host-only test; intermediate-symlink tests |
| Runtime profiles fail closed on drift and failure | Accepted K0-A timeout, marker, no-retry, and stop rules | Per-test runner plus suite controller enforce 120-second test and 1,800-second suite limits, 32 MiB stream limits, first-failure stop, and remaining `NOT-RUN` records | 25 fake-binary tests, including timeout, stream, marker, hash, scratch-reuse, and failure propagation cases |
| Candidate cleanliness is not confused with immutable retention | Accepted K0-S gate | Source profile records a clean detached observation separately from zero ref containment and unrelated current checkout | Direct Git-object relation checks; zero containing branches/tags; explicit `not-ready` fields |
| Generated planning documentation derives from maintained Markdown and leaves Helium unchanged | Repository documentation SOP | Isolated `npm run docs:build` output under `docs/html/**` | Link, Chromium, responsive, direct-file, and pre/post Helium byte/status comparisons |

## 5. Review history and resolved findings

The following substantive findings were discovered and closed before target
creation:

1. **Stale authorization status.** The first draft still said no workspace had
   been supplied and preparation had not started. The record now binds the
   exact instruction timeline while omitting the private locator.
2. **Dummy restricted provenance.** The prospective package initially claimed
   complete mapping with dummy role records. It now retains exact-minimum
   human provenance only in the mode-`0600` restricted map, uses one captured
   profile-local key, and binds complete 43-of-43 ordinary/restricted
   coverage without printing restricted content.
3. **Private absolute paths in committed documentation.** Newly added source
   and package locators were replaced by stable project-local IDs and an
   explicit session-local, non-retained disposition.
4. **Controller self-integrity gap.** The first controller relied on the child
   runner to detect controller tampering after the controller had started.
   The controller now validates its own current bytes before creating output
   or launching the runner.
5. **Intermediate symlink gap.** The runner, controller, and hash freezer now
   reject unsafe intermediate install components, not only a symlinked root
   or leaf.
6. **Unreferenced candidate not recorded.** The source profile and planning
   record now state that no checked local branch or tag contains the candidate
   and that the current checkout is unrelated.
7. **Out-of-scope Helium generated drift.** Five deterministic diagram-layout
   changes and related Helium generated assets existed before this target.
   They remain unstaged and absent from commit
   `c65705582c243dd908ff47d3189df07601167400`. The packet-validation
   `./be docs-check` run passed, but regenerated Helium's known unstable
   hashed asset names. The exact retained pre-check Helium baseline was then
   restored byte-for-byte and status-for-status before packet staging.
8. **Stale README label.** The final package README still called the restricted
   map dummy after remediation. The label was corrected to exact-minimum, the
   package checksum inventory was refreshed, and all dependent planning
   hashes and generated pages were rebuilt.

The following questions were presented for responsible-human review:

- Is accepting a Git target that records hash-bound but mutable external
  preparation bytes useful at this stage, provided acceptance is explicitly
  limited to status accuracy?
- Is the exact interpretation of the recorded session authority correct?
- Should the next source-owner step preserve or recreate the candidate under a
  reviewed immutable ref, or prepare a separately approved immutable bundle?
- Are the minimum restricted provenance fields and retention boundary
  acceptable?

The supplied acceptance resolves only whether the exact target is an accurate
bounded preparation/status record. It does not answer those questions for
later package bytes, route implementation, readiness, execution, or a result.

## 6. Validation and retained evidence

The following commands passed on September 28, 2026:

| Command or check | Evidence boundary |
| --- | --- |
| `./tests/run-tests.sh` in `k0s-source-owner-profile-v1` | Deterministic generation, static/schema/mode/inventory/checksum checks, and 25 host-only fake-binary tests; no real KVM, serial, board, or hardware path |
| `sha256sum --quiet -c SHA256SUMS` | Strict current-package checksum closure over 34 entries |
| Direct safe metadata assertions | Restricted map mode `0600`, 43-of-43 ID coverage, non-dummy retained key, zero candidate branches/tags, and absent immutable ref; restricted content was not printed |
| `git diff --check` and JS/TS syntax checks | Maintained source formatting and syntax |
| `npm run docs:build` | Isolated planning diagram and direct-file planning-site generation |
| `npm run docs:build:http` | HTTP-served planning-site generation used by browser checks |
| `node docs/check-links.mjs` | Target content: 74 Markdown sources and 75 HTML pages; packet integration: 75 Markdown sources and 76 HTML pages; no broken local targets |
| `node pathfinder/tests/check-docs-render.mjs planning` | Target content: 74 planning pages; packet integration: 75 planning pages in Chromium, including responsive and direct-file K0-S rendering |
| `./be docs-check` | Full planning and Helium build, link, HTTP, browser, and direct-file gates passed; the exact pre-check Helium generated baseline was restored afterward because the open asset-reproducibility defect changed hashed filenames |
| Added-line and generated-site privacy scans | No newly introduced private K0-S locator, private URL, restricted identity, retained key, stale checksum, or old test count |
| Pre/post Helium status and SHA-256 manifests | Existing `pathfinder/docs/html/**` and `pathfinder/docs/public/diagrams/**` bytes and status remained unchanged |

These checks ran on the byte-identical staged tree immediately before commit
`c65705582c243dd908ff47d3189df07601167400`. After commit, the target paths
were clean with zero untracked target paths. The target itself contains the
generated planning output and its exact tree is
`a3f1f74c42d2c583aae8c6aa486f1f97f5379439`.

Repository-wide `make check`, R8 checks, KVM selftests, K0-X, hardware, and
publication checks were not used as target evidence. The current host has
known pinned-tool drift for the accepted R8 launcher; that unrelated
environmental failure does not validate or invalidate this documentation and
fake-only K0-S target.

### Acceptance-record follow-up boundary

The documentation-only acceptance-record follow-up is validated separately
with `git diff --check`, JavaScript/TypeScript syntax checks,
`npm run docs:build`, the planning link checker, the complete planning
HTTP/direct-file/responsive browser gate, and root `./be docs-check`.
Pre/post manifests bind the retained Helium generated bytes and Git status;
if root documentation validation changes those known nondeterministic assets,
the exact pre-check state is restored and rechecked before commit.

Those commands validate only this decision/status documentation, navigation,
browser-title inventory, generated planning HTML, and privacy boundary. They
do not rerun or extend target
`c65705582c243dd908ff47d3189df07601167400`, validate the external package's
later bytes, prove the separately selected route, establish K0-S readiness,
or supply import, selftest, serial, K3, hardware, result, successor, BSP, or
publication evidence.

Validation date: **2026-09-29**.

| Command or check | Follow-up result and boundary |
| --- | --- |
| `git diff --check`; `node --check pathfinder/tests/check-docs-render.mjs`; `node --check planning/.vitepress/config.mts` | PASS for the maintained acceptance-record sources |
| Exact target inventory and mode audit | PASS: 112 rename-aware target entries, comprising ten maintained paths and 102 generated planning-site entries; all ten maintained target paths are mode `100644` |
| `npm run docs:build` and `npm run docs:build:http` | PASS with VitePress 1.6.4 and the maintained planning diagrams |
| `node docs/check-links.mjs` | PASS: 75 Markdown sources, 76 HTML pages, no broken local targets |
| `HE_CHROMIUM=/usr/lib64/chromium-browser/headless_shell node pathfinder/tests/check-docs-render.mjs planning` | PASS: 75 planning pages under Chromium `153.0.8010.36`, including HTTP, direct-file, desktop, and mobile/responsive checks; two intrinsic-overflow pages were recorded by the passing gate |
| `HE_CHROMIUM=/usr/lib64/chromium-browser/headless_shell ./be docs-check` | PASS: complete planning and Helium source generation, links, HTTP rendering, direct-file rendering, and responsive browser gates; Helium reported 12 sources, 13 HTML pages, 12 rendered pages, and zero intrinsic-overflow pages |
| Added-line privacy and scope audit | PASS: no added private absolute path, URL, SSH locator, credential/key marker, human `Signed-off-by`, or publication-gate change; changed maintained scope is the review record, five current-position sources, navigation, and the shared planning-title inventory |
| Pre/post Helium generated-state proof | PASS after restoring known nondeterministic assets: 71 generated files matched the pre-check SHA-256 manifest `f205ea882f4d55336c24fb4022e39d85c897bbc238f0a416b8c5d5479ec9aa04`, mode manifest `bf0049dc46da5d127ac643407f6c6eb09066e1439943a28d94da244528faad7f`, and empty status SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## 7. Recommended later audit sequence

1. Inspect the exact target identity and finite source inventory:

   ```sh
   git show --no-ext-diff --stat --summary \
     c65705582c243dd908ff47d3189df07601167400
   git diff --no-ext-diff --name-status -M \
     478d5886e8dc261546e3373421e0ab428062f82a \
     c65705582c243dd908ff47d3189df07601167400
   ```

2. Review the authority and claim boundary first:

   ```sh
   git show \
     c65705582c243dd908ff47d3189df07601167400:planning/k3-kvm0-k0s-authorization-record.md
   git diff \
     478d5886e8dc261546e3373421e0ab428062f82a \
     c65705582c243dd908ff47d3189df07601167400 \
     -- planning/roadmap.md planning/HANDOFF.md planning/README.md
   ```

3. Review historical temporalization and ensure no earlier decision is
   widened:

   ```sh
   git diff \
     478d5886e8dc261546e3373421e0ab428062f82a \
     c65705582c243dd908ff47d3189df07601167400 \
     -- planning/k3-kvm0-plan-k0a-review-summary.md \
        planning/k3-kvm0-k0i-review-summary.md
   ```

4. At the responsible-human-supplied private package locator, verify the exact
   current-byte identities without printing restricted content:

   ```sh
   sha256sum FILES.modes SHA256SUMS source-profile-v1.json \
     restricted/provenance-map-v1.json
   sha256sum --quiet -c SHA256SUMS
   stat -c '%a %s %n' restricted/provenance-map-v1.json
   ./tests/run-tests.sh
   ```

5. If independent documentation validation is desired, use an isolated
   detached worktree:

   ```sh
   git worktree add --detach ../be-k0s-review \
     c65705582c243dd908ff47d3189df07601167400
   cd ../be-k0s-review
   npm ci
   npm run docs:build
   npm run docs:build:http
   node docs/check-links.mjs
   node pathfinder/tests/check-docs-render.mjs planning
   ```

6. Confirm that the recorded acceptance remains limited to the exact target's
   preparation/status record and does not approve K0-S readiness or later
   work.

## 8. Human decision checklist

- [ ] The exact target and parent are correct.
- [ ] The ten maintained source paths and generated planning-site changes are
      within the intended K0-S documentation/status scope.
- [ ] The session instructions are interpreted no more broadly than intended.
- [ ] K0-I destination tooling and K0-S source-owner authority remain separate.
- [ ] The target's claims match the package hashes, source relation, and
      host-only test evidence.
- [ ] The mutable external-package assumption is acceptable for a status
      record and is not mistaken for immutable K0-S evidence.
- [ ] The restricted provenance boundary and privacy treatment are acceptable.
- [ ] Important negative paths are covered by the 25 fake-only tests.
- [ ] Real selftests, serial, hardware, K0-X, K0-R, successors, and publication
      remain excluded.

### Recorded decision

- [x] **Accept** exact commit
      `c65705582c243dd908ff47d3189df07601167400` on 2026-09-29 by the
      responsible-human instruction
      `accept c65705582c243dd908ff47d3189df07601167400`.
- [ ] Request revisions and require a new exact target and record.
- [ ] Defer and preserve the prior unaccepted state.

Only the acceptance-decision box is checked because the responsible human
explicitly supplied that decision. The technical-review boxes remain
unchecked as retained review history. No signature or human `Signed-off-by`
is generated.

## 9. After the decision

### Recorded outcome: exact bounded status target accepted

Exact target `c65705582c243dd908ff47d3189df07601167400` (parent
`478d5886e8dc261546e3373421e0ab428062f82a`, tree
`a3f1f74c42d2c583aae8c6aa486f1f97f5379439`) was accepted on 2026-09-29
by the exact instruction quoted above. Packet commit
`d3499c3a7cd4b339fd5f24b145a651844a72d672` and this acceptance-record
follow-up are decision support, not accepted target content.

The target remains immutable. Its internal draft status, absent documentation
target, old package hashes, zero-ref observation, and other pre-decision
fields remain accurate target-time evidence. This record carries the later
decision without rewriting them.

### Current external-package and route boundary

The external package has since evolved outside Git and remains mutable. No
current package byte, archive, bundle, artifact, missing input, or restricted
content is accepted here. The later exact-Git-target route selection is a
separate responsible-human decision. Its implementation remains blocked
before protected private-ref containment is proven, so the package remains
route-neutral/unselected and fail-closed at current implementation status.
No actual route completion, source-candidate acceptance, destination import,
installation, real selftest, serial, or hardware action follows from this
record.

### Unchanged gates and non-authorizations

- K0-S remains not ready and not complete.
- Source candidate `c1c7e254143f99d4ad3cdbf25021a76364d6d75a` remains
  unaccepted.
- No immutable route, bundle, artifact set, or missing input is accepted.
- Destination import/install, real selftests, serial, K0-X, K0-R, and KVM0
  result evidence remain `NOT-RUN`, blocked, or unauthorized.
- B0/B1, development-kernel/BSP selection, R8 successors/H1-H4, root
  integration, dependencies, pins, Linux, devices, DMA, multicore, policy,
  and later project work remain separately gated.
- K3/Beryllium/R8 hardware remain `NOT-RUN`; the development kernel/BSP
  remains `UNDECIDED`.
- Push, tag, publication, release, migration, archival, and upstream
  submission remain blocked.

Had revisions been requested, a new target and packet would have been
required. Had review been deferred, this target would have remained
unaccepted. Neither alternative occurred.

**Status:** exact K0-S preparation/status target
`c65705582c243dd908ff47d3189df07601167400` is responsible-human accepted
as of 2026-09-29, only as an accurate bounded documentation target. K0-S is
still not ready or complete; KVM0 and all Beryllium/R8 K3 hardware remain
`NOT-RUN`.

**Next:** preserve the exact accepted target and continue only separately
authorized route/readiness work from its own current implementation state.
Do not advance to K0-X.

**Action required from you:** none for this recorded acceptance. Any route
completion, readiness, import, execution, result, successor, BSP, hardware,
push, tag, publication, or release action still requires its own satisfied
gate and exact authority.
