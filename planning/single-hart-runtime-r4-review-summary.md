<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R4 review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves the packet-time former private repository identity and remote
> state. The current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

## Decision record

The responsible human explicitly accepted the exact R4 implementation target
on 2026-07-29 with this instruction, preserved verbatim:

```text
accept exact commit
```

The accepted implementation is only
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52`, whose immediate parent/main
implementation is `6e5c55c59e94bbaba136269c784db28ec1b53f54` and whose
whole-R4 base is `4440ffa34b7d29bbd3bcae7ffa4ecadaddd66fdb`. Packet commit
`ec7be2f146a851e7608e77eb2875076e66aab2e6` is decision support and is
**not** an accepted implementation target. Acceptance does not erase trusted
assumptions, `NOT RUN` items, resolved findings, or the open generated-asset
byte-reproducibility finding. It does not authorize R5, a tag, a push,
publication, release, hardware claims, or a publication-gate change.

## 1. Decision summary

| Field | Required content |
| --- | --- |
| Review target | Exact corrective R4 target `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` (`runtime: make R4 evidence commit-ready`), immediate parent/main implementation `6e5c55c59e94bbaba136269c784db28ec1b53f54` (`runtime: implement single-hart R4 trap context`), whole-R4 base `4440ffa34b7d29bbd3bcae7ffa4ecadaddd66fdb` (`docs: accept single-hart runtime R3`). |
| Current status | R4 was authorized by the exact human instruction `proceed to implement R4` on 2026-07-29; it is implemented, exact-target validated, and **responsible-human accepted** at exact commit `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29. |
| Decision recorded | Accepted exact commit `0783dfc6557453fbac0da93a5364f2e6e2cb1f52`; packet commit `ec7be2f146a851e7608e77eb2875076e66aab2e6` is not accepted implementation. |
| Branch | `beryllium/single-hart-runtime-r0`. |
| Prior accepted boundary | R3 remains accepted only at `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`; its packet follow-up `fcc0f267a1f59241f872c0a1d2a371a95a58cba6` remains decision support, not accepted implementation. |
| Successor status | The bounded R5 plan was later separately accepted at exact commit `fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30, R5 implementation was separately authorized under that accepted plan, and exact R5 implementation target `165f4d001a2b59b582b397bdea79ec4826168fdb` was separately accepted on 2026-07-30; R6+ remain not authorized and not started. |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`; target is local, unpushed, and untagged. Push, tag, public release, and publication remain blocked. |

The remaining action is independent review of this acceptance record, without
changing the accepted target.

## 2. Deliverables

The whole-R4 range
`4440ffa34b7d29bbd3bcae7ffa4ecadaddd66fdb..0783dfc6557453fbac0da93a5364f2e6e2cb1f52`
contains the implementation commit and corrective evidence commit. `git diff
--numstat` reports 122 paths, 4,338 insertions, and 414 deletions: 44
non-generated paths plus 78 generated planning paths (46 HTML pages, 31
hash-named assets, and `docs/html/hashmap.json`). The corrective parent delta
`6e5c55c59e94bbaba136269c784db28ec1b53f54..0783dfc6557453fbac0da93a5364f2e6e2cb1f52`
is 106 paths, 367 insertions, and 318 deletions: 12 source paths and 94
generated paths (76 planning and 18 Helium). Review the whole range, not only
that corrective delta.

### Exact whole-range changed-file inventory

Non-generated paths:

