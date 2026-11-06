<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R7 bounded exact-proof and evidence record

## Status and evidence boundary

This is an implementation and evidence record. It is **not** a decision record,
it records **no** responsible-human decision, and nothing in it may be read as
review, acceptance, authorization, or approval.

- R7 is **authorized**. The bounded plan
  [`single-hart-runtime-r7-plan.md`](single-hart-runtime-r7-plan.md) is
  responsible-human accepted at exact target
  `18c43596d308052cfad67edc6e2cb8f543f75600` on 2026-08-05, recorded in
  [`single-hart-runtime-r7-plan-review-summary.md`](single-hart-runtime-r7-plan-review-summary.md).
- **Plan revision R7-A** is separately responsible-human accepted at exact
  target `0605028220e3795d99393156d0bfb7d6a7d631a4` on 2026-08-05, recorded in
  [`single-hart-runtime-r7-plan-r7a-review-summary.md`](single-hart-runtime-r7-plan-r7a-review-summary.md).
  Its scope is `predecessor-acceptance-pin-enumeration-only`: it enumerates
  exactly six authorized predecessor acceptance-pin refreshes and changes no
  proof obligation, no cut point, no claim, and no non-goal of the original
  accepted plan.
- The `tests/r7/` package is **complete in the local working tree** and is
  offered as an exact **candidate commit**; its integration state is measured,
  not declared (`r7_integration=local-only-uncommitted` while no `tests/r7`
  path is tracked at `HEAD`, `r7_integration=committed-candidate-not-accepted`
  once it is). Root integration into `Makefile`, `be`, and
  `scripts/check-be.sh` has now been applied under accepted revision R7-A, and
  all six enumerated acceptance pins are re-derived at the exact prospective
  content and applied. No seventh acceptance update was needed or made.
- `r7_acceptance=not-reviewed` and `r7_accepted_commit=none`. Nothing here is
  accepted R7 evidence.
- The proof is **bounded**: `formal_verification=bounded-not-whole-system`.
  Beryllium is **not** formally verified, and no whole-image, whole-system, or
  C-refinement claim is made or implied.
- Hardware validation is **NOT RUN**. R8, push, tag, publication, and release
  remain **blocked**.

## Two distinct authorization statements

`be status` prints two R7 authorization statements. They are different facts
and must never be merged, reordered into one key, or rewritten:

| key | value | meaning |
| --- | --- | --- |
| `r7_authorization` | `not-authorized` | the accepted **R6** package's historical statement, reproduced verbatim as accepted history |
| `r7_authorization_source` | `accepted-r6-package-historical` | provenance of the line above |
| `r7_package_authorization` | `authorized` | the current live R7 authorization |

`scripts/check-be.sh` asserts that `r7_authorization` appears **exactly once**,
that it is immediately followed by its provenance key, and that the live
`r7_package_authorization` key is separate and also unique. The historical line
is accepted R6 content and is not corrected, retimed, or deleted here.

## Measured, not asserted

Package and integration state are measured from the repository, never declared:

| measured input | derived value |
| --- | --- |
| `git ls-tree -r --name-only HEAD -- tests/r7` is empty | `r7_package_implementation=complete-local`, `package_state=local-only-uncommitted`, `r7_integration=local-only-uncommitted` |
| `git ls-tree … -- tests/r7` is non-empty | `r7_integration=committed-candidate-not-accepted` |
| `r7-check` present in 0 of `Makefile`, `be`, `scripts/check-be.sh` | `root_integration=not-integrated` |
| present in 1-2 of the three | `root_integration=partially-integrated` |
| present in all three | `root_integration=root-integrated` |

