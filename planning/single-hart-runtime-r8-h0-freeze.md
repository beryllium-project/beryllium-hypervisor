<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R8-H0 K3 profile freeze source

## Status and authority

This is the bounded, non-privileged source package for R8-H0. Its exact
status is:

```text
r8_h0_status=implementation-authorized-h0-local-not-reviewed
r8_h0_source=present-local-not-reviewed
r8_h0_candidate=local-uncommitted-not-reviewed
r8_h0_profile=blocking-unknowns-present
r8_h0_exit=not-met
r8_h0_acceptance=not-reviewed
r8_h1_authorization=not-authorized
r8_hardware_execution=NOT-RUN
```

The responsible human accepted the immutable R8 plan at exact target
`7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5` on 2026-08-07 and separately
authorized implementation only for the non-privileged H0 profile freeze.
Commit `cb0ac2a0f818ac57f2866cb7815767145608cf58` remains that original
authorization record. The responsible human then accepted exact Plan revision
R8-A target `8fa9d672cfcfb81ab68d9ed9553a5af48b884932`; its acceptance-record
commit and the exact H0 implementation base is
`1f6109f0d0371eb3707e296c3416e8c55235683e`, tree
`79a3410353e960d10c4fccc7b09e7b1e73e528a4`. Neither decision accepts H0,
authorizes H1-H4 or K3 execution, or creates a hardware result.

The original accepted plan file has SHA-256
`33f77df3cb6bfc32926e249ba87ca6adfff962c732253325e1fb61f3c60573ac` at the
original target. The current immutable plan, including accepted R8-A, has
SHA-256
`13f1b2482fdf21017a94c957be841477af452d68b4ce628ccd2fdc388b521b14`
at the accepted R8-A target and in this candidate. H0 edits neither accepted
plan object.

Accepted R7 implementation target
`9bf22913d67e9b72286813cd5f7993a9ad3857a8` remains the exact predecessor
boundary. Its review record, not its retained pre-decision status fields,
carries the R7 acceptance decision.

## Purpose and non-privileged boundary

H0 records checked input and a reviewable disposition for every required
board, firmware, boot, tool, capture, memory, hart, architectural-feature,
security-state, claim, and path fact. Its maintained host-only launchers,
checkers, contracts, mutation tests, and blocked/not-ready report add no
privileged C, assembly, linker script, image, generated evidence, CSR access,
reset, board load, or execution behavior to Beryllium. The package contains one
restricted-C **host launcher** source and its static ELF trust anchor; neither
is privileged target code.

No H0 content is K3 evidence. Public documentation is context only. The
machine-readable mirror is `tests/r8/h0-profile-v2.json`;
`tests/r8/h0-row-contract-v2.json` independently binds every stable row ID to
its matrix, disposition, resolution phase, and blocking gate; and
`tests/r8/h0-source-boundary-v2.json` is the canonical complete maintained
path/mode and bootstrap-path authority.
`tests/r8/h0-claim-contract-v1.json`, itself authenticated by the static
launcher, binds the SHA-256 and byte size of this **entire** Markdown file and
the complete profile and row-contract bytes, plus canonical hashes for every
UNKNOWN, disposition, gate, matrix, claim, non-claim, exit, and current-status
object. Extra prose, a new heading, whitespace drift, or an unrecognized table
row is therefore a stop. A mismatch among the four authorities is not a
choice of whichever value is more convenient.

## Exact `UNKNOWN` semantics

`UNKNOWN` means the exact delivered-board or selected-profile value has not
been supplied or observed. It is not a wildcard, default, inferred value,
zero, don't-care value, permission to use a public-board example, or
permission to proceed.

Every machine-readable row whose value is exactly `UNKNOWN` must have:

1. one allowed disposition;
2. a nonempty resolution phase;
3. one explicit blocking gate;
4. a nonempty observation or resolution plan; and
5. a nonempty fail-closed outcome.

The only allowed dispositions are:

| Disposition | Exact meaning |
| --- | --- |
| `required-and-tested` | A later separately authorized package must test the exact requirement; failure stops. |
| `disabled-and-checked` | The feature or source must be disabled or quiescent and that state checked. |
| `observed-assumption` | The retained value remains a trusted platform or firmware assumption, not a Beryllium proof. |
| `excluded` | The item is outside the R8 claim and cannot carry authority or rescue a run. |
| `deferred` | The item is inventoried only; active use requires later reviewed work. |
| `stop` | The present value or unresolved condition blocks its explicitly declared gate. |

Identity-critical board, firmware, normative load/reset/capture-tool,
physical-memory, and hart-selection unknowns keep H0 incomplete. They must be
supplied before H0 can be presented as exit-ready. Characterization values may
remain `UNKNOWN` in a later exact H0 candidate only when the candidate carries
a fail-closed observation plan for a separately authorized H1.

`NOT-RUN` is distinct: it means execution was not performed. Neither
`UNKNOWN` nor `NOT-RUN` is PASS.

## Public context is not the delivered profile

Tracked primary K3 documentation provides conservative planning context for
X100 RV64 with RVH, Sv39/Sv39x4, AIA, Sstc, Smstateen, Smepmp, 16 documented
PMP entries, optional F/D/V state, non-coherent DMA, and nine documented IOPMP
instances. Public material also describes a candidate
BootROM-to-FSBL-to-ESOS-to-OpenSBI-to-EDK2 sequence. These are not
measurements of the delivered board and do not establish that its actual
configuration exposes or uses any listed feature or stage.

The actual board, SKU, revision, X100 stepping, DRAM, firmware versions,
firmware source/configuration, boot sequence, load address, DTB, OpenSBI K3
port, lifecycle, PMP state, optional-state accessibility, hart parking,
DBCN/SRST behavior, and normative load path are all `UNKNOWN`. Preliminary
candidate product names are deliberately not selected or encoded as delivered
facts.

No public assertion overrides a matrix `UNKNOWN`, and no unverified detail is
promoted into the profile.

## Exact H0 package and path boundary

`tests/r8/h0-source-boundary-v2.json` is the single canonical complete
path/mode inventory. It enumerates:

- 24 maintained H0 paths: this freeze and exactly 23 paths under `tests/r8/`;
- the exact nine maintained R8-A support-source paths and no other support
  path;
- 25 pre-execution bootstrap entries embedded with exact mode, byte size,
  owner, and SHA-256 in `run-make.c`; the static `run-make.sh` ELF is the trust
  anchor and is deliberately not self-hashed;
- `docs/html/` as the sole authorized generated-derivative prefix, bound by the
  full candidate tree but excluded from H0 authority, semantic projection,
  deterministic report content, and digest;
- `.git/`, `build/`, and `node_modules/` as the only explicit physical-scan
  exclusions; Git ignore and info-exclude state never hides a candidate path;
  and
- exactly `tests/r8/run-make.sh` and `tests/r8/check-tools.sh` as executable
  maintained files; every other maintained path is mode `100644`.

The output trust rule is exact: every existing directory from repository
`build/` through each H0 output, scratch, `HOME`, and `TMPDIR` descendant is an
euid-owned real directory with no symlink and mode `0700`. New directories are
created `0700` and immediately descriptor/lstat/realpath/owner/mode
revalidated. Output files are euid-owned regular single-link files in an exact
mode allowlist. Parent ownership and mode are revalidated immediately before
create, write, fsync/close, rename, chmod, and removal as applicable. Cleanup
uses validated entry-by-entry unlink/rmdir and rejects hostile directories or
special files rather than performing broad recursive deletion.

