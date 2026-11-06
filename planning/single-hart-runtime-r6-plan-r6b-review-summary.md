<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R6 plan revision B review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves the packet-time former private repository identity and remote
> state. The current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

This document began as the decision-support packet for one exact immutable
commit — `6d6464c6c937abccd59df932006c1049fd79fac6`, which carries **Plan
revision R6-B**, the narrow correction of two statements the accepted R6 plan
makes *about* D-15's evidence — and now also records the responsible-human
decision taken on it. The decision-support material below is retained
unchanged as review history; it remains the evidence the decision rests on.
Except where a statement is explicitly marked as current, sections 1 through 9
describe the state **at the time of that decision**.

Two earlier R6 plan decisions are untouched by this record and remain exact,
complete, and byte unchanged:

- original plan target `609867fdad75279c0913022909efd65c4a838909`, accepted
  2026-07-30, recorded in
  [`single-hart-runtime-r6-plan-review-summary.md`](single-hart-runtime-r6-plan-review-summary.md);
- corrected plan target `75269f058ae578b0a76a113d6c05c0aaceeac8ec` carrying
  **Plan revision R6-A** (the D-15 injection site), accepted 2026-07-30,
  recorded in
  [`single-hart-runtime-r6-plan-revision-review-summary.md`](single-hart-runtime-r6-plan-revision-review-summary.md).

Revision R6-B changes **no fixture construction**: not D-15's base file, not
its exact `+2 / -0` two-instruction defect, not its declared class, layer,
marker set, disposition, or safety argument. It corrects how the plan records
D-15's image-layout consequence and how R6 retains QEMU trace evidence.

## Decision record

Responsible-human review **accepted the exact R6-B plan-revision commit**
`6d6464c6c937abccd59df932006c1049fd79fac6` (parent
`4d6c3c9b0899c7a30b2150ff0d4067369ccef774`, the R6-A acceptance record) on
2026-07-30, in explicit response to the exact acceptance question posed for
that commit by this packet. The recorded selection was: `Accept exact R6-B
plan commit (Recommended)`.

The revised plan, carrying
[Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention),
is therefore the **plan of record for D-15's L8 expectation and for R6 trace
retention**. The original plan target
`609867fdad75279c0913022909efd65c4a838909` (accepted 2026-07-30) and the
corrected target `75269f058ae578b0a76a113d6c05c0aaceeac8ec` carrying **Plan
revision R6-A** (accepted 2026-07-30) remain **accepted history and byte
unchanged**; this acceptance supersedes only the two evidence-bookkeeping
statements it corrects, and it changes no fixture construction, count, class,
layer, or gate.

No new implementation authorization was requested or given here. Paused R6
integration and evidence work **may resume** under the two already-recorded R6
implementation authorization instructions, preserved verbatim with their
timestamps:

- `proceed to implement R6 exact` (2026-07-30T20:34:36.241+00:00).
- `proceed with all r6 implementation work` (2026-07-30T20:36:53.931+00:00).

Resumption is bounded strictly by the revised plan's scope and keeps every
gate fail-closed. **Every value this revision pins must be re-derived from a
checked run at the exact future implementation commit**: the exactly 2
differing runs and 10 differing bytes at the stated per-toolchain offsets, the
unchanged `.monitor.text` allocated size, the unchanged checker-fixed and
checker-required allocated symbol addresses, the per-run semantics records,
digests, byte counts, and bounded excerpts, and the measured retained-evidence
size under the unrelaxed `<= 512 MiB` gate. A mismatch fails R6 and forces
another plan revision; the harness must not relax, widen, recompute, or
auto-adopt an observed value.

Packet commit `325117f4b2d2bac4a864221d3457295f8ff385ab`
(`docs: add R6-B plan review packet`) and this acceptance-record commit are
**decision support only**. Neither is plan text and neither is implementation;
the accepted plan-revision target remains exactly
`6d6464c6c937abccd59df932006c1049fd79fac6` over parent
`4d6c3c9b0899c7a30b2150ff0d4067369ccef774`, byte unchanged.

