<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M0 result review and acceptance record

This packet presents the result of M0, the first milestone of the accepted
[MVP plan](mvp-plan.md): the maintained MVP source line `mvp/`, the
static multi-hart substrate (hart 0 as the control hart, harts 1 and 2
each running one Linux domain), the evaluation harness, the tool lock and
the clean evaluator, and the K3 platform record. It was implemented and
run under the accepted [M0 plan](mvp-m0-plan.md), revision 2, whose
[decision record](mvp-m0-plan.md#decision-record) holds its
authorization, and under the plan's three revisions M0-A, M0-B, and M0-C,
each directed by the responsible human during implementation and each
presented here for exact-commit acceptance with the result, as the plan
requires. It also records the responsible human's decision on it.

## Decision record

The responsible human accepted exact commit
`b266972563a39b0687ba2ac8c5b4cb943f3c766a` (parent
`13992d6d902131a6c19978b620724fad0524256f`) as the M0 result on
2026-10-26, with Plan revisions M0-A (`30c5e1a8af48b24b2315735922576cc949063f48`),
M0-B (`77559defa70175a363bc869b18f7c3fbb7696352`), and M0-C
(`260ceba668e2d94c54c817c61ae6053dc1cbded8`) as implemented. The
instruction, given in reply to this packet's request to accept, revise,
or defer that exact commit, was `accept b26697`. The abbreviation
`b26697` was checked to resolve uniquely to that commit
(`git rev-parse --disambiguate=b26697`).

- **Scope:** acceptance covers exactly that commit and the claim boundary
  in section 3. Sections 2 to 8 are the packet as presented, apart from a
  note above the section 8 checklist. Section 1's status rows and the
  closing lines of section 9 now show the outcome. The decision itself is
  recorded only here.
- **Decision support:** packet commit
  `c935a3b4c84e2494c14137beaf0350c6e3d47ec5` and this acceptance-record
  follow-up are decision support, not implementation.
- **Successor:** acceptance starts no successor, and none is authorized.
  Each of these needs separate direction:
  - M1, the TE PoC scenario on two Linux guests, and its bounded plan;
  - merging `beryllium/mvp-m0` into the development branch
    `beryllium/single-hart-runtime-r0`;
  - pushing the commits after the 2026-10-24 backup to the private
    `origin`;
  - the planned additive security model v1 revision and any Model change
    (M3);
  - root `Makefile`/`be`/`scripts/check-be.sh` integration;
  - development-kernel/BSP selection;
  - wiring the remote reset (`k3ctl`, available on `l1` since 2026-10-26)
    into the board tools, since the accepted plan names the human as the
    one who resets.
- **Evidence status:** the board runs are diagnostic bring-up evidence for
  one board, firmware, and Fedora kernel. Acceptance adds no hardware
  validation, no qualification, and no formal-verification claim, and
  makes no security claim; isolation between the domains remains by
  construction only. It does not tag, publish, or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `b266972563a39b0687ba2ac8c5b4cb943f3c766a`, parent `13992d6d902131a6c19978b620724fad0524256f`, branch `beryllium/mvp-m0`. Comparison base: the M0 plan acceptance record `6ef36d3a6dd41e370fddd363c4727c19c5bc4b68`, over accepted plan `4d129808979cb54b7e0a7cc0b3e79d39533e0b9c` on the S3 acceptance record `1fb464199dc5ace11c77e4697ff5e13a35f21434`. Two commits form the result: `13992d6d` holds the whole `mvp/` tree with its README, and `b2669725` adds the board record made against `13992d6d` from a clean tree. |
| Current status | Implemented, checked in QEMU and in the clean evaluator, and run on the board. Both Linux domains booted on harts 1 and 2 and ran to power-off concurrently in 4 of 4 RAM-only COM260 scenario runs through Linux kexec (three GCC, one Clang), with identical counts in every run; the three probe images reported their facts, none of them a stop-6 fact; the `payload` image failed as declared. No stop condition applied in the second campaign. At the exact commit `13992d6d`, from a clean tree on the workstation `l1`, `./mvp/mvp check`, `./mvp/mvp evaluate` (146 of 146 images identical between host and evaluator), and `./mvp/mvp kexec-rehearsal` pass, and `kernel-repro` passed again. Responsible-human accepted on 2026-10-26 (instruction `accept b26697`). |
| Decision requested | Accept exact commit `b2669725` as the M0 result, which also accepts Plan revisions M0-A (`30c5e1a8`), M0-B (`77559def`), and M0-C (`260ceba6`) as implemented; or request revisions; or defer. Recorded outcome: accepted. |
| Successor status | Not started and not authorized: M1 (the TE PoC scenario), any merge into the development branch, a security model v1 revision, a Model change, root `Makefile`/`be`/`scripts/check-be.sh` integration, and development-kernel/BSP selection. |
| Publication status | Private repository. `beryllium/mvp-m0` is on the private `origin` through `1a6898e9` (the 2026-10-24 backup push); the 12 commits after it, through `b2669725`, are local and unpushed, as is this packet. The development branch `beryllium/single-hart-runtime-r0` is at `1fb46419` locally and on `origin`. No tag, publication, or release. |

As presented, the packet asked the human to decide whether exact commit
`b2669725` is accepted as the M0 result, with the three plan revisions.
The [decision record](#decision-record) above holds that decision.

## 2. Deliverables

M0 was authorized by the acceptance of exact plan commit `4d129808` on
2026-10-23 (instruction `accept 4d129808, proceed with implementation
using opus-5.5 model`, open questions Q1 to Q13 at their defaults), as
work packages M0-1 to M0-6 under `mvp/` on branch `beryllium/mvp-m0`
from the acceptance record `6ef36d3a`. Fifty commits follow that record
to `b2669725`: 39 under `mvp/` and 11 under `planning/` (the three plan
revisions, their status records, and the handoff and instructions). Nothing outside `mvp/`,
`planning/`, and `.github/copilot-instructions.md` changed; no accepted
R0-R7 or B0-B7 byte, retained R8 input, or root file was touched
(`git diff --stat 6ef36d3a b2669725 -- . ':!mvp' ':!planning'
':!.github'` is empty).

| Deliverable | Paths | Purpose | Trust or privilege boundary | Review question |
| --- | --- | --- | --- | --- |
| The MVP line, seeded by the counted port | `mvp/src/` (22 files), `mvp/shim/mvp-shim.S`, `mvp/tools/port.py`, `mvp/Makefile`, `mvp/guest.mk`, `mvp/tools.mk`, the README's "Files copied from B7" tables | B2's generated port (`port.py --check`: 32 files, 2 changed, 12 rules, 14 substitutions) with the MVP region rule of M0-A.1; B7's and B3's files as counted copies, each hunk tabulated | HS-mode monitor: the accepted R3 prelude through `BE_R3:06`, then the MVP layer (`.mvp.text`/data at `0x102064000`, 256 KiB) | Do the counted tables account for every changed line, and does M0-A.1's region rule leave the accepted first `0x34000` bytes of the flat image as the accepted layout? |
| Pure-C mechanism | `mvp/src/mvp-ring.{h,c}`, `mvp/src/mvp-hart.{h,c}`, `mvp/src/mvp-sbi.c`, `mvp/tests/{ring,hart,sbi,gstage,payload}-test.c` | Single-writer, single-reader rings; hart blocks with a generation word written last; hart 0's control loop (ready, entered, shutdown, fail, done, timeout) with M0-C's round-robin drain; the per-hart SBI core | No privileged instruction; GCC = Clang on pinned counts (ring 157 scenarios, hart 652, sbi 41, gstage 16, payload 8) | Is the drain order (one record per domain per pass) and its bound exactly M0-C.1, and does the host test pin it? |
| Monitor, hart entry, and images | `mvp/src/mvp-runtime.c`, `mvp-trap.S`, `mvp-hartentry.S`, `mvp-hartmain.c`, `mvp-boot.lds`, the scenario generator `mvp/tools/gen-scenario.py`, `mvp/scenarios/two-guests`, the image checker `mvp/tests/check-image.py`, `mvp/tools/budgets.py` | Hart 0 seals, starts harts 1 and 2 through SBI HSM, publishes the barrier, drains the rings, alone writes the console; each domain hart installs its root once and runs the HS fast path with native `wfi`; SBI IPIs both ways; the NOLOAD hart region at `0x102044000` | The only privileged transition is the fast path; `hgatp` writes and `hfence.gvma` only in the accepted R3 functions, the install function with exactly two call sites; the image checker's rules and 91 rejected mutations per toolchain | Does the image checker's site table admit nothing beyond the plan's instruction and CSR inventory, and does `BE_MVP:02`'s boot-hart rule (M0-A.2) admit exactly one `STARTED` non-domain hart equal to the shim's recorded boot hart? |
| Probe images and negative variants | `mvp/src/mvp-probe.c`, `mvp-probe-arch.S`, `mvp/guest/probe-stub.{c,S,lds}`, the variants under `mvp/Makefile` (`payload`, `exit-budget`, `run-timeout`, `ring-full`, `hart-start`, `init-exit`, `rdcycle`, `no-sstc`, `sbi-3.0`, `sbi-time`, `shim-rule`) | The three probe images (HSM, `hgatp` modes, guest-page faults, IPIs, ordering, VMID tagging) and the negative images, each separately linked | The raw `hgatp` write exists only in the two VMID probe images, admitted by the probe checker profile alone and tested by a mutation | Are the probe module's privileged accesses confined to the probe images (`mvp_text` of the scenario image holds no probe code)? |
| Harness: capture checker, QEMU driver, rehearsal | `mvp/tests/check-capture.py` and its 12 fixtures, `mvp/tests/run-qemu.sh`, `mvp/tests/kexec-rehearsal.sh`, `mvp/tests/kexec-rehearsal/init.c` | Every capture judged in guest terms against the scenario's expectation; 154 of 154 mutations rejected; 34 eight-hart QEMU runs each judged, a refused domain-hart boot repeated within a bound; the eight-hart Linux kexec rehearsal | Test-only; no production surface | Does the checker's alternation floor (K = 8, re-justified by M0-C.2) and the stop-6 fixture from the board (`k3-two-guests-gcc-stop6-alternations.log`) reject the first campaign's capture on the floor alone? |
| Board tools and the board record | `mvp/tools/kexec-load.py`, `mvp/tools/k3-{preflight,run,campaign}.sh`, `mvp/tests/fake-board.py`, `mvp/tests/test-kexec-load.py`, `mvp/tests/run-tool-dry-run.sh` (17 cases), `mvp/tools/evidence.py`, `mvp/tools/platform-record.py`, `mvp/results/20261025-com260/` | RAM-only kexec from Fedora with the layout rule; output-only serial capture; a campaign ends at the first run that does not pass; B0's retention of the record with the MVP's tool record, scenario, image digests, verdicts, and the platform record under one manifest | Board safety: no firmware, U-Boot environment, flash, or storage write; automation never types at U-Boot; no path read from a record is ever executed; the record is never overwritten | Does the record (`source_commit=13992d6d`, `source_tree=clean`, `lock_check_status=0`, 75 files, manifest SHA-256 `d56d9585…`) verify, and does every excerpt give its recorded verdict again? |
| Tool lock and clean evaluator | `mvp/tools/lock/tool-lock.{py,conf}`, `mvp/tools/lock/closure.txt`, `mvp/tools/evaluator/{Containerfile,evaluate.sh,fetch-closure.py}`, `mvp/mvp` | 29 roles (26 in the evaluator; `podman`, `ssh`, `scp` host-only, M0-B.4), each by absolute path, resolved path, version, SHA-256, and NEVRA; a 259-package closure with a SHA-256 per RPM (M0-B.1), fetched once into a verified cache (M0-B.2), the image built from it with repositories disabled (M0-B.3); `mvp check` inside, images compared with the host's | The evaluator runs from a read-only source mount with a hidden build tree, a digest-pinned base, no network, and `GIT_OPTIONAL_LOCKS=0`; the one install transaction removes five named base packages | Are the five named base removals (`systemd-standalone-sysusers`, `glibc-minimal-langpack`, `rpm-build-libs`, `rpm-sign-libs`, `dnf5-plugins`) and the closure's two host-dependent additions on `l1` (`glibc-langpack-en`, `systemd-rpm-macros`) acceptable, and is the lock's refresh under direction recorded completely? |
| Plan revisions M0-A, M0-B, M0-C | `planning/mvp-m0-plan.md` (`30c5e1a8`, `77559def`, `260ceba6`, and their "as implemented" notes `5fe007ff`, `6f8e5199`, `4900d004`) | M0-A: the MVP code region, the boot-hart rule, the `ring-full` variant, the `0x104044000` erratum; M0-B: the evaluator's closure source; M0-C: the control hart's drain order | Plan text only; each revision names what it does not change | Does each revision stay within the accepted plan's claim boundary and stop conditions, and is each implemented as its text says? |
| Results and status | `mvp/README.md` (4,140 lines), this packet, `planning/HANDOFF.md`, `planning/roadmap.md`, `.github/copilot-instructions.md` | Every step's result with exact identifiers; 43 open items, each with its state | Documentation | Do the README's results and this packet agree with the retained records, and do the claims stay inside section 3? |

## 3. Claim boundary

**Supported by the exact commit:**

- **On the COM260** (2026-10-25 and 26 UTC; the SpacemiT BSP's U-Boot
  2022.10, the firmware reporting `SBI implementation ID=0x1
  Version=0x10006`, Fedora `7.3.0-65.1.riscv64.omni.fc45.riscv64`), with
  the M0-C boot images (GCC `185396d1db7c…`, Clang `19a5f2d2e89d…`, the
  GCC `payload` variant `f9c47dd08ac8…`, the GCC probe images
  `cede8006150d…`, `1f64375150a2…`, `0c8de5d68db1…`, all byte-identical
  to the build at `13992d6d` and to the evaluator's), in 8 of 8 RAM-only
  runs through Linux `kexec_load`, each on a distinct boot with a human
  reset after it, automation never typing at U-Boot:
  - both load checks loaded the GCC and Clang scenario images at L =
    `0x1_0800_0000` with the FDT at `0x1_0840_0000` and unloaded them;
  - `probe-platform`: harts 1 to 7 `STOPPED`; `hgatp` Sv39x4 with 14
    VMID bits, the Sv48x4 and Sv57x4 writes not taken; `htval` = GPA >> 2
    for a load, a store, and a fetch at GPA `0x9000_0000` (`htinst`
    `0x3303`, `0x3023`, `0x0`); 100 of 100 IPIs delivered in HS (median
    `0x1f` ticks) and at V=1 (median `0x21`); 0 stale reads in 10,000
    iterations, fenced and unfenced;
  - `probe-vmid-distinct`: after a raw `hgatp` switch to root B at VMID 2
    without a fence, the stub read B's value (tagging by VMID);
    `probe-vmid-shared`: with root B at VMID 1, the stub read A's value
    (a translation cached under the shared VMID), a fact by the plan's
    table;
  - in each of the four scenario runs, hart 0 ran the accepted R3
    prelude through `BE_R3:06`, sealed, published the blocks, started
    harts 1 and 2 through SBI HSM (`0x384` to `0x484` ticks), and both
    pinned Linux `v7.2` guests ran in VS mode on their own harts,
    concurrently (overlap `0x2540332`-`0x25403f2` of the shorter domain's
    `0x2563bf9`-`0x2563ca7` ticks), each printing its 65 lines under its
    own prefix, sleeping 1 s (`elapsed_ms=1004`), and powering off;
    hart 0 printed `exits_g0=157 exits_g1=157 records=138 wakes=2
    alternations=125 g0=65 g1=65` and `hart0_idle_permille=431` in
    every run, GCC and Clang alike, with `ring_peak` `0x1278` and
    `0x12b0` against the budget `0x4000`, the longest run 1.696 s against
    the budget of `0x1_0000_0000` ticks, and `hedeleg=0xb15c` read back
    on both domain harts;
  - the `payload` image printed `BE_MVP:FAIL payload` after both
    `BE_MVP:03` lines and ran no domain;
  - every capture passed the capture checker in kexec mode on the board
    tool's run and again from its retained excerpt in the board record;
    M0-5's exit criterion is met with no stop.
- **In QEMU** (`qemu-system-riscv64` 10.2.2, OpenSBI v1.6 `fw_dynamic`,
  `-smp 8 -m 8G`), at `13992d6d`: the two-guests scenario passes on the
  `k3-like`, `rva23`, and `plic` machines for GCC and Clang, each run
  judged by the capture checker, a boot on a domain hart `REFUSED` and
  repeated (34 runs, 41 attempts, 7 refused); every negative variant
  fails as declared; the six probe images report their facts in the
  declared format; `shim-rule` shows the start rule; the eight-hart kexec
  rehearsal passes for both images.
- **Host and evaluator**, at `13992d6d` from a clean tree: the port
  re-derives byte for byte; the tool lock passes on `l1` (29 roles) and
  in the evaluator (26 roles); the host tests give identical GCC and
  Clang output on pinned counts; the image checker passes with 91
  rejected mutations per toolchain and 4 per probe image; every budget
  holds; the capture checker rejects 154 of 154 mutations; the dry run's
  17 cases pass (one skipped inside the evaluator's read-only mount, and
  says so); the evidence bundle is byte-identical for a fixed input set;
  `BE_MVP_IMAGE_IDENTITY: PASS images=146 same=146 differing=0`;
  `kernel-repro`: 10 outputs identical.
- **The platform record** (`mvp/results/20261025-com260/platform-record.md`
  and `.json`) gathers the facts above with their sources, beside QEMU's
  values as emulation facts. Nothing in it is a claim.
- **Plan revisions M0-A, M0-B, and M0-C** are implemented as their text
  says, with the departures the README and the plan's "as implemented"
  notes record (M0-B: five named base removals; M0-C: the fixture from
  the board).

**Trusted or assumed:**

- The accepted R3 prelude, B2's generated port, B3's shim, and B7's
  copied files, at their accepted commits.
- OpenSBI 1.6 on the board (HSM `hart_start` and `hart_get_status`, IPI
  `send_ipi`, SRST) and Fedora's `kexec_load` path; the host's cross GCC
  16.2.1, binutils 2.46.1, Clang and LLD 22.1.8, QEMU 10.2.2, and the
  closure's packages, as the lock pins them.
- The guest's upstream Linux `v7.2` (`8d3ae592…`) and B6's config
  fragment, an external test input, never committed.
- Isolation between the domains is by construction only: two disjoint
  windows, two re-walked roots on two harts under distinct VMIDs, DBCN
  copies from the calling domain's window only, no shared page or
  channel. M0 runs no denial or fault-injection test between the domains.

**Unavailable or `NOT RUN`:**

- OpenSBI's PMP and domain-region prints at power-on are not observable
  on this BSP's console (the first text after a reset is U-Boot SPL's);
  the firmware is visible only through SBI and its reserved memory only
  through the FDT reservations and `/proc/iomem`.
- No board run under U-Boot `booti`; no second board; no run with the
  Fedora 44 host kernel of B0-B7.
- No formal result: the substrate has no proof; the Rocq model is
  untouched; R7's bounded proof does not extend to M0.
- The evaluator's `tree-state` dry-run case is skipped inside the
  evaluator (read-only source mount) and runs on the host.

**Not implemented or selected:** a scheduler, time-multiplexing, domain
migration or overcommit, a third domain hart, a hart started or stopped
after the barrier, a shared page or channel, a denial or fault-injection
test, a VMID policy, a guest ABI, an SBI profile, a console protocol, an
IPI mechanism for Beryllium beyond M0, a development kernel or BSP,
OpenSBI as the long-term firmware boundary, a device, MMIO, or DMA path,
root integration, a Model change, a security model v1 revision, M1, or
any CHERI mechanism. This is diagnostic bring-up evidence for one board,
firmware, and Fedora kernel, never hardware validation, qualification, or
formal verification; QEMU results are emulation; Model, Helium, R-series,
and B0-B7 claims do not transfer; and nothing here is a security claim.

## 4. Load-bearing invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| Hart 0 alone seals, starts the domain harts, and writes the console; a domain hart installs its root once and never writes `hgatp` again | Plan, "Boot sequence on hart 0", "Domain hart entry and fast path" | `mvp/src/mvp-runtime.c`, `mvp-hartmain.c`, `mvp-hartentry.S`; the install function's two call sites | Image checker (`hgatp` writes and `hfence.gvma` only in the accepted R3 functions; the install function with exactly two call sites), mutation "a third install call", "a raw `hgatp` write in the MVP image"; `BE_MVP:08`-`:10` on the board |
| A hart arriving at the entry runs only if the block names its hart ID and the generation word is current; anything else parks | Plan, "Hart region", "Domain hart entry" | `mvp-hartentry.S` and `mvp-hartmain.c` read the bindings, the generation word, and the offsets in that order after `fence r, r` | `tests/hart-test.c` (block validation: hart id, generation, offsets); the `hart-start` variant (`BE_MVP:FAIL hart-start`); `BE_MVP:02`'s all-`STOPPED` rule with M0-A.2's one admitted boot hart |
| Every ring has one writer and one reader; a full ring is refused, never overwritten; hart 0 drains the two rings round-robin, one record per domain per pass | Plan, "Control loop"; M0-C.1 | `mvp/src/mvp-ring.c`, `mvp-hart.c` | `tests/ring-test.c` (every fill level, wrap, full-ring refusal); `tests/hart-test.c` (drain order, pinned); the `ring-full` variant; the capture checker's alternation floor with the board's stop-6 fixture rejected on the floor alone; `alternations=125` in 4 of 4 board runs |
| The fast path takes no lock and no atomic read-modify-write; VTW is never set; the per-domain CSRs are written only by the arm helper | Plan, "Domain hart entry and fast path", "Guest controls" | `mvp-trap.S`, the arm and budget helpers | Image checker's CSR-writer rules; mutations "VTW in an arm immediate", "a `stimecmp` write outside the budget helper" |
| Every budget is hard: monitor text below `0x102008000`, data at or below `0x10200f000`, the MVP region within `0x40000`, exits 2^20 per domain, run 2^32 ticks, ring high-water at most half | Plan, "Budgets"; M0-A.1 | Linker asserts; `tools/budgets.py`; the exit and time budgets in `mvp-hart.c` | `BE_MVP_BUDGET` lines for all 146 images (`two_links=identical`); the `exit-budget` and `run-timeout` variants; on the board `ring_peak` ≤ 29 percent, 157 exits, 1.696 s |
| A board run is RAM-only and output-only; a campaign ends at the first run that does not pass; no path read from a record is executed | Plan, "Board safety and procedure"; S1 H30 | `tools/k3-run.sh`, `k3-campaign.sh`, `kexec-load.py` (layout rule), `evidence.py` | The dry run's `kexec-busy`, `kexec-not-tmpfs`, `kexec-tampered`, `campaign-stop`, `kexec-refused` cases; the first campaign's stop at run 1 |
| The evaluator builds only from the verified cache with repositories disabled, and every image is byte-identical between host and evaluator | Plan, "Tool lock and the clean evaluator"; M0-B | `tools/evaluator/Containerfile`, `fetch-closure.py`, `evaluate.sh` | `BE_MVP_FETCH: RECORDED signatures=259 … header_digests=259`; `BE_MVP_IMAGE_IDENTITY: PASS images=146 same=146`; the lock inside (`roles=26 host_only_skipped=3`) |

## 5. Review history and resolved findings

Findings during implementation, each returned to the responsible human
when the plan required and otherwise resolved in place, are recorded in
`mvp/README.md`'s open items (43, each with its state) and in the plan's
"as implemented" notes. The substantive ones:

| Finding | Resolution |
| --- | --- |
| **Stop condition 3** (2026-10-23): Clang's scenario monitor text ended at `0x1020087e0`, over the accepted `0x102008000` limit | Returned; Plan revision M0-A directed (`agreed, proceed with your recommendations, planning and implementation`): the MVP code region at `0x102064000` by a counted port rule; Clang now ends at `0x102004770`, GCC `0x102004540` |
| A QEMU boot hart other than 0 parked HSM `STARTED` and failed `BE_MVP:02`; the `ring-full` variant never filled in QEMU | M0-A.2 admits at most one `STARTED` non-domain hart equal to the shim's recorded boot hart; M0-A.3 redefines `ring-full` with a delayed first drain; both tested |
| The plan's two `0x104044000` occurrences | Transcription errors; the hart region is `0x102044000` (M0-A.4 erratum, README open item 1) |
| **Stop condition 11** (2026-10-24): the evaluator image could not build; Fedora's updates had replaced one closure NEVRA and `systemd-sysusers` conflicted with the base | Returned; Plan revision M0-B directed (`accept A`): per-RPM digests, a verified cache, repositories disabled, the explicit swap; implemented; five named base removals recorded |
| **Stop condition 6** (2026-10-25, first board campaign): the GCC scenario run failed the alternation floor (5 of K = 8) because hart 0 drained one ring to empty before the other behind the 115200-baud console | Returned; Plan revision M0-C directed (`proceed with A`): round-robin drain; the stopped capture kept as a fixture the checker must reject on the floor alone; the second campaign gave 125 alternations in 4 of 4 runs |
| Two test-only harness defects found in the orchestrating session's line-by-line review of M0-C: evaluator records overwritten; two load checks of one UTC second retained as one | Fixed in `f89366bc` with the dry run's `same-second` case |
| The host's `ca-certificates` moved to `-2.fc44`; rolling it back declined as a security issue | On `refresh the lock` (2026-10-25): one closure line and its digest (`804fa95f`) |
| Host move to `l1` (2026-10-25/26): QEMU and ShellCheck absent, OpenSSH newer than the lock | On `qemu=install-exact` and `lock=refresh-ssh-scp` (2026-10-26): both installed at their locked NEVRAs (QEMU's binary SHA-256 equal to the lock's; ShellCheck's RPM equal to the closure's recorded digest); `ssh`/`scp` to `-16.fc44`; closure 257 → 259, the two additions resolved from `l1`'s installed set (`glibc-langpack-en`, `systemd-rpm-macros` through `rpm-build`); four digests recorded from Fedora-signed RPMs (README open item 39) |
| `evidence.py --board` read the tree's state after creating its load-check staging directory, so a record under a tracked `mvp/results/` would count its own staging directory (found by the M0-6 agent) | Fixed in `13992d6d`: the state is read first; the new dry-run case `tree-state` fails on the old code (`changed=8`, git 7) and passes on the new (`changed=0` on a clean tree) |
| The `tree-state` case failed inside the evaluator: the source tree is mounted read-only | The case skips there and prints `SKIPPED (... is read-only; the case runs on the host)`; the first `evaluate` at the M0-6 content failed for this and the second passed |
| On `l1`, rootless podman could initialise no OCI runtime: the account's podman state DB (2025-12-04, uid 1000) pinned `/run/user/1000`, the account is now uid 501 | The stale, empty store (124 KB, no named image) was moved aside reversibly to `~/.local/share/containers.uid1000-stale-20261026` while the responsible human was asleep; `podman system reset` was not run; host state outside the lock (README open item 43) |
| The campaign tool prints `STOP` when its wait for a reset times out, though no stop condition applies; it exited twice in the second campaign and was resumed into the same record | Recorded (README open item 38); the runs were each made once in the plan's order |
| OpenSBI's power-on prints are not on this BSP's console | Recorded as a fact in the platform record's "Serial log" section, a paragraph written by hand into the generator (README open item 40) |
| The plan inferred 20 to 30 minutes for `mvp check`; it takes about 2.5 minutes on the laptop and 2 on `l1` | Recorded as a fact; the QEMU runs are sequential at about 1.4 s each beyond the guests' 1 s sleeps |

**Open for human judgment:** the three plan revisions (section 2); the
closure's dependence on the host's installed set (open item 39); the
stale podman store (open item 43); the guest kernel's `.config` lines
that follow host tools outside the lock (rustc, pahole; open item 42, the
pinned outputs unchanged); whether the campaign tool's wait timeout
should be renamed or lengthened (open item 38).

**Not run by SOP:** no iterative-evaluation review with a different
model, no separate scope review, and no deep security review. The work
ran on `claude-opus-5.5` sub-agents as the plan's acceptance directed,
orchestrated and reviewed in this last session by `claude-fable-5.1` at
the responsible human's direction for that session (`use the current
model for planning, orchestration & review, and opus-5.5 max long
context to perform coding`); the repository's model pin is unchanged.

## 6. Validation and retained evidence

All at exact commit `13992d6d` from a clean tree on `l1` (x86_64, Fedora
44, 32 CPUs), 2026-10-26, through the wrapper's clean environment:

| Command | When (UTC) | Result | Covers |
| --- | --- | --- | --- |
| `./mvp/mvp check` | 08:41:27-08:43:30 | `BE_MVP_CHECK: PASS`; `BE_MVP_LOCK: PASS roles=29 … closure=259 lock_sha256=6e99262f04a1`; `BE_MVP_QEMU: PASS runs=34 attempts=41 refused=7`; `BE_MVP_EVIDENCE: PASS development … files=165 images=146 qemu_attempts=41 rehearsals=2`; `BE_MVP_RUN_TOOL[tree-state]: PASS (… changed=0)` | Lock, port, host tests, images and mutations, variants, probes, budgets, capture checker and mutations, the 17 dry-run cases, the QEMU suite, the bundle |
| `./mvp/mvp evaluate` | 08:43:40-08:45:42 | `host source=13992d6d… tree=clean images=146`; `BE_MVP_LOCK: PASS roles=26 host_only_skipped=3 …` (inside); `BE_MVP_CHECK: PASS` (inside); `BE_MVP_IMAGE_IDENTITY: PASS images=146 same=146 differing=0`; `BE_MVP_EVALUATE: PASS image=localhost/beryllium-mvp-evaluator:2875ddd675b4-009c2eba5655` | The whole check inside the clean evaluator (`image_id=05e75d8dea9e…`, 293 RPMs from the 259-package closure and the digest-pinned base, built from the verified cache with repositories disabled), images compared with the host's |
| `./mvp/mvp kexec-rehearsal` | 08:45:42-08:46:03 | `BE_MVP_KEXEC_REHEARSAL: PASS smp=8 attempts=1 refused=0 kexec_harts=0 image=185396d1db7c …` and `… kexec_harts=3 image=19a5f2d2e89d …` | Linux `kexec_load` of both boot images under QEMU with eight harts |
| `K3_RUN_ROOT=… ./mvp/mvp board-evidence` | 08:46 | `BE_RETAIN: PASS runs=8 load_checks=2 files=73`; eight `ok … recorded PASS, excerpt PASS`; `BE_MVP_PLATFORM_RECORD: PASS … runs=8 probe_values=11 scenario_runs=4 qemu_gcc,clang=11,11`; `BE_MVP_EVIDENCE: PASS board … runs=8 pass=8 fail=0 refused=0 stop=0`; `--verify … files=75` | The committed board record, `mvp/results/20261025-com260/` (`source_commit=13992d6d`, `source_tree=clean`, `lock_check_status=0`; `MANIFEST.sha256` SHA-256 `d56d95853c84b2999817d8acf69ea9d85a7502734358af4c5a222bccbefa9fdc`) |
| `make -C mvp kernel-repro LINUX_GIT=<mirror>` | 07:39 (at the M0-6 content; the guest inputs unchanged since) | `BE_MVP_KERNEL_REPRO: PASS outputs=10 identical; sysroot_files=1065 sysroot_sha256=c931b51b…` | A second full guest build compared with the first |

The same three gates had passed at the pre-commit M0-6 content
(08:16-08:30 UTC), after one failure of `evaluate` on the `tree-state`
case's read-only-mount defect, fixed before the exact-commit runs. The
board runs themselves are the retained records above; the campaign
directory `build/mvp/k3-campaigns/20261025-com260/`, with the five
console transcripts, and the superseded first record of 06:53 UTC stay
on `l1`, outside the repository. Each run's raw serial capture stays
private; `captures.txt` records its SHA-256, bytes, and lines.

`mvp/README.md` records every intermediate result with the commit at
which it was taken: M0-1 to M0-4 and each revision at its `mvp/` commits
(`90fcc7f1` to `f89366bc`), the lock refresh at `804fa95f`, the first
campaign's stop at `2d0a4fe5`, and M0-5 and M0-6 at `13992d6d` and
`b2669725`. Its checker-to-monitor size table at `13992d6d`: 8,562
monitor lines; 15,389 checking lines (checkers 5,931, host tests 7,083,
harness 2,375); 1.80 checking lines per monitor line (B7: 2.68).

## 7. Recommended review sequence

Use a detached worktree at the exact commit so local changes cannot affect
what you read or run:

```sh
git worktree add --detach /tmp/be-m0-review b266972563a39b0687ba2ac8c5b4cb943f3c766a
cd /tmp/be-m0-review
git --no-pager log --oneline 6ef36d3a..HEAD              # the 50 M0 commits
git --no-pager diff --stat 6ef36d3a HEAD -- . ':!mvp' ':!planning' ':!.github'   # must be empty
```

1. **Plan and revisions** (30 min): `planning/mvp-m0-plan.md`, the
   "Decision record", "Claim boundary and non-goals", "Stop conditions",
   and the three revisions with their "as implemented" notes; then this
   packet's section 3 against them.
2. **The board record** (20 min): `mvp/results/20261025-com260/`:
   `summary.md`, `mvp/bundle.txt`, `mvp/runs.tsv`, one scenario run's
   `check.txt` and `handoff-excerpt.log`, the `payload` run's,
   `platform-record.md`; then `python3 -B mvp/tools/evidence.py --verify
   mvp/results/20261025-com260`.
3. **README results** (30 min): `mvp/README.md` from "M0-5's second
   board campaign (2026-10-25 and 26)" through "M0-6's checks on `l1`",
   then the open items.
4. **The substrate** (60 min): `mvp/src/mvp-runtime.c`,
   `mvp-hartmain.c`, `mvp-hartentry.S`, `mvp-trap.S`, `mvp-hart.c`, `mvp-ring.c`, against
   section 4; the image checker's rules in `mvp/tests/check-image.py`.
5. **The harness and tools** (30 min): `mvp/tests/check-capture.py`
   (the alternation floor and the stop-6 fixture),
   `mvp/tools/evidence.py` and `mvp/tools/platform-record.py`,
   `mvp/tests/run-tool-dry-run.sh`.
6. **Run the gates** (10 min on a host that satisfies the lock; the
   evaluator needs rootless podman): `./mvp/mvp check`, `./mvp/mvp
   evaluate`, `./mvp/mvp kexec-rehearsal`. On a host that does not
   satisfy the lock, `./mvp/mvp tool-lock check` names the role.

```sh
cd /tmp/be-m0-review && ./mvp/mvp tool-lock check && ./mvp/mvp check && ./mvp/mvp evaluate && ./mvp/mvp kexec-rehearsal
cd - && git worktree remove /tmp/be-m0-review
```

## 8. Human decision checklist

The checklist is kept as presented; the responsible human's decision is
in the [decision record](#decision-record), not in these boxes.

- [ ] The scope matches the accepted M0 plan at `4d129808` with Q1 to Q13
      at their defaults, and the three revisions stay within its claim
      boundary and stop conditions.
- [ ] The claims in section 3 match the retained evidence: the board
      record, the QEMU records, the evaluator record, and the README.
- [ ] The trust assumptions are acceptable: the accepted R3 prelude and
      B2/B3/B7 inputs, OpenSBI 1.6 and Fedora's kexec on the board, the
      locked toolchain and closure, the external Linux `v7.2` input, and
      isolation by construction without a denial test.
- [ ] The tests cover the important negative paths: the ten negative
      variants, the image and capture mutations, the dry run's refusal
      cases, the first campaign's stop-6 fixture.
- [ ] The five named base removals in the evaluator and the closure's
      two host-dependent additions are acceptable.
- [ ] The host-state action taken in your absence (the stale podman
      store moved aside, reversibly) is acceptable, and its disposition
      is yours.
- [ ] Successor work stays excluded: M1, the merge into the development
      branch, a security model v1 revision, a Model change, root
      integration, development-kernel/BSP selection.
- [ ] Decision: accept exact commit `b2669725` with Plan revisions M0-A,
      M0-B, and M0-C; request revisions; or defer.

## 9. After the decision

- **Accept:** you explicitly authorize recording acceptance of exact
  commit `b266972563a39b0687ba2ac8c5b4cb943f3c766a`, with Plan
  revisions M0-A (`30c5e1a8`), M0-B (`77559def`), and M0-C
  (`260ceba6`), and the date. The acceptance record names that SHA; the
  plan's revision status records and the status documents are updated
  to match. Acceptance starts no successor: M1's bounded plan, any merge
  of `beryllium/mvp-m0` into the development branch, and any push beyond
  the 2026-10-24 backup each need their own instruction.
- **Request revisions:** a new commit and a new packet follow;
  `b2669725` is not treated as accepted.
- **Defer:** the status stays as presented; no dependent work starts.

**Status:** exact commit `b266972563a39b0687ba2ac8c5b4cb943f3c766a` is
responsible-human accepted as the M0 result as of 2026-10-26
(instruction `accept b26697`), with Plan revisions M0-A, M0-B, and
M0-C. It is on local branch `beryllium/mvp-m0`, unpushed beyond
`1a6898e9`; no successor is started or authorized.

**Next:** none within M0. M1's plan, the merge into the development
branch, and any push each wait on your separate direction.

**Action required from you:** none for M0. Direct the next step when you
choose.
