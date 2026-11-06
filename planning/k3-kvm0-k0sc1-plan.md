<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# KVM0 K0-SC1 custody and selection plan

## Status and authority

K0-SC1 is the first separately gated package under the accepted K0-S
completion plan. It prepares stable package-specific custody and exact human
selection decisions for currently available K0-S inputs. It does not rebuild
missing inputs, access the K3 board, assemble the final K0-A payload, import
anything through K0-I, or make K0-S ready.

The responsible human supplied:

```text
the k3 h/w is back online and available. proceed as appropriate
```

at `2026-10-04T20:28:37.102+02:00`. For this target, that statement is
bounded to:

- human-reported board availability as non-evidentiary scheduling input; and
- authorization to draft this K0-SC1 plan.

It is not K0-SC1 implementation authorization and does not authorize K0-SC3,
board access, connectivity probing, capture, KVM0 execution, or hardware
evidence.

This plan's immutable pre-decision status is:

```text
k0sc1_plan=proposed-not-reviewed
k0sc1_plan_target=none
k0sc1_plan_base=b36190352d270ce9ed70a6ddab8f4c7e7030f4e6
k0sc1_drafting_authorization=authorized
k0sc1_drafting_authorization_timestamp=2026-10-04T20:28:37.102+02:00
k0sc1_implementation=not-authorized
k0sc1_custody=NOT-RUN
k0sc1_selection=NOT-RUN
k0sc1_remote_ref_check=NOT-RUN
k0sc2=not-authorized
k0sc3=NOT-RUN-not-authorized
k3_availability=human-reported-online-and-available-non-evidentiary
k0s_readiness_completion_authority=paused-at-missing-input-stop
k0s_readiness_completion_authority_consumed=no
k0s_readiness_completion_authority_revoked=no
k0s_readiness=not-ready
k0x=blocked-not-authorized
k0r=blocked-no-result
beryllium_k3_hardware=NOT-RUN
r8_k3_hardware=NOT-RUN
development_kernel_bsp=UNDECIDED
publication=blocked
```

Acceptance of this plan would approve planning text only. It would not
authorize custody copying, artifact or selftest selection, remote-ref access,
source modification, board access, K0-SC2, K0-SC3, package assembly, import,
readiness, K0-X, K0-R, push, publication, or release.

## Plan revision K0-SC1-A: review corrections

Exact original K0-SC1 target
`9b9923f8a58fe7102a108cb2a976ea09979427a1` is responsible-human accepted
as planning text only. Its review and acceptance record is
`0c8a625df9d49254332b2105ae4b3c9cbe60a982`. The accepted original bytes
remain authoritative history at:

```text
9b9923f8a58fe7102a108cb2a976ea09979427a1:planning/k3-kvm0-k0sc1-plan.md
```

Review of that exact target found K0SC1-F1, K0SC1-F2, and K0SC1-F3. The
responsible human accepted the target without resolving or waiving them.
**Plan revision K0-SC1-A** proposes bounded corrections while preserving the
original target and decision.

This revision's immutable pre-decision status is:

```text
k0sc1_plan_revision=K0-SC1-A
k0sc1_plan_revision_status=proposed-not-reviewed
k0sc1_plan_revision_base=0c8a625df9d49254332b2105ae4b3c9cbe60a982
k0sc1_plan_revision_target=none
k0sc1_plan_revision_review_packet=none
k0sc1_plan_revision_decision=pending
k0sc1_plan_revision_findings=K0SC1-F1,K0SC1-F2,K0SC1-F3-proposed-addressed-pending-human-decision
k0sc1_plan_revision_residual_findings=K0SC-R1,K0SC-R2,K0SC-R3-unresolved-unwaived
k0sc1_plan_revision_implementation=not-authorized
```

K0-SC1-A changes only:

1. **K0SC1-F1:** C5 becomes a human selection of test IDs/names, order, argv,
   cwd, environment, timeouts, limits, exits, and markers. Exact selftest
   binaries, hashes, install tree, 18-entry install manifest, and final
   structured command manifest remain K0-SC2 obligations.
2. **K0SC1-F2:** ordinary/root directory mode, maximum path depth, maximum
   ordinary directory count, and maximum `FILES.modes` row count become
   finite and numeric.
3. **K0SC1-F3:** exact ref-binding attachment fields and all 16 mandatory stop
   IDs become explicit in the authorization template and validation.

The corrections are proposed, not reviewed, and do not authorize
implementation. K0SC-R1/R2/R3 remain unresolved and unwaived; K0SC-R2 remains
open for K0-SC2 and K0-SC3.

## Plan revision K0-SC1-B: casefold-safe host custody paths

Exact Plan revision K0-SC1-A target
`c00f4d000c845a7c3d62921c1d7939fc158744e2` is responsible-human accepted
as planning corrections only. Its review and acceptance record is
`06cda3814426de940afadb05cd5cf59ee8253688`. The accepted K0-SC1-A bytes
remain authoritative history.

Read-only preparation under the later responsible-human instruction found a
terminal A2 blocker: four Unicode-casefold equivalence groups covering eight
otherwise distinct host rows. No member was selected, omitted, renamed,
deduplicated, or copied. The same preparation confirmed zero raw-path and
zero NFC-path collision groups. These aggregate observations are
session-private drafting input and must be rederived under any future exact
implementation authorization.

At `2026-10-05T13:13:59.788+02:00`, the responsible human supplied:

```text
authorized, proceed and continue as far as possible
```

For K0-SC1-B, that instruction authorizes drafting and review of a bounded
path-collision plan revision only. It does not authorize K0-SC1
implementation, custody copying, selection, remote-ref checking, board
access, or any successor.

This revision's immutable pre-decision status is:

```text
k0sc1_plan_revision_k0sc1b=proposed-not-reviewed
k0sc1_plan_revision_k0sc1b_base=06cda3814426de940afadb05cd5cf59ee8253688
k0sc1_plan_revision_k0sc1b_target=none
k0sc1_plan_revision_k0sc1b_review_packet=none
k0sc1_plan_revision_k0sc1b_decision=pending
k0sc1_plan_revision_k0sc1b_authorization=drafting-and-review-only
k0sc1_plan_revision_k0sc1b_authorization_timestamp=2026-10-05T13:13:59.788+02:00
k0sc1_plan_revision_k0sc1b_a2=proposed-addressed-by-uniform-by-row-mapping-pending-human-decision-and-later-implementation-validation
k0sc1_plan_revision_k0sc1b_open_findings=restricted-search-quality,K0SC-R1,K0SC-R2,K0SC-R3
k0sc1_plan_revision_k0sc1b_implementation=not-authorized
```

