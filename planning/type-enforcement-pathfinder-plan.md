<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Fixed Type Enforcement pathfinder plan

## Status

This plan defines the fifth and final bounded Helium pathfinder experiment
on `historical_he/type-enforcement-poc`. The branch starts from exact commit
`cc6029acdd5df1fc14157c4faea4cc047e49a90e` of the minimal RISC-V PoC.

The experiment evaluates one deliberately small Type Enforcement (TE)
configuration. It does **not** select TE for Beryllium, define MVP 1.0, or supersede
the ownership, software-capability, capability-plus-flow, dual-architecture,
or exact-proof comparison evidence on their respective branches.

The question is narrow:

> What mechanism, policy state, enforcement, test, and review cost is required
> for two fixed VS-mode subjects to share one memory resource with different
> TE permissions while remaining isolated from each other's private memory?

## Terminology

The implementation has two synthetic virtual subjects:

- **writer**: a VS-mode subject labeled `writer_t`;
- **reader**: a VS-mode subject labeled `reader_t`.

They are not complete virtual machines. They execute sequentially on one hart,
share one payload code page intentionally, have no scheduler or saved vCPU
object, and never run concurrently. Each subject nevertheless has a distinct
Sv39x4 G-stage root, private stack, private data page, and monitor-held
security identity.

TE uses:

- a **source type** assigned to a subject;
- a **target type** assigned to a resource;
- an **object class**, fixed here to `memory`;
- a requested permission set; and
- an explicit allow rule.

An absent, incomplete, invalid, uninitialized, or unsealed rule or label
denies access. A resource identifier or GPA conveys no authority.

## Fixed configuration

### Subjects

| Subject | Privilege | Type | Execution |
| --- | --- | --- | --- |
| monitor | HS-mode | `monitor_t` | Trusted mechanism and fixed initializer |
| writer | VS-mode | `writer_t` | Runs first |
| reader | VS-mode | `reader_t` | Runs after a fenced G-stage switch |

### Resources

All resources have object class `memory`.

| Resource | GPA | Backing | Target type | Intended mapping |
| --- | ---: | --- | --- | --- |
| payload code | `0x40000000` | Shared read-only code page | `payload_t` | Both subjects: read/execute |
| writer stack | `0x40001000` | Writer-private page | `writer_t` | Writer: read/write |
| reader stack | `0x40002000` | Reader-private page | `reader_t` | Reader: read/write |
| writer private data | `0x40003000` | Writer-private page | `writer_t` | Writer: read/write |
| reader private data | `0x40004000` | Reader-private page | `reader_t` | Reader: read/write |
| shared data | `0x40005000` | One common physical page | `shared_t` | Writer: read/write; reader: read-only |

Both roots cover the same bounded GPA region. Each maps only common code, its
own stack, its own private data, and the common shared page. The other
subject's stack and private page have no leaf in that root.

### Object class and permissions

The only object class is `memory`. The complete permission vocabulary is:

| Permission | Meaning in this experiment |
| --- | --- |
| `open` | The monitor may expose the object in the subject's G-stage root |
| `read` | The G-stage leaf may carry `R` |
| `write` | The G-stage leaf may carry `W`; RISC-V also requires `R` |
| `execute` | The G-stage leaf may carry `X` |

`open` is a TE permission, not a file operation, guest ABI, hypercall, or
runtime request. The monitor checks it while constructing the fixed roots.
Only `read`, `write`, and `execute` become hardware PTE bits.

### Complete allow policy

| Source type | Target type | Class | Allowed permissions |
| --- | --- | --- | --- |
| `writer_t` | `payload_t` | memory | open, read, execute |
| `reader_t` | `payload_t` | memory | open, read, execute |
| `writer_t` | `writer_t` | memory | open, read, write |
| `reader_t` | `reader_t` | memory | open, read, write |
| `writer_t` | `shared_t` | memory | open, read, write |
| `reader_t` | `shared_t` | memory | open, read |

There are no wildcard, transition, inheritance, relabel, override, constraint,
role, user, boolean, conditional, or dynamic-policy rules. In particular:

- `writer_t` has no rule for `reader_t` objects;
- `reader_t` has no rule for `writer_t` objects;
- `reader_t` lacks `write` to `shared_t`;
- neither guest type can execute private or shared data; and
- an allow rule never creates a mapping beyond the fixed configuration.

This is a TE matrix, not SELinux, XSM/FLASK, a general policy language, or a
complete information-flow system.

## Initialization and trust boundary

The fixed initializer remains inside the trusted HS image for this experiment:

1. reset every subject and object label to invalid;
2. assign all three subject types;
3. assign all six target types and the memory class;
4. reject duplicate, missing, out-of-range, or post-seal labeling;
5. seal the label state;
6. derive each intended PTE permission from an `open` decision plus individual
   `read`, `write`, and `execute` decisions;
7. create the two G-stage roots; and
8. verify required mappings and required denials before first VS entry.

The initialization is explicit so a later system-description compiler and
validated initializer can replace it. This branch has no manifest parser,
policy compiler, policy server, security context string parser, access-vector
cache, or runtime relabeling.

The trusted mechanism owns:

- label storage and one-way sealing;
- range and state validation;
- default-deny rule matching;
- derivation of hardware permissions from policy decisions;
- two fixed G-stage roots and the active-subject identity;
- exact trap, address, PC, phase, and policy-denial checks; and
- the global `HFENCE.GVMA` when switching roots with VMID zero.

The fixed policy owns only label assignments and six allow rules.

## Executable sequence

1. OpenSBI enters Helium in HS-mode on hart zero.
2. Helium labels and seals the fixed TE configuration.
3. It builds the writer and reader G-stage roots from TE decisions.
4. It enters the writer at its exact VS entry and stack.
5. The writer reads and writes its private page.
6. The writer reads, writes, and rereads the shared page.
7. The writer reports the positive accesses at one exact `ECALL`.
8. The writer loads the reader-private GPA. The exact unmapped load faults;
   HS checks the current TE denial and advances only that test instruction.
9. A checked writer event switches to the reader root and stack. The monitor
   writes `HGATP`, executes global `HFENCE.GVMA`, and returns to the exact
   reader entry.
10. The reader reads and writes its own private page and reads the writer's
    value from the shared page.
11. The reader reports those positive accesses at one exact `ECALL`.
12. The reader attempts to write the shared page. The read-only G-stage leaf
    raises the exact store guest-page fault; HS confirms TE denies `write` and
    that the backing value is unchanged.
13. The reader reloads the shared value, then loads the writer-private GPA.
    The exact unmapped load faults and HS confirms the cross-type denial.
14. One exact completion event terminates through OpenSBI reset.

Every other event, phase, PC, address, trap cause, interrupt, label state,
policy result, page-table state, hart, or transition fails closed.

## Unit and integration evidence

### Core-mechanism unit tests

Host GCC and Clang tests cover:

- reset, invalid-label state, and unsealed denial;
- valid one-time subject and object labeling;
- rejection of duplicate, invalid, incomplete, and post-seal labeling;
- exact rule matching and all-requested-permissions semantics;
- default denial for absent rules and invalid inputs;
- two independent G-stage roots;
- exact PTE permissions derived for writer and reader;
- unmapped cross-subject resources; and
- rejection of malformed, duplicate, misaligned, or over-permissive mappings.

### Fixed-policy unit tests

Host GCC and Clang tests cover every positive rule and representative negative
decision, including:

- writer shared open/read/write allow;
- reader shared open/read allow and write deny;
- private self-type open/read/write allow;
- cross-type open/read/write deny;
- execute only for `payload_t`;
- no partial satisfaction of a multi-permission request; and
- invalid subject, resource, class, type, and permission denial.

### QEMU evidence

GCC/GNU ld and Clang/lld images each run three times under pinned QEMU. The
serial checker requires every positive access, cross-private denial, shared
write denial, root switch, and final result in exact order. QEMU exit status
alone is not evidence.

An offline deterministic TE report records:

- all subject and target labels;
- the memory object class and complete permission vocabulary;
- all six allow rules;
- every fixed mapping and hardware permission;
- positive and negative decisions for both subjects; and
- the selected source revision and toolchain evidence.

Helium never parses this report. It grants no runtime authority.

## Security claim

The supportable branch claim is:

> In the fixed single-hart QEMU scenario, host unit tests and repeated GCC and
> Clang images show that two sequential VS-mode subjects receive distinct
> monitor-assigned TE types and G-stage roots; the writer can read and write
> one shared page, the reader can read but not write it, and each subject's
> tested access to the other's private page is denied.

This is test evidence over a fixed scenario. It is not a universal
noninterference theorem, C refinement, binary proof, arbitrary-guest
containment result, hardware result, or formal verification of the
hypervisor.

## Trusted assumptions and limits

The experiment trusts or leaves unverified:

- the restricted C implementation and fixed policy source;
- GCC, GNU binutils, Clang, lld, and the generated binaries;
- reset, VS-entry, root-switch, and trap assembly behavior;
- linker layout and identity-mapped HS physical addresses;
- OpenSBI handoff, console, and reset behavior;
- QEMU's RVH, Sv39x4, trap, `HGATP`, and `HFENCE.GVMA` behavior;
- the ratified RISC-V privileged architecture;
- single-hart, sequential execution with interrupts disabled; and
- absence of DMA and devices.

The run demonstrates selected architectural read/write denials. It does not
cover arbitrary code, speculative or microarchitectural leakage, availability,
DMA, IOMMU/IOPMP, interrupts, timers, multicore, policy updates, label
transitions, stale access-vector caches, Linux, K3 hardware, CHERI properties,
secure boot, attestation, certification, or production hardening.

The exact-proof branch's machine-checked claims do not transfer to this
changed C, assembly, page-table, policy, or linked-image configuration.

## Non-goals

- Selecting TE, SELinux, XSM, FLASK, or a production policy architecture.
- General domain or vCPU creation.
- Concurrent guests, scheduling, saved vCPU contexts, or multiple harts.
- A policy language, compiler, parser, server, cache, update, or ABI.
- Dynamic labeling, relabeling, transitions, delegation, or revocation.
- Capabilities, CHERI mechanisms, role-based access control, MLS/MCS, or
  information-flow proof.
- Linux boot, devices, DMA, IOMMU, IOPMP, interrupts, timers, or SBI proxying.
- Hardware validation, performance claims, certification, or upstream-ready
  code.

## Completion gates

1. The branch remains based on the exact minimal RISC-V commit named above.
2. One fixed TE source and no runtime policy dispatcher is linked.
3. Both subject roots are generated only from sealed TE decisions.
4. Host GCC and Clang mechanism and policy tests pass.
5. GCC/GNU ld and Clang/lld QEMU images pass the complete ordered sequence
   three times each.
6. The offline report proves review-visible distinction between writer
   read/write and reader read-only shared authority.
7. Source annotations, standalone HTML, diagrams, evaluator guidance,
   planning evidence, threat model, and claim limits match the implementation.
8. The complete local and pinned rootless Helium gates pass.
9. K3 hardware remains explicitly `NOT RUN`.
10. The final comparison does not describe TE as selected for Beryllium.

## Primary references

Accessed 2026-07-20:

- Spencer et al., [The Flask Security Architecture: System Support for
  Diverse Security Policies](https://www.usenix.org/conference/8th-usenix-security-symposium/flask-security-architecture-system-support-diverse-security).
- SELinuxProject,
  [SELinux Notebook: Type Enforcement](https://github.com/SELinuxProject/selinux-notebook/blob/main/src/type_enforcement.md).
- SELinuxProject reference policy,
  [FLASK object classes and access vectors](https://github.com/SELinuxProject/refpolicy/blob/master/policy/flask/access_vectors).
- Xen Project,
  [XSM and FLASK documentation](https://xenbits.xenproject.org/docs/unstable/misc/xsm-flask.txt).
- RISC-V International, ratified
  [Hypervisor Extension](https://docs.riscv.org/reference/isa/priv/hypervisor.html).
