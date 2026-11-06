<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R2 plan responsible-human review summary

> **Repository rehoming note (current-line editorial context):** This record
> preserves packet-time references to former private repository
> `jamorris_microsoft/beryllium`, its remotes, and historical absolute checkout
> paths. The current active private repository is
> `beryllium-project/beryllium-hypervisor`. Use
> [project orientation](project-orientation.md) for current commands; do not
> reinterpret historical remote-containment or publication facts.

## Decision record

Responsible-human review **accepted exact plan commit**
`cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` on 2026-07-28. The explicit
instruction was: `Accept exact plan commit`.

Responsible-human review **separately authorized R2 implementation** under
that accepted plan on 2026-07-28. The explicit instruction was:
`Authorize R2 implementation`.

The Decision A prompt explicitly disclosed: review packet path
`planning/single-hart-runtime-r2-plan-review-summary.md`; documentation
functional gates pass; generated-asset byte reproducibility remains
unresolved. Acceptance does not resolve the open byte-reproducibility
finding; it remains an unresolved recorded limitation.

These decisions apply only to the exact immutable plan commit. They do not
authorize an R2 tag, a private push, public release, R3 implementation, or
any other successor work beyond the accepted R2 plan scope. R2 implementation
may now begin under the exact scope defined in the accepted plan.

## 1. Decision summary