K0-SC1-B changes only the host custody pathname formula and its A2
validation:

1. every `H_regular_eligible` host manifest row maps to
   `ordinary/host/by-row/<row-4d>.bin`, where `<row-4d>` is the exact 1-based
   manifest data-row number `0001` through `2030`;
2. noneligible rows remain metadata-only and receive no custody path;
3. each eligible row is copied separately even when content is identical;
4. original member/origin/type/mode/size/hash metadata remains exact in the
   custody inventory;
5. Unicode-casefold equivalence among otherwise valid original host member
   paths is diagnostic rather than an A2 stop after this mapping; and
6. the complete final ordinary file and directory path set must remain unique
   under raw, NFC, NFC-casefold, and NFKC-casefold forms, or A2 still stops
   implementation.

K0-SC1-B adds no disposition class, control file, custody root, general
evidence store, content-addressed storage, or implementation authority.
Raw-identical or NFC-identical original paths, path escape, unsafe objects,
unsafe modes, and every other accepted A2 predicate remain stops.

## Corrected Plan revision K0-SC1-B: F1-F4 correction

Exact first K0-SC1-B target
`1ce71e73078a65a271949d84db47343e4eaacf14`, packet
`d4bbba7950a1f375a2a012a43e5ad54a6716eceb`, and revisions-requested
decision record `e1cd15a72e84304812a7c893d5b3a8c4990ea628` remain immutable,
unaccepted decision support.

At `2026-10-05T22:58:19.170+02:00`, the responsible human supplied:

```text
authorize correction drafting from exact base e1cd15a72e84304812a7c893d5b3a8c4990ea628
```

That instruction authorizes drafting and review of text corrections for
K0SC1B-F1 through K0SC1B-F4 only. It does not authorize K0-SC1
implementation, custody copying, selection, remote-ref checking, Lane B,
board access, or a successor.

This corrected revision's immutable pre-decision status is:

```text
k0sc1_plan_revision_k0sc1b_corrected=proposed-not-reviewed
k0sc1_plan_revision_k0sc1b_corrected_base=e1cd15a72e84304812a7c893d5b3a8c4990ea628
k0sc1_plan_revision_k0sc1b_corrected_target=none
k0sc1_plan_revision_k0sc1b_corrected_review_packet=planning/k3-kvm0-k0sc1-plan-k0sc1b-corrected-review-summary.md
k0sc1_plan_revision_k0sc1b_corrected_decision=pending
k0sc1_plan_revision_k0sc1b_corrected_authorization=correction-drafting-and-review-only
k0sc1_plan_revision_k0sc1b_corrected_authorization_timestamp=2026-10-05T22:58:19.170+02:00
k0sc1_plan_revision_k0sc1b_corrected_findings=K0SC1B-F1-proposed-addressed,K0SC1B-F2-proposed-addressed,K0SC1B-F3-proposed-addressed,K0SC1B-F4-proposed-addressed
k0sc1_plan_revision_k0sc1b_corrected_a2=unresolved-pending-later-implementation-validation
k0sc1_plan_revision_k0sc1b_corrected_residual_findings=K0SC-R1,K0SC-R2,K0SC-R3,K0SC-R4-open-unwaived
k0sc1_plan_revision_k0sc1b_corrected_implementation=not-authorized
```

The corrected revision changes only:

1. **K0SC1B-F1:** final-tree validation retains tagged file and directory
   occurrences until twelve file/file, directory/directory, and
   file/directory checks complete under raw, NFC, NFC-casefold, and
   NFKC-casefold keys;
2. **K0SC1B-F2:** every host row has exactly one total, disjoint
   eligible-custody or metadata-only schema with exact nullability and
   expected copy count;
3. **K0SC1B-F3:** the future authorization binds strict UTF-8, one exact UCD
   version, full default non-Turkic locale-independent folding, normalization
   ordering, and the complete executable/data closure through existing
   encoding, tool-lock, and command fields; and
4. **K0SC1B-F4:** the previously untraceable label becomes proposed stable
   finding `K0SC-R4`, explicitly `OPEN`, `DEFINITION UNKNOWN`, and pending a
   responsible-human non-restricted definition and later separate closure or
   waiver decision.

These are planning corrections only. They add no disposition class, control,
custody path namespace, stop ID, implementation result, or authority.

## Controlling accepted history

| Boundary | Exact identity and effect |
| --- | --- |
| KVM0 Plan revision K0-A | Accepted target `5227266ceddb664a1595e22e5a92da57a013652f`; controls source evidence, 15-control bundle, privacy, digest order, execution and result gates |
| K0-I destination tooling | Accepted target `abd092a1f2734c720a205803c29496fe2245b0ef`; offline importer/checker only |
| K0-S status record | Accepted documentation target `c65705582c243dd908ff47d3189df07601167400`; accurate status only, not readiness or package acceptance |
| K0-SC plan | Accepted planning target `33f35981483bccbc4e3a1c87f4a5af52e0e15d41` |
| K0-SC acceptance record | Follow-up `b36190352d270ce9ed70a6ddab8f4c7e7030f4e6`; planning acceptance only, no package authority |
| Original K0-SC1 plan | Accepted planning target `9b9923f8a58fe7102a108cb2a976ea09979427a1`; K0SC1-F1/F2/F3 remain unresolved and unwaived |
| Original K0-SC1 acceptance record | Follow-up `0c8a625df9d49254332b2105ae4b3c9cbe60a982`; planning acceptance only, no implementation authority |
| K0-SC1-A plan revision | Accepted planning-corrections target `c00f4d000c845a7c3d62921c1d7939fc158744e2`; addresses K0SC1-F1/F2/F3 in text only |
| K0-SC1-A acceptance record | Follow-up `06cda3814426de940afadb05cd5cf59ee8253688`; planning corrections only, no implementation authority |
| October 4 readiness-completion authority | Bound to Beryllium base `a8e137ebbbeeff2a5475050b047a8ec6109d22e0`; paused at its missing-input stop, unconsumed and unrevoked |

The exact source relation remains:

```text
kvm_base=a5f72fd298f6bd02e6d30599dafb43cfa16576b6
prepared_candidate_commit=c1c7e254143f99d4ad3cdbf25021a76364d6d75a
prepared_candidate_tree=a5f77b5acef26d8975fe756512edbd2413fa1239
board_enablement_patch_count=14
host_release=7.3.0-rc4-k3-kvm-host-a1
source_relation_status=recorded-not-accepted
```

