<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R5 review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves the packet-time former private repository identity and remote
> state. The current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

## Decision record

The responsible human explicitly accepted the exact R5 implementation target
on 2026-07-30, with this instruction, timestamped
2026-07-30T18:06:26.639+00:00, preserved verbatim:

```text
accept exact 165f4d001a2b59b582b397bdea79ec4826168fdb
```

The accepted implementation is only
`165f4d001a2b59b582b397bdea79ec4826168fdb`, whose immediate parent/main
implementation is `9312c1355a23d411e3bdafb2183be342683a8ab9` and whose
whole-R5 comparison base is `a8161e639af4a141e0d3ca1322202c91129724c7`. The
accepted plan is `fecae6b62a507bdbb93d211262197a31f5422316`. Review packet
commit `9bb89fe196740c5e3252bdccced6fb202df65e55`, and the later follow-up
commit that records this decision, are decision support and are **not**
accepted implementation.

Acceptance does not erase trusted assumptions, `NOT RUN` items, resolved
findings, the open generated-asset byte-reproducibility finding, or the
raw-trace byte-nonidentity boundary. It adds no hardware or formal evidence.
It does not authorize or start R6 or any successor, and it does not authorize
a tag, a push, publication, release, or a `pathfinder/publication-gate.conf`
change.

The review material below is preserved as written for the exact target. Only
the decision fields were updated.

## 1. Decision summary

