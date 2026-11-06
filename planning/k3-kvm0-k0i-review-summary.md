<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# KVM0 K0-I implementation review and acceptance record

This is the authoritative review and acceptance record for exact KVM0 K0-I
implementation target `abd092a1f2734c720a205803c29496fe2245b0ef`, whose
immediate parent is `d490183d0177a5ba38276c572685f0c2e4ee3863` and whose Git
tree is `f683c1b634e8cd07ba967960d9e00ef2c6a76efa`.

The accepted implementation relation begins at authorized base
`e4e0209f19596e0cbccbb6bb4de84c50bbd11f92` under accepted KVM0 Plan
revision K0-A target `5227266ceddb664a1595e22e5a92da57a013652f`. Prior
implementation candidates `1795400868c6d6cb3a6a9fed8ce069424c7bc2ef` and
`d490183d0177a5ba38276c572685f0c2e4ee3863` are preserved as superseded,
unaccepted candidates. They are implementation ancestry, not separately
accepted targets.

## Decision record

The responsible human accepted exact K0-I implementation target
`abd092a1f2734c720a205803c29496fe2245b0ef` on September 26, 2026, by the
exact instruction:

```text
accept exact target abd092a1f2734c720a205803c29496fe2245b0ef
```

Acceptance covers **K0-I destination-side offline tooling only**. It applies
to the exact immutable target named above and the cumulative ten-path
implementation it carries from the authorized base. It does not separately
accept either prior candidate.

This documentation-only acceptance-record follow-up, its maintained status
updates, and its generated `docs/html/**` derivatives are decision support.
They are not implementation, imported evidence, result bytes, a KVM0
qualification result, Beryllium or R8 hardware evidence, or a successor
authorization.

Status recorded by this K0-I decision before the later K0-S authorization was:

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

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact K0-I implementation commit `abd092a1f2734c720a205803c29496fe2245b0ef` (`tests: bind KVM0 retained host evidence`), tree `f683c1b634e8cd07ba967960d9e00ef2c6a76efa` |
| Parent | `d490183d0177a5ba38276c572685f0c2e4ee3863` (`tests: harden KVM0 evidence validation`), a superseded and unaccepted candidate |
| Authorized base | `e4e0209f19596e0cbccbb6bb4de84c50bbd11f92`, the K0-A acceptance-record commit and exact K0-I implementation base |
| Accepted plan | KVM0 Plan revision K0-A target `5227266ceddb664a1595e22e5a92da57a013652f` |
| Current status | The cumulative ten-path K0-I destination package is implemented, exact-target tested, and responsible-human accepted at exact target `abd092a1f2734c720a205803c29496fe2245b0ef` as of 2026-09-26 |
| Decision | Accepted by exact instruction `accept exact target abd092a1f2734c720a205803c29496fe2245b0ef` |
| Scope | Offline bundle/contract checking, confined import, deterministic report generation, independent report checking, and synthetic negative testing only |
| Prior candidates | `1795400868c6d6cb3a6a9fed8ce069424c7bc2ef` and `d490183d0177a5ba38276c572685f0c2e4ee3863` remain superseded and unaccepted |
| Branch and repository | `beryllium/single-hart-runtime-r0`; private repository `beryllium-project/beryllium-hypervisor` |
| Target containment | At acceptance-record preparation, zero remote-tracking branches and zero tags contained the target; it was local-only and unpushed |
| Successor status | K0-S, K0-X, K0-R, K0-G, B0, B1, R8 successors, and all K3 execution remain blocked or unauthorized |
| Publication status | Push, tag, publication, release, migration, archival, and upstream submission remain blocked |

**Action taken:** the responsible human accepted only exact K0-I target
`abd092a1f2734c720a205803c29496fe2245b0ef`. No later gate is satisfied by
that decision.

## 2. Deliverables and exact inventory

### Cumulative authorized implementation scope

The exact authorized-base-to-target range
`e4e0209f19596e0cbccbb6bb4de84c50bbd11f92..abd092a1f2734c720a205803c29496fe2245b0ef`
adds exactly ten maintained paths, with these exact modes:

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

Git reports 14,617 insertions and no deletions for that complete relation. No
root integration, dependency, accepted-plan, accepted-runtime, checker-pin,
publication-gate, generated-documentation, or private-source path is part of
the implementation range.

