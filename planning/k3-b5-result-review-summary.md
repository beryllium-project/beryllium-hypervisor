<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# K3 B5 result review and acceptance record

This record presents the result of B5: a first real guest on the SpacemiT
K3 COM260, implemented and run under the accepted
[B5 plan](k3-b5-plan.md). It also records the responsible human's decision
on it.

## Decision record

The responsible human accepted exact commit
`829562395bf14fedbeea0beb82b30da15ec5f7cf` (parent
`ca56efbe629eff6e722141e9ea8feffb4aedae36`) as the B5 result on
2026-10-07. The instruction, given in reply to this packet's request to
accept, revise, or defer that exact commit, was `accept 829562`. The
abbreviation `829562` was checked to resolve uniquely to that commit.

- **Scope:** acceptance covers exactly that commit and the claim boundary in
  section 3. Everything after section 1 is the packet as presented; the
  decision is recorded only here.
- **Decision support:** packet commit
  `6be5fca248c93a70b6c60065eb2aaff8ce6acb99` and this acceptance-record
  follow-up are decision support, not implementation.
- **Successor:** acceptance starts no successor, and none is authorized.
  Each of these needs separate direction:
  - merging B5 into the development branch, and pushing;
  - a Linux or other OS guest, or more guest RAM;
  - development-kernel/BSP selection;
  - root `Makefile`/`be`/`scripts/check-be.sh` integration.

  KVM0 and K0-SC1-B remain parked.
- **Evidence status:** acceptance adds no hardware validation, no
  qualification, and no formal-verification claim. It does not push, tag,
  publish, or release.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `829562395bf14fedbeea0beb82b30da15ec5f7cf`, parent `ca56efbe`, branch `beryllium/k3-b5-bringup`. Comparison base: the B5 plan acceptance record `87be98f1ad00e5f0c73df9eaa2f2ece1f570fd39`. |
| Current status | Implemented, rehearsed, and run on the board. The guest ran to its shutdown in 4 of 4 RAM-only COM260 runs (three GCC, one Clang), with every line identical across runs. `make -C bringup/k3-b5 check` passes at the exact commit in a clean clone. Responsible-human accepted on 2026-10-07 (instruction `accept 829562`). |
| Decision requested | Accept exact commit `82956239` as the B5 result, request revisions, or defer. Recorded outcome: accepted. |
| Successor status | Not started and not authorized. That covers a Linux or other OS guest, more guest RAM, development-kernel/BSP selection, root integration, and merging B5 into the development branch. |
| Publication status | Private repository. `beryllium/k3-b5-bringup` and its worker branches are local and unpushed. No tag, publication, or release. |

