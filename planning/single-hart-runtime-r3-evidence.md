<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R3 boot and first-entry evidence

## Status, authorization, and acceptance boundary

Responsible-human instruction on 2026-07-29 was `proceed with R3`. The
accepted single-hart plan's separate R3 authorization gate is therefore
satisfied. This authorization is distinct from implementation completion and
from responsible-human acceptance. The later responsible-human decision on
2026-07-29 explicitly accepted the exact implementation target with this
instruction, preserved verbatim:

```text
accept  6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
```

The bounded R3 boot-and-first-entry implementation content is complete:

```text
pinned OpenSBI S/HS handoff
  -> exact image / SBI validation
  -> accepted R1 copy / validate / seal / derive
  -> R2 build in actual linker-reserved physical pools
  -> independent R2 re-walk
  -> bounded HS/VS reset and readback
  -> management binding preparation
  -> HGATP write
  -> local HFENCE.GVMA x0,x0
  -> HGATP readback and active publication
  -> set and inspect sstatus.SPP=1 at the final entry boundary
  -> SRET
  -> QEMU V=1 at the first management instruction GPA 0x40010000
```

`./tests/r3/run-make.sh r3-check` and `./be r3-check` pass with strict
GCC/GNU-ld and Clang/lld images, 128 host scenarios / 704 assertions per host
compiler, semantic ELF checks, and three traced QEMU runs per image. The
checked launcher rejects hostile external GNU Make controls before starting
the pinned Make executable while preserving bounded job-count and
output-synchronization flags.

**R3 is responsible-human accepted only at exact implementation target
`6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`.** Its immediate parent is
`86a4cd38bfc9d47794cba2d26c5b7dc777c5d835`; the whole-R3 base is
`3024e79867911cbdd47085832b7a64f713970f65`. Packet follow-up
`fcc0f267a1f59241f872c0a1d2a371a95a58cba6` is decision support, not
accepted implementation. Default `tests/r3/check-acceptance.sh` status mode
reports:

```text
r3_authorization=authorized
r3_authorized_at=2026-07-29
r3_implementation=complete
r3_implementation_record=complete-accepted-content
r3_acceptance=accepted
r3_accepted_commit=6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
r3_accepted_at=2026-07-29
r3_accepted_mechanism_match=yes
r3_review_target=6fb65b28592d5ef225d1ddbcd0ec3a509a98096d
r3_review_packet_commit=fcc0f267a1f59241f872c0a1d2a371a95a58cba6
r4_authorization=not-authorized
r3_publication_scope=blocked
r3_hardware_validation=NOT-RUN
```

The R4 field is the preserved historical R3-decision status, not current
project status. The responsible human subsequently accepted exact R4 target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29. Its implementation
parent is `6e5c55c59e94bbaba136269c784db28ec1b53f54`; decision-support packet
follow-up `ec7be2f146a851e7608e77eb2875076e66aab2e6` is not accepted
implementation. The bounded R5 plan was later accepted, R5 implementation
was separately authorized, and exact R5 target
`165f4d001a2b59b582b397bdea79ec4826168fdb` was separately accepted on
2026-07-30. R6 and every later successor remain gated, not authorized, and
not started; publication remains blocked.

`tests/r3/check-acceptance.sh --require` succeeds only when accepted status
and accepted-content match are both present. Drift exits 1; invalid arguments
exit 2.

The accepted-content set is derived from the R3 Makefile source/header/test
graph: 23 direct runtime/header/linker inputs, the frozen platform lock, and
14 direct tool/image/QEMU/negative-test inputs, for 38 immutable paths. Those
paths are byte-and-mode compared with the accepted target. Nine mixed files
(`tests/r1/check-acceptance.sh`, `tests/r3/Makefile`, report/evidence
generators and checker, report-negative tests, `be`, `scripts/check-be.sh`,
and `tests/r3/check-acceptance.sh`) use
exact full-file approved-delta digests tied to both target and current bytes;
there is no broad regex or unchecked technical region. Focused tests reject
immutable drift, mixed-file technical drift, acceptance-checker logic drift,
wrong SHA/date, review-required reversion, packet SHA substitution, false R4
authorization, and publication relaxation while the exact allowed acceptance
delta passes.

The complete immutable path set is:

