<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R5 bounded plan

## Status and decision required

This plan is drafted for exact-commit responsible-human review. It is **not
accepted**; R5 implementation is **not authorized** and **not started**. This
document intentionally names no self-referential plan SHA.

**Decision required:** the responsible human must first accept an exact commit
containing this plan, then separately and explicitly authorize R5
implementation. Neither plan review, dependency order, an R4 acceptance, nor
this document authorizes source, tests, wrappers, Makefiles, evidence
generation, a review packet, a tag, a push, publication, or release.

## Prerequisites and objective

| Prerequisite | Status |
| --- | --- |
| Fixed bounded runtime plan | accepted 2026-07-25 |
| R3 boot-and-first-entry target | accepted at `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` |
| R4 trap-and-context target | accepted at `0783dfc6557453fbac0da93a5364f2e6e2cb1f52` |
| R4 acceptance-record follow-up HEAD | `87b136bc4889a04a58c2399e4eb81f7925cba5e0`, not implementation |
| R5 | defined by this draft; gated, unimplemented, not authorized, not started |

R5 is the bounded checked-switch package for the fixed one-hart QEMU `virt`,
pinned OpenSBI, synthetic two-VS profile. It implements only:

```text
management -> protected -> management -> terminal shutdown
```

It adds no scheduling, restart, rollback, dynamic binding, root edit, PTE
write, policy decision, guest SBI, or later-package behavior. R6 and R7
remain gated.

## Frozen scenario and bindings

### Management-to-protected boundary

R5 reuses the accepted R4 management fixture:

1. management stores then reads private value `17`;
2. its protected-private load at `0x40010014` is denied for GPA/GVA
   `0x40001000`;
3. it resumes at `0x40010018`, writes then reads shared value `34`; and
4. at `0x40010030` it raises the private cause-10 event with
   `{a7=1,a6=0,a0=17,a1=34}`.

The R5 image re-executes this accepted R4 management sequence from the initial
management entry; it does not import execution state from an earlier image.
At the event, the unchanged R4 mechanism validates the event, advances the
saved management frame to `sepc=0x40010034`, and reaches exact R4
`COMPLETE`. Before the platform consumes R4's same-management restore
decision, the R5 mechanism imports that completed state and frame. R5 then
suppresses the same-management restore and begins the checked switch to
protected. This is the only R4-to-R5 seam.

The management binding remains the exact accepted R3/R4 binding. The target
protected binding is fixed:

| Field | Exact value |
| --- | --- |
| Domain | `protected` |
| vCPU | `2` |
| Root | `102` |
| VMID | `0` |
| HGATP | `BE_R3_PROTECTED_HGATP` |
| Initial PC | `0x40011000` |
| Guest SP | `0x40002000` |
| Trusted SP | `0x8022a000` |
| Saved-state ID | `2` |
| Saved physical address | `0x8022c000` |
| VS stage 1 | Bare |
| Publication | unpublished until the checked R5 transition publishes it |

The management and protected roots are immutable R2 products. R5 writes no
PTE and never changes a root, VMID, stack extent, saved-page binding, or
mapping.

### Protected fixture

Protected code starts at GPA `0x40011000`. Every listed fixture operation,
including the private write/read setup before `0x40011014`, occupies frozen
four-byte instruction slots. No assembler relaxation, padding, macro
expansion, or additional instruction may move a checked PC.

| PC | Required operation and observation |
| --- | --- |
| `0x40011000` | `lui t0,0x40001`: select protected-private GPA `0x40001000`. |
| `0x40011004` | `addi t1,zero,51`: construct the fixed protected-private value. |
| `0x40011008` | `sw t1,0(t0)`: write protected-private value `51`. |
| `0x4001100c` | `lw s0,0(t0)`: read back and retain protected-private value `51`. |
| `0x40011010` | `lui t2,0x40000`: select management-private GPA `0x40000000`. |
| `0x40011014` | `lw s1,0(t2)` is denied: `scause=21`, GVA/GPA `0x40000000`; same-domain resume advances to `0x40011018`. |
| `0x40011018` | `lui t2,0x40002`: select shared GPA `0x40002000`. |
| `0x4001101c` | `lw a1,0(t2)`: read shared value `34`. |
| `0x40011020` | `addi t1,zero,68`: construct the fixed denied-store candidate. |
| `0x40011024` | `sw t1,0(t2)` is denied: `scause=23`, GVA/GPA `0x40002000`; candidate `68` must not change shared backing `34`; same-domain resume advances to `0x40011028`. |
| `0x40011028` | `addi a0,s0,0`: report protected-private readback `51`. |
| `0x4001102c` | `addi a7,zero,2`: select protected event `2`; zeroed `a6` remains event version/function `0`. |
| `0x40011030` | `ecall`: private cause-10 event has `{a7=2,a6=0,a0=51,a1=34}`. |
| `0x40011034` | Fixed self-loop, saved but not executed after the protected event in R5. |

