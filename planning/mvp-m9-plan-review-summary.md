<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M9 plan review summary

This packet presents one decision: the [M9 plan](mvp-m9-plan.md),
measurement, **second candidate**, at exact commit
`4f4a8f76` (full SHA below; parent `d470fb7f`, the first candidate's
packet commit, over `86f1c68b`, the first candidate, over `6fbcc3d1`,
the M8 plan's acceptance record, a linear descendant of the development
branch's tip `6105c34d`) on local branch `beryllium/mvp-m9-plan`. The
first candidate `86f1c68b` is **superseded**, not accepted, after the
independent steering review the human directed (section 5). The plan bounds the milestone S3-C.5 defines,
under S3-C's D20, its stop 1 as amended and stops (a), (c), (d), (e), and
Q31, Q38 to Q41 at their defaults. It supports the responsible human's
decision and records none.

## Decision record

The responsible human accepted the second candidate, exact commit
`4f4a8f760a1ed7e5f9886b4e02e94b7a849bfc33`, on 2026-11-03 (00:26 in the
human's time zone) by the instruction `accept 4f4a8f76`; Q1 to Q19 at
their defaults (Q17 answered by the steering review the human directed).
The same message said the board is available. The decision authorizes
M9-2 to M9-6 on `beryllium/mvp-m9` from the acceptance-record commit,
Part 1 Revision 3 as its own exact commit, item 104's premise record, and
the claim's sentences as D-9 fixes them (taking effect through the
result's acceptance); it directs no fast-forward or push. This packet is
the review and acceptance record; the sections below are the packet as
presented, with the status rows and the closing lines showing the
outcome.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `4f4a8f76` (`4f4a8f760a1ed7e5f9886b4e02e94b7a849bfc33`; parent `d470fb7f`) on local branch `beryllium/mvp-m9-plan`; it changes `planning/mvp-m9-plan.md` and nothing else (402 lines added, 156 removed against the first candidate). The commit after it adds the steering review's text, this packet's update, and the registrations. The first candidate `86f1c68b78e2d36920ea53721ce80bbb91a7328b` is superseded. |
| Current status | **Accepted 2026-11-03** (`accept 4f4a8f76`). Documentation only; local, unpushed. No code, model text, claim text, or tool changes. |
| Decision requested | Accept exact commit `4f4a8f76` as the M9 plan (which authorizes M9-2 to M9-6 on `beryllium/mvp-m9` from the acceptance-record commit, with Q1 to Q19 at their defaults unless answered; Q17 is answered), request revisions, or defer. |
| Successor status | M9-2 to M9-6 not started. M8-2 to M8-7 run in their own lane on `beryllium/mvp-m8` (started 2026-11-02); M10's plan waits for M7's, M8's, and M9's results. |
| Publication status | Private repository (the internal one). The development branch is at `6105c34d` locally and on the private `origin`; `beryllium/mvp-m8-plan` (`6fbcc3d1`), `beryllium/mvp-m8`, and this branch are unpushed. The public review snapshot is at `36e2590c`. No tag, publication, release step, or snapshot refresh. |

Please review exact commit `4f4a8f76` and accept it, request revisions,
or defer; answer any of Q1 to Q19, or let the defaults apply. The
steering review's own answers to Q4, Q10, Q13, and Q14 agree with the
defaults (section 5).

### What the plan is, in one paragraph

Hart 0 keeps a bounded, versioned, zero-initialized **log page** (an
explicitly encoded 128-byte header and 96-byte records at fixed
little-endian offsets, capacity 41 with the close included; four
**measurement registers** beside it, extended by measured records only; a
close record before any domain hart starts; overflow failing closed) and
prints it losslessly as `BE_MVP:19 LOG` and `BE_MVP:20 REGISTERS` lines.
Its records are: the monitor's **self-measurement** of its own text and
read-only data (an informational self-report, compared offline, gating
nothing, kept only if the build reproduces the loaded ranges); the
**configuration** (the core identity measured at boot; the console grant
as a measured record, item 108; the configuration and policy identities
build-recorded; `two-guests` recording the absence of a policy); and
**each domain's launch** (the kernel Image and device tree as placed, and
`anchor`'s secret page), extending M2's one measurement of one domain to
both domains and gating each domain's entry on its launch register under
one global rule (every comparison succeeds and the log closes before
`BE_MVP:07`, or no domain hart starts). A **per-image contract** fixes,
for every image class including the probes and the negatives, the
records required, the gate, the completion state, and the permitted
terminal prefix. A **post-link reference manifest** per image, in the
Beryllium log profile (a JSON profile derived from TCG CEL 1.1, mapped
field by field, no interoperability claimed), says what every record must
be; the checker rebuilds the page from the lines, replays the registers
(labelled unprotected), recomputes every digest from the build's inputs,
compares every field with the reference, and exports the profile, with
the negatives S3-C.5 lists, metadata-only mutations the registers cannot
see, a wrong digest at each monitor-controlled record, and a mechanical
`self-report-flip`. The loader's MD5 (an unmeasured U-Boot's) stays
the checker's board-only attribution and never enters the page; the
human's read-only JTAG probe of the board's lifecycle and debug state is
a dated platform assumption with four outcome classes, and the
boot-authentication disposition for 1.0 is a documented assumption. IMA
is never used, made testable in three places. Security model v1 gets an
additive Part 1 Revision 3 as its own exact commit; a crosswalk analyses
the vTPM, SBI-extension, and systemd-adapter routes without implementing
any (Q39). The claim gains the measurement clause S3-C.5 fixes in content
and the plan fixes in words. QEMU evidence is the gate; one correlation
boot folds into the next scheduled board session.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Review question |
| --- | --- | --- | --- | --- |
| The M9 plan, second candidate | `planning/mvp-m9-plan.md` | the milestone's design (D-1 to D-12), the encoding, the per-image contract, the records table, the claim words with their fixed conditional forms, six work packages, a 6,000-line soft limit, twelve stops, Q1 to Q19 | planning text only; authorizes nothing until accepted | Does every design choice trace to S3-C.5's shape, to a steering-review finding recorded in section 5, or to one of the plan's own open questions with a default? |
| The steering review | `planning/mvp-m9-plan-review-gpt-6-astra.md` | the independent review of the first candidate, unedited (its citation-rendering tokens removed), with a provenance note | steering input; records no decision | Is each of its blockers B1 to B5 answered by the second candidate as section 5's table says? |
| This packet | `planning/mvp-m9-plan-review-summary.md` | the decision support | decision support only | — |
| Registrations | `planning/README.md`, `planning/roadmap.md`, `planning/HANDOFF.md`, `planning/.vitepress/config.mts`, `.github/copilot-instructions.md`, `mvp/README.md` | the plan's place in the maintained navigation and status | status text | — |

## 3. Claim boundary

**What the commit supports saying:** a bounded plan exists for M9 whose
every design choice traces to S3-C.5's shape or to one of its own open
questions with a default; its facts were read in the tree at `6fbcc3d1`
with line numbers by a read-only fact sheet re-checked where cited, and
re-checked again by the steering review (fourteen facts spot-checked;
one corrected: the core identity's printed prefix is checked offline).
Three facts the design turns on hold at that commit: today's measurement
is one SHA-256 over four inputs for `anchor`'s domain 1 alone, gated
before the barrier, and the other scenarios measure nothing; the sealed
configuration's core identity is printed by its first sixteen hex digits,
matched offline by the checker against the generator's expected line, and
compared with nothing at runtime; the board's U-Boot offers `crc32` and `md5sum` and no `hash`, `sha1sum`,
`sha256sum`, `tpm`, or `verify` (the retained `help` listings under
`build/`, which the plan commits as item 104's premise record).

**What it does not do:** no code, no model text, no claim change (the
sentences are fixed here and take effect only through the result's
acceptance), no board command, no push. It does not promise that the
self-measurement survives the post-link reproduction rule (R2 is dropped
and recorded if the loaded ranges do not reproduce), nor that the human's
probe reaches a determinate outcome ("not determined" is an honest
outcome with a disposition), nor a board run of its own (the correlation
boot folds into the next scheduled session).

**What stays trusted or assumed in the design:** the build's inputs and
the generator (the expected values come from the same bytes the monitor
measures, computed offline); SHA-256 as `mvp-sha256.c` implements it
(FIPS 180-4 vectors; no key); U-Boot as the loader, identified by its
banner and unmeasured; the firmware's SBI identity from Fedora's log; the
human's probe and its tool; the absence of any root of trust, stated in
the claim's limit. The log is a self-report in the sense S3-C.5 fixes:
code able to alter the monitor can fabricate its records.

## 4. Load-bearing decisions

| Decision | Content | Why this way |
| --- | --- | --- |
| D-1 | a 4 KiB page of hart 0's with an explicit little-endian encoding (128-byte header, 96-byte records, capacity 41), four registers beside it, a close record, the global start rule, overflow failing closed, lossless `:19`/`:20` rendering | S3-C.5's log clause; the page is the log and the lines its checked rendering; the single-writer rule (I15, I16) carries it; the review's B1 |
| D-2 | R1 checker-held and never in the page; R2 informational and offline; R3 the core identity and the console grant measured and the identities bound; R4 per domain, gated per domain; a per-image contract for every image class | S3-C.5's four records; M2's gate generalized to both domains; the configuration identity bound through the reference, not folded into a launch hash; the review's B2; item 108 |
| D-3 | a post-link, per-image reference manifest under `build/` in the Beryllium log profile, deterministic, pinned by the image checker and copied into records; only pre-link values in the image | the pre-link report cannot hold post-link digests; `two-guests` and the probes have no report; no self-reference |
| D-4 | the checker rebuilds, replays, recomputes every digest, compares every field, exports the profile; the negatives in five kinds, a mechanical `self-report-flip` | S3-C.5's exit list; the review's B3 and B5; the registers bind digests only, so the field comparison binds the rest |
| D-5 | IMA never, in three testable places | D20's "made testable" |
| D-6 | the probe on a template with four outcome classes, dated; the boot-authentication disposition a documented assumption; item 104's record committed | Q40's default; the hardware roadmap's open question answered for 1.0 the honest way |
| D-7 | the crosswalk analysed, nothing implemented | Q39's default |
| D-8 | Part 1 Revision 3 as its own exact commit | stop 1 as S3-C amended it |
| D-9 | the clause's words fixed, with three slots each having a fixed pair of forms for the outcomes the plan permits (self-report kept or omitted; probe performed or not; board correlation run or not) | S3-C.7's pre-authorization and S3-C.5's content; the words the matcher cannot catch kept out by fixing them here; the review's B4: every permitted outcome has true words |
| D-10 | QEMU as the gate; the correlation boot folded into the next scheduled session; M8's lane untouched | Q31's default; S3-C.7's merge-order rule |

## 5. Review history and resolved findings

The plan was written on the session model from the accepted S3-C.5 text
and a read-only fact sheet of the tree at `6fbcc3d1` (an explore agent
on `claude-opus-5.5`, 2026-11-02; its facts re-checked where cited).
Three things the writing settled:

1. **The base.** As for M8 (its Q1), the plan is based on the latest
   acceptance record, `6fbcc3d1`, a linear descendant of the development
   tip `6105c34d`, so that the M9 lane starts from the tree M8's lane
   starts from and the two merge in acceptance order (S3-C.7).
2. **M2's single hash cannot carry per-domain registers.** The accepted
   measurement folds the configuration identity into the protected
   domain's digest; S3-C.5 wants the configuration bound through the
   reference and each domain gated on its own launch. The plan therefore
   replaces `:06 MEASURED` with per-object records and a `:06 LAUNCH`
   gate per domain, in every scenario, and keeps `wrong-measurement`'s
   name with the redefined flip (Q16); `anchor`'s accepted declared lines
   change, its counts do not (stop 5).
3. **A tooling honesty item found on the way** (item 116): `k3-run.sh`
   writes `staged_sha256=yes` as a literal in its attribution verdict,
   true only because the script dies earlier on a mismatch; M9-4 makes
   the field computed from the recorded comparison.

**The steering review (Q17 answered).** On the human's instruction
`have gpt-6-astra review the m9 plan as steering input` (2026-11-02, after
the first candidate was presented), a `gpt-6-astra` agent reviewed the
first candidate `86f1c68b` in a detached worktree at the packet commit
`d470fb7f`, reading no other review; its text is kept unedited at
[`mvp-m9-plan-review-gpt-6-astra.md`](mvp-m9-plan-review-gpt-6-astra.md).
It recommended a second candidate, which this is. Its findings and their
dispositions:

| Finding | What it found | Disposition in the second candidate |
| --- | --- | --- |
| B1 (blocker) | the 64-byte header cannot hold two 32-byte identities and the magic; no explicit encoding; `.mvp.bss` is not an output section | D-1: a 128-byte header and 96-byte records at fixed little-endian offsets, capacity 41 with the close included, registers in their own storage, the close's count a field, padding canonical zero; alignment and containment checked; the terminology corrected (confirmed by the session: 8 + 32 + 32 = 72 > 64) |
| B2 (blocker) | no per-image contract: `two-guests` has no policy identity, probes cannot emit Linux launch records, early negatives cannot close a log, the console grant is outside both identities, the temporal rule is loose | D-2's per-image contract table; the `console-grants` measured record (Q18); the global rule "every comparison succeeds and the log closes before `:07`, or no domain hart starts"; I20 restated |
| B3 (blocker) | `self-report-flip`'s oracle moves with the defect; S3-C.5's wrong digest at each record not preserved; post-link values must stay out of the image | D-4: the mechanical recipe on `be_mvp_log_canary` with the nominal reference frozen and the mutated hash recorded; per-record capture mutations with recomputed registers; metadata-only mutations; D-3's pre-link-only rule |
| B4 (blocker) | D-9's words false under permitted outcomes (R2 dropped; no probe; board pending; "in QEMU there is none") | D-9: the main clause scoped to the ledger's runs and measured records; three slots with fixed pairs of forms; direct QEMU and the U-Boot rehearsal distinguished; C-08/C-16's meaning kept |
| B5 (blocker) | "CEL-shaped" is not CEL (per-index `recnum`; `pcr`; `.pcrlock` uses `pcr`/`digests`) | D-4 and Q7: the Beryllium log profile, derived from CEL 1.1 rev. 11, mapped field by field with unmapped fields listed, no interoperability claim; S3-C.5's "CEL-JSON" read as this profile, the reading recorded for acceptance |
| the core-identity fact | "compared with nothing" is wrong unqualified: the printed prefix is matched offline | the fact and the Purpose corrected |
| checker trust | replaying printed digests is not independent hashing; the pinned fallback must not serve M9 | D-4: independent recomputation of every digest; the fallback historical only; a strict schema |
| register properties | the recurrence binds digest values only, not metadata or interleaving | D-1 says so; D-4's field comparison binds the rest; the close is structural |
| timing | hashing a 2 MiB Image and rendering at 115200 baud cost time the plan did not name | the facts carry the RC3 measurement (34.2 ms for 1.9 MB) and the baud cost; D-10 measures and reports both; D-11 and stop 5 judge counts by the checker's existing rule, no new invariant |
| M8 and Revision 3 | the gate predicate gains the close condition; the running and offline TCBs differ; the `measurement` asset exists | D-8 restated; I20 as the global precondition; U-12 stays open |
| Q4, Q10, Q13, Q14 | agrees with the defaults; narrower Q14 wording | Q14's wording adopted; the rest unchanged |
| recommendations | item 116 computed, item 115 kept open, the IMA allowlist, the Q17/Q16 typo, the crosswalk's required content, Amutable's document named | adopted (D-4, D-5, D-7, Q16); items 115 and 116 as the review says |

Open for your judgement, beyond the defaults: Q4 (keep the
self-measurement at all), Q10 (the correlation boot's session), Q13
(Amutable's one document, 2026-09-03), Q14 (the wording adopted), Q18
(the console-grants record), Q19 (`.monitor.input` in R2), and the
reading of S3-C.5's "CEL-JSON" as a derived profile (Q7).

## 6. Validation and retained evidence

Documentation checks only: `node scripts/check-doc-sources.mjs` PASS at
the packet commit (at the plan commit `4f4a8f76` it reports the review
file's link as a missing target, the review text being added in the
packet commit), `git diff --check` clean, `git status` clean; `git diff
--stat d470fb7f 4f4a8f76` lists one file, `planning/mvp-m9-plan.md`.
The session confirmed B1's arithmetic and the core-identity correction
against the sources before writing the second candidate. Nothing was
built or run. The fact sheet is a session artifact, not repository
content; the steering review's text is repository content.

## 7. Recommended human review sequence

```sh
git worktree add --detach /tmp/be-m9-plan 4f4a8f760a1ed7e5f9886b4e02e94b7a849bfc33
cd /tmp/be-m9-plan
git --no-pager diff --stat 6fbcc3d1..HEAD
git --no-pager diff 86f1c68b..HEAD -- planning/mvp-m9-plan.md
```

1. `planning/mvp-m9-plan.md`: "Purpose", then D-9 (the words that will
   be published, with the slot forms), then D-1 and D-2 (the encoding,
   the records table, the per-image contract), then D-4 (the checker and
   the negatives; the profile's reading of "CEL-JSON"), then D-6 (the
   probe and the disposition), then the stops and Q1 to Q19; the second
   `diff` shows exactly what the review changed.
0. Optionally first, section 9 of
   `planning/mvp-m9-plan-review-gpt-6-astra.md` (the reviewer's blockers,
   recommendations, answers, and verdict), then section 5 above for each
   finding's disposition.
2. `planning/mvp-plan.md` S3-C.5 (L1656-L1828) beside it, to confirm the
   plan stays inside the shape; S3-C.7's M9 pre-authorization (L1889-L1905).
3. The facts section, if you want to check a citation.

## 8. Human decision checklist

- [ ] The plan stays within S3-C.5 and its defaults: no attestation, no
      SBI measurement extension, no vTPM, no IMA, no firmware or NOR
      write, no measurement of SPL, OpenSBI, or U-Boot.
- [ ] The claim's sentences (D-9) are the ones you want published, with
      the probe's slots.
- [ ] The three evidence classes stay separate as recorded (the log, the
      loader observation, the platform observation).
- [ ] The soft limit (6,000 lines) and the stops are acceptable.
- [ ] Q1 to Q19 at their defaults, or answered (Q17 is answered); the reading of S3-C.5's "CEL-JSON" as the derived profile (Q7) accepted or not.
- [ ] Each of the steering review's blockers B1 to B5 is answered as section 5's table says.
- [ ] Successor work stays excluded (M8's lane is separate; M10 waits).
- [ ] Exact commit `4f4a8f760a1ed7e5f9886b4e02e94b7a849bfc33` is accepted
      (authorizing M9-2 to M9-6), revisions are requested, or the review
      is deferred.

## 9. After the decision

- **Accept:** an acceptance record names `4f4a8f760a1ed7e5f9886b4e02e94b7a849bfc33`
  and the date; M9-2 to M9-6 run on `beryllium/mvp-m9` from the
  acceptance-record commit under the plan's stops; Part 1 Revision 3 is
  presented as its own exact commit when written; the probe is yours,
  when convenient, on the template; the fast-forward and push of the
  development branch stay on your instruction.
- **Request revisions:** a third candidate on the same branch; this
  packet updated; the second marked superseded (the first already is).
- **Defer:** the branch stays as it is; nothing starts.

**Status:** the M9 plan is **accepted** at exact commit `4f4a8f76`
(2026-11-03, `accept 4f4a8f76`; Q1 to Q19 at their defaults, Q17
answered) on local branch `beryllium/mvp-m9-plan`, which took the
development tip `55047781` by merge before the acceptance record;
unpushed; nothing is implemented, built, or run.
**Next:** M9-2 on `beryllium/mvp-m9` from the acceptance-record commit;
Part 1 Revision 3 comes to you as its own exact commit; M8-6 continues in
its lane.
**Action required from you:** none on this plan; the probe (Q31) is
yours when convenient; any `ff + push` of the M9 line is your
instruction.