```text
arch/riscv/be/beryllium.lds
arch/riscv/be/entry.S
arch/riscv/be/freestanding.c
arch/riscv/be/guest.S
arch/riscv/be/platform.c
arch/riscv/be/privileged.S
arch/riscv/be/r0-layout.h
arch/riscv/be/r0-platform.conf
arch/riscv/be/r0-registers.h
arch/riscv/be/r0-sbi.h
arch/riscv/be/r3-platform.h
arch/riscv/be/runtime.c
arch/riscv/be/sv39x4.c
include/be/manifest.h
include/be/r0-config.h
include/be/r1-config.h
include/be/r2.h
include/be/r3.h
include/be/state.h
include/be/types.h
tests/r0/check-tools.sh
tests/r3/check-image-parity.mjs
tests/r3/check-image.mjs
tests/r3/check-qemu-artifacts.mjs
tests/r3/check-tools.sh
tests/r3/make-control.mjs
tests/r3/r3-check.c
tests/r3/run-make.sh
tests/r3/run-qemu.sh
tests/r3/test-qemu-artifact-integrity.mjs
tests/r3/test-tool-binding.mjs
tests/r3/tool-lock.conf
tests/r3/tool-lock.mjs
tests/r3/verify-tool-lock.mjs
virt/be/manifest.c
virt/be/r1-config.c
virt/be/r3.c
virt/be/state.c
```

Planning Markdown, generated `docs/html/**`, and
`pathfinder/tests/check-docs-render.mjs` are documentation/rendering inputs,
not R3 mechanism-match inputs. They remain checked by documentation gates and
included in dynamic evidence source identity where applicable, but cannot
make changed technical R3 content appear accepted.

R3 acceptance does not itself authorize R4, tagging, pushing, public release,
publication-gate changes, or hardware claims.

### Self-reference-safe repository identity

The implementation report separates five identities instead of treating one
commit field as all of them:

- `implementationBaseCommit` is fixed at
  `3024e79867911cbdd47085832b7a64f713970f65`, the clean roadmap/base commit
  immediately before the R3 content;
- `repositoryHeadAtGeneration` is obtained from `git rev-parse HEAD` whenever
  evidence is generated and is independently recomputed by the checker;
- source identity is the exact path/content hash inventory plus
  `sourceStateAtGeneration` and the complete
  `repositoryStatusAtGeneration`, so both dirty pre-commit candidates and
  clean successor commits are described truthfully; and
- `reviewTarget` is the accepted exact implementation target
  `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`; and
- the packet follow-up
  `fcc0f267a1f59241f872c0a1d2a371a95a58cba6` remains a separate
  decision-support identity.

The checker requires the generation HEAD to equal the current HEAD and to be
the fixed base or any descendant of it. It independently recomputes the base
relationship, full repository status, every source hash, and the identity
again after semantic checking. A generation HEAD is evidence context, not the
accepted implementation target merely because it contains later status work.

## Claim boundary

Supported by this implementation content and evidence:

- bounded privileged R3 source is present;
- GCC/GNU-ld and Clang/lld link static Beryllium ELF images at
  `0x80200000`;
- OpenSBI enters hart zero in S/HS mode and its `a1` value is recorded but
  never dereferenced;
- the image validates the exact linker layout, required SBI Base/DBCN/SRST
  behavior, accepted R1 state, physical-pool R2 output, independent R2
  re-walk, bounded HS/VS state, and initial management binding;
- management `HGATP=0x8000000000080214` is written, followed by local
  `HFENCE.GVMA x0,x0`, read back exactly, and only then published;
- all six QEMU runs emit the required ordered pre-entry DBCN markers, execute
  the exact R3 `SPP=1 -> SRET` transition, show SPP set in that SRET CPU
  block, and only afterward show `V=1` at `pc=0x40010000`; and
- the expected bounded timeout occurs only after that traced VS instruction.

The VS conclusion is deliberately composite: static image inspection and the
executed exact R3 wrapper trace establish `sstatus.SPP=1` immediately before
`SRET`; trace ordering requires that SRET block before the management block
where QEMU reports `V=1`. QEMU does not emit a separate magical `VS`
privilege label.

Explicitly not implemented or not run:

- no trap classification, trap frame, context save/restore, or private event
  protocol;
- no root switching, protected VS entry, second-domain execution, or
  state-separation test;
- no private/shared access test and no guest-page-fault evidence;
- no skipped-fence runtime fixture;
- no R7 exact-byte proof or source-to-binary proof;
- no Model 0.2-to-C/runtime refinement;
- no Linux, service, device, DMA, interrupt, timer, multicore, policy, or
  guest-visible SBI behavior;
- no K3 or other hardware execution; and
- no formal-verification, arbitrary-guest-isolation, full-runtime, or
  production claim.

Helium evidence remains separate and does not validate R3. Public release
remains blocked.

## Component and file tour

### R3 mechanism contract

- `include/be/r3.h`
  - one-way R3 phases from `EMPTY` through `ENTRY_ARMED` or terminal
    `FAILED`;
  - stable error classes for handoff, layout, SBI discovery, R1/R2 state,
    HS state, binding, publication, every frozen DBCN result, and SRST
    failures;
  - exact image-layout, boot-contract, HS-state, binding, and DBCN-progress
    structures;
  - exact management/protected HGATP, initial PC/stack, diagnostic range,
    status masks, and retry cap; and
  - public kernel-doc contracts for every R3 mechanism operation.

