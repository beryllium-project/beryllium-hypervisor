<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R6 adversarial-image evidence

## Status and evidence boundary

This is an implementation and evidence record, not the decision record. The
responsible-human decision is recorded in
`planning/single-hart-runtime-r6-review-summary.md`: exact target
`7ba3649f03cf13b65df33020e345d361cce2993a` was accepted on 2026-08-05.
The evidence below remains the pre-decision exact-target evidence boundary.

- The R6 plan and exact implementation target are responsible-human accepted.
  Its integration state is **measured, never assumed**: the package is a
  complete, locally checked working tree that reports
  `r6_integration=local-only-uncommitted` while no `tests/r6` path is tracked
  at `HEAD`, and   `r6_integration=committed-accepted-content` after the acceptance record when
  immutable package content matches the exact accepted target.
- `tests/r6/check-acceptance.sh` reports `r6_implementation=complete-local`,
  the measured `r6_integration` value for the current tree
  (`local-only-uncommitted` before the package is tracked,
  `committed-candidate-not-accepted` after),
  `r6_evidence_claim=complete-local-not-reviewed`,
  `r6_acceptance=not-reviewed`, and `r6_accepted_commit=none` in **both**
  states.
- `r6_evidence_claim` is **derived** from the measured `r6_implementation`
  state, never asserted. The mapping is total and fixed:

  | measured `r6_implementation` | derived `r6_evidence_claim` |
  | --- | --- |
  | `not-complete` | `not-generated` |
  | `report-generated` | `report-generated-not-reviewed` |
  | `complete-local` | `complete-local-not-reviewed` |

  No state maps to a claim above itself, no state maps to a reviewed, accepted,
  or published claim, and an unrecognised state is a refusal rather than a
  default. `tests/r6/check-acceptance.sh`, `be`, `scripts/check-be.sh`, and
  `tests/r6/check-report.mjs` all apply this one mapping, and each *checks*
  consistency instead of demanding the complete value, so a clean tree with no
  generated report reports `not-generated` and still passes.
- The source state is **measured, not asserted**. The report and
  `check-acceptance.sh` count the package paths Git actually tracks at `HEAD`
  (`git ls-tree -r --name-only HEAD -- tests/r6`), publish that count as
  `package.head_tracked_r6_paths`, and derive both the package state and
  `r6_integration` from it:

  | measured `head_tracked_r6_paths` | derived `package.state` | derived `r6_integration` |
  | --- | --- | --- |
  | `0` | `local-uncommitted` | `local-only-uncommitted` |
  | `> 0` | `committed-not-accepted` | `committed-candidate-not-accepted` |

  Committing the package is therefore no longer a hard failure, and it is also
  no longer an acceptance: both derived states keep `r6_acceptance=not-reviewed`
  and `r6_accepted_commit=none`, and `package.r6_accepted_implementation_commit`
  stays `none` in either state. A published count that disagrees with the
  measured one, a state that does not follow from the count, and an
  acceptance-shaped state such as `committed-accepted` are all refusals.
  `tests/r6/test-committed-state.mjs` proves this over three isolated temporary
  Git repositories rather than by argument, and it measures this tree rather
  than assuming it is uncommitted, so every case in it keeps testing once the
  package is committed. The report additionally publishes the exact
  `git status --porcelain -- tests/r6` entries it measured, and the independent
  checker re-measures them and compares the published array entry by entry.
- The implementation is committed at exact candidate target
  `7ba3649f03cf13b65df33020e345d361cce2993a`, whose parent
  `9ed5ad7069b6067f03e1923c09937fe218240a59` is the initial implementation
  commit over accepted-plan base `4012d794e769fd4029b11f6f45e366ed0ef117f5`,
  and `planning/single-hart-runtime-r6-review-summary.md` is the
  decision-neutral review packet prepared for that exact target. The packet
  records no decision, the packet's own commit is decision support rather than
  implementation, and nothing in this document or that packet may be read as
  responsible-human acceptance, authorization, or approval.
- R7 is `not-authorized` and `not-started`. Hardware validation is **NOT RUN**.
  Formal verification is **NOT RUN** and not claimed. Push, tag, publication,
  and release remain **blocked**.

`be status` prints two distinct authorization statements and they must not be
confused:

| Field | Value | Meaning |
| --- | --- | --- |
| `r6_authorization` | `not-authorized` | historical line emitted verbatim by the **accepted R5 package**, `tests/r5/check-acceptance.sh`; it is a frozen accepted byte and is never rewritten |
| `r6_authorization_source` | `accepted-r5-package-historical` | provenance of the line above |
| `r6_package_authorization` | `authorized` | live R6 field: the responsible human accepted an exact R6 plan commit and separately authorized R6 implementation work |

The historical R5 line records the state at R5 acceptance time, when R6 had not
yet been authorized. It is preserved byte for byte because R5's accepted bytes
are immutable. The live field records the current state. `be status` prints
`r6_authorization=` exactly once, and `scripts/check-be.sh` asserts both that
uniqueness and the exact value of each field.

## Plan and acceptance identities

| Identity | Commit | Note |
| --- | --- | --- |
| Original accepted plan | `609867fdad75279c0913022909efd65c4a838909` | acceptance record `4bff41764cf8ec9275e771cd3c1ce124961da93a`, review packet `21cf80daa2021590378de81d7a094e14f4e5c8ca` |
| Plan revision R6-A (D-15 injection site) | `75269f058ae578b0a76a113d6c05c0aaceeac8ec` | acceptance record `4d6c3c9b0899c7a30b2150ff0d4067369ccef774`, packet `fd3e18477da24868edb53d492a0ed7d2636ac79d` |
| Plan revision R6-B (D-15 image layout and trace retention) | `6d6464c6c937abccd59df932006c1049fd79fac6` | **current accepted plan target**, accepted 2026-07-30 |
| Latest acceptance record HEAD | `4012d794e769fd4029b11f6f45e366ed0ef117f5` | decision record; not implementation |
| R6-B review packet | `325117f4b2d2bac4a864221d3457295f8ff385ab` | decision support; not implementation |
| Accepted R5 baseline | `165f4d001a2b59b582b397bdea79ec4826168fdb` | parent `9312c1355a23d411e3bdafb2183be342683a8ab9` |
| Accepted R6 implementation commit | `7ba3649f03cf13b65df33020e345d361cce2993a` | parent `9ed5ad7069b6067f03e1923c09937fe218240a59`; accepted 2026-08-05 |

The accepted plan text is `planning/single-hart-runtime-r6-plan.md`
(SHA-256 `6e5ce90fe75391fc65899cf198048f515ce4298dd019b6d0e8b3836d5379dc32`
in this worktree). The R6 report refuses any other plan, revision, decision
record, or packet identity.

The accepted R5 baseline is verified on every run: `r5_acceptance=accepted`,
`r5_accepted_mechanism_match=yes`, 116 immutable accepted paths byte-and-mode
unchanged, and an unchanged R5 implementation content digest
`a26fcf98375ccb665c025fc8a7514f9c73b9c6b406ba518cc62154f9a1908b9c`.

## Test-only package: no new production surface

R6 adds **no** production runtime code. It adds no source file under
`arch/`, `include/`, or `virt/`, no `BE_R6_*` runtime identifier, no new image,
no new privileged instruction, and no new guest-visible behavior. `be status`
reports `r6_surface=test-only-no-production-runtime-change`, and
`tests/r6/check-sources.mjs` proves `production-surfaces=0` and
`r6-identifiers=0` against the accepted R0-R5 sources.

R6 measures the accepted R5 mechanism; it never modifies it. The accepted R5
image checker, linker script, source inventory, parity checker, and host
mechanism are the *instrument*, and each adversarial fixture is an *input* to
that instrument.

## What changed outside `tests/r6/`

The complete change set of this worktree, by scope, measured from
`git status --porcelain` rather than asserted. Nothing outside these six scopes
changed. Counts are the measured state at the time this record was written; the
generated-documentation scope is build output and its exact count moves with
every documentation build.

