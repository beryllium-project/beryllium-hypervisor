<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP plan revision S3-C review summary

This packet presents one decision:
[Plan revision S3-C](mvp-plan.md#plan-revision-s3-c-the-mvp-ladder-and-mvp-1-0-widened-to-interactive-guests-a-first-verification-plan-and-measurement)
of the [MVP plan](mvp-plan.md), **second candidate, exact commit
`27d2e557f069edf8dd714f5ac9b5ccb9b204a801`** (parent `81c5e0b6`, branch
`beryllium/mvp-s3c-plan`). The first candidate, `95c9ab24` (2026-10-31),
was read by three independent design reviews under this packet's section
8 brief and is superseded, never accepted. The second candidate turns the
responsible human's directions of 2026-10-31 into plan text as the first
did (the MVP ladder; MVP 1.0 widened by M7 interactive guests, M8 the
first verification plan, M9 measurement, M10 release candidate 4;
decisions D19 to D22) and answers the reviews' 43 reconciled rows. The
packet recorded the decision below after it was given.

## Decision record

The responsible human accepted exact commit
`27d2e557f069edf8dd714f5ac9b5ccb9b204a801` (parent `81c5e0b6`) as Plan
revision S3-C on 2026-11-01 (13:34 in the human's time zone). The
instruction, given in reply to this packet's request to accept, revise,
or defer that exact commit and to answer Q27 to Q46 or let the defaults
apply, was `note that from now on, we will push changes for the rc3 snapshot as normal deltas, so people can see what is changing. accept 27d2e557, defaults ff + push/` (the trailing `/` a stray key). The
abbreviation was checked to resolve uniquely
(`git rev-parse --disambiguate=27d2e557`).

- **Scope:** acceptance covers exactly the revision's text at that commit
  (`planning/mvp-plan.md`, the section "Plan revision S3-C", whose
  accepted body above it is byte-identical) and this packet's claim
  boundary (section 3): D19 to D22 as amended, the amended stop condition
  1, S3-A.1 item 8, the superseded lines, and **Q27 to Q46 at their
  defaults** (`defaults`), the three the reviews changed (Q27, Q28, Q34)
  and the four they added (Q43 to Q46) included. The first candidate
  `95c9ab24` stays superseded and never accepted; the three reviews stay
  steering input, as section 5 says.
- **What it authorizes:** writing the bounded plans of M7 (interactive
  guests), M8 (the first verification plan), and M9 (measurement), each
  on its own branch from the development branch, in any order or in
  parallel; and M10's plan after those three milestones' results are
  accepted. Nothing else: no implementation, no board command (the COM260
  is in the other project's use until the human says otherwise), no
  accepted-byte, model, or claim-text change (the claim
  pre-authorizations take effect through the milestone plans'
  acceptance), no release-path step.
- **The same instruction directs** the fast-forward of the development
  branch `beryllium/single-hart-runtime-r0` from `44112dec` to the commit
  recording this decision and its push to the private `origin` (the
  branch `beryllium/mvp-s3c-plan`, which holds the development tip by the
  merge `b6e323bd`, is pushed with it), and gives a standing direction on
  the public review snapshot: from now on changes for it are pushed as
  normal deltas, so that people can see what is changing (`mvp/README.md`
  item 107, which records the direction and the one shape question it
  leaves).
- **Since the packet was written:** debt sweeps 4 and 5 were accepted on
  the development branch (2026-11-01) and closed `mvp/README.md` items
  95, 99, 100, 102, and 105 of the items this packet named as waiting
  for direction; 101, 103, and 104 stay open for M8 and M9; the public
  review snapshot was refreshed twice (`6c71fa4c` pushed; `36e2590c`
  made, the human's push pending).

## 1. Decision summary

| Item | Value |
| --- | --- |
| Decision requested | None outstanding; the decision was `accept 27d2e557, defaults ff + push` (the decision record above) |
| Status | **Responsible-human accepted as of 2026-11-01** at exact commit `27d2e557`; the branch holds the development tip (`b53c02a8` by the merge `6cce40fd` when the candidate was written; `44112dec`, debt sweeps 4 and 5, by the merge `b6e323bd` before the acceptance record), and the development branch is fast-forwarded to the acceptance record and pushed on the same instruction |
| What it is | Plan text replacing the first candidate's section at the end of `planning/mvp-plan.md` (813 lines added, 288 removed against the first candidate; the accepted body above line 1142 is byte-identical); no other file changes at the target |
| What it changes | The MVP plan only: the superseded-lines table now has 24 rows (the first candidate's 10, completed); stop condition 1 is amended by name; S3-A.1 gains item 8; stops (a) to (i); Q27 to Q46; M0 to M6's accepted texts, every accepted record, the claim's present text, the board policy's items 1 to 7, and the standing kexec rule are unchanged |
| What acceptance authorizes | Writing the bounded plans of M7, M8, and M9 on their own branches; M10's after those three milestones' results are accepted; nothing else (in force since 2026-11-01) |
| What it does not authorize | Implementation; any board command (the COM260 is in the other project's use); accepted-byte, model, or claim-text changes; the code fixes of `mvp/README.md` items 100 to 104; push, merge, publication, or release steps |
| Strongest validation | Documentation checks only: `node scripts/check-doc-sources.mjs` PASS at the packet commit, `git diff --check` clean, the accepted body unchanged by `git diff`; every fact the reconciliation relies on re-read in the tree (its section 2) |
| Hardware | None run; none claimed |
| Model | Planning, reconciliation, and this packet on the session model (`claude-fable-5.1`); the three reviews on their own models (the Codex CLI's, the Claude Code session's `claude-opus-5-5`, the Copilot CLI session's with two `claude-opus-5.5` research agents); the pin is unchanged |

## 2. Deliverables

| Commit | Content | Role |
| --- | --- | --- |
| `27d2e557` | Plan revision S3-C, second candidate, in `planning/mvp-plan.md`: S3-C.1 why and naming; S3-C.2 the ladder; S3-C.3 M7; S3-C.4 M8; S3-C.5 M9; S3-C.6 M10; S3-C.7 order, lanes, release path, the claim pre-authorizations; S3-C.8 D19 to D22, stop 1 amended, stops (a) to (i); S3-C.9 board policy item 8; superseded lines; Q27 to Q46; what acceptance would authorize; a revision history; the status addendum | **The exact target** |
| `81c5e0b6` | The three review documents, unedited but for a provenance comment ([Copilot CLI](mvp-plan-s3c-review-copilot-cli.md), [Codex CLI](mvp-plan-s3c-independent-design-review.md), [Claude Code](mvp-plan-s3c-review-claude-code.md)); the [reconciliation](mvp-plan-s3c-review-reconciliation.md); `mvp/README.md` items 95 (updated) and 99 to 104 | Decision support: the evidence behind every change in the target |
| `6cce40fd` | The merge of the development tip `b53c02a8` into this branch | So the candidate is written against the accepted state (debt sweep 3 fixed the claim's header and the snapshot template the reviews faulted) |
| `95c9ab24` | The first candidate | Superseded; the commit the reviews read, kept in the branch's history |
| This packet and its registrations (roadmap, planning README, sidebar, handoff, instructions) | Decision support | Not plan content |

## 3. Claim boundary

- The revision claims nothing about the monitor, the board, or any proof.
  It proposes milestones; each needs its own plan and result acceptance.
- Claim-text changes are pre-authorized as a bounded list (S3-C.7), each
  fixed in words by its milestone plan and accepted with it: M7's
  console, guest-software, and operator-boundary sentences; M8's
  narrowing of the required limit **only on a positive result**, naming
  the proved functions, the kind of result, the source, tool, and
  assumptions, with new method terms "C-level contract proof" and
  "bounded model check" (never "bounded proof"); M9's measurement clause
  with content fixed in S3-C.5 (per platform; the self-measurement a
  self-report; loader attribution on the board only by an unmeasured
  U-Boot; SPL, OpenSBI, and U-Boot unmeasured; no key, nonce, freshness,
  or root of trust; the lifecycle and debug state a dated assumption)
  and the firmware residual in the required limit; M10's RC4 metadata.
  The words "chain", "lowest stage", "measured identity", "measured
  boot", "attested", and "secure boot" stay out of the clause: the first
  candidate's suggested phrases passed the forbidden-phrasing matcher,
  which is why the content is fixed in the plan rather than left to a
  check.
- M9's bottom is stated plainly and per platform: the loader's MD5 is a
  checker-held, board-only attribution of the whole boot image, absent in
  QEMU (CRC-32 in the rehearsal); no root of trust is characterized.
  Attestation, with a simulated root scoped to storage and reporting, is
  MVP 2.0's.
- M8 is a first bounded result about named functions under stated
  assumptions, positive or negative; "refinement" is reserved for a result
  that meets S3-C.4's relational target; it is never "formally verified",
  and the recorded tool roles stand.
- Console input is monitor mechanism outside the policy for 1.0 (Q43),
  with a ledger non-claim; the policy notation gains no class.
- LiteBox: the July [runtime sidebar](sidebar-minimal-vs-runtimes.md)'s
  disposition stands until the 2.0 bake-off, which reopens it.

## 4. Load-bearing decisions

| Decision | Content | Where it comes from |
| --- | --- | --- |
| D19 | MVP 1.0 is M0 to M10, a security-research demonstrator ("useful to show" and, bounded, "to trust"); 2.0, 3.0, 4.0 named with focus, contents, and order; the 1.0 decisions later rungs inherit | The human's ladder of 2026-10-31; the comparison; reconciliation rows AL and AK |
| D20 | Measurement first (M9) as a log with registers beside the checker-held loader attribution and the dated platform assumption, never one chain; attestation in 2.0; IMA never, by three testable criteria; policy bound, not measured | `we want to measure and attest, but start with measurement`; `we are not using IMA ever`; rows Y, AA, AB, AG |
| D21 | RC4 is M10's result; a snapshot refresh is a publication act under stop 7 on an instruction naming the exact accepted commit, with the gates recorded | S3-A.3 and S3-B.3; row AM |
| D22 | The model split; M8's specifications drafted from the plans and the claim, frozen by hash, the human their reviewer of record; the three reviews steering input | The human's session direction; rows W, AO |
| Stop 1 amended | Its exception list gains, by name, the Part 1 revisions M7 and M9 carry and, only under Q43's alternative, a console class | Row A, AQ |
| S3-A.1 item 8 | Typing into a running MVP: static session files, the focus bytes, re-gated on hart-0 lines, never during U-Boot, no reset in a session, every keystroke recorded; a banner aborts | Row H |
| Q27 | **Flipped**: no shell and no console grant in the anchor's protected domain; the secret's bytes never appear in a capture | Row G, all three reviews |
| Q28 | **Changed**: a two-byte line-start sequence, the prefix doubled for a literal, a pure parser, a hart-0 focus line, drops counted | Row E, all three reviews |
| Q34 | **Flipped**: `be_mvp_denial_decide` carries the selection; the ring is the second leaf | Row O, two reviews against one (reconciliation 4.1) |
| Q43 to Q46 | New: console-input representation (mechanism); console output model (line mode); input ring topology (dedicated); stage 1's target commit (M8's base, re-proved at RC4) | Rows A, F, B, T |
| Q31, Q33 | Board time refined (the probe counted; one correlation boot folded in); dynamic management in 2.0, the human's spoken list of 2026-10-31 noted | Rows M, AE; the comparison |

## 5. Review history and resolved findings

Three independent reviews of the first candidate, each under section 8's
brief, none reading the others:

| Review | Date | Headline | In the second candidate |
| --- | --- | --- | --- |
| Copilot CLI ([report](mvp-plan-s3c-review-copilot-cli.md)) | 2026-11-01 | Request a revised S3-C while keeping the cut: console authority (F01), the console contract (F02), Q27 (F03), M8's four layers and leaf (F04), the model's relation (F05), identity kinds and the post-link reference (F06), M9's record origins (F07), the claim gate (F08) | Each answered: rows A, E/F/K/L, G, N/O, R, AD, Y/AA, AI |
| Codex CLI ([report](mvp-plan-s3c-independent-design-review.md)) | 2026-10-31 | Five acceptance-blocking defects: the claim gate; "refinement" without a relation; M9's merged chain; the focus premise and Q27; no stable object for M8 to model | Rows AI, N, Y, E/G, T; its ladder order, the three-artifact framing, the licence duties, the NOR collision, and M9's negatives adopted; its Q34, Q42, and Model 0.2 simulation taken as alternatives (reconciliation 4.1, 4.3, 4.6) |
| Claude Code ([report](mvp-plan-s3c-review-claude-code.md); 102 findings) | 2026-11-01 | Fifteen decisions to write into S3-C before acceptance; nine high findings; two reproduced code facts (the forged loader block; the model gate's plural keywords) | The fifteen decisions are in the text (rows A to AQ); the code facts are `mvp/README.md` items 100 and 102, for the human's direction |

The [reconciliation](mvp-plan-s3c-review-reconciliation.md) is the record:
43 rows, 2 facts tables, 6 adjudications, a false-clearance check, and
the findings outside S3-C with their status. **Departures from the
reviews**, for the human's judgment: Q34 flipped against the Codex CLI's
"keep and strengthen"; M8's goal reworded rather than a positive C result
required (Codex) or only negative exits admitted (Claude, Copilot);
stage 1 related to M3's modules rather than simulated to Model 0.2
(Codex); H06's aggregation recorded as answered (against the Codex CLI's
2.0 step); Q42 kept with the reviewer of record rather than the Codex
CLI's per-plan review rule; Q31 refined rather than a separate M9 board
run (Codex). Two findings the reviews made against the tree at
`95c9ab24` (the claim's header naming release candidate 2; the snapshot
README template's hard-coded candidate) were already fixed by debt sweep
3 before this candidate was written; the candidate's base carries the
fix.

## 6. Validation and retained evidence

| Check | Result |
| --- | --- |
| `node scripts/check-doc-sources.mjs` | PASS at `27d2e557` (`site_markdown=158`, `configured_routes=384`) and at the packet commit |
| `git diff 8b7559d2 27d2e557 -- planning/mvp-plan.md` | Every changed line is at or after line 1144, inside S3-C; the accepted body is byte-identical |
| `git diff --check` | Clean |
| The facts the reconciliation relies on | Each re-read in the tree at `95c9ab24` (reconciliation section 2); the `mvp/` sources are the same bytes at the candidate's base |
| Cited line numbers of the accepted body (L113-L115, L213-L239, L250-L254, L316-L322, L566-L589, L629-L644, L677-L680, L738, L794, L883-L893, L967) | Each read back against `planning/mvp-plan.md`, which the development tip did not change |

No build, test, QEMU, proof, or board step applies to a plan revision.
The reviews' external observations (Fedora's Frama-C build, Alt-Ergo's
licence, `clightgen`'s dependencies) are carried as the reviews'
observations with their dates, not re-verified here.

## 7. Recommended human review sequence

Use a detached worktree so nothing local affects what you read:

```sh
git worktree add --detach ../be-s3c-review 27d2e557f069edf8dd714f5ac9b5ccb9b204a801
cd ../be-s3c-review
git diff 95c9ab24 27d2e557 -- planning/mvp-plan.md
```

1. The reconciliation's bottom line and section 4 (the six
   adjudications): these are the judgment calls.
2. S3-C.8 and the questions table: Q27, Q28, Q34 flipped or changed;
   Q43 to Q46 new; stop 1's amendment; item 8.
3. S3-C.3 (M7), with the reconciliation's rows A to M beside it.
4. S3-C.4 (M8), rows N to X; then S3-C.5 (M9), rows Y to AH.
5. S3-C.7's claim pre-authorizations and the superseded-lines table.
6. The three reports themselves, as much as you want; they are unedited.
7. `mvp/README.md` items 99 to 104: your SECURITY.md direction and the
   five code and document items the reviews surfaced, each waiting for
   your direction.

## 8. Brief for the independent review

(Kept as the first candidate's reviewers received it; the three reviews
answered it.)

The responsible human directed a separate review of this revision by a
different agent, with a written report as steering input. The report is
for the human; nothing in it decides anything. What it should read, and
what it is asked:

- **Read:** the revision at `95c9ab24` (section
  "Plan revision S3-C" at the end of `planning/mvp-plan.md`), on its
  own first; then the [comparison](post-rc3-candidates-2026-10-31.md),
  the [snapshot](project-snapshot-mvp-1.0-rc2.md) sections 5, 6, and 8,
  the MVP plan's accepted body (D1 to D18, Scope, Non-goals, Release
  path), `mvp/docs/claim.md`, and S1's rows H06 to H09, H22, H38, H41,
  H57, H58 in [the synthesis](he-to-be-synthesis.md).
- **Ask of the ladder:** is MVP 1.0's cut the right one for "something
  useful", and is anything on 2.0's list a precondition of it? Is the
  2.0/3.0/4.0 placement defensible, and what is missing from the whole
  ladder?
- **Ask of M7:** is console input through the control hart and a
  per-domain input ring the smallest sound design? What does a focus
  sequence on one serial line get wrong? Does a BusyBox shell in the
  protected domain weaken the anchor (Q27)? What should the scripted
  sessions prove?
- **Ask of M8:** is a separate concrete model beside Model 0.2 (Q35)
  the right first step, or a mistake that costs a rewrite later? Is
  `mvp-ring.c` the right pilot leaf (Q34)? CN versus Frama-C/WP versus
  VST on this subset, and the place of bounded model checking (Q36):
  what would you choose and why? Where should annotations live (Q37)?
  Which of Helium's conditional recommendations (H41) should Beryllium
  adopt?
- **Ask of M9:** is a chain that bottoms out in the firmware's MD5 worth
  building in 1.0, and how should the claim say it? Is the
  self-measurement record honest as labelled, or should it go? What
  should the measurement log's format be so that attestation in 2.0 and
  systemd's `pcrlock` model can consume it? What is the right simulated
  root of trust for 2.0 given the lab (JTAG, the ESP32 dongle, GPIO, a
  management chip)? Is anything here IMA by another name?
- **Ask of the whole:** which of Q27 to Q42 has the wrong default; which
  stop condition is missing; which accepted line the revision should
  have superseded and did not; what in it is not readable on its own.
- **Not asked:** to approve, accept, or authorize; to review code (there
  is none for M7 to M10); to assess hardware claims (none are made).

## 9. After the decision

- Accepted (**the outcome, 2026-11-01**): the acceptance record is
  written here and in the revision's decision record and status addendum;
  the M7, M8, and M9 bounded plans may be written on their own branches
  (M8's can start first: it needs no board); the roadmap, handoff, and
  instructions move; this branch, which holds the development tip by
  merge, is fast-forwarded into the development branch and pushed on the
  same instruction. Items 95, 99, 100, 102, and 105 were closed by debt
  sweeps 4 and 5 before the decision; 101, 103, and 104 are M8's and
  M9's.
- Revisions requested: a third candidate on the same branch, this packet
  updated, the second marked superseded.
- Deferred: the branch stays as it is; the development branch's state is
  unchanged.
