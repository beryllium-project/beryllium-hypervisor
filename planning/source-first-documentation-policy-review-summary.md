<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Source-first documentation policy review summary

This is the decision-neutral responsible-human review packet for exact
source-first documentation policy and tooling target
`ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e`. Its immediate parent is
`d4c5ff0616c78d997367a050db85512c44960acb` and its Git tree is
`210a68ce4fe972942bc632ab3435cf234cc3a16f`.

The target is implemented and extensively tested, but it is **not accepted**
by this packet. The responsible human must decide whether to accept that exact
commit, request revisions, or defer.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e`, parent `d4c5ff0616c78d997367a050db85512c44960acb`, tree `210a68ce4fe972942bc632ab3435cf234cc3a16f` |
| Branch and repository | `beryllium/single-hart-runtime-r0`; private internal repository; target is local, unpushed, and untagged |
| Current status | Implemented; exact source gate, command graph, R1-R6, and bounded R7 validation completed; responsible-human review not yet recorded |
| Decision requested | Accept exact target, request revisions, or defer |
| Successor status | No successor package is started or authorized by this target |
| Publication status | Push, tag, public migration, publication, and release remain blocked; `pathfinder/publication-gate.conf` is unchanged |

**Action expected:** review the exact commit and choose acceptance, revision, or
deferral without widening any runtime, hardware, successor, or publication
gate.

## 2. Deliverables

The target changes 354 paths with rename detection disabled: 24 modified,
two added, and 328 deleted. The maintained boundary is 26 paths; the remaining
262 planning HTML and 66 retained-Helium HTML paths are generated-output
deletions.

| Deliverable | Paths | Purpose and boundary | Highest-value review question |
| --- | --- | --- | --- |
| Source-first policy | `.github/copilot-instructions.md`, `.github/skills/helium-documentation/SKILL.md`, `.github/skills/human-review-summary/SKILL.md`, `LLM_POLICY_ALIGNMENT.md`, `planning/README.md`, `planning/HANDOFF.md`, `planning/glossary.md`, `planning/project-orientation.md`, `planning/roadmap.md`, `planning/single-hart-runtime-r6-plan-review-summary.md` | Makes Markdown and DOT the routine source of truth while preserving complete rendered-site gates for milestones, release, publication, and periodic CI | Does the policy improve engineering velocity without weakening evidence, review, or publication requirements? |
| Fail-closed source gate | `scripts/check-doc-sources.mjs`, `scripts/test-doc-source-check.mjs`, `package.json` | Checks Markdown, links, fragments, routes, static VitePress configuration, references, filesystem containment, privacy, retired names, generated-output state, and policy syntax without executing configuration or using the network | Are unsupported syntax, filesystem indirection, unsafe routes, and historical-evidence exceptions rejected rather than guessed? |
| Root command graph | `Makefile`, `be`, `scripts/check-be.sh` | Adds `docs-source-check`, uses it in routine model/root checks, verifies the routine graph excludes rendered-site tooling, and retains explicit complete docs commands | Are routine and milestone commands visibly distinct and mechanically enforced? |
| Retained Helium command graph | `pathfinder/Makefile`, `pathfinder/he`, `pathfinder/README.md`, `pathfinder/docs/index.md`, `pathfinder/docs/quickstart.md`, `pathfinder/docs/engineering-sop.md` | Adds a routine source/policy/host-unit/report gate without QEMU, rendered docs, or retained-evidence generation; the complete component gate remains unchanged | Does `check-source` omit only heavyweight routine work while `check` still retains QEMU, rendered documentation, and evidence? |
| Generated-output disposition | `.gitignore`, `docs/html/**`, `pathfinder/docs/html/**` | Removes generated HTML from the active line, ignores local regeneration, and preserves the historical private snapshot at `archive/generated-docs-2026-09-30` | Is the archive clearly historical and non-authorizing, with Markdown still authoritative? |
| Predecessor acceptance bindings | `tests/r1/check-acceptance.sh`, `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs` | Refreshes exactly six previously authorized root-tooling delta pins; no accepted mechanism byte changes | Do the recomputed hashes bind only the intended root tooling changes? |

The maintained target inventory is:

```text
.github/copilot-instructions.md
.github/skills/helium-documentation/SKILL.md
.github/skills/human-review-summary/SKILL.md
.gitignore
LLM_POLICY_ALIGNMENT.md
Makefile
be
package.json
pathfinder/Makefile
pathfinder/README.md
pathfinder/docs/engineering-sop.md
pathfinder/docs/index.md
pathfinder/docs/quickstart.md
pathfinder/he
planning/HANDOFF.md
planning/README.md
planning/glossary.md
planning/project-orientation.md
planning/roadmap.md
planning/single-hart-runtime-r6-plan-review-summary.md
scripts/check-be.sh
scripts/check-doc-sources.mjs
scripts/test-doc-source-check.mjs
tests/r1/check-acceptance.sh
tests/r3/check-accepted-content.mjs
tests/r4/check-accepted-content.mjs
```

## 3. Claim boundary

Exact target `ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e`
supports saying:

- authoritative Markdown and DOT are checked routinely without regenerating
  HTML or invoking Chromium;
- the routine documentation gate validates 90 site Markdown files, five
  policy Markdown files, 889 rendered references, 219 configured routes, ten
  DOT sources, and ten public assets, with zero tracked generated HTML;
- 34 adversarial cases exercise fail-closed parsing, links, fragments,
  configuration overrides, rewrite semantics, filesystem indirection,
  special files, privacy inventories, tracked output, timeouts, process
  observation, network isolation, and generated-tree immutability;
- root and retained-Helium routine graphs contain no QEMU or rendered-site
  command, while explicit complete gates retain QEMU, VitePress, Chromium,
  rendered-site, and evidence generation;
- the active line tracks no file under `docs/html/` or
  `pathfinder/docs/html/`; both roots are ignored for local milestone output;
- all six predecessor acceptance pins recompute exactly; and
- R1-R6 pass in the retained pinned environment and bounded R7 passes in the
  provenance-recorded derived environment described below.

The target still trusts:

- Node, Git, Markdown rendering libraries, shell tools, and filesystem
  behavior within their checked versions and observed execution boundaries;
- the private archive ref as preservation of the parent snapshot;
- the retained predecessor OCI as the pinned Node/Rocq-core base; and
- the Fedora signature and package metadata for the bounded derived
  `rocq-stdlib` addition used only to complete R7 validation.

Evidence that remains unavailable or not accepted:

- the original retained OCI alone cannot run R7 because it omits
  `rocq-stdlib`;
- the derived OCI is session-local validation infrastructure, not a
  repository-pinned or responsible-human-accepted environment;
- an inherited tracked binary at `tests/r8/run-make.sh` triggers a
  pinned-Git source-policy portability failure; that byte is unchanged by the
  target;
- K3 and all Beryllium hardware validation remain `NOT-RUN`; and
- no generated HTML milestone build or Chromium run is claimed for this
  source-first policy target because renderer and theme behavior are not
  changed.

The target does **not**:

- accept or authorize R8-ALM1 implementation, an H0 successor, H1-H4, K0-X,
  K0-R, B0, B1, Linux, service, device, DMA, or multicore work;
- change an accepted R0-R7 mechanism, proof, or evidence input;
- make Beryllium or Helium formally verified;
- add K3 or other hardware evidence;
- approve the derived OCI for normative future use;
- approve push, tag, publication, release, or public migration; or
- change the Helium publication gate.

## 4. Security and correctness invariants

| Invariant | Contract and implementation | Test or evidence |
| --- | --- | --- |
| Routine checks cannot silently execute documentation configuration | `scripts/check-doc-sources.mjs` parses a bounded static configuration subset and rejects duplicate, spread, computed, method, dynamic-route, and pattern-rewrite syntax | `scripts/test-doc-source-check.mjs`; 34 adversarial cases |
| Local references cannot escape trusted roots or traverse filesystem indirection | Lexical and canonical containment, `lstat`, regular-file requirements, and symlink/FIFO/socket/special-file rejection | Traversal, parent/leaf symlink, FIFO, socket, and generated-root fixtures |
| Unsafe or missing rendered references fail closed | Markdown-rendered links, HTML references, definition labels, routes, fragments, and unsafe schemes are checked | Missing-fragment, undefined-reference, unsafe-scheme, rewrite, and nested-page fixtures |
| Historical private locators cannot expand or disappear unnoticed | Existing review-record locator inventories are bound by exact digest; new records receive no blanket exemption | Addition/change/removal adversarial fixtures |
| Routine gates do not perform heavyweight emulation or browser work | Root and component Make graphs use source/host targets; `scripts/check-be.sh` rejects QEMU and rendered-site commands from routine dry runs | Exact-target graph assertions and host `./pathfinder/he check-source` |
| Complete gates remain available | `./be docs-check`, `./pathfinder/he check`, and publication checks retain their prior milestone/release roles | Full-graph dry runs show QEMU, rendered docs, and evidence generation |
| Accepted predecessor content remains bounded | Six exact target-to-current delta digests bind the root Makefile, wrappers, and acceptance checker changes | R1-R5 acceptance and negative checks; direct R3/R4 accepted-content checks |
| Source checks cannot mutate documentation artifacts | The isolation harness hashes generated/public trees before and after, observes subprocesses, rejects network events, and applies a hard timeout | Zero network events and zero generated/public-tree changes |

## 5. Review history and resolved findings

Automated and independent review found and closed substantive defects before
the exact target was committed:

1. **First MAX review:** broken-fragment and reference gaps, unsafe URL
   schemes, path traversal, symlink/special-file handling, configuration and
   instruction parsing, privacy variants, tracked-HTML handling, timeout and
   process-observation weaknesses, and retained-Helium graph leakage.
2. **Independent review round one:** effective VitePress property override,
   rewrite-route, nested reserved-directory page, and review-record privacy
   bypasses.
3. **Independent review round two:** VitePress pattern rewrites, root
   generated/public Markdown, and complete removal of historical locator
   inventories.
4. **Pinned validation:** incorrect Make target-range parsing and routine
   Helium QEMU reachability.

Each finding received a regression or graph assertion. Final independent
review reported no significant issue and all 34 adversarial cases passed.

Open findings requiring human awareness, but not introduced by this target:

- the retained OCI lacks `rocq-stdlib`, so R7 required a bounded derived OCI;
- pinned Git treats inherited `tests/r8/run-make.sh` as binary during one
  source-policy grep, preventing the aggregate component gate in that
  environment; and
- the generated-asset reproducibility finding remains unresolved on the
  active line.

## 6. Validation and retained evidence

Validation date: September 30, 2026.

| Validation | Result and boundary |
| --- | --- |
| `./be docs-source-check` | PASS on the exact target: 90 site Markdown, five policy Markdown, 889 references, 219 routes, ten DOT sources, ten public assets, zero tracked HTML, 34 adversarial cases, zero network events, zero generated-tree changes |
| `make be-check` | PASS on the exact target in the retained pinned OCI; source gate, wrapper behavior, command graph, syntax, and acceptance bindings pass |
| R1-R5 acceptance and negative checks | PASS on the exact target; R2 executed 5,511 tests per compiler |
| Full R6 | PASS on the exact target in the retained OCI: 47 entries, 32 images, 64 QEMU runs, 21,740 assertions; 550-file evidence bundle; zero raw traces; `--require-complete` passed |
| Full R7 in original retained OCI | FAIL as expected from environment incompleteness: `Stdlib.ZArith` is absent because `rocq-stdlib` is not installed |
| Full R7 in bounded derived OCI | PASS on the exact target: two images, 22 symbols, 1,420 words, 144 targets, nine Rocq modules, 135 theorems, closed assumptions, independent `rocq check`, 6,186 report checks, 31-file evidence bundle |
| Host `./pathfinder/he check-source` | PASS on content equivalent to the exact target: source documentation/policy, tool checks, GCC/Clang host unit tests, and authority report semantics; no QEMU or rendered docs |
| Routine/full graph assertions | PASS: routine root/model/component graphs exclude QEMU and rendered-site tooling; the complete component graph retains QEMU, full docs, and evidence |
| Exact inventory and tree state | PASS: 354 paths, 26 maintained paths, no unexpected mode changes, clean exact target, HTML roots absent/ignored, public/generated manifests unchanged |
| `git diff --check` and source syntax | PASS |

Retained validation identities:

```text
base_oci_sha256=6aac298509662161ff43063b8b14d848c0cf6d517aba6dfca28e0b3d40682a06
derived_oci_sha256=4dabaa9902ce80505c2fcfd77dc7c5f67d446a7de655156e0dd229a77f02b241
derived_oci_image_id=ebe213f212c6f7c698735af3304fb23a5d945a7057a16d79e7950ea9d15216ad
rocq_stdlib_rpm=rocq-stdlib-9.1.0-2.fc44.x86_64
rocq_stdlib_rpm_sha256=e36797b782c1121655e1c3d0b8e353112263d9682f8dce884252a7ee42a31de5
r6_report_sha256=4dac1288c498cf76b8e3048281298d26f46f1c9f8178b043342fb6ef64425c1c
r6_evidence_manifest_sha256=96527c9fbd62db6eb1e7ab8ce6682dc01671de8560d3d98e3c1d2b245258923c
r7_report_sha256=594f14bc2c481bddf62d520884c2571c18edb84b4f81d75acec47f3faa3ed773
r7_evidence_manifest_sha256=2f291b7f9c78b3e12c287710a2caf79de3c3bd2e5b01f1c6d81546b84b0c4b0e
```

The six exact predecessor pins are:

```text
r1_makefile=21eadec8a69cbb7981de66c455299ced4bf8985ea8654068abdec97097bb2a51
r3_to_r1=13cd25e9dffc8ceace984e9a23ff94aa2f84269c819a80134ddfd920c28769fe
r3_to_be=35ef12181d6a5e7951677470bc68fcf02aaa1c7e79fff70aeec05c0248502ab2
r3_to_check_be=5193f04dce9bf0ce0d68b5b578dc69faea8b0d2a60fb47b5542b321e7ffb2659
r4_to_be=95739bdae3b4b50d0ac3a8afaa97b1c9364ea1d6e6667389ecd1f5cdc482efec
r4_to_check_be=af08a8ccbd9e90f9353c1f34905096fa3fd1c705a57dbfbf65a0a6bf7fc53c30
```

Session-retained logs and the derived environment recipe are identified by
`source-first-corrected-validation-logs-66eaa7f7` and
`rocq-r7-derived-66eaa7f`. They are not publication artifacts.

## 7. Recommended human review sequence

1. Inspect the exact identity and inventory:

   ```sh
   git show --no-patch --pretty=fuller ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e
   git diff --no-renames --name-status \
     d4c5ff0616c78d997367a050db85512c44960acb \
     ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e
   ```

2. Review policy and claim boundaries first:

   ```sh
   git diff d4c5ff0616c78d997367a050db85512c44960acb \
     ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e -- \
     LLM_POLICY_ALIGNMENT.md planning/README.md planning/roadmap.md \
     planning/project-orientation.md planning/HANDOFF.md \
     .github/copilot-instructions.md .github/skills
   ```

3. Review the fail-closed checker and adversarial harness:

   ```sh
   git diff d4c5ff0616c78d997367a050db85512c44960acb \
     ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e -- \
     scripts/check-doc-sources.mjs scripts/test-doc-source-check.mjs
   ```

4. Review root/component command separation and predecessor bindings:

   ```sh
   git diff d4c5ff0616c78d997367a050db85512c44960acb \
     ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e -- \
     Makefile be scripts/check-be.sh pathfinder/Makefile pathfinder/he \
     tests/r1/check-acceptance.sh tests/r3/check-accepted-content.mjs \
     tests/r4/check-accepted-content.mjs
   ```

5. If rerunning, use an isolated detached worktree:

   ```sh
   git worktree add --detach ../be-source-first-review \
     ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e
   cd ../be-source-first-review
   ./be docs-source-check
   ```

The host Node installation does not match the accepted R3/R7 executable lock.
Use the retained or derived pinned environment for normative predecessor
replay rather than relaxing locks or substituting host tools.

## 8. Human decision checklist

- [ ] The 26 maintained paths and 328 generated-output deletions match the
      intended source-first scope.
- [ ] Markdown/DOT authority and deferred HTML policy match the current
      project priority.
- [ ] Routine gates omit only the intended QEMU/browser/generated-evidence
      work, while complete milestone and publication gates remain intact.
- [ ] Fail-closed source checks cover the important negative paths.
- [ ] Historical private evidence is preserved without permitting new locator
      drift.
- [ ] The six predecessor pins and unchanged accepted mechanisms are
      acceptable.
- [ ] The derived-OCI R7 result is interpreted only as bounded validation,
      not as acceptance of that environment.
- [ ] The inherited pinned-Git source-policy finding is acceptable as an open
      follow-up rather than hidden by this target.
- [ ] K3/hardware, runtime successors, publication, and release remain
      excluded.
- [ ] Accept exact commit
      `ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e`, request revisions, or defer.

## 9. After the decision

- **Accept:** the responsible human explicitly authorizes recording acceptance
  of exact SHA `ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e`.
  A later acceptance record names that SHA and the decision date. Acceptance
  does not itself approve the derived OCI, push, tag, publication, release,
  hardware execution, or successor work.
- **Request revisions:** create a new implementation commit and a new review
  packet. This target remains unaccepted.
- **Defer:** preserve the local private target and current blockers; do not
  start dependent work.

**Status:** exact implementation target is local, tested, unpushed, untagged,
and not reviewed or accepted by the responsible human.

**Next:** responsible-human decision on exact commit
`ee1feaf9dbc9f0762db4bd55e5d0910b07e84a5e`.

**Action required from you:** accept that exact commit, request revisions, or
defer.
