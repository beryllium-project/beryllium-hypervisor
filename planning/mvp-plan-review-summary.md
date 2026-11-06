<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# S3 MVP plan: review summary

This packet supports a responsible-human decision on one exact commit. It
was presented as decision-neutral and not self-approving; the decision
record below holds the outcome.

## Decision record

The responsible human accepted exact commit
`93967fbac926b4fdfdfe636df4d07e8926b625b7` (parent `882868b9`) as the S3
MVP plan on 2026-10-23 with the instruction `accept 93967fba`, given in
reply to this packet's request to accept, revise, or defer that exact
commit. The abbreviation was checked to resolve uniquely to that commit.

- **Scope:** acceptance covers exactly the document text at that commit,
  revision 1 of the plan. Sections 1 to 9 are the packet as presented,
  apart from the outcome rows in section 1, a note above the section 8
  checklist, and the closing lines of section 9. The document carries its
  own decision record. The first candidate `06c35f48` stays superseded
  and was never accepted.
- **Open questions:** Q1 to Q12 were not answered, so their defaults
  apply, as listed in the document's decision record.
- **Effect:** the plan selects M0 to M4, records D1 to D16 at their
  defaults, and authorizes writing M0's bounded plan, which includes the
  static multi-hart substrate, on a new branch from the development
  branch. No implementation, hart start, board run, accepted-byte change,
  model change, security model v1 revision, push, merge into the
  development branch, publication, or release step follows from it. The
  development branch is at `0096de3e` and does not yet hold the accepted
  plan; fast-forwarding it and any push need their own instruction.
- **Decision support:** the packet commit `2f282dc8` and this
  acceptance-record follow-up are decision support, not plan content.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `93967fbac926b4fdfdfe636df4d07e8926b625b7` (tree `2e2044a586622aaa18088e4f61f8fa34b8de1b71`), parent `882868b952b7921bd528555b7f20c908cb363eea`, the packet commit of the first candidate; branch `beryllium/s3-mvp-plan`, from the development branch at `0096de3e` |
| Superseded candidate | `06c35f4829f14b4896a5cc46dee77ed8bee0ef9d` (tree `9b3999074d52be15f7d458a15f4235124b7d6280`), the first S3 candidate of 2026-10-22: a single-hart MVP on B7's scheduler, with a second hart excluded. Never accepted; superseded on 2026-10-23 by the responsible human's revision request before any decision on it |
| Current status | Documentation only; revision 1 of the plan, directed on 2026-10-23 by `revise the plan so that the MVP 1.0 is one hart per guest and the security monitor / protected domain (remind me, what are we calling this?) has its own hart as well`, with four form answers (section 5); the fast source check passes. Recorded outcome: accepted on 2026-10-23 (`accept 93967fba`) |
| Decision requested | Accept the exact commit as the S3 MVP plan, request revisions, or defer; answer any of Q1 to Q12 or let the defaults apply. Q1 to Q12 were not answered; their defaults apply |
| Successor status | MVP milestones M0 to M4 not started; the acceptance authorizes writing M0's bounded plan only, and M0 now includes the static multi-hart substrate; no stop condition fired |
| Publication status | Private repository; the target is on local branch `beryllium/s3-mvp-plan`, unpushed; the development branch is at `0096de3e` locally and on `origin`, pushed on 2026-10-22; no tag, publication, or release |