Before this package is tracked the measured values are
`r7_head_tracked_paths=0`, `package_state=local-only-uncommitted`, and
`root_integration=root-integrated`; once it is tracked they become
`r7_head_tracked_paths` > 0 and
`package_state=committed-candidate-not-accepted`, with root integration
unchanged. Both root-scoped keys are **derived** from the measured
implementation state and never asserted: `r7_integration` from the tracked-path
measurement, and `r7_evidence_claim` from whether the report and evidence
artifacts have been generated. No state maps to a reviewed, accepted, or
published claim, and an unrecognised state is a refusal rather than a default.
With the artifacts generated the derived value is
`r7_evidence_claim=complete-local-not-reviewed`.

The report publishes a **separately scoped** key,
`r7_report_evidence_claim`, derived from `package_state`
(`generated-local-uncommitted-not-reviewed` before the package is tracked,
`generated-committed-candidate-not-reviewed` after). It is deliberately **not**
named `r7_evidence_claim`: the root key measures artifact presence, the report
key measures package tracking state, and the independent checker refuses a
report that carries the root-scoped name.

## Accepted inputs consumed and not modified

| input | exact commit |
| --- | --- |
| R7 plan | `18c43596d308052cfad67edc6e2cb8f543f75600` |
| R7 Plan revision R7-A | `0605028220e3795d99393156d0bfb7d6a7d631a4` |
| R1 mechanism | `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` |
| R2 implementation | `6e1cb579257c5dbe3234bd484fd091629e87181b` |
| R5 implementation | `165f4d001a2b59b582b397bdea79ec4826168fdb` (parent `9312c1355a23d411e3bdafb2183be342683a8ab9`) |
| R6 implementation | `7ba3649f03cf13b65df33020e345d361cce2993a` (parent `9ed5ad7069b6067f03e1923c09937fe218240a59`) |

R7 re-extracts, regenerates, re-proves, and re-states every result against the
accepted Beryllium images. No Helium theorem, constant, proof object,
implementation byte, or assurance claim transfers.

## Authorized predecessor acceptance-pin refreshes (exactly six)

Accepted Plan revision R7-A authorizes exactly these six constants, in this
order, and no other acceptance update. Every value below was **re-derived fresh
from the exact prospective content of this tree** after the last edit to any
bound file; none was copied from an earlier draft or from the retained
diagnostic patch.

| # | owning checker | constant | bound file |
| --- | --- | --- | --- |
| 1 | `tests/r1/check-acceptance.sh` | `successor_makefile_sha256` | root `Makefile` |
| 2 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` | `tests/r1/check-acceptance.sh` |
| 3 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` | `be` |
| 4 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` | `scripts/check-be.sh` |
| 5 | `tests/r4/check-accepted-content.mjs` | `approvedDeltaSha256` | `be` |
| 6 | `tests/r4/check-accepted-content.mjs` | `approvedDeltaSha256` | `scripts/check-be.sh` |

### Exact formulas

Pin 1 is a plain content digest of the successor root `Makefile`:

```text
successor_makefile_sha256 = SHA-256( bytes(Makefile) )
```

Pins 2-6 are approved target-to-current delta digests:

```text
approvedDeltaSha256 = SHA-256( targetMode || 0x00 ||
                               currentMode || 0x00 ||
                               targetBytes || 0x00 ||
                               currentBytes || 0x00 )
```

`targetMode`/`targetBytes` come from the owning checker's accepted commit
(`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` for R3,
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` for R4);
`currentMode`/`currentBytes` come from the working tree. Modes are the Git
literals `100644`/`100755`.

### Ordering

Pin 1 must be written into `tests/r1/check-acceptance.sh` **before** pin 2 is
computed, because pin 2 hashes that file's final bytes. All six were derived
and applied in the table order above, then re-derived once more at the final
content and confirmed unchanged.

### Modes are unchanged

No mode pin was touched. `tests/r1/check-acceptance.sh` keeps
`successor_makefile_mode=644`; the five delta-bound files keep mode `100755`
and the root `Makefile` keeps `100644` at both target and current. A mode
change is a hard failure, never a re-pin.

## Bounded exact-byte proof