K0-SC1 may report on that relation. It may not accept it, rewrite it, move a
ref, or silently substitute another relation.

## Relationship to accepted residual findings

The accepted K0-SC review record retains K0SC-R1, K0SC-R2, and K0SC-R3 as
unresolved and unwaived. This proposed plan does not rewrite that accepted
history. It proposes:

| Finding | Proposed K0-SC1 disposition | Remaining boundary |
| --- | --- | --- |
| K0SC-R1: undefined “seventh artifact-selection class” | Original K0-SC1 proposed six named disposition classes; K0-SC1-A retains those classes and narrows C5 ownership | Remains unresolved in accepted K0-SC; K0-SC1-A disposition awaits human decision |
| K0SC-R2: authorization-time path bounds only | K0-SC1-A adds K0-SC1-specific directory modes, depth, directory count, row maximum, and exact stop validation | K0-SC2 and K0-SC3 path maxima remain unresolved for their later plans |
| K0SC-R3: private diagnostic retention risk | Package-specific stable custody remains a K0-SC1 human decision and current loss/drift remains a stop | No interim copy is authorized; risk persists until implementation is separately authorized and completed |
| K0SC-R4: restricted-search preparation quality | Proposed stable ID for the retained `restricted-search-quality` label; non-restricted evidence establishes only that the finding exists and lacks a definition, evidence boundary, and human question | Remains `OPEN`, `DEFINITION UNKNOWN`, and unwaived; no checker can close it and no additional operational gate is inferred |

Plan acceptance would approve these K0-SC1-specific planning dispositions
only. It would not establish custody or close the implementation-time risks.

For K0SC-R4, retained non-restricted evidence does not identify the search
corpus, expected method or coverage, observed deviation, affected output, or
closure criterion. These details must not be inferred from casefold
preparation, privacy-scan results, private-locator blockers, restricted-map
metadata, or restricted contents.

The exact future responsible-human question is:

> Should the open `restricted-search-quality` label be recorded as
> `K0SC-R4`, and what exact non-restricted definition should govern it -
> identifying the authorized preparation/search step, intended corpus and
> quality criterion, observed deviation, permissible evidence boundary, and
> existing gates affected - while leaving it open and unwaived until a
> separate explicit responsible-human closure or waiver decision?

No checker may define, close, or waive K0SC-R4.

## Objective

K0-SC1 asks:

> Can the exact currently available K0-S records and candidate bytes be
> placed into one bounded, privacy-separated, package-specific custody
> candidate, while preserving source relation and provenance limits and
> presenting exact host, selftest, skip, and ref-report decisions to the
> responsible human without allowing checks to decide them?

The answer is not yet known. K0-SC1 is not a general evidence store and not a
K0-S readiness package.

## Six disposition classes

Exactly six classes are permitted:

| Class | Name | Accepted K0-SC inputs/blockers | Deliverable and human decision |
| --- | --- | --- | --- |
| C1 | Ordinary custody corpus | The 12 recovered discovery records; the 2,030-row host corpus; ordinary files from the current preparation profile | Ordinary custody inventory; human accepts, revises, or defers custody location, exact member inventory, origin mapping, and separation controls |
| C2 | Restricted-provenance custody | The restricted provenance map separated from accepted input class three | Restricted custody statement; shares the custody decision while remaining outside every ordinary surface |
| C3 | Source-ref report disposition | Exact source relation plus selected local/tracking records and optional separately authorized remote observation | Human accepts, revises, or defers the report disposition only: remote checked under authority or `NOT RUN`; source relation stays recorded-not-accepted |
| C4 | Host build/stage artifact selection | Host corpus and host-selection blocker | Host-selection packet; human selects, revises, or defers one exact existing candidate set |
| C5 | ST01-ST16 set selection | Exact retained selftest-selection inputs and the accepted 16-test blocker | Combined selftest/skip packet; human approves, revises, or defers exactly the ST01-ST16 IDs/names, order, argv, cwd, environment, timeouts, limits, exits, and markers |
| C6 | ST16 skip selection | Exact retained skip output and legend input | Same packet; human approves, revises, or defers the ST16 skip identity, exit `4`, exact marker, reason, and outside-KVM0 rationale |

The candidate changed-path/mode inventory is a cross-cutting control, not a
seventh class. Any input, decision, output, or authority class outside C1-C6
is a stop requiring a reviewed plan revision.

Ordinary-profile custody is derived from accepted K0-SC1 maximum input class
three. Separating its restricted component into C2 operationalizes the
already accepted restricted-provenance blocker and creates no new blocker.

## Draft-time expected input identities

These expected values are planning inputs only. Every value must be rederived
at the exact future K0-SC1 implementation candidate:

| Input | Draft-time expected identity | Boundary |
| --- | --- | --- |
| Recovered discovery set | 12 records; closure SHA-256 `d7d48d43686960e06e25750f2da0965fe0514e7c399b29afbc41baf623aee5f4`; sorted `basename<TAB>sha256<LF>` identity `3fc33b42c2b4ce4727ecc869fb38aeba1ad23f1bf1b394a384c6d1781d627a83` | Private member locators and contents remain outside Git |
| Host corpus | 2,030 manifest rows; manifest SHA-256 `015f53fe41ab689736116ce8fae64ef0466cd4327b7d575b30379e8977f60b2a` | Exact type/mode/size/hash and origin mapping must be rechecked |
| Preparation profile | 46 regular files, 53 path/type/mode rows, 45 checksum entries | Current mutable package bytes, not accepted K0-S target evidence |
| `FILES.modes` | SHA-256 `003f8f79b7bf97f9699d995292089521dee0f255834ff253774bc90dfd44c195` | Recheck before use |
| `SHA256SUMS` | SHA-256 `21b1ea3ef1b246aff7c27b3728a41a415be80aa677699837f106bb025c343060` | Recheck all 45 entries |
| Source profile | SHA-256 `4052b8a1748ed4d2303bd39acad88d5c5109e9eb8f5f3c9365b9d9d2d956e35f` | Relation record only; not source acceptance |
| Restricted map | mode `0600`, 42,570 bytes, SHA-256 `eb734dc9dad08a2ec5e73d4f5b50a4fe59ed9100580dcf0490687dfb2f8943c4`, 43-of-43 coverage | Contents remain access-controlled and excluded from ordinary custody |
| Retained selftest-selection inputs | Exactly three profile members: `retained-selection-inputs/SUMMARY.tsv`, `retained-selection-inputs/vm_types_test.log`, and `retained-selection-inputs/LEGEND.txt` | These bind the ST01-ST16 names/order and ST16 skip basis only; they establish no binary hash, install tree, install manifest, or final command-manifest identity |
| Ref-record classes | Source-relation record, selected local-ref records, selected tracking-ref records, and one remote-status record | Exact local/tracking counts must be rederived; remote status is authorized read-only observation or `NOT RUN` |

