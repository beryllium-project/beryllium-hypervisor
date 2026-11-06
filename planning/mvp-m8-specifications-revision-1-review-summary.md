<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M8 specifications Revision 1: review packet

This packet supports the responsible human's decision on exact commit
`93a8d136d38547a8c581197315f7607b5eef7bad` (parent `14851913`, the M8-4 merge,
on branch `beryllium/mvp-m8`), which revises
[`planning/mvp-m8-specifications.md`](mvp-m8-specifications.md), the
specification the human accepted as reviewer of record at `004f31ae` on
2026-11-02. Under the accepted [M8 plan](mvp-m8-plan.md)'s D-6 a change
to the specification "re-freezes the hash and re-runs every proof that
cites it"; the human directed this revision on 2026-11-03 at the plan's
stop 2 (form answer `spec_mismatches=revision_1_rerun`). The packet
recorded the decision below after it was given.

## Decision record

The responsible human accepted exact commit
`93a8d136d38547a8c581197315f7607b5eef7bad` (parent `14851913`) as
Revision 1 of the M8 specifications on 2026-11-03 (09:43 in the human's
time zone) by the instruction `accept 93a8d136`, the reply to this
packet's request; the abbreviation was checked to resolve uniquely.
Acceptance covers exactly the document's text at that commit and this
packet's claim boundary (section 3): the specification's hash is
re-frozen at `aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b`,
every arm's annotation cites it in the re-run, and the three arms are
re-run against it under the plan's D-7, as the human decided at stop 2.
Each of the nine rows stands as a specification erratum; none was
rejected as a code defect, so no leaf changes. Sections 1 to 6 are the
packet as presented, apart from the status rows of section 1 and the
closing lines of section 6, which now show the outcome.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `93a8d136d38547a8c581197315f7607b5eef7bad` (parent `14851913`, the M8-4 merge, on `beryllium/mvp-m8`); one file, `planning/mvp-m8-specifications.md`: 105 lines added, 22 removed against the accepted text; the document's new SHA-256 `aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b` |
| Current status | Documentation only; **responsible-human accepted as of 2026-11-03** (the decision record above); local, unpushed, on the M8 implementation branch |
| Decision requested | None outstanding; the decision was `accept 93a8d136` |
| Successor status | The arms' records against the accepted text are merged and retained (`bc98a875`, `0b45698e`; `mvp/results/20261103-verify/`); the re-run (M8-6 continued) waits for this decision; M8-7's outcome and packet follow the re-run; stage 1 (merged, 26 theorems) is unaffected |
| Publication status | Private repository (the internal one); nothing pushed; the development branch at `55047781` |

The action this section asked of the human, the decision on
`93a8d136`, is taken; what follows it is in the decision record above.

## 2. What the revision changes (and only changes)

Nine clauses, each marked `[R1-n]` in place and tabled with its accepted
wording, corrected wording, evidence, and reading in the document's new
section "Revision 1":

| # | Clause | Correction | Why it is an erratum and not a code defect |
| --- | --- | --- | --- |
| R1-1 | 4.2 E7 | the GPA must be outside the window first, for every cause; then unmapped or read-only | the accepted M1 plan's entry says "a fault inside the window … stay[s] terminal" and its read-only case is "cause 23 at a GPA in the channel page"; the accepted text dropped the qualifier; `deny-test.c` pins the leaf |
| R1-2 | 4.3 | `map.size > 0` is a precondition | the leaf refuses every exit under a zero-size map; `deny-test.c` asserts it; an unwalked map is outside the contract's domain |
| R1-3 | 4.5 | the helpers' contracts strengthened to what a modular proof needs (`access_fault` returns `0` outside the three causes; the Boolean helpers return exactly `0`/`1`; `leaf_at`'s lowest-index rule) | the WP arm proved these as additions; without them no modular proof of the leaf closes; no behaviour changes |
| R1-4 | 5 `init` | `domain ∈ {0, 1}`; non-null index lines; `peak = head − tail` | the header says "@domain: 0 or 1"; `ring-test.c` refuses 2 |
| R1-5 | 5 `init` | `limit = cursor`, the view's own index | the accepted text said "the peer's"; the code and `ring-test.c` say the own index |
| R1-6 | 5 `post`, `post_words`, `room` | the tail bounded by the **published head** (`limit − t ≤ C`), not the cursor | the code's comment: "at or behind the head the writer published" |
| R1-7 | 5 `acquire` | the head bounded by the **released tail** | the code's comment: "at most a capacity past the tail it released" |
| R1-8 | 5 `taken` | a **writer** view's reading of the reader's tail | the header's one-line description says exactly this; the accepted text swapped the roles |
| R1-9 | 5 sequence; the common safety paragraph | the **free bytes** grow by the released size (`room` is capped at 256 after the header); the index advances wrap by design beside the differences | `room`'s definition; configuration A's eight index-advance sites |

