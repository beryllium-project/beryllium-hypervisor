<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M6 plan: the MVP core profile, release candidate 3

## Decision record

The responsible human accepted this plan at exact commit
`b2c62d54f21c3cabdad3fefcc562499ace601089` (parent `f8b77ac9`, Plan
revision S3-B's commit, on branch `beryllium/mvp-m6-plan` from
`cd9cfa5f`) on 2026-10-30, the second of the two ordered decisions the
[review and acceptance record](mvp-m6-plan-review-summary.md) presented,
and separately authorized M6 implementation. The instruction `accept
f8b77ac9 and f8b77ac9` named decision 1's commit twice; the second
decision was confirmed by the form answer `accept-and-authorize` (accept
`b2c62d54` as the M6 plan and authorize M6-2 to M6-8, Q1 to Q11 at
their defaults). The same instruction accepted
[Plan revision S3-B](mvp-plan.md#plan-revision-s3-b-release-candidate-3-and-milestone-m6-the-mvp-core-profile)
at `f8b77ac9`, the ordered decision this plan depends on.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted; only this
  section and the status block's trailing lines were set afterwards.
- **Authorization:** M6-2 to M6-8 on branch `beryllium/mvp-m6` from the
  acceptance-record commit, coding on `claude-opus-5.5` under the
  session's orchestrating model, with Q1 to Q11 at their defaults, under
  the stop conditions; board commands only after the human confirms the
  board free, the human present at the install and the restore; no push,
  merge, tag, publication, release, or kexec use. The result is release
  candidate 3, presented in one packet.
- **The result (2026-10-31):** the M6 result, exact commit
  `89ef04e9354c08ebadbaeb88d553c5081a00b84d` (`RC3`, over the candidate
  tree `X3` `ebc49a88`), is responsible-human accepted as MVP 1.0
  release candidate 3 by the instruction `accept 89ef04e9, proceed`; the
  [M6 result review and acceptance record](mvp-m6-result-review-summary.md)
  carries the decision and the thirteen plan-letter departures (the
  model instance deferred under Q4 among them), and the
  [M6 evidence record](mvp-m6-evidence.md) the evidence. Only the
  status block's trailing lines below were added afterwards; the plan
  text is as accepted.

## Status

```text
m6_status=proposed-not-reviewed
m6_direction=we-will-go-with-RC3-first;2026-10-30
m6_plan_target=b2c62d54f21c3cabdad3fefcc562499ace601089
m6_plan_parent=f8b77ac94fc6b5a80e68e6a972fa353b800d068b
m6_acceptance_instruction=accept-f8b77ac9-and-f8b77ac9;decision-2-confirmed-by-form-accept-and-authorize
m6_acceptance_date=2026-10-30
m6_acceptance_record=mvp-m6-plan-review-summary.md
m6_open_questions=Q1-Q11-defaults
m6_authorization=M6-2..M6-8-on-beryllium/mvp-m6-from-acceptance-record;2026-10-30;board-after-human-confirmation
m6_base=cd9cfa5f
m6_plan_branch=beryllium/mvp-m6-plan
m6_work_packages=M6-1..M6-8
m6_release_candidate=rc3
m6_soft_limit_lines=4000
m6_board_runs=20
m6_result=accepted-89ef04e9354c08ebadbaeb88d553c5081a00b84d;parent-X3-ebc49a889273c811836c3d39fb0fc9bfe808be4c;2026-10-31;instruction-accept-89ef04e9-proceed;record-mvp-m6-result-review-summary.md;evidence-mvp-m6-evidence.md
m6_departures=13
m6_stops_fired=none
m6_model_instance=deferred-Q4-default;U-13;Model.v-closed-frame-gpa
m6_code_lines=3258-of-4000
m6_board_campaign=20-of-20-2026-10-31-X3-images;restore-record3-equals-record1
m6_release_path=step-1-holds-for-rc3;steps-2-7-not-started-each-needs-instruction
```

## Purpose

Retire the "MVP core profile" debt (M0 Plan revision M0-A.5; S3-B.1):
make the monitor validate, seal, and derive the MVP's real configuration
through the accepted R1 mechanism in place of the frozen single-hart
fixed profile, drop the fixture roots, pages, and prelude steps the MVP
builds and never uses, gather the privileged effects behind one executor
with the proof-bearing subset named (S1 H22), and present the result as
MVP 1.0 release candidate 3 with the same evidence M4 and M5 made: the
gates from a clean checkout, a board campaign from system reset, the
records, the ledger, the evidence record, and a packet. The MVP's claim
does not change; what changes is that the claim's "checked offline
against the sealed configuration, and enforced through derived mappings"
now rests on a sealed configuration that is the MVP's own, validated by
the ported accepted mechanism at boot, rather than on the MVP's `ASSERT`s
beside an unused synthetic core.

## Inputs

| Input | Exact commit | Role |
| --- | --- | --- |
| MVP plan with Plan revision S3-A | `93967fba`, `0d134bbc` | the milestones, D1 to D17, the release path, the board policy, the standing rule |
| Plan revision S3-B | the commit presented with this plan | M6, release candidate 3, D18 |
| M0 plan with Plan revisions M0-A to M0-C | `4d129808`; `30c5e1a8`, `77559def`, `260ceba6` | the layout, the hart region, the MVP region, the budgets, M0-A.5's debt record |
| M1 and M2 plans | `7b2c055c`, `854a5415` | the channel, the denial path, the pages, the management extension, the measurement |
| M3 plan and result | `c2c249f4`, `b0a0f352` | the policy layer in the model; the differential harness; the generated instances |
| M5 plan and release candidate 2 | `0066794d`, `3867c66c` | the board policy as run, the tools, the records' shape, the campaign's run plan |
| Debt sweep 1 | `80ef8a13` | the board tools as they stand |
| Project snapshot | `2c80835c` (and its Frama-C/WP note `cd9cfa5f`) | the verification route whose stage 0 this plan folds in |
| S1 synthesis | `fd670dcd` | H22 (the seams), H59 (policy as specification) |
| Security model v1 | `0e3eec8b` | the notation, the instances, A1 to A8, the policy-to-manifest relation |
| Accepted R1, R2, R3 | `a6e0bb17`, `6e1cb579`, `6fb65b28` | the mechanism the MVP ports: `virt/be/manifest.c`, `state.c`, `r1-config.c`, `r3.c`, `arch/riscv/be/sv39x4.c`, the platform and entry code |

## Facts the design rests on (read-only findings, 2026-10-30)

- **The prelude today.** Hart 0 runs the accepted R3 prelude unchanged
  through `BE_R3:06`: the boot check (`BE_R3:01`), R1's copy, validate,
  seal, and derive of the **fixed thirteen-resource profile** (`:02`;
  `virt/be/r1-config.c` through the port), R2's build and re-walk of the
  two **fixture roots** in the accepted root pools (`:03`), the HS/VS
  state check and the management binding (`:04`, `:05`), and the
  publication of the management root's `hgatp` on hart 0 (`:06`). Only
  then do the MVP steps begin (`BE_MVP:01` onward). Hart 0 runs no guest:
  `:04` to `:06` prepare a VS entry that never happens, and the fixture
  roots map fixture pages no domain uses.
- **The fixture extents.** The first `0x34000` bytes of the flat image are
  the accepted B2 layout: the accepted code (below `0x1_0200_8000`) and
  data, then NOLOAD: the management and protected root pools (2 × `0x8000`
  at `0x102014000` and `0x10201c000`), the management and protected
  stacks (2 × `0x2000`), saved pages (2 × `0x1000`), private pages (2 ×
  `0x1000`), the shared page (`0x1000`), and the accepted fixture guest
  code (`arch/riscv/be/r5-guest.S`). Of these the MVP uses the management
  stack (hart 0's) and nothing else. The MVP-owned extents follow: the
  pool at `0x102034000` (two B6-shaped 32 KiB pools), the hart region at
  `0x102044000` (`0x20000`), the MVP region at `0x102064000` (`0x40000`),
  which ends the `0xa4000`-byte image (`mvp/src/mvp-layout.h`).
- **The accepted limits.** `include/be/manifest.h`: `BE_MAX_DOMAINS 2`,
  `BE_MAX_RESOURCES 13`, `BE_MAX_AUTHORITIES 6`, `BE_MAX_ROOTS 2`,
  `BE_MAX_MAPPINGS 6`; the inventory names a sole active hart. The MVP's
  configuration has three harts, two domains, between twelve and sixteen
  resources depending on the scenario (code, data, the pool, two hart
  blocks, the MVP region, the staging area, two windows, one to three
  shared pages, the secret page), and per domain one private window plus
  up to three shared-page grants: it does not fit the accepted bounds.
- **The accepted R2 backend maps 4 KiB frames only**
  (`arch/riscv/be/sv39x4.c` requires `frame->size == BE_PAGE_SIZE`). The
  MVP's windows are 64 MiB mapped as 32 leaves of 2 MiB by the MVP's own
  builder, `mvp/src/mvp-gstage.c` (ported from B7), which also places the
  level-0 pages for the shared pages and re-walks the result.
- **The configuration's origin.** `mvp/tools/gen-scenario.py` turns a
  scenario (`scenarios/<s>/scenario.json`, `policy.te`) into the sealed
  scenario record the monitor links (the bindings, the windows, the
  channel or pages with their derived rights, the measured inputs), after
  `tools/policy-check.py` passes A1 to A8 and writes the authority report.
  The monitor re-walks what it built against that record. The accepted R1
  mechanism's inventory and proposal structures are not involved.
- **The model.** `model/` holds Model 0.2's inventory, proposal, canonical,
  and derived structures in Rocq and in C, the policy layer M3 added, the
  three policy instances (`Instances.v`, generated), and the differential
  harness over the Rocq oracle, the model's C checker, and the MVP's
  checker (91 mutations). The Rocq proofs about validation, sealing, and
  derivation are over the abstract model's bounds, not the C's constants.
- **What the ports are.** `mvp/tools/port.py` derives the MVP port from
  B2's port (the accepted R0 to R5 sources with the K3 address
  substitutions) by counted rules; the MVP compiles the ported
  `virt/be/manifest.c`, `state.c`, `r1-config.c`, `r3.c`,
  `arch/riscv/be/sv39x4.c`, `platform.c`, `freestanding.c`,
  `privileged.S`, `r5-guest.S`, and `r5-entry.S`. Accepted bytes under
  `include/`, `virt/`, and `arch/` are never edited; a port rule changes
  the copy, counted.
- **Sizes.** The monitor is about 7,300 lines of C and 1,200 of assembly
  under `mvp/src/` and `mvp/shim/`; `mvp-runtime.c` 2,203, `mvp-sbi.c`
  1,269, `mvp-gstage.c` 1,047, `mvp-hart.c` 915, `mvp-trap.S` 672.
- **What depends on the markers and the layout.** The capture checker's
  `direct`, `uboot`, and (test-only) `kexec` modes expect `BE_R3:01` to
  `:06` before `BE_MVP:01`; the image checker requires the accepted
  `0x34000` span, the accepted code extent, and the MVP region's budgets;
  the scenario expectations (v1 to v3) name the lines; the platform
  record and the preflight name the MVP extents; the fixtures under
  `mvp/tests/fixtures/` are real captures; the shim's `bytes=0xa4000`
  and the staging's image size are the image's.
- **Board facts that bound the layout.** The MVP extents
  `0x102000000`-`0x1020a4000`, the staging area at `0x108000000`, the
  windows at `0x110000000` and `0x114000000`, and the shared pages at
  `0x118000000` are free of Fedora's and U-Boot's use (every preflight,
  the M5-6a characterization's `/reserved-memory` check). U-Boot's
  `booti` places the image at `0x108000000` and the shim copies it to
  `0x102000000`.

## Design

### D-1 The MVP core profile replaces the fixed profile

A generated, per-scenario **inventory and proposal** in the accepted R1
structures, widened by port rules (the MVP's copy of `manifest.h`):

- `BE_MAX_HARTS` (new) 3 named harts: the control hart and the two domain
  harts, with the platform's hart count; the sole-active-hart field
  becomes the control hart, and the domain harts are the bindings
  (M3's H0 to H3 in the model already state the binding's properties);
- `BE_MAX_RESOURCES` 24, `BE_MAX_AUTHORITIES` 12, `BE_MAX_MAPPINGS` 8,
  `BE_MAX_ROOTS` and `BE_MAX_DOMAINS` 2 (Q1);
- resource kinds as accepted (monitor code, monitor data, root table,
  trusted stack, saved state, assignable, guest code), a window being a
  guest-code resource whose extent is 64 MiB (the structures allow any
  page-multiple size); the hart region's stacks, saved pages, state pages,
  and rings are trusted-stack, saved-state, and monitor-data resources;
  the MVP region is monitor code and data; the staging area is a
  monitor-data resource the monitor owns and no domain maps.

`gen-scenario.py` emits `build/mvp/gen/<s>/mvp-config.c`, the inventory
and proposal as constants, from the scenario and the authority report:
every grant in the report becomes an authority; every object an
resource; the result must be exactly what `policy-check.py` validated
(the generator asserts the report's grants and the proposal's authorities
agree, and the ledger's policy-to-manifest relation now has a concrete
manifest in R1's sense). The monitor's boot copies the inventory and the
proposal, validates, seals, and derives through the ported `manifest.c`
and `state.c` (R1's `be_runtime_*`), exactly as the prelude does today
for the fixed profile; a failure fails closed before any hart starts.

### D-2 Derived mappings drive the MVP's builder

The derived roots (R1's abstract roots: per domain, the mappings with
their rights) are the single input of `mvp-gstage.c`, which keeps its
2 MiB-leaf windows and 4 KiB shared pages and its re-walk, now checked
against the **derived** mappings rather than the generated scenario
record's leaves. The accepted R2 backend and the two fixture root pools
are dropped from the MVP (R2 stays accepted and untouched under
`arch/riscv/be/`; the MVP never used its roots). `BE_MVP:03
GSTAGE_BUILT_REWALKED` and `CHANNEL_CHECKED` keep their lines, with the
leaves' rights now traceable to a derived mapping, and the authority
report's `derived.flags` to the same.

### D-3 The prelude becomes the MVP's boot

Hart 0's boot: the accepted boot check (hart 0, the image layout, the SBI
identity) kept through the ported `r3.c` as `BE_MVP:00 BOOT_VALIDATED`
(Q2 names the final markers); then `BE_MVP:00 CONFIG_SEALED
inventory=<n> authorities=<n> roots=2 harts=0,1,2 identity=<sha256
prefix>` (the sealed configuration's identity, computed as M2's
configuration identity is, over the inventory and the proposal); then
the MVP steps as today from `BE_MVP:01`. The HS/VS state check, the
binding, and the control hart's `hgatp` publication (`BE_R3:04` to `:06`)
go: hart 0 publishes no `hgatp`, and each domain hart's `HART_READY`
line remains the record of the roots that are armed. The accepted
fixture guest code and the fixture pages go with them; the management
stack becomes hart 0's trusted stack by name.

### D-4 The layout

The MVP-owned extents do not move: the pool at `0x102034000`, the hart
region at `0x102044000`, the MVP region at `0x102064000`, the image
`0xa4000` bytes, the staging area, the windows, and the shared pages as
today, so the preflight's region list, the platform record, the shim, the
staging, and the board tools are unchanged in what they check. The first
`0x34000` bytes are laid out by an MVP-owned linker script derived from
the ported `r5-beryllium.lds` by a counted rule: the code extent below
`0x102008000` (the accepted budget becomes the MVP's), the data, hart 0's
stack, and the rest unused and zero; no fixture section. The image
checker's accepted-span identity rule is replaced by the new layout's
rules (the code and data extents, no section outside its extent, the
unused span zero, the budgets). `BE_MVP_ACCEPTED_IMAGE_BYTES` goes.

### D-5 The seams (S1 H22; the snapshot's stage 0)

Within the budget: every privileged effect the MVP's C performs (CSR
writes including `hgatp` and the delegation registers, `hfence`, SBI
calls including HSM `hart_start` and the IPIs, the console write) moves
behind one `mvp/src/mvp-executor.c` with one function per effect, called
from the decision code and nowhere else; the trap assembly is unchanged.
`mvp/README.md` gains a table naming each C function's layer
(proof-bearing decision, support, executor, platform/assembly) and the
proof-bearing subset's line count. No contract is written yet; that is
the first verification plan's. Behavior is unchanged, which the host
tests, the capture checker, and the QEMU suite show.

### D-6 The model (additive only)

If the generated instances' shape admits it within the budget, the MVP
core profile's inventory and proposal become an instance of Model 0.2 in
`Instances.v` (generated by the same tooling as M3's) and a case of the
differential harness, so that the model's validation, sealing, and
derivation are checked against the MVP's own configuration beside the
policy analyses. Additive: no proved theorem changes; if one would have
to, stop condition 4. If the shape does not admit it, the plan records
why and defers it to the first verification plan (Q4).

### D-7 What does not change

The claim's text and the required limit; the guests, their kernel,
configuration, and init; the scenarios' policies and labelings; the
denial path, the rings, the IPIs, the barrier, the management extension,
the measurement's inputs (its value changes with the image, as it does at
every commit); the board tools, the boot path, and the board policy; the
QEMU-only image rule (header bytes only); the hart assignment; the SBI
subset. The `KEXEC_*` constants and the scenarios' `kexec_fdt` object,
which M5 kept to preserve the configuration identities, are removed now
that the identities change anyway (Q3; open item 59 closes).

## Work packages

| WP | Delivers | Exit |
| --- | --- | --- |
| M6-1 | Plan revision S3-B; this plan; the review packet | both accepted (ordered) |
| M6-2 | The core profile: the widened manifest by port rules; `gen-scenario.py`'s `mvp-config.c`; the boot's copy, validate, seal, derive, and `CONFIG_SEALED`; `mvp-gstage.c` from the derived mappings; the fixture roots, pages, guest code, and `BE_R3:04` to `:06` removed; the MVP linker script and layout; the image checker's rules; the capture checker's markers and regenerated fixtures; the expectations; host tests for the widened validator on the MVP profile with GCC and Clang output identical; `./mvp/mvp check` | `check` PASS on both toolchains; the line count reported |
| M6-3 | The seams: `mvp-executor.c`; the layer table; the subset's count | `check` PASS; behavior unchanged (the capture checker's counts equal M5's for every scenario in QEMU) |
| M6-4 | The model instance and differential case, or the recorded deferral | `./be model-check` and `./be evaluate` PASS; no theorem changed |
| M6-5 | Release surfaces: the guide's boot story and layout, the walkthrough, the disclosure, the ledger's rows that cite the prelude, the layout, or M0-A.5's non-claim (C-10's evidence hashes among them), `mvp/README.md`; the roadmap row | `claim-ledger-check` PASS |
| M6-6 | `X3` fixed; the gates from a clean checkout (the lock, `check`, `evaluate`, `uboot-rehearsal`, `kernel-repro`, `model-check`, `evaluate`); `rc-record` | records verify |
| M6-7 | The board campaign at `X3`'s images under the S3-A policy as M5 ran it: preflight, staging, records, install (the human present), 20 runs (3 probes, 12 scenario runs, 5 negatives), restore (the human present), fresh-prompt check, preflight after, `board-evidence` | 20 of 20 as declared; the restore rule satisfied |
| M6-8 | The evidence record; the ledger rows; release candidate 3 (`RC3`, over `X3`; the name avoids the R-series' `R3`); `check` at `RC3`; the packet | packet presented |

Order: M6-2, then M6-3 and M6-4 (independent), M6-5, M6-6, M6-7, M6-8.
Coding runs on `claude-opus-5.5` sub-agents in worktrees as M5's did;
this model plans, orchestrates, reviews each merge line by line, runs the
gates and the campaign, and writes the records and the packet (the
session's standing split).

## Soft limits (re-evaluation stops)

**Counting rule:** added lines by `git diff --numstat` from the M6 base
(this plan's acceptance record) in C, assembly, linker scripts, Python,
shell, Make, and the wrapper, tests included; generated files, fixtures,
JSON, Markdown, and the model's Rocq excluded and reported separately.
**Limit: 4,000.** Estimate: the widened manifest rules and `mvp-config`
generation 400 to 600; the boot and the builder's new input 300 to 500;
removals net negative; the linker script and layout 150; the image and
capture checkers 300 to 500; host tests 400 to 600; the executor and the
table 300 to 500; the model instance and harness case 200 to 400; tools
and docs scripts 100: 2,150 to 3,350. Rocq additions reported, unlimited.
Documents unlimited. The proof-bearing subset's line count is reported,
not limited.

## Stop conditions (each returns to the human)

1. Any need to change an accepted R0-R7 or B0-B7 byte, or an accepted
   document's text (ports and this plan's own revision excepted).
2. Any need to change the claim's text or the required limit.
3. Any need to move an MVP-owned extent, the image's base or size, the
   shim's placement, or the staging, window, or shared-page addresses.
4. Any need to change a proved Rocq theorem, or a model instance that
   cannot be made additively.
5. A monitor behavior change the capture checker can see in a scenario's
   declared lines or counts, other than the markers this plan renames
   and removes.
6. The soft limit exceeded (checkpoint after M6-2 and after M6-3).
7. A board run whose verdict differs from the declared one; a count M5
   compared that differs and the captures do not explain; a layout
   surprise at the characterization step (a reservation inside an MVP
   extent).
8. The board unavailable or in the other project's use (wait; no board
   command before the human's confirmation).
9. Any push, merge, tag, publication, or release step.
10. Any kexec launch (the standing rule).
11. A generated `mvp-config` that disagrees with the authority report, or
    a boot-time validation failure of a scenario the offline checker
    passed (a defect in one of them; which one is the human's to see).

## Open questions and defaults

| ID | Question | Default |
| --- | --- | --- |
| Q1 | The widened limits | harts 3 named plus the platform count; resources 24; authorities 12; mappings 8; roots and domains 2; each a port rule on the MVP's `manifest.h` copy, asserted against the generated configuration's counts |
| Q2 | Markers | `BE_R3:01` to `:06` replaced by `BE_MVP:00 BOOT_VALIDATED` and `BE_MVP:00 CONFIG_SEALED …`; `BE_MVP:01` onward unchanged; the fixtures regenerated from new QEMU captures; the retained records untouched |
| Q3 | `KEXEC_*` and `kexec_fdt` | removed (open item 59 closes); the configuration identities change with the rest |
| Q4 | The model | additive instance and differential case if the generated instances' shape admits it; else deferred with a recorded reason |
| Q5 | The executor's scope | CSR writes, fences, SBI calls, and the console write; the trap assembly unchanged; no contracts |
| Q6 | The configuration identity | SHA-256 over the canonical inventory and proposal bytes, printed in `CONFIG_SEALED` and recorded in the authority report |
| Q7 | Board runs | 20 as M5: three GCC probes, each scenario three GCC and one Clang, five negatives; the probes again because the layout and the boot changed |
| Q8 | Characterization | none beyond M5's (the board facts hold); the campaign's first run is the first probe |
| Q9 | Release candidate naming | `X3` the candidate tree, `RC3` the release-candidate commit |
| Q10 | A steering review of this plan by another model | none (the SOP); run one if the human asks |
| Q11 | What the guide says about the boot | section 3's line-by-line story rewritten for the new markers; the M4/M5 records' stories stay theirs |

## What acceptance authorizes

M6-2 to M6-8 on branch `beryllium/mvp-m6` from the acceptance-record
commit, with Q1 to Q11 at their defaults unless answered, under the
stop conditions above; board commands only after the human confirms the
board free, with the human present at the install and the restore; no
push, merge, tag, publication, release, or kexec use.