### Final corrective delta

The exact parent-to-target corrective delta
`d490183d0177a5ba38276c572685f0c2e4ee3863..abd092a1f2734c720a205803c29496fe2245b0ef`
changes exactly seven regular `100644` paths:

```text
tests/kvm0/README.md
tests/kvm0/check-bundle.mjs
tests/kvm0/check-contract.mjs
tests/kvm0/check-report.mjs
tests/kvm0/generate-report.mjs
tests/kvm0/kvm0-contract-v1.json
tests/kvm0/test-rejections.mjs
```

Git reports 3,016 insertions and 297 deletions for that correction. The
launcher, Make graph, and source-boundary file retain their prior bytes and
modes in the final delta.

| Deliverable | Paths | Purpose | Trust or privilege boundary | Primary review question |
| --- | --- | --- | --- | --- |
| Checked launcher and package graph | `tests/kvm0/run-make.sh`, `tests/kvm0/Makefile` | Authenticate one target, scrub inherited controls, bind absolute tools, close stdin, and confine generated state below `build/kvm0/` | Host-only destination tooling; no board, serial, SSH, network, or private-source access | Can caller environment, Make control, path aliasing, or cleanup escape create a success-shaped run? |
| Closed contract and authority boundary | `tests/kvm0/kvm0-contract-v1.json`, `tests/kvm0/kvm0-source-boundary-v1.json`, `tests/kvm0/check-contract.mjs` | Bind the accepted plan, authorized base, exact ten-file inventory/modes, schemas, limits, non-claims, tools, and source policy | Declarative and host-side only; no source-owner evidence is supplied | Does every accepted field remain inside K0-I and fail closed on drift? |
| Safe importer | `tests/kvm0/check-bundle.mjs` | Validate and atomically import one explicit evidence directory tree, raw/canonical host streams, firmware bytes, manifests, checksums, evidence closure, and failure ledgers | Consumes only supplied bytes; writes only under `build/kvm0/`; restricted provenance map remains inaccessible | Can malformed, aliased, incomplete, privacy-violating, or drifting input become accepted output? |
| Report derivation and independent checking | `tests/kvm0/generate-report.mjs`, `tests/kvm0/check-report.mjs` | Derive the fixed report without trusting caller outcomes and independently reconstruct its exact semantics | Deterministic host processing only; no result acceptance and no hardware claim | Do generator and checker independently preserve failure, `NOT-RUN`, and evidence identity? |
| Synthetic and negative testing | `tests/kvm0/test-rejections.mjs` | Exercise non-executed, captured-failure, eligible-route test-only, guest-image-envelope, mutation, launcher, and cleanup paths | Fixtures only; cannot produce a supportable KVM0 PASS | Do positive fixtures stay non-claiming and do one-defect mutations fail for the intended reason? |
| Package documentation | `tests/kvm0/README.md` | Explain the exact interfaces, evidence semantics, trust boundary, and non-claims | Descriptive source for the accepted package; not a result record | Does the documentation match the actual closed contract and accepted scope? |

## 3. Claim boundary

### Supported by the exact target

- K0-I implements destination-side offline tooling only: strict contract
  checking, safe confined directory-tree import, deterministic report
  generation, independent report reconstruction, synthetic tests, and a
  bounded rejection suite.
- The package binds accepted plan
  `5227266ceddb664a1595e22e5a92da57a013652f`, authorized base
  `e4e0209f19596e0cbccbb6bb4de84c50bbd11f92`, and the exact ten-path/mode
  inventory above.
- Raw serial and current-boot journal bytes remain authoritative and are
  independently bound to lossless bounded canonical views. Forbidden-marker
  checking scans raw streams, while structured marker and journal facts are
  parsed from checked canonical views.
- Firmware records bind retained regular-file bytes, mode, size, SHA-256,
  artifact identity, source identity, immutability, and opaque provenance.
- Matrix, command, artifact, selftest, host-fact, capture, recovery, and
  result records must close exactly over manifest-declared, checksum-covered
  evidence.
- Generator and checker independently derive the sorted complete failure
  ledger. Missing, extra, duplicate, reordered, or forged reasons are
  rejected.
- The generic future guest-image envelope is identity-only under K0-I:
  execution remains false, outcome and qualification remain `NOT-RUN`, and
  no matrix or result-evidence binding is allowed.
