<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# S2 security model v1 plan: review summary

This packet supports a responsible-human decision on one exact commit. It
was presented as decision-neutral and not self-approving; the decision
record below holds the outcome.

## Decision record

The responsible human accepted exact commit
`5ce7827f9c2ffc6e0f88568692ab238e5feca49f` (parent `0eb37570`) as the S2
plan on 2026-10-19 with the instruction `accept 5ce782`, given in reply to
this packet's request to accept, revise, or defer that exact commit. The
abbreviation was checked to resolve uniquely to that commit.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Sections 1 to 9 are the packet as presented, apart from the outcome rows
  in section 1, the Q1 entry in section 5, a note above the section 8
  checklist, and the closing lines of section 9. The plan carries its own
  decision record.
- **Authorized:** work packages S2-1 to S2-7, ending in one exact commit of
  `planning/security-model-v1.md` for a separate decision, with Q1
  answered as A and Q2 to Q7 at their defaults. No code, no `model/`
  change, no accepted-byte change, no push, no S3.
- **Decision support:** the packet commits `b194b9d6` and `75bfea7e` and
  this acceptance-record follow-up are decision support, not plan content.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `5ce7827f9c2ffc6e0f88568692ab238e5feca49f` (tree `504f20dcd9884eee62e9dafdcdce531e664f4623`), parent `0eb37570f9cb901ef994cc10aef8c7890c6134e9`, the development-branch tip: the S2 plan |
| Current status | Documentation only; the fast source checks pass. Recorded outcome: accepted on 2026-10-19 (`accept 5ce782`) |
| Decision requested | Accept the exact commit, request revisions, or defer; answer any of Q1 to Q7 or let the defaults apply. Q1 was answered on 2026-10-19 (see section 5); Q2 to Q7 are open with their defaults |
| Successor status | S2 itself authorized by this acceptance and not yet started; S3 not started and not authorized |
| Publication status | Private repository; the target is on local branch `beryllium/s2-security-model`, from the development branch at `0eb37570`, unpushed; the development branch is at `0eb37570` locally and on `origin`; no tag, publication, or release |

