<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R3 review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves packet-time references to former private repository
> `jamorris_microsoft/beryllium`, its remotes, dependency layout, and
> historical absolute checkout paths. The current active private repository is
> `beryllium-project/beryllium-hypervisor`. Use
> [project orientation](project-orientation.md) for current commands; do not
> reinterpret historical remote-containment or publication facts.

## Decision record

The responsible human explicitly accepted the exact R3 implementation target
on 2026-07-29 with this instruction, preserved verbatim:

```text
accept  6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
```

The accepted implementation is only
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`, whose immediate parent is
`86a4cd38bfc9d47794cba2d26c5b7dc777c5d835` and whose whole-R3 base is
`3024e79867911cbdd47085832b7a64f713970f65`. Follow-up commit
`fcc0f267a1f59241f872c0a1d2a371a95a58cba6` is the review packet and
decision-support follow-up; it is **not** an accepted implementation target.
Acceptance does not erase trusted assumptions, `NOT RUN` items, resolved
findings, or the open VitePress hash-named-asset reproducibility finding. It
does not authorize R4, hardware claims, a tag, a push, public release, or a
publication-gate change.

## 1. Decision summary

| Field | Required content |
| --- | --- |
| Review target | Exact commit `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` (`runtime: make R3 evidence commit-safe`), with immediate parent `86a4cd38bfc9d47794cba2d26c5b7dc777c5d835` (`runtime: implement single-hart R3 entry`) |
| Current status | R3 is separately authorized, implemented at the bounded boot-and-first-entry boundary, exact-target tested, and **responsible-human accepted** at exact commit `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` on 2026-07-29. |
| Decision recorded | Accepted exact commit `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`; no packet or follow-up commit is accepted as implementation. |
| Successor status | At this exact R3 decision boundary, R4 had not started and was not authorized; this review itself authorized no successor work. Subsequently, responsible-human review accepted exact R4 target `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29. Its implementation parent `6e5c55c59e94bbaba136269c784db28ec1b53f54` and decision-support follow-up `ec7be2f146a851e7608e77eb2875076e66aab2e6` remain distinct. R5 was later separately accepted at exact target `165f4d001a2b59b582b397bdea79ec4826168fdb` on 2026-07-30. R6 and every later successor remain gated, not authorized, and not started; publication remains blocked. |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`; the target is absent from remote refs and tags, no push or tag has occurred, and Beryllium public release remains blocked. |

The remaining action is independent review of this acceptance record and its
fail-closed tooling integration, without changing the accepted target.

### Exact identity and lineage

| Item | Exact value |
| --- | --- |
| Branch | `beryllium/single-hart-runtime-r0` |
| Whole-R3 comparison base | `3024e79867911cbdd47085832b7a64f713970f65` |
| Main implementation commit | `86a4cd38bfc9d47794cba2d26c5b7dc777c5d835` |
| Corrective review target | `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` |
| Remote state before this packet | Branch was seven commits ahead of `origin/beryllium/single-hart-runtime-r0`; no remote ref contained the target |
| Tag state | No tag contained the target |
| Commit metadata | Required `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` trailer is present on both R3 commits; no human `Signed-off-by` is present |

The target is the second of two R3 commits after the whole-R3 base. Review the
whole range
`3024e79867911cbdd47085832b7a64f713970f65..6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`,
not only the corrective parent-to-target delta.

## 2. Deliverables

### Exact changed-file inventory

`git diff 3024e79867911cbdd47085832b7a64f713970f65
6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` reports:

- **119 paths**, 11,167 insertions, 434 deletions;
- **44 non-generated paths**, 10,702 insertions, 150 deletions; and
- **75 generated documentation paths**, 465 insertions, 284 deletions:
  44 HTML pages, 30 hash-named assets, and `docs/html/hashmap.json`.

The corrective range
`86a4cd38bfc9d47794cba2d26c5b7dc777c5d835..6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`
reports:

- **90 paths**, 728 insertions, 367 deletions;
- **18 non-generated paths**, 506 insertions, 153 deletions; and
- **72 generated documentation paths**, 222 insertions, 214 deletions.

| Deliverable | Paths | Purpose | Trust / privilege boundary | Most important human review question |
| --- | --- | --- | --- | --- |
| R3 contract and mechanism | `include/be/r3.h`, `virt/be/r3.c` | Define the one-way R3 phase/error contract; validate handoff, image, SBI, accepted R1/R2 state, HS/VS reset state, binding preparation/publication, bounded DBCN progress, and terminal failure | Restricted C used by the privileged runtime; no direct CSR or SBI instruction in the mechanism file | Does the state machine fail closed and prevent active-binding publication or entry before every prerequisite is complete? |
| Eight-file privileged RISC-V runtime/linker boundary | `arch/riscv/be/beryllium.lds`, `entry.S`, `freestanding.c`, `guest.S`, `platform.c`, `privileged.S`, `r3-platform.h`, `runtime.c` | Link the fixed image; receive the pinned OpenSBI handoff; perform SBI calls, HS/VS reset, HGATP/fence/readback, deterministic entry setup, and first management entry | First privileged Beryllium implementation; trusts pinned OpenSBI below HS and the architecture/compiler/linker correspondence; contains the sole CSR/SBI/HFENCE/SRET boundary | Are the linker assertions, reset state, HGATP/fence/readback order, final `SPP=1 -> SRET` sequence, and non-R4 halt paths exact and complete? |
| Nineteen-file accepted-target `tests/r3/` evidence package | `tests/r3/Makefile`, `check-acceptance.sh`, `check-image.mjs`, `check-image-parity.mjs`, `check-qemu-artifacts.mjs`, `check-report.mjs`, `check-tools.sh`, `generate-evidence.sh`, `generate-report.mjs`, `make-control.mjs`, `r3-check.c`, `run-make.sh`, `run-qemu.sh`, `test-qemu-artifact-integrity.mjs`, `test-report-rejection.mjs`, `test-tool-binding.mjs`, `tool-lock.conf`, `tool-lock.mjs`, `verify-tool-lock.mjs` | Provide GCC/Clang host tests, linked-image semantics, six bounded QEMU traces, exact artifact manifests, deterministic reports, negative evidence tests, tool binding, checked Make invocation, retained hashes, and the target's then-review-required status | Host/emulation/evidence infrastructure; it does not turn QEMU into hardware evidence. Follow-up acceptance tooling records, but does not create, the human decision. | Do the independent and adversarial checks reject missing, reordered, forged, substituted, stale, or success-shaped evidence? |
| Wrapper and status surface | `be`, `scripts/check-be.sh` | Add stable R3 commands, compose the repository gate, preserve a separate non-evidence preview, and keep repository/publication status blocked | No runtime authority; command/status orchestration only | Can any wrapper, environment, dry-run, or component-publication path report R3 success or Beryllium release approval without executing the normative checks? |
| Maintained Markdown, policy, and navigation | `.github/copilot-instructions.md`, `README.md`, `pathfinder/tests/check-docs-render.mjs`, `planning/.vitepress/config.mts`, `planning/HANDOFF.md`, `planning/README.md`, `planning/implementation-plan.md`, `planning/research-synthesis.md`, `planning/roadmap.md`, `planning/single-hart-runtime-plan.md`, `planning/single-hart-runtime-r2-evidence.md`, `planning/single-hart-runtime-r2-review-summary.md`, `planning/single-hart-runtime-r3-evidence.md` | Record the bounded claim, authorization/review status, commands, open findings, R4 boundary, and browser inventory | Markdown is normative; policy and prior accepted R1/R2 claim boundaries must remain unchanged | Do all maintained claims distinguish authorization, implementation completion, exact-target validation, human acceptance, and public release? |
| Derivative generated planning site | `docs/html/**` | Render the maintained planning Markdown for static and HTTP review | Generated and non-normative; hash-named asset byte reproducibility remains unresolved | Are the generated pages functionally correct and link/browser-render complete without treating byte instability as resolved? |

The corrective target fixes evidence identity, status, tool/Make controls, and
maintained prose. It does not amend the parent and does not change the R3
contract/mechanism or eight privileged runtime/linker files. The review packet
and its original navigation update are committed separately at
`fcc0f267a1f59241f872c0a1d2a371a95a58cba6`; the current acceptance-record
tooling/docs are an uncommitted follow-up. Neither is part of the accepted
implementation inventory or exact-target evidence.

## 3. Claim boundary

### Supported by the exact target

- The pinned OpenSBI handoff is accepted only for hart zero at the exact
  linked entry, the firmware pointer is recorded but not dereferenced, and
  the image validates the frozen layout plus exact SBI Base version and
  separate DBCN/SRST extension probes.
- The accepted R1 flow executes unchanged and its accepted mechanism inputs
  match `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb`.
- R2 builds both Sv39x4 trees in the actual linker-reserved physical pools,
  produces the exact management/protected HGATP values, and independently
  re-walks all six leaves. The accepted R2 implementation inputs match
  `6e1cb579257c5dbe3234bd484fd091629e87181b`.
- The bounded HS/VS reset state is written, read back, and checked before
  entry.
- Management `HGATP=0x8000000000080214` is written, followed by local
  `HFENCE.GVMA x0,x0`, exact readback, and only then active publication.
- Static image inspection and all six ordered QEMU traces establish the exact
  R3 `sstatus.SPP=1 -> SRET` sequence before the management block where QEMU
  reports `V=1` at `pc=0x40010000`. The VS conclusion uses both pieces of
  evidence; QEMU does not provide a standalone `VS` privilege label.
- Strict GCC/GNU-ld and Clang/lld images have checked semantic parity. Their
  bytes and hashes legitimately differ; byte equality is not claimed.
- R3 ends at an externally observed bounded timeout after the first
  management instruction because no R4 completion/trap protocol exists.

### Trusted or assumed

- Pinned OpenSBI and QEMU behavior.
- The ratified RISC-V privileged architecture and SBI specifications.
- GCC/GNU-ld, Clang/lld, assembler, disassembler, ELF inspection, and the
  correspondence between inspected instructions and executed behavior.
- M-mode setup, PMP/ePMP, delegation, debug exclusion, and writable-monitor
  assumptions outside the bounded HS checks.
- The fixed compiled inventory/proposal input and caller-owned R1/R2/R3
  storage.
- The local-hart meaning of `HFENCE.GVMA x0,x0`; no cross-hart property is
  claimed.
- There is no Model 0.2-to-C or Model 0.2-to-runtime refinement result.

### Unavailable or `NOT RUN`

- K3 or other hardware validation: **NOT RUN**.
- Protected-domain entry and second-domain execution: **NOT RUN**.
- Private/shared access and guest-page-fault isolation evidence:
  **NOT RUN**.
- A skipped-fence runtime fixture: not implemented.
- Exact-byte or open source-to-binary proof: **NOT RUN**.
- Full runtime completion: not implemented.
- Formal verification of R3 or a Model 0.2 refinement: unavailable.

### Explicitly absent

- No R4 trap frame, trap classification, context save/restore, or private
  event protocol.
- No checked root switching, protected entry, second-domain execution, or
  successful guest completion/shutdown path.
- No Linux, guest-visible SBI, service semantics, device, DMA, interrupt,
  timer, multicore, scheduler, migration, overcommit, capability, TE, or
  runtime-policy implementation.
- No arbitrary-guest-isolation, complete noninterference, production,
  certification, hardware, or public-release claim.
- The minimal unexpected-trap sink only disables bounded interrupt paths and
  halts; it is not a partial R4 handler.
- Helium and Model 0.2 evidence remain separate and do not validate R3.

## 4. Security and correctness invariants

| Load-bearing invariant | Contract | Implementation | Test / evidence |
| --- | --- | --- | --- |
| Exact handoff, image, and SBI prerequisites precede runtime state | `include/be/r3.h`: boot/layout structures, frozen constants, `be_r3_validate_boot()` and distinct error classes | `entry.S`, `beryllium.lds`, `platform.c`, `runtime.c`, `virt/be/r3.c:image_layout_valid()` and `be_r3_validate_boot()` | `tests/r3/r3-check.c` boot/layout/SBI mutations; `check-image.mjs` entry/symbol/section/PHDR/linker assertions; `check-report.mjs` firmware/image recomputation |
| Accepted R1 and R2 inputs remain the only mechanism dependencies | `be_r3_note_r1_derived()` and `be_r3_note_r2_built()` require exact phases, identity, roots, bindings, HGATP values, and leaves | `runtime.c` calls the accepted R1 flow, binds R2 to linker pools, independently re-walks, then advances R3; `virt/be/r3.c` rechecks the results | `r3-check.c` R1/R2 corruption cases; `tests/r1/check-acceptance.sh`; `tests/r2/check-acceptance.sh`; retained `r1-acceptance.txt` and `r2-acceptance.txt` |
| HS/VS state is reset and read back before binding preparation | `include/be/r3.h`: `be_r3_hs_state`, masks, `be_r3_note_hs_ready()` | `privileged.S:be_r3_arch_reset_state`; `runtime.c`; `virt/be/r3.c:hs_state_valid()` | `r3-check.c` mutates every zero-required field, `hstatus`, `stvec`, and post-reset SPP; `check-image.mjs` checks reset instructions and post-reset `SPP=0` |
| No active binding is published before HGATP write, local fence, and exact readback | `be_r3_prepare_management_binding()`, `be_r3_publish_management_binding()`, `be_r3_arm_management_entry()` and pending/active binding separation | `privileged.S:be_r3_arch_install_management()` executes `csrw hgatp -> hfence.gvma x0,x0 -> csrr hgatp`; `runtime.c` publishes only after readback; `virt/be/r3.c` clears bindings on failure | `r3-check.c` wrong fence/readback/pending/active cases; `check-image.mjs` instruction order; six QEMU traces; `check-report.mjs` transition recomputation |
| Initial entry is VS, not VU, at the exact management PC | `include/be/r3.h`: management PC/stack and `BE_R3_SSTATUS_SPP`; entry may be armed only for the exact active binding | `privileged.S:be_r3_arch_enter_management()` writes HS `sepc`, initializes every guest GPR, sets `SPP=1` immediately before `sret`; `guest.S` supplies the first management instruction | `check-image.mjs` exact unique SPP/SRET order; `check-qemu-artifacts.mjs` requires SPP in the SRET CPU state and SRET before the unique `V=1`, `pc=0x40010000` block; both artifact-negative suites reject reorder/duplicate/tamper |
| Failure is sticky and R3 has no hidden success or R4 path | `BE_R3_PHASE_FAILED`, `be_r3_fail()`, bounded DBCN progress, frozen SRST results | `virt/be/r3.c`, `platform.c`, `runtime.c:runtime_fail()`, `privileged.S` halt/trap sink, `guest.S` infinite loop | `r3-check.c` terminal, DBCN, and SRST negatives; `run-qemu.sh` and `check-qemu-artifacts.mjs` accept only timeout 124 after ordered entry evidence; report non-claims |
| Retained evidence is exact-schema, independently grounded, and cannot substitute a follow-up for the accepted target | `tests/r3/check-acceptance.sh` names the exact accepted target/date and requires accepted-content match; report identity separates fixed base, dynamic generation HEAD/state, accepted review target, and packet follow-up | `check-accepted-content.mjs` byte-compares 38 immutable paths and exact-validates approved deltas for nine mixed files, including the R1 and R3 acceptance checkers; report/evidence tools recompute repository, source, tool, firmware, image, trace, status, and artifact identities | Focused acceptance drift tests plus `test-report-rejection.mjs` forged base, HEAD, ancestry, state, acceptance, date, match, packet, target, source, tool, QEMU, firmware, and schema cases; deterministic double generation; exact 12-log/two-summary manifest |
| Normative execution cannot be replaced by hostile Make/tool controls | `tool-lock.conf` binds 42 roles; `run-make.sh` is the checked boundary; externally supplied internal `BE_R3_*` controls are forbidden | `tool-lock.mjs`, `verify-tool-lock.mjs`, `make-control.mjs`, `run-make.sh`, parse-time `Makefile` preflight, wrapper separation of non-evidence `BE_DRY_RUN` | `test-tool-binding.mjs` real subprocess negatives for dry-run/touch/question/eval/alternate-file/include/timestamp/override/shell/PATH/manifest cases; `check-tools.sh`; report tool recomputation |

## 5. Review history and resolved findings

The following substantive findings were exposed during implementation,
adversarial review, or exact-target validation. Closed findings are present
in the target; recording closure is not responsible-human acceptance.

| # | Finding | Closure and evidence |
| --- | --- | --- |
| 1 | **The frozen global C `-march` omits H.** H instructions were required without silently changing the accepted global architecture string. | `arch/riscv/be/privileged.S` uses local `.option arch,+h` only around the explicit H boundary and emits a truthful H ELF attribute. `tests/r3/check-image.mjs` and `check-image-parity.mjs` require H in both final images while F/D/V remain absent. |
| 2 | **SBI version and extension availability were initially conflated.** | `platform.c`, `runtime.c`, and `virt/be/r3.c` now require the exact encoded SBI specification version and independently probe DBCN and SRST. `r3-check.c` has separate negative cases; the report recomputes each result. |
| 3 | **Initial-PC terminology confused HS `sepc` with reset VS `vsepc`.** | The contract, `privileged.S`, plan, and evidence now distinguish HS `sepc=0x40010000` from reset `vsepc=0`. `check-image.mjs` checks the actual entry wrapper. |
| 4 | **A successful R3 shutdown would have imported R4 behavior.** | `guest.S`, `run-qemu.sh`, `check-qemu-artifacts.mjs`, and the report define success only as ordered first-entry evidence followed by externally bounded timeout. No post-entry trap/shutdown protocol was added. |
| 5 | **GCC/Clang parity was initially at risk of being described as byte equality.** | `check-image-parity.mjs` checks semantics and fixed security layout while retaining separate image hashes and explicitly reporting `byte-equality=not-claimed`. |
| 6 | **Critical VU-versus-VS defect: the original entry wrapper left SPP clear.** | `privileged.S` now keeps post-reset SPP clear, then sets `SPP=1` immediately before `SRET` and clears the scratch GPR. `check-image.mjs` enforces the exact static sequence; all six traces require SPP in the SRET state before QEMU `V=1` at the management PC. |
| 7 | **QEMU retention failed open through wildcard hashing and missing-log tolerance.** | `tests/r3/Makefile`, `run-qemu.sh`, and `check-qemu-artifacts.mjs` require exactly 12 logs and two summaries. `test-qemu-artifact-integrity.mjs` rejects deletion, tampering, reordered entry, duplicate SRET, altered markers, and extra files for both toolchains. |
| 8 | **The initial report checker accepted fabricated or asserted evidence fields.** | `generate-report.mjs` and `check-report.mjs` use an exact schema and independently recompute source, repository, tool, firmware, image, trace, status, claim, and non-claim facts. `test-report-rejection.mjs` rejects forged identity/status and prior fabricated-report patterns. |
| 9 | **Tool substitution and PATH overrides could undermine the evidence graph.** | The 42-role `tool-lock.conf` binds invocation path, resolved path, version, executable hash, owning package, and compiler subtools. `verify-tool-lock.mjs`, `check-tools.sh`, `test-tool-binding.mjs`, and report checking reject overrides, shadows, and tampering. |
| 10 | **Trace evidence did not originally enforce the load-bearing order.** | `check-qemu-artifacts.mjs` now requires one unique R3 SPP block and one unique SRET block, adjacency, SPP in the SRET CPU state, and that block before the unique management `V=1` block. The artifact-negative test covers reorder and duplication with recomputed hashes. |
| 11 | **GNU Make dry-run, touch, question, eval, alternate-file, and timestamp controls could bypass real execution.** | `make-control.mjs`, `run-make.sh`, the `Makefile` parse-time preflight, and `test-tool-binding.mjs` add checked-launcher rejection plus real subprocess negatives. The documented direct-Make limitation remains explicit. |
| 12 | **Internal `BE_R3_MAKE_DRY_RUN` produced success-shaped output without evidence.** | The normative launcher preview was removed and all externally supplied internal `BE_R3_*` controls now reject, including empty/zero values. The separate documented top-level `BE_DRY_RUN` remains explicitly non-evidence and is covered by `test-tool-binding.mjs`. |
| 13 | **Publication status coupled Beryllium release to the Helium component gate and left stale prose.** | `be`, `scripts/check-be.sh`, and maintained documentation now keep Beryllium repository/public release unconditionally blocked under the clean-repository process and label the Helium gate separately. |
| 14 | **First immutable candidate `86a4cd38...` had a self-reference defect.** Its report bound generation HEAD to the pre-commit base while maintained prose said no immutable target existed. | The target was superseded without amend. `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` separates fixed implementation base, dynamic generation HEAD/state, and external review target. `check-report.mjs` and forged identity/status negatives enforce that split. |
| 15 | **Exact validation of `86a4cd38...` was blocked by the self-reference defect.** | That blocked result remains part of the review history and is not represented as a pass. Exact detached validation of corrected target `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` passed; the automation-local bundle retains the command and boundary records. |

### Open finding requiring human judgment

VitePress hash-named generated assets are not byte-reproducible across builds.
Functional links, direct-file rendering, and browser-render gates pass. The
finding remains **unresolved**: this packet does not classify it as accepted,
resolved, or harmless.

## 6. Exact-target validation and retained evidence

### Exact detached-target validation completed 2026-07-29

Validation ran in a detached worktree at exact target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`. Tracked files were clean before
and after. The only worktree addition was the named untracked dependency link
`node_modules -> /home/jamorris/src/beryllium/node_modules`; the generated
report truthfully records that untracked state rather than calling the whole
directory clean.

| Command or check | Result | Exact boundary / coverage |
| --- | --- | --- |
| `./be clean` | **PASS** | Removed regenerable outputs before the exact-target run |
| `./be check` | **PASS** | Repository gate, including R3 host/image/QEMU/report/evidence checks; Model and Helium results remain separately scoped and do not validate R3 |
| `./be docs-check` | Functional **PASS** | Planning/Helium links, direct-file rendering, and browser rendering passed; hash-named generated-asset byte reproducibility remains open |
| `tests/r3/run-make.sh r3-report` | **PASS** | Normative checked launcher; both images, semantic parity, exact QEMU artifacts, deterministic report, independent checker, and report-rejection tests |
| `tests/r3/run-make.sh r3-evidence` | **PASS** | Clean-target retained source/tool/firmware/object/artifact/status bundle generation |
| `tests/r1/check-acceptance.sh --require` | `accepted`, mechanism match `yes` | Accepted R1 inputs unchanged |
| `tests/r2/check-acceptance.sh --require` | `accepted`, mechanism match `yes` | Accepted R2 inputs unchanged |
| Exact-target `tests/r3/check-acceptance.sh` | `review-required` | Historical status at the immutable implementation target before the later human decision |
| Follow-up `tests/r3/check-acceptance.sh` | `accepted`, exact target/date, mechanism match `yes` | Records the explicit decision while keeping packet/current HEAD distinct |
| Follow-up `tests/r3/check-acceptance.sh --require` | **PASS** | Requires accepted status plus exact accepted-content match |
| Tool/Make/internal-control negative checks | **PASS** | Dry-run/eval/alternate-file/internal-control/tool override/PATH shadow/manifest tamper cases rejected |
| QEMU artifact integrity negatives | **PASS**, GCC and Clang | Missing, tampered, reordered, duplicated, marker-altered, and extra artifacts rejected |
| Report rejection suite | **PASS** | Forged base/HEAD/ancestry-state/acceptance/review-target/source/tool/QEMU/firmware/schema cases rejected |
| `git diff --check` | **PASS** | Exact-target diff hygiene |
| K3 or other hardware | **NOT RUN** | No hardware claim |

Observed R3 results:

- GCC host: 128 scenarios / 704 assertions.
- Clang host: 128 scenarios / 704 assertions.
- QEMU: three GCC and three Clang ordered traces.
- Each accepted trace contains the exact R3 SPP/SRET sequence before the
  management block with `V=1` at `pc=0x40010000`.
- Each run ends with the expected bounded timeout; timeout alone is not
  sufficient evidence.

### Pre-commit, first-target, exact-target, and packet boundaries

- Pre-commit and parent-candidate testing informed implementation review, but
  the first immutable candidate `86a4cd38...` could not pass exact-target
  report validation because of the self-reference defect.
- The corrective commit was created without amending the parent.
- Exact-target validation passed only for
  `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`; that remains the sole accepted
  implementation target.
- Packet commit `fcc0f267a1f59241f872c0a1d2a371a95a58cba6` and the current
  uncommitted acceptance-record/tooling worktree are follow-ups. Current
  validation checks acceptance-record integration and reruns unchanged
  accepted technical content; the prior detached run remains the exact-target
  validation.

### Automation-local, noncommitted exact evidence

The exact-target evidence bundle is retained locally at:

```text
/home/jamorris/.copilot/session-state/6444e78c-d448-405e-88d1-9c90b875e4ea/files/r3-exact-evidence-6fb65b/
```

It is **automation-local and noncommitted**. It contains command logs,
commit/inventory/boundary records, the deterministic R3 report and checker
output, source/tool/firmware/object/artifact identities, both image-semantic
records, exactly 12 QEMU logs and two summaries, acceptance-status output,
and bundle hash verification. It is retained review evidence, not a
publication artifact or acceptance record.

Regenerable in-repository outputs are under `build/r3/` when the target gates
run. The maintained source of truth remains the target commit plus
`planning/single-hart-runtime-r3-evidence.md`; generated reports and
`docs/html/**` do not override it.

### Follow-up acceptance-record integration checks

The uncommitted follow-up worktree is checked with:

```sh
node tests/r3/test-acceptance-content.mjs
tests/r3/check-acceptance.sh --require
./scripts/check-be.sh
tests/r3/run-make.sh r3-check
./be check
npm run docs:build
./be docs-check
git diff --check
```

These checks cover accepted-content projection/drift semantics, status/report/
evidence integration, rerun the unchanged accepted technical content, and
validate Markdown, generated planning HTML, links, direct-file output, browser
rendering, and diff hygiene. They do not replace the prior detached exact-
target run and do not turn the follow-up HEAD into accepted implementation.

All requested follow-up commands passed on 2026-07-29:

| Command | Result | Follow-up boundary |
| --- | --- | --- |
| `node tests/r3/test-acceptance-content.mjs` | **PASS** | Immutable drift, mixed technical drift, allowed exact status delta, wrong SHA/date, review reversion, packet substitution, R4, publication, and invalid-argument semantics |
| `sh -n be scripts/check-be.sh tests/r3/check-acceptance.sh` | **PASS** | Shell syntax |
| R1/R2/R3 acceptance default and `--require` checks | **PASS** | R1/R2 still match their accepted inputs; R3 names exact target/date and reports mechanism match `yes` |
| `./scripts/check-be.sh` | **PASS** | Help/status/version and dispatch boundaries |
| Clean `./tests/r3/run-make.sh r3-check` | **PASS** | Acceptance integration plus unchanged host/image/six-run-QEMU/report/evidence content |
| `./be check` | **PASS** | Complete repository gate; component evidence remains separately labeled |
| `npm run docs:build` | **PASS** | Regenerated committed planning HTML |
| `./be docs-check` | **PASS** | 44 planning sources/45 HTML pages and 12 Helium sources/13 HTML pages; link, direct-file, and browser rendering gates |
| `./be status`, `./be help`, `./be version` | **PASS** | Accepted target/date/match and packet/current revision remain distinct |
| `git diff --check` | **PASS** | Follow-up diff hygiene |

An initial follow-up `./be check` run caught horizontal overflow in the
rendered acceptance-record invariant table. The prose was made wrap-safe; the
subsequent documentation gate and complete repository gate passed. This was a
follow-up documentation integration finding, not a change to the accepted R3
technical target.

## 7. Recommended human review sequence

### Prepare an isolated detached worktree

Use a disposable sibling worktree so local packet changes cannot affect the
exact target:

```sh
cd /home/jamorris/src/beryllium
git worktree add --detach ../beryllium-r3-review-6fb65b \
  6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
cd ../beryllium-r3-review-6fb65b
git status --short --branch
test "$(git rev-parse HEAD)" = \
  6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
```

### Bounded read-only review passes

1. **Confirm identity, lineage, metadata, and both inventories:**

   ```sh
   git --no-pager show --format=fuller --stat --summary \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
   git --no-pager log --reverse --format=fuller \
     3024e79867911cbdd47085832b7a64f713970f65..\
6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
   git diff --shortstat \
     3024e79867911cbdd47085832b7a64f713970f65 \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
   git diff --shortstat \
     86a4cd38bfc9d47794cba2d26c5b7dc777c5d835 \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
   git branch -r --contains \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
   git tag --contains \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
   ```

2. **Review policy, accepted scope, evidence, and the R4/publication
   boundary:**

   ```sh
   git --no-pager show \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d:LLM_POLICY_ALIGNMENT.md
   git --no-pager show \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d:planning/single-hart-runtime-plan.md
   git --no-pager show \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d:planning/single-hart-runtime-r3-evidence.md
   git --no-pager show \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d:planning/HANDOFF.md
   ```

3. **Review the architecture-neutral contract and mechanism first:**

   ```sh
   git --no-pager diff \
     3024e79867911cbdd47085832b7a64f713970f65 \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d -- \
     include/be/r3.h virt/be/r3.c
   ```

4. **Review the complete privileged boundary and linker map:**

   ```sh
   git --no-pager diff \
     3024e79867911cbdd47085832b7a64f713970f65 \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d -- \
     arch/riscv/be/beryllium.lds \
     arch/riscv/be/entry.S \
     arch/riscv/be/freestanding.c \
     arch/riscv/be/guest.S \
     arch/riscv/be/platform.c \
     arch/riscv/be/privileged.S \
     arch/riscv/be/r3-platform.h \
     arch/riscv/be/runtime.c
   ```

5. **Review the self-contained test/evidence package, emphasizing independent
   checkers and negative suites:**

   ```sh
   git --no-pager diff \
     3024e79867911cbdd47085832b7a64f713970f65 \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d -- \
     tests/r3
   ```

6. **Review the corrective commit separately so the self-reference,
   fail-open, Make/tool, status, and prose fixes are visible:**

   ```sh
   git --no-pager diff \
     86a4cd38bfc9d47794cba2d26c5b7dc777c5d835 \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d -- \
     tests/r3 be scripts/check-be.sh \
     README.md .github/copilot-instructions.md planning
   ```

7. **Confirm accepted R1/R2 implementation inputs remain byte-identical at
   the target:**

   ```sh
   git diff --exit-code \
     a6e0bb178c10a7e68c9447a8e58affb94b8ecadb \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d -- \
     Makefile arch/riscv/be/r0-layout.h \
     include/be/r0-config.h include/be/manifest.h \
     include/be/r1-config.h include/be/state.h include/be/types.h \
     tests/Makefile tests/r1/check-report.mjs \
     tests/r1/r1-check.c tests/r1/r1-report.c \
     virt/be/manifest.c virt/be/r1-config.c virt/be/state.c
   git diff --exit-code \
     6e1cb579257c5dbe3234bd484fd091629e87181b \
     6fb65b28592d5ef225d1ddbcd0ec3a509a98096d -- \
     include/be/r2.h arch/riscv/be/sv39x4.c \
     tests/r2/Makefile tests/r2/r2-check.c \
     tests/r2/r2-report.c tests/r2/check-report.mjs
   ```

8. **Treat generated documentation as derivative.** Review the Markdown and
   this packet first. Use `docs/html/**` only for functional/link/browser
   consistency, with the open hash-named-asset reproducibility finding in
   mind.

### Optional execution in the isolated worktree

If reusing the installed dependency tree, make that untracked boundary
explicit:

```sh
if [ ! -e node_modules ]; then
  ln -s /home/jamorris/src/beryllium/node_modules node_modules
fi
./be clean
./be check
./be docs-check
./tests/r3/run-make.sh r3-report
./tests/r1/check-acceptance.sh --require
./tests/r2/check-acceptance.sh --require
./tests/r3/check-acceptance.sh
./tests/r3/check-acceptance.sh --require
git diff --check
git status --short
```

Documentation generation may change hash-named generated assets in this
disposable worktree. That is the disclosed open finding, not a reason to
rewrite the exact target.

### Cleanup after review

```sh
cd /home/jamorris/src/beryllium
git worktree remove --force ../beryllium-r3-review-6fb65b
```

## 8. Human decision checklist

- [ ] The exact target, parent, whole-R3 base, two-commit lineage, changed-file inventories, and commit metadata are correct.
- [ ] The implementation scope matches the accepted R3 package: boot and first management entry only, with no R4 or later-package behavior.
- [ ] The supported claims match the exact target evidence and do not transfer Model, Helium, QEMU, or host results across boundaries.
- [ ] The trusted assumptions are acceptable: OpenSBI/QEMU/specification/toolchain/assembly correspondence, M-mode/PMP/delegation/debug/writable-monitor state, fixed compiled input, and local-hart fence scope.
- [ ] The host, image, QEMU, report, artifact, tool, and Make negative paths cover the important fail-open risks.
- [ ] The critical VU-versus-VS defect and the other fourteen disclosed findings are adequately closed in the target.
- [ ] The open VitePress generated-asset byte-reproducibility finding is acceptable as an unresolved limitation or is grounds for revision/defer.
- [ ] Accepted R1 and R2 implementation inputs remain exact matches and their accepted claim boundaries are unchanged.
- [ ] Hardware, protected entry, access/fault isolation, skipped-fence runtime testing, exact-byte/source-to-binary proof, and full runtime remain explicitly unavailable or absent.
- [ ] At this R3 decision time, R4 remained not started and unauthorized; no push, tag, public release, or successor work was authorized by this decision. Subsequent R4 authorization is recorded separately and does not alter this acceptance.
- [ ] The required Copilot trailers are present, no human `Signed-off-by` was added by automation, and the private/public boundary is correct.
- [x] **Accept** exact commit `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` on 2026-07-29, by explicit instruction `accept  6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`.
- [ ] **Request revisions** and require a new commit plus a new exact-target packet.
- [ ] **Defer** and preserve the current review-required state.

Only the acceptance-decision box is checked because that decision was
explicitly supplied by the responsible human. The technical-judgment
checklist remains unchanged as review history; no signature is generated.

## 9. Recorded decision and remaining boundaries

- **Recorded acceptance:** exact implementation target
  `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` is accepted as of 2026-07-29.
- **Packet boundary:** follow-up
  `fcc0f267a1f59241f872c0a1d2a371a95a58cba6` remains decision support, not
  accepted implementation.
- **Successor and release boundary:** this R3 acceptance itself authorized no
  successor. Responsible-human review subsequently accepted exact R4 target
  `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29; its parent
  `6e5c55c59e94bbaba136269c784db28ec1b53f54` and decision-support follow-up
  `ec7be2f146a851e7608e77eb2875076e66aab2e6` remain distinct. No push, tag,
  public release, publication-gate change, hardware claim, R5, or later
  package is authorized.
- **Future revisions:** any technical change to accepted R3 inputs requires a
  new exact target and a new explicit responsible-human decision; it does not
  silently inherit this acceptance.

---

**Status:** exact target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` is implemented at the bounded R3
scope, passed the recorded exact-target validation, and was
responsible-human accepted on 2026-07-29. R4 is accepted at exact target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52`; R5 and every successor remain
separately gated, not authorized, and not started.

**Next:** preserve the accepted R4 implementation/evidence and
keep R5 gated. Do not amend the accepted R3 target or packet commits.

**Action required from you:** review the uncommitted acceptance record for
accuracy. No further acceptance choice, R5 authority, or release authority is
implied.