The accepted K0-S target recorded an older 35-file/41-path/34-checksum
generation. The current 46/53/45 values must never be described as accepted
K0-S target evidence.

## Custody candidate path, count, and mode envelope

The future K0-SC1 authorization must supply two private external-root
pseudonyms out of band:

```text
ordinary_custody_root_id=<human-assigned-pseudonym>
restricted_custody_root_id=<human-assigned-pseudonym>
```

No absolute locator may enter Git, an ordinary report, or publication-safe
output.

### Ordinary input paths

The ordinary candidate uses these deterministic namespaces:

```text
ordinary/discovery/<source_name>
ordinary/host/by-row/<row-4d>.bin
ordinary/profile/<relative_path>
```

Rules:

1. `ordinary/discovery/` contains exactly the 12 hash-bound discovery records.
2. `ordinary/host/` considers exactly the 2,030 manifest rows. Each eligible
   regular row maps one-for-one to
   `ordinary/host/by-row/<row-4d>.bin`, where `<row-4d>` is the exact
   zero-padded 1-based manifest data-row number `0001` through `2030`.
   Manifest row identity, not eligible-row ordinal, determines the filename.
   Non-regular, excluded, unsafe, missing, or mismatched rows are retained
   only as inventory dispositions, carry `custody_path=null`, and create no
   file or path reservation.
3. `ordinary/profile/` contains exactly the 45 ordinary regular profile files
   after excluding `restricted/provenance-map-v1.json`. The profile's ordinary
   path/type/mode closure has 51 rows after excluding the restricted directory
   and restricted map from the 53-row source inventory.
4. The three retained selection inputs and source/ref records are referenced
   from their ordinary profile members; they are not duplicated.
5. The ordinary custody root and every ordinary descendant directory are mode
   `0755`. Every ordinary custody copy is a regular mode-`0644` file. The custody
   inventory separately records original type, mode, size, SHA-256, origin,
   privacy class, duplicate group, and disposition.
6. Relative path depth is the number of non-empty `/`-separated components;
   root depth is zero and every ordinary path depth is at most 64.
7. Every original host member path must pass raw-byte identity, NFC identity,
   non-casefold duplicate-normalized-name, path-escape, unsafe-component,
   object, link, type, mode, executable, and origin checks. For original host
   member paths only, Unicode casefold equivalence is diagnostic and is not
   by itself an A2 stop when all raw and non-casefold predicates pass. This
   exception applies only to equality produced by NFC-casefold or
   NFKC-casefold comparison; it does not change eligibility, merge rows,
   select content, or apply to any final custody path or non-host namespace.
8. Symlinks, hard links, devices, sockets, FIFOs, setuid/setgid bits, path
   escape, raw or NFC collision, other duplicate normalized names, unsafe
   modes, and undeclared executables remain forbidden.
9. Duplicate logical rows and equal-content rows are preserved as separately
   namespaced files when eligible. K0-SC1 does not create a content-addressed
   store, alias equal bytes, or deduplicate them into a shared service.

For host manifest rows only, the custody inventory is the total and disjoint
union of two variants. Every one of the 2,030 rows satisfies exactly one
variant. Every listed field is present; `null` means JSON null. Omitted
fields, empty-string sentinels, zero-valued custody metadata, and other
substitutes for `null` are forbidden.

An **eligible-custody row** has:

- the existing eligibility predicate true: regular, safe, present, matching,
  and not excluded;
- `custody_path=ordinary/host/by-row/<row-4d>.bin`;
- `custody_type=regular`;
- `custody_mode=0644`;
- `custody_size=original_size`;
- `custody_sha256=original_sha256`;
- `disposition=selected`;
- `exclusion_reason=null`; and
- `expected_copy_count=1`.

A **metadata-only row** has:

- the existing eligibility predicate false, including an unresolved
  predicate represented by the existing `UNKNOWN` disposition;
- `custody_path=null`;
- `custody_type=null`;
- `custody_mode=null`;
- `custody_size=null`;
- `custody_sha256=null`;
- `disposition` equal to one existing non-selected value: `excluded`,
  `metadata-only`, `mismatch`, `missing`, or `UNKNOWN`;
- a non-null stable `exclusion_reason` identifier bound to the exact
  justification record; and
- `expected_copy_count=0`.

For both variants, the exact manifest data-row number, opaque origin ID,
source class and source object or manifest-row reference, original member
path, original type, original mode, original size, original SHA-256, privacy
class, duplicate group, and disposition-justification record remain non-null
and exact. Missing or mismatching source bytes do not permit
manifest-declared original metadata to be nulled or replaced by custody
metadata. `expected_copy_count` is per row, never duplicate-group
cardinality: equal-content eligible rows each remain `1`.
`disposition=selected` describes the row's proposed custody-copy state only;
it is not responsible-human acceptance of custody, host selection, or the
plan.

Let `H_regular_eligible` be the exact number of host rows that are regular,
safe, present, matching, and not excluded when rederived. Then:

```text
0 <= H_regular_eligible <= 2030
H_metadata_only = 2030 - H_regular_eligible
H_regular_eligible + H_metadata_only = 2030
count(host rows with custody_path != null) = H_regular_eligible
count(host rows with custody_path == null) = H_metadata_only
sum(host expected_copy_count) = H_regular_eligible
count(host rows with expected_copy_count = 1) = H_regular_eligible
count(host rows with expected_copy_count = 0) = H_metadata_only
ordinary_input_regular_files =
  12 + H_regular_eligible + 45
ordinary_input_regular_files <= 2087
```

No concrete eligible count is stated without authorized private-input
rederivation. These host-only relationships do not change accepted aggregate
file formulas or any non-host inventory schema.

For every possible host row, the constructed custody path has:

```text
filename_bytes=8
relative_path_bytes=29
relative_path_depth=4
path_alphabet=lowercase-ASCII-digits-hyphen-dot-slash
```