- `virt/be/r3.c`
  - validates every linker boundary against the accepted R0 physical map;
  - independently rechecks accepted R1 derived/sealed state;
  - validates both R2 roots, exact HGATP values, domain/root/VMID bindings,
    and all six independently walked leaves;
  - validates the complete bounded HS/VS CSR readback;
  - prepares, fences, publishes, and arms only the exact management binding;
  - makes failure sticky and clears pending/active binding output; and
  - handles DBCN partial, zero, malformed, error, range, and retry-exhaustion
    paths without issuing an SBI call itself.

### RISC-V architecture boundary

- `arch/riscv/be/entry.S`
  - exact `be_reset` entry at `0x80200000`;
  - preserves OpenSBI `a0`/`a1`, zeros the linked BSS, and starts on trusted
    management stack top `0x80227000`;
  - forwards `a1` only as an opaque scalar; and
  - halts if the non-returning C runtime unexpectedly returns.

- `arch/riscv/be/privileged.S`
  - sole CSR, SBI `ecall`, `HFENCE.GVMA`, `SRET`, `WFI`, and trap-sink
    implementation;
  - keeps the global build at the frozen
    `rv64imac_zicsr_zifencei` while using local `.option arch,+h` only for
    explicit H instructions;
  - truthfully emits an ELF H architecture attribute for this one object;
  - resets and reads back every bounded HS/VS CSR;
  - implements exact
    `csrw hgatp -> hfence.gvma x0,x0 -> csrr hgatp` order;
  - writes HS `sepc`, retains the trusted stack in `sscratch`, initializes
    every guest GPR deterministically, sets `sstatus.SPP=1` only at the final
    entry boundary, clears the scratch GPR again, and executes `sret`; and
  - provides a minimal stack-free unexpected-trap sink that disables bounded
    interrupt injection and halts without implementing R4.

- `arch/riscv/be/platform.c`
  - SBI Base version and extension probes;
  - DBCN writes only after copying trusted bytes into
    `[0x8020f000,0x80210000)`;
  - exact partial/zero progress handling through the R3 mechanism; and
  - SRST shutdown with no legacy fallback.

- `arch/riscv/be/runtime.c`
  - constructs the runtime view of linker symbols;
  - executes the accepted R1 flow unchanged;
  - binds R2 to the actual `__be_root_*` linker pools;
  - resets and validates architecture state;
  - prepares/publishes/arms the exact initial binding;
  - emits seven ordered DBCN markers; and
  - enters management VS and cannot return successfully.

- `arch/riscv/be/freestanding.c`
  - bounded `memcpy`/`memset` implementations required by compiler-lowered
    fixed-size structure operations; no allocator or broader libc.

- `arch/riscv/be/guest.S`
  - one-page R-X management infinite loop at physical `0x80232000`, mapped at
    GPA `0x40010000`;
  - separate one-page R-X protected stub at physical `0x80233000`, linked but
    never entered in R3.

- `arch/riscv/be/beryllium.lds`
  - executable linker script derived from
    `arch/riscv/be/beryllium.lds.plan`;
  - separate R-X monitor text, read-only fixed input/rodata, RW monitor data,
    RW reserved physical extents, and separate R-X guest PHDRs;
  - exact root pools, trusted stacks, saved-state pages, private/shared pages,
    guards through gaps, and guest pages; and
  - more than twenty load-bearing `ASSERT` checks for security-sensitive
    boundaries and alignment.

### Test and evidence package

`tests/r3/` is self-contained so accepted R1/R2 build and test inputs remain
unchanged:

- `r3-check.c`: positive flow plus adversarial boot/layout, R1/R2, HS state,
  binding, publication, terminal-failure, and DBCN cases;
- `tool-lock.conf`, `tool-lock.mjs`, `verify-tool-lock.mjs`, and
  `check-tools.sh`: one fail-closed executable manifest consumed by Make,
  shell execution, report generation, evidence generation, and independent
  checking;
- `make-control.mjs` and `run-make.sh`: the checked Make boundary; the
  launcher captures external `MAKEFLAGS`, `GNUMAKEFLAGS`, `MAKEFILES`,
  `MFLAGS`, and `MAKEOVERRIDES`, rejects graph/execution controls, clears the
  caller environment, preserves only safe scheduling/output flags, and starts
  the manifest-bound `/usr/bin/make`; externally supplied internal `BE_R3_*`
  controls are rejected even when empty or zero, and the Makefile invokes the
  same checker at parse time whenever it is loaded;
- `test-tool-binding.mjs`: real subprocess probes for direct and wrapper
  dry-run, touch, question, eval, timestamp, alternate-file/include,
  recipe-prefix, shell/tool, manifest-tampering, and PATH-shadow rejection,
  plus safe parallel/output synchronization;
