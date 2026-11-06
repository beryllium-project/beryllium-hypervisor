<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R8 plan review and acceptance record

> **Repository rehoming note (current-line editorial context):** This record
> preserves its packet-time former private repository and remote-containment
> state. The current active private repository is
> `beryllium-project/beryllium-hypervisor`; use
> [project orientation](project-orientation.md) for current repository
> guidance.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact planning commit `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` |
| Parent / comparison base | `742ce4450dc85fc632d2ca7ff1061de09f3cf171` (`docs: record exact R7 implementation acceptance`) |
| Branch | `beryllium/single-hart-runtime-r0`; target is one private local commit ahead of `origin/beryllium/single-hart-runtime-r0` at packet preparation time |
| Repository | Packet-time private repository `jamorris_microsoft/beryllium` (`PRIVATE`); current active private repository `beryllium-project/beryllium-hypervisor` |
| Current status | Exact R8 plan accepted on 2026-08-07; separate implementation authorization now permits only non-privileged R8-H0 work; no H0 acceptance, K3 execution, or hardware result |
| Plan decision | Accepted exact plan commit `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` by explicit instruction `accept exact 7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` |
| Implementation authorization | Separate instruction `Authorize R8 implementation under accepted plan 7d0f0cbf…; proceed with R8-H0`; the unique prefix resolves to accepted exact plan target `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` |
| Authorization context | Instruction received with clean HEAD `f2ac627915ce9b1259b500d61d43b75f145e05d8`, the plan-acceptance-record commit; the accepted plan file matched the exact target byte-for-byte |
| Successor status | Non-privileged R8-H0 may proceed but is not accepted; R8-H1 through R8-H4, R9, and every later successor remain blocked |
| Publication status | Public push, tag, publication, release, clean-repository migration, and any `pathfinder/publication-gate.conf` change remain blocked |

The responsible human accepted exact commit
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` on 2026-08-07. This record
preserves that supplied decision. The responsible human then separately
authorized implementation under that accepted plan only far enough to proceed
with non-privileged R8-H0. This authorization does not accept H0 or authorize
privileged work.

## 2. Deliverables

The exact target changes 96 paths: 10 maintained paths and 86 generated
planning-site paths. It changes no file under `arch/`, `include/`, `virt/`,
`model/`, or `tests/r0/` through `tests/r7/`, and does not change the root
`Makefile`, `be`, `scripts/check-be.sh`, or a predecessor acceptance pin.

| Deliverable | Paths | Purpose and boundary | Primary review question |
| --- | --- | --- | --- |
| Bounded R8 plan | `planning/single-hart-runtime-r8-plan.md` | Defines the planning-only H0-H4 K3 program, fixed claim boundary, stop rules, hardware dispositions, core-design ledger, evidence requirements, and non-goals | Is the sequence narrow enough to inform the core design and validate one K3 profile without importing OS, multicore, device, or policy work? |
| Current-position records | `README.md`, `planning/{README,HANDOFF,implementation-plan,roadmap}.md`, `.github/copilot-instructions.md` | Records exact-plan acceptance and the later H0-only implementation authorization while H0 acceptance, privileged work, and hardware remain blocked or `NOT RUN` | Do all status surfaces distinguish plan acceptance, H0-only implementation authority, and H0 acceptance? |
| K3 hardware roadmap | `planning/riscv-security-hardware.md` | Places single-hart K3/core validation before OS support and preserves the complete feature inventory | Does the plan deliberately use, characterize, disable, defer, or stop on every relevant K3 feature? |
| Documentation integration | `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs` | Adds the R8 plan to navigation and to the shared planning-page browser inventory; the renderer change adds one planning entry only | Is the one shared-renderer exception acceptable without changing Helium pages, claims, commands, or component behavior? |
| Generated planning site | 86 paths under `docs/html/`, including `single-hart-runtime-r8-plan.html` and its generated assets | Reviewable derivative of Markdown; source remains authoritative | Does the rendered page preserve status, claim limits, tables, links, and direct-file readability despite the open byte-reproducibility finding? |

The complete exact inventory is:

```sh
git diff --name-status \
  742ce4450dc85fc632d2ca7ff1061de09f3cf171 \
  7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5
