<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R2 implementation responsible-human review summary

> **Repository rehoming note (current-line editorial context):** This record
> preserves packet-time references to former private repository
> `jamorris_microsoft/beryllium`, its remotes, and historical absolute checkout
> paths. The current active private repository is
> `beryllium-project/beryllium-hypervisor`. Use
> [project orientation](project-orientation.md) for current commands; do not
> reinterpret historical remote-containment or publication facts.

## Decision record

Responsible-human review **accepted exact commit**
`6e1cb579257c5dbe3234bd484fd091629e87181b` on 2026-07-28. The explicit
instruction was: `Accept exact R2 commit`.

The open VitePress generated-asset byte-reproducibility finding was disclosed
before the decision and **remains unresolved**. Acceptance records only the
exact implementation SHA and date.

This decision does **not** authorize tagging, a private push, public release,
or R3 start. Each of those requires separate explicit responsible-human
authorization.

Subsequent status: R3 was separately authorized on 2026-07-29 and its
exact implementation target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` was separately accepted on
2026-07-29. Packet follow-up remains decision support. That later decision was
not inferred from this R2 acceptance and does not change the exact R2 claim
boundary.

## 1. Decision summary

| Field | Required content |
| --- | --- |
| Review target | Exact commit `6e1cb579257c5dbe3234bd484fd091629e87181b` with parent `6ca11fc91cbd3d974cce9f2fcd5a55bba16b4a7e` |
| Current status | R2 Sv39x4 backend implemented, tested, and accepted at exact commit `6e1cb579257c5dbe3234bd484fd091629e87181b` on 2026-07-28 |
| Decision requested | Decision recorded: accept exact R2 commit |
| Successor status | At this R2 record's decision time, R3 exact implementation target `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` was later separately accepted on 2026-07-29. Responsible-human review then accepted exact R4 target `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29; its parent `6e5c55c59e94bbaba136269c784db28ec1b53f54` and decision-support follow-up `ec7be2f146a851e7608e77eb2875076e66aab2e6` remain distinct. R5 was then accepted at exact target `165f4d001a2b59b582b397bdea79ec4826168fdb` on 2026-07-30. R6 and every later successor remain gated, not authorized, and not started; publication remains blocked. No R2 tag or push has occurred. |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`; accepted implementation commit `6e1cb579257c5dbe3234bd484fd091629e87181b` and this follow-up decision record remain local until separately pushed; public release remains blocked |

No further acceptance decision is pending for this exact SHA. Any tag, push,
public release, or successor start requires separate explicit authorization.

### Lineage

| Dependency | Commit / status |
| --- | --- |
| Accepted runtime plan | `planning/single-hart-runtime-plan.md`, accepted 2026-07-25 |
| Accepted R0 freeze | `64a88b15a6c35d522fa997699c4fb514b15da314`, accepted 2026-07-27 |
| Accepted R1 mechanism | `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb`, accepted 2026-07-28 |
| Accepted R2 plan | `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce`, accepted 2026-07-28; implementation separately authorized |
| R1 mechanism match | `r1_accepted_mechanism_match=yes` (all R1 paths unchanged) |

## 2. Deliverables

`git diff --name-only 6ca11fc91cbd3d974cce9f2fcd5a55bba16b4a7e 6e1cb579257c5dbe3234bd484fd091629e87181b`
reports 74 changed paths (5579 insertions, 223 deletions). The
review-relevant source-of-truth content is:

| Deliverable | Key paths | Purpose | Trust / privilege boundary | Most important human review question |
| --- | --- | --- | --- | --- |
| R2 contract header | `include/be/r2.h` (159 lines, new) | Sv39x4 constants, R2 one-way state, pool/result/leaf structs, `be_r2_build` and `be_r2_walk_and_check` public API | Non-privileged restricted C; no CSR write, no privilege, no assembly | Does the public API express exactly the R2 plan scope without implying R3, boot, or QEMU behavior? |
| Sv39x4 implementation | `arch/riscv/be/sv39x4.c` (1183 lines, new) | Pool-based page-table builder, independent walker, re-walk; LE byte-buffer PTE access; all-or-nothing failure/scrub | Non-privileged host code only; pool memory via byte-buffer helpers with bounded offsets; no pointer casts | Are the PTE encoding, pool layout, failure scrub, and walker independence correct and consistent with the plan and contract? |
| Host tests | `tests/r2/r2-check.c` (2478 lines, new) | 95 scenarios, 5511 assertions: positive flow, adversarial builder/walker/state, pool/root/mapping rejection, frozen-profile divergence, failure isolation, terminal state | Host-only evidence; no Beryllium QEMU or hardware execution | Do the negative tests cover the load-bearing failure modes and walker structural integrity? |
| Deterministic report | `tests/r2/r2-report.c` (253 lines, new) | JSON report with R1 identity, R2 state, roots, HGATP, PTE layout, leaves, unused storage, claims | Reporting tool; compiler-independence verified | Does the report surface match the claim ledger exactly? |
| Semantic report checker | `tests/r2/check-report.mjs` (276 lines, new) | Validates exact HGATP values, PTE flags, pointer layout, leaf mappings, rights, spare verification, claim fields | Node.js test infrastructure | Are the checked values correct per the Sv39x4 specification? |
| Evidence/acceptance scripts | `tests/r2/generate-evidence.sh` (113 lines, new), `tests/r2/check-acceptance.sh` (new) | Retained source/tool/artifact identity bundle; R2 acceptance-status checker (currently `review-required`) | Evidence packaging; no runtime effect | Does the evidence bundle capture all source-of-truth paths and claim the correct status? |
| Self-contained build graph | `tests/r2/Makefile` (new) | `r2-test`, `r2-report`, `r2-evidence`, `r2-check` targets; includes R1 source as read-only compile inputs | Does **not** modify `Makefile`, `tests/Makefile`, or any R1 source file | Is the build graph self-contained and does it correctly depend on R1 without altering it? |
| Wrapper/status updates | `be` (+45 lines), `scripts/check-be.sh` (+15/-6 lines) | `./be r2-check`, `./be r2-evidence`, status/version/help updates | Stable wrapper surface; no runtime effect | Do wrapper claims stay within the exact R2 evidence boundary? |
| Maintained planning/docs | `planning/HANDOFF.md`, `planning/README.md`, `planning/single-hart-runtime-plan.md`, `planning/single-hart-runtime-r2-evidence.md` (512 lines, new), `planning/.vitepress/config.mts` | R2 evidence record, updated review queue, navigation, document index | Source-of-truth prose; generated `docs/html/**` are derivative | Do maintained claims avoid silently starting R3 or implying acceptance? |
| Root README and copilot instructions | `README.md`, `.github/copilot-instructions.md` | Onboarding, current-phase summary, R2 command surface, copilot policy alignment | Maintained prose | Do updated sections stay within the review-required boundary? |
| Browser render inventory | `pathfinder/tests/check-docs-render.mjs` (+4 lines) | Add new R2 evidence page to planning-site render check | Test infrastructure | Does the title match the new page `<h1>` exactly? |
| Generated HTML and assets | `docs/html/**` (51 changed files) | VitePress output from the above source changes | Derivative; not normative; hash-named JS assets are non-reproducible | Functional and link-correct? (Byte reproducibility is unresolved.) |

**Unchanged from accepted R1:** root `Makefile`, `tests/Makefile`,
`include/be/types.h`, `include/be/manifest.h`, `include/be/state.h`,
`include/be/r0-config.h`, `include/be/r1-config.h`, `virt/be/manifest.c`,
`virt/be/state.c`, `virt/be/r1-config.c`, `arch/riscv/be/r0-layout.h`,
`tests/r1/*`. `tests/r1/check-acceptance.sh` confirms
`r1_accepted_mechanism_match=yes`.

## 3. Claim boundary

### Supported by this exact commit

- R2 is pure non-privileged restricted C: build two concrete Sv39x4
  page-table trees from R1 sealed canonical state into 32 KiB pools with
  fixed page layout (root 4 pages, L1 1 page, L0 1 page, 2 spares), produce
  HGATP values (`MODE=Sv39x4`, `VMID=0`, pool PPN), and verify with an
  independent leaf walker.
- The fixed full profile has 13 resources, 6 canonical authorities, and 2
  derived roots with 3 leaf mappings each (6 total 4 KiB leaf PTEs).
- HGATP values are computed and stored but **not** written to the `hgatp` CSR.
- Pool memory is accessed exclusively through LE byte-buffer helpers with
  bounded offsets and no pointer casts.
- Failure is terminal (`BE_R2_STATE_FAILED`); both pools are scrubbed; no
  retry API exists.
- R1 remains valid and unchanged at phase `DERIVED` after R2 completion or
  failure (const pointer prevents mutation).
- The independent walker confirms every leaf against canonical authority with
  no unexpected or missing entries, no nonzero unused storage, and all pointer
  PPNs verified against exact known pool addresses.
- GCC and Clang strict host tests pass with 95 scenarios and 5511 assertions.
- Deterministic report is byte-identical across compilers and semantically
  validated.
- R1 accepted mechanism is unchanged: `r1_accepted_mechanism_match=yes`.
- R2 plan acceptance SHA `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` is
  recorded; the plan file is byte-identical to that commit.
- The exact commit includes the required Copilot trailers and no human
  `Signed-off-by`.

### Trusted or assumed

- Caller-owned C storage integrity remains a trusted assumption.
- Host-buffer non-overlap between two 32 KiB pool allocations is a documented
  trusted cut point: portable restricted C can reject identical start pointers
  but cannot prove partial overlap. R2 host tests use distinct `static be_u8`
  arrays; R3+ derives pointers from non-overlapping physical extents.
- Sequential single-caller: the transaction-like guarantee is a
  single-caller sequential contract, not C11 concurrency atomicity.
- Sv39x4 PTE encoding rules are drawn from the ratified RISC-V Privileged
  Architecture 20240411 specification; correctness depends on specification
  trust until R3+ QEMU/hardware validation.
- Terminal shutdown integration remains unimplemented; later platform code
  must discard a failed instance and follow the accepted shutdown path.

### Unavailable or `NOT RUN`

- Beryllium QEMU execution: **NOT RUN**. No linked image, boot, trap, or
  CSR write exists.
- K3 hardware validation: **NOT RUN**.
- Formal verification: none. R2 is not formally verified and not a Model 0.2
  Rocq refinement.
- Retained Helium QEMU evidence does **not** validate R2.
- Public release remains **blocked**.

### Explicitly not implemented here

- No CSR write (`hgatp`, `HFENCE.GVMA`, or any privileged instruction).
- No assembly, boot path, trap path, or context switch.
- No linked ELF image or binary.
- No Beryllium QEMU execution or hardware evidence.
- No formal verification claim or Model 0.2 proof refinement.
- No R3 behavior: no VS entry, no register save/restore, no fence.
- No modification to any R1 source file.
- No modification to root `Makefile` or `tests/Makefile`.

## 4. Security and correctness invariants

| Invariant | Contract | Implementation | Test / evidence |
| --- | --- | --- | --- |
| R1 integrity preserved across R2 | `include/be/r2.h` const `be_runtime *`; `include/be/state.h` sealed/derived phases | `revalidate_r1()` in `sv39x4.c` independently calls `be_check_canonical`, `be_check_enforcement`, and recomputes configuration identity before PTE construction or result publication | `r2-check.c`: N1–N8g (NULL runtime, wrong phase, identity mismatch, unsealed, check_result bad); `check-acceptance.sh` `r1_accepted_mechanism_match=yes` |
| Exact fixed profile enforced at R2 entry | `include/be/r2.h` frozen profile contract; `single-hart-runtime-r2-plan.md` fixed inputs | `validate_frozen_profile()` in `sv39x4.c` checks all 13 frames, 2 saved states, 6 authorities, channel tuple, root IDs, domain ordering, GPA, configuration version, architecture, profile | `r2-check.c`: N57–N64 (non-frozen root IDs, domain ordering, GPA, wrong version/arch/profile, excess mappings); audit tests for frozen frame/saved-state/channel |
| Pool memory safety: bounded byte-buffer access with no pointer casts | `include/be/r2.h` pool descriptor; `single-hart-runtime-r2-plan.md` §pool layout | `pte_store_le64`/`pte_load_le64` use fixed bounded offsets; `be_r2_build()` checks pointers, exact sizes, and distinct starts; `validate_pool_desc()` checks alignment and PA/PPN extent bounds | `r2-check.c`: N9–N16d (NULL buf, misaligned, undersized, oversized, duplicate, PPN overflow, 64-bit overflow, PA exceed, PA boundary crossing, one-valid/one-invalid scrub) |
| Sv39x4 PTE encoding and HGATP correctness | `include/be/r2.h` constants; RISC-V Priv 20240411 §9.3.1, §17.2.10 | `build_one_root()` in `sv39x4.c`: leaf V+R/W/X+U+A+D flags, pointer V-only, HGATP `MODE=8<<60 \| PPN` | `r2-check.c`: P1–P11 (exact HGATP, per-root leaf count, pool-page structure, PTE flags); `check-report.mjs` validates exact HGATP values and all flag bits |
| Independent walker verifies every leaf against canonical authority | `include/be/r2.h` `be_r2_walk_and_check`; `single-hart-runtime-r2-plan.md` §walker | `walk_one_root()` in `sv39x4.c`: three-level descent, leaf GPA/PA/rights comparison against canonical mappings, unexpected/missing/extra entry checks, spare-page zero verification | `r2-check.c`: N33–N51 (corrupt PPN, unexpected level, extra/missing leaf, wrong PA/rights, flag violations, spare nonzero, malformed pointer); P1–P11 re-walk matching builder |
| All-or-nothing failure: both pools scrubbed, results zeroed, terminal state | `include/be/r2.h` failure contract; `single-hart-runtime-r2-plan.md` §4 | `be_r2_build()` scrubs both pools at attempt entry; on failure re-scrubs, zeroes results, sets `FAILED`; `FAILED` is permanent | `r2-check.c`: N52–N56 (first root failure, second root failure, walker failure on second root — all verify both pools zeroed, results zeroed, terminal state sticky) |
| R1 unchanged after R2 failure | `include/be/r2.h` const pointer; R1 phase machine | R2 holds `const struct be_runtime *`; never writes through it | `r2-check.c`: N52–N56 verify R1 phase remains `DERIVED` after every R2 failure |
| Deterministic evidence identity | `tests/r2/r2-report.c`, `tests/r2/check-report.mjs`, `tests/r2/generate-evidence.sh` | GCC and Clang reports byte-identical; semantic checker validates structure and claim fields; evidence script captures source/tool/artifact hashes | `build/r2/reports/sv39x4.json` byte-identical; `build/r2/reports/report-check.txt`; `build/r2/evidence/` bundle |
| R3 exclusion | `include/be/r2.h`, `planning/single-hart-runtime-r2-evidence.md` §10 | No CSR write, no assembly, no image, no boot, no trap, no QEMU execution | At the exact R2 target, `check-report.mjs` validates the then-current `r3_status=not-started`, plus `hgatp_csr_written=no` and `privileged_code=no`; later R3 evidence remains separate |

## 5. Review history and resolved findings

The following substantive defects were found during adversarial test
development and fixed before the target commit:

| # | Finding | Resolution |
| --- | --- | --- |
| 1 | **Wrong-size re-walk result:** The initial public re-walk reused the builder's scrub-safety predicate, which conflated null buffer and incorrect buffer size into one `BE_CHECK_NULL` return. A valid buffer with wrong size therefore returned `BE_CHECK_NULL` instead of `BE_CHECK_UNSUPPORTED`. | Fixed: the re-walk now checks the pointer and exact size separately. Audit test added to exercise the exact boundary. |
| 2 | **Stale leaf sets on precondition failure:** The initial public re-walk checked `BUILT` state before zeroing `leaf_sets`. An `INVALID_PHASE` return could leave caller-provided stale leaf data intact. | Fixed: output leaf sets are now zeroed immediately after validating their pointer, before all later return paths. |
| 3 | **Explicit fixed-profile tuple gap:** Independent audit found that the initial R2-specific profile checker omitted explicit comparisons for the 13 canonical frame tuples, 2 saved-state descriptors, 6 authority tuples, and the channel tuple. The earlier generic R1 checkers masked many mutations. | Fixed: R2 now checks every tuple explicitly. Focused audit tests exercise frame, saved-state, and channel mutations. Final code review confirmed the complete comparison set. |
| 4 | **Evidence documentation accuracy:** The evidence document initially named nonexistent encode helpers and misstated defects 1–3 above. | Fixed: evidence document corrected before the target commit to accurately describe the actual implementation and the above resolved defects. |

### Independent automated code review

An independent final code-review agent reviewed the full 1183-line core
implementation (`arch/riscv/be/sv39x4.c`), the 2478-line test file
(`tests/r2/r2-check.c`), and the complete report/check/evidence/wrapper/docs
diff. The review found no high-confidence blocker. This is automated review,
not responsible-human acceptance.

### Open finding

VitePress-generated asset filenames and HTML references are
non-byte-reproducible across builds. Documentation functional gates pass.
This behavior was observed during VitePress generation and remains
**unresolved**. It is not accepted, resolved, or harmless; it is an open
item requiring human judgment.

## 6. Validation and retained evidence

### Validation runs completed 2026-07-28

| Validation | Result | Boundary / coverage |
| --- | --- | --- |
| `git --no-pager show --format=fuller --stat --summary 6e1cb579257c5dbe3234bd484fd091629e87181b` | Reviewed | Confirms exact commit, parent `6ca11fc`, required Copilot trailers, no human `Signed-off-by` |
| Exact-target `./be r2-check` in detached worktree before documentation generation | **PASS** | Tracked files matched the exact commit; the temporary untracked `node_modules` dependency link was present. GCC and Clang each passed 5511 assertions; reports were byte-identical; `BE_R2_REPORT: PASS`; evidence and source/artifact SHA checks passed. |
| Exact composite `make check && ./be r2-check` in detached worktree | **PASS** | `make check` includes retained Helium QEMU emulation (GCC/Clang), Model 0.2 (unit/run/report/proof), R0 freeze, R1 mechanism, and evidence gates. Helium QEMU results do **not** validate R2. |
| `./be r2-evidence` | **PASS** | R2 hashes, R1 accepted match, R2 review-required status |
| `tests/r1/check-acceptance.sh` | `r1_accepted_mechanism_match=yes` | All R1 paths unchanged from accepted commit `a6e0bb1` |
| `tests/r2/check-acceptance.sh` | `r2_acceptance=review-required` | No accepted R2 implementation commit yet |
| Wrapper/shell/Node syntax, semantic checker, diff hygiene | **PASS** | `scripts/check-be.sh`, `check-report.mjs`, `git diff --check` |
| `./be docs-check` | Functional **PASS** (40 planning pages, 12 Helium pages) | Generated asset byte-reproducibility **unresolved**: exact worktree became dirty (285 generated files). Functional rendering over HTTP and direct filesystem both pass. |
| Beryllium QEMU | **NOT RUN** | No linked image, no boot, no trap, no CSR write |
| K3 hardware | **NOT RUN** | No hardware available |
| Formal verification / Model 0.2 refinement | **Not available** | R2 has no proof or refinement target |

### Exact-target versus pre-commit equivalence

The validation was performed in a detached worktree at exact target commit
`6e1cb579257c5dbe3234bd484fd091629e87181b`. Tracked files were clean and
matched the target; the worktree contained only a temporary untracked
`node_modules` link used to provide installed dependencies. Pre-commit
equivalent-content validation also passed before the commit was created.
These runs are labeled separately for precision.

### Automation-local exact evidence artifacts

Automation-local, non-committed exact-clean-start artifacts are retained at:

```
/home/jamorris/.copilot/session-state/7f365144-a17a-40b6-8696-57e0fed5bbf2/files/r2-exact-evidence/
```

Contents: `artifacts.sha256`, `claim-status.txt`, `report-check.txt`,
`report.json`, `source.sha256`, `source-state.txt`.

The `source-state.txt` records:

```
generated_utc=2026-07-28T09:19:51Z
repository_commit=6e1cb579257c5dbe3234bd484fd091629e87181b
repository_status=
?? node_modules
```

These are automation-local retained copies, not committed repository
artifacts. The committed evidence scripts under `tests/r2/` regenerate the
report, claim status, and source/artifact hashes from the exact target;
generation time and repository status are intentionally environment-specific.

### Retained build artifacts (regenerable from exact commit)

| Artifact | Path | Content |
| --- | --- | --- |
| Deterministic report | `build/r2/reports/sv39x4.json` | R1 identity, R2 state, roots, HGATP, leaves, PTE layout, claims |
| Report semantic check | `build/r2/reports/report-check.txt` | Structural and semantic validation output |
| Source state | `build/r2/evidence/source-state.txt` | Generation timestamp and commit hash |
| Tool versions | `build/r2/evidence/tool-versions.txt` | GCC/Clang/Node/make versions |
| Source hashes | `build/r2/evidence/source.sha256` | SHA-256 of all R2 source-of-truth paths |
| Artifact hashes | `build/r2/evidence/artifacts.sha256` | SHA-256 of generated report and check output |
| Claim status | `build/r2/evidence/claim-status.txt` | Key-value claim state (see §evidence claim status) |

## 7. Recommended human review sequence

### Prepare an isolated detached worktree

```sh
cd /home/jamorris/src/beryllium
git worktree add --detach ../beryllium-r2-review-6e1cb57 \
  6e1cb579257c5dbe3234bd484fd091629e87181b
cd ../beryllium-r2-review-6e1cb57
git status --short --branch
```

### Read-only review passes

1. **Confirm the immutable target and changed-path inventory:**

   ```sh
   git --no-pager show --stat --summary \
     6e1cb579257c5dbe3234bd484fd091629e87181b
   git --no-pager diff --name-status \
     6ca11fc91cbd3d974cce9f2fcd5a55bba16b4a7e \
     6e1cb579257c5dbe3234bd484fd091629e87181b
   ```

2. **Review policy, accepted plan, R1 acceptance, and R2 plan:**

   ```sh
   git --no-pager show \
     6e1cb579257c5dbe3234bd484fd091629e87181b:LLM_POLICY_ALIGNMENT.md
   git --no-pager diff \
     6ca11fc91cbd3d974cce9f2fcd5a55bba16b4a7e \
     6e1cb579257c5dbe3234bd484fd091629e87181b -- \
     planning/single-hart-runtime-plan.md \
     planning/single-hart-runtime-r2-evidence.md \
     planning/HANDOFF.md \
     planning/README.md
   ```

3. **Review the R2 contract and Sv39x4 implementation (core):**

   ```sh
   git --no-pager show \
     6e1cb579257c5dbe3234bd484fd091629e87181b:include/be/r2.h
   git --no-pager show \
     6e1cb579257c5dbe3234bd484fd091629e87181b:arch/riscv/be/sv39x4.c
   ```

4. **Review the host tests, report, semantic checker, evidence, and build graph:**

   ```sh
   git --no-pager show \
     6e1cb579257c5dbe3234bd484fd091629e87181b:tests/r2/r2-check.c
   git --no-pager show \
     6e1cb579257c5dbe3234bd484fd091629e87181b:tests/r2/r2-report.c
   git --no-pager show \
     6e1cb579257c5dbe3234bd484fd091629e87181b:tests/r2/check-report.mjs
   git --no-pager show \
     6e1cb579257c5dbe3234bd484fd091629e87181b:tests/r2/generate-evidence.sh
   git --no-pager show \
     6e1cb579257c5dbe3234bd484fd091629e87181b:tests/r2/check-acceptance.sh
   git --no-pager show \
     6e1cb579257c5dbe3234bd484fd091629e87181b:tests/r2/Makefile
   ```

5. **Review wrapper, status, and copilot instructions:**

   ```sh
   git --no-pager diff \
     6ca11fc91cbd3d974cce9f2fcd5a55bba16b4a7e \
     6e1cb579257c5dbe3234bd484fd091629e87181b -- \
     be scripts/check-be.sh \
     README.md .github/copilot-instructions.md
   ```

6. **Verify R1 is unchanged:**

   ```sh
   git --no-pager diff \
     a6e0bb178c10a7e68c9447a8e58affb94b8ecadb \
     6e1cb579257c5dbe3234bd484fd091629e87181b -- \
     include/be/types.h include/be/manifest.h include/be/state.h \
     include/be/r0-config.h include/be/r1-config.h \
     virt/be/manifest.c virt/be/state.c virt/be/r1-config.c \
     arch/riscv/be/r0-layout.h Makefile tests/Makefile \
     tests/r1/r1-check.c tests/r1/r1-report.c \
     tests/r1/check-report.mjs
   ```

   This should produce no output (empty diff), confirming R1 paths are
   byte-identical to the accepted mechanism commit.

7. **Treat `docs/html/**` as generated derivatives only** if you want a
   publication-consistency spot check. Do not use them as the normative source.

> **Warning:** Running `npm run docs:build` in the review worktree will
> regenerate VitePress assets with non-reproducible content-hash filenames,
> dirtying the worktree. This is the open byte-reproducibility finding.
> Prefer reviewing source/plan/evidence Markdown before derivative HTML.

### Optional execution in the isolated worktree

The full composite gate needs the lockfile-resolved documentation
dependencies. Providing a local `node_modules` tree or symlink is an
environment setup step and must not be mistaken for an exact tracked-source
change.

```sh
make -C tests/r2 r2-check        # R2-only host tests + report + evidence
make check && ./be r2-check       # Full composite gate
```

### Cleanup after review

```sh
cd /home/jamorris/src/beryllium
git worktree remove ../beryllium-r2-review-6e1cb57
```

## 8. Human decision checklist

- [ ] The exact scope matches the accepted R2 bounded plan (`cdcf1603b97e0ef4da3e571e43fd7045116ea1ce`) and does not start R3.
- [ ] The claims stay within evidence: 2 Sv39x4 roots × 3 leaves each, HGATP computed but not written to CSR, all-or-nothing failure, no privileged code, no linked image, no boot, no QEMU, no hardware, no formal verification.
- [ ] R1 source files are unchanged from accepted mechanism commit `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb`.
- [ ] The trust assumptions are acceptable: caller-owned C storage integrity, host-buffer non-overlap, sequential single-caller, specification trust for PTE encoding until QEMU/hardware validation.
- [ ] Negative-path coverage is sufficient for pool memory safety, PTE/HGATP encoding, walker structural integrity, profile divergence, R1 integrity mutation, wrong-phase use, failure isolation, and terminal state.
- [ ] The four resolved findings (wrong-size re-walk, stale leaf sets, explicit profile tuple gap, evidence doc accuracy) are adequately addressed.
- [ ] The open VitePress byte-reproducibility finding is acceptable as a recorded unresolved limitation.
- [ ] No tag, push, public release, R3 start, or dependent work is authorized by this review.
- [ ] The exact commit metadata is acceptable: required Copilot trailers present, no human `Signed-off-by`.
- [x] Decision recorded: accept exact commit `6e1cb579257c5dbe3234bd484fd091629e87181b` on 2026-07-28.

## 9. After the decision

- **Accepted and recorded:** exact SHA `6e1cb579257c5dbe3234bd484fd091629e87181b` was accepted on 2026-07-28. The open VitePress byte-reproducibility finding was disclosed and remains unresolved. Acceptance does **not** authorize tagging, pushing, public release, or R3 start. Any of those requires separate explicit authorization.

- **Request revisions:** create a new commit with the requested changes and
  a new review packet for that new SHA. The old SHA
  `6e1cb579257c5dbe3234bd484fd091629e87181b` is not silently treated as
  accepted.

- **Defer:** at the decision point, preserve status
  (`r2_acceptance=review-required`, `r2_accepted_commit=none`, and the
  then-current `r3_status=not-started`). Do not tag, push, publish, or start
  dependent work.

---

**Status:** exact commit `6e1cb579257c5dbe3234bd484fd091629e87181b` is
implemented, evidence-backed, exact-target tested, and responsible-human
accepted on 2026-07-28. The open VitePress generated-asset
byte-reproducibility finding remains unresolved.

**Next:** preserve this exact R2 acceptance record. R3 was later separately
accepted at exact implementation target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`. R4 was then accepted at exact
target `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29; its parent
and decision-support follow-up remain distinct. R5 was then accepted at exact
target `165f4d001a2b59b582b397bdea79ec4826168fdb` on 2026-07-30. R6 and every
later successor remain gated, not authorized, and not started; publication
remains blocked. No tag or push has occurred.

**Action required from you:** none for acceptance recording. Separately
authorize any tag, private push, public release, or successor work if desired.
