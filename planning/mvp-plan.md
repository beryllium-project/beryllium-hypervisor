<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# S3: MVP plan for the initial security-research platform

## Decision record

The responsible human accepted this document as the S3 MVP plan at exact
commit `93967fbac926b4fdfdfe636df4d07e8926b625b7` (parent
`882868b952b7921bd528555b7f20c908cb363eea`) on 2026-10-23. The
instruction, given in reply to the
[review packet](mvp-plan-review-summary.md)'s request to accept, revise,
or defer that exact commit, was `accept 93967fba`, which resolves
uniquely to that commit.

- **Scope:** acceptance covers exactly the document text at that commit,
  revision 1 of the plan. Everything after this section is the document
  as accepted, including the pre-decision status text below; only this
  section and the acceptance fields in the status record were set
  afterwards. The first candidate `06c35f48` stays superseded and was
  never accepted.
- **Open questions:** Q1 to Q12 were not answered, so the defaults the
  document applies stand: MVP 1.0 is M0 to M4, with M1 a step toward M2
  (Q1); a self-contained MVP line (Q2); M0's platform record as the K3
  evidence beyond the B-series (Q3); the pinned Linux guest with a
  `nolibc` program and two polled single-writer pages for M2 (Q4); M3 in
  MVP 1.0 (Q5); a public release through a new clean repository, each
  step separately authorized, GPL-3.0-only (Q6); no independent review
  beyond the responsible human's exact-commit reviews (Q7); findings
  S5-S8 and S10 and R4's budget outside MVP 1.0 (Q8); the run's time
  budget on hart 0's Sstc timer (Q9); eight harts in the QEMU profile
  (Q10); a terminated domain's hart parks in HS (Q11); and harts 0, 1,
  and 2 as the device tree numbers them (Q12).
- **Effect:** this document selects M0 to M4 in its order, records D1 to
  D16 at their defaults, and authorizes writing M0's bounded plan, which
  includes the static multi-hart substrate, on a new branch from the
  development branch. It authorizes no implementation, hart start, board
  run, accepted-byte change, model change, security model v1 revision,
  push, merge into the development branch, publication, or release step;
  M0's plan and each later milestone's plan and result need their own
  acceptance.

## Status

Proposed for responsible-human review; not accepted. This is S3, directed
on 2026-10-22 by the instruction `merge & push, start S3`, given after
[security model v1](security-model-v1.md) was accepted at exact commit
`0e3eec8b` (instruction `accept 0e3eec8b`). Under the same instruction the
development branch was fast-forwarded to `0096de3e`, the record of that
acceptance, and pushed to the private `origin`.

