<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M10 plan review packet

This packet supports the responsible human's decision on the
[MVP M10 plan](mvp-m10-plan.md), release candidate 4, the last of MVP
1.0's milestones under the accepted Plan revision S3-C (`27d2e557`,
section S3-C.6).

## Decision record

The responsible human accepted the plan at exact commit
`600b78c5198c7462ca76fdb30113f3770fdf5fa7` on 2026-11-04 by the instruction
`accept 600b78c5` (Q1 to Q15 at their defaults), and directed `proceed
with development`: M10-2 to M10-7 are authorized on branch
`beryllium/mvp-m10` from the commit that records this decision, with the
target digests' re-write at `X4`; board commands only after the human
confirms the board free, with the human present at the install and the
restore; no push, merge, tag, publication, snapshot refresh, release-path
step beyond the first, or kexec use. Sections 1 to 9 below are the packet
as presented and are unchanged.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `600b78c5198c7462ca76fdb30113f3770fdf5fa7` (the plan `planning/mvp-m10-plan.md`), parent `c59003e7` (the development branch's tip after the integration of the M8 and M9 lines, its fixes and record, and the beryllium-cheri sidebar import), on local branch `beryllium/mvp-m10-plan` |
| Current status | Plan text proposed, not reviewed; written on the orchestrating model under S3-C's D22; no implementation; no steering review (Q10) |
| Decision requested | Accept the exact commit (authorizing M10-2 to M10-7 on `beryllium/mvp-m10` from the acceptance record, and the target digests' re-write at `X4`), request revisions, or defer; answer Q1 to Q15 or take their defaults |
| Successor status | M10 implementation not started; no branch `beryllium/mvp-m10` exists; the release path's steps 2 to 7 not started and not part of M10 |
| Publication status | Private repository (the internal one; the local `origin`), whose development branch holds the sidebar import at `c59003e7` (its push and the day's record are the handoff's); the plan branch is local and unpushed; the public review snapshot was refreshed from `6ff17c67` on the same instruction, for the human's own push, and holds nothing of M10 |

The action expected from you: decide on `600b78c5198c7462ca76fdb30113f3770fdf5fa7`, with Q1 to Q15 at
their defaults or answered.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Review question |
| --- | --- | --- | --- | --- |
| The plan | `planning/mvp-m10-plan.md` | Bounds release candidate 4: the eight gates from a clean checkout (`verify` and stage 1 among them), the re-proof at `X4` under the M8 plan's D-2 and S3-C.7, the board campaign of 26 runs with the sessions typed under item 8 and the log judged in every run, the release surfaces through the ledger's release object, the licence manifest, four small debts, M10-1 to M10-7, a 2,500-line soft limit, 13 stops, Q1 to Q15 | Planning text; no code, model, claim, or accepted-byte change; its acceptance authorizes implementation and the `target-digests.txt` re-write and nothing else | Is the shape right: one more release candidate with the three milestones' additions exercised on the board, and the red gates closed by re-proof rather than by edit? |
| This packet | `planning/mvp-m10-plan-review-summary.md` | The decision support | Decision support only | None |
| Registrations | `planning/.vitepress/config.mts`, `planning/README.md`, `planning/roadmap.md`, `planning/HANDOFF.md`, `.github/copilot-instructions.md`, `mvp/README.md` | Navigation, the roadmap's position, the handoff's next action, the instructions' current direction, the development log | Documentation | Do they say "proposed", never "accepted"? |

## 3. Claim boundary

**What the exact commit supports saying.** A bounded plan exists for
release candidate 4; it changes no monitor source and plans none; it
closes the two by-design red gates of the integrated tree (stage 1's
readings and the pilot's digests; `mvp/README.md` item 127) by re-reading
and re-proving stage 1 at `X4` with every theorem's statement unchanged,
and by re-running every verifier suite at `X4` with the digests re-written
there; it exercises M7's sessions and M9's log on the board within one
campaign; it names release candidate 4 on every surface through one
source of truth; it states the guest software's licences per component.

**What remains trusted or assumed.** The accepted M8 result's reading
(inconclusive; no C-level contract proof) is not revisited: M10
re-establishes the same evidence at `X4` and adds no claim; a positive
result is not expected and not planned for (Q6: no new arm round). The
board policy's trust (the resident firmware, U-Boot, the loader's MD5 as
the loader observation, `k3ctl`) is M5's and M9's; the human's platform
probe stays the human's (Q5). The licence manifest states obligations for
a distribution the project does not make today.

**Evidence unavailable or not run.** Nothing of M10 has run: no gate at
any `X4`, no board command (the board's availability is confirmed for the
night of 2026-11-04; M10's campaign waits for its own confirmation and the
human's presence at the install and the restore), no re-proof. The
estimates (26 runs; four to five hours of verifier time per run; 850 to
1,530 counted lines) are the plan's, from the recorded costs of RC3, M8,
and M9.

**What the plan explicitly does not do.** No release-path step beyond
the first (steps 2 to 7 each need their own instruction; D21); no
snapshot refresh (Q15); no merge or push; no kexec; no claim-text change
beyond RC4's metadata and M9's D-9 slots (anything else is S3-C's stop
(d)); no M8 specification revision (S-1 to S-5 stay errata); no change to
the accepted M8 or M9 records; items 106, 117, and 125 are not M10's.

## 4. Load-bearing properties of the plan

| Property | Where the plan fixes it | How it is checked in M10 |
| --- | --- | --- |
| The re-proof precedes any pin (S3-C.7; M8 plan D-2) | D-2; M10-2 before M10-4; stop 5 | `verify` at the base and at `X4`, line for line; `digests` at `X4`'s digests; the ledger's rows cite the `X4` run only |
| Stage 1's statements do not move | D-2, Q4; stop 4 | `make -C model proof` green with the readings gate; the lineage table re-made; a statement change returns to the human |
| The monitor does not change | D-7; stop 3 | `git diff --stat` of `mvp/src/` from the acceptance record empty; the leaves' digests equal the base's |
| Measurement is judged in every board run | D-3; fact 5 | the checker's log module on every capture; D-9's board clause takes its "run" form only from those captures |
| Sessions are typed only under item 8 | D-3, Q11 | the console tool's gate and record; a banner aborts (stop (b)); the session file hashed into the run record |
| One source of truth for the candidate's name and commit | D-4 | `claim-ledger check`'s release-surfaces check at `X4` and `RC4` |
| Every identifier in use has its text | D-5, Q7; stop 12 | `check-licenses.py` and the manifest's `--check` in `check` |

## 5. Review history and resolved findings

No independent review was run on this candidate (Q10; the SOP). The
plan's facts were taken from the integrated tree at `c59003e7` and the
records cited in its "Inputs" table; the one computed count (26 runs) is
`K3_PLAN`'s 21 plus `self-report-flip` plus the three sessions, and the
cost figures are the recorded ones (RC3's 26-minute campaign; M8's
`wall_seconds=13480`). Open for the human's judgment, not findings:

- **Q2's campaign size.** 26 runs is RC3's 20 plus the probe M7 added,
  the negative M9 added, and three sessions; the alternative is RC3's 20
  and the sessions only, which would leave `probe-console-input` and
  `self-report-flip` as QEMU evidence.
- **Q3's direction.** The M8 plan reserves the digests' re-write to the
  human's direction; this plan makes its acceptance that direction, in
  words, rather than asking separately at M10-2.
- **Q5's probe.** The plan does not schedule the human's platform probe;
  it fills the claim's platform clause from whatever record exists at
  `RC4`.
- **Q6's arms.** No new WP round (item 125 names the choice as the
  human's); the plan keeps M10 to re-establishing M8's evidence.

## 6. Validation and retained evidence

On the worktree at the exact content of `600b78c5198c7462ca76fdb30113f3770fdf5fa7` (2026-11-04):
`node scripts/check-doc-sources.mjs` passed (`site_markdown=182`, every
route configured); `git diff --check` clean. No MVP gate was run for a
planning commit; the planning pages carry no ledger pin. The facts in
"Facts the design rests on" were read from the tree at `c59003e7`
(`mvp/tools.mk`'s `K3_PLAN`, `mvp/Makefile`'s image families,
`mvp/tools/claim-ledger.py`'s release-surfaces check,
`mvp/tools/verifier/verify.sh`'s suites, `mvp/verify/target-digests.txt`,
`LICENSES/`, `mvp/tools/check-licenses.py`) and from the accepted records
cited.

## 7. Recommended human review sequence

1. S3-C.6 and S3-C.7 of `planning/mvp-plan.md` beside the plan's
   "Purpose", D-1, and "What acceptance authorizes".
2. D-2 (the re-proof) against the M8 plan's D-2 and the M8 evidence
   record's outcome; then Q3, Q4, Q6.
3. D-3 (the campaign) against S3-A.1 with item 8 and RC3's campaign
   record; then Q2, Q5, Q11.
4. D-4 and D-5 (the surfaces and the manifest); then Q7, Q12.
5. The stops and the soft limit.

```sh
git worktree add --detach /tmp/be-m10-plan 600b78c5198c7462ca76fdb30113f3770fdf5fa7
git -C /tmp/be-m10-plan show --stat HEAD
git -C /tmp/be-m10-plan diff c59003e7 HEAD -- planning/mvp-m10-plan.md
```

## 8. Human decision checklist

- [ ] The scope matches S3-C.6 (one release candidate; the eight gates;
      the re-proof; the campaign with sessions and measurement; the
      surfaces; the licence manifest) and adds nothing else.
- [ ] The re-proof rule is kept: no pin re-derived before the suites run
      at `X4`; the ledger cites the `X4` run; the M8 outcome's reading is
      unchanged.
- [ ] Q3's reading is acceptable: this acceptance directs the digests'
      re-write at `X4`.
- [ ] The campaign's composition (Q2), the sessions on the board (Q11),
      and the probe's handling (Q5) are as you want them.
- [ ] The claim changes are bounded to RC4's metadata and M9's slot forms.
- [ ] The soft limit (Q14) and the stops are acceptable.
- [ ] Accept `600b78c5198c7462ca76fdb30113f3770fdf5fa7`, request revisions, or defer.

## 9. After the decision

- **Accept:** the acceptance record (this packet's decision record, the
  plan's decision record and status, the roadmap, the planning README,
  the handoff, the instructions, the development log) is one commit on
  `beryllium/mvp-m10-plan`; `beryllium/mvp-m10` starts from it; M10-2 and
  M10-3 start in parallel on `claude-opus-5.5` sub-agents; the board
  campaign waits for your confirmation that the board is free and your
  presence at the install and the restore; a fast-forward or push of the
  plan line needs its own word.
- **Request revisions:** a new commit and a new packet; this SHA is not
  treated as accepted.
- **Defer:** nothing starts; the development branch stays where it is.

**Status:** the M10 plan is proposed at exact commit `600b78c5198c7462ca76fdb30113f3770fdf5fa7` on local
branch `beryllium/mvp-m10-plan` (parent `c59003e7`), unpushed; M7's,
M8's, and M9's results are accepted; nothing of M10 has run.

**Next:** your decision on `600b78c5198c7462ca76fdb30113f3770fdf5fa7`, with Q1 to Q15.

**Action required from you:** `accept 600b78c5`, revisions, or defer.
