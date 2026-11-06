<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Debt sweep 4 (items 99, 100, 102, 105, and `SECURITY.md`): review packet

This packet supports the responsible human's decision on exact commit
`d162c60db4aab7bda77f2a557f91ac7446cca37c`, the candidate of debt sweep 4,
which fixes the code defects among the open items the processing of the
three independent S3-C design reviews registered on 2026-11-01 and adds the
security policy the human directed for the public review snapshot. It
recorded the decision below after it was given.

## Decision record

The responsible human accepted exact commit
`d162c60db4aab7bda77f2a557f91ac7446cca37c` (parent `954b8f7f`) as debt
sweep 4 on 2026-11-01 (10:20 in the human's time zone). The instruction,
given in reply to this packet's request to accept, revise, or defer that
exact commit, was `accept d162c60d & ff + push`. The abbreviation was
checked to resolve uniquely to that commit
(`git rev-parse --disambiguate=d162c60d`).

- **Scope:** acceptance covers exactly that commit and the claim boundary
  of section 3, the two readings section 5 left to the human included:
  `fix code issues` is confirmed as the authorization for the change to
  the accepted M3 gate bytes (`97874695`, the escape patterns and their
  test), and `SECURITY.md`'s wording, open-reporting rule, and address
  stand as written. Sections 1 to 9 are the packet as presented, apart
  from the status rows of section 1 and the closing lines of section 9,
  which now show the outcome. `mvp/README.md` open items 99, 100, 102,
  and 105 are closed by this acceptance; 101, 103, and 104 stay open for
  M8 and M9, and 94 to 97 stay the human's.
- **The same instruction directs** the fast-forward of the development
  branch `beryllium/single-hart-runtime-r0` from `b53c02a8` to the commit
  recording this decision and the push of that branch and of
  `beryllium/mvp-debt-4` to the private `origin`. It does not direct a
  further refresh of the human's local clone of the public review
  snapshot, which stays at the snapshot of this packet's commit
  `03443dfc` (`d4d3955d` in the clone, section 6) with its pre-decision
  wording; a re-refresh from the acceptance record is one instruction
  away, and the publication of the clone's `main` stays the human's act.
- **What it is not:** no release-path step (steps 2 to 7 are not
  started); no tag or publication; no board command and no kexec; no
  change to the claim statement, any accepted plan, any monitor source,
  or any accepted byte beyond the two M3 gate scripts named above; no
  decision on Plan revision S3-C, whose second candidate `27d2e557` on
  `beryllium/mvp-s3c-plan` waits separately.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `d162c60db4aab7bda77f2a557f91ac7446cca37c`, parent `954b8f7ff1b4d5b88af94623faf1a42def8c1cdf`; the sweep is the six commits `ed0c413d` to `d162c60d` on local branch `beryllium/mvp-debt-4` from the debt sweep 3 acceptance record `b53c02a8bfcda21b622f94d7044bff2221d5b4ce`, the development tip (`beryllium/single-hart-runtime-r0`, local and `origin`) |
| Current status | Implemented; the gates of section 6 ran at `d162c60d` from a clean tree; **responsible-human accepted as of 2026-11-01** (the decision record above) |
| Decision requested | None outstanding on this commit; the decision was `accept d162c60d & ff + push` |
| Successor status | None started. Plan revision S3-C's second candidate `27d2e557` on `beryllium/mvp-s3c-plan` awaits its own decision and is unaffected; no milestone, plan, or release-path step is started or authorized by this sweep or its acceptance |
| Publication status | The same instruction directs the fast-forward of the development branch to the commit recording this decision and the push of it and the sweep's branch to the private `origin`. The human's local clone of the public review snapshot (`beryllium-hypervisor-rc3`, beside the checkout) holds the snapshot of this packet's commit (section 6, "The snapshot refresh"); its push to the public `main` (at `1ae5fd8c` as this is written) stays the human's act |

The action this section asked of the human, the decision on `d162c60d`,
is taken; what follows it is in the decision record above and in
section 9.

### What the sweep is, in one paragraph

On 2026-11-01 the responsible human directed `add todo for the public rc3
repo: add a security md file to note this is an early pre-release snapshot
for external review purposes only. any security issues may be openly filed
against the repo for now.`, then `update the security.md as you feel best,
fix code issues`, then `then let's focus on updating the snapshot with
fixes & security md`. The code issues are the three among the open items
that the S3-C review processing had registered the same day: the capture
checker's forged-loader-block reading (item 100, reproduced by the Claude
Code review), the model gate's singular-only escape pattern (item 102,
confirmed by the same review), and the snapshot tool's hard-coded session
trailer (item 105, found during the refresh of the human's clone); a fourth
small defect found in the same refresh, the evaluator's cache argument
ignored, is fixed beside them. `SECURITY.md` is written as a root file so
that every snapshot carries it unchanged. No monitor source (`mvp/src/`),
claim statement, accepted plan text, or board record changes; no board
command and no kexec. One accepted M3 gate pair (`model/tests/run-proofs.sh`,
`model/tests/check-source-policy.sh`) changes under `fix code issues`, as
the accepted-tool fixes of 2026-10-07 were authorized, and the acceptance
of this commit confirms that reading or rejects it.

## 2. Deliverables

| Deliverable | Paths | Purpose | Boundary | Review question |
| --- | --- | --- | --- | --- |
| The one-autoboot rule (item 100), `ed0c413d` | `mvp/tests/check-capture.py` (`uboot_facts`, `forged_loader_block`, four mutations), `mvp/tools/k3-uboot.py` (`attribution`), `mvp/tests/run-tool-dry-run.sh` (two expectation lines) | U-Boot's loader lines are read after the one autoboot line of the run; a second autoboot line is a finding | Host checker over serial captures; the retained captures are read-only inputs | Is "exactly one autoboot line per run" the right attribution rule for every capture the checker judges (board runs sliced from the reset; the QEMU rehearsal), and is `attribution`'s "at most one" right for the typed `run be_ld`? |
| C-10's pin, `01661500` | `mvp/docs/claim-ledger.json`, `mvp/docs/claim-ledger.md` | The ledger cites the checker's new bytes at the commit holding them | Ledger bookkeeping | Does the pin name the commit that holds the bytes (`ed0c413d`)? |
| The plural keywords (item 102), `97874695` | `model/tests/run-proofs.sh`, `model/tests/check-source-policy.sh`, new `model/tests/check-escape-pattern.sh`, `model/Makefile` (`toolcheck`) | Rocq's plural assumption keywords and `Conjecture` join both escape patterns; a test reads each pattern from its script and checks it | Accepted M3 gate bytes (the proof modules are untouched) | Is `fix code issues` the authorization for these accepted gate bytes, as the 2026-10-07 accepted-tool fixes were? Is the pattern now complete for the Rocq version in the lock? |
| The session trailer and the cache argument (item 105), `f1bad063` | `mvp/tools/snapshot.sh` (`commit_snapshot`, self-test), `mvp/tools/evaluator/evaluate.sh` | A snapshot commit names the session that made it or no session; `./mvp/mvp evaluate MVP_RPM_CACHE=DIR` seeds the fetch | Snapshot and evaluator tooling, host only | Is omitting the trailer when no session is given the right default (the `Co-authored-by` disclosure line stays)? |
| `SECURITY.md` (item 99), `954b8f7f` | `SECURITY.md`, `README.md` (layout table), `mvp/tools/snapshot-readme.md`, `mvp/tools/snapshot.sh` (kept paths) | The pre-release review snapshot's security policy: open reporting for now, the address for those who would rather not, what to expect, when it changes | A public-facing statement; it makes no claim beyond `mvp/docs/claim.md` | Is the wording what you want published under your name, in particular the open-reporting rule, the address, and "do not run it to protect anything"? |
| The record, `d162c60d` | `mvp/README.md` (development log, open items 99 to 105) | The sweep's record and the items' registration on the integration line | Documentation | Do the closures match the commits? |

## 3. Claim boundary

**The exact commit supports saying:**

- `mvp/tests/check-capture.py --mode uboot` rejects a capture with more
  than one U-Boot autoboot line before the markers and reads the loader's
  lines after the single one; four mutations planting a forged loader block
  after a second autoboot line are rejected (adversarial test, host:
  `self-test cases=133 mutations=321 rejected=321`); the 40 retained RC2
  and RC3 serial logs each have exactly one autoboot line, so the rule
  finds nothing against any accepted record (read-only re-judgement, not a
  re-run).
- `model/tests/run-proofs.sh` and `model/tests/check-source-policy.sh`
  refuse `Axioms`, `Parameters`, `Variables`, `Hypotheses`, `Conjecture`,
  and `Conjectures` in the proof sources as they refuse the singular forms;
  `model/tests/check-escape-pattern.sh` fails against the previous patterns
  (unit test, host); the Rocq proof passes unchanged (proof, bounded as
  before).
- `mvp/tools/snapshot.sh` writes a `Copilot-Session` trailer only from
  `BE_SNAPSHOT_SESSION`, refuses a malformed id, and omits the trailer when
  unset (unit test, `cases=33`); `mvp/tools/evaluator/evaluate.sh` exports
  an `MVP_RPM_CACHE=DIR` argument before the fetch (exercised by the
  snapshot refresh of section 6).
- `SECURITY.md` is present at the root and in every snapshot the tool makes
  (the self-test requires it).

**What remains trusted or assumed:** the one-boot-per-run shape of the
captures (M5's `k3-run.sh` slices each run's serial log from its reset;
the QEMU rehearsal prints one autoboot line); the lock's Rocq version's
keyword set; the host's tool lock.

**Not run:** no board command, no kexec, no release-path step. The B0, B6,
and B7 tooling gates (`host-test`, `tools-check`) were not re-run: the
sweep does not touch `bringup/`.

**The commit does not:** change `mvp/src/`, the claim statement, any
accepted plan, any board record, or the ledger's claims (C-10's evidence
pin moves; its claim text does not); close items 101, 103, or 104
(Binding.v's readings, the VST route, Q38's premise are M8 and M9
matters); push, merge, tag, or publish anything; decide S3-C.

