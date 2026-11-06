<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# KVM0 K0-S source-owner preparation authorization record

**Document status:** `draft-not-reviewed`. This maintained-source draft is
based on Beryllium documentation HEAD
`478d5886e8dc261546e3373421e0ab428062f82a`. It has no exact documentation
target, Git tree, or review decision and must not be cited as an accepted or
immutable record until those identities exist and responsible-human review
occurs.

This draft records the exact session instructions that authorized bounded
KVM0 K0-S source-owner preparation, supplied the authoritative workspace, and
allowed the already bounded work to continue. It also records the completed
local source-owner preparation package at its current file/mode/hash identity.
That package remains mutable local input with
`profile_review_status=not-reviewed`; it is not retained K0-S readiness or
acceptance evidence. This draft records no K0-S readiness, source acceptance,
destination import, real selftest or K0-X execution, hardware result, or KVM0
result.

The governing accepted boundaries remain:

```text
kvm0_plan_target=5227266ceddb664a1595e22e5a92da57a013652f
kvm0_k0i_accepted_target=abd092a1f2734c720a205803c29496fe2245b0ef
kvm0_k0s_document_status=draft-not-reviewed
kvm0_k0s_documentation_target=none
profile_review_status=not-reviewed
```

## 1. Exact session decision evidence

At `2026-09-28T00:17:59.413Z`, the responsible human supplied:

```text
Fleet deployed: proceed with K0-S per above
```

For this record, `per above` is bounded only by Gate K0-S in accepted KVM0
Plan revision K0-A target
`5227266ceddb664a1595e22e5a92da57a013652f`: source-owner preparation,
read-only audit, and evidence-profile drafting. Accepted K0-I target
`abd092a1f2734c720a205803c29496fe2245b0ef` remains a separate
destination-side offline-tooling boundary. K0-I implementation authority is
not merged with K0-S source-owner authority.

At `2026-09-28T02:06:12.937Z`, the responsible human supplied the exact
authoritative source-owner workspace locator. The accepted K0-A privacy rule
requires that private locator to be omitted from committed Beryllium
documentation. This draft therefore assigns the stable project-local
identifier:

```text
source_workspace_id=k0s-source-owner-workspace-1
source_workspace_supplied_at=2026-09-28T02:06:12.937Z
locator_disposition=responsible-human-supplied-private-session-local-not-retained-in-committed-documentation
```

The exact private locator remains session-local and publication-excluded.

At `2026-09-28T02:07:09.427Z`, the responsible human supplied:

```text
continue
```

That instruction allowed the bounded read-only audit and profile drafting to
continue from the supplied workspace. At `2026-09-28T03:15:09.437Z`, the
responsible human supplied the conditional instruction:

```text
if repairable, proceed to repair
```

That conditional instruction permits repair of K0-S preparation/profile
draft material only when repairable within the accepted boundary. It grants
no source import, source-owner repository modification, selftest or K0-X
execution, serial or hardware access, readiness, acceptance, result, or
publication authority.

## 2. Current maintained status

