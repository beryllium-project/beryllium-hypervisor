<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R5 checked-switch evidence

## Status and evidence boundary

This is an implementation and evidence record, **not** the decision record.
Responsible-human review accepted exact R5 plan commit
`fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30 and separately
authorized R5 implementation under that accepted plan, with the verbatim
instruction, timestamped 2026-07-30T04:33:03.944+00:00:

```text
authorize r5 implementation, proceed
```

The decision record is `a8161e639af4a141e0d3ca1322202c91129724c7`
(`docs: accept and authorize single-hart runtime R5 plan`).

**R5 implementation exists as an exact immutable commit, and that exact
commit is now responsible-human accepted:** accepted target
`165f4d001a2b59b582b397bdea79ec4826168fdb`
(`tests: make R4 and R5 checks fresh-worktree safe`) over parent
`9312c1355a23d411e3bdafb2183be342683a8ab9`
(`runtime: implement bounded single-hart R5 switch`). It had independently
passed `./be r5-check`, `./be r4-check`, and `make check` first-try from
separate fresh detached worktrees checked out at that exact target, and an
independent core/runtime review found no significant issue. The responsible
human then accepted it on 2026-07-30 with the verbatim instruction,
timestamped 2026-07-30T18:06:26.639+00:00:

```text
accept exact 165f4d001a2b59b582b397bdea79ec4826168fdb
```

`tests/r5/check-acceptance.sh` always reports
`r5_accepted_commit=165f4d001a2b59b582b397bdea79ec4826168fdb`, identifying
the responsible-human accepted target even when local drift makes
validation fail. It reports `r5_acceptance=accepted` and
`r5_accepted_mechanism_match=yes` only when immutable inputs match the
target's bytes and modes, approved-delta inputs match their exact pinned
target-to-current deltas, the self-referential acceptance-tooling path
passes its current-file regular/allowed-mode/non-empty checks, and pinned
dependencies match; it refuses the plan, decision-record, parent, and
review-packet commits as acceptance targets. This evidence record
is regenerated from whatever source is currently checked out; it must not be
read as, and does not itself constitute, responsible-human acceptance. The
exact-target review and acceptance record is
`planning/single-hart-runtime-r5-review-summary.md`; the commit that added it
as a decision packet, `9bb89fe196740c5e3252bdccced6fb202df65e55`, and the
later commit that records the decision, are decision support, not
implementation.

Acceptance adds no new validation. The exact-target results recorded below
remain the evidence boundary; no run from a follow-up or dirty worktree is
claimed as exact-target validation.

The status block below is the verbatim output of
`tests/r5/check-acceptance.sh` in this acceptance record. At the accepted
target itself the same checker reported `r5_acceptance=not-reviewed` and
`r5_accepted_commit=none` unconditionally, because no decision existed yet
and the checker is part of the content-bound package under review. Following
the R3 and R4 convention, the acceptance fields are updated only here, in a
responsible-human acceptance record, never by a review packet.

```text
r5_plan_acceptance=accepted
r5_plan_accepted_commit=fecae6b62a507bdbb93d211262197a31f5422316
r5_plan_accepted_at=2026-07-30
r5_decision_record_commit=a8161e639af4a141e0d3ca1322202c91129724c7
r5_authorization=authorized
r5_authorized_at=2026-07-30
r5_implementation=complete
r5_implementation_record=complete-accepted-content
r5_implementation_content_match=yes
r5_implementation_content_digest=a26fcf98375ccb665c025fc8a7514f9c73b9c6b406ba518cc62154f9a1908b9c
r5_dependencies_match=yes
r5_acceptance=accepted
r5_accepted_commit=165f4d001a2b59b582b397bdea79ec4826168fdb
r5_accepted_at=2026-07-30
r5_accepted_parent_commit=9312c1355a23d411e3bdafb2183be342683a8ab9
r5_accepted_mechanism_match=yes
r5_review_target=165f4d001a2b59b582b397bdea79ec4826168fdb
r5_review_packet_commit=9bb89fe196740c5e3252bdccced6fb202df65e55
r6_authorization=not-authorized
r5_publication_scope=blocked
r5_hardware_validation=NOT-RUN
r5_formal_verification=NOT-RUN-not-claimed
```

The maintained decision identity is:

```text
r5_accepted_target_commit=165f4d001a2b59b582b397bdea79ec4826168fdb
r5_accepted_target_parent=9312c1355a23d411e3bdafb2183be342683a8ab9
r5_review_record=planning/single-hart-runtime-r5-review-summary.md
r5_review_decision=accepted-2026-07-30
```

This does not alter any earlier accepted identity: R3 remains accepted only
at exact target `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`, and R4 remains
accepted only at exact target `0783dfc6557453fbac0da93a5364f2e6e2cb1f52`
(implementation parent `6e5c55c59e94bbaba136269c784db28ec1b53f54`; its
acceptance-record follow-up HEAD `87b136bc4889a04a58c2399e4eb81f7925cba5e0`
is not implementation). R5 composes over that accepted R4 state and modifies
no R0-R4 accepted file.

At the time this record was accepted, R6 and every later successor remained
not authorized and not started. R6 implementation work has since been
separately authorized and its bounded plan accepted; the R6 package is now
complete locally and fully checked but uncommitted, unreviewed, and
unaccepted (see the
[R6 adversarial-image evidence](single-hart-runtime-r6-evidence.md)). That
changes nothing about this record: no R6 result is claimed here, and R7 and
every later successor remain **not authorized and not started**.
Push, tag, publication, and release remain **blocked**. The VitePress
generated-asset byte-reproducibility finding remains **open and
unresolved**; this record does not resolve it, and passing functional
documentation/browser gates is not a claim of byte reproducibility.

## Exact bounded behavior

Within one image, R5 first re-executes the accepted R4 management prelude to
its exact `COMPLETE` state, then performs exactly one checked two-way domain
switch:

```text
exact accepted R4 management prelude (denied load, private event, COMPLETE)
  -> import R4 COMPLETE at sepc=0x40010034
  -> checked switch management -> protected
  -> protected fixture (denied private load, denied shared store, switch event)
  -> checked switch protected -> management
  -> management final event
  -> allowlisted SRST shutdown
