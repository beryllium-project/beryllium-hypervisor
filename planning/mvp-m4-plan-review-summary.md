<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M4 plan review and acceptance record

This packet presents the bounded plan for M4, "Release candidate", the
last milestone of the accepted [MVP plan](mvp-plan.md), for the
responsible human's decision. The plan was directed on 2026-10-28 by the
instruction `then proceed with (1) and (2)`, given after the M3 result's
acceptance, where (2) was "directing the M4 plan (the release candidate)
as a proposal on a new branch from that tip". It was written by the
orchestrating session under the repository's model split. On the
responsible human's session SOP of 2026-10-28 (`ok, SOP for this session
is to have gpt-5.6-sol max long review planning steps`), the first
candidate `91f4a820` was reviewed read-only by `gpt-5.6-sol` (`max`,
`long_context`); its nine findings and their resolutions are in section
5, and the revised plan is the review target below. The first candidate
is superseded. It also records the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`0d02df725541e4e8f93b3fc3de002358827aa1da` (parent `95fc0123`, tree
`49bc2298`, on branch `beryllium/mvp-m4-plan` from `fb8accc9`) as the
M4 plan on 2026-10-28, and separately authorized M4 implementation. The
instruction, given in reply to this packet's request to accept, revise,
or defer that exact commit, was `accept 0d02df27, authorize M4`. The
written abbreviation `0d02df27` matches no object in the repository
(`git rev-parse --disambiguate=0d02df27` returns nothing); its first six
characters `0d02df` resolve uniquely to the proposed target
(`git rev-parse --disambiguate=0d02df` returns exactly
`0d02df725541e4e8f93b3fc3de002358827aa1da`), and that target is the
only commit this packet asked the human to decide on, so the
instruction is read as `accept 0d02df72` with two digits transposed,
as the M2 result's `acctp 898af` was read as `accept 898af`. Q1 to Q13
were not answered, so their defaults apply. The first candidate
`91f4a820` is superseded and was never accepted.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Sections 2 to 8 are the packet as presented, apart from a note above
  the section 8 checklist. Section 1's status rows and the closing lines
  of section 9 now show the outcome. The decision itself is recorded
  only here and in the plan's own decision record.
- **Decision support:** packet commits `95fc0123` and `6096a8ba` and
  this acceptance-record follow-up are decision support, not plan
  content.
- **Review:** the first candidate was reviewed by `gpt-5.6-sol` under
  the responsible human's session SOP, and its nine findings are
  incorporated in the accepted text (section 5); the accepted plan was
  not re-reviewed, each resolution having been written by the
  orchestrating session against the sources the reviewer cited.
- **Authorized** (`authorize M4`): work packages M4-1 to M4-6 under the
  accepted plan, on branch `beryllium/mvp-m4` from this
  acceptance-record commit, ending in one review packet for the
  release-candidate commit `R`. The board campaign (M4-5) waits on the
  responsible human's confirmation that the K3 is free and issues no
  board command before it; M4 waits there for as long as the human
  needs. The plan's defaults apply: the release surfaces under
  `mvp/docs/` (Q1); the 11-run campaign with the `anchor` byte
  comparison (Q2); the JSON-sourced ledger (Q3); the clean evidence from
  the pinned evaluators on a standalone checkout of `X` (Q4); no review
  of the result by another model unless the human directs one (Q5); the
  claim's wording as fixed (Q6); the disclosure's content (Q7); the
  guide's board section (Q8); Markdown only (Q9); the soft limits
  (Q10); the model split (Q11); "MVP 1.0 release candidate" and the
  exact commit, no tag or version file (Q12); the four surfaces as the
  phrasing checker's scope (Q13). Each of the plan's ten stop conditions
  returns M4 to the responsible human; a soft limit exceeded returns the
  limit for re-evaluation. The repository's model split and the
  session SOP apply.
- **Not authorized:** any release-path step after the first (the
  selection of what migrates, the clean public repository, a tag, the
  gates' re-run there, publication, the archive); any push, merge, or
  tag; any change to a monitor source, the shim, a guest input, a
  scenario, the generator, a checker's rules, the lock, `model/`, or an
  accepted document's text; root `Makefile`/`be`/`scripts/check-be.sh`
  integration; a fourth scenario or instance; development-kernel/BSP
  selection; any board command before the human's confirmation.
- **Evidence status:** acceptance adds no implementation or evidence.
  Nothing of M4 has been written; the plan's one comparison is a
  read-only lookup on `l1`. Hardware is `NOT RUN` for M4.

### Errata and stops under the accepted plan

Recorded here as M3's were; the accepted plan's text at `0d02df72` is
not edited.

1. (M4-4, stop condition 5, 2026-10-29.) The new checking and record
   code of M4-1 and M4-4 is 1,347 lines at `ca322220`
   (`tools/claim-ledger.py` 692, `tools/rc-record.py` 591, `Makefile`
   23, `mvp` 28, `tools.mk` 13; 326 of them the two seeded self-tests
   and 81 the docstrings that define the tools' interfaces) against
   Q10's soft limit of about 900 for all of it. Nothing was cut; both
   tools run in under 4 s. The responsible human re-evaluated the limit
   and **re-set it to 2,000 lines** (`re stop 5, increase the limit to
   2000.`). The new-targets time limit of about 60 s is unchanged.
2. (M4-4, stop condition 9, 2026-10-29.) A board record made with the
   accepted board tools carries the board's ssh target and IPv4 address
   and a fixed M2 title; the remedy changes `tools/evidence.py` and
   `tools.mk` beyond the plan's letter. The responsible human directed
   the remedy (`re stop 9, agree with redaction / code names.`), recorded
   as [Plan revision M4-A](mvp-m4-plan.md#plan-revision-m4-a-the-board-record-s-identifying-strings)
   in the plan and presented for acceptance with M4's result.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `0d02df725541e4e8f93b3fc3de002358827aa1da` (tree `49bc2298`), parent `95fc0123` (this packet's first commit), on branch `beryllium/mvp-m4-plan` from `fb8accc9`, the development branch's tip after the M3 acceptance record and the push record. The target changes one file, `planning/mvp-m4-plan.md` (725 lines), and nothing else. The first candidate `91f4a820` (parent `fb8accc9`; 560 lines) is superseded: `git diff 91f4a820 0d02df72 -- planning/mvp-m4-plan.md` is the review's effect. |
| Current status | Documentation only: a bounded plan written under the accepted MVP plan (`93967fba`), whose M4 section it implements, with M0 (`b2669725`), M1 (`ff84533c`), M2 (`18d552bc`), and M3 (`b0a0f352`) accepted. No M4 work has started; nothing under `mvp/` or `model/` has changed. The first candidate was reviewed by `gpt-5.6-sol` on the session SOP; the nine findings are incorporated (section 5). The fast source checks pass (whitespace, every link and anchor). Responsible-human accepted on 2026-10-28 (instruction `accept 0d02df27, authorize M4`, read as `accept 0d02df72`; Q1 to Q13 at their defaults), with M4 implementation authorized. |
| Decision requested | Accept the exact commit as the M4 plan, request revisions, or defer; answer any of its Q1 to Q13 or let the defaults apply. Four defaults are flagged for explicit attention in section 3: the release-candidate board campaign (11 runs, `anchor` added only if its images differ from the M2-A record's) and its dependence on the board's availability (Q2), the MVP claim's final wording fixed by the plan (Q6), no review of the result by another model (Q5), and the release surfaces' location under `mvp/docs/` (Q1). Recorded outcome: accepted; the defaults apply; M4 implementation authorized. |
| Successor status | As presented: not started and not authorized: M4 implementation (work packages M4-1 to M4-6, which the plan's acceptance would authorize on `beryllium/mvp-m4` from its acceptance record, with the board campaign waiting on the human's confirmation that the K3 is free); every release-path step after the first (migration, the clean public repository, tag, publication, archive); any change to a monitor source, a guest input, a scenario, `model/`, or an accepted document's text; root `Makefile`/`be`/`scripts/check-be.sh` integration; any merge or push. After the decision: M4-1 to M4-6 are authorized on `beryllium/mvp-m4` from the acceptance-record commit, the board campaign still waiting on the confirmation; everything else stays not authorized. |
| Publication status | Private repository. `beryllium/mvp-m4-plan` is local and unpushed; the acceptance changes none of that, and any push or merge needs its own instruction. The development branch `beryllium/single-hart-runtime-r0`, `beryllium/mvp-m3`, and `beryllium/mvp-m3-plan` are on the private `origin` at `fb8accc9`, `fb8accc9`, and `97be918d`, as pushed on 2026-10-28. No tag, publication, or release. |

As presented: please review exact commit `0d02df72` and accept it,
request revisions, or defer. Outcome: accepted, with M4 implementation
authorized; see the [decision record](#decision-record).

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| The M4 plan | [`mvp-m4-plan.md`](mvp-m4-plan.md) (725 lines) | Defines M4's goal and pass criterion (the MVP plan's M4 "Delivers" and "Exit", made exact); the base and inputs with one read-only planning comparison (the current `anchor` images equal M2's board images; M0's and M1's board images are not in the current manifest) and the review of the first candidate; the MVP claim's final wording, scoped to `te-poc` and `anchor` with `anchor`'s tested attempts listed, with its required limit and forbidden phrasings (the MVP plan's list plus 24 literals in 14 groups, single-sourced in `claim.md`); the claim ledger (a JSON source, a rendered table, a checker with a seeded self-test, a method vocabulary that has no "verified", "hardware validation", or "formal verification", the commit check on the host only); the researcher guide's nine sections, with "write a scenario" stating what is data and what is a source change; the AI-assistance disclosure, stating what the assistance executed on direction; the release-candidate evidence from the pinned evaluators on a clean standalone checkout of the candidate tree `X`, every tool in `X`, the record and the ledger rows that cite it added in `R`, the release-candidate commit; one board campaign of 11 runs for `two-guests` and `te-poc` at `X`'s images, `anchor` added only if its images differ from the M2-A record's, gated on the human's confirmation; soft limits for re-evaluation; four departures; Q1 to Q13; ten stop conditions; work packages M4-1 to M4-6 | Planning text; it changes no source, no monitor byte, and no accepted document; it authorizes nothing until accepted | Is the fixed claim exactly what the retained records support, and is the board campaign's gating on the human's confirmation stated so that no board command can precede it? |
| Navigation | `planning/.vitepress/config.mts` | Lists the plan and this packet in the three navigation lists | Site configuration only, in this packet's commit | None beyond placement |
| Status pages | [`roadmap.md`](roadmap.md), [`HANDOFF.md`](HANDOFF.md), [`README.md`](README.md), `.github/copilot-instructions.md` | Record the proposed plan | Changed in this packet's commit, not in the target; status text only | None |

Exact changed-file inventory:

```text
# git diff --name-status 95fc0123 0d02df72
M	planning/mvp-m4-plan.md
# git diff --name-status fb8accc9 91f4a820   (the superseded first candidate)
A	planning/mvp-m4-plan.md
```

`git diff --stat 95fc0123 0d02df72 -- . ':!planning/mvp-m4-plan.md'` is
empty: the target changes one file and nothing else. Across the whole
branch, `git diff --name-status fb8accc9 0d02df72` lists only the plan,
this packet, and the status pages and navigation.

## 3. Claim boundary

**What the target supports saying.** A bounded plan for M4 exists that,
if accepted, would fix the MVP claim's wording and authorize six work
packages producing the four release surfaces, two small harness
additions, the clean evidence from the pinned evaluators at the candidate
tree, and, on the human's confirmation of the board, one board campaign,
ending in a release-candidate commit for the human's decision.

**What remains the human's judgment, with the defaults flagged.**

- **Q2, the board campaign.** The default runs 11 RAM-only kexec runs
  (three GCC and one Clang each for `two-guests` and `te-poc`; `payload`,
  `reader-write`, and `no-inject` once) at the candidate's images, only
  after the human confirms the K3 is free, with the `k3ctl` reset opted
  in and at most one reset by hand per run; `anchor` (four more runs and
  its two negatives, 17 in all) is added only if the candidate's `anchor`
  images differ from the four the M2-A record states, otherwise that
  record is the `anchor` evidence and the ledger states both hashes. The
  reason is the planning comparison: the `two-guests` and `te-poc` board
  evidence is at M0's and M1's images, which M1's and M2's monitor
  changes replaced, while `anchor`'s is at the current images. The
  alternatives are (b) no campaign, with the claim's first sentence
  gaining a clause the plan fixes now, and (c) the full 17 runs. The
  board is in use by the human for another project; the plan issues no
  board command before the confirmation (stop condition 7), M4-1 to M4-4
  do not need the board, and M4 waits at M4-5 for as long as the human
  needs, no alternative becoming the default by waiting.
- **Q6, the claim's wording.** The plan fixes the MVP claim, correcting
  the MVP plan's draft from the records: "RAM-only load" names Linux
  kexec from the board's Fedora host; "recorded firmware" becomes the
  firmware's recorded SBI identity (`ID=0x1 Version=0x10006`, OpenSBI
  1.6), because this BSP's console shows no firmware prints; the policy
  sentence is scoped to `te-poc` and `anchor`, because `two-guests` has
  no policy; "every access attempted outside the declared channels"
  becomes "every tested access not authorized by the declared rights",
  because M1's reader and M2's host store to declared pages beyond their
  rights; and "secret, result, and measurement were neither read nor
  altered" becomes the list of `anchor`'s tested attempts (the review
  found that the host reads the result from the response page by
  design). The required limit names `two-guests` as substrate evidence,
  the guests' provenance (unmodified upstream `v7.2` from a recorded
  configuration, the in-tree `nolibc` init, one module under its own
  license), the unproved monitor paths, and that the MVP's offline
  checker is not the proved function. The forbidden list adopts the MVP
  plan's and adds 24 literals in 14 groups, single-sourced in
  `claim.md`. Accepting the plan accepts this wording and the alternative
  (b) clause; a later change is a plan revision (stop condition 2).
- **Q5, a review of the result by another model.** None by default, per
  the 2026-10-06 SOP and the MVP plan's Q7; the session SOP of
  2026-10-28 covers planning steps, which this plan's review was. The
  alternative is one critique of the release surfaces by `gpt-5.6-sol`
  before the result packet, which the human may direct.
- **Q1, the surfaces' location.** `mvp/docs/`, with the code, so the
  release path's step 2 selects them together; not rendered by the
  planning site (Q9).

**What the plan explicitly does not do.** No monitor, shim, guest,
scenario, generator, checker-rule, lock, or `model/` change; no new
scenario; no root integration; no tag, version file, or SBI version
change; no release-path step after the first; no public repository,
migration, archive, or publication; no HTML generation; no Helium
material; no edit to an accepted document's text.

**Evidence status.** The plan adds no evidence. Its one comparison is a
read-only lookup of the three board records' image hashes in the last
check's manifest on `l1`, which the reviewer repeated with the same
result; nothing was built or changed. Hardware is `NOT RUN` for M4.

## 4. Load-bearing decisions

| Decision | Where | Why it matters |
| --- | --- | --- |
| The claim is fixed by the plan, not by the implementation | Q6; "The MVP claim" | The wording is accepted before it is published in the tree; the implementation copies it byte for byte (pass criterion 1) |
| The ledger's method vocabulary excludes "verified", "hardware validation", and "formal verification" | "The claim ledger" | A row cannot claim more than the evidence terms allow; the checker enforces it |
| The ledger has one JSON source and a rendered table | Q3 | The reader's table and the checker's data cannot diverge |
| The release surfaces are the only documents the phrasing checker scans | Q13 | The two READMEs quote the phrasings in negation throughout their history; the release path's step 2 decides their public form |
| Every tool is in the candidate tree `X`; `R` adds only records, the ledger rows that cite them, and the evidence record, and the ledger is checked again at `R` | Q4; "The release-candidate evidence"; departure 1 | The gates' evidence applies to `X`; `R` is the one reviewed commit; the ledger cannot hash records that do not yet exist |
| The gates run from a clean standalone checkout, not a linked worktree | pass criterion 4 | The evaluator mounts the tree alone; a linked worktree's `.git` file points outside it |
| The forbidden list has one source, `claim.md`; the commit check runs on the host only | Q13; "The claim ledger" | A duplicated list would fail the phrasing scan; `git` inside the evaluator has no repository for a linked worktree |
| `anchor` is re-run only if its images differ from the M2-A record's | Q2 | The campaign follows its own rationale: board evidence at the candidate's images for every scenario, without repeating runs whose images already match |
| The board campaign waits on the human's confirmation | Q2; stop condition 7 | The board is in use for another project |
| Soft limits re-evaluate, never cut | Q10; "Soft limits" | The responsible human's direction of 2026-10-28 |

## 5. Review history and resolved findings

**The `gpt-5.6-sol` review of the first candidate `91f4a820`
(2026-10-28).** On the responsible human's session SOP (`ok, SOP for
this session is to have gpt-5.6-sol max long review planning steps`),
the first candidate was reviewed read-only by that model at `max` with
the `long_context` tier. The governance hook's required model
(`~/.copilot/hooks/beryllium-governance-hook.sh`, line 188) was edited
to `gpt-5.6-sol` for that one launch and restored at once (SHA-256
`4f4c2c8717e2a0d8…` before and after). The reviewer verified the plan's
facts (the empty `mvp/` diff since `18d552bc`; the four M2 image hashes
in the current 247-image manifest and none of M0's six or M1's four;
the five board negatives; every board run through `kexec_load`; the
firmware identity; the evaluator's read-only mount and `git-core` in its
closure; the guest's clean source and 16-entry configuration delta;
`be-mgmt.c` under `GPL-2.0-only`; `kernel-repro` as a Make target only)
and ran no build, test, evaluator, or board command. Its verdict was
"not ready as-is": three blockers, six should-fix. Each finding and its
resolution in `0d02df72`:

| # | Finding (severity) | Resolution |
| --- | --- | --- |
| 1 | The fixed claim overstated the records (blocker): M1's reader and M2's host store to declared pages beyond their rights, so "outside the declared channels" was wrong; the host reads the protected domain's result from the response page by design, so "result … neither read" was false; `two-guests` has no policy; "one firmware build" is unsupported | The claim is scoped to `te-poc` and `anchor`; "every tested access not authorized by the declared rights"; `anchor`'s tested attempts listed (read the secret, alter the result, reach the private window and the monitor's region) with the measurement unaltered; "one reported SBI implementation identity and version"; the required limit names `two-guests` as substrate evidence, the unproved monitor paths, and the result's read by design |
| 2 | The X/R construction was impossible as ordered (blocker): `rc-record` was added after `X` was "fixed", and the ledger at `X` had to hash records that exist only at `R` | Every tool, `rc-record` included, is in `X`; `R` adds records, the ledger rows that cite them (`evidence_source_commit: X`, no container SHA), the rendered table, and the evidence record; `claim-ledger.py check` runs again at `R` on the host; the gates run from a clean standalone checkout, not a linked worktree |
| 3 | The checker's specification conflicted with itself (blocker): the forbidden list duplicated into the ledger would fail the scan of `mvp/docs/*.md`; `git cat-file -e` accepts any object; directories have no hash rule; `not run` beside required evidence; matching unspecified; `git` inside the evaluator cannot see a linked worktree's repository | The list's single source is `claim.md`'s section; `<sha>^{commit}`; a record is cited by its `MANIFEST.sha256`; `not run` is exclusive; the literal matching rule is stated; the commit check runs on the host and is skipped, and says so, inside the evaluator |
| 4 | Q2's rationale was sound but 17 runs repeated `anchor`, whose images already match; the load checks named no scenario; the commands were implicit; the extra-reset rule was unstated; alternative (b) had no claim wording; the probe facts were not marked historical (should-fix) | 11 runs for `two-guests` and `te-poc`; `anchor` only if `X`'s four `anchor` images differ from the M2-A record's; the load checks and every command named; at most one reset by hand per run, recorded; alternative (b)'s clause fixed with the claim; the probe values marked M0-image characterization |
| 5 | The disclosure would have been inaccurate (should-fix): commits carry `Co-authored-by: Copilot`; the campaign tools executed `k3ctl` resets; pushes were executed in assisted sessions; `LLM_POLICY_ALIGNMENT.md` says AI is not a reviewer | The disclosure states the human as author and committer, decision-maker, and sole approver; the trailer; the commands executed on direction (campaigns with the opted-in reset, pushes, fast-forwards); model critiques as automated analysis, the human's exact-commit review as the review |
| 6 | The RC record lacked provenance and hygiene (should-fix): `./be evaluate` removes the host's `build/model`; the model subset omitted the claim status, assumption reports, and tool versions; no stop for secrets, host paths, or identifiers; `rc-record`'s inputs implicit | The host's model evidence is copied aside between `./be model-check` and `./be evaluate`; the complete evidence directories are retained; `rc-record` takes explicit inputs that must name `X` and the recorded evaluator identity; the privacy rule in the checker; stop 9 |
| 7 | "Write a scenario" overstated the supported path (should-fix): the harness's lists and the model's generator and driver are fixed to the three scenarios and the accepted instances | The guide states what is data and what is a source change, names the lists and the generator inputs, and adds no fourth scenario |
| 8 | The soft limits were not measurable or loophole-free (should-fix): shell could escape a Python count; whole-check time varies; the checker-to-monitor table was omitted | The limit counts every language, tests included, generated files excluded; the new targets' own time, three runs; the checker-to-monitor table reported in M4-6 |
| 9 | Exact details (should-fix): `kernel-repro` has no wrapper form; "no accepted document's text" clashed with editing `mvp/README.md`; `mvp/docs/` headers unspecified; this packet said "fifteen phrasings" for 24 literals in 14 groups | `make -C mvp kernel-repro`; the accepted-document boundary defined, the development log and status pages outside it; the SPDX line and this repository's copyright identity required; the count corrected here |

The reviewer's answer to the governance question was that the first
candidate inferred no acceptance, authorized no release step, and gated
the board on the human's confirmation; those properties are unchanged.
Its suggestion of a separate `artifact_container_commit` field was not
adopted: the rows added at `R` carry only `evidence_source_commit: X`,
because the commit containing the ledger cannot be named inside it, and
the evidence record names `R`. Its suggested default of 11 runs was
adopted with the `anchor` byte-comparison rule instead of a fixed count,
so that the campaign always covers every scenario whose board evidence
is not at the candidate's images.

**The orchestrating session's own checks** while writing the first
candidate (kept for the record): the draft claim's "recorded firmware"
and "every access attempted"; the stale `two-guests` and `te-poc` board
images; the bundle that cannot name its own commit (departure 1); the
READMEs' historical negations (Q13).

**Open for human judgment:** Q1 to Q13; the four flagged defaults.

## 6. Validation and retained evidence

| Check | Result |
| --- | --- |
| `git diff --check` on the plan (both candidates) | clean |
| Every relative link and anchor in the plan | resolves |
| Lines over 80 columns outside tables, links, record fields, and commands | none |
| Retired names and former identities in the plan | none |
| The plan's own text against its forbidden literals | the literals occur only in the "Forbidden phrasings" list |
| The `gpt-5.6-sol` review's fact checks | agree with the plan (section 5) |

Nothing was built, run, or changed under `mvp/` or `model/`; the plan's
facts are cited to the records and sources named in its "Base and
inputs". The review's text is retained in the session's files, not in
the repository; its findings and resolutions are recorded above.

## 7. Recommended review sequence

1. The decision requested, the open questions, and the four flagged
   defaults (the plan's first two sections).
2. "The MVP claim": the claim, the required limit, the corrections to
   the draft, and the forbidden phrasings; compare with the MVP plan's
   "The MVP claim".
3. "The claim ledger", "The researcher guide", "The AI-assistance
   disclosure", "The release-candidate evidence", "The release-candidate
   board campaign", and "What M4 does not do".
4. "Soft limits", "Accepted decisions M4 departs from", "Risks", "Claim
   boundary and non-goals", "Work packages", "Stop conditions", and "How
   M4 feeds the release path".

Read-only commands:

```sh
git show --stat 0d02df72
git diff 95fc0123 0d02df72 --stat
git diff 91f4a820 0d02df72 -- planning/mvp-m4-plan.md   # the review's effect
git show 0d02df72:planning/mvp-m4-plan.md | less
git show 93967fba:planning/mvp-plan.md | sed -n '/^### M4/,/^## Order/p'
git show 93967fba:planning/mvp-plan.md | sed -n '/^### The MVP claim/,/^## Decisions recorded/p'
```

The planning comparison can be repeated read-only against the last
check's manifest on `l1`:

```sh
for r in 20261025-com260 20261027-com260-m1b 20261028-com260-m2a; do
  grep -o 'Image SHA-256 values on the board: .*' mvp/results/$r/summary.md
done
cat build/mvp/evidence/check/images.sha256 | grep -E 'boot\.img$'
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The plan implements the MVP plan's M4 "Delivers" and "Exit"
      exactly, with every reinterpretation named as a departure.
- [ ] The fixed claim and its required limit say no more than the
      retained records support, and the corrections to the draft are
      right.
- [ ] The forbidden phrasings are the ones to enforce, and scanning only
      the release surfaces is acceptable.
- [ ] The board campaign's default (11 runs after your confirmation,
      `anchor` added only if its images differ from the M2-A record's)
      or an alternative ((b) none, with the fixed clause; (c) 17 runs)
      is chosen.
- [ ] No review of the result by another model (Q5), or one is directed.
- [ ] The resolutions of the nine review findings (section 5) are
      acceptable, including the two the plan decided differently from
      the reviewer's suggestion.
- [ ] The soft limits as re-evaluation stops are acceptable.
- [ ] Successor work stays excluded: every release-path step after the
      first, any merge or push, any source or accepted-text change.
- [ ] Decision: accept exact commit `0d02df72` as the M4 plan; request
      revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `0d02df725541e4e8f93b3fc3de002358827aa1da` and the date, with
  any answers to Q1 to Q13. The acceptance record names that SHA; the
  status documents are updated to match. Acceptance authorizes work
  packages M4-1 to M4-6 on `beryllium/mvp-m4` from the acceptance record,
  the board campaign only after your confirmation that the K3 is free,
  and nothing else: no release-path step after the first, no merge, no
  push.
- **Request revisions:** a new commit and a new packet follow;
  `0d02df72` is not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commit `0d02df725541e4e8f93b3fc3de002358827aa1da` is
responsible-human accepted as the M4 plan as of 2026-10-28 (instruction
`accept 0d02df27, authorize M4`, read as `accept 0d02df72`; Q1 to Q13
at their defaults; the first candidate `91f4a820` superseded after the
`gpt-5.6-sol` review), and M4 implementation is authorized. It is on
branch `beryllium/mvp-m4-plan`, local and unpushed; the K3 is untouched.

**Next:** M4-1 to M4-6 begin on `beryllium/mvp-m4` from this
acceptance-record commit (coding on `claude-opus-5.5` per the model
split; critiques of planning steps by `gpt-5.6-sol` per the session
SOP). The board campaign (M4-5) waits on your confirmation that the K3
is free. The result is presented as one review packet for the
release-candidate commit `R`.

**Action required from you:** none for the plan. When the K3 is free,
say so; M4-5 does not start before that.