The expected final backing observations are management private `17`, shared
`34`, and protected private `51`. For both G-stage faults, `htval` may be zero
or, if supplied, reconstruct the exact GPA using the ratified shifted-HTVAL
treatment. `htinst` is excluded and supplies no acceptance condition.

### Protected-to-management and completion boundary

The protected event saves its advanced protected frame with
`sepc=0x40011034` and switches back to the saved management frame at
`0x40010034`. That management fixture executes exactly
`addi a7,zero,3` at `0x40010034`, then a cause-10 `ecall` at
`0x40010038`. A fixed self-loop at `0x4001003c` is linked but must not execute
after the final event. The completion event preserves and reports:

```text
management s0 = 17
management a0 = 17
management a1 = 34
shared backing = 34
protected-private backing = 51
```

HS validates that final event and requests only the fixed allowlisted SRST
shutdown. A returned SRST request is terminal failure. There is no guest entry
after the final event, whether shutdown succeeds or fails.

## State, frame, and failure contract

Within the same R5 image, the runtime first executes the accepted R4
management prelude:

```text
initial management VS entry
  -> expected management load fault at 0x40010014
  -> same-management resume at 0x40010018
  -> validated management event at 0x40010030
  -> R4 COMPLETE with saved sepc=0x40010034
```

This prelude remains governed by the accepted R4 phase machine and is outside
the R5 phase machine below. R5 imports the resulting completed R4 state and
frame only through an exact accepted-R4 compatibility check; no earlier-image
or synthetic execution state is accepted. It retains the exact R4 320-byte
frame unchanged and uses one monitor-owned saved page per domain. The initial
protected frame is monitor-created: all GPR, VS, and trap fields are zero
except `x2` set to the protected guest SP and `sepc` set to the protected
initial PC; its reserved word is zero. The management frame captured by the
current image's R4 event trap remains saved unchanged until the return switch.

Frame or page selection derives exclusively from the exact active or pending
monitor binding and the checked trusted-stack identity. Guest pointers,
guest-register values, fault addresses, and guest-provided identifiers never
select monitor context or storage.

### Architecture-neutral phase machine

The planned one-way states are:

```text
FRESH
  -> IMPORT_R4_COMPLETE
  -> PENDING_PROTECTED
  -> PROTECTED_FENCED
  -> PROTECTED_PUBLISHED_EXPECT_LOAD_FAULT
  -> PROTECTED_EXPECT_SHARED_STORE_FAULT
  -> PROTECTED_EXPECT_SWITCH_EVENT
  -> PENDING_MANAGEMENT
  -> MANAGEMENT_FENCED
  -> MANAGEMENT_PUBLISHED_EXPECT_FINAL_EVENT
  -> COMPLETE

any state -> FAILED
```

`FRESH` admits only one exact in-image R4 `COMPLETE` import with the advanced
management frame. The preceding initial management entry, expected management
load fault, same-domain resume, and management event are required R4-prelude
evidence but are not duplicated as R5 phases.
`PROTECTED_FENCED` and `MANAGEMENT_FENCED` are post-fence/readback,
pre-publication partial-transition states. Publication atomically enters
`PROTECTED_PUBLISHED_EXPECT_LOAD_FAULT` or
`MANAGEMENT_PUBLISHED_EXPECT_FINAL_EVENT`, respectively.
`PROTECTED_EXPECT_SHARED_STORE_FAULT` and
`PROTECTED_EXPECT_SWITCH_EVENT` are entered only after the preceding
same-domain exit is completely validated and its saved `sepc` is advanced.
The protected load and shared-store exits resume the same domain; the
protected switch event instead saves its advanced frame and constructs
`PENDING_MANAGEMENT`. The names therefore identify the only accepted next
exit at every guest-running phase.