As presented, the packet asked the human to decide whether exact commit
`82956239` is accepted as the B5 result. The
[decision record](#decision-record) above holds that decision.

## 2. Deliverables

B5 was authorized by the acceptance of exact plan commit `c3f8ef51` on
2026-10-07 (`accept c3f8ef51`), with the open questions' defaults: the
hardware Sstc guest timer, board runs through U-Boot `booti` only, and the
provisional SBI implementation ID `0x4245` with the `BE_B5_GUEST: ` prefix.
Two workers built the core and the tools in parallel worktrees; the
orchestrator integrated them.

| Commit | Paths | Purpose and boundary | Key review question |
| --- | --- | --- | --- |
| `48e0b44e` B5-1 | `bringup/k3-b5/scripts/k3-preflight.sh` | Read-only SSH probe under Fedora: `sstc` on hart 0 in the device tree and `/proc/cpuinfo`, the timebase, and the kernel's SBI, timer, and KVM lines | Is it strictly read-only? |
| `cf4a4193` B5-2/B5-3 | `bringup/k3-b5/guest/`, `src/`, `scripts/port.py`, `tests/b5-sbi-test.c`, `tests/check-b5-image.py`, `Makefile`, `README.md` | The guest; the pure-C SBI core and its host tests; the port of B2 with six counted rules; the B5 monitor layer (exit vector, resume tail, guest controls, SBI dispatch, tagged console); GCC and Clang images; B3's unchanged shim around them; the image checker | Is the monitor layer correct and as small as the plan allows? |
| `e59f054f` B5-4 | `bringup/k3-b5/tests/check-b5-markers.py`, `run-qemu.sh`, `run-qemu-uboot.py`, `check-b5-capture.py`, `run-tool-dry-run.sh`, `scripts/k3-uboot-run.sh` | The marker and capture checkers and the QEMU, U-Boot, and board tools, copied from B2 and B3 with counted changes and the same board-safety model | Are the copies faithful and the checks strict? |
| `ca56efbe` integration | `tests/check-b5-markers.py`, `README.md`, status documents | Pins `exits=53`; accepts `exception` without `BE_B5:DETAIL` for the monitor's two integrity checks; README procedure and counted-change tables | Are the two checker decisions sound? |
| `82956239` B5-5 | `bringup/k3-b5/results/20261007-com260/`, `README.md`, status documents | The sanitized records of the four board runs and the preflight, with their README | Do the records support the claims? |

The monitor layer is about 1,760 lines (`b5.h`, `b5-sbi.c`, `b5-runtime.c`,
`b5-trap.S`, `b5-platform.h`, `b5-payload.S`); the guest is about 650.
Outside `bringup/k3-b5/`, only `planning/HANDOFF.md`, `planning/roadmap.md`,
`planning/README.md`, and `.github/copilot-instructions.md` change. No
accepted R0-R7 byte, retained R8 input, accepted B0-B4 file, or root
`Makefile`, `be`, or `scripts/check-be.sh` changes: B2's `port.py`, B1's
quiesce, B3's shim, and B0's retention tool are reused unchanged.

## 3. Claim boundary

**Supported by the exact commit:**

- **On the COM260** (2026-10-07; SpacemiT BSP U-Boot 2022.10 and OpenSBI
  1.6 reporting SBI 2.0), in 4 of 4 RAM-only runs (three GCC, one Clang),
  U-Boot `booti` entered B3's shim on hart 0 at `0x1_0220_0000`, and the
  shim entered the B5 monitor at `0x1_0200_0000`. Then:
  - the accepted R3 boot, G-stage, and first-entry sequence printed
    `BE_R3:01`-`07`;
  - `henvcfg.STCE` read back set (`BE_B5:01`), and the guest controls read
    back as planned: `hstatus` controls `0x300180`, `hideleg` `0x40`,
    `hcounteren` `0x2`, `vstimecmp` all ones (`BE_B5:02`);
  - the separately built guest ran at `0x4001_0000` in VS mode and printed
    its nine lines through the B5 DBCN path. They show the Base answers
    (SBI 2.0, implementation `0x4245` version 1, zero machine IDs), the
    probes, `-2` for unsupported calls, `-3` and `-4` for the four refused
    DBCN ranges and the read, the byte write, `-3`/`-2` for the SRST
    refusals, and its VS timer interrupt (`cause=0x8000000000000005`)
    taken in its own handler after its deadline and cleared, then
    `RESULT pass`;
  - the monitor reported `exits=53` (all `ecall`s, the same for both
    toolchains) and requested its SRST shutdown;
  - U-Boot's 60 s watchdog did not reset the board within 75 s after any
    run.
- **In QEMU 10.2.2** with OpenSBI v1.6 (emulation): the plan's five
  scenarios and seven negative variants behave as planned, and the board
  procedure passes through U-Boot v2022.10 `booti` for the GCC, Clang, and
  `k3-address` images.
- **Host:** the pure-C SBI core passes 21 scenarios and 8,240 assertions
  with identical GCC and Clang output.
- **Images:** every plan budget holds (monitor text ends at `0x1_0200_5660`
  for GCC and `0x1_0200_5c30` for Clang, below `0x1_0200_8000`; data below
  `0x1_0200_f000`; guest code `0xca2` and `0xd0e` bytes; flat images
  exactly `0x34000` bytes), and the image checker's rules and 17-defect
  mutation test pass.

**Trusted or assumed:**

- The firmware below HS: the BSP's OpenSBI 1.6, which prints no banner on
  this board, and its `menvcfg.STCE` setting. The monitor's `henvcfg.STCE`
  readback and the guest's timer interrupt show that Sstc reaches VS.
- This workstation's unpinned tools, as in B2-B4: GCC 16.2.1, binutils
  2.46.1, clang/lld 22.1.8, QEMU 10.2.2, Python 3.14.7.
- The accepted R1-R3 code as ported by B2, and B1's quiesce and B3's shim,
  all reused unchanged.
- The B5 monitor layer has no proof; its evidence is host tests, the image
  checker, QEMU, and the board runs.

**Not run or unavailable:**

- R6/R7-style adversarial or proof work for B5: not applicable, as the
  plan states; B5 links none of the R5 switch those concern.
- The negative variants on the board: QEMU only, as planned.
- A Linux kexec launch of B5: not planned (default Q2).
- Any second hart, device, interrupt controller, or guest beyond the one.

**Explicitly not claimed:**

- Hardware validation, qualification, or formal verification.
- SBI conformance beyond the listed functions; any SBI profile, guest ABI,
  Linux interface, or selection of OpenSBI as the long-term firmware
  boundary.
- A second entered domain or isolation beyond B2's; the protected root is
  built but never entered.
- Any R8 evidence: B5 sits outside R8.

## 4. Load-bearing invariants

| Property | Contract and implementation | Test or evidence |
| --- | --- | --- |
| Accepted bytes unchanged | B5 is a port of B2 with six counted rules; every other accepted file is reused unchanged | `scripts/port.py --check` re-derives the port byte for byte (6 rules, 8 substitutions); the image checker requires the three R3 functions byte-identical to B2's |
| No guest request reaches M-mode | The SBI subset is emulated in HS; the only `ecall` is the accepted `be_r3_arch_sbi_call`, reached only from the accepted platform helpers | Image checker: one `ecall` site and its callers; host tests of every SBI row |
| DBCN reads only the guest's own readable pages | `[a1, a1 + a0)` must lie in one readable management leaf; the high word must be 0; no wrap; at most 256 bytes; the copy goes through the leaf's translation into a monitor buffer | Host tests at every leaf edge; the guest's four refused ranges on the board (`-3`) |
| The guest cannot forge monitor lines | HS prefixes `BE_B5_GUEST: `, maps non-printable bytes to `?`, and ends any open guest line before its own | Host tests over all 256 byte values; the marker checker rejects any tag inside a guest line |
| HS takes no interrupt | `sie`, `sstatus.SIE`, and `hvip` stay 0; the VS timer is delivered by hardware through `hideleg` VSTI and `vstimecmp` | Arm and resume checks; image checker CSR-write inventory; the board timer line |
| Fail-closed boot and controls | `henvcfg.STCE` readback, the guest controls, and every resume check fail closed with a class | QEMU `no-sstc` (`BE_B5:FAIL sstc`), `sbi-3.0` (`boot`), and the seven variants |
| Bounded run | 1,024-exit budget | QEMU `exit-budget` variant |
| Images within budget | Monitor text, data, guest pages, and the exact `0x34000` flat image | Image checker; measured budgets above |

## 5. Review history and resolved findings

The scope-review, different-model evaluation, and deep security-review
SOPs are dropped for this repository; no independent review ran. Every
worker used the pinned model.

1. **B5-1.** The planning QEMU flag check was repeated and passed: QEMU
   accepted the `k3-like` flags (including `svade=true`), OpenSBI v1.6
   booted, and B2 printed all 22 markers. The read-only preflight passed
   twice on the board.
2. **Implementation choices beyond the plan's text (core worker):**
   - The guest keeps its helper functions out of line: with inlining,
     Clang's guest grew to 11.5 KiB, over its 4 KiB page. The guest also
     takes the monitor's standard flags (no relaxation, builtins, or PIC).
   - A trap taken from HS prints `BE_B5:FAIL exception` with a `DETAIL`
     line and requests the shutdown before halting, as R5 does, rather than
     halting silently.
   - The arm and resume checks also cover `satp`, `stvec`, `sscratch`,
     `hgeie`, `hie`, `hgatp`, and `vsatp`.
3. **Integration decisions:**
   - The marker checker pins `exits=53`, the count both guests make.
   - It accepts `BE_B5:FAIL exception` without `BE_B5:DETAIL`. The
     monitor's two integrity checks (a trap on a bad stack, and a frame
     that is not the management saved page) report `exception` with no
     guest exit to describe. The plan's rule that exit failures carry a
     detail line still holds for every guest exit. No scenario triggers
     either check.
