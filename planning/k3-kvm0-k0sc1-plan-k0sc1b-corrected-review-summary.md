<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Corrected KVM0 K0-SC1-B plan revision review summary

This is the decision-neutral responsible-human review packet for exact
corrected K0-SC1-B target
`13463e4f8473e4a5497ef60f92f284ea4f9944f5`. It supports a decision on
that immutable commit only. It does not record acceptance, authorize K0-SC1
implementation, resolve A2, or change any custody, selection, source,
hardware, readiness, successor, publication, or release gate.

## 1. Decision summary

| Field | Review value |
| --- | --- |
| Review target | Exact commit `13463e4f8473e4a5497ef60f92f284ea4f9944f5` (`docs: propose corrected K0-SC1-B revision`) |
| Parent / comparison base | `e1cd15a72e84304812a7c893d5b3a8c4990ea628` |
| Git tree | `2d8ea7cdfc76c75466c11fbaefed3a6f3b55d32b` |
| Accepted predecessor | K0-SC1-A target `c00f4d000c845a7c3d62921c1d7939fc158744e2`, accepted as planning corrections only |
| Unaccepted predecessor | First K0-SC1-B target `1ce71e73078a65a271949d84db47343e4eaacf14`, packet `d4bbba7950a1f375a2a012a43e5ad54a6716eceb`, and revisions-requested record `e1cd15a72e84304812a7c893d5b3a8c4990ea628` remain immutable decision support |
| Current status | Corrected K0-SC1-B target is proposed, exact-clean source-checked, not responsible-human reviewed or accepted |
| Automated review disposition | **Revisions recommended before acceptance:** four high and three medium findings remain open |
| Decision requested | Request revisions, accept exact target as written, or defer |
| Implementation / execution | K0-SC1 implementation, custody, selection, private-input execution, and remote-ref checking remain unauthorized or `NOT RUN`; K0-S remains `not-ready` |
| Successor / hardware status | K0-SC2 and K0-SC3 remain unauthorized; K0-SC3 and Beryllium/R8 K3 hardware remain `NOT RUN`; K0-X/K0-R and official B0 remain blocked |
| Repository / branch | Current private Beryllium repository; `beryllium/single-hart-runtime-r0` |
| Push / tag state | Target is the clean local branch tip, 21 commits ahead of the last-fetched tracking ref, untagged, and absent from local remote-tracking containment; no network recheck was performed |
| Publication status | Push, tag, public migration, publication, release, paper submission, collaboration commitment, and upstream submission remain blocked |

**Action expected:** review exact target
`13463e4f8473e4a5497ef60f92f284ea4f9944f5`, especially
K0SC1B-CF1 through K0SC1B-CF7, and respond with request revisions, accept,
or defer.

This packet's later follow-up commit is decision support only. It is not plan
content and cannot authorize K0-SC1.

## 2. Deliverables

The exact parent-to-target delta is five modified mode-`100644` planning
paths:

```text
M planning/HANDOFF.md
M planning/README.md
M planning/k3-kvm0-k0sc1-plan.md
M planning/project-orientation.md
M planning/roadmap.md
```

The target contains 358 insertions and 64 deletions.

| Deliverable | Paths | Purpose | Trust or privilege boundary | Highest-value review question |
| --- | --- | --- | --- | --- |
| Corrected K0-SC1-B revision | `planning/k3-kvm0-k0sc1-plan.md` | Propose text corrections for K0SC1B-F1 through F4 | Planning text only; accepted and unaccepted predecessor history remains immutable | Do the corrected contracts remove the original findings without introducing ambiguity or regression? |
| Current-position placemat | `planning/roadmap.md` | Record bounded correction authority, proposed status, exact base, residuals, and unchanged gates | Status only | Does the placemat avoid implying acceptance, A2 resolution, or implementation authority? |
| Returning-human guide | `planning/project-orientation.md` | Explain the corrected proposal and unchanged critical path | Re-entry guidance only | Can a returning owner distinguish proposed text corrections from implemented custody behavior? |
| Planning index | `planning/README.md` | Summarize and navigate the corrected proposal | Navigation-level status only | Does discoverability preserve the revisions-requested predecessor and new proposed status? |
| Operational handoff | `planning/HANDOFF.md` | Preserve exact drafting authority, proposed corrections, and non-authorizations | Handoff only | Can a later session resume without treating review findings or draft text as authority? |

