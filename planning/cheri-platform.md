<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The CHERI platform branch

> **On the public research branch `cheri-platform`.** This page is the
> internal branch's page, `beryllium/cheri-platform` at its last
> internal commit; the commits that it names are internal and do not
> resolve in this repository. The public branch holds that branch's
> change over MVP 1.0, the tag `mvp-1.0`, with these differences:
>
> - The branch's base holds the fixes made before MVP 1.0's release,
>   among them S-01's digest pin on QEMU's firmware. The CHERI-aware
>   monitor's firmware, the CHERI Alliance OpenSBI, is pinned the same
>   way, by the `firmware` line of `mvp/guest/cheri-pins.txt`.
> - The branch has no catch-up merge. Part 2 of
>   `mvp/tools/cheri-check.sh` builds its reference at the branch's
>   merge base with `main`, and compares the plain variant's boot images
>   with the release's record, `mvp/results/20261108-release/`.
> - Part 1 of `cheri-check.sh` runs 19 of `make check`'s steps here, not
>   20: the release removed `snapshot-check`.
> - The other planning pages are the release's, as they stood at the
>   release's source commit.
> - The CHERI research repository, beryllium-cheri, has joined this
>   branch under `cheri/` (see `cheri/README.md`): the CHERI stack's
>   pins, `cheri/pins.txt`; the tools that fetch and build the stack,
>   `cheri/tools/`; the CHERI QEMU's two local changes,
>   `cheri/patches/`; and its experiments, as records.
>   `cheri-check.sh` and `cheri-live.sh` read the pins from
>   `cheri/pins.txt`, and the stack from `build/cheri/` or from the
>   stack root given as `CHERI_DIR`, which may still be a
>   beryllium-cheri checkout. Where this page says that the CHERI inputs
>   or beryllium-cheri's scripts come from `../beryllium-cheri`, read
>   these places instead.

## Status and scope

The responsible human's direction of 2026-11-05: "for now, we will create
a long-lived branch in beryllium for the CHERI platform, to be developed
and maintained in parallel with the main Be workstream". This branch,
`beryllium/cheri-platform`, is that branch, and this page exists only on
it.

It changes nothing on the development branch, `main`. That line's plans,
claim (`mvp/docs/claim.md`), gates, tool lock, and accepted bytes stay as
they are. There, CHERI stays the MVP 3.0 research track (`mvp-plan.md`,
Plan revision S3-C), and Type Enforcement stays the policy specification.
What this branch shows is on CHERI v0.9.3 under emulation, and none of it
is evidence for the MVP's claim.

Development moved from `beryllium/single-hart-runtime-r0` to `main` on
2026-11-05, at `f3f4ad62f52ec7e891c6fbd9a8d23f02cf5f2292`.
`beryllium/single-hart-runtime-r0` is frozen there and never moves again.
`main` is also the private repository's default branch on GitHub. "The
development branch" on this page means `main`.

## Creation and first catch-up

The branch was created on 2026-11-05 from the package maintained by the
sibling beryllium-cheri repository at exact commit
`528f31218c60968ab9f3af2fa1b0f40a421580eb`. The package used exact
Beryllium base `d776f3240e938eb96c6ee789e589a0f6c93a1dbb`; applying its
seven ordered patches produced frozen tree
`1ff9e0cd350f47568807057eddf6beb7fe487eb2`.

Before catch-up, `mvp/tools/cheri-check.sh` passed with 48 QEMU runs and
six shell sessions, the documentation source check passed, the
claim-phrasing scan found no issue, and `git diff --check` passed. Merge
commit `0496d7eeb5b61a3df5cc1882edfc490bb020c40f` then brought in exact
accepted M10 acceptance record
`9d06b0245c39a34a0b2c8cbd45d40db07cdebb68`.

On the caught-up tree, the same CHERI check passed again with 48 QEMU
runs and six shell sessions. The documentation source check, the
claim-phrasing scan, and `git diff --check` also passed before this
record was committed. The responsible human's instruction to create
this branch and push it to the private `origin` authorizes that one
initial branch push.

This record does not move the development branch, add CHERI evidence to
the accepted MVP claim, select CHERI for the development line, or
authorize a public release. Later catch-ups enter by merge, never by
rebasing, and each later private-origin push needs its own instruction.

## Second catch-up: `main` through `9dcea2dd`

The first catch-up merged accepted M10 from
`beryllium/single-hart-runtime-r0`. After it, development moved to
`main`, which added two commits over the M10 acceptance record
`9d06b024`:

- `f3f4ad62f52ec7e891c6fbd9a8d23f02cf5f2292`, which cut development over
  to `main` and synced the roadmap;
- `9dcea2ddb4109db7827313616c5593215c3a654c`, which records the default
  branch and the snapshot decision.

Both change documentation only (`planning/` and `.github/`). Merge
commit `f3d134d1ce8dcfde20bdda67baf516897d7c2013` brought them in on
2026-11-05, without conflict. The merge changed no file under `mvp/`,
`model/`, `tests/`, or `scripts/`.

On the merged tree, with no uncommitted change, `mvp/tools/cheri-check.sh`
passed against beryllium-cheri at
`f7a1f76628064229b57b97dc031f8cdd0df2a2e7`:

- the emulator `QEMU emulator version 8.1.0, build/qemu-ia-fix`, and the
  firmware with SHA-256
  `e0aeeae9ac48ed52ec95188dd7cb9a415be266f182c70acb63b8a3c91d628c7d`;
- all 20 make invocations: among them the image check, which rejected
  all of its 127 (two-guests), 131 (te-poc), and 140 (anchor) mutations
  with each toolchain, and all eleven host tests;
- `BE_MVP_QEMU: PASS runs=48 attempts=57 refused=9`;
- `BE_MVP_SESSIONS: PASS sessions=6 attempts=7 refused=1`;
- `BE_MVP_CHERI_CHECK: PASS`.

The guest's sources did not change, so the check reused its outputs, and
the image check compared them with their pins. The documentation source
check, the claim-phrasing scan, and `git diff --check` passed on this
record before it was committed.

## The variant split

On 2026-11-05 the responsible human directed the split that
beryllium-cheri's handoff proposes as this branch's first work: CHERI as
a variant of the RISC-V arch, not a separate arch, chosen by a build
switch. Two commits made it:

- `581caf9e95415b15bf47ec896c07533e337fcce5`, which makes the QEMU
  harness hand its build tree to the capture checker, so that each run
  is judged against the references of the tree it booted;
- `167f160dbb7a9c7382cf624dcc1f2ee52d14250f`, which makes the CHERI
  changes a monitor variant and a guest flavour.

The two switches and their values are in "What the branch carries",
below. The plain variant is the default because it is then the
development line's build. `./mvp/mvp`, which passes neither switch, the
evaluator, the tool lock, and every recursive make work as they do on
the development line. The CHERI inputs, which the tool lock does not
hold, are needed only when the CHERI variant is asked for, and
`mvp/tools/cheri-check.sh` asks for it explicitly.

What is per variant, and where:

- **The monitor's assembly.** In `mvp/src/mvp-trap.S`, the six routines
  that CHERI changes carry their CHERI code in `#ifdef BE_MVP_CHERI`
  blocks: the trap vector, the resume tail, the three arm helpers, and
  the injection helper. The vector and the resume tail save and restore
  the guest's registers through `MVP_SAVE_GPR` and `MVP_RESTORE_GPR`, as
  CHERI Alliance Linux's `entry.S` does through `CREG_S` and `CREG_L`.
  Without `BE_MVP_CHERI` the file assembles to the development line's
  instructions, and with it to the proof of concept's, with GCC and with
  Clang.
