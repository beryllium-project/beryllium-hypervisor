<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M6 result review and acceptance record

This packet presents the result of M6, "The MVP core profile and release
candidate 3", the milestone the accepted
[Plan revision S3-B](mvp-plan.md#plan-revision-s3-b-release-candidate-3-and-milestone-m6-the-mvp-core-profile)
added to the [MVP plan](mvp-plan.md) on the responsible human's
direction `we will go with RC3 first`: the "MVP core profile" debt (M0
Plan revision M0-A.5: the monitor re-executed the frozen single-hart
fixed profile and built fixture roots and pages it never used) retired
before the release path's steps 2 to 7, with the result presented as
MVP 1.0 release candidate 3. It was implemented under the accepted
[M6 plan](mvp-m6-plan.md) (`b2c62d54`), whose
[acceptance record](mvp-m6-plan-review-summary.md) holds its
authorization. It also records the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`89ef04e9354c08ebadbaeb88d553c5081a00b84d` (the release-candidate commit
`RC3`, parent `ebc49a889273c811836c3d39fb0fc9bfe808be4c`, the candidate
tree `X3`; tree `a6ce6d3c`) as the M6 result and MVP 1.0 release
candidate 3 on 2026-10-31 (2026-10-30 in the human's time zone). The
instruction, given in reply to this packet's request to accept, revise,
or defer that exact commit, was `accept 89ef04e9, proceed`. The
abbreviation was checked to resolve uniquely to that commit
(`git rev-parse --disambiguate=89ef04e9`). `proceed` directed no push,
merge, tag, publication, or release: the packet's section 9 and the
standing rules give each of those its own instruction, so it was read
as continuing with the work that needs no further gate (the record of
this decision, and the development log's follow-ups), with the release
path's step 2, the human's own selection of what migrates, and any push
or merge left to the human.

- **Scope:** acceptance covers exactly that commit and the claim boundary
  in section 3, the thirteen departures of section 3 included, the
  deferral of the model instance (U-13) among them. Sections 2 to 8 are
  the packet as presented, apart from a note above the section 8
  checklist. Section 1's status rows and the closing lines of section 9
  now show the outcome. The decision itself is recorded only here and
  in the M6 plan's status record and the MVP plan's S3-B addendum.
- **What it is:** the release path's step 1 for the latest candidate.
  Release candidate 2 (`3867c66c`) and release candidate 1 (`c5df0cfa`)
  are accepted history; the "MVP core profile" debt (M0 Plan revision
  M0-A.5, deferred by D3 and S1 H22) is retired. Steps 2 to 7 of the
  release path are not started, and each needs its own instruction.
- **What it is not:** no push (`beryllium/mvp-m6` and
  `beryllium/mvp-m6-plan` stay local), no merge into the development
  branch (`cd9cfa5f` locally and on the private `origin`), no tag,
  publication, or release; no hardware validation, qualification, or
  formal-verification claim; no model generalization or executor
  contract (the first verification plan's); no kexec use.
- **Evidence terms:** the board results are diagnostic bring-up evidence
  for one COM260, one reported SBI identity and version, and one U-Boot
  build as its banner reports it, at the candidate's images; the gates
  are host tests, adversarial tests, deterministic reports, semantic
  checks, emulation, the proof about the abstract model on the
  regenerated policy instances, and differential agreement.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `89ef04e9354c08ebadbaeb88d553c5081a00b84d` (tree `a6ce6d3c`), the release-candidate commit `RC3`, parent `ebc49a889273c811836c3d39fb0fc9bfe808be4c`, the candidate tree `X3` (tree `0a60a35f`), on local branch `beryllium/mvp-m6` from the M6 acceptance record `366c8af4`. `RC3` adds, over `X3`, the two retained records, the ledger rows that cite them, the evidence record, the development log's closing entry, and one `.gitattributes` line; no source byte differs between `X3` and `RC3`. |
| Current status | **Responsible-human accepted on 2026-10-31** (instruction `accept 89ef04e9, proceed`; the [decision record](#decision-record)). As presented: implemented, checked on the host and in the pinned evaluator, rehearsed in QEMU, and run on the board. At `X3`, from this checkout clean at `X3` on `l1` (2026-10-31, 03:54 to 04:08 UTC), the seven gates pass and are recorded in `mvp/results/20261031-rc3/`; on 2026-10-31 (04:12 to 04:38 UTC) twenty board runs from system reset at `X3`'s images passed as declared on the COM260 with every count equal to release candidate 2's, recorded in `mvp/results/20261031-com260-rc3/`; `./mvp/mvp check` passes at `RC3` (`BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=46 boundary=13`). Nothing is pushed. |
| Decision requested | As presented: accept exact commit `89ef04e9` as the M6 result and MVP 1.0 release candidate 3; or request revisions; or defer. The claim's text and required limit are unchanged from release candidate 2 (stop condition 2 was not reached). Outcome: accepted. |
| Successor status | As presented and after the decision: not started and not authorized: every release-path step after the first (the selection of what migrates, the clean public repository, a tag, the publication gate), any merge of `beryllium/mvp-m6` or `beryllium/mvp-m6-plan` into the development branch, any push, any source change, and any model generalization (the first verification plan's). |
| Publication status | Private repository. As presented and after the decision: `beryllium/mvp-m6` and `beryllium/mvp-m6-plan` are local and unpushed (the acceptance instruction directed no push); the development branch `beryllium/single-hart-runtime-r0` is at `cd9cfa5f` locally and on the private `origin`. No tag, publication, or release. |

As presented: please review exact commit `89ef04e9` and accept it,
request revisions, or defer. Outcome: accepted; see the
[decision record](#decision-record).

## 2. Deliverables

| Deliverable | Paths | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| The core profile (M6-2, `356150bb`, `bd16099a`; `32850958`, `53c9ad8e`) | `mvp/tools/port.py` (+435; 43 counted rules), `mvp/tools/gen-scenario.py` (+259), `mvp/tools/policy-check.py` (+115), `mvp/src/mvp-core.c`/`.h` (new), `mvp/src/mvp-runtime.c` (`seal_config`), `mvp/src/mvp-monitor.lds` (new), `mvp/src/mvp-layout.h`, `mvp/tests/config-test.c` (new) | Each scenario's own inventory and proposal, generated from its policy, labeling, and layout and checked against the authority report; copied, validated, sealed, and derived at boot by the ported, widened accepted R1 mechanism; the derived roots as the builder's, the measurement's, and the control loop's input; the sealed configuration compared with the linked record, failing closed; `BE_MVP:00 BOOT_VALIDATED` and `CONFIG_SEALED … identity=<16 hex>` in place of `BE_R3:01` to `:06`; the fixture roots, pages, and guest code gone | The accepted R1 structures are widened by port rules, not edited; a semantic change would show in the host tests (36 scenarios, 139 assertions, 29 single defects each refused for its own class, GCC = Clang) | Does the widened validator refuse every malformed configuration the plan's D-1 names, and does the generated configuration agree with the authority report for every scenario (stop condition 11)? |
| The executor and the layers (M6-3, `acda84bc`, `eadd030c`) | `mvp/src/mvp-executor.c`/`.h` (new; 28 `be_mvp_exec_*` functions), `mvp/tests/check-image.py` (the seam rule), `mvp/README.md` (the layer table) | Every privileged effect the MVP's C performs behind one file, called from the decision code and nowhere else; the image checker refuses a linked image in which another MVP function names an assembly or accepted privileged helper (one mutation); the proof-bearing subset named: 6,285 code lines, support 1,105, the executor 177, platform and assembly 930 | A code restructuring with no behavior change: the capture checker's counts equal M5's for every scenario in QEMU and on the board; no contract is written | Is the seam complete (no privileged effect outside the executor), and is the checker's rule the right witness? |
| The model (M6-4, deferred) | `mvp/docs/claim-ledger.json` U-13; `planning/mvp-m6-evidence.md`; no `model/` structure, proof, or theorem changed | `Model.v`'s `frame` and `gpa` are closed enumerations of the fixed profile, so the MVP's inventory is not an additive instance (Q4's default: deferred with the reason recorded); M3's nat-indexed policy layer already holds te-poc and anchor | The core profile is validated by the ported C, the host tests, the image checker's binding, QEMU, and the board, not by the Rocq model (U-13) | Is the deferral's reason sound, and is U-13's statement of the boundary complete? |
| The model's pinned identities (`ebc49a88`) | `model/tests/unit/policy_test.c` (+3 −3), `model/tests/check-reports.mjs` (+6 −6) | M3's policy instances 2 and 3 are generated from the scenarios, so Q3's `kexec_fdt` removal changed their labeling and configuration identities and object counts; the two test files that pin those values are refreshed; the Rocq proofs pass unchanged on the regenerated instances (`instances=generated`) | Found by the first gates run (README item 88); no theorem changed, so stop condition 4 does not apply | Are the refreshed values the regenerated ones and nothing else (the view and policy identities unchanged)? |
| The release surfaces (M6-5, `4cc5c53a`) | `mvp/docs/guide.md` (sections 1, 3, 6), `mvp/docs/ai-assistance.md`, `mvp/docs/claim-ledger.json`/`.md` (C-40, C-41, U-13; C-10's capture-checker pin) | The boot story for the new markers (Q11); release candidate 3's disclosure; the ledger's rows for the boot's validation and sealing, the executor seam, and the model boundary | The claim's text and required limit unchanged | Do C-40 and C-41 say no more than the tests and checkers support? |
| The gates record (M6-6, in `RC3`) | `mvp/results/20261031-rc3/` (394 files) | `rc.txt` with `X3`, its tree, the host, the lock's and closure's SHA-256, and each gate's PASS line and times; the bundle; the evaluator record (253 of 253 images identical); the model evidence; seven rehearsal cases; `kernel-repro` | One host, one day, the locked tools | Does every gate log name `X3` and end in its PASS line? |
| The board record (M6-7, in `RC3`) | `mvp/results/20261031-com260-rc3/` (197 files) | Twenty runs from reset at `X3`'s images with their captures, verdicts, attribution, and reset records; the keystroke log; the environment verdicts (records 1 to 3, the install, 13 selects, the restore); the staging record; the preflights before and after; the hand-written Serial log paragraph | Diagnostic bring-up evidence for one board; the preflight pair differs in the kernel release, with the cause recorded (item 90) | Are the twenty captures the declared ones, each attributed to its image, with the M6 prelude and release candidate 2's counts? |
| The evidence record (M6-8, in `RC3`) | `planning/mvp-m6-evidence.md` | The files and counts, the departures, the model deferral, the gates, the records, the campaign, the stops and limits, the open items, the claim boundary | Records what ran; claims nothing beyond its lines | Does it match the records it describes? |
| The development log | `mvp/README.md` (M6-2 to M6-8 entries, the layer table, the port's rules, open items 87 to 91) | The log and the open items | — | Are the open items complete and honest? |

Exact changed-file inventory outside `mvp/results/`:

```text
# git diff --name-status 366c8af4 89ef04e9 | grep -v '^A.mvp/results/'
M	.gitattributes
M	model/tests/check-reports.mjs
M	model/tests/unit/policy_test.c
M	mvp/Makefile
M	mvp/README.md
M	mvp/docs/ai-assistance.md
M	mvp/docs/claim-ledger.json
M	mvp/docs/claim-ledger.md
M	mvp/docs/guide.md
M	mvp/scenarios/anchor/scenario.json
M	mvp/scenarios/te-poc/scenario.json
A	mvp/src/mvp-core.c
A	mvp/src/mvp-core.h
A	mvp/src/mvp-executor.c
A	mvp/src/mvp-executor.h
M	mvp/src/mvp-hartmain.c
M	mvp/src/mvp-layout.h
A	mvp/src/mvp-monitor.lds
M	mvp/src/mvp-payload.c
M	mvp/src/mvp-payload.h
M	mvp/src/mvp-platform.h
M	mvp/src/mvp-probe.c
M	mvp/src/mvp-probe.h
M	mvp/src/mvp-runtime.c
M	mvp/src/mvp-trap.S
M	mvp/tests/check-capture.py
M	mvp/tests/check-image.py
A	mvp/tests/config-test.c
A	mvp/tests/fixtures/pre-m6/anchor/authority-report.json
A	mvp/tests/fixtures/pre-m6/anchor/expect/{anchor,no-grant-check,response-writable,secret-shared,wrong-measurement}.json
A	mvp/tests/fixtures/pre-m6/te-poc/authority-report.json
A	mvp/tests/fixtures/pre-m6/te-poc/expect/{no-inject,reader-write,te-poc}.json
A	mvp/tests/fixtures/qemu-{anchor,no-grant-check,no-inject,payload,probe-platform,probe-vmid-distinct,probe-vmid-shared,reader-write,te-poc,two-guests,wrong-measurement}-gcc-m6.log
A	mvp/tests/fixtures/qemu-rva23-clang-m6-refused.log
M	mvp/tests/payload-test.c
M	mvp/tests/run-tool-dry-run.sh
M	mvp/tests/test-platform-probe.py
M	mvp/tools/gen-scenario.py
M	mvp/tools/platform-probe.py
M	mvp/tools/policy-check.py
M	mvp/tools/port.py
A	planning/mvp-m6-evidence.md
```

`git diff --stat 366c8af4 89ef04e9 -- mvp/guest mvp/shim
mvp/scenarios/*/policy.te model/src model/include model/proof
model/fixtures include virt arch bringup tests` is empty: no guest
input, shim, scenario policy, model structure, proof, or theorem, or
accepted R0-R7 or B0-B7 byte changed. The scenarios' `scenario.json`
files lose their `kexec_fdt` object (Q3) and nothing else. New code by
the plan's counting rule: 3,258 added lines (754 deleted) against the
limit of 4,000.

## 3. Claim boundary

**Supported by `RC3`:** the monitor's boot copies, validates, seals, and
derives each scenario's own configuration through the ported accepted
mechanism and fails closed when the derived records differ from the
linked ones (C-40); the generated configuration agrees with the
authority report for every scenario (stop condition 11 did not fire);
every privileged effect the MVP's C performs is behind the executor, and
the image checker refuses an image with one elsewhere (C-41); the
behavior the capture checker sees is unchanged: every scenario's
records, denials, management counts, and exits equal release candidate
2's in QEMU (58 runs) and on the board (20 of 20 from system reset at
`X3`'s images, the M6 prelude printed in every run), with the five
negatives failing as declared; the seven gates pass at `X3` from a clean
checkout; the lock's tools built every image byte-identically inside the
pinned evaluator (253 of 253); the U-Boot rehearsal passes in QEMU for
every scenario image of both toolchains; U-Boot's saved environment was
installed and restored (record 3 equals record 1 byte for byte, and both
equal release candidate 2's); the Rocq proofs pass unchanged on the
regenerated policy instances.

**Trusted or assumed:** the accepted M0 to M5 results, release candidate
2's board path and board facts (unchanged), and M3's model work; that
widening the accepted R1 structures by port rules does not change their
semantics (the host tests on both compilers are the check, not a proof);
the external Linux input by its pins; the board's firmware and U-Boot by
their banners and the SBI identity Fedora's log reports, not hashed;
`md5sum` as the digest witness; the `k3ctl` client (by its SHA-256) and
the dongle, outside the lock; the operator's picocom session and its log
as the serial witness; the responsible human's statements that the
board was free and theirs alone from the install to the restore and that
the recorded `bootcmd` (its digest equal to release candidate 2's) is
their default with no one-shot boot pending.

**Not run or unavailable:** hardware validation, qualification, or
formal verification of any kind; any model instance of the MVP core
profile (U-13; deferred to the first verification plan); any contract on
the executor's functions; any comparison of the NOR's stored bytes; any
hash of the firmware; a second board.

**Explicitly not implemented:** any release-path step after the first;
any kexec launch (the standing rule); any change to the claim's text or
required limit, the guests, the scenarios' policies, the board tools'
behavior, or `model/`'s structures, proofs, or theorems; a domain hart
checked against the platform's hart count at the seal (the firmware's
answer at the hart's start remains the check).

**Departures for your attention** (each recorded in the evidence record
and `mvp/README.md`): (1) `KEXEC_FDT_*` constants stay in the capture
checker as test-only constants for the retained kexec records, though
D-4 and Q3 remove them from the monitor (they are gone from
`mvp-layout.h`); (2) a domain's hart is checked distinct and not the
control hart, not against the platform count (Q1's "plus the platform
count"); the `hart-start` variant still fails at its start, as declared;
(3) the probe images seal two-guests' configuration and print `roots=2
harts=0,1,2` (D-3 is silent on the probes); (4) M1's and M2's fixtures
are kept and judged against pre-M6 expectations so both prelude forms
are tested (Q2 says regenerated); (5) the executor seam is enforced by
an image-checker rule and a mutation, beyond D-5's letter; (6) the model
instance is deferred with its reason (Q4's default); (7) the accepted
plan's Q3 says "open item 59 closes": a transcription error, item 59 is
unrelated, and nothing closes (item 87); (8) two of the model's test
files changed to refresh pinned identities after Q3 changed the
generated instances (item 88; D-6 says additive only, and no theorem
changed); (9) the console tool's tmux target was given as
`k3-console-1:0` because the operator's session had gained a second
window (item 89); (10) the preflight pair differs in the kernel release
because the Fedora before the session had been booted by hand as a
one-shot test, with nothing saved (item 90); (11) the wrapper took a
stray `k3-env install` argument as a make goal after the install's PASS
(item 91); (12) `board-evidence` was re-made once from the stored
session so that its tree state reads `clean`; (13) `.gitattributes`
changed in `RC3`, as in M4's and M5's release-candidate commits, for the
board excerpts' whitespace, now for every release candidate's board
record.

## 4. Load-bearing invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| The sealed configuration is the scenario's own | M6 plan D-1, D-2; stop 11 | `gen-scenario.py`'s `core_config` from `policy-check.py`'s `core()`; `core_agrees()` against the authority report; `seal_config()` compares the derived records with the linked ones | `BE_MVP_HOST: PASS config scenarios=36 assertions=139 gcc=clang`; `CONFIG_SEALED` with the scenario's counts and identity in every QEMU run and board run; the image checker's configuration rule |
| A malformed configuration is refused for its own class | D-1 | the widened validator (channels one per frame, authority rights equal to channel-end rights, owner checks, disjoint GPA ranges, one guest-code window per domain, distinct VMIDs and harts, hart 0 never a domain hart) | `config-test.c`: 29 single defects each refused with its own code |
| No privileged effect outside the executor | D-5 | `mvp-executor.c`'s 28 functions; the image checker's seam rule | the rule's mutation (`time read outside the executor`) rejected; the layer table |
| The layout's extents do not move | D-4; stop 3 | `mvp-monitor.lds` within the first `0x34000` bytes; `BE_MVP_CORE_BYTES`, `BE_MVP_STAGING_BYTES` | `BE_MVP_BUDGETS: PASS measured=32`; the preflight's region check and the platform record unchanged; the board's `Loading Device Tree` and shim addresses equal release candidate 2's |
| Behavior unchanged | M6-3's exit; stop 5 | — | the capture checker's counts equal release candidate 2's for every scenario in QEMU and on the board |
| Only the template lines are typed; nothing saved but at a fresh prompt after a passing comparison; every reset `k3ctl` under the port-open rule | M5 plan (unchanged) | `k3-console.sh`, `k3-env.sh` | the keystroke log: 91 keys, every line a template; 15 `saveenv` each after a passing comparison; 39 resets with their reasons; record 3 = record 1 |
| A run is its image's | M5 plan "Run attribution and distinctness" | `k3-run.sh`'s five conditions | every `run.txt` `attribution=PASS selected=yes staged_sha256=yes size_md5=yes check=yes`; the 14 MD5s distinct |
| No identifying string in a record | B0's rule; M4-A; Q8 | `evidence.py`, `claim-ledger.py check_privacy` | `identifying()` finds nothing in either record; `claim ledger privacy: PASS files=549` |
| Every gate's evidence binds to `X3` | M6-6 | `rc-record.py` | `BE_MVP_RC_RECORD: PASS … commit=ebc49a88… files=394`; `--verify` PASS |
| The retained records are never edited | M0-B's rules | `MANIFEST.sha256`; `--verify` | the seven earlier records verify unchanged; the two new ones verify |

## 5. Review history, stops, and errata

| Event | Resolution |
| --- | --- |
| M6-2 and M6-3 each implemented by a `claude-opus-5.5` sub-agent in a worktree and reviewed line by line by the orchestrating model before the merge | Follow-ups `32850958` (the core and staging reserve by their own names; the removed constants; renames) and `53c9ad8e` (C-10's capture-checker pin) by the orchestrating model |
| Soft limit checkpoints: 2,545 lines after M6-2, 3,231 after M6-3, 3,258 at `X3` against 4,000 | Within the limit; stop 6 did not fire |
| M6-4: `Model.v`'s closed `frame` and `gpa` enumerations | Deferred with the reason recorded (Q4's default); U-13; no theorem changed |
| `claim-ledger.py check` failed on U-13's coverage word | Reworded to the fixed vocabulary before the M6-5 commit |
| The first gates run at `4cc5c53a` failed `./be model-check` on a pinned instance identity | The model's policy instances follow the scenarios (Q3's `kexec_fdt` removal); two test files' pins refreshed (`ebc49a88`); `X3` moved; the gates re-run (item 88). The M6-4 exit had not been run at M6-4 |
| The console tool's pane check stopped `k3-env record` (the tmux session's active window was not picocom's) | Nothing typed, no reset; re-run with the window named (item 89) |
| The preflight pair differs in the kernel release | A hand-typed one-shot test boot before the session; the saved environment is unchanged and shown restored (item 90; C-45 says so) |
| The wrapper took a stray install argument as a make goal | After the install's PASS; nothing further on the board (item 91) |
| `board-evidence`'s first copy read `source_tree=dirty changed=1` (the untracked gates record in the tree) | Re-made from the stored session with the tree clean; the two copies differ in that line and the hashes that carry it |

**Open for human judgment:** the thirteen departures of section 3;
README item 80 (the dongle's power tap) as before; items 89 and 91 as
later source changes if wanted; the deferral of the model instance.

**Not run by SOP:** no review of the result by another model; no
separate scope review; no deep security review. Implementation ran on
`claude-opus-5.5` sub-agents at `max` effort with the `long_context`
tier for M6-2 and M6-3, orchestrated and reviewed line by line by
`claude-fable-5.1`, which also wrote M6-5's surfaces, ran the gates, the
board session, and the record tools, refreshed the model's pins, and
wrote the evidence record and this packet.

## 6. Validation and retained evidence

All on the workstation `l1` (Fedora Linux 44, x86_64), the lock's tools
(`lock_sha256=2f1b732dcf24`), 2026-10-31 UTC. The evidence record has
the gate table with times and the run table.

| Command | When | Boundary | Result |
| --- | --- | --- | --- |
| `./mvp/mvp tool-lock check` | 03:54, clean at `X3` | the 32 locked roles on this host | `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259` |
| `./mvp/mvp check` | 03:54 to 03:59, clean at `X3` | host unit tests (the new `config` suite among eight), the image and capture checkers with their mutations, the policy checks, the dry run, the QEMU suite (58 runs, 70 attempts), the budgets, the ledger | `BE_MVP_CHECK: PASS` |
| `./mvp/mvp evaluate` | 03:59 to 04:04, clean at `X3` | the same inside the pinned evaluator; image identity | `BE_MVP_EVALUATE: PASS`; `BE_MVP_IMAGE_IDENTITY: PASS images=253 same=253 differing=0` |
| `./mvp/mvp uboot-rehearsal` | 04:04 to 04:06, clean at `X3` | emulation: six scenario images booted from ext4 under B3's pinned U-Boot and judged in `uboot` mode; the fall-through | `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=7 refused=0` |
| `make -C mvp kernel-repro` | 04:06, clean at `X3` | the guest kernel's reproducible build | `BE_MVP_KERNEL_REPRO: PASS outputs=15 identical` |
| `./be model-check`, `./be evaluate` | 04:06 to 04:08, clean at `X3` | the accepted M3 model work on the regenerated instances: proofs about the abstract model, differential agreement | `… evidence: PASS` (`instances=generated`); `BE_EVALUATION: Model 0.2 rootless evidence PASS` |
| `./mvp/mvp rc-record` | 04:09, clean at `X3` | the seven gates' record from named inputs each checked to name `X3` | `BE_MVP_RC_RECORD: PASS … commit=ebc49a88… files=394`; `--verify` PASS |
| The board session (`k3-preflight`, `k3-stage`, `k3-env record`/`install`/`restore`, `k3-campaign`) | 04:12 to 04:38, at `X3`'s images | diagnostic board runs on one COM260 | 20 of 20 as declared; the restore rule satisfied; no stop |
| `./mvp/mvp board-evidence` | after the session, clean at `X3` | the board record from the session's stored captures and logs, each run judged again | `BE_MVP_EVIDENCE: PASS board … runs=20 pass=20 fail=0 refused=0 stop=0`; `--verify` PASS |
| `./mvp/mvp check` | clean at `RC3` | the ledger's 46 rows against the committed records; the privacy rule over 549 record files | `BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=46 boundary=13`; `BE_MVP_CHECK: PASS` |
| `git diff --check` | before `X3` and before `RC3` | whitespace | PASS |

The retained evidence: `mvp/results/20261031-rc3/` and
`mvp/results/20261031-com260-rc3/` (manifests `c9674b53…` and
`79460ad7…`), the ledger rows C-10, C-40 to C-46, and U-13, and
`planning/mvp-m6-evidence.md`. Not retained: the raw serial log (the
operator's, outside the repository), the full `printenv` texts (the
private store), the gates' driver logs (`build/mvp/rc3-gates/`), the
first gates attempt (`build/mvp/rc3-gates-attempt-1-4cc5c53a/`), and
the first copy of the board record.

## 7. Recommended human review sequence

1. Section 1 and the claim boundary (section 3), then the ledger's C-40,
   C-41, and U-13 against `mvp/src/mvp-runtime.c`'s `seal_config`,
   `mvp/src/mvp-executor.c`, and the M6-4 entry in `mvp/README.md`.
2. The evidence record `planning/mvp-m6-evidence.md`, then
   `mvp/results/20261031-com260-rc3/mvp/session/env/` (the verdicts),
   `platform-record.md`'s preflight pair (the `kernel` row) and resets,
   and `mvp/results/20261031-rc3/rc.txt`.
3. `mvp/tools/port.py`'s core rules and `mvp/tests/config-test.c`'s
   defects; `mvp/tools/gen-scenario.py`'s `core_agrees`.
4. `mvp/tests/check-image.py`'s seam rule and `mvp/tests/check-capture.py`'s
   two prelude forms.
5. `model/tests/unit/policy_test.c` and `model/tests/check-reports.mjs`
   at `ebc49a88` (the refreshed pins) against `make -C model policy-run`.
6. `mvp/docs/guide.md` sections 1, 3, and 6; the development log
   `mvp/README.md` from the M6-2 entry and items 87 to 91.

Read-only commands, in a detached worktree so local changes cannot affect
what you read or run:

```sh
git worktree add --detach /tmp/be-m6-review 89ef04e9354c08ebadbaeb88d553c5081a00b84d
cd /tmp/be-m6-review
git --no-pager log --oneline 366c8af4..HEAD
git --no-pager diff --stat ebc49a88 HEAD -- . ':!mvp/results'
git --no-pager diff --stat 366c8af4 HEAD -- mvp/guest mvp/shim model/src model/include model/proof model/fixtures
python3 -B mvp/tools/evidence.py --verify mvp/results/20261031-com260-rc3
python3 -B mvp/tools/rc-record.py --verify mvp/results/20261031-rc3
python3 -B mvp/tools/claim-ledger.py check
cat mvp/results/20261031-com260-rc3/mvp/session/env/records.txt \
    mvp/results/20261031-com260-rc3/mvp/session/env/install.txt \
    mvp/results/20261031-com260-rc3/mvp/session/env/restore.txt
grep -h 'CONFIG_SEALED' mvp/results/20261031-com260-rc3/*/handoff-excerpt.log | sort | uniq -c
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The scope matches the accepted M6 plan at `b2c62d54` with Q1 to
      Q11 at their defaults and Plan revision S3-B.
- [ ] The claim's text and required limit are unchanged, and the ledger's
      new rows and non-claims say no more than the records support.
- [ ] The trust assumptions are acceptable: the widened accepted R1
      structures checked by host tests, not proved; the firmware and
      U-Boot by their banners and SBI identity; the `k3ctl` client and
      dongle outside the lock; the operator's picocom log as the serial
      witness; your own statements about the board and `bootcmd`.
- [ ] The negative paths are covered: the 29 configuration defects, the
      image checker's core and seam mutations, the capture checker's 317
      mutations, the five board negatives as declared.
- [ ] The thirteen departures are acceptable as recorded, the model
      deferral among them.
- [ ] Successor work stays excluded: release-path steps 2 to 7, any merge
      or push, any source or accepted-text change, any kexec use, any
      model generalization.
- [ ] Decision: accept exact commit `89ef04e9` as the M6 result and
      MVP 1.0 release candidate 3; request revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `89ef04e9354c08ebadbaeb88d553c5081a00b84d` and the date. The acceptance record names that SHA;
  the plan's status record and the status documents are updated to
  match, and the roadmap's "MVP core profile" debt row closes. That is
  the release path's step 1 for the latest candidate; steps 2 to 7, any
  merge of `beryllium/mvp-m6` into the development branch, and any push
  each need their own instruction.
- **Request revisions:** a new commit and a new packet follow;
  `89ef04e9` is not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commit `89ef04e9354c08ebadbaeb88d553c5081a00b84d`
(`RC3`, over the candidate tree `X3` `ebc49a88`) is responsible-human
accepted as the M6 result and MVP 1.0 release candidate 3 as of
2026-10-31 (instruction `accept 89ef04e9, proceed`; the
[decision record](#decision-record)). The seven gates pass at `X3` and
twenty of twenty board runs passed at its images; `./mvp/mvp check`
passes at `RC3`. Nothing is pushed, merged, tagged, published, or
released; no successor is authorized.
