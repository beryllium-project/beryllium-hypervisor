<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M1 plan review and acceptance record

This packet presents the exact commit that adds
[`mvp-m1-plan.md`](mvp-m1-plan.md), the bounded plan for M1, "The TE PoC
scenario on two Linux guests", the second milestone of the accepted
[MVP plan](mvp-plan.md). It also records the responsible human's decision
on it.

## Decision record

The responsible human accepted exact commit
`7b2c055c1587f9582812a575b296cd625746662b` (parent
`6f7b6e7c1fd609299fd88af164d400da3d6435ae`) as the M1 plan on
2026-10-26. The instruction, given in reply to this packet's request to
accept, revise, or defer that exact commit, was `accept 7b2c055c`,
checked to resolve uniquely (`git rev-parse --disambiguate=7b2c055c`).
Q1 to Q19 were not answered, so their defaults apply, including the two
departures section 1 named: the `k3ctl` remote reset (Q14) and the guest
kernel fragment change (Q2).

- **Scope:** acceptance covers exactly the plan text at that commit.
  Sections 2 to 8 are the packet as presented, apart from a note above
  the section 8 checklist. Section 1's status rows and the closing lines
  of section 9 now show the outcome. The decision itself is recorded
  only here and in the plan's own decision record.
- **Decision support:** packet commit
  `23a0bb1905e4dc83630d6d5c6e70cbc43ab2e4d6` and this acceptance-record
  follow-up are decision support, not plan content.
- **Authorized:** M1 implementation under the accepted plan, work
  packages M1-1 to M1-6, on branch `beryllium/mvp-m1` from this
  acceptance-record commit, ending in one result review packet; each of
  the plan's fourteen stop conditions returns M1 to the responsible
  human. The repository's model pin applies to the implementation unless
  the responsible human directs otherwise.
- **Not authorized:** M2, M3, or M4 deliverables; a Model change or the
  security model v1 revision; root integration; a merge into the
  development branch; any push beyond the 2026-10-26 push of
  `beryllium/mvp-m0` and the development branch; tag, publication, or
  release; any `k3ctl` command but `status`, the `ping` handshake, and
  `reset`.
- **Evidence status:** acceptance adds no implementation, emulation, or
  board evidence; nothing of M1 has been built or run.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `7b2c055c1587f9582812a575b296cd625746662b` (tree `7be73a218452d58115c5227c9190668a20c76835`), parent `6f7b6e7c1fd609299fd88af164d400da3d6435ae`, the M0 result acceptance record; branch `beryllium/mvp-m1-plan`, from that record |
| Current status | Documentation only: the bounded plan for M1, written under the accepted [MVP plan](mvp-plan.md) (`93967fba`, accepted 2026-10-23), whose M1 section it implements and whose rule "each milestone needs its own bounded plan and its own result acceptance" it follows; directed on 2026-10-26 by the instruction `proceed` and the form answers `m1-plan` and `k3ctl`, given after the M0 result's acceptance. The fast source checks pass. Responsible-human accepted on 2026-10-26 (instruction `accept 7b2c055c`; Q1 to Q19 at their defaults) |
| Decision requested | Accept the exact commit as the M1 plan, request revisions, or defer; answer any of its Q1 to Q19 or let the defaults apply. Recorded outcome: accepted, defaults applying |
| Successor status | M1 implementation (work packages M1-1 to M1-6) is authorized by the acceptance, on branch `beryllium/mvp-m1` from the acceptance record; nothing of it has started. M2 to M4 not started and not authorized |
| Publication status | Private repository; the target is on local branch `beryllium/mvp-m1-plan`, unpushed. `beryllium/mvp-m0` and the development branch `beryllium/single-hart-runtime-r0` are at `6f7b6e7c` locally and on the private `origin` (pushed 2026-10-26 on `proceed`, form answers `ff-dev` and `push`). No tag, publication, or release |

