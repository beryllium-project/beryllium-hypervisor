<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M8 evidence record

This record holds the evidence of M8, "The first verification plan", on
branch `beryllium/mvp-m8`, made under the accepted [M8 plan](mvp-m8-plan.md)
(`7a0c74ae`, accepted 2026-11-02 with M8-2 to M8-7 authorized at the
acceptance record `6fbcc3d1`, the M8 base and the target commit) and the
accepted
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
(`27d2e557`, its section S3-C.4 and S3-C.7). It records what was run,
when, on which commit, and what it printed; it makes no claim beyond those
lines. The gates ran on exact commit `f181384192bd4a79df52ba7cdb5dfbed55ab3307` (`X`; a standalone clean clone
at `X`): the merge of the arms' re-run (`2e298c3a`), the ledger's stage-1
rows and the review item (`a9323ed5`), and the dry run's autoboot-window
fix cherry-picked from M9's accepted line (`f1813841`, below). The
commits after `X` hold only the plan's decision record, this record, the
README's records, and the packet: no monitor, model, verification, test,
or tool byte follows `X`. The result commit `R` adds the README's records
over this record; the packet, committed after it, names it.

## The outcome, first

Under the plan's decision rule (D-7), **the pilot's outcome is
inconclusive**: no arm met items 1 to 7 on Leaf A within its time box, so
no monitor function has a C-level contract proof, the claim is unchanged,
the pre-authorized sentence is not added, and the ledger gains the stage-1
rows and a review item (D-11). The reasons, per arm, against the
specification's Revision 1 (`93a8d136`, SHA-256 `aeb75682…`):

| Arm (Leaf A unless said) | Result | Why not a positive result |
| --- | --- | --- |
| WP (Frama-C 33.0, why3 1.8.2, Alt-Ergo 2.4.3) | OPEN, 130 of 134 goals; 18 of 24 mutants killed | four true goals (`D_inject_vsstatus_spp`, `_spie`, `_sie`, `_rest`) time out at 60 s in Alt-Ergo, which has no bit-level reasoning (`_rest` needs `&` distributed over `|`); CBMC proves the same postconditions; a tried second annotation round closed three of them and slowed other goals past the budget, so it was not adopted; and since stop 5's decision A the arm runs with Alt-Ergo alone, which cannot meet item 7 (Z3 is unsound through why3 1.8.2 on WP's prelude, item 117; cvc5 hangs under WP's memory limit) |
| CN (`cn` `cbe879c7`, Cerberus `68bdc84b`; Z3 4.16.0, cvc5 1.3.4) | OPEN, 5 of 55; 1 mutant killed, 1 unobservable | tool limits: the compound literal `*out = {0}` leaves a resource CN never releases (44 goals), `leaf_at`'s pointer liveness needs a `focus` a braceless loop cannot hold (5 goals), and `&`, `|`, `^` are uninterpreted (`HI_iff`); the pair formed; the token gate passes (686 tokens) |
| CBMC Leaf A (6.8.0; `sat`, cvc5) | **SUCCESSFUL**, 336 of 336 properties at unwind 4; 22 mutants killed, 1 unobservable (m04), 1 contract finding (m12); vacuity ok | a bounded model check, never a proof (D-8); the solver pair is `sat` and cvc5, not the plan's Z3 and cvc5 (CBMC with Z3 was non-terminating on the qualification's vacuity case); m12 (the null test on `out`) is neither killed nor shown unobservable: the host test observes it outside the contract's domain |
| CBMC Leaf B, the ring (6.8.0; `sat`, cvc5) | OPEN, 13,547 of 14,931 properties; 22 mutants killed, 1 unobservable (m18), 1 harness finding (m02); coverage and vacuity ok | 1,382 open properties are the 4,096-byte buffer parts, of which 3 of 512 position classes run within 600 s; 1 is `room` against R1-6, erratum S-5; the rest cvc5 timeouts where `sat` checked; a bound, not a verdict |

