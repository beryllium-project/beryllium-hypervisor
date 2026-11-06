<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Security model v1 Revision 2 (the console path): review packet

This packet supports the responsible human's decision on exact commit
`afd395b8a80b6baa1f5f0946cd0bff91ad806cc9` (parent `641389eb`, on branch
`beryllium/mvp-m7`), which appends
[Revision 2: the console path](security-model-v1.md#revision-2-2026-11-01-the-console-path)
to `planning/security-model-v1.md`. It is work package M7-5's first
deliverable under the accepted [M7 plan](mvp-m7-plan.md) (design D-7),
presented as its own exact commit as the plan requires, admitted by name
in the MVP plan's stop condition 1 as Plan revision S3-C amended it. The
packet recorded the decision below after it was given.

## Decision record

The responsible human accepted exact commit
`afd395b8a80b6baa1f5f0946cd0bff91ad806cc9` (parent `641389eb`) as
Revision 2 of security model v1 on 2026-11-01 (14:57 in the human's time
zone) by the instruction `accept afd395b8`, the reply to this packet's
request; the abbreviation was checked to resolve uniquely. Acceptance
covers exactly the appended text at that commit and this packet's claim
boundary (section 3); sections 1 to 6 are the packet as presented, apart
from the status rows of section 1 and the closing lines of section 6,
which now show the outcome. It authorizes no code, no model change, and
no claim change of its own; M7-5's claim and ledger rows may now cite I17
and I18, and the M7 result's acceptance is where the claim sentences take
effect. If M7-3's implementation departs from D-1 or D-3 in a way that
changes I17's wording, a second candidate of this revision is presented
before the result, as section 3 says.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `afd395b8a80b6baa1f5f0946cd0bff91ad806cc9` (parent `641389eb`); one file, `planning/security-model-v1.md`, 199 lines appended, 0 removed (`git diff --stat`); the accepted Parts 1 to 7 and Revision 1 byte-identical |
| Current status | Documentation only; **responsible-human accepted as of 2026-11-01** (the decision record above); local, unpushed, on the M7 implementation branch |
| Decision requested | None outstanding; the decision was `accept afd395b8` |
| Successor status | M7-2 and M7-3 are in progress under the accepted plan and do not depend on this decision; M7-5's claim and ledger rows cite I17 and I18 and wait for it; `InputRing.v` (D-8) waits for M7-3's ring |
| Publication status | Private repository; nothing pushed; the development branch at `f5dc770b` |

The action this section asked of the human, the decision on
`afd395b8`, is taken; what follows it is in the decision record above.

## 2. What the revision adds (and only adds)

| Section | Addition | Why |
| --- | --- | --- |
| R2.1 | No object class; the console grant and the focus are configuration, not authority, as Revision 1 treated hart identifiers; the input ring is monitor-owned `memory` under the hart region | S3-C's Q43 at its default: console input is mechanism outside the policy |
| R2.2 | I17 (routing: every delivered byte to the announced focus holding the grant; drops counted, never a failure; the copy only inside the domain's own window, checked first) and I18 (the two output invariants: printable-only; every printed line begins with a tag or prefix) | the two properties the console path must keep; I18 names why the operator's terminal is now a target |
| R2.3 | The threat model: attackers' console attempts; a new "trusted inputs" list (the operator and the typing tool; the operator's relay outside the policy); a shell as an attacker's demonstration; the focus and grants as assets; three availability or latency effects allowed; three containment clauses; loss and cadence deferred | S3-C.3's "the operator and the typing tool are trusted inputs" and the M7 plan's claim words |
| R2.4 | Three TCB rows: the control hart's input path, the domain hart's served read, the firmware console's read path (availability only: the firmware never sees the focus) | the new privileged effect (the firmware read) and the new dependency |
| R2.5, R2.6 | Scope (claimed only as the M7 result's evidence supports; not proved); no change to Parts 2 to 7; when a console class would reopen (a domain holding or passing focus, a run-time grant change, two consoles at once) | the revision's bound |

## 3. Claim boundary

The commit supports saying that security model v1 now states, for the
MVP's console path as the M7 plan designs it, which properties hold
(I17, I18), who is trusted (the operator, the typing tool), what a domain
may attempt and what bounds it, and what the TCB gains. It implements,
proves, and tests nothing; the evidence it names is M7-3's host tests,
M7-4's QEMU sessions and checker, M7-6's board characterization, and
M7-5's `InputRing.v`, none of which exists yet. It changes no claim text
(the M7 plan's sentences take effect through the result). The code the
revision describes is being written in parallel; if M7-3's
implementation departs from D-1 or D-3 in a way that changes I17's
wording, the revision gets a second candidate before the result, not a
silent edit.

## 4. Review sequence

```sh
git show afd395b8 --stat
git show afd395b8 | sed -n '/^+## Revision 2/,$p' | less
```

1. R2.2's two rows (the invariants are what the checker will test).
2. R2.3's "Trusted inputs" and "Allowed effects" (the boundary you will
   publish through the claim's required limit).
3. R2.4's third row (the firmware dependency's status).

## 5. Human decision checklist

- [ ] The revision is additive: the accepted text is byte-identical
      (0 lines removed).
- [ ] I17 and I18 say what you want the console path to guarantee.
- [ ] The operator and the typing tool as trusted inputs, and the relay
      outside the policy, is the boundary you want.
- [ ] No object class is the right reading of Q43's default.
- [ ] Exact commit `afd395b8` is accepted, revisions are requested, or
      the review is deferred.

## 6. After the decision

- **Accept:** the decision-record bullet and the revision's status line
  are set, as Revision 1's were; M7-5's claim and ledger rows cite I17
  and I18.
- **Request revisions:** a second candidate on the same branch; this
  packet updated.
- **Defer:** M7-2 to M7-4 continue; the claim and ledger rows wait.

**Status:** Revision 2 is **responsible-human accepted as of
2026-11-01** at exact commit `afd395b8` (`accept afd395b8`); the
document's decision record and the revision's status line and addendum
carry it.
**Next:** M7-5's claim and ledger rows cite I17 and I18; M7-2 and M7-3
continue.
**Action required from you:** none on this commit.