- `check-image.mjs`: ELF entry, symbols, sections, PHDR W^X, no
  dynamic/unresolved/relocated state, H attributes, guest pages, linker
  assertions, HGATP ordering, and exact `SPP=1 -> SRET` wrapper ordering;
- `check-image-parity.mjs`: GCC/Clang semantic parity without claiming byte
  equality;
- `run-qemu.sh`: exact R0 QEMU command plus bounded evidence-only
  `in_asm,cpu` tracing over the two entry wrappers and first management
  instruction, three runs per compiler, ordered markers, SPP/SRET state,
  `V=1` at the management PC, and expected timeout;
- `check-qemu-artifacts.mjs`: exact seven-file per-compiler inventory,
  nonempty/bounded logs, semantic trace and console checks, and recomputed
  per-run hashes;
- `test-qemu-artifact-integrity.mjs`: focused missing, tampered, semantic-
  alteration, and extra-file rejection tests;
- `generate-report.mjs` / `check-report.mjs`: deterministic
  `be-r3-boot-entry-v1` report and independently grounded exact-schema
  semantic checker, including the fixed implementation base, dynamic
  generation HEAD, base ancestry, exact repository status, source hashes,
  exact accepted review target, and distinct packet follow-up;
- `test-report-rejection.mjs`: forged base, generation HEAD,
  ancestry/state, acceptance/SHA/date/content-match/packet/R4/publication/
  review-target, source, QEMU, firmware, artifact, and schema rejection
  tests;
- `check-acceptance.sh`: successful default status and `--require` modes only
  while exact accepted content matches; and
- `test-acceptance-content.mjs`: focused immutable, mixed-delta, authority,
  packet-substitution, R4, publication, and invalid-argument negatives; and
- `generate-evidence.sh`: retained source, tool, firmware, object, ELF,
  binary, map, disassembly, config, exact QEMU manifest, report, and claim
  identities.

## Exact boot and first-entry sequence

1. OpenSBI jumps to `be_reset` at `0x80200000`.
2. `entry.S` records `a0` and `a1`, zeros only
   `[__be_bss_start,__be_bss_end)`, and sets `sp=0x80227000`.
3. SBI Base reports specification version 3.0 for the pinned firmware.
4. SBI Base probes DBCN and SRST and both return exact availability value 1.
5. `be_r3_validate_boot()` checks hart zero, every linker boundary, the
   diagnostic page, root alignment, guest pages, and trap-sink placement.
6. The runtime calls the unchanged accepted R1 copy, proposal copy,
   validation, sealing, and derivation APIs.
7. R3 independently requires R1 phase `DERIVED`, sealed configuration identity
   `0x771e1e75110201ac`, and valid canonical/derived checks.
8. R2 builds into physical pools:
   - management `[0x80214000,0x8021c000)`;
   - protected `[0x8021c000,0x80224000)`.
9. `be_r2_walk_and_check()` independently enumerates all six leaves.
10. R3 requires:
    - management `HGATP=0x8000000000080214`;
    - protected `HGATP=0x800000000008021c`;
    - VMID zero for both roots; and
    - exact private, shared, and R-X code leaves.
11. `be_r3_arch_reset_state()` resets/fences and reads back all bounded HS/VS
    state.
12. R3 prepares the unpublished management binding.
13. Assembly writes management HGATP, executes local
    `HFENCE.GVMA x0,x0`, and reads HGATP back.
14. C publishes the binding only after exact readback and the assembly fence
    contract.
15. The entry wrapper writes HS `sepc=0x40010000`,
    `sscratch=0x80227000`, sets guest `sp=0x40001000`, zeros every other
    guest GPR, then executes the exact final sequence
    `li t0,0x100 -> csrs sstatus,t0 -> li t0,0 -> sret`.
16. QEMU tracing observes the unique exact R3 SPP-setting/SRET sequence, its
    SPP CPU state, and then the later virtual-mode management block:

    ```text
    mstatus  0000000a00000180
    0x8020....:  10200073  sret

    0x40010000:  0000006f  j 0x40010000
     V      =   1
     pc       0000000040010000
    ```

    The `mstatus` value contains the `sstatus.SPP` bit. The architecture
    semantics inspected in the wrapper distinguish VS from VU; `V=1` confirms
    virtual execution at the management PC.
17. With R4 intentionally absent, the guest loops and the harness accepts
    only the expected bounded timeout after that trace evidence.

## Initial architectural constants