- The exact-Git-target eligible fixture traverses the real source-ready route
  but ends in a fixed test-only terminal failure. No synthetic fixture can
  create a KVM0 PASS or hardware claim.
- The package uses Node.js built-ins only, performs no network, SSH, serial,
  board, private-source, package-manager, or ambient-workspace operation, and
  confines generated bytes below `build/kvm0/`.

### Trusted or assumed

- Git commit, tree, path, mode, link-count, and object semantics behave as
  used by the source-boundary and exact-target checks.
- Node.js 22.22.2 and the eight absolute host tools reported by
  `kvm0-toolcheck` behave as executed.
- JavaScript regular-expression and string-decoding semantics behave as used
  by the source-policy, privacy, marker, and schema checks.
- SHA-256 and the operating system's no-follow descriptor, rename, mode, and
  filesystem identity semantics provide the intended integrity boundary.
- The supplied future K0-S bundle, if one is ever authorized and prepared,
  accurately represents its source-owner evidence before this independent
  destination tooling evaluates it.

### Evidence unavailable or `NOT RUN`

- No immutable K0-S source target or approved immutable evidence bundle is
  supplied or accepted by this target.
- The exact source-owner 16-command selftest set, approved skip, restricted
  provenance map, live FDT/initramfs identities, complete firmware chain,
  host rootfs closure, and exact execution command manifest remain missing
  K0-S inputs.
- No K0-X K3 boot, reset, power, serial, KVM selftest, guest matrix,
  recovery, or hardware execution occurred.
- No K0-R result commit or K0-G evidence/review package exists.
- KVM0 remains `NOT-RUN`; Beryllium K3 hardware remains `NOT-RUN`; R8 K3
  hardware remains `NOT-RUN`; the development kernel/BSP remains
  `UNDECIDED`.

### Explicitly not implemented, accepted, or authorized

- K0-S source-owner build, selftest preparation, evidence capture, evidence
  readiness, or private source-repository access.
- K0-X board access or execution, K0-R result acceptance, or K0-G
  evidence/review integration.
- Any Beryllium runtime, Linux integration, root `Makefile`/`be` integration,
  dependency or acceptance-pin change, accepted-plan edit, or accepted
  R0-R8 mechanism change.
- B0, B1, an H0 successor, R8 H1-H4, persistent Fedora guest qualification,
  devices, DMA, multicore, service, policy, capability, TE, CHERI, VBS, or
  attestation work.
- Any Linux/KVM, QEMU, firmware, guest, board, performance, reliability,
  isolation, correctness, production, formal-verification, certification, or
  hardware result.
- Push, tag, publication, release, migration, archival, upstream submission,
  or publication-gate change.

## 4. Security and correctness invariants

| Invariant | Contract | Implementation | Test or evidence |
| --- | --- | --- | --- |
| Authority is exact and finite | Accepted K0-A plan plus `kvm0-source-boundary-v1.json` | Exact base, plan, ten paths, and modes checked by `check-contract.mjs` | Tool/source/contract gates and Git inventory audit |
| Destination execution is confined | Launcher contract and K0-I no-network boundary | Scrubbed `env -i`, absolute tools, closed stdin, checked physical paths, `build/kvm0/**` writes only | Launcher rejection cases, fresh-root test, and `kvm0-clean` |
| Import is fail closed | Bundle, member, mode, size, checksum, and privacy contracts | No-follow reads, pre/post identity checks, atomic staging and rename | Bundle rejection matrix and exact import round trips |
| Digest order is acyclic | Accepted plan cycle-free digest rule | Report omits self/checksum/archive digests; checksum omits itself; archive identity stays external | Contract checks and checksum/report mutations |
| Host streams are losslessly bound | Raw/canonical capture and journal contracts | Exact raw bytes plus bounded canonical transformation and independent rescans | CRLF, invalid-byte, split-stream, overlap, hidden-hit, and forged-ledger cases |
| Firmware identity is byte-backed | Firmware and artifact manifests | Independent regular-file mode/size/SHA-256 and provenance/artifact linkage | Missing, unmanifested, checksum, size, hash, alias, swap, and superficial-metadata mutations |
| Evidence closure is complete | Command, artifact, matrix, host, capture, selftest, result, and recovery schemas | Every executed observation has exact command-bound, manifest-declared, checksum-covered evidence | Missing stream/path, command mismatch, topology, block, network, host-fact, and recovery mutations |
| Failure cannot become success | Exact deterministic failure ledger | Importer, generator, and checker independently derive complete sorted reasons | Ledger removal, addition, forgery, duplication, and report mutation cases |
| Guest-image scope cannot widen | K0-I guest-image envelope | `executed=false`, `NOT-RUN`, `outside-kvm0`, no matrix/evidence binding | Guest-image execution, identity, and qualification rejection cases |
| Synthetic eligibility cannot claim a result | Test-only profile contract | Eligible route ends with fixed `test-only-terminal-failure` | Self-test reports `claimed-result=NOT-RUN hardware=NOT-RUN` |