| Field | Required content |
| --- | --- |
| Review target | Exact commit `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` with parent `feeb819e29b37c57444bac989d00fdf87dbed27c` |
| Current status | R2 bounded plan accepted at exact commit `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` on 2026-07-28; R2 implementation separately authorized but not yet started |
| Decision recorded | (A) Accept exact plan commit `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce`; (B) Authorize R2 implementation under that accepted plan |
| Successor status | R2 implementation authorized-next, not yet started; R3 has NOT started |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`; target commit is local-only (ahead 1 of `origin/beryllium/single-hart-runtime-r0`); no push, tag, or public release has occurred |

**Action expected:** no further acceptance decision is pending for this exact
SHA. Both decisions are recorded. R2 implementation may begin under the
accepted plan scope. Any tag, push, public release, or R3 start requires
separate explicit authorization.

## 2. Deliverables

`git diff --name-only feeb819e29b37c57444bac989d00fdf87dbed27c cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` reports 56 changed paths. The review-relevant
content is:

| Deliverable | Paths | Purpose | Trust / privilege boundary | Most important human review question |
| --- | --- | --- | --- | --- |
| R2 bounded plan source | `planning/single-hart-runtime-r2-plan.md` (new, 1428 lines) | Define the exact scope, API, algorithm, test matrix, evidence model, claim ledger, and exclusions for R2 | Planning documentation only; no implementation, privilege, or execution | Does the plan define a complete, reviewable, implementable scope without collapsing R3, modifying R1, or claiming formal verification? |
| Planning navigation wiring | `planning/.vitepress/config.mts` (+12 lines) | Add R2 plan to sidebar and nav in both "Runtime" and "All documents" groups | Generated-site configuration; no runtime effect | Does the new entry appear as "(proposed)" and link to the correct path? |
| Planning index and handoff | `planning/README.md` (+10 lines), `planning/HANDOFF.md` (+7 lines) | Human review queue entry, document index entry, and session handoff paragraph | Maintained prose; source of truth for review status | Does the queue/handoff correctly state "proposed, awaiting review" and not imply acceptance? |
| Browser render inventory | `pathfinder/tests/check-docs-render.mjs` (+4 lines) | Add the new page title to the planning-site render check expected list | Test infrastructure; functional validation only | Does the title match the plan's `<h1>` exactly? |
| Generated HTML and assets | `docs/html/**` (51 changed files) | VitePress output from the above source changes | Derivative; not normative; hash-named JS assets are non-reproducible (see §5, §6) | Are the generated pages functional and link-correct? (Byte reproducibility is unresolved.) |

## 3. Claim boundary

### Supported by this exact commit

- A complete, bounded, R2 implementation plan exists and is reviewable.
- The plan preserves the exact accepted R1 mechanism (no R1 source file is
  modified; R2 composes over const R1 state).
- The plan defines a self-contained `tests/r2/Makefile` build graph that does
  not modify `Makefile`, `tests/Makefile`, or any R1 source file.
- The plan specifies an all-or-nothing two-root Sv39x4 page-table builder
  with an independent walker, terminal failure, and deterministic error codes.
- The plan explicitly excludes R3 work (CSR write, HFENCE, boot, image,
  QEMU execution).

### Trusted or assumed

- The plan trusts that the accepted R1 sealed canonical state is intact at R2
  entry (verified at R2 start by independent revalidation).
- Caller host-buffer non-overlap is a documented trusted cut point (portable
  restricted C cannot prove non-overlap of arbitrary 32 KiB allocations).
- Sv39x4 PTE encoding rules are drawn from the ratified RISC-V Privileged
  Architecture 20240411 specification; correctness depends on specification
  trust until R3+ QEMU/hardware validation.

### Unavailable or `NOT RUN`

- R2 implementation: does not exist.
- R2 host tests: unavailable (implementation has not started).
- Beryllium QEMU execution: `NOT RUN`.
- K3 hardware validation: `NOT RUN`.
- Formal verification / Rocq proof of Sv39x4 builder: not available.
- Model 0.2 refinement evidence for R2: not available.

### Explicitly not implemented here

- No R2 source code, headers, or tests.
- No `tests/r2/Makefile` or `./be r2-check` wrapper commands.
- No Sv39x4 page tables, HGATP computation, or walker code.
- No R3 collapse (CSR write, boot, trap, image, assembly).
- No modification of any R1 accepted file.

## 4. Security and correctness invariants

These are plan-level contracts for future implementation, not existing
implementation/test citations. Each points to the plan section where the
contract is defined.

| Invariant | Plan contract reference | Evidence boundary |
| --- | --- | --- |
| R1 preservation: no R1 file may be modified by R2 | §R1 preservation contract — list of 14 frozen paths; `tests/r1/check-acceptance.sh` must continue to pass | Verified at plan commit by `tests/r1/check-acceptance.sh --require` passing |
| Fixed-profile equivalence: R2 rejects inputs not matching the exact frozen 13-resource, 6-authority, 2-root, 3-mappings-per-root profile | §Frozen fixed-profile validation | To be tested at implementation; no code yet |
| All-or-nothing two-root publication: results written only after BOTH roots succeed; both pools zeroed on any failure | §Complete top-level algorithm steps 13–14 and failure path | To be tested at implementation |
| Pool/PTE/walker bounds: byte-buffer LE access only, exact buf_size, 56-bit PA range, 44-bit PPN, VPN geometry, spare-page zeroing | §Pool-memory model, §Sv39x4 architecture rules, §Independent leaf walker | To be tested at implementation |
| Evidence boundary: R2 is host-tested only; NOT formally verified, NOT QEMU executed, NOT hardware validated | §Documentation, evidence, and claim ledger — "What R2 will NOT support saying" | Enforced by claim ledger in plan |
| R3 exclusion: no CSR write, no HFENCE, no boot, no image, no assembly | §Exclusions and explicit R3+ boundary | Enforced by scope in plan |

## 5. Review history and resolved findings

Independent code review found and resolved the following substantive issues
in the plan content **before** the target commit was created:

| Finding | Resolution |
| --- | --- |
| Initial proposal would have modified R1-accepted paths (`tests/Makefile`, root `Makefile`) | Replaced with self-contained `tests/r2/Makefile`; R1 files are read-only inputs only |
| Per-root state and per-root publication allowed partial observable output | Replaced with single `struct be_r2_output` with all-or-nothing semantics: both results written only after BOTH roots pass |
| Walker/buffer gap: walker could follow arbitrary PPN from PTE into unchecked host memory | Walker now verifies PPN equals exact known pool page-4/page-5 PA before buffer indexing; never converts arbitrary PPN to host pointer |
| Incorrect root layout: the initial pool table placed the VPN[2]=1 pointer in the wrong root page | Fixed VPN extraction and pool-page offset table; root entry 1 is at byte offset 8 in page 0 |
| Incorrect/missing RISC-V specification citations | Pinned to ratified 20240411; added Chapter 17 §17.2.10, §17.5, §17.5.1 and Chapter 9 §9.3.1, §9.4 |
| Incomplete identity/profile checks: R2 could proceed without verifying sealed canonical integrity | Full `sealed_integrity_result` reconstruction added at R2 entry (phase, check_result, sealed, validated_identity, sealed_identity, configuration_id match, both checkers) |
| Inconsistent scrub ordering: scrub before validating whether pools are safe to scrub | Two-pass model: first pass determines scrub-safety; second pass scrubs only safe descriptors; full validation follows |
| Unresolved build-gate conflict: adding R2 to root `Makefile check` target would alter R1 acceptance set | R2 explicitly stays outside the root build graph; composite validation is `make check && ./be r2-check`; root-graph integration is a separate future plan |
| Missing PA extent/alias/error mapping: plan did not reject frame PA boundary crossing or 64-bit overflow | Added explicit `buf_size - 1 <= PA_MASK - base`, 64-bit overflow check, and per-frame boundary crossing distinct from overflow |
| Unsafe publication pre-BUILT: partial results could be observable before both roots succeed | Results zeroed at entry; written only after both roots pass in step 14; failure path re-zeroes |

### Open finding (unresolved)

| Finding | Status |
| --- | --- |
| Generated documentation reproducibility: every `./be docs-check` or `npm run docs:build` rewrites hash-named VitePress JS assets and HTML references, even at the exact target on the canonical path | **Open.** Functional link/browser rendering passes; byte-identical regeneration does not hold. This is a VitePress build characteristic, not a plan defect, but it means the exact target does NOT remain clean after any documentation rebuild. No maintained source currently calls this harmless, known, or accepted. |

## 6. Validation and retained evidence

| Command / check | Result | Ran on exact target? | Boundary / coverage |
| --- | --- | --- | --- |
| `./be docs-check` (equivalent content before commit) | PASS: 38 Markdown sources, 39 planning HTML pages, planning browser render PASS; 12 Helium sources, 13 HTML pages, Helium render PASS | No — ran on equivalent pre-commit content at the canonical repository path | Functional links, page existence, browser rendering; does not prove byte-identical asset generation |
| `./be docs-check` (exact target, isolated detached worktree) | Functional PASS (same counts) | Yes — exact commit `cdcf160` in detached worktree | Functional correctness confirmed for exact target; VitePress rewrote hash-named assets making the worktree dirty |
| `./be docs-check` (exact target, canonical path) | Functional PASS (same counts) | Yes — exact commit at HEAD on main worktree | Same functional pass; same non-reproducibility observation |
| `tests/r1/check-acceptance.sh --require` (before commit) | PASS: `r1_accepted_mechanism_match=yes` | No — pre-commit equivalent | R1 mechanism unchanged by this plan commit |
| `tests/r1/check-acceptance.sh --require` (exact target, detached) | PASS: `r1_accepted_mechanism_match=yes` | Yes — exact commit | R1 accepted paths match `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` |
| `tests/r1/check-acceptance.sh --require` (exact target, canonical) | PASS: `r1_accepted_mechanism_match=yes` | Yes — exact commit at HEAD | Confirms R1 preservation |
| `git diff --check feeb819 cdcf160` (all locations) | PASS | Yes | No whitespace errors in the commit |
| Independent code-review agent | No blocking plan defects after two correction passes | Pre-commit equivalent | Structural review of plan scope, algorithm, contracts, test matrix, claim boundaries |

### Important limitations

1. **No exact clean rebuild.** Every `./be docs-check` execution rewrites
   tracked VitePress hash-named JS assets and HTML references. The exact target
   commit does NOT remain clean after any documentation rebuild. Byte-identical
   regeneration is currently unresolved.

2. **Functional pass only.** The documentation gates confirm page existence,
   link integrity, title matching, and browser rendering. They do not confirm
   byte-identical asset generation.

3. **R2 implementation tests are unavailable.** The target is a plan commit;
   no R2 source or tests exist to execute.

4. **QEMU Beryllium: `NOT RUN`. Hardware: `NOT RUN`.**

## 7. Recommended human review sequence

### Prepare an isolated detached worktree

```sh
cd /home/jamorris/src/beryllium
git worktree add --detach ../beryllium-r2-plan-review-cdcf160 \
  cdcf1603b97e0ef4da3e571e43fd7045116ea1ce
cd ../beryllium-r2-plan-review-cdcf160
git status --short --branch
```

> **Warning:** running `npm ci && npm run docs:build` or `./be docs-check` in
> the worktree will rewrite hash-named VitePress assets and make the worktree
> dirty. This is expected due to the unresolved documentation reproducibility
> finding. Do not accept based on a dirty worktree; validate source Markdown
> and configuration only.

### Read-only review passes

1. Confirm the immutable target and changed-path inventory:

   ```sh
   git --no-pager show --stat --summary \
     cdcf1603b97e0ef4da3e571e43fd7045116ea1ce
   git --no-pager diff --name-status \
     feeb819e29b37c57444bac989d00fdf87dbed27c \
     cdcf1603b97e0ef4da3e571e43fd7045116ea1ce
   ```

2. Review the plan source (most important):

   ```sh
   git --no-pager show \
     cdcf1603b97e0ef4da3e571e43fd7045116ea1ce:planning/single-hart-runtime-r2-plan.md \
     | less
   ```

3. Review planning navigation, index, and handoff changes:

   ```sh
   git --no-pager diff \
     feeb819e29b37c57444bac989d00fdf87dbed27c \
     cdcf1603b97e0ef4da3e571e43fd7045116ea1ce -- \
     planning/.vitepress/config.mts \
     planning/README.md \
     planning/HANDOFF.md \
     pathfinder/tests/check-docs-render.mjs
   ```

4. Confirm R1 preservation (no R1 source files changed):

   ```sh
   git --no-pager diff --name-only \
     feeb819e29b37c57444bac989d00fdf87dbed27c \
     cdcf1603b97e0ef4da3e571e43fd7045116ea1ce -- \
     include/be/ virt/be/ arch/riscv/be/ tests/Makefile Makefile
   # Expected: empty (no output)
   ```

5. Confirm policy and claim alignment:

   ```sh
   git --no-pager show \
     cdcf1603b97e0ef4da3e571e43fd7045116ea1ce:LLM_POLICY_ALIGNMENT.md
   git --no-pager show \
     cdcf1603b97e0ef4da3e571e43fd7045116ea1ce:planning/single-hart-runtime-plan.md \
     | grep -A30 "## Authorized implementation work packages"
   ```

6. Spot-check generated HTML (derivative only):

   ```sh
   git --no-pager diff --stat \
     feeb819e29b37c57444bac989d00fdf87dbed27c \
     cdcf1603b97e0ef4da3e571e43fd7045116ea1ce -- docs/html/
   ```

### Cleanup after review

```sh
cd /home/jamorris/src/beryllium
git worktree remove ../beryllium-r2-plan-review-cdcf160
```

## 8. Human decision checklist

### Decision A: Accept, revise, or defer the exact plan commit

- [ ] The plan scope matches the accepted single-hart runtime plan's R2 work-package definition (non-privileged Sv39x4 backend, host-tested only).
- [ ] The plan preserves the exact R1 mechanism: no R1 source file is modified; R2 composes over const R1 state with separate one-way R2 state.
- [ ] The plan's claim boundary is correct: host testing only, no formal verification, no QEMU, no hardware, no R3 collapse.
- [ ] The plan's trust assumptions are acceptable: host-buffer non-overlap is a documented cut point; specification trust for PTE encoding.
- [ ] The plan's test matrix covers the load-bearing failure modes: both-pool zeroing, terminal state, R1 isolation, walker safety, frozen-profile divergence.
- [ ] The plan's build-graph approach (self-contained `tests/r2/Makefile`, no root Makefile or `tests/Makefile` change) is acceptable.
- [ ] The plan's Sv39x4 architecture references (ratified 20240411, Chapter 17, Chapter 9) are correct and sufficient.
- [ ] The plan does not start R3, collapse successor work, or authorize tagging/pushing/publication.
- [ ] The exact commit metadata is acceptable: required Copilot trailers present, no human `Signed-off-by`.
- [ ] The open documentation reproducibility finding is noted and acceptable for a plan commit.
- [x] **Decision A:** accept exact plan commit `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` / ~~request revisions~~ / ~~defer~~.

### Decision B: Authorize or withhold R2 implementation start

> This decision is independent of plan acceptance. A plan acceptance alone does
> NOT authorize implementation.

- [x] R2 implementation may begin under the accepted plan's scope and constraints.
- [ ] OR: R2 implementation is withheld pending [reason].

## 9. After the decision

Both gates are satisfied and recorded on 2026-07-28:

- **Decision A (accept plan):** exact plan commit
  `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` is accepted.
- **Decision B (authorize implementation):** R2 implementation is authorized
  under the exact scope defined in the accepted plan.

R2 implementation may now begin. It creates its core API, mechanism, and tests
under `include/be/r2.h`, `arch/riscv/be/sv39x4.c`, and `tests/r2/`, with only
the additive wrapper and documentation/evidence integration defined by the
plan.

### Prohibited until separate authorization

- No R2 tag, private push, or public release.
- No R3 start (CSR write, HFENCE, boot, image, assembly).
- No modification of any R1 accepted file.
- The open documentation byte-reproducibility finding remains unresolved;
  acceptance does not resolve it.

---

**Status:** exact plan commit `cdcf1603b97e0ef4da3e571e43fd7045116ea1ce` is
accepted. R2 implementation is separately authorized under the accepted plan
scope. No R2 implementation exists yet. R1 accepted mechanism
`a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` remains unchanged.

**Next:** R2 implementation may begin under accepted plan scope. No tag, push,
public release, or R3 occurs until R2 is separately reviewed and accepted.

**Action required from you:** none for these two decisions. Both plan
acceptance and implementation authorization are recorded. Tagging, pushing,
publication, and R3 remain prohibited without separate explicit authorization.
