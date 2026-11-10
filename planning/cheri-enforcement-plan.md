<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The CHERI platform branch: CHERI enforcement (plan)

This plan answers the responsible human's question of 2026-11-06, "on
cheri, does it actually enforce anything during these tests, or it just
enabled & running?", and the instruction that followed, `accept 6944d7b4 ;
push cheri and plan cheri enforcement`. It is a bounded plan for the
[CHERI platform branch](cheri-platform.md) only. It finds, from sources
and four scratch experiments, what CHERI can enforce under Beryllium's
CHERI-aware monitor on CHERI v0.9.3 under emulation, and plans the work
that makes the branch's checks show it. It writes, changes, and pushes no
code. Its acceptance would authorize only the work packages of section 5,
on the branch's own lines, and nothing that reaches `main`.

## Decision record

The responsible human accepted this plan at exact commit
`9ec57998148b693019e7af6eba88c2160bfc09da` (parent `aa0aea14`, on branch
`beryllium/cheri-enforcement-plan`) on 2026-11-06 by the instruction
`accept 9ec57998; classify as proposed; soft limit increase to 4000; accept 9249dfd1`, whose first part is the reply the
[review packet](cheri-enforcement-plan-review-summary.md) requested; the
abbreviation resolves uniquely. Q1 to Q12 apply at their defaults.

- **Scope:** acceptance covers exactly the plan text at that commit; the
  packet (`b42a02b1`) is decision support.
- **Authorization:** work packages CE-2 to CE-5 under section 9's stop
  conditions, as "What acceptance would authorize" lists them. They run
  on branch `beryllium/cheri-enforcement`, from the commit that records
  this decision. The owner session merges the branch into
  `beryllium/cheri-platform` when the result is accepted (Q9). Nothing
  else is authorized: no push, no merge into `main`, no change on
  `main`'s pages, no publication, no board command or kexec use, no
  change in the beryllium-cheri repository or to an external pin, and no
  claim beyond section 8's words.
- **Priority:** the same instruction directed that work for MVP 1.0 takes
  priority. This plan's work runs behind the MVP 1.0 release path. It
  yields the host's CPU to that path's development runs (its QEMU gates
  run at a lower priority), and its reviews wait while that path needs
  the session.
- **Erratum 1, the soft limit (Q10, stop 10), 2026-11-07.** Before CE-4,
  with 1,203 of the 1,500 counted lines used (38 of 100 in `mvp/src/`),
  the human raised the limit to 2,000 lines in all, the `mvp/src/` lane
  staying at 100 (the form answer `cheri_limit=true` to "Raise the CHERI
  enforcement plan's soft limit from 1,500 to 2,000 lines (mvp/src stays
  at 100)?"). Section 7's text stays as accepted; this erratum governs.
- **CE-4's resumption, 2026-11-07.** The human chose to resume CE-4 (the
  form answer `cheri_ce4=resume`): its code is written while the MVP 1.0
  release's formal step 4 gate run's `verify` gate runs, with no build,
  emulator run, or check until that run ends, and its builds and checks
  then run at a lower priority. CE-2 (`20af3dac`) and CE-3 (`15e25343`)
  were reviewed line by line by the owner session before it; CE-3's
  `CONFIG_COREDUMP=y`, beyond Q2's two options, is recorded for CE-5's
  packet.

## Status

**Accepted on 2026-11-06** (the decision record above). Written on 2026-11-06 (the responsible
human's time zone) by an AI sub-agent of the owner session, on local
branch `beryllium/cheri-enforcement-plan` from `beryllium/cheri-platform`
at `aa0aea140a2413d0937a0202a85ebf8f49cece8c`, in a separate clone whose
push is disabled, for the owner session to review and import; unpushed.
No independent review was run (the 2026-10-06 SOP). `beryllium/cheri-platform`
was pushed to the private `origin` at `aa0aea14` earlier the same day, on
the same instruction.

```text
cheri_enforcement_plan_status=accepted
cheri_enforcement_plan_target=9ec57998148b693019e7af6eba88c2160bfc09da
cheri_enforcement_plan_acceptance_instruction=accept-9ec57998
cheri_enforcement_plan_acceptance_date=2026-11-06
cheri_enforcement_plan_acceptance_record=cheri-enforcement-plan-review-summary.md
cheri_enforcement_plan_open_questions_answered=Q1-Q12-defaults
cheri_enforcement_plan_priority=behind-the-mvp-1.0-release-path
cheri_enforcement_plan_branch=beryllium/cheri-enforcement-plan;local;unpushed
cheri_enforcement_plan_base=beryllium/cheri-platform-aa0aea140a2413d0937a0202a85ebf8f49cece8c
cheri_enforcement_direction=accept-6944d7b4-;-push-cheri-and-plan-cheri-enforcement;2026-11-06
cheri_enforcement_scope=beryllium/cheri-platform-only;cheri-v0.9.3-under-emulation;outside-the-mvp-claim
cheri_enforcement_answer_a=bounded-first-capabilities-infeasible-for-linux-guests;r4-stays-a-design-fact-now-observed
cheri_enforcement_answer_b=g-stage-cw-under-zcheripte;window-leaves-cw;declared-page-leaves-no-cw;fail-closed
cheri_enforcement_answer_c=cause-28-already-delegated;add-in-guest-faults-that-must-occur
cheri_enforcement_answer_d=deferred
cheri_enforcement_work_packages=CE-1..CE-5
cheri_enforcement_plain_variant=byte-identical;cheri-check-part-2;162-images
cheri_enforcement_open_questions=Q1-Q12-with-defaults
cheri_enforcement_soft_limit_lines=1500;monitor-lane-100
cheri_enforcement_soft_limit_erratum_1=2000;monitor-lane-100;2026-11-07;form-answer-cheri_limit=true;1203-used-before-ce-4
cheri_enforcement_result=accepted-3998e34ea09fabaea324b14863b6318994d86a13;2026-11-07;instruction-accept-3998e34e-merge-and-push;record-planning/cheri-enforcement-result-review-summary.md;beryllium/cheri-platform-fast-forwarded-and-pushed
cheri_enforcement_progress=CE-2-20af3dac;CE-3-15e25343;CE-4-9ab49914;each-owner-session-reviewed;CE-5-the-branch-page-and-COPYING-then-the-result-packet;1715-of-2000-lines-through-CE-5-by-section-7;38-of-100-in-mvp/src
cheri_enforcement_stops=1-14
cheri_enforcement_scratch_experiments=E1-E4;scratch-not-evidence
cheri_enforcement_authorization_if_accepted=CE-2..CE-5;work-branch-beryllium/cheri-enforcement;owner-session-merges-into-beryllium/cheri-platform;no-push;no-main;no-publication
```

## The answer in brief

- **Today, CHERI enforces something inside each CHERI guest, but no test
  shows it, and it enforces nothing between domains.** Each guest's
  kernel runs its user space with capabilities it bounds itself, and the
  monitor delegates the guest's own CHERI faults to it (`hedeleg` bit 28).
  No run makes such a fault. Isolation between domains rests on the
  G-stage page tables alone, and a guest kernel can store a tagged
  capability into the shared channel page (E3).
- **"Give each guest bounded capabilities from the start" (A) is not
  feasible for Linux guests.** CHERI Alliance Linux derives every
  capability it uses from its first PCC and panics unless that PCC is the
  whole address space with every permission. Its kernel and user
  addresses lie at the two ends of the address space, so no smaller
  interval serves it. A guest given a PCC bounded to its 64 MiB window
  stops in its first C code (E4). The guest's first `ddc` is cleared by
  the kernel itself. Section 3.2 has the sources.
- **What is meaningful instead (B): a G-stage capability-write control.**
  The emulator checks the capability-write bit, CW (bit 60), in every
  translation stage when its `cheri_pte` property (Zcheripte) is on; the
  branch's harness leaves it off. With it on, CW set in each domain's own
  window leaves, and CW clear in every declared page's leaf, a
  guest kernel's tagged capability store to the channel page traps to the
  monitor as a store guest-page fault, cause 23, and the monitor stops the
  run (E3). Without it, the same store lands (E3). A guest user program
  cannot make that store under an unmodified CHERI Alliance Linux, which
  gives `MAP_SHARED` mappings no capability permission (E2); a guest
  kernel can.
- **Tests that must fault (C, E):** a purecap process's load one byte past
  a 16-byte capability, delivered to it as `SIGSEGV` with
  `SEGV_CAPBOUNDSERR` while the run continues; a `write(2)` through that
  capability returning `EFAULT`; a guest kernel's tagged store to the
  channel page ending the run at the G-stage; and three negative images
  and one control run that show each mechanism is the one doing the work.
- **Monitor self-protection (D)** through window-bounded capabilities for
  the monitor's own copies of guest bytes is deferred, with its cost
  (section 4).

## 1. The governing text

| Source | What it says | What this plan takes from it |
| --- | --- | --- |
| The responsible human's direction of 2026-11-05 ([branch page](cheri-platform.md), "Status and scope") | "for now, we will create a long-lived branch in beryllium for the CHERI platform, to be developed and maintained in parallel with the main Be workstream" | The branch as the only place this work happens |
| The branch's one-way rule ([branch page](cheri-platform.md), "Keeping it in step with the development line", item 4; `.github/copilot-instructions.md`) | "Changes flow one way, from the development line to this branch. Nothing from this branch enters the development line without the responsible human's separate decision under an approved bounded plan." | Nothing here reaches `main`; stop 2 |
| [MVP plan](mvp-plan.md), Plan revision S3-C, the MVP ladder, the MVP 3.0 row | "Independent research tracks, each with its own trigger, hardware precondition, threat-model delta, and exit: MPT (memory protection tables), CoVE, CHERI, and policy composition"; "Investigation-grade unless hardware arrives" | CHERI stays a research track on `main`; this plan's results are emulation results, outside the MVP claim |
| The question of 2026-11-06 | "on cheri, does it actually enforce anything during these tests, or it just enabled & running?" | Section 3.1 answers it; sections 5 and 6 make the checks show the answer |
| The owner session's recommendation, the same day | "Make CHERI enforce something. Today each guest starts with an unbounded capability in its ddc register and in its program counter (PCC), so only the page tables confine it. Give each guest bounded capabilities from the start, then add tests that must fault. This stays on the branch and outside the MVP claim." | Evaluated in sections 3.2 and 4: the first half is not feasible for Linux guests; the tests that must fault are planned |
| The instruction of 2026-11-06 | `accept 6944d7b4 ; push cheri and plan cheri enforcement` | This plan |
| The responsible human's rule of 2026-11-04 ([branch page](cheri-platform.md), "Gates") | "Nothing from Codasip's non-public sources enters this branch" | Every source cited here is a public repository or specification; stop 5 |
| The model split (2026-10-27) and the SOP (2026-10-06) | Code on `claude-opus-5.5` at `max` effort with the `long_context` tier; planning, review, and evaluation on the session model; no independent review as standard practice | Who writes what (section 5) |

## 2. Scope and non-goals

**In scope**, all on the CHERI platform branch, for the CHERI-aware
monitor (`MVP_MONITOR=cheri`) on CHERI v0.9.3 under emulation:

- Zcheripte on for every CHERI run, and the G-stage capability-write
  control: CW in each domain's window leaves, none in a declared page's
  leaf (CE-2);
- tests inside the CHERI Linux guests that must fault, and the run
  continuing (CE-3);
- a guest kernel's tagged capability store to the channel page, which
  must end the run at the G-stage, with a control run that shows the
  store is real (CE-4);
- the negative images, capture-checker rules, mutations, host tests, and
  harness changes that judge them (section 6);
- the branch page's records, a section stating what CHERI enforces on the
  branch in fixed words, and one result packet (CE-5).

**Not in scope** (each needs its own decision):

- anything on `main`, any merge into it, and any push (stop 2);
- any change to the plain variant's images, which must stay `main`'s
  byte for byte (stop 1), or to the development line's checker rules,
  scenarios, guest pins, policy text, claim, or ledger (stops 3 and 4);
- bounding the guests' first PCC or `ddc` (section 4, A: not feasible);
- the monitor's own accesses to guest memory through bounded
  capabilities (section 4, D: deferred);
- a purecap monitor build, RVY (v0.9.10), and HLV.Y/HSV.Y;
- a change to `mvp/src/mvp-sbi.c`'s denial decision (Q1);
- any change in the beryllium-cheri repository, which is read only here
  (stop 6), and any new external pin (stop 11);
- any board command or kexec use (stop 7);
- any claim about CHERI hardware, or any wording that makes these
  emulation results evidence for the MVP's claim (section 8).

## 3. Facts the plan rests on (2026-11-06)

Read-only findings, each with its source at a pinned commit, and four
scratch experiments (section 3.6), each labelled "scratch experiment, not
evidence". The emulator is CHERI Alliance QEMU at `008944fe` (the
`codasip-latest` line, v0.9.3), as beryllium-cheri pins it, built with
beryllium-cheri's two local changes (`experiments/build-qemu-vs-reset.sh
--ia-fix`): one sets `vstvecc` and `vsepcc` to the infinite capability at
reset, and one corrects the invalid-address conversion's width. Neither
touches page-table, TLB, or delegation code, so the source lines cited
below are the built emulator's. The guest is CHERI Alliance Linux at
`3934c32f` (v7.1) with the purecap user ABI, built by the branch's
`mvp/tools/build-guest-cheri.sh` against `mvp/guest/cheri-pins.txt`; the
firmware is CHERI Alliance OpenSBI at `c0575bc8` (`codasip-cheri-riscv-1.8.1`).
All are public repositories.

### 3.1 What the branch enforces today

1. **The guest's own CHERI faults are delegated to the guest.** The
   CHERI-aware monitor writes `hedeleg` = `0x1000b15d`, bit 28 being CHERI
   v0.9.3's CHERI fault, and refuses a hart on which bit 28 does not stick
   (`mvp/src/mvp.h` L207-L227, `mvp/src/mvp-trap.S` L68-L73). The firmware
   delegates cause 28 from M to HS (OpenSBI `lib/sbi/sbi_hart.c` L255). The
   emulator's `hedeleg` mask includes it (`target/riscv/csr.c` L1232,
   L3417-L3421) and sends a delegated trap from V=1 to VS
   (`target/riscv/cpu_helper.c` L2439), swapping `stval2` with `vstval2`
   on each V transition (L630, L687), so the guest reads its own CHERI
   cause. Every CHERI run's `BE_MVP:09` line shows `hedeleg=0x1000b15d`.
   The beryllium-cheri dossier's statement that such a fault, undelegated,
   is terminal in HS (its section 8b, row 4) describes the development
   line's monitor, which runs no CHERI-enabled guest; this branch's
   CHERI-aware monitor delegates it.
2. **Inside each guest, the kernel bounds what its user space holds.**
   The guest kernel prints its own authorities at boot: its code, data,
   and read-only capabilities cover the upper half of the address space,
   and the user root capability covers the lower half (E2's console,
   `CHERI: kernel code cap` to `CHERI: user root cap`; derived in
   `arch/riscv/kernel/riscvcheri.c` L110-L161). A purecap process's
   pointers are capabilities bounded by the kernel and its C library
   (E2's register dump: the child's stack capability bounded to its
   stack's reservation, and others to objects of 8, 0x78, and 0x280
   bytes).
3. **No test makes a CHERI fault.** No CHERI run's capture holds a CHERI
   exception, and the branch's expectations name none.
4. **Between domains, only the G-stage confines.** The guests' first
   PCC and `ddc` are the whole address space (r4 on the
   [branch page](cheri-platform.md)), now also observed: every CHERI
   guest prints `CHERI: Root capability: ...[V:1111:C:rwxCalse:1:.:0x0000000000000000-0xffffffffffffffff]`
   (E2). A capability is authority over addresses in its holder's own
   translation, so this root reaches nothing outside the guest's G-stage
   window; the G-stage is what confines.
5. **A capability can cross the channel page today.** With the branch's
   CPU model, a guest kernel's tagged capability store into the te-poc
   channel page lands, tag set (E3, the run without Zcheripte).

### 3.2 The guest's first capabilities (A)

1. **The purecap kernel's boot ABI: its root is PCC.** At `_start_kernel`
   the kernel enters Capability Pointer Mode (`arch/riscv/kernel/head.S`
   L263) and makes its first code and data capabilities from PCC, with
   `auipc ct0, 0` and `scaddr ct0, ct0, x0`, "Temporarily setup
   kernel_code_cap as infinite" (L344-L352). It then passes PCC to
   `init_cap_relocs` and `riscv_cheri_caps_init` (L395-L401). `a1` carries
   the device tree, which the monitor already passes as a capability
   bounded to the tree's 4 KiB (`mvp/src/mvp-trap.S` L265-L321).
2. **The kernel requires that root to be everything.**
   `riscv_cheri_check_root_cap` requires it tagged, unsealed, with every
   permission the hart supports, base 0, and length `~0UL`
   (`arch/riscv/kernel/riscvcheri.c` L54-L93); otherwise
   `riscv_cheri_init` panics with "CHERI: Invalid root cap" (L33-L36).
   A PCC attenuated only in permissions therefore panics the guest.
3. **The kernel clears `ddc` itself.** `csrw CSR_DDC, zero` follows the
   root's use, on the boot hart and on secondary harts (head.S L418,
   L211). The guest's first `ddc` authorizes nothing after its first few
   instructions, which make no data access before `enter_capmode`.
4. **The kernel's addresses span both ends of the address space.** It
   splits its root into kernel authorities over `[2^63, 2^64)` and user
   authorities over `[0, 2^63)` (riscvcheri.c L110-L161). A capability's
   bounds are one interval with no wraparound, so the only interval that
   holds both halves is the whole space.
5. **The plain `linux` flavour under the CHERI-aware monitor** runs with
   `henvcfg.CRE` set and in Integer Pointer Mode: `ddc` authorizes its
   data accesses and PCC its fetches, and it never changes either. Its
   kernel addresses are in the upper half and its user addresses in the
   lower half, so the same interval argument applies: any smaller bound
   faults its first access outside it. Its accesses need R, W, and X,
   and its CSR accesses need PCC's ASR permission, without which the
   emulator raises a CHERI fault (`target/riscv/csr.c` L5019-L5033).
   Dropping the capability
   load and store permission from its `ddc` and PCC would be accepted by a
   guest that never uses capabilities, but changes the reach of none of
   its accesses (section 4, A).
6. **What a bounded first PCC does (E4).** With PCC and `ddc` bounded to
   the guest's window `[0x80000000, 0x84000000)`, each CHERI guest took
   one CHERI tag fault in early boot, at `sc ca1, 0x0(ct0)` in
   `__pi___memset`, through `ct0` at an address inside the bounds
   (`0x80388000`). That fits the kernel's first data capability, made by
   `scaddr ct0, ct0, x0` at address 0, having lost its tag as
   unrepresentable so far outside a 64 MiB bound; this is an inference
   from the source, not traced. The fault was delegated to the guest,
   whose early trap vector parks the hart; the guest printed nothing.

### 3.3 The G-stage and capability flow (B)

1. **The emulator has a capability-write PTE bit, off by default.** For
   v0.9.3 it defines CW as bit 60 and CRG as bit 59
   (`target/riscv/cpu_bits.h` L798-L799). The CPU property `cheri_pte`
   (alias `Svucrg`), which enables Zcheripte, defaults to false
   (`target/riscv/cpu.c` L2337-L2338). The `rv64` CPU that every CHERI
   run uses (`mvp/tests/run-qemu.sh` L133-L136, L158;
   `mvp/tests/session-typist.py` L93; `mvp/tools/cheri-live.sh` L127)
   does not set it (`rv64_base_cpu_init`, cpu.c L493-L504); the
   emulator's CPU models for Codasip's cores do (cpu.c L551-L556,
   L592-L597).
2. **When it is on, every translation stage checks CW on a capability
   store.** In the walk, a store of a tagged capability (`MMU_DATA_CAP_STORE`)
   through a leaf without CW fails as a CHERI failure (cpu_helper.c
   L1322-L1333). In a two-stage walk, a G-stage failure is raised as cause
   23, a store/AMO guest-page fault (L1597-L1600), with `htval` the GPA
   shifted right by 2 (L1881-L1883, L2457) and `hstatus.GVA` set (L2322,
   L2465); a VS-stage CHERI failure is a store page fault, cause 15
   (L1601-L1604).
   CW on a non-leaf entry fails the walk regardless of the property
   (L1186-L1192).
3. **Why CHERI guests boot today.** The branch's G-stage window leaves
   carry no CW (`mvp/src/mvp-gstage.h` L71-L77: "G, RSW, PBMT, N, and
   reserved bits 0"; the walker refuses any high bit, `mvp/src/mvp-gstage.c`
   L455), and the harness leaves `cheri_pte` off, so no stage checks CW.
   With it on, today's image stops at the guest kernel's first capability
   store (E1). This reconciles the beryllium-cheri dossier's row 3 with
   the passing runs; it also corrects two statements of that repository's
   proof of concept, that "This QEMU reports no `PTE.CW` support"
   (`experiments/be-cheri-poc.md`, "Gaps"; that was the guest's own probe
   result with the property off) and that closing the channel flow "needs
   a G-stage capability control that v0.9.3 does not have"
   (`experiments/cheri-guest.md`, "Result"), which holds of the
   specification, not of this emulator. This plan edits nothing there.
4. **The cause, `htval`, and `htinst` observed.** A tagged `sc` to a
   CW-clear G-stage leaf gave `cause=0x17`, `htval` = GPA >> 2, and
   `htinst=0x0`, from VS mode with VS-stage translation off (E1) and on
   (E3). The emulator forms `htinst` by transforming the instruction
   (L2335); it gave zero for `sc` in both runs, which the denial leaf's
   `htinst_accepted` accepts (`mvp/src/mvp-sbi.c` L213-L234).
5. **The denial leaf refuses it today.** `be_mvp_denial_decide` accepts
   only a fault from VU mode, and only on an unmapped GPA or a leaf
   without W (`mvp/src/mvp-sbi.c` L279-L299). A capability-store fault
   happens on a leaf that has W, so it is not a denial: the run ends with
   `BE_MVP:FAIL guest-page-fault` and a `BE_MVP:DETAIL` line that carries
   the cause, `htval`, `htinst`, and `spvp` (E1, E3). The monitor can tell
   it from an ordinary write denial by its own walked leaf alone: an
   integer store never faults on a leaf with W, so a cause-23 fault on a
   leaf with W and without CW is a tagged capability store. (The emulator
   also reports a PMP failure after a successful G-stage walk as cause 23;
   the declared pages are RAM that the firmware's PMP leaves open to
   S-mode accesses, a guest's included, so that case does not arise
   there.)
6. **The G-stage cannot strip or trap capability loads on this
   emulator.** With Zcheripte, CW clear also makes capability loads
   return untagged, and CRG against `sstatus.UCRG` traps them. The walk
   sets these for either stage (L1476-L1499), but the two-stage fill keeps
   only the VS stage's: "CHERI's load-side caveats are enforced only on
   the guest tables at the moment" (L1835-L1859). The monitor needs no
   load control: with CW clear in every domain's leaf of a page, no guest
   can store a tag there, the monitor clears declared pages with integer
   stores, and integer stores clear tags.
7. **The emulator's TLB makes the store check depend on the page's tag
   block.** A two-stage TLB fill keeps a store-trap flag only if both
   stages set it (L1859), so a G-stage CW-clear leaf alone leaves none.
   The emulator adds a refill trap to every fill of a page whose 64 KiB
   host tag block holds no tag yet (`target/cheri-common/cheri_tagmem.c`
   L102, L857-L866), and a tagged store through such an entry is refilled
   and checked (`accel/tcg/cputlb.c` L1588-L1596). So the check holds
   while no tag has ever been stored in the declared pages' 64 KiB block:
   today they are the only things in `[0x118000000, 0x118010000)`, the
   second window ending at `0x118000000` (E1's `BE_MVP:03` lines). E3
   made an integer store before the tagged store, through the same
   mapping, and the check held. Stop 12 keeps that layout fact.
8. **Guest user space cannot make that store under an unmodified
   guest kernel.** CHERI Alliance Linux
   grants a mapping capability load and store permission only for
   `MAP_PRIVATE` or `MAP_ANONYMOUS` mappings
   (`arch/riscv/include/asm/mman.h` L28-L38; `lib/user_ptr.c` L122-L146),
   and sets CW in a user PTE only for those (`arch/riscv/mm/init.c`
   L381-L389). The init's `/dev/mem` channel mapping is `MAP_SHARED`, so
   its capability lacks the permission (E2's dump: `rw....se` against
   `rw.C.lse`), and the emulator stores a capability through such an
   authority with its tag cleared, without a fault
   (`target/cheri-common/op_helper_cheri_common.c` L1860-L1873; E2). A
   guest kernel can: its own mappings carry CW when the hart needs it
   (`arch/riscv/include/asm/pgtable.h` L179-L185) and its data
   capabilities carry the permission (E3).
9. **The guest kernel adapts to Zcheripte by itself.** It probes whether
   its PTEs need CW with a capability store at boot and sets CW in every
   leaf when they do (`arch/riscv/mm/init.c` L870-L886, L979-L985); it
   then prints `PTE.CW support: yes` (riscvcheri.c L40-L41; E2, E3). The
   device trees need no new extension name.
10. **The specification's position.** RISC-V CHERI's RVY v0.9.10.1 says
    the capability field "is not currently defined in G-stage PTEs and so
    remains reserved", and the task group lists G-stage capability control
    as future work (riscv-cheri #1178, background in #1171), as the
    beryllium-cheri dossier records (rows 3 and 4, and section 8b). This
    plan found no G-stage definition for v0.9.3. The control planned here
    is therefore the emulator's behaviour, stated as such.

### 3.4 The guest's own CHERI faults (C)

1. **A purecap process's bounds fault is delivered to it, and the run
   continues (E2).** A forked child loaded one byte past a capability
   bounded to 16 bytes; the guest kernel reported `xtval2=0x10004 (length
   violation, data fault due to load store or AMO)` and delivered
   `SIGSEGV` with `si_code` 12, `SEGV_CAPBOUNDSERR`
   (`include/uapi/asm-generic/siginfo.h` L242-L246;
   `arch/riscv/kernel/traps.c` L525-L536), at the faulting address; the
   child's handler exited with status 0, and both domains completed.
2. **The kernel's report of it would fail the capture check.** For a
   fault from user mode, `__do_trap_cheri` prints a report, the registers,
   the code, and a stack dump whenever `show_unhandled_signals` is set,
   whether or not the process handles the signal (traps.c L538-L564); it
   is set to 1 (L39) and adjustable only through the `exception-trace`
   sysctl (`kernel/signal.c` L5031-L5041), which needs `CONFIG_PROC_SYSCTL`.
   The guest's tinyconfig kernel has `CONFIG_SYSCTL_EXCEPTION_TRACE` but
   neither `CONFIG_PROC_FS` nor `CONFIG_PROC_SYSCTL`. The dump holds
   "Call Trace:", one of every scenario's rejected substrings (E2).
3. **A bounds fault in a usercopy is silent (E2).** `write(2)` of 64 bytes
   from a capability bounded to 16 returned `EFAULT`, and of the same
   bytes from the whole buffer returned 64. The kernel copies through the
   user's capability with fixups (`arch/riscv/lib/uaccess.S` L100-L102,
   L256-L269); `access_ok` checks the address range only
   (`include/asm-generic/access_ok.h` L31-L42); a kernel-mode CHERI fault
   is fixed up before any report (traps.c L541-L544).
4. **The checker needs** the new lines in the CHERI flavour's
   expectations (`mvp/tools/gen-scenario.py`'s `FLAVOUR_LINES` and
   `flavour_lines`, L367-L400, apply the flavour's lines today) and rules
   that read their values, not only their presence (section 6).

### 3.5 The monitor's accesses to guest memory (D)

The monitor copies guest bytes in four places, through integer pointers
made from HS physical addresses, authorized by the monitor's own `ddc`:
the DBCN write copy (`mvp/src/mvp-hartmain.c` L263-L277), the DBCN read
copy (L288-L308, through `be_mvp_input_serve`), and the boot-time window
clearing and payload placement (`mvp/src/mvp-runtime.c` L1360-L1480). The
management calls carry integers only, and the rings live in the monitor's
own hart region. Each copy is guarded by a window check in C, host-tested
(the DBCN window cases of `mvp/tests/sbi-test.c`) and exercised by the
hostile runs. The monitor's C is compiled by plain GCC and Clang, so a
capability bounded to a window can be used only from hand-written
assembly in Capability Pointer Mode, as the vector does.

### 3.6 The scratch experiments (scratch experiment, not evidence)

Each ran on 2026-11-06 between 20:52 and 21:12 UTC on the development
workstation, one QEMU at a time, with no other QEMU running. The scratch
trees were shallow clones of `aa0aea14` under a git-ignored `build/scratch/`
of a separate clone; nothing tracked was edited and nothing was committed.
Every boot used the invocation of `mvp/tests/run-qemu.sh`'s `boot`
(QEMU's `virt` machine with eight harts and 8 GiB, the firmware as
`-bios`, the boot ELF as `-kernel`, the serial console to a file, no
monitor, no reboot), with the CPU string in the table, beryllium-cheri's
`build/qemu-ia-fix` emulator (`qemu-system-riscv64cheristd`, SHA-256
`b5dfea44…`), and the SDK's purecap OpenSBI (`fw_dynamic.bin`,
`e0aeeae9…`, the branch page's). A boot whose firmware started on a
domain hart was to be repeated; none was.

| ID | What changed in the scratch copy | CPU | Result |
| --- | --- | --- | --- |
| E1 | Nothing: the branch's own GCC te-poc boot image, as built in another clone at `aa0aea14` (SHA-256 `82e6c96a…`), only read and run | `rv64,h=true,cheri_pte=on` | The run stopped at domain 0's first exit: `BE_MVP:FAIL guest-page-fault`, `BE_MVP:DETAIL domain=0 hart=1 cause=0x17 pc=0x8020010a tval=0x804805d0 htval=0x20120174 htinst=0x0 spvp=1 vsatp=0x0 exits=1`. The instruction at the kernel's `_start + 0x10a` is `sc ct2, 0x0(ct2)`, the kernel's first capability store (`_start_kernel`, before paging) |
| E2 | `mvp-gstage.c`: CW (bit 60) in every window leaf, and the window walker accepting exactly that high bit; `mvp-init.c`, purecap only, after the writer's line 07: a child's load one byte past a 16-byte capability, with a `SIGSEGV` handler; two `write(2)`s of 64 bytes to a pipe, from the 16-byte capability and from the whole buffer; an integer store, then a tagged store of the mapping's own capability, at the channel mapping's offsets 64 and 128. Guest built by `build-guest-cheri.sh --unpinned` with the SDK at the branch's CHERI pins (the scratch `cheri-pins.txt` re-pinned), image by `make ... gcc/te-poc/be-mvp-boot.elf` (SHA-256 `3c2a2cc1…`) | `rv64,h=true,cheri_pte=on` | Both guests booted and printed `PTE.CW support: yes`; te-poc's three denials were delivered as in every run; the child's handler got `signo=11 code=12` at `base + 16` and the run continued; `write` gave `-1`, `errno=14` from the 16-byte capability and 64 from the whole buffer; the user's tagged store to the channel returned, and the slot read back with tag 0 (the mapping's capability lacks the capability permission); `RESULT pass` for both, `BE_MVP:13 RUN_COMPLETE`, `BE_MVP:14 SHUTDOWN` |
| E3 | E2's changes, plus `mvp/guest/mgmt/be-mgmt.c`'s module init, purecap kernel only: a tagged store into its own static data and a readback; `memremap` of GPA `0x84000000`; an integer store at offset 64 and a readback; a tagged store of the mapping's capability at offset 128 and a readback (`memremap` added to the scratch `cheri-ksyms.txt`); the writer's init loading `/be-mgmt.ko` after E2's probes. Image SHA-256 `8c015002…`, run twice | (a) `rv64,h=true,cheri_pte=on`; (b) `rv64,h=true` | (a) `own-ram cap-store tag=1`, `channel int-store value=0x5678`, then `BE_MVP:FAIL guest-page-fault`, `BE_MVP:DETAIL domain=0 hart=1 cause=0x17 pc=0xffffffff0035a138 tval=0xffffffc600008080 htval=0x21000020 htinst=0x0 spvp=1 vsatp=0x800010000008099d exits=381`: GPA `0x84000080`, the channel. (b) `PTE.CW support: no`; the same store returned and read back `tag=1` in the channel page; both domains `RESULT pass`, `RUN_COMPLETE`, `SHUTDOWN` |
| E4 | A second scratch copy with the branch's guest (the pinned build, `pins=match`) and `mvp-trap.S`'s arm helper writing `sepcc` and the guest's first `ddc` (frame slot 0) as the monitor's `ddc` bounded by SCADDR and SCBNDSR to `[0x80000000, 0x84000000)`. Image SHA-256 `49f1d858…`; QEMU also given `-d int`, and killed after 20 seconds | `rv64,h=true` | After entering its guest, each domain hart took exactly one trap, `cause:0x1c ... epc:0x8035d982, tval:0x80388000, desc=cheri_fault` ("Tag Violation, caused by register 5"), at `sc ca1, 0x0(ct0)` in `__pi___memset`; neither guest printed a line |

The scratch patches, the console logs, and the trap log are kept,
uncommitted, in that clone's `build/scratch/` for the owner session; the
scratch build trees were deleted. A re-run follows the rows above.

## 4. Options and defaults

| Item | Options | Default and reason |
| --- | --- | --- |
| **A. The guests' first capabilities** | (a) Bound PCC and `ddc` to the GPA window. (b) Attenuate only their permissions. (c) Give the purecap flavour a null first `ddc`. (d) Make the device-tree capability read-only too (beryllium-cheri's handoff lists it, untested). (e) Keep r4 and make it a checked fact: the CHERI expectations require each guest's `CHERI: Root capability` line with the whole address space | **(e).** (a) stops a CHERI guest in its first C code (E4) and would panic it anyway (section 3.2, item 2), and confines nothing the G-stage does not, since bounds apply to addresses in the guest's own translation; for the `linux` flavour no smaller interval serves both halves (item 5). (b) panics the purecap guest (item 2) and changes the reach of no access of the `linux` flavour. (c) is feasible and meaningless: the kernel clears `ddc` itself and derives everything from PCC. (d) confines nothing while the guest holds a root PCC. Q6 |
| **B. Capability flow through declared pages** | (a) Leave it: under an unmodified guest kernel, user space cannot move tags through `MAP_SHARED` mappings (section 3.3, item 8). (b) Zcheripte on, CW in every window leaf, none in a declared page's leaf; a tagged store to a declared page ends the run (fail closed). (c) As (b), with a new denial kind for that fault, injected as a store/AMO access fault. (d) Make one endpoint of each channel CHERI-off (`henvcfg.CRE` clear) | **(b).** It makes "no tag crosses a declared page" a monitor-set property instead of a property of both guest kernels, under this emulator. Fail closed matches the MVP's treatment of every other guest-page fault from VS mode, needs no change to `mvp-sbi.c` (in M8's frozen record), and only a guest kernel that stores a tag there reaches it. (c) is Q1's alternative. (d) changes the guest, not the page, and loses CHERI for that guest |
| **C. The guests' own CHERI faults** | (a) Nothing: delegation exists. (b) Tests that must fault in the guest: the bounds fault in a child and the usercopy `EFAULT`, the guest kernel's report silenced around the deliberate fault through the `exception-trace` sysctl, which needs `CONFIG_PROC_FS` and `CONFIG_PROC_SYSCTL` in the CHERI kernel fragment. (c) As (b), with the checker accepting exactly one declared report block instead. (d) The usercopy test alone | **(b), in te-poc's two domains.** It is the simplest real demonstration, and it keeps every rejected substring in force. Q2 (how the report is handled) and Q3 (where the tests run) |
| **D. The monitor's own accesses to guest memory** | (a) Defer. (b) Window-bounded capabilities for the two DBCN copies, through new assembly helpers in Capability Pointer Mode. (c) As (b), plus the boot-time clearing and placement | **(a), deferred.** Estimated cost of (b): 60 to 100 lines of new privileged assembly, 20 to 40 of C at the call sites, and 250 to 400 of image-check rules and mutations; (c) about doubles it. It protects against a defect in the monitor's own window checks, which are host-tested and exercised by the hostile runs, so it answers a different question from the human's. It belongs with a purecap-monitor study (the beryllium-cheri dossier's new row B), a plan of its own. Q5 |

## 5. Work packages

| WP | Delivers | Exit |
| --- | --- | --- |
| CE-1 | This plan and its packet | Accepted |
| CE-2 | Zcheripte for every CHERI run and the G-stage capability-write control (B) | `cheri-check` passes all three parts with Zcheripte on; part 2's 162 images equal the reference's; the new host-test cases and the `channel-cw` image pass |
| CE-3 | The guests' own CHERI faults, which must occur (C) | `cheri-check` passes with the new lines in te-poc's runs; the `cheri-fault-hs` image fails as declared; every new mutation is rejected |
| CE-4 | A guest kernel's tagged store to the channel page (B), and its control run | The `cap-store` image ends at the declared G-stage fault with Zcheripte on and lands the tag without it; every new mutation is rejected |
| CE-5 | The branch page's records, section 8's words on the page, and the result packet | The last full `cheri-check` and the plain variant's `make -C mvp check` pass as the gates below state, on the exact result commit; the packet is presented |

They run in that order, each ending in its own commit or commits on the
work branch. Code, tests, tools, and generated expectations are written
by sub-agents on `claude-opus-5.5` at `max` effort with the
`long_context` tier; the session model writes the texts, reviews each
commit line by line before the next, runs the checks, and writes the
records and the packet.

**Gates for every commit that changes code:**

- `mvp/tools/cheri-check.sh` passes all three parts. Part 2's 162 boot
  images equal the reference, the latest `main` commit merged into the
  branch, byte for byte. A run that fails by the emulator's wake-up stall
  is run again, as the branch page says; no expectation is relaxed.
- `make -C mvp check`, the plain variant, passes every step but
  `claim-ledger-check`, which fails for the same seven files as today
  (`mvp/src/mvp-runtime.c`, `mvp/tests/check-capture.py`,
  `mvp/tests/check-image.py`, `mvp/tests/sbi-test.c`,
  `mvp/tests/session-typist.py`, `mvp/tools/gen-scenario.py`, and
  `mvp/tools/port.py`) and no other.
- `git diff --check`, and the documentation source check for every
  documentation change.

### CE-2 Zcheripte and the G-stage capability-write control

- **The emulated hart.** Every CHERI run's CPU gains `cheri_pte=on`:
  `mvp/tests/run-qemu.sh` and `mvp/tests/session-typist.py` take a
  CHERI-only addition to their CPU strings from the environment, which
  `mvp/tools/cheri-check.sh` sets for parts 1 and 3 (Q7);
  `mvp/tools/cheri-live.sh` adds it to its printed commands. The plain
  variant's runs, through the tool lock's QEMU, never see it.
- **The builder and the walker**, in `mvp/src/mvp-gstage.c`, under
  `BE_MVP_CHERI`: `write_window` sets CW in every 2 MiB window leaf, and
  `walk_l1` requires exactly CW among a window leaf's high bits. The root
  walker keeps refusing any high bit in the pointer (the emulator also
  refuses CW there), and `walk_l0` keeps comparing each declared page's
  leaf with the exact value of its rights, which holds no CW. Without
  `BE_MVP_CHERI` the file's code is the development line's.
- **Host tests.** `mvp/tests/gstage-test.c` gains cases for the CHERI
  build, built with `-DBE_MVP_CHERI` as `sbi-test` is: CW in every window
  leaf and in no other entry; the walker refusing a window leaf without
  CW, with CRG (bit 59) or another high bit, a channel or page leaf with
  CW, and a pointer with CW. The plain build's cases and assertion count
  stay. `HOST_ASSERTIONS_gstage` gains a CHERI value, as
  `HOST_ASSERTIONS_sbi` has.
- **Expectations.** The CHERI flavour's domain lines gain the guest
  kernel's `[<s>] CHERI: Selected SATP mode: 0x8000000000000000 PTE.CW
  support: yes` and (A, Q6) its `CHERI: Root capability:` line with the
  whole address space, in every CHERI scenario, through
  `mvp/tools/gen-scenario.py`'s CHERI rules. `scenario.json` stays the
  development line's.
- **One negative image, `channel-cw`** (section 6).
- **Exit:** as the table above, with parts 1 and 3's runs and sessions all
  passing under Zcheripte, anchor's and two-guests' included, which no
  scratch experiment ran.

### CE-3 The guests' own CHERI faults

- **The tests**, in CHERI-only files built only for the `cheri-linux`
  flavour (`mvp/guest/cheri/cheri-tests.c`, linked into the CHERI init by
  `build-guest-cheri.sh`), called from te-poc's two roles through a hook
  in `mvp/guest/mvp-init.c` under `__CHERI_PURE_CAPABILITY__`, after line
  02 (Q3):
  1. the init writes `0` to `/proc/sys/debug/exception-trace` (mounting
     `proc` first) and prints the value it reads back;
  2. a forked child, with a `SA_SIGINFO` handler for `SIGSEGV`, loads one
     byte past a capability bounded to 16 bytes; the handler prints the
     signal, `si_code`, the capability's base, and `si_addr`, and exits 0;
  3. `write(2)` of 64 bytes to a pipe, from the 16-byte capability and
     from the whole buffer, each result printed;
  4. the init writes `1` back and prints the value it reads back.

  The lines are `MVPINIT 14 CHERI ...`, a number no init line uses; their
  exact words are fixed in CE-3 and checked by value (section 6).
- **The CHERI kernel fragment** (`mvp/guest/cheri-kernel.config`) gains
  `CONFIG_PROC_FS=y` and `CONFIG_PROC_SYSCTL=y` (Q2); its Image is checked
  against `BE_MVP_KERNEL_FILE_MAX` (4 MiB; 3,264,512 bytes today).
- **Pins.** The CHERI guest's outputs move and are re-pinned in
  `mvp/guest/cheri-pins.txt`, as the branch's procedure says; no external
  pin moves.
- **One negative image, `cheri-fault-hs`** (section 6).

### CE-4 A guest kernel's tagged store to the channel page

- **The store**, made by a CHERI-only guest kernel module,
  `mvp/guest/cheri/be-cheri-store.c` (Q11), built out of tree by
  `build-guest-cheri.sh` and added to the CHERI initramfs only. At load it:
  1. stores a tagged capability into its own data and prints the tag it
     reads back;
  2. maps the GPA its parameter names with `memremap`, stores an integer
     at offset 64, and prints the value it reads back;
  3. stores the mapping's own tagged capability at offset 128 and prints
     the tag it reads back, a line printed only if the store returns.

  `memremap` and `memunmap` join `mvp/guest/cheri-ksyms.txt`.
- **The image `cap-store`**, a te-poc boot image for the CHERI flavour
  only, whose first domain's device tree (`gen-dts.py`'s CHERI rules)
  names `rdinit=/init-cap-store`, a CHERI-only link to `/init`. That init
  loads the module with the channel's GPA before its pattern write, so
  that in the control run the pattern's integer stores clear the tag
  before the reader looks.
- **Two runs per toolchain:** with Zcheripte on, it must end at the
  store; without it, the control, the store must land (section 6).

### CE-5 Records and the result packet

- The branch page gains "What CHERI enforces on this branch" with
  section 8's words, its r4 residual updated with section 3.2's evidence,
  its check's new counts, and the results of the last runs.
- One result packet, in the human-review-summary form, on the exact
  result commit, asks for `accept <sha>`, `revise: ...`, or `defer`.

## 6. Tests that must fault

Each item below is judged by `mvp/tests/check-capture.py`'s CHERI rules
(`--monitor cheri`) against expectations that `mvp/tools/gen-scenario.py`
generates for the CHERI flavour; each new rule has mutations of a passing
capture that it must reject, in the style of the branch's existing CHERI
mutations, and each new image has its own expectation. The runs join
part 1 of `cheri-check` for both toolchains.

| Test | Image or run | Expected trap or signal | What the capture checker must see | Mutations it must reject |
| --- | --- | --- | --- | --- |
| B1, the window leaves | Every CHERI run, Zcheripte on | None: the guest's capability stores to its own window succeed | `PTE.CW support: yes` in each CHERI guest | The line missing; `PTE.CW support: no` |
| B2, the monitor's own rule | `channel-cw`: a builder defect that also sets CW in each declared page's leaf (a variant macro, as `reader-write`'s `BUILDER_DEFECT`), the sealed record unchanged | None: refused at boot | `BE_MVP:FAIL gstage` before `BE_MVP:07`, with the walker's refusal of the level-0 leaf; no domain hart started | A `BE_MVP:07` line; the failure after a domain entered; another failure class |
| B3, the store | `cap-store`, Zcheripte on | Cause 23 from VS mode at the G-stage | In domain 0, the module's own-data tag 1 and its integer readback `0x5678`, then `BE_MVP:FAIL guest-page-fault` and `BE_MVP:DETAIL domain=0 hart=1 cause=0x17 ... htval=0x21000020 htinst=0x0 spvp=1` with a nonzero `vsatp` and `tval`'s page offset `0x080`; no line of the module after the store | `htval` of another page; `spvp=0`; a nonzero `htinst`; the module's post-store line present; the own-data tag 0; the integer readback missing |
| B4, the control | `cap-store`, Zcheripte off | None | `PTE.CW support: no`; the module's post-store line with tag 1; both domains' `RESULT pass`, `BE_MVP:13`, and `BE_MVP:14` | The post-store line with tag 0 or missing; a `BE_MVP:FAIL` |
| C1, a bounds fault in user space | te-poc's runs (both domains) | Cause 28 from VU mode, delegated to VS; `SIGSEGV`, `SEGV_CAPBOUNDSERR` | The trace line `0`, the child's line with `signo=11`, `code=12`, and `si_addr` equal to its base plus 16, the trace line `1`, in that order; no "===== CHERI exception" line; no monitor line (`BE_MVP:DENY` or `BE_MVP:FAIL`) for the fault | `code=2` (`SEGV_ACCERR`); `signo=7`; `si_addr` at the base or base + 17; a "no fault" line; the trace line `1` missing or `0`; a CHERI exception report |
| C2, a bounds fault in a usercopy | The same runs | Cause 28 from VS mode, delegated and fixed up; `EFAULT` | The 16-byte write's `-1` with `errno=14`, and the whole buffer's 64 | The bounded write returning 64 or 16; the whole write failing |
| C3, delegation is what lets the run continue | `cheri-fault-hs`: te-poc with bit 28 left out of `hedeleg` and of the required set (a variant macro over `mvp.h`'s and `mvp-trap.S`'s values) | Cause 28 reaches HS: terminal | `BE_MVP:09` with `hedeleg=0xb15d`; `BE_MVP:FAIL exception` and `BE_MVP:DETAIL` with `cause=0x1c`, `spvp=0`, and `tval` the faulting child's address, in whichever domain faults first; no line of that child after the trace line `0` | `hedeleg=0x1000b15d`; another cause; the run passing |

The image check (`mvp/tests/check-image.py`) learns the two new monitor
variants' values (`channel-cw`'s builder and `cheri-fault-hs`'s
`hedeleg`) through its variant specifications, each with a mutation; it
stays silent on C code, so the window leaves' CW is checked by the host
tests, the walker at every boot, and B1 to B4.

## 7. Tools, rules, and the soft limit

**Where the code goes.** CHERI-only code goes into CHERI-only files
(`mvp/guest/cheri/`, `mvp/guest/cheri-kernel.config`,
`mvp/guest/cheri-ksyms.txt`, `mvp/guest/cheri-pins.txt`,
`mvp/tools/build-guest-cheri.sh`, `mvp/tools/cheri-check.sh`,
`mvp/tools/cheri-live.sh`). Files shared with the plain variant get only
`BE_MVP_CHERI` or `__CHERI_PURE_CAPABILITY__` blocks, the CHERI rules of
the checkers and generators (`--monitor cheri`, `--guest-flavour
cheri-linux`), or the switches' conditionals in `mvp/Makefile`,
`mvp/guest.mk`, and `mvp/tools.mk`, each marked `beryllium-cheri:` where
the file allows a comment, so that a catch-up can find them.

**Rules the work keeps.** No expectation is relaxed at run time; every
new rule reads values, not only the presence of a line; the plain
variant's checker rules, mutations, and assertion counts stay as they
are; and no run depends on another's order.

**Soft limit (Q10).** Added lines by `git diff --numstat` from the
acceptance record to the result commit, tests and generators included,
Markdown and generated expectation files excluded and reported: **1,500
lines in all, of which at most 100 in `mvp/src/`**, each lane reported.
Estimates: `mvp/src/` 40 to 70 (the builder's and walker's CHERI blocks,
two variant macros); the CHERI guest files 250 to 350 (the tests about
120, the module about 70, the build script and initramfs entries about
60); the checkers, generators, harness, and host tests 550 to 800.
Exceeding a limit is stop 10: a re-evaluation of the limit, never a cut
of the work.

**Cost.** Part 1 gains eight runs (B2, B3, B4, and C3, for each
toolchain, B3 and B4 being two runs of one image) and longer te-poc runs:
about two to three minutes on the branch's check of about fourteen.

## 8. The claim boundary on the branch

The branch page's new section carries these words, with the run counts
filled in from the last check, and no other claim about CHERI
enforcement (Q12):

> On this branch, under emulation of CHERI v0.9.3 (CHERI Alliance QEMU at
> `008944fe` with beryllium-cheri's two local changes, its `cheri_pte`
> property on), the CHERI-aware monitor's G-stage leaves allow tagged
> capability stores to each domain's own window and refuse them to every
> declared page (the channel, request, response, and secret pages). In
> the branch's check, a guest kernel's tagged
> capability store to te-poc's channel page ended the run at the G-stage
> as a store guest-page fault, and the same store landed when the
> emulated hart lacked that property. Inside each CHERI Linux guest of
> te-poc, a purecap process's load one byte past a 16-byte capability was
> delivered to it as `SIGSEGV` with `SEGV_CAPBOUNDSERR`, and a `write(2)`
> through that capability returned `EFAULT`, while the run continued. The
> guests' first PCC and `ddc` remain the whole address space, which CHERI
> Alliance Linux requires. The G-stage control is this emulator's
> behaviour: the RISC-V CHERI specification leaves the field reserved in
> G-stage entries. These are emulation results for one emulator and one
> guest; they are not evidence for the MVP's claim and show nothing about
> CHERI hardware.

## 9. Stop conditions

Each returns the work to the responsible human.

1. Any of part 2's 162 plain boot images differs from the reference, or
   a change would make one differ.
2. Any change on `main`, any merge into it, or any push.
3. A change to an accepted byte or record (R0 to R7, B0 to B7, or the
   records under `mvp/results/` and `bringup/*/results/`), to
   `mvp/docs/claim.md`, to the claim ledger, to the plain variant's
   checker rules, mutations, or assertion counts, or to a file the ledger
   pins other than the seven named in section 5.
4. A change to a scenario's `scenario.json`, a policy text, the authority
   report's analyses, `mvp/guest/pins.txt`, or any input of the plain
   variant's guests.
5. Any input from Codasip's non-public sources.
6. A need to change the beryllium-cheri repository, its emulator build,
   or its toolchain (that repository's owner decides).
7. Any board command, or any kexec use.
8. A fact that contradicts section 3: under Zcheripte, a CHERI guest that
   does not boot with CW window leaves, or a run or session that fails
   other than by the recorded wake-up stall; a tagged store to a declared
   page that lands under Zcheripte, in either access order; a fault whose
   cause, `htval`, or `htinst` differs from section 3.3's; a bounds fault
   not delivered with `SEGV_CAPBOUNDSERR`, or one that ends the run; or a
   result that differs between the toolchains.
9. A need to change `mvp/src/mvp-sbi.c`, or to accept a fault from VS
   mode as a denial, beyond Q1's answer.
10. A soft limit exceeded: a re-evaluation of the limit, never a cut of
    the work.
11. A need to move a CHERI external pin (the SDK, LLVM, Linux, musl,
    BusyBox, OpenSBI, or QEMU); re-pinning the CHERI guest's own outputs
    is the branch's procedure, not a stop.
12. A layout change that puts memory that can hold tags in the same
    64 KiB-aligned host block as a declared page (section 3.3, item 7).
13. Any test whose outcome needs an expectation relaxed at run time.
14. A need to write planning text on `main`'s pages (`planning/roadmap.md`,
    `planning/HANDOFF.md`), which are `main`'s and would conflict at the
    next catch-up.

## 10. Risks

| Risk | Response |
| --- | --- |
| The G-stage control is emulator behaviour, not specified (section 3.3, item 10), and may change or vanish in a later emulator | Stated as such in section 8; a new emulator pin is stop 11, and B3 and B4 fail if the behaviour changes |
| The emulator's store check depends on the declared pages' tag block (section 3.3, item 7) | B3 keeps the integer-then-capability order E3 used; stop 12 keeps the layout fact |
| Zcheripte breaks a scenario no experiment ran (anchor, two-guests, the sessions, part 3) | CE-2's exit; stop 8 |
| The guest kernel's report or its handling of `MAP_SHARED` changes with a new CHERI Linux pin | The C and B expectations fail; a new pin is stop 11 |
| Silencing the exception trace hides another fault in that window | The window is the child's one fault; the restore line is checked by value (C1) |
| The `/proc` the C tests need widens the CHERI guest | Only the CHERI flavour's kernel; the alternative is Q2's |
| The wake-up stall fails a run | The branch's rule: read the capture, run the check again |
| A catch-up from `main` conflicts with the CHERI code | CHERI code in CHERI-only files; marked blocks elsewhere (section 7) |
| The results are read as more than emulation evidence | Section 8's fixed words; the claim's forbidden phrasings avoided in every new text |
| The check's time grows | About two to three minutes more (section 7) |

## 11. Open questions and defaults

| ID | Question | Default | Consequence and alternative |
| --- | --- | --- | --- |
| Q1 | What does the monitor do with a tagged store to a declared page? | Fail closed: the existing `BE_MVP:FAIL guest-page-fault` with its `BE_MVP:DETAIL`; `mvp-sbi.c` unchanged | Alternative: a denial kind for a cause-23 fault on a leaf with W and without CW, injected as a store/AMO access fault, for VU and VS origins; it changes `mvp-sbi.c`, which M8's frozen record names, and extends the denial model to faults from VS mode on this branch |
| Q2 | How is the guest kernel's report of the deliberate user fault kept out of the capture? | The `exception-trace` sysctl set to `0` around it and back to `1`, with `CONFIG_PROC_FS` and `CONFIG_PROC_SYSCTL` in the CHERI kernel fragment | Alternatives: the checker accepts exactly one declared report block (no kernel change; a narrowly scoped exemption of "Call Trace:" inside that block, with mutations); or the usercopy test alone (no user-mode fault) |
| Q3 | Where do the C tests run? | te-poc's two domains, and so its variants | Alternative: every domain of every CHERI scenario, which touches anchor's timed protocol and every variant's expectation |
| Q4 | Is the Zcheripte-off control (B4) kept? | Yes: it shows the store is real, so B3 cannot pass vacuously | Alternative: B3 alone |
| Q5 | The monitor's own accesses through window-bounded capabilities (D)? | Deferred (section 4) | Alternatives: the two DBCN copies now; or those and the boot-time copies |
| Q6 | Is the guests' root capability made a checked line (A, (e))? | Yes | Alternative: r4 stays a source reading on the page |
| Q7 | Zcheripte for part 3 (the Linux guests under the CHERI-aware monitor) and the live runs too? | Yes: one emulated hart for the branch | Alternative: part 1 only, leaving part 3 on today's hart |
| Q8 | `henvcfg.CRE` for the `linux` flavour under the CHERI-aware monitor? | Unchanged (set) | Alternative, a later plan: clear it for that flavour, as RVY recommends for unmodified guests, which changes part 3's purpose and the monitor's armed value per flavour |
| Q9 | Where does the work land? | On `beryllium/cheri-enforcement` from the commit that records the acceptance; the owner session merges it into `beryllium/cheri-platform` when the result is accepted | Alternative: directly on `beryllium/cheri-platform` |
| Q10 | The soft limit? | 1,500 lines, at most 100 in `mvp/src/` (section 7) | Another limit |
| Q11 | The test module's licence? | `GPL-2.0-only`, as `mvp/guest/mgmt/be-mgmt.c`: it is linked into the GPL-2.0-only guest kernel | Alternative: no module, a test hook in `be-mgmt.c` under the CHERI kernel's macro |
| Q12 | The branch page's claim words? | Section 8's, with the counts filled in | Revised words in the reply |

## What acceptance would authorize

Accepting this exact commit, with Q1 to Q12 at their defaults or as
answered, would authorize work packages CE-2 to CE-5 under the stop
conditions above:

- on branch `beryllium/cheri-enforcement`, from the commit that records
  the acceptance, merged into `beryllium/cheri-platform` by the owner
  session when the result is accepted (Q9);
- the code, tests, tools, expectations, and records of section 5, written
  as section 5 says;
- builds and QEMU runs on the development workstation with the CHERI
  inputs from beryllium-cheri, only read;
- one result packet at the end.

It would authorize nothing else: no push of any branch, no merge into
`main`, no change on `main`'s pages, no publication, no board command and
no kexec use, no change in the beryllium-cheri repository or to any
external pin, no change to the MVP's claim or ledger, and no claim beyond
section 8's words. The record of this plan's use of beryllium-cheri in
that repository's `COLLAB.md`, if wanted, is the owner session's, under
that ledger's rules.
