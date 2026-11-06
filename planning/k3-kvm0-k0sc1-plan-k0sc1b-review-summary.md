<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# KVM0 K0-SC1-B plan revision review summary

This is the decision-neutral responsible-human review packet for exact Plan
revision K0-SC1-B target
`1ce71e73078a65a271949d84db47343e4eaacf14`. It supports a decision on that
immutable commit only. It does not record acceptance, authorize K0-SC1
implementation, resolve A2, or change any custody, selection, source,
hardware, readiness, successor, publication, or release gate.

## 1. Decision summary

| Field | Review value |
| --- | --- |
| Review target | Exact commit `1ce71e73078a65a271949d84db47343e4eaacf14` (`docs: propose K0-SC1-B path revision`) |
| Parent / comparison base | `06cda3814426de940afadb05cd5cf59ee8253688` |
| Git tree | `de7b9023153023cb12d32367eb48a832030981a7` |
| Accepted predecessor | K0-SC1-A target `c00f4d000c845a7c3d62921c1d7939fc158744e2`, accepted as planning corrections only; original K0-SC1 and K0-SC1-A history remains immutable |
| Current status | Revisions requested on October 5, 2026; exact target remains unaccepted and immutable decision support |
| Automated review disposition | **Revisions recommended before acceptance:** one high and three medium findings remain open |
| Decision requested | **Decision complete:** revisions requested for K0SC1B-F1 through K0SC1B-F4 |
| Implementation / execution | K0-SC1 implementation, custody, selection, and remote-ref checking remain unauthorized or `NOT RUN`; K0-S remains `not-ready` |
| Successor / hardware status | K0-SC2 and K0-SC3 remain unauthorized; K0-SC3 and Beryllium/R8 K3 hardware remain `NOT RUN`; K0-X/K0-R remain blocked |
| Repository / branch | Current private Beryllium repository; `beryllium/single-hart-runtime-r0` |
| Push / tag state | Target is the clean local branch tip, 18 commits ahead of the last-fetched tracking ref, untagged, and absent from local remote-tracking containment; no network recheck was performed |
| Publication status | Push, tag, public migration, publication, release, paper submission, collaboration commitment, and upstream submission remain blocked |

**Responsible-human decision:** on October 5, 2026, at
`2026-10-05T21:53:34.643+02:00`, the responsible human instructed:

> Request revisions to exact K0-SC1-B target
> `1ce71e73078a65a271949d84db47343e4eaacf14` for findings F1-F4.

In that instruction, `F1-F4` means exactly K0SC1B-F1, K0SC1B-F2,
K0SC1B-F3, and K0SC1B-F4 in this packet. It does not refer to K0SC1-F1,
K0SC1-F2, K0SC1-F3, K0SC-R1, K0SC-R2, K0SC-R3, or another finding set.

The decision selects the packet's **request revisions** outcome. Exact target
`1ce71e73078a65a271949d84db47343e4eaacf14` and packet commit
`d4bbba7950a1f375a2a012a43e5ad54a6716eceb` remain immutable, unaccepted
decision support. This follow-up records the decision only. It grants no
authority to draft a replacement, implement K0-SC1, or start dependent work.

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

The target contains 226 insertions and 28 deletions.

| Deliverable | Paths | Purpose | Trust or privilege boundary | Highest-value review question |
| --- | --- | --- | --- | --- |
| K0-SC1-B revision | `planning/k3-kvm0-k0sc1-plan.md` | Replace host member-path custody names with a uniform manifest-row namespace and require final-tree collision checks | Planning text only; accepted predecessor remains immutable history | Is the mapping and collision contract complete enough to accept without pre-approving implementation? |
| Current-position placemat | `planning/roadmap.md` | Record accepted predecessor, proposed revision, pending decision, and unchanged gates | Status only | Is A2 visibly proposed addressed rather than closed? |
| Returning-human guide | `planning/project-orientation.md` | Explain the proposed by-row mapping and unchanged package/hardware boundary | Re-entry guidance only | Can a returning owner distinguish original-path diagnostics, custody paths, and implementation validation? |
| Planning index | `planning/README.md` | Link and summarize the proposed revision | Navigation-level status only | Does discoverability avoid implying acceptance or implementation readiness? |
| Operational handoff | `planning/HANDOFF.md` | Preserve drafting authority, aggregate blocker boundary, proposed correction, and non-authorizations | Handoff only | Could a later session resume without selecting, omitting, renaming, or copying a colliding row? |

No accepted original or K0-SC1-A plan/packet/record, K0-A/K0-I/K0-S/K0-SC
record, KVM0 destination tool, runtime, model, proof, dependency, policy,
instruction, generated page, or publication-gate byte changes in the target.