As presented, the packet asked for the exact target to be accepted,
revised, or deferred; the [decision record](#decision-record) above holds
the outcome.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| The S3 MVP plan, revision 1 | [`mvp-plan.md`](mvp-plan.md) | Defines MVP 1.0 on three statically assigned harts of the COM260's eight, one control hart and one hart per domain; its scope and non-goals; milestones M0 to M4 with goals, deliverables, exits, and evidence classes, M0 now holding the multi-hart substrate; the evaluation harness; a method per claim, the MVP claim, its required limit, and its forbidden phrasings; decisions D1 to D16; the decisions and guidance it departs from; the release path; stop conditions; risks; open questions Q1 to Q12; and a revision record | A plan only: it selects milestones and authorizes, if accepted, writing M0's bounded plan and nothing else; no code, model, board, hart start, push, or release change | Is the static three-hart layout with a dedicated control hart the MVP 1.0 you want ("Hart layout"; D14 to D16), given that the research document recommends against a control hart as the first design (departure 2)? |
| Status pages | [`roadmap.md`](roadmap.md), [`HANDOFF.md`](HANDOFF.md), [`project-orientation.md`](project-orientation.md), [`README.md`](README.md), [`glossary.md`](glossary.md), [`implementation-plan.md`](implementation-plan.md), `.github/copilot-instructions.md` | Record revision 1, the new candidate, and the superseded first candidate; the glossary gains **monitor**, **control hart**, and **domain hart** and updates **hart** | Changed in this packet's commit, not in the target; status text only | None |

Exact changed-file inventory:

```text
# git diff --name-status 882868b9 93967fba
M	planning/mvp-plan.md
```

`git diff --stat 882868b9 93967fba -- model/ include/ virt/ arch/ bringup/
tests/` is empty. Against the superseded candidate, the plan text grows by
358 lines and loses 114 (`git diff --stat 882868b9 93967fba`).

## 3. Claim boundary

**The commit supports saying:** Beryllium has a proposed MVP plan, in its
first revision. It defines MVP 1.0 as the first release that a security
researcher can build, run in QEMU and on a K3 board, and use to study
isolation between Linux-class domains under a declared policy, with every
domain on its own hart and the monitor's shared work on a dedicated
control hart; it reconciles the expected first MVP milestone with the
founding anchor use case by making the first a step toward the second; it
selects five milestones with exit criteria and evidence classes; it
records a decision, with a default, on every item that the accepted
documents leave to S3; and it records where it departs from accepted
decisions and recorded guidance.

**Trusted or assumed:**

- The accepted documents the plan cites say what it quotes. Each was read
  at `0096de3e`, and the line references were re-checked there: the
  implementation plan's concurrency model (L1201-L1228) and milestone 4
  (L2030-L2038), the research document's hart sections (L165-L251), the
  hardware document (L70-L76, L142-L152, L230), and the B1 and B2 records
  (L158, L171).
- The K3 facts the plan uses are B7's preflight record of 2026-10-08
  (eight harts, each listing `h`, `sstc`, `smaia`, `ssaia`, and `svinval`;
  "SBI HSM extension detected") and the B1 and B2 records ("Linux stopped
  its other harts before each kexec"). Beryllium has never started a
  second hart, taken an IPI in HS, or shared a page between harts. The
  substrate design is planning judgment; that HSM `hart_start` works
  after a kexec on this firmware, that an IPI reaches HS while a domain
  runs, and that the layout's harts are coherent are assumptions M0 must
  record, and each is stop condition 2 if false.
- The reading of "the security monitor / protected domain has its own
  hart" as a dedicated control hart, with the monitor's enforcement path
  still on every domain hart, follows the research document (L165-L169)
  and the form answer `control_hart`.
- That the milestones are feasible as scoped is a planning judgment, not
  evidence. No milestone has a bounded plan, and the plan gives no effort
  or date estimate.
- The session ran on `claude-fable-5.1` after the responsible human
  switched the model from the pinned `claude-opus-5.5`; the pin in
  `.github/copilot-instructions.md` is unchanged. No research agent,
  independent review, separate scope review, or deep security review ran
  (the 2026-10-06 SOP).

**Unavailable or not run:** no implementation, build, QEMU run, board run,
hart start, or proof; no generated HTML, `npm run docs:build`,
`./be docs-check`, or Chromium render.

**Not implemented:** everything in M0 to M4, including the MVP line, the
tool lock, the multi-hart substrate (HSM start, boot barrier, rings, IPI
protocol, control loop), the harness, the offline checker, the authority
report generator, the security model v1 revision, and the Model changes.

## 4. Load-bearing decisions

| Decision | Where stated | Evidence |
| --- | --- | --- |
| MVP 1.0 runs one domain per hart with a dedicated control hart: the static part of the implementation plan's Stage 2, with the dynamic part left to milestone 4 | "Hart layout"; D14 to D16; non-goals | The responsible human's request and form answers (revision record); reading against implementation plan L1211-L1220 and research L183-L217 |
| The monitor's enforcement path runs in HS on every domain hart; the control hart holds only the shared work, and no domain hart's fast path touches shared mutable state | "Hart layout"; M0 deliverable 5 | Reading against research L165-L169 and L219-L238 |
| The dedicated control hart departs from the research document's guidance; its five costs are named, carried as risks, and its protocol is recorded as unproved | "Hart layout"; departure 2; risks; "Method per claim" | Reading against research L171-L181 |
| M0 absorbs the multi-hart substrate instead of a new B8 bring-up milestone | M0 deliverable 5 | Form answer `substrate_home=fold_into_m0` |
| M3 plans an additive security model v1 revision as its own exact commit, which stop condition 1 admits; the accepted document is unchanged by this plan | M3 deliverable 1; stop condition 1; departure 4 | Form answer `model_treatment=add_hart_obligations`; reading against security model v1 Part 1 (I5, I7) and Part 7 |
| S1 H12's stale-authority check no longer applies without a root switch in the scenario; the invariant is restated and K3's VMID tagging moves to a probe in M0, so S1's third gap is still closed | M1 deliverable 4; M0 deliverable 4; "Method per claim" | Reading against S1 H12 and the hand-off's three gaps |
| MVP 1.0 reconciles project review F-08: M1 is a step toward M2, the anchor use case in static form | "What the MVP is"; D1; Q1 | Unchanged from the first candidate; reading against implementation plan L629-L641 and project review option 2 |
| No accepted byte or document changes, and no implementation authority | "What acceptance authorizes"; stop condition 1; the status record | The changed-file inventory above; `s3_authorization=none` and `mvp_implementation_authorization=none` |
| M2 stays inside security model v1: only `pause` and `terminate` of the `domain` class, now crossing harts through the control hart, and a measurement the monitor logs rather than one a domain queries | M2, items 1, 3, and 4 | Reading against security model v1, "Object classes" and Part 6 |
| The MVP claim is bounded, with a required limit that now fixes the hart assignment and forbidden phrasings that now cover "SMP" and "multicore" | "The MVP claim" | Reading |
| Every release step needs its own explicit instruction | "Release path"; stop condition 7 | Unchanged; reading against `LLM_POLICY_ALIGNMENT.md` |

## 5. Review history and resolved findings

Revision 1 (2026-10-23):

1. **The request.** Asked how two guests on one hart are scheduled, the
   responsible human asked `is this really useful? would it be better to
   have two guests running on their own harts?` and then directed the
   revision quoted in section 1. Before writing it, four questions were
   put and answered: `control_hart=control_hart` (a dedicated control
   hart, rather than the research document's monitor-on-every-hart-only
   layout); `layout_confirm=true` (M1: control, writer, reader harts; M2:
   control, untrusted Linux, protected-domain harts); `substrate_home=
   fold_into_m0` (no B8); `model_treatment=add_hart_obligations`. The
   defaults stated with the questions (SBI HSM and IPI, native `wfi`, no
   scheduler, remaining harts never started, QEMU with eight harts, the
   binding in the manifest, `06c35f48` superseded) were taken.
2. **Terminology.** "the security monitor / protected domain" names two
   things. The plan uses **the monitor** for the HS software and **the
   protected domain** for `prot_t`; because the monitor's enforcement path
   must run on every domain hart, the dedicated hart is **the control
   hart**. The glossary gains the three terms in this packet's commit.
3. **The stale-authority check.** S1 hand-off item 1 and H12 put Helium's
   stale-authority check into the first MVP milestone. Under static
   ownership no root switch occurs on a hart during a scenario, so the
   check has nothing to test. The revision restates the invariant for the
   layout, enforces it by readback and a single-writer rule, and moves
   K3's VMID tagging to a bounded probe in M0's platform record. For your
   judgment: whether a probe meets H12's intent.
4. **Stop condition 1.** M3's hart obligations need the accepted security
   model v1 to gain a hart binding. The revision plans that as an additive
   revision in its own exact commit, before any model work, and amends
   stop condition 1 to admit exactly it.
5. **Guidance departed from.** The research document recommends against a
   dedicated control hart as the first design and lists what it adds
   (L171-L181). The revision follows your answer, quotes the list, carries
   each item as a risk, and records the protocol as unproved. S1 H57, the
   implementation plan's Stage 1 time-multiplexing, and security model
   v1's switch-based I5 and I7 are the other recorded departures.
6. **Line length.** The first commit of the revision, `139941ec`, had an
   81-character M0 heading; it was amended into the target and is not
   referenced anywhere else.
7. **Not resolved, for your judgment:** Q1 to Q12, most of all Q1 (what
   MVP 1.0 contains), Q2 (root integration), Q3 (K3 evidence beyond the
   B-series), Q6 (what "release" means), and the new Q9 to Q12 (the time
   budget, the QEMU hart count, how a terminated domain's hart ends, and
   which physical harts).

First candidate (2026-10-22), kept as history:

1. **M2's management calls.** The first draft gave the untrusted Linux
   domain `status` and `measurement` calls, for which security model v1's
   `domain` class has no permission, so authorizing them would have needed
   a change to the accepted model. Corrected before commit: M2 uses only
   `pause` and `terminate`, and the monitor logs the measurement instead.
2. **The `domain` class.** The first draft said V2 defined the class for
   M2's use; V2 kept it granted to no static subject. Corrected: M2 is the
   first instance in which a domain holds a `domain` permission, the use the
   class was kept for.
3. **Claim wording.** "every tested access" repeated "In the tested
   scenarios"; corrected.
4. **Research agents.** The governance hook denied all three planned
   sub-agents because `BERYLLIUM_PARENT_ROOT` is unset in the hook's
   configuration, which `project-manager/scripts/beryllium-governance.sh`
   writes at install time. The session read the inputs directly and did not
   change the hook. Repairing it is a workstation action for you or the
   Project Manager.

No research agent, separate scope review, or deep security review ran in
either session.

## 6. Validation and retained evidence

These ran on 2026-10-23 on the working tree immediately before the target
commit and again on the committed target; the commit records exactly that
content. They did not run in a fresh checkout.

| Command | Result | Covers |
| --- | --- | --- |
| `git diff --check 882868b9 93967fba` | pass | whitespace in the changed tracked file |
| `grep -nP '[ \t]+$'`, `grep -nP '[^\x00-\x7F]'`, and a `grep` for absolute home, temporary, and session-folder prefixes on the plan | no matches | whitespace, ASCII, private locators |
| An `awk` scan for prose lines longer than 80 characters in the plan, excluding table rows, quotes, and status-record keys | none | line wrapping |
| `node docs/check-links.mjs --tasking-fence-regression` | pass, 8 cases | the owner tasking section's regression cases |
| `node docs/check-links.mjs --tasking-contract` | pass | the owner tasking contract |
| `umask 0022 && npm run docs:source-check` | pass: self-tests `PASS`; `site_markdown=123`, `policy_markdown=5`, `rendered_references=1372`, `configured_routes=293`; isolation `PASS` with `network_events=0`, `generated_tree_changes=0`, `adversarial_cases=34` | the checker's self-tests; links, anchors, routes, private locators; the source gate under isolation |
| `git diff --stat 882868b9 93967fba -- model/ include/ virt/ arch/ bringup/ tests/` | empty | no code, model, bring-up, or test change |

No report, ledger, or hash is produced by a documentation-only package; the
commit is the artifact.

## 7. Recommended review sequence

Read-only commands, from the Beryllium checkout:

```sh
git show --stat 93967fbac926b4fdfdfe636df4d07e8926b625b7
git show 93967fbac926b4fdfdfe636df4d07e8926b625b7:planning/mvp-plan.md
git diff 06c35f4829f14b4896a5cc46dee77ed8bee0ef9d 93967fbac926b4fdfdfe636df4d07e8926b625b7 -- planning/mvp-plan.md
```

The third command shows exactly what revision 1 changed against the
superseded candidate.

1. **"Revision record" and "Hart layout":** the request, the four answers,
   the three-hart layout, what the control hart holds and what the domain
   harts keep, the relation to the implementation plan's Stage 2 and the
   research document, and "Why not time-slicing".
2. **"Decisions and guidance this revision departs from":** the four
   departures, above all the research document's guidance against a
   dedicated control hart (L171-L181).
3. **"What the MVP is" and Q1:** the reconciliation of the TE PoC scenario
   with the anchor use case, unchanged.
4. **"Milestones":** M0's deliverable 5 (the substrate) and 4 (the
   platform record); M1's deliverable 4 (the VMID invariant restated) and
   5 (the concurrent protocol); M2's deliverable 3 (management calls
   across harts); M3's deliverable 1 (the planned security model v1
   revision). Read M2 against implementation plan L629-L658.
