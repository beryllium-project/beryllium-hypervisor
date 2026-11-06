<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Security model v1 Revision 1 review and acceptance record

This packet presents the exact commit that appends Revision 1, "the hart
binding and the third instance", to the accepted
[security model v1](security-model-v1.md): work package M3-1 of the
accepted [M3 plan](mvp-m3-plan.md) (`c2c249f4`, accepted 2026-10-28),
which the accepted [MVP plan](mvp-plan.md)'s M3 requires as "an
additive revision of security model v1, as its own exact commit for
acceptance before any model work". It also records the responsible
human's decision on it.

## Decision record

The responsible human accepted exact commit
`019cca64971d2399faba3d768d6f5b1fc9145198` (parent `9063b7a5`, on
branch `beryllium/mvp-m3` from the M3 plan's acceptance record
`97be918d`) as Revision 1 of security model v1 on 2026-10-28. The
instruction, given in reply to this packet's request to accept, revise,
or defer that exact commit, was `accept 019cca64`, checked to resolve
uniquely (`git rev-parse --disambiguate=019cca64`). The first candidate
`32298add` is superseded and was never accepted. The five flagged
readings of section 3 stand as the revision states them, the
interpretation of A8's "binding" (R1.3) among them, so no plan revision
is needed for it; the seven errata of the accepted M3 plan stand as
recorded in its acceptance record with the judgment that none needs a
plan revision before M3-2.

- **Scope:** acceptance covers exactly the appended section at that
  commit; the accepted text of Parts 1 to 7 is byte-identical and was
  not re-accepted. Sections 2 to 8 are the packet as presented, apart
  from a note above the section 8 checklist. Section 1's status rows and
  the closing lines of section 9 now show the outcome. The decision
  itself is recorded only here, in the document's decision record, and
  in the revision's status line and record.
- **Decision support:** packet commits `9063b7a5` and `cc364094` and
  this acceptance-record follow-up are decision support, not revision
  content.
- **Effect under the accepted M3 plan:** work packages M3-2 to M3-6 may
  begin on `beryllium/mvp-m3`: the lock refresh and the enumerated
  build-list edits, the Rocq modules, the executable model and host
  checker, the differential check, and the record and packet; each of
  the plan's ten stop conditions returns M3 to the responsible human,
  and a soft limit exceeded returns the limit for re-evaluation. Nothing
  else is authorized: no board work (the shared K3 is in use by the
  responsible human for another project), no change under `mvp/`, no
  push or merge, no M4.
- **Evidence status:** acceptance adds no implementation, proof, or test
  evidence; I13 to I16 are specification, and no claim is made that the
  implementation or the hardware satisfies them.
- **Errata recorded after acceptance, revision text unchanged** (found
  by M3-3 against the MVP's sources on 2026-10-28; the responsible human
  agreed to their recording, `errata=true`; none makes an obligation
  false, and `model/proof/Binding.v` classifies the objects as the
  sources show):
  1. R1.1's `hart` row says hart 0 starts each domain hart "before the
     barrier". The source publishes the blocks, the generation word last
     (`BE_MVP:07 BLOCKS_PUBLISHED`), and starts the harts after
     (`BE_MVP:08 HART_STARTED`; `mvp-runtime.c`, `publish_blocks` then
     `start_harts`); the start writes only hart 0's data either way.
  2. R1.2's I15 lists the domain hart's private words as the trusted
     stack, the saved frame, `controls`, `state`, and `entered`; each
     hart's two ring **views** (`struct be_mvp_hart_page`'s `inbound` and
     `outbound`) are also the hart's own after the barrier
     (`mvp-hartmain.c`: "from here on they are this hart's").
  3. R1.2's I16 list of immutable published data omits the two G-stage
     roots, which hart 0 builds before the barrier and no transition
     writes after it.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `019cca64971d2399faba3d768d6f5b1fc9145198` (tree `c5a1ba72db1e24b9c45a014cfc5e3867e027d465`), parent `9063b7a5`, on branch `beryllium/mvp-m3` from the M3 plan's acceptance record `97be918d`, as the plan directs. The first candidate `32298add` is superseded: the second `gpt-5.6-sol` review the responsible human directed found its I15 and I16 wrong against the MVP's sources and its erratum carrying a false rights fact (section 5); nothing else changed between the two (`git diff 32298add 019cca64 -- planning/security-model-v1.md`) |