As presented, the packet asked the human to decide whether exact commit
`7b2c055c` is accepted as the M1 plan and whether any of Q1 to Q19 takes
other than its default, naming two departures for explicit attention
(section 3): the remote reset (Q14), which departs from the accepted MVP
plan's own scope text "with human resets", and the guest kernel fragment
change (Q2), which departs from M0's stop condition 5. The
[decision record](#decision-record) above holds that decision.

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| The M1 plan | [`mvp-m1-plan.md`](mvp-m1-plan.md) (1,476 lines) | Defines M1's goal and pass criterion (the MVP plan's M1 "Exit"); the base and inputs; security model v1's Instance 2 as the `te-poc` scenario's policy, labeling, need sets, and manifest, with the offline checker (A1 to A6 and A8; A7 vacuous) and the JSON authority report; one declared 4 KiB channel page (GPA `0x8400_0000`, HPA `0x1_1800_0000`) mapped read-write by the writer's root and read-only by the reader's through a level-0 page in each pool, with the walker's one new rule and the channel check that replaces B7's "refuses shared pages"; the denial path (an exact accepted entry for guest-page faults from VU mode; one injection helper with readback; one DENIAL record per denial, posted before the resume; `BE_MVP:DENY` lines; everything else terminal); the `nolibc` guest programs (writer and reader over a fenced protocol; three denied accesses observed through `SIGSEGV`/`SEGV_ACCERR`); the four negative images; markers; tests, mutations, QEMU, and the evaluator; the remote reset through `k3ctl`; budgets and the checker's size budget; departures; risks; the claim boundary; work packages M1-1 to M1-6; fourteen stop conditions; the board procedure; and Q1 to Q19 with defaults | A plan only: it authorizes, if accepted, M1 implementation within its text and nothing else; no code, model, board, push, or release change | Is the denial path's accepted entry exact enough, and does delivering a G-stage denial to the guest as an architectural access fault (with `vscause`, `vstval`, `vsepc`, `vsstatus`, and `vstvec` written by one helper) stay inside "enforcement derived from the specification" (M01-A) without a runtime policy decision? |
| Navigation | `planning/.vitepress/config.mts` | Lists the plan and this packet, and the M0 result record, which the overnight M0 packet had not added, in the three navigation lists | Site configuration only, in this packet's commit | None beyond placement |
| Status pages | [`roadmap.md`](roadmap.md), [`HANDOFF.md`](HANDOFF.md), [`README.md`](README.md), `.github/copilot-instructions.md` | Record the proposed plan | Changed in this packet's commit, not in the target; status text only | None |

Exact changed-file inventory:

```text
# git diff --name-status 6f7b6e7c 7b2c055c
A	planning/mvp-m1-plan.md
```

`git diff --stat 6f7b6e7c 7b2c055c -- . ':!planning/mvp-m1-plan.md'` is
empty: the target adds one file and changes nothing else.

## 3. Claim boundary

**The commit supports saying:** Beryllium has a proposed bounded plan for
M1 that implements exactly the accepted MVP plan's M1 deliverables 1 to 6
and its exit criterion, on the accepted M0 line at `b2669725`, with every
design choice justified from the accepted documents or marked as an
inference; and that the plan proposes, on the responsible human's
2026-10-26 form answer, wiring the `k3ctl` remote reset into the board
tools.

**Design decisions the plan takes, each with its alternative recorded
(the human may override any by answering the question):**