```text
.github/copilot-instructions.md
Makefile
README.md
arch/riscv/be/r4-beryllium.lds
arch/riscv/be/r4-entry.S
arch/riscv/be/r4-guest.S
arch/riscv/be/r4-platform.h
arch/riscv/be/r4-runtime.c
arch/riscv/be/r4-trap.S
be
include/be/r4.h
pathfinder/tests/check-docs-render.mjs
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/research-synthesis.md
planning/roadmap.md
planning/single-hart-runtime-plan.md
planning/single-hart-runtime-r2-review-summary.md
planning/single-hart-runtime-r3-evidence.md
planning/single-hart-runtime-r3-review-summary.md
planning/single-hart-runtime-r4-evidence.md
scripts/check-be.sh
tests/r1/check-acceptance.sh
tests/r3/check-acceptance.sh
tests/r3/check-accepted-content.mjs
tests/r3/test-acceptance-content.mjs
tests/r4/Makefile
tests/r4/check-image-parity.mjs
tests/r4/check-image.mjs
tests/r4/check-qemu-artifacts.mjs
tests/r4/check-report.mjs
tests/r4/check-tools.sh
tests/r4/generate-evidence.sh
tests/r4/generate-report.mjs
tests/r4/make-control.mjs
tests/r4/r4-check.c
tests/r4/run-make.sh
tests/r4/run-qemu.sh
tests/r4/test-qemu-artifact-integrity.mjs
tests/r4/test-report-rejection.mjs
tests/r4/test-tool-binding.mjs
tests/r4/tool-lock.conf
virt/be/r4.c
```

Generated paths (derivative, non-normative):

```text
docs/html/404.html
docs/html/HANDOFF.html
docs/html/architecture-model-0.1-evidence.html
docs/html/architecture-model-0.1.html
docs/html/architecture-model-0.2-evidence.html
docs/html/architecture-model-0.2.html
docs/html/arm64-pathfinder-plan.html
docs/html/assets/HANDOFF.md.Bieui3PR.js
docs/html/assets/HANDOFF.md.Bieui3PR.lean.js
docs/html/assets/app.Clu5ilEu.js
docs/html/assets/chunks/@localSearchIndexroot.CUXBnq5_.js
docs/html/assets/chunks/@localSearchIndexroot.D3U9X3lj.js
docs/html/assets/chunks/VPLocalSearchBox.2dIHqNg_.js
docs/html/assets/chunks/theme.BK9Rge7d.js
docs/html/assets/implementation-plan.md.C3SsnOxJ.js
docs/html/assets/implementation-plan.md.DCsb6OoE.js
docs/html/assets/implementation-plan.md.DCsb6OoE.lean.js
docs/html/assets/index.md.DCFHHY7V.js
docs/html/assets/index.md.DKbgJMmY.js
docs/html/assets/index.md.DKbgJMmY.lean.js
docs/html/assets/research-synthesis.md.DgKnHa8H.js
docs/html/assets/research-synthesis.md.DgKnHa8H.lean.js
docs/html/assets/research-synthesis.md.fHFoIj4J.js
docs/html/assets/roadmap.md.BI7uT10P.js
docs/html/assets/roadmap.md.BI7uT10P.lean.js
docs/html/assets/roadmap.md.Dc_ezXHV.js
docs/html/assets/roadmap.md.Dc_ezXHV.lean.js
docs/html/assets/single-hart-runtime-plan.md.BImIDeQR.js
docs/html/assets/single-hart-runtime-plan.md.BImIDeQR.lean.js
docs/html/assets/single-hart-runtime-r2-review-summary.md.DgrQ4C1A.js
docs/html/assets/single-hart-runtime-r2-review-summary.md.DgrQ4C1A.lean.js
docs/html/assets/single-hart-runtime-r3-evidence.md.zE3guc-d.js
docs/html/assets/single-hart-runtime-r3-evidence.md.zE3guc-d.lean.js
docs/html/assets/single-hart-runtime-r3-review-summary.md.B6R_Gp0p.js
docs/html/assets/single-hart-runtime-r3-review-summary.md.B6R_Gp0p.lean.js
docs/html/assets/single-hart-runtime-r3-review-summary.md.C6Z4E7qA.js
docs/html/assets/single-hart-runtime-r4-evidence.md.ZwBvA2WG.js
docs/html/assets/single-hart-runtime-r4-evidence.md.ZwBvA2WG.lean.js
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
docs/html/supervisory-security-policy.html
docs/html/type-enforcement-pathfinder-evidence.html
docs/html/type-enforcement-pathfinder-plan.html
```