| Current status | Documentation only: 254 lines appended to `planning/security-model-v1.md` as the section "Revision 1 (2026-10-28): the hart binding and the third instance" with its own status record. The accepted text above it is byte-identical to the accepted document (checked: the new file begins with the old file; `git diff 97be918d 019cca64` has no removed line). Reviewed twice by `gpt-5.6-sol` on the responsible human's direction and session authorization (the plan's first draft, then this revision's first candidate); every finding is incorporated (section 5). The fast source checks pass (whitespace; every link and anchor in the revision). Responsible-human accepted on 2026-10-28 (instruction `accept 019cca64`) |
| Decision requested | Accept the exact commit as Revision 1 of security model v1, request revisions, or defer. Five readings are flagged for explicit attention in section 3: the interpretation of A8's "binding" (R1.3), I13 to I16's scope (R1.2), I15's and I16's per-word, per-phase form against the MVP plan's sentence (R1.2), the `te-poc` scenario as an extension of Instance 2's labeling (R1.4), and the erratum on Model 0.2's fixture (R1.5). Seven errata of the accepted M3 plan found by the same review are recorded in the plan's [acceptance record](mvp-m3-plan-review-summary.md), with the judgment that none needs a plan revision before M3-2 unless the A8 interpretation is rejected. Recorded outcome: accepted; the readings stand |
| Successor status | As presented: acceptance would let work packages M3-2 to M3-6 of the accepted M3 plan begin on this branch (the lock refresh, the Rocq modules, the executable model, the differential check, the record); none had started. After the decision: M3-2 to M3-6 begin. M4 and everything the M3 plan does not authorize stay excluded |
| Publication status | Private repository; the target is on local branch `beryllium/mvp-m3`, unpushed, as are `beryllium/mvp-m3-plan` (`97be918d`). The development branch `beryllium/single-hart-runtime-r0` is at `50b77c00` locally and on the private `origin`. No tag, publication, or release |

