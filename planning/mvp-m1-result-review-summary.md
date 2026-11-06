<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M1 result review and acceptance record

This packet presents the result of M1, the second milestone of the accepted
[MVP plan](mvp-plan.md): security model v1's Instance 2 as the `te-poc`
scenario on two Linux guests, each on its own hart, with one declared
4 KiB channel between them, three declared denials logged, injected, and
observed by the guests, an offline policy checker with its authority
report, four negative images, and the remote reset in the board tools. It
was implemented and run under the accepted [M1 plan](mvp-m1-plan.md),
whose [decision record](mvp-m1-plan.md#decision-record) holds its
authorization, and under the plan's two revisions M1-A and M1-B, each
directed by the responsible human during implementation and each
presented here for exact-commit acceptance with the result, as the plan
requires. It also records the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`ff84533cb3c13d89063be77652575347c2a82757` (parent
`17ed82f7217c82328bb6027c294acfd71e73826f`) as the M1 result on
2026-10-27, with Plan revisions M1-A (`00051fc4`) and M1-B (`745c293a`,
implemented at `804cd24c`) as implemented. The instruction, given in
reply to this packet's request to accept, revise, or defer that exact
commit and to a summary of the open decisions with recommendations, was
`approve ff84533c and revisions, accept your recommendations, authorize
proceeding per those`. The abbreviation `ff84533c` was checked to resolve
uniquely to that commit (`git rev-parse --disambiguate=ff84533c`).

- **Scope:** acceptance covers exactly that commit and the claim boundary
  in section 3. Sections 2 to 8 are the packet as presented, apart from a
  note above the section 8 checklist. Section 1's status rows and the
  closing lines of section 9 now show the outcome. The decision itself is
  recorded only here.
- **Decision support:** packet commit
  `5aee883d82b0e34e66beb3ca53ca8f8ad1958b9a`, the backup-push record
  `c71a1bed`, and this acceptance-record follow-up are decision support,
  not implementation.
- **Recommendations accepted with the result** (the same instruction),
  each a separate action after this record and none a change to the
  accepted commit: fast-forwarding the development branch
  `beryllium/single-hart-runtime-r0` to the commit that records this
  acceptance and pushing it to the private `origin`; directing the M2
  plan, a bounded plan on a new branch from that record; formalizing in
  `.github/copilot-instructions.md` the model split these sessions ran
  under (planning, orchestration, and review on `claude-fable-5.1`;
  coding on `claude-opus-5.5` at `max` with the `long_context` tier), as
  its own commit; deleting the stale rootless podman store moved aside on
  `l1` (`mvp/README.md` open item 43); keeping the shared-K3
  confirmation gate; and leaving the three unplanned `two-guests` runs
  set aside, not evidence (open item 45).
- **Erratum noted, plan text unchanged** (open item 44): the accepted M1
  plan's [board procedure](mvp-m1-plan.md#board-safety-and-procedure)
  lists `./mvp k3-campaign TOOLCHAIN=gcc RUNS=3` and `TOOLCHAIN=clang
  RUNS=1` for the `te-poc` runs; since M1-5 added the `SCENARIO=`
  selector those commands need `SCENARIO=te-poc`, as `mvp/README.md`'s
  Commands show (`VARIANT=reader-write` and `VARIANT=no-inject` select
  `te-poc` by themselves). The accepted plan text is not edited.
- **Successor:** acceptance itself starts no successor; the M2 plan is
  directed by the same instruction's acceptance of the recommendations
  and is a proposal until its own exact commit is accepted. Each of
  these still needs its own decision: M2 implementation; M3 (the policy
  layer and the hart binding in the model, with the planned additive
  security model v1 revision) and any Model change; root
  `Makefile`/`be`/`scripts/check-be.sh` integration;
  development-kernel/BSP selection.
- **Evidence status:** the board runs are diagnostic bring-up evidence for
  one board, firmware, and Fedora kernel. Acceptance adds no hardware
  validation, no qualification, and no formal-verification claim, and
  makes no security claim: the three denials are the plan's declared
  denials on one declared channel, and isolation beyond that channel
  remains by construction only. It does not tag, publish, or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `ff84533cb3c13d89063be77652575347c2a82757` (parent `17ed82f7`), branch `beryllium/mvp-m1`. Comparison base: the M1 plan acceptance record `41f88795`, over accepted plan `7b2c055c` on the M0 acceptance record `6f7b6e7c`. Two commits form the result: `17ed82f7` holds the whole `mvp/` tree with its README, and `ff84533c` adds the board record made against `17ed82f7` from a clean tree. |
| Current status | Implemented, checked in QEMU and in the clean evaluator, and run on the board. In the second board campaign (2026-10-27), with `17ed82f7`'s images, both Linux domains booted on harts 1 and 2 and ran to power-off in 4 of 4 RAM-only COM260 `te-poc` runs through Linux kexec (three GCC, one Clang), with identical counts in every run; the writer's channel pattern was read by the reader at its first poll; the three declared denials were logged, injected, and observed by the guests' children in every run; `reader-write` and `no-inject` failed as declared; each run was followed by one `k3ctl` reset and none by hand. No stop condition applied in the second campaign. At exact commit `17ed82f7`, from a clean tree on `l1`, `./mvp/mvp check`, `./mvp/mvp evaluate` (184 images identical between host and evaluator), `./mvp/mvp kexec-rehearsal`, and `kernel-repro` pass. Responsible-human accepted on 2026-10-27 (instruction `approve ff84533c and revisions, accept your recommendations, authorize proceeding per those`). |
| Decision requested | Accept exact commit `ff84533c` as the M1 result, which also accepts Plan revisions M1-A (`00051fc4`) and M1-B (`745c293a`, implemented at `804cd24c`) as implemented; or request revisions; or defer. Recorded outcome: accepted. |
| Successor status | As presented: not started and not authorized: M2 (a static protected research domain beside an untrusted Linux), any merge into the development branch, the planned additive security model v1 revision and any Model change (M3), root `Makefile`/`be`/`scripts/check-be.sh` integration, and development-kernel/BSP selection. After the decision: the M2 plan is directed (a proposal, not an authorization of M2 implementation) and the development-branch fast-forward is authorized; see the [decision record](#decision-record). |
| Publication status | Private repository. As presented, `beryllium/mvp-m1` was local and unpushed, as were `beryllium/mvp-m1-plan` (`41f88795`) and this packet; on `push current work` (2026-10-27) both branches were pushed to the private `origin` as a backup (`c71a1bed`). The development branch `beryllium/single-hart-runtime-r0` was at `6f7b6e7c` locally and on `origin`. No tag, publication, or release. |

## 2. Deliverables

M1 was authorized by the acceptance of exact plan commit `7b2c055c` on
2026-10-26 (instruction `accept 7b2c055c`, open questions Q1 to Q19 at
their defaults), as work packages M1-1 to M1-6 under `mvp/` on branch
`beryllium/mvp-m1` from the acceptance record `41f88795`, on the
instruction `start implementation with existing pin`. Thirteen
commits follow that record to `ff84533c`: nine under `mvp/` and
four under `planning/` (the two plan revisions, the stop
records, and the handoff). Nothing outside `mvp/`, `planning/`, and
`.github/copilot-instructions.md` changed; no accepted R0-R7 or B0-B7
byte, retained R8 input, M0 result file, or root file was touched
(`git diff --stat 41f88795 ff84533c -- . ':!mvp' ':!planning'
':!.github'` is empty, and `mvp/results/20261025-com260/` is unchanged).

| Deliverable | Paths | Purpose | Trust or privilege boundary | Review question |
| --- | --- | --- | --- | --- |
| The policy, the scenario, and the offline checker (M1-1) | `mvp/scenarios/te-poc/{scenario.json,policy.te,negatives/}`, `mvp/tools/policy-check.py` (890 lines), `mvp/tools/gen-scenario.py` (v2), `mvp/tools/gen-dts.py`, `mvp/Makefile` `policy-negatives` | Security model v1's Instance 2 verbatim as `policy.te`; the v2 scenario with the labeling, the need set, the channel, the accepted-exit entry, the guest roles, and the expected denials; A1 to A6 and A8 run offline on every build (A7 vacuous for a fixed binding), 33 self-test cases, 7 mutations; the JSON authority report (6 grants, 1 declared flow, configuration identity `9cf02807…`); `undeclared-flow` and `grant-without-rule` stop the build and never produce an image | Host-only; the sealed manifest is derived from the scenario and validated against the policy (security model v1's validate-not-compile decision) | Is Instance 2 transcribed exactly, and does each of A1-A8 check what security model v1 defines? |
| The channel in the G-stage (M1-2) | `mvp/src/mvp-layout.h`, `mvp/src/mvp-gstage.{h,c}`, `mvp/tests/gstage-test.c` (37 scenarios, 33,475 assertions) | One level-0 page per root (`0x102039000`, `0x102041000`) mapping GPA `0x84000000` to HPA `0x118000000`: writer PTE `0x460000d7` (RW), reader `0x46000053` (R); hart 0's walk of both leaves at boot (`BE_MVP:03 CHANNEL_CHECKED`), refusing a leaf other than the declared one (`reader-write`: `BE_MVP:FAIL gstage`) | The roots are built and re-walked before any domain hart starts; `two-guests` is byte-for-byte unchanged | Does the channel check compare the walked leaf with the declared one for both roots before the barrier, and is the `two-guests` build unchanged? |
| The denial path (M1-3) | `mvp/src/mvp.h`, `mvp/src/mvp-sbi.c` (`be_mvp_denial_decide`), `mvp/src/mvp-trap.S` (`be_mvp_arch_inject`), `mvp/src/mvp-hartmain.c`, `mvp/src/mvp-hart.{h,c}`, `mvp/src/mvp-runtime.c`, `mvp/tests/deny-test.c` (30 scenarios, 2,357 assertions), `mvp/tests/check-image.py` (97 and 100 rejected mutations) | A guest-page fault is accepted only from VU mode (`hstatus.SPVP=0`) at a declared denial's GPA and kind, in an image whose accepted-exit set holds `denial`; it is logged as a 12-word DENIAL record and hart 0's `BE_MVP:DENY` line, the corresponding access fault is injected (`vscause` 1, 5, or 7, `vstval`, `vsepc`, `vsstatus` SPP/SPIE/SIE, resume at the `vstvec` base) with readback, and the guest resumes; every other guest-page fault stays terminal (`no-inject`: `BE_MVP:FAIL guest-page-fault`); `exits = sbi + ipi + denials` | The only new privileged step is the injection helper; the decision is a pure function; the image checker's rules pin the helper's CSR writes and the entry's VU-only condition | Does the decision admit exactly the declared denials from VU mode and nothing else, and does the injection write exactly the values the plan names? |
| The guests (M1-4, Plan revision M1-A) | `mvp/guest/mvp-kernel.config` (`CONFIG_DEVMEM=y`, `CONFIG_STRICT_DEVMEM=y`), `mvp/tools/build-guest.sh` (the `.config` delta check, Q16), `mvp/guest/mvp-init.c`, `mvp/guest/pins.txt` (init `9682c97f…`, Image `17f0e98c…`) | The writer fills the channel and the reader polls it through `/dev/mem`; a forked child of the init installs the SIGSEGV handler, makes the role's denied accesses at fixed labels, prints `MVPINIT 08 DENIED` with `si_addr`, and exits clean (M1-A, because Linux prints `unhandled signal` for pid 1 whatever handler is installed); `RESULT pass` needs the child's clean exit | External test input (upstream Linux `v7.2`), never committed; built by the pinned cross toolchain; `kernel-repro` passes | Is the `.config` delta exactly the two options, and does the child's report match the DENY line in `gpa`, `stval`/`va`, and `sepc`/`pc`? |
| Harness (M1-4) | `mvp/tests/check-capture.py` (47 self-test cases, 170 of 170 mutations rejected), fixtures `qemu-te-poc-gcc.log`, `qemu-reader-write-gcc.log`, `qemu-no-inject-gcc.log`, `qemu-te-poc-gcc-stop6-pid1.log`, `k3-no-inject-gcc-stop6-fallback.log`, `mvp/tests/run-qemu.sh` (44 runs), `mvp/tests/kexec-rehearsal.sh`, `mvp/tools/evidence.py` | Every capture judged in guest terms against the scenario's expectation, the DENY lines reconciled with the guests' reports and the authority report; the two stop-6 captures kept as fixtures the checker must reject; QEMU on three machines for both toolchains | Test-only | Do the reconciliation rules admit exactly the declared denials in declared order per domain, and do both stop-6 fixtures fail for their recorded findings alone? |
| Plan revision M1-B: the wait that measures progress | `mvp/src/mvp.h`, `mvp/src/mvp-sbi.c` (`be_mvp_ack_wait_start`, `be_mvp_ack_wait_step`), `mvp/src/mvp-ring.{h,c}` (`be_mvp_ring_taken`, `be_mvp_ring_published`), `mvp/src/mvp-hartmain.c` (`hart_fail`), `mvp/tests/sbi-test.c` (63 scenarios, 14,655 assertions), `mvp/tests/ring-test.c` (160 scenarios, 409,413 assertions) | A failed domain hart's 2^24-tick wait for hart 0's ACK restarts each time hart 0 takes a record from its outbound ring, so a healthy hart 0 behind the 115200-baud console is not mistaken for a wedged one; a still tail for the window, or a malformed tail, still falls back; hart 0's terminal path, the ACK, the window's length, and the `ring-full` immediate fallback are unchanged | The domain hart reads one more shared word (the tail hart 0 alone writes, which the writer already reads to find room); no new shared state; the decision is a pure function | Is the fallback's trigger now exactly "no progress and no ACK for 2^24 ticks", and does the host test pin the restart, the window boundary, the malformed tail, and the time wrap? |
| Board tools and the remote reset (M1-5) | `mvp/tools/k3ctl.sha256`, `mvp/tests/fake-k3ctl.py`, `mvp/tools/k3-run.sh`, `mvp/tools/k3-campaign.sh`, `mvp/tools/k3-preflight.sh`, `mvp/tools/kexec-load.py`, `mvp/tests/fake-board.py`, `mvp/tests/run-tool-dry-run.sh` (40 cases), `mvp/tools.mk` (`SCENARIO=`) | `K3_RESET=k3ctl` (opt-in): after a passing run's terminal marker, anchored at the start of a line, one `status`, one `reset`, one `status`, then the wait for a new boot ID; the client checked against its pin before any run and before each command; `status` and `reset` only, never `recovery` or `power`; a reset that cannot be made safely, or does not bring Fedora back, is stop 10; the preflight checks the channel page as an MVP extent and the firmware identity against M0's record | Board safety as M0's, plus: the client runs only at a fixed, pinned path with a fixed argument vector; no path read from a record is executed | Does the reset path send exactly `status`/`reset`/`status`, only after the terminal marker, only once per run, and never after a run that did not pass? |
| The board record and the platform record (M1-5, M1-6) | `mvp/results/20261027-com260-m1b/` (82 files), `mvp/tools/platform-record.py` (1,139 lines), `mvp/tools/evidence.py` | B0's retention of the second campaign: the preflight, both te-poc load checks, the six runs with their captures' excerpts, verdicts, resets, and the hand-written serial-log paragraph; the platform record's new sections: Preflight beside M0's record, te-poc runs, Denials on K3 (each DENY line beside its guest's report: `gpa`, `htval` = GPA >> 2, `stval=va`, `sepc=pc` in 12 of 12; `htinst` `0x3303` for the 8 loads, `0x3023` for the 4 stores), The channel (5 of 5 `CHANNEL_CHECKED` lines equal to the report's channel; the writer's and reader's digests equal in 5 of 5 runs), and the other runs' FAIL and DETAIL counts | The record is never overwritten; nothing in it is a claim | Does the record (`source_commit=17ed82f7`, `source_tree=clean`, `MANIFEST.sha256` SHA-256 `c4bd1b4900bee961a0bc475366f9c6bf3b28fcaebae101da59ce079d208571e9`) verify, and does every excerpt give its recorded verdict again? |
| Plan revisions M1-A and M1-B | `planning/mvp-m1-plan.md` (`00051fc4`; `745c293a`) | M1-A: the denied accesses in a forked child of the init; M1-B: the domain hart's wait measures hart 0's progress, with the corrected reading of the first campaign's stop | Plan text only; each revision names what it does not change | Does each revision stay within the accepted plan's claim boundary and stop conditions, and is each implemented as its text says? |
| Results and status | `mvp/README.md` (5,605 lines), this packet, `planning/HANDOFF.md`, `planning/roadmap.md`, `.github/copilot-instructions.md` | Every step's result with exact identifiers; 46 open items, each with its state; the size ratio 2.143 against the 2.2 limit (stop condition 13) | Documentation | Do the README's results and this packet agree with the retained records, and do the claims stay inside section 3? |

## 3. Claim boundary

**Supported by the exact commit:**

- **On the COM260** (2026-10-27, 17:45 to 18:02 UTC; the SpacemiT BSP's
  U-Boot 2022.10, the firmware reporting `SBI implementation ID=0x1
  Version=0x10006`, Fedora `7.3.0-65.1.riscv64.omni.fc45.riscv64`), with
  `17ed82f7`'s boot images (GCC `te-poc` `a55a5791b4b4…`, Clang `te-poc`
  `e32de2439ef0…`, the GCC `reader-write` variant `c575bc03d456…`, the
  GCC `no-inject` variant `4cb0df81bcdb…`, all byte-identical to the
  build at `17ed82f7` and to the evaluator's), in 6 of 6 RAM-only runs
  through Linux `kexec_load`, each on a distinct boot with one `k3ctl`
  reset after it and none by hand, automation never typing at U-Boot:
  - the preflight found harts 0 to 2 with H and Sstc, HSM detected, the
    eight MVP extents including the channel page `0x118000000-0x118001000`
    free, the firmware identity equal to M0's record, and the `k3ctl`
    client equal to its pin; both load checks loaded the GCC and Clang
    `te-poc` images at L = `0x1_0800_0000` with the FDT at
    `0x1_0840_0000` and unloaded them;
  - in each of the four `te-poc` runs, hart 0 ran the accepted R3 prelude
    through `BE_R3:06`, built and re-walked both roots with the channel's
    leaves (`writer_pte=0x460000d7 reader_pte=0x46000053`,
    `config=9cf02807…`), cleared the domains' RAM and the channel page,
    started harts 1 and 2 through SBI HSM, and both pinned Linux `v7.2`
    guests ran in VS mode on their own harts, concurrently (overlap
    `0x25405a7`-`0x2540615` of the shorter domain's `0x2563e5e`-`0x2563ed6`
    ticks); the writer filled the channel (digest `0xeacaea8433f5c641`,
    flag `0x42454d314348414e`) and the reader read the same digest at its
    first poll (`polls=1 match=1`); the writer's child made its one denied
    access and the reader's child its two, each logged by hart 0 as a DENY
    line (`kind=unmapped cause=0x15 injected=0x5 gpa=0x84001000
    htval=0x21000400 htinst=0x3303`; `kind=read-only cause=0x17
    injected=0x7 gpa=0x84000ff8 htval=0x210003fe htinst=0x3023`;
    `kind=unmapped cause=0x15 injected=0x5 gpa=0x90000000 htval=0x24000000
    htinst=0x3303`) with `vstvec=0xffffffff800af0b8` and service of
    `0xe`-`0x25` ticks, each observed by the guest as `SIGSEGV` code 2 at
    the label (`stval=va`, `sepc=pc`), the reader's store leaving the
    channel's last word unchanged (`unchanged=1`); both guests slept 1 s
    (`elapsed_ms=1004`), printed `RESULT pass`, and powered off; hart 0
    printed `exits_g0=163 exits_g1=167 denials_g0=1 denials_g1=2
    records=146 wakes=2 alternations=127 g0=67 g1=68` in every run, GCC
    and Clang alike, with `ring_peak` `0x1420` and `0x1558` against the
    budget `0x4000` and the longest run 1.696 s against `0x1_0000_0000`
    ticks;
  - `reader-write` printed `BE_MVP:FAIL gstage` and `DETAIL channel=0
    domain=1 hart=2 walked=0x460000d7 declared=0x46000053` after the
    second `BE_MVP:03` line and ran no domain; `no-inject` printed
    exactly one `BE_MVP:FAIL guest-page-fault` and its `DETAIL` (domain
    0, `cause=0x15 … htval=0x21000400 htinst=0x3303 … exits=94`), hart
    0's, after 54 guest lines from each domain, both `MVPINIT 07 CHANNEL`
    lines among them, and no line from a domain hart;
  - Fedora returned 33 to 47 s after each `k3ctl reset`
    (`reset_outcome=reset` six times); every capture passed the capture
    checker in kexec mode on the board tool's run and again from its
    retained excerpt in the board record; M1-5's exit criterion is met
    with no stop in the second campaign.
- **The first campaign** (2026-10-27, 09:32 to 09:41 UTC; the images of
  `9020c4f8`; `build/mvp/k3-campaigns/20261027-com260/`, outside the
  repository) passed its preflight, both load checks, three GCC and one
  Clang `te-poc` runs with the same counts, and `reader-write`, and
  stopped at `no-inject` (stop condition 6): both domain harts printed
  their own `FAIL` and `DETAIL` lines by M0's Q10 fallback, because the
  2^24-tick wait measured hart 0's latency and hart 0's 115200-baud
  backlog of 7,660 bytes outlasted it. Its stopped capture is the
  fixture `k3-no-inject-gcc-stop6-fallback.log`; its passing runs are the
  record of the stop, not M1's board evidence, because their images are
  not the revised commit's.
- **In QEMU** (`qemu-system-riscv64` 10.2.2, OpenSBI v1.6 `fw_dynamic`,
  `-smp 8 -m 8G`), at `17ed82f7`: `te-poc` passes on the `k3-like`,
  `rva23`, and `plic` machines for GCC and Clang, each run judged by the
  capture checker with its DENY lines reconciled, a boot on a domain hart
  `REFUSED` and repeated (44 runs, 57 attempts, 13 refused, the
  `two-guests` regression among them); `reader-write` and `no-inject`
  fail as declared; every M0 negative variant and probe image gives its
  declared result; the eight-hart kexec rehearsal passes for all four
  boot images.
- **Host and evaluator**, at `17ed82f7` from a clean tree: the port
  re-derives byte for byte; the policy check passes with its 33 cases and
  7 mutations and the two build-stopping negatives are refused; the tool
  lock passes on `l1` and in the evaluator; the host tests give identical
  GCC and Clang output on pinned counts (ring 160, hart 722, sbi 63,
  gstage 37, payload 8, deny 30 scenarios); the image checker passes with
  97 (`two-guests`) and 100 (`te-poc`) rejected mutations per toolchain
  and 4 per probe image; every budget holds (22 measured); the capture
  checker rejects 170 of 170 mutations; the dry run's 40 cases pass (one
  skipped inside the evaluator's read-only mount, and says so); the
  evidence bundle is byte-identical for a fixed input set;
  `BE_MVP_IMAGE_IDENTITY: PASS images=184 same=184
  differing=0`; `kernel-repro`: 12 outputs identical.
- **The authority report** (`build/mvp/gen/te-poc/authority-report.json`,
  retained in the record under `mvp/scenario/te-poc/`) states six grants
  and one declared flow, from G0 to G1 through the shared page, and no
  undeclared flow; A7 is vacuous for the fixed binding; neither the
  capability trigger nor the runtime-check trigger fires for Instance 2
  (security model v1), and nothing in M1 selects a runtime policy
  mechanism.
- **The platform record** (`mvp/results/20261027-com260-m1b/platform-record.md`
  and `.json`) gathers the facts above with their sources, beside M0's
  record and QEMU's values. Nothing in it is a claim.
- **Plan revisions M1-A and M1-B** are implemented as their text says.

**Trusted or assumed:**

- The accepted M0 result, the accepted R3 prelude, B2's generated port,
  B3's shim, and B7's copied files, at their accepted commits.
- OpenSBI 1.6 on the board (HSM, IPI, SRST), the firmware's SRST halting
  every hart promptly (which the `no-inject` run's single pair rests on),
  and Fedora's `kexec_load` path; the host's cross GCC 16.2.1, binutils
  2.46.1, Clang and LLD 22.1.8, QEMU 10.2.2, and the closure's packages,
  as the lock pins them; the `k3ctl` client at its pinned SHA-256 and the
  ESP32-C3 dongle it drives, outside the lock.
- The guest's upstream Linux `v7.2` (`8d3ae592…`), B6's fragment and the
  MVP's two-option delta, an external test input, never committed; its
  `/dev/mem` with `STRICT_DEVMEM` mapping exactly the non-RAM pages the
  roles touch; its delivery of the injected access faults as
  `SIGSEGV`/`SEGV_ACCERR` with `si_addr` the faulting address.
- Isolation between the domains beyond the declared channel is by
  construction only: two disjoint windows, two re-walked roots under
  distinct VMIDs, one declared page with declared rights; the three
  denials are the plan's declared denials, not a search for undeclared
  ones.

**Unavailable or `NOT RUN`:**

- OpenSBI's power-on prints are not on this BSP's console; the firmware
  is visible only through SBI and its reserved memory only through the
  FDT reservations and `/proc/iomem`.
- No fetch denial (the guest cannot map an executable non-RAM page under
  FLATMEM, as the plan records); no denial from VS mode or from a second
  process at once; no board run under U-Boot `booti`; no second board;
  no run with the Fedora 44 host kernel of B0-B7.
- No formal result: the denial path has no proof; the Rocq model is
  untouched; R7's bounded proof does not extend to M1; A1-A8 are offline
  checks of the manifest against the policy, not a proof.
- The evaluator's `tree-state` dry-run case is skipped inside the
  evaluator (read-only source mount) and runs on the host.

**Not implemented or selected:** a runtime policy mechanism, an access
vector cache, dynamic relabeling, a policy language beyond the fixed
notation, a protected domain (M2), a scheduler, a third domain hart, a
shared page beyond the one declared channel, a device, MMIO, or DMA path,
a development kernel or BSP, root integration, a Model change, a security
model v1 revision, or any CHERI mechanism. This is diagnostic bring-up
evidence for one board, firmware, and Fedora kernel, never hardware
validation, qualification, or formal verification; QEMU results are
emulation; Model, Helium, R-series, B0-B7, and M0 claims do not transfer
beyond what M1 reuses; and nothing here is a security claim.

## 4. Load-bearing invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| A guest-page fault is accepted only from VU mode, at a declared denial's GPA and kind, in an image whose accepted-exit set holds `denial`; everything else is terminal | Plan, "The denial path"; MVP plan D8; S1 H15, H16 | `be_mvp_denial_decide` (pure); `mvp-hartmain.c`'s `deny()`; the image's accepted-exit set from the scenario | `tests/deny-test.c` (30 scenarios: VS-mode, undeclared GPA, wrong kind, cause 20, an image without the entry); the `no-inject` image in QEMU and on the board; image-checker mutations |
| The injected fault is exactly `vscause` 1, 5, or 7 by kind, `vstval` = `stval`, `vsepc` = `sepc`, `vsstatus` SPP/SPIE/SIE as the plan names, resume at the `vstvec` base, each written with readback | Plan, "The denial path" | `be_mvp_arch_inject` (`mvp-trap.S`), `be_mvp_inject_words` | The image checker's CSR rules for the helper; `tests/sbi-test.c` on the words; the guests' `MVPINIT 08` lines (`signo=11 code=2`, `va`, `pc`) matched to the DENY lines in 12 of 12 board denials |
| The channel is one level-0 leaf per root with the declared rights, walked at boot and refused if other | Plan, "The channel in the G-stage" | `mvp-gstage.c` `build_channel`, `walk_channel`, `channel_check`; `mvp-runtime.c` `CHANNEL_CHECKED` | `tests/gstage-test.c` (37 scenarios); `reader-write` refused in QEMU and on the board; the platform record's "The channel" |
| The DENIAL record's words and hart 0's DENY line reconcile with the guest's report and the authority report; `exits = sbi + ipi + denials` | Plan, "Markers", "Scenarios and the harness" | `be_mvp_post_denial`, `emit_denial`; the capture checker's reconciliation rules | 170 of 170 capture mutations rejected; 4 of 4 board `te-poc` runs with `denials_g0=1 denials_g1=2` |
| A failed domain hart prints its own lines only when hart 0 neither acknowledges nor takes a record for 2^24 ticks | Plan revision M1-B.1 | `be_mvp_ack_wait_step`; `hart_fail()` | `tests/sbi-test.c` (10 scenarios, the board's backlog replayed); the first campaign's stop capture rejected as a fixture; the second campaign's `no-inject` run with one pair |
| The remote reset sends only `status`, `reset`, `status`, through the pinned client, after a passing run's anchored terminal marker, once per run | Plan, "The remote reset" (Q14) | `k3-run.sh` `k3ctl_command`; `tools/k3ctl.sha256` | The dry run's reset cases with the fake dongle (40 cases); six `reset.txt` records; the first campaign's stop with `reset_outcome=no-reset-verdict` |
| A board run is RAM-only and output-only; a campaign ends at the first run that does not pass; no path read from a record is executed | Plan, "Board safety and procedure"; S1 H30 | `k3-run.sh`, `k3-campaign.sh`, `kexec-load.py` (the channel page as an MVP extent), `evidence.py` | The dry run's refusal cases; the first campaign's stop at its sixth run |

## 5. Review history and resolved findings

| Finding | Resolution |
| --- | --- |
| **Stop condition 6** (2026-10-27, M1-4 in QEMU): Linux `v7.2` prints `init[1]: unhandled signal 11 …` and a register dump for pid 1 whatever handler is installed (`kernel/signal.c:536-538`, `is_global_init`), an M0 rejected substring, although every injected fault reached the init as `SIGSEGV`/`SEGV_ACCERR` at the label and both guests passed | Returned; Plan revision M1-A directed (`A`): the denied accesses in a forked child of the init; implemented at `65648204`; the pid-1 capture kept as the fixture `qemu-te-poc-gcc-stop6-pid1.log` |
| **Responsible-human gate on the K3** (2026-10-27): another project was using the board | Recorded; the campaign waited for the explicit release (`the other session has released the k3`) |
| **Stop condition 6** (2026-10-27, M1-5, first campaign, `no-inject`): both domain harts printed their own `FAIL` and `DETAIL` pairs | Returned with three options; the handoff's first reading (hart 0 went terminal without acknowledging domain 1) was wrong, and the corrected reading is in Plan revision M1-B: hart 0 never took a FAIL record; Q10's 2^24-tick window measured hart 0's latency behind the console. Directed `accept B, proceed`; M1-B implemented at `804cd24c` as the progress-measured wait; the stopped capture kept as a fixture; the campaign restarted with the revised images and passed 6 of 6 |
| The plan revision's byte count for the backlog (7,749) counted the capture's CRs twice | Corrected to 7,660 bytes on the wire before commit (`745c293a`) |
| The implementation commit `804cd24c` summarizes the text growth as `0xb0` (GCC) and `0xc0` (Clang) | The README's measured table has the exact figure: `mvp_text` grew by `0xb0` in 17 images and `0xc0` in 5 |
| An invocation of the campaign tool without `SCENARIO=te-poc` ran M0's `two-guests` scenario three times with `804cd24c`'s images before the second campaign | The three runs passed with M0's exact counts (`exits 157/157 records=138 wakes=2 alternations=125`); set aside under `build/mvp/k3-campaigns/20261027-com260-m1b-two-guests-unplanned/`, recorded in the README as an unplanned observation, not evidence (open item 45); the plan's command list predates the selector (open item 44); the README's Commands show the selector |
| The platform record's pairing rule mirrors the capture checker's rather than importing it | The checker reads `mvp-layout.h` on import; the mirrored rule is checked by the dry run's `te-poc-record` case, which catches a reversed pairing |
| The checker-to-monitor size ratio | 2.143 at the M1-6 content (M0: 1.797; M1-5: 1.994), under the plan's 2.2 limit (stop condition 13); the policy checker and the fake dongle account for most of the growth |

**Open for human judgment:** the two plan revisions (section 2); the
remote reset as a departure from the MVP plan's "with human resets",
accepted into the M1 plan at Q14 and exercised six times; the `.config`
delta (`CONFIG_DEVMEM`, `CONFIG_STRICT_DEVMEM`); the three unplanned
`two-guests` runs (open item 45); the stale podman store on `l1` (open
item 43, unchanged).

**Not run by SOP:** no iterative-evaluation review with a different
model, no separate scope review, and no deep security review. The work
ran on `claude-opus-5.5` sub-agents at `max` effort with the
`long_context` tier for every implementation package, orchestrated and
reviewed by `claude-fable-5.1` at the responsible human's direction for
this session (`use the current model for planning, orchestration &
review, and opus-5.5 max long context to perform coding`); the
repository's model pin is unchanged. The orchestrating session reviewed
M1-B's mechanism diff line by line before commit.

## 6. Validation and retained evidence

All at exact commit `17ed82f7` from a clean tree on `l1` (x86_64, Fedora
44), 2026-10-27, through the wrapper's clean environment:

| Command | When (UTC) | Result | Covers |
| --- | --- | --- | --- |
| `./mvp/mvp check` | 19:26:16-19:30:23 | `BE_MVP_CHECK: PASS`; `BE_MVP_LOCK: PASS roles=29 host_only_skipped=0 closure=259 lock_sha256=6e99262f04a1`; `BE_MVP_CAPTURE_SELF_TEST: PASS cases=47 failed=0`; `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=170 rejected=170`; `BE_MVP_RUN_TOOL_DRY_RUN: PASS`; `BE_MVP_QEMU: PASS runs=44 attempts=49 refused=5`; `BE_MVP_BUDGETS: PASS measured=22`; `BE_MVP_EVIDENCE: PASS development … files=220 images=184 qemu_attempts=49 rehearsals=4` | Lock, port, policy check and negatives, guest pins, host tests, images and mutations, variants, probes, budgets, capture checker and mutations, the 40 dry-run cases, the QEMU suite, the bundle |
| `./mvp/mvp evaluate` | 19:31:41-19:36:07 | `host source=17ed82f7… tree=clean images=184`; `BE_MVP_LOCK: PASS roles=26 host_only_skipped=3 …` (inside); `BE_MVP_QEMU: PASS runs=44 attempts=58 refused=14` and `BE_MVP_CHECK: PASS` (inside); `BE_MVP_IMAGE_IDENTITY: PASS images=184 same=184 differing=0`; `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655` | The whole check inside the clean evaluator, images compared with the host's |
| `./mvp/mvp kexec-rehearsal` | 19:36:14-19:37:10 | four `BE_MVP_KEXEC_REHEARSAL: PASS smp=8 …` lines, images `2d33d5887cc0`, `a55a5791b4b4`, `0115b6960b73`, `e32de2439ef0`, each refused domain-hart boot repeated within the bound | Linux `kexec_load` of all four boot images under QEMU with eight harts |
| `./mvp/mvp kernel-repro` | 19:37:24-19:37:46 | `BE_MVP_KERNEL_REPRO: PASS outputs=12 identical; sysroot_files=1065 sysroot_sha256=c931b51b…` (`make -C mvp kernel-repro LINUX_GIT=/home/jmorris/src/kernel.org/linux`) | A second full guest build compared with the first |
| `K3_RUN_ROOT=… ./mvp/mvp board-evidence` | 19:37:54-19:37:57 | `BE_RETAIN: PASS runs=6 load_checks=2 files=80`; six `ok … recorded PASS, excerpt PASS`; `BE_MVP_PLATFORM_RECORD: PASS … runs=6 te_poc_runs=4 denials=12 channel_checked=5 resets=human:0,k3ctl:6`; `BE_MVP_EVIDENCE: PASS board … runs=6 pass=6 fail=0 refused=0 stop=0`; `--verify … files=82` | The committed board record, `mvp/results/20261027-com260-m1b/` (`source_commit=17ed82f7`, `source_tree=clean`; `MANIFEST.sha256` SHA-256 `c4bd1b4900bee961a0bc475366f9c6bf3b28fcaebae101da59ce079d208571e9`) |

The board runs themselves are the retained records above; the campaign
directories `build/mvp/k3-campaigns/20261027-com260/` (the first
campaign, with its stop) and `20261027-com260-m1b/` (the second, with the
six console transcripts) stay on `l1`, outside the repository. Each run's
raw serial capture stays private; `captures.txt` records its SHA-256,
bytes, and lines.

## 7. Recommended review sequence

```sh
git worktree add --detach /tmp/be-m1-review ff84533cb3c13d89063be77652575347c2a82757
cd /tmp/be-m1-review
git --no-pager log --oneline 41f88795..HEAD              # the M1 commits
git --no-pager diff --stat 41f88795 HEAD -- . ':!mvp' ':!planning' ':!.github'   # must be empty
git --no-pager diff --stat 41f88795 HEAD -- mvp/results/20261025-com260            # must be empty
```

1. **Plan and revisions** (30 min): `planning/mvp-m1-plan.md`, the
   "Decision record", "Claim boundary", "Stop conditions", and the two
   revisions; then this packet's section 3 against them.
2. **The policy and the report** (20 min): `mvp/scenarios/te-poc/policy.te`
   against security model v1's Instance 2; `mvp/tools/policy-check.py`'s
   A1-A8; the retained report in the record.
3. **The board record** (20 min): `mvp/results/20261027-com260-m1b/`:
   `summary.md`, `mvp/runs.tsv`, one `te-poc` run's `check.txt` and
   excerpt, the `no-inject` run's, `platform-record.md` ("Denials on K3",
   "The channel"); then `python3 -B mvp/tools/evidence.py --verify
   mvp/results/20261027-com260-m1b`.
4. **The mechanism** (60 min): `be_mvp_denial_decide` and `deny()`;
   `be_mvp_arch_inject`; `mvp-gstage.c`'s channel functions;
   `be_mvp_ack_wait_step` and `hart_fail()`; the image checker's rules.
5. **The harness and tools** (30 min): `tests/check-capture.py`'s
   reconciliation rules and the two stop-6 fixtures; `tools/k3-run.sh`'s
   reset path; `tests/run-tool-dry-run.sh`.
6. **README results** (30 min): `mvp/README.md` from "M1-1 and M1-2"
   through "M1-6", then open items 44 to 46.
7. **Run the gates** (15 min on a host that satisfies the lock):

```sh
cd /tmp/be-m1-review && ./mvp/mvp tool-lock check && ./mvp/mvp check && ./mvp/mvp evaluate && ./mvp/mvp kexec-rehearsal
cd - && git worktree remove /tmp/be-m1-review
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The scope matches the accepted M1 plan at `7b2c055c` with Q1 to Q19
      at their defaults, and the two revisions stay within its claim
      boundary and stop conditions.
- [ ] The claims in section 3 match the retained evidence: the board
      record, the QEMU records, the evaluator record, and the README.
- [ ] The trust assumptions are acceptable: the accepted M0 result and
      its inputs, the firmware's prompt SRST, the external Linux `v7.2`
      input with the two-option delta, the `k3ctl` client and dongle
      outside the lock, and isolation beyond the channel by construction.
- [ ] The tests cover the important negative paths: the four negative
      images, the image and capture mutations, the deny host test's
      refusals, the dry run's reset and refusal cases, both stop-6
      fixtures.
- [ ] The remote reset's safety rules, exercised six times, are
      acceptable.
- [ ] Successor work stays excluded: M2, the merge into the development
      branch, a security model v1 revision, a Model change, root
      integration, development-kernel/BSP selection.
- [ ] Decision: accept exact commit `ff84533c` with Plan revisions M1-A
      and M1-B; request revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `ff84533cb3c13d89063be77652575347c2a82757`, with Plan revisions M1-A (`00051fc4`) and
  M1-B (`745c293a`), and the date. The acceptance record names that SHA;
  the plan's revision status records and the status documents are
  updated to match. Acceptance starts no successor: M2's bounded plan,
  any merge of `beryllium/mvp-m1` into the development branch, and any
  push each need their own instruction.
- **Request revisions:** a new commit and a new packet follow;
  `ff84533c` is not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commit `ff84533cb3c13d89063be77652575347c2a82757` is
responsible-human accepted as the M1 result as of 2026-10-27
(instruction `approve ff84533c and revisions, accept your
recommendations, authorize proceeding per those`), with Plan revisions
M1-A and M1-B. It is on branch `beryllium/mvp-m1`, backed up on the
private `origin`; M2 implementation is not started or authorized.

**Next:** the accepted recommendations, in order: the development-branch
fast-forward and push; the model-split paragraph in the instructions;
the M2 plan as a proposal on a new branch.

**Action required from you:** none for M1. The M2 plan will return as its
own exact commit for your decision.