### Corrective parent-delta inventory

The target's parent delta changes these 12 non-generated source paths:

```text
.github/copilot-instructions.md
README.md
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/research-synthesis.md
planning/roadmap.md
planning/single-hart-runtime-plan.md
planning/single-hart-runtime-r2-review-summary.md
planning/single-hart-runtime-r3-evidence.md
planning/single-hart-runtime-r3-review-summary.md
planning/single-hart-runtime-r4-evidence.md
```

Its 94 generated paths are 76 planning paths under `docs/html/` and these 18
Helium paths under `pathfinder/docs/html/`:

```text
pathfinder/docs/html/404.html
pathfinder/docs/html/architecture.html
pathfinder/docs/html/assets/app.Bu3JrJEH.js
pathfinder/docs/html/assets/chunks/@localSearchIndexroot.CMKEtpSE.js
pathfinder/docs/html/assets/chunks/@localSearchIndexroot.Cb-U770w.js
pathfinder/docs/html/assets/chunks/VPLocalSearchBox.b3DCd5iO.js
pathfinder/docs/html/assets/chunks/theme.Cpx74AMQ.js
pathfinder/docs/html/code-tour.html
pathfinder/docs/html/concepts.html
pathfinder/docs/html/engineering-sop.html
pathfinder/docs/html/evaluation.html
pathfinder/docs/html/index.html
pathfinder/docs/html/policy-and-publication.html
pathfinder/docs/html/policy-models.html
pathfinder/docs/html/quickstart.html
pathfinder/docs/html/references.html
pathfinder/docs/html/security-and-limits.html
pathfinder/docs/html/verification.html
```

The exact status/path inventory for either range remains reproducible without
interpretation:

```sh
git diff --name-status 4440ffa34b7d29bbd3bcae7ffa4ecadaddd66fdb 0783dfc6557453fbac0da93a5364f2e6e2cb1f52
git diff --name-status 6e5c55c59e94bbaba136269c784db28ec1b53f54 0783dfc6557453fbac0da93a5364f2e6e2cb1f52
```

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary review question |
| --- | --- | --- | --- | --- |
| R4 contract and transaction | `include/be/r4.h`, `virt/be/r4.c` | Import exact accepted R3 state; classify two management exits; advance only successful saved PCs; fail closed | Restricted C receives observations from privileged assembly but owns no direct CSR instruction | Are binding, observation, phase, reserved-word, and sticky-failure checks complete before a restore result is returned? |
| Privileged entry, trap, guest, runtime, and linker boundary | `arch/riscv/be/r4-*` | Trusted-stack vector, full-frame save/restore, CSR reset/readback, same-management `sret`, fixed fixtures and layout | The only R4 privileged/assembly boundary; trusts pinned compiler, linker, OpenSBI, QEMU, and RISC-V behavior | Does every path save the exact S set before C, reset/check controls, retain management HGATP, and restore only the validated same-management frame? |
| Evidence and hostile-control checks | `tests/r4/**` | GCC/Clang host tests, image semantics/parity, six QEMU traces, reports, evidence retention, tool lock, and rejection tests | Host and QEMU evidence; not hardware or a source-to-binary proof | Do independent checkers reject substituted tools, hostile Make controls, altered/stale logs, invalid reports, hidden entry, and post-entry HGATP/HFENCE activity? |
| Acceptance-drift and wrapper integration | `tests/r1/check-acceptance.sh`, `tests/r3/check-*`, `be`, `Makefile`, `scripts/check-be.sh` | Preserve exact accepted R1/R2/R3 boundaries while integrating R4 into repository checks/status | Orchestration cannot create acceptance; earlier accepted content remains exact-bound | Can later R4 work silently change prior accepted inputs, skip required checks, or report acceptance/release? |
| Maintained documentation and render inventory | `.github/copilot-instructions.md`, `README.md`, `planning/**`, `pathfinder/tests/check-docs-render.mjs` | Record the bounded R4 state, evidence, R5 exclusion, and browser coverage | Markdown is authoritative; generated HTML is derivative | Do source documents separate implementation, exact-target validation, human decision, and blocked publication? |
| Generated planning site | `docs/html/**` listed above | Render maintained Markdown | Derivative only; byte reproducibility is open | Are links and browser/static rendering functional without treating unstable hash-named assets as resolved? |