| property | value |
| --- | --- |
| images | 2 (GCC/GNU ld and Clang/lld, accepted R5 recipes) |
| GCC allocated-image SHA-256 (pinned) | `46fdf832d26e3e8f3212a0fa78adc56bf45afcad11225656ab5b5d1dcab73d27` |
| Clang allocated-image SHA-256 (pinned) | `162a96462e722a622f6b362e10fa27517a08b16d7ae2f765070cfee580211994` |
| allocated sections behind each digest | 16 per image, pinned row by row (name, type, flags, address, size, content SHA-256) |
| allocated bytes | GCC 46856 file / 153352 memory; Clang 46096 file / 152592 memory |
| whole-ELF-file SHA-256 | recorded per run in the report; **not** pinned and **not** build-path independent (see below) |
| scoped symbols | 22 (11 per image) |
| scoped 32-bit words | 1420 (710 per image) |
| relocation-resolved targets | 144 (72 per image) |
| cross-check | direct ELF parser versus independently locked `riscv64-linux-gnu-objdump` 2.46-1.fc44, agreement `exact` |
| proof modules | 9 |
| theorems | 135 (plus 4 lemmas) |
| exported bundle | `be_r7_claims_hold : be_r7_claims` |
| generated proof input | reproduced twice and byte-compared before Rocq consumes it (`inputs=regenerated-identical`) |
| independent check | `rocq check`, `assumptions=closed` |

Module breakdown (`module_order` =
`ISA, ExactInput, Exact, Entry, Trap, Switch, ConfigurationTrace, Configuration, Claims`;
`ExactInput` and `ConfigurationTrace` are generated):

| module | theorems | lemmas | source SHA-256 (prefix) | bytes |
| --- | --- | --- | --- | --- |
| `ISA` | 4 | 4 | `d38f6e68569fe828` | 26946 |
| `Exact` | 50 | 0 | `7c5833bf7f0d0dab` | 44985 |
| `Entry` | 17 | 0 | `20ac52854865bb52` | 18191 |
| `Trap` | 6 | 0 | `41eb4492d3fd6283` | 20941 |
| `Switch` | 23 | 0 | `65246fd91c061769` | 24393 |
| `Configuration` | 34 | 0 | `63b89ad99466584b` | 24177 |
| `Claims` | 1 | 0 | `374473af6bf5eda1` | 4604 |

The proof covers only the enumerated privileged-wrapper symbols. It does not
cover `be_reset`, the C handlers, diagnostic output, SBI calls, guest fixtures,
or the remainder of either ELF merely because those bytes share an image.

## Generated fixed-configuration facts

| property | value |
| --- | --- |
| trace SHA-256 | recorded per run in the report; a **run identity**, because the trace binds the freshly regenerated accepted R5 report digest, and R5 does not claim byte-identical reports across launches |
| Rocq module SHA-256 | `aa1003ab64850838b5019b02b637e425f49c237eb65f78903b310207932a68eb` (stable while the derived facts below are unchanged) |
| resources | 13 |
| sealed authorities | 6 |
| domains | 2 |
| G-stage roots | 2 |
| leaves per root | 3 |
| total mappings | 6 |

The link from C state to these generated facts is an explicit assumption
(`fact-linkage` cut point), not a proved refinement.

## Supportable claim

> For the fixed single-hart QEMU profile and both pinned toolchains, a
> machine-checked bounded development consumes exact linked bytes from the
> accepted R5 runtime images, independently cross-checks those bytes with GNU
> objdump, decodes the enumerated privileged-wrapper subset, checks the fixed
> entry, trap-frame, root-install/fence/readback, restore, and return
> properties, and checks generated fixed-configuration facts against the
> accepted two-domain access matrix. The C implementation, direct ELF parser,
> compiler, linker outside the extracted symbols, OpenSBI, QEMU, RISC-V
> hardware, and the connection from C state to the generated configuration
> facts remain explicit assumptions. This is not a statement that Beryllium is
> formally verified.

## Evidence classes, cut points, and non-claims

