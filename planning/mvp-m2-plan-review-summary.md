<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M2 plan review and acceptance record

This packet presents the exact commit that adds
[`mvp-m2-plan.md`](mvp-m2-plan.md), the bounded plan for M2, "A protected
research domain beside an untrusted Linux", the third milestone of the
accepted [MVP plan](mvp-plan.md) and its anchor use case. It also records
the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`854a54152502c4c9a14fe2d1897d907a358a8251` (parent
`ccf70a3d3e9ab716ba52e055ccc7882179b50d04`) as the M2 plan on
2026-10-27. The instruction, given in reply to this packet's request to
accept, revise, or defer that exact commit, was `accept 854a5415 , gpl
2.0 only ok`, checked to resolve uniquely
(`git rev-parse --disambiguate=854a5415`). Q20 was answered: the guest
module's one file is `GPL-2.0-only`, the flagged default, which also
takes Q2's default, the module; Q1 to Q19 were not answered, so their
defaults apply.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Sections 2 to 8 are the packet as presented, apart from a note above
  the section 8 checklist. Section 1's status rows and the closing lines
  of section 9 now show the outcome. The decision itself is recorded
  only here and in the plan's own decision record.
- **Decision support:** packet commit
  `c5467e00a4a4a5ce74dbee155973d0fdeed9822b` and this acceptance-record
  follow-up are decision support, not plan content.
- **Authorized:** M2 implementation under the accepted plan, work
  packages M2-1 to M2-7, on branch `beryllium/mvp-m2` from this
  acceptance-record commit, ending in one result review packet; each of
  the plan's fourteen stop conditions returns M2 to the responsible
  human; board access only after the responsible human's confirmation
  that the shared board is free. The repository's model split applies
  to the implementation unless the responsible human directs otherwise.
- **Not authorized:** M3 or M4 deliverables; a Model change or the
  security model v1 revision; root integration; a merge into the
  development branch; any push of `beryllium/mvp-m2-plan` or
  `beryllium/mvp-m2`; tag, publication, or release; any successor.
- **Evidence status:** acceptance adds no implementation, emulation, or
  board evidence; nothing of M2 had been built or run at the accepted
  commit.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | `854a54152502c4c9a14fe2d1897d907a358a8251` (tree `a26d5a302f6978bc9f1060010545967fdd450209`), parent `ccf70a3d3e9ab716ba52e055ccc7882179b50d04`, the development branch's tip after the M1 acceptance record; branch `beryllium/mvp-m2-plan`, from that tip |
| Current status | Documentation only: the bounded plan for M2, written under the accepted MVP plan (`93967fba`), whose M2 section it implements and whose rule "each milestone needs its own bounded plan and its own result acceptance" it follows; directed on 2026-10-27 by the instruction `approve ff84533c and revisions, accept your recommendations, authorize proceeding per those`, which accepted the recommendation to direct this plan. The fast source checks pass (whitespace, every link and anchor). Responsible-human accepted on 2026-10-27 (instruction `accept 854a5415 , gpl 2.0 only ok`; Q20 answered as its default, Q1 to Q19 at their defaults) |
| Decision requested | Accept the exact commit as the M2 plan, request revisions, or defer; answer any of its Q1 to Q20 or let the defaults apply. Two defaults are flagged for explicit attention in section 3: the guest module (Q2) and its `GPL-2.0-only` license (Q20). Recorded outcome: accepted; Q20 answered `gpl 2.0 only ok`; the other defaults apply |
| Successor status | M2 implementation (work packages M2-1 to M2-7) is authorized by the acceptance, on branch `beryllium/mvp-m2` from the acceptance record; nothing of it had started at the accepted commit. M3 and M4 not started and not authorized |
| Publication status | Private repository; the target is on local branch `beryllium/mvp-m2-plan`, unpushed. `beryllium/mvp-m1` and the development branch `beryllium/single-hart-runtime-r0` are at `ccf70a3d` locally and on the private `origin` (pushed 2026-10-27). No tag, publication, or release |

## 2. Deliverables