No accepted original or K0-SC1-A plan/packet/record, prior K0-SC1-B
target/packet/decision record, K0-A/K0-I/K0-S/K0-SC record, KVM0 destination
tool, runtime, model, proof, dependency, policy, instruction, generated page,
or publication-gate byte changes in the target.

The authoritative controls reviewed for this packet are
`planning/k3-kvm0-k0sc1-plan.md`,
`planning/k3-kvm0-k0s-completion-plan.md`, `planning/k3-kvm0-plan.md`,
`planning/HANDOFF.md`, `planning/roadmap.md`, and
`LLM_POLICY_ALIGNMENT.md`.

## 3. Claim boundary

### Supported by the exact target

The target supports saying:

- a corrected K0-SC1-B planning target is proposed over exact
  revisions-requested base
  `e1cd15a72e84304812a7c893d5b3a8c4990ea628`;
- the original uniform host-row custody mapping remains proposed;
- intended final files and directories are represented by tagged
  occurrences, with twelve proposed collision predicates across raw, NFC,
  NFC-casefold, and NFKC-casefold keys;
- host rows are proposed as exactly one eligible-custody or metadata-only
  variant with explicit nullability and expected copy counts;
- future authorization is proposed to bind strict UTF-8, one exact UCD
  version, full default non-Turkic locale-independent folding, and complete
  executable/data closure;
- `restricted-search-quality` is proposed traceable as K0SC-R4 while its
  substantive definition remains `UNKNOWN`, open, and unwaived; and
- six classes, eight controls, existing numeric maxima and file arithmetic,
  ref binding, and all 16 stop IDs remain.

### Trusted or assumed inputs

Four casefold-equivalence groups covering eight rows remain unrederived,
session-private draft-time input. The target does not retain member names or
claim those observations as custody evidence.

The 2,030-row manifest order, eligibility, path/type/mode/hash identities,
directory declarations, Unicode implementation/data closure, and every
aggregate count remain future implementation-time rederivation obligations.
No private input was accessed for this target or review.

The branch's ahead state is a last-fetched local-ref observation; no remote
server was queried.

### Unavailable or `NOT RUN`

- no custody tree, mapping, copy, selection, checksum, or package exists;
- no occurrence sequence or complete directory closure has been constructed;
- no final collision checker or host-row schema checker has executed;
- no Unicode version, implementation, tool, package, data closure, or command
  has been selected or run;
- no substantive K0SC-R4 definition or closure evidence exists;
- no remote-ref check or board access occurred;
- K0-SC1 implementation remains unauthorized; and
- K0-SC2, K0-SC3, package assembly, import, readiness, K0-X, K0-R, official
  B0, hardware, push, tag, publication, and release remain `NOT RUN`,
  blocked, or unauthorized.

### Explicit non-claims

The target does not:

- resolve A2 or prove a future final tree collision-free;
- establish that the proposed F1/F2/F3/F4 corrections are complete,
  accepted, implemented, or empirically closed;
- select, omit, rename, merge, reindex, alias, deduplicate, copy, or prefer
  any host row or directory declaration;
- establish custody, stable preservation, source relation acceptance, host or
  selftest selection, package acceptance, or readiness;
- establish Unicode conformance certification or a complete tool/data closure;
- define, resolve, or waive K0SC-R1 through K0SC-R4;
- authorize network, board, QEMU, guest execution, real KVM selftests, import,
  readiness, or successors;
- establish KVM0 execution, K3 qualification, Beryllium hardware validation,
  retained-R8 evidence, Linux/BSP selection, official B0/B1, services,
  devices, DMA, multicore, policy, attestation, or an MVP; or
