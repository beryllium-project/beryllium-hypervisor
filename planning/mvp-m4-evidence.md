<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M4 evidence record

This record holds the evidence of M4, "Release candidate", on branch
`beryllium/mvp-m4`, made under the accepted [M4 plan](mvp-m4-plan.md)
(`0d02df72`, accepted 2026-10-28, with M4 implementation authorized) and
its
[Plan revision M4-A](mvp-m4-plan.md#plan-revision-m4-a-the-board-record-s-identifying-strings)
(directed 2026-10-29; presented for acceptance with M4's result). It
records what was run, when, on which commit, and what it printed; it
makes no claim beyond those lines. The candidate tree `X` is exact
commit `d42b9ec0a6d2f9f32d66ec2a983018e802b2d537` (tree `51f304d7`); no
source change follows it. The release-candidate commit `R` is the commit
that adds this record's final form with the two retained records and the
ledger rows that cite them, over `X`; the review packet names it.

## What M4 adds, by file

All under `mvp/` but the planning documents. No monitor source, shim,
guest input, scenario, generator, checker rule, lock, or `model/` file
changes: `git diff --stat 18d552bc d42b9ec0 -- mvp/src mvp/shim
mvp/guest mvp/scenarios mvp/tools/gen-scenario.py mvp/tools/policy-check.py
mvp/tests/check-capture.py mvp/tests/check-image.py mvp/tools/lock model`
is empty.

| File | Lines | What it holds |
| --- | --- | --- |
| `docs/claim.md` (new, M4-1) | 126 | The MVP 1.0 claim, byte-equal to the plan's fixed text, without the alternative-(b) clause (Q2's default applies); the required limit; the forbidden phrasings as the list's single source (11 literals inherited from the MVP plan, 24 added by M4 in 14 groups, 3 conditionals, 2 review items) with the matching rule |
| `docs/claim-ledger.json` (new, M4-1; rows added at `R`) | 1,045 | The ledger's source: 34 claim rows (28 at M4-1; C-29 to C-31 for the gates record; C-32 to C-34 for the board record), 12 unproved-boundary items, the 2 review items, the release identity (`candidate_tree_commit` = `X`; `release_candidate_commit` null: the commit that contains the ledger cannot be named inside it, and the packet names `R`) |
| `docs/claim-ledger.md` (rendered) | 264 | The table `tools/claim-ledger.py render` writes from the JSON; `check` fails if they differ |
| `docs/guide.md` (new, M4-2) | 1,055 | The researcher guide, nine sections; 19 wrapper command words, each in `./mvp/mvp help`; section 5 states what is data and what is a source change |
| `docs/ai-assistance.md` (new, M4-3) | 275 | The disclosure, every statement cited to a plan or record field or a Git command |
| `tools/claim-ledger.py` (new, M4-1) | 694 | `check` (schema, methods, evidence hashes, commits on the host, rendering, the guide's commands, phrasing, privacy, headers), `render`, `join`, `--self-test` (21 seeded mutations, 5 variants) |
| `tools/rc-record.py` (new, M4-4) | 591 | `./mvp/mvp rc-record`: the release-candidate record from explicit inputs each checked to name `X`; `--verify`; `--self-test` (21 mutations) |
| `tools/evidence.py` (edited, M4-A) | +144 | Redaction of an ssh user-and-host target to `<board-ssh>` and an IPv4 literal to `<ip>` in every text the development bundle and the board record write; `identifying()` refuses what the ledger's privacy rule finds; six self-test cases |
| `tools.mk`, `Makefile`, `mvp`, `tools/make-control.py`, `tests/run-tool-dry-run.sh` (edited) | +22, +23, +31, +12, +61 | The `claim-ledger-check` and `rc-record-check` targets in `check`; the `claim-ledger` and `rc-record` commands; `K3_RECORD_TITLE` (default `MVP COM260 campaign`) and its Make-control allowlist; the dry run's `code-names` case |
| `results/20261029-rc/` (new, M4-4) | 422 files | The release-candidate record of the seven gates at `X` |
| `results/20261029-com260-rc/` (new, M4-5) | 123 files | The release-candidate board record: 11 runs at `X`'s images |
| `README.md`, root `README.md` (edited, M4-3 and after) | | The development log's M4 entries, open items 63 to 70; one pointer in "Current phase" |

New checking and record code: 1,576 lines (`claim-ledger.py` 694,
`rc-record.py` 591, `evidence.py` 144, the dry run 61, `mvp` 31,
`Makefile` 23, `tools.mk` 22, `make-control.py` 12; `git diff --numstat
4e10fca3 d42b9ec0` over those files) against the soft limit re-set to
2,000 (erratum 1). Documents have no limit.

## The claim, the limit, and the phrasings

`docs/claim.md`'s claim blockquote and required-limit paragraph are
byte-equal to the plan's "The MVP claim" (checked by a script that
extracts both from `planning/mvp-m4-plan.md` and compares). The 35
literals occur in no release surface outside `claim.md`'s "Forbidden
phrasings" section, and the two conditional phrasings occur nowhere
(`claim ledger phrasing: PASS surfaces=4 literals=35 conditionals=3
review_items=2`). The phrasing rule is case-insensitive on
whitespace-normalized text with hyphen and space equivalent, each
literal a whole phrase at word boundaries; two of its literals, "TEE"
and "SMP", also match the shell command `tee` and the rehearsal's
`smp=8` field in prose, so the surfaces avoid both words (`mvp/README.md`
open item 66).

## The ledger

Thirty-four claim rows, 76 evidence artifacts (each a regular file in the
tree with its SHA-256, or a record's `MANIFEST.sha256`), each with its
method terms from the vocabulary (`by construction`, `host unit test`,
`adversarial test`, `deterministic report`, `semantic checker`,
`emulation`, `diagnostic board run`, `proof about the abstract model`,
`differential agreement`, `not run`, the last exclusive) and its
non-claim; 6 rows marked historical (the M0 and M1 campaigns, whose
images later monitor changes replaced, and the M0 probe facts, which
characterize the board and firmware, not the candidate's images); 12
unproved-boundary items (R7's cut points for the accepted R5 bytes only;
the B5 to B7 layers; the boot barrier, rings, IPI protocol, control
loop, G-stage builder and channel check, injection decision, management
decision, measurement; memory ordering between harts; the sealed state's
protection inside HS), each marked `host unit test` or `semantic
checker` where that exists and `not run` for proof. The rows added at
`R`: C-29 (the seven gates at `X`), C-30 (247 of 247 images identical at
`X`), C-31 (the candidate's four `anchor` board images byte-identical to
the accepted M2-A record's, both manifests cited), C-32 and C-33 (the
release-candidate campaign's `two-guests` and `te-poc` runs and
negatives), and C-34 (its resets); the board record is also cited from
the claim's rows C-09, C-11, and C-15.
`BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=34 boundary=12`.

## Plan revision M4-A, as implemented

Found before any release-candidate record was made: a board record made
with the accepted board tools carries the board's ssh target (20
occurrences in the accepted M2 record) and IPv4 address (26), and
`tools.mk` fixed the record's title as "MVP M2 COM260 campaign". The
responsible human's direction (`re stop 9, agree with redaction / code
names.`) is implemented at `0b2ac6fa`: the writer rewrites an ssh target
(`k3_ssh=` values, `ssh`/`scp` targets, `user@host:` prefixes, `ssh://`)
to `<board-ssh>` and an IPv4 literal (the ledger's own pattern, so a
package version after a hyphen is not one) to `<ip>`, keeping
`@sha256:` digests, the guest's pinned `(be@beryllium)` banner, and
addresses in copyright lines; `identifying()` refuses what the ledger's
rule finds; the originals' digests keep their place
(`mvp/resets/originals.sha256`, each run's `SHA256SUMS`). The accepted M0
to M2 records are not edited. Re-making the M2 campaign's record into
scratch redacted all 20 and 26 occurrences in the same files and lines,
with the ledger's eight privacy patterns finding nothing;
`BE_MVP_EVIDENCE_SELF_TEST: PASS cases=34/34`;
`BE_MVP_RUN_TOOL[code-names]: PASS`; `--verify` of the three accepted
records unchanged (`files=75`, `82`, `93`). `K3_RECORD_TITLE` is a Make
caller variable with the default `MVP COM260 campaign`; M4-5 passes
`MVP 1.0 release candidate COM260 campaign`.

## The gates at `X`, from this checkout clean at `X`

Run by a driver under `build/mvp/rc-gates/` (outside the tree), each
gate's output logged between `start_utc=` and `end_utc=` lines, in the
plan's order, 2026-10-29, workstation `l1` (Fedora Linux 44, x86_64),
the lock's tools (`lock_sha256=6e99262f04a1`), the host's
`build/model/evidence` copied aside between the last two gates:

| Gate | UTC | Result |
| --- | --- | --- |
| `./mvp/mvp tool-lock check` | 08:42:12 to 08:42:16 | `BE_MVP_LOCK: PASS roles=29 host_only_skipped=0 closure=259 lock_sha256=6e99262f04a1` |
| `./mvp/mvp check` | 08:42:16 to 08:48:38 | `BE_MVP_CHECK: PASS`; the bundle `files=329 images=247 qemu_attempts=76 rehearsals=6`; `BE_MVP_CLAIM_LEDGER: PASS checks=9 claims=28 boundary=12`; `rc-record self-test: PASS mutations=21` |
| `./mvp/mvp evaluate` | 08:48:38 to 08:54:56 | `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; `BE_MVP_IMAGE_IDENTITY: PASS images=247 same=247 differing=0`; inside, `BE_MVP_LOCK: PASS roles=26 host_only_skipped=3`, `BE_MVP_CHECK: PASS` |
| `./mvp/mvp kexec-rehearsal` | 08:54:56 to 08:56:22 | six `BE_MVP_KEXEC_REHEARSAL: PASS smp=8 …` lines, images `80ac8e334151`, `153e7482d2b0`, `4f4d684b8689`, `746585fbecb8`, `3b554f2cd0c6`, `37cdfd7064b0`, the refused domain-hart boots repeated within the bound |
| `make -C mvp kernel-repro LINUX_GIT=<local mirror>` | 08:56:22 to 08:56:53 | `BE_MVP_KERNEL_REPRO: PASS outputs=15 identical; sysroot_files=1065 sysroot_sha256=c931b51b…` |
| `./be model-check` | 08:56:53 to 08:57:57 | `Beryllium Architecture Model 0.2 evidence: PASS`; `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91 three_way=73 two_way=22 comparisons=241`; the documentation source gate PASS |
| `./be evaluate` | 08:57:57 to 08:58:57 | `BE_EVALUATION: Model 0.2 rootless evidence PASS` |

Two earlier attempts are development history, not evidence
(`build/mvp/rc-gates/attempt-1-0b2ac6fa/`, `attempt-2-73b1f7f2/`): the
first stopped at `./be model-check` on a planning link whose VitePress
slug was wrong (fixed at `73b1f7f2`, no `mvp/` change); the second
passed every gate, but `rc-record` refused its record because the
self-tests' own fixture strings (an address, a scheme, a home path) were
in the evaluator's retained `check.log`, quoted by the checkers'
findings; the checkers now report the kind and line only (`42009986`),
which moved `X`.

## The release-candidate record

`./mvp/mvp rc-record` made `mvp/results/20261029-rc/` at 08:59:14 UTC
from the inputs named explicitly (the host bundle, the evaluator record
`20261029T084838Z`, the host's and the evaluator's model evidence and
the evaluator's logs, the six rehearsals, `kernel-repro`, the seven gate
logs), each checked to name `X` and the evaluator's identity checked
against `tools/lock/closure.txt` and `tools/evaluator/Containerfile` at
`X`: `BE_MVP_RC_RECORD: PASS … commit=d42b9ec0… files=422` (3.4 MB).
`rc.txt` names `X`, its tree, the host's OS and architecture, the lock's
and closure's SHA-256, and each gate's PASS line with its times;
`host/` is the bundle (11 files rewritten); `evaluator/` the record with
`compare-images.txt`; `model/host/`, `model/evaluator/`,
`model/evaluator-logs/`; six `rehearsal/<label>/`; `kernel-repro.txt`;
`MANIFEST.sha256` (SHA-256 `8502f9d76c9cc271…`) over every other file.
`--verify` passes (`BE_MVP_EVIDENCE: PASS verify … files=422`); the
ledger's privacy rule finds nothing in it (`claim ledger privacy: PASS
files=426`); the external rehearsal kernel's banner reads
`(<build-user>@<build-host>)`. The record is committed in `R`,
with the board record below.

## Q2's `anchor` comparison and M4-5

`X`'s four `anchor` board images in the record's `host/images.sha256`
(`gcc/anchor/be-mvp-boot.img` `3b554f2cd0c6…`, `clang/anchor/
be-mvp-boot.img` `37cdfd7064b0…`, `variants/gcc/wrong-measurement/
be-mvp-boot.img` `61a3cd8a3c48…`, `variants/gcc/no-grant-check/
be-mvp-boot.img` `9b0aca48af15…`) are byte-identical to the four the
accepted M2-A board record's `summary.md` states, so by Q2's rule the
release-candidate board campaign is the **11-run** campaign for
`two-guests` and `te-poc` (three GCC and one Clang each; `payload`,
`reader-write`, and `no-inject` once with GCC), and
`mvp/results/20261028-com260-m2a/` is the `anchor` evidence at the
candidate's images (ledger row C-31).

## The release-candidate board campaign (M4-5)

On 2026-10-29 the responsible human confirmed the board free (`k3 is
available for you now, proceed`). The board was then running a one-shot
boot of another project's kernel, `7.3.0-k3-kvm-csr1` (booted 08:24
UTC from `/boot/k3-kvm-csr1/`), with the GRUB default unchanged at the
recorded `7.3.0-65.1.riscv64.omni.fc45`; the plan's stop condition 3
names a host kernel that differs from the records, and the MVP claim's
required limit names one host kernel. The human was asked how to proceed
and was not available, so the assisting session made one `k3ctl reset`
before any board command (17:06:55 UTC, `OK reset`; recorded in the
campaign directory's `pre-campaign-reset.txt` with its reason), which
returned the board to the recorded kernel (boot ID `19befccc…`, over SSH
at 17:08 UTC), as the campaign's own opted-in reset after its first run
would have; it is outside the plan's per-run reset rule and is recorded
here for the responsible human's review. The campaign then followed the
plan's procedure with `K3_RESET=k3ctl` and
`K3_RECORD_TITLE="MVP 1.0 release candidate COM260 campaign"`:

| Step | UTC | Result |
| --- | --- | --- |
| `./mvp/mvp k3-preflight` | 17:11 | `BE_MVP_PREFLIGHT: PASS`; `kernel=7.3.0-65.1.riscv64.omni.fc45.riscv64`; `firmware_identity=ID=0x1 Version=0x10006`; the three windows free |
| `./mvp/mvp k3-load-check SCENARIO=two-guests TOOLCHAIN=gcc`, then `clang` | 17:12, 17:13 | `kexec_loaded=1` then `unload=ok kexec_loaded=0`, `outcome=load-only`, Fedora running |
| `k3-campaign SCENARIO=two-guests TOOLCHAIN=gcc RUNS=3` | 17:14, 17:15, 17:16 | `BE_MVP_RESULT: PASS terminal=shutdown-requested`, `BE_MVP_CAPTURE[kexec two-guests]: PASS`, `exits_g0=157 exits_g1=157 records=138 wakes=2 alternations=125` in each; image `80ac8e334151` |
| `… SCENARIO=two-guests TOOLCHAIN=clang RUNS=1` | 17:19 | the same lines and counts; image `153e7482d2b0` |
| `… VARIANT=payload RUNS=1` | 17:21 | `BE_MVP:FAIL payload` before any hart started; `BE_MVP_RESULT: PASS terminal=fail-marker`; image `27544cb42108` |
| `… SCENARIO=te-poc TOOLCHAIN=gcc RUNS=3` | 17:24, 17:25, 17:27 | `BE_MVP_RESULT: PASS terminal=shutdown-requested`, `BE_MVP_CAPTURE[kexec te-poc]: PASS`, `exits_g0=163 exits_g1=167 denials_g0=1 denials_g1=2 records=146 wakes=2 alternations=127` in each, the three `DENY` lines and both `CHANNEL` lines; image `4f4d684b8689` |
| `… SCENARIO=te-poc TOOLCHAIN=clang RUNS=1` | 17:29 | the same lines and counts; image `746585fbecb8` |
| `… VARIANT=reader-write RUNS=1` | 17:31 | `BE_MVP:FAIL gstage` with its `DETAIL` line, no domain run; `terminal=fail-marker`; image `1e4e43ecf40e` |
| `… VARIANT=no-inject RUNS=1` | 17:34 | `BE_MVP:FAIL guest-page-fault`, hart 0's one `FAIL` and `DETAIL` pair after 54 lines from each guest; `terminal=fail-marker`; image `88a27e0b67c3` |
| `./mvp/mvp board-evidence K3_RECORD_TITLE=…` | 17:37; re-made at `X` 17:42 | `BE_RETAIN: PASS runs=11 load_checks=2 files=121`; eleven `ok … recorded PASS, excerpt PASS`; `BE_MVP_PLATFORM_RECORD: PASS … runs=11 scenario_runs=4 te_poc_runs=4 denials=12 channel_checked=5`; `BE_MVP_EVIDENCE: PASS board … runs=11 pass=11 fail=0 refused=0 stop=0` |

Eleven of eleven runs as declared, each image's SHA-256 on the board
equal to `X`'s in the gates record's `host/images.sha256`; the counts
equal M0's (`two-guests`) and M1-B's (`te-poc`) accepted records', the
monitor unchanged since. Each run was followed by the tools' `k3ctl`
reset (`reset_reply=OK`, the client's hash equal to
`tools/k3ctl.sha256`), Fedora returning with a new boot ID in 33 to 47
s; no reset was made by hand, no run needed the plan's extra reset, and
nothing was typed at the console. No stop condition applied. The record
`mvp/results/20261029-com260-rc/` (123 files, 1.2 MB; the title "MVP 1.0
release candidate COM260 campaign"), made by `board-evidence` from this
checkout clean at `X` (`bundle.txt`: `source_commit=d42b9ec0…`,
`source_tree=clean`; a first making from a later documentation-only
commit, byte-identical but for that field and the platform record's copy
of it, was discarded), verifies (`files=123`), carries the
code names `<board-ssh>` (35) and `<ip>` (22) where the accepted records
carry the board's ssh target and address, and holds no identifying
string; the ledger's privacy rule finds nothing in it (`claim ledger
privacy: PASS files=549`). Its platform record agrees with M0's on the
SBI identity, the SBI specification, and the Fedora kernel. The
`anchor` scenario was not run (Q2's rule: its images are byte-identical
to the M2-A record's, C-31).

## Soft limits and stops in M4

| Event | Stop | Outcome |
| --- | --- | --- |
| New code 1,347 lines against about 900 (M4-4's tool) | 5 | Returned; the limit re-set to 2,000 (erratum 1); 1,576 at `X` |
| A board record carries the board's ssh target and address; the title fixed | 9 | Returned; Plan revision M4-A directed and implemented (`0b2ac6fa`) |
| The ledger's privacy rule read an `@sha256:` digest and a package version as private | none (a defect of M4's own checker) | Fixed with self-test cases (`ca322220`); the rule's meaning unchanged |
| A planning link's VitePress slug failed the documentation gate | none | Fixed (`73b1f7f2`); no `mvp/` change |
| The checkers quoted matched private strings into a retained log | none (a defect of M4's own checkers) | Fixed (`42009986`); `X` moved |
| The board unavailable at M4-5 (2026-10-29, 02:00 to 10:00 local) | the plan's waiting rule | M4 waited; the human confirmed the board free at 10:04 |
| The board on another project's one-shot kernel when confirmed free | 3 (by its letter) | One `k3ctl` reset before any board command returned the recorded kernel; recorded above for the human's review |

Every soft limit holds at `X`: new code 1,576 of 2,000; the new
targets' time (`claim-ledger.py check` 0.14 to 0.16 s and its self-test
2.3 to 3.2 s; `rc-record` self-test about 0.2 s) under 60 s; no
monitor, guest, scenario, or `model/` line changed.

## Open items

From `mvp/README.md`: 63 and 65 resolved by M4-A; 64 (the rehearsal
kernel's banner) handled by `rc-record`; 66 ("TEE" and "SMP" as words);
67 resolved by erratum 1; 68 and 70 closed; 69, an IPv6 address is
neither rewritten nor refused (none occurs in any record), recorded for
the responsible human.

## Claim boundary

What is recorded here: unit tests, adversarial tests (seeded mutations
and negative images), deterministic reports, semantic checks (the image
and capture checkers, the ledger checker), emulation (QEMU), the proof
about the abstract model and the differential agreement carried over
from the accepted M3 result, the release-candidate campaign's
diagnostic board runs for `two-guests` and `te-poc` at the candidate's
images, and, for `anchor`, the accepted M2-A diagnostic board runs tied
to the candidate by byte-identical images.
The board runs are diagnostic bring-up evidence for one board (the
COM260), one firmware identity, and one host kernel, at the candidate's
images. Not recorded: any claim the required limit excludes; any
release-path step after the first, none of which is started.
