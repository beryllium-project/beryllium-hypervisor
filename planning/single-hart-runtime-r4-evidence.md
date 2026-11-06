<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R4 trap-and-context evidence

## Status and evidence boundary

This is an implementation and evidence record, **not** the decision record.
The responsible human separately authorized R4 on 2026-07-29 with the
verbatim instruction:

```text
proceed to implement R4
```

The responsible human then accepted exact R4 target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29. Its implementation
parent is `6e5c55c59e94bbaba136269c784db28ec1b53f54`; packet follow-up
`ec7be2f146a851e7608e77eb2875076e66aab2e6` is decision support, not accepted
implementation. The bounded R5 plan was later separately accepted at exact
commit `fecae6b62a507bdbb93d211262197a31f5422316` on 2026-07-30, R5
implementation was separately authorized under that accepted plan, and exact
R5 implementation target `165f4d001a2b59b582b397bdea79ec4826168fdb` was
separately accepted on 2026-07-30. R6 and every later successor remain not
authorized and not started; push, tag, publication, and release remain
blocked. Therefore:

The VitePress generated-asset byte-reproducibility finding remains open and
unresolved. It does not change this exact acceptance or create a hardware,
proof, release, or successor-work claim.

```text
r4_authorization=authorized
r4_implementation=implemented
r4_acceptance=accepted
r4_accepted_commit=0783dfc6557453fbac0da93a5364f2e6e2cb1f52
r4_accepted_at=2026-07-29
r4_review_packet_commit=ec7be2f146a851e7608e77eb2875076e66aab2e6
r5_plan_status=accepted-2026-07-30
r5_accepted_plan_commit=fecae6b62a507bdbb93d211262197a31f5422316
r5_implementation_authorization=authorized
r5_acceptance=accepted-2026-07-30
r5_accepted_commit=165f4d001a2b59b582b397bdea79ec4826168fdb
r6_authorization=not-authorized
publication=blocked
```

This does not alter the accepted R3 identity:
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` remains the exact
responsible-human accepted R3 boot-and-first-entry target.  R4 evidence is generated from its current source inventory and must not be
presented as accepted implementation merely because a later source state
contains the target. The bounded R5 plan was later separately accepted, its
implementation separately authorized, and exact R5 target
`165f4d001a2b59b582b397bdea79ec4826168fdb` separately accepted; R6 and every
later package remain separately authorization-gated.

## Exact bounded behavior

R4 imports only the exact R3 `ENTRY_ARMED` management binding and performs one
same-management sequence:

```text
exact accepted R3 ENTRY_ARMED import
  -> expected management denied protected-private load
  -> full-frame same-management resume at 0x40010018
  -> exact management private VS ecall
  -> full-frame same-management resume at 0x40010034
  -> management loop timeout
```

`include/be/r4.h` fixes a 320-byte, eight-byte-aligned monitor-owned frame:
31 GPR slots for `x1` through `x31`, `vstvec`, `vsepc`, `vscause`, `vstval`,
`scause`, `sepc`, `stval`, `htval`, and a required-zero reserved word.  The
R4 state machine has exactly these one-way states:

```text
EMPTY -> EXPECT_FAULT -> EXPECT_EVENT -> COMPLETE
                  \             \            \
                   ------------> FAILED <------
