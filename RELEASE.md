<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# Release record: Beryllium MVP 1.0

This is the release record of this repository. It states where the
content came from, how it was copied and adapted, what was fixed after
two reviews before release, what was scanned and how the responsible
human classified it, what the gates gave here, and how the release is
tagged.
`RELEASE.txt` is its machine-readable marker. Each table between a pair of
`release.py` markers is rendered by the release path's internal tools
(`release/release.py record`, in the private internal repository) from
this repository and the responsible human's selection, and is checked
against a fresh rendering before this file is committed.

## Provenance

This repository's history begins at its copy commit. The source is a
commit of the project's private internal repository: the internal record
of the acceptance of MVP 1.0 release candidate 4 over its internal
candidate tree. The responsible human selected what migrates (the release
path's step 2) and accepted the plan for this repository (step 3), both on
2026-11-06.

<!-- release.py:begin provenance -->
| Item | Value |
| --- | --- |
| Source commit, the private internal repository's | `9d06b0245c39a34a0b2c8cbd45d40db07cdebb68` |
| Source tree, the private internal repository's | `5d1714aab58dd666053ba323ab13eeababeb3db4` |
| MVP 1.0 release candidate 4, the private internal repository's | `d70a8535474a690920ff152e7b38a25c589adba9` |
| Candidate tree commit, the private internal repository's | `a6eaa88501b1d08b9e83c734d692c82376117e77` |
| Selection, accepted 2026-11-06, the private internal repository's | `38fa3a0803fc898ac357078e5ea95768581a271f` |
| Step 3 plan, accepted 2026-11-06, the private internal repository's | `6944d7b4374eab370e5cf706b9fec1ec990c0498` |
| Copy commit, this repository's | `230d62b8b94afecf07dec16ad8653b643fc22666` |
| Copy commit's tree, this repository's | `9383943ff5c3091b63173f09849480230502170d` |
| Files copied byte for byte | 4,585 (4,370 regular and 215 executable; 46,073,684 bytes) |
| Files excluded | 101 in 10 entries (2,743,276 bytes) |
<!-- release.py:end provenance -->

## The copy and its adaptations

The copy commit holds the selected tree: every file of the source but the
excluded ones, each with its own bytes and mode, so that the commit's tree
ID is the selected tree's. Each of the next eight commits is one
adaptation that lets release candidate 4's gates run here or that
describes this repository,
touching only its group's files, in the order the step 3 plan sets. Each
reason is the one the step 2 selection gives.

<!-- release.py:begin adaptations -->
| Commit | Group | Files | Reason |
| --- | --- | --- | --- |
| `55c3b6db72dc6cccae6f159af3fb9fa91a1a56bc` | A6 | `planning/HANDOFF.md` (new) | The handoff is excluded but linked from 17 kept pages, routed by the site, and hashed by A3's list |
| `63852d737b5502d2c3d2dd6db12e1eb7c89bf040` | A2 | `be` (new), `Makefile` (new) | Gates 6 and 7 enter through the root; the internal root reaches Helium and carries R-series pins (D3; `defer_to_migration`) |
| `caa11b10f2fe968719a673f7e2083f651cb96a42` | A1 | `README.md` (new) | The internal status page is excluded (M4 plan Q13) |
| `05b253dac5b186d73acd0fed0ed3f9b5633a00fd` | A3 | `model/tests/generate-evidence.sh` (revised) | Its fixed list names seven paths the selection excludes (`sha256sum` fails on a missing file) |
| `5f7beb8ac5f148802febc231c1c63e66de3bb63f` | A4 | `scripts/check-doc-sources.mjs` (revised), `scripts/test-doc-source-check.mjs` (revised), `docs/check-links.mjs` (revised), `docs/README.txt` (revised), `scripts/serve-docs.mjs` (revised), `scripts/docs-preview.sh` (revised), `package.json` (revised) | The documentation check validates the Helium site and the `.github/` policy documents; the link checker's owner-tasking contract reads the instructions and the handoff |
| `337d10972cc2a0a306daf6872b84c15734818f17` | A5 | `RELEASE.txt` (new), `mvp/tools/claim-ledger.py` (revised), `mvp/verify/specification-93a8d136.md` (new), `mvp/verify/tools/specification-text.sh` (new), `mvp/tools/verifier/verify.sh` (revised), `mvp/verify/tools/in-image.sh` (revised), `mvp/tools.mk` (revised) | Under fresh history: the ledger's commit check resolves 36 internal commits; `verify` exports the frozen specification from internal commit `93a8d136`; the snapshot tool's self-test needs the internal layout |
| `298cc2df598044d3741147aef9be38ec73b207e6` | A7 | `SECURITY.md` (revised), `COPYING` (revised), `LLM_POLICY_ALIGNMENT.md` (revised), `mvp/docs/guide.md` (revised), `mvp/docs/ai-assistance.md` (revised) | Wording that describes the internal repository or the review snapshot (section 8) |
| `46867d89ab6fc9b6247e57af27a2c19f8019c94a` | A8 | `RELEASE.md` (new) | Provenance under fresh history |
<!-- release.py:end adaptations -->

## The fixes after two reviews

After the adaptations were signed off, and before the gates ran for this
record, two reviews read this repository at the last adaptation: a
security review, made with an unlisted model, and a review of the
project's state before release, made with `claude-fable-5.1`, each
read-only and at the responsible human's direction. Each finding was put
before MVP 1.0, after it, or deferred for more analysis. The commits
below answer the findings put before MVP 1.0, each touching only its
group's files: the F groups the tools and gates, the D groups the
documentation and the planning site. A finding's ID is its review's: S
for the security review, T for its notes on third-party components, and
P for the project review. The reports are kept in the private internal
repository's planning record; the findings that bear on using this
release are among `README.md`'s known limitations, but for S-06, which
is described after the table below. The responsible human reviewed the
fixes and signed each of them off.

<!-- release.py:begin fixes -->
| Commit | Group | Findings | Files | Reason |
| --- | --- | --- | --- | --- |
| `475c94e701aa510ea42da165e7d4e06c3eedc2b3` | F1 | S-01 | `mvp/Makefile` (revised), `mvp/docs/claim-ledger.json` (revised), `mvp/docs/claim-ledger.md` (revised), `mvp/docs/guide.md` (revised), `mvp/guest.mk` (revised), `mvp/tests/run-qemu.sh` (revised), `mvp/tests/run-tool-dry-run.sh` (revised), `mvp/tests/session-typist.py` (revised), `mvp/tests/uboot-rehearsal.sh` (revised), `mvp/tools.mk` (revised), `mvp/tools/evaluator/evaluate.sh` (revised), `mvp/tools/lock/tool-lock.conf` (revised), `mvp/tools/lock/tool-lock.py` (revised), `mvp/tools/run-reference-boot.sh` (revised) | QEMU's OpenSBI firmware bound to a SHA-256 pin in the tool lock, and checked against it before every run that boots it |
| `e59acdceec6d22deec54782ea6beced869511973` | F2 | S-02 | `mvp/docs/guide.md` (revised), `mvp/mvp` (revised), `mvp/tests/run-tool-dry-run.sh` (revised), `mvp/tools/evaluator/evaluate.sh` (revised) | ./mvp/mvp evaluate runs the evaluator in the wrapper's clean environment: the lock check first, every command by its absolute path, and Python in isolated mode |
| `d8ffb0e8db689638b522f47305a852efc7f6a9d2` | F3 | S-03 | `Makefile` (revised), `be` (revised), `mvp/tests/run-tool-dry-run.sh` (revised) | ./be runs make in a clean environment and refuses make's own controls, a dry run prints no PASS, and gate 6 installs its packages with npm ci |
| `ebc0d39489684a5556506e92b86f239e2a9bfd8f` | F4 | S-05 | `mvp/docs/claim-ledger.json` (revised), `mvp/docs/claim-ledger.md` (revised), `mvp/tests/fake-board.py` (revised), `mvp/tests/run-tool-dry-run.sh` (revised), `mvp/tools.mk` (revised), `mvp/tools/k3-campaign.sh` (revised), `mvp/tools/k3-console.sh` (revised), `mvp/tools/k3-env.sh` (revised), `mvp/tools/k3-input-characterize.sh` (revised), `mvp/tools/k3-preflight.sh` (revised), `mvp/tools/k3-run.sh` (revised), `mvp/tools/k3-stage.sh` (revised), `mvp/tools/k3ctl.sha256` (revised), `mvp/tools/platform-probe.py` (revised) | The board tools run Python as /usr/bin/python3 -I -B, and their remote scripts from / |
| `7fedf6cffb5b3306198bd3d0d59d11ca20079ea2` | D1 | P-02, P-03, P-04, P-05, P-06, P-10, P-13, P-14, S-04, T-04 | `CONTRIBUTING.md` (new), `LLM_POLICY_ALIGNMENT.md` (revised), `README.md` (revised), `docs/README.txt` (revised), `mvp/docs/ai-assistance.md` (revised), `mvp/docs/guide.md` (revised), `planning/mvp-m1-plan.md` (revised), `planning/mvp-m4-plan.md` (revised), `planning/mvp-m9-plan-review-gpt-6-astra.md` (revised), `planning/mvp-rc-walkthrough.md` (revised) | The release's documentation: what runs where, the known limitations, the maintainer, how to contribute, the AI-assistance record, and the planning site's build |
| `d99539f8c4d5a4088813ddaf3a4a07b92337ad32` | D2 | P-04 | `planning/README.md` (revised), `planning/project-orientation.md` (revised), `planning/roadmap.md` (revised) | A reading note on the planning record's three entry pages, which give the source commit's position |
| `d6f96ddd56533853f52f201536d9ab04897433d9` | D3 | P-03 | `planning/.vitepress/config.mts` (revised) | Links to the planning README render as the page the planning site generates, so that the site's link check passes |
<!-- release.py:end fixes -->

### A finding not fixed in this release

One finding of the security review, S-06, is not fixed in this release,
and bears on using it. In the `anchor` scenario the host domain may pause
or terminate the protected domain. If the protected domain has just made
a management request of its own, and hart 0 delivers such an authorized
order to it before taking that request from the protected domain's ring,
the protected domain treats the order as a protocol error and fails, and
hart 0 ends the run. The race pauses or terminates no domain against the
sealed grants, grants no management right, and exposes no memory: its
effect is a failed run, and the claim's
[required limit](mvp/docs/claim.md#required-limit) claims nothing about
availability. It was found by reading the code; no run has shown it. Its
fix, a change to the protocol between the harts for management requests,
is deferred until after MVP 1.0.

## The exclusions

These entries of the source are not in this repository, each for the
reason the responsible human's selection gives.

<!-- release.py:begin exclusions -->
| Entry | Files | Bytes | Reason |
| --- | ---: | ---: | --- |
| `pathfinder/` | 66 | 402,902 | Helium material is not part of the MVP release; its current source is the separate helium-te-poc repository |
| `.github/` | 5 | 204,187 | The AI operating instructions and skills (the review snapshot's exclusion) |
| `tests/r8/` | 23 | 1,562,364 | The dropped R8 stage's accepted H0 package; its run-make.sh is a checked-in stripped x86-64 executable |
| `planning/HANDOFF.md` | 1 | 416,629 | The internal session handoff with its Project Manager returns; a stub is written at the path (A6) |
| `README.md` | 1 | 50,493 | An internal status page; a release README is written at the path (A1) |
| `be` | 1 | 32,240 | The internal root wrapper reaches the excluded Helium pathfinder and carries predecessor acceptance pins; a new build root is written (A2) |
| `Makefile` | 1 | 4,152 | The internal root Makefile reaches the excluded Helium pathfinder and carries predecessor acceptance pins; a new build root is written (A2) |
| `scripts/check-be.sh` | 1 | 33,891 | It checks the internal root wrapper and carries R-series acceptance pins (A2) |
| `mvp/tools/snapshot.sh` | 1 | 26,228 | The internal repository's review-snapshot tool: it names the private internal repository, and its self-test requires the internal repository's excluded paths |
| `mvp/tools/snapshot-readme.md` | 1 | 10,190 | The review-snapshot tool's README template |
| All | 101 | 2,743,276 | |
<!-- release.py:end exclusions -->

## The scans and their classification

Every blob reachable from `main`, every commit message, and every
identity were scanned twice. The first scanner is the tools' patterns for
the categories of step 2's section 9. The second is gitleaks 8.30.0,
Fedora 44's package, its signature and digests checked, unpacked and never
installed, run with its default rules only, so that no file in this
repository can silence it. The responsible human classified the first
scan's findings, over the copy commit, on 2026-11-06 (`classify as
proposed`). The rules below are that classification: the first matching
rule wins, and each is shown with its count over this commit's history. No
finding is of a stop kind, and every finding in a file added or changed
after the copy commit is covered by a rule.

<!-- release.py:begin rules -->
| Rule | Category | Path pattern | Class | Reason | Findings | Occurrences |
| --- | --- | --- | --- | --- | ---: | ---: |
| R1 | `credential` | `bringup/k3-b0/tests/fedora-rehearsal/run.sh` | kept | The B0 QEMU rehearsal's default sudo password (`linux`) for a disposable Fedora test image; FEDORA_SUDO_PASSWORD overrides it, and it opens no real system (step 2, section 9) | 1 | 1 |
| R2 | `credential` | `mvp/README.md` | kept | gitleaks generic-api-key on Fedora 44's public RPM signing-key fingerprint, quoted in the evaluator's record | 1 | 2 |
| R3 | `credential` | `mvp/tools/evaluator/fetch-closure.py` | kept | gitleaks generic-api-key on Fedora 44's public RPM signing-key fingerprint, which the closure fetch pins | 1 | 1 |
| R4 | `credential` | `tests/r6/fixtures/*` | kept | gitleaks generic-api-key on each R6 fixture's "api" field, which names the monitor function it targets (be_r5_handle_exit) | 10 | 10 |
| R5 | `credential` | `bringup/*` | kept | Variables named token, secret, or password in the B-series scripts and checkers; the rehearsal's password is read from the environment; no value is a secret | 15 | 63 |
| R6 | `credential` | `tests/*` | kept | Variables named token or secret in the R-series test tools, and gitleaks generic-api-key on a constant's name (bannerKey in tests/r6/tool-lock.mjs); no value is a secret | 14 | 48 |
| R7 | `credential` | `mvp/*` | kept | Variables named token or secret in the monitor, checkers, and tools; the anchor scenario's deliberately public test secret (BE-MVP-M2-TEST-SECRET-0000000000, in hex); gitleaks generic-api-key on a test comment naming the secret-shared variant; no value is a secret | 14 | 63 |
| R8 | `codasip` | `planning/sidebar-cheri-mvp.md` | kept | The public names of the emulator branch and CPU model that the CHERI runs used, in the CHERI-Alliance QEMU repository's public branches and source, checked 2026-11-06; no non-public material | 1 | 3 |
| R9 | `codasip` | `planning/mvp-m7-plan.md` | kept | A line reference (L110) that the CPU-model pattern matches; not a Codasip name | 1 | 1 |
| R10 | `session-id` | `@message/*` | kept | Each commit's Copilot-Session trailer, naming the owner session that made it (the copy commit's is part of its fixed message, S3W-3) | 18 | 36 |
| R11 | `session-id` | `mvp/docs/ai-assistance.md` | kept | The AI-assistance disclosure names one session deliberately (step 2, section 9) | 2 | 9 |
| R12 | `session-id` | `planning/*` | kept | Session identifiers in the three 2026-07-20 session-analysis pages and two R-series review records, history at the source commit (step 2, section 9) | 5 | 7 |
| R13 | `home-path` | `planning/*` | kept | Home-directory paths in seven planning review records, packet-time evidence at the source commit (step 2, section 9) | 7 | 15 |
| R14 | `home-path` | `bringup/*` | kept | A local checkout path in each of two B-series READMEs (step 2, section 9) | 2 | 2 |
| R15 | `home-path` | `mvp/README.md` | kept | A local Linux mirror's path in three open items (step 2, section 9) | 1 | 3 |
| R16 | `home-path` | `mvp/tools/*` | kept | Synthetic home paths in the tools' self-tests and the claim ledger's privacy rule | 4 | 8 |
| R17 | `home-path` | `scripts/*` | kept | Synthetic home paths in the documentation check's self-test | 2 | 4 |
| R18 | `home-path` | `tests/*` | kept | Synthetic home paths in the R6 and KVM0 tests | 3 | 5 |
| R19 | `board-network` | `mvp/results/*` | kept | The board's LAN host names, its ssh target, and its private address in the retained board records | 46 | 133 |
| R20 | `board-network` | `bringup/*` | kept | The same in B0 to B7's records and READMEs, and the addresses of B0's point-to-point test link | 57 | 98 |
| R21 | `board-network` | `mvp/*` | kept | The same in the MVP's open items and the board tools' defaults, and synthetic hosts in the tools' privacy rules and tests | 12 | 52 |
| R22 | `board-network` | `planning/*` | kept | The same in two planning records | 2 | 2 |
| R23 | `board-network` | `tests/kvm0/*` | kept | A board address in the dropped KVM0 workstream's contract, history | 1 | 1 |
| R24 | `machine-id` | `mvp/results/*` | kept | Linux boot IDs (boot_id, boot_id_before, boot_id_after) in the board records, random per boot (step 2, section 9) | 94 | 340 |
| R25 | `machine-id` | `bringup/*` | kept | Linux boot IDs in B0 to B7's records, random per boot | 42 | 55 |
| R26 | `machine-id` | `mvp/*` | kept | Synthetic MAC addresses and serial numbers in the privacy rules' patterns and self-tests; step 2 found they occur only as checker patterns | 6 | 20 |
| R27 | `private-locator` | `package-lock.json` | kept | npm packages' public funding links (github.com/sponsors/...) | 1 | 27 |
| R28 | `private-locator` | `planning/*` | kept | Public upstream repositories' URLs; the public review snapshot's repository name; the former private identity and the private repository's name in historical records, each already public in the review snapshot | 52 | 195 |
| R29 | `private-locator` | `mvp/*` | kept | The same in the MVP's README, its licence manifest's and verifier's public source URLs, and the claim ledger's privacy rule's own patterns | 5 | 17 |
| R30 | `private-locator` | `LLM_POLICY_ALIGNMENT.md` | kept | The same in the AI policy document, already public in the review snapshot; A7 rewords what describes the internal repository | 2 | 16 |
| R31 | `private-locator` | `scripts/*` | kept | The documentation check's private-locator rule, its allowances, and its self-test's cases | 4 | 18 |
| R32 | `private-locator` | `bringup/*` | kept | Public upstream repositories' URLs in B1 to B3's READMEs | 3 | 3 |
| R33 | `internal-process` | `planning/*` | kept | References to the internal process (the project-management returns, the instructions directory, and the session handoff) in the planning record at the source commit | 96 | 324 |
| R34 | `internal-process` | `@message/*` | kept | The copy commit's message names the excluded instruction files and the excluded session handoff | 2 | 3 |
| R35 | `internal-process` | `mvp/*` | kept | The same in the MVP's README, the retained records, and the AI-assistance disclosure (adapted by A7) | 13 | 68 |
| R36 | `internal-process` | `LLM_POLICY_ALIGNMENT.md` | kept | The same in the AI policy document (adapted by A7) | 1 | 2 |
| R37 | `internal-process` | `scripts/*` | kept | The documentation check's rules for the instructions directory and the handoff (adapted by A4) | 2 | 16 |
| R38 | `internal-process` | `docs/*` | kept | The link checker's owner-tasking contract (adapted by A4) | 1 | 16 |
| R39 | `internal-process` | `model/*` | kept | The model's evidence script's list of files (adapted by A3) | 2 | 4 |
| R40 | `internal-process` | `tests/*` | kept | The R1 to R3 evidence and report scripts' lists naming those files, history | 4 | 9 |
| R41 | `third-party` | `LICENSES/*` | kept | The licence texts the repository's licences require | 6 | 8 |
| R42 | `third-party` | `mvp/guest/keys/*` | kept | BusyBox's and musl's maintainers' public signing keys, pinned for the guest build's verification | 2 | 2 |
| R43 | `third-party` | `mvp/results/*` | kept | The board vendor's name in the board's console captures | 199 | 847 |
| R44 | `third-party` | `bringup/*` | kept | The vendor's name in B0 to B7's records and READMEs | 38 | 128 |
| R45 | `third-party` | `planning/*` | kept | The vendor's name and short attributed quotations of vendor documentation in planning records (step 2, section 9) | 30 | 63 |
| R46 | `third-party` | `mvp/*` | kept | The vendor's name in the MVP's README, claim, guide, ledger, and tools, and the guest-pins tool's key-armour marker | 10 | 20 |
| R47 | `third-party` | `tests/kvm0/*` | kept | The vendor's name in the dropped KVM0 workstream's tests, history | 1 | 2 |
| R48 | `unresolvable-ref` | `*` | kept | Internal commit IDs, by design under fresh history (step 2, section 6); RELEASE.md and README.md say why they do not resolve | 332 | 4,357 |
| R49 | `internal-process` | `RELEASE.md` | kept | The release record's exclusions and adaptations tables name the excluded instruction files and the session handoff, with the selection's reasons, as its required content | 1 | 15 |
| R50 | `codasip` | `RELEASE.md` | kept | The release record's rules table names the category of R8, R9, and this rule, and quotes R9's reason, as its required content | 1 | 15 |
<!-- release.py:end rules -->

## Identifying strings

The records keep identifying strings as evidence of their time: the
board's network names and address, home-directory paths, and a former
repository identity. This table counts them over the copy commit's files,
the material that migrated byte for byte:

<!-- release.py:begin strings-copy -->
| String | Distinct values | Occurrences | Files |
| --- | --- | --- | --- |
| private IPv4 address (RFC 1918) | 3 | 50 | 19 |
| board host name on the development LAN | 2 | 153 | 96 |
| home path | 9 | 34 | 17 |
| former repository identity | 1 | 30 | 20 |
<!-- release.py:end strings-copy -->

And over this commit's tree:

<!-- release.py:begin strings-exit -->
| String | Distinct values | Occurrences | Files |
| --- | --- | --- | --- |
| private IPv4 address (RFC 1918) | 3 | 50 | 19 |
| board host name on the development LAN | 2 | 153 | 96 |
| home path | 9 | 34 | 17 |
| former repository identity | 1 | 27 | 19 |
<!-- release.py:end strings-exit -->

## Why internal commit IDs do not resolve here

The planning record, the claim ledger, the results, and the AI-assistance
disclosure cite commits by their IDs in the private internal repository,
whose history this repository does not hold (fresh history, the step 2
selection's section 6). They are kept as cited, as the records' own
evidence, and they do not resolve here. The claim ledger's commit check
reads `RELEASE.txt` and skips them with that reason.

## Wording kept although it describes the internal repository

The selection keeps these files byte for byte, although some of their
wording describes the private internal repository or the public review
snapshot as they stood at the source commit:

- the planning record's status pages, `planning/roadmap.md` and
  `planning/README.md`: the project's position, branches, and pushes at
  the source commit, each with a reading note after its title that says
  so (D2, among the fixes above);
- the licence manifest, `mvp/docs/licence-manifest.md`, whose "A later
  distribution" says that "the review snapshot holds sources and pins": its
  generator, `mvp/tools/licence-manifest.py`, writes that sentence, and
  only a change to the generator would alter it, which this step does not
  make;
- the CHERI sidebar, `planning/sidebar-cheri-mvp.md`, which cites
  evidence in the beryllium-cheri research repository, not yet published
  (the step 2 selection's Q15).

## The policy recheck

On 2026-11-06, before this record was written, the Linux kernel's
`coding-assistants.rst`, `generated-content.rst`, and
`submitting-patches.rst` were read at that day's mainline commit against
the revision `LLM_POLICY_ALIGNMENT.md` had checked on 2026-10-31. Each is
byte for byte the same, so nothing bears on this repository's
disclosure, licence, or sign-off (the step 3 plan's Q10). The policy's
partner matrix names both commits.

## AI assistance

This repository was made with AI assistance under the responsible human's
review and decisions. [`mvp/docs/ai-assistance.md`](mvp/docs/ai-assistance.md)
discloses it, its section 8 covering the release path's steps 2 and 3,
the two reviews before release, and the fixes, and
[`LLM_POLICY_ALIGNMENT.md`](LLM_POLICY_ALIGNMENT.md) states the policy.

## Sign-off

Each commit that automation prepared carries the `Co-authored-by: Copilot`
and `Copilot-Session` trailers. The responsible human accepted the exit
commit of step 3 and added his own `Signed-off-by` to each of its nine
commits with one command (the step 3 plan's Q11); he then reviewed the
fixes after the two reviews and signed each of them off the same way, and
he signed off step 4's commit, which adds the gates' records, and step
5's, which adds the tag's section below, each after his review of it. The
internal tools checked, commit for commit, that each sign-off changed
nothing but its line: each tree and parent tree, each author, and each
message otherwise. Each sign-off gave its commits new IDs, the ones this
record names. A8's message was written before the first sign-off: where
it says that every commit ID of this repository it names resolves here,
it describes the history as it was then.

## Gate results (step 4)

Step 4 ran release candidate 4's eight gates, in its order, from a clean
local clone of this repository at commit
`d6f96ddd56533853f52f201536d9ab04897433d9`, the tip of the signed fixes
above, on the development host (Fedora Linux 44 (Server Edition),
x86_64), on 2026-11-08 from 01:35 to 05:54 UTC, each gate's log kept by
a driver outside the tree. Each gate passed:

| Gate | Command | Result | Seconds |
| --- | --- | --- | --- |
| Tool lock | `./mvp/mvp tool-lock check` | `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259` | 3 |
| Check | `./mvp/mvp check` | `BE_MVP_CHECK: PASS` | 805 |
| Evaluator | `./mvp/mvp evaluate` | `BE_MVP_EVALUATE: PASS` | 805 |
| U-Boot rehearsal | `make -C mvp uboot-build`, then `./mvp/mvp uboot-rehearsal` | `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=12 refused=5 qemu=10.2.2` | 162 |
| Kernel reproduction | `make -C mvp kernel-repro` | `BE_MVP_KERNEL_REPRO: PASS outputs=23 identical` | 53 |
| Model check | `./be model-check` | `Beryllium Architecture Model 0.2 evidence: PASS` | 142 |
| Model evaluator | `./be evaluate` | `BE_EVALUATION: Model 0.2 rootless evidence PASS` | 132 |
| Verifier | `./mvp/mvp verify` | `BE_MVP_VERIFY: PASS` | 13,396 |

The verifier's suites gave release candidate 4's verdicts and counts,
which its record's README lists: WP and CN remain OPEN, and CBMC's
results are bounded model checks.

Beside the eight gates, `./be docs-check`, the planning site's full
build and link check, passed before `verify` ran
(`Documentation check passed: 172 Markdown sources, 173 HTML pages, no broken local targets.`).

**The comparison with release candidate 4.** The internal release tool
compared the release record's
`mvp/results/20261108-release/host/images.sha256` with release candidate
4's, `mvp/results/20261105-rc4/host/images.sha256`: each of the 185
path-independent outputs (the 162 flat images and the 23 guest outputs)
equals release candidate 4's, digest for digest, and none is missing or
added. The 156 ELF files are reported, not compared: 50 of them, each a
`be-mvp.elf`, differ, as they did in the comparison at step 3's exit,
because an ELF file keeps its build directory's path.

**The records**, added by step 4's commit:

- [`mvp/results/20261108-release/`](mvp/results/20261108-release/rc.txt):
  the release record, written by `./mvp/mvp rc-record` from the gates'
  logs and evidence: its `mvp/results/20261108-release/rc.txt` holds
  each gate's line, and its manifest each file's digest;
- [`mvp/results/20261108-verify-release/`](mvp/results/20261108-verify-release/README.md):
  the verifier's records, in release candidate 4's shape;
- [`mvp/results/20261108-model-evaluator/`](mvp/results/20261108-model-evaluator/README.md):
  the packages the model evaluator's image held (`README.md`, "Known
  limitations of this release").

A gate's PASS is the result of its own checks on these bytes on this
host; what the evidence shows, and what it does not, is the claim's
[required limit](mvp/docs/claim.md#required-limit) and the
[claim ledger](mvp/docs/claim-ledger.md).

The results above leave out the digests and image names the gates print;
`mvp/results/20261108-release/rc.txt` and
`mvp/results/20261108-verify-release/verify.txt` hold each line in full.

## The release's tag (step 5)

MVP 1.0 is released at this repository's tag `mvp-1.0`: an annotated tag
that the responsible human created and signed with his OpenPGP key,
fingerprint `4137 0FEA 4038 E3A3 B4BB  BD3B 7120 D2C2 6E2F 20C6`, on the
commit that adds this section, after his review of that commit (the
release path's step 5). That commit holds release candidate 4's monitor
and images, unchanged: the 185 path-independent outputs that step 4
compared equal release candidate 4's (above). The fixes after the two
reviews (above) changed the release's tools and documentation. The
claim, the claim ledger, and the guide keep the candidate's name, "MVP
1.0 release candidate 4"; the release and its tag are MVP 1.0.

That commit changes only this file and `SECURITY.md`. Of the gates,
only the licence check reads them, and only their first three lines,
which the commit leaves as they were; no record of the gates names them.
Step 4's results (above) therefore stand for it.

The tag's message names the tree of the commit it tags. To check the
tag, fetch the key, then check the signature and the tree:

```sh
gpg --keyserver hkps://keys.openpgp.org --recv-keys 41370FEA4038E3A3B4BBBD3B7120D2C26E2F20C6
git verify-tag mvp-1.0
git rev-parse 'mvp-1.0^{tree}'
```

`git verify-tag` must report a good signature by that key, and the last
command must print the tree that the message's `Tree:` line names.