| Field | Required content |
| --- | --- |
| Review target | Exact corrective R5 target `165f4d001a2b59b582b397bdea79ec4826168fdb` (`tests: make R4 and R5 checks fresh-worktree safe`), immediate parent/main implementation `9312c1355a23d411e3bdafb2183be342683a8ab9` (`runtime: implement bounded single-hart R5 switch`), whole-R5 comparison base `a8161e639af4a141e0d3ca1322202c91129724c7` (`docs: accept and authorize single-hart runtime R5 plan`). |
| Current status | R5 was authorized by the exact human instruction `authorize r5 implementation, proceed` on 2026-07-30 under accepted plan `fecae6b62a507bdbb93d211262197a31f5422316`; it is implemented, exact-target validated, and **responsible-human accepted** at exact commit `165f4d001a2b59b582b397bdea79ec4826168fdb` on 2026-07-30. |
| Decision recorded | Accepted exact commit `165f4d001a2b59b582b397bdea79ec4826168fdb`; review packet commit `9bb89fe196740c5e3252bdccced6fb202df65e55` and this acceptance record are not accepted implementation. |
| Branch | `beryllium/single-hart-runtime-r0`, internal/private. |
| Prior accepted boundary | R3 remains accepted only at `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`; R4 remains accepted only at `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` (implementation parent `6e5c55c59e94bbaba136269c784db28ec1b53f54`). Their follow-ups `fcc0f267a1f59241f872c0a1d2a371a95a58cba6` and `87b136bc4889a04a58c2399e4eb81f7925cba5e0` remain decision support, not accepted implementation. |
| Successor status | R6 and every later successor are **not authorized and not started**. |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`; the target is local, unpushed, and untagged (zero remote refs and zero tags contain it). Push, tag, public release, and publication remain blocked. |

The remaining action is independent review of this acceptance record, without
changing the accepted target.

## 2. Deliverables

R5 implementation spans two commits. The whole-R5 range
`a8161e639af4a141e0d3ca1322202c91129724c7..165f4d001a2b59b582b397bdea79ec4826168fdb`
reports 121 paths, 11,141 insertions, and 347 deletions: 51 non-generated
paths plus 70 generated planning paths under `docs/html/`. The corrective
parent delta
`9312c1355a23d411e3bdafb2183be342683a8ab9..165f4d001a2b59b582b397bdea79ec4826168fdb`
is 14 paths, 1,015 insertions, and 20 deletions, all non-generated and all
under `tests/r4/` and `tests/r5/`. **Review the whole range, not only that
corrective delta.**

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary review question |
| --- | --- | --- | --- | --- |
| R5 contract and switch transaction | `include/be/r5.h`, `virt/be/r5.c` | Import exact R4 `COMPLETE` state; drive the one-way phase machine; validate bindings/frames; build one complete pending target; decide publication; fail closed and sticky | Restricted C with no privileged instruction; it consumes observations from privileged assembly and owns no CSR write | Can any path publish a target before the root write, fence, and verified readback all succeed, or accept a guest-influenced binding? |
| Privileged entry, trap, runtime, guest, and linker boundary | `arch/riscv/be/r5-entry.S`, `arch/riscv/be/r5-trap.S`, `arch/riscv/be/r5-runtime.c`, `arch/riscv/be/r5-guest.S`, `arch/riscv/be/r5-platform.h`, `arch/riscv/be/r5-beryllium.lds` | HS entry, trusted-stack vector, complete 320-byte frame save, CSR/HGATP/fence/readback/reset boundary, frozen fixtures, physical ownership and linker assertions, no-call restore/`SRET` tail | The only R5 privileged/assembly boundary; trusts pinned OpenSBI, GCC, Clang, GNU ld, lld, assembler/disassembler, QEMU, and the ratified RISC-V privileged architecture | Is exactly one HGATP write, one local `HFENCE.GVMA`, and one verified readback performed per switch, with no rollback, alternate target, or re-entry after a partial publication? |
| Evidence, image, and hostile-control checks | `tests/r5/**` (23 paths) | GCC/Clang host tests, image semantics and parity, six QEMU runs, deterministic report, evidence retention, tool lock, scratch confinement, fresh-bootstrap and rejection suites | Host and QEMU evidence only; not hardware, not a source-to-binary proof | Do the independent checkers reject substituted tools, hostile Make controls, redirected scratch, altered or stale artifacts, and invalid reports without ever relaxing the R3 tool lock? |
| Fresh-worktree scratch correction (target's parent delta) | `tests/r5/prepare-scratch.sh`, `tests/r5/probe-tool-versions.mjs`, `tests/r5/test-fresh-bootstrap.mjs`, `tests/r5/run-make.sh`, `tests/r5/check-tools.sh`, `tests/r5/Makefile`, `tests/r5/tool-lock.mjs`, `tests/r4/prepare-scratch.sh`, `tests/r4/Makefile`, `tests/r4/generate-report.mjs` | Create and confine every scratch component parent-first before a pinned tool runs; probe every normative role under both the R5-owned and inherited R3 clean environments; prove a build-absent fresh checkout works | Harness only; adds no privileged code and relaxes no locked tool identity | Does parent-first preparation genuinely refuse symlinked or out-of-repository scratch, rather than creating through it? |
| Acceptance-drift and wrapper integration | `tests/r5/check-acceptance.sh`, `tests/r5/check-accepted-content.mjs`, `tests/r5/test-acceptance-content.mjs`, `tests/r1/check-acceptance.sh`, `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs`, `tests/r4/test-acceptance-content.mjs`, `be`, `Makefile`, `scripts/check-be.sh` | Bind current R5 content to a deterministic digest, keep exact accepted R1-R4 boundaries, and integrate R5 into repository checks/status | Orchestration and status reporting cannot create acceptance; earlier accepted content stays exact-bound through immutable, approved-delta, and added-file classes | Can any later R5 or harness work silently change previously accepted inputs, manufacture an acceptance target, or report release authority? |
| Maintained documentation and render inventory | `.github/copilot-instructions.md`, `README.md`, `planning/HANDOFF.md`, `planning/README.md`, `planning/implementation-plan.md`, `planning/roadmap.md`, `planning/single-hart-runtime-r5-evidence.md`, `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs` | Record the bounded R5 state, evidence, R6 exclusion, and browser coverage | Markdown is authoritative; generated HTML is derivative | Do the source documents keep implementation, exact-target validation, human decision, and blocked publication strictly separate? |
| Generated planning site | 70 paths under `docs/html/` | Render the maintained Markdown | Derivative only; byte reproducibility remains open | Are links and static/browser rendering functional without treating unstable hash-named assets as resolved? |

### Exact whole-range changed-file inventory

Non-generated paths (51):

```text
.github/copilot-instructions.md
Makefile
README.md
arch/riscv/be/r5-beryllium.lds
arch/riscv/be/r5-entry.S
arch/riscv/be/r5-guest.S
arch/riscv/be/r5-platform.h
arch/riscv/be/r5-runtime.c
arch/riscv/be/r5-trap.S
be
include/be/r5.h
pathfinder/tests/check-docs-render.mjs
planning/.vitepress/config.mts
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/roadmap.md
planning/single-hart-runtime-r5-evidence.md
scripts/check-be.sh
tests/r1/check-acceptance.sh
tests/r3/check-accepted-content.mjs
tests/r4/Makefile
tests/r4/check-accepted-content.mjs
tests/r4/generate-report.mjs
tests/r4/prepare-scratch.sh
tests/r4/test-acceptance-content.mjs
tests/r5/Makefile
tests/r5/check-acceptance.sh
tests/r5/check-accepted-content.mjs
tests/r5/check-image-parity.mjs
tests/r5/check-image.mjs
tests/r5/check-qemu-artifacts.mjs
tests/r5/check-report.mjs
tests/r5/check-sources.mjs
tests/r5/check-tools.sh
tests/r5/generate-evidence.sh
tests/r5/generate-report.mjs
tests/r5/make-control.mjs
tests/r5/prepare-scratch.sh
tests/r5/probe-tool-versions.mjs
tests/r5/r5-check.c
tests/r5/run-make.sh
tests/r5/run-qemu.sh
tests/r5/test-acceptance-content.mjs
tests/r5/test-fresh-bootstrap.mjs
tests/r5/test-qemu-artifact-integrity.mjs
tests/r5/test-report-rejection.mjs
tests/r5/test-tool-binding.mjs
tests/r5/tool-lock.conf
tests/r5/tool-lock.mjs
virt/be/r5.c
```

Generated paths (70, derivative and non-normative; renames are `old -> new`):

```text
docs/html/404.html
docs/html/HANDOFF.html
docs/html/architecture-model-0.1-evidence.html
docs/html/architecture-model-0.1.html
docs/html/architecture-model-0.2-evidence.html
docs/html/architecture-model-0.2.html
docs/html/arm64-pathfinder-plan.html
docs/html/assets/HANDOFF.md.7nIrhsgw.js -> docs/html/assets/HANDOFF.md.C-tvfmAY.js
docs/html/assets/HANDOFF.md.7nIrhsgw.lean.js -> docs/html/assets/HANDOFF.md.C-tvfmAY.lean.js
docs/html/assets/app.DU_90geB.js -> docs/html/assets/app.CmFZUJD6.js
docs/html/assets/chunks/@localSearchIndexroot.CiEm9YNZ.js
docs/html/assets/chunks/@localSearchIndexroot.VeZnUMNq.js
docs/html/assets/chunks/VPLocalSearchBox.BTvhXoZD.js -> docs/html/assets/chunks/VPLocalSearchBox.5tAEwQNk.js
docs/html/assets/chunks/theme.cyZQtrNa.js -> docs/html/assets/chunks/theme.Dtgli5if.js
docs/html/assets/implementation-plan.md.BT1oRMrv.js
docs/html/assets/implementation-plan.md.DfrAEYlc.js
docs/html/assets/implementation-plan.md.DfrAEYlc.lean.js -> docs/html/assets/implementation-plan.md.BT1oRMrv.lean.js
docs/html/assets/index.md.CHApwwa2.js
docs/html/assets/index.md.ZoiU5xcw.js
docs/html/assets/index.md.ZoiU5xcw.lean.js -> docs/html/assets/index.md.CHApwwa2.lean.js
docs/html/assets/roadmap.md.BSBI-Syd.js
docs/html/assets/roadmap.md.BSBI-Syd.lean.js
docs/html/assets/roadmap.md.C8JpCYhp.js
docs/html/assets/roadmap.md.C8JpCYhp.lean.js
docs/html/assets/single-hart-runtime-r5-evidence.md.2YtSjKNV.js
docs/html/assets/single-hart-runtime-r5-evidence.md.2YtSjKNV.lean.js
docs/html/beryllium-hypervisor-notes.html
docs/html/capability-policy-architecture.html
docs/html/cheri-alignment.html
docs/html/hashmap.json
docs/html/implementation-plan.html
docs/html/index.html
docs/html/isolation-engine-policy-research.html
docs/html/minimal-pathfinder-evidence.html
docs/html/minimal-pathfinder-plan.html
docs/html/open-tooling.html
docs/html/pathfinder-comparison.html
docs/html/pathfinder-evidence.html
docs/html/pathfinder-plan.html
docs/html/research-provenance.html
docs/html/research-synthesis.html
docs/html/riscv-security-hardware.html
docs/html/roadmap.html
docs/html/session-analysis-cap-te-cheri-2026-07-20.html
docs/html/session-analysis-isolation-engine-2026-07-20.html
docs/html/session-analysis-te-vbs-2026-07-20.html
docs/html/session-analysis-transcripts-2026-07-20.html
docs/html/sidebar-dynamic-authority-caches.html
docs/html/sidebar-high-assurance-standards.html
docs/html/sidebar-lvbs-equivalence.html
docs/html/sidebar-minimal-vs-runtimes.html
docs/html/sidebar-rust-vs-components.html
docs/html/single-hart-runtime-plan.html
docs/html/single-hart-runtime-r0-freeze.html
docs/html/single-hart-runtime-r1-evidence.html
docs/html/single-hart-runtime-r1-review-summary.html
docs/html/single-hart-runtime-r2-evidence.html
docs/html/single-hart-runtime-r2-plan-review-summary.html
docs/html/single-hart-runtime-r2-plan.html
docs/html/single-hart-runtime-r2-review-summary.html
docs/html/single-hart-runtime-r3-evidence.html
docs/html/single-hart-runtime-r3-review-summary.html
docs/html/single-hart-runtime-r4-evidence.html
docs/html/single-hart-runtime-r4-review-summary.html
docs/html/single-hart-runtime-r5-evidence.html
docs/html/single-hart-runtime-r5-plan-review-summary.html
docs/html/single-hart-runtime-r5-plan.html
docs/html/supervisory-security-policy.html
docs/html/type-enforcement-pathfinder-evidence.html
docs/html/type-enforcement-pathfinder-plan.html
```

### Corrective parent-delta inventory

The target's parent delta changes these 14 paths, all harness:

```text
tests/r4/Makefile
tests/r4/check-accepted-content.mjs
tests/r4/generate-report.mjs
tests/r4/prepare-scratch.sh
tests/r5/Makefile
tests/r5/check-accepted-content.mjs
tests/r5/check-report.mjs
tests/r5/check-tools.sh
tests/r5/generate-report.mjs
tests/r5/prepare-scratch.sh
tests/r5/probe-tool-versions.mjs
tests/r5/run-make.sh
tests/r5/test-fresh-bootstrap.mjs
tests/r5/tool-lock.mjs
```

The exact status/path inventory for either range remains reproducible without
interpretation:

```sh
git diff --name-status a8161e639af4a141e0d3ca1322202c91129724c7 165f4d001a2b59b582b397bdea79ec4826168fdb
git diff --name-status 9312c1355a23d411e3bdafb2183be342683a8ab9 165f4d001a2b59b582b397bdea79ec4826168fdb
```

## 3. Claim boundary

### Supported by the exact target

- In the fixed single-hart QEMU profile, GCC and Clang images re-execute the
  accepted R4 management prelude to its exact `COMPLETE` state at
  `sepc=0x40010034`, perform one checked management-to-protected switch,
  execute the frozen protected fixture, perform the symmetric checked
  protected-to-management switch, validate the final management event, and
  issue only the allowlisted SRST shutdown with QEMU exit status `0`.
- Each switch performs exactly one target HGATP write while `V=0`, one local
  `HFENCE.GVMA x0,x0`, and one verified readback, in that order, before the
  target's active state is published. Observed published roots are
  `0x800000000008021c` (protected) and `0x8000000000080214` (management),
  both immutable R2 products. No PTE or root is edited after seal.
- The protected fixture's denied private load is observed at PC `0x40011014`
  with `scause=21`; the denied shared store at PC `0x40011024` with
  `scause=23`, leaving shared backing unchanged; the protected switch event at
  PC `0x40011030` with `scause=10`; and the final management event at PC
  `0x40010038` with `scause=10`.
- Isolation observations recorded for this scenario: management read of
  protected-private denied; protected read of management-private denied;
  protected store to shared denied; protected read of shared permitted;
  management store to shared permitted.
- GCC and Clang host runs each cover 32 scenarios and 9,707 assertions with
  identical result streams. GCC/GNU-ld and Clang/lld images have semantic
  parity, explicitly `byte-equality=not-claimed`.
- The evidence report schema is `be-r5-checked-switch-v1`. Report generation
  is deterministic for a fixed checked input set (byte-identical on
  regeneration); cross-launch determinism is claimed only as canonical
  semantic equality.
- A fresh checkout with no `build/` directory and no manually created scratch
  reaches the same results: scratch is prepared parent-first and confined to
  the repository root, and every normative tool role is probed under both the
  R5-owned and the inherited R3 clean environment.

### Trusted or assumed

- Pinned OpenSBI (`qemu-system-riscv-core-10.2.2-1.fc44.x86_64`, firmware
  SHA-256 `49bdf7b939bda11321132d1042bf99d7324fb190f1feef423171fed3573f8705`),
  QEMU, the ratified RISC-V privileged architecture, GCC, Clang, GNU ld, lld,
  the assembler/disassembler, Node, GNU Make, and inspected-to-executed
  assembly correspondence.
- The exact accepted R3 and R4 inputs, the fixed compiled fixtures, monitor
  memory integrity, the trusted stacks, caller storage, the single-hart
  environment, and the M-mode/PMP/delegation/debug setup outside the bounded
  checks.
- `vsatp` remains `Bare` in this profile, so no VS-stage fence is exercised.

### Unavailable or `NOT RUN`

- Hardware and K3 validation are **NOT RUN**.
- Formal proof, refinement, and verification are **NOT RUN and not claimed**.
- R6 adversarial-image completion and R7 exact-byte or source-to-binary proof
  are not started.
- There is no negative *image* test in R5; compiled adversarial image fixtures
  remain R6 scope.
- Byte-identical raw QEMU traces, generated reports, or whole evidence bundles
  across independent launches are not established.

### Explicitly not implemented

- Multi-switch scheduling, more than two domains, preemption, interrupts,
  timers, DMA, devices, guest SBI beyond the allowlisted SRST shutdown,
  multicore, Linux, service, or policy semantics.
- Arbitrary-guest isolation, complete adversarial coverage, production
  readiness, certification, and public release.
- CHERI or Type Enforcement selection or behavior.
- No Model 0.1/0.2 proof or C-refinement result and no Helium claim or proof
  transfers to R5.

## 4. Load-bearing invariants

| Invariant | Contract | Implementation | Test / evidence |
| --- | --- | --- | --- |
| Only exact accepted R4 `COMPLETE` state enters R5 | `include/be/r5.h`: R4 import contract and `BE_R5_PHASE_IMPORT_R4_COMPLETE`; `struct be_r4_frame` reused unchanged | `virt/be/r5.c` import/validation; `arch/riscv/be/r5-runtime.c` | Host import negatives; `tests/r5/check-image.mjs` accepted R3/R4 installation check; R1-R4 acceptance checkers report `accepted_mechanism_match=yes` |
| A target is entered only after write, fence, and verified readback succeed | Ordered switch transaction and `PENDING_* -> *_FENCED -> *_PUBLISHED_*` phases in `r5.h` | `virt/be/r5.c` pending construction and publication decision; `arch/riscv/be/r5-trap.S`, `r5-runtime.c` CSR/fence/readback boundary | Host phase/ordering negatives; image checker requires the two ordered write/fence/readback triples; six QEMU traces record exactly one write, one fence, one readback per switch |
| The pending binding is monitor-formed, never guest-selected | `struct be_r5_pending`, fixed protected binding constants (vCPU `2`, root `102`, saved-state `2`, guest SP `0x40002000`, trusted SP `0x8022a000`, saved PA `0x8022c000`) | `virt/be/r5.c` builds one complete pending target from frozen contract values | Host binding negatives; image checker rejects a guest-influenced or incomplete binding |
| Failure is sticky and terminal; there is no rollback or alternate target | `BE_R5_PHASE_FAILED` with no recovery edge; stable `enum be_r5_error` classes | `virt/be/r5.c` clears retained authority; the runtime halts rather than re-entering | Host terminal negatives; image checker requires the absence of an R6 or fallback path; QEMU runs show no re-entry after the final event |
| Guest state is never trusted for trap entry or restore | Trusted-stack/`sscratch` contract; unchanged 320-byte frame ABI | `arch/riscv/be/r5-trap.S` swaps `sscratch` before stack use; no-call restore/`SRET` tail | Image checker requires the swap, fixed frame offsets, and a call-free tail; host frame-mode negatives |
| Roots and PTEs are immutable after seal | Immutable R2 root identities in `r5.h`; no PTE mutation interface | `virt/be/r5.c` and `arch/riscv/be/r5-runtime.c` install roots by value only | Image checker records roots/PTEs immutable after seal; report isolation table; six QEMU traces |
| Evidence, tools, and scratch cannot be substituted or redirected | `tests/r5/tool-lock.conf` bound to accepted `tests/r3/tool-lock.conf`; checked-launcher contract | `tests/r5/run-make.sh`, parse-time Make preflight, `check-tools.sh`, `prepare-scratch.sh`, `probe-tool-versions.mjs` | 115 rejected hostile-control cases; 36 roles × 2 environments = 72 version probes; 477 fresh-bootstrap checks; 12 QEMU artifact mutations per toolchain and 34 report mutations rejected |
| Automation cannot manufacture R5 acceptance | `tests/r5/check-accepted-content.mjs` forbidden-target list, fail-closed content binding | `tests/r5/check-acceptance.sh` reports status only | `tests/r5/test-acceptance-content.mjs` rejects inconsistent acceptance/plan/record/digest combinations; at the target, status was `r5_acceptance=not-reviewed`, `r5_accepted_commit=none`, and the acceptance record can only report the exact human-named commit, never the plan, decision record, parent, or review packet |

## 5. Review history and resolved findings

All substantive automated findings raised during implementation were resolved
inside the reviewed range. Recording them is part of the packet; none of these
closures constitutes acceptance.

| Finding | Severity as assessed | Resolution |
| --- | --- | --- |
| GNU Make forged-success controls were only partially refused: clustered short options (`-ik`, `-ki`) and letter-only flag words (`MAKEFLAGS=i`, `MAKEFLAGS=k`, `MAKEFLAGS=n`, `GNUMAKEFLAGS=ik`, `MFLAGS=-ik`) could reach a recipe | High: a hostile control could produce a success banner without running the checks | `tests/r5/make-control.mjs` was rewritten to validate against an allowlist rather than a list of forbidden spellings, and is enforced both in the launcher and at Make parse time. `tests/r5/test-tool-binding.mjs` now rejects 115 cases (53 launcher, 28 raw command line, 30 raw environment, 2 unpinned-Make, 1 foreign directory, 1 control argument) |
| Two factual inaccuracies in the R5 evidence document, and determinism wording that read as byte-level | Medium: documentation overclaim | Both inaccuracies corrected; determinism is now stated as byte-identical report regeneration for a fixed checked input set plus canonical semantic equality across launches |
| Raw QEMU `-d in_asm,cpu` traces varied between independent invocations | Low: benign, outside the checked sequence | Variation was localized to two pre-guest areas (TCG boot-ROM block splitting and an OpenSBI boot-time counter-derived register probe), bounded in the checkers, and explicitly excluded from any byte-reproducibility claim |
| A fresh checkout failed because the R5 boundary silently inherited the accepted R3 clean environment's `build/r3/tmp`, which R3 names but never creates; the inherited version reader then reported a misleading executable "version drift" for what was a scratch fault | High: a clean-clone reviewer would see a false tool-identity failure and no true diagnosis | `tests/r5/prepare-scratch.sh` and `tests/r4/prepare-scratch.sh` create and confine the required components before any pinned tool runs, under their own diagnostic name; `tests/r5/probe-tool-versions.mjs` probes 36 normative roles under both the R5-owned and inherited R3 environments. No locked tool identity was relaxed |
| R5 scratch preparation could have been satisfied by a symlinked or out-of-repository component, and the inherited environment was not probed | Medium: scratch escape and an undetected environment gap | Preparation is parent-first and refuses symlinks before traversal, re-checks after `mkdir`, and requires each component's physical path to equal its repository path; `tests/r5/test-fresh-bootstrap.mjs` adds 477 checks over a build-absent checkout covering both the R4 and R5 boundaries |
| Independent core and runtime review of the contract, transaction, and assembly boundary | No significant findings | No change required |
| Final rereviews of the complete range | No remaining defects found | No change required |

**Open:** the VitePress generated-asset byte-reproducibility finding remains
open and unresolved. Functional documentation, link, and browser gates pass,
but regeneration can produce different hash-named JavaScript assets. This is
not a functional documentation failure, is not resolved by this packet, and
should not be read as byte reproducibility. Human judgment remains required on
scope, claims, trust assumptions, and this finding.

## 6. Exact-target validation and retained evidence

The following ran on 2026-07-30 against the clean exact target
`165f4d001a2b59b582b397bdea79ec4826168fdb`, not merely equivalent pre-commit
content. Each ran in its own **fresh detached worktree checked out at the
exact target**, with **no manually created scratch directories** and no
inherited `build/` tree, so each command had to bootstrap itself. Each was the
**first** invocation in that worktree. The ephemeral worktrees were removed
afterwards.

| Scenario / command | Result and coverage |
| --- | --- |
| Fresh detached worktree 1: first `./be r5-check` | **PASS**. Scratch prepared and confined; 36 roles × 2 environments = 72 version probes; 477 fresh-bootstrap checks; 115 hostile-control rejections; source inventory 27 inputs, digest `e1d47dd9be03844f29ed84bab30bef215eef5e2d7ae3499b4d1c3acc5e2bce0f`; host GCC and Clang each 32 scenarios / 9,707 assertions with identical streams; two semantically equivalent images (`semantic-parity=yes byte-equality=not-claimed`); three GCC plus three Clang QEMU runs with identical cross-toolchain semantics; 12 QEMU artifact mutations rejected per toolchain (12 × 2); 34 report mutations rejected; retained evidence of 12 logs and 2 manifests. |
| Fresh detached worktree 2: first `./be r4-check` | **PASS**, confirming the accepted R4 package still passes from a build-absent checkout after the shared scratch correction. |
| Fresh detached worktree 3: first full `make check` after lockfile `npm ci` | **PASS**: root wrapper, Helium, Model, R0 freeze, R1, checked R4, checked R5, and retained-evidence consistency. |
| Acceptance status at the exact target | `r5_implementation_content_match=yes` with content digest `f4b3dcaf95500a23fd6a08c97fa778b933587c536d4ab528941c205b7206911f`; `r5_dependencies_match=yes`; R1/R2/R3/R4 `accepted_mechanism_match=yes`; `r5_acceptance=not-reviewed`; `r5_accepted_commit=none`; `r6_authorization=not-authorized`; `r5_publication_scope=blocked`; `r5_hardware_validation=NOT-RUN`; `r5_formal_verification=NOT-RUN-not-claimed`. Those were the honest values **before** the decision; the later acceptance-record commit reports `r5_acceptance=accepted`, `r5_accepted_commit=165f4d001a2b59b582b397bdea79ec4826168fdb`, and `r5_accepted_mechanism_match=yes` over a different local-content digest, because the acceptance record itself changes the checked acceptance tooling. The R6, publication, hardware, and formal values are unchanged by the decision. |
| Observed final scenario values | Final management event reports `s0=17`, `a0=17`, `a1=34`; observed backings are management-private `17`, shared `34`, and protected-private `51`, matching the accepted plan's frozen fixture exactly. |

Retained R5 evidence is `build/r5/reports/checked-switch.json` and
`build/r5/evidence/` (report, 12 console/trace logs, two per-toolchain image
manifests, an aggregate `artifacts.sha256`, acceptance status, and a claim
ledger). `planning/single-hart-runtime-r5-evidence.md` is the authoritative
evidence and claim record.

**Reproducibility boundary.** Report generation is byte-deterministic for a
fixed checked input set. Cross-launch equality is claimed only semantically,
over canonical per-run trace tuples within and across toolchains, plus
identical hashes of the six retained console logs of a run set. Raw QEMU
traces, generated reports, and whole evidence bundles are not claimed
byte-identical across independent launches. The generated VitePress asset
byte-reproducibility finding remains open and separate from both.

**Execution boundary.** The results above bind to commit
`165f4d001a2b59b582b397bdea79ec4826168fdb` only. The review packet and this
acceptance record are later follow-up commits; re-running any gate from a
follow-up commit or a dirty worktree validates that later content, not the
review target. Follow-up validation is recorded separately in
`planning/HANDOFF.md` and is not a substitute for the exact-target results.

## 7. Recommended human review sequence

Use an isolated detached worktree so unrelated local changes cannot affect the
review:

```sh
git worktree add --detach ../beryllium-r5-review 165f4d001a2b59b582b397bdea79ec4826168fdb
cd ../beryllium-r5-review
git status --short
git show --no-patch --format=fuller 165f4d001a2b59b582b397bdea79ec4826168fdb
git diff --check a8161e639af4a141e0d3ca1322202c91129724c7 165f4d001a2b59b582b397bdea79ec4826168fdb
```

1. Read `planning/single-hart-runtime-r5-plan.md` (accepted at
   `fecae6b62a507bdbb93d211262197a31f5422316`), its
   [plan review and acceptance record](single-hart-runtime-r5-plan-review-summary.md),
   the accepted R4 record, `planning/single-hart-runtime-r5-evidence.md`, and
   then this packet. Confirm the R5/R6 and claim boundaries first.
2. Inspect the complete implementation range, not only the corrective delta:

   ```sh
   git log --reverse --oneline a8161e639af4a141e0d3ca1322202c91129724c7..165f4d001a2b59b582b397bdea79ec4826168fdb
   git diff --stat a8161e639af4a141e0d3ca1322202c91129724c7 165f4d001a2b59b582b397bdea79ec4826168fdb
   git diff --find-renames a8161e639af4a141e0d3ca1322202c91129724c7 165f4d001a2b59b582b397bdea79ec4826168fdb -- include/be/r5.h virt/be/r5.c arch/riscv/be tests/r5
   ```

3. Review the contract and the fail-closed switch transaction, then the
   assembly/linker boundary and the static image checker. Ask whether a target
   can ever be entered before its write, fence, and verified readback all
   succeeded, and whether any partial publication can be resumed.
4. Review the corrective delta on its own terms, then confirm it changes only
   harness behavior:

   ```sh
   git diff 9312c1355a23d411e3bdafb2183be342683a8ab9 165f4d001a2b59b582b397bdea79ec4826168fdb
   ```

5. Review the evidence, tool-lock, scratch-confinement, and rejection graph.
   Check that QEMU remains emulation evidence, that image parity is semantic
   and not byte equality, and that no locked tool identity was relaxed to make
   a fresh checkout pass.
6. Confirm the acceptance surfaces cannot self-approve: `tests/r5/
   check-accepted-content.mjs` refuses the plan, packet, and decision-record
   commits as acceptance targets, and previously accepted R1-R4 content stays
   bound through its immutable, approved-delta, and added-file classes.
7. If reproducing, run the checked commands documented in the evidence record
   from a build-absent checkout; preserve the generated-asset result as an
   open reproducibility question. Remove the review worktree only after
   recording the human decision:

   ```sh
   cd -
   git worktree remove ../beryllium-r5-review
   ```

## 8. Human decision checklist

- [ ] The exact R5 scope matches accepted plan `fecae6b62a507bdbb93d211262197a31f5422316` and the R5/R6 boundary.
- [ ] Claims match the exact-target host, image, and QEMU evidence, including
  the semantic-not-byte parity and determinism wording.
- [ ] Trusted compiler, linker, firmware, emulator, Make/Node, monitor-memory,
  `vsatp=Bare`, and single-hart assumptions are acceptable.
- [ ] Negative paths cover unexpected observation, bad binding, wrong phase or
  ordering, partial publication, malformed event, sticky failure, evidence
  tampering, redirected scratch, and hostile Make/shell/tool controls
  sufficiently.
- [ ] The absence of a negative *image* test, and its deferral to R6, is
  acceptable for R5.
- [ ] R6 and every later successor, plus tag, push, publication, and release
  work, remain excluded.
- [ ] The open generated-asset byte-reproducibility finding is understood and
  remains open.
- [x] **Accept** exact commit `165f4d001a2b59b582b397bdea79ec4826168fdb`
  on 2026-07-30, by explicit instruction
  `accept exact 165f4d001a2b59b582b397bdea79ec4826168fdb`.
- [ ] Request revisions through a new commit and a new review packet.
- [ ] Defer the decision while preserving current gates.

Only the acceptance-decision box is checked because that decision was
explicitly supplied by the responsible human. The technical-judgment
checklist remains unchanged as review history; no signature is generated.

## 9. Recorded decision and remaining boundaries

- **Recorded acceptance:** exact implementation target
  `165f4d001a2b59b582b397bdea79ec4826168fdb` is accepted as of 2026-07-30.
  The accepted implementation spans that target and its immediate parent
  `9312c1355a23d411e3bdafb2183be342683a8ab9`, under accepted plan
  `fecae6b62a507bdbb93d211262197a31f5422316` and authorization record
  `a8161e639af4a141e0d3ca1322202c91129724c7`.
- **Packet boundary:** review packet commit
  `9bb89fe196740c5e3252bdccced6fb202df65e55`, and the later commit that
  records this decision, remain decision support, not accepted
  implementation. Neither may be substituted for the accepted target.
- **Evidence boundary:** acceptance adds no new validation. The exact-target
  results in section 6 remain the evidence boundary; no run from a dirty
  follow-up worktree is claimed as exact-target validation. Hardware
  validation stays `NOT RUN`, and formal verification stays not claimed.
- **Successor and release boundary:** this R5 acceptance authorizes no
  successor. R6 and every later package remain not authorized and not
  started, and require their own separately accepted bounded plan and
  separate implementation authorization. No push, tag, public release,
  publication-gate change, or hardware claim is authorized.
- **Open findings:** the generated-asset byte-reproducibility finding remains
  open; acceptance does not resolve or close it. The raw-trace byte
  non-identity boundary and the semantic-not-byte image parity limit stand
  exactly as recorded.
- **Future revisions:** any technical change to accepted R5 inputs requires a
  new exact target and a new explicit responsible-human decision; it does not
  silently inherit this acceptance.

---

**Status:** exact target `165f4d001a2b59b582b397bdea79ec4826168fdb` is
implemented at the bounded R5 checked-switch scope, passed the recorded
exact-target validation, and was responsible-human accepted on 2026-07-30.
Review packet commit `9bb89fe196740c5e3252bdccced6fb202df65e55` and this
acceptance record are not accepted implementation. R6 and every later
successor remain not authorized and not started. Hardware validation is
`NOT RUN` and formal verification is not claimed. Push, tag, publication, and
release remain blocked.

**Next:** independently review this acceptance record and keep R6+ gated. Do
not amend the accepted R5 target or the review packet commit.

**Action required from you:** review the uncommitted acceptance record for
accuracy. No further acceptance choice, R6 authority, or release authority is
implied.