5. **"Evidence claims":** the method per claim, with the new rows for the
   root binding and per-hart state; the MVP claim, its required limit, and
   its forbidden phrasings.
6. **"Decisions recorded by this plan":** D8, and the new D14 to D16.
7. **"Stop conditions", "Risks", and "Open questions and defaults":**
   stop conditions 1 to 3 as amended, the six new risks, and Q9 to Q12.
8. **"Release path":** against `LLM_POLICY_ALIGNMENT.md`, unchanged.

To re-run the source checks on the exact commit, use a detached worktree in
the workspace's `worktrees/` container, then `npm ci` and
`umask 0022 && npm run docs:source-check` inside it:

```sh
git worktree add --detach ../worktrees/beryllium-hypervisor/review-93967fba 93967fbac926b4fdfdfe636df4d07e8926b625b7
```

## 8. Human decision checklist

As presented, the packet asked the human to decide on `93967fba`. The
[decision record](#decision-record) above holds that decision; the
checklist is retained as presented.

- [ ] The static three-hart layout, one control hart and one hart per
      domain, is the MVP 1.0 you want, knowing the research document
      recommends against a dedicated control hart as the first design
      ("Hart layout"; departure 2; D14 to D16).
- [ ] MVP 1.0 as defined, M1 as a step toward M2, is the release you want
      (Q1).
- [ ] The non-goals are right, in particular no dynamic multicore, no
      time-multiplexing, no devices, a static configuration, and no
      attestation.
- [ ] M0 is the right home for the multi-hart substrate, and its platform
      record covers what the design assumes (HSM start after kexec, IPI
      delivery to HS, cross-hart ordering, VMID tagging).
- [ ] Dropping the stale-authority switch test for a readback rule and an
      M0 probe meets S1 H12's intent (finding 3).
- [ ] M3 may plan an additive revision of the accepted security model v1,
      and stop condition 1 may admit exactly that (finding 4).
- [ ] Each milestone's exit is the right evidence, with the right board
      campaign size.
- [ ] The MVP claim, its required limit, and its forbidden phrasings match
      the evidence the milestones would produce.
- [ ] D1 to D16 are acceptable, or you answer Q1 to Q12.
- [ ] The release path matches your intent for publication (Q6).
- [ ] Each milestone, hart start, board campaign, push, and release step
      stays excluded until separately directed.
- [ ] Decision: accept `93967fba`, request revisions, or defer.

## 9. After the decision

- **Accept:** on your instruction, a follow-up records the acceptance of
  exactly `93967fbac926b4fdfdfe636df4d07e8926b625b7` with the instruction,
  the date, and any answers to Q1 to Q12; M0's bounded plan may then be
  written on a new branch from the development branch. Nothing is pushed
  unless you say so.
- **Request revisions:** a new commit and a new packet follow; this SHA is
  not treated as accepted, and `06c35f48` stays superseded.
- **Defer:** the current status stays, and no MVP milestone starts.

**Status:** exact commit `93967fba`, revision 1 of the S3 MVP plan, is
responsible-human accepted as of 2026-10-23 (`accept 93967fba`), on local
branch `beryllium/s3-mvp-plan`; nothing is pushed. The first candidate
`06c35f48` is superseded and was never accepted. The development branch
is at `0096de3e` locally and on `origin` and does not yet hold the
accepted plan.

**Next:** M0's bounded plan may be written on a new branch from the
development branch; fast-forwarding the development branch to the
acceptance record and any push each need an explicit instruction.

**Action required from you:** none for the S3 MVP plan; direction on the
development-branch fast-forward, the push, and the start of M0's plan.
