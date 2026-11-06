<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M10 result review summary

## Decision record

The responsible human accepted exact release-candidate commit
`d70a8535474a690920ff152e7b38a25c589adba9` (`RC4`, parent `f3f8c8d8`, over candidate tree
`X4` `a6eaa88501b1d08b9e83c734d692c82376117e77`) on 2026-11-05 by the instruction
`accept d70a8535`. Acceptance covers exactly that commit and the
bounded claim/evidence in this packet: plan errata 1 and 2, the licence
manifest's U-Boot and nolibc readings, and the evidence record's eight
departures stand. The ledger's `release_candidate_commit` is filled with
that exact SHA; release-path step 1 holds for RC4. The instruction does
not authorize a fast-forward, push, tag, publication, snapshot refresh,
release-path step 2, archive or MVP 2.0 work. Sections 1 to 9 below are
the packet as presented and are unchanged.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact release-candidate commit `d70a8535474a690920ff152e7b38a25c589adba9` (`RC4`), parent `f3f8c8d8c3051be3284306915d1d9a2a7c5ed900`, tree `aaacd987b9caa3e2c5d44da687067b9f42a9dbc4`, on local branch `beryllium/mvp-m10` |
| Candidate tree | Exact `X4` `a6eaa88501b1d08b9e83c734d692c82376117e77`; every gate and the board campaign use its images and bytes |
| Current status | M10-2 to M10-7 implemented under the accepted M10 plan (`600b78c5`; acceptance record `b5842520`); tested; exact-target `check` passes; result proposed, **not reviewed or accepted** |
| Decision requested | Accept exact commit `d70a8535`, request revisions, or defer; in accepting, accept plan errata 1 and 2, the two licence-manifest readings, and the eight departures in the evidence record |
| Successor status | MVP 2.0 not planned or started; release-path steps 2 to 7 not started; the result authorizes none of them |
| Publication status | Private internal repository; branch local and unpushed; no tag, merge, public snapshot refresh, publication or release action |

**Action expected from you:** reply exactly `accept d70a8535`, or
`revise: …`, or `defer`.

## 2. Deliverables

| Deliverable | Paths | Purpose and boundary | Most important review question |
| --- | --- | --- | --- |
| Re-proof at the integrated tree | `model/proof/Concrete*.v`; `mvp/verify/`; `mvp/results/20261104-verify-rc4-base/`; `mvp/results/20261105-verify-rc4/` | Re-read stage 1 where M9 replaced `measure()` with `measure_log()` and a gate per domain; re-prove the existing 26 theorem statements unchanged; re-run every M8 suite at `X4`; abstract model and bounded tools, never C refinement or whole-monitor proof | Is the per-domain gate and global rule the right abstraction, and is preserving every theorem statement sufficient? |
| Campaign and small tools | `mvp/tools/{k3-campaign,k3-run,k3-console,k3-uboot}.sh`/`.py`; `mvp/tools.mk`; `mvp/tests/run-tool-dry-run.sh`; `mvp/tests/fake-uboot.py`; `mvp/verify/tools/cbmc-ring.py`; `mvp/tools/{rc-record,platform-record,evidence}.py` | Make the three shell sessions board campaign groups; add `self-report-flip`; close items 115/118/121/122; fix the bundle's missing BusyBox/musl outputs; privileged tooling, covered by negative tests and a diagnostic board session | Do the session gate, late-prompt handling, fail-closed real missed-stop behavior, and retained-record checks preserve the board policy? |
| Licence manifest | `mvp/tools/licence-manifest.py`; `mvp/docs/licence-manifest.md`; `LICENSES/{BSD-2-Clause,GPL-2.0-or-later,LGPL-2.1}`; `COPYING`; `mvp/tools/check-licenses.py` | Generated, checked inventory of guest software and firmware, their notices and corresponding source; no binary distributed | Accept the U-Boot and nolibc readings in section 5? |
| Release surfaces | `mvp/docs/{claim,claim-ledger,guide,ai-assistance}.md`/`.json`; `README.md`; `mvp/tools/snapshot-readme.md`; `planning/mvp-rc-walkthrough.md` | Name release candidate 4 through the ledger; fill only S3-C.7's pre-authorized RC4 metadata and M9's fixed slots; describe the shell, measurement log, verifier and manifest | Do the words stay within the evidence, especially “diagnostic board run” and M8's inconclusive outcome? |
| Gate record | `mvp/results/20261105-rc4/` (641 files) | `rc-record` of the clean-checkout gates at `X4`: host/evaluator bundles, references and exports, model evidence/logs, rehearsal, kernel-repro, gate summaries; `--verify` passes | Does it retain enough to reproduce each PASS without implying more? |
| Board record | `mvp/results/20261105-com260-rc4/` (314 files) | 25-run COM260 campaign from system reset at `X4`, three typed sessions, M9's log judged in every applicable run, restore/preflight/audit; diagnostic evidence from one board | Are the run set, expected negatives, session typing, measurement correlation and restore evidence sufficient for RC4? |
| Evidence record | `planning/mvp-m10-evidence.md` | Exact line, gates, re-proof, tools, campaign, limits/stops/departures and claim boundary | Are every material defect and departure visible? |

