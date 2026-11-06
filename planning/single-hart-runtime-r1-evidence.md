<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium single-hart runtime R1 pure-C mechanism evidence

## Status and claim boundary

R1 is the pure-C mechanism package in the accepted
[bounded single-hart runtime plan](single-hart-runtime-plan.md). The local
implementation now present in this worktree is complete, and
`make -C tests r1-check` / `./be r1-check` pass with strict GCC and Clang host
builds, adversarial state-machine/checker tests, byte-identical deterministic
reports, report semantic checking, and retained source/artifact evidence.

R1 is **non-privileged pure restricted-C only**:

```text
copy -> validate -> canonicalize -> seal -> abstract derive -> report -> terminal failure
```

Precise limits:

- R1 links **no** Beryllium image and adds **no** assembly, boot path,
  page-table backend, privileged instruction, trap path, or Beryllium QEMU
  execution.
- The full profile has **13 resources**, including **2 R-X guest-code
  operational-extension resources**, **6 authorities**, and **2 abstract
  derived roots with 3 mappings each**. These roots are **not** Sv39x4 page
  tables and do not start R2.
- R1 is **not** a Model 0.2 refinement, formally verified, hardware
  validated, or a production hypervisor. The configuration identity is for
  deterministic reporting/equivalence only, not integrity measurement or
  attestation.
- Responsible-human review accepted exact R1 mechanism commit
  `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28. R2 is next by
  dependency and has not started; acceptance did not authorize tagging,
  pushing, public release, or R2.
- QEMU Beryllium and K3 hardware remain **NOT RUN**. Retained Helium evidence
  does **not** validate R1. Public release remains **blocked**.

## 1. Component and API tour

### Fixed-profile contracts

- `include/be/types.h` — bounded scalar and size types.
- `include/be/manifest.h` — fixed-profile inventory, copied proposal,
  canonical sealed state, abstract derived enforcement, deterministic checker
  results, and reporting-only configuration identity contract.
- `include/be/state.h` — runtime phase machine and deterministic report
  summary API.
- `include/be/r1-config.h` — immutable accessors for the frozen R1 full-profile
  inventory and copied proposal.

### Restricted-C implementation

- `virt/be/r1-config.c` — the full fixed profile at the accepted R0 physical
  addresses.
- `virt/be/manifest.c` — inventory checking, proposal canonicalization,
  deterministic identity, and abstract root derivation.
- `virt/be/state.c` — fail-closed runtime phase machine for copied, validated,
  sealed, derived, and reported state.

### Host evidence tools

- `tests/r1/r1-check.c` — positive flow, adversarial validation, integrity,
  wrong-phase, and terminal fail-closed coverage.
- `tests/r1/r1-report.c` — deterministic JSON report generator.
- `tests/r1/check-report.mjs` — semantic checker for the emitted report.
- `tests/r1/generate-evidence.sh` — retained source/tool/artifact identity
  bundle under `build/r1/evidence/`.
- `tests/Makefile` — `r1-test`, `r1-report`, `r1-evidence`, and `r1-check`.
- `./be` — stable wrapper entry points for `r1-check` and `r1-evidence`.

## 2. Exact fixed full profile

The local R1 mechanism consumes the accepted R0 physical layout and extends
the Model 0.2 eleven-resource projection to the exact thirteen-resource
runtime profile:

| Resource set | Count | Notes |
| --- | --- | --- |
| Monitor code/data | 2 | trusted monitor-owned extents |
| Root-table storage | 2 | one per domain, still abstract in R1 |
| Trusted stacks | 2 | one per domain |
| Saved-state storage | 2 | one per domain |
| Private data pages | 2 | one management, one protected |
| Shared page | 1 | directional management-RW to protected-R channel |
| Guest-code pages | 2 | R-X operational-extension resources |
| **Total** | **13** | fixed full profile |

Canonical authority is equally fixed:

| Domain | Authorities |
| --- | --- |
| management | private `rw`, shared `rw`, guest-code `rx` |
| protected | private `rw`, shared `r`, guest-code `rx` |
| **Total** | **6** |

The derived output is abstract enforcement only:

| Root | Domain | Mappings |
| --- | --- | --- |
| 101 | management | private `rw`, shared `rw`, guest-code `rx` |
| 102 | protected | private `rw`, shared `r`, guest-code `rx` |
| **Total** | **2 roots** | **6 mappings** |

The current deterministic report,
`build/r1/reports/runtime.json`, records the fixed configuration identity
`0x771e1e75110201ac` and the exact domain/frame/authority/root structure for
this profile.

## 3. Phase and failure contract

`include/be/state.h` and `virt/be/state.c` define the R1 phase machine:

```text
empty
  -> inventory-copied
  -> proposal-copied
  -> validated
  -> sealed
  -> derived
  -> failed
