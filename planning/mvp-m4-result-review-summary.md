<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M4 result review and acceptance record

This packet presents the result of M4, "Release candidate", the last
milestone of the accepted [MVP plan](mvp-plan.md): MVP 1.0 as one exact
commit with its claim, required limit, and forbidden phrasings, a
checked claim ledger, a researcher guide, an AI-assistance disclosure,
the clean evidence of the pinned evaluators at the candidate tree, and
one release-candidate board campaign at the candidate's images. It was
implemented under the accepted [M4 plan](mvp-m4-plan.md), whose
[decision record](mvp-m4-plan.md#decision-record) holds its
authorization, and under the plan's
[revision M4-A](mvp-m4-plan.md#plan-revision-m4-a-the-board-record-s-identifying-strings),
directed by the responsible human at stop condition 9 and presented
here for exact-commit acceptance with the result, as the plan requires.
The plan's erratum 1 (the new-code soft limit re-set to 2,000 lines) is
recorded in the plan's acceptance record. It also records the
responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`c5df0cfae26ce5529cd1ef112911063fcf5b56d8` (the release-candidate commit `R`,
parent `d42b9ec0a6d2f9f32d66ec2a983018e802b2d537`, the candidate tree `X`; tree
`69c04610`) as the M4 result and the MVP 1.0 release candidate on
2026-10-29, with Plan revision M4-A as implemented. The instruction,
given in reply to this packet's request to accept, revise, or defer
that exact commit, was `no worries on the other project, correct
decision. accept c5df0cfa, commit & push, I will review in detail.`
The abbreviation was checked to resolve uniquely to that commit
(`git rev-parse --disambiguate=c5df0cfa`). The same instruction directed
committing this record and pushing the work to the private `origin`
(below), and asked for an operator's walkthrough of the release
candidate, which is [`mvp-rc-walkthrough.md`](mvp-rc-walkthrough.md).

- **Scope:** acceptance covers exactly that commit and the claim boundary
  in section 3, the four departures of section 3 included (the human's
  words on the first: `no worries on the other project, correct
  decision`). Sections 2 to 8 are the packet as presented, apart from a
  note above the section 8 checklist. Section 1's status rows and the
  closing lines of section 9 now show the outcome. The decision itself
  is recorded only here and in the plan's status record.
- **Decision support:** packet commit `8d2c5033` and this
  acceptance-record follow-up are decision support, not implementation.
- **Plan revision M4-A** is accepted as implemented: the board record's
  writer redacts an ssh user-and-host target to `<board-ssh>` and an
  IPv4 literal to `<ip>`, `identifying()` refuses what the ledger's
  privacy rule finds, and `K3_RECORD_TITLE` names the record; no
  monitor source, image, or accepted record changed. The accepted plan's
  text at `0d02df72` is not edited; the revision is appended to it, and
  its status record is updated to match.
- **The release path:** this acceptance is step 1 of the MVP plan's
  "Release path". Steps 2 to 7 (the responsible human's selection of
  what migrates; the clean public repository; the gates' re-run there as
  a new exact commit; the human's approval of that commit and its tag;
  publication; the internal repository's archive) each need their own
  explicit instruction, and none follows from this acceptance
  (`LLM_POLICY_ALIGNMENT.md`; S1 H48). Any merge of `beryllium/mvp-m4`
  into the development branch needs its own instruction.
- **Push (2026-10-29, the same instruction):** `beryllium/mvp-m4`,
  through the commit that records this acceptance and the walkthrough,
  and `beryllium/mvp-m4-plan` (`4e10fca3`) are pushed to the private
  `origin` as a backup for the human's detailed review. The development
  branch `beryllium/single-hart-runtime-r0` stays at `fb8accc9` locally
  and on `origin`; the local branch `beryllium/mvp-m4-wip-20261029` is
  not pushed.
- **Evidence status:** the board runs are diagnostic bring-up evidence
  for one board, one firmware identity, and one host kernel, at the
  candidate's images. Acceptance adds no hardware validation, no
  qualification, and no formal-verification claim, and makes no
  security claim beyond the required limit of `mvp/docs/claim.md`: the
  denials are the declared, tested accesses; the measurement is a local
  identity; isolation beyond the declared pages is by construction only.
  It does not tag, publish, or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `c5df0cfae26ce5529cd1ef112911063fcf5b56d8` (tree `69c04610`), the release-candidate commit `R`, parent `d42b9ec0a6d2f9f32d66ec2a983018e802b2d537`, the candidate tree `X` (tree `51f304d7`), on branch `beryllium/mvp-m4` from the M4 plan's acceptance record `4e10fca3`. Comparison base: `4e10fca3`, over the accepted plan `0d02df72` on the development branch's tip `fb8accc9`. `X` holds every source change of M4 (M4-1 to M4-4's tools and surfaces, Plan revision M4-A); `R` adds the two retained records, the ledger rows that cite them, the rendered table, the [evidence record](mvp-m4-evidence.md), and the Git attribute the retained console captures need, and nothing else (`git diff --stat d42b9ec0 c5df0cfa -- mvp ':!mvp/results' ':!mvp/docs/claim-ledger.json' ':!mvp/docs/claim-ledger.md'` is empty). |
| Current status | Implemented, checked on the host and in both pinned evaluators, and run on the board. At `X`, from this checkout clean at `X` on `l1` (2026-10-29, 08:42 to 08:59 UTC), the seven gates of pass criterion 4 pass: the lock, `./mvp/mvp check`, `./mvp/mvp evaluate` (247 of 247 images identical between the host and the evaluator), the six kexec rehearsals, `kernel-repro` (15 outputs identical), `./be model-check`, and `./be evaluate`; `rc-record` made `mvp/results/20261029-rc/` (422 files) from them. On the responsible human's confirmation that the K3 was free (`k3 is available for you now, proceed`), the release-candidate board campaign ran at `X`'s images (17:11 to 17:37 UTC): the preflight, the two load checks, and eleven RAM-only `kexec_load` runs on the COM260, each judged by the capture checker and each followed by the tools' `k3ctl` reset; eleven of eleven as declared (`two-guests` three GCC and one Clang with M0's counts, `payload` failing as declared; `te-poc` three GCC and one Clang with M1-B's counts, `reader-write` and `no-inject` failing as declared), no hand reset, no stop; `mvp/results/20261029-com260-rc/` (123 files) is its record. `anchor` was not run: `X`'s four `anchor` board images are byte-identical to the accepted M2-A record's (Q2's rule). `claim-ledger.py check` passes at `R` (`checks=9 claims=34 boundary=12`; the privacy rule over 549 record files). Responsible-human accepted on 2026-10-29 (instruction `accept c5df0cfa, commit & push, I will review in detail`), with Plan revision M4-A. |
| Decision requested | Accept exact commit `c5df0cfa` as the M4 result and the MVP 1.0 release candidate, which also accepts Plan revision M4-A as implemented; or request revisions; or defer. The MVP claim's wording was fixed by the plan's acceptance (Q6) and is published unchanged in `mvp/docs/claim.md`. Recorded outcome: accepted, with the revision; the human's detailed review follows on the pushed branch. |
| Successor status | As presented and after the decision: not started and not authorized: every release-path step after the first (the selection of what migrates, the clean public repository, a tag, the gates' re-run there, publication, the archive; MVP plan "Release path" steps 2 to 7); any merge of `beryllium/mvp-m4` into the development branch; any push; any change to a monitor source, a guest input, a scenario, `model/`, or an accepted document's text; root `Makefile`/`be`/`scripts/check-be.sh` integration; development-kernel/BSP selection. Acceptance of `R` is the release path's step 1 and starts no other step. |
| Publication status | Private repository. As presented, `beryllium/mvp-m4` and `beryllium/mvp-m4-plan` were local and unpushed; on the acceptance instruction both are pushed to the private `origin` (the decision record). The development branch `beryllium/single-hart-runtime-r0` is at `fb8accc9` locally and on `origin`; any merge needs its own instruction. No tag, publication, or release. |

As presented: please review exact commit `c5df0cfa` and accept it,
request revisions, or defer. Outcome: accepted, with Plan revision
M4-A; see the [decision record](#decision-record).

## 2. Deliverables

| Deliverable | Paths | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| The claim (M4-1, `30800dd3`) | `mvp/docs/claim.md` | The MVP 1.0 claim byte-equal to the plan's fixed text, the required limit, and the forbidden phrasings as the list's single source (11 literals inherited, 24 added in 14 groups, 3 conditionals, 2 review items) with the matching rule | A release surface; the plan's text, accepted at `0d02df72` | Is the published text the plan's, and does the required limit say everything the records need it to? |
| The claim ledger and its checker (M4-1; rows at `R`) | `mvp/docs/claim-ledger.json`, `mvp/docs/claim-ledger.md` (rendered), `mvp/tools/claim-ledger.py` (694 lines), the `claim-ledger-check` target in `./mvp/mvp check` | 34 claim rows (the MVP plan's eight method-per-claim rows; the claim's clauses; M3's rows; the platform facts, marked historical; the reproducibility rows; the M0 to M2 campaigns; C-29 to C-34 for the two release-candidate records), 76 evidence artifacts each with its SHA-256 and `evidence_source_commit`, 12 unproved-boundary items, the 2 review items; the method vocabulary has no "verified", "hardware validation", or "formal verification"; `check` verifies the schema, the vocabulary, every hash, every commit (on the host), the rendering, the guide's commands against `mvp help`, the phrasing rules, the privacy rule, and the headers; a seeded self-test of 21 mutations and 5 variants | Documents and records only; no monitor claim beyond the records' | Does every row's method term match its evidence, and does every non-claim bound what the records cannot show? |
| The researcher guide (M4-2, `c0097a4c`, `9ac01ff5`) | `mvp/docs/guide.md` (1,055 lines) | Nine sections: what this is, build, QEMU, the board, write a scenario (what is data and what is a source change, named list by list), the authority report, a bundle and a board record, the evaluator, where the rest is; 19 wrapper command words each in `./mvp/mvp help` | Exercises only what the harness implements; links to the claim rather than restating it | Does section 5 keep a reader from believing two data files add a scenario? |
| The disclosure (M4-3, `90b6b4a5`) | `mvp/docs/ai-assistance.md` (275 lines), `mvp/README.md`'s title and opening, the root `README.md`'s pointer | The responsible human as author, committer, decision-maker, and sole approver; the assisting system, the models by role and milestone, the `Co-authored-by` trailers; what the assistance did, including the recorded commands it executed on direction (board campaigns with the opted-in `k3ctl` reset, the by-hand resets of M1 and M2, the pushes); what it never did; the milestones' acceptances; the Linux `Assisted-by` rule as the destination's | Every statement cited to a plan or record field or a Git command; four statements cite the assisting session's command log, which is outside the repository | Are the statements about who issued which command acceptable as cited, and is "automated critique, not review" the right description of the `gpt-5.6-sol` passes? |
| The release-candidate record tool (M4-4, `0a968bf0`, `ca322220`) | `mvp/tools/rc-record.py` (591 lines), `./mvp/mvp rc-record`, the `rc-record-check` target | The record of the seven gates from explicit inputs each checked to name `X` (the bundle, the evaluator record and its image identity against the closure and `Containerfile` at `X`, the model evidence host and evaluator, the rehearsals, `kernel-repro`, the seven gate logs with their PASS lines and times); never a "latest" directory; every text rewritten and scanned; a 21-mutation self-test | A record tool; it runs nothing an input names | Does the record bind every gate to `X` without a gap? |
| Plan revision M4-A (`0b2ac6fa`) | `mvp/tools/evidence.py` (+144), `mvp/tools.mk`, `mvp/mvp`, `mvp/tools/make-control.py`, `mvp/tests/run-tool-dry-run.sh` | The board record's writer redacts an ssh user-and-host target to `<board-ssh>` and an IPv4 literal to `<ip>`; `identifying()` refuses what the ledger's privacy rule finds; `K3_RECORD_TITLE` replaces the fixed M2 title; six self-test cases and a dry-run case; the accepted M0 to M2 records are not edited | The board tools' record writer only; no monitor or image change | Does the rule redact exactly the board's strings and nothing a record needs (versions, digests, the guest's banner)? |
| The gates record (M4-4, in `R`) | `mvp/results/20261029-rc/` (422 files) | `rc.txt` with `X`, its tree, the host's OS and architecture, the lock's and closure's SHA-256, and each gate's PASS line and times; the host bundle; the evaluator record with `compare-images.txt`; the model evidence host and evaluator with the evaluator's logs; the six rehearsals; `kernel-repro.txt`; `MANIFEST.sha256` | Made against `X` from this checkout clean at `X`; no host, user, or address in it | Does `rc.txt` show every gate PASS with times that follow the plan's order? |
| The board record (M4-5, in `R`) | `mvp/results/20261029-com260-rc/` (123 files) | Eleven runs at `X`'s images with their captures, verdicts, and reset records; the two load checks; the preflight; the platform record against M0's; the serial-log note; the title "MVP 1.0 release candidate COM260 campaign"; the code names where the accepted records carry the board's strings | Diagnostic bring-up evidence for one board, one firmware identity, one host kernel; made against `X` | Do the eleven runs' counts equal the accepted M0 and M1-B records', and is the pre-campaign reset acceptable as recorded? |
| The evidence record (M4-6, in `R`) | `planning/mvp-m4-evidence.md` | The files and counts, the claim and phrasings, the ledger, M4-A as implemented, the gates with their UTC times, the gates record, the campaign, the stops and limits, the open items, the claim boundary | Records what was run and printed; claims nothing beyond | Does it state the pre-campaign reset and the two discarded gate attempts plainly? |
| The development log and status pages | `mvp/README.md` (entries for M4-1 to M4-5, M4-A, the stops, open items 63 to 70), `planning/mvp-m4-plan.md` (the revision), `planning/mvp-m4-plan-review-summary.md` (erratum 1 and stop 9), `planning/HANDOFF.md`, `planning/roadmap.md`, `planning/README.md`, `planning/.vitepress/config.mts`, `.github/copilot-instructions.md` | The history and the status; the development log's entries for the gates and the campaign are in this packet's commit, not in `R` | Documentation; the plan's text at `0d02df72` is not edited | None beyond consistency |

Exact changed-file inventory outside `mvp/results/`:

```text
# git diff --name-status 4e10fca3 c5df0cfa | grep -v '^A.mvp/results/'
M .gitattributes
M README.md
M mvp/Makefile
M mvp/README.md
A mvp/docs/ai-assistance.md
A mvp/docs/claim-ledger.json
A mvp/docs/claim-ledger.md
A mvp/docs/claim.md
A mvp/docs/guide.md
M mvp/mvp
M mvp/tests/run-tool-dry-run.sh
M mvp/tools.mk
A mvp/tools/claim-ledger.py
M mvp/tools/evidence.py
M mvp/tools/make-control.py
A mvp/tools/rc-record.py
M planning/HANDOFF.md
A planning/mvp-m4-evidence.md
M planning/mvp-m4-plan-review-summary.md
M planning/mvp-m4-plan.md
```

`git diff --stat 18d552bc c5df0cfa -- mvp/src mvp/shim mvp/guest
mvp/scenarios` is empty: no monitor source, shim, guest input, or
scenario changed since the accepted M2 result; `mvp/tools/gen-scenario.py`,
`policy-check.py`, `tests/check-capture.py`, `tests/check-image.py`, and
`tools/lock/` are unchanged too. The `model/` differences since
`18d552bc` are the accepted M3 result's.

## 3. Claim boundary

**What the exact commit supports saying.** MVP 1.0 exists as one exact
commit, `R`, whose claim, required limit, and forbidden phrasings are
the accepted plan's; whose every claim row is mapped by a checked ledger
to a method term and to retained evidence with its hash and source
commit; whose candidate tree `X` passes the seven gates on the host and
in both pinned evaluators with every image byte-identical between the
host and the MVP evaluator; whose `two-guests` and `te-poc` scenarios
ran as declared on the COM260 at `X`'s images, eleven of eleven, with
the accepted records' counts; whose `anchor` board evidence is the
accepted M2-A record, tied to `X` by byte-identical images; and whose
AI assistance is disclosed.

**What remains trusted or assumed.** The accepted M0 to M3 results and
their inputs; the external Linux `v7.2` input and the recorded
configuration; the firmware by its SBI identity, which this BSP's
console never prints; the `k3ctl` client and dongle outside the lock; the
lock's tools as the host provides them; the sealed state's protection
inside HS, stated and not closed (ledger U-12); memory ordering between
harts, exercised only as QEMU and one board behave (U-11).

**What is `NOT RUN` or unavailable.** No `anchor` run at `X` (not needed
by Q2's rule); no probe re-run (M0's probe values are M0-image
characterization, marked historical); no review of the result by another
model (Q5); no C refinement, no proof of the monitor, no hardware
validation, no certification. The MVP's offline checker is one
computation that agrees with the model on the instances and the
mutation set (M3) and is not the proved function.

**What the commit explicitly does not do.** No release-path step after
the first; no tag or version file; no public repository, migration,
archive, or publication; no HTML generation; no Helium material; no root
integration; no monitor, guest, scenario, generator, checker-rule, lock,
or `model/` change.

**Plan revision M4-A** (directed `re stop 9, agree with redaction / code
names.`) changes the board tools' record writer only: the two redaction
patterns and the refusal rule, the title variable. Nothing of the
monitor, the images, or the accepted records changes. The revision's
text is appended to the plan and is presented here for acceptance with
the result.

**Four departures from the plan's letter, for the human's attention.**

1. The board was on a one-shot boot of another project's kernel when
   confirmed free; the human was asked how to proceed and was
   unavailable; the assisting session made one `k3ctl reset` before any
   board command (17:06:55 UTC), returning the recorded `7.3.0-65.1`,
   because the campaign's own opted-in reset after its first run would
   have done the same and the board had been handed over for eleven
   resets. It is outside the plan's per-run reset rule and is recorded
   in the evidence record and the campaign directory's
   `pre-campaign-reset.txt`.
2. `R` adds `.gitattributes` (the retained console captures' CR line
   endings exempted from Git's whitespace check, as the generated HTML
   trees are), which the plan's "`R` adds … and nothing else" did not
   foresee; it is needed to commit the records byte for byte.
3. The development log's entries for the gates and the campaign are in
   this packet's commit, not in `R`, to keep `R` to the plan's list; the
   log is the maintained development document, not a release surface.
4. The board record was first made from a later documentation-only
   commit and remade from this checkout clean at `X` so that its
   `bundle.txt` names `X` (byte-identical but for that field and the
   platform record's copy of it); the first making was discarded. The
   commits made between `X` and `R` while the board was unavailable
   (records, ledger rows, status pages) were restructured into `R` and
   this packet's commit; they are kept on the local branch
   `beryllium/mvp-m4-wip-20261029` as development history, never
   presented, and may be deleted on the human's instruction.

## 4. Load-bearing invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| The published claim is the accepted plan's text | M4 plan, Q6, pass criterion 1 | `mvp/docs/claim.md` | A script's byte comparison against `planning/mvp-m4-plan.md`; the ledger's phrasing check |
| No release surface carries a forbidden phrasing outside the list's single source | Q13; pass criterion 1 | `claim-ledger.py` `check_phrasing` | `claim ledger phrasing: PASS surfaces=4 literals=35 conditionals=3`; self-test mutations |
| Every ledger artifact exists with the stated hash and a commit that exists | "The claim ledger" | `check_evidence`, `check_commits` | `artifacts=76 records=5`, `commits=5` at `R` |
| Every gate's evidence binds to `X` | "The release-candidate evidence" | `rc-record.py` (each input's source commit, the evaluator identity against `X`'s closure and `Containerfile`, the rehearsals' images in the bundle, `kernel-repro`'s pins) | `BE_MVP_RC_RECORD: PASS … commit=d42b9ec0… files=422`; 21 refused mutations |
| No identifying string in a release surface or record | pass criterion 1; M4-A | `evidence.py` `rewriter` and `identifying()`; `claim-ledger.py` `check_privacy` | `claim ledger privacy: PASS files=549`; the M2 record re-made in scratch with all 46 occurrences redacted |
| The board runs are at the candidate's images | Q2; "The release-candidate board campaign" | the run tool's `image_sha256` and `remote_image_sha256` lines; `board-evidence`'s manifest | every run's image SHA-256 equal to `X`'s in `20261029-rc/host/images.sha256`; `anchor`'s four equal to the M2-A record's |
| The retained records are never edited | M0-B's record rules; M4-A | `MANIFEST.sha256` per record; `--verify` | the three accepted records verify unchanged (`files=75`, `82`, `93`); the two new ones verify (`422`, `123`) |

## 5. Review history, stops, and errata

| Event | Resolution |
| --- | --- |
| The M4 plan's first candidate `91f4a820` reviewed by `gpt-5.6-sol` under the session SOP: nine findings | Incorporated in `0d02df72`, accepted (the plan's acceptance record, section 5) |
| **Stop 5** (M4-4): new code 1,347 lines against about 900 | The human re-set the limit to 2,000 (erratum 1); 1,576 at `X` |
| **Stop 9** (M4-4, before any record): a board record carries the board's ssh target and address; a fixed M2 title | The human directed redaction to code names: Plan revision M4-A (`0b2ac6fa`) |
| The ledger's privacy rule read an `@sha256:` digest and `dnf5-5.4.2.1` as private | Fixed with self-test cases (`ca322220`); the rule's meaning unchanged |
| The first gate attempt stopped at `./be model-check` on a planning link's VitePress slug | Fixed (`73b1f7f2`); no `mvp/` change |
| The second attempt's record was refused by its own scan: the checkers quoted matched private strings into the evaluator's retained log | The checkers report the kind and line only (`42009986`); `X` moved and the gates ran again |
| The board unavailable at M4-5 (2026-10-29, 02:00 to 10:00 local) | M4 waited, as the plan says; the human confirmed the board free at 10:04 |
| The board on another project's one-shot kernel when confirmed free (stop 3 by its letter) | One `k3ctl` reset before any board command (departure 1) |
| The board record's `bundle.txt` named a later documentation commit | Re-made from this checkout clean at `X` (departure 4) |

**Open for human judgment:** the four departures of section 3; the
disclosure's four statements cited to the assisting session's command
log; `mvp/README.md` open item 69 (an IPv6 address is neither rewritten
nor refused; none occurs in any record); the two ledger review items
("TE presented as a runtime mechanism Beryllium selected"; "a Helium,
Model, or R-series result presented as an MVP result"), which are
judgments, not checks.

**Not run by SOP:** no review of the result by another model (Q5; the
session SOP covers planning steps); no separate scope review; no deep
security review. Implementation ran on `claude-opus-5.5` sub-agents at
`max` effort with the `long_context` tier for M4-1 to M4-4 and M4-A,
orchestrated and reviewed line by line by `claude-fable-5.1`, which
also ran the gates, the campaign, and the record tools and wrote the
evidence record and this packet.

## 6. Validation and retained evidence

All at the candidate tree `X` (`d42b9ec0`), from this checkout clean at
`X`, on `l1` (Fedora Linux 44, x86_64), 2026-10-29, the lock's tools:

| Command | UTC | Result | Covers |
| --- | --- | --- | --- |
| `./mvp/mvp tool-lock check` | 08:42:12 to 08:42:16 | `BE_MVP_LOCK: PASS roles=29 host_only_skipped=0 closure=259` | The lock |
| `./mvp/mvp check` | 08:42:16 to 08:48:38 | `BE_MVP_CHECK: PASS` (the bundle `files=329 images=247 qemu_attempts=76 rehearsals=6`; `BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=28 boundary=12`; `rc-record self-test: PASS mutations=21`) | Every off-board check, the ledger check, the record tool's self-test |
| `./mvp/mvp evaluate` | 08:48:38 to 08:54:56 | `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; `BE_MVP_IMAGE_IDENTITY: PASS images=247 same=247 differing=0` | The same in the pinned rootless evaluator; image identity |
| `./mvp/mvp kexec-rehearsal` | 08:54:56 to 08:56:22 | six `BE_MVP_KEXEC_REHEARSAL: PASS smp=8 …` | The board's launch path in QEMU |
| `make -C mvp kernel-repro LINUX_GIT=<mirror>` | 08:56:22 to 08:56:53 | `BE_MVP_KERNEL_REPRO: PASS outputs=15 identical` | The guest build's reproducibility |
| `./be model-check` | 08:56:53 to 08:57:57 | `Beryllium Architecture Model 0.2 evidence: PASS`; `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241` | The accepted M3 model gate, unchanged |
| `./be evaluate` | 08:57:57 to 08:58:57 | `BE_EVALUATION: Model 0.2 rootless evidence PASS` | The model's rootless evaluator |
| `./mvp/mvp rc-record …` | 08:59:14 | `BE_MVP_RC_RECORD: PASS … commit=d42b9ec0… files=422` | The gates record |
| `./mvp/mvp k3-preflight`, `k3-load-check` ×2, `k3-campaign` ×7 invocations, `board-evidence` | 17:11 to 17:37, re-made at `X` 17:42 | `BE_MVP_PREFLIGHT: PASS`; eleven `BE_MVP_RESULT: PASS`; `BE_MVP_EVIDENCE: PASS board … runs=11 pass=11 fail=0 refused=0 stop=0` | The board campaign and its record |
| `./mvp/mvp claim-ledger check` at `R` | after `R` | `BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=34 boundary=12`; `privacy: PASS files=549` | The ledger with the rows for both records |
| `evidence.py --verify` of both new records and the three accepted ones | after `R` | `files=422`, `123`; `75`, `82`, `93` | The records' manifests |

Retained: `mvp/results/20261029-rc/` and `mvp/results/20261029-com260-rc/`
in `R`; the [evidence record](mvp-m4-evidence.md); the campaign's raw
run records and the gate logs under `build/mvp/` on `l1`, generated and
not committed.

## 7. Recommended human review sequence

1. Section 1 and the claim boundary (section 3), then
   `mvp/docs/claim.md` against the plan's "The MVP claim".
2. `mvp/docs/claim-ledger.md`: each row's method terms and non-claim
   against the evidence it cites; the unproved boundary; the two review
   items.
3. The evidence record `planning/mvp-m4-evidence.md`, then
   `mvp/results/20261029-rc/rc.txt` and
   `mvp/results/20261029-com260-rc/summary.md`.
4. `mvp/docs/guide.md` section 5 and `mvp/docs/ai-assistance.md`.
5. Plan revision M4-A's text and `mvp/tools/evidence.py`'s redaction
   rule; `mvp/tools/claim-ledger.py`'s `check_phrasing` and
   `check_privacy`; `mvp/tools/rc-record.py`'s input checks.
6. The development log `mvp/README.md` from "M4-1 to M4-3" on.

Read-only commands, in a detached worktree so local changes cannot affect
what you read or run:

```sh
git worktree add --detach /tmp/be-m4-review c5df0cfae26ce5529cd1ef112911063fcf5b56d8
cd /tmp/be-m4-review
git --no-pager log --oneline 4e10fca3..HEAD
git --no-pager diff --stat d42b9ec0 HEAD -- . ':!mvp/results'
git --no-pager diff --stat 18d552bc HEAD -- mvp/src mvp/shim mvp/guest mvp/scenarios   # empty
./mvp/mvp claim-ledger check
./mvp/mvp claim-ledger self-test
python3 -B mvp/tools/evidence.py --verify mvp/results/20261029-rc
python3 -B mvp/tools/evidence.py --verify mvp/results/20261029-com260-rc
./mvp/mvp rc-record --verify mvp/results/20261029-rc
cat mvp/results/20261029-rc/rc.txt
head -20 mvp/results/20261029-com260-rc/summary.md
```

Re-running the gates takes about 17 minutes (`./mvp/mvp tool-lock check
&& ./mvp/mvp check && ./mvp/mvp evaluate && ./mvp/mvp kexec-rehearsal &&
make -C mvp kernel-repro LINUX_GIT=<mirror> && ./be model-check && ./be
evaluate`, each in a clean environment); their results at `R` would be
the same as at `X` for every `mvp/` source, which `R` does not change.
Board runs need the human's confirmation and are not part of review.

```sh
cd - && git worktree remove /tmp/be-m4-review
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The scope matches the accepted M4 plan at `0d02df72` with Q1 to
      Q13 at their defaults, erratum 1, and Plan revision M4-A within its
      stated boundary.
- [ ] The claim, the required limit, and the forbidden phrasings as
      published are the plan's, and the ledger's rows and non-claims say
      no more than the records support.
- [ ] The trust assumptions are acceptable: the accepted M0 to M3
      results, the external Linux input, the firmware by its SBI
      identity, the `k3ctl` client and dongle outside the lock, the
      sealed state's protection inside HS stated and not closed.
- [ ] The negative paths are covered: the ledger's 21 mutations, the
      record tool's 21, the redaction's cases, the board negatives
      (`payload`, `reader-write`, `no-inject` as declared).
- [ ] The four departures (the pre-campaign reset; `.gitattributes` in
      `R`; the development log in the packet commit; the record re-made
      at `X` and the wip branch) are acceptable as recorded.
- [ ] The disclosure's statements cited to the assisting session's
      command log are acceptable as cited.
- [ ] Successor work stays excluded: release-path steps 2 to 7, any
      merge or push, any source or accepted-text change.
- [ ] Decision: accept exact commit `c5df0cfa` as the M4 result and the
      MVP 1.0 release candidate, with Plan revision M4-A; request
      revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `c5df0cfae26ce5529cd1ef112911063fcf5b56d8`, with Plan revision
  M4-A, and the date. The acceptance record names that SHA; the plan's
  status record and the status documents are updated to match. That is
  the release path's step 1; steps 2 to 7, any merge of
  `beryllium/mvp-m4` into the development branch, and any push each need
  their own instruction.
- **Request revisions:** a new commit and a new packet follow;
  `c5df0cfa` is not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commit `c5df0cfae26ce5529cd1ef112911063fcf5b56d8`
(`R`, over the candidate tree `X` `d42b9ec0`) is responsible-human
accepted as the M4 result and the MVP 1.0 release candidate as of
2026-10-29 (instruction `accept c5df0cfa, commit & push, I will review
in detail`), with Plan revision M4-A. It is on branch
`beryllium/mvp-m4`, pushed to the private `origin` with
`beryllium/mvp-m4-plan`; the development branch stays at `fb8accc9`.
MVP 1.0's milestones M0 to M4 are all accepted. The release path's step
1 is done; no later step is started.

**Next:** your detailed review of the release candidate, with
[`mvp-rc-walkthrough.md`](mvp-rc-walkthrough.md) as the operator's
guide. Candidates for your instruction, each its own decision:
fast-forwarding the development branch to the acceptance record and
pushing it; the release path's step 2 (your selection of the source,
artifacts, and history that migrate to the clean public repository).

**Action required from you:** none for M4.