An R5 pending record contains exactly one complete unpublished target binding,
direction (`management-to-protected` or `protected-to-management`), and frame
mode (`initial` or `saved`). The active binding remains the source until the
target root has been written, fenced, read back, and target restore prepared.
Publication atomically makes the target active and clears pending. A duplicate
operation, an invalid phase, a missing or malformed pending record, source or
target mismatch, or any corruption enters sticky `FAILED`.

Stable error classes must distinguish at least: import failure; phase or
duplicate operation; active/pending binding mismatch; trusted-stack or
saved-page mismatch; source HGATP or VS-origin mismatch; non-Bare `vsatp`;
frame/reserved-word failure; target reset/readback failure; fence/ordering
failure; unexpected trap, PC, cause, GVA/GPA, event, or backing observation;
publication partial state; and terminal SRST return. They are diagnostic
classes only and do not create recovery.

## Exact switch transaction

For either direction, the architecture boundary performs exactly this ordered
transaction:

1. Validate source binding, current HGATP, VS origin, trusted stack, and
   `vsatp=Bare`.
2. Save the complete source frame.
3. Form one complete pending target binding and context.
4. Write target HGATP while `V=0`.
5. Execute local `HFENCE.GVMA x0,x0`.
6. Read back and exactly validate target HGATP.
7. Reset and verify target R-state, then validate and prepare its S-frame.
8. Atomically publish target active state and clear pending.
9. In a no-call assembly tail, restore final GPRs, set `sstatus.SPP=1`, and
   execute `SRET`.

No target instruction may execute before the fence and publication. An HGATP
write alone supplies no required ordering. Before target `SRET`, the boundary
also verifies target HGATP, required `hstatus` controls including `SPV` and
`VTVM`, `sstatus.SPP`, and `vsatp=Bare`. No VS-stage fence is needed in this
fixed Bare profile.

A trap or failure during pending, fenced, restore, or publication partial
state is terminal. There is no rollback, alternate target, source fallback,
or re-entry. Failure prevents every future guest entry. The return switch is
the same transaction with the saved management frame mode, not a special
shortcut.

## Planned source and assembly boundary

No R5 file is created by this plan. A separately authorized implementation
would be constrained to these proposed surfaces:

| Proposed path | Planned responsibility |
| --- | --- |
| `include/be/r5.h` | Restricted-C R5 ABI: binding, pending, phase, stable error, observation, and transaction-result declarations; imports `struct be_r4_frame` unchanged. |
| `virt/be/r5.c` | Architecture-neutral import, phase/binding/frame validation, pending construction, publication decision, and sticky failure; no privileged instruction. |
| `arch/riscv/be/r5-entry.S` | HS entry and initial checked handoff. |
| `arch/riscv/be/r5-trap.S` | Trusted-stack vector, complete frame save, source validation handoff, and no-call restore/SRET tail. |
| `arch/riscv/be/r5-runtime.c` | RISC-V CSR/reset/readback/SRST boundary with bounded arguments. |
| `arch/riscv/be/r5-guest.S` | Frozen management and protected instruction-slot fixtures only. |
| `arch/riscv/be/r5-platform.h`, `arch/riscv/be/r5-beryllium.lds` | Fixed constants, physical ownership, and linker assertions. |
| `tests/r5/` | Isolated checked launcher, tool lock, host/image/QEMU/report/evidence checks. |

The proposed public restricted-C symbols are
`be_r5_import_r4_complete`, `be_r5_handle_exit`,
`be_r5_prepare_pending`, `be_r5_publish_target`, and `be_r5_fail`.
The assembly-only symbols are `be_r5_trap_vector`,
`be_r5_switch_tail`, `be_r5_management_fixture`, and
`be_r5_protected_fixture`. Exact function signatures, object layouts beyond
the unchanged R4 frame, and linker details are implementation work and require
the separate authorization.