The responsible human directed this plan on 2026-10-18 with
`then proceed with S2 plan`. As presented, the packet asked for the exact
target to be accepted, revised, or deferred; the
[decision record](#decision-record) above holds the outcome.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| S2 plan | [`s2-security-model-plan.md`](s2-security-model-plan.md) | Bounds the writing of `planning/security-model-v1.md` as seven work packages that fill the accepted seven-part S2 definition, with inputs, a decision-gate mapping, stop conditions, and Q1 to Q7 | Proposed only; if accepted, authorizes documentation work ending in one exact commit, nothing else: no code, no `model/` change, no accepted-byte change, no push, no S3 | Are the seven packages the right decomposition of the accepted definition, and are the defaults (a tool-free notation defined in the document; analyses defined, not implemented; three use cases for the triggers; no independent review) what you want? |
| Navigation | `planning/.vitepress/config.mts` | Lists the plan and this packet in the three navigation lists | Site configuration only | None beyond placement |
| Status pages | [`roadmap.md`](roadmap.md), [`HANDOFF.md`](HANDOFF.md), [`project-orientation.md`](project-orientation.md), [`README.md`](README.md), [`glossary.md`](glossary.md), `.github/copilot-instructions.md` | Record the development-branch fast-forward and push to `0eb37570` and the proposed S2 plan | Status text only | None |

Exact changed-file inventory:

```text
# git diff --name-status 0eb37570 5ce7827f
M	planning/.vitepress/config.mts
A	planning/s2-security-model-plan.md
```

## 3. Claim boundary

**The commit supports saying:** a bounded plan for S2 exists, derived from
the accepted S2 definition (`1ac7080f`), the accepted M01-A trigger text
(`95ef0f6c`), the accepted S1 (`fd670dcd`), and the implementation plan's
founding policy sections, for the responsible human to accept, revise, or
defer.

**Trusted or assumed:**

- The accepted documents say what the plan cites; each line reference was
  read at `0eb37570`.
- The plan's seven packages are a decomposition of the seven-part
  definition, not an extension of it; the decision-gate mapping names the
  three gate items (authorization API, audit schema, CHERI mapping) that
  S2 hands to a later plan rather than fills.
- The owner session ran on `claude-fable-5.1` at the responsible human's
  direction for this session; no research agent ran for this plan.

**Unavailable or not run:** no execution of any kind; no generated HTML,
`npm run docs:build`, `./be docs-check`, Chromium render, or flagless
`node docs/check-links.mjs`.

**Not implemented:** `planning/security-model-v1.md` does not exist; no
policy notation, analysis, manifest relation, or trigger evaluation has
been written; nothing under `model/` or any accepted target changed.

## 4. Load-bearing properties

| Property | Where stated | Evidence |
| --- | --- | --- |
| The plan authorizes documentation only, and only if accepted | "Status", "Claim boundary and non-goals", status record `s2_code_change=none`, `s2_model_change=none` | Reading |
| The seven packages map one-to-one onto the accepted definition | "Goal" lists the definition; "Work packages" S2-1 to S2-7 | Reading against `1ac7080f`'s roadmap S2 row |
| Every stop condition returns to the human rather than widening scope | "Stop conditions" 1-5 | Reading |
| The plan neither selects nor pre-empts a runtime mechanism, protected service, or tool | S2-5 ("A result of 'fires' selects nothing"), stop condition 3, Q1, Q4 | Reading |
| The plan is consistent with M01-A | S2-5 uses M01-A's two triggers and the two-case condition verbatim in substance | Reading against `95ef0f6c` |

## 5. Review history and resolved findings

1. **Branch placement.** The plan and packet are on a new branch from the
   development-branch tip, following the S1 and B-series practice; the
   development branch itself was fast-forwarded to `0eb37570` and pushed
   on 2026-10-18 at the responsible human's instruction
   `fast-forward dev to 0eb37570 and push`, which this packet's status
   updates record.
2. **Q1 answered (2026-10-19).** After a discussion of the three Q1
   options (a notation defined in the document; Rocq definitions embedded
   in the document; a Cedar-like surface syntax) and of whether Rego could
   serve, the responsible human answered `Let's go with (A)`: the policy
   is written in a small declarative notation defined in full in the
   document, with no parser or tool. That confirms the plan's default, so
   the plan text at `5ce7827f` is unchanged; the acceptance record, if the
   plan is accepted, carries the answer. The discussion noted, without
   deciding, that Rego fits the offline analysis plane in the
   `cheriot-audit` pattern the implementation plan already names (L416)
   and not the specification role, and that any such tool is an S3 or
   separate decision under S1 row H45 and stop condition 3.
3. **Not resolved, for your judgment:** the plan itself, and Q2 to Q7, in
   particular Q5 (independent review of S2), which the accepted project
   review's option 5 raised and the 2026-10-06 SOP declines by default.

No research agent, separate scope review, or deep security review ran.

## 6. Validation and retained evidence

These ran on 2026-10-18 on the working tree immediately before the commit;
the commit records exactly that content, and the tree was clean afterwards.
They did not run in a fresh checkout.

| Command | Result | Covers |
| --- | --- | --- |
| `git diff --check` | pass | whitespace in tracked changes |
| `grep -nP '[ \t]+$'`, `grep -nP '[^\x00-\x7F]'`, and a `grep` for absolute home and temporary directory prefixes on the new files | no matches | whitespace, ASCII, private locators |
| `node docs/check-links.mjs --tasking-fence-regression` | pass, 8 cases | the owner tasking section's regression cases |
| `node docs/check-links.mjs --tasking-contract` | pass | the owner tasking contract |
| `node scripts/check-doc-sources.mjs --self-test` | pass | the checker's self-tests |
| `node scripts/check-doc-sources.mjs` | pass: `site_markdown=119`, `configured_routes=281` | links, anchors, routes, private locators |
| `umask 0022 && npm run docs:source-check` | pass: `network_events=0`, `generated_tree_changes=0`, `adversarial_cases=34` | the source gate under isolation |

## 7. Recommended review sequence

Read-only commands, from the Beryllium checkout:

```sh
git show --stat 5ce7827f9c2ffc6e0f88568692ab238e5feca49f
git show 5ce7827f9c2ffc6e0f88568692ab238e5feca49f:planning/s2-security-model-plan.md
git diff 0eb37570f9cb901ef994cc10aef8c7890c6134e9 5ce7827f9c2ffc6e0f88568692ab238e5feca49f -- planning/roadmap.md planning/HANDOFF.md
```

1. **"Goal" and "Work packages":** the seven packages against the accepted
   definition in the roadmap's S2 row at `1ac7080f`.
2. **S2-5 and "The decision-gate update":** the trigger evaluation against
   M01-A at `95ef0f6c` and the implementation plan's gate (L970-L979).
3. **"Open questions and defaults":** Q1 to Q7.
4. **"Claim boundary and non-goals" and "Stop conditions".**

To re-run the source checks on the exact commit, use a detached worktree in
the workspace's `worktrees/` container, then `npm ci` and
`umask 0022 && npm run docs:source-check` inside it:

```sh
git worktree add --detach ../worktrees/beryllium-hypervisor/review-5ce7827f 5ce7827f9c2ffc6e0f88568692ab238e5feca49f
```

## 8. Human decision checklist

As presented, the packet asked the human to decide on `5ce7827f`. The
[decision record](#decision-record) above holds that decision; the
checklist is retained as presented.

- [ ] The plan's scope matches the accepted S2 definition and adds nothing
      to it.
- [ ] The seven packages and the decision-gate mapping are the right
      decomposition.
- [ ] The defaults for Q1 to Q7 are acceptable, or you answer them.
- [ ] The stop conditions are the right returns to you.
- [ ] S3, implementation, `model/` changes, and any push stay excluded.
- [ ] Decision: accept `5ce7827f`, request revisions, or defer.

## 9. After the decision

- **Accept:** on your instruction, a follow-up records the acceptance of
  exactly `5ce7827f9c2ffc6e0f88568692ab238e5feca49f` with the instruction
  and date; S2-1 to S2-7 then
  proceed under the plan and end in one exact commit of
  `planning/security-model-v1.md` with its own packet. Nothing is pushed
  unless you say so.
- **Request revisions:** a new commit and a new packet follow; this SHA is
  not treated as accepted.
- **Defer:** the current status stays, and S2 does not start.

**Status:** exact commit `5ce7827f` is responsible-human accepted as the S2
plan as of 2026-10-19, on local branch `beryllium/s2-security-model`;
nothing is pushed. The development branch is at `0eb37570` locally and on
`origin`.

**Next:** S2-1 to S2-7 proceed under the accepted plan and end in one
exact commit of `planning/security-model-v1.md` with its own packet for
your decision.

**Action required from you:** none for the plan.
