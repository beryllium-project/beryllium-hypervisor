<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Project review and revision plan: review summary

This packet supports two ordered responsible-human decisions on two exact
commits. It was presented as decision-neutral and not self-approving; the
decision record below holds the outcome.

## Decision record

The responsible human accepted both exact commits on 2026-10-18 with the
single instruction `approve 480d 07541`, given in reply to this packet's
request to decide first on A and then on B. The abbreviations were checked
to resolve uniquely:

- **A, accepted:** the project review at
  `480dab72de7a74f8b84c64c2fefee8190cb87b70` (parent `91d2c108`). Its first
  candidate `65fc52e0` is superseded and unaccepted. Acceptance covers the
  review text at that commit; the findings stand as the record, and the
  options remain options.
- **B, accepted:** the revision plan at
  `07541c59426865ce8b1eef3c409913923cd5e64b` (parent `65fc52e0`). Acceptance
  authorizes the three documentation work packages RP-1, RP-2, and RP-3,
  each ending in its own exact commit, presented as ordered decisions in one
  packet, with the Q1 to Q6 defaults. It authorizes no code, no S2 or S3
  content, no change to any accepted target or to Model 0.1's Rocq model,
  and no push.

Sections 1 to 9 are the packet as presented, apart from the outcome rows in
section 1, a note above the section 8 checklist, and the closing lines of
section 9. Each accepted document carries its own decision record. The
packet commits `91d2c108` and `5c14180c` and this acceptance-record
follow-up are decision support, not review or plan content.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review targets | A: `480dab72de7a74f8b84c64c2fefee8190cb87b70` (tree `f21d5551aada452a7e0d236f2c0c5f0629efa3e4`), parent `91d2c108c0326a77619c91b88a4e1c966aeb06bc`: the project review as corrected on 2026-10-18 after a second research run; it supersedes the first candidate `65fc52e0b06fc60691669f75d44a1cc9356ac4c0`, which is unaccepted. B: `07541c59426865ce8b1eef3c409913923cd5e64b` (tree `40003f53bd91bb9f02167148c9db904fb230a9fd`), parent `65fc52e0`: the revision plan, unchanged by the second run |
| Current status | Both documentation-only; the fast source checks pass at each. Recorded outcome: both accepted on 2026-10-18 (`approve 480d 07541`) |
| Decisions requested | Ordered: first accept, revise, or defer A; then, if A is accepted, accept, revise, or defer B. B rests on A's findings F-01 to F-04, whose direction and severity the second run left unchanged. Recorded outcome: A accepted, then B accepted |
| Successor status | S2 and S3 not started and not authorized; the S1 draft `0fbca0fd` stays proposed and unaccepted until RP-1 replaces it; the revision plan's packages RP-1 to RP-3 are authorized by B's acceptance and not yet started |
| Publication status | Private repository; both targets on local branch `beryllium/project-review-20261017`, from the S1 branch tip `2256101c`, unpushed; no tag, publication, or release |

The responsible human requested the review on 2026-10-17 and chose
`revise-adopt` for S1's direction the same day. On 2026-10-18 the human
directed a second run of the research agents on `claude-fable-5.1`, with the
model pin overridden for this session; A is the result. Please review A,
then B.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| Project review (A) | [`project-review-2026-10-17.md`](project-review-2026-10-17.md) | Reviews the S1 draft and its critique, then the project against its founding goals along five angles; 18 findings with citations and 8 options | Decision-neutral; accepts and selects nothing | Do the three high findings (F-01 to F-03) hold: that the policy-specification layer was never scheduled, that the TE trigger displaced it, and that S1 inherited the error? |
| Revision plan (B) | [`s1-te-trigger-revision-plan.md`](s1-te-trigger-revision-plan.md) | Three documentation work packages: revise S1 (RP-1), rewrite Model 0.1's TE-trigger text (RP-2), revise the S2 scope statement (RP-3) | Proposed only; if accepted, authorizes documentation work ending in exact commits, nothing else | Is "a central, declarative policy in the Type Enforcement family as the specification, with enforcement derived" the right statement of your direction, and is RP-2's split between specification and runtime check the right cut? |
| Navigation | `planning/.vitepress/config.mts` | Lists both pages in the three navigation lists | Site configuration only | None beyond placement |