"No vehicle fits" is not the outcome: CN's grounds are tool limits a later
toolchain may lift and not structural; WP's are the solver pair's. The
**recommendation per claim class**, non-load-bearing until the promotion
gates hold (D-7): (a) pure decision functions over captured inputs: CN
remains the vehicle that can give a proof, with WP under Alt-Ergo as the
specification-debugging arm (it found two of the nine errata) and CBMC's
bounded check beside them; (b) ring-class code: CBMC's bounded per-call
checks, with the protocol's obligations stage 1's; (c) the cross-hart
protocol: stage 1 with its litmus premises; (d) compiled execution:
assumed, the locked compilers and the executor, no binary correspondence.

## What M8 adds, by work package

| Package | Exact commits | Delivers |
| --- | --- | --- |
| M8-2 the specification and the tools | `004f31ae` (the specification, frozen; **accepted** as reviewer of record 2026-11-02), `4b829fe4` (merged), `da9854b1`; Revision 1 `93a8d136` (**accepted** 2026-11-03) | `planning/mvp-m8-specifications.md` (P1 to P9, E1 to E9, the ring rows); `model/tools/gen-concrete-layout.py` and `ConcreteLayout.v`; `model/tests/check-concrete-readings.sh`, `check-concrete-tools.sh`; `mvp/verify/tools/mutate.py`; item 103's two sentences |
| M8-3 stage 1 | `0ae59356` (merged `5f02a5f3`); record `90e13508` | `model/proof/Concrete.v`, `ConcreteRings.v`, `ConcreteBridge.v`, `ConcreteClaims.v`, `ConcreteAssumptions.v` (with the generated `ConcreteLayout.v`, 7,450 lines): 26 theorems, every assumption closed, 92 source readings by symbol; `model/tests/run-concrete.sh`; one `model/Makefile` line; errata S-1 to S-4 found |
| M8-4 the litmus tests | `a9eb534b` (merged `14851913`) | `mvp/verify/litmus/L1.litmus` to `L5.litmus`, the qualification tests, `sequences.txt` (55 symbols per toolchain by digest), `tools/litmus.py`; the sequences suite first in `verify` |
| M8-5 the verifier | `48652b03` (merged) | `mvp/tools/verifier/` (the closure of 481 NEVRAs resolved in the pinned base, `sources.txt` with `herdtools7` 7.58, CN, Cerberus, `monomorphic` by SHA-256, the Containerfile, `verify.sh`), `./mvp/mvp verify`, `tools/token-equal.py`, `digests.py` and `target-digests.txt`, `qualify.py` and its fixtures; the qualification matrix |
| M8-6 first run | `bc98a875` (Leaf A), `0b45698e` (Leaf B) | the arms against the first freeze: every arm OPEN or FAILED on nine specification clauses (`mvp/results/20261103-verify/`); stop 2, decided `revision_1_rerun` |
| M8-6 re-run | `b2f40b1d` to `d31b6362` (merged `2e298c3a` = `X`) | the arms against Revision 1 (`mvp/results/20261103-verify-r1/`): the table above; erratum S-5 found; `digests.py` hashing the host's export of the pinned text in the image |
| M8-7 | `a9323ed5` (the ledger's rows and the review item), `f1813841` (item 93's dry-run fix, cherry-picked from M9's `b7e059b5`) = `X`; the plan's decision record, this record, the README's records; the packet | the outcome; the H38 and H41 record; the gates from the clean clone |

## The specification and its errata

The specification was drafted from the plans and the claim without reading
the C (D22), frozen by hash, and accepted by the human as reviewer of
record (`004f31ae`, SHA-256 `ade32fa6…`, 2026-11-02). Stage 1's proofs
found four errata (S-1 P1 holds for the block's immutable published words
only; S-2 P5 holds below the exit ceiling; S-3 a parked domain still takes
a terminate; S-4 `mgmt_answered_once` as a safety property with decisions
counted), recorded in the plan's decision record and not in the document;
stage 1 cites the first hash. The arms' first run found nine more, all
places where the specification's words departed from the M1 plan's
accepted denial entry or the ring header's contracts and the leaves did
what those say (R1-1 to R1-9); the human decided Revision 1 and a re-run
(`93a8d136`, SHA-256 `aeb75682…`, accepted 2026-11-03), which the arms
cite. The re-run found one more, S-5: R1-6's `room` row defines a
well-formed tail by the published head alone where `be_mvp_ring_room`,
as its header contract says, also fails the view for a tail more than a
capacity behind the cursor; the human chose to record it as an erratum
without a Revision 2 (the ring arm is OPEN at its bound either way). No
finding of the whole package is a code defect.

The frozen hash is the hash of the document's text at its accepted commit
(`git show COMMIT:PATH`), since an acceptance edit changes the working
file; `mvp/verify/tools/digests.py` pins it so, and inside the verifier
image, which has no git, hashes the copy `verify.sh` exports on the host
(a wrong copy fails the check).

## Stage 1: the lineage of the accepted theorems (Q15)

Each of Model 0.2's 24 theorems and M3's 22 is classed in
`ConcreteClaims.v`'s index as inherited (holds by import), re-proved
(restated over the concrete model), strengthened, or inapplicable (about
the fixed single-hart profile's closed objects, which the MVP does not
run; U-13):

| Source | Inherited | Re-proved | Strengthened | Inapplicable |
| --- | --- | --- | --- | --- |
| Model 0.2 (24) | 0 | 9 (`failed_validation_no_publication` → `gate_false_no_start`; `monitor_exclusion`, `derived_root_soundness`, `derived_rights_bounded`, `mapping_soundness` → `roots_from_instance`; `directional_channel_confinement` → `flow_is_declared_channel`; `saved_state_separation`, `canonical_state_immutable_after_sealing` → `single_writer_carried`; `terminal_fail_closed_behavior` → `control_ring_fails_closed` and `denial_iff_entry_below_ceiling`) | 0 | 15 (the validation, sealing, derivation, proposal, activation, ownership, resource, and single-hart switch theorems, and the bundle) |
| M3 (22) | 13 (the seven policy theorems by import; `binding_h0_control_excluded`, `h1_injective_total`, `h2_private_state`; `policy_instance2_results` and `instance3_results` recomputed in `ConcreteBridge.v`; the bundle) | 0 | 1 (`binding_h3_single_writer` → `single_writer_carried`, every word every step changes, the input path included) | 8 (Instance 1's projection of the fixed profile and its results) |

P9 (input routing) is `InputRing.v`'s T1 to T4 by import: stage 1's input
steps refine `InputRing.v`'s. The 26 theorems (`ring_no_overrun`,
`ring_take_published_only`, `ring_indices_monotone`, `control_ring_fails_closed`,
`input_ring_drops_under_room`, `ring_fifo_integrity`, `ring_type_set`,
`drain_round_robin`, `drain_in_order`, `concrete_step_within_footprint`,
`single_writer_carried`, `roots_from_instance`, `instance_page_numbering`,
`mgmt_grants_from_instance`, `barrier_publication_block`,
`flow_is_declared_channel`, `denial_iff_entry_below_ceiling`,
`denial_record_before_resume`, `mgmt_decided_by_control_hart`,
`mgmt_outcome_from_grants`, `mgmt_one_pending_per_domain`,
`mgmt_answered_once`, `parked_never_resumes`, `entry_after_gate`,
`gate_false_no_start`, and the bundle `stage1_claims`) are bundled in
`stage1_claim_set`; the gate prints `Beryllium MVP concrete model (stage
1): PASS theorems=26 assumptions_closed=26 citations=92
layout_sha256=c50da8ad3b06`. One stated premise stays an input:
`instance_page_numbering` assumes a scenario's pages are listed in
guest-physical order from the channel address (true of both scenarios'
data; U-16).

## The premises and the litmus tests (D-3, D-9)

| Premise | What it states (the plan's D-3) | Shape | Under herd7 7.58, RVWMO |
| --- | --- | --- | --- |
| L1 | the barrier: a domain hart that reads the published generation word reads every block word hart 0 wrote before its `fence w,w` (P1's premise) | message passing, `fence w,w` and `fence r,r` | Never (2 states, 0 positive) |
| L2 | ring publish: a reader that acquires the head and fences reads the records' bytes the writer posted before its `fence w,w` (P3, P4, P8) | message passing on a ring | Never (3 states) |
| L3 | ring release: a writer that reads the tail reads no record byte before the reader has read it, the reader's `fence r,w` preceding its tail store (P3, P4, P8) | load buffering with `fence r,w` | Never (2 states) |
| L4 | buffer reuse: a writer that finds room by reading the tail stores into the freed slot only after that read, by the control dependency on the room check (P3) | the tail load, the branches, the store on the allowed path | Never (2 states) |
| L5 | the input ring's drop: a writer that asks `room` and posts within it never overwrites (P3 (e), `input_ring_drops_under_room`) | as L3 and L4 on the input ring | Never (2 states) |

Each test's instructions mirror the compiled sequences of the exact
symbols at the target commit (`sequences.txt`: both toolchains' monitor
ELFs without debug sections by SHA-256, 55 symbols each by section,
address, size, bytes' SHA-256, and excerpt, checked against the
disassembly by the sequences suite, the first of `verify`); the ablated
tests (a fence removed) are `Sometimes`, so none is vacuous; herd7 7.58
lacks `bltu` and `bnez`, so `blt` and `bne` on the same registers stand
in (recorded). The premises are discharged for the compiled sequences
under the axiomatic model and for nothing else: the hardware's fences and
caches are exercised only as they behave (U-11).

## The qualification matrix (D-7 item 2; H41 stage 3)

Per arm and solver, the four cases (known-pass, known-fail,
vacuity-requires, vacuity-ensures, wrong-implementation), 60 s per goal:

| Arm | Solver | Qualified | What failed |
| --- | --- | --- | --- |
| WP | Alt-Ergo 2.4.3 | yes | — |
| WP | Z3 4.16.0 | **no** | known-fail proved, vacuity-ensures proved, wrong-implementation proved: Z3 answers `unsat` on WP's prelude with no goal (item 117) |
| WP | cvc5 1.3.4 | no | known-pass times out; vacuity-requires undetected |
| CBMC | `sat` (MiniSat 2.2.1) | yes | — |
| CBMC | Z3 | no | vacuity-ensures killed after 60 s |
| CBMC | cvc5 | yes | — |
| CN | Z3 | yes | — |
| CN | cvc5 | yes | — |
| litmus | herd7 | yes | — |

`BE_MVP_QUALIFY: PASS arms=9 qualified=6 not_run=0`. Q17: WP's Rocq
export is not qualified (why3 1.8.2 knows `coqtop` 8.16 to 8.20; the
image has `rocq` 9.3.0). Q8: the ACSL importer placed every annotation
Leaf A needed. The machdep is `gcc_x86_64` (RISC-V LP64 has unsigned
`char`; the leaf's `_Static_assert`s hold), recorded in each arm's
assumption inventory.

## The arms' records

Two runs are retained: the first, against the first freeze
(`mvp/results/20261103-verify/`, 36 files: every arm OPEN or FAILED on the
nine clauses, the evidence of the errata), and the re-run against
Revision 1 (`mvp/results/20261103-verify-r1/`, 28 files). Per arm the
re-run holds `transcription.txt` (the clauses to the annotations),
`goals.txt`, `rounds.txt`, `mutants.txt`, `vacuity.txt`, and
`assumptions.txt`; the ring adds `properties.txt`, `sequence.txt`,
`coverage.txt`, `wrap-sites.txt`, `summary.json`, and `defect-room.txt`
(the S-5 finding with its host reproducer: `CONFIRMED contradictions=4`).
The WP arm's vacuity is `not-ok` by its rule, and rightly: two code paths
are dead under the contract, the `SPVP` arm at `mvp-sbi.c:317` under E3
(the first run's finding) and the `map->size == 0` test under R1-2's
`requires map->size > 0` (six dead tests where the rule allows five); the
rule was not changed after the result. The CN arm's vacuity is `not-ok`
on the same `leaf_at` liveness limit. CBMC's vacuity is ok on both leaves
(every function's reach and contradiction checks pass; cover 6 of 6
goals). The ring's 20 index-advance wrap sites are intended under R1-9;
mutant m18 (`HEADER_TYPE=0`) is unobservable and m02 (`failed=2` against
the test's `== 1`) a harness finding, both as in the first run.

## H38 and H41, as resolved (D-12)

| Helium stage | Disposition | What M8 did |
| --- | --- | --- |
| 1 select a seam | adapted | Leaf A (the denial decision and its four helpers, 113 pure lines) carried the selection; Leaf B (the ring) admitted with the protocol as stage 1's obligation |
| 2 entry criteria | adopted | the exact source boundary by digest (`target-digests.txt`: 13 files) at the target commit `6fbcc3d1`; the re-proof rule |
| 3 qualify the tool | adopted | the matrix above: 6 of 9 pairs; two unsound or non-terminating pairs excluded before any leaf goal ran |
| 4 independent specification ownership | adapted | drafted without reading the C, frozen by hash, the human reviewer of record; fourteen errata found by the proofs and the arms, each recorded, none a code defect |
| 5 a mutation plan | adopted | 24 seeded mutants per leaf (seed `0x4d38`), each killed, unobservable, or a finding, per arm |
| 6 exact evidence | adopted | the digests, the records, the hashes of the specification's text at its commits |
| 7 a clean evaluator | practice | the verifier image, its closure and sources by SHA-256, `--network=none` |
| 8 clean-commit and human gates | practice | this packet |
| 9 exit criteria | adopted | the three outcomes; this one inconclusive, recorded as a valid outcome |

H38 is resolved as bounded checking per named claim (CBMC on the two
leaves, reported as such); H42's lessons stayed where they were.

## Departures from the plan's letter, recorded in the session

| Plan text | As done | Where |
| --- | --- | --- |
| Model lane 6,000; bridge lane 3,000 | errata 1 to 3: 12,000 and 12,000 (the harnesses and runners undershot by about four times); at `X` the model lane holds 8,544 (Rocq 7,450, tools and gates 1,094), the bridge lane 11,811, the tool-glue lane 1,473 (1,954 less the closure's 481 data lines), 9 of 10 pinned tools | the plan's decision record |
| Stop 5: Z3 and cvc5 the pair for WP | decision A: Alt-Ergo alone, a recorded arm that cannot meet item 7 | the plan's decision record |
| Stop 2: nine specification clauses | Revision 1 and a re-run (the human's `revision_1_rerun`); S-1 to S-4 recorded, not edited | `93a8d136` |
| Stop 2 again: the `room` row | erratum S-5, no Revision 2 (the human's `erratum_s5`) | the plan's decision record |
| D-7 item 7 for CBMC | the `sat` and cvc5 pair, since CBMC with Z3 did not terminate on the vacuity case | the qualification matrix |
| Q10: CN attempted, with fallback | attempted and run: the toolchain built offline from pinned sources; the arm OPEN on tool limits | M8-5, M8-6 |
| The specification pinned by file | pinned by the commit's blob, since an acceptance edit moves the file; the image hashes the host's export | `928b07bd`, `b2f40b1d` |
| `verify` in `check` | `verify` is its own gate (`./mvp/mvp verify`, 3 h 44 min); the sequences check is its first suite, not `check`'s | M8-4 |
| The gates at the merge of the re-run | the first attempt at `2e298c3a` passed `check` and stopped at `evaluate` for want of the OpenSBI firmware in the fresh clone (an environment fact, hard-linked in); the second failed `check` in the dry run's timing case `missed-s-retry` at a load average of 1.5 (item 93, whose fix M9's accepted line holds), and `evaluate` runs the same dry run; so the fix was cherry-picked, test files only (`fake-uboot.py`, `run-tool-dry-run.sh`; the case lists resolved without M9's `staged-sha256` case), the dry run passed once in the main checkout (`latest s 0.75 s`), and the gates ran again at `f1813841` | `f1813841`; `build/m8-gates/attempt-1/`, `attempt-2/` |

## The gates at `X` = `f181384192bd4a79df52ba7cdb5dfbed55ab3307`, from a standalone clean clone

The gates ran from a standalone clean clone at `X`
(`worktrees/beryllium-hypervisor/m8-gates`, `git status --porcelain`
empty; the guest, OpenSBI, U-Boot, verifier, and evaluator caches
hard-linked in from the main checkout), driven by a script outside the
tree (`build/m8-gates/run-gates.sh`, M9-6's retargeted), each gate's output
logged between `start_utc=` and `end_utc=` lines under
`build/m8-gates/final/` in the clone; two earlier attempts at `2e298c3a`
are kept beside it (`attempt-1/`: `check` PASS, `evaluate` stopped for
want of the OpenSBI firmware in the fresh clone; `attempt-2/`: `check`
failed in the dry run's `missed-s-retry` timing case, item 93, at a load
average of 1.5). The host's load average was 0.9 to 3.5 during the run.
Every line below is from those logs.

| Gate | Command | Result | When (UTC, 2026-11-04) |
| --- | --- | --- | --- |
| The tool lock | `./mvp/mvp tool-lock check` | PASS (`roles=32 host_only_skipped=0 closure=259`) | 01:50:02 |
| Every off-board check | `./mvp/mvp check` | `BE_MVP_CHECK: PASS` in 10 min 25 s: the port; the ten host tests; the image checker and its mutations on every image; the QEMU suite (`BE_MVP_QEMU: PASS runs=62 attempts=74 refused=12`) and the sessions; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=164 failed=0`, `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=399 rejected=399`; the dry run `BE_MVP_RUN_TOOL_DRY_RUN: PASS` with its autoboot check (24 boards inside their 3 s windows, the latest `s` 0.78 s after `Autoboot in`); the licences, the platform-record and platform-probe checks; `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=55 boundary=16`; the evidence bundle `BE_MVP_EVIDENCE: PASS development … files=354 images=315 qemu_attempts=74 session_attempts=8` | 01:50:02 to 02:00:27 |
| The evaluator | `./mvp/mvp evaluate` | `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; `check` passing inside the image from the clean source mount (the dry run's autoboot check there: the latest `s` 0.81 s); `BE_MVP_IMAGE_IDENTITY: PASS images=315 same=315 differing=0` | 02:00:27 to 02:11:54 |
| The claim ledger | `./mvp/mvp claim-ledger check` | `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=55 boundary=16` (the phrasing check `review_items=3`) | 02:11:55 |
| The model's gate | `./be model-check` | PASS: `Beryllium Architecture Model 0.2 proofs: PASS`; `Beryllium security model v1 policy and hart binding proofs: PASS instances=generated`; `Beryllium MVP input ring proofs: PASS theorems=4 assumptions_closed=4`; **`Beryllium MVP concrete model (stage 1): PASS theorems=26 assumptions_closed=26 citations=92 layout_sha256=c50da8ad3b06`**; `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`; the escape-hatch patterns, the source policy, the reports; the whole gate 131 s | 02:11:55 to 02:14:06 |
| The model's evaluator | `./be evaluate` | `BE_EVALUATION: Model 0.2 rootless evidence PASS` | 02:14:06 to 02:16:06 |
| The verifier | `./mvp/mvp verify` | `BE_MVP_VERIFY: PASS image=localhost/beryllium-mvp-verifier:ce7ca11cb755-b71721530f48-36eaf6d2362b`, `wall_seconds=13480` (3 h 44 min 40 s): the specification `93a8d136 … sha256=aeb75682…`; `BE_MVP_LITMUS_SEQUENCES: PASS elfs=2 symbols=55 lines=206`; `BE_MVP_TARGET_DIGESTS: PASS files=13`; `BE_MVP_TOKEN_EQUAL: PASS tokens=686`; `BE_MVP_QUALIFY: PASS arms=9 qualified=6 not_run=0`; `BE_MVP_LITMUS: PASS premises=5 never=5 sometimes=0 not_run=0`; `BE_MVP_WP_ARM: OPEN goals=134 proved=130 rounds=1 solvers=alt-ergo mutants=24 killed=18 unobservable=0 contract-findings=0 vacuity=not-ok pair=not-formed`; `BE_MVP_CN_ARM: OPEN goals=55 proved=5 rounds=0 solvers=z3,cvc5 mutants=24 killed=1 unobservable=1 contract-findings=0 vacuity=not-ok pair=formed`; `BE_MVP_CBMC_LEAF_A: SUCCESSFUL properties=336 failed=0 solvers=sat,cvc5 mutants=24 killed=22 unobservable=1 contract-findings=1 vacuity=ok unwind=4`; `BE_MVP_CBMC_RING: OPEN functions=14 capacities=512,4096 properties=14931 checked=13547 open=1384 solvers=sat,cvc5 mutants=24 killed=22 unobservable=1 harness-findings=1 coverage=ok vacuity=ok`: every verdict and count the re-run's | 02:16:06 to 06:00:46 |

`verify`'s suite verdicts at `X` equal the re-run's at `6555266b` line for
line (the arms are deterministic under their budgets; the WP goals' and
the ring parts' timings vary, their verdicts did not).

## Soft limits and stops in M8

| Limit or stop | Outcome |
| --- | --- |
| Model lane (12,000 after erratum 1) | 8,544 at `X` |
| Bridge and contracts lane (12,000 after errata 2 and 3) | 11,811 at `X` |
| Tool-glue lane (2,500; at most 10 pinned tools) | 1,473; 9 tools |
| Proof time (600 s) | the whole model gate 131 s at `X` (`make -C model proof` within it; stage 1 alone about 59 s) |
| Stop 1 (monitor source; accepted model files; axioms) | not reached: no monitor byte; the accepted modules unchanged; the one `model/Makefile` line is D-1's enumerated addition; no axiom |
| Stop 2 (a defect found) | fired twice, both times specification errata and no code defect; decided Revision 1 and S-5 |
| Stop 3 (the two first obligations) | not reached: `concrete_step_within_footprint` and the instances' recomputed decisions hold |
| Stop 4 (a property that cannot be stated without the C) | not reached |
| Stop 5 (the solver pair) | fired for WP; decision A |
| Stop 6 (the soft limits) | fired three times; errata 1 to 3 |
| Stops 7 to 12 | not reached; no board, no push, no claim change |

## Open items

Opened or closed by M8 in `mvp/README.md`:

| Item | State | What |
| --- | --- | --- |
| 101 | closed (M8-7) | C-06's non-claim re-read at the target commit; stage 1's 92 readings cite symbols and are gate-checked; Binding.v's line citations are M3's history |
| 103 | closed (M8-2) | the two planning sentences on a VST route corrected |
| 116 | M9's (closed there) | — |
| 117 | open | WP with Z3 4.16.0 through why3 1.8.2 unsound on WP's prelude; a report upstream is the human's choice |
| 118 | open | a timed-out cvc5 leaves about 1 GB of temporary files under `build/mvp/verify/tmp` until the next run |
| 124 | open | the ledger's IDs are numbered per lane (M8's C-51 to C-55, U-16; M9's C-51 to C-53, U-16, U-17); the second line to integrate into the development branch renumbers its rows, and the documents that cite them keep the numbers as assigned at acceptance |
| 125 | open | the CN arm's three tool limits (a compound literal's resource never released; `leaf_at`'s pointer liveness needing a `focus` a braceless loop cannot hold; `&`, `\|`, `^` uninterpreted) and WP's four Alt-Ergo timeouts are candidates for upstream reports and for M10's re-proof round; the human's choice |

## Claim boundary

What this record supports: in the concrete operational model of the
protocol (stage 1), under sequentially consistent interleaving and with
the five ordering premises discharged by litmus tests for the compiled
sequences, the 26 stated properties hold with every assumption closed
(the ledger's C-51 to C-55); the specification's fourteen errata are
recorded and none is a code defect; CBMC's bounded model check of the
denial decision at unwind 4 found no failing property against Revision 1,
and its bounded check of the ring found one specification erratum and no
code defect within its bound.

What it does not support: a C-level contract proof of any monitor
function (none was obtained; the claim's sentence on the implementation
stands unnarrowed); any refinement between the model and the C; any
statement about memory ordering beyond the five premises under the
axiomatic model, or about the hardware's fences and caches; any result
about the firmware, the trap assembly, the G-stage walk, the measurement
log (M9's lane; M10 re-reads the correspondence), or the sealed state's
protection inside HS; and nothing on the board. The stage-1 theorems are
proofs about an abstract model and are never to be described as a
verification of Beryllium's implementation.