```

`include/be/r5.h` fixes the protected binding (vCPU `2`, immutable R2 root
`102`, saved-state id `2`, guest SP `0x40002000`, trusted SP `0x8022a000`,
saved physical page `0x8022c000`) and reuses the unchanged 320-byte R4 frame.
The R5 phase machine is exactly one-way:

```text
FRESH -> IMPORT_R4_COMPLETE -> PENDING_PROTECTED -> PROTECTED_FENCED
  -> PROTECTED_PUBLISHED_EXPECT_LOAD_FAULT
  -> PROTECTED_EXPECT_SHARED_STORE_FAULT
  -> PROTECTED_EXPECT_SWITCH_EVENT
  -> PENDING_MANAGEMENT -> MANAGEMENT_FENCED
  -> MANAGEMENT_PUBLISHED_EXPECT_FINAL_EVENT -> COMPLETE

any state -> FAILED (sticky, no recovery)
```

The protected fixture executes at fixed four-byte PCs from `0x40011000`
through the final saved (not executed) slot `0x40011034`. Both G-stage
denials and the two events observed in this run match the plan exactly:

| Event | PC | `scause` | Observation |
| --- | --- | --- | --- |
| Protected denied private load | `0x40011014` | `21` (`0x15`) | GVA/GPA `0x40000000`; same-domain resume to `0x40011018`. |
| Protected denied shared store | `0x40011024` | `23` (`0x17`) | GVA/GPA `0x40002000`; candidate `68` does not commit; backing stays `34`; same-domain resume to `0x40011028`. |
| Protected switch event | `0x40011030` | `10` (`0x0a`) | `{a7=2,a6=0,a0=51,a1=34}`; saves advanced `sepc=0x40011034` and starts `PENDING_MANAGEMENT`. |
| Management final event | `0x40010038` | `10` (`0x0a`) | `{a7=3,a6=0}`; reports `s0=17, a0=17, a1=34`. |

The observed final backing values are management-private `17`, shared `34`,
and protected-private `51`, matching the plan's frozen fixture exactly. HS
then requests only the fixed allowlisted SRST shutdown; the run exits with
QEMU status `0`. There is no guest entry after the final event.

## Switch transaction and root/CSR boundary

Each of the two cross-domain switches performs the same ordered, no-rollback
transaction, observed in every run:

1. validate the source binding, current HGATP, VS origin, and trusted stack;
2. save the complete source frame into its saved-state page;
3. form one complete pending target binding (never a guest-selected one);
4. write the target HGATP while `V=0`;
5. execute local `HFENCE.GVMA x0,x0`;
6. read back and validate the written target HGATP;
7. reset and verify target reset (R-) state, then validate/prepare its
   S-frame (initial GPR/VS/trap state for protected; the saved R4 frame for
   the return switch);
8. atomically publish the target active state and clear pending; and
9. in a no-call assembly tail, restore final GPRs, set `sstatus.SPP=1`, and
   execute `SRET`.

The generated report records exactly one HGATP write, one
`HFENCE.GVMA`, and one verified readback per switch (two switches total), and
the two published HGATP values observed are `0x800000000008021c` (protected
root, physical `0x8021c000`) and `0x8000000000080214` (management root,
physical `0x80214000`) -- both immutable R2 products written by the checked
transaction, never edited in place. No PTE is written or changed after seal.
`vsatp` remains `Bare`; no VS-stage fence is used or required in this fixed
Bare profile. A trap or failure at any pending/fenced/publication-partial
state is terminal; there is no rollback, alternate target, or re-entry.

Isolation observations recorded by the host/image checks for this run:

| Access | Result |
| --- | --- |
| Management read of protected-private | denied |
| Protected read of management-private | denied |
| Protected store to shared | denied |
| Protected read of shared | permitted |
| Management store to shared | permitted |
| Roots immutable after seal | yes |
| PTEs immutable after seal | yes |

## Components and evidence

- `include/be/r5.h` defines the R5 ABI: fixed PCs/values/bindings, phases,
  pending/publication rules, stable error classes, and the
  `be-r5-checked-switch-v1` report schema; it imports `struct be_r4_frame`
  unchanged.
- `virt/be/r5.c` implements architecture-neutral import, phase/binding/frame
  validation, pending construction, publication decision, and sticky
  failure; it contains no privileged instruction.
- `arch/riscv/be/r5-entry.S` and `arch/riscv/be/r5-trap.S` provide the HS
  entry, trusted-stack vector, complete frame save, and the no-call
  restore/`SRET` tail.
- `arch/riscv/be/r5-runtime.c` provides the RISC-V CSR/reset/readback/SRST
  boundary.
- `arch/riscv/be/r5-guest.S` provides the frozen management and protected
  instruction-slot fixtures only.
- `arch/riscv/be/r5-platform.h` and `arch/riscv/be/r5-beryllium.lds` fix
  constants, physical ownership, and linker assertions.
- `tests/r5/r5-check.c` exercises 32 host scenarios and 9,707 assertions,
  identical with both GCC and Clang.
- `tests/r5/check-image.mjs` inspects each linked image for the frozen
  fixture slots, immutable roots, the accepted initial R3/R4 management
  installation, the two ordered cross-switch HGATP writes/fences/readbacks,
  the publication split, and the absence of an R6 path.
- `tests/r5/check-image-parity.mjs` requires GCC/Clang semantic parity
  (`semantic-parity=yes byte-equality=not-claimed`); ELF bytes and hashes are
  intentionally not required to match. In this run the GCC image is 366,944
  ELF bytes and the Clang image is 281,744 ELF bytes; both share the flat
  212,992-byte load image, entry `0x80200000`, six load segments, and
  architecture string
  `rv64i2p1_m2p0_a2p1_c2p0_h1p0_zicsr2p0_zifencei2p0_zmmul1p0_zaamo1p0_zalrsc1p0_zca1p0`.
- `tests/r5/check-qemu-artifacts.mjs`, `tests/r5/test-qemu-artifact-integrity.mjs`,
  and `tests/r5/test-report-rejection.mjs` reject missing, altered, stale, or
  semantically incomplete evidence: in this run the QEMU-artifact integrity
  test rejected 12 artifact mutations per toolchain and the report-rejection
  test rejected 38 report mutations; the accepted target itself carried 34,
  and this acceptance record adds four acceptance-field mutations. There is
  no negative *image* test in R5;
  compiled adversarial image fixtures remain R6 scope and are not claimed
  here.
- `tests/r5/test-tool-binding.mjs` and `tests/r5/test-acceptance-content.mjs`
  reject hostile Make/shell/tool controls and inconsistent
  acceptance/plan/record/digest combinations. `tests/r5/make-control.mjs`
  validates Make controls against an allowlist rather than a list of forbidden
  spellings, so clustered short options and bare Make flag words cannot slip
  through: in this run 53 launcher cases, 28 raw command-line cases, and 30
  raw environment cases were rejected, including `-i`, `--ignore-errors`,
  `-ik`, `-ki`, `MAKEFLAGS=i`, `MAKEFLAGS=k`, `MAKEFLAGS=n`, `GNUMAKEFLAGS=ik`,
  and `MFLAGS=-ik`. Each is rejected while the Makefile is being parsed,
  before any recipe line or success banner, and an unpinned or renamed copy of
  Make is rejected rather than allowed to borrow a legitimate outer
  invocation.
- `tests/r5/check-sources.mjs` records a 27-input source-inventory digest for
  this run; `tests/r5/check-acceptance.sh` separately reports a distinct
  content-binding digest covering current bytes and modes for the immutable,
  approved-delta, and acceptance-tooling paths. Immutable paths are
  byte-and-mode compared against the accepted target
  `165f4d001a2b59b582b397bdea79ec4826168fdb`; approved-delta paths are pinned
  by exact target-to-current mode/content delta digests rather than direct
  byte comparison; and the sole acceptance-tooling path
  (`tests/r5/check-accepted-content.mjs`) cannot pin its own delta without a
  fixed point, so it is instead checked for a regular, allowed-mode,
  non-empty current file and folded into the reported current-worktree
  digest without being compared to the accepted commit.
  Both the content-binding digest and the source-inventory digest are
  current-worktree values, not accepted-commit hashes.

The generated report is `build/r5/reports/checked-switch.json`, schema
`be-r5-checked-switch-v1`; evidence retention copies it to
`build/r5/evidence/report.json`. It records the authorization/acceptance
status block above, source/tool-lock/firmware hashes, per-toolchain image and
QEMU semantics, the two switch-transition records, the isolation table, the
final backing observations, and an explicit non-claim block. Report
generation is deterministic for a fixed checked input set: `r5-report`
generates the report twice from the same retained artifacts and requires the
two outputs to be byte-identical. Determinism across independent launches is
claimed only semantically: the checkers compare canonical per-run trace
tuples (ordered events, VS entries, traps, root installs, and counts) within
each toolchain and across GCC and Clang, and require the six retained console
logs of a run set to hash identically. Raw QEMU `-d in_asm,cpu` logs,
generated reports, and whole evidence bundles are **not** claimed to be
byte-identical across independent launches; observed cross-run variation in
the raw traces is confined to two benign pre-guest areas (TCG boot-ROM block
splitting and an OpenSBI boot-time counter-derived register probe) and does
not reach the checked R5 sequence.
Evidence retention copies the report and all 12 console/trace logs (three
QEMU runs times two console+trace files, per toolchain) to
`build/r5/evidence/`, together with two per-toolchain image manifests, an
aggregate `artifacts.sha256`, and a claim ledger; retention rechecks SHA-256
integrity of exactly those retained bytes.

The checked launcher `tests/r5/run-make.sh` is the normative interface. It
admits exactly one of `r5-toolcheck`, `r5-host-test`, `r5-image`,
`r5-image-check`, `r5-qemu`, `r5-report`, `r5-evidence`, `r5-check`, or
`clean`; rejects external Make, shell, compiler, linker, QEMU, Node, and
forged-success controls; and invokes the locked `tests/r5/Makefile`, which
independently repeats the parse-time hostile-control checks and validates
`tests/r5/tool-lock.conf` (based on, and rejecting rebinding away from,
`tests/r3/tool-lock.conf`). Every normative executable is bound to an
absolute command path, resolved path, version, SHA-256, and owning package,
including the pinned OpenSBI firmware
(`qemu-system-riscv-core-10.2.2-1.fc44.x86_64`,
SHA-256 `49bdf7b939bda11321132d1042bf99d7324fb190f1feef423171fed3573f8705`).

## Reproducible commands

Run the checked R5 targets from the repository root:

```sh
./tests/r5/run-make.sh r5-toolcheck
./tests/r5/run-make.sh r5-host-test
./tests/r5/run-make.sh r5-image
./tests/r5/run-make.sh r5-image-check
./tests/r5/run-make.sh r5-qemu
./tests/r5/run-make.sh r5-report
./tests/r5/run-make.sh r5-evidence
./tests/r5/run-make.sh r5-check
```

The corresponding stable root-wrapper commands are:

```sh
./be r5-check
./be r5-evidence
```

`r5-host-test` requires the GCC and Clang result streams to match and
reports exactly 32 scenarios and 9,707 assertions. `r5-image-check` requires
the same checked semantics from GCC/GNU-ld and Clang/lld, not byte equality.
`r5-qemu` retains three runs for each compiler: six bounded QEMU runs total,
each showing the ordered accepted R3/R4 setup, the R4-to-R5 import, both
cross-domain HGATP writes/fences/readbacks, the management/protected
expected fault and event sequence above, and the final allowlisted SRST
shutdown with QEMU exit status `0`. `./be r5-evidence` additionally regenerates
and rechecks the retained evidence bundle under `build/r5/evidence/`.

## Claims and exclusions

The evidence supports only this bounded, QEMU-only functional statement for
the exact responsible-human accepted R5 target
`165f4d001a2b59b582b397bdea79ec4826168fdb`:

> In the fixed single-hart QEMU profile, GCC and Clang images re-execute the
> accepted R4 management prelude, import its exact `COMPLETE` state, perform
> a checked management-to-protected switch (one target HGATP write, one
> local fence, one verified readback), exercise the fixed protected fixture
> (a denied private load, a denied shared store that does not alter shared
> backing, and a switch event), perform the symmetric checked
> protected-to-management switch, validate the final management event with
> the expected backing observations, and issue only the allowlisted SRST
> shutdown -- all without a root/PTE edit after seal, a rollback, or an R6
> path.

It does **not** support any of the following:

- any acceptance beyond the exact accepted commit
  `165f4d001a2b59b582b397bdea79ec4826168fdb`, whose acceptance adds no new
  evidence -- the review-packet commit
  `9bb89fe196740c5e3252bdccced6fb202df65e55` and the acceptance-record
  commit are decision support, not accepted implementation;
- any authorization derived from that acceptance for R6, a successor, a tag,
  a push, publication, release, or a publication-gate change;
- hardware or K3 validation -- `NOT RUN`;
- formal proof, refinement, or verification -- `NOT-RUN-not-claimed`;
- Linux, service, guest-SBI, device, DMA, interrupt, timer, multicore, or
  policy behavior;
- CHERI or Type Enforcement selection or behavior;
- R6 adversarial-image completion or R7 exact-byte proof;
- a Model 0.1/0.2 proof or C-refinement transfer to R5, or a Helium claim or
  proof transfer to Beryllium;
- byte-identical raw QEMU traces, generated reports, or evidence bundles
  across independent launches -- only canonical semantic equality and the
  fixed-input report comparison above are claimed;
- resolution of the open VitePress generated-asset byte-reproducibility
  finding; or
- tagging, pushing, public release, or any authorization for R6 or later
  work.

The tested QEMU behavior is functional evidence only. It does not establish
arbitrary-guest isolation, complete adversarial coverage, production
readiness, or public-release approval. Publication remains blocked pending
the separate responsible-human process.