- authorize push, tag, publication, release, migration, paper submission,
  collaboration outreach, venue selection, or upstream submission.

## 4. Security and correctness invariants

| Invariant | Target location | Proposed control | Evidence or review boundary |
| --- | --- | --- | --- |
| No row/node disappears before collision checks | Corrected revision; hard maxima; final-tree uniqueness | Tagged `F_occ`/`D_occ` sequences and no path-keyed pre-check collapse | Textual proposal only; parent-sharing identity is ambiguous, K0SC1B-CF1 |
| Directory coverage is total | Hard maxima and final-tree uniqueness | Intended directory declarations and occurrence counts | Proper-parent closure is not required, K0SC1B-CF2 |
| Host rows have one total schema | Ordinary input paths; origin handling | Eligible-custody versus metadata-only variants | Non-host custody schema regressed, K0SC1B-CF3 |
| Casefold collision forms are complete | Mandatory final-tree uniqueness | Four key forms and twelve predicates | Proposed ordering has a false negative, K0SC1B-CF4 |
| Original path safety remains fail-closed | Ordinary input paths; stops | Raw/NFC/object/mode/origin predicates remain | Original-host casefold-only diagnostic exception stays bounded |
| Unicode dependencies are explicit and private | Uniqueness; authorization template; stops | Strict decoding, future exact UCD, complete lock closure, A2/A3/A5 | No concrete dependency selected or run |
| Residual finding is traceable but not defined | Residual findings; claim boundary | K0SC-R4 ID, evidence limit, human question, no auto-close | Definition remains `UNKNOWN` and unwaived |
| Board availability grants no board authority | Status and current pages | Human report remains non-evidentiary; K0-SC3/hardware `NOT RUN` | No board contact occurred |

## 5. Review history and resolved/open findings

### Preserved predecessor history

- Original K0-SC1 is accepted as planning text only.
- K0-SC1-A is accepted as planning corrections only.
- First K0-SC1-B target
  `1ce71e73078a65a271949d84db47343e4eaacf14` remains unaccepted; the
  responsible human requested revisions to K0SC1B-F1 through F4.
- Exact decision record
  `e1cd15a72e84304812a7c893d5b3a8c4990ea628` separately authorized
  drafting the bounded corrected target, not implementation.

### Original findings

K0SC1B-F1 through K0SC1B-F4 are proposed addressed by the target text. The
independent exact-target review found the following new issues. None was fixed
in the immutable target.

| ID | Significance | Confidence | Target location | Finding and human question |
| --- | --- | ---: | --- | --- |
| K0SC1B-CF1 | **High; revision recommended** | 8/10 | Hard maxima; final-tree uniqueness | Parent sharing is said to use one directory node, while independent declarations with equal bytes remain distinct, but no non-path trigger distinguishes them. Must every node carry an explicit parent-declaration tag, with sharing decided only by tag identity? |
| K0SC1B-CF2 | **High; revision recommended** | 8/10 | Hard maxima; final-tree uniqueness | `D_occ` no longer requires the complete proper-parent closure of every file occurrence. Must the plan restore exact parent-chain totality and make missing/extra directory nodes A1? |
| K0SC1B-CF3 | **High; revision recommended** | 8/10 | Origin and duplicate handling | The universal custody-field list was narrowed to host rows, leaving discovery, profile, and control rows without explicit custody tuple/copy requirements while claiming non-host schemas are unchanged. Must the universal non-host schema be restored explicitly? |
| K0SC1B-CF4 | **High; revision recommended** | 9/10 | Mandatory final-tree uniqueness | The NFC-based casefold ordering has a demonstrated canonical-caseless false negative. Must the keys use the normative decomposition/casefold ordering, with names and validation updated consistently? |
| K0SC1B-CF5 | **Medium; revision recommended** | 7/10 | Host variants; origin handling; stops | Metadata-only dispositions do not distinguish recordable outcomes from record-and-stop outcomes; the zero-valued-metadata ban conflicts with `expected_copy_count=0`; and disposition/reason pairing lacks a checkable vocabulary. What exact partition and pairing rules apply? |
| K0SC1B-CF6 | **Medium; revision recommended** | 7/10 | Hard maxima; final-tree uniqueness | `ordinary_directory_count` includes the external root, but `FILES.modes` records paths and the root has no relative path, creating a possible one-row ambiguity. Is the root represented by a fixed token or excluded from `FILES.modes` arithmetic? |
| K0SC1B-CF7 | **Medium; revision recommended** | 8/10 | Corrected scope; source-ref encoding; authorization | Strict ref-attachment encoding is an unenumerated correction, `k0sc1-unicode-profile-v1` is undefined, and the literal drafting instruction is rendered as drafting-and-review authority. Should these scope and identifier bindings be made explicit? |