The source checker implements exactly two accepted R8-A repository relations.
Development mode requires `HEAD` at full implementation base
`1f6109f0d0371eb3707e296c3416e8c55235683e`, the normal index exactly equal
to `HEAD`, and the complete candidate only in the 24 H0 paths, nine support
sources, and `docs/html/**`. Committed mode requires a clean `HEAD` that is
exactly one child of that base with the same changed-path boundary. A physical
walk, not `git status`, Git attributes, filters, or excludes, derives the
worktree.

The complete real index is inspected independently through configuration-
sanitized, replacement-disabled, fsmonitor-aware
`git ls-files -v --stage --debug --sparse --full-name -z`. Every entry must
have uppercase `H`, stage zero, a nonzero object, flags zero, and the exact
path, mode, type, and object in `HEAD`. Lowercase assume-unchanged,
skip-worktree, intent-to-add, unmerged stages, fsmonitor-valid,
sparse-directory, staged-only, zero-object, and every other non-normal bit or
mismatch are rejected. `GIT_OPTIONAL_LOCKS=0` and a before/after byte
comparison of `.git/index` prove that inspection did not refresh, normalize,
or otherwise mutate the user's index.

The physical walk remains an independent authority. In particular, a
worktree change hidden from `git status` by an isolated assume-unchanged
fixture is still found after the fixture index is returned to normal. The
checker independently derives the full Git tree and a
33-path non-generated semantic projection; an isolated synthetic committed
child proves that development and committed modes produce the same tree,
semantic digest, and semantic path count.

The report records generation state plus prospective or exact target, parent,
and tree. It never records generated documentation filenames, file counts,
byte counts, hashes, churn, or transient index-entry counts. Root
`package.json` and `package-lock.json` remain byte-identical to the exact
implementation base; the parser remains vendored only under
`tests/r8/third_party/acorn/`.

### Exact committed-candidate validation procedure

After the H0 candidate is committed, derive its exact full commit identity and
run the following gates from **three separate fresh, clean, detached
checkouts** of that same commit:

1. standalone H0: `./tests/r8/run-make.sh r8-check`;
2. documentation: `./be docs-check`; and
3. complete repository: `make check`.

Do not reuse a checkout between gates. Planning-site derivatives below root
`docs/html/` are candidate content. Any `pathfinder/docs/html/` changes
created by documentation validation are Helium derivative scratch caused by
the open generated-asset reproducibility issue. They are outside the R8-A H0
support and derivative boundary, must be discarded with that validation
checkout, and must never enter the H0 candidate, semantic projection, report,
or review inventory.

The H1 `arch/riscv/be/r8-h1-*` wildcard remains unresolved and grants no file
permission. The accepted plan's H2 maximum family remains a maximum, not an
exact authorized inventory. Root `Makefile`, `be`, and
`scripts/check-be.sh`, predecessor acceptance pins, and accepted R0-R7 paths
remain outside H0 and must not change.

The exact H1 and H2 additive path inventories remain `UNKNOWN` and are stop
conditions. They must be supplied in an accepted H0 candidate or a reviewed
plan revision before privileged implementation.

## Immutable R0-R7 predecessor manifest

`tests/r8/r0-r7-immutable-manifest-v1.json` is computed from exact accepted R7
implementation target `9bf22913d67e9b72286813cd5f7993a9ad3857a8`, tree
`18c734bada34a76a78c5e7df81b0a649b60b9535`.

It inventories all tracked regular or symlink files in the accepted plan
families:

```text
model/
tests/r0/
tests/r1/
tests/r2/
tests/r3/
tests/r4/
tests/r5/
tests/r6/
tests/r7/
include/be/r0-config.h
include/be/r1-config.h
include/be/r2.h
include/be/r3.h
include/be/r4.h
include/be/r5.h
virt/be/r0-config.c
virt/be/r1-config.c
virt/be/manifest.c
virt/be/state.c
virt/be/r3.c
virt/be/r4.c
virt/be/r5.c
arch/riscv/be/r0-*
arch/riscv/be/r3-*
arch/riscv/be/r4-*
arch/riscv/be/r5-*
arch/riscv/be/sv39x4.c
```

The accepted-plan-scoped canonical manifest contains 285 entries: 237 mode `100644`, 48 mode
`100755`, and no mode `120000` entry at the accepted target. Each entry records
its exact path, Git mode, kind, SHA-256 of file bytes, accepted-target
provenance, and matched plan family. Hashes are over exact Git blob bytes, not
Git object IDs. A future symlink would hash its target byte sequence without
dereferencing it. Entries use ascending UTF-8 path-byte order. Generated build
outputs are excluded.

Any missing, added, byte-different, or mode-different predecessor entry is a
stop. H0 supplies no authority to refresh an acceptance pin or modify a
predecessor checker. The manifest deliberately covers the accepted plan
families above; predecessor acceptance interfaces and the whole-candidate
checker cover broader shared files. It is not described as a complete
repository-wide predecessor inventory.

## Matrix reading rule

The following tables are complete for this H0 source. A row's resolution plan
is a plan only; it is not an observation. `authorized-h1-only` means the plan
may be executed only after exact H0 acceptance and a separate instruction
that authorizes H1. Current hardware state remains `NOT-RUN`.

Each row carries one independently checked blocking gate:

| Gate | Rows | Current `UNKNOWN` rows | Current blockers | Meaning |
| --- | ---: | ---: | ---: | --- |
| `h0-acceptance` | 81 | 81 | 81 | Genuine unresolved H0 profile facts that block presentation for H0 acceptance. |
| `h1-entry` | 1 | 0 | 0 | A fixed all-R8 stop condition that applies before and throughout a separately authorized H1. |
| `h1-completion` | 35 | 33 | 33 | H1-only characterization facts; they do not block H0 acceptance but must be resolved for H1 completion. |
| `h2-entry` | 3 | 3 | 3 | H1/H2 compatibility facts that must be resolved before H2 entry. |
| `nonblocking-deferred` | 27 | 2 | 0 | Fixed, excluded, accepted-predecessor, or not-selected deferred rows. |

The 147-row disposition totals remain independent of gate assignment:
25 `required-and-tested`, 9 `disabled-and-checked`, 10
`observed-assumption`, 10 `excluded`, 9 `deferred`, and 84 `stop`. In
particular, the two `stop` dispositions whose resolution phase is H1-only are
not H0-acceptance blockers.

## Board and silicon identity matrix

The delivered board is not selected by public product similarity. Every identity-critical `UNKNOWN` below blocks the H0 exit.

