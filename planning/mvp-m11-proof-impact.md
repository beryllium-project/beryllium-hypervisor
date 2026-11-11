<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP 2.0 milestone M11: the proof-impact review

**Status.** This is the review that the [M11 plan](mvp-m11-plan.md)
asks of work package M11-2 before any proof is re-run (its D-11). It
was made by reading, at the plan's accepted commit `77eabce5`: nothing
was built, run, or proved for it. References were gathered in a first
read-only pass; those that a conclusion rests on were then checked
against the sources at that commit, and an independent read-only
review of two drafts checked many of them again. Line numbers are
those of that commit.

It decides nothing that the plan leaves to the responsible human.
Where it finds such a thing, section 7 says so.

**Decided.** On 2026-11-11 the responsible human answered section 7's
three items together.

- Item 1: the reading of "the state's configuration" is condition 1's
  recommendation. Hart 0 publishes the four configuration words
  read-only, and the hart keeps a working copy in its own state.
- Item 2 was seen.
- Item 3: the direction is given. The litmus tests' record of compiled
  sequences, with its excerpts, the tests' comments, and the scan of
  the other two scenarios' call sites, is re-derived at each of
  D-11's points, and the one line number in WP's record is corrected
  when the line moves. No test's program, premise, statement, verdict,
  or count changes that way.

The sections below are as they were put to him.

**Terms.**

- *Stage 1* is the M8 plan's concrete model of the monitor's three
  harts, in Rocq, with its 26 theorems. `C.v`, `R.v`, `B.v`, and
  `Cl.v` are `model/proof/Concrete.v`, `ConcreteRings.v`,
  `ConcreteBridge.v`, and `ConcreteClaims.v`.
- *The leaves* are the two pieces of C that the M8 pilot checks with
  tools: Leaf A, the denial decision, and Leaf B, the ring. *The arms*
  are those tools' runs: WP, CN, CBMC on Leaf A, and CBMC on the ring.
- *The specification* is the M8 specification. Stage 1 cites its
  accepted text and the arms cite its Revision 1,
  `mvp/verify/specification-93a8d136.md`; properties P1 to P9 read the
  same in both.
