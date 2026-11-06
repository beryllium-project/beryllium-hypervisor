<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M0 plan: review summary

This packet supports a responsible-human decision on one exact commit. It
was presented as decision-neutral and not self-approving; the decision
record below holds the outcome.

## Decision record

The responsible human accepted exact commit
`4d129808979cb54b7e0a7cc0b3e79d39533e0b9c` (parent `391cfaed`) as the M0
plan on 2026-10-23 with the instruction
`accept 4d129808, proceed with implementation using opus-5.5 model`,
given in reply to this packet's request to accept, revise, or defer that
exact commit. The abbreviation was checked to resolve uniquely to that
commit.

- **Scope:** acceptance covers exactly the plan text at that commit,
  revision 2. Sections 1 to 9 are the packet as presented, apart from the
  outcome rows in section 1, a note above the section 8 checklist, and
  the closing lines of section 9. The plan carries its own decision
  record. The first candidate `6e4b9d4a` and revision 1 `d95b28e9` stay
  superseded and were never accepted.
- **Open questions:** Q1 to Q13 were not answered, so their defaults
  apply, as listed in the plan's decision record.
- **Effect:** M0 implementation is authorized under the plan, work
  packages M0-1 to M0-6, on branch `beryllium/mvp-m0` from the
  acceptance-record commit, using the `claude-opus-5.5` model as the
  instruction directs; each stop condition returns M0 to the responsible
  human, and M0 ends in one result review packet for a separate
  decision. No M1 or later work, push, merge into the development
  branch, publication, or release follows from it.
- **Decision support:** the packet commits `688672e7`, `391cfaed`, and
  `9c3953bf` and this acceptance-record follow-up are decision support,
  not plan content.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `4d129808979cb54b7e0a7cc0b3e79d39533e0b9c` (tree `9d14ce71c325a8268efb1e6e1ae5732bfa85a7ec`), parent `391cfaed3e7a097660b11026472ecd64694f18d5`, revision 1's packet commit; branch `beryllium/mvp-m0-plan`, from the S3 acceptance record `1fb46419` |
| Superseded candidates | `6e4b9d4a1e2da249d68aeb4e1aea5a27cf3755f8` (tree `f71a9335`), the first M0 plan candidate of 2026-10-23, superseded the same day by revision 1 on the responsible human's question whether any hart number is special; and `d95b28e953bccbdd489b1e6eec69d48fa028fd29` (tree `752be7d9`), revision 1, superseded the same day by revision 2, which adds the scratch QEMU probe's facts. Neither was accepted |
| Current status | Documentation only: revision 2 of the bounded plan for M0, written under the accepted [MVP plan](mvp-plan.md) (`93967fba`, accepted 2026-10-23 by `accept 93967fba`), whose acceptance authorized writing it; directed on 2026-10-23 by the choice `(b)` and the instruction `sure. update that, then proceed with (a) and continue development`; the fast source checks pass. Recorded outcome: accepted on 2026-10-23 (`accept 4d129808, proceed with implementation using opus-5.5 model`) |
| Decision requested | Accept the exact commit as the M0 plan, request revisions, or defer; answer any of its Q1 to Q13 or let the defaults apply. Q1 to Q13 were not answered; their defaults apply |
| Successor status | M0 implementation (work packages M0-1 to M0-6) authorized under the plan on branch `beryllium/mvp-m0` from the acceptance record, not yet started at the accepted commit; M1 to M4 not started and not authorized; no stop condition fired |
| Publication status | Private repository; the target is on local branch `beryllium/mvp-m0-plan`, unpushed. On 2026-10-23 the same instruction carried out `(a)`: the development branch `beryllium/single-hart-runtime-r0` was fast-forwarded from `0096de3e` to `1fb46419`, the S3 acceptance record, and pushed to the private `origin` together with `beryllium/s3-mvp-plan`; local and `origin` agree at `1fb46419`, which is this branch's base. No tag, publication, or release |

