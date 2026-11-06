<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Beryllium K3 project-status roadmap review and acceptance record

This is a post-decision bookkeeping record for the responsible human's
acceptance of one immutable documentation target. No separate pre-decision
review packet was created. This record does not widen any authority or alter
the accepted target.

## Decision summary

| Field | Recorded value |
| --- | --- |
| Review target | `a9bb91df94f7e1df2b0e7f2d3ca057f6516ea511` |
| Parent | `a8e137ebbbeeff2a5475050b047a8ec6109d22e0` |
| Tree | `e7375b0ac8656094be8892076037b65469ad239a` |
| Target status | Responsible-human accepted documentation status target |
| Decision evidence | Exact instruction `accept a9bb91` at `2026-10-04T11:12:12.886+02:00`; checked unique resolution to the full target above |
| Repository state at decision recording | Private active branch `beryllium/single-hart-runtime-r0`; target was clean, untagged, unpushed, and seven commits ahead of the last-fetched private origin |
| Successor status | No K0-S readiness decision, K0-X/K0-R, B0/B1, R8 successor, release-definition, paper, or collaboration work is started or authorized by this acceptance |
| Publication status | Push, tag, public migration, publication, release, paper submission, and upstream submission remain blocked |

The responsible-human decision accepts exactly the target commit and its
bounded documentation claims. This follow-up record and its navigation/status
links are later bookkeeping, not part of the accepted target.

## Deliverables

| Paths in the accepted target | Purpose | Boundary |
| --- | --- | --- |
| `planning/roadmap.md` | Maintain the current work-item table, K0-S authorization boundary, and future gated He-to-Be/research-release item | Status and sequencing only; no implementation, execution, release, or publication authority |
| `planning/project-orientation.md` | Give a returning human the matching current-position explanation | Re-entry guidance only; linked exact records remain authoritative |
| `planning/README.md` | Keep the planning entry point consistent with the roadmap | Navigation-level status only |
| `planning/HANDOFF.md` | Preserve the October 4 K0-S and PMR-077 current outcomes | Operational handoff only; no source, board, import, execution, or publication action |

## Claim boundary

The accepted target supports saying that, as of October 4, 2026:

- the roadmap's work-item table and directly related summaries accurately
  record the maintained project status and gates;
- bounded K0-S readiness-completion is authorized exactly as documented while
  K0-S remains not ready;
- PMR-077's COM260/KVM/Fedora report is non-evidentiary planning input;
- the post-hardware Helium-to-Beryllium synthesis, initial limited security
  research platform, paper, collaboration, and conference/venue work remain
  future gated items; and
- publication and release remain blocked.

Acceptance explicitly does **not**:

- accept K0-S readiness or the recorded K0-S source relation;
- change the K0-S authorization scope, exclusions, or authorized base;
- convert PMR-077 into retained evidence or a K3 hardware result;
- authorize board access, live capture, destination import/install, K0-X,
  K0-R, B0, BSP selection, B1, or an R8 successor;
- approve or finalize a Helium-to-Beryllium synthesis, Beryllium architecture,
  MVP, or initial release definition;
- authorize paper drafting or submission, collaboration outreach or
  commitment, or conference/venue selection;
- authorize push, tag, public migration, publication, release, or upstream
  submission; or
- approve this later acceptance-record commit or its bookkeeping edits.

## Validation and retained evidence

Before the target commit, the equivalent four-file content passed:

```text
git diff --check
umask 0022 && npm run docs:source-check
```

The source check reported zero network events and zero generated-tree changes.
After the decision, while the exact target was still the clean branch tip,
the following target-bound checks also passed:

```text
git diff --check a8e137ebbbeeff2a5475050b047a8ec6109d22e0 \
  a9bb91df94f7e1df2b0e7f2d3ca057f6516ea511
umask 0022 && npm run docs:source-check
```

The exact clean-target source check covered 91 site Markdown files, five
policy Markdown files, 891 rendered references, 221 configured routes, and 34
adversarial cases, with zero tracked HTML, network events, or generated-tree
changes. Hardware, KVM0 execution, and publication checks were not run and
are not claims of this target.

## Recorded decision

At `2026-10-04T11:12:12.886+02:00`, the responsible human supplied:

```text
accept a9bb91
```

The abbreviation was checked to resolve uniquely to
`a9bb91df94f7e1df2b0e7f2d3ca057f6516ea511`. The exact documentation target
is therefore recorded as responsible-human accepted.

**Status:** exact documentation target
`a9bb91df94f7e1df2b0e7f2d3ca057f6516ea511` is accepted; this later record
is unaccepted bookkeeping.

**Next:** resume only work that already has separate authority. The immediate
critical path remains bounded K0-S offline payload/archive completion; K0-S
readiness still requires a later explicit decision.

**Action required from you:** none for this recorded acceptance. Any K0-S
readiness decision, hardware execution, successor, push, publication, release,
paper, collaboration, or venue action requires its own exact authority.
