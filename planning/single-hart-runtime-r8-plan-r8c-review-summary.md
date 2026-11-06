<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R8 plan revision C review and acceptance record

This document began as the decision-support packet for one exact immutable
planning commit -- `f47ae60266a467ca1a7704fd9a50b140e0f31bb0`, which carries
**Plan revision R8-C**, the narrow content-based correction plan for the
Helium retired-parent namespace scan -- and now also records the
responsible-human decision taken on it. The decision-support material below is
retained as review history and remains the evidence the decision rests on.
Except where a statement is explicitly marked as current, sections 1 through
9 describe the state at the time of that decision. The target is immutable and
changes only `planning/single-hart-runtime-r8-plan.md`.

The accepted original R8 plan remains exact history at
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`. Accepted Plan revision R8-A
remains exact history at `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`;
its acceptance-record commit
`1f6109f0d0371eb3707e296c3416e8c55235683e` remains the historical H0
implementation base. Exact H0 candidate
`6e93461f6ea097cb095e31558f6956dc6c0c2708` remains blocked, byte unchanged,
not reviewed, and unaccepted.

Resolved PMR-081 tasking is identified by source commit
`35f0f20037f85109bebd1cd24d6d0d3b141989a1` and request-table blob
`6276caeb69869a2a47508498e9b2fc86db387013`. It authorizes this planning
package only. It does not authorize implementation.

## Decision record

Responsible-human review **accepted the exact R8-C plan-revision commit**
`f47ae60266a467ca1a7704fd9a50b140e0f31bb0` (parent
`fc6795b03b5f68849fe5ef882d7e2cae77ab4e90`) on 2026-09-17. The supplied
instruction was exactly:

```text
Accept exact R8-C plan commit f47ae60266a467ca1a7704fd9a50b140e0f31bb0. Record this decision only; do not implement R8-C or start a successor H0 candidate.
```

The accepted target's Git tree is
`b6470b1c002c66afd58fd7ad9362e3ba34cd5fda`, and its subject is
`docs: propose narrow R8-C source scan revision`. This decision applies only
to that exact immutable commit. The target remains byte unchanged.

The accepted target's own plan text still reports
`r8_plan_revision_r8c=proposed-not-reviewed`. That is frozen pre-decision
content describing the commit as offered. Its retained
`r8_r8c_implementation_authorization=none` and
`r8_h0_successor=not-authorized` fields remain consistent with this decision.
This record and the maintained current-position documents carry the later
acceptance decision; the immutable plan file is not rewritten after review.

Packet commit `0b8fdad1b4052791baae0327c52a37d9ec3a76e1`
(`docs: prepare exact R8-C plan review`) and this acceptance-record follow-up
are decision support only. Neither is plan text, checker implementation, H0
implementation, or an approved implementation base. The accepted R8-C target
remains exactly `f47ae60266a467ca1a7704fd9a50b140e0f31bb0` over parent
`fc6795b03b5f68849fe5ef882d7e2cae77ab4e90`.

Acceptance covers **plan text only**. It records no R8-C implementation
authorization, selects no implementation base or direct-child relation,
changes no checker byte, and does not authorize or start a successor H0
candidate. Exact blocked H0 candidate
`6e93461f6ea097cb095e31558f6956dc6c0c2708` remains byte unchanged,
blocked, not reviewed, and unaccepted; it is not an approved future base.
R8-H1 through R8-H4 remain unauthorized and not started, and K3 execution and
hardware validation remain `NOT RUN`.

This decision does not close the generated-asset reproducibility finding and
does not authorize push, tag, publication, release, clean-repository
migration, or any `pathfinder/publication-gate.conf` change.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `f47ae60266a467ca1a7704fd9a50b140e0f31bb0` (`docs: propose narrow R8-C source scan revision`, tree `b6470b1c002c66afd58fd7ad9362e3ba34cd5fda`) |
| Parent / comparison base | `fc6795b03b5f68849fe5ef882d7e2cae77ab4e90` |
| Accepted predecessors | R8 plan `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`; R8-A `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`; R8-A acceptance/base `1f6109f0d0371eb3707e296c3416e8c55235683e` |
| Branch and repository | `beryllium/single-hart-runtime-r0`; private repository `beryllium-project/beryllium-hypervisor` |
| Target publication state | Local, unpushed, and untagged at packet preparation; zero remote branches and zero tags contain the target |
| Current status | R8-C is **accepted at exact target `f47ae60266a467ca1a7704fd9a50b140e0f31bb0` as of 2026-09-17**. The immutable target retains its proposed pre-decision field. The checker is unchanged, R8-C implementation authorization is none, and the blocked H0 candidate remains unchanged and unaccepted. |
| Decision | Responsible-human acceptance of exact commit `f47ae60266a467ca1a7704fd9a50b140e0f31bb0` on 2026-09-17 by the exact instruction quoted above |
| Successor status | No R8-C implementation or successor H0 candidate is authorized or started; H1-H4 remain blocked and K3 execution is `NOT RUN` |
| Publication status | Push, tag, publication, release, clean-repository migration, and any `pathfinder/publication-gate.conf` change remain blocked |

**Action taken:** the responsible human accepted exact R8-C target
`f47ae60266a467ca1a7704fd9a50b140e0f31bb0`. That decision covers plan text
only. No implementation authorization, implementation base or relation,
successor H0 candidate, H1-H4 authority, hardware execution, or publication
authority follows.

## 2. Deliverables

The exact parent-to-target delta is one regular mode-`100644` file:

```text
planning/single-hart-runtime-r8-plan.md
```

| Deliverable | Path | Purpose | Trust / privilege boundary | Primary human question |
| --- | --- | --- | --- | --- |
| Plan revision R8-C | `planning/single-hart-runtime-r8-plan.md` | Define content-based text-versus-binary handling for only the repository-wide retired-parent scan; preserve the exact diagnostic; enumerate the complete three-path future implementation boundary, regression obligations, and successor relation | Planning text only; no checker, test, Makefile, H0 candidate, runtime, privileged source, evidence, pin, or publication state changes | Does the plan eliminate only the binary false positive while preserving genuine text rejection, the historical allowance, H0 semantics, and every accepted predecessor boundary? |

The target does not change:

- `pathfinder/tests/check-source-policy.sh`;
- `pathfinder/Makefile`;
- any `pathfinder/tests/` regression source;
- blocked candidate `6e93461f6ea097cb095e31558f6956dc6c0c2708`;
- any accepted R0-R7 mechanism, checker, evidence input, or pin;
- any R8 H0 source, contract, report, generated evidence, image, runtime,
  assembly, linker, or hardware path;
- root integration, dependencies, publication configuration, or generated
  documentation.

Reproduce the exact target inventory with:

```sh
git diff --name-status \
  fc6795b03b5f68849fe5ef882d7e2cae77ab4e90 \
  f47ae60266a467ca1a7704fd9a50b140e0f31bb0
