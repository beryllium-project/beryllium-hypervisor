<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M7 plan review summary

This packet presents one decision: the [M7 plan](mvp-m7-plan.md),
interactive guests, at exact commit `4f4d094efb3985435673f7bda62f35ad51c6165e` (parent `f5dc770b`, the
development branch's tip: Plan revision S3-C accepted, debt sweeps 3 to
5 accepted) on local branch `beryllium/mvp-m7-plan`. The plan bounds the
milestone S3-C.3 defines, under S3-C's Q27 to Q46 at their defaults,
stops (a) to (i), and board policy item 8. The packet recorded the
decision below after it was given.

## Decision record

The responsible human accepted exact commit
`4f4d094efb3985435673f7bda62f35ad51c6165e` (parent `f5dc770b`) as the
M7 plan on 2026-11-01 (14:43 in the human's time zone) by the
instruction `accept 4f4d094e`, the reply to this packet's request; the
abbreviation was checked to resolve uniquely
(`git rev-parse --disambiguate=4f4d094e`). No question was answered: Q1
to Q16 apply at their defaults.

- **Scope:** acceptance covers exactly the plan text at that commit and
  this packet's claim boundary (section 3). Sections 1 to 9 are the
  packet as presented, apart from the status rows of section 1 and the
  closing lines of section 9, which now show the outcome.
- **What it authorizes:** M7-2 to M7-6 on branch `beryllium/mvp-m7` from
  the acceptance-record commit, under the plan's thirteen stop
  conditions and its soft limit; Part 1 Revision 2 as its own exact
  commit for the human's decision when written; board commands only
  after the human confirms the COM260 free, with the human present,
  under board policy item 8. Nothing else: no push, merge, tag,
  publication, release step, or kexec; no claim change beyond the plan's
  "Claim text"; nothing of M8, M9, or M10.
- **Not directed:** a fast-forward or push. The development branch
  `beryllium/single-hart-runtime-r0` stays at `f5dc770b` locally and on
  the private `origin`; `beryllium/mvp-m7-plan` is local.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `4f4d094efb3985435673f7bda62f35ad51c6165e` (parent `f5dc770b`) on local branch `beryllium/mvp-m7-plan`; it adds `planning/mvp-m7-plan.md` and this packet and registers them; no `mvp/`, `model/`, or accepted file changes |
| Current status | Documentation only; **responsible-human accepted as of 2026-11-01** (the decision record above), Q1 to Q16 at their defaults; local, unpushed |
| Decision requested | None outstanding; the decision was `accept 4f4d094e` |
| Successor status | M7-2 to M7-6 are authorized on `beryllium/mvp-m7` from the acceptance-record commit and start on the same day; Part 1 Revision 2 will be presented as its own exact commit during M7-5; the M8 and M9 plans (authorized by S3-C) and M10 are not started |
| Publication status | Private repository. The development branch is at `f5dc770b` locally and on the private `origin`; this branch is unpushed. The public review snapshot is at `36e2590c`. No tag, publication, or release |

The action this section asked of the human, the decision on
`4f4d094e`, is taken; what follows it is in the decision record above
and in section 9.

### What the plan is, in one paragraph

Console input through the control hart: hart 0 polls the firmware's
`sbi_debug_console_read` on its own Sstc timer, a pure three-state parser
routes bytes by a two-byte focus sequence (`~0`, `~1`, `~~` literal) typed
at line start, a dedicated input-only ring per domain hart in the block's
unused region carries them with no IPI, and the domain hart serves DBCN
read for a domain whose sealed configuration grants console input,
copying into the guest only after the write-authority check the write
path already has. Drops are counted by reason and printed; nothing about
input fails a hart or the run. The output path does not change and its
two invariants become tested claims. A pinned static BusyBox with musl
(soft float, with the locked GCC's `lp64` multilib) joins the one guest
Image; the shell is an `argv[0]` variant of the in-tree init, selected
in new `shell` variant images, with helper verbs for the channel and the
denials, so every accepted expectation stays intact but the SBI version
line. Scripted sessions, static files typed by a QEMU typist in lockstep
with a per-run nonce, are judged by the capture checker as a gate; the
board gets one typed characterization under item 8 and no campaign. The
console grant is a configuration fact, not a policy grant (Q43); the
triggers do not fire; Part 1 gets an additive revision; `InputRing.v`
covers the new ring beside `Binding.v` or a gap row says it does not.
The claim gains S3-C.7's pre-authorized sentences, fixed in words.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Review question |
| --- | --- | --- | --- | --- |
| The M7 plan | `planning/mvp-m7-plan.md` | the milestone's design (D-1 to D-12), the trigger evaluation, the claim words, six work packages, a soft limit of 8,000 lines, thirteen stops, Q1 to Q16 | planning text; authorizes M7-2 to M7-6 on acceptance | Is the design S3-C.3's shape, with its defaults, and nothing more? Are the claim sentences the ones you want? |
| This packet | `planning/mvp-m7-plan-review-summary.md` | the decision support | decision support only | — |
| Registrations | `planning/README.md`, `planning/roadmap.md`, `planning/HANDOFF.md`, `planning/.vitepress/config.mts`, `.github/copilot-instructions.md`, `mvp/README.md` | the plan's place in the maintained documents | documentation | — |

## 3. Claim boundary

**What the commit supports saying:** a bounded plan exists for M7 whose
every design choice traces to S3-C.3's shape or to one of its own open
questions with a default; its facts were read in the tree at `f5dc770b`
with line numbers, and the two facts S3-C left to be checked hold (the
locked cross GCC has the `lib64/lp64` multilib and links with it; the
markers run to `:14`, so `:15` to `:18` are free).

**What it does not do:** no code, no model text, no claim change (the
sentences are fixed here and take effect only through the result's
acceptance, S3-C.7), no board command, no push. The plan does not
promise that the board's firmware console supplies input (that is what
the characterization decides; stop 10) nor that BusyBox and musl build
at the first attempt under the soft-float ABI (stop 8 names the
fallback's cost).

**What stays trusted or assumed in the design:** the operator and the
typing tool (trusted inputs, stated in the claim's limit and Part 1
Revision 2); Linux's `hvc` polling driver (the 2 s idle back-off is a
latency, stated); the firmware console's read path (no input buffer;
loss is an availability matter, stated); the upstream BusyBox and musl
releases and their signing keys.