4. **A board attempt set aside.** After run 1, a reset missed the autoboot
   stop, so U-Boot booted Fedora before the B5 run. That capture held two
   boots, and the capture checker refused it as designed. Its B5 lines were
   complete and identical to the others; it is kept privately, and run 2 was
   repeated from a fresh reset.
5. **Excerpt whitespace.** U-Boot ends some lines with a space; the
   retained excerpts keep the board's bytes verbatim, as B3's do, so
   `git diff --check` reports them.

Open for your judgment: the provisional SBI implementation ID `0x4245`
(unregistered) and the integration's `exception` detail rule.

## 6. Validation and retained evidence

**At the exact commit**, in a clean clone (2026-10-07T19:10:12Z to
19:13:19Z):

- `make -C bringup/k3-b5 check`: PASS in 187 s. It cloned and built
  OpenSBI v1.6 and U-Boot v2022.10 (`u-boot.bin` `d96d1c22…`) itself.
  - Host tests: 21 scenarios, 8,240 assertions, GCC = Clang.
  - Port: 6 rules, 8 substitutions, B2's manifest matched.
  - Images: GCC and Clang, the seven variants, and the three U-Boot images
    pass the image checker; the mutation test rejects all 17 defects.
  - Markers: 126 self-test cases; the sources check finds all 22 lines.
  - QEMU: `BE_K3_B5_QEMU: PASS scenarios=12 runs=17`.
  - U-Boot rehearsal: GCC, Clang, and `k3-address` pass.
  - Board-tool dry run: seven cases pass.
