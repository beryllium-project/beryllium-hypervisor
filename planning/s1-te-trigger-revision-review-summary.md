<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# S1 and TE-trigger revision, RP-1 to RP-3: review summary

This packet supports three ordered responsible-human decisions on three
exact commits, produced under the accepted
[S1 and TE-trigger revision plan](s1-te-trigger-revision-plan.md) (exact
commit `07541c59`, accepted 2026-10-18, instruction `approve 480d 07541`).
It was presented as decision-neutral and not self-approving; the decision
record below holds the outcome.

## Decision record

The responsible human accepted all three exact commits on 2026-10-18 with
the single instruction `I accept RP-1 RP-2 RP-3`, given in reply to this
packet's request to decide on RP-1, then RP-2, then RP-3. The package names
map to the exact commits in section 1, and the order of the instruction
matches the order the packet asked for:

- **RP-1, accepted:** the revised S1 synthesis at
  `fd670dcd54ff4f2c66349d377be914698b9dda3b` (parent `ef50c005`). S1, the
  first step of the planned sequence, is complete; its classifications,
  including the specification role in row H59, are accepted planning input
  to S2 and S3. The first draft `0fbca0fd` stays superseded and unaccepted.
- **RP-2, accepted:** Model 0.1 plan revision M01-A at
  `95ef0f6c0fc1fe457e93b7d34b48cde5a411e8ab` (parent RP-1). The revised
  "TE trigger" section is the governing text, recorded against the Model
  0.1 accepted on 2026-07-22 as a revision; the Rocq model under `model/`
  is unchanged.
- **RP-3, accepted:** the revised S2 definition at
  `1ac7080f3375dfbfb8358706db767a8a89678a78` (parent RP-2). S2's seven-part
  scope stands; S2 itself is not started and needs its own authorization.

Acceptance selects no runtime mechanism or specification language form,
authorizes no S2 or S3 work, changes no accepted R0-R7 or B0-B7 target, and
pushes nothing. Sections 1 to 9 are the packet as presented, apart from the
outcome rows in section 1, a note above the section 8 checklist, and the
closing lines of section 9. Each accepted document carries its own decision
record or acceptance note. The packet commit `1d996e61` and this
acceptance-record follow-up are decision support, not package content.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review targets | RP-1: `fd670dcd54ff4f2c66349d377be914698b9dda3b` (tree `72a0f7e3c122000a503a5ea6f070b9be4c3c9ab7`), parent `ef50c005882f1a3698442943158ca3435ee3a1e9`, the acceptance record of the review and plan: the revised S1 synthesis. RP-2: `95ef0f6c0fc1fe457e93b7d34b48cde5a411e8ab` (tree `74a3623dccbfaf31ceb283312881a1c0438b4a5d`), parent RP-1: Model 0.1 plan revision M01-A. RP-3: `1ac7080f3375dfbfb8358706db767a8a89678a78` (tree `0cc6b60fd47a610983b790e2cd44de9caf85e9b5`), parent RP-2: the revised S2 scope statement |
| Current status | All three documentation-only; the fast source checks pass at each. Recorded outcome: all three accepted on 2026-10-18 (`I accept RP-1 RP-2 RP-3`) |
| Decisions requested | Ordered, as the plan's Q6 default: first accept, revise, or defer RP-1; then RP-2; then RP-3. RP-3 depends on RP-2's trigger wording and falls if RP-2 is revised; RP-1 and RP-2 are independent of each other in content, though RP-1 refers to M01-A by name. Recorded outcome: RP-1, RP-2, and RP-3 accepted, in that order |
| Successor status | S2 and S3 not started and not authorized; the first S1 draft `0fbca0fd` superseded and unaccepted; no other package of the plan remains, so the revision plan is complete |
| Publication status | Private repository; all three targets on local branch `beryllium/project-review-20261017`, which descends from the S1 branch tip `2256101c` and the development branch `56e36ae1`; `beryllium/s1-synthesis` was fast-forwarded to RP-1; nothing pushed; no tag, publication, or release |