| ID | Required fact | Current value | Disposition | Blocking gate | Resolution phase and plan | Fail-closed outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `board.vendor` | Exact delivered board vendor. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Read the delivered board label and authoritative purchase or inventory record; retain a non-secret normalized value. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.product` | Exact delivered product name. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Read the delivered board label and authoritative vendor product identifier; do not select from public candidate names. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.sku` | Exact delivered SKU or ordering code. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Record the delivered unit SKU from the physical label or authoritative inventory record. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.revision` | Exact PCB or product revision. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Record the physical revision markings and retain a bounded photograph digest or inventory note without serial numbers. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.lab-inventory-id` | Stable non-secret lab inventory identifier. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Assign a project-local identifier that contains no serial number, credential, personal data, or secret. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.soc-identity` | Authoritative K3 SoC identity exposed on the delivered unit. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Obtain the documented SoC identity from physical markings or an authoritative firmware interface; H1 may cross-check but not invent it. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.x100-stepping` | Exact X100 stepping or revision identifier. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Obtain a vendor-documented stepping identifier and define the later H1 read-only cross-check if architecturally exposed. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.dram-size` | Installed usable DRAM size. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Obtain the board configuration and firmware memory map, then independently reconcile every usable and reserved extent. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.dram-topology` | Relevant DRAM channels, ranks, interleave, and address topology. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Obtain the exact board and firmware memory-topology description and identify any aliases or holes before assigning memory. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.boot-medium` | Actual boot medium used for normative R8 boots. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Record the populated medium and selected boot source from board configuration and observed cold boot. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.strap-state` | Boot and board configuration strap state. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Record every relevant switch, jumper, strap, and immutable board option before defining the cold-boot procedure. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.console-interface` | Physical serial or console interface. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Identify connector, voltage level, direction, and firmware console path from authoritative board documentation and the delivered unit. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.console-adapter` | Electrical adapter identity and configuration. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Record an exact non-secret adapter model, voltage, wiring, and host interface; do not retain a serial number. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.power-procedure` | Exact power-on and power-off procedure. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Write a bounded manual or open-tool procedure that is repeatable and cannot silently become a warm reset. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.cold-reset-procedure` | Exact cold-boot reset and minimum power-off interval. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Define and later verify the cold-boot sequence, including power removal, wait, strap state, and capture start ordering. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.debug-physically-connected` | Whether JTAG, DTM, trace, or another debug cable is physically connected. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Inspect the delivered setup and record each connected debug or trace path before any capture. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `board.trace-physically-connected` | Whether an external trace path is physically connected. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Inspect the delivered setup and record the connector and tool state, or explicitly record no connection. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |

## Boot, firmware, handoff, and SBI matrix

The actual boot chain and load path are not inferred from a documented or common K3 stack. Exact mutable bytes, open provenance, configuration, addresses, handoff, parking, and SBI behavior are required.

| ID | Required fact | Current value | Disposition | Blocking gate | Resolution phase and plan | Fail-closed outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `firmware.actual-boot-chain` | Exact ordered cold-boot chain on the delivered board. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Supply and hash every mutable stage and record any immutable ROM-reported identity; do not assume a public BootROM-to-FSBL-to-ESOS-to-OpenSBI-to-EDK2 sequence. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.rom-version` | Immutable ROM-reported version or explicit absence of a version interface. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Use an authoritative documented interface or record that no version is exposed; never infer the ROM revision from a mutable stage. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.first-mutable-stage` | First mutable boot stage identity, source, configuration, and SHA-256. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Obtain the exact image bytes and open source/build provenance or stop if only an opaque unidentifiable stage is load-bearing. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.bootloader` | Exact bootloader identity, source, configuration, and SHA-256. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Retain the exact binary, source revision, license, build recipe, and configuration for the bootloader used. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.m-mode-runtime` | Exact M-mode runtime or OpenSBI binary identity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Retain the exact binary and identify its source revision, license, build recipe, configuration, and SHA-256. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.opensbi-k3-port` | Exact OpenSBI K3 platform port and source revision if OpenSBI is used. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Locate and pin the exact open source implementing the board handoff; a banner or vendor statement alone is insufficient. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.configuration` | Complete firmware configuration affecting privilege, memory, harts, SBI, debug, and security state. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Retain build-time and board-time configuration and map each setting to the H1 observation plan. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.dtb` | Exact firmware-supplied DTB bytes and SHA-256. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Capture the exact DTB from the normative boot path and retain its bytes and hash; treat it as provenance, not authority. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.load-mechanism` | Normative mechanism that places Beryllium in DRAM. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select one fully open, locally reproducible path and pin its tools, arguments, stages, and failure behavior. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.load-address` | Exact Beryllium load address. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive the address from the exact board memory map and load path, then prove containment and non-overlap before any image exists. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.entry-address` | Exact Beryllium HS entry address. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Bind the entry address to the future linker plan and the exact firmware handoff; reject any mismatch before execution. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.entry-privilege` | Expected and later observed entry privilege and virtualization state. | `UNKNOWN` | `required-and-tested` | `h1-completion` | authorized-h1-only: Define a minimal read-only H1 observation that records privilege and virtualization state before any VS entry. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `firmware.a0-hart-id` | Initial a0 hart identity supplied at HS entry. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Define the exact expected participating hart from the selected boot path and retain the later H1 readback. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.a1-pointer` | Initial a1 pointer provenance and treatment. | `non-authoritative provenance only; no in-core parsing` | `excluded` | `nonblocking-deferred` | h0-policy-fixed: Hash and retain the pointed-to input only through open host tooling; independently validate normalized data before privileged use. | Any attempt to treat a1 or its contents as authority is a stop requiring revision. |
| `firmware.hart-parking` | Mechanism that parks or withholds every non-participating X100 hart. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Obtain the exact firmware contract and define continuous H1-H3 observation for every non-participating hart. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.sbi-base` | Exact SBI specification version and Base extension responses. | `UNKNOWN` | `required-and-tested` | `h1-completion` | authorized-h1-only: Probe the exact Base functions through bounded monitor-owned arguments and retain every return value. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `firmware.sbi-dbcn` | DBCN extension and console_write availability and failure behavior. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Establish whether the exact firmware provides DBCN and define bounded partial-progress and error handling; no legacy or MMIO fallback. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.sbi-srst` | SRST extension and system_reset availability and failure behavior. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Establish whether the exact firmware provides SRST and define deterministic termination; no undocumented fallback. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.sbi-allowlist` | Complete HS-facing SBI EID/FID allowlist. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Freeze an exact minimal allowlist after the firmware and diagnostic path are selected; reject every unlisted call. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `firmware.guest-sbi` | Guest-visible SBI surface. | `none` | `excluded` | `nonblocking-deferred` | h0-policy-fixed: Keep the two synthetic VS payloads on the private fixed event protocol. | Any guest-visible SBI requirement is outside R8 and stops for a reviewed plan revision. |

## Normative tool, reset, load, and capture matrix

Exact normative tools remain unselected. Fastboot and Python are candidates only; TitanTools is excluded; a SpacemiT OpenOCD path is exploratory unless an exact fully open source and build are pinned.