As presented: please review exact commit `019cca64` and accept it,
request revisions, or defer. Outcome: accepted; see the
[decision record](#decision-record).

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| Revision 1 | [`security-model-v1.md`](security-model-v1.md), the appended section (254 lines, after the accepted status record) | R1.1 the `hart` object class with the block extents and the `domain` row's binding (Part 1); R1.2 invariants I13 to I16, scoped to the MVP's static-binding configurations, I15 and I16 stated per word and per phase (the control hart's pre-barrier initialization; the stack, saved frame, and `controls`/`state`/`entered` private after it; immutable published data and ring state as the two kinds of shared words, the rings' records and head the writer's and the tail the reader's; the management state hart 0's own), and two consequences of the binding in place of a literal I5 and I7; R1.3 the interpretation of A8's "binding", with its reason, for acceptance; R1.4 Instance 3, the `anchor` policy verbatim with its labeling, need sets, hart binding, the accepted M2 result's board facts, and the eight analyses' results, and the note that `te-poc` extends Instance 2's labeling; R1.5 Part 7's three new rows, the Fixtures row's entry, and the erratum that Model 0.2's fixed-TE fixture is a projection of Instance 1 with four non-executable mappings; R1.6 what it does not change; its status record | Specification text only; additive; the accepted text unchanged; nothing implemented, proved, or tested; no code or model change | Is every change an addition that leaves the accepted analyses, instances, and claims as they are, and does each new invariant state exactly what the MVP's sources show (`mvp/src/mvp-hart.h`, `mvp-platform.h`, `mvp-ring.c`, `mvp-runtime.c`, `mvp-hartmain.c`, `mvp-layout.h`)? |
| Status pages and navigation | [`roadmap.md`](roadmap.md), [`HANDOFF.md`](HANDOFF.md), [`README.md`](README.md), `.github/copilot-instructions.md`, `planning/.vitepress/config.mts` | Record the proposed revision | Changed in this packet's commit, not in the target; status text only | None |

Exact changed-file inventory:

```text
# git diff --name-status 9063b7a5 019cca64
M	planning/security-model-v1.md
# git diff --name-status 97be918d 019cca64   (both candidates together)
M	planning/security-model-v1.md
```

`git diff --stat 9063b7a5 019cca64 -- . ':!planning/security-model-v1.md'`
is empty: the target changes one file and nothing else, and against the
acceptance record the change is an append (`git diff 97be918d 019cca64`
shows additions only).

## 3. Claim boundary

**What the revision adds to the accepted specification:**

- A `hart` object class (Part 1), monitor-owned, with its authority in
  the manifest's binding records, the hart region, and the start rule;
  the `domain` class's binding to its one hart in the MVP.
- Four invariants, scoped to the MVP's static-binding configurations
  (the fixed profile and Model 0.2, two domains on one hart, are outside
  them): I13 (each hart at most one domain), I14 (each domain exactly
  one hart, not the control hart; nothing about idle harts), I15
  (per-hart state private after the barrier, the control hart's
  initialization before it, named per word), I16 (every shared word has
  one writer: immutable published data and ring state after the barrier;
  the management state is hart 0's own). Each has no obligation today;
  M3-3 is to prove them over the static binding in the abstract model.
- An interpretation of A8's wording, for acceptance: A8's "binding" is
  the domain's binding to its extents, and structural bindings (vCPU,
  root, VMID, stack, saved state, and the hart) are mechanism metadata
  outside A8, because A8's own parenthesis gives no permission for them
  and no rule class names those objects, so no instance could pass A8
  under the other reading; the MVP's checker implements this reading
  (`policy-check.py`, `a8`).
- The note that the `te-poc` scenario extends Instance 2's labeling by
  the hart and MVP regions; Instance 2's text is unchanged.
- Instance 3, the `anchor` scenario: policy (SHA-256 `bfecfa92…`),
  labeling, need sets, hart binding, and the analyses' results as the
  MVP's checker reports them (A1 to A8 pass; A5 reports two static
  single-writer pages; A6 `F = D = {(host_t, prot_t), (prot_t, host_t)}`;
  A7 vacuous); the configuration identity `336bfddc…`.
- Three Part 7 rows (the binding, the per-hart state, the rings), the
  Fixtures row's entry for Instance 3, and the erratum on Model 0.2's
  fixture.

**What it does not change:** the notation; A1 to A8; Instances 1 and 2;
I1 to I12; Parts 4, 5, 6; V1 to V4; the accepted status record; any
accepted claim. The MVP plan's stop condition 1 admits exactly this
revision.

**What it does not claim:** any implementation, proof, or test; any
hardware or security claim (Instance 3's board facts are the accepted M2
result's diagnostic bring-up evidence, cited); that the MVP monitor
satisfies I13 to I16 (the obligations M3-3 would prove are about the
abstract static binding, not the implementation's rings, IPIs, barrier,
or memory ordering).

**Flagged readings.**

1. **R1.3, the interpretation of A8's "binding"** (M3 plan Q1's
   default, made explicit): the second review found that the accepted
   A8 quantifies over every binding in the sealed manifest, and Model
   0.2's manifest binds a domain to its vCPU, root, VMID, stack, and
   saved state, so a reading in which the hart binding, or any
   structural binding, is outside A8 fixes an ambiguity in the accepted
   wording. The revision says so and gives the reason the other reading
   is untenable (no permission, no rule class, no passing instance). It
   does not edit A8; the responsible human accepts or rejects the
   reading with the revision, and a rejection needs an M3 plan revision
   before M3-3.
2. **R1.2, the scope.** I13 does not hold for the fixed profile, whose
   two domains share one hart by checked switches; the revision scopes
   I13 to I16 to the MVP's static-binding configurations and marks the
   fixed profile and Model 0.2 "not applicable".
3. **R1.2, I15's and I16's form.** The MVP plan says "the control hart
   is the only writer of shared monitor state" and the M3 plan's Q7
   named the management state as control-written shared state; the
   sources show otherwise: hart 0 initializes a domain hart's whole
   block before the barrier (`mvp-runtime.c`), the domain hart's ring
   indices are read by hart 0 (`mvp-ring.c`), domain harts read
   immutable published data after the barrier (`mvp-hartmain.c`), and
   the management state is hart 0's own (`mvp-hart.h`). I15 and I16
   state the discipline per word and per phase; the plan's intent, that
   no shared word has two writers and that the control hart alone
   initializes, is kept.
4. **R1.4, Instance 2.** The `te-poc` scenario labels two monitor
   regions Instance 2's accepted text does not name (the hart region and
   the MVP region, M0's); the revision records it as an extension of the
   labeling, and the M3 plan's fixture "Instance 2" is that extension.
5. **R1.5, the erratum.** The accepted Part 7 row says the fixed-TE
   fixture's topology is Instance 1; Model 0.2 has no guest-code frame
   and grants no `execute` (fact: `Model.v` `platform_inventory`,
   `read_write_rights`, `read_rights`, `canonical_authority`), so its
   fixture is a projection of Instance 1 with four non-executable
   mappings. The accepted sentence stands; the revision records the
   correction, as the governance rule for accepted text requires.

## 4. Load-bearing decisions

| Decision | Where | Why it matters | Alternative recorded |
| --- | --- | --- | --- |
| Additive only; the accepted text byte-identical | The whole section | The MVP plan's stop condition 1 and the repository's rule for accepted documents | Edit the tables in place |
| I15 and I16 stated per block field and per phase from the sources | R1.2 | A per-hart "block" is written by hart 0 before the barrier and by the domain hart after it; a coarser statement would be false | The MVP plan's sentence taken literally |
| The hart binding outside A8 | R1.3 | Keeps the policy about authority and the MVP's checker as it is | A `hart : run` rule class |
| Instance 3 verbatim, with the checker's results quoted | R1.4 | The instance is the accepted M2 result's configuration, not a paraphrase; the results are the MVP's checker's, which M3-5 will compare with the model's and the oracle's | A summary |
| The erratum recorded, not edited | R1.5 | M3-3's T4 is stated for the projection; the accepted document's sentence is corrected without changing accepted text | Silently hard-code the missing frames, or edit the row |
| I13 to I16 scoped to the MVP's static binding | R1.2 | I13 is false for the fixed profile; an unscoped invariant would be refuted by an accepted configuration | Assert them of every configuration |
| The A8 reading presented as an interpretation for acceptance | R1.3 | It fixes an ambiguity the accepted wording has; presenting it as "unchanged A8" would hide that | Edit A8, or leave the ambiguity to the implementation |

## 5. Review history and resolved findings

Two reviews by `gpt-5.6-sol` were run on the responsible human's
direction and session authorization (`I will authorize gpt-5.6-sol for
this session as a reviewer`), each through a one-launch edit of the
governance hook's required model, restored afterwards with an equal
SHA-256 (`4f4c2c87…`); the repository's model pin is unchanged. The
first reviewed the M3 plan's draft (its twelve findings and their
resolutions are in the plan's [acceptance
record](mvp-m3-plan-review-summary.md), section 5). The second, on
2026-10-28 (16:38 to 16:51 UTC), reviewed the accepted plan as updated
and this revision's first candidate `32298add`, and returned seven
findings on the plan (recorded as errata in the plan's acceptance
record), eleven on the revision, and four on this packet's first text.
The revision's findings and what `019cca64` now says:

| # | Finding (severity as given) | Resolution in the target |
| --- | --- | --- |
| B1 | must-fix: R1.3 redefined A8's "binding" as extent grants, which excludes the manifest's structural bindings and so changes A8 while claiming no analysis changes | R1.3 presents the reading as an interpretation of A8's wording for acceptance with the revision, with the reason the other reading is untenable, names the structural bindings it places outside A8, and says a rejection needs a plan revision |
| B2 | must-fix: I15 listed the domain hart's ring indices (`inbound_tail`, `outbound_head`) as private, but hart 0 reads them after the barrier (`mvp-ring.c`) | They are ring state under I16; I15's private words are the stack, the saved frame, `controls`, `state`, and `entered` |
| B3 | must-fix: I15's "written by no other hart" ignored hart 0's pre-barrier initialization of the whole hart page (`mvp-runtime.c`, `mvp-platform.h`) | I15 is stated by phase: the control hart alone writes everything before the barrier; the private words are private after it |
| B4 | must-fix: I16's "after the barrier every shared word is a ring word" omitted the immutable published data domain harts read (descriptor, entry frame, map, leaves, state configuration, hart 0's binding table; `mvp-hartmain.c`) | I16 names two kinds of post-barrier shared words, immutable published data and ring state, with the one-writer discipline for each |
| B5 | must-fix: I13 is false for the fixed profile (two domains on one hart), and I15 said the hart region is `monitor_mem_t` in Instance 2, which the accepted text does not state | I13 to I16 are scoped to the MVP's static-binding configurations, the fixed profile and Model 0.2 marked "not applicable"; the hart region is named `monitor_mem_t` "in the `te-poc` and `anchor` scenarios" |
| B6 | must-fix: R1.5 said I13 and I14 make the binding "onto non-control harts" | "into the non-control harts; nothing about harts that run no domain" |
| B7 | must-fix: R1.4 said the management operations are "decided by the control hart against the policy's `domain` class", but HS evaluates no policy | "validated offline against the policy's `domain` class (A8) and decided at run time by the control hart from the sealed grants alone, with no policy evaluation in HS" |
| B8 | must-fix: the erratum said Model 0.2's four mappings have `execute` rights; every rights record has `right_execute := false` | "four non-executable mappings (… `right_execute := false` in every rights record); … grants no `execute`" |
| B9 | should-fix: R1.1 gave the per-hart block as `0x20000` bytes, the whole region | The region (`0x20000`) and the two 64 KiB blocks (`0x102044000`, `0x102054000`) are stated separately |
| B10 | should-fix: applying I5 to a first entry is not literal (no source and target pair; the entry frame is copied into the saved page) | Two consequences of the binding are stated in place of a literal application; I5's and I7's text unchanged |
| B11 | should-fix: "nothing here is a hardware or security claim" is umbrella wording for normative invariants | "I13 to I16 are specification: no claim is made that the implementation or the hardware satisfies them" |