```text
kvm0_gate_k0p=satisfied-by-exact-plan-acceptance
kvm0_gate_k0i=satisfied-by-explicit-authorization
kvm0_k0i_scope=offline-tooling-only
kvm0_k0i_implementation=accepted
kvm0_gate_k0s=authorization-satisfied-local-preparation-recorded-readiness-not-met
kvm0_k0s_authorization=authorized-by-session-instruction
kvm0_k0s_authorization_timestamp=2026-09-28T00:17:59.413Z
kvm0_k0s_scope=source-owner-preparation-read-only-audit-and-profile-drafting-only
kvm0_k0s_authorization_record=planning/k3-kvm0-k0s-authorization-record.md
kvm0_k0s_authorization_record_status=draft-not-reviewed
kvm0_k0s_documentation_target=none
kvm0_k0s_source_workspace_id=k0s-source-owner-workspace-1
kvm0_k0s_source_workspace_locator_disposition=responsible-human-supplied-private-session-local-not-retained-in-committed-documentation
kvm0_k0s_source_workspace_supplied_at=2026-09-28T02:06:12.937Z
kvm0_k0s_source_workspace_access=opened-read-only-for-audit
kvm0_k0s_continue_timestamp=2026-09-28T02:07:09.427Z
kvm0_k0s_conditional_repair_timestamp=2026-09-28T03:15:09.437Z
kvm0_k0s_source_preparation=completed-local-profile-package-current-bytes-not-reviewed
kvm0_k0s_source_import=not-performed
kvm0_k0s_profile_package_documentation_integration=complete-current-local-bytes-only
kvm0_k0s_profile_package_id=k0s-source-owner-profile-v1
kvm0_k0s_profile_package_locator_disposition=responsible-human-supplied-private-session-local-not-retained-in-committed-documentation
kvm0_k0s_profile_package_path_evidence=none-file-mode-checksum-identities-only
kvm0_k0s_profile_package_git_containment=none
kvm0_k0s_profile_package_immutable=no-current-local-bytes-only
kvm0_k0s_profile_package_file_count=35
kvm0_k0s_profile_package_inventory_entries=41
kvm0_k0s_profile_package_files_modes_sha256=f8f130dbcbddfa557298bab1a9bcac859a4ec8af8adb219d271e467c52ffa5db
kvm0_k0s_profile_package_sha256sums_entries=34
kvm0_k0s_profile_package_sha256sums_sha256=57d0753ab55333ca29198d894e176c5a270e52747e29303b6ad1d2bb8cd606b3
kvm0_k0s_profile_package_source_profile_sha256=aaa4b83d216cd932fd77c32230dded6ff206f6224224670bcac2169bd5a36238
kvm0_k0s_profile_package_restricted_map_mode=0600
kvm0_k0s_profile_package_restricted_map_bytes=42570
kvm0_k0s_profile_package_restricted_map_sha256=eb734dc9dad08a2ec5e73d4f5b50a4fe59ed9100580dcf0490687dfb2f8943c4
kvm0_k0s_profile_package_restricted_mapping_coverage=complete-43-of-43
kvm0_k0s_profile_package_identity_status=remediated-current-bytes-integrated-not-reviewed
kvm0_k0s_profile_static_check=PASS
kvm0_k0s_profile_controller_self_hash_preflight=PASS
kvm0_k0s_profile_host_only_fake_tests=PASS-25
kvm0_k0s_profile_review_status=not-reviewed
kvm0_k0s_destination_import=NOT-RUN
kvm0_k0s_destination_install=NOT-RUN
kvm0_k0s_real_selftests=NOT-RUN
kvm0_k0s_serial_endpoint=UNKNOWN
kvm0_k0s_serial_access=NOT-RUN
kvm0_k0s_readiness=not-ready
kvm0_k0s_future_k0i_source_branch_label_literal=main
kvm0_k0s_future_k0i_not_run_profile_state_literal=source-ready-not-run
kvm0_k0s_future_k0i_literals_are_current_readiness=no
kvm0_k0s_source_base=a5f72fd298f6bd02e6d30599dafb43cfa16576b6
kvm0_k0s_discovery_candidate_commit=c1c7e254143f99d4ad3cdbf25021a76364d6d75a
kvm0_k0s_discovery_candidate_tree=a5f77b5acef26d8975fe756512edbd2413fa1239
kvm0_k0s_discovery_candidate_parent=405a74dd4f1afc793b52f8589ccdcda5ee515f8e
kvm0_k0s_discovery_commit_count=14
kvm0_k0s_discovery_changed_path_count=11
kvm0_k0s_candidate_worktree=clean-detached
kvm0_k0s_candidate_status_porcelain_v1_bytes=0
kvm0_k0s_candidate_status_porcelain_v1_sha256=e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
kvm0_k0s_candidate_ref_status=unreferenced-object
kvm0_k0s_candidate_containing_checked_local_branches=0
kvm0_k0s_candidate_containing_checked_tags=0
kvm0_k0s_authorized_checkout_relation=unrelated-to-discovery-candidate
kvm0_k0s_clean_immutable_referenced_source_target=none
kvm0_k0s_discovery_candidate_status=unaccepted-unretained-preparation-input
kvm0_gate_k0x=blocked-not-authorized
kvm0_gate_k0r=blocked-no-result
kvm0_result=NOT-RUN
beryllium_k3_hardware=NOT-RUN
r8_k3_hardware=NOT-RUN
development_kernel_bsp=UNDECIDED
publication=blocked
```

