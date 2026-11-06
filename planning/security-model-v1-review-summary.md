<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Security model v1 (S2): review summary

This packet supports a responsible-human decision on one exact commit. It
was presented as decision-neutral and not self-approving; the decision
record below holds the outcome.

## Decision record

The responsible human accepted exact commit
`0e3eec8b4fd74003f8cedbf2ca66871c31412624` (parent `3d1b1913`) as security
model v1 on 2026-10-22 with the instruction `accept 0e3eec8b`, given in
reply to this packet's request to accept, revise, or defer that exact
commit. The abbreviation was checked to resolve uniquely to that commit.

- **Scope:** acceptance covers exactly the document text at that commit.
  Sections 1 to 9 are the packet as presented, apart from the outcome rows
  in section 1, the outcome of item 3 in section 5, a note above the
  section 8 checklist, and the closing lines of section 9. The document
  carries its own decision record.
- **Open questions:** V1 to V4 were not answered, so their defaults
  apply, and Part 5's "undecidable" results for the dynamic case stand as
  written.
- **Review note:** before deciding, the responsible human asked where
  registers are covered. The answer: in Part 1 only, by the `vcpu_state`
  class (which names the VS CSRs by reference to "the B7 record") and
  invariant I5; Part 2 declares no `vcpu_state` class, so no policy rule
  or Part 3 analysis covers register state. No revision was requested.
- **Effect:** security model v1 is the accepted statement of Beryllium's
  security properties and planning input to S3. No S3, no Model 0.2
  change, no implementation, no push, and no merge into the development
  branch follow from it.
- **Decision support:** the packet commit `9e793795`, the roadmap refresh
  `c872d239`, and this acceptance-record follow-up are decision support,
  not document content.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `0e3eec8b4fd74003f8cedbf2ca66871c31412624` (tree `78610e065bcdd9e09d37614c01f374d29cf92403`), parent `3d1b1913`, the S2 plan's acceptance record; branch `beryllium/s2-security-model`, from the development branch at `0eb37570` |
| Current status | Documentation only, written under the accepted [S2 plan](s2-security-model-plan.md) (`5ce7827f`) as work packages S2-1 to S2-7; the fast source checks pass; the two policy instances were checked for well-formedness and for their flow relation by a throwaway script (section 6). Recorded outcome: accepted on 2026-10-22 (`accept 0e3eec8b`) |
| Decision requested | Accept the exact commit as security model v1, request revisions, or defer; answer any of V1 to V4 or let the defaults apply. V1 to V4 were not answered; their defaults apply |
| Successor status | S3 (the MVP plan) not started and not authorized; the Model 0.2 changes Part 7 inventories not started; the acceptance authorizes neither; no stop condition fired |
| Publication status | Private repository; the target is on local branch `beryllium/s2-security-model`, unpushed; the development branch is at `0eb37570` locally and on `origin`; no tag, publication, or release |