| ID | Required fact | Current value | Disposition | Blocking gate | Resolution phase and plan | Fail-closed outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `tool.host-environment` | Normative host OS or container image, package set, and digest. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select a fully open local environment and pin image/source/package identities and reproducible setup steps. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.gcc` | GCC version, executable path, resolved path, package/source, license, and SHA-256. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin the exact open GCC executable and owning source/package. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.gnu-binutils` | GNU assembler, objcopy, objdump, readelf, nm, and related binary tools. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin every invoked executable independently; do not treat a package version as the executable identity. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.gnu-ld` | GNU linker identity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin the exact linker executable, source/package, configuration, and SHA-256. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.clang` | Clang version and identity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin the exact open Clang executable and owning source/package. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.llvm-binary-utils` | LLVM binary-utility identities. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin every invoked LLVM executable and retain an independent GNU cross-check where applicable. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.lld` | LLD linker identity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin the exact lld executable, source/package, configuration, and SHA-256. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.make` | GNU Make identity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin GNU Make and preserve the checked-launcher design before any commands are introduced. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.node` | Node.js identity for deterministic host-side checking. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin an open Node.js build, executable path, source/package, and SHA-256. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.shell` | Normative POSIX shell identity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin the exact shell executable and prohibit caller substitution in later launchers. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.hash` | SHA-256 implementation identity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin the exact local open hashing executable and cross-check representative inputs independently. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.elf-primary` | Primary ELF inspection implementation. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin one open implementation with explicit supported-input limits. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.elf-cross-check` | Independent ELF inspection cross-check. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin an independently implemented open cross-check; disagreement must fail closed. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `tool.python` | Python interpreter if used for loading or capture. | `candidate-only; exact use and identity UNKNOWN` | `deferred` | `nonblocking-deferred` | before-h0-acceptance-if-selected: Use only if the normative load or capture path selects it, then pin interpreter, modules, source, license, and hashes. | Python is non-normative until selected and pinned; no result may depend on an ambient interpreter. |
| `tool.fastboot` | Fastboot implementation if used to load the board. | `candidate-only; exact use and identity UNKNOWN` | `deferred` | `nonblocking-deferred` | before-h0-acceptance-if-selected: Confirm the delivered board supports the exact path, select an open implementation, and pin source, binary, arguments, and transport. | Fastboot is non-normative until selected and pinned; lack of a verified path keeps H0 incomplete. |
| `tool.openocd` | OpenOCD identity if used. | `UNKNOWN` | `deferred` | `nonblocking-deferred` | before-h0-acceptance-if-selected: Use only after pinning an exact fully open upstream or vendor source revision, build recipe, license, configuration, and binary hash. | An unpinned or source-unavailable OpenOCD path is exploratory only and cannot satisfy H0. |
| `tool.gdb` | GDB identity if used. | `UNKNOWN` | `deferred` | `nonblocking-deferred` | before-h0-acceptance-if-selected: Pin exact open GDB source/package and executable only if the accepted capture or load procedure needs it. | GDB is non-normative until selected and pinned. |
| `tool.titantools` | TitanTools or another proprietary vendor tool. | `proprietary candidate excluded from normative evidence` | `excluded` | `nonblocking-deferred` | h0-policy-fixed: Do not use for normative loading, flashing, debug, reset, capture, checking, or evidence. | Any exploratory use produces non-normative data and requires blocker-policy documentation; it cannot satisfy H0-H4. |
| `capture.serial-tool` | Open serial capture tool identity and license. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select and pin one fully open local capture tool, source/package, binary hash, and exact invocation. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `capture.serial-settings` | Serial device selection, baud, data bits, parity, stop bits, and flow control. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive exact settings from the delivered board and retain them without embedding host-specific secrets. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `capture.serial-arguments` | Exact serial capture arguments, timeout, byte limits, and terminal handling. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Freeze bounded arguments that cannot silently switch devices, append stale data, or turn timeout into success. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `capture.reset-tool` | Open reset or power-control mechanism and identity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select a manual documented procedure or fully open local tool; pin every executable and argument if automated. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `capture.load-tool` | Open normative load or flashing tool and identity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Select one exact fully open path; retain source, license, build, binary hash, transport, arguments, and verification readback. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `capture.load-arguments` | Exact load/flash arguments and verified target region. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Freeze arguments only after the physical memory map and boot path are exact; verify bytes or cryptographic identity before execution. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `capture.capture-start-order` | Ordering of power/reset, capture start, load, and release. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Define an exact cold-boot procedure that cannot omit early firmware output or reuse a stale transcript. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `capture.redaction` | Pre-capture secret and personal-data exclusion rules. | `exclude secrets, credentials, device keys, private serial numbers, and personal data; preserve security-relevant state` | `required-and-tested` | `nonblocking-deferred` | h0-policy-fixed: Inspect planned outputs and define bounded substitutions before capture; hash raw retained inputs only when policy permits retention. | If safe capture cannot preserve required security facts without retaining prohibited data, R8 stops for a revised evidence path. |
| `capture.hardware-unavailable` | Behavior when the exact board or path is unavailable. | `NOT-RUN` | `required-and-tested` | `nonblocking-deferred` | h0-policy-fixed: Emit NOT-RUN and no success-shaped artifact; never substitute QEMU, another board, or a cached transcript. | Hardware unavailability cannot become PASS. |

## Memory, image, inventory, and comparison matrix

No unknown physical extent is assigned to a domain. Accepted guest semantics and Sv39x4 shape remain fixed while all K3 physical placement stays unresolved.

