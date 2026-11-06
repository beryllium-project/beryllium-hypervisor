<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R7 plan revision A review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves the packet-time former private repository identity and remote
> state. The current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

This document began as the decision-support packet for one exact immutable
commit — `0605028220e3795d99393156d0bfb7d6a7d631a4`, which carries **Plan
revision R7-A**, the narrow enumeration of the predecessor acceptance-pin
refreshes that the already accepted R7 plan requires but does not supply — and
now also records the responsible-human decision taken on it. The
decision-support material below is retained unchanged as review history; it
remains the evidence the decision rests on. Except where a statement is
explicitly marked as current, sections 1 through 9 describe the state **at the
time of that decision**.

The earlier R7 plan decision is untouched by this record and remains exact,
complete, and byte unchanged: plan target
`18c43596d308052cfad67edc6e2cb8f543f75600`, responsible-human accepted on
2026-08-05, recorded in
[`single-hart-runtime-r7-plan-review-summary.md`](single-hart-runtime-r7-plan-review-summary.md)
at acceptance-record commit `014b0f654ed65758bb99112f401529975d2dfd44`, which
is also this target's parent.

Revision R7-A changes **no proof obligation, symbol, cut point, claim, tool
lock, retention rule, evidence limit, or non-goal**. It adds one enumeration,
its exact formulas, a re-derivation rule, an ordering, and a validation gate.

**The untracked local `tests/r7/` package is not the review target.** It is
not part of this commit, it was not offered for acceptance here, it is not
accepted, and none of its output is accepted evidence.

## Decision record

Responsible-human review **accepted the exact R7-A plan-revision commit**
`0605028220e3795d99393156d0bfb7d6a7d631a4` (parent
`014b0f654ed65758bb99112f401529975d2dfd44`, the R7 plan acceptance record) on
2026-08-05, in explicit response to the exact acceptance question posed for
that commit by this packet. The recorded selection was:

```text
Accept exact 0605028220e3795d99393156d0bfb7d6a7d631a4
```

The decision date is recorded as **2026-08-05**, the date supplied with the
decision. The target's Git AuthorDate is `2026-08-06T01:44:40+00:00` (UTC);
the two differ only in date convention, not in ordering — the decision
followed the commit it names.