- **The arming values.** `mvp/src/mvp.h` sets three per variant:
  `BE_MVP_HEDELEG` (`0xb15d`, or `0x1000b15d`),
  `BE_MVP_HEDELEG_REQUIRED` (`0xb10c`, or `0x1000b10c`), and
  `BE_MVP_HENVCFG_ARMED` (STCE, or STCE and CRE). `mvp/src/mvp-runtime.c`
  holds a set of `_Static_assert`s for each variant. The rest of the C,
  the Type Enforcement decision code among it, is one text for both.
- **The guests.** `mvp/guest/pins.txt` and the three scenarios'
  `scenario.json` are the development line's files again. The CHERI
  Linux guests' pins moved, line for line, to `mvp/guest/cheri-pins.txt`.
  `mvp/guest.mk` builds each flavour with its own script, against its
  own pins. `mvp/tools/gen-dts.py` takes `--guest-flavour`, which adds
  Zcherihybrid and Zcheripurecap to the device trees.
  `mvp/tools/gen-scenario.py` takes it too, and derives the CHERI guests'
  kernel release lines (7.1.0) from `scenario.json`; its `--monitor` sets
  the armed `henvcfg` that `BE_MVP:09` reports. `mvp/guest/mvp-init.c`
  and `mvp/guest/mgmt/be-mgmt.c` keep their CHERI code under the CHERI
  compiler's and kernel's own macros (`__CHERI_PURE_CAPABILITY__`,
  `CONFIG_CHERI_PURECAP_UABI`), so the Linux flavour compiles the
  development line's code.
- **The port and the Make controls.** `mvp/tools/port.py --cheri` adds
  the SBI 3.0 rule. `mvp/tools/make-control.py` allows the two switches
  on make's command line.
- **The checkers.** Their rules stay apart from the code.
  `mvp/tests/check-image.py` takes `--monitor` and `--guest-flavour` and
  selects the CHERI rules and mutations before any check.
  `mvp/tests/check-capture.py` takes `--monitor`, which sets the
  `hedeleg` it expects. `mvp/tests/sbi-test.c` has expected values and
  WARL tables for each variant. In `mvp/Makefile`, `HOST_ASSERTIONS_sbi`
  is 16,292, or 16,294 for the CHERI-aware monitor.
- **The harness.** `mvp/tests/run-qemu.sh` and
  `mvp/tests/session-typist.py` read `BE_MVP_MONITOR`, which sets the
  firmware's SBI version and the checker's `--monitor`, and
  `BE_MVP_GUEST_PINS`. `mvp/tools.mk` refuses `qemu-test`, `sessions`,
  and `uboot-rehearsal` for `MVP_MONITOR=cheri`: their emulator and
  firmware are the tool lock's, and `cheri-check.sh` runs the same
  harness with the CHERI ones.

The CHERI-aware monitor's objects and host tests get `-DBE_MVP_CHERI`
through pattern-specific values on its own build tree. The global flags
in `mvp/Makefile` therefore stay the development line's, which
`mvp/verify/tools/digests.py` parses.

Every result below is for the split's commit, `167f160d`. The image
comparison and the CHERI check ran with no uncommitted change. The other
runs ran while this page was being edited, with no other change, so the
plain check's evidence bundle records `source_tree=dirty changed=1`.

- **The plain variant reproduces the development line's boot images
  byte for byte.** After `make -C mvp clean`, `make -C mvp image variants
  probes qemu-images` built 162 images: 50 `be-mvp.bin`, 54
  `be-mvp-boot.img`, 52 `be-mvp-boot-pic.img`, and 6
  `be-mvp-boot-qemu.img`, for every scenario, variant, and probe, with
  GCC and with Clang. Each is equal, by `cmp`, to its counterpart in a
  build of `main` at `9dcea2dd`, made in a separate clone with the same
  tools and invocation. Their SHA-256 digests are the 162 that release
  candidate 4's record lists
  (`mvp/results/20261105-rc4/host/images.sha256`). Neither build makes
  an image that the other lacks. The two probe stubs and the 23 guest
  outputs are equal too. The ELF files were not compared, since they
  carry debug data and the checkout's path.
- **The plain variant passes `make -C mvp check` up to its last step.**
  Every step before `claim-ledger-check` passed, among them:
  - `BE_MVP_GUEST_PINS: PASS files=23`;
  - `BE_MVP_REFERENCE: PASS guests=2`;
  - every host test, with `BE_MVP_HOST: PASS sbi scenarios=133
    assertions=16292`;
  - the image check's 122 (two-guests), 126 (te-poc), and 135 (anchor)
    mutations with each toolchain, as in release candidate 4's record;
  - `BE_MVP_CAPTURE_SELF_TEST: PASS cases=300 failed=0` and
    `BE_MVP_CAPTURE_MUTATIONS: PASS mutations=459 rejected=459`;
  - `BE_MVP_RUN_TOOL_DRY_RUN: PASS` and `BE_MVP_TOOLS_CHECK: PASS`;
  - `BE_MVP_QEMU: PASS runs=64 attempts=77 refused=13`;
  - `BE_MVP_SESSIONS: PASS sessions=6 attempts=6 refused=0`;
  - `BE_MVP_EVIDENCE: PASS`, with 524 files.

  `claim-ledger-check` then failed, as the table under "Checking it"
  says. Its evidence check found 11 SHA-256 mismatches, in the seven
  pinned files that the split changes, and its other checks passed. Its
  self-test failed with it, since each seeded mutation then also fails
  the evidence check. `make -C mvp kernel-repro` passed:
  `BE_MVP_KERNEL_REPRO: PASS outputs=23 identical`, with release
  candidate 4's sysroot and musl digests.
- **The CHERI variant passes `mvp/tools/cheri-check.sh`.** It ran from
  a fresh build tree, against beryllium-cheri at
  `f7a1f76628064229b57b97dc031f8cdd0df2a2e7`, with the emulator and
  firmware of the second catch-up:
  - `BE_MVP_GUEST_BUILD: PASS cheri pins=match`;
  - all 20 make invocations: among them the image check, which rejected
    all of its 127 (two-guests), 131 (te-poc), and 140 (anchor) mutations
    with each toolchain, and all eleven host tests, with
    `BE_MVP_HOST: PASS sbi scenarios=133 assertions=16294`;
  - `BE_MVP_QEMU: PASS runs=48 attempts=55 refused=7`;
  - `BE_MVP_SESSIONS: PASS sessions=6 attempts=6 refused=0`;
  - `BE_MVP_CHERI_CHECK: PASS`.

  Its 162 boot images and 23 guest outputs are equal to those of an
  earlier build of the same sources.
- **The CHERI variant's code is the proof of concept's.** Each of its
  162 boot images differs from the same image in a build of `49f812fc`,
  from before the split, made in a separate clone, only in one run of 32
  bytes: the scenario's SHA-256, which the monitor's measurement log
  carries. `scenario.json` is now the development line's.
- **The CHERI-aware monitor also runs the Linux guests.** As a further
  regression check, not part of the split's acceptance,
  `MVP_MONITOR=cheri` with the default `linux` guests was built in
  `build/mvp.cheri.linux` and run on the CHERI emulator and firmware with
  the CHERI check's runs and sessions. Its guest outputs matched
  `mvp/guest/pins.txt`, the image check rejected its 127, 131, and 140
  mutations with each toolchain, and `BE_MVP_QEMU: PASS runs=48
  attempts=55 refused=7` and `BE_MVP_SESSIONS: PASS sessions=6
  attempts=7 refused=1`.

These results are properties of this branch's build. They add nothing to
the MVP's claim, whose evidence stays the development line's records.

## Third catch-up: `main` through `c7be2498`