## 5. Review history and open observations

### Candidate history

| Candidate | Relation and role | Current disposition |
| --- | --- | --- |
| `1795400868c6d6cb3a6a9fed8ce069424c7bc2ef` | First direct child of authorized base `e4e0209f19596e0cbccbb6bb4de84c50bbd11f92`; introduced the complete ten-path offline package | Superseded and unaccepted |
| `d490183d0177a5ba38276c572685f0c2e4ee3863` | Child of the first candidate; hardened evidence validation and is the immediate parent of the accepted target | Superseded and unaccepted as a standalone candidate |
| `abd092a1f2734c720a205803c29496fe2245b0ef` | Final seven-path correction binding retained host streams, firmware/artifact identity, matrix/evidence closure, deterministic failures, guest-image non-execution, and expanded rejection coverage | Responsible-human accepted on 2026-09-26 |

The prior candidates were not amended or silently promoted. Acceptance names
only the final exact target.

### Open low-severity non-blocking observations

1. **Bare side-effect JavaScript imports.** The source-policy import regex in
   `tests/kvm0/check-contract.mjs` recognizes `from 'pkg'` and dynamic
   `import('pkg')`, but not a bare side-effect form such as `import 'pkg'`.
   The exact accepted target contains zero bare side-effect imports. This is
   a low-severity source-policy coverage gap, not an observed dependency or
   network path in the accepted bytes.
2. **Streaming privacy carry length.** The payload privacy scanner retains
   512 characters of carry between read chunks. A deliberately adversarial
   URL or email pattern spanning a longer boundary could evade that streaming
   match. Realistic leak shapes, parsed manifests, and the derived report
   remain covered. This is a low-severity residual, not evidence of a leak in
   the accepted target or its synthetic fixtures.

Acceptance does not close either observation. A future technical change
requires its own exact target, review, and authority.

## 6. Validation and retained evidence

Validation date: **2026-09-26**.

### Exact implementation target

| Command or check | Exact boundary | Result |
| --- | --- | --- |
| Git identity, ancestry, tree, mode, and cumulative/final inventory audit | Exact target `abd092a1f2734c720a205803c29496fe2245b0ef` | PASS: parent `d490183d0177a5ba38276c572685f0c2e4ee3863`; tree `f683c1b634e8cd07ba967960d9e00ef2c6a76efa`; exact ten-path cumulative inventory and seven-path final delta; `git diff --check` PASS |
| `./tests/kvm0/run-make.sh kvm0-toolcheck` | Exact target in a scrubbed environment | PASS: Node 22.22.2, eight absolute tools, ten source files, zero external dependencies |
| `./tests/kvm0/run-make.sh kvm0-contract-check` | Exact target | PASS: closed contract, accepted plan, authorized base, K0-S blocked, hardware `NOT-RUN` |
| `./tests/kvm0/run-make.sh kvm0-self-test` | Exact target | PASS: 17 imports, 34 generations, 34 independent report checks, byte-identical double generation |
| `./tests/kvm0/run-make.sh kvm0-rejection-test` | Exact target | PASS: 187 rejections - 2 contract, 147 bundle, 29 report, and 9 launcher |
| `./tests/kvm0/run-make.sh kvm0-check` | Exact target | PASS: complete offline package; source readiness blocked and hardware `NOT-RUN` |
| `./tests/kvm0/run-make.sh kvm0-clean` | Exact target | PASS: bounded `build/kvm0` cleanup |
| Fresh detached exact-target validation | Clean detached worktree at the exact target, no pre-existing K0-I build output | PASS: `kvm0-check`, `kvm0-clean`, and final clean Git status |