| ID | Required fact | Current value | Disposition | Blocking gate | Resolution phase and plan | Fail-closed outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `memory.usable-dram` | Complete usable DRAM extents: exact base, size, end, rights, cacheability, owner, and mutation phase (platform inventory). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.reserved-memory` | Complete firmware and board reserved-memory extents: exact base, size, end, rights, cacheability, owner, and mutation phase (firmware/platform). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.firmware` | Firmware-resident memory extents: exact base, size, end, rights, cacheability, owner, and mutation phase (M-mode firmware). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.bootloader` | Bootloader-resident memory extents: exact base, size, end, rights, cacheability, owner, and mutation phase (bootloader). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.dtb` | Firmware-supplied DTB extent: exact base, size, end, rights, cacheability, owner, and mutation phase (firmware provenance input). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.monitor-code` | Beryllium monitor code extent: exact base, size, end, rights, cacheability, owner, and mutation phase (monitor). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.monitor-data` | Beryllium monitor data extent: exact base, size, end, rights, cacheability, owner, and mutation phase (monitor). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.diagnostic` | Bounded diagnostic buffer extent: exact base, size, end, rights, cacheability, owner, and mutation phase (monitor). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.root-management` | Management Sv39x4 root-table pool: exact base, size, end, rights, cacheability, owner, and mutation phase (monitor). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.root-protected` | Protected Sv39x4 root-table pool: exact base, size, end, rights, cacheability, owner, and mutation phase (monitor). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.stack-management` | Management trusted stack: exact base, size, end, rights, cacheability, owner, and mutation phase (monitor). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.stack-protected` | Protected trusted stack: exact base, size, end, rights, cacheability, owner, and mutation phase (monitor). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.state-management` | Management saved-state area: exact base, size, end, rights, cacheability, owner, and mutation phase (monitor). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.state-protected` | Protected saved-state area: exact base, size, end, rights, cacheability, owner, and mutation phase (monitor). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.guest-code-management` | Management synthetic guest-code extent: exact base, size, end, rights, cacheability, owner, and mutation phase (management). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.guest-code-protected` | Protected synthetic guest-code extent: exact base, size, end, rights, cacheability, owner, and mutation phase (protected). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.private-management` | Management private page extent: exact base, size, end, rights, cacheability, owner, and mutation phase (management). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.private-protected` | Protected private page extent: exact base, size, end, rights, cacheability, owner, and mutation phase (protected). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.shared` | Directional shared-page extent: exact base, size, end, rights, cacheability, owner, and mutation phase (explicit channel). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.guards` | All guard, padding, and excluded extents: exact base, size, end, rights, cacheability, owner, and mutation phase (monitor/platform). | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from the exact board, firmware, load path, and linker plan; independently check alignment, containment, non-overlap, ownership, W^X, and mutation phase. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. No uncertain byte may be assigned to a domain or used for the monitor, page-table pools, trusted state, guest code, private pages, or the shared page. |
| `memory.gpa-management-private` | Management private GPA. | `0x40000000` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Preserve the accepted R5 semantic meaning and compare it in future H2/H3 evidence. | Any semantic change requires a reviewed plan revision. |
| `memory.gpa-protected-private` | Protected private GPA. | `0x40001000` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Preserve the accepted R5 semantic meaning and compare it in future H2/H3 evidence. | Any semantic change requires a reviewed plan revision. |
| `memory.gpa-shared` | Directional shared GPA. | `0x40002000` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Preserve management RW and protected R rights from accepted authority. | Any semantic or rights change requires a reviewed plan revision. |
| `memory.gpa-management-code` | Management synthetic code GPA. | `0x40010000` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Preserve the accepted synthetic payload address and R-X/W^X boundary. | Any change requires a reviewed plan revision and proof-impact analysis. |
| `memory.gpa-protected-code` | Protected synthetic code GPA. | `0x40011000` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Preserve the accepted synthetic payload address and R-X/W^X boundary. | Any change requires a reviewed plan revision and proof-impact analysis. |
| `memory.gpa-width` | Sv39x4 guest-physical width constraint. | `41 bits (GPA[40:0])` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Check every GPA and mapping before image construction. | An out-of-range GPA is a hard refusal. |
| `memory.page-size` | Leaf page size. | `4096 bytes` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Use only 4 KiB leaves in the fixed R8 scenario. | Huge pages or another leaf size require revision. |
| `memory.root-alignment` | Sv39x4 root alignment. | `16384 bytes` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Check both physical root pools and linked symbols. | Misalignment is a hard refusal before entry. |
| `memory.pool-size` | Per-domain complete page-table pool size. | `32768 bytes` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Retain the accepted eight-page pool shape and independently walk all used and spare pages. | A different pool shape requires revision. |
| `memory.root-count` | Number of G-stage roots. | `2` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Build exactly management and protected roots. | Any additional or missing root is a hard refusal. |
| `memory.mappings-per-root` | Leaf mappings per root. | `3` | `required-and-tested` | `nonblocking-deferred` | accepted-predecessor-fixed: Require exactly private, shared, and guest-code mappings in each root. | A fourth mapping or missing mapping requires revision. |
| `memory.cacheability` | CPU cacheability and memory-type profile for every experiment extent. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Obtain authoritative platform information and define later H1 read-only checks and H2 ordering observations. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `memory.normalized-inventory` | Offline normalized platform inventory contents and identity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Derive from exact retained board inputs with open host tooling, then independently validate every extent; extraction grants no authority. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `memory.fixed-proposal` | K3-instantiated fixed proposal and expected canonical state. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Instantiate only after exact physical frames are fixed while preserving accepted ownership, bindings, channel direction, and rights. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `memory.qemu-comparison-input` | Exact canonical QEMU comparison input for H3. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Choose either the semantically compatible accepted R5 record or an enumerated additive R8 QEMU profile; no run-time choice. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |

## Hart matrix

R8 remains one-active-X100-hart only. The exact participating ID, population, parking mechanism, and continuous check are unresolved and block H1.

| ID | Required fact | Current value | Disposition | Blocking gate | Resolution phase and plan | Fail-closed outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `hart.active-count` | Number of active X100 harts in the experiment. | `1` | `required-and-tested` | `h1-completion` | h0-policy-fixed-h1-observed: A later H1 must identify the participating hart and continuously account for every other X100 hart. | Any second active or unbounded hart stops R8. |
| `hart.participating-id` | Exact participating hart ID. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Bind the selected firmware handoff to one exact a0 hart ID and define the H1 cross-check. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `hart.population` | Complete delivered X100 hart population and IDs. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Obtain the exact board/SoC configuration and list every X100 hart that must be parked or unavailable. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `hart.nonparticipating-state` | Required state for every non-participating X100 hart. | `parked or unavailable under the exact firmware contract` | `disabled-and-checked` | `h1-completion` | h0-policy-fixed-h1-observed: Define a later H1 observation that accounts for each hart at entry and throughout characterization. | An unaccounted or executing hart stops R8. |
| `hart.parking-mechanism` | Exact firmware mechanism implementing parked or unavailable state. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Retain the exact source/configuration contract and define an independent observation where possible. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `hart.parking-check` | Exact observation for parked-state entry and continuity. | `UNKNOWN` | `stop` | `h0-acceptance` | before-h0-acceptance: Define a bounded read-only check that cannot wake another hart and is retained for every normative run. | H0 remains incomplete and not exit-ready; H1 and all K3 execution remain blocked until an exact value and retained provenance replace UNKNOWN. |
| `hart.a100-cluster` | A100 AI-core execution. | `not an R8 execution target` | `excluded` | `nonblocking-deferred` | h0-policy-fixed: Inventory only enough to ensure it cannot access experiment memory unexpectedly. | No R8 code may execute on A100. |
| `hart.ipi` | Interprocessor interrupts. | `none` | `excluded` | `nonblocking-deferred` | h0-policy-fixed: Keep IPI sources disabled and do not add an IPI path. | Any required IPI support is outside R8. |
| `hart.remote-fence` | Remote fence operations. | `none` | `excluded` | `nonblocking-deferred` | h0-policy-fixed: Use only local-hart HFENCE.GVMA in the fixed single-hart sequence. | Any remote-fence requirement indicates multicore behavior and stops R8. |
| `hart.unexpected-execution` | Unexpected hart execution against experiment memory. | `stop condition` | `stop` | `h1-entry` | all-r8-phases: Observe and retain the single-hart condition before and during every later authorized run. | Stop immediately and record r8-blocked; no CPU-isolation claim may be made. |

## Architectural feature matrix

These are planned H1/H2 observations, not results. Accessible unmodeled optional state is a core-design stop, not permission to weaken the context contract.

| ID | Required fact | Current value | Disposition | Blocking gate | Resolution phase and plan | Fail-closed outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `feature.misa` | Exact ISA identity visible to HS. | `UNKNOWN` | `required-and-tested` | `h1-completion` | authorized-h1-only: Read architecturally available identity and reconcile with exact firmware/platform documentation. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.hypervisor` | RISC-V H extension behavior required by the profile. | `UNKNOWN` | `required-and-tested` | `h1-completion` | authorized-h1-only: Probe required HS/VS CSRs and WARL behavior without VS entry; later H2 requires real VS execution. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.sv39x4` | Sv39x4 G-stage mode availability. | `UNKNOWN` | `required-and-tested` | `h1-completion` | authorized-h1-only: Probe hgatp Bare/Sv39x4 WARL behavior and reject any fallback mode. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.vmid-width` | Implemented VMID width. | `UNKNOWN` | `required-and-tested` | `h1-completion` | authorized-h1-only: Measure WARL width independently rather than relying only on documentation. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.vmid-value` | VMID used by the fixed runtime. | `0` | `required-and-tested` | `nonblocking-deferred` | h0-policy-fixed: Require exact HGATP readback with VMID zero. | A nonzero allocation scheme is later work. |
| `feature.hfence-gvma` | Local HFENCE.GVMA x0,x0 availability and ordering. | `UNKNOWN` | `required-and-tested` | `h2-entry` | authorized-h1-h2-only: H1 confirms instruction availability; H2 later checks root-write, fence, readback, and publication order. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.henvcfg` | henvcfg implemented bits and reset/handoff value. | `UNKNOWN` | `observed-assumption` | `h1-completion` | authorized-h1-only: Read and retain implemented bits; any bit that enables unmodeled guest state must be disabled and checked or stop. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.hstateen` | hstateen/mstateen availability, ownership, and handoff. | `UNKNOWN` | `observed-assumption` | `h1-completion` | authorized-h1-only: Record every implemented state-enable register visible to the exact firmware and HS profile. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.f` | Floating-point F state exposed to VS. | `UNKNOWN` | `disabled-and-checked` | `h1-completion` | authorized-h1-only: Show absence, firmware disablement, or checked state-enable denial before H2. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.d` | Floating-point D state exposed to VS. | `UNKNOWN` | `disabled-and-checked` | `h1-completion` | authorized-h1-only: Show absence, firmware disablement, or checked state-enable denial before H2. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.v` | Vector state exposed to VS. | `UNKNOWN` | `disabled-and-checked` | `h1-completion` | authorized-h1-only: Show absence, firmware disablement, or checked state-enable denial before H2. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.other-optional-state` | All other guest-accessible optional register state. | `UNKNOWN` | `stop` | `h1-completion` | authorized-h1-only: Enumerate every accessible state element; exclude/inhibit it or stop for a complete save/reset/restore plan revision. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.aia` | AIA, IMSIC, APLIC topology and enable state. | `UNKNOWN` | `disabled-and-checked` | `h1-completion` | authorized-h1-only: Record topology, GEILEN, guest files, pending and enable state; keep every source quiescent. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.sstc` | Sstc availability, delegation, and timer state. | `UNKNOWN` | `disabled-and-checked` | `h1-completion` | authorized-h1-only: Record delegation and enable state; ensure no guest timer or asynchronous event can enter the payload. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.counters-pmu` | Counter and PMU visibility and filtering. | `UNKNOWN` | `disabled-and-checked` | `h1-completion` | authorized-h1-only: Record mcounteren/hcounteren/scounteren and state-enable filtering; require VS denial. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.fault-metadata` | Guest-page-fault scause, sepc, stval, htval, and htinst behavior. | `UNKNOWN` | `required-and-tested` | `h2-entry` | authorized-h1-h2-only: Freeze the ratified mandatory/permitted-value matrix before H2 and never ignore a field dynamically. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.cache-hierarchy` | CPU cache hierarchy, shared levels, and ordering relevant to private/shared pages. | `UNKNOWN` | `required-and-tested` | `h2-entry` | authorized-h1-h2-only: Record authoritative topology and later observe required instruction/data visibility and shared-page ordering. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.cache-block-management` | Cache-block-management availability and required use. | `UNKNOWN` | `observed-assumption` | `h1-completion` | authorized-h1-only: Inventory support and determine whether the CPU-only scenario needs a bounded platform operation. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `feature.vendor-extensions` | Unsupported or vendor-specific architectural behavior affecting the profile. | `UNKNOWN` | `stop` | `h1-completion` | authorized-h1-only: Inventory all encountered behavior and stop if it adds unmodeled state or weakens an exact expectation. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |

## Security state, debug, external-master, and DMA matrix

PMP/Smepmp, lifecycle, debug, IOMMU/IOPMP, and external-master facts remain assumptions or deferred inventory until exact observations exist. No device or DMA workload is in scope.

| ID | Required fact | Current value | Disposition | Blocking gate | Resolution phase and plan | Fail-closed outcome |
| --- | --- | --- | --- | --- | --- | --- |
| `security.pmp-count` | Implemented PMP entry count and complete handoff state. | `UNKNOWN` | `observed-assumption` | `h1-completion` | authorized-h1-only: Retain every observable PMP entry, permissions, address mode, lock bit, and ownership; public documentation is context only. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.smepmp` | Smepmp/ePMP availability, mseccfg state, and ownership. | `UNKNOWN` | `observed-assumption` | `h1-completion` | authorized-h1-only: Use exact H1 M-mode firmware only if HS cannot observe the required machine state; retain source/configuration/bytes. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.hs-dram-reachability` | HS reachability of monitor and experiment DRAM under PMP/Smepmp. | `UNKNOWN` | `required-and-tested` | `h1-completion` | authorized-h1-only: Compare exact memory extents to retained PMP/Smepmp state before any H2 image. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.m-mode-reachability` | M-mode firmware reachability of experiment state. | `UNKNOWN` | `observed-assumption` | `h1-completion` | authorized-h1-only: Record the trusted firmware reachability boundary and any locked entries. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.secure-boot` | Secure-boot state for the exact cold-boot chain. | `UNKNOWN` | `observed-assumption` | `h1-completion` | authorized-h1-only: Record only documented observable state and exact firmware provenance; do not claim measured launch or integrity. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.lifecycle` | Lifecycle and eFuse lock state relevant to boot/debug. | `UNKNOWN` | `observed-assumption` | `h1-completion` | authorized-h1-only: Use documented interfaces and retain a redacted, non-secret state description. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.debug-trace` | Debug and trace enable/authentication/lock state. | `UNKNOWN` | `excluded` | `h1-completion` | authorized-h1-only: Record connection and observable state; treat external debug as a trusted/excluded bypass in the lab profile. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.system-bus-debug` | System-bus debug access to experiment DRAM. | `UNKNOWN` | `excluded` | `h1-completion` | authorized-h1-only: Determine whether the connected or enabled debug path can bypass CPU privilege checks and make the bypass explicit. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.external-masters` | Complete list of non-CPU bus masters that could access experiment DRAM. | `UNKNOWN` | `disabled-and-checked` | `h1-completion` | authorized-h1-only: Enumerate from exact board, firmware, DTB, and primary documentation; prove quiescence or default denial for the CPU-only claim. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.dma-workload` | Assigned device or DMA workload. | `none` | `excluded` | `nonblocking-deferred` | h0-policy-fixed: Do not assign a device or initiate DMA. | Any device or DMA requirement is outside R8 and requires a new reviewed plan. |
| `security.dma-coherency` | SoC DMA coherency behavior. | `UNKNOWN` | `observed-assumption` | `h1-completion` | authorized-h1-only: Record public and exact-board behavior but make no DMA-isolation or coherency claim. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.iommu` | IOMMU instances, ownership, access, and default state. | `UNKNOWN` | `deferred` | `h1-completion` | authorized-h1-only: Locate and characterize only; do not program a device domain. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.iopmp` | Documented IOPMP instances, ownership, access, lock, and default state. | `UNKNOWN` | `deferred` | `h1-completion` | authorized-h1-only: Locate and characterize every documented instance; do not infer nine active usable instances from public documentation. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.trng` | TRNG visibility and ownership. | `UNKNOWN` | `deferred` | `h1-completion` | authorized-h1-only: Inventory documented visibility only; the R8 payload has no entropy dependency. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.crypto-engines` | Crypto-engine visibility and ownership. | `UNKNOWN` | `deferred` | `h1-completion` | authorized-h1-only: Inventory only; do not expose engines or keys to either synthetic domain. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.keys` | Device keys, credentials, secrets, and private serial identifiers. | `must not be captured or retained` | `excluded` | `nonblocking-deferred` | h0-policy-fixed: Define redaction and capture boundaries before observation while preserving non-secret security-state facts. | If required evidence cannot be collected without prohibited data, R8 stops. |
| `security.ras-reri` | RAS, ECC/poison, and RERI routing state. | `UNKNOWN` | `deferred` | `h1-completion` | authorized-h1-only: Inventory documented state or retain NOT-RUN; no containment claim. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.interrupt-timer-quiescence` | No enabled interrupt, delegated/pending VS interrupt, or guest timer. | `UNKNOWN` | `disabled-and-checked` | `h1-completion` | authorized-h1-only: Record all relevant enables, pending state, delegation, and sources before H2. | If a later separately authorized H1 cannot observe and retain this fact, or observes an incompatible value, record r8-blocked or plan-revision-required; do not enter VS mode. |
| `security.cpu-originated-claim` | Maximum isolation claim if external-master quiescence/default denial is not established. | `CPU-originated accesses only` | `observed-assumption` | `nonblocking-deferred` | h0-policy-fixed: Carry the limitation into every future report unless stronger retained evidence exists. | Never claim whole-memory or DMA isolation from CPU-only evidence. |