| Deliverable | Path | Purpose | Boundary | Most important review question |
| --- | --- | --- | --- | --- |
| The M2 plan | [`mvp-m2-plan.md`](mvp-m2-plan.md) (785 lines) | Defines M2's goal and pass criterion (the MVP plan's M2 "Exit"); the base and inputs with their facts; Instance 3 in security model v1's notation (`host_t`, `prot_t`, the request, response, and secret pages, the first `domain` rule held by a domain) as the `anchor` scenario's policy, labeling, need sets, manifest, and management grants, with the offline checker's `domain` class and A3 extension; three leaves per root in M1's level-0 pages, with exact PTEs; the management extension (EID `0x0800_4245`, `pause` and `terminate`, result codes, synchronous wait with M1-B's progress window, hart 0's pure decision, IPI delivery, the paused and terminated states, no resume); the SHA-256 in restricted C and the core-held measurement, compared with a baked expected value and recomputed by the checker; the triggers evaluated for Instance 3; the sealed-state obligation stated with its mechanical part checked; the guest module, the init's roles, the HMAC, and the kernel fragment's `CONFIG_MODULES=y`; six negative images; markers; tests and evidence; departures; risks; the claim boundary; work packages M2-1 to M2-7; fourteen stop conditions; the board procedure under the shared-board gate and the remote reset; and Q1 to Q20 with defaults | A plan only: it authorizes, if accepted, M2 implementation within its text and nothing else; no code, model, board, push, or release change | Does the management path keep "enforcement derived from the specification" (M01-A): a static grant in the sealed manifest, checked offline by A8, consulted by hart 0 as derived authority, with no type, label, or `decide` in HS, and does the plan's trigger evaluation hold? |
| Navigation | `planning/.vitepress/config.mts` | Lists the plan and this packet in the three navigation lists | Site configuration only, in this packet's commit | None beyond placement |
| Status pages | [`roadmap.md`](roadmap.md), [`HANDOFF.md`](HANDOFF.md), [`README.md`](README.md), `.github/copilot-instructions.md` | Record the proposed plan | Changed in this packet's commit, not in the target; status text only | None |

Exact changed-file inventory:

```text
# git diff --name-status ccf70a3d 854a5415
A	planning/mvp-m2-plan.md
```

`git diff --stat ccf70a3d 854a5415 -- . ':!planning/mvp-m2-plan.md'` is
empty: the target adds one file and changes nothing else.

## 3. Claim boundary

**The commit supports saying:** Beryllium has a proposed bounded plan for
M2 that implements the accepted MVP plan's M2 deliverables 1 to 5 and its
exit criterion on the accepted M1 line at `ff84533c`, with every design
choice justified from the accepted documents, a source fact, or marked as
an inference, and with the two questions the MVP plan left to M2's plan
answered: whether resuming a paused domain maps onto `enter` (no, Q4),
and whether either trigger fires for the use case (neither, Q18).

**Two defaults flagged for explicit attention:**

- **The guest module (Q2).** The untrusted domain makes its management
  calls through one out-of-tree kernel module of ours, built against the
  pinned unmodified `v7.2` tree and loaded by the init, because an
  unmodified kernel issues no custom SBI call on userspace's behalf and
  the MVP plan's extension is an SBI extension (D8). The kernel tree is
  not modified; the fragment gains `CONFIG_MODULES=y`, a departure from
  "an unmodified kernel with an in-tree init" that the plan records. The
  alternative, VU-mode `ecall` interposition on the untrusted domain's
  hart, avoids any kernel-linked code but puts the monitor in every
  system call of that domain and makes its exit count timing-dependent;
  the plan does not take it.
- **The module's license (Q20).** The one module file would be
  `GPL-2.0-only`, because it is linked at run time into the GPL-2.0-only
  guest kernel and calls its exported `__sbi_ecall`; a GPL-3.0-only module
  would be license-incompatible with that kernel. This is a departure from
  the repository's GPL-3.0-only header rule for one test-input file that
  never enters the Beryllium image and is never submitted anywhere. If
  the responsible human declines the exception, Q2's alternative is the
  path without it.

**Design decisions the plan takes, each with its alternative recorded:**

- **Pages (Q1):** three 4 KiB pages above the windows, in M1's level-0
  pages, with exact PTEs (`0x460000d7`, `0x46000453`, `0x46000053`,
  `0x460004d7`, `0x46000853`); the MVP-owned extent grows from one page
  to three. The PTE values were recomputed by the orchestrating session
  from M1's: PPN `0x118000`, `0x118001`, `0x118002` shifted by 10, with
  the flag sets M1 used.
