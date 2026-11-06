<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# S1 Helium-to-Beryllium synthesis: review summary

> **Superseded (2026-10-18).** This packet presented the first S1 draft at
> exact commit `0fbca0fd`. On 2026-10-17 the responsible human found that
> the draft treats TE only as a runtime denial, and the accepted
> [project review](project-review-2026-10-17.md) (`480dab72`) and
> [revision plan](s1-te-trigger-revision-plan.md) (`07541c59`) followed.
> Work package RP-1 of that plan replaces `0fbca0fd`, which is superseded
> and unaccepted, with a revised `he-to-be-synthesis.md`; the revised S1 is
> presented in the
> [revision review summary](s1-te-trigger-revision-review-summary.md), not
> here. This packet is retained as history and asks for no decision.

This packet supports a responsible-human decision on one exact commit. It
records no decision and is not self-approving.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef` (tree `6e7734589a4af05c03771733763a6084237b9098`), parent `56e36ae11e47bb08416a44c5647aecd304fd4902`, the development-branch tip |
| Current status | Documentation complete; the fast source checks pass; not reviewed or accepted by the responsible human |
| Decision requested | Accept the exact commit, request revisions, or defer |
| Successor status | S2 and S3 not started and not authorized |
| Publication status | Private repository; the target is on local branch `beryllium/s1-synthesis`, unpushed; no tag, publication, or release |

S1 was authorized on 2026-10-16 by the instruction `authorize S1, proceed`.
Please review the exact target and either accept it, request revisions, or
defer.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| S1 synthesis | [`he-to-be-synthesis.md`](he-to-be-synthesis.md) | Classifies 58 Helium elements against the B0-B7 evidence (34 adopt, 14 adapt, 3 reject, 7 defer), with hand-offs to S2 and S3 | Planning input only; selects nothing and transfers no Helium result | Do the classifications, especially the adapt, reject, and defer rows, follow from the cited evidence? |
| Navigation | `planning/.vitepress/config.mts` | Three entries that list the page in the planning site | Site configuration only | None beyond placement |

Exact changed-file inventory, from
`git diff --name-status 56e36ae1 0fbca0fd`:

```text
M	planning/.vitepress/config.mts
A	planning/he-to-be-synthesis.md
```

## 3. Claim boundary

**The exact commit supports saying:** S1 proposes a classification of
Helium's lessons, judged against the accepted B0-B7 records and Beryllium's
recorded decisions, read at Beryllium base `56e36ae1` and Helium commit
`1c9e526`. Each row cites its Helium source, its K3 evidence (E01-E12), or a
recorded decision.

**Trusted or assumed:**

- The accepted B0-B7 records describe their runs correctly; S1 ran nothing.
- Helium's figures (for example 18 CBMC checks, 152 claims, 19,419
  properties, and the line counts) are as Helium's own documents record them.
  S1 did not rerun Helium's tests or CBMC.
- Three read-only research agents extracted the Helium lessons, the B-series
  evidence, and the recorded decisions. The owner checked the quoted Helium
  passages verbatim at the pin and the Helium lineage with Git; other
  extracted figures were not independently re-derived.

**Unavailable or not run:** no test, emulation, proof, or board run; no Helium
gate, `./he check`, or CBMC rerun; no generated HTML, `npm run docs:build`,
`./be docs-check`, Chromium render, or full `node docs/check-links.mjs`.

**Not implemented:** anything outside documentation; no S2 or S3 content
beyond hand-off lists; no change to any other planning document.

## 4. Load-bearing properties

| Property | Where stated | Evidence |
| --- | --- | --- |
| No Helium result transfers, and nothing is selected | S1 "Purpose and boundary" and "Non-claims" | Reading the document; no other planning document changed (section 2 inventory) |
| The Helium pin is exact and read as evidence only | S1 "Helium pin" and Q1 | `merge-base` of `f928aac5` and `1c9e526` is `1ab289c`; `1ab289c..1c9e526` is 60 commits; `f928aac5` differs from `1ab289c` only in `HANDOFF.md`; the name-status counts from `f928aac5` to `1c9e526` are 214 added, 86 modified, 5 renamed, and 21 deleted, all deleted files being generated HTML assets |
| The summary counts match the rows | S1 "Summary" | A script recount found 58 rows: 34 adopt, 14 adapt, 3 reject, 7 defer, with the same ID lists |
| Every Helium quotation is verbatim at the pin | the quoted passages in H07, H10, H38, H40, H41, and H43 | Each phrase found verbatim in `docs/*.md` of the `1c9e526` tree, with whitespace normalized |
| The K3 evidence is cited, not re-claimed | S1 "K3 bring-up evidence" | Each E-row links its record; the wording keeps "diagnostic bring-up evidence for one board" |

## 5. Review history and resolved findings

1. **Helium pin premise (corrected before the target).** Before S1 was
   authorized, the owner described `f928aac5` as the approved H7 release
   plus two documentation commits. Research found that `f928aac5` and
   `1c9e526` are separate lines from base `1ab289c`, and that `1c9e526` is
   the content superset. S1 therefore reads `1c9e526`, as evidence only, and
   Q1 records the alternative.
2. **First Helium inventory overstated some lessons (resolved).** An
   inventory taken at `f928aac5` described its `htval` check as exact and its
   validators as complete. At `1c9e526`, Helium records that the shift-based
   check would accept a high-bit alias, and that review found two validator
   defects (HA-02, HA-03). S1 cites the release-line state (H16, H26).
3. **Two wording corrections before the commit.** H07's attribution became
   "Helium records", since the quoted passage is in
   `docs/fv-pathfinder-lessons.md` rather than only in the ledger. E08 and
   H55 now state that B7 re-walks its roots and that its pair check refuses
   any shared page, which the B7 record confirms.
4. **Open, for your judgment:** the observations in S1's "Observations
   outside S1's scope", which are a stale milestone number, a read-write
   gate mount, finding S6, the comparison's stale figures, and Helium's
   inconsistent release documents, and Q1 and Q2.

No different-model, separate scope, or deep security review was run, per the
2026-10-06 process SOP.

## 6. Validation and retained evidence

These ran on 2026-10-16 on the working tree immediately before the target
commit; the commit records exactly that content, with no edits in between,
and the tree was clean afterwards. They did not run in a fresh checkout of
the target.

| Command | Result | Covers |
| --- | --- | --- |
| `git diff --check` | pass | whitespace in tracked changes |
| `grep -nP '[ \t]+$'` and `grep -nP '[^\x00-\x7F]'` on the new page | no matches | whitespace and ASCII in the new, then untracked, file |
| `node docs/check-links.mjs --tasking-fence-regression` | pass, 8 cases | the owner tasking section's regression cases |
| `node docs/check-links.mjs --tasking-contract` | pass | the owner tasking contract in `.github/copilot-instructions.md` |
| `node scripts/check-doc-sources.mjs --self-test` | pass | the source checker's self-tests |
| `node scripts/check-doc-sources.mjs` | pass: `site_markdown=112`, `configured_routes=260`, `rendered_references=1115` | links, anchors, navigation routes, and private locators across the planning site |
| `umask 0022 && npm run docs:source-check` | pass: `network_events=0`, `generated_tree_changes=0`, `adversarial_cases=34` | the source gate under isolation |
| An `awk` recount of the classification rows, and a table cell-count check | 58 rows, 34/14/3/7; every row well-formed | the summary counts |

No retained report or evidence bundle applies; the document is its own
artifact.

## 7. Recommended review sequence

Read-only commands, from the Beryllium checkout:

```sh
git show --stat 0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef
git diff --name-status 56e36ae11e47bb08416a44c5647aecd304fd4902 0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef
git show 0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef:planning/he-to-be-synthesis.md
git -C ../helium-te-poc merge-base f928aac5979b6166f3f68a76a9acf1fc916161d8 1c9e52693abe0072ac9b8ce4e0a3ecb5f8bb9489
git -C ../helium-te-poc rev-list --count 1ab289c..1c9e52693abe0072ac9b8ce4e0a3ecb5f8bb9489
git -C ../helium-te-poc diff --name-status f928aac5979b6166f3f68a76a9acf1fc916161d8 1c9e52693abe0072ac9b8ce4e0a3ecb5f8bb9489 | cut -f1 | sort | uniq -c
git -C ../helium-te-poc show 1c9e52693abe0072ac9b8ce4e0a3ecb5f8bb9489:docs/fv-pathfinder-lessons.md
```

1. **Boundary and pin:** S1 "Status", "Purpose and boundary", "Inputs",
   "Helium pin", and Q1.
2. **Evidence:** the E01-E12 table against the linked B0-B7 records.
3. **Classifications:** the 24 adapt, reject, and defer rows first, then
   H02 and H55, which carry the reasoning about the TE PoC scenario.
4. **Hand-offs:** the S2 and S3 lists and the table of the comparison's open
   decisions.
5. **Observations and non-claims.**

To re-run the source checks on the exact commit, use a detached worktree in
the workspace's `worktrees/` container, then run `npm ci` and
`umask 0022 && npm run docs:source-check` in it:

```sh
git worktree add --detach ../worktrees/beryllium-hypervisor/s1-review-0fbca0fd 0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef
```

## 8. Human decision checklist

- [ ] The scope matches S1 as planned: documentation only, classifying
      Helium lessons against the B0-B7 evidence, with hand-offs to S2 and S3.
- [ ] Q1: reading `1c9e526` as evidence only is acceptable, or `f928aac5`
      should be used instead.
- [ ] The classifications follow from the cited evidence and recorded
      decisions, especially H02, H05, H06, H12, H16, H17, and H55.
- [ ] The rejects (H10, H24, H46) and defers (H07-H09, H38, H41, H57, H58)
      are acceptable.
- [ ] The claims match the evidence, and no Helium result is transferred.
- [ ] The validation covers what a documentation-only target needs.
- [ ] Q2: leaving the observations for separate direction is acceptable.
- [ ] S2 and S3 stay excluded until separately directed.
- [ ] Decision: accept `0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef`, request
      revisions, or defer.

## 9. After the decision

- **Accept:** on your explicit instruction, a follow-up records the
  acceptance of exactly `0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef`, with the
  instruction and date, and updates the status pages. S2 still needs its own
  direction; nothing is pushed unless you say so.
- **Request revisions:** a new commit and a new review packet follow; this
  SHA is not treated as accepted.
- **Defer:** the current status stays, and no dependent work starts.

**Status:** the S1 synthesis is complete at exact commit
`0fbca0fdc7b9ecca2aaf6635bb04a3335bca72ef` on local branch
`beryllium/s1-synthesis`; it is not reviewed, accepted, or pushed.

**Next:** your decision on that exact commit.

**Action required from you:** accept `0fbca0fd`, request revisions, or
defer.