| Item | Exact R3 value |
| --- | --- |
| OpenSBI next-stage entry | `0x80200000` |
| Accepted hart | `a0=0` |
| Firmware pointer | `a1` recorded, never dereferenced |
| HS `satp` | Bare (`0`) |
| VS `vsatp` | Bare (`0`) |
| Post-reset HS `sstatus.SPP` | clear (`0`) |
| Final entry `sstatus.SPP` | set (`1`) immediately before `sret` |
| `hstatus` required set | `SPV`, `SPVP`, `VTVM`, `VTW`, `VTSR` |
| `hstatus` required clear | `HU`, `VGEIN` |
| Delegation | `hedeleg=0`, `hideleg=0` |
| Interrupt paths | `sie=0`, `hie=0`, `hvip=0`, `vsie=0`, `vsip=0` |
| Counter paths | `scounteren=0`, `hcounteren=0` |
| Environment/time | `senvcfg=0`, `henvcfg=0`, `htimedelta=0` |
| Reset VS CSRs | `vsstatus/vstvec/vsscratch/vsepc/vscause/vstval=0` |
| Management HGATP | `0x8000000000080214` |
| Protected HGATP (built/re-walked, not entered) | `0x800000000008021c` |
| Initial HS SRET target | `sepc=0x40010000` |
| Reset VS saved PC | `vsepc=0` |
| Initial guest stack | `sp=0x40001000` |
| Initial trusted stack | `0x80227000` |
| Other guest GPRs | zero |
| Management saved-state page | `0x8022b000` |
| DBCN physical page | `[0x8020f000,0x80210000)` |
| DBCN retry bound | 256 calls |

### `sepc` / `vsepc` terminology cut point

The accepted plan and R0 matrix use `vsepc` when describing saved per-domain
VS state. At the R3 initial-entry boundary, however, the architectural
HS-to-VS `sret` target is HS `sepc`. R3 therefore:

- resets and verifies `vsepc=0` as separate VS state;
- writes `sepc=0x40010000`, then sets `sstatus.SPP=1` at the final transition
  boundary before the initial `sret`; and
- does not silently rewrite the accepted saved-state matrix.

R4 must define how later traps save and restore both the HS trap `sepc` and
the complete per-domain context. R3 does not begin that work.

## Failure behavior

Every invalid pre-entry path is terminal:

- wrong entry, hart, linker extent, alignment, SBI version/probe, R1 phase or
  integrity, R2 state/root/domain/VMID/HGATP/leaf, CSR readback, binding field,
  fence flag, HGATP readback, or publication state enters `FAILED`;
- pending and active bindings are cleared on mechanism failure;
- no R3 API leaves `FAILED`;
- DBCN uses only the diagnostic physical page and a fixed 256-call bound;
- successful zero progress consumes one bounded iteration without advancing;
- partial progress advances only by the returned count;
- oversized progress, undefined errors, range overflow, and all frozen SBI
  errors are distinct terminal results;
- failure may attempt bounded DBCN diagnostics and then SRST;
- no legacy console, legacy shutdown, fallback, retry boot, or recovery path
  exists; and
- if SRST returns or an unexpected VS trap occurs, assembly disables bounded
  interrupt paths and halts without using the guest-valued stack.

SBI response-failure injection is host tested. The pinned OpenSBI positive
run is not misrepresented as firmware error-injection evidence.

## Image and tool evidence

The global target compilation remains:

```text
-march=rv64imac_zicsr_zifencei
-mabi=lp64
-mcmodel=medany
```

Only `privileged.S` enables H locally. Both final ELF attribute sections
include `h1p0`, while F, D, and V remain absent.

Image checks require:

- ELF type `EXEC`, entry `0x80200000`, static linkage;
- no dynamic section, interpreter, unresolved symbols, or relocations;
- exact section/symbol extents and one-page guest sections;
- no writable/executable section or LOAD segment;
- read-only fixed R1 input section;
- exact root/stack/state/private/shared/guest boundaries;
- management and protected guest pages in separate R-X PHDRs;
- exact HGATP/fence/readback instruction order;
- HS `sepc` entry wrapper, complete guest GPR initialization, post-reset
  `SPP=0`, and final exact `SPP=1 -> SRET` order;
- reset of the required HS/VS controls; and
- GCC/Clang semantic parity, with compiler-specific byte hashes retained
  separately.

The single retained `be-r3-tool-lock-v1` manifest covers 42 directly executed
roles: GNU Make and Bash; Node.js; host GCC/Clang and the GCC `cc1`,
`collect2`, assembler, and linker paths; cross GCC and its exact subordinate
paths; cross `as`, `ld`, `nm`, `objcopy`, `objdump`, `readelf`, and `size`;
lld; QEMU; `timeout`; `sha256sum`; RPM and Git; and every shell utility used
by the normative graph. Each entry records the absolute invocation path,
actual resolved executable, exact version output, executable SHA-256, and
owning package. GCC subordinate resolution is independently recomputed.
Make variables that could replace tools, flags, sources, outputs, shell, or
evidence parameters are rejected; shell-level `QEMU`, `TIMEOUT`, `NM`,
`SHA256SUM`, and `NODE` substitutions are rejected. The execution PATH is
sanitized, while all normative tools are invoked by manifest-selected absolute
paths, so PATH shadowing cannot select a different executable.

