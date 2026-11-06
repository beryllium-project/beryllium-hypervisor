<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M3 result review and acceptance record

This packet presents the result of M3, the fourth milestone of the
accepted [MVP plan](mvp-plan.md): security model v1's policy layer in
the abstract model and its executable form, the static hart binding of
the MVP stated and proved in the same model, and differential checking
of three independent computations of the analyses. It was implemented
under the accepted [M3 plan](mvp-m3-plan.md), whose
[decision record](mvp-m3-plan.md#decision-record) holds its
authorization, after the accepted
[security model v1 Revision 1](security-model-v1.md#revision-1-2026-10-28-the-hart-binding-and-the-third-instance)
(work package M3-1, its own exact commit). The plan was not revised;
eleven errata and four stops, each returned to and decided by the
responsible human, are recorded in its acceptance record and summarized
in section 5. It also records the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`b0a0f352d7969a8f8cf28cf0d25b89fc372e70f2` (parent
`d35813c7b29dcf3ceebb0d463a724989df4efb96`, tree `f6f9c043`) as the M3
result on 2026-10-28. The instruction, given in reply to this packet's
request to accept, revise, or defer that exact commit, was `6000 per
lane, so 12,000 combined soft limit. accept b0a0f352`. The abbreviation
was checked to resolve uniquely to that commit
(`git rev-parse --disambiguate=b0a0f352`).

- **Scope:** acceptance covers exactly that commit and the claim boundary
  in section 3. Sections 2 to 8 are the packet as presented, apart from a
  note above the section 8 checklist and a closing note to section 5's
  open-judgment paragraph. Section 1's status rows and the closing lines
  of section 9 now show the outcome. The decision itself is recorded only
  here.
- **Decision support:** packet commit `374b9959` and this
  acceptance-record follow-up are decision support, not implementation.
- **The soft limits, clarified with the acceptance:** the responsible
  human's question of the same day, whether the work exceeded "the 6000
  rocq+c limits", was answered with the measured counts (Rocq 3,044; C
  3,448; together 6,492), and the instruction states the reading: the
  re-set limits of errata 9 and 11 are **6,000 per lane**, so the
  combined Rocq-and-C soft limit is **12,000 lines**, against which the
  result measures 6,492. No limit is exceeded; no stop applies. The
  clarification is recorded as erratum 12 in the plan's
  [acceptance record](mvp-m3-plan-review-summary.md#decision-record);
  the accepted plan's text at `c2c249f4` is not edited.
- **No plan revision:** the four stops (stop 6 for the evaluator's
  Node.js, stop 5 twice for the C and Rocq soft limits, pass criterion 4
  for Instance 1) were each returned to and decided by the responsible
  human and are recorded as errata 8 to 11; the plan's text is unchanged
  and its status record is updated to match.
- **Revision 1 errata, text unchanged:** the three prose errata M3-3
  found against the sources (the harts start after the publication; the
  ring views are private; the roots are published data) stay in
  Revision 1's acceptance record; `Binding.v` classifies as the sources
  show.
- **Successor:** acceptance itself starts no successor. Each of these
  still needs its own decision: M4 (the release candidate) and its
  bounded plan; any merge of `beryllium/mvp-m3` into the development
  branch and any push; a security model v1 change beyond the accepted
  Revision 1; any change to the accepted Model 0.2 modules; root
  `Makefile`/`be`/`scripts/check-be.sh` integration;
  development-kernel/BSP selection.
- **Push and fast-forward (2026-10-28, after the acceptance):** the
  instructions `push all work` and `then proceed with (1) and (2)`
  directed pushing `beryllium/mvp-m3` (through the commit that records
  this) and `beryllium/mvp-m3-plan` (`97be918d`) to the private
  `origin`, fast-forwarding the development branch
  `beryllium/single-hart-runtime-r0` from `50b77c00` to that same
  commit and pushing it, and proposing the M4 plan on a new branch
  from that tip. The acceptance itself did none of these; each was
  separately directed.
- **Evidence status:** the evidence is a proof about the abstract model,
  unit tests, deterministic reports, and differential agreement among
  three computations, on the host and in the pinned rootless evaluator.
  Acceptance adds no C refinement, no claim that the MVP monitor
  satisfies I10 to I16, no formal verification of Beryllium, no
  emulation or hardware result, and nothing about the dynamic case. It
  does not tag, publish, or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `b0a0f352d7969a8f8cf28cf0d25b89fc372e70f2` (parent `d35813c7`), branch `beryllium/mvp-m3`. Comparison base: the M3 plan's acceptance record `97be918d`, over the accepted plan `c2c249f4` on the development branch's tip `50b77c00`. Two commits form the result: `d35813c7` holds the whole `model/` work (M3-2 to M3-5) and the gates ran on it from a clean tree; `b0a0f352` adds the [evidence record](mvp-m3-evidence.md) made against it. |
| Current status | Implemented, proved, tested, and run in the rootless evaluator; no board work (none planned). At exact commit `d35813c7`, from a clean tree on `l1`, `./be model-check` and `./be evaluate` pass: the accepted Model 0.2 gate unchanged under the refreshed lock (GCC 16.2.1, Clang 22.1.8, Node.js 22.23.1, Python 3.14.8, Rocq 9.3.0), the new record `security_model_v1_claim_set` with its fourteen fields proved and 22 assumption reports closed beside the accepted 24, the policy layer's 169 pinned unit checks GCC = Clang, the three instances and the projection all passing A1 to A8 as the security model states, and `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241` on the host and in the evaluator. Responsible-human accepted on 2026-10-28 (instruction `6000 per lane, so 12,000 combined soft limit. accept b0a0f352`). |
| Decision requested | Accept exact commit `b0a0f352` as the M3 result; or request revisions; or defer. No plan revision is bundled: the four stops were resolved by the responsible human's decisions recorded as errata 8 to 11. Recorded outcome: accepted, with the soft limits clarified as 6,000 per lane (erratum 12). |
| Successor status | As presented and after the decision: not started and not authorized: M4 (the release candidate), any merge of `beryllium/mvp-m3` into the development branch, any push, a security model v1 change beyond the accepted Revision 1, any change to the accepted Model 0.2 modules, root `Makefile`/`be`/`scripts/check-be.sh` integration, and development-kernel/BSP selection. |
| Publication status | Private repository. As presented, `beryllium/mvp-m3` and `beryllium/mvp-m3-plan` were local and unpushed, as was this packet; the acceptance changes none of that, and any push or merge needs its own instruction. The development branch `beryllium/single-hart-runtime-r0` is at `50b77c00` locally and on the private `origin`. No tag, publication, or release. |

As presented: please review exact commit `b0a0f352` and accept it,
request revisions, or defer. Outcome: accepted; see the
[decision record](#decision-record).

## 2. Deliverables

M3 was authorized by the acceptance of exact plan commit `c2c249f4` on
2026-10-28 (instruction `accept c2c249f4`, Q1 to Q12 at their defaults)
as work package M3-1 on branch `beryllium/mvp-m3` from the acceptance
record `97be918d`, and M3-2 to M3-6 after Revision 1's acceptance at
`019cca64` the same day (`accept 019cca64`). Eighteen commits follow
`97be918d` to `b0a0f352`: eight under `model/`, nine under `planning/`
(Revision 1, its packet and acceptance record, the stop and errata
records, the evidence record), and the instructions' status paragraph.
Nothing under `mvp/` changed; no accepted R0-R7 or B0-B7 byte, retained
R8 input, M0, M1, or M2 record, or root file was touched (`git diff
--stat 97be918d b0a0f352 -- . ':!model' ':!planning'` lists only
`.github/copilot-instructions.md`). Under `model/`, sixteen files are
new and exactly the seven accepted files the plan enumerates (Q5) are
modified, each additively; the six accepted Rocq modules and the
accepted C, tools, tests, and scripts outside that list are
byte-identical to the accepted Model 0.2 at `f8f89758`.

| Deliverable | Paths | Purpose | Trust or privilege boundary | Review question |
| --- | --- | --- | --- | --- |
| Revision 1 of security model v1 (M3-1; accepted `019cca64`) | `planning/security-model-v1.md`, the appended section | The `hart` class; I13 to I16 per word and per phase; the A8 interpretation (structural bindings outside A8); Instance 3; Part 7's rows; the projection erratum | Specification; accepted separately, with three prose errata recorded afterwards | Already decided; the errata are in its [acceptance record](security-model-v1-revision-1-review-summary.md) |
| The lock and the build lists (M3-2; `12e6fb06`, `0e05d338`) | `model/toolchain.conf`, `model/tests/check-tools.sh`, `model/tests/generate-evidence.sh`, `model/Containerfile` | The accepted gate re-run under the host's tools with identical results, then the lock moved to GCC 16.2.1, Rocq 9.3.0, Node.js 22.23.1 (stop 6, remedy A), `python3` 3.14.8 as a lock role | The lock pins what the gate ran with; the evaluator's six tools equal the host's | Were the accepted outputs identical under the new tools before the lock moved (M3-2's commit messages record them), and is the Node.js move acceptable as erratum 8? |
| The Rocq policy layer and binding (M3-3; `dadc6f63`, `cef9fad5`) | `model/proof/Policy.v` (2,002 lines), `Binding.v` (787), `PolicyClaims.v` (220), `PolicyAssumptions.v` (35), `InstancesSample.v` (301, a development stand-in), `model/tests/run-proofs.sh` (additive) | The raw-term vocabulary and the A1 validator; `decide`; A2 to A8 and `verdicts`; T1 to T5 (the adapter `view_of_canonical`, `projection_m02`, two bridge lemmas, `seal_with_policy` with the combined identity); the MVP binding with the object classes, phases, and transition vocabulary with footprints; H0 to H3; the record and its proof; the assumption audit | Proof about the abstract model; T4 uses the accepted `claim_derived_root_soundness` and `claim_derived_rights_bounded` as projections of `architecture_model_0_2_claims`, not re-proved; no escape hatch (the runner's grep); every report closed | Do T1 to T5 and H0 to H3 state what the plan and Revision 1 say (section 3 and the [evidence record](mvp-m3-evidence.md)'s table), and are the transition footprints faithful to the MVP sources they cite? |
| The executable model and host checker (M3-4; `83e850d0`, `6055b55a`, `6cfbc9ff`) | `model/include/be/policy.h`, `policy_fixtures.h`, `model/src/policy.c`, `model/tests/unit/policy_test.c`, `model/tools/policy-run.c`, `policy-report.c`, `model/tools/gen-policy-fixtures.mjs`, `model/fixtures/instance-1/`, `model/Makefile`, `model/tests/check-reports.mjs` (additive) | Restricted C with no libc: A1, `decide`, A2 to A8, `verdicts`, the FNV-1a identities, the adapter, `be_seal_with_policy` (A1 to A6 and A8 before sealing; one combined identity), the binding check; the build-time generator (no runtime parser) writing C data, Rocq terms, and MVP-checker files for the three instances, the projection, and the mutations; 169 pinned checks GCC = Clang | Host-only; the model's binaries read no file; the generator's output byte-identical across runs; the accepted C untouched | Does `be_seal_with_policy` refuse every A1-A6/A8-failing input the test constructs, and does the adapter's view of the fixed-TE fixture equal the generated projection? |
| Differential checking (M3-5; `d35813c7`) | `model/tests/differential.sh`, `model/fixtures/mutations.json` (seed 73, 91 mutations), `model/Makefile`, `model/tests/generate-evidence.sh` (additive) | The Rocq oracle (`vm_compute` of `verdicts` on every term), the C checker (both toolchains), and the MVP's `policy-check.py` compared verdict by verdict; each mutation's observed failing set against the expected set written from Part 3; six injected faults each fail the driver | Test-only; the MVP checker runs read-only from the same commit; its inputs hashed into the evidence; Instance 1 and its projection two-way (erratum 10) | Are the expected failing sets right by Part 3's definitions, and is the three-way agreement on 73 and two-way on 22 the plan's pass criterion 4 as the erratum reads it? |
| The record and this packet (M3-6; `b0a0f352`) | `planning/mvp-m3-evidence.md`, this packet, `planning/HANDOFF.md`, `planning/roadmap.md`, `.github/copilot-instructions.md` | The gates at `d35813c7` with their UTC times and lines; the bundle's hashes; the stops; six open items; the claim boundary | Documentation | Do the record's lines match the retained logs and `build/model/evidence/`, and do the claims stay inside section 3? |

## 3. Claim boundary

**Supported by the exact commit** (proof about the abstract model, unit
tests, deterministic reports, and the differential comparison; no
emulation, no hardware):

- **In the abstract model** (`model/proof/`, Rocq 9.3.0, every theorem
  closed under the global context): the validated policy semantics is
  total and default-deny (T1, I10); for every validated instance that
  passes A8, every grant's permission is allowed by `decide` and every
  channel's endpoints have their rules (T2, I11); under A8 the view's
  flows are within the policy's, and under A6 the closures of the
  policy's flows and the declared channels are equal (T3a, T3b), the
  three relations equal for the projection; for Model 0.2's projection
  of the fixed profile, every derived mapping of `derive_enforcement
  canonical_configuration` has its presence and each of its leaf rights
  allowed by `decide` (T4; the four non-executable mappings; not the
  guest-code resources Model 0.2 lacks); a policy-sealed state exists
  only when A1 to A6 and A8 pass and carries one combined identity (T5);
  for the MVP's three-hart binding, no domain's hart is the control hart
  (H0), the binding is injective and total into the non-control harts
  (H1; nothing about idle harts), each hart's private objects are
  disjoint from every other hart's, from every domain's window and the
  shared pages, and from everything a root can map, and no view passing
  A3 and A8 grants a domain a permission on monitor memory (H2), and
  over the twenty-transition vocabulary only the control hart writes
  before the barrier while after it published data is never written, a
  ring's records and head are its writer's and its tail its reader's,
  and a transition writes only its own hart's private objects (H3); the
  three instances and the projection compute to the security model's
  stated results, and the generated projection equals the adapter's.
- **The executable model** (`model/src/policy.c`, GCC and Clang): the
  same analyses on the same terms give the same verdicts as the Rocq
  functions on every instance and mutation; `be_seal_with_policy`
  refuses each A1 to A6 and A8 failure the tests construct; the
  adapter's view of the fixed-TE fixture equals the generated projection;
  169 pinned checks, identical output on both toolchains; the identities
  equal the Rocq ones (FNV-1a over the same bytes).
- **Differential agreement:** the Rocq oracle, the model's checker, and
  the MVP's offline checker agree on Instances 2 and 3 and their 73
  mutations (three-way), and the oracle and the model's checker on
  Instance 1, its projection, and their 22 mutations (two-way); every
  mutation's observed failing set equals the one written from Part 3
  before any checker ran; 241 comparisons, no disagreement, identical on
  the host and in the evaluator.
- **The accepted Model 0.2 gate is unchanged** under the refreshed lock
  and beside the new work: the accepted reports byte-identical, the
  identity `0x2a4c5a62bc446015`, the 24 accepted reports closed.
- **The gates** at `d35813c7` from a clean tree: `./be model-check`
  (2026-10-28, 22:19 to 22:20 UTC) and `./be evaluate` (22:20 to 22:21
  UTC) pass; the evaluator's six tools equal the host's.

**Trusted or assumed:** the accepted Model 0.2 and its 23 obligations,
used as they are; the Rocq prover 9.3.0 and its standard library 9.2.0
(not pinned by the lock; open item 4); the host's toolchain as the lock
pins it; the MVP's `policy-check.py` as one of the three computations,
not as an oracle; the transition footprints as the plan's reading of the
MVP sources, recorded with their lines; the fixed identifier assignment
(classes memory 0, channel 1, domain 2, manifest 3; permissions read 0
to pause 9) that the generator enforces and both checkers share.

**Unavailable or `NOT RUN`:** no board (none planned; the K3 untouched);
no emulation; no byte identity between the host's and the evaluator's
`.vo` files and binaries (the `/work` mount path; the reports, the
closed-assumption logs, `source.sha256`, and the differential table are
identical; open item 3); no MVP-checker form of Instance 1 (erratum 10).

**Not implemented or claimed:** C refinement (neither checker is proved
to be the Rocq function); that the MVP monitor satisfies I10 to I16 (the
barrier, the rings' implementation, the IPI protocol, and memory ordering
are unmodeled); formal verification of Beryllium; any dynamic case (Part
6; A7 beyond its vacuity and the refusal of a delegating permission); a
manifest encoding or runtime parser; widening Model 0.2's bounds; a
runtime policy mechanism; M4's claim ledger. Model, Helium, R-series,
B-series, M0, M1, and M2 claims do not transfer beyond what M3 uses by
name; nothing here is a security claim about the implementation.

## 4. Load-bearing invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| The notation's semantics is total and default-deny | Security model v1 Part 2; I10 | `decide` over the validated policy | T1 (`claim_decide_total`); `be_policy_decide`; the differential |
| A validated view passing A8 grants nothing the policy denies | Part 3 A8; I11; Revision 1 R1.3 | `a8`, `be_policy_a8` | T2 (`claim_a8_sound`); 20 grant mutations rejected by all computations |
| Sealing with policy implies conformance | Part 7 row 1; plan Q4 | `seal_with_policy`, `be_seal_with_policy` | T5; the unit test's refusals; `claim_projection_results` |
| The derived mappings of the fixed profile are policy-allowed | Plan Q6; the accepted `claim_derived_rights_bounded`, `claim_derived_root_soundness` | the adapter and bridge lemmas | T4 (`claim_projection_mappings_allowed`) |
| The MVP binding: one domain per hart, one non-control hart per domain | Revision 1 I13, I14 | `mvp_binding` | H0, H1; `policy_test.c`'s binding mutations |
| Per-hart private state disjoint and unmapped; one writer per shared word by phase | Revision 1 I15, I16 | `Binding.v`'s classes, extents, transitions, footprints | H2, H3 |
| The analyses are implemented the same three times | Plan Q8, Q9; Part 4's differential method | the oracle, `policy-run`, `policy-check.py` | `BE_MODEL_DIFFERENTIAL: PASS … comparisons=241` |
| The accepted model is untouched | Plan stop 2, Q5 | | `git diff f8f89758 d35813c7` on the accepted files empty; the 24 accepted reports closed |

## 5. Review history, stops, and errata

| Event | Resolution |
| --- | --- |
| The M3 plan's first draft was reviewed by `gpt-5.6-sol` (the responsible human's direction and authorization): twelve findings | Incorporated before acceptance; plan acceptance record, section 5 |
| Q12's budgets made soft limits (the human: limits must not impact quality) | `c2c249f4`, the accepted plan |
| The second `gpt-5.6-sol` review (the human's direction) of the accepted plan and Revision 1's first candidate: seven plan errata, eleven revision findings, four packet findings | Errata 1 to 7 recorded; Revision 1 corrected (`019cca64`) and accepted |
| **Stop 6** (M3-2): the rootless evaluator installs Node.js 22.23.1 where the lock had v22.22.2 | The human's remedy A: the host and the lock moved to 22.23.1 (`0e05d338`); erratum 8 |
| **Stop 5** (M3-4): new C 3,447 lines against about 2,000 | The human re-set the limit to 6,000; erratum 9 |
| **Pass criterion 4** (M3-4, M3-5): Instance 1 has no MVP-checker form | The human chose two-way for Instance 1 and its projection; erratum 10 |
| **Stop 5** (M3-3): new Rocq 3,044 lines against about 3,000 | The human re-set the limit to 6,000; erratum 11 |
| Three Revision 1 prose errata found by M3-3 against the sources (the harts start after the publication; the ring views are private; the roots are published data) | Recorded in Revision 1's acceptance record with the human's agreement; `Binding.v` classifies as the sources show |
| M3-4's `policy_test.c` pinned the mutation count at zero before M3-5's set existed | The pin moved to 91 in M3-5's commit (an M3 file) |
| The seed 20261028 drew two identical anchor mutations | Seed 73, with a distinctness check |
| The Rocq and C identities differed in the first reconciliation | Both now FNV-1a over the same byte layout; the four combined identities equal; the Rocq sealed canonical identity stays the accepted abstract one, so that one combined value differs by design |

**Open for human judgment:** the eleven plan errata (the plan's
acceptance record); the six open items of the evidence record; the
soft limits as re-set (C 6,000; Rocq 6,000; generator and driver about
1,500, at 1,377). *Closing note:* with the acceptance, the responsible
human read the two re-set limits as 6,000 per lane, a combined 12,000
for Rocq and C against the measured 6,492 (erratum 12); see the
[decision record](#decision-record).

**Not run by SOP:** no review of the implementation by a different
model beyond the two plan-stage reviews the responsible human directed;
no separate scope review; no deep security review. The work ran on
`claude-opus-5.5` sub-agents at `max` effort with the `long_context`
tier for every implementation package, orchestrated and reviewed by
`claude-fable-5.1` under the repository's model split; the orchestrating
session reviewed each package's report, the integration, and the gates.

## 6. Validation and retained evidence

All at exact commit `d35813c7` from a clean tree on `l1` (x86_64, Fedora
44), 2026-10-28, the lock's tools, ccache bypassed:

| Command | When (UTC) | Result | Covers |
| --- | --- | --- | --- |
| `./be model-check` | 22:19:14-22:20:13 | `tools: PASS`; `source policy: PASS`; the accepted unit tests PASS (GCC, Clang); `policy fixtures: PASS instances=3 projection=1 mutations=91`; `policy layer unit tests: PASS checks=169 instances=4 mutations=91`; four `BE_MODEL_RESULT: PASS`; `BE_POLICY_RUN: PASS instances=4 mutations=91`; `policy layer report: PASS`; `reports: PASS`; `security model v1 policy and hart binding proofs: PASS instances=generated`; `proofs: PASS`; `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`; `evidence: PASS`; the documentation source gate PASS | The whole model gate under the refreshed lock, through the root wrapper |
| `./be evaluate` | 22:20:27-22:21:27 | `Model 0.2 evaluator image build: PASS`; the same lines inside the container; `Model 0.2 rootless checks: PASS`; `Beryllium Architecture Model 0.2 rootless validation: PASS`; `BE_EVALUATION: Model 0.2 rootless evidence PASS` | The same in the pinned rootless evaluator, its six tools equal to the host's |
| `make -C model clean check` | 22:17-22:18 (54.0 s; on the content of `d35813c7` 44 s before its commit) | The same lines; the proof 45.7 s | The make-level gate |

Retained: the [evidence record](mvp-m3-evidence.md) with the bundle's
hashes (`source.sha256` `b259ae51…` identical host and evaluator;
`differential.txt` `57a5267e…` identical; `artifacts.sha256`
`5101b82e…` host, `732e6a6e…` evaluator; `mvp-inputs.sha256` with the
six MVP inputs' SHA-256s); the model's `build/model/evidence/` and
`build/model-rootless-logs/` on `l1`, generated and not committed; the
logs under the session folder.

## 7. Recommended review sequence

```sh
git worktree add --detach /tmp/be-m3-review b0a0f352d7969a8f8cf28cf0d25b89fc372e70f2
cd /tmp/be-m3-review
git --no-pager log --oneline 97be918d..HEAD                      # the M3 commits
git --no-pager diff --stat 97be918d HEAD -- . ':!model' ':!planning' ':!.github'   # must be empty
git --no-pager diff --stat f8f89758 HEAD -- model/proof/Model.v model/proof/Initialization.v model/proof/Isolation.v model/proof/Transition.v model/proof/Claims.v model/proof/Assumptions.v model/src/manifest.c model/src/state.c model/src/fixtures.c model/tests/unit/test_main.c model/tools/model-run.c model/tools/model-report.c   # must be empty
```

1. **Plan, revision, errata** (30 min): `planning/mvp-m3-plan.md`
   ("Decision record", "Goal and pass criterion", "Claim boundary and
   non-goals"); the plan's acceptance record's errata 1 to 11; Revision
   1's acceptance record and its three errata; then section 3 of this
   packet against them.
2. **The claims** (60 min): `model/proof/PolicyClaims.v` (the record's
   fourteen fields), then `Policy.v`'s T1 to T5 and `Binding.v`'s H0 to
   H3 and its transition table against `mvp/src/mvp-runtime.c`,
   `mvp-hartmain.c`, `mvp-ring.c`, `mvp-hart.h`, `mvp-platform.h`,
   `mvp-layout.h`; `PolicyAssumptions.v`'s reports in
   `build/model/proof/policy-assumptions.log` after step 5.
3. **The executable model** (40 min): `model/src/policy.c`'s A1 to A8
   against security model v1 Part 3 and `mvp/tools/policy-check.py`;
   `be_seal_with_policy`; `policy_test.c`'s refusals and binding
   mutations; `gen-policy-fixtures.mjs`'s identifier rule and the
   projection's derivation.
4. **The differential check** (20 min): `model/fixtures/mutations.json`'s
   expected sets against Part 3; `model/tests/differential.sh`; the
   `differential.txt` table in the evidence bundle.
5. **Run the gates** (3 min on a host that satisfies the lock; the
   evaluator relabels the tree and rebuilds `build/model`, open items 1
   and 2):

```sh
cd /tmp/be-m3-review && CCACHE_DISABLE=1 make -C model check && ./be evaluate
cd - && git worktree remove /tmp/be-m3-review
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The scope matches the accepted M3 plan at `c2c249f4` with Q1 to
      Q12 at their defaults and the eleven errata as recorded, and the
      accepted Revision 1 at `019cca64` with its three errata.
- [ ] The claims in section 3 match the evidence record and the retained
      bundle, and stay inside "proof about the abstract model, unit
      tests, differential agreement".
- [ ] The trust assumptions are acceptable: the accepted Model 0.2 used
      as it is, Rocq 9.3.0 with the unpinned standard library, the MVP
      checker as one computation, the footprints as the plan's reading
      of the sources, the fixed identifier assignment.
- [ ] The negative paths are covered: the 91 mutations with their
      expected sets, the sealing refusals, the binding mutations, the
      six injected driver faults.
- [ ] The four stops' resolutions (remedy A; the limits re-set; Instance
      1 two-way) are confirmed as recorded.
- [ ] Successor work stays excluded: M4, the merge into the development
      branch, any push, further security model or Model changes, root
      integration.
- [ ] Decision: accept exact commit `b0a0f352` as the M3 result; request
      revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `b0a0f352d7969a8f8cf28cf0d25b89fc372e70f2` and the date. The
  acceptance record names that SHA; the plan's status record and the
  status documents are updated to match. Acceptance starts no successor:
  M4's bounded plan, any merge of `beryllium/mvp-m3` into the
  development branch, and any push each need their own instruction.
- **Request revisions:** a new commit and a new packet follow;
  `b0a0f352` is not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commit `b0a0f352d7969a8f8cf28cf0d25b89fc372e70f2` is
responsible-human accepted as the M3 result as of 2026-10-28
(instruction `6000 per lane, so 12,000 combined soft limit. accept
b0a0f352`). It is on branch `beryllium/mvp-m3`, local and unpushed; M4
is not started or authorized.

**Next:** nothing is directed. Candidates for your instruction, each its
own decision: fast-forwarding the development branch
`beryllium/single-hart-runtime-r0` to the commit that records this
acceptance and pushing it with `beryllium/mvp-m3` and
`beryllium/mvp-m3-plan` to the private `origin`; directing the M4 plan
(the release candidate) as a proposal on a new branch from that tip.

**Action required from you:** none for M3.