- **The secret (Q5):** a fixed test secret placed by hart 0 into a page
  only the protected root maps; public in the source, with confidentiality
  demonstrated by the denials and by a result that depends on it.
- **The computation (Q6) and the measurement (Q7):** HMAC-SHA-256 and
  SHA-256 over the protected domain's placed image and the configuration
  identity, one restricted-C SHA-256 shared by the monitor and the guest
  program, host-tested against the standard vectors; the checker
  recomputes both with Python's standard library.
- **Pause and terminate (Q4, Q14, Q15):** synchronous from the guest's
  view, decided only by hart 0, delivered by IPI, the target hart parked
  in HS with its state saved; no resume; a terminated domain counts as
  ended, a paused one does not.
- **Negatives (Q10):** two build-time, three fail-closed at boot, one
  (`no-grant-check`) ending in `run-timeout` under a 2^27-tick variant
  budget, so that no negative hangs for the full run budget.
- **Markers (Q13):** no M0 or M1 line changes format; every retained
  fixture keeps its verdict.
- **Budgets (Q17):** the checking ratio's bound rises from 2.2 to 2.3
  with the plan's justification, since M1 measured 2.143.

**Facts the plan relies on, each checked by the orchestrating session:**
`__sbi_ecall` is exported (`arch/riscv/kernel/sbi_ecall.c:48@v7.2`); the
SBI error codes used exist in `arch/riscv/include/asm/sbi.h:546-558@v7.2`;
`misc.o` is always built and `misc_register` honours a requested free
minor (`drivers/char/misc.c@v7.2`); M1's guest `.config` has `MODULES`,
`PROC_FS`, `SYSFS`, and `DEVTMPFS` unset; M1's board record shows the
IPIs, the denials, and the channel working on the COM260; M1-B's lesson
on console latency.

**Acceptance would not support saying:** that any of M2 exists, builds,
or runs; that a protected domain has been isolated on K3; that the
measurement is attestation; that the sealed state is protected inside HS
beyond the stated obligation; that any runtime policy mechanism is
selected; or anything about M3, M4, publication, or release.

## 4. Load-bearing decisions

| Decision | Where | Why it matters | Alternative recorded |
| --- | --- | --- | --- |
| Management grants are static manifest records, validated by A8, consulted by hart 0 as derived authority | Q14, Q18, "The triggers for Instance 3" | Keeps enforcement derived from the specification; neither trigger fires | A per-request TE `decide` in HS, which the plan rejects |
| Only hart 0 decides; a domain hart never decides | "The management extension" | One serialized control path, as the MVP plan's layout requires | A local denial on the requester's hart, rejected |
| The call is synchronous and one request is outstanding per domain | Q14 | A burst costs only the caller; the ring is bounded | A queue of requests, rejected |
| The wait measures hart 0's progress | Q14, M1-B | The console backlog cannot be mistaken for a wedged hart 0 | A fixed window, which M1-B retired |
| No resume | Q4 | The MVP plan grants `host_t` only `pause` and `terminate` | `enter` and a `resume` FID |
| The measurement is compared with a baked value and recomputed by the checker | Q7 | Fails closed on a wrong payload; a generator defect cannot make the two agree | Logging without comparison |
| The module, under its own license | Q2, Q20 | The only path to an SBI call from an unmodified kernel | VU-mode interposition |

## 5. Review history and resolved findings

| Finding | Resolution |
| --- | --- |
| The MVP plan's M2 text imagines the management call as an SBI extension but the guest kernel is unmodified upstream Linux, which issues no custom SBI call for userspace | Q2: one out-of-tree module of ours; Q20: its license; the alternative recorded |
| A negative image whose declared outcome depends on a domain that never ends would hang for the run budget (2^32 ticks, 179 s on K3, 429 s in QEMU) | `no-grant-check` carries a 2^27-tick variant budget; the other negatives fail closed at boot or offline |
| A policy-denied management call from the host, wrongly allowed, can only harm the host itself (two domains) | The `no-grant-check` shape uses the protected domain's unauthorized `terminate 0`, which the variant delivers; the host's own unauthorized calls come after its requests |
| The checking ratio reached 2.143 against M1's 2.2 | Q17 raises the bound to 2.3 with the reasons; stop condition 13 |
| M1's accepted plan omitted the `SCENARIO=` selector in its board commands (open item 44) | The M2 procedure names `SCENARIO=anchor` and the variants |
| The shared board | Every board access, the preflight included, waits for the responsible human's confirmation (Q11; stop condition 9) |

