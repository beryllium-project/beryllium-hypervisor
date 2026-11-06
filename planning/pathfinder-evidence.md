# Helium dual-architecture pathfinder evidence

## Purpose and scope

Beryllium is an open-source defensive security project for Linux-oriented systems.
Its pathfinder sub-project is **Helium** (He). This evidence records the
bounded RISC-V implementation and the Arm64 reference backend used to evaluate
multi-architecture support. It is not an MVP, production hardening claim,
Linux upstream proposal, certification, or hardware result.

This evidence checkpoint predates the Helium 0.5.0 rename. Its immutable
source uses the historical Beryllium / `be` interface. The branch ref is now
`historical_he/dual-arch-poc`; the retained checkpoint is exact commit `2c0bf53`.
The commands below remain those of that immutable source.
It also predates the current Beryllium parent-project identity; current prose
uses the new project name editorially without rewriting the checkpoint.

The implemented chain is:

```text
QEMU virt -> OpenSBI M-mode -> Beryllium HS-mode -> synthetic VS-mode payload
QEMU virt -> TF-A EL3 -> Beryllium EL2 -> synthetic EL1h payload
```

The implementation is under `pathfinder/`. Generated evidence is retained
under `build/pathfinder/evidence/` and is reproducible with:

```sh
make check
./pathfinder/be evaluate --arch all
```

Standalone Helium HTML is generated under
`pathfinder/docs/html/`; `./pathfinder/be` is the checkpoint's evaluator
wrapper.

The rootless command builds the pinned Fedora environment, disables networking
while running the tests, and invokes Cerberus in a separate pinned rootless
container.

## Exact assurance wording

The supportable statement is:

> Helium contains machine-checked abstract models and targeted formal
> verification of one sequential C module; the hypervisor implementation,
> assembly boundary, compiler output, and hardware are not formally verified
> as a whole.

Do not shorten this to “Helium is formally verified” or “the hypervisor code
is formally verified.”

Private internal development and evaluation are allowed. A public GitHub push
is separately blocked until responsible-human review is recorded for an exact
clean commit and `./pathfinder/be publication-check` passes.

## Gate status

| Gate | Status | Evidence |
| --- | --- | --- |
| OpenSBI -> HS -> VS | Pass on QEMU | GCC and Clang images enter VS mode |
| TF-A BL1/BL2/BL31 -> EL2 -> EL1 | Pass on QEMU | Source-built flash/FIP enters BL33 at EL2h |
| VS -> HS -> VS exit | Pass on QEMU | Exact event PC, cause 10, and virtual-origin checks |
| Assigned G-stage page | Pass on QEMU | Guest reads and validates the assigned value |
| Unassigned page | Pass on QEMU | Exact load guest-page fault, no mapping added |
| Revoked page | Pass on QEMU | Leaf PTE cleared, global `HFENCE.GVMA`, later access faults |
| Arm assigned/unassigned/revoked pages | Pass on QEMU | Canonical stage-2 leaves, exact L3 faults, global TLBI |
| Arm PSCI shutdown | Pass on QEMU | Secure GPIO marker; runtime semihosting disabled |
| Determinism | Pass on QEMU | Three runs per compiler and boot profile on every full check |
| Tiny ownership proof | Pass | Rocq checks unique writable frame ownership |
| Bounded architecture models | Pass | Rocq checks `BoundedH.v` and `BoundedArm64.v` |
| Sail-to-Rocq viability | Report complete; H path blocked | Generic RV64D generation succeeds, mainline H semantics are incomplete |
| Sequential C verifier pilot | Pass within stated scope | CBMC, Frama-C/WP/Z3, and Cerberus |
| Policy comparison | Complete for the pathfinder phase | No permanent policy architecture selected |
| K3 mechanism matrix | Complete as a disposition | Every hardware result remains `NOT RUN` |
| Rootless open environment | Pass | Pinned Fedora and Cerberus container images |

These results satisfy the executable pathfinder spine. They do not define MVP
1.0; the planning gates in `README.md` remain in force.

## Arm64 reference-backend evidence

### Pinned platform