git ls-tree \
  f47ae60266a467ca1a7704fd9a50b140e0f31bb0 \
  planning/single-hart-runtime-r8-plan.md
```

Authoritative inputs for this review are:

- `planning/single-hart-runtime-r8-plan.md`, including accepted R8/R8-A
  history and proposed R8-C;
- `planning/single-hart-runtime-r8-h0-freeze.md` and the PMR-080 return in
  `planning/HANDOFF.md`, which bound the blocked H0 candidate and its
  non-claims;
- `planning/roadmap.md` and `planning/README.md`, which carry current position
  and navigation;
- repository-root `LLM_POLICY_ALIGNMENT.md`, which keeps review, authorship,
  and public-release authority human-controlled; and
- resolved PMR-081 source commit
  `35f0f20037f85109bebd1cd24d6d0d3b141989a1` and request-table blob
  `6276caeb69869a2a47508498e9b2fc86db387013`.

## 3. Claim boundary

### What the exact target supports saying

- Git 2.55.0 can report a binary match when arbitrary non-text instruction
  bytes happen to satisfy the existing retired-parent text regular
  expression.
- Exact blocked candidate
  `6e93461f6ea097cb095e31558f6956dc6c0c2708` contains a mode-`100755`,
  750384-byte static ELF at `tests/r8/run-make.sh`, blob
  `3e5d242fa474be70a708b44b38a155a9a325a562`, with bytes
  `83 78 68 00` at zero-based offsets `298230` and `306332`.
- No printable retired-name string occurs in that blob.
- Filename classification is invalid for this purpose because the static ELF
  retains a `.sh` suffix.
- The minimum planned policy change is content-based binary exclusion for only
  the repository-wide `former_parent` `git grep`; the regular expression,
  pathspec exclusions, exact historical transcript allowance, diagnostics,
  and unrelated source-policy checks stay unchanged.
- The complete new future implementation boundary is exactly three paths:
  `pathfinder/tests/check-source-policy.sh`,
  `pathfinder/tests/check-source-policy-regression.mjs`, and
  `pathfinder/Makefile`.
- A generated binary fixture must pass and generated genuine text fixtures
  must fail without permanently embedding or allowlisting forbidden text.
- The existing 33-path H0 semantic projection and claim boundary do not gain
  the three R8-C repository-gate support paths.

### What the exact target alone does not support saying

- By itself, that R8-C has been reviewed or accepted; the separate decision
  record above now supplies acceptance for that exact target.
- That the checker has been changed or that its complete gate now passes.
- That a regression driver or Makefile invocation exists.
- That blocked candidate
  `6e93461f6ea097cb095e31558f6956dc6c0c2708` is accepted, unblocked,
  amended, superseded, or a valid future base.
- That a successor H0 candidate is authorized or has started.
- That any H0 path, mode, hash, tree, projection, count, report identity, or
  blocker has been re-derived.
- That any board, firmware, hardware, K3, H1-H4, runtime, proof,
  C-refinement, whole-system, production, or publication evidence exists.

### Trusted or assumed

- Git commit, tree, blob, path, and mode identity behave as used by the plan.
- Git 2.55.0 `git grep -I` content classification provides the intended
  binary exclusion while retaining matching text.
- The future regression driver can exercise the real checker in a disposable
  local Git fixture using only repository-standard Node.js and Git.
- The accepted R8, R8-A, and R0-R7 records mean exactly what their existing
  review and acceptance records state.
- The private repository and local validation host remain trusted development
  infrastructure, not assurance evidence.

### Evidence unavailable or `NOT RUN`

- No R8-C implementation or exact implementation target exists.
- No successor H0 candidate exists.
- The complete candidate `make check` remains blocked by the unchanged
  checker behavior recorded by PMR-080.
- R8-H1 through R8-H4 have not started.
- K3 execution and hardware validation are `NOT RUN`.
- The generated-asset byte-reproducibility finding remains open.

## 4. Security and correctness invariants

These are plan obligations, not implemented properties.

| Invariant | Contract in the target | Future enforcement or evidence point | Current status |
| --- | --- | --- | --- |
| Binary handling is content-based | `Required text-versus-binary semantics` | The one production `git grep` gains binary-ignore semantics; binary `.sh` and text `.bin` regression cases | Proposed; not implemented |
| Genuine text remains denied | `Required text-versus-binary semantics`; `Required regression coverage` | Generated text cases for byte sequences `78 68`, `78 68 5f`, and `58 48 5f` must trigger the existing diagnostic | Proposed; underlying current regex remains unchanged |
| The policy expression does not drift | `Required text-versus-binary semantics` | Source assertion binds the unchanged `former_parent` assignment and pathspec exclusions | Proposed; target changes no checker byte |
| The historical allowance remains exact | Same section and regression obligation 4 | Baseline checker execution and unchanged transcript path exclusion | Proposed; target changes no allowance |
| Future path authority is finite | `Exact future implementation path inventory` | Exact three-path changed-path and mode audit | Proposed: three paths, no wildcard |
| Tests exercise the real checker | `Required regression coverage` | Disposable local Git fixtures invoke `pathfinder/tests/check-source-policy.sh` | Proposed; no reimplemented policy oracle is accepted |
| Forbidden fixture text is not retained | Regression byte-generation rule | Numeric run-time byte construction and cleanup on every exit | Proposed |
| H0 semantics stay unchanged | `Successor H0 base and identity boundary` | Existing 33-path semantic projection and H0 claim checks | Preserved by plan; no H0 source changes |
| Blocked evidence remains immutable | R8-C status and successor boundary | Exact candidate, parent, tree, mode, blob, size, and offset checks | PASS as Git identity; no candidate byte changed |
| Implementation remains separately gated | R8-C status and effect | Exact human plan decision followed by a separate implementation authorization naming the base and relation | Unsatisfied |

## 5. Review history and resolved findings

### Prior accepted boundaries

1. The responsible human accepted exact original R8 plan target
   `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` on 2026-08-07.
2. A later instruction authorized only non-privileged H0 implementation under
   that plan.
3. The responsible human accepted exact R8-A target
   `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`; acceptance record
   `1f6109f0d0371eb3707e296c3416e8c55235683e` became the historical H0 base.
4. PMR-080 produced blocked exact H0 candidate
   `6e93461f6ea097cb095e31558f6956dc6c0c2708`; it remains unaccepted.

### Finding that required R8-C

The complete PMR-080 gate stopped in the Helium source-policy checker because
Git 2.55.0 classified the static ELF as binary but still reported a match for
arbitrary instruction bytes. The affected checker path is outside accepted
R8-A H0 path authority. The candidate was not modified to grind different
ELF bytes, and the checker was not changed without a reviewed plan.

### Resolved planning questions

- **Revision label:** repository history already uses R8-B at exact object
  `c6e0da62f99a5bf0cb3435f7495129962a3be21b` on a non-ancestor branch, so
  this target uses the next unused label, R8-C. It imports no authority or
  plan semantics from that branch.
- **Classification rule:** content, not filename, suffix, mode, or path.
- **Minimum production behavior:** add binary-ignore semantics only to the
  repository-wide retired-parent `git grep`.
- **Test shape:** one new dependency-free Node.js regression driver invoking
  the real checker, wired by one Makefile command.
- **Documentation decision:** no `pathfinder/docs/` or
  `pathfinder/docs/html/` path is authorized because the command, diagnostic,
  policy contract, and user workflow remain unchanged. A discovered need for
  such a path forces another reviewed revision.
- **Candidate relation:** R8-C acceptance alone grants no implementation
  authority. A later instruction must name an exact approved base and
  direct-child relation; the acceptance-record commit is the only eligible
  default base.

### Open questions requiring human judgment

- Is content-based `git grep -I` treatment the correct narrow policy
  semantics for arbitrary non-text tracked objects?
- Is the exact three-path boundary complete and minimal?
- Is a separate Node.js regression driver preferable to embedding a
  self-test in the production checker?
- Is one new `toolcheck` invocation sufficient to make the regression
  mandatory without changing the build graph?
- Is leaving standalone Helium documentation unchanged justified by the
  unchanged user-facing contract?
- Does excluding the three repository-gate support paths from H0 semantics
  preserve the accepted H0 claim boundary?
- Is the acceptance-record-base plus direct-child successor relation the
  correct default, subject to later explicit implementation authorization?

## 6. Validation and retained evidence

Checks below were run on 2026-09-17 UTC.

| Command or check | Execution boundary | Result and coverage |
| --- | --- | --- |
| `git diff --check fc6795b… f47ae602…` | Exact immutable R8-C target | PASS |
| Exact target inventory and mode audit | Exact immutable R8-C target | PASS: one changed path, `planning/single-hart-runtime-r8-plan.md`, regular mode `100644` |
| Commit, parent, tree, and ancestry resolution | Exact Git objects | PASS: target `f47ae602…`, parent `fc6795b…`, tree `b6470b1…`; accepted R8 and R8-A targets are ancestors |
| `git fsck --no-dangling f47ae602…` | Exact immutable target | PASS |
| Remote branch and tag containment | Exact immutable target | PASS: zero remote branches and zero tags contain the target |
| Blocked candidate identity audit | Exact candidate object | PASS: parent `1f6109f…`, tree `b9fe2f7…`, mode `100755`, blob `3e5d242…`, size 750384 bytes |
| Exact byte-offset inspection | Exact candidate blob | PASS: `83 78 68 00` occurs at offsets 298230 and 306332 |
| Printable-string inspection | Exact candidate blob | PASS: zero printable strings satisfy the retired-parent pattern |
| `LC_ALL=C git grep -nE` against the exact candidate path | Exact candidate tree with current scan semantics | Expected reproduction: Git 2.55.0 reports a binary match |
| `LC_ALL=C git grep -InE` against the exact candidate path | Exact candidate tree with proposed binary-ignore semantics | PASS for the intended correction: no match output |
| Disposable Git fixture probe | Scratch repository, not retained | PASS: generated binary content with the matching bytes is ignored with `-I`; generated genuine text is still reported |
| `npm run docs:build` | Descendant packet/current-position/navigation content | PASS: planning diagrams and 66 Markdown sources built successfully |
| `HE_CHROMIUM=$(command -v chromium-headless-shell) ./be docs-check` | Descendant packet/current-position/navigation/renderer content | PASS: 66 planning sources, 67 planning HTML pages, 66 Chromium-rendered planning pages, 12 Helium sources, 13 Helium HTML pages, and 12 Chromium-rendered Helium pages; Chromium `150.0.7871.186` |

The exact-target Git checks validate the immutable plan target. The Git grep
and scratch-fixture probes validate the feasibility of the proposed semantics;
they are not an implementation test and do not make the current complete
repository gate pass.

The first plain `./be docs-check` invocation completed the planning build and
link checks but stopped because the renderer does not search `PATH` for the
available `chromium-headless-shell`. No dependency was installed. The rerun
used the documented `HE_CHROMIUM` override and passed. Packet and generated
documentation validation applies to descendant decision-support content, not
the exact R8-C plan target and not any future checker implementation.

Retained review evidence consists of:

- the exact target, parent, tree, subject, timestamp, and one-file diff in Git;
- the exact blocked candidate and static-ELF blob identities;
- the exact byte offsets and printable-string result;
- the current and proposed Git grep outcomes;
- this review packet and maintained planning return; and
- generated planning-site derivatives for the packet.

At packet preparation, no checker implementation, regression output, H0
evidence bundle, hardware trace, K3 result, proof, or acceptance record
existed for R8-C. This document now supplies only the acceptance record. No
implementation, successor candidate, hardware result, or new evidence has
been added.

**Current post-decision boundary.** This acceptance-record change is limited
to maintained decision/status Markdown, planning navigation, the browser
render title inventory, and generated planning HTML. Documentation must be
rebuilt and checked before this follow-up is committed. Recording the decision
does not run or satisfy the unchanged complete candidate `make check` gate,
which retains the known binary false-positive failure until separately
authorized implementation.

## 7. Recommended human review sequence

Use an isolated detached worktree:

```sh
git worktree add --detach \
  ../beryllium-r8c-plan-review \
  f47ae60266a467ca1a7704fd9a50b140e0f31bb0
