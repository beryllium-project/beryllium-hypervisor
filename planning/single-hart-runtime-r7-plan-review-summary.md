<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R7 plan review and acceptance record

## 1. Decision summary

| Field | Record |
| --- | --- |
| Review target | Exact plan commit `18c43596d308052cfad67edc6e2cb8f543f75600`; parent `2cc6e96413ab4d426bbf2327dc6c9b309b3f3aac` |
| Current status | Bounded R7 plan complete and documentation-checked; no R7 proof implementation or result |
| Decision | Responsible-human acceptance of exact commit `18c43596d308052cfad67edc6e2cb8f543f75600` on 2026-08-05 |
| Successor status | R7 implementation may proceed under the prior instruction to commence R7; implementation remains not started; R8 is not authorized |
| Publication status | Private internal repository only; public push, tag, publication, and release remain blocked |

The responsible human first requested acceptance of the uncommitted file
`planning/single-hart-runtime-r7-plan.md`. Automation did not infer an
immutable target from that request. It committed the unchanged reviewed plan
content, reported the resulting exact commit and parent, and asked for an
exact decision. The responsible human then selected:

```text
Accept exact 18c43596d308052cfad67edc6e2cb8f543f75600
```

This record names that exact plan commit only. It does not accept a future R7
implementation commit.

## 2. Deliverables

| Deliverable | Paths | Purpose and boundary | Primary review question |
| --- | --- | --- | --- |
| Bounded R7 plan | `planning/single-hart-runtime-r7-plan.md` | Defines exact linked-byte, bounded RV64/Rocq, fixed-configuration, claim-ledger, evaluator, report, and reproducibility scope; adds no runtime implementation | Are the symbols, proof obligations, cut points, and non-goals narrow enough for the fixed profile? |
| Current-position records | `README.md`, `planning/{README,HANDOFF,implementation-plan,roadmap}.md`, `.github/copilot-instructions.md` | Records accepted R6, authorized R7 planning, and the pre-decision plan gate without transferring proof claims | Do all maintained records preserve the implementation and publication gates? |
| Documentation integration | `planning/.vitepress/config.mts`, `pathfinder/tests/check-docs-render.mjs`, generated `docs/html/` | Makes the plan navigable and checks direct-file browser rendering | Does generated output correspond to the Markdown source without changing Helium claims? |

The exact changed-path inventory is the output of:

```sh
git diff-tree --no-commit-id --name-status -r \
  18c43596d308052cfad67edc6e2cb8f543f75600
```

It contains 86 paths: the new plan, seven maintained source/navigation/check
paths, current-position records, and the generated planning-site pages and
content-hashed assets. No file under `include/`, `virt/`, `arch/`, `tests/r7/`,
`pathfinder/publication-gate.conf`, or the Helium documentation source changed.

## 3. Claim boundary

The accepted plan supports saying only that:

- R7 is authorized and its exact bounded plan is accepted;
- future R7 implementation is confined to `tests/r7/` plus enumerated root
  integration and maintained documentation;
- exact-byte proof scope is limited to the named R3/R5 wrapper symbols in the
  two pinned R5 images;
- the fixed configuration trace is finite and does not prove the R1/R2 C
  implementation or transfer Model 0.2 results; and
- every proof, report, evaluator, and evidence result remains `NOT RUN`.

Trusted or assumed boundaries remain the bounded local ISA semantics, ELF
parser and independent objdump cross-check, Rocq kernel and host, C cut
points, surrounding compiler/linker output, OpenSBI, QEMU, and the fixed
single-hart/no-device/no-DMA profile.

Unavailable evidence remains hardware validation, whole-C refinement,
source-to-binary validation, complete RISC-V H semantics, arbitrary-guest
isolation, and public-release approval.

The accepted plan does not implement Linux, guest SBI, services, devices,
interrupts, multicore, CHERI, Type Enforcement, attestation, an MVP, R8, or a
new pathfinder. It does not support saying that Beryllium is formally
verified.

## 4. Security and correctness invariants