`k0s-source-owner-workspace-1` has been supplied and opened for bounded
read-only audit. `k0s-source-owner-profile-v1` is complete at the current
external bytes, and this maintained draft records its deterministic
file/mode/checksum identities. The package is outside Git, remains mutable,
and is not reviewed. No source bytes or package bytes have been imported into
Beryllium, and no readiness condition is satisfied.

## 3. Decision summary

| Field | Content |
| --- | --- |
| Accepted plan | Exact KVM0 Plan revision K0-A target `5227266ceddb664a1595e22e5a92da57a013652f`, accepted 2026-09-25 |
| Accepted destination tooling | Exact K0-I offline-tooling target `abd092a1f2734c720a205803c29496fe2245b0ef`, accepted 2026-09-26; separate from K0-S authority |
| Authorization | `Fleet deployed: proceed with K0-S per above` at `2026-09-28T00:17:59.413Z` |
| Source-owner workspace | `k0s-source-owner-workspace-1`, supplied at `2026-09-28T02:06:12.937Z`; exact locator intentionally omitted under the accepted privacy rule |
| Continue instruction | `continue` at `2026-09-28T02:07:09.427Z` |
| Conditional repair | `if repairable, proceed to repair` at `2026-09-28T03:15:09.437Z`; limited to repairable preparation/profile draft material |
| Local preparation package | `k0s-source-owner-profile-v1`; 35 files; 41 path/type/mode rows; current `FILES.modes` SHA-256 `f8f130dbcbddfa557298bab1a9bcac859a4ec8af8adb219d271e467c52ffa5db`; current 34-entry `SHA256SUMS` SHA-256 `57d0753ab55333ca29198d894e176c5a270e52747e29303b6ad1d2bb8cd606b3`; source-profile SHA-256 `aaa4b83d216cd932fd77c32230dded6ff206f6224224670bcac2169bd5a36238`; private locator omitted, outside Git, and not immutable |
| Restricted provenance | Exact-minimum, access-controlled, hash-bound, publication-excluded, and not printed; mode `0600`, 42,570 bytes, SHA-256 `eb734dc9dad08a2ec5e73d4f5b50a4fe59ed9100580dcf0490687dfb2f8943c4`, with complete 43-of-43 mapping coverage |
| Current work | Bounded local source-owner preparation package remediated and status-integrated at its current bytes; `profile_review_status=not-reviewed` |
| Source import and execution | No source or package import or destination install; real KVM selftests, K0-X, serial, and hardware are `NOT-RUN` or unauthorized; 25 host-only fake tests and the controller self-hash preflight are preparation checks only |
| K0-S readiness | Not ready; candidate containment is zero checked local branches and zero checked tags, the authorized checkout is unrelated, no clean immutable referenced source target exists, retained inputs and operational identities are missing, no approved immutable route exists, and no destination import/install, real execution, or readiness decision occurred |
| Document state | Draft, not reviewed, and without an exact documentation target or tree |
| Successor status | K0-X, K0-R, K0-G, B0, B1, R8 successors, and H1-H4 remain blocked or unauthorized |
| Publication | Push, tag, publication, release, migration, archival, and upstream submission remain blocked |

## 4. Authorized work boundary

The supplied workspace may be used only for K0-S source-owner preparation:

- verify the exact workspace and source relation through read-only inspection;
- audit the proposed base, candidate, ordered 14-patch relation, source and
  configuration identities, and changed-path/mode inventory;
- draft or conditionally repair the bounded K0-S profile and required
  manifests without importing source bytes into Beryllium;
- draft the exact 16-command KVM selftest profile, including the one proposed
  skip identity, marker, and reason, without executing it;