Not changed: sections 1 to 3 (stage 1's P1 to P9, whose modules cite the
accepted hash they proved against), sections 6 and 7, any monitor source,
any arm's annotation (each is re-made against this hash in the re-run).
Two arm findings are recorded as **not** errata (the dead SPP arm at
`mvp-sbi.c` L317 under E3; Leaf B's mutant `m02`, the test stricter than
the contract).

## 3. Claim boundary

The commit supports saying that the M8 specification now states, for the
two leaves, contracts the leaves can meet as the accepted M1 plan and the
ring header fix them; that the nine disagreements the pilot's first run
found were in the specification's drafting from the plans without reading
the C (D-6's deliberate rule) and not in the monitor; and that no monitor
source changes. It does not say any arm has closed: WP, CN, and CBMC's
results against the accepted text are OPEN, OPEN, FAILED, and OPEN, as
recorded, and the re-run against this revision has not happened. It does
not change stage 1, the claim, or the ledger. The reading "erratum, not
defect" is the session's, confirmed against `planning/mvp-m1-plan.md`
L504-L522, `mvp/src/mvp-ring.h`, `mvp/src/mvp-ring.c`,
`mvp/tests/deny-test.c`, and `mvp/tests/ring-test.c`; it is yours to
reject for any row, in which case that row is a code finding under stop
2 and the leaf's fix is routed before M10.

## 4. Review sequence

```sh
git show 93a8d136 --stat
git show 93a8d136 -- planning/mvp-m8-specifications.md | less
sed -n '/^## Revision 1/,$p' planning/mvp-m8-specifications.md
```

1. The document's "Revision 1" section: the nine-row table, each row's
   evidence column against the source it names.
2. Section 4.2's E7 row and the sentence after the table (R1-1), against
   `planning/mvp-m1-plan.md` L514-L518.
3. Section 5's `init`, `post`, `acquire`, and `taken` rows (R1-4 to R1-8),
   against `mvp/src/mvp-ring.h`'s contract comments.

## 5. Human decision checklist

- [ ] Each of the nine rows is an erratum of the specification, not a
      defect of the leaf (reject any row you read otherwise).
- [ ] Sections 1 to 3, 6, and 7 are unchanged; no monitor source changes.
- [ ] The two non-errata findings (the dead SPP arm; mutant `m02`) are
      recorded and not acted on, as you want.
- [ ] Exact commit `93a8d136` is accepted (re-freezing the hash at
      `aeb75682…` and directing the arms' re-run), revisions are
      requested, or the review is deferred.

## 6. After the decision

- **Accept:** the plan's status block records `m8_specifications_revision_1=accepted`
  with the hash; the three arms are re-run against it in the verifier
  (WP about four hours, CBMC on the ring about two, CN minutes), each
  arm's annotation re-made to cite the new hash, under the same decision
  rule; M8-7 follows with the outcome.
- **Request revisions:** a second candidate on the same branch; this
  packet updated.
- **Defer:** the arms' first-run records stand; M8-7 cannot state an
  outcome against a specification the leaves cannot meet, so M8 waits.

**Status:** Revision 1 is **responsible-human accepted as of
2026-11-03** at exact commit `93a8d136` (`accept 93a8d136`); the
document's head and Revision 1 section and the M8 plan's status block
carry it; the arms' first run is merged and recorded.
**Next:** the three arms re-run against the re-frozen hash in the
verifier (WP, CN, CBMC on both leaves), then M8-7.
**Action required from you:** none on this commit.
