<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Security model v1 Revision 3 (the measurement log): review packet

This packet supports the responsible human's decision on exact commit
`4bc079dbb96540cb44008a53df857701696e9bad` (parent `bc80b620`, the M9 plan's
acceptance record, on branch `beryllium/mvp-m9`), which appends
[Revision 3: the measurement log](security-model-v1.md#revision-3-2026-11-03-the-measurement-log)
to `planning/security-model-v1.md`. It is work package M9-2's first
deliverable under the accepted [M9 plan](mvp-m9-plan.md) (exact commit
`4f4a8f76`; design D-8), presented as its own exact commit as the plan
requires, admitted by name in the MVP plan's stop condition 1 as Plan
revision S3-C amended it. The packet recorded the decision below after it
was given.

## Decision record

The responsible human accepted exact commit
`4bc079dbb96540cb44008a53df857701696e9bad` (parent `bc80b620`) as
Revision 3 of security model v1 on 2026-11-03 (00:46 in the human's time
zone) by the instruction `accept 4bc079db`, the reply to this packet's
request; the abbreviation was checked to resolve uniquely. Acceptance
covers exactly the appended text at that commit and this packet's claim
boundary (section 3); sections 1 to 6 are the packet as presented, apart
from the status rows of section 1 and the closing lines of section 6,
which now show the outcome. It authorizes no code, no model change, and
no claim change of its own; M9-5's claim and ledger rows may now cite I19
and I20, and the M9 result's acceptance is where the claim sentences take
effect. If M9-3's or M9-4's implementation departs from the plan's D-1,
D-2, or D-4 in a way that changes I19's or I20's wording, a second
candidate of this revision is presented before the result, as section 3
says.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `4bc079dbb96540cb44008a53df857701696e9bad` (parent `bc80b620`, the M9 plan's acceptance record, on `beryllium/mvp-m9`); one file, `planning/security-model-v1.md`, 252 lines appended, 0 removed (`git diff --stat`); the accepted Parts 1 to 7 and Revisions 1 and 2 byte-identical |
| Current status | Documentation only; **responsible-human accepted as of 2026-11-03** (the decision record above); local, unpushed, on the M9 implementation branch |
| Decision requested | None outstanding; the decision was `accept 4bc079db` |
| Successor status | M9-2's other deliverables (the log profile document, item 104's premise record, the probe template) are being written in a worktree and do not depend on this decision; M9-3 and M9-4 implement against the plan and the profile; M9-5's claim and ledger rows cite I19 and I20 and wait for this decision; the M9 result's acceptance is where the claim sentences take effect |
| Publication status | Private repository (the internal one); nothing pushed; the development branch at `55047781` |

The action this section asked of the human, the decision on
`4bc079db`, is taken; what follows it is in the decision record above.

## 2. What the revision adds (and only adds)

| Section | Addition | Why |
| --- | --- | --- |
| R3.1 | No object class; Part 1's existing `measurement` row ("named as an unimplemented asset") is instantiated as the log page and the registers: hart 0's monitor-owned `memory`, mapped by no domain root (I2), one writer (I15, I16); its authority recorded in the reference manifest and the baked expected values; what the asset is not: not a secret (the test secrets are public; no generalization to a future low-entropy secret or confidential policy), not evidence against an adversary who alters the monitor (the self-report gates nothing; no key, nonce, freshness, or root of trust) | the M9 plan's D-1 and D-9; the steering review's finding that the existing asset should be instantiated, not a new class invented |
| R3.2 | I19 (hart 0 alone writes the log and the registers, only before any domain hart starts, closing with the expected count; overflow or a page that cannot close fails the run; no domain hart reads it) and I20 (no domain hart starts unless every required launch comparison has **succeeded** and the log is closed; each domain's records and gate precede its `HART_STARTED`); what the registers bind, exactly: each stream's ordered digest values and nothing else; the field comparison with the reference binds the rest; the close is structural, not cryptographic | the two properties the log must keep; the plan's global rule; the review's register-properties finding, stated so no later milestone assumes the registers authenticate the log |
| R3.3 | The threat model: forged `:19`/`:20` lines (bounded by I18) and post-measurement alteration (not seen by the log) as attempts; the reference manifest, the generator, the loader observation, and the platform observation as trusted inputs that are **never one chain**; the assets; the hashing and rendering time as measured availability effects; four containment clauses; the deferred firmware measurement, root of trust, and boot-ROM question | S3-C.5's three evidence classes kept separate; D20's "measure first, then attest"; Q14's disposition |
| R3.4 | The TCB's measurement row filled by six rows (hart 0's measurement path; the baked expected values; the reference manifest and the generator; the checker's log module; the loader observation; the platform observation) and a distinction the accepted table did not need: the **running TCB** against the **offline evidence TCB** (a defect in the generator, the reference, or the checker weakens the evidence, never the containment) | the review's recommendation; the honest place of the offline tools |
| R3.5, R3.6 | Scope (claimed only as the M9 result's evidence supports; not proved; not a theorem of M8's stage 1, whose gate predicate is re-read against M9's global rule at integration under the re-proof rule; no trigger evaluated; the log is no channel, notification, or manifest; nothing about bytes after the point of measurement, the firmware, the loader, or the boot ROM); no change to Parts 2 to 7 or to any code, model, claim, or plan | the revision's bound |

## 3. Claim boundary

The commit supports saying that security model v1 now states, for the
MVP's measurement log as the M9 plan designs it, which properties hold
(I19, I20), what the registers do and do not bind, which inputs are
trusted and that they are three separate kinds of evidence, what a
domain may attempt and what bounds it, and what the TCB gains, with the
running TCB and the offline evidence TCB told apart. It implements,
proves, and tests nothing; the evidence it names is M9-3's host tests
and image checks, M9-4's checker and its negatives, the QEMU runs, and,
when a session is scheduled, one correlation boot, none of which exists
yet. It changes no claim text (the M9 plan's D-9 sentences take effect
through the result). The code the revision describes will be written
against the plan and the log profile document; if M9-3's or M9-4's
implementation departs from D-1, D-2, or D-4 in a way that changes I19's
or I20's wording, the revision gets a second candidate before the
result, not a silent edit. Nothing here is a theorem of M8's stage 1, and
nothing here says the registers authenticate anything.

## 4. Review sequence

```sh
git show 4bc079db --stat
git show 4bc079db | sed -n '/^+## Revision 3/,$p' | less
```

1. R3.2's two rows (the invariants the checker will test) and the
   paragraph after them on what the registers bind.
2. R3.3's "Trusted inputs" (the three evidence classes, never one chain)
   and "Deferred" (the boundary you will publish through the claim's
   required limit).
3. R3.4's distinction between the running TCB and the offline evidence
   TCB, and its last two rows (the loader and platform observations).

## 5. Human decision checklist

- [ ] The revision is additive: the accepted text is byte-identical
      (0 lines removed).
- [ ] I19 and I20 say what you want the log and the launch gate to
      guarantee, and the registers' binding is stated as narrowly as you
      want it published.
- [ ] The three evidence classes as separate trusted inputs, never one
      chain, is the boundary you want.
- [ ] Instantiating the existing `measurement` asset (no new class) is
      the right reading.
- [ ] Exact commit `4bc079db` is accepted, revisions are requested, or
      the review is deferred.

## 6. After the decision

- **Accept:** the decision-record bullet and the revision's status line
  are set, as Revisions 1 and 2's were; M9-5's claim and ledger rows cite
  I19 and I20.
- **Request revisions:** a second candidate on the same branch; this
  packet updated.
- **Defer:** M9-2's other deliverables and M9-3 and M9-4 continue against
  the plan; the claim and ledger rows wait.

**Status:** Revision 3 is **responsible-human accepted as of
2026-11-03** at exact commit `4bc079db` (`accept 4bc079db`); the
document's decision record and the revision's status line and addendum
carry it.
**Next:** M9-5's claim and ledger rows cite I19 and I20; M9-2's other
documents, M9-3, and M9-4 continue.
**Action required from you:** none on this commit.
