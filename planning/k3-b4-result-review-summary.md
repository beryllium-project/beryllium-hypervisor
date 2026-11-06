<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B4 result review and acceptance record

This record presents the result of B4: the accepted R6 adversarial
catalogue and the accepted R7 bounded exact-byte proof, each re-derived
for the K3 port and images that B2 builds. It also records the responsible
human's decision on it.

## Decision record

The responsible human accepted exact commit
`135b1d3ae4def25691472bba0fa0179aa509d532` (parent
`50dd09172fde8bfb8c8246294faa89671d3e23f0`) as the B4 result on
2026-10-07. The instruction, given in reply to this packet's request to
accept, revise, or defer that exact commit, was `accept 135b1d3a`. The
abbreviation `135b1d3a` was checked to resolve uniquely to that commit.

- **Scope:** acceptance covers exactly that commit and the claim boundary in
  section 3. Everything after section 1 is the packet as presented; the
  decision is recorded only here.
- **Decision support:** packet commit
  `1d775d7c7e3bcf757f811ac92d14fadbe765ff02` and this acceptance-record
  follow-up are decision support, not implementation.
- **Successor:** acceptance starts no successor, and none is authorized.
  Each of these needs separate direction:
  - a first real guest on K3;
  - development-kernel/BSP selection;
  - root `Makefile`/`be`/`scripts/check-be.sh` integration;
  - any fix to the accepted R7 extractor or R5 image checker.

  KVM0 and K0-SC1-B remain parked.
- **Evidence status:** acceptance adds no hardware validation and no
  formal-verification claim. It does not push, tag, publish, or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `135b1d3ae4def25691472bba0fa0179aa509d532`, parent `50dd09172fde8bfb8c8246294faa89671d3e23f0`, branch `beryllium/k3-b4-bringup`. Comparison base: the B3 acceptance record `dabf817db25cc5f3481c91e5a9cbcc1f9026e54a`. |
| Current status | Implemented and committed. R6 half: all 47 accepted catalogue entries match on the K3 port (32 images, 64 traced QEMU runs, 0 layer shifts). R7 half: `proof=PASS` over both K3 images, with accepted R7's counts. The B4 gate passes at the exact commit in a clean detached worktree. Responsible-human accepted on 2026-10-07 (instruction `accept 135b1d3a`). |
| Decision requested | Accept exact commit `135b1d3a` as the B4 result, request revisions, or defer. Recorded outcome: accepted. |
| Successor status | Not started and not authorized. That covers a first real guest on K3, development-kernel/BSP selection, root integration, and any fix to the accepted R7 extractor or R5 image checker. KVM0 remains parked. |
| Publication status | Private repository. `beryllium/k3-b4-bringup` and the two worker branches are local and unpushed. No tag, publication, or release. |