## 3. Claim boundary

### Supported by the exact target

- In the fixed single-hart QEMU profile, GCC and Clang images import accepted
  R3 management state, save a fixed complete R4 frame at two management exits,
  validate the expected protected-private load and private VS ecall, and
  restore that same management context at `0x40010018` and `0x40010034`.
- The denied load is observed at PC `0x40010014`, GVA `0x40001000`, and
  `scause=21`; the event is `scause=10` at PC `0x40010030`. Three bounded
  QEMU runs per compiler show this order. The protected guest is linked but
  not entered.
- GCC and Clang host runs each cover ten scenarios and 1,283 assertions.
  GCC/GNU-ld and Clang/lld images have semantic parity, not byte equality.
- The evidence report schema is `be-r4-trap-context-v1`. Static and QEMU
  checks reject a post-initial management HGATP write or `HFENCE.GVMA`.

### Trusted or assumed

- Pinned OpenSBI, QEMU, the ratified RISC-V privileged architecture, GCC,
  Clang, GNU ld, lld, assembler/disassembler, and inspected-to-executed
  correspondence.
- The fixed compiled inputs, monitor memory integrity, trusted stack, caller
  storage, single-hart environment, and M-mode/PMP/delegation/debug setup
  outside the bounded checks.

### Unavailable or `NOT RUN`

- Hardware/K3 validation, protected VS entry, second-domain execution,
  shared-read-only denial, R6 completion, R7 exact-byte or source-to-binary
  proof, and formal verification are **NOT RUN** or unavailable.

### Explicitly not implemented

- R5 switching, root selection/fence for another domain, context separation
  across domains, Linux, service, device, DMA, interrupt/timer, multicore,
  guest SBI, arbitrary guest isolation, production readiness, certification,
  and public release.
- No Model proof/refinement or Helium proof/evidence transfers to R4.

## 4. Load-bearing invariants

| Invariant | Contract | Implementation | Test / evidence |
| --- | --- | --- | --- |
| Only accepted R3 management state enters R4 | `include/be/r4.h`: R3 import/binding contract | `virt/be/r4.c`; `arch/riscv/be/r4-runtime.c` | Host R3 import negatives; R1/R2/R3 acceptance checkers; retained report identities |
| A successful restore is only same-management and full-frame | 320-byte frame ABI, `EMPTY -> EXPECT_FAULT -> EXPECT_EVENT -> COMPLETE` | `r4-trap.S` saves/restores x1–x31 and the eight defined VS/trap CSRs; `r4.c` returns restore only after a valid observation | Host 10-scenario/1,283-assertion tests; `check-image.mjs`; six QEMU traces |
| Guest stack is never trusted for trap entry | Trusted-stack/`sscratch` contract | Direct `csrrw sp, sscratch, sp` before stack use in `r4-trap.S` | Image checker requires the swap and fixed frame offsets |
| Failure is sticky and cannot enter another domain | `BE_R4_PHASE_FAILED`, terminal result/error contract | `r4.c` clears retained authority; runtime halts rather than restoring/entering | Host terminal negatives; image checker; QEMU rejects terminal failure/protected entry |
| Reset controls are checked without overclaiming WARL behavior | R/S/R classification and writable-control masks in `r4.h` | Trap/runtime reset then masked readback; management HGATP readback before `sret` | Host CSR mutations; static CSR-order inspection; QEMU absence of post-entry HGATP/HFENCE |
| Evidence and tools cannot be substituted silently | `tests/r4/tool-lock.conf`, checked launcher contract | `run-make.sh`, parse-time Make preflight, `check-tools.sh` source hashes | Tool-binding and report-rejection negatives; retained manifests and logs |