If `H_regular_eligible` is zero, the host namespace contributes no directory.
If it is nonzero, its proper-parent set is exactly:

```text
ordinary
ordinary/host
ordinary/host/by-row
```

The `ordinary` root already exists for the fixed discovery/profile inputs, so
the host namespace adds at most two ordinary directories.

### Restricted path

Exactly one restricted regular file is permitted:

```text
restricted/provenance-map-v1.json
```

The restricted directory is mode `0700`; the map is mode `0600`. It is not
covered by the ordinary checksum file and must not enter Git, ordinary
custody, an ordinary archive, K0-I import, a report, or publication output.
The ordinary restricted custody statement binds only exact size, SHA-256,
coverage, opaque-ID relation, access policy, and exclusions.

### Generated ordinary control paths

Exactly eight generated mode-`0644` regular files are permitted:

```text
controls/custody-inventory-v1.json
controls/restricted-custody-statement-v1.json
controls/host-selection-packet-v1.json
controls/selftest-skip-selection-packet-v1.json
controls/source-ref-report-v1.json
controls/candidate-path-mode-inventory-v1.tsv
FILES.modes
SHA256SUMS
```

Every selection packet is decision-neutral and carries
`decision=pending-responsible-human`. No checker may change that field to an
accepted or selected state.

### Hard maxima and deterministic formulas

```text
ordinary_regular_files =
  ordinary_input_regular_files + 8
ordinary_regular_files <= 2095

ordinary_checksum_entries =
  ordinary_regular_files - 1

restricted_regular_files = 1
all_regular_files <= 2096
all_regular_files <= 4096

F_occ =
  one tagged occurrence for every intended final ordinary regular file
length(F_occ) = ordinary_regular_files

D_occ =
  one tagged occurrence for every intended materialized ordinary
  descendant directory, excluding the external ordinary root
ordinary_directory_count = 1 + length(D_occ)
ordinary_directory_count <= 4096
every external ordinary root and D_occ member mode = 0755

restricted_directory_set =
  restricted root only
restricted_directory_count = 1
every restricted_directory_set member mode = 0700

FILES.modes rows =
  length(F_occ) + ordinary_directory_count
FILES.modes rows <= 6191
```

Every `F_occ` and `D_occ` node carries one unique, pathname-independent tag.
File tags are the exact discovery-record, host-manifest-row,
profile-inventory-row, or generated-control identities. Directory tags are
exact opaque declaration identities bound by `exact_path_mode_inventory`.
Multiple children sharing one intended parent reference the same directory
node. Independent directory declarations remain distinct nodes even when
their path bytes match.

No path-keyed set, map, sort-unique operation, filesystem insertion, or
normalized key may discard or coalesce a tagged node before all collision
checks complete. The numeric maxima and file arithmetic remain unchanged;
only the directory collection and count representation is corrected to
retain occurrences.

`SHA256SUMS` hashes every ordinary regular file except itself, in raw UTF-8
path-byte order. It excludes `restricted/**`. `FILES.modes` records every
ordinary path, type, and mode, including directories, in the same path order.

Additional caps:

```text
maximum_relative_path_depth=64
maximum_path_bytes=512
maximum_generated_control_bytes_each=4194304
maximum_ordinary_expanded_bytes=4294967296
restricted_map_bytes=42570
serial_output_bytes=0
guest_output_bytes=0
```

If exact rederivation would exceed a cap, add a seventh class, introduce
another path namespace, or require a general evidence store, K0-SC1 stops for
a reviewed revision.

Depth, directory-count, directory-mode, `FILES.modes` row, path-byte, and
formula disagreement maps to added stop A1. Unsafe object/path/mode defects map
to A2. Generated-control or expanded-byte cap violations map to A6. These
corrections add no seventeenth stop and grant no K0-I import authority.

### Mandatory final-tree uniqueness

`F_occ` and `D_occ` are occurrence-preserving sequences, not path sets.
Before collision validation, every node retains its unique tag and exact path
bytes. The external ordinary root is excluded because it has no relative
pathname. The restricted root remains separate and unchanged.

For every pathname byte string `b` subject to an original-host normalized
comparison or a final-tree normalized key:

```text
u = strict_utf8_decode(b)
```

`strict_utf8_decode` accepts only shortest-form UTF-8 encodings of Unicode
scalar values. It rejects truncated, overlong, stray-continuation, surrogate,
and out-of-range sequences. It performs no replacement, omission, escaping,
best-fit conversion, or locale-dependent decoding.

The exact key functions are:

```text
raw_key(b) = b
nfc_key(b) =
  UTF8_strict(NFC_UCD(u))
nfc_casefold_key(b) =
  UTF8_strict(
    NFC_UCD(
      Full_Default_Non_Turkic_Case_Fold_UCD(
        NFC_UCD(u))))
nfkc_casefold_key(b) =
  UTF8_strict(toNFKC_Casefold_UCD(u))
```

`Full_Default_Non_Turkic_Case_Fold_UCD` uses the exact bound UCD's full
default case-fold mappings, including multi-code-point expansions: statuses
`C` and `F`, never simple-only `S` or Turkic `T` mappings. It is independent
of locale and environment. `toNFKC_Casefold_UCD` is the normative operation
for the same exact UCD version; no substitute ordering is permitted.

For each key function `K` above, all three predicates are mandatory:

```text
file injectivity:
  for all distinct file tags i,j,
  K(file_path_i) != K(file_path_j)

directory uniqueness:
  for all distinct directory tags a,b,
  K(dir_path_a) != K(dir_path_b)

file/directory disjointness:
  for every file tag i and directory tag a,
  K(file_path_i) != K(dir_path_a)
```

These are twelve checks: three predicates under four key forms. Any failed
predicate is A2, including exact file/file, directory/directory, or
file/directory collision. Diagnostics may identify every involved tag and key
form, but must not select or prefer a row/node; omit, merge, rename, reindex,
rewrite, alias, or deduplicate it; relax a key form; materialize partial
success; or convert a final-tree collision into the original-host casefold
diagnostic exception.

Failure of strict decoding, normalization, folding, or strict encoding
produces no key and is A2. It must never become inequality, `UNKNOWN`, a
warning, partial success, fallback, or replacement-character output.
Construction arguments and the by-row host grammar do not replace the
complete occurrence-preserving final-tree checks.

The future authorization must bind identical values wherever
`host_path_encoding` appears:

```text
host_path_encoding=ordinary-host-by-row-v1:utf8-strict:unicode-<exact-UCD-version>:k0sc1-unicode-profile-v1
```