From `X4` to `RC4`, 998 files change: the 641-file gate record,
33-file final verifier record, 314-file board record, the M10 evidence
record and the final claim/ledger/status updates. No runtime source,
guest, scenario, expectation, M8 specification or theorem statement
changes after `X4`.

## 3. Claim boundary

### What this exact commit supports saying

- At `X4`, every eight-gate command the accepted M10 plan names passes
  from a clean standalone checkout; the exact-target `check` also passes
  at `RC4`.
- Stage 1 has 99 source citations and 26 closed theorem reports; every
  theorem statement is byte-identical to M8's accepted `X`; the gate is
  now per domain under M9's global rule.
- Every M8 verifier suite ran at the integrated tree and at `X4`;
  verdicts/counts equal the accepted M8 result's.
- On one COM260, 25 of 25 runs from system reset passed as declared at
  `X4`'s images: four probes, twelve scenario runs, six negatives and
  three typed shell sessions; the log/reference/gate and loader
  attribution passed in every applicable run; the environment restored
  and the preflight after equalled the one before.
- The guest-software/firmware licence manifest is generated from the
  pins and checked.

### What remains trusted or assumed

- The resident BootROM, SPL, OpenSBI and U-Boot; the loader's printed MD5
  as attribution, never integrity rooted below the monitor.
- Correct pinning and behavior of the compiler, solvers, QEMU, OpenOCD-
  independent board tools and resident firmware.
- Stage 1's sequentially consistent word interleaving and ordering
  premises L1 to L5; the litmus tests are evidence about the compiled
  sequences under herd7's RVWMO model, not a proof of the C or hardware.
- The board's lifecycle/debug state: not determined as of 2026-11-05;
  no JTAG probe performed (item 129).

### Evidence unavailable or `NOT RUN`

- No second board, long-duration stress run, fault injection below HS,
  physical attack, power-cut recovery, JTAG/debug-state probe, or
  independent hardware validation.
- No C refinement, trap-vector proof, source-to-binary validation, whole-
  system proof, certification, attestation, secure-boot qualification, or
  release-repository gate run.