The authoritative controls reviewed for this packet are
`planning/k3-kvm0-k0sc1-plan.md`,
`planning/k3-kvm0-k0s-completion-plan.md`, `planning/k3-kvm0-plan.md`,
`planning/HANDOFF.md`, `planning/roadmap.md`, and
`LLM_POLICY_ALIGNMENT.md`.

## 3. Claim boundary

### Supported by the exact target

The target supports saying:

- a uniform custody pathname is proposed for every eligible regular host
  manifest row:
  `ordinary/host/by-row/<row-4d>.bin`;
- `<row-4d>` is the exact 1-based manifest data-row number from `0001` through
  `2030`, not eligible-row order;
- each eligible row maps to one distinct file; noneligible rows remain
  metadata-only with no custody path;
- equal content remains represented by separate rows and files; there is no
  content-addressed storage, aliasing, omission, winner selection, or
  deduplication;
- original member/origin/type/mode/size/hash and disposition metadata remains
  in the custody inventory;
- original-host Unicode-casefold equivalence alone is proposed as diagnostic
  after the mapping, while raw/NFC/path/object/mode/origin checks remain;
- every final ordinary file and directory path must remain unique under raw,
  NFC, NFC-casefold, and NFKC-casefold forms, or A2 stops implementation;
- the host path is fixed lowercase ASCII, 29 bytes, depth 4, and adds at most
  two net ordinary directories; and
- six classes, eight controls, existing formulas/caps, restricted separation,
  ref binding, and all 16 stops otherwise remain unchanged.

### Trusted or assumed inputs

The target records four casefold-equivalence groups covering eight rows only
as unrederived, session-private draft-time input. It does not retain member
names or claim those observations as accepted custody evidence.

The 2,030-row manifest order, input identities, eligible-row predicate, and
all draft aggregate counts remain future implementation-time rederivation
obligations. This packet did not access private inputs.

The branch's ahead state is a last-fetched local-ref observation; no remote
server was queried.

### Unavailable or `NOT RUN`

- no eligible-row set or final custody tree exists;
- no row mapping, inventory, copy, selection, checksum, or custody root has
  been implemented;
- no final raw/NFC/casefold uniqueness run exists;
- no exact Unicode data/tool closure has been selected or run;
- no remote-ref check or board access occurred;
- K0-SC1 implementation remains unauthorized;
- K0-SC2, K0-SC3, package assembly, import, readiness, K0-X, K0-R, and
  hardware remain `NOT RUN` or blocked; and
- no push, tag, publication, or release occurred.

### Explicit non-claims

The target does not:

- resolve A2 or prove the future final tree collision-free;
- select, omit, rename, merge, deduplicate, copy, or prefer any host row;
- establish custody, stable preservation, source relation acceptance, host or
  selftest selection, package acceptance, or readiness;
- close the independent restricted-search quality finding or K0SC-R1/R2/R3;
- authorize network, board, QEMU, guest execution, real KVM selftests, import,
  readiness, or successors;
- establish KVM0 execution, K3 qualification, Beryllium hardware validation,
  retained-R8 evidence, Linux/BSP selection, B0/B1, services, devices, DMA,
  multicore, policy, attestation, or an MVP; or
- authorize push, tag, publication, release, migration, paper submission,
  collaboration outreach, venue selection, or upstream submission.

## 4. Security and correctness invariants

| Invariant | Target location | Proposed control | Evidence or review boundary |
| --- | --- | --- | --- |
| Manifest rows remain one-to-one | `Plan revision K0-SC1-B`; `Ordinary input paths` | Exact data-row number determines one path; equal bytes remain separate | Textual invariant; no custody tree exists |
| Noneligible rows cannot disappear | `Ordinary input paths`; `Origin and duplicate handling` | Every row remains an inventory record; noneligible rows have `custody_path=null` | Null schema needs clarification; see K0SC1B-F2 |
| Original path safety remains fail-closed | `Ordinary input paths`; `Stop conditions` | Raw/NFC/noncasefold/escape/object/mode/origin checks remain A2 | Casefold-only exception is bounded to valid host originals |
| Final tree must be collision-free | `Mandatory final-tree uniqueness` | Four-form check spans all final ordinary files and directories | Set formulation has an exact-collision defect; see K0SC1B-F1 |
| Mapping is not a general store | Revision status; namespace and duplicate rules | Row ordinal, no digest, no alias/dedup, package-specific roots | Planning invariant; no copy exists |
| Classes, controls, caps, and stops remain bounded | Revision and validation sections | Six classes, eight controls, accepted numeric caps, 16 stops | Exact-target source audit passed |
| Unicode behavior must be pinned | Authorization field and validation | Exact UCD version and implementation tool lock | Dependency semantics need clarification; see K0SC1B-F3 |
| Board availability grants no board authority | Status and current pages | Human report remains non-evidentiary; K0-SC3/hardware `NOT RUN` | No board contact occurred |