## 4. Load-bearing decisions

| Decision | Content | Why this way |
| --- | --- | --- |
| D-1 | hart 0 polls on its own timer; a dedicated input ring; DBCN read served under the write-authority rule; drops counted | S3-C.3's shape and Q45's default; the read exit is the domain hart's natural point; no new wake is needed because `hvc` polls |
| D-2 | a documented output bound, not backpressure | the smaller change; the outbound ring's fail-closed property stays; the overflow is visible and an availability matter the claim excludes (Q3) |
| D-3 | `~0`, `~1`, `~~` at line start; a pure parser; a hart-0 focus line; lockstep typing | Q28's default; the conserver convention is printable and typeable through picocom and tmux (Q1) |
| D-4 | the output invariants stated and tested; line mode; a paused domain's partial line flushed | Q44's default; the invariants are what stops forgery and terminal queries |
| D-5, D-6 | the console grant a configuration fact; the triggers evaluated and found not to fire | Q43's default; M2's precedent for Instance 3 |
| D-7, D-8 | Part 1 Revision 2 as its own commit; `InputRing.v` beside `Binding.v` or a gap row | stop 1 as S3-C amended it; `Binding.v`'s types are closed, so an importing module cannot extend them |
| D-9 | BusyBox and musl pinned external inputs, soft float, in the one Image; the shell a `shell` variant; helper verbs of the one init | Q29's and Q27's defaults; the accepted expectations stay intact; no BusyBox `devmem` (M1-A's rejected substring) |
| D-10 | the SBI version 3 to 5 (4 to 6) in every image; the version line the one declared-line change | D8's rule; the surface exists in every image |
| D-11 | scripted sessions in QEMU as a gate; a run nonce; the checker's reconciliation with the keystroke log | Q30's default; the nonce defeats canned transcripts |
| D-12 | one typed characterization on the board, no campaign | Q31's default; stop (f) decides the firmware console |

## 5. Review history and resolved findings

The plan was written on the session model from the accepted S3-C text
and a read-only fact sheet of the tree (an explore agent on
`claude-opus-5.5`, 2026-11-01; its facts re-checked where cited). Three
things the writing settled:

1. **S3-C's line citations check out** against `f5dc770b` (`mvp-sbi.c`
   L416-L418 and L443-L447; `mvp-layout.h` L203 and L401;
   `mvp-gstage.h` L71-L77); the console-feed function spans L941-L974,
   not L946-L975 as S3-C says (cosmetic; the plan cites the real span).
