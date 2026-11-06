<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R6 review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves the packet-time former private repository identity and remote
> state. The current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

The responsible human accepted exact R6 implementation target
`7ba3649f03cf13b65df33020e345d361cce2993a` on 2026-08-05 by explicit
instruction `Accept exact commit
7ba3649f03cf13b65df33020e345d361cce2993a`.

The accepted target's immediate parent is
`9ed5ad7069b6067f03e1923c09937fe218240a59`; whole-R6 comparison base is
`4012d794e769fd4029b11f6f45e366ed0ef117f5`. Review packet commit
`e0daa12b34ca4e30a601bd435ef038d5bc4088f1` and the later follow-up commit
that records this decision are decision support, not accepted implementation.
Acceptance adds no validation and does not erase any assumption, `NOT RUN`
item, resolved finding, or open reproducibility finding below.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact corrected implementation target `7ba3649f03cf13b65df33020e345d361cce2993a` (`tests: make R6 checks standalone reproducible`), immediate parent and initial implementation `9ed5ad7069b6067f03e1923c09937fe218240a59` (`tests: implement bounded single-hart R6 adversarial images`), whole-R6 comparison base `4012d794e769fd4029b11f6f45e366ed0ef117f5` (`docs: accept R6-B plan`) |
| Current status | R6 implementation work was authorized by the recorded instructions `proceed to implement R6 exact` and `proceed with all r6 implementation work` (2026-07-30) under accepted plan revision R6-B target `6d6464c6c937abccd59df932006c1049fd79fac6`. The package is implemented, locally complete, root-integrated, exact-target validated in two independent fresh detached worktrees, and **responsible-human accepted** at exact target `7ba3649f03cf13b65df33020e345d361cce2993a` on 2026-08-05. |
| Decision recorded | Accepted exact commit `7ba3649f03cf13b65df33020e345d361cce2993a`; review packet commit `e0daa12b34ca4e30a601bd435ef038d5bc4088f1` and this acceptance record are not accepted implementation. |
| Branch | `beryllium/single-hart-runtime-r0`, internal/private, worktree clean at the target |
| Prior accepted boundary | R5 remains accepted only at `165f4d001a2b59b582b397bdea79ec4826168fdb` (implementation parent `9312c1355a23d411e3bdafb2183be342683a8ab9`); R4 only at `0783dfc6557453fbac0da93a5364f2e6e2cb1f52`; R3 only at `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`. R6 changes no accepted mechanism byte of any of them |
| Plan chain | Original plan `609867fdad75279c0913022909efd65c4a838909`, revision R6-A `75269f058ae578b0a76a113d6c05c0aaceeac8ec`, revision R6-B `6d6464c6c937abccd59df932006c1049fd79fac6` (current accepted plan). R6-B packet `325117f4b2d2bac4a864221d3457295f8ff385ab` and acceptance record `4012d794e769fd4029b11f6f45e366ed0ef117f5` are decision support, not implementation |
| Successor status | R7 is **not authorized and not started**. No R7 content exists |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`. The target is local, unpushed, and untagged. Push, tag, public release, and publication remain **blocked**; `pathfinder/publication-gate.conf` is untouched |

The responsible-human decision is recorded above; no successor authorization
or publication permission follows from it.

## 2. Deliverables

R6 implementation spans **two commits**. The whole-R6 range
`4012d794e769fd4029b11f6f45e366ed0ef117f5..7ba3649f03cf13b65df33020e345d361cce2993a`
reports **221 paths, 50,147 insertions, 353 deletions**: 144 non-generated
paths (49,822 insertions, 91 deletions) plus 77 generated planning-site paths
under `docs/html/` (325 insertions, 262 deletions). The corrective parent delta
`9ed5ad7069b6067f03e1923c09937fe218240a59..7ba3649f03cf13b65df33020e345d361cce2993a`
is 94 paths, 678 insertions, 376 deletions: 18 non-generated paths (447
insertions, 145 deletions) plus 76 generated paths. **Review the whole range,
not only that corrective delta.**

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary review question |
| --- | --- | --- | --- | --- |
| Adversarial fixture catalogue and partitions | `tests/r6/catalogue*.mjs`, `tests/r6/handlers.mjs`, `tests/r6/fixtures.json`, `tests/r6/fixtures/**` (47 entries: 14 static, 17 host, 15 dynamic, 1 control) | One declared single defect per entry over a copy of an accepted R5 source, with its declared detection layer, disposition, error class, and last console marker | Test-only inputs to the accepted R5 instrument; no production surface, no accepted byte changed | Is every declared expectation architecturally justified, and is any expectation reachable only because it was relaxed to match what was observed? |
| Detection pipeline and partition drivers | `tests/r6/static.mk`, `host.mk`, `dynamic.mk`, `report.mk`, `Makefile`, `build-fixture.sh`, `overlay-defect.mjs`, `check-static.mjs`, `check-fixtures.mjs`, `check-fixture-image.mjs`, `check-qemu-eligibility.mjs`, `check-dynamic.mjs`, `run-qemu.sh`, `r6-check.c` | Eleven detection layers in real pipeline order; six R6-owned (L1, L2, L8, L9, L10, L11), the rest accepted R5 or pinned-toolchain stages R6 observes but never replaces | R6 owns no privileged code and writes no CSR; QEMU and host execution only | Can a mutated static image ever be promoted or executed, and does a rejection at a layer other than the declared one really fail as `layer-shift`? |
| Harness security boundary | `tests/r6/run-make.sh`, `make-control.mjs`, `run-lock.mjs`, `run-identity.mjs`, `tool-lock.mjs`, `tool-lock.conf`, `check-tools.sh`, `check-tool-identity.mjs`, `prepare-scratch.sh`, `materialize-scratch.mjs`, `check-sources.mjs`, `authority-policy.mjs` | Checked launcher with parse-time Make-control guards, digest-bound tool identity, prepared and inventoried scratch, kernel `flock` invocation lock, source/write-surface guard, hash-only authority policy | Harness only; relaxes no accepted R3 tool-lock identity and adds no accepted-package launch path | Can a hostile Make control, shell override, aliased writer, or substituted executable produce a success banner without running the checks? |
| Report, evidence, and rejection suites | `tests/r6/generate-report.mjs`, `check-report.mjs`, `generate-evidence.sh`, `check-evidence.mjs`, `acceptance-pins.mjs`, `check-acceptance.sh`, `check-baseline.sh`, and the `test-*.mjs` suites | Canonical `be-r6-adversarial-images-v1` report, independently re-checked; exact-set evidence bundle with aggregate `artifacts.sha256`; 1,424 pinned report mutations refused 1,477 times; 43 evidence forgeries refused | Evidence integrity only; the checkers can lower a claim but can never raise one | Does every published number get re-derived by an independent checker, and is any success-shaped mismatch reported rather than refused? |
| Root integration and six authorized pin refreshes | `Makefile`, `be`, `scripts/check-be.sh`, `tests/r1/check-acceptance.sh`, `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs` | `r6-check`, `r6-evidence`, `r6-evidence-verify`, an R6 step in `check`, R6 bundle verification in `evidence-check`, R6 status/help/version fields, and exactly six enumerated predecessor acceptance-pin constants | Orchestration and status reporting cannot create acceptance; predecessor acceptance checkers stay exact-bound through their immutable, approved-delta, and added-file classes | Do the six refreshed pins move only because the root files legitimately changed, and does every predecessor still report `accepted_mechanism_match=yes`? |
| Evidence record and maintained documentation | `planning/single-hart-runtime-r6-evidence.md`, `README.md`, `.github/copilot-instructions.md`, `planning/README.md`, `planning/HANDOFF.md`, `planning/implementation-plan.md`, `planning/roadmap.md`, `planning/single-hart-runtime-r5-evidence.md`, `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs` | Authoritative R6 evidence and claim record, plus status, navigation, and browser-render coverage | Markdown is authoritative; generated HTML is derivative | Do the documents keep implementation completion, local validation, human decision, and blocked publication strictly separate? |
| Generated planning site | 77 paths under `docs/html/` | Render the maintained Markdown | Derivative build output only; byte reproducibility remains an open finding | Are links and static/browser rendering functional without treating unstable hash-named assets as resolved? |

### Exact non-generated inventory of the whole range

`tests/r6/` contributes **128 added files**, all test-only, and is the complete
new-package surface. The remaining 16 non-generated paths are:

```text
.github/copilot-instructions.md
Makefile
README.md
be
pathfinder/tests/check-docs-render.mjs
planning/.vitepress/config.mts
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/roadmap.md
planning/single-hart-runtime-r5-evidence.md
planning/single-hart-runtime-r6-evidence.md
scripts/check-be.sh
tests/r1/check-acceptance.sh
tests/r3/check-accepted-content.mjs
tests/r4/check-accepted-content.mjs
```

There is **no** added or modified path under `arch/`, `include/`, `virt/`, or
`model/`, and no new image, linker script, privileged instruction, or
guest-visible behavior. `tests/r6/check-sources.mjs` proves that as a measured
property: `production-surfaces=0` and `r6-identifiers=0` in accepted code.
`planning/single-hart-runtime-r5-evidence.md` carries one narrow amendment:
the accepted R5 record's forward-looking "R6 and every later successor remain
not authorized and not started" sentence is time-stamped as true at R5
acceptance and now speaks for R7 onwards. No R5 result, digest, count, or
claim changed.

### Exact corrective parent-delta inventory

`9ed5ad7069b6067f03e1923c09937fe218240a59..7ba3649f03cf13b65df33020e345d361cce2993a`,
18 non-generated paths plus 76 generated:

```text
.github/copilot-instructions.md
README.md
be
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/roadmap.md
planning/single-hart-runtime-r6-evidence.md
scripts/check-be.sh
tests/r3/check-accepted-content.mjs
tests/r4/check-accepted-content.mjs
tests/r6/check-dynamic.mjs
tests/r6/check-fixture-image.mjs
tests/r6/check-report.mjs
tests/r6/check-tool-identity.mjs
tests/r6/test-fresh-bootstrap.mjs
tests/r6/test-report-rejection.mjs
tests/r6/tool-lock.mjs
```

That delta closes two defects that only a fresh standalone run could expose
(findings 11 and 12 in section 5), reports the measured integration state
instead of asserting an uncommitted one, and recomputes pins 3-6, which those
`be` and `scripts/check-be.sh` edits invalidated. It changes no fixture, no
declared expectation, and no accepted mechanism byte.

## 3. Claim boundary

### Supported by the exact target

The exact commit supports exactly this bounded, QEMU-only statement about an
**unaccepted candidate package**, measured against the byte-immutable accepted
R5 target `165f4d001a2b59b582b397bdea79ec4826168fdb`:

> In the fixed single-hart QEMU `virt` profile, with pinned OpenSBI, 46
> separately constructed single-defect adversarial fixtures were each rejected
> or terminated fail-closed at their declared layer: 14 image-construction
> defects were rejected before any execution — four by the accepted source
> inventory, four by accepted linker assertions, and six by the accepted image
> checker; 17 host-mechanism defects produced their exact stable error class;
> and 15 dynamic defects each terminated at the declared phase with the exact
> stable error class, the declared last console marker, no forbidden marker,
> and a monitor-issued SBI SRST shutdown, over two toolchains and two runs
> each. Each dynamic image additionally differed from its same-toolchain
> control image by exactly the one declared delta and in no other byte.

Also supported, as measured properties of the target:

- The accepted R5 baseline is unmodified: 116 immutable paths byte-and-mode
  unchanged, `r5_acceptance=accepted`, `r5_accepted_mechanism_match=yes`, and
  an unchanged content digest
  `a26fcf98375ccb665c025fc8a7514f9c73b9c6b406ba518cc62154f9a1908b9c`.
- R6 adds no production surface and no `BE_R6_*` runtime identifier.
- `./be r6-check` is **standalone**: it passes from a worktree with no
  `build/` directory and with no R0-R5 target run first, creating scratch only
  under `build/r6`.
- The integration and claim state is derived from measurement, not asserted,
  and no measured state maps to a reviewed, accepted, or published claim.

### Trusted or assumed

1. Pinned GCC, Clang, GNU `ld`, `lld`, GNU Make, `bash`, Node, and `flock` are
   trusted and digest-bound.
2. Pinned QEMU 10.2.2 and pinned OpenSBI
   (`49bdf7b939bda11321132d1042bf99d7324fb190f1feef423171fed3573f8705`) are
   trusted and digest-bound; R6 does not model firmware defects.
3. The accepted R0-R5 mechanism is trusted as the measurement instrument; R6
   measures inputs against it and never modifies it.
4. QEMU faithfully models the bounded RISC-V H-extension behavior exercised
   here. QEMU is not hardware.
5. A single hart, no DMA, no external device, and no concurrency.

### Unavailable or `NOT RUN`

- **Hardware validation: NOT RUN.** No K3 or other silicon result exists.
- **Formal verification: NOT RUN and not claimed.** No proof, refinement, or
  model-checking result covers R6.
- **Multi-hart: out of scope.** No concurrency, DMA, IOMMU, or device result.
- **Byte reproducibility of generated assets: open and unresolved.** The
  VitePress generated-asset finding is not resolved by this target.
- **Cross-run byte identity of the report and evidence bundle: not claimed.**
  Byte identity is asserted only between the two generations *within* one run.

### Explicitly not implemented or claimed

- Any acceptance of the R6 implementation, in either integration state.
- Universal containment of malicious or arbitrary guests; the catalogue is
  finite and enumerated, not exhaustive.
- Any hardware or emulator theorem about a genuinely skipped `HFENCE.GVMA`;
  only that the accepted checker rejects the unpaired construction (S-05) and
  that the monitor refuses an unacknowledged fence (D-11).
- New R5 evidence or R5 re-acceptance from control fixture C-01.
- Coverage of `shutdown-returned`/`shutdown-rejected` under QEMU; both are
  host-mechanism results only.
- General asynchronous interrupt handling; exactly one monitor-injected VS
  software interrupt is exercised, with no timer, external, or nested case.
- Any property of a raw QEMU trace beyond its recorded SHA-256, byte count,
  bounded excerpt, and derived canonical semantics; raw traces are ephemeral
  and deleted after extraction (`raw_traces_retained=0`).
- Linux, service, driver, scheduling, restart, rollback, policy, capability,
  Type Enforcement, or CHERI behavior.
- Any Model 0.1/0.2 proof, C-refinement, or Helium claim transfer to R6.
- **Any R7 result, R7 authorization, publication readiness, or release
  authority.**

## 4. Load-bearing invariants

| Invariant | Contract / plan basis | Implementation | Test / evidence artifact |
| --- | --- | --- | --- |
| The catalogue is exactly 47 entries, 46 with exactly one declared defect and C-01 unmutated | Accepted plan R6-B partition tables | `tests/r6/catalogue.mjs`, `catalogue-schema.mjs`, `catalogue-static/-host/-dynamic.mjs`, `fixtures.json` | Catalogue digest `54e8f3414cb0ed2433e923c0cf490eaee68bec177e55af877a9b2b112827c8ca` carried identically by the fixture gate, the report, and every per-fixture eligibility record; `test-fixture-mutation.mjs` (32 mutations, 8 gate refusals, 181 checks) |
| The accepted R5 mechanism is the instrument and is never modified | Accepted R5 acceptance boundary; plan's no-production-surface rule | Fixtures overlay defects onto *copies* in R6-owned scratch only | `check-baseline.sh`: 116 immutable paths, `changed=0`, digest `a26fcf98…`, `r5_accepted_mechanism_match=yes`; `test-baseline-guard.mjs` (24 drift cases, 211 checks) |
| No mutated static image is ever executed | Plan's static-partition rule | `static.mk`, `check-static.mjs` quarantine and digest-based promotion scan over `build/r6` and `build/r5` roots | Static partition measured `promoted=0`, `qemu-runs=0`, 12 ELFs and 24 artifacts quarantined; static self-test 91 cases including 14 built-and-accepted forgeries |
| Host fixtures produce their exact stable accepted error class | Accepted `virt/be/r5.c` error enum; plan's host table | `tests/r6/r6-check.c` calls the accepted architecture-neutral mechanism with exactly one malformed argument or field | 17 fixtures → 18 class outcomes, 1,063 assertions over 68 executions, `gcc-clang-deterministic=yes`, `qemu-runs=0` |
| Every dynamic image differs from its same-toolchain control by exactly the declared delta | Plan L8 single-delta rule; R6-B D-15 pins | `check-fixture-image.mjs` L8 differential, sealed and re-verified | 32 per-image deltas published `by_toolchain`; D-15 pinned to GCC `{30032,9}`/`{30042,1}` with `.monitor.text` `30224` and Clang `{30080,9}`/`{30090,1}` with `30272`, 10 bytes each, from constants the checker owns; 18 layout self-test cases |
| Dynamic eligibility is bound, not assumed | Plan L9/L10 rules | `check-qemu-eligibility.mjs` binds catalogue digest, image digest, and measured accepted-image parity per image | 32 images, 64 runs, 0 timeouts, 0 non-zero QEMU statuses; dynamic self-test 141 cases (11 eligibility, 11 record, 18 image, 18 layout, 20 run, 16 forbidden, 16 console, 17 malformed, 14 shape) |
| D-06's declared class rests on a stated architectural justification | Accepted plan D-06 entry | Frozen guest word `00040513` → `68002573` at GPA `0x40011028` | Observed cause `22` (virtual instruction) at `0x40011028`, class `cause`, last marker `BE_R5:06`; a different observed cause forces a plan revision, never a re-label |
| D-15 preempts before any protected instruction retires | Accepted plan revision R6-A/R6-B | `csrsi hvip,4` then `csrsi hie,4` inserted after every `be_r5_switch_tail` entry-control readback and the last frame restore pair | `scause=0x8000000000000002`, `sepc=0x40011000`, class `interrupt`, last marker `BE_R5:04`, `BE_R5:05` and `BE_R5:12` both absent; flat image stays `212992` bytes |
| Every normative executable is identity-bound, and R6 launches nothing it has not delegated | Plan tool-lock rule derived from accepted R3 lock | `tool-lock.conf` (`c3ce6c32e27433aededdeb72510ec85ca1d3241b19bd7fed303f21c0d6d7e647`) derived from accepted base `c88bd42bedebb181a301b8cffddfb9559517256df7f7363c33b09def4896ba7b`; launch-free `verifyLockedIdentity` shared by `tool-lock.mjs` and `check-tool-identity.mjs` | 36 R6 roles bound by absolute command path, resolved path, version, SHA-256, and owning package; the accepted R3 verifier (42 roles) and accepted R5 probe (36 roles) run once per invocation at `r6-toolcheck` inside R6-owned scratch; `test-tool-binding.mjs` 142 combined hostile-control rejections; the only role R6 itself launches is `flock` |
| Scratch is prepared, inventoried, and confined; nothing is mutated in tree | Plan scratch rule | `prepare-scratch.sh`, `materialize-scratch.mjs`, `overlay-defect.mjs` | 30 trees × 16 components, 5 source components, byte-and-mode verified, `faults=0`, confined to the repository root; scratch self-test 592 checks; `test-scratch-prerequisites.mjs` |
| No R6 file may write outside its declared surface, and no R6 identifier may reach accepted code | Plan source-guard rule | `check-sources.mjs` over 128 package files, 52 guarded | Inventory SHA-256 `e4368c0e7b9439fed49b0e14aa6d27b4e81060b1a703e40536f3c3fe97b56386`; 28 writers over 361 write sites, 1,038 commands, 904 programs, 23 launchers, 92 refused surfaces, `production-surfaces=0`, `r6-identifiers=0`; self-test accepts 72 baselines and refuses 472 hostile variants |
| Overlapping checked invocations are refused, not serialized | Plan run-lock rule | Kernel `flock` on `build/r6/run-lock/lock` via pinned `/usr/bin/flock` | `test-run-lock.mjs` 121 checks; `clean` preserves the lock inode; 2 concurrent-run rejection cases in the tool-binding suite |
| The historical R5 authorization key can never be rewritten into a claim form | Plan authority rule | `authority-policy.mjs` is hash-only: the key and its claim/accepted forms are recognized by SHA-256 and never written literally in checker code | 15 authority-policy invocations pinned by exact normalized line text, aggregate digest, occurrence count, and reachable function; `be status` prints `r6_authorization=` exactly once with provenance `accepted-r5-package-historical`, alongside the distinct live `r6_package_authorization=authorized` |
| The report is independently re-derived, and the evidence bundle is an exact set | Plan report/evidence rules | `generate-report.mjs` / `check-report.mjs`; `generate-evidence.sh` / `check-evidence.mjs` | Report schema `be-r6-adversarial-images-v1`, 47 entries, generated twice byte-identically within a run; `test-report-rejection.mjs` 1,424 mutations → 1,477 refusals; bundle 549 manifest entries / 550 files / `set=exact` / `raw-traces=0` / 536,870,912-byte cap; `test-evidence-rejection.mjs` 43 forgeries → 43 refusals |
| Exactly six predecessor acceptance pins are refreshed, and no more | Accepted plan's enumerated, ordered refresh | `tests/r1/check-acceptance.sh` `successor_makefile_sha256` = `bff108039a5a3397a59f2a633360e16949429fc264164a3655297d31f462fa54`; `tests/r3/check-accepted-content.mjs` approved deltas for `tests/r1/check-acceptance.sh` = `eab6ebd61b33a7ecb63b9ee174844d688fda1b8806ec89cb5b7e75861c591699`, `be` = `cd4fefc69efc69b2321e7e3d636861cb07e6ca25a9ca334cb224578b9b78173e`, `scripts/check-be.sh` = `d98d68ee7ce823ad5cf1c7db0e05434d0c3af4a725872d0e4821ece5a7289820`; `tests/r4/check-accepted-content.mjs` approved deltas for `be` = `d35792bb12cf01d55f9efb397b44ac5be8665d4c9424b2afcfc818cee1f2022a`, `scripts/check-be.sh` = `75e87326e147aa2044ecc24e91b0c22b3adb43665079edf0b53f4f45fa37132e` | `acceptance-pins.mjs` recomputes all six from the same formula and reports `required=6 applied=6`; each pin is proven live by its revert self-test; R1-R5 `--require` all pass with `accepted_mechanism_match=yes` |
| Integration state and evidence claim are measured and derived, never asserted, and neither can rise to acceptance | Plan governance rules and the R6 evidence record's claim ladder | `git ls-tree -r --name-only HEAD -- tests/r6` → `package.head_tracked_r6_paths` → `package.state` and `r6_integration`; `r6_evidence_claim` is a total function of the measured implementation state, applied identically by `check-acceptance.sh`, `be`, `scripts/check-be.sh`, and `check-report.mjs` | `test-committed-state.mjs` over 3 isolated temporary Git repositories: 128 tracked paths measured, 4 derived states, 6 root-integration targets, 79 cases, 41 refusals, all with `acceptance=not-reviewed`; 15 claim-ladder mutations run the real checker over a real staged tree |

## 5. Review history and resolved findings

Every substantive finding raised during planning, implementation, and
independent review is recorded here with its resolution. Micro-style comments
are omitted. **Closing a finding is not acceptance.**

### Accepted-plan corrections made before implementation

| # | Finding | Severity as assessed | Resolution |
| --- | --- | --- | --- |
| P1 | Root acceptance-pin conflict: required root integration is bound by predecessor acceptance checkers, so an unrefreshed pin would flip `r1_acceptance` and cascade to `r5_acceptance=review-required` | Critical: a dependency-status regression falsely readable as an R5 mechanism change | Explicitly authorized six-constant refresh with mandated ordering, bidirectional revert self-tests, and an unchanged `r5_implementation_content_digest` requirement |
| P2 | Dynamic guest-opcode fixtures would be rejected by the accepted image checker before reaching QEMU | Critical: the dynamic partition as drafted could not run | Per-partition applicability rules: a declared, enumerated, single-message `accepted_image_check` disposition plus mandatory L8 single-delta comparison against a control image that passed the complete accepted checker; no accepted invariant is waived |
| P3 | Layer ordering did not match the accepted `tests/r5/Makefile` execution order, and derived counts were inconsistent | Critical: the pipeline model was wrong | Eleven layers re-derived in real execution order, scratch preparation demoted to a precondition, every fixed count asserted in the report |
| P4 | Draft fixtures cited R4 marker text the accepted console never emits; several host fixtures named non-existent structure members or unreachable classes; the S-08 construction was dead code at `-O2`; R6 initially reused the accepted `r6_authorization` key; the scratch inventory omitted the two accepted R3 tool-lock files | High, correctness and honesty | Markers quoted verbatim from the accepted 22-line `expectedConsole`; host fixtures re-sited by field-level accuracy against accepted headers; two reachable S-08 call sites plus a pre-L6 disassembly assertion; distinct live key `r6_package_authorization` with provenance and an exactly-once assertion; R3 tool-lock files made a mandatory fifth scratch component |
| P5 | **Revision R6-A:** D-15's originally accepted injection site could not reach its declared class — arming `hvip[2]`/`hie[2]` inside `switch_domain` is detected by the immutable `be_r5_switch_tail` readback and terminates as `entry-controls` at `BE_R5:04`, never as `interrupt` | Critical plan defect: the declared class was unreachable under any restricted-C spelling | Defect moved to a copy of `arch/riscv/be/r5-trap.S`, after every entry-control readback and the last frame restore pair. Accepted at `75269f058ae578b0a76a113d6c05c0aaceeac8ec`. The gate was **not** relaxed to match the observation |
| P6 | **Revision R6-B defect 1:** the plan's D-15 layout arithmetic was factually wrong — `.monitor.text` does not grow by 8 bytes and no symbol moves, because the existing `.align 4` padding absorbs the two inserted instructions | High: an L8 expectation written from that text would have declared an impossible delta | Exact per-toolchain `{start, length}` runs, 2-run/10-byte totals, and unchanged `.monitor.text` sizes pinned |
| P7 | **Revision R6-B defect 2:** retaining 32 raw `in_asm,cpu` traces (~10.6-11.5 GiB; all 64 ≈ 21 GiB) was arithmetically impossible against the plan's own 512 MiB cap | High: the retention rule could not be satisfied | Raw traces made ephemeral: each run keeps canonical semantics, a SHA-256, a byte count, and a bounded excerpt, then deletes the log. Both defects accepted as R6-B at `6d6464c6c937abccd59df932006c1049fd79fac6` |

### Harness and framework hardening rounds (eight rounds, all closed)

| Round | Finding | Resolution |
| --- | --- | --- |
| 1 | Accepted-phony invocation scanning misfired on fixture defect copies, and the write-boundary logic was tautological rather than fail-closed | Fixture payloads exempted from phony scanning while framework/partition guards were preserved; write-boundary logic replaced with real fail-closed checks plus load-bearing mutation coverage |
| 2 | Fresh-bootstrap tests could execute implemented partition pipelines or treat arbitrary failures/timeouts as success; aliased Node write APIs, `shell -c`, and variable-valued commands bypassed the write boundary | Bootstrap tests confined to graph inspection; aliased-writer, shell, and variable-command bypasses closed with load-bearing mutations |
| 3 | Untracked `node:fs/promises` and file-descriptor writers, interpreter string execution, in-place editors, and archive/patch/git mutation escaped the write surface | All banned with added controls; `stdin`-driven `xargs` writes rejected |
| 4 | Direct compiler/linker/`objcopy`/QEMU invocations were not modelled exactly, so path-valued outputs (dependency, map, trace, device paths) were unconfined | Exact per-tool modes modelled, every path-valued output confined, and every unmodelled flag rejected |
| 5 | `child_process` launcher names could be aliased through namespace, default, and dynamic imports, and `exec`/`execSync` were reachable; self-tests were not reentrant | Exact launcher names enforced, aliases and `exec` family banned, self-tests given unique scratch roots |
| 6 | Cross-file or unreadable child-process helpers could hide launches; run-identity teardown could leave stale directories | Helpers refused unless same-file and non-exported; live-token overlap proofs, signal cleanup, and stale reclamation added |
| 7 | Computed-role direct launch authority remained, and pinned shell roles could be launched with code strings | Computed-role launches removed, the legitimate version probe constrained to a dedicated non-exported helper, pinned shell-role launches and code strings rejected |
| 8 | A dynamic-role exemption still allowed R6 to launch tools directly for version probing | Exemption eliminated; version proof delegated to the accepted R5/R3 verifiers inside a confined materialized scratch tree, leaving every R6 launch under normal mode and write analysis |

Two further harness findings were closed in the same period: the custom
advisory run lock was replaced with a pinned kernel `flock` held across the
whole invocation (with `clean` preserving the lock inode and `renameSync`
modelled as both a source and a destination write), and the authority policy
was rewritten to scan raw and bounded assembled source uniformly, so comments,
regular expressions, and string fragments cannot hide the historical key.

### Partition, report, and evidence findings

| # | Finding | Severity as assessed | Resolution |
| --- | --- | --- | --- |
| F1 | Static promotion scanning could miss artifacts promoted into `tmp`, `home`, or root-level locations, and could crash on files vanishing during a whole-build scan | High: a promoted mutated artifact could escape detection | Digest-based scanning walks the `build/r6` and `build/r5` roots directly; `ENOENT`/`ENOTDIR` from vanishing files is treated as absent while every other error and persistent digest detection is preserved; at least one built-and-accepted forgery added per static fixture, plus an S-08 no-fold assertion before L6 |
| F2 | Host records published class and world as emitted constants rather than observations, and H-17 did not measure transactional/sticky scrub state | Medium: published values could drift from what ran | Class and world derived from the observed accepted R5 enum and phase names; H-17 measures the scrub state |
| F3 | Dynamic coverage lacked real image-byte L8 mutations and per-fixture forbidden-marker rejection; L10 readers accepted malformed counts, digest member types, and null eligibility records | High: a forged or malformed artifact could pass | Real extra/missing/relocated delta mutations added, forbidden-marker rejection added for every dynamic fixture, and record shape, counts, and digest types validated with deterministic refusal of null records |
| F4 | A framework self-test defect: a leaving probe run could survive its own teardown, because `rmSync` races a peer's late `observed-` marker and the failure surfaced from an `exit` handler with status `0` | Medium: an intermittent false failure that masked its own cause | Teardown made claim-then-remove via an atomic `renameSync` to `closing-`; late acknowledgements now fail `ENOENT` harmlessly, `closing-` directories are never peers and dead ones are reclaimed. Coverage was added rather than a retry (`leaving-runs=6`, 190 checks); the new case fails with the old code and passes with the fix |
| F5 | Three unfounded claims in the evidence record's own first draft: the `be status` image-split string was wrong (32 images / 64 runs, not "thirty-two fail-closed plus one control"); `r6_evidence_claim` was an asserted constant; and the record claimed no other tracked file changed | High: overclaim in the authoritative record | The status string corrected and asserted exactly by `scripts/check-be.sh`; the evidence claim made a pure derived function of the measured implementation state, with each consumer checking consistency and refusing its own printed pair on divergence; the inventory claim replaced by a measured, scoped `git status --porcelain` inventory. Pins 3-6 re-derived |
| F6 | The retained evidence summary counted a set it was not part of, and `artifacts.sha256` did not cover it | Medium: one retained artifact stood outside the integrity manifest, and two true numbers described an unnamed set | Summary generated first and hashed into the manifest; fields replaced with `manifest_entries`, `bundle_files`, `payload_bytes`, `manifest_bytes`, `bundle_bytes`, each true of a named set, settled to a fixed point and re-measured from disk; exact-set verifier added and wired into the root `evidence-check` through the checked `r6-evidence-verify` target; 43 forgeries refused. Pins 1, 2, 4, and 6 re-derived in the mandated order |
| F7 | The image-delta comparison published one toolchain's measurement for both | High: a real per-toolchain divergence (D-10 differs by 5,237 bytes under GCC and 464 under Clang) would have been reported as one number | `by_toolchain` records published and checked against each toolchain's own differential result and run-length sum, with D-15's exact per-toolchain offsets and `.monitor.text` sizes pinned in the checker itself and the two accepted layouts required to be distinct; per-toolchain forgeries added |
| F8 | A committed package would have failed the report rather than been described: the generator refused any tree where `tests/r6` was tracked at `HEAD` | Critical for review: the first honest commit of the package — exactly what a review packet requires — would have turned every R6 gate red | State measured instead of asserted: `head_tracked_r6_paths` published and re-measured, `package.state` and `r6_integration` derived from it, neither derived state an acceptance. Proven over three isolated temporary Git repositories (79 cases, 41 refusals). Pins 3-6 re-derived |
| F9 | The state-aware evidence was itself written for one state: root integration was measured as working-tree dirtiness, the committed-state suite compared against a hard-coded zero, several forgeries became no-ops once committed, and `worktree_entries` was published without being re-measured | High: the fix for F8 was not actually proven after a commit | Root integration measured as `git diff --name-only <accepted R5 commit> -- <six refresh targets>`, which is the same set before and after a commit; every state forgery made toggling so it forges a real claim in either state; `worktree_entries` re-measured and compared entry by entry with five new forgeries |
| F10 | Independent final code, harness, and claims reviews of the complete integrated package | No significant remaining defects found | No change required beyond the items already listed |

### The corrective delta: two defects only a fresh standalone run could expose

The initial implementation candidate `9ed5ad7069b6067f03e1923c09937fe218240a59`
passed the complete `make check`, but **failed a first `./be r6-check` in a
fresh worktree with no `build/`**. Both defects were undeclared dependencies on
a previous package's build, and both were masked because `make check` runs R3
and R5 first.

| # | Finding | Severity as assessed | Resolution in `7ba3649f03cf13b65df33020e345d361cce2993a` |
| --- | --- | --- | --- |
| 11 | `check-fixture-image.mjs` (L8) and `check-dynamic.mjs` (L10) called the accepted R3 `verifyToolLock`, re-exported by `tests/r6/tool-lock.mjs`. That verifier launches every locked tool under the accepted R3 clean environment naming `build/r3/tool-home` and `build/r3/tmp` — a tree no R6 target creates or may create. In a fresh checkout GNU Make wrote a missing-`TMPDIR` warning to stderr, the accepted stderr-first version reader consumed it as the version string, and R6 refused with `make version drift` | High: a **misreported** fault. A reviewer starting from a clean clone would see a false tool-identity failure and no true diagnosis | `tool-lock.mjs` no longer re-exports `verifyToolLock`; it exports a launch-free `verifyLockedIdentity` binding each role by absolute command path, executable mode, regular-file status, resolved real path, and SHA-256 digest, requiring membership of both accepted role sets. Launch-dependent facts stay delegated to the accepted verifiers, run exactly once per invocation at `r6-toolcheck` inside R6-owned scratch, a transitive prerequisite of every partition target. `check-tool-identity.mjs` shares that one definition, and R6 exports no function that launches a process |
| 12 | With finding 11 fixed, a fresh standalone run reached `r6-report` and was refused with `D-01 gcc claims parity with the accepted image`: `check-report.mjs` demanded `differs`/`identical` unconditionally, although the accepted R5 image is a build product of the accepted R5 target and of no R6 target | High: the same class of undeclared dependency, again masked by `make check` | `check-report.mjs` now measures `build/r5/<toolchain>/beryllium.bin` itself, requires the eligibility record to bind the digest it measured, and requires the published parity to follow that measurement **in both directions** — demanded when the accepted image exists, refused when it does not. A toggling `accepted-parity-suppressed` forgery joins the existing `-claimed` case; the pinned rejection suite moved from 1,408 to 1,424 mutations and 1,461 to 1,477 refusals |

Neither fix relaxes a locked tool identity, a declared expectation, or a
gate. The bounded regression is `test-fresh-bootstrap.mjs`, which deletes
`build/` and runs both later-stage semantic checkers directly, requiring each
to refuse for its own artifact reason, never to blame executable identity or
scratch, and to leave no `build/r3`, no `build/r5`, and no `build/` at all.

### Open questions requiring human judgment

- **The open generated-asset byte-reproducibility finding remains
  unresolved.** The VitePress planning build produces different hash-named
  JavaScript assets on regeneration. Functional link and static/browser render
  gates pass. R6 does not resolve this and claims no byte reproducibility for
  generated HTML.
- **Standalone and full-repository validation are both exact and both
  reported**, but they are not identical runs: the report's exact byte count
  and the independent checker's assertion count legitimately differ between
  them because accepted-image parity is available in one and not the other
  (section 6). Whether reporting both states, rather than pinning one, is the
  right boundary is a judgment call for you.
- Whether the finite 47-entry catalogue is adequate adversarial coverage for
  R6, given that it is explicitly not exhaustive, is a scope judgment.
- Whether QEMU-only evidence, with hardware and formal verification `NOT RUN`,
  is an acceptable evidence boundary for accepting this package.

## 6. Validation and retained evidence

All results below were obtained on 2026-08-04 against the **clean exact target
`7ba3649f03cf13b65df33020e345d361cce2993a`**, not equivalent pre-commit
content. Two independent detached worktrees were checked out at that exact
commit, each starting with **no `build/` and no `node_modules/`**, and 128
tracked `tests/r6` paths. Both worktrees were removed with
`git worktree remove --force` afterwards; the main worktree is clean at the
target, with refs, tags, and remotes unchanged.

### Scenario A — standalone

| Step | Result |
| --- | --- |
| Pre-state | detached clean; `build/` ABSENT; `node_modules/` ABSENT; no `npm ci`; no manually created scratch |
| **First build command: `./be r6-check`** | **PASS**, 21m09s (05:43:19→06:04:28Z) |
| Build roots created | **`build/r6` only** — `build/r3` and `build/r5` ABSENT afterwards |
| Accepted-image parity | `accepted_image_parity=not-available` ×32, and the report is required to carry exactly that |
| Follow-up | `./be r6-evidence` **PASS** 12m13s; `./be status`, `./be help`, `./be version`; `r6-evidence-verify` → `set=exact`; `sha256sum --quiet -c build/r6/evidence/artifacts.sha256` exit 0 over 549 entries; 10 negative cases all refused |
| Churn | zero — `git status` clean, no untracked path outside gitignored `build/` |

The 10 refused negatives were: `r6-bogus` target, two targets at once, injected
`CC=`, injected `MAKEFLAGS=`, injected `R6_SCRATCH_ROOT=`,
`BE_R3_MAKE_DRY_RUN=1`, `./be status extra`, `BE_DRY_RUN=2` (each exit 2), plus
`check-evidence.mjs` on an absent directory and `check-acceptance.sh --bogus`
(each exit 1 with `BE_R6:FAIL`).

### Scenario B — full repository

| Step | Result |
| --- | --- |
| Pre-state | detached clean; `build/` ABSENT; `node_modules/` ABSENT |
| `npm ci` | 5s, non-build; `package.json` (`c6580467…`, 1,529 B) and `package-lock.json` (`1578a532…`, 88,575 B) byte-identical afterwards; `build/` still ABSENT |
| **First build command: `make check`** | **PASS**, 30m25s (06:26:03→06:56:28Z), including `evidence-check` |
| Build roots created | `docs model pathfinder r0 r1 r3 r4 r5 r6` |
| Accepted-image parity | available: `differs` ×30 and `identical` ×2 |
| Follow-up | `make be-check` **PASS** 10s; `./be r6-evidence` **PASS** 12m21s; `make evidence-check` **PASS**; `./be docs-build` **PASS**; `./be docs-check` **PASS** |
| Churn | only generated planning-site churn from the documentation build (60 modified `docs/html/*.html`, 4 deleted and 4 new content-hash assets); **zero** changes under `tests/ arch/ include/ model/ virt/ scripts/ be Makefile package.json package-lock.json README.md planning/`; restored |

### Definitive counts — identical in both scenarios

| Partition / gate | Measured |
| --- | --- |
| Static | `fixtures=14`, `promoted=0`, `qemu-runs=0`; 24 results, 20 build attempts, 8 link failures, 12 image rejections, 12 ELFs quarantined; manifests `l3=4 l5=4 l6=6 budget=6/6` |
| Host | `executions=68`, `assertions=1063`, `gcc-clang-deterministic=yes`; 17 fixtures, 18 class outcomes, 30 cases |
| Dynamic | `differential_invocations=32`, `qemu_runs=64`, self-test `cases=141` (11 eligibility, 11 record, 18 image, 18 layout, 20 run, 16 forbidden, 16 console, 17 malformed, 14 shape) |
| Report | `entries=47` (14 static, 17 host, 15 dynamic, 1 control), 32 images, 64 runs |
| Report rejection | `mutations=1424`, `refusals=1477` (29 classes, 11 layers, 15 claim-ladder, 21 acceptance) — identical in both |
| Evidence | `manifest-entries=549`, `bundle-files=550`, `set=exact`, `raw-traces=0`, `limit=536870912` (512 MiB), fixtures 47, scratch trees 30; evidence rejection `mutations=43 refusals=43` |
| D-15 L8 pins | GCC `runs=[{30032,9},{30042,1}] bytes=10 monitor_text_size=30224`; Clang `runs=[{30080,9},{30090,1}] bytes=10 monitor_text_size=30272`; both `parity_stage=ran`, `kind=monitor-range` |
| Pins | `pins-authorized=6 pins-required=6 pins-refreshed=6` |
| Authority | live keys 15; authority scan `paths=1 files=550` |
| Baseline | `immutable-paths=116 changed=0`, accepted R5 `165f4d001a2b59b582b397bdea79ec4826168fdb`, digest `a26fcf98…`, `r5_accepted_mechanism_match=yes` |
| Pre-decision integration posture at the exact target | `r6_integration=committed-candidate-not-accepted`, `r6_head_tracked_paths=128`, `r6_implementation=complete-local`, `r6_evidence_claim=complete-local-not-reviewed`, `r6_acceptance=not-reviewed`, `r6_accepted_commit=none`, `r6_package_authorization=authorized`, `r6_hardware_validation=NOT-RUN`, `r6_formal_verification=NOT-RUN-not-claimed`, `r6_publication_scope=blocked`, `r6_release_scope=blocked`, `r7_authorization=not-authorized`, `r7_implementation=not-started`; these are the exact-target values before the later responsible-human decision |
| Committed-state suite | 3 repositories, 128 tracked, 128 live-tracked, 0 worktree entries, 4 derived states, 6 integration targets, 79 cases, 41 refusals |
| Report-check assertions | scenario A **21,740**; scenario B **21,804** |

### Exact per-scenario artifact hashes and byte counts

| Artifact | A after `r6-check` | A after `r6-evidence` | B after `make check` | B after `r6-evidence` |
| --- | --- | --- | --- | --- |
| `build/r6/reports/adversarial-images.json` SHA-256 | `c3cdf53db2e922b1890fcd2c83d2e01ddc2f4c2b1f979375be772a529122cba1` | `51cac98fa038a3dbfb04953514cee14835e82e530b3999665eab76c173a310b1` | `d5169bb52bb6b7386828e6e02d6cccde8cca4b4f779594e2eb713cee5052befb` | `a6e60f6b018f9ad772b1872c33a93232e0f96fbdf2458c1674f64a23f1478f0c` |
| Report bytes | `521589` | `521589` | `521401` | `521401` |
| `build/r6/evidence/artifacts.sha256` SHA-256 | `77afab156bc83c39cebe04bf80fd562d90e87072cad78a1fcd350ca68e080baa` | `d32a9394ceee769f70e857fcba7bad1a5f17b19b2c0b567a5ea0c7549fcb20b8` | `ac39c3d0814b2c8648bfba24eae6136824d65e3d7424454468bb7bd07200007a` | `95330107d7f37f2e2b094cc39852efff22057e6d770e0af5e225db57c51b9370` |
| Manifest bytes | `63702` | `63702` | `63702` | `63702` |
| `scratch-inventory.txt` | `8ca47cb70a39e773dc6202ab7fe84abf4a6ee7b3840670458059055ff640d510` / 767 B | identical | identical | identical |
| `claim-ledger.txt` | `cf055b81846d60d55e4d7169b7593572c2709b208aaae751d8f9cd8b2538fc53` / 1168 B | identical | identical | identical |
| Payload / bundle bytes | `4807409` / `4871111` | `4807611` / `4871313` | `4809648` / `4873350` | `4808609` / `4872311` |

**Why the runs and hashes are not identical, and why that is not a defect.**

- The **188-byte report difference** between scenarios (521,589 in A versus
  521,401 in B) and the **+64 report-check assertions** in B both follow from
  one field: accepted-image parity. In A the accepted R5 image does not exist,
  so 32 records carry `not-available`; in B 30 carry `differs` and 2 carry
  `identical`, and the extra assertions are gated on parity being available.
  This is stated as arithmetic consistency, not as an independently isolated
  proof of the delta.
- The **report and `artifacts.sha256` are not hash-stable across independent
  executions**, although their byte lengths are stable within a scenario. Byte
  identity is asserted only between the two generations compared **within one
  run** (`generations=2 comparison=byte-identical`, PASS in every run), because
  each run records the SHA-256 and byte count of its ephemeral raw QEMU traces,
  and those digests differ per run.
- **Payload and bundle bytes vary run to run** (4,807,409 / 4,807,611 /
  4,808,609 / 4,809,648) while `manifest-entries=549`, `bundle-files=550`, and
  `manifest_bytes=63702` stay fixed. `scratch-inventory.txt` and
  `claim-ledger.txt` were hash-identical across all four generations.
- The report's exact size also moves with the tree's measured **integration
  state**, by design: an untracked package, a committed package, and a
  committed package with uncommitted follow-up edits each produce a different
  exact size. That is why the evidence record validates equivalent content and
  re-derives exact numbers per run, and why exact bytes are recorded here, for
  one exactly validated target, rather than carried forward.

### Execution boundary

These results bind to commit `7ba3649f03cf13b65df33020e345d361cce2993a` only.
This packet is a later follow-up commit; re-running any gate from the packet
commit or from a dirty worktree validates that later content, not the review
target. `planning/single-hart-runtime-r6-evidence.md` is the authoritative
evidence and claim record.

## 7. Recommended human review sequence

Use an isolated detached worktree so unrelated local changes cannot affect the
review:

```sh
git worktree add --detach ../beryllium-r6-review 7ba3649f03cf13b65df33020e345d361cce2993a
cd ../beryllium-r6-review
git status --short
git show --no-patch --format=fuller 7ba3649f03cf13b65df33020e345d361cce2993a
git show --no-patch --format=fuller 9ed5ad7069b6067f03e1923c09937fe218240a59
git diff --check 4012d794e769fd4029b11f6f45e366ed0ef117f5 7ba3649f03cf13b65df33020e345d361cce2993a
```

1. Read the accepted plan `planning/single-hart-runtime-r6-plan.md` at
   revision R6-B, its
   [R6-B review and acceptance record](single-hart-runtime-r6-plan-r6b-review-summary.md),
   the [R6 evidence record](single-hart-runtime-r6-evidence.md), and then this
   packet. Confirm the claim and R6/R7 boundaries before reading code.
2. Inspect the whole implementation range, not only the corrective delta:

   ```sh
   git log --reverse --oneline 4012d794e769fd4029b11f6f45e366ed0ef117f5..7ba3649f03cf13b65df33020e345d361cce2993a
   git diff --stat 4012d794e769fd4029b11f6f45e366ed0ef117f5 7ba3649f03cf13b65df33020e345d361cce2993a
   git diff --name-status 4012d794e769fd4029b11f6f45e366ed0ef117f5 7ba3649f03cf13b65df33020e345d361cce2993a -- ':!docs/html'
   ```

3. Confirm the test-only boundary directly, rather than from prose:

   ```sh
   git diff --name-only 4012d794e769fd4029b11f6f45e366ed0ef117f5 7ba3649f03cf13b65df33020e345d361cce2993a -- arch include virt model
   git diff 165f4d001a2b59b582b397bdea79ec4826168fdb 7ba3649f03cf13b65df33020e345d361cce2993a -- tests/r1/check-acceptance.sh tests/r3/check-accepted-content.mjs tests/r4/check-accepted-content.mjs
   ```

   The first command must print nothing. The second must show exactly six
   changed constant lines and nothing else.
4. Review the fixture catalogue and the declared expectations
   (`tests/r6/catalogue*.mjs`, `handlers.mjs`, `fixtures.json`,
   `fixtures/*/fixture.json`). Ask whether each declared layer, disposition,
   class, and marker is architecturally justified — especially D-06's cause
   `22` and D-15's pinned per-toolchain layout — and whether any expectation
   was written to match an observation.
5. Review the harness security boundary (`run-make.sh`, `make-control.mjs`,
   `tool-lock.mjs`, `check-tools.sh`, `prepare-scratch.sh`,
   `check-sources.mjs`, `run-lock.mjs`, `authority-policy.mjs`). Ask whether a
   hostile Make control, shell override, aliased writer, or substituted
   executable can reach a success banner, and whether the launch-free identity
   rebinding in the corrective delta genuinely delegates rather than weakens
   the proof.
6. Review the report and evidence integrity path (`generate-report.mjs`,
   `check-report.mjs`, `generate-evidence.sh`, `check-evidence.mjs`) and the
   rejection suites. Confirm that the measured accepted-image parity is
   required in both directions, that the claim ladder cannot rise, and that
   the acceptance surfaces report status only.
7. Review the corrective delta on its own terms and confirm it changes only
   harness behavior and reported state:

   ```sh
   git diff 9ed5ad7069b6067f03e1923c09937fe218240a59 7ba3649f03cf13b65df33020e345d361cce2993a -- ':!docs/html'
   ```

8. If reproducing, run the documented commands from a build-absent checkout of
   the exact target — `./be r6-check` alone for the standalone property, and
   `npm ci && make check` for the full gate — and expect the parity and byte
   differences described in section 6. Remove the review worktree only after
   recording your decision:

   ```sh
   cd -
   git worktree remove --force ../beryllium-r6-review
   ```

## 8. Human decision checklist

- [ ] The scope of the exact target matches accepted plan revision R6-B
  `6d6464c6c937abccd59df932006c1049fd79fac6`, including the D-15 injection
  site, the pinned per-toolchain layout, and the ephemeral raw-trace retention
  rule.
- [ ] The claims in section 3 match the retained evidence, and the QEMU-only,
  finite-catalogue boundary is stated accurately and not overstated.
- [ ] The trusted toolchain, pinned OpenSBI, pinned QEMU, accepted-R5-as-
  instrument, and single-hart assumptions are acceptable.
- [ ] Negative paths — hostile Make and shell controls, substituted or
  redirected tools and scratch, forged reports and evidence, forged authority,
  forged pins, forged integration state, and the fresh-tree artifact refusals
  — are covered sufficiently.
- [ ] R6 genuinely adds **no** production surface: nothing under `arch/`,
  `include/`, or `virt/`, no `BE_R6_*` runtime identifier, and no new image.
- [ ] Exactly six predecessor acceptance pins were refreshed, no accepted R0-R5
  mechanism byte changed, and every predecessor still reports
  `accepted_mechanism_match=yes`.
- [ ] The standalone (`./be r6-check` from a build-absent tree) and full
  (`npm ci` then `make check`) exact-target reproductions, and the explained
  differences between them, are acceptable evidence.
- [ ] R7 and every later successor, plus tag, push, publication, and release
  work, remain excluded.
- [ ] The open generated-asset byte-reproducibility finding is understood and
  remains open.
- [x] **Accept** exact commit `7ba3649f03cf13b65df33020e345d361cce2993a`
  on 2026-08-05 by explicit responsible-human instruction.
- [ ] **Request revisions** through a new commit and a new review packet.
- [ ] **Defer** the decision while preserving current gates.

Only the acceptance-decision box is checked because the responsible human
explicitly supplied that decision. The technical-judgment checklist remains
unchanged as review history; no signature is generated.

## 9. Recorded decision and remaining boundaries

- **Recorded acceptance:** acceptance applies to exact commit
  `7ba3649f03cf13b65df33020e345d361cce2993a` and to the R6 implementation it
  carries, which spans that commit and its parent
  `9ed5ad7069b6067f03e1923c09937fe218240a59`.
- Acceptance records acceptance **only**. It does not authorize or start R7,
  and it adds no hardware, formal, multi-hart, device, Linux, or service
  evidence.
- Acceptance does not erase the trusted assumptions, the `NOT RUN` items, the
  resolved findings, or the open generated-asset byte-reproducibility finding.
- Push, tag, public release, publication, and any
  `pathfinder/publication-gate.conf` change remain **prohibited** without
  separate, explicit authorization.

**Status.** R6 is implemented, locally complete, root-integrated, and
exact-target validated at `7ba3649f03cf13b65df33020e345d361cce2993a` in two
independent fresh detached worktrees, and is responsible-human accepted at
that exact target as of 2026-08-05. Hardware validation and
formal verification are **NOT RUN**. R7 is not authorized and not started.
Push, tag, publication, and release remain blocked.

**Next.** No successor work is authorized; R7 remains gated.

**Action required from you.** None for this recorded R6 decision. Separate
explicit authorization is required before R7, push, tag, publication, or
release work.
