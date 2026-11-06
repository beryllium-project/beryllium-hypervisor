<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M6 plan review and acceptance record

This packet presents two ordered decisions that follow the responsible
human's direction of 2026-10-30, `we will go with RC3 first`:
[Plan revision S3-B](mvp-plan.md#plan-revision-s3-b-release-candidate-3-and-milestone-m6-the-mvp-core-profile)
of the MVP plan, which adds milestone M6 and release candidate 3 before
the release path's steps 2 to 7 (decision D18), and the
[M6 plan](mvp-m6-plan.md), which bounds the retirement of the "MVP core
profile" debt as release candidate 3. It also records the responsible human's decisions on them.

## Decision record

The responsible human accepted Plan revision S3-B at exact commit
`f8b77ac94fc6b5a80e68e6a972fa353b800d068b` (parent `cd9cfa5f`) and the
M6 plan at exact commit `b2c62d54f21c3cabdad3fefcc562499ace601089`
(parent `f8b77ac9`), both on branch `beryllium/mvp-m6-plan`, on
2026-10-30, and separately authorized M6 implementation. The instruction
given in reply to this packet's two ordered decisions was `accept
f8b77ac9 and f8b77ac9`, which names decision 1's commit twice; because
the second decision's target could not be inferred from a repeated SHA,
the session asked, and the responsible human answered the form
`accept-and-authorize` ("Accept b2c62d54 as the M6 plan AND authorize
M6 implementation (M6-2 to M6-8), Q1-Q11 at defaults"), with no open
question answered differently. Each abbreviation was checked to resolve
uniquely (`git rev-parse --disambiguate`).

- **Scope:** acceptance covers exactly the two commits' texts: the
  appended Plan revision S3-B in `planning/mvp-plan.md` and
  `planning/mvp-m6-plan.md`, with Q1 to Q11 at their defaults. Sections
  1 to 8 are the packet as presented, apart from a note above the
  section 8 checklist; section 1's status rows and section 9's closing
  lines now show the outcome. The decision is recorded here, in the M6
  plan's decision record and status, and in the MVP plan's S3-B status
  addendum.
- **Decision support:** packet commit `b2db94c3` and this
  acceptance-record follow-up are decision support, neither plan nor
  implementation.
- **Authorization:** M6 implementation, work packages M6-2 to M6-8 of
  the accepted plan, on branch `beryllium/mvp-m6` from this
  acceptance-record commit, coding on `claude-opus-5.5` under this
  model's orchestration and review (the session's standing split), under
  the plan's eleven stop conditions; board commands only after the human
  confirms the board free, with the human present at the install and the
  restore; no push, merge, tag, publication, release, or kexec use. The
  result is presented as release candidate 3 in one packet.
- **Release candidates:** release candidate 2 (`3867c66c`) stays the
  latest accepted candidate until release candidate 3 is accepted;
  release candidate 1 is accepted history; the release path's steps 2 to
  7 wait for release candidate 3 by this direction (D18) and each need
  their own instruction.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review targets | **Decision 1:** exact commit `f8b77ac94fc6b5a80e68e6a972fa353b800d068b` (parent `cd9cfa5f`, the development branch's tip: release candidate 2 accepted, debt sweep 1, the project-snapshot skill and snapshot), on branch `beryllium/mvp-m6-plan`; it appends Plan revision S3-B to `planning/mvp-plan.md` and changes nothing else. **Decision 2:** exact commit `b2c62d54f21c3cabdad3fefcc562499ace601089` (parent `f8b77ac9`), which adds `planning/mvp-m6-plan.md` and changes nothing else. |
| Current status | **Responsible-human accepted on 2026-10-30** (see the [decision record](#decision-record)), with M6 implementation authorized. As presented: documentation only; proposed, not reviewed. No `mvp/` file, no accepted byte, and no accepted text other than the MVP plan's appended revision changes. No board command. |
| Decisions requested | Recorded outcome: both accepted, M6 authorized, Q1 to Q11 at their defaults. As presented, **in order:** (1) accept exact commit `f8b77ac9` as Plan revision S3-B, request revisions, or defer; (2) accept exact commit `b2c62d54` as the M6 plan and, separately, authorize M6 implementation (work packages M6-2 to M6-8), request revisions, or defer; answer any of Q1 to Q11 whose default you do not want. |
| Successor status | After the decision: M6-2 to M6-8 are authorized on `beryllium/mvp-m6` from the acceptance-record commit, the board campaign waiting on the human's confirmation and presence; everything else stays not authorized. As presented, not started and not authorized: M6 implementation; any change under `mvp/` or `model/`; the board campaign (which waits, after acceptance, on your confirmation that the board is free and your presence at the install and the restore); release-path steps 2 to 7; any merge, push, tag, publication, or kexec use. |
| Publication status | Private repository. `beryllium/mvp-m6-plan` is local and unpushed; the development branch `beryllium/single-hart-runtime-r0` is at `cd9cfa5f` locally and on the private `origin`. No tag, publication, or release. |

As presented: please review exact commits `f8b77ac9` and then `b2c62d54`
and decide on each. Outcome: both accepted, M6 authorized; see the
[decision record](#decision-record).

## 2. Deliverables

| Deliverable | Paths | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| Plan revision S3-B (`f8b77ac9`) | `planning/mvp-plan.md`, appended section | Records the direction: the core-profile debt retired as M6 before the release path's steps 2 to 7, its result release candidate 3 (D18); the three accepted lines it supersedes; the staging with RC1 and RC2 as accepted history | Changes no accepted text but this plan's own appended revision; the claim's text is untouched | Is "RC3 before steps 2 to 7" what you directed, and is D18's wording right? |
| The M6 plan (`b2c62d54`) | `planning/mvp-m6-plan.md` | The design (D-1 to D-7), eight work packages, the counting rule and 4,000-line limit, eleven stop conditions, Q1 to Q11 with defaults, what acceptance authorizes | Bounds M6; authorizes nothing until accepted | Does the design retire the debt without widening the MVP (section 3)? |

Exact changed-file inventory:

```text
# git diff --name-status cd9cfa5f b2c62d54
M	planning/mvp-plan.md
A	planning/mvp-m6-plan.md
```

## 3. Claim boundary

**What the plans say and support:** the frozen fixed profile is replaced
by the MVP's own configuration, generated per scenario from the authority
report, validated, sealed, and derived at boot by the ported accepted R1
mechanism; the derived mappings drive the existing Sv39x4 builder; the
unused fixture roots, pages, guest code, and the control hart's VS-entry
steps go; the privileged effects gather behind one executor with the
proof-bearing subset named; the layout's MVP-owned extents, the image's
base and size, and the board path do not move; release candidate 3 is
made exactly as release candidate 2 was (gates from a clean checkout, a
20-run board campaign from system reset, records, ledger, evidence
record, packet).

**What they deliberately do not change:** the MVP claim's text and
required limit (a needed change is stop 2); the guests, scenarios,
policies, denial path, rings, IPIs, barrier, management extension, and
measurement inputs; the accepted R0-R7 and B0-B7 bytes (ports only); the
board policy and the standing rule; the hart assignment.

**Trusted or assumed:** that the accepted R1 structures widen by port
rules without a semantic change (the host tests on the MVP profile with
both compilers are the check); that the model's instance shape admits the
MVP configuration additively (else deferred, Q4); that the board facts of
M5-6a still bound the layout (unchanged extents).

**Departures for your attention:** the debt was recorded as "after MVP 1.0
or with the clean-repository build root" and now comes before the release
path's steps 2 to 7 on your direction (D18); the `KEXEC_*` names and
`kexec_fdt`, which M5 kept to preserve configuration identities, are
removed (Q3) because M6 changes the identities anyway; the `BE_R3` markers
are replaced (Q2), so the guide's boot story and the fixtures change
while the retained records keep theirs; the seams (D-5) are a code
restructuring with no behavior change, included on the verification
route's stage 0 and bounded by the limit.

**Not run:** nothing of M6 has run; the plan's estimates are estimates.

## 4. Load-bearing decisions

| Decision | Where | Why it matters |
| --- | --- | --- |
| The generated inventory and proposal must agree with the authority report, and boot-time validation must pass for every scenario the offline checker passed | D-1; stop 11 | Closes the policy-to-manifest relation with a concrete manifest in R1's sense; a disagreement is a defect in one of the two |
| The derived mappings are the builder's single input | D-2 | The leaves' rights trace to a derived mapping, not to generated constants |
| The MVP-owned extents, the image's base and size, and the board path do not move | D-4; stop 3 | The board tools, the preflight's region list, the shim, and the staging keep their checks; M5-6a's board facts stay valid |
| Behavior unchanged but for the renamed and removed markers | stop 5; M6-3's exit | The capture checker's counts equal M5's in QEMU; RC3's board counts are compared with RC2's |
| Additive model work only | D-6; stop 4 | No proved theorem changes under this plan |
| The limit and its counting rule | "Soft limits"; stop 6 | 4,000 added lines, checkpoints after M6-2 and M6-3 |

## 5. Review history and resolved findings

No independent review of these plans has been run (Q10; the session SOP
does not run one as standard practice). The design rests on read-only
findings listed in the plan's "Facts" section, each checked at
`cd9cfa5f`: the prelude's steps, the fixture extents in the ported
linker script, the accepted limits in `include/be/manifest.h`, the R2
backend's 4 KiB-only frames, the generator's role, the model's instance
mechanism, the port's file list, the sizes, and the dependents of the
markers and the layout.

**Open for human judgment:** the departures of section 3; Q1 (the
widened limits), Q3 (removing `kexec_fdt`), Q4 (the model instance), Q5
(the executor's scope), Q7 (20 board runs again), Q10 (a steering review).

## 6. Validation and retained evidence

Documentation only. At `b2c62d54`: the documentation source check
(`npm run docs:source-check`) passes; `git diff --check` is clean; every
link and anchor in both documents resolves. No `mvp/` check ran because
no `mvp/` file changed.

## 7. Recommended human review sequence

1. S3-B.1 and S3-B.2 (why first; M6's goal and exit), then D18 and the
   superseded lines.
2. The M6 plan's "Facts" (what the prelude does today and what the MVP
   never uses), then D-1 to D-4.
3. D-5 (the seams) and D-6 (the model) against the limit.
4. The stop conditions and Q1 to Q11.

```sh
git worktree add --detach /tmp/be-m6-plan-review b2c62d54f21c3cabdad3fefcc562499ace601089
cd /tmp/be-m6-plan-review
git --no-pager show --stat f8b77ac9 b2c62d54
git --no-pager diff cd9cfa5f f8b77ac9 -- planning/mvp-plan.md
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decisions are
in the [decision record](#decision-record), not in these boxes.

- [ ] S3-B records the direction you gave (RC3 before release-path steps
      2 to 7) and supersedes only the three lines it names.
- [ ] The M6 design retires the debt without widening the MVP's scope
      (no new guest behavior, no claim change, extents unchanged).
- [ ] The departures (D18's timing; `kexec_fdt` removed; the markers
      replaced; the seams included) are acceptable.
- [ ] Q1 to Q11's defaults stand, or your answers are given.
- [ ] Successor work stays excluded: release-path steps 2 to 7, any merge
      or push, any accepted-byte change, any kexec use.
- [ ] Decision 1: accept exact commit `f8b77ac9` as Plan revision S3-B;
      request revisions; or defer.
- [ ] Decision 2: accept exact commit `b2c62d54` as the M6 plan and
      authorize M6 implementation; request revisions; or defer.

## 9. After the decisions

- **Accept both and authorize:** the acceptance record names both SHAs,
  the date, and any answers to Q1 to Q11; the status documents are
  updated; M6-2 begins on `beryllium/mvp-m6` from the acceptance record,
  coding on `claude-opus-5.5` under this model's orchestration and
  review; the board campaign waits for your confirmation that the board
  is free and your presence at the install and the restore. No release
  step, merge, or push follows.
- **Accept S3-B only:** D18 is recorded; the M6 plan is revised or
  deferred as you direct.
- **Request revisions:** new commits and a new packet; neither SHA is
  treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commits `f8b77ac94fc6b5a80e68e6a972fa353b800d068b`
(Plan revision S3-B) and `b2c62d54f21c3cabdad3fefcc562499ace601089` (the
M6 plan) are responsible-human accepted as of 2026-10-30 (instruction
`accept f8b77ac9 and f8b77ac9`, the second decision confirmed by the
form answer `accept-and-authorize`; Q1 to Q11 at their defaults), and M6
implementation is authorized. They are on branch `beryllium/mvp-m6-plan`,
local and unpushed; release candidate 2 stays the latest accepted
candidate; the board is free and untouched by M6.

**Next:** M6-2 begins on `beryllium/mvp-m6` from this acceptance-record
commit (coding on `claude-opus-5.5`); the board campaign (M6-7) waits on
your confirmation that the board is free and your presence at the
install and the restore. The result is presented as release candidate 3
in one packet.

**Action required from you:** none now; later, your confirmation that
the board is free for M6-7, and your decision on release candidate 3.