As presented, the packet asked the human to decide whether exact commit
`135b1d3a` is accepted as the B4 result. The
[decision record](#decision-record) above holds that decision.

## 2. Deliverables

B4 was authorized on 2026-10-06 by `ok, as I will be asleep soon, let's go
with R6 and R7 overnight, in parallel if feasible`. Two workers built the
halves in parallel, in separate worktrees, on branches
`beryllium/k3-b4-r6-wip` (tip `61e6b722`) and `beryllium/k3-b4-r7-wip`
(tip `c00176d1`). Each half is squashed into one commit on top of the B3
acceptance record:

- `3121561d`: the R7 half, `bringup/k3-b4/r7/`;
- `50dd0917`: the R6 half, `bringup/k3-b4/r6/`;
- `135b1d3a`: the B4 Makefile and README, and the status documents.

Outside `bringup/k3-b4/`, only `planning/HANDOFF.md`,
`planning/roadmap.md`, and `.github/copilot-instructions.md` change. No
accepted byte changes: `tests/`, `include/`, `virt/`, `arch/`, and B0-B3
are untouched.

| Deliverable | Paths | Purpose and boundary | Key review question |
| --- | --- | --- | --- |
| R7 half | `bringup/k3-b4/r7/`: `Makefile`, `scripts/port-r7.py`, `scripts/report.py`, `tests/check-images.py`, `tests/check-negative.py`, `README.md` | Copies accepted R7's tooling and proof (`tests/r7` at `9bf22913`) and the R1/R2 report tools, pinned by SHA-256, with 59 counted rules. Re-runs extraction, the objdump cross-check, double generation, the Rocq build, and `rocq check` over B2's images | Are the proof-source changes constant-only, and is the K3 cut-point ledger complete? |
| R6 half | `bringup/k3-b4/r6/`: `Makefile`, `scripts/derive.py`, `tests/check-r6-k3.py`, `tests/run-qemu.sh`, `README.md` | Pins 90 accepted inputs. Runs every accepted R6 fixture at its declared layer on the K3 port, using K3 copies of the accepted checkers and the accepted QEMU tracing | Are the checker-copy rules (address rebases, the F-2 `sret` rule, the F-1 pair rule) narrow and justified? |
| Integration | `bringup/k3-b4/Makefile`, `bringup/k3-b4/README.md` | Runs R6, then R7, never at once (both build B2's port). Summary, shared method, findings, claims | Is the summary exactly bounded? |
| Status | `planning/HANDOFF.md`, `planning/roadmap.md`, `.github/copilot-instructions.md` | B4 authorization and status | Are the claims exactly bounded? |

Both halves use this workstation's unpinned tools, as B2 does. The accepted
R6/R7 tool locks pin node v22.22.2, GCC 16.1.1, and binutils 2.46; this
host has node v22.23.1, GCC 16.2.1, and binutils 2.46.1. Rocq 9.2 matches
accepted R7's digest. No accepted launcher, tool lock, evidence bundle, or
acceptance-pin checker runs.

## 3. Claim boundary

**Supported by the exact commit:**

- **Inputs:**
  - accepted R6 `7ba3649f` and R7 `9bf22913`;
  - accepted R5 `165f4d00`, through B2's port (accepted at `898af4e0`);
  - B2's images, GCC `9c145f00…a08c79` and Clang `47be17e3…c54fe`. These
    are the same images that ran on the COM260 in B2 and B3.
- **R6 half:** each of the 46 single-defect fixtures is detected on the K3
  port at its declared layer, with its declared class and last marker. The
  control reproduces B2's 22 markers.
  - **Static (14):** 4 rejected at source inventory (L3), 4 at link (L5),
    6 at image check (L6), on both toolchains.
  - **Host (17):** 18 class outcomes and 1,063 assertions, with identical
    GCC and Clang result streams.
  - **Dynamic (15, plus the control):**
    - Each of the 32 images reaches its declared L6 disposition and passes
      a single-delta differential.
    - Each image runs twice under QEMU, 64 runs in all. Each fails closed
      with its declared class and last marker, an allowlisted SRST, and
      QEMU status 0.
    - Under the accepted `-d in_asm,cpu,int` tracing, VS entries, guest
      exits, `hstatus`, `htval`, and final registers equal the accepted
      values. Root installs differ only by B2's hgatp rebase.
- **R7 half:** for both K3 images, a bounded Rocq development:
  - consumes the exact linked bytes of the 11 scoped privileged-wrapper
    symbols, cross-checked with GNU objdump;
  - decodes the enumerated subset;
  - checks the entry, trap-frame, root install/fence/readback, restore,
    and return properties;
  - checks generated configuration facts from B2's port against the
    accepted two-domain access matrix.

  The counts equal accepted R7: 22 symbols, 1,420 words, 144 targets, 32
  sections, and 9 modules with 135 Theorem and 4 Lemma declarations. The
  claims theorem has closed assumptions, and every compiled module passes
  `rocq check`.

**Trusted or assumed:**

- **Dynamic platform:** QEMU 10.2.2's K3-like virt machine (H extension,
  Sstc, AIA) with OpenSBI v1.6. It is not K3 hardware, and it is not the
  accepted minimal R5 CPU profile.
- **Tools:** this workstation's unpinned tools, as listed in section 2,
  plus clang/ld.lld 22.1.8 and Python 3.14.7.
- **Copies:** B2's port and the K3 copies of accepted checkers and
  tooling, with their counted rules. Each half's README lists every rule.
- **R7 cut points:**
  - the C implementation;
  - `be_reset`, its call to `be_b1_quiesce`, and B1's 96 bytes of quiesce
    code, including its own `sret`;
  - the ELF parser, and the compiler and linker outside the scoped
    symbols;
  - the connection from C state to the configuration facts.

**Not run or unavailable:**

- **Hardware:** NOT RUN. B4 ran nothing on the board.
- **Accepted machinery:** the R6/R7 tool locks, launchers, report and
  evidence-bundle machinery, and acceptance-pin checkers.
- **R6 trace dump count:** recorded, not compared, as in accepted R6.

**Explicitly not implemented or claimed:**

- **Accepted tools:** B4 changes no accepted R5/R6/R7 checker or tool. The
  two latent defects in section 5 are fixed only in the K3 copies.
- **Not claimed:** formal verification of Beryllium, C refinement,
  whole-ELF coverage, hardware validation, any board claim, or a
  re-acceptance of R6 or R7.

## 4. Load-bearing invariants

| Property | Contract and implementation | Test or evidence |
| --- | --- | --- |
| Accepted-input fidelity | Every consumed accepted file is pinned by SHA-256 against `git show`, and copies change only by counted rules | `derive.py` (90 pins) and `port-r7.py` (15 copied inputs, 17 pins, 59 rules), each with refusal self-tests |
| Image identity | Only B2's images; B2's accepted flat-image hashes are required | R7 `check-images.py`; R6 requires the C-01 images to be byte-identical to B2's |
| Single-defect fixtures | Each fixture tree is the control tree plus exactly one changed file; each mutation must apply with its exact count | `derive.py` hunk checks; the L8 single-delta differential |
| No success-shaped bypass | The R6 gate exits 0 only when every entry and count matches, and has no override. R7's `proof=` comes only from the proof outputs | R6: 124 self-test cases, covering layer shifts, wrong classes, missing markers, and unexpected deltas. R7: 12 negative cases with 16 refusals |
| Determinism | R7 generates its inputs twice and byte-compares them. The R6 summary is reproducible | R6 `summary.json` `5c6aeb95…` and `summary.txt` `26a6400f…`, identical in the worker's worktree, the main checkout, and the clean validation |
| Proof-source minimality | Five modules are byte-identical. In `Exact.v` and `Configuration.v`, every change is a literal. The 135 Theorem / 4 Lemma inventory and the absence of QEMU-range addresses are enforced | `port-r7.py` guards. With every numeric and hash literal normalized, both files are textually identical to accepted R7 |
| F-1 rule narrowness | Matches only `auipc rd` immediately followed by `addi rd,rd,0`, with the same register and exactly one symbol at the resulting address | Self-tests: the pass case, wrong, non-marker, and unresolvable pairs, and the unmodified checker as a control. It resolves 1 address in 44 images |
| No unfenced execution | Inherited from accepted R6: S-05 is rejected statically, and D-11 withholds only the fence acknowledgement | S-05 at L6; D-11 fails closed with class `fence` |

## 5. Review history and resolved findings

The scope-review, iterative-evaluation, and deep security-review SOPs are
dropped for this repository; no independent review ran. Both workers used
the pinned model. The orchestrator gave each one follow-up, then re-ran
both gates in the main checkout before committing.

1. **R7: the accepted extractor truncates addresses (fixed in the K3
   copy).** It formats addresses with `>>> 0`, which truncates every
   address at or above 2^32, as all K3 addresses are. The objdump
   cross-check and the Rocq pins refuse the truncated values. The copy uses
   an exact formatter, and a negative test keeps the old one as a control.
   Accepted R7 is unaffected, because every QEMU R5 address is below 2^32.
2. **R6 F-1: a blind spot in the accepted image checker (fixed in the K3
   copy).** The first R6 run matched 46 of 47 entries.
   - The accepted R5 image checker finds marker references only through
     objdump's `<symbol>` annotations.
   - D-10's GCC image on the K3 layout forms `marker_management_verified`
     with `auipc` followed by `addi rd,rd,0`. objdump prints that pair as
     `mv` with no annotation.
   - So the checker rejected D-10 at L6, a layer shift.
   - The orchestrator chose the narrow resolution rule over re-deriving
     D-10, and removed a deviation override from the gate.
   - D-10 now passes L6 and fails closed in QEMU with `target-readback`,
     as accepted. On the accepted QEMU layout the same fixture passes L6
     with this host's toolchain, so accepted R6 is unaffected.
3. **R6 L10 parity (restored).** The first R6 run traced only interrupts:
   full tracing writes about 700 MB and takes up to a minute per run. The
   follow-up restored the accepted tracing and the full L10 comparison.
   Each run's raw trace is deleted after extraction, 43 GB per gate run.
4. **R7 root `Makefile` coupling (removed).** The first R7 gate ran the
   accepted R1 acceptance check, which pins the root `Makefile` hash, so
   an unrelated root edit would have broken it. The follow-up reads the
   four provenance keys from pinned inputs as text, so no acceptance-pin
   checker runs. A throwaway clone with a root `Makefile` edit confirmed
   that the B4 trace still passes.
5. **F-2 (closed).** B1's quiesce adds an `sret` that the accepted image
   checker does not expect. One counted K3 rule covers it.
6. **Layout shift (closed).** The quiesce call grows `be_reset`, so the
   scoped symbols move by `+0x81e00010`, not B2's `+0x81e00000`. D-15's
   byte-delta pin is translated with R7's measured addresses and matches
   exactly.
7. **Inherited warning (closed).** The accepted `check-disassembly.sh`
   has a shellcheck SC1007 warning. The R7 gate requires shellcheck to
   report exactly that one finding for the copy.

Open for your judgment: whether to fix findings 1 and 2 in the accepted
tools. That would be a separate, separately authorized change.

## 6. Validation and retained evidence

**At the exact commit**, in a clean detached worktree:

- `make -C bringup/k3-b4 check` passed, from 2026-10-06T23:45:11Z to
  23:59:49Z (878 s). It cloned and built OpenSBI v1.6 (`bd613dd9`)
  itself.
  - B2's port re-derived (32 files, 11 changed), and both B2 images
    rebuilt to their accepted hashes.
  - R6: `BE_K3_B4_R6_CHECK: PASS matched=47/47 images=32 qemu_runs=64
    layer_shifts=0 findings=0`, with the same summary digests
    (`5c6aeb95…`, `26a6400f…`).
  - R7: `proof=PASS` and `BE_B4_R7_CHECK: PASS`, with the same totals.
- The worktree had no changes before or after.

**Before committing**, on the same content in the main checkout:

- `make -C bringup/k3-b4 r7-check` passed in 87 s with `proof=PASS`.
- `make -C bringup/k3-b4 r6-check` passed in 690 s with
  `matched=47/47 images=32 qemu_runs=64 layer_shifts=0`. Its summary
  digests match the R6 worker's.
- The documentation source check and `git diff --check` passed.
- Every changed line of `Exact.v` and `Configuration.v` is a literal: with
  numeric and hash literals normalized, both files equal accepted R7's.

**Worker runs:**

- R7: a clean gate in 151 s at `c00176d1`, and a clean clone at another
  path in 366 s.
- R6: two clean gates in 11 min 27 s and 12 min 37 s, with byte-identical
  summaries.

**Retained:** B4 adds no results directory, because every result
regenerates off-board. Its gates rebuild the R6 summary byte for byte. The
R7 report differs between checkouts only in the ELF hashes, which embed
debug paths. The flat-image hashes and the allocated-image hashes pinned
in Rocq (GCC `ef2b1af6…`, Clang `4dd9a613…`) do not change.

## 7. Recommended review sequence

1. Claims: `bringup/k3-b4/README.md`, then section 3 above.
2. R7: `r7/README.md`, the "Proof-source changes" and "Supportable claim"
   sections.
3. R6: `r6/README.md`, the "Substitutions and mutations", "Why the K3
   detection is equivalent", "Expectations that differ", and F-1 sections.
4. Run the gate on the exact commit.

Read-only commands:

```sh
git --no-pager log --oneline dabf817d..135b1d3a
git --no-pager diff --stat dabf817d..135b1d3a
git --no-pager show 135b1d3a:bringup/k3-b4/README.md
git --no-pager show 50dd0917 --stat
git --no-pager show 3121561d --stat
```

Exact-commit execution. In a fresh worktree, B2 clones and builds OpenSBI
v1.6, which needs network access. The gate takes about 20 minutes, and
R6's traced runs write and then delete about 43 GB:

```sh
git worktree add --detach /tmp/be-b4-review 135b1d3ae4def25691472bba0fa0179aa509d532
cd /tmp/be-b4-review
make -C bringup/k3-b4 check
for f in Exact Configuration; do
    diff -u <(git show 9bf22913:tests/r7/proof/$f.v) \
        build/k3-b4/r7/port/tests/r7/proof/$f.v
done | less
cd - && git worktree remove /tmp/be-b4-review
```

## 8. Human decision checklist

The checklist is kept as presented. The decision is recorded in the
[decision record](#decision-record), not in these boxes.

- [ ] B4 matches the authorized direction: accepted R6 and R7 re-derived
      for the K3 images, off-board.
- [ ] The R7 proof-source changes are constant-only, and the K3 cut-point
      ledger is acceptable.
- [ ] The R6 checker-copy rules are narrow and justified.
- [ ] The claims in section 3 match the evidence, and QEMU's K3-like
      machine is an acceptable dynamic platform.
- [ ] Unpinned tools, without the accepted tool locks, launchers, and
      evidence machinery, are acceptable.
- [ ] Leaving the two latent defects in the accepted tools for a separate
      decision is acceptable.
- [ ] Successor work remains excluded until separately directed.
- [ ] Decision: accept exact commit `135b1d3a`, request revisions, or
      defer.

## 9. After the decision

- **Accept:** record acceptance of exact SHA
  `135b1d3ae4def25691472bba0fa0179aa509d532` with its date and instruction
  in a follow-up record. Any successor still needs your separate
  direction.
- **Request revisions:** make a new commit and a new packet. `135b1d3a` is
  not treated as accepted.
- **Defer:** keep the current status and start no dependent work.

**Status:** exact result commit `135b1d3a` is responsible-human accepted
as of 2026-10-07. On B2's K3 images, accepted R6's catalogue matches 47
of 47 entries, and accepted R7's bounded proof passes with the same
counts.

**Next:** a successor needs your direction. Candidates include a first
real guest on K3 under a new bounded plan, which would need guest SBI
services and guest image loading, and the two accepted-tool fixes in
section 5. None is started or authorized.

**Action required from you:** none for B4.
