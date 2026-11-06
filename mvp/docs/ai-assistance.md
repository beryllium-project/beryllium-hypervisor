<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# AI assistance in the Beryllium MVP 1.0 release candidates

This document discloses the AI assistance in developing MVP 1.0 release
candidate 4, exact commit `d70a8535` (`RC4`, responsible-human
accepted 2026-11-05), over candidate tree `X4`, exact commit `a6eaa885`;
the [claim ledger](claim-ledger.md#release)'s release table names both, and its accepted predecessors, release candidate 1, exact
commit `c5df0cfa`, accepted on 2026-10-29, release candidate 2, exact
commit `3867c66c`, accepted on 2026-10-30, and release candidate 3, exact
commit `89ef04e9`, accepted on 2026-10-31 (the MVP plan, "Release path": "Every
release surface discloses AI assistance"). It follows
[`LLM_POLICY_ALIGNMENT.md`](../../LLM_POLICY_ALIGNMENT.md), the
[M4 plan](../../planning/mvp-m4-plan.md)'s Q7 and "The AI-assistance
disclosure (M4-3)", the [M5 plan](../../planning/mvp-m5-plan.md)'s
"Documents and the claim (M5-4)", and the
[M6 plan](../../planning/mvp-m6-plan.md)'s M6-5. Each statement cites its source in
parentheses: a file with its section or field, or a Git command, run at
`30800dd3` (M4-1's commit) unless the text says otherwise; the statements
about M5 were checked at `154dc810`, the commit M5-4's revision of this
document starts from, and the statements about M6 at `f1bce832`, the
M6-3 merge. Paths are relative to the repository root. Where
this document and a record differ, the record holds. It describes how the
work was done and adds no evidence to the [claim](claim.md).

**In this repository.** This document is published in MVP 1.0's clean
repository, whose history begins at its copy commit (`RELEASE.md` at the
repository's root). The Git commands it cites ran on the private internal
repository's history, which this repository does not hold, and the commit
IDs it names are that repository's. The files it cites under `.github/`,
and the internal session handoff, are that repository's too and are not
part of this one. Section 8 discloses the assistance in the release path's
steps 2 and 3, which made this repository.

## 1. The responsible human

James Morris is the responsible human for Beryllium, the decision-maker on
every plan, revision, and result (section 5), and the sole approver. An AI
system is "an assisting tool, not the author, copyright holder, DCO
signatory, reviewer, or public-release approver" (`LLM_POLICY_ALIGNMENT.md`,
"Purpose").

- **Author and committer.** Each of the 135 commits from the MVP plan's
  base `0096de3e` to `30800dd3`, the MVP range below, names `James Morris
  <jmorris@namei.org>` as both author and committer (`git log
  --format='%an <%ae> | %cn <%ce>' 0096de3e..30800dd3 | sort | uniq -c`).
  These fields record the identity a commit was made under, not who ran
  the command: the assisting session `bd7da407…` (section 2), which made
  the commits from M0-5's completion on, ran `git commit` itself with that
  identity set for the command (that session's command log, outside the
  repository). The 41 commits after `30800dd3` up to `154dc810` (the rest
  of M4, Plan revision S3-A, the M5 plan, and M5-1 to M5-3) name the same
  identity as both (the same command over `30800dd3..154dc810`).
- **Two addresses.** Source files added to the internal repository, this
  document among them, carry `James Morris <jamorris@linux.microsoft.com>`
  in their copyright line, as the accepted runtime plan and the
  source-policy checkers require; `James Morris <jmorris@namei.org>` is the
  preferred identity for Git authorship and DCO sign-offs, and for new
  source in a future clean repository unless its reviewed policy requires
  another. Both identify the same responsible human
  (`LLM_POLICY_ALIGNMENT.md`, "Local authorship rules"). In the clean
  repository, files copied from the internal repository keep their bytes,
  their copyright lines among them; files new there name `James Morris
  <jmorris@namei.org>`, except where a checker binds the old line; and
  every commit is authored and committed as `James Morris
  <jmorris@namei.org>` (the release path's step 2, Q13).
- **Earlier history.** Of the 457 commits reachable from `30800dd3`, 347
  name `jmorris@namei.org`; the other 110, all dated 2026-07-14 to
  2026-08-09, name two other addresses under the same name (108) or a
  synthetic test identity (2) (`git log --format='%ad %an <%ae>'
  --date=short 30800dd3`).

## 2. The assisting system

GitHub Copilot CLI is the assisting system. M4-1's commit ends with its two
trailers (`git log -1 --format=%B 30800dd3`), and the M3 result's commit
with the same two (`git log -1 --format=%B b0a0f352`):

```text
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>
Copilot-Session: bd7da407-7682-492f-afbd-5e610657b601
```

Every one of the 135 commits of the MVP range carries both trailers
(`git log --format=%B 0096de3e..30800dd3 | grep -c '^Co-authored-by:
Copilot'`, and the same with `'^Copilot-Session: '`, each give 135), from
three sessions: `2d1ff5d6…` (2 commits, 2026-10-22: the MVP plan's first
candidate and its packet), `2b567477…` (58, 2026-10-23 and 24: the MVP
plan's revision 1 through part of M0-5), and `bd7da407…` (75, 2026-10-26
to 28: the rest of M0-5 through M4-1)
(`git log --format='%(trailers:key=Copilot-Session,valueonly)'
0096de3e..30800dd3 | sort | uniq -c`). All 457 commits reachable from
`30800dd3` name the assisting system the same way (`git log --format=%B
30800dd3 | grep -c 'Co-authored-by: Copilot'` gives 457). Through
`154dc810` the MVP range holds 176 commits, every one with both trailers,
from the same three sessions, `bd7da407…` now with 116 of them
(`git log --format='%(trailers:key=Copilot-Session,valueonly)'
0096de3e..154dc810 | sort | uniq -c`). The trailer
acknowledges the assisting system in the commit metadata; it does not make
it an author, copyright holder, or signatory (`LLM_POLICY_ALIGNMENT.md`,
"Purpose" and "Local authorship rules").

The models, as the records name them by role:

| Model | Setting | Role | Source |
| --- | --- | --- | --- |
| `claude-opus-5.5` | `max` effort, `long_context` tier | Implementation in M0 to M10: every package that wrote or changed source, tests, tools, proofs, or generated expectations (in M6, the core profile M6-2 and the executor M6-3, each on its own branch, `mvp/README.md`'s "M6-2" and "M6-3" entries; in M7, the guest userland, the input path, the harness, and the model's input-ring module; in M8, the concrete model's tools, stage 1's proofs, the litmus tests, the verifier, and the pilot's arms and their re-run; in M9, the log, the references, and the checker's log module; in M10, the re-proof at the base tree and the tools of the campaign's sessions, the debts, and the licence manifest); in M4 also the drafts of the release surfaces, this document among them, and in M5 their revision for release candidate 2 (M5-4); and, read-only, the steering review of the M5 plan's draft on 2026-10-29, at the responsible human's request | M0 plan, decision record (`accept 4d129808, proceed with implementation using opus-5.5 model`) and status record (`mvp_m0_implementation_model=claude-opus-5.5`); M0 to M3 result records, "Not run by SOP"; M4 plan, Q11; M5 plan, Q13 and "Decision requested"; the M5 plan packet, introduction (`then have opus 5.5 review the plan for steering input`) and section 5; `.github/copilot-instructions.md`, "Model (pinned split, 2026-10-27)" |
| `claude-fable-5.1` | `max` effort | Planning and orchestration: the plans and plan revisions, Revision 1 of security model v1, the review packets and status documents, and the review of the implementation agents' output, line by line where the records say so; in M4 also the line-by-line review of the release surfaces; in M6 also the small follow-ups after each merge (the layout's names, the ledger's pins) and the release surfaces' revision for release candidate 3 (M6-5); in M7 to M9 the plans, the security model's Revisions 2 and 3, the M8 specification (drafted from the plans and the claim, frozen by hash, the human its reviewer of record), the crosswalk, and the packets; in M10 the plan, the release surfaces' revision for release candidate 4 (M10-4), and the integration of the M8 and M9 lines. In the sessions the records name: the MVP plan's revision 1, its acceptance, and the M0 plan; M0's last session; M1, M2, M3, and M4; and M5, whose plan, Plan revision S3-A, and packet were written by the orchestrating session under the same split | MVP plan, revision record (2026-10-23); `.github/copilot-instructions.md`, "Next sequence" (the M0 text) and "Model (pinned split, 2026-10-27)"; M0 to M3 result records, "Not run by SOP"; M3 plan, Q10; M4 plan, Q5 and Q11; M5 plan, Q13; the M5 plan packet, introduction |
| `gpt-5.6-sol` | `max` effort, `long_context` tier; read-only | Automated critique, three times: the M3 plan's first draft; the accepted M3 plan with security model v1 Revision 1's first candidate `32298add`; and the M4 plan's first candidate `91f4a820` | The M3 plan packet, the Revision 1 packet, and the M4 plan packet, section 5 of each |
| `gpt-6-astra` | `max` effort, `long_context` tier; read-only | Automated critique, once: the M9 plan's first candidate `86f1c68b`, at the responsible human's request; its five blockers shaped the accepted second candidate | The M9 plan packet, section 5, and `planning/mvp-m9-plan-review-gpt-6-astra.md` (the review's text, unedited) |

Plan revision S3-C's first candidate was also read by three independent
design reviews the human directed (2026-10-31 to 2026-11-01): this
project's own session, a Codex CLI session, and a Claude Code session,
each kept unedited under `planning/` (`mvp-plan-s3c-review-copilot-cli.md`,
`mvp-plan-s3c-independent-design-review.md`,
`mvp-plan-s3c-review-claude-code.md`) and reconciled into 43 rows
(`mvp-plan-s3c-review-reconciliation.md`); they are steering input, not
decisions, and the records name their tools rather than their models.
The records name no other model. They do not name the orchestrating model
of the sessions between the M0 plan's acceptance and M0's last session,
which this document therefore does not attribute; the repository's earlier
pin, `claude-opus-5.5` for all work, "stands as history for the sessions
that ran under it" (`.github/copilot-instructions.md`, "Model (pinned
split, 2026-10-27)"). The log of session `bd7da407…` also shows a
command-running helper on `gpt-5.6-luna`, used three times on 2026-10-27,
which ran the MVP's `make` checks and one QEMU run, reported their output,
and wrote only build outputs, and the CLI's own utility calls to smaller
models, which wrote nothing (that session's log, outside the repository).

Each `gpt-5.6-sol` critique was the human's call: the first on `have it
reviewed by gpt-5.6-sol for potential steering (you decide what to
incorporate)` with `I will authorize gpt-5.6-sol for this session as a
reviewer` (M3 plan, "Decision requested"), the second on `have the updated
plan reviewed by gpt-5.6-sol` (`planning/HANDOFF.md`, the M3-1 entry), and
the third under the session SOP `ok, SOP for this session is to have
gpt-5.6-sol max long review planning steps` (M4 plan packet, introduction).
Each ran through a one-launch edit of the user-level governance hook's
required model, restored with its SHA-256 unchanged (`4f4c2c87…`; section 5
of each packet). The orchestrating session judged each finding, and the
revised text was the human's to accept (section 5 below).

## 3. What the assistance did

- **Drafting.** Under the accepted plans, the assistance drafted the plans,
  their revisions, the review packets, the acceptance records that quote
  the human's instructions, and the status documents; the `mvp/` source,
  tests, tools, scenarios, and generated expectations; M3's additions under
  `model/`; M4's release surfaces, this document among them; and in M5,
  Plan revision S3-A, the M5 plan, the partition tool, the board tools for
  a boot from reset, the U-Boot rehearsal, and this revision of the
  release surfaces (section 2's sources; `git log --oneline
  6a5f6fed..154dc810`). The plans and results went to the responsible
  human as exact commits to accept, revise, or defer (section 5).
- **Gates.** Within the authorized work packages it ran the host and QEMU
  checks, the evaluators, the kexec rehearsal in QEMU (M0 to M4), the
  U-Boot rehearsal in QEMU that replaced it (M5), and `kernel-repro` (each
  result record, section 6; for M5, `git log -1 3512c280`).
- **Board campaigns, M0 to M4.** It ran the board tools (`k3-preflight`,
  `k3-load-check`, `k3-campaign`, and `board-evidence`) from a development
  machine through the board's Fedora host, which launched every run by
  Linux kexec, reading the operator's serial log output-only and never
  typing at U-Boot (`mvp/README.md`, the sections on M0-5's, M1-5's, M2-6's,
  and M4-5's campaigns; the M1, M2, and release candidate 1 board records'
  `mvp/serial-log-note.txt`). From 2026-10-27 each campaign began only after
  the human confirmed the shared board free (`mvp/README.md`, "M1-5's first
  board campaign and its stop"; for M2, `conform k3 is free, proceed`, and
  for release candidate 1, `k3 is available for you now, proceed`,
  `.github/copilot-instructions.md`, "Next sequence").
- **Board sessions from system reset, M5.** On the responsible human's
  direction of 2026-10-29 (`modify the plan so that the mvp candidate boots
  from system reset. I don't know where those safety rules came from.`,
  with the answers Plan revision S3-A records: automation types at U-Boot
  through the operator's picocom session, every keystroke recorded), the
  board tools type fixed line templates at the board's U-Boot prompt
  through the operator's picocom session in tmux, and run `saveenv` to
  install a `be_`-prefixed boot command for the session, to select each
  image group, and to restore the human's environment at its end; the
  human is present at the install, the restore, and any recovery
  (`planning/mvp-plan.md`, "Plan revision S3-A", S3-A.1 items 3 and 6; the
  M5 plan, "Typing at U-Boot: the console tool (M5-2)", "The session
  protocol (M5-6)", and Q15). The attended characterization (M5-6a) types
  its own templates the same way and runs no `saveenv`. A session's every
  key, prompt, and reset is in its keystroke log and reset table, which its
  board record keeps under `mvp/session/` (`mvp/tools/k3-console.sh`;
  `mvp/tools/evidence.py`), and release candidate 2's evidence record
  states what was typed (the M5 plan, M5-7).
- **The partition.** The responsible human ran the partition tool,
  `mvp/tools/k3-make-partition.sh`, with `--apply` on the board on
  2026-10-30, which made the ext4 partition labelled `beryllium` from which
  U-Boot loads the images; automation does not run it (the M5 plan,
  decision record and "The partition tool (M5-1)": "no automation runs
  it"; `git log -1 f3a04a86`, whose message records that run's result).
- **kexec.** The responsible human's standing rule of 2026-10-29, `no more
  kexec unless I approve it`, clarified `no more kexec means don't use
  this from here, unless it is truly needed for something`, holds from M5
  on: M5-2 removed the kexec loader and the kexec rehearsal from the MVP
  line's tools, and release candidate 1's board records, made by Linux
  kexec, are history (`planning/mvp-plan.md`, S3-A.1 item 2; `git log -1
  6252e51b`).
- **Resets.** In M0's campaigns the human made every reset (`mvp/README.md`,
  the M0-5 entry). The M1 plan made the `k3ctl` remote reset an opt-in of
  the board tools, `K3_RESET=k3ctl`, accepted with the plan (the M1 plan,
  "The remote reset" and decision record). In M5 every reset is the
  opted-in client's or the human's, and the tools open the dongle's port
  only under the M5 plan's port-open rule (the M5 plan, "Resets and the
  dongle" and Q14). Every `k3ctl` reset of M1 to M4:

| Date (UTC) | Resets | How | On | Source |
| --- | --- | --- | --- | --- |
| 2026-10-26 | 1, the reset's first use | by hand | the human's request to run it | M1 plan, "Base and inputs" |
| 2026-10-27 | 5, M1's first campaign | the tools | the human's confirmation that the board was free | `mvp/README.md`, "M1-5's first board campaign and its stop" |
| 2026-10-27, 17:45 | 1, the board halted by that campaign's stop | by hand | `accept B, proceed` | the same section |
| 2026-10-27 | 3, after three unplanned `two-guests` runs | the tools | within the confirmed board access, by an invocation without `SCENARIO=te-poc`, outside the plan's procedure; the runs are set aside, not evidence | `mvp/README.md`, open item 45 |
| 2026-10-27 | 6, M1's second campaign | the tools | `accept B, proceed` | `mvp/results/20261027-com260-m1b/mvp/resets/` |
| 2026-10-28, 02:44:32 | 1, after M2's first campaign stopped | by hand | `remedy=A, reset_board=true` | `mvp/README.md`, "M2-6's first board campaign and its stop" |
| 2026-10-28 | 6, M2's second campaign | the tools | `conform k3 is free, proceed` | `mvp/results/20261028-com260-m2a/mvp/resets/` |
| 2026-10-28, 06:05:31 | 1, after a boot without network | by hand | `action=reset-resume, extra_reset_rule=true` | `mvp/README.md`, open item 60; the M2 record, decision record |
| 2026-10-29, 17:06:55 | 1, before release candidate 1's campaign, the board on another project's one-shot kernel | by the assisting session, the human asked and unavailable | `k3 is available for you now, proceed` | `planning/mvp-m4-result-review-summary.md`, section 3, departure 1; `mvp/README.md`, "M4-5's board campaign" |
| 2026-10-29 | 11, release candidate 1's campaign | the tools | the same instruction | `mvp/results/20261029-com260-rc/mvp/resets/` |

The three retained board records with the tools' resets hold 23 reset
records, six, six, and eleven, each beside `originals.sha256` (`ls` of the
three `mvp/resets/` directories). The records state the resets made by
hand in the passive voice ("made by hand … on the responsible human's
direction", `mvp/README.md`, open item 60); the command log of session
`bd7da407…` shows that it issued each of those four `k3ctl reset`
commands itself, the first at the human's request to run the client. M5's
resets are in its sessions' records (above).

- **Pushes and fast-forwards,** each on an instruction
  (`planning/HANDOFF.md` and `.github/copilot-instructions.md`, the entry
  of each date):

| Date | Instruction | Effect |
| --- | --- | --- |
| 2026-10-22 | `merge & push, start S3` | the development branch fast-forwarded to `0096de3e` and pushed |
| 2026-10-23 | `sure. update that, then proceed with (a) and continue development` | the development branch fast-forwarded to `1fb46419` and pushed with `beryllium/s3-mvp-plan` |
| 2026-10-24 | `push, I will work on this later when k3 is available` | `beryllium/mvp-m0` and `beryllium/mvp-m0-plan` pushed as a backup |
| 2026-10-26 | `proceed` (form answers `ff-dev`, `push`, `m1-plan`, `k3ctl`) | the development branch fast-forwarded to `6f7b6e7c` and pushed with `beryllium/mvp-m0` |
| 2026-10-27 | `push current work` | `beryllium/mvp-m1` and `beryllium/mvp-m1-plan` pushed as a backup |
| 2026-10-27 | `approve ff84533c and revisions, accept your recommendations, authorize proceeding per those` | the development branch fast-forwarded to `ccf70a3d` and pushed with `beryllium/mvp-m1` |
| 2026-10-28 | `approve 1 & 2. proceed` | the development branch fast-forwarded to `50b77c00` and pushed with `beryllium/mvp-m2` and `beryllium/mvp-m2-plan` |
| 2026-10-28 | `push all work`; `then proceed with (1) and (2)` | `beryllium/mvp-m3` and `beryllium/mvp-m3-plan` pushed; the development branch fast-forwarded to `fb8accc9` and pushed |
| 2026-10-29 | `no worries on the other project, correct decision. accept c5df0cfa, commit & push, I will review in detail.` | `beryllium/mvp-m4`, through release candidate 1's acceptance record and the operator's walkthrough, and `beryllium/mvp-m4-plan` pushed as a backup; the development branch unchanged |

The records state each push and its instruction
(`planning/mvp-m4-result-review-summary.md`, decision record, for the last
row). The command log of session `bd7da407…` shows that it issued the
`git push` commands of the last six rows itself; the earlier sessions'
logs were not consulted. No M5 branch has been pushed (`git for-each-ref
refs/remotes/origin`, 2026-10-30): the M5 plan authorizes no push, merge,
or tag (the M5 plan, decision record).

## 4. What the assistance never did

- **Sign.** No commit message carries `Signed-off-by`: `git log --all
  --format=%B | grep -c Signed-off-by` gives 0 over every ref (522 commits
  on 2026-10-28, and 570 on 2026-10-30), and `git log --format=%B
  fb8accc9~200..30800dd3 | grep -c Signed-off-by` gives 0 over 231
  commits. Only James Morris may add one, after his own review and DCO
  assessment (`LLM_POLICY_ALIGNMENT.md`, "Binding upstream requirements").
- **Accept or approve.** Every acceptance in section 5 is the human's
  instruction, given in reply to a packet's request to accept, revise, or
  defer an exact commit (each record's decision record). A packet must not
  infer acceptance, sign for a human, push, tag, publish, or start
  dependent work (`.github/copilot-instructions.md`, the
  `human-review-summary` SOP).
- **Publish.** It created no public repository, selected nothing to
  migrate, and made no tag or release; the repository is private, its
  public release is blocked, and automation may not create or populate a
  public repository, select what migrates, or archive this one
  (`LLM_POLICY_ALIGNMENT.md`, "Purpose" and "Future clean public
  repository"; the MVP plan, "Release path"; the M4 plan, decision record).
- **Touch the board or push without direction.** Each reset and push in
  section 3 follows the direction named there. From 2026-10-27 the board
  was reserved: "Do not touch the K3 without the responsible human's
  confirmation" (`planning/HANDOFF.md`, the direction of 2026-10-27),
  renewed on 2026-10-28 as "no board access without the human's
  confirmation" (`.github/copilot-instructions.md`, "Next sequence"); M4's
  campaign waited on that confirmation (the M4 plan, Q2 and stop condition
  7), and M5 issues no board command before the human has created the
  partition and confirmed the board free (the M5 plan, decision record).
  The departures from a plan's board procedure are the three unplanned
  runs of section 3 and the reset before release candidate 1's campaign
  (`planning/mvp-m4-result-review-summary.md`, section 3, departure 1).
- **Act as the reviewer of record.** The `gpt-5.6-sol` critiques, the
  `claude-opus-5.5` steering review of the M5 plan's draft, and the
  orchestrating model's reviews are automated analysis for steering: the
  first critique was asked for "for potential steering (you decide what to
  incorporate)" (M3 plan, "Decision requested"), the M5 review "for
  steering input" (the M5 plan packet, introduction), and the M4 plan calls
  model critiques "automated analysis for steering" (M4 plan, "The
  AI-assistance disclosure (M4-3)"). The review of record is the responsible
  human's review and decision on each exact commit (section 5). No result
  was reviewed by another model (the result records, "Not run by SOP"; the
  M4 plan, Q5).

## 5. The milestones and their acceptances

Each instruction is verbatim from the record's decision record, which also
checks that the abbreviation resolves to the exact commit:

| Decision | Exact commit | Date | Instruction | Record |
| --- | --- | --- | --- | --- |
| The MVP plan (S3), revision 1 | `93967fbac926b4fdfdfe636df4d07e8926b625b7` | 2026-10-23 | `accept 93967fba` | `planning/mvp-plan-review-summary.md` |
| The M0 plan | `4d129808979cb54b7e0a7cc0b3e79d39533e0b9c` | 2026-10-23 | `accept 4d129808, proceed with implementation using opus-5.5 model` | `planning/mvp-m0-plan-review-summary.md` |
| The M0 result, with Plan revisions M0-A, M0-B, and M0-C | `b266972563a39b0687ba2ac8c5b4cb943f3c766a` | 2026-10-26 | `accept b26697` | `planning/mvp-m0-result-review-summary.md` |
| The M1 plan | `7b2c055c1587f9582812a575b296cd625746662b` | 2026-10-26 | `accept 7b2c055c` | `planning/mvp-m1-plan-review-summary.md` |
| The M1 result, with Plan revisions M1-A and M1-B | `ff84533cb3c13d89063be77652575347c2a82757` | 2026-10-27 | `approve ff84533c and revisions, accept your recommendations, authorize proceeding per those` | `planning/mvp-m1-result-review-summary.md` |
| The M2 plan | `854a54152502c4c9a14fe2d1897d907a358a8251` | 2026-10-27 | `accept 854a5415 , gpl 2.0 only ok` | `planning/mvp-m2-plan-review-summary.md` |
| The M2 result, with Plan revision M2-A | `18d552bc4cf3a463bc4dc491e5e346989e5a521c` | 2026-10-28 | `accept 18d552bc` | `planning/mvp-m2-result-review-summary.md` |
| The M3 plan | `c2c249f4c3d364590d2e505a4f6fb5e65456ff81` | 2026-10-28 | `accept c2c249f4` | `planning/mvp-m3-plan-review-summary.md` |
| Security model v1, Revision 1 (M3-1) | `019cca64971d2399faba3d768d6f5b1fc9145198` | 2026-10-28 | `accept 019cca64` | `planning/security-model-v1-revision-1-review-summary.md` |
| The M3 result | `b0a0f352d7969a8f8cf28cf0d25b89fc372e70f2` | 2026-10-28 | `6000 per lane, so 12,000 combined soft limit. accept b0a0f352` | `planning/mvp-m3-result-review-summary.md` |
| The M4 plan, with M4 authorized | `0d02df725541e4e8f93b3fc3de002358827aa1da` | 2026-10-28 | `accept 0d02df27, authorize M4`, read as `accept 0d02df72`: `0d02df27` matches no object, and its prefix `0d02df` resolves only to this commit | `planning/mvp-m4-plan-review-summary.md` |
| The M4 result, MVP 1.0 release candidate 1, with Plan revision M4-A | `c5df0cfae26ce5529cd1ef112911063fcf5b56d8` | 2026-10-29 | `no worries on the other project, correct decision. accept c5df0cfa, commit & push, I will review in detail.` | `planning/mvp-m4-result-review-summary.md` |
| Plan revision S3-A of the MVP plan, then the M5 plan, with M5 authorized | `0d134bbc49377576b961989831a02c068b479355`, then `0066794dbec22807d46cc274f2ad00fb79b555ae` | 2026-10-29 | `accept 0d134bbc and 066794d, authorize m5`, read as `0066794d`: `066794d` matches no object, and `0066794d` resolves uniquely to the M5 plan | `planning/mvp-m5-plan-review-summary.md` |

Release candidate 2's commit is the responsible human's to accept, revise,
or defer at M5's end, and this document is part of what that review covers
(the M5 plan, "Work packages", M5-7); release candidate 1's acceptance
stands as history and is not reopened (the M5 plan, Q16).

## 6. For a Linux submission

Linux's `coding-assistants.rst`, at the revision `LLM_POLICY_ALIGNMENT.md`
checked on 2026-10-31 (`36aad21d50d1`), requires the responsible human's
review of AI-generated code, a human `Signed-off-by` for the Developer
Certificate of Origin, and full human responsibility, and AI agents must
not add `Signed-off-by` tags; its `generated-content.rst` asks that the
cover letter and changelog say what tools were used, their inputs or a
summary of the prompts and the assistance, which portions they affected,
and how the submission was tested (`LLM_POLICY_ALIGNMENT.md`, "Binding
upstream requirements"). The `Assisted-by` tag that the revision first
checked (2026-07-16) required was reduced to `Assisted-by: LLM` upstream on
2026-08-03 and removed on 2026-10-14; the policy document's "History of the
attribution rule" records it. That is the destination's rule, and it is not
applied here: the MVP range's commits carry the trailers of section 2, no
`Assisted-by` tag, and no `Signed-off-by` (`git log --format=%B
0096de3e..30800dd3 | grep -c '^Assisted-by:'` gives 0, as it does over
`0096de3e..154dc810`; section 4). Eight earlier commits, of 2026-07-16 to
18, carry `Assisted-by: GitHub-Copilot-CLI:gpt-5.6-sol` tags (`git log
--format=%B 30800dd3 | grep '^Assisted-by:'`), the rule of their day. A
patch derived from this work would carry the disclosure in its cover letter
and changelog in the form above, this document being its source, with James
Morris's own `Signed-off-by` and no `Assisted-by` tag unless the
destination's policy at that time asks for one (`LLM_POLICY_ALIGNMENT.md`,
"Binding upstream requirements").

Every file under `mvp/` with a license line is `GPL-3.0-only` but the guest
module `mvp/guest/mgmt/be-mgmt.c`, a `GPL-2.0-only` test input built
against the guest kernel (`git ls-files mvp | xargs grep -h -o
'SPDX-License-Identifier: [A-Za-z0-9.-]*' | sort | uniq -c`; the M2 plan,
decision record). Linux is `GPL-2.0-only`, so current Beryllium
implementation text must not be submitted directly for inclusion, and any
in-tree work needs a separate licensing and provenance decision
(`LLM_POLICY_ALIGNMENT.md`, "License boundary").

## 7. Scope of this disclosure

This document covers the MVP 1.0 release candidates' development history
in the private internal repository, as their plans and records state it, from the MVP
plan's first candidate (2026-10-22) to M4-3, the commit that added this
document, and, as M5-4 revised it for release candidate 2, through
`154dc810`; the plans and records are the source of truth (the M4 plan,
"The AI-assistance disclosure (M4-3)"; the M5 plan, "Documents and the
claim (M5-4)"). M4-4 to M4-6 ran under the same model split (the M4 plan,
Q11), and the M4 evidence record and packet, written at M4-6, record them;
M5-5 to M5-7, release candidate 2's characterization, board session,
gates, and packet, run under it too (the M5 plan, Q13), and its evidence
record and packet record them. The accepted work the MVP builds on, the
R-series core whose bytes it keeps, the B-series bring-up it was ported
from, the S1 synthesis, and security model v1, carries the same trailer
(section 2) and is not itemized here. What source, artifacts, and history
migrate to a clean public repository, and in what form, is the
responsible human's decision at the release path's step 2; nothing here
selects or publishes anything (the MVP plan, "Release path";
`LLM_POLICY_ALIGNMENT.md`, "Future clean public repository").

## 8. The release path's steps 2 and 3

This repository was made under the release path's steps 2 and 3 (the MVP
plan, "Release path"; the step 2 selection,
`planning/mvp-release-step-2.md`; the step 3 plan,
`planning/mvp-release-step-3-plan.md`), in one Copilot CLI session,
`c9f9a152-50f1-4e28-a3c6-6b0865b78703`. Every commit of this repository
carries that session's `Copilot-Session` trailer beside the
`Co-authored-by: Copilot` one (`git log
--format='%(trailers:key=Copilot-Session,valueonly)'`). The owner session
and its sub-agents ran Claude Opus 5.5 (`claude-opus-5.5`), the
sub-agents at `max` effort with the `long_context` tier (the step 3 plan,
section 5).

| Work | Made by | Under |
| --- | --- | --- |
| Step 2's proposal of what migrates, and its review packet | A sub-agent of the owner session; reviewed by the owner session | The form answer `run=both_lanes` (2026-11-05) |
| The selection | The responsible human | `accept 38fa3a08` (2026-11-06) |
| Step 3's plan and its review packet | A sub-agent of the owner session; reviewed by the owner session, whose review notes are part of the record | `ff + push, write the step 3 plan, create the clean repo` (2026-11-06) |
| The plan's acceptance | The responsible human | `accept 6944d7b4` (2026-11-06) |
| The internal tools that copy, scan, and record this repository (in the internal repository) | A sub-agent; reviewed by the owner session | The plan's acceptance |
| The copy commit | The owner session, running the tools' `copy` command | The plan's acceptance |
| The scans, gitleaks among them, and the proposed classification rules | The owner session | The plan's acceptance |
| The classification of every finding | The responsible human | `classify as proposed` (2026-11-06) |
| The adaptations' texts: A6, A1, A7, and A8 | The owner session | The plan's acceptance |
| The adaptations' code: A2, A3, A4, and A5 | A sub-agent; each commit reviewed by the owner session | The plan's acceptance |
| The recheck of the Linux kernel's AI and patch-process documents (the plan's Q10) | The owner session | The plan's acceptance |
| Approving the exit commit, signing off, approving the public commit and its tag, and publishing | The responsible human alone | Each its own instruction |

No AI system selected what migrated, classified a finding, approved a
commit, added a `Signed-off-by`, or published anything
(`LLM_POLICY_ALIGNMENT.md`, "Beryllium public GitHub release
boundary").