Exact changed-file inventory:

```text
# git diff --name-status 2256101c 65fc52e0   (first candidate of A)
M	planning/.vitepress/config.mts
A	planning/project-review-2026-10-17.md
# git diff --name-status 65fc52e0 07541c59   (B)
M	planning/.vitepress/config.mts
A	planning/s1-te-trigger-revision-plan.md
# git diff --name-status 91d2c108 480dab72   (A, the corrections)
M	planning/project-review-2026-10-17.md
```

The branch order is `2256101c` -> `65fc52e0` -> `07541c59` -> `91d2c108`
(the first packet commit) -> `480dab72` (A) -> this packet's commit. B
therefore precedes A in history; its content does not depend on which
candidate of A is accepted, and it changed in neither.

## 3. Claim boundary

**The commits support saying:** A records findings about the repository's
own documents and Git history as they stand at `2256101c`, each cited to a
file and line, plus measurements made with `git`, `ls`, and `wc`. B proposes
bounded documentation work that would follow from A's findings and the
responsible human's `revise-adopt` direction.

**Trusted or assumed:**

- The accepted records describe their own results correctly; the review
  ran no test, build, emulation, proof, or board run.
- Helium's figures (CBMC checks, claims, properties, line counts) are as
  Helium's documents at `1c9e526` record them; nothing was rerun.
- Four read-only research agents extracted the goals ledger, the decision
  chain, the B-series progress, and the assurance and debt audit: first on
  `claude-opus-5.5` on 2026-10-17, then again on `claude-fable-5.1` on
  2026-10-18 at the responsible human's direction, each second-run agent
  forming its own reading before comparing it with the review. The owner
  verified every quotation used in A against its source with `grep`,
  confirmed the Helium lineage with Git, and re-measured every figure the
  second run disputed with Git and `wc`; figures neither quoted in A nor
  disputed were not independently re-derived.
- The owner session ran on `claude-fable-5.1` at the responsible human's
  direction. This is a different-model review of the kind the 2026-10-06 SOP
  avoids as standard practice; it was human-directed. For the second run,
  the governance hook's required subagent model was edited from
  `claude-opus-5.5` to `claude-fable-5.1` with the human's consent and
  restored from a backup when the run ended; the hook is outside the
  repository, and no other rule changed.

**Unavailable or not run:** no execution of any kind; no generated HTML,
`npm run docs:build`, `./be docs-check`, Chromium render, or full
`node docs/check-links.mjs`.

**Not implemented:** nothing beyond the two documents and navigation. No
other planning document changed in A or B. The status pages changed only in
this packet's own commits, which follow B and A respectively.

## 4. Load-bearing properties

| Property | Where stated | Evidence |
| --- | --- | --- |
| A accepts and selects nothing; B authorizes nothing until accepted, and then only documentation | A "Status" and "Non-claims"; B "Status" and "Non-claims" | Reading; the file inventories in section 2 |
| Every quotation in A is verbatim at `2256101c` | A, throughout | Each quoted phrase was found with `grep -F` in its cited file; one line number (B6 plan L447) was corrected to L448 before the first commit; the second run verified every first-run line citation and found one misattributed quotation, now cited to its file |
| A's counts are consistent | A "Findings" and "Status record" | 18 findings: F-01 to F-03 high, F-04 to F-13 and F-15 medium, F-14 and F-16 to F-18 low; 8 options; 8 second-run corrections |
| The measurements are reproducible | A, Part 6 | Commands: `ls planning/*.md`, `wc -l -c`, `git log --format=%H -- planning/HANDOFF.md`, `git rev-list --count`, `git ls-files`; all at `2256101c`. The second run could not reproduce three first-run figures (`tests/` lines, `bringup/` lines, commits since 2026-10-06); A now carries the re-measured values with their exclusions and date method stated |
| B changes no accepted target | B "RP-2" and "Non-claims" | RP-2 is text-only in the TE-trigger section; the Rocq model is untouched; stop condition 1 |
| A is self-consistent without B | A refers to B by file name in plain text, not by link | `node scripts/check-doc-sources.mjs` passes at A's first candidate alone (114 pages, 266 routes), at B (115 pages, 269 routes), and at A (116 pages, 272 routes, with this packet's page present) |