## 5. Review history and resolved findings

Closed substantive findings in the target include:

- VS ecall cause corrected from 9 to 10; same-domain restore/`sret` retained
  in R4 while switching remains R5.
- The unsafe 512-byte reset-CSR frame became the matrix-exact 320-byte S set;
  protected/shared-write fixtures were deferred rather than implied.
- Trusted-stack top spill, assembly enum constants, nested-trap `sscratch`
  rebound, guest `t1` restore clobber, private-backing preseeding, WARL
  `sstatus`/`vsstatus` masking, and stale QEMU marker schema were corrected.
- `check-tools.sh` now reports source hashes; R1 checker and successor
  Makefile inputs are exact-bound with drift tests; stale or overclaiming
  documentation was corrected.

Independent core, platform, and full-diff reviews found no remaining
high-confidence code defects. Those closures do not constitute acceptance.

**Open:** Exact-target `./be docs-check` functionally passed but regenerated
different hash-named JavaScript assets. The generated changes were restored
to target state. This is an open generated-asset byte-reproducibility finding,
not a functional documentation failure and not resolved by this packet.
Human judgment remains required on scope, claims, trust assumptions, and this
finding.

## 6. Exact-target validation and retained evidence

The following ran on 2026-07-29 from the clean exact target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52`, not merely equivalent
pre-commit content:

| Command / evidence | Result and coverage |
| --- | --- |
| `./be check` | **PASS**: root, Helium, Model, R0, R1, R4/evidence, then R2 and checked R3. |
| `tests/r1/check-acceptance.sh --require`, R2 equivalent, R3 equivalent | **PASS**; accepted-match fields report yes. |
| `./be status` | **PASS**: clean target; R4 authorized/implemented/not-accepted; R5 not-authorized; publication blocked; hardware `NOT RUN`. |
| `./be docs-check` | **PASS**: 45 Markdown/46 HTML planning pages before this packet and 12/13 Helium pages; functional link/browser checks passed. See the open generated-asset finding. |
| `git diff --check` | **PASS**. |

Retained R4 evidence is `build/r4/reports/trap-context.json`,
`build/r4/evidence/`, manifests, claim ledger, image semantic records, and
12 console/trace logs; `planning/single-hart-runtime-r4-evidence.md` is the
authoritative evidence/claim record. The report records source hashes, locked
tools, image records, and two three-run QEMU summaries. Prior precommit runs
are not substituted for these exact-target results.

## 7. Recommended human review sequence

Use an isolated detached worktree so unrelated local changes cannot affect
the review:

```sh
git worktree add --detach ../beryllium-r4-review 0783dfc6557453fbac0da93a5364f2e6e2cb1f52
cd ../beryllium-r4-review
git status --short
git show --no-patch --format=fuller 0783dfc6557453fbac0da93a5364f2e6e2cb1f52
git diff --check 4440ffa34b7d29bbd3bcae7ffa4ecadaddd66fdb 0783dfc6557453fbac0da93a5364f2e6e2cb1f52
```

1. Read `planning/single-hart-runtime-plan.md`, R3's accepted target/record,
   `planning/single-hart-runtime-r4-evidence.md`, then this packet. Confirm
   the R4/R5 and claim boundaries first.
2. Inspect the complete implementation range, not only the evidence delta:

   ```sh
   git log --reverse --oneline 4440ffa34b7d29bbd3bcae7ffa4ecadaddd66fdb..0783dfc6557453fbac0da93a5364f2e6e2cb1f52
   git diff --stat 4440ffa34b7d29bbd3bcae7ffa4ecadaddd66fdb 0783dfc6557453fbac0da93a5364f2e6e2cb1f52
   git diff --find-renames 4440ffa34b7d29bbd3bcae7ffa4ecadaddd66fdb 0783dfc6557453fbac0da93a5364f2e6e2cb1f52 -- include/be/r4.h virt/be/r4.c arch/riscv/be tests/r4
   ```

3. Review contract and fail-closed transaction, then the assembly/linker
   boundary and static checkers. Ask whether every restore remains
   same-management, full-frame, and post-validation.
4. Review the evidence/tool-control graph and retained report schema. Check
   that QEMU remains emulation evidence and that semantic image parity is not
   byte equality.
5. If reproducing, run the checked commands documented in the evidence record;
   preserve the generated-asset result as an open reproducibility question.
   Remove the review worktree only after recording the human decision:

   ```sh
   cd -
   git worktree remove ../beryllium-r4-review
   ```

## 8. Human decision checklist

- [ ] The exact R4 scope matches the accepted runtime plan and the R4/R5 boundary.
- [ ] Claims match the exact-target host, image, and QEMU evidence.
- [ ] Trusted compiler, linker, firmware, emulator, monitor-memory, and
  single-hart assumptions are acceptable.
- [ ] Negative paths cover unexpected observation, bad binding/phase, malformed
  event, sticky failure, evidence tampering, and hostile controls sufficiently.
- [ ] R5/successor work, protected entry, switching, and release work remain excluded.
- [ ] The open generated-asset byte-reproducibility finding is understood.
- [x] **Accept** exact commit `0783dfc6557453fbac0da93a5364f2e6e2cb1f52`
  on 2026-07-29, by explicit instruction `accept exact commit`.
- [ ] Request revisions through a new commit and review packet.
- [ ] Defer the decision while preserving current gates.

Only the acceptance-decision box is checked because that decision was
explicitly supplied by the responsible human. The technical-judgment
checklist remains unchanged as review history; no signature is generated.

## 9. Recorded decision and remaining boundaries

- **Recorded acceptance:** exact implementation target
  `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` is accepted as of 2026-07-29.
- **Packet boundary:** packet commit
  `ec7be2f146a851e7608e77eb2875076e66aab2e6` remains decision support, not
  accepted implementation.
- **Successor and release boundary:** this R4 acceptance authorizes no
  successor. The bounded R5 plan was later separately accepted at exact
  commit `fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30, R5
  implementation was separately authorized under that accepted plan, and
  exact R5 implementation target
  `165f4d001a2b59b582b397bdea79ec4826168fdb` was separately accepted on
  2026-07-30; none of those later decisions was inferred from this R4
  acceptance. R6+ remain unauthorized and not started. No push, tag, public
  release, publication-gate change, hardware claim, or later package is
  authorized.