## 5. Review history and resolved/open findings

### Preserved predecessor findings

K0-SC1-A textually addressed K0SC1-F1/F2/F3 and is accepted as planning
corrections only. K0SC-R1/R2/R3 remain unresolved and unwaived. K0-SC1-B does
not reopen those bounded corrections and does not claim to close residuals.

### Open K0-SC1-B findings

| ID | Significance | Confidence | Target location | Finding and human question |
| --- | --- | ---: | --- | --- |
| K0SC1B-F1 | **High; revision recommended** | 9/10 | `Mandatory final-tree uniqueness` | `F union D` uses set semantics before comparing distinct paths. An exact duplicate file path or exact file/directory collision can collapse to one set value and evade the stated raw uniqueness check. Should files and directories be represented as tagged occurrences, with separate file injectivity and file/directory disjointness checks? |
| K0SC1B-F2 | **Medium; revision recommended** | 8/10 | `Ordinary input paths`; `Origin and duplicate handling` | Noneligible rows require `custody_path=null`, but every inventory row still unconditionally requires custody type, mode, size, and SHA-256. What exact null/absent schema and copy-count behavior applies to metadata-only rows? |
| K0SC1B-F3 | **Medium; revision recommended** | 8/10 | `Mandatory final-tree uniqueness`; authorization field | Exact UCD version/tool locking is directionally correct, but malformed UTF-8 rejection, full/default/non-Turkic casefold semantics, and dynamically loaded Unicode data closure are not explicit. What executable Unicode profile must be pinned? |
| K0SC1B-F4 | **Medium; traceability revision recommended** | 8/10 | Revision status/current pages | `restricted-search-quality` is retained as open but has no stable ID, authoritative definition, evidence boundary, or human decision question in tracked planning text. Should the revision define that finding before acceptance? |

These findings were not corrected in the packet because doing so would change
the immutable target. If revisions are required, create a new plan target and
packet.

## 6. Validation and retained evidence

### Pre-commit equivalent-content validation

Before commit, equivalent five-path revision content passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

The source check reported:

```text
site_markdown=97
policy_markdown=5
rendered_references=922
configured_routes=221
tracked_html=0
network_events=0
generated_tree_changes=0
adversarial_cases=34
```

Additional checks covered the mapping grammar, row range, path bounds,
metadata mapping, A2 boundary, four-form final-tree requirement, exact
five-path scope, privacy, and unchanged accepted history.

### Exact-clean-target validation

On October 5, 2026, with exact target
`1ce71e73078a65a271949d84db47343e4eaacf14` as clean `HEAD`, these checks
passed:

```text
git diff --check \
  06cda3814426de940afadb05cd5cf59ee8253688 \
  1ce71e73078a65a271949d84db47343e4eaacf14
umask 0022 && npm run docs:source-check
```

The exact-target source check reported the same `97/5/922/221` source counts,
zero tracked HTML, zero network events, zero generated-tree changes, and 34
adversarial cases. The worktree remained clean.

Exact-target audit also confirmed:

- five modified mode-`100644` planning paths;
- target tree `de7b9023153023cb12d32367eb48a832030981a7`;
- unchanged accepted predecessor targets/packets/records, K0-A/K0-I/K0-S/K0-SC
  records, KVM0 tooling, runtime/model/pathfinder, dependencies, policies,
  instructions, and publication gate; and
- last-fetched local branch state: 18 ahead, zero behind, untagged.

### Packet-follow-up validation

On October 5, 2026, this packet and its four minimal status links passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

The packet source check reported:

```text
site_markdown=98
policy_markdown=5
rendered_references=927
configured_routes=221
tracked_html=0
network_events=0
generated_tree_changes=0
adversarial_cases=34
```

Fail-closed follow-up checks also confirmed the exact five-path
mode-`100644` boundary, unchanged target-plan and accepted-history blobs, six
resolving added relative links, no private locator or credential in added
lines, and no generated-tree change. Because the new packet was initially
untracked, a separate no-index whitespace check covered it in addition to
`git diff --check`.

Packet validation covers decision support and status integration only. It
cannot accept the revision or authorize implementation.

## 7. Recommended human review sequence

1. Confirm target, parent, tree, five-path inventory, accepted predecessor,
   and proposed/not-reviewed status.
2. Review row numbering, eligible/noneligible mapping, original metadata, and
   no-selection/no-dedup invariants.