| Item | Value |
| --- | --- |
| QEMU | 10.2.2 `virt`, Cortex-A57, one CPU, GICv2 |
| TF-A | v2.15.0, commit `da738d5eae93af342fdc4995dd3c05acb4c9d757` |
| TF-A archive SHA-256 | `3a13cf062213f92a54af015c55ced26b1ea75a2ca48c77491a4f5077bfb14ca1` |
| RAM | 1 GiB at `0x40000000`; required for default BL33 at `0x60000000` |
| Firmware | BL1 + FIP in flash, FIP offset `0x00040000` |
| Console/shutdown | PL011 `0x09000000`; PSCI secure GPIO `0x090b0000` |

The diagnostic direct-EL2 path is tested separately and emits `evidence=no`.
Evidence requires the TF-A path and a QEMU command with no semihosting option.

### Stage-2 and exception profile

- `VTCR_EL2=0x80023560`: 32-bit IPA, 4 KiB granule, L1 start,
  inner-shareable write-back walks, 40-bit PA.
- VMID 1 and the exact aligned L1 physical address in `VTTBR_EL2`.
- One L1, one L2, and one L3 table; no block mappings.
- Read-only executable code and read/write execute-never data.
- HVC64 accepted only with `EC=0x16`, EL1h origin, exact event, phase, and
  preferred return PC.
- Denied loads accepted only with `EC=0x24`, `DFSC=0x07`, read direction,
  valid FAR, no stage-1 walk, exact FAR/HPFAR-derived IPA/ELR/phase.
- Revocation clears the expected leaf, then executes
  `DSB ISHST; TLBI VMALLS12E1IS; DSB ISH; ISB`.

Both GCC and Clang payloads pass three direct runs and three TF-A runs. The
TF-A runner requires `QEMU System Power off: with GPIO.` after
`BE_RESULT: PASS`.

## RISC-V executable behavior

### Boot and privilege transition

- QEMU loads packaged OpenSBI 1.7 at `0x80000000`.
- OpenSBI transfers hart 0 to the Beryllium ELF entry at `0x80200000` in S-mode
  with virtualization disabled, which is HS-mode when RVH is present.
- Beryllium clears BSS, installs its HS trap vector, creates a 16 KiB-aligned
  Sv39x4 root, and maps only four guest pages.
- VS-stage translation is Bare. G-stage alone maps the synthetic guest code,
  stack, assigned data, and initially revocable data.
- Beryllium sets the HS return state and executes `SRET` into VS-mode.

The guest page layout is:

| GPA | Purpose | Initial rights |
| --- | --- | --- |
| `0x40000000` | Synthetic payload | Read, execute |
| `0x40001000` | Guest stack | Read, write |
| `0x40002000` | Assigned test data | Read, write |
| `0x40003000` | Unassigned negative test | Unmapped |
| `0x40004000` | Revocation test data | Read, write, then unmapped |

All G-stage leaf entries set `U`, because G-stage permission checks treat
accesses as user accesses even for VS-mode.

### Isolation sequence

1. The guest reads the assigned page and checks its sentinel value.
2. A VS `ECALL` reaches HS with cause 10. Beryllium checks the exact guest PC,
   event value, state-machine phase, and `hstatus.SPV`, then resumes VS.
3. The guest loads the unmapped page. HS accepts only load guest-page fault 21
   from the expected instruction and phase, and requires
   `stval == (htval << 2) == 0x40003000`.
4. The guest reads the revocable page while it is still mapped.
5. A checked VS event asks the harness to revoke that page. Beryllium clears the
   expected leaf PTE, verifies the expected HPA, and executes global
   `HFENCE.GVMA` before resuming.
6. The guest repeats the load. HS accepts it only as the expected guest-page
   fault at `0x40004000`.
7. A final event from the exact completion PC terminates the test through SBI
   system reset.

The expected negative faults are recovered only so the synthetic test can
continue. Recovery does not grant access: the handler checks cause, phase,
guest PC, GVA, and GPA before skipping the fixed four-byte test instruction.
Every other trap, interrupt, address, event, or state transition fails closed.

## Exit and SBI surface

### Accepted VS exits

| Cause | Accepted use |
| --- | --- |
| 10, environment call from VS | Events 1, 2, and 3 at their exact PCs |
| 21, load guest-page fault | Exact unassigned or revoked load in the expected phase |