- No proof of the WP/CN-open goals or of the ring's 1,384 open bounded
  properties; no new arm round (Q6's default).

### Explicit non-implementations

No dynamic management, device/DMA path, service domain, general guest,
guest IMA, hardware root of trust, attestation, migration, overcommit,
runtime policy parser, scheduler, kexec, release migration, tag,
publication or MVP 2.0 work.

## 4. Security and correctness invariants

| Property | Contract / implementation | Evidence |
| --- | --- | --- |
| No domain starts before its launch gate passes; a failure starts none | M9 global rule; `measure_log()`, `log_launch()`, `be_mvp_log_gate()`; stage-1 `global_rule`, `entry_after_gate`, `gate_false_no_start` | stage 1 PASS at `X4`; wrong-measurement QEMU and board negative; C-52 |
| Published block contents and single-writer footprints | stage-1 P1/P2; `publish_blocks`, hart binding, ring/input extents | 26 unchanged theorem statements; L1; C-54/C-55 |
| Ring safety and round-robin drain | stage-1 P3/P4/P8; `mvp-ring.c`, drain functions | stage-1 proofs; L2-L5; ring bounded model check OPEN at its bound; C-56/U-18 |
| Denial and management outcomes remain as declared | stage-1 P5/P6; sealed policy/grants; capture checker | stage-1 proofs, host/QEMU suites, `te-poc`/`anchor` board runs and negatives; C-57/C-58 |
| Console bytes go only to the focused, input-granted domain; output invariants remain | M7 input ring/parser, `guest-type`, item 8 | 160 host cases/395 mutations; 6 QEMU sessions; M7 characterization; RC4's three 16-step/130-key sessions; C-47/C-48 |
| Measurement records and registers equal the placed/sealed inputs and post-link reference | log profile v1; `mvp-log.c`, `measure_log`, references and log module | host test, 300/459 capture suite, 64 QEMU runs, RC4's board runs, `self-report-flip`; C-51/C-53 |
| Loader observation is not overstated | one U-Boot autoboot block, exact staged image/size/MD5; unmeasured firmware | capture checker, RC4 record; U-16; claim required limit |
| Board saved environment returns to its recorded state | S3-A policy, `k3-env.sh` | record 3 = record 1 under the V rule; Fedora autoboot; preflight pair equal; 49/49 reset/banner audit |

## 5. Review history and resolved findings

| Finding / decision | Resolution |
| --- | --- |
| M10 plan D-3/Q2 adds 4 + 12 + 6 + 3 as 26 | Plan erratum 1: **25**; implementation and record use 25 |
| M8 bridge lane reached 12,248 of 12,000 by its added-lines rule | Stop 7 returned; human chose `reset-13000`; nothing cut (erratum 2) |
| `dtb_plan()` inserted `rdinit=/init-shell` twice for two shell expectations | Fixed `da4fd1b9`; discriminating image-check/dry-run coverage; ledger pins refreshed |
| Timed-out cvc5 jobs left about 1 GiB temporary files | Per-job 0700 `TMPDIR`, removed in `finally`; timeout and success self-tests (item 118 closed) |
| Late prompt could echo retry `s` and be mistaken for a missed stop | Status-5 late-prompt path records and clears it; old code fails the new case; passing board session has no late prompt/MISSED (item 121 closed) |
| First board-session install had a real missed stop | Fail-closed behavior was correct: prompt immediately followed by NUL and ROM boot output, no retry sent. Human chose `restore-fix-restart`; environment restored; no campaign run; second session passed. |
| Release record omitted M9 references/exports | `rc-record.py` requires/copies references and QEMU/session/rehearsal exports; six refusals (item 122 closed) |
| Evidence bundle omitted M7's standalone BusyBox/musl outputs | `a6eaa885`; focused self-tests PASS; first all-green candidate superseded; all eight gates rerun at new `X4` |
| Platform record omitted console-input details | “Console input on K3” section and grouped self-test cases; M7 and RC4 records render it (item 115 closed) |
| U-Boot licence interpretation | Manifest says project-level `GPL-2.0-or-later`, with the project's `Licenses/README` caveat that the whole is redistributable under v2 and most files allow later; human to accept or request a different row |
| nolibc not named by Q7 | Included because it is compiled into the init: `LGPL-2.1 OR MIT`, with a third new licence text; human to accept or request its removal/wording |
| M10 D-4 says the release-candidate commit is filled at creation “as RC3's was” | Reading corrected in the evidence record: a commit cannot contain its own SHA; `RC4` leaves the field null, and an acceptance record fills it if accepted, as debt sweep 3 did for RC3 |

## 6. Validation and retained evidence

### At exact candidate tree `X4`

Clean standalone checkout, 2026-11-05 13:22-17:32 UTC:

| Command | Result |
| --- | --- |
| `./mvp/mvp tool-lock check` | PASS, roles 32, closure 259 |
| `./mvp/mvp check` | PASS |
| `./mvp/mvp evaluate` | PASS, 339/339 images byte-identical |
| `./mvp/mvp uboot-rehearsal` | PASS, cases 7, attempts 12, refused 5 |
| `make -C mvp kernel-repro …` | PASS, 23 outputs identical |
| `./be model-check` | PASS, stage 1 included |
| `./be evaluate` | PASS, rootless model evidence |
| `./mvp/mvp verify` | PASS, `wall_seconds=13254`, every suite as section 3 states |

`mvp/results/20261105-rc4/` verifies; `mvp/results/20261105-verify-rc4/`
is the retained verifier record. The previous all-green run at
`7a5c7062` is diagnosis only: its `rc-record` found the BusyBox/musl
omission, which moved `X4` and forced the full rerun.

### On the COM260 at `X4`'s images

2026-11-05 22:20-22:42 UTC, human present at install and restore:

```text
BE_MVP_K3_CAMPAIGN: PASS runs=25 groups=19 sessions=3
```

All captures, negatives, logs/registers/references, sessions, reset/banner
audit, restore and preflight checks pass. Record:
`mvp/results/20261105-com260-rc4/`, 314 files; `evidence.py --verify`
and privacy check PASS. The board was restored and left on Fedora.

### At exact review target `RC4`

`./mvp/mvp check LINUX_GIT=<local mirror>` ran from a clean tree at
`d70a8535` on 2026-11-05 23:08-23:20 UTC:

```text
BE_MVP_CHECK: PASS
BE_MVP_QEMU: PASS runs=64 attempts=76 refused=12
BE_MVP_SESSIONS: PASS sessions=6 attempts=6 refused=0
BE_MVP_CAPTURE_SELF_TEST: PASS cases=300 failed=0
BE_MVP_CAPTURE_MUTATIONS: PASS mutations=459 rejected=459
BE_MVP_LICENCE_MANIFEST: PASS components=8 identifiers=6 sources=2 outputs=23 pins=3
BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=58 boundary=18
```

The development bundle passed (`files=521 images=341 log_exports=58`);
the reference self-test passed 41 cases and each toolchain's 29 images
matched; budgets measured 50 images. `node scripts/check-doc-sources.mjs`,
`git diff --check`, `evidence.py --verify` on the board record and
`rc-record --verify` also pass at the exact content committed in `RC4`.

Soft limits: M10 1,429/2,500; model lane 8,655/12,000; bridge lane
12,248/13,000; checker-to-monitor 2.349 (reported, not limited).

## 7. Recommended human review sequence

1. Plan outcome and departures:
   `planning/mvp-m10-plan.md`, then
   `planning/mvp-m10-evidence.md` sections “Outcome first”, “Soft limits
   and stops”, “Departures and readings for review”.
2. Claim and ledger diff from `X4` to `RC4`:
   `mvp/docs/claim.md`, the ledger release table and C-47/C-48/C-51 to
   C-58/U-16, then `guide.md` and `ai-assistance.md`.
3. M10-2:
   `model/proof/Concrete.v`, `ConcreteClaims.v`, and the two verifier
   records; confirm theorem statements unchanged and the outcome
   remains inconclusive.
4. M10-3:
   campaign/session changes, item 121, `rc-record.py`, platform record,
   licence manifest and texts.
5. The gate and board records:
   read `rc.txt`, both `README.md` files, `summary.md`,
   `platform-record.md`, then a sample scenario, negative and shell run.

Copyable read-only commands:

```sh
git worktree add --detach /tmp/be-rc4-review d70a8535474a690920ff152e7b38a25c589adba9
git -C /tmp/be-rc4-review show --stat HEAD
git -C /tmp/be-rc4-review diff a6eaa88501b1d08b9e83c734d692c82376117e77 HEAD -- \
  mvp/docs planning/mvp-m10-evidence.md planning/mvp-m10-plan.md README.md
git -C /tmp/be-rc4-review show d70a8535:mvp/results/20261105-rc4/rc.txt
git -C /tmp/be-rc4-review show d70a8535:mvp/results/20261105-com260-rc4/summary.md
```

## 8. Human decision checklist

- [ ] The result stays within the accepted M10 plan (including errata 1
      and 2) and no monitor source changed after `X4`.
- [ ] The M8 outcome remains accurately inconclusive; no abstract or
      bounded result is promoted to a C/whole-monitor proof.
- [ ] The claim and ledger methods match the retained gate/QEMU/board
      evidence and their non-claims.
- [ ] The three typed board sessions and measurement correlation are
      sufficient and item 8's operator boundary is acceptable.
- [ ] The first stopped session and the BusyBox/musl integration defect
      are adequately disclosed.
- [ ] U-Boot's `GPL-2.0-or-later` row and nolibc's
      `LGPL-2.1 OR MIT` row are acceptable.
- [ ] The platform/JTAG assumption remains explicit and not inferred.
- [ ] Release-path steps 2 to 7, push/publication and MVP 2.0 remain
      excluded.
- [ ] Accept exact `d70a8535474a690920ff152e7b38a25c589adba9`,
      request revisions, or defer.

## 9. After the decision

- **Accept:** the human explicitly authorizes recording acceptance of
  exact `d70a8535`; the acceptance record fills the ledger's
  `release_candidate_commit` with that SHA and states that release-path
  step 1 holds for RC4. Any fast-forward/push, release-path step 2,
  snapshot refresh or successor needs its own instruction.
- **Request revisions:** make a new exact commit and packet; this SHA is
  not treated as accepted.
- **Defer:** preserve this local branch and do not start dependent work.

**Status:** exact `RC4` `d70a8535` is implemented, tested and proposed
on local branch `beryllium/mvp-m10`; it is not accepted, pushed, merged,
tagged, published or released.

**Next:** the responsible human's decision on exact `d70a8535`.

**Action required from you:** reply exactly `accept d70a8535`, or
`revise: …`, or `defer`.