3. Review original-path A2 checks and the casefold-only diagnostic exception.
4. Review final-tree uniqueness and decide K0SC1B-F1.
5. Review metadata-only null semantics and decide K0SC1B-F2.
6. Review the Unicode execution profile and decide K0SC1B-F3.
7. Review traceability of the restricted-search quality finding and decide
   K0SC1B-F4.
8. Confirm unchanged classes, controls, formulas, caps, stops, source relation,
   board non-evidence, residual findings, and every non-authorization.
9. Review exact-clean-target validation and maintained status links.

Useful read-only commands:

```sh
git --no-pager show --stat --summary \
  1ce71e73078a65a271949d84db47343e4eaacf14
git --no-pager diff --find-renames \
  06cda3814426de940afadb05cd5cf59ee8253688 \
  1ce71e73078a65a271949d84db47343e4eaacf14 -- \
  planning/k3-kvm0-k0sc1-plan.md \
  planning/roadmap.md planning/project-orientation.md \
  planning/README.md planning/HANDOFF.md
git --no-pager show \
  1ce71e73078a65a271949d84db47343e4eaacf14:planning/k3-kvm0-k0sc1-plan.md
```

If rerunning executable checks against the exact target, first use an isolated
detached worktree so unrelated local changes cannot affect the result:

```sh
review_root="$(mktemp -d)"
review_dir="$review_root/worktree"
git worktree add --detach "$review_dir" \
  1ce71e73078a65a271949d84db47343e4eaacf14
(
  cd "$review_dir"
  git diff --check \
    06cda3814426de940afadb05cd5cf59ee8253688 \
    1ce71e73078a65a271949d84db47343e4eaacf14
  umask 0022
  npm run docs:source-check
)
git worktree remove "$review_dir"
rmdir "$review_root"
```

## 8. Human decision checklist

- [ ] The revision scope matches the accepted K0-SC1/K0-SC1-A planning boundary.
- [ ] Proposed claims match exact-target evidence and explicit non-claims.
- [ ] Trusted inputs and unavailable evidence are acceptable for a planning decision.
- [ ] The accepted predecessor target and records remain immutable history.
- [ ] The by-row mapping applies uniformly to every eligible regular host row.
- [ ] Row identity cannot enable selection, omission, aliasing, or deduplication.
- [ ] Every noneligible row remains represented with unambiguous null custody semantics.
- [ ] Original raw/NFC/path/object/mode/origin checks remain fail-closed.
- [ ] Final ordinary file and directory uniqueness detects exact and normalized collisions.
- [ ] Unicode version, data closure, casefold profile, locale, and invalid-input behavior are sufficiently pinned.
- [ ] Six classes, eight controls, formulas/caps, restricted separation, ref binding, and 16 stops remain unchanged.
- [ ] Important negative paths remain bound to fail-closed stop conditions.
- [ ] The restricted-search quality finding is adequately defined and reviewable.
- [ ] K0SC-R1/R2/R3 remain unresolved and unwaived.
- [ ] Board availability remains non-evidentiary; K0-SC3/hardware remain unauthorized and `NOT RUN`.
- [ ] Successor work remains excluded.
- [ ] No custody, selection, implementation, network, board, readiness, successor, push, publication, or release authority follows.
- [ ] Exact target `1ce71e73078a65a271949d84db47343e4eaacf14` is accepted, revisions are requested, or review is deferred.

## 9. After the decision

### If accepted

Record acceptance of exact target
`1ce71e73078a65a271949d84db47343e4eaacf14` in a separate follow-up.
Acceptance approves the bounded path-planning correction only. It does not
resolve A2 through implementation evidence, authorize custody, selection,
remote or board access, K0-SC2/K0-SC3, import, readiness, K0-X/K0-R, push,
publication, or release. A template-conforming exact instruction and
implementation-time final-tree validation would still be required.

### If revisions are requested

This outcome was selected on October 5, 2026. A future separately authorized
task may create a new exact revision target and packet. This decision does
not grant, extend, or reinterpret drafting or implementation authority.
Preserve this target and packet as unaccepted decision support.

### If deferred

Preserve the target and packet as decision support. Do not start K0-SC1 or
dependent work.

**Status:** exact target
`1ce71e73078a65a271949d84db47343e4eaacf14` has a recorded
responsible-human request for revisions to K0SC1B-F1 through K0SC1B-F4. It
remains unaccepted; all four findings remain open and unwaived.

**Next:** the responsible human may separately authorize or decline drafting
a superseding exact revision target. No correction task is authorized by this
decision.

**Action required from you:** if correction drafting is desired, issue a
separate exact instruction naming its base and bounded scope. Otherwise no
action follows; the target remains revisions-requested and unaccepted.