Additional observations for a later revision:

- custody size/hash should be observed from the written file and compared
  with originals, not treated as definitional equalities;
- directory declarations should state how conditional host parents are bound;
- JSON mode representation should be typed explicitly; and
- the target's forward packet-path field is frozen pre-packet content and
  should not be confused with an artifact present in the target tree.

Independent review found no significant issue with the arithmetic maxima,
manifest-row filename grammar, six classes, eight controls, 16-stop literal,
K0SC-R4 evidence boundary, privacy boundary, or the explicit
non-authorizations.

## 6. Validation and retained evidence

### Pre-commit equivalent-content validation

Equivalent five-path content passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

The source check reported:

```text
site_markdown=98
policy_markdown=5
rendered_references=925
configured_routes=221
tracked_html=0
network_events=0
generated_tree_changes=0
adversarial_cases=34
```

Additional fail-closed checks covered the five-path/mode boundary, no
generated changes, privacy, no concrete Unicode dependency selection,
unchanged historical records, and no Git writer or operation state.

### Exact-clean-target validation

On October 5, 2026, exact clean target
`13463e4f8473e4a5497ef60f92f284ea4f9944f5` passed:

```text
git diff --check \
  e1cd15a72e84304812a7c893d5b3a8c4990ea628 \
  13463e4f8473e4a5497ef60f92f284ea4f9944f5
umask 0022 && npm run docs:source-check
```

The exact-target source check reported the same `98/5/925/221` source counts,
zero tracked HTML, zero network events, zero generated-tree changes, and 34
adversarial cases. The worktree remained clean.

Exact-target audit also confirmed:

- five modified mode-`100644` planning paths;
- tree `2d8ea7cdfc76c75466c11fbaefed3a6f3b55d32b`;
- unchanged accepted and prior unaccepted target/packet/decision histories;
- exact target status `proposed-not-reviewed`, decision `pending`, and
  implementation `not-authorized`; and
- last-fetched local branch state: 21 ahead, zero behind, untagged.

### Packet-follow-up validation

On October 5, 2026, this packet and its four minimal status links passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

The packet source check reported:

```text
site_markdown=99
policy_markdown=5
rendered_references=929
configured_routes=221
tracked_html=0
network_events=0
generated_tree_changes=0
adversarial_cases=34
```

Fail-closed follow-up checks also confirmed the exact five-path
mode-`100644` boundary, unchanged target-plan and accepted/history blobs, 212
resolving relative Markdown links, no private locator or credential in added
lines, and no generated-tree change. Because the new packet was initially
untracked, a separate no-index whitespace check covered it in addition to
`git diff --check`.

Packet validation covers decision support and status integration only. It
cannot accept the target or authorize implementation.

## 7. Recommended human review sequence

1. Confirm target, parent, tree, five-path inventory, authority, and
   proposed/not-reviewed status.
2. Confirm the predecessor target/packet/decision and accepted K0-SC1-A
   remain immutable history.
3. Review K0SC1B-CF1 and CF2 together: directory identity and complete parent
   closure.