After the variant split, `main` moved from `9dcea2dd` to
`c7be2498f2e0edf6affa4ac4fdb9ef1cd42e0a5a`. Its six new commits record
the two parallel lanes, the release path's step 2 proposal (`38fa3a08`),
its review packet, and its acceptance record. All change documentation
only (`planning/` and `.github/`). Merge commit
`d14a8b0eb6f8fbe32367cbffb13724b7e406febc` brought them in on
2026-11-06, without conflict.

On the merged tree, with no uncommitted change, `mvp/tools/cheri-check.sh`
passed against beryllium-cheri at
`316ad8c48de39e97084d0bfaaf023ed61c88e1c8`, whose commits since
`f7a1f76` change only its `COLLAB.md` and `HANDOFF.md`:

- all 20 make invocations: among them the image check, which rejected
  all of its 127 (two-guests), 131 (te-poc), and 140 (anchor) mutations
  with each toolchain, and all eleven host tests;
- `BE_MVP_QEMU: PASS runs=48 attempts=61 refused=13`;
- `BE_MVP_SESSIONS: PASS sessions=6 attempts=10 refused=4`;
- `BE_MVP_CHERI_CHECK: PASS`.

The documentation source check, the claim-phrasing scan, and
`git diff --check` passed on this record before it was committed.

## What the branch carries

The branch is Beryllium's MVP with CHERI as a build variant of the
RISC-V monitor, not a separate architecture. It starts from the proof of
concept in the sibling research repository `../beryllium-cheri`
(`experiments/be-cheri-poc.md` there), whose five commits are the
branch's first five, applied unchanged. The variant split (above) then
made the proof of concept's changes a variant.

Two caller variables of `mvp/Makefile` select what is built:

| Switch | Values | Default |
| --- | --- | --- |
| `MVP_MONITOR` | `riscv`, the RISC-V monitor; `cheri`, the CHERI-aware monitor for CHERI v0.9.3 | `riscv` |
| `MVP_GUEST_FLAVOUR` | `linux`, the development line's Linux guests; `cheri-linux`, the CHERI Linux guests | `linux` |

- **The plain variant**, with both defaults, is the development line's
  MVP. It builds in `build/mvp`, and its boot images are the development
  line's, byte for byte, as part 2 of the branch's check compares on
  every run (see "Checking it").
- **The CHERI variant**, `MVP_MONITOR=cheri MVP_GUEST_FLAVOUR=cheri-linux`,
  builds in `build/mvp.cheri.cheri-linux`.
  - **The monitor is CHERI-aware.**
    - `henvcfg.CRE` is set for the guests.
    - The trap vector enters Capability Pointer Mode before any access.
      It saves and restores every guest register whole, as a capability,
      and switches `ddc` on every trap.
    - `hedeleg` delegates cause 28, CHERI v0.9.3's CHERI fault, and
      arming refuses a hart that cannot delegate it.
    - The device tree is passed to the guest as a capability.
    - The injection helper moves `sepcc` and `vstvecc` whole.
    - One port rule accepts firmware that reports SBI 3.0.
    - The G-stage's leaves for each domain's window carry the
      capability-write bit; no declared page's leaf carries it, and the
      walker refuses it there (the enforcement plan's CE-2).
  - **The guests are CHERI Linux.** `mvp/tools/build-guest-cheri.sh`
    builds them, and `mvp/guest/cheri-pins.txt` pins them:
    - CHERI Alliance Linux v7.1 with the purecap user ABI;
    - a purecap init against CHERI Alliance musl;
    - CHERI Alliance BusyBox;
    - the management module;
    - in te-poc's roles, the init's own CHERI faults (CE-3), and, in the
      initramfs alone, the capability-store module,
      `mvp/guest/cheri/be-cheri-store.c`, which te-poc's `cap-store`
      image loads (CE-4).
- `MVP_MONITOR=cheri` with the default `linux` guests builds in
  `build/mvp.cheri.linux`. The pair `riscv` and `cheri-linux` is refused:
  a CHERI guest runs only under the CHERI-aware monitor.
- **Beryllium's checkers judge each variant by its own rules.** The CHERI
  rules in `mvp/tests/check-image.py`, `mvp/tests/check-capture.py`, and
  `mvp/tests/sbi-test.c` apply only to the CHERI-aware monitor. The owner
  session reviewed those of the first two on 2026-11-06 (see "The CHERI
  rules' review").

Most changes from the development line carry a `beryllium-cheri:`
comment, so that a merge can find them; new changes should carry one
too, where the file allows a comment. The complete list is
`git diff main...beryllium/cheri-platform`.

## Checking it

The branch's check is `mvp/tools/cheri-check.sh [CHERI_DIR]`, and
`mvp/tools/cheri-check.sh --help` prints its description. It runs in
three parts and passes only when all three pass, in about 15 minutes on
the development workstation. When a catch-up has brought a new `main`
commit, the first run also builds that commit's reference, in about 80
seconds more. Its CHERI inputs are not in Beryllium's tool lock. They
come from `CHERI_DIR`, a beryllium-cheri checkout (by default the sibling
`../beryllium-cheri`), which is only read:

- the CHERI Alliance SDK and the pinned CHERI sources;
- the CHERI QEMU with two local changes (its
  `experiments/build-qemu-vs-reset.sh --ia-fix`);
- the SDK's purecap OpenSBI.

1. **The CHERI variant.** It builds `MVP_MONITOR=cheri
   MVP_GUEST_FLAVOUR=cheri-linux` in `build/mvp.cheri.cheri-linux` and
   requires:
   - the CHERI guests' build to match `mvp/guest/cheri-pins.txt`;
   - every check of `make check` that is not in the table below to pass
     (20 make invocations, among them the image check and every host
     test);
   - `tests/run-qemu.sh`'s 56 runs to pass: two-guests, te-poc, and
     anchor, the ten monitor variants, the four probes, te-poc's five
     negatives (`reader-write`, `no-inject`, and the enforcement plan's
     `channel-cw`, `cheri-fault-hs`, and `cap-store`) and anchor's five,
     and `cap-store`'s control, for GCC and Clang;
   - the CHERI rules' mutations of each passing capture to be rejected
     (`tests/check-capture.py --cheri-mutations`), each for its own
     reason;
   - `tests/session-typist.py`'s six shell sessions, M7's, to pass.
2. **The plain variant's identity with `main`.** It cleans the images in
   `build/mvp` and rebuilds them with the defaults, `make -C mvp image
   variants probes qemu-images`. Every `be-mvp.bin`, `be-mvp-boot.img`,
   `be-mvp-boot-pic.img`, and `be-mvp-boot-qemu.img` under `gcc/`,
   `clang/`, `variants/`, and `probes/`, 162 today, must equal the
   reference's, byte for byte, with no image missing and none extra. The
   ELF files are not compared, since they carry debug data and the
   checkout's path.
   - **The reference** is a build of the latest `main` commit merged into
     the branch: the second parent of the newest merge on `HEAD`'s
     first-parent history. That commit must also be the merge base of
     `HEAD` and `main` (`origin/main` where there is no `main`), so the
     check fails if the newest merge brought in anything but the
     development line.
   - It is built with the same tools and invocation, in a temporary clone
     under `build/cheri-check/reference/<commit>/`, which then keeps only
     the digests and the build log. Later runs reuse the digests, so the
     reference is built again only when a catch-up brings a new `main`
     commit.
   - **The release-candidate records** add a cross-check while they
     apply. A record applies when its candidate commit has the
     reference's build inputs (every path but `planning/`, `.github/`,
     `mvp/results/`, `mvp/docs/`, and Markdown files is equal) and the
     record says it was made from that commit's clean tree. The reference
     must then equal the record's `host/images.sha256` too. Today that is
     release candidate 4's record, `mvp/results/20261105-rc4/`.
3. **The CHERI-aware monitor with the Linux guests.** It builds
   `MVP_MONITOR=cheri MVP_GUEST_FLAVOUR=linux` in `build/mvp.cheri.linux`
   and runs its image check. Then it runs part 1's runs but
   `cheri-fault-hs`, `cap-store`, and its control, 50, and six sessions
   on the CHERI emulator and firmware, judged against
   `mvp/guest/pins.txt`. This regression check does not depend on CHERI
   Linux.

Every run uses QEMU's `plic` machine (`BE_MVP_QEMU_K3_LIKE=plic`) and
`BE_MVP_MONITOR=cheri`. Every run and session of parts 1 and 3 but
`cap-store`'s control also turns on the emulator's Zcheripte, the
capability-write check of its page-table entries
(`BE_MVP_QEMU_CHERI_CPU=cheri_pte=on`; the enforcement plan's CE-2 and
Q7); the control runs `cap-store`'s image without it. Part 1's runs also
set `BE_MVP_GUEST_PINS` to `mvp/guest/cheri-pins.txt`. The script writes
its logs and `summary.txt` to `build/cheri-check/`, which each run
empties but for the reference
digests.

**The CHERI emulator's wake-up stall.** beryllium-cheri records a defect
of the CHERI QEMU, for its owner to report: now and then a guest halted
in `wfi` stays halted although its timer interrupt is pending and
enabled (its `HANDOFF.md` and `experiments/monitor-run.md`). A guest that
sleeps then never wakes. In a run it shows as one domain falling silent
in the middle of its work: the run is killed at its 300-second limit, or,
in anchor, the host's requests time out because the protected domain
never answers. Parts 1 and 3 can meet it. On 2026-11-06 it stopped two
runs of one check: gcc's anchor run in part 1 and gcc's `hostile` run in
part 3. These were the only two among the 648 runs and sessions that the
branch's checks had completed when this paragraph was written, refused
boots not counted, and the check's next run passed. The three full checks
since, at `82a24819` and on the trees of `369e79f0` and `d4d4f5e0`,
completed 324 more without it. On 2026-11-08 it stopped one more, the
Clang `two-guests` shell session in part 3 of the first check at
`9ab49914`, whose first domain fell silent 0.0586 s into its boot
while the second reached its shell; the check's next run passed. The check
relaxes no expectation for it: read the failed run's capture, and when it
shows that stall, run the check again.

The check passed on 2026-11-08 on a clean tree at `9ab49914`, the
enforcement plan's CE-4, in its second run (the first met the stall
above):

