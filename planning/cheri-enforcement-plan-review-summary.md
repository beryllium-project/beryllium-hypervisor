<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# CHERI enforcement plan review packet

This packet supports the responsible human's decision on the
[CHERI enforcement plan](cheri-enforcement-plan.md), the bounded plan for
the instruction `accept 6944d7b4 ; push cheri and plan cheri enforcement`
(2026-11-06) on the [CHERI platform branch](cheri-platform.md), which
answers the question "on cheri, does it actually enforce anything during
these tests, or it just enabled & running?".

## Decision record

The responsible human accepted the plan at exact commit
`9ec57998148b693019e7af6eba88c2160bfc09da` on 2026-11-06 by the
instruction `accept 9ec57998; classify as proposed; soft limit increase to 4000; accept 9249dfd1`, whose first part is the reply section 1
requested. Q1 to Q12 apply at their defaults.

- **What it authorizes:** work packages CE-2 to CE-5 on
  `beryllium/cheri-enforcement`, from the commit that records the
  decision. The owner session merges them into `beryllium/cheri-platform`
  when the result is accepted.
- **What it does not authorize:** a push, a merge into `main`, a
  publication, a board command, or a claim beyond the plan's section 8.
- **Priority:** the instruction also directed that work for MVP 1.0
  takes priority, so this work runs behind the MVP 1.0 release path.

Sections 1 to 9 below are the packet as presented and are unchanged.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `9ec57998148b693019e7af6eba88c2160bfc09da` (`planning/cheri-enforcement-plan.md`, one file), parent `aa0aea140a2413d0937a0202a85ebf8f49cece8c` (`beryllium/cheri-platform`, as pushed to the private `origin` on 2026-11-06), on local branch `beryllium/cheri-enforcement-plan` |
| Current status | Plan written and checked (section 6); not reviewed; planning text only; written by an AI sub-agent of the owner session; four scratch experiments, not evidence, behind its facts; no independent review (the 2026-10-06 SOP) |
| Decision requested | Accept the exact commit, which authorizes work packages CE-2 to CE-5 with Q1 to Q12 at their defaults or as answered; request revisions; or defer |
| Successor status | No work package is started: no code, test, expectation, or record of the plan exists on any branch. `beryllium/cheri-enforcement` does not exist |
| Publication status | Private internal repository only. `beryllium/cheri-platform` is at `aa0aea14` on the private `origin`. This branch is local and unpushed, made in a separate clone whose push is disabled, for the owner session to import. Nothing touches `main` |

**Action expected from you:** reply `accept 9ec57998` to accept with Q1
to Q12 at their defaults, `accept 9ec57998 with Q<n>=<alternative>, ...`
to accept with answers, `revise: <what to change>`, or `defer`.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Review question |
| --- | --- | --- | --- | --- |
| The plan | `planning/cheri-enforcement-plan.md` (exact commit `9ec57998`) | The answer to your question, with sources; A to D evaluated with defaults; work packages CE-2 to CE-5: Zcheripte and the G-stage capability-write control, in-guest CHERI faults that must occur, a guest kernel's tagged store to the channel page that must end the run, and the records; the tests that must fault and their mutations; the branch page's claim words; 14 stops; risks; Q1 to Q12 | Planning text; its acceptance authorizes CE-2 to CE-5 on a work branch merged into `beryllium/cheri-platform` by the owner session, and nothing that reaches `main` | Is "bounded first capabilities" rightly set aside, and is the G-stage control plus the in-guest tests the enforcement you want shown? |
| This packet | `planning/cheri-enforcement-plan-review-summary.md` | Decision support | Decision support only | None |
| Registrations | `planning/cheri-platform.md` ("Enforcement plan (proposed)"), `planning/README.md`, `planning/.vitepress/config.mts`, `.github/copilot-instructions.md` (one sentence) | Navigation and the branch's own records | Documentation on this branch only; `planning/roadmap.md` and `planning/HANDOFF.md`, which are `main`'s, are not touched | Do they say "proposed", never "accepted" or "authorized"? |

## 3. Claim boundary

**What the exact commit supports saying.** A bounded plan exists, and
its findings, each cited at a pinned commit of a public repository:

- the CHERI-aware monitor already delegates the guests' own CHERI faults
  (`hedeleg` bit 28), and no test makes one;
- the guests' first PCC and `ddc` are the whole address space, and CHERI
  Alliance Linux requires that: it derives every capability from its
  first PCC and panics unless that PCC is the whole space with every
  permission, so bounding it is not feasible for Linux guests;
- the emulator checks a capability-write PTE bit (CW, bit 60) in every
  translation stage when its `cheri_pte` property is on, and the branch
  leaves it off, which is why CHERI guests boot today on leaves without
  CW;
- the emulator does not apply load-side capability caveats from the
  G-stage, and its store check depends on the declared pages' tag block
  holding no tag;
- CHERI Alliance Linux gives `MAP_SHARED` mappings no capability
  permission, so only a guest kernel can store a tag into the channel
  page.

**What remains trusted or assumed.**

- The emulator's G-stage capability-write check is the emulator's
  behaviour; RVY v0.9.10.1 leaves the G-stage field reserved, and the
  plan found no G-stage definition for v0.9.3. The planned evidence is
  about this emulator.
- The scratch experiments ran one toolchain (GCC) and one scenario
  (te-poc), one run each; anchor, two-guests, the sessions, and part 3
  under Zcheripte are untried until CE-2.