Guest event 255 is an explicit failure report. Unknown events, instruction
guest-page faults, store guest-page faults, virtual-instruction faults,
interrupts, and every other synchronous cause terminate the PoC as a failure.

There is no general hypercall ABI, guest SBI proxy, device model, timer
virtualization, or interrupt injection.

### HS-to-OpenSBI calls

| SBI operation | Purpose |
| --- | --- |
| Legacy console putchar, extension 1 | Deterministic serial evidence |
| System reset, extension `0x53525354`, function 0 | Test shutdown |
| Legacy shutdown, extension 8 | Fallback if system reset returns |

Linux boot was not attempted. A Linux VS payload would at least require a
separately reviewed SBI virtualization surface for extension discovery,
timers, interprocessor interrupts, remote fences, reset, console, and possibly
hart management. The exact set is configuration-dependent and remains
unmeasured. Linux boot therefore remains a stretch outcome, not an implied
result.

## RISC-V baseline measured size

The retained 2026-07-16 rootless run measured:

- 1,983 lines across implementation C, assembly, headers, and linker script,
  including the complete onboarding annotations.
- 12,288-byte loaded binary for both GCC and Clang.
- GCC: 4,176-byte `.text`, 1,472-byte `.rodata`, and one 4,096-byte guest page.
- Clang: 4,464-byte `.text`, 1,272-byte `.rodata`, and one 4,096-byte guest page.
- 49,152-byte GCC BSS and 53,248-byte Clang BSS, dominated by the 16 KiB
  Sv39x4 root, lower-level tables, test pages, alignment, and stack.

These are pathfinder measurements, not optimized targets.

## Formal investigation

### Ownership invariant

`pathfinder/formal/Ownership.v` models writable ownership as a partial
function from frames to domains. Rocq checks:

- a frame cannot be writable-owned by two distinct domains;
- a successful grant establishes the requested owner;
- a grant to an already owned frame fails closed;
- revocation removes the writable owner; and
- assignment and revocation preserve unique ownership.

This is an abstract invariant, not refinement from the C implementation,
assembly, page-table walker, compiler output, or QEMU.

`pathfinder/formal/BoundedH.v` supplies the redirect model for the exact
hypervisor behavior used by the PoC. It checks:

- an unassigned page is denied;
- a mapped readable page is allowed;
- a stale cached translation can survive PTE revocation before a fence;
- clearing the PTE and executing `HFENCE.GVMA` denies the later load;
- the modeled VS -> HS -> VS trap round trip restores VS mode; and
- only the VS `ECALL` and load guest-page fault are in the modeled surface.

These definitions encode selected H-specification behavior; they do not prove
that QEMU, the assembly boundary, or the C implementation implements it.

`pathfinder/formal/BoundedArm64.v` separately checks the modeled consequences
of readable stage-2 leaves, stale cached translations, global TLBI, and the
EL1 -> EL2 -> EL1 round trip. It assumes the Arm architectural meaning of
descriptors and maintenance and is not a refinement proof.

### Arm ASL viability result

The open Arm ASL interpreter and published machine-readable specification path
are relevant upstream candidates, but this implementation did not establish a
pinned ASL-to-Rocq or ASL-to-C refinement for EL2 stage 2. No ASL result is
used as normative evidence.

Disposition:

1. Retain `BoundedArm64.v` as an explicit non-claiming model of only the
   behavior exercised by the PoC.
2. Treat descriptor, exception, and TLBI semantics as architecture assumptions
   checked against the Arm ARM and QEMU execution.
3. Evaluate a pinned open ASL execution/refinement path as a follow-on tooling
   task and prefer upstream contributions over a Beryllium-specific model fork.
4. Do not delay or inflate the current assurance claim while that path is
   absent.

### Sail-to-Rocq result

The experiment pinned:

- `riscv/sail-riscv` commit
  [`02e2ae8956965d3d89c2f3491f35972cba39e072`](https://github.com/riscv/sail-riscv/commit/02e2ae8956965d3d89c2f3491f35972cba39e072).
- Sail release `0.20.2-binary`, asset `sail-Linux-x86_64.tar.gz`,
  SHA-256
  `26b59bcab2d66e9f220d317dfe45f8b09170ed70e59a824553d6f525134d1ff6`.
- Rootless `rocq/rocq-prover:9.0.1` image.
- `coq-sail-stdpp` 0.20.2.

The all-module RV64D model generated and compiled to Rocq successfully. The
generated `rv64d.v` was 5,245,221 bytes and the checked `rv64d.vo` was
5,533,484 bytes.

That success does **not** establish an H-extension proof path. At the pinned
revision:

- `hartSupports(Ext_H)` is false in the mainline model.
- The H module only supplies the extension-enablement clause.
- `misa.H` is marked not fully supported.
- Hypervisor exception identifiers are present, but the required hypervisor
  CSRs, instructions, and two-stage translation are not a complete merged
  model.
- The upstream H implementation status lists two-stage translation and
  hypervisor instructions as draft work.

Disposition:

1. Keep the generated mainline Sail/Rocq model for supported base behavior.
2. Do not claim that it validates `hgatp`, Sv39x4 walking, `SRET` HS/VS
   transitions, or `HFENCE.GVMA`.
3. Use the checked `BoundedH.v` model for only those bounded H behaviors and
   keep it aligned with the ratified privileged specification.
4. Use QEMU and later hardware as differential implementation checks, not as
   proof authorities.
5. Track the upstream H work and contribute reusable tests or fixes rather
   than creating a Beryllium-specific Sail fork.

This activates the redirect criterion in `pathfinder-plan.md`: the mainline
Sail-to-Rocq H path is currently immature.

Sources:

- [Sail RISC-V extension roadmap](https://github.com/riscv/sail-riscv/wiki/Extension-Roadmap)
- [Sail RISC-V hypervisor implementation status](https://github.com/riscv/sail-riscv/wiki/Hypervisor-Implementation-Status)
- [RISC-V privileged architecture](https://github.com/riscv/riscv-isa-manual)

## Sequential C verification pilot

The selected leaf is `src/core/test_flow.c`, the deterministic state machine
that authorizes the positive test, both negative-fault recoveries, revocation,
and completion.

### Results

| Tool | Result | Scope |
| --- | --- | --- |
| CBMC 6.8.0 | 123 checks passed | Memory safety, arithmetic checks, invalid ordering, symbolic event/address cases |
| Frama-C 32.1 WP | 91/91 goals proved | ACSL contracts and runtime-error obligations |
| Qed plus Z3 4.16.0 | 70 plus 17 goals; four structural goals | Internal simplification, SMT discharge, termination, and reachability |
| Cerberus `dccd7b4...` | Returned specified value 0 | Sequential ISO C execution of the valid trace |
| CN | Not run | Optional and non-load-bearing |

Limitations:

- Only the sequential state machine was analyzed; no whole-hypervisor proof is
  implied.
- Fedora Why3 1.8.2 treats Z3 4.16.0 as a newer unrecognized version even
  though Frama-C successfully discharged the obligations. This is a tool
  qualification warning to retain.
- Cerberus currently supplies an older x86-64 implementation profile. It was
  used for language semantics, not RISC-V ABI or object-layout evidence.
- The upstream Cerberus release container invokes `dune subst` without usable
  version metadata for a detached pinned revision. The checked-in container
  recipe avoids substitution, pins the source and opam-repository revisions,
  and builds directly.

## Policy comparison

| Model | Core state and mediation | Revocation/delegation | Proof and audit burden | Pathfinder result |
| --- | --- | --- | --- | --- |
| Ownership plus explicit grants | Small owner map and fixed transitions | Direct revoke; limited delegation | Lowest | Best fit for current PoC mechanism |
| Software capabilities | Derivation, rights, lineage, and object references | Natural attenuation; revocation needs explicit design | Medium; strong CHERI alignment | Candidate for post-PoC model |
| Capabilities plus TE | Capability graph plus labels, classes, policy generations, and flow rules | Rich mandatory constraints | Highest; composition and usability risk | Not justified in the current core |

Recommendation for MVP planning:

- Retain ownership and explicit grants as the current mechanism baseline.
- Prototype a software-capability authority graph outside the privileged core.
- Evaluate whether a mandatory-flow layer adds a concrete property that cannot
  be expressed acceptably through ownership and bounded capabilities.
- Do not add labels, a policy server, or a permanent capability ABI to the
  pathfinder core.

This is not final policy selection.

## K3 and RISC-V mechanism disposition

K3 hardware is unavailable. Every K3 result below is therefore `NOT RUN`.

| Mechanism | PoC disposition | QEMU evidence | K3 status |
| --- | --- | --- | --- |
| RVH HS/VS | Used | Pass | `NOT RUN` |
| Sv39x4 G-stage | Used | Assigned, denied, and revoked access pass | `NOT RUN` |
| Trap handling | Used | Causes 10 and 21 only | `NOT RUN` |
| AIA/IMSIC/APLIC | Deferred; payload needs no interrupts | Not exercised | `NOT RUN` |
| Sstc | Deferred; payload needs no timer | Not exercised | `NOT RUN` |
| State-enable/counter filtering | K3 bring-up candidate | Not exercised | `NOT RUN` |
| PMP/ePMP/Smepmp | Observe firmware handoff | OpenSBI reports 16 PMP entries; no HS programming | `NOT RUN` |
| RISC-V IOMMU | Later device-domain work | No DMA or device assignment | `NOT RUN` |
| Nine K3 IOPMP instances | Later device-domain work | Not represented | `NOT RUN` |
| Cache-block operations/non-coherent DMA | K3 bring-up and I/O work | CPU-only test | `NOT RUN` |
| Secure boot/eFuse/rollback | Platform-assumption study | Not represented | `NOT RUN` |
| Crypto/vector crypto/TRNG | Attestation or later research | Not used | `NOT RUN` |
| Debug/JTAG/N-Trace lockdown | Security-profile bring-up | Not represented | `NOT RUN` |
| RAS/RERI | Later containment work | Not represented | `NOT RUN` |
| GPU/accelerator isolation | Later research | Not represented | `NOT RUN` |

No K3 feature is inferred from QEMU success.

## Assumptions and threat-model delta

The PoC explicitly trusts:

- QEMU's implementation of RVH and Sv39x4.
- Packaged OpenSBI handoff and SBI console/reset behavior.
- GCC, Clang, assemblers, linkers, and their generated binaries.
- The ratified RISC-V privileged specification as the architecture reference.
- Single-hart execution with interrupts disabled.
- QEMU's Arm stage-2, exception, TLBI, PL011, and secure-GPIO behavior.
- TF-A BL1/BL2/BL31 handoff and PSCI implementation.
- The Armv8-A architecture specification for the selected EL2 profile.

The PoC demonstrates architectural CPU memory denial for two controlled loads.
It does not establish:

- protection from malicious firmware, QEMU, hardware, or compilers;
- arbitrary hostile-guest containment;
- DMA, interrupt, timer, device, or IOMMU isolation;
- multicore invalidation or concurrency correctness;
- side-channel resistance;
- Linux management-domain isolation;
- cryptographic measurement, secure boot, or attestation;
- availability; or
- proof-to-C or source-to-binary correspondence.
- Arm hardware behavior, RME/CCA, GIC, SMMU, or platform firmware outside the
  pinned QEMU TF-A port.

All non-test traps terminate. The serial log contains only deterministic test
state and no secrets.

## One-slide architecture summary

```text
RISC-V                         Arm64
OpenSBI (M)                    TF-A (EL3)
    |                              |
Beryllium (HS)                        Beryllium (EL2)
Sv39x4 + HFENCE                stage 2 + DSB/TLBI/DSB/ISB
    |                              |
payload (VS)                   payload (EL1h)

Both: assigned read -> denied read -> revoke -> denied post-revoke read
```

The security value is intentionally narrow: demonstrate and measure the
smallest defensive isolation spine before defining a Linux-facing MVP.

## Remaining pathfinder work

- Connect the bounded H and ownership models to implementation contracts in a
  later refinement step.
- Evaluate an open Arm ASL path without making it normative or load-bearing.
- Re-run the K3 matrix when hardware becomes available.
- Record the short demo and assemble the October 2026 discussion package.
- Review the evidence and community feedback before defining MVP 1.0.