The existing `tool_locks` attachment binds every executable, library, plugin,
generated table, source Unicode-data artifact, and runtime-loaded data object
whose bytes can affect the four keys. Each applicable entry binds a stable
role and opaque lock ID; private absolute and resolved regular-file paths;
mode, byte size, and SHA-256; exact implementation/data and UCD versions;
source or owning open package and exact package version; license identity;
and embedded or runtime-loaded status.

Embedded data binds both its containing binary/library and exact source-data
identities. Dynamic data binds the complete runtime closure. Every entry
agrees on one UCD version. Ambient locale, mutable search paths, plugins,
caches, package-manager resolution, network fallback, unlisted data, mixed
UCD versions, and unverifiable dynamic loading are forbidden and map to A5.
Concrete private tool/data locators entering Git or ordinary output map to
A3.

`k0sc1_operational_commands` binds the exact transformer and closure-check
argv, cwd, environment, limits, exits, outputs, and markers. No locale or
Unicode-data environment input may affect results unless explicitly bound.
This correction selects no UCD release, implementation, package, data file,
embedded/dynamic mode, locator, hash, command, cross-check, or test vector.

## Origin and duplicate handling

The custody inventory binds every ordinary input to exact origin and original
metadata. Host rows use the total, disjoint eligible-custody and metadata-only
variants above; non-host schemas remain unchanged.

Every host row binds:

- exact manifest data-row number;
- one opaque origin ID;
- source class and exact source object or manifest row;
- original member path;
- original type, mode, size, and SHA-256;
- privacy class;
- duplicate group;
- selected, excluded, metadata-only, mismatch, missing, or `UNKNOWN`
  disposition; and
- the exact record that justifies the disposition.

It additionally binds the complete custody-field tuple, `exclusion_reason`,
and `expected_copy_count` required by exactly one host-row variant. A host row
matching both variants or neither is A1. So are an omitted required field,
custody-field nullability violation, rewritten or nulled original metadata,
ineligible-row path/reservation/copy, eligible-row custody tuple differing
from `regular`/`0644`/original-size/original-SHA-256, invalid disposition and
reason pairing, expected copy count outside `{0,1}`, or host split/path/count
equality failure.

A missing or duplicated origin mapping is a stop. A duplicate byte does not
permit silent aliasing, omission, or shared-store promotion.

## Selection packets and human decisions

### Custody decision

The responsible human accepts, revises, or defers:

- the ordinary and restricted root pseudonyms;
- exact ordinary and restricted member inventories;
- mode/size/hash and origin closure;
- ordinary/restricted separation controls;
- package-specific retention and deletion prohibition; and
- whether the candidate is sufficient to proceed to later K0-SC1 decisions.

### Host-selection decision

The host packet must enumerate exact existing candidate IDs and their complete
mode/size/hash/provenance dispositions. The responsible human selects one,
requests revisions, or defers. A candidate name, release string, branch,
manifest pass, or available board does not select it.

### Selftest and skip decisions

The combined packet must enumerate:

- exact ST01-ST16 IDs, names, order, argv, cwd, environment, timeouts, output
  limits, exits, and markers; and
- exact ST16 skip identity, exit `4`, marker, reason, evidence source, and
  outside-KVM0 rationale.

The packet contains no selftest binary bytes or hashes, install tree,
18-entry runner/controller/16-binary install manifest, or final structured
command manifest. Accepted K0-SC assigns those identities and constructions
to K0-SC2. C5 values neither satisfy nor pre-approve any K0-SC2 obligation.

The responsible human separately approves, revises, or defers the test set
and the skip. K0-I schema placeholders and prior observations do not approve
either decision.

### Source-ref report disposition

The report preserves the source relation as `recorded-not-accepted` and
contains:

- exact local-ref records;
- exact tracking-ref records;
- remote status as either a separately authorized read-only check with time
  and command identity, or `NOT RUN`; and
- ref governance and drift findings.

The authorization supplies one exact `ref_binding_attachment` with no extra
fields:

```json
{
  "relation_id": "<opaque-source-relation-record-id>",
  "local_record_count": 0,
  "local_records": [
    {
      "record_id": "<opaque-record-id>",
      "sha256": "<64-lowercase-hex>"
    }
  ],
  "tracking_record_count": 0,
  "tracking_records": [
    {
      "record_id": "<opaque-record-id>",
      "sha256": "<64-lowercase-hex>"
    }
  ],
  "remote_state": "<exact-observed-state-or-NOT RUN>",
  "remote_check_time": "<RFC3339-with-offset-or-NOT RUN>",
  "remote_command_id": "<K0-SC1-operational-command-id-or-NOT RUN>",
  "governance_findings": ["<stable-finding-id>"],
  "drift_findings": ["<stable-finding-id>"]
}
```

Rules:

- record arrays are sorted by raw UTF-8 ID bytes and contain no duplicate ID;
- each count equals the corresponding array length;
- every record contains exactly one opaque ID and SHA-256 pair;
- `relation_id` resolves to the authorization's exact source relation;
- concrete remote state requires a concrete check time and command ID;
- remote state `NOT RUN` requires both remote fields to equal `NOT RUN`;
- governance and drift arrays are mandatory, with `[]` representing no
  observed finding; and
- `controls/source-ref-report-v1.json` reproduces the same attachment without
  substitution.

The attachment and reproduced control are serialized as strict UTF-8, and
parsed string values contain only Unicode scalar values. Raw ID ordering
remains ordering by exact serialized UTF-8 bytes; no normalization or
casefolding applies to ref IDs. Invalid encoding makes the authorization
non-conforming.

The human accepts, revises, or defers the report disposition only. This is not
source-relation acceptance, protected-ref proof, readiness, or immutable
custody.

## Separate implementation authorization

Plan acceptance does not authorize K0-SC1. A future exact instruction must
name all of:

```text
package=K0-SC1
accepted_k0sc_plan=33f35981483bccbc4e3a1c87f4a5af52e0e15d41
accepted_k0sc_record=b36190352d270ce9ed70a6ddab8f4c7e7030f4e6
accepted_k0sc1_plan=<future-exact-plan-target>
beryllium_full_base=<full-40-hex-SHA>
source_relation=<exact-base-candidate-tree-patch-count-release>
profile_relation=<exact-files-paths-checksums-and-control-hashes>
recovered_relation=<exact-record-set-and-host-manifest-identities>
decision_classes=C1,C2,C3,C4,C5,C6
ref_binding_attachment=<complete-exact-attachment>
host_path_encoding=ordinary-host-by-row-v1:utf8-strict:unicode-<exact-UCD-version>:k0sc1-unicode-profile-v1
external_root_ids=<ordinary-and-restricted-pseudonyms>
exact_path_mode_inventory=<complete-authorization-attachment>
path_count_formulas=<this-plan-formulas>
tool_locks=<complete-executable-library-plugin-table-and-runtime-data-closure>
k0sc1_operational_commands=<exact-argv-cwd-environment-timeout-limit-exit-output-marker-contracts>
final_structured_command_manifest=deferred-to-K0-SC2
output_and_retention_boundaries=<package-specific-only>
size_caps=<exact-integers-within-this-plan-maxima>
mandatory_stop_ids=I1,I2,I3,I4,I5,I6,I7,A1,A2,A3,A4,A5,A6,A7,A8,A9
exclusions=<all-plan-non-authorizations>
```

Private locators are supplied out of band and never retained in Git. Every
command is a structured argv array; ambient `PATH`, shell evaluation, network
access, source mutation, board access, device access, and package-manager
resolution are forbidden unless separately and explicitly named. The optional
remote-ref check requires its own read-only network clause; otherwise it is
`NOT RUN`.

## Permitted future K0-SC1 work

Only a later exact authorization may permit:

- read-only local Git-object/ref inspection;
- metadata, stat, mode, size, and SHA-256 verification;
- deterministic origin/duplicate/privacy classification;
- bounded copying into the two named package-specific custody roots;
- deterministic creation of the eight control files;
- host and selection-only selftest/skip decision packet generation; and
- an optional separately authorized read-only remote-ref observation.

K0-SC1 operational commands may build custody and decision-support records
only. They do not create K0-SC2 selftest binaries, an install tree, the
18-entry install manifest, or the final structured command manifest.

No source repository, preparation package, recovered record, host input, or
restricted mapping may be modified. Original inputs remain authoritative for
comparison.

## Exit condition

K0-SC1 exits only after:

1. exact custody candidate checks pass without drift or privacy failure;
2. the responsible human accepts, revises, or defers the custody decision;
3. the responsible human selects, revises, or defers the host candidate;
4. the responsible human approves, revises, or defers the ST01-ST16 set;
5. the responsible human approves, revises, or defers the ST16 skip;
6. the responsible human accepts, revises, or defers the source-ref report
   disposition; and
7. one exact K0-SC1 candidate and decision-neutral review packet exist.

A passing checker, inventory, custody copy, branch, report, or package cannot
make any decision or start K0-SC2.

## Stop conditions

K0-SC1 stops on every accepted K0-SC1 stop:

1. **I1** - recovered-record or host-manifest hash, mode, size, type, or count
   drift;
2. **I2** - missing or duplicated origin mapping;
3. **I3** - restricted material entering Git, ordinary custody, ordinary archive,
   K0-I import, report, or publication output;
4. **I4** - need for a general evidence store or any blocked Phase 2 decision;
5. **I5** - source-relation drift or candidate-ref rewrite;
6. **I6** - any seventh disposition class outside C1-C6; or
7. **I7** - any need to access the board, rebuild or recapture bytes, run QEMU, run a
   guest, run real KVM selftests, or begin another K0-SC package.

It also stops on:

- **A1** - path/mode/count formula disagreement;
- **A2** - symlink, hard link, special file, path escape, collision, unsafe mode, or
  undeclared executable;
- **A3** - privacy leakage or a private locator entering an ordinary output;
- **A4** - output-root reuse, mutable overwrite, append, or partial success shaping;
- **A5** - missing tool/command provenance;
- **A6** - a size cap violation;
- **A7** - source/profile/recovered-input mutation;
- **A8** - a selection packet not marked pending human decision; or
- **A9** - an active writer, stale authority, unexpected seventh maintained path, or
  unavailable exact base.

For A2, Unicode-casefold equivalence among original host member paths alone is
diagnostic under K0-SC1-B when every raw and non-casefold original-path
predicate passes and the uniform by-row mapping is used. A2 remains mandatory
for every raw/NFC/other normalized original-path defect, unsafe object/path,
invalid UTF-8 or Unicode transform/encoding failure, and any file/file,
directory/directory, or file/directory collision under raw, NFC,
NFC-casefold, or NFKC-casefold keys in the occurrence-preserving final
ordinary tree.

For host-row schema validation, a row matching both variants or neither,
field omission, custody nullability violation, original-metadata rewrite,
invalid custody tuple, disposition/reason mismatch, invalid expected copy
count, or host split/count mismatch is A1. I1, I2, and A2 additionally apply
when the underlying defect is respectively input drift, missing/duplicated
origin mapping, or an unsafe object/path/mode.

Missing, mismatched, unbound, unresolved, non-regular, extra, mixed-version,
fallback-dependent, or dynamically unverifiable Unicode tool/data closure is
A5. A private Unicode tool/data locator entering Git or ordinary output is
A3. No mapping adds a seventeenth stop or weakens the accepted wording of
I1-I7 or A1-A9.

Every authorization must contain the exact ordered literal:

```text
mandatory_stop_ids=I1,I2,I3,I4,I5,I6,I7,A1,A2,A3,A4,A5,A6,A7,A8,A9
```

All 16 IDs are mandatory. No authorization may omit, disable, rename, or
substitute an ID. Each ID binds the exact wording above.

No stop authorizes repair, substitution, deletion, reconstruction, or scope
expansion.

## Relationship to later packages

K0-SC1:

- does not create K0-SC2 replacement inputs;
- does not access K0-SC3 or the board;
- does not reconcile offline and live identities;
- does not create the final 15-control K0-A payload or external archive;
- does not import through K0-I;
- does not make K0-S ready; and
- does not authorize K0-X or any successor.

K0-SC2 remains separately planned and unauthorized. K0-SC3 remains
separately planned, unauthorized, and `NOT RUN` even though the board is
human-reported online.

K0-SC2 owns:

- exact selftest binaries and hashes;
- construction and hashing of the runner/controller/16-binary install tree;
- the 18-entry install manifest; and
- the final structured command manifest.

K0-SC1 C5 names/order/argv/cwd/environment/timeouts/limits/exits/markers
neither satisfy nor pre-approve those K0-SC2 obligations.

## Plan path and mode boundary

This proposed plan target may change exactly:

```text
100644 planning/k3-kvm0-k0sc1-plan.md
100644 planning/roadmap.md
100644 planning/project-orientation.md
100644 planning/README.md
100644 planning/HANDOFF.md
```