cd ../beryllium-r8c-plan-review
git status --short
git show --no-patch --format=fuller \
  f47ae60266a467ca1a7704fd9a50b140e0f31bb0
git diff --check \
  fc6795b03b5f68849fe5ef882d7e2cae77ab4e90 \
  f47ae60266a467ca1a7704fd9a50b140e0f31bb0
```

1. Confirm the one-file target inventory:

   ```sh
   git diff --name-status \
     fc6795b03b5f68849fe5ef882d7e2cae77ab4e90 \
     f47ae60266a467ca1a7704fd9a50b140e0f31bb0
   ```

2. Review the R8-C plan delta only:

   ```sh
   git diff \
     fc6795b03b5f68849fe5ef882d7e2cae77ab4e90 \
     f47ae60266a467ca1a7704fd9a50b140e0f31bb0 \
     -- planning/single-hart-runtime-r8-plan.md
   ```

3. Check the exact diagnostic table against the blocked candidate:

   ```sh
   git rev-parse \
     6e93461f6ea097cb095e31558f6956dc6c0c2708^ \
     6e93461f6ea097cb095e31558f6956dc6c0c2708^{tree}
   git ls-tree \
     6e93461f6ea097cb095e31558f6956dc6c0c2708 \
     tests/r8/run-make.sh
   git cat-file -s \
     3e5d242fa474be70a708b44b38a155a9a325a562
   ```

4. Review the seven required scanner semantics. Confirm that only content
   classification changes and that the expression, exclusions, transcript
   allowance, diagnostics, and unrelated checks remain exact.
5. Review the three-path future inventory and the explicit decision not to
   authorize Helium documentation or generated paths.
6. Review the generated binary/text regression obligations, especially the
   requirement to invoke the real checker without retaining forbidden text.
7. Review the successor H0 relation and confirm that the blocked candidate is
   evidence only, never amended or reused as an approved base.
8. Confirm that acceptance of the plan would still require separate
   implementation authorization and later exact H0 review.

Remove the isolated worktree after review:

```sh
cd ..
git worktree remove beryllium-r8c-plan-review
```

## 8. Human decision checklist

### Technical review

- [ ] The exact target is
      `f47ae60266a467ca1a7704fd9a50b140e0f31bb0` over parent
      `fc6795b03b5f68849fe5ef882d7e2cae77ab4e90`.
- [ ] The target changes only
      `planning/single-hart-runtime-r8-plan.md`.
- [ ] The diagnostic evidence matches the exact blocked candidate, blob,
      size, mode, byte sequence, and offsets.
- [ ] Text-versus-binary classification is content-based and not
      filename-based.
- [ ] The regular expression, historical transcript allowance, pathspec
      exclusions, diagnostics, and unrelated policy checks remain unchanged.
- [ ] The future implementation boundary is exactly the checker, one Node.js
      regression driver, and one Makefile invocation.
- [ ] The generated tests retain no forbidden text fixture and prove both
      binary non-failure and genuine text failure.
- [ ] The decision not to change Helium documentation or generated Helium
      HTML is acceptable for an unchanged command and policy contract.
- [ ] The three R8-C paths remain outside H0 authority, semantic projection,
      hardware evidence, and claims.
- [ ] Accepted predecessor pins, mechanisms, evidence, runtime, privileged
      code, images, assembly, linker, hardware, H1-H4, root integration, and
      publication state remain untouched.
- [ ] Blocked candidate
      `6e93461f6ea097cb095e31558f6956dc6c0c2708` remains immutable evidence,
      not an approved base.
- [ ] Claims match the evidence: this is planning-only; no checker fix,
      successor H0 candidate, K3 run, or hardware validation exists.
- [ ] Trust assumptions and the open generated-asset finding are acceptable.
- [ ] Successor work remains excluded until the separate gates are satisfied.

### Decision

- [x] **Decision:** accept exact R8-C target
      `f47ae60266a467ca1a7704fd9a50b140e0f31bb0` /
      ~~request revisions~~ / ~~defer~~.

Only the decision box above is checked because that decision was explicitly
supplied by the responsible human on 2026-09-17. The technical-review boxes
remain unchecked as review history. No signature is generated.

## 9. After the decision

### Recorded outcome: the exact commit is accepted

Exact R8-C plan-revision target
`f47ae60266a467ca1a7704fd9a50b140e0f31bb0` (parent
`fc6795b03b5f68849fe5ef882d7e2cae77ab4e90`) was accepted on 2026-09-17 by
the exact instruction quoted above. Packet commit
`0b8fdad1b4052791baae0327c52a37d9ec3a76e1` and this acceptance-record
follow-up are decision support, not plan text or implementation.

Acceptance approves plan text only. The checker remains unchanged, R8-C
implementation authorization remains none, and this decision selects no
implementation base or direct-child relation. Blocked H0 candidate
`6e93461f6ea097cb095e31558f6956dc6c0c2708` remains byte unchanged,
blocked, unreviewed, unaccepted, and not an approved future base. No successor
H0 candidate is authorized or started.

### Prohibited until separate authorization

- No change to `pathfinder/tests/check-source-policy.sh`,
  `pathfinder/Makefile`, or a new regression driver.
- No successor H0 candidate, implementation base, or direct-child relation.
- No change to the blocked H0 candidate, its H0 sources, predecessor pins,
  generated evidence, runtime, image, assembly, linker, root integration, or
  dependencies.
- No H1-H4 work or K3/hardware execution; those remain unauthorized or
  `NOT RUN`.
- No Linux, service, device, DMA, multicore, policy, TE, CHERI, VBS,
  attestation, or later successor work.
- No push, tag, publication, release, clean-repository migration, or
  publication-gate approval change.
- No claim that the open generated-asset reproducibility finding is closed.

### Not taken: request revisions

Had revisions been requested, a new plan commit and review packet would have
been required, and this exact target would not have been treated as accepted.
Checker implementation and successor H0 work would have remained blocked.

### Not taken: defer

Had review been deferred, R8-C would have remained proposed and unaccepted.
The checker, blocked H0 candidate, successor, hardware, and publication states
would have remained unchanged.

---

**Status:** exact R8-C plan target
`f47ae60266a467ca1a7704fd9a50b140e0f31bb0` (parent
`fc6795b03b5f68849fe5ef882d7e2cae77ab4e90`) is **accepted** as of
2026-09-17. Its immutable proposed field remains retained pre-decision
content. R8-C implementation authorization is none; the checker and blocked
H0 candidate are unchanged; no successor H0 candidate is authorized. K3
execution and hardware validation are `NOT RUN`. The generated-asset
reproducibility finding remains open, and push, tag, publication, release,
and migration remain blocked.

**Next:** no implementation or successor action is authorized by this record.
Any future R8-C implementation would require a separate responsible-human
instruction that names an exact approved base and relation.

**Action required from you:** none for this decision. R8-C plan acceptance is
recorded. Implementation, any successor H0 candidate, H1-H4, K3 execution,
publication, and later successor work remain behind their separate gates.