The pinned major identities include cross GCC 16.1.1, cross GNU binutils
`2.46-1.fc44`, Clang/lld 22.1.8, QEMU 10.2.2, OpenSBI v1.7, and firmware SHA-256
`49bdf7b939bda11321132d1042bf99d7324fb190f1feef423171fed3573f8705`.

## QEMU evidence

Each compiler image runs three times with the exact R0 command:

```sh
qemu-system-riscv64 \
  -machine virt,aia=none \
  -cpu rv64,h=true,f=false,d=false,v=false,zfa=false,sv48=off,sv57=off,\
sstc=false,smstateen=false,svadu=false,debug=false \
  -smp 1 \
  -m 128M \
  -bios default \
  -kernel <beryllium.elf> \
  -nographic \
  -no-reboot
```

Evidence-only tracing adds:

```text
-d in_asm,cpu
-dfilter <install-wrapper-range>,<entry-wrapper-range>,0x40010000+0x4
-D <trace>
```

The symbol-derived GCC and Clang filters are retained separately. They bound
each trace to the HGATP wrapper, final entry wrapper, and first management
instruction; current retained traces are approximately 17 KiB each rather
than unbounded whole-monitor CPU logs.

Every run requires these markers in order:

```text
BE_R3:01 BOOT_VALIDATED
BE_R3:02 R1_DERIVED
BE_R3:03 R2_BUILT_REWALKED
BE_R3:04 HS_VS_STATE_VERIFIED
BE_R3:05 BINDING_PREPARED
BE_R3:06 HGATP_FENCED_PUBLISHED
BE_R3:07 ENTER_MANAGEMENT_VS pc=0x40010000
```

The harness also requires the traced management wrapper opcodes in exact
HGATP-write, fence, readback order. For entry, it selects the unique
`be_r3_arch_enter_management` blocks containing the exact R3 SPP mask/set and
SRET opcodes, requires those blocks to be adjacent, requires SPP in the SRET
CPU state, and requires that SRET block to precede the unique management
instruction block containing both `V=1` and `pc=0x40010000`. Duplicate,
reordered, unrelated, or malformed sequences fail. The checker also rejects
protected entry at `0x40011000` and accepts timeout status 124 only after
those checks. A normal QEMU exit, the final marker alone, or timeout without
the ordered composite VS evidence fails.

Exactly three console and three trace logs plus one summary are required per
compiler. The independent checker rejects missing, extra, empty, oversized,
semantically invalid, or hash-mismatched files. The focused negative test
deletes a required trace, appends to a trace, reorders the management block
ahead of the exact R3 SRET sequence while recomputing the retained trace hash
and size, duplicates the SRET block with recomputed identity, alters a
required console marker, and adds an unexpected file; every case must be
rejected.

## Host adversarial evidence

Both host compilers run 128 scenarios and 704 assertions covering:

- positive end-to-end R3 state progression;
- null, wrong-phase, and sticky terminal behavior;
- wrong handoff entry/hart, SBI version, and DBCN/SRST probe values;
- every image-layout start/end, root alignment, trap-vector range/alignment,
  input/BSS containment, and diagnostic boundary;
- wrong R1 phase and integrity;
- wrong R2 state, management/protected HGATP, root, domain, VMID, and leaf;
- every zero-required HS/VS state field plus `hstatus` and `stvec`, including
  a focused rejection of post-reset `sstatus.SPP=1`;
- wrong management domain/vCPU/root/VMID/HGATP/PC/guest stack/trusted
  stack/saved-state/VSATP/publication field;
- wrong fence completion, readback, pending, active, and entry binding;
- DBCN zero-length completion;
- partial and zero progress;
- below/above/overflowing diagnostic ranges;
- `FAILED`, `NOT_SUPPORTED`, `INVALID_PARAM`, `DENIED`, and
  `INVALID_ADDRESS`;
- undefined error and oversized progress;
- exact 256-call zero-progress exhaustion; and
- DBCN wrong-phase and failed-state stickiness; and
- returned SRST success plus every frozen SRST error and an undefined result.

## Deterministic report and retained artifacts