This decision applies only to that exact immutable plan commit. It does
**not** accept any R6 implementation, any local `tests/r6/` work, or any R6
evidence, report, coverage, or acceptance claim; local R6 implementation
remains unreviewed, unaccepted, and incomplete, and no D-15 result is
reproduced, retained, or claimed here. It does not resolve the open
generated-asset byte-reproducibility finding, and it does not authorize R7,
hardware validation, formal-verification claims, a tag, a push, publication,
or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `6d6464c6c937abccd59df932006c1049fd79fac6` (`docs: correct R6 image and trace retention plan`), parent `4d6c3c9b0899c7a30b2150ff0d4067369ccef774` (`docs: accept corrected R6 D15 plan`). Branch `beryllium/single-hart-runtime-r0`. |
| Prior accepted plan targets | `609867fdad75279c0913022909efd65c4a838909` (original, accepted 2026-07-30) and `75269f058ae578b0a76a113d6c05c0aaceeac8ec` (corrected, carrying revision R6-A, accepted 2026-07-30). Both remain **accepted history and byte unchanged**. Their packet commits `21cf80daa2021590378de81d7a094e14f4e5c8ca` and `fd3e18477da24868edb53d492a0ed7d2636ac79d`, and the acceptance records `4bff41764cf8ec9275e771cd3c1ce124961da93a` and `4d6c3c9b0899c7a30b2150ff0d4067369ccef774`, are decision support: none is plan text and none is implementation. |
| Current status | Plan revision R6-B is **accepted** at exact commit `6d6464c6c937abccd59df932006c1049fd79fac6` on 2026-07-30, after automated mechanism, evidence, and governance review. R6 implementation continues to exist only as local, untracked, unreviewed, unaccepted, incomplete work; **paused R6 integration and evidence work may now resume** under the already-recorded implementation authorization, within the revised plan's scope, with every pinned value re-derived at the exact implementation commit. |
| Decision recorded | Accept exact R6-B plan-revision commit `6d6464c6c937abccd59df932006c1049fd79fac6` (recorded selection `Accept exact R6-B plan commit (Recommended)`, 2026-07-30). |
| Successor status | R7 is gated, undefined, not authorized, and **not started**. No R6 implementation review packet, evidence bundle, coverage figure, or acceptance record is requested, recorded, or implied here. |
| Publication status | `jamorris_microsoft/beryllium` is `PRIVATE`. The target is local, unpushed, and untagged: zero remote branches and zero tags contain it. Push, tag, publication, and release remain blocked. |

**Action expected:** no further plan-acceptance decision is pending for this
exact SHA. Revision R6-B is accepted as **plan text only**, and paused R6
integration and evidence work may resume under the already-recorded R6
implementation authorization. It accepts no R6 implementation, no R6 evidence,
and no successor package; a complete R6 implementation still requires its own
exact-commit review packet and its own separate acceptance, and any tag, push,
publication, release, or R7 start requires separate explicit authorization.

## 2. Deliverables and exact inventory

The parent delta is **84 changed entries, 779 insertions, 343 deletions**:
nine non-generated source paths and 75 generated `docs/html/` entries (12 of
the 84 entries are renames of hash-named assets). No `tests/r6/`
implementation, no `build/` artifact, no `include/`, `virt/`, or `arch/` file,
no `Makefile`, `be`, `scripts/check-be.sh`, or `tests/**` change, no
acceptance pin, and no `pathfinder/publication-gate.conf` change is present.