## 4. Security and correctness invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| The checker reads U-Boot's loader lines, not an image's imitation | `check-capture.py` docstring, "uboot mode"; M5's attribution rule | `uboot_facts`: `autoboot_lines == 1`, `after = autoboot_index + 1` | the four `forged-loader-block` mutations and `no autoboot line, counted`, rejected |
| The proof gate's escape pattern is closed over Rocq's assumption vocabulary | `run-proofs.sh` L20 comment; `check-source-policy.sh` | the two patterns | `check-escape-pattern.sh` (must-match and must-pass lines; fails 12 against the old patterns) |
| A snapshot commit's session trailer is true or absent | `snapshot.sh` header comment | `commit_snapshot` | self-test cases: trailer read back; malformed id refused; no trailer on an update without a session |
| The snapshot carries the security policy | `snapshot.sh` self-test's kept paths | `SECURITY.md` is a tracked root file; the tool keeps every file but `README.md` | `snapshot-check` |

## 5. Review history and resolved findings

The sweep's inputs are findings of the three independent S3-C design
reviews (`planning/mvp-plan-s3c-review-reconciliation.md` on the S3-C
branch; rows Z and the model-gate row) and of this session's refresh of the
human's snapshot clone. Resolved in the sweep:

1. **Item 100** (Claude Code review, reproduced against the checker): the
   checker read after the *last* autoboot line. Fixed by the one-autoboot
   rule; four mutations added. The 40 retained captures were re-judged
   read-only before the rule was committed, so that no accepted record is
   contradicted by it.
