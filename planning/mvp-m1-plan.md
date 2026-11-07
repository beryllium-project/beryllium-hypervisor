<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M1 plan: the TE PoC scenario on two Linux guests

## Decision record

The responsible human accepted this plan at exact commit
`7b2c055c1587f9582812a575b296cd625746662b` (parent
`6f7b6e7c1fd609299fd88af164d400da3d6435ae`, the M0 result acceptance
record) on 2026-10-26. The instruction, given in reply to the
[review packet](mvp-m1-plan-review-summary.md)'s request to accept,
revise, or defer that exact commit, was `accept 7b2c055c`, whose
abbreviation resolves uniquely to that commit.

- **Scope:** acceptance covers exactly the plan text at that commit.
  Everything after this section is the plan as accepted, including the
  pre-decision status text below; only this section and the acceptance
  fields in the status record were set afterwards.
- **Authorized:** M1 implementation under this plan, work packages M1-1
  to M1-6, on branch `beryllium/mvp-m1` from the acceptance-record
  commit: the `te-poc` scenario with its policy, labeling, need sets,
  and manifest; `tools/policy-check.py` and the authority report; the
  channel in the G-stage builder, walker, and check; the denial path and
  its injection helper; the new records, lines, and checks; the guest
  init's roles, M1's two-option kernel fragment, and the rebuilt pinned
  guest outputs; the four negative images; QEMU with eight harts, the
  kexec rehearsal, and the clean evaluator; the board tools' remote-reset
  path and its dry run; the read-only Fedora preflight; and RAM-only
  COM260 runs through Linux kexec as [Board safety and
  procedure](#board-safety-and-procedure) lists them, each followed by
  one reset, through `k3ctl` under Q14's default or by hand, ending in
  one result review packet. Each [stop condition](#stop-conditions)
  returns M1 to the responsible human. The repository's model pin
  (`.github/copilot-instructions.md`) applies to the implementation
  unless the responsible human directs otherwise.
- **Open questions:** Q1 to Q19 were not answered, so the defaults
  apply, including the two departures the packet named: the `k3ctl`
  remote reset, opt-in, `status` and `reset` only, one per passing run
  (Q14), and the guest kernel fragment `CONFIG_DEVMEM=y` and
  `CONFIG_STRICT_DEVMEM=y` merged after B6's unchanged fragment (Q2).
- **Not authorized:** everything the plan excludes, as "Acceptance would
  not authorize" below lists it: any M2, M3, or M4 deliverable; a runtime
  TE check or capabilities; a scheduler or dynamic hart use; devices or
  injected interrupts; a change to any accepted byte, accepted document,
  retained R8 input, M0's retained board record, or anything under
  `model/`; root integration or development-kernel/BSP selection; an
  HS-to-M SBI call beyond M0's surface; U-Boot automation or any
  persistent firmware, environment, flash, or storage change; any
  `k3ctl` command but `status`, the `ping` handshake, and `reset`; and
  push, tag, publication, release, a merge into the development branch,
  or any successor, including M2's plan.
- **Evidence status:** acceptance adds no implementation, emulation, or
  board evidence. Nothing of M1 had been built or run at the accepted
  commit; the plan's readings of the RISC-V privileged specification and
  of the pinned Linux source are the plan's, not yet exercised.

## Decision requested

**Status:** accepted on 2026-10-26; see the
[decision record](#decision-record). As presented, the plan was
proposed and not accepted, as the paragraph below states.

**Status as presented:** proposed for responsible-human review; not
accepted. No M1 implementation has started: nothing under `mvp/` has
changed for M1, and nothing has been built or run for it. Facts below
come from the accepted
documents, the M0 result at exact commit `b2669725` with its retained board
record, the MVP line's sources, and read-only planning reads of the pinned
Linux `v7.2` source (the M0 build tree's checkout at `8d3ae592`) and of the
`k3ctl` bundle. *Fact* marks what a record or source shows, *inference*
reasoning from facts; upstream sources are `path:line@v7.2`, and readings
of the RISC-V privileged specification are named by section and are this
plan's readings.

The accepted [MVP plan](mvp-plan.md) (exact commit `93967fba`, accepted
2026-10-23) orders M1, "The TE PoC scenario on two Linux guests", after
M0, and gives each milestone "its own bounded plan and its own result
acceptance". The responsible human accepted the M0 result at exact commit
`b2669725` (parent `13992d6d`) on 2026-10-26 with the instruction
`accept b26697`; its acceptance record is `6f7b6e7c`, and
`beryllium/mvp-m0` and the development branch
`beryllium/single-hart-runtime-r0` are both at `6f7b6e7c`, locally and on
the private `origin`. This plan's branch, `beryllium/mvp-m1-plan`, starts
there. On 2026-10-26 the responsible human also selected, by form answer,
that this plan propose wiring the `k3ctl` remote reset into the board
tools (Q14); the M0 acceptance record had listed that wiring among the
successors needing direction, "since the accepted plan names the human as
the one who resets".

M1 changes the MVP line in place. It adds Instance 2 of [security model
v1](security-model-v1.md) as the configuration of a new scenario,
`te-poc`; an offline checker that runs A1 to A6 and A8 and writes the
authority report; one declared channel page that the writer's root maps
read-write and the reader's read-only; a denial path on each domain hart
that logs a G-stage fault, delivers it to the guest as the corresponding
access fault, and resumes the guest; guest programs that use the channel
and make three denied accesses; four negative images; and the remote
reset. It changes no accepted R0-R7 or B0-B7 byte and nothing under
`model/`.

The responsible human is asked to decide on the exact commit that adds
this plan on branch `beryllium/mvp-m1-plan`:

- **Accept:** authorizes M1 implementation under this plan, work packages
  M1-1 to M1-6, on a branch `beryllium/mvp-m1` from this plan's acceptance
  record: the `te-poc` scenario with its policy, labeling, need sets, and
  manifest; `tools/policy-check.py` and the authority report; the channel
  in the G-stage builder, walker, and check; the denial path and its
  injection helper; the new records, lines, and checks; the guest init's
  roles, M1's two-option kernel fragment, and the rebuilt pinned guest
  outputs; the four negative images; QEMU with eight harts, the kexec
  rehearsal, and the clean evaluator; the board tools' remote-reset path
  and its dry run; the read-only Fedora preflight; and RAM-only COM260
  runs through Linux kexec as [Board safety and
  procedure](#board-safety-and-procedure) lists them, each followed by one
  reset, through `k3ctl` under Q14's default or by hand. It ends in one
  result review packet. Each [stop condition](#stop-conditions) returns M1
  to the responsible human. The repository's model pin
  (`.github/copilot-instructions.md`) applies to the implementation
  unless the responsible human directs otherwise.
- **Request revisions** or **defer:** M1 stays unstarted.

Acceptance would not authorize:

- any M2, M3, or M4 deliverable: a management extension or call, a
  measurement, a protected domain, a second channel, the security model
  v1 revision that M3 plans, any change under `model/`, or the release
  candidate;
- a runtime TE check, software capabilities, dynamic management, a policy
  parser or `decide` in HS, or any per-access decision beyond the derived
  mappings;
- a scheduler, time-multiplexing, domain migration or overcommit, a third
  domain hart, starting or stopping a hart after the boot barrier, or a
  lock held across guest execution;
- devices, MMIO, interrupt controllers, DMA, or any injected interrupt;
- a change to any accepted R0-R7 or B0-B7 byte, to an accepted document's
  text, to a retained R8 input, or to M0's retained board record and the
  fixture made from its board capture;
- root `Makefile`, `be`, or `scripts/check-be.sh` integration (MVP plan
  D3), or a development-kernel/BSP selection;
- an HS-to-M SBI call beyond M0's surface;
- a U-Boot run, automation typing at U-Boot, or any persistent firmware,
  U-Boot environment, flash, boot-configuration, or storage change;
- any `k3ctl` command but `status`, the client's `ping` handshake, and
  `reset`: in particular `recovery`, `power`, `press`, `hold`, `release`,
  and `raw`;
- push, tag, publication, release, a merge into the development branch,
  or any successor, including M2's plan.

### Open questions

Each has a default, so acceptance can proceed without answers.

| # | Question | Default if unanswered |
| --- | --- | --- |
| Q1 | Where is the shared page, and how do the roots map it? | One 4 KiB page at GPA `0x8400_0000`, directly above each guest's 64 MiB window and the same in both roots, backed by HPA `0x1_1800_0000`, a new MVP-owned 4 KiB extent directly above G1's window. Each root maps it through one level-0 page, the pool's spare page at pool + `0x5000` (`0x1_0203_9000` and `0x1_0204_1000`), behind level-1 entry 32: the writer's leaf `V R W U A D` (PTE `0x460000d7`), the reader's `V R U A` (`0x46000053`), `X` in neither ([G-stage and VMIDs](#g-stage-and-vmids)). The alternative, one 2 MiB shared leaf with the guests told to use its first 4 KiB, keeps M0's walker rule of exact 2 MiB leaves, but grants 512 pages of shared authority where Instance 2 declares one page, needs a 2 MiB-aligned HPA extent, and would make M2's two pages 4 MiB |
| Q2 | How do the guest programs reach the page and the denied addresses? | Through `/dev/mem`: M1 adds a two-option MVP fragment, `CONFIG_DEVMEM=y` and `CONFIG_STRICT_DEVMEM=y`, merged after B6's unchanged fragment, and `/dev/mem` to the initramfs. With STRICT, `/dev/mem` maps only addresses that are not the guest's RAM (`lib/devmem_is_allowed.c:21-28@v7.2`), which are exactly the channel and the denied addresses. The alternatives, weighed in [Guest software](#guest-software): `CONFIG_DEVMEM=y` alone (one line, but the init could map the guest's own RAM); UIO (two options and a device node in a guest DT that has none); a driver or a kernel patch (the guest stops being unmodified upstream Linux); `memmap=` (absent on RISC-V in `v7.2`); a DT memory node over the page (Linux would allocate it, and the reader's kernel would fault writing it) |
| Q3 | Which denials does the scenario make? | Three: G0, the writer, loads from GPA `0x8400_1000`, beside the channel page, which no root maps (cause 21); G1, the reader, stores to GPA `0x8400_0ff8` in the channel page (cause 23, read-only), then loads from GPA `0x9000_0000`, the GPA of M0's K3 probe (cause 21). The faults arise at three places in the walk: a zero level-0 entry, a leaf without `W`, and a zero level-1 entry. No scenario access is a fetch: the guest program cannot fetch from a page outside its RAM safely on the pinned kernel ([Guest software](#guest-software)), so cause 20's acceptance and encoding are covered by host tests only. The alternative removes cause 20 from the accepted entry until a test can exercise it end to end |
| Q4 | What is the accepted-exit set? | Per scenario (MVP plan D8): `two-guests` keeps M0's, and `te-poc` adds one denial entry: cause 20, 21, or 23 from VU mode (`hstatus.SPV` 1, `SPVP` 0, `GVA` 1), `htval` below 2^39, `htinst` zero or the transformed load (cause 21) or store or AMO (cause 23), `vstvec` in Direct or Vectored mode, and either a GPA the hart's root does not map or a store to the channel page in a root whose leaf lacks `W`. Everything else stays terminal, a fault from VS mode and a fetch from the channel page included ([The denial path](#the-denial-path)). The alternative also admits VS-mode faults, so that the guest kernel's own fixups run; M2's plan may take it for its hostile tests |
| Q5 | How is a denial delivered? | As the corresponding access fault, written by one helper and read back before the record is posted: `vscause` 1, 5, or 7 for cause 20, 21, or 23; `vstval` = `stval`, the guest virtual address; `vsepc` = `sepc`; `vsstatus.SPP` = the guest's mode at the fault (VU, so 0), `SPIE` = `SIE`, `SIE` = 0; the guest resumes in VS mode at `vstvec`'s base; `htval` and `htinst` are logged only. The alternative, a page fault (12, 13, or 15), would make Linux find its own PTE valid and run the instruction again, which faults again (inference) |
| Q6 | How do denials reach the console? | One outbound DENIAL record per denial, posted to the hart's own ring before the guest resumes; hart 0 drains it in M0-C's round-robin order and prints one `BE_MVP:DENY` line. The channel adds `BE_MVP:03 CHANNEL_CHECKED` and `BE_MVP:05 CHANNEL_CLEARED`, once per declared channel. No M0 line changes format, so `two-guests`, M0's fixtures, and the board's stop-6 fixture stay valid ([Markers](#markers)). The alternative renumbers lines or adds fields to `:12` and `:13`, which invalidates M0's fixtures, including the board capture that must fail on the alternation floor alone (M0-C.2) |
| Q7 | What form does the offline checker take? | `mvp/tools/policy-check.py`, Python 3 only (a locked role): Instance 2 in Part 2's concrete syntax in `scenarios/te-poc/policy.te`; the labeling, need sets, and manifest in `scenario.json`; A1 to A6 and A8 as pure functions, and A7 recorded as vacuous; the authority report in JSON (MVP plan D9); a self-test and seeded single-defect mutations; at most 900 lines in all. The alternative, a C checker sharing the monitor's code, would not be an independent implementation for M3's differential check |
| Q8 | What is the manifest? | M1's own: the scenario's domains (each window with its rights, and the hart, VMID, root, and block binding), objects (the channel page and the monitor's extents), and channels (object, GPA, endpoints, rights), read as the canonical sealed state and validated by A8. It is not a Model 0.2 encoding: Model 0.2 is "encoding-independent" and does not "provide a stable manifest encoding" ([Model 0.2](architecture-model-0.2.md), "Fixed scope" and "Non-goals"); relating M1's checker to Model 0.2's validator is M3's differential check |
| Q9 | What identity does the image carry? | A configuration identity: SHA-256 over the report's manifest, policy, and labeling identities (Part 4), computed offline, linked as a constant, and printed by hart 0 in `BE_MVP:03 CHANNEL_CHECKED`; the image checker and the capture checker both match it to the report. It is not a measurement. The alternative, a digest computed by the monitor at boot, is M2's measurement work |
| Q10 | Scenario schema? | `be-mvp-scenario-v2` for `te-poc`, because v1 has no field for a policy, labeling, need set, object, channel, accepted-exit entry, guest role, or expected denial, and the generator refuses unknown fields; `two-guests` stays v1, unchanged, as the QEMU regression of M0's scenario. The alternative moves `two-guests` to v2 with an empty channel list |
| Q11 | Which negative images, and where? | Four ([Scenarios and the harness](#scenarios-and-the-harness)): `undeclared-flow` and `grant-without-rule` stop the build at the offline check and never produce an image, so they run on the host and in the evaluator only; `reader-write` (the root builder sets `W` in the reader's leaf; the sealed manifest is unchanged) is refused by the boot-time channel check; `no-inject` (`te-poc` without the denial entry) fails closed at the first guest-page fault. The last two run in QEMU (GCC and Clang) and on the board (GCC) |
| Q12 | Board campaign size? | Both load checks, then six RAM-only kexec runs, each followed by one reset: three GCC and one Clang `te-poc` runs, then `reader-write` and `no-inject` (GCC). The alternative drops the two negative runs, to four |
| Q13 | Do M0's probe images run again? | No: M0's platform record stands as M1's input. The preflight records the firmware identity, and one other than M0's record (`SBI implementation ID=0x1 Version=0x10006`) is a stop before any kexec run. The alternative runs `probe-platform` again first |
| Q14 | Remote reset? | `k3ctl` wired into the board tools, opt-in per invocation (`K3_RESET=k3ctl`) and used for M1's campaigns: after a passing run's terminal marker, with Fedora down, `status` then `reset`, at most one reset per run, the client pinned by SHA-256, every reply recorded ([The remote reset](#the-remote-reset)). A run without its terminal marker gets no automated reset: it is a stop, and the board stays as it is for the human. The tools never issue `recovery`, `power`, `press`, `hold`, `release`, or `raw`. The alternative is human resets as in M0, which stay the tools' default; a second alternative also resets after the tool's own timeout, which this plan rejects because Fedora may then still be running |
| Q15 | Does M0's `vmid-shared` finding change anything? | No. No hart switches roots, no root changes after the barrier, and each root is installed on exactly one hart under exactly one VMID for the whole run (MVP plan M1 deliverable 4), so no stale translation can arise; the reader's denied store is H12's observation on this layout |
| Q16 | The guest `.config` follows the host's Rust and pahole (M0 open item 42)? | The guest build passes Kbuild's own `RUSTC`, `BINDGEN`, and `PAHOLE` variables (`Makefile:549-554@v7.2`) naming no executable, so Kconfig's probes give the same `.config` on every host, and `kernel-repro` compares across `lx2` and `l1`; the pinned outputs never depended on those lines (open item 42). The alternatives lock Rust and dwarves, two roles with their closures, or normalize the lines in `kernel-repro` |
| Q17 | The closure's dependence on the host (M0 open items 37 and 39)? | Unchanged in M1: M1 adds no role, and a host update that drifts the lock is refreshed only on the responsible human's direction, as in M0. Deriving the closure from its roles on a reference package set is left to M4's clean exact-commit evidence (S1 H30 to H32), where the reproducibility wording is settled once. The alternative does it in M1 |
| Q18 | The campaign tool's wait (M0 open item 38)? | With `k3ctl`, the wait after the tool's own reset is bounded (`K3_RESET_RETURN_SECONDS`, default 300 s) and a timeout is a stop. With human resets, a wait timeout prints `BE_MVP_K3_CAMPAIGN: PAUSED` with its own exit status, writes the summary of the runs made, and names the runs left, instead of `STOP`. The alternative leaves the wording as it is |
| Q19 | SBI implementation version? | 3, unchanged: D8 raises it with "every change to the guest-visible SBI surface", and M1 changes no SBI extension, function, argument, or result; a denial reaches the guest as an architectural access fault through its own trap vector, not through SBI. The alternative raises it to 4 to mark the new behaviour |

## Goal and pass criterion

M1 delivers the MVP plan's M1 deliverables 1 to 6 on the M0 line and
meets its exit: in QEMU and in the default board campaign, both domains
run concurrently, each on its own hart; data crosses the channel from the
writer to the reader only; every denied access appears exactly once in
the monitor's denial log, with the fields the guest reports and in the
order the guest reports them; both guests continue and power off; the
authority report lists exactly Instance 2's grants and the one flow
`writer_t -> reader_t`; every check passes; and every negative image fails
as declared. M1 passes when:

1. `tools/policy-check.py` passes A1 to A6 and A8 on Instance 2, with A7
   vacuous, and writes a report of exactly six grants, each with its
   allowing rule, and one declared flow; the two build-time negatives stop
   the build as declared, on the host and in the evaluator;
2. the `te-poc` images (GCC and Clang) pass the image checker, and every
   budget holds;
3. every `te-poc` capture passes the capture checker, including the
   reconciliation of the denial log with the guests' reports and of the
   boot-time channel line with the report: QEMU with eight harts on the
   `k3-like`, `rva23`, and `plic` machines for GCC and Clang, the kexec
   rehearsal, and the board's three GCC and one Clang runs;
4. `reader-write` and `no-inject` fail as declared in QEMU (GCC and Clang)
   and on the board (GCC);
5. M0's `two-guests` scenario, its negative variants, and its probe images
   pass in QEMU as in M0, and M0's capture fixtures give their recorded
   verdicts, the board's stop-6 capture on the alternation floor alone;
6. `mvp check`, the kexec rehearsal, and `mvp evaluate` pass, with every
   image byte-identical between the development host and the evaluator.

This closes, for this scenario, the three gaps S1 names before any
isolation claim between Linux guests: the shared page and the denial test
on K3 here, K3's `htval` in M0's platform record, and K3's VMID tagging in
M0's probe (MVP plan, M1 "Exit").

## Base and inputs

- **Base:** `beryllium/mvp-m1-plan` from `6f7b6e7c`, the acceptance record
  of the M0 result, which holds accepted B0-B7, S1, S2, the MVP plan, the
  M0 plan with Plan revisions M0-A, M0-B, and M0-C, and the M0 result.
  Implementation would run on `beryllium/mvp-m1` from this plan's
  acceptance record and change `mvp/` in place (MVP plan M0 deliverable
  1), with a counted change table for every changed file in
  `mvp/README.md`.
- **Governing plan:** the [MVP plan](mvp-plan.md) (`93967fba`): M1's
  deliverables 1 to 6 and exit, the hart layout, D1 to D16, Q1 to Q12 at
  their defaults, the harness rules, the method per claim, and stop
  conditions 1 to 7. This plan implements M1 within it; its departures are
  listed in [Accepted decisions M1
  departs from](#accepted-decisions-m1-departs-from).
- **Security model v1** (`0e3eec8b`): Part 1's classes and invariants I1 to
  I12; Part 2's notation and Instance 2; Part 3's analyses; Part 4's
  validate decision (V1), pipeline, and authority report schema; Part 5's
  trigger results; V1 to V4 at their defaults.
- **M0:** the result `b2669725` (parent `13992d6d`; packet `c935a3b4`) and
  the plan `4d129808` with M0-A (`30c5e1a8`), M0-B (`77559def`), and M0-C
  (`260ceba6`): the line, the substrate, the harness, the tool lock and the
  evaluator, the board tools, the board record and platform record
  `mvp/results/20261025-com260/`, and the 43 open items of
  `mvp/README.md`.
- **S1** (`fd670dcd`): H03, H12, H15, H16, H22, H26, H27, H29, H30, H33,
  H39, H43, H44, and H55. **Model 0.1 revision M01-A** (`95ef0f6c`): the
  policy is specification, not trigger-gated; a runtime TE check only if
  its trigger fires. **Model 0.2** (`planning/architecture-model-0.2.md`):
  the separation of proposed, canonical sealed, and derived state, which
  M1's manifest follows in JSON; nothing under `model/` changes.
- **Prior art, not depended on:** Helium's fixed TE PoC in the retained
  `pathfinder/` tree: "Shared object, asymmetric PTEs" (writer `R=1 W=1
  X=0`, reader `R=1 W=0 X=0`) and "Accepted traps" (`HTVAL << 2`
  reconstructs the GPA; `HSTATUS.GVA`; `SEPC`) in
  `pathfinder/docs/concepts.md`, and the offline report of
  `pathfinder/tools/authority-report.c` ("Helium never parses this
  output"). Current Helium lives in `../helium-te-poc`; no Helium claim
  transfers.
- **Reused unchanged:** B6's `guest/b6-kernel.config` and
  `scripts/fetch-linux.sh`, used by path; B0's retention, summary, and
  `mkcpio.py` tools; B2's port inputs; `tools/port.py`, whose output M1
  does not change.
- **External input, never committed:** Linux `v7.2`
  (`8d3ae59288f1e7d58d76558a6ee96d533bc5019f`, tag object
  `237a1c39e8dfd3e1c6f1f023eea37a48ec04cc63`) with its UAPI headers and
  `tools/include/nolibc`, and OpenSBI `v1.6`
  (`bd613dd92113f683052acfb23d9dc8ba60029e0a`) for QEMU. There is no new
  external input: M1's two kernel options are within the pinned tree.
- **Platform facts** (M0's platform record and board record): harts 1 to 7
  `STOPPED` after kexec; harts 0 to 3 in `cluster0` and 4 to 7 in
  `cluster1`, each cluster with one `next-level-cache`; Sv39x4 with 14
  VMID bits, the Sv48x4 and Sv57x4 writes not taken; for a VS-mode load,
  store, and fetch at GPA `0x9000_0000`, `scause` `0x15`, `0x17`, and
  `0x14`, `htval` `0x24000000` (GPA >> 2), `htinst` `0x3303`, `0x3023`,
  and `0x0`, and `gva=1`; IPIs 100 of 100 in HS (median `0x1f` ticks) and
  at V=1 (median `0x21`); 0 stale reads in 10,000 flag-and-payload
  iterations from hart 0 to hart 1, fenced and unfenced; after an unfenced
  `hgatp` switch, tagging by VMID under distinct VMIDs and a translation
  cached under a shared VMID; `hedeleg` reading `0xb15c` (QEMU `0xb15d`);
  in each of four scenario runs, 157 exits and 65 lines per domain,
  `records=138 wakes=2 alternations=125`, `ring_peak` `0x1278` and
  `0x12b0`, and at most 1.696 s; firmware `SBI implementation ID=0x1
  Version=0x10006`, Fedora `7.3.0-65.1.riscv64.omni.fc45.riscv64`, and the
  BSP's U-Boot 2022.10. The preflight of 2026-10-24 records System RAM
  `0x1_0200_0000`-`0x2_ffff_ffff` with no `/proc/iomem` child between
  `0x1_0600_0000` and `0x2_ef44_7fff`.
- **Board tooling:** `k3ctl`, in the responsible human's `k3-com260-info`
  checkout on `l1` (`tools/k3ctl/`): an ESP32-C3 dongle on `/dev/ttyACM0`
  and a standard-library Python client that sends one command line and
  relays one reply (exit status 0 for `OK`, 1 for `ERR`, 2 for a device or
  usage error); [The remote reset](#the-remote-reset) describes it. Its
  README records that "only `reset` has been tested so far" and that an
  `OK` "acknowledges a firmware command, not a verified K3 boot"; the
  firmware source names protocol version `1.0`
  (`firmware/k3ctl/k3ctl.ino:52`), which "does not identify the build".
  On `l1` on 2026-10-26, `reset` answered `OK reset` and Fedora answered
  with a new boot ID about 40 s later; `status` reports `k3=n/a`, no power
  sense being wired. At planning time the client's SHA-256 was
  `7ca3d78a47de404becc6ee8450617dfad4382b7e316e37370f203be6e7eea3ec`.
- **Hosts:** the laptop `lx2` and the workstation `l1` (x86_64, Fedora 44,
  32 CPUs); the tool lock passes on `l1` (29 roles, closure 259,
  `lock_sha256=6e99262f04a1`).
- **Planning reads** (2026-10-26, read-only): the pinned Linux source in
  `build/mvp/linux-src` and M0's built guest `.config`; M0's board record;
  the `k3ctl` README, client, and firmware source. Nothing was built or
  run for this plan.

M0's open items that defer to M1, and what M1 does with each:

| Item | M0 state | M1 | Where |
| --- | --- | --- | --- |
| 37, 39 | The closure is resolved against the host's installed set and pins its security packages, so host updates drift the lock | Unchanged; refreshed only on direction | Q17 |
| 38 | `k3-campaign.sh` prints `STOP` when its wait for a human reset times out | A bounded wait after the tool's own reset, whose timeout is a stop; `PAUSED` on the human path | Q18, M1-5 |
| 40 | OpenSBI's power-on lines are not on this BSP's console; the platform record carries a fixed paragraph written for M0's campaign | M1 needs no PMP layout: the channel page lies in S-mode RAM that the preflight and the loader's layout rule check. The paragraph becomes a per-campaign input written by hand from the operator's picocom log | [Platform record](#platform-record) |
| 42 | The guest `.config` records the host's Rust and pahole versions; `kernel-repro` fails across hosts | Kbuild's `RUSTC`, `BINDGEN`, and `PAHOLE` name no executable | Q16, M1-4 |
| 43 | A stale podman store, moved aside on `l1` | The responsible human's; M1 does not touch it | |

## Architecture

### The policy, the labeling, and the manifest

The scenario's policy is Instance 2 of security model v1, verbatim, in
`mvp/scenarios/te-poc/policy.te`:

```text
type monitor_t;      type writer_t;       type reader_t;
type writer_mem_t;   type reader_mem_t;   type shared_wr_t;
type monitor_mem_t;

class memory  { read write execute map }
class channel { send receive }

allow writer_t writer_mem_t : memory { read write execute map };
allow writer_t shared_wr_t  : memory { read write map };
allow writer_t shared_wr_t  : channel { send };

allow reader_t reader_mem_t : memory { read write execute map };
allow reader_t shared_wr_t  : memory { read map };
allow reader_t shared_wr_t  : channel { receive };
```

Part 2 defines the concrete syntax as one statement per line, while
Instance 2 writes three `type` statements on one line; the parser ends a
statement at `;` (for `type` and `allow`) or `}` (for `class`), so the text
parses verbatim. It also ignores `#` comments and blank lines, a lexical
convenience the notation does not define, used only for the file's SPDX
and copyright header. The policy identity is the SHA-256 of the file's
bytes.

The labeling (`scenario.json`, `labeling`) is Instance 2's, which names
"the monitor's image, pool, staging region, and kexec FDT slot" as
`monitor_mem_t`, extended to the two monitor-owned extents M0 added, the
hart region and the MVP region:

| Subject or object | Class | Extent (HPA, bytes) | Type |
| --- | --- | --- | --- |
| The monitor | subject | | `monitor_t` |
| G0, domain 0, hart 1 | subject | | `writer_t` |
| G1, domain 1, hart 2 | subject | | `reader_t` |
| `g0_window` | `memory` | `0x1_1000_0000`, `0x400_0000` | `writer_mem_t` |
| `g1_window` | `memory` | `0x1_1400_0000`, `0x400_0000` | `reader_mem_t` |
| `shared_page` | `memory` | `0x1_1800_0000`, `0x1000` | `shared_wr_t` |
| `channel0` | `channel` | `shared_page` | `shared_wr_t` |
| `accepted_image` (monitor code and data) | `memory` | `0x1_0200_0000`, `0x3_4000` | `monitor_mem_t` |
| `pool` (both roots, level-1 and level-0 pages) | `memory` | `0x1_0203_4000`, `0x1_0000` | `monitor_mem_t` |
| `hart_region` (M0) | `memory` | `0x1_0204_4000`, `0x2_0000` | `monitor_mem_t` |
| `mvp_region` (M0-A.1) | `memory` | `0x1_0206_4000`, `0x4_0000` | `monitor_mem_t` |
| `staging` | `memory` | `0x1_0800_0000`, `0x40_0000` | `monitor_mem_t` |
| `kexec_fdt` | `memory` | `0x1_0840_0000`, `0x20_0000` | `monitor_mem_t` |

The need sets of A4 (`scenario.json`, `need`) are Instance 2's permission
sets, one per (source, target, class), as Part 3 states for both instances.

The manifest is M1's own (Q8): the scenario's `domains`, `objects`, and
`channels`, read as the canonical sealed state. It holds what Model 0.2's
canonical sealed state lists ("complete resource inventory and extent
ownership; monitor, root, stack, and saved-state exclusion;
domain/vCPU/root/stack/saved-state bindings; explicit channel endpoints and
directional rights"): each domain's window, owner, and rights (`read write
execute`, V4's default), and its binding (hart, VMID, root, block); the
monitor's extents, owned by the monitor and mapped by no root; the channel
page; and `channel0`, whose writer is G0 with `read write` and whose reader
is G1 with `read`, at GPA `0x8400_0000`. The bindings are not governed by
the policy, whose v1 classes have no hart; the hart binding is M3's
security model revision (MVP plan M3 deliverable 1). The manifest identity
is the SHA-256 of the canonical JSON of these three sections (sorted keys,
no insignificant white space), and the labeling identity likewise of
`labeling`.

### The offline pipeline and the authority report

Part 4's pipeline, with the policy at its head and validate, not compile
(V1):

```text
policy.te + labeling + mvp-layout.h
  -> A1 to A6 on the policy and labeling; A7 vacuous      tools/policy-check.py
  -> the manifest (scenario.json domains, objects, channels)
  -> structural checks against mvp-layout.h + A8          policy-check.py, gen-scenario.py
  -> the sealed manifest and the configuration identity
  -> mvp-scenario.h: bindings, windows, channel record, identity, accepted exits
  -> boot: hart 0 builds and re-walks both roots and checks the channel
  -> authority-report.json, matched to the boot lines by check-capture.py
```

`tools/policy-check.py` implements each analysis as Part 3 defines it, as
a pure function over the parsed policy, labeling, need sets, and manifest:

| Analysis | M1's implementation | Instance 2 |
| --- | --- | --- |
| A1 | Parse; every type and class declared before use; every permission in its class; no empty set; every subject and object labeled once with a declared type | Pass |
| A2 | Every rule's source labels a subject, and its target an object of its class | Pass: six rules, all reachable |
| A3 | No rule gives a domain type any permission on `monitor_mem_t`, or `map` on another domain's private type; every `channel` rule has a `memory` rule on the same target for the same source; every target that two sources hold `memory` rules on has a `channel` rule for each | Pass |
| A4 | Every rule's set is within its need set, and every rule has one | Pass, by construction (Part 3) |
| A5 | Every shared writable target has exactly one writer type: "static, not revocable, single writer", which V3 accepts for U2 | Pass: `shared_wr_t`, writer `writer_t` |
| A6 | `F`, `D`, and their transitive closures from the rules; `F+ = D+` | Pass: `F = D = {(writer_t, reader_t)}` |
| A7 | Not implemented: Part 3 calls it vacuous for static instances, so the checker requires its vacuity (no domain holds a `domain` permission, and no delegation exists) and records it as `pass` with the detail `vacuous` | Pass, vacuous |
| A8 | Every ownership, right, and channel endpoint in the manifest is allowed by a rule under the labeling (`map` for presence, `read`, `write`, `execute` for leaf rights, `send` or `receive` for an endpoint) | Pass: six grants, each with its rule |

A7's general check waits for a request vocabulary (MVP plan, "Evaluation
harness"); recording it as vacuous rather than leaving it out keeps the
report within Part 4's rule that any check whose result is not `pass`
describes a configuration that "must not be sealed".

The authority report, `authority-report.json` (schema
`be-mvp-authority-report-v1`, JSON by D9, sorted keys), follows Part 4's
schema: `identity` (`manifest_identity`, `policy_identity`,
`labeling_identity`, and the `configuration_identity` of Q9, the SHA-256 of
the other three digests in that order), `policy` (types, classes, and
rules, each with its text), `labeling`, `subjects` (G0 and G1 with their
types and domain indices), `objects` (each with its class, type, and HPA
extent), `grants`, `flows`, and `checks` (A1 to A8). Each memory grant
also carries what the root builder will derive from it, the GPA, size, and
leaf flags by the fixed table `map` -> `V U A`, `read` -> `R`, `write` ->
`W D`, `execute` -> `X`, which is what the boot lines are matched against.
For Instance 2 the report holds exactly six grants:

| Subject | Object | Class | Permissions | Derived | Source |
| --- | --- | --- | --- | --- | --- |
| G0 | `g0_window` | `memory` | `execute map read write` | GPA `0x8000_0000`, 64 MiB, leaves `0xdf` | `allow writer_t writer_mem_t : memory { read write execute map };` |
| G0 | `shared_page` | `memory` | `map read write` | GPA `0x8400_0000`, 4 KiB, leaf `0xd7` | `allow writer_t shared_wr_t : memory { read write map };` |
| G0 | `channel0` | `channel` | `send` | | `allow writer_t shared_wr_t : channel { send };` |
| G1 | `g1_window` | `memory` | `execute map read write` | GPA `0x8000_0000`, 64 MiB, leaves `0xdf` | `allow reader_t reader_mem_t : memory { read write execute map };` |
| G1 | `shared_page` | `memory` | `map read` | GPA `0x8400_0000`, 4 KiB, leaf `0x53` | `allow reader_t shared_wr_t : memory { read map };` |
| G1 | `channel0` | `channel` | `receive` | | `allow reader_t shared_wr_t : channel { receive };` |

and one flow, from G0 to G1 through `shared_page`, `declared: yes`, which
is A6's `writer_t -> reader_t` at the level of the manifest. A report with
a grant whose `source` is `none`, a flow whose `declared` is `no`, or a
check that is not `pass` stops the build: `gen-scenario.py` writes no
header for such a scenario, so no image exists (Part 4: such a
configuration "must not be sealed"). The monitor never parses the policy,
the labeling, or the report, and never evaluates `decide`; it consumes the
sealed record that the header carries (Part 4: "Nothing in this pipeline
runs in HS").

### What M1 takes from M0 and what it changes

| Area | M0 | M1 |
| --- | --- | --- |
| Hart layout, boot, barrier, rings, IPIs, drain order | Hart 0 controls, harts 1 and 2 run one domain each, 3 to 7 never started by the monitor; M0-C's round-robin drain | Unchanged |
| Scenarios | `two-guests` (schema v1) | `te-poc` (v2) added; `two-guests` unchanged, a QEMU regression |
| Offline checks | None: "no policy or manifest yet" (M0 plan); the stage runs the pin checks | `policy-check.py`, A1 to A6 and A8, the report |
| G-stage | 32 leaves of 2 MiB per root; "no level-0 table, no per-page rights"; the pair check refuses any shared byte | Plus one level-0 page per root and one 4 KiB channel leaf, writer `RW`, reader `R`; the check admits exactly the declared page |
| Accepted exits | VS `ecall` to the SBI subset; the IPI; "anything else" terminal | Per scenario (D8): `te-poc` adds the denial entry |
| Exit record | The R4 frame, then `hstatus`, `htinst`, `vsatp`, `time` | Plus `vsstatus`, the guest's at the exit |
| `vs*` writes after arming | `vstimecmp` by TIME only | Plus `vscause`, `vstval`, `vsepc`, `vsstatus` by the injection helper, once per accepted denial |
| Records | READY, ENTERED, LINE, PONG, SHUTDOWN, FAIL; PING, ACK | Plus outbound DENIAL; SHUTDOWN gains the domain's denial count, which hart 0 reconciles |
| Hart 0's lines | `:01` to `:14` | Unchanged formats; plus `:03 CHANNEL_CHECKED`, `:05 CHANNEL_CLEARED`, and `BE_MVP:DENY` |
| Guest | M0's init: eight steps, a 1 s sleep, power-off | Plus a role from its arguments: the writer's or reader's channel steps and its denied accesses, with a SIGSEGV handler |
| Guest kernel | B6's fragment unchanged | Plus `CONFIG_DEVMEM=y` and `CONFIG_STRICT_DEVMEM=y`; `/dev/mem` in the initramfs |
| Board resets | By the human | By `k3ctl` under Q14's default, or by the human |

### Boot sequence additions on hart 0

M0's boot sequence stands ("Boot sequence on hart 0", steps 1 to 6). Two
of its steps gain the channel; nothing else changes:

- **Step 3, roots.** Hart 0 builds each root with its channel leaf from the
  sealed channel record, re-walks it, and prints that domain's `:03` line
  as M0 does (the window's fields only, so the line is unchanged). It
  then runs the channel check over both walked maps and the sealed record
  ([G-stage and VMIDs](#g-stage-and-vmids)) and prints `BE_MVP:03
  CHANNEL_CHECKED` with the page's GPA, HPA, and size, both level-0 pages,
  both leaf PTEs, and the configuration identity. A refusal is
  `BE_MVP:FAIL gstage` with `BE_MVP:DETAIL channel=0 domain=<d> hart=<h>
  walked=<pte> declared=<pte>`, before any domain runs.
- **Step 3, clears.** After both `:05 DOMAIN_RAM_CLEARED` lines hart 0
  zeroes the channel page and prints `BE_MVP:05 CHANNEL_CLEARED`, so no
  byte from before the kexec reaches either guest and the reader's first
  poll reads zero.
- **Step 4, blocks.** Each block's state page carries the hart's walked map
  with its channel leaf, written by hart 0 before the barrier: the private
  state the hart's denial decision reads.

A scenario without a channel, `two-guests`, builds no level-0 page,
prints no channel line, and boots exactly as in M0.

### The denial path

A domain hart's exit with cause 20, 21, or 23 is decided, in a scenario
whose accepted-exit set names `denial`, by a pure function,
`be_mvp_denial_decide`, in `src/mvp-sbi.c` beside `be_mvp_handle_exit`. It
reads only the exit record the vector saved (captured inputs) and the
hart's private state (its walked map with the channel leaf); it writes
nothing and returns accept, with the record's fields and the values to
inject, or refuse (S1 H22). Placing it in an existing object keeps the MVP
region's explicit input-section patterns (M0-A.1), and so `tools/port.py`,
unchanged.

**The accepted entry.** The decision accepts exactly this, and anything
else is terminal (`BE_MVP:FAIL guest-page-fault` with M0's exit `DETAIL`):

| Field | Accepted | Basis |
| --- | --- | --- |
| `scause` | 20, 21, or 23 | MVP plan M1 deliverable 3 |
| `hstatus.SPV`, `SPVP`, `GVA` | 1, 0, 1: from VU mode, `stval` a guest virtual address | Q4; the vector admits only V=1 exits |
| `htval` | Below 2^39, so the GPA is below Sv39x4's 2^41 | S1 H16's alias-rejecting rule |
| GPA | `(htval << 2) \| (stval & 3)` | M0's platform record: `htval` = GPA >> 2 on K3 |
| `htinst` | Zero; or, for cause 21, a transformed load, and for cause 23, a transformed store or AMO (bit 0 set, bits 6:2 the LOAD, STORE, or AMO major opcode); for cause 20, zero; never a pseudoinstruction | M0's record: `0x3303`, `0x3023`, `0x0` |
| Place | A GPA the root does not map (outside the window and the channel page), for any of the three causes; or cause 23 at a GPA in the channel page of a root whose leaf lacks `W` | Instance 2: absent mappings and the reader's missing `write` |
| `vstvec.MODE` | Direct or Vectored | Below |

A fault from VS mode, a pseudoinstruction (an implicit VS-stage access), a
fetch from the channel page, a fault inside the window, and an `htval` with
an alias bit stay terminal, as M0's are. The decision consults no type,
rule, or policy: only the root the hart installed and the sealed channel
record, so the denial is the absent mapping's, as Part 5 states for U2.

**The injected values** (Q5):

| Target | Value |
| --- | --- |
| `vscause` | 1, 5, or 7 for cause 20, 21, or 23 (instruction, load, store or AMO access fault) |
| `vstval` | `stval`, the faulting guest virtual address |
| `vsepc` | `sepc`, the faulting instruction |
| `vsstatus` | `SPP` = `SPVP` (0, VU), `SPIE` = `SIE`, `SIE` = 0, every other bit as the vector read it |
| Resume | The frame's `sepc` = `vstvec & ~3`; the saved `SPVP` = 1, so the resume tail's single `SRET` enters VS mode at the guest's trap vector |
| Not delivered | `htval`, `htinst`: logged only |

This is the plan's reading of the RISC-V privileged specification (Volume
II, "Hypervisor Extension": "Trap Entry", "Hypervisor Status Register
(hstatus)", "Hypervisor Trap Value Register (htval)", and "Transformed
Instruction or Pseudoinstruction for mtinst or htinst"; and "Supervisor
Trap Vector Base Address Register (stvec)"): a trap taken into VS mode
writes `vscause`, `vsepc`, and `vstval`, sets `vsstatus.SPP` to the
previous privilege, copies `SIE` to `SPIE` and clears `SIE`, keeps V at
1, and sets the PC to `vstvec`'s BASE for every synchronous exception in
either mode. No hardware path delivers a guest-page fault there: `hedeleg`
bits for causes 20 to 23 are read-only zero, and M0 arms `0xb15d`, which
names none of them. The monitor therefore performs the trap entry itself
from HS, as the access fault the guest would take if a physical-memory
check refused the access. `htval` holds the GPA shifted right by 2;
`stval`, with `hstatus.GVA` set, holds the guest virtual address, whose
low two bits are the GPA's; a transformed instruction has bit 0 set, and a
pseudoinstruction has bits 1:0 clear.

Fact (Linux `v7.2`): `arch/riscv/kernel/entry.S:485-493` dispatches causes
1, 5, and 7 to `do_trap_insn_fault`, `do_trap_load_fault`, and
`do_trap_store_fault` (M0's `.config` has `# CONFIG_ERRATA_SIFIVE is not
set`, so the instruction-fault alternative stays); each sends a user-mode
program SIGSEGV with `SEGV_ACCERR` and the faulting PC as `si_addr`
(`arch/riscv/kernel/traps.c:146-160`, `:168-169`, `:196-197`,
`:250-251`), and prints nothing when the program handles the signal
(`traps.c:115-130`); in kernel mode it calls `fixup_exception` or `die`
(`traps.c:132-143`). The entry admits VU-mode faults only, so the guest
kernel never takes an injected fault in kernel mode.

**One executor, in order.** For an accepted denial the domain hart:

1. counts the exit and the denial (`exits` and the new `denials`);
2. writes `vscause`, `vstval`, `vsepc`, and `vsstatus` through
   `be_mvp_arch_inject` in `src/mvp-trap.S`, the only writer of the four
   after arming, which reads each back; C requires the four readbacks to
   equal the values written, else `FAIL controls` with a register `DETAIL`;
3. posts one DENIAL record, publishes the ring with `fence w, w`, and sends
   hart 0 one IPI; a ring that refuses the record is `FAIL ring` by M0's
   fallback path;
4. sets the frame's `sepc` and saved `SPVP` and resumes through M0's tail,
   which writes no `vs*` CSR, `hgatp`, or fence.

A DENY line therefore implies that the injection's readback passed and
that the record existed before the guest ran again (MVP plan: the guest
resumes "only when every recorded field matches the accepted entry"). The
path writes no `hgatp`, executes no fence, takes no lock, and touches no
other hart's block.

**The DENIAL record** carries twelve words: the domain's denial sequence
number from 1, the cause, the kind (`unmapped` or `read-only`), the GPA,
`htval`, `htinst`, `stval`, `sepc`, the guest's `vsstatus` at the exit,
`vstvec`, the injected `vscause`, and the exit's time; its header time is
the post. At 112 bytes with its header it fits a ring record's 256-byte
payload limit.

### Control loop and failure paths

Hart 0's control loop (M0, "Control loop", with M0-C's drain) gains one
step: a DENIAL record, valid only between its domain's ENTERED and
SHUTDOWN records, whose sequence number is the domain's previous one plus
1, whose injected cause matches its cause, and whose kind fits its GPA
against the sealed record, prints one `BE_MVP:DENY` line and counts it;
anything else is `FAIL ring`. A SHUTDOWN's new denial word must equal the
number of DENIAL records drained for that domain, else `FAIL ring`. The
`:12` and `:13` formats do not change: the capture checker counts the DENY
lines itself, and `:13`'s `records` counts DENIAL records as it counts
every drained record. The failure paths are M0's; M1 adds no class.

### Guest controls and the CSR inventory

| State | M0 | M1 | Checked |
| --- | --- | --- | --- |
| `vscause`, `vstval`, `vsepc`, `vsstatus` | Written once by the arm helper | Also by the injection helper, once per accepted denial | The helper's readback; the image checker's writer table |
| `vsstatus` read | At arming | Also by the vector, at every exit | The image checker: the vector's words |
| `vstvec`, `vsie`, `vsscratch`, `vsatp`, `scounteren`, `senvcfg` | Once at arming | Unchanged | As M0 |
| `hgatp` | Once per hart, before the barrier | Unchanged; never on the denial path | Install readback; resume; single-writer rule |
| `hvip` | VS bits tested zero | Unchanged: no interrupt is injected | Arm, resume |
| Every other control | M0 | Unchanged | M0 |

### Port and copies

M1 adds no port rule and no C object to the monitor: `tools/port.py
--check` re-derives the same 32 files (`BE_MVP_PORT: CHECK PASS files=32
changed=2 rules=12 substitutions=14`). The channel page lies outside the
flat image, like the windows, and the level-0 pages lie in the pools'
NOLOAD bytes, so the linker script and the flat image (`0xa4000` bytes) do
not change. Each changed file gets a counted change table in
`mvp/README.md`:

| File | M1's change |
| --- | --- |
| `src/mvp-layout.h` | The channel's GPA, HPA, and size; the level-0 offset in each pool; static assertions: the page outside every other extent, above G1's window, and inside the windows' root entry and level-1 table |
| `src/mvp-gstage.{h,c}` | The channel in the descriptor and the walked map; the builder's level-1 pointer and level-0 leaf; the walker's one new rule; the channel check |
| `src/mvp.h`, `src/mvp-sbi.c` | The exit record's `vsstatus`; the `denials` counter; the DENIAL record and its codec; the denial action and `be_mvp_denial_decide`; SHUTDOWN's denial word; the accepted-exit set from the scenario header |
| `src/mvp-hart.{h,c}` | The control loop's DENIAL step and the SHUTDOWN reconciliation |
| `src/mvp-runtime.c` | The channel's build, check, and clear on hart 0; the channel in each block's map; the three new lines |
| `src/mvp-hartmain.c`, `src/mvp-platform.h` | The denial action's executor; the hart page's map with its channel leaf |
| `src/mvp-trap.S` | The vector's `vsstatus` word; `be_mvp_arch_inject` |
| `src/mvp-payload.c` | The channel page in the staged image's disjointness set |
| `tools/gen-scenario.py`, `tools/gen-dts.py` | Schema v2; the policy check before any header; the channel record, identity, and accepted exits in `mvp-scenario.h`; the init arguments in each DTB's `bootargs` |
| `tools/policy-check.py`, `scenarios/te-poc/` | New: the offline checker; `scenario.json` and `policy.te` |
| `guest/mvp-init.c`, `guest/mvp-guest-id.h`, `guest/initramfs.list.in`, `guest/mvp-kernel.config` (new), `guest/pins.txt`, `tools/build-guest.sh`, `guest.mk` | Roles, the handler, and reports; `/dev/mem`; the two options and the `.config` delta check; Q16; the new pins |
| `tests/deny-test.c` (new), `tests/{gstage,sbi,hart}-test.c` | Host tests |
| `tests/check-image.py`, `tests/check-capture.py`, `tests/run-qemu.sh`, `tests/kexec-rehearsal.sh` | Rules, mutations, fixtures, and runs |
| `tools/kexec-load.py`, `tests/test-kexec-load.py`, `tools/k3-preflight.sh` | The channel page as an MVP extent; the firmware identity |
| `tools/k3-run.sh`, `tools/k3-campaign.sh`, `mvp`, `tools/k3ctl.sha256` (new), `tests/fake-board.py`, `tests/fake-k3ctl.py` (new), `tests/run-tool-dry-run.sh` | The remote reset and its dry run; Q18 |
| `tools/evidence.py`, `tools/platform-record.py` | The report and the policy check in bundles; M1's platform-record additions |
| `Makefile`, `tools.mk`, `tools/make-control.py` | Targets; the board variants `reader-write` and `no-inject` |

### Budgets

Every budget is hard; an overrun is a [stop](#stop-conditions).

| Budget | Limit | Basis |
| --- | --- | --- |
| Monitor text: the accepted code and the MVP assembly | Below `0x1_0200_8000` (accepted `ASSERT`) | Fact (M0 README, "Budgets (measured)"): GCC ends at `0x1_0200_4540` (`0x3ac0` spare), Clang at `0x1_0200_4770` (`0x3890`). Inference: the injection helper and the vector's one more word add under `0x100` |
| MVP region: text, rodata, data, BSS | At most `0x4_0000` | Fact: M0's scenario images use `0x5eb0` (GCC) and `0x6410` (Clang). Inference: the decision, the channel walk and check, and the DENIAL codec and step add `0x1000` to `0x2000` |
| Accepted data; pool; hart region; flat image | At or below `0x1_0200_f000`; `0x1_0000`; `0x2_0000`; exactly `0xa4000` | Unchanged: the level-0 pages use the pools' spare bytes |
| Channel page | Exactly `0x1000` at `0x1_1800_0000`; one per scenario | Q1 |
| Kernel `Image`, DTBs, boot image | File at most 4 MiB and `image_size` at most 8 MiB; two of exactly 4 KiB; at most 4 MiB | Fact (`guest/pins.txt`): 1,553,332 bytes, `image_size` `0x1af628`. Inference: `/dev/mem` and the init add a few KiB |
| Exits | 2^20 per domain | Fact: 157 per domain on the board. Inference: M1 adds one or two denial exits and a few DBCN writes |
| Denials | Exactly the scenario's: 1 for G0 and 2 for G1 | Q3; the capture checker |
| Outbound ring high-water mark | At most half of 32 KiB | Fact: `0x1278` and `0x12b0` on the board. Inference: at most `0x2a0` more, two DENIAL records and three report lines |
| Run time | 2^32 ticks | Fact: at most 1.696 s on the board. Inference: the reader's poll is bounded at 10 s and normally ends at once |
| Remote reset | One per run; Fedora's new boot ID within `K3_RESET_RETURN_SECONDS` (300 s) | Fact: about 40 s on 2026-10-26 |
| Checking code | `policy-check.py` at most 900 lines with its self-test and mutations; the line's checking code at most 2.2 lines per monitor line | Fact (M0 result, section 6): 8,562 monitor lines and 15,389 checking lines, 1.80 per monitor line (B7: 2.68); S1 H43 |

The checking budget is the scope guard of S1 H43 and MVP plan stop 6:
inference, M1 adds about 600 to 700 monitor lines and 2,300 to 2,700
checking lines (the checker, host tests, image and capture rules, the
dry-run cases), which keeps the ratio near 1.9. The result packet reports
the ratio for the line and for M1's increment.

## Memory and load paths

| HPA | Use | Basis |
| --- | --- | --- |
| `0x1_0000_0000`-`0x1_01ff_ffff` | OpenSBI 1.6, no-map | B0-B7 and M0 records |
| `0x1_0200_0000`-`0x1_020a_3fff` | Monitor flat image: the accepted `0x34000` bytes, the pool, the hart region, the MVP region | M0, M0-A.1 |
| `0x1_0203_4000`-`0x1_0204_3fff` | Pool: G0's root `0x1_0203_4000`, level-1 `0x1_0203_8000`, level-0 `0x1_0203_9000`; G1's root `0x1_0203_c000`, level-1 `0x1_0204_0000`, level-0 `0x1_0204_1000` | M0; the level-0 pages are new uses of spare bytes (Q1) |
| `0x1_0204_4000`-`0x1_0206_3fff` | Hart region: block 0 (hart 1), block 1 (hart 2) | M0 |
| `0x1_0206_4000`-`0x1_020a_3fff` | MVP region | M0-A.1 |
| L = `0x1_0800_0000`; the kexec FDT at `0x1_0840_0000` | Staging | M0's load checks |
| `0x1_1000_0000`-`0x1_13ff_ffff` | G0's window, `writer_mem_t` | M0 |
| `0x1_1400_0000`-`0x1_17ff_ffff` | G1's window, `reader_mem_t` | M0 |
| `0x1_1800_0000`-`0x1_1800_0fff` | The channel page, `shared_wr_t` | New (Q1) |

Each guest sees M0's layout, its window at GPA `0x8000_0000`-`0x83ff_ffff`
(kernel at `0x8020_0000`, DTB at `0x83e0_0000`), plus the channel page at
GPA `0x8400_0000`-`0x8400_0fff`; nothing else is mapped. The guest's DT is
M0's, with one memory node for the window and no other node: the page is
not RAM to Linux, and the guest programs learn its GPA from their
arguments. Fact (preflight of 2026-10-24): System RAM spans
`0x1_0200_0000`-`0x2_ffff_ffff`, and no `/proc/iomem` child or FDT
reservation lies between `0x1_0600_0000` and `0x2_ef44_7fff`, so the page
is in free RAM; the preflight and the loader's layout rule check it again
before every load, as an MVP extent. The board path is M0's: Linux
`kexec_load` from Fedora through `tools/kexec-load.py` for every run;
QEMU boots the boot ELF directly with `-smp 8 -m 8G`. No U-Boot run.

## G-stage and VMIDs

M0's builder and walker map each window as 32 leaves of 2 MiB in one
level-1 table under a 16 KiB root. The walker accepts "exactly one root
entry", "only exact 2 MiB leaves forming one contiguous linear run", and
"zero in every other pool byte" (`src/mvp-gstage.h`); each 32 KiB pool is
the root at `+0x0`, the level-1 page at `+0x4000`, and 12 KiB of spare
bytes from `+0x5000` (`BE_MVP_GSTAGE_SPARE_OFFSET`) that must be zero. M1
maps the channel through the first spare page:

- the channel's GPA `0x8400_0000` lies under the windows' root entry
  (index 2) and in their level-1 table, at index 32, after the window's
  leaves at 0 to 31;
- level-1 entry 32 becomes a pointer to the level-0 page at pool +
  `0x5000`: G0's `0x1_0203_9000` (PTE `0x4080e401`) and G1's
  `0x1_0204_1000` (PTE `0x40810401`);
- level-0 entry 0 is the one 4 KiB leaf, to HPA `0x1_1800_0000`: the
  writer's `0x460000d7` (`V R W U A D`) and the reader's `0x46000053`
  (`V R U A`), the rights the report derives from `read write` and
  `read`; the other 511 entries are zero, so GPA `0x8400_1000` and every
  other page of that 2 MiB region fault;
- the pool's bytes from `+0x6000` stay spare and zero.

`U` is set because every G-stage access counts as a user access, and `A`
(and `D` where `W` is granted) so that no access depends on hardware
updating them; no leaf carries `X`, `G`, PBMT, `N`, or reserved bits, as
in Helium's asymmetric PTEs with `X` clear in both. The window's leaves
keep `0xdf`.

**The walker** gains one rule and no other: besides the window's run, it
accepts at most one level-1 pointer, at the channel's level-1 index, to
this pool's level-0 page, and in that page exactly one leaf, at the
channel's level-0 index, whose PPN is the channel's HPA and whose flags are
`V U A R`, with `W D` or without both, never `X`. It records the leaf in
the walked map and refuses anything else: a second pointer, a pointer
elsewhere, a second leaf, a leaf with any other bit. It does not compare
the leaf's rights with the declared rights; the channel check does, from
the walked bytes, so that a defective builder is caught by a check that
shares none of its code (the `reader-write` image).

**The channel check** extends M0's pair check (`be_mvp_gstage_pair_check`,
a counted copy of B7's, which "refuses shared pages"). Over both walked
maps and the sealed channel record it requires M0's rules (pools disjoint,
windows disjoint, no window over a pool, distinct nonzero VMIDs, distinct
harts other than hart 0, distinct `hgatp` values), plus: neither window
over the channel page, which covers no pool; with no channel declared, no
level-0 leaf in either map; with one declared, both maps holding its leaf
at the declared GPA and the same HPA, the writer's flags exactly `0xd7`
and the reader's exactly `0x53`, from the record's rights by the report's
table. Every page the two roots share is then the declared channel page
with its declared rights, and everything else is refused (MVP plan M1
deliverable 2). The check is pure C over walked bytes and sealed values,
host-tested with every refusal.

**VMIDs** are M0's: `hgatp` `0x8000100000102034` for G0 on hart 1 (VMID 1)
and `0x800020000010203c` for G1 on hart 2 (VMID 2), each installed once
through the accepted install function and read back before the barrier,
and checked at every resume; after the barrier no hart writes `hgatp`,
the denial path included, which the image checker enforces as a
single-writer rule. The invariant MVP plan M1 deliverable 4 restates
holds: each root is installed on exactly one hart, under exactly one VMID,
for the whole run (Q15). The roots never change after the barrier, so no
TLB shootdown exists; the two harts' translations of the page live in
their own VMID-tagged TLBs.

## Guest SBI subset and the firmware surface

The guest sees M0's subset unchanged: Base (implementation ID `0x4245`,
version 3), TIME `set_timer` into the hart's `vstimecmp`, DBCN write from
the domain's walked window (read returns -4), and SRST shutdown with
reason 0; every other call returns -2. DBCN reads only the window, never
the channel page, whose GPA lies outside the walked window that
`be_mvp_gstage_translate` serves. The monitor's own firmware calls stay
M0's: Base, DBCN write, SRST, HSM `hart_start` and `hart_get_status`, and
IPI `send_ipi`, all through the accepted `be_r3_arch_sbi_call`.

The implementation version stays 3 (Q19): M1 changes no SBI extension,
function, argument, or result, and the guest's expected line `SBI
implementation ID=0x4245 Version=0x3` is unchanged.

## Guest software

- **Kernel:** M0's uniprocessor Linux `v7.2` `Image`, from B6's fragment,
  unchanged and used by path, merged first, then M1's
  `guest/mvp-kernel.config`, which holds exactly `CONFIG_DEVMEM=y` and
  `CONFIG_STRICT_DEVMEM=y` (Q2). `tools/build-guest.sh` requires every
  value of both fragments in the final `.config` and compares it with the
  `.config` that B6's fragment alone gives from the same tree: inference
  from the Kconfig sources, the only differences are those two lines and
  `# CONFIG_IO_STRICT_DEVMEM is not set`, which becomes visible under
  STRICT; `CONFIG_EXCLUSIVE_SYSTEM_RAM=y` stays, because its condition
  `!DEVMEM || STRICT_DEVMEM` still holds (`mm/Kconfig:508-510`). Any other
  difference is stop condition 5. The guest build passes Kbuild's
  `RUSTC`, `BINDGEN`, and `PAHOLE` (`Makefile:549-554`) naming no
  executable, so Kconfig's probes (`scripts/Kconfig.include:71-72`,
  `init/Kconfig:63-70` and `:196-198`) record the same values on every
  host (Q16; open item 42). The rebuilt outputs get new pins;
  `kernel-repro` passes on `l1` and across `lx2` and `l1`.
- **Why `/dev/mem`.** Fact: `DEVMEM` is `default y`
  (`drivers/char/Kconfig:259-266`) but off in M0's tinyconfig-based
  `.config` (`# CONFIG_DEVMEM is not set`); `STRICT_DEVMEM` defaults to
  `y` only on PPC, x86, arm64, and s390 (`lib/Kconfig.debug:1962-1966`),
  and RISC-V selects the generic `devmem_is_allowed`
  (`arch/riscv/Kconfig:122`), which refuses an exclusive I/O range and
  RAM and allows anything else (`lib/devmem_is_allowed.c:21-28`).
  `/dev/mem`'s `mmap` remaps the requested physical range
  (`drivers/char/mem.c:325`), and opening it needs `CAP_SYS_RAWIO`
  (`:603-610`), which `/init` has. With both options the init can map the
  channel page and the denied addresses, none of them RAM to the guest, and
  nothing of the guest's own RAM. The alternatives: `CONFIG_DEVMEM=y`
  alone, one line, but `/dev/mem` would then reach the guest kernel's own
  memory; UIO (`CONFIG_UIO`, `CONFIG_UIO_PDRV_GENIRQ`, a module parameter,
  and a device node in a guest DT that has none); a driver or a kernel
  patch, which ends the guest's status as unmodified upstream Linux, an
  external input never committed; `memmap=`, which `v7.2` parses only on
  MIPS, x86, and Xtensa (`arch/mips/kernel/setup.c:418`,
  `arch/x86/kernel/e820.c:1012`, `arch/xtensa/mm/init.c:180`); and a DT
  memory node over the page, which would make the page Linux's RAM to
  allocate and write, so the reader's kernel would fault on its own write.
  The guest kernel has no `CONFIG_RISCV_ISA_SVPBMT` (M0's `.config`), and
  `henvcfg.PBMTE` is clear, so `/dev/mem`'s non-cached attribute adds no
  PBMT bit: inference, the page has DRAM's attributes on both harts.
- **Userland:** M0's `nolibc` init, `/init`, with M0's lines and steps. Its
  arguments (`-- be.guest=<g>` and, for `te-poc`, `be.role=`,
  `be.channel=`, and `be.deny=`; [Scenarios and the
  harness](#scenarios-and-the-harness)) select a role; without
  `be.role=`, as in `two-guests`, it runs exactly M0's lines. The role's
  steps run after `MVPINIT 02` and before the first `STEP`:
  - **Writer (G0):** maps the channel page through `/dev/mem`
    (`MAP_SHARED`, read-write), writes a 4,088-byte pattern from a fixed
    xorshift seed at offsets `0x8`-`0xfff`, executes `fence w, w`, writes
    the flag `0x42454d314348414e` (ASCII `BEM1CHAN`) at offset 0, reads the
    pattern back, and prints `MVPINIT 07 CHANNEL role=writer` with its
    64-bit FNV-1a digest. It then makes its listed denial, a load from a
    page it mapped read-only at GPA `0x8400_1000`.
  - **Reader (G1):** maps the channel page read-write, so that its store
    passes the VS stage and reaches the G-stage; polls the flag at most
    10 s of `CLOCK_MONOTONIC`, 1 ms apart; executes `fence r, r`; reads the
    pattern; and prints `MVPINIT 07 CHANNEL role=reader` with its digest,
    the polls, and `match=1` when the digest equals the one computed from
    the seed. It then stores at GPA `0x8400_0ff8` and reads that word back,
    which must still be the writer's (`unchanged=1`), and loads from GPA
    `0x9000_0000`, a page it mapped read-only.
  - **Denials:** before its first denied access the init installs a
    SIGSEGV handler. Fact: `nolibc` in `v7.2` has no `sigaction`
    (`tools/include/nolibc/signal.h` defines only `raise`), but its
    `sys.h:17` includes `<linux/signal.h>`, which gives the UAPI `struct
    sigaction` (`include/uapi/asm-generic/signal.h:75-82`, no `sa_restorer`
    on RISC-V, which defines no `SA_RESTORER`), and `sys/syscall.h:18`
    provides `syscall()`; the kernel returns from a handler through the
    vDSO's `rt_sigreturn` (`arch/riscv/kernel/signal.c:438-439`), which
    M0's guest kernel builds. So the init calls `rt_sigaction` directly
    with `SA_SIGINFO`. Each denied load or store is one fixed 4-byte
    instruction at a global label (`.option norvc`); the handler records
    `si_signo`, `si_code`, `si_addr`, and the `ucontext`'s `pc`
    (`sc_regs.pc`, the first word of `struct sigcontext`), and moves `pc`
    past the instruction. Each denial prints `MVPINIT 08 DENIED`, in the
    order the accesses were made.
  - **No fetch.** Fact: RISC-V Linux runs `flush_icache_pte` for every
    executable PTE it installs (`arch/riscv/include/asm/pgtable.h:622-628`),
    and that reads and sets a flag in the PTE's `struct page`
    (`arch/riscv/mm/cacheflush.c:100-108`); `/dev/mem`'s `mmap` installs
    its PTEs through `set_pte_at` (`mm/memory.c:2929`); and the guest
    kernel is `CONFIG_FLATMEM=y` (M0's `.config`), whose `mem_map` has no
    entry for a page outside the guest's RAM. Inference: mapping
    `0x8400_1000` executable would make the guest kernel write outside
    `mem_map`, so no guest program fetches from a denied page, and cause
    20 is exercised by `tests/deny-test.c` only (Q3).
  - **Result:** `MVPINIT 05 RESULT pass` additionally requires a valid
    role and arguments; for the writer a digest equal to the seed's; for
    the reader the flag within 10 s and `match=1`; and for every listed
    denial exactly one signal with `si_signo` 11 (SIGSEGV), `si_code` 2
    (`SEGV_ACCERR`), and `si_addr` equal to the address of the access's own
    instruction, the program then continuing, and `unchanged=1` after the
    store.
- **Device trees:** M0's template; each `te-poc` DTB differs from its
  `two-guests` counterpart only in `bootargs`, which carry the init's
  arguments, and is pinned.
- **Reference boot:** M0's, on the `two-guests` DTBs under plain OpenSBI
  `v1.6`; the `te-poc` DTBs run only under the monitor, because their
  roles' denials need its G-stage.

## Scenarios and the harness

A scenario stays data (MVP plan, "Evaluation harness"; M0 Q9). M1's
scenario is `te-poc`, in `scenarios/te-poc/` as `scenario.json` (schema
`be-mvp-scenario-v2`, Q10) and `policy.te`. Version 2 keeps every v1
field and adds:

```text
policy          "policy.te"
labeling        subjects and objects -> types (the labeling table above)
need            [ { source, target, class, permissions } ]   (A4)
objects         [ { name, class, hpa, bytes, owner } ]       (monitor extents, shared_page)
channels        [ { name, object, gpa, writer, reader, writer_rights, reader_rights } ]
accepted_exits  M0's classes plus "denial"                   (D8: per scenario)
domains[].role  "writer" | "reader"                          (passed to /init)
domains[].deny  [ { access, gpa } ]                          (passed to /init)
expect.denials  per domain: [ { seq, access, kind, gpa } ]
expect.report   grants 6, flows [ G0 -> G1 via shared_page ]
```

The domains are M0's binding (G0 on hart 1, VMID 1, root `0x1_0203_4000`;
G1 on hart 2, VMID 2, root `0x1_0203_c000`; the windows of
[Memory and load paths](#memory-and-load-paths)). Their `bootargs` are
M0's with the init's arguments:

```text
G0  earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1 -- be.guest=0 be.role=writer be.channel=0x84000000 be.deny=load@0x84001000
G1  earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1 -- be.guest=1 be.role=reader be.channel=0x84000000 be.deny=store@0x84000ff8,load@0x90000000
```

`tools/gen-scenario.py` runs `policy-check.py` first, writes no header
unless it passes, and then emits `mvp-scenario.h` (the binding, the
channel record, the configuration identity, and the accepted-exit set),
the DTBs' `bootargs`, and one expectation file per image. `two-guests`
(v1) keeps M0's expectation files byte for byte; its header differs only
by declaring no channel and no denial entry.

**Expectations.** M0's control lines and per-domain chains, with
`name=te-poc`, `BE_MVP:03 CHANNEL_CHECKED` after the two `:03` lines, and
`BE_MVP:05 CHANNEL_CLEARED` after the two `:05` lines; each domain's M0
lines with its own command line, plus `MVPINIT 07` and its `MVPINIT 08`
lines after `MVPINIT 02`; M0's rejected substrings, which include
`unhandled signal` and `segfault`, so an unhandled denial fails the run;
M0's counters (`ipi` 1, `time` 0, `dbcn_byte` 0, `srst` 1, `refused` 0,
`exits` and `ring_peak` in range); `exits = sbi + ipi + denials` per
domain; exactly one denial for G0 and two for G1; and M0's concurrency
floors, the overlap of at least half the shorter interval and K = 8
alternations, which M1's denials and channel lines do not change.

**The denial log against the guests' reports.** For each domain d, let
the DENY lines naming d, in capture order, be D1 to Dn, its `MVPINIT 08`
lines R1 to Rm, and the scenario's expected denials E1 to Ek. The capture
checker requires n = m = k, and for each i:

1. Di's `seq` is i, and Di appears in the capture before Ri: the record
   precedes the resume, and the report follows the handler;
2. Di's `gpa` equals Ri's and Ei's, and Di's `htval` equals Ei's GPA
   shifted right by 2, compared as 64-bit values (S1 H16's alias-rejecting
   comparison); Di's `stval` equals Ri's `va`, and Di's `sepc` equals Ri's
   `pc` (Linux's `si_addr` for an access fault is the faulting PC);
3. Di's `cause` and `injected` are 20 and 1, 21 and 5, or 23 and 7 for
   Ri's and Ei's `kind` of `fetch`, `load`, or `store`; Di's `kind` is
   Ei's (`unmapped`, or `read-only` for the store); Di's `htinst` is zero
   or the transformed encoding of the init's instruction for that access;
4. Ri shows `signo=11`, `code=2`, `observed=1`, and, for the store,
   `unchanged=1`; every Di of d shows the same `vstvec`, in Direct mode.

**The channel and the report.** The writer's and the reader's `MVPINIT 07`
digests are equal and the reader shows `match=1`; `BE_MVP:03
CHANNEL_CHECKED` shows the report's channel GPA, HPA, and size, both
level-0 pages, leaf flags equal to the report's derived flags for G0's and
G1's `shared_page` grants, and `config` equal to the report's
configuration identity; each `:03 GSTAGE_BUILT_REWALKED` line shows its
window grant's GPA, HPA, and size. The checker reads the report given with
`--report` and checks it too: six grants, each with its rule, one declared
flow, every check `pass`.

**Negative images** (S1 H27), each separately built, none selectable at run
time:

| Variant | How it is made | Where | Expected |
| --- | --- | --- | --- |
| `undeclared-flow` | `te-poc`'s policy plus `allow reader_t shared_wr_t : memory { write };` | Host and evaluator | The build stops at the offline check: A6 fails (the undeclared flow `reader_t -> writer_t` through `shared_wr_t`), as do A5 (two writers) and A4 (`write` outside the reader's need); every other analysis passes; no header or image |
| `grant-without-rule` | `te-poc`'s manifest with the reader's rights on `channel0` widened to `read write` | Host and evaluator | A8 fails alone: the report holds a grant with `source: none` and a flow G1 to G0 with `declared: no`; no header or image |
| `reader-write` | The root builder writes `W` and `D` into the reader's leaf (a compile-time switch in `mvp-gstage.c`); the sealed record is unchanged | QEMU (GCC, Clang), board (GCC) | Both `:03 GSTAGE_BUILT_REWALKED` lines, then `BE_MVP:FAIL gstage` and `BE_MVP:DETAIL channel=0 domain=1 hart=2 walked=0x460000d7 declared=0x46000053`; no `:03 CHANNEL_CHECKED`, and no domain runs |
| `no-inject` | `te-poc` with `denial` removed from its accepted-exit set | QEMU (GCC, Clang), board (GCC) | The first guest-page fault ends the run: `BE_MVP:FAIL guest-page-fault` with M0's exit `DETAIL`, either domain 0 with cause `0x15` and `htval=0x21000400` or domain 1 with cause `0x17` and `htval=0x210003fe`; no `BE_MVP:DENY` and no `MVPINIT 08` line |

The two build-time negatives never produce an image, so the MVP plan's
"run on the board as well as in QEMU" applies to the other two; their
evidence is the build's refusal, on the host and in the evaluator.

**QEMU:** M0's machines, `-smp 8 -m 8G`, QEMU 10.2.2, OpenSBI `v1.6`
`fw_dynamic`, each attempt judged by the capture checker and a refused
domain-hart boot made again, as M0:

| Scenario or variant | Machines | Toolchains | Expected |
| --- | --- | --- | --- |
| `te-poc` | `k3-like`, `rva23`, `plic` | GCC, Clang | Pass |
| `reader-write`, `no-inject` | `k3-like` | GCC, Clang | As declared above |
| `two-guests`, its negative variants, `shim-rule`, and the three probe images | As M0 | As M0 | As M0 |

That adds ten runs to M0's 34. The kexec rehearsal runs both `te-poc` boot
images under QEMU with eight harts.

**Mutations** (S1 H39), each a single seeded defect that one named claim
must reject, kept in each checker as M0 keeps them:

| Mutation | Checker | Claim that must fail |
| --- | --- | --- |
| A DENY line's `gpa` changed | capture | The log carries the fields the guest reports |
| A DENY line removed | capture | Every denied access appears exactly once |
| A DENY line duplicated | capture | Exactly once |
| A load's `injected=0x7` | capture | Delivered as the corresponding access fault |
| G1's two DENY lines swapped | capture | In the order the guest reports them |
| `kind=read-only` at a GPA outside the channel page | capture | The kind follows the sealed record |
| A guest report's `pc` changed | capture | The guest observed the logged fault |
| A DENY line moved after its report | capture | The record precedes the resume |
| `htval` with bit 39 set | capture | The alias-rejecting comparison |
| The reader's `match=0`, or the digests differing | capture | Data crosses from the writer to the reader |
| The reader's `unchanged=0` | capture | The denied store changed nothing |
| `reader_pte=0x460000d7` | capture | The reader's root maps the page read-only |
| One digit of `config` changed | capture | The boot-time re-walk is the report's configuration |
| A report with a seventh grant | capture | Exactly Instance 2's grants |
| A report flow with `declared: no` | capture | One flow, `writer_t -> reader_t`, declared |
| A rule naming an undeclared type; an object left unlabeled | policy | A1 |
| A rule whose target labels no object | policy | A2 |
| `allow writer_t reader_mem_t : memory { map };`, need included | policy | A3 alone |
| The writer's channel rule widened to `{ send receive }` | policy | A4 alone |
| A reader `write` rule on `shared_wr_t`, need included | policy | A5 and A6 |
| The manifest granting G0 `execute` on `shared_page` | policy | A8 alone |
| A `vscause` write outside the injection helper | image | One writer of the injected CSRs |
| A second call site of the injection helper | image | One executor |
| An `hgatp` write on the denial path | image | No `hgatp` write after the barrier |
| The channel page inside G1's window | image | The channel is disjoint from every other extent |
| The linked identity differing from the report | image | The image carries the checked configuration |
| A level-0 page holding a second leaf; the reader's leaf with `W`; a second page both roots map | host (`gstage-test.c`) | The walker's rule; every shared page is the declared channel with its declared rights |

**Evidence:** `mvp evidence` adds the policy check's output, the authority
report, and the scenario's `policy.te` to the bundle under its manifest;
the board record adds them likewise, with the runs' reset records
([Platform record](#platform-record)). No recorded path is ever executed
(S1 H30).

The harness stages, as M1 changes them:

| Stage | M1 |
| --- | --- |
| Scenario | `te-poc` (v2); `two-guests` (v1) unchanged |
| Offline checks | `policy-check.py`: A1 to A6 and A8, A7 vacuous, the report; a failing check stops the build; the two build-time negatives |
| Build | M0's, with the generated channel record, identity, and accepted exits |
| Run | Host tests; QEMU with eight harts; the kexec rehearsal; RAM-only board runs with one reset each, by `k3ctl` (Q14) or by hand |
| Check | M0's rules, the reconciliation above, and the channel line against the report |
| Evidence | The report and the policy check in every bundle and board record |
| Mutation | The table above, before the result packet |
| Costs | M0's, plus each denial's service ticks (post minus exit) and each reset's seconds to Fedora's new boot ID; recorded only |

## Tool lock and the clean evaluator

- **The lock** (`tools/lock/tool-lock.conf`, schema `be-mvp-tool-lock-v2`)
  keeps M0's 29 roles: 26 checked in the evaluator, with `podman`, `ssh`,
  and `scp` host-only (M0-B.4). M1 adds none. The offline checker is
  Python 3, a locked role, with the standard library only; the policy, the
  labeling, and the report need no other tool, and there is still no
  Node.js. A refresh runs only on the responsible human's direction, as in
  M0 (Q17).
- **The evaluator** is M0-B's: the digest-pinned Fedora base, the
  259-package closure with a SHA-256 per RPM, built from the verified
  cache with every repository disabled. `mvp evaluate` runs `mvp check`
  inside, now with the policy checks, the build-time negatives, and the
  `te-poc` images and runs, and requires every image to equal the host's
  byte for byte.
- **`k3ctl` is not a lock role.** A role is an RPM-owned executable whose
  record ends in its package's NEVRA (`rpm -qf`), which is why `ssh` and
  `scp`, RPM-owned board tools, are host-only roles; the `k3ctl` client is
  a script in a separate checkout that no package owns, and the evaluator
  never runs it. It is pinned instead: `tools/k3ctl.sha256` holds its
  SHA-256, recorded at M1-5 from the client the responsible human
  designates, and the campaign tool refuses a client that differs before it
  sends anything. The tool runs it with the locked Python 3
  (`python3 -B <client>`), and records its SHA-256 and the dongle's replies in every
  run and in the board record. The dongle's firmware is outside the lock
  and is recorded by the protocol version its replies carry (`1.0`), which
  its README says "does not identify the build".

## Platform record

M0's platform record (`mvp/results/20261025-com260/platform-record.md`
and `.json`) stands as M1's platform input (Q13). M1's board record gets
its own platform record, from `tools/platform-record.py` with these
additions, each a recorded fact and none a claim:

- **Preflight:** the channel page against `/proc/iomem` and the FDT
  reservations, as an MVP extent; the firmware identity from Fedora's log,
  compared with M0's record; the Fedora kernel release.
- **Denials on K3:** for each `te-poc` run, each DENY line's fields (cause,
  kind, GPA, `htval`, `htinst`, `stval`, `sepc`, `vsstatus`, `vstvec`, the
  injected cause, the service ticks) beside the guest's report: K3's
  `htinst` for VU-mode accesses through Linux's VS stage, which M0's probe,
  run in VS mode with `vsatp` Bare, did not record.
- **The channel:** each run's `:03 CHANNEL_CHECKED` line and the readers'
  polls and digests.
- **Resets:** for each run, the method (`k3ctl` or human), the client's
  SHA-256, the `status` replies before and after the reset (`rst`,
  `fcrec`, `pwr`, `k3`, `up`, `ver`), the `reset` reply, the UTC times,
  the boot IDs before and after, and the seconds to the new boot ID.
- **Serial log:** M0 open item 40's paragraph becomes an input, written by
  hand for each campaign from the operator's picocom log, so each record
  states its own reading instead of M0's campaign's.

## Markers

A passing `te-poc` capture holds M0's lines in M0's order, with three new
kinds of line. Hart 0's stream:

```text
BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000 fdt=<f> dest=0x0000000102000000 bytes=0x00000000000a4000
BE_R3:01 BOOT_VALIDATED
BE_R3:02 R1_DERIVED
BE_R3:03 R2_BUILT_REWALKED
BE_R3:04 HS_VS_STATE_VERIFIED
BE_R3:05 BINDING_PREPARED
BE_R3:06 HGATP_FENCED_PUBLISHED
BE_MVP:01 SCENARIO name=te-poc domains=2 harts=0,1,2 of=8 ring_bytes=0x8000 mvp_region=0x102064000 mvp_bytes=0x40000 image_bytes=0xa4000
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1 started=none
BE_MVP:03 GSTAGE_BUILT_REWALKED domain=0 hart=1 gpa=0x80000000 hpa=0x110000000 size=0x4000000 leaves=32 root=0x102034000 vmid=1
BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1 hart=2 gpa=0x80000000 hpa=0x114000000 size=0x4000000 leaves=32 root=0x10203c000 vmid=2
BE_MVP:03 CHANNEL_CHECKED channel=0 writer=0 reader=1 gpa=0x84000000 hpa=0x118000000 bytes=0x1000 level0=0x102039000,0x102041000 writer_pte=0x460000d7 reader_pte=0x46000053 config=<64 hex digits>
BE_MVP:04 PAYLOAD_CHECKED kernel_bytes=<K> image_size=<S>
BE_MVP:05 DOMAIN_RAM_CLEARED domain=0 gpa=0x80000000 size=0x4000000 ticks=<T>
BE_MVP:05 DOMAIN_RAM_CLEARED domain=1 gpa=0x80000000 size=0x4000000 ticks=<T>
BE_MVP:05 CHANNEL_CLEARED channel=0 hpa=0x118000000 bytes=0x1000 ticks=<T>
BE_MVP:06 PAYLOAD_PLACED domain=0 kernel=0x80200000 kernel_bytes=<K> image_size=<S> dtb=0x83e00000 dtb_bytes=0x1000 ticks=<T>
BE_MVP:06 PAYLOAD_PLACED domain=1 kernel=0x80200000 kernel_bytes=<K> image_size=<S> dtb=0x83e00000 dtb_bytes=0x1000 ticks=<T>
BE_MVP:07 BLOCKS_PUBLISHED region=0x102044000 bytes=0x20000 generation=1 budget_ticks=0x100000000
BE_MVP:08 to :10 for each domain, as M0
  ... domain lines, BE_MVP:DENY lines, BE_MVP:11 and :12 for each domain, as M0 ...
BE_MVP:13 RUN_COMPLETE domains=2 records=<N> wakes=<N> idle_ticks=<T> overlap_ticks=<T> ticks=<T>
BE_MVP:14 SHUTDOWN type=0 reason=0
```

`:02`'s `started=` and the boot hart follow M0-A.2, and `:09` shows K3's
WARL `hedeleg` (`0xb15c`; QEMU `0xb15d`). Each denial gives one line from
hart 0, between its domain's `:10` and `:12`, interleaved with the domain
lines in M0-C's drain order:

```text
BE_MVP:DENY hart=<h> domain=<d> seq=<n> kind=<unmapped|read-only> cause=<c> injected=<e> gpa=<g> htval=<t> htinst=<i> stval=<v> sepc=<p> vsstatus=<s> vstvec=<b> ticks=<T> service=<S>
```

with `ticks` the exit's time since the barrier and `service` the post's
time minus the exit's. Values print in hex without leading zeros, so the
line stays under 280 characters, within M0's 320-byte monitor line. The
two channel lines appear once per declared channel, so a scenario with
none, `two-guests`, prints neither; no existing line changes format (Q6).

Each domain's stream holds M0's required lines in order, with its own
command line, and adds after `MVPINIT 02`:

```text
G0  MVPINIT 07 CHANNEL role=writer gpa=0x84000000 bytes=4088 digest=<x> flag=0x42454d314348414e
G0  MVPINIT 08 DENIED n=1 kind=load gpa=0x84001000 va=<v> pc=<p> signo=11 code=2 observed=1
G1  MVPINIT 07 CHANNEL role=reader gpa=0x84000000 bytes=4088 digest=<x> polls=<n> match=1
G1  MVPINIT 08 DENIED n=1 kind=store gpa=0x84000ff8 va=<v> pc=<p> signo=11 code=2 observed=1 unchanged=1
G1  MVPINIT 08 DENIED n=2 kind=load gpa=0x90000000 va=<v> pc=<p> signo=11 code=2 observed=1
```

Then M0's eight `STEP` lines, `SLEEP`, `RESULT pass`, `POWER_OFF`, and
`reboot: Power down`. The `MVPINIT` numbers keep M0's meaning, so 07 and
08 come before 03 in time. The reconciliation rules are those of
[Scenarios and the harness](#scenarios-and-the-harness).

- **Terminal marker:** the board tools anchor M0's terminal expression at
  the start of a line, `^(BE_MVP:14 SHUTDOWN|BE_MVP:FAIL|BE_K3_B3:
  FAIL)`. Only monitor code writes the console: hart 0 prints every domain
  line behind its prefix, with every byte outside `0x20`-`0x7e` but LF
  replaced, and a domain hart writes only its own `FAIL` and `DETAIL`
  lines in M0's fallback path; so no guest can print a line that starts
  with `BE_MVP:` (inference from M0's console rules), on which the remote
  reset depends.
- **Failures** are M0's: `BE_MVP:FAIL <class>`, a `DETAIL` line, then the
  SRST request; the channel check's refusal is `gstage` and a refused
  denial `guest-page-fault`, with M0's exit `DETAIL`.

## Tests and evidence

| Layer | Check | Pass criterion |
| --- | --- | --- |
| Offline | `tools/policy-check.py` on `te-poc`; `--self-test`; `--mutation-test` | A1 to A6 and A8 pass, A7 vacuous; six grants and one declared flow; every mutation rejected for its own analysis |
| Offline | `make -C mvp policy-negatives` (in `check`) | `undeclared-flow` fails exactly A4, A5, and A6; `grant-without-rule` exactly A8; neither writes a header |
| Host | `tests/gstage-test.c` (changed): the channel's build and walk; every walker refusal (a second pointer or leaf, a pointer elsewhere, `X`, `G`, PBMT, `N`, reserved bits, a wrong PPN); the channel check's every refusal (a missing or extra leaf, different HPAs, the reader with `W`, the writer without it, a window over the page); no channel: M0's roots byte for byte | Identical GCC and Clang output with pinned counts |
| Host | `tests/deny-test.c` (new): `be_mvp_denial_decide` over every cause, both sides of each region boundary (window, page, the neighbouring page), `SPVP`, `SPV`, and `GVA` values, `htval` alias bits, every `htinst` form (zero, transformed, compressed transformed, each pseudoinstruction, the wrong opcode), every `vstvec` mode; the injected values and the `vsstatus` transform for every `SIE`, `SPIE`, `SPP` combination | Identical GCC and Clang output with pinned counts |
| Host | `tests/sbi-test.c`, `tests/hart-test.c` (changed): the denial action and counters (`exits = sbi + ipi + denials`); the DENIAL codec; a full ring; the control loop's DENIAL step (phase, sequence, kind, cause mapping) and the SHUTDOWN reconciliation, in the pseudo-random interleavings | Identical GCC and Clang output with pinned counts |
| Guest inputs | `build-guest.sh` pins and the `.config` delta check; `kernel-repro` on `l1` and across `lx2` and `l1`; M0's reference boots | Pins match; the delta is the three declared lines; identical repeat builds |
| Port | `tools/port.py --check` | Unchanged: 32 files, 12 rules, 14 substitutions |
| Lock | `mvp tool-lock check` on the host and in the evaluator | 29 roles; 26 inside |
| Image | `tests/check-image.py` and its mutations, with the `te-poc` profile, the `two-guests` and probe profiles, and the variants | The rules below, for GCC and Clang |
| Markers | `tests/check-capture.py --self-test` and `--mutation-test` | M0's fixtures give their verdicts, the board's stop-6 capture failing on the alternation floor alone; new `te-poc`, `reader-write`, and `no-inject` fixtures from QEMU; every mutation rejected |
| QEMU | `tests/run-qemu.sh`, `-smp 8`; the kexec rehearsal | The table in [Scenarios and the harness](#scenarios-and-the-harness) |
| Evaluator | `mvp evaluate` | Every gate inside; images byte-identical with the host's |
| Board tools | `tests/run-tool-dry-run.sh` with `tests/fake-k3ctl.py`; `tests/test-kexec-load.py` | M0's 17 cases and the reset cases of [The remote reset](#the-remote-reset); the layout rule with the channel page on the recorded `/proc/iomem` |
| Board | `k3-preflight`, `k3-load-check`, `k3-campaign` | Preflight passes; three GCC and one Clang `te-poc` runs pass; `reader-write` and `no-inject` fail as declared; one reset per run |

**Image checker** (M0's rules, with these changes):

- **CSR writers:** `vscause`, `vstval`, `vsepc`, and `vsstatus` written
  after the R3 reset only by the arm helper and `be_mvp_arch_inject`, which
  writes exactly those four from its argument words, reads each back, and
  touches no other CSR; the vector reads `vsstatus` once and stores it at
  the exit record's offset 352; no other change to the writer table.
- **Call sites:** `be_mvp_arch_inject` is called from exactly one site,
  the denial action, in images whose accepted-exit set names `denial`
  (`te-poc`, `reader-write`), and from none in the others (`two-guests`
  and its variants, `no-inject`, the probe images); the install function
  keeps exactly two call sites; `hgatp` writes and `hfence.gvma` stay
  inside the accepted R3 functions; no `sret`, `ecall`, `fence.i`, or
  `wfi` is added.
- **Layout:** the channel page, from the layout header and the linked
  channel record, is the ninth extent in the pairwise-disjoint set
  (M0's eight and the page), in S-mode RAM above G1's window; the linked
  record's GPA, HPA, size, endpoints, and rights, and the linked
  configuration identity, equal the authority report's. The roots are
  built at boot and are not in the image, so that the page appears in
  exactly the two roots, with the two declared leaves, is shown by the
  boot-time channel check, whose line the capture checker reads.

## Accepted decisions M1 departs from

Each applies to the MVP line only and changes no accepted byte or accepted
document's text.

| # | Accepted decision or guidance | M1 departure | Accounted for by |
| --- | --- | --- | --- |
| 1 | B7's pair check "refuses shared pages" (`be_b7_gstage_pair_check`, MVP plan M1 deliverable 2), as M0's counted copy does | The check admits exactly the declared channel page with its declared rights and refuses everything else | MVP plan M1 deliverable 2; Instance 2; host tests; `reader-write` |
| 2 | M0's G-stage: "Per root: one level-1 table, no level-0 table, no per-page rights" (`mvp/src/mvp-gstage.h`) | One level-0 page per root, holding one 4 KiB leaf with per-root rights | The walker's one new rule; host tests; `:03 CHANNEL_CHECKED` |
| 3 | M0's exit table: a guest-page fault is "Terminal for the run, as in B7 (its Q8)" | In `te-poc`, the exact denial entry is logged, injected, and resumed; everything else stays terminal | MVP plan M1 deliverable 3 and D8; S1 H15, H16; `no-inject`; host tests; mutations |
| 4 | M0: "no `vs*` write after each hart's arming but TIME's `vstimecmp`"; the resume tail "writes no vs* CSR" | `be_mvp_arch_inject` writes four `vs*` CSRs once per accepted denial; the tail is unchanged | One helper with readback; the image checker's writer table and call site |
| 5 | M0 stop condition 5: "a kernel config change beyond B6's fragment" | B6's fragment plus `CONFIG_DEVMEM=y` and `CONFIG_STRICT_DEVMEM=y`; Kbuild's host-probe variables fixed (Q16) | Q2; the `.config` delta check; stop 5 |
| 6 | The MVP plan's Scope ("RAM-only loading through Linux kexec from hart 0 as in B7, with human resets", "The B-series board-safety rules stand unchanged") and harness ("with human resets"); M0's "the human powers the board on and resets it after every run"; `k3-campaign.sh` "never touches power, reset, firmware, or the serial input" | Under Q14's default, the campaign tool resets the board through `k3ctl` after each passing run; every other board-safety rule stands | Q14; [The remote reset](#the-remote-reset); stop conditions 9 and 10; the dry run |

## Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| K3's VS CSRs or its `SRET` into VS mode at `vstvec` behave otherwise than QEMU's | The guest does not reach its handler, or a readback differs | QEMU first; the helper's readback; `te-poc` and `no-inject` on the board; stop 6 |
| K3's `htinst` for VU-mode accesses through Linux's VS stage is not the form the entry accepts | A planned denial is refused as terminal | M0's VS-mode values (`0x3303`, `0x3023`, `0x0`); the entry accepts zero or the transformed form; the platform record keeps each value; stop 6 |
| Linux handles an injected access fault otherwise than the plan reads `traps.c` | The program dies, prints `unhandled signal`, or the kernel panics | VU-mode faults only; the handler; the rejected substrings; QEMU first; stop 6 |
| `nolibc` cannot install the handler | No denial is observed | The raw `rt_sigaction` through `syscall()` and the UAPI types `nolibc` already includes; QEMU first; a libc would be stop 5 |
| A guest program maps a page outside its RAM executable | The guest kernel writes outside its `mem_map` (`flush_icache_pte` on a FLATMEM kernel) | No scenario access is a fetch, and the init maps every denied page read-only; cause 20 is host-tested only ([Guest software](#guest-software)) |
| The page is shared by two harts under two VMIDs and two roots | Stale or torn data | One HPA page; static roots, so no switch and no shootdown; VMID-tagged TLBs on each hart; DRAM's attributes with no PBMT anywhere; the protocol's fences; the reader's digest; M0's ordering probe (0 stale reads, hart 0 to hart 1, both in `cluster0`), while M1's channel crosses harts 1 and 2, also in `cluster0`; stop 6 |
| A guest floods denials | A full ring; a busy console | The scenario expects exactly three; a full ring fails closed on its writer's hart only; M0-C's round-robin drain gives a flooding domain at most every other record on hart 0's console; the exit ceiling; availability is outside the claim |
| `k3ctl` resets at the wrong moment | Fedora loses unsaved data, or a run is cut short | A reset only after a passing run's anchored terminal marker, the kexec handoff, and an SSH probe that finds Fedora down; the dongle's port opened only then; one reset per run; the human keeps physical access |
| The dongle enters recovery | The BootROM's download mode, a firmware-write path | `recovery`, `press`, and `hold` are never sent; `fcrec=0` is required before a reset; the README's advice to wire only ground and reset is the responsible human's to apply; stop 9 |
| Opening the dongle's port reboots it, with unvalidated transients on its lines | An unintended reset | The client allows for a reboot on open, and the README lists startup transients as unvalidated: the tool opens the port only while Fedora is down; a residual risk Q14 asks the responsible human to accept |
| The client or the dongle's firmware changes | Unknown behaviour | The client's SHA-256 pin; the protocol version `1.0`; stop 10 |
| The checking machinery grows | S1 H43 | The budgets; the ratio in the result packet; stop 13 |
| The parser accepts more than Part 2 defines | A wrong policy passes | A strict grammar; A1; the mutations |
| The report and the image describe different configurations | Evidence about another configuration | The identity and the channel record checked by both the image checker and the capture checker |
| M1 invalidates M0's fixtures | The stop-6 property is lost | No M0 line changes format; `two-guests` stays v1; the fixtures are judged again in M1-4 |
| QEMU's TCG passes the protocol by luck | A stale read on the board | Fences on both sides; the digest; board runs |

## Claim boundary and non-goals

- **Evidence:** host tests, the offline checks, emulation, and diagnostic
  bring-up evidence for one board, its firmware, and one Fedora kernel,
  never hardware validation, qualification, or formal verification. QEMU
  results are emulation. M0's platform facts stay facts for one board.
  Model, Helium, R-series, and B0-B7 claims do not transfer.
- **What M1 shows:** in the tested scenario, on QEMU and one board, a
  declared channel, one page that the writer's root maps read-write and the
  reader's read-only, between two Linux guests on two harts; data crossing
  it from the writer to the reader under a fenced protocol; and logged
  denials of the accesses the scenario makes, two loads from unmapped
  pages and a store to the read-only page, each delivered to the
  offending guest as the corresponding access fault, observed by the
  program that made it, and followed by its continuing; plus the offline
  checks of Instance 2 and an authority report that the boot-time re-walk
  matches.
- **The claim ledger** (MVP plan, "Method per claim"): "Each root maps
  only what the manifest grants, and roots share only declared channels"
  rests on the boot-time re-walk and channel check and on host tests, not
  on a proof of the root builder; "The tested cross-domain accesses are
  denied, logged, and delivered as faults" on QEMU and board runs, the
  negative images, and the mutations, not containment of arbitrary
  guests; "The manifest conforms to the policy (I11)" on A8 before the
  build, not on a proved checker, whose soundness and differential
  agreement are M3's.
- **Not claimed:** an isolation proof, noninterference, freedom from side
  channels (the page is an intended channel, and timing through it is not
  analyzed), containment of arbitrary guests, or anything about the
  untested accesses: isolation beyond the tested accesses remains by
  construction, two disjoint windows and two re-walked roots that share
  one declared page. A denied fetch (cause 20) is accepted and injected by
  the same path but tested on the host only. The denial path, the channel
  check, the rings, and the offline checker have no proof.
- **TE is specification here.** The policy is the specification; the
  monitor never parses it, never evaluates `decide`, and decides a denial
  from the installed root and the sealed channel record alone, so
  enforcement stays derived (M01-A). Neither trigger fires for U2
  (security model v1, Part 5): the reader's store and the out-of-window
  accesses are absent mappings, and injection and logging are "monitor
  behavior on an already-denied access, not a policy decision on an
  allowed one"; nothing is designated, delegated, or revoked at run time.
  M1 selects no runtime TE mechanism and no capability; a design that
  needed one would be stop condition 14.
- **Not selected:** a fault-injection or denial-log format for Beryllium
  beyond M1, a guest ABI, an SBI profile, a manifest encoding (M3's), a
  policy tool beyond this checker, a development kernel or BSP, or OpenSBI
  as the long-term firmware boundary. `k3ctl` is board-operations tooling
  for these campaigns, not a Beryllium mechanism, and no evidence rests on
  it.
- **CHERI alignment** (MVP plan D12): types, labels, domain indices, VMIDs,
  and GPAs are identifiers, and only the sealed record and the leaves a
  hart installs grant access (S1 H03); the channel is an explicit shared
  object with one writer, fixed rights, and directional `send` and
  `receive`, the explicit sharing CHERIoT's compartments use; a denied
  access is delivered to the faulting domain alone, as a CHERI fault is to
  the faulting compartment; and the report is offline JSON in the
  `cheriot-audit` pattern (D9). No CHERI mechanism is used.

## Work packages

M1-1 and M1-2 are independent; the rest run in order, and one result
review packet follows M1-6.

| Package | Work | Exit criteria |
| --- | --- | --- |
| M1-1 The policy offline | `scenarios/te-poc/policy.te` and the v2 `scenario.json` (labeling, need sets, objects, channels, accepted exits, roles, denials, expectations); `tools/policy-check.py` with its self-test and mutations; the authority report; the two build-time negatives; `gen-scenario.py`'s v2 support, its policy check before any header, and the channel record, identity, and accepted exits in `mvp-scenario.h` | A1 to A6 and A8 pass and A7 is vacuous; the report lists exactly six grants and one declared flow; both negatives fail as declared; the self-test and every mutation pass; the checker within 900 lines; `two-guests`' expectation files byte-identical to M0's |
| M1-2 The channel in the G-stage | The channel in the layout, the descriptor, and the walked map; the builder's pointer and leaf; the walker's rule; the channel check; `tests/gstage-test.c` | Identical GCC and Clang output with pinned counts; every refusal covered; with no channel, M0's roots byte for byte |
| M1-3 The denial path and the images | The exit record's `vsstatus`; `be_mvp_denial_decide` and `tests/deny-test.c`; `be_mvp_arch_inject`; the DENIAL record, the denial action, hart 0's step, and the three new lines; the channel page in the payload, loader, and layout extents; the `te-poc`, `reader-write`, and `no-inject` images; the image checker's rules and mutations; measured budgets | The image checks pass for both toolchains and every profile; every budget holds; the host tests give identical GCC and Clang output with pinned counts |
| M1-4 Guest, harness, QEMU, evaluator | The init's roles, handler, and reports; `guest/mvp-kernel.config` and the `.config` delta check; `/dev/mem`; Q16's build change; new pins; `kernel-repro`; the capture checker's rules and mutations and the new fixtures; the QEMU suite; the kexec rehearsal; the bundle with the report; `mvp check`; `mvp evaluate` | `mvp check`, the kexec rehearsal, and `mvp evaluate` pass; images identical across host and evaluator; M0's fixtures give their verdicts |
| M1-5 Board | The remote-reset path in `k3-campaign.sh` and `k3-run.sh`, the anchored terminal marker, the pin, the wrapper's settings, the fake client and its dry-run cases, Q18's `PAUSED`; then `k3-preflight`, both `k3-load-check`s, and the campaign of Q12 | Every capture passes its checker, or a stop applies; each run is followed by exactly one reset that returns Fedora |
| M1-6 Record and packet | The board record with its platform record; README results and the checking-to-monitor ratio; `kernel-repro` again; `planning/mvp-m1-result-review-summary.md`; status documents | One exact result commit and packet for the responsible human's decision |

## Stop conditions

Each returns M1 to the responsible human, with the evidence so far, before
any workaround:

1. A needed change to an accepted R0-R7 or B0-B7 byte, an accepted
   document's text, a retained R8 input, M0's retained board record or the
   fixture made from its board capture, or anything under `model/`; root
   integration.
2. A needed HS-to-M SBI call beyond M0's surface (Base, DBCN write, SRST,
   HSM `hart_start` and `hart_get_status`, IPI `send_ipi`); `hvip` or any
   injected interrupt; an H load or store; a third domain hart, or a hart
   started or stopped after the barrier; a scheduler or time slice; a lock
   or atomic read-modify-write in the fast path; an `hgatp` write,
   `hfence`, or `sfence` after the barrier, the denial path included; a
   device, MMIO, or DMA path.
3. A budget overrun, including a ring high-water mark above half, a denial
   count other than the scenario's, or a second shared page.
4. A needed CSR access outside M1's inventory: M0's, plus the vector's
   `vsstatus` read and the injection helper's writes and readbacks of
   `vscause`, `vstval`, `vsepc`, and `vsstatus`.
5. An init, `Image`, DTB, or OpenSBI that does not rebuild byte for byte or
   match its pin; an image that differs between the host and the
   evaluator; a missing tool; a final guest `.config` that differs from the
   one B6's fragment alone gives beyond `CONFIG_DEVMEM`,
   `CONFIG_STRICT_DEVMEM`, and `CONFIG_IO_STRICT_DEVMEM`; a guest that
   needs a kernel patch, a driver, or a libc; any new external input.
6. A board outcome QEMU did not show, diagnosed read-only first: an
   unexpected exit class, a missing line, a hang, a REFUSED run, or any of
   these: `htval` other than GPA >> 2; an `htinst` outside the accepted
   forms; an injection readback that differs; an injected fault that Linux
   does not deliver as SIGSEGV with `SEGV_ACCERR` and the faulting PC, or
   after which the program does not continue; a denial the guest observes
   without a DENY line, or a DENY line without the guest's report; a
   channel read that differs from what the writer wrote (`match=0`), or a
   denied store that changed the page (`unchanged=0`). The same outcomes
   in QEMU, where they contradict this plan's reading of Linux or of the
   specification, are also returned rather than worked around.
7. A preflight `/proc/iomem` child or FDT reservation in the staging
   region, the hart region, the MVP region, either window, or the channel
   page.
8. The preflight lacks `h` or `sstc` on harts 0 to 2 or HSM in Fedora's
   log, or shows firmware other than M0's record (`SBI implementation
   ID=0x1 Version=0x10006`); or a run prints `BE_MVP:FAIL sstc` or `FAIL
   firmware`.
9. Any step that would write firmware, the U-Boot environment, flash, boot
   configuration, or board storage; use TFTP or a staged-NVMe `load`; need
   automation to type at U-Boot; or need any `k3ctl` command but `status`,
   the client's `ping` handshake, and `reset`, `recovery` and `power`
   included.
10. A remote reset that does not bring Fedora back with a new boot ID
    within the bounded wait; any need for a second automated reset for one
    run; a `k3ctl` reply that is `ERR`, a device error, a held line
    (`rst`, `fcrec`, or `pwr` not 0), or another version than `1.0`; a
    client whose SHA-256 differs from the pin; or Fedora answering with
    the run's own boot ID after its terminal marker.
11. A guest that needs SBI outside the subset.
12. A tool-lock role the development host cannot satisfy with open tools,
    or an evaluator base or closure that cannot be pinned (MVP plan stop
    5).
13. Checking machinery beyond this plan's budgets: `policy-check.py` above
    900 lines with its self-test and mutations, or the line's checking code
    above 2.2 lines per monitor line (MVP plan stop 6; S1 H43).
14. A scenario or design that fires the capability or runtime-check
    trigger, such as a denial decision that needs the policy, a type, or
    anything but the hart's root and the sealed channel record (MVP plan
    stop 4).

## Board safety and procedure

- **RAM only:** as M0. Kexec stages the image and loader in Fedora's tmpfs
  `/tmp`, and `kexec_load` places the segments in RAM. The shim writes only
  the monitor image and its report line; the monitor writes only its image,
  its pool, the hart region, the two windows, and the channel page; the
  domain harts run only RAM-resident code and never touch firmware.
- **Human control:** the human powers the board on and off, decides to
  start each campaign, and may reset the board by hand at any time.
  Automation reads the serial log output-only, uses SSH only for the
  read-only preflight and B0's staging, load, and `systemctl kexec` steps,
  and never types at U-Boot. With `K3_RESET=k3ctl` (Q14), the campaign
  tool also resets the board after each passing run, as below; without
  it, the human resets after every run, as in M0.
- **Procedure,** after `mvp check`, `mvp evaluate`, and the kexec rehearsal
  pass: the human's `status` check of the dongle, the preflight, both load
  checks, three GCC and one Clang `te-poc` runs, then `reader-write` and
  `no-inject` (Q12), each run followed by one reset:

```sh
cd mvp
python3 -B <k3ctl client> -d /dev/ttyACM0 status        # by hand: rst=0 fcrec=0 pwr=0 k3=n/a ver=1.0
./mvp k3-preflight
./mvp k3-load-check TOOLCHAIN=gcc
./mvp k3-load-check TOOLCHAIN=clang
export K3_RESET=k3ctl K3CTL=<k3ctl client> K3CTL_DEV=/dev/ttyACM0
export K3_SERIAL_LOG=<the operator's picocom log>
export K3_RUN_ROOT=$PWD/../build/mvp/k3-campaigns/<date>-com260
./mvp k3-campaign TOOLCHAIN=gcc RUNS=3
./mvp k3-campaign TOOLCHAIN=clang RUNS=1
./mvp k3-campaign TOOLCHAIN=gcc VARIANT=reader-write RUNS=1
./mvp k3-campaign TOOLCHAIN=gcc VARIANT=no-inject RUNS=1
./mvp board-evidence
```

### The remote reset

This is the departure from M0's procedure that Q14 asks the responsible
human to accept, with its safety analysis.

- **The device.** The `k3ctl` dongle on `l1`, powered from `l1` only,
  pulls `SYS_RST`, `FORCE_RECOVERY`, or `SLEEP/WAKE` low on command and
  otherwise leaves them released; it never drives a line high. `reset`
  holds `SYS_RST` low for 200 ms (README). The board then restarts as
  after the human's button: boot ROM, U-Boot, and Fedora's autoboot, which
  answered with a new boot ID about 40 s later on 2026-10-26. A reset
  writes nothing: no firmware, U-Boot environment, flash, boot
  configuration, or storage.
- **What the tools send:** `status`, a query that drives no line, and
  `reset`, from fixed argument vectors, each preceded by the client's own
  `ping` handshake, which must answer `OK pong k3ctl 1.0`. Never
  `recovery` (`FORCE_RECOVERY` held through a reset, entering the boot
  ROM's download mode, a firmware-write path), `power`, `press`, `hold`,
  `release`, `raw`, or `help`. The client is the pinned one
  (`tools/k3ctl.sha256`), run by the locked Python 3, through `K3CTL` and
  `K3CTL_DEV`, which the wrapper passes to the `k3-*` commands only.
- **When.** After a run, only if all of these hold, in this order: the
  capture holds Linux's kexec handoff (`Will call new kernel at 108000000
  from hart id <h>`) and, after it, a monitor terminal line, never a
  domain line, by the anchored expression of [Markers](#markers), and the
  tail wait has ended; the capture checker's verdict is `PASS` (a negative
  image that fails as declared passes); one SSH probe with a short timeout
  finds Fedora down; and `status` shows `rst=0 fcrec=0 pwr=0` and
  `ver=1.0`. Then `reset` once, `status` once more while the board boots,
  the wait of Q18 for a new boot ID, and M0's settle wait before the next
  kexec.
- **When not.** A run without its terminal marker within
  `K3_WAIT_SECONDS` (240 s), or with any verdict but `PASS`, ends the
  campaign without a reset: it is a stop, and the board stays as it is for
  the human's read-only diagnosis and reset. A reset after the tool's own
  timeout is not taken, because the board's state is then unknown and
  Fedora may still be running if the kexec never happened, and a reset
  "abruptly restarts the K3 and can lose unsaved data" (README). If the
  SSH probe answers with the run's own boot ID, Fedora never left: no
  reset, stop 10. If it answers with a new boot ID, the human has already
  reset the board: no reset, and the campaign continues.
- **The port opens only while Fedora is down.** The client allows for the
  dongle rebooting when its port opens, and the README lists startup
  transients on the lines as unvalidated; the tool therefore opens the
  port only after a run's terminal marker, never while Fedora runs. The
  `status` check before a campaign is the human's, made by hand.
- **One per run, then a stop.** At most one automated reset per run. A
  reset after which Fedora does not answer with a new boot ID within the
  bounded wait is a stop, not a retry (stop 10).
- **What stays the human's:** power, starting each campaign, the dongle's
  wiring (its README advises connecting only ground and the reset line
  until the other lines have had an attended test; with `FORCE_RECOVERY`
  unwired no command can enter recovery), every reset after a stop, and
  the choice of `K3_RESET=k3ctl` at all. The README cautions against
  board-control commands as "unattended contribution checks"; under Q14's
  default a campaign proceeds between runs without a human at the board,
  which is the risk Q14 asks the responsible human to accept.
- **Records:** each run directory gains `reset.txt` (the method, the
  client's SHA-256, both `status` replies, the `reset` reply, the UTC
  times, the boot IDs before and after, and the seconds to the new one),
  covered by the run's checksums and the board record's manifest.
- **Dry run:** `tests/fake-k3ctl.py` logs each command and answers as the
  firmware's protocol does, and `tests/fake-board.py` changes its boot ID
  after a `reset`. The new cases: three passing runs with three resets;
  a run without a terminal marker (no reset; stop); a failing run (no
  reset; stop); a held `fcrec=1` (no reset; stop); Fedora answering with
  the run's boot ID (no reset; stop); a boot ID that does not change (one
  reset, then stop); a client that differs from the pin (stop before any
  run); `ver=1.1` (stop); a domain line containing `BE_MVP:14 SHUTDOWN`
  (no reset before hart 0's own line); and, in every case, a command log
  holding only `ping`, `status`, and `reset`. None can reach a real board
  or dongle.

## How M1 feeds M2

M2, the protected research domain beside an untrusted Linux domain, needs
its own plan; M1 gives it a policy pipeline that takes a third instance
(`host_t` and `prot_t`) through the same checker and report; a channel
record and a level-0 page that can hold M2's request and response pages,
each a declared channel; a denial path whose accepted entry M2's plan may
widen for its hostile tests, for example to VS-mode faults, and whose
fetch case still lacks an end-to-end test on this guest kernel; the DENY
lines and their reconciliation with a guest's reports; the configuration
identity, which M2's core-held measurement will bind; and board campaigns
that can run unattended between runs. M2's plan decides its management
extension, which changes the guest-visible SBI surface and so the
implementation version (D8); its measurement, the first digest computed in
the monitor; and whether `pause` maps onto `enter`. Nothing in M1 selects
M2's design beyond what the MVP plan states.

## Status record

```text
mvp_m1_plan_status=accepted
mvp_m1_plan_target=7b2c055c1587f9582812a575b296cd625746662b
mvp_m1_plan_acceptance_instruction=accept-7b2c055c
mvp_m1_plan_acceptance_date=2026-10-26
mvp_m1_plan_base=6f7b6e7c1fd609299fd88af164d400da3d6435ae
mvp_m1_plan_branch=beryllium/mvp-m1-plan
mvp_m1_governing_plan=93967fbac926b4fdfdfe636df4d07e8926b625b7
mvp_m1_security_model=0e3eec8b4fd74003f8cedbf2ca66871c31412624
mvp_m1_m0_result=b266972563a39b0687ba2ac8c5b4cb943f3c766a
mvp_m1_m0_result_record=6f7b6e7c1fd609299fd88af164d400da3d6435ae
mvp_m1_m0_plan=4d129808979cb54b7e0a7cc0b3e79d39533e0b9c
mvp_m1_m0_revisions=30c5e1a8af48b24b2315735922576cc949063f48,77559defa70175a363bc869b18f7c3fbb7696352,260ceba668e2d94c54c817c61ae6053dc1cbded8
mvp_m1_open_questions=Q1-Q19-defaults
mvp_m1_scenario=te-poc
mvp_m1_scenario_schema=be-mvp-scenario-v2
mvp_m1_policy=security-model-v1-instance-2
mvp_m1_offline_checker=tools/policy-check.py;A1-A6,A8;A7-vacuous;report-json
mvp_m1_channel=gpa-0x84000000;hpa-0x118000000;4k-level0-leaf;writer-rw;reader-r
mvp_m1_guest_access=dev-mem;CONFIG_DEVMEM=y;CONFIG_STRICT_DEVMEM=y
mvp_m1_denials=g0-load-0x84001000;g1-store-0x84000ff8;g1-load-0x90000000;cause-20-host-tests-only
mvp_m1_injection=vscause-1-5-7;vstval-stval;vsepc-sepc;vsstatus-spp-spie-sie;resume-vstvec-base
mvp_m1_guest_sbi_version=3-unchanged
mvp_m1_markers=m0-formats-unchanged;03-channel-checked;05-channel-cleared;deny
mvp_m1_negative_images=undeclared-flow,grant-without-rule,reader-write,no-inject
mvp_m1_board_runs=2-load-checks;6-kexec-runs
mvp_m1_probe_rerun=none
mvp_m1_reset=k3ctl-proposed;opt-in;reset-only;one-per-passing-run
k3ctl=proposed-reset-only
mvp_m1_work_packages=M1-1..M1-6
mvp_m1_implementation_authorization=M1-1..M1-6-under-this-plan
mvp_m1_implementation_branch=beryllium/mvp-m1
mvp_m1_implementation_status=M1-1-b591b187;M1-2-0174f7a8;M1-3-d3d28d7e;M1-4-65648204-under-M1-A;M1-5-9020c4f8-tools;M1-B-745c293a-804cd24c;M1-6-17ed82f7;result-ff84533c
mvp_m1_board_campaigns=20261027-com260-first-stopped-at-no-inject-stop-6;20261027-com260-m1b-6-of-6-pass-k3ctl-resets-6
mvp_m1_result=accepted-ff84533cb3c13d89063be77652575347c2a82757;2026-10-27;instruction-approve-ff84533c-and-revisions;record-mvp-m1-result-review-summary.md
mvp_m2_authorization=plan-directed-2026-10-27;implementation-none
```

## Plan revision M1-A: the denied accesses in a child of the init

**Status: directed, not yet accepted at an exact commit.** On 2026-10-27
work package M1-4 stopped at [stop condition 6](#stop-conditions). In
QEMU (`k3-like`, GCC with boot hart 5 and Clang with boot hart 7, at
`mvp/` commit `d3d28d7e` with M1-4's guest), every injected fault reached
`/init` as `SIGSEGV` with `SEGV_ACCERR` and `si_addr` equal to the
access's label; the handler ran and stepped past the instruction; the
init continued; both guests printed `RESULT pass` before `BE_MVP:14`; the
three `BE_MVP:DENY` lines matched the guests' `MVPINIT 08` reports in
`gpa`, `htval`, `stval`/`va`, and `sepc`/`pc`, with one `vstvec`
throughout; `htinst` read `0x3303` for the load and `0x3023` for the
store, the values M0 recorded on K3; and `exits = sbi + ipi + denials`
held for both domains. But for every denial the guest kernel printed
`init[1]: unhandled signal 11 code 0x2 at 0x<pc> in init[...]` and a
register and code dump of about fifteen lines. The responsible human was
offered a child process (A), an exact rule for the kernel's block (B),
and a lower console loglevel (C), and directed `A`. As with M0-A, M0-B,
and M0-C, the direction is recorded here, implementation proceeds under
it, and the exact commit carrying this revision is presented for
acceptance with M1's result packet. It changes no accepted byte and no
accepted document.

### The cause

Fact (Linux `v7.2`): `kernel/signal.c:536-538`, `unhandled_signal()`,
returns true for the global init, `is_global_init(tsk)`, before it looks
at the installed handler; `arch/riscv/kernel/traps.c:119-127` then prints
the line and the dump whenever `show_unhandled_signals` is set, which the
pinned `.config` leaves at its default of 1, before `force_sig_fault`
delivers the signal to the handler. The plan's reading of `traps.c`
("prints nothing when the program handles the signal", [The denial
path](#the-denial-path)) holds for every process but pid 1. The guest
programs are pid 1, and `unhandled signal` is one of M0's rejected
substrings (M0 plan, "Markers"), so the capture checker must fail the run,
as the Risks table foresaw.

### M1-A.1 A child process makes the denied accesses

The init forks once after its channel step; the child installs the
SIGSEGV handler, makes the role's denied accesses in order, prints each
`MVPINIT 08 DENIED` line, and exits with its failure count; the init
waits for it and treats a fork failure, an abnormal exit, or a nonzero
status as a failure of the run (`RESULT fail`). The child is not pid 1,
so the kernel prints nothing for a handled fault, and every other line
and rule stands. The channel steps (`MVPINIT 07`) stay in the init. A
scratch prototype of twelve lines showed exactly this on 2026-10-27:
the same DENY and `MVPINIT 08` lines, no kernel line, both guests
passing, 67 and 68 domain lines. Fact: `nolibc` provides `fork()` and
`waitpid()` through the `clone` and `wait4` system calls, which every
uniprocessor MMU kernel has, so no kernel option changes and stop
condition 5's delta check is unaffected.

### M1-A.2 The plan's text, revised

- [The denial path](#the-denial-path): the sentence "prints nothing when
  the program handles the signal (`traps.c:115-130`)" is read as "prints
  nothing when a process other than pid 1 handles the signal
  (`traps.c:119-127`, `kernel/signal.c:536-538`)"; the entry's VU-only
  rule is unchanged.
- [Guest software](#guest-software), "Denials": "before its first denied
  access the init installs a SIGSEGV handler" becomes "a child of the
  init, forked after the channel step, installs the handler and makes the
  denied accesses"; the handler, the fixed instructions at global labels,
  the `MVPINIT 08` line, and the result rules are unchanged, with one
  addition: the child's clean exit is part of `RESULT pass`.
- [Markers](#markers): each domain's stream gains no line; the `MVPINIT 08`
  lines come from the child through the same console.
- [Scenarios and the harness](#scenarios-and-the-harness), "The denial log
  against the guests' reports": unchanged; `MVPINIT 08` lines are matched
  by content, not by pid.

### What this revision does not change

The policy, the labeling, the manifest, and the report; the channel and
the G-stage; the denial path on the domain hart, the accepted entry, the
injected values, the DENIAL record, and the DENY line; M0's rejected
substrings, including `unhandled signal`, which stay in force for every
scenario; the kernel fragment of Q2 and the `.config` delta check; every
expectation file but the te-poc init's line counts; the negative images;
the board procedure and the remote reset; every budget; every stop
condition. Option B, an exact rule for the kernel's block, is not taken,
because it would relax an M0 rule to admit kernel output that the design
can avoid; option C is not taken, because it hides output and leaves the
dump.

### Revision status record

```text
mvp_m1_plan_revision_m1a=directed-2026-10-27;accepted-with-result-ff84533c-2026-10-27
mvp_m1a_direction_instruction=A
mvp_m1a_trigger=stop-6;qemu-te-poc-gcc-clang;linux-v7.2-prints-unhandled-signal-for-pid-1-despite-handler
mvp_m1a_cause=kernel/signal.c:536-538-is_global_init;traps.c:119-127
mvp_m1a_remedy=denied-accesses-in-a-forked-child-of-init;handler-in-child;init-waits;nonzero-status-fails-run
mvp_m1a_unchanged=policy;channel;denial-path;deny-line;m0-rejected-substrings;fragment;budgets;stops
mvp_m1a_options_not_taken=B-exact-rule-for-kernel-block;C-lower-loglevel
```

## Plan revision M1-B: a domain hart's wait for hart 0 measures its progress

**Status: directed, not yet accepted at an exact commit.** On 2026-10-27
work package M1-5's board campaign (`build/mvp/k3-campaigns/20261027-com260/`)
stopped at [stop condition 6](#stop-conditions) in its `no-inject` run
(`20261027T094024Z`), after the preflight, both load checks, three GCC
and one Clang `te-poc` runs, and the `reader-write` run had passed. The
responsible human was offered a wider `no-inject` expectation (A), a
mechanism change to M0's failure path so that only hart 0 prints (B),
and dropping `no-inject` from the board campaign (C), and directed
`accept B, proceed`. As with M1-A, the direction is recorded here,
implementation proceeds under it, and the exact commit carrying this
revision is presented for acceptance with M1's result packet. It changes
no accepted byte and no accepted document; it changes M0's Q10 behaviour
on the domain harts of the MVP line, which M0's plan records as accepted
history and this plan carries forward.

### What the board showed, and the corrected reading

Fact (the run's `serial.log`, and the operator's picocom log, which ends
at the same line): after `BE_MVP:10` for both domains, hart 0 printed 89
guest lines, 7,660 bytes on the wire (7,482 of text, each line ended by
the firmware console's CR and LF); then, in this order,
`BE_MVP:FAIL guest-page-fault`, a `BE_MVP_G1:` line, a second
`BE_MVP:FAIL guest-page-fault`, `BE_MVP:DETAIL domain=0 hart=1 cause=0x15
… htval=0x21000400 htinst=0x3303 … exits=94`, a `BE_MVP_G0:` line, and
`BE_MVP:DETAIL domain=1 hart=2 cause=0x17 … htval=0x210003fe
htinst=0x3023 … exits=94`; then nothing, the board halted. Both guests had
reached their first denied access (the writer's load at `0x84001000`, the
reader's store at `0x84000ff8`), each the declared one.

The handoff's first reading, that hart 0 drained domain 0's FAIL record
and went terminal without acknowledging domain 1, was wrong, and the
option B it described ("hart 0 acknowledges the second domain before
going terminal") would not have changed this run. Only hart 0 prints
prefixed guest lines, and the two guest lines between the four failure
lines are hart 0's, so hart 0 was alive and still draining when all four
were printed; hart 0's own terminal path prints its `FAIL` and `DETAIL`
back to back and then requests SRST, which no line here matches; and the
log ends without hart 0's pair. So **both domain harts took Q10's fallback
path** and printed their own `FAIL` and `DETAIL` lines, interleaved with
hart 0's drain and with each other through the firmware's console, and a
domain hart's SRST request ended the run before hart 0 reached either
FAIL record.

The cause is the window, not a wedged hart 0. M0's Q10 measures hart 0's
latency: a failing domain hart posts its FAIL record behind every line it
has already posted, sends one IPI, and waits 2^24 ticks, 0.699 s on the
board's 24 MHz timebase, for the ACK in its inbound ring. Hart 0 drains
one record per domain per pass (M0-C.1) and prints each through the
firmware console at 115200 baud, 11,520 bytes per second, so the 7,660
bytes of guest lines queued ahead of the FAIL records took about 0.66 s
to print, after the guests had reached their faults about 0.02 s into
their boot (the kernel's own timestamps read 0.017 s at the last line
before the faults). Inference from those figures: both windows expired
within a line or two of hart 0 reaching the first FAIL record. In QEMU
the console is immediate, hart 0
keeps pace with the guests, and the ACK follows the FAIL within
microseconds, which is the one-fault shape the expectation encodes and
the four `te-poc` board runs' DENY lines, drained the same way without a
window, never exposed. The monitor behaved as M0 specifies on every hart;
the finding is a board outcome QEMU did not show (stop 6), and the
window's definition is the defect.

### M1-B.1 The wait restarts on hart 0's progress

A domain hart that has posted its FAIL record and sent its IPI waits for
hart 0's ACK as before, but the 2^24-tick window now measures hart 0's
progress, not its latency: it restarts each time hart 0 takes a record
from the domain's outbound ring, which the hart observes through the
ring's tail, the index hart 0 alone writes and the writing hart already
reads to find room. The fallback fires only when hart 0 has neither
acknowledged the FAIL nor taken a record for 2^24 ticks: a wedged hart 0,
whose tail is still, which is the risk Q10 names; not a healthy hart 0
behind a slow console, whose tail advances at least once per drain pass
while the domain has records, and whose pass takes at most two 256-byte
records through the console, about 0.05 s at 115200 baud. A tail that
moves backwards or past the published head is malformed, and the hart
falls back at once. The window's length, 2^24 ticks, the ACK record, the
IPI, the park on ACK, the fallback lines, the SRST request, and the
immediate fallback for a ring that cannot carry the FAIL (the
`ring-full` variant, M0-A.3) are unchanged.

The decision is a pure function in the SBI core with a host test, as the
denial decision (M1-3) and the drain order (M0-C) are: given the window's
start, the last tail seen, the current time, the current tail, the
published head, and whether the ACK is present, it answers park, wait, or
fall back, and advances its own record of the tail. The domain hart's
terminal path calls it in its wait loop and nothing else about that path
changes. The ring API gains the two reads the function needs, the tail a
writer view sees and the head it has published, with their own host-test
assertions.

### M1-B.2 Hart 0's terminal path is unchanged

Hart 0 still ends the run on the first FAIL record it takes: the ACK to
that domain, its `FAIL` and `DETAIL` lines, the SRST request. It does not
acknowledge the other domain, because it cannot acknowledge a FAIL it has
not taken, and taking it means draining that domain's ring, printing or
discarding the guest lines queued ahead of it. Under M1-B.1 the other
domain's hart, if it has also failed, prints only when hart 0 neither
takes its records nor acknowledges it for 2^24 ticks after hart 0 has
halted, which is to say only when the firmware's shutdown did not take
effect; that is the case Q10 exists for, and the right outcome in it.
So in every run that ends in a domain's failure, only hart 0 prints,
whichever domain's FAIL record it takes first; the `no-inject`
expectation already admits either domain's first denied access, and does
not change.

### M1-B.3 Tests, evidence, and the board

- The pure function's host test, in the SBI core's suite, with cases for
  the ACK, the still tail that reaches the window, the tail that advances
  within the window and restarts it, repeated advances across many
  windows, the malformed tail, and the time CSR's wrap; the pinned counts
  move with it.
- The stopped run's capture, `20261027T094024Z/serial.log`, becomes a
  checker fixture that `tests/check-capture.py --self-test` must reject
  with its findings (the second `FAIL` and `DETAIL` pair and the guest
  lines after the first `FAIL`), as M0-C kept its stopped capture. M0's
  and M1's QEMU fixtures are unchanged, since the change is invisible
  where the ACK arrives at once.
- The image checker, the budgets, `mvp check`, the kexec rehearsal, and
  the evaluator pass again on the revised images.
- The board's kexec runs restart with the revised images, as M0-C's did:
  the preflight, both load checks, three GCC and one Clang `te-poc` runs,
  `reader-write`, and `no-inject`, each followed by one reset, into a new
  campaign directory. The first campaign's six runs and its stopped run
  stay as the record of the stop and are cited by M1's result packet; its
  passing runs are not M1's board evidence, because their images are not
  the revised commit's.

### What this revision does not change

The policy, the labeling, the manifest, and the report; the channel and
the G-stage; the denial path, the injected values, the DENIAL record, and
the DENY line; hart 0's control loop, its drain order and bound (M0-C),
its terminal path, and its ACK; the FAIL record, the fallback lines, and
the SRST request; the window's length; every expectation file; the
negative images; the board procedure and the remote reset; every budget;
every stop condition. Option A is not taken, because the two fallback
pairs are not the designed shape of a failure but a misclassification of
a healthy hart 0, which an expectation should not admit; option C is not
taken, because the board is where the window was wrong.

### Revision status record

```text
mvp_m1_plan_revision_m1b=directed-2026-10-27;accepted-with-result-ff84533c-2026-10-27
mvp_m1b_direction_instruction=accept-B-proceed
mvp_m1b_trigger=stop-6;k3-no-inject-gcc-run-20261027T094024Z;both-domain-harts-took-q10-fallback
mvp_m1b_cause=q10-window-measures-hart-0-latency;115200-baud-backlog-7660-bytes-0.66s-against-2^24-ticks-0.699s
mvp_m1b_handoff_reading_corrected=hart-0-never-took-a-fail-record;literal-option-B-would-not-have-changed-the-run
mvp_m1b_remedy=window-restarts-on-hart-0-progress-via-outbound-tail;pure-function-in-sbi-core;host-tested
mvp_m1b_unchanged=hart-0-terminal-path;ack;window-length;ring-full-immediate-fallback;expectations;budgets;stops
mvp_m1b_board=campaign-restarts-with-revised-images;first-campaign-retained-as-stop-record
mvp_m1b_options_not_taken=A-widen-expectation;C-drop-from-board
mvp_m1b_implementation=745c293a-plan-text;804cd24c-mechanism;sbi-63-14655;ring-160-409413;fixture-k3-no-inject-gcc-stop6-fallback
mvp_m1b_board=second-campaign-20261027-com260-m1b;6-of-6-pass;no-inject-one-fail-detail-pair-from-hart-0
```