This is revision 1 of the plan. The first candidate, exact commit
`06c35f48`, defined MVP 1.0 as single-hart: two Linux guests time-sliced
on hart 0 by B7's round-robin scheduler, with a second hart a non-goal and
a stop condition. On 2026-10-23, before deciding on it, the responsible
human directed a revision: `revise the plan so that the MVP 1.0 is one
hart per guest and the security monitor / protected domain (remind me,
what are we calling this?) has its own hart as well`, and answered four
design questions ([revision record](#revision-record)). `06c35f48` is
superseded and was never accepted. Revision 1 changes the concurrency
model, the hart layout, M0 to M3, decision D8, the stop conditions, and
the risks, and adds D14 to D16 and Q9 to Q12; the release path, the
harness rules, and the other decisions stand.

The roadmap defines S3 as "The initial security-research-platform release:
scope, non-goals, milestones, evaluation harness, evidence claims, and
release path", with one accepted plan as its exit. This document is that
plan. It selects and orders the MVP milestones and records the decisions
that the accepted documents leave to S3. It implements, runs, and proves
nothing. Accepting it would select the milestones and authorize writing the
bounded plan for the first of them, M0, and nothing else: each milestone's
plan and result, every board campaign, and every push, publication, or
release step need their own decision.

Line references are to the development branch at `0096de3e`.

## Revision record

| Date | Event |
| --- | --- |
| 2026-10-22 | First candidate proposed at exact commit `06c35f48`: a single-hart MVP on B7's scheduler, with a second hart excluded. Not accepted. |
| 2026-10-23 | The responsible human asked, of B7's time-slicing, `is this really useful? would it be better to have two guests running on their own harts?`, then directed the revision quoted in [Status](#status). Terminology was confirmed: the privileged HS software is **the monitor**; the anchor use case's VS subject is **the protected domain** (`prot_t`), beside **the untrusted Linux domain** (`host_t`). Because the monitor's enforcement path must run in HS on every hart that runs a domain ([research](isolation-engine-policy-research.md) L165-L169), "its own hart" is read as a dedicated control hart. |
| 2026-10-23 | Form answers: `control_hart=control_hart`, a dedicated control hart rather than the research document's monitor-on-every-hart-only layout; `layout_confirm=true`, M1 on a control hart, a writer hart, and a reader hart, and M2 on a control hart, an untrusted Linux hart, and a protected-domain hart; `substrate_home=fold_into_m0`, the multi-hart substrate is built in M0 rather than in a new B8 bring-up milestone; `model_treatment=add_hart_obligations`, M3 adds per-hart obligations and the security model v1 revision they need. |
| 2026-10-23 | Revision 1 proposed at this commit; `06c35f48` superseded. The revision was written in a session the responsible human switched to `claude-fable-5.1`; the model pin in `.github/copilot-instructions.md` is unchanged. |

## Decision requested

Accept this exact commit as the S3 MVP plan, request revisions, or defer.
Answer any of Q1 to Q12 or let the defaults apply.

## Inputs

| Input | Exact commit | What this plan takes from it |
| --- | --- | --- |
| [Security model v1](security-model-v1.md) | `0e3eec8b` | The policy notation and its analyses A1 to A8; Instance 2 as M1's policy; validate over compile (V1); the pipeline and the authority report schema (Part 4); the two differences from B7 that are "S3's to build" (Instance 2); the management-request vocabulary that Part 6 leaves "to S3 and to the first protected-domain milestone"; the Model 0.2 change inventory (Part 7) |
| [S1 synthesis](he-to-be-synthesis.md) | `fd670dcd` | The "Hand-off to S3", items 1 to 6, and the three gaps to close "before any isolation claim between Linux guests": no shared page or denial test between Linux guests on K3, K3's unrecorded `htval`, and K3's untested VMID tagging |
| Model 0.1 plan revision M01-A, in [Model 0.1](architecture-model-0.1.md) | `95ef0f6c` | The TE-family policy as the specification, not trigger-gated; a runtime TE check only if its trigger fires |
| [Project review](project-review-2026-10-17.md) | `480dab72` | Findings F-05 to F-13, F-16, and F-17, and options 2, 3, 4, and 7: reconcile the first MVP milestone with the anchor use case, decide what replaces R8's characterization, choose a verification method per claim, and schedule the debt |
| [B7 plan](k3-b7-plan.md) and [result](k3-b7-result-review-summary.md) | `026974fb`, `7b6b846b` | The two-guest substrate on K3, and "Shared pages, channels, denial logging, fault injection, console input, and a richer userland stay for the MVP plan"; B7's scheduler, which revision 1 leaves as bring-up history |
| [B1](k3-b1-result-review-summary.md) and [B2](k3-b2-result-review-summary.md) records, and B7's preflight record | at `0096de3e` | "Linux stopped its other harts before each kexec" (B1 L158, B2 L171); the COM260 preflight of 2026-10-08: `online_cpus=0-7`, eight `cpu@N` nodes each listing `h`, `sstc`, `smaia`, `ssaia`, and `svinval`, and "SBI HSM extension detected" (`bringup/k3-b7/results/20261008-com260/preflight.txt`) |
| [Implementation plan](implementation-plan.md) | at `0096de3e` | The anchor use case (L629-L641) with its availability and side-channel scope (L643-L658), principle 5 (L681), threat model v0 (L483), the selected concurrency model (L1201-L1228: Stage 1 single-hart, Stage 2 serialized multicore, and the proof targets), the expected first MVP milestone (L2003), and candidate milestones 3 to 10 (L2020-L2089), in particular milestone 4 (L2030-L2038) |
| [Isolation-engine and policy research](isolation-engine-policy-research.md) | at `0096de3e` | "Why the monitor executes on every hart" (L165-L181), the "Smallest multicore experiment" (L183-L217), and "Per-hart and global state" (L219-L251) |
| [RISC-V security hardware](riscv-security-hardware.md) | at `0096de3e` | K3's RVH, Sstc, and AIA (L70-L76); the CPU-side shared-memory ordering test the PoC owes (L142-L152); "Keep every non-participating X100 hart parked and measured as a firmware assumption" (L230) |
| [Roadmap](roadmap.md) and [planning README](README.md) | at `0096de3e` | What the MVP plan decides: development kernel/BSP, root integration, a formal K3 evidence package, a richer userland, and whether to recreate KVM0 |
| `LLM_POLICY_ALIGNMENT.md` | at `0096de3e` | The public release boundary, the clean-repository migration, and the license boundary |

## What the MVP is

MVP 1.0 is the first Beryllium release that a security researcher can build
from source, run in QEMU and on a K3 board, and use to study isolation
between Linux-class domains under a declared policy, with evidence that
states exactly what was tested. It is deliberately limited: three
statically assigned harts of the board's eight, no devices, a static
configuration, and claims bounded to tests, emulation, diagnostic board
runs, and proofs about the abstract model.

The plan reconciles the expected first MVP milestone with the founding
anchor use case (project review F-08 and option 2) by taking the first as a
step toward the second:

- **M1** is the expected first MVP milestone as S1 adapted it (H55) and
  security model v1 specifies it (Instance 2): two Linux guests, a writer
  and a reader, share one page; private memory is denied; the monitor
  injects the faults and logs each denial.
- **M2** is the anchor use case in its smallest static form: "a protected
  security-research domain whose confidentiality and integrity remain
  enforced after host Linux is compromised" (implementation plan L629),
  holding "a secret and an integrity-sensitive computation" (L641) beside an
  untrusted Linux domain that may stop it but cannot read or alter it or
  its core-held measurement.

The reason is the founding plan's own: the anchor defines "the first usable
system", and a release without it would offer researchers a denial
demonstration but no protected research domain. The TE PoC scenario comes
first because it exercises, on the smallest configuration, everything M2
reuses: a declared channel, offline policy checks, fault injection, and
denial logging between Linux guests on K3. Reproducing that scenario still
selects no runtime TE mechanism: under M01-A the TE-family policy is the
specification, and enforcement stays derived from it.

### Hart layout

Every domain runs on its own hart, and the monitor's shared work runs on
a hart of its own (revision 1). The K3 COM260 has eight X100 harts, each
with the hypervisor extension, Sstc, and AIA (B7's preflight record). MVP
1.0 uses three:

| Hart | Role | M1 | M2 |
| --- | --- | --- | --- |
| 0 | Boot and control hart: HS only, never enters a domain | the monitor's control loop | the same |
| 1 | Domain hart | the writer (`writer_t`) | the untrusted Linux domain (`host_t`) |
| 2 | Domain hart | the reader (`reader_t`) | the protected domain (`prot_t`) |
| 3 to 7 | Never started; a recorded firmware assumption | | |

The monitor is not confined to hart 0. A hart that runs a domain has its
own HS trap state, `hgatp`, VMID, trusted stack, and fence obligations,
so the monitor's enforcement path runs in HS on every domain hart
(research L165-L169). What hart 0 holds is everything the domain harts
would otherwise have to share: it validates and seals the configuration,
derives the roots, starts the domain harts, publishes the sealed
configuration through a boot barrier, owns the console and the denial
log, holds M2's measurement, decides M2's management requests, and keeps
the run's time budget (Q9). A domain hart runs the HS fast path and
nothing else: it takes its domain's exits, decides them from captured
inputs and its private per-hart state, and posts records to a ring that
only it writes and only hart 0 reads. No lock, atomic read-modify-write,
or shared mutable word sits in a domain hart's fast path; the only
steady-state global mutation is hart 0's.

This is the static part of the implementation plan's selected concurrency
model, Stage 2 (L1211-L1220): "CPUs are statically assigned to domains or
the management role", fast-path state is per-core, and shared mutable
state is confined to one bounded serialized control path, here the
control hart. The dynamic part, the global control lock and the dynamic
mapping protocol (L1215-L1219; research L240-L269), stays with
implementation-plan milestone 4. The layout is the research document's
"Smallest multicore experiment" (L183-L217) with a control hart added.
The research document weighs a dedicated control hart against the
simplest design and names what it adds: "an inter-hart request queue; IPI
delivery and acknowledgement; an availability dependency; additional
shared state; and another protocol to specify and prove" (L171-L181).
Revision 1 takes it on the responsible human's answer, because M2's
management requests, the console, and the denial log would otherwise need
a lock between domain harts, and because it keeps every domain hart's
fast path free of shared state. The five costs are carried as
[risks](#risks), and the protocol is recorded as unproved in the
[claim ledger](#method-per-claim).

Why not time-slicing: B7 showed that two Linux guests can share hart 0
under a round-robin scheduler, with identical counts across four board
runs. For the MVP that layout would make every isolation scenario depend
on the scheduler, let one domain's idling set the other's timing, never
exercise the declared channel under real concurrency, and leave M2's
protected domain running only when the untrusted domain yields. Static
ownership removes the scheduler and the per-switch save and restore from
the MVP's mechanism, at the price of a boot barrier, cross-hart
signalling, and the first second hart Beryllium has ever started.
Availability stays outside the claim either way.

## Scope

In MVP 1.0:

- One platform profile: the K3 COM260, harts 0 to 2 of eight, statically
  assigned as in [Hart layout](#hart-layout), RAM-only loading through
  Linux kexec from hart 0 as in B7, with human resets; QEMU with eight
  harts as the emulation profile (Q10). The B-series board-safety rules
  stand unchanged.
- Static hart ownership: the control hart starts each domain hart once
  through SBI HSM, binds it to one domain, one root, and one VMID before
  the boot barrier, and never migrates, overcommits, or restarts a domain.
  Harts 3 to 7 are never started.
- Cross-hart signalling through the SBI IPI extension and single-writer,
  single-reader rings: a domain hart posts denial records, console bytes,
  and M2's management requests to hart 0; hart 0 delivers M2's `pause`
  and `terminate` and the request results to a domain hart. No guest sees
  an injected interrupt.
- No scheduler: a domain's `wfi` completes natively (`hstatus.VTW`
  clear), its Sstc timer is its own, and there is no HS time slice.
- Guests: the pinned upstream Linux `v7.2` guest of B6 and B7,
  uniprocessor, without devices, FP, or vector, running `nolibc` programs
  built from the pinned tree.
- A static configuration per scenario: a policy in security model v1's
  notation, a labeling, and a manifest, checked offline before the image is
  built, with the derived roots re-walked and checked by the monitor at
  boot.
- Declared channels as static shared pages, each with a single writer.
- Guest fault injection and denial logging with resume, on an exact
  accepted-exit set.
- Distinct VMIDs per domain, each published once on its hart with its
  root and read back; no `hgatp` write after the boot barrier.
- B7's guest SBI subset (Base, DBCN, TIME, SRST) and, for M2, a minimal,
  versioned management extension for the untrusted Linux domain.
- A core-held measurement of the protected domain and the configuration
  (M2), as local identity only.
- The evaluation harness of this plan.
- The policy layer that security model v1 Part 7 inventories for Model 0.2
  (M3).
- A release candidate and the release path (M4).

## Non-goals

| Excluded from MVP 1.0 | Source or reason |
| --- | --- |
| Dynamic multicore: domain migration, vCPU overcommit, shared run queues, starting or stopping a hart after the boot barrier, the global control lock and dynamic mapping protocol, fine-grained locking, and multicore hardware validation | Implementation-plan milestone 4 and the dynamic part of Stage 2 (L1211-L1228); S1 H57 |
| Time-multiplexing two domains on one hart: B7's scheduler, HS time slice, and per-switch save and restore | Revision 1 ([Hart layout](#hart-layout)); B7's records stay accepted bring-up history |
| Devices, IOMMU, IOPMP, DMA, I/O service domains, and guest-visible interrupt injection beyond each domain's own timer; the monitor's HS-to-HS IPIs are not guest-visible | Milestone 5; the B-series stop on `hvip` injection; the policy notation "does not express" device or interrupt-injection objects (security model v1) |
| Dynamic management: creating domains, assigning regions, creating channels, revocation other than terminating a domain, delegation envelopes, and generations | Security model v1 Part 6; both triggers are "undecidable" for the dynamic case (Part 5) |
| Software capabilities and any runtime TE check | Neither trigger fires for the fixed profile or the first MVP milestone (security model v1 Part 5); M2's plan evaluates both triggers for its own use case |
| Remote attestation, measured boot, sealed storage, and anti-rollback | Milestone 7; M2's measurement is local identity, not attestation |
| Arm or another ISA | Milestone 8 |
| An assurance release: open binary correspondence, C refinement, and whole-system proof | Milestone 9 |
| Upstream submission and Kbuild placement | Milestone 10; the license boundary |
| Guest console input and a richer userland, such as BusyBox with musl | Roadmap; the `nolibc` programs suffice for every scenario here |
| Development-kernel/BSP selection | No domain sees a device, and no Linux runs on the bare board under Beryllium |
| Recreating KVM0 or an R8-style formal K3 evidence package | The roadmap and README leave both to this plan; see D4 and D6 |
| Hardware validation, qualification, microarchitectural noninterference, and availability against the untrusted domain, including the control hart's availability under a flood of requests | Threat model v0 and the anchor's availability and side-channel scope (implementation plan L643-L658) |
| Any change to an accepted R0-R7 or B0-B7 byte | Accepted targets are immutable; accepted code enters through counted, re-derivable ports, as in B1-B7 |
| LiteBox or another library OS as a guest, and CHERI mechanisms | Later research ([LiteBox sidebar](sidebar-minimal-vs-runtimes.md)); CHERI alignment is stated, not implemented (D12) |

## Milestones

Each milestone needs its own bounded plan and its own result acceptance, as
B5 to B7 did. The defaults below for board campaigns follow B7: three GCC
runs and one Clang run, RAM-only, on the COM260.

### M0. The MVP line, the multi-hart substrate, and the evaluation harness

**Goal.** One maintained, pinned, reproducible source line for the MVP;
the static multi-hart substrate every later milestone runs on; and the
harness through which every later milestone produces its evidence.

**Delivers.**

1. One maintained tree, working name `mvp/`, seeded from B7 by B7's own
   counted port method. Later milestones change this tree in place instead
   of copying it forward, which ends the chain of generated copies across
   milestones (project review F-12). Accepted R-series code keeps entering
   through counted, re-derivable generated ports; no accepted byte changes.
   B7's boot, G-stage pair, SBI subset, console, markers, and tools are
   carried; its scheduler, HS time slice, and per-switch save and restore
   are not.
2. A tool lock that the development host can satisfy (project review
   option 7; S1 H32): exact versions and digests of the cross GCC and
   binutils, Clang and LLD, QEMU, Python, OpenSBI for the QEMU profile, and
   the Linux source pin, with a digest-pinned open container image as the
   clean evaluator and the reproducibility wording "digest-pinned base plus
   recorded closure".
3. The evaluation harness described below, with B7's two-guest scenario,
   re-hosted on two domain harts, as its first scenario.
4. A K3 platform record from bounded probes and selected negative images
   on the board (S1 H16, H27; project review option 3): K3's `htval` and
   `htinst` for G-stage faults, recorded before any fault-injection design
   depends on them; the `hgatp` modes and the VMID width as Beryllium reads
   them back; the PMP and domain regions as OpenSBI reports them at boot;
   the hart topology the device tree and firmware describe, including
   which harts share a cluster (Q12); the HSM state of harts 1 to 7 after
   kexec and the result of each `hart_start`; IPI delivery to HS on a hart
   whose domain is running and on a hart waiting in HS; the ordering of a
   flag and a payload written on one of the layout's harts and read on
   another, with and without fences (hardware doc L142-L152); and a
   bounded single-hart VMID probe in B7's style, two roots switched on one
   hart with the fence omitted, once under distinct VMIDs and once under
   one shared VMID, each a separately linked negative image whose observed
   translations are recorded as a platform fact, not as a claim. Cache and
   debug behavior beyond that ordering probe stay unexamined and outside
   every claim.
5. The static multi-hart substrate of [Hart layout](#hart-layout). Hart 0
   runs the accepted R3 prelude as B6 and B7 do, validates and seals the
   configuration, derives both roots, initializes a trusted stack and a
   private state record for each domain hart, starts harts 1 and 2 with
   SBI HSM `hart_start` at a monitor entry point, and publishes the sealed
   configuration through a boot barrier; each domain hart installs its one
   root and VMID, reads them back, and enters its domain once. After the
   barrier no hart is started or stopped, no root is written, and no frame
   changes owner (research L204-L217). Hart 0 then runs the control loop:
   it waits in `wfi` for IPIs, drains each domain hart's ring in order,
   writes the console with each domain's prefix, keeps the denial log, and
   ends the run when both domains have shut down or the time budget
   expires (Q9). Each ring has one writer and one reader, with release and
   acquire fences and no atomic read-modify-write; a full ring fails
   closed on the writing hart. B7's two-guest scenario on this substrate
   is the first harness scenario, with per-hart exit counters in place of
   B7's switch counts.

**Exit.** B7's scenario, re-hosted on two domain harts, passes under the
harness in QEMU and in the default board campaign, built from the MVP
line with the locked tools: both domains boot their Linux and run to
power-off concurrently, each domain's line set appears exactly once
through hart 0's console, and the counters match their declared exact
values or ranges; the selected negative images fail as declared on the
board, with `htval` and `htinst` recorded; the platform record, including
the hart, HSM, IPI, ordering, and VMID facts, is retained.

**Evidence.** Host tests, emulation, and diagnostic bring-up evidence.
M0 is the first time Beryllium starts a second hart, takes an IPI in HS,
or shares a page between harts; each result is diagnostic bring-up
evidence for one board, never hardware validation.

### M1. The TE PoC scenario on two Linux guests

**Goal.** The expected first MVP milestone, as S1 hand-off item 1 states it
and security model v1 Instance 2 specifies it.

**Delivers.**

1. Instance 2's policy, labeling, and manifest as the scenario's
   configuration. The offline checker runs A1 to A6 and A8 on them and
   emits the authority report of Part 4 from the sealed manifest and the
   derived roots; any failing check, any grant without an allowing rule,
   or any undeclared flow stops the build, because such a configuration
   "must not be sealed" (Part 4).
2. Root derivation that admits exactly the declared channel: the writer's
   root maps the shared page read-write and the reader's maps it read-only.
   B7's pair check, `be_b7_gstage_pair_check` in
   `bringup/k3-b7/src/b7-gstage.c`, which "refuses shared pages", becomes a
   check that every page two roots share is a declared channel with its
   declared rights; it still refuses everything else.
3. Fault injection with denial logging and resume (S1 H15, H16): an exact
   accepted-exit set; a G-stage fault on a page the guest's root does not
   map, or a store to the read-only page, is logged once with the domain,
   the cause, the guest physical address from `htval`, `htinst`, and
   `sepc`, and is delivered to the guest as the corresponding access fault.
   The guest resumes only when every recorded field matches the accepted
   entry. M1's plan fixes the injected encoding from M0's `htval` and
   `htinst` record. An exit outside the set still ends the run, as in B7.
4. Distinct VMIDs, one per domain hart, each published once with its root
   before the boot barrier and read back; after the barrier no hart writes
   `hgatp`, which the image checker enforces as a single-writer rule. The
   stale-authority check of S1 H12 was a check on switching between roots
   on one hart; with no switch in the scenario it no longer applies, and
   K3's VMID tagging is characterized by M0's probe instead. The invariant
   it protected is restated for this layout: each root is installed on
   exactly one hart, under exactly one VMID, for the whole run.
5. Guest programs built with `nolibc`. The writer and the reader run at
   the same time on their harts, so the protocol over the shared page is
   explicit: the writer writes a pattern and then a flag word, with a
   release fence between; the reader polls the flag, reads the pattern
   behind an acquire fence, and checks it. The reader then attempts a
   store, which is denied, logged, and observed by the guest program; each
   guest attempts one access outside its window. Both guests then power
   off.
6. Separately linked negative images (S1 H27), run on the board as well as
   in QEMU: an undeclared flow, which A6 must reject at build time; a
   manifest grant with no allowing rule, which A8 must reject; a reader
   root with write rights, which the boot-time channel check must refuse;
   and a disabled injection path, which must fail closed.

**Exit.** In QEMU and in the default board campaign, both domains run
concurrently, each on its own hart; data crosses the channel from writer
to reader only; every denied access appears exactly once in the monitor's
denial log, with the fields the guest reports and in the order the guest
reports them; both guests continue and power off; the authority report
lists exactly Instance 2's grants and the one flow `writer_t ->
reader_t`; every check passes; and every negative image fails as
declared. This closes S1's three gaps before any isolation claim between
Linux guests: the shared page and the denial test on K3 here, `htval` in
M0's record, and VMID tagging in M0's probe.

**Evidence.** Host tests, emulation, diagnostic bring-up evidence, and the
offline checks.

### M2. A protected research domain beside an untrusted Linux

**Goal.** The anchor use case in its smallest static form: a protected
domain whose confidentiality and integrity hold against an untrusted Linux
domain that may stop it but cannot read or alter it.

**Delivers.**

1. A third policy instance in security model v1's notation: `host_t` for
   the untrusted Linux domain and `prot_t` for the protected research
   domain; their private memory; a request page that `host_t` writes and
   `prot_t` reads and a response page that `prot_t` writes and `host_t`
   reads, each a declared channel; and `domain` rules that give `host_t`
   only `pause` and `terminate` on `prot_t`. This is the first instance in
   which a domain holds a `domain` permission, the use the class was kept
   for ("the monitor's transitions on behalf of one domain toward
   another"). A1 to A6 and A8 pass. A5 reports both pages as "static, not
   revocable, single writer", which this plan accepts for M2 on the same
   ground as V3 accepts the first MVP milestone's page.
2. The protected payload: a program that holds a secret embedded in its
   image and computes an integrity-sensitive result over each request, such
   as a keyed digest, returning it through the response page. The domains
   poll the pages; there is no notification.
3. A minimal, versioned management extension for the untrusted Linux
   domain, the first static slice of Part 6's vocabulary: `pause` and
   `terminate`. A call traps to the HS fast path on the Linux domain's
   hart, which posts it to its ring, raises an IPI to hart 0, and waits in
   HS for the answer, so the call is synchronous from the guest's view and
   bounded by the ring. Hart 0 checks the request against the manifest's
   management grants, which A8 checks against the `domain` rules, and
   either denies and logs it, answering `SBI_ERR_DENIED`, or delivers it
   by IPI to the protected domain's hart; that hart's HS fast path takes
   the IPI while its domain runs, saves the domain's state, records the
   transition in its ring, and parks in HS. Hart 0 then answers the
   caller through the ring it writes for that hart. Whether resuming a
   paused domain maps onto `enter` is M2's plan's decision. Creating
   domains, assigning regions, creating channels, and revoking grants stay
   out.
4. A core-held measurement: before first entry, the monitor computes a
   digest of the protected domain's image and of the configuration identity
   and keeps it in hart 0's monitor-owned memory, which no root maps and
   no domain hart's fast path reads or writes. The monitor logs it at
   launch and at termination; no domain can read or write it, so no new
   permission is needed.
5. Hostile-domain tests from the untrusted Linux domain, running at the
   same time as the protected domain: reads and writes of the protected
   domain's memory, writes to the response page, reads of the secret,
   attempts on the measurement, and unauthorized management calls,
   including a burst of them, each denied and logged, the burst costing
   only the caller's own progress; `terminate` succeeds, is recorded in
   core-held state, parks the protected domain's hart, and leaves the
   measurement unaltered.

**Exit.** In QEMU and in the default board campaign, the protected domain
computes beside the untrusted Linux domain on its own hart; every request
gets the correct result; every hostile attempt is denied and logged; the
measurement equals the offline computation; and termination is detected
in core-held state with the protected domain's hart parked.

**Evidence.** Host tests, emulation, diagnostic bring-up evidence, and the
offline checks. The measurement is local identity, not attestation. The
protection of the sealed state inside HS, which security model v1 leaves as
an open obligation on the first protected-domain milestone, is stated in
M2's plan; this plan does not close it.

### M3. The policy layer in the model, with differential checking

**Goal.** The policy-to-manifest relation proved in the abstract model and
checked by two independent implementations, and the static hart binding
of revision 1 stated and proved in the same model.

**Delivers.**

1. An additive revision of security model v1, as its own exact commit for
   acceptance before any model work: a hart binding, in the `domain` class
   or as a `hart` class, with the invariants revision 1 relies on, which
   that revision numbers: each hart runs at most one domain; each domain
   runs on exactly one hart; per-hart monitor state is private to its
   hart; and the control hart is the only writer of shared monitor state.
   Part 7's inventory is extended by the binding, the per-hart state, and
   the rings as monitor-owned objects, and M2's instance becomes the third
   instance. The revision changes no accepted analysis, instance, or
   claim; it is the one planned change that stop condition 1 admits.
2. The additive changes that security model v1 Part 7 inventories: the
   policy and labeling identities in the configuration identity; new Rocq
   obligations for I10, for I11 (A8 soundness), and for the invariance of
   A6's flow relation under the derived mappings, in a new module;
   Instance 1, Instance 2, and M2's instance as fixtures; and A1 to A6 and
   A8 in the executable model and host checker. To these, revision 1 adds
   obligations for the hart invariants of deliverable 1: the derived
   binding maps domains to harts injectively; each hart's private state is
   disjoint from every other hart's and from every domain's memory; and
   only the control hart's transitions write shared monitor state.
3. Differential checking: the MVP line's offline checker and the model's
   checker run on every instance and on a seeded single-defect mutation
   set (S1 H39) and must agree. Model 0.2's seam and its 23 obligations
   stay unchanged.

**Exit.** The security model revision is accepted at its exact commit; the
model's proof and checks pass with the new module, including the hart
obligations; and the two checkers agree on every instance and every
mutation.

**Evidence.** Proof about the abstract model, and unit tests. It is not C
refinement: the offline checker is not proved to be the model's function,
and the boot barrier, the rings, the IPI protocol, and the implementation's
memory ordering are not modeled. The hart obligations are about the static
binding, not about concurrent execution.

### M4. Release candidate

**Goal.** MVP 1.0 as one exact, reviewed commit, ready for the release
path.

**Delivers.** A researcher guide (build, run in QEMU and on the board,
write a scenario, and read the authority report and an evidence bundle);
the MVP claim with its required limit and forbidden phrasings (S1 H34); the
claim ledger, mapping every claim to its method and evidence; the clean
evidence bundle for the exact commit from the pinned evaluator (S1 H30 to
H32); the AI-assistance disclosure (S1 H47); and a review packet.

**Exit.** Responsible-human acceptance of the exact release-candidate
commit. That acceptance starts no release step.

## Order and dependencies

```text
M0 -> M1 -> M2 -> M4
M0 -> M3 -------> M4
```

M3 depends only on security model v1, the revision it plans, and the
instances, so it may run alongside M1 and M2 once its own plan and that
revision are accepted. Each milestone is useful before the next one
exists (implementation plan L681): M0 gives a pinned, reproducible
two-domain line on three harts with its harness; M1 the first channel and
denial scenario between Linux guests; M2 the anchor demonstration; M3 the
proof of the policy layer and the hart binding; and M4 the release
candidate.

## Evaluation harness

The harness is built in M0 and extended by each milestone. It carries out
S1 hand-off item 2.

| Stage | What it does | Rules |
| --- | --- | --- |
| Scenario | A scenario is data: a policy, a labeling, a manifest, guest programs, and the expected outcomes (accepted exits, denial-log entries, guest reports, and counters) | Nothing selects behavior inside the monitor at run time; negative images are linked separately (S1 H27) |
| Offline checks | A1 to A6 and A8 on the policy and the manifest, and the authority report in the Part 4 schema | A failing check stops the build; A7 waits for a request vocabulary |
| Build | GCC and Clang images from the locked tools | Reject caller overrides, `MAKEFILES`, and `--eval`; accept only exact toolchain values (S1 H33) |
| Run | Host tests; QEMU direct boot and kexec rehearsal with eight harts; RAM-only K3 kexec campaigns from hart 0 with human resets | Board safety unchanged; automation never types at U-Boot |
| Check | Marker and log validators | Exact cardinality within each domain's stream and hart 0's own: each expected line exactly once and in order, and one parser run per file (S1 H26); order across streams only where the scenario declares it; counters exact or within a declared range per scenario; the monitor's denial log reconciled with the guests' reports |
| Evidence | Bundles with a SHA-256 manifest and the tool record | Clean exact-commit evidence kept apart from development runs, and no path recorded in a bundle is ever executed (S1 H30); the evaluator runs from a read-only source mount with hidden build trees, a pinned image digest, no network, and `GIT_OPTIONAL_LOCKS=0` (S1 H31) |
| Mutation | Seeded single-defect mutations of the new checks, each mapped to the claim that must fail (S1 H39) | Run before each milestone's result packet |
| Costs | Per-exit and idle costs, the IPI round trip, and ring latency, as B7 planned to measure its own costs | Recorded only; no performance or side-channel claim |

One stable wrapper command runs the MVP line's stages (S1 H44). The harness
stays small relative to the mechanism it checks (S1 H43): each milestone's
result packet reports the size of the checking code against the size of the
monitor code it checks, and the milestone's plan justifies any growth.

## Evidence claims

### Method per claim

S1 H38 and project review option 4 ask for a verification method per claim.

| Claim | Method | Explicitly not claimed |
| --- | --- | --- |
| The policy semantics is total (I10) | By construction; a Rocq obligation (M3) | |
| The manifest conforms to the policy (I11) | Offline A8 before the build; A8 soundness in Rocq (M3); differential agreement of the two checkers (M3) | That the offline checker is the proved function |
| Each root maps only what the manifest grants, and roots share only declared channels | The boot-time independent re-walk and channel check (M1); host tests | A proof of the B-series or MVP root builder |
| The tested cross-domain accesses are denied, logged, and delivered as faults | QEMU and board runs; negative images; mutations | Containment of arbitrary guests |
| Each root is installed on exactly one hart under its own VMID, once, before its domain runs, and no hart writes `hgatp` after the boot barrier | Boot-time readback on each hart; the image checker's single-writer rule; host tests; M0's VMID probe as a platform fact | VMID tagging correctness on K3 in general; any proof of the MVP boot barrier or entry path; R7's bounded proof covers the accepted R5 single-hart switch bytes only and does not transfer |
| Per-hart monitor state is private to its hart, and only the control hart writes shared monitor state | The hart obligations in Rocq (M3), over the static binding; host tests of the ring and control-loop functions over captured inputs | Any proof of the implementation's rings, IPIs, or memory ordering; freedom from data races in the C |
| Management requests are decided only by the control hart, against the sealed manifest (M2) | Host tests of the decision function; QEMU and board runs; negative images; mutations | Availability of the control hart; any proof of the request protocol |
| The protected domain's secret, result, and measurement resist the tested attacks of the untrusted Linux domain (M2) | QEMU and board runs; negative images | Resistance to every attack; microarchitectural isolation; availability |

The unproved boundary is recorded in the claim ledger: R7's fifteen cut
points stand for the accepted R5 bytes, and the B5-B7 layers and every MVP
addition, now including the boot barrier, the rings, the IPI protocol,
and the control loop, remain unproved (S1 H36, H40). The MVP does not
restructure the B5-B7 layers into the modeled seam (project review option
4). New decision logic, such as the channel check, the injection decision,
the ring protocol, and the management-call check, is written as pure
functions over captured inputs with host tests (S1 H22), which keeps that
restructuring open for a later plan.

### The MVP claim

Draft, fixed in M4:

> In QEMU and on one SpacemiT K3 COM260 board (harts 0 to 2 of eight,
> statically assigned, one control hart and one hart per domain; RAM-only
> load; recorded firmware), the Beryllium MVP runs Linux guests, one per
> hart, in separate G-stage domains whose memory authority is specified
> by a declarative policy in the Type Enforcement family, checked offline
> against the sealed configuration, and enforced through derived mappings.
> In the tested scenarios, every access attempted outside the declared
> channels was denied, logged, and delivered to the offending guest as a
> fault, and a protected domain's secret, result, and measurement were
> neither read nor altered by the untrusted Linux domain running beside
> it.

**Required limit.** This is test, emulation, and diagnostic bring-up
evidence for one board and one firmware build. The policy-to-manifest
relation and the static hart binding are proved only in the abstract
model. Isolation is architectural only. The hart assignment is fixed
before any domain runs; nothing is claimed about migration, overcommit,
dynamic multicore operation, or the harts that are never started, whose
state is a firmware assumption. It is not formal verification, hardware
validation, or certification.

**Forbidden phrasings**, with others that M4 lists: "formally verified" or
"verified hypervisor"; "proven secure", or "secure against a compromised
host" without the required limit; "hardware-validated",
"multicore-validated", or "certified"; "SMP" or "multicore hypervisor"
without "static hart ownership"; "attested" or "confidential computing";
"SELinux, FLASK, or XSM for RISC-V"; any wording that presents TE as a
runtime mechanism Beryllium selected; and any Helium, Model, or R-series
result presented as an MVP result.

## Decisions recorded by this plan

| ID | Open item and its source | Decision (the default unless answered) |
| --- | --- | --- |
| D1 | MVP 1.0 scope, and the first milestone against the anchor use case (S1 open decisions; project review F-08, option 2) | M1 as a step toward M2, both in MVP 1.0 (Q1) |
| D2 | Development kernel/BSP (roadmap; README gate 5) | Not needed: no domain sees a device, and no Linux runs on the bare board under Beryllium |
| D3 | Root integration (roadmap; S1 H33, H44; project review F-11, option 7) | The MVP line is self-contained, with its own wrapper and build controls, outside the root `Makefile`, `be`, and `scripts/check-be.sh`; the build root is designed afresh in the clean-repository migration (Q2) |
| D4 | What replaces R8's characterization (project review F-07, option 3) | No formal K3 evidence package: M0's platform record, which revision 1 extends with the hart, HSM, IPI, ordering, and VMID facts, stated as diagnostic evidence in the MVP claim (Q3) |
| D5 | A richer userland (roadmap; B7 plan) | Not in MVP 1.0; `nolibc` programs |
| D6 | KVM0 | Not recreated |
| D7 | A verification method per claim (S1 H38; project review option 4) | As in "Method per claim"; the model work is M3, which revision 1 extends with the hart obligations and the security model revision they need (Q5) |
| D8 | SBI, exit-surface, and scheduling boundaries (S1 hand-off item 6; H15, H18, H24) | B7's guest SBI subset plus M2's management extension, with one versioning rule: the SBI implementation version increases with every change to the guest-visible SBI surface; an exact accepted-exit set per scenario; no scheduler: static hart ownership, native `wfi`, and no HS time slice (revision 1; D14). The monitor's own firmware SBI surface grows from Base, DBCN, and SRST by HSM and IPI (D15) |
| D9 | The authority report's encoding (security model v1 Part 4) | JSON, with consumption by offline audit tools in the `cheriot-audit` pattern as a compatibility goal |
| D10 | The protected-service use case (decision gate 2) | M2's protected research domain, holding a secret and an integrity-sensitive computation; no service runtime |
| D11 | Open audit findings S5-S8 and S10, and R4's QEMU budget (project review option 7) | Outside MVP 1.0, for separate direction; the MVP's own checkers follow S1 H26 (Q8) |
| D12 | CHERI alignment (project review F-17) | Each milestone plan states its CHERI alignment in one paragraph; no CHERI mechanism |
| D13 | The release path and license (S1 H47, H48) | As in "Release path" (Q6) |
| D14 | The concurrency model for MVP 1.0 (implementation plan Stage 2, L1211-L1220; research L165-L217; revision 1) | The static part of Stage 2: one domain per hart, per-hart fast-path state, and one bounded serialized control path, which is the control hart; no global control lock, dynamic mapping protocol, or fine-grained locking |
| D15 | Cross-hart mechanisms (revision 1) | SBI HSM `hart_start` once per domain hart before the boot barrier; the SBI IPI extension for signalling in both directions; one single-writer, single-reader ring per direction per domain hart, with release and acquire fences and no atomic read-modify-write in the fast path; AIA IMSIC deferred |
| D16 | Hart layout and emulation profile (revision 1) | Hart 0 control, harts 1 and 2 domains, harts 3 to 7 never started (Q12); QEMU with eight harts (Q10); a terminated domain's hart parks in HS (Q11); the run's time budget on hart 0's Sstc timer (Q9) |

## Decisions and guidance this revision departs from

Each applies to the MVP plan only and changes no accepted byte or accepted
document's text.

| # | Accepted decision or recorded guidance | Departure | Accounted for by |
| --- | --- | --- | --- |
| 1 | S1 H57 defers "multiple harts" with Helium's other scaling risks, and this plan's first candidate made a second hart a non-goal and a stop condition | MVP 1.0 uses three harts under static ownership | D14, D16; the dynamic part of multicore stays a non-goal |
| 2 | The research document's guidance that "the initial monitor code should instead execute in HS on every active hart, with private per-hart state and no steady-state global mutation", with its list of what a dedicated control hart adds (L171-L181) | A dedicated control hart from the start | The responsible human's answer `control_hart`; the five added costs are named in [Hart layout](#hart-layout) and carried as risks, and the protocol is recorded as unproved in the claim ledger |
| 3 | The implementation plan's Stage 1, in which "one Linux management vCPU and one protected-domain vCPU may be time-multiplexed for functional bring-up" (L1203-L1209), realized by B7 | No time-multiplexing in the MVP; B7's scheduler stays bring-up history | D8, D14 |
| 4 | Security model v1's object classes have no hart, and its invariants I5 and I7 are stated for switches between domains on one hart | A planned additive revision in M3 adds the hart binding and its invariants; I5 and I7 apply to each hart's single entry and to M2's `pause` and `terminate` | M3 deliverable 1; stop condition 1 |

## Release path

Each step needs its own explicit responsible-human instruction, and none
follows from accepting this plan or M4 (S1 H48; `LLM_POLICY_ALIGNMENT.md`).

1. M4's exact release-candidate commit is accepted.
2. The responsible human selects the source, artifacts, and history that
   migrate.
3. A new clean public Beryllium repository is created and populated with
   only that reviewed material; automation does neither without explicit
   authorization.
4. The gates run again in the clean repository, and the result is a new
   exact commit for review.
5. The responsible human approves that exact public commit and its tag;
   any later source change invalidates the approval.
6. Publication to the community venues that the implementation plan names:
   the problem statement, the results, and an invitation to review.
7. The internal repository is archived when the responsible human decides.

The license for the public research release is GPL-3.0-only, as today. Any
upstream or in-tree submission needs a separate licensing and provenance
decision under the license boundary. Helium material is not part of the
MVP release; if a later decision includes it, Helium's own publication gate
applies. Every release surface discloses AI assistance, and no automation
adds a human `Signed-off-by`, approves a release, or edits
`pathfinder/publication-gate.conf`. Publishing a problem statement before
MVP 1.0, as the community strategy suggests, is also a publication step
and needs its own instruction.

## Stop conditions

Each returns this plan, or the milestone in progress, to the responsible
human.

1. Any need to change an accepted R0-R7 or B0-B7 byte or an accepted
   document's text, other than the additive security model v1 revision
   that M3 plans, which goes to the responsible human as its own exact
   commit.
2. A K3 observation that contradicts a planned claim or design input, such
   as `htval` or `htinst` values that do not support the alias-rejecting
   comparison; an HSM `hart_start` that fails, or a hart that does not
   reach the monitor's entry after kexec; an IPI not delivered to HS while
   a domain runs; a flag-and-payload ordering that fences do not make
   coherent between the layout's harts; or a domain hart's Sstc timer that
   does not behave as hart 0's does.
3. Any milestone that needs a hart beyond the layout, a domain on more
   than one hart or more than one domain on a hart, a hart started or
   stopped after the boot barrier, a lock held across guest execution or
   an untrusted-domain call, a device, an IOMMU, DMA, or guest-visible
   interrupt injection beyond each domain's own timer.
4. A scenario that fires the capability trigger or the runtime-check
   trigger, or that needs dynamic management beyond M2's management calls.
5. A tool lock that the development host cannot satisfy with open tools.
6. Checking machinery that grows beyond what the milestone's plan
   justifies (S1 H43).
7. Any push, publication, repository creation, release, or archive step
   without its explicit instruction.

## Risks

| Risk | Response |
| --- | --- |
| M2 grows into implementation-plan milestone 3: a Linux management domain with a dynamic vocabulary, notifications, and lifecycle | M2 stays static; anything beyond its management calls is stop condition 4 |
| K3's fault reporting does not support the planned injection | M0 records `htval` and `htinst` first; stop condition 2 |
| Evidence machinery outweighs the mechanism (project review F-15) | The harness rules; stop condition 6 |
| Diagnostic board runs are read as validation | The MVP claim's required limit and forbidden phrasings |
| One board and human resets bound the campaigns | Board campaigns as in B7; QEMU carries the broad matrix |
| The tool lock fails on the development host, as the R6 and R7 locks do | The lock is designed for the development host from the start (project review option 7) |
| The release stalls on licensing or provenance | GPL-3.0-only for the research release; upstream licensing decided separately |
| The B5-B7 and MVP layers stay unproved | Recorded as the unproved boundary; a later plan may restructure them (S1 H22) |
| Starting a second hart is new to Beryllium, and HSM `hart_start` after a Linux kexec, with harts 1 to 7 HSM-stopped by Linux, may not behave as on a cold boot | M0 owns the substrate, records the HSM state and each start result first, and rehearses in QEMU before the board; a defect returns M0 under stop condition 2 |
| Cross-hart ordering that holds on QEMU's TCG passes on the board by luck | Single-writer rings with release and acquire fences; M0's ordering probe on the layout's harts; repeated scenario runs; no RVWMO claim |
| The control hart is an availability dependency and a target for request floods, as the research document warns (L171-L178) | Synchronous, ring-bounded requests cost only the caller's progress; availability is outside the claim |
| QEMU's multi-hart timing differs from the board's, so emulation under-tests races | The board campaign carries the timing evidence; QEMU carries the matrix |
| Console output from three harts interleaves and hides a missing line | Only hart 0 writes the console, draining the rings in order with per-domain prefixes; exact cardinality per stream |

## Open questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | What does MVP 1.0 contain? | M0 to M4: the TE PoC scenario (M1) as a step toward the static protected domain (M2) | Stop at M1 and leave M2 to a later plan; or go straight to M2 |
| Q2 | Root integration? | A self-contained MVP line; the build root is designed in the clean-repository migration | Integrate into the root build now, with one pins manifest replacing the six embedded constants |
| Q3 | K3 evidence beyond the B-series? | M0's platform record and M1's VMID characterization, as diagnostic evidence | Recreate a bounded R8-style characterization package before M1 |
| Q4 | M2's protected payload and channel form? | The pinned Linux guest with a `nolibc` program; two static single-writer pages, polled; no notification | A bare-metal payload in B5's style; or a notification, which needs interrupt injection (stop condition 3) |
| Q5 | Is the model work (M3) in MVP 1.0? | Yes | Defer M3 until after MVP 1.0 |
| Q6 | What does "release" mean for MVP 1.0? | A public release through a new clean repository, each step separately authorized; GPL-3.0-only | A private release to named collaborators first |
| Q7 | Independent review? | None beyond the responsible human's exact-commit reviews, per the 2026-10-06 SOP | One independent review of M4's release candidate (project review option 5) |
| Q8 | Open findings S5-S8 and S10, and R4's budget? | Outside MVP 1.0 | Fix them in M0 |
| Q9 | Does hart 0 keep the run's time budget? | Yes, on hart 0's own Sstc timer, ending the run as B7's budget did | Each domain hart keeps its own budget; or no budget on the board |
| Q10 | How many harts in the QEMU profile? | Eight, mirroring the board, with harts 3 to 7 never started | Three |
| Q11 | How does a terminated domain's hart end? | It parks in HS, in `wfi`, for the rest of the run | SBI HSM `hart_stop`, a firmware call after the barrier |
| Q12 | Which physical harts? | 0, 1, and 2 as the device tree numbers them; M0 records each hart's cluster, and the choice stands unless M0's ordering probe fails on it | Choose the domain harts by cluster once M0 records the topology |

## What acceptance authorizes

Accepting this exact commit would select M0 to M4 in the order above,
record D1 to D16 with the defaults or the answers given, supersede
`06c35f48`, and authorize writing M0's bounded plan, which now includes
the static multi-hart substrate, on a new branch from the development
branch. It would authorize no implementation, hart start, board run,
accepted-byte change, model change, security model revision, push,
publication, or release step.

## Status record

```text
s3_status=accepted
s3_plan_target=93967fbac926b4fdfdfe636df4d07e8926b625b7
s3_acceptance_instruction=accept-93967fba
s3_acceptance_date=2026-10-23
s3_open_questions=Q1-Q12-defaults
s3_revision=1
s3_revision_date=2026-10-23
s3_revision_request=one-hart-per-guest-and-a-control-hart
s3_superseded_candidate=06c35f4829f14b4896a5cc46dee77ed8bee0ef9d
s3_direction_instruction=merge-and-push-start-S3
s3_direction_date=2026-10-22
s3_base=0096de3e063ae19fd7ba6d2ac157af780176b10f
s3_input_security_model_v1=0e3eec8b4fd74003f8cedbf2ca66871c31412624
s3_input_s1=fd670dcd54ff4f2c66349d377be914698b9dda3b
s3_input_m01a=95ef0f6c0fc1fe457e93b7d34b48cde5a411e8ab
s3_input_project_review=480dab72de7a74f8b84c64c2fefee8190cb87b70
s3_milestones=M0,M1,M2,M3,M4
s3_first_mvp_milestone=M1-te-poc-two-linux-guests
s3_anchor_milestone=M2-static-protected-domain
s3_concurrency=static-hart-ownership-with-control-hart
s3_hart_layout=hart0-control,hart1-domain,hart2-domain,harts3-7-never-started
s3_scheduler=none
s3_cross_hart=sbi-hsm-start,sbi-ipi,single-writer-rings
s3_qemu_harts=8
s3_model_hart_obligations=M3
s3_security_model_v1_revision=planned-in-M3-not-made
s3_root_integration=self-contained-mvp-line
s3_development_kernel_bsp=not-needed
s3_formal_k3_package=not-recreated
s3_kvm0=not-recreated
s3_richer_userland=not-in-mvp
s3_report_encoding=json
s3_release=clean-public-repository-each-step-authorized
s3_license=GPL-3.0-only
s3_authorization=m0-bounded-plan-only
mvp_implementation_authorization=none
```

## Plan revision S3-A: boot from system reset, the board policy, M5, and release-candidate staging

**Decision record.** The responsible human accepted this revision at
exact commit `0d134bbc49377576b961989831a02c068b479355` (parent
`6a5f6fed`, on branch `beryllium/mvp-m5-plan`) on 2026-10-29 by the
instruction `accept 0d134bbc and 066794d, authorize m5`, the first of the
two ordered decisions the [M5 plan review and acceptance record](mvp-m5-plan-review-summary.md)
presented; the same instruction accepted the [M5 plan](mvp-m5-plan.md)
at `0066794d` and authorized M5. Acceptance covers exactly the revision's
text at that commit; the status paragraph below is the pre-decision text
as presented, and only this paragraph and the status-record addendum's
acceptance fields were set afterwards. The accepted plan's own status
record above is not edited: its `s3_milestones` and `s3_authorization`
lines are superseded by the addendum, as the superseded-lines table says.

**Status as presented: directed, not yet accepted at an exact commit.** On 2026-10-29,
after accepting MVP 1.0 release candidate 1 (exact commit `c5df0cfa`,
[M4 result review and acceptance record](mvp-m4-result-review-summary.md)),
the responsible human asked `clarify if this mvp target is kexec based or
boots up via opensbi from system reset`, was told that every board run of
M0 to M4 was a Linux `kexec_load` from the board's running Fedora under
the resident OpenSBI and never a boot from reset, and directed: `modify
the plan so that the mvp candidate boots from system reset. I don't know
where those safety rules came from.` In two question rounds the same day
the human chose the mechanism (a dedicated partition on the board's NVMe,
not an SD card; U-Boot's saved environment changed within a recorded work
session and restored at its end; a script, run by the human, creates the
partition), automation typing at U-Boot through the operator's picocom
session with every keystroke recorded, the removal of kexec from the board
tools and the claim, a new milestone with the MVP staged as release
candidates, image selection by one `saveenv` per image group, and a U-Boot
rehearsal in QEMU in place of the kexec rehearsal. The human then set the
standing rule `no more kexec unless I approve it`, and clarified it with
`no more kexec means don't use this from here, unless it is truly needed
for something. use p3. make soft limit 5000. proceed.` This revision
records those directions in the MVP plan. It changes no accepted R0-R7 or
B0-B7 byte, no accepted document other than this plan, and nothing of M0
to M4's accepted texts, which stay as the history of how those milestones
ran. The exact commit carrying it is presented for acceptance with the
[M5 plan](mvp-m5-plan.md) as two ordered decisions. Line references are
to this document at `6a5f6fed`.

### Where the rule came from

*Fact.* The "board safety boundary" (RAM-only loading by Linux kexec or an
interactive U-Boot `booti`, output-only serial capture, no persistent
firmware, U-Boot environment, flash, or boot-configuration change, and
human-performed resets) first appears in `bringup/k3-b0/README.md` in the
commit that added B0's board tooling (`62060e2d`, 2026-10-06), written by
the automation as its own working rule for a board it was about to use
for the first time. Every later plan inherited it: B1 to B7's board
sections, M0's "Board safety and procedure", M1's `k3ctl` reset decision,
and this plan's Scope bullet (L205-L208) and harness "Run" row (L553).
No instruction of the responsible human asked for it, and the board's own
saved U-Boot environment was already the human's custom one (the board
autoboots Fedora 45 from NVMe, which the BSP's shipped environment does
not do). The rule served its purpose: it let bring-up proceed without a
decision the human had not been asked for. It is now replaced by a policy
the human has decided.

### S3-A.1 The board policy

From this revision, board work under the MVP plan follows this policy in
place of the inherited boundary. Each milestone plan restates what it
uses of it and may narrow it, never widen it.

1. **Boot from reset.** The MVP's board evidence comes from boots from
   system reset: the board's resident firmware (SPL, OpenSBI, U-Boot in
   the QSPI NOR) runs, U-Boot's saved environment loads the MVP image
   from one Beryllium partition on the board's NVMe, and `booti` enters
   the shim. Linux on the board is used only to stage images and to run
   read-only preflight checks, never to launch the MVP.
2. **kexec is not used.** The responsible human's rule of 2026-10-29,
   `no more kexec unless I approve it`, clarified as `don't use this from
   here, unless it is truly needed for something`: Beryllium's tools and
   procedures do not use kexec from here on. If a later step truly needs
   it, the need is stated to the responsible human and the use waits for
   their approval. The retained kexec tools under `bringup/` and the
   kexec records of B0 to B2, B5 to B7, M0 to M2, and release candidate 1
   are history, neither deleted nor re-run; re-judging a retained capture
   with a checker is a read-only test, not a use.
3. **The NOR firmware is never written.** No step writes SPL, OpenSBI,
   U-Boot, or U-Boot's environment partition, except that U-Boot's saved
   environment is changed by `saveenv` within a recorded work session and
   restored at its end: the environment is recorded at a fresh prompt
   before the session, every change is a declared variable with a `be_`
   prefix or the `bootcmd` line that runs them before the human's own
   boot command, and the restore returns the human's `bootcmd` byte for
   byte and removes every `be_` variable, with the printed environment
   compared to the pre-session record under the rule the milestone plan
   states. `env default`, `env erase`, and every flash, MTD, or firmware
   write command are never typed.
4. **One Beryllium partition.** Images live on one ext4 partition
   labelled `beryllium`, created once by the responsible human with a
   tool the plan delivers (dry run by default; the human names the
   source partition; backups before any write). No other partition, the
   UFS, `env_k3.txt`, or the human's boot files are written.
5. **Resets** are the opt-in `k3ctl` reset or the human's; U-Boot's
   `reset` and `boot` are not typed. Every boot the session records maps
   to a recorded reset.
6. **Typing at U-Boot** is done by automation through the operator's
   picocom session, from a fixed set of line templates with every
   keystroke and prompt recorded in the campaign record, or by the human.
   The human is present for the environment's install and restore and
   for any recovery.
7. **Privacy.** Environment records that leave the board are kept
   private; the repository holds hashes, the `be_` names and values, and
   verdicts, under the milestone plan's rule.

### S3-A.2 Milestone M5: release candidate 2, boot from system reset

**Goal.** MVP 1.0 as one exact commit whose board evidence is made by
boots from system reset under the policy above, with kexec removed from
the MVP line's board tools and claim.

**Delivers.** The board tools for the new path (a console tool for the
templated U-Boot typing; staging, environment, run, and campaign tools;
the capture checker's `uboot` mode; the partition tool); a U-Boot
rehearsal in QEMU (OpenSBI, a real U-Boot, `booti` of QEMU-only images
that differ from the board images only in the header's `text_offset`)
replacing the kexec rehearsal; the kexec loader, its test, its rehearsal,
and the load check removed, with the read-only platform probe kept; the
claim's board clause, the guide, the disclosure, the ledger, and the
walkthrough rewritten for the new path; a characterization of the board
from a cold boot; one board campaign under the policy; the clean gates;
and a review packet.

**Exit.** Responsible-human acceptance of the exact release candidate 2
commit. That acceptance starts no release step.

M5 follows M4 in the order:

```text
M0 -> M1 -> M2 -> M4 -> M5
M0 -> M3 -------> M4
```

### S3-A.3 Release-candidate staging and the release path

The MVP is staged as release candidates. Release candidate 1 is exact
commit `c5df0cfa`, accepted on 2026-10-29 with its kexec-launched board
evidence; it stays accepted history and is not reopened. Release
candidate 2 is M5's result. The [release path](#release-path)'s step 1,
"M4's exact release-candidate commit is accepted", is restated as "the
latest release candidate's exact commit is accepted"; step 1 is satisfied
by release candidate 1 today and will be by release candidate 2 when it
is accepted. No release step proceeds from either candidate without its
own instruction, as before.

### S3-A.4 Decision D17 and the standing rule

| ID | Open item and its source | Decision |
| --- | --- | --- |
| D17 | The MVP's board launch path (this revision; the human's direction of 2026-10-29) | Boot from system reset under the board policy of S3-A.1: resident firmware and U-Boot, one Beryllium partition on the NVMe, a `be_`-prefixed environment installed for a recorded session and restored, `k3ctl` or human resets, templated and recorded U-Boot typing. kexec is not used (policy item 2). The claim's board clause changes accordingly; the M5 plan fixes its text |

The standing rule of policy item 2 applies to every later plan under
this document and is also recorded in `.github/copilot-instructions.md`
and `planning/HANDOFF.md`.

### Accepted lines this revision supersedes

| Where (at `6a5f6fed`) | Accepted text | Under this revision |
| --- | --- | --- |
| Scope, L205-L208 | "RAM-only loading through Linux kexec from hart 0 as in B7, with human resets … The B-series board-safety rules stand unchanged." | Boot from system reset under the board policy; the B-series rules are history |
| Milestones, L264-L265 | "The defaults below for board campaigns follow B7: three GCC runs and one Clang run, RAM-only, on the COM260." | Three GCC and one Clang run per scenario stand; "RAM-only" becomes "booted from reset under the board policy" |
| Harness "Run" row, L553 | "QEMU direct boot and kexec rehearsal with eight harts; RAM-only K3 kexec campaigns from hart 0 with human resets … Board safety unchanged; automation never types at U-Boot" | QEMU direct boot and the U-Boot rehearsal with eight harts; K3 campaigns booted from reset with `k3ctl` or human resets; the board policy; automation types at U-Boot from templates, recorded |
| Stop condition 2, L699 | "a hart that does not reach the monitor's entry after kexec" | "after the boot path in use" |
| Risks, L724 and L728 | "One board and human resets bound the campaigns … Board campaigns as in B7"; "HSM `hart_start` after a Linux kexec, with harts 1 to 7 HSM-stopped by Linux, may not behave as on a cold boot" | One board bounds the campaigns; `k3ctl` resets and unattended boots from reset make a campaign about one hour; the cold-boot HSM start is M5's characterization and first board test, a defect returning M5 under stop condition 2 |
| Release path step 1, L663 | "M4's exact release-candidate commit is accepted." | "The latest release candidate's exact commit is accepted." |
| Order and dependencies, L529-L532 | `M0 -> M1 -> M2 -> M4` | M5 after M4, as in S3-A.2 |
| The MVP claim draft, L596; the accepted claim's clause "RAM-only load through Linux kexec from the board's Fedora host" (`mvp/docs/claim.md` L11-L12, fixed by the M4 plan's Q6) | "RAM-only load" | The M5 plan's board clause; changing the claim is the plan revision M4's Q6 requires, and this is it together with the M5 plan |
| "What acceptance authorizes", L753, and `s3_milestones` | "M0 to M4" | M0 to M5 |

Every other line of the accepted plan stands. D1 to D16 are unchanged;
D16's hart layout and emulation profile apply to M5 as to M4. The
soft-limit and stop-condition rules of the milestone plans are
unchanged; M5's own limits are in its plan.

### Consequences

- Nothing of M0 to M4 is re-run or re-accepted. Their records remain the
  evidence they were, labelled with the launcher they used.
- The MVP line's `mvp/` tree changes only under the M5 plan after its
  acceptance; this revision changes no file but this one.
- The partition tool, `mvp/tools/k3-make-partition.sh`, is delivered with
  the M5 plan for the human to review and run; its one `--apply` run on
  the board is the human's, before any M5 board command.
- The `.github/copilot-instructions.md` "Board safety for B0 runs" text
  and the board lines of every accepted plan are superseded as rules by
  the board policy and stay as history.

### Status record addendum

```text
s3_revision_s3a=accepted
s3_revision_s3a_target=0d134bbc49377576b961989831a02c068b479355
s3_revision_s3a_acceptance_instruction=accept-0d134bbc-and-066794d-authorize-m5
s3_revision_s3a_acceptance_date=2026-10-29
s3_revision_s3a_acceptance_record=mvp-m5-plan-review-summary.md
s3_revision_s3a_direction_date=2026-10-29
s3_revision_s3a_direction=modify-the-plan-so-that-the-mvp-candidate-boots-from-system-reset
s3_revision_s3a_standing_rule=no-more-kexec-unless-approved
s3_revision_s3a_milestones=M0,M1,M2,M3,M4,M5
s3_revision_s3a_release_candidates=rc1-c5df0cfa-accepted-history,rc2-3867c66c-accepted-2026-10-30
s3_revision_s3a_board_policy=boot-from-reset,no-kexec,nor-never-written,saved-env-session-restored,one-partition,k3ctl-or-human-resets,templated-recorded-typing
s3_revision_s3a_partition_source=p3-human-choice
s3_revision_s3a_m5_soft_limit=5000
s3_revision_s3a_m5_plan=accepted-0066794d-2026-10-29
s3_revision_s3a_authorization=M5-implementation-on-beryllium/mvp-m5
s3_revision_s3a_m5_result=accepted-3867c66c5df2108e1051d8f8c44c12d62611e485;parent-X2-6dd81ee39dd620a1815605c50c9c916894c9974c;2026-10-30;instruction-accept-3867c66c;record-mvp-m5-result-review-summary.md
s3_revision_s3a_release_path=step-1-holds-for-rc2-3867c66c;steps-2-7-not-started-each-needs-instruction
```

## Plan revision S3-B: release candidate 3 and milestone M6, the MVP core profile

**Decision record.** The responsible human accepted this revision at
exact commit `f8b77ac94fc6b5a80e68e6a972fa353b800d068b` (parent
`cd9cfa5f`, on branch `beryllium/mvp-m6-plan`) on 2026-10-30 by the
instruction `accept f8b77ac9 and f8b77ac9`, the first of the two ordered
decisions the [M6 plan review and acceptance record](mvp-m6-plan-review-summary.md)
presented; the same instruction, with the form answer
`accept-and-authorize` for the second decision, accepted the
[M6 plan](mvp-m6-plan.md) at `b2c62d54` and authorized M6. Acceptance
covers exactly the revision's text at that commit; the status paragraph
below is the pre-decision text as presented, and only this paragraph and
the status-record addendum's acceptance fields were set afterwards.

**Status as presented: directed, not yet accepted at an exact commit.** On
2026-10-30, the day release candidate 2 (exact commit `3867c66c`,
[M5 result review and acceptance record](mvp-m5-result-review-summary.md))
was accepted, the responsible human reviewed the project's position
([project snapshot](project-snapshot-mvp-1.0-rc2.md)) and chose, of the two
routes the snapshot states, release candidate 3 before the release path's
steps 2 to 7 (`we will go with RC3 first`): the "MVP core profile" debt
is to be retired under its own bounded plan and its result presented as
release candidate 3. This revision records that direction in the MVP plan.
It changes no accepted R0-R7 or B0-B7 byte, no accepted document other
than this plan, and nothing of M0 to M5's accepted texts. The exact
commit carrying it is presented for acceptance with the
[M6 plan](mvp-m6-plan.md) as two ordered decisions. Line references are
to this document at `cd9cfa5f`.

### S3-B.1 The debt and why it comes first

M0 Plan revision M0-A.5 records the debt: the frozen R0 inventory and the
accepted R1-R3 validation describe the accepted single-hart core only;
the MVP pool, the hart region, the MVP region, the guest windows, and the
shared pages are MVP-owned extents validated by the MVP line's own
`ASSERT`s, image checker, and boot-time checks, not by R1-R3; the MVP
grows around a frozen synthetic core whose fixture roots and pages it
builds and never uses. The roadmap's "Later phases" row defers its
retirement to "after MVP 1.0 or with the clean-repository build root",
and S1 H22 names the shape the retirement should take (pure decision
functions over captured inputs, one executor for privileged effects).
The human's reasons for doing it before publication: it is the one known
structural debt in the monitor; it is bounded; the first public commit
should not carry it; and a board re-run is now cheap under S3-A's boot
from reset. Doing it first also makes release candidate 3, not a later
commit, the proof target the snapshot's verification route needs.

### S3-B.2 Milestone M6: the MVP core profile

**Goal.** The monitor's boot validates, seals, and derives the MVP's real
configuration (the control hart and the domain harts; the monitor's code
and data, the pool, the hart region, the MVP region, the staging area, the
domain windows, and the shared pages; each domain's authority over them)
through the accepted R1 mechanism, ported and widened, in place of the
frozen fixed profile; the derived mappings drive the MVP's Sv39x4
builder; the fixture roots, the fixture pages, and the single-hart
prelude steps the control hart does not need (the HS/VS state check, the
binding, and the control hart's `hgatp` publication) are gone; the flat
image no longer carries the accepted B2 layout as its first `0x34000`
bytes; and the privileged effects are gathered behind one executor with
the proof-bearing subset named (S1 H22, the snapshot's stage 0). Every
scenario, negative, probe, checker, rehearsal, and board tool follows; the
release surfaces say what changed. The [M6 plan](mvp-m6-plan.md) bounds
it.

**Exit.** Responsible-human acceptance of the exact release candidate 3
commit, made as M4 and M5 made theirs: the gates from a clean checkout at
the candidate tree, the board campaign at its images under the S3-A board
policy, the records, the ledger rows, the evidence record, and the packet.

### S3-B.3 Release-candidate staging

Release candidate 1 (`c5df0cfa`) and release candidate 2 (`3867c66c`) are
accepted history and are not reopened. Release candidate 3 is M6's
result. The [release path](#release-path)'s step 1, "the latest release
candidate's exact commit is accepted" (S3-A.3), is satisfied by release
candidate 2 today and will be by release candidate 3 when it is accepted;
the human's direction is that steps 2 to 7 wait for release candidate 3.
No release step proceeds from any candidate without its own instruction,
as before.

### S3-B.4 Decision D18

| ID | Open item and its source | Decision |
| --- | --- | --- |
| D18 | When the MVP core profile debt is retired (M0 Plan revision M0-A.5; the roadmap's "Later phases"; the snapshot's two routes) | Before the release path's steps 2 to 7, as milestone M6 and release candidate 3 (the human's direction of 2026-10-30, `we will go with RC3 first`); the clean-repository build root stays a migration-step design (D3) |

### Accepted lines this revision supersedes

| Where | Accepted text | Now |
| --- | --- | --- |
| M0 Plan revision M0-A.5 (`mvp-m0-plan.md`) | "as its own bounded plan after MVP 1.0 or with the clean-repository build root" | the bounded plan is the M6 plan, before the release path's steps 2 to 7 (D18); the M0 text stays as history |
| Roadmap, "Later phases", "MVP core profile" | "Not before MVP 1.0, or with the clean-repository build root" | M6, release candidate 3 |
| S3-A.3, L946-L949 | "step 1 is satisfied by release candidate 1 today and will be by release candidate 2 when it is accepted" | by release candidate 2 today, by release candidate 3 when accepted (S3-B.3) |

### Consequences

- Nothing of M0 to M5 is re-run or re-accepted; their records remain the
  evidence they were.
- The MVP line's `mvp/` tree changes only under the M6 plan after its
  acceptance; this revision changes no file but this one.
- The claim's text is not changed by this revision; whether M6 changes a
  release surface is the M6 plan's to say, and a claim change would be
  its own stop (the M6 plan's stop conditions).
- The board policy of S3-A.1 and the standing rule of S3-A.4 apply to
  M6's board campaign unchanged.

### Status record addendum

```text
s3_revision_s3b=accepted
s3_revision_s3b_target=f8b77ac94fc6b5a80e68e6a972fa353b800d068b
s3_revision_s3b_acceptance_instruction=accept-f8b77ac9-and-f8b77ac9
s3_revision_s3b_acceptance_date=2026-10-30
s3_revision_s3b_acceptance_record=mvp-m6-plan-review-summary.md
s3_revision_s3b_direction_date=2026-10-30
s3_revision_s3b_direction=we-will-go-with-RC3-first
s3_revision_s3b_milestones=M0,M1,M2,M3,M4,M5,M6
s3_revision_s3b_release_candidates=rc1-c5df0cfa-accepted-history,rc2-3867c66c-accepted-history,rc3-89ef04e9-accepted-2026-10-31
s3_revision_s3b_m6_plan=accepted-b2c62d54-2026-10-30
s3_revision_s3b_authorization=M6-implementation-on-beryllium/mvp-m6
s3_revision_s3b_decision=D18-core-profile-before-release-path-steps-2-7
s3_revision_s3b_m6_result=accepted-89ef04e9354c08ebadbaeb88d553c5081a00b84d;parent-X3-ebc49a889273c811836c3d39fb0fc9bfe808be4c;2026-10-31;instruction-accept-89ef04e9-proceed;record-mvp-m6-result-review-summary.md;evidence-mvp-m6-evidence.md
s3_revision_s3b_core_profile_debt=retired-by-M6-at-89ef04e9
s3_revision_s3b_release_path=step-1-holds-for-rc3-89ef04e9;steps-2-7-not-started-each-needs-instruction
```

## Plan revision S3-C: the MVP ladder, and MVP 1.0 widened to interactive guests, a first verification plan, and measurement

**Decision record.** The responsible human accepted this revision at
exact commit `27d2e557f069edf8dd714f5ac9b5ccb9b204a801` (parent
`81c5e0b6`, on branch `beryllium/mvp-s3c-plan`) on 2026-11-01 by the
instruction `note that from now on, we will push changes for the rc3 snapshot as normal deltas, so people can see what is changing. accept 27d2e557, defaults ff + push/` (the trailing `/` a stray key), the reply to the
[S3-C packet](mvp-plan-s3c-review-summary.md)'s request, with Q27 to Q46
at their defaults (`defaults`). Acceptance covers exactly the revision's
text at that commit: D19 to D22, the amended stop condition 1, S3-A.1
item 8, the superseded lines, and Q27 to Q46 at their defaults; it
authorizes writing the bounded plans of M7, M8, and M9, each on its own
branch from the development branch, and M10's after those three
milestones' results are accepted, and nothing else. The status paragraph
below is the pre-decision text as presented, and only this paragraph and
the status-record addendum's acceptance fields were set afterwards. The
same instruction fast-forwards the development branch to the commit
recording the decision and pushes it, and gives a standing direction on
the public review snapshot (changes pushed as normal deltas from now on;
`mvp/README.md`, item 107).

**Status as presented: directed; second candidate, not yet accepted at an
exact commit.** The first candidate, exact commit `95c9ab24`, was read by
three independent design reviews under the same brief (section 8 of the
[S3-C packet](mvp-plan-s3c-review-summary.md)): the Copilot CLI session's
own ([report](mvp-plan-s3c-review-copilot-cli.md)), a Codex CLI session's
([report](mvp-plan-s3c-independent-design-review.md)), and a Claude Code
session's ([report](mvp-plan-s3c-review-claude-code.md)). Their findings
are mapped, verified, and adjudicated in the
[reconciliation](mvp-plan-s3c-review-reconciliation.md), whose rows A to
AQ this candidate answers; the first candidate is superseded and was
never accepted. The responsible human directed the processing of the
reviews on 2026-11-01 (`also now process the claude cli and codex reviews
and iterate as appropriate`).

Release candidate 3 (exact commit `89ef04e9`, accepted 2026-10-31,
[M6 result review and acceptance record](mvp-m6-result-review-summary.md))
is the latest accepted candidate. The public review snapshot
(`mvp/README.md`, "The refreshed RC3 snapshot") is a fresh-history copy
of an accepted commit of the development branch, not of release
candidate 3's exact commit: its public `main` `1ae5fd8c` is a snapshot of
`3fe427b7` (release candidate 3 with its accepted follow-ups, no monitor
or claim change), and the human's local clone is refreshed from
`b53c02a8` (debt sweep 3 accepted) for the human's own push. On
2026-10-31 the responsible human directed, in order: `because we have a
review release published, we can take a bit more time if needed to get
to a useful MVP 1.0. make the one page comparison`; then, after reading
the [comparison](post-rc3-candidates-2026-10-31.md), the shape of an MVP
ladder (MVP 1.0 "something useful", 2.0 "finalize core architecture and
formalize", 3.0 "composition and extension", 4.0 the general-guest work),
with `we want to measure and attest, but start with measurement`, `we are
not using IMA ever`, a simulated hardware root of trust for the proof of
concept, a look at systemd's measured-boot work and Amutable's where
applicable, and an analysis of LiteBox for MVP 2.0; and finally that,
once this revision was written, a separate review by a different agent
would produce a report as steering input (three did). This revision turns
those directions into plan text. It changes no accepted R0-R7 or B0-B7
byte, no accepted document other than this plan, and nothing of M0 to
M6's accepted texts. Line references to the accepted body are to the
development branch at `8b7559d2`, whose plan text is unchanged at
`b53c02a8`.

### S3-C.1 Why MVP 1.0 widens, and the naming this revision fixes

Release candidate 3 is the accepted MVP plan complete: M0 to M6 are
accepted, the core-profile debt is retired, and the release path's step 1
holds. What a researcher gets from it is bounded in a way the comparison
states on its first page: the three scenarios run in QEMU and on a
COM260, the authority report and the claim ledger can be read, a scenario
can be written; but nothing can be typed into a guest (the guest kernel's
SBI console driver polls `sbi_debug_console_read` and the monitor answers
`SBI_ERR_DENIED`, `mvp/src/mvp-sbi.c` L416-L418), the guests are `nolibc`
programs in an initramfs, and nothing is proved about the monitor's C
beyond host tests and checkers. The public snapshot removes the pressure
to publish that state as "MVP 1.0": the human's direction is to spend the
time a useful 1.0 needs. The snapshot can be refreshed from an accepted
commit on the human's instruction meanwhile (D21).

"Useful" was read three ways in the comparison: to show, to build on, and
to trust. MVP 1.0 takes the first and the third, bounded, and adds
measurement as evidence plumbing: it is a **security-research
demonstrator**, useful to show the isolation mechanisms live and useful to
inspect their bounded evidence; it is not a workload platform (static,
device-less, unable to run a networked or persistent guest), and
dynamic management ("to build on") moves to MVP 2.0 (Q33). D19 names
that meaning. Concretely, a researcher with MVP 1.0 can:

1. build and boot a named configuration, type into a guest, and
   deliberately exercise the writer/reader channel and the paired denial
   evidence (M7);
2. drive the untrusted side of `anchor` while the protected domain keeps
   its narrow interface and known computation (M7, Q27);
3. change an authorized scenario or policy input and see either an
   offline refusal or the corresponding change in authority and
   behaviour, without editing the trusted core (as today);
4. inspect a first source-bound result about the monitor's own C, positive
   or negative (M8), and a launch-evidence record whose assumptions,
   observations, and expected values are kept apart (M9).

Scripted sessions are the evidence; a live session is a demonstration,
not evidence (S3-C.3).

The naming from here on, so that the plans, the roadmap, and the reviews
use one vocabulary:

| Term | Meaning |
| --- | --- |
| S3-A, S3-B, S3-C | Revisions of this plan, appended as sections with their own decision records |
| M7, M8, M9, M10 | The milestones this revision adds to MVP 1.0 (below); each gets its own bounded plan, as M0 to M6 did |
| RC1, RC2, RC3, RC4 | The release candidates; RC1 to RC3 are accepted history; RC4 is M10's result |
| MVP 1.0, 2.0, 3.0, 4.0 | The ladder (S3-C.2); each later rung is named here and planned later by its own revision or plan |
| The three scenarios | `two-guests` (M0; the policy-free control), `te-poc` (M1; security model v1's Instance 2), and `anchor` (M2; Instance 3, with the protected domain) |
| The review snapshot; the project snapshot | Two different things: the public fresh-history copy of an accepted commit (`mvp/tools/snapshot.sh`), and the dated overview document [`project-snapshot-mvp-1.0-rc2.md`](project-snapshot-mvp-1.0-rc2.md), whose section 8 lists the verification stages 0 to 5 that S3-C.4 cites |
| Implementation-plan milestone N | A milestone of the [implementation plan](implementation-plan.md) (3 dynamic management, 4 dynamic multicore, 5 devices and the I/O service domain, 6 the policy substrate, 7 measured launch and attestation, 8 Arm, 9 the assurance release, 10 upstream); never an MVP milestone, which is written MN |
| S1 H rows | Rows of the [Helium-to-Beryllium synthesis](he-to-be-synthesis.md): H06 and H07 (policy aggregation and authority without a mapping; permission semantics), H08 and H09 (the capability and runtime-check triggers), H22 (pure decision functions over captured inputs, one executor), H38 (Helium's bounded model checking: a verification method per claim), H41 (Helium's nine conditional recommendations for a Beryllium verification effort, "decision gates, not an adopted work plan") |
| Input armed | The hart-0 line after which the typing tool may type into a domain: the first hart-0 report of that domain's first served DBCN read, a marker the M7 plan numbers |
| Qualified; normative | A tool is *qualified* when it meets open-tooling's criteria and the project's own qualification suite for the question asked (known-pass, known-fail, vacuity, wrong-implementation cases) at pinned versions; a result is *normative* when the ledger cites it as a method for a claim |
| The comparison's rows | Retired from use outside that page; this revision names them: interactive guests, the first verification plan, dynamic management, measured launch, the pass-through device, the I/O service domain, dynamic multicore, the policy substrate |

### S3-C.2 The MVP ladder

Direction, recorded as decision D19. Only MVP 1.0 is planned by this
revision; each later rung needs its own plan revision or plan, written
after the rung before it is released (the release path's step 5,
publication, is "released"), and may be re-cut then. Read-only
preparation for a later rung, such as characterizing the K3 Mini-ITX,
may run before 1.0's release under its own bounded plan.

**Decisions of 1.0 that later rungs inherit**, each designed for its
successor: M9's log format (2.0's attestation covers it; a format change
later costs the verifier), M7's console-input representation and the
DBCN-read contract (2.0's first I/O class builds on them), and M8's
relational target for "refinement" (every later C result is stated
against it).

| Rung | Focus (the human's words) | Contents | What it is not |
| --- | --- | --- | --- |
| **MVP 1.0** | "something useful" | M0 to M6 as accepted; M7 interactive guests; M8 the first verification plan (resolving S1 H38 and H41); M9 measurement; M10 release candidate 4; then the release path's steps 2 to 7 | Not devices, not dynamic management, not attestation; a demonstrator, not a workload platform |
| **MVP 2.0** | "finalize core architecture and formalize" | In this order, each step a precondition of the next: (1) characterize the IOMMU/IOPMP, interrupt, reset, and device-ownership facts of the board; (2) the device and DMA object model, with H06's "authority without a mapping" and H07 answered where devices and the service domain make them concrete (H06's aggregation half is already answered: security model v1 Part 2, "unioned across rules, conjunctive across permissions"); (3) one static pass-through device path and the I/O service domain (implementation-plan milestone 5); (4) implementation-plan milestone 4's serialized mapping and invalidation protocol, which dynamic management and the device path both need, with its proof targets in 2.0's formalization; (5) dynamic management (milestone 3's dynamic part: restart, notifications, a management vocabulary), after H08 and H09 are evaluated for it; (6) the first non-Linux domain, chosen by the bake-off the [runtime sidebar](sidebar-minimal-vs-runtimes.md) left open with its candidate set kept or explicitly narrowed, LiteBox among them ([analysis](post-rc3-candidates-2026-10-31.md#litebox-analyzed-for-mvp-2-0-2026-10-31); the bake-off reopens the sidebar's "do not select"), after the service ABI is demonstrated; (7) attestation over M9's log with a simulated root of trust (D20), after M9's event semantics, the verifier's trust boundary, key custody, freshness, and replay rules are fixed; also Model 0.3, the generalized model (U-13 moved here, S3-C.4); the H57 scaling and H58 residual-risk analyses; sealed storage and anti-rollback as features of the simulated root (an eFuse-backed counter is stop (a)); new object classes as additive security-model revisions admitted by name; the K3 Mini-ITX as a second platform record. "Formalize" means: the project snapshot's stage 2 for the proof-bearing subset's decision functions and stage 3's cut-point contracts for the trap vector and the resume tail; stages 4 and 5 stay with implementation-plan milestone 9 | Not a general VMM; not multicore beyond static ownership unless its plan says so |
| **MVP 3.0** | "composition and extension" | Independent research tracks, each with its own trigger, hardware precondition, threat-model delta, and exit: MPT (memory protection tables), CoVE, CHERI, and policy composition (MCS or MLS beside TE, as a security model v2); a compatibility analysis of MPT's and CoVE's identity, ownership, measurement, and ABI boundaries is 2.0's last step, so that 2.0's architecture is not called final without it. Arm's MTE is Arm-only; a ratified RISC-V memory-tagging extension would join this list if hardware offers it. Investigation-grade unless hardware arrives | Not a product profile; no minimum set of tracks makes a 3.0 release until its plan says so |
| **MVP 4.0** | general guests | The general-guest work, defined by a guest profile its plan fixes: vCPU and SMP model and a scheduler, interrupt virtualization, the boot ABI (a UEFI and UKI path for image-based guests such as ParticleOS), the device set, storage and network, reset and recovery semantics, resource and availability limits, and a compatibility target; a LiteBox-class library-OS domain if 2.0 chose one; the remaining "normal Linux guest" steps. Storage and network delivery and a supported guest CPU and ABI profile do not wait on 3.0's hardware tracks; stage work may proceed in parallel earlier as community resourcing allows | "General guests" is not an exit criterion; the profile is |

Unplaced, each keeping its own gate from the implementation plan or the
[hardware roadmap](riscv-security-hardware.md): implementation-plan
milestones 6 (the policy substrate; it lands when a trigger fires, H08 or
H09), 7's remainder (the evidence adapters and the runtime
integrity-monitor experiment, which D20's IMA line applies to), 8 (Arm),
9 (the assurance release, including source-to-binary correspondence),
and 10 (upstream); side-channel research and stronger profiles;
availability and RAS/RERI; the DRTM profile; a hardware root of trust;
and the release process for the rungs after 1.0. Each enters the ladder
by its own plan.

### S3-C.3 Milestone M7: interactive guests

**Goal.** A researcher types into a Linux guest over the board's one
serial line, or QEMU's, and sees the isolation live: a shell in the
`two-guests` and `te-poc` domains and in `anchor`'s untrusted domain
(Q27); from the writer, write the shared page and from the reader read
it; from either, load an address no root of that domain maps, or store to
a shared page it may only read, and get `SIGSEGV` as the denial log
records the fault (neither guest can name "the other's private page":
both windows sit at the same guest-physical address). Scripted sessions
make the same demonstrations evidence the checker judges; a live session
is a demonstration, not evidence.

**Facts the plan rests on** (corrected from the first candidate):

- Release candidate 3 refuses DBCN read (`mvp-sbi.c` L416-L418); OpenSBI
  1.6 implements the read call; whether this board's firmware console
  driver supplies input to it has never been exercised (the B-series and
  the MVP only wrote). The guest kernel has `CONFIG_HVC_RISCV_SBI=y`; its
  `hvc` driver polls, backing off to 2 s when idle.
- Hart 0 already writes each domain hart's inbound ring, which carries
  PING, ACK, MGMT_RESULT, PAUSE, and TERMINATE (`mvp.h`,
  `BE_MVP_RECORDS_INBOUND`): the hart-0-to-domain direction exists; a
  writer that finds no room fails closed (`mvp-ring.h`), and M0
  deliverable 5 makes a full ring fail the writing hart. The block has
  12 KiB unused (`mvp-layout.h`, `BE_MVP_BLOCK_UNUSED_BYTES`).
- Console output is line-buffered and filtered to printable ASCII
  (0x20-0x7e) before posting (`mvp-sbi.c` L946-L975), and every printed
  line starts with a monitor tag or the domain's prefix. Hart 0 is the
  console's writer in the ordinary case; a domain hart writes its own
  FAIL and DETAIL lines when hart 0 makes no progress
  (`mvp-hartmain.c`), so "hart 0 alone writes the console" is false.
- The run budget is 2^32 ticks: 178 s on the board at 24 MHz
  (`mvp-layout.h` L203, L401), about 430 s in QEMU at 10 MHz; a run that
  reaches it ends as `run-timeout`. The guests boot with `panic=-1
  oops=panic panic_on_warn=1` (`gen-dts.py`), and a guest reboot request
  ends the run (`mvp-sbi.c` L443-L447): a typed `reboot`, or any oops,
  WARN, or panic a command provokes, ends the whole run for both
  domains.
- The board's console is one 115200-baud line, the bottleneck under load:
  output queues behind it (M0-C's finding); OpenSBI's uart8250 driver
  keeps no input buffer and reports no overrun, so input can be lost
  without trace while hart 0 writes a line, which QEMU cannot show.
- Every window leaf is V R W X U A D (`mvp-gstage.h` L71-L77) and the
  declared pages, the secret among them, lie outside the window: that is
  why the write path's "check the source against the window" rule can be
  reused for a copy *into* the guest.
- The U-Boot rehearsal's QEMU driver uses stdio pipes, not a PTY.
- Both domains boot one Linux `Image` with an embedded initramfs; a
  guest-visible surface change raises the SBI implementation version
  (D8).

**Shape** (the M7 plan bounds it; nothing here is implementation):

- **Console input.** Hart 0 gains one executor function that polls
  `sbi_debug_console_read` from HS at a stated cadence by a named wake
  mechanism (default: the control hart's own Sstc timer, which today arms
  the run budget only; hart 0 otherwise sleeps in `wfi` for IPIs, and a
  polling guest sends none), while idle and between printed lines. The
  bytes go to a **dedicated input-only ring per domain hart** (Q45) in
  the block's unused region: hart 0 writes it, the domain hart reads it
  at its DBCN-read exits, it carries no control record and sends no IPI,
  and its view takes a new INPUT type alone; the control ring's views
  then pass the five control types explicitly. The guest buffer is a
  guest-physical range the domain hart checks against the domain's own
  window before it copies, stated as **write authority**: addition
  overflow, zero and maximum lengths, a range crossing the window's end,
  and a range naming a declared page are refused, a refused call changes
  no guest byte and consumes no queued byte, and host tests show it.
  Input is never a reason to fail a hart or the run: bytes for no focus,
  for a target that is not running or holds no console grant, or for a
  full input ring are **dropped and counted by reason** (a departure
  from M0 deliverable 5's fail-closed rule, superseded for this ring), and
  hart 0 keeps per-run accounting (bytes read, delivered per domain,
  dropped per reason) that the record reconciles with the keystroke log;
  on the board a mismatch is a stop. Every byte received before the boot
  barrier is discarded.
- **Output volume.** A shell's output is unbounded and the outbound ring
  fails closed. The M7 plan chooses one of two designs: a documented
  output bound per session command, or backpressure where DBCN write
  returns a short count, derived only from the domain's own ring against
  a fixed drain share, never from the other domain's demand (which would
  open an undeclared cross-domain channel through hart 0's shared drain).
  Linux's `hvc` retries tty output on a short count but drops `printk`
  text on a zero count; the plan states the consequence.
- **Focus** (Q28). A two-byte sequence recognized only at the start of a
  typed line selects the domain that receives input; the prefix byte
  doubled sends it literally; any other pair is dropped and counted; no
  timeout, so routing never depends on arrival timing. The parser is a
  pure function host-tested over every byte value (H22). Hart 0 prints a
  **focus line** on each change, and the typing tool waits for it before
  the next typed line (lockstep: one line, then a token whose text differs
  from its echo; no type-ahead); no focus is implicit; input before any
  focus, to a paused, terminated, or shut-down target, or to a domain
  without the grant is dropped and counted, with a hart-0 line the first
  time each happens. The focus bytes join the typing tool's key set.
- **Output.** The output path is unchanged in 1.0 and its two invariants
  are stated: **no guest byte outside 0x20-0x7e reaches the terminal**,
  and **every printed line starts with a monitor tag or the domain's
  prefix**. Together they stop a guest from forging a monitor or log
  line, and the first alone stops a guest from making the operator's
  terminal answer a query into the focused domain. Relaxing either is a
  stop (h); a prefixed flush of a partial line is not a relaxation, and
  the plan says whether a paused or terminated domain's unterminated last
  line is flushed or lost. The console model is a question (Q44): line
  mode is the default, so the shell is blind before Enter and only the
  focus line confirms where input goes.
- **Representation** (Q43). For 1.0, console input and output are
  **monitor mechanism outside the policy**, as console output already is:
  which domain may receive console input is a configuration fact of the
  scenario's manifest, shown in the authority report as a configuration
  fact and not as a policy grant, and the claim ledger carries the
  non-claim. The policy notation gains no class (security model v1's
  classes are memory, channel, domain, and manifest), and the
  `two-guests` control stays policy-free. The alternative, a named
  additive security-model revision adding a console class, is admitted
  only by amending stop condition 1 by name and costs checker, generator,
  Rocq A1, and instance changes. Under either option the M7 plan records
  its evaluation of the two triggers (H08 and H09) for console input and
  focus, as M2's plan did for Instance 3; under M2's reasoning neither
  fires if focus selects only among domains that hold the grant, no
  domain can request, move, or query focus through any monitor
  interface, and HS evaluates no policy. The operator and the typing tool
  are trusted inputs; the M7 plan says how console output and the
  operator's relay between domains are treated. Security model v1 Part 1
  (the threat model, assets, and TCB) gains an additive revision for the
  console path, as its own exact commit, admitted by name in stop 1.
- **Binding.v coverage.** M3's hart-binding proof enumerates two rings
  and a closed set of steps; the input ring falls outside it. M7 adds an
  importing module beside Binding.v that extends the ring vocabulary
  without editing it, or records a ledger gap row; M7 may touch `model/`
  additively for that purpose.
- **Userland.** A pinned static **BusyBox** with **musl**, two external
  inputs beside the pinned Linux `v7.2`, built by `build-guest.sh` from
  exact tags and commits with release-tarball SHA-256s and upstream
  signatures where published, never committed, with a reproducibility
  check in the pattern of `kernel-repro`; the in-tree BusyBox `.config`
  is part of the pin (Q29). The M7 plan names: PID 1 starting the shell on
  a `/dev/hvc0` node with a new session and a controlling tty; the device
  nodes the initramfs gains; a pinned `PROC_FS` delta or explicitly none;
  the rv64imac/lp64 soft-float build against the locked GCC's multilib;
  an image-size budget under the boot-image limit; and whether the
  shells live in the accepted scenario images or in separately named
  interactive images (default: separate, so every accepted expectation
  stays intact). The `nolibc` programs of M1 and M2 stay as the
  regression baseline. BusyBox is GPL-2.0-only and musl MIT: no project
  code is linked into them, and any distributed guest image carries its
  components' licences, notices, and corresponding source (S3-C.6; the
  release path's "GPL-3.0-only" is the project's own source).
- **SBI.** `dbcn_read` is served, so the SBI implementation version
  increases (D8's rule); `anchor`'s protected domain keeps
  `SBI_ERR_DENIED`, a declared negative inside an accepted scenario.
- **Evidence.** A **scripted-session checker**: a static session file of
  `focus` and `send` actions, hashed into the run record and never
  executed, typed after input is armed; QEMU runs it through its serial
  character device, the board through the console tool's **guest-typing
  mode** under S3-A.1 item 8 (S3-C.9). The session specification proves
  what only the monitor can attest, transcripts corroborating: every typed
  byte reached only the announced focus holding the grant (hart-0 focus
  changes, delivered-byte counts and SHA-256 per focus period, and drops
  by reason, reconciled with the keystroke log); each demonstrated denial
  matches its DENY line from user mode, with the address and cause and
  the protected data unchanged; the declared channel works; the declared
  negatives hold (no grant, input before focus, a paused or terminated
  target, ring overflow, a literal prefix, and on the board a terminal
  query); in `anchor` the protected domain received no input, its
  computation and measurement are unchanged, management actions still
  complete, and **the secret's bytes, raw or hex, never appear in the
  capture**. Matching is bound to the accepted check rows: whole lines
  after the prefix, in order, counted, with a run nonce, so that a guest
  printing a look-alike marker satisfies nothing. Denied accesses use a
  handled-fault helper (an `argv[0]` variant of the in-tree init), not
  BusyBox `devmem`, whose handler-less `SIGSEGV` makes the kernel print
  "unhandled signal", which M1-A keeps rejected. Each session ends with
  both domains powered off inside the budget; an interactive budget is
  the M7 plan's, named as a departure from M0's Q11. Loss, pacing, and
  outbound overflow can be shown only on the board.
- **Claim.** The claim gains the sentences S3-C.7 pre-authorizes for M7;
  the M7 plan fixes their words.

**Board characterization.** M7's first board step is a **typed and
recorded** characterization under S3-A.1 item 8: a probe image that
reports what the read call returns while a named typist (the human, or
the typing tool under item 8) types a fixed text; a probe nobody types
into reads zero bytes with success and decides nothing. It covers absence,
blocking, and loss at the pacing the plan fixes (stop (f)). One short
scripted session may run inside it (Q31).

**Exit.** Scripted sessions pass in QEMU for both toolchains and every
scenario that declares one; the typed characterization is recorded; the
trigger evaluation, the Part 1 revision, and the Binding.v module or gap
row are made; the M7 plan's own exit criteria.

### S3-C.4 Milestone M8: the first verification plan

**Goal.** A first bounded result about the monitor's own C, positive or
negative, and a decided, or deliberately undecided, vehicle for proving
more: the project snapshot's stage 1 (a concrete operational model) and a
stage-2 pilot, chosen small enough to learn which tool fits before
committing further. RC4 waits on M8 **accepted**, not on M8 successful.

**Four layers, named.** A C result is one of these, and the plan says
which: a **per-call contract** (preconditions, result, memory footprint,
rejection behaviour, and runtime-error obligations in the tool's C
semantics); the **C-to-model relation** (the contract's correspondence
to the stage-1 definition); the **concurrent protocol** (interleavings,
ordering, and ownership per word and phase, which sequential tools cannot
see); and **compiled execution** (what the locked compilers and the
executor preserve, assumed where no binary correspondence exists). A
result may be called **refinement** only if it establishes, for every
concrete state related by `R` to a model state `m`, that terminating
defined execution of the exact production function preserves the stated
frame, returns the model's result, and leaves a state related by `R` to
the model's next state. CN and Frama-C/WP deliver a contract proof plus a
link to stage 1, by a Rocq-checked realization or a named and reviewed
transcription; that is recorded as a **contract proof**, with the
remaining relation an assumption, never relabelled refinement.

**Shape.**

- **Stage 1, the concrete model.** A Rocq operational model of harts 0 to
  2 of the MVP: the hart blocks with their publication generation words,
  the single-writer rings (whose indices have no generation words), the
  boot barrier, the denial path, `pause` and `terminate`, and the
  measurement's abstract measure-before-entry gate only, with M9's
  implementation explicitly unproved. It is built on M3's accepted
  modules, which already model the MVP: new modules import `Binding.v`
  and `Policy.v` unedited, with two first obligations (each concrete
  step's writes lie within Binding.v's footprint for its transition, so
  H3 carries over; the concrete roots, leaf rights, denial and management
  decisions are computed from the generated instance, so A8 and A6
  apply), and a **property-lineage table** (inherited, re-proved,
  strengthened, inapplicable) for Model 0.2's properties. Model 0.2's
  `Model.v` stays as accepted: its closed inductives describe the fixed
  single-hart switching profile the MVP never runs, so an MVP instance is
  not additive and a simulation to it would relate the MVP to a profile
  it does not run (Q35). The model's **memory semantics are stated**:
  interleavings of the three harts, with the ordering premises (the
  fences, and the ring writer's control dependency, on which buffer reuse
  rests) as theorem premises, never axioms, checked as litmus tests on
  the compiled sequences (herd7 or isla-axiomatic); a sequentially
  consistent first result, if any, is labelled as such and not promoted.
  The project snapshot's stage-1 row carried that clause; the first
  candidate dropped it. Stage 1 names a **target commit** (Q46):
  M8's own base, with every source reading made at that commit (Binding.v's
  hand-copied readings are stale at RC3, `mvp/README.md` item 101; C-06's
  note is re-read, symbols are cited rather than lines, layout constants
  are generated from `mvp-layout.h`, and a gate check catches drift) and
  the re-proof rule below at RC4. Its specifications are drafted from the plans and the
  claim, not from the C, frozen by hash before proof drafting, and
  reviewed by the human as reviewer of record (D22). The model gate is
  extended additively: one "Closed under the global context" report per
  new theorem, and the plural keywords added to the escape-hatch pattern
  (`mvp/README.md` item 102).
- **Stage 2, the pilot.** Two tools on one leaf, with bounded model
  checking as the complement. The leaf the selection rests on is
  **`be_mvp_denial_decide`** with its static helpers (`mvp-sbi.c`;
  contract in `mvp.h`): pure over const, hart-private inputs, no
  volatile, typical of the proof-bearing subset, behind U-08 and C-15,
  and inside CN's accepted single-hart role (Q34). `mvp-ring.c` is the
  **second leaf**: the bounded-model-checking target and the tool stress
  test (fixed-width arithmetic, bounded loops, aliasing, volatile shared
  indices, wraparound), with a contract arm if the budget allows, whose
  claim is per call, holds for any value of the peer's index, names its
  ownership premise, and claims nothing for U-04 or U-11; the ring
  protocol's ordering is stage 1's. The arms: **Frama-C/WP** as the
  primary arm (ACSL through the importer, beside the unchanged source;
  WP's export to Rocq, whose path against the model lock `rocq-9.3` must
  be qualified, not assumed); **CN** as the second arm on the same leaf,
  built with Cerberus from pinned source into the evaluator image with
  M0-B's digest discipline (more than "the pattern of the closure"; it
  publishes no releases, so a commit is pinned); **bounded model
  checking** (CBMC, Fedora-packaged, in open-tooling's baseline) for
  specification debugging, mutation and vacuity checks for every arm, and
  bounded per-call properties of the ring, never called proof and given
  its own ledger method term (Q36); ordering edges by litmus tests, which
  the C arms cannot see. **VST** is excluded for the project's own C:
  verifying it needs `clightgen`, whose passes depend on CompCert files
  outside the open licence (open-tooling L144 and research-synthesis L376
  rest on a false premise; `mvp/README.md` item 103). RefinedC is deferred
  until a release is pinned to the project's Rocq; direct Rocq proofs
  stay the recorded open load-bearing candidate. Solvers: Z3 and cvc5 as
  the independent pair; Alt-Ergo only as a release under a free licence
  (the reviews report its current GitHub and opam releases as
  non-commercial). A **decision
  rule is registered before any arm starts**: the stage-1 property list
  every arm must state, the gates (open tools at pinned versions by NEVRA
  and SHA-256, an offline reproducible build, the leaf unchanged, an
  assumption inventory per arm, all goals closed, `unknown` and timeouts
  never counted as success), an equal time box per arm, and a mutant set
  chosen in advance (the harness's seeded single-defect rule applied to
  every proved leaf, plus vacuity checks). Fedora packaging is provenance,
  not qualification: the reviews report that Fedora built Frama-C 33.0
  with its tests disabled, so the project's own qualification suite runs.
  The Copilot CLI review's research found CN's proof-log code holding an
  unrestricted placeholder for SMT provability: its results are solver
  checks, not independent certificate replay, until that is re-checked at
  the pinned commit.
- **Outcome.** A **recommended vehicle per claim class**, non-load-bearing
  until the recorded promotion gates hold (the implementation plan's for
  CN; an explicit direction from the human for WP); "inconclusive" and
  "no vehicle fits" are valid, recorded outcomes. The pilot selects no
  tool "for the proof-bearing subset"; the recorded tool roles
  ([open tooling](open-tooling.md); [implementation plan](implementation-plan.md),
  CN's role and promotion gates) stand and are cited, and change only by
  an explicit direction.
- **Where annotations live** (Q37). Beside the source, by default: WP's
  through the ACSL importer; CN's in an annotated copy, because its loop
  invariants and proof hints sit inside function bodies, gated in the
  evaluator by a check that the copy's comment-stripped token stream
  equals the source's and by recorded digests of the source, every header
  of its translation unit, the flags, and the tool pins. The first
  candidate's rationale overstated the cost of annotating in place: no
  ledger row pins `mvp-ring.c`, and the ELF is identical when comments
  change; moving annotations into the source later costs ELF digests and
  line counts only.
- **Re-proof rule.** Every proof binds the digests of its translation unit,
  flags, and tool pins; a change to any of them, which M7 (`mvp-sbi.c` and
  the headers every leaf includes) and M9 will make, invalidates the row
  until the proof is re-run; a failure is a stop and a stale run
  downgrades the row (open-tooling L276). M10's gates run every tool on
  every proved leaf at RC4's exact tree.
- **Resolving H38 and H41.** S1 deferred both to S3. Both reviews that
  read Helium's `docs/fv-pathfinder-lessons.md` (at `1c9e5269`) agree
  stage by stage; the M8 plan reproduces each stage by its text and fixes
  the evidence per stage:

  | Helium stage (H41) | Disposition |
  | --- | --- |
  | 1, select a candidate seam | Adapt: the denial decision carries the selection; the ring is admissible only with its cross-hart protocol as a separate obligation |
  | 2, require entry criteria | Adopt: the exact source boundary and the target commit |
  | 3, qualify the tool for the question | Adopt for every arm, not only bounded model checking: pinned tools, solvers, options; known-pass, known-fail, vacuity, and wrong-implementation cases |
  | 4, independent specification ownership | Adapt: the human as reviewer of record; specifications drafted from the plans and the claim, frozen by hash |
  | 5, a mutation plan before acceptance | Adopt: the seeded single-defect rule on every proved leaf, plus vacuity checks |
  | 6, exact evidence | Adopt: digests of the translation unit, flags, and pins, with the re-proof rule |
  | 7, a clean evaluator workflow | Already practice; M8 extends the evaluator |
  | 8, clean-commit and human gates | Already practice; the human's exact-commit decision is the review of record |
  | 9, exit criteria | Adopt, including "a negative feasibility result is a valid outcome" |

  Helium's "lessons not to transfer" are adopted too, above all "do not
  conflate CBMC with proof-assistant verification". H38 is resolved as
  adapted bounded checking per named claim, never Helium's suite or its
  counts transferred; the resolution is recorded in the M8 plan and in
  this plan's status, and the synthesis's text is not edited.

**What it does not do.** No board; no monitor behaviour change; no
whole-system claim; no claim-text change unless the pilot's result is
positive, and then only the amendment S3-C.7 pre-authorizes. The forbidden
phrasings stand: this is a bounded result about named functions, never
"formally verified".

**Exit.** One of three recorded outcomes, each accepted by the human: a
vehicle recommended per claim class with its gates, assumptions, and
mutation results; inconclusive, with the reasons; or no vehicle fits,
with the reasons. In every case: the stage-1 model builds and its stated
properties are proved in the evaluator under its stated premises; the
lineage table, the litmus results, the decision rule and its outcome, the
bounded-model-checking record, the H38 and H41 record, and the ledger
rows (new rows only on a positive result) are made; the size guide is
re-derived in the M8 plan for stage 1's scope, per lane (model, bridge
and contracts, tool glue), and a limit is re-evaluated, never cut (Q41).

### S3-C.5 Milestone M9: measurement

**Goal.** The launch identities the monitor records, and the loader and
platform observations beside them, made explicit per platform, with a
log a researcher can read and the checker verifies against the build;
"measure first, then attest" (D20). It is honest about its bottom: on this
board no root of trust is characterized, SPL, OpenSBI, and U-Boot are
unmeasured, and the firmware's loader offers only what it offers. Nothing
here is a chain of trust.

**What exists.** The monitor computes SHA-256 (`mvp/src/mvp-sha256.c`);
the sealed configuration's **core identity** is a SHA-256 of its
canonical bytes, computed at boot (M6; `mvp/src/mvp-core.h`); the build's
**configuration identity** binds the manifest, the policy, and the
labeling (`policy_identity` and `labeling_identity`) and is linked into
the image (M2, M3); hart 0 measures the protected domain's kernel and
device tree before entry and the `wrong-measurement` negative proves the
check bites (M2; `BE_MVP_CLASS_MEASUREMENT`); U-Boot's `be_ld` prints
`md5sum` of the loaded file, which the checker uses as run attribution
(M5). The BSP's U-Boot has `crc32` and `md5sum` and no `hash`, `sha1sum`,
or `sha256sum` (characterization attempt 7, 2026-10-30; the record is to
be committed, `mvp/README.md` item 104), and `crc32` prints nothing on
this build. M9 adds no firmware or NOR write; the one write the board
policy allows is S3-A.1 item 3's recorded `saveenv` (S3-C's "nothing
writes the NOR" of the first candidate was false under it).

**Three evidence classes**, each with its producer and checking rule,
never merged into one record:

| Class | Producer | Checking rule |
| --- | --- | --- |
| The monitor log | Hart 0: measured values, and the identities the image carries labelled as build-recorded | Against each image's post-link references, offline; the per-domain launch measurement also gates entry, as M2's does |
| The loader observation | The host's capture of U-Boot's load and digest lines: MD5 on the board, CRC-32 in the U-Boot rehearsal, nothing in direct QEMU boot; the staged file's SHA-256 from the staging record | Checker-held, board-only attribution of the whole boot image (shim, monitor, kernel Image, both device trees) by an unmeasured U-Boot identified by its banner; binding the MD5 to a SHA-256 does not upgrade it |
| The platform observation | The human's dated, read-only probe of the board's lifecycle and debug state | A platform assumption in the record and the claim's required limit, stated with its date; never a per-boot event |

**Shape.**

- **The log.** A canonical, versioned, bounded binary page, hart 0's
  alone, zero-initialized, with no timing fields, printed losslessly as
  `BE_MVP` lines (the lines are a checked rendering, the page is the
  log); a header (magic, version, scenario and configuration identity,
  capacity and count, completeness state), length-delimited records
  (sequence, producer, record type, stream, object, representation and
  exact byte range, algorithm identifier from the TCG registry with
  SHA-256 as 0x000B and its digest, outcome), and a close record before
  first domain entry with the expected count. Two record types:
  **measured** records extend a named **measurement register**, `R =
  SHA-256(R || digest)` from zero, one register per stream (platform and
  monitor, configuration, each domain), printed at the barrier and at the
  run's end and called registers, not PCRs; **informational** records are
  typed as such and never extended. Overflow fails closed; duplicates,
  omissions, and reordering are findings. The checker rebuilds the page
  from the lines, replays the registers (its replay values labelled
  unprotected), and exports CEL-JSON. MD5 has no registry entry and stays
  in the checker's run record, never in the page. Log records are accepted
  only from hart 0's unprefixed stream.
- **The records, per image class** (the M9 plan's per-stage table says,
  for each, what computes it, over which bytes, where the expected value
  comes from, who compares, when, and what a mismatch does):
  - **R1, loader attribution**: checker-held, board-only (above); absent
    in QEMU, CRC-32 in the rehearsal; never a log record. The checker
    enforces M5's one-boot-per-run rule, exactly one autoboot line and one
    `Starting kernel ...` per run's loader stream, so that an image cannot
    print its own autoboot line and a forged loader block (the present
    checker reads the lines after the *last* autoboot line; `mvp/README.md`
    item 100, a prerequisite of M9).
  - **R2, the monitor's self-measurement**: SHA-256 of its own text and
    read-only data at boot, an informational record, a self-report
    (a consistency witness against the build's digest of the same bytes,
    which detects a corrupted load and not an adversary or a modified
    monitor). Never gates entry (an expected value inside the measured
    range is a fixed point); compared offline with the post-link digest;
    its negative is a post-link byte flip inside the range. It misses the
    shim, whose bytes lie outside the monitor's text; kept only if the
    build reproduces the exact final loaded ranges, else dropped.
  - **R3, the configuration**: the core identity, measured at boot, and
    the configuration and policy identities the image carries,
    build-recorded: the log **binds** the policy and never "measures" it.
    `two-guests` records the absence of a policy explicitly.
  - **R4, each domain's launch**: the kernel Image and device tree of
    both domains, extending M2's one measurement, logged and then gated
    per domain as M2's is; the secret page for `anchor`. There is no
    separate initramfs object: both domains boot one Image with an
    embedded initramfs, and no cpio parser enters HS.
- **References.** The pre-link authority report stays an input; it is
  generated with the monitor's compile inputs and cannot hold a post-link
  digest, and `two-guests` and the probe images have no report. M9 adds a
  **post-link, per-image reference manifest** that binds the report's
  hash, the exact source, configuration, toolchain, and variant, the ELF
  and boot-image digests, the measured range table, and the expected
  records, in the CEL-JSON shape of `systemd-pcrlock`'s `.pcrlock` files
  with a stated update rule per build. The checker binds the two
  configuration identities through the reference, never comparing them
  as one hash.
- **Standing decisions.** Measurement is of images, configuration, and
  policy at the domain boundary, never of files inside a guest; **IMA is
  never used** (D20), made testable: no Beryllium-built guest `.config`
  sets `CONFIG_IMA` (the existing delta check asserts it); no Beryllium
  record, verifier, or claim consumes an IMA measurement list or a CEL IMA
  content type; the monitor measures only what it places or seals before
  entry. Nothing writes an eFuse or a lifecycle, secure-boot, or debug
  configuration, and nothing writes the NOR beyond S3-A.1 item 3 (stop
  (a)).
- **Platform facts.** The human will probe JTAG, read-only (TAP and Debug
  Module status, no halt, no write), outside the campaign tools (Q40),
  with four outcome classes: Debug Module reachable without
  authentication; authentication required; TAP answers but no Debug
  Module; no connection, cause unknown, never recorded as "locked". The
  outcome, dated, is a platform assumption in the record and the claim's
  required limit, in words the forbidden list allows; "not determined" is
  an honest outcome with a disposition. Whether a debug adapter stays
  attached during evidence runs is recorded. The probe is board time and
  is counted (Q31).
- **Analysis deliverable**, no implementation in 1.0 unless Q39 is
  answered otherwise: a requirements crosswalk among (a) a later minimal
  vTPM with a standard TCG event log, (b) a Beryllium per-domain
  measurement-register SBI extension that a guest extends and the
  monitor logs, and (c) a lossless adapter from the Beryllium log profile
  to the TCG and systemd model (`systemd-pcrlock`, `systemd-measure`,
  `systemd-pcrphase`, UKIs); what the reference manifest already
  supplies; what attestation with a simulated root needs from the log;
  how a guest's own IMA stays out of Beryllium's evidence under (a) and
  (b); and where implementation-plan milestone 7's runtime
  integrity-monitor experiment belongs under D20's line. Amutable's
  image- and configuration-as-artifact approach is design input, with a
  source cited; its product assurances do not transfer. No claim of stock
  systemd compatibility until a TPM-facing interface and adapter exist.
- **Claim.** The content of the measurement clause is fixed here, its
  words by the M9 plan (pre-authorized, S3-C.7): stated per platform; what
  the monitor recorded and what the checker compared; the self-measurement
  as a self-report; loader attribution on the board only, by an
  unmeasured U-Boot identified by its banner, none in QEMU; SPL, OpenSBI,
  and U-Boot unmeasured; no key, nonce, freshness, or root of trust, so
  code able to alter the monitor can fabricate its records and a record
  does not show the bytes unchanged after the measurement point; the
  lifecycle and debug state as a dated assumption. The words "chain",
  "lowest stage", "measured identity", "measured boot", "attested", and
  "secure boot" stay out of the clause; the first candidate's suggested
  phrases passed the forbidden-phrasing matcher, which is why their
  content is fixed here rather than left to a check.

**Toward attestation (MVP 2.0, not planned here).** No lab option is a
root of trust for measurement; 2.0's "simulated" root is scoped to
storage and reporting (a key, a monotonic counter, registers) and claims
the protocol, freshness, and the verifier's decisions, never hardware
trust or resistance to physical access. The candidates and their
prerequisites: JTAG through the Debug Module, the only reader independent
of the measured software, able to cross-check the monitor's text against
the build, but needing open debug (an isolation bypass the hardware
roadmap names), with halt and bus coherence stated; its read of the log
page only re-reads the monitor's own report. The ESP32 dongle, today a
reset controller that senses nothing, with unidentified firmware outside
the tool lock: to hold registers it needs a reset-sense input, pinned
firmware, and a data path (a monitor-driven link is a device, stop 3,
and waits for 2.0's device path; a passive console tap avoids that). The
carrier's management chip, characterized nowhere in the tree. A signer of
monitor-supplied digests notarizes a self-report. The 2.0 default: the
dongle holds the registers and produces the nonce-bound quote, fed by a
passive console tap, with JTAG for independent text checks, as "an
external lab verifier observation". The human is asked to confirm that
"a simulated hardware root of trust for the proof of concept" meant 2.0.

**Exit.** The log and its page, the per-image reference manifests, the
checker's verification and replay, the negatives (omission, duplication,
reorder, a wrong producer, object, algorithm, or range, an unsupported
version, truncation and overflow, a wrong reference image, toolchain, or
variant, a forged loader block, a false platform-fact binding, and a wrong
digest at each record the monitor controls), the platform fact with its
outcome class, the secure-boot disposition for 1.0 as a documented
platform assumption, the analysis, the ledger rows (C-40, U-10, U-12
restated as needed), which of implementation-plan milestone 7's gate items
M9 discharges; board evidence per Q31.

### S3-C.6 Milestone M10: release candidate 4

As M4 made release candidate 1: with M7, M8, and M9 accepted (their
results, not only their plans), one exact commit at which the gates pass
from a clean checkout (`check`, `evaluate`, the U-Boot rehearsal,
`kernel-repro` and its BusyBox and musl counterparts, the model gates
including stage 1's, every M8 tool on every proved leaf at RC4's exact
tree, and the CN copy-equality check), the board campaign under the S3-A
board policy with item 8 runs at its images (the scenarios with their
scripted sessions, the probes, the negatives, measurement verified in
every run), the records, the ledger rows, the evidence record, and the
packet. M10 owns the release surfaces: the claim (its header and
evidence paragraph restated for RC4 through the ledger's release object,
as debt sweep 3 made them), the guide, the walkthrough, the AI-assistance
disclosure, and the snapshot README template, and a per-component
licence manifest with notices and corresponding source for any
distributed guest image. Release candidate 4 is MVP 1.0's candidate for
the release path's steps 2 to 7.

### S3-C.7 Order, parallel lanes, and the release path

```text
M0 ... M6 (accepted) ─┬─> M7 interactive guests ──┐
                      ├─> M8 verification plan ───┼─> M10 (RC4) ─> steps 2-7
                      └─> M9 measurement ─────────┘
```

- M8 touches `model/`, the evaluator, and at most the pilot leaves'
  annotated copies; it needs no board and can start while the COM260 is
  in the other project's use. M7 and M9 both change the monitor and the
  checker: they are planned as separate lanes on separate branches, as
  M6's work packages were, and merged in the order their results are
  accepted, each merge re-deriving the ledger's pins, the guest pins, and
  the expected digests. **The lanes are parallel, not independent**: M7
  changes the ring layout and record grammar M8 models and the headers
  its leaves include, and M9 changes the measurement M8 abstracts. So M8
  is under the merge-order rule too, its stage 1 models a named target
  commit with parameterized interfaces, and the re-proof rule (S3-C.4)
  runs every M8 proof again at RC4's exact tree before any pin is
  re-derived; a green replay of proofs about the old state space is not
  post-merge revalidation. M7 may touch `model/` additively for its
  Binding.v module.
- Board time, which is contested: each milestone's plan says whether it
  needs a board run of its own; the default (Q31) is QEMU evidence at the
  milestone, M7's typed characterization, M9's human probe counted as
  board time, one bounded M9 correlation boot folded into a board session
  already scheduled, and one campaign at RC4. 1.0's defaults if the
  COM260 stays busy, if stop (f) fires, or if M8's pilot is inconclusive:
  M7's QEMU evidence stands and its board evidence waits; M9's QEMU
  evidence stands with the loader attribution recorded as absent; M8 is
  accepted at its recorded outcome; RC4's campaign waits for the board.
- The release path's steps are unchanged. Step 1, "the latest release
  candidate's exact commit is accepted" (S3-A.3, S3-B.3), holds for
  release candidate 3 today and will for release candidate 4 when it is
  accepted; steps 2 to 7 follow release candidate 4 (D21). Steps 2 to 4
  have a bounded first form in the review snapshot, which the human may
  refresh from an accepted commit with `mvp/tools/snapshot.sh update`
  under an instruction naming that exact commit, with the gates the last
  refresh ran recorded in its README; a refresh is a publication act
  under stop 7, not a release step, and does not move step 1.
- **Claim-text changes pre-authorized**, each fixed in words by the
  milestone plan and accepted with it, the forbidden-phrasing list
  checked, in the pattern of S3-A's pre-authorization of M5's board
  clause: **M7**, the sentences on console input and the shell (what a
  researcher can type, where input may go, the focus rule), the guest
  software sentence (BusyBox and musl beside the `nolibc` programs), and
  the required limit's operator boundary (the operator and the typing tool
  are trusted inputs; a shell in a domain is not evidence that arbitrary
  guests are contained); **M8**, only on a positive result, the required
  limit's sentence that the rings and the rest of the implementation are
  covered by tests and checks "and by nothing else", narrowed to name the
  proved functions, the kind of result (contract proof, or refinement
  under S3-C.4's relational target), the exact source commit, tool, and
  assumptions, every other function staying as it is, and the ledger's
  method vocabulary gaining "C-level contract proof" and "bounded model
  check" (never "bounded proof"), with every umbrella phrasing still
  forbidden; **M9**, the measurement clause with S3-C.5's fixed content,
  and the firmware residual (SPL, OpenSBI, U-Boot unmeasured) and the
  dated lifecycle and debug assumption in the required limit; **M10**,
  RC4's metadata (the candidate's name and commit through the ledger's
  release object, the evidence paragraph's records, the board-records
  table). Any other claim change is stop (d). The method-per-claim table
  (L566-L589), D7, and the non-goal L252 are superseded to the extent
  these amendments state, and no further.
- The LiteBox analysis changes nothing in MVP 1.0; its record is the
  comparison page's section and the runtime sidebar's disposition, which
  the 2.0 bake-off reopens.

### S3-C.8 Decisions D19 to D22, and the stops this revision adds

| ID | Open item and its source | Decision |
| --- | --- | --- |
| D19 | The MVP ladder and MVP 1.0's scope after release candidate 3 (the human's directions of 2026-10-31; the comparison) | MVP 1.0 is M0 to M10 as S3-C.2 lists, a security-research demonstrator ("useful to show" and, bounded, "to trust"): interactive guests (M7), the first verification plan (M8), measurement (M9), and release candidate 4 (M10) join the accepted M0 to M6; MVP 2.0, 3.0, and 4.0 are named with their focus, contents, and order, and each is planned by its own later revision or plan; the 1.0 decisions later rungs inherit are S3-C.2's three. D1's default "M1 as a step toward M2, both in MVP 1.0", Q1's default "M0 to M4", and D5's "not in MVP 1.0; `nolibc` programs" are superseded as the table below states |
| D20 | Measurement and attestation (implementation-plan milestone 7; the hardware roadmap's "Secure boot and lifecycle"; the human: `we want to measure and attest, but start with measurement`, `we are not using IMA ever`) | Measurement first, in MVP 1.0 (M9): the monitor's launch identities in a log with measurement registers, verified against each image's post-link references, beside the checker-held loader attribution and the dated platform assumption, never one chain; attestation with a simulated root of trust in MVP 2.0. Measurement is at the domain boundary, of images, configuration (measured), and policy (bound); IMA is never used, by the three testable criteria of S3-C.5. systemd's measured-boot stack and Amutable's work are analysed in M9 and implemented, if at all, from 2.0 unless Q39 is answered otherwise |
| D21 | Release-candidate staging and the release path (S3-A.3, S3-B.3) | Release candidate 4 is M10's result and MVP 1.0's candidate for the release path's steps 2 to 7; RC1 to RC3 stay accepted history; the review snapshot may be refreshed from an accepted commit on an instruction naming it, as a publication act under stop 7 with the gates run and recorded, without being a release step |
| D22 | Model split for this revision and its milestones (the human's direction at the first candidate's session, 2026-10-31: the orchestrating model plans, orchestrates, and reviews, `claude-opus-5.5` codes) | This revision and the M7 to M10 plans and packets are written on the orchestrating model; code and proof drafts on `claude-opus-5.5` at the pinned effort and context; M8's specifications are drafted from the plans and the claim, not from the C, frozen by hash before proof drafting, and the human is their reviewer of record; the independent reviews the human directed (three, on 2026-10-31 and 2026-11-01) are steering input, not decisions. The pin in `.github/copilot-instructions.md` is unchanged |

**Stop condition 1 amended by name.** Its exception list, "the additive
security model v1 revision that M3 plans", gains: the additive security
model v1 Part 1 revisions (threat model, assets, TCB) that the M7 and M9
plans carry, each as its own exact commit; and, only if Q43 is answered
with its alternative, the console class revision. Each goes to the
responsible human as its own exact commit.

Stop conditions this revision adds to the plan's list (each returns the
work to the responsible human):

- **(a)** any need to write an eFuse or other one-time-programmable bit,
  to make a persistent change to the board's lifecycle, secure-boot, or
  debug configuration, or to write the NOR other than by S3-A.1 item 3's
  recorded `saveenv`; the human's read-only debugger attachment (TAP and
  Debug Module status, no halt, no write) is outside it;
- **(b)** a guest-typing session that would type a line outside its
  session file or anything during U-Boot; a boot banner (SPL, U-Boot,
  "Autoboot in") during a live session aborts the session and is a stop;
- **(c)** a measured object whose expected value the checker cannot
  compute from the build's inputs, as one class; an unavailable or
  contradicted platform observation as another;
- **(d)** a claim-text change other than those S3-C.7 pre-authorizes;
- **(e)** any change to monitor source beyond comments, or to an accepted
  model file or gate (Model 0.2's modules; M3's `Policy.v`, `Binding.v`,
  `PolicyClaims.v`, `PolicyAssumptions.v`; `run-proofs.sh`) other than
  the new importing modules and gate extensions the M7 and M8 plans
  enumerate; a global axiom in any model module; a proof whose
  assumption the deployed configuration violates, or a footprint the
  sources contradict. A defect found by a proof follows a protocol:
  record the counterexample and a failing host test in a scratch copy,
  freeze the specification, and stop; the human routes the fix before
  M10 and decides on a snapshot note;
- **(f)** a firmware console that does not supply input, blocks, or loses
  or corrupts input at the pacing the M7 plan fixes, judged by a typed
  and recorded characterization, which returns M7's board evidence to the
  human with the QEMU evidence intact;
- **(g)** any input byte delivered anywhere but to the announced focus
  holding the console grant, before input is armed, or to a domain that
  is not running, in QEMU or on the board;
- **(h)** any need to relax the output invariants: a guest byte outside
  0x20-0x7e reaching the terminal, or a guest byte starting a printed
  line;
- **(i)** a merge that changes an accepted M8 proof's translation unit,
  flags, or pins without the proof re-run first; a failure is a stop, and
  a stale run downgrades the row.

### S3-C.9 Board policy item 8: typing into a running MVP (additive to S3-A.1)

S3-A.1 governs every board session; its items 1 to 7 stand. This
revision adds item 8, which M7's typing needs and which no milestone plan
may widen:

8. **Typing into a running MVP.** The console tool's guest-typing mode
   types only the lines of a static session file hashed into the run
   record, and the two focus bytes, each line only after the hart-0 line
   that arms input for its focus domain and after the focus line that
   confirms it, re-gated on a line-start hart-0 line before every piece;
   never during U-Boot, SPL, or autoboot; no reset during a session; every
   keystroke recorded, as the U-Boot templates are. A banner during a
   session aborts it (stop (b)). The human types during a typed
   characterization, or the tool does under this item. S3-A's rewritten
   harness "Run" row, "automation types at U-Boot from templates,
   recorded", is extended: automation also types into a running MVP, only
   under this item.

### Accepted lines this revision supersedes

| Where | Accepted text | Now |
| --- | --- | --- |
| "What the MVP is" (L113-L115) | claims bounded to "proofs about the abstract model" | and, on a positive M8 result, a bounded C-level result about named functions (S3-C.4) |
| Scope, cross-hart signalling (L213-L217) | the rings carry denial records, console bytes, requests one way, and `pause`, `terminate`, results the other | and a dedicated input-only ring per domain hart, hart 0 writing, no IPI (M7, Q45) |
| Scope, "Guests" (L220-L222) | "running `nolibc` programs built from the pinned tree" | and a static BusyBox with musl shell, from two more pinned external inputs (M7) |
| Scope, "B7's guest SBI subset" (L232-L233) | Base, DBCN, TIME, SRST, and M2's management extension | DBCN's read call is served from the domain's input ring (M7); the implementation version increases (D8) |
| Scope, the measurement line (L234-L235) | "A core-held measurement of the protected domain and the configuration (M2), as local identity only" | widened to both domains, the monitor's self-report, and the configuration's record, with a log and registers (M9); still local identity, never attestation |
| Scope, the model line (L237-L238); D7 (L635) "the model work is M3" | the policy layer for Model 0.2 (M3) | and M8's stage-1 operational model beside M3's modules |
| Scope, the release candidate (L239) | M4's | M10's (RC4; D21) |
| Non-goals, "Remote attestation, measured boot, sealed storage, and anti-rollback" (L250) | "Milestone 7; M2's measurement is local identity, not attestation" | Measurement with a log and registers in MVP 1.0 (M9); attestation, sealed storage, and anti-rollback stay out, for MVP 2.0; "measured boot" in the TCG sense stays a non-goal |
| Non-goals, "An assurance release: open binary correspondence, C refinement, and whole-system proof" (L252) | Milestone 9 | narrowed to "C refinement beyond M8's pilot leaves"; binary correspondence and the whole-system proof stay with milestone 9 |
| Non-goals, "Guest console input and a richer userland" (L254) | "Roadmap; the `nolibc` programs suffice for every scenario here" | M7 |
| M0 deliverable 5 (L316-L322) | hart 0 "waits in `wfi` for IPIs"; "a full ring fails closed on the writing hart" | hart 0 also wakes on a stated cadence to poll the console; the input ring drops and counts instead of failing (M7) |
| Method per claim (L566-L589): the non-claims at L574, L577, L578 and "remain unproved" at L581-L585 | no root-builder, ring, or request-protocol proof; every MVP addition unproved | on a positive M8 result, the proved leaf's row gains its method and the matching non-claim narrows, exactly as S3-C.7's M8 amendment states; nothing else moves |
| D1 (L629) | "M1 as a step toward M2, both in MVP 1.0 (Q1)" | MVP 1.0 is M0 to M10 (D19); M1 and M2's relation is unchanged |
| D5 (L633) | "Not in MVP 1.0; `nolibc` programs" | A pinned BusyBox with musl and console input in M7; the `nolibc` programs stay as the regression baseline |
| D15 (L643-L644) | "one single-writer, single-reader ring per direction per domain hart" | two rings from hart 0 to each domain hart: the control ring and the input ring (Q45) |
| Q1 default (L738) | "M0 to M4" | M0 to M10 |
| Status record `s3_richer_userland=not-in-mvp` (L794) | | `in-mvp-1.0-M7` |
| S3-A's rewritten harness "Run" row (L967) | "automation types at U-Boot from templates, recorded" | and into a running MVP under S3-A.1 item 8 (S3-C.9) |
| S3-B.3 (L1087-L1093) | "will be by release candidate 3 when it is accepted; the human's direction is that steps 2 to 7 wait for release candidate 3" | holds for release candidate 3 today; steps 2 to 7 follow release candidate 4 (D21) |
| Claim ledger U-13's forward sentence; the M6 plan's D-6 and Q4; the M6 evidence record; the M6 acceptance record (the generalized model assigned to "the first verification plan") | | Model 0.3 is MVP 2.0's (Q35); the three accepted M6 texts are superseded on this point without being edited; `mvp/README.md` and the ledger note follow at the next status refresh |
| Roadmap, "Later phases", "Measured launch and attestation"; roadmap L431-L434 (BusyBox out of 1.0) and L562 ("Selected refinement" later); implementation plan L1380-L1383 and L2027-L2030 (MVP 1.0 as M0 to M4) | maintained documents | measurement in MVP 1.0 (M9), attestation in 2.0; BusyBox in M7; the pilot in M8; MVP 1.0 as M0 to M10; each follows at the next status refresh |
| Project snapshot section 8, "the pragmatic first bounded plan"; its stage-1 row's concurrency and RVWMO clause | stage 0 inside RC3 plus stage 1 and a CN pilot; the clause | M8 as S3-C.4 states, with Frama-C/WP piloted beside CN on the denial decision, bounded model checking evaluated, and the clause restored |
| CN's and WP's recorded roles (open-tooling L289-L294; implementation plan L1132-L1137); open-tooling L144 and research-synthesis L376 (the VST route) | | the roles stand and are cited, changing only by an explicit direction; the VST route is recorded as unusable for the project's own C (item 103), the two documents' correction being the human's |

Unchanged: the hart layout and static ownership (D14 and D16; D15 as
superseded above), the policy notation and the analyses under Q43's
default, the core in restricted C, the standing kexec rule (S3-A), the
board policy's items 1 to 7 (item 8 added), the release path's steps, the
claim's present text until the pre-authorized sentences are fixed by
their plans, and every accepted record.

### Open questions and defaults

The numbering continues this plan's (Q1 to Q12) and does not collide with
the milestone plans' own questions; Q13 to Q26 are deliberately unused,
so that an S3-C question number is never one a milestone plan also uses
(each numbers its own from Q1); the gap is cosmetic.

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q27 | Does the anchor's protected domain get a shell too? | **No**: no shell and no console grant in the protected domain, whose DBCN read stays `SBI_ERR_DENIED`; shells in `two-guests`, `te-poc`, and `anchor`'s untrusted domain; the secret's bytes never appear in an anchor capture; BusyBox is in the one Image either way | A separately named debug scenario with a protected-domain shell, whose claim words say its behaviour includes unmeasured operator commands and which makes no secret claim |
| Q28 | The focus sequence | A two-byte sequence recognized at line start, the prefix doubled for a literal, no timeout, a pure host-tested parser, a hart-0 focus line the typing tool waits for, drops counted by reason, no implicit focus change | Framed records with target, length, epoch, and acknowledgment; a second UART (the board has one console) |
| Q29 | How BusyBox and musl are pinned | Exact upstream tags and commits with release-tarball SHA-256s and upstream signatures where published, the in-tree BusyBox `.config` part of the pin, fetched and built by `build-guest.sh` like Linux, never committed, with a reproducibility check; session files hashed into the run record | Fedora's source RPMs by NEVRA and SHA-256, as the evaluator's closure is |
| Q30 | Where the scripted sessions run | In QEMU for every scenario that declares one, both toolchains, as a gate, matching bound to the accepted check rows with a run nonce; on the board in the campaign; QEMU cannot show loss, pacing, or outbound overflow | Board only |
| Q31 | Board runs before release candidate 4 | QEMU evidence at each milestone; M7's typed and recorded characterization, with one short scripted session inside it; M9's human probe counted as board time; one bounded M9 correlation boot folded into a board session already scheduled; one campaign at RC4 | A campaign per milestone, as M1 and M2 had |
| Q32 | Does MVP 1.0 wait for the K3 Mini-ITX? | No; the COM260 is MVP 1.0's board, and the Mini-ITX joins as a second platform record in 2.0; if the COM260 stays busy, S3-C.7's defaults apply | RC4's campaign on both |
| Q33 | Dynamic management in 1.0 or 2.0? | 2.0, as recorded on 2026-10-31 (the human's spoken list of that day had it in 1.0; the recorded direction is the comparison's), MVP 1.0 being a demonstrator and not a platform to build workloads on | A fourth milestone in 1.0, M2-sized or larger, before RC4 |
| Q34 | M8's pilot leaf | `be_mvp_denial_decide` with its static helpers carries the selection; `mvp-ring.c` is the second leaf (bounded model checking; a per-call contract arm if the budget allows) | The ring alone, with the recorded outcome narrowed to ring-class code |
| Q35 | The concrete model's relation to the accepted models | A separate operational model under `model/` importing M3's `Binding.v` and `Policy.v` unedited, with the two first obligations and the lineage table; Model 0.2's proofs stay as accepted; the generalization (Model 0.3) is MVP 2.0's, with U-13's six texts superseded on that point | Close U-13 in stage 1 (generalize now) and re-derive the size guide; generalizing `Model.v` is barred by stop (e) |
| Q36 | Bounded model checking (H38) | Evaluated in the pilot as the complement (specification debugging, mutation and vacuity checks for every arm, bounded per-call properties of the ring) under a defined qualification, with its own ledger method term and its bit widths, bounds, unwinding checks, and assumptions recorded; never "proof" | Excluded from M8 |
| Q37 | Where M8's annotations live | Beside the source: WP's through the ACSL importer; CN's in an annotated copy gated by token-stream equality and recorded digests | In the source, with the ledger's and checker's pins re-derived in M8's own commit |
| Q38 | The loader's digest | MD5 by this U-Boot, an unauthenticated loader observation held by the checker as board-only attribution, excluded from the log's registers; the NOR is not rewritten to gain a SHA command; the premise's record committed (item 104) | Chain-load a second U-Boot from the partition (a new boot path; not in 1.0) |
| Q39 | The per-domain measurement-register extension | Analysed in M9 (the crosswalk), implemented from 2.0 | Implemented in M9 if its plan finds it small; D20 then follows |
| Q40 | The lifecycle and debug probe | The human's, read-only (TAP and Debug Module status, no halt, no write), recorded with the board, probe, and tool identity, the exact commands, the raw capture's hash, the date, and one of four outcome classes, "not determined" among them; the tools do not touch JTAG | A tool-driven probe under its own templates |
| Q41 | Soft limits | Set by each milestone plan and re-evaluated rather than cut; the guides: M7 "M1's monitor work plus a tool effort on M5's scale"; M9 small to medium; M8 re-derived in its plan for stage 1's scope per lane (model, bridge and contracts, tool glue), counting theorems, assumptions, and tools beside lines | One limit for all three |
| Q42 | Independent review | The three reviews of this revision were steering input; none is required for the milestone plans beyond the SOP, the human's reviewer-of-record role for M8's specifications (D22) standing | A focused independent review of each milestone plan and its security-relevant result (M7 protocol and threat; M8 formal methods; M9 schema and claim) before any claim or ledger change |
| Q43 | How console input is represented | Monitor mechanism outside the policy for 1.0, as console output already is: the console grant a configuration fact of the manifest, shown in the authority report as such; a ledger non-claim; the notation gains no class; a console class is 2.0's first I/O class | A named additive security-model revision adding a console class, admitted by amending stop condition 1 by name, with checker, generator, Rocq A1, and instance changes |
| Q44 | The console output model | Line mode, as today: output held until LF, printable-only, prefixed; the shell is blind before Enter and the focus line confirms routing | Character mode with a prefixed partial-line flush on a cadence, if the M7 plan shows both invariants hold |
| Q45 | The input ring's topology | A dedicated input-only ring per domain hart in the block's unused region, no IPI, no control record, an INPUT type alone; D15 superseded | Typed bytes as a record kind on the existing control ring, with proved reserved control capacity, priority, and bounded delay |
| Q46 | Stage 1's target commit | M8's own base commit, with every source reading made there and a drift check, and the re-proof rule at RC4's exact tree | RC4's tree, stage 1 waiting for M7 and M9 |

### What acceptance would authorize

Accepting this revision at its exact commit would record D19 to D22 as
amended, the amended stop condition 1, S3-A.1 item 8, the superseded
lines, and Q27 to Q46 at their defaults or as answered, and would
authorize writing the bounded plans of M7, M8, and M9, in any order or in
parallel, each on its own branch from the development branch, and, after
those three milestones' **results** are accepted, M10's plan. It would
authorize no implementation, no board command (none until the human says
the COM260 is free), no accepted-byte change, no model change, no
claim-text change (the pre-authorizations take effect through the
milestone plans' acceptance), no push, merge, publication, or release
step, and no code fix of the open items this revision names (100 to 104),
each of which waits for the human's direction.

### Revision history of S3-C

| Candidate | Exact commit | What happened |
| --- | --- | --- |
| First | `95c9ab24ba2846eea6d102639abb3482c97989ec` (2026-10-31) | Read by three independent reviews under the packet's section 8 brief; superseded, never accepted |
| Second | this text | Rewritten against the reconciliation's rows A to AQ: Q27, Q28, Q34, Q38's meaning, Q40, Q41 changed; Q43 to Q46 added; stop 1 amended by name; stops (a), (c), (e), (f) reworded and (g) to (i) added; S3-A.1 item 8; the claim pre-authorizations as a bounded list; the supersession table completed; M7's facts corrected; M8's four layers, leaf, outcome, and re-proof rule; M9's three evidence classes, log requirements, and claim content; the ladder's order and placements; the spelling of Amutable |

### Status record addendum

```text
s3_revision_s3c=accepted
s3_revision_s3c_target=27d2e557f069edf8dd714f5ac9b5ccb9b204a801
s3_revision_s3c_acceptance_instruction=accept-27d2e557-defaults-ff-push
s3_revision_s3c_acceptance_date=2026-11-01
s3_revision_s3c_acceptance_record=mvp-plan-s3c-review-summary.md
s3_revision_s3c_open_questions_answered=Q27-Q46-defaults
s3_revision_s3c_authorization=write-M7-M8-M9-plans-each-on-its-own-branch;M10-plan-after-their-results;nothing-else
s3_revision_s3c_open_items_status=99-100-102-105-closed-by-debt-sweep-4;95-closed-by-debt-sweep-5;101-103-104-open;106-107-open
s3_revision_s3c_first_candidate=95c9ab24ba2846eea6d102639abb3482c97989ec;superseded-never-accepted;reviewed-by-three-independent-reviews
s3_revision_s3c_reviews=copilot-cli-2026-11-01;codex-cli-2026-10-31;claude-code-2026-11-01;reconciliation-mvp-plan-s3c-review-reconciliation.md-rows-A-AQ
s3_revision_s3c_base_commit=8b7559d2-for-the-accepted-body;branch-merged-with-b53c02a8-debt-sweep-3-accepted
s3_revision_s3c_direction_dates=2026-10-31;2026-11-01
s3_revision_s3c_directions=take-more-time-for-a-useful-MVP-1.0;the-ladder;measure-first-then-attest;IMA-never;simulated-root-of-trust;systemd-and-amutable-where-applicable;litebox-analysed-for-2.0;separate-review-by-a-different-agent;process-the-reviews-and-iterate
s3_revision_s3c_milestones=M0,M1,M2,M3,M4,M5,M6,M7,M8,M9,M10
s3_revision_s3c_release_candidates=rc1-c5df0cfa-accepted-history,rc2-3867c66c-accepted-history,rc3-89ef04e9-accepted-2026-10-31,rc4-M10-result
s3_revision_s3c_decisions=D19-ladder-and-scope-demonstrator;D20-measurement-first-IMA-never-testable;D21-rc4-and-release-path-refresh-gated;D22-model-split-and-reviewer-of-record
s3_revision_s3c_open_questions=Q27-Q46-defaults;changed-from-first-candidate-Q27-Q28-Q34-Q38-Q40-Q41;added-Q43-Q46
s3_revision_s3c_stops=stop-1-amended-by-name;a-to-i
s3_revision_s3c_board_policy=S3-A.1-item-8-typing-into-a-running-MVP
s3_revision_s3c_claim_changes_preauthorized=M7-console-and-guest-software-sentences-and-operator-boundary;M8-required-limit-narrowed-only-on-a-positive-result-and-method-terms;M9-measurement-clause-with-fixed-content-and-firmware-residual;M10-rc4-metadata
s3_revision_s3c_authorization_if_accepted=write-M7-M8-M9-plans-then-M10-after-their-results
s3_revision_s3c_open_items=mvp/README.md-100-forged-loader-block;101-binding.v-readings;102-gate-plural-keywords;103-vst-route;104-q38-premise-record
s3_revision_s3c_release_path=step-1-holds-for-rc3-89ef04e9;steps-2-7-after-rc4
s3_revision_s3c_m7_plan=accepted-4f4d094e-2026-11-01
s3_revision_s3c_m7_result=accepted-e1a6395e038d4dd095960f7a942a87399bdbce18;parent-8418a377;2026-11-02;instruction-accept-e1a6395e-move-k3ctl-pin-to-v1.1-pin-part-reversed;record-mvp-m7-result-review-summary.md
s3_revision_s3c_m8_m9_plans=not-started;on-go-either-first
```

## Plan revision S3-D: a physical boundary under the monitor first, supervisor-domain alignment, and the domain terminology rule

**Status.** Directed, and proposed by the commit that adds this section.
This revision is made on the public development line, `main` after the
tag `mvp-1.0`, where each commit is prepared unsigned and the responsible
human signs it off and pushes it. So: if the commit that adds this
section is on the public `main` with the responsible human's
`Signed-off-by`, this revision is accepted as written, with Q52 to Q57 at
their defaults. Any other answer needs a revised commit before the
sign-off. The signed commit differs from the one reviewed only by that
line and its committer date; if it must be rebased first, the internal
record says so. Both commit IDs and the instruction are kept in the
project's internal records, as the CHERI integration's were. Line
references are to this document at `a0d0b78b`.

MVP 1.0 was published on 2026-11-08 at the tag `mvp-1.0`, so the rung
after it may now be planned (S3-C.2, L1262-L1265). On 2026-11-09 and
2026-11-10 the responsible human reviewed how the policy is enforced and
directed, in these words:

- `we need to use assume breach model`, and `I don't feel comfortable
  with the lack of a boundary between HS domains` ("HS domains" there
  means the monitor's per-hart parts in HS mode; S3-D.2 gives the terms
  used from here on);
- `part of the purpose of this project is to utilize & validate platform
  features, so we should plan to integrate PMP possibly as the next
  step, and update the plan`;
- `we should also ensure we are aligned with supervisor domains
  architecture, and can readily implement it (initially via emulation)`;
- `we should also make changes now to avoid clashes with SD
  terminology`;
- `we will change the NOR policy, and we can always reset the K3 to
  factory when/if needed`;
- `if any policies seem to forbid a direction, stop and raise that with
  me (e.g. the NOR policy)`;
- and, on reading a draft of this revision, `re M12 waiting on mem
  protection tables, any reason we can't implement that and contribute?`

A session plan built on the first six directions was reviewed
independently, and the human approved it on 2026-11-10 with five form
answers: `ladder=boundary_first`, `board_firmware=staged`,
`naming=profile`, `attacker=post_activation`, and
`m11_steps=domain_harts_first`. To the last direction he gave three
more: `m12=lane_now`, `qemu=fork`, and `upstream_model=nameable`. When
the state of others' work had been read in full (S3-D.4), he answered
again: `m12_shape=build_on` and `first_contact=work_first`, which
replace `qemu=fork`. Three candidates of this revision were reviewed
independently before this text, which answers those reviews; none was
signed.

This revision turns the directions and the answers into plan text. It is
deliberately narrow. It records the direction, re-orders the ladder,
fixes a terminology rule, and names two milestones in outline. It selects
no design. It changes no claim text, no identifier, no image, no item of
the board policy, and no accepted document other than this plan.

### S3-D.1 Why: what MVP 1.0 leaves open inside the monitor

MVP 1.0's monitor is one HS-mode image that runs on harts 0 to 2. The
G-stage bounds each guest. Nothing that the monitor controls bounds the
monitor's own code: PMP belongs to the firmware, MVP 1.0 does not use
it, and what the board's firmware programs was never recorded. The
[security model](security-model-v1.md) records this as open (L217): "The
sealed manifest's protection inside HS | none: the seal is an API
property, and any HS C code can write the sealed state (S1 H05)". A flaw
in one hart's trap path that gave a guest control of HS-mode code there
would reach every VS domain's memory, the other harts' state, the sealed
configuration, and the secret page. MVP 1.0's claim does not say
otherwise: its threat model trusts the monitor's code whole.

"Assume breach" adds an attacker that the model does not have: **HS-mode
code on a hart, after that hart's activation**. Activation is a VS-domain
hart's first guest entry, and the control hart's boot barrier. Boot code
before that stays in the trusted base, and its inputs stay untrusted and
checked, as today (`attacker=post_activation`).

HS-mode code cannot bound itself. The mechanism this hardware has for the
purpose is physical memory protection (PMP): per-hart rules that only
M-mode programs. The [hardware roadmap](riscv-security-hardware.md)'s
principle applies: every relevant platform security feature is to be
"inventoried and assigned an explicit use, deferral, verification, or
unsupported status", and used "when it strengthens a stated property
without obscuring the reference monitor or inflating the TCB". PMP has
had no use so far.

What such a boundary could and could not do is stated here, so that no
later text overstates it. Against a breached hart it would protect:

- the other VS domains' memory;
- pages that the breached hart's VS domain has no right to, the secret
  page among them;
- the other harts' private monitor state;
- the sealed configuration and every G-stage table.

It would not protect:

- the breached hart's own VS domain, or whatever that VS domain may
  already write;
- the mailboxes between harts, which both ends write by design. The
  control hart stays a hub: a breached VS-domain hart can attack the
  control hart through them, and through it the other hart;
- the evidence lines: a breached hart can print forged text;
- availability;
- anything against cache or timing channels between harts.

M-mode's own memory is the firmware's to protect, as it is today. The
firmware's call interface becomes the next thing that a breached hart
attacks. That is why the firmware is in scope (S3-D.5, S3-D.6).

### S3-D.2 The terminology rule (D24)

"Domain" occurs 3,882 times in the planning pages, the MVP's documents,
and its sources (2,308, 476, and 1,098; `git grep -I -i -o -E
'\bdomains?\b'` at `a0d0b78b`), and "domain hart" 461 times. Three other
things that this revision brings into view use the same word: the
firmware's OpenSBI domains; the supervisor domains of the RISC-V
Supervisor Domains Access Protection specification (v0.9.0 of
2026-08-19, not ratified: the document calls itself a draft, and a
release script added to its repository later names v0.9 the "frozen"
milestone); and the interrupt domains of the Advanced Interrupt
Architecture. The rule: the specification's words keep the
specification's meanings, and ours are qualified.

| Term | Meaning from this revision on |
| --- | --- |
| **supervisor domain** (the specification's "SD"), **RDSM**, **SDSM**, **SDID**, **MPT** | The specification's meanings only. No Beryllium unit is named one, or given one, before M11's or M12's plan records that mapping as a decision (stop (k)). The reading below is of MVP 1.0 as a whole |
| **OpenSBI domain** | The firmware's construct, always written in full |
| **interrupt domain** | AIA's APLIC domains and the specification's supervisor interrupt domains: always qualified |
| **VS domain** | Beryllium's policy subject: a VS-mode guest with one G-stage root, one VMID, and, where the scenario has a policy, one type; the security model's `domain`. New and maintained text writes "VS domain" wherever M-mode, PMP, OpenSBI, or the specification is in view. "Domain" alone, in a document accepted before this rule, means VS domain |
| **VS-domain hart** | The accepted "domain hart", written in full wherever firmware constructs are in view |
| **host VS domain** | `anchor`'s untrusted Linux guest; never "host domain" |
| Compound names | "Protected domain" and "service domain" keep their accepted form, and are written "protected VS domain" and "service VS domain" wherever M-mode, PMP, OpenSBI, or the specification is in view |
| **physical access profile** | The new thing: the set of physical extents, with rights, that one hart may reach after its activation, enforced by M-mode. A hart under one is **confined**. No new noun is introduced for "the unit" (`naming=profile`) |
| **G-stage root** | Never "root" alone near M-mode text: the firmware's default OpenSBI domain is named ROOT |
| **microSD card** | Never "SD" for a card: "SD" is the specification's abbreviation |

How the specification's model reads on MVP 1.0, as a reading and not a
decision: the whole of MVP 1.0, the monitor with both guests, sits in one
hosting supervisor domain, with OpenSBI in the RDSM's role and the
monitor in the SDSM's, and a VS domain is a virtual machine hosted inside
it. Whether M11's confined harts are to be called supervisor domains is
for M11's plan. The specification's motivation says that PMP can be used
for "creating isolated supervisor domains", but that "this approach is
typically suitable only for simple systems with statically allocated
resources". Its operative text is "The RDSM may utilize `Smepmp` ... -
or equivalent and/or the `Smsd` (Supervisor Domains) extension". Whether
a design on plain PMP qualifies, and what differs, would have to be
stated there.

**What changes with this revision:** the rule; the
[glossary](glossary.md)'s rows for the terms above and its stale rows
(hart, control hart, domain hart, PMP, protected domain); and the
hardware roadmap's stale names and statuses.

**What does not change:** no identifier, no image byte, no accepted
text, and nothing at the tag `mvp-1.0`. New identifiers arrive with M11's
code. Renaming the policy types `prot_t` and `prot_mem_t` is not a clash
with the specification, and `policy.te`'s hash is in every `te-poc` and
`anchor` image: it is a separate, later sweep (Q52).

### S3-D.3 The ladder, re-cut (D23, D27)

MVP 2.0 keeps the focus that S3-C.2 gave it, "finalize core architecture
and formalize", and its seven steps in their order. M11 now comes before
them, and M12 runs beside M11 (`ladder=boundary_first`, `m12=lane_now`):

| Order | Milestone | What | Why here |
| --- | --- | --- | --- |
| First | **M11**, the physical boundary | Each hart that the monitor uses is confined by a physical access profile owned by M-mode, and every other hart is parked | The device path, the service VS domain, and dynamic management all add HS-mode code and shared state. A boundary under that code costs less before it exists than after, and the memory layout that the boundary needs (S3-D.5) would otherwise be redone |
| Beside M11 | **M12**, the supervisor-domain lane | Memory protection tables under emulation, outside the claim: contributions to the specification, the reference model, the emulator, and the firmware that others have in progress; then M11's descriptor enforced by the tables | It keeps M11's descriptor honest: a descriptor that only PMP could enforce would not be aligned. It does not wait, and it does not duplicate (D27) |
| After M11 | S3-C.2's steps (1) to (7) | Unchanged, in their order. They do not wait for M12 | |

M12 gates one thing only: S3-C.2's "compatibility analysis of MPT's and
CoVE's identity, ownership, measurement, and ABI boundaries", which
stays MVP 2.0's last step and builds on M12. MVP 3.0 keeps memory
protection tables on hardware, and CoVE, as research tracks.

Each milestone gets its own bounded plan, as M0 to M10 did. The release
process for the rungs after 1.0 stays unplaced (S3-C.2, L1283-L1292):
M11's result is a new candidate on the development line, not a release.

### S3-D.4 Milestones M11 and M12 in outline

**M11, the physical boundary. Goal.** After its activation, each hart
that the monitor uses can reach only the physical memory that its role
needs, under rules that M-mode programs from a description built offline
and that HS-mode code on that hart cannot change. The harts that the
monitor does not use are parked under rules that deny them the monitor's
memory. Every scenario still passes; hostile test images show that a
forbidden access has no effect.

**Requirements.** M11-R1 to M11-R9 are adopted from the independent
review of the session plan, and M11-R10 follows from the human's
alignment direction. The prefix keeps them apart from the runtime
packages R0 to R8. M11's plan may refine them, and returns to the human
before it drops one.

| # | Requirement |
| --- | --- |
| M11-R1 | One immutable partition descriptor, generated offline from the scenario and the layout, with an identity. M-mode installs a profile from it and never takes a range, a profile, or a hart from HS-mode code |
| M11-R2 | A complete allowlist of M-mode calls for each hart and phase. Everything else is absent from the firmware or refused after activation. Every call that takes an address is checked against the caller's profile. Suspend, stop, and start paths that would reprogram PMP are closed |
| M11-R3 | Every execution context that can address physical memory is accounted for: confined, parked, or named in the trusted base. All eight X100 harts are tested |
| M11-R4 | A new memory layout: each hart's private state, each ring's words by writer, and each shared mailbox in its own extent, aligned as the mechanism needs. Shared regions are listed exceptions |
| M11-R5 | An exact PMP entry table for each hart, read back after it is programmed |
| M11-R6 | The control hart's narrowing is a one-way move out of its boot profile. Its evidence is a record held in M-mode, or an oracle outside the monitor |
| M11-R7 | A negative test passes when the forbidden access has no effect, with M-mode's own count of denials as the witness. A hart that merely stops is not a pass |
| M11-R8 | Security model v1 Part 1 Revision 4 first, as its own exact commit: the attacker of S3-D.1, the profile and the shared regions as objects, the activation phase, M-mode's services, the unused harts, and numbered invariants |
| M11-R9 | A proof-impact review before any M8 proof is re-run. A newly accepted M8 specification where an interface changes. The CHERI check as a gate, with the boundary off for that variant |
| M11-R10 | Alignment: the descriptor names no PMP-specific fact above its backend (no power-of-two assumption), lists shared memory, hart membership, and lifecycle explicitly, has a stable identity that the measurement can bind, and says how interrupts and devices would be assigned, so that memory protection tables could enforce it unchanged |

**The design is not chosen here.** M11's plan chooses it on the
characterization's facts (S3-D.5), among at least: one OpenSBI domain
with an activation call; one OpenSBI domain per hart; per-hart OpenSBI
domains with a small amount of M-mode code of ours; and a minimal M-mode
runtime. It also makes, for this static profile, the three-way
comparison that the [implementation plan](implementation-plan.md)
requires of a later runtime plan (L467-L471): "OpenSBI below Beryllium
HS", "a Beryllium-owned M-mode component", and "a separately maintained
minimal M-mode runtime". The accepted decisions that a design would
change are named and decided there (S3-D.8). Before any M-mode code of
ours is committed, the plan fixes its language rules, its licence
(OpenSBI is BSD-2-Clause; `COPYING` makes GPL-3.0-only the project's
default), where it lives, and how the firmware is built reproducibly
(stop (m)).

**Order of work.** Revision 4, then the plan. Under emulation, two
steps: the VS-domain harts confined first, observed by the control hart
and the checker; then the control hart narrowed
(`m11_steps=domain_harts_first`). The board comes last, after the
amendment of S3-D.6.

**Evidence, in outline.** Host tests of the derivation; image-checker
rules; every scenario passing with the boundary on; and hostile-monitor
negative images under M11-R7, each also run with the boundary off, to
show that the test discriminates. PMP cannot stop a write to `hgatp`, so
a forged `hgatp` is tested by the access that follows it.

**Exit.** Responsible-human acceptance of M11's exact result commit. The
plain images of MVP 1.0, its claim, and its tag are not changed by it.

**M12, the supervisor-domain lane. Goal.** M11's partition descriptor
enforced by the specification's memory protection tables under
emulation, on a reference model, an emulator, and a firmware that others
can run too; and, on the way, contributions to the work that others have
in progress on each. It is a variant with its own check, outside the
tool lock and the claim, as the CHERI variant is.

It does not wait, and it does not start a parallel implementation where
one is in progress (D27, `m12_shape=build_on`). When read on 2026-11-10,
no upstream reference model, emulator, or firmware had merged support
for the tables, and no end-to-end stack ran. Work was in progress in
each project:

- the specification, v0.9.0, still a draft: it leaves several
  behaviours that a model needs unspecified, and its instruction
  encodings are not settled;
- the Sail RISC-V model's pull request #1727: the registers and the
  fence instructions, without the table walk and without tests;
- a QEMU series, at version 8 and written to draft v0.49 (its cover
  letter's "v0.4.9"), which its author has said he will update to
  v0.9.0;
- an OpenSBI series, posted as an RFC at version 7, which builds one
  table for each OpenSBI domain;
- Spike's pull request #2336, for one table mode;
- no shared test suite.

The lane's steps, each bounded by M12's plan:

1. **Questions to the specification's authors**: the behaviours that a
   model needs and the text leaves open.
2. **Directed tests** that run unchanged on each implementation that
   supports the case, among the Sail model, QEMU, and Spike, once the
   instruction encodings are settled (step 1).
3. **The table walk for the Sail model**, on top of pull request #1727,
   with those tests. A model that the project helps to write is a
   reference only through its review by Sail's maintainers, and through
   cross-checks against the implementations that others wrote.
4. **Testing and review of the QEMU series' next version and of the
   OpenSBI series**, with a per-hart descriptor as the workload. A fork
   of the emulator is kept only for what M12 needs and the posted series
   still lacks, and none before its author's update is posted.
5. **M11's descriptor under the tables**, once that descriptor is
   stable and the pieces run together.

The project prepares steps 2 and 3 first, and drafts step 1's questions
with them. The responsible human writes to the people whose work they
build on when there is something to show, and the questions go with
that first contact (`first_contact=work_first`). Nothing is offered to
another project before he has.

Rules for anything bound for another project: code, tests, device
trees, documentation, and the text of a submission (stop (o)).

- That project's contribution policy is read at the time, and followed.
  As read on 2026-11-10:
  - QEMU: "Current QEMU project policy is to DECLINE any contributions
    which are believed to include or derive from AI generated content."
    The policy leaves other uses free, "such as researching APIs or
    algorithms, static analysis, or debugging, provided their output is
    not included in contributions", and it invites discussion of
    exceptions on QEMU's list. So nothing written with AI assistance is
    offered to QEMU. What is offered there is test results, defect
    reports, and review, in the responsible human's own writing.
  - The Sail RISC-V model requires that any use of generative AI be
    disclosed, and a sign-off.
  - The specification's repository requires a sign-off in the
    submitter's real name; its text is under CC-BY-4.0.
  - OpenSBI requires a sign-off.
- It is written only with AI tools that can be disclosed by name, and it
  derives from no work that was written with one that cannot
  (`upstream_model=nameable`).
- The characterization's scratch is never a source for it: that scratch
  is uncommitted and unreviewed, and has no provenance record. M12
  writes afresh what it needs.
- It is written under the destination's licence, with no text of this
  repository copied in. M12's plan decides where it lives.
- Each change records the tool that wrote it. AI-written commits in any
  public fork are marked as such, so that no one offers them to a
  project that declines them.
- Every submission is the responsible human's: his name, his sign-off,
  and his correspondence. Automation sends nothing to another project.
- Existing work is built on and credited, not duplicated.
- `LLM_POLICY_ALIGNMENT.md` is rechecked for each destination first.

**Order.** Steps 1 to 4 do not wait for M11; step 5 does.

**Exit.** Acceptance of M12's plan, and then of each step's result, at
exact commits. What another project accepts is that project's decision,
and is not an exit condition.

### S3-D.5 The characterization, and what it has found so far

The characterization began on 2026-11-10 on the human's instruction
(`start stage 1`). It is reading of sources and documents, and emulation
in scratch space outside the repository. That scratch holds bare-metal
M-mode test harnesses, OpenSBI builds from changed configurations, and
prototype patches to OpenSBI. They run only under emulation. They are
never committed, never run on the board, and never cited as evidence for
a claim (stop (m)). The characterization changes no file here. Its
findings are recorded, with their evidence, in M11's and M12's plans;
until then they are inputs to those plans. To date:

- Under emulation, PMP gives each hart its own view: the same page was
  readable and writable on one hart, read-only on a second, and
  unreachable on a third.
- OpenSBI domains, described in the firmware's device tree, provide such
  a view for each hart. Across OpenSBI domains the firmware refuses a
  hart start and does not deliver an IPI. D15's hart start and IPIs both
  cross harts, so one OpenSBI domain for each hart breaks D15 as
  accepted.
- The firmware matters as much as PMP does, because its calls act in
  M-mode on a caller's behalf. Upstream OpenSBI v1.6, which the project
  pins for emulation, predates a correction to the address-range check
  that those calls use (upstream commit `9595829a3367`, "lib:
  sbi_domain: reject overflowing address range in check_addr_range()",
  first released in v1.9). The gap was read in source, and reproduced
  under emulation with plain PMP between two test OpenSBI domains. MVP
  1.0's claim is unaffected: its threat model trusts the monitor's
  HS-mode code, and no guest reaches a firmware call. The vendor's
  published source for the board's firmware carries an equivalent
  check; whether the board's binary is built from that source is not
  established. A boundary against a breached hart needs a firmware
  build of ours in every candidate design: for M11-R2's allowlist, and
  so as not to rely on a correction that the board's binary is not
  shown to carry.
- Today's memory layout fits no candidate's PMP entry budget, and it
  keeps the secret's source among constants that the monitor's HS-mode
  code reads on every hart. The new layout (M11-R4) comes first.
- The monitor touches no device, so a confined hart's profile can deny
  every device range.
- By the vendor's documents and upstream OpenSBI's K3 support, the K3
  has more execution contexts than the eight X100 harts: eight A100
  harts without the H extension, and RCPU cores that run the vendor's
  real-time firmware from memory beside the monitor's. Whether this
  board runs them, and what they can reach, is not established
  (M11-R3).
- No upstream emulator, firmware, or reference model had merged
  support for the supervisor-domain extensions when read on 2026-11-10.
  Work was in progress in each (S3-D.4, M12).

### S3-D.6 The board firmware (D25)

Only M-mode programs PMP. The resident firmware could in principle
program a profile for each hart from its device tree. But a boundary
against a breached hart needs a firmware build of ours: for M11-R2's
allowlist, and so as not to rely on a correction that the board's
binary is not shown to carry (S3-D.5). S3-A.1 rules that out today.
Item 1 boots by "the board's resident firmware (SPL, OpenSBI, U-Boot in
the QSPI NOR)". Item 3 says "The NOR firmware is never written". Item 4
says "No other partition, the UFS, `env_k3.txt`, or the human's boot
files are written". The M5 plan uses no card, and stop (a) bars any NOR
write other than the recorded `saveenv`. The human's direction is `we
will change the NOR policy, and we can always reset the K3 to factory
when/if needed`.

This revision records the direction. It changes no item of S3-A.1, and
it adds stop (j). **S3-A.1's items 1 to 8 and stop (a) stand until an
amendment is accepted at its own exact commit**
(`board_firmware=staged`). The staging is fixed now:

1. **Read-only first, before the amendment, under S3-A.1 as it
   stands.** The boot chain as this board runs it; where its SPL takes
   OpenSBI, and OpenSBI's device tree, from; the state of its signature
   checks; the NOR's layout and hashes; the other execution contexts.
   From documents and sources pinned by commit, and then from a
   read-only inventory taken from the board's own Linux, in sessions
   that the human opens. The inventory is read as one of S3-A.1 item
   1's read-only preflight checks. Its outputs are copied off the
   board, or written only to the Beryllium partition (item 4). Records
   that hold the environment stay private (item 7). Stop (j) does not
   cover these reads.
2. **The amendment**, proposed when step 1's facts are known. Steps 3
   to 5 run only under it, each on the human's own word, with him
   present.
3. **A recovery rehearsal that writes nothing.**
4. **A microSD card that carries our firmware build**, with the NOR
   untouched. PMP's grain is readable only from M-mode, so our build
   reads it here. The card slot's pins are the board's only JTAG pins
   (`mvp/README.md`, item 129), so a card and the read-only debug probe
   exclude each other.
5. **A NOR write last**, under its own authorization. Its first
   instance writes back, to each partition that is to change, the bytes
   that step 1 read from it.

Which PMP entries the resident firmware programs is learned from the
vendor's published source and, if M11's plan asks for it, from probe
images run as the MVP's are. Neither needs the amendment.

Never, under any amendment this revision foresees: a write to the NOR's
`bootinfo` or `fsbl` areas; an eFuse or any other one-time-programmable
bit (stop (a)); or a closed flashing tool. Cards and recovery use the
open `dd` and `fastboot` only; the R8 H0 freeze already excluded the
vendor's closed tool. The M1 plan's rule that `k3ctl`'s `recovery` is
never sent stands until the amendment decides it.

### S3-D.7 The claim

Unchanged by this revision, and S3-C's stop (d) stands. This revision
pre-authorizes a subject only: M11's plan may propose one clause about
the physical boundary, with its words fixed there and a form for each
outcome. The claim's present sentences about "the board's installed
firmware", which "no campaign step wrote", describe MVP 1.0 and stay
true of it. A board result under other firmware would need words of its
own, which M11's plan would fix with the clause.

### S3-D.8 Decisions D23 to D27, and the stops this revision adds

| ID | Open item and its source | Decision |
| --- | --- | --- |
| D23 | What MVP 2.0 starts with (S3-C.2; the human's directions of 2026-11-09 and 10; `ladder=boundary_first`) | M11, the physical boundary; then S3-C.2's seven steps in their order. M12 runs beside M11 (D27) and gates only MVP 2.0's last step. Memory protection tables on hardware, and CoVE, stay in MVP 3.0 |
| D24 | The word "domain" (the human: `make changes now to avoid clashes with SD terminology`; `naming=profile`) | The rule of S3-D.2, in documentation now. No identifier, image, or accepted text changes; new identifiers arrive with M11's code |
| D25 | The board's firmware (S3-A.1 items 1, 3, and 4; stop (a); the human: `we will change the NOR policy`; `board_firmware=staged`) | The direction is recorded, and no item of S3-A.1 changes. The amendment is its own exact commit, proposed when step 1's facts are known, with the staging of S3-D.6 |
| D26 | The attacker (the human: `we need to use assume breach model`; `attacker=post_activation`) | HS-mode code on a hart after that hart's activation joins the threat model, by security model v1 Part 1 Revision 4, as its own exact commit before M11's plan. Boot code before activation stays in the trusted base |
| D27 | Supervisor-domain support, which no upstream project had merged (the human: `any reason we can't implement that and contribute?`; `m12=lane_now`, `upstream_model=nameable`; then, with others' work read, `m12_shape=build_on` and `first_contact=work_first`) | The lane of S3-D.4: build on the work in progress, and contribute what it lacks. Questions on the specification, directed tests, and the table walk for the Sail model come first; then testing and review of the emulator and firmware series. No parallel implementation. Each destination's contribution policy is followed; anything bound for another project is written only with AI tools that can be disclosed by name; every submission is the responsible human's |

**Stop condition 1 amended by name.** Its exception list gains the
additive security model v1 Part 1 Revision 4 that M11 needs (M11-R8),
which goes to the responsible human as its own exact commit.

**The stops that stay.** The plan's stop conditions 1 to 7 and (a) to
(i) stand. M11 will run into several accepted rules. Its plan names each
one that its design would change, for the human's decision there: D8
("no HS time slice", and the monitor's firmware call surface); D15 (hart
start and IPIs); D16 and stop condition 3 (harts 3 to 7 never started,
against M11-R3's test of all eight); and S3-C's stops (e) and (i), with
the rule that the plain images equal MVP 1.0's byte for byte.

Stop conditions this revision adds to the plan's list (each returns the
work to the responsible human):

- **(j)** any board firmware step before the amendment of S3-D.6 is
  accepted: a write to the NOR other than S3-A.1 item 3's recorded
  `saveenv`, a card inserted to boot the board, a recovery or download
  mode entered, or a boot of the board under firmware, or a firmware
  device tree, other than its resident ones. The read-only inventory of
  S3-D.6's step 1 is not such a step;
- **(k)** naming a Beryllium unit a supervisor domain (or "SD"), an
  RDSM, or an SDSM, or giving one an SDID or an MPT, before M11's or
  M12's plan records that mapping as a decision. S3-D.2's reading of
  MVP 1.0 as a whole is not such a naming;
- **(l)** any change to an identifier, an image byte, an accepted text,
  or anything at the tag `mvp-1.0` in the name of terminology;
- **(m)** any M-mode code of ours, or firmware build of ours, that is
  committed here, run on the board, or cited as evidence for a claim,
  before M11's plan has fixed its language rules, licence, location,
  and build. The characterization's scratch harnesses, builds, and
  prototypes, run only under emulation, are not;
- **(n)** a boundary design in which M-mode takes a physical range, a
  profile, or a hart from HS-mode code after activation, or in which a
  confined hart can widen its own profile by any firmware call;
- **(o)** anything sent to another project other than by the
  responsible human; anything offered to a project whose contribution
  policy declines it; or anything bound for another project that was
  written with, or derives from work written with, an AI tool that
  cannot be disclosed by name, that carries text of this repository, or
  that has no record of the tool that wrote it.

### Accepted lines this revision supersedes

| Where | Text | Now |
| --- | --- | --- |
| S3-C.2, MVP 2.0's contents (L1279) | "In this order, each step a precondition of the next: (1) characterize the IOMMU/IOPMP, interrupt, reset, and device-ownership facts of the board; …" | M11 comes before step (1). M12 runs beside M11 and gates only the last step. Steps (1) to (7) keep their order (D23, D27) |
| S3-C.2, MVP 3.0's contents (L1280) | "MPT (memory protection tables), CoVE, CHERI, and policy composition", and the compatibility analysis as "2.0's last step" | Unchanged for hardware and for CoVE. Memory protection tables under emulation are MVP 2.0's M12; the compatibility analysis stays 2.0's last step and builds on it |
| Stop condition 1 (L692-L695), as S3-C amended it | the exception list | gains Part 1 Revision 4 (S3-D.8) |
| Glossary (a maintained document): hart, control hart, domain hart, protected domain | "not yet implemented", "not implemented", "Beryllium has never started a second hart" | implemented since M0 and M2; "VS-domain hart" beside "domain hart" |
| Glossary: PMP / Smepmp / ePMP | "Firmware PMP handoff and locks remain uncharacterized since R8 H1 was dropped; current work does not add broad HS PMP programming" | not used by MVP 1.0; the subject of M11 |
| Hardware roadmap (a maintained document): "Current R8 boundary"; "PoC records and validates the OpenSBI PMP/Smepmp handoff …"; "Smmtt or successor memory-tracking mechanisms" | | marked as history; PMP's planned use; the specification's present name |
| Roadmap, "Later phases" | MVP 2.0 named as "the device path and service domain, dynamic management, the policy questions H06 to H09, attestation with a simulated root of trust" | preceded by M11, with M12 beside it; that page carries a reading note and follows at its next status refresh |

Not superseded, each decided where shown: S3-A.1's items 1 to 8, the M5
plan's "No SD card", the M1 plan's `k3ctl` rule, and stop (a) (with the
amendment, D25); D8, D15, D16, stop condition 3, and S3-C's stops (e)
and (i) (in M11's plan, by name); the threat model's trust in the
monitor's code (with Revision 4); the claim (S3-D.7); and every accepted
record.

### Open questions and defaults

The numbering continues S3-C's (Q27 to Q46).

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q47 | The naming rule | S3-D.2: "VS domain" for ours, "physical access profile" for the new thing, the specification's words in its sense only. **Answered:** `naming=profile` | A new noun for the unit; or "supervisor domain (static, PMP-backed)" now |
| Q48 | Where the attacker begins | HS-mode code after the hart's activation; boot code before it trusted, its inputs untrusted and checked. **Answered:** `attacker=post_activation` | Boot code on a hart is an attacker too, which needs profiles that M-mode derives with no HS-mode part |
| Q49 | M11's steps under emulation | The VS-domain harts first, then the control hart. **Answered:** `m11_steps=domain_harts_first` | Both in one step |
| Q50 | The ladder | The boundary first in MVP 2.0. **Answered:** `ladder=boundary_first` | After the device path |
| Q51 | The board's firmware | The direction now; the amendment after the board's facts; a card before any NOR write. **Answered:** `board_firmware=staged` | Amend now; or emulation only |
| Q52 | Renaming `prot_t` and `prot_mem_t` | A separate, later sweep that changes images, with the new names decided then | Inside M11; or never |
| Q53 | The design | Chosen in M11's plan on the characterization's facts | Fixed now |
| Q54 | The CHERI check during M11 | A gate at M11's result; it may fail on the working branch in between | A gate throughout |
| Q55 | M-mode code of ours | The project's restricted-C and evidence rules; licence and location decided in M11's plan, before any is committed | Decided now |
| Q56 | Names | S3-D, M11, M12 | The human's |
| Q57 | How this revision's decision is recorded | As the status paragraph says: the sign-off of the proposing commit, with the record kept internally | A second commit here that sets a decision record, as S3-A to S3-C have |
| Q58 | M12 without a merged upstream stack | A lane beside M11 that builds on the work in progress and contributes what it lacks. **Answered:** `m12=lane_now`, then `m12_shape=build_on` | Our own implementations in parallel; or wait for the upstream pieces |
| Q59 | The emulator, given QEMU's contribution policy | The posted series' next version, pinned; a fork only for what M12 needs and the series still lacks; QEMU is offered test results, defect reports, and review, in the human's own writing. **Answered:** `m12_shape=build_on`, which replaces an earlier `qemu=fork` | Our own fork now; or ask QEMU's list for an exception |
| Q60 | Who writes what is bound for another project | Only AI tools that can be disclosed by name. **Answered:** `upstream_model=nameable` | Disclose AI use without naming a tool |
| Q61 | Who moves first on the lane | The project prepares the tests and the Sail table walk; the human writes to the authors when there is something to show. **Answered:** `first_contact=work_first` | The human writes first, and no work starts before that |

### What acceptance would authorize

Accepting this revision would record D23 to D27, the amended stop
condition 1, stops (j) to (o), the superseded lines, and Q47 to Q61 as
answered or at their defaults. It would authorize:

- the terminology rule and this commit's documentation changes;
- the characterization to its end, as S3-D.5 describes it, with reading
  for the supervisor-domain lane, and with a read-only inventory of the
  board from its own Linux in sessions that the human opens;
- the writing of security model v1 Part 1 Revision 4, of M11's bounded
  plan, and of M12's bounded plan, each as a proposal at its own exact
  commit. M12's plan may be proposed before M11's result.

It would authorize no implementation here; no M-mode code or firmware
build outside the characterization's emulation scratch; nothing written
for another project before M12's plan is accepted, and nothing sent to
one; no board command other than
that read-only inventory; no firmware write and no card; no claim-text
change; no change to an identifier, an image, or an accepted text; and
no push, merge, tag, or release step.

### Status record addendum

```text
s3_revision_s3d=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
s3_revision_s3d_base=a0d0b78b0ca83c4a084701f10ff2e1c9ce433a35
s3_revision_s3d_direction_dates=2026-11-09;2026-11-10
s3_revision_s3d_directions=assume-breach;a-boundary-between-the-monitor's-HS-parts;use-and-validate-platform-features-PMP-next;align-with-supervisor-domains-emulation-first;avoid-terminology-clashes-now;the-NOR-policy-will-change;raise-any-policy-that-forbids-a-direction;implement-memory-protection-tables-and-contribute
s3_revision_s3d_form_answers=ladder=boundary_first;board_firmware=staged;naming=profile;attacker=post_activation;m11_steps=domain_harts_first;m12=lane_now;upstream_model=nameable;m12_shape=build_on-replacing-qemu=fork;first_contact=work_first
s3_revision_s3d_decisions=D23-boundary-first-in-MVP-2.0;D24-domain-terminology-rule;D25-board-firmware-direction-staged-no-item-changed;D26-attacker-post-activation-by-Revision-4;D27-supervisor-domain-lane-builds-on-the-work-in-progress-and-contributes-what-it-lacks
s3_revision_s3d_milestones=M11-the-physical-boundary;M12-the-supervisor-domain-lane-beside-M11
s3_revision_s3d_requirements=M11-R1..M11-R10
s3_revision_s3d_stops=stop-1-amended-by-name;stops-1-7-and-a-to-i-stand;j-to-o-added
s3_revision_s3d_open_questions=Q47-Q61;answered-Q47-Q51-and-Q58-Q61;Q52-Q57-defaults
s3_revision_s3d_board_policy=unchanged;S3-A.1-items-1-8-and-stop-a-stand-until-the-amendment;read-only-inventory-before-it
s3_revision_s3d_claim=unchanged;subject-of-one-M11-clause-pre-authorized
s3_revision_s3d_design=not-selected;chosen-in-the-M11-plan
s3_revision_s3d_characterization=started-2026-11-10;reading-and-emulation-scratch-only;findings-recorded-in-the-M11-and-M12-plans
s3_revision_s3d_review=three-candidates-reviewed-independently-never-signed;this-text-answers-those-reviews
s3_revision_s3d_authorization_if_accepted=terminology-and-documentation;characterization-with-read-only-board-inventory;write-Revision-4-the-M11-plan-and-the-M12-plan;nothing-else
s3_revision_s3d_release=MVP-1.0-published-2026-11-08-tag-mvp-1.0-unchanged
```