2. **Item 102** (Claude Code review): the plural keywords. Fixed in both
   patterns with the new test; the proof modules are untouched and the
   accepted six stay byte-identical.
3. **Item 105** (found in the refresh): the hard-coded trailer. Fixed with
   three self-test cases.
4. **The evaluator's cache argument** (found in the refresh): the wrapper's
   `VAR=VALUE` form reached `evaluate.sh` as an argument, not the
   environment, so `MVP_RPM_CACHE=DIR` was ignored by the fetch. Fixed by
   exporting it; the snapshot refresh of section 6 uses the argument form.
5. **`shellcheck` SC1007** on the self-test's `BE_SNAPSHOT_SESSION=` (a
   space after `=`), fixed to `''` before the commit; the self-test's
   first test id was not UUID-shaped and was refused by the new check,
   corrected to a UUID-shaped id (`01234567-89ab-cdef-0123-456789abcdef`).

Open for the human's judgement (not defects of this sweep): the reading of
`fix code issues` as authorization for the accepted M3 gate bytes (the
alternative is to request a separate decision, in which case commit
`97874695` is dropped from the sweep); whether `SECURITY.md`'s address and
open-reporting wording are as wanted.

## 6. Validation and retained evidence

Gates at `d162c60d`, from a clean tree (`git status --porcelain` empty) in
the worktree `worktrees/beryllium-hypervisor/rc3-review-remediation`, the
external inputs (`build/mvp/guest`, `build/mvp/linux-src`, `build/k3-b*`,
`build/mvp-evaluator`) linked from the main checkout and `build/model` a
fresh directory, one gate at a time, logged under
`build/mvp/sweep4-gates/` (outside the tree):

