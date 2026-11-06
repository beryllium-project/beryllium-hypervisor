<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R8-H0/R8-C review and acceptance record

This document began as the decision-neutral responsible-human review packet
for exact implementation target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`, whose immediate parent is the
R8-C acceptance-record commit
`d18b1c9c6ca8a0f2285f820ec960258620ae4b50`. The target is exactly one clean
non-merge child of that base and has Git tree
`7a9d80d08d0abb771d43cf76a4a297d9d668b375`. The review material below is
retained as the evidence and decision surface presented to the responsible
human.

## Decision record

The responsible human accepted exact bounded non-privileged H0/R8-C
implementation target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` on
2026-09-17. The supplied instruction was exactly:

```text
accept exact target 1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4
```

This decision applies only to that exact immutable commit. Decision-neutral
packet commit `2752bc476961ce3a65cde277d295e590faff364b` and this
acceptance-record follow-up are decision support, not implementation. The
accepted target, its parent, its tree, and the accepted R8/R8-A/R8-C plan
objects remain byte unchanged.

Acceptance adds no validation and erases no target evidence. The 80 unresolved
H0 facts, 118 `UNKNOWN` values, `r8_h0_exit=not-met`,
`BLOCKED-NOT-READY`, blocked/not-exit-ready posture, assumptions, trusted
boundaries, resolved findings, and open generated-asset reproducibility
finding all remain. The immutable target's own `not-reviewed` and `unaccepted`
fields are frozen pre-decision evidence; this record and the maintained
current-position documents carry the later responsible-human decision.