| Invariant | Contract | Future implementation/evidence boundary |
| --- | --- | --- |
| Accepted runtime immutability | Plan package and acceptance gates | No accepted `include/`, `virt/`, or `arch/` byte may change |
| Exact-byte identity | Exact linked-byte scope and `Exact.v` obligations | Direct ELF extraction must agree word-for-word with locked GNU objdump |
| Bounded semantics | `ISA.v`, `Entry.v`, `Trap.v`, `Switch.v` obligations | Unsupported words and out-of-scope control flow must fail |
| Explicit cut points | Tool/trust boundary and claim ledger | C, parser, compiler, linker, firmware, QEMU, and hardware assumptions remain visible |
| No proof-shaped fallback | Claim-ledger rule | Missing or failed proof reports `NOT-RUN` or `FAIL`, never success |
| Successor/publication exclusion | Explicit non-goals and current state | R8 and public publication remain blocked |

## 5. Review history and resolved findings

The plan adapted the retained Helium exact-proof method only as a methodology.
It explicitly rejected theorem, byte, generated-input, proof-object, and claim
transfer. The plan also narrowed the proposed proof from a whole runtime or
isolation claim to enumerated assembly symbols and a finite configuration
trace with explicit C and tooling cut points.

The only acceptance-process finding was that the initial instruction named a
working-tree file rather than an immutable commit. That was resolved by
creating exact commit `18c43596d308052cfad67edc6e2cb8f543f75600` without
changing the reviewed plan content and obtaining a second explicit decision
that named the resulting SHA. No open plan finding is being hidden by this
record.

## 6. Validation and retained evidence

The following passed on 2026-08-05:

```sh
npm run docs:build
./be docs-check
```

The first execution checked equivalent pre-commit content. After commit
`18c43596d308052cfad67edc6e2cb8f543f75600` was created, `./be docs-check`
passed again from its clean exact worktree, covering 57 planning Markdown
sources, 58 planning HTML pages, browser rendering, links, generated diagrams,
and the separately labeled Helium documentation gate.

No R7 tool, extraction, proof, report, evaluator, evidence, QEMU, or hardware
command exists or ran. Those results remain `NOT RUN`.

## 7. Recommended human review sequence

The completed review can be reproduced read-only with:

```sh
git show --stat --oneline 18c43596d308052cfad67edc6e2cb8f543f75600
git diff 2cc6e96413ab4d426bbf2327dc6c9b309b3f3aac..18c43596d308052cfad67edc6e2cb8f543f75600 \
  -- planning/single-hart-runtime-r7-plan.md
git diff --name-status \
  2cc6e96413ab4d426bbf2327dc6c9b309b3f3aac..18c43596d308052cfad67edc6e2cb8f543f75600
```

For isolated execution:

```sh
git worktree add --detach /tmp/be-r7-plan-review \
  18c43596d308052cfad67edc6e2cb8f543f75600
cd /tmp/be-r7-plan-review
npm ci
./be docs-check
```

Review the plan in this order: supportable claim and non-claims; exact symbol
scope; proof obligations and cut points; package/root-integration boundary;
acceptance gates; retained evidence; successor and publication exclusions.

## 8. Human decision checklist

The responsible human considered the exact target and recorded acceptance.
This preserved checklist is not a signature and is not completed by
automation:

- [ ] Scope matches the authorized R7 master-plan row.
- [ ] Proposed claims match the future evidence gates.
- [ ] Trust assumptions and cut points are acceptable.
- [ ] Planned rejection tests cover important negative paths.
- [ ] Runtime changes, R8, and publication remain excluded.
- [ ] Accept exact commit, request revisions, or defer.

## 9. After the decision

- **Accepted:** this follow-up records acceptance of exact plan commit
  `18c43596d308052cfad67edc6e2cb8f543f75600` and date 2026-08-05. R7
  implementation may now proceed strictly under that plan and the prior
  authorization to commence R7. A future implementation requires its own
  exact-commit review and explicit acceptance.
- **Revisions later requested:** create a new plan commit and new review
  packet. Do not silently extend this acceptance to changed content.
- **Implementation deferred:** preserve accepted-plan status with proof,
  QEMU, and hardware results `NOT RUN`.

**Status:** Exact R7 plan accepted; R7 implementation not started.

**Next:** Implement only the accepted bounded R7 package and prepare a separate
exact-implementation evidence and review record.

**Action required from you:** None for plan acceptance; the exact decision is
recorded above.