```

The maintained-source-only inventory is the same command with
`-- ':!docs/html'`.

## 3. Claim boundary

### What the exact target supports saying

The target supports only these planning facts:

- responsible-human direction on 2026-08-07 authorized R8 planning and
  selected combined single-hart K3 core validation before OS support;
- the proposed plan fixes one X100 core on one exact board, one active hart,
  the existing two role-neutral synthetic VS domains, immutable
  ownership/explicit-channel authority, Sv39x4, VMID zero, and no guest SBI;
- R8 is ordered as:
  - H0 exact non-privileged board/firmware/tool/profile freeze;
  - H1 characterization without VS entry;
  - H2 separately gated fixed synthetic runtime execution;
  - H3 canonical QEMU/K3 comparison and bounded negative evidence; and
  - H4 deterministic report, evidence bundle, and exact-target review;
- accepted R0-R7 runtime mechanism, proof, and evidence-input bytes are
  immutable under the plan;
- a required common-core change, accessible unmodeled optional state,
  second active hart, device/DMA path, widened exit surface, or relaxed
  expectation is a stop requiring a reviewed plan revision; and
- exact plan acceptance, separate implementation authorization, and exact H0
  acceptance are distinct gates before privileged work.

The first two gates are now satisfied. Exact H0 acceptance remains required
before R8-H1 or any later privileged work.

### Trusted or assumed

The plan remains conditional on future H0/H1 evidence for:

- the exact K3 board, X100 stepping, firmware, OpenSBI, bootloader, boot
  chain, and non-participating-hart parking;
- RVH, Sv39x4, VMID width, CSR/WARL, fault metadata, and local invalidation
  behavior;
- optional F/D/V and other architectural-state exclusion or inaccessibility;
- PMP/Smepmp/ePMP, secure-boot/lifecycle, debug/trace, AIA/Sstc,
  state-enable, counters, cache, IOMMU, IOPMP, external-master, and RAS state;
- open build, flashing, capture, reset, ELF, report, and evidence tools; and
- the correctness of firmware, compilers, linkers, hardware, capture host,
  canonicalizer, checkers, and lab procedure.

The plan exposes these assumptions; it does not resolve them.

### Evidence unavailable or `NOT RUN`

- R8-H0 profile freeze: authorized to proceed, but no exact candidate is
  delivered or accepted.
- R8-H1 characterization: not authorized or started.
- R8-H2 synthetic runtime: not authorized or started.
- R8-H3 QEMU/K3 comparison and negative cases: not authorized or started.
- R8-H4 report/evidence implementation: not authorized or started.
- K3 execution and hardware validation: `NOT RUN`.
- R8 host, image, QEMU, K3, report, evidence, and evaluator commands: do not
  exist.
- No new C refinement, binary correspondence, whole-image proof, or
  whole-system verification result exists.

### Explicitly not implemented or authorized

The target adds no:

- target C, assembly, linker, configuration, platform, guest, or test-runtime
  implementation;
- Linux or other OS, VMM, protected service, guest SBI, hypercall ABI, UAPI,
  parser, or stable manifest encoding;
- multicore execution, interrupt injection, guest timer, scheduler, device,
  DMA, IOMMU/IOPMP programming, or driver domain;
- capability, CHERI, TE, CAP+TE, policy service, measured launch,
  attestation, key sealing, or MVP behavior;
- R7 acceptance-status tooling or generated-asset reproducibility closure;
- hardware, certification, production, publication, or release claim; or
- R9 or later successor authority.

## 4. Security and correctness invariants

These are plan obligations, not implemented properties.

| Invariant | Contract location | Planned enforcement/evidence | Human review focus |
| --- | --- | --- | --- |
| Plan acceptance, implementation authority, and H0 acceptance are distinct | `Status and authority`; `Current state after this proposed plan` | Exact status text across maintained records; H0-only authorization recorded without changing the plan or adding implementation paths | Are the remaining H0 acceptance and privileged-work gates unambiguous? |
| Accepted predecessor mechanism stays immutable | `Predecessor and immutability boundary` | H0 exact path/mode/SHA-256 inventory; predecessor acceptance interfaces; stop on any common-core change | Is the immutable set complete, and is the planning-page renderer exception sufficiently narrow? |
| One active hart only | `Fixed R8 scope`; `R8-H1: Entry and hart state` | Exact firmware parking contract and retained H1-H3 observations | Can the plan honestly establish a single-hart experiment on an eight-core SoC without implying multicore support? |
| Optional state cannot leak across domains | `R8-H1: Optional state stop rule` | Absent/disabled, inaccessible through checked controls, or later complete save/reset/restore revision | Is stopping preferable to importing F/D/V or other state opportunistically? |
| Authority remains proposal -> canonical -> sealed -> derived | `Fixed R8 scope`; `Normalized platform input`; H2 execution sequence | Reuse of accepted R1/R2 mechanism and independent validation of the K3 profile | Does the offline DT/profile path preserve the accepted authority seam? |
| Every root switch remains write -> local fence -> readback -> publication | H2 execution sequence; hardware/core-design matrix | Exact transition evidence and real VS accesses; no deliberately unsafe skipped-fence image | Does the plan test enough without creating a hazardous hardware fixture? |
| External masters cannot be silently ignored | H1 cache/external-master section; hardware disposition matrix | Quiescence/default-deny evidence or an explicitly CPU-originated-only claim | Is the claim downgrade adequate if DMA exclusion cannot be established? |
| QEMU/K3 comparison does not equate physical encodings | H3 canonical comparison | Per-profile HGATP mode/VMID/root-PPN expectations and exact mandatory/permitted metadata rules | Are the comparison rules strict without requiring numerically identical platform addresses? |
| Failure never becomes a permissive fallback | H0/H1 exit gates; H2 core-design stop rule; acceptance gates | `UNKNOWN`, `NOT RUN`, `FAIL`, plan revision, or blocked status | Are all material unknowns and incompatibilities routed to a stop? |
| No claim exceeds one board and one lab profile | Supportable completion claim and required limit | H4 claim/non-claim ledger and exact-target human review | Is the planned claim useful yet properly bounded? |

## 5. Review history and resolved findings

### Resolved in the exact target

1. **R8 was undefined.** The accepted R0-R7 plan ended at R7. The
   responsible human selected combined K3/core validation rather than an
   inferred Linux successor.
2. **Evidence hygiene was considered but not selected as R8.** The plan
   records what acceptance-status and generated-asset reproducibility cleanup
   would buy, and why it does not answer the immediate core/hardware
   questions.
3. **OS ordering was corrected.** Single-hart K3/core validation now precedes
   Linux/protected-domain planning; multicore and devices remain later.
4. **The initial immutability wording was too broad.** The planning build
   requires one entry in `pathfinder/tests/check-docs-render.mjs`. The final
   target narrows immutability to accepted mechanism/proof/evidence inputs and
   explicitly permits only that planning-page inventory change; no Helium
   page or claim changes.
5. **Cross-platform HGATP comparison was over-broad.** The final plan compares
   each profile's independently expected mode, VMID, and root PPN rather than
   requiring equal numeric HGATP values across different physical layouts.
6. **The QEMU comparison source was ambiguous.** H0 must choose either the
   accepted R5 canonical record or an enumerated additive R8 QEMU profile;
   “if required” cannot become a run-time choice.
7. **Machine-state observations may be inaccessible to HS.** The final plan
   requires exact retained H1 M-mode firmware instrumentation where needed and
   requires H1 to be repeated if H2 firmware bytes change.
8. **Instruction visibility was implicit.** The H1 cache boundary now
   includes firmware-to-HS instruction visibility and any required `FENCE.I`
   or platform cache operation.

### Open questions for responsible-human judgment

- Is H0-H4 the right review granularity, or is the sequence over-gated?
- Is byte-immutable reuse of accepted common-core inputs the right initial K3
  test, with every required common-core change forcing a revision?
- Is OpenSBI below HS acceptable as a first K3 lab assumption?
- Is “exclude/inhibit optional state or stop” the right first-hardware rule?
- Is a CPU-originated-only claim useful if external-master quiescence cannot
  be established?
- Is the no-skipped-fence-hardware-fixture rule appropriately conservative?
- Are three cold boots per compiler an adequate minimum?
- Are the 512 MiB evidence cap and proposed exact-report boundary sufficient?

### Open generated-asset finding

The exact target's documentation functions correctly but is not byte-clean
under a rebuild. In a fresh detached worktree at the exact target,
`npm ci && ./be docs-check` passed all link, browser, direct-file, planning,
and Helium documentation gates, then left changes only under `docs/html/`,
including regenerated hash-named application/search/theme assets. This is the
already-recorded generated-asset byte-reproducibility finding. The exact plan
does not claim to close it.

### Recorded after the exact target

The plan was accepted in the current branch by acceptance-record commit
`f2ac627915ce9b1259b500d61d43b75f145e05d8`. With that commit at clean
`HEAD`, the responsible human then supplied the exact instruction
`Authorize R8 implementation under accepted plan 7d0f0cbf…; proceed with
R8-H0`. The unique prefix resolves to
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`.