H1-H4 remain unauthorized and not started. K3 and all Beryllium hardware
validation remain `NOT RUN`. No root integration, predecessor-pin refresh,
dependency change, Linux, service, device, DMA, multicore, policy, successor,
publication, release, migration, push, or tag is authorized. Blocked candidate
`6e93461f6ea097cb095e31558f6956dc6c0c2708` and superseded candidates
`6e3b49e3a574626405ec2c4608bb4c4cf85161fa` and
`b0165f11c8be33a7bee8836a5aa0b36fabea588c` remain unchanged and
unaccepted.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact bounded non-privileged H0/R8-C implementation target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` (`r8: rebuild R8-C H0 successor candidate`), tree `7a9d80d08d0abb771d43cf76a4a297d9d668b375` |
| Parent / implementation base | Exact R8-C acceptance-record commit `d18b1c9c6ca8a0f2285f820ec960258620ae4b50`, tree `b7a5900e3519446362ef679337cb66c073fcea66` |
| Accepted plan chain | R8 plan `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`; R8-A `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`; R8-C `f47ae60266a467ca1a7704fd9a50b140e0f31bb0` |
| Branch and repository | Local branch `beryllium/r8-c-h0-pmr-081-v3` in the private Beryllium repository; the branch has no upstream |
| Current status | Implemented, committed, exact-target tested, independently reviewed with no significant open code finding, and **responsible-human accepted** at exact target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` on 2026-09-17. H0 remains blocked and not exit-ready by 80 unresolved facts and 118 `UNKNOWN` values |
| Decision recorded | **Accepted** exact target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` on 2026-09-17 by the explicit instruction `accept exact target 1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` |
| Retained target status | The target's `not-reviewed`, `unaccepted`, `BLOCKED-NOT-READY`, and `r8_h0_exit=not-met` fields remain frozen pre-decision evidence. Packet `2752bc476961ce3a65cde277d295e590faff364b` and this acceptance-record follow-up are decision support, not implementation |
| Successor status | H1-H4 are unauthorized and not started; K3 execution and Beryllium hardware validation are `NOT RUN` |
| Publication status | No push or tag was performed; public push, publication, release, clean-repository migration, and any `pathfinder/publication-gate.conf` change remain blocked |

The responsible-human decision is recorded above. No H1-H4 authority, K3 or
hardware result, root integration, dependency or predecessor-pin change,
successor work, publication permission, or wider assurance claim follows from
it.

## 2. Deliverables and exact inventory

The candidate is one commit over the accepted R8-C base. With rename
detection, Git reports **117 changed entries**: 94 modified, seven added, six
deleted, and ten renamed. With rename detection disabled, the union is
**127 paths**:

- 27 non-generated paths; and
- 100 generated planning-site paths under `docs/html/**`.

The 27 non-generated paths comprise 17 changed members of the 24-path H0
inventory, seven changed members of the nine-path R8-A support inventory, and
exactly three R8-C paths. Inventory counts describe the complete authority
sets; not every authorized path differs from the base.

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary human question |
| --- | --- | --- | --- | --- |
| H0 freeze and host-only validation package | `planning/single-hart-runtime-r8-h0-freeze.md`; changed files under `tests/r8/` | Reconstruct the accepted H0/R8-A package on the new exact base, bind the selected profile inputs, derive the exact candidate identity, and retain fail-closed host checks | Non-privileged host tooling only; no target runtime, CSR access, image, board load, or K3 execution | Do the 147 rows, 80 H0 blockers, launcher trust boundary, mutation tests, and exact-child identity remain complete and fail closed? |
| Content-based retired-parent scan | `pathfinder/tests/check-source-policy.sh` | Exclude content Git classifies as binary from only the repository-wide retired-parent scan | Repository policy checker; no H0 authority or runtime behavior | Does the `-I` addition eliminate only binary false matches while preserving the regex, pathspecs, historical allowance, diagnostic, and genuine-text rejection? |
| Real-checker regression | `pathfinder/tests/check-source-policy-regression.mjs` | Exercise the real checker with generated binary/text fixtures, deterministic C-locale child behavior, hostile Git environments, and bounded cleanup | Test-only scratch repositories; strict child environment prevents caller Git state from redirecting fixture writes | Can any locale, `GIT_DIR`-family variable, user Git configuration, path suffix, or cleanup edge make the test pass without proving the production behavior? |
| Mandatory wiring | `pathfinder/Makefile` | Run the regression once after the live source-policy checker in `toolcheck` | Build/test orchestration only | Is the new test mandatory without changing the target graph or any other command? |
| Current position and generated planning site | Seven maintained R8-A support files plus `docs/html/**` | Record the authorized successor boundary and render the maintained planning pages | Documentation and generated derivatives only; generated byte reproducibility remains open | Do current-position pages distinguish implemented, tested, reviewed, accepted, hardware-run, and publication states? |

### Exact non-generated parent-to-target inventory

```text
.github/copilot-instructions.md
README.md
pathfinder/Makefile
pathfinder/tests/check-source-policy-regression.mjs
pathfinder/tests/check-source-policy.sh
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/riscv-security-hardware.md
planning/roadmap.md
planning/single-hart-runtime-r8-h0-freeze.md
tests/r8/Makefile
tests/r8/README.md
tests/r8/check-launcher.mjs
tests/r8/check-profile.mjs
tests/r8/check-report.mjs
tests/r8/check-sources.mjs
tests/r8/generate-report.mjs
tests/r8/h0-ast-contract-v1.json
tests/r8/h0-claim-contract-v1.json
tests/r8/h0-profile-v2.json
tests/r8/h0-row-contract-v2.json
tests/r8/h0-source-boundary-v2.json
tests/r8/run-make.c
tests/r8/run-make.sh
tests/r8/safe-paths.mjs
tests/r8/test-rejections.mjs
```

The exact three R8-C implementation paths and modes are:

```text
100644 pathfinder/Makefile
100644 pathfinder/tests/check-source-policy-regression.mjs
100755 pathfinder/tests/check-source-policy.sh
```

The target changes no root `Makefile`, `be`, `scripts/check-be.sh`,
`package.json`, `package-lock.json`, predecessor acceptance pin or checker,
accepted R0-R7 mechanism or proof input, `pathfinder/docs/**`,
`pathfinder/docs/html/**`, target code under `include/`, `virt/`, or `arch/`,
or publication configuration.

## 3. Claim boundary

### What the exact candidate supports saying

- It is exactly one clean non-merge child of the authorized R8-C
  acceptance-record base.
- The H0 profile contains 147 rows, 118 `UNKNOWN` values, 83 `stop`
  dispositions, 80 H0-acceptance blockers, zero H1-entry blockers, 33
  H1-completion blockers, three H2-entry blockers, and one `NOT-RUN` row.
- The H0 rejection suite contains 119 cases: 20 profile, 13 manifest, 11
  report, 34 source, 12 bootstrap, 15 Make-control, and 14 path cases.
- The complete H0 semantic projection remains exactly 33 paths: 24 maintained
  H0 paths plus nine R8-A support paths. Its SHA-256 is
  `527d6e039080b529fe36564e287e37b448085c360b289e6b21779bdac9d32f95`.
- The three R8-C repository-gate paths are bound by the full candidate tree
  but remain outside the H0 semantic projection and claim inputs.
- The committed H0 report is 10,351 bytes with SHA-256
  `efb4233f93369f160287b3042ea921f7ff982db28653e2d01db8cd8b5b7894a2`.
- The static H0 launcher is 750,424 bytes with SHA-256
  `7e609b4ee769c5c63336937a3824fce0c4ed0340c240629aae2b345093d0da2c`;
  two independent rebuilds were identical.
- The source-policy regression invokes the real checker, generates the
  retired-name byte cases numerically, forces deterministic C-locale child
  behavior, proves the old non-`-I` behavior at run time, rejects genuine
  text, and isolates every fixture from ambient Git state.
- The exact candidate passed its standalone H0 gate, documentation gate,
  complete Helium gate, and repository-wide `make check` in the recorded
  environments.

### Trusted or assumed

- Git object, mode, tree, index, pathspec, regular-expression, and
  content/attribute classification semantics behave as exercised by Git
  2.55.0.
- `git grep -I` may honor applicable future Git attributes. The current
  repository has no binary or `-diff` attribute that suppresses a selected
  genuine-text path; a future attribute change must be reviewed as policy
  input.
- The selected Fedora 44 OCI image, read-only host dependency mounts, static
  launcher bootstrap table, compiler and linker, QEMU/OpenSBI used by Helium,
  browser renderer, Graphviz, and Rocq remain trusted validation
  infrastructure at their recorded identities.
- The H0 launcher deliberately leaves a disclosed same-euid concurrent-rename
  residual after its ownership, mode, link-count, descriptor, and bounded
  cleanup checks.
- Generated planning and Helium assets are functionally checked but are not
  claimed byte-reproducible across independent builds.

### Evidence unavailable or `NOT RUN`

- The 80 H0-acceptance facts remain unresolved, so H0 exit criteria are not
  met.
- No R8-H1, H2, H3, or H4 package has started.
- No K3 command, board reset, load, serial capture, observation, comparison,
  or Beryllium hardware validation was run.
- At exact-target validation time no H0 acceptance record existed. The
  immutable target retains that pre-decision state; this later record carries
  the responsible-human acceptance decision and adds no target evidence.
- No public-release or publication evidence exists.

### What the candidate does not implement or prove

- No privileged Beryllium runtime, assembly entry, linker script, target
  image, CSR access, guest behavior, device, DMA, multicore, Linux, service,
  policy, TE, CHERI, VBS, or attestation behavior.
- No formal verification, C refinement, whole-system proof, hardware
  validation, certification, integrity measurement, or attestation.
- No predecessor acceptance refresh, root integration, H1-H4 authorization,
  publication permission, or successor authority.
- Helium unit, QEMU, documentation, and evidence results inside `make check`
  remain Helium evidence and do not establish Beryllium K3 execution.

## 4. Security and correctness invariants

| Invariant | Contract | Implementation | Test or evidence |
| --- | --- | --- | --- |
| Exact-child identity | Accepted R8-A/R8-C plan; H0 freeze status and source boundary | `tests/r8/check-sources.mjs`, report generator/checker | `r8-check` reports target, parent, tree, and `committed-exact-child` |
| Binary handling is content-based | Accepted R8-C required semantics | `pathfinder/tests/check-source-policy.sh` retired-parent scan | Binary `.sh`, text `.bin`, no-suffix text, and old-scan behavioral cases |
| Genuine text remains denied | Unchanged `former_parent` expression and pathspec boundary | Same checker scan and historical transcript checks | Three generated text alternatives fail with the unchanged diagnostic |
| Fixture Git state is isolated | R8-C disposable-fixture and fail-closed requirements | `childEnvironment()` and sanitized-environment registration in the regression driver | Hostile `GIT_DIR`, worktree, index, object, config, attribute, exclude, trace, PATH, and shell probes leave a victim repository unchanged |
| Scratch cleanup is bounded | R8-C cleanup requirement | Lexical-boundary checks plus `lstat`-only recursive removal | Success, rejection, signal/error, and symlink cleanup probes leave no scratch root |
| R8-C does not alter H0 semantics | Accepted R8-C successor identity boundary | `REPOSITORY_GATE_SUPPORT_PATHS` is separate from `semanticPaths` | 33-path semantic SHA remains stable while the full candidate tree changes |
| H0 remains fail closed | R8-H0 profile, row, claim, AST, source, and report contracts | `tests/r8/` checkers and static launcher | 119 mutation cases; 80 H0 blockers; report remains `BLOCKED-NOT-READY` / not reviewed as frozen pre-decision target evidence, while this record carries the later acceptance decision |
| Launcher pre-authentication remains silent | H0 launcher threat boundary | `tests/r8/run-make.c` and static `run-make.sh` | Credential, environment, descriptor, alias, bootstrap, tool, path, mode, and cleanup rejections |
| Accepted predecessor bytes remain immutable | Accepted R0-R7 records and R8 plan chain | Candidate inventory excludes predecessor mechanisms and pins | Git path/object audit and complete repository gate |
| Generated documentation is nonsemantic | Accepted R8-A/R8-C support boundary | Planning generator and browser-render inventory | Link/static/browser checks; generated drift remains an explicit open finding |

## 5. Review history and resolved findings

### Original blocked evidence

PMR-080 candidate `6e93461f6ea097cb095e31558f6956dc6c0c2708`
remains byte unchanged, blocked, and unaccepted. Git 2.55.0 reported a binary
match when two non-text instruction sequences in its static
`tests/r8/run-make.sh` blob happened to satisfy the retired-parent expression.
The candidate was not amended or byte-ground to evade the match.

### Plan and implementation authority

The responsible human accepted exact R8-C plan target
`f47ae60266a467ca1a7704fd9a50b140e0f31bb0` on 2026-09-17. A later
instruction authorized the successor implementation from exact base
`d18b1c9c6ca8a0f2285f820ec960258620ae4b50` as one clean child. Neither
decision accepted H0 or authorized privileged work.

### Closed automated-review findings

1. **Ambient-locale test gap — superseded candidate
   `6e3b49e3a574626405ec2c4608bb4c4cf85161fa`.** The binary behavioral case
   was vacuous under UTF-8 locales because the old expression matched the
   instruction bytes only under the C locale. That candidate also contained
   unrelated `--noprofile`/`--norc` high-fd Bash hardening. The next candidate
   forced C locale for checker children, added a real old-scan behavioral
   probe, and removed the unrelated delta.
2. **Inherited Git environment — superseded candidate
   `b0165f11c8be33a7bee8836a5aa0b36fabea588c`.** A hostile ambient `GIT_DIR`
   could redirect fixture `git init` and `git add` into a victim repository
   while the driver still reported PASS. The final candidate uses an exact
   allowlisted child environment, disables user/system Git configuration and
   attributes, rejects unsanitized child environments structurally, and
   passed hostile victim-repository probes.
3. **Launcher validation environment.** Early independent runs exited 126
   silently because the caller injected forbidden `LD_LIBRARY_PATH` and
   `GIT_CONFIG_COUNT` variables or used an untrusted `/tmp` parent. A clean
   non-`/tmp` physical clone with the launcher's exact scrubbed environment
   passed. No launcher check was weakened.

Independent review of the final exact candidate found no significant open
code or plan-compliance issue.

### Open questions for human judgment

- Is Git's `-I` content/attribute classification the right policy boundary
  for tracked non-text objects?
- Is the exact three-path R8-C surface minimal and adequately separated from
  the 33-path H0 semantic projection?
- Are the static launcher, selected OCI/tool mounts, Git semantics, and
  same-euid concurrent-rename residual acceptable trusted boundaries?
- Do the 119 rejection cases cover the important negative paths without
  creating a success-shaped gap?
- Is functional documentation validation sufficient while generated-asset
  byte reproducibility remains unresolved?
- Does the exact candidate preserve the intended H0 claim boundary while
  leaving all 80 acceptance blockers explicit?

## 6. Validation and retained evidence

All target-validation results below are **pre-decision**. They were produced
from the exact clean target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` before packet
`2752bc476961ce3a65cde277d295e590faff364b` and before the responsible-human
decision. Acceptance adds no execution, rerun, measurement, or evidence.
Later documentation builds and checks validate only this acceptance-record
content and must not be represented as validation of the immutable target.

Validation was completed on 2026-09-17. The exact candidate worktree and each
validation clone began clean. The H0, documentation, Helium, and root gates
were run from separate physical clones so one gate's generated output could
not become another gate's input.

| Command or check | Exact boundary | Result |
| --- | --- | --- |
| Git parent/tree/inventory/mode and `git diff --check` audit | Exact target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` | PASS: one parent, tree `7a9d80d0...`, 27 non-generated paths and 100 generated-path union, no unexpected mode or path |
| Direct source-policy regression under C and UTF-8 callers | Exact target, disposable local Git fixtures | PASS: seven cases, forced C child locale, content classification, exact pathspecs, old scan rejected |
| Hostile Git environment and victim-repository probe | Exact driver and disposable victim repository | PASS: ambient Git/worktree/index/object/config/attribute/exclude/trace/PATH state did not reach children; victim index, tree, HEAD, sentinel, and status remained unchanged |
| `/usr/bin/env -i PATH=/usr/bin SHELL=/bin/bash HOME=/home/jmorris ./tests/r8/run-make.sh r8-check` | Fresh physical clone at exact target | PASS: 147 rows, 118 unknown, 80 H0 blockers, 119 rejections, exact parent/tree, 33 semantic paths, two identical launcher rebuilds |
| `HE_CHROMIUM=$(command -v chromium-headless-shell) ./be docs-check` | Separate fresh exact-target clone | PASS: 66 planning pages and 12 Helium pages browser-rendered with Chromium `150.0.7871.186` |
| `./pathfinder/he check` | Separate exact-target clone in the retained Fedora 44 Podman image, `--network none` | PASS, exit 0; stdout 16,627 bytes / SHA-256 `2be69ebe1b4777cc471348773b01f5521407a884a20dc98d1746a9eaf2fd5925`; stderr 3,001 bytes / SHA-256 `f6cef29a027127d2c12cada8d2b60ac3f5bfedc1b5f845b67c592ec8b626b408` |
| Literal root `make check` | Third exact-target clone in the same network-disabled image and read-only tool mounts | PASS, exit 0; stdout 151,902 bytes / SHA-256 `2d884a0a7d6206f0787bc18666d59323bef67cc1c9d8460cd0fc0a5643c66789`; stderr 3,001 bytes / SHA-256 `cd620293bab910a54892c18aff826e89475e4c0d7bb5790e3fd77713e5b21ed6`; retained-evidence consistency PASS |
| Independent final code review | Exact target and parent-to-target range | PASS: no significant finding; prior two Medium findings closed in superseded sibling candidates |

The selected validation image is the retained
`beryllium-r8-h0-static-fc44-candidate.oci.tar` archive, 809,764,352 bytes,
SHA-256
`fcf6c595140a9dd55d6afb633ac7777162492cdae6b77cd27a59e4541c1bd1f5`.
Its OCI manifest is
`sha256:fc48376706fb7f2265aab9d14072cff4413c770d9d1bae9d990bae49bf8e7cc9`,
its config/image ID is
`sha256:d8e5373fa92ddaf2c70c4b11e9c1d985d37d49f3b6b0a55a1cba46e3eea4ba81`,
and its recorded base-image label is
`sha256:dbf1bc988918e2a3d5ce4ca098f2f07087285a80405dcfbeea0c37d6a9707bbe`.

The complete offline gates used the selected image plus read-only mounts for
the exact Node/npm dependency closure, Graphviz, Chromium
`150.0.7871.186`, and the required Rocq standard library. These mounts and
the local Podman storage are trusted validation inputs. Networking was
disabled.

The stderr logs contain only Fontconfig and VitePress chunk-size warnings.
The validation clones acquired generated-document changes after the
documentation subgates: the root `make check` clone reported 95 changed or
untracked generated paths afterward. This is consistent with the open
generated-asset reproducibility finding. The clones were disposable, and
their changed generated output is not candidate content or retained evidence.
The immutable candidate worktree itself remained clean.

No K3 or other Beryllium hardware execution occurred.

### Retained pre-decision status fields and where acceptance lives

The accepted target and its H0 machinery are immutable and were not modified
to record the decision. Their `not-reviewed`, `unaccepted`,
`BLOCKED-NOT-READY`, and `r8_h0_exit=not-met` values therefore remain the
exact pre-decision measurements. They coexist with the unchanged 80 unresolved
H0 facts and 118 `UNKNOWN` values.

Those fields are not a statement that the exact target is unaccepted today.
The responsible human's acceptance of
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` on 2026-09-17 is carried by
this review and acceptance record and by the maintained current-position
documents that cite it. Rewriting the target, freeze, report, checker, or
accepted plan objects after the fact would falsify exact-target evidence.

## 7. Recommended human review sequence

Create an isolated detached worktree:

```sh
git worktree add --detach \
  ../beryllium-r8c-h0-review \
  1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4
cd ../beryllium-r8c-h0-review
git status --short
git show --no-patch --format=fuller \
  1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4
```

1. Verify the exact-child relation and inventory:

   ```sh
   git rev-parse HEAD HEAD^ HEAD^{tree}
   git diff --check \
     d18b1c9c6ca8a0f2285f820ec960258620ae4b50 \
     1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4
   git diff --name-status -M \
     d18b1c9c6ca8a0f2285f820ec960258620ae4b50 \
     1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4
   ```

2. Review the complete three-path R8-C behavior:

   ```sh
   git diff \
     d18b1c9c6ca8a0f2285f820ec960258620ae4b50 \
     1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4 -- \
     pathfinder/Makefile \
     pathfinder/tests/check-source-policy.sh \
     pathfinder/tests/check-source-policy-regression.mjs
   ```

3. Review H0 authority and semantic separation:

   ```sh
   git show 1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4:tests/r8/check-sources.mjs
   git show 1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4:tests/r8/h0-source-boundary-v2.json
   git show 1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4:planning/single-hart-runtime-r8-h0-freeze.md
   ```

4. Review the regression's environment allowlist, real-checker invocation,
   old-scan behavioral probe, genuine-text cases, and cleanup.
5. Review the 119 rejection categories and the static launcher's
   pre-authentication environment, descriptor, ownership, mode, and bootstrap
   checks.
6. Re-run the host-only candidate gate in a trusted physical checkout:

   ```sh
   /usr/bin/env -i \
     PATH=/usr/bin \
     SHELL=/bin/bash \
     HOME="$HOME" \
     ./tests/r8/run-make.sh r8-check
   ```

7. Confirm that all 80 H0 blockers, H1-H4 exclusion, K3 `NOT RUN`, and
   publication blocks remain explicit.

Remove the review worktree afterward:

```sh
cd ..
git worktree remove beryllium-r8c-h0-review
```

## 8. Human decision checklist

### Technical review

- [ ] The exact target is
      `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` over parent
      `d18b1c9c6ca8a0f2285f820ec960258620ae4b50`.
- [ ] The candidate is exactly one clean non-merge child of the authorized
      base.
- [ ] The complete changed-path inventory is limited to the authorized
      H0/R8-A reconstruction, exactly three R8-C paths, and generated planning
      derivatives.
- [ ] The production checker changes only the intended binary-classification
      semantics and preserves the expression, pathspecs, transcript allowance,
      diagnostic, and unrelated checks.
- [ ] The regression invokes the real checker and would fail if `-I` were
      removed even when its source assertion is bypassed.
- [ ] The regression's child environment prevents ambient Git or shell state
      from redirecting or corrupting fixture operations.
- [ ] Binary `.sh`, genuine text `.bin`/no-suffix, all three text expression
      alternatives, historical allowance, and cleanup paths are covered.
- [ ] The three R8-C paths remain outside the 33-path H0 semantic projection.
- [ ] All 80 H0 blockers and every `UNKNOWN`/`NOT RUN` distinction remain
      explicit and fail closed.
- [ ] The static launcher assumptions and same-euid concurrent-rename residual
      are acceptable.
- [ ] The independent code review's two Medium findings are visibly resolved
      rather than omitted.
- [ ] The tests cover the important negative paths and no success-shaped skip
      or broad error suppression remains.
- [ ] The selected OCI and read-only tool-mount trust assumptions are
      acceptable.
- [ ] The open generated-asset reproducibility finding is acceptable at this
      review boundary.
- [ ] Claims match the evidence and do not transfer Helium QEMU results to
      Beryllium K3 or hardware.
- [ ] H1-H4, K3 execution, root integration, publication, and successors
      remain excluded.

### Decision

- [x] **Accept** exact R8-H0/R8-C implementation target
      `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` on 2026-09-17 by explicit
      responsible-human instruction
      `accept exact target 1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`.
- [ ] Request revisions and require a new exact target and packet.
- [ ] Defer review and preserve all current blocked states.

Only the acceptance-decision box is checked because the responsible human
explicitly supplied that decision. The technical-review boxes remain
unchecked as review history; they record questions presented to the human,
not claims that automation settled them. No signature is generated.

## 9. Recorded decision and remaining boundaries

- **Recorded acceptance.** Acceptance applies only to exact bounded
  non-privileged H0/R8-C implementation target
  `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`, over parent
  `d18b1c9c6ca8a0f2285f820ec960258620ae4b50`, under accepted R8 plan
  `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`, R8-A
  `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`, and R8-C
  `f47ae60266a467ca1a7704fd9a50b140e0f31bb0`.
- **Decision support is not implementation.** Decision-neutral packet commit
  `2752bc476961ce3a65cde277d295e590faff364b` and this acceptance-record
  follow-up support the decision but are not accepted implementation. The
  target remains byte unchanged.
- **Scope accepted.** Acceptance covers the exact non-privileged H0/R8-C
  implementation boundary and its bounded host, repository-policy,
  documentation, and retained test evidence. It does not convert H0 into an
  exit-ready package or a privileged runtime.
- **Acceptance adds no validation or resolution.** The standalone H0 gate,
  documentation gate, network-disabled complete Helium gate, network-disabled
  root `make check`, and independent final review remain the exact pre-decision
  validation record. Acceptance does not erase the 80 unresolved H0 facts,
  118 `UNKNOWN` values, `r8_h0_exit=not-met`, `BLOCKED-NOT-READY`,
  blocked/not-exit-ready posture, assumptions, trusted boundaries, resolved
  findings, or open generated-asset reproducibility finding.
- **Frozen target fields stay as measured.** The target's `not-reviewed` and
  `unaccepted` fields remain pre-decision exact-target evidence. This record,
  not modified target machinery, carries the later responsible-human
  decision.
- **Candidate history is unchanged.** Blocked candidate
  `6e93461f6ea097cb095e31558f6956dc6c0c2708` and superseded candidates
  `6e3b49e3a574626405ec2c4608bb4c4cf85161fa` and
  `b0165f11c8be33a7bee8836a5aa0b36fabea588c` remain unchanged and
  unaccepted.
- **Successor and publication boundaries.** H1-H4 remain unauthorized and not
  started; K3 and Beryllium hardware remain `NOT RUN`. No root integration,
  predecessor-pin refresh, dependency change, Linux, service, device, DMA,
  multicore, policy, successor, publication, release, migration, push, tag,
  or `pathfinder/publication-gate.conf` change is authorized.

---

**Status:** exact bounded non-privileged H0/R8-C target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` (parent
`d18b1c9c6ca8a0f2285f820ec960258620ae4b50`, tree
`7a9d80d08d0abb771d43cf76a4a297d9d668b375`) is implemented, tested,
independently reviewed with no significant open finding, and
responsible-human accepted as of 2026-09-17. It remains local-only, unpushed,
untagged, blocked by 80 unresolved facts and 118 `UNKNOWN` values, and not
exit-ready; `r8_h0_exit=not-met`. K3 and Beryllium hardware validation are
`NOT RUN`.

**Next:** no successor work is authorized. H1-H4 and K3 remain gated, and all
publication and integration boundaries remain blocked.

**Action required from you:** none for this recorded H0/R8-C decision.
Separate explicit authorization is required before H1-H4, K3 execution, root
integration, dependency or predecessor-pin changes, successor work, push,
tag, publication, release, or migration.

## 2026-09-24 current-line reconciliation

On 2026-09-24, the responsible human confirmed that the existing
2026-09-17 instruction
`accept exact target 1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` and this
acceptance record are genuine. This is a reconciliation of current status,
not a second acceptance date and not a broader decision.

The active current line carries this historical record and maintained status
only. It does not merge or cherry-pick target
`1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4`, packet
`2752bc476961ce3a65cde277d295e590faff364b`, or acceptance-record commit
`0d53120a7c840b9dc8e2e05d089c922591032522`. Those objects remain on local
branch `beryllium/r8-c-h0-pmr-081-v3`; no remote-tracking ref contains them.

Count attribution remains exact:

- accepted target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` has 147 rows,
  118 `UNKNOWN` values, 80 H0-acceptance blockers, 33 H1-completion blockers,
  three H2-entry blockers, `BLOCKED-NOT-READY`, and
  `r8_h0_exit=not-met`; and
- the separate historical, unaccepted H0 source package introduced at
  `102f2b0569396bf33ed2177ea5b7558cf5e6fbaa` on the active line reports 81
  H0 blockers. Its count is not an accepted-target measurement and its
  hash-bound source is not changed by this reconciliation.

A COM260 board is available, and read-only inventory and troubleshooting
occurred on 2026-09-24. Those observations are session-local discovery only:
they are not part of the accepted target, are not retained R8 hardware
evidence, do not change K3 from `NOT RUN`, and do not select a development
kernel or BSP. Physical, firmware, and tool facts require a later reviewed
successor relation from the accepted target before they can become maintained
H0 evidence.

Prospective tree `8f192c530b03ea33496b95f11ea46537ac02d0b6`, reconstructed
from the `d18b1c9c6ca8a0f2285f820ec960258620ae4b50` base before this
confirmation, is uncommitted diagnostic content only. It is not a candidate,
successor, accepted target, or authorized relation.

The next gate is unchanged and exact: a separately reviewed plan, base, and
relation plus explicit responsible-human authorization are required before
any H0 successor may incorporate COM260 facts. Acceptance of exact H0/R8-C
target `1999ee70084a0f3bb9bb943b5d1f13e99d6b59a4` alone does not authorize
H1. H1-H4 remain not started and unauthorized; K3 and all Beryllium hardware
validation remain `NOT RUN`.