The self-test and rejection suite cover the raw/canonical host-stream
boundary, firmware byte binding, matrix and evidence closure, complete
deterministic failure ledger, generic guest-image `NOT-RUN` envelope,
eligible-route test-only failure, no-network source boundary, launcher
confinement, and cleanup. No network, SSH, serial, K3, or private source
repository was accessed.

Node.js **22.22.2** executed the target. A direct Node 18 executable was not
available as `node18`, `node-18`, or `/usr/bin/node-18`; no Node 18 direct
execution result is claimed.

Repository-wide `make check` was **not green and is not K0-I acceptance
evidence**. It exited 2 in the unrelated retained R3 tool lock with:

```text
R3 rejects node executable digest drift
```

No K0-I failure was implicated, no retained lock was changed, and this record
does not imply a repository-wide PASS.

### Acceptance-record validation boundary

The documentation-only follow-up must pass `git diff --check`,
`node --check pathfinder/tests/check-docs-render.mjs`,
`npm run docs:build`, `node docs/check-links.mjs`, and
`HE_CHROMIUM="$(command -v chromium-headless-shell)" ./be docs-check`, then
the same documentation/link/browser gates from a fresh detached worktree at
the exact acceptance-record commit. Those checks validate only this
decision/status documentation. They do not rerun, extend, or replace the
accepted K0-I target evidence above.

## 7. Recommended human inspection sequence

The decision is already recorded. For later read-only audit, use an isolated
detached worktree:

```sh
git worktree add --detach \
  ../beryllium-kvm0-k0i-review \
  abd092a1f2734c720a205803c29496fe2245b0ef
cd ../beryllium-kvm0-k0i-review
git status --short
git rev-parse HEAD HEAD^ HEAD^{tree}
```

1. Confirm the authorized-base-to-target ten-path/mode inventory and the
   parent-to-target seven-path corrective delta:

   ```sh
   git diff --name-status \
     e4e0209f19596e0cbccbb6bb4de84c50bbd11f92 \
     abd092a1f2734c720a205803c29496fe2245b0ef
   git diff --name-status \
     d490183d0177a5ba38276c572685f0c2e4ee3863 \
     abd092a1f2734c720a205803c29496fe2245b0ef
   git ls-tree -r \
     abd092a1f2734c720a205803c29496fe2245b0ef -- tests/kvm0
   ```

2. Read the accepted plan's K0-I and KVM0-B boundaries, then
   `tests/kvm0/kvm0-source-boundary-v1.json` and
   `tests/kvm0/kvm0-contract-v1.json`.
3. Review the launcher and Make parse-time controls before the importer.
4. Review raw/canonical host-stream and privacy handling, firmware binding,
   evidence closure, report derivation, and independent checking.
5. Review the complete synthetic and rejection suite, including both open
   low-severity observations above.
6. Re-run the exact package gate in a scrubbed environment:

   ```sh
   /usr/bin/env -i \
     PATH=/usr/bin \
     SHELL=/bin/bash \
     HOME="$HOME" \
     ./tests/kvm0/run-make.sh kvm0-check
   /usr/bin/env -i \
     PATH=/usr/bin \
     SHELL=/bin/bash \
     HOME="$HOME" \
     ./tests/kvm0/run-make.sh kvm0-clean
   ```

Remove the disposable worktree afterward.

## 8. Human decision checklist

### Technical review history

- [ ] The exact target, parent, tree, authorized base, accepted plan, and
      ten-path/mode inventory are correct.
- [ ] The final seven-path corrective delta closes the intended retained
      host-evidence boundary without widening K0-I.
- [ ] Claims match the exact host-only test evidence and preserve all
      `NOT-RUN`, blocked, and non-claim states.
- [ ] Import, report, failure, privacy, firmware, evidence-closure, launcher,
      and cleanup trust boundaries are acceptable.
- [ ] The two low-severity non-blocking observations are accurately retained.
- [ ] The important positive and negative paths are covered without a
      success-shaped fallback.
- [ ] K0-S, K0-X, K0-R, K0-G, K3/private-source access, root integration,
      successors, persistent Fedora guest qualification, and publication
      remain excluded.

### Decision