This is a separate implementation authorization under the accepted plan. It
permits only the non-privileged H0 profile-freeze work and changes no plan,
runtime, proof, test, root-wrapper, or acceptance-pin byte.

## 6. Validation and retained evidence

All dates below are 2026-08-07 UTC.

| Command or check | Execution boundary | Result and coverage |
| --- | --- | --- |
| `./be docs-check` | Final pre-commit content that became the exact target | PASS: 62 planning Markdown sources, 63 generated HTML pages, no broken local targets, 62 planning pages rendered in Chromium; 12 Helium sources and pages also passed |
| `make check` | Final pre-commit content that became the exact target | PASS: complete existing repository gate, including wrapper/source policy, Model, R0-R7, Helium, proof/test/QEMU, evidence, and documentation checks; no R8 hardware or implementation stage exists |
| `git diff --check 742ce445… 7d0f0cbf…` | Exact immutable target | PASS |
| `git fsck --no-dangling 7d0f0cbf…` | Exact immutable target | PASS |
| Exact inventory checks | Exact immutable target | PASS: 96 changed paths, 86 generated planning-site paths, 10 maintained paths, 0 forbidden runtime paths |
| `npm ci && ./be docs-check` | Fresh detached worktree at exact target `7d0f0cbf…` | PASS functional gates; post-check dirty state confined to `docs/html/`, reproducing the open generated-asset finding |
| HEAD, clean-tree, and plan-identity precheck | Before authorization-record edits | PASS: clean `HEAD` was `f2ac627915ce9b1259b500d61d43b75f145e05d8`; prefix `7d0f0cbf` resolved uniquely; the working plan and exact accepted target had identical Git blob hashes |
| `./be docs-check` | Final pre-commit authorization-record content | PASS: 63 planning Markdown sources, 64 generated HTML pages, no broken local targets, and 63 planning pages rendered in Chromium; 12 Helium sources and 13 pages also passed |
| `git diff --check` plus changed-path and frozen-plan checks | Final pre-commit authorization-record content | PASS: exactly 8 maintained documentation paths changed and every other changed path is generated planning-site content; no runtime, proof, test, root-wrapper, or acceptance-pin path changed; the accepted R8 plan remained byte-identical |

