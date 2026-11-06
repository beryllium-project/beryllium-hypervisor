<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# Project snapshot as of MVP 1.0 release candidate 2

A point-in-time overview written on 2026-10-30, the day exact commit
`3867c66c5df2108e1051d8f8c44c12d62611e485` was accepted as MVP 1.0
release candidate 2. It answers, in one place, what Beryllium is for,
how it got here, what the MVP demonstrates, what can and cannot be said
about formal verification, how far it has moved from the Helium
pathfinder, and how the monitor would likely be covered by formal
verification later. It is a snapshot: the [roadmap](roadmap.md), the
[MVP plan](mvp-plan.md), the milestone records it cites, and the
[handoff](HANDOFF.md) stay authoritative, and the
`project-snapshot` skill derives the current position from them rather
than from this file. Every exact commit here is short; the records hold
the full SHAs.

## 1. Goal

Beryllium is a minimal RISC-V HS-mode security monitor: a small trusted
core that enforces isolation and resource ownership, with drivers, I/O
stacks, orchestration, and rich policy evaluation kept outside it in
separate domains. Its first purpose is to be a trustworthy and
experimentally useful substrate for security research and development
(implementation plan, "Problem statement").

**MVP 1.0** is the first release a security researcher can build from
source, run in QEMU and on a SpacemiT K3 COM260, and use to study
isolation between Linux-class domains under a declared policy, with
evidence that states exactly what was tested. It is deliberately
limited: three statically assigned harts of the board's eight, no
devices, a static configuration, and claims bounded to tests, emulation,
diagnostic board runs, and proofs about the abstract model
([MVP plan](mvp-plan.md#what-the-mvp-is)).

## 2. The ladder so far

| Phase | What it delivered | Accepted |
| --- | --- | --- |
| Helium pathfinders | five QEMU variants, including the fixed Type Enforcement PoC; the comparison selected ownership plus explicit channels, with capabilities and TE trigger-gated | before July 2026 |
| Architecture Model 0.1 and 0.2 | the abstract single-hart isolation contract, then the policy-neutral separation of proposals, sealed canonical state, and derived enforcement, with Rocq obligations and a C validator | 2026-07-22, 2026-07-24 |
| R0 to R7 (QEMU) | the single-hart runtime: the fixed-profile freeze, the pure-C mechanism, the Sv39x4 G-stage backend, boot and first VS entry, traps and context, the checked domain switch, 47 adversarial images, and R7's bounded exact-byte proof | 2026-07-27 to 2026-08-05 |
| B0 to B7 (K3) | the boot marker, first VS entry, the checked switch, the U-Boot `booti` shim, R6/R7 re-derived for the K3 images, the accepted-tool fixes, a bare-metal guest with a guest SBI subset, an unmodified Linux `v7.2` guest, two Linux guests on one hart | 2026-10-06 to 2026-10-09 |
| S1, S2, S3 | the Helium-to-Beryllium synthesis (59 lessons classified); security model v1 (a TE-family declarative policy as the specification, enforcement derived from it); the MVP plan | 2026-10-18, 2026-10-22, 2026-10-23 |
| MVP M0 to M5 | section 3 | 2026-10-26 to 2026-10-30 |

Dropped with records kept: the R8 formal K3 core-validation line (H0
accepted but blocked; H1 to H4 never authorized) and the KVM0
workstream, both on 2026-10-08.

## 3. MVP 1.0 milestones

| Milestone | Goal | Result |
| --- | --- | --- |
| M0 | the MVP line ported from B7 by a counted port; the multi-hart substrate (hart 0 the control hart; harts 1 and 2 each one domain; SBI HSM start, boot barrier, single-writer rings, SBI IPIs); the evaluation harness; the tool lock and the clean evaluator | accepted 2026-10-26, `b2669725` |
| M1 | the TE PoC scenario (`te-poc`): two Linux guests, one declared channel page, denials injected as faults and logged | accepted 2026-10-27, `ff84533c` |
| M2 | the anchor use case (`anchor`): a protected research domain holding a secret and an integrity-sensitive computation beside an untrusted Linux domain that may pause or terminate it but cannot read or alter it; a core-held measurement | accepted 2026-10-28, `18d552bc` |
| M3 | the policy layer in the Rocq model, with differential checking against the C offline checker | accepted 2026-10-28, `b0a0f352` |
| M4 | release candidate 1: the claim and its required limit, the claim ledger, the researcher guide, the AI-assistance disclosure, the clean evaluator evidence, a board campaign launched by Linux kexec | accepted 2026-10-29, `c5df0cfa` (**RC1**, now accepted history) |
| M5 (Plan revision S3-A) | release candidate 2: the board boots the candidate from system reset through the board's installed firmware and U-Boot, from a Beryllium partition on the NVMe; kexec removed from the tools and the claim; a U-Boot rehearsal in QEMU | accepted 2026-10-30, `3867c66c` (**RC2**) |

Debt sweep 1 (`80ef8a13`, accepted 2026-10-30) closed three cosmetic
items after RC2. The development branch `beryllium/single-hart-runtime-r0`
holds everything through that sweep's acceptance record.

## 4. The release path and the position

The MVP plan's release path, each step its own responsible-human
instruction (`LLM_POLICY_ALIGNMENT.md`; S1 H48):

1. the latest release candidate's exact commit is accepted — **done
   (RC2)**;
2. the responsible human selects the source, artifacts, and history
   that migrate;
3. a new clean public Beryllium repository is populated with only that
   reviewed material;
4. the gates run again there, giving a new exact commit;
5. the responsible human approves that exact public commit and its tag
   (**that tagged public commit is "MVP 1.0"**);
6. publication: the problem statement, the results, an invitation to
   review;
7. the internal repository is archived when the human decides.

**Direction taken on 2026-10-30:** release candidate 3 first. The
"MVP core profile" debt (the monitor still re-executes the frozen R3
synthetic prelude and carries unused fixture roots and pages; recorded by
M0 Plan revision M0-A.5, deferred by MVP plan D3 and S1 H22 to "after MVP
1.0 or with the clean-repository build root") is to be retired under its
own bounded plan, and its result presented as RC3, before steps 2 to 7
proceed. No plan is drafted yet; nothing starts without its instruction.

**After MVP 1.0** (implementation plan milestones 3 to 10, candidates,
none authorized): one protected domain with the full OS boundary
(dynamic management, notifications, lifecycle); the dynamic part of
serialized multicore with hardware validation; an external I/O service
domain with DMA containment; a first-class policy substrate if a trigger
fires; measured launch and attestation; conditional Arm portability; an
assurance release; an upstream or foundation-grade proposal.

## 5. What the MVP demonstrates

### The substrate

On the COM260, and in QEMU's eight-hart `virt` machine, hart 0 is the
control hart and harts 1 and 2 each run one unmodified upstream Linux
`v7.2` guest (uniprocessor, no devices, a static `nolibc` init) in its
own G-stage domain with its own VMID. There is no scheduler and no
device; the guests' console lines reach the operator through hart 0,
tagged `BE_MVP_G0: ` and `BE_MVP_G1: `. On the board the image boots
from system reset: U-Boot loads it from the `beryllium` partition under
a boot command installed in its saved environment for the session and
restored afterwards.

### A TE-family policy enforced between two Linux guests

The policy is a real Type Enforcement policy in security model v1's
notation (`mvp/scenarios/te-poc/policy.te`):

```text
type monitor_t;      type writer_t;       type reader_t;
type writer_mem_t;   type reader_mem_t;   type shared_wr_t;
class memory  { read write execute map }
class channel { send receive }
allow writer_t writer_mem_t : memory { read write execute map };
allow writer_t shared_wr_t  : memory { read write map };
allow writer_t shared_wr_t  : channel { send };
allow reader_t reader_mem_t : memory { read write execute map };
allow reader_t shared_wr_t  : memory { read map };
allow reader_t shared_wr_t  : channel { receive };
```

It is **checked offline** by `mvp/tools/policy-check.py` (analyses A1 to
A8; a deterministic authority report) against the scenario's labeling
and manifest, and the monitor **enforces the mappings derived from it**:
the G-stage leaves carry exactly the granted rights (the writer's PTE
low byte `0xd7`, read-write; the reader's `0x53`, read-only; the
`CHANNEL_CHECKED` line prints both and checks them against the sealed
record). An access outside the declared rights is a guest page fault
that the domain hart turns into an injected access fault into the guest
and a `BE_MVP:DENY` record on hart 0. What there is **not**: a runtime TE
check (no label lookup or access-vector cache at access time);
enforcement is derived from the specification, as S1 H59 and Model 0.1
revision M01-A state. The accurate phrase is "a TE-family policy as the
specification, enforced through derived G-stage mappings".

### What the guest user space does

`mvp/guest/mvp-init.c` is a static `nolibc` program running as PID 1 in
each guest:

- **`te-poc`.** The writer maps the channel page through `/dev/mem`,
  writes 4,088 bytes of an xorshift pattern and a flag word, and prints
  the pattern's FNV-1a digest; the reader polls the flag, reads the
  pattern, and prints the same digest with `match=1`. Each then forks a
  child that performs the denied accesses on purpose (the reader stores
  to the read-only page; each loads from the other's private window or
  an unmapped address), catches `SIGSEGV` with `SEGV_ACCERR`, and prints
  `MVPINIT 08 DENIED … observed=1 unchanged=1`. Each such line pairs
  with the monitor's `BE_MVP:DENY` line (cause, injected cause, GPA,
  `htval`). `RESULT pass` requires all of it.
- **`anchor`.** The protected domain reads a 32-byte secret that only it
  maps and serves requests from the untrusted host over a request page
  and a response page (HMAC-SHA-256 keyed by the secret); the host's
  tested attempts to read the secret, alter the result, and reach the
  protected domain's private window and the monitor's region each
  fault; the host then pauses and terminates the protected domain
  through a versioned SBI management extension (a loadable `be-mgmt.ko`
  and `/dev/be-mgmt`), and the monitor prints the domain's measurement
  unchanged.
- **`two-guests`.** The substrate alone: both guests compute, sleep, and
  power off; no policy.
- **The negatives.** `reader-write`, `no-inject`, `payload`,
  `wrong-measurement`, and `no-grant-check` are images that must fail
  with their declared marker: the system fails closed.

### What to record

Every command is in `mvp/docs/guide.md`.

1. `./mvp/mvp qemu`, or one scenario: the console from `BE_MVP:01` to
   `BE_MVP:14`, the two Linux boots, `CHANNEL`, the three paired
   `DENY`/`DENIED` lines, `RUN_COMPLETE`; the guide's section 3 narrates
   a `te-poc` run line by line.
2. The `anchor` run: `REQUEST`/`RESPONSE` digests, the denied secret
   read, `DOMAIN_PAUSED` and `DOMAIN_TERMINATED`, the measurement line.
3. The board: the serial console from `k3ctl reset` through U-Boot's
   `md5 for …` and `Moving Image from 0x140000000 to 0x108000000` to the
   same story on hardware, about fifteen seconds.
4. The offline policy: `policy.te`, the authority report (guide section
   6), then a negative (`policy-negatives`: a grant without a rule fails
   A8; a secret flow fails A3): a configuration that must not be sealed
   is refused before any image exists.
5. `./mvp/mvp evaluate`: every image byte-identical between the host and
   the pinned evaluator (253 of 253 at RC2).

### What it does not demonstrate

Dynamic policy or management, a runtime TE check, devices or DMA,
attestation (the measurement is a local identity), performance,
microarchitectural isolation, availability, or anything about the harts
that are never started. Board results are diagnostic bring-up evidence
for one board, one SBI identity, and one U-Boot build, never hardware
validation (`mvp/docs/claim.md`, "Required limit").

## 6. Formal verification: what can be said

- **Proofs about the abstract model (Rocq, `model/proof/`).** Model 0.1
  and 0.2 with M3's policy layer: 77 theorems and lemmas, no admits:
  unique private ownership and monitor exclusion, derived-root
  soundness, derived rights bounded by grants, directional channel
  confinement, sealing only after validation and no publication after a
  failed validation, the static hart binding (H0 to H3), and the
  soundness of A6, A7, and A8 over the three instances.
- **Differential agreement.** The C offline checker agrees with the Rocq
  policy model on the instances and 91 seeded mutations (M3). The C is
  not the proved function; the agreement is a bridge, not a proof.
- **R7's bounded exact-byte proof (Rocq, 139 theorems and lemmas).**
  Over the accepted R5 single-hart images' bytes (1,420 words, 22
  symbols): bounded, not whole-system, and it does not cover the MVP
  monitor.
- **Not proved: the MVP monitor's implementation.** The boot barrier,
  the rings, the IPI protocol, the control loop, the G-stage builder,
  the denial path, the management decision, and the measurement are
  covered by host tests, image and capture checks, emulation, and the
  board runs, and by nothing else. The claim's required limit says so,
  and the forbidden-phrasing list bans the umbrella phrases.
- **CBMC is not used.** The Beryllium MVP line has never run CBMC; the
  recorded stack is Rocq-first with Cerberus as the C semantics
  reference. Helium's final line added eight tiers of bounded CBMC
  checks; S1 classified that work as deferred (H38, H41), a candidate
  for the assurance milestone, not an adopted method.

The honest one-line framing: a machine-checked model and a tested
implementation.

## 7. The gap between the final Helium commit and Beryllium now

| | Helium `1c9e526` (`v0.6.0`, 2026-09-09) | Beryllium RC2 `3867c66c` (2026-10-30) |
| --- | --- | --- |
| Platform | QEMU only, one hart | QEMU and the COM260, three harts (a control hart and one per domain), booted from system reset through U-Boot |
| Subjects | two sequential bare-metal VS subjects | two concurrent unmodified Linux `v7.2` guests with `nolibc` user space |
| Policy | the monitor assigns TE labels at initialization; one fixed `te` policy; offline policy JSON emitted | the TE-family policy is the specification, checked offline (A1 to A8, an authority report); enforcement derived; `anchor` adds a `domain { pause terminate }` class and a management extension |
| Shared page and denials | one shared page, writer read-write and reader read-only, cross-private accesses denied | the same pattern on hardware, plus the protected-domain anchor: a secret, an HMAC service, pause and terminate, a measurement |
| Assurance | bounded CBMC over production C in eight tiers; no Rocq | Rocq abstract model and policy layer, differential agreement with the C checker, R7's bounded byte proof; no CBMC |
| Process | a review-and-test PoC with a publication gate; GPL-3.0-only | exact-commit acceptance per milestone; a claim ledger of 39 rows with hashes; a pinned tool lock and a clean evaluator; retained board records; a forbidden-phrasing checker; an AI-assistance disclosure |
| Status | a frozen snapshot (`for-review` at `f928aac` differs only in its handoff) | active: MVP 1.0 M0 to M5 accepted, release path step 1 |

Of Helium's 59 lessons, S1 adopted 34, adapted 15, rejected 2, and
deferred 8. The three gaps it named before any isolation claim between
Linux guests (no shared-page or denial test between Linux guests on K3;
`htval` unrecorded on K3; VMID tagging untested) were closed by M0 and
M1 (`probe-platform`, `probe-vmid-distinct`, `probe-vmid-shared`, and
`te-poc` on the board).

## 8. How the monitor would likely be covered by formal verification

The recorded direction (implementation plan, "Selected C implementation
boundary", "Selected proof ecosystem", "Selected binary-assurance
staging"; S1 H22, H38, H41) fixes the shape. Against the monitor as it is
(about 7,300 lines of C and 1,200 of assembly under `mvp/src/` and
`mvp/shim/`, plus the accepted R3 prelude):

**What exists to build on:** the Rocq model with its proved properties
(the specification side); the differential agreement with the C checker
(a bridge); R7's technique, Rocq RV64 semantics over exact image bytes
with cut points, proved on 1,420 words (the assembly side); and pure-C
decision functions already host-tested with identical GCC and Clang
output (rings, hart blocks, control loop, SBI core, G-stage builder,
denial decision, management decision, SHA-256).

| Stage | What | Tooling | Notes |
| --- | --- | --- | --- |
| 0. Seams (fold into RC3) | Make the plan's three layers explicit: a proof-bearing subset of pure decision functions over captured inputs (barrier, ring protocol, G-stage derivation, denial decision, management decision, measurement); one executor that performs the privileged effects (CSR and `hgatp` writes, `hfence`, IPIs, ring publication); the thin assembly boundary with a contract per function. Freeze the restricted-C rules. | none | S1 H22 is this shape; the core-profile rewrite is the natural moment, so RC3 becomes the proof target. Expect a proof-bearing subset of roughly 2,500 to 3,500 C lines. |
| 1. Concrete model | Extend `model/proof/` to the MVP's operational model: hart blocks, single-writer rings with generation words, the barrier, the denial path, pause and terminate, the measurement; re-prove the existing properties over it; the three-hart concurrency under static ownership with the RVWMO fences as explicit axioms. | Rocq | Additive to M3's development; the ring and barrier protocol is the new hard part. |
| 2. C refinement | Prove the proof-bearing C functions refine the stage-1 functions. | Cerberus as the semantics reference; candidates to evaluate side by side on the same leaf: a CN pilot, Frama-C/WP with ACSL contracts (see the note below), VST's BSD distribution or RefinedC after their license and community gates | The differential harness stays the bridge until proofs land. Frama-C's Eva and CBMC bounded checks for the support code (Helium's tiers are a template); not load-bearing. |
| 3. Assembly | Cut-point contracts for the trap vector, the resume tail, hart entry, the `hgatp` write, fence, and readback, and the shim; R7-style exact-byte proofs. | Rocq, with the project's own H-extension subset semantics (upstream Sail lacks H) | About a thousand instructions against R7's 1,420 words; feasible with R7's machinery once the bytes are frozen. |
| 4. Source-to-binary | Open translation validation of the proof-bearing subset for the pinned GCC and Clang. | Isla and Islaris, seL4-style methods; Isabelle allowed as load-bearing here | The open-tooling gap and a tracked side project. Until it exists the compiler is an explicit assumption and any release is pre-assurance. |
| 5. Assurance case | Explicit assumptions (OpenSBI's HSM and IPI semantics, the firmware state of harts 3 to 7, the memory model, the hardware), trusted boundaries, non-claims, the profile-neutral crosswalk. | documents | What could then be said: the proof-bearing subset is proved to refine a model with these properties, under these assumptions. |

**Note to evaluate (2026-10-30): Frama-C/WP as a stage-2 vehicle.**
Frama-C has been in the project's open tool set from the start
([open tooling](open-tooling.md): the core with open plugins such as Eva
and WP), was piloted once in the original pathfinder's sequential C
verifier pilot (Frama-C 32.1 WP, 91 of 91 goals proved from ACSL
contracts and runtime-error obligations through Qed and Z3, with a Why3
version-qualification warning retained;
[pathfinder evidence](pathfinder-evidence.md)), and the
[high-assurance sidebar](sidebar-high-assurance-standards.md) lists
Frama-C/WP beside Rocq/VST and RefinedC for C contracts and refinement.
The implementation plan positions "Frama-C open plugins" for broad
static and bounded checks, and the route above first named only CN, VST,
and RefinedC for refinement; WP has not been weighed for the MVP
monitor's proof-bearing subset. The first bounded verification plan
should evaluate it on the same leaf as the CN pilot (`mvp-ring.c`, then
the G-stage derivation), on: expressing the stage-1 Rocq specification
as ACSL contracts without loss; WP's aliasing and memory models against
the monitor's restricted C (fixed arrays, no function pointers, volatile
MMIO kept in the executor); discharge through Alt-Ergo, Z3, and cvc5 as
independent backends and, for goals SMT cannot close, WP's export to
Rocq, which is the natural bridge to the model; the gap between an
ACSL-proved function and a Rocq refinement statement (what remains an
assumption); and tool qualification (Fedora-packaged Frama-C and Why3
versions, the pathfinder's Z3 warning). Outcome wanted: one of CN, WP,
or VST selected for the subset with the others as cross-checks, or a
recorded reason to keep more than one.

Outside even that: microarchitectural noninterference, availability,
whole-system verification (the guests, the firmware, the hardware), and
any umbrella claim; the assurance milestone's gate requires open binary
correspondence or a clearly labelled pre-assurance release.

Functional-correctness proof developments run at large proof-to-code
ratios; bounding the subset and reusing the model keeps the work
tractable, but stages 2 and 4 are each multi-milestone efforts. The
pragmatic first bounded plan would be stage 0 inside RC3 plus the
stage-1 ring, barrier, and denial model and a CN pilot on `mvp-ring.c`:
small enough to learn whether CN or VST is the right vehicle before
committing further.

## 9. Boundaries in force

- **Standing rule:** Beryllium does not use kexec from here on; a truly
  needed use is stated to the responsible human and waits for approval
  (Plan revision S3-A, decision 8).
- **Evidence:** board runs are diagnostic bring-up evidence on one
  COM260, not hardware validation; the proofs are about the abstract
  model and R5's bytes, not whole-system verification; the monitor is
  tested, not proved.
- **Publication:** the repository is private; no tag, release, or public
  push; every release-path step needs its own instruction; automation
  never approves a release or adds a human sign-off
  (`LLM_POLICY_ALIGNMENT.md`).