Nine labelled evidence classes: `machine-checked-proof`,
`checked-generated-configuration-facts`, `host-tests`,
`image-semantic-checks`, `qemu-emulation`, `trusted-tools-and-parsers`,
`unproved-c-cut-points`, `hardware-validation`, `explicit-non-claims`.

Fifteen cut points, each an explicit unproved boundary: `c-mechanism`,
`c-trap-dispatch`, `c-pending-binding`, `c-validator`, `c-pte-builder`,
`fact-linkage`, `elf-parser`, `objdump`, `input-generator`, `rocq`,
`compiler`, `firmware`, `emulator`, `architecture`, `profile`.

Ten trusted boundaries and fourteen explicit non-claims are published in the
report and re-checked independently. The tenth boundary is the build-path
dependence of the recorded whole-ELF-file digest. `qemu_execution=not-re-run-in-r7`,
`c_refinement=not-claimed`, `whole_elf=not-claimed`,
`linux_service_device_multicore=out-of-scope`.

## Plan-obligation substitution

One accepted-plan obligation is **not** delivered as written. The report
publishes it as a structured `plan_obligation_substitutions` entry, the
evaluator prints `plan_obligation_substitutions=1`, and the independent
checker re-derives it; it is recorded here so no reader has to reconstruct it
from the JSON.

| field | value |
| --- | --- |
| plan obligation | the switch path "clears live guest GPR authority" |
| status | `substituted-narrower-byte-true-property` |
| delivered instead | every argument the proved assembly forms for the C cut point, and every value it publishes, is monitor-derived from the frame base or from a monitor CSR read; no guest-supplied register value reaches a call argument or a published control word |
| what is **not** proved | that the saved guest GPR contents are dead, zeroed, or otherwise cleared; they remain live in the trap frame across the C cut point |
| classification | plan-obligation substitution and an unproved cut point (`c-mechanism`, `c-trap-dispatch`), **not** a proved clearing claim |

The substituted property is byte-true over the extracted words. The stronger
plan wording is withdrawn, not silently satisfied. Any successor that needs
guest-GPR clearing must obtain a new bounded plan and prove it directly.

## Reproducibility bundle

| property | value |
| --- | --- |
| manifest entries | 30 |
| bundle files | 31 |
| payload bytes | 3946023 (observed run value, see below) |
| manifest bytes | 3249 |
| bundle bytes | 3949272 (observed run value, see below) |
| hard limit | 536870912 (512 MiB) |
| raw traces retained | 0 |
| raw objdump retained | 0 |
| duplicated predecessor traces | 0 |
| predecessor images retained | 0 |
| proof object hashes retained | 9 |
| proof objects retained | 0 |

Raw disassembly and proof objects are extracted into canonical semantics,
digests, and bounded excerpts, then deleted; only the digests and excerpts are
retained.

The two byte totals are **observed run values, not pins**. The report the
bundle carries embeds the HEAD commit and the measured package state, so the
totals shift when that state does: the same package measured
`payload=3911538 bundle=3914787` while `tests/r7` was untracked,
`payload=3911563 bundle=3914812` once it was tracked as a candidate,
`payload=3946023 bundle=3949272` in this warm tree after the clean-worktree
fixes recorded below enlarged the checked package, and
`payload=3946031 bundle=3949280` in a fresh detached worktree at the same
source state, where the report records R6's measured local state as
`report-generated` rather than `complete-local` because only the delegated
`r6-report` has run in that tree. All are four orders of magnitude below the
hard limit, which is the property that matters. No byte total here is a
reproducibility claim.

### What the bundle digests do and do not establish

The `artifacts.sha256` file and the manifest bind the **exact set of files in
one generated bundle** to each other: within a bundle, every payload file is
hashed, the manifest covers every file, and the independent checker recomputes
all of it. That integrity property is unchanged and is not weakened here.

Those digests are **run identities, not reproducible identities**. This
document therefore pins no bundle-level digest at all, and no such digest may
be re-pinned later:

| artifact | property | status |
| --- | --- | --- |
| generated proof input (`ExactInput.v`) | regenerated twice and byte-compared in the same run | deterministic, checked |
| generated configuration facts (`ConfigurationTrace.v`, trace JSON) | content-addressed, digest published above | deterministic, checked |
| report structure and canonical semantic fields | fixed key order, fixed derivation from a fixed checked input set | deterministic, checked |
| report file bytes | embed the HEAD commit and the measured package state | **not** byte-reproducible across commits |
| Rocq `.vo` proof objects | hashed as retained, but Rocq builds are not claimed bit-reproducible across hosts, toolchain builds, or environments | **not** byte-reproducible; observed run identity only |
| whole-ELF-file SHA-256 and file size | the accepted R5 recipes compile with `-g3 -gdwarf-4` and no `-fdebug-prefix-map`, so `DW_AT_comp_dir` carries the absolute path of the building worktree | **not** build-path independent; recorded as an observed run identity, never pinned |
| allocated-image SHA-256 (`be-r7-alloc-image-v1`) and its 16-row section table | covers the entry point and every `SHF_ALLOC` section header and content, and nothing else | build-path independent; measured equal in two worktrees at different absolute paths, and pinned in Rocq |
| `artifacts.sha256` and bundle byte count | derived from the above | **not** byte-reproducible; observed run identity only |

This is exactly what the ninth published trusted boundary states: a reader who
recomputes a `.vo` hash on another host and gets a different value has found
nothing about Beryllium, only about Rocq build reproducibility. The proof's
meaning rests on `rocq check` reporting `assumptions=closed` over the same
sources, not on any object-file hash.

## Local check results

All results below are **local, unreviewed, and unaccepted**.

| check | result |
| --- | --- |
| `./be r7-check` | PASS |
| `./be r7-evidence` | PASS |
| source inventory | PASS `total=20 present=20 pending=0 digest=66702f97453958300ab35deb26fe82cdcd7041088662af1faa4d0ec585ad6410` |
| tool boundary | PASS `controls=launcher-plus-parse-time` |
| predecessor prerequisite mark/verify | PASS `mode=verify-prerequisites regenerated=6 present=8 predecessors=r5,r6 mark=consumed` |
| predecessor prerequisite self-test | PASS `positive=2 rejected=20 inputs=8 delegated-targets=verified predecessors=r5,r6` |
| ELF extractor self-test | PASS `mutations=24 all-rejected=yes identity-cases=3 alloc-identity=build-path-independent` |
| disassembly cross-check self-test | PASS `mutations=11 all-rejected=yes` |
| configuration-trace self-test | PASS `determinism=yes mutations_rejected=40` |
| bounded proof | PASS `modules=9 inputs=regenerated-identical assumptions=closed checker=rocq-check` |
| report | PASS `schema=be-r7-exact-proof-evidence-v1 images=2 symbols=22 words=1420 targets=144 modules=9 theorems=135 predecessors=7 hardware=NOT-RUN` |
| evaluator | PASS `classes=9 cut-points=15 trusted=10 non-claims=14 hardware=NOT-RUN` |
| independent report check | PASS `checks=6186 objects=9` |
| evidence bundle | PASS `manifest-entries=30 bundle-files=31 payload-bytes=3946023 bundle-bytes=3949272 raw-traces=0` |
| independent evidence check | PASS `checks=571 files=31 acceptance=not-reviewed` |
| report generator self-test | PASS `staged=17 not-run=5 fail=7 hard-refusals=5 artifacts=11 determinism=yes` |
| report checker self-test | PASS `cases=122 rejected=122 accepted=0` |
| evidence checker self-test | PASS `cases=72 rejected=72 accepted=0` |
| predecessor interfaces | PASS `checked=7 interfaces=r0,r1,r2,r3,r4,r5,r6 all_accepted=yes` |