`build/r3/reports/boot-entry.json` uses schema
`be-r3-boot-entry-v1`. Two independently generated copies must compare
byte-for-byte before retention. The checker rejects missing or extra schema
keys; requires the fixed `implementationBaseCommit`; independently obtains
the current HEAD, verifies that the base is its ancestor or equal, and
compares it with `repositoryHeadAtGeneration`; recomputes the full Git status,
dirty/clean state, exact source path inventory, and every SHA-256 from disk;
requires the exact accepted target/date/content match, exact
`reviewTarget=6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`, and distinct packet commit
`fcc0f267a1f59241f872c0a1d2a371a95a58cba6`; pins the source-controlled
tool-lock digest and
independently recomputes every resolved executable, version, hash, package,
and compiler subordinate path; validates the frozen QEMU command, trace
events, symbol-derived filters, and run count; checks the actual OpenSBI
firmware digest, owning package, version evidence, and traceability;
regenerates image semantics from the real ELF artifacts; validates exactly 12
logs and two summaries; enforces every transition, claim, and non-claim
value; and rechecks repository identity after semantic validation. It does
not compare the report only to another unchecked generated file and does not
infer that the generation HEAD is the review target.

Retained evidence under `build/r3/evidence/` includes:

- `source-state.txt`
- `tool-lock.conf`
- `tool-identities.json`
- `config-firmware.txt`
- `source.sha256`
- `objects.sha256`
- `artifacts.sha256`
- `object-paths.txt`
- `artifact-paths.txt`
- `r1-acceptance.txt`
- `r2-acceptance.txt`
- `r3-acceptance.txt`
- `claim-status.txt`

Regenerable image artifacts include both toolchains' exact object inventory,
ELF, binary, link map, disassembly, section/PHDR report, architecture
attributes, symbols, image semantic report, all 12 QEMU console/trace logs,
both normalized QEMU summaries, and the strict report/check output.

## Commands

Checked targeted commands:

```sh
./tests/r3/run-make.sh r3-toolcheck
./tests/r3/run-make.sh r3-host-test
./tests/r3/run-make.sh r3-image
./tests/r3/run-make.sh r3-image-check
./tests/r3/run-make.sh r3-qemu
./tests/r3/run-make.sh r3-report
./tests/r3/run-make.sh r3-evidence
./tests/r3/run-make.sh r3-check
```

Stable wrapper commands:

```sh
./be r3-check
./be r3-evidence
```

Follow-up acceptance-record checks:

```sh
node tests/r3/test-acceptance-content.mjs
tests/r3/check-acceptance.sh
tests/r3/check-acceptance.sh --require
./scripts/check-be.sh
```

The 2026-07-29 follow-up worktree reran a clean R3 gate and the complete
repository gate successfully. That execution validates acceptance-record/
tooling integration and unchanged accepted technical content; the prior
detached run at `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d` remains the
exact-target validation.

`./be check` composes the existing repository gate, accepted R2 gate, and R3
gate without modifying accepted R1/R2 Makefiles. It routes all three Make
processes, including the root gate that invokes Helium, through the checked
launcher, so hostile Make-control environment does not propagate.

Raw `make -C tests/r3 TARGET` remains an inspectable developer interface.
When `tests/r3/Makefile` is loaded, its first parse-time preflight rejects
dry-run/just-print, touch, question, ignored errors, environment precedence,
symlink-time changes, assume-new/old, include-path changes, eval, recipe
prefix/SHELL changes, builtin-rule removal, graph shuffling, and unsupported
external Make controls. Safe bounded job counts and output synchronization
remain usable.

That Makefile check cannot undo a side effect already performed by GNU Make
while preprocessing `--eval`, and no Makefile can reject an early
`--help`/`--version` exit or an alternate `-f` file that prevents the R3
Makefile from loading. Therefore `run-make.sh` or `./be` is the normative
boundary whenever command-line or environment control is not already trusted.

## Resolved implementation findings

1. **H extension without changing the frozen global `-march`.** Both
   assemblers accept local `.option arch,+h`, but that directive alone did not
   make the final GNU-linked ELF attribute advertise H. The privileged object
   now also carries a truthful H architecture attribute while every global
   compiler command retains the accepted base `cross_march`.
2. **Pinned SBI specification result.** The pinned OpenSBI v1.7 firmware
   reports Runtime SBI Version 3.0. R3 validates exact encoded value
   `0x03000000` and separately probes DBCN/SRST; version alone is not treated
   as extension evidence.
3. **Initial PC terminology.** The initial target is HS `sepc`, while
   `vsepc` is explicitly reset VS state. This evidence records the cut point
   without silently changing the accepted R0 saved-state matrix.
4. **Successful R3 termination.** R3 has no successful shutdown because that
   would require a post-entry event/trap protocol owned by R4. Evidence
   therefore uses ordered DBCN markers plus instruction tracing and accepts
   only a bounded timeout after the first VS instruction.
5. **Compiler parity versus byte equality.** GCC and Clang have identical
   checked semantics and fixed security layout but legitimately different
   code/data sizes and ELF hashes. R3 records both identities and makes no
   byte-equality claim.