## 5. Review history and resolved findings

1. **Governance hook versus the subagent choice (2026-10-17).** The
   responsible human chose `claude-fable-5.1` for the research agents. The
   project's hook (`PMD-20261006-001`) denied every non-pinned model for
   `task` calls. The owner did not work around it: the agents ran on
   `claude-opus-5.5`, the human was told, and A's model note records it.
2. **Dangling references before the first commit of A.** The review linked
   to the not yet existing revision plan; the source checker reported three
   missing targets. The links were made plain-text file names so that A
   stands on its own; B links back to A.
3. **One citation corrected.** "All RAM is RWX" is at B6 plan L448, not
   L447; fixed before commit.
4. **Second run on `claude-fable-5.1` (2026-10-18).** The human directed
   `override pinning and use fable 5.1 for everything, re-run the research
   agents, apply changes if any`, and chose a temporary edit of the hook
   over disabling it. The hook's required model line was changed to
   `claude-fable-5.1`, the four agents ran against `91d2c108`, and the hook
   was restored from its backup, byte-identical, when they finished. The
   eight corrections and the added material are listed in A under "Second
   run (2026-10-18)" and in commit `480dab72`'s message. Three of the
   corrections are factual errors in the first candidate (the R7 cut-point
   names, two Part 6 line counts, and a quotation cited to the wrong file);
   the rest are overstatements made precise. No finding changed direction
   or severity; the second run also confirmed every first-run line citation.
   `65fc52e0` is superseded and unaccepted.
5. **Roadmap date inconsistency introduced by the first packet commit.**
   `91d2c108` set the roadmap's status date to 2026-10-17 while its
   "Current position" line and `roadmap_status_date` field still said
   2026-10-16. The second run noticed it; this packet's commit aligns the
   three to 2026-10-18.
6. **Not resolved, for your judgment:** the findings themselves, the options
   in A, and B's open questions Q1 to Q6. In particular, F-10 observes that
   the 2026-10-06 SOP's removal of independent review was not weighed
   against the founding "small enough to audit" requirement; this packet
   does not propose a resolution.

No separate scope review or deep security review was run. The second run is
a different-model re-read of the same inputs by read-only agents, not an
independent human review.

## 6. Validation and retained evidence

These ran on 2026-10-17 (first candidate of A, and B) and 2026-10-18 (A) on
the working tree immediately before each commit; each commit records exactly
that content, and the tree was clean after each. They did not run in a fresh
checkout.

| Command | Result at `65fc52e0` | Result at B | Result at A | Covers |
| --- | --- | --- | --- | --- |
| `git diff --check` | pass | pass | pass | whitespace in tracked changes |
| `grep -nP '[ \t]+$'`, `grep -nP '[^\x00-\x7F]'`, and a `grep` for absolute home and temporary directory prefixes on the changed file | no matches | no matches | no matches | whitespace, ASCII, private locators |
| `grep -n s1-te-trigger-revision-plan planning/.vitepress/config.mts` | no match (route held back) | three entries | three entries | no dangling route |
| `node docs/check-links.mjs --tasking-fence-regression` | pass, 8 cases | pass, 8 cases | pass, 8 cases | the owner tasking section's regression cases |
| `node docs/check-links.mjs --tasking-contract` | pass | pass | pass | the owner tasking contract |
| `node scripts/check-doc-sources.mjs --self-test` | pass | pass | pass | the checker's self-tests |
| `node scripts/check-doc-sources.mjs` | pass: `site_markdown=114`, `configured_routes=266`, `rendered_references=1167` | pass: `site_markdown=115`, `configured_routes=269`, `rendered_references=1175` | pass: `site_markdown=116`, `configured_routes=272`, `rendered_references=1200` | links, anchors, routes, private locators |
| `umask 0022 && npm run docs:source-check` | pass: `network_events=0`, `generated_tree_changes=0`, `adversarial_cases=34` | same | same | the source gate under isolation |

The eight research reports (four per run) and the owner's notes are retained
in the session workspace, not in the repository; A is the artifact.

## 7. Recommended review sequence

Read-only commands, from the Beryllium checkout:

```sh
git show --stat 480dab72de7a74f8b84c64c2fefee8190cb87b70
git show --stat 07541c59426865ce8b1eef3c409913923cd5e64b
git diff --name-status 2256101c5fb790f3569055479049288ff2235d36 480dab72de7a74f8b84c64c2fefee8190cb87b70
git show 480dab72de7a74f8b84c64c2fefee8190cb87b70:planning/project-review-2026-10-17.md
git show 480dab72de7a74f8b84c64c2fefee8190cb87b70 -- planning/project-review-2026-10-17.md
git show 07541c59426865ce8b1eef3c409913923cd5e64b:planning/s1-te-trigger-revision-plan.md
```

The fifth command shows only what the second run changed; the fourth shows
the whole review as it stands.

1. **A, "Second run (2026-10-18)":** the eight corrections, so you know what
   moved between the candidate you may have read and this one.
2. **A, Parts 1 and 2:** the S1 error and the decision chain; check the
   quoted founding statements against `planning/implementation-plan.md`
   L401, L416-L417, L734, L740, L844, L931-L940,
   `planning/architecture-model-0.2.md` L273-L274, and now
   `planning/pathfinder-evidence.md` L345, L351-L352.
3. **A, Findings:** the three high findings, then the medium ones you would
   want decided before S3.
4. **A, Parts 3 to 6:** progress, assurance, debt, and the measurements.
5. **A, Options:** which, if any, to direct.
6. **B:** the three packages, the stop conditions, and Q1 to Q6.

To re-run the source checks on an exact commit, use a detached worktree in
the workspace's `worktrees/` container, then `npm ci` and
`umask 0022 && npm run docs:source-check` inside it:

```sh
git worktree add --detach ../worktrees/beryllium-hypervisor/review-480dab72 480dab72de7a74f8b84c64c2fefee8190cb87b70
```

## 8. Human decision checklist

As presented, the packet asked the human to decide on A and then on B. The
[decision record](#decision-record) above holds both decisions; the
checklist is retained as presented.

- [ ] A's scope matches the request: the S1 draft and its critique, then the
      project against its founding goals, along the five chosen angles.
- [ ] A's three high findings hold against the cited sources.
- [ ] A's claims match its evidence, and it transfers no Helium result.
- [ ] A's measurements and stale-statement list are accurate enough to act
      on.
- [ ] The second run's corrections are acceptable, and the temporary hook
      edit, now reversed, needs no further action from you.
- [ ] B states the `revise-adopt` direction correctly.
- [ ] B's RP-2 cut between TE as specification and TE as runtime check is
      the right one, and leaving the Rocq model untouched is acceptable.
- [ ] B's RP-3 definition of S2 is the scope you want S2 to have.
- [ ] B's defaults for Q1 to Q6 are acceptable, or you answer them.
- [ ] S2, S3, RP-1 to RP-3, and any push stay excluded until separately
      directed.
- [ ] Decision on A: accept `480dab72`, request revisions, or defer.
- [ ] Decision on B: accept `07541c59`, request revisions, or defer.

## 9. After the decisions

- **Accept A:** on your instruction, a follow-up records the acceptance of
  exactly `480dab72de7a74f8b84c64c2fefee8190cb87b70` with the instruction
  and date, and updates the status pages. Accepting A does not accept B.
  The first candidate `65fc52e0` stays superseded and unaccepted.
- **Accept B:** on your instruction, a follow-up records the acceptance of
  exactly `07541c59426865ce8b1eef3c409913923cd5e64b`; RP-1 to RP-3 may then
  start, each ending in its own exact commit and packet. Nothing is pushed
  unless you say so.
- **Request revisions (either):** a new commit and a new packet follow;
  the old SHA is not treated as accepted.
- **Defer (either):** the current status stays, and no dependent work
  starts. The S1 draft `0fbca0fd` stays unaccepted in every case.

**Status:** exact commits `480dab72` (the project review; `65fc52e0`
superseded) and `07541c59` (the revision plan) are responsible-human
accepted as of 2026-10-18, on local branch
`beryllium/project-review-20261017`; nothing is pushed.

**Next:** RP-1, RP-2, and RP-3 proceed under the accepted plan, each ending
in its own exact commit, to be presented as three ordered decisions in one
packet. S2, S3, and any push wait for your separate direction.

**Action required from you:** none for A or B.