Report generation is deterministic for a fixed checked input set. Raw traces,
report bytes, proof objects, and evidence bundles are **not** claimed
byte-identical across independent launches, hosts, or commits; see the
reproducibility table above.

### Fresh detached worktree validation

The results above are from a warm tree. The same source state was also run from
two fresh detached worktrees, which is the validation these fixes exist for:

| validation | result |
| --- | --- |
| standalone-first `./be r7-check` in a clean worktree (no `build/` at all) | PASS |
| `./be r7-evidence` immediately after it in the same worktree | PASS, same `payload-bytes=3946031 bundle-bytes=3949280` |
| `npm ci && make check` in a second clean worktree | PASS |

The standalone run rebuilds the accepted R5 pipeline and the accepted R6
adversarial-image pipeline through their own launchers before any R7 stage, so
a single `./be r7-check` from an empty tree is now a long run; `./be r7-check`
already includes `r7-evidence`, so running both in sequence repeats that work.

## Clean-worktree validation defects and their fixes

An earlier R7 candidate passed only in a warm working tree. Three independent
defects were found by running the package in fresh detached worktrees, and all
three are fixed here. No fix touches production code, no fix changes a root
file or an acceptance pin, and none weakens an expected equality, difference,
cardinality, exact-byte, decode, or control-flow claim.

### Defect 1: the graph consumed an R5 artefact it did not rebuild

`r7-extract` delegated `r5-image` to the accepted R5 launcher, but the R7
configuration-trace stage reads the accepted R5 report at
`build/r5/reports/checked-switch.json` and deliberately refuses to regenerate
the heavy R5 pipeline itself. In a clean tree that report does not exist, so the
first `./be r7-check` failed; in a tree some earlier run had warmed, it silently
passed on a stale artefact.

Fix: `r7-extract` now delegates `r5-evidence`, the minimal accepted R5 target
that produces every canonical input R7 consumes. `r5-report` alone is **not**
sufficient and was measured failing from a clean tree, because R5's report
generator reads host-test output that only `r5-host-test` writes.

Regression tests, all in `tests/r7/check-configuration-trace.mjs`:

- `--mark-prerequisites` writes a single-use nonce mark before the delegated
  launch and `--verify-prerequisites` requires the accepted R5 report to exist
  and to be no older than that mark, then consumes the mark, so a stale report
  left by an earlier run cannot satisfy this run and a mark cannot be replayed.
  Both run inside `r7-extract`, so every package run proves the rebuild
  happened.
- A static guard reads `tests/r7/Makefile` and refuses any r7-extract recipe
  that delegates a predecessor target which does not produce every canonical
  input, or that does not bracket every delegated launch with the mark and the
  verify. It refuses the old `r5-image` shape by name.
- `--prerequisite-self-test`, run by `r7-check`, exercises two positive cases and
  twenty refusals on a hermetic fixture inside `build/r7`: ten mark/freshness
  refusals (replayed consumed mark, missing mark, missing required input, stale
  required input, empty required input, a required input that is not generated
  build output, foreign schema, empty nonce, wrong input set, malformed mark) and
  ten synthetic-recipe refusals (R5 delegated as `r5-image`, R5 delegated as
  `r5-report`, missing R5 delegation, missing R6 delegation, R6 delegated as
  `r6-static`, duplicated R6 delegation, an R6 launch before the mark, an R5
  launch after the verify, a missing mark, and a missing verify). It moves,
  deletes, and rewrites nothing outside `build/r7`, which keeps R7 inside its own
  write boundary.

There is deliberately no in-gate test that deletes `build/r5` or `build/r6` and
re-runs the package: that test is a clean detached worktree, and it is what
actually found these defects. What the gate proves on every run is the same
property in composition -- the recipe delegates producing targets (static
guard), the delegated launches really wrote all eight canonical inputs after
this run's single-use mark (mark/verify), and the verifier refuses a missing,
empty, stale, or non-generated input (hermetic self-test).

