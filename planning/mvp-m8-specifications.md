<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# MVP M8 specifications: stage 1's properties and the pilot's contracts

**Revision 1 (2026-11-03; accepted the same day at exact commit
`93a8d136`, instruction `accept 93a8d136`; as presented: proposed, not
accepted).** This is the specification's Revision 1: the accepted text of exact commit `004f31ae`
(SHA-256 `ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d`,
accepted 2026-11-02) with nine clauses corrected where the pilot's arms
found the accepted wording to disagree with the leaves as the accepted M1
plan and the ring header's contracts fix them (the M8 plan's stop 2,
decided by the responsible human on 2026-11-03: a Revision 1, re-frozen,
then the arms re-run against it). Each corrected clause is marked
**[R1-n]** in place, and the section "Revision 1" at the end lists the
nine with the accepted wording, the corrected wording, the evidence, and
the reading (specification erratum, not a code defect: no monitor source
changes). The stage-1 property list P1 to P9 and sections 6 and 7 are
unchanged, so the stage-1 modules' citation of the accepted hash stands
as a citation of the text they proved against (their errata S-1 to S-4
are the M8 plan's, recorded there); the arms cite this revision's hash.

This document is M8-2's specification, under the accepted
[M8 plan](mvp-m8-plan.md) (`7a0c74ae`; D-6, D-7, D-8). It states, in
prose with a formal reading, the **stage-1 property list** P1 to P9 that
the concrete operational model must prove, the **contract of Leaf A**
(`be_mvp_denial_decide` and its four static helpers) that every C arm
must state and prove, and the **per-call properties of Leaf B**
(`mvp-ring.c`'s public functions) that bounded model checking must
establish. It is **drafted from the plans and the claim, not from the
C** (S3-C's D22): its sources are the M0 plan with M0-A to M0-C (the hart
region, the rings, the barrier, the drain), the M1 plan (the denial
path: the accepted entry and the injected values), the M2 plan (the
pages, the management extension, the measurement), security model v1
with Revisions 1 and 2 (I13 to I18; A6 and A8), `Binding.v`'s H3 and
`Policy.v`'s A6 and A8 as M3 proved them, `InputRing.v`'s T1 to T4, and
the claim. The one recorded exception: the drafter read the M8 fact
sheet of 2026-11-02, which quotes the leaf's declaration and contract
comment (`mvp/src/mvp.h`), the ring header's contract comments
(`mvp/src/mvp-ring.h`), and the parameter types' definitions; the
drafter did not open `mvp-sbi.c` or `mvp-ring.c`. Where this document
and the C disagree, the proof attempt finds it and the plan's stop 2
(the defect protocol) or stop 4 (a property the plans cannot state)
applies; this document is not edited to match the C.

**Freeze.** This document is its own exact commit; its SHA-256 is
recorded in the M8 plan's status block (`m8_specifications=`) and cited
in the header of every stage-1 module and every arm's annotation file.
The responsible human is its **reviewer of record**; proof drafting may
start against the frozen hash (the plan's Q12), and a change from the
review re-freezes the hash and re-runs every proof that cites it.

## 1. Notation and the memory semantics

- **Harts.** `H = {0, 1, 2}`: hart 0 the control hart, hart 1 running
  domain 0, hart 2 running domain 1 (`mvp_binding`, `Binding.v`).
  `hart(d)` is the hart of domain `d`.
- **Words and objects.** The shared state is a finite set `W` of
  64-bit-aligned words, each in exactly one **object** of `Binding.v`'s
  `hart_object` where one exists (the ring index lines, the descriptors
  with their generation words, the first-entry frames, the walked maps
  and leaves, the configurations, the binding table, the control data)
  or in one of the objects stage 1 adds (each ring's buffer bytes, each
  state page's counters and phase, the input rings' words as
  `InputRing.v` names them). `writer(o, φ)` is the one hart that may
  write object `o` in phase `φ ∈ {BeforeBarrier, AfterBarrier}`
  (`Binding.v`'s `footprint`, I15, I16).
- **Steps and traces.** Each hart is a labelled transition system whose
  steps are the protocol steps of section 2, each step a finite set of
  word reads followed by a finite set of word writes by one hart. A
  **trace** is a finite interleaving of the three harts' steps from the
  initial state (every word zero but the loaded image), each read seeing
  the most recent write to its word in the trace: **sequentially
  consistent interleaving**. Every stage-1 theorem is a statement about
  all traces of this semantics and is labelled so; nothing is promoted
  beyond it (the plan's D-3).
- **Ordering premises.** Five premises, `L1` to `L5`, name what the
  compiled code's fences and dependencies must provide for the SC
  semantics to describe the hardware's behaviour (the plan's D-3 table).
  A theorem that would be vacuous without one takes it as a hypothesis,
  written `respects(L_i)` on the trace, and the litmus table discharges
  each `L_i` separately. `L1` the barrier's publication order; `L2` a
  ring's publish order; `L3` a ring's release order; `L4` the writer's
  control dependency on its room check; `L5` the input ring's drop under
  `room`.
- **Values.** `N` the naturals; `u64 = N mod 2^64` for the ring indices
  (the plan's Q5); `bytes` finite sequences over `0..255`; `||`
  concatenation; `SHA-256 : bytes → bytes_32`, a function (its
  properties are not assumed beyond being a function).

## 2. The protocol steps stage 1 models

Each step names its hart, its phase, the `Binding.v` transition it
refines (obligation 1 of the plan's D-1 requires its writes within that
transition's `footprint`), and its plan source.

| Step | Hart | Phase | Refines | Source |
| --- | --- | --- | --- | --- |
| `prepare`: validate, seal, and derive the configuration; build the roots | 0 | before | `Prepare` | M0 plan "Boot sequence"; M6 (the core profile) |
| `publish(d)`: fill domain `d`'s block (descriptor, first-entry frame, walked map and leaves, configuration, both ring index pairs reset), then the generation word last | 0 | before | `Publish` | M0 plan L384-L388 |
| `start(d)`: SBI HSM start of `hart(d)` | 0 | after | `Start d` | M0 plan |
| `ready(d)`: `hart(d)` checks its hart id and the generation word, posts READY | `hart(d)` | after | `Ready d` | M0 plan L410-L412 |
| `enter(d)`: first entry into domain `d` (after the launch gate; stage 1 models the gate as a predicate on the pre-entry state, M9's content abstracted) | `hart(d)` | after | `Entered d` | M2 plan "The measurement"; M9 plan D-2 (abstracted) |
| `post(r, rec)`: the writer of ring `r` copies record `rec` past its cursor | `writer(r)` | after | `ExitRecord d` / `Ping d` / … (by ring and record) | M0 plan L340-L353 |
| `publish_ring(r)`: the writer sets `head(r) := cursor` | `writer(r)` | after | the same | M0 plan |
| `acquire(r)`: the reader reads `head(r)` | `reader(r)` | after | `Drain d` / `Pong d` / … | M0 plan |
| `take(r)`: the reader copies the next record at its cursor | `reader(r)` | after | the same | M0 plan |
| `release(r)`: the reader sets `tail(r) := cursor` | `reader(r)` | after | the same | M0 plan |
| `room(r)`: the writer reads `tail(r)` and computes the free payload | `writer(r)` | after | (input ring) | M7 plan D-1, D-4 |
| `drop(r, n)`: the input ring's writer counts `n` bytes it did not post | 0 | after | (input ring) | M7 plan D-4; `InputRing.v` T3 |
| `drain`: hart 0 takes at most one record from domain 0's outbound ring, then at most one from domain 1's, repeating while either has one | 0 | after | `Drain d` | M0-C.1 |
| `exit(d, e)`: `hart(d)` saves exit record `e`, decides it, and either resumes, denies (posts DENIAL, injects), serves (console, time, SRST, management), or fails | `hart(d)` | after | `ExitRecord d` / `Request d` | M1 plan "The denial path"; M2 plan |
| `decide_mgmt(q)`: hart 0 decides a management request against the sealed grants and delivers or answers | 0 | after | `DecideDeliver d` / `Answer d` | M2 plan L394-L406 |
| `park(d)`: `hart(d)` takes PAUSE or TERMINATE, posts PAUSED or TERMINATED, parks | `hart(d)` | after | `Pause d` / `Terminate d` / `Park d` | M2 plan |
| `fail(d)`: `hart(d)` posts FAIL and waits | `hart(d)` | after | `FailRecord d` | M0 plan; M1-B |
| `end`: hart 0 ends the run (budget or both domains down) | 0 | after | `RunEnd` | M0 plan |

## 3. The stage-1 property list

Each property is stated for every trace of the SC semantics (section 1),
with its premises, its source, and the names of the theorems that must
prove it (the module may split a property into several theorems; the
assumption report must be closed for each).

**P1 Barrier publication.** If `hart(d)` reads the generation word of
its block equal to the published value in step `ready(d)`, then every
word hart 0 wrote in `publish(d)` before writing the generation word
holds, at that read, the value `publish(d)` wrote. *Premise:* `L1`.
*Source:* M0 plan L384-L388, L410-L412; I16's "immutable published
data". *Theorems:* `barrier_publication`.

**P2 Single writer per word per phase.** For every step `s` of a trace
and every word `w` the step writes, `hart(s) = writer(object(w),
phase(s))`; before the barrier only hart 0 writes; after it the shared
words are immutable published data (never written) or ring words whose
records and head are written only by the ring's writer and whose tail
only by its reader; a domain hart's stack, saved frame, and private
state-page words are written and read by that hart alone. *Premise:*
none. *Source:* I15, I16; `Binding.v` H3. *Theorems:*
`concrete_step_within_footprint` (obligation 1: for every step, its
write set is within `footprint mvp_binding (refines s)`),
`single_writer_carried` (H3 instantiated on the concrete steps).

**P3 Ring safety.** For each ring `r` with capacity `C` (a power of two
in `[512, 32768]`): (a) `head(r) − tail(r) ≤ C` in `u64` after every
step (no overrun); (b) a `take(r)` reads only buffer positions in
`[tail, head)` (nothing unpublished); (c) `head(r)` and `tail(r)` are
non-decreasing in `u64` difference along the trace and each advance is a
multiple of 8; (d) a `post(r, rec)` on a **control ring** with
`head − tail + size(rec) > C` performs no buffer write and fails the
writer's view, which stays failed (M0 deliverable 5); (e) a `post` on an
**input ring** happens only after a `room(r)` whose answer is at least
the record's payload, else the bytes are dropped and counted by `drop`
(M7-3). *Premises:* `L2`, `L3`, `L4`, and `L5` for (e). *Source:* M0 plan
L340-L353; M7 plan D-1, D-4; `InputRing.v` T3. *Theorems:*
`ring_no_overrun`, `ring_take_published_only`, `ring_indices_monotone`,
`control_ring_fails_closed`, `input_ring_drops_under_room`.

**P4 Ring integrity.** Every record a `take(r)` returns equals, byte for
byte, a record some earlier `post(r, ·)` wrote and `publish_ring(r)`
published, records are taken in the order they were posted (FIFO), and
the record's type is in the ring's type set. *Premises:* `L2`, `L3`.
*Source:* M0 plan L340-L353 ("a record is a 16-byte header … and at most
256 payload bytes"). *Theorems:* `ring_fifo_integrity`,
`ring_type_set`.

**P5 Denial.** In `exit(d, e)` with `e.scause ∈ {20, 21, 23}` on a hart
whose image accepts denials: the exit is **denied** exactly when
`Entry(e, d)` of section 4 holds (the GPA lies outside domain `d`'s
window and every page its root maps, for any of the three causes, or
`e.scause = 23` and the GPA lies in a page whose leaf lacks `W`); a
denied exit posts exactly one DENIAL record carrying the entry's fields
and the injected `vscause ∈ {1, 5, 7}` before the domain resumes; an exit
with `e.scause ∈ {20, 21, 23}` that is not denied fails the domain (no
resume). Further, the rights the decision consults (the window and the
leaves' `W`) are those the sealed instance derives for domain `d`: for
`te-poc` and `anchor`, every mapping and right of domain `d`'s root is
one `Policy.v`'s A8 admits for the generated instance, and the only
cross-domain flow (`F`) is the declared channel (A6). *Premise:* none.
*Source:* M1 plan "The denial path"; M2 plan; security model v1 Part 5
(U2: the denial is the absent mapping's); A6, A8. *Theorems:*
`denial_iff_entry`, `denial_record_before_resume`,
`roots_from_instance` (obligation 2: the concrete roots and leaf rights
are computed from `Instances.v` and satisfy `Policy.v`'s A8 for the
instance), `flow_is_declared_channel` (A6 applied).

**P6 Management.** A `pause` or `terminate` request from domain `d` is
decided by hart 0 alone in `decide_mgmt`, as `INVALID_PARAM` (unknown
target), `DENIED` (no grant from `d` for that FID on the target, the
requester itself included), `INVALID_STATE` (the target terminated, shut
down, paused for `pause`, or with a request pending), or delivered;
delivery posts PAUSE or TERMINATE to the target's inbound ring; a target
that takes it parks and takes no further step but `fail` or `end`'s
observation (never resumes); at most one request is pending per domain;
every request is answered or refused exactly once; the grants consulted
are the sealed instance's (A8). *Premise:* none. *Source:* M2 plan
L382-L406. *Theorems:* `mgmt_decided_by_control_hart`,
`mgmt_outcome_from_grants`, `parked_never_resumes`,
`mgmt_one_pending_per_domain`, `mgmt_answered_once`.

**P7 Measure before entry.** `enter(d)` occurs in a trace only after the
launch-gate predicate for domain `d` holds on the state (the gate's
content is M9's and is abstracted as a predicate on the placed bytes and
the image's expected value); a trace in which the gate is false for `d`
has no `enter(d)` and no `start(d')` for any `d'` (the run fails before
any hart starts). *Premise:* none. *Source:* M2 plan "The measurement";
M9 plan D-2 (R4). *Theorems:* `entry_after_gate`, `gate_false_no_start`.

**P8 Drain.** Hart 0's `drain` takes at most one record per domain per
pass, alternating domain 0 then domain 1, until both outbound rings are
empty; each ring's records are taken in posting order (P4). *Premise:*
`L2`, `L3`. *Source:* M0-C.1. *Theorems:* `drain_round_robin`,
`drain_in_order`.

**P9 Input routing (inherited).** `InputRing.v`'s T4: a byte hart 0
delivers to an input ring goes to the current focus, a domain whose
sealed configuration grants console input and which is running, and to
no other; T1 to T3 for the input ring's words and drop rule. *Status in
stage 1:* inherited by import, listed in the lineage table as
`inherited`; the concrete model's input-ring steps are those of
`InputRing.v`. *Source:* M7 plan D-1, D-3; I17.

**Lineage table.** Beside P1 to P9, `ConcreteClaims.v`'s index comment
and the evidence record classify each of Model 0.2's 24 theorems and
M3's 22 as `inherited` (holds by import on the shared vocabulary),
`re-proved` (restated and proved over the concrete model), `strengthened`
(a stronger concrete statement proved), or `inapplicable` (about the
fixed single-hart profile's objects the MVP does not run, with the
reason; `Model.v`'s closed inductives, Q35).

## 4. Leaf A: the contract of `be_mvp_denial_decide` and its helpers

The leaf decides one guest-page-fault exit against the denial entry. Its
inputs are the hart's private state (`state`), its walked window (`map`),
its walked leaves of the root's pages (`leaves`, at most three; a page
with zero bytes is absent), and the exit record the vector saved
(`record`); its one output is `out`. Every input is read through a
`const` pointer; nothing else is written. The contract is stated in a
tool-neutral form; each arm transcribes it (ACSL for WP; CN's
specification language for CN) without strengthening or weakening it,
and the transcription is recorded beside the arm's result.

### 4.1 Definitions

- `SPV(h) = bit 7 of h`, `SPVP(h) = bit 8 of h`, `GVA(h) = bit 6 of h`
  for an `hstatus` value `h` (the RISC-V privileged specification,
  "Hypervisor Status Register"; the M1 plan's table).
- `GPA(record) = (record.htval << 2) | (record.stval & 3)`.
- `OPCODE(i) = (i >> 2) & 0x1f`; `LOAD = 0x00`, `STORE = 0x08`, `AMO =
  0x0b`.
- `HTINST_OK(scause, i)` holds iff `i = 0`, or (`i < 2^32` and `i & 1 =
  1` and ((`scause = 21` and `OPCODE(i) = LOAD`) or (`scause = 23` and
  `OPCODE(i) ∈ {STORE, AMO}`))). For `scause = 20` only `i = 0` holds.
- `INSIDE(a, base, n)` holds iff `base ≤ a < base + n` (no wrap; see the
  preconditions).
- `MAPPED(gpa)`: `INSIDE(gpa, map.gpa_base, map.size)` or some page `p`
  of `leaves` with `p.bytes > 0` has `INSIDE(gpa, p.gpa, p.bytes)`.
- `PAGE(gpa)`: the page `p` of `leaves` with the lowest index such that
  `p.bytes > 0` and `INSIDE(gpa, p.gpa, p.bytes)`, if any.
- `W(p)` holds iff bit 2 of `p.pte` is set.
- `ACCESS_FAULT(scause) = 1, 5, 7` for `scause = 20, 21, 23`.
- `VSTVEC_MODE(v) = v & 3`.

### 4.2 The entry

`Entry(state, map, leaves, record)` holds iff all of:

| | Condition | Source |
| --- | --- | --- |
| E1 | `state.accept_denial = 1` | M1 plan: a scenario whose accepted-exit set names `denial` |
| E2 | `record.frame.scause ∈ {20, 21, 23}` | M1 plan, "The accepted entry" |
| E3 | `SPV(record.hstatus) = 1`, `SPVP(record.hstatus) = 0`, `GVA(record.hstatus) = 1` | the same: from VU mode, `stval` a guest virtual address |
| E4 | `record.frame.htval < 2^39` | the same: the GPA below Sv39x4's 2^41 |
| E5 | `HTINST_OK(record.frame.scause, record.htinst)` | the same: zero or a transformed load/store/AMO, never a pseudoinstruction |
| E6 | `VSTVEC_MODE(record.frame.vstvec) ∈ {0, 1}` | the same: Direct or Vectored |
| E7 | `¬INSIDE(GPA(record), map.gpa_base, map.size)` (the GPA is outside the window; a fault inside the window is refused whatever the cause, the M1 plan's "a fault inside the window … stay[s] terminal"), and then either **unmapped**: `PAGE(GPA(record))` does not exist; or **read-only**: `record.frame.scause = 23`, `PAGE(GPA(record))` exists, and `¬W(PAGE(GPA(record)))` **[R1-1]** | the same, "Place": a GPA the root does not map (outside the window and the channel page), for any cause; or cause 23 at a GPA in a declared page whose leaf lacks `W` |

`KIND = 0` (unmapped) when E7's unmapped case holds and `1` (read-only)
when its read-only case holds. A fault inside the window (any cause), a
fetch from or a load of a declared page, a store to a writable declared
page, a fault from VS mode, a pseudoinstruction, an `htval` at or above
2^39, and any other `scause` are refused. `MAPPED` of 4.1 is not used by
E7 after Revision 1; it is kept as a definition for the reading "the GPA
is inside the window or inside a declared page".

### 4.3 Preconditions

- `state`, `map`, `leaves`, `record`, and `out` are valid, non-null,
  non-aliasing pointers to complete objects of their types (`out` is
  separated from every input).
- `map.size > 0` and `map.gpa_base + map.size` does not wrap in 64 bits;
  for every page `p` of `leaves`, `p.gpa + p.bytes` does not wrap (the
  walked map and leaves are the hart's sealed, derived roots: a 64 MiB
  window at a GPA below 2^41 and 4 KiB pages below 2^41). A `map` with
  `size = 0` is not a walked window: the leaf refuses every exit under it
  (the result is `0`), which the host test pins, and the contract's
  result clause is stated for `size > 0` only **[R1-2]**.
- No other precondition: every value of `record`'s fields is admitted
  (they are the hardware's).

### 4.4 Result and postconditions

- **Result.** `1` iff `Entry(state, map, leaves, record)`; else `0`.
- **On 1**, `out` holds: `cause = record.frame.scause`; `kind = KIND`;
  `gpa = GPA(record)`; `htval = record.frame.htval`; `htinst =
  record.htinst`; `stval = record.frame.stval`; `sepc =
  record.frame.sepc`; `vsstatus = record.vsstatus` (the guest's at the
  exit); `vstvec = record.frame.vstvec`; `time = record.time`;
  `inject_vscause = ACCESS_FAULT(record.frame.scause)`; `inject_vstval =
  record.frame.stval`; `inject_vsepc = record.frame.sepc`;
  `inject_vsstatus =` `record.vsstatus` with bit `SPP` (bit 8) set to
  `SPVP(record.hstatus)` (that is, cleared), bit `SPIE` (bit 5) set to
  the value of bit `SIE` (bit 1), bit `SIE` cleared, every other bit
  unchanged; `resume_pc = record.frame.vstvec & ~3`.
- **On 0**, every field of `out` is `0`.
- **Frame.** The function writes `*out` and nothing else; it reads no
  object but the four inputs.
- **Runtime errors.** Under the preconditions no undefined behaviour:
  every access is within the objects, every shift and arithmetic
  operation is on unsigned 64-bit values within range (`htval << 2 <
  2^41` under E4; the `INSIDE` sums do not wrap by precondition), no
  division, no signed overflow.
- **Determinism and purity.** The result and `*out` are functions of the
  four inputs' values alone.

### 4.5 The helpers

| Helper | Contract |
| --- | --- |
| `access_fault(scause)` | For `scause ∈ {20, 21, 23}` returns `ACCESS_FAULT(scause)` (`1`, `5`, `7`); for any other value returns `0` (the leaf calls it before E2 and takes its `0` as E2's refusal) **[R1-3]**. Pure; no memory access. |
| `htinst_accepted(scause, htinst)` | Returns `1` iff `HTINST_OK(scause, htinst)`, else `0`, for every pair of values (the result is a Boolean `0` or `1`, which the leaf tests for truth) **[R1-3]**. Pure. |
| `inside(address, base, bytes)` | Requires `base + bytes` not to wrap; returns `1` iff `INSIDE(address, base, bytes)`, else `0` (so `0` for `bytes = 0`) **[R1-3]**. Pure. |
| `leaf_at(leaves, gpa)` | Requires `leaves` valid and each page's `gpa + bytes` not to wrap; returns a pointer to `PAGE(gpa)` within `leaves` if it exists (the lowest-index page with `bytes > 0` containing `gpa`), else the null pointer; reads `leaves` only; writes nothing; its loop visits at most the array's three entries **[R1-3]**. |

### 4.6 What the contract does not say

Nothing about the vector that saved `record`, the injection helper that
writes the `vs*` CSRs from `out` and reads them back, the DENIAL record's
posting, or the resume: those are the executor's and the exit handler's,
outside the leaf (the M1 plan's "One executor, in order"), covered by
host tests and the semantic checker (U-08) and modelled by stage 1's P5.
Nothing about compiled execution (claim class (d)).

## 5. Leaf B: the per-call properties of `mvp-ring.c`

A ring is a buffer of `C` bytes, `C` a power of two in `[512, 32768]`,
with a **head** the writer owns and a **tail** the reader owns, each a
free-running `u64` byte count, a multiple of 8, alone in its own 64-byte
line; a record is a 16-byte header (type, domain, length, reserved, the
writer's time) and at most 256 payload bytes padded to a multiple of 8;
positions in the buffer are the counts masked by `C − 1`. Each side holds
its own **view** (buffer pointer, capacity, the two index pointers, the
type set, the domain, the role, a `failed` flag, a `cursor`, a `limit`,
and the writer's `peak`), in its own memory. (M0 plan L340-L353; the
header's contract as the fact sheet quotes it.)

**Ownership premise (stated, not checked by the tool).** One writer view
and one reader view per ring; the writer writes only the buffer and the
head, the reader only the tail; a view's own index is written only by
that view. The **peer's index is an arbitrary `u64`** at every call: the
properties hold for every value of it, and the harness makes it
nondeterministic (the plan's D-8). The fences are the callers' and are
outside these properties (stage 1's `L2` to `L4`).

For each public function, the harness states the property below plus the
**safety properties common to all**: every buffer access is at a
position `< C`; every read of a view field is within the view; no
unsigned arithmetic is undefined (wraparound in `u64` is defined and is
the intended semantics of the index differences **and of the index
advances** `cursor + 8`, `cursor + 16`, `cursor + 16 + i`, and
`cursor + size` on the free-running counters **[R1-9]**); every loop is
bounded (by 8, 256, or 32) and fully unwound.

| Function | Property (for any peer index value) |
| --- | --- |
| `be_mvp_ring_reset(head, tail)` | Both index values become `0`; nothing else is written. |
| `be_mvp_ring_init(view, buffer, C, head, tail, types, domain, role)` | Returns `1` iff `buffer`, `head`, and `tail` are non-null, `C` is a power of two in `[512, 32768]`, `types` is a non-empty subset of the inbound set, the outbound set, or the input set, `domain ∈ {0, 1}` **[R1-4]**, `role` is writer or reader, and the two index values are multiples of 8 with `head − tail ≤ C` in `u64`; on `1` the view's `cursor` is its own index's value (a writer's the head, a reader's the tail), `limit = cursor` (the view's own index, not the peer's: a writer's limit is what it has published, a reader's what it has acquired, each advanced by `publish` or `acquire`) **[R1-5]**, `peak = head − tail`, `failed = 0`; on `0` the view is failed. Writes no index and no buffer byte. |
| `be_mvp_ring_record_bytes(length)` | Returns `16 + ((length + 7) & ~7)` for `length ≤ 256`, else `0`. |
| `be_mvp_ring_post(view, type, time, payload, length)` | For a writer view not failed, `type` in the view's type set, `length ≤ 256`, `payload` non-null when `length > 0`, and the peer's tail `t` **well formed**: a multiple of 8 with `limit − t ≤ C` (at or behind the head the writer has published, by at most a capacity) **[R1-6]**, and `cursor − t ≤ C` and `cursor − t + record_bytes(length) ≤ C`: returns `1`, writes exactly the record's `record_bytes(length)` bytes (header, payload, zero padding) at positions `cursor .. cursor + size − 1` masked, writes no other buffer byte and no index, advances `cursor` by `size`, and updates `peak` to the most bytes in use seen; otherwise returns `0`, writes no buffer byte, and the view is failed (a malformed tail, not aligned or more than `C` behind the published head, fails it too). |
| `be_mvp_ring_room(view)` | For a writer view not failed with a well-formed tail (as `post` reads it: aligned, with `limit − t ≤ C`) **[R1-6]**: returns the largest `n ≤ 256` such that a record of payload `n` would fit, or `0` if none fits; writes nothing and never fails the view for want of room; a malformed tail, a reader's view, or a failed view returns `0` and fails the view. |
| `be_mvp_ring_post_words(view, type, time, words, count)` | For `count ≤ 32`: as `post` with the `count` words as a little-endian payload of `8·count` bytes; `count > 32` returns `0` and fails the view. |
| `be_mvp_ring_publish(view)` | For a writer view not failed: sets the head to `cursor` and returns `1`; else `0` and the view is failed; writes no buffer byte. |
| `be_mvp_ring_acquire(view)` | For a reader view not failed, the released tail `r` (the view's own index line as it stands), and a head `h` that is a multiple of 8 with `h − r ≤ C` and `cursor − r ≤ h − r` in `u64` (at or past what this reader has taken, and at most a capacity past the tail it released) **[R1-7]**: sets `limit := h` and returns `h − cursor`; a head behind the cursor, more than `C` past the released tail, or unaligned returns `0` and fails the view; a writer's or failed view returns `0`. Writes no index and no buffer byte. |
| `be_mvp_ring_take(view, record)` | For a reader view not failed: if `limit − cursor = 0` returns `EMPTY` and `record` is zero; else reads the header at `cursor`, and if its type is in the view's set, its domain the view's, its length `≤ 256`, its reserved word `0`, its padding zero, and `record_bytes(length) ≤ limit − cursor`, copies type, domain, length, time, and payload into `record`, advances `cursor` by the record's size, and returns `RECORD`; otherwise returns `INVALID`, fails the view, and `record` is zero. Reads only positions in `[cursor, limit)`; writes no buffer byte and no index. |
| `be_mvp_ring_release(view)` | For a reader view not failed: sets the tail to `cursor` and returns `1`; else `0` and the view is failed. |
| `be_mvp_ring_peak(view)` | Returns the writer view's `peak`; writes nothing. |
| `be_mvp_ring_taken(view)` | For a **writer** view not failed: returns the reader's tail as the writer reads it from the index line, with no validation, no fence, and no change to the view (the bytes the reader has taken and released; a failed domain hart waits on it for hart 0's progress, Plan revision M1-B); `0` for an absent, failed, or reader's view **[R1-8]**. |
| `be_mvp_ring_published(view)` | For a writer view not failed: returns the head's value as it stands; `0` for an absent, failed, or reader's view. |
| `be_mvp_record_word(record, index)` | Returns the little-endian 64-bit word at payload offset `8·index` if `8·index + 8 ≤ length`, else `0`. |

**Sequence property.** For a writer and a reader view on one buffer:
`post`, `publish`; `acquire`, `take`, `release`, across a wrap of the
positions (a start index near `2^64 − 256` and one near `C`), returns the
posted record byte for byte, and after `release` the writer's **free
bytes**, `C − (cursor − tail)`, grow by the released record's size
(`room` itself is the payload a next record may carry, counted after its
16-byte header and capped at 256, so it grows by the released size only
until the cap) **[R1-9]**. (P3 and P4 at the harness's bounds.)

**Claim boundary of Leaf B's result.** Per call, for any peer index, under
the ownership premise; nothing for U-04 (the rings as the implementation
runs them, with fences) or U-11 (memory ordering); never called proof
(S3-C's Q36).

## 6. Mutation and vacuity expectations

- **Mutants.** `mvp/verify/tools/mutate.py` with seed `0x4d38` and
  `count = 24` on each leaf (Leaf A: the five functions; Leaf B: all
  twenty), each mutant a single change by its operator, constant, or
  dropped-check rule. For every mutant, at least one goal of the arm's
  frozen contract (Leaf A) or of the harness's properties (Leaf B) must
  fail; a mutant that still proves is run against the leaf's host test
  (`mvp/tests/deny-test.c` for Leaf A, `ring-test.c` for Leaf B): if the
  host test passes too, the mutant is recorded as unobservable
  (equivalent at the tested inputs) and not counted as killed, and the
  specification's strength at that point is a finding for the human's
  review; if the host test fails, the arm's contract missed a behaviour
  the test sees, a finding about the arm.
- **Vacuity.** For each arm on Leaf A: the preconditions of section 4.3
  must be shown satisfiable (a goal `ensures \false`, or its equivalent,
  must **not** prove); a deliberately contradictory precondition must be
  detected by the tool's own check; for each helper likewise. For the
  harness on Leaf B: every assertion must be reachable (coverage) and
  the assumptions jointly satisfiable.
- **Known-pass, known-fail, wrong-implementation** (the plan's D-7 item
  2): a trivially correct function with a true contract proves; the same
  with a false postcondition fails; a function with a planted defect
  against a true contract fails; recorded per arm and solver before the
  leaf.

## 7. Claim classes (for the outcome's recommendation)

| Class | What | Example functions | Evidence in M8 |
| --- | --- | --- | --- |
| (a) pure decision functions over captured inputs | `const` inputs, one output object, no volatile, bounded loops | the denial decision (Leaf A); the management decision; the G-stage derivation; the launch gate | the C arms (contract proof) |
| (b) ring-class code with shared volatile indices | per-call contracts under an ownership premise, any peer index | `mvp-ring.c` (Leaf B) | bounded model check; a WP contract arm if budget |
| (c) the cross-hart protocol | interleavings, phases, ordering premises | the barrier, the drain, the rings' protocol, management delivery | stage 1 with its litmus premises; no C tool |
| (d) compiled execution | what the locked compilers and the executor preserve | everything | assumed; no binary correspondence |

## Revision 1 (2026-11-03): nine clauses corrected

**Status: accepted on 2026-11-03 at exact commit `93a8d136` (instruction
`accept 93a8d136`); the re-frozen SHA-256 of that commit's text is
`aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b`, the
hash every arm's annotation cites in the re-run. As presented: proposed,
not accepted.** The pilot's three arms (M8-6: WP and
CN on Leaf A; CBMC on Leaf A and on Leaf B), run against the accepted text
of `004f31ae`, found nine places where that text disagrees with the
leaves. In each the leaf does what the accepted M1 plan's "The accepted
entry" (`planning/mvp-m1-plan.md`) or the ring header's contract comments
(`mvp/src/mvp-ring.h`) say, and the host tests (`mvp/tests/deny-test.c`,
`mvp/tests/ring-test.c`) pin that behaviour: the disagreements are errata
of this document, which was drafted from the plans and the claim without
reading the C (D-6), not defects of the monitor. On the M8 plan's stop 2
the responsible human decided on 2026-11-03 (form answer
`spec_mismatches=revision_1_rerun`) that the nine clauses are corrected
in a Revision 1, re-frozen as its own exact commit for acceptance, and the
arms re-run against it. No monitor source changes. The arms' records of
the run against the accepted text are kept under
`mvp/results/20261103-verify/` as the finding's evidence.

| # | Clause | Accepted wording | Corrected wording | Evidence | Reading |
| --- | --- | --- | --- | --- | --- |
| R1-1 | 4.2 E7 | the read-only case did not exclude the window; the unmapped case was `¬MAPPED` | the GPA is outside the window first, for every cause; then unmapped (no declared page) or read-only (cause 23, a declared page without `W`) | M1 plan L514 and L517-L518 ("a fault inside the window … stay[s] terminal"); `deny-test.c`; all three arms' `D_complete_in_window` counterexample: a store at `0x80000000` inside the window and inside page 0 with PTE `0x46000053` | erratum: the accepted text dropped the M1 plan's qualifier |
| R1-2 | 4.3 | no condition on `map.size` | `map.size > 0`; a zero-size map is not a walked window and the leaf refuses every exit under it | `deny-test.c` `test_inputs` (a zeroed map: refused); the arms' `D_complete_empty_window` counterexample | erratum: an unwalked map is outside the contract's domain |
| R1-3 | 4.5 | `access_fault` unconstrained outside `{20, 21, 23}`; the Boolean helpers' results not stated as `0`/`1`; `leaf_at`'s "lowest index" only in 4.1 | `access_fault` returns `0` outside the three causes (the leaf calls it before E2 and takes `0` as the refusal); `htinst_accepted` and `inside` return exactly `0` or `1`; `leaf_at` returns the lowest-index page | the WP arm's proved additions `AF_other`, `HI_bool`, `IN_bool`, `LA_null`, `LA_found`, without which no modular proof of the leaf is possible | erratum: the helper contracts were too weak for a modular proof |
| R1-4 | 5 `init` | no condition on `domain` | `domain ∈ {0, 1}`; `head` and `tail` non-null; `peak = head − tail` | `mvp-ring.h` ("@domain: 0 or 1"); `mvp-ring.c` (`domain >= BE_MVP_DOMAINS` refused); `ring-test.c` (domain 2 refused); CBMC `init` 2 failed properties | erratum |
| R1-5 | 5 `init` | `limit` the peer's index | `limit = cursor`, the view's own index, advanced by `publish` or `acquire` | `mvp-ring.c` (`ring->limit = ring->cursor`); `ring-test.c` (`limit == cursor`); CBMC `init` | erratum: the accepted text misread the view's fields |
| R1-6 | 5 `post`, `post_words`, `room` | the tail bounded by the cursor only | the tail well formed: aligned, and at or behind the **published head** by at most a capacity (`limit − t ≤ C`), then the cursor conditions | `mvp-ring.c` (`ring->limit - tail > ring->capacity` refused, "at or behind the head the writer published"); CBMC `post` and `room` 1 failed property each, the trace a record posted and not yet published | erratum: the published head, not the cursor, bounds the reader |
| R1-7 | 5 `acquire` | the head bounded by the cursor | the head bounded by the **released tail**: `h − r ≤ C` and `cursor − r ≤ h − r` | `mvp-ring.c` ("at most a capacity past the tail it released"); CBMC `acquire` at 512 after a take | erratum |
| R1-8 | 5 `taken` | a reader view's own tail | a **writer** view's reading of the reader's tail; `0` for a reader's view | `mvp-ring.h` ("the reader's tail, as a writer view reads it"); `mvp-ring.c` (`writer_view(ring)`); CBMC `taken` 2 failed properties | erratum: the accepted text swapped the roles |
| R1-9 | 5 sequence property and the common safety paragraph | "`room` grows by the released size"; wraparound intended for the index differences only | the free bytes `C − (cursor − tail)` grow by the released size (`room` is the payload after the header, capped at 256); the index advances wrap by design too | `mvp-ring.c` (`room` capped at `BE_MVP_RECORD_PAYLOAD_MAX`, counted after the header; `cursor + size` on free-running counters); CBMC sequence 1 failed property in all 128 class runs; configuration A's 8 index-advance sites | erratum: a wording that did not match the function's definition |

Two findings of the arms are **not** errata and change no clause: the
vacuity check's dead branch at `mvp-sbi.c` L317 (the `SPVP ? SPP : 0` arm
can only yield `0` because E3 refuses `SPVP = 1`; a true observation about
the code, harmless, recorded for a later comment) and the mutant `m02` of
Leaf B (`failed = 2` where the test asserts `== 1`: the header and this
document say "failed", nonzero; the test is stricter; recorded as a
harness finding for the human's review, the contract unchanged).

What this revision does not change: the stage-1 property list P1 to P9
and sections 1 to 3 (the modules cite the accepted hash they proved
against, and their own errata S-1 to S-4 are the M8 plan's); sections 6
and 7; any monitor source; any arm's annotation (each arm's transcription
is re-made against this revision's hash in the re-run). The freeze rule
of the head applies: this revision is its own exact commit, its SHA-256
is recorded in the M8 plan's status block as `m8_specifications_revision_1=`
beside the accepted hash, and every arm's annotation file cites it.

```text
m8_specifications_revision_1=accepted
m8_specifications_revision_1_target=93a8d136d38547a8c581197315f7607b5eef7bad
m8_specifications_revision_1_sha256=aeb75682f4c300b44f98c3ba3710e6f7142ed686a597bec3bf8a484c69693b8b
m8_specifications_revision_1_acceptance_instruction=accept-93a8d136
m8_specifications_revision_1_acceptance_date=2026-11-03
m8_specifications_revision_1_record=mvp-m8-specifications-revision-1-review-summary.md
m8_specifications_revision_1_base=004f31ae;sha256-ade32fa639d255ec2ba08040bbe8dbba2d7d8bf3fc4401947f4c542ecc9dc53d
m8_specifications_revision_1_clauses=R1-1..R1-9;sections-4.2-4.3-4.5-5
m8_specifications_revision_1_reading=nine-errata-no-code-defect
m8_specifications_revision_1_decision=stop-2;form-answer-spec_mismatches=revision_1_rerun;2026-11-03
m8_specifications_revision_1_stage_1_unchanged=P1-P9-sections-1-3-6-7
```