- **Channel geometry (Q1):** a level-0 page per root holding one 4 KiB
  leaf, rather than a 2 MiB shared leaf, because Instance 2 declares one
  page and a 2 MiB leaf would grant 512. The PTE values and page-table
  indices in the plan were recomputed by the orchestrating session and are
  exact; the HPA lies in System RAM with no `/proc/iomem` child or FDT
  reservation (M0's preflight).
- **Guest access (Q2):** `/dev/mem` through a two-option fragment
  (`CONFIG_DEVMEM=y`, `CONFIG_STRICT_DEVMEM=y`) merged after B6's unchanged
  fragment, so the guest stays unmodified upstream Linux and `/dev/mem`
  reaches only non-RAM addresses: the channel and the denied pages. This
  departs from M0's stop condition 5; the plan declares the change and
  makes any other `.config` difference a stop.
- **Delivery (Q5):** the corresponding access fault (`vscause` 1, 5, or
  7), not a page fault, because Linux would retry a page fault forever.
  Facts checked by the orchestrating session in the pinned `v7.2` source:
  `nolibc` has no `sigaction` (only `raise`), so the init calls
  `rt_sigaction` through `syscall()`; RISC-V returns from a handler
  through the vDSO's `rt_sigreturn`, which the guest kernel builds
  (`CONFIG_MMU=y`, `CONFIG_HAVE_GENERIC_VDSO=y`); a user-mode load or
  store access fault is delivered as `SIGSEGV` with `SEGV_ACCERR`
  (`arch/riscv/kernel/traps.c`).
- **No fetch denial in the scenario (Q3):** RISC-V Linux's
  `flush_icache_pte` writes the `struct page` of every executable PTE,
  and the guest kernel is `CONFIG_FLATMEM=y`, so an executable `/dev/mem`
  mapping of a non-RAM page would write outside `mem_map`; cause 20 is
  accepted and injected by the same path but host-tested only. This is
  the one place the plan does less than a literal reading of the MVP
  plan's "a G-stage fault on a page the guest's root does not map" might
  suggest; it says so.
- **Markers (Q6):** no M0 line changes format and the `MVPINIT` numbers
  keep their meaning, so M0's fixtures, including the board's stop-6
  capture that must fail on the alternation floor alone, stay valid.
- **SBI version (Q19):** 3, unchanged, because D8 ties the version to the
  SBI surface and a denial reaches the guest through its trap vector, not
  SBI. The alternative, 4, is recorded.
- **Remote reset (Q14):** opt-in (`K3_RESET=k3ctl`), `status` and `reset`
  only, after a passing run's anchored terminal marker with Fedora down,
  one reset per run, the client pinned by SHA-256
  (`7ca3d78a47de404b…`, equal to the file on `l1` at planning time), every
  reply recorded; `recovery`, `power`, `press`, `hold`, `release`, and
  `raw` never sent. The plan quotes the dongle README's own cautions
  ("abruptly restarts the K3 and can lose unsaved data"; "Do not issue
  board-control commands as unattended contribution checks"; startup
  transients unvalidated; "Start with confirmed ground and the reset line
  only"), which the orchestrating session verified against the README,
  and names the residual risk the human is asked to accept: a campaign
  proceeds between runs without a human at the board.

**Departures from accepted text that acceptance would adopt** (plan,
"Accepted decisions M1 departs from"): B7's pair check (now admits the
declared channel); M0's G-stage geometry (one level-0 page per root);
M0's "a guest-page fault is terminal" (the exact denial entry resumes);
M0's "no `vs*` write after arming" (one helper, with readback); M0's stop
condition 5 (the two-option fragment); and **the accepted MVP plan's
Scope** ("RAM-only loading through Linux kexec from hart 0 as in B7, with
human resets"; "The B-series board-safety rules stand unchanged") and
M0's "the human ... resets it after every run" (the tool resets after a
passing run under Q14). The plan changes no accepted document's text; it
records the departures for this decision, as M0's plan did for B7's. The
last departure is from the MVP plan's own scope rather than from a
predecessor's mechanism, which is why this packet names it in section 1.

**Trusted or assumed:** the accepted documents and the M0 result at their
exact commits; the pinned Linux `v7.2` source as read; the RISC-V
privileged specification as the plan reads it (named sections; the
reading is the plan's); the `k3ctl` README and client as read on
2026-10-26 (its repository's commit moved while the plan was written, so
the plan pins the client's SHA-256 rather than a commit); M0's platform
record for K3's `htval`, `htinst`, VMID, IPI, and ordering facts.

**Unavailable or `NOT RUN`:** everything M1 would build or run; the
plan's reading of the specification and of Linux is not yet exercised in
QEMU or on the board; `k3ctl`'s power sense (`k3=n/a`) is unwired; the
dongle's `FORCE_RECOVERY` and `SLEEP/WAKE` wiring is the human's choice
and the plan leaves it to them.

**Not implemented or selected by the plan:** M2's management extension,
measurement, or protected domain; a runtime TE check or capabilities (the
plan restates that neither trigger fires for Instance 2); a Model change
or the security model v1 revision (M3); root integration; a scheduler;
devices; dynamic management; any accepted-byte change; U-Boot automation;
firmware, environment, flash, or storage writes; push, tag, publication,
release. Board results, when they exist, will be diagnostic bring-up
evidence, never hardware validation or qualification; QEMU results
emulation; nothing a proof.

## 4. Load-bearing decisions

| Decision | Where in the plan | Why it bears load |
| --- | --- | --- |
| The denial is decided by a pure function from the exit record and the hart's own walked map, consulting no type, rule, or policy | "The denial path" | Keeps enforcement derived (M01-A) and both triggers unfired (security model v1, Part 5); stop condition 14 guards it |
| The accepted entry is exact: causes 20/21/23 from VU mode only, `htval` < 2^39, `htinst` zero or the transformed form, `vstvec` Direct or Vectored, and either an unmapped GPA or a store to the read-only channel leaf; everything else terminal | "The denial path", Q4 | The resume-with-log path is the first non-terminal fault handling in the line; its width is the attack surface it adds |
| One injection helper writes `vscause`, `vstval`, `vsepc`, `vsstatus` and reads each back; the DENIAL record is posted before the resume | "The denial path", "One executor, in order" | A DENY line implies both the readback and the record; the image checker's writer table pins the helper as the only `vs*` writer after arming |
| The walker accepts exactly one level-0 pointer and one leaf with `V U A R` (with or without `W D`, never `X`); the channel check, sharing no code with the builder, compares the leaf's rights with the declared rights | "G-stage and VMIDs" | B7's "refuses shared pages" becomes "admits exactly the declared channel"; the `reader-write` negative image shows the check catches a wrong builder |
| No `hgatp` write, fence, lock, or atomic after the barrier, the denial path included; each root on exactly one hart under exactly one VMID for the run | "G-stage and VMIDs", Q15 | The invariant that replaces S1 H12's stale-authority check on this layout; M0's `vmid-shared` finding needs no action because nothing switches |
| `/dev/mem` with `STRICT_DEVMEM`, both fragments required in the final `.config`, any other difference a stop | "Guest software", Q2 | Keeps the guest unmodified upstream Linux while giving the program a declared way to touch non-RAM GPAs |
| The remote reset: `status` then `reset`, only after a passing run's anchored terminal marker and an SSH probe that finds Fedora down; one per run; a timeout or any other reply is a stop; the port opened only while Fedora is down | "The remote reset", Q14, Q18, stop conditions 9 and 10 | The only automation that acts on the board outside kexec; bounded so that it can neither cut a run short nor loop |
| Checker size budget: `policy-check.py` at most 900 lines; the line's checking code at most 2.2 lines per monitor line | Budgets, stop condition 13 | S1 H43; M0 ended at 1.80 |

## 5. Review history and resolved findings

The plan was drafted by a `claude-opus-5.5` sub-agent from a brief that
named the governing documents, the design options to weigh, and the new
facts (the M0 acceptance, the branch state, `k3ctl`); the orchestrating
session (`claude-fable-5.1`, at the responsible human's direction for this
session) reviewed it section by section against the governing documents,
the M0 code, the pinned Linux source, and the `k3ctl` bundle. Findings:

| Finding | Resolution |
| --- | --- |
| The brief suggested a fetch denial in the scenario | The agent found `flush_icache_pte` on a FLATMEM kernel makes an executable non-RAM mapping unsafe; the plan removes the fetch from the scenario, keeps cause 20 in the accepted entry, host-tests it, and says so (Q3) |
| The brief assumed `nolibc` had `sigaction` and spoke of `SIGBUS` | The pinned `v7.2` `nolibc` has only `raise`; access faults arrive as `SIGSEGV` with `SEGV_ACCERR` and `si_addr` = the faulting PC; the plan uses raw `rt_sigaction`, matches `si_addr` to the logged `sepc`, and names the vDSO return path. The orchestrating session confirmed each in the source |
| The brief said `k3ctl` is "not a lock role, like `ssh`" | `ssh` and `scp` are host-only lock roles; the plan instead pins the client by SHA-256 and records the dongle's version string, since lock roles are RPM-owned executables |
| The brief suggested a reset after the tool's own timeout | Rejected: Fedora may still be running if the kexec never happened; the plan resets only after a passing run's terminal marker and an SSH probe finds Fedora down |
| The brief described `FORCE_RECOVERY` and `SLEEP/WAKE` as wired | The dongle README advises wiring ground and reset only until the other lines have an attended test; the plan records this as the human's choice and requires `fcrec=0` before any reset |
| The brief's Model 0.2 quote came from the instructions file | The plan quotes Model 0.2's own text ("encoding-independent"; no "stable manifest encoding") |
| The `k3ctl` repository's commit changed during drafting | The plan pins the client's SHA-256 (`7ca3d78a…`), which the orchestrating session confirmed equals the file on `l1` |
| The vector does not capture `vsstatus` | The exit record gains it (offset 352), listed in the CSR inventory and stop condition 4 |
| The PTE values and indices (Q1) | Recomputed by the orchestrating session: `0x460000d7`, `0x46000053`, `0x4080e401`, `0x40810401`; root index 2, level-1 index 32, level-0 index 0; the window's last leaf is index 31 |
| The M0 result record was missing from the VitePress navigation | Added in this packet's commit with the M1 entries |

Checks run on the target: whitespace clean; every relative link and
in-file and cross-file anchor resolves; no retired name or home path; the
seven lines over 80 columns are in code and status blocks, as in the M0
plan; every 40-hex value is a commit in this repository or one of the
four external pins the lock records (Linux commit and tag object, OpenSBI
commit) or the `k3ctl` client's SHA-256.

**Open for human judgment:** Q1 to Q19 (each with a default); the two
departures named in section 1; whether `k3ctl`'s other lines are wired.

## 6. Validation and retained evidence

Documentation only. The fast source checks of section 5 passed on the
exact target. No build, QEMU run, evaluator run, or board run belongs to
this commit; the M0 gates passed at `13992d6d` and are recorded in the
[M0 result review and acceptance record](mvp-m0-result-review-summary.md).
No VitePress build or Chromium check was run, per the documentation
policy for wording and status changes; the navigation change is three
list entries in the existing form.

## 7. Recommended review sequence

```sh
git worktree add --detach /tmp/be-m1-plan-review 7b2c055c1587f9582812a575b296cd625746662b
cd /tmp/be-m1-plan-review
git --no-pager diff --name-status 6f7b6e7c HEAD      # one file added
```

1. **Decision requested and open questions** (15 min): what acceptance
   authorizes and does not; Q1 to Q19; decide which defaults you want to
   override, Q2 and Q14 first.
2. **The denial path** (20 min): the accepted entry, the injected values,
   the specification reading, the Linux facts, "One executor, in order",
   the DENIAL record; against the MVP plan's M1 deliverable 3 and security
   model v1 Part 5.
3. **G-stage and VMIDs, and Guest software** (20 min): the channel
   geometry and the channel check; `/dev/mem`; the init's roles, the
   signal handler, and "No fetch".
4. **The remote reset** (15 min): "Board safety and procedure" and "The
   remote reset", with the departures table's row 6 and stop conditions 9
   and 10; the dongle README on `l1`.
5. **Scenarios and the harness, Markers, Tests and evidence, Work
   packages, Stop conditions** (20 min).
6. **Claim boundary** (10 min): what M1 would and would not show.

```sh
cd - && git worktree remove /tmp/be-m1-plan-review
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The plan implements the accepted MVP plan's M1 deliverables 1 to 6
      and its exit criterion, and nothing of M2 to M4.
- [ ] The denial path stays within M01-A: a pure decision from the
      installed root and the sealed record, no policy consulted at run
      time, neither trigger fired.
- [ ] The accepted-exit entry is as narrow as the scenario needs.
- [ ] The guest kernel fragment change (Q2) is acceptable, with the
      `.config` delta check and stop condition 5 as its bound.
- [ ] The remote reset (Q14) is acceptable as a departure from the
      accepted MVP plan's "with human resets", with its bounds: `status`
      and `reset` only, after a passing run's terminal marker with Fedora
      down, one per run, every other outcome a stop; and you accept that
      a campaign then proceeds between runs without a human at the board.
- [ ] The defaults of Q1 to Q19 stand, or you name the answers you want.
- [ ] Successor work stays excluded: M2's plan, a Model change, the
      security model v1 revision, root integration, a merge into the
      development branch, any push.
- [ ] Decision: accept exact commit `7b2c055c` as the M1 plan; request
      revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `7b2c055c1587f9582812a575b296cd625746662b` and the date, and
  name any answers to Q1 to Q19; the acceptance record names that SHA.
  Acceptance authorizes M1 implementation, work packages M1-1 to M1-6, on
  branch `beryllium/mvp-m1` from the acceptance record, under the model
  pin unless you direct otherwise, and nothing else; each stop condition
  returns M1 to you, and M1 ends in one result review packet.
- **Request revisions:** a new commit and a new packet follow; `7b2c055c`
  is not treated as accepted.
- **Defer:** the status stays as presented; M1 stays unstarted.

**Status:** exact commit `7b2c055c1587f9582812a575b296cd625746662b` is
responsible-human accepted as the M1 plan as of 2026-10-26 (instruction
`accept 7b2c055c`), with Q1 to Q19 at their defaults; M1 implementation
is authorized on branch `beryllium/mvp-m1` from this acceptance record
and has not started. The plan branch is local and unpushed.

**Next:** M1 implementation, work packages M1-1 to M1-6, under the
accepted plan; each stop condition returns to you; one result review
packet follows M1-6.

**Action required from you:** none for the plan. Direct the start of
implementation (and the model to use, if other than the pin) when you
choose.