- draft source, patch, tool, firmware, artifact, command, provenance, board,
  capture, selftest, matrix, result, and recovery manifest structures;
- draft the restricted provenance map and publication-safe opaque identifiers;
- bind identities that can be established by read-only audit without K3,
  serial, selftest, guest, or hardware execution; and
- reserve accepted K0-I tooling for later destination-side offline checking of
  explicitly supplied immutable input.

The source-owner repository remains read-only for this bounded work. Every
profile statement must be derived from the supplied workspace and accepted
plan. A changed source relation, broader path boundary, import requirement,
execution need, or hardware need is a stop requiring separate review.

## 5. Verified local source-owner preparation package

The completed bounded repair is identified as
`k0s-source-owner-profile-v1`. Its exact private session-local locator is
intentionally omitted under the accepted privacy rule and is not evidence.
The package is not inside a Git worktree. It therefore has no commit or tree
identity and must not be described as committed, immutable, accepted, or
retained evidence. The following file/mode/checksum identities bind only the
current bytes inspected on 2026-09-28:

| Property | Verified current value |
| --- | --- |
| Regular files | `35` |
| Closed path/type/mode inventory | `41` rows in `FILES.modes`: 35 files and six directories |
| `FILES.modes` SHA-256 | `f8f130dbcbddfa557298bab1a9bcac859a4ec8af8adb219d271e467c52ffa5db` |
| `SHA256SUMS` entries | `34`, covering every regular package file except `SHA256SUMS` itself |
| `SHA256SUMS` SHA-256 | `57d0753ab55333ca29198d894e176c5a270e52747e29303b6ad1d2bb8cd606b3` |
| `source-profile-v1.json` SHA-256 | `aaa4b83d216cd932fd77c32230dded6ff206f6224224670bcac2169bd5a36238` |
| Restricted provenance map | Mode `0600`; 42,570 bytes; SHA-256 `eb734dc9dad08a2ec5e73d4f5b50a4fe59ed9100580dcf0490687dfb2f8943c4`; complete 43-of-43 mapping coverage |
| Checksum verification | `PASS` with strict status checking |
| Controller self-hash preflight | `PASS`; direct controller tampering fails before any session output is created |
| Host-only fake tests | `PASS`; 25 tests |
| Profile review | `profile_review_status=not-reviewed` |

The restricted provenance map is described only by its mode, byte count,
hash, and coverage count. Its exact-minimum human provenance remains
access-controlled, hash-bound, publication-excluded, and not printed here.
These identities bind the inspected remediated current bytes only. The
integration is complete for those mutable bytes, but the package remains
outside Git and is not an immutable, accepted, or retained evidence target.

The source profile binds these exact decision and source identities:

```text
accepted_k0a=5227266ceddb664a1595e22e5a92da57a013652f
accepted_k0i=abd092a1f2734c720a205803c29496fe2245b0ef
base=a5f72fd298f6bd02e6d30599dafb43cfa16576b6
candidate=c1c7e254143f99d4ad3cdbf25021a76364d6d75a
tree=a5f77b5acef26d8975fe756512edbd2413fa1239
parent=405a74dd4f1afc793b52f8589ccdcda5ee515f8e
ordered_commits=14
changed_paths=11
host_release=7.3.0-rc4-k3-kvm-host-a1
```

The exact ordered first-parent commit sequence is:

```text
P01 8d8fde35997085df2968916ea2c94c62e382dc77
P02 b84196573a9fe8c17396fe3e8c599877e9cde174
P03 8adf36ee2517fc52c5d63f5d5b59c4d873a62821
P04 4fea63fb354e3bae6ac0f29d068abc13305ad7f9
P05 fee1b86ca274099d74e613536d9cb68518b3c583
P06 026884188ff65066774cf9a991bf6629a84e94b1
P07 ca44cbe811592c71848f3926ef5eb394a8052c33
P08 122580a66af8c8f9f5fe9176555e2d269f4a8bbf
P09 bc10f366f2496a703dc8e94cd123488f321b8e67
P10 19a8fa01dc1c130b9f1c73323fb290c776426d2b
P11 b749d17325025129a8b2ec97846e8386cedc1830
P12 e126a0e16d28e05cdf730373faa6ba690712853b
P13 405a74dd4f1afc793b52f8589ccdcda5ee515f8e
P14 c1c7e254143f99d4ad3cdbf25021a76364d6d75a
```