Only the R5 report is freshness-tested. The two ELF images are ordinary file
targets of the delegated Make graph, so an already up-to-date image is
legitimately not rewritten; requiring them to be newer than the mark would fail
a correct warm rebuild. Their existence is checked here, their currency is
Make's obligation, and their bytes are hashed and pinned downstream.

### Defect 2: a pinned identity that no other build path can satisfy

`tests/r7/proof/Exact.v` pinned the whole-ELF-**file** SHA-256 and file size of
both images. A fresh worktree therefore failed `Unable to unify true with false`
at the GCC image-identity theorem. The cause is not a semantic difference: the
accepted R5 recipes compile with `-g3 -gdwarf-4` and no `-fdebug-prefix-map`, so
`DW_AT_comp_dir` embeds the absolute path of the building worktree. Comparing
two builds of the same commit at different paths, only non-allocated bytes
differ -- GCC `.debug_info`, `.debug_macro`, `.debug_str`; Clang `.debug_info`,
`.debug_str`, `.debug_aranges`, and the `$d` mapping-symbol strings in
`.symtab`. Every `SHF_ALLOC` section, the entry point, the section count, the
symbol-table entry count, and every scoped symbol's address, size, and bytes are
identical, and `beryllium.bin` is byte-identical. Prior local validation passed
only because the pinned constants had been derived in the same worktree that
rebuilt the images.

Fix: pin the property that is actually exact and reproducible, and record the
one that is not.

- The extractor now also computes a schema-tagged `be-r7-alloc-image-v1`
  identity: the entry point, the allocated-section count, and one canonical row
  per `SHF_ALLOC` section (name, type, flags, address, size, content SHA-256) in
  section-header order -- exactly the bytes the loader maps and the hart
  executes.
- `Exact.v` pins that digest, both 16-row allocated-section tables, the
  allocated file/memory byte totals, the entry point, and the symbol-table entry
  count, and additionally proves that every allocated row really carries
  `SHF_ALLOC`, that the recorded totals are the sums of the pinned rows, that
  the two loadable images are distinct, and that all eleven scoped symbols lie
  wholly inside the pinned read-only executable `.monitor.text` row of their own
  image. The whole-file digest is still recorded, and the file-distinctness
  claim is retained, but it is no longer asserted to be reproducible.
- `check-report.mjs` re-derives the allocated-image identity from the ELF bytes
  with its own minimal section reader, sharing no code with the extractor, and
  refuses a report that restates it incorrectly. The report publishes the
  distinction (`elf_file_digest=observed-run-identity-build-path-dependent`,
  `elf_allocated_image_digest=reproducible-across-build-paths-and-pinned-in-rocq`)
  as a tenth trusted boundary.

Regression tests: `r7-check` now runs the extractor self-test, which was
previously a manually invoked check, and that self-test gained three identity
cases proving
the allocated identity is exactly the allocated section set, that mutating a
non-allocated `.debug_*` byte changes the file digest but neither the allocated
identity nor the symbols, and that mutating an executed byte does move the
allocated identity. The report checker gained rejection cases for a forged
allocated digest, a forged allocated section count, forged allocated file bytes,
a reproducibility claim the package does not support, and a dropped
`DW_AT_comp_dir` trusted boundary; the evidence checker gained a retained
allocated-identity manifest mutation.

This is a defect in the R7 implementation, not in the accepted plan. The plan
requires the extractor to **record** the ELF SHA-256, which it still does; it
nowhere requires that digest to be proved reproducible.

### Defect 3: a predecessor acceptance interface that reads generated artefacts

With defects 1 and 2 fixed, a fresh detached worktree got as far as the R7
report stage and then failed:

```
BE_R7_REPORT: FAIL predecessor r6 failed with status 1:
BE_R6:FAIL acceptance: the canonical R6 report has not been generated
```