| Deliverable | Paths | Purpose | Trust / privilege boundary | Primary human question |
| --- | --- | --- | --- | --- |
| Plan revision R6-B | `planning/single-hart-runtime-r6-plan.md` (+362 / -32) | Add [Plan revision R6-B](single-hart-runtime-r6-plan.md#plan-revision-r6-b-d-15-image-layout-and-trace-retention) and apply it: corrected D-15 layout arithmetic and exactly pinned L8 delta; raw QEMU traces made ephemeral scratch with bounded per-run extraction; report schema, retention, acceptance criteria, non-claims, and review-gate checklist updated to match. | Plan text only. It creates no privileged surface, links no image, and executes nothing. | Are the corrected layout account and the bounded retention rule *right*, and are both pinned fail-closed rather than adaptive? |
| Revision R6-A record annotation | `planning/single-hart-runtime-r6-plan-revision-review-summary.md` (+17 / -3) | Add a navigation-only successor note and annotate the one superseded invariant row, without altering the recorded acceptance. | Historical decision record; it adds no new decision. | Does the annotation correct a fact while leaving the R6-A acceptance exact, complete, and byte unchanged? |
| Status and navigation sources | `.github/copilot-instructions.md` (+5 / -3), `README.md` (+8 / -3), `planning/README.md` (+27 / -6), `planning/HANDOFF.md` (+41 / -6), `planning/implementation-plan.md` (+18 / -3), `planning/roadmap.md` (+12 / -6), `planning/.vitepress/config.mts` (+3 / -3) | State plan-accepted-through-R6-A, revision R6-B drafted and not accepted, R6 integration/evidence/acceptance paused, implementation local and unaccepted. | Markdown is authoritative; navigation is documentation only. | Does every status surface avoid implying that revision R6-B, or any implementation, is accepted? |
| Generated planning site | `docs/html/**` (75 entries) | Render the changed authoritative Markdown. | Derivative, non-normative output; hash-named asset byte reproducibility remains an open finding. | Is rendering functional without treating generated-asset churn as resolved? |

### Non-generated paths in the target

```text
.github/copilot-instructions.md
README.md
planning/.vitepress/config.mts
planning/HANDOFF.md
planning/README.md
planning/implementation-plan.md
planning/roadmap.md
planning/single-hart-runtime-r6-plan-revision-review-summary.md
planning/single-hart-runtime-r6-plan.md
```

Reproduce the inventory without interpretation:

```sh
git diff --name-status -M 4d6c3c9b0899c7a30b2150ff0d4067369ccef774 6d6464c6c937abccd59df932006c1049fd79fac6
git diff --shortstat 4d6c3c9b0899c7a30b2150ff0d4067369ccef774 6d6464c6c937abccd59df932006c1049fd79fac6
git diff --shortstat 75269f058ae578b0a76a113d6c05c0aaceeac8ec 6d6464c6c937abccd59df932006c1049fd79fac6 -- planning/single-hart-runtime-r6-plan.md
```

Against the **accepted corrected plan target**
`75269f058ae578b0a76a113d6c05c0aaceeac8ec`, the plan document itself changes
by **408 insertions and 67 deletions** in one file.

This packet's own commit `325117f4b2d2bac4a864221d3457295f8ff385ab` and the
later acceptance-record commit that adds the decision above are **decision
support only**. Neither is the review target, neither is plan text, and
neither is implementation.

## 3. Claim boundary

### What the exact target supports saying

- It states a **narrow plan correction**. It withdraws one factually wrong
  layout claim, replaces one arithmetically impossible retention rule, and
  pins both replacements exactly and fail-closed.
- It preserves the accepted plan's fixture construction and counts: the
  47-entry catalogue with 46 single-defect fixtures, 52 image build attempts,
  44 successful links, 8 link failures, 64 QEMU runs, the 14 static / 17 host
  / 15 dynamic / 1 control partitioning, the 29 primary classes with 0
  uncovered and 4 secondary claims, the detection layers, the outcome taxonomy
  and marker vocabulary, the wrong-error-class and layer-shift gates, the
  acceptance-pin refresh scope, the recorded implementation authorization, and
  every R7, publication, hardware, and formal non-claim.
- It supports the reasoning in
  [Defect 1](single-hart-runtime-r6-plan.md#defect-1-the-d-15-layout-arithmetic-was-factually-wrong),
  [Defect 2](single-hart-runtime-r6-plan.md#defect-2-the-planned-raw-trace-retention-is-impossible),
  and the two corrected rules that follow them.

### What it does not support saying

- It is **not implementation evidence**. No R6 build, run, report, digest,
  coverage number, evidence bundle, or acceptance claim exists at this target.
- The measured values it pins — the 10 differing bytes in 2 runs, the exact
  offsets, the `.monitor.text` sizes, the `st_size` change, the debug-section
  deltas, the ~310-370 MiB raw-trace size — were **observed in the local,
  untracked, unreviewed `tests/r6/` working tree**, which is outside this
  commit and is not accepted evidence. They are recorded as the plan's
  normative expectation, and they **must be re-derived from a checked run at
  the exact future implementation commit** rather than trusted from this text.
- The plan's own
  [expected deterministic result](single-hart-runtime-r6-plan.md#expected-deterministic-result)
  table remains explicitly `NOT RUN / unverified as retained R6 evidence`.
- One preserved-count nuance, stated plainly: the **mutation self-test table
  does change**. It gains one row — D-15 pinned-delta mutation, minimum 8
  cases (an extra differing byte, a missing pinned byte, a relocated pinned
  run, and a `.monitor.text` size change, each rejected per toolchain) — and
  the acceptance criteria gain items 17 and 18. Those additions exist to
  enforce the two corrections; the catalogue, partition, run-matrix, class,
  layer, and disposition counts are unchanged.

### Trusted or assumed

Pinned GCC, Clang, GNU ld, lld, QEMU, OpenSBI, and `readelf`/disassembler
behavior; the accepted R5 sources, linker script, and checkers as written; the
correspondence between inspected ELF metadata and the extracted flat image;
and the accuracy of the local measurements this revision pins, subject to the
mandatory re-derivation gate above.

### Explicit non-claims

This target does not implement, accept, or claim: any R6 fixture, harness,
report, or evidence bundle; R6 coverage; R6 implementation acceptance; raw
QEMU trace byte identity across launches; R7; exact-byte proof; hardware
validation; formal verification or refinement; Linux, service, guest-SBI,
device, DMA, timer, interrupt-controller, multicore, policy, CHERI, or TE
behavior; resolution of the open generated-asset byte-reproducibility finding;
or any tag, push, publication, or release authority.

## 4. Load-bearing corrections

Both corrections are planned text at this target, not measured evidence at
this target.

### Correction 1 — D-15 image layout, pinned exactly

| Corrected statement | Plan reference | Evidence boundary |
| --- | --- | --- |
| **Withdrawn:** the accepted plan's claim that D-15's two inserted instructions make `.monitor.text` "grow by 8 bytes" and "deterministically shift the monitor code after the insertion point". Both statements are false, and an L8 expectation written from them would declare a delta that cannot occur. | [Defect 1](single-hart-runtime-r6-plan.md#defect-1-the-d-15-layout-arithmetic-was-factually-wrong) | Withdrawal of a plan claim; nothing is asserted as evidence. |
| **Padding consumption.** The accepted `arch/riscv/be/r5-trap.S` ends `be_r5_switch_tail` with `j be_r5_enter_guest_tail` and aligns the shared entry tail with `.align 4`, which already emits **12 bytes of `nop` padding** (three `00000013` words). The two inserted 4-byte `csrsi` instructions consume **8 of those 12 bytes**; 4 bytes of padding remain and `be_r5_enter_guest_tail` keeps its accepted address. The tail `j` moves 8 bytes later inside the same padding window, its immediate changing `+0x10` -> `+0x8`, still targeting the unmoved label. | [Defect 1](single-hart-runtime-r6-plan.md#defect-1-the-d-15-layout-arithmetic-was-factually-wrong) | Planned account, derived from the accepted assembly and confirmed by local unreviewed `readelf`/disassembly. Re-derivation required. |
| **Allocated size and flat extent unchanged.** `.monitor.text` keeps its accepted allocated size — `0x7610` under GCC, `0x7640` under Clang — and the extracted flat image stays `212992` bytes under both toolchains, exactly as in the same-toolchain control image. Every allocated section's address, file offset, size, flags, and content outside the pinned delta is unchanged. | [Defect 1](single-hart-runtime-r6-plan.md#defect-1-the-d-15-layout-arithmetic-was-factually-wrong) | Same. This is the runtime/flat-image invariant the corrected L8 expectation rests on. |
| **Exactly 10 differing bytes in exactly 2 differing runs per toolchain**, at fixed flat-image offsets: GCC `{start: 30032, length: 9}` and `{start: 30042, length: 1}`; Clang `{start: 30080, length: 9}` and `{start: 30090, length: 1}`. Offset `30032` is `0x7550` (virtual `0x80207550`) under GCC; `30080` is `0x7580` (virtual `0x80207580`) under Clang. The 9-byte run is the two inserted words plus the first byte of the relocated `j`; the byte at `+9` is coincidentally equal in both images, and the jump immediate's next byte (`0x00` -> `0x80`) forms the 1-byte run at `+10`. That coincidence is why the delta is two runs rather than one 11-byte range. | [Corrected D-15 L8 expectation](single-hart-runtime-r6-plan.md#corrected-d-15-l8-expectation-pinned-exactly) | Planned normative expectation, `NOT RUN` as retained R6 evidence. A future checked L8 run must reproduce these values exactly. |
| **Symbol invariant scoped to allocated symbols only.** Every defined allocated `FUNC`/`OBJECT` symbol the accepted checker fixes by address (`be_reset`, `be_r5_management_fixture[_end]`, `be_r5_protected_fixture[_end]`) or requires by presence (including `be_r5_switch_tail` and `be_r5_enter_guest_tail`) keeps its accepted address in both toolchains. This is deliberately **not** an "no symbol changes at all" claim: `be_r5_switch_tail`'s address is unchanged but its recorded `st_size` grows `212` -> `220`, and an `st_size` is not an address, not an allocated-section size, and not a flat-image byte. | [Defect 1](single-hart-runtime-r6-plan.md#defect-1-the-d-15-layout-arithmetic-was-factually-wrong) | Planned; the narrower claim is the one the accepted checker can actually enforce. |
| **Non-allocated debug and symbol-table changes are explicitly excluded.** GCC: `.debug_line` grows `0xe89c` -> `0xe8a8` (+12), shifting the file offsets of `.debug_str`, `.debug_frame`, `.symtab`, `.strtab`, `.shstrtab` and the section header table, with the whole ELF growing a net **+8 bytes**. Clang: `.debug_line` grows `0x6e0e` -> `0x6e10` (+2) and `.debug_aranges`'s offset shifts by the same +2, while `.symtab`, `.strtab`, `.shstrtab`, and total ELF size are unchanged, and **12 local `$d` mapping symbols** move (ten into `.debug_str` content, two into `.debug_line`). None carries `SHF_ALLOC`, none is loaded, mapped into the flat image, or executed. `tests/r6/check-fixture-image.mjs` does not pin them and must not start pinning them; they may appear in report metadata as observed facts, never as a pinned expectation or a runtime claim. | [Explicit non-runtime changes](single-hart-runtime-r6-plan.md#explicit-non-runtime-changes-debug-and-symbol-table-sections) | Planned exclusion. This is the load-bearing scope boundary that keeps the L8 pin true rather than over-broad. |
| **Fail-closed, never adaptive.** The checker must pin the differing-run count (`2`), the differing-byte count (`10`), the exact `{start, length}` pairs, the unchanged `.monitor.text` allocated size, and the unchanged fixed/required allocated symbol addresses. Any extra differing byte, missing declared byte, relocated offset, third run, or `.monitor.text` size change is a **rejection**. The harness must not relax, widen, recompute, or auto-adopt an observed delta; a mismatch fails R6 and forces a further plan revision. | [Corrected D-15 L8 expectation](single-hart-runtime-r6-plan.md#corrected-d-15-l8-expectation-pinned-exactly) | Mandatory future gate, extended by 8 new mutation self-test cases. |

### Correction 2 — QEMU trace retention

| Corrected statement | Plan reference | Evidence boundary |
| --- | --- | --- |
| **Withdrawn as impossible.** The accepted plan required retaining "the first trace log of each fixture/toolchain pair (32 traces)" while capping retained evidence at 512 MiB. One run's `in_asm,cpu` trace is roughly **310-370 MiB**; 32 are about **10.6-11.5 GiB** and all 64 about **21 GiB**, i.e. 20x to 40x over the plan's own cap. The retention rule, not the cap, was wrong. | [Defect 2](single-hart-runtime-r6-plan.md#defect-2-the-planned-raw-trace-retention-is-impossible) | Arithmetic against the plan's own bound. |
| **Raw traces are ephemeral build scratch.** For each of the 64 runs, `tests/r6/run-qemu.sh` writes the raw trace under `build/r6/`, `tests/r6/check-dynamic.mjs --extract` derives (1) the canonical semantics record `be-r6-run-semantics-v1`, (2) the raw trace's SHA-256, (3) its exact byte count, and (4) a bounded head/tail excerpt of at most the first 400 and last 800 lines — and the raw trace is then **deleted** before the next run starts. | [Corrected retention rule](single-hart-runtime-r6-plan.md#corrected-retention-rule-raw-traces-are-ephemeral) | Planned harness rule; the local unreviewed implementation already streams and deletes this way. |
| **Uniform per-run retention for all 64 runs.** Retained evidence holds the report, all 64 console logs, all 64 exit-status files, all **64** canonical semantics records (each carrying its raw-trace SHA-256 and byte count), all **64** bounded excerpts, the fixture catalogue and per-fixture manifests, static rejection transcripts, the 30 scratch preparation banners, image manifests, the coverage ledger, the claim ledger, and `artifacts.sha256` over every retained byte. No run's evidence is silently thinner than another's. | [Corrected retention rule](single-hart-runtime-r6-plan.md#corrected-retention-rule-raw-traces-are-ephemeral) | Planned. Replaces the accepted plan's asymmetric "first trace of each pair" rule. |
| **No raw trace log is retained under any circumstance.** A raw trace is never copied into `build/r6/evidence/`, never digested into `artifacts.sha256` as a file, and never published. `tests/r6/generate-evidence.sh` must fail closed if any file matching a raw-trace path reaches the evidence tree, and `tests/r6/check-report.mjs` must fail closed if any of the 64 runs lacks its semantics record, raw-trace digest, byte count, or bounded excerpt. | [Corrected retention rule](single-hart-runtime-r6-plan.md#corrected-retention-rule-raw-traces-are-ephemeral) | Two planned fail-closed gates plus acceptance criterion 17. |
| **`<= 512 MiB` remains a hard, unrelaxed gate**, enforced by measurement rather than by the plan's estimate that per-run retained artifacts are tens of kilobytes. Exceeding it is a failure requiring plan revision, never a larger cap chosen after the fact. | [Corrected retention rule](single-hart-runtime-r6-plan.md#corrected-retention-rule-raw-traces-are-ephemeral) | Unchanged bound; only the retention rule inside it changed. |
| **Raw-trace byte identity is an explicit non-claim.** The report schema `be-r6-adversarial-images-v1` records `trace_sha256[]`, `trace_bytes[]`, `trace_excerpt_sha256[]`, and `raw_trace_retained: false` per run. Each digest and byte count is an observed fact about a deleted scratch file; equality across runs or toolchains is neither required nor claimed. Canonical semantics, console digests, and the generated report remain the reproducible artifacts, and the inherited R5 semantic-versus-byte boundary is unchanged. | [Corrected retention rule](single-hart-runtime-r6-plan.md#corrected-retention-rule-raw-traces-are-ephemeral), plan non-claims | Planned non-claim, added explicitly to the plan's non-claim list. |

### Governance invariants preserved by this target

| Invariant | Plan reference | Status |
| --- | --- | --- |
| The original and R6-A acceptances remain exact, complete, and byte unchanged; the R6-A record's superseded row is annotated, not rewritten, and records no decision on R6-B. | [Status and decision](single-hart-runtime-r6-plan.md#status-and-decision) | Verified in the diff (section 7). |
| While revision R6-B is unaccepted, `tests/r6/check-acceptance.sh` must report `r6_plan_acceptance` as **not accepted** for any package depending on the corrected layout expectation or retention rule, and R6 integration, evidence, and acceptance stay paused. *Current as of this record:* revision R6-B is accepted at exact commit `6d6464c6c937abccd59df932006c1049fd79fac6`, so a package matching that exact target may report `accepted`; the same rule still binds any later unaccepted revision. | [Report, retention, and reproducibility](single-hart-runtime-r6-plan.md#report-retention-and-reproducibility), acceptance criterion 18 | Planned; the pause was stated on every status surface at review time. |
| Accepted R0-R5 bytes remain immutable; the defect exists only as a fixture overlay in a confined scratch tree, and `tests/r5/check-acceptance.sh --require` still reports accepted target `165f4d001a2b59b582b397bdea79ec4826168fdb` unchanged. | [Immutable accepted bytes](single-hart-runtime-r6-plan.md#immutable-accepted-bytes) | This target changes no accepted file; R1-R5 acceptance checkers pass (section 6). |
| R7, hardware validation, formal verification, tag, push, publication, and release remain excluded and unclaimed. | [Publication, R7, and governance](single-hart-runtime-r6-plan.md#publication-r7-and-governance) | Unchanged from the accepted plan. |

## 5. Review history and findings

All reviews recorded in this section are **automated in-session reviews**,
independent of one another but not responsible-human review. At the time they
were recorded, no responsible-human review or acceptance of revision R6-B had
occurred; the responsible-human decision itself is in the
[decision record](#decision-record) above.

### Closed findings

1. **The two plan defects were found by an independent read-only dynamic
   implementation review, not assumed.** That review covered all 15 dynamic
   fixtures plus the control, the checker allowlists, differential and
   eligibility rules, the 64-run QEMU semantics, the resumed D-15 path, and
   artifact retention and mutations. It established that the accepted plan's
   `.monitor.text` growth arithmetic contradicts the accepted tail's own
   `.align 4` padding, and that the accepted 32-raw-trace retention rule
   cannot fit the accepted 512 MiB cap.
2. **Dynamic-harness defects found by the same review were fixed in the local
   implementation and re-reviewed clean.** Real image-byte L8 mutations
   replaced synthetic ones, per-entry forbidden-marker and console gates were
   applied to every dynamic fixture, sandbox confinement was tightened, and
   self-test counts were corrected. Those fixes live in the untracked
   `tests/r6/` tree; they are **outside this commit** and are not evidence for
   it. This target only records the plan consequence: one new mutation
   self-test row of 8 minimum cases.
3. **Mechanism review of the drafted revision found an over-broad scope claim,
   and it was fixed before this target.** The draft asserted an unqualified
   "no symbol moves / nothing else changes" invariant. That is false for
   non-allocated content. The target now scopes the unchanged-layout pins to
   allocated sections and to defined allocated `FUNC`/`OBJECT` symbols in the
   accepted checker's fixed and required sets, states `be_r5_switch_tail`'s
   `st_size` `212` -> `220` explicitly, and records the GCC and Clang
   debug/symbol-table file-offset changes and the 12 Clang local `$d` mapping
   symbols accurately as excluded, never-loaded metadata.
4. **Evidence-boundary review verified the non-overclaiming boundary.**
   Retention wording, the measured layout facts, the report schema fields, the
   unchanged hard cap, the provenance of the measurements, the exactness of
   the prior acceptance history, and the paused status were each checked as
   stated rather than implied.
5. **Final mechanism review and final evidence/governance review of the
   content that became this target were clean.** The correction is narrow, the
   catalogue and run counts are preserved, the added self-test row and
   acceptance criteria are enforcement rather than scope creep, the prior
   acceptances are left intact, and no acceptance, authorization, or evidence
   claim is asserted.

### Open questions requiring human judgment

- **Accept a corrected design whose measured pins come from implementation
  outside the target.** Every number this revision pins was observed in the
  local, untracked, unreviewed `tests/r6/` tree. Nothing at this commit proves
  them. The revision asks to be judged on whether the corrected layout
  account, the exactly pinned fail-closed L8 expectation, and the bounded
  retention rule are *right*, backed by the mandatory re-derivation gate: if a
  checked run at the future exact implementation commit disagrees with any
  pinned value, the fixture fails and the plan is revised again — the harness
  must not adapt.
- **Is bounded extraction sufficient forensic depth?** Retained evidence will
  hold canonical semantics, digests, byte counts, and 400-head/800-tail
  excerpts, but never a raw trace. A future investigation needing full trace
  context must re-run rather than re-read.
- **Open finding, unchanged:** generated hash-named asset byte reproducibility
  remains unresolved. This packet does not call it resolved.

## 6. Validation and evidence boundary

On 2026-08-01, against a working tree whose **tracked** content equals exact
target `6d6464c6c937abccd59df932006c1049fd79fac6` plus this packet and its
status/navigation updates — that is, equivalent plan content, not a rerun of
the immutable target itself:

| Command | Result | What it covers |
| --- | --- | --- |
| `npm run docs:build` | pass | VitePress build of the authoritative planning Markdown, including this packet and the revised plan. |
| `./be docs-check` | pass | Planning and Helium documentation gates, including the static direct-file render inventory. |
| `./scripts/check-be.sh` | pass | Wrapper dispatch graph, SPDX/copyright headers, and retained Helium delegation. |
| `git diff --check` | pass | No whitespace defects in the staged documentation change. |
| `git diff --name-status -M`, `git diff --shortstat` | pass | Exact inventory of the target and of the plan delta against the accepted corrected plan target. |
| `tests/r1..r5/check-acceptance.sh --require` | pass | Accepted R1-R5 targets, including `165f4d001a2b59b582b397bdea79ec4826168fdb`, are unchanged by this documentation work. |

**Execution boundary.** The review target is the exact immutable commit
`6d6464c6c937abccd59df932006c1049fd79fac6`. This packet commit
`325117f4b2d2bac4a864221d3457295f8ff385ab` and the later acceptance-record
commit that adds the decision above are **separate follow-up commits**; their
own documentation build, render gate, wrapper check, and diff checks validate
decision-support content, not the target. Neither follow-up changes, amends,
or re-validates the target, and neither is R6 implementation.

**Not run and not retained:**

- No R6 host, image, emulation, report, or evidence gate ran as part of this
  documentation change. `tests/r6/` is untracked, excluded from the commit,
  never staged, and not exercised or cited as acceptance evidence.
- No R6 report, claim ledger, digest set, coverage figure, or evidence bundle
  exists or is accepted. R6 integration, evidence, and acceptance were paused
  at review time; *current as of this record*, they may resume under the
  already-recorded implementation authorization, and nothing produced by that
  resumption is accepted evidence until its own exact-commit review and
  separate acceptance.
- No checked D-15 build, image check, or QEMU run is retained, reproducible,
  or accepted as evidence for this target. The numbers this revision pins are
  local unreviewed discovery awaiting re-derivation.
- Hardware validation and formal verification remain `NOT RUN` and unclaimed.

## 7. Recommended human review sequence

Use an isolated detached worktree so the concurrently changing untracked
`tests/r6/` tree cannot affect what you read.

1. **Identity and boundary.** Confirm the target, its parent, the private
   repository state, and that no remote ref or tag contains it.
2. **The decision delta.** Read the plan delta against the accepted corrected
   plan target `75269f058ae578b0a76a113d6c05c0aaceeac8ec` first; it is the
   decision.
3. **Correction 1.** Read
   [Defect 1](single-hart-runtime-r6-plan.md#defect-1-the-d-15-layout-arithmetic-was-factually-wrong),
   [the non-runtime exclusions](single-hart-runtime-r6-plan.md#explicit-non-runtime-changes-debug-and-symbol-table-sections),
   and
   [the pinned L8 expectation](single-hart-runtime-r6-plan.md#corrected-d-15-l8-expectation-pinned-exactly)
   end to end. Judge the padding account, the two-run/10-byte pin, the
   allocated-only symbol scope, and the explicit debug exclusions.
4. **Correction 2.** Read
   [Defect 2](single-hart-runtime-r6-plan.md#defect-2-the-planned-raw-trace-retention-is-impossible)
   and
   [the corrected retention rule](single-hart-runtime-r6-plan.md#corrected-retention-rule-raw-traces-are-ephemeral).
   Judge ephemeral raw traces, uniform 64-run retention, the two fail-closed
   evidence gates, the unrelaxed cap, and the raw-identity non-claim.
5. **The non-evidence boundary.** Read
   [Status of the measurements](single-hart-runtime-r6-plan.md#status-of-the-measurements-behind-this-revision)
   and confirm the local implementation measurements are excluded from the
   acceptance basis and subject to re-derivation.
6. **Unchanged scope.** Spot-check that the catalogue, partitions, run matrix,
   layers, classes, dispositions, ledger, claims, and non-claims are
   preserved, and that the only additions are the enforcement self-test row
   and acceptance criteria 17 and 18.
7. **Status surfaces.** Confirm that, at review time, no status document
   claimed revision R6-B, or any implementation, was accepted.

```sh
git show -s --format=fuller 6d6464c6c937abccd59df932006c1049fd79fac6
git branch -r --contains 6d6464c6c937abccd59df932006c1049fd79fac6
git tag --contains 6d6464c6c937abccd59df932006c1049fd79fac6
git diff --check 4d6c3c9b0899c7a30b2150ff0d4067369ccef774 6d6464c6c937abccd59df932006c1049fd79fac6
git diff --name-status -M 4d6c3c9b0899c7a30b2150ff0d4067369ccef774 6d6464c6c937abccd59df932006c1049fd79fac6

# The decision delta: revised plan against the accepted corrected plan target.
git diff 75269f058ae578b0a76a113d6c05c0aaceeac8ec 6d6464c6c937abccd59df932006c1049fd79fac6 -- planning/single-hart-runtime-r6-plan.md
git diff 4d6c3c9b0899c7a30b2150ff0d4067369ccef774 6d6464c6c937abccd59df932006c1049fd79fac6 -- planning/single-hart-runtime-r6-plan-revision-review-summary.md

# Isolated read-only inspection at the exact target.
git worktree add --detach .review-r6b 6d6464c6c937abccd59df932006c1049fd79fac6
(cd .review-r6b && sed -n '/^## Plan revision R6-B/,/^## Prerequisites and objective/p' planning/single-hart-runtime-r6-plan.md)
(cd .review-r6b && sed -n '/^## Mutation and self-tests/,/^## Report, retention/p' planning/single-hart-runtime-r6-plan.md)
(cd .review-r6b && ./be docs-check && ./be status)
git worktree remove .review-r6b
```

The decision-support material for the two already accepted plan targets
remains in
[`single-hart-runtime-r6-plan-review-summary.md`](single-hart-runtime-r6-plan-review-summary.md)
and
[`single-hart-runtime-r6-plan-revision-review-summary.md`](single-hart-runtime-r6-plan-revision-review-summary.md);
this packet does not restate or replace either.

## 8. Human decision checklist

The technical-judgment items below remain unchecked as review history. Only
the explicitly supplied decision is marked; automation does not answer,
pre-check, or sign for the questions, and checking them is not inferred from
the decision. No signature is generated on the responsible human's behalf.

- [ ] **Correction 1 is right.** The `.align 4` padding account replaces the
  false "grows by 8 bytes" claim correctly; `.monitor.text`'s allocated size
  (`0x7610` GCC, `0x7640` Clang) and the `212992`-byte flat extent are
  genuinely unchanged; and the pinned L8 delta — exactly 2 runs, exactly 10
  bytes, at exactly the stated per-toolchain offsets — is the right fail-closed
  expectation.
- [ ] **Correction 1's scope is right.** Pinning only allocated sections and
  the accepted checker's fixed and required allocated `FUNC`/`OBJECT` symbol
  addresses, recording `be_r5_switch_tail`'s `st_size` `212` -> `220`, and
  explicitly excluding non-allocated GCC/Clang debug and symbol-table changes
  (including the 12 Clang local `$d` mapping symbols) is accurate and
  sufficient.
- [ ] **Correction 2 is right.** Making raw QEMU traces ephemeral scratch —
  extracted into canonical semantics, a SHA-256, a byte count, and a bounded
  400/800-line excerpt, then deleted — resolves the impossible 32-trace rule;
  retaining console, status, semantics, and excerpt artifacts for all 64 runs
  is sufficient; the `<= 512 MiB` gate stays hard and unrelaxed; and
  raw-trace byte identity is correctly an explicit non-claim.
- [ ] **The evidence boundary is acceptable.** The pinned values are local,
  unreviewed implementation discovery outside this commit, must be re-derived
  from a checked run at the exact implementation commit, and any mismatch
  forces another plan revision rather than a run-time relaxation.
- [ ] **Scope is unchanged.** The 47-entry catalogue, partitions, 64-run
  matrix, layers, classes, dispositions, ledger entries, supported claims, and
  non-claims match the accepted corrected plan; the only additions are the
  D-15 pinned-delta self-test row (8 cases) and acceptance criteria 17 and 18.
- [ ] **History and pause are correct.** The original and R6-A acceptances
  remain exact and byte unchanged; R6 integration, the evidence bundle, the
  report claim, and R6 acceptance remain paused; local `tests/r6/` work
  remains unreviewed and unaccepted.
- [ ] **Successor work remains excluded.** R7, hardware validation, formal
  verification, tag, push, publication, and release remain prohibited.
- [x] **Decision:** accept exact commit
  `6d6464c6c937abccd59df932006c1049fd79fac6` / ~~request revisions~~ /
  ~~defer~~.

Only the decision box above is checked, because that decision was explicitly
supplied by the responsible human on 2026-07-30. No signature is generated.

## 9. After the decision

### Recorded outcome: the exact commit is accepted

Exact plan-revision target `6d6464c6c937abccd59df932006c1049fd79fac6` (parent
`4d6c3c9b0899c7a30b2150ff0d4067369ccef774`) was accepted on 2026-07-30, and
this record names that SHA and date. The follow-up acceptance-record commit is
decision support, not plan text and not implementation.

The revised plan is now the plan of record for D-15's L8 expectation and for
R6 trace retention, and paused R6 integration and evidence work **may resume**
under the **already recorded** implementation authorization instructions
(`proceed to implement R6 exact`, `proceed with all r6 implementation work`),
strictly within the revised plan's scope.

Every pinned value must be re-derived from a checked run at the exact future
implementation commit. A mismatch fails R6 and forces another plan revision;
no expectation, pinned delta, or retention gate may be relaxed at run time.

Acceptance of this revision accepts **no** R6 implementation, no local
`tests/r6/` work, and no R6 evidence, report, or coverage claim. Local R6
implementation remains unreviewed, unaccepted, and incomplete, and a complete
R6 implementation still requires its own exact-commit review packet and its
own separate acceptance.

### Prohibited until separate authorization

- No R6 tag, private push, public release, or change to
  `pathfinder/publication-gate.conf`.
- No R7 start; R7 remains undefined, gated, and not authorized.
- No acceptance of any R6 implementation, and no presentation of local
  `tests/r6/` output as accepted R6 evidence.
- No run-time relaxation of any fixture expectation, pinned delta, or
  retention gate.
- No modification of any accepted R0-R5 byte beyond the six enumerated
  acceptance-pin constants the accepted plan authorizes.
- No hardware-validation or formal-verification claim; both remain `NOT RUN`.
- The open generated-asset byte-reproducibility finding remains unresolved;
  this acceptance does not resolve it.

### Not taken: request revisions

Had revisions been requested, a new commit and a new review packet would have
been prepared, this SHA would not have been treated as accepted, R6
integration, evidence, and acceptance would have stayed paused, and no
dependent work would have started.

### Not taken: defer

Had the decision been deferred, the original and R6-A plan targets would have
stayed the only accepted plan text, revision R6-B would have stayed
unaccepted, R6 integration, evidence, and acceptance would have stayed paused,
and no dependent work would have started.

---

**Status:** exact plan-revision target
`6d6464c6c937abccd59df932006c1049fd79fac6` (parent
`4d6c3c9b0899c7a30b2150ff0d4067369ccef774`) is **accepted** as of 2026-07-30.
The original R6 plan target `609867fdad75279c0913022909efd65c4a838909` and the
corrected R6-A target `75269f058ae578b0a76a113d6c05c0aaceeac8ec` remain
accepted history, exact and byte unchanged. R6 implementation exists only as
local, untracked, unreviewed, unaccepted, incomplete work; R6 integration and
evidence work may resume under the already-recorded implementation
authorization but no R6 evidence, report, coverage figure, or implementation
acceptance exists or is claimed here. R7 is not started; hardware validation
and formal verification are `NOT RUN`; push, tag, publication, and release
remain blocked.

**Next:** bounded R6 integration and evidence work may resume within the
accepted revised plan's scope, with every pinned value re-derived from a
checked run at the exact implementation commit and every fail-closed gate
enforced rather than relaxed. No local implementation result may be presented
as accepted R6 evidence, and completion of R6 requires its own exact-commit
review and separate acceptance.

**Action required from you:** none for this decision. Plan-revision acceptance
is recorded. R6 implementation acceptance, tagging, pushing, publication,
release, and R7 all remain prohibited without separate explicit authorization.