As presented, the packet asked for the exact target to be accepted,
revised, or deferred; the [decision record](#decision-record) above holds
the outcome.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| Security model v1 | [`security-model-v1.md`](security-model-v1.md) | The seven parts of the accepted S2 definition: objects, invariants, threat model, and TCB (Part 1); the policy notation and two instances (Part 2); analyses A1-A8 (Part 3); the validate decision, the restored pipeline, and the report schema (Part 4); the two triggers against three use cases (Part 5); the dynamic authority ceiling (Part 6); the Model 0.2 change inventory (Part 7) | Specification and definitions only; implements, runs, and proves nothing; selects no mechanism, service, tool, or encoding; changes nothing under `model/` | Is the notation of Part 2, with union across rules and conjunction across permissions, the TE-family specification you intended, and are the two instances the right first instances? |
| Navigation | `planning/.vitepress/config.mts` | Lists the document in the three navigation lists | Site configuration only | None beyond placement |
| Status pages | [`roadmap.md`](roadmap.md), [`HANDOFF.md`](HANDOFF.md), [`project-orientation.md`](project-orientation.md), [`README.md`](README.md), [`glossary.md`](glossary.md), `.github/copilot-instructions.md` | Record the proposed document; changed in this packet's commit, not in the target | Status text only | None |

Exact changed-file inventory:

```text
# git diff --name-status 3d1b1913 0e3eec8b
M	planning/.vitepress/config.mts
A	planning/security-model-v1.md
```

`git diff --stat 0eb37570 0e3eec8b -- model/ include/ virt/ arch/ bringup/ tests/`
is empty.

## 3. Claim boundary

**The commit supports saying:** Beryllium has a proposed security model v1
in which the security properties are specified by a declarative, total,
default-deny policy in the Type Enforcement family with a defined notation
(abstract syntax, concrete syntax, semantics), defined analyses, a defined
relation to the canonical manifest (validate), and a defined authority
ceiling for the dynamic case; the fixed two-domain profile and the
expected first MVP milestone are written as instances; and under M01-A
neither runtime trigger fires for those instances, while both are
undecidable for the dynamic case until a management-request vocabulary
exists.

**Trusted or assumed:**

- The accepted documents cited (Models 0.1 and 0.2 and their evidence, the
  R0 freeze, the B-series records, the implementation plan, S1, M01-A, the
  S2 definition, the S2 plan) say what the document quotes; each line
  reference was read at `0eb37570`, and the two implementation-plan
  references the document makes (threat model v0 at L481-L532; the first
  MVP milestone at L1996-L2001) were re-read after RP-3 moved the text.
- The B2 result's two denials (causes 21 and 23) and the B7 configuration
  (two 64 MiB windows, VMIDs 1 and 2, a pair check that refuses shared
  pages) are as their records state; the document uses them as instances
  of the specification, not as evidence for it.
- The owner session ran on `claude-fable-5.1` at the responsible human's
  direction; no research agent and no independent review ran (plan Q5
  default).

**Unavailable or not run:** no implementation of any analysis; no
machine-checked semantics; no Rocq, C, QEMU, or board execution; no
generated HTML, `npm run docs:build`, `./be docs-check`, or Chromium
render. The throwaway consistency script of section 6 is not retained
tooling and establishes nothing beyond what it checked.

**Not implemented:** everything Part 7 inventories; any management-request
vocabulary (Part 6); any encoding of the policy, labeling, or report; any
protected service; any runtime mechanism; S3.

## 4. Load-bearing properties

| Property | Where stated | Evidence |
| --- | --- | --- |
| The policy semantics is total, deterministic, and default-deny | Part 2, "Semantics" | By definition: `decide` is defined for every argument from a finite rule set, with `deny` otherwise |
| Only one rule form exists, so there is no conflict to resolve; any new form must define its resolution first | Part 2, "Conflict resolution" | Reading |
| Types are identities, not authority; the monitor consults the manifest and mappings, never types, at run time | Part 2, "Labeling"; Part 4, "The pipeline" | Reading; consistent with Model 0.2 and S1 H03 |
| Both instances are well-formed (A1) and their flow relations equal their declared channels (A6) | Part 2 instances; Part 3 A1, A6 | Checked by the throwaway script in section 6: 8 and 6 rules, each with declared types, classes, and permissions; `F = D = {(mgmt_t, prot_t)}` and `{(writer_t, reader_t)}`; no rule targets `monitor_mem_t` |
| B2's denials are instances of the policy, not evidence about the trigger | Part 2, Instance 1; Part 5 | Reading against M01-A and the B2 record (causes 21 and 23) |
| The validate decision leaves Model 0.2's seam and 23 obligations unchanged | Part 4; Part 7 | The inventory lists only additive changes; `model/` is unchanged in the commit |
| Neither trigger fires for U1 or U2; both are undecidable for U3 | Part 5 | Reading; each cell cites its evidence |
| The document selects no runtime mechanism, service, tool, or encoding | "Claim boundary and non-claims"; status record | Reading; plan stop condition 3 did not fire |

## 5. Review history and resolved findings

1. **Line references moved by RP-3.** The first draft cited the first MVP
   milestone at implementation plan L1972-L1977, which was its location
   before RP-3 lengthened section 2.16; the text is now at L1996-L2001,
   and the document was corrected before commit.
2. **Instance consistency.** A throwaway script parsed the two policy
   blocks from the document and checked declaration before use, known
   permissions, nonempty permission sets, the flow relation, and the
   declared-channel relation. Both passed. The script is not retained and
   is not the implementation of A1 or A6; it was a review aid.
3. **Not resolved, for your judgment:** V1 (validate over compile), V2
   (the `domain` class in v1), V3 (the static shared page as non-revocable
   under A5), and V4 (guest memory as `read write execute`); and whether
   Part 5's "undecidable" results for the dynamic case are the right
   record, or whether you want a position taken now. **Outcome
   (2026-10-22):** not answered; the defaults apply, and Part 5 stands as
   written.

No research agent, separate scope review, or deep security review ran.

## 6. Validation and retained evidence

These ran on 2026-10-19 on the working tree immediately before the commit;
the commit records exactly that content, and the tree was clean afterwards
apart from the status-page edits held for this packet's commit. They did
not run in a fresh checkout.

| Command | Result | Covers |
| --- | --- | --- |
| `git diff --cached --check` | pass | whitespace in the committed changes |
| `grep -nP '[ \t]+$'`, `grep -nP '[^\x00-\x7F]'`, and a `grep` for absolute home and temporary directory prefixes on the new file | no matches | whitespace, ASCII, private locators |
| A throwaway Python script over the document's two policy blocks | both well-formed; `F = D` for each; no rule on `monitor_mem_t` | A1, A3's monitor check, and A6 on the two instances, as a review aid only |
| `node docs/check-links.mjs --tasking-fence-regression` | pass, 8 cases | the owner tasking section's regression cases |
| `node docs/check-links.mjs --tasking-contract` | pass | the owner tasking contract |
| `node scripts/check-doc-sources.mjs --self-test` | pass | the checker's self-tests |
| `node scripts/check-doc-sources.mjs` | pass: `site_markdown=120`, `configured_routes=284` | links, anchors, routes, private locators |
| `umask 0022 && npm run docs:source-check` | pass: `network_events=0`, `generated_tree_changes=0`, `adversarial_cases=34` | the source gate under isolation |

No report, ledger, or hash is produced by a documentation-only package; the
commit is the artifact.

## 7. Recommended review sequence

Read-only commands, from the Beryllium checkout:

```sh
git show --stat 0e3eec8b4fd74003f8cedbf2ca66871c31412624
git show 0e3eec8b4fd74003f8cedbf2ca66871c31412624:planning/security-model-v1.md
git diff --stat 0eb37570f9cb901ef994cc10aef8c7890c6134e9 0e3eec8b4fd74003f8cedbf2ca66871c31412624 -- model/
```

1. **Part 2, "Notation" and Instance 1:** the semantics, then whether the
   fixed profile's policy says what R0's resource table and the B2 record
   say.
2. **Part 5:** the two trigger tables, against M01-A's wording in
   `planning/architecture-model-0.1.md`.
3. **Part 3, A6 and A8, and Part 4, "Compile or validate":** the flow
   analysis and the manifest relation, which carry I11.
4. **Part 6 and Part 7:** the ceiling and the change inventory, which are
   S3's and a later plan's inputs.
5. **Part 1:** the invariant table's third column, which states what is
   unproved for B5-B7.
6. **"Open questions and defaults":** V1 to V4.

To re-run the source checks on the exact commit, use a detached worktree in
the workspace's `worktrees/` container, then `npm ci` and
`umask 0022 && npm run docs:source-check` inside it:

```sh
git worktree add --detach ../worktrees/beryllium-hypervisor/review-0e3eec8b 0e3eec8b4fd74003f8cedbf2ca66871c31412624
```

## 8. Human decision checklist

As presented, the packet asked the human to decide on `0e3eec8b`. The
[decision record](#decision-record) above holds that decision; the
checklist is retained as presented.

- [ ] The document fills the seven parts of the accepted S2 definition and
      stays within the accepted plan's work packages and non-goals.
- [ ] The notation and semantics of Part 2 are the specification you
      chose with `revise-adopt` and `Let's go with (A)`.
- [ ] The two instances are correct against the R0 resource table, the B2
      record, and the first MVP milestone's description.
- [ ] The analyses are defined precisely enough to implement twice and
      compare.
- [ ] Validate over compile (V1) is acceptable.
- [ ] The trigger results, including "undecidable" for the dynamic case,
      are the right record.
- [ ] The defaults for V2 to V4 are acceptable, or you answer them.
- [ ] S3, the Part 7 changes, any implementation, and any push stay
      excluded until separately directed.
- [ ] Decision: accept `0e3eec8b`, request revisions, or defer.

## 9. After the decision

- **Accept:** on your instruction, a follow-up records the acceptance of
  exactly `0e3eec8b4fd74003f8cedbf2ca66871c31412624` with the instruction
  and date; security model v1 becomes the accepted statement of the
  system's security properties and planning input to S3, which still needs
  its own direction and plan. Nothing is pushed unless you say so.
- **Request revisions:** a new commit and a new packet follow; this SHA is
  not treated as accepted.
- **Defer:** the current status stays, and S3 does not start.

**Status:** exact commit `0e3eec8b` is responsible-human accepted as
security model v1 as of 2026-10-22, on local branch
`beryllium/s2-security-model`; nothing is pushed. The development branch
is at `0eb37570` locally and on `origin`.

**Next:** S3, the MVP plan, starts only on your direction; merging the S2
branch into the development branch and any push each need an explicit
instruction.

**Action required from you:** none for security model v1.