- part 1: all 20 make invocations, the image check's 153, 157, and 166
  mutations with each toolchain, `BE_MVP_QEMU: PASS runs=56 attempts=62
  refused=6`, `BE_MVP_CHERI_CAPTURE_MUTATIONS: PASS runs=14 mutations=94
  rejected=94`, and `BE_MVP_SESSIONS: PASS sessions=6 attempts=9
  refused=3`;
- part 2: `BE_MVP_CHERI_PLAIN: PASS images=162 (be-mvp-boot-pic.img=52
  be-mvp-boot-qemu.img=6 be-mvp-boot.img=54 be-mvp.bin=50)
  reference=c7be2498f2e0 records=20261105-rc4:162`, with the
  reference's digests reused from an earlier run;
- part 3: the image check's 153, 157, and 166 mutations with each
  toolchain, `BE_MVP_QEMU: PASS runs=50 attempts=62 refused=12`,
  `BE_MVP_CHERI_CAPTURE_MUTATIONS: PASS runs=2 mutations=10
  rejected=10`, and `BE_MVP_SESSIONS: PASS sessions=6 attempts=6
  refused=0`;
- `time: cheri 499 s, plain 30 s, regression 387 s, total 916 s` and
  `BE_MVP_CHERI_CHECK: PASS`.

The check before the enforcement work passed on 2026-11-06 at
`d99f62be`, with 48 runs in parts 1 and 3.

`make -C mvp check`, or `./mvp/mvp check`, which passes neither switch,
checks the plain variant as the development line is checked, with the
tool lock's tools. It passes every step but the last,
`claim-ledger-check` (see the table below).

The steps of `make check` that part 1 does not run, and the other
checks, for each variant:

| Check | Plain variant | CHERI variant |
| --- | --- | --- |
| Byte identity with `main`'s boot images | Part 2 of `cheri-check.sh`, on every run | Not applicable |
| `guest-pin-check` | Passes | Not run: its facts describe the Linux guests: an `rv64imac` attribute, their GCC, and M7's 3 MiB Image budget, which the CHERI kernel exceeds by 118,784 bytes |
| `capture-check` | Passes | Not run: 96 of its 300 self-test cases fail, since their fixtures are captures from the Linux guests |
| `run-tool-check` | Passes | Not run: the board tools' dry run starts from those fixtures |
| `reference-boot`, `kernel-repro` | Pass | Not run: they boot and rebuild the Linux guests, with the tool lock's tools |
| `qemu-test`, `sessions` | Pass | Refused by `mvp/tools.mk`: parts 1 and 3 of `cheri-check.sh` run the same harness with the CHERI emulator and firmware |
| `evidence` | Passes | Not run: it bundles every check's records |
| `claim-ledger-check` | Fails: the ledger pins, by SHA-256, seven files that the split changes; its claims are the development line's | Not run, for the same reason |
| The `k3-like`, `rva23`, and `no-sstc` machines | Run in `qemu-test` | QEMU 8.1 lacks the CPU properties they need, so `k3-like`'s variants and probes run on `plic` |
| `uboot-rehearsal` | Not run here: it needs B3's U-Boot build | Refused by `mvp/tools.mk` |
| `live` | Prints the plain commands (see "Running it by hand") | Refused by `mvp/tools.mk`: `mvp/tools/cheri-live.sh` prints and runs the CHERI commands |
| `./mvp/mvp evaluate`, `./mvp/mvp verify` | Not run: each takes hours | Not run |

M8's frozen record (`mvp/verify/target-digests.txt`) names
`mvp/src/mvp-sbi.c` and `mvp/src/mvp.h`, and this branch changes both:
the plain variant's boot images are the development line's, byte for
byte, but the text of these two files is not. M8's results therefore
describe the development line's files, not this branch's.

## The CHERI rules' review

On 2026-11-06 the owner session read every CHERI rule of
`mvp/tests/check-image.py` and `mvp/tests/check-capture.py`, as at
`3f1ccc1e`, against `mvp/src/mvp-trap.S`'s CHERI code: the trap vector,
the resume tail, the injection helper, and the arm and budget helpers.
The rules held on that code. The review's six findings, F1 to F6, named
defects that the rules would let through, and two commits fix them:
`7e18b68b` (F6), then `369e79f0` (F1 to F5). A third, `d4d4f5e0`, fixes
r5, a gap found while F4's mutation was written, on the owner session's
decision of 2026-11-06 (T5). They change only CHERI rules, each marked
`beryllium-cheri:`. The plain variant's rules and mutations are the
development line's, and stay as they are.

- **F1, the vector's `ddc` switch.** The rules accepted the four words
  reordered, with the monitor's `ddc` installed before the guest's is
  saved. Every trap would then save the monitor's `ddc` as the guest's,
  and the resume tail would hand it to the guest. Now the vector holds
  exactly one `ddc` read and one `ddc` write. The read is at once
  followed by the store of its register in slot 0, and the write is at
  once preceded by the load of its register from the monitor's slot,
  `CF_MON_DDC`. The read comes first, and both come before Integer
  Pointer Mode.