As presented, the packet asked for the exact target to be accepted,
revised, or deferred; the [decision record](#decision-record) above holds
the outcome.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| The M0 plan, revision 2 | [`mvp-m0-plan.md`](mvp-m0-plan.md) | Defines M0's goal and pass criterion; the MVP line `mvp/` seeded from B7; hart identifiers as configuration, with the control hart fixed at 0 by the accepted boot check and the domain harts as scenario data; the static multi-hart substrate (the control hart, the hart region, SBI HSM hart start, the boot barrier, the per-hart fast path, single-writer rings, SBI IPIs, the control loop, failure paths); the guest controls per hart; the tool lock and the digest-pinned evaluator; scenarios as data and the harness stages; the platform-record probes and the negative images; the markers; tests, image-checker profiles, and QEMU scenarios with eight harts; budgets, with three planning measurements; departures from B7; risks; the claim boundary; work packages M0-1 to M0-6; twelve stop conditions; the board procedure; and Q1 to Q13 with defaults | A plan only: it authorizes, if accepted, M0 implementation within its text and nothing else; no code, model, board, hart start, push, or release change | Is the substrate design the right first multi-hart step: a control hart that starts two domain harts once, a boot barrier, rings with one writer each, IPIs both ways, native `wfi`, and no scheduler (its "Architecture")? |
| Navigation | `planning/.vitepress/config.mts` | Lists the plan in the three navigation lists | Site configuration only, added in the superseded candidate `6e4b9d4a` | None beyond placement |
| Status pages | [`roadmap.md`](roadmap.md), [`HANDOFF.md`](HANDOFF.md), [`project-orientation.md`](project-orientation.md), [`README.md`](README.md), [`glossary.md`](glossary.md), [`implementation-plan.md`](implementation-plan.md), `.github/copilot-instructions.md` | Record the proposed plan, its revision, and the development-branch fast-forward and push | Changed in this packet's commit, not in the target; status text only | None |

Exact changed-file inventory:

```text
# git diff --name-status 391cfaed 4d129808
M	planning/mvp-m0-plan.md
# git diff --name-status 688672e7 d95b28e9   (revision 1, superseded)
M	planning/mvp-m0-plan.md
# git diff --name-status 1fb46419 6e4b9d4a   (the first candidate, superseded)
M	planning/.vitepress/config.mts
A	planning/mvp-m0-plan.md
```

`git diff --stat 1fb46419 4d129808 -- model/ include/ virt/ arch/ bringup/
tests/` is empty. Revision 2 changes 48 lines and removes 20 against
revision 1 (`git diff --stat 391cfaed 4d129808`).

## 3. Claim boundary

**The commit supports saying:** Beryllium has a proposed bounded plan for
M0, the first MVP milestone, in its second revision. It stays within the
accepted MVP plan's M0 deliverables 1 to 5, its exit, its hart layout,
and its decisions D1 to D16 with Q1 to Q12 at their defaults; it names
the base, inputs, and facts it relies on; it states that hart IDs are
configuration and why the control hart is nonetheless fixed at 0; it
fixes the memory layout, markers, budgets, checker rules, QEMU
scenarios, board procedure, work packages, and stop conditions; and it
records what it departs from and what it does not claim.

**Trusted or assumed:**

- The accepted documents and records the plan cites say what it quotes.
  The B7 facts (measured text, data, and BSS ends; 583 and 594 exits per
  guest; about 360 `wfi` and 65 slice exits per guest; about 10 KB of
  console output per guest; the preflight's eight harts with `h`,
  `sstc`, `smaia`, `ssaia`, `svinval`, `sstvala`, and `shtvala`; "SBI
  HSM extension detected") were read from `bringup/k3-b7/README.md`,
  `planning/k3-b7-plan.md`, `planning/k3-b7-result-review-summary.md`,
  and `bringup/k3-b7/results/20261008-com260/preflight.txt`. The R3
  boot check (`virt/be/r3.c`, `hart_id != BE_CONFIGURATION_HART_ID`),
  the accepted reset and install functions (`arch/riscv/be/privileged.S`),
  B3's shim (`bringup/k3-b3/src/b3-shim.S`), and B7's vector and tail
  (`bringup/k3-b7/src/b7-trap.S`) were read for the design.
- Three planning measurements were made on 2026-10-23, with scratch
  under the gitignored `build/mvp-research/`. Two are read-only against
  B7's existing build outputs under `build/k3-b7/`: `riscv64-linux-gnu-nm
  -S` on both toolchains' B7 images for the symbols M0 drops (about
  `0x3e0` bytes of text for GCC and `0x5c0` for Clang), and ten
  eight-hart runs of B7's GCC boot ELF under QEMU 10.2.2 and the pinned
  OpenSBI v1.6, which reported `Boot HART ID` 3, 7, 2, 4, 3, 4, 0, 5, 0,
  2. The third is a 2.4 KiB freestanding S-mode probe written for the
  purpose, not Beryllium code and never committed (`probe.S`, `probe.c`,
  `probe.lds`, `run.sh` under `build/mvp-research/hsm-ipi/`), run eight
  times with eight harts (six on the `k3-like` machine, two on `plic`)
  and once with one: in every eight-hart run every non-boot hart was HSM
  `STOPPED`, `hart_start` succeeded with the opaque word delivered, an
  SBI IPI woke the boot hart from `wfi`, and the reply IPI and a fenced
  acknowledgement completed the round trip; with one hart,
  `hart_get_status` of a nonexistent hart returned -3. They are planning
  facts, not M0 evidence, and the plan cites them as "planning research
  1", "2", and "3".
- No Beryllium image has started a second hart, taken an IPI in HS, or
  shared a page between harts. Every multi-hart behaviour in the plan is
  design: that HSM `hart_start` works after a Linux kexec on this
  firmware, that IPIs reach HS while a domain runs at V=1 (the probe
  tested delivery to a hart waiting in HS only), and that the layout's
  harts are coherent are inferences the plan marks and turns into
  probes and stop condition 6; that QEMU's boot hart differs from 0 in
  most eight-hart runs is measured, and the `shim-rule` variant
  exercises the rule deterministically.
- The budget inferences (M0's text about `0x300`-`0x600` above B7's,
  within `0x100`-`0x400` of the Clang limit; about 160 exits per domain;
  a 32 KiB ring against about 10 KB of output) are estimates from B7's
  measured values and the symbol measurement, to be measured at M0-3
  and M0-4; the Clang text budget is the plan's acknowledged tight spot,
  with stop 3 and a named remedy to propose if it overruns.
- That the work packages are feasible as scoped is a planning judgment,
  not evidence. No code exists, and the plan gives no effort or date
  estimate.
- The session ran on `claude-fable-5.1` after the responsible human
  switched the model from the pinned `claude-opus-5.5`; the pin in
  `.github/copilot-instructions.md` is unchanged. No research agent,
  independent review, separate scope review, or deep security review
  ran (the 2026-10-06 SOP).

**Unavailable or not run:** no implementation, build, QEMU run, board
run, hart start, or proof; no generated HTML, `npm run docs:build`,
`./be docs-check`, or Chromium render.

**Not implemented:** everything in M0, including `mvp/`, the tool lock,
the evaluator image, the substrate, the probe images, the scenario
generator, the checkers, and the platform record; and everything in M1
to M4.

## 4. Load-bearing decisions

| Decision | Where stated | Evidence |
| --- | --- | --- |
| The plan implements the accepted MVP plan's M0 without changing it: deliverables 1 to 5, the hart layout, D14 to D16, Q1 to Q12 at defaults, the harness rules, stop conditions 1 to 7 | "Base and inputs"; "Architecture"; "Stop conditions" | Reading against `mvp-plan.md` at `93967fba` |
| Hart IDs are configuration, not authority; the control hart is fixed at 0 only because the accepted R3 boot check and B3 shim require it, a static binding needs a fixed control-hart ID, and every board run entered on hart 0; the domain harts are scenario data validated at boot | "Hart identifiers"; Q2; Q12 | `virt/be/r3.c:292`; `bringup/k3-b3/src/b3-shim.S`; every B-series `SHIM hart=0x0` record; S1 H03 |
| The branch starts from the S3 acceptance record `1fb46419`; after `(a)` on 2026-10-23 the development branch is at the same commit locally and on `origin` | "Decision requested"; the status record | `git merge-base --is-ancestor 0096de3e 1fb46419`; the push record in section 1 |
| Hart 0 keeps the accepted layout and prelude; each domain hart owns a 64 KiB block in a new NOLOAD region with its saved page at its stack top, so the vector and tail derive the record from `sscratch` | "Hart region"; Q1 | Reading of B7's vector and tail, which hard-code the management stack and saved page |
| Every `hgatp` write and `hfence.gvma` stays in the accepted R3 functions; the install function keeps two call sites in the MVP image; the probe images' raw `hgatp` write is the one listed exception | "G-stage and VMIDs"; "Tests and evidence" | The B7 rule, carried over; the probe profile and its mutation |
| The firmware SBI surface grows by exactly HSM `hart_start`, HSM `hart_get_status`, and IPI `send_ipi`, through the accepted helper, so the image keeps one `ecall` site | "Guest SBI subset and the firmware surface"; stop 2 | MVP plan D15; `arch/riscv/be/r0-sbi.h` names the accepted four |
| The shim starts hart 0 through HSM if another hart boots, so the accepted R3 hart check stands | Q2; "Boot sequence on hart 0" | `virt/be/r3.c:292`; the `shim-rule` QEMU variant |
| A full ring fails closed, as the accepted MVP plan states; the ring is sized at 32 KiB against 10 KB measured, and the high-water mark is recorded with a stop above half | "Hart region"; "Budgets"; stop 3 | MVP plan M0 deliverable 5; B7's console figure |
| The guest-visible SBI surface is unchanged, so the implementation version stays 3 | Q3 | MVP plan D8's versioning rule |
| The platform record's probes are separately linked images run on the board before the scenario; their values are facts, and only the named contradictions are stops | "Platform record: probes and negative images"; stop 6 | MVP plan M0 deliverable 4 and stop condition 2 |
| Eight RAM-only kexec runs with human resets, automation never typing at U-Boot | Q6; "Board safety and procedure" | The B-series board-safety rules |

## 5. Review history and resolved findings

Revision 2 (2026-10-23, later again):

1. **The HSM and IPI probe.** Under `continue development`, with M0
   implementation not authorized, the session wrote a scratch S-mode
   probe in B7's planning-research style and ran it in QEMU, turning two
   of the plan's inferences into emulation facts: HSM status and start
   of a stopped hart, and SBI IPI delivery to a hart waiting in HS. The
   plan cites them at the boot sequence, the control loop, and two
   risks, and adds the -3 status error to the fail-closed firmware
   check. Delivery at V=1 stays untested until the `probe-platform`
   image. The probe is not Beryllium code and is not committed; the
   statement that no Beryllium image has started a second hart stands.

Revision 1 (2026-10-23, later the same day):

1. **Hart identifiers.** The responsible human asked `do we need to
   specify hart 0? why are any hart numbers special?` and then directed
   `sure. update that, then proceed with (a) and continue development`.
   The plan gains "Hart identifiers": no hart number is special to the
   architecture; hart IDs are configuration, not authority; the control
   hart is fixed at 0 for three stated reasons about accepted code and
   the platform; the domain harts are scenario data; the shim's start
   rule exists only to satisfy the accepted check, and a boot contract
   accepting any boot hart belongs to the clean-repository design.
2. **Planning measurements.** Two read-only measurements against B7's
   existing build outputs replaced inferences: the dropped symbols' sizes
   narrow the Clang text-budget estimate, and ten eight-hart QEMU runs
   show the boot hart differs from 0 in most runs, so the shim's start
   rule is exercised in ordinary eight-hart runs as well as by the
   `shim-rule` variant.
3. **Numbering and ASCII.** The probe-toolchain question moved to Q13 so
   that Q12 matches the accepted MVP plan's Q12 (which physical harts);
   the first candidate's section signs became ASCII.
4. **The fast-forward `(a)`.** The same instruction carried it out: the
   development branch moved by fast-forward from `0096de3e` to
   `1fb46419` and was pushed with `beryllium/s3-mvp-plan`. The M0 plan
   branch's base is now the development tip, as the accepted MVP plan
   asks; the M0 plan commits themselves stay on their branch.

First candidate (2026-10-23), kept as history:

1. **Branch base.** The accepted MVP plan says M0's plan is written "on a
   new branch from the development branch". At the time the development
   branch (`0096de3e`) did not hold the accepted plan because `(a)` had
   not been directed, so the branch started from `1fb46419` and said so.
   Closed by revision 1's finding 4.
2. **Boot hart in QEMU.** Reading B3's shim showed that it parks every
   hart but 0, and the accepted R3 boot check requires hart 0. With eight
   QEMU harts the boot hart is not guaranteed to be 0 (an inference then;
   measured in revision 1). Resolved in the plan by the shim's start rule
   (Q2) and a QEMU-only `shim-rule` variant that exercises it
   deterministically, replacing an earlier draft's statistical runs.
3. **`hgeie`.** An earlier draft listed `hgeie` among CSRs never
   accessed; the accepted reset function writes and reads it. Corrected.
4. **Instruction-site wording.** An earlier draft guessed which code the
   three accepted `sret` sites belong to; the plan now carries B7's table
   as B7 states it.
5. **Ring full.** The design considered partial DBCN returns as
   back-pressure instead of failing closed; the accepted MVP plan fixes
   fail-closed, so the plan keeps it and sizes the ring with a recorded
   high-water mark and a stop. For your judgment: whether fail-closed is
   the behaviour you want for the console path, or whether a later MVP
   plan revision should allow back-pressure.
6. **Not resolved, for your judgment:** Q1 to Q13, most of all Q1 (the
   hart region), Q2 (the shim rule, and whether the better long-term
   boot contract should instead be planned now as an accepted-byte
   change), Q6 (eight board runs), and Q7 and Q8 (the evaluator and the
   lock's roles).

No research agent, separate scope review, or deep security review ran.

## 6. Validation and retained evidence

These ran on 2026-10-23 on the working tree immediately before each
commit; each commit records exactly that content. They did not run in a
fresh checkout.

| Command | Result | Covers |
| --- | --- | --- |
| `git diff --check` | pass, before each commit | whitespace in the changed tracked files |
| `grep -nP '[ \t]+$'`, `grep -nP '[^\x00-\x7F]'`, and a `grep` for absolute home, temporary, and session-folder prefixes on the plan | no matches at `4d129808` (the first candidate had section signs, replaced in revision 1) | whitespace, ASCII, private locators |
| An `awk` scan for prose lines longer than 80 characters in the plan, excluding table rows, quotes, status-record keys, marker lines, and the shell and tree listings | none | line wrapping |
| `node docs/check-links.mjs --tasking-fence-regression` | pass, 8 cases | the owner tasking section's regression cases |
| `node docs/check-links.mjs --tasking-contract` | pass | the owner tasking contract |
| `umask 0022 && npm run docs:source-check` | pass before each commit: self-tests `PASS`; at revision 2 `site_markdown=125`, `policy_markdown=5`, `rendered_references=1433`, `configured_routes=299`; isolation `PASS` with `network_events=0`, `generated_tree_changes=0`, `adversarial_cases=34` | the checker's self-tests; links, anchors, routes, private locators; the source gate under isolation |
| `git diff --stat 1fb46419 4d129808 -- model/ include/ virt/ arch/ bringup/ tests/` | empty | no code, model, bring-up, or test change |
| `build/mvp-research/hsm-ipi/run.sh` (scratch) | 8 of 8 eight-hart runs `PROBE DONE`; 1 single-hart run | the planning research 3 facts the plan cites; emulation only |
| `git merge-base --is-ancestor 0096de3e 1fb46419`; `git push origin beryllium/single-hart-runtime-r0 beryllium/s3-mvp-plan` | ancestor confirmed; `0096de3e..1fb46419` and a new remote branch; `git ls-remote` shows both at `1fb46419` | the `(a)` fast-forward and push |

No report, ledger, or hash is produced by a documentation-only package;
the commit is the artifact.

## 7. Recommended review sequence

Read-only commands, from the Beryllium checkout:

```sh
git show --stat 4d129808979cb54b7e0a7cc0b3e79d39533e0b9c
git show 4d129808979cb54b7e0a7cc0b3e79d39533e0b9c:planning/mvp-m0-plan.md
git diff 6e4b9d4a1e2da249d68aeb4e1aea5a27cf3755f8 4d129808979cb54b7e0a7cc0b3e79d39533e0b9c -- planning/mvp-m0-plan.md
```

The third command shows exactly what revisions 1 and 2 changed against
the first candidate.

1. **"Decision requested" and "Open questions":** what acceptance would
   and would not authorize; Q1 to Q13.
2. **"Hart identifiers":** the statement that hart IDs are configuration
   and the three reasons the control hart is fixed at 0; whether the
   better long-term boot contract should wait for the clean repository
   or be planned sooner as an accepted-byte change.
3. **"Architecture":** the hart region and its block layout; the boot
   sequence, the boot-hart and HSM measurements, and the shim rule; the domain
   hart entry, fast path, and resume checks; the control loop; the
   failure paths; the guest controls. Read against the accepted MVP
   plan's "Hart layout".
4. **"Budgets":** the symbol measurement and the Clang monitor-text
   inference, with the remedy the plan would propose if stop 3 fires.
5. **"Platform record: probes and negative images":** whether the probes
   record what M1 needs (`htval`, `htinst`, VMID tagging, IPI delivery,
   ordering, HSM state) and whether their stop conditions are right.
6. **"Markers" and "Tests and evidence":** the checker's floors, the
   image-checker profiles, the QEMU scenarios, and the evaluator.
7. **"Tool lock and the clean evaluator":** Q7 and Q8.
8. **"Work packages", "Stop conditions", "Board safety and procedure".**

To re-run the source checks on the exact commit, use a detached worktree
in the workspace's `worktrees/` container, then `npm ci` and
`umask 0022 && npm run docs:source-check` inside it:

```sh
git worktree add --detach ../worktrees/beryllium-hypervisor/review-4d129808 4d129808979cb54b7e0a7cc0b3e79d39533e0b9c
```

## 8. Human decision checklist

As presented, the packet asked the human to decide on `4d129808`. The
[decision record](#decision-record) above holds that decision; the
checklist is retained as presented.

- [ ] The plan stays within the accepted MVP plan's M0 and changes none
      of its decisions.
- [ ] The substrate design (control hart, hart region, HSM start, boot
      barrier, rings, IPIs, native `wfi`, no scheduler) is the first
      multi-hart step you want, with its costs carried as risks.
- [ ] "Hart identifiers" says what you meant: IDs are configuration, the
      control hart is fixed at 0 for the stated reasons, and the better
      boot contract waits for the clean-repository design (Q2).
- [ ] The probes record the facts M1 needs, and their stops are the right
      ones.
- [ ] The tight Clang text budget and its remedy path are acceptable.
- [ ] Fail-closed on a full ring is the behaviour you want for M0.
- [ ] Eight RAM-only board runs with human resets are acceptable (Q6).
- [ ] The defaults for Q1 to Q13 are acceptable, or you answer them.
- [ ] M0 implementation, every board run, M1, and any further push stay
      excluded until separately directed.
- [ ] Decision: accept `4d129808`, request revisions, or defer.

## 9. After the decision

- **Accept:** on your instruction, a follow-up records the acceptance of
  exactly `4d129808979cb54b7e0a7cc0b3e79d39533e0b9c` with the
  instruction, the date, and any answers to Q1 to Q13; M0 implementation
  may then start on a branch `beryllium/mvp-m0` from the acceptance
  record, as work packages M0-1 to M0-6, each stop condition returning
  to you. Nothing further is pushed unless you say so.
- **Request revisions:** a new commit and a new packet follow; this SHA is
  not treated as accepted, and `6e4b9d4a` and `d95b28e9` stay
  superseded.
- **Defer:** the current status stays, and M0 does not start.

**Status:** exact commit `4d129808`, revision 2 of the M0 plan, is
responsible-human accepted as of 2026-10-23 (`accept 4d129808, proceed
with implementation using opus-5.5 model`), on local branch
`beryllium/mvp-m0-plan`; nothing further is pushed. The first candidate
`6e4b9d4a` and revision 1 `d95b28e9` are superseded and were never
accepted. The development branch is at `1fb46419`, the S3 acceptance
record, locally and on `origin`.

**Next:** M0 implementation under the plan, work packages M0-1 to M0-6,
on branch `beryllium/mvp-m0` from the acceptance record, each stop
condition returning to you, ending in one result review packet.
Fast-forwarding the development branch to the acceptance record and any
push need their own instruction.

**Action required from you:** none for the M0 plan; the board campaign
(M0-5) will need your resets and your presence.