## Immutable R0-R7 contract

The accepted predecessor target is consumed, never rewritten. During H0 and
all later R8 work:

1. every manifest path must remain byte- and mode-identical to the accepted R7
   target;
2. no accepted architecture-neutral invariant, root result, switch order,
   fault expectation, proof input, or evidence input may change;
3. no predecessor checker, source guard, launcher, acceptance interface, or
   pin may be adjusted to accommodate R8;
4. K3 physical layout and platform facts must remain additive and visibly
   separate from accepted common-core behavior; and
5. a required common-core change stops privileged R8 and requires a reviewed
   plan revision with proof, test, and acceptance impact.

The manifest does not claim that Git, SHA-256, the generation environment, or
this source is independently verified. A later H0 checker must independently
recompute the inventory from the exact target and refuse disagreement.

## Claim, assumption, trusted-boundary, and non-claim ledger

### Supported source claims

- The exact accepted-plan and H0-only authorization provenance is recorded.
- The canonical source contract enumerates exactly 24 maintained H0 paths,
  nine R8-A support sources, one generated-derivative prefix, and 25
  pre-execution bootstrap entries. The 33 non-generated paths form the
  candidate semantic projection.
- The static launcher rejects root real/effective/saved/filesystem uid or gid,
  mismatched ids, supplementary group zero, active/ambient capabilities, and
  every inherited descriptor above stderr, then sets and verifies
  `PR_SET_NO_NEW_PRIVS` before its first child.