| Gate | Result | Time (UTC) |
| --- | --- | --- |
| `./mvp/mvp tool-lock check` | `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`; the lock, fetch, and closure self-tests pass | 17:38:02 to 17:38:05 |
| `./mvp/mvp check` | `BE_MVP_CHECK: PASS`: `BE_MVP_CAPTURE_SELF_TEST: PASS cases=133 failed=0`, `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=321 rejected=321`, `BE_MVP_RUN_TOOL_DRY_RUN: PASS` (27 cases), `BE_MVP_SNAPSHOT: PASS self-test cases=33`, `BE_MVP_LICENSES: PASS identifiers=2 files=860 texts=2 source=git`, `BE_MVP_QEMU: PASS runs=58 attempts=75 refused=17`, the image checks and mutations, the policy negatives, `BE_MVP_EVIDENCE: PASS … files=294 images=253` with `source_commit=d162c60d…` and `source_tree=clean` in `bundle.txt`, `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=46 boundary=13` | 17:38:05 to 17:43:55 (the images and runs of the pre-commit checks were up to date) |
| `./mvp/mvp claim-ledger check` | `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=46 boundary=13` | 17:43:56 |
| `./mvp/mvp evaluate` | first attempt `FAIL`: the inner `mvp check` stopped at the dry run's `missed-s-retry` case (`an unplanned boot`), the timing-bound case of `mvp/README.md` item 93, the host's load average 2.7 from other users' work; the second, alone, `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`, `BE_MVP_IMAGE_IDENTITY: PASS images=253 same=253 differing=0`, the lock inside `roles=26 host_only_skipped=6`; both logs retained | 17:44 to 17:46 (attempt 1), 17:46:38 to 17:51:59 (attempt 2) |
| `./be model-check` | the documentation source check (`site_markdown=154`), `Beryllium model escape-hatch patterns: PASS` (the new test), source policy, unit tests, `BE_POLICY_RUN: PASS instances=4 mutations=91`, reports, `security model v1 policy and hart binding proofs: PASS`, `Model 0.2 proofs: PASS`, `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`, evidence: PASS | 17:51:59 to 17:53:10 |
| `./be evaluate` (the model's rootless evaluator) | from the worktree, `FAIL status=2` at its evidence step: the container mounts the tree at `/work`, and a linked worktree's `.git` is a gitfile pointing outside the mount (`gitfile does not point to a valid repository`); every step before it (unit, reports, proofs with the new pattern, differential) passed inside the container. Re-run from a standalone clone at `d162c60d` (`/tmp/be-debt-4-model`, `git status` clean): `BE_EVALUATION: Model 0.2 rootless evidence PASS`, image `42e46715…` (`sha256:213d5030…`) | 17:53:10 to 17:54:10 (worktree), to 17:55:34 (clone) |
| `git diff --check` | clean | 17:54 |

The B0, B6, and B7 tooling gates were not run: `bringup/` is untouched.
The first `evaluate` attempt and the worktree `./be evaluate` failure are
environment effects (item 93's timing case; the linked worktree's
gitdir), not findings against the sweep, and are recorded rather than
hidden.

Before the commits, in the same tree: `env -u LD_LIBRARY_PATH make -C mvp
capture-check` (`cases=133 mutations=321 rejected=321`), `run-tool-check`
(27 cases, `attribution_lines=… autoboot_lines=1` and `typed_load=…
autoboot_lines=0` in the records), `snapshot-check` (`cases=33`), `make -C
model toolcheck source-check proof`, `shellcheck` on the changed shell
scripts, `node scripts/check-doc-sources.mjs`, `python3 -B
mvp/tools/check-licenses.py check`, `git diff --check`; and the read-only
re-judgement of the 40 retained RC2 and RC3 serial logs under
`build/mvp/k3-sessions/` with the new rule (each: one autoboot line, one
`Starting kernel`, one banner; no finding).

### The snapshot refresh

On the human's `then let's focus on updating the snapshot with fixes &
security md`, the human's local clone of the public review snapshot
(`beryllium-hypervisor-rc3`, beside the checkout; `main` at `3b6d76da`,
the unpushed refresh from `b53c02a8`) is refreshed in place by
`BE_SNAPSHOT_SESSION=<this session> mvp/tools/snapshot.sh update <this
packet's commit> <clone>` after this packet is committed, so that the
snapshot carries the sweep's fixes, `SECURITY.md`, and this packet; the
gates (`./mvp/mvp check`, `./mvp/mvp evaluate MVP_RPM_CACHE=<the
development host's verified cache>`, the argument form this sweep fixes)
are run in the clone, their results written into the snapshot README's
checks table, and the snapshot commit amended, as the earlier refreshes
were. The refresh's record (the snapshot commit, the blob comparison, the
gates' results) is in `mvp/README.md`'s development log in the commit
after this packet, on the same branch, because a commit cannot record a
snapshot made from itself. The push of the public `main` is the human's
act, after their own review of the clone; nothing is pushed by
automation. Note for the decision: the snapshot is made from a proposed,
not accepted, commit, as the human's direction asks for the fixes and the
policy in the snapshot now; if the human prefers the snapshot to come
from the acceptance record, say so and the clone is re-refreshed from it
after the decision (the earlier refreshes, from `3fe427b7` and
`b53c02a8`, were each from a commit the human had accepted or accepted the
same day).

## 7. Recommended human review sequence

In a detached worktree of the exact commit:

```sh
git worktree add --detach /tmp/be-debt-4 d162c60db4aab7bda77f2a557f91ac7446cca37c
cd /tmp/be-debt-4
git log --oneline b53c02a8..HEAD
git diff --stat b53c02a8..HEAD
```

1. **The policy** (`SECURITY.md`; `git show 954b8f7f`): the wording is
   published under your name; the open-reporting rule, the address, and
   the "not a release" statements are the review.
2. **The checker rule** (`git show ed0c413d -- mvp/tests/check-capture.py`):
   `uboot_facts` and the four mutations; then `env -u LD_LIBRARY_PATH make
   -C mvp capture-check`.
3. **The gate change on accepted bytes** (`git show 97874695`): the two
   patterns and the test; `make -C model toolcheck`.
4. **The tool fixes** (`git show f1bad063`): `commit_snapshot` and the
   self-test; `evaluate.sh`'s argument loop.
5. **The ledger pin** (`git show 01661500`): `./mvp/mvp claim-ledger check`.
6. **The record** (`git show d162c60d -- mvp/README.md`).

## 8. Human decision checklist

- [ ] The sweep stays within `update the security.md as you feel best, fix
      code issues` and `then let's focus on updating the snapshot with
      fixes & security md`: no monitor change, no claim change, no plan
      text change, no board command, no kexec.
- [ ] `fix code issues` is accepted as the authorization for the change to
      the accepted M3 gate bytes (`97874695`), or that commit is to be
      dropped and decided separately.
- [ ] The one-autoboot rule is the attribution rule wanted for the checker,
      and no retained record is contradicted by it (none is, by the
      read-only re-judgement).
- [ ] `SECURITY.md`'s wording, the open-reporting rule, and the address are
      as you want them published.
- [ ] The tests cover the negative paths (forged block, plural keyword,
      malformed session id, missing policy file).
- [ ] Successor work stays excluded: S3-C's decision is separate; items
      101, 103, and 104 stay open for M8 and M9.
- [ ] Exact commit `d162c60d` is accepted, revisions are requested, or the
      review is deferred.

## 9. After the decision

- **Accept:** an acceptance record names `d162c60d` and the date; the
  development branch may be fast-forwarded to it and pushed, and the
  human's clone of the public snapshot re-refreshed from the acceptance
  record, each on your instruction; the public push is yours.
- **Request revisions:** a new commit and a new packet; `d162c60d` is not
  treated as accepted.
- **Defer:** the branch stays local and unmerged; the snapshot clone's
  refresh (section 6) stays unpushed.

**Status:** debt sweep 4 is implemented at exact commit `d162c60d` on
branch `beryllium/mvp-debt-4`, gates passed from a clean tree, and
**responsible-human accepted as of 2026-11-01** (`accept d162c60d & ff +
push`); the development branch is fast-forwarded to the commit recording
the decision and pushed with the sweep's branch to the private `origin`
on the same instruction.
**Next:** your push of the refreshed public review snapshot, if and when
you want it (`git push origin main` from your local clone, a fast-forward
of the public `main` from `1ae5fd8c`; say so first if you want it
re-refreshed from the acceptance record); your decision on Plan revision
S3-C's second candidate `27d2e557`; open items 94 to 97 (the closure's
remedies first).
**Action required from you:** none on this commit.