2. **`Binding.v` cannot be extended by import** (closed inductives), so
   the plan's default is a separate module about the input ring alone
   with a gap row, not an extension of the binding proof.
3. **The soft-float build is possible** with the locked toolchain
   (`-print-multi-lib` lists `lib64/lp64`; a static `-lgcc` link under
   it resolves), so the plan need not put FP in the guest kernel; stop 8
   covers the case where BusyBox or musl still will not build that way.

Open for your judgement, beyond the defaults: the claim sentences'
words; whether a live `shell` session (Q12's `live` variant) belongs in
1.0 at all or only the scripted ones; whether to ask for a steering
review of this plan (Q16).

## 6. Validation and retained evidence

Documentation checks only: `node scripts/check-doc-sources.mjs` PASS at
the packet commit (the new page, its route, and its references), `git
diff --check` clean, `git status` clean, the accepted plan text and every
`mvp/` and `model/` file unchanged by `git diff --stat f5dc770b`.
Nothing was built or run.

## 7. Recommended human review sequence

```sh
git worktree add --detach /tmp/be-m7-plan 4f4d094efb3985435673f7bda62f35ad51c6165e
cd /tmp/be-m7-plan
git diff --stat f5dc770b..HEAD
```

1. `planning/mvp-m7-plan.md`: "Claim text" (the words that will be
   published), then D-1, D-3, D-4 (the security-relevant mechanism),
   then D-9 (what enters the guest image), then the stops and Q1 to Q16.
2. `planning/mvp-plan.md` S3-C.3 (L1294-L1485) beside it, to confirm
   the plan stays inside the shape.
3. The facts section, if you want to check a citation.

## 8. Human decision checklist

- [ ] The plan stays within S3-C.3 and its defaults: no board campaign,
      no console class, no backpressure, no shell in the protected
      domain, no change to the output path.
- [ ] The claim sentences are the ones you want published (section
      "Claim text").
- [ ] The trusted-input boundary (the operator and the typing tool) is
      acceptable.
- [ ] The soft limit (8,000 lines) and the stops are acceptable.
- [ ] Q1 to Q16 at their defaults, or answered.
- [ ] Successor work stays excluded (M8, M9, M10 plans are separate).
- [ ] Exact commit `4f4d094efb3985435673f7bda62f35ad51c6165e` is accepted (authorizing M7-2 to M7-6),
      revisions are requested, or the review is deferred.

## 9. After the decision

- **Accept:** an acceptance record names `4f4d094efb3985435673f7bda62f35ad51c6165e` and the date; M7-2 to
  M7-6 run on `beryllium/mvp-m7` from the acceptance-record commit under
  the plan's stops; Part 1 Revision 2 is presented as its own exact
  commit when written; the board step waits for your confirmation and
  presence; the fast-forward and push of the development branch are on
  your instruction.
- **Request revisions:** a second candidate on the same branch; this
  packet updated; the first marked superseded.
- **Defer:** the branch stays as it is; nothing starts.

**Status:** the M7 plan is **responsible-human accepted as of
2026-11-01** at exact commit `4f4d094e` (`accept 4f4d094e`; Q1 to Q16
at their defaults); M7-2 to M7-6 are authorized on `beryllium/mvp-m7`
from the acceptance-record commit; the development branch is not moved
and nothing is pushed.
**Next:** M7-2 (userland) and M7-3 (the monitor) on `claude-opus-5.5`
sub-agents in worktrees, reviewed line by line, then M7-4 to M7-6; Part
1 Revision 2 to you as its own commit when written; the board step when
you say the COM260 is free.
**Action required from you:** none on this commit.