The revised plan, carrying
[Plan revision R7-A](single-hart-runtime-r7-plan.md#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh),
is therefore the **plan of record for R7 predecessor acceptance-pin
enumeration**. The original R7 plan target
`18c43596d308052cfad67edc6e2cb8f543f75600` (accepted 2026-08-05) remains
**accepted history and byte unchanged**; this acceptance adds only the
enumeration, its formulas, its re-derivation rule, its ordering, and its
validation gate, and it moves no proof obligation, symbol, cut point, claim,
tool lock, retention rule, evidence limit, or non-goal.

No new implementation authorization was requested or given here. Blocked R7
root integration **may resume** under the already-recorded R7 authorization
instruction `once complete, commit and push, then commence R7` and the
accepted plan, bounded strictly to:

- editing only root `Makefile`, `be`, and `scripts/check-be.sh`;
- refreshing exactly the **six** enumerated constants and no seventh;
- following the mandatory pre-edit → edit → recompute → re-check → gate
  ordering; and
- **re-deriving every one of the six constants at the exact future R7
  implementation commit** by its own owning checker's computation.

No value observed during the blocked diagnostic, and no scratch value, may be
copied into a checker in place of a re-derived one. If a seventh constant, a
fourth root file, or a predecessor self-test change turns out to be required,
R7 **stops** and requests a further plan revision; that discovery is a plan
defect, never permission to widen the set.

Packet commit `402afc824fde0458bf1dce0c3e291cadc2319fba`
(`docs: prepare exact R7-A plan review`) and this acceptance-record follow-up
are **decision support only**. Neither is plan text and neither is
implementation; the accepted plan-revision target remains exactly
`0605028220e3795d99393156d0bfb7d6a7d631a4` over parent
`014b0f654ed65758bb99112f401529975d2dfd44`, byte unchanged.

The accepted plan text at that immutable target still reports
`r7_plan_revision_r7a=proposed-not-reviewed` in its own current-state block.
That is frozen pre-decision plan content describing the commit as it was
offered; it is preserved unchanged, and this record — together with the
maintained status documents — is the authoritative surface for the decision.

This decision applies only to that exact immutable plan commit. It does
**not** accept any R7 implementation, any local `tests/r7/` work, or any R7
proof, extraction, configuration-trace, report, evaluator, evidence, or
coverage claim; local R7 implementation remains untracked, unreviewed, and
unaccepted. Hardware validation and formal verification of Beryllium remain
`NOT RUN`. R8 remains undefined, gated, not authorized, and not started, and
push, tag, publication, and release remain blocked.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `0605028220e3795d99393156d0bfb7d6a7d631a4` (`docs: propose narrow R7-A pin revision`, AuthorDate 2026-08-06T01:44:40+00:00), parent `014b0f654ed65758bb99112f401529975d2dfd44` (`docs: record exact R7 plan acceptance`). Branch `beryllium/single-hart-runtime-r0`. |
| Prior accepted plan target | `18c43596d308052cfad67edc6e2cb8f543f75600` (parent `2cc6e96413ab4d426bbf2327dc6c9b309b3f3aac`), responsible-human accepted 2026-08-05. It remains **accepted history and byte unchanged**; its packet commit and the acceptance-record commit `014b0f654ed65758bb99112f401529975d2dfd44` are decision support, neither plan revision nor implementation. |
| Current status | Plan revision R7-A is **accepted at that exact target as of 2026-08-05**. At decision time R7 root integration was **blocked** with zero of the six acceptance pins applied and root `Makefile`, `be`, and `scripts/check-be.sh` byte unchanged; **currently** that integration may resume within the accepted enumeration, and no pin has been applied by this record. The `tests/r7/` package exists only as local, untracked, unreviewed, unaccepted work, and every R7 proof, report, and evidence result is local and unaccepted. |
| Decision | Responsible-human acceptance of exact commit `0605028220e3795d99393156d0bfb7d6a7d631a4` on 2026-08-05, by the explicit selection `Accept exact 0605028220e3795d99393156d0bfb7d6a7d631a4`. Packet commit `402afc824fde0458bf1dce0c3e291cadc2319fba` and this acceptance-record follow-up are decision support, neither plan text nor implementation. |
| Successor status | R8 is gated, undefined, not authorized, and **not started**. No R7 implementation review packet, evidence bundle, coverage figure, or acceptance record is requested, recorded, or implied here. |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`. The target is local, unpushed, and untagged: zero remote branches and zero tags contained it at decision time. Push, tag, publication, and release remain blocked. |

**Action taken:** the responsible human decided on exact plan-revision commit
`0605028220e3795d99393156d0bfb7d6a7d631a4` and accepted it. That acceptance
covers **plan text only** and authorizes resuming root integration strictly
under the six enumerated, re-derived pins; it accepts no R7 implementation, no
R7 evidence, and no successor package.

## 2. Deliverables and exact inventory

The parent delta is **87 changed entries, 686 insertions, 338 deletions**:
seven non-generated source paths and 80 generated `docs/html/` entries (8 of
the 87 entries are renames of hash-named assets). No `tests/` file, no
`include/`, `virt/`, or `arch/` file, no root `Makefile`, `be`, or
`scripts/check-be.sh` change, no acceptance-pin constant, no `build/`
artifact, no `pathfinder/` file, and no `pathfinder/publication-gate.conf`
change is present.

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary human question |
| --- | --- | --- | --- | --- |
| Plan revision R7-A | `planning/single-hart-runtime-r7-plan.md` (+267 / -14) | Add [Plan revision R7-A](single-hart-runtime-r7-plan.md#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh) and thread it through the package boundary, commands, acceptance gates, and current state: the defect statement, the six-constant enumeration, the exact binding formulas, the re-derivation rule, the mandatory ordering, and the pre-review validation gate. | Plan text only. It creates no privileged surface, links no image, edits no checker, and executes nothing. | Is exactly six the right set — sufficient for the already accepted root-integration edits, and minimal in that no member can be dropped? |
| Current-position records | `.github/copilot-instructions.md` (+35 / -11), `README.md` (+11 / -5), `planning/README.md` (+17 / -6), `planning/HANDOFF.md` (+29 / -10), `planning/implementation-plan.md` (+25 / -14), `planning/roadmap.md` (+21 / -9) | State plan-accepted-at-`18c4359…`, revision R7-A proposed and not reviewed, package complete only locally and unaccepted, root integration blocked, `r7_acceptance_pins_applied=0-of-6`. | Markdown is authoritative; these are status records, not authority. | Does every status surface avoid implying that R7-A, the local package, or any R7 result is accepted? |
| Generated planning site | `docs/html/**` (80 entries) | Render the changed authoritative Markdown. | Derivative, non-normative output; hash-named asset byte reproducibility remains an **open unresolved finding**. | Is rendering functional without treating generated-asset churn as resolved? |

### Non-generated paths in the target

```text
.github/copilot-instructions.md
README.md
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/roadmap.md
planning/single-hart-runtime-r7-plan.md
```

Reproduce the inventory without interpretation:

```sh
git diff --name-status -M 014b0f654ed65758bb99112f401529975d2dfd44 0605028220e3795d99393156d0bfb7d6a7d631a4
git diff --shortstat 014b0f654ed65758bb99112f401529975d2dfd44 0605028220e3795d99393156d0bfb7d6a7d631a4
git diff --numstat -M 014b0f654ed65758bb99112f401529975d2dfd44 0605028220e3795d99393156d0bfb7d6a7d631a4 -- . ':!docs/html'
```

The parent acceptance-record commit changed **no byte** of
`planning/single-hart-runtime-r7-plan.md`, so the decision delta measured
against the **accepted plan target** is the identical `+267 / -14`:

```sh
git diff --numstat 18c43596d308052cfad67edc6e2cb8f543f75600 0605028220e3795d99393156d0bfb7d6a7d631a4 -- planning/single-hart-runtime-r7-plan.md
git diff 18c43596d308052cfad67edc6e2cb8f543f75600 0605028220e3795d99393156d0bfb7d6a7d631a4 -- planning/single-hart-runtime-r7-plan.md
```

This packet file itself, and the two documentation-integration edits that make
it navigable and browser-checked (`planning/.vitepress/config.mts`,
`pathfinder/tests/check-docs-render.mjs`), are **not** in the reviewed target.
They are later decision-support content in packet commit
`402afc824fde0458bf1dce0c3e291cadc2319fba`, and this acceptance record is a
further follow-up to it; neither is plan text and neither is implementation.

## 3. Claim boundary

### What the exact target supports saying

- The accepted R7 plan authorizes root integration of `Makefile`, `be`, and
  `scripts/check-be.sh` while requiring any predecessor acceptance-pin update
  to be enumerated before it is applied, and it enumerates none.
- Revision R7-A supplies exactly six enumerated constants, their owning
  checkers, their bound files, their exact binding formulas, a re-derivation
  rule, a mandatory ordering, and a pre-review validation gate.
- Revision R7-A applies **zero** pins, edits **zero** checkers, and edits
  **zero** root files. Verified read-only: the target's changed-path inventory
  contains no `tests/` or root build-surface path, and the working tree at
  packet time carries zero tracked modifications.
- The plan document now separates accepted plan text from an unreviewed
  proposal and marks the local implementation and its measurements as
  unaccepted.

### What it does not support saying

- That any pin value is known, correct, or pinned. **No value is pinned by
  this revision**, and no value observed during the blocked diagnostic may be
  copied into a checker.
- That six is proved sufficient or minimal. That conclusion is *local,
  unreviewed implementation discovery*, not evidence, and it must be
  re-established at the exact future implementation commit.
- That the local `tests/r7/` package is complete in any accepted sense, that
  its proof, report, or evidence output is valid, or that R7 has any result.
- That any R0-R6 acceptance checker has been re-run and still passes after a
  refresh; no refresh exists.
- That Beryllium is formally verified. R7's supportable claim, when and if
  earned, remains the bounded statement in
  [Supportable completion claim](single-hart-runtime-r7-plan.md#supportable-completion-claim).

### Trusted or assumed

- The accepted predecessor checkers (`tests/r1/check-acceptance.sh`,
  `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs`)
  bind the three root files by exact content and mode as described, and the
  accepted R6 manifest `tests/r6/acceptance-pins.mjs` measures the same six
  pins. This packet points at those files for read-only confirmation; it runs
  no checker and claims no execution result.
- Git object identity, `sha256sum`/`stat` behavior, and the Node `createHash`
  concatenation used by the R3/R4 delta formula.
- Everything the accepted plan already trusts: bounded local ISA semantics,
  the ELF parser with its independent objdump cross-check, the Rocq kernel and
  host, the C cut points, surrounding compiler and linker output, OpenSBI,
  QEMU, and the fixed single-hart/no-device/no-DMA profile.

### Explicit non-claims

- Hardware validation is `NOT RUN`; formal verification of Beryllium is not
  claimed.
- No R7 tool, extraction, proof, report, evaluator, evidence, or QEMU result
  is accepted; all such local output is unreviewed discovery.
- The open generated-asset byte-reproducibility finding remains unresolved.
- Nothing here authorizes R8, Linux, services, devices, interrupts,
  multicore, CHERI, Type Enforcement, attestation, an MVP, a tag, a push,
  publication, or release.

## 4. Security and correctness invariants

| Invariant | Where the target states it | Enforcement point | Status |
| --- | --- | --- | --- |
| Accepted mechanism immutability except the six constants | [What this revision does not change](single-hart-runtime-r7-plan.md#what-this-revision-does-not-change); acceptance gate 2 | R1-R6 acceptance checkers over `include/`, `virt/`, `arch/`, `tests/r0/`-`tests/r6/` | Forward obligation; nothing changed yet |
| Fail-closed pin accounting (never partial) | [Mandatory ordering](single-hart-runtime-r7-plan.md#mandatory-ordering) | Accepted `tests/r6/acceptance-pins.mjs`: a pin is `required` when its bound file differs from accepted R5 content, `applied` only when recorded equals recomputed; a count that is neither `0` nor the full set is refused | Currently `0-of-6`, the clean state |
| Re-derivation at the exact candidate | [Re-derivation rule](single-hart-runtime-r7-plan.md#re-derivation-rule) | Each owning checker recomputes its own constant from committed content | Forward obligation; no value pinned |
| Mode invariance | [Exact binding formulas](single-hart-runtime-r7-plan.md#exact-binding-formulas) | R3/R4 checkers reject a target-to-current mode change outright; R1 keeps `successor_makefile_mode=644` untouched | Unchanged |
| No seventh constant, no fourth root file | [Authorized refresh](single-hart-runtime-r7-plan.md#authorized-refresh-exactly-six-constants-no-others) | Stop-and-revise rule; R6 manifest asserts the authorized pin count and ordering | Stated, untested |
| Historical vs live R7 authority keys stay distinct | [Required validation](single-hart-runtime-r7-plan.md#required-validation-before-an-r7-candidate-is-reviewable) | `scripts/check-be.sh` and the accepted R6 rule preserving the historical `r7_authorization` line exactly once | Preserved; no wrapper byte changed |
| Successor and publication exclusion | [Explicit non-goals](single-hart-runtime-r7-plan.md#explicit-non-goals); [Current state](single-hart-runtime-r7-plan.md#current-state) | Repository publication gate and this decision's stated limits | R8 not started; publication blocked |

## 5. Review history and findings

### The defect being corrected

The accepted [package boundary](single-hart-runtime-r7-plan.md#package-boundary)
permits root integration limited to root `Makefile` targets, `be`,
`scripts/check-be.sh`, maintained documentation sources, and generated
planning HTML — and then requires that *any* predecessor acceptance-pin update
"must be enumerated before it is applied", declaring an update outside the
enumerated set "a plan defect, not permission to widen the implementation".

The accepted plan enumerates none. Because accepted predecessor checkers bind
all three root files by exact content and mode, the accepted plan
simultaneously authorizes root integration and forbids the only way to perform
it. The accepted rule names its own remedy — a revision, not a widened
implementation — and R7-A supplies exactly that enumeration and nothing else.

### The blocked diagnostic and its status

Root integration was attempted once in an isolated working copy to **measure,
not to apply**, the binding. Its diff is retained only as ephemeral local
scratch at `build/r7-root-integration-blocked.patch`, which is git-ignored
generated output and is not part of any package, commit, or evidence bundle.
**No tracked root file was edited and no acceptance-pin constant was
recomputed into any checker.** The only working-tree change from the R7 work
is the untracked `tests/r7/` package.

The diagnostic observed that the R7 launcher, `r7-check`/`r7-evidence`
targets, `check`/`clean` participation, help and status text, and wrapper
assertions require edits to exactly the three root files the accepted plan
already lists; that three accepted predecessor checkers bind those files,
producing exactly six constants; that the accepted R6 manifest
`tests/r6/acceptance-pins.mjs` already enumerates the identical six and
hard-fails a partial refresh; and that no seventh constant, fourth root file,
or predecessor self-test change appeared necessary.

**Status of those findings: unreviewed local implementation discovery.** They
are not retained R7 evidence, they are not accepted, and no value measured
during the diagnostic is pinned by this revision or may be carried into an
implementation commit as if it were already checked. The sufficiency and
minimality conclusion must be re-established by running the acceptance
checkers and the R3/R4/R5 negative suites at the exact implementation
candidate.

### The authorized refresh: exactly six constants

| # | Owning checker (file edited) | Constant | Bound file | Reason the refresh becomes required |
| --- | --- | --- | --- | --- |
| 1 | `tests/r1/check-acceptance.sh` | `successor_makefile_sha256` | root `Makefile` | the root `Makefile` gains `r7-check`/`r7-evidence` and the R7 `check`, `evidence-check`, and `clean` steps |
| 2 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` for `tests/r1/check-acceptance.sh` | `tests/r1/check-acceptance.sh` | constant 1 changed that file |
| 3 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` for `be` | `be` | `be` gains the R7 launcher binding, subcommands, help, status, version, and clean participation |
| 4 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` for `scripts/check-be.sh` | `scripts/check-be.sh` | `scripts/check-be.sh` gains the R7 wrapper assertions |
| 5 | `tests/r4/check-accepted-content.mjs` | `approvedDeltaSha256` for `be` | `be` | same `be` edit, second binding |
| 6 | `tests/r4/check-accepted-content.mjs` | `approvedDeltaSha256` for `scripts/check-be.sh` | `scripts/check-be.sh` | same `scripts/check-be.sh` edit, second binding |

**The no-seventh rule.** This is the complete authorized set; nothing may be
added, removed, or reordered. The R1 accepted-commit and
`successor_makefile_mode` constants, the R3/R4 accepted-commit, accepted-date,
parent, and review-packet constants, every `immutablePaths` entry, every other
`mixedFiles` entry, every `addedFiles` entry, and every R2, R5, and R6
acceptance surface stay exactly as accepted. If implementation shows that a
seventh constant, a fourth root file, or a predecessor self-test change is
required, **R7 stops and requests a further revision**; that discovery is a
plan defect, never permission to widen the set.

### The exact binding formulas

Constants 2 through 6 are the mixed approved target-to-current delta the
owning checker computes as:

```text
SHA-256( target mode || NUL || current mode || NUL
         || target bytes || NUL || current bytes || NUL )
```

Each of the four parts is followed by a single `0x00` byte; the modes are the
git regular-file strings `100644` or `100755`; the target mode and bytes come
from that checker's own accepted commit —
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` for
`tests/r3/check-accepted-content.mjs` and
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` for
`tests/r4/check-accepted-content.mjs` — and the current mode and bytes come
from the worktree at the exact R7 implementation candidate. A target-to-current
mode difference is a failure, never a value to re-pin.

Constant 1 is **not** that formula. `tests/r1/check-acceptance.sh` keeps its
existing successor mode-and-content form: the root `Makefile` mode read with
`stat -c '%a'` must equal the unchanged pinned `644`, and
`successor_makefile_sha256` must equal the plain `sha256sum` of the root
`Makefile` bytes at the exact candidate. Only the SHA-256 constant is
refreshed; the mode constant is not touched.

### Open questions requiring human judgment

These questions were posed for the decision and are retained as review
history. The recorded acceptance decided the exact commit; it annotated no
individual answer, and automation infers none.

1. **Is enumeration-by-revision the right remedy?** The alternative readings
   are to treat the accepted boundary as implicitly permitting the pins, or to
   re-plan root integration entirely. R7-A takes the narrowest reading the
   accepted plan itself prescribes.
2. **Is six right?** Sufficiency and minimality rest on unreviewed local
   measurement plus the accepted R6 manifest's identical enumeration. Neither
   is accepted evidence here.
3. **Is the forward re-derivation discipline strong enough** given that the
   values are deliberately absent from this commit and can only be checked at
   a future implementation candidate?
4. **Is the pre-review validation gate** in
   [Required validation](single-hart-runtime-r7-plan.md#required-validation-before-an-r7-candidate-is-reviewable)
   the right bar for a future R7 candidate to be reviewable at all?

### Closed in this target

- The plan no longer states that the `./be` R7 delegations exist; it records
  that only the local untracked launcher exists and that root integration is
  blocked.
- The plan's current-state block no longer reports `r7_implementation=not-started`;
  it reports the measured local, unaccepted position, including
  `r7_acceptance_pins_applied=0-of-6`.
- Every maintained status surface was updated in the same commit, so no record
  claims implementation or revision acceptance.

## 6. Validation and evidence boundary

| Command | Result | What it covers | Execution boundary |
| --- | --- | --- | --- |
| `npm run docs:build` | PASS, 2026-08-05 session | VitePress build of the maintained planning Markdown, including the revised plan | Ran on the content that became this exact target, **before** the commit was created; the target's `docs/html/**` is that build's output |
| `./be docs-check` | PASS, 2026-08-05 session | Planning build, HTTP build, link/target/portability check, and direct-file browser rendering, plus the separately labeled Helium documentation gate | Same pre-commit content boundary |
| `git diff --check 014b0f6…​ 0605028…` | PASS, clean | No whitespace or conflict-marker damage in the parent→target delta | Re-run read-only at the exact immutable target while preparing this packet |

This is **documentation and plan validation only**. It establishes that the
revised plan text builds, renders, and links; it establishes nothing about R7.

Not run, not claimed, and explicitly excluded from the acceptance basis:

- every R7 tool, extraction, disassembly cross-check, proof, configuration
  trace, report, evaluator, evidence, and QEMU result — the local `tests/r7/`
  outputs are unreviewed local discovery;
- any acceptance-checker run after a pin refresh, because no refresh exists;
- `make check` and the component gates at this target, which this packet does
  not claim; and
- hardware validation, which remains `NOT RUN`.

Corroboration a reviewer can obtain read-only, without accepting anything:

```sh
grep -n 'successor_makefile_mode\|successor_makefile_sha256' tests/r1/check-acceptance.sh
grep -n "path: '" tests/r3/check-accepted-content.mjs
grep -n "path: '" tests/r4/check-accepted-content.mjs
git show 7ba3649f03cf13b65df33020e345d361cce2993a:tests/r6/acceptance-pins.mjs | sed -n '1,60p'
git status --porcelain            # expect only: ?? tests/r7/
```

**Current post-decision boundary.** This acceptance record changes maintained
Markdown, planning navigation labels, and the browser-render title inventory
only. Those documentation sources must be rebuilt and re-checked
(`npm run docs:build`, `./be docs-check`) before the acceptance-record commit
is made; no execution result for that rebuild is claimed here. Recording this
decision executed no R7 tool, no acceptance checker, and no pin refresh, and
it adds no evidence to the accepted target.

## 7. Recommended human review sequence

This sequence is retained as review history; it is the read-only path the
completed review followed, and it can be reproduced without changing anything.
Use an isolated detached worktree so the untracked `tests/r7/` tree cannot
affect what you read.

1. **Identity and boundary.** Confirm the target, its parent, the private
   repository state, and that no remote ref or tag contains it.
2. **The decision delta.** Read the plan delta against the accepted plan
   target `18c43596d308052cfad67edc6e2cb8f543f75600` first; it is the
   decision, and it is the same `+267 / -14`.
3. **The defect.** Read
   [The defect in the accepted plan](single-hart-runtime-r7-plan.md#the-defect-in-the-accepted-plan)
   against the accepted
   [package boundary](single-hart-runtime-r7-plan.md#package-boundary). Judge
   whether the accepted text really does authorize and forbid the same edit.
4. **The enumeration.** Read
   [Bound files and binding checkers](single-hart-runtime-r7-plan.md#bound-files-and-binding-checkers)
   and
   [Authorized refresh](single-hart-runtime-r7-plan.md#authorized-refresh-exactly-six-constants-no-others).
   Judge sufficiency, minimality, and the no-seventh stop rule.
5. **The formulas.** Read
   [Exact binding formulas](single-hart-runtime-r7-plan.md#exact-binding-formulas)
   and check them against the checkers themselves, including that constant 1
   is deliberately a different form and that the mode constant is untouched.
6. **The forward discipline.** Read
   [Re-derivation rule](single-hart-runtime-r7-plan.md#re-derivation-rule),
   [Mandatory ordering](single-hart-runtime-r7-plan.md#mandatory-ordering),
   and
   [Required validation](single-hart-runtime-r7-plan.md#required-validation-before-an-r7-candidate-is-reviewable).
7. **The non-evidence boundary.** Read
   [What the isolated diagnostic established, and its status](single-hart-runtime-r7-plan.md#what-the-isolated-diagnostic-established-and-its-status)
   and
   [R7 package state under this revision](single-hart-runtime-r7-plan.md#r7-package-state-under-this-revision);
   confirm the local measurements are excluded from the acceptance basis.
8. **Unchanged scope.** Spot-check that objective, supportable claim, exact
   inputs, linked-byte scope, proof obligations, tool/trust boundary, report
   and retention, and non-goals are preserved.
9. **Status surfaces.** Confirm no status document claims that R7-A, the local
   package, or any R7 result is accepted.

```sh
git show -s --format=fuller 0605028220e3795d99393156d0bfb7d6a7d631a4
git branch -r --contains 0605028220e3795d99393156d0bfb7d6a7d631a4
git tag --contains 0605028220e3795d99393156d0bfb7d6a7d631a4
git diff --check 014b0f654ed65758bb99112f401529975d2dfd44 0605028220e3795d99393156d0bfb7d6a7d631a4
git diff --name-status -M 014b0f654ed65758bb99112f401529975d2dfd44 0605028220e3795d99393156d0bfb7d6a7d631a4

# The decision delta: revised plan against the accepted plan target.
git diff 18c43596d308052cfad67edc6e2cb8f543f75600 0605028220e3795d99393156d0bfb7d6a7d631a4 -- planning/single-hart-runtime-r7-plan.md

# Status surfaces only.
git diff 014b0f654ed65758bb99112f401529975d2dfd44 0605028220e3795d99393156d0bfb7d6a7d631a4 -- README.md planning/README.md planning/HANDOFF.md planning/implementation-plan.md planning/roadmap.md .github/copilot-instructions.md

# Isolated read-only inspection at the exact target.
git worktree add --detach .review-r7a 0605028220e3795d99393156d0bfb7d6a7d631a4
(cd .review-r7a && sed -n '/^## Plan revision R7-A/,/^## Objective/p' planning/single-hart-runtime-r7-plan.md)
(cd .review-r7a && sed -n '/^## Package boundary/,/^## Exact linked-byte scope/p' planning/single-hart-runtime-r7-plan.md)
(cd .review-r7a && git status --porcelain && ./be status)
git worktree remove .review-r7a
```

The decision-support material for the accepted plan target remains in
[`single-hart-runtime-r7-plan-review-summary.md`](single-hart-runtime-r7-plan-review-summary.md);
this packet does not restate or replace it.

## 8. Human decision checklist

The technical-judgment items below remain unchecked as review history. Only
the explicitly supplied decision is marked; automation does not answer,
pre-check, or sign for the questions, and checking them is not inferred from
the decision. No signature is generated on the responsible human's behalf.

- [ ] **The defect is real.** The accepted plan genuinely authorizes root
  integration of `Makefile`, `be`, and `scripts/check-be.sh` while enumerating
  no acceptance-pin update, and a revision — not a widened implementation — is
  the correct remedy it names.
- [ ] **The enumeration is right.** Exactly six constants, with those owners
  and bound files, are sufficient for the already accepted root-integration
  edits and minimal in that dropping any one leaves a bound file edited
  without its matching constant.
- [ ] **The no-seventh rule is acceptable.** A seventh constant, a fourth root
  file, or a predecessor self-test change stops R7 and forces another
  revision, rather than widening the set at implementation time.
- [ ] **The formulas are right.** The four-part NUL-delimited target-to-current
  delta, its two accepted target commits, the mode-difference-is-failure rule,
  and constant 1's distinct `stat`/`sha256sum` form with an untouched `644`
  mode constant are accurate.
- [ ] **The forward discipline is strong enough.** Every constant must be
  re-derived at the exact implementation candidate; diagnostic and scratch
  values are explicitly not pinned and must not be copied.
- [ ] **The evidence boundary is acceptable.** The sufficiency/minimality
  finding is local, unreviewed implementation discovery, excluded from the
  acceptance basis, and subject to re-establishment at the exact candidate.
- [ ] **Scope is unchanged.** No proof obligation, symbol, cut point, claim,
  tool lock, retention rule, evidence limit, or non-goal moved; no accepted
  R0-R6 byte changed; no pin was applied.
- [ ] **Status surfaces are honest.** No record implies that R7-A, the local
  untracked `tests/r7/` package, or any R7 proof, report, or evidence result
  is accepted.
- [ ] **Successor work remains excluded.** R8, hardware validation, formal
  verification, tag, push, publication, and release remain prohibited.
- [x] **Decision:** accept exact commit
  `0605028220e3795d99393156d0bfb7d6a7d631a4` / ~~request revisions~~ /
  ~~defer~~.

Only the decision box above is checked, because that decision was explicitly
supplied by the responsible human on 2026-08-05. No signature is generated.

## 9. After the decision

### Recorded outcome: the exact commit is accepted

Exact plan-revision target `0605028220e3795d99393156d0bfb7d6a7d631a4` (parent
`014b0f654ed65758bb99112f401529975d2dfd44`) was accepted on 2026-08-05, and
this record names that SHA and date. Packet commit
`402afc824fde0458bf1dce0c3e291cadc2319fba` and this acceptance-record
follow-up are decision support, not plan text and not implementation.

The revised plan is now the plan of record for R7 predecessor acceptance-pin
enumeration, and blocked R7 root integration **may resume** under the
**already recorded** R7 authorization instruction (`once complete, commit and
push, then commence R7`) and the accepted plan, strictly bounded to:

- editing only root `Makefile`, `be`, and `scripts/check-be.sh`;
- refreshing exactly the six enumerated constants and nothing else; and
- following the mandatory pre-edit → edit → recompute → re-check → gate
  ordering.

Every one of the six constants must be **re-derived at the exact future R7
implementation commit** by its own owning checker's computation. A constant
that was not recomputed there is a defect even if it happens to match, and no
diagnostic or scratch value may be copied into a checker in place of a
re-derived one.

If a seventh constant, a fourth root file, or a predecessor self-test change
turns out to be required, R7 **stops** and requests a further revision.

Acceptance of this revision accepts **no** R7 implementation, no local
`tests/r7/` work, and no R7 proof, report, evidence, or coverage claim. Local
R7 implementation remains untracked, unreviewed, and unaccepted, and a
complete R7 implementation still requires its own exact-commit review packet
and its own separate acceptance.

### Prohibited until separate authorization

- No R7 tag, private push, public release, or change to
  `pathfinder/publication-gate.conf`.
- No R8 start; R8 remains undefined, gated, and not authorized.
- No acceptance of any R7 implementation, and no presentation of local
  `tests/r7/` output as accepted R7 evidence.
- No modification of any accepted R0-R6 byte beyond the six enumerated
  constants this revision authorizes.
- No copying of a diagnostic or scratch value into a checker in place of a
  re-derived one.
- No hardware-validation or formal-verification claim; both remain `NOT RUN`.
- The open generated-asset byte-reproducibility finding remains unresolved;
  this acceptance does not resolve it.

### Not taken: request revisions

Had revisions been requested, a new commit and a new review packet would have
been prepared, this SHA would not have been treated as accepted, root
integration and the pin refresh would have stayed blocked, no pin would have
been applied, and no dependent work would have started.

### Not taken: defer

Had the decision been deferred, plan target
`18c43596d308052cfad67edc6e2cb8f543f75600` would have stayed the only accepted
R7 plan text, revision R7-A would have stayed unaccepted, root integration
would have stayed blocked at `0-of-6` pins applied, the local package would
have stayed unreviewed and unaccepted, and no dependent work would have
started.

---

**Status:** exact plan-revision target
`0605028220e3795d99393156d0bfb7d6a7d631a4` (parent
`014b0f654ed65758bb99112f401529975d2dfd44`) is **accepted** as of 2026-08-05.
The R7 plan target `18c43596d308052cfad67edc6e2cb8f543f75600` remains accepted
history, exact and byte unchanged. R7 root integration may now resume within
the accepted six-constant enumeration; no pin is applied by this record, and
root `Makefile`, `be`, and `scripts/check-be.sh` are byte unchanged. The
`tests/r7/` package exists only as local, untracked, unreviewed, unaccepted
work, and no R7 proof, report, evidence, or coverage result is accepted. R8 is
not started; hardware validation and formal verification are `NOT RUN`; push,
tag, publication, and release remain blocked.

**Next:** bounded R7 root integration may resume under the already-recorded R7
authorization and the accepted revised plan, limited to the three root files
and the six enumerated constants, with every constant re-derived at the exact
implementation commit and every fail-closed gate enforced rather than relaxed.
No local implementation result may be presented as accepted R7 evidence, and
completion of R7 requires its own exact-commit review and separate acceptance.

**Action required from you:** none for this decision. Plan-revision acceptance
is recorded. R7 implementation acceptance, R7 evidence claims, R8, hardware
validation, tagging, pushing, publication, and release all remain prohibited
without separate explicit authorization.