4. Review K0SC1B-CF3 and CF5: universal inventory schema and host-only
   variant semantics.
5. Review K0SC1B-CF4: Unicode caseless-key ordering and the demonstrated false
   negative.
6. Review K0SC1B-CF6 and CF7: row arithmetic and exact scope/identifier
   bindings.
7. Confirm K0SC-R1 through R4, A2, privacy, hardware, successor, and
   publication boundaries remain open or blocked.
8. Review exact-clean-target validation and packet-link integration.

Useful read-only commands:

```sh
git --no-pager show --stat --summary \
  13463e4f8473e4a5497ef60f92f284ea4f9944f5
git --no-pager diff --find-renames \
  e1cd15a72e84304812a7c893d5b3a8c4990ea628 \
  13463e4f8473e4a5497ef60f92f284ea4f9944f5 -- \
  planning/k3-kvm0-k0sc1-plan.md \
  planning/roadmap.md planning/project-orientation.md \
  planning/README.md planning/HANDOFF.md
git --no-pager show \
  13463e4f8473e4a5497ef60f92f284ea4f9944f5:planning/k3-kvm0-k0sc1-plan.md
```

If rerunning executable checks against the exact target, use an isolated
detached worktree so unrelated local changes cannot affect the result:

```sh
review_root="$(mktemp -d)"
review_dir="$review_root/worktree"
git worktree add --detach "$review_dir" \
  13463e4f8473e4a5497ef60f92f284ea4f9944f5
(
  cd "$review_dir"
  git diff --check \
    e1cd15a72e84304812a7c893d5b3a8c4990ea628 \
    13463e4f8473e4a5497ef60f92f284ea4f9944f5
  umask 0022
  npm run docs:source-check
)
git worktree remove "$review_dir"
rmdir "$review_root"
```

## 8. Human decision checklist

- [ ] The exact target, parent, tree, and five-path inventory match.
- [ ] The correction scope matches the F1-F4 drafting authority.
- [ ] Claims match exact-target evidence and explicit non-claims.
- [ ] Trusted draft-time inputs and unavailable evidence are acceptable.
- [ ] Parent sharing and proper-parent closure are fully deterministic.
- [ ] Universal non-host and host-row schemas are total and unambiguous.
- [ ] Unicode key ordering detects the intended caseless collisions.
- [ ] Metadata-only stop, nullability, reason, and copy-count rules are checkable.
- [ ] Directory and `FILES.modes` arithmetic has one exact root convention.
- [ ] K0SC-R1 through K0SC-R4 and A2 remain open and unwaived.
- [ ] Important negative paths remain bound to fail-closed stop conditions.
- [ ] No custody, implementation, board, successor, push, publication, or release authority follows.
- [ ] Exact target `13463e4f8473e4a5497ef60f92f284ea4f9944f5` is accepted, revisions are requested, or review is deferred.

## 9. After the decision

### If accepted

Record acceptance of exact target
`13463e4f8473e4a5497ef60f92f284ea4f9944f5` in a separate follow-up.
Acceptance would approve the bounded corrected planning text only. It would
not resolve A2 through implementation evidence, authorize K0-SC1, custody,
selection, remote or board access, K0-SC2/K0-SC3, readiness, K0-X/K0-R,
official B0, push, publication, or release.

### If revisions are requested

A future separately authorized task may create a new exact revision target
and packet. Preserve this target and packet as unaccepted decision support.
Do not alter the immutable target to repair K0SC1B-CF1 through CF7.

### If deferred

Preserve the target and packet as decision support. Do not start K0-SC1 or
dependent work.

**Status:** exact target
`13463e4f8473e4a5497ef60f92f284ea4f9944f5` is proposed,
source-checked, independently reviewed, and not accepted. Automated review
recommends revisions for four high and three medium findings.

**Next:** responsible-human request revisions, accept exact target as written,
or defer.

**Action required from you:** review K0SC1B-CF1 through K0SC1B-CF7 and choose
one of those three outcomes. No implementation authority is implied.
