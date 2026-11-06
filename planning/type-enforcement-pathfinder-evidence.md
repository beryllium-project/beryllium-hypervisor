<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Fixed Type Enforcement pathfinder evidence

## Purpose and scope

This document records the fifth and final bounded Helium pathfinder
experiment on `historical_he/type-enforcement-poc`. The branch starts from exact
minimal-RISC-V commit
`cc6029acdd5df1fc14157c4faea4cc047e49a90e`.

It evaluates one fixed TE configuration over two sequential VS-mode subjects,
two distinct Sv39x4 roots, private memory, and one asymmetrically shared page.
It does not select TE for Beryllium, define MVP 1.0, or supersede evidence on the
other comparison branches.

## Helium 0.5.0 identity refactor

The 2026-07-21 refactor changes the active pathfinder identity from Beryllium
to Helium without changing the fixed TE policy, roots, access sequence, trap
surface, or security claim.

It is intentionally interface-breaking:

- wrapper `he`;
- public `he_` / `HE_` C namespace and `include/he/`;
- `helium.*` image and log names;
- `HE_*` serial markers and evaluator environment variables;
- `he-te-v1` report schema;
- `he:docs:*` npm scripts; and
- `helium/*` private branch refs.

There are no compatibility aliases. The linked bytes and report identity
change, so the complete GCC, Clang, QEMU, report, documentation, local, and
rootless gates were rerun. The supportable security statement remains bounded
to the behavior below.

## Exact executable chain

```text
QEMU 10.2.2 virt
  -> packaged OpenSBI M-mode
  -> Helium HS-mode
     -> writer_t synthetic VS subject
     -> HGATP write + global HFENCE.GVMA
     -> reader_t synthetic VS subject
```

One hart runs with interrupts disabled. VS-stage translation is Bare. Writer
and reader execute different entry sequences from one intentionally shared RX
payload page. They are security subjects, not complete VMs: there is no
scheduler, concurrent execution, general vCPU object, or saved context.

## Fixed labels and policy

Subject labels:

```text
monitor -> monitor_t
writer  -> writer_t
reader  -> reader_t
```

Object labels:

```text
code                           -> payload_t
writer stack + private data    -> writer_t
reader stack + private data    -> reader_t
shared data                    -> shared_t
```

The only object class is `memory`; permissions are `open`, `read`, `write`,
and `execute`.

The complete six-rule matrix is:

| Source | Target | Permissions |
| --- | --- | --- |
| `writer_t` | `payload_t` | open, read, execute |
| `reader_t` | `payload_t` | open, read, execute |
| `writer_t` | `writer_t` | open, read, write |
| `reader_t` | `reader_t` | open, read, write |
| `writer_t` | `shared_t` | open, read, write |
| `reader_t` | `shared_t` | open, read |

Every absent rule denies. Labels begin invalid, accept one assignment, and must
all be present before one-way API sealing. The fixed monitor initializer
performs labeling before either root is constructed.

## Exact roots

| GPA | Resource | Type | Writer root | Reader root |
| ---: | --- | --- | --- | --- |
| `0x40000000` | common code | `payload_t` | RX | RX |
| `0x40001000` | writer stack | `writer_t` | RW | absent |
| `0x40002000` | reader stack | `reader_t` | absent | RW |
| `0x40003000` | writer private | `writer_t` | RW | absent |
| `0x40004000` | reader private | `reader_t` | absent | RW |
| `0x40005000` | shared data | `shared_t` | RW | R |

Code and shared GPAs resolve to common physical pages. Private GPAs resolve
only in the owning root.

`open` authorizes exposure but is not a PTE bit. Runtime derives R/W/X,
requires one combined rule to cover the complete set, installs the leaf, and
compares each TE decision with the resulting access bit.

## Gate results

| Gate | Result | Evidence |
| --- | --- | --- |
| OpenSBI -> HS | Pass on QEMU | both compiler images reach HS |
| Fixed labeling and seal | Pass | host GCC/Clang plus target initialization |
| Writer VS entry | Pass on QEMU | exact entry/root/stack |
| Writer private RW | Pass on QEMU | physical sentinel changed |
| Writer shared RW | Pass on QEMU | common sentinel changed |
| Writer cross-private denial | Pass on QEMU | cause 21, exact PC/GVA/GPA, TE deny, absent leaf |
| VMID-zero root switch | Pass on QEMU | exact event, HGATP write, global fence, reader stack |
| Reader private RW | Pass on QEMU | distinct physical sentinel changed |
| Reader shared read | Pass on QEMU | observes writer's common value |
| Reader shared write denial | Pass on QEMU | cause 23, TE deny, present R/non-W leaf, value unchanged |
| Reader cross-private denial | Pass on QEMU | cause 21, exact PC/GVA/GPA, TE deny, absent leaf |
| Host TE mechanism tests | Pass | GCC and Clang |
| Host fixed-policy tests | Pass | every allow rule plus default/invalid denials |
| Host two-root tests | Pass | exact RX/RW/R bits and malformed-map failures |
| Helium 0.5.0 identity | Pass | no active compatibility aliases; source policy rejects the former namespace |
| TE report | Pass | `he-te-v1` labels, rules, decisions, and eight mappings |
| Standalone documentation | Pass | 12 sources, 13 HTML pages, links and 12-page Chromium render |
| Planning documentation | Pass | 22 sources, 23 HTML pages, links and 20-page Chromium render |
| Complete local gate | Pass | tools, source policy, both compilers, QEMU, report, docs, evidence |
| Pinned rootless evaluation | Pass | runtime networking disabled; complete check repeated |
| K3 hardware | `NOT RUN` | no QEMU result is promoted to hardware evidence |

Target matrix:

| Model | GCC/GNU ld | Clang/lld |
| --- | --- | --- |
| Fixed Type Enforcement | 3 ordered QEMU runs pass | 3 ordered QEMU runs pass |

The pinned rootless evaluator image records ID
`d2248f9c9574befbf722fa50c17de2e6489a0cad207d0b1283e9d58c670f9be4`
and digest
`sha256:6f4acdfdf49e4270041b02d059c2d2cccaff88ec2461e807870aa606c799efb9`.
The Fedora base is pinned by digest; installed package versions are recorded
evidence rather than inferred reproducibility from a human-readable tag.

## Accepted exit surface

| Cause | Accepted use |
| --- | --- |
| 10, VS environment call | writer accesses, writer completion/switch, reader accesses, final completion, explicit failure; each at exact PC/state |
| 21, load guest-page fault | writer load of reader-private GPA; reader load of writer-private GPA |
| 23, store/AMO guest-page fault | reader store to shared read-only GPA |

Every interrupt and every other synchronous cause is terminal. There is no
guest SBI proxy, general hypercall ABI, timer, interrupt injection, or device
model.

## Root-switch result

Both roots use VMID zero and map the same shared GPA with different
permissions. The platform switch writes reader `HGATP`, executes global
`HFENCE.GVMA`, then places the reader stack in `SSCRATCH` for the common trap
return.

The later denied reader store makes stale writer RW authority observable: a
stale writable translation can alter the common sentinel and prevent the
required trace from completing. This is bounded QEMU evidence, not a universal
architectural proof.

## TE mechanism and report

`src/te.c` implements only:

- invalid-label reset;
- one-time bounded labeling;
- complete-set seal;
- exact type/class keys;
- rule validation; and
- one-rule-covers-all-requested-permissions default denial.

`src/policy/te.c` selects all labels and the six rules. There is no runtime
dispatcher, parser, security-context string, wildcard, transition, role,
constraint, AVC, policy generation, update, or service.

`build/pathfinder/te/authority.json` records:

- all subject/object labels;
- memory class and permission vocabulary;
- all six rules;
- policy-derived PTE mappings; and
- every individual writer/reader decision.

The target never parses the report. It grants no authority and does not prove
target binary correspondence.

## Size result

The selected implementation contains 2,253 lines across target C, assembly,
headers, and linker script.

Both compiler/linker pairs produce a 16,384-byte loaded binary:

| Section | GCC/GNU ld | Clang/lld |
| --- | ---: | ---: |
| `.text` | 6,944 | 7,472 |
| `.rodata` | 2,436 | 2,144 |
| `.guest` | 4,096 | 4,096 |
| `.bss` | 98,344 | 90,160 |
| `.stack` | 8,192 | 8,192 |

BSS is dominated by two 16 KiB Sv39x4 roots, four lower tables, two stacks,
two private pages, one shared page, alignment, and policy state.

Compared with the minimal branch's selected 1,608-1,651 lines and 12,288-byte
loaded images, this branch adds 602-645 lines and one loaded 4 KiB region.
That difference includes a changed two-subject application, a second root,
label mechanism, fixed TE policy, extra fault path, report changes, and tests;
it is not a pure measurement of TE decision cost.

Line count and binary size are not security proofs.

## Assurance status

This branch contains no formal-verification setup.

There is no theorem proving, model-to-C refinement, bounded C verification,
assembly proof, translation validation, source-to-binary proof, or hardware
validation for this configuration.

Supportable statement:

> In the fixed single-hart QEMU scenario, host unit tests and repeated GCC and
> Clang images show that two sequential VS-mode subjects receive distinct
> monitor-assigned TE types and G-stage roots; the writer can read and write
> one shared page, the reader can read but not write it, and each subject's
> tested access to the other's private page is denied.

Required limit:

> This is a review-and-test PoC. It is not formally verified and has not been
> validated on hardware. Type Enforcement is not selected for Beryllium.

The exact-proof branch's machine-checked claims do not transfer to this changed
C, assembly, policy, root layout, or linked image.

## Trusted assumptions

This branch trusts or leaves unverified:

- GCC, GNU binutils, Clang, lld, and generated target binaries;
- OpenSBI entry, console, and reset behavior;
- QEMU RVH, Sv39x4, trap, `HGATP`, fence, and SBI behavior;
- the ratified RISC-V architecture and future hardware implementation;
- reset, VS-entry, trap, and root-switch assembly/inline assembly;
- linker layout and identity-mapped HS addresses;
- single-hart, interrupts-disabled execution;
- absence of devices and DMA; and
- human and LLM review quality.

It does not establish arbitrary guest containment, Linux isolation, complete
TE/FLASK semantics, information-flow noninterference, CHERI properties,
multicore/device correctness, side-channel resistance, K3 behavior,
availability, certification, or production readiness.

## Reproduction

```sh
make -C pathfinder MODEL=te unit
make -C pathfinder MODEL=te qemu
make -C pathfinder MODEL=te report-check
./pathfinder/he docs-check
./pathfinder/he check
./pathfinder/he evaluate --arch all
```

Generated evidence under `build/pathfinder/evidence/` records source state,
tools, hashes, image metrics, accepted exits, browser screenshots, and variant
metadata.

## Comparison conclusion

The experiment makes a mandatory type decision independently visible at three
points:

- cross-type private objects are not openable or mapped;
- the same shared object receives different PTE rights by source type; and
- the read-only reader denial survives the VMID-zero root switch.

It also exposes additional trusted state and future obligations: label
initialization, complete mediation, policy/PTE consistency, lifecycle,
relabeling, updates, decision caching, and proof composition.

This result is evidence for the final cross-variant policy review. It is not a
decision to place TE in the Beryllium core.
