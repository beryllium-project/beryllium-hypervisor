<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The CHERI platform branch: CHERI enforcement, the result (review packet)

This is the result packet of the [CHERI enforcement plan](cheri-enforcement-plan.md),
accepted on 2026-11-06 at exact commit `9ec57998` (`accept 9ec57998`, Q1
to Q12 at their defaults; its
[review and acceptance record](cheri-enforcement-plan-review-summary.md)).
The plan answers the responsible human's question of that day, "on cheri,
does it actually enforce anything during these tests, or it just enabled &
running?", for the CHERI platform branch alone. Its work packages CE-2 to
CE-5 ran on the local branch `beryllium/cheri-enforcement` from the
acceptance record `89ab3ac3`, behind the MVP 1.0 release path, which had
priority; CE-4 resumed on the human's form answer `cheri_ce4=resume`
(2026-11-07), with the soft limit raised to 2,000 lines by
`cheri_limit=true` (the plan's erratum 1). Code, tests, and generated
expectations were written by a `claude-opus-5.5` sub-agent; the owner
session reviewed each commit line by line and wrote the texts. This packet
asks for the human's decision on the exact result commit.

## Decision record

The responsible human accepted the exact result commit
`3998e34ea09fabaea324b14863b6318994d86a13` on 2026-11-07 in the human's
time zone (2026-11-08 UTC) by the instruction `accept 3998e34e, merge and
push`, with the departures of section 3 as presented. The work packages
CE-2 to CE-5 are complete, and this packet is their review and acceptance
record.

On the same instruction, under the plan's Q9, the owner session
fast-forwards `beryllium/cheri-platform` from `aa0aea14` to the commit
that records this decision, over the plan, its acceptance record, CE-2,
CE-3, erratum 1, CE-4, CE-5, and this packet, and pushes it to the
private `origin`. `beryllium/cheri-enforcement` stays local. No successor
plan is started; publication and any merge into `main` each still need
their own instruction.

Sections 1 to 9 below are the packet as presented, unchanged.

## 1. Decision summary

| Field | Content |
| --- | --- |
| Review target | Exact commit `3998e34ea09fabaea324b14863b6318994d86a13` (CE-5), on the local branch `beryllium/cheri-enforcement`, over CE-4 `9ab49914`, erratum 1 `61c752b1`, CE-3 `15e25343`, and CE-2 `20af3dac`, from the plan's acceptance record `89ab3ac3`. The branch is a fast-forward of `beryllium/cheri-platform` (`aa0aea14`, on the private `origin`) |
| Current status | Implemented and checked (section 6): each work package reviewed line by line by the owner session; at the exact result commit, the branch's full check, `mvp/tools/cheri-check.sh`, passes all three parts, and the plain variant's `make -C mvp check` passes every step but `claim-ledger-check`, which fails as before on the seven files the CHERI split changes. Not reviewed or accepted by the human |
| Decision requested | Accept `3998e34e`, request revisions, or defer. Under the plan's Q9, acceptance lets the owner session merge the work into `beryllium/cheri-platform` |
| Successor status | No successor is planned or started. Pushing `beryllium/cheri-platform`, publication, and any merge into `main` each need their own instruction |
| Publication status | Nothing pushed. The work branch is local, in the CHERI clone and imported into the canonical checkout |

**Action expected:** read sections 3 and 5 and the branch page's new
section, then reply `accept 3998e34e`, or ask for revisions.

## 2. Deliverables

| Commit | Paths | Purpose | Boundary | Your question |
| --- | --- | --- | --- | --- |
| CE-2 `20af3dac` | `mvp/src/mvp-gstage.c` (26 lines, under `BE_MVP_CHERI`), `mvp/tests/gstage-test.c`, `mvp/tests/run-qemu.sh`, `mvp/tests/session-typist.py`, `mvp/tools/cheri-check.sh`, `mvp/tools/cheri-live.sh`, `mvp/tools/gen-scenario.py`, `mvp/tests/check-capture.py`, `mvp/tests/check-image.py`, `mvp/Makefile` | The emulator's Zcheripte (`cheri_pte=on`) for every CHERI run; the capability-write bit (CW) in each domain's window leaves and in no declared page's leaf, the walker refusing it elsewhere; the `channel-cw` negative image (B2); each CHERI guest's root capability and `PTE.CW support: yes` lines required (B1, Q6) | The monitor's G-stage builder and walker, CHERI build only; the plain variant's images unchanged | Is the CW control's reliance on this emulator's behaviour (section 3) acceptable for the branch? |
| CE-3 `15e25343` | `mvp/guest/cheri/cheri-tests.c` and `.h` (new), `mvp/guest/mvp-init.c` (a `__CHERI_PURE_CAPABILITY__` hook), `mvp/guest/cheri-kernel.config`, `mvp/guest/cheri-pins.txt`, `mvp/src/mvp.h`, `mvp-trap.S`, `mvp-runtime.c` (12 lines, the `cheri-fault-hs` switch), the checkers and generator, `mvp/Makefile` | The guests' own CHERI faults, which must occur while the run continues (C1, C2), and `cheri-fault-hs`, whose `hedeleg` leaves cause 28 to HS (C3) | Guest user space and the guest kernel's fix-up; the monitor's delegation | Is `CONFIG_COREDUMP=y` in the CHERI kernel fragment acceptable (section 3)? |
| Erratum 1 `61c752b1` | `planning/cheri-enforcement-plan.md` | The soft limit raised to 2,000 lines, `mvp/src/` at 100, and CE-4's resumption, as the human chose | Text | None |
| CE-4 `9ab49914` | `mvp/guest/cheri/be-cheri-store.c` (new, `GPL-2.0-only`, Q11) and `Kbuild`, `mvp/guest/cheri/cheri-tests.c`, `mvp/guest/mvp-init.c`, `mvp/guest/cheri-ksyms.txt`, `mvp/guest/cheri-pins.txt`, `mvp/tools/build-guest-cheri.sh`, `mvp/tools/gen-dts.py`, `mvp/guest.mk`, `mvp/Makefile`, the checkers, generator, and harness | A guest kernel module's tagged capability store to te-poc's channel page: the `cap-store` image ends at the G-stage under Zcheripte (B3), and the same image's control run without it lands the tag (B4) | The guest kernel module is untrusted guest code; the monitor's G-stage decides; no `mvp/src/` change | Is a second expectation of one image the control you want (section 3)? |
| CE-5 `3998e34e` | `planning/cheri-platform.md`, `COPYING`, `planning/cheri-enforcement-plan.md` | The branch page's "What CHERI enforces on this branch" with section 8's words unchanged (Q12) and the last check's counts; its description, check, stall record, and r4 updated; `COPYING`'s second `GPL-2.0-only` module; the plan's status keys | Text | Do the page's words and counts say what you want, and nothing more? |

## 3. Claim boundary, departures, and residuals

**What the target supports saying.** Section 8's words, now on the branch
page: under emulation of CHERI v0.9.3 (CHERI Alliance QEMU at `008944fe`
with beryllium-cheri's two local changes, `cheri_pte` on), the
CHERI-aware monitor's G-stage leaves allow tagged capability stores to
each domain's own window and refuse them to every declared page; in the
branch's check a guest kernel's tagged store to te-poc's channel page
ended the run at the G-stage, and landed without that property; inside
each CHERI Linux guest of te-poc, a purecap process's out-of-bounds load
was delivered as `SIGSEGV`/`SEGV_CAPBOUNDSERR` and a `write(2)` through
the bounded capability returned `EFAULT`, while the run continued; the
guests' first PCC and `ddc` remain the whole address space.

**What stays trusted or assumed.** The G-stage capability-write check is
this emulator's behaviour: the RISC-V CHERI specification leaves the
field reserved in G-stage entries, so the control may change or vanish in
another emulator (plan, section 10). The CHERI toolchain, emulator, and
the SDK's purecap OpenSBI come from beryllium-cheri at `316ad8c` and are
not in Beryllium's tool lock; the firmware's SHA-256 is recorded
(`e0aeeae9…`), not pinned. CHERI Alliance Linux and its musl and BusyBox
are pinned by `mvp/guest/cheri-pins.txt`.

**Not run.** No CHERI hardware exists here; every result is emulation for
one emulator and one guest, not evidence for the MVP's claim. The plain
variant's `claim-ledger-check` fails as before (section 6). `./mvp/mvp
evaluate` and `./mvp/mvp verify` are not run on the branch.

**Not implemented (the plan's decisions).** The monitor's own accesses
to guest memory through window-bounded capabilities (D) are deferred
(Q5); a bounded first PCC or `ddc` does not suit CHERI Linux guests
(section 3.2, r4); `henvcfg.CRE` stays set for the plain Linux guests
under the CHERI-aware monitor (Q8).

**Departures from the plan's letter**, each reviewed by the owner session
and each judged not to need a plan revision:

- CE-2: the environment variable's name, `BE_MVP_QEMU_CHERI_CPU`, and the
  root line's placeholders, `<capaddr>` and `<capword>`, were left to the
  implementation; `channel-cw` also runs in part 3, which reuses part 1's
  list; the capture mutations judge each run's own passing capture, the
  CHERI flavour having no committed fixtures; the gstage host test's
  CHERI scenario count (46) beside the assertion count the plan named;
  two B2 mutations beyond its list.
- CE-3: `CONFIG_COREDUMP=y` joins Q2's `CONFIG_PROC_FS` and
  `CONFIG_PROC_SYSCTL` in the CHERI kernel fragment, because CHERI
  Alliance Linux at its pin does not build `fs/proc/base.c` without it
  (`/proc/PID/auxv` reads a field declared only under that option); the
  init's core-size limit is 0, so no core is written. The bounded
  capability is at a fixed anonymous page, so every C1 value is checked
  exactly; `cheri-fault-hs` links its own `mvp-trap.o` as a toolchain of
  its own; C3's DETAIL also fixes `htval=0x0 htinst=0x0`; four C3
  mutations beyond its list; the guest kernel's CHERI exception report is
  rejected in every CHERI guest scenario, not only te-poc's.
- CE-4: `param_ops_ulong` joins `memremap` and `memunmap` in the kept
  exports, since the module's `gpa` parameter needs it; the control is a
  second expectation, `cap-store-control`, of `cap-store`'s image, run
  without the CPU property; CE-3's `last_line` is generalised to
  `last_lines`; the build checks the two modules' imports together
  against the list; B3's `tval` and `vsatp` mutations, B4's
  `PTE.CW support: yes`, and the image check's one are beyond the
  lists; its kernel fragment change is a comment, which its message does
  not name.
- CE-5: `COPYING` names the branch's second `GPL-2.0-only` module beside
  `be-mgmt.c`, which Q11 makes necessary, though CE-5's text list does
  not name `COPYING`. Its 8 lines count under section 7's rule.

**Residuals.** The CHERI rules' review's r1 to r3 stand as the page
records; r4 is now seen in every run (the root capability line). The
CHERI emulator's wake-up stall stopped one session in this work (section
5); beryllium-cheri holds it for its owner to report. M8's frozen record
names `mvp/src/mvp-sbi.c` and `mvp.h`, which this branch changes. When
the release's fixes reach `main` and then this branch, F1's firmware pin
will need a CHERI counterpart. The human's P-15 (a) change after MVP 1.0
(the kernel-facing files to `GPL-2.0-only`) should include this branch's
`mvp/guest/cheri/Kbuild`. `main`'s accepted `/proc` change (item 130)
comes in at the next catch-up merge; CE-3 mounts `proc` itself.

## 4. Security and correctness invariants

| Property | Contract | Implementation | Evidence |
| --- | --- | --- | --- |
| The plain variant is the development line's MVP, byte for byte | The branch page, "Checking it", part 2 | The variant split; every CHERI change under `BE_MVP_CHERI`, `__CHERI_PURE_CAPABILITY__`, or a CHERI-only file | `cheri-check.sh` part 2: 162 boot images equal `main`'s reference `c7be2498` and release candidate 4's record |
| Window leaves carry CW; declared pages' leaves do not; the walker refuses CW elsewhere | The plan, section 3.3 and CE-2 | `mvp/src/mvp-gstage.c`'s CHERI blocks | The gstage host test's CHERI scenarios; B2 (`channel-cw` refused at boot); B1 |
| A guest kernel's tagged store into a declared page ends the run at the G-stage, and lands without Zcheripte | Section 6, B3 and B4 | CE-2's leaves; CE-4's module and image | B3 and B4 for each toolchain, with their mutations |
| The guests' own CHERI faults reach the guest, and only delegation lets the run continue | Section 6, C1 to C3 | `hedeleg` bit 28; CE-3's tests | C1 and C2 in te-poc's runs; C3 (`cheri-fault-hs` terminal) |
| Each new rule judges values, not mere presence | Section 6, "Mutations it must reject" | `tests/check-capture.py --cheri-mutations`; `tests/check-image.py` | 94 of 94 mutations rejected in part 1, 10 of 10 in part 3; the image check's 153, 157, and 166 |
| The soft limit | Section 7, Q10, erratum 1 | `git diff --numstat 89ab3ac3 3998e34e`, Markdown excluded | 1,715 of 2,000 lines; 38 of 100 in `mvp/src/` |

## 5. Review history and resolved findings

The owner session reviewed each code commit line by line before the next
began, against the plan's sections 5 to 7, and ran or read its checks:

- **CE-2 `20af3dac`:** accepted as is. The `mvp/src` change is minimal
  and gated; `BE_MVP_QEMU_CHERI_CPU` is a whole-string anchored allowlist
  in both harnesses and refused for the plain monitor; the plain
  variant's 162 images equal the reference.
- **CE-3 `15e25343`:** accepted as is, `CONFIG_COREDUMP=y` recorded as a
  departure (section 3). The `mvp-init.c` hook changed nothing in the
  plain build's outputs (the plain guest pins and part 2).
- **CE-4 `9ab49914`:** accepted as is. Checked in particular: the init
  loads the module before `make_pattern()` and `write_channel()`, and
  only as `/init-cap-store`; the module's three steps and its licence;
  the build wiring gated to the CHERI monitor with the CHERI guest; the
  generator's B3 last lines, which make "no module line after the store"
  a rule; the twelve mutations; `run-qemu.sh`'s one caller of `boot()`;
  and the captures themselves, whose B3 DETAIL reads `cause=0x17
  tval=0xffffffc600007080 htval=0x21000020 htinst=0x0 spvp=1`.
- **The CHERI emulator's wake-up stall:** CE-4's first `cheri-check` run
  failed in part 3 on the Clang `two-guests` shell session, whose first
  domain fell silent 0.0586 s into its boot while the second reached its
  shell, the defect the branch page describes. Part 3's images and
  expectations do not change in CE-4; the check ran again unchanged and
  passed. Nothing was relaxed.
- **CE-5's own count:** the first CE-5 commit, `e4e985c4`, gave 1,707
  lines, CE-2 to CE-4's code alone; section 7's rule counts every
  non-Markdown line from the acceptance record to the result commit, so
  `COPYING`'s 8 count, and the corrected `3998e34e` says 1,715.
  `e4e985c4` is superseded; no gate completed on it.

## 6. Validation and retained evidence

**At the exact result commit `3998e34e`** (2026-11-08, 07:05 to 07:32
UTC, in the CHERI clone, its tree clean before and after; logs under its
`build/ce5/`):

- `mvp/tools/cheri-check.sh`: `BE_MVP_CHERI_CHECK: PASS` on its first run,
  `time: cheri 504 s, plain 29 s, regression 394 s, total 927 s`:
  - part 1: all 20 make invocations, the image check's 153, 157, and 166
    mutations with each toolchain, `BE_MVP_QEMU: PASS runs=56 attempts=67
    refused=11`, `BE_MVP_CHERI_CAPTURE_MUTATIONS: PASS runs=14
    mutations=94 rejected=94`, and `BE_MVP_SESSIONS: PASS sessions=6
    attempts=8 refused=2`;
  - part 2: `BE_MVP_CHERI_PLAIN: PASS images=162 (be-mvp-boot-pic.img=52
    be-mvp-boot-qemu.img=6 be-mvp-boot.img=54 be-mvp.bin=50)
    reference=c7be2498f2e0 records=20261105-rc4:162`;
  - part 3: the image check's 153, 157, and 166, `BE_MVP_QEMU: PASS
    runs=50 attempts=62 refused=12`, `BE_MVP_CHERI_CAPTURE_MUTATIONS: PASS
    runs=2 mutations=10 rejected=10`, and `BE_MVP_SESSIONS: PASS
    sessions=6 attempts=9 refused=3`.
- `make -C mvp check`, the plain variant with the tool lock's tools:
  every step passed up to its last, `claim-ledger-check`, among them
  `BE_MVP_QEMU: PASS runs=64 attempts=87 refused=23`, `BE_MVP_SESSIONS:
  PASS sessions=6 attempts=7 refused=1`, `BE_MVP_EVIDENCE: PASS`
  (`files=561 images=341`), and `BE_MVP_LICENSES: PASS identifiers=6
  files=1071`, which reads the new `COPYING`. `claim-ledger-check` failed
  as at CE-2 to CE-4: its self-test (`mutations=30 variants=7`, its output
  CE-4's but for one scratch commit's ID), and `claim-ledger.py check`'s
  evidence check, with the same 11 SHA-256 findings over the same seven
  files (`mvp/src/mvp-runtime.c`, `mvp/tests/check-capture.py`,
  `mvp/tests/check-image.py`, `mvp/tests/sbi-test.c`,
  `mvp/tests/session-typist.py`, `mvp/tools/gen-scenario.py`, and
  `mvp/tools/port.py`); its other nine checks pass.
- `git diff --check`: clean. The planning site's documentation source
  check: PASS.

**Earlier, per work package** (the sub-agent's runs, read by the owner
session; logs under the CHERI clone's `build/ce2/`, `build/ce3/`, and
`build/ce4/`):

| Commit | `cheri-check.sh` | Part 1 | Part 3 | Plain `make -C mvp check` |
| --- | --- | --- | --- | --- |
| CE-2 `20af3dac` | PASS, 1,064 s | `runs=50 attempts=55 refused=5`; 34 of 34 mutations | `runs=50 attempts=59 refused=9`; 10 of 10 | Every step but `claim-ledger-check` |
| CE-3 `15e25343` | PASS, 975 s | `runs=52 attempts=61 refused=9`; 70 of 70 | `runs=50 attempts=58 refused=8`; 10 of 10 | The same |
| CE-4 `9ab49914` | PASS on its second run, 916 s | `runs=56 attempts=62 refused=6`; 94 of 94 | `runs=50 attempts=62 refused=12`; 10 of 10 | The same |

Part 2 passed in each: 162 images equal to `main`'s reference
`c7be2498` and release candidate 4's record.

## 7. Recommended review sequence

From the canonical checkout's root, read-only (the work branch is
imported there):

1. This packet, then the branch page's new section and r4:

   ```sh
   git show beryllium/cheri-enforcement:planning/cheri-enforcement-result-review-summary.md | glow -p
   git show beryllium/cheri-enforcement:planning/cheri-platform.md | glow -p
   ```

2. The commits, and the monitor's whole change:

   ```sh
   git --no-pager log --stat --format='%h %s' 89ab3ac3..beryllium/cheri-enforcement
   git --no-pager diff 89ab3ac3 3998e34e -- mvp/src/
   ```

3. The guest side of the store, and its expectations:

   ```sh
   git --no-pager show 9ab49914 -- mvp/guest/cheri/be-cheri-store.c mvp/guest/cheri/cheri-tests.c mvp/guest/mvp-init.c
   git --no-pager show 9ab49914 -- mvp/tools/gen-scenario.py
   ```

## 8. Human decision checklist

- [ ] The work stays within the accepted plan and erratum 1.
- [ ] The page's words are section 8's, and its counts match the check.
- [ ] Relying on the emulator's G-stage behaviour is acceptable for the
      branch.
- [ ] The departures of section 3 are acceptable.
- [ ] The negative tests (B2 to B4, C3) and the mutations judge values.
- [ ] Pushing, publication, and any merge into `main` stay excluded.
- [ ] `3998e34e` is accepted, revisions are requested, or review is
      deferred.

## 9. After the decision

**Accept.** Reply `accept 3998e34e`. The owner session then records the
acceptance on the work branch and fast-forwards `beryllium/cheri-platform`
to it (Q9), locally. Pushing `beryllium/cheri-platform` to the private
`origin` needs its own instruction; `accept 3998e34e, merge and push`
gives both.

**Request revisions.** The owner session makes new commits on
`beryllium/cheri-enforcement` and a new packet; `3998e34e` is not treated
as accepted.

**Defer.** The work branch stays as it is, unmerged; nothing on
`beryllium/cheri-platform` changes.

**Status:** the CHERI enforcement plan's CE-2 to CE-5, checked at the
exact result commit; not accepted. **Next:** your decision on
`3998e34e`. **Action required from you:** read sections 3 and 5 and the
branch page's new section, then reply `accept 3998e34e`, or ask for
revisions. The MVP 1.0 release path's step 5 is independent of this
decision.