A sixth path, glossary change, VitePress configuration, browser inventory,
generated HTML/SVG, accepted-plan or acceptance-record edit, source/profile
path, runtime/tooling path, dependency, policy/instruction file, or
publication-gate change is a stop requiring a revised plan.

The later decision-neutral review packet may change only:

```text
100644 planning/k3-kvm0-k0sc1-plan-k0sc1b-corrected-review-summary.md
100644 planning/roadmap.md
100644 planning/project-orientation.md
100644 planning/README.md
100644 planning/HANDOFF.md
```

That packet may review one exact proposed-plan target. It may not rewrite the
target, record acceptance, or authorize implementation.

## Validation for the proposed plan

The exact proposed-plan target requires:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

It additionally requires:

- exact five-path and mode-`100644` inventory from base
  `e1cd15a72e84304812a7c893d5b3a8c4990ea628`;
- byte-identical preservation of accepted original target
  `9b9923f8a58fe7102a108cb2a976ea09979427a1`, its review and acceptance
  record, accepted K0-SC1-A target and record, and their plan/packet blobs;
- six-class traceability and rejection of a seventh class;
- exact C5 field set: IDs/names, order, argv, cwd, environment, timeouts,
  limits, exits, and markers, with no binary/install/final-manifest ownership;
- exact numeric maxima and file arithmetic, occurrence-preserving file and
  directory counts, ordinary/root directory mode `0755`, restricted
  directory mode `0700`, depth `64`, directory maximum `4096`,
  `FILES.modes` row maximum `6191`, caps, and exit decisions;
- exact `ref_binding_attachment` key set, count/array/hash/relation/remote tuple
  rules, and source-ref report equality;
- exactly 16 stop definitions `I1-I7,A1-A9`, each once, with the same ordered
  literal in the authorization template and validation;
- exact host mapping grammar
  `ordinary/host/by-row/<row-4d>.bin`, manifest row range `0001..2030`,
  fixed path bytes `29`, depth `4`, lowercase ASCII grammar, exact
  eligible-custody/metadata-only partition, required nullability and
  copy-count equalities, and no content deduplication;
- preservation of every raw/NFC/unsafe original-host predicate, relaxation of
  original-host casefold equivalence only, occurrence-preserving node tags,
  no pre-check collapse, and all twelve final-tree file/file,
  directory/directory, and file/directory checks under raw, NFC,
  NFC-casefold, and NFKC-casefold keys;
- exact strict-UTF-8 decoder, transform ordering, full default non-Turkic
  locale-independent folding, identical `host_path_encoding` values, one UCD
  version, complete Unicode tool/data closure, failure injection, and
  fail-closed A2/A3/A5 behavior;
- K0SC-R4 traceability as `OPEN`, `DEFINITION UNKNOWN`, unwaived, with exact
  evidence/blocking boundary and responsible-human question;
- privacy scan for locators, credentials, human-readable restricted
  identities, host/device identifiers, network addresses, and sensitive
  absolute paths;
- zero generated-tree or Chromium work;
- no network, board, source/profile, custody-copy, selection, import, archive,
  runtime, proof, or publication action; and
- explicit unchanged-byte audit for accepted K0-A/K0-I/K0-S/K0-SC targets and
  records, KVM0 tooling, runtime/model/pathfinder content, dependencies,
  policies, instructions, and publication gate.

## Claim and non-claim boundary

This plan supports saying only:

- one bounded corrected K0-SC1-B target is proposed over exact
  revisions-requested base `e1cd15a72e84304812a7c893d5b3a8c4990ea628`;
- four casefold groups covering eight rows are aggregate draft-time input,
  not accepted custody evidence;
- a uniform by-row host custody path is proposed for every eligible regular
  host row, with original metadata retained and no selection, omission,
  source rename, aliasing, or content deduplication;
- original-host casefold equivalence alone is proposed relaxed while tagged
  occurrences and twelve raw/NFC/NFC-casefold/NFKC-casefold final-tree
  collision checks remain mandatory;
- host rows are proposed as one exact eligible-custody or metadata-only
  variant with explicit nullability and expected copy counts;
- future authorization is proposed to bind strict UTF-8 and one complete,
  exact, fail-closed Unicode implementation/data closure without selecting
  those dependencies now;
- `restricted-search-quality` is proposed traceable as K0SC-R4 while its
  substantive definition remains unknown, open, and unwaived;
- exactly six disposition classes, eight controls, existing numeric maxima
  and file arithmetic, ref binding, and 16 mandatory stops remain unchanged;
- package-specific ordinary/restricted custody remains separate from blocked
  evidence-retention Phase 2;
- the board is human-reported online, but K0-SC3 and hardware remain
  unauthorized and `NOT RUN`; and
- exact later human authorization and decisions remain mandatory.

It does not claim:

- the A2 blocker is resolved, custody paths have been implemented or checked,
  or any colliding member has been selected, omitted, renamed, or copied;
- K0SC1B-F1/F2/F3/F4 are accepted, implemented, or empirically closed;
- K0SC-R1/R2/R3/R4 are resolved or waived, or a substantive K0SC-R4
  definition has been supplied;
- Unicode conformance certification, a collision-free final tree, or a
  complete tool/data closure exists;
- K0-SC1 plan acceptance, implementation authorization, custody, preservation,
  immutability, selection, or remote verification;
- evidence-store deployment, encryption, secondary replication, indexing,
  lifecycle, restore policy, or retention approval;
- source relation, host set, profile, selftest set, skip, package, or K0-S
  acceptance;
- historical-byte recovery, rebuild, recapture, board characterization,
  KVM0 execution, K3 qualification, or hardware evidence;
- K0-SC2, K0-SC3, final package/archive, K0-I import, K0-S readiness, K0-X,
  K0-R, B0/B1, R8 successor, Linux/BSP, service, device, DMA, multicore,
  policy, attestation, or MVP authority; or
- push, tag, publication, release, migration, paper submission,
  collaboration commitment, venue selection, or upstream submission.

## Decision required

After one exact corrected K0-SC1-B target and decision-neutral packet exist,
the
responsible human may:

1. accept the exact corrected K0-SC1-B revision target;
2. request a revised target; or
3. defer K0-SC1.

Acceptance would approve the collision-path planning correction only. It
would authorize no K0-SC1 implementation. A later exact instruction must
satisfy the revised authorization template and implementation-time A2 checks
above.
