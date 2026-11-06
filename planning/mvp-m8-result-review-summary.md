<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M8 result review summary

This packet presents the result of M8, "The first verification plan", the
milestone the accepted
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
(`27d2e557`, S3-C.4) added to the [MVP plan](mvp-plan.md): a concrete
operational model of the protocol in Rocq (stage 1) with its ordering
premises discharged by litmus tests, a frozen specification with the human
as reviewer of record, a pinned verifier image, and a pilot of three
C-verification arms on two leaves judged by a decision rule registered
before any arm ran. It was implemented under the accepted
[M8 plan](mvp-m8-plan.md) (`7a0c74ae`), whose
[acceptance record](mvp-m8-plan-review-summary.md) holds its
authorization, with Q10 answered (`with CN`), Q1 to Q9 and Q11 to Q17 at
their defaults, errata 1 to 3 (the model and bridge lanes re-set to
12,000), stop 5's decision A (WP with Alt-Ergo alone), and the two stop 2
decisions (Revision 1 and a re-run; erratum S-5). **Its outcome is
inconclusive under the plan's own rule, recorded as the plan says a valid
outcome is recorded: the claim is unchanged.** It also records the
responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`12b0e71b908e36041745601d214c03a5be34ad1e` (the M8 result commit `R`,
parent `9af19d81350ce5f753f13f316368d0259c059aac`, over the gates'
commit `X` = `f181384192bd4a79df52ba7cdb5dfbed55ab3307`) as the M8 result
on 2026-11-04 (00:45 in the human's time zone). The instruction, given in
reply to this packet's request to accept, revise, or defer that exact
commit, was `accept 12b0e71b`; the abbreviation was checked to resolve
uniquely (`git rev-parse --disambiguate=12b0e71b`). With it the human
accepted the result as presented: the **inconclusive** outcome under the
plan's D-7 (no C-level contract proof of any monitor function; the claim
unchanged; the ledger's stage-1 rows C-51 to C-55, U-16, the restated
U-11, U-13, and C-06, and the third review item; the recommendation per
claim class non-load-bearing), the specification's fourteen errata as
errata (S-5 among them, the human's `room_row=erratum_s5`), item 93's
dry-run fix cherry-picked from M9's accepted line for the gates' sake,
item 124's per-lane ledger IDs to be renumbered by the second line to
integrate, and item 125's tool limits left to the human's choice on
upstream reports. The instruction directed no fast-forward, merge, push,
snapshot refresh, or successor: each keeps its own gate; the development
branch stays at `55047781` locally and on the private `origin`, and
`beryllium/mvp-m8` is pushed only through that commit. M7's, M8's, and
M9's results are now accepted, so M10's plan (release candidate 4) may be
written on the human's `go`; it re-runs every M8 proof and arm at RC4's
tree before any pin is re-derived (S3-C.7).

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `12b0e71b908e36041745601d214c03a5be34ad1e` (the M8 result commit `R`, parent `9af19d81350ce5f753f13f316368d0259c059aac`, over the gates' commit `X` = `f181384192bd4a79df52ba7cdb5dfbed55ab3307`), on local branch `beryllium/mvp-m8` from the M8 plan's acceptance record `6fbcc3d1` (the target commit). `X` is the merge of the arms' re-run (`2e298c3a`), the ledger's stage-1 rows and the review item (`a9323ed5`), and item 93's dry-run fix cherry-picked from M9's accepted line (`f1813841`); `R` adds over `X` only the plan's decision record, the evidence record `planning/mvp-m8-evidence.md`, and the README's records; no monitor, model, verification, test, or tool byte follows `X`. |
| Current status | **Responsible-human accepted on 2026-11-04** (instruction `accept 12b0e71b`; the [decision record](#decision-record)). As presented: implemented and run to its recorded outcome; reviewed line by line by the session before each merge; the gates pass at `X` from a standalone clean clone at `X` (2026-11-04; `build/m8-gates/final/` in the clone), `./mvp/mvp verify` among them (`wall_seconds=13480`, 3 h 45 min); `./mvp/mvp claim-ledger check` passes at `R` (`claims=55 boundary=16 review_items=3`). No board step (the plan has none). |
| Decision requested | As presented: accept exact commit `12b0e71b908e36041745601d214c03a5be34ad1e` as the M8 result, with the outcome **inconclusive** (no C-level contract proof; the claim unchanged; the stage-1 rows and the review item added; the recommendation per claim class non-load-bearing); or request revisions; or defer. With it: the departures in section 5 and the ledger-ID note (item 124). |
| Successor status | As presented and after the decision: not started and not authorized: M10 (release candidate 4) is a plan to write after the M8 and M9 results are accepted (M9's is, `892b68c8`, 2026-11-03); M10 runs every M8 proof and arm again at RC4's exact tree before any pin is re-derived (S3-C.7's merge-order rule), since M9 changed `mvp-sbi.c`, Leaf A's translation unit. |
| Publication status | Private repository (the internal one). As presented and after the decision: `beryllium/mvp-m8` is pushed through `55047781` (the M8-5 push record) and local after it; `beryllium/mvp-m8-plan` is pushed; the development branch is at `55047781` locally and on the private `origin`; no tag, publication, release step, or snapshot refresh. |

As presented: please review exact commit
`12b0e71b908e36041745601d214c03a5be34ad1e` and accept it, request
revisions, or defer. Outcome: accepted; see the
[decision record](#decision-record).

## 2. Deliverables

| Deliverable | Paths | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| The specification (M8-2; `004f31ae`, **accepted** as reviewer of record 2026-11-02; Revision 1 `93a8d136`, **accepted** 2026-11-03) | `planning/mvp-m8-specifications.md`, `planning/mvp-m8-specifications-revision-1-review-summary.md` | P1 to P9 over the protocol, E1 to E9 for the denial leaf, the ring's per-function rows; drafted without reading the C, frozen by hash | Accepted separately; fourteen errata recorded (S-1 to S-5 in the plan's decision record; R1-1 to R1-9 in the document), none a code defect | Already decided; S-5 is new: is the `room` row's reading (the code's stricter malformed-tail rule is the header's contract) acceptable as an erratum rather than a code defect? |
| Stage 1 (M8-3; `0ae59356`, merged `5f02a5f3`) | `model/proof/Concrete.v`, `ConcreteRings.v`, `ConcreteBridge.v`, `ConcreteClaims.v`, `ConcreteAssumptions.v`, `ConcreteLayout.v` (generated); `model/tests/run-concrete.sh`, `check-concrete-readings.sh`, `check-concrete-tools.sh`; `model/tools/gen-concrete-layout.py`; `model/Makefile` (+1) | 26 theorems over a concrete operational model of three harts, the rings, the barrier, the exit and management paths, and the input path; every assumption closed; 92 source readings by symbol at the target commit, gate-checked; the lineage of Model 0.2's 24 and M3's 22 theorems | A proof about an abstract model, never about the C; sequentially consistent interleaving with five premises; the accepted modules unchanged | Is the model faithful where it matters: `measure_log()`'s place, the exit ceiling, the parked domain, the barrier's published words (errata S-1 to S-4 are where the first reading was not)? Is the one stated premise (pages in GPA order) acceptable? |
| The litmus tests (M8-4; `a9eb534b`, merged `14851913`) | `mvp/verify/litmus/L1.litmus` to `L5.litmus`, `qualify/`, `sequences.txt`, `sequences/` (55 symbols per toolchain); `mvp/verify/tools/litmus.py` | The five ordering premises discharged for the compiled sequences under herd7 7.58's RVWMO; each `Never`, each ablation `Sometimes`; the sequences check first in `verify` | The axiomatic model, not the hardware; `blt`/`bne` stand in for `bltu`/`bnez` | Do the tests mirror the sequences they cite (the excerpts beside the disassembly in `sequences.txt`)? |
| The verifier (M8-5; `48652b03`) | `mvp/tools/verifier/` (Containerfile, `closure.txt` 481 NEVRAs, `closure.py`, `fetch-sources.py`, `sources.txt`, `build-image.sh`, `verify.sh`), `./mvp/mvp verify`, `mvp/verify/tools/qualify.py`, `token-equal.py`, `digests.py`, `mvp/verify/target-digests.txt`, `qualify/` fixtures | The pinned image (Fedora RPMs by NEVRA and SHA-256; `herdtools7`, CN, Cerberus, `monomorphic` from a verified source cache; `--network=none`); the qualification matrix (6 of 9 pairs); the leaf's digests; the token gate | Items 1 to 3 of D-7; WP with Z3 unsound (item 117) and CBMC with Z3 non-terminating, excluded before any leaf goal | Is the exclusion of the two pairs, and the WP arm's recorded status under decision A, what you intended? |
| The pilot's arms (M8-6; first run `bc98a875`, `0b45698e`; re-run `b2f40b1d` to `d31b6362`, merged `2e298c3a`) | `mvp/verify/wp/*.acsl`, `why3.conf`, `cn/mvp-sbi-leaf.c`, `cbmc/leaf-a/harness.c`, `cbmc/ring/*.c`, `tools/{arm-lib,wp-arm,cn-arm,cbmc-leaf-a,cbmc-ring}.py`; `mvp/results/20261103-verify/` (36 files), `20261103-verify-r1/` (28 files) | WP OPEN 130/134; CN OPEN 5/55; CBMC Leaf A SUCCESSFUL 336/336 (bounded); the ring OPEN at its bound with S-5; 24 seeded mutants per leaf per arm; the two runs retained | No positive result; the records are findings, not claims; CBMC's result is a bounded model check and never a proof | Is the outcome's classification (inconclusive, not "no vehicle fits") and the recommendation per claim class the reading you want recorded? |
| The words (M8-7; `a9323ed5`) | `mvp/docs/claim-ledger.json`/`.md` (C-51 to C-55, U-16; U-11, U-13, C-06 restated), `mvp/docs/claim.md` (the third review item in the phrasings' list only) | The stage-1 rows as D-11 words them; the review item recording the outcome; the claim's blockquote and required limit unchanged | Stop (d) not reached: the only `claim.md` edit is the review item D-11 calls for | Do the five rows say "a proof about the abstract model" and nothing that reads as a proof of the C? |
| The dry run's window (M8-7; `f1813841`, cherry-picked from M9's accepted `b7e059b5`) | `mvp/tests/fake-uboot.py`, `mvp/tests/run-tool-dry-run.sh` | The fake U-Boot's autoboot window the board's 3 s with lateness reported as such (item 93), so that `check` and `evaluate` do not flake on the harness's timing; test files only | Not M8's; the same change you accepted in M9's result on 2026-11-03 | Is carrying an accepted harness fix across the lanes for the gates' sake acceptable in M8's result? |
| The evidence record and the log (M8-7; `R`) | `planning/mvp-m8-evidence.md`; `mvp/README.md` (the M8 entries; items 101 closed, 118, 124); `planning/mvp-m8-plan.md`'s decision record | The outcome first; the lineage; the premises; the qualification matrix; the arms; H38 and H41; the departures; the gates | — | Are the departures and the open items complete and honest? |

Exact changed-file inventory from the M8 base to `X`, outside the two
record directories (64 files) and the compiled-sequence excerpts (55
files):

```text
# git diff --name-status 6fbcc3d1 f1813841 | grep -v -e '^A.mvp/results/' -e 'mvp/verify/litmus/sequences/'
M	.github/copilot-instructions.md
M	model/Makefile
A	model/proof/Concrete.v  ConcreteAssumptions.v  ConcreteBridge.v  ConcreteClaims.v  ConcreteLayout.v  ConcreteRings.v
A	model/tests/check-concrete-readings.sh  check-concrete-tools.sh  run-concrete.sh
A	model/tools/gen-concrete-layout.py
M	mvp/README.md  mvp/mvp  mvp/tools.mk  mvp/tools/make-control.py
M	mvp/docs/claim.md  mvp/docs/claim-ledger.json  mvp/docs/claim-ledger.md
M	mvp/tests/fake-uboot.py  mvp/tests/run-tool-dry-run.sh
A	mvp/tools/verifier/Containerfile  build-image.sh  closure.py  closure.txt  fetch-sources.py  sources.txt  verify.sh
A	mvp/verify/cbmc/leaf-a/harness.c
A	mvp/verify/cbmc/ring/{acquire,init,peak,post,post_words,publish,published,record_bytes,record_word,release,reset,room,sequence,take,taken}.c  harness.h
A	mvp/verify/cn/mvp-sbi-leaf.c
A	mvp/verify/litmus/L1.litmus … L5.litmus  qualify/{MP,MP+fence.r.r+fence.r.r,MP+fence.w.w+fence.r.r,MP+fence.w.w+fence.r.r+filter,MP+fence.w.w+fence.r.r+sc}.litmus  sequences.txt
A	mvp/verify/qualify/{cbmc,cn,wp}/{known-pass,known-fail,vacuity-requires,vacuity-ensures,wrong-implementation}.c  expectations.json
A	mvp/verify/target-digests.txt
A	mvp/verify/tools/{arm-lib,cbmc-leaf-a,cbmc-ring,cn-arm,digests,litmus,mutate,qualify,token-equal,wp-arm}.py  in-image.sh  in-image-ring.sh
A	mvp/verify/wp/mvp-sbi-leaf.acsl  round-1.acsl  why3.conf
M	planning/.vitepress/config.mts  planning/HANDOFF.md  planning/README.md  planning/roadmap.md  planning/mvp-m8-plan.md  planning/open-tooling.md  planning/research-synthesis.md
A	planning/mvp-m8-specifications.md  planning/mvp-m8-specifications-revision-1-review-summary.md
```

No file under `mvp/src/`, `mvp/guest/`, `mvp/scenarios/`, `tests/r*/`,
`bringup/`, or `pathfinder/` changes, and no accepted model module
(`Model.v`, `Policy.v`, `Binding.v`, and the rest) changes; the one
`model/Makefile` line is D-1's enumerated addition. Stop 1 was not
reached.

## 3. Claim boundary

**What `R` supports saying:** nothing new in the claim's blockquote or
its required limit, which are unchanged; in the ledger, five rows with the
method `proof about the abstract model` (and `semantic checker` for the
litmus tests), each worded "in the concrete operational model (stage 1)
under sequentially consistent interleaving, with ordering premises L1 to
L5 discharged by litmus tests": the barrier's published words and the
launch gate (C-51), one writer per word per phase carried to every
concrete step (C-52), the rings' safety, integrity, and drain (C-53), the
denial below the exit ceiling (C-54), and management decided by the
control hart against the grants (C-55); and the review item, which says
what the pilot did not give.

**What remains trusted or assumed:** the model's faithfulness to the
sources, read by symbol and gate-checked but not derived from the code;
the five premises beyond the compiled sequences' ordering under the
axiomatic model; the firmware's HSM start and IPI delivery; the one stated
premise on the scenarios' page order; the locked compilers and the
executor (claim class (d), assumed).

**What is unavailable or `NOT RUN`:** a C-level contract proof of any
function (WP OPEN on four true goals that time out, CN OPEN on tool
limits); the ring's bounded check beyond its 600 s bound at 4,096 bytes;
WP's Rocq export (Q17, not qualified); the M8 arms at a tree that holds
M9's changes (M10's re-proof); hardware (the plan has no board step).

**What the commit does not implement:** a refinement between the model
and the C; a measured-boot, measurement, or M9 content (its lane); any
promotion of a tool role (the recommendation is non-load-bearing until the
promotion gates hold); Model 0.3 (2.0's, Q35); any change to the monitor.

## 4. Security and correctness invariants

| Property | Contract | Implementation | Test or evidence |
| --- | --- | --- | --- |
| The decision rule was registered before any arm ran and was not loosened after a result | the plan's D-7; stop 5's decision A recorded before the arms ran | `mvp/verify/tools/arm-lib.py`'s verdict rule (OPEN on any unproved goal; a pair not formed under one solver) | each arm's `rounds.txt` and `goals.txt`; the WP vacuity rule left `not-ok` after the result |
| The leaf is the target commit's | D-7 item 3 | `digests.py` and `target-digests.txt` (13 files; the specification by its commit's blob) | `BE_MVP_TARGET_DIGESTS: PASS files=13` in every `verify` |
| Every stage-1 theorem is closed, with no axiom, parameter, or admitted term | stop 1; D-1 | `ConcreteAssumptions.v`; `run-concrete.sh`'s per-theorem reports | `assumptions_closed=26`; the escape-hatch pattern check |
| The source readings cite symbols that exist at the target commit | D-2; item 101 | `check-concrete-readings.sh` | `citations=92` checked; `ConcreteLayout.v` equal to the generator's output |
| The verifier runs offline from pinned inputs | D-7 item 1; D-10 | `closure.txt`, `sources.txt`, `--network=none` | `BE_MVP_VERIFY: rpms PASS … sources PASS`; the image tag names the closure's and sources' digests |
| Mutants are judged, never assumed | D-7 item 6 | `mutate.py` (seed `0x4d38`, 24 per leaf); each arm's `mutants.txt` | killed, unobservable (by the host test), compile-error, masked, or a finding, each named |

## 5. Review history, stops, and errata

- **Steering:** the plan was written from two read-only fact sheets; no
  independent review of the implementation by another model (the SOP).
- **Stop 6, three times:** errata 1 (model lane 6,000 → 12,000, at 6,278
  with two of five modules), 2 (bridge lane 3,000 → 6,000 after M8-5),
  3 (bridge lane → 12,000 at about 9,250 after the first run); at `X`
  8,544, 11,811, and the tool-glue lane 1,473 of 2,500.
- **Stop 5:** WP's solver pair: Z3 unsound through why3 on WP's prelude
  (item 117), cvc5 hanging; decision A: Alt-Ergo alone as a recorded arm
  that cannot meet item 7; CN the arm that could give a positive result.
- **Stop 2, the first time:** nine specification clauses against the
  leaves, which do what the M1 plan's accepted entry and the ring header's
  contracts say; decision `revision_1_rerun`; Revision 1 accepted
  (`93a8d136`); the arms re-run.
- **Stop 2, the second time:** the `room` row (R1-6); decision
  `erratum_s5`, no Revision 2, no re-run.
- **The outcome reading** confirmed by the human (`outcome_reading=true`):
  inconclusive; the claim unchanged.
- **Errata S-1 to S-4** found by stage 1's proofs (P1 scoped to the
  block's immutable words; P5 below the exit ceiling; the parked domain
  still takes a terminate; `mgmt_answered_once` as safety), recorded in
  the plan, not the document, which stage 1 cites at its first hash.
- **Housekeeping findings:** item 117 (WP with Z3 unsound; a report
  upstream is the human's choice), item 118 (a timed-out cvc5 leaves about
  1 GB of temporary files), the WP arm's two dead code paths under the
  contract (true observations of defensive code the contract excludes,
  harmless), the CBMC contract finding m12 (the host test calls the leaf
  with `out == NULL`, outside 4.3's domain).
- **The gates' three attempts:** the first at `2e298c3a` passed `check`
  and stopped at `evaluate` for want of the OpenSBI firmware in the fresh
  clone (hard-linked in); the second failed `check` in the dry run's
  `missed-s-retry` case at a load average of 1.5 (item 93, the harness's
  0.08 s margin); the fix M9's accepted line holds was cherry-picked
  (`f1813841`) and the gates ran again there.
- **Item 124, the ledger IDs:** M8's rows C-51 to C-55 and U-16 and M9's
  accepted C-51 to C-53, U-16, U-17 are numbered per lane; the second line
  to integrate into the development branch renumbers its rows and the
  documents that cite them keep the numbers as assigned at acceptance.
- **Open questions for your judgment:** whether CN's tool limits warrant a
  report upstream now or at M10; whether the WP arm's four timeouts are
  worth a fourth round at M10's re-proof (allowed by Q6, not tried);
  whether M10's re-proof should run the arms at RC4's tree before or after
  M9's log is read into stage 1's `launch gate` predicate.

## 6. Validation and retained evidence

All at `X` = `f181384192bd4a79df52ba7cdb5dfbed55ab3307`, from a standalone
clean clone at `X` (2026-11-04, 01:50 to 06:00 UTC), each gate's log under
`build/m8-gates/final/` in the clone (outside the tree): `./mvp/mvp tool-lock check` PASS (01:50); `./mvp/mvp check` `BE_MVP_CHECK: PASS` (01:50 to 02:00: `BE_MVP_QEMU: PASS runs=62 attempts=74 refused=12`, `BE_MVP_CAPTURE_SELF_TEST: PASS cases=164`, `mutations=399`, the dry run PASS with its autoboot check, `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=55 boundary=16`, the bundle `files=354 images=315`); `./mvp/mvp evaluate` PASS (02:00 to 02:11; `BE_MVP_IMAGE_IDENTITY: PASS images=315 same=315 differing=0`); `./mvp/mvp claim-ledger check` PASS (`review_items=3`); `./be model-check` PASS (02:11 to 02:14; `Beryllium MVP concrete model (stage 1): PASS theorems=26 assumptions_closed=26 citations=92`, the input ring's four theorems, `BE_MODEL_DIFFERENTIAL: PASS … comparisons=241`); `./be evaluate` `Model 0.2 rootless evidence PASS` (02:14 to 02:16); `./mvp/mvp verify` `BE_MVP_VERIFY: PASS` (02:16 to 06:00, `wall_seconds=13480`: the sequences suite `symbols=55`, the digests `files=13`, the token gate `tokens=686`, `BE_MVP_QUALIFY: PASS arms=9 qualified=6`, `BE_MVP_LITMUS: PASS premises=5 never=5`, `BE_MVP_WP_ARM: OPEN goals=134 proved=130`, `BE_MVP_CN_ARM: OPEN goals=55 proved=5`, `BE_MVP_CBMC_LEAF_A: SUCCESSFUL properties=336 failed=0`, `BE_MVP_CBMC_RING: OPEN … checked=13547 open=1384`, every verdict the re-run's).
At `R`: `./mvp/mvp claim-ledger check` PASS (`claims=55 boundary=16
review_items=3`); `node scripts/check-doc-sources.mjs` PASS; `git diff
--check` clean. Retained: `mvp/results/20261103-verify/` and
`20261103-verify-r1/` (the arms' two runs), `mvp/verify/litmus/sequences.txt`
and `target-digests.txt` (the exact inputs), and the evidence record. Not
run: any board step; the arms at any tree but the target commit's.

## 7. Recommended human review sequence

```sh
git worktree add --detach /tmp/be-m8-review 12b0e71b908e36041745601d214c03a5be34ad1e
```

1. **The outcome and the claim** (10 min): the evidence record's first
   section; `git show 12b0e71b908e36041745601d214c03a5be34ad1e:mvp/docs/claim.md` (only the third review item
   differs from the M7 text); the ledger's C-51 to C-55, U-16, and the
   restated U-11, U-13, C-06.
2. **The specification's errata** (15 min): the plan's decision record
   (S-1 to S-5) and the document's "Revision 1" table; `mvp-ring.c`
   `be_mvp_ring_room` and `mvp-ring.h`'s contract against R1-6
   (`mvp/results/20261103-verify-r1/leaf-b/defect-room.txt`).
3. **Stage 1** (30 min): `ConcreteClaims.v`'s index comment and
   `stage1_claim_set`; `Concrete.v`'s step relation and footprints;
   `ConcreteBridge.v`'s `single_writer_carried` and `roots_from_instance`;
   `model/tests/run-concrete.sh`'s PASS line in the gates' log.
4. **The arms' records** (20 min): `20261103-verify-r1/leaf-a/wp/goals.txt`
   and `rounds.txt` (the four open goals), `cn/goals.txt` (the tool
   limits), `cbmc/mutants.txt` (m04, m12), `leaf-b/summary.json`.
5. **The qualification** (10 min): the evidence record's matrix; the
   verifier's `verify.txt` lines in the gates' log.
6. **The gates** (5 min): `build/m8-gates/final/driver.txt` in the clone.

## 8. Human decision checklist

- [ ] The scope matches the accepted M8 plan (M8-2 to M8-7, Q10 with CN,
      the rest at their defaults, errata 1 to 3, stop 5's A, the two stop
      2 decisions).
- [ ] The outcome's classification (inconclusive; not "no vehicle fits")
      and the recommendation per claim class are the reading you want
      recorded, non-load-bearing.
- [ ] The claim is unchanged, and the ledger's five rows and the review
      item say "a proof about the abstract model" and nothing more.
- [ ] The fourteen specification errata are errata, not code defects
      (S-5 included).
- [ ] The trust assumptions are acceptable: the model's faithfulness by
      symbol readings; the five premises under the axiomatic model; the
      firmware; the one page-order premise.
- [ ] Item 124's renumbering rule at integration is acceptable.
- [ ] Successor work stays excluded: M10's plan is next, with the
      re-proof at RC4's tree.
- [ ] Exact commit `12b0e71b908e36041745601d214c03a5be34ad1e` is accepted, revisions are requested, or the
      review is deferred.

## 9. After the decision

- **Accept:** say `accept 12b0e71b`; the session records the acceptance in
  this packet's decision record, the M8 plan's decision record and status,
  the roadmap, the planning README, `HANDOFF.md`, the instructions, and
  `mvp/README.md`; nothing is fast-forwarded, merged, or pushed without
  its own instruction; M10's plan may then be written on your `go`.
- **Request revisions:** name them; a new commit and a new packet follow;
  `12b0e71b` is not treated as accepted.
- **Defer:** the branch stays as it is; no dependent work starts.

**Status:** M8 implemented through M8-7 at exact commit
`12b0e71b908e36041745601d214c03a5be34ad1e`, the gates passing at `X`,
`verify` among them, the outcome inconclusive and recorded;
**responsible-human accepted on 2026-11-04** (`accept 12b0e71b`; the
[decision record](#decision-record)).
**Next:** nothing waits on you on M8; M10's plan on your `go`; the
`ff + push` of the M8 and M9 lines when you want them; items 117, 118,
and 125 at your choice.
**Action required from you:** none on M8 (as presented: accept, request
revisions, or defer; outcome: accepted).