```

Key guarantees enforced by the host tests:

- copied inventory and proposal are non-authoritative input only;
- canonical state becomes authoritative exactly once, at `seal`;
- derived enforcement is produced only from sealed canonical state;
- pre-seal failures zero canonical state, derived state, and retained
  identities;
- post-seal failures zero derived state and move to terminal failure;
- failed state is sticky for every public R1 API, with no API reset or
  recovery transition;
- fresh storage is created with `BE_RUNTIME_INITIALIZER`, which is an
  initialization contract rather than a state-machine transition; and
- report output is zeroed before work and remains zero on failure.

R1 exposes its bounded state structure to later trusted packages and host
evidence. A trusted C caller therefore owns the storage and could overwrite or
discard any instance out of band. R1 does not claim to prevent that memory
operation. Its enforceable property is that no R1 API transitions a failed
instance back to an earlier phase. Later platform integration must treat the
instance as discarded and follow the accepted terminal-shutdown path; it must
not use fresh initialization as guest-visible or in-run recovery.

## 4. Adversarial coverage

`tests/r1/r1-check.c` covers:

- positive end-to-end copy/validate/seal/derive/report flow;
- source-vocabulary and proposal-order independence, with byte-identical
  canonical and derived state;
- null-pointer and wrong-phase failures for every runtime API;
- inventory rejection for incomplete, unaligned, zero-sized, overflowing,
  duplicated, overlapping, and composition-invalid resources;
- proposal-envelope rejection for direct-authority publication, closure
  mismatch, count mismatch, duplicate resource requests, and invalid metadata;
- domain/root/stack/saved-state binding rejection;
- private/shared/guest-code ownership and rights rejection;
- directional channel and shared-backing rejection;
- direct-derive, seal-integrity, derive-integrity, and report-integrity
  fail-closed behavior with zero publication; and
- terminal failed-state stickiness with no public R1 API recovery transition.
  The host harness starts each independent case with fresh local storage; that
  is not recovery evidence.

The current passing host output is:

```text
BE_R1_CHECK: PASS resources=13 authorities=6 roots=2 mappings=6
BE_R1_REPORT: PASS
Beryllium R1 evidence: PASS
Beryllium R1 pure-C mechanism: PASS
```

## 5. Deterministic report and retained evidence

`make -C tests r1-report`:

1. builds GCC and Clang host report tools with strict warnings;
2. emits compiler-specific JSON;
3. compares the two byte-for-byte;
4. retains `build/r1/reports/runtime.json`; and
5. runs `tests/r1/check-report.mjs` for structural and semantic validation.

`make -C tests r1-evidence` retains:

- `build/r1/evidence/source-state.txt`
- `build/r1/evidence/tool-versions.txt`
- `build/r1/evidence/source.sha256`
- `build/r1/evidence/artifacts.sha256`
- `build/r1/evidence/claim-status.txt`

The retained claim ledger records:

```text
r1_pure_c_mechanism=complete
r1_acceptance=accepted
r1_accepted_commit=a6e0bb178c10a7e68c9447a8e58affb94b8ecadb
r1_accepted_at=2026-07-28
r1_accepted_mechanism_match=yes
privileged_code=no
linked_image=no
full_profile_resources=13
guest_code_overlays=2
canonical_authorities=6
derived_roots=2
derived_mappings=6
model_0_2_refinement=no
terminal_api_recovery=no
caller_storage_integrity=trusted-assumption
terminal_shutdown_integration=not-implemented
qemu_beryllium_result=NOT-RUN
hardware_validation=NOT-RUN
r2_status=not-started
public_release=blocked
```

## 6. Commands and wrapper status

Supported direct commands:

```sh
make -C tests r1-test
make -C tests r1-report
make -C tests r1-evidence
make -C tests r1-check
make check
```

Current wrapper surface:

```sh
./be r1-check
./be r1-evidence
```

Wrapper status is intentionally narrower than the raw test graph: `./be` does
not currently expose separate `r1-test` or `r1-report` commands.

## 7. Claim ledger

What R1 supports saying now:

- R1 implementation is complete locally and `make -C tests r1-check` /
  `./be r1-check` pass with strict GCC and Clang host builds, adversarial
  state-machine/checker tests, byte-identical deterministic reports, report
  semantic checking, and retained source/artifact evidence.
- Responsible-human review accepted exact mechanism commit
  `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` on 2026-07-28.
- `tests/r1/check-acceptance.sh` requires the current R1 mechanism, build, and
  host-test inputs to match that exact commit before accepted-status evidence
  can be emitted.
- R1 is non-privileged pure restricted-C only: copy, validate, canonicalize,
  seal, abstract derive, report, terminal failure.
- Full profile: 13 resources including 2 R-X guest-code operational-extension
  resources; 6 authorities; 2 abstract derived roots with 3 mappings each.
  These are **not** Sv39x4 tables and do not start R2.
- No linked image, assembly, boot, page-table backend, privileged
  instruction, or Beryllium QEMU execution is present.
- Model 0.2 and Rocq proof claims do not transfer; R1 is not a proved
  refinement, formally verified, hardware validated, or production
  hypervisor.
- Configuration identity is deterministic reporting/equivalence only, not
  integrity measurement or attestation.
- Terminal failure is enforced across the R1 API. Caller-owned C storage
  integrity and the future platform shutdown response remain explicit trusted
  assumptions.
- Retained Helium evidence does not validate R1.

What R1 does **not** support saying:

- that acceptance applies to any commit other than
  `a6e0bb178c10a7e68c9447a8e58affb94b8ecadb` or authorizes tagging, pushing,
  public release, or R2;
- that R1 starts R2, builds Sv39x4 tables, boots via OpenSBI, or runs in QEMU;
- that Beryllium QEMU or K3 hardware results exist; or
- that public release is approved or unblocked.

## 8. Explicit R2 boundary

R2 remains the Sv39x4 backend package from the runtime plan. It depends on
this locally complete R1 mechanism and has **not** started. No separately
recorded responsible-human acceptance for R1 or implementation start for R2 is
currently known in the maintained planning sources.

R1 therefore stops before:

- fixed page-table storage consumption beyond abstract root identifiers;
- leaf walkers or PTE encoding;
- `HGATP` construction or writes;
- fences, traps, boot, or guest entry;
- image linking or exact wrapper bytes; and
- any Beryllium QEMU or hardware evidence.

## Primary references

- [Bounded single-hart runtime plan](single-hart-runtime-plan.md)
- [R0 fixed profile and layout freeze](single-hart-runtime-r0-freeze.md)
- [Implementation plan](implementation-plan.md)
- `include/be/manifest.h`, `include/be/state.h`, `include/be/r1-config.h`
- `virt/be/manifest.c`, `virt/be/state.c`, `virt/be/r1-config.c`
- `tests/r1/r1-check.c`, `tests/r1/r1-report.c`,
  `tests/r1/check-report.mjs`, `tests/r1/generate-evidence.sh`
