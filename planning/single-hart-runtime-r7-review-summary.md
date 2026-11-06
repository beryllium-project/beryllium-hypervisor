<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R7 review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves the packet-time former private repository identity and remote
> state. The current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

The responsible human accepted exact R7 implementation target
`9bf22913d67e9b72286813cd5f7993a9ad3857a8` on 2026-08-05 by explicit
instruction `Accept exact 9bf22913d67e9b72286813cd5f7993a9ad3857a8`.

The accepted target's immediate parent, and the superseded first candidate, is
`95639afb0ab57959a32d055f7b7f9bdb474fe762`; the whole-R7 comparison base is
`3ee8a20a3ab7e3673b88a502476f39559909a12e`. Review packet commit
`a4cc49d3d41e4bc22a7b17def836e6c4746f3c82` and the later follow-up commit that
records this decision are decision support, **not** accepted implementation.
`95639afb0ab57959a32d055f7b7f9bdb474fe762` is preserved as history and is
**not** accepted on its own; acceptance names exactly one commit.

Acceptance adds no validation and erases no assumption, `NOT RUN` item,
resolved finding, trusted boundary, plan-obligation substitution, or open
reproducibility finding recorded below. It adds no hardware evidence, no C
refinement, and no whole-system verification result, and it authorizes no
successor, push, tag, publication, or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact implementation target `9bf22913d67e9b72286813cd5f7993a9ad3857a8` (`r7: fix clean-worktree validation`); immediate parent and superseded first candidate `95639afb0ab57959a32d055f7b7f9bdb474fe762` (`r7: add bounded exact-byte proof evidence`); whole-R7 comparison base `3ee8a20a3ab7e3673b88a502476f39559909a12e` (`docs: record exact R7-A plan acceptance`) |
| Current status | R7 implementation was authorized by the recorded instruction `once complete, commit and push, then commence R7` under accepted plan `18c43596d308052cfad67edc6e2cb8f543f75600` and accepted Plan revision R7-A `0605028220e3795d99393156d0bfb7d6a7d631a4`. The package is implemented, complete, root-integrated, committed, exact-target validated in two independent fresh detached worktrees, and **responsible-human accepted** at exact target `9bf22913d67e9b72286813cd5f7993a9ad3857a8` on 2026-08-05. The status fields measured at the target (`r7_package_implementation=complete-local`, `r7_integration=committed-candidate-not-accepted`, `r7_head_tracked_paths=20`, `r7_evidence_claim=complete-local-not-reviewed`, `r7_acceptance=not-reviewed`, `r7_accepted_commit=none`) are **pre-decision exact-target evidence** and are deliberately left unchanged; see section 6 |
| Decision recorded | **Accepted** exact commit `9bf22913d67e9b72286813cd5f7993a9ad3857a8` on 2026-08-05. Review packet commit `a4cc49d3d41e4bc22a7b17def836e6c4746f3c82`, this acceptance record, and their commits are decision support, not accepted implementation. First candidate `95639afb0ab57959a32d055f7b7f9bdb474fe762` is superseded and not accepted |
| Branch | `beryllium/single-hart-runtime-r0`, internal/private, worktree clean at the target |
| Prior accepted boundary | R6 remains accepted only at `7ba3649f03cf13b65df33020e345d361cce2993a` (parent `9ed5ad7069b6067f03e1923c09937fe218240a59`); R5 only at `165f4d001a2b59b582b397bdea79ec4826168fdb`; R4 only at `0783dfc6557453fbac0da93a5364f2e6e2cb1f52`; R3 only at `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`. R7 changes no accepted mechanism byte of any of them, apart from the six predecessor acceptance-pin constants Plan revision R7-A authorizes |
| Plan chain | Plan `18c43596d308052cfad67edc6e2cb8f543f75600` accepted 2026-08-05 (record `014b0f654ed65758bb99112f401529975d2dfd44`); Plan revision R7-A `0605028220e3795d99393156d0bfb7d6a7d631a4` accepted 2026-08-05 (record `3ee8a20a3ab7e3673b88a502476f39559909a12e`, this range's base). Packet commits `402afc824fde0458bf1dce0c3e291cadc2319fba`, `a4cc49d3d41e4bc22a7b17def836e6c4746f3c82`, and the acceptance-record follow-ups are decision support, not plan and not implementation |
| Successor status | R8 is **not authorized and not started**. No R8 content exists (`r8_authorization=not-authorized`); this acceptance does not authorize it |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`. Push, tag, public release, and publication remain **blocked** by this acceptance; `pathfinder/publication-gate.conf` is untouched |

The responsible-human decision is recorded above; no successor authorization,
publication permission, hardware result, or wider verification claim follows
from it.

## 2. Deliverables

R7 implementation spans **two commits**. The whole-R7 range
`3ee8a20a3ab7e3673b88a502476f39559909a12e..9bf22913d67e9b72286813cd5f7993a9ad3857a8`
reports **115 paths, 13,161 insertions, 367 deletions**: 35 non-generated
paths (12,849 insertions, 90 deletions) plus 80 generated planning-site paths
under `docs/html/` (312 insertions, 277 deletions). The corrective parent
delta
`95639afb0ab57959a32d055f7b7f9bdb474fe762..9bf22913d67e9b72286813cd5f7993a9ad3857a8`
touches 11 non-generated paths, all of them the R7 evidence record and
`tests/r7/` content. **Review the whole range, not only that corrective
delta.**

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary review question |
| --- | --- | --- | --- | --- |
| Exact-byte extraction and independent cross-check | `tests/r7/extract-exact-image.mjs`, `tests/r7/check-disassembly.sh` | Read the two final R5 ELFs directly; record entry point, allocated-section table, symbol addresses/sizes, raw little-endian words, and relocation-resolved targets for 11 scoped privileged-wrapper symbols per image; confirm every word and target independently with the locked `riscv64-linux-gnu-objdump` | Read-only over accepted R5 build output; writes only under `build/r7`; the parser is explicitly **not** trusted for instruction meaning | Can the direct parser and the objdump cross-check ever agree by construction rather than independently, and is any disagreement or unsupported encoding a hard refusal? |
| Generated proof input and configuration trace | `tests/r7/generate-exact-input.mjs`, `tests/r7/check-configuration-trace.mjs` | Render extracted bytes as data-only Rocq input (`ExactInput.v`), regenerated twice and byte-compared before Rocq consumes it; derive the fixed 13-resource / 6-authority / 2-domain / 2-root / 3-leaf configuration facts (`ConfigurationTrace.v`) from the accepted R1/R2/R5 canonical state; mark and verify the delegated predecessor rebuild | Generated data only; no instruction semantics and no theorem live in generated modules | Does the generated input carry any semantics, and can the mark/verify bracket be satisfied by a stale or checked-in artefact? |
| Bounded proof development | `tests/r7/proof/ISA.v`, `Exact.v`, `Entry.v`, `Trap.v`, `Switch.v`, `Configuration.v`, `Claims.v` (7 maintained modules; `ExactInput` and `ConfigurationTrace` are generated, 9 in total) | 135 `Theorem` and 4 `Lemma` declarations over a bounded RV64/RVC decode of exactly the extracted words: entry/CSR profile, single management `HGATP` write with local `HFENCE.GVMA` and readback, 320-byte trap frame, root transaction, restore, call-free tails, single guest-return `SRET`, and the finite access matrix | Proof over linked bytes only; every C body, the parser, the toolchain, firmware, QEMU, and hardware are explicit cut points | Is any theorem stated over generated data that the proof also assumes, and does `Claims.v` export anything wider than the enumerated symbols? |
| Report, evaluator, and independent checker | `tests/r7/generate-report.mjs`, `tests/r7/check-report.mjs` | Canonical `be-r7-exact-proof-evidence-v1` report with fixed key order; 9 evidence classes, 15 cut points, 10 trusted boundaries, 14 non-claims, 1 structured plan-obligation substitution; independent re-derivation, including a second minimal ELF section reader for the allocated-image identity | Evidence integrity only; the checker can lower a claim and can never raise one | Does every published number get re-derived independently, and can a missing or failed proof ever leave a success-shaped report? |
| Retained evidence bundle and its checker | `tests/r7/generate-evidence.sh`, `tests/r7/check-evidence.mjs` | Exact-set bundle: report, checker transcript, ledgers, evaluator output, acceptance status, generated inputs, proof sources, proof-object hashes, both prover transcripts, ELF/symbol/word manifests, cross-check, configuration trace, tool lock, aggregate `artifacts.sha256`; staged into a sibling directory and renamed into place only after every check passes | Retention only; raw disassembly, raw traces, and `.vo` objects are extracted to digests/excerpts and deleted | Is the retained set exactly the manifest, and is a late failure incapable of destroying the last good bundle? |
| Harness and tool boundary | `tests/r7/run-make.sh`, `tests/r7/Makefile`, `tests/r7/check-tools.sh`, `tests/r7/tool-lock.conf`, `tests/r7/check-sources.mjs` | Checked launcher with parse-time Make-control guards; `be-r7-tool-lock-v1` binds the accepted R3 36-role lock by digest and adds exactly one R7-owned role (`rocq` 9.2, `bc30069432d192a3…`); package-wide source guard over every maintained script, the Makefile, and embedded programs, with an 18-program launch allowlist | Harness only; relaxes no accepted R3/R5 tool identity | Can a hostile Make control, shell override, aliased writer, or substituted executable reach a success banner? |
| Root integration and six authorized pin refreshes | `Makefile`, `be`, `scripts/check-be.sh`, `tests/r1/check-acceptance.sh`, `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs` | `r7-check`/`r7-evidence` targets, an R7 step in `check`, R7 bundle verification in `evidence-check`, `clean`, and `be` help/status/version/commands; exactly six enumerated predecessor acceptance-pin constants | Orchestration and status reporting cannot create acceptance; predecessor acceptance checkers stay exact-bound | Do the six pins move only because the three root files legitimately changed, and does every predecessor still report `accepted_mechanism_match=yes`? |
| Evidence record and maintained documentation | `planning/single-hart-runtime-r7-evidence.md`, `planning/roadmap.md`, `planning/HANDOFF.md`, `planning/README.md`, `planning/implementation-plan.md`, `README.md`, `.github/copilot-instructions.md`, `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs` | Authoritative R7 evidence and claim record, plus status, navigation, and browser-render coverage | Markdown is authoritative; generated HTML is derivative | Do the documents keep implementation completion, local validation, human decision, and blocked publication strictly separate? |
| Generated planning site | 80 paths under `docs/html/` | Render the maintained Markdown | Derivative build output only; byte reproducibility remains an open repository finding | Are links and static/browser rendering functional without treating unstable hash-named assets as resolved? |

### Exact non-generated inventory of the whole range

`tests/r7/` contributes **20 added files**, all test-only, and is the complete
new-package surface. It matches the accepted plan's package boundary file for
file:

```text
tests/r7/Makefile
tests/r7/check-configuration-trace.mjs
tests/r7/check-disassembly.sh
tests/r7/check-evidence.mjs
tests/r7/check-report.mjs
tests/r7/check-sources.mjs
tests/r7/check-tools.sh
tests/r7/extract-exact-image.mjs
tests/r7/generate-evidence.sh
tests/r7/generate-exact-input.mjs
tests/r7/generate-report.mjs
tests/r7/proof/Claims.v
tests/r7/proof/Configuration.v
tests/r7/proof/Entry.v
tests/r7/proof/Exact.v
tests/r7/proof/ISA.v
tests/r7/proof/Switch.v
tests/r7/proof/Trap.v
tests/r7/run-make.sh
tests/r7/tool-lock.conf
```

The remaining 15 non-generated paths are:

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
planning/single-hart-runtime-r7-evidence.md
scripts/check-be.sh
tests/r1/check-acceptance.sh
tests/r3/check-accepted-content.mjs
tests/r4/check-accepted-content.mjs
```

There is **no** added or modified path under `arch/`, `include/`, `virt/`, or
`model/` — measured as zero paths by
`git diff --name-only 3ee8a20a…9bf22913… -- include virt arch model`. No new
image, linker script, privileged instruction, guest-visible behavior, or
runtime identifier is introduced.

### The six authorized pin refreshes, and no seventh

Plan revision R7-A authorizes exactly these six constants. The diff over the
whole range touches exactly these six lines in the three predecessor checkers
and nothing else in them:

| # | Owning checker | Constant | Bound file | Value at the target |
| --- | --- | --- | --- | --- |
| 1 | `tests/r1/check-acceptance.sh` | `successor_makefile_sha256` | root `Makefile` | `cd694c6d5df84dc1d38c0593079abb7f3420594faec41ef88e2c33d1de5172de` |
| 2 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` | `tests/r1/check-acceptance.sh` | `3f1ec4795a568fa45803cfc890a59c28812dbacbd7d0f88650a96d937b583de3` |
| 3 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` | `be` | `ce70897b9eabe3ebb299875bdf436261e0ccafabe6af1f2ec9245577f182b6d6` |
| 4 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` | `scripts/check-be.sh` | `5154840c2f46ffa235a65bb37acfd141febbdeec099cd7f4185c9485aaa48703` |
| 5 | `tests/r4/check-accepted-content.mjs` | `approvedDeltaSha256` | `be` | `24fde8748d98e802fe0b1f4a8ab3ec3f166cd4814745be69490efbc8ddb5de46` |
| 6 | `tests/r4/check-accepted-content.mjs` | `approvedDeltaSha256` | `scripts/check-be.sh` | `c4528150c78a604aba37f40b4c22b7680cdab8402cac81614411a7ed0dd56b3a` |

No mode pin changed, and no seventh acceptance update was needed or made.

### Root-integration scope

`Makefile` adds `r7-check` and `r7-evidence` phony targets and recipes, one R7
step in `check`, one `sha256sum --quiet -c build/r7/evidence/artifacts.sha256`
line in `evidence-check`, and one `clean` delegation. `be` adds the R7
launcher, help/version/clean text, the `r7-check`/`r7-evidence` commands, and
the R7 status block. `scripts/check-be.sh` grows by 119 lines that assert that
block, including that the accepted-R6 historical line
`r7_authorization=not-authorized` appears **exactly once** with provenance
`r7_authorization_source=accepted-r6-package-historical`, and that the live
`r7_package_authorization=authorized` is a separate, unique key.

## 3. Claim boundary

### Supported by the exact target

The exact commit supports exactly this bounded statement, measured while the
package was still an **unaccepted candidate** and unchanged by the later
acceptance of that same commit:

> For the fixed single-hart QEMU profile and both pinned toolchains, a
> machine-checked bounded development consumes exact linked bytes from the
> accepted R5 runtime images, independently cross-checks those bytes with GNU
> objdump, decodes the enumerated privileged-wrapper subset, checks the fixed
> entry, trap-frame, root-install/fence/readback, restore, and return
> properties, and checks generated fixed-configuration facts against the
> accepted two-domain access matrix. The C implementation, direct ELF parser,
> compiler, linker outside the extracted symbols, OpenSBI, QEMU, RISC-V
> hardware, and the connection from C state to the generated configuration
> facts remain explicit assumptions. This is not a statement that Beryllium is
> formally verified.

Measured quantities behind that statement, all re-derived by an independent
checker:

| Property | Value at the target |
| --- | --- |
| images | 2 (GCC/GNU ld and Clang/lld, accepted R5 recipes) |
| scoped symbols | 22 (11 per image) |
| scoped 32-bit instruction units | 1,420 (710 per image) |
| relocation-resolved control-flow targets | 144 (72 per image) |
| allocated sections pinned row by row | 32 (16 per image) |
| GCC allocated-image identity (`be-r7-alloc-image-v1`) | `46fdf832d26e3e8f3212a0fa78adc56bf45afcad11225656ab5b5d1dcab73d27` |
| Clang allocated-image identity | `162a96462e722a622f6b362e10fa27517a08b16d7ae2f765070cfee580211994` |
| allocated bytes | GCC 46,856 file / 153,352 memory; Clang 46,096 / 152,592 |
| configuration facts | 13 resources, 6 sealed authorities, 2 domains, 2 G-stage roots, 3 leaves per root, 6 mappings |
| generated configuration module digest | `aa1003ab64850838b5019b02b637e425f49c237eb65f78903b310207932a68eb` |
| proof modules | 9 (7 maintained, 2 generated) |
| proof declarations | 135 `Theorem`, 4 `Lemma` — `Exact` 50, `Configuration` 34, `Switch` 23, `Entry` 17, `Trap` 6, `ISA` 4 + 4 lemmas, `Claims` 1 |
| exported bundle | `be_r7_claims_hold : be_r7_claims` |
| assumption closure | `Closed under the global context`, independently re-checked by `rocq check` (`assumptions=closed`) |
| cross-check | direct ELF parser versus locked `riscv64-linux-gnu-objdump` 2.46-1.fc44, agreement `exact` |
| evidence classes / cut points / trusted boundaries / non-claims | 9 / 15 / 10 / 14 |
| plan-obligation substitutions | 1, published as a structured report entry |
| source inventory | `total=20 present=20 pending=0 digest=66702f97453958300ab35deb26fe82cdcd7041088662af1faa4d0ec585ad6410` |

Also supported as measured properties of the target:

- R7 adds **no production surface**: no path under `include/`, `virt/`,
  `arch/`, or `model/`, and no accepted R0-R6 mechanism byte moves apart from
  the six authorized pin constants.
- Package state, integration state, and evidence claim are **derived from
  measurement**, never asserted, and no measured state maps to a reviewed,
  accepted, or published claim.
- The pinned allocated-image identity is **build-path independent**: it was
  measured equal in two worktrees at different absolute paths.

### Trusted or assumed

1. The ratified RISC-V privileged and hypervisor specification is faithfully
   represented by the bounded local `ISA.v` semantics.
2. The direct ELF parser (`extract-exact-image.mjs`) and the independent
   objdump cross-check together identify the intended linked bytes. Neither is
   proved.
3. Rocq's kernel, `rocq check`, and the pinned host platform execute
   correctly. Rocq 9.2 is bound by absolute path, resolved path, version, and
   SHA-256.
4. The C cut points satisfy their stated contracts. Fifteen cut points are
   published, each an unproved boundary: `c-mechanism`, `c-trap-dispatch`,
   `c-pending-binding`, `c-validator`, `c-pte-builder`, `fact-linkage`,
   `elf-parser`, `objdump`, `input-generator`, `rocq`, `compiler`, `firmware`,
   `emulator`, `architecture`, `profile`.
5. The link from C state to the generated configuration facts is an explicit
   assumption (`fact-linkage`), not a proved refinement.
6. GCC, Clang, GNU `ld`, and `lld` compiled and linked the surrounding image
   correctly; they are trusted outside the extracted symbols.
7. The pinned OpenSBI provides the frozen handoff, and pinned QEMU implements
   the relevant architecture. No R7 theorem consumes a QEMU result.
8. A single hart, no DMA, no devices, no guest SBI, and the fixed synthetic
   profile hold.

### Unavailable or `NOT RUN`

- **Hardware validation: NOT RUN.** No K3 or other silicon result exists.
- **QEMU: not re-run in R7** (`qemu_execution=not-re-run-in-r7`). R7 inherits
  accepted R5/R6 emulation evidence and produces none of its own.
- **C refinement: not claimed** (`c_refinement=not-claimed`). No source-to-binary
  validation result exists.
- **Whole-ELF proof: not claimed** (`whole_elf=not-claimed`).
- **Byte reproducibility of report bytes, `.vo` proof objects, and the evidence
  bundle: retracted and not claimed.** Their recorded digests are run
  identities. The whole-ELF-**file** digest is additionally build-path
  dependent, because the accepted R5 recipes compile with `-g3 -gdwarf-4` and
  no `-fdebug-prefix-map`, so `DW_AT_comp_dir` embeds the building worktree's
  absolute path. Only the allocated-image identity is claimed build-path
  independent and pinned in Rocq.
- **Byte reproducibility of generated planning assets: open and unresolved.**
  The repository-wide VitePress finding is not resolved by this target.

### Explicitly not implemented or claimed

- Any acceptance beyond the single exact commit
  `9bf22913d67e9b72286813cd5f7993a9ad3857a8`: the superseded first candidate
  `95639afb0ab57959a32d055f7b7f9bdb474fe762`, this record's own follow-up
  commit, any later worktree state, and any successor package remain
  unaccepted.
- Whole-image, whole-system, or whole-hypervisor formal verification.
  Beryllium is **not** formally verified;
  `formal_verification=bounded-not-whole-system`.
- Any proof about `be_reset`, the C handlers, diagnostic output, SBI calls,
  guest fixtures, or the remainder of either ELF merely because those bytes
  share an image.
- **Clearing of live guest GPR authority.** The accepted plan's obligation that
  the switch path "clears live guest GPR authority" is **not** delivered as
  written. What is proved is narrower and byte-true: every argument the proved
  assembly forms for the C cut point, and every value it publishes, is
  monitor-derived from the frame base or from a monitor CSR read; no
  guest-supplied register value reaches a call argument or a published control
  word. The saved guest GPR contents remain **live** in the trap frame across
  the C cut point. This is a plan-obligation substitution and an unproved cut
  point, not a proved clearing claim, and the stronger plan wording is
  withdrawn rather than silently satisfied.
- Arbitrary-guest or arbitrary-page-table isolation, information-flow,
  availability, timing, or side-channel results.
- Multicore, DMA, IOMMU, device, interrupt, timer, Linux, guest-SBI, or
  service behavior.
- Any Model 0.1/0.2 or Helium theorem, constant, proof object, or claim
  transfer; every result is re-derived against the accepted Beryllium images.
- Production assurance, certification, or release approval.
- **Any R8 result, R8 authorization, publication readiness, or release
  authority.**

## 4. Load-bearing invariants

| Invariant | Contract / plan basis | Implementation | Test / evidence artifact |
| --- | --- | --- | --- |
| The package is exactly the 20 files the accepted plan names | Accepted plan "Package boundary" | `tests/r7/check-sources.mjs` inventory | `total=20 present=20 pending=0 digest=66702f97…`; `r7_head_tracked_paths=20` measured by `be status` |
| The extracted bytes are the linked bytes, and the parser is not trusted for meaning | Accepted plan "Exact linked-byte scope" | `extract-exact-image.mjs` plus an independent locked `objdump` pass in `check-disassembly.sh` | Cross-check agreement `exact` over 1,420 words and 144 targets; extractor self-test 24 mutations all rejected, 3 identity cases; disassembly self-test 11 mutations all rejected, including pc+0, instruction-address, raw-encoding, and wrong-instruction target forgeries |
| A resolved target is confirmed only from a decoded operand | Independent-review finding 1 | `check-disassembly.sh` matches objdump's decoded operand field or its `#` comment for that exact instruction | The four target-forgery mutations above; `r7-check` now runs the suite |
| The pinned image identity is one another correct build can satisfy | Accepted plan gate 12 (fresh detached worktree) | `be-r7-alloc-image-v1`: entry point, allocated-section count, and one canonical row per `SHF_ALLOC` section, pinned in `Exact.v` | Allocated identity measured equal in two worktrees at different absolute paths; `Exact.v` additionally proves every pinned row is allocated, the totals are the sums of the rows, the two images are distinct, and all 11 scoped symbols lie inside the pinned read-only executable `.monitor.text` row |
| The whole-ELF-file digest is recorded, never claimed reproducible | Independent-review defect 2 | Report field `elf_file_digest=observed-run-identity-build-path-dependent`; tenth trusted boundary | `check-report.mjs` rejects a dropped `DW_AT_comp_dir` boundary and a reproducibility claim the package does not support |
| Every scoped word decodes, and unsupported words are refusals | Accepted plan gate 6 | `ISA.v` total decode over the enumerated streams | 135 theorems compile; no fallback decode path exists |
| The entry path writes management `HGATP` once, fences locally, reads back, and `SRET`s only in the accepted state | Accepted plan "Entry" | `Entry.v` (17 theorems), including a proof that the reset path contains no indirect jump | Proof stage `assumptions=closed`, re-checked by `rocq check` |
| The trap wrapper exchanges `sp` first, saves the complete accepted 320-byte frame at unique aligned offsets, passes only a monitor-owned pointer, and treats dispatch return as terminal | Accepted plan "Trap frame" | `Trap.v` (6 theorems); no branch or jump target can re-enter before the three interrupt masks; the producer immediately before `csrw sscratch,t1` is pinned to a monitor-derived `addi t1,sp,16` | Same proof stage; the GPR-clearing obligation is explicitly substituted, not claimed |
| The root transaction writes exactly one target `HGATP`, performs exactly one local `HFENCE.GVMA`, reads back, and the tails are call-free with a single guest-return `SRET` | Accepted plan "Root transaction and return" | `Switch.v` (23 theorems): the restore path reads `sscratch` and compares it, the complete 37-CSR write sequence is pinned in order, and the `stvec` trap sink is read back and compared against the materialized trap-vector address | Same proof stage |
| The finite access matrix follows from the generated facts alone | Accepted plan "Fixed configuration trace" | `Configuration.v` (34 theorems) over all 13 resources, so the monitor frames' unmapped status is proof-backed | Configuration-trace self-test `determinism=yes mutations_rejected=40`; module digest `aa1003ab…` |
| Generated proof input is deterministic before any theorem is claimed | Accepted plan "Package boundary" | `r7-proof` regenerates both generated modules and refuses to continue unless the second generation is byte-identical | `inputs=regenerated-identical` |
| No proof asserts instead of proving | Accepted plan gate 7 | `FORBIDDEN_DECLS` scan over maintained and generated sources for `Admitted`, `Abort`, `Axiom`, `Parameter`, `admit`, `exact_no_check`, `Unset Guard/Positivity/Universe Checking`, and more | Proof stage fails outright on a match; `Closed under the global context` asserted, axiom-shaped `Print Assumptions` lines rejected |
| The package rebuilds every predecessor input it measures | Accepted plan gate 4 | `r7-extract` delegates `r5-evidence` and `r6-report` through the accepted, unmodified predecessor launchers inside a single-use nonce mark/verify bracket; a static guard reads `tests/r7/Makefile` and refuses a non-producing target or a dropped bracket | Prerequisite mark/verify `regenerated=6 present=8 predecessors=r5,r6 mark=consumed`; prerequisite self-test `positive=2 rejected=20` (10 mark/freshness, 10 synthetic-recipe refusals) |
| A missing, stale, or failed proof cannot leave a success-shaped report | Accepted plan "Claim and cut-point ledger" | `generate-report.mjs` fails closed: hard refusal writes no report, absent artefact writes `proof=NOT-RUN`, stale or failed writes `proof=FAIL`; none exits zero | Report generator self-test `staged=17 not-run=5 fail=7 hard-refusals=5 artifacts=11 determinism=yes` |
| Every published number is independently re-derived | Accepted plan gate 10 | `check-report.mjs` re-derives the allocated-image identity with its own minimal section reader and re-checks every field | Independent report check `checks=6186 objects=9`; report checker self-test `cases=122 rejected=122 accepted=0` |
| The retained set is exact, hash-covered, and bounded | Accepted plan gate 11 | `generate-evidence.sh` stages into a sibling directory with `umask 022` and explicit modes, renaming into place only after every check passes | Bundle `manifest-entries=30 bundle-files=31 raw-traces=0` under the 536,870,912-byte hard limit; independent evidence check `checks=571 files=31 acceptance=not-reviewed`; evidence checker self-test `cases=72 rejected=72 accepted=0` |
| Exactly six predecessor acceptance pins are refreshed, and no more | Accepted Plan revision R7-A | The six constants in section 2, derived in the mandated order and re-derived at the final content | R1-R6 `--require` all PASS; R3/R4/R5 accepted-content negative suites PASS; predecessor interfaces `checked=7 interfaces=r0,r1,r2,r3,r4,r5,r6 all_accepted=yes` |
| The historical R6 authorization line can never be rewritten into a live claim | Accepted R6 package boundary | `be status` prints `r7_authorization=not-authorized` exactly once with `r7_authorization_source=accepted-r6-package-historical`, separately from `r7_package_authorization=authorized` | `scripts/check-be.sh` asserts single-key occurrence, ordering, and separation |
| Integration state and evidence claim are measured, never asserted, and cannot rise to acceptance | Accepted plan governance | `git ls-tree -r --name-only HEAD -- tests/r7` drives `r7_integration`, and artifact presence drives `r7_evidence_claim`; the report publishes the separately scoped `r7_report_evidence_claim`, and the checker refuses a report carrying the root-scoped name | Measured at the target: `r7_head_tracked_paths=20`, `r7_integration=committed-candidate-not-accepted`, `r7_evidence_claim=complete-local-not-reviewed`, `r7_acceptance=not-reviewed` |

## 5. Review history and resolved findings

Every substantive finding raised during planning, implementation, and
independent review is recorded here with its resolution. **Closing a finding is
not acceptance.**

### Plan-stage correction

| # | Finding | Severity as assessed | Resolution |
| --- | --- | --- | --- |
| P1 | The originally accepted R7 plan required predecessor acceptance-pin updates to be enumerated before being applied, but **enumerated none**. Root integration would therefore have invalidated R1/R3/R4 acceptance constants with no authorized set to refresh | Critical: implementation would have had to widen its own scope to proceed, or leave the repository gate red | Root integration was **blocked**, an isolated diagnostic established which constants move, and narrow **Plan revision R7-A** enumerated exactly six constants with exact formulas, a mandatory ordering, a re-derivation rule, and a validation gate. Accepted at `0605028220e3795d99393156d0bfb7d6a7d631a4` on 2026-08-05 |
| P2 | Values observed during the blocked diagnostic could have been copied into checkers | High: a stale pin would bind the wrong content | R7-A forbids copying any diagnostic or scratch value; all six constants were re-derived from the exact prospective content after the last edit to any bound file, applied in the mandated order, then re-derived once more and confirmed unchanged. Root integration resumed only after R7-A was accepted, and no seventh constant was needed |

### Independent review of the first complete local package

Independent implementation, proof, and evidence review of the first complete
local package raised **thirteen** findings. All thirteen were resolved before
`95639afb0ab57959a32d055f7b7f9bdb474fe762` was committed; the authoritative
resolution record is that commit's message body, and the rows below group the
findings the same way.

| # | Finding | Resolution |
| --- | --- | --- |
| 1 | The disassembly cross-check could confirm a resolved target against the instruction address or the raw encoding word rather than objdump's decoded operand | Targets are now confirmed only against the decoded operand field or the `#` comment for that exact instruction; the self-test grew to 11 mutations including pc+0, instruction-address, raw-encoding, and wrong-instruction forgeries, and `r7-check` runs it |
| 2 | The ELF section-header string-table path was unhardened: a `NOBITS`, non-`SHT_STRTAB`, empty, overrunning, or non-NUL-terminated `shstrtab` was read before validation | All five conditions are refused before any string read; extractor self-test mutations grew from 18 to 24 |
| 3 | The source guard checked only the first argument of three files | `check-sources.mjs` now parses every maintained shell script, the Makefile, and the programs those recipes embed, resolves their variables, and checks every path argument and redirection |
| 4 | The launch surface was effectively unbounded | Launches are held to an 18-program allowlist with per-file absolute-path allowlists |
| 5 | One second-argument write escape (the retain helper) was unpinned, and the guard file itself was unbound because it must quote the table | The retain helper is pinned and every call site's destination is resolved and bounded; every JavaScript write is pinned by complete call text; the checker is bound at the import boundary |
| 6 | `Switch.v` did not prove the restore path reads and compares `sscratch`, did not pin the CSR write sequence in order, and proved the `stvec` trap sink only materialized rather than read back | All three added: `sscratch` read-and-compare, the complete 37-CSR write sequence pinned in order, and a `stvec` readback compared against the materialized trap-vector address, keeping the no-reroot and fence checks |
| 7 | `Trap.v` did not exclude a branch or jump re-entering before the three interrupt masks, and did not pin the producer of the value written to `sscratch` | Both proved: no branch or jump target can re-enter before the masks, and the producer immediately before `csrw sscratch,t1` is pinned to a monitor-derived `addi t1,sp,16` |
| 8 | `Configuration.v`'s access matrix did not cover all thirteen resources, so the monitor frames' unmapped status was not proof-backed | The matrix was extended to all thirteen resources |
| 9 | `Entry.v` did not exclude an indirect jump on the reset path | Proved absent |
| 10 | The accepted plan's "clears live guest GPR authority" obligation was not delivered as written and was not disclosed | Disclosed as a structured `plan_obligation_substitutions` report entry, counted by the evaluator (`plan_obligation_substitutions=1`), re-derived by the checker, and recorded in the evidence document; the delivered property is the narrower byte-true one, and the stronger wording is withdrawn |
| 11 | Determinism was overclaimed: Rocq `.vo` digests and evidence-bundle digests were presented as reproducible identities | Retracted. Both are published as run identities in a ninth trusted boundary; the planning record pins no bundle-level digest and none may be re-pinned. Deterministic generated inputs, canonical semantic facts, report structure, and exact-set hash integrity within one bundle are retained |
| 12 | A late failure during evidence generation could destroy the last good bundle | `generate-evidence.sh` sets `umask 022` with explicit modes and assembles into a sibling staging directory, renaming into place only after every check passes |
| 13 | State was measured from the Git index rather than the commit; the report's evidence-claim key collided with the differently scoped `be status` key; and evidence checking accepted a partial cut-point set, an unvalidated report-check transcript, empty extra directories, and a wrong bundle-root mode | Both generator and checker read `git ls-tree -r --name-only HEAD -- tests/r7`; the report key was renamed `r7_report_evidence_claim` and the checker refuses the root-scoped name; all fifteen cut-point identifiers are required, the retained transcript is validated field by field against the retained report, and both directory and mode defects are rejected |

### Clean-worktree defects found after the first candidate

The first candidate `95639afb0ab57959a32d055f7b7f9bdb474fe762` passed only in a
**warm** working tree. Running it from fresh detached worktrees — the
validation accepted-plan gate 12 requires — exposed three independent defects.
The candidate was **not amended**; it is preserved as history and is superseded
by `9bf22913d67e9b72286813cd5f7993a9ad3857a8`, which fixes all three
test-only, inside `tests/r7/`, with no root-file, acceptance-pin, production,
or plan change.

| # | Defect | Why it mattered | Fix at the target |
| --- | --- | --- | --- |
| C1 | `r7-extract` delegated `r5-image`, but the configuration-trace stage reads the accepted R5 report at `build/r5/reports/checked-switch.json` and deliberately refuses to regenerate the heavy R5 pipeline. A clean tree failed; a warm tree silently passed on a **stale** artefact | An input consumed but not produced: the package could report success over an artefact this run never generated | Delegate `r5-evidence`, the minimal accepted R5 target that produces every canonical input R7 consumes (`r5-report` alone was measured failing from a clean tree). A single-use nonce mark is written before the launch and verified and consumed after it; a static guard refuses any `r7-extract` recipe that delegates a non-producing target or drops either bracket; a hermetic self-test drives 2 positive cases and 20 refusals inside `build/r7` |
| C2 | `Exact.v` pinned the whole-ELF-**file** SHA-256 and size, which no other build path can satisfy. A fresh worktree failed with `Unable to unify true with false` at the GCC image-identity theorem | Not a semantic difference: `-g3 -gdwarf-4` with no `-fdebug-prefix-map` embeds `DW_AT_comp_dir`, so only non-allocated `.debug_*` bytes (and Clang's `$d` mapping-symbol strings) differ. Prior local validation passed only because the pins were derived in the same worktree that built the images | Pin the property that is exact and reproducible: the schema-tagged `be-r7-alloc-image-v1` allocated-image identity, both 16-row allocated-section tables, the allocated byte totals, the entry point, and the symbol-table entry count, plus new theorems that every pinned row is allocated, the totals are the sums of the rows, the two images are distinct, and all 11 scoped symbols lie inside the pinned `.monitor.text` row. The whole-file digest is still recorded and published as a tenth trusted boundary, but is no longer asserted reproducible. `check-report.mjs` re-derives the allocated identity with an independent section reader. Theorem count rose from 127 to **135**; lemmas stayed at 4 |
| C3 | With C1 and C2 fixed, a fresh worktree reached the R7 report stage and failed `BE_R6:FAIL acceptance: the canonical R6 report has not been generated`. `tests/r6/check-acceptance.sh --require` is the only predecessor interface that reads generated build output | The same class as C1: R7 measures predecessor acceptance through each predecessor's own interface, and one of them needed artefacts nothing in R7 produced | Delegate `r6-report` through the accepted, unmodified `tests/r6/run-make.sh`, inside the same prerequisite bracket and after the R5 rebuild. The mark now covers eight canonical inputs across two predecessors; the static guard is per-predecessor; the self-test drives it over ten synthetic recipes; `check-sources.mjs` declares both cross-package dependencies; and `--verify-prerequisites` refuses a declared input that is not generated build output or is not a non-empty regular file. An audit confirms those eight are the complete set of generated predecessor inputs |

Both C1 and C3 are R7 implementation defects, not plan defects: accepted-plan
gate 4 requires the package to rebuild what it measures through the accepted
launchers. C2 is likewise an implementation defect: the plan requires the
extractor to **record** the ELF SHA-256, and nowhere requires that digest to be
proved reproducible.

The honest cost is recorded rather than optimized away: a standalone
`./be r7-check` from a clean tree now runs the full accepted R5 pipeline and
the full accepted R6 adversarial-image pipeline before any R7 stage, and the
repository gate runs the R6 pipeline a second time.

### Open questions requiring human judgment

The responsible human recorded acceptance of the exact target with all four of
these open; acceptance resolves none of them and closes none of them.

- Whether the **plan-obligation substitution** (finding 10) is an acceptable
  narrowing of the accepted plan's trap-frame obligation, or requires a plan
  revision before any acceptance.
- Whether the **allocated-image identity** is the right pinned notion of image
  identity for a proof of this kind, given that the whole-file digest is
  recorded but not reproducible.
- Whether delegating two full predecessor pipelines inside `r7-extract` is the
  right trade against reusing warm build output.
- The repository-wide **generated-asset byte-reproducibility** finding remains
  open and is not resolved by this target.

## 6. Validation and retained evidence

All results below are **pre-decision**: they were produced at the exact clean
commit `9bf22913d67e9b72286813cd5f7993a9ad3857a8`, in two independent fresh
detached worktrees, both of which have since been removed, and **before** the
responsible-human decision. Acceptance adds no execution, no rerun, and no new
measurement to them. Nothing here substitutes a later or dirty worktree for
that target.

### Package gate, at the target

| Check | Result |
| --- | --- |
| `./be r7-check` | PASS |
| `./be r7-evidence` | PASS |
| source inventory | PASS `total=20 present=20 pending=0 digest=66702f97453958300ab35deb26fe82cdcd7041088662af1faa4d0ec585ad6410` |
| tool boundary | PASS `controls=launcher-plus-parse-time` |
| predecessor prerequisite mark/verify | PASS `mode=verify-prerequisites regenerated=6 present=8 predecessors=r5,r6 mark=consumed` |
| predecessor prerequisite self-test | PASS `positive=2 rejected=20 inputs=8 delegated-targets=verified predecessors=r5,r6` |
| ELF extractor self-test | PASS `mutations=24 all-rejected=yes identity-cases=3 alloc-identity=build-path-independent` |
| disassembly cross-check self-test | PASS `mutations=11 all-rejected=yes` |
| configuration-trace self-test | PASS `determinism=yes mutations_rejected=40` |
| bounded proof | PASS `modules=9 inputs=regenerated-identical assumptions=closed checker=rocq-check` |
| report | PASS `schema=be-r7-exact-proof-evidence-v1 images=2 symbols=22 words=1420 targets=144 modules=9 theorems=135 predecessors=7 hardware=NOT-RUN` |
| evaluator | PASS `classes=9 cut-points=15 trusted=10 non-claims=14 hardware=NOT-RUN` |
| independent report check | PASS `checks=6186 objects=9` |
| evidence bundle | PASS `manifest-entries=30 bundle-files=31 raw-traces=0` |
| independent evidence check | PASS `checks=571 files=31 acceptance=not-reviewed` |
| report generator self-test | PASS `staged=17 not-run=5 fail=7 hard-refusals=5 artifacts=11 determinism=yes` |
| report checker self-test | PASS `cases=122 rejected=122 accepted=0` |
| evidence checker self-test | PASS `cases=72 rejected=72 accepted=0` |
| predecessor interfaces | PASS `checked=7 interfaces=r0,r1,r2,r3,r4,r5,r6 all_accepted=yes` |

### Predecessor and root gates, at the target

| Check | Result |
| --- | --- |
| `tests/r1/check-acceptance.sh --require` through `tests/r6/check-acceptance.sh --require` | PASS (all six) |
| R3/R4/R5 accepted-content negative suites | PASS |
| `scripts/check-be.sh` | PASS |
| `./be docs-check` | PASS |

### The two exact-target executions

| Execution | Worktree | Commands, in order | Result |
| --- | --- | --- | --- |
| Standalone-first | fresh detached worktree at the exact target, **no** `build/` directory, **no** `npm ci`, **no** preseeded artefacts | `./be r7-check`, then `./be r7-evidence` | Both PASS |
| Full repository gate | a **separate** fresh detached worktree at the exact target | `npm ci && make check` | PASS |

The standalone execution is the property the clean-worktree fixes exist for: a
single `./be r7-check` from an empty tree rebuilds the accepted R5 pipeline and
the accepted R6 adversarial-image pipeline through their own launchers before
any R7 stage, so it is a long run. `./be r7-check` already includes
`r7-evidence`, so running both in sequence repeats that work; the second
command reported the same byte totals as the first.

### Recorded byte totals, and the 8-byte difference

| Execution | Payload bytes | Bundle bytes |
| --- | --- | --- |
| standalone fresh detached worktree | 3,946,031 | 3,949,280 |
| full fresh detached worktree (`npm ci && make check`) | 3,946,023 | 3,949,272 |

Both are four orders of magnitude below the 536,870,912-byte hard limit, which
is the property that matters. **Neither total is a pin or a reproducibility
claim.** The report the bundle carries embeds the HEAD commit and the measured
package state, so the totals shift when that state does.

The two runs differ by exactly **8 bytes**. The explanation on record is that
the report in the standalone tree records R6's measured local state as
`report-generated` rather than `complete-local`, because only the delegated
`r6-report` ran there, whereas the full gate runs the whole R6 package. That
explanation is **derived** from the recorded R6 state semantics; it is **not**
read from a direct byte-level diff transcript of the two bundles. A reviewer
who wants it established directly should diff the two bundles' reports.

### Digests recorded from the standalone execution

- source inventory `66702f97453958300ab35deb26fe82cdcd7041088662af1faa4d0ec585ad6410`
- GCC allocated-image `46fdf832d26e3e8f3212a0fa78adc56bf45afcad11225656ab5b5d1dcab73d27`
- Clang allocated-image `162a96462e722a622f6b362e10fa27517a08b16d7ae2f765070cfee580211994`
- generated configuration module `aa1003ab64850838b5019b02b637e425f49c237eb65f78903b310207932a68eb`

The full `make check` execution is recorded as PASS only. It did **not** emit
whole-ELF-file digests or report/bundle digests into the captured transcript,
so this record records none for that run and no such value may be inferred
from it.

### Execution-boundary caveats

- The full-gate worktree was **dirtied by generated documentation** during
  `make check` (the VitePress build rewrites hash-named assets under
  `docs/html/`). Those generated files were restored before the worktree was
  removed. **Do not read this as `make check` leaving the tree byte-clean**;
  the open generated-asset byte-reproducibility finding remains unresolved.
- Report generation is deterministic for a fixed checked input set, and
  cross-run and cross-toolchain comparison is canonical-semantic. Report bytes,
  `.vo` proof objects, and evidence bundles are **not** claimed byte-identical
  across independent launches, hosts, or commits.
- Both review worktrees were removed after validation. The results above
  describe the exact clean commit, not any current working tree.

### Retained evidence

- Authoritative record:
  [`single-hart-runtime-r7-evidence.md`](single-hart-runtime-r7-evidence.md).
- Bundle: 30 manifest entries, 31 files, aggregate `artifacts.sha256`,
  `raw_traces_retained=0`, `raw_objdump_retained=0`,
  `predecessor_images_retained=0`, `proof_objects_retained=0` with 9 proof-object
  hashes retained.
- Root wiring: `make evidence-check` verifies
  `build/r7/evidence/artifacts.sha256` alongside the R1/R5/R6 bundles.

### Retained pre-decision status fields, and where acceptance actually lives

The accepted target's implementation and evidence machinery is **immutable**
and was **not** modified to record this decision. Every status field it emits
therefore still carries its pre-decision value, and each of those values is
retained deliberately as exact-target evidence rather than corrected after the
fact:

| Surface | Retained pre-decision fields |
| --- | --- |
| `be status` and `scripts/check-be.sh` | `r7_acceptance=not-reviewed`, `r7_accepted_commit=none`, `r7_integration=committed-candidate-not-accepted`, `r7_evidence_claim=complete-local-not-reviewed` |
| `be-r7-exact-proof-evidence-v1` report and `tests/r7/check-report.mjs` | `r7_report_evidence_claim=generated-committed-candidate-not-reviewed` and the same acceptance status |
| Retained evidence bundle and `tests/r7/check-evidence.mjs` | `acceptance=not-reviewed` across `checks=571 files=31` |
| [`single-hart-runtime-r7-evidence.md`](single-hart-runtime-r7-evidence.md) | The same measured values, recorded as the pre-decision exact-target evidence boundary |

Those fields describe the exact target as measured **before** the decision.
They are **not** a statement that the target is unaccepted today. The
responsible human's acceptance of exact commit
`9bf22913d67e9b72286813cd5f7993a9ad3857a8` on 2026-08-05 is carried by **this
review and acceptance record** and by the maintained current-position
documentation that cites it. Rewriting those retained fields would falsify
exact-target evidence; teaching the checked tooling to report an accepted R7
commit is a separate change that requires its own explicit authorization,
its own exact-target validation, and its own predecessor-pin enumeration. No
such change is made here, and no acceptance checker or pin refresh is
introduced by this record.

## 7. Recommended human review sequence

Run the exact target in an isolated detached worktree so unrelated local
changes cannot affect results.

```sh
git worktree add --detach ../beryllium-r7-review 9bf22913d67e9b72286813cd5f7993a9ad3857a8
cd ../beryllium-r7-review
git status --short
git show --no-patch --format=fuller 9bf22913d67e9b72286813cd5f7993a9ad3857a8
git show --no-patch --format=fuller 95639afb0ab57959a32d055f7b7f9bdb474fe762
git diff --check 3ee8a20a3ab7e3673b88a502476f39559909a12e 9bf22913d67e9b72286813cd5f7993a9ad3857a8
```

1. Read the accepted plan
   [`single-hart-runtime-r7-plan.md`](single-hart-runtime-r7-plan.md) including
   [Plan revision R7-A](single-hart-runtime-r7-plan.md#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh),
   its two acceptance records
   ([plan](single-hart-runtime-r7-plan-review-summary.md),
   [R7-A](single-hart-runtime-r7-plan-r7a-review-summary.md)), the
   [R7 evidence record](single-hart-runtime-r7-evidence.md), and then this
   record. Settle the claim boundary before reading code.
2. Inspect the whole implementation range, not only the corrective delta:

   ```sh
   git log --reverse --oneline 3ee8a20a3ab7e3673b88a502476f39559909a12e..9bf22913d67e9b72286813cd5f7993a9ad3857a8
   git diff --stat 3ee8a20a3ab7e3673b88a502476f39559909a12e 9bf22913d67e9b72286813cd5f7993a9ad3857a8
   git diff --name-status 3ee8a20a3ab7e3673b88a502476f39559909a12e 9bf22913d67e9b72286813cd5f7993a9ad3857a8 -- ':!docs/html'
   ```

3. Confirm the test-only boundary and the six-pin limit directly, rather than
   from prose:

   ```sh
   git diff --name-only 3ee8a20a3ab7e3673b88a502476f39559909a12e 9bf22913d67e9b72286813cd5f7993a9ad3857a8 -- arch include virt model
   git diff 3ee8a20a3ab7e3673b88a502476f39559909a12e 9bf22913d67e9b72286813cd5f7993a9ad3857a8 -- tests/r1/check-acceptance.sh tests/r3/check-accepted-content.mjs tests/r4/check-accepted-content.mjs
   ```

   The first command must print nothing. The second must show exactly six
   changed constant lines and nothing else.
4. Review the claim ledger first: the supportable claim, the 15 cut points, the
   10 trusted boundaries, the 14 non-claims, and above all the single
   `plan_obligation_substitutions` entry in
   `tests/r7/generate-report.mjs`. Decide whether the substituted guest-GPR
   property is an acceptable narrowing of the accepted plan.
5. Review the extraction and cross-check path
   (`tests/r7/extract-exact-image.mjs`, `tests/r7/check-disassembly.sh`). Ask
   whether the objdump pass is genuinely independent, whether the allocated-image
   identity covers exactly the bytes the loader maps, and whether any
   unsupported or ambiguous encoding could pass.
6. Review the proof development in dependency order — `ISA.v`, `Exact.v`,
   `Entry.v`, `Trap.v`, `Switch.v`, `Configuration.v`, `Claims.v` — against the
   generated `ExactInput`/`ConfigurationTrace` data. Ask what `Claims.v`
   actually exports, and whether any theorem is true only of generated data the
   proof also assumes:

   ```sh
   grep -c '^Theorem ' tests/r7/proof/*.v
   grep -rnE '(Admitted|Axiom|Parameter|admit)' tests/r7/proof
   ```

7. Review the prerequisite bracket and the static Makefile guard in
   `tests/r7/check-configuration-trace.mjs` and `tests/r7/Makefile`. Ask
   whether a stale predecessor artefact can still satisfy a run, and whether
   the guard's synthetic-recipe refusals cover the shapes that broke a fresh
   worktree.
8. Review the report and evidence integrity path
   (`tests/r7/generate-report.mjs`, `check-report.mjs`,
   `generate-evidence.sh`, `check-evidence.mjs`). Confirm that the checker can
   only lower a claim, that a missing or failed proof cannot exit zero, and
   that the acceptance surfaces report status only.
9. Review the corrective delta on its own terms and confirm it is test-only:

   ```sh
   git diff 95639afb0ab57959a32d055f7b7f9bdb474fe762 9bf22913d67e9b72286813cd5f7993a9ad3857a8 -- ':!docs/html'
   ```

10. If reproducing, run the documented commands from a build-absent checkout of
    the exact target — `./be r7-check` alone for the standalone property, and
    `npm ci && make check` for the full gate — and expect the byte differences
    and the generated-documentation dirtying described in section 6. Remove the
    review worktree only after recording your decision:

    ```sh
    cd -
    git worktree remove --force ../beryllium-r7-review
    ```

## 8. Human decision checklist

- [ ] The scope of the exact target matches the accepted plan
  `18c43596d308052cfad67edc6e2cb8f543f75600` and accepted Plan revision R7-A
  `0605028220e3795d99393156d0bfb7d6a7d631a4`, including the 20-file package
  boundary and the six-constant pin enumeration.
- [ ] The claims in section 3 match the retained evidence, and the bounded,
  proof-plus-checked-facts boundary is stated accurately and not overstated as
  formal verification of Beryllium.
- [ ] The **plan-obligation substitution** — guest GPR contents remain live
  across the C cut point, and only monitor-derived arguments and published
  values are proved — is an acceptable narrowing rather than a defect requiring
  a plan revision.
- [ ] The trusted assumptions are acceptable: the bounded ISA model, the direct
  ELF parser plus objdump cross-check, Rocq's kernel and `rocq check`, the
  compilers and linkers outside the extracted symbols, the C cut points and the
  C-to-generated-fact link, pinned OpenSBI, pinned QEMU, and the single-hart
  fixed synthetic profile.
- [ ] Negative paths are covered sufficiently: 24 extractor mutations, 11
  disassembly mutations, 40 configuration-trace mutations, 20 prerequisite
  refusals, 122 report-checker rejections, 72 evidence-checker rejections, and
  the forbidden-declaration scan over maintained and generated proof sources.
- [ ] R7 genuinely adds **no** production surface: nothing under `arch/`,
  `include/`, `virt/`, or `model/`, no new image, and no runtime identifier.
- [ ] Exactly six predecessor acceptance pins were refreshed, no seventh was
  added, no accepted R0-R6 mechanism byte changed, and every predecessor still
  reports an exact match.
- [ ] The two exact-target reproductions — standalone `./be r7-check` from a
  build-absent tree, and `npm ci && make check` in a separate fresh worktree —
  and the explained 8-byte difference, the non-reproducible report/bundle/`.vo`
  digests, and the generated-documentation dirtying, are acceptable evidence.
- [ ] The open questions in section 5 (allocated-image identity as the pinned
  notion, double predecessor pipeline execution, generated-asset
  reproducibility) are understood and remain open.
- [ ] R8 and every later successor, plus tag, push, publication, and release
  work, remain excluded.
- [x] **Accept** exact commit `9bf22913d67e9b72286813cd5f7993a9ad3857a8`
  on 2026-08-05 by explicit responsible-human instruction
  `Accept exact 9bf22913d67e9b72286813cd5f7993a9ad3857a8`.
- [ ] **Request revisions** through a new commit and a new review packet.
- [ ] **Defer** the decision while preserving current gates.

Only the acceptance-decision box is checked, because the responsible human
explicitly supplied that decision. The technical-judgment boxes above are left
unchecked as review history: they record the questions put to the human, not
claims that an automated agent settled them. No signature is generated.

## 9. Recorded decision and remaining boundaries

- **Recorded acceptance.** Acceptance applies to exact commit
  `9bf22913d67e9b72286813cd5f7993a9ad3857a8` and to the R7 bounded
  exact-proof implementation and evidence it carries, which spans that commit
  and its parent `95639afb0ab57959a32d055f7b7f9bdb474fe762`. The parent is
  **not** separately accepted: it is the superseded first candidate, preserved
  as history, and only the named exact commit is accepted. The review packet
  commit `a4cc49d3d41e4bc22a7b17def836e6c4746f3c82` and this acceptance record
  are decision support, not accepted implementation.
- **Scope of what was accepted.** The accepted claim is the bounded one in
  section 3: a machine-checked development over exact linked bytes from the two
  accepted R5 images, plus generated fixed-configuration facts, under 15
  published cut points and 10 trusted boundaries. Acceptance does **not**
  convert it into whole-image, whole-system, or C-refinement verification;
  `formal_verification=bounded-not-whole-system` stands, and Beryllium is
  **not** formally verified.
- **What acceptance does not add.** No hardware validation (**NOT RUN**), no
  new QEMU execution (`qemu_execution=not-re-run-in-r7`), no C refinement
  (`c_refinement=not-claimed`), no whole-ELF claim (`whole_elf=not-claimed`),
  no multi-hart, device, Linux, or service evidence, and no resolution of the
  plan-obligation substitution, the allocated-image-identity question, or the
  open generated-asset byte-reproducibility finding.
- **Status fields stay as measured.** `r7_acceptance=not-reviewed`,
  `r7_accepted_commit=none`, `r7_integration=committed-candidate-not-accepted`,
  and `r7_evidence_claim=complete-local-not-reviewed` remain the retained
  pre-decision values of the immutable target, as set out in section 6. This
  record, not the tooling, carries the decision.
- **Successor and publication boundaries.** R8 is **not** authorized and
  **not** started; no dependent work begins. Pushing, tagging, publication,
  public release, archiving, and any `pathfinder/publication-gate.conf` change
  remain **prohibited** without separate, explicit authorization.

**Status.** R7 is implemented, complete, root-integrated, committed at
`9bf22913d67e9b72286813cd5f7993a9ad3857a8`, exact-target validated in two
independent fresh detached worktrees, and responsible-human accepted at that
exact target as of 2026-08-05. The proof is bounded, not whole-system formal
verification. Hardware validation is **NOT RUN**. R8 is not authorized and not
started. Push, tag, publication, and release remain blocked.

**Next.** No successor work is authorized; R8 remains gated. Any tooling change
that would report an accepted R7 commit is a separate, separately authorized
package.

**Action required from you.** None for this recorded R7 decision. Separate
explicit authorization is required before R8, push, tag, publication, or
release work.