```

The first error is sticky.  Failure clears retained binding/configuration
authority, yields only the terminal decision, and authorizes neither a frame
restore nor guest entry.

The real management fixture first stores and reads private value `17`.  Its
load from protected-private GPA/GVA `0x40001000` faults at PC `0x40010014`
with `scause=21`.  QEMU supplies `htval=0x10000400`; R4 permits the ratified
shifted-HTVAL treatment by reconstructing the expected GPA when HTVAL is
nonzero, while also permitting the architecture-defined zero-HTVAL case.  The
validated fault advances only `sepc` to `0x40010018` and restores the complete
frame under the unchanged management HGATP.

The resumed management fixture writes and reads shared value `34`, then
executes the exact private VS ecall at PC `0x40010030` with `scause=10`,
`a7=1`, `a6=0`, `a0=17`, and `a1=34`.  That event has zero `stval` and
`htval`; its same-management full restore advances only `sepc` to
`0x40010034`, the fixed management loop.  The protected fixture is linked but
is not entered.

## Frame, CSR, and root boundary

The direct `stvec` vector begins by exchanging the guest stack with trusted
storage (`csrrw sp, sscratch, sp`) before any stack access.  It saves the
complete frame into the management saved-state page, validates the VS-origin
condition, calls the restricted-C transaction, and restores only after a
successful same-management result.  The image checks require every GPR and
all eight defined trap/VS CSRs at their fixed frame offsets.

The following table is the exact bounded frame/restore classification.  `S`
means saved and restored from the R4 frame; it is not a claim to save every
architectural state element.

| Treatment | Exact bounded set | R4 handling |
| --- | --- | --- |
| **S: GPRs** | `x1`–`x31` | Direct vector saves and same-management restore reloads every slot. |
| **S: VS/trap metadata** | `vstvec`, `vsepc`, `vscause`, `vstval`, `scause`, `sepc`, `stval`, `htval` | Saved exactly; only successful C handling advances `sepc` by four. |
| **R: reset then verify** | `sstatus`, `stvec`, `sscratch`, `sie`, `senvcfg`, `scounteren`, `hstatus`, `hedeleg`, `hideleg`, `hie`, `hvip`, `hcounteren`, `htimedelta`, `henvcfg`, `hgeie`, `vsstatus`, `vsie`, `vsscratch`, `vsip`, `vsatp` | Reset before restore and read back before frame restoration. `sstatus`, `vsstatus`, and `hstatus` use their specified writable-control masks, so WARL non-control bits are not falsely required to be zero. |
| **S: reset before frame restore** | `sepc`, `scause`, `stval`, `htval`, `vstvec`, `vsepc`, `vscause`, `vstval` | Cleared as part of the reset discipline, then restored only from the validated S frame. |
| **Constant or retained and checked** | HS `satp=Bare`, management `hgatp` | HS stage 1 remains Bare and is verified. Management HGATP is never in the frame, reset, or written after initial R3 entry, and is read back as the exact management value before return. No post-initial `HFENCE.GVMA` is executed. |
| **Denied by the fixed profile** | `sip`, `hip`, `hgeip` | No enabled interrupt source or delegation exposes this read-only pending state. R4 does not claim to dynamically validate these fields. |
| **Terminal observations** | interrupt bit, unexpected cause/PC/GVA/GPA, bad active binding/hart/HGATP, invalid phase, nonzero reserved word, bad backing observations, malformed event arguments | Any invalid observation enters sticky terminal failure with no recovery or alternate domain path. |
| **Excluded** | `htinst`, all other unlisted CSR/register state, root selection, pending binding, protected state | They are not R4 frame authority. Read-only or otherwise unowned state is not invented as per-domain saved state, and R4 does not implement R5 switching. |

The direct vector uses the trusted-stack swap, not a guest stack, before
calling C.  It verifies reset controls before restoring the S set and verifies
the unchanged management HGATP immediately before `sret`.  The static checks
reject a trap-body HGATP write or `HFENCE.GVMA`; the QEMU traces independently
reject either instruction after the initial R3 entry.

## Components and evidence

- `include/be/r4.h` defines the exact ABI, fixed PCs/values, phases, error
  classes, observations, results, and transactional public C contract.
- `virt/be/r4.c` imports only exact accepted R3 state, validates the two
  observations, advances the saved PC only on success, and makes failure
  sticky.
- `arch/riscv/be/r4-entry.S`, `r4-runtime.c`, `r4-trap.S`, `r4-guest.S`,
  `r4-platform.h`, and `r4-beryllium.lds` provide the explicit RISC-V
  entry/platform/linker boundary.
- `tests/r4/r4-check.c` exercises ten host scenarios and 1,283 assertions
  with both GCC and Clang.
- `tests/r4/check-image.mjs` inspects each linked image for the direct vector,
  full frame, trusted-stack transition, CSR treatment, fixed guest PCs, W^X,
  no protected entry, and no hidden R5 path.
- `tests/r4/check-image-parity.mjs` requires GCC/Clang semantic parity.  ELF
  bytes, hashes, and code/data sizes are intentionally not required to match.
- `tests/r4/check-qemu-artifacts.mjs`, its integrity negative test, and
  `tests/r4/test-report-rejection.mjs` reject missing, altered, stale, or
  semantically incomplete evidence.

The deterministic report is
`build/r4/reports/trap-context.json`, schema
`be-r4-trap-context-v1`.  It records source hashes, tool-lock identity,
image semantic records and object hashes, two three-run QEMU summaries, and
the explicit acceptance/publication/proof/hardware fields. Evidence
retention copies the report and all 12 console/trace logs to
`build/r4/evidence/`, records the two manifests and claim ledger, and
rechecks SHA-256 integrity.

The checked launcher is the normative interface when Make controls are not
already trusted.  It admits one allowlisted target, rejects external Make,
shell, compiler, loader, QEMU, and Node controls, constructs a minimal
environment, and invokes the locked Makefile.  That Makefile independently
repeats parse-time hostile-control checks and validates
`tests/r4/tool-lock.conf`; every normative executable has a locked absolute
path, resolved path, version, SHA-256, and owning package.

## Reproducible commands

Run the checked R4 targets from the repository root:

```sh
./tests/r4/run-make.sh r4-toolcheck
./tests/r4/run-make.sh r4-host-test
./tests/r4/run-make.sh r4-image
./tests/r4/run-make.sh r4-image-check
./tests/r4/run-make.sh r4-qemu
./tests/r4/run-make.sh r4-report
./tests/r4/run-make.sh r4-evidence
./tests/r4/run-make.sh r4-check
```

The corresponding stable root-wrapper commands are:

```sh
./be r4-check
./be r4-evidence
```

`r4-host-test` requires the GCC and Clang result streams to match and reports
exactly ten scenarios and 1,283 assertions.  `r4-image-check` requires the
same checked semantics from GCC/GNU-ld and Clang/lld, not byte equality.
`r4-qemu` retains three expected-timeout runs for each compiler: six bounded
QEMU runs total.  Each run must show ordered R3 setup, R4 import, the denied
load metadata, VS resume at `0x40010018`, private-event metadata, and VS
resume at `0x40010034`; it must not show terminal failure, protected entry,
guest SBI, a post-entry HGATP write, or a post-entry fence.

## Claims and exclusions

The evidence supports only this bounded QEMU-only functional statement:

> In the fixed single-hart QEMU profile, GCC and Clang images import the
> accepted R3 management state, save a fixed complete R4 frame for each of two
> management exits, validate the exact denied protected-private load and
> private event, and restore that same management context at the two fixed
> post-instruction PCs without a post-entry HGATP write or HFENCE.

It does **not** support any of the following:

- protected VS entry, domain switching, or any R5 behavior;
- a shared-read-only denial test;
- R6 adversarial-image completion;
- R7 exact-byte proof, formal verification, or source-to-binary proof;
- hardware or K3 validation;
- Linux, service, device, DMA, interrupt, timer, multicore, or guest-SBI
  behavior;
- a Model 0.1/0.2 proof or C-refinement transfer to R4; or
- a Helium claim or proof transfer to Beryllium.

The tested QEMU behavior is functional evidence only.  It does not establish
arbitrary-guest isolation, complete trap handling, production readiness, or
public-release approval.  Publication remains blocked pending the separate
responsible-human process.