6. **VU entry caused by cleared SPP.** Independent review found that the
   original wrapper left `sstatus.SPP=0`, so its VS wording was unsupported.
   The reset check remains SPP-clear, while the final wrapper now sets SPP,
   clears its scratch register, and executes `sret` in an exact inspected
   order. Six bounded QEMU traces also show the SPP bit at the SRET boundary
   and `V=1` at the management PC.
7. **Fail-open QEMU retention.** The original graph targeted summaries and
   wildcard-hashed whatever logs happened to exist. The graph now requires a
   strict validated stamp and exact 12-log/two-summary manifest; independent
   semantic checking and negative deletion/tampering tests run in the gate.
8. **Fail-open report semantics.** The original checker accepted fabricated
   source identities and several asserted evidence fields. The replacement
   uses an exact schema and independently recomputes the fixed implementation
   base relationship, dynamic generation HEAD, repository state, source,
   tool, firmware, image, QEMU, transition, acceptance, claim, and non-claim
   facts. Focused forged-base, forged-HEAD, wrong-state, misleading
   acceptance/SHA/date/content-match/packet/R4/publication/review-target, and
   prior fabricated-report tests must fail.
9. **Fail-open tool substitution and incomplete identities.** One
   source-controlled manifest now drives execution, reporting, retention, and
   independent checking for every normative executable. Absolute command and
   resolved paths, versions, hashes, packages, compiler subordinate paths,
   checked-launcher Make controls, loaded-Makefile overrides, shell
   substitutions, and PATH shadowing are all checked. R3 default status and
   `--require` now succeed only while current accepted-content inputs match
   exact target `6fb65b28592d5ef225d1ddbcd0ec3a509a98096d`.
10. **Fail-open GNU Make execution controls.** `MAKEFLAGS=-n` previously let
    `./be r3-check` exit zero without executing a recipe, and eval is processed
    before recipe-time checks. The wrapper and checked launcher now reject
    hostile `MAKEFLAGS`/`GNUMAKEFLAGS`/`MAKEFILES` before Make starts, while
    the R3 Makefile performs the same check at parse time whenever loaded.
    Real subprocess negatives cover dry-run, touch, question, eval, timestamp,
    graph, shell/tool, PATH, and alternate-file controls; bounded parallel and
    output-sync controls still execute the probe.
11. **Fail-open internal launcher preview.** `BE_R3_MAKE_DRY_RUN=1` previously
    let both `./be r3-check` and `./tests/r3/run-make.sh r3-check` exit zero
    after only a success-shaped `BE_COMMAND` line. The normative launcher no
    longer has a preview mode and rejects all externally supplied internal
    `BE_R3_*` controls, including empty and zero values, before output. The
    documented top-level `BE_DRY_RUN=1 ./be ...` preview now uses a separate
    non-evidence checker path and never enters the normative launcher. Real
    subprocess negatives cover inherited and explicit-environment forms for
    both exact reported commands, while normal launcher and wrapper gates
    still execute validation.
12. **Repository/component publication coupling.** `./be status` now keeps
    Beryllium repository and public release unconditionally blocked under the
    future clean-repository process. The Helium gate appears only in separately
    labeled component fields.
13. **Commit self-reference in implementation evidence.** Treating
    pre-content HEAD as the only valid report commit failed after the content
    was committed, while embedding a future enclosing SHA in its own source
    would be circular. The report now fixes only the pre-R3 comparison base,
    records generation HEAD and repository state dynamically, preserves exact
    content hashes, and keeps the accepted implementation target distinct from
    the packet and later acceptance-record worktree.

## Open finding

VitePress-generated hash-named asset byte reproducibility remains unresolved.
Functional documentation and browser-render gates pass, but this R3 work does
not classify the existing finding as accepted, resolved, or harmless.

## R4 boundary

At the exact R3 decision boundary, R4 was not authorized and had not started.
The responsible human subsequently accepted exact R4 target
`0783dfc6557453fbac0da93a5364f2e6e2cb1f52` on 2026-07-29. Its implementation
parent `6e5c55c59e94bbaba136269c784db28ec1b53f54` and decision-support packet
follow-up `ec7be2f146a851e7608e77eb2875076e66aab2e6` remain distinct from the
accepted implementation. R5 was later separately accepted at exact target
`165f4d001a2b59b582b397bdea79ec4826168fdb` on 2026-07-30; R6 and every later
successor remain gated, not authorized, and not started, and publication
remains blocked. Its scope is limited to:

- an exact trap frame;
- cause/PC/address classification;
- a private VS event protocol;
- context save/restore;
- the fixed guest-page-fault handling; and
- terminal failure on every other path.

It excludes a successful post-entry completion path, root switching, protected
VS entry, and every R5/R6/R7 behavior.

The R3 unexpected-trap sink is intentionally not a partial R4 handler: it
does not inspect cause, save state, advance a PC, resume a guest, or select a
root.
