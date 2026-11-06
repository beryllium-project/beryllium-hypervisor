<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Accepted-tool fixes review and acceptance record

This record presents fixes to defects in accepted test tools: the two
latent defects B4 found, the similar defects an audit then found, unit
tests for them, and the acceptance-pin refresh the fixes require. It also
records the responsible human's decision on them.

## Decision record

The responsible human accepted exact commit
`c60896e35cb2ddb8d8662c973aa46d4b5d0d8ef2` (parent
`4aed7e10cb70ed1fac354b8221223df17272c5e5`) as the corrected accepted tools
and their acceptance-pin refresh on 2026-10-07. The instruction was
`accept`, given in reply to this packet's request to accept, revise, or
defer that exact commit, the only target then awaiting a decision.

- **Scope:** acceptance covers exactly that commit and the claim boundary in
  section 3. Everything after section 1 is the packet as presented; the
  decision is recorded only here.
- **Accepted predecessors:** R3 `6fb65b28`, R4 `0783dfc6`, R5 `165f4d00`,
  R6 `7ba3649f`, R7 `9bf22913`, and B4 `135b1d3a` stay accepted at their
  exact targets, with their results unchanged; none is re-accepted. Their
  accepted tool bytes remain the evidence for those results. The corrected
  tools, bound by the refreshed pins, are the maintained versions from this
  commit on.
- **Decision support:** packet commit
  `1fe24ec29529bb8314b04ded3d1c1f2bc2811b9a` and this acceptance-record
  follow-up are decision support, not implementation.
- **Successor:** acceptance starts no successor, and none is authorized.
  Each of these needs separate direction:
  - running the pinned-OCI full gates with the corrected tools;
  - fixing the audit's open findings S5-S8 and S10;
  - R8 pin refresh;
  - a first real guest on K3;
  - development-kernel/BSP selection;
  - root `Makefile`/`be`/`scripts/check-be.sh` integration.

  KVM0 and K0-SC1-B remain parked.
- **Evidence status:** acceptance adds no hardware validation and no
  formal-verification claim, and the pinned-OCI full gates remain not run.
  It does not push, tag, publish, or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `c60896e35cb2ddb8d8662c973aa46d4b5d0d8ef2`, parent `4aed7e10cb70ed1fac354b8221223df17272c5e5`, branch `beryllium/accepted-tool-fixes`. Comparison base: the B4 acceptance record `afa4c00f8f6888408153eb2e0fd0983791b400da`. |
| Current status | Implemented and committed in five commits. At the exact commit, in a fresh clone, 187 unit cases, the R1-R5 acceptance checks, the R3/R4/R5 negative self-tests, and the B4 gate pass. Responsible-human accepted on 2026-10-07 (instruction `accept`). |
| Decision requested | Accept exact commit `c60896e3` as the corrected accepted tools and their pin refresh, request revisions, or defer. Recorded outcome: accepted. |
| Successor status | Not started and not authorized: a first real guest on K3, development-kernel/BSP selection, root integration, R8 pin refresh, and the audit's unfixed latent findings. KVM0 remains parked. |
| Publication status | Private repository. `beryllium/accepted-tool-fixes` and `beryllium/k3-b4-bringup` are local and unpushed. No tag, publication, or release. |