- *The room kept* is the 360 bytes that, from M11-4 on, every
  VS-domain hart keeps free in its outbound ring for its last records
  (the plan's D-8).
- *The lift* is the plan's row on S3-C's stop (e): the edits to the
  monitor, to accepted model files, and to one gate's pin that M11
  may make.

## 1. Result

The plan expects four things of this review (D-11). Each holds, under
the conditions of section 6.

| The plan expects | This review finds |
| --- | --- |
| No property's statement changes | Confirmed for P1 to P9 and for both leaves' contracts. Two things come with it. Where the four words of "the state's configuration" live after the layout's split needs a reading of accepted text (condition 1; section 7). And one clause, P3 (d), keeps its statement but is left with no case that stage 1 reaches (condition 6; section 7) |
| Definitions and readings do change | Confirmed, and listed in section 4: the exit decision, the post step, one step of the inbound take, one lemma restated and others added, the generated constants, and the readings of the files that change |
| Both leaves' pinned inputs change at four points: M11-2, M11-3, M11-4, and the candidate | Confirmed against the thirteen pinned files (section 3). "No fifth" holds as the sources stand; condition 5 says what keeps it so |
| The confinement itself is not modelled | Confirmed: no module of stage 1 names a physical access profile or an invariant of I21 to I28 |

Three things are for the responsible human (section 7): the reading of
"the state's configuration"; P3 (d), left with no case that stage 1
reaches; and two things that must follow the monitor and that the plan
does not name, a record of its compiled code and a line number in a
tool.

## 2. The nine properties

The specification names no IPI, timer, or tick: its step table has no
such step, and stage 1 says of itself that "an exit of any kind may
occur at any time in guest mode, a hart in an HS wait may read its
inbound ring at any time" (`C.v`, its header). That is why the
statements stand.

| Property | Stage 1's theorems | What M11 changes under it | Statement |
| --- | --- | --- | --- |
| P1, the barrier | `barrier_publication_block` | The values of the two `hgatp` constants and the two block addresses (D-4); the publication code, when the block is split by writer. The proof uses one value only: the generation is not zero | Unchanged |
| P2, one writer | `concrete_step_within_footprint`, `single_writer_carried` | The exit step, for the tick; the post step, for the room kept (D-8). No word is added between harts | Unchanged |
| P3, the rings' safety | `ring_no_overrun`, `ring_take_published_only`, `ring_indices_monotone`, `control_ring_fails_closed`, `input_ring_drops_under_room` | The post step. The ring functions themselves do not change. Clause (d) is left with no case that stage 1 reaches (condition 6) | Unchanged |
| P4, records in order | `ring_fifo_integrity`, `ring_type_set` | Nothing, as long as M11-4 adds no record type (condition 7) | Unchanged |
| P5, the denial | `denial_iff_entry_below_ceiling`, `denial_record_before_resume`, `roots_from_instance`, `flow_is_declared_channel` | The exit decision: the tick comes in, and the supervisor software interrupt now fails the hart; a tick is not charged to the ceiling. The decision function of Leaf A and the G-stage roots do not change | Unchanged |
| P6, management | `mgmt_decided_by_control_hart`, `mgmt_outcome_from_grants`, `mgmt_one_pending_per_domain`, `parked_never_resumes`, `mgmt_answered_once`, `mgmt_grants_from_instance` | Delivery is found at the target's tick. Today the step that an IPI enters fails the hart when its inbound ring is empty; a tick with an empty ring must not | Unchanged |
| P7, the launch gate | `entry_after_gate`, `gate_false_no_start` | Nothing that the model has. The stub, `confine`, and the dropped status poll lie between a hart's start and its readiness, where stage 1 has no step | Unchanged |
| P8, the drain's order | `drain_round_robin`, `drain_in_order` | Only what triggers a drain. The model's drain step is already enabled at any idle point | Unchanged |
| P9, the input ring | Inherited from `InputRing.v` | Nothing: the poll period stays 2^18 | Unchanged |

The specification's errata keep their scope. S-1 limits P1 to the
published words, and the layout now puts those words in an extent of
their own. S-2 limits P5 to exits below the ceiling, and a tick is not
charged. S-3 and S-4 are untouched: the latency that ticks add is
liveness, which S-4 already sets aside. S-5 corrects Leaf B's row for
`room`, which only the input ring's writer calls; the room kept does
not use that function.

## 3. The two leaves

**Contracts.** Neither changes.

- Leaf A is `be_mvp_denial_decide` with its four helpers
  (`mvp/src/mvp-sbi.c`, lines 201 to 324). No work package names a
  change to them. Its entry condition E1 reads `state.accept_denial`,
  and its inputs are "the hart's private state", the walked window,
  the walked leaves, and the exit record. Condition 1 keeps that true
  after the layout's split.
- Leaf B is `mvp/src/mvp-ring.c`. The plan keeps the ring's code as it
  is. The room kept must therefore not become a new function of that
  file: a function there with no row in the contract would be stop 9
  (condition 6).

**Pinned inputs.** `mvp/verify/target-digests.txt` pins thirteen files,
the compile's recipe and flags, and three pins.

| Pinned | Leaf | Changes at |
| --- | --- | --- |
| `mvp/src/mvp-sbi.c` | A, its unit | M11-4: the exit classification, the class names, the controls check, the posts, and the serve's rule for an empty ring |
| `mvp/src/mvp-ring.c` | B, its unit | Not at all |
| The ported `be/r3.h` | A and B | M11-2: a new value of the firmware's expected SBI version, a macro that neither leaf uses. Perhaps M11-3, if a constant of the ported boot check moves with the core's layout (D-4, "The core") |
| The ported `be/manifest.h`, `r2.h`, `r4.h`, `state.h`, `types.h` | A and B | Not expected |
| `mvp/src/mvp-layout.h` | A and B | M11-3 |
| `mvp/src/mvp.h` | A and B | M11-3, in comments only (condition 1); M11-4: the class list, the tick's cause and enable |
| `mvp/src/mvp-gstage.h`, `mvp/src/mvp-ring.h` | A and B | Not expected |
| `mvp/src/mvp-sbi.h` | A | Not expected. It holds firmware extension numbers, so the boundary extension's number must live elsewhere (condition 5) |
| The compile's recipe, its make variables, and its flags | A and B | Not expected (condition 5) |
| The specification's pin, the verifier's closure, the verifier's sources | | Not expected. The verifier image is not affected by the tool locks' move |

So the plan's four points are right: M11-2, M11-3, M11-4, and the
candidate.

**The baseline to compare with** is the last record,
`mvp/results/20261109-verify-cheri-integration/`:

| Arm | The record |
| --- | --- |
| WP | OPEN: 130 of 134 goals proved |
| CN | OPEN: 5 of 55 goals proved |
| CBMC on Leaf A | SUCCESSFUL: 336 properties, a bounded check |
| CBMC on the ring | OPEN: 13,547 of 14,931 properties checked, 1,384 open |

Four things in it are fragile, and the re-runs watch them.

- **The ring's arm runs close to its limit.** Each solver run has 600
  seconds. One row took 575.8 s, 577.8 s, and 593.1 s in the last
  three records (`20261105-verify-rc4`, `20261108-verify-release`,
  and the baseline); another went from 64.5 s and 78.4 s to 329.8 s
  when the CHERI integration added lines to `mvp.h` that the plain
  build does not compile. The records keep a row's total and not each
  run's time, so the margin is not known until M11-2's new step reads
  the arms' logs. Leaf B's unit does not change in M11, but its
  headers do at M11-2, M11-3, and M11-4. A count that changes because
  a run crossed its limit is stop 9, recorded as that.
- **Leaf A's frame check rests on one solver.** In the baseline it
  was answered by cvc5 alone: MiniSAT reached its limit of 300
  seconds, where it had taken 5 s in the two records before. The
  cause is likely the same.
- **The bounded check of Leaf A** compares its four input structures
  before and after the call, with a loop bound of 513 bytes. The
  hart's state is 432 bytes today and the exit record 360. Each of
  the four must stay within 512 (condition 7).
- **WP's record quotes a line number** of `mvp-sbi.c` (section 7).

At M11-2 the change to the leaves' inputs is one macro's value in a
ported header, with no line added. The risk to the solvers' times is
at M11-3 and M11-4.

## 4. Stage 1: what changes, and what does not

Stage 1 has 26 theorems in three modules, 99 readings by symbol, and
96 generated layout constants.

**What "statement" means here.** The plan's stop 9 names "a stage 1
statement". This review reads that as the statements of the 26
theorems: the 25 that `stage1_claim_set` (`Cl.v`) bundles, and
`stage1_claims`, which proves that bundle.

- It is what M10 checked when it re-proved stage 1 for M9's change:
  the 26 statements byte-identical, while definitions changed, two
  lemmas were added, and one proof was written again
  (`planning/mvp-m10-evidence.md`). D-11 says "as M10 did".
- The plan's own design needs it. D-11 puts the room kept inside the
  post step, with the fail step as an outcome. The lemma
  `exec_post_effect` (`R.v`) says that a post has two outcomes. So a
  lemma's statement changes by the plan's own words, and "statement"
  cannot include lemmas.
- Byte-identity is necessary and not enough: definitions that change,
  such as the exit decision, stand inside theorem statements. So each
  re-proof point repeats M10's mechanical check, and M11's evidence
  lists every changed definition that a theorem's statement names,
  with the reason that its meaning is kept.

**What changes, and what covers each edit.**

| Edit | Where | Covered by |
| --- | --- | --- |
| `exit_decide`, and the action that an IPI exit had: the tick's cause comes in; a software interrupt now fails the hart, as any other interrupt does | `C.v` | The lift: "the concrete model's exit decision" |
| The exit step's count: a tick is not charged | `C.v` | The lift. The C function that the exit decision reads is documented as "count and classify one exit, and decide it" |
| The inbound take that a guest-level interrupt enters: an empty ring is no longer a failure | `C.v` | The lift: "ring steps" |
| The post step: the room kept (condition 6) | `C.v` | The lift: "ring steps"; D-11 |
| `ConcreteLayout.v`, generated again | | The lift: "the generated layout constants" |
| Lemma `exec_post_effect`, restated with a third outcome | `R.v` | D-11: "read again and re-proved with every statement unchanged, as M10 did"; M11-4's exit |
| A lemma for the tick's cause. `gpf_not_ssi` stays true as it is, since the software interrupt's cause stays defined | `Cl.v` | The same |
| A new invariant: a hart that has not failed keeps the room | `R.v` | The same |
| Proofs that unfold a changed definition | `R.v`, `B.v`, `Cl.v` | The same |
| Readings written again where a cited symbol changes | `C.v`, `B.v` | For the exit decision and the ring steps, the lift: "with their readings (D-11)". M11-3's row: "stage 1's generated constants and readings" |
| A note beside the exit decision, on the working copy of condition 1 | `C.v` | The lift |

Two kinds of edit rest on readings of the plan, as "statement" does.

- The lift's words name definitions and constants. The lemmas and
  proofs rest on D-11's re-proof "as M10 did", and M10 added lemmas
  and wrote a proof again. What M11-4 adds are lemmas, not theorems:
  a new theorem would need a line in `ConcreteAssumptions.v`, an
  accepted file outside the lift, and would change the count of 26.
- A reading that is written again for a symbol outside the exit
  decision and the ring steps rests on M11-3's row alone. That row is
  not in the table of accepted decisions that stop 1 excepts. So
  condition 2 keeps those symbols' names, and a rename that cannot be
  avoided is stop 1.

**What must not need a change.** The lift names model edits "for
nothing else". So M11-3 must leave the model's publication and
readiness steps alone. Conditions 1 and 2 are what make that possible:
the same words are published, under the same names, and a block still
has one address that the hart checks. `Binding.v`, `Policy.v`,
`InputRing.v`, Model 0.2, the model's tests and their pins, the
generator, and the readings gate are not edited, but for the
`python3` version that the lift names.

**The generated constants.** The layout header is the generator's only
input. The generator takes a constant only as a literal, and it
refuses one inside a conditional other than the include guard. It is
an accepted tool outside the lift, so the header keeps that form.

- Of the 96 constants, 15 change with D-4 for certain: the image's
  size and the boot image's kernel offset, which follows it; the
  pools' address with the six G-stage root and table addresses; the two
  `hgatp` values; the hart region's address and the two block
  addresses; and the MVP region's base. Three more almost certainly
  change: the state page's offset and size, and the outbound ring's
  offset.
- Stage 1 names eleven constants (condition 2). It depends on the
  value of two, and D-4 changes neither: the generation is not zero,
  and there are three declared pages.

**The readings.** The readings gate checks that each cited symbol
still exists in its file. It does not check that the symbol still
means what the model says. One example: the supervisor software
interrupt's cause stays defined, because the probe images use it,
while its meaning for the exit decision turns from "serve" to "fail".
So at each re-proof point all 99 readings are read again by hand, as
M10 did, and the gate's PASS is not taken for that.

| Cited file | Readings | First changes at |
| --- | --- | --- |
| `mvp-ring.c`, `mvp-ring.h`, `mvp-gstage.h`, `mvp-log.c`, `mvp-core.c` | 27 | Not expected |
| `mvp-layout.h`, `mvp-hart.h`, `mvp-platform.h` | 6 | M11-3 |
| `mvp-runtime.c` | 14 | M11-3 (publication, the ring views), M11-4 (the control loop's tick), M11-8 (the control hart's `confine`) |
| `mvp-hart.c` | 13 | M11-3 perhaps (the block's fill), M11-4 (the tick probe) |
| `mvp-hartmain.c` | 2 | M11-3, M11-4, M11-7 |
| `mvp.h`, `mvp-sbi.c` | 37 | M11-4 |

**`Binding.v` is not edited.** It is an accepted file outside the
lift, and M8 left it unedited for the same reason. M11's evidence
lists what goes stale in it:

- at M11-3, its hand-copied layout literals: the block addresses and
  offsets, the MVP region's address, and perhaps the accepted image's
  size;
- at M11-4, its footprint comments that cite IPI lines;
- with condition 1, its description of the state's configuration, and
  the readiness step's footprint with its comment, which, read as the
  C's writes, no longer names the copy (section 7).

Its theorem `binding_h2_private_state` stays true of its literals. The
lineage row in `Cl.v`, "no published object is written after the
barrier", stays true under condition 1's reading and rests on it.

## 5. The ordering premises

The five premises are about fences and dependencies in the ring's and
the barrier's code. None is about an IPI: the M8 plan says that
"Nothing is claimed about caches, IPIs' delivery timing, or the
firmware's HSM".

| Premise | Its compiled sequence | With M11 |
| --- | --- | --- |
| L1, the barrier | Hart 0's publication and a hart's entry check | The code moves with the layout (M11-3) and is entered through the stub (M11-7). The fences and the pattern stay |
| L2, publish | A writer's post and publish; a reader's acquire and take | A reader now comes from a tick. It runs the same acquire, fence, and take |
| L3, release | Hart 0's take and release against a hart's post | Hart 0's drain now runs at its tick: the same code |
| L4, buffer reuse | A hart's take and release, entered by the IPI, against hart 0's post | The entry is replaced by the tick's (M11-4). The pattern stays; the test's quoted lines and names follow |
| L5, the input ring | The console read against hart 0's flush | Not expected to change |

**No new pattern.** M11 adds two kinds of load of a word that another
hart writes. Neither needs a new premise.

- *The room kept.* Before a post, the hart reads the reader's tail and
  branches. The post then loads the tail again, checks, and stores,
  which is the writer's sequence in L3. The safety of the store rests
  on that second load and its control dependency, as today. The
  earlier load supplies no value to the store and adds ordering only
  to itself, so an execution of the code, projected onto the test's
  events, is an execution of the test. The tests' own rule then
  applies: a reduced test keeps fewer accesses and orderings than the
  code, so what the memory model forbids in the test, it forbids in
  the code.

  That the hart's failure records always fit is a different matter,
  of reporting and not of P1 to P9. It rests on two things that the
  memory model gives without a fence: one hart's stores to one address
  reach memory in program order, and a later load of that address by
  one hart never returns an older value than an earlier load did.
- *The working copy of condition 1.* The hart loads four published
  words. Those loads come after the generation check and its fence,
  where L1 covers them.

The tick's serve must be today's serve path, with its fences: acquire,
fence, take; then fence, release. Today that path is entered from the
IPI exit and from the waits in HS mode. Then L2's and L4's test
programs stay as they are (condition 7).

**The record of compiled sequences** does not survive any of this. See
section 7.

## 6. Conditions on the work packages

Each keeps one of the plan's expectations true. A work package that
cannot keep one stops.

1. **`struct be_mvp_state` keeps its fields, and Leaf A is not
   touched** (M11-3).
   - *The question.* Hart 0 writes four words into that structure
     before the barrier: the exit ceiling and the three accept words
     (`mvp-runtime.c`, lines 1843 to 1846). The accepted invariant I16
     lists them, as "the state's configuration", among the immutable
     published data. I15 lists the structure as the hart's private
     state. Revision 4's I22 (b) gives published data to a profile
     read-only. The plan's D-4, rule 4, puts "the words that boot code
     published" in an extent of their own, D-5 gives the hart that
     extent to read, and D-10's hostile test of "The published words",
     "Its own, to write", expects a fault. Leaf A reads one of the four
     from the structure, and its contract calls the structure "the
     hart's private state".
   - *What this review recommends: a working copy.* Hart 0 publishes
     the four words in the hart's read-only published extent. The
     hart loads them into its own structure at its entry: after the
     generation word reads equal and after the read fence that
     follows, and before READY. From then on the structure is wholly
     the hart's own. The structure, Leaf A's code, and Leaf A's
     contract are as they are today. D-4, D-5, D-10, I15, and I22 (b)
     hold as written.
   - *What it costs.* I16's words "the state's configuration" then
     mean the four published words, and the four fields of the structure
     become a copy that the hart writes after the barrier. `Binding.v`
     makes the old identification, and it is not edited. That is a
     reading of accepted text, and section 7 puts it to the
     responsible human. It is also a new abstraction: the C's exit
     decision reads the copy, where the model's reads the published
     words. That is sound only if the copy is made where this
     condition says and is never written again. So M11-3 adds a check
     that only the entry writes the four fields, by a source check, a
     host test, or a rule of the image checker; the abstraction is
     recorded beside the model's exit decision and in M11's evidence;
     and the comments on the fields in `mvp.h`, three of which say
     "written by hart 0 before the barrier", are corrected at M11-3.
   - *The alternative: leave the four words where they are*, in the
     hart's private state, written by hart 0 before the barrier as
     today. It keeps I16's and `Binding.v`'s words as they are, and it
     needs no new abstraction. The ring views already have that
     shape: fields that hart 0 fills, in a structure that is the
     hart's own. But four words that I16 calls published would lie in
     an extent that the hart may write. That is against D-4's rule 4
     and D-5 as written, and it needs a reading of which clause of
     I22 (b) governs them. And the hostile write to them would
     succeed, which is stop 4 unless the test leaves them out.
   - *What a breached hart gains* by changing its working copy is what
     it does to its own VS domain and what it posts into its own
     mailbox. Revision 4 lists both among a breached hart's allowed
     effects.
   - *Nothing else leaves the question open.* Only hart 0 writes the
     descriptor, the first-entry frame, and the walked map and leaves,
     and the hart only reads them. They move to the published extent
     with no change to Leaf A, to its contract, or to its harness.
     The hart's controls, its entered flag, and its input stage are
     its private state: hart 0 fills them, and the hart then writes
     them. The ring views raise the question for their fixed fields,
     and the second erratum in
     [Revision 1's record](security-model-v1-revision-1-review-summary.md)
     already answers it: the views are the hart's own after the
     barrier.
   - If M11-3 finds that the copy must be a write of the model's
     readiness step, that needs an edit to `Binding.v`'s footprint for
     that step: stop 1.
2. **Names stay** (M11-3).
   - Stage 1 names these constants: `BE_MVP_G0_HGATP`,
     `BE_MVP_G1_HGATP`, `BE_MVP_G0_BLOCK_HPA`, `BE_MVP_G1_BLOCK_HPA`,
     `BE_MVP_GENERATION`, `BE_MVP_PAGES_MAX`, `BE_MVP_KERNEL_GPA`,
     `BE_MVP_OUTBOUND_RING_BYTES`, `BE_MVP_GUEST_GPA`,
     `BE_MVP_GUEST_BYTES`, and `BE_MVP_CHANNEL_GPA`. Their values may
     change, and their names do not.
   - A block keeps one address, in its descriptor, which the hart
     compares at its entry.
   - The cited C symbols that the layout's split touches keep their
     names: `be_mvp_hart_page`, `publish_blocks`, `be_mvp_block_fill`,
     `ring_views`, and `be_mvp_hart_main`. A rename that cannot be
     avoided is stop 1 (section 4).
3. **The layout header is complete at M11-3**, in the form that the
   generator takes.
   - The three addresses at which a hart resumes confined (D-4's
     rule 7).
   - The tick's period, as the constant that exists for the console
     poll or as a new one. The plan's default is the existing
     constant's value for both roles.
   - `BE_MVP_HART_START_TICKS` stays in the header, unused once the
     status poll goes, so that the header does not change after
     M11-3. Removing it would also change every scenario's limits.
   - The variants' constants that M11-4 and M11-7 will need are
     settled now: the `ring-full` variant's ring, which must stay a
     power of two of at least 512 bytes against the 360 bytes kept;
     its drain delay; the variant run budget, which is four tick
     periods today; and the `hart-start` variant's hart. So M11-3's
     design looks ahead to those variants.
   - The 360 bytes' own constant does not live in this header: it is
     added at M11-4, in `mvp.h` or `mvp-sbi.c`.
4. **The scenarios' object lists keep their shape** (M11-3): the same
   objects, with the same identifiers, classes, labels, and order.
   Only their extents change. The model's tests pin the identities of
   the instances that are generated from those lists, and one theorem
   of stage 1 needs the declared pages to be objects 2 to 4. Those
   pins are accepted model files outside the lift.
5. **Every change that M11 needs in the pinned inputs lands at
   M11-2, M11-3, or M11-4.**
   - At M11-4: the failure classes, the boundary's among them; the
     tick's cause, its enable, and the controls check; the serve's
     rule for an empty ring; the room kept.
   - As the sources stand, M11-7 and M11-8 need no change there. The
     helpers that they will use differently are functions whose
     callers, in files that are not pinned, choose: the status and
     census helpers of hart start, the acknowledgement wait, and the
     failure post. So M11-4 leaves them alone. This condition guards
     against what is not foreseen.
   - The boundary extension's number and the boundary's other
     constants live in a header that neither leaf includes.
   - The compile's recipe and its recorded make variables do not
     change. The boundary's build option reaches the runtime's units
     only, and no boundary build recompiles `mvp-sbi.c` with a
     define.

   If something is missed, the plan allows a further point, at the
   cost of one more `verify` run.
6. **The room kept** (M11-4).
   - *The reading that D-11 asks this review to record.* The room
     kept is part of the specification's `post` step, whose outcome
     may be the `fail` step. The step table stays as written, and its
     `room` step stays the input ring's alone.
   - *In the code.* Every post of a VS-domain hart but its failure
     path's own is checked: the answer that a served record posts,
     the line post on the normal path, and the five posting helpers
     for READY, ENTERED, SHUTDOWN, DENIAL, and a management request.
     The failure path's posts are exempt: its unfinished line and its
     failure record. The check is computed from the writer's own view
     and the existing function that reads the reader's tail with no
     check and no fence. It is not a new function of `mvp-ring.c`.
   - *In the model.* Inside the post step, for a hart that is not
     already failing; the exemption follows the hart's mode, not the
     record's type. A post that would leave fewer than 360 bytes
     writes nothing at all: no ring word, and not the hart's phase
     word either, which the accepted footprints of the readiness and
     entry steps do not include. It changes the hart's mode to
     failing, and the existing fail step writes the phase. It logs no
     refusal: the model's refusal implies a failed view, and a failed
     view would refuse the failure record itself.
   - *P3 (d).* `control_ring_fails_closed` keeps its statement, and
     the proof needs the new invariant. For an outbound ring its case,
     a post over the ring's capacity, can then be reached by no hart:
     the failure path's records fit in the room. An inbound ring does
     not reach it today. So stage 1 no longer reaches the case at all
     (section 7). What is left to show that a control ring fails
     closed lies outside stage 1: the ring arm's bounded check of the
     post function at 512 and 4,096 bytes, which is OPEN and never
     called a proof, and the host tests of the path for a malformed
     tail.
7. **The tick** (M11-4).
   - *Its place in the exit decision.* A tick is recognized only in
     an exit from guest mode, and the test for it comes before the
     ceiling's. Every other test keeps today's order: the ceiling,
     then guest mode, then the cause. The C and the model move
     together. In the C the tick's test comes after the checks of the
     arguments and of the hart's phase. It requires guest mode and a
     zero reserved word in the exit record, as the test that follows
     the ceiling does today; the model has no reserved word. A tick
     is served and never charged, and it is never
     the exit that trips the ceiling: the exit counts then do not
     depend on when a tick arrives. The control hart's wake and drain
     counts do, as the plan says.
   - *Its serve* is today's serve path with its fences (section 5).
   - *"Bounded"*, in the plan's "counted apart, bounded", is read as
     a bound in the run's expectations, which the capture checker
     applies. The plan names no failure for it, and the model counts
     no ticks. A bound that the monitor enforced would make a run's
     outcome depend on its length, which the run's budget already
     bounds.
   - *The tick probe* uses the records that exist, PING and PONG. No
     record type is added, so the type sets and the ring's assertion
     that they are disjoint stand.
   - *Where the tick count lives* is M11-4's choice, within two
     limits. Each structure that Leaf A's bounded check compares
     stays within 512 bytes. And no record that the model keeps at
     its C length gains a word; the shutdown record, which the model
     abstracts, may.

## 7. For the responsible human

1. **A reading of accepted text: "the state's configuration".**
   Condition 1 recommends that hart 0 publish the four configuration
   words read-only and that the hart keep a working copy in its own
   state. That reads I16's words as the four published words, where
   I16 and `Binding.v` today mean four fields of the hart's state.
   - The recommendation costs three things: a new abstraction, which
     no proof and no existing gate checks, since the C's exit decision
     reads a copy where the model reads the published words; a check
     at M11-3 that only the entry writes the copy; and a change of
     comments in `mvp.h`, a pinned file, at M11-3.
   - The alternative leaves the four words in the hart's private
     state. It keeps the words of I16 and of `Binding.v` and needs no
     abstraction. But it excepts the four words from D-4's rule 4,
     from D-5's read-only extent, and from the hostile test, with a
     reading of I22 (b).

   Neither changes what a breached hart can do. Either way an
   accepted text is read anew. M11-3 needs the answer.
2. **P3 (d) is left with no case that stage 1 reaches.** The plan's
   D-8 prescribes the room kept, and D-11 says how it is modelled. The
   theorem for "a post over capacity writes nothing and fails the
   writer's view for good" is then about a case that stage 1 never
   reaches.
   - On an outbound ring, the room kept prevents it for every hart:
     the failure path's records fit in the room.
   - On an inbound ring it does not arise, today or after M11. The
     control hart has at most four records outstanding there, a PING,
     an order, a result, and an acknowledgement: 88 bytes, in a ring
     of at least 512.
   - The theorem's statement does not change, and the theorem stays
     true. The room kept's own outcome is stated by the restated lemma
     `exec_post_effect`, which is not one of the 26 theorems.
   - What shows that a control ring fails closed then lies outside
     stage 1: the ring arm's bounded check, which is OPEN, and the
     host tests.

   This review reads that from the model's steps and has not proved
   it. It follows from what the plan already decides; it is here so
   that it is seen before the first re-proof.
3. **Two things that must follow the monitor**: a record of its
   compiled code, and a line number in a tool. The plan gives the
   direction to write the target digests again at each of its points.
   It names neither of these.
   - *The litmus tests' record of compiled sequences*,
     `mvp/verify/litmus/sequences.txt`, with its 55 excerpt files.
     It holds, for each toolchain's `two-guests` monitor, the digest
     of the program without its debug sections, and for each of 55
     entries (32 symbols over the two toolchains) an address, a size,
     a digest, and the lines that a test quotes. `verify`'s first
     suite fails on any difference, and `check` requires every digest
     that a test cites to be in the record. Every plain image changes
     at M11-2. So the record changes at each of D-11's points. Its
     excerpts and the tests' comments change with it wherever a cited
     symbol's bytes or address move.
   - Its own header says "Re-written only on the responsible human's
     direction". M10 re-derived it under its plan: 49 of 55 excerpts
     were extracted again, and the five tests changed only in
     comments.
   - The record also carries a fixed sentence: that the call sites of
     the other two scenarios were scanned in their programs when it
     was written and have the same fence shapes. M11-4 changes those
     sites. So the direction asked includes that scan, done again at
     each re-derivation and recorded.
   - *One line number in WP's record.* `mvp/verify/tools/wp-arm.py`
     writes a sentence that names "mvp-sbi.c line 318", the place of
     one statement of Leaf A. M11-4 adds lines above Leaf A, so the
     sentence becomes wrong then. M10 moved the same literal by one
     line under its plan. (The frozen specification names the same
     statement as line 317; it stays as frozen.)
   - What is asked: the direction to re-derive the record with its
     excerpts and the tests' comments, with the scan, at each of
     D-11's points; and to correct that one literal when the line
     moves. No test's program, no premise, no statement, no verdict,
     and no count changes that way. A test whose program would have
     to change is stop 1, and stop 9 if a premise would.

## 8. M3's and Model 0.2's theorems

Stage 1's lineage table classes the 24 theorems of Model 0.2 and the
22 of M3 as re-proved, inherited, strengthened, or inapplicable. M11
changes no policy, labeling, grant, binding, or manifest semantics:
the windows and the declared pages stay, and the guest-visible SBI
interface does not change. So every class stands. Three things are
recorded:

- `binding_h2_private_state` is proved over `Binding.v`'s own
  literals, which D-4 makes stale (section 4);
- the generated instances keep their identities only under
  condition 4;
- Model 0.2's `terminal_fail_closed_behavior` is carried by two
  theorems. `denial_iff_entry_below_ceiling` is not affected.
  `control_ring_fails_closed` keeps its statement, but stage 1 no
  longer reaches its case (condition 6).

## 9. What this review did not do

It ran no proof, no arm, and no build, and it ran no litmus test with
the room kept's extra load: section 5's argument rests on the memory
model's rules. It did not read the proofs of the 26 theorems in full,
the 160 lemmas of `R.v`, `InputRing.v`, or Model 0.2's modules beyond
the lineage table's rows, so it has not confirmed that every proof
which splits on the exit's action needs only mechanical edits. It did
not design M11-3's layout or M11-4's tick: it states what each must
keep. The first re-proof, at M11-2's point, is where its findings are
first tested.