The exact base-to-candidate changed-path set is:

```text
100644 M Documentation/devicetree/bindings/pci/snps,dw-pcie.yaml
100644 M Documentation/devicetree/bindings/pci/spacemit,k1-pcie-host.yaml
100644 M Documentation/driver-api/phy/phy.rst
100644 M arch/riscv/boot/dts/spacemit/k3-com260-ifx.dts
100644 M arch/riscv/boot/dts/spacemit/k3-com260.dtsi
100644 M arch/riscv/boot/dts/spacemit/k3-pinctrl.dtsi
100644 M arch/riscv/boot/dts/spacemit/k3.dtsi
100644 M drivers/pci/controller/dwc/Kconfig
100644 M drivers/pci/controller/dwc/pcie-spacemit-k1.c
100644 M drivers/phy/phy-core.c
100644 M include/linux/phy/phy.h
```

Direct read-only Git checks in `k0s-source-owner-workspace-1` confirmed
that both total and first-parent counts are 14, the range contains zero merge
commits, the merge base is the recorded base, and the base-to-candidate diff
contains exactly the 11 paths above. Every changed path remains mode `100644`
and change type `M`; every ordered commit, parent, tree, subject, changed-path
mode, and candidate-file SHA-256 in `source-profile-v1.json` was matched
directly to the source-owner Git objects. The candidate commit and tree remain
absent from the Beryllium object database and remain unaccepted source-owner
input.

The separate detached candidate worktree was directly rechecked at the
candidate commit. Its private locator is intentionally omitted. Its index and
worktree diffs are empty, and `git status --porcelain=v1 -z
--untracked-files=all` produced zero bytes with SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
This is current worktree-clean preparation evidence, not candidate acceptance
or retained K0-S readiness evidence.

The candidate is currently contained by zero checked local branches and zero
checked tags, and the current authorized checkout is unrelated to it. That
zero ref containment prevents an immutable referenced source target from
existing. This is a K0-S readiness blocker, not source rejection: the
candidate remains an unaccepted/unretained preparation input.

The literals `branch_label=main` and `source-ready-not-run` belong only to the
accepted future K0-I import/report contract. They do not describe the current
source-owner checkout or current K0-S readiness. The current K0-S source
profile makes no branch-label readiness claim, K0-S remains `not-ready`, and
destination import and install remain `NOT-RUN`.

The current files in `k0s-source-owner-profile-v1` contain the date-only label
`k0s_authorization_date=2026-09-27`. That mutable package field is not adopted
as Beryllium decision evidence. The maintained authorization and source-path
timeline remains the exact 2026-09-28 sequence in section 1.

After source inspection established that the package gate uses only static
checks, deterministic generation checks, temporary fake install roots, and
fake binaries, the existing non-executing gate passed:

```text
K0S_PROFILE_GENERATION: PASS files=17 mode=check
K0S_PROFILE_CHECK: PASS paths=41 patches=14 changed_paths=11 manifests=14 tests=16 execution=NOT-RUN
K0S_PROFILE_TESTS: PASS tests=25
```

The 25 tests are host-only fake-runner/fake-binary tests. They include a
direct controller-tamper case that verifies the controller's own install-hash
preflight fails before creating session output. The static checker also
requires complete 43-of-43 restricted mapping coverage. These checks do not
execute a selected real KVM selftest, QEMU, serial, board, network, or
hardware path, do not write `/opt`, and do not import or install package bytes
through K0-I tooling.

## 6. K0-S readiness still required

K0-S remains not ready until the accepted plan's source gate is satisfied by
one exact clean immutable Git target or one explicitly approved immutable
bundle, including at least:

- complete source, patch, tool, firmware, artifact, command, provenance,
  board, capture, selftest, matrix, result, and recovery manifests;