- **F2, slots 2, 5, and 6, and `sscratchc`.** The rules accepted those
  slots stored from any register, and did not require `sscratchc` to be
  restored. Now `ct0` and `ct1` are each loaded whole from their spill
  below the trusted top (`-32`, `-16`) and at once stored in their slot
  (5, 6), and `csp` is read whole from `sscratchc` and at once stored in
  slot 2. After that, and before Integer Pointer Mode, `csrrw zero,
  sscratch, sp` makes `sscratchc` the trusted top again, whole. It is
  the vector's one write of `sscratch` besides the exchange, its second
  word.
- **F3, the injection helper's mode.** The rules checked the capability
  moves' data flow but not their mode, so either mode switch could be
  removed. Now exactly the four moves lie between the helper's one
  `MODESW.CAP` and its one `MODESW.INT`: `sepcc` to `vsepcc`, then
  `vstvecc` to `sepcc`, each through one register. The integer writes
  of `vsepc` and `vsstatus`, from `a2` and `a3`, and the four readbacks
  follow the `MODESW.INT`. The arm and budget helpers must also enter
  Capability Pointer Mode once and then leave it once. The review did
  not ask for that part, which was added with F3 because the same
  removal passed there.
- **F4, the scans of the `sscratchc` rule.** The base of the SCADDR that
  makes `sscratchc` could come from any earlier `ddc` read. Now the
  nearest earlier write of that register must be the `ddc` read. The
  arm, budget, and injection helpers must hold no compressed
  instruction, as the vector and the resume tail must not, since these
  rules scan 32-bit words.
- **F5, the capability frame's clear.** Nothing checked the arm helper's
  33 stores of a null capability. Now each slot of the frame, at
  `CF + 16k` for k from 0 to 32 through `a1`, is stored from `x0` once,
  before Capability Pointer Mode and before the helper's three stores
  through `t1`.
- **F6, the console line's length.** `check-capture.py` held a copy of
  `BE_MVP_CONSOLE_LINE_BYTES`. It now reads the value from
  `mvp/src/mvp.h`, as it reads `mvp-layout.h`, and stops when the header
  holds no literal definition of it, or two.