The pre-commit `make check` and `./be docs-check` ran against bytes identical
to the committed target, but not after the commit object existed. The separate
detached-worktree documentation run names and executes the exact commit.
There is no exact-target R8 runtime report, proof, hardware trace, or evidence
bundle because the target is a plan only.

The final three rows validate this later authorization record, not the
accepted plan target and not any H0 implementation.

Retained review evidence is:

- exact Git target and parent;
- exact 96-path Git inventory and diff;
- authoritative Markdown plan;
- generated R8 HTML page and navigation;
- complete command outputs in the originating private session; and
- this packet, which is decision support and not part of the plan target.

## 7. Recommended human review sequence

Create an isolated detached worktree:

```sh
git worktree add --detach \
  ../beryllium-r8-plan-review \
  7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5
cd ../beryllium-r8-plan-review
git status --short
git show --no-patch --format=fuller \
  7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5
git diff --check \
  742ce4450dc85fc632d2ca7ff1061de09f3cf171 \
  7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5
```

1. Read the R7 acceptance boundary in
   `planning/single-hart-runtime-r7-review-summary.md`, then the R8 plan's
   `Status and authority`, `Selected ordering`, and supportable claim. Confirm
   that the user instruction has been interpreted as planning authority only.
2. Review `Fixed R8 scope`, the predecessor immutability boundary, and the
   H0-H4 graph. Ask whether each package has one useful result and a
   sufficiently explicit stop condition.
3. Review H0 and H1 before H2. Focus on exact firmware identity,
   non-participating harts, optional state, PMP/Smepmp, AIA/Sstc, cache and
   instruction visibility, debug, and external masters.
4. Review H2 and H3 against the accepted R5 scenario. Confirm that no OS,
   guest SBI, second hart, device, DMA, policy, or relaxed fault/fence
   expectation enters through the hardware port.
5. Review the hardware disposition matrix and core-design question ledger.
   Decide whether they expose the intended design questions without
   prejudging a production architecture.
6. Inspect the exact maintained-source diff and the planning-only boundary:

   ```sh
   git diff --name-status \
     742ce4450dc85fc632d2ca7ff1061de09f3cf171 \
     7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5 \
     -- ':!docs/html'
   git diff \
     742ce4450dc85fc632d2ca7ff1061de09f3cf171 \
     7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5 \
     -- planning/single-hart-runtime-r8-plan.md
   ```

7. Review current-position wording in `planning/roadmap.md`, `README.md`,
   `planning/README.md`, and `planning/HANDOFF.md`. Confirm that every surface
   binds plan acceptance to the exact target while keeping implementation
   unauthorized and hardware `NOT RUN`.
