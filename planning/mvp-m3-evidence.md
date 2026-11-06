<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M3 evidence record

This record holds the evidence of M3, "The policy layer and the hart
binding in the model", as it stands at exact commit `d35813c7` on branch
`beryllium/mvp-m3`, made under the accepted [M3 plan](mvp-m3-plan.md)
(`c2c249f4`, accepted 2026-10-28) and the accepted
[security model v1 Revision 1](security-model-v1.md#revision-1-2026-10-28-the-hart-binding-and-the-third-instance)
(`019cca64`, accepted 2026-10-28). It records what was run, when, on
which commit, and what it printed; it makes no claim beyond those
lines.
The model's own evidence bundle, `build/model/evidence/`, is generated,
not committed; its identifying hashes are below.

## What M3 adds, by file

All under `model/`. The six accepted Rocq modules, `src/manifest.c`,
`src/state.c`, `src/fixtures.c`, `tests/unit/test_main.c`,
`tools/model-run.c`, `tools/model-report.c`, `tests/check-source-policy.sh`,
and `tests/run-rootless.sh` are byte-identical to the accepted Model 0.2
(`git diff f8f89758 d35813c7 -- <those paths>` is empty).

| File | Lines | What it holds |
| --- | --- | --- |
| `proof/Policy.v` (new) | 2,002 | The raw-term vocabulary; the A1 validator (`validate`, `a1_findings`); `decide`; A2 to A8; `verdicts`; the adapter `view_of_canonical`, the projection term `projection_m02`, two bridge lemmas; `seal_with_policy` with the combined identity; T1 to T5 |
| `proof/Binding.v` (new) | 787 | The MVP's static binding (control hart 0; G0 on hart 1, G1 on hart 2), the object classes of Revision 1's I15 and I16 with their extents from `mvp-layout.h`, the barrier phases, the transition vocabulary with total write footprints and source lines, H0 to H3 proved for `mvp_binding` |
| `proof/PolicyClaims.v` (new) | 220 | `security_model_v1_claim_set` (T1 to T5, A7's vacuity, the projection's flow equality, H0 to H3, the computed results of `instance1`, `instance2`, `instance3`, `projection_m02`, and `instance1_m02 = projection_m02`) and `Theorem security_model_v1_claims` |
| `proof/PolicyAssumptions.v` (new) | 35 | `Print Assumptions` for the 22 new theorems and the record |
| `proof/InstancesSample.v` (new) | 301 | A development stand-in for the generated `Instances.v`, compiled only when the generated file is absent; the gate's `Instances` is the generated one (`instances-source.txt` records which) |
| `include/be/policy.h`, `include/be/policy_fixtures.h` (new) | 715, 96 | The bounded raw and validated structures (bounds: types 16, classes 8, permissions 16, rules 24, subjects 8, objects 24, labels 40, needs 24, grants 24, channels 4, ownerships 16, bindings 8, harts 8, findings 16), finding codes, the API; the generated data's API |
| `src/policy.c` (new) | 1,500 | A1, `be_policy_decide`, A2 to A8, `be_policy_verdicts`, the FNV-1a identities, `be_view_of_canonical`, `be_seal_with_policy` and `be_seal_view_with_policy`, the binding check; no libc |
| `tests/unit/policy_test.c` (new) | 631 | 169 pinned checks, GCC = Clang |
| `tools/policy-run.c`, `tools/policy-report.c` (new) | 129, 377 | The verdict lines; the deterministic report |
| `tools/gen-policy-fixtures.mjs` (new) | 1,070 | The build-time generator: the three instances, the projection, and the mutation set as C data, Rocq terms, and MVP-checker files; deterministic |
| `tests/differential.sh` (new) | 307 | The three-way driver and the generated oracle |
| `fixtures/instance-1/{policy.te,instance.json}`, `fixtures/mutations.json` (new) | 28, 77, 101 | Instance 1 verbatim from security model v1 Part 2 with its labeling, need sets, and manifest; the seeded mutation set (seed 73, count 91) |
| `Makefile`, `tests/run-proofs.sh`, `tests/check-reports.mjs`, `tests/generate-evidence.sh`, `tests/check-tools.sh`, `toolchain.conf`, `Containerfile` (accepted, edited additively) | | The seven enumerated edits of plan Q5 (the generator, test, run, report, proof, and differential targets; the new modules and the 22-report audit; the report's checks; the evidence's new lines and hashes; the lock's versions and `python3`) |

New Rocq: 3,044 lines (the sample excluded) against the soft limit
re-set to 6,000 (plan erratum 11); new restricted C: 3,448 lines against
6,000 (erratum 9); generator and driver: 1,377 lines against about 1,500.

## The obligations, as stated

The new record `security_model_v1_claim_set` (`proof/PolicyClaims.v`)
holds, each proved with no axiom, `Admitted`, or other escape hatch (the
runner's grep) and each `Closed under the global context`:

| Field | Statement (summary; the module has the exact form) |
| --- | --- |
| `claim_decide_total` (T1, I10) | `decide` agrees with `policy_allows` in both directions, depends only on the rules, and is `false` for every query when there is no rule |
| `claim_a8_sound` (T2, I11) | for every validated instance with `a8 = true`, every permission of every grant is allowed by `decide`, and every channel's writer has `send` and reader `receive` |
| `claim_flow_confinement` (T3a) | under `a8 = true`, the view's flow relation is contained in the policy's |
| `claim_a6_closure_equality` (T3b) | under `a6 = true`, the transitive closure of the policy's flow relation equals that of the declared-channel relation |
| `claim_projection_flows_equal` | for the projection, the view's flows, the policy's flows, and the declared channels are equal (by computation) |
| `claim_projection_mappings_allowed` (T4) | for `derive_enforcement canonical_configuration`, every derived mapping's presence (`map`) and each leaf right it allows is allowed by `decide` under the projection; uses the accepted `claim_derived_root_soundness` and `claim_derived_rights_bounded` as projections of `architecture_model_0_2_claims`, not re-proved |
| `claim_seal_requires_conformance` (T5) | `seal_with_policy canonical policy labeling needs = Some sealed` implies the labeling matches the canonical state, A1 (validation) and A2 to A6 and A8 pass, and the record's four identities are the stated functions |
| `claim_a7_vacuous` | A7 passes for every delegation-free validated instance |
| `claim_control_excluded` (H0) | no domain's hart is the control hart |
| `claim_binding_injective_total` (H1; I13, I14) | `hart_of` is injective, and each domain's hart is a started non-control hart |
| `claim_hart_private_state` (H2; I15) | every private object's extent is disjoint from every other hart's private objects, from every domain's window and the shared pages, and from everything a root can map; and in any view passing A3 and A8 no domain holds a non-`domain` permission on monitor memory |
| `claim_single_writer` (H3; I16) | before the barrier only the control hart writes; after it nothing writes published data, a ring's records and head are written only by its writer and its tail only by its reader, and a transition writes only its own hart's private objects |
| `claim_instance1_results`, `_instance2_`, `_instance3_` | `verdicts` all pass; A5 reports the shared pages the security model names (Instance 1: `shared_mp_t`; Instance 2: `shared_wr_t`; Instance 3: `req_t` and `resp_t`); delegation-free (A7 vacuous) |
| `claim_projection_results`, `claim_generated_projection` | the projection's results as stated and its sealing with `canonical_configuration` succeeds; the generated `instance1_m02` equals the adapter-side `projection_m02` |

What T4 covers: the projection's four non-executable mappings (each
domain's private read-write, the producer's shared read-write, the
consumer's shared read-only). What it does not: Instance 1's guest-code
resources 12 and 13 and their `execute`, which Model 0.2 does not
contain (Revision 1, R1.5).

The transition vocabulary of `Binding.v` (hart 0 the control hart, `d`
a domain's hart; Prepare and Publish before the barrier, the rest
after): Prepare (0), Publish (0), Start (0), Ready (d), Entered (d),
ExitRecord (d), Drain (0), Ping, DecideDeliver, Answer, Acknowledge (0),
Pong, Request, Pause, Terminate (d), Park (d), Shutdown, FailRecord (d),
Wake, RunEnd (0); each with its write footprint and the source lines in
`mvp-runtime.c`, `mvp-hartmain.c`, `mvp-sbi.c` from which it was read.
Three differences between Revision 1's prose and the sources, none a
false obligation, are recorded as errata in Revision 1's
[acceptance record](security-model-v1-revision-1-review-summary.md).

## The differential check

`tests/differential.sh` compares, verdict by verdict, three
computations of A1 to A8 on the same terms: the Rocq oracle (a generated
`build/model/differential/Oracle.v` that evaluates `Policy.v`'s
`verdicts` by `vm_compute` for every instance and mutation against the
checked modules; `rocq compile`, 0.4 s), the model's C checker
(`policy-run`, the GCC and Clang builds required to agree), and the
MVP's offline checker (`mvp/tools/policy-check.py` on the generated
`policy.te`/`scenario.json` of every MVP-shaped instance and mutation,
with the MVP Makefile's arguments). Instance 1 and its projection have no
MVP-checker form (plan erratum 10), so their comparison is two-way. The
mutation set (`fixtures/mutations.json`, seed 73): 91 single-defect
mutations, Instance 1 20, te-poc 34, anchor 37; 42 drawn by the
generator's mutator and 49 explicit edits; each with the analyses that
must fail it, written from Part 3's definitions before any checker ran on
the set, and the claim it tests (S1 H39); 29 fail at A1 alone, 62
exercise A2 to A8. Result, identical on the host and in the evaluator:

```text
BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241
```

Every observed failing set equals the expected one; no disagreement
between any two of the three computations. The driver fails on each of
six injected faults (a wrong expected set, a tampered MVP input, an MVP
refusal, the stand-in `Instances.v`, tampered and truncated oracle
output, a wrong count). Agreement is the claim; neither host checker is
thereby the Rocq function (`claim-status.txt`:
`differential=…-not-a-refinement`).

The MVP inputs the check reads, hashed into the evidence
(`mvp-inputs.sha256`): `mvp/tools/policy-check.py` `709a5ba4…`,
`mvp/src/mvp-layout.h` `7ba1ac47…`, `mvp/scenarios/te-poc/policy.te`
`4a1fac2b…`, `scenario.json` `4fe51645…`, `mvp/scenarios/anchor/policy.te`
`bfecfa92…`, `scenario.json` `533183f4…`.

## Identities (reporting and equivalence only)

The Rocq and C identities are the same 64-bit FNV-1a over the same byte
layout. Policy identities: te-poc `4a1fac2b…` and anchor `bfecfa92…` are
the SHA-256 of the files, equal to the MVP's; the combined identities the
C checker prints are instance1 `0x63c22d4da9dcedfa`, instance2
`0x14bf7d9df5ad5475`, instance3 `0x5fdcbf76ee262f71`, instance1_m02
`0x2145ed531d6de1c8`; sealing the fixed-TE fixture through the adapter
gives canonical `0x2a4c5a62bc446015` (the accepted model's), policy
`0x7e582038aaacb063`, labeling `0x16587c280e677382`, combined
`0x97cc83217469369d`. The Rocq `seal_with_policy` uses the accepted
model's abstract canonical identity, so its combined value differs from
the C's; only determinism is claimed for it.

## The gates at `d35813c7`, from a clean tree on `l1`

Workstation `l1` (x86_64, Fedora 44), 2026-10-28, the lock's tools (GNU
Make 4.4.1, GCC 16.2.1, Clang 22.1.8, Node.js v22.23.1, Python 3.14.8,
Rocq 9.3.0; ccache bypassed), each from a clean tree at exact commit
`d35813c7`:

| Command | When (UTC) | Result |
| --- | --- | --- |
| `make -C model clean check` (on the content of `d35813c7` as its working tree, 44 s before the commit; the clean-tree runs follow) | 22:17-22:18 (54.0 s) | `tools: PASS`; `source policy: PASS`; the accepted `unit tests: PASS` twice (11 tests); `policy fixtures: PASS instances=3 projection=1 mutations=91`; `policy layer unit tests: PASS checks=169 instances=4 mutations=91` (GCC = Clang); four `BE_MODEL_RESULT: PASS`; `BE_POLICY_RUN: PASS instances=4 mutations=91`; `policy layer report: PASS`; `reports: PASS`; `security model v1 policy and hart binding proofs: PASS instances=generated`; `proofs: PASS` (24 + 22 closed assumption reports; the proof 45.7 s); `BE_MODEL_DIFFERENTIAL: PASS … comparisons=241`; `evidence: PASS` |
| `./be model-check` | 22:19:14-22:20:13 | The same lines through the root wrapper, with the documentation source gate (`Documentation source gate isolation: PASS … adversarial_cases=34`) |
| `./be evaluate` | 22:20:27-22:21:27 | `Model 0.2 evaluator image build: PASS` (the image reused from the cache; its six tools equal the host's); inside the container every line above, `BE_MODEL_DIFFERENTIAL: PASS … comparisons=241`, `Model 0.2 rootless checks: PASS`, `Beryllium Architecture Model 0.2 rootless validation: PASS`; `BE_EVALUATION: Model 0.2 rootless evidence PASS` |

The accepted outputs are unchanged under the new tools and beside the
new work: the accepted reports `source-a.json` `1614de6a…` and
`source-b.json` `93389936…` byte-identical to the accepted evidence, the
identity `0x2a4c5a62bc446015`, the 24 accepted assumption reports closed
(M3-2's baseline, `12e6fb06` and `0e05d338`).

The evidence bundle (`build/model/evidence/`, the host's run):
`source.sha256` (77 files) SHA-256 `b259ae51…`, identical to the
evaluator's; `differential.txt` `57a5267e…`, identical to the evaluator's;
`artifacts.sha256` `5101b82e…` on the host and `732e6a6e…` in the
evaluator, the difference being the `/work` mount path the `.vo` files
and debug builds embed (open item below); `tool-versions.txt` the six
tools above; `claim-status.txt` as the accepted one with
`proof=rocq-9.3-23-bounded-obligations` and the `differential=` line.

## Soft limits and stops in M3

| Event | Plan condition | Outcome |
| --- | --- | --- |
| The rootless evaluator installed Node.js 22.23.1 where the lock had v22.22.2 (M3-2) | stop 6 | Returned; remedy A: the host and the lock moved to 22.23.1 (`0e05d338`; erratum 8) |
| New C 3,447 lines against about 2,000 (M3-4) | stop 5 | Returned; the limit re-set to 6,000 (erratum 9) |
| Instance 1 has no MVP-checker form (M3-4, M3-5) | pass criterion 4 | Returned; two-way for Instance 1 and its projection (erratum 10) |
| New Rocq 3,044 lines against about 3,000 (M3-3) | stop 5 | Returned; the limit re-set to 6,000 (erratum 11) |

No stop condition 2, 3, 4, 7, 8, 9, or 10 applied: no accepted module
was edited, the three computations never disagreed, no obligation was
false for an instance, no eighth accepted file was touched, no
concurrency was modeled, and no accepted byte or retained record changed.

## Open items

1. The Model 0.2 rootless evaluator's `:Z` mount relabels the whole
   repository for SELinux, the `build/` tree included (host processes
   unaffected; `restorecon -R` restores); accepted behaviour, observed in
   M3-2 and M3-6.
2. Its in-container `make clean` deletes the host's `build/model`, which
   the container's own check then regenerates with `/work` paths;
   accepted behaviour; the host's bundle was copied aside before each
   evaluator run.
3. The evaluator's `.vo` files and C binaries embed the `/work` mount
   path, so `artifacts.sha256` differs from the host's while the reports,
   the closed-assumption logs, `source.sha256`, and `differential.txt` are
   identical; the accepted rootless claim is the checks' PASS, not byte
   identity (the MVP evaluator mounts at the host path and achieves
   identity; a later plan may align the model's).
4. The model's lock does not pin `rocq-stdlib` (9.2.0 on the host and in
   the evaluator).
5. `tool-versions.txt` gained Python's version in M3-5; the accepted
   `generate-evidence.sh` listed five tools.
6. Three Revision 1 prose errata (recorded in its acceptance record).

## Claim boundary

This record supports saying, about the abstract model: the validated
policy semantics is total and default-deny (T1); a validated view that
passes A8 grants no right the policy denies (T2), and for Model 0.2's
projection of the fixed two-domain profile every derived mapping's
presence and leaf right is policy-allowed (T4); A8 confines the view's
flows within the policy's and A6 equates the closures of the policy's
flows and the declared channels (T3); a policy-sealed state exists only
for conforming inputs and carries one combined identity (T5); the MVP's
static binding is injective and total into the non-control harts, each
hart's private state is disjoint and unmapped, and over the enumerated
vocabulary only the control hart writes before the barrier and each
shared word has its one writer after it (H0 to H3); the three instances'
analyses compute to the security model's stated results; and the Rocq
oracle, the model's C checker, and the MVP's offline checker agree on
them and on 91 mutations (three-way for 73, two-way for 22).

It does not support saying: that any C code is proved (the checkers are
tested and compared, not refined); that the MVP monitor satisfies I10 to
I16 (the barrier, the rings' implementation, the IPI protocol, and
memory ordering are unmodeled; the footprints are the plan's reading of
the sources); that Beryllium is formally verified; any hardware result
(none run; the K3 untouched); or any dynamic case (Part 6; A7 beyond
its vacuity and the delegating-permission refusal).