- **r5 (T5), what the arm helper stores in the frame.** F5's rule
  required the helper's three stores through `t1`, but no rule checked
  what they store. Now the helper accesses `ddc` exactly once, by a
  read. It makes exactly three stores through the register that its
  last write of `sscratch` takes: at `CF_MON_DDC`, in slot 0, and in
  slot 11 (`a1`'s). The first two store the register that the `ddc` read
  wrote, and nothing writes that register again before the value's last
  use. Slot 11's stores the device tree's capability: an SCBNDSR whose
  bounds register holds `BE_MVP_DTB_BYTES`, of an SCADDR of the `ddc`
  read's register whose address register holds `BE_MVP_DTB_GPA`. Every
  source is its operand's nearest earlier writer. Each constant is
  evaluated from the words that make it, back through their nearest
  earlier writers, with the checker's own semantics for `lui`, `addi`,
  `addiw`, and `slli`. It is compared with the value that the checker
  reads from `mvp-layout.h`. GCC makes `BE_MVP_DTB_GPA` with `addiw t2,
  zero, 1055` and Clang with `addi t2, zero, 1055`, each then shifted by
  `slli t2, t2, 21`; both make `BE_MVP_DTB_BYTES` with `lui t2, 0x1`.

Each new rule has a negative test among the image check's CHERI
mutations, each an in-place replacement of one to four words: sixteen
for F1 to F5, and ten for r5.

- F1: the `ddc` block reordered (load, install, read, save); a second
  `ddc` write, on the vector's bad-stack path.
- F2: `ct0` saved from `ct1`'s spill; `ct1` saved from `ct0`'s; the read
  of `sscratchc` made a NOP, so slot 2 takes the guest's `ct1`; the
  restore made a NOP; the restore from the guest's `csp`; a third write
  of `sscratch`, on the bad-stack path.
- F3: the injection helper's `MODESW.CAP` made a NOP; its `MODESW.INT`
  made a NOP; its `MODESW.INT` moved after the write of `vsepc` from
  `a2`; the arm and budget helpers' `MODESW.INT` made a NOP.
- F4: in the arm helper, the SCADDR's base set to zero after the `ddc`
  read, by a three-word window that drops the first word of `li t2,
  BE_MVP_DTB_GPA` (before r5's rule, no rule noticed that loss); the
  budget helper's `ret` as `c.jr ra` and `c.nop`.
- F5: the clear of slot 16 made a NOP.
- r5: the store at `CF_MON_DDC` from `t3`; slot 0's from `x0`; slot
  11's from `t0`, the unbounded `ddc`; 1054 in place of 1055 in the
  `li`'s first word; the SCBNDSR's bounds register `a1` in place of
  `t2`; its constant made by `lui t2, 0x2`; the device tree's SCADDR
  based on `x0`; slot 11's store moved to slot 12 (`a2`'s); `addi t0,
  zero, 0` in place of the `li`'s first word, which writes the `ddc`
  read's register before the value's last use; and a second `ddc` read
  in that place.

Each mutation of F1 to F5 was applied alone to the CHERI variant's
images of the three scenarios, built with each toolchain. The checker of
`82a24819`, before the fixes, accepted every one, and the fixed checker
rejected every one with its new rule's message: 192 judgements, none
unexpected. Each mutation of r5 was applied alone in the same way to the
images of the CHERI variant and of part 3, the CHERI-aware monitor with
the Linux guests. The checker of `fca46846`, before T5, accepted every
one, and T5's rejected every one with its clause's message: 240
judgements, none unexpected. F6 has no mutation: the CHERI capture runs
of parts 1 and 3 cover it. The image check's CHERI mutations are now 153
(two-guests), 157 (te-poc), and 166 (anchor), in parts 1 and 3; after F1
to F5 they were 143, 147, and 156.

The tree of `369e79f0` was checked on 2026-11-06, before it was
committed:

- `make -C mvp check`, the plain variant, passed every step but
  `claim-ledger-check`, among them the image check's 122, 126, and 135
  mutations with each toolchain, unchanged; the capture checker's 300
  self-test cases and 459 mutations; `BE_MVP_QEMU: PASS runs=64
  attempts=81 refused=17`; `BE_MVP_SESSIONS: PASS sessions=6 attempts=9
  refused=3`; and `BE_MVP_EVIDENCE: PASS`, with 557 files.
  `claim-ledger-check` failed as it has since the split, with the same
  11 SHA-256 mismatches in the same seven files.
- `mvp/tools/cheri-check.sh` passed against beryllium-cheri at
  `316ad8c4`:
  - part 1: all 20 make invocations, `BE_MVP_QEMU: PASS runs=48
    attempts=54 refused=6`, and `BE_MVP_SESSIONS: PASS sessions=6
    attempts=6 refused=0`;
  - part 2: `BE_MVP_CHERI_PLAIN: PASS images=162 (be-mvp-boot-pic.img=52
    be-mvp-boot-qemu.img=6 be-mvp-boot.img=54 be-mvp.bin=50)
    reference=c7be2498f2e0 records=20261105-rc4:162`;
  - part 3: the image check, `BE_MVP_QEMU: PASS runs=48 attempts=56
    refused=8`, and `BE_MVP_SESSIONS: PASS sessions=6 attempts=7
    refused=1`;
  - `time: cheri 453 s, plain 29 s, regression 383 s, total 865 s` and
    `BE_MVP_CHERI_CHECK: PASS`.
- The sixteen mutations, judged again on that run's images, gave 192
  judgements for part 1's and 192 for part 3's, the CHERI-aware monitor
  with the Linux guests, none unexpected.

The tree of `d4d4f5e0` was checked on 2026-11-06, clean, as a commit on
a detached `HEAD`, before the branch moved to it:

- `make -C mvp check`, the plain variant, passed every step but
  `claim-ledger-check`, among them the image check's 122, 126, and 135
  mutations with each toolchain, unchanged; the capture checker's 300
  self-test cases and 459 mutations; `BE_MVP_QEMU: PASS runs=64
  attempts=80 refused=16`; `BE_MVP_SESSIONS: PASS sessions=6 attempts=6
  refused=0`; and `BE_MVP_EVIDENCE: PASS`, with 533 files.
  `claim-ledger-check` failed with the same 11 findings, SHA-256
  mismatches in the same seven files, as before T5.
- `mvp/tools/cheri-check.sh` passed against beryllium-cheri at
  `316ad8c4`:
  - part 1: all 20 make invocations, among them the image check with
    153, 157, and 166 mutations; `BE_MVP_QEMU: PASS runs=48 attempts=56
    refused=8`; and `BE_MVP_SESSIONS: PASS sessions=6 attempts=7
    refused=1`;
  - part 2: `BE_MVP_CHERI_PLAIN: PASS images=162 (be-mvp-boot-pic.img=52
    be-mvp-boot-qemu.img=6 be-mvp-boot.img=54 be-mvp.bin=50)
    reference=c7be2498f2e0 records=20261105-rc4:162`;
  - part 3: the image check with 153, 157, and 166 mutations;
    `BE_MVP_QEMU: PASS runs=48 attempts=54 refused=6`; and
    `BE_MVP_SESSIONS: PASS sessions=6 attempts=8 refused=2`;
  - `time: cheri 463 s, plain 29 s, regression 382 s, total 874 s` and
    `BE_MVP_CHERI_CHECK: PASS`.
- r5's ten mutations, judged again on that run's images, gave 120
  judgements for part 1's and 120 for part 3's, none unexpected.

The review left these residuals, which are not changed here; r5,
once among them, is fixed above:

- **r1, the resume tail's restore window.** Today the tail's restore
  runs straight from its `MODESW.CAP` to its `sret`: `ct6` from
  `sscratchc`, the guest's `ddc`, then the 31 registers, `ct6` last. No
  rule requires that the window hold nothing else. An instruction
  between two of its loads (a second `ddc` write, a `MODESW.INT`, a
  register's clobber) would pass. The mutations replace words in place
  and cannot insert one, and every word of the window is one that a rule
  requires, so no negative test can show it.
- **r2, the merge loop.** The resume tail's rule for a register that the
  dispatch changed checks the loop's two stores, the integer over the
  slot's address and the zero over its metadata, not the loop itself, as
  its docstring says.
- **r3, the plain variant's rules.** They share F2's looseness: the
  vector's slots for `x2`, `x5`, and `x6` may be stored from any
  register, and no static rule requires the vector's restore of
  `sscratch`. The resume tail's run-time check, that `sscratch` equals
  the record's address, catches a wrong address. The development line's
  checker is accepted and pinned, so this branch leaves those rules as
  they are. Tightening them is a candidate for the development line, for
  the responsible human to decide.
- **r4, a design fact: the guest's first `ddc` and PCC.** Each guest's
  first `ddc` is the monitor's: the arm helper stores the `ddc` it reads
  in slot 0, which the resume tail installs. Its first PCC is `sepcc` as
  the first `sret` finds it, with the guest's entry as its address: the
  resume tail writes `sepc` as an integer, which sets only the address,
  and `sret` installs `sepcc` whole. On a domain hart, the monitor writes
  neither `ddc` before the arm helper reads it nor `sepcc` as a
  capability before that first `sret`, and it takes no interrupt in HS
  there, since `sstatus.SIE` stays 0. The firmware's hart start
  (`sbi_hart_switch_mode`) writes `mepcc`, `stvecc`, `sscratchc`, `sie`,
  and `satp`. The firmware writes `sepcc` elsewhere only with a trap it
  redirects to HS, an SSE event, which the monitor would have to
  register, or a switch between firmware domains, which QEMU's device
  tree does not define beyond the root one; and it writes no `ddc`. So,
  unless the monitor takes an exception in HS before its guest's first
  entry, `ddc` and `sepcc` hold their reset values, which the CHERI QEMU
  sets to its infinite capability: base 0, the whole address space,
  every permission, Integer Pointer Mode. This is read from the
  emulator's and the firmware's sources (see "Sources"), not observed in
  a run; on other CHERI hardware the reset values are the
  implementation's. A guest therefore starts with capabilities in `ddc`
  and PCC that bound none of its accesses, and its confinement on this
  branch rests on the G-stage alone, not on capability bounds. The
  branch makes no capability-confinement claim.
  The enforcement plan's section 3.2 adds the guest's side, from CHERI
  Alliance Linux's source: the purecap kernel makes its first
  capabilities from PCC and panics unless that root is tagged, unsealed,
  with every permission the hart supports, base 0, and length `~0UL`,
  and it clears `ddc` itself; in a scratch run with PCC and `ddc`
  bounded to a guest's window, each guest stopped in early boot (E4, not
  evidence). Since CE-2 every CHERI guest's capture must carry its
  kernel's report of that root, `CHERI: Root capability:` with the bounds
  `0x0000000000000000-0xffffffffffffffff`, and a capture whose root is
  bounded to the window is rejected (the plan's Q6). r4 therefore stays
  a design fact of CHERI Linux guests, now seen in every run.

## Enforcement plan (accepted)

On 2026-11-06 the responsible human asked: "on cheri, does it actually
enforce anything during these tests, or it just enabled & running?" On
the instruction `accept 6944d7b4 ; push cheri and plan cheri enforcement`
the same day, the [CHERI enforcement plan](cheri-enforcement-plan.md) was
written on local branch `beryllium/cheri-enforcement-plan` from
`aa0aea14`, and is accepted at exact commit
`9ec57998148b693019e7af6eba88c2160bfc09da` (2026-11-06, `accept
9ec57998`, Q1 to Q12 at their defaults; its
[review and acceptance record](cheri-enforcement-plan-review-summary.md)).
Its work packages CE-2 to CE-5 run on `beryllium/cheri-enforcement`, behind
the MVP 1.0 release path, which the same instruction made the priority. From sources and four
scratch experiments, which are not evidence, it finds:

- the guests' own CHERI faults are already delegated (`hedeleg` bit 28),
  but no test makes one;
- bounding a guest's first PCC and `ddc` (r4, above) does not suit Linux
  guests: CHERI Alliance Linux requires a first PCC that is the whole
  address space with every permission, and clears `ddc` itself;
- the emulator checks a capability-write PTE bit in the G-stage when its
  `cheri_pte` property is on, which this branch's runs leave off.

It plans, for this branch only and outside the MVP's claim: that
property on for every CHERI run, with the capability-write bit set in
each domain's window leaves and clear in every declared page's leaf; a
guest kernel's tagged store to the channel page that must end the run;
in-guest CHERI faults that must occur while the run continues; and the
negative images and mutations that judge them. The work's result comes
to the responsible human as one result packet.

On 2026-11-07 the human raised the plan's soft limit to 2,000 counted
lines, the `mvp/src/` lane staying at 100 (its erratum 1), and resumed
CE-4. The work packages are done on `beryllium/cheri-enforcement`, each
reviewed line by line by the owner session: CE-2, Zcheripte and the
G-stage capability-write control (`20af3dac`); CE-3, the guests' own
CHERI faults (`15e25343`); CE-4, a guest kernel's tagged store to the
channel page and its control (`9ab49914`); and CE-5, this page's records
and `COPYING`'s second module. From the plan's acceptance record
`89ab3ac3` through CE-5 they add 1,715 counted lines of the 2,000 by its
section 7's rule (Markdown excluded), 38 of them in `mvp/src/`. The
result, exact commit `3998e34e`, is responsible-human accepted (2026-11-07,
`accept 3998e34e, merge and push`; the
[result review and acceptance record](cheri-enforcement-result-review-summary.md)),
and this branch is fast-forwarded to the commit recording it and pushed
to the private `origin`.

## What CHERI enforces on this branch

The enforcement plan's section 8 fixes these words, and this page makes
no other claim about CHERI enforcement (its Q12):

On this branch, under emulation of CHERI v0.9.3 (CHERI Alliance QEMU at
`008944fe` with beryllium-cheri's two local changes, its `cheri_pte`
property on), the CHERI-aware monitor's G-stage leaves allow tagged
capability stores to each domain's own window and refuse them to every
declared page (the channel, request, response, and secret pages). In
the branch's check, a guest kernel's tagged
capability store to te-poc's channel page ended the run at the G-stage
as a store guest-page fault, and the same store landed when the
emulated hart lacked that property. Inside each CHERI Linux guest of
te-poc, a purecap process's load one byte past a 16-byte capability was
delivered to it as `SIGSEGV` with `SEGV_CAPBOUNDSERR`, and a `write(2)`
through that capability returned `EFAULT`, while the run continued. The
guests' first PCC and `ddc` remain the whole address space, which CHERI
Alliance Linux requires. The G-stage control is this emulator's
behaviour: the RISC-V CHERI specification leaves the field reserved in
G-stage entries. These are emulation results for one emulator and one
guest; they are not evidence for the MVP's claim and show nothing about
CHERI hardware.

The counts, from the last check (2026-11-08, at `9ab49914`; "Checking
it" above):

| Test (the plan's section 6) | Runs in part 1 | What the captures showed |
| --- | --- | --- |
| B1, the window leaves | 56, all but `cap-store`'s control with the property on | Each CHERI guest's `PTE.CW support: yes`; `no` in the control |
| B2, the monitor's own rule | `channel-cw`, one per toolchain | `BE_MVP:FAIL gstage` at boot, no domain hart started |
| B3, the store | `cap-store`, one per toolchain | `BE_MVP:FAIL guest-page-fault`, `cause=0x17`, `htval=0x21000020`, `htinst=0x0`, `spvp=1`; the first domain's last line the module's integer readback, `value=0x5678` |
| B4, the control | `cap-store`'s image without the property, one per toolchain | The module's `channel offset=0x80 tag=1`; both domains' `RESULT pass` |
| C1 and C2, the guests' own faults | te-poc's run, `no-inject`, `cap-store`, and its control, one each per toolchain | In both domains: `bounds signo=11 code=12`, the 16-byte write's `result=-1 errno=14`, the 64-byte write's `result=64`; both domains' `RESULT pass` in te-poc's run |
| C3, delegation | `cheri-fault-hs`, one per toolchain | `BE_MVP:FAIL exception` with `cause=0x1c`, `spvp=0` |

The CHERI rules' mutations of 14 passing captures in part 1, 94, and of 2
in part 3, 10, were each rejected for its own reason.

## Running it by hand

The responsible human's request of 2026-11-06: "I will want to run Be
manually and watch all of the console & busybox activity etc, on both RVI
and cheri". Each scenario has a shell image (M7), whose granted domains run
BusyBox's `sh` on the console, `/dev/hvc0`. A live run is a demonstration,
never evidence. Each image keeps the accepted run budget, 2^32 ticks: 429
seconds, about 7 minutes, at QEMU's 10 MHz timebase.

### The commands

From the repository root, for the plain variant (RISC-V, the tool lock's
QEMU 10.2.2 and OpenSBI v1.6):

```sh
./mvp/mvp live
```

It builds the shell images (make's `variants`) and prints one line per
image, `BE_MVP_LIVE: TOOLCHAIN/SCENARIO image=BOOT_IMG qemu: COMMAND`, for
GCC and Clang and for two-guests, te-poc, and anchor, then a closing line.
To run one of them, here GCC's te-poc, in this terminal:

```sh
eval "$(./mvp/mvp live | sed -n 's|^BE_MVP_LIVE: gcc/te-poc image=[^ ]* qemu: ||p')"
```

For the CHERI variant (the CHERI emulator and firmware from
`../beryllium-cheri`, which is only read):

```sh
mvp/tools/cheri-live.sh
mvp/tools/cheri-live.sh --run cheri.cheri-linux/gcc/te-poc
```

The first builds the CHERI-aware monitor's shell images with each guest
flavour and prints one line per image, `BE_MVP_CHERI_LIVE:
cheri.FLAVOUR/TOOLCHAIN/SCENARIO image=BOOT_IMG qemu: COMMAND`, for the
flavours `cheri-linux` (CHERI Linux, purecap BusyBox) and `linux` (the
plain Linux guests), then a closing line. The second builds one flavour's
images and runs the one command in this terminal, and `--help` prints the
runner's description. `make -C mvp live
MVP_MONITOR=cheri` refuses, naming this runner: its command would name the
tool lock's QEMU and firmware, which cannot run the CHERI-aware monitor.

On 2026-11-06 each printed command was smoke-tested on a
pseudo-terminal, as a human's terminal holds it: the six plain commands,
the twelve CHERI ones, the one-liner above, and `--run` for two images.
Each booted to `BE_MVP:15 INPUT_ARMED`, `BE_MVP:16 FOCUS none`, and each
shell's `MVPINIT 11 SHELL` line, in about 0.4 seconds (plain) and 1.3 to
2.6 seconds (CHERI) after QEMU started. Then `~0`, and `~1` where G1 has
a shell, each followed by Enter, brought back that shell's `# ` prompt.
Three CHERI boots were refused (below) and run again. This is a
demonstration check, never evidence; its logs are not kept in the
repository.

### At the console

- **Boot.** OpenSBI's banner, then the monitor's `BE_MVP:00` to
  `BE_MVP:11` lines, then each guest's lines, prefixed `BE_MVP_G0:` or
  `BE_MVP_G1:`. The console is ready when hart 0 has printed
  `BE_MVP:15 INPUT_ARMED grants=...` and `BE_MVP:16 FOCUS none`, and each
  shell `MVPINIT 11 SHELL tty=/dev/hvc0 role=...`.
- **A refused boot.** QEMU's `virt` machine starts the firmware on any of
  its eight harts. When that is a domain hart, the monitor stops at
  `BE_MVP:FAIL firmware`, right after `BE_MVP:02`, and QEMU exits. Run the
  command again.
- **Focus.** At the start of a line, `~0` or `~1` gives that domain the
  input, and hart 0 prints `BE_MVP:16 FOCUS g0` or `g1`. `~~` types one
  `~`, and `~` before any other key is dropped. Typed bytes go to the
  focused domain only. A line typed before any focus, or to a domain
  without the grant, is dropped, and hart 0 prints the first drop of each
  kind, for example `BE_MVP:17 INPUT_DROP no-focus`.
- **Output.** Nothing you type shows until you press Enter: the guest
  echoes each key, but the monitor prints only whole lines. The line then
  appears with the shell's prompt, as `BE_MVP_G0: # echo hello`, and the
  command's output follows. Backspace edits the line in the shell, but
  its echo prints as `? ?`, since the monitor prints any byte outside
  0x20 to 0x7e as `?`: `echo abc`, Backspace, `d` shows as
  `BE_MVP_G0: # echo abc? ?d` and prints `abd`. A prompt that waits for
  its line can share it with a later kernel message, as `random: crng
  init done` does about 86 seconds in. Each domain's lines keep its
  prefix, and hart 0's own lines (`BE_MVP:DENY`, `BE_MVP:MGMT`, and the
  rest) appear between them.
- **The end.** `exit` in a shell ends it (`MVPINIT 11 SHELL exit=0`), and
  its domain then powers off. When every domain has, hart 0 prints
  `BE_MVP:13 RUN_COMPLETE` and `BE_MVP:14 SHUTDOWN`, and QEMU exits. If
  the run budget runs out first, hart 0 prints `BE_MVP:20 REGISTERS
  at=terminal ...`, `BE_MVP:FAIL run-timeout`, and `BE_MVP:DETAIL
  ticks=...`, and QEMU exits. An idle run of GCC's two-guests ended so
  after about 430 seconds, on each emulator.
- **A frozen domain (CHERI emulator).** Now and then a domain stops for
  good: the CHERI QEMU's wake-up stall (under "Checking it"). End QEMU
  with Ctrl-C and run the command again.
- **Quitting at once.** Ctrl-C ends QEMU at once, which prints
  `terminating on signal 2`. The commands give QEMU `-monitor none`, so
  its console is plain standard input and output with no Ctrl-A escape:
  Ctrl-A then x reaches the focused shell as two bytes, and Ctrl-C never
  reaches a guest. The smoke test ended every run so.

### What to type

Type each line, then Enter. After a focus line, `~0` or `~1`, Enter only
brings back the focused shell's prompt.

- **two-guests:** a shell in each domain.

  ```text
  ~0
  echo hello from g0
  ls /bin | wc -l
  ~1
  echo hello from g1
  exit
  ~0
  exit
  ```

- **te-poc:** G0 is the channel's writer, G1 its reader (security model
  v1's Instance 2).

  ```text
  ~0
  be-chan write hello
  be-deny load-unmapped
  ~1
  be-chan read
  be-deny store-shared
  be-deny load-unmapped
  exit
  ~0
  exit
  ```

  `be-chan write hello` prints `MVPINIT 12 CHAN write gpa=0x84000000
  bytes=... text=hello` in G0, and `be-chan read` prints `MVPINIT 12 CHAN
  read ... text=hello` in G1. Each `be-deny` makes one denied access:
  hart 0 prints `BE_MVP:DENY ...`, and the guest prints `MVPINIT 08
  DENIED n=... kind=... gpa=...`.
- **anchor:** only G0, the untrusted host, has a shell; G1, the protected
  domain, keeps its role and has no grant (Instance 3).

  ```text
  ~0
  be-anchor request 7
  be-deny store-shared
  be-deny load-unmapped
  ~1
  be-anchor pause
  be-anchor terminate
  exit
  ```

  `be-anchor request 7` prints `MVPINIT 09 REQUEST n=7 digest=...` in G0
  after G1's `MVPINIT 09 RESPONSE n=7 digest=...`, the same digest. `~1` is
  dropped (`BE_MVP:17 INPUT_DROP no-grant`), so the focus stays on G0.
  `be-anchor pause` and `be-anchor terminate` ask hart 0, through the
  management extension, to pause and then terminate G1; hart 0 prints
  `BE_MVP:12 DOMAIN_PAUSED` and `BE_MVP:12 DOMAIN_TERMINATED`.

## Keeping it in step with the development line

1. **Merge `main` after each move of the development branch.** Merge
   `main` into this branch with a merge commit. Never rebase this branch
   once it has been pushed.
2. **Resolve conflicts by keeping both sides:** the development line's
   change and the CHERI adaptation. The CHERI side is in the CHERI
   variant's own places: the `BE_MVP_CHERI` blocks in `mvp/src/`
   and `mvp/tests/sbi-test.c`, the switches' conditionals in
   `mvp/Makefile`, `mvp/guest.mk`, and `mvp/tools.mk`, the
   `--monitor cheri` and `--guest-flavour cheri-linux` rules of the
   checkers and generators, and `mvp/guest/cheri-pins.txt` with the
   CHERI guest build. A development-line change to the plain variant's
   own files, among them `mvp/guest/pins.txt` and each `scenario.json`,
   merges as it is. If the change reaches what the CHERI rules depend
   on, adapt the CHERI side here. Examples are the six routines in
   `mvp/src/mvp-trap.S`; `mvp/tests/check-image.py`; and the guest
   build.
3. **Run `mvp/tools/cheri-check.sh`.** Its part 2 builds the merged
   `main` commit's reference and requires the plain variant's boot
   images to equal it, byte for byte. Re-pin `mvp/guest/cheri-pins.txt`
   only when a CHERI guest input changed, and say why in the merge
   commit.
   `mvp/tools/build-guest-cheri.sh --unpinned` prints the new pin lines;
   its header lists its inputs.
4. **Changes flow one way**, from the development line to this branch.
   Nothing from this branch enters the development line without the
   responsible human's separate decision under an approved bounded plan.
   A fix that is not CHERI-specific goes to the development line by its
   normal process, then returns here by merge.

## Where the work happens

Work on this branch is Beryllium owner work. It happens in a separate
clone of the canonical checkout, so that the shared checkout can stay on
the development line while both lines move. The clone pushes the branch
back to the canonical repository. Git refuses a push to the branch that
a checkout has checked out, so switch the shared checkout to this branch
only when no clone needs to push. The CHERI stack's pins, its build
tools, the CHERI QEMU's patches, and the experiments' records are under
`cheri/` (see `cheri/README.md`), and the stack is built under
`build/cheri/`, outside the tracked tree.

## Gates

Each of these needs the responsible human's instruction:

- pushing this branch to the private `origin`;
- any publication;
- any merge into `main`, the development branch.

Nothing from Codasip's non-public sources enters this branch (the
responsible human's rule of 2026-11-04).

## Sources

- beryllium-cheri, at commit `75b93e6`:
  - `experiments/be-cheri-poc.md`: the proof of concept's method,
    findings, and gaps;
  - `experiments/be-cheri-poc-results.txt`: its results;
  - `experiments/be-cheri-poc-vdso.txt`: the emulator defect behind the
    second local QEMU change.
- beryllium-cheri, at commit `f7a1f76`, for the variant split:
  - `HANDOFF.md`, "Where things stand": the recommendation to treat
    CHERI as a variant of the RISC-V arch, and the proposed split with
    its acceptance test;
  - `experiments/cheri-guest.md`, "Result": why the monitor switches
    `ddc` on every trap.
- For r4 of the CHERI rules' review, the emulator's and the firmware's
  sources, as beryllium-cheri at commit `316ad8c` pins and builds them
  (read only):
  - CHERI Alliance QEMU at `008944fe`, with beryllium-cheri's two local
    changes, which leave `sepcc` and `ddc` as they are: the reset in
    `target/riscv/cpu.c`, `update_special_register` in
    `target/riscv/cpu_helper.c` (an integer write sets only the
    address), the `sret` helper in `target/riscv/op_helper.c`, and
    `set_max_perms_capability` in `target/cheri-common/cheri_utils.h`;
  - CHERI Alliance OpenSBI at `c0575bc8`: `sbi_hart_switch_mode` in
    `lib/sbi/sbi_hart.c`, `sbi_hsm_hart_start_finish` in
    `lib/sbi/sbi_hsm.c`, and its writes of `sepcc` in `lib/sbi/sbi_trap.c`,
    `lib/sbi/sbi_sse.c`, and `lib/sbi/sbi_domain_context.c`.
- `sidebar-cheri-mvp.md` and `cheri-alignment.md`, from the development
  line.