As presented, the packet asked for RP-1, then RP-2, then RP-3 to be
accepted, revised, or deferred in that order; the
[decision record](#decision-record) above holds the outcome.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| RP-1: revised S1 synthesis | [`he-to-be-synthesis.md`](he-to-be-synthesis.md); a superseded notice in [`he-to-be-synthesis-review-summary.md`](he-to-be-synthesis-review-summary.md) | Replaces `0fbca0fd`: removes the E03 trigger argument, adds row H59 adopting a central, declarative policy in the Type Enforcement family as the specification, moves H02 to Adapt, rewords H08 as the runtime TE check, moves H10 to Defer, rewords H56, condenses fourteen practice rows (Q2), and updates purpose, non-claims, hand-offs, and counts (59 rows: 34 adopt, 15 adapt, 2 reject, 8 defer) | Planning input to S2 and S3 only; selects no runtime mechanism; Helium pin `1c9e526` unchanged (Q1) | Does H59 state the specification role you chose with `revise-adopt`, and does the rest of the document now follow from it without overreaching into S2? |
| RP-2: plan revision M01-A | [`architecture-model-0.1.md`](architecture-model-0.1.md), "Status and authorization boundary" note and the "TE trigger" section | Separates TE as specification (not trigger-gated; S2 produces it; enforcement derived) from TE as a runtime check (the accepted trigger wording and two-case condition, kept, described as a composition test) and states the dynamic case as the implementation plan's authority ceiling; quotes the accepted text, which governs until acceptance | Text only; the Rocq model under `model/`, the fixed instance, the obligations, the non-goals, and the software-capability trigger (Q4) are unchanged | Is the cut between specification and runtime check the right one, and does the retained two-case condition still mean what you want it to mean? |
| RP-3: revised S2 definition | [`roadmap.md`](roadmap.md) (executive position, S2 row, first-milestone sentence), [`implementation-plan.md`](implementation-plan.md) (section 2.16 item 4, milestones preamble, decision gate 2), [`project-orientation.md`](project-orientation.md), [`README.md`](README.md) (remaining decision gates), [`glossary.md`](glossary.md) | Defines S2 as one document with seven parts: objects/invariants/threat model/TCB; the policy specification; its analyses; its relation to the canonical manifest; the two triggers under M01-A; the dynamic authority ceiling; and any Model 0.2 changes. The language form is S2's choice (Q5) | Changes S2's definition, not its content; S2 stays unauthorized; each place is marked RP-3, proposed | Is this the scope you want S2 to have, and is leaving the specification language form to S2 acceptable? |

Exact changed-file inventory:

```text
# git diff --name-status ef50c005 fd670dcd   (RP-1)
M	planning/he-to-be-synthesis-review-summary.md
M	planning/he-to-be-synthesis.md
# git diff --name-status fd670dcd 95ef0f6c   (RP-2)
M	planning/architecture-model-0.1.md
# git diff --name-status 95ef0f6c 1ac7080f   (RP-3)
M	planning/README.md
M	planning/glossary.md
M	planning/implementation-plan.md
M	planning/project-orientation.md
M	planning/roadmap.md
```

`git diff --stat ef50c005 1ac7080f -- model/` is empty: no Rocq, C, test,
or fixture under `model/` changed.

Branch placement. The plan bases RP-1 on the S1 branch and RP-2 and RP-3 on
the development branch. All three commits are on
`beryllium/project-review-20261017`, which descends from the S1 branch tip
`2256101c` and from the development branch at `56e36ae1`; the S1 branch
`beryllium/s1-synthesis` was fast-forwarded to RP-1, so RP-1 is its tip. The
files RP-2 and RP-3 edit were unchanged between `56e36ae1` and their
parents apart from the status text added by the S1 and review packets, so
each commit's content base is the development branch's. Merging any of
these into the development branch, or pushing, needs separate direction.

## 3. Claim boundary

**The commits support saying:** RP-1 is a revised classification of Helium's
lessons against the B0-B7 records, with one recommendation about the role
of a declarative policy, cited to the implementation plan, the
capability-policy research, and Helium's documents at the pin. RP-2 is a
proposed text revision of one section of Model 0.1 and a status note. RP-3
is a proposed definition of a future document. Each is documentation that
a responsible human may accept as planning input.

**Trusted or assumed:**

- The accepted records (R0-R7, B0-B7, the project review, the revision
  plan) describe their own results correctly; nothing was re-run.
- Helium's documents at `1c9e526` say what the revised S1 quotes; the quote
  in H59 was checked against `docs/faq.md` at that commit with Git.
- The plan's Q1 to Q6 defaults apply, as its decision record states; none
  was answered otherwise.
- The owner session ran on `claude-fable-5.1` at the responsible human's
  direction for this session. No research agent ran for RP-1 to RP-3; the
  owner edited directly from the accepted plan's change list.

**Unavailable or not run:** no execution of any kind: no test, build,
emulation, proof, or board run; no generated HTML, `npm run docs:build`,
`./be docs-check`, Chromium render, or flagless `node docs/check-links.mjs`,
which needs the untracked generated tree.

**Not implemented:** S2 content of any kind, including any policy language,
analysis, or manifest relation; any change to Model 0.1's Rocq model, Model
0.2, or any accepted R0-R7 or B0-B7 byte; any runtime mechanism selection;
any change to `.github/copilot-instructions.md`, `HANDOFF.md`, or the review
packet's status rows, which this packet's own commit carries.

## 4. Load-bearing properties

| Property | Where stated | Evidence |
| --- | --- | --- |
| RP-1 selects no runtime mechanism and authorizes nothing | S1 "Purpose and boundary", "Non-claims", status record `s1_runtime_mechanism_selected=none` | Reading; H59's hand-off routes production to S2 |
| RP-1 removed the E03 trigger argument everywhere the plan names | S1 findings bullet 2, H02, H08, H55, S2 hand-off item 1 | `grep -n 'does not show' planning/he-to-be-synthesis.md` matches only the status paragraph that describes the removal |
| RP-1's counts are consistent | S1 "Summary" and status record | 59 `H` rows, no duplicate IDs (`grep -cE '^\| H[0-9]{2} '`); 34 + 15 + 2 + 8 = 59; the Summary row lists agree with the tables |
| RP-2 changes Model 0.1's text only | M01-A note; plan stop condition 1 | `git diff --stat fd670dcd 95ef0f6c` touches one file; `model/` unchanged across all three commits |
| RP-2 keeps the accepted trigger wording and two-case condition | "TE as a runtime check" and the quoted accepted text | Reading: the retained sentences match the quotation, which matches `git show 2256101c:planning/architecture-model-0.1.md` L266-L282 |
| RP-3 defines S2 without starting it | Every RP-3 location says "proposed and pending acceptance" and "S2 is not started or authorized"; plan stop condition 3 | Reading; no new S2 document exists |
| No package selects a policy language, runtime mechanism, or protected service | Plan stop condition 2 | RP-2 and RP-3 leave the language form to S2 (Q5); protected-service selection stays in "an accepted S2 or S3 scope" |

## 5. Review history and resolved findings

1. **Dangling reference avoided.** The superseded notice added to the old
   S1 packet in RP-1 names this packet by file name in plain text, because
   this packet did not yet exist at RP-1; this packet's commit turns the
   name into a link. The source checker passed at RP-1 with the plain
   text.
2. **Branch placement** differs in form from the plan's "on the S1 branch"
   and "the development branch" wording, as section 2 explains; the S1
   branch was fast-forwarded so that RP-1 is its tip. If you prefer RP-2
   and RP-3 on the development branch itself, say so and they will be
   cherry-picked there under your direction; their content does not change.
3. **Ordering of RP-3 against RP-2's acceptance.** The plan says RP-3 is
   based on the development branch "after RP-2 is accepted" and also that
   one packet presents all three targets as ordered decisions (Q6). RP-3
   was drafted after RP-2's commit, so it depends on M01-A's wording as the
   plan requires; its acceptance is conditioned on RP-2's in the order
   above. If you want RP-3 held until RP-2 is accepted separately, defer
   RP-3.
4. **Not resolved, for your judgment:** the wording of H59 and of M01-A's
   three cases, and S2's seven-part scope. No stop condition fired.

No research agent, separate scope review, or deep security review ran for
these packages.

## 6. Validation and retained evidence

These ran on 2026-10-18 on the working tree immediately before each commit;
each commit records exactly that content, and the tree was clean after each.
They did not run in a fresh checkout.

| Command | RP-1 | RP-2 | RP-3 | Covers |
| --- | --- | --- | --- | --- |
| `git diff --check` | pass | pass | pass | whitespace in tracked changes |
| `grep -nP '[ \t]+$'`, `grep -nP '[^\x00-\x7F]'`, and a `grep` for absolute home and temporary directory prefixes on the changed files | no matches | no matches | no matches | whitespace, ASCII, private locators |
| `node docs/check-links.mjs --tasking-fence-regression` | pass, 8 cases | pass, 8 cases | pass, 8 cases | the owner tasking section's regression cases |
| `node docs/check-links.mjs --tasking-contract` | pass | pass | pass | the owner tasking contract |
| `node scripts/check-doc-sources.mjs --self-test` | pass | pass | pass | the checker's self-tests |
| `node scripts/check-doc-sources.mjs` | pass: `site_markdown=116`, `configured_routes=272`, `rendered_references=1219` | pass: `rendered_references=1223` | pass: `rendered_references=1231` | links, anchors, routes, private locators |
| `umask 0022 && npm run docs:source-check` | pass: `network_events=0`, `generated_tree_changes=0`, `adversarial_cases=34` | same | same | the source gate under isolation |

The Helium quotation in H59 was checked with
`git -C ../helium-te-poc show 1c9e526:docs/faq.md` (lines 74-78). No report,
ledger, or hash is produced by documentation-only packages; the commits are
the artifacts.

## 7. Recommended review sequence

Read-only commands, from the Beryllium checkout:

```sh
git show --stat fd670dcd54ff4f2c66349d377be914698b9dda3b
git show --stat 95ef0f6c0fc1fe457e93b7d34b48cde5a411e8ab
git show --stat 1ac7080f3375dfbfb8358706db767a8a89678a78
git diff --name-status ef50c005882f1a3698442943158ca3435ee3a1e9 1ac7080f3375dfbfb8358706db767a8a89678a78
git diff --stat ef50c005882f1a3698442943158ca3435ee3a1e9 1ac7080f3375dfbfb8358706db767a8a89678a78 -- model/
git show fd670dcd54ff4f2c66349d377be914698b9dda3b -- planning/he-to-be-synthesis.md
git show 95ef0f6c0fc1fe457e93b7d34b48cde5a411e8ab
git show 1ac7080f3375dfbfb8358706db767a8a89678a78
```

1. **RP-1, "Status" and row H59:** the specification role and its basis,
   against `planning/implementation-plan.md` L401, L416-L417, L734, L740,
   L890-L901, L931-L940 and `planning/capability-policy-architecture.md`
   L36-L44, L240.
2. **RP-1, rows H02, H08, H10, H55, H56, the findings, and the S2
   hand-off:** that the E03 argument is gone and nothing else moved.
3. **RP-2, the "TE trigger" section:** the three cases and the quoted
   accepted text; then the status note.
4. **RP-3, the roadmap S2 row and implementation plan item 4:** the seven
   parts; then the shorter forms in the other three files.
5. **This packet's section 3:** the non-claims.

To re-run the source checks on an exact commit, use a detached worktree in
the workspace's `worktrees/` container, then `npm ci` and
`umask 0022 && npm run docs:source-check` inside it:

```sh
git worktree add --detach ../worktrees/beryllium-hypervisor/review-1ac7080f 1ac7080f3375dfbfb8358706db767a8a89678a78
```

## 8. Human decision checklist

As presented, the packet asked the human to decide on RP-1, RP-2, and RP-3
in order. The [decision record](#decision-record) above holds all three
decisions; the checklist is retained as presented.

- [ ] RP-1 follows the accepted plan's change list and nothing else.
- [ ] H59 states the `revise-adopt` direction correctly: a central,
      declarative policy in the Type Enforcement family as the
      specification, with enforcement derived from it.
- [ ] RP-1 selects no runtime mechanism and transfers no Helium result.
- [ ] RP-2's cut between TE as specification and TE as a runtime check is
      the right one, and the retained two-case condition reads as a
      composition test.
- [ ] RP-2 leaves the Rocq model, the fixed instance, and the capability
      trigger untouched.
- [ ] RP-3's seven-part S2 scope is the scope you want, and leaving the
      specification language form to S2 is acceptable.
- [ ] The branch placement in section 2 and the RP-3 ordering in section 5
      are acceptable.
- [ ] S2, S3, and any push stay excluded until separately directed.
- [ ] Decision on RP-1: accept `fd670dcd`, request revisions, or defer.
- [ ] Decision on RP-2: accept `95ef0f6c`, request revisions, or defer.
- [ ] Decision on RP-3: accept `1ac7080f`, request revisions, or defer.

## 9. After the decisions

- **Accept RP-1:** on your instruction, a follow-up records the acceptance
  of exactly `fd670dcd54ff4f2c66349d377be914698b9dda3b` with the
  instruction and date, S1 becomes the accepted planning input to S2 and
  S3, and the status pages are updated. It does not authorize S2.
- **Accept RP-2:** a follow-up records the acceptance of exactly
  `95ef0f6c0fc1fe457e93b7d34b48cde5a411e8ab`; M01-A becomes the governing
  TE-trigger text, recorded against the accepted Model 0.1 as a revision,
  with the Rocq model unchanged.
- **Accept RP-3:** a follow-up records the acceptance of exactly
  `1ac7080f3375dfbfb8358706db767a8a89678a78`; the revised S2 definition
  stands, and S2 still needs its own authorization to start.
- **Request revisions (any):** a new commit and a new packet follow; the
  old SHA is not treated as accepted. A revision to RP-2 reopens RP-3.
- **Defer (any):** the current status stays, and no dependent work starts.
  The first S1 draft `0fbca0fd` stays superseded and unaccepted in every
  case.

**Status:** exact commits `fd670dcd` (RP-1, the revised S1), `95ef0f6c`
(RP-2, Model 0.1 plan revision M01-A), and `1ac7080f` (RP-3, the revised S2
definition) are responsible-human accepted as of 2026-10-18, on local branch
`beryllium/project-review-20261017`; nothing is pushed. S1 is complete, and
the revision plan has no remaining package.

**Next:** S2 (security model v1, under its revised definition) needs your
authorization and its own plan or decision before it starts; merging this
branch into the development branch and any push need your separate
direction.

**Action required from you:** none for RP-1 to RP-3.
