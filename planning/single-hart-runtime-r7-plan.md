<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R7 proof and evidence plan

## Status and authority

The responsible human instructed `once complete, commit and push, then
commence R7` on 2026-08-05. The prerequisite R6 acceptance record was committed
as `2cc6e96413ab4d426bbf2327dc6c9b309b3f3aac` and pushed to the private
`beryllium/single-hart-runtime-r0` branch before this plan was started.

That instruction authorizes R7 work under the accepted master-plan row:

```text
R7: proof and evidence
  exact-byte adaptation, claim ledger, evaluator, reports, docs,
  and reproducibility bundle
```

R7 is `authorized` and its bounded plan is responsible-human accepted at exact
target `18c43596d308052cfad67edc6e2cb8f543f75600` on 2026-08-05, recorded in
[`single-hart-runtime-r7-plan-review-summary.md`](single-hart-runtime-r7-plan-review-summary.md)
at acceptance-record commit `014b0f654ed65758bb99112f401529975d2dfd44`. That
acceptance covers the plan text only. Implementation under it is local,
untracked, unreviewed, and unaccepted, and no R7 result is accepted evidence.
Root integration is blocked pending acceptance of
[Plan revision R7-A](#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh).

The accepted implementation input is exact R6 target
`7ba3649f03cf13b65df33020e345d361cce2993a`, whose immediate implementation
parent is `9ed5ad7069b6067f03e1923c09937fe218240a59`. The acceptance-record
follow-up is decision support, not implementation.

Exact plan target `18c43596d308052cfad67edc6e2cb8f543f75600` was
responsible-human accepted on 2026-08-05 and remains accepted history.
[Plan revision R7-A](#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh)
is a later, narrower proposal that is **not** covered by that decision and is
unreviewed until a responsible human accepts an exact commit containing it.

## Plan revision R7-A: authorized predecessor acceptance-pin refresh

**Status: proposed, not reviewed.** This revision changes no proof obligation,
symbol, cut point, claim, tool, retention rule, or non-goal. It adds exactly
one thing the accepted plan requires but does not supply: the prior
enumeration of the predecessor acceptance-pin updates that the plan's own root
integration needs.

Until a responsible human accepts an exact commit containing this revision:

- R7 root integration stays blocked;
- no predecessor acceptance-pin constant may be recomputed or replaced;
- root `Makefile`, `be`, and `scripts/check-be.sh` stay byte-unchanged; and
- no R7 implementation output becomes accepted evidence.

Acceptance of this revision would authorize only the six enumerated pin
refreshes and the already accepted root-integration edits. It would accept no
R7 implementation, no R7 evidence, no R7 claim, and no successor.

### The defect in the accepted plan

The accepted [package boundary](#package-boundary) permits root integration
limited to root `Makefile` targets, `be`, `scripts/check-be.sh`, maintained
documentation sources, and generated planning HTML, and then states:

> Any predecessor acceptance-pin update must be enumerated before it is
> applied, derived from the exact target-to-current delta, and leave every
> R0-R6 acceptance checker passing. A needed update outside that enumerated
> set is a plan defect, not permission to widen the implementation.

The accepted plan enumerates **no** such update. Editing any of those three
root files is impossible without one, because accepted predecessor acceptance
checkers bind all three by exact content and mode. The accepted plan therefore
authorizes root integration and simultaneously forbids the only way to perform
it. That is a plan defect, and the accepted rule names the correct remedy: a
revision, not a widened implementation. This revision supplies the missing
enumeration and nothing else.

### What the isolated diagnostic established, and its status

Root integration was attempted once in an isolated working copy to measure,
not to apply, the binding. Its diff is retained only as ephemeral local
scratch at `build/r7-root-integration-blocked.patch`, which is generated
output and not part of any package, evidence bundle, or commit. **No tracked
root file was edited and no acceptance-pin constant was recomputed into any
checker**; the only working-tree change from the R7 work is the untracked
`tests/r7/` package.

The diagnostic observed that:

1. the R7 checked launcher, `r7-check`/`r7-evidence` targets, `check` and
   `clean` participation, help and status text, and wrapper assertions require
   edits to exactly root `Makefile`, `be`, and `scripts/check-be.sh`, matching
   the accepted plan's root-integration list;
2. three accepted predecessor checkers bind those three files, producing
   exactly six constants;
3. the accepted R6 framework already measures this same set. Accepted
   `tests/r6/acceptance-pins.mjs` enumerates the identical six pins, marks a
   pin `required` when its bound file differs from accepted R5 target
   `165f4d001a2b59b582b397bdea79ec4826168fdb`, marks it `applied` only when
   the recorded constant equals the constant its owning checker recomputes
   from the **current** worktree, and hard-fails on a partly applied refresh
   or on a count that is neither `0` nor the full authorized set. Editing the
   three root files for R7 without refreshing all six therefore fails accepted
   R6 checks as well as the R1/R3/R4 checkers; and
4. no seventh constant and no fourth root file was observed, and no
   predecessor self-test appeared to need a change. The accepted R5 structural
   fix already stages
   `be`, `scripts/check-be.sh`, `tests/r1/check-acceptance.sh`,
   `tests/r3/check-accepted-content.mjs`,
   `tests/r4/check-accepted-content.mjs`, and root `Makefile` into the
   predecessor negative worktrees, so the shared successor command graph
   appears to need no further teaching for R7. That observation must be
   re-established by running the negative suites at the exact implementation
   candidate.

The diagnostic's conclusion is that these six refreshes are **sufficient** to
make the accepted root-integration edits pass every predecessor acceptance
checker, and **minimal** in that removing any one of them leaves a bound file
edited without its matching constant, which its owning checker refuses.

**Status of those findings: unreviewed local implementation discovery.** They
are not retained R7 evidence, they are not accepted, and no value measured
during the diagnostic is pinned by this revision or may be carried into an
implementation commit as if it were already checked.

### Bound files and binding checkers

| Bound file | Bound by | Binding form |
| --- | --- | --- |
| root `Makefile` | `tests/r1/check-acceptance.sh` | one exact successor mode (`644`) and one exact SHA-256 of the file bytes |
| `tests/r1/check-acceptance.sh` | `tests/r3/check-accepted-content.mjs` | one approved target-to-current delta SHA-256 |
| `be` | `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs` | one approved target-to-current delta SHA-256 per checker |
| `scripts/check-be.sh` | `tests/r3/check-accepted-content.mjs`, `tests/r4/check-accepted-content.mjs` | one approved target-to-current delta SHA-256 per checker |

### Authorized refresh: exactly six constants, no others

| # | File | Constant | Bound file | Reason |
| --- | --- | --- | --- | --- |
| 1 | `tests/r1/check-acceptance.sh` | `successor_makefile_sha256` | root `Makefile` | the root `Makefile` gains the `r7-check`/`r7-evidence` targets and the R7 `check`, `evidence-check`, and `clean` steps |
| 2 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` for `tests/r1/check-acceptance.sh` | `tests/r1/check-acceptance.sh` | constant 1 changed that file |
| 3 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` for `be` | `be` | `be` gains the R7 launcher binding, subcommands, help, status, version, and clean participation |
| 4 | `tests/r3/check-accepted-content.mjs` | `approvedDeltaSha256` for `scripts/check-be.sh` | `scripts/check-be.sh` | `scripts/check-be.sh` gains the R7 wrapper assertions |
| 5 | `tests/r4/check-accepted-content.mjs` | `approvedDeltaSha256` for `be` | `be` | same `be` edit, second binding |
| 6 | `tests/r4/check-accepted-content.mjs` | `approvedDeltaSha256` for `scripts/check-be.sh` | `scripts/check-be.sh` | same `scripts/check-be.sh` edit, second binding |

This is the complete authorized set. Nothing may be added to it, removed from
it, or reordered within it. In particular the R1 accepted-commit and
`successor_makefile_mode` constants, the R3/R4 accepted-commit, accepted-date,
parent, and review-packet constants, every `immutablePaths` entry, every other
`mixedFiles` entry, every `addedFiles` entry, and every R2, R5, and R6
acceptance surface stay exactly as accepted. If implementation shows that a
seventh constant, a fourth root file, or a predecessor self-test change is
required, R7 must stop and request a further revision. That discovery is a
plan defect, never permission to widen the set.

### Exact binding formulas

Constants 2 through 6 are the mixed approved target-to-current delta computed
by the owning checker as:

```text
SHA-256( target mode || NUL || current mode || NUL
         || target bytes || NUL || current bytes || NUL )
```

where each of the four parts is followed by a single `0x00` byte, the modes
are the git regular-file strings `100644` or `100755`, the target mode and
bytes come from that checker's own accepted commit
(`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` for
`tests/r3/check-accepted-content.mjs`,
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` for
`tests/r4/check-accepted-content.mjs`), and the current mode and bytes come
from the worktree at the exact R7 implementation candidate. The owning
checkers already reject a target-to-current mode change outright, so a mode
difference is a failure, never a value to re-pin.

Constant 1 is **not** that formula. `tests/r1/check-acceptance.sh` keeps its
existing successor mode-and-content form: the root `Makefile` mode read with
`stat -c '%a'` must equal the unchanged pinned `644`, and
`successor_makefile_sha256` must equal the plain SHA-256 of the root
`Makefile` bytes, as reported by `sha256sum`, at the exact R7 implementation
candidate. Only the SHA-256 constant is refreshed; the mode constant is not
touched.

### Re-derivation rule

Every one of the six constants must be re-derived from the exact future R7
implementation candidate, by running the owning checker's own computation over
the committed content of that candidate. Values observed during the blocked
diagnostic, during any earlier local run, or in any scratch patch are
explicitly **not** pinned by this revision, must not be copied into a checker,
and must not be cited as accepted evidence. A constant that was not recomputed
at the exact candidate is a defect even if it happens to match.

### Mandatory ordering

An R7 implementation candidate must perform root integration in this order:

1. record pre-edit evidence: `tests/r1/check-acceptance.sh --require`,
   `tests/r2/check-acceptance.sh --require`,
   `tests/r3/check-acceptance.sh --require`,
   `tests/r4/check-acceptance.sh --require`, and
   `tests/r5/check-acceptance.sh --require` all pass, with
   `r5_acceptance=accepted` and `r5_accepted_mechanism_match=yes`, and
   `tests/r6/check-acceptance.sh` reports `r6_acceptance=accepted`, using
   `--require` once the R6 gate has generated and checked its report;
2. edit only root `Makefile`, `be`, and `scripts/check-be.sh`;
3. recompute and replace exactly the six constants above, and nothing else;
4. re-run all six acceptance checkers, each of which must pass again with
   unchanged accepted-commit identities and an unchanged R5 implementation
   content digest; and
5. only then run the R7, predecessor, documentation, and repository gates.

A candidate that edits a root file without the matching refresh, or refreshes
a constant no edit required, is refused rather than reported.

### Required validation before an R7 candidate is reviewable

- every target-to-current mode is unchanged for all six bound and binding
  files;
- no accepted R0-R6 mechanism byte under `arch/`, `include/`, `virt/`,
  `tests/r0/`-`tests/r6/`, or any other accepted acceptance surface changes,
  apart from the six enumerated constants;
- each refreshed constant equals the exact approved target-to-current delta
  its owning checker recomputes at the candidate, and matches `^[0-9a-f]{64}$`;
- `tests/r1/`, `tests/r2/`, `tests/r3/`, `tests/r4/`, `tests/r5/`, and
  `tests/r6/` acceptance checkers all pass with `--require`, the R6 checker
  after its own gate has generated and checked its report, and the accepted
  R6 acceptance-pin manifest reports all six pins `required` and `applied`;
- the R3, R4, and R5 negative and rejection suites still pass, including the
  isolated-worktree acceptance-content self-tests;
- `scripts/check-be.sh` passes, with the accepted R6 rule preserved: the
  historical R6-owned R7 authority keys stand exactly once each in `be` and in
  the wrapper check, carrying exactly the accepted values, and any live R7
  posture is separately keyed and measured rather than declared;
- `./be r7-check` and `./be r7-evidence` pass through the checked launcher;
- `./be docs-check` passes for the maintained Markdown, navigation, and
  generated planning HTML; and
- `make check` passes from a fresh detached worktree at one exact clean
  commit.

Passing these gates does not accept R7. Acceptance still requires the separate
explicit responsible-human decision named in
[Acceptance gates](#acceptance-gates).

### What this revision does not change

R7-A adds no runtime, production, or proof surface. It adds no file under
`include/`, `virt/`, `arch/`, or `tests/r0/`-`tests/r6/`. It changes no
accepted R0-R6 mechanism byte, no symbol scope, no proof obligation, no cut
point, no claim, no tool lock, no retention rule, no evidence limit, and no
non-goal. It does not authorize hardware work, publication, tagging, pushing,
release, R8, or any successor, and it does not make any R7 result accepted.

### R7 package state under this revision

The `tests/r7/` package is complete in the local working tree, matching the
accepted plan's inventory, and is untracked, unreviewed, and unaccepted. Its
proof, report, and evidence outputs are local implementation results only.
Root integration is blocked, no acceptance pin is applied, hardware validation
is `NOT RUN`, and R8 and publication remain blocked.

## Objective

R7 answers three bounded questions for the fixed single-hart QEMU profile:

1. Which exact privileged-wrapper bytes are linked into the GCC/GNU ld and
   Clang/lld R5 images carried unchanged by the accepted R6 target?
2. What transition, trap-frame, root-install, fence, readback, restore, and
   `SRET` properties follow from those bytes in a bounded RV64 model?
3. Do generated fixed-configuration facts instantiate the already accepted
   two-domain, two-root, three-mapping-per-root access matrix without claiming
   a C refinement or transferring Model 0.2 or Helium theorems?

R7 adds evidence only. It changes no accepted runtime source, image behavior,
fixture expectation, page table, policy, or guest-visible interface.

## Supportable completion claim

If every gate in this plan passes at one exact clean commit, R7 may support:

> For the fixed single-hart QEMU profile and both pinned toolchains, a
> machine-checked bounded development consumes exact linked bytes from the
> accepted R5 runtime image, independently cross-checks those bytes with GNU
> objdump, decodes the enumerated privileged-wrapper subset, checks the fixed
> entry, trap-frame, root-install/fence/readback, restore, and return
> properties, and checks generated fixed-configuration facts against the
> accepted two-domain access matrix. The C implementation, direct ELF parser,
> compiler, linker outside the extracted symbols, OpenSBI, QEMU, RISC-V
> hardware, and the connection from C state to the generated configuration
> facts remain explicit assumptions.

This must not be shortened to “Beryllium is formally verified.” It is not a
whole-ELF proof, C refinement, source-to-binary validation result, hardware
validation, arbitrary-guest isolation theorem, or production assurance claim.

## Exact immutable inputs

R7 consumes, but does not modify:

- accepted R5 implementation target
  `165f4d001a2b59b582b397bdea79ec4826168fdb`;
- accepted R6 implementation target
  `7ba3649f03cf13b65df33020e345d361cce2993a`;
- accepted R1 canonical state and R2 Sv39x4 roots;
- the pinned R3/R5 tool lock, GCC/GNU ld and Clang/lld image recipes;
- the ratified RISC-V privileged and hypervisor specifications cited by the
  master plan; and
- the retained Helium exact-proof method as a method reference only.

No Helium theorem, generated constant, proof object, implementation byte, or
assurance claim transfers to Beryllium. R7 must re-extract, regenerate,
re-prove, and re-state every result against the accepted Beryllium images.

## Package boundary

All new implementation content is self-contained under `tests/r7/`:

```text
tests/r7/
  Makefile
  run-make.sh
  tool-lock.conf
  check-tools.sh
  check-sources.mjs
  extract-exact-image.mjs
  check-disassembly.sh
  generate-exact-input.mjs
  check-configuration-trace.mjs
  generate-report.mjs
  check-report.mjs
  generate-evidence.sh
  check-evidence.mjs
  proof/
    ISA.v
    Exact.v
    Entry.v
    Trap.v
    Switch.v
    Configuration.v
    Claims.v
```

Generated exact inputs, proof objects, reports, logs, and evidence live only
under `build/r7/`. Generated proof input is reproduced twice and byte-compared
before Rocq consumes it. Proof objects are checked independently with
`rocq check`.

R7 adds no file under `include/`, `virt/`, or `arch/`. Root integration, after
plan acceptance and only with the package implementation, is limited to:

- `Makefile` targets;
- `be` help, status, version, clean, `r7-check`, and `r7-evidence`;
- `scripts/check-be.sh`;
- maintained planning/navigation/render sources; and
- generated planning HTML.

Any predecessor acceptance-pin update must be enumerated before it is applied,
derived from the exact target-to-current delta, and leave every R0-R6
acceptance checker passing. A needed update outside that enumerated set is a
plan defect, not permission to widen the implementation. The accepted plan
enumerated none;
[Plan revision R7-A](#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh)
supplies the exactly six authorized updates and is itself unreviewed.

## Exact linked-byte scope

The direct ELF extractor reads the final GCC and Clang R5 ELF files and records
the ELF SHA-256, symbol address, size, raw little-endian 32-bit words, and
relocation-resolved branch/call targets for these load-bearing symbols:

### Initial HS setup and management entry

- `be_r3_arch_reset_state`;
- `be_r3_arch_install_management`; and
- `be_r3_arch_enter_management`.

### Trap, checked switching, and return

- `be_r5_arch_reset_state`;
- `be_r5_trap_vector`;
- `be_r5_arch_read_controls`;
- `be_r5_arch_install_root`;
- `be_r5_arch_reset_target`;
- `be_r5_arch_restore_active`;
- `be_r5_switch_tail`; and
- `be_r5_enter_guest_tail`.

The extractor is not trusted for instruction meaning. A separate locked GNU
objdump pass must independently recover the same address and word stream for
every symbol in both images. Any unsupported, compressed, truncated,
overlapping, multiply defined, relocated-out-of-range, or cross-toolchain
unexpected word is a hard refusal.

The proof does not cover `be_reset`, C handlers, diagnostic output, SBI calls,
guest fixtures, or the rest of either ELF merely because those bytes share an
image.

## Bounded proof obligations

### Exact decoding

`ISA.v` defines only the RV64 instruction, CSR, fence, memory, branch, call,
and `SRET` subset required by the extracted symbols. Decode is total over the
enumerated word streams and fails for every unsupported word. Generated input
contains data only; instruction semantics remain maintained proof source.

`Exact.v` checks:

- two exact image records and their ELF identities;
- exact symbol count, address, size, and word count;
- complete decode of every scoped word;
- expected equality and expected relocation differences across toolchains;
- every direct and `AUIPC`/`JALR` control-flow target; and
- no control-flow edge outside the scoped symbol or its explicitly named C
  cut point.

### Entry

`Entry.v` checks the exact reset/install/entry sequence establishes the frozen
CSR profile used by R3, writes the management `HGATP` exactly once, performs
the required local all-GPA/all-VMID `HFENCE.GVMA`, verifies the readback, and
executes `SRET` only with the accepted management PC, stack, root, and
privilege-control state.

### Trap frame

`Trap.v` checks the exact R5 trap wrapper:

- exchanges guest `sp` for monitor-owned trusted storage before any stack
  access;
- saves the complete accepted 320-byte frame at unique, aligned, bounded
  offsets;
- clears live guest GPR authority before calling the C dispatch cut point;
- passes only the monitor-owned frame pointer to C;
- treats dispatch return as terminal failure; and
- reaches only the named restore/switch/terminal paths.

The C dispatch body remains an explicit cut point. R7 does not prove it.

### Root transaction and return

`Switch.v` checks:

- `be_r5_arch_install_root` observes the source root, writes exactly one
  monitor-selected target `HGATP`, records the written value, performs exactly
  one local `HFENCE.GVMA`, and reads back before returning;
- target reset and active restore never rewrite a G-stage page table;
- restore paths require the expected root and trusted stack;
- `be_r5_switch_tail` and `be_r5_enter_guest_tail` are call-free after
  publication;
- the complete accepted frame is restored; and
- the shared entry tail contains the sole R5 guest-return `SRET`.

The proof assumes the C mechanism supplies the documented monitor-formed
pending binding and calls a tail only after successful publication. That C
precondition is recorded, not proved.

### Fixed configuration trace

`Configuration.v` consumes generated facts for:

- the accepted thirteen-resource R1 profile;
- two sealed domain authorities;
- two R2 roots with exactly three leaf mappings each;
- management-private, protected-private, and shared backing identity;
- management read/write shared rights;
- protected read-only shared rights; and
- each cross-private denial.

It checks equality with the frozen constants and proves only the finite access
matrix implied by those generated facts. The direct configuration extractor,
R1/R2 C implementation, PTE builder, and C-to-generated-fact connection remain
cut points. Model 0.2's abstract proof remains separate evidence.

### Claim and cut-point ledger

`Claims.v` exports only the theorem bundle named by the report. The generated
claim ledger must separately classify:

- proved exact-byte properties;
- checked generated configuration facts;
- host tests;
- image semantic checks;
- QEMU emulation;
- trusted tool and parser boundaries;
- unproved C cut points;
- `NOT RUN` hardware evidence; and
- explicit non-claims.

A missing, stale, or failed proof lowers the report to `proof=NOT-RUN` or
`proof=FAIL`; no checker may preserve a success-shaped claim.

## Tool and trust boundary

R7 reuses the pinned open R3/R5 build and ELF-inspection toolchain. It adds only
the already selected Rocq 9.2 proof checker from the repository's pinned open
evaluation environment. Every executable is bound by absolute path, resolved
path, version, SHA-256, and owning package.

The normative flow uses no proprietary analyzer, hosted proof service, or
network dependency. Mainline Sail RISC-V H semantics remain incomplete for
this claim and are not introduced. Cerberus, CN, CBMC, Frama-C, Isla/Islaris,
Katamaran, and a C refinement are not R7 dependencies.

Trusted or assumed:

- the ratified ISA is represented faithfully by the bounded local semantics;
- the direct ELF parser and independent objdump cross-check identify the
  intended linked bytes;
- Rocq's kernel and the pinned host platform execute correctly;
- the C cut points satisfy their stated contracts;
- GCC/Clang compile surrounding C correctly;
- OpenSBI provides the frozen handoff;
- QEMU implements the relevant architecture; and
- single-hart, no DMA, no devices, no guest SBI, and the fixed synthetic
  profile remain true.

## Report and retained evidence

The canonical report is `be-r7-exact-proof-evidence-v1`. It records:

- exact repository, accepted R5/R6, plan, tool, source, and generated-input
  identities;
- both ELF identities and every scoped symbol stream;
- direct-parser/objdump agreement;
- decoder coverage and theorem inventory;
- proof-source and proof-object identities;
- `rocq check` output;
- configuration-trace facts and checked matrix;
- R0-R6 acceptance status;
- all cut points, assumptions, and non-claims; and
- hardware, publication, and successor status.

The evidence bundle retains the report, independent checker transcript,
exact-input files, proof sources, proof-object hashes, `rocq check` transcript,
ELF/symbol/word manifests, disassembly cross-check, configuration trace,
claim/cut-point ledger, tool lock, and an exact-set SHA-256 manifest. It does
not retain duplicate R5/R6 QEMU traces. The hard retained-evidence limit is
512 MiB.

## Commands after accepted-plan implementation

The intended checked interfaces are:

```sh
./tests/r7/run-make.sh r7-toolcheck
./tests/r7/run-make.sh r7-extract
./tests/r7/run-make.sh r7-proof
./tests/r7/run-make.sh r7-report
./tests/r7/run-make.sh r7-evidence
./tests/r7/run-make.sh r7-check
./be r7-check
./be r7-evidence
```

The `./tests/r7/run-make.sh` interfaces exist only in the local untracked
package; the `./be` delegations do not exist, because root integration is
blocked pending
[Plan revision R7-A](#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh).
Listing them defines the implementation interface; it is not evidence that any
R7 result has run or is accepted.

## Acceptance gates

An R7 implementation candidate is reviewable only if:

1. the exact plan commit is responsible-human accepted before implementation,
   and the exact
   [Plan revision R7-A](#plan-revision-r7-a-authorized-predecessor-acceptance-pin-refresh)
   commit is separately accepted before root integration or any
   acceptance-pin refresh;
2. no accepted production or R0-R6 mechanism byte changes, apart from the six
   enumerated predecessor acceptance-pin constants;
3. every R0-R6 acceptance checker still reports an exact match;
4. the two final ELF inputs are rebuilt through the pinned checked launcher;
5. direct ELF extraction is deterministic and agrees with independent GNU
   objdump for every scoped word;
6. every scoped word decodes in the bounded maintained semantics;
7. every theorem module compiles without `Admitted`, project `Axiom`,
   project `Parameter`, or an unchecked proof shortcut;
8. `rocq check` independently checks every retained proof object;
9. the fixed configuration trace equals the accepted R1/R2/R5 constants and
   is independently checked;
10. report and evidence rejection suites refuse altered bytes, symbols,
    targets, generated facts, theorems, claims, tools, and manifests;
11. the retained evidence set is exact, hash-covered, and at most 512 MiB;
12. `./be r7-check`, `./be r7-evidence`, predecessor gates, documentation
    checks, and `make check` pass from a fresh detached worktree at one exact
    clean commit;
13. hardware remains `NOT RUN` and no formal, hardware, Linux, service,
    device, multicore, CHERI, TE, production, certification, or release claim
    exceeds the bounded evidence; and
14. a new decision-neutral exact-commit review packet is prepared for the
    responsible human.

Passing these gates does not accept R7. Acceptance requires a later explicit
responsible-human decision naming the exact implementation commit.

## Explicit non-goals

R7 does not add or authorize:

- runtime source, another image, another guest, or another pathfinder;
- Linux, guest SBI, service, device, DMA, interrupt, timer, or multicore work;
- K3 or other hardware validation;
- complete RISC-V ISA or H-extension semantics;
- proof of C validators, C handlers, root-builder C, compiler, linker,
  firmware, QEMU, or hardware;
- whole-ELF, whole-hypervisor, information-flow, availability, timing, or
  side-channel proof;
- arbitrary page tables, arbitrary guests, dynamic mappings, or revocation;
- CHERI, software-capability, Type Enforcement, VBS, attestation, or MVP work;
- public release, publication, tagging, or a public repository push; or
- an R8 or any successor package.

## Current state

```text
r7_authorization=authorized
r7_authorization_source=responsible-human-instruction-2026-08-05
r7_phase=implementation-local-root-integration-blocked
r7_plan_acceptance=accepted
r7_accepted_plan_target=18c43596d308052cfad67edc6e2cb8f543f75600
r7_plan_acceptance_record=014b0f654ed65758bb99112f401529975d2dfd44
r7_plan_revision_r7a=proposed-not-reviewed
r7_implementation=local-uncommitted-not-accepted
r7_root_integration=blocked-pending-r7a-acceptance
r7_acceptance_pins_applied=0-of-6
r7_proof=bounded-local-not-accepted
r7_hardware_validation=NOT-RUN
r7_publication_scope=blocked
r8_authorization=not-authorized
```

The next decision is responsible-human review of an exact commit containing
Plan revision R7-A. Root integration, acceptance-pin refresh, and any R7
evidence or acceptance claim wait for that decision; a later, separate
decision on an exact implementation commit remains required to accept R7
itself.