- The exception-trace toggle (Q2's default) silences the guest kernel's
  report of the deliberate fault only; that it does so deterministically
  rests on the sysctl being read at fault time (`kernel/signal.c`,
  `arch/riscv/kernel/traps.c`).

**Evidence unavailable or not run.** No work package has run, so no
branch check includes any of the tests. The scratch experiments are not
evidence. `npm run docs:source-check` was not run in this clone
(section 6).

**What the commit does not do.** It changes no code, test, expectation,
image, pin, or record; it changes nothing on `main`; it pushes, merges,
and publishes nothing; it edits nothing in the beryllium-cheri
repository; and it makes no claim beyond its section 8's planned words.

## 4. Load-bearing properties of the plan

| Property | Where the plan fixes it | How the work checks it |
| --- | --- | --- |
| The plain variant stays `main`'s, byte for byte | Section 5's gates; stop 1 | `cheri-check` part 2: 162 boot images equal to the reference on every code commit |
| Nothing reaches `main`, and the development line's checks, claim, ledger, scenarios, and guest pins stay | Section 2; stops 2 to 4 | `make -C mvp check` passing every step but `claim-ledger-check`, which fails for the same seven files and no other |
| The window leaves allow tags and the declared pages refuse them | CE-2; section 6, B1 and B2 | Host tests; the walker at every boot; `PTE.CW support: yes` in every CHERI guest; `channel-cw` refused at boot |
| A guest kernel's tagged store to the channel page ends the run, and the store is real | CE-4; section 6, B3 and B4 | `cap-store` with Zcheripte: the exact `BE_MVP:DETAIL` (cause `0x17`, `htval=0x21000020`, `htinst=0x0`, `spvp=1`); without it: the tag lands and the run completes |
| A guest's own CHERI fault is delivered to it and the run continues | CE-3; section 6, C1 to C3 | `SEGV_CAPBOUNDSERR` at base plus 16; `EFAULT` from the usercopy; `cheri-fault-hs` ending the run when bit 28 is not delegated |
| No expectation is relaxed, and every rule reads values | Section 7; stop 13 | Each new rule's mutations rejected |
| The words on the branch page match the evidence | Section 8; Q12 | The result packet quotes the counts from the last check |

## 5. Review history and resolved findings

No independent review was run (the 2026-10-06 SOP). The owner session
reviews the branch before presenting it. Findings made while drafting,
and how the plan answers them:

- **The premise about delegation was out of date.** The question set
  for this plan said a guest's own CHERI fault is terminal in HS; that is
  the beryllium-cheri dossier's statement about the development line's
  monitor. This branch's monitor delegates cause 28, and a scratch run
  showed a guest process receiving its own `SEGV_CAPBOUNDSERR`. The plan
  therefore adds tests rather than delegation, plus `cheri-fault-hs` to
  show the delegation is what keeps the run going.
- **"Bounded first capabilities" does not survive the guest's own
  rules.** CHERI Alliance Linux's root check and its use of both halves
  of the address space rule it out; a scratch run with a 64 MiB-bounded
  PCC stopped in early boot. The plan keeps r4 as a design fact and makes
  it a checked line (Q6).
- **The emulator has the G-stage control, off by default.** beryllium-cheri's
  proof of concept read the guest's "PTE.CW support: no" as the emulator
  lacking it; with `cheri_pte=on` the emulator raises cause 23 on a
  tagged store to a G-stage leaf without CW. The plan corrects the
  statements on Beryllium's side only.
- **A user-level test cannot exercise the G-stage control.** The guest's
  purecap user ABI strips the tag before any page-table check. The plan's
  test uses a CHERI-only guest kernel module (Q11).
- **The guest kernel's report of a user CHERI fault holds "Call Trace:".**
  The plan's default turns the guest's exception trace off around the
  deliberate fault (Q2) rather than exempting the substring.
- **The emulator's store check depends on its TLB and tag blocks.** The
  plan keeps the tested integer-then-capability order and makes a layout
  change near the declared pages a stop (12).
- **`htinst` is zero for the capability store**, which the denial leaf
  accepts; the leaf's own W bit tells a capability-store fault from a
  write denial. The plan fails closed (Q1) and leaves `mvp-sbi.c`, in
  M8's frozen record, unchanged.
- **A claim-phrasing hazard.** The QEMU option for the hart count matches
  one of the claim's conditional phrasings, so the plan describes the
  invocation in words.
- **A review-command constraint.** The commands in section 7 run from the
  root of your canonical checkout: a home-relative path containing the
  repository's name would trip the planning pages' private-locator rule,
  so the `cd` is left to you.

Questions worth a word, open for your judgement:

- **Q1:** fail closed on a tagged store to a declared page, or a denial
  that the guest kernel can recover from;
- **Q2:** the guest kernel's `/proc` and exception-trace sysctl for the
  tests, or a narrowly scoped checker exemption;
- **Q3:** the in-guest tests in te-poc only, or in every scenario;
- **Q7:** Zcheripte for part 3 and the live runs too;
- **Q11:** a CHERI-only test module under `GPL-2.0-only`.

## 6. Validation and retained evidence

On the exact content of `9ec57998` (the index before the commit, the
tree clean after it), in the clone, on 2026-11-06 at about 21:30 UTC:

| Command | Result | Covers |
| --- | --- | --- |
| `git diff --cached --check` | PASS | Whitespace |
| `node scripts/check-doc-sources.mjs` | PASS, `site_markdown=188 policy_markdown=6 rendered_references=1992 configured_routes=469` | Links, anchors, the private-locator rule, and headings on the planning and Helium sites and the policy documents |
| `node docs/check-links.mjs --tasking-contract` | PASS | The owner tasking contract |
| `node docs/check-links.mjs --tasking-fence-regression` | PASS, 8 cases | The tasking-section regression |
| A text search of the plan for `mvp/docs/claim.md`'s forbidden phrasings, private repository locators, and home-directory paths | None found | The writing rules |
| `npm run docs:source-check` | Not run | Its Unix-socket cases need a short temporary directory, which this clone's path does not give; the owner session runs the unmodified command after the import |

The same checks passed on this packet commit's content before it was
made, the documentation check then counting the second new page and
the new routes.

**Read-only probes behind the plan's facts:**

- the CHERI Alliance QEMU source at `008944fe` (`cpu.c`, `cpu_bits.h`,
  `cpu_helper.c`, `csr.c`, `cputlb.c`, `cheri_tagmem.c`,
  `op_helper_cheri_common.c`) and beryllium-cheri's two local changes'
  build script;
- the CHERI Alliance Linux source at `3934c32f` (`head.S`,
  `riscvcheri.c`, `traps.c`, `uaccess.S`, `mm/init.c`, `mman.h`,
  `pgtable.h`, `lib/user_ptr.c`, `kernel/signal.c`, `siginfo.h`,
  `access_ok.h`) and the built guest's `.config`;
- the CHERI Alliance OpenSBI source at `c0575bc8` (`sbi_hart.c`);
- the branch's `mvp/src/` CHERI code, the G-stage builder and walker,
  the denial leaf, `mvp/tests/check-capture.py` and
  `mvp/tests/check-image.py`, `mvp/tools/gen-scenario.py`, the harness,
  and the CHERI guest build;
- the beryllium-cheri dossier (rows 3 and 4, and section 8), its proof
  of concept's and CHERI-guest experiment's records, and its handoff;
- the claim ledger's pinned files, hashed against the branch to list the
  seven that already differ.

**Scratch experiments (not evidence):** E1 to E4 of the plan's section
3.6, run between 20:52 and 21:12 UTC under the clone's ignored
`build/scratch/`, where their patches, console logs, and trap log remain;
their build trees were deleted afterwards. No MVP or model gate ran:
none is needed for a planning commit.

## 7. Recommended human review sequence

1. The plan's "The answer in brief", its closing "What acceptance would
   authorize", and its section 11 (Q1 to Q12).
2. Section 3.2 (the guests' first capabilities) and section 4's row A.
3. Section 3.3 (the G-stage and capability flow) and section 4's row B.
4. Sections 5 and 6: the work packages and the tests that must fault.
5. Section 8 (the words for the branch page), then sections 9 and 10.

Run these from the root of your canonical checkout of the private
internal repository, once the owner session has imported the branch:

```sh
git show 9ec57998148b693019e7af6eba88c2160bfc09da:planning/cheri-enforcement-plan.md | gp
git show beryllium/cheri-enforcement-plan:planning/cheri-enforcement-plan-review-summary.md | gp
git show --stat 9ec57998148b693019e7af6eba88c2160bfc09da
git diff --stat aa0aea14 beryllium/cheri-enforcement-plan
```

If `gp` is not defined in your shell, replace `| gp` with `| glow -p`.

## 8. Human decision checklist

- [ ] Setting aside bounded first capabilities, with the evidence of
      section 3.2, is acceptable.
- [ ] The G-stage capability-write control under the emulator's
      Zcheripte (CE-2, CE-4; Q1, Q7) is the enforcement between domains
      you want shown.
- [ ] The in-guest tests and the handling of the guest kernel's report
      (CE-3; Q2, Q3) are acceptable.
- [ ] Deferring monitor self-protection (D; Q5) is acceptable.
- [ ] The negative images, the control run, and the mutations (section 6;
      Q4) cover what must fault.
- [ ] Section 8's words for the branch page (Q12) are right.
- [ ] Where the work lands (Q9), the soft limit (Q10), and the module's
      licence (Q11) are acceptable.
- [ ] Any push, merge into `main`, and publication remain excluded.
- [ ] Accept `9ec57998148b693019e7af6eba88c2160bfc09da`, request
      revisions, or defer.

## 9. After the decision

- **Accept:** your instruction names this exact commit, with the answers
  you give or the defaults. An acceptance record names `9ec57998`, the
  date, and the answers, in the plan's decision record, this packet, the
  branch page, the planning README, and the instructions.
  `beryllium/cheri-enforcement` starts from that record, and CE-2 begins.
  The result comes to you as one exact commit with its own packet.
  Nothing is pushed.
- **Request revisions:** a new commit and a new packet; `9ec57998` is
  not treated as accepted.
- **Defer:** nothing starts; the branch stays local.

**Status:** the CHERI enforcement plan is proposed at exact commit
`9ec57998148b693019e7af6eba88c2160bfc09da` on local branch
`beryllium/cheri-enforcement-plan` (parent `beryllium/cheri-platform`
`aa0aea14`), unpushed. It is not reviewed, and no work package is
started.

**Next:** your decision on `9ec57998`, with Q1 to Q12.

**Action required from you:** from the root of your canonical checkout,
once the branch is imported, read the plan with `git show
9ec57998148b693019e7af6eba88c2160bfc09da:planning/cheri-enforcement-plan.md
| gp` (or `| glow -p`), then reply `accept 9ec57998` (Q1 to Q12 at their
defaults), `accept 9ec57998 with Q<n>=<alternative>, ...`, `revise: <what
to change>`, or `defer`.