As presented, the packet asked the human to decide whether exact commit
`c60896e3` is accepted. The [decision record](#decision-record) above
holds that decision.

## 2. Deliverables

The request, on 2026-10-07 after `what are the b4 bugs?`, was `fix these
bugs, add unit tests for them and then look for any similar issues in the
code`. Four workers ran in parallel: the R7 extractor fix, the R5 checker
fix, a read-only audit for similar defects, and a read-only map of the
acceptance pins the fixes would break. After reading the audit and the
map, the responsible human chose to:

- fix the audit's real findings, S1-S4, in the R3, R4, and R5 checkers,
  not only B4's narrow F-1 pair;
- keep R6's tool lock bound, through an exact approved delta;
- make B4 read its accepted inputs from git;
- not run the pinned-OCI full gates.

| Commit | Paths | Purpose and boundary | Key review question |
| --- | --- | --- | --- |
| `94e2a7ce` R7 extractor | `tests/r7/extract-exact-image.mjs`; `tests/unit/test-r7-extract-addresses.mjs` | `hex()` printed every address through `>>> 0`, keeping only 32 bits. It now prints any non-negative safe integer exactly and refuses anything else. A section end or allocated total above 2^53 - 1 is refused | Is the output below 2^32 unchanged? |
| `d7f26d8c` B4 inputs | `bringup/k3-b4/r6/scripts/derive.py`, `bringup/k3-b4/r7/scripts/port-r7.py`, three B4 READMEs | B4 pinned its accepted inputs to `git show` digests but read them from the working tree, so any accepted-tool fix broke its gate. It now reads 85 of 91 R6 pins and all 15 copied R7 inputs from their accepted commits. This changes accepted B4 bytes; its pins, rules, and outputs are unchanged | Is changing accepted B4 bytes acceptable for this? |
| `f6cb72fb` image checkers | `tests/r3/check-image.mjs`, `tests/r4/check-image.mjs`, `tests/r5/check-image.mjs`; `tests/unit/` | One 164-line decoder block, byte-identical in the three checkers, derives symbol references, CSR writes, and jumps from the instruction words instead of objdump's annotations. The rules read its results | Is the decoder correct, and is no rule weaker? |
| `4aed7e10` pin refresh | `tests/r3/`, `tests/r4/`, and `tests/r5/check-accepted-content.mjs`; `tests/r6/check-accepted-content.mjs`; `tests/r6/tool-lock.conf` | Moves each changed checker from its stage's immutable list to an exact approved delta, refreshes `R6_IMAGE_CHECKER_SHA256`, and binds the changed R6 lock through a new approved-delta mechanism | Is this exactly the set of constants the change requires? |
| `c60896e3` status | `planning/HANDOFF.md`, `planning/roadmap.md`, `.github/copilot-instructions.md` | Not-reviewed status and the unit-test commands | Are the claims bounded? |

`tests/unit/Makefile` runs the six suites: `make -C tests/unit check`, or
`decoder-check`, `r5-check`, `r4-check`, `r3-check`, `mutation-check`, and
`r7-check`. The suites need the RISC-V cross GCC and binutils, keep their
scratch under `build/`, and take about 3 minutes. They are not wired into
root `make check`, because that would move the R7-A root pins.

No production source changes: `include/`, `virt/`, `arch/`, the root
`Makefile`, `be`, `scripts/check-be.sh`, `tests/r8/`, and B0-B3 are
untouched. The changed accepted bytes are test tools and B4's two
derivation scripts.

| Accepted tool | Accepted SHA-256 | Corrected SHA-256 |
| --- | --- | --- |
| `tests/r3/check-image.mjs` (R3 `6fb65b28`) | `f5ff4012…` | `b8d3c69f…` |
| `tests/r4/check-image.mjs` (R4 `0783dfc6`) | `3fab4777…` | `46bd59bb…` |
| `tests/r5/check-image.mjs` (R5 `165f4d00`) | `b53830dd…` | `07486454…` |
| `tests/r7/extract-exact-image.mjs` (R7 `9bf22913`) | `f4483e15…` | `1dff5f0e…` |

## 3. Claim boundary

**Supported by the exact commit:**

- **R7 extractor:**
  - It prints addresses at and above 2^32 exactly. On B2's K3 images, for
    example, `0x102006aa0` no longer prints as `0x02006aa0`.
  - Its output is byte-identical to the accepted extractor's for the
    accepted R5 QEMU images rebuilt on this host. Their allocated-image
    digests equal the accepted `Exact.v` pins.
  - On B2's K3 images, its output is byte-identical to the output of
    B4's K3 copy.
- **Image checkers:** S1-S4 and F-1 are closed (section 5).
  - **Accepted QEMU images:** on the R3, R4, and R5 GCC and Clang images
    rebuilt with the accepted recipes, the corrected and accepted checkers
    give identical status, stdout, and stderr. That covers 9 runs,
    including the 3 parity checks.
  - **R6 QEMU fixtures:** the 44 fixture images retained from the
    2026-09-30 pinned-OCI R6 run were replayed.
    - The accepted checker reproduces the retained results on all 44
      (status, `Error:` lines, and output).
    - The corrected checker gives the accepted checker's status, `Error:`
      lines, and byte-identical output on all 44. So R6's declared L6
      dispositions and L7 parity inputs are unchanged.
  - **K3:** K3 copies of the corrected checker were made with B4's rules,
    without its F-1 rule. On B4's 44 fixture images and B2's 2 images, they
    give B4's accepted outcomes on all 46. The accepted rules alone differ
    on one image, D-10 GCC: the F-1 false reject, which now passes.
  - **Decoder:** it agrees with objdump on all 514,553 instructions of
    those 52 listings.
  - **Newly visible references:** `be_r5_control` (QEMU R5 GCC),
    `marker_management_verified` (K3 D-10 GCC), and
    `switch_domain.publish_trips` (K3 D-13 Clang). No exact-name annotation
    objdump prints is lost.
- **Pins:** at the exact commit, the R1-R5 `--require` checks report
  accepted at their unchanged accepted targets, and R6 reports accepted
  content and status. `./be status` passes. The R3/R4/R5 negative
  self-tests pass, and tampering with the R6 lock fails closed (section 6).
- **B4:** it derives from the accepted bytes. Its gate passes at the exact
  commit with the accepted summary digests and R7 counts (section 6).

**Trusted or assumed:**

- **Tools:** this workstation's unpinned tools: node v22.23.1, GCC
  16.2.1, binutils 2.46.1, and clang/lld 22.1.8. The accepted tool locks
  pin node v22.22.2, GCC 16.1.1, and binutils 2.46. The R6 replay used the
  retained OCI listings, with this host's `readelf` and `nm`.
- **objdump 2.46.1:** the audit's probes of when objdump annotates a
  reference.
- **Retained R6 build:** the 2026-09-30 fixture products under
  `build/r6/` in the main checkout. They are not committed, but the
  accepted checker reproduces their recorded results.
- **Decoder reach:**
  - It sees addresses formed from `auipc`, `lui`, or `c.lui` plus
    immediates, within a function.
  - It does not see addresses loaded from memory or formed by other
    arithmetic. The accepted checkers did not see those either.
  - A jump-table target sees only its fall-through state.
  - A target that another function also reaches starts with no known
    base.

**Not run or unavailable:**

- **Pinned-OCI full gates:** not run, by your decision: `./be r3-check`,
  `r4-check`, `r5-check`, `r6-check`, `r7-check`, and root `make check`.
  So no R3-R7 report or evidence bundle has been regenerated with the
  corrected tools.
  - In a fresh clone, R6 `--require` fails because no canonical R6
    report exists there. It fails the same way at the base.
  - In the main checkout, which keeps stale R6 reports, it passes.
- **`scripts/check-be.sh`:** fails on this host's node digest drift, as
  at the base.
- **R8:** `tests/r8` is untouched. Its inventory and sources checks fail
  at the base and at the target. The inventory drift grows from 3 to 10
  entries: the 3 image checkers, the R5 and R6 accepted-content checkers,
  `tests/r6/tool-lock.conf`, and the R7 extractor. R8 pin refresh is not
  authorized.
- **Hardware:** NOT RUN. Nothing ran on the board.

**Explicitly not implemented or claimed:**

- **Accepted results:** no accepted image or result changes, and R3-R7
  stay accepted at their exact targets. This is not a re-acceptance of
  R3-R7 or B4.
- **Audit findings left open:** S5-S8 and S10 are not fixed; section 5
  explains each.
- **Not claimed:** formal verification, hardware validation, R8 changes,
  or root integration.

## 4. Load-bearing invariants

| Property | Contract and implementation | Test or evidence |
| --- | --- | --- |
| Accepted outcomes unchanged | Corrected tools give the accepted tools' results on every accepted input | QEMU images: 9 of 9 runs identical. R6 fixtures: 44 of 44. Extractor: byte-identical on the accepted R5 images. B4 gate: same digests |
| Exact 64-bit formatting | `hex()` refuses anything that is not a non-negative safe integer | `r7-check`: 15 tests at 0, `0xffffffff`, `0x100000000`, `0x102006aa0`, and 2^53 - 1, and each refusal. 9 of them fail against the accepted extractor |
| Decoder fidelity | One decoder of RV64IMAC, Zicsr, Zifencei, the privileged and H forms, and RVC | `decoder-check`: 54 cases on a 162-instruction probe at K3 and QEMU addresses. 514,553 instructions agree with objdump |
| Blind spots closed | References, CSR writes, and jumps come from the words | `r5-check` 50, `r4-check` 25, `r3-check` 12 cases. Each also runs the accepted checker as a control, which misses each false accept and fails each false reject |
| The tests can fail | Deliberate breakage of the decoder, tracker, and rules | `mutation-check`: 27 breakages, each caught (31 cases) |
| Exact pin refresh | Only the enumerated constants change, computed from the final bytes with the checkers' own formula | R1-R5 acceptance and R6 content pass. The R3/R4/R5 negative self-tests pass |
| R6 lock binding fails closed | The lock leaves R6's immutable set only for one exact target-to-current delta and its accepted mode | An extra byte, the accepted digest restored, another key edited, the accepted bytes restored, mode 755, or deletion: each is refused |
| B4 independence | B4 reads accepted inputs from their accepted commits | B4 gate at the exact commit: the same summary digests and counts |

## 5. Review history and resolved findings

The scope-review, iterative-evaluation, and deep security-review SOPs are
dropped for this repository; no independent review ran. Every worker used
the pinned model.

1. **R7 extractor truncation (B4 finding; fixed in `94e2a7ce`).** The
   worker also found two adjacent precision limits: an end address and
   the allocated total summed as Numbers above 2^53 - 1. Both are now
   refused. The defect failed safe, because the objdump cross-check and
   the Rocq pins refuse truncated values.
2. **R6 F-1 (B4 finding; fixed in general in `f6cb72fb`).** A narrow
   adjacent-pair rule (`14efd819`, on a worker branch) was superseded
   before integration, because the audit showed more blind forms (S9).
3. **S1: R5 rules relied on objdump annotations (fixed).** objdump
   annotates only the first use of an `auipc` or `lui` base, and never a
   `mv` or `sext.w` form. Every annotation-based R5 rule now reads decoded
   references, as do R4's hidden-R5-path scan and dispatch call and R3's
   ordered calls. The root-pool rules also match formed addresses.
   - Before the fix, a blind form could hide an extra marker, root-pool
     reference, SBI issue point, or caller (a false accept). It could also
     hide a required reference (a false reject).
   - On an accepted input, this changes only the K3 D-10 GCC outcome.
4. **S3: CSR writes matched only `csrw`/`csrs` (fixed).** A one-line
   listing edit showed `csrrw`, `csrs`, `csrc`, and `csrwi` writes of
   `hgatp` passing. CSR writes are now decoded in every spelling, by name
   or number, in R3, R4, and R5. `hlv` and `hsv` are not counted as CSR
   accesses.
5. **S4: `callFree()` let `j`, branches, and unannotated `jr` leave
   (fixed).** Every jump and branch must now stay in the function or reach
   an allowed target, and a register jump must resolve. `ret` counts as a
   return only in a function that never writes `ra`.
6. **S2: R3/R4 `block()` assumed 32-bit headers (fixed).** On K3
   listings every block ran to the end of the listing. It now ends at the
   next header of any width.
7. **Left open (latent, low, or cosmetic; no outcome affected today).**
   Each is in a file this change does not touch:
   - S5: R6's D-13 and S-08 construction guards count call sites by
     annotation.
   - S6: R3's QEMU trace checks match the `sret` word as an unanchored
     substring, which could collide with K3 addresses. R3's runner is not
     used on K3.
   - S7: R4's post-entry trace check matches only one `csrw hgatp`
     encoding and one `hfence.gvma` encoding.
   - S8: R5 and R6 exit and guest-entry labels keep only the low 32 bits.
     The full values are compared separately.
   - S10: B1/B2 port guards recognize only bare 8-digit QEMU literals.
     This is theoretical.

   S9, the narrowness of B4's F-1 rule, is superseded by the general
   fix; B4 keeps its accepted rule.
8. **Pin web (resolved by your choices):**
   - B4 read its pinned inputs from the working tree; it now reads them
     from git (`d7f26d8c`).
   - R6 bound its lock as immutable content; a new approved delta now
     binds it.
   - R8 is left untouched, and its drift is recorded.
9. **Process findings:**
   - **Worker loss:** the first R5 worker stopped during a network outage
     mid-fix. A fresh worker reviewed its partial diff before completing
     it.
   - **Coverage gap:** integration found that the workers' evidence did
     not cover R6's QEMU fixture images, and replayed them (44 of 44).
   - **First candidate superseded:** validating `4dbab999` showed that
     the new R6 mechanism threw an uncaught `ENOENT` for a deleted lock.
     It still exited 1. A clean refusal was folded into `4aed7e10`, so
     `4dbab999` is superseded and was never presented.
   - **Makefile comment:** the merged unit-test Makefile comment was
     corrected before commit.

Open for your judgment:

- whether S5-S8 and S10 need fixing;
- whether the pinned-OCI full gates must run before or after acceptance;
- the R8 drift.

## 6. Validation and retained evidence

**At the exact commit**, in a fresh clone with no changes before or after
(2026-10-07T12:18:52Z to 12:40:20Z):

- `make -C tests/unit check`: decoder 54, R5 50, R4 25, R3 12, mutation
  31, and R7 15; 187 cases, all PASS.
- Host checks:
  - R1-R5 `--require`, the R3/R4/R5 accepted-content checks, R6
    accepted content and status, R6 `check-baseline.sh`, `loadToolLock`,
    and R6 and R7 `check-sources`: all PASS. Path counts (immutable,
    approved delta) are R3 37 and 10, R4 34 and 8 plus 3 added files, and
    R5 42 and 7;
  - the R3/R4/R5 negative self-tests, `./be status`, the documentation
    source check, and the source policy: all PASS.
  - Four fail exactly as at the base in a fresh clone: R6 `--require`
    (no R6 report), R8 inventory and sources, and `scripts/check-be.sh`.
- `make -C bringup/k3-b4 check`: PASS in 861 s. It cloned and
  built OpenSBI v1.6 itself.
  - R6: `BE_K3_B4_R6_CHECK: PASS matched=47/47 images=32 qemu_runs=64
    layer_shifts=0 findings=0`, with the accepted B4 summary digests
    (`5c6aeb95…`, `26a6400f…`).
  - R7: `proof=PASS` with totals of 22 symbols, 1,420 words, 144 targets,
    32 sections, 9 modules, 135 Theorem and 4 Lemma declarations.
- R6 lock binding: the clean lock passes, and each of the six tampering
  cases in section 4 is refused with `BE_R6:FAIL`.

**At the exact commit in the main checkout:**

- The R6 fixture replay gave 44 of 44 controls reproduced and 44 of 44
  identical.
- The host checks give the same results, with R6 `--require` passing
  against the retained R6 reports.

**On identical bytes before integration:**

- The workers' runs at `f1f6eee5`, whose checker bytes are identical to
  the target's, and at `d5923638`, whose extractor is identical, supply:
  - the QEMU image comparison;
  - the K3 regression over 46 images;
  - the 514,553-instruction cross-check;
  - the extractor byte-identity results.
- The superseded candidate `4dbab999` differs from the target only in
  the R6 missing-path message and one HANDOFF reference. Its fresh-clone
  unit tests, host checks, and B4 gate (1,053 s, the same digests) gave
  the same results.

**Retained:** nothing beyond the unit tests is committed. Every result
regenerates: the unit tests build their own images, and the replay needs
the R6 build products of a full R6 run.

## 7. Recommended review sequence

1. Claims: section 3 above, then the HANDOFF status entry.
2. R7 extractor: `94e2a7ce`.
3. The decoder block and the rules that use it: the R5 diff first, then
   R4 and R3.
4. Unit tests: `tests/unit/image-check-harness.mjs`, then the suites.
5. Pin refresh: `4aed7e10`, including the new R6 mechanism.
6. B4: `d7f26d8c`.
7. Run the unit tests, acceptance checks, and B4 gate on the exact commit.

Read-only commands:

```sh
git --no-pager log --oneline afa4c00f..c60896e3
git --no-pager diff --stat afa4c00f..c60896e3
git --no-pager show 94e2a7ce -- tests/r7/extract-exact-image.mjs
git --no-pager diff afa4c00f c60896e3 -- tests/r5/check-image.mjs
git --no-pager show 4aed7e10
git --no-pager show d7f26d8c -- bringup/k3-b4/r6/scripts/derive.py
for r in r3 r4 r5; do
    git show c60896e3:tests/$r/check-image.mjs |
        sed -n '/^\/\/ -* references from the words$/,/insn\.csr === csr && insn\.csrWrite)$/p' |
        sha256sum
done
```

The loop prints the same digest three times, `a1572a0b…`.

Exact-commit execution. In a fresh worktree, B2 clones and builds OpenSBI
v1.6, which needs network access. The B4 gate takes about 20 minutes, and
its traced R6 runs write and then delete about 43 GB:

```sh
git worktree add --detach /tmp/be-atf-review c60896e35cb2ddb8d8662c973aa46d4b5d0d8ef2
cd /tmp/be-atf-review
make -C tests/unit check
bash tests/r5/check-acceptance.sh --require
node tests/r6/check-accepted-content.mjs
./be status
make -C bringup/k3-b4 check
cd - && git worktree remove --force /tmp/be-atf-review
```

## 8. Human decision checklist

The checklist is kept as presented. The decision is recorded in the
[decision record](#decision-record), not in these boxes.

- [ ] The change matches the request: B4's two bugs fixed in the
      accepted tools, unit tests, and similar issues found and fixed as
      you scoped them.
- [ ] The shared decoder and the rules that use it are correct, and no
      accepted rule is weaker.
- [ ] The pin refresh is exactly the required set, and the new R6
      approved-delta mechanism is acceptable.
- [ ] Changing accepted B4 bytes so that B4 reads from git is
      acceptable.
- [ ] The claims in section 3 match the evidence, and unpinned host
      tools without the pinned-OCI full gates are acceptable.
- [ ] Leaving S5-S8, S10, and the R8 drift for later is acceptable.
- [ ] Successor work remains excluded until separately directed.
- [ ] Decision: accept exact commit `c60896e3`, request revisions, or
      defer.

## 9. After the decision

- **Accept:** record acceptance of exact SHA
  `c60896e35cb2ddb8d8662c973aa46d4b5d0d8ef2` with its date and instruction
  in a follow-up record. Running the pinned-OCI full gates, refreshing R8,
  fixing S5-S8 or S10, pushing, and any successor each still need your
  direction.
- **Request revisions:** make a new commit and a new packet. `c60896e3` is
  not treated as accepted.
- **Defer:** keep the current status. The accepted tools at their accepted
  commits stay authoritative, and no dependent work starts.

**Status:** exact commit `c60896e3` is responsible-human accepted as of
2026-10-07. Its corrected tools give the accepted results on every
accepted input tested, and the B4 gate still passes.

**Next:** a successor needs your direction. Candidates include running
the pinned-OCI full gates with the corrected tools, and a first real
guest on K3 under a new bounded plan, which would need guest SBI services
and guest image loading. None is started or authorized.

**Action required from you:** none for these fixes.