- The four retained excerpts pass `check-b5-capture.py` on their own, and
  `MANIFEST.sha256` verifies.
- The rebuilt U-Boot images match the board images: GCC `3630ac0e…9d3eb3`,
  Clang `4191023e…ff5153`.

**On the board**, 2026-10-07: runs `20261007T183419Z`, `20261007T185605Z`,
`20261007T185940Z` (GCC), and `20261007T190247Z` (Clang), each with
`check_status=0` and `after_reset=no`; preflight PASS before run 1.

**Retained:** `bringup/k3-b5/results/20261007-com260/`: each run's
`run.txt`, `load.txt`, `check.txt`, `result.json`, and handoff excerpt;
the preflight; `summary.md`, `captures.txt`, `originals.sha256`, and
`MANIFEST.sha256`; and a README. The full serial captures, with the
board's TLV identity lines, are kept privately.

## 7. Recommended review sequence

1. Claims: section 3 above, then `bringup/k3-b5/README.md` (design, tests,
   K3 results) and the results README.
2. The monitor layer: `src/b5-trap.S` (exit vector and resume tail), then
   `src/b5-runtime.c` (sequence, controls, dispatch, console), then
   `src/b5-sbi.c` and `src/b5.h` (the SBI subset).
3. The guest: `guest/guest.c` and `guest/crt0.S`.
4. The checkers: `tests/check-b5-image.py`, `tests/check-b5-markers.py`.
5. The board records.

Read-only commands:

```sh
git --no-pager log --oneline 87be98f1..82956239
git --no-pager diff --stat 87be98f1..82956239
git --no-pager show 82956239:bringup/k3-b5/results/20261007-com260/README.md
git --no-pager show 82956239:bringup/k3-b5/src/b5-trap.S
git --no-pager show 82956239:bringup/k3-b5/src/b5-sbi.c
```

Exact-commit execution in a fresh worktree. B2 clones and builds OpenSBI
v1.6, and B3 clones and builds U-Boot, which needs network access:

```sh
git worktree add --detach /tmp/be-b5-review 829562395bf14fedbeea0beb82b30da15ec5f7cf
cd /tmp/be-b5-review
make -C bringup/k3-b5 check
cd - && git worktree remove --force /tmp/be-b5-review
```

## 8. Human decision checklist

The checklist is kept as presented. The decision is recorded in the
[decision record](#decision-record), not in these boxes.

- [ ] B5 matches the accepted plan: a tiny separately built VS guest on
      the accepted R3 path, a bounded B5-only SBI subset, the hardware
      Sstc timer, and RAM-only U-Boot runs.
- [ ] The monitor layer and the SBI subset are correct, and the guest
      cannot reach M-mode, read outside its pages, or forge monitor lines.
- [ ] The implementation choices and integration decisions in section 5
      are acceptable.
- [ ] The claims in section 3 match the evidence, including the set-aside
      attempt.
- [ ] Unpinned workstation tools and no proof for the B5 layer are
      acceptable for this bring-up milestone.
- [ ] Successor work remains excluded until separately directed.
- [ ] Decision: accept exact commit `82956239`, request revisions, or
      defer.

## 9. After the decision

- **Accept:** record acceptance of exact SHA
  `829562395bf14fedbeea0beb82b30da15ec5f7cf` with its date and instruction
  in a follow-up record. Merging B5 into the development branch, pushing,
  and any successor each still need your direction.
- **Request revisions:** make a new commit and a new packet. `82956239` is
  not treated as accepted.
- **Defer:** keep the current status and start no dependent work.

**Status:** exact commit `82956239` is responsible-human accepted as of
2026-10-07. The B5 guest ran to its shutdown, with its own VS timer
interrupt, in 4 of 4 RAM-only COM260 runs.

**Next:** a successor needs your direction. Candidates include merging B5
into the development branch and pushing it, and a next guest step under a
new bounded plan, such as more guest RAM or a Linux guest. None is started
or authorized.

**Action required from you:** none for B5.