**Not run by SOP:** no iterative-evaluation review with a different
model, no separate scope review, and no deep security review. The plan
was written by the orchestrating session on `claude-fable-5.1`, as the
repository's model split of 2026-10-27 assigns planning; no coding
sub-agent ran.

## 6. Validation and retained evidence

Documentation only. Checked at the target: `git diff --check` clean;
every relative link in the plan names an existing file and every anchor
an existing heading (a script over the Markdown); the target adds one
file (`git diff --name-status ccf70a3d 854a5415`); the kernel facts above
were read in the pinned tree at `v7.2`; the PTE values were recomputed.
No VitePress build was run (a wording and navigation change under the
routine-documentation rule).

## 7. Recommended review sequence

```sh
git worktree add --detach /tmp/be-m2-plan-review 854a54152502c4c9a14fe2d1897d907a358a8251
cd /tmp/be-m2-plan-review
git --no-pager diff --name-status ccf70a3d HEAD     # A planning/mvp-m2-plan.md only
```

1. **Scope against the MVP plan** (20 min): `planning/mvp-plan.md`, "M2"
   and "Hart layout"; then the plan's "Decision requested" and "Goal and
   pass criterion".
2. **The two flagged defaults** (15 min): Q2 and Q20 with "Guest
   software"; decide whether the module and its license are acceptable or
   whether the alternative is preferred.
3. **The policy and the triggers** (20 min): "The policy, the labeling,
   and the manifest" against security model v1 Parts 2, 3, and 5; "The
   triggers for Instance 3".
4. **The mechanism** (30 min): "The management extension", "The
   measurement" with the obligation paragraph, "G-stage and VMIDs", Q14,
   Q15.
5. **The rest of the open questions, the negatives, the stops, and the
   board procedure** (20 min).

```sh
cd - && git worktree remove /tmp/be-m2-plan-review
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The plan implements the MVP plan's M2 deliverables 1 to 5 and its
      exit, and nothing beyond MVP 1.0's scope.
- [ ] The two flagged defaults are acceptable: the guest module (Q2) and
      its `GPL-2.0-only` license (Q20); or the alternative is chosen.
- [ ] The management path keeps enforcement derived from the
      specification, and the trigger evaluation (Q18) holds.
- [ ] The measurement's definition (Q7) and the stated, unclosed
      sealed-state obligation are acceptable.
- [ ] The negatives, the stop conditions, the budgets (Q17), and the
      board procedure under the shared-board gate are acceptable.
- [ ] Any of Q1 to Q20 to answer other than by its default.
- [ ] Decision: accept exact commit `854a5415` as the M2 plan; request
      revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `854a54152502c4c9a14fe2d1897d907a358a8251` and the date, with
  your answers to any open questions. The acceptance record names that
  SHA; M2 implementation then proceeds on `beryllium/mvp-m2` from the
  acceptance record, work packages M2-1 to M2-7, each stop condition
  returning to you, ending in one result review packet.
- **Request revisions:** a new commit and a new packet follow;
  `854a5415` is not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commit `854a54152502c4c9a14fe2d1897d907a358a8251` is
responsible-human accepted as the M2 plan as of 2026-10-27 (instruction
`accept 854a5415 , gpl 2.0 only ok`), Q20 answered as its default and
Q1 to Q19 at their defaults. It is on local branch
`beryllium/mvp-m2-plan`, unpushed; M2 implementation is authorized on
`beryllium/mvp-m2` from this acceptance record.

**Next:** M2 implementation, work packages M2-1 to M2-7; the board
campaign (M2-6) waits for your confirmation that the shared board is
free.

**Action required from you:** none for the plan. Confirm the board when
M2-6 is reached; each stop condition returns M2 to you.