- [x] **Accept** exact K0-I implementation target
      `abd092a1f2734c720a205803c29496fe2245b0ef` on 2026-09-26 by explicit
      responsible-human instruction
      `accept exact target abd092a1f2734c720a205803c29496fe2245b0ef`.
- [ ] Request revisions and require a new exact target and record.
- [ ] Defer and preserve the prior unaccepted state.

Only the acceptance-decision box is checked because the responsible human
explicitly supplied that decision. The technical-review boxes remain
unchecked as retained review history. No signature or human
`Signed-off-by` is generated.

## 9. Recorded decision and remaining boundaries

- **Recorded acceptance.** Acceptance applies only to exact K0-I target
  `abd092a1f2734c720a205803c29496fe2245b0ef`, parent
  `d490183d0177a5ba38276c572685f0c2e4ee3863`, tree
  `f683c1b634e8cd07ba967960d9e00ef2c6a76efa`, under authorized base
  `e4e0209f19596e0cbccbb6bb4de84c50bbd11f92` and accepted plan
  `5227266ceddb664a1595e22e5a92da57a013652f`.
- **Prior candidates.** `1795400868c6d6cb3a6a9fed8ce069424c7bc2ef`
  and `d490183d0177a5ba38276c572685f0c2e4ee3863` remain superseded and
  unaccepted. Their ancestry in the final target is not separate acceptance.
- **Decision support.** This acceptance-record follow-up and generated
  documentation are not implementation, imported evidence, or result bytes.
- **Evidence boundary.** Acceptance adds no source-owner evidence, execution,
  result, K3, Beryllium hardware, R8 hardware, formal, or publication
  evidence. The package's host-only tests remain the exact evidence class.
- **Open observations.** The bare side-effect import-regex gap and 512-character
  privacy carry residual remain open, low severity, and non-blocking for the
  accepted exact target.
- **No later authority at the K0-I decision.** K0-S, K0-X, K0-R, K0-G, B0,
  B1, R8 successors,
  H1-H4, K3/private-source access, hardware execution, root integration,
  dependencies, pins, persistent Fedora guest qualification, push, tag,
  publication, release, migration, archival, and upstream remain blocked or
  unauthorized.

---

**Status at the K0-I decision:** exact K0-I destination-side offline-tooling target
`abd092a1f2734c720a205803c29496fe2245b0ef` is responsible-human accepted
as of 2026-09-26. At that decision, K0-P and K0-I were satisfied at their
exact boundaries; K0-S, K0-X, and K0-R were blocked; KVM0 and all K3 hardware
results were `NOT-RUN`; the development kernel/BSP was `UNDECIDED`; and
publication was blocked.

**Next at the K0-I decision:** no later KVM0 phase or project successor was
authorized by this record. The next KVM0 gate was K0-S source-owner evidence
readiness under a separate explicit decision and exact evidence relation.

**Action required from you:** none for this recorded K0-I decision.

## 2026-09-28 K0-S current-status addendum

The responsible human later supplied the exact instruction
`Fleet deployed: proceed with K0-S per above` at
`2026-09-28T00:17:59.413Z`. The separate
[K0-S source-owner preparation authorization-record draft](k3-kvm0-k0s-authorization-record.md)
records that instruction under accepted K0-A plan target
`5227266ceddb664a1595e22e5a92da57a013652f` while preserving this record's
accepted K0-I target `abd092a1f2734c720a205803c29496fe2245b0ef` as a separate
destination offline-tooling boundary.

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
publication-excluded, and not printed. These instructions and checks do not
alter the accepted K0-I bytes or evidence, authorize source import,
destination install, selftest/K0-X execution, or make K0-S ready or complete.
The K0-S documentation record remains draft/not-reviewed with no exact
target. Candidate containment is zero checked local branches and zero checked
tags, the current authorized checkout is unrelated, and no clean immutable
referenced source target exists. It remains an unaccepted/unretained
preparation input, not rejected source. The accepted K0-I literals
`branch_label=main` and `source-ready-not-run` remain future import/report
contract values rather than current readiness.

K0-X, K0-R, K0-G, K3 execution, B0/B1, R8 successors/H1-H4, root
integration, BSP selection, push, tag, publication, release, migration, and
upstream work remain blocked or unauthorized. KVM0 and all Beryllium/R8 K3
hardware results remain `NOT-RUN`.