- the exact 16-command selftest set and approved single-skip record;
- reviewed and immutably retained restricted provenance-map coverage plus its
  hash/size binding; the current mutable draft has complete 43-of-43 coverage
  but does not satisfy this gate;
- exact live FDT and live initramfs identities;
- complete ROM, U-Boot, OpenSBI/M-mode, QEMU, host-rootfs, and package
  provenance;
- exact artifact sizes, modes, and SHA-256 values;
- exact command-manifest identity; and
- a decision-neutral source-owner evidence statement.

The current blockers are explicit:

- retained `SUMMARY.tsv` bytes and retained prior skip-output bytes are
  missing; their paths, sizes, and SHA-256 values remain `UNKNOWN`;
- operational tool, firmware, artifact, and guest-command values remain
  `UNKNOWN`;
- candidate `c1c7e254143f99d4ad3cdbf25021a76364d6d75a` is contained by zero
  checked local branches and zero checked tags, the current authorized
  checkout is unrelated, and no clean immutable referenced source target
  exists; this is an unaccepted/unretained preparation-input blocker, not
  source rejection;
- the local package has no Git containment or approved immutable-bundle
  identity;
- destination import is `NOT-RUN`;
- real KVM selftests are `NOT-RUN`;
- the serial endpoint is `UNKNOWN`, serial use is `NOT-RUN`, and no
  output-only proof was executed;
- K3 and all Beryllium/R8 hardware remain `NOT-RUN`;
- K0-X is blocked and unauthorized, and K0-R is blocked with no result; and
- push, tag, publication, release, migration, archival, and upstream
  submission remain blocked.

A read-only audit, repaired preparation package, passing static or host-only
fake test, available local directory, successful future K0-I import, or clean
candidate worktree does not make K0-S accepted, complete, or ready by itself.

## 7. Explicit non-authorizations

The session instructions and this draft do **not** authorize or establish:

- modification of the source-owner repository or import of its source bytes;
- acceptance of proposed commit
  `c1c7e254143f99d4ad3cdbf25021a76364d6d75a` or tree
  `a5f77b5acef26d8975fe756512edbd2413fa1239`;
- immutable or accepted profile-package content, K0-S readiness, completion,
  source acceptance, bundle approval, or evidence acceptance;
- execution of the 16-command selftest profile;
- K0-X board access, boot, reset, power, serial, guest-matrix, recovery, or
  hardware execution;
- K0-R result acceptance or K0-G evidence/review integration;
- B0, B1, development-kernel/BSP selection, an H0/R8 successor, or R8 H1-H4;
- Beryllium runtime changes, accepted R0-R8 byte changes, root integration,
  dependency or acceptance-pin changes, source-policy changes, or
  publication-gate changes;
- a KVM0 PASS, K3 result, Beryllium hardware result, retained R8 evidence, H0
  row resolution, formal-verification claim, or production claim; or
- push, tag, publication, release, clean-repository migration, archival, or
  upstream submission.

## 8. Exact maintained-source inventory

The cumulative dirty K0-S maintained-source documentation set remains limited
to these regular files and modes:

```text
100644 pathfinder/tests/check-docs-render.mjs
100644 planning/.vitepress/config.mts
100644 planning/HANDOFF.md
100644 planning/README.md
100644 planning/glossary.md
100644 planning/k3-kvm0-k0i-review-summary.md
100644 planning/k3-kvm0-k0s-authorization-record.md
100644 planning/k3-kvm0-plan-k0a-review-summary.md
100644 planning/project-orientation.md
100644 planning/roadmap.md
```

Within that already-dirty set, todo `integrate-k0s-remediation` changes
exactly these maintained Beryllium sources:

```text
100644 planning/HANDOFF.md
100644 planning/README.md
100644 planning/glossary.md
100644 planning/k3-kvm0-k0i-review-summary.md
100644 planning/k3-kvm0-k0s-authorization-record.md
100644 planning/k3-kvm0-plan-k0a-review-summary.md
100644 planning/project-orientation.md
100644 planning/roadmap.md
```

The accepted KVM0 plan text and the temporal K0-A/K0-I decision records are
not rewritten by this integration. Their earlier statements remain scoped to
the times and decisions they record.