The publication split is mandatory: C never executes with guest-restored
GPRs. Assembly saves the source frame and invokes C with monitor state; C
checks and publishes active state only after target preparation; then a
no-call assembly tail loads final GPRs and executes `SRET`. Any trap after
publication and before `SRET` is terminal.

## Planned evidence and separation from R6

The planned R5 evidence schema is `be-r5-checked-switch-v1`. Its isolated,
checked command surface is deliberately prospective:

```sh
./tests/r5/run-make.sh r5-toolcheck
./tests/r5/run-make.sh r5-host-test
./tests/r5/run-make.sh r5-image
./tests/r5/run-make.sh r5-image-check
./tests/r5/run-make.sh r5-qemu
./tests/r5/run-make.sh r5-report
./tests/r5/run-make.sh r5-evidence
./tests/r5/run-make.sh r5-check
./be r5-check
./be r5-evidence
```

All commands, the launcher, the lock, the wrapper entries, source files,
tests, artifacts, and evidence are **NOT IMPLEMENTED / NOT RUN** until the
separate implementation authorization.

If authorized, the isolated launcher and tool lock must bind every normative
tool to its absolute command, resolved path, version, SHA-256, and owning
package; reject hostile Make, shell, compiler, linker, QEMU, Node, and
forged-success controls; and run deterministic GCC and Clang host tests.
Image semantic checks must establish the frozen fixture slots, immutable
roots, the accepted initial R3/R4 management installation, then the ordered
two R5 cross-switch HGATP writes/fences/readbacks, publication split, and
absence of an R6 path. GCC/GNU-ld and Clang/lld need semantic parity, not byte
equality.

Three QEMU runs per compiler must retain exact ordered markers and traces for
the in-image R4 prelude, both R5 cross-switch HGATP writes, fences, and
readbacks after the initial accepted management installation, and exactly
three VS entries: initial management, protected, and restored management.
They must retain the management expected load fault, both protected expected
faults, all three same-domain fault resumes, the two cross-domain switches,
the final restored event, and allowlisted shutdown. Tests must establish state
separation across both saved pages and frames. Reports, manifests, and
SHA-256 checks must reject tampering, stale artifacts, and forged success.

R5 host/unit checks cover only its phase, binding, root, readback, frame, and
publication invariants, including terminal behavior for partial transitions.
R6 retains compiled broad adversarial fixtures for malformed images,
partial-publication variants, wrong bindings, skipped fences, and unexpected
events. R5 must not claim execution of a skipped-fence fixture.

Semantic image and QEMU evidence would not be an R7 exact-byte proof or a
universal timing theorem.

## Claims, trust, exclusions, and review gate

If separately authorized, implemented, and validated, R5 could support only a
QEMU-only statement for this exact pinned one-hart scenario. It would trust
pinned OpenSBI, GCC, Clang, GNU ld, lld, QEMU, the assembler/disassembler, and
inspected-to-executed assembly correspondence.

It would not claim hardware or K3 evidence; formal proof or refinement;
arbitrary-guest isolation; Linux, service, guest-SBI, device, DMA, interrupt,
timer, multicore, policy, CHERI, or TE behavior; R6 or R7 completion;
publication; or release. The open generated-asset reproducibility finding
remains open. Hardware and proof are `NOT RUN`.

Before accepting an exact plan commit, the responsible human must verify:

1. the commit contains this plan without a self-referential plan SHA;
2. R4 is named only at its accepted exact target and the `87b136bc...`
   follow-up is not represented as implementation;
3. the scope is exactly management-to-protected-to-management in the fixed
   one-hart QEMU/OpenSBI profile;
4. all fixture PCs, values, faults, event arguments, frame constraints,
   binding values, and terminal SRST treatment are frozen;
5. the phase/error/pending/publication and exact ordering rules prohibit
   fallback, target execution before publication, and guest-selected context;
6. C/assembly publication separation and no-call final restore are explicit;
7. R5 evidence is distinguished from R6 adversarial fixtures and R7 proof;
8. all planned commands remain marked NOT IMPLEMENTED / NOT RUN; and
9. acceptance records no implementation authorization.

Only after that exact-plan acceptance may the responsible human issue a
separate explicit implementation authorization. Until then R5 remains
defined/gated, not authorized, and not started; R6 and R7 remain gated.