8. Optionally reproduce the documentation gate:

   ```sh
   npm ci
   ./be docs-check
   ```

   Expect functional PASS and generated `docs/html/` dirtying. That dirtying
   is an open reproducibility finding, not a source failure and not a claim
   that the committed generated bytes reproduce exactly.

Remove the review worktree only after recording the decision:

```sh
cd -
git worktree remove --force ../beryllium-r8-plan-review
```

## 8. Human decision checklist

- [ ] The instruction `r7 reviewed, proceed to r8` is correctly interpreted as
      authority to prepare the previously undefined R8 plan, not as acceptance
      of this exact plan or authority to implement it.
- [ ] Core correctness and single-hart K3 validation properly precede Linux
      and other OS support.
- [ ] The fixed one-board, one-active-hart, two-synthetic-domain scope is
      sufficiently narrow and useful.
- [ ] The H0-H4 package graph and separate decision gates are proportionate.
- [ ] Accepted R0-R7 mechanism/proof/evidence-input immutability and the
      stop-on-core-change rule are acceptable.
- [ ] The optional-state, parked-hart, PMP/Smepmp, interrupt/timer,
      cache/instruction-visibility, debug, and external-master dispositions
      are sufficiently complete.
- [ ] The planned QEMU/K3 comparison distinguishes architectural semantics
      from platform-specific physical encodings.
- [ ] The negative paths are sufficient without deliberately executing a
      skipped-fence or partially published image on hardware.
- [ ] The supportable completion claim and required limit match the planned
      evidence and do not imply formal verification, arbitrary-guest
      isolation, or production hardware support.
- [ ] The open generated-asset byte-reproducibility finding is acceptable as
      a recorded unresolved limitation for this planning commit.
- [ ] Linux, guest SBI, services, multicore, devices, DMA, policy,
      publication, and every later successor remain excluded.
- [x] **Accept** exact plan commit
      `7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`.
- [x] **Authorize implementation only for non-privileged R8-H0** under that
      accepted exact plan.
- [ ] **Accept** an exact R8-H0 freeze before any privileged R8-H1 or later
      work.
- [ ] **Request revisions** through a new commit and new review packet.
- [ ] **Defer** the decision while preserving all current gates.

Only the supplied plan-acceptance and H0-only implementation-authorization
boxes are checked. The technical-judgment and H0-acceptance boxes remain
unchecked; automation does not settle them. No signature is generated.

## 9. Recorded decisions and remaining boundaries

The responsible human accepted exact commit
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` on 2026-08-07 by the explicit
instruction `accept exact 7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`.
Acceptance covers the plan text only.

The responsible human separately supplied the exact instruction
`Authorize R8 implementation under accepted plan 7d0f0cbf…; proceed with
R8-H0`. The unique prefix resolves to accepted exact plan target
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5`. This second decision authorizes
R8 implementation only for the plan's non-privileged H0 profile freeze.

The plan acceptance and H0-only implementation authorization do not:

- accept this review/acceptance-record commit as plan content;
- accept an H0 candidate or result;
- authorize privileged R8-H1 through R8-H4 work;
- authorize K3 execution or any K3 result;
- authorize root integration or predecessor acceptance-pin refresh;
- accept or create any hardware, runtime, proof, C-refinement, Linux or other
  OS, multicore, device, DMA, policy, or production result;
- authorize push, tag, publication, or release;
- resolve the generated-asset byte-reproducibility finding; or
- authorize R9 or any later successor.

The plan target's own `r8_plan=proposed-not-reviewed`,
`r8_implementation=not-authorized`, and `r8_hardware_execution=NOT-RUN` text
is frozen pre-decision and pre-authorization plan content. This review,
acceptance, and authorization record, not a rewrite of the immutable target,
carries the current decisions.

Historical alternatives remain:

- a requested revision would require a new plan commit and review packet; and
- deferral would have preserved the proposed-not-reviewed state.

Neither alternative was selected.

**Status.** Exact planning commit
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` is responsible-human accepted as
of 2026-08-07. R8 implementation is separately authorized only for
non-privileged H0. H0 is not accepted, privileged H1-H4 work remains blocked,
and K3 execution is `NOT RUN`.

**Next.** Proceed only with the non-privileged R8-H0 profile freeze under the
accepted plan. Present its exact candidate for responsible-human review before
any R8-H1 or later privileged work.

**Action required from you.** None for this authorization record. A later
explicit decision must accept an exact H0 candidate before privileged work.