- Before dynamic execution, descriptor-stable
  `O_NONBLOCK|O_NOFOLLOW` reads authenticate every bootstrap file and the
  exact Make, Node, Bash, Git, GCC, and `mkfifo` entry binaries by path, full
  special-bit-aware mode, byte size, owner, SHA-256, and absence of
  `security.capability`; the static launcher validates its own path, mode, and
  capability state separately.
- Descriptor 1 or 2 may not alias any authenticated entry. Before the first
  complete package-authentication pass proves both aliases absent, every
  launcher failure exits without writing stdout or stderr; alias rejection
  itself is always silent. Only then are fixed-prefix, constant-message,
  160-byte-bounded diagnostics enabled. The stdout regression and three early
  stderr append-redirection regressions prove exact authenticated bytes and
  SHA-256 remain unchanged for alias rejection, a bad target, a forbidden
  environment control, and a setgid launcher structure; FIFO substitution is
  bounded and nonblocking.
- The launcher remains resident as GNU Make's direct parent, supplies a
  nonce-bearing inherited `SOCK_SEQPACKET` handoff, invokes absolute
  `/usr/bin/make` with absolute `-C` and authenticated absolute `-f Makefile`,
  and propagates Make exit/signal state. Parse-time and recipe-time controls
  verify the actual parent executable, process relation, descriptor identity,
  nonce response, command line, working directory, and inherited
  `no_new_privs`; forged `BE_R8_*` variables do not authenticate raw Make.
- Built-in make rules/variables are disabled, Makefile restart/remaking is
  rejected, and hostile `GNUmakefile` and `makefile` files are ignored by the
  authenticated absolute `-f` invocation.
- `tests/r8/h0-claim-contract-v1.json` binds every byte of this Markdown file
  and the complete machine profile and semantic ledgers.
- The only parser is vendored Acorn 8.18.0 source under `tests/r8/`, with its
  exact MIT license, npm source integrity, tarball SHA-256, parser SHA-256, and
  byte size recorded; no root package dependency carries parser authority.
- Node modules are parsed against an exact AST contract. Source-bearing named
  re-exports and all export-all declarations are forbidden without resolving
  or executing the referenced module.
- Every machine-readable row has exactly one allowed disposition and one
  independently bound blocking gate.
- Every current `UNKNOWN` row has a nonempty fail-closed resolution plan, and
  the 81 genuine H0 blockers are distinct from later-gate characterization
  blockers.
- The accepted R0-R7 path families are inventoried at exact accepted R7 target
  `9bf22913d67e9b72286813cd5f7993a9ad3857a8` by path, mode, and file-byte
  SHA-256.
- Every exact Git identity read disables replacement objects, uses only
  strict object/index reads, sanitizes global/system/config environment, and
  rejects active replacement refs, dangerous local config/includes/filters,
  fsmonitor, attributes, material hooks, and material info excludes. Physical
  untracked enumeration uses only the source-contract exclusions. A clean-
  filter marker is never executed and an info-excluded rogue file cannot be
  hidden. The complete index must also be normal and byte-stable across
  read-only inspection; isolated regressions cover assume-unchanged,
  skip-worktree, fsmonitor-valid, intent-to-add, staged-only, unmerged, and a
  worktree mutation hidden from `git status`.
- All package writes are physically checked below `build/r8`; every output
  directory is euid-owned exact `0700`, every file is euid-owned,
  regular, single-link, and exact-mode, and symlink components and symlink
  final outputs are rejected.
- Launcher rebuilds set `HOME` and `TMPDIR` below `build/r8`; the retained GCC
  `-v` trace check rejects any `/tmp` or `/var/tmp` intermediate.
- The rejection contract contains 111 cases: 17 profile, 13 predecessor
  manifest, 11 report, 34 source/Git/AST/freeze, 12 bootstrap/launcher, 15
  Make/control, and nine output-path cases. The path cases cover
  pre-existing `0755`, `0770`, and `0777` directories, a world-writable
  nested parent, synthetic wrong ownership, a mode change after validation
  but before write, hostile cleanup, and two symlink escapes; every sentinel
  remains unchanged.
- No K3 execution is performed by this package.

### Assumptions and trusted boundaries

- The accepted Git target and its object database are available and authentic
  for manifest recomputation.
- Public K3 primary sources are correct only as planning context; they do not
  establish delivered-unit state.
- Future board labels, firmware bytes, open-source provenance, lab procedures,
  tool identities, physical wiring, and observations require human-controlled
  acquisition and review.
- Future compilers, linkers, firmware, hardware, capture host, cabling,
  canonicalizer, checkers, and procedure remain trusted at their stated cut
  points.
- The launcher hashes the exact host entry binaries. Dynamically loaded
  root-owned shared objects remain explicit host assumptions, including the
  `libnode` implementation reached through the small `/usr/bin/node-22` entry
  binary; entry-binary hashing is not a closure hash of those libraries.
- The exact host toolchain lock is host-specific. Reproduction requires the
  recorded paths, owners, modes, sizes, hashes, shared-object assumptions, and
  GCC trace behavior; a different host must rederive and deliberately repin
  the complete lock in a reviewed H0 change rather than silently substituting
  tools.
- Firmware hart parking, M-mode ownership, and external-master quiescence are
  trusted unless later independently enforced and measured.
