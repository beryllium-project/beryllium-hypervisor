<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Debt sweep 5 (item 95, the closure from public sources): review packet

This packet supports the responsible human's decision on exact commit
`e8ab73b7`, the candidate of debt sweep 5, which makes the evaluator's
package closure fetchable from public sources again by adding Fedora's
updates archive as a source of the fetch tool. It recorded the decision
below after it was given.

## Decision record

The responsible human accepted exact commit
`e8ab73b712a974dc25d6cd8eab9bad24bd129405` (parent `41c872b6`) as debt
sweep 5 on 2026-11-01 (13:03 in the human's time zone). The instruction,
given in reply to this packet's request to accept, revise, or defer that
exact commit (and to its offer of the fast-forward, the push, and the
snapshot re-refresh), was `accept  & ff + push , and  re-refresh`; it
names no SHA, and is read as the answer to this packet's request, the
only decision this packet asked for.

- **Scope:** acceptance covers exactly that commit and the claim boundary
  of section 3, the reading section 5 left to the human included: the
  accepted M0 plan's "from Fedora's repositories or koji" (M0-B) admits
  Fedora's updates archive as one of Fedora's repositories, and no plan
  erratum is directed. Sections 1 to 9 are the packet as presented, apart
  from the status rows of section 1 and the closing lines of section 9,
  which now show the outcome. `mvp/README.md` item 95 is closed by this
  acceptance and item 106 (Fedora 44's end of life) stays open, the
  human's.
- **The same instruction directs** the fast-forward of the development
  branch `beryllium/single-hart-runtime-r0` from `486fd5a9` to the commit
  recording this decision, the push of that branch and of
  `beryllium/mvp-debt-5` to the private `origin`, and the re-refresh of
  the human's local clone of the public review snapshot from the
  acceptance record (`mvp/tools/snapshot.sh update`, the gates run in it
  with no RPM cache, so that the snapshot's own README records the
  closure fetched from public sources, its record); the push of the
  clone's `main` to the public repository stays the human's act.
- **What it is not:** no release-path step; no tag or publication; no
  board command and no kexec; no change to the lock, the closure, the
  evaluator image, the claim statement, any accepted plan, or `mvp/src/`;
  no decision on Plan revision S3-C, whose second candidate `27d2e557` on
  `beryllium/mvp-s3c-plan` waits separately.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `e8ab73b712a974dc25d6cd8eab9bad24bd129405`, parent `41c872b6fd61535fbb6080a61e97928633793370`; the sweep is the two commits `41c872b6` (the tool) and `e8ab73b7` (the documents and record) on local branch `beryllium/mvp-debt-5` from `486fd5a9`, the development tip (`beryllium/single-hart-runtime-r0`, local and `origin`) |
| Current status | Implemented; the gates of section 6 ran at `e8ab73b7` from a clean tree; **responsible-human accepted as of 2026-11-01** (the decision record above) |
| Decision requested | None outstanding on this commit; the decision was `accept  & ff + push , and  re-refresh` |
| Successor status | None started. Plan revision S3-C's second candidate `27d2e557` on `beryllium/mvp-s3c-plan` awaits its own decision and is unaffected |
| Publication status | The same instruction directs the fast-forward of the development branch to the commit recording this decision, the push of it and the sweep's branch to the private `origin`, and the re-refresh of the human's local clone of the public review snapshot from the acceptance record (its push to the public `main`, at `6c71fa4c` as this is written, stays the human's act) |

The action this section asked of the human, the decision on `e8ab73b7`,
is taken; what follows it is in the decision record above and in
section 9.

### What the sweep is, in one paragraph

Item 95 said `./mvp/mvp evaluate` could not build the evaluator image on a
host without the development host's verified RPM cache, because Fedora's
`updates` repository drops a build when a newer one replaces it and koji
prunes its signed copies: a cache-less fetch on 2026-11-01 found 16 of
the 259 closure packages in no source the tool tried. On `summarize item
95` a read-only probe found that Fedora keeps every update build pushed
to stable for a supported release in a public updates archive the tool
did not try, that all 259 closure NEVRAs were served that day (135 by
the archive, 124 by the permanent release repository), and that the
archive's copy of the first missing package is byte-identical to the
closure's pin. The human chose remedy A of the four laid out (`do A`):
the archive becomes the fetch's third source, after the repositories and
before koji, with no trust change, since a file still enters the cache
only when its SHA-256 is the closure's. A cache-less fetch of the whole
closure from public sources then passed. The documents that told a third
party otherwise are corrected; item 95 is closed and the residual, Fedora
44's end of life, is item 106. No monitor source, claim statement,
accepted plan text, lock, closure, image, board command, or kexec.

## 2. Deliverables

| Deliverable | Paths | Purpose | Boundary | Review question |
| --- | --- | --- | --- | --- |
| The archive source, `41c872b6` | `mvp/tools/evaluator/fetch-closure.py`: `UPDATES_ARCHIVE`, `FEDORA_RELEASE`, `Package.archive_url`, `https_source` (koji's curl path, now shared), `archive_source`, `fetch_sources` (the order), nine self-test cases | A missing closure RPM is also looked for in Fedora's updates archive, by its NVRA file name fully percent-encoded, after the repositories and before koji | The evaluator's one network step; a file enters the cache only on a SHA-256 match with the closure, as before | Is the archive, Fedora infrastructure outside the project's control, acceptable as a source on the same footing as the repositories and koji (which it already depended on)? Is the order right? |
| The documents and record, `e8ab73b7` | `mvp/README.md` (evaluator paragraphs, file description, development log, items 95 and 106), `mvp/docs/guide.md` (section 8, item 3), `mvp/tools/snapshot-readme.md` ("How to run the checks") | The public-facing statement that the closure cannot be obtained from public sources is withdrawn; the residual is named | Documentation; the snapshot README template reaches the public snapshot on its next refresh | Does the snapshot README's new paragraph say what you want a third party told? |

## 3. Claim boundary

**The exact commit supports saying:**

- `fetch-closure.py` tries, in order, `MVP_RPM_CACHE` (when set), Fedora's
  `fedora` and `updates` repositories, Fedora's updates archive, and
  koji's signed copies, and admits a file only when its SHA-256 equals
  the closure's (unit test: the source order; the HTTPS sources through a
  faked curl, a served file with wrong bytes refused and kept out of the
  cache; `cases=48`; the old quoting rule and the old order each fail the
  self-test).
- On 2026-11-01 the whole closure fetched from public sources with no
  cache: `rpms=259 bytes=385621571 sources=fedora:116,updates:124,
  updates-archive:19`, koji not needed (an actual fetch, twice: before the
  commit and as a gate at the candidate, section 6).
- The lock, the closure, its digests, the evaluator image, and the
  images it checks are unchanged (`evaluate`: 253 of 253 identical).

**What remains trusted or assumed:** Fedora's signing and its retention
(the archive's documented policy is to keep stable updates for supported
releases); the host's `dnf` and `curl`; the pinned Fedora 44 key for
`--record` (unchanged, not re-run).

**Not run:** no board command, no kexec, no release-path step, no model
gate (nothing under `model/` changes), no B-series gate (nothing under
`bringup/` changes).

**The commit does not:** change the lock or the closure (no pin moves; the
ledger is untouched); change the claim statement, any accepted plan, or
`mvp/src/`; publish the verified cache or the image; decide S3-C; refresh
the public snapshot.

## 4. Security and correctness invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| Nothing unverified enters the cache, whatever the source | the tool's docstring, "Trust" | `admit()` on every fetched file before `os.replace` into the cache | self-test: "a served file whose bytes are not the closure's" refused and "it did not enter the cache" |
| A failed transfer leaves no file | `https_source` | `path.unlink(missing_ok=True)` on a non-zero curl status | self-test: "a transfer curl fails leaves no file" |
| The archive URL names the exact file | `Package.archive_url` | `<release>/x86_64/<NVRA>.rpm`, epoch dropped, `quote(safe='')` | self-test: the four URL cases; the live fetch of 19 files, each SHA-256 matched |
| The order is the documented one | `fetch_sources` | one list | self-test: with and without a seed |

## 5. Review history and resolved findings

1. **Item 95's figures** ("38 of 259 not in the repositories, 25 absent
   from koji") came from a `dnf repoquery` measurement in debt sweep 3;
   the fetch tool's own live run found 19 not in the repositories, 3 on
   koji's signed path, 16 in no source. The item's closure text records
   the correction; the live figures are the operative ones.
2. **The archive's encoding rule**: a literal `+` in a file name is a 404
   on the archive and a 200 on koji; the archive source encodes
   everything, koji's URL is unchanged. Found by probing `gcc-c++`
   before writing; covered by a self-test case that fails against koji's
   rule.
3. **`noarch` files** are under the archive's `x86_64` directory (15 of
   the closure's 26 `noarch` packages are updates there; the other 11 are
   GA packages in the release repository). Found by probing before
   writing; covered by a self-test case.

Open for the human's judgement: the reading that the accepted M0 plan's
"from Fedora's repositories or koji" (M0-B) admits the updates archive as
one of Fedora's repositories; the alternative is a plan erratum, which
the human may direct.

## 6. Validation and retained evidence

Gates at `e8ab73b7`, from a clean tree (`git status --porcelain` empty) in
the worktree `worktrees/beryllium-hypervisor/rc3-review-remediation`, the
external inputs linked from the main checkout, `MVP_RPM_CACHE` unset, one
gate at a time, logged under `build/mvp/sweep5-gates/` (outside the tree):

| Gate | Result | Time (UTC) |
| --- | --- | --- |
| `./mvp/mvp tool-lock check` | `BE_MVP_LOCK: PASS roles=32 host_only_skipped=0 closure=259 lock_sha256=2f1b732dcf24`; `BE_MVP_FETCH_SELF_TEST: PASS cases=48` | 19:08:42 to 19:08:45 |
| `./mvp/mvp check` | `BE_MVP_CHECK: PASS`: `BE_MVP_FETCH_SELF_TEST: PASS cases=48`, `BE_MVP_SNAPSHOT: PASS self-test cases=33`, `BE_MVP_LICENSES: PASS identifiers=2 files=861`, `BE_MVP_QEMU: PASS runs=58 attempts=79 refused=21`, `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=321 rejected=321`, `BE_MVP_CLAIM_LEDGER: PASS checks=10 claims=46 boundary=13`; the evidence bundle's `source_tree=clean` | 19:08:45 to 19:14:08 |
| `./mvp/mvp claim-ledger check` | `PASS checks=10 claims=46 boundary=13` (no pin moves) | 19:14:08 |
| `./mvp/mvp evaluate` (host cache present, so the fetch keeps every file) | `fetch PASS rpms=259 sources=fedora:116,updates:143` (the host cache's recorded origins); `BE_MVP_IMAGE_IDENTITY: PASS images=253 same=253 differing=0`; `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655` (the image unchanged: same closure, same Containerfile) | 19:14:08 to 19:19:07 |
| `fetch-closure.py --cache <scratch>` with `MVP_RPM_CACHE` unset (the sweep's own acceptance test) | `source fedora-repositories: fetched 240 of 259`; `source updates-archive: fetched 19 of 19`; `BE_MVP_FETCH: PASS rpms=259 bytes=385621571 sources=fedora:116,updates:124,updates-archive:19`; `SOURCES.tsv` retained as `build/mvp/sweep5-gates/public-fetch.sources.tsv`, the RPMs deleted | 19:19:07 to 19:19:24 |
| `git diff --check` | clean | 19:19:24 |

Before the commits: `fetch-closure.py --self-test` (`cases=48`; the two
mutations refused), the cache-less public fetch into a scratch directory
(19:06:20 to 19:06:44 UTC, `sources=fedora:116,updates:124,updates-archive:19`;
log and `SOURCES.tsv` under `build/mvp/tmp/`), `make -C mvp
snapshot-check` (`cases=33`), `node scripts/check-doc-sources.mjs`, `git
diff --check`; and the read-only probe of 2026-11-01 (about 500 `HEAD`
requests over the 259 NEVRAs against the archive and the release
repository; one download compared with the pin).

## 7. Recommended human review sequence

```sh
git worktree add --detach /tmp/be-debt-5 e8ab73b712a974dc25d6cd8eab9bad24bd129405
cd /tmp/be-debt-5
git log --oneline 486fd5a9..HEAD
git show 41c872b6 -- mvp/tools/evaluator/fetch-closure.py
python3 -B mvp/tools/evaluator/fetch-closure.py --self-test
git show e8ab73b7 -- mvp/tools/snapshot-readme.md mvp/docs/guide.md
```

1. `fetch_sources` and `Package.archive_url` (the policy, ten lines).
2. `https_source` (koji's path, now shared; nothing else about koji
   changes).
3. The self-test's `https_cases` and the URL cases.
4. The snapshot README template's paragraph, which a third party reads.
5. Optionally, the decisive test yourself (385 MB download, under a
   minute on this network): `env -u MVP_RPM_CACHE python3 -B
   mvp/tools/evaluator/fetch-closure.py --cache /tmp/be-debt-5-rpms`,
   then `rm -rf /tmp/be-debt-5-rpms`.

## 8. Human decision checklist

- [ ] The sweep stays within `do A`: the archive as a source, the
      documents corrected, nothing else.
- [ ] The archive is acceptable as a source (same footing as the
      repositories and koji; the SHA-256 admission unchanged).
- [ ] The M0-B reading ("one of Fedora's repositories") is accepted, or a
      plan erratum is directed.
- [ ] The snapshot README's new paragraph says what a third party should
      be told.
- [ ] Item 106 (Fedora 44's end of life) is the residual you expect.
- [ ] Exact commit `e8ab73b7` is accepted, revisions are requested, or the
      review is deferred.

## 9. After the decision

- **Accept:** an acceptance record names `e8ab73b7` and the date; on your
  instruction the development branch is fast-forwarded to it and pushed
  with the sweep's branch, and the public snapshot can be re-refreshed
  from the acceptance record (one instruction: `re-refresh`), so that its
  README stops telling third parties the closure needs a cache; the
  public push stays yours.
- **Request revisions:** a new commit and a new packet; `e8ab73b7` is not
  treated as accepted.
- **Defer:** the branch stays local and unmerged.

**Status:** debt sweep 5 is implemented at exact commit `e8ab73b7` on
branch `beryllium/mvp-debt-5`, gates passed from a clean tree, and
**responsible-human accepted as of 2026-11-01** (`accept  & ff + push ,
and  re-refresh`); the development branch is fast-forwarded to the commit
recording the decision and pushed with the sweep's branch to the private
`origin`, and the human's snapshot clone is re-refreshed from the
acceptance record, on the same instruction.
**Next:** your push of the re-refreshed public review snapshot (`git push
origin main` from your local clone, a fast-forward of the public `main`
from `6c71fa4c`); your decision on Plan revision S3-C's second candidate
`27d2e557`; item 106 when Fedora 44 nears its end of life.
**Action required from you:** none on this commit.