- **Open finding:** the generated-asset byte-reproducibility finding remains
  open; acceptance does not resolve or close it.
- **Future revisions:** any technical change to accepted R4 inputs requires a
  new exact target and a new explicit responsible-human decision; it does not
  silently inherit this acceptance.

---

**Status:** exact target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` is implemented at the bounded R4
scope, passed the recorded exact-target validation, and was
responsible-human accepted on 2026-07-29. Packet commit
`ec7be2f146a851e7608e77eb2875076e66aab2e6` is not accepted implementation.
The bounded R5 plan was later separately accepted, its implementation
separately authorized (see
[`single-hart-runtime-r5-plan-review-summary.md`](single-hart-runtime-r5-plan-review-summary.md)),
and exact R5 target `165f4d001a2b59b582b397bdea79ec4826168fdb` separately
accepted on 2026-07-30 (see
[`single-hart-runtime-r5-review-summary.md`](single-hart-runtime-r5-review-summary.md));
R6 and every later successor remain separately gated; publication remains
blocked.

**Next:** independently review the open generated-asset reproducibility
finding and keep R6+ gated. Do not amend the accepted R4 target or packet
commit.

**Action required from you:** review the uncommitted acceptance record for
accuracy. No further acceptance choice, R6 authority, or release authority is
implied.