- The static launcher detects path replacement during each descriptor-stable
  read and performs a second complete pass immediately before forking Make.
  Linux ownership prevents this uid from replacing the pinned root-owned tool
  paths. A concurrent process with the **same repository-owner uid** could
  still rename a repository path after that final pass and before a later
  Make, Node, or Bash pathname open; the H0 host package does not claim to
  isolate mutually hostile same-uid processes. Run the gate without such a
  concurrent writer.
- Node output confinement likewise assumes no concurrent same-uid rename
  between its checked path-component walk and use. Exact `0700` private
  directories exclude other-uid and group writers; existing symlinks,
  non-private modes, wrong ownership, multiply linked files, and ordinary
  pre-launch tampering are rejected. This same-effective-uid rename is the
  only disclosed output-path race.

### Explicit non-claims

This H0 source does not claim:

- that a physical board has been delivered, selected, powered, reset, loaded,
  or executed;
- any exact board, silicon, DRAM, firmware, DTB, load-address, SBI, lifecycle,
  PMP/Smepmp, optional-state, debug, cache, IOMMU/IOPMP, or external-master
  fact;
- that a normative toolchain, flashing path, reset path, or capture path is
  selected or pinned;
- that H0 is complete, exit-ready, reviewed, or accepted;
- authorization for H1, H2, H3, H4, K3 execution, root integration, pin
  refresh, Linux, multicore, device, DMA, policy, publication, or a successor;
- hardware validation, hardware isolation, DMA isolation, whole-memory
  isolation, secure boot, measured launch, attestation, debug lockdown,
  production support, C refinement, whole-system proof, or formal
  verification of Beryllium; or
- that public K3 documentation, candidate board names, another K3 board, QEMU,
  or a cached transcript describes the delivered unit.

## H0 exit criteria and current result

| # | Exit criterion | Current result |
| ---: | --- | --- |
| 1 | Every identity and expected value is exact or explicitly `UNKNOWN`. | Met for source shape; many identity-critical facts remain `UNKNOWN`. |
| 2 | Every `UNKNOWN` has a fail-closed observation or resolution plan. | Met for source shape. |
| 3 | No unknown physical extent is assigned to a domain. | Met. |
| 4 | No closed or hosted-only tool is normative. | Met; exact normative tools remain `UNKNOWN`, and TitanTools is excluded. |
| 5 | Every non-participating hart has a planned parked-state check. | Not met: exact hart population, parking mechanism, and check are `UNKNOWN`. |
| 6 | Every possible external master has a quiescence/default-deny disposition. | Not met: the exact delivered-board inventory is `UNKNOWN`. |
| 7 | Optional architectural state has exclusion, reset, save/restore, or stop disposition. | Met for source shape; observation is `NOT-RUN`. |
| 8 | The planned claim remains single-board, single-hart, CPU-originated, and synthetic. | Met. |
| 9 | A responsible human accepts one exact H0 commit before H1 begins. | Not met. |
| 10 | Exact board, normative load path, selected open tools, physical memory map, and exact future privileged path inventory are supplied. | Not met. |

Therefore:

```text
r8_h0_exit=not-met
r8_h0_complete=not-claimed
r8_h0_acceptance=not-reviewed
h0_acceptance_blockers=81
h1_completion_blockers=33
h2_entry_blockers=3
```

H0 readiness remains blocked by the 81 genuine unresolved H0 facts, unmet exit
criteria, and absent exact-commit acceptance. The 33 H1-completion and three
H2-entry blockers are separately reported and do not inflate the H0 blocker
count. H1 cannot be authorized or started until the exact board, load path,
selected open tools, required physical/profile facts, and exact H1 path
inventory are supplied and one exact H0 commit is accepted.

## H1 and later stop boundary

H1 through H4 remain unauthorized. No H1 command, privileged source, image,
probe, reset, board load, or capture may be created or run under this H0-only
authorization.

Even after exact H0 acceptance, later work must stop before:

- entering H1 without separate responsible-human authorization;
- using a board, firmware image, DTB, tool, load path, address, or path not in
  the accepted H0 profile;
- entering VS mode during H1;
- proceeding with an unaccounted or active second hart;
- proceeding with accessible optional state not covered by exclusion,
  reset/save/restore, or an accepted revision;
- modifying an accepted R0-R7 path or needing a common-core change;
- adding a device, DMA path, guest SBI, interrupt/timer service, policy,
  privileged/runtime parser, allocator, scheduler, or multicore behavior;
- substituting a proprietary, hosted-only, unpinned, cached, or other-board
  result for normative local open evidence; or
- relaxing an exact fault, binding, fence, publication, or claim expectation.

A stop is useful design information. It is not permission to improvise an
implementation.

## Current state fields

```text
r7_acceptance=accepted-by-review-record
r7_accepted_commit=9bf22913d67e9b72286813cd5f7993a9ad3857a8
r8_plan=accepted-exact-target
r8_plan_target=7d0f0cbf8e1f457f1094aa5049d577cf4e164ae5
r8_plan_revision_r8a=accepted-exact-target
r8_plan_revision_r8a_target=8fa9d672cfcfb81ab68d9ed9553a5af48b884932
r8_h0_implementation_base=1f6109f0d0371eb3707e296c3416e8c55235683e
r8_implementation_authorization=authorized-h0-only
r8_h0_status=implementation-authorized-h0-local-not-reviewed
r8_h0_source=present-local-not-reviewed
r8_h0_candidate=local-uncommitted-not-reviewed
r8_h0_profile=blocking-unknowns-present
r8_h0_exit=not-met
r8_h0_acceptance=not-reviewed
r8_h1_authorization=not-authorized
r8_h1=not-started
r8_h2=not-started
r8_h3=not-started
r8_h4=not-started
r8_hardware_execution=NOT-RUN
r8_root_integration=deferred-not-authorized
r8_publication=blocked
```

## Primary references

Project sources:

- [Accepted R8 plan](single-hart-runtime-r8-plan.md)
- [R8 plan review, acceptance, and H0 authorization record](single-hart-runtime-r8-plan-review-summary.md)
- [RISC-V and K3 security-hardware roadmap](riscv-security-hardware.md)
- [Open tooling policy](open-tooling.md)
- [R0 fixed-profile freeze](single-hart-runtime-r0-freeze.md)
- [R7 bounded evidence](single-hart-runtime-r7-evidence.md)
- [R7 review and acceptance record](single-hart-runtime-r7-review-summary.md)

Tracked primary public context:

- SpacemiT K3 documentation: <https://github.com/spacemit-com/docs-chip>
- K3 datasheet: <https://raw.githubusercontent.com/spacemit-com/docs-chip/main/en/key_stone/k3/k3_docs/k3_ds.md>
- K3 security documentation: <https://github.com/spacemit-com/docs-chip/blob/main/en/key_stone/k3/k3_docs/k3_usermanual/15_security.md>
- Upstream K3 Device Tree series: <https://lore.kernel.org/linux-riscv/20260115-k3-basic-dt-v5-0-6990ac9f4308@riscstar.com/>
- RISC-V Hypervisor Extension: <https://docs.riscv.org/reference/isa/priv/hypervisor.html>
- RISC-V Privileged Architecture: <https://docs.riscv.org/reference/isa/priv/priv-index.html>
- RISC-V SBI specification: <https://github.com/riscv-non-isa/riscv-sbi-doc>
- OpenSBI: <https://github.com/riscv-software-src/opensbi>

These references do not replace exact delivered-board observations.