Generated `docs/html/**`, `pathfinder/docs/html/**`, and
`pathfinder/docs/public/diagrams/**` are outside this maintained-source repair
and must not be edited or regenerated here. `planning/index.md` does not
exist; the planning homepage source is `planning/README.md` through the
VitePress rewrite.

## 9. Validation and next action

The documentation-build, link, browser, direct-file, and generated-site gates
are `NOT RUN` for this integration. No generated site was regenerated. The
following bounded checks passed on 2026-09-28:

```text
package k0s-source-owner-profile-v1 strict SHA256SUMS verification
k0s-source-owner-profile-v1 FILES.modes: 41 paths / SHA-256 f8f130dbcbddfa557298bab1a9bcac859a4ec8af8adb219d271e467c52ffa5db
k0s-source-owner-profile-v1 SHA256SUMS: 34 entries / SHA-256 57d0753ab55333ca29198d894e176c5a270e52747e29303b6ad1d2bb8cd606b3
k0s-source-owner-profile-v1 source profile SHA-256 aaa4b83d216cd932fd77c32230dded6ff206f6224224670bcac2169bd5a36238
k0s-source-owner-profile-v1 restricted map: mode 0600 / 42570 bytes / SHA-256 eb734dc9dad08a2ec5e73d4f5b50a4fe59ed9100580dcf0490687dfb2f8943c4 / complete 43-of-43 coverage
k0s-source-owner-profile-v1 K0S_PROFILE_GENERATION check: PASS, 17 generated files
k0s-source-owner-profile-v1 K0S_PROFILE_CHECK: PASS, 41 paths / 14 patches / 11 changed paths / 14 manifests / 16 prospective tests / execution NOT-RUN
k0s-source-owner-profile-v1 controller self-hash preflight: PASS
k0s-source-owner-profile-v1 K0S_PROFILE_TESTS: PASS, 25 host-only fake tests
source-profile direct Git-object check: PASS, 14 ordered commits / 11 changed paths
candidate ref containment: PASS, zero checked containing local branches / zero checked containing tags
current authorized checkout relation: PASS, unrelated to candidate
candidate detached worktree index/worktree/status check: PASS, zero status bytes
tracked added-line K0-S private-locator search: PASS
untracked K0-S record private-locator search: PASS
git diff --check
git diff --no-index --check /dev/null planning/k3-kvm0-k0s-authorization-record.md
node --check pathfinder/tests/check-docs-render.mjs
node --check planning/.vitepress/config.mts
```

The no-index check returned the expected difference status `1` with no
whitespace diagnostics. The package checks validate current local package
structure and fake-only behavior, not real KVM, serial, board, hardware,
destination import, K0-S readiness, or acceptance.

The next K0-S step is not K0-X. The source-owner side must first close or
preserve the missing retained inputs and operational identities, establish one
approved immutable retention route, and obtain review of an exact evidence
target.
Only a later separate decision may establish K0-S readiness or authorize
K0-X.

---

**Status:** the exact session evidence authorizes bounded K0-S preparation,
the authoritative source-owner locator was supplied and is intentionally
omitted, and `k0s-source-owner-profile-v1` is recorded at its current
remediated deterministic file/mode/hash identities. Its restricted provenance
remains exact-minimum, access-controlled, hash-bound, publication-excluded,
and not printed. The package remains outside Git, mutable,
`profile_review_status=not-reviewed`, and not retained K0-S readiness or
acceptance evidence. Candidate containment remains zero checked local
branches and zero checked tags, so no clean immutable referenced source target
exists. K0-S remains not ready or complete. This document remains
`draft-not-reviewed` with no exact documentation target.

**Next:** close the retained-input and operational-identity gaps, establish an
approved immutable route, and prepare exact review evidence without importing
source or package bytes, executing real selftests or K0-X, accessing serial or
hardware, or claiming readiness.

**Action required from the responsible human:** none for this source-document
repair. Any execution, readiness, acceptance, publication, or scope expansion
still requires its own exact evidence and decision.