`./be docs-check` in the [complete gate](#reproducible-commands) below
regenerates and validates **both** documentation sites: the planning site into
`docs/html/` and the Helium/pathfinder site into `pathfinder/docs/html/`. Only
the planning output is a scope of this change. Running the full check leaves
incidental Helium-site build churn in the worktree; that churn is unrelated to
R6, is not a scope below, and is restored after every run
(`git checkout HEAD -- pathfinder/docs/html`, then deletion of the newly
hashed, untracked assets it leaves behind), so
`git status --porcelain -- pathfinder/docs/html` reports nothing.
`pathfinder/tests/check-docs-render.mjs` is the sole intended `pathfinder/`
change (scope 4): a documentation-test source file, not build output, and it is
never restored.

| # | Scope | Tracked | Untracked | Contents |
| --- | --- | --- | --- | --- |
| 1 | Root integration | 3 | 0 | `Makefile`, `be`, `scripts/check-be.sh` |
| 2 | Predecessor acceptance pins | 3 | 0 | `tests/r1/check-acceptance.sh`, `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs`, carrying exactly six constants |
| 3 | R6 package | 0 | 128 | every file under `tests/r6/`, the R6 implementation itself |
| 4 | Source, status, navigation, and render files | 9 | 0 | enumerated below |
| 5 | This evidence record | 0 | 1 | `planning/single-hart-runtime-r6-evidence.md` |
| 6 | Generated documentation | 70 | 17 | `docs/html/` VitePress build output; generated, never hand-edited |

Scopes 1 and 2 are the only edits to accepted-adjacent surfaces, and scope 2 is
exactly the plan's six authorized pin constants. The earlier claim that no other
tracked file changed was wrong: scopes 4 and 6 are tracked changes and are
enumerated here rather than omitted.

Totals at the time of writing, remeasured from `git status --porcelain` after
restoring the incidental Helium/pathfinder documentation churn described above
and rebuilding only the planning site (`npm run docs:build`), then confirmed
stable across a second rebuild: **85 tracked entries** (71 modified, 14
deleted), of which 15 are outside `docs/html/`, and **146 untracked entries**
(128 R6 package files, 17 generated documentation assets, and this record).
`pathfinder/docs/html/` contributes zero tracked or untracked entries to either
total.

### Scope 1: root integration (3 tracked files)

| File | Change |
| --- | --- |
| `Makefile` | `r6-check`, `r6-evidence`, and `r6-evidence-verify` targets through the checked launcher, an R6 step in `check` after the R5 step, R6 bundle verification in `evidence-check` through the checked `r6-evidence-verify` target rather than a bare `sha256sum -c`, and an R6 line in `clean` |
| `be` | `r6-check` and `r6-evidence` subcommands, help lines, R6 status fields, R6 plan identity in `version`, R6 clean, and the derived-claim consistency check for the mapping in [Status and evidence boundary](#status-and-evidence-boundary) |
| `scripts/check-be.sh` | exact assertions for every new help/status string, the R6 launcher, the checked `r6-evidence-verify` invocation in `evidence-check`, dry-run construction of both new subcommands, and the same derived-claim consistency check |

Root `Makefile`, `be`, and `scripts/check-be.sh` are not accepted R5
`immutablePaths`, but they are **bound** by the R1, R3, and R4 acceptance
checkers. The plan authorizes exactly six pin constants to be refreshed, and no
more.

### Scope 4: source, status, navigation, and render files (9 tracked files)

These are documentation, status, navigation, and documentation-test files. None
is an accepted mechanism, an acceptance checker, a pin owner, or a production
runtime source; none is scanned by any R6 checker; and none changes an R6
result.

| File | Change |
| --- | --- |
| `README.md` | R6 row updated to the complete-local, unreviewed, unaccepted candidate state and linked to this record |
| `.github/copilot-instructions.md` | project-state paragraph and R6 command/status lines updated to the same state |
| `planning/HANDOFF.md` | current position, R6 status, and next-step text updated to the same state |
| `planning/README.md` | R6 status paragraphs, decision-gate note, and a document-inventory entry for this record |
| `planning/implementation-plan.md` | R6 row and status text updated to the same state |
| `planning/roadmap.md` | placemat R6 position and authorization boundary updated to the same state |
| `planning/single-hart-runtime-r5-evidence.md` | one amendment: the accepted R5 record's "R6 and every later successor remain not authorized and not started" sentence is time-stamped as true at R5 acceptance and pointed at this record, and the same sentence now speaks for R7 onwards. No R5 result, digest, count, or claim changed, and the R5 acceptance itself is untouched |
| `planning/.vitepress/config.mts` | one navigation entry for this record in each of the three sidebars that list the runtime records |
| `pathfinder/tests/check-docs-render.mjs` | one direct-file render expectation for the new page, so the static rendering gate covers this record like every other page |

The R5 amendment is deliberately narrow: `planning/single-hart-runtime-r5-evidence.md`
is a record of an accepted target, so it is amended only where it made a
forward-looking statement about R6 that later stopped being true, and it still
states no R6 result.

### Scope 6: generated documentation (`docs/html/`, planning site only)

`docs/html/` is committed VitePress build output for the **planning** site,
regenerated by `npm run docs:build` and gated by `./be docs-check`. It is
generated, is never hand-edited, and its exact inventory is **not** a stable
count: VitePress names its chunks by content hash, so adding one page rewrites
the page shells, the search index, and the hashed asset set, and re-running the
same build churns digests. The measured inventory, remeasured after the
restoration described above and after rebuilding the planning site, is 56
tracked entries modified, 14 tracked entries deleted, and 17 untracked entries
added: 70 tracked entries touched plus 17 additions.

The Helium/pathfinder site (`pathfinder/docs/html/`) is a distinct build output
tree under a distinct source tree (`pathfinder/docs/`) and is **not** part of
this scope: it carries no R6 documentation change, so it is restored to `HEAD`
and measured at zero tracked and zero untracked entries, not enumerated as a
seventh scope.

This is exactly the surface the open generated-asset byte-reproducibility
finding covers. R6 does not resolve that finding, claims no byte
reproducibility for generated HTML, and treats this scope as build output rather
than evidence.

### The six authorized acceptance-pin refreshes

Applied in the plan's mandated order; pin 1 changes the byte stream that pins
2-6 measure, so it is written first and the rest are recomputed after it.

| # | Owner | Constant | Bound object | Refreshed value |
| --- | --- | --- | --- | --- |
| 1 | `tests/r1/check-acceptance.sh` | `successor_makefile_sha256` | root `Makefile` | `bff108039a5a3397a59f2a633360e16949429fc264164a3655297d31f462fa54` |
| 2 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` | `tests/r1/check-acceptance.sh` | `eab6ebd61b33a7ecb63b9ee174844d688fda1b8806ec89cb5b7e75861c591699` |
| 3 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` | `be` | `cd4fefc69efc69b2321e7e3d636861cb07e6ca25a9ca334cb224578b9b78173e` |
| 4 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` | `scripts/check-be.sh` | `d98d68ee7ce823ad5cf1c7db0e05434d0c3af4a725872d0e4821ece5a7289820` |
| 5 | `tests/r4/check-accepted-content.mjs` | `approvedDeltaSha256` | `be` | `d35792bb12cf01d55f9efb397b44ac5be8665d4c9424b2afcfc818cee1f2022a` |
| 6 | `tests/r4/check-accepted-content.mjs` | `approvedDeltaSha256` | `scripts/check-be.sh` | `75e87326e147aa2044ecc24e91b0c22b3adb43665079edf0b53f4f45fa37132e` |

Pin 1 is a plain `sha256` of the current root `Makefile`. Pins 2-6 use the
established approved-delta formula, identical to the accepted R3/R4 precedent:

```text
sha256(targetMode + "\0" + currentMode + "\0" + targetContent + "\0" + currentContent + "\0")
```

where `targetMode`/`targetContent` are the bytes and mode at the accepted
predecessor commit and `current*` are the present worktree bytes and mode. An
approved delta therefore pins the *exact* target-to-current difference: any
further edit to `be`, `scripts/check-be.sh`, `tests/r1/check-acceptance.sh`, or
the root `Makefile` invalidates it and must be re-approved. That rule was
exercised five times in practice. The later correction of the `be` and
`scripts/check-be.sh` QEMU-evidence string and derived-claim check invalidated
pins 3-6, which were recomputed from the same formula against the same accepted
targets and rewritten above. The subsequent root `Makefile` change that routes
`evidence-check` through the checked `r6-evidence-verify` target then
invalidated pin 1, and rewriting pin 1 inside `tests/r1/check-acceptance.sh`
invalidated pin 2, which binds that file; both were recomputed in that mandated
order and rewritten above. The same change required `scripts/check-be.sh` to
assert the new `evidence-check` line, which invalidated pins 4 and 6, and those
were recomputed from the same formula against the same accepted R3 and R4
targets. The later replacement of the hard "`tests/r6` must be untracked"
refusal by the measured `head_tracked_r6_paths` derivation added that derived
check to both `be` and `scripts/check-be.sh`, which invalidated pins 3-6 once
more; all four were recomputed from the same formula against the same accepted
R3 and R4 targets. A fifth, postcommit change then restated `be`'s usage text
to state the `local-only-uncommitted` and `committed-candidate-not-accepted`
integration outcomes explicitly instead of the single prior phrasing, and added
the matching `require_text` assertions for that help output to
`scripts/check-be.sh`, alongside the derived `r6_integration`/claim fields the
same script already checked against `./be status`. That changed `be` and
`scripts/check-be.sh`, which again invalidated pins 3-6; all four were
recomputed from the same formula against the same accepted R3 and R4 targets
and are the values above. Counting every trigger enumerated above and in
findings 6-8 below, this is the third cumulative invalidation of pins 3 and 5
and the fourth of pins 4 and 6. Pins 1 and 2 measure the root `Makefile` and
`tests/r1/check-acceptance.sh`: after the mandated re-derivation that the root
`Makefile` change and the pin 1 rewrite caused, none of the three later
changes touched either bound file, so both have remained byte-identical to the
values fixed by that re-derivation. The recomputation was validated against
the formula rather than assumed: with the pre-edit bytes substituted back, the
formula reproduces the previous pin 2 constant exactly.

`tests/r6/acceptance-pins.mjs` independently recomputes all six from the same
formula, reports `required=6 applied=6`, and refuses a report in which any pin
is required and unapplied, unrequired and applied, or forged. The measured
`git status --porcelain` over the six refreshable paths must list exactly those
files and nothing else.

Proof that only the pins moved: `git diff 165f4d001a2b59b582b397bdea79ec4826168fdb --`
over the three predecessor checker files shows exactly six changed constant
lines, and the R6 baseline gate reports `immutable-paths=116 changed=0`.

### Negative and predecessor checks run

- `tests/r1/check-acceptance.sh --require`, `tests/r2/...`, `tests/r3/...`,
  `tests/r4/...`, and `tests/r5/check-acceptance.sh --require` all pass, each
  reporting its accepted mechanism match as `yes`, before and after the edits.
- The R3, R4, and R5 negative acceptance suites pass, including the revert
  self-tests that prove each refreshed pin is live rather than decorative.
- `r5_implementation_content_digest` is unchanged across the whole change set.

## Catalogue, partitions, and detection layers

47 catalogue entries: **14 static**, **17 host**, **15 dynamic**, **1 control**.
46 carry exactly one declared defect; C-01 is the unmutated control. Catalogue
digest `54e8f3414cb0ed2433e923c0cf490eaee68bec177e55af877a9b2b112827c8ca`.

That digest is the SHA-256 of the catalogue's canonical serialisation -- the
sorted-key, two-space JSON document of schema, accepted R5 commit, layers,
expected and measured counts, coverage, and every entry with its families,
terminated by one newline -- not of any source file. It was recomputed for this
record by hashing that serialisation with `sha256sum` rather than by trusting
the emitter, and it is the same value carried independently by the fixture gate
banner, the report's `catalogue_digest`, and the `binding.catalogue_sha256` of
every per-fixture eligibility record. The catalogue's *sources* are pinned
separately: `tests/r6/catalogue.mjs`
`47621c15e7b09166c4dc09603367275332c57d3697b7f6db18a839e2e9d5195d`,
`tests/r6/catalogue-schema.mjs`
`01fae6c5b9abca5658c80b6619a1b6e65e6f94f8e17b67c3bffbda9e185e9eb5`, and
`tests/r6/handlers.mjs`
`8c0a1956c4e6f20d46d9be75173f274ec87f2a1f95c0a7e173bb8926e67628b5`. The
retained `build/r6/evidence/catalogue.json` is a different artifact again: the
`be-r6-evidence-catalogue-v1` map of entry, base file, and defect file, hashed
into the bundle manifest like every other retained file.

Eleven detection layers, in real pipeline order. Six are R6-owned (L1, L2, L8,
L9, L10, L11); the rest are accepted R5 or pinned-toolchain stages that R6
observes but never replaces. Scratch preparation is a precondition of L3-L10,
not a layer; a failure there is a `scratch-fault`, never a layer result.

| Layer | Stage | Owner | Role |
| --- | --- | --- | --- |
| L1 | baseline immutability | R6 | pass-through gate |
| L2 | catalogue integrity | R6 | pass-through gate |
| L3 | source inventory and generation | accepted R5 | rejection layer |
| L4 | compile | pinned toolchains | pass-through invariant |
| L5 | link | accepted R5 | rejection layer |
| L6 | static image semantics | accepted R5 | rejection layer and mandatory disposition check for every image |
| L7 | toolchain parity | accepted R5 | pass-through invariant |
| L8 | single-delta differential | R6 | rejection layer for undeclared drift |
| L9 | QEMU artifact production | R6 | execution stage |
| L10 | dynamic semantics | R6 | rejection layer |
| L11 | host mechanism | R6 driver over accepted mechanism | rejection layer |

Rejection at a layer other than the declared one, or a disposition other than
the declared one, is a `layer-shift` failure of the run. The harness never
relaxes, widens, or auto-adopts an observed expectation; a mismatch fails R6 and
requires a plan revision.

Coverage ledger: **29 primary classes, 0 uncovered, 4 secondary claims** not
counted toward completeness (12 dynamic primary, 17 host primary).

## Static partition: 14 fixtures, rejected before execution, 0 QEMU runs

Four fixtures are rejected by the accepted source inventory (L3), four by
accepted linker assertions (L5), and six by the accepted image checker (L6).

| ID | Base | Layer | Observed outcome |
| --- | --- | --- | --- |
| S-01 | `r5-beryllium.lds` | L5 | `rejected-at-link` |
| S-02 | `r5-beryllium.lds` | L5 | `rejected-at-link` |
| S-03 | `r5-beryllium.lds` | L5 | `rejected-at-link` |
| S-04 | `r5-trap.S` | L3 | `rejected-at-source-inventory` |
| S-05 | `r5-trap.S` | L6 | `rejected-by-image-check` |
| S-06 | `r5-trap.S` | L6 | `rejected-by-image-check` |
| S-07 | `r5-runtime.c` | L6 | `rejected-by-image-check` |
| S-08 | `r5-runtime.c` | L6 | `rejected-by-image-check` |
| S-09 | `r5-trap.S` | L6 | `rejected-by-image-check` |
| S-10 | `r5-trap.S` | L6 | `rejected-by-image-check` |
| S-11 | `r5-guest.S` | L3 | `rejected-at-source-inventory` |
| S-12 | `r5-guest.S` | L5 | `rejected-at-link` |
| S-13 | `virt/be/r5.c` | L3 | `rejected-at-source-inventory` |
| S-14 | `tests/r5/Makefile` | L3 | `rejected-at-source-inventory` |

Measured: 14 fixtures, 24 results, 20 build attempts, 8 link failures, 12 image
rejections, 12 ELFs quarantined, 24 artifacts quarantined, 2 promotion roots,
24 promotion digests searched, **0 promoted**, **0 QEMU runs**. No mutated
static ELF is ever executed, and no accepted R5 phony target is invoked for a
mutated image. Static self-test: 73 mutations, 18 controls, 91 cases, all 14
fixtures exercised, including 14 built-and-accepted forgeries.

S-05 is the static half of the skipped-fence family: the accepted checker
rejects the unpaired `hfence.gvma` construction. No unfenced image is executed
anywhere in R6.

## Host partition: 17 fixtures, 18 class outcomes, 0 QEMU runs

`tests/r6/r6-check.c` calls the accepted architecture-neutral mechanism in
`virt/be/r5.c` with exactly one malformed argument, or one malformed field of an
otherwise well-formed argument, and requires the exact stable error class. These
cover classes that cannot be produced safely, or at all, inside the fixed QEMU
profile.

Classes exercised: `null` (H-01), `pending` (H-02), `binding` (H-03),
`trusted-stack` (H-04), `saved-page` (H-05, secondary to D-14),
`vs-origin` (H-06), `vsatp` (H-07), `frame-reserved` (H-08),
`frame-state` (H-09), `target-reset` (H-10), `entry-controls` (H-11),
`publication` (H-12), `hart` (H-13), `htval-overflow` (H-14), `gpa` (H-15),
`trap-metadata` (H-16), and both `shutdown-returned` and `shutdown-rejected`
(H-17, two outcomes from one fixture).

Measured: 17 fixtures, 18 class outcomes (17 primary, 1 secondary), 17 negative
self-tests, 8 ledger mutations, 30 cases, **1063 assertions**, 68 host
executions, and `gcc-clang-deterministic=yes` — the GCC and Clang host binaries
produce identical result streams. **0 QEMU runs.**

## Dynamic partition: 15 fail-closed fixtures plus 1 control, 64 QEMU runs

Every dynamic image is built, passes or reaches its declared L6 disposition,
passes the L8 single-delta differential against its same-toolchain control
image, and is then executed under QEMU twice per toolchain. Every one
terminated fail-closed with the declared class and last marker, with no
forbidden marker, an allowlisted SBI SRST shutdown, and QEMU status `0`.

| ID | Base | L6 disposition | L8 delta | Observed class | Last marker |
| --- | --- | --- | --- | --- | --- |
| C-01 | none (control) | pass | identity | `none` | `BE_R5:12` |
| D-01 | `r5-guest.S` | `reject-with` | guest word | `event-args` | `BE_R5:06` |
| D-02 | `r5-guest.S` | `reject-with` | guest word | `backing` | `BE_R5:04` |
| D-03 | `r5-guest.S` | `reject-with` | guest word | `gva` | `BE_R5:04` |
| D-04 | `r5-guest.S` | `reject-with` | guest word | `cause` | `BE_R5:04` |
| D-05 | `r5-guest.S` | `reject-with` | guest word | `cause` | `BE_R5:06` |
| D-06 | `r5-guest.S` | `reject-with` | guest word | `cause` | `BE_R5:06` |
| D-07 | `r5-guest.S` | `reject-with` | guest word | `pc` | `BE_R5:04` |
| D-08 | `r5-guest.S` | `reject-with` | guest word | `import` | `BE_R4:02` |
| D-09 | `r5-guest.S` | `reject-with` | guest word | `event-args` | `BE_R5:10` |
| D-10 | `r5-runtime.c` | pass | monitor range | `target-readback` | `BE_R5:02` |
| D-11 | `r5-runtime.c` | pass | monitor range | `fence` | `BE_R5:02` |
| D-12 | `r5-runtime.c` | pass | monitor range | `hgatp` | `BE_R5:02` |
| D-13 | `r5-runtime.c` | pass | monitor range | `invalid-phase` | `BE_R5:04` |
| D-14 | `r5-runtime.c` | pass | monitor range | `saved-page` | `BE_R5:03` |
| D-15 | `r5-trap.S` | pass | monitor range, exactly 10 bytes | `interrupt` | `BE_R5:04` |

C-01 reproduces the exact 22-line accepted marker sequence
`BE_R3:01..07`, `BE_R4:01..03`, `BE_R5:01..12`, line for line, with QEMU status
`0` and no `BE_R5:FAIL`. It is harness self-validation only: **not** new R5
evidence and **not** an R5 re-acceptance.

Every guest-driven fixture stays inside its own immutable G-stage map. None can
reach another domain's private page, because the accepted roots, not the
fixture, define reachability. D-11 is the safe dynamic half of the skipped-fence
family: the fence is still executed and only its acknowledgement is withheld,
so no unfenced guest ever runs; it proves the monitor refuses to proceed without
a completed local fence.

Measured: 16 entries, 32 images, 64 runs, 2 toolchains, 0 timeouts, 0 non-zero
QEMU statuses. The exact split is 15 fail-closed fixtures x 2 toolchains = 30
fail-closed images x 2 runs = 60 runs, plus 1 control fixture x 2 toolchains =
2 control images x 2 runs = 4 runs. `be status` reports that split as
`r6_qemu_evidence=sixty-four-local-runs-thirty-fail-closed-images-plus-two-control-images-not-accepted`,
and `scripts/check-be.sh` asserts that exact string. Dynamic self-test: **141
cases** (11 eligibility, 11 record, 18 image, **18 layout**, 20 run, 16
forbidden, 16 console, 17 malformed, 14 shape), the nine reported groups summing
exactly to the reported total. The 18 layout cases are the per-toolchain
`declared_delta.layout` and `pinned_layout` checks the D-15 pins added.

### D-06: cause 22 from a VS-mode `csrr a0,hgatp`

D-06 replaces one frozen protected-guest word at GPA `0x40011028`
(`00040513` -> `68002573`), so the protected guest executes `csrr a0,hgatp`
from VS mode. RISC-V raises a **virtual instruction** exception, cause `22`, at
`0x40011028`; the observed class is `cause` and the last marker is `BE_R5:06`.
The recorded architectural justification must remain true: if QEMU reported
cause `2` instead, the accepted expected class would still be `cause`, but the
recorded justification would be wrong and the fixture would have to be revised
rather than silently re-labelled.

### D-15: pinned two-run, ten-byte image delta

D-15 is the only fixture whose defect is in a copy of `arch/riscv/be/r5-trap.S`.
Two instructions, `csrsi hvip,4` then `csrsi hie,4`, are inserted as one
contiguous `+2 / -0` hunk **after** every `be_r5_switch_tail` entry-control
readback and after the last frame restore pair, immediately before the jump to
the shared entry tail. The observed result is `scause=0x8000000000000002`
(VS software interrupt), `sepc=0x40011000`, `stval=0`, `htval=0`, class
`interrupt`, last marker `BE_R5:04`, and **zero retired protected guest
instructions**: `SRET` completes into VS mode in the exact architectural sense,
and the injected interrupt preempts before any protected instruction retires.
`BE_R5:05` and `BE_R5:12` must both be absent.

The L8 expectation is pinned exactly and fails closed:

| Toolchain | Differing runs (flat-image offsets) | Differing bytes | `.monitor.text` size |
| --- | --- | --- | --- |
| GCC | `{start: 30032, length: 9}`, `{start: 30042, length: 1}` | 10 | `0x7610`, unchanged |
| Clang | `{start: 30080, length: 9}`, `{start: 30090, length: 1}` | 10 | `0x7640`, unchanged |

Both flat images stay `212992` bytes. The two inserted words consume 8 of the 12
existing `.align 4` padding bytes, so `be_r5_enter_guest_tail` keeps its
accepted address and `.monitor.text` keeps its allocated size. The delta is two
runs rather than one because the byte at `+9` is coincidentally equal in both
images. Any extra differing byte, missing declared byte, relocated offset, third
run, or `.monitor.text` size change is a rejection.

Both rows are pinned in the fixture manifest as a **nested per-toolchain**
`declared_delta.layout` (`layout.gcc` and `layout.clang`), each dynamic
differential record carries the `pinned_layout` the image was actually measured
against, and both are checked and published per toolchain. The report's
`differential_result.by_toolchain` carries one measured record for each of GCC
and Clang -- kind, differing bytes, run count, publish-target references,
verdict, and, where the fixture declares a layout for that toolchain, the exact
run list and declared layout -- and `tests/r6/check-report.mjs` compares each
record against that toolchain's own `<toolchain>-differential.json`, requires
the run lengths to sum to the differing byte count, requires the measured runs
to equal the declared runs and the measured `pinned_layout` to equal that
toolchain's nested declared layout, and holds D-15 to the accepted R6-B
constants of *each* toolchain -- the exact offsets `30032 + 9` / `30042 + 1`
with `.monitor.text` at `30224` bytes for GCC and `30080 + 9` / `30090 + 1`
with `30272` bytes for Clang -- from constants the checker owns rather than
from the fixture it is checking. The two accepted layouts are required to be
distinct, so neither can stand in for the other. Publishing one toolchain's
measurement for both, mislabelling a record, dropping a record, relocating a
run, resizing `.monitor.text`, or inventing a run layout is refused; the delta
sizes genuinely differ by toolchain elsewhere in the matrix (D-10 differs by
5237 bytes under GCC and 464 under Clang), so a single-toolchain publication
would have been a real substitution rather than a harmless simplification. Non-allocated
debug/symbol-table changes (GCC `.debug_line`, `.debug_str`, `.debug_frame`,
`.symtab`, `.strtab`, `.shstrtab`; Clang `.debug_line`, `.debug_aranges`, and 12
local `$d` mapping symbols) are excluded by construction; `be_r5_switch_tail`
keeps its address and only its `st_size` differs (`212` -> `220`).

## Framework, tool, scratch, lock, and authority guards

- **Source guard.** `tests/r6/check-sources.mjs` scans 128 package files, 52 of
  them guarded, and reports inventory SHA-256
  `e4368c0e7b9439fed49b0e14aa6d27b4e81060b1a703e40536f3c3fe97b56386`. It proves
  76 fixture payloads, 28 writers over 361 write sites, 1038 commands, 242
  indirect commands, 904 programs, 52 tool modes, 212 modules, 23 launchers, 4
  traps, 92 refused surfaces, 42 accepted sources, **0 production surfaces**,
  and **0 R6 identifiers** in accepted code. Its self-test accepted 72 baselines
  and refused 472 hostile variants, including 9 run-overlap cases.
- **Root-integration guard.** The same checker now also scans the two root files
  it owns lines in (`be`, `scripts/check-be.sh`): each must carry exactly one
  accepted-form historical authorization line, must not carry the forbidden
  claim form, must not assemble the key from fragments, must carry the live
  package-authorization key, and must name the R6 checked launcher. Reported as
  `root-integrated-files=2 root-authority-allowed-lines=2`. Five new refusal
  cases cover a duplicated historical line, a historical line flipped to the
  claim form, a dropped live key, a dropped launcher reference, and a removed
  wrapper.
- **Authority policy.** `tests/r6/authority-policy.mjs` is `hash-only`: the
  16-character key and its claim/accepted forms are recognized by SHA-256, never
  written literally in checker code. Permitted longer keys are
  `r6_package_authorization`, `r6_authorization_source`, and `r7_authorization`.
  `check-sources.mjs` pins 15 authority-policy invocations by exact normalized
  line text, aggregate digest, occurrence count, and reachable function.
  Planning prose may quote the forbidden literal to explain it; no checker scans
  planning documents, and R6 adds no repository-wide textual ban.
- **Tool binding.** `tests/r6/tool-lock.conf`
  (`c3ce6c32e27433aededdeb72510ec85ca1d3241b19bd7fed303f21c0d6d7e647`) is
  derived from, and forbidden to rebind away from, the accepted
  `tests/r3/tool-lock.conf` base
  (`c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b`). 36 tool
  roles are bound to absolute command path, resolved path, version, SHA-256, and
  owning package, including pinned OpenSBI firmware
  `49bdf7b939bda11321132d1042bf99d7324fb190f1feef423171fed3573f8705`. Hostile
  Make and shell controls are rejected at parse time: 73 launcher cases, 30 raw
  command-line cases, 35 raw environment cases, 2 unpinned-make cases, 1 foreign
  directory, 1 control-argument case, 2 concurrent-run cases, 142 combined —
  clustered short options, bare flag words, and forged success all rejected.
  Every launch that proves a version, a resolved program, or an owning package
  is **delegated**, and happens exactly once per invocation at `r6-toolcheck`:
  `tests/r6/check-tools.sh` copies the accepted files into R6-owned scratch
  byte-and-mode identically and runs the accepted R3 verifier (42 roles) and
  the accepted R5 probe (36 roles) there, with `HOME` and `TMPDIR` inside that
  tree, comparing both banners in full. Because `r6-toolcheck` is a transitive
  prerequisite of every partition target, no checked R6 target can run without
  it. Later semantic checkers rebind to those facts **without launching
  anything**, through the shared `verifyLockedIdentity` in
  `tests/r6/tool-lock.mjs`: absolute command path, executable mode, regular
  file, resolved real path, and SHA-256 content digest, plus membership of both
  accepted role sets. R6 exports no function that launches a process, and the
  only role R6 itself launches is `flock`.
- **Scratch confinement.** 30 scratch trees, 16 components each, 5 source
  components, byte-and-mode verified, `faults=0`, confined to the repository
  root. Each tree held all 5 source components byte-and-mode identical apart
  from its single overlaid defect, and the scratch `tests/r3` copy contained
  exactly `tool-lock.mjs` and `tool-lock.conf` at the verified base digest.
  Scratch self-test: 592 checks.
- **Run lock.** The only role R6 itself owns is `flock`
  (`/usr/bin/flock`, util-linux 2.41.5,
  `c41ea2a70dab86eba37d106c0a444c58db15216c0d8435c9058dbfa178a87bf9`). Mutual
  exclusion is kernel `flock` on `build/r6/run-lock/lock`, not an advisory file
  convention; overlapping invocations are refused rather than serialized. Run
  lock self-test: 121 checks.
- **Baseline guard.** 22 accepted console lines, 10 bound inputs, 116 immutable
  paths, 9 forbidden markers, 6 pins required and applied, root integration
  `performed`, production surfaces absent, R6 symbols absent, 24 drift cases, 4
  delegated detections, 211 checks.
- **Fresh bootstrap.** 3 bootstrapped trees, 4 components, 2 fresh-tree
  later-stage checker cases, 12 refusals, 8 graph
  cases, 7 partition targets all implemented, 0 launched, nested invocation
  exercised, 2 concurrent runs, 6 forced leaving-run/acknowledgement races
  (2132 acknowledgements in the recorded run), accepted scratch untouched, 206
  checks.
- **Fixture-mutation guard.** 32 catalogue mutations, 8 gate refusals, 2
  generated-drift cases, 181 checks.

## Report and evidence bundle

The canonical report is `build/r6/reports/adversarial-images.json`, schema
`be-r6-adversarial-images-v1`, generated by `tests/r6/generate-report.mjs` and
independently re-checked by `tests/r6/check-report.mjs`.

| Property | Value |
| --- | --- |
| Report bytes | measured per run; not pinned here -- see below |
| Report SHA-256 | run-specific; not pinned here -- see below |
| Entries | 47 (14 static, 17 host, 15 dynamic, 1 control) |
| Report-check assertions | measured per run; not pinned here -- see below |
| Images | 32 (30 fail-closed dynamic + 2 control) |
| QEMU runs | 64 (60 fail-closed dynamic + 4 control; 0 for static or host) |
| Build attempts / successful links / link failures | 52 / 44 / 8 |
| Image-check / parity / differential invocations | 44 / 7 / 32 |
| Host executions / assertions | 68 / 1063 |
| Scratch trees / faults | 30 / 0 |
| Determinism | generated twice, byte-identical |
| Acceptance pins | authorized 6, required 6, applied 6 |
| Root integration | `performed` |
| Tracked R6 paths at `HEAD` (measured) | dual state: `0` -> `local-uncommitted` / `local-only-uncommitted` before the package is tracked; `128` -> `committed-not-accepted` / `committed-candidate-not-accepted` once it is |
| Worktree entries for `tests/r6` (measured, re-measured by the checker) | measured per run: `1` (`?? tests/r6/`) before tracking, one ` M` entry per uncommitted follow-up edit after |
| Per-toolchain image deltas published | 32 (one per image, 2 per dynamic and control entry) |
| Accepted R5 image parity (measured, re-measured by the checker) | `differs` for every dynamic image and `identical` for the control image when `build/r5/<toolchain>/beryllium.bin` exists; `not-available` for every image when it does not, and a published value that disagrees with the measurement is refused either way |

The report records the applied pin manifest with, for each pin, its owner,
constant, bound object, recorded value, independently recomputed value, and its
`required`/`applied` state; a report whose recorded and recomputed values
disagree, or whose root-integration state is forged, is refused.

Determinism here is *within* a run: `r6-report` generates the report twice from
the same recorded evidence and requires the two generations to be byte-identical.
It is not a claim of byte-identical reports *across* independent runs, and it is
not a claim of a stable byte count or assertion count either. Each dynamic run
records the SHA-256 and byte count of its ephemeral raw trace, and those digests
differ between runs. The report additionally publishes the measured tracked-path
count and the measured `git status --porcelain -- tests/r6` entries, so the
report's exact byte count -- and, with it, the number of assertions the
independent checker makes over it -- also moves with the tree's **tracked
integration state**: an untracked package, a committed package, and a committed
package carrying uncommitted follow-up edits each produce a different exact
size. This record therefore validates **equivalent content**, not exact bytes:
the entry, image, run, and assertion *structure* above is what is checked, and
`r6-report` re-derives and re-checks the exact numbers on every run. Exact
final byte, digest, and assertion values are recorded only in a review packet
for one exactly validated target commit, never carried forward here. The
evidence bundle's retained byte count varies for the same reason, which is why
the summary's byte fields are measured from the bundle at retention time rather
than pinned.

`tests/r6/test-committed-state.mjs` runs inside `r6-report` and writes
`build/r6/reports/committed-state.txt`, which the retained bundle keeps and
`check-acceptance.sh --require` requires: 3 isolated temporary Git
repositories, 128 tracked paths measured in the committed one, the live
tracked-path count measured in this tree (`128` here, `0` before the package
is tracked), the measured worktree entries (`7` in this follow-up state, `1`
before the package is tracked), 4 derived states, 6 root-integration
targets, 79 cases, and 41 refusals, all with `acceptance=not-reviewed`.

`tests/r6/test-report-rejection.mjs` applies **1424 pinned mutations** and
records **1477 refusals** across 47 entries, 29 classes, 11 layers, 5
command-line cases, 8 policy cases, 3 injection cases, 3 evidence cases, 15
claim-ladder cases, and 21 acceptance cases. Forged authority is explicitly
covered: a report claiming R6
authorization on the historical key, or a forged
`r6_package_authorization=accepted`, is rejected; so are a report claiming pins
unapplied, a forged required count, an unapplied or unrequired pin entry, a
forged pin constant, and a denied root-integration state.

Three of the pinned mutations forge the claim ladder itself: an evidence claim
that outruns the report's implementation state, an implementation state and
claim raised together so that the pair is internally consistent but still
outruns the report, and a claim resting on a state the mapping does not define.

The 15 claim-ladder cases are not paper cases; they run the real checker over a
real staged tree. A complete copy of the package and of every partition result
is staged with no retained bundle, with the report check required to carry its
pass banner, and with the refusal transcript deliberately empty, because this
suite is itself the program that writes that transcript and cannot honestly
stage its own unwritten result. Over that tree, `check-acceptance.sh` reports
the report-only rung and exactly the claim that rung supports; `--require` and
`--require-complete` both refuse it, naming the refusal suite the tree has not
passed, and print no claim at all; a copy of the checker edited to print
`complete-local-not-reviewed` refuses *itself* before printing, because its
printed pair no longer matches what it measured; and once the honest bundle is
retained the same checker rises exactly one rung, to `complete-local` and the
complete claim, while still refusing the completeness gate the staged tree has
not passed. A success-shaped mismatch is therefore refused rather than reported,
and a retained bundle buys no check the tree did not run.

The evidence bundle is `build/r6/evidence/`, described by
`build/r6/evidence/summary.txt` (schema `be-r6-evidence-summary-v1`), covered by
an aggregate `artifacts.sha256` manifest, and re-verified as an exact set by
`tests/r6/check-evidence.mjs`:

| Property | Value |
| --- | --- |
| Manifest entries (payload, summary included) | `549` |
| Bundle files (payload plus the manifest) | `550` |
| Payload bytes (manifest-covered) | measured at retention time (`4791971` in the run behind this record) |
| Manifest bytes | `63702` |
| Bundle bytes (payload plus manifest) | measured at retention time (`4855673` in the run behind this record; limit 536870912, 512 MiB) |
| Console logs / exit-status files | 64 / 64 |
| Canonical semantics records | 64 |
| Bounded trace excerpts | 64 |
| Raw traces retained | **0** (64 raw-trace digests and byte counts recorded) |
| Fixtures / scratch trees | 47 / 30 verified, none kept |
| Manifest | verified, and the retained set matched exactly |

The four counts are stated so that each is true of a named set rather than of an
ambiguous one. `summary.txt` is itself a retained artifact, so it is written
*before* the manifest and hashed into it: a summary written afterwards would be
evidence that nothing covers. Because the summary counts bytes that include its
own, `generate-evidence.sh` writes it, re-measures the bundle, and rewrites it
until the stated numbers are a fixed point of the bundle on disk, then re-reads
the settled numbers from disk and refuses to finish if they disagree with what
it measures. Only `artifacts.sha256` stands outside its own coverage, because a
manifest cannot state its own digest; it is still counted in `bundle_files` and
`bundle_bytes`, and the 512 MiB bound is applied to `bundle_bytes`, the bytes
the directory actually holds.

`tests/r6/check-evidence.mjs` re-derives all of that from the bundle instead of
accepting it. It parses every manifest path as a safe relative path under
`build/r6/evidence/` (no absolute path, no `..`, no empty component, no
duplicate, no self-listed manifest), refuses a symbolic link or a non-regular
file standing in for a retained artifact, re-hashes and re-measures every listed
file, requires the retained tree to be *exactly* the manifest paths plus
`artifacts.sha256` (an unlisted extra file and a missing listed file are both
refused), requires the named artifacts the bundle must carry, refuses any
retained raw trace, and then checks every summary field -- its schema, its exact
field set and order, its numeric form, its counts, its byte totals, and its cap
-- against what it measured and against the retained catalogue, scratch
inventory, claim ledger, and report retention block. It is run by `r6-evidence`
and `r6-check`, by the standalone checked target `r6-evidence-verify`, and by
the root `evidence-check`, which invokes that checked target rather than a bare
`sha256sum -c`.

`tests/r6/test-evidence-rejection.mjs` holds that verifier to its refusals: over
a staged copy of the retained bundle it applies **43 forgeries** and records
**43 refusals**, one honest control, and 5 command-line cases, covering an
unlisted file, a removed listed file, a removed required artifact, a symbolic
link substitution, a tampered byte, a tampered digest, a truncation, a repeated,
traversing, absolute, foreign, self-listed, malformed, newline-less, or empty
manifest, a retained raw trace, every summary field individually, the summary's
schema, field set, ordering, and numeric form, and the catalogue, scratch
inventory, claim ledger, and retained report the summary is checked against. A
semantic forgery also restates the byte totals and re-hashes what it edited, as
a forger with write access would, so each refusal is earned by the claim under
test rather than by stale arithmetic.

The claim ledger in `build/r6/evidence/claim-ledger.txt` carries the
authorization, acceptance, publication, hardware, formal, and reproducibility
statements verbatim, including `r6_evidence_claim`,
`acceptance_pins_applied=6`, `acceptance_pins_required=6`, and
`root_integration=performed`.

The retained `build/r6/evidence/report/acceptance-status.txt` and the ledger's
`r6_evidence_claim` line record the posture **at bundling time**, which is
`r6_implementation=report-generated` / `r6_evidence_claim=report-generated-not-reviewed`.
This is not a discrepancy and is not a weaker result quietly substituted for a
stronger one: `r6-evidence` deletes and rebuilds the bundle before the retained
status is measured, so at that instant the retained evidence tree does not yet
exist and the checker cannot honestly say `complete-local`. The bundle therefore
demonstrates the ladder in the live pipeline rather than describing it. Only
`tests/r6/check-acceptance.sh --require-complete`, run after retention
completes, observes and requires `complete-local`.

## Reproducible commands

Targeted R6 checks go through the checked launcher, which is the normative
interface:

```sh
./tests/r6/run-make.sh r6-toolcheck
./tests/r6/run-make.sh r6-baseline
./tests/r6/run-make.sh r6-host-test
./tests/r6/run-make.sh r6-fixture-check
./tests/r6/run-make.sh r6-static
./tests/r6/run-make.sh r6-dynamic
./tests/r6/run-make.sh r6-report
./tests/r6/run-make.sh r6-evidence
./tests/r6/run-make.sh r6-evidence-verify
./tests/r6/run-make.sh r6-check
```

The stable root-wrapper commands are:

```sh
./be r6-check
./be r6-evidence
```

Both wrapper subcommands invoke the checked launcher in a scrubbed environment
(`/usr/bin/env -i PATH=/usr/bin LC_ALL=C LANG=C SHELL=/bin/bash`); neither
invokes `make -C tests/r6` directly, and the launcher refuses overlapping
invocations through the kernel run lock. The root `Makefile` exposes the same
two targets plus `r6-evidence-verify`, runs R6 in `check` after the accepted
R0-R5 gates, verifies the retained R6 bundle in `evidence-check` by invoking the
checked `r6-evidence-verify` target, and cleans R6 through the launcher, while
preserving plain `make` as the Helium image build.

`./be r6-check` is **standalone**: it is required to pass from a worktree that
has no `build/` directory at all, without any R0-R5 target having been run
first, and to create no scratch outside `build/r6` while doing so. That is a
measured property, not a convention. It was validated end to end from a
separate detached worktree that began with no `build/`
(`BE_R6: PASS r6-check entries=47 runs=64 acceptance=not-reviewed`, with
`build/` holding `r6` and nothing else afterwards), and
`tests/r6/test-fresh-bootstrap.mjs` keeps a bounded regression for it that
deletes `build/` and runs the two later-stage semantic checkers directly,
requiring each to refuse for its own artifact reason and to leave no `build/`
behind. Findings 11 and 12 record the two defects this property exposed.

Predecessor and integration checks:

```sh
tests/r1/check-acceptance.sh --require
tests/r2/check-acceptance.sh --require
tests/r3/check-acceptance.sh --require
tests/r4/check-acceptance.sh --require
tests/r5/check-acceptance.sh --require
tests/r6/check-acceptance.sh --require-complete
scripts/check-be.sh
./be status
```

Complete gate:

```sh
make check && ./be r6-check
npm run docs:build && ./be docs-check && scripts/check-be.sh
```

## Findings and resolutions

1. **R6-A: D-15's accepted injection site could not reach its declared class.**
   The original plan armed `hvip[2]`/`hie[2]` inside `switch_domain`, before the
   immutable `be_r5_switch_tail` re-reads both control registers on the
   published no-call path and rejects a non-zero value. Any arming there is
   detected by the accepted mechanism itself and terminates as `entry-controls`
   with last marker `BE_R5:04`, never as `interrupt`. Because the declared class
   was unreachable at the named site under any restricted-C spelling, this was a
   plan defect, not an implementation defect, and the wrong-error-class gate
   required a plan revision rather than a relaxed expectation. **Resolved** by
   moving the defect to `arch/riscv/be/r5-trap.S`, after every entry-control
   readback and the last frame restore pair. Accepted at
   `75269f058ae578b0a76a113d6c05c0aaceeac8ec`.
2. **R6-B defect 1: the D-15 layout arithmetic was factually wrong.** The plan
   asserted `.monitor.text` would grow by 8 bytes and shift subsequent code.
   Both statements are false: the existing `.align 4` padding already provides
   12 `nop` bytes, so the two inserted instructions consume 8 of them, the
   allocated size does not change, and the flat image stays `212992` bytes. An
   L8 expectation written from the original text would have declared a delta
   that cannot occur. **Resolved** by pinning the exact per-toolchain
   `{start, length}` runs, the 2-run/10-byte totals, and the unchanged
   `.monitor.text` size and allocated symbol addresses.
3. **R6-B defect 2: the planned raw-trace retention was arithmetically
   impossible.** Retaining 32 raw `in_asm,cpu` traces at roughly 310-370 MiB
   each is about 10.6-11.5 GiB against the plan's own 512 MiB cap; all 64 would
   be about 21 GiB. **Resolved** by making raw traces ephemeral: each run keeps
   a canonical semantics record, a raw-trace SHA-256, a byte count, and a
   bounded excerpt, and the raw log is deleted after extraction. Measured
   retained evidence is `4855435` bundle bytes, far inside the cap, with
   `raw_traces_retained=0`. Both defects were accepted as revision R6-B at
   `6d6464c6c937abccd59df932006c1049fd79fac6`.
4. **Root integration required exactly six predecessor pin refreshes.** Editing
   the root `Makefile`, `be`, and `scripts/check-be.sh` invalidates the R1
   successor-Makefile pin and the R3/R4 approved-delta pins that bind them. This
   is the authorized, enumerated, ordered refresh described above; it changes no
   accepted mechanism byte, and each refreshed pin is proven live by its revert
   self-test.
5. **Framework self-test defect found, diagnosed, and fixed: a leaving probe
   run could survive its own teardown.** `tests/r6/test-fresh-bootstrap.mjs`
   intermittently failed with "a concurrent probe run left `run-XXXXXX` behind"
   when it ran nested under the launcher lock. The cause was in the probe
   harness, not in any checked property, and not the recreation of a removed
   directory: `run-identity.mjs::removeRun()` removed a run directory in one
   step with `fs.rmSync(directory, {recursive: true, force: true})`, which
   enumerates and unlinks entries and then removes the directory. A live peer's
   `acknowledge()` may write its `observed-<token>` marker into that directory
   after the enumeration and before the `rmdir`, so the `rmdir` fails
   `ENOTEMPTY`. Because teardown runs from a `process.on('exit')` handler, the
   thrown error printed a stack trace but left the exit status at `0`: the
   leaving run reported success while its directory survived holding only the
   late marker, and the observing run's absence assertion then failed. A
   targeted harness reproduced the exact symptom in 7 of 25 and 7 of 12 forced
   rounds; standalone probe pairs did not reproduce it, which matches the
   nested-only observation. **Resolved** by making teardown claim-then-remove:
   `claimRun()` first `renameSync`s `run-XXXXXX` to `closing-XXXXXX` in the same
   group, which is atomic, so after the claim the run name resolves to nothing,
   late acknowledgements fail `ENOENT` on their own (already a handled, false
   result), and the subsequent removal of the claimed directory has no writer to
   race. Peer enumeration matches only the run-directory pattern, so a
   `closing-` directory is never itself a peer, and `peerRuns()` reclaims
   `closing-` directories whose owner is absent or dead so they cannot
   accumulate. The invocation lock still serializes external targets; internal
   self-test runs remain concurrent by design and are now stable under that
   concurrency. Coverage was added rather than a retry: `test-fresh-bootstrap`
   now asserts that a claim frees the run name, that a late acknowledgement
   cannot resurrect a claimed run, that a pre-claim acknowledgement is removed
   with the directory, that `closing-` directories are never peers and dead ones
   are reclaimed, and it forces 6 "leaving run beside an acknowledging peer"
   rounds asserting empty child stderr, exit status `0`, and no leftover
   directory (`leaving-runs=6`, 190 checks). The new case was confirmed to fail
   with the original one-step removal and to pass with the fix. No R6 mechanism,
   gate, or expectation was modified to accommodate the defect, and the runs
   recorded here were obtained without clearing state or retrying.
6. **Three unfounded claims in this record's own first draft, found by review
   and corrected.** Each was a claim about the package rather than a defect in
   it, and each is now measured rather than asserted.
   1. *The status string misdescribed the image split.* `be status` reported
      `r6_qemu_evidence=thirty-two-fail-closed-images-plus-one-control`, but the
      measured run is 30 fail-closed dynamic images over 60 runs plus 2 control
      images over 4 runs: 32 images and 64 runs in total. The string now reads
      `sixty-four-local-runs-thirty-fail-closed-images-plus-two-control-images-not-accepted`,
      `scripts/check-be.sh` asserts it exactly, and the split is stated above.
   2. *The evidence claim was asserted, not derived.* `r6_evidence_claim` was a
      constant `complete-local-not-reviewed` in the acceptance checker, in `be`,
      and in `scripts/check-be.sh`, so a tree with no retained bundle would have
      published the complete claim and the wrapper gate would have demanded it.
      The claim is now a pure function of the measured implementation state, the
      three consumers check consistency instead of completeness, the checker
      refuses its own printed pair if it diverges from what it measured, and the
      ladder is exercised over a real staged tree.
   3. *This record claimed no other tracked file changed.* It did: nine tracked
      source, status, navigation, and render files and the generated `docs/html`
      build output also changed. The claim is replaced by the measured, scoped
      inventory above, derived from `git status --porcelain`.

   Correcting `be` and `scripts/check-be.sh` invalidated pins 3-6, which were
   re-derived from the same formula against the same accepted targets; pins 1
   and 2 were unaffected. The complete R6 gate, both wrapper gates, and every
   predecessor acceptance and negative suite were re-run afterwards.
7. **The retained evidence summary counted a set it was not part of, and the
   manifest did not cover it.** `generate-evidence.sh` wrote `summary.txt`
   *after* `artifacts.sha256`, so the summary was the one retained artifact no
   digest covered, and its `files=`/`bytes=` fields counted neither itself nor
   the manifest. The bundle therefore held 549 files while the banner reported
   547 and the bytes of only those 547: not a forgery, but two true numbers
   about an unnamed set presented as the size of the bundle, understating it by
   two files and by the manifest's own 63591 bytes, and leaving one retained
   artifact outside the integrity manifest. The package's own authority scan
   already measured the larger, true totals, which is how the disagreement was
   found.
   **Resolved** by generating the summary first and hashing it into the
   manifest, by replacing the ambiguous fields with `manifest_entries`,
   `bundle_files`, `payload_bytes`, `manifest_bytes`, and `bundle_bytes`, each
   true of a named set, by settling the self-referential byte counts to a fixed
   point and re-measuring them from disk, and by applying the 512 MiB bound to
   the bytes the directory actually holds. The retained set is now verified as
   an exact set by `tests/r6/check-evidence.mjs`, which is what the root
   `evidence-check` runs through the checked `r6-evidence-verify` target, and
   `tests/r6/test-evidence-rejection.mjs` proves that verifier refuses 43
   forgeries of the retained set, its bytes, its manifest, and its summary. The
   root `Makefile` change invalidated pin 1, the pin 1 rewrite invalidated pin
   2, and teaching `scripts/check-be.sh` to assert the new `evidence-check` line
   invalidated pins 4 and 6; all four were re-derived in the mandated order,
   pins 3 and 5 were confirmed unchanged, and the complete R6 gate, the root
   evidence gate, `scripts/check-be.sh`, and every predecessor acceptance and
   negative suite were re-run afterwards.

8. **A committed package would have failed the report rather than been
   described.** The generator refused any tree in which `tests/r6` was tracked
   at `HEAD`, and `check-acceptance.sh`, `be`, and `scripts/check-be.sh`
   asserted the constant `r6_integration=local-only-uncommitted`. That is true
   only before the implementation is committed for review: the first honest
   commit of this package, which is exactly what a review packet requires,
   would have turned every R6 gate red and made the fix pressure point at the
   evidence rather than at the state.
   **Resolved** by measuring instead of asserting. The report publishes
   `package.head_tracked_r6_paths`, measured with
   `git ls-tree -r --name-only HEAD -- tests/r6`, and derives `package.state`
   and `r6_integration` from that count; the acceptance script, `be`, and
   `scripts/check-be.sh` derive the same values and refuse a printed value that
   disagrees with what they measured. Neither derived state is an acceptance:
   `r6_acceptance` stays `not-reviewed`, `r6_accepted_commit` stays `none`, and
   the renamed `package.r6_accepted_implementation_commit` stays `none` in both.
   `tests/r6/test-committed-state.mjs` builds three isolated temporary Git
   repositories -- one with the package committed, one without, and one that
   simulates root integration -- measures each with the production functions,
   and runs the real checkers over both package states: 79 cases and 41
   refusals, including a forged count, a forged state, an acceptance-shaped
   `committed-accepted`, a forged worktree measurement, and a checker edited to
   print an acceptance it did not measure. Non-recursive `git ls-tree` was rejected
   during that work because it reports one tree entry rather than the package's
   128 files. Adding the derived check to `be` and `scripts/check-be.sh`
   invalidated pins 3-6, which were re-derived from the same formula against
   the same accepted R3 and R4 targets; pins 1 and 2 were unaffected.
9. **The image-delta comparison published one toolchain's measurement for
   both.** The report's `differential_result` was measured from
   `toolchains[0]`, so a per-toolchain delta divergence -- which the matrix
   really contains, D-10 differing by 5237 bytes under GCC and 464 under Clang
   -- would have been reported as a single number covering both images.
   **Resolved** by publishing and checking `by_toolchain` records, by requiring
   each record to match that toolchain's own differential result, run-length
   sum, nested `declared_delta.layout.<toolchain>` and measured
   `pinned_layout`, by pinning D-15's exact per-toolchain offsets and
   `.monitor.text` sizes in the checker itself and requiring the two accepted
   layouts to be distinct, and by adding per-toolchain forgeries (substituted,
   mislabelled, dropped, invented-layout, relocated run, resized section,
   accepted-layout substitution, forged bytes, runs, verdict, and references)
   to the rejection suite.
10. **The state-aware evidence was itself written for one state.** The fix for
    finding 8 measured the tree, but the tests that were supposed to prove it
    still assumed the tree was uncommitted. Root integration was measured as
    working-tree dirtiness, so a committed R6 change set would have read as
    "root integration edited nothing"; the committed-state suite compared the
    canonical report against a hard-coded zero; the report-rejection suite
    forged the package state and the integration posture by naming one
    enumeration member outright, which is a real forgery only while the package
    is uncommitted and a no-op -- an accepted report checked against itself --
    once it is committed; and `package.worktree_entries` was published without
    being re-measured, so a report could list any entries it liked.
    **Resolved** in four places. `tests/r6/test-baseline-guard.mjs` now
    measures `git diff --name-only <accepted R5 commit> -- <six refresh
    targets>` against the working tree, which is the same set before and after
    a commit, and `tests/r6/test-committed-state.mjs` simulates that in a third
    isolated repository: the six paths are committed at a base revision, edited,
    and measured in both states, where the difference from the base names
    exactly six before and after the commit while dirtiness names them only
    before. The committed-state suite now measures this tree with the
    production `headTrackedR6Paths` and `worktreeEntries` and holds the
    canonical report to what it measured, and it constructs an explicit
    uncommitted report and an explicit committed report and runs every forgery
    against both. Each forgery is taken from the value the report under test
    carries to the other value of the same claim, and each is required to have
    changed that report before a refusal is demanded, so no case can be a no-op
    in either state; the same toggling form is now used by the package state
    and integration mutations in `tests/r6/test-report-rejection.mjs`. Finally,
    `tests/r6/check-report.mjs` re-measures `git status --porcelain --
    tests/r6` and compares the published `worktree_entries` array exactly --
    length, order, bytes, and every path inside the package -- with five new
    forgeries (shifted, invented, foreign, restated, and not a list) covering
    it, and the committed repository, whose worktree is clean, is required to
    publish an empty array. The shifted case is a toggle like the state cases:
    it drops an entry from a tree that has work in it and invents one inside
    the package for a clean committed tree, so it forges a real claim in either
    state rather than emptying a list that is already empty.
11. **A fresh standalone `./be r6-check` failed at the first semantic
    checker.** `tests/r6/check-fixture-image.mjs` (L8) and
    `tests/r6/check-dynamic.mjs` (L10) called the accepted R3
    `verifyToolLock` directly, re-exported for them by
    `tests/r6/tool-lock.mjs`. That verifier launches every locked tool under
    the accepted R3 clean environment, which names `build/r3/tool-home` and
    `build/r3/tmp` under the repository root -- directories only an R3 target
    creates. In a tree with no `build/`, GNU Make wrote
    `TMPDIR value .../build/r3/tmp: No such file or directory` to stderr, the
    accepted verifier's stderr-first version reader consumed it as the version
    string, and R6 refused with `make version drift` -- a **misreported**
    fault, since no tool had drifted. The complete `make check` masked it
    because R3 runs first and leaves that scratch behind, so the defect was
    invisible to every gate that ran the packages in order.
    **Resolved** by removing R6's only remaining path into an accepted
    launcher. `tests/r6/tool-lock.mjs` no longer re-exports `verifyToolLock`
    and instead exports a launch-free `verifyLockedIdentity`, which binds each
    normative role to the accepted lock by absolute command path, executable
    mode, regular-file status, resolved real path, and SHA-256 content digest,
    and requires the role to be one the accepted R3 verifier and the accepted
    R5 probe both cover. The launch-dependent facts -- versions, program
    resolution, and owning packages -- are still proved by the accepted
    verifiers themselves, but exactly once per invocation at `r6-toolcheck`,
    which `tests/r6/check-tools.sh` runs inside R6-owned scratch after copying
    the accepted files there byte-and-mode identically, and which is a
    transitive prerequisite of every partition target. Equal content digests
    then carry those facts to the point of use without a launch. Nothing is
    weakened: the delegated run covers all 42 accepted R3 roles rather than the
    36 R6 names, `tests/r6/check-tool-identity.mjs` now shares the one
    definition instead of duplicating it, and R6 keeps no exported function
    that launches a process. `tests/r6/test-fresh-bootstrap.mjs` gained a
    fresh-tree regression that deletes `build/` and runs both later-stage
    checkers directly: each must refuse for the **artifact** reason, must not
    say `drift`, must not name `TMPDIR` or an R6 scratch fault, and must leave
    no `build/r3`, no `build/r5`, and in fact no `build/` at all.
12. **The image differential still required a previous R5 build.** With
    finding 11 fixed, a fresh standalone `./be r6-check` reached
    `r6-report` and was refused there with `D-01 gcc claims parity with the
    accepted image`. `tests/r6/check-fixture-image.mjs` compares each image
    against `build/r5/<toolchain>/beryllium.bin` and correctly records
    `accepted_image_parity=not-available` when that build is absent, but
    `tests/r6/check-report.mjs` demanded `differs` for every dynamic image and
    `identical` for the control image unconditionally. The accepted R5 image is
    a build product of the accepted R5 target and of no R6 target, so this was
    the same class of defect as finding 11 -- an undeclared dependency on a
    previous package's build -- again masked by `make check` running R5 first.
    **Resolved** by measuring instead of demanding, the same way the package
    state is measured. `check-report.mjs` now measures
    `build/r5/<toolchain>/beryllium.bin` itself, requires the eligibility
    record to bind the digest it measured, requires the published parity to
    equal the eligibility record's, and requires the published parity to follow
    the measurement in **both** directions: parity is demanded exactly when the
    accepted image exists, and a parity claim is refused when it does not. R6
    therefore never fabricates a comparison it did not make and never suppresses
    one it did, and neither deleting nor restoring `build/r5` changes what it
    will accept. A second rejection case,
    `dynamic-<id>-accepted-parity-suppressed`, forges the opposite direction of
    the existing `-claimed` case, and both are state-toggling so neither is a
    no-op in either tree state; the pinned rejection-suite size moved from 1408
    to 1424 mutations and 1461 to 1477 refusals accordingly. The bounded
    regression for this finding is those two toggling forgeries plus the
    standing requirement that a fresh standalone `./be r6-check` pass with no
    `build/` present; the absent-`build/r5` branch itself is exercised by that
    full standalone run rather than by a sandboxed self-test, because
    `check-report.mjs` measures the real worktree root by construction.

## Claims

The evidence supports exactly this bounded, QEMU-only statement about the
unaccepted R6 candidate package -- measured in whichever integration state the
tree is in -- against the accepted R5 baseline:

> In the fixed single-hart QEMU `virt` profile, with pinned OpenSBI and the
> byte-immutable accepted R5 target `165f4d001a2b59b582b397bdea79ec4826168fdb`,
> 46 separately constructed single-defect adversarial fixtures were each
> rejected or terminated fail-closed at their declared layer: 14
> image-construction defects were rejected before any execution, four by the
> accepted source inventory, four by accepted linker assertions, and six by the
> accepted image checker; 17 host-mechanism defects produced their exact stable
> error class; and 15 dynamic defects each terminated at the declared phase with
> the exact stable error class, the declared last console marker, no forbidden
> marker, and a monitor-issued SBI SRST shutdown, over two toolchains and two
> runs each. Each dynamic image additionally differed from its same-toolchain
> control image by exactly the one declared delta and in no other byte.

## Non-claims and exclusions

R6 does **not** claim:

- any acceptance of the R6 implementation; it is complete-local and
  `not-reviewed`, with `r6_accepted_commit=none`, in both the untracked and the
  committed-candidate integration state;
- that malicious or arbitrary guests are universally contained; the catalogue is
  finite and enumerated, not exhaustive;
- that a declared accepted-image-checker rejection makes a dynamic fixture safe
  on its own; safety for those images rests on the L8 single-delta comparison
  against a control image that passed the complete accepted checker, plus the
  immutable accepted G-stage roots;
- that the accepted R1, R3, and R4 acceptance checkers were left untouched;
  exactly six enumerated pin constants are refreshed, and no accepted mechanism
  byte changes;
- any hardware or emulator behavior for a genuinely skipped `HFENCE.GVMA`; only
  that the accepted checker rejects the unpaired construction (S-05) and that
  the monitor refuses an unacknowledged fence (D-11);
- formal verification, refinement, or proof of the mechanism or the fixtures;
- coverage of `shutdown-returned` or `shutdown-rejected` under QEMU; both are
  host-mechanism results only;
- general asynchronous interrupt handling; exactly one monitor-injected VS
  software interrupt is exercised, with no timer, external, or nested case;
- byte-identical raw QEMU traces, evidence bundles, or generated HTML;
- any property of a raw QEMU trace beyond its recorded SHA-256, byte count,
  bounded excerpt, and the canonical semantics derived from it; raw traces are
  ephemeral scratch, are deleted after extraction, and are never retained,
  digested as evidence files, or published;
- new R5 evidence or R5 re-acceptance from control fixture C-01;
- hardware validation, K3 results, multi-hart behavior, DMA/IOMMU behavior, or
  device isolation;
- Linux, service, driver, scheduling, restart, rollback, policy, capability,
  Type Enforcement, or CHERI behavior;
- a Model 0.1/0.2 proof or C-refinement transfer to R6, or a Helium claim or
  proof transfer to Beryllium;
- any R7 result, any acceptance, or any publication readiness.

Hardware validation: **NOT RUN**. Formal verification: **NOT RUN**. Multi-hart:
**out of scope**.

## Reproducibility boundaries

| Object | Claim |
| --- | --- |
| Canonical report | byte-identical across two generations from fixed artifacts |
| Console logs | SHA-256 identical across two toolchains and two runs |
| Canonical semantic tuples | identical across runs and toolchains |
| Host transcripts | byte-identical across both host binaries |
| Images | per-toolchain only; no cross-toolchain byte claim |
| Raw QEMU traces | **not** byte-identical, not claimed |
| Evidence bundle | **not** byte-identical, not claimed |
| Generated HTML | **not** byte-identical, not claimed |

Because each run records its raw-trace digests and byte counts, the report and
evidence-bundle digests quoted above are properties of the recorded local run,
not reproducibility claims. A later run produces the same 47 entries, the same
counts, the same classes, the same markers, and the same canonical semantics,
with different raw-trace digests.

The open generated-asset byte-reproducibility finding for the VitePress
documentation build remains **unresolved**, and R6 does not resolve it.

## Trust assumptions

1. Pinned GCC, Clang, GNU `ld`, `lld`, GNU Make, `bash`, and Node are trusted
   and digest-bound.
2. Pinned QEMU 10.2.2 and pinned OpenSBI are trusted and digest-bound; R6 does
   not model firmware defects and does not forge firmware.
3. The accepted R0-R5 mechanism is trusted as the measurement instrument; R6
   measures inputs against it and never modifies it.
4. QEMU faithfully models the bounded RISC-V H-extension behavior exercised
   here; QEMU is not hardware.
5. A single hart, no DMA, no external device, and no concurrency.

## Governance: R7, publication, and next steps

- R6 acceptance has **not** been granted. The next step is the responsible
  human's decision on `planning/single-hart-runtime-r6-review-summary.md`, the
  decision-neutral packet prepared under
  `.github/skills/human-review-summary/SKILL.md` against exact target
  `7ba3649f03cf13b65df33020e345d361cce2993a`. Until that decision is recorded,
  `r6_acceptance` stays `not-reviewed` and `r6_accepted_commit` stays `none`.
- R7 remains gated and undefined. R6 acceptance would not authorize it, and no
  R7 content exists.
- Push, tag, publication, and release remain blocked. R6 does not touch
  `pathfinder/publication-gate.conf` and cannot infer approval.
- No automated agent may add a human `Signed-off-by`, record acceptance, or
  represent itself as a human co-developer.
