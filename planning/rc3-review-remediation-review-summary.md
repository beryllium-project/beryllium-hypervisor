<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Debt sweep 3 (the RC3 snapshot reviews): review packet

This packet supports the responsible human's decision on exact commit
`3b7ab0e3e43bdad48772c0ae5eb8d831f218c29f`, the candidate of debt sweep 3,
which remediates the twelve verified root causes (rows A to L) that two
read-only Rhyolite reviews of the public RC3 review snapshot found. It
recorded the decision below after it was given.

## Decision record

The responsible human accepted exact commit
`3b7ab0e3e43bdad48772c0ae5eb8d831f218c29f` (parent `9c908d12`) as debt
sweep 3 on 2026-11-01 (2026-11-01 in the human's time zone, 07:25). The
instruction, given in reply to this packet's request to accept, revise,
or defer that exact commit, was `accept 3b7ab0e3, fast fwd, push, use
your best judgement`. The abbreviation was checked to resolve uniquely to
that commit (`git rev-parse --disambiguate=3b7ab0e3`).

- **Scope:** acceptance covers exactly that commit and the claim boundary
  of section 3, the seven departures of section 5 included (the interior
  dot in a variant's name; the ownership and parent-chain rule in place
  of `mktemp -d`; the lock that did not move, with the measured 38 of
  259 closure builds no longer served and 25 of those absent from koji's
  signed paths; the kernel's GPL-2.0 text; the B-series READMEs left as
  accepted records; the two-commit ledger pin; the gate environment).
  Sections 1 to 9 are the packet as presented, apart from the status
  rows of section 1 and the closing lines of section 9, which now show
  the outcome. The twelve rows A to L of the consolidated reviews are
  closed by this acceptance; `mvp/README.md` open items 94 to 98 stay
  open, each the human's.
- **The same instruction directs** the fast-forward of the development
  branch `beryllium/single-hart-runtime-r0` from `8b7559d2` to the commit
  recording this decision and the push of that branch and of
  `beryllium/rc3-review-remediation` to the private `origin`. `use your
  best judgement` was read as covering the acceptance record's
  bookkeeping and the refresh of the human's local clone of the public
  review snapshot from the accepted content (`mvp/tools/snapshot.sh
  update`, the gates run in it, its record), which prepares the human's
  own push of the public `main` without making it: the publication of the
  refreshed snapshot stays the human's act, as before.
- **What it is not:** no release-path step (steps 2 to 7 are not
  started); no tag or publication; no board command and no kexec; no
  change to the claim statement, any accepted plan, or any accepted
  R-series byte beyond the B0/B6/B7 tooling the human's `harden_and_gate`
  authorized; no re-acceptance of the B-series results; nothing of tier
  2, which waits for the Claude CLI and Codex CLI reviews.
- **Correction to the packet as presented:** the packet, `mvp/README.md`
  open item 98, and the remediation plan described tier 2 as waiting on
  "the Claude CLI and Codex CLI reviews" as further reviews of the
  snapshot's code. The two reviews the human was waiting for, which
  arrived on 2026-10-31 and 2026-11-01, are independent design reviews
  of Plan revision S3-C under the S3-C packet's section 8 brief (one by a
  Codex CLI session, `planning/mvp-plan-s3c-independent-design-review.md`,
  untracked in the main checkout; one by a Claude Code session, outside
  the repository), to be compared with this session's own S3-C review:
  they review a plan, not the snapshot. Tier 2 therefore has no pending
  input; the register closes at rows A to L, and a later review of the
  snapshot's code would open a new sweep. Item 98 is corrected and
  closed in the acceptance record; the S3-C reviews are processed under
  the human's direction of 2026-11-01 (`also now process the claude cli
  and codex reviews and iterate as appropriate`) on the S3-C plan branch,
  not here.
- **Evidence terms:** the gates of section 6 are host unit tests,
  adversarial tests, deterministic reports, semantic checkers, and
  emulation, at `3b7ab0e3` from a clean tree; nothing here is hardware
  validation or formal verification, and the evaluator's PASS used the
  development host's verified RPM cache.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `3b7ab0e3e43bdad48772c0ae5eb8d831f218c29f`, parent `9c908d120d479522ca342fc479a987e8063ec3a5`; the sweep is the sixteen commits `e728b27e` to `3b7ab0e3` on local branch `beryllium/rc3-review-remediation` from the development tip `8b7559d2cc85640172a0f731b86d6ef0eecee2a6` (`beryllium/single-hart-runtime-r0`, local; `origin`'s is at `30cab198`, six commits behind, as `planning/HANDOFF.md` records) |
| Current status | Implemented; every planned gate passed at `3b7ab0e3` from a clean tree (section 6); **responsible-human accepted as of 2026-11-01** (the decision record above) |
| Decision requested | None outstanding on this commit; the decision was `accept 3b7ab0e3, fast fwd, push, use your best judgement` |
| Successor status | No tier 2 input is pending (the two awaited reviews are S3-C design reviews, not snapshot reviews: the decision record's correction); a later review of the snapshot's code would open a new sweep; no milestone, plan, or release-path step is started or authorized by this sweep or its acceptance |
| Publication status | The same instruction directs the fast-forward of the development branch to the commit recording this decision and the push of it and the sweep's branch to the private `origin`; the human's local clone of the public review snapshot is refreshed from the accepted content, and its push to the public `main` (at `1ae5fd8c` as this is written) stays the human's act |

The action this section asked of the human, the decision on `3b7ab0e3`,
is taken; what follows it is in the decision record above and in
section 9.

### What the sweep is, in one paragraph

The responsible human consolidated two Rhyolite read-only reviews of the
public RC3 review snapshot (`1ae5fd8c`, made from `3fe427b7`) into three
documents outside this repository (`rhyolite-output/repo-review/be-rc3/`:
`README.md`, `COMPARISON-REPORT.md`, `AGENT-FEEDBACK.md`) with twelve
verified root causes, rows A to L, none in the monitor's guest-facing
code (`mvp/src/`), all in the privileged board tooling, the release
surfaces, licensing, and reproducibility. Every row was re-verified at
`8b7559d2` before work began; all twelve were present. The human answered
five questions on 2026-11-01 (`harden_and_gate`, `gate_variable`,
`exclude_from_snapshot`, `defer_to_migration`, `tier1_now`); the sweep
implements each row within those answers, one commit per row (two where a
ledger pin follows), each with a negative test built to misbehave; records
the standing rules behind the defects; and changes no monitor behaviour,
claim statement, accepted plan text, or accepted R-series byte. It ran no
board command and no kexec (the standing rule of 2026-10-29).

## 2. Deliverables

| Row | Commit | Paths | What it does | Boundary | Review question |
| --- | --- | --- | --- | --- | --- |
| A, D | `e728b27e` | `bringup/k3-b{0,6,7}/scripts/k3-run.sh`, `k3-campaign.sh`; `bringup/k3-b{0,1,2}/Makefile`, `k3-b{6,7}/tools.mk`; `tests/test-kexec-load.py` (B0, B6, B7), `tests/fake-board.py` and `tests/run-tool-dry-run.sh` (B6, B7) | The retained kexec launchers run the remote loader as `python3 -I` (no script directory on `sys.path`, no `PYTHON*` environment), use a fixed remote image name, build every remote command through one `remote_command()` (`printf '%q'` per word), and refuse before any board contact unless `BE_KEXEC_APPROVED` is set, recording its value; every kexec-using make target has `kexec-approval` as a prerequisite | **Accepted B-series bytes change** (B0 `bb8fd210`, B6 `e20c55df`, B7 `7b6b846b` tooling), under the human's `harden_and_gate`; the B-series results and records are not re-run or re-accepted | Is the gate's wording and placement what you meant by `gate_variable`, and is hardening accepted tooling in place (as the accepted-tool fixes of 2026-10-07 were) what you authorized? |
| E | `ab1892a9` | `mvp/tools/k3-console.sh` (`diagnostic()`), `mvp/tests/fake-uboot.py`, `mvp/tests/run-tool-dry-run.sh` | The console tool's diagnostic filter is an anchored whole-line allowlist in `template()`'s shape (alphabet, exact strings, anchored forms for the read-only commands the characterization typed); the first-word test, blacklist, and exemptions are gone; `K3_DIAGNOSTICS=human-authorized` and the 120-byte bound stay | Lines typed at the board's U-Boot prompt in a human-authorized diagnostic session | Does the accepted list hold every read-only form you want available, and nothing you do not? |
| G | `3c143857` | `mvp/tools/snapshot.sh` | `update` verifies the commit and that the destination is a snapshot before it removes anything (`verify_source()` in `populate` and before the deletion loop) | The snapshot tool runs on the host against a local clone | None beyond reading the ordering |
| H | `306bf666` | `mvp/docs/claim-ledger.json` (`release`), `claim-ledger.md`, `claim.md`, `guide.md`, `ai-assistance.md`, `mvp/tools/claim-ledger.py`, `mvp/tools/snapshot-readme.md`, `mvp/tools/snapshot.sh` | The ledger names release candidate 3 at `89ef04e9`; each surface's self-description carries that name and short SHA; the kexec-launched records (M0 to M2, RC1) and the boots from system reset (RC2, RC3) are told apart; the snapshot README takes the name, commit, and commit count from the ledger and `git rev-list`; `claim-ledger check` gains "release surfaces" | The release surfaces are the claim's public statement; the claim statement's text (the blockquote) and the required limit are unchanged | Is the ledger's `release` object the right single source of truth, and are the reworded "which records were kexec launches" sentences accurate? |
| B | `92d14404` | `mvp/tools/k3-stage.sh`, `mvp/mvp`, `mvp/tests/fake-board.py`, `mvp/tests/run-tool-dry-run.sh`, `mvp/docs/guide.md` | Staging binds to the partition's UUID (`K3_PARTITION_UUID` or the newest preflight record's), cross-checks label and type, mounts with `nosymfollow` where the kernel accepts it (probed, recorded), refuses any non-regular entry on the partition before writing, copies with `--remove-destination`, records the UUID's SHA-256 and the mount options | Writes to the Beryllium partition on the board's NVMe over SSH as root | Is the UUID (from the preflight record, or given) the identity you want staging bound to? |
| C | `7ec20021` | `mvp/tools/k3-make-partition.sh`, `mvp/tests/test-k3-make-partition.sh`, `mvp/tests/fake-partition-tools/` | Precondition 11 admits only a backup directory the caller owns, writable by neither group nor others, not a symbolic link, with every directory above it root's or the caller's and not group- or other-writable unless sticky (sshd's StrictModes rule), empty, off the source partition; every record is created exclusively (`excl`, a subshell with noclobber; `dd conv=excl`); the comments say what noclobber does not refuse (a link to a device or a fifo) and why the ownership rule is the control | The human-run, root, one-time partition tool; the partition already exists on the board | The plan said `mktemp -d` inside `--backup-dir`; the sweep chose the ownership and parent-chain rule instead, which keeps the documented layout and closes the parent-swap case `mktemp` does not (section 5, departure 2). Acceptable? |
| F | `13c7456c`, pin `9e6cdc3e` | `mvp/tools/gen-scenario.py`, `mvp/docs/claim-ledger.json` (C-40), `claim-ledger.md` | Every variant name meets the scenario's grammar with an interior dot allowed, every probe name `probe-` and letters, none named like the scenario or another image; the writer requires every expect path to resolve inside `expect/`; the three self-tests gain the refusals; the generated outputs are unchanged | The generator runs at build time on scenario files in the tree | The plan's literal grammar `[a-z][a-z0-9-]{0,31}` would refuse M0's accepted variant `sbi-3.0`; the interior dot is the departure (section 5, departure 1). Acceptable? |
| I | `2deabaeb` | `mvp/docs/claim-ledger.json` (C-05), `claim-ledger.md` | C-05 states the boundary the code has: one install per domain hart at its entry after observing the published generation word (`BE_MVP:07`); the install function's two call sites; no `hgatp` write once every domain hart has installed (`BE_MVP:08` to `:10`); the evidence is unchanged; the accepted M0 plan's sentence is recorded as an erratum (open item 94) | A claim row's wording; no code | Does the restated boundary read as you understand the mechanism? |
| L | `5930a67c`, fix `6daeb1f4` | `LICENSES/GPL-2.0-only`, `COPYING`, `README.md`, `mvp/tools/snapshot-readme.md`, `mvp/tools/check-licenses.py`, `mvp/Makefile` | The GPL-2.0 text (the pinned guest kernel's `LICENSES/preferred/GPL-2.0`, byte for byte), a root `COPYING` saying which file is under which licence, a License section in the root README and the snapshot README, and a check in `make -C mvp lint` that every identifier a tracked file's header names has its text under `LICENSES/` and a line in `COPYING`, and no text is unused | Licensing statements; the one GPL-2.0-only file is the guest kernel module, never linked into the monitor | Is `COPYING`'s wording the statement you want to make? |
| K | `f7e58b04` | `mvp/tools/snapshot.sh`, `mvp/tools/snapshot-readme.md` | `tests/r8` joins the snapshot's exclusions; `same_blobs` handles an excluded directory below the top level; the self-test asserts the snapshot holds no ELF object; the README explains the four exclusions | The accepted R8 bytes (`1999ee70`) are unchanged in the source | None beyond confirming `exclude_from_snapshot` was the intent |
| J | `a3d295c8` | `mvp/tools/snapshot-readme.md` | "How to run the checks": `./mvp/mvp check` and `evaluate` are the snapshot's entry points; the root `Makefile` and `be` are the internal repository's and not usable there; `evaluate` needs a verified cache of the closure's exact RPMs where Fedora no longer serves a build | No root `Makefile` or `be` change (the R1 pin; MVP plan D3; your `defer_to_migration`); the lock refreshed from the host did not move | The measured availability (section 5, departure 3) makes the evaluator unbuildable from public sources without the cache; the two remedies are yours (open item 95) |
| Rules and record | `da9dc9a5` | `.github/copilot-instructions.md`, `mvp/README.md` | The "Privileged tooling standard" (six standing rules); the development-log entry for the sweep; open items 94 to 98 | Operating instructions and the development log | Are the six rules the ones you want standing? |
| Gate-found fixes | `6daeb1f4`, `9c908d12`, `3b7ab0e3` | `mvp/tools/check-licenses.py`, `COPYING`, `mvp/tools/snapshot.sh`, `mvp/README.md` | Three defects of the sweep's own tests that the clean-tree gate runs caught (section 5, findings 1 to 3) | Test tooling only | Read section 5 |

Inventory from Git: 45 files changed, 2,448 insertions, 222 deletions
(`git diff --stat 8b7559d2..3b7ab0e3`); of these, 591 insertions and 55
deletions are under `bringup/` (rows A and D). Untouched, by the same
diff: `mvp/src/`, `model/`, `include/`, `virt/`, `arch/`, `tests/r7/`,
`tests/r8/`, the root `Makefile`, `be`, `scripts/check-be.sh`, every
`planning/` document, and every retained record under `mvp/results/` and
`bringup/*/results/`.

## 3. Claim boundary

**What `3b7ab0e3` supports saying.** Each of rows A to L has a change that
removes the mechanism the review named and a test, in the existing gate,
that fails without it: the launcher's isolated interpreter and its gate
(host unit tests with a planted module; fake-board dry runs), the
diagnostic allowlist (74 lines, 35 accepted and 39 refused, in the fake
tmux), the snapshot tool's validate-before-delete (self-test), the release
surfaces' single source of truth (`claim-ledger check`, three
self-test mutations), staging by UUID with no non-regular entry (five
fake-board cases), the partition tool's exclusive writes into a directory
only the caller can write (seven self-test cases, two of them races;
removing either exclusive write fails its case), the variant-name grammar
and expect-path containment (self-test refusals in all three scenarios),
the licence texts and the licence check (ten self-test cases; `identifiers=2
files=857 texts=2`), the snapshot without `tests/r8` or any ELF object
(self-test), and the explicit entry-point wording. `./mvp/mvp check`,
`claim-ledger check`, `evaluate` (253 of 253 images identical to the
host's), the B0 host test, and the B6 and B7 tools checks pass at
`3b7ab0e3` from a clean tree (section 6).

**What stays trusted or assumed.** The board tooling is still privileged
host tooling run by the human (root on the board over SSH; U-Boot typing
in the human's picocom session); the sweep narrows what it accepts and
how it writes, and tests that on fakes, not on the board. The partition
tool's ownership rule assumes the kernel's ordinary permission semantics
and that the caller does not plant entries against itself. The licence
check reads the first lines of tracked files; a licence named only in a
file's body is not a use. The snapshot's "no ELF object" assertion
covers the snapshot tree, not the source. The evaluator's PASS inside the
container used the development host's verified RPM cache
(`MVP_RPM_CACHE` semantics; section 5, departure 3).

**Evidence unavailable or `NOT RUN`.** No board run (none planned; the
COM260 is in the human's other project's use). No kexec anywhere (the
standing rule): the launchers' gate and isolation are host and fake-board
evidence only. The U-Boot rehearsal, `kernel-repro`, `make -C model …`,
and `./be model-check`/`evaluate` were not re-run: the sweep changes no
image, kernel input, or model file, and those gates' inputs are the same
bytes as at `8b7559d2`. The documentation source checks ran at the same
clean tree with the main checkout's `node_modules` linked in and removed
afterwards (section 6).

**What the commit does not implement.** No monitor change; no claim
statement change; no accepted plan edit (the M0 plan's `hgatp` sentence is
an erratum recorded beside it, open item 94); no root build change; no
deletion of the kexec tools or records; no snapshot refresh, push, merge,
tag, or publication; no closure move (open item 95); no edit to the
B-series READMEs' procedures (open item 96); nothing from the Claude CLI
or Codex CLI reviews (open item 98).

## 4. Security and correctness invariants

| Property | Contract | Implementation | Test or evidence |
| --- | --- | --- | --- |
| The retained launchers never import a module from the loader's remote directory, and never run kexec without the human's explicit approval | Launcher headers and `kexec-approval` targets | `python3 -I` at every call site; `remote_command()`; `BE_KEXEC_APPROVED` checked before any board contact, value recorded | `tests/test-kexec-load.py::launcher_runs_the_loader_isolated` (B0, B6, B7: planted `ctypes.py` marker absent under the launcher's form, present under the old); B6/B7 dry-run cases `kexec-unapproved`, `kexec-hostile-name`; the fake boards accept only the new form |
| A diagnostic line reaches the board only if the whole line is an allowed read-only form | `k3-console.sh` usage text, `diagnostic()` | Anchored alphabet, exact strings, and whole-line regexes; no first-word test | `run-tool-dry-run.sh` case `diagnostic`: 35 accepted, 39 refused (metacharacters, `run`, `mw`, `nvme write`, a third `crc32` address, 121 bytes, unauthorized, misauthorized), none typed |
| `snapshot.sh update` removes nothing until the commit and the destination are verified | `snapshot.sh` usage text | `verify_source()` before the deletion loop | Self-test: a bad commit and an update from inside a snapshot leave the destination byte-identical (ignored file included) |
| Every release surface names the ledger's current candidate and commit | `claim-ledger.py` docstring ("release surfaces") | `check_release` over whitespace-collapsed text | `claim-ledger check` (`candidate=3 commit=89ef04e9`); three self-test mutations fail exactly that check |
| Staging writes only to the partition it was given and only through regular files | `k3-stage.sh` header; `guide.md` | `blkid -U`, label and type cross-checks, `nosymfollow` probe, `find ! -type f` refusal, `cp --remove-destination`, UUID SHA-256 recorded | Fake-board cases `stage-symlink`, `stage-other-uuid`, `stage-no-uuid`, `stage-given-uuid`, `stage-old-kernel` |
| The partition tool's records are created exclusively in a directory only the caller can write | `k3-make-partition.sh` usage text, `backup_dir_problem`, `excl` | Ownership, mode, symlink, parent-chain (sticky allowed above), emptiness, and off-source checks; `excl` (noclobber in a subshell); `dd conv=excl` | Self-test cases `refuse-backup-planted-link`, `-group-writable`, `-symlink`, `-parent-writable`, `accept-backup-under-sticky-parent`, `stop-backup-link-planted-gpt-backup.before.bin`, `stop-backup-link-planted-blkid.before.txt`; mutation check: removing either exclusive write fails its race case |
| A variant or probe name is one path component under `expect/` and never the scenario's or another image's | `gen-scenario.py` (`SCENARIO_NAME`, `VARIANT_NAME`, `PROBE_NAME`) | `check()` grammar and uniqueness; `path.resolve().parent == expect_dir` before writing | Self-tests: `../x`, `/tmp/x`, `.x`, the scenario's name, `probe-../x`, a variant named like a probe refused (two-guests 46, te-poc 45, anchor 57 cases) |
| Every licence in use has its text and is named in `COPYING`; no text is unused | `check-licenses.py` docstring; `COPYING` | Anchored header line, SPDX-identifier tokens, `LICENSES/<id>` in the kernel's form, `COPYING` mention | `check-licenses.py --self-test` (10 cases) and `check` in `make -C mvp lint` (`identifiers=2 files=857 texts=2`) |
| The review snapshot holds no executable object and no excluded path | `snapshot.sh` (`EXCLUDED`, `no_executables`) | `tests/r8` excluded; `same_blobs` per excluded path or anything under it | Self-test (30 cases; `no_executables` names `tests/r8/run-make.sh` when pointed at the source's `tests/`) |

## 5. Review history and resolved findings

**Findings the clean-tree gate runs made against the sweep's own work
(closed).**

1. `check-licenses.py` (row L, `5930a67c`) read tracked files only, so it
   had not seen `COPYING` until that file was committed; `COPYING`'s
   second line named the tag in a sentence, which the unanchored pattern
   took as a header and whose words it took as identifiers
   (`identifiers=7`, five findings; the gate run at `da9dc9a5` failed in
   `lint`). Fixed in `6daeb1f4`: a header line is the tag and an
   expression and nothing else but a comment opener and closer (Rocq's
   `(* *)` included, which the proofs use), every token must be an SPDX
   identifier or an operator, and `COPYING` names the identifiers without
   the tag; the self-test gained the COPYING-like file, a Rocq header, and
   the parser's refusal of a sentence.
2. The snapshot self-test's in-snapshot case (row G, `3c143857`) copied
   this very script into a scratch snapshot and committed it
   unconditionally; at a clean tree the copy equals HEAD's file and git
   has nothing to commit (the gate run at `6daeb1f4` failed there). Fixed
   in `9c908d12`: the copy is committed only when the index differs.
3. Inside the clean evaluator, which mounts a linked worktree without its
   gitdir, the snapshot self-test failed (`fatal: gitfile does not point
   to a valid repository`) where the ledger's commit check skips and says
   so (the gate run at `9c908d12` failed in `evaluate`). Fixed in
   `3b7ab0e3`: the self-test skips there, saying so; a repository that is
   present is never skipped. This condition had not arisen before because
   every earlier gate run was made in the main checkout, whose `.git` is a
   directory.

**A process signal, not a defect.** The first gate run at `9c908d12`
failed the dry run's `port-open-prior.stop` case with `BE_MVP_K3_CONSOLE:
MISSED the boot command runs: an unplanned boot`: the fake U-Boot's 0.8 s
autoboot window closed before the console tool's `s` landed, on a host
running other sessions. This is `mvp/README.md` open item 93 (recorded
2026-10-31), not a change of the sweep; the same case passed in the runs
before and after, and the gates were run one at a time.

**Departures from the approved plan (for your judgment).**

1. *Row F's grammar.* The plan applied the scenario's literal grammar
   `[a-z][a-z0-9-]{0,31}` to variant names; M0's accepted `two-guests`
   scenario has the variant `sbi-3.0`, so that grammar would have refused
   an accepted scenario or required renaming its image. `VARIANT_NAME`
   allows a dot between two characters (never leading, trailing, or
   doubled; at most 32 characters), which still excludes `.`, `..`,
   hidden names, and paths. The scenario's own grammar is unchanged.
2. *Row C's mechanism.* The plan named `mktemp -d` inside `--backup-dir`
   plus noclobber and `conv=excl`. A fresh 0700 directory inside a
   directory someone else can write still leaves the parent swap (the
   attacker renames the directory away and puts a link in its place), and
   it changes the documented layout the records and the human's procedure
   use. The sweep instead requires the given directory to be the caller's
   alone and every directory above it root's or the caller's and not
   group- or other-writable unless sticky (sshd's StrictModes rule), and
   keeps noclobber and `conv=excl` as the exclusive writes; the comments
   say that noclobber does not refuse a link to a device or a fifo, which
   is why the ownership rule is the control. The usage text tells the
   human how to make such a directory (`install -d -m 700 /root/be-backup`).
3. *Row J's refresh.* The plan expected the lock and closure refreshed
   from the host "so that the evaluator image builds from currently
   served RPMs". `./mvp/mvp tool-lock refresh` on this host changed
   nothing (`changed_keys=0 closure_added=0 closure_removed=0`): the
   closure is the host's installed set, and the host has not moved.
   Measured on 2026-11-01 against Fedora 44's `fedora` and `updates`
   repositories (`dnf repoquery --available` over the 259 NEVRAs) and
   koji's signed paths (one HEAD request each): 38 closure builds are no
   longer in the repositories and 25 of those are absent from koji's
   signed paths too (gcc `16.2.1-2`, libstdc++, util-linux `2.41.5-1`,
   qemu `10.2.2-1`, openssl-libs `3.5.9-1`, xz `5.8.2-2` among them), up
   from the nine the snapshot's record of 2026-10-31 named. The evaluator
   therefore cannot be built from public sources today without the
   development host's verified cache; the snapshot README now says so,
   and the remedies (publish the verified cache, 385 MB of Fedora-signed
   RPMs; or update the host and move the lock and closure to served
   builds, a toolchain move with the gates re-run and the image
   identities re-recorded) are yours (open item 95).
4. *Row L's text.* `LICENSES/GPL-2.0-only` is the Linux kernel's
   `LICENSES/preferred/GPL-2.0` at the pinned guest kernel `8d3ae592`
   (SHA-256 `8780e78a1a737e127f25a65f6d95269bffd36158dc261114de7859b490bfc5aa`),
   in the same form as the existing `LICENSES/GPL-3.0-only`; the plan
   said "the verbatim GPL-2.0 text" without naming a source.
5. *The B-series READMEs.* The accepted READMEs of B0, B6, and B7 still
   describe the kexec procedure without the gate (open item 96); the sweep
   edited their tools and tests under `harden_and_gate` and left the
   accepted records' prose alone.
6. *A ledger pin on a tool.* C-40 pins `gen-scenario.py` by SHA-256, so
   row F is two commits, the first of which (`13c7456c`) fails
   `claim-ledger check` until the second (`9e6cdc3e`) refreshes the pin,
   as debt sweep 1's C-10 did; open item 97 asks whether tools should be
   pinned by commit instead.
7. *The gate environment.* The gates ran from the linked worktree at the
   clean candidate, with the main checkout's external build inputs linked
   under its `build/` (`build/mvp/guest`, the pinned guest kernel and its
   inputs, which `guest-pin-check` verifies; `build/mvp/linux-src`, the
   Linux checkout the evaluator mounts; `build/k3-b0` to `k3-b7`,
   `build/model`, `build/mvp-evaluator` with its verified RPM cache;
   `build/docs`, `build/pathfinder`); everything under `build/mvp/` but
   `guest` and `linux-src` was built afresh by the gates. The first
   arrangement (every `build/` entry linked) failed `platform-record.py`'s
   path containment through a resolved symlink and was replaced; that
   failure was the environment's, not the tree's.

**Open questions for human judgment.** Departures 1 to 3 above; the
`COPYING` wording; whether the six standing rules in
`.github/copilot-instructions.md` are the ones you want; open items 94
to 98.

## 6. Validation and retained evidence

All at exact commit `3b7ab0e3` from a clean tree (`git status --porcelain`
empty), 2026-11-01 UTC, on the development workstation (Fedora Linux 44,
x86_64) with the lock's tools (`lock_sha256=2f1b732dcf24`), by a driver
under `build/mvp/sweep3-gates/` (outside the tree; each gate's output
logged between `start_utc=` and `end_utc=` lines), one gate at a time:

| Gate | UTC | Result |
| --- | --- | --- |
| `./mvp/mvp tool-lock check` | 09:43:07 to 09:43:11 | `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`; `BE_MVP_LOCK_SELF_TEST: PASS cases=50`; `BE_MVP_FETCH_SELF_TEST: PASS cases=39` |
| `./mvp/mvp check` | 09:43:11 to 09:48:50 | `BE_MVP_CHECK: PASS`; `BE_MVP_LICENSES: PASS identifiers=2 files=857 texts=2 source=git` (self-test 10 cases); `BE_MVP_QEMU: PASS runs=58 attempts=71 refused=13`; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=129 failed=0`; `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=317 rejected=317`; the three scenario self-tests `cases=46`, `45`, `57`; `k3-make-partition self-test: PASS (29 cases)`; `BE_MVP_RUN_TOOL_DRY_RUN: PASS` (the `diagnostic` case among its cases); `BE_MVP_SNAPSHOT: PASS self-test cases=30`; `BE_MVP_TOOLS_CHECK: PASS`; `BE_MVP_BUDGETS: PASS measured=32`; `BE_MVP_EVIDENCE: PASS development … files=282 images=253 qemu_attempts=71`; `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=46 boundary=13` |
| `./mvp/mvp claim-ledger check` | 09:48:50 to 09:48:52 | `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=46 boundary=13`: schema, methods, evidence (`artifacts=95 records=9`), commits (`commits=16`), rendering, release surfaces (`candidate=3 commit=89ef04e9`), guide commands (35), phrasing (35 literals, 3 conditionals), privacy (549 files), headers |
| `./mvp/mvp evaluate` | 09:48:52 to 09:54:03 | `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655`; `BE_MVP_IMAGE_IDENTITY: PASS images=253 same=253 differing=0`; inside: `BE_MVP_CHECK: PASS`, `BE_MVP_QEMU: PASS runs=58 attempts=73 refused=15`, `BE_MVP_LICENSES: PASS identifiers=2 files=857 texts=2 source=walk`, `BE_MVP_LOCK: PASS roles=26 host_only_skipped=6 closure=259`, the snapshot self-test skipped saying so (no gitdir), the partition self-test skipped saying so (root); the fetch took all 259 RPMs from the verified cache |
| `make -C bringup/k3-b0 host-test` | 09:54:03 | `kexec-load self-test: 14/14 PASS` (`launcher_runs_the_loader_isolated` among them); `BE_B0_MARKER_SELF_TEST: PASS` |
| `make -C bringup/k3-b6 tools-check` | 09:54:03 to 09:54:59 | `BE_B6_TOOLS_CHECK: PASS`; `BE_B6_RUN_TOOL_DRY_RUN: PASS`; `BE_B6_CAPTURE_SELF_TEST: PASS cases=101`; `BE_B6_MARKER_SELF_TEST: PASS cases=263`; the kexec-load self-test with `launcher_runs_the_loader_isolated` |
| `make -C bringup/k3-b7 tools-check` | 09:54:59 to 09:55:47 | `BE_B7_TOOLS_CHECK: PASS`; `BE_B7_RUN_TOOL_DRY_RUN: PASS`; `BE_B7_CAPTURE_SELF_TEST: PASS cases=86`; `BE_B7_MARKER_SELF_TEST: PASS cases=439`; the kexec-load self-test with `launcher_runs_the_loader_isolated` |
| `git diff --check` | 09:55:47 | no output |
| `node scripts/check-doc-sources.mjs`; `npm run docs:source-check` | after the driver, same clean tree | `Documentation source check passed: site_markdown=152 …`; the checker's self-tests PASS; `Documentation source gate isolation: PASS … adversarial_cases=34` (with the main checkout's `node_modules` linked in for the run and removed after) |

Earlier runs of the same driver at `da9dc9a5`, `6daeb1f4`, and
`9c908d12` are the development history of section 5's findings, not
evidence. The evidence bundle of `check` is under
`build/mvp/evidence/check` and the evaluator's record under
`build/mvp-evaluator/record/20261101T094852Z` (outside the tree); the
retained evidence of the sweep is this packet, the development-log entry,
and the tests in the tree. No `rc-record` was made: the sweep is not a
release candidate.

## 7. Recommended human review sequence

Use a detached worktree so nothing local affects what you read or run:

```sh
git worktree add --detach ../be-sweep3-review 3b7ab0e3e43bdad48772c0ae5eb8d831f218c29f
cd ../be-sweep3-review
git log --oneline 8b7559d2..3b7ab0e3
git diff --stat 8b7559d2..3b7ab0e3
```

1. *The rows against the review.* The consolidated review's table (its
   `README.md`, rows 1 to 12) beside section 2 here, one row at a time;
   the development-log entry in `mvp/README.md` ("Debt sweep 3") gives
   each row's mechanism and test in a paragraph.
2. *The accepted-byte change.* `git diff 8b7559d2..3b7ab0e3 -- bringup`:
   the launchers' `remote_command()`, the `-I` call sites, the gate, and
   the `kexec-approval` targets; then `bringup/k3-b0/tests/test-kexec-load.py`'s
   `launcher_runs_the_loader_isolated` and B6/B7's dry-run cases
   `kexec-unapproved` and `kexec-hostile-name`.
3. *The two mechanism departures.* `mvp/tools/k3-make-partition.sh`
   (`backup_dir_problem`, `excl`, step 1) with `mvp/tests/test-k3-make-partition.sh`'s
   seven new cases; `mvp/tools/gen-scenario.py` (`SCENARIO_NAME`,
   `VARIANT_NAME`, `PROBE_NAME`, the containment check).
4. *The allowlist.* `mvp/tools/k3-console.sh` `diagnostic()` and the
   `case_diagnostic` lists in `mvp/tests/run-tool-dry-run.sh`.
5. *The release surfaces and licensing.* `mvp/docs/claim-ledger.json`'s
   `release` object, C-05, and C-40; `mvp/docs/claim.md` and `guide.md`
   where "kexec" appears; `COPYING`; `mvp/tools/snapshot-readme.md`.
6. *The standing rules.* `.github/copilot-instructions.md`, "Privileged
   tooling standard"; `mvp/README.md` open items 94 to 98.
7. *Re-run what you like* (host only; nothing touches the board):
   `./mvp/mvp claim-ledger check`; `make -C mvp partition-tool-check`;
   `make -C mvp snapshot-check`; `make -C mvp lint`;
   `make -C bringup/k3-b0 host-test`; `./mvp/mvp check` (about 6 minutes
   with the pinned guest kernel built; it needs the external inputs the
   guide names).

## 8. Human decision checklist

- [ ] The sweep's scope matches the approved remediation plan and your five
      answers of 2026-11-01 (`harden_and_gate`, `gate_variable`,
      `exclude_from_snapshot`, `defer_to_migration`, `tier1_now`).
- [ ] The accepted B0/B6/B7 tooling change (rows A and D) is what
      `harden_and_gate` authorized, and the B-series results stay
      accepted history without re-acceptance.
- [ ] Departures 1 to 3 of section 5 (the interior dot, the ownership rule
      in place of `mktemp -d`, the lock that did not move and the measured
      38/25) are acceptable.
- [ ] The claims of section 3 match the evidence of section 6, and the
      claim statement and required limit are unchanged.
- [ ] The trust assumptions of section 3 are acceptable.
- [ ] The negative tests cover the paths that matter to you (section 4).
- [ ] Nothing of tier 2, no milestone, no release-path step, and no
      push, merge, snapshot refresh, or publication is started.
- [ ] Decision: accept exact commit `3b7ab0e3`, request revisions, or
      defer.

## 9. After the decision

- **Accept.** Say so naming `3b7ab0e3`; the acceptance record (this
  packet's decision section, the development log, `planning/HANDOFF.md`,
  and `.github/copilot-instructions.md`) is then written as its own commit
  naming that SHA and the date. Say separately whether the development
  branch `beryllium/single-hart-runtime-r0` is to be fast-forwarded to the
  acceptance record and pushed to the private `origin` (it is six commits
  ahead of `origin` already, as the handoff records), and whether the
  public review snapshot is to be refreshed (`mvp/tools/snapshot.sh update`
  and your push). Open items 94 to 98 stay open until you decide each.
- **Request revisions.** Name the rows or departures; the revision is a
  new commit on the same branch with a new packet; `3b7ab0e3` is not
  treated as accepted.
- **Defer.** Everything stays as it is: the branch local and unpushed,
  the development branch at `8b7559d2`, the public snapshot at
  `1ae5fd8c`, tier 2 waiting for the Claude CLI and Codex CLI reviews.

**Status:** debt sweep 3 is implemented at exact commit `3b7ab0e3`, every
planned gate passing from a clean tree, and **responsible-human accepted
as of 2026-11-01** (`accept 3b7ab0e3, fast fwd, push, use your best
judgement`); the development branch is fast-forwarded to the commit
recording the decision and pushed with the sweep's branch to the private
`origin` on the same instruction.

**Next:** your push of the refreshed public review snapshot, if and when
you want it (`git push origin main` from your local clone, a
fast-forward of the public `main`); your decisions on open items 94 to
97 (the closure's remedies first); the two independent S3-C design
reviews are processed on the S3-C plan branch under your direction of
the same day.

**Action required from you:** none on this commit.
