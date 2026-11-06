<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M0 plan: the MVP line, multi-hart substrate, and evaluation harness

## Decision record

The responsible human accepted this plan at exact commit
`4d129808979cb54b7e0a7cc0b3e79d39533e0b9c` (parent
`391cfaed3e7a097660b11026472ecd64694f18d5`) on 2026-10-23. The
instruction, given in reply to the
[review packet](mvp-m0-plan-review-summary.md)'s request to accept,
revise, or defer that exact commit, was
`accept 4d129808, proceed with implementation using opus-5.5 model`,
whose abbreviation resolves uniquely to that commit.

- **Scope:** acceptance covers exactly the plan text at that commit,
  revision 2. Everything after this section is the plan as accepted,
  including the pre-decision status text below; only this section and
  the acceptance fields in the status record were set afterwards. The
  first candidate `6e4b9d4a` and revision 1 `d95b28e9` stay superseded
  and were never accepted.
- **Authorized:** M0 implementation under this plan, work packages M0-1
  to M0-6, on branch `beryllium/mvp-m0` from the acceptance-record
  commit: the new tree `mvp/` and its tests, seeded from B7 by B7's
  counted port method; the tool lock and the digest-pinned evaluator
  image; building the pinned upstream Linux `v7.2` with its `nolibc`
  userland; the QEMU rehearsals with eight harts, including the kexec
  rehearsal; the read-only Fedora preflight; RAM-only COM260 runs through
  Linux kexec as [Board safety and procedure](#board-safety-and-procedure)
  lists them, with a human reset after each; and the platform record,
  ending in one result review packet. Each
  [stop condition](#stop-conditions) returns M0 to the responsible
  human. The same instruction directs that the implementation use the
  `claude-opus-5.5` model, the pinned model of
  `.github/copilot-instructions.md`.
- **Open questions:** Q1 to Q13 were not answered, so the defaults
  apply: the hart region at `0x1_0204_4000` (Q1); the shim's start rule
  (Q2); the `BE_MVP:` identifiers and SBI version 3 (Q3); the IPI probe
  inside the scenario (Q4); the ticks-based overlap and K = 8 (Q5);
  eight board runs (Q6); the digest-pinned Fedora evaluator (Q7); the
  lock roles without Node.js (Q8); JSON scenarios (Q9); the domain
  hart's 2^24-tick wait before its own `FAIL` (Q10); B7's exit ceiling
  and run budget (Q11); harts 1 and 2 as the domain harts (Q12); and GCC
  only for the probe images on the board (Q13).
- **Not authorized:** everything the plan excludes, including any M1 or
  later deliverable; a scheduler, time-multiplexing, migration,
  overcommit, a third domain hart, or a hart started or stopped after
  the barrier; devices, MMIO, interrupt controllers, DMA, or
  guest-visible injection beyond each domain's timer; a change to any
  accepted R0-R7 or B0-B7 byte or accepted document's text; root
  integration; an HS-to-M SBI call beyond the accepted four plus HSM
  `hart_start`, HSM `hart_get_status`, and IPI `send_ipi`; a U-Boot run
  or automation typing at U-Boot; any persistent firmware, U-Boot
  environment, flash, boot-configuration, or storage change; and push,
  tag, publication, release, or any successor, including M1.
- **Evidence status:** acceptance adds no implementation, emulation, or
  board evidence. No M0 implementation had started at the accepted
  commit; the planning research the plan cites is not M0 evidence.

## Decision requested

**Status:** accepted on 2026-10-23; see the
[decision record](#decision-record). As presented, the plan was
proposed and not accepted, as the paragraph below states.

**Status as presented:** proposed for responsible-human review; not
accepted. No M0
implementation has started: `mvp/` does not exist, and nothing has been
built or run for M0. Facts cited below come from the B-series records and
sources, the accepted documents, the B7 preflight record, and three
read-only planning measurements, two against B7's existing build outputs
and one with a scratch QEMU probe that is not Beryllium code;
inferences are marked. This is revision 2 of the plan: the first
candidate, `6e4b9d4a`, was revised the same day on the responsible
human's question whether any hart number is special, adding
[Hart identifiers](#hart-identifiers) and two measurements (revision 1,
`d95b28e9`); revision 2 adds the third measurement, a scratch QEMU probe
of HSM hart start and IPI delivery. Both earlier candidates are
superseded and were never accepted.

The accepted [MVP plan](mvp-plan.md) (exact commit `93967fba`, accepted
2026-10-23, instruction `accept 93967fba`) selects M0 as the first MVP
milestone and authorizes "writing M0's bounded plan, which includes the
static multi-hart substrate, on a new branch from the development branch".
On 2026-10-23 the responsible human chose option `(b)`, the start of M0's
plan, without directing the development-branch fast-forward. The
development branch is therefore still at `0096de3e` and does not hold the
accepted MVP plan, so this plan's branch, `beryllium/mvp-m0-plan`, starts
from the S3 acceptance record `1fb46419`, whose ancestor is the development
branch tip; a later fast-forward of the development branch to `1fb46419`
would make the two the same. Writing this plan authorizes no
implementation, hart start, board run, or push.

The responsible human is asked to decide on the exact commit that adds
this plan on branch `beryllium/mvp-m0-plan`:

- **Accept:** authorizes M0 implementation under this plan, work packages
  M0-1 to M0-6: the new tree `mvp/` and its tests, seeded from B7 by B7's
  counted port method; the tool lock and the digest-pinned evaluator
  image; building the pinned upstream Linux `v7.2`, the same external
  guest input as B6 and B7, with its `nolibc` userland; the QEMU
  rehearsals with eight harts, including the kexec rehearsal; the
  read-only Fedora preflight; RAM-only COM260 runs through Linux kexec,
  as [Board safety and procedure](#board-safety-and-procedure) lists
  them; and the platform record. It ends in one result review packet.
  Each [stop condition](#stop-conditions) returns M0 to the responsible
  human.
- **Request revisions** or **defer:** M0 stays unstarted.

Acceptance would not authorize:

- any M1 or later deliverable: a shared page or channel between the
  domains, fault injection or denial logging with resume, a policy or
  manifest checker, the authority report, a management extension, a
  measurement, or Model changes;
- a scheduler, time-multiplexing, domain migration or overcommit, a third
  domain hart, starting or stopping a hart after the boot barrier, or a
  lock held across guest execution;
- devices, MMIO, interrupt controllers, DMA, or guest-visible interrupt
  injection beyond each domain's own timer;
- a development-kernel/BSP selection, or any change to the board's host
  kernel;
- a change to any accepted R0-R7 or B0-B7 byte, to an accepted document's
  text, or to a retained R8 input;
- root `Makefile`, `be`, or `scripts/check-be.sh` integration (MVP plan
  D3);
- an HS-to-M SBI call beyond the accepted four plus HSM `hart_start`,
  HSM `hart_get_status`, and IPI `send_ipi`;
- a U-Boot run, or automation typing at U-Boot;
- any persistent firmware, U-Boot environment, flash, boot-configuration,
  or storage change;
- push, tag, publication, release, or any successor, including M1.

### Open questions

Each has a default, so acceptance can proceed without answers.

| # | Question | Default if unanswered |
| --- | --- | --- |
| Q1 | Where do the domain harts' stacks, saved pages, blocks, and rings live? | A NOLOAD hart region of two 64 KiB blocks at HPA `0x1_0204_4000`, after B7's pool and below Fedora's kernel at `0x1_0220_0000`; each block holds the hart's 8 KiB trusted stack, its saved page at the stack top, its state page, a 4 KiB inbound ring, and a 32 KiB outbound ring ([Hart region](#hart-region)) |
| Q2 | QEMU with eight harts picks a boot hart other than 0 in most runs (planning research 2; [Boot sequence](#boot-sequence-on-hart-0)); what then? | The MVP shim, a counted copy of B3's, starts hart 0 through HSM `hart_start` at its own entry with the same FDT and parks, so hart 0 always runs the monitor and the accepted R3 hart check stands. The alternative, accepting any boot hart as the control hart, needs a change to the accepted R3 boot check and is a stop; it is the better long-term contract ([Hart identifiers](#hart-identifiers)) and belongs to the clean-repository boot design |
| Q3 | Identifiers? | `BE_MVP:` (control-hart lines), `BE_MVP_G0: ` and `BE_MVP_G1: ` (domain lines, from the scenario's domain names), `MVPINIT` (init lines), DT model "Beryllium MVP guest" and compatible "beryllium,mvp-guest", SBI implementation ID `0x4245`, version 3 unchanged, because M0 changes nothing the guest sees through SBI (MVP plan D8) |
| Q4 | Is the IPI probe part of the two-guest scenario? | Yes: when hart 0 drains a domain's first console line, it sends that domain's hart one PING; the hart answers PONG from its fast path. The alternative keeps IPI delivery at V=1 in the probe image only |
| Q5 | How is "both domains ran concurrently" checked? | From recorded ticks: the two domains' entry-to-shutdown intervals overlap by at least half of the shorter, and hart 0's drained console shows at least K = 8 alternations between the domains' lines ([Markers](#markers)) |
| Q6 | Board campaign size? | Eight RAM-only kexec runs with a human reset after each: the three probe images (GCC), the two-guest scenario (three GCC, one Clang), and the `payload` negative image (GCC). The alternative drops the negative run and the IPI probe image to six |
| Q7 | The evaluator image? | A Containerfile from a digest-pinned Fedora base, as `model/Containerfile`, installing the exact package closure the tool lock records, with the kernel source mounted read-only from a local mirror; it runs with no network ([Tool lock and evaluator](#tool-lock-and-the-clean-evaluator)) |
| Q8 | Tool-lock roles? | GNU Make, bash, Python 3, the cross GCC and binutils, Clang and LLD, the host GCC and Clang for host tests, QEMU, `dtc`, `sha256sum`, `rpm`, `git`, and the Linux and OpenSBI source pins. No Node.js: the MVP line has no JavaScript, which removes the role whose version broke the R6 and R7 locks on this host |
| Q9 | The scenario encoding? | JSON, as D9 chose for the authority report, consumed by one generator that emits a C header, the DTBs, and the checkers' expectations |
| Q10 | If a domain hart fails and hart 0 does not acknowledge? | The hart waits 2^24 ticks (0.7 s) for hart 0's acknowledgement in its inbound ring, then prints its `FAIL` line itself and requests SRST ([Failure paths](#failure-paths)) |
| Q11 | Exit ceiling and run budget? | B7's: 2^20 exits per domain and 2^32 ticks per run (179 s at 24 MHz), the budget kept on hart 0's Sstc timer (MVP plan Q9) |
| Q12 | Which physical harts run the domains? | 1 and 2 as the device tree numbers them, as the accepted MVP plan's Q12 default; they are scenario data, validated at boot, and nothing in the monitor depends on the values ([Hart identifiers](#hart-identifiers)). M0 records each hart's cluster; the choice stands unless the ordering probe fails on it |
| Q13 | Clang builds of the probe images on the board? | No: the probes run on the board from the GCC build only; Clang builds pass the same QEMU runs |

## Goal and pass criterion

M0 delivers the maintained MVP source line `mvp/`, seeded from B7; a tool
lock the development host satisfies and a digest-pinned clean evaluator;
the evaluation harness, with scenarios as data and B7's two-guest scenario
re-hosted on two domain harts as its first scenario; the static multi-hart
substrate of the accepted MVP plan's [Hart layout](mvp-plan.md#hart-layout);
and a K3 platform record from bounded probes and negative images. M0
passes when, in QEMU with eight harts and on the COM260 under the default
board campaign, both Linux domains boot on their own harts, run to
power-off concurrently, and the [capture checker](#markers) accepts every
capture; the negative images fail as declared; the probe images report
their facts in the declared format; and the harness, the tool lock, and
the evaluator pass their own checks, with every image byte-identical
between the development host and the evaluator.

## Base and inputs

- **Base:** `beryllium/mvp-m0-plan` from `1fb46419`, the S3 acceptance
  record, which holds accepted B0-B7, the accepted-tool fixes, S1, S2,
  and the accepted MVP plan. Implementation would run on a branch
  `beryllium/mvp-m0` from this plan's acceptance record.
- **Governing plan:** the accepted [MVP plan](mvp-plan.md) (`93967fba`):
  M0's deliverables 1 to 5 and exit, the hart layout, D1 to D16, Q1 to
  Q12 at their defaults, the harness rules, and stop conditions 1 to 7.
  This plan implements M0 within it and changes nothing in it.
- **Reused unchanged:** B2's `scripts/port.py` output rules and pinned
  inputs, B1's `src/b1-handoff.S`, B0's retention and summary tools and
  rehearsal `mkcpio.py`, B6's `scripts/fetch-linux.sh` and
  `guest/b6-kernel.config`. Everything else M0 takes from B7 is a counted
  copy under `mvp/` ([Port and copies](#port-and-copies)); `bringup/`
  does not change.
- **External input, never committed:** B6's and B7's Linux `v7.2`
  (`8d3ae59288f1e7d58d76558a6ee96d533bc5019f`, tag object
  `237a1c39e8dfd3e1c6f1f023eea37a48ec04cc63`), with its UAPI headers and
  `tools/include/nolibc` for the userland, and OpenSBI `v1.6`
  (`bd613dd9`) for the QEMU profile. There is no new external input.
- **Platform facts:** the B7 preflight
  (`bringup/k3-b7/results/20261008-com260/preflight.txt`): eight `cpu@N`
  nodes, each listing `h`, `sstc`, `smaia`, `ssaia`, `svinval`,
  `sstvala`, and `shtvala`; `online_cpus=0-7`; `timebase_frequency=
  24000000`; "SBI HSM extension detected" in Fedora's boot log. The B1
  and B2 records: "Linux stopped its other harts before each kexec". The
  B7 records: `VMID 14 bits available`; no `/proc/iomem` child or FDT
  reservation in `0x1_05e0_0000`-`0x2_ee04_7fff`; the pool at
  `0x1_0203_4000` below Fedora's kernel at `0x1_0220_0000`; 583 and 594
  exits per guest per board run, of which about 360 `wfi` and 65 slice
  exits; and about 10 KB of console output per guest, the longest line
  190 characters. No Beryllium image has started a second hart, taken an
  IPI in HS, or shared a page between harts; every multi-hart behaviour
  below is design, shown so far only by the scratch probe of planning
  research 3 in QEMU, and to be shown by M0 first in QEMU and then on
  the board.
- **Design inputs:** the research document's "Why the monitor executes on
  every hart", "Smallest multicore experiment", and "Per-hart and global
  state" (L165-L251 at `0096de3e`); the implementation plan's Stage 2
  (L1211-L1220); the H-extension and SBI specifications for HSM, IPI,
  and the supervisor software interrupt. *Fact* marks what a record or
  source shows, *inference* reasoning from facts; upstream sources are
  `path:line@v7.2`.
- **Planning research:** three read-only measurements made for this plan
  on 2026-10-23, with scratch under `build/mvp-research/` (gitignored):
  "planning research 1", the sizes of the B7 symbols M0 drops, from
  `riscv64-linux-gnu-nm -S` on both toolchains' existing B7 images under
  `build/k3-b7/`; "planning research 2", QEMU's boot-hart choice over ten
  eight-hart runs of B7's GCC boot ELF under the pinned OpenSBI v1.6;
  and "planning research 3", a 2.4 KiB freestanding S-mode probe, not
  Beryllium code and never committed, that under the same QEMU and
  firmware reads every hart's HSM status, starts the lowest stopped hart
  with an opaque word, exchanges an SBI IPI in each direction with the
  receiver waiting in `wfi` with `sie.SSIE` set and `sstatus.SIE` clear,
  and passes a fenced payload and acknowledgement word between the
  harts. They are planning facts, not M0 evidence; no Beryllium image
  has started a second hart or taken an IPI.

## Architecture

### Hart identifiers

No hart number is special to the architecture. A RISC-V hart ID is a
name: the ISA requires only that some hart has ID 0, and the project's
rule that identifiers are not authority (S1 H03; security model v1,
"Object classes") applies to hart IDs as to domain indices, VMIDs, and
GPAs. In M0 the hart IDs are configuration:

- **The control hart is fixed at hart 0,** for three reasons that are
  about accepted code and the platform, not the number. First, the
  accepted R3 boot check requires the booting hart to be hart 0
  (`virt/be/r3.c:292`, `BE_CONFIGURATION_HART_ID`), and the accepted B3
  shim parks every other hart (`bringup/k3-b3/src/b3-shim.S`); changing
  either is an accepted-byte change, stop condition 1. Second, a static
  binding needs a fixed control-hart ID: if the control hart were
  whichever hart booted, the domain harts would have to be chosen
  relative to it at run time, and the binding could no longer be sealed
  offline and validated at boot. Third, every B-series board run entered
  on hart 0 through both U-Boot and Linux kexec (`SHIM hart=0x0` in every
  record), and the ISA guarantees that hart 0 exists.
- **The domain harts are scenario data** (`scenario.json`, [Scenarios
  and the harness](#scenarios-and-the-harness); Q12): the binding names
  them, the generator emits them into the layout header and the
  expectations, and hart 0 validates them at boot, each must exist in
  the firmware's view, be `STOPPED`, and start. Nothing in the monitor's
  code depends on their values being 1 and 2.
- **The shim's start rule** (Q2) exists only to make a QEMU machine with
  eight harts conform to the accepted hart-0 check; it adds no meaning to
  hart 0 and would be unnecessary under a boot contract that accepted any
  boot hart as the control hart. Such a contract is a candidate for the
  clean-repository boot design, where the binding would be resolved
  against a platform hart list; it is outside M0.

### What M0 takes from B7 and what it drops

| Area | B7 | M0 |
| --- | --- | --- |
| Harts | One; the shim parks the rest | Hart 0 controls (fixed by the accepted boot check), the two domain harts named by the scenario, 1 and 2 by default, each run one domain, and the rest are never started ([Hart identifiers](#hart-identifiers)) |
| Guests | Two, time-shared | Two, one per hart, concurrent |
| Scheduler, HS slice, `wfi` trap (VTW), per-switch save and restore | Yes | None: VTW clear, native `wfi`, no `stimecmp` write but hart 0's budget, no `vs*` write after each hart's arming but TIME's `vstimecmp` |
| G-stage | Two roots, VMIDs 1 and 2, installed on every switch | Two roots, VMIDs 1 and 2, each installed once on its hart |
| Exit record | The management saved page | One saved page per domain hart, at its trusted-stack top |
| HS interrupts | The supervisor timer while V=1 | The supervisor software interrupt (IPI) while V=1 and in hart 0's wait; the supervisor timer in hart 0's wait only |
| Console | Per-guest line buffers; the running hart writes the firmware console | Per-hart line buffers; lines travel by ring to hart 0, the only firmware console writer |
| Firmware SBI calls | Base probes, DBCN write, SRST | Plus HSM `hart_start` and `hart_get_status`, and IPI `send_ipi` |
| Guest SBI | Base, TIME, DBCN, SRST, version 3 | The same, unchanged |
| Tree | `bringup/k3-b7/`, a generated copy of B6 | `mvp/`, one maintained tree, seeded once from B7 |
| Tools | This workstation's, unpinned | The tool lock and the evaluator image |
| Checks | Markers fixed in the checker | Scenarios as data; the checker reads the scenario's expectations |

The R3 prelude, the payload checks, the window clear and copy, the pure-C
SBI core, the G-stage builder and walker, and the checked resume tail stay
B7's, with counted changes. Every `hgatp` write and `hfence.gvma` stays
inside the accepted R3 functions.

### The MVP line

`mvp/` is self-contained (MVP plan D3) and keeps the B-series shape:

```text
mvp/
  mvp                 the stable wrapper: check, image, qemu, kexec-rehearsal,
                      k3-preflight, k3-load-check, k3-probe, k3-campaign,
                      evidence, tool-lock, evaluate
  Makefile, guest.mk, tools.mk, make-control.py
  src/                the monitor: layout, runtime, trap, hart, ring, sbi,
                      gstage, payload, console, boot.lds, probe module
  shim/               the MVP shim, a counted copy of B3's
  guest/              the nolibc init, the DTS template, pins, the VS probe stub
  scenarios/          two-guests/scenario.json and its expectations
  tools/              gen-scenario.py, port.py, build-guest.sh, gen-dts.py,
                      gen-payload.py, kexec-load.py, k3-*.sh, lock/, evaluator/
  tests/              host tests, image checker, capture checker, mutation
                      tests, run-qemu.sh, kexec-rehearsal.sh, dry runs
  results/            retained board records
  README.md           counted change tables, measured budgets, results
```

Accepted R-series code enters through `tools/port.py`, B7's generator with
B7's rules plus one: the hart region. Later milestones change `mvp/` in
place (MVP plan M0 deliverable 1), so `mvp/README.md` carries the change
tables from B7 and every later diff is an ordinary commit.

### Hart region

Hart 0 keeps the accepted layout: the R3 prelude runs on the management
trusted stack (top `0x1_0202_7000`) and installs the management root as
B6 and B7 do; hart 0 never enters a domain, so it needs no saved page.
Each domain hart h (1 or 2) owns one 64 KiB block in a NOLOAD region
after B7's pool (Q1), written only at run time:

| Offset in block | Bytes | Content | Writer |
| --- | --- | --- | --- |
| `0x0000` | `0x2000` | Trusted stack; the top is the block's `sscratch` | Hart h |
| `0x2000` | `0x1000` | Saved page: the exit record, at the stack top, so the vector and the tail derive it from `sscratch` | Hart h |
| `0x3000` | `0x1000` | State page: hart id, domain, `hgatp`, the first-entry frame, the armed readbacks, counters, the 256-byte line buffer, the ring indices (each in its own 64-byte line) | Hart 0 before the barrier; hart h after |
| `0x4000` | `0x1000` | Inbound ring: hart 0 writes, hart h reads (PING; M2's commands later) | Hart 0 |
| `0x5000` | `0x8000` | Outbound ring: hart h writes, hart 0 reads (console lines, READY, ENTERED, PONG, SHUTDOWN, FAIL) | Hart h |
| `0xd000` | `0x3000` | Unused | |

The region is `0x1_0204_4000`-`0x1_0206_3fff`: block 0 (hart 1) at
`0x1_0204_4000`, block 1 (hart 2) at `0x1_0205_4000`. A static `ASSERT`
and the image checker keep it disjoint from the monitor, the pool, the
staged image, the kexec FDT slot, and both windows; the kexec loader's
layout rule adds it to the ranges it checks against `/proc/iomem` and the
FDT reservations. Inference: the region lies in the same free RAM as
B7's pool, between the monitor image and Fedora's kernel.

**Rings.** A ring is a power-of-two byte buffer with a head the writer
owns and a tail the reader owns, each in its own 64-byte line in the
state page, and no atomic read-modify-write anywhere. The writer copies
a record, executes `fence w, w`, and advances the head; the reader reads
the head, executes `fence r, r`, copies the record, and advances the
tail. A record is a 16-byte header (type, domain, length, reserved, and
the writer's `time`) and at most 256 payload bytes. A writer that finds
no room fails closed (MVP plan M0 deliverable 5). Inference: at B7's
measured 10 KB of console output per guest and about 120 lines, a 32 KiB
outbound ring holds a whole run's output with a margin above three, even
if hart 0 never drained it; each shutdown record reports the ring's
high-water mark, and [stop condition 3](#stop-conditions) applies above
half the capacity. The ring and block logic is pure C, host-tested, with
no CSR, SBI, or I/O (S1 H22).

### Boot sequence on hart 0

1. A loader places the boot image at L = `0x1_0800_0000` and enters the
   MVP shim. The shim copies the monitor to `0x1_0200_0000` and jumps,
   as B3's does. Fact (`b3-shim.S`): B3's shim parks any hart but 0.
   Fact (planning research 2): with `-smp 8`, QEMU's `virt` machine
   under the pinned OpenSBI v1.6 reported `Boot HART ID` 3, 7, 2, 4, 3,
   4, 0, 5, 0, and 2 in ten runs of B7's GCC boot ELF; the two runs on
   hart 0 printed the shim line and ran, and the other eight never
   reached the shim line, because B3's shim parked the boot hart. With
   `-smp 1` the boot hart is 0. On the board, Linux kexec runs on hart 0
   and U-Boot boots hart 0 (every B-series `SHIM hart=0x0` line). The MVP
   shim adds one rule (Q2): a hart other than 0 prints
   `BE_MVP_SHIM: boot_hart=0x<h> starting hart 0`, calls HSM
   `hart_start(0, shim entry, a1)`, and parks; a failed call parks too,
   which the run's timeout reports as a hang. Hart 0 then runs the shim
   with its own id and the same FDT. The rule would also cover a kexec
   from another hart, which no B-series run saw. QEMU exercises it
   deterministically through the `shim-rule` variant
   ([QEMU scenarios](#tests-and-evidence)), and the eight-hart scenario
   runs exercise it whenever the lottery picks another hart, in about
   four runs of five by the measurement above.
2. The accepted R3 sequence prints `BE_R3:01`-`:06` on hart 0.
3. Hart 0 probes HSM and IPI through the accepted probe helper and reads
   `hart_get_status` for harts 1 to 7 (`BE_MVP:02`); a missing extension
   or a hart not `STOPPED` fails closed. It builds and re-walks both roots
   (`BE_MVP:03`), checks the payload once (`:04`), zeroes both windows
   (`:05`), and copies the kernel into both windows and each DTB into its
   own (`:06`), as B7 does, then executes a data `fence`.
4. Hart 0 fills both blocks: hart id, domain, `hgatp`, the first-entry
   frame (`sepc` `0x8020_0000`, `a0` 0, `a1` `0x83e0_0000`, other GPRs
   0), zero ring indices, and the generation word last, after a `fence
   w, w`. This is the boot barrier's publication (`BE_MVP:07`). It arms
   its own budget: `stimecmp` = now + 2^32 ticks, `sie` = SSIE | STIE.
5. Hart 0 calls `hart_start(h, hart entry, block h)` for h = 1 then 2,
   and polls `hart_get_status(h)` until `STARTED`, within 2^24 ticks
   (`BE_MVP:08` per hart); a failure or a timeout is `FAIL hart-start`.
   After this step no hart is started or stopped, no root is written,
   and no frame changes owner. Fact (planning research 3): in eight
   eight-hart QEMU runs, six on the `k3-like` machine and two on `plic`,
   with boot harts 0, 3, 4, and 7, every non-boot hart reported HSM
   status `STOPPED` (1), `hart_start` of the lowest stopped hart
   returned 0 and the hart reached `STARTED` within `0x2c26`-`0x4331`
   ticks of QEMU's 10 MHz timebase (1.1-1.7 ms), with the opaque word
   delivered in `a1`; with one hart, `hart_get_status` of a nonexistent
   hart returned error -3 (`SBI_ERR_INVALID_PARAM`), so step 3 treats
   an error as "not `STOPPED`" and fails closed.
6. Hart 0 enters the control loop ([below](#control-loop)).

### Domain hart entry and fast path

A started hart arrives at the hart entry in HS with `a0` = its id and
`a1` = its block. The entry, in assembly, sets `sp` to the block's stack
top before any other memory access, then calls C, which:

1. checks `a0` against the block's hart id and the generation word
   against the published value after a `fence r, r`; a mismatch parks the
   hart (there is no console yet);
2. calls the accepted `be_r3_arch_reset_state` with the MVP trap vector,
   then the MVP arm helper: `vstimecmp` = ~0, `hedeleg` `0xb15d` (WARL),
   `hideleg` VSTI, `hcounteren` TM, `henvcfg` STCE, `sscratch` = the
   stack top, `hstatus` VTVM, VTSR, and VTW clear, `sie` = SSIE;
3. installs the domain's root through the accepted install function and
   requires the readback to equal the block's `hgatp`; writes the initial
   per-domain CSR set once (all zero, `vstimecmp` ~0) and reads it back;
4. executes `fence.i`, the image's one, so its fetches observe the
   kernel hart 0 placed (the writer's data `fence` came before the
   barrier);
5. posts READY with its readbacks, then ENTERED, to its outbound ring,
   sends hart 0 an IPI, copies the first-entry frame into its saved page,
   and enters the domain through the checked resume tail.

Every exit traps to the MVP vector, a counted copy of B7's: it exchanges
`sp` and `sscratch`, derives the record from the stack top, requires the
top to lie in the hart region at a block's `0x2000` offset, saves the
frame and the exit CSRs, and enters C with monitor values only. The
dispatcher serves:

| Exit | Service | Resume |
| --- | --- | --- |
| VS `ecall` (cause 10), Base, TIME, or SRST | B7's SBI core with the hart's own state; TIME writes the hart's `vstimecmp`; SRST shutdown with reason 0 posts SHUTDOWN with the counters and parks the hart in HS `wfi` | Same domain, except after a shutdown |
| VS `ecall`, DBCN write | Bytes copied from the domain's walked window into the hart's line buffer; each completed line, or a full buffer, posts one LINE record and one IPI; DBCN read returns -4 | Same domain |
| Supervisor software interrupt (cause `0x8000000000000001`) | Clears `sip.SSIP`, drains the inbound ring; a PING posts PONG with the receipt time; anything else is `FAIL ipi` | Same domain |
| Anything else: another interrupt, an exception, a guest-page fault, a reboot, an exit beyond the ceiling | Terminal for the run, as in B7 (its Q8) | None |

The resume tail checks every control, this hart's `hgatp` and
`sscratch`, `satp` 0, `stvec`, `sie` = SSIE, and `sstatus`, sets SPP from
the saved SPVP, restores the frame, and executes one SRET. Nothing in the
fast path reads or writes another hart's block, a shared word, or
anything hart 0 writes after the barrier except the inbound ring.

### Control loop

Hart 0 waits in `wfi` with `sstatus.SIE` 0 and `sie` = SSIE | STIE, as
B7's wait did for the timer. Fact (planning research 3): in the eight
QEMU runs above, an SBI IPI sent by the started hart woke the boot hart
from exactly this wait in every run, with `sip.SSIP` set and cleared by
a `csrc`, `0x2011`-`0x2a7b` ticks (0.8-1.1 ms of TCG time) after the
send; the reply IPI to the started hart, also waiting in `wfi`, and its
fenced acknowledgement word completed the round trip in
`0xa47`-`0x16ae` ticks. Those are emulation facts about SBI IPIs between
harts in HS, not about delivery while a domain runs at V=1, which the
`probe-platform` image measures. On each wake it clears `sip.SSIP`, drains
block 0's ring and then block 1's, and acts on each record: a LINE is
written to the firmware console with its domain's prefix in one DBCN
write; READY and ENTERED print `BE_MVP:09` and `:10`; the first LINE of a
domain sends that hart one PING (Q4), and its PONG prints `BE_MVP:11`;
SHUTDOWN prints `BE_MVP:12`; FAIL prints the hart's `FAIL` and `DETAIL`
lines and ends the run. When both domains have shut down, hart 0 prints
`BE_MVP:13` and `:14` and requests the accepted SRST shutdown. A wake by
STIP means the budget expired: `FAIL run-timeout`. Hart 0's loop is the
only steady-state writer of the console, the denial log (empty in M0), and
the run's counters; it never writes a domain hart's block after the
barrier except the inbound ring.

### Failure paths

- **Hart 0:** `BE_MVP:FAIL <class>`, a `DETAIL` line, and the SRST
  request, as B7's terminal path; classes are B7's plus `firmware`
  (a missing HSM or IPI extension, or a hart not `STOPPED`),
  `hart-start`, `hart-ready` (no READY within 2^26 ticks),
  `run-timeout`, `ring`, and `ipi`.
- **A domain hart:** posts FAIL with the class and detail, sends an IPI,
  and waits up to 2^24 ticks for hart 0's acknowledgement in its inbound
  ring, then parks; without the acknowledgement it prints the two lines
  itself through DBCN and requests SRST (Q10), so a wedged hart 0 cannot
  hide a domain's failure. A full outbound ring is `FAIL ring` by the
  fallback path, since the ring cannot carry it.
- **Before the console exists:** a hart that fails its block check parks;
  the run then ends in `FAIL hart-ready` on hart 0.

### Guest controls

Armed on each domain hart by its arm helper after the accepted reset,
read back before its first entry, and checked at every resume.

| State | B7 | M0 | Checked |
| --- | --- | --- | --- |
| `hstatus` under the R3 mask `0x73f380` | `0x200180` (VTW set) | `0x180`: VTW, VTVM, and VTSR clear, B6's value | Arm, resume |
| `hedeleg`, `hideleg` | `0xb15d` (WARL; K3 reads `0xb15c`), `0x40` | Same | Arm, resume |
| `henvcfg`, `hcounteren`, `htimedelta` | STCE, `0x2`, 0 | Same, per hart | Arm, resume |
| `sie` | `0x20` (STIE) | `0x2` (SSIE) on domain harts; `0x22` on hart 0 | Arm, resume; hart 0's wait |
| `stimecmp` | The slice deadline, every resume | Hart 0's budget, written once | Image checker: one writer |
| `hvip` | VSSIP, VSTIP, VSEIP tested zero | Same | Arm, resume |
| `hgatp` | The running guest's, on every switch | This hart's domain's, once | Install readback, resume |
| `vs*`, `scounteren`, `senvcfg` | Per guest, by the load helper on every switch | Written once per hart at arming; `vstimecmp` also by TIME | Arm readback |
| `sscratch`, `stvec`, `satp` | The management top, the vector, 0 | This hart's stack top, the vector, 0 | Resume |
| `hstateen0`, `hvictl`, `hvien`, `hviprio1`/`2` | Never accessed | Never accessed | Stop 4 |

### Port and copies

`tools/port.py` is B7's with its rules and substitutions, with MVP names,
and one more rule: the NOLOAD hart region `.hart.mvp` at `0x1_0204_4000`
with its `ASSERT`s. Every accepted `ASSERT` stays, and `--check` re-derives
the tree byte for byte. Each copy gets a counted change table in
`mvp/README.md`.

| MVP file | From | Main counted changes |
| --- | --- | --- |
| `src/mvp-layout.h` | `src/b7-layout.h` | The hart region and blocks; per-domain harts and VMIDs; no slice; the ring sizes; the identifiers (Q3) |
| `src/mvp-hart.{h,c}`, `src/mvp-ring.{h,c}` | New | Block validation, the record format, ring push and pop, the control loop's state machine, the overlap computation: pure C |
| `src/mvp.h`, `src/mvp-sbi.c` | B7's | No `wfi` or slice class; the IPI class; per-hart state; line records instead of console writes; version 3 unchanged |
| `src/mvp-gstage.{h,c}`, `src/mvp-payload.{h,c}` | B7's | Names; a hart field per root |
| `src/mvp-runtime.c`, `src/mvp-platform.h` | B7's | Firmware probes, the blocks, hart start, the control loop; no scheduler, switch, or wait |
| `src/mvp-hartentry.S`, `src/mvp-trap.S` | New; B7's | The hart entry; the vector and tail derive the record from `sscratch`; the arm helper without VTW and STIE; the SSIP clear; no save, load, deadline, or wait helpers; the HS wait on either interrupt |
| `src/mvp-probe.{h,c}`, `guest/probe-stub.{c,S}` | New; B5's guest style | The probe module and the VS probe stub ([Platform record](#platform-record-probes-and-negative-images)) |
| `shim/mvp-shim.S` | B3's `src/b3-shim.S` | The boot-hart rule (Q2) and its line; the QEMU-only `shim-rule` variant's start-and-stop prologue |
| `src/mvp-boot.lds`, `src/mvp-guest-payload.S` | B7's | Names |
| `guest/`, `tools/build-guest.sh`, `gen-dts.py`, `gen-payload.py` | B7's | `MVPINIT`; the model and compatible; the scenario's `bootargs` |
| `tools/gen-scenario.py`, `scenarios/` | New | The scenario data and the generated header and expectations |
| `tests/`, `tools/k3-*.sh`, `tools/kexec-load.py`, `tools.mk`, `mvp` | B7's; new | Names and markers; eight-hart QEMU; the hart region in the layout rule; the preflight's hart topology, cache, and HSM facts; the probe campaign; the wrapper |

### Budgets

Every budget is hard; an overrun is a [stop](#stop-conditions).

| Budget | Limit | Basis |
| --- | --- | --- |
| Monitor text | Below `0x1_0200_8000` (accepted `ASSERT`) | Fact (B7 README): B7 ends at `0x1_0200_7000` (GCC, `0x1000` spare) and `0x1_0200_7910` (Clang, `0x6f0` spare), with its own C at `-Os`. Fact (planning research 1): the symbols M0 drops, the scheduler (`be_b7_sched_*`), the vCPU save, restore, and CSR helpers (`be_b7_vcpu_*`, `be_b7_vcsr_*`, `be_b7_arch_save_vcsr`, `be_b7_arch_load_vcsr`), the deadline, timer, and wait helpers, and Clang's out-of-line `schedule` and `switch_fail`, total about `0x3e0` bytes of text in the GCC image and `0x5c0` in the Clang image, plus about `0x3f0` of data (`be_b7_vcpus`, `be_b7_sched`) and `0xd0` of marker strings. Inference: the hart entry, block and ring logic, the control loop, the IPI handler, and three firmware calls add about `0x700`-`0xa00`, so M0's text lands about `0x300`-`0x600` above B7's for each toolchain, which is within the limit for GCC and within `0x100`-`0x400` of it for Clang. The probe module is linked only into the probe images. Measured at M0-3; if Clang overruns, stop 3 applies, and the remedy to propose is a counted port rule that grows the monitor code region with every accepted invariant substituted, which needs the responsible human's decision |
| Monitor data and BSS | At or below `0x1_0200_f000` (accepted `ASSERT`) | B7 ends at `0x1_0200_b688`; M0 moves per-domain state into the blocks and adds little |
| Flat image; pool; hart region | Exactly `0x34000`; `0x10000` at `0x1_0203_4000`; `0x20000` at `0x1_0204_4000` | B7's image and pool; Q1 |
| Kernel `Image`, DTBs, boot image | File at most 4 MiB, `image_size` at most 8 MiB; two of exactly 4 KiB; at most 4 MiB | B7's pins, unchanged but for `bootargs` and the model |
| Exits | 2^20 per domain (Q11) | Inference: about 160 per domain per run, B7's exits less its `wfi` and slice exits |
| Outbound ring high-water mark | At most half of 32 KiB | Inference above; measured at M0-4 and on the board |
| Run time | 2^32 ticks from publication (Q11) | Inference: about 1.5 s of guest time on the board, both domains running at once |
| Hart start; READY | 2^24 ticks per start; 2^26 ticks to READY | Inference: a start and an entry take milliseconds |

## Memory and load paths

| HPA | Use | Basis |
| --- | --- | --- |
| `0x1_0000_0000`-`0x1_01ff_ffff` | OpenSBI 1.6, no-map | B0-B7 records |
| `0x1_0200_0000`-`0x1_0203_3fff` | Monitor flat image (accepted layout) | As B7 |
| `0x1_0203_4000`-`0x1_0204_3fff` | Pool: domain 0's root `0x1_0203_4000`, domain 1's `0x1_0203_c000` | As B7 |
| `0x1_0204_4000`-`0x1_0206_3fff` | Hart region: block 0 (hart 1), block 1 (hart 2) | New (Q1) |
| L = `0x1_0800_0000`; the kexec FDT at L + 2 MiB | Staging, as B7 | B7 records |
| `0x1_1000_0000`-`0x1_13ff_ffff` | Domain 0's window | B7's G0 window |
| `0x1_1400_0000`-`0x1_17ff_ffff` | Domain 1's window | B7's G1 window |

Each domain sees B7's guest-physical layout in its own window. The boot
image is B7's: the shim page, the monitor at `0x1000`, the kernel at
`0x35000`, then the two DTBs. The board path is Linux `kexec_load` from
Fedora through B7's raw loader for every run; QEMU boots the boot ELF
directly with `-smp 8 -m 8G` (MVP plan Q10). No U-Boot run.

## G-stage and VMIDs

B7's builder and walker are reused: each root maps its domain's 64 MiB as
32 leaves of 2 MiB and nothing else, the walker re-derives every mapping
from the pool's bytes before any `hgatp` write, and a host test refuses two
roots that share a page. `hgatp` is `0x8000100000102034` for domain 0 on
hart 1 (VMID 1) and `0x800020000010203c` for domain 1 on hart 2 (VMID 2).
Each is installed once, on its hart, through the accepted install
function, and read back; after the barrier no hart writes `hgatp`, which
the image checker enforces as a single-writer rule, and the tail checks it
at every resume. Distinct VMIDs are kept as the MVP plan's scope states,
although on separate harts they are not needed for correctness; the
accepted install function's full `hfence.gvma` runs on each hart at
install. The install function has exactly two call sites in the MVP image:
R3's on hart 0 and the hart entry's; the probe image adds a third, in the
probe module.

## Guest SBI subset and the firmware surface

The guest sees B7's subset unchanged: Base (implementation ID `0x4245`,
version 3), TIME `set_timer` into the hart's `vstimecmp`, DBCN write from
the domain's walked window (read returns -4), and SRST shutdown with
reason 0, which stops the calling domain; every other call returns -2,
and a reboot or a shutdown with reason 1 is terminal. No guest request
reaches M-mode, and no SBI profile, guest ABI, or Linux interface is
selected.

The monitor's own calls to firmware grow from the accepted four (Base
`get_spec_version` and `probe_extension`, DBCN write, SRST) by HSM
`hart_start` and `hart_get_status` and IPI `send_ipi`, all through the
accepted `be_r3_arch_sbi_call` helper, so the image keeps one `ecall`
site. `mvp-sbi.h` names the two extensions and three functions; the
accepted `r0-sbi.h` allowlist is unchanged.

## Guest software

- **Kernel:** B7's uniprocessor `Image` from B6's fragment, rebuilt
  reproducibly with `kernel-repro`; only the built-in initramfs differs.
  Each domain runs it as one virtual CPU on one hart; the guest's hart id
  is 0 in its DT and in `a0`, whatever the physical hart.
- **Userland:** B7's `nolibc` init with the `MVPINIT` tag (Q3): the guest
  id from `argv`, eight compute-and-sleep steps, the 1 s sleep check, a
  result, and power-off; plus B7's `init-exit` and `rdcycle` QEMU-only
  variants. Fact (B7 result): on the board, Linux's `wfi` trapped 356 and
  363 times per guest; in M0 it completes natively, so the init's sleeps
  idle the hart.
- **Device trees:** B7's template with the MVP model and compatible; one
  DTB per domain, differing only in `bootargs`' guest digit.
- **Reference boot:** each DTB under plain OpenSBI v1.6, as B7.

## Scenarios and the harness

A scenario is data (MVP plan, "Evaluation harness"):
`scenarios/<name>/scenario.json` names the domains, their harts, windows,
roots, VMIDs, DTB `bootargs`, guest programs, and expected outcomes: the
control-hart lines in order, each domain's required lines in order, the
rejected substrings, the counters as exact values or ranges, the accepted
exit classes, and the concurrency floors (Q5). `tools/gen-scenario.py`
emits `mvp-scenario.h` for the build, the DTBs' `bootargs`, and the
expectation files the checkers read; a scenario change is a build, never a
run-time selection. Negative images are separately linked variants with
their own expectation files (S1 H27).

M0's one scenario is `two-guests`: domain G0 on hart 1 and G1 on hart 2,
B7's windows, roots, and VMIDs, B7's init, and the expectations in
[Markers](#markers). The harness stages are the MVP plan's:

| Stage | M0 implementation |
| --- | --- |
| Scenario | `scenario.json`, the generator, and the generated header |
| Offline checks | None in M0 (no policy or manifest yet); the stage exists and runs the pin checks |
| Build | `make -C mvp` through `make-control.py`, which rejects caller overrides, `MAKEFILES`, and `--eval` and accepts only exact toolchain values (S1 H33), with every tool taken from the lock |
| Run | Host tests; `tests/run-qemu.sh` with eight harts; `tests/kexec-rehearsal.sh`; the RAM-only board tools |
| Check | `tests/check-capture.py`: exact cardinality per stream and one parser run per file (S1 H26); cross-stream order only where the scenario declares it; counters exact or within range; the ticks-based overlap; the alternation floor |
| Evidence | `mvp evidence`: a bundle with a SHA-256 manifest, the tool record, and the scenario, kept under `mvp/results/` for board records and `build/mvp/evidence/` for development runs; no recorded path is ever executed (S1 H30) |
| Mutation | `tests/mutate-*.py`: seeded single-defect mutations of the image and capture checkers, each mapped to the claim that must fail (S1 H39) |
| Costs | From the records' `time` fields: per-exit ticks on each hart, the PING-to-PONG round trip, ring post-to-drain latency, and hart 0's idle ticks; recorded only |

`mvp check` runs every stage but the kernel rebuild, the kexec rehearsal,
the evaluator, and the board. The result packet reports the checking
code's size against the monitor's (S1 H43); inference from B7, about three
lines of checker and test per line of monitor, which M0 must justify or
reduce.

## Tool lock and the clean evaluator

- **The lock** (`tools/lock/tool-lock.conf`, schema `be-mvp-tool-lock-v1`)
  records, for each role in Q8, the command, the resolved executable, the
  version output, its SHA-256, and the owning package, as the R3-R7 locks
  do, plus the Linux and OpenSBI source pins. `mvp tool-lock check`
  verifies every role before any build and fails closed on drift; `mvp
  tool-lock refresh` rewrites the lock from the current host and is run
  only on the responsible human's direction after a tool update, so the
  diff is reviewed. The lock is designed for the development host from
  the start (project review option 7): its roles are the tools the MVP
  line uses, and nothing else.
- **The evaluator** (`tools/evaluator/Containerfile`, Q7) starts from a
  Fedora image named by digest, as `model/Containerfile` does, installs
  exactly the package closure the lock records (`closure.txt`, exact
  NEVRAs, no weak dependencies), and records `rpm -qa` into the image.
  `mvp evaluate` runs the gates inside it with networking disabled, the
  source mounted read-only, hidden build trees, `GIT_OPTIONAL_LOCKS=0`,
  and the kernel source mounted read-only from a local mirror (S1 H31).
  Inside, `tool-lock check` must pass with the same lock, and every image
  must equal the development host's byte for byte. The reproducibility
  wording is "digest-pinned base plus recorded closure" (S1 H32): the
  base is pinned by digest, the closure is recorded, and the registry's
  retention of both is the remaining assumption.

## Platform record: probes and negative images

The platform record (`mvp/results/<date>-com260/platform-record.md` and
`.json`) gathers facts for M1's design and the MVP claim. Nothing in it is
a claim; every value is recorded with its source.

**From the preflight** (read-only, extended from B7's): each hart's DT
node and extensions, `/cpus/cpu-map` and the cache nodes for the cluster
topology (MVP plan Q12), `/sys/devices/system/cpu/*/topology`, HSM
detection in Fedora's boot log, `/proc/iomem`, and the FDT reservations
against the hart region as well as B7's ranges. **From the serial log:**
the PMP and domain regions OpenSBI prints at power-on, which the
output-only capture includes before Fedora boots.

**From the probe images,** separately linked, GCC on the board (Q13), GCC
and Clang in QEMU, each one RAM-only kexec run:

| Image | Probe | Records | Expected on K3 |
| --- | --- | --- | --- |
| `probe-platform` | HSM `hart_get_status` for harts 1 to 7 | Each status | All `STOPPED` (1); otherwise stop 6 |
| | `hgatp` modes and VMID width: writes Sv48x4, Sv57x4, and Sv39x4 with VMID `0x3fff` through the accepted install function, reading each back, then restores the management root | The three readbacks | Sv39x4 with 14 VMID bits (B7 records); other modes recorded as facts |
| | Guest-page faults: hart 1 runs the VS probe stub, a bare-metal guest in B5's style mapped by a probe root; the stub loads from, stores to, and fetches from a GPA outside the root; the probe handler records each fault and re-enters the stub at its next label | `scause`, `htval`, `htinst`, `stval`, `sepc` per fault | `htval` = GPA >> 2 for each (S1 H16); `htinst` recorded; a different `htval` is stop 6 |
| | IPI delivery: hart 0 sends 100 IPIs to hart 1 waiting in HS, then 100 while the stub spins at V=1 | Delivered count; min, median, and max ticks from send to receipt; `hstatus.SPV` at receipt | 100 and 100; a miss is stop 6 |
| | Ordering: hart 0 writes a payload then a flag 10,000 times, hart 1 spins on the flag and reads the payload; once without fences, once with `fence w, w` and `fence r, r` | Stale reads in each mode | 0 with fences (otherwise stop 6); the unfenced count is a fact |
| `probe-vmid-distinct` | Hart 1 runs the stub under root A at VMID 1, reading GPA X ten times; the probe writes `hgatp` for root B at VMID 2 with no fence, a raw write the probe-image checker profile alone admits; the stub reads X again | The values read under A and after the switch | B's value (tagging by VMID); A's value is stop 6 |
| `probe-vmid-shared` | The same with root B at VMID 1 | The same | A fact either way: A's value shows a cached translation that needs the fence; B's shows none was cached |

The probe images run hart 0's prelude and the substrate, not the Linux
domains; the probe module replaces the payload placement. The raw `hgatp`
write exists only in the two VMID images and is the one exception to the
install-function rule, listed in the probe checker profile and tested by a
mutation. On the board the probe campaign precedes the scenario campaign,
so that the facts exist before the two-guest runs are read.

**Negative images** of the scenario, each separately linked:

| Variant | Toolchains | Where | Expected |
| --- | --- | --- | --- |
| `payload` (kernel `magic2` altered) | GCC | QEMU and board | `BE_MVP:FAIL payload` after `:03` |
| `exit-budget` (ceiling 64) | GCC | QEMU | `BE_MVP:FAIL exit-budget` with `DETAIL domain=<d> hart=<h>` |
| `run-timeout` (budget 2^20 ticks) | GCC | QEMU | `BE_MVP:FAIL run-timeout` on hart 0 |
| `ring-full` (outbound ring 1 KiB) | GCC | QEMU | `BE_MVP:FAIL ring` by the fallback path |
| `hart-start` (block 1 names hart 9) | GCC | QEMU | `BE_MVP:FAIL hart-start` |
| `init-exit` (G1 `rdinit=/init-exit`) | GCC | QEMU | `BE_MVP:FAIL guest-reboot`, `domain=1` |
| `rdcycle` (G0 `rdinit=/init-rdcycle`) | GCC | QEMU | `BE_MVP:FAIL virtual-instruction`, `domain=0`, cause 22 |
| `no-sstc` (the accepted R5 CPU) | GCC, Clang | QEMU | `BE_MVP:FAIL sstc` after `:02` |
| `sbi-3.0` (QEMU's OpenSBI 1.7) | GCC, Clang | QEMU | `BE_MVP:FAIL boot` before `BE_R3:01` |
| `sbi-time` (both DTBs without `sstc`) | GCC | QEMU | Pass, with `time` above 0 for each domain |

## Markers

A passing capture holds the shim line, then these lines in this order on
hart 0:

```text
BE_K3_B3: SHIM hart=0x0000000000000000 shim=0x0000000108000000 fdt=<f> dest=0x0000000102000000 bytes=0x0000000000034000
BE_R3:01 BOOT_VALIDATED
BE_R3:02 R1_DERIVED
BE_R3:03 R2_BUILT_REWALKED
BE_R3:04 HS_VS_STATE_VERIFIED
BE_R3:05 BINDING_PREPARED
BE_R3:06 HGATP_FENCED_PUBLISHED
BE_MVP:01 SCENARIO name=two-guests domains=2 harts=0,1,2 of=8 ring_bytes=0x8000
BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 status=1:1,2:1,3:1,4:1,5:1,6:1,7:1
BE_MVP:03 GSTAGE_BUILT_REWALKED domain=0 hart=1 gpa=0x80000000 hpa=0x110000000 size=0x4000000 leaves=32 root=0x102034000 vmid=1
BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1 hart=2 gpa=0x80000000 hpa=0x114000000 size=0x4000000 leaves=32 root=0x10203c000 vmid=2
BE_MVP:04 PAYLOAD_CHECKED kernel_bytes=<K> image_size=<S>
BE_MVP:05 DOMAIN_RAM_CLEARED domain=0 gpa=0x80000000 size=0x4000000 ticks=<T>
BE_MVP:05 DOMAIN_RAM_CLEARED domain=1 gpa=0x80000000 size=0x4000000 ticks=<T>
BE_MVP:06 PAYLOAD_PLACED domain=0 kernel=0x80200000 kernel_bytes=<K> image_size=<S> dtb=0x83e00000 dtb_bytes=0x1000 ticks=<T>
BE_MVP:06 PAYLOAD_PLACED domain=1 kernel=0x80200000 kernel_bytes=<K> image_size=<S> dtb=0x83e00000 dtb_bytes=0x1000 ticks=<T>
BE_MVP:07 BLOCKS_PUBLISHED region=0x104044000 bytes=0x20000 generation=1 budget_ticks=0x100000000
BE_MVP:08 HART_STARTED hart=1 domain=0 result=0 status=0 ticks=<T>
BE_MVP:08 HART_STARTED hart=2 domain=1 result=0 status=0 ticks=<T>
BE_MVP:09 HART_READY hart=1 domain=0 hgatp=0x8000100000102034 hstatus_controls=0x180 hedeleg=<h> hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:09 HART_READY hart=2 domain=1 hgatp=0x800020000010203c hstatus_controls=0x180 hedeleg=<h> hideleg=0x40 hcounteren=0x2 sie=0x2 henvcfg=0x8000000000000000 vstimecmp=0xffffffffffffffff
BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 pc=0x80200000 a0=0x0 a1=0x83e00000 ticks=<T>
BE_MVP:10 DOMAIN_ENTERED hart=2 domain=1 pc=0x80200000 a0=0x0 a1=0x83e00000 ticks=<T>
BE_MVP:13 RUN_COMPLETE domains=2 records=<N> wakes=<N> idle_ticks=<T> overlap_ticks=<T> ticks=<T>
BE_MVP:14 SHUTDOWN type=0 reason=0
```

Between `BE_MVP:10` and `:13` come both domains' lines, interleaved in
hart 0's drain order, and four more control-hart lines: `BE_MVP:11
IPI_PROBE hart=<h> domain=<d> sent=<T> received=<T> answered=<T> spv=1`
once per domain, after its first line, and after each domain's last line
`BE_MVP:12 DOMAIN_SHUTDOWN hart=<h> domain=<d> exits=<N> sbi=<N> ipi=1
base=<N> time=0 dbcn_write=<N> dbcn_read=<N> dbcn_byte=0 srst=1 refused=0
lines=<N> ring_peak=<B> entered=<T> ticks=<T>`. The `:09` and `:10` pairs
and the two `:11` and `:12` lines may come in either hart order. Each
domain's lines carry its prefix (`BE_MVP_G0: ` or `BE_MVP_G1: `) and must
hold, in order, among other lines, B7's required set with the M0 names:

```text
[<s>] Linux version 7.2.0 <banner>
[<s>] SBI implementation ID=0x4245 Version=0x3
[<s>] Kernel command line: earlycon=sbi console=hvc0 panic=-1 oops=panic panic_on_warn=1 -- be.guest=<g>
[<s>] riscv-timer: Timer interrupt in S-mode is available via sstc extension
[<s>] Memory: <m>K/65536K available <rest>
[<s>] Run /init as init process
MVPINIT 01 START guest=<g> pid=1
MVPINIT 02 UNAME release=7.2.0 machine=riscv64
MVPINIT 03 STEP n=<i>/8 rounds=<r> t_ms=<t>
MVPINIT 04 SLEEP requested_ms=1000 elapsed_ms=<e> ok=1
MVPINIT 05 RESULT pass
MVPINIT 06 POWER_OFF
[<s>] reboot: Power down
```

- **Concurrency (Q5):** `overlap_ticks`, the overlap of the two domains'
  `entered`-to-shutdown intervals from their records' `time` fields, is
  at least half the shorter interval; and at least K = 8 alternations
  appear between the domains' lines, control-hart lines ignored.
  Inference: both domains boot and step at once, so both floors sit well
  below the expected values; neither depends on wall time.
- **Consistency:** each `domain=<d>` and `hart=<h>` matches the
  scenario's binding and the line's prefix; `:08` to `:12` appear once
  per domain; both domains show `srst=1` and `ipi=1`; per domain `exits`
  = `sbi` + `ipi`, with `sbi` the sum of the call classes; `lines`
  equals the number of that domain's lines hart 0 printed; `records`
  equals the sum of records drained; `ring_peak` is at most `0x4000`; and
  `ticks` is at most the budget.
- **Console:** B7's rules: lines whole, CR dropped, bytes outside
  `0x20`-`0x7e` as `?`, a full 256-byte buffer written as its own line,
  a partial line flushed at shutdown and before a `FAIL`.
- **Rejected:** B6's rejected substrings in any domain line; an untagged
  line between the first and last control-hart lines; a tag inside a
  domain line; any `BE_MVP:FAIL`; a missing required line; anything after
  `BE_MVP:14`.
- **Failures:** `BE_MVP:FAIL <class>`, a `DETAIL` line with `domain=<d>
  hart=<h>` where a domain hart is involved, then the SRST request. The
  terminal regex is `BE_MVP:14 SHUTDOWN|BE_MVP:FAIL|BE_K3_B3: FAIL`.
- **Probe images** print `BE_MVP:PROBE <name> <fields>` lines in a fixed
  order and end with `BE_MVP:14`; the checker requires the format and
  records the values, applying the expectations in the probe table only
  as the stop conditions they name.

## Tests and evidence

| Layer | Check | Pass criterion |
| --- | --- | --- |
| Host | `tests/ring-test.c`, `tests/hart-test.c` (new): push and pop at every fill level, wrap, full-ring refusal, header validation, block validation (hart id, generation, offsets), the control loop's state machine (ready, entered, shutdown, fail, done, timeout), the overlap computation, saturating time; invalid input fails closed | Identical GCC and Clang output with pinned counts |
| Host | `tests/sbi-test.c` (B7's, changed): no `wfi` or slice class; the IPI class (PING, an empty inbound ring, an unknown record); line records; per-hart counters; version 3 | Identical GCC and Clang output with pinned counts |
| Host | `tests/gstage-test.c`, `tests/payload-test.c` (B7's) | As B7 |
| Guest inputs | `build-guest.sh` pins; `kernel-repro`; both reference boots | Pins match; an identical repeat build; `RESULT pass` with each guest's id |
| Port | `tools/port.py --check` | Byte-identical; B7's rules plus the hart region |
| Lock | `mvp tool-lock check` on the host and in the evaluator | Every role matches; images identical across the two |
| Image | `tests/check-image.py` and its mutation test, with the MVP and probe profiles | The rules below, for GCC and Clang |
| Markers | `tests/check-capture.py --self-test` and the mutation set | Every mutation of a passing capture rejected: a missing line in either stream, a domain or hart that differs from the binding, a mixed line, an overlap below the floor, fewer than K alternations, a missing `ipi=1`, wrong sums, one shutdown only, a line after `:14` |
| QEMU | `tests/run-qemu.sh` with `-smp 8`; `kexec-rehearsal` | The scenario, the negative variants, and the probe images below; GCC and Clang through kexec |
| Evaluator | `mvp evaluate` | The lock, host tests, images, and QEMU runs pass inside; images byte-identical with the host's |
| Board tools | `tests/run-tool-dry-run.sh`; `tests/test-kexec-load.py` | Dry runs pass; the layout rule, with the hart region, passes on the recorded `/proc/iomem` |
| Board | `k3-preflight`, `k3-load-check`, `k3-probe`, `k3-campaign` | Preflight passes; the probe runs report their facts; three GCC and one Clang scenario runs pass; the `payload` run fails as declared |

**Image checker** (B7's rules, adapted; the MVP profile):

- **Instructions:** B7's site table less the scheduler's additions: its
  three `sret`, one `ecall`, one `fence.i` (now in the hart entry), and
  the accepted halts' three `wfi`, plus hart 0's wait and the domain park;
  no `hfence.vvma`, `mret`, H load or store, or F, D, or V instruction;
  `hgatp` writes and `hfence.gvma` only inside the accepted R3 functions,
  the install function with exactly two call sites.
- **CSR writers:** the per-domain CSRs only by the arm helper
  (`vstimecmp` also by TIME); `stimecmp` only by hart 0's budget helper
  and B1's quiesce; `sie` written only by the arm helper and the budget
  helper; `sip` cleared only by the IPI handler; VTW never set; no access
  to `hstateen0`, `hvictl`, `hvien`, or `hviprio*`.
- **Shim:** the board images' shim holds B3's instructions plus the start
  rule's `ecall`; HSM `hart_stop` appears only in the QEMU-only
  `shim-rule` variant.
- **Layout and payload:** B3's header; the kernel and two DTBs at their
  offsets, the DTBs equal but for `bootargs`; both `hgatp` values; the
  monitor, pool, hart region, staging, kexec FDT slot, and windows
  pairwise disjoint; the hart region's blocks at their offsets.
- **Probe profile:** the probe module's install call site; the raw
  `hgatp` write in the two VMID images only.
- **Mutation test:** in-memory defects, each rejected for its own reason:
  VTW in an arm immediate; a `stimecmp` write outside the budget helper;
  a third install call in the MVP image; a raw `hgatp` write in the MVP
  image; equal VMIDs; a block offset moved; a ring size that is not a
  power of two; equal `bootargs`.

**QEMU scenarios:** B6's machines and CPUs with `-smp 8 -m 8G`, QEMU
10.2.2, OpenSBI v1.6 `fw_dynamic`, 300 s per run; outcomes judged in
guest terms.

| Scenario | Toolchains | Expected |
| --- | --- | --- |
| `k3-like`, `rva23`, `plic` | GCC, Clang | Pass |
| The negative variants | As listed | As listed |
| `probe-platform`, `probe-vmid-distinct`, `probe-vmid-shared` | GCC, Clang | The probe lines in order; QEMU's values recorded as emulation facts |
| `shim-rule` (a QEMU-only variant shim: hart 0 starts hart 1 at the shim and stops itself through HSM, so hart 1 arrives as the boot hart) | GCC | `BE_MVP_SHIM: boot_hart=0x1 starting hart 0`, then `SHIM hart=0x0` and a passing run; the start rule is shown without depending on QEMU's lottery |

Inference: `mvp check` takes 20-30 minutes, as every QEMU run boots two
Linux guests on an eight-hart machine; the evaluator run takes about as
long again.

## Accepted decisions M0 departs from

Each applies to the MVP line only and changes no accepted byte. B6's and
B7's departures from their predecessors carry over for each domain.

| # | Accepted B7 decision | M0 departure | Accounted for by |
| --- | --- | --- | --- |
| 1 | One hart; the shim parks the rest | Three harts under static ownership; the shim starts hart 0 if another hart boots | The accepted MVP plan; Q2; the `shim-rule` variant |
| 2 | The HS supervisor timer is the only HS interrupt, at V=1 | The supervisor software interrupt at V=1 and in hart 0's wait; the timer only in hart 0's wait | SSIE arm and check; the IPI probe; stop 6 |
| 3 | VTW set; `wfi` traps and parks | VTW clear; native `wfi`, as B6 | The arm immediate; the mutation test |
| 4 | Per-guest CSRs loaded on every switch | Written once per hart | Arm readback; the writer table |
| 5 | `hgatp` written on every switch | Once per hart | Install readback; the single-writer rule |
| 6 | One exit record in the management saved page | A saved page per domain hart in a new region | The vector's and tail's `sscratch` check; the layout `ASSERT`s |
| 7 | No HS-to-M SBI call beyond the accepted four | HSM start and status, IPI send, through the accepted helper | MVP plan D15; one `ecall` site; `mvp-sbi.h` |
| 8 | Markers fixed in the checker | Scenarios as data | The generator; the checker reads the expectations |
| 9 | Unpinned workstation tools | The tool lock and the evaluator | MVP plan M0 deliverable 2 |

## Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| HSM `hart_start` after kexec does not behave as on a cold boot | No domain hart; `FAIL hart-start` | The status probe first; QEMU rehearsal, where the HSM path works (planning research 3); stop 6 |
| A started hart does not reach the entry or fails its block check | `FAIL hart-ready` with no detail from that hart | The 2^26-tick wait; the status probe records `STARTED`; diagnosed read-only |
| IPIs are not delivered to HS at V=1 on K3 | No PONG; `FAIL ipi` or a missing `:11` | The probe image first; QEMU delivers IPIs between harts in HS (planning research 3), V=1 untested anywhere; stop 6 |
| Cross-hart ordering holds in QEMU's TCG by luck | A stale ring record or payload on the board | Fences on both sides; the ordering probe; the checker's consistency sums |
| Clang monitor text | Over `0x8000` | `-Os`; the probe module out of the MVP image; measured at M0-3; stop 3 and the remedy to propose |
| The outbound ring fills | `FAIL ring` | 32 KiB against 10 KB measured; `ring_peak` recorded; stop 3 above half |
| Console bandwidth: about 20 KB of output through one hart at 115200 baud | A run of about 2 s; drain lags production | The rings absorb the lag; the budget is 179 s |
| QEMU's boot-hart lottery | A hang if hart 0 never runs | The shim's start rule; the `shim-rule` variant |
| The evaluator's package closure leaves the mirrors | The image cannot be rebuilt | The lock records the closure; `refresh` under direction; a risk, not a stop |
| The checker grows faster than the monitor | S1 H43 | The size ratio in the packet; stop 12 |
| Timing-dependent checks | A flaky checker | Ticks-based overlap and structural floors; no wall-time check |

## Claim boundary and non-goals

- **Evidence:** QEMU results are emulation; board results are diagnostic
  bring-up evidence for one board, firmware, and Fedora kernel, never
  hardware validation, qualification, or formal verification. The probe
  facts are platform facts for one board. QEMU, Model, Helium, R-series,
  and B0-B7 claims do not transfer.
- **Isolation:** by construction only, as B7: two disjoint windows, two
  re-walked roots on two harts under distinct VMIDs, DBCN copies from the
  calling domain's window only, no shared page or channel. M0 runs no
  denial or fault-injection test between the domains; the probe stub's
  faults are the probe's, not a scenario's. The substrate has no proof.
- **Not selected:** a scheduler (none), a VMID policy, a guest ABI, an
  SBI profile, a console protocol, an IPI mechanism for Beryllium beyond
  M0, a development kernel or BSP, or OpenSBI as the long-term firmware
  boundary.
- **CHERI alignment** (MVP plan D12): the hart ID, the domain index, the
  VMID, and the record types are identifiers, as [Hart
  identifiers](#hart-identifiers) states for hart IDs; authority is the
  sealed block and the root a hart installs once, and nothing a domain
  hart reads after the barrier grants more. The only shared monitor
  memory is the rings, each with one writer and one reader, and the only
  transition is the fast path. No CHERI mechanism is used.

## Work packages

The packages run in order; one result review packet follows M0-6.

| Package | Work | Exit criteria |
| --- | --- | --- |
| M0-1 The line and the lock | `mvp/` seeded by `port.py` with the hart-region rule; the counted copies and their tables; `make-control.py`; the wrapper; the tool lock and `check`; the evaluator Containerfile and closure; the guest inputs and pins with the MVP names; `kernel-repro`; both reference boots | `mvp tool-lock check` passes on the host and in the evaluator; the port re-derives; pins match; an identical repeat build |
| M0-2 Pure-C mechanism | `mvp-ring`, `mvp-hart`, the changed SBI core, and their host tests | Identical GCC and Clang output with pinned counts |
| M0-3 Monitor and images | The hart entry, vector, tail, arm, and budget helpers; the runtime; the shim rule; the scenario generator; the MVP image, the negative variants, and the probe images with the stub; the image checker, both profiles, and its mutation test; measured budgets | Image checks pass for both toolchains; every budget holds |
| M0-4 Harness, QEMU, evaluator | The capture checker and its mutations; eight-hart QEMU runs, including `shim-rule`; the kexec rehearsal; the evidence bundle; `mvp check`; `mvp evaluate` | `mvp check`, `kexec-rehearsal`, and `evaluate` pass; images identical across host and evaluator |
| M0-5 Board | `k3-preflight`; `k3-load-check` for GCC and Clang; `k3-probe`: the three probe images; `k3-campaign`: three GCC and one Clang scenario runs, then the `payload` run; a human reset after each | Every capture passes its checker, or a stop applies |
| M0-6 Record and packet | The platform record; retention with B0's tool; README results and the size ratio; `kernel-repro` again; `planning/mvp-m0-result-review-summary.md`; status documents | One exact result commit and packet for your decision |

## Stop conditions

Each returns M0 to the responsible human, with the evidence so far, before
any workaround:

1. A needed change to an accepted R0-R7 or B0-B7 byte, an accepted
   document's text, or a retained R8 input; root integration.
2. A needed HS-to-M SBI call beyond HSM `hart_start` and
   `hart_get_status` and IPI `send_ipi`; `hvip` injection; an H load or
   store; a third domain hart or a hart started or stopped after the
   barrier; a scheduler or time slice; a lock or atomic read-modify-write
   in the fast path; a device, MMIO, or DMA path.
3. A budget overrun, including a ring high-water mark above half.
4. A needed CSR access outside the M0 inventory.
5. An init, `Image`, DTB, or OpenSBI that does not rebuild byte for byte
   or match its pin; an image that differs between the host and the
   evaluator; a missing tool; a kernel config change beyond B6's
   fragment; a libc; any new external input.
6. A board outcome QEMU did not show, diagnosed read-only first: an
   unexpected exit class, a missing line, a hang, a watchdog reset, or
   any of these K3 facts: a hart not `STOPPED` before start; a failed or
   timed-out `hart_start`; a hart that does not reach READY; an IPI not
   delivered at V=1 or in HS; a stale read with fences in the ordering
   probe; a stale translation under distinct VMIDs; `htval` not equal to
   GPA >> 2; a per-hart CSR readback mismatch; a domain hart's Sstc timer
   that does not fire.
7. A preflight `/proc/iomem` child or FDT reservation in the staging
   region, the hart region, or either window.
8. The preflight lacks `h` or `sstc` on harts 0 to 2, or HSM in Fedora's
   log; or a run prints `BE_MVP:FAIL sstc` or `FAIL firmware`.
9. Any step that would write firmware, the U-Boot environment, flash,
   boot configuration, or board storage; use TFTP or a staged-NVMe
   `load`; or need automation to type at U-Boot.
10. A guest that needs SBI outside the subset.
11. A tool-lock role the development host cannot satisfy with open tools,
    or an evaluator base or closure that cannot be pinned (MVP plan stop
    5).
12. Checking machinery that grows beyond what this plan justifies (MVP
    plan stop 6).

## Board safety and procedure

- **RAM only:** kexec stages the image and loader in Fedora's tmpfs
  `/tmp`, and `kexec_load` places the segments in RAM. The shim writes
  only the monitor image and its report line. The monitor writes only its
  image, its pool, the hart region, and the two windows. The domain harts
  run only RAM-resident code and never touch firmware.
- **Human control:** the human powers the board on and resets it after
  every run (OpenSBI 1.6 halts it after SRST); Fedora then autoboots.
  Automation reads the serial log output-only and uses SSH only for the
  read-only preflight and B0's staging, load, and `systemctl kexec`
  steps; it never types at U-Boot.
- **Procedure,** after `mvp check`, `mvp evaluate`, and the kexec
  rehearsal pass: the preflight, both load checks, the three probe runs,
  three GCC and one Clang scenario runs, then the `payload` run, with a
  human reset after each (Q6):

```sh
cd mvp
./mvp k3-preflight
./mvp k3-load-check TOOLCHAIN=gcc
./mvp k3-load-check TOOLCHAIN=clang
K3_SERIAL_LOG=<abs picocom log> K3_RUN_ROOT=$PWD/../build/mvp/k3-campaigns/<date>-com260 ./mvp k3-probe TOOLCHAIN=gcc
K3_SERIAL_LOG=<abs picocom log> K3_RUN_ROOT=$PWD/../build/mvp/k3-campaigns/<date>-com260 ./mvp k3-campaign TOOLCHAIN=gcc RUNS=3
K3_SERIAL_LOG=<abs picocom log> K3_RUN_ROOT=$PWD/../build/mvp/k3-campaigns/<date>-com260 ./mvp k3-campaign TOOLCHAIN=clang RUNS=1
K3_SERIAL_LOG=<abs picocom log> K3_RUN_ROOT=$PWD/../build/mvp/k3-campaigns/<date>-com260 ./mvp k3-campaign TOOLCHAIN=gcc VARIANT=payload RUNS=1
```

## How M0 feeds M1

M1 adds the declared channel, the policy and manifest checker, fault
injection with denial logging and resume, and the authority report. M0
gives it the line to change in place; the harness and the scenario format
to add Instance 2 to; the platform record's `htval` and `htinst` values,
from which M1 fixes its injected encodings; the VMID facts that replace
the stale-authority switch test; the per-hart fast path to which the
injection decision is added as a pure function; and the rings through
which the denial log reaches hart 0. Nothing in M0 selects M1's design
beyond what the accepted MVP plan states.

## Status record

```text
mvp_m0_plan_status=accepted
mvp_m0_plan_target=4d129808979cb54b7e0a7cc0b3e79d39533e0b9c
mvp_m0_plan_acceptance_instruction=accept-4d129808-proceed-with-implementation-using-opus-5.5-model
mvp_m0_plan_acceptance_date=2026-10-23
mvp_m0_plan_open_questions=Q1-Q13-defaults
mvp_m0_implementation_branch=beryllium/mvp-m0
mvp_m0_implementation_model=claude-opus-5.5
mvp_m0_plan_revision=2
mvp_m0_superseded_candidates=6e4b9d4a1e2da249d68aeb4e1aea5a27cf3755f8,d95b28e953bccbdd489b1e6eec69d48fa028fd29
mvp_m0_governing_plan=93967fbac926b4fdfdfe636df4d07e8926b625b7
mvp_m0_plan_base=1fb464199dc5ace11c77e4697ff5e13a35f21434
mvp_m0_branch=beryllium/mvp-m0-plan
mvp_m0_tree=mvp
mvp_m0_seed=bringup/k3-b7-counted-port
mvp_m0_hart_layout=hart0-control,hart1-domain0,hart2-domain1,harts3-7-never-started
mvp_m0_hart_ids=configuration-not-authority;control-fixed-by-accepted-boot-check;domain-harts-scenario-data
mvp_m0_qemu_boot_hart_research=10-runs-smp8:hart0-in-2
mvp_m0_qemu_hsm_ipi_research=8-runs-smp8:stopped-start-ipi-roundtrip-all-pass;v1-delivery-untested
mvp_m0_hart_region=0x104044000+0x20000
mvp_m0_cross_hart=sbi-hsm-start-status,sbi-ipi-send,single-writer-rings
mvp_m0_scheduler=none
mvp_m0_guest_sbi_version=3-unchanged
mvp_m0_scenario=two-guests
mvp_m0_probe_images=probe-platform,probe-vmid-distinct,probe-vmid-shared
mvp_m0_board_runs=8
mvp_m0_tool_lock=be-mvp-tool-lock-v1
mvp_m0_evaluator=digest-pinned-fedora-recorded-closure
mvp_m0_work_packages=M0-1..M0-6
mvp_m0_implementation_authorization=M0-1..M0-6-under-this-plan
mvp_m0_implementation_status=M0-1..M0-6-complete
mvp_m0_result=accepted
mvp_m0_result_target=b266972563a39b0687ba2ac8c5b4cb943f3c766a
mvp_m0_result_parent=13992d6d902131a6c19978b620724fad0524256f
mvp_m0_result_acceptance_instruction=accept-b26697
mvp_m0_result_acceptance_date=2026-10-26
mvp_m0_result_record=mvp-m0-result-review-summary.md
mvp_m1_authorization=none
```

## Plan revision M0-A: MVP region, boot-hart rule, and ring-full variant

**Status: directed, not yet accepted at an exact commit.** On 2026-10-23,
after M0-3 reported stop condition 3 and open items 9 and 10
(`mvp/README.md`), the responsible human asked for recommendations, then
asked whether the first recommendation created architectural technical
debt and whether to address it now, and, on the revised answer, directed:
`agreed, proceed with your recommendations, planning and implementation`.
As with B6's `fix-warl` direction, that instruction is recorded here and
implementation proceeds under it; the exact commit carrying this revision
is presented for acceptance with M0's result packet. This revision changes
no accepted R0-R7 or B0-B7 byte and no accepted document. It changes the
plan in five bounded places and nothing else; every other section of the
accepted plan stands.

### The stop and the two gaps

1. **Stop condition 3.** Clang's scenario monitor text ends at
   `0x1020087e0`, `0x7e0` bytes past the accepted `0x102008000` limit;
   GCC's ends at `0x102007fe0`, `0x20` spare. Measured on the M0-3 objects
   (`riscv64-linux-gnu-size -A`, section sums before garbage collection),
   the accepted port's text is `0x44b2` (GCC) and `0x471e` (Clang) and
   the MVP layer's own C and assembly text is `0x4028` (GCC) and `0x4664`
   (Clang): the layer is 16-18 KiB on its own, so no shrinking of M0
   within its plan reaches the limit, and M1 would have stopped at the
   same place for GCC.
2. **Open item 9.** With eight harts, QEMU's boot hart is 0 in a minority
   of runs. A boot hart other than 0 runs the shim's start rule (Q2),
   starts hart 0, and parks in `wfi`; a parked hart is HSM `STARTED`, so
   hart 0's `BE_MVP:02`, which requires every hart but itself `STOPPED`,
   refuses it as `FAIL firmware`. The accepted plan did not reconcile
   the two.
3. **Open item 10.** With 1 KiB outbound rings, hart 0 drains each LINE
   record as soon as its IPI arrives, so the `ring-full` variant never
   fills a ring (high-water marks `0xd8`-`0x2d8` bytes in every run) and
   the domain hart's fallback path, a `FAIL` with no acknowledgement
   from hart 0, stays unexercised in QEMU.

### M0-A.1 The MVP region

The accepted plan's "Budgets" named the remedy to propose for stop 3 as
"a counted port rule that grows the monitor code region with every
accepted invariant substituted". Growing `.monitor.text` past
`0x102008000` would collide with the accepted R3 boot validation
(`virt/be/r3.c`, `BE_R3_MONITOR_CODE_END`, and its code and data extent
checks) and with the frozen R0 code and data split, so the port would
have to substitute constants in accepted C and headers as well as the
linker script, and the frozen profile's bookkeeping would follow. The
revision takes a smaller and more honest remedy instead:

- **A new MVP-owned region.** One more counted rule in `tools/port.py`
  adds a PT_LOAD output section `.mvp.text` (with `.mvp.rodata`,
  `.mvp.data`, and `.mvp.bss` behind it) at HPA `0x102064000`, directly
  after the hart region, of `0x40000` bytes (256 KiB), with `ASSERT`s on
  its start, end, alignment, and its place after the hart region. The
  region holds the sections of the MVP layer's C objects
  (`mvp-runtime.o`, `mvp-hartmain.o`, `mvp-sbi.o`, `mvp-hart.o`,
  `mvp-ring.o`, `mvp-gstage.o`, `mvp-payload.o`, and in the probe images
  `mvp-probe.o`), routed by explicit input-section patterns and excluded
  from `.monitor.text` and the accepted data sections. The assembly
  objects `mvp-trap.o` and `mvp-hartentry.o` stay in `.monitor.text`,
  because the accepted R3 validation requires the trap vector inside the
  accepted code extent, and the resume tail and the hart entry belong
  with it. The accepted sections keep their addresses, sizes, and
  `ASSERT`s; `monitor_code_end` in the R3 layout record keeps describing
  the accepted code extent, which is now accepted code plus the MVP
  assembly, with about 14 KiB spare.
- **The loaded image grows.** The flat image becomes the bytes from
  `0x102000000` to the region's end, `0xa4000` bytes; the NOLOAD pool and
  hart region inside it are zeros in the file and are rebuilt at boot as
  before. Its first `0x34000` bytes keep the accepted layout. The shim's
  descriptor and its `bytes=` line, `mvp-boot.lds`'s offsets and
  `ASSERT`s (the kernel moves to offset `0xa5000`, the DTBs after it; the
  boot image stays below 4 MiB), the kexec loader's layout rule, the
  layout header, the image checker's extents and disjointness set
  (monitor, pool, hart region, MVP region, staging, kexec FDT slot, both
  windows), and the QEMU and kexec tools follow, each as a counted change
  in `mvp/README.md`. The region ends at `0x1020a4000`, 1.4 MiB below
  Fedora's kernel at `0x102200000` and inside the range the B7 preflight
  recorded free.
- **Budgets.** "Monitor text below `0x102008000`" stays the accepted
  `ASSERT` and now bounds the accepted code plus the MVP assembly. New
  rows: the MVP region's text, rodata, data, and BSS together at most
  `0x40000`, measured and reported per toolchain; the flat image exactly
  `0xa4000`. Stop condition 3 applies to the new rows as to the old.
- **Markers.** `BE_MVP:01 SCENARIO` gains `mvp_region=0x102064000
  mvp_bytes=0x40000 image_bytes=0xa4000`.
- **Why this and not the plan's sketch.** No accepted byte, no R0
  resource or R3 constant substitution, no change to the flat image's
  accepted first `0x34000` bytes; the same mechanism as B7's pool and
  M0's hart region (an MVP-owned extent added by a counted port rule
  outside every accepted extent); and headroom for M1 and M2 so that the
  layout is decided once.

### M0-A.2 The boot-hart rule in `BE_MVP:02`

`BE_MVP:02` requires both domain harts `STOPPED` and every other hart but
hart 0 `STOPPED` with one exception: at most one hart may be `STARTED`,
and `:02` reports it as `started=<h>` (`started=none` otherwise). Any
second `STARTED` hart, any error status, or a domain hart not `STOPPED`
stays `FAIL firmware`. The capture checker requires `started=<h>` to
equal the `boot_hart=0x<h>` of the shim's start-rule line when that line
is present and `started=none` when it is absent. The board shim gains no
firmware call, nothing is stopped after the barrier, and the board, where
every recorded run entered on hart 0, is unaffected. The accepted plan's
"harts 3 to 7 are never started" reads "never started by the monitor";
the platform record states which hart booted each run. The `shim-rule`
variant keeps its QEMU-only `hart_stop` and stays the deterministic
exercise of the rule.

### M0-A.3 The `ring-full` variant

`ring-full` becomes: 1 KiB outbound rings, and hart 0 waits `0x2000000`
ticks after both domains' `ENTERED` records before its first LINE drain
(a compile-time switch in hart 0's control loop only). The domains' boot
output fills a ring, the writing hart fails closed, posts `FAIL ring`,
receives no acknowledgement while hart 0 waits, and takes the fallback
path: it prints `BE_MVP:FAIL ring` and its `DETAIL` line itself through
DBCN and requests SRST (Q10). The expectation is that failure, with the
`DETAIL` line's `hart=` naming a domain hart and no `BE_MVP:ACK` from
hart 0 before it. This exercises the "control hart wedged" risk the
accepted plan lists.

### M0-A.4 Erratum

The accepted plan's `BE_MVP:07` example (`region=0x104044000`) and status
record (`mvp_m0_hart_region=0x104044000+0x20000`) are transcription
errors for the hart region the plan places everywhere else at
`0x1_0204_4000`, that is `0x102044000`; the implementation uses
`0x102044000`, and `BE_MVP:07` prints `region=0x102044000`. The accepted
text is not edited; this revision records the correction.

### M0-A.5 The claim ledger and the roadmap

The result packet's claim ledger gains this non-claim: the frozen R0
inventory and the accepted R1-R3 validation describe the accepted core
only; the pool, the hart region, the MVP region, and the guest windows are
MVP-owned extents validated by the MVP line's own `ASSERT`s, image
checker, and boot-time checks, not by R1-R3. The MVP grows around a
frozen synthetic core whose fixture roots and pages it builds and never
uses; that is recorded structural debt, deferred by the accepted MVP plan
(D3) and S1 H22 to a later plan. The roadmap gains the later item "MVP
core profile": replace the fixed-profile prelude with an inventory of the
MVP's real layout and drop the unused fixture roots and pages, as its own
bounded plan after MVP 1.0 or with the clean-repository build root.

### M0-A.2 and M0-A.3 as implemented

The implementation (`mvp/` commits `65454598`, `106062f6`, `ebae089d`,
and `b0fd5780`) read the two rules as follows; this note records the
reading so that M0-4's capture checker and the result packet agree with
it.

- **A boot on a domain hart is refused.** M0-A.2 keeps "a domain hart not
  `STOPPED` is `FAIL firmware`", so when QEMU's firmware boots on hart 1
  or 2 the shim's start rule leaves that hart parked and `STARTED`, and
  hart 0's `BE_MVP:02` refuses the run. That is the plan's precondition
  failing, not a scenario result: `run-qemu.sh` records the run as
  `REFUSED` and counts it separately, and M0-4 repeats a refused run,
  within a bounded number of attempts, until each scenario, variant, and
  probe has a completed run per toolchain; the refusal counts go in the
  evidence and the platform record. On the board every recorded run has
  booted on hart 0; a board run refused this way is stop 6, not a repeat.
  `started=<h>` prints in decimal like every other hart field; the shim's
  `boot_hart=0x<h>` is hexadecimal, and the capture checker converts.
  In the `shim-rule` variant the shim line is present and `:02` prints
  `started=none`, because that variant's shim stops the boot hart.
- **`ring-full` falls back at once.** A full ring fails the writing hart's
  ring view, so it cannot post the `FAIL ring` record and does not wait
  for an acknowledgement; it prints `BE_MVP:FAIL ring` and its `DETAIL`
  line through DBCN immediately. The expectation is therefore that hart 0
  prints nothing between `BE_MVP:10` and the first `FAIL`, that the
  `DETAIL` names a domain hart, and that `:11` to `:14` never appear.
- The region's segments are three (`R-X`, `R`, `RW`), so its constants
  are not executable; the probe images count only domain 0's hart as a
  domain hart; the negative variants are built and run for Clang as well
  as GCC; and the two-`STARTED`-harts case is covered on the host only.

### What this revision does not change

The hart layout, the hart region, the rings, the IPIs, the scheduler-free
design, the guest SBI surface, the firmware surface (HSM `hart_start` and
`hart_get_status`, IPI `send_ipi`), the probe images, the scenario, the
harness rules, the tool lock, the evaluator, the board procedure, the
work packages, and stop conditions 1 to 12. M0-3 resumes under it, then
M0-4 to M0-6.

### Revision status record

```text
mvp_m0_plan_revision_m0a=directed-2026-10-23;accepted-with-result-b2669725-2026-10-26
mvp_m0a_direction_instruction=agreed-proceed-with-your-recommendations-planning-and-implementation
mvp_m0a_mvp_region=0x102064000+0x40000
mvp_m0a_flat_image_bytes=0xa4000
mvp_m0a_monitor_text_assert=0x102008000-unchanged
mvp_m0a_boot_hart_rule=at-most-one-started-non-domain-hart-equal-to-shim-boot-hart
mvp_m0a_ring_full=1k-rings-plus-hart0-drain-delay-0x2000000-ticks
mvp_m0a_hart_region_erratum=0x104044000-reads-0x102044000
mvp_m0a_debt_item=mvp-core-profile-later-plan
mvp_m0a_implementation=65454598,106062f6,ebae089d,b0fd5780;mvp-check-pass-gcc-clang
mvp_m0a_refused_runs=domain-hart-boot-refused;qemu-repeat-bounded;board-stop-6
```

## Plan revision M0-B: the evaluator's closure source

**Status: directed, not yet accepted at an exact commit.** M0-4 found
that the evaluator image does not build from the pinned base and the
recorded closure (`mvp/README.md` open item 7; stop condition 11):
Fedora's `updates` repository had replaced the closure's
`ca-certificates-2026.2.92_v9.0.319-1.fc44.noarch` with `-2.fc44` while
koji still serves the exact build, and the closure's
`systemd-sysusers-259.10-1.fc44.x86_64` conflicts with the base image's
installed `systemd-standalone-sysusers-259.7-1.fc44.x86_64`, which `dnf
install` does not erase. Nothing was loosened. On 2026-10-24 the
responsible human was offered three remedies and answered `accept A`:
"keep the closure NEVRAs, add a SHA-256 per RPM, fetch the exact closure
once from the repos/koji into a verified local cache, build with repos
disabled, explicit swap of the base's standalone sysusers, and record
podman/ssh/scp as host-only lock roles" (B was a lock refresh from the
host now; C was to defer). As with M0-A, the direction is recorded here,
implementation proceeds under it, and the exact commit carrying this
revision is presented for acceptance with M0's result packet. It changes
no accepted byte and no accepted document; it changes the plan's "Tool
lock and the clean evaluator" section as follows and nothing else.

### M0-B.1 Per-RPM digests in the closure

The closure keeps its 257 NEVRAs unchanged. For each, the closure records
the SHA-256 of the RPM file as Fedora built and signed it. The digests
are derived once, under this direction, from RPMs fetched as M0-B.2
describes and verified two ways before recording: the RPM's signature
checks against the Fedora 44 key the host's `fedora-gpg-keys` installs
(`rpmkeys --checksig`), and, for every closure package the host has
installed, the file's header digest equals the installed package's
(`rpm -q --qf '%{SHA256HEADER}'`). The lock's `MVP_CLOSURE_SHA256`
re-binds the closure's new bytes. The lock's diff under this revision
contains only the digest additions, that re-binding, the host-only roles
of M0-B.4, and a schema line if the form changes; any other changed line
is host drift, which stops the work for a report rather than being
absorbed.

### M0-B.2 A verified local cache, fetched once

A new tool under `tools/evaluator/` fetches each closure RPM by exact
NEVRA into a local cache directory of exact RPMs verified by SHA-256
(the `MVP_RPM_CACHE` pattern `tools/build-guest.sh` already uses for
B3's pinned RPMs), trying Fedora's repositories first and koji
(`kojipkgs.fedoraproject.org/packages/<name>/<version>/<release>/<arch>/`)
second, recording which source served each file, skipping a file that is
present and verifies, and failing closed on any digest mismatch or
missing package. This fetch and the base image's pull by digest are the
evaluator's only network use; the evaluation itself still runs with no
network.

### M0-B.3 The image builds from the cache with repositories disabled

The Containerfile installs the closure from the verified cache with every
repository disabled and weak dependencies off, then checks that every
closure NEVRA is installed exactly and records `rpm -qa` as before. The
base image's `systemd-standalone-sysusers` is swapped explicitly, by
name, for the closure's `systemd-sysusers-259.10-1.fc44.x86_64`; no
general `--allowerasing`, `--skip-unavailable`, `--nobest`, or
unnamed erasure is used. If the exact closure cannot be installed on the
pinned base by explicit, named, local operations, that is stop condition
11 again and a report, not a loosening. The reproducibility wording
becomes "digest-pinned base plus recorded closure with per-RPM digests"
(S1 H32): the remaining assumption is that some source retains the exact
bytes, which the digests verify from any source, rather than that the
mirrors keep the NEVRAs.

### M0-B.4 Host-only lock roles

`podman`, `ssh`, and `scp` enter the lock as roles the host must satisfy
(command, resolved executable, version, SHA-256, owning package) and the
evaluator does not: `tool-lock check` verifies them on the host and skips
them inside the image, where it recognizes the evaluator by its recorded
package list. Their packages do not enter the closure, so the image gains
no container, SSH, or network tooling. Nothing else in Q8 changes.

### M0-B as implemented

The implementation (`mvp/` commits `b364fe92`, `83916b5a`, `67731e4c`,
and `19c3d455`) read the revision as follows; the result packet carries
each point for the responsible human's review.

- **Four named base packages are removed with the swap.** With every
  repository disabled, swapping `systemd-standalone-sysusers` alone does
  not resolve: four packages of the pinned base require the exact
  versions of base packages the closure upgrades (`glibc-minimal-langpack
  -2.43-7.fc44`, `rpm-build-libs-6.0.1-2.fc44`, `rpm-sign-libs-6.0.1-2
  .fc44`, `dnf5-plugins-5.4.2.1-1.fc44`). The Containerfile names all
  five removals and the 257 installs in one transaction (`dnf5 do
  --action=remove ... --action=install ...`), with `--disablerepo='*'`,
  weak dependencies off, and `clean_requirements_on_remove` off, so
  nothing unnamed is erased; the image records the five removals and
  the one install, and `rpm -q` confirms every closure NEVRA. This is
  read as M0-B.3's "explicit, named, local operations", not as stop
  condition 11; the swap-alone transaction's refusal is retained in the
  evaluator record for review.
- **Koji serves the signed copy.** Koji's `<arch>/` file is the unsigned
  build and the strict signature check refuses it; the fetch takes the
  signed copy under koji's `data/signed/<key id>/` path for the one RPM
  the repositories no longer hold.
- **The SSH client was already in the closure.** `openssh-clients` is a
  hard requirement of the closure's `git-core`, so `ssh` and `scp` exist
  inside the image; their roles are host-only all the same, and no
  package was added for them or for `podman`, which is absent inside.
- **Verification counts.** 256 RPMs came from Fedora's repositories (116
  `fedora`, 140 `updates`) and one from koji; 257 of 257 signatures are
  good under the Fedora 44 key (`6d9f90a6`); 254 header digests equal the
  host's installed packages', and the remaining three (B3's pinned `m4`,
  `bison`, and `flex`, not installed on the host) equal B3's SHA-256
  pins. Inside the evaluator the lock passed with 26 roles checked and 3
  skipped, every gate passed, and all 146 images are byte-identical with
  the host's.

### What this revision does not change

The base image and its digest, the closure's NEVRAs, the 26 existing
roles, the Linux and OpenSBI pins, the gates the evaluator runs, the
read-only mounts and the no-network rule, the image-identity requirement
(every image byte-identical with the host's), the board procedure, and
stop conditions 1 to 12. M0-4's exit criteria then apply unchanged:
`mvp check`, `kexec-rehearsal`, and `evaluate` pass, with images
identical across host and evaluator. M0-5 follows when they do.

### Revision status record

```text
mvp_m0_plan_revision_m0b=directed-2026-10-24;accepted-with-result-b2669725-2026-10-26
mvp_m0b_direction_instruction=accept-A
mvp_m0b_closure=257-nevras-unchanged;sha256-per-rpm;signature-and-header-digest-verified
mvp_m0b_rpm_source=fedora-repositories-then-koji;verified-local-cache;repositories-disabled-at-build
mvp_m0b_swap=systemd-standalone-sysusers-for-systemd-sysusers-259.10-1.fc44.x86_64
mvp_m0b_host_only_roles=podman,ssh,scp;not-in-closure
mvp_m0b_evaluator_network=base-pull-and-closure-fetch-only
mvp_m0b_implementation=b364fe92,83916b5a,67731e4c,19c3d455;evaluate-pass;images-identical-146-of-146
mvp_m0b_base_removals=systemd-standalone-sysusers,glibc-minimal-langpack,rpm-build-libs,rpm-sign-libs,dnf5-plugins;named-in-one-transaction
```

## Plan revision M0-C: the control hart's drain order

**Status: directed, not yet accepted at an exact commit.** On 2026-10-25
(02:22Z) the first GCC scenario run of the M0-5 board campaign on the
COM260, host kernel 7.3.0-65.1, ran both Linux guests concurrently on
harts 1 and 2 to `BE_MVP:14` (overlap `0x25403a9` of the shorter run's
`0x2563c63` ticks, 99.6 percent; `exits=157` each; `ipi=1` and `srst=1`
for both; hart 0 idle 43 percent), and the capture checker failed it on
one finding: `5 alternations between the domains' lines, fewer than
K = 8 (Q5)`. `k3-campaign.sh` stopped before runs 2 and 3, as stop
condition 6 requires (a board outcome QEMU did not show). The preflight,
both load checks, and the three probe runs had passed. The responsible
human was offered a monitor fix (A), a checker-only change (B), and a
stop (C), and directed `proceed with A`. As with M0-A and M0-B, the
direction is recorded here, implementation proceeds under it, and the
exact commit carrying this revision is presented for acceptance with
M0's result packet. It changes no accepted byte and no accepted document.

### The cause

Hart 0's control loop drains block 0's ring to empty and then block 1's
on every wake (`mvp/src/mvp-runtime.c`, `control_loop` and `drain`), and
each drained LINE record is printed through the firmware console before
the next record is taken. In QEMU the console is effectively free, so
hart 0 woke once per record or so (109 wakes for 138 records) and the
printed order followed the production order. On the board the 115200
baud UART is the bottleneck: the guests' 9.7 KB of text takes about
0.85 s to print while the guests finish in 1.63 s, so hart 0 woke three
times for 138 records and printed six long batches (41, 57, 20, 4, 4,
and 4 lines). The alternation count therefore measured hart 0's drain
batching, not the guests' concurrency; the ticks-based overlap, which
does measure it, passed. The accepted inference under Q5, "both floors
sit well below the expected values", held in emulation and not on
hardware. It is a defect in the plan's inference and in the monitor's
drain order, not in the guests, the substrate, or the checker's rule.

### M0-C.1 Round-robin drain

Hart 0 drains the two outbound rings round-robin: on each wake it takes
and prints at most one record from block 0, then at most one from block
1, and repeats until both rings are empty. Each ring's head is acquired
and its tail released around each take as before (the reader's fences
and the single-writer rule for the tail do not change), so the printed
order follows the order in which records became visible to hart 0, and
the alternation count measures what Q5 meant it to measure. The
`ring-full` variant's hold (M0-A.3) applies to each take as it applied
to each pass. Nothing else in the control loop, the rings, the IPIs, the
records, or the domain harts' code changes; `records`, `wakes`, `lines`,
and every other counter keep their meanings. The probe images share the
drain code and are rebuilt; their one-domain behaviour is unchanged.

### M0-C.2 The floor stays, re-justified

K = 8 stays the floor and keeps its definition (alternations between the
domains' lines in hart 0's drained output, control-hart lines ignored).
Its justification becomes: with the round-robin drain, two domains that
produce lines at once alternate on the console at least once per wake
in which both rings hold a record, and the guests' boot and eight
`STEP` lines each give many such wakes on both QEMU and the board; a
console-bound hart 0 lowers the wake count but not the alternation
between the two rings within a wake. The result packet reports the
board's and QEMU's alternation counts and wake counts side by side so
the justification can be checked against the record.

### M0-C.3 Checks and the board campaign

`make -C mvp check` (host tests, both toolchains' images and the image
checker, the QEMU suite, the capture checker with its fixtures and
mutations, the evidence bundle), `./mvp/mvp evaluate` (images identical
across host and evaluator), and the eight-hart kexec rehearsal must pass
again before the board. The in-tree capture fixtures are regenerated
from the new images' QEMU runs where the drain order changed them, and a
fixture made from the stopped board run's capture (the drain-batched
order, 5 alternations) is kept as a negative that the checker must still
reject. The board campaign restarts from the beginning of M0-5's kexec
runs with the new images: the two load checks, the three probe runs,
three GCC and one Clang scenario runs, then the `payload` run, with a
human reset after each; the preflight stands. The stopped run's record
(`20261025T022152Z`) is retained as stop-6 evidence in the campaign
directory and the result packet; it is not a scenario result.

### M0-C as implemented and reviewed

The implementation (`mvp/` commits `129626e0`, `c5ecedee`, and
`2d0a4fe5`, written by the `claude-opus-5.5` sub-agent) was reviewed in
full by the orchestrating session, which read every changed line and
re-ran the host tests and one QEMU run itself. The reading it takes of
M0-C.1 and the review's findings are recorded here for the result
packet.

- **One take per visit, the tail released before the print.** Each
  visit acquires the ring's head, fences, takes at most one record into
  hart 0's own copy, fences, releases the tail, and only then steps the
  record (prints the line). M0-C.1's "acquired and its tail released
  around each take" is read as around the ring's take, the copy, not
  around the print; nothing reads the ring's bytes after the copy, so a
  slow console holds no ring bytes and the rings' high-water marks fall
  on a console-bound hart 0. Before M0-C the tail was released once per
  pass after every take and print. No marker or counter changes meaning.
- **The order and its bound are pure C.** `be_mvp_drain_begin`,
  `be_mvp_drain_next`, and `be_mvp_drain_visited` (`mvp-hart.c`) hold the
  round-robin order and the bound, each ring's capacity in record headers
  plus one visit, so that every record a ring held when the drain began
  is taken even against a writer as fast as the drain; the drain ends
  when the latest visit to each ring took nothing. `hart-test.c`'s
  `test_drain_order` pins the take sequence and visit counts over every
  pair of fill levels up to eight, the one-ring probe case, a held ring,
  a fast writer, the bound at each ring size, and invalid arguments (652
  scenarios, 140,687 assertions, identical for GCC and Clang).
- **The floor is load-bearing on the board's capture.** The stopped
  run's capture is an in-tree fixture that the self-test requires the
  checker to reject with the alternation finding alone and
  `records=138 wakes=3 alternations=5`; all 154 mutations stay rejected.
- **QEMU cannot show the fix,** because hart 0 there wakes about once
  per record under either drain (the suite's `k3-like` runs: GCC 101
  alternations in 110 wakes, Clang 87 in 114; before, 94 in 112 and 94
  in 115); the host test and the board re-run are its evidence.
- **Two harness defects found by the review** were fixed after it, in
  test-only code (`mvp/` commit `f89366bc`): the evaluator overwrote its
  record directory on every run, and B0's retention filed two load
  checks made in one UTC second under one name, so the board record kept
  one; each evaluator run now has its own record directory, and
  `evidence.py --board` stages the load checks under
  toolchain-qualified names before the unchanged B0 tool retains them,
  with a deterministic dry-run case for the same-second pair.
- **Host drift blocks the gates, not M0-C.** A workstation update on
  2026-10-24 (17:02 EDT) replaced the closure's
  `ca-certificates-2026.2.92_v9.0.319-1.fc44` with `-2.fc44`, so the
  tool lock fails on the host and `mvp check` and `mvp evaluate` stop at
  their first step; every later stage passes (`c5ecedee`, 2 min 39 s;
  QEMU 34 runs, 43 attempts, 9 refused; kexec rehearsal GCC and Clang).
  The orchestrating session first proposed restoring the locked
  package from the verified local cache (a `dnf downgrade` of the
  signature-checked `-1.fc44` RPM); the responsible human declined it
  (`we can't downgrade those certs, it's a security issue`), which
  stands: the lock does not justify rolling a security package back on
  the workstation, and that remedy is withdrawn. The remaining remedy is
  the plan's own, a lock and closure refresh from the host as it is,
  which runs only on the responsible human's direction: `tool-lock
  refresh` (the 26 roles expected to reproduce byte for byte, as in
  M0-B; the closure's one changed line `ca-certificates` `-1` to
  `-2.fc44`, which `openssl-libs` requires), `fetch-closure --record`
  for the new RPM's signature-verified digest, the evaluator image
  rebuilt from the cache with repositories disabled, then `mvp check`,
  `mvp evaluate`, and the kexec rehearsal again; a diff beyond that one
  closure line, its digest, and the re-bound `MVP_CLOSURE_SHA256` is a
  stop. The responsible human directed `refresh the lock` on
  2026-10-25: the refresh reproduced all 29 roles byte for byte and
  changed the one closure line and its digest (`mvp/` commit
  `804fa95f`), the evaluator image was rebuilt from the verified cache,
  and `mvp check`, `mvp evaluate` (146 of 146 images identical), and the
  kexec rehearsal pass on the M0-C images. That the lock pins the host's
  security packages into the evaluator's closure, so that every such
  host update drifts it, is a question for the result packet and M1's
  plan, not for M0-C.
- **The board campaign that M0-C.3 restarts passed.** On 2026-10-25 and
  26, with the M0-C images, all eight RAM-only kexec runs passed on the
  COM260: the three GCC probe runs, three GCC and one Clang scenario
  runs with `records=138 wakes=2 alternations=125` in each (the old
  drain's 3 wakes gave 5), and the `payload` run failing as declared; no
  stop condition applied. M0-5 and M0-6 are complete, and the M0 result
  is responsible-human accepted at exact commit
  `b266972563a39b0687ba2ac8c5b4cb943f3c766a` as of 2026-10-26
  (instruction `accept b26697`), with this revision and M0-A and M0-B,
  as each revision's status record says; the
  [result review and acceptance record](mvp-m0-result-review-summary.md)
  holds the decision. `mvp/README.md` holds the results.

### What this revision does not change

The hart layout, the hart region, the rings' format and sizes, the IPIs,
the boot sequence, the markers, Q5's two floors and their values, the
guest SBI surface, the firmware surface, the tool lock, the evaluator,
the board procedure, the work packages, and stop conditions 1 to 12.

### Revision status record

```text
mvp_m0_plan_revision_m0c=directed-2026-10-25;accepted-with-result-b2669725-2026-10-26
mvp_m0c_direction_instruction=proceed-with-A
mvp_m0c_trigger=board-gcc-run-1-alternations-5-below-K-8;stop-6;record-20261025T022152Z
mvp_m0c_drain=round-robin-one-record-per-domain-per-pass
mvp_m0c_floor=K-8-unchanged-rejustified
mvp_m0c_board_campaign=restart-load-checks-probes-scenario-payload
mvp_m0c_implementation=129626e0,c5ecedee,2d0a4fe5;reviewed-by-orchestrator;harness-fixes-f89366bc
mvp_m0c_gates=host-tests-pass;qemu-suite-pass;kexec-rehearsal-pass;check-and-evaluate-blocked-by-host-lock-drift
mvp_m0c_lock_drift_remedy=downgrade-declined-security;refreshed-under-direction-804fa95f;gates-pass
mvp_m0c_board_campaign_2=20261025-com260;load-checks-pass;probe-platform-pass;remaining-runs-pending-resets
```