The four findings on this packet's first text (that it called the
I15/I16 defect resolved, treated the A8 reading and Instance 2 as
unchanged, did not report the target's `execute` sentence, and repeated
the umbrella non-claim) are resolved by this text. The review confirmed:
the commit is append-only; Instance 3's policy body, labeling, need
sets, hart binding, identities, grant count, flows, and all eight checker
results match the files; the ring directions and head-and-tail ownership
are correct; the projection erratum's conclusion is correct.

**Open for human judgment:** the five flagged readings of section 3; the
seven plan errata and the judgment that none needs a plan revision
before M3-2 unless the A8 interpretation is rejected.

**Not run by SOP:** no review beyond the two the responsible human
directed. The revision was written by the orchestrating session on
`claude-fable-5.1`; no coding sub-agent ran.

## 6. Validation and retained evidence

Documentation only. Checked at the target: `git diff --check` clean; the
accepted text is byte-identical (the new file begins with the accepted
file's bytes); every link and anchor in the revision resolves; the
target changes one file, by addition only against the acceptance
record. The facts quoted were read at
`mvp/scenarios/anchor/{policy.te,scenario.json}` (`18d552bc`),
`build/mvp/gen/anchor/authority-report.json` as built at `397670e5`,
`mvp/results/20261028-com260-m2a/`, `mvp/src/mvp-layout.h`,
`mvp/src/mvp-hart.h`, `mvp/src/mvp-platform.h`, `mvp/src/mvp-ring.c`,
`mvp/src/mvp-runtime.c`, `mvp/src/mvp-hartmain.c`, and
`model/proof/Model.v` and `model/src/fixtures.c` at `f8f89758`. No
VitePress build was run.

## 7. Recommended review sequence

```sh
git worktree add --detach /tmp/be-smv1-r1-review 019cca64971d2399faba3d768d6f5b1fc9145198
cd /tmp/be-smv1-r1-review
git --no-pager diff --name-status 97be918d HEAD        # M planning/security-model-v1.md only
git --no-pager diff 97be918d HEAD | grep -c '^-[^-]'  # 0: additions only
git --no-pager diff 32298add HEAD -- planning/security-model-v1.md   # the second-review corrections
```

1. **The accepted inputs** (15 min): `planning/mvp-plan.md`, M3
   deliverable 1 and departure row 4; `planning/mvp-m3-plan.md`, "The
   security model revision (M3-1)", Q1, Q3, Q7.
2. **R1.1 and R1.2** (30 min): against `planning/security-model-v1.md`
   Part 1 as accepted, and against `mvp/src/mvp-layout.h` (the block
   layout), `mvp/src/mvp-hart.h` (`struct be_mvp_state_page`),
   `mvp/src/mvp-platform.h` (`struct be_mvp_hart_page`),
   `mvp/src/mvp-runtime.c` (the publication), `mvp/src/mvp-ring.c` (who
   reads which index), and `mvp/src/mvp-hartmain.c` (the entry).
3. **R1.3 and R1.4** (20 min): against Part 3's A8 and
   `mvp/tools/policy-check.py`'s `a8`; `mvp/scenarios/anchor/policy.te`
   and `scenario.json`; the M2 result's record.
4. **R1.5 and R1.6** (10 min): against Part 7 as accepted and
   `model/proof/Model.v`.

```sh
cd - && git worktree remove /tmp/be-smv1-r1-review
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The revision is additive: the accepted text is byte-identical, and
      no accepted analysis, instance, or claim changes.
- [ ] I13 to I16 state what the MVP's sources show, their scope (the
      MVP's static-binding configurations) is right, and I15's and I16's
      per-word, per-phase form is the intended precise reading of the
      MVP plan's sentence.
- [ ] The interpretation of A8's "binding" (R1.3) is accepted, or a plan
      revision is requested instead.
- [ ] The seven plan errata need no plan revision before M3-2.
- [ ] Instance 3 is the `anchor` scenario verbatim, with the checker's
      results quoted correctly.
- [ ] The erratum on Model 0.2's fixture (R1.5) is correct and correctly
      left as a recorded correction.
- [ ] Decision: accept exact commit `019cca64` as Revision 1 of security
      model v1; request revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `019cca64971d2399faba3d768d6f5b1fc9145198` and the date; the
  revision's status record and the status documents follow. Under the
  accepted M3 plan, M3-2 to M3-6 may then begin on `beryllium/mvp-m3`.
- **Request revisions:** a new commit and a new packet follow;
  `019cca64` is not treated as accepted.
- **Defer:** the status stays as presented; M3-2 to M3-6 do not start.

**Status:** exact commit `019cca64971d2399faba3d768d6f5b1fc9145198` is
responsible-human accepted as Revision 1 of security model v1 (M3-1) as
of 2026-10-28 (instruction `accept 019cca64`; the first candidate
`32298add` superseded). It is on branch `beryllium/mvp-m3`, local and
unpushed. M3-2 to M3-6 begin under the accepted M3 plan.

**Next:** M3-2, the lock refresh and the enumerated build-list edits,
then M3-3 to M3-6, ending in one result review packet.

**Action required from you:** none until the M3 result is presented, or
a stop condition returns M3 to you.