The R7 report and its independent checker measure predecessor acceptance by
running each predecessor's own interface. `tests/r6/check-acceptance.sh
--require` is the only one of the six that reads generated build output: it
requires `build/r6/reports/adversarial-images.json` and the four transcripts
`report-check.txt`, `report-rejection.txt`, `committed-state.txt`, and
`baseline.txt`. R1's and R2's reports were already regenerated by the
configuration-trace stage itself, and R3's, R4's, and R5's interfaces read only
committed sources and git state, so R6 was the one remaining gap. It is the same
class of defect as defect 1: an input consumed but not produced.

Fix: `r7-extract` now also delegates `r6-report` through the accepted,
unmodified `tests/r6/run-make.sh`, inside the same prerequisite bracket and
after the R5 rebuild, because R6's own report stage re-verifies the accepted R5
baseline first. `r6-report` is the minimal accepted R6 target that writes all
five required artefacts; its recipe deletes them before regenerating them, so
all five are freshness-tested against the mark.

The cost is honest and deliberate: a standalone `./be r7-check` from a clean
tree now runs the full accepted R5 pipeline and the full accepted R6
adversarial-image pipeline before any R7 stage, and the repository gate runs the
R6 pipeline a second time. Reusing whatever `build/r6` happened to contain would
be faster and would reintroduce exactly the stale-artefact defect this section
records.

Regression tests:

- The prerequisite mark now covers eight canonical inputs across two
  predecessors, and `--verify-prerequisites` reports which predecessors it
  covered.
- The static Makefile guard is now per-predecessor: it requires exactly one
  delegated launch of each accepted predecessor launcher, requires each
  delegated target to be one that produces every canonical input, and requires
  the mark and the verify to bracket every launch.
- That guard is itself exercised over ten synthetic recipes in
  `--prerequisite-self-test` (listed under defect 1), so the shapes that broke a
  fresh worktree are proven to be rejected rather than merely absent, and the
  real Makefile is then held to the same guard.
- `tests/r7/check-sources.mjs` now declares both accepted cross-package
  dependencies and fails if either launcher is missing from the recipe.
- `--verify-prerequisites` additionally refuses a declared input that is not
  generated build output and one that is not a non-empty regular file, so a
  truncated or checked-in stand-in cannot satisfy the list.

An audit of every `build/` path any R7 stage reads confirms these eight are the
complete set of generated predecessor inputs; R7 produces everything else it
reads under `build/r7`.

This is also an R7 implementation defect, not a plan defect: accepted-plan gate
4 requires the package to rebuild what it measures through the accepted
launchers, which is exactly what the fix does.

## Predecessor and root-gate results

| check | result |
| --- | --- |
| `tests/r1/check-acceptance.sh --require` | PASS |
| `tests/r2/check-acceptance.sh --require` | PASS |
| `tests/r3/check-acceptance.sh --require` | PASS |
| `tests/r4/check-acceptance.sh --require` | PASS |
| `tests/r5/check-acceptance.sh --require` | PASS |
| `tests/r6/check-acceptance.sh --require` | PASS |
| `tests/r6/acceptance-pins.mjs` | PASS `pins-authorized=6 pins-required=6 pins-refreshed=6 root-integration=performed` |
| R3/R4/R5 accepted-content negative suites | PASS |
| `scripts/check-be.sh` | PASS |
| `./be docs-check` | PASS |

## Boundary and non-goals

R7 adds no file under `include/`, `virt/`, or `arch/`, and modifies no accepted
R0-R6 mechanism byte. Root integration is limited to `Makefile`, `be`,
`scripts/check-be.sh`, the six enumerated acceptance pins, maintained
planning/navigation/render sources, and generated planning HTML.

R7 does **not** establish: whole-image or whole-system formal verification; a C
refinement; a proof about `be_reset`, C handlers, guest fixtures, OpenSBI,
QEMU, or hardware; multicore, Linux, service, or device behavior; hardware
validation; or any basis for R8, publication, tagging, pushing, or release.

R7 acceptance requires an explicit responsible-human decision on an exact
implementation commit. This document records none.
