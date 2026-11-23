<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP M11 evidence record

This record holds the evidence of M11, the physical boundary under the
monitor, made under the accepted [M11 plan](mvp-m11-plan.md) (proposed
as exact commit `1be9272a`, accepted 2026-11-11 by the responsible
human's sign-off, `77eabce5` on `main`) and its decision record. M11's
work lands on one working branch from that commit, and this record grows
with it: one section per work package, each written when the package
ends. It records what was run, when, on which commit, and what it
printed; it makes no claim beyond those lines. Every run here is under
emulation; nothing here ran on a board. Through M11-3 the runs are on
the development host `lx2` (an Intel i7-10610U, 4 cores and 8 threads,
46 GB, Fedora 44, the performance profile). From 2026-11-15 they are on
the workstation `l1` (an Intel i9-14900K, 24 cores and 32 threads,
62 GB, Fedora 44, the throughput-performance profile), by the decision
record's entry of that date; M11-4's section tells the move.

## M11-2: preparation

### Outcome first

M11-2's required result (the plan's work-package table) holds at its
point, exact commit `1532acb0`:

- both tool locks pass on `lx2` after one move (`f17d108b`), and both
  baselines hold: the gates at the lock commit equal the last record
  made under the old lock, and the `verify` baseline is that run, with
  the WP arm's records taken again under the decision `verify: wp3`
  (from 18:00Z to 21:33Z on 2026-11-12: 130 of 134 goals, and 18 of the 24
mutants killed, as in the record; its records equal the record's but for
round 0's counts, where 12 prover runs timed out against the record's 5
and round 1 proved all seven, which the decision `accept crossings`
takes as time-limit crossings);
- the proof-impact review is written ([mvp-m11-proof-impact.md](mvp-m11-proof-impact.md),
  `d82e0462`, with its decision `65587855`);
- the firmware binary that the evaluator builds equals the host's
  (`evaluate` at `1532acb0`: 342 of 342 images identical, the firmware binary among them);
- every scenario, variant, typed session, and U-Boot rehearsal case
  passes under the firmware base, with no change but the named ones:
  one instruction of each monitor, the two-guests scenario's digest, and
  the negative `sbi-3.0` renamed `firmware-version`;
- the QEMU oracle reads all eight harts' PMP registers and named words
  of memory at the end of every run of the plain monitor, recording the
  PMP registers as absent on the `rva23` CPU, which has none;
- the boot chain's call families before the monitor are listed below;
- at the point, every verifier suite gives the base's verdicts, and the
  base's counts but where solver runs reached their time limits (two
  goals of the WP arm and three rows of the ring's bounded check,
  recorded as time-limit crossings under the decision `accept
  crossings`; each arm's verdict, the ring's totals, and every mutant's
  verdict are the base's).

### The commits

On the working branch `m11`, over `77eabce5`, each reviewed line by line
before it landed, unsigned:

| Commit | Content |
| --- | --- |
| `f17d108b` | Both tool locks moved to `lx2`: `python3` 3.14.10, the host GCC and `cpp` 16.2.1-3, `util-linux` 2.41.6 (`sfdisk`); the evaluator's closure from 259 packages to 257 (36 newer, 2 dropped, none added); ledger rows C-20 and C-21 |
| `d82e0462`, `65587855` | The proof-impact review and its decision |
| `8ab6ccf8` | The plan's decision record: `ar: yes`, `review: yes`, `verify: wp3`, `oracle: absent`, `harness: 7000` |
| `fdb2a8de` | `mvp/verify/tools/near-limit.py`: each solver run near or over its limit, listed from the arms' own logs |
| `b32c9c9e` | The tool lock's role `cross_ar` |
| `c86a5b1a` | The firmware base: upstream OpenSBI at `ed70256d` (tree `f3685099`), fetched by commit and tree, built reproducibly in its default `generic` configuration, `fw_dynamic.bin` pinned as `ebd912c6…` |
| `3793fb4a` | The QEMU oracle and the harness's new pass rule |
| `1c2e6099` | The WP arm's parallelism from the host's physical cores |
| `9e0563d7` | Every plain run on the firmware base; `firmware-version`; M9's saved captures judged against a pinned era set |
| `1532acb0` | The target digests and the litmus record written again at `9e0563d7` (the point) |

### The baseline at the lock commit

The gates ran at `f17d108b` from a clean clone on 2026-11-11, 17:19Z to
18:25Z: the tool lock (32 roles, 257 packages); `./mvp/mvp check`;
`./mvp/mvp evaluate` (341 of 341 images identical; evaluator image
`89052df019b8-009c2eba5655`); the U-Boot rehearsal (7 cases); the
kernel's second build (23 outputs identical); `./be model-check`; and
the model's evaluator. Against the last record made under the old lock
(`mvp/results/20261109-cheri-integration/`), all 162 flat images and all
185 outputs that are not ELF files have the record's digests, and
`check`'s five deterministic records are byte-identical.

`./mvp/mvp verify` ran at the same commit from 18:26Z to 06:23Z
(`wall_seconds=43004`). Of its 32 retained files, 26 equal the last
record's once run metadata is set aside. The six that differ are the WP
arm's (127 of 134 goals against 130: seven prover runs on three goals
crossed the 60 s limit, with six provers per job and two mutant jobs at
once on four cores), the summary's WP line, and the solver
qualification's `vacuity-ensures` case, which timed out (61.5 s) where
the last record's run answered at 49.5 s; its verdict is the same. The
ring's bounded check ended every one of its 837 main runs as the record
did. Trials of the WP arm's final round alone, on a quiet machine, gave
128 goals with six provers, and the record's 130 with three or two. This
was the plan's stop 11; the decision `verify: wp3` made the WP arm's
provers and mutant jobs follow the host's physical cores (`1c2e6099`:
three and one on `lx2`, six and two from thirteen cores up), and the WP
arm ran again alone at the lock commit with that change (2026-11-12,
18:00:44Z to 21:32:54Z, 12,730 s: `OPEN goals=134 proved=130`, 24
mutants with 18 killed, as in the record. Five of its six record files
equal the record's once run metadata is set aside; the sixth,
`rounds.txt`, differs only in round 0 (117 proved and 12 timeouts, where
the record has 124 and 5), and round 1 equals it (134 goals, 130 proved,
4 open). Its near-limit list: 2,724 prover runs, the slowest 59.3 s of
60, 15 near the limit, 297 over it; the decision `accept crossings`
makes this run the WP arm's baseline).

### The firmware base and the switch

The base builds on the host and inside the evaluator from the same
pinned source; the binary is `ebd912c6…` in both (`evaluate` at `1532acb0`: 342 of 342 images identical, the firmware binary among them). Every
plain run boots it, checked against its pin before each boot; the
earlier firmware, OpenSBI v1.6 as pinned before, is booted only by
`firmware-version`, which must fail as `boot` before any monitor line
and does: it prints `BE_MVP:FAIL boot` and no `BE_R3:01`.

The port's two counted rules raise `BE_R3_OPENSBI_SPEC_VERSION` in
`include/be/r3.h` to SBI 3.0. Against the lock commit's build, each of
the 50 monitor images (`be-mvp.bin`) differs in one byte, of one
instruction (`be_r3_validate_boot`'s `lui a3,0x2000`, now `0x3000`),
and the 28 built from the two-guests scenario also in the 32 bytes of
its scenario file's SHA-256. All 64 QEMU runs, 6 typed sessions, and 7
rehearsal cases gave their baseline verdicts, with the one renamed run,
and every count (exits, records, denials) lay within the ranges seen in
seven earlier sets of the same runs; five values had not been seen
before, all inside those ranges.

M9's saved captures carry measurement logs of images that are no longer
built. Under the plan's rule for saved captures, they are kept byte for
byte and judged against the expectations, authority reports, and
reference manifests of their time: `mvp/tests/fixtures/pre-m11/`, 36
files copied byte for byte from the lock commit's build and pinned by
their listing's SHA-256. Synthetic stand-ins, rendered from those
captures for the current images, keep every case that recomputes from
the build: the capture checker's self-test has 318 cases (300 before),
and its mutation test rejects 461 mutations (459 before).

### The oracle

At the end of every QEMU run, typed session, and rehearsal case, the
oracle stops the machine through QEMU's monitor on a private channel and
reads each of the eight harts' `pmpcfg0`, `pmpcfg2`, `pmpaddr0` to
`pmpaddr15`, `menvcfg`, and `mseccfg`, its program counter, and named
words of memory, and then quits QEMU. On the `rva23` CPU, which has no
PMP, the record says absent (the decision `oracle: absent`); the
CHERI-aware monitor's emulator exits at the guest's shutdown, so its
runs keep their own end of run with a fixed record that says so. On the
reviewed content, 64 QEMU runs, 6 sessions, and 7 rehearsal cases gave
their baseline verdicts, with 93 oracle records passing.

### The boot chain's call families

Observed in QEMU at the firmware's trap entry (`0x800005c0`, the
`mtvec` that the base installs; supervisor calls not delegated), with
QEMU's CPU log before the entry's first instruction and translation
blocks unchained, on direct boots of `two-guests`, three probe images,
and the U-Boot rehearsal's `two-guests` case:

| Caller | Families and functions |
| --- | --- |
| U-Boot, before the shim (rehearsal) | none |
| The shim | DBCN write; HSM hart start (its start rule) |
| The monitor on hart 0 | Base (specification version, extension probe); DBCN write; HSM hart start and status; IPI send; SRST system reset |
| The monitor on a VS-domain hart | IPI send |

Every call in each observed run is accounted for by these rows (for
example, the rehearsal's `two-guests` case: 427 calls, among 558 trap
entries). No run used another family.

### The re-proof point

M11-2's port rule changes `include/be/r3.h`, a header of both proved
leaves, so M11-2 is the first point of D-11. At `9e0563d7`, a clean
clone's `./mvp/mvp check` passed (2026-11-12, 11:26Z), and from its
build the two records were written again:

- `mvp/verify/target-digests.txt`: the target commit and `r3.h`'s
  digest. The specification's pin is unchanged; on this line the host
  has no commit `93a8d136`, so the record was written, and is checked,
  with the frozen text exported as `verify.sh` exports it.
- `mvp/verify/litmus/sequences.txt`: the target commit and both monitor
  ELFs' digests; no recorded symbol, address, size, byte, or excerpt
  changed, so the five litmus tests did not.

At `1532acb0`, the other seven gates passed from a fresh clean clone on 2026-11-12, 11:30Z to 12:21Z: the tool lock (33 roles, 257 packages); `check`; `evaluate` (342 of 342 images identical; evaluator image `89052df019b8-009c2eba5655`); the U-Boot rehearsal (7 cases, in 11 attempts, 4 of them refused and repeated because the firmware had booted on a VS-domain hart); the kernel's second build (23 outputs identical); `./be model-check` (stage 1: 26 theorems, 99 citations); and the model's evaluator. Its `verify` ran on `lx2` from 21:33Z on 2026-11-12 to 10:30Z on 2026-11-13 (46,599 s),
after the WP arm's night run. Against the base (the lock commit's run,
with the WP arm's records from that night run), 25 of its 32 record files
are equal once run metadata is set aside. The others are:
- the litmus record's digest, which the point wrote again;
- the near-limit suite's line, new in M11-2;
- the WP arm: two of Leaf A's assertions, `D_reads_87` and `D_reads_97`,
  whose prover parts each proved in under 54 s in the base, now reach the
  60 s limit in five of their ten parts (a sixth took 59.2 s), so 128 of
  134 goals are proved instead of 130; every mutant's verdict is
  unchanged (18 killed), and four masked mutants name the two goals among
  those that mask them;
- the ring's bounded check: three rows that took 556 s to 586 s of 600 in
  the base now reach 600 s (`acquire` at 512 bytes under cvc5, and `post`
  and `post_words` at 4,096 bytes under the SAT solver in configuration
  B); its totals (13,547 of 14,931 properties checked) and every mutant's
  verdict are unchanged.
Leaf A's code is token-equal to the base's; the leaves' only changed
input is `include/be/r3.h`, which the plan's F23 names as able to move a
solver's time. Its near-limit list: 4,331 runs, 19 near, 326 over. The
decision `accept crossings` records the WP arm's two goals and the three
rows as time-limit crossings, under stop 9.

### Departures and readings for review

- **The pieces landed on the working branch before the point's
  `verify`.** S3-C's stop (i), as the plan reads it, applies at each
  work package's merge into that branch. M11-2's pieces landed one by
  one as each was reviewed; the arms were re-run at M11-2's point
  before anything of M11-3 landed, which is how this record reads the
  rule for a package that lands in pieces.
- **The README's file table** gained the oracle's rows with the switch
  (`9e0563d7`), not with the oracle.
- **`digests.py` on this line.** Without the frozen text's export, its
  host mode hashes the working specification page, and `--check`
  reports only its first difference. The point's record was written
  with the export; later points do the same.
- **Soft limits.** The harness lane's limit is 7,000 lines by the
  decision `harness: 7000`; at the point, M11-2 adds 4,338 counted lines by the plan's rule from `77eabce5`: 4,071 in that lane, 246 in the firmware's build rules (limit 2,500), and 21 in the monitor's lane (the port's rule; limit 3,500). JSON, Markdown, the era fixtures, the proof records, and the lock's data are reported apart.

## M11-3: the layout

### Outcome first

M11-3's required result (the plan's work-package table) holds at its
point, exact commit `0e074244`:

- `check` passes on both toolchains, and the image checker refuses each
  of its 129, 133, and 143 mutations of the three scenarios' images
  (before the landing, from a clean clone of the reviewed content, on
  2026-11-13 from 10:35Z to 10:56Z, and again at the point);
- `./be model-check` passes with stage 1 proved again: its 26 theorems,
  their statements unchanged, 26 assumption sets closed, 99 citations,
  and the generated layout `b5536372…`;
- at the point, every verifier suite gives the base's verdicts. Its
  counts differ from the base's only where a run that reached the
  earlier time limit in the base ends within the doubled one (the
  decision `increase time limits`), and one known finding has a new
  witness that follows from the layout header (below).

### The commits

On the working branch `m11`, over the public `main` at `fa0e3c56`,
unsigned:

| Commit | Content |
| --- | --- |
| `6d0f5ae` | The layout by role and by writer (D-4, D-5), with the boundary off; the claim ledger's pins in C-10, C-40, C-41, C-48, and C-51 to C-55 |
| `5d0d7846` | Every time limit of the verifier's arms doubled, on the responsible human's direction, with its decision-record entry |
| `0e074244` | The point's records: the target digests and the litmus record at `5d0d7846` |

M11-6 (`9ab77ec`) and M11-5 (`a3dcbe9`) landed between `6d0f5ae` and
`5d0d7846`, so the point holds them too; neither changes an input of a
proved leaf. M11-3 adds 1,914 counted lines to the monitor's lane
(limit 6,000).

### The re-proof point

M11-3 changes three of the leaves' pinned inputs (`mvp-layout.h`,
`mvp.h`, and the port's `r3.h`), so its point is D-11's second. At
`5d0d7846`, from a clean clone's build (2026-11-13):

- `mvp/verify/target-digests.txt`: the target commit and the three
  files' digests, written with the frozen specification's export, as at
  M11-2;
- the litmus record: M11-3 moved the cited symbols, and 35 of the 55
  symbols' digests changed. Its 206 excerpt lines were found again by
  role: 80 with the same encoding, 112 with a new PC-relative offset,
  and 14 with a new register or offset (the descriptor's generation word
  is now at offset 128 of the published page). The five tests'
  programs, premises, and conditions are unchanged; their comments'
  addresses and digests are derived again, and one sentence of L1's
  comment is rewritten for a load that M11-3 added before the barrier
  (the VS-domain hart's check of its published page's address, which
  can only park it). The call-site scan finds the same fences at all
  ten sites;
- the claim ledger's pins in C-54, C-56 (two), C-57, and C-58, each with
  a note on its row.

At `0e074244` the other gates passed from a fresh clean clone
(2026-11-13, 16:03Z to 17:11Z): the tool lock; `check`; `evaluate` (609
of 609 images identical; evaluator image `89052df019b8-009c2eba5655`);
the U-Boot rehearsal (7 cases in 9 attempts, 2 refused because the
firmware had booted on a VS-domain hart, and repeated); the kernel's
second build (23 outputs identical); `./be model-check` (as above, with
the model's differential check); and the model's evaluator.

Its `verify` ran three times on `lx2`:

- the first, from 17:11Z on 2026-11-13, was ended by a loss of power at
  about 08:23Z on 2026-11-14, in its last arm, the ring's bounded check;
  every earlier arm had ended;
- the second, from 13:58Z on 2026-11-14, ended at 14:16Z in the WP
  arm's first qualification case: its container received SIGTERM from
  no podman command, at the moment podman's rootless pause process was
  replaced. No out-of-memory kill, core dump, or kernel event was
  logged, and the cause was not found; a run of that arm alone then
  started normally. `verify.sh` stopped without the arm's line (below);
- the third, from 14:26Z on 2026-11-14 to 06:05Z on 2026-11-15
  (56,297 s), is the point's record. Both partial records are kept
  beside it.

Against the base, M11-2's point at the earlier limits, 17 of the 32
record files are equal once run metadata is set aside (9 byte for
byte). Each difference in the other 15, read run by run:

- the limits themselves: the stated limit in the WP arm's rounds, in
  CN's assumptions and rounds, in Leaf A's bounded check's assumptions,
  and in the ring's assumptions; one qualification case's "killed after
  120 s"; and the digest of the qualification's expectations, a file
  that carries the limits;
- the litmus record's digest and the five tests' digests, written again
  at this point;
- runs that reached the earlier limit in the base and end within the
  doubled one, each recorded as an effect of the limit:
  - the WP arm: eight goals of round 0 (13 timeouts in the base, 5
    here) and Leaf A's `D_reads_87` and `D_reads_97` in round 1, all
    closed by Alt-Ergo, so 130 of 134 goals are proved, as at the lock
    commit's baseline. Every mutant's verdict is unchanged (18 killed),
    and the masks no longer name the two goals;
  - the WP qualification case `vacuity-ensures`: the prover gave up
    within the limit where it reached it in the base; the verdict is
    unproved, as required, in both;
  - Leaf A's bounded check of `check_frame` under the SAT solver:
    successful (284 properties) where it reached 300 s in the base; the
    arm's verdict is SUCCESSFUL in both;
  - the ring's three rows that reached 600 s in the base: `acquire` at
    512 bytes under cvc5 now ends with its 15 failed properties, as at
    the lock commit's baseline, and `post` and `post_words` at 4,096
    bytes under the SAT solver end successful. The ring's totals (13,547
    of 14,931 properties checked) are unchanged; its mutants now run
    the two runs that those rows complete (`not_run` 2 to 0), and every
    mutant's verdict is unchanged;
- the ring's recorded finding `room` (the specification's room row
  against the leaf, a specification mismatch): the same assertion and
  reason, and the same four contradictions confirmed by its reproducer,
  with different values in its counterexample. Its trace job run again
  (2026-11-15) reproduces each point's values exactly at that point's
  commit, and the harness compiles `mvp-layout.h`, which M11-3 changed:
  another witness of the same finding, not a verdict;
- the near-limit suite's line: 4,419 runs, 1 near its limit, 273 over
  it (the base: 4,331, 19, and 326).

No verdict changed, and every changed count is an effect of the limit:
no stop 9. Leaf A's code is token-equal to the base's.

### Departures and readings for review

- **The point's `verify` ran three times**, for the reasons above; its
  record is the third run, from the start.
- **`verify.sh` stops at a suite with no result line.** Under
  `set -euo pipefail`, its search for the suite's result line fails and
  ends the script before that suite's line is written, so the suite is
  not named and the later suites do not run. It changed nothing here,
  since the run was repeated; it is left unchanged, as the arms' tools
  are, and listed as a residual.
- **The witness of `room`** is read as above: a bounded model checker's
  counterexample is one assignment among many, and this one follows
  from the compiled inputs.

## M11-4: signalling

### Outcome first

M11-4's required result (the plan's work-package table) holds at its
point, exact commit `47136f70`:

- `check` passes on both toolchains with no IPI call in any scenario
  image: the image checker refuses a scenario image that links either
  of the monitor's IPI send functions, and refuses each of its 133,
  137, and 147 mutations of the three scenarios' images;
- the counts are pinned: each scenario's expectation fixes `ipi` at 0
  and bounds `tick` by the run's interval, and the capture checker
  passes its 320 cases and refuses its 461 mutations;
- the six typed shell sessions pass, and each outbound ring's peak
  stays within its budget: the largest that a VS-domain hart reports in
  the point's runs is 2,696 bytes, of a budget of 16,384;
- `./be model-check` passes with stage 1 proved again: its 26 theorems,
  their statements unchanged, 26 assumption sets closed, 100 citations,
  and the generated layout `b5536372…`;
- at the point, every verifier suite gives the base's verdicts and
  counts on the same host. One more prover run reached its time limit,
  in a mutant that is killed either way (below).

### The commits

On the working branch `m11`, over the public `main` at `5ea5243a`,
unsigned:

| Commit | Content |
| --- | --- |
| `e52308a2` | Signalling on each hart's own timer tick (D-7), with the boundary off; the concrete model's exit decision and ring steps; the claim ledger's seventeen pins in C-10, C-40, C-41, C-48, and C-51 to C-58 |
| `cb9716ca` | The decision record: the checks' host is the workstation `l1` again (`hosts: l1`) |
| `c6334708` | The tool lock moved to `l1`; ledger rows C-20 and C-21 |
| `47136f70` | The point's records: the target digests and the litmus record at `c6334708` |
| `9540c69c`, `0ab4bd34` | The decision record: three soft limits re-set, and the harness lane's again |

By the plan's count from `77eabce5`, M11-4 adds 1,070 lines to the
monitor's lane and 202 to the harness lane. At the point the lanes
stand at: the firmware additions 708 (limit 800); the firmware's tests
and build rules 2,763 (3,000); the monitor 2,978 (8,000); the
descriptor's tools 3,266 (4,000); the harness 4,357 (15,000). The
limits are those of the decision record's entries of 2026-11-12 and
2026-11-16; the two of 2026-11-16 were asked for M11-7's work, which is
not on the branch at this point.

### The host

The workspace moved back from the laptop `lx2` to the workstation `l1`
on 2026-11-15, after M11-4 had landed. The decision record's entry of
that date (`cb9716ca`) makes `l1` the development host and the host for
`verify`, and names what follows here.

**Before the move, on `lx2`.** M11-4's content passed, from a clean
clone of a scratch commit of it (2026-11-15, 07:33Z to 08:52Z): the tool
lock, `check`, `./be model-check`, `evaluate` (609 of 609 images
identical), and the U-Boot rehearsal. Its commit message has the
counts.

**The lock.** `l1` had the lock's bytes for every role but `git`
(2.56.1; the lock named 2.56.0). The lock commit, `c6334708`, refreshes
the MVP's lock and its closure by the lock's own `refresh`: that role,
and the evaluator's closure from 257 packages to 259 (five at newer
versions, two added again, none dropped). It changes the files that
"The development host" lists, and no other.

**The gates at the lock commit**, from a clean clone on `l1`
(2026-11-16, 00:11Z to 00:56Z), before any other change: the tool lock
(33 roles, 259 packages); `check` (64 QEMU runs in 85 attempts, the 21
others refused because the firmware had booted on a VS-domain hart, and
repeated; 6 typed sessions in 7 attempts); `evaluate` (609 of 609
images identical; evaluator image `87263109e660-009c2eba5655`); the
U-Boot rehearsal (7 cases in 8 attempts); the kernel's second build (23
outputs identical); `./be model-check`; and the model's evaluator, at
its second attempt (below).

**Against the reference.** No record had been made on `l1` under the
lock of 2026-11-11, so the reference is the build that `lx2` made of
the same sources in M11-4's checks. All 162 flat images have that
build's digests, and `check`'s five deterministic records equal that
build's (the image check, the variants, the probes, the capture
checker's self-test, and its mutation test). Of the 609 listed build
outputs, 94 differ, all by the clone's path: the 50 monitor ELF files,
each identical once its debug sections are stripped, and the 44
expected-table files, which differ only in the digest of the firmware's
ELF file; the firmware binaries are equal. No stop 11.

### The re-proof point

M11-4 changes two of the leaves' pinned inputs: `src/mvp-sbi.c`, Leaf
A's translation unit, and `src/mvp.h`. Its point is D-11's third. The
two commits after M11-4 change no input of a leaf and nothing of the
monitor, so the records were written at the lock commit, `c6334708`,
from the build of the clean clone whose gates passed there:

- `mvp/verify/target-digests.txt`: the target commit, and the two
  files' digests; the other eleven files' digests, the flags, and the
  pins are unchanged. Written with the frozen specification's export,
  as at M11-2.
- The litmus record: the 55 excerpts were found again by role in the
  new monitors. Of their 206 lines, 103 keep their encoding (49 of them
  at the same address), and 103 are the same instruction to the same
  function or branch target with a new PC-relative offset; none has a
  new register or offset. Of the 55 symbols' digests, 35 changed. The
  five tests' initial states, programs, and conditions are
  byte-identical. Their comments' addresses and digests are derived
  again; L2 and L4 name the tick where they named the IPI; and L3 gains
  one sentence, on the room that a VS-domain hart now keeps in its
  outbound ring. The scan of the ring's callers finds no reader or
  writer added or removed and no fence changed; the one new load of a
  word that another hart writes is the room check's read of the
  reader's tail before a post, which the proof-impact review foresaw
  (its section 5).
- The claim ledger's pins in C-54, C-56 (two), C-57, and C-58, each
  with a note on its row.

At `47136f70` the other gates passed from a fresh clean clone on `l1`
(2026-11-16, 14:23Z to 15:03Z): the tool lock; `check` (64 QEMU runs in
89 attempts, 25 refused and repeated; 6 typed sessions in 10 attempts,
4 refused; 50 images within their budgets; the claim ledger's 9 checks
of 58 claims); `evaluate` (609 of 609 images identical; the same
evaluator image); the U-Boot rehearsal (7 cases in 10 attempts, 3
refused); the kernel's second build (23 outputs identical); `./be
model-check` (as above, with the model's differential check); and the
model's evaluator.

**The base on `l1`.** M11-3's point was run on `lx2`, so `verify` was
run once more at that commit, `0e074244`, on `l1` (2026-11-16, 06:44Z
to 12:16Z; 19,913 s, against 56,297 s on `lx2`). Every suite gives
`lx2`'s verdict: the WP arm 130 of 134 goals, with 18 of the 24 mutants
killed; CN 5 of 55; Leaf A's bounded check successful, 336 properties;
the ring's bounded check 13,547 of 14,931 properties. Of the record's
32 files, 26 are equal to `lx2`'s once run metadata is set aside (12
byte for byte). The other six, read run by run:

- the verifier image's local ID. Its tag, closure digest, sources
  digest, and the digest of its 613 packages are equal. `l1` still
  holds the image that it built before the workspace moved to `lx2`,
  and its ID is the one in the last record before M11
  (`mvp/results/20261109-verify-cheri-integration/`);
- three cases in which the prover must fail, and does on both hosts:
  the WP qualification's `known-fail`, and the vacuity cases
  `vacuity-ensures` and `vacuity-ensures+lemma-options`. On `l1` the
  prover gave up within the limit; on `lx2` it reached the limit;
- mutant m17, killed on both hosts: two of its goals reached the limit
  on `lx2`, and one on `l1`;
- round 0 of the WP arm: 1,088 split obligations proved on `l1` and
  1,080 on `lx2`; the same 124 of 129 goals proved, the same five open,
  the same counts by prover, and five timeouts on both;
- the near-limit list: of 4,419 runs, none near its limit and 264 over
  it on `l1`; one and 273 on `lx2`.

Each is a run that ends within its time limit on one host and reaches
it on the other, which the decision record's entry records as an
effect of the host, or the list of such runs, or the image's local ID.
No verdict differs: no stop 9.

**The point's `verify`** ran on `l1` from 15:03Z to 20:39Z on
2026-11-16 (20,161 s). Every suite's line gives the base's verdict and
counts: the WP arm 130 of 134 goals in one round, with 18 of the 24
mutants killed; CN 5 of 55; Leaf A's bounded check successful, 336
properties; the ring's bounded check 13,547 of 14,931 properties; the
five litmus tests Never. Against the base on `l1`, 24 of its 32 record
files are equal once run metadata is set aside (10 byte for byte). The
other eight, read run by run:

- the leaf's place in its file. Leaf A's five functions lie three
  lines lower in `src/mvp-sbi.c` (lines 204 to 327, for 201 to 324).
  The token gate passes on the same 686 tokens. The new line numbers
  appear in its line of the summary, in CN's transcription record, in
  each mutant's place in the three arms' mutant records, and in the
  unreachable statements that the WP vacuity record lists. With those
  three lines taken off, CN's and the bounded check's mutant records
  and the vacuity record equal the base's;
- the litmus record's digest and the five tests' digests, written again
  at this point (above); each test's result and its states are the
  base's;
- mutant m17 of the WP arm, killed in both runs: two of its goals
  reached the 120 s limit, where one did at the base on `l1`. Both did
  at the base on `lx2`;
- the near-limit list, by that run: of 4,419 runs, none near its limit
  and 265 over it (264 at the base);
- the ring's recorded finding `room`: the same assertion and reason,
  and the same four contradictions confirmed by its reproducer, with
  different values in its counterexample. The ring's header includes
  `src/mvp.h`, which M11-4 changed. At the base, the two hosts' records
  hold the same counterexample, value for value: it follows from the
  compiled inputs. Another witness of the same finding, not a verdict.

No verdict changed, and no suite's count. One run crossed its time
limit, m17's second goal, and with it the near-limit list's count. By
the plan's rule for D-11's points, a count that changes only because a
run crossed its limit is recorded as that and goes to the responsible
human under stop 9 with that reading: it is put to him with this
section. Leaf A's code is token-equal to the base's.

### Departures and readings for review

- **One run crossed its time limit at the point**, as above. It is read
  as an effect of the limit and not of the code: the mutant is killed
  either way, and the same run crossed the limit at the base on `lx2`.
  The responsible human's sign-off of the commit that adds this section
  accepts that reading.
- **Light work ran beside both runs of `verify` on `l1`**: builds, tool
  dry runs, and reading for the next work packages, by four delegates
  at most at once, each held to one core of the host's 32 threads, and
  the owner session's own short commands. Nothing that starts QEMU or a
  container ran beside either run.
- **The point's records are in the third commit after M11-4.** M11-4's
  message has them "in the commit after it". The decision record's
  entry on the host and the lock's move came between, and neither
  changes a leaf's input or the monitor; the records name the lock
  commit as their target, whose `mvp/src` and `mvp/Makefile` are
  M11-4's.
- **One change to M11-4's code was made at review, by the owner
  session.** The session that wrote M11-4 ended with the power loss of
  2026-11-14, with its work complete. The owner session's review of
  every line found no defect and made one cleanup, which the commit
  message names: the static `wait_serve()` takes no time arguments, and
  `wait_tick()` returns nothing.
- **The model's evaluator at the lock commit.** Its first attempt
  failed its tool check inside an image that podman had cached on `l1`
  on 2026-10-28, whose `python3` was 3.14.8; the gate had built
  nothing. The old image was set aside, and the gate, run again, built
  a fresh image and passed. This is read as the host's state, and not
  as stop 11's "a tool check that fails inside the model's evaluator".
- **The base's `verify` ran twice on `l1`**, by the owner session's
  mistake: it changed its scratch driver while the night's chain was
  reading that file, and the chain started `verify` again in the same
  clone, over the first run's record. The first run (01:09Z to 06:44Z)
  had ended with exit status 0, and what was read of it before it was
  lost agrees with the second: the first six suites passed, the WP arm
  stood at 130 of 134 goals and 18 mutants, CN at 5 of 55, and Leaf A's
  bounded check at 336 properties. The record is the second run's, from
  its start. The first run had also fetched the pinned Linux from its
  default address, where the second used the host's mirror; the
  kernel's bytes are pinned either way.
- **M11-7's first runs under emulation were made between the base's
  `verify` and the point's gates** (12:20Z to 14:20Z), in a scratch
  clone, to use the time that the second run had cost.
- **Two observations of the litmus re-extraction**, recorded in
  `47136f70`'s message and not acted on there. L4's program stores an
  ACK's type byte while its comment cites the PING's call site, as it
  has since M8; both callers reach the same cited lines. And the
  failure path has no guard against a second entry; M11-7 changes that
  path for a confined hart, and its section says what a second entry
  does there.

## M11-7: step 1, the VS-domain harts confined

### Outcome first

M11-7's required result (the plan's work-package table) holds at exact
commit `e87e84de`, the last of its nine commits:

- every scenario passes with the boundary on, with D-10's four checks:
  `check` runs 95 QEMU runs, 63 of them under the boundary, each of
  those judged by the capture checker, the oracle, and
  `tests/check-boundary.py`; the six typed sessions and the U-Boot
  rehearsal's seven cases run under it too;
- every hostile-monitor image passes: on each VS-domain hart, HS-mode
  code makes 112 attempts on what lies outside the hart's profile, and
  each ends as it declares (76 denied with an access fault, 30 calls
  refused, one instruction illegal, five controls allowed); M-mode's
  counts for the hooked hart equal those sums (76 PMP faults, 30 blocked
  calls) and are zero for every other hart; and the scenario runs to
  `anchor`'s end with `anchor`'s lines and counts;
- each image's run without the boundary shows the effect of every
  attempt that has a witness (63 attempts for VS domain 0's hart, 62
  for VS domain 1's): no failed discrimination;
- the boundary's seven negatives each fail closed for their declared
  reason, on both toolchains;
- the firmware binary without the boundary extension, built for one
  negative, is identical between the host's build and the evaluator's,
  as the firmware's is (`evaluate`: 738 of 738 images identical);
- `./be model-check` passes with no file under `model/` changed.

It is emulation: nothing is proved, the attempts are a list and not
every access, and nothing here ran on a board (D-10, "What this
evidence is not"). The control hart is not confined in this step: it is
left at boot, and M11-8 confines it.

### The commits

On the working branch `m11`, unsigned, over `789a67f9` (the planning
site's entries for M12-1's page, itself over the signed `8f07d612`):

| Commit | Content |
| --- | --- |
| `bddd343f` | The harness's forms for a run under the boundary: the oracle's PMP mode, M-mode's record table, named words, and two kinds of device register; `tests/check-boundary.py`, D-10's four checks; the capture checker's boundary-on lines. Every run still off |
| `2eb0cdee` | Step 1's device trees and tables (`--control-hart boot`), and the pairing |
| `0e998df1` | The build option, off in every image; the off copies |
| `0183a338` | Step 1 for the three scenarios: the identity check, the confine stub, the confined failure path, the image checker's rules |
| `f2794a71` | The boundary on for every variant, typed session, and rehearsal case; the Smepmp runs |
| `88819537` | The hostile-monitor images, with two fixes that the first runs brought |
| `c01eb733` | The boundary's negatives, with the second firmware binary |
| `0e641b36` | The firmware's tenth patch: a commit record printed whole |
| `e87e84de` | The README's and the guide's words |

A tenth commit follows them in the same range and is not M11-7's:
`7e5071b2`, the console tool's rule for the reset dongle's firmware
1.1.1 ("The console tool", below).

Each commit's content was written by the coding delegate, sub-step by
sub-step, and reviewed line by line by the owner session before the
next was taken; the claim ledger's notes, the README, and the guide are
the owner session's. The firmware's patch was written by the tool that
its `AI-assisted-by` line names, as D-2 requires.

**Checked at each commit**, from a fresh clean clone on `l1`: the tool
lock and `./mvp/mvp check`. The checks ran at the scratch commits that
were then landed here; each landed commit's `mvp/` and `model/` trees
equal its scratch commit's.

| Commit | When (UTC) | QEMU runs (under the boundary) | Attempts, refused | The six sessions' attempts |
| --- | --- | --- | --- | --- |
| `bddd343f` | 2026-11-17, 00:11 to 00:27 (a second run; below) | 64 (0) | 81, 17 | 8 |
| `2eb0cdee` | 2026-11-16, 22:13 to 22:33 | 64 (0) | 81, 17 | 7 |
| `0e998df1` | 22:33 to 22:52 | 64 (0) | 89, 25 | 8 |
| `0183a338` | 22:52 to 23:10 | 64 (10) | 75, 11 | 7 |
| `f2794a71` | 23:10 to 23:28 | 69 (41) | 76, 7 | 6 |
| `88819537` | 23:28 to 23:49 | 81 (49) | 97, 16 | 6 |
| `c01eb733` | 23:49 to 00:10 | 95 (63) | 107, 12 | 6 |
| `7e5071b2` | 2026-11-17, 00:27 to 00:48 | 95 (63) | 101, 6 | 6 |

Every refused attempt is a run without the boundary that QEMU's
firmware booted on a VS-domain hart, repeated as since M0; a run under
the boundary cannot be refused, because its device tree fixes the boot
hart. The eighth commit was not checked from a clone of its own: the
coding delegate ran the firmware's own tests, `check`, and the loaded
batch on its content ("The firmware's tenth patch", below), and the
ninth differs from it in the README and the guide alone.

At the ninth commit's content, from a fresh clean clone (2026-11-16,
21:08 to 22:03): the tool lock; `check` (95 runs in 97 attempts, the two
refused runs boundary-off; 6 sessions); `evaluate` (738 of 738 images
identical; both firmware binaries among them); the U-Boot rehearsal (7
cases, one attempt each); the kernel's second build (23 outputs
identical); `./be model-check`; and the model's evaluator. The
text-level checks pass on the range.

### What a run under the boundary shows

The `k3-like` run of `two-guests` (GCC), as an example of the 63:

- OpenSBI's banner lists five OpenSBI domains (`root`, `be_boot`,
  `be_g0`, `be_g1`, `be_park`) and the line `Domain commit digest`, the
  partition identity from the device tree;
- `BE_MVP:02 FIRMWARE_PROBED hsm=1 ipi=1 boundary=1 status=1:1,2:1
  started=none identity=<that digest>`: hart 0 read the identity through
  the boundary extension and compared it with the image's own;
- each `BE_MVP:08 HART_STARTED` has no HSM status: hart 0 starts the
  hart at the confine stub and asks nothing more of the firmware about
  it;
- after `BE_MVP:14 SHUTDOWN` the firmware prints each hart's commit
  record: hart 0 `committed=0`; harts 1 and 2 `committed=1`, with
  `menvcfg`, `mseccfg`, and sixteen PMP entries; harts 3 to 7
  `committed=0`; every count zero;
- the oracle's read of the stopped machine gives the same tables, and
  `check-boundary.py` prints `BE_MVP_BOUNDARY: PASS … control_hart=boot
  harts=0:boot,1:confined,2:confined,3-7:never-started`.

Under Smepmp (seven runs: the three scenarios with GCC, and the four
breach rows), `mseccfg` reads `0x5` on every hart that M-mode confined
and 0 on the others.

### The hostile-monitor images

`anchor`'s `breach-g0` (hart 1, VS domain 0) and `breach-g1` (hart 2,
VS domain 1). Twelve runs: each image under plain PMP and under Smepmp,
with both toolchains, and each image's copy without the boundary.

| Attempts | For each hart | Declared, and shown under the boundary |
| --- | --- | --- |
| Loads, stores, and jumps on forbidden memory and devices; accesses across an extent's edge and misaligned ones; accesses through an HS-mode page table, a forged `hgatp`, and tables in forbidden memory; an atomic operation, a load-reserved and store-conditional pair, and the cache-block zero | 76 | An access fault of the access's own kind, recorded by the hook with its address; every witness word unchanged; M-mode counts 76 PMP faults |
| The cache-block invalidate on a block that the hart may only read | 1 | An illegal-instruction fault; no count |
| Firmware calls: `confine` again, hart start, stop, and suspend of every hart, and a call of each family that the build keeps | 30 | The call's error, with nothing changed; M-mode counts 30 blocked calls |
| Controls inside the profile: a load, a store, a hypervisor load through its own G-stage, a cache-block zero, and a load-reserved and store-conditional pair | 5 | Each succeeds |

The oracle reads 48 words of memory and two device registers (the
UART's scratch register and one source configuration of the supervisor
APLIC) with the machine stopped: under the boundary the 38 witnesses of
forbidden attempts are unchanged and both registers read 0.

**Discrimination.** The copies without the boundary make only the
attempts that have a witness, 63 for VS domain 0's hart and 62 for VS
domain 1's, and every one takes effect: stop 15 is not reached. Not
discriminated, by attempt, as D-10 foresees:

| Attempts | Rows | Why |
| --- | --- | --- |
| The jumps | A3, B4, C5, C7, G5, H10, I8, J3; for VS domain 1 also B3 | No witness: a jump that was allowed would run what it reached |
| The cache-block invalidate | H5 | No effect on memory to witness: QEMU has no cache |
| Another hart's interrupt file; the power device | I5, I6; I7 | They leave nothing that a read can show, or end the run |
| M-mode's memory, the timer, and the M-level interrupt controller | J1, J2, J4 to J8 | The firmware denies them in both builds |
| The calls | M1 to M30 | Each kept call's own working is shown by every run |

### The boundary's negatives

Runs of `two-guests`' own image, built with the boundary, on both
toolchains (D-10's table, in its order):

| Negative | What the run shows |
| --- | --- |
| `boundary-absent`: a firmware without the boundary extension | The probe finds no extension; `FAIL boundary` before any hart starts |
| `boundary-no-identity`, `boundary-identity`: a device tree with no identity, or with another image's | `FAIL boundary` at the identity check, before any hart starts |
| `boundary-two-narrow`, `-wrong-boot`, `-no-list`: a hart in two narrow OpenSBI domains, another boot hart, no call list | The guard refuses `confine`; both VS-domain harts park in the stub, left at boot; `FAIL hart-ready`; no guest is entered |
| `boundary-no-window`: a profile without its VS domain's window | The guest's first fetch faults; `FAIL access-fault`; M-mode counts one PMP fault, on that hart |
| `boundary-no-cold-boot`: a device tree with no cold-boot restriction | The independent checker refuses the tree; no run boots it |

`boundary-no-identity` is one more than D-10's table has. Each changed
device tree is refused by the independent checker for the reason that
its run declares, and is admitted for that run alone:
`boundary-negatives-check` tries every tree against every run (7 trees,
8 runs, 6 admitted).

### The firmware's tenth patch

A defect of the firmware additions (M11-6), found by M11-7's loaded
runs and fixed by a tenth patch of the series (`0e641b36`).

At a system reset the firmware prints each hart's commit record. The
report read a hart's `committed` flag twice, once for the record's
first line and once to decide whether to print the rest, with no
ordering against that hart's own `confine`. A hart that confined itself
between the two reads was printed as `committed=0` followed by the four
lines of a committed record. Only the `hart-start` negative can end a
run with a hart inside its `confine`: 1 run in 120 showed the torn
record with four suites at once, and 1 in 80 with sixteen. Both
checkers refuse that form, so such a run failed; no run passed with it.

With the patch, the seal publishes the flag after the rest of the
record, behind a write barrier, and the report reads the flag once,
behind a read barrier, and uses that value for the line and for the
test: a record is printed whole. It adds 12 lines to one file of the
additions and removes 2; patches 0001 to 0009 are byte-identical. It
was written afresh by the tool that its `AI-assisted-by` line names,
and reviewed against D-2's six rules. Both firmware pins move to the
binaries of the ten-patch series; the firmware's layout does not
change, so no PMP table entry moves.

The coding delegate's runs with the patch (2026-11-16, 20:41 to 21:05):
the firmware's own tests (41 runs, both PMP modes); `check`; and the
loaded batch three times over, 480 `hart-start` runs with sixteen
suites at once, with no torn record.

### The console tool

The range's tenth commit, `7e5071b2`, is the responsible human's
direction of 2026-11-16, `update console tool to accept latest dongle
fw`, and is recorded in the plan's decision record. It is not part of
M11-7 and authorizes no board step.

The reset dongle's firmware 1.1.1 adds three fields to its status
line, and the console tool's rule for a clean status admitted firmware
1.0's line alone, so it refused every reset. The rule now admits three
whole lines, matched by bytes: firmware 1.0's, as before, and firmware
1.1.1's in two forms, by whether the dongle senses the board's power.
Each field of the new forms is held to what the firmware's own source
can print. No variable selects or widens a form. The pinned client is
unchanged: it relays the line.

Its tests: a matcher mutation matrix (38 mutants, each killed) and five
mutants of the tool, by the coding delegate; and the board tools' dry
run's new case `dongle-firmware` (seven resets that pass, 25 lines
refused before the reset's pulse, and one after it), in `check` at the
commit (the table above).

### The proofs' records, and the CHERI variant

M11-7 is not one of D-11's points: it changes no input of a proved
leaf (`digests.py --check` passes, 13 files, with the specification's
export). Two of the functions that stage 1's readings cite gain one
call each, in the breach images alone (`be_mvp_dispatch`,
`publish_blocks`); every other image's functions are unchanged, and
`./be model-check` passes with no file under `model/` changed.

The litmus record is stale from this commit to the candidate, as the
plan's four points have it: `verify`'s first suite would stop at the
first symbol whose address moved. Of the record's 55 symbols, GCC's 28
are 18 with the same bytes, 8 that differ in addresses or PC-relative
offsets only, and 2 that differ otherwise (`be_mvp_runtime_main`,
`hart_fail`); Clang's 27 are 17, 9, and 1 (`hart_fail`). Each of the
three still holds its excerpt's lines in the same order. The record is
derived again at the candidate.

Not run for M11-7: `./mvp/mvp verify`, for that reason; and the CHERI
check, which D-11 asks for at the candidate (stop 10). M11-7 changes
harness code that the CHERI variant shares, with the boundary off
there.

### The checkpoint: the soft limits

By the plan's count from `77eabce5`, at the range's tip:

| Lane | At M11-4's point | Since | Now | Limit |
| --- | --- | --- | --- | --- |
| The firmware additions | 708 | 12 | 720 | 800 |
| The firmware's tests and build rules | 2,763 | 62 | 2,825 | 3,000 |
| The monitor | 2,978 | 2,393 | 5,371 | 8,000 |
| The descriptor's tools | 3,266 | 83 | 3,349 | 4,000 |
| The harness | 4,357 | 5,951 | 10,308 | 15,000 |

No limit is reached. Of the harness lane's lines since the point, 282
are the console tool's.

### Departures and readings for review

Each was decided by the owner session's judgement, at the design's
review or during the work; none is a stop of the plan.

- **A second firmware binary.** D-10's first negative needs "a firmware
  that reports the right SBI version and lacks the boundary extension".
  It is built from the same pinned commit, patch series, and tools, with
  the extension's one configuration line off, and pinned in the tool
  lock beside the firmware. The base's pin, the series, and the
  committed configuration do not change.
- **Step 1 is a mode of the backend and of the checker**, not a field
  of the descriptor: the descriptor's identity is the same in both
  steps. Every artifact that depends on the step names it (the tables,
  the partition record, each run's boundary record, and the attempts'
  table), and from M11-8 an image of step 2 under a step-1 tree fails
  closed.
- **The hostile-monitor images are variants of `anchor` alone**, the one
  scenario with every target class of D-10's column for a VS-domain
  hart.
- **A window's write witness** is the last word of the other guest's
  device-tree page, which nothing else uses; D-10's example is "a page
  that the variant's guest device tree reserves". The breach images'
  measured inputs then stay `anchor`'s. The image checker requires the
  word to lie past the end of the device tree's blocks.
- **`ring-full` under the boundary.** D-8 has "the control hart reports
  the failure", and D-12 "the control hart reports each failure". The
  control hart ends the run at the first failure record that it drains,
  as it always has, so the console shows one failure; the run must also
  show, by the oracle's read of each hart's own state word, that both
  VS-domain harts ended failed with the ring's class. The expectation
  admits either VS domain as the one reported: the drain's order gives
  domain 0 in every run seen (26 of 26), and the code admits domain 1.
- **`hart-start`.** The run ends while hart 1 may be inside its
  `confine`. Its declared state is "started", judged by the run's own
  lines and by M-mode's record: confined, with the confined table
  exactly, when the record says so; no comparison of its entries when
  it does not; never a printed record that claims more than the read.
- **A VS-domain hart's declared end state follows from the run's own
  lines** (its `BE_MVP:08` and `BE_MVP:09`), not from timing:
  `run-timeout`, whose budget can end before either hart reports ready,
  showed the gap.
- **Misaligned accesses (D-10's "which M-mode may emulate").** QEMU's
  `k3-like` CPU performs a misaligned access itself, so no misaligned
  trap reaches M-mode in these runs and M-mode's emulation path is not
  exercised by them; M11-6's trap-path test is that path's evidence.
  QEMU checks PMP over the whole access at its own address, and an
  access that is not wholly inside one entry fails before any byte is
  written: under the boundary neither part of a store across an
  extent's edge was written, and without it both were. The privileged
  specification allows this behaviour and the other, in which the
  access is split; the plan's first rule had assumed the split. A board
  may differ.
- **Calls from a VS-domain hart.** Its call list is empty, so every
  call is refused before any argument is read. D-10's rows for a listed
  call with a bad buffer, a wrapping length, or a zero length therefore
  belong to the control hart's list, and to M11-8.
- **The failure path's second entry** (M11-4's litmus re-extraction
  noted that the path has no guard against one). In an image built with
  the boundary, a second entry ends with the hart parked in HS mode, or
  repeating in HS mode while the fault recurs, with no firmware call, no
  guest entry, and the first failure's published record unchanged. This
  is read from the code, path by path, and the image checker's rule
  closes it: no firmware call is reachable from a VS-domain hart's
  entry or from the trap vector. No code changed for it.
- **The firmware's tenth patch** is a change to M11-6's additions, made
  under D-2's rules for every change to them. Until it, `check` could
  fail on the torn record alone, about once in fifty to a hundred
  checks, at the three commits before it.
- **The first runs under emulation were made on the coding delegate's
  tree**, between the night chain's two `verify` runs, and the fixes
  that they brought are folded into the commits that they fix. The
  checks recorded above were then made from clean clones of the
  commits.
- **The first commit's first check failed**, in a test that the commit
  does not touch (2026-11-16, 22:03 to 22:13). The board tools' dry run
  has a case, `port-open.during-saveenv`, that starts the console tool
  typing a slow `saveenv` in the background, sleeps a fixed 0.8 s, and
  then expects a reset to be refused. The machine was loaded by two
  other jobs, the tool had not begun to type after 0.8 s, and the reset
  found an idle prompt and went ahead, as the rule has it. It is read
  as a race in the test, not a defect of the tool or of the commit: the
  same check passed on a quiet machine (the table above), and the case
  passed in the other eight checks of the range. The test's race is
  fixed in a commit of its own, after this range.
- **The checks' trees.** While the checks ran, the public line gained
  commits that touch neither `mvp/` nor `model/` (M12-1's three, M11-4's
  evidence section, and Plan revision S3-E), so each landed commit's
  whole tree differs from its scratch commit's in the policy file's two
  lines and in four planning pages. No check of `./mvp/mvp check` reads
  those files; the claim ledger pins none of them.
- **Boot-only code that a confined VS-domain hart can still execute**
  (found while M11-8 was designed; a residual of M11-3's layout, in
  force since this step). D-4's rule 1 puts boot-only code in extents
  that no profile names, and D-5 gives a confined hart none of it. The
  layout groups code by object file, and five small functions that only
  boot code calls lie in the VS-domain harts' extents: the ring's
  `be_mvp_ring_reset` and `be_mvp_ring_init` in the shared text, and
  `be_mvp_entry_frame`, `be_mvp_hsm_census_init`, and
  `be_mvp_hsm_census_add` in the VS-domain harts' text (with Clang, an
  out-of-line copy of `be_mvp_hgatp` too). Each computes on memory that
  its caller gives it and makes no firmware call, so a confined hart
  that ran one would reach nothing outside its profile; the hostile
  images' attempts on the boot-only extents are denied as declared.
  D-4 says of each function's need that it "is reviewed, not checked".
  M11-8 moves these functions to the boot-only text and makes the rule
  a check of the image checker's, for every role; its first sub-step
  confirms this list by the checker's own reach.

## M11-8: step 2, the control hart confined

### Outcome first

M11-8's required result (the plan's work-package table: as M11-7's,
"for all three harts and all eight") holds at exact commit `77666b8b`,
the sixth of the range's nine commits:

- every scenario passes with the boundary on in step 2, with D-10's
  four checks: `check` runs 111 QEMU runs, 77 of them under the
  boundary, each of those judged by the capture checker, the oracle,
  and `tests/check-boundary.py`. Wherever a run gets past both hart
  starts, hart 0 calls `confine` for itself, and where M-mode does not
  refuse it (four negatives are built so that it does) hart 0 is
  confined as harts 1 and 2 are: its PMP entries, as the oracle reads
  them from the stopped machine and as M-mode prints them, equal the
  tables of its own OpenSBI domain, `be_control`. The six typed
  sessions and the U-Boot rehearsal's seven cases run under step-2
  device trees too;
- the hostile-monitor image for the control hart passes: after its
  confinement, HS-mode code on hart 0 makes 132 attempts on what lies
  outside its profile and its call list, and each ends as it declares
  (88 denied with an access fault, 2 instructions illegal, 28 calls
  refused, 7 listed calls rejected, 2 console writes of no byte, 5
  controls allowed); M-mode's counts for hart 0 equal those sums (88
  PMP faults, 28 blocked calls, 7 failed calls) and are zero for every
  other hart; and the scenario runs to `anchor`'s end with `anchor`'s
  lines and counts;
- that image's run without the boundary shows the effect of each of
  the 73 attempts that have a witness: no failed discrimination;
- the parked harts' tests (D-9's row): the start and the status of
  each of the eight harts, stop, and suspend are now refused from
  every confined role, the control hart's among them, and in every run
  under the boundary the oracle's read shows harts 3 to 7 never
  started, with no PMP entry and no commit;
- the control hart's five negatives each fail closed for their
  declared reason, on both toolchains; with M11-7's seven, twelve;
- `evaluate`: 801 of 801 images identical between the host's build and
  the evaluator's;
- `./be model-check` passes with no file under `model/` changed.

With this step every hart that the monitor uses is confined to its
physical access profile before it takes its first input from another
hart's VS domain (D-6; Revision 4's I26).

It is emulation: nothing is proved, the attempts are a list and not
every access, and nothing here ran on a board (D-10, "What this
evidence is not").

### The commits

On the working branch `m11`, unsigned, over `1023f3ec` (M11-7's
evidence section, the tip of M11-7's range, unsigned too):

| Commit | Content |
| --- | --- |
| `668883af` | Not M11-8's: the board tools' dry run no longer races its own tools ("The dry run's race", below) |
| `2235f642` | Each role's extents hold what that role reaches: the linker script's lists by exact name, and the image checker's rules C8 to C10 |
| `26e5551f` | The harness reads the boundary's step from each run's declaration. The build still names step 1 |
| `3ab26bc7` | Step 2: hart 0's own `confine`, its confined entry, and the image checker's rules C1 to C7, C13, and C14 |
| `27eab153` | The control hart's five negatives |
| `77666b8b` | The hostile-monitor image for the control hart, `breach-c`, and its copy without the boundary |
| `cdd47511` | The README's and the guide's words |
| `46ffa531` | Sixteen comments and opening texts that the boundary's steps left untrue. No code changes ("The sweep of comments", below) |
| `5a8db9ba` | Not M11-8's: the ring arm's self-test reads a dead task as dead ("The ring arm's self-test", below) |

M11-8's own content, the second to the sixth commits, was written by
the coding delegate (Claude Opus 5.5 in the GitHub Copilot CLI),
sub-step by sub-step, and reviewed line by line by the owner session,
in three parts, before the first run under emulation; the claim
ledger's notes in those commits, and the seventh commit's README and
guide, are the owner session's. The delegate then split the reviewed
tree into those five patches. The owner session checked each state of
that series against the sub-step trees that it had reviewed: the fifth
state is the reviewed tree; the fourth and the third are reviewed
sub-steps, the third with the second review's two rules; the first two
are reviewed sub-steps with the first review's fixes. Twenty lines
exist only in a middle state, each an earlier sub-step's line that a
later one extends; each was read. The first commit, the eighth
commit's texts, and the ninth commit were each written by a coding
delegate of the same tool (the eighth's by M11-9's), and each was read
line by line by the owner session, the eighth's texts each against the
code that makes it true.

**Checked at each commit**, from a fresh clean clone on `l1`: the tool
lock and `./mvp/mvp check`. The checks ran at the scratch commits that
were then landed here; each landed commit's tree equals its scratch
commit's.

| Commit | When (UTC, 2026-11-17) | QEMU runs (under the boundary) | Attempts, refused | The six sessions' attempts |
| --- | --- | --- | --- | --- |
| `668883af` | 02:12 to 02:33 | 95 (63) | 100, 5 | 6 |
| `2235f642` | 04:05 to 04:25 | 95 (63) | 102, 7 | 6 |
| `26e5551f` | 04:25 to 04:45 | 95 (63) | 106, 11 | 6 |
| `3ab26bc7` | 04:45 to 05:06 | 95 (63) | 97, 2 | 6 |
| `27eab153` | 05:06 to 05:26 | 105 (73) | 118, 13 | 6 |
| `77666b8b` | 06:27 to 06:48, its second check ("The ring arm's self-test", below) | 111 (77) | 123, 12 | 6 |
| `cdd47511` | 03:12 to 03:33, in the gates | 111 (77) | 116, 5 | 6 |
| `46ffa531` | 05:37 to 05:58, in the gates | 111 (77) | 116, 5 | 6 |
| `5a8db9ba` | 06:48 to 07:09 | 111 (77) | 128, 17 | 6 |

Every refused attempt is a run without the boundary that QEMU's
firmware booted on a VS-domain hart, repeated as since M0.

The seven gates were run twice, each time from a fresh clean clone: at
the seventh commit's content (03:12 to 04:05), and at the eighth's
(05:37 to 06:27). The ninth commit, the range's tip, changes one
verifier tool's self-test and no image: `check` at it is the table's
last row.
Both times: the tool lock; `./mvp/mvp check` (111 QEMU runs in 116
attempts, 77 under the boundary; the six sessions in six attempts);
`./mvp/mvp evaluate` (801 of 801 images identical between the host's
build and the evaluator's); the U-Boot rehearsal (7 cases);
`kernel-repro` (23 outputs identical); `./be model-check`; and the
model's evaluator.

The two builds were made in different directories. Of the 801 outputs
that `check` records, 566 are the same byte for byte in both, among
them every flat image, boot image, device tree, descriptor, firmware
binary, and guest binary. The other 235 are the monitors' ELF files
(70), whose debug information names the build's directory as the
firmware's ELF does, and the expected tables and the checker's records
(165), which bind the firmware ELF's digest or a table's. In the one
pair of ELF files that was read section by section, every loaded
section is equal and the debug strings differ in the directory's name
alone.

### What a run under step 2 shows

The `k3-like` run of `two-guests` (GCC), as an example of the 77:

- OpenSBI's banner lists six OpenSBI domains: M11-7's five (`root`,
  `be_boot`, `be_g0`, `be_g1`, `be_park`) and `be_control`, hart 0's
  own, whose call list is the console write and the shutdown (and, in
  an image whose scenario grants console input, the console read);
- `BE_MVP:02` is as in step 1: hart 0 reads the partition identity in
  boot code and compares it with the image's own;
- both `BE_MVP:08 HART_STARTED` lines have step 1's text. Hart 0 now
  prints them from its confined entry, after its own `confine`, with
  the ticks that it kept at each start; no line that the monitor prints
  differs from step 1's;
- after `BE_MVP:14 SHUTDOWN` the firmware prints each hart's commit
  record: harts 0, 1, and 2 `committed=1`, each with `menvcfg`,
  `mseccfg`, and its PMP entries; harts 3 to 7 `committed=0`; every
  count zero;
- the oracle's read of the stopped machine gives the same tables, and
  `check-boundary.py` prints `BE_MVP_BOUNDARY: PASS … control_hart=confined
  harts=0:confined,1:confined,2:confined,3-7:never-started`.

In the runs that end in hart 0's boot code (a failure before the
barrier, a refused start, or hart 0's own refused `confine`), hart 0 is
left in the boot OpenSBI domain with no commit, and the judge requires
exactly that: a declared state of hart 0 is admitted only where the
run's own lines show it.

**What crosses the move.** M-mode's move gives hart 0 fresh supervisor
registers, and the first entry is made as a hart start makes one. The
confined entry trusts no register: it forms the stack pointer from the
link, and its C side resets hart 0's HS-mode state with the trap
vector and arms the control tick again; the run's deadline holds,
because the budget is kept in hart 0's own data and the timer
comparator carries over. The comment above `be_mvp_control_confined()`
lists each register across the move. One interval has no vector of the
monitor's: from the move to that reset, an HS-mode exception would
enter the confined entry again, and the run would loop without output
until the harness's timeout failed it. Nothing in that interval can
fault unless hart 0's text or stack lies outside its profile, and the
independent checker refuses such a descriptor or tree before any run.

### The placement by role

Step 2 needs each role's extents to hold what that role reaches, and
nothing that only boot code uses (D-4's rule 1). The second commit
makes it so, and makes it checked:

- the linker script names each role's input sections exactly. Against
  M11-7's images, 57 names (GCC) and 48 (Clang) leave the roles'
  extents for the boot extents: the measurement log's functions and
  tables, the boot-time executor calls, the functions that hand
  objects to hart 0's state, and the five functions of M11-7's
  residual (`be_mvp_ring_reset`, `be_mvp_ring_init`,
  `be_mvp_entry_frame`, `be_mvp_hsm_census_init`,
  `be_mvp_hsm_census_add`). Clang no longer links a copy of
  `be_mvp_hgatp`;
- two things that the control loop reads after the barrier move into
  the control hart's constants: the target states' names, and the
  management grants (which were in the MVP boot read-only data, and
  are still measured, now in the MVP text's record of stream 0);
- the image checker's rules C8 to C10 hold for every image built with
  the boundary, each with its mutations: no pointer out of the control
  profile in the control role's constants; each object that boot code
  hands to hart 0 inside the control profile; no boot-only function or
  constant in a role's extents. A name that the lists miss falls to
  the boot extents, and the role rules then refuse the image: shown by
  removing one entry of the script at a time.

One comparison moved with it. `build_gstage()` compared each walked
`hgatp` with `be_mvp_hgatp()` of its binding; that call was Clang's
only out-of-line use of the function, in boot code. The comparison is
now in `publish_blocks()`: the `hgatp` that hart 0 publishes for each
VS-domain hart must be the walked G-stage root's, or the run fails as
class `gstage` before the barrier. Each VS-domain hart still compares
the published value with `be_mvp_hgatp()` of its binding itself.

### The hostile-monitor image for the control hart

`anchor`'s `breach-c`: the hook runs once on hart 0, after its
activation and before it reads any ring. Six runs: the image under
plain PMP and under Smepmp, and its copy without the boundary, with
both toolchains.

| Attempts | Rows | Declared, and shown under the boundary |
| --- | --- | --- |
| Loads, stores, and jumps on forbidden memory and devices: both guest windows; every declared page; the secret's source, boot-only text, constants, and data, and the staged boot image; the monitor's text, the sealed configuration, and the log, to write; the VS role's text; both G-stage pools, both VS-domain harts' published words and private state; M-mode's memory, the timer, the M-level interrupt controller, and memory that no extent names. An atomic operation, a load-reserved and store-conditional pair, and the cache-block zero on each mailbox that hart 0 may only read. An extent's edge, and misaligned accesses. Accesses through an HS-mode page table and a forged G-stage root that hart 0 can read, through each VS domain's own G-stage root, and through VS-stage tables in forbidden memory | 88 | An access fault of the access's own kind, recorded by the hook with its address; every witness word unchanged; M-mode counts 88 PMP faults |
| The cache-block invalidate on each mailbox that hart 0 may only read | 2 | An illegal-instruction fault; no count |
| Firmware calls outside `be_control`'s list, from every family that the build keeps: two Base calls; the start and the status of each of the eight harts, stop, and suspend; a console byte write, and the console read (not on `anchor`'s list); both reboots, and a reset type above the list's; an IPI; `confine` again, and the identity read | 28 | The call's error, with nothing changed; M-mode counts 28 blocked calls |
| The console write, which is on the list, with a buffer that hart 0 may not read and write (the secret page, a guest window, the sealed configuration, M-mode's memory, past its data's end), with a wrapping length, and with a non-zero upper address word | 7 | The firmware's error (`invalid-param`, or `failed` for the upper word); nothing written; M-mode counts 7 failed calls |
| The console write of no byte, once with the secret page as its buffer | 2 | Success; nothing written; no count |
| Controls inside the profile: a load, a store, a hypervisor load of the sealed configuration through the forged G-stage root, a cache-block zero, and a load-reserved and store-conditional pair | 5 | Each succeeds |

The oracle reads 63 words of memory and two device registers with the
machine stopped: under the boundary every witness of a forbidden
attempt is unchanged. Under Smepmp, the entry that the firmware
reserves for reaching a caller's console buffer is off at the end of
every run, the rejected writes' runs included.

**Discrimination.** The copy without the boundary makes the 73
attempts that have a witness, and every one takes effect: stop 15 is
not reached. Not discriminated, by attempt, as D-10 foresees:

| Attempts | Rows | Why |
| --- | --- | --- |
| The jumps | A3, A6, B7, C5, C7, D9, D10, H11, I8, J3 | No witness: a jump that was allowed would run what it reached |
| The cache-block invalidates | H5, H10 | No effect on memory to witness: QEMU has no cache |
| The VS-domain harts' interrupt files; the power device | I5, I6; I7 | They leave nothing that a read can show, or end the run |
| M-mode's memory, the timer, and the M-level interrupt controller | J1, J2, J4 to J8 | The firmware denies them in both builds |
| The calls | M1 to M28, R1 to R7, Z1, Z2 | Each kept call's own working is shown by every run: hart 0 prints through the console write, polls through the console read in the images that take input, and ends the run by the shutdown |

The console read's own rows (a buffer outside the profile, a wrapping
length) are not made from the monitor: `anchor`'s list does not hold
the read, so `breach-c` shows it refused, and the firmware's checks of
a listed read are shown by M11-6's firmware test `console-checks`,
which makes them from hart 0 with the read listed ("Departures",
below).

### The control hart's negatives

Runs of `two-guests`' own image, built with the boundary, on both
toolchains:

| Negative | What the run shows |
| --- | --- |
| `boundary-control-absent`: step 1's device tree, with no OpenSBI domain for hart 0 | M-mode refuses hart 0's `confine` (`-4`). Both VS-domain harts are started by then. Hart 0 prints both `BE_MVP:08` lines, `BE_MVP:DETAIL boundary=1 confine=-4`, and `FAIL boundary` from its boot code, and reads no ring. It ends in the boot OpenSBI domain, with no commit |
| `boundary-control-no-list`, `-wrong-boot`, `-two-narrow`: `be_control` without its call list, with another boot hart, or hart 0 also in a VS-domain hart's OpenSBI domain | The same |
| `boundary-control-no-mailbox`: `be_control` without the mailboxes that the VS-domain harts write | Hart 0's `confine` succeeds. Its first read of a mailbox faults, and its vector ends the run: `FAIL exception`. M-mode counts one PMP fault, on hart 0 |

Each changed device tree is refused by the independent checker for the
reason that its run declares, and is admitted for that run alone:
`boundary-negatives-check` tries every tree against every run (12
trees, 13 runs, 11 admitted). Repeated by the coding delegate, the
four refusals gave `confine=-4` and `FAIL boundary` in 168 runs of
168, and the fifth gave `FAIL exception` with one PMP fault in 22 of
22.

### The dry run's race

The range's first commit, `668883af`, is not part of M11-8. It fixes the
test whose failure M11-7's evidence records (its first commit's first
check). Three races of the board tools' dry run against its own fake
tools are closed, with no change to a tool or an image: the fake
U-Boot's slow `saveenv` is a hold that the test releases, so the case
no longer sleeps a fixed 0.8 s before a reset that must be refused;
the `reset-*` cases wait for the fake board's halt; and the fake board
writes its power-off file whole. The coding delegate showed the old
case failing 10 times of 10 beside six busy processes and the new one
passing 10 of 10 there; a console tool with the port-open rule removed
fails the new case.

### The ring arm's self-test

The range's last commit, `5a8db9ba`, is not part of M11-8 either. The
first check at the sixth commit's content failed (05:26 to 05:36), in
`verify-tools-check` and in a file that M11-8 does not change: the
self-test of `mvp/verify/tools/cbmc-ring.py` printed `FAIL a timeout
kills the command's children`, a case that M8-6 wrote. The check was
made again from a fresh clean clone and passed (06:27 to 06:48); the
failed run's logs are kept.

The child was dead. The case kills a command at its time limit and
then requires the command's child to be gone, and the arm's own code
was right: the kill reaches the child, and `execute()` returns only
when the child has closed its output. The case's reading was wrong in
two ways. It took every state of the child but `Z`, a zombie, for
running, and a task that its new parent is reaping reads `X`, dead,
for a moment before its entry goes. And it read the state twice, in
the wait's condition and again in the verdict: a first read of `Z`
ended the wait, and the second, a moment later, could find `X`.

The owner session measured that pair of reads 4 times in 1,500 kills
on `l1`, then gave the fix to a coding delegate. In the fix a task is
gone when its stat cannot be read or reads `Z` or `X` (a function of
the stat's text, with three cases on fixed texts), and the case's
verdict is the read that ended its wait. `execute()` and everything
else that the arm's runs use are unchanged byte for byte, so no
verdict, bound, solver, setting, or record changes. With the tool's
own `execute()`, 6,000 kills: the old rule failed 4 times, each on `Z`
and then `X` with the child dead, and the new rule never. The
self-test, now 36 cases, passed 200 times of 200. Each of the three
new cases fails when its rule is replaced by a wrong one (only `Z`
gone; the first `)`; an unreadable stat taken for running).

The race is as old as the case. No earlier failure of it is recorded.

### The proofs' records, and the CHERI variant

M11-8 is not one of D-11's points. It changes no input of a proved
leaf: the two units, their eleven headers, and the flags that
`mvp/verify/target-digests.txt` names are M11-7's, and the record's
check passes at the eighth commit's build (13 files). `./be
model-check` passes with no file under `model/`
changed (stage 1: 26 theorems, 100 citations read).

The litmus record stays stale until the candidate, as since M11-7.
Against M11-7's build, GCC's 28 cited symbols are 6 with the same
bytes, 21 that differ in addresses or PC-relative offsets only, and 1
that differs otherwise (`be_mvp_runtime_main`); Clang's 27 are 9, 14,
and 4 (`publish_blocks`, `domain_failed`, `drain`, `poll_input`).
Clang's last three differ only in offsets into hart 0's data, where
objects moved. The other two hold the first test's publication
sequence, and changed by design: the hart starts left GCC's
`be_mvp_runtime_main` for `start_harts()`, and the comparison that
moved into `publish_blocks()` adds one load pair and one branch between
the block's fill and the fence. No store, call, or fence was added
there, and the fence and the two generation-word stores follow in the
same order. The coding delegate's report lists the instructions for
the candidate's re-derivation, which is made by extraction and
reading.

Not run for M11-8: `./mvp/mvp verify`, for that reason; and the CHERI
check, which D-11 asks for at the candidate (stop 10).

### The checkpoint: the soft limits

By the plan's count from `77eabce5`, at the range's tip:

| Lane | At M11-7's tip | Since | Now | Limit |
| --- | --- | --- | --- | --- |
| The firmware additions | 720 | 0 | 720 | 800 |
| The firmware's tests and build rules | 2,825 | 0 | 2,825 | 3,000 |
| The monitor | 5,371 | 1,535 | 6,906 | 8,000 |
| The descriptor's tools | 3,349 | 24 | 3,373 | 4,000 |
| The harness | 10,308 | 1,252 | 11,560 | 15,000 |

No limit is reached. Of the harness lane's lines since M11-7's tip, 73
are the race fix's, 8 the sweep's, and 36 the self-test fix's. The
monitor lane counts the image checker, which has most of this step's
lines; 49 of them are the sweep's comments.

### Departures and readings for review

Each was decided by the owner session's judgement, at the design's
review or during the work; none is a stop of the plan.

- **A refused `confine` of the control hart** (D-6, "Refusal": "The
  control hart ends the run with a failure line"). The run ends in
  hart 0's boot code with both `BE_MVP:08` lines, since both starts
  succeeded, then the DETAIL with the call's error and `FAIL
  boundary`. Hart 0 reads no ring on that path and enters no control
  loop. D-10's words for a refused `confine`, "no guest is entered",
  are read as of the refused hart. The VS-domain harts were started
  before hart 0's call, as D-6's order has it: each is on its way to
  its own confinement, or confined, when the run ends, and a confined
  one may have entered its guest. The judge declares them started and
  admits either state: in 167 of the delegate's 168 runs neither had
  committed at the end, and in one both had, after the firmware
  printed its records.
- **Hart 0's declared end state follows from the run's own lines**, as
  a VS-domain hart's does since M11-7: left at boot only where the run
  fails before the barrier or with a failure that only boot code
  prints; confined only where the capture holds both `BE_MVP:08` lines
  and no such failure.
- **The confined entry's address is formed once in the image**, as
  data: hart 0's boot code forms the MVP region's start for its region
  check, and since M11-3 the control hart's entry slot is that
  region's first byte. D-6 has the entry named by the device tree
  alone. The image checker admits that one formation, by that
  function, and refuses a call, a jump, or any other formation.
- **No hostile-monitor image for a shell scenario.** D-10's rows for a
  listed call with a bad buffer are made from the monitor for the
  console write. For the console read they would need a breach copy of
  a shell image, run as a typed session; they are left to M11-6's
  firmware test instead, and `breach-c` shows the read refused where
  it is not granted.
- **The control hart's negatives are D-10's rows made for
  `be_control`**: the third row's three trees (`-two-narrow`,
  `-wrong-boot`, `-no-list`); the fourth row's (`-no-mailbox`: the
  extent removed is the pair of mailboxes that the VS-domain harts
  write); and one more, `boundary-control-absent`, an image of step 2
  under a step-1 tree, which M11-7's evidence said would fail closed
  from this step.
- **M11-7's negatives under step 2.** In the three whose VS-domain
  hart is refused, hart 0's own `confine` succeeds, and the run fails
  as before (`FAIL hart-ready`), now with hart 0 confined.
- **Every monitor rebuilds its own hart entry.** The confined entry is
  kept by the linker script and calls a function that only a monitor
  built with the boundary defines, so the object can no longer be
  shared with the copies built without it. M11-7's copies were checked:
  none linked the confine stub.
- **The image checker's rule C10 has a stated limit.** A constant
  without a symbol of its own (a merged string) is taken to run on to
  the next symbol, so a boot-only string that follows one of a role's
  is not refused. No such string lies in a role's constants in the
  eight images that were read. And what no role reaches is not
  refused: `be_mvp_arch_inject` stays in the VS role's text in
  `two-guests`, which never calls it, as before this step.
- **One sentence of M11-7's ledger notes is corrected** (the fifth
  commit). C-52's note on `tools/gen-scenario.py` said that a boundary
  negative's run class is its image's. The class is the negative's
  own, by the place of its failure (`run_class()`): pre-measurement
  for the three that fail at `BE_MVP:02`, post-launch-failure for the
  four after the start. No claim and no check read the sentence.
- **The sweep of comments** (the eighth commit). After M11-8's commits
  were built, a reading of every comment in the MVP's code against what
  M11-8 changed found ten that it had left untrue, and six older ones
  on the way (three since M11-3, one since M11-6, two since M11-7):
  among them `tests/check-image.py`'s opening text, which still placed
  the grants in `.mvp.rodata` and named none of step 2's rules. The
  eighth commit makes each true. It changes no code: the four Python
  files' syntax trees are equal but for docstrings and one mutation's
  label, which nothing reads; under `src/` and in `tools.mk` only
  comment lines change, and each file under `src/` keeps its number of
  lines. Two of the files are pinned by the ledger (rows C-40, C-41,
  and C-52), and each pin's note names the reading. It is in this
  range, and not in M11-9's, so that the candidate's proof records can
  name a commit of this line whose monitor sources are the
  candidate's.
- **The first runs under emulation were made on the coding delegate's
  tree**, as in M11-7 (2026-11-17, 00:49 to 01:50: `check`, the U-Boot
  rehearsal, the experiments, and `evaluate`). The checks recorded
  above were then made from clean clones of the commits.
- **One check was made twice.** The first check at the sixth commit's
  content failed in the ring arm's self-test, which that commit does
  not change. The second, from a fresh clean clone, passed, and the
  range's last commit removes the cause ("The ring arm's self-test",
  above). The failed check stopped there, before its runs under QEMU.

## M11-9: the words and the gates

### Outcome first

M11-9's required result (the plan's work-package table: "The gates pass
at one exact candidate commit. M11-E's result is presented") holds.

**The candidate is one tree, `7a826991eb80d19c03caae883c19271a52f42963`.**
It is the tree of exact commit `2fb5c69d` of the working branch, as
that commit was when the gates ran, before any sign-off. The nine gates
that the plan lists passed at it, each from a clean clone on `l1`, from
22:18Z on 2026-11-17 to 05:03Z on 2026-11-18:

- the tool lock: 33 roles, 259 packages;
- `./mvp/mvp check`: 111 QEMU runs, 77 of them under the boundary (68
  with plain PMP, 9 with Smepmp), each of those judged by the capture
  checker, the oracle, and `tests/check-boundary.py`; the firmware's
  own tests, in both PMP modes; the twelve hostile-monitor runs under
  the boundary and their six copies without it; the boundary's twelve
  negatives; and the six typed sessions;
- `./mvp/mvp evaluate`: 801 of 801 outputs identical between the
  host's build and the evaluator's, the firmware binary and the binary
  without the boundary extension among them;
- the U-Boot rehearsal, under the boundary: 7 cases;
- `kernel-repro`: 23 outputs identical;
- `./be model-check`, with no file under `model/` changed since M11-4
  (stage 1: 26 theorems, 100 citations read);
- the model's evaluator;
- the CHERI check, whole: its three parts pass (stop 10);
- `./mvp/mvp verify`, on `l1`: every suite gives the verdict and
  counts of M11-4's point. Three prover runs that are recorded as
  timeouts there ended otherwise here, and no verdict follows from
  them ("`verify` at the candidate", below).

**After the gates, one tool's self-test was changed.** The first
`check` of the result's content, with the ledger naming the candidate,
failed in the claim ledger's tool, in one case of its self-test, and
nowhere else: the case had been written for a ledger that names no
tree yet. `6c3baa4b` changes that case and one more, in the self-test
alone, before the commit that names the candidate. The candidate and
its records are unchanged. The first eight gates were then run again
at the tree of `64fa2288`, the last commit before this section's, and
pass; `verify` was not, since it reads nothing that changed ("A
self-test changed after the candidate", below).

**The claim.** `mvp/docs/claim-boundary.md` holds the plan's clause for
a candidate in which all three of the monitor's harts are confined, and
its limit, word for word. Since `e0a98f8b` the page and the
claim ledger's second set name the candidate's tree, and each of the
set's seven claim rows cites the gates' record. The ledger's check
passes with 17 checks: nine of the release's ten, whose rows are
unchanged, and the set's eight. The tenth, the release's check of its
commits, is skipped on this line, as it has been since the release.

**The words** that the work package names are written: the guide's
section 10, the AI-assistance disclosure's section 9, the glossary's
three rows, and the hardware roadmap's bullet.

M11-E's result is presented with this section: the result commit is
the one that adds it, the last of the range. On this line the
responsible human's sign-off of that commit is his decision on it.

It is emulation: nothing is proved, the attempts are a list and not
every access, and nothing here ran on a board (D-10, "What this
evidence is not"). MVP 1.0's images, its claim, and its tag are not
changed.

### The commits

**The first part**, six commits, signed off by the responsible human
and on `main` since 2026-11-17, with M11-7's and M11-8's ranges:

| Commit | Content |
| --- | --- |
| `1ffc5e20` | The record tool can name a candidate's record: `tools/rc-record.py --kind candidate` |
| `cdf73bdc` | The claim's page, the ledger's second set, and the ledger tool's eight checks of it |
| `4500691e` | The guide's section 10, the disclosure's section 9, and the README's bullet and rows |
| `b20c5e6a` | The glossary's three rows and the hardware roadmap's bullet |
| `a176be83` | The CHERI variant's checks follow M11's changes ("The CHERI variant's checks", below); the README's open items 131 and 132 |
| `d6a1aa02` | The CHERI platform page follows the check |

The three ranges, 28 commits, were signed together, on the `main` on
which that sign-off had first been tried on a copy. Each signed commit
holds its reviewed commit's change and message, compared pair by
pair, and gains only his line.

**The candidate's range**, unsigned, on the working branch `m11` over
`d6a1aa02`:

| Commit | Content |
| --- | --- |
| `a566d5a9` | The README's open item 133: `verify` cannot start from an empty cache ("The verifier's closure", below) |
| `96ea7452` | Not M11's: the planning site's entries for two pages of M12, which that lane's pages were waiting for |
| `2fb5c69d` | The proofs' records at the candidate: the target digests and the litmus record. **The candidate** |
| `fd7b0cf2` | The three records of the gates, under `mvp/results/`, with a page beside two of them |
| `6c3baa4b` | The ledger tool's self-test: two of the second set's cases hold once the set names its tree ("A self-test changed after the candidate", below) |
| `e0a98f8b` | The candidate named: the ledger's set and the claim's page name its tree, each claim row cites the gates' record, and the CHERI platform page names that record; the README's open items 134 and 135 |
| `64fa2288` | The root README's note on `main` names M11 |
| This section's commit | This section |

The record tool's option and the ledger's tool were written by a
coding delegate (Claude Opus 5.5 in the GitHub Copilot CLI), the
change to the ledger tool's self-test by another, and the CHERI
variant's checks by two more of the same tool; each was read line by
line by the owner session. The litmus excerpts were found
again by a sub-agent of the same tool and read line by line. The
claim's page, the ledger's rows and notes, the guide's and the
disclosure's sections, the glossary's and the roadmap's rows, the
README's words, and this record are the owner session's. The records
under `mvp/results/` are the tools' output, with a page beside two of
them.

**Checked at each commit of the first part**, on `l1`, at the scratch
commits that were then landed (each landed commit's `mvp/` and `model/`
trees are its scratch commit's):

| Commit | When (UTC, 2026-11-17) | Checked |
| --- | --- | --- |
| `1ffc5e20` | 07:10 to 07:31 | The tool lock and `check`, from a fresh clean clone: 111 QEMU runs (77 under the boundary) in 117 attempts; the six sessions in six |
| `cdf73bdc` | 07:32 to 07:53 | The same: 111 (77) in 121 attempts; the six sessions in six; the ledger's 17 checks, and its self-test's 34 and 24 mutations |
| `4500691e` | 13:05 to 13:06 | The ledger's check, lint, the tool lock, the release's scan, and the text check of the added lines |
| `b20c5e6a`, `d6a1aa02` | 13:02 to 13:07 | The documentation's checks, the ledger's check, lint, the release's scan, and the text check of the added lines |
| `a176be83` | 13:00 to 13:22, then 13:22 to 13:46 | The tool lock and `check`, from a fresh clean clone: 111 (77) in 120 attempts; the six sessions in six. Then the CHERI check, whole, from another |

Every refused attempt is a run without the boundary that QEMU's
firmware booted on a VS-domain hart, repeated as since M0.

**Checked on the candidate's range:** the release's scan, the text
check of the added lines, lint, the tool lock, the ledger's check, and
the publication gate's audit, on `d6a1aa02..96ea7452` and on
`96ea7452..2fb5c69d`; the documentation's checks at `96ea7452`; and
the nine gates at `2fb5c69d` ("The gates at the candidate", below).

**Checked on the result's commits:** the same text-level checks on
`2fb5c69d..fd7b0cf2`, on `fd7b0cf2..6c3baa4b`, and on `6c3baa4b..64fa2288`,
the last with the documentation's checks. On the records' commit the
text check judged the two pages and the message: the records' files
hold tools' output, and were left to the scan, which reads every blob.
Then the CHERI check at `fd7b0cf2` ("The CHERI check at the
candidate", below); the tool lock and `check` at `6c3baa4b`, and the
first eight gates at `64fa2288`, each from a clean clone ("A self-test
changed after the candidate", below); and the documentation's checks
at this section's commit.

### The claim's page and the ledger's second set

The plan puts the boundary's claim on a page of its own and its rows
in the ledger as a second set, apart from the release's ("Claim
text").

- **The page**, `mvp/docs/claim-boundary.md`: two blockquotes, the
  clause and the limit, each equal to the plan's by a script's
  comparison when it was written, and held to the ledger's rows by the
  tool since.
- **The set**, the key `candidate` of `mvp/docs/claim-ledger.json`,
  rendered as `mvp/docs/claim-ledger-boundary.md`: seven claim rows,
  which are the clause cut into its parts, and eleven non-claim rows,
  which are the limit's sentences. Each claim row has the plan's
  methods and no other (host unit test, adversarial test, semantic
  checker, emulation), and its evidence: 30 entries on 18 files of the
  tree, each by its SHA-256 and each with a note, and since `e0a98f8b`
  one more entry in each row, the gates' record.
- **The tool**, `mvp/tools/claim-ledger.py`: eight checks of the set
  after the release's ten, which keep their rules and their order. The
  set names a tree and no commit, because a sign-off gives a commit
  another name and keeps its tree; the tool requires that tree to be
  the tree of a commit on the line, and a cited gates' record to name
  the same tree. Its self-test holds 24 seeded mutations of the set,
  each failing its own check alone, and 5 variants that pass. Two of
  the cases were written for a set that names no tree, and were
  changed in `6c3baa4b` ("A self-test changed after the candidate",
  below).

Each note on a gates' record says what the record holds for that part
of the clause, with its counts. Each count was computed from the
record by a script before the note was written, and the script stops
if one differs.

The release's rows are not changed by the result's commits. In the
first part and at the candidate, seven of their pins, on six changed
files, were refreshed by the plan's rule, each with a note: the image
checker's two (C-41, C-52) and the litmus files' five (C-54, C-56
twice, C-57, C-58). No row's claim, method, or non-claim changed.

### The words

- **The guide's section 10**, "The physical boundary (M11)": what the
  boundary is, part by part in the order of the build; a boot in
  order; how to build the firmware and run its tests; how to read a
  run under the boundary; the hostile-monitor images and the
  negatives; and what none of it shows. The owner session read each
  sentence against the code before it landed, and corrected five.
- **The disclosure's section 9**, "After the release: M11, the
  physical boundary": the two sessions, by their trailers; who wrote
  what; which model each part ran on, where it can be named; and what
  no AI system did.
- **The glossary** ("OpenSBI domain", "physical access profile", "PMP /
  Smepmp / ePMP") and **the hardware roadmap** ("Physical and I/O
  protection"): what the candidate does under emulation, and that
  nothing of it has run on the board.

### The CHERI variant's checks

The plan let the CHERI check fail on the working branch between
M11-2 and the candidate (D-11). Its first run on the working branch,
on the first part's content before the fifth commit (2026-11-17,
07:09Z to 07:10Z), failed at its first step. Taken step by step to
the end of its third part, it had three causes and one loss of
coverage:

- **The CHERI-aware monitor's trap vector.** M11-3 made the vector,
  which both monitors share, compare its trusted stack top with each
  private block's stack top exactly. In the CHERI-aware vector the top
  reaches the compared register by a plain move, so the image
  checker's tracker reports both comparisons, and its rule for CHERI
  images still required the `hstatus.SPV` check alone. The rule now
  requires all three, in order, with the branches' targets, and has
  fourteen mutations.
- **The off copies.** Every CHERI-aware image is built without the
  boundary, so a scenario's off copy is the same build as its image,
  and the rule that a variant differs from its reference refused it.
  Where the reference is not built with the boundary, an off copy must
  now equal it byte for byte; one mutation.
- **A pinned count.** The CHERI-aware monitor's pin of the SBI host
  test's assertions followed M11-4's change: 16,294 to 16,352.
- **The loss of coverage.** Since M11-7 the harness's `plic` rows boot
  each scenario's off copy, whose captures the CHERI rules' mutations
  do not judge: the mutations judged in the check's first part had
  fallen from 94 to 48. The check now runs the three scenarios in
  their `k3-like` rows on the same `plic` machine, and judges 94.

The check's first part also gained the five checks that M11 brought
to `make check` and that judge the CHERI variant's own build. No rule
for the RISC-V monitor's images changed: in a plain build made before
and after, the image checker's four records and all 222 flat and boot
images' digests are equal.

Two things were found on the way and left as they are, each an open
item of the README. The image checker requires less of the RISC-V
monitor's vector than of the CHERI-aware one's: the two stack tops as
branch operands, but not the compared register, the branches' senses,
their order, or their targets (item 131). And the CHERI check does not
run `ring-full-off` (item 132). No defect of the monitor is known from
either.

### The verifier's closure

A first start of `verify` in a clone with an empty package cache
stopped at the fetch (2026-11-17, 13:52Z). One of the closure's 481
packages, `openh264-2.6.0-3.fc44.x86_64`, is pinned by the bytes that
Fedora's codec repository serves; the fetch's sources do not hold
those bytes, and it refuses koji's copy by its SHA-256. The closure is
the release's, unchanged since M8, so MVP 1.0's `verify` stops the
same way from an empty cache. A directory that holds the package,
named as `MVP_RPM_CACHE`, is the remedy, and was tried the same day:
one package from the directory, 480 from the sources.

Every `verify` whose record this repository holds ran with a cache
that held the package, which the fetch admits by the same SHA-256, so
no result depends on it. The candidate's `verify`, and the early one
below, ran with the clone's two caches copied from the host's earlier
ones. The README's open item 133 has the finding and the remedy; the
fix is left for after M11.

### The candidate's proof records (D-11's fourth point)

M11-7 and M11-8 change none of the thirteen files that the two
leaves pin, but they change both monitors, so the litmus record's
cited sequences moved. The candidate is D-11's fourth point, and both
records were written again in `2fb5c69d`:

- **They name a signed commit.** Both are written at `d6a1aa02`, the
  signed tip of the first part, whose `mvp/src`, `mvp/Makefile`, and
  the other inputs that the litmus record binds equal the candidate's.
  The records that they replace named `c6334708`, the commit of
  M11-4's point as it was before its sign-off, which this repository
  does not hold.
- `mvp/verify/target-digests.txt`: the target commit alone. The
  thirteen digests, the flags, and the pins are unchanged.
- **The litmus record.** The 55 excerpts were found again by role in
  the candidate's monitors, which are built with the boundary. Of
  their 206 lines, 100 keep their encoding (13 of them at the same
  address), and 106 are the same instruction to the same function or
  fence with a new PC-relative offset; none has a new register or
  offset, and none was lost. Of the 55 symbols' digests, 40 changed.
  The five tests' initial states, programs, and conditions are
  byte-identical; only the addresses and digests in their comments
  changed.
- **What changed around the cited sequences** is what M11-7 and M11-8
  designed: the hart starts moved out of GCC's `be_mvp_runtime_main`,
  and one comparison (a load pair and a branch) came between the
  block's fill and the fence in `publish_blocks`. No store, call, or
  fence was added there. The calls of the ring's functions, the
  fences, and the posts were listed for each calling function, for the
  three scenarios and both toolchains, at the base and at the
  candidate: no difference.
- The claim ledger's five pins on the litmus files, each with a note.

Two readings of the re-extraction are recorded in that commit's
message and not acted on. Since M11-7 and M11-8, hart 0 reads the
rings only after its own confinement, and a VS-domain hart enters its
main function only when confined; neither changes a cited sequence.
And L4's pattern is reached in the monitor, but its full inbound ring
is not, before these changes or after them: the test's wording is as
it has been since M8.

### The gates at the candidate

Each gate ran from a clean clone of `2fb5c69d` on `l1`, one at a
time, with nothing else heavy on the host. The first seven and
`verify` shared one clone, and the CHERI check had its own.

| Gate | When (UTC) | Result |
| --- | --- | --- |
| The tool lock | 2026-11-17, 22:18 | 33 roles, 259 packages |
| `./mvp/mvp check` | 22:18 to 22:39 | 111 QEMU runs in 125 attempts; the six sessions in six; the ledger's 17 checks |
| `./mvp/mvp evaluate` | 22:39 to 22:59 | 801 of 801 outputs identical; evaluator image `87263109e660-009c2eba5655` |
| The U-Boot rehearsal | 22:59 to 23:03 | 7 cases in 7 attempts, each under its scenario's step-2 device tree |
| `kernel-repro` | 23:03 | 23 outputs identical |
| `./be model-check` | 23:03 to 23:06 | Stage 1: 26 theorems, 100 citations; the differential check: 4 instances, 91 mutations |
| The model's evaluator | 23:06 to 23:08 | Passes |
| The CHERI check | 23:08 to 23:32 | Passes: its three parts ("The CHERI check at the candidate", below) |
| `./mvp/mvp verify` | 23:32 to 05:03 on 2026-11-18 | Every suite's verdict and counts as at M11-4's point; 19,847 s |

**`check` at the candidate**, in more detail:

- 111 QEMU runs in 125 attempts. The 14 refused attempts are runs
  without the boundary that QEMU's firmware booted on a VS-domain
  hart, repeated. No run under the boundary was refused: such an image
  boots on hart 0 alone, and its device tree says so.
- 77 runs under the boundary, each judged PASS by the boundary's
  judge. In 41 of them all three harts are judged confined (32 with
  plain PMP, 9 with Smepmp). The other 36 are negatives whose declared
  failure comes before that, or may: each is judged with every hart in
  the state that its declaration and its capture give, and in 16 of
  them boot code fails closed before any hart starts. In all 77, harts
  3 to 7 are read as never started.
- The hostile-monitor images: twelve runs under the boundary (three
  images, both toolchains, plain PMP and Smepmp), each with M11-7's
  and M11-8's rows and counts (112 attempts for a VS-domain hart, 132
  for the control hart; M-mode's counts 76, 30, 0 and 88, 28, 7), and
  six runs without it (63, 62, and 73 rows, each allowed).
- The boundary's negatives: `trees=12 runs=13 admitted=11`.
- The firmware's own tests: 41 runs of their rows, in both PMP modes,
  and the host test of the series' two decisions (14,455 checks).
- The image checker's mutations: 159, 163, and 174. The capture
  checker: 325 self-test cases and 494 mutations.
- Its evidence bundle: 1,115 files; 801 outputs by digest.

### `verify` at the candidate

`verify` ran on `l1` from 23:32Z on 2026-11-17 to 05:03Z on
2026-11-18 (19,847 s). Every suite's line gives the verdict and counts
of M11-4's point, D-11's third: the WP arm 130 of 134 goals in one
round, with 18 of the 24 mutants killed; CN 5 of 55; Leaf A's bounded
check successful, 336 properties; the ring's bounded check 13,547 of
14,931 properties; the five litmus tests Never; and the token gate on
the same 686 tokens. Against that point's record, 27 of the 32 record
files are equal once run metadata is set aside (12 byte for byte). The
other five, read run by run:

- the litmus record's digest and the five tests' digests, written
  again at the candidate (above). Each test's result and its states
  are that point's;
- three runs of the WP arm's prover, each recorded as a timeout at
  that point, at the 120 s limit, and otherwise here:
  - one goal of the qualification's `wrong-implementation` case is
    recorded as a failure of the prover. The case must be unproved,
    and is, either way;
  - mutant m16, killed in both runs by the same goals: for one of
    them the prover's run is recorded as a failure;
  - mutant m17, killed in both runs: by two goals at the limit there,
    and by one here. The other is proved here, in 24 s, as it was at
    the base on `l1`;
- the near-limit list, by the two mutants' runs: of 4,419 runs, none
  near its limit and 263 over it (265 at that point).

No verdict changed, and no suite's count. The proof attempt's own
rounds hold the same timeouts as at that point, and no failure. Three
runs that had ended at their time limit ended otherwise, and the
near-limit list's count follows two of them. By the plan's rule for
D-11's points, a count that changes only because a run crossed its
limit is recorded as that and goes to the responsible human under stop
9 with that reading: it is put to him with this section, as M11-4's
was. The two failures are read with it: the record says that the
prover failed where it had run out of time, on goals that are
unproved either way.

Both leaves' code is that point's: the thirteen files that the target
digests name are unchanged. The early run on the content before its
sign-off ("The early runs", below) gave that point's record in all of
these: the same three runs were timeouts there.

### The CHERI check at the candidate

The check ran in a clean clone of its own, with the CHERI stack of the
CHERI research repository, by path (1,454 s):

1. **The CHERI-aware monitor with the CHERI Linux guests:** the 24
   checks of `make check` that the variant runs; the guests' build
   against its pins, and the firmware's pin; 56 QEMU runs in 63
   attempts; the CHERI rules' 94 capture mutations, each rejected; and
   six sessions in six attempts. The image checker's mutations for
   these images: 178, 182, and 192.
2. **The plain variant:** its 222 boot images equal, byte for byte, a
   second build of the same commit in another directory, which is the
   check's reference on the development line.
3. **The CHERI-aware monitor with the Linux guests:** the image check;
   50 QEMU runs in 60 attempts; ten capture mutations; and six
   sessions in seven attempts.

**The guard's record** (the plan's table of changed decisions: "The
candidate's plain images are new. The guard's record is derived again
at the candidate"). The record is the gates' record at the candidate,
`mvp/results/20261118-m11-candidate/`: its `host/images.sha256` holds
the digests of the 222 images among its 801 outputs, from the build
that `check` made in another clone, and they equal the 222 digests of
the CHERI check's own build. The guard takes the record where the
candidate's commit is present: the CHERI check ran again, whole, at
`fd7b0cf2`, from a clean clone that held that commit (2026-11-18,
05:10Z to 05:35Z). It passed its three parts, and its second part
reported `records=20261118-m11-candidate:222`. A clone of this
repository will not hold the candidate's commit after the sign-off,
and there the guard compares no record (the README's open item 134).
Nor does it from `6c3baa4b` on, in any clone: that commit changes the
ledger's tool, and the guard counts every file outside the
documentation and the records as a build input.

### A self-test changed after the candidate

The result's commits were first made without `6c3baa4b`: the records,
then the candidate named, then the README's note. `check` on that
content, from a clean clone (2026-11-18, 05:36Z to 05:57Z), failed at
its last step, the claim ledger's. Its 111 runs under QEMU and its
six sessions had passed. The ledger tool's self-test, which that step
runs first, failed in one case of its 71; the ledger's own 17 checks,
which follow it, had passed on the same content in the text-level
checks.

- **The case**, "a named tree that the page does not name", put
  another tree in a copy of the ledger and required the page's check
  alone to fail. With each claim row citing the gates' record, the
  evidence check failed as well: the record names the candidate's
  tree, and not the other. The case was written in the first part,
  for a set that names no tree and cites no record, and the self-test
  runs its cases on the set as the tree holds it. So the candidate's
  gates ran it on such a set, where it passes, and it first met a
  named tree in the result's own content.
- **A second case**, "a cited record while the set names no tree",
  left the set's tree as it found it. Once the set named a tree, the
  case failed the evidence check as before, but because the cited
  record names another tree, and no longer by the rule in its name.
- **The change**, `6c3baa4b`. The first case keeps a tree that the set
  names, gives a set that names none the tree of the commit that is
  checked out, and changes its copy of the page wherever the page
  names the set's tree. The second sets the tree to none. It is 17
  lines added and 5 removed, in the function that lists the second
  set's cases. No check's rule changed, and no other case; the
  self-test's counts are the same. A coding delegate wrote it to the
  owner session's design, and the owner session read each line. The
  delegate showed, and the owner session ran again, that the
  self-test passes on the set without a tree and on the set with one;
  and that on the set with a tree, with either rule switched off in a
  scratch copy of the tool, the self-test fails on that rule's case
  alone. The delegate also showed the same on the set without a tree;
  the self-test passing in a copy of each without a repository; and
  each of the two cases failing by the finding in its name.
- **Its place in the range**: after the records' commit and before
  the one that names the candidate, so that `check` passes at each
  commit. At `6c3baa4b`'s tree, where the set names no tree, the tool
  lock and `check` pass from a clean clone (06:49Z to 07:10Z): 111
  runs under QEMU in 121 attempts, 77 of them under the boundary, and
  the six sessions in six.
- **The first eight gates again**, at `64fa2288`'s tree, where the set
  names the candidate: each passes, from clean clones (07:10Z to 08:27Z;
  the table below). The ninth, `verify`, was not run again. Between
  the candidate and `64fa2288` these files differ: the ledger's tool;
  the three records; the ledger, its second table, and the claim's
  page under `mvp/docs/`; the two READMEs; and the CHERI platform
  page. `verify` reads none of them, and the thirteen files that the
  target digests name are the candidate's.
- **What it leaves.** The candidate is the tree at which the nine
  gates passed, and the tool at the result differs from the
  candidate's in those lines of its self-test. The self-test still
  compares which checks fail and not their findings, and runs on one
  state of the set at each commit (the README's open item 135).
- **How it was missed.** While the candidate's `verify` ran, the owner
  session tried the result's commits on the earlier driver run's
  record (the departures, below). That trial ran the ledger's check,
  and not `check` whole, which runs the self-test first.

The clean clones for these runs were of scratch commits that differ
from `6c3baa4b` and `64fa2288` in the commits' messages alone: each has
its commit's tree.

| Gate, at `64fa2288`'s tree | When (UTC, 2026-11-18) | Result |
| --- | --- | --- |
| The tool lock | 07:10 | 33 roles, 259 packages |
| `./mvp/mvp check` | 07:10 to 07:32 | 111 QEMU runs in 115 attempts, 77 of them under the boundary; the six sessions in six; the ledger tool's self-test and the ledger's 17 checks |
| `./mvp/mvp evaluate` | 07:32 to 07:53 | 801 of 801 outputs identical; the candidate's evaluator image |
| The U-Boot rehearsal | 07:53 to 07:57 | 7 cases in 7 attempts |
| `kernel-repro` | 07:57 | 23 outputs identical |
| `./be model-check` | 07:57 to 08:00 | Stage 1: 26 theorems, 100 citations; the differential check: 4 instances, 91 mutations |
| The model's evaluator | 08:00 to 08:02 | Passes |
| The CHERI check | 08:02 to 08:27 | Its three parts pass (1,499 s): 56 QEMU runs in 65 attempts and 50 in 56; the 94 and the 10 capture mutations rejected; the 222 plain boot images equal to a second build's, and no record compared (`records=none`) |

Of the 801 outputs of `check`'s build at that tree, made in another
directory, 566 have the digests of the candidate's record: every flat
image, boot image, device tree, descriptor, firmware binary, and
guest binary. The other 235 are the 70 ELF files of the monitors,
whose debug information names the build directory, and the 165
tables and records that bind an ELF file's digest or a table's.

### The early runs, on the content before its sign-off

Two runs were made before the candidate existed: `verify` had not run
since M11-4's point, and the driver that runs the nine gates in order
and makes their records was new. Neither is evidence for the
candidate.

- **An early `verify`** (2026-11-17, 13:59Z to 19:31Z), on the first
  part's content before its sign-off, with the records derived in
  place: every suite gave M11-4's point's verdict and counts. It took
  the place of a first run at the candidate that might have stopped.
- **The gates' driver, whole** (19:36Z to 21:52Z), on the same
  content: the first eight gates passed, and the records were made
  from them with the early `verify`'s. It showed the size of the
  gates' record, below.

### The records

All three are under `mvp/results/`, added by `fd7b0cf2`:

- **`20261118-m11-candidate/`**: the record of the first seven gates,
  made by `tools/rc-record.py --kind candidate` from the gates' clone,
  and checked by its own `--verify`: 1,209 files,
  16.1 MB. Its `rc.txt` names the candidate's commit as it was,
  `2fb5c69d`, its tree, and each gate's result line. It holds the
  evidence bundle of `check` (each attempt's capture, checker verdict,
  oracle record, and boundary judgement; the references; the
  deterministic records), the evaluator's record with its comparison
  of the 801 outputs, the rehearsal's seven cases, `kernel-repro`'s
  line, and the model's two evidence sets.
- **`20261118-verify-m11-candidate/`**: `verify`'s record, 32 files
  and a page that reads them.
- **`20261118-cheri-check-m11-candidate/`**: the CHERI check's
  summary, with the stack root's path written `<stack-root>`, and a
  page.

No file of the three holds a home path, an IP address, an ssh target,
or a serial number.

### The checkpoint: the soft limits

By the plan's count from `77eabce5`, at `64fa2288`. A Make line is
counted in the lane of what it builds, as since M11-7.

| Lane | At M11-8's tip | Since | Now | Limit |
| --- | --- | --- | --- | --- |
| The firmware additions | 720 | 0 | 720 | 800 |
| The firmware's tests and build rules | 2,825 | 0 | 2,825 | 3,000 |
| The monitor | 6,906 | 234 | 7,140 | 8,000 |
| The descriptor's tools | 3,373 | 0 | 3,373 | 4,000 |
| The harness | 11,560 | 805 | 12,365 | 15,000 |

No limit is reached. The monitor lane's lines are the image checker's
rules for the CHERI-aware vector and the off copies. The harness
lane's are the ledger tool's second set (725), the record tool's
option (48), and the CHERI check's script (29), with three more. Of
the ledger tool's lines, 12 came after the candidate: `6c3baa4b` adds 17
and removes 5 of the set's own. Nothing else after the first part
adds a counted line: the other commits change Markdown, JSON, and
records, which the rule sets apart.

### Departures and readings for review

Each was decided by the owner session's judgement. None is a stop of
the plan but the first, which stop 9 sends to the responsible human
with its reading.

- **Three prover runs of `verify` ended otherwise than at M11-4's
  point** ("`verify` at the candidate", above): one goal of a mutant
  is proved where its run had ended at the time limit, and two runs
  are recorded as failures of the prover where they had ended at the
  limit, on goals that are unproved either way. They are read as
  effects of the limits and of the host's load, and not of the code:
  no verdict and no suite's count changes, and both leaves' inputs
  are that point's. The responsible human's sign-off of the commit
  that adds this section accepts that reading.
- **A tool's self-test was changed after the candidate, and eight of
  the nine gates were run again at the result** ("A self-test changed
  after the candidate", above). The plan's result is that the gates
  pass at one exact candidate commit, and they did. The result's own
  content then failed `check`, in a self-test case that the
  candidate's gates could run only on a ledger without a named tree.
  The owner session judged a change of 17 lines to a self-test, read
  line by line and followed by the first eight gates at the result,
  to be in proportion. It judged a second candidate with all nine
  gates not to be needed, since the ninth, `verify`, reads nothing
  that changed. The responsible human may ask for that second
  candidate instead.
- **The gates' records name a commit that this line will not hold.**
  The gates ran at `2fb5c69d`, before the sign-off that gives the
  commit its name on `main`. The records say `2fb5c69d`, and its tree.
  The ledger and the claim's page name the tree alone, and the
  ledger's tool finds the commit of the line that has it. The tree
  survives a sign-off only if the range is signed on the `main` that
  it was built on, so the result's range must be signed before any
  other push to `main`; if `main` moves first, the range is rebased
  and the nine gates run again. The CHERI integration's records name
  their commit in the same way.
- **The CHERI check's guard reads a record's commit, not its tree.**
  Part 2 compares a gates' record only where the record's commit is
  present in the clone. So on `main`, after the sign-off, it compares
  the two builds alone, for this record as for the CHERI
  integration's. The README's open item 134 has it; the script is left
  as the gates ran it. From `6c3baa4b` on, the guard compares no record
  in any clone, since the ledger's tool is among the files that it
  counts.
- **The first part was signed before the candidate was cut.** The
  fifth commit changes one line of `mvp/Makefile`, which the litmus
  record binds, and the proofs' records were to name a signed commit.
  So the claim's page and the set's rows were on `main` before the
  gates' record existed: the page said so, and the set named no tree
  and cited no record until now.
- **The early runs** ("The early runs", above) were made on unsigned
  content, in scratch clones. The candidate's gates were then run
  whole, from clean clones of the candidate.
- **The gates' clones took their fetched inputs from the host**: the
  evaluator's and the verifier's package caches, the verifier's four
  source archives, the firmware base's source and the pinned Linux
  from the host's mirrors, the two userland archives with their
  signatures, and the two earlier builds that the lock pins by SHA-256
  (the earlier firmware and the rehearsal's U-Boot). Each is admitted
  by a commit or a digest that the tree holds.
- **The gates' record is larger than the earlier ones**:
  16.1 MB in 1,209 files, where the last before it, the
  CHERI integration's, has 6.0 MB in 663. It keeps every attempt's
  capture, oracle record, and judgement, and M11 has more runs and two
  more records for each.
- **A refused attempt keeps its records.** Four attempts of the
  hostile-monitor images without the boundary were refused at the
  monitor's boot check and repeated. Each one's record of the judge
  says FAIL, since the hook never ran; the attempt's verdict is
  REFUSED, and the run's is its repeat's.
- **`verify`'s summary says that the two monitors' ELF files differ
  from the litmus record's.** The record was written from another
  clone's build, and an ELF file holds its build directory's name.
  The check compares the cited sections' bytes, and passes.
- **Light work ran beside the candidate's `verify`**: the owner
  session read the gates' logs, drafted these words and the ledger's
  notes, and tried the text-level checks of the result's commits on
  the earlier driver run's record, held to four of the host's
  efficiency cores at the lowest priority. Nothing that starts QEMU or
  a container ran, and the M12 lane's heavy work was held.
- **The root README's note on `main`** said that the plain variant's
  boot images are MVP 1.0's. That stopped being true at M11-2.
  `64fa2288` makes the note name M11 and date the CHERI integration's
  statements.
- **One commit of the range is not M11's**: the planning site's
  entries for two pages of M12, which that lane's signed pages were
  waiting for.

## M11-B1 and M11-B2: the board's tools, and the M-mode addition

### Outcome first

These are the first two work packages of the
[board addendum](mvp-m11-board-addendum.md): the tools for the M11
candidate's runs on the board (M11-B1) and the one M-mode addition
(M11-B2). **No step of either has run on the board.** Everything below
is emulation, or a tool run on files.

Their exits hold at the last commit that changes a tool, which as
reviewed, unsigned, is `964696195fb0a887f004131d8d743d5a598f4bc9` (tree
`1917147b98fd882f8465cf1c4e06627ad8f5111b`). A sign-off gives each
commit of the range another name and the same change; this section
names commits by their subjects.

- M11-B1, "B-10's tests pass": each of B-10's tests that can run before
  a sitting passes ("B-10's list", below).
- M11-B2, "its two tests pass under QEMU. The build for QEMU is
  unchanged, byte for byte": the rows `k3-halt` and `k3-reset-absent`
  pass, and both pinned firmware binaries are the candidate's.

**No image of the candidate's changes.** In a clone at the path of the
candidate's gates' clone, every one of the 801 outputs that the
candidate's record lists (`mvp/results/20261118-m11-candidate/host/`
`images.sha256`) is byte for byte the same, the monitors' ELF files
among them (801 of 801 at M11-B3's gates, below; `check` makes 64
more outputs there, all under `k3/check/`).

**No input of the proofs' records changes** (stop B7): nothing under
`mvp/src`, `mvp/Makefile`, `mvp/scenarios`, `mvp/guest`,
`mvp/tools/lock`, the four tools that the records bind, or
`bringup/k3-b2`.

M11-B3's gates, at the same commit, are in the next section.

### The commits

Twenty-seven commits on the working branch, over the decision
record's two entries of 2026-11-18 and 2026-11-19, in the order in
which the five lanes depend on each other:

| Lane | Commits, by subject |
| --- | --- |
| The frame | "the frame for the board's build and its gate" |
| F, the addition | "a reset device that only halts, and the board's build"; "the test device's region only under a reset node"; "the end of a run whose machine halts"; "the board firmware's tier-1 build, and B-2's rows in QEMU"; "the sittings' two firmware forms under QEMU" |
| T, the tree | "the recipe for the board firmware's device tree"; "the board's description and hostile-monitor declarations"; "the partition backend's board platform"; "D-3's checker on the board's trees and tables"; "the generator's rules for the board's declarations"; "the bundle carries a halting run's halt record"; "the board's hostile-monitor images and their QEMU rows"; "the board gate's steps, and each image's board.json"; "evaluate runs the board gate, given the published files" |
| K, the form | "the capture checker's form for a boot from a card"; "the claim ledger's method for a diagnostic board run" |
| C, the card | "the firmware's FIT and the card's environment"; "the card image"; "the reader's tool: the dry run, the write, the read-back"; "card.mk, the gate's step, and the commands" |
| S, the sittings | "the driver of the two sittings at the board"; "the console tool types nothing while a card is in the slot"; "the reading of the NOR, and the board back on its own boot"; "a sitting's boots from a card, judged by the card-boot form"; "the record of a sitting" |
| The owner's words | "the README, the guide, and the disclosure for M11-B's tools" |

Each lane was written by a coding sub-agent on `claude-opus-5.5` in a
clone of its own, part by part; the owner session read every part line
by line and then landed it. The commit boundaries are the owner's: a
lane's small later fixes are folded into the commit that they correct,
and no commit holds another lane's file.

### The addition (B-2), and the firmware's builds (B-1)

- **The patch.** `0011` adds `CONFIG_SBI_SYSTEM_RESET_HALT` (default
  n): one reset device, at priority 1, for the shutdown type alone,
  which stops the calling hart in `sbi_hart_hang()` and touches no
  device. It is 48 lines of C. It was written afresh from the addendum
  under BSD-2-Clause, by a tool that can be named, with an
  `AI-assisted-by` line and no `Signed-off-by` (D-2, Q9).
- **The build for QEMU is unchanged.** With the option off, the
  firmware's binary and the binary without the boundary extension have
  the lock's SHA-256 (`fdab16e9…`, `f997165a…`), and both ELF files are
  byte for byte the candidate's.
- **The board's configuration** is the committed one with that one
  line more (`FIRMWARE_WITH`); Kconfig's resolution must differ from
  the committed configuration's in that setting alone. With
  `FIRMWARE_FDT` a device tree is built in, and after the build the
  binary's bytes at the tree's place are compared with the tree. Built
  twice in two directories, the binary is the same.
- **Its two tests** (B-2), on QEMU's `k3-like` machine with a tree
  that has no reset device of QEMU's: `k3-halt`, a run under the
  boundary that ends with the commit records and then the halt; and
  `k3-reset-absent`, the candidate's own binary on the same tree, which
  finds no reset device, so that the monitor's first check fails as
  declared. Three more rows go beyond B-2's two: `k3-halt-fallback`
  (QEMU's reset devices outrank the halt device), and `k3-first` and
  `k3-second`, which boot the form that each sitting's firmware has, a
  tree built in.
- **A run whose machine halts** ends when its declared last line has
  been printed and the console has been quiet for a settling time. The
  judge then requires hart 0 inside `sbi_hart_hang` and every other
  hart inside the firmware's wait, by the firmware ELF's own symbols.

### The firmware's tree (B-3)

- **The recipe** (`tools/k3-recipe.py`) on the published tree, at the
  gate: step 0 is the tree that the published U-Boot image carries for
  the board's product; steps 1 to 3 are each their input with their
  own changes alone, read back through the lock's dtc, with no new
  warning; made twice, the results are equal. In `check` the recipe
  runs on stand-ins with made-up values (77 cases, a refusal for each
  rule).
- **The board's description** (`k3/platform.json`) holds each fact
  with its source and the published tree's 69 devices with their
  kinds; the gate compares it with the tree.
- **The backend's board platform and D-3's checker**: the tree and the
  tables of each of the four images, from each image's own firmware
  build, pass the independent checker, which has the board's rules
  apart from the backend's; its mutations on the published step 3 are
  each refused by their own rule (28 at the gate, on the published
  step 3; 28 in `check`, on a stand-in, with the backend's own 20
  cases).
- **The model of the root regions** is compared with a firmware's own
  print under QEMU alone (the `k3-like` platform, in the two board
  images' runs). The board's own banner is first seen at the first
  sitting.

### The board's hostile-monitor images (B-10)

- `k3-breach-g1` and `k3-breach-c` are the candidate's `breach-g1` and
  `breach-c` with the table of attempts made from the board's
  declarations: each must equal its candidate image outside the table,
  and does (`changed=67` and `changed=69` bytes of the tables).
- The declarations pass the generator's board rules against the
  published tree's devices, and each of stop B9's mutations is
  refused: a row on a device that holds persistent state, on another
  device, in the real-time cores' memory, where nothing lies, and off
  the end of one of the five devices.
- Under QEMU, with the boundary on: `k3-breach-g1`, 112 rows, 73
  denied, 33 refused, 1 illegal instruction, 5 controls allowed;
  `k3-breach-c`, 132 rows, 85 denied, 31 refused, 7 rejected, 2
  illegal, 2 of no byte, 5 controls. M-mode's counts are the declared
  ones. Under QEMU the board's device addresses are memory outside
  every profile, so these runs test the declarations, the counts, and
  the hook, and nothing of the board's devices.

### The form for a boot from a card (B-8), and the ledger tool's method

- `tests/check-capture.py --mode card` is tested on captures built
  from parts, with made-up values and no line of a real log: three
  shapes pass (the boundary off, on, and a hostile-monitor image's),
  and a mutation of each requirement fails with its own finding and
  its stop of the addendum (`BE_MVP_K3_FORM: PASS shapes=3
  mutations=122 variants=7 inputs=32 medium=6 refusals=10 written=6`).
- It requires and refuses some lines beyond B-8's list, and reads some
  of B-8's items more strictly ("Departures", below).
- `tools/claim-ledger.py` has the rules for rows about the board, with
  no such row in the ledger: the ledger and both renderings are
  unchanged but for the pins and notes of this range.

### The card (B-4)

- The makers' self-test and the reader tool's test pass, the latter
  on a stand-in machine of regular files (206 and 194 cases).
- At the gate, each image's FIT has the structure of the published
  firmware image, and the card's environment is the published one
  with 25 variables removed by rule and 93 kept.
- **In these two packages no card was written, and the reader's tool
  did not run on a reader.** The first sitting's card is M11-B3's
  (below).

### The sittings' tools

- Both sittings run whole on stand-ins of the board, the dongle, the
  console, the workstation's USB bus, and the gate, each boot a
  capture that the card-boot form's test wrote and the form judged;
  with them, a boot that fails with each kind of stop, a boot that
  never ends, a reading that differs in each range, each typing
  command refused with a card in, and the record of each sitting.
  (`BE_MVP_K3_SESSION: PASS self_test=183 cases=27`).
- **The first sitting was rehearsed on the gate's real outputs, on
  files**, by the lane's writer, on the stack of the five lanes before
  the landing (2026-11-19, 05:48Z): the gate's record and
  `board.json`; a card image of a made-up size, written and read back
  through the reader tool's stand-in machine; a capture that the
  form's test wrote from the real `board.json`; then every step of
  the driver, through the sitting's record. Every step passed, and no
  real output differed from what a tool expects. No board, no reader,
  and no card was touched.
- **As uid 0** the dry run's two ends run the card reader's tool for
  another uid, and say so in a NOTE line: the evaluator's container is
  uid 0, and that tool refuses uid 0, as it should. A first trial of
  `evaluate` on the stack failed there (2026-11-19, 05:42Z), which is
  how this was found; the tool is unchanged.

### B-10's list

B-10 names what must pass "before any sitting, under emulation or
offline". Each item, where it runs, and what it printed at M11-B3's
gates (the next section has their times):

| B-10's item | Where | Result |
| --- | --- | --- |
| The addition's two tests | `check`: the rows `k3-halt` and `k3-reset-absent` | Both pass, each at its first attempt |
| The recipe's tests: each step's effect on the published tree, read back through the compiler | The gate: `k3-gate-recipe`, `k3-gate-platform`, `k3-gate-tree` | `PASS extract`, the description's `findings=0`, four trees, `room trees=4` |
| D-3's independent checker on each of the board's trees and expected tables, with its mutations | The gate: `k3-gate-partition` | Four images pass (three with profiles 8, 8, 9; `two-guests-off` with the boundary off); 28 mutations refused |
| The board's two hostile-monitor images under QEMU's `k3-like` machine, the boundary on | `check`: the rows `k3-breach-g1` and `k3-breach-c` | Both pass at their first attempt; each run's banner equals the backend's model of the root regions |
| The generator's refusal of a row outside the list, with one mutation for each kind of device | The gate: `k3-gate-breach`, against the published tree's 69 devices | Both declarations pass; 28 and 27 mutations refused |
| The form for a boot from a card, on synthetic captures: a passing one, and one mutation for each requirement | `check`: `k3-form-check` | Three shapes pass; 122 mutations fail, each with its own finding |
| The card's tools, on a file in place of a device, and their refusals; the read-back's refusal of a card with an old backup table or an old partition's bytes | `check`: `k3-card-check` | 206 and 194 cases |
| The first sitting's firmware build, on the host and in the evaluator, equal byte for byte | The gate on the host, and again inside `evaluate` | The next section |
| The candidate's own gates, which must still pass | M11-B3 | The next section |

### The soft limits

Counted as the addendum counts them, from M11-E's candidate; the
limits are the decision record's (2026-11-18, `limits: ok; b7: a`, and
2026-11-19, `card 11000`):

| Lane | Limit | Now |
| --- | --- | --- |
| The addition | 80 left of the firmware additions' limit | 48 |
| The addition's tests, and the board's build rules | 3,000 | 2,430 |
| The frame | 1,200 | 1,123 |
| The tree's recipe, the backend's second platform, the checker, and the declarations with the generator's rules | 2,500 | 2,387 |
| The card's tools and the session's tools, with their dry runs | 11,000 | 10,419 |
| The form for a boot from a card, the end of a halting run, and the ledger tool's method | 3,500 | 2,950 |

"Now" is one diff from the candidate to the tip, 19,309 counted lines
in 41 files, each line given to the lane of the commit that wrote it.
While they wrote, the lanes kept running counts, which count a line
again when a later part rewrote it and split one shared file
otherwise: 2,403, 1,150, 2,396, 10,543, and 2,985. Those were the
numbers held against the limits.

No limit is passed. Stop B8 fired twice while the lanes were written,
and the responsible human re-set the limits each time, before anything
of the lanes was landed; nothing was cut to meet a limit.

### The owner's own tests

On each part the owner session changed the tools one rule at a time
and ran the lane's tests. Where it kept a count, in nine parts: 141
such changes, of which 117 failed the tests at once. Of the other 24,
21 led to new test rows, and one was another form of the same code.
Two are gaps that stay: nothing shows that the banner comparison's
three mutations were made, and the console's audit after a boot's
judgement finds nothing that the dry run can make.

### Departures and readings for review

Each is the session's reading or choice, made while the lanes were
written, and each stands unless the responsible human says otherwise.

From the addendum:

1. **B-2, where the halt device lives.** It is a member of the
   firmware's static list of reset devices in the core library, built
   only with its option. A statement added to the platform's code
   would have changed the candidate's ELF, which the expected tables
   bind.
2. **B-1, where the board builds' pins live.** The three tier-1 builds
   are pinned beside the tool lock, in `k3/firmware-pins.txt`, since
   the lock is an input of the proofs' records. A sitting's firmware
   is pinned in `k3/sitting-pins.txt` in the commit that puts its
   SHA-256 into the decision record.
3. **B-2, rows beyond its two tests:** `k3-halt-fallback`, `k3-first`,
   and `k3-second`.
4. **B-10, a hart among 8 to 15.** The declarations start hart 8 and
   read its status, as B-10 has it, and also start hart 15. The three
   rows stand in the places of the candidate's two rows on the S-level
   interrupt controller, which the board's tree disables, and of its
   row on the power device, which the board lacks. Each table then
   keeps its row count, and each image differs from the candidate's in
   the table's bytes alone.
5. **B-10, what an attempt would do if the boundary failed.** Each
   declaration says it, in an entry of its own, for every row that
   writes, invalidates a cache block, jumps, or calls on one of the
   five devices or the firmware's place, for the two hart starts, and
   for the store into the memory that no extent names. A row that only
   reads has none. The generator requires the entries, and refuses one
   that names no row or a row that only reads.
6. **B-4, the card's environment.** Beyond the variables that write
   storage or firmware or download, the boot menu's and the splash's
   are removed: 25 removed in all, 93 kept. The step's expected counts
   are constants of the tool.
7. **B-8, the form.** It goes beyond B-8's list in four ways. Each
   was taken from the vendor's published sources, or from the board's
   own log of boots from the NOR.
   - *Required too:* the environment's line, loaded from the card, in
     either of the two shapes that the vendor's U-Boot prints; and the
     power chip's line, once, with a value other than the one that
     sends U-Boot into its download mode.
   - *Refused too*, a line of each of fifteen kinds: an MTD device
     removed; a failed write of the identity data; a write to a block
     device; a failure of the power chip's driver; fastboot's USB
     lines; the environment saved; the vendor's search of a card for a
     flashing table; the splash's partition lines; a network line; a
     variable not defined; an environment file loaded; one of the
     vendor's boot flows begun; the SPL's environment lines; a second
     SPL banner or firmware banner; and one more form of a partition
     table's error.
   - *Read more strictly:* the firmware banner's 35 fields, each once
     and in order, with the build's fields equal to `board.json`'s;
     B-6's thresholds as rules (at least 14 PMP entries, a grain of at
     most 12 bits, privilege version 1.12 or later); the root OpenSBI
     domain's regions text for text; each hart assigned to exactly one
     OpenSBI domain; and, with the boundary on, the commit records'
     values against the plain PMP table and the declared counts.
   - *Not read:* a hostile-monitor image's own record of its attempts
     (the decision record's erratum of 2026-11-18, `b7: a`).
8. **S3-E's item 9, a reading.** A reading types ten lines from eight
   templates: the probe, the read, the six digests, and then the read
   and the whole flash's digest again, which must be equal.
9. **M11-B6's "redacted as MVP 1.0's are".** A sitting's record is
   held to stricter rules than MVP 1.0's board records: no path of the
   workstation outside its named roots, no host name of the
   workstation, no digest of a range of the NOR, no USB ID, no
   reader's link. It holds no `images.sha256`: the inputs that the
   sitting ran on are in its plan, each by path and SHA-256.
10. **The gate makes all four images now.** The second sitting's three
    firmware builds are made again at M11-B4, with the first sitting's
    facts, as the addendum has it.
11. **The order around a sitting.** The driver takes a gate's record
    only if its commit is an ancestor of the source's commit, with
    nothing changed since but the sitting's pins, the observed facts,
    records, and planning pages. A sign-off rewrites commits, so the
    board gate is run again at the signed commit before a sitting.

From the plan and the conventions:

12. **The frame** is a lane that the addendum did not name (the
    decision record, 2026-11-18).
13. **`evaluate` gains a setting**, `MVP_K3_PUBLISHED`. Without it
    nothing of the gate runs, and the evaluator's record is as before.
14. **The halt record of a boundary-off run** is a file of its own,
    `.halt.txt`, which the bundle carries.
15. **The commits.** The lanes were written in parallel on a shared
    frame and landed in dependency order; a whole `check` was run from
    a clean clone at each lane's last commit and at the tip, not at
    every commit. Each commit passed the ledger's check and the
    fragments' own check.
16. **The scratch text check** admits one shell utility by its
    absolute path under `/usr/bin`, where the tools call it as a
    program: its name is one of the claim's forbidden phrasings, which
    is why this record does not write it.

Found, and left:

17. **`mvp/Makefile`'s comment** counts two pure decisions (the
    README's open item 136).
18. **The `shim-rule` variant's race** (the README's open item 137):
    the release's own, seen twice in a lane's whole check under load.
    Not changed.
19. **M11-B's rows run only where their expectations exist** (the
    README's open item 138).
20. **The tools' comments use working names**: the five lanes in which
    they were written, parts of a lane, and items of the lanes'
    reviews, which no public page defines; three messages of the
    sittings' driver name a lane too. The README's entry for M11-B
    under "Design" now says which lane is which, and its open item 140
    owes a sweep, in a commit of its own, before M11-B's result. It
    was found while the last lane finished, and a sweep then would
    have changed fifteen files that had passed their checks.

### What is not shown

The README's open item 139 has the list. In short: nothing of the
board; the board's description against the board; the card's tools on
a real reader (M11-B3, below, runs them on one, for the first
sitting's card); the records' values under the board's tables; the
sitting's record through its own recipe; and the board's
hostile-monitor images on the board's devices. The sittings are what
test these.

## M11-B3: the gates, and the first sitting's card

### Outcome first

M11-B3's exit is "They pass. The firmware's and the image's SHA-256
are in the decision record": B-10's list and the candidate's gates at
one commit that holds M11-B1 and M11-B2, and the first sitting's card
image, written to its card and read back.

- **The gates pass** at the commit named in the section above
  (unsigned `964696195fb0a887f004131d8d743d5a598f4bc9`, tree
  `1917147b98fd882f8465cf1c4e06627ad8f5111b`), each from a clean clone
  on `l1`, 2026-11-19, 07:22Z to 14:30Z.
- **Every image of the candidate's is unchanged**: all 801 outputs of
  the candidate's signed record, byte for byte.
- **`verify`** gives the candidate's verdict and counts in every
  suite. One prover run that ended inside its time limit in the
  candidate's run reached it in this one; the mutant that it belongs
  to is killed in both. That one count is put to the responsible
  human with its reading (the plan's stop 9; below).
- **The first sitting's firmware and card**: the build's and the
  image's SHA-256 are in the decision record and in the sitting's
  pins; the image is on the card; and the whole card, read back, is
  the image.

**Nothing here ran on the board.** The gates are emulation and tools
run on files; the card was written on the workstation.

### The gates

One after another, and until 10:12Z with nothing heavy beside them
(departure 1, below). The clone is at the path of the candidate's
gates' clone, so that every output can be compared with the
candidate's.

| Gate | UTC | Result |
| --- | --- | --- |
| The tool lock | 07:22 | `BE_MVP_LOCK: PASS roles=33` |
| `./mvp/mvp check` | 07:22 to 07:49 | `BE_MVP_CHECK: PASS`. 118 runs under QEMU in 131 attempts: 82 under the boundary, 36 with it off; the 13 other attempts were refused by `BE_MVP:02` and made again, as before. Six sessions. The bundle holds 1,180 files and 865 images |
| The board gate, on the vendor's published files | 07:50 | `BE_MVP_K3_GATE: PASS steps=9 images=38` |
| `./mvp/mvp evaluate`, with the board gate inside the evaluator | 07:50 to 08:17 | `BE_MVP_EVALUATE: PASS`. Inside: `check` passes (118 runs in 127 attempts). The host's and the evaluator's outputs are equal, 865 of 865; and the gate's, made again inside, 38 of 38 |
| The U-Boot rehearsal | 08:17 to 08:20 | `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=7 refused=0` |
| `kernel-repro` | 08:20 to 08:21 | `BE_MVP_KERNEL_REPRO: PASS outputs=23 identical` |
| `./be model-check` | 08:21 to 08:23 | Stage 1: `PASS theorems=26 assumptions_closed=26 citations=100`. `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91`. |
| The model's evaluator | 08:23 to 08:26 | `BE_EVALUATION: Model 0.2 rootless evidence PASS` |
| The CHERI check | 08:26 to 08:51 | `BE_MVP_CHERI_CHECK: PASS` (1,506 s). 56 runs in 68 attempts and six sessions on the CHERI build; 94 capture mutations, each rejected; the plain build's 222 images equal to the reference's; the regression build's 50 runs in 60 attempts and six sessions. |
| `./mvp/mvp verify` | 08:51 to 14:30 | Exit 0 after 20,382 s. Every suite's line is the candidate's, but for one count of the near-limit list: one prover run reached its time limit, where it had given up inside it. No verdict changes (below). |

**The images.** The gates' `check` bundle lists 865 outputs. The 801
that the candidate's record lists are byte for byte the candidate's;
the 64 others are M11-B's, all under `k3/check/`. Both firmware ELF
files, which no record lists, were compared with the candidate's
gates' build at the same path: equal.

Fourteen of the 64 name the commit that they were built from: the
reference manifests of M11-B's seven rows under QEMU, and the seven
files that hold their digests. At one commit they are the same on any
host (the host's and the evaluator's are equal, above). Between two
commits they differ in that one field, so a `check` at a later commit,
or at a signed one, can agree with this list in 851 outputs at most.
The bundle's own reference manifests name their commit too, but the
list does not hold them ("Found, and left", below).

**The board's firmware builds** (B-1), made at the gate on the host
and again inside the evaluator, equal byte for byte, each 540,600
bytes:

| Image | Sitting | SHA-256 of `fw_dynamic.bin` |
| --- | --- | --- |
| `two-guests-off` | first | `d2f1b1e4d8e864673ec24617abc9ca3c5a16664f38d9aa93c09ad7236478eb5e` |
| `anchor` | second | `d71737154979310c4c8d4a452cb878ff79c320a6b39c791cd668dd57a67a5309` |
| `k3-breach-g1` | second | `a91dceb4280968e077e5fd4f0fbbeada084013ffe180cc561d4e54413b497b37` |
| `k3-breach-c` | second | `7d4a9dbee8c8f2b8b9024b5fab717f2dcfcf0717c2c446b70e8bad8be35e8c4e` |

The second sitting's three are made again at M11-B4, with the first
sitting's facts; only the first is pinned now.

**`verify`.** Against the candidate's record on this host, by the
comparison that M11-E used: 32 files; 12 are equal byte for byte, 30
once run metadata is set aside, and two differ, each in one line.

- `verify.txt`: the near-limit list counts 264 runs that reached their
  limit, where the candidate's counts 263. Every other suite's line is
  the candidate's: the WP arm proves 130 of 134 goals and kills 18 of
  24 mutants; the CN arm proves 5 of 55; CBMC on Leaf A, 336 of 336
  properties; CBMC on the ring, 13,547 of 14,931.
- `leaf-a/wp/mutants.txt`: the line of mutant m16 (a constant of
  `be_mvp_denial_decide` changed from 0 to 1). It is killed in both
  runs, by the same goals. One part of one of those goals, `D_E7`,
  ended without a proof inside its 120 s in the candidate's run (the
  prover gave up; the report keeps no time for such a run), and
  reached the limit in this run. The goal's four other unproved parts
  reach the limit in both runs. The provers of that job were slower
  throughout in this run: its slowest proof took 35.7 s, where the
  candidate's took 24.7 s, and the two parts of `D_E7` that took
  14.1 s and 13.5 s there took 18.2 s and 18.9 s here.

**The reading, for the responsible human (the plan's stop 9).** No
verdict changes, and no contract or statement. One count changes, and
only because one prover run crossed its time limit: the plan has such
a count recorded as that and put to the responsible human. The host
was more loaded than at the candidate's run. Until 10:12Z these gates
ran with nothing heavy beside them. Then the responsible human asked
whether the M12 lane had to wait for these runs; the owner session
answered that it need not, and lifted the hold. That lane's image
builds ran from 10:29Z to 12:09Z, and the owner session's own setup of
a second host for development checks ran from 11:04Z to 11:08Z. Mutant
m16's job ran from about 10:45Z to 11:10Z. `verify` took 20,382 s,
against the candidate's 19,847 s. His sign-off of this section accepts
the reading, as his sign-off of M11-4's section did for the crossing
there.

### The first sitting's firmware and card

- **The firmware.** The gate's build for `two-guests-off`, the same on
  the host and inside the evaluator, is recorded in the plan's
  decision record and pinned in `mvp/k3/sitting-pins.txt` (the commit
  "the first sitting's firmware build is recorded and pinned"):
  `fw_dynamic.bin`, 540,600 bytes, SHA-256 `d2f1b1e4…eb5e`, the table
  above.
- **The card image.** Made at that commit, in the gates' clone, from
  the gate's outputs, for the card's size (14:33Z): `card.img`,
  31,927,042,048 bytes, SHA-256
  `7dcec03cad476ec301319531471ec006b98ef9f7837d0fbdf3f6825235d3c24c`.
  Its FIT (SHA-256 `c36a6582…5d9f`) and its environment (SHA-256
  `f0a14d29…3600`) are byte for byte the ones that the gate made. It
  is recorded and pinned in the next commit ("the first sitting's card
  image is recorded and pinned"), and is not committed: it holds the
  vendor's files.
- **The reader.** One USB card reader, named by its stable ID path.
  The reader tool's dry run wrote the access rule for it (QB4), and
  the responsible human installed the rule with one command (by
  09:01Z): his account may open that reader's whole-disk node, and
  nothing else changes. Until then the tool had run on no reader; its
  test uses regular files that stand for a machine.
- **The write.** A dry run through the make target passed each of the
  tool's checks on the real reader and printed the write's
  confirmation (14:35Z). With it, the tool wrote the whole card,
  14:36Z to 15:11Z: 31,927,042,048 bytes in 2,106 s (15.2 MB/s),
  the image, the zeros to the card's last blocks, and the backup
  table; flushed; the bytes that it wrote have the image's SHA-256.
- **The read-back.** The tool then read the whole card back, 15:12Z
  to 15:39Z: 31,927,042,048 bytes, whose SHA-256 is the image's, and
  each of the fourteen regions equal to the image's (the tables, the
  environment, the vendor's four files, the FIT, the gaps, the zeros,
  and the backup table). The card had not been taken out of the
  reader between the write and the read-back.
- The two records, and the reader's rule, are in the sittings' private
  area beside the working clone; a sitting's record takes the card's
  records with it (M11-B6).

So M11-B3's exit holds: the gates pass, and the firmware's and the
image's SHA-256 are in the decision record.

### What was run, and what was not

- The gates ran at the last commit that changes a tool. The two
  commits after it change the sitting's pins and the decision record,
  and the one after those changes this record alone. A whole `check`
  from a clean clone passes at the second of them, the commit of the
  card's pin (14:37Z to 15:04Z: 118 runs under QEMU in 123 attempts,
  six sessions, `BE_MVP_CHECK: PASS`).
- No record of these gates is committed: the board's result (M11-B6)
  brings the records. The logs are kept beside the working clone.
- The gates' driver is the owner's scratch script, after the
  candidate's.
- A development check, which is not a gate: on a second host (a
  virtual machine with another maker's processors), in the pinned
  evaluator image built there from Fedora's own repositories, a whole
  `check` of the gates' commit passes, and its 865 outputs are byte
  for byte this host's (11:25Z to 12:08Z).

### Departures at M11-B3

Each stands unless the responsible human says otherwise.

1. **Other work ran beside `verify`.** Until 10:12Z the gates ran
   with nothing heavy beside them, as the candidate's gates did.
   From then on the M12 lane's work could run on the host (the
   reading above says why), and did. One count of `verify` differs
   from the candidate's, and its reading is above.
2. **The card was written before the range's sign-off**, as the
   work package has it. A sign-off gives the commits other names, so
   before the first sitting the board gate is run again at the signed
   commit, and the card's image is made again there: it must have the
   pinned SHA-256, which the card was read back against.
3. **The whole `check` after the gates** is at the commit of the
   card's pin, not at the range's last commit, which changes this
   record alone.
4. **The reader tool's first dry run** was made before the card's
   image existed, from the working tree, to give the access rule for
   the responsible human to install; it reads the system's own
   description of the reader and writes nothing to it. The dry run
   that gave the write's confirmation was made after the image and
   its pin, through the make target.

Found, and left:

5. **Fourteen of M11-B's 64 listed outputs name their commit** ("The
   images", above). A comparison of two commits' lists must set them
   aside. Whether the list should hold them is settled with M11-B4's
   work, with the sweep of the working names (the section above,
   item 20).

## M11-B4, first part: the first sitting, and the corrections after it

### Outcome first

M11-B4's exit is "It passes, or stops. Its facts are in the decision
record, with each build's and each image's SHA-256. If the facts
change the board's platform description, M11-B3's gates pass again at
the commit that holds the change."

- **The first sitting stopped** at its first boot from the card
  (2026-11-20; the addendum's stop B5: no firmware banner). No line of
  the project's firmware, of U-Boot, or of the monitor reached the
  console. The NOR and the card were unchanged afterwards. Its facts
  are in the decision record. Its record is not in this range
  (departure 1).
- **The cause is established from sources, and is not shown on the
  board**: the published tree names the console `ns16550` alone, and
  for that name the firmware base clears the UART's unit enable as it
  sets its console up.
- **The facts change the platform description**: the recipe now names
  the console `intel,xscale-uart`, then `ns16550` (the erratum to B-3,
  on the responsible human's `fix: go`). So every board tree, firmware
  build, and card changes, and M11-B3's gates are run again.
- **Nine of the ten gates pass** at the commit that holds the change
  (unsigned `8af29f25ec1305e3935bdd77bec0003e159590ef`, tree
  `adb04e652800e5afa490593718eecf1bcad9c6d6`), each from a clean clone
  on `l1`, 2026-11-20, 15:49Z to 17:20Z. **The tenth, `verify`, runs
  at that commit as this section is written** (since 19:07Z); its
  result is added to this record in a commit of its own (departure
  4). None of its inputs changes in this range.
- **Every image of the candidate's is unchanged**: all 801 outputs of
  the candidate's signed record, byte for byte.
- **The first sitting's firmware and card are made again.** Their
  SHA-256 are in the decision record and the sitting's pins; the image
  is on the card; and the whole card, read back, is the image.
- **The sittings' tools are corrected** where the first sitting showed
  them wrong: the record of a sitting that stopped, the reset after a
  boot from a card that stopped, and the stop's name.

**Nothing here shows that the corrected firmware prints on the
board.** Under QEMU the firmware printed with either name, because
QEMU's UART has no unit enable. The next sitting's first boot from the
card is the first direct evidence. By the decision record's entry of
`fix: go`, that sitting is run only on the responsible human's word
and with him present, after all ten gates have passed at the commit
that holds the corrections, that commit is signed, and the card is
written and read back.

### The first sitting

The decision record's entry of 2026-11-20 has the account; this is
what the tools' records hold (05:32Z to 05:49Z, at M11-B3's signed
commit).

| Step | Result |
| --- | --- |
| `begin`, `preflight`, `stage`, `reading-0` | Each passed. The reading's boot was from the NOR; U-Boot showed 8 GiB |
| `card-in-1` | On the responsible human's word |
| `boot-1.1` | One reset by the dongle, nothing typed. The capture is 191 bytes: four lines of the boot ROM, the SPL's banner, and two lines of its own; then nothing for 120 s. The form refused it; the driver's stop was B3, where the addendum's stop for a boot with no firmware banner is B5 |
| `card-out-1` | On his word |
| `reading-1` | Stopped with no reset made: the console tool held no reason to reset a board that hangs after a card's SPL banner |
| The close | By hand, on his word, outside the driver's records: one reset by the dongle, a boot from the NOR to the board's own system, a reading of the NOR by the reader that the rehearsal used, and the preflight again |
| The card, read back | Each of its fourteen regions equal to its image |

- The closing reading by hand equals the sitting's first reading in
  all six ranges, and the preflight's verdict line after equals the
  one before.
- The boot ROM's lines hold no identifier; they are in the decision
  record's account by their count alone.

### The corrections

Each is a commit of its own, written by a coding sub-agent and read
line by line by the owner session; the last is the owner's words.

| Commit | What |
| --- | --- |
| "the record of a sitting that stopped, made at a later commit" | The record tool could not record a sitting that stopped. It now does, and admits a record made at a later commit when, under `mvp/` and `bringup/`, nothing differs from the sitting's commit but the record tool and its dry run |
| "the board tools say things in plain words" | The sweep of working names (the README's open item 140, closed): comments, eighteen messages, and names inside the sittings' dry run, in 21 files. No rule changes |
| "the recipe names the board's console as the firmware needs it" | The recipe's step 4, with six refusals, and the rule in the recipe's own check of the description |
| "the independent checker requires the console's names" | The same rule on every board tree, with three mutations |
| "QEMU's tree at tier 1 names its console as the board's" | The tier-1 tree, its tree check with two negatives, and the two tier-1 firmware pins |
| "a board that hangs in a boot from a card can be reset" | The console tool's two reasons, `card-hang` and `card-uboot-hang`, each admitted on the tool's own reading of the log and of the card's ledger, after 30 s of quiet |
| "the sittings' driver asks for a reset after a stopped boot" | The driver's flag for the closing reading and for a boot taken up again, and the dry run's sittings for each way that a boot from a card stops |
| "a refused boot's stop is named by the stage that it did not reach" | The form's stop, its facts as the capture shows them, and the claim ledger's rule for a cited record of a sitting |
| "the first sitting and its corrections in the guide and the README" | The owner's words, with the disclosure's section 11 and two new open items of the README (141, 142) |

**Tried on the first sitting's own bytes**, in private scratch: with
the corrected reader, the 191 bytes of the boot and the sitting's own
ledger give `card-hang`, so the closing reading's reset would have
been admitted and the sitting closed by the tools.

**What the corrections' tests do not show.**

- The unit enable, under QEMU: QEMU's UART keeps only the low four
  bits of its interrupt-enable register, so the five firmware rows
  look the same whichever name the firmware matched. They show that
  the firmware finds, binds, and drives its console with the new name
  first.
- How the firmware picks its console: the rules read the one node
  that the description names. A second serial node earlier in the
  tree, or a `stdout-path` that resolved elsewhere, would pass them.
  The published tree holds one serial node, and its `stdout-path`
  names an alias that the tree lacks, so the firmware scans for a
  serial node and finds that one.
- The reading of the firmware base on which every one of these rules
  rests: names in order, and the unit enable for that one name. The
  firmware project's own post about this board says the same.
- A board whose boot ROM or SPL prints lines that the reader does not
  take for a card's; and a console that drops its output for longer
  than the quiet, which the reset's argument makes harmless and
  nothing detects.
- Whether a boot of the board prints the lines that the form expects
  after the SPL's. No boot from a card has reached the firmware's
  banner; a line that the form refuses at the next sitting is a
  finding, and stops the sitting.

### The gates again

One after another, with nothing heavy beside them: the owner session
wrote records and ran one small test of its own on two cores, and the
M12 lane ran nothing. The clones are at the paths of the candidate's
gates' clones, so that every output can be compared with the
candidate's.

| Gate | UTC | Result |
| --- | --- | --- |
| The tool lock | 15:49 | `BE_MVP_LOCK: PASS roles=33` |
| `./mvp/mvp check` | 15:49 to 16:19 | `BE_MVP_CHECK: PASS`. 118 runs under QEMU in 126 attempts: 82 under the boundary, 36 with it off; the 8 other attempts were refused by `BE_MVP:02` and made again, as before. Six sessions. The bundle holds 1,152 files and 865 images |
| The board gate, on the vendor's published files | 16:19 | `BE_MVP_K3_GATE: PASS steps=9 images=38` |
| `./mvp/mvp evaluate`, with the board gate inside the evaluator | 16:19 to 16:48 | `BE_MVP_EVALUATE: PASS`. Inside: `check` passes (118 runs in 127 attempts). The host's and the evaluator's outputs are equal, 865 of 865; and the gate's, made again inside, 38 of 38 |
| The U-Boot rehearsal | 16:48 to 16:51 | `BE_MVP_UBOOT_REHEARSAL: PASS cases=7 attempts=7 refused=0` |
| `kernel-repro` | 16:51 to 16:52 | `BE_MVP_KERNEL_REPRO: PASS outputs=23 identical` |
| `./be model-check` | 16:52 to 16:54 | Stage 1: `PASS theorems=26 assumptions_closed=26 citations=100`. `BE_MODEL_DIFFERENTIAL: PASS instances=4 mutations=91` |
| The model's evaluator | 16:54 to 16:56 | `BE_EVALUATION: Model 0.2 rootless evidence PASS` |
| The CHERI check | 16:56 to 17:20 | `BE_MVP_CHERI_CHECK: PASS` (1,441 s). 56 runs in 64 attempts and six sessions on the CHERI build; 94 capture mutations, each rejected; the plain build's 222 images equal to the reference's; the regression build's 50 runs in 57 attempts and six sessions |
| `./mvp/mvp verify` | from 19:07 | Running as this section is written; its result follows in a commit of its own |

**The images.** The gates' `check` bundle lists 865 outputs. The 801
that the candidate's record lists are byte for byte the candidate's.
Of the 64 others, M11-B's, 32 are byte for byte those of M11-B3's
gates, and 32 differ, as designed:

- the 17 outputs of the tier-1 firmware rows, whose trees now name
  the console: the two sittings' firmware forms, each with its tree,
  its build, and its build's record; and the three trees without
  reset devices, each with its table and its record;
- the 14 that name the commit that they were built from;
- the card environment's report, which holds the digest of
  `tools/k3-env.sh`, whose comments the sweep changed.

**The board's firmware builds** (B-1), made at the gate on the host
and again inside the evaluator, equal byte for byte, each 540,600
bytes. All four change with the console's name:

| Image | Sitting | SHA-256 of `fw_dynamic.bin` |
| --- | --- | --- |
| `two-guests-off` | first | `d2b4af5d7e246279cbfb7c665ab48c19c440357b13462eec162232636676c9b4` |
| `anchor` | second | `a95128a2140951fdb1a442d178ebbb3ce70219c3f9f582f28a658dd09b254cb4` |
| `k3-breach-g1` | second | `0fd9b322f91ca805844ddd95d073ca6662a77b0f2ab579595efaa4a9e7a028ff` |
| `k3-breach-c` | second | `1f0ad1f9724bef6bdadab2255883bad884b1e7e9b6464b298e85994103d6794b` |

Only the first is pinned now, as before.

**`verify`'s inputs.** From M11-B3's signed commit to the gates'
commit, nothing differs under the paths that the proofs' records
bind (`mvp/src`, `mvp/Makefile`, `mvp/scenarios`, the four tools,
the tool lock, `mvp/guest`, `bringup/k3-b2`), under `mvp/verify`,
under `model`, or in the verifier's own definition and the
specification. So `verify` here is the run of M11-B3's gates again,
on the same inputs.

### The first sitting's firmware and card, made again

- **The firmware.** The gate's build for `two-guests-off`, the same
  on the host and inside the evaluator, is recorded in the plan's
  decision record and pinned in `mvp/k3/sitting-pins.txt` in place of
  the first run's (the commit "the first sitting's firmware build,
  made again, is pinned"): `fw_dynamic.bin`, 540,600 bytes, SHA-256
  `d2b4af5d…c9b4`, the table above. Its device tree's SHA-256 is
  `f07e3217…c4c1`.
- **The card image.** Made at that commit, in a copy of the gates'
  clone (departure 5), from the gate's outputs, for the card's size
  (17:22Z to 17:23Z): `card.img`, 31,927,042,048 bytes, SHA-256
  `cbc68f8c01c0389af5040fa6b56e48601539f232096b82ef994ea8effd43dc49`.
  Its FIT (541,307 bytes, SHA-256 `852b6198…602a`) and its
  environment (SHA-256 `f0a14d29…3600`, the first card's) are byte
  for byte the ones that the gate made. It is recorded and pinned in
  the next commit ("the first sitting's card image, made again, is
  pinned"), and is not committed: it holds the vendor's files.
- **The write.** The same card, in the same reader, under the access
  rule of M11-B3. A dry run through the make target passed each of
  the tool's checks on the reader and printed the write's
  confirmation (17:24Z). It is another than the first card's: the
  image is another, and the reader's disk has another sequence
  number, since the card was taken out for the sitting and put in
  again. With it, the tool wrote the whole card, 17:25Z to 18:00Z:
  31,927,042,048 bytes in 2,102 s (15.2 MB/s), the image, the zeros
  to the card's last blocks, and the backup table; flushed; the bytes
  that it wrote have the image's SHA-256.
- **The read-back.** The tool then read the whole card back, 19:08Z
  to 19:36Z: 31,927,042,048 bytes, whose SHA-256 is the image's, and
  each of the fourteen regions equal to the image's (the tables, the
  environment, the vendor's four files, the FIT, the gaps, the zeros,
  and the backup table). The card had not been taken out of the
  reader between the write and the read-back: the reader's disk has
  the write's sequence number.
- The records are in the sittings' private area beside the working
  clone.

### What was run, and what was not

- The gates ran at the last commit that changes a tool or a page
  under `mvp/`. The two commits after it change the sitting's pins
  and the decision record, and the one after those changes this
  record alone. A whole `check` from a clean clone passes at the
  second of them, the commit of the card's pin (17:24Z to 17:53Z,
  beside the card's write: 118 runs under QEMU in 129 attempts, six
  sessions, `BE_MVP_CHECK: PASS`).
- Before the gates, a whole `check` from a clean clone passed at the
  content of each commit of the corrections but two: the console
  tool's reset, whose next commit holds its dry run's sittings, and
  the last, which is the gates' own commit. The commits' messages
  give each run. One of them failed once first (departure 2).
- No record of these gates is committed: the board's result (M11-B6)
  brings the records. The logs are kept beside the working clone.
- The gates' driver is the owner's scratch script, after M11-B3's.
- The second host for development checks (M11-B3) could not be
  reached on this day, and no check ran there.

### The soft limits

Counted as the addendum counts them, from M11-E's candidate; the
limits are the decision record's, three of them re-set on 2026-11-20
(`fix: go`):

| Lane | Limit | At M11-B3 | Now |
| --- | ---: | ---: | ---: |
| The addition's tests and the board's build rules | 3,000 | 2,430 | 2,475 |
| The frame | 1,200 | 1,123 | 1,123 |
| The tree's recipe, the backend's second platform, the checker on the board's trees, and the hostile-monitor declarations | 3,000 | 2,387 | 2,487 |
| The card's tools and the session's tools, with their dry runs | 12,500 | 10,419 | 11,341 |
| The checker's form for a boot from a card, the harness's end of a halting run, and the ledger tool's method | 4,000 | 2,950 | 3,137 |

"Now" is one diff from the candidate to the last commit that changes
a tool, each line given to the lane of the commit that wrote it, and
a later commit's lines to the lane that holds most of its file. The
running counts that were held against the limits while the lanes were
written count a rewritten line again, and so count the sweep's
comments: 2,479, 1,150, 2,587, 11,785, and 3,239. No limit is passed
by either count.

### The owner's own tests

Beside each sub-agent's own tests, the owner session changed the
corrected tools one rule at a time, in scratch copies, to see that a
test fails. Where none did, a row was asked for and added.

| Tool | Seeded changes | Fail a test | The rest |
| --- | ---: | ---: | --- |
| The console tool's reader (`can-reset`) | 11 | 8 at first, 10 with two rows added | One, the account's check dropped, cannot be shown without another account |
| The driver's wiring of the flag, each through the whole dry run | 6 | 5 | The sixth fails the row that was added for it, in the sub-agent's run |
| The form's stage rule and facts | 4 | 4 | |
| The form's rule for a line of U-Boot's that is absent | 7 | 3 at first, 5 with two captures added | Two change no capture that the form admits: the autoboot line taken anywhere in the capture, and by a search within a line |

The sweep was compared with its form before by a script of the
owner's, apart from the sub-agent's: the Python files' syntax trees
but for docstrings, and the other files' lines but for comments and
the mapped names. Eleven strings in four Python files change,
sixteen lines of the dry run, and nothing else.

### Departures and readings for review

Each stands unless the responsible human says otherwise.

1. **The first sitting's record is not in this range.** The record
   tool could not record a sitting that stopped, and its correction
   has the record made at the commit that corrected it, once that
   commit is signed. The record then lands in a commit of its own,
   with its pointer in the README and the guide. Until then the
   decision record's entry is the sitting's account.
2. **A whole check failed once, in MVP 1.0's own board-tool dry run**
   (2026-11-20, 15:02Z to 15:12Z; `late-prompt.record: exit 1,
   expected 0`), at the content of the commit "a refused boot's stop
   is named by the stage that it did not reach". The owner session
   read the cause from the run's records: the dry run's stand-in for
   U-Boot prints its late prompt, writes a record of its own, and
   then echoes the console tool's second `s`; held up between the two
   for longer than the dry run's quiet of 0.05 s, it shows the tool a
   prompt with nothing after it. Three heavy runs of the owner
   session's were going at once. This range changes neither that path
   of the stand-in nor the tool's rule. Run again alone, the same
   content passed (15:17Z to 15:45Z). It is the README's open item
   142; the stand-in's correction is owed, and is not in this range.
3. **Two rehearsals, which are not gates**, at the content of the
   commit "the sittings' driver asks for a reset after a stopped
   boot": the CHERI check passed (14:35Z to 15:11Z); `evaluate` with
   the board gate showed the board-tool dry run, the form's test, and
   the sittings' dry run passing inside the evaluator, where the
   tools run as uid 0, and then stopped at the `shim-rule` variant's
   race (the README's open item 137, its signature exactly), again
   beside the owner session's other runs. The gates' own `evaluate`,
   run alone, is in the table above.
4. **`verify` runs last and apart, and this section does not wait
   for it.** The other nine gates ran first; then the pins, the
   card's write, and the whole `check` at the card's pin, so that
   nothing heavy runs beside `verify`; then `verify`, at the gates'
   commit, in the gates' clone. It was started at 19:07Z, not when
   the whole `check` ended at 17:53Z: the owner session was not
   running between 17:36Z and 19:07Z, and had not chained the two.
   The card's read-back ran beside its first half hour. Its inputs
   are those of M11-B3's gates ("`verify`'s inputs", above). Its
   result is added here in a commit of its own. The decision record
   has the sitting wait for it; a sign-off of this range before it
   ends is the responsible human's choice.
5. **The card was made in a copy of the gates' clone**, so that
   nothing is written in the clone in which `verify` runs. The copy
   holds the board gate's outputs as the gates made them; the image's
   FIT and environment are byte for byte the gate's.
6. **The card was written before the range's sign-off**, as at
   M11-B3. Before the first sitting is run again, the board gate is
   run again at the signed commit and the card's image is made again
   there: it must have the pinned SHA-256, which the card was read
   back against.
7. **The whole `check` after the gates** is at the commit of the
   card's pin, not at the range's last commit, which changes this
   record alone.
8. **The form's reading of "past its place"** (the commit "a refused
   boot's stop is named by the stage that it did not reach"): a line
   of U-Boot's that is absent names a stop of its own only where,
   after U-Boot's banner, a later line of the form's list or the
   autoboot line is in the capture. It reads what follows the banner,
   not where those lines stand.
9. **The quiet before a reset of a hung boot from a card is 30 s, and
   is not a setting of the wrapper.** A sitting run through
   `./mvp/mvp` always waits that long.
10. **The first sitting's own record will keep the stop that the
    driver named, B3**, beside the form's stops `B3,B5`: the form of
    the sitting's commit judged that boot, and judges it again where
    the record is made. The decision record says that the addendum's
    stop for it is B5.
11. **The lanes are counted two ways**, and both are given ("The soft
    limits", above).
12. **A second sub-agent finished the sittings' tools**, after the
    first stopped on a network failure, from the first's committed
    part and its written design. The disclosure's section 11 says so.
13. **The fourteen listed outputs that name their commit** (the
    section above this one, item 5) are not settled here. The sweep
    landed without them, and this range's comparisons set them aside
    as before. They stay for M11-B4's later work, with an open item
    of the README then.

### What is not shown

- That the project's firmware prints on the board's console, or boots
  at all. The first sitting stopped before its first line.
- Anything of the form's rules for the firmware's banner, U-Boot's
  lines, the load, and the monitor's lines on a real boot from a
  card: no boot has reached them. They were written from sources and
  from the board's own log of boots from the NOR.
- The corrected tools on the board: the reset after a boot from a
  card that stopped, and the close-out after it, ran on stand-ins
  alone.
- `verify` at the gates' commit, until its result is added.

## M11-B4, first part, continued: `verify`, the first sitting's record, and the second run's preparation

The section above was signed on 2026-11-20 at 23:51Z, while `verify`
ran: the choice that its departure 4 left to the responsible human.
This section adds what that section said would follow, and what was
made ready for the first sitting's second run. It was written before
that run, and tells nothing of it; the section after this one does.

### `verify` at the gates' commit

`./mvp/mvp verify` ran at the gates' commit (reviewed as `8af29f25`,
signed as `8a131357515179a206e82e1d0ec4d64f738c01d0`; the same
tree), in the gates' clone, from 2026-11-20, 19:07Z, to 2026-11-21,
00:39Z: exit 0 after 19,889 s.

- **Every suite's line is that of M11-B3's gates**, the near-limit
  list's among them (264 runs that reached their limit): the WP arm
  proves 130 of 134 goals and kills 18 of 24 mutants; the CN arm
  proves 5 of 55; CBMC on Leaf A, 336 of 336 properties; CBMC on the
  ring, 13,547 of 14,931.
- **Against M11-B3's gates' record on this host**, by the comparison
  that M11-E used: 32 files; 13 are equal byte for byte, 30 once run
  metadata is set aside, and two differ, each in one line. Both are
  the qualification's record, as text and as JSON, and the line is
  one case: the WP arm's qualification with a wrong implementation,
  under Alt-Ergo. Three of that case's 19 goals end without a proof
  in both runs, so the case is unproved in both, which is what the
  qualification requires of it (`ok=yes`). In M11-B3's run one of the
  three is recorded as a failure of the prover and two reached their
  120 s; in this run all three reached it. The case took 121.2 s
  there and 121.8 s here. The near-limit list does not count a
  qualification's goals, so its count is the same.

So all ten of M11-B3's gates have passed again at the commit that
holds the corrections, which is the first of the three things that
the decision record's entry of `fix: go` asks for before the first
sitting is run again.

**The reading, for the responsible human (the plan's stop 9).** No
verdict changes, and no contract or statement. One count of one
qualification case changes, and only because one prover run reached
its time limit: the plan has such a count recorded as that and put
to the responsible human. That case ran at about 19:10Z to 19:12Z.
The card's read-back ran beside it (departure 4 of the section
above), and the owner session's text-level checks of the pins'
commits, on four cores at low priority, ended as it began. The same
case has ended either way before: at M11-4's point all three runs
reached the limit, and at M11-E's candidate one was recorded as a
failure of the prover ("`verify` at the candidate", above). His
sign-off of this section accepts the reading.

**What ran beside `verify`.** The card's read-back (19:08Z to
19:36Z); the text-level checks of the pins' commits and of the
evidence commit, on four cores at low priority, and the sign-off's
trial and the publication gate's check, which are Git work (19:08Z
to 19:41Z); and, after the sign-off, the comparison of the signed
commits and the audit of the archived ref (23:52Z). By its status
page, the M12 lane's last heavy work had ended at 12:37Z. No whole
check, build, or other gate ran beside it.

### The first sitting's record

Departure 1 of the section above is closed: the record is
`mvp/results/20261120-com260-m11b-first/` (the commit "the first
sitting's record").

- **Where it was made.** At the signed commit of the record tool's
  correction (`6d647374e985630145c89e0277aa1d93dcc7e626`), in the
  sitting's own clone, by that tree's tool, on 2026-11-21 at 00:39Z,
  as soon as `verify` had ended and the gates' clones had left the
  path that the sitting's plan names. Its bundle says
  `tool_tree=source` and `source_tree=clean`, names both commits, and
  lists the two paths that differ from the sitting's commit: the
  record tool and its dry run.
- **What the tool printed:** `BE_MVP_EVIDENCE: PASS sitting …
  result=stopped boots=1 readings=2 readbacks=1 stops=1 B3`. The boot
  was judged again, with the same output as at the sitting.
- **What it holds:** 99 files: the sitting's eight steps (six passed,
  two stopped) and its plan, with the workstation's paths replaced by
  names; the boot's records; the two readings' records, which hold no
  digest; the card's write and two read-backs; the gate's record's
  digests; the tool lock; and the expectations and references of the
  sitting's build. No raw capture: the boot's 191 bytes are named by
  their SHA-256 and kept privately.
- **Read before it was committed:** the boot ROM's four lines hold no
  identifier; no file holds a home path, the account's or the host's
  name, an IPv4 or MAC address, a USB ID, the reader's link, or the
  board's SSH name. The record tool's `--verify` passes on it at its
  own commit and at the commit that adds it.
- No row of the claim ledger cites it: a sitting that stopped shows
  nothing of the claim.

### The second run's preparation

The decision record's entry of `fix: go` has the first sitting run
again only on the responsible human's word and with him present,
after three things: M11-B3's gates, all ten, passed again at the
commit that holds the corrections; that commit signed; and a card
with the new firmware written and read back. With `verify`, above,
all three hold.

The sittings' driver asks for one thing more: a clean tree at a
signed commit that holds the board gate's record, made at that
commit. The chain made it after the record (2026-11-21):

- **The clone:** a clean clone at the last commit of the range that
  the responsible human signed on 2026-11-20
  (`0d81d673e3901a12bbd89947636ca0c859e85645`), at the gates' path.
- **`./mvp/mvp check`, whole**, after the tool lock (`roles=33`),
  00:39Z to 01:09Z: `BE_MVP_CHECK: PASS`. 118 runs under QEMU in 124
  attempts; the six other attempts were refused by `BE_MVP:02` and
  made again, as before. Six sessions. 851 of its 865 listed outputs
  are byte for byte the gates'; the fourteen others name the commit
  that they were built from (the README's open item 143).
- **The board gate**, on the vendor's published files, 01:10Z:
  `BE_MVP_K3_GATE: PASS steps=9 images=38`. 34 of its 38 outputs are
  byte for byte the gates'; the four others are each image's
  `board.json`, which holds the digest of a reference that names the
  commit.
- **The card's image**, 01:10Z, made again from that gate's outputs
  for the card's size. The board firmware and the image have the
  SHA-256 values of the sitting's pins (`d2b4af5d…c9b4` and
  `cbc68f8c…dc49`), and the image's description is byte for byte that
  of the image that was written on 2026-11-20. So the card that was
  written and read back then is the second run's card. It has not
  left the reader since: the reader's disk still has the write's
  sequence number (read at 01:20Z).
- **The owner session's check before a sitting**, 01:12Z. It is a
  scratch script that calls the driver's own functions on the clone's
  files, the card's records, and the workstation's list of USB
  devices; it contacts no board, dongle, console, or reader. It
  passes: the tree clean at that signed commit; the gate's commit that
  commit; the firmware's pin; the card's write and read-back records
  and the image's description in agreement; no device of the board on
  the workstation's USB.

Nothing heavy ran beside that whole check: the owner session read
and committed the first sitting's record meanwhile.

### What was run, and what was not

- **Run:** `verify` at the gates' commit. The record tool at the
  signed commit of its correction, and its `--verify` on the record
  there and at the commit that adds it. In the second run's clone,
  the tool lock, a whole `check`, the board gate, and the card's
  image. The text-level checks of the two commits before this one:
  the release's scan read each of the record's 99 files; one of them,
  the stopped boot's record of loads, is empty, since that boot
  loaded nothing.
- **Not run:** no board command, no dongle command, and no write to a
  card. No gate but `verify`. No whole `check` at the commits of this
  range, whose content is a record, two pages' words, an open item,
  and this section: one is run at the range's tip before its sign-off
  is asked for.

### Departures and readings for review

Each stands unless the responsible human says otherwise.

1. **The steps after `verify` were chained behind it** in a script
   of the owner's, so that they did not wait for the session: the
   gates' clones set aside, the first sitting's record, and the
   second run's clone. The owner read the record afterwards, and
   committed it.
2. **The first sitting's record, the open item, and this section
   land after the range that they belong to**, in a range of their
   own.
3. **The README's open item 143** (the commit "an open item for the
   listed outputs that name their commit") tracks what departure 13
   of the section above left; it settles nothing.
4. **The owner's check wrote a cached-bytecode file into the second
   run's clone, and the owner removed it.** The check's first run
   (01:11Z) imported the sittings' driver without the setting that
   keeps Python from writing bytecode, and left
   `mvp/tools/__pycache__/k3-sitting.cpython-314.pyc` in the clone: a
   file of the kind that the README's open item 141 is about, and the
   one path by which Git then showed the tree as changed. The owner
   removed the file and its directory at once (01:12Z), and the
   script now cannot write one. The tree is clean at that signed
   commit again, as the check's second run, told above, says; and a
   search finds no such directory outside the clone's build
   directory. No step of the sitting had run.
5. **The second run's clone is at the last commit of the signed
   range, which was not the public `main`'s tip.** Four minutes after
   the sign-off of 2026-11-20 (23:51Z), two commits of the M12 lane
   went onto `main` after it, and a third on 2026-11-21 (04:48Z):
   two planning pages of that lane, and one line of
   `LLM_POLICY_ALIGNMENT.md`. The owner session saw that only on
   2026-11-21 at 06:01Z, and until then called that commit the tip.
   It is a signed commit of the public line, and the three later
   commits change nothing that the board gate, the card's tools, or
   the sittings' tools read.

### What is not shown

Nothing in this section is a board step. So it shows nothing of the
project's firmware on the board, of the form's rules on a real boot
from a card, or of the corrected tools on the board. The section
after this one tells the first sitting's second run.

## M11-B4, second part: the first sitting's second run

### Outcome first

- **The first sitting passed** (2026-11-21, 03:38Z to 03:53Z), at the
  signed commit that holds the corrections
  (`0d81d673e3901a12bbd89947636ca0c859e85645`), on the responsible
  human's word and with him at the board: each of its eleven steps at
  its first attempt, and each of its three boots from the card, which
  the form admitted with no stop.
- **The project's firmware printed its banner on the board's
  console**, in each boot. The vendor's U-Boot then loaded the staged
  image, and the candidate's `two-guests`, built without the boundary,
  ran to its shutdown line on harts 0, 1, and 2. Then the firmware
  halted.
- **The banner's facts are inside the addendum's thresholds** (B-6):
  16 PMP entries, a grain of 4 KiB, 38 address bits, and privilege
  version 1.12. They force no change to the board's platform
  description.
- **The NOR and the card are unchanged.** The closing reading equals
  the opening reading in all six ranges; the card, read back whole,
  equals its image.
- **Nothing of the boundary is shown.** No hart was confined, and no
  claim changes.
- **M11-B4 is not complete.** Its second part follows: the second
  sitting's three firmware builds and their card images, at a commit
  that holds the first sitting's facts.

The plan's decision record has the account of the run ("the first
sitting, run again"). This section adds what the record of a run
needs beside it.

### The run

| Step | UTC | Result |
| --- | --- | --- |
| `begin` | 03:39:27 | Passed, on his `sitting: go` (03:38:47Z) |
| `preflight` | 03:39:32 to 03:39:35 | Passed, from the board's own Linux |
| `stage` | 03:39:40 to 03:39:41 | Passed: `be-mvp-two-guests-off-gcc.img` on partition 6 |
| `reading-0` | 03:39:49 to 03:40:29 | Passed: the board's Linux halted; one reset; a boot from the NOR; U-Boot's memory, 8 GiB; the flash read twice, equal |
| `card-in-1` | 03:46:53 | Passed, on his `card in` (03:46:44Z) |
| `boot-1.1` | 03:47:01 to 03:47:18 | Passed: one reset, nothing typed, the form's verdict `PASS stops=none` |
| `boot-1.2` | 03:47:42 to 03:48:03 | Passed, the same |
| `boot-1.3` | 03:48:08 to 03:48:29 | Passed, the same |
| `card-out-1` | 03:52:03 | Passed, on his `card out` (03:51:53Z) |
| `reading-1` | 03:52:09 to 03:52:38 | Passed: one reset; a boot from the NOR; each of the six ranges equal to `reading-0`'s |
| `end` | 03:52:53 to 03:53:33 | Passed: one reset; the board's own Linux up; the preflight's verdict line equal to the first; the session's audit, `banners=6 resets=6 findings=0` |

No other job of the owner session's ran on the workstation during the
sitting, and the M12 lane's lock for heavy work was last taken on
2026-11-20 at 12:32Z.

**Each boot from the card**, as the form judged it and as the record
tool judged it again:

- `BE_MVP_CARD: sitting=first rom_lines=4 … memory=8_GiB
  product=k3_com260_ifx harts=16 priv_version=v1.12 pmp_count=16
  pmp_granularity=12_bits pmp_address_bits=38 digest=none parked=none
  other_lines=0 no_flash_device=d420c000.spi …`: the same line in the
  three boots;
- `BE_MVP_COUNTS: boot_hart=0 started=none exits_g0=156 exits_g1=156
  records=138 wakes=70 … alternations=129`: the same counts in the
  three boots, with other tick values in each;
- `BE_MVP_LOG: contract=v1/complete … state=closed count=13`, and each
  of the thirteen records equal to the reference's;
- `BE_MVP_BOUNDARY: NOT-APPLICABLE boundary=off`;
- `BE_MVP_RESULT: PASS terminal=shutdown-requested`;
- `BE_MVP_CAPTURE[card two-guests-off]: PASS stops=none`.

The three captures have 318 lines each. The banners are equal line
for line, 63 lines; the rest differs only in times, tick counts, the
read speed that U-Boot prints for the load, and the round counts of
the guests' loop.

**The halt held.** U-Boot's own line says that it started a watchdog
with a timeout of 60 s. After the third boot's last line the board
stayed halted, with the card in, for 3 min 50 s, until the closing
reading's reset, and printed nothing: the serial log's offset at that
reset is the offset at the boot's end. So nothing reset the board in
that time. Whether U-Boot stops that watchdog before it starts the
image is not established here.

### The banner, and the build's expectation

The form compares each field of the banner that follows from the
build with the gate's `board.json` for the image, and the root OpenSBI
domain's regions line by line. Each was equal, in each boot. What the
banner adds is the hardware's facts, which no build can give; the
decision record's entry lists them. Against B-6's thresholds:

| Fact | The banner | The threshold |
| --- | --- | --- |
| PMP entries | 16 | at least 14 |
| PMP grain | 12 bits, 4 KiB | at most 4 KiB |
| Privilege version | 1.12 | 1.12 or later |

The banner speaks for the boot hart alone (B-6). Its list of ISA
extensions has no Smepmp, as the published tree's has none.

`mvp/k3/observed.json` (the commit "the first sitting's observed
facts") holds the facts that the second sitting's form compares its
boots with. The owner wrote it by hand, in the form that the capture
checker takes, from the three boots' results, and then compared them
by a script of its own: the file equals the facts in each of the
three results, which are equal to each other, and the form's own
check of the file's shape passes. The frame's check passes with the
file present (`BE_MVP_K3_FRAME: PASS fragments=8 files=26 tools=11`).

### The NOR, and the card

- **The readings.** Each reading read the whole flash twice at
  U-Boot's prompt, with the two reads equal, and digested the six
  ranges of S3-E's item 9. The closing reading's six digests equal the
  opening reading's. The digests stay in the private store; the
  record says `equal` for each range.
- **The lines.** Each boot's capture holds the vendor's line that
  announces the save of the training record, then its line that it
  found no valid device for the flash's controller, and none that the
  form refuses: no flash detected, and no write to the NOR.
- **The card.** After the sitting the card went back into the reader,
  and the tool read it back whole (03:54Z to 04:21Z): 31,927,042,048
  bytes, whose SHA-256 is the image's, and each of the fourteen
  regions equal to the image's, the environment's among them. The
  reader's disk had a new sequence number, as it must after the card
  was out.

### The record

`mvp/results/20261121-com260-m11b-first/` (the commit "the record of
the first sitting's second run"), 121 files.

- **Where it was made.** In the sitting's clone, at the sitting's own
  commit, by that tree's record tool, at 04:21Z, as soon as the
  card's read-back had passed: `BE_MVP_EVIDENCE: PASS sitting …
  result=closed boots=3 readings=2 readbacks=1 stops=none`. Its bundle
  says `tool_tree=source`, `source_tree=clean`, and
  `sitting_source_tree=clean`, names one commit as the source's, the
  sitting's, and the gate's, and says that nothing changed since the
  sitting. The read-back and the record were chained in a script of
  the owner's, started when the sitting had ended.
- **What it holds.** The eleven steps and the plan, with the
  workstation's paths replaced by names; for each boot, the form's
  output, the result with the banner as the form took it, the capture
  from U-Boot's autoboot line on, the measurement log's export, and
  the reset's record; the two readings' records; the session's
  keystrokes, which hold each typed line of the readings and withhold
  the digest of each digest's output; the six resets; the card's
  write and two read-backs; the two preflights; the gate's record's
  digests; the tool lock; and the expectations and references of the
  sitting's build.
- **What it does not hold.** The raw captures: each is named by its
  SHA-256 and kept privately. U-Boot's lines before its autoboot line
  hold the board's identifiers, and are in no file of the record.
- **Read before it was committed.** The boot ROM's four lines, which
  hold no identifier. Each boot's banner and kept capture. A search of
  every file for a home path, the account's and the host's names, an
  IPv4 or MAC address, a USB ID, the reader's link, the board's SSH
  name, and any value of an MD5's form: each such value is the staged
  image's, but one in each preflight, which is the build host's name
  in the banner of the board's own kernel, as in MVP 1.0's board
  records. The record tool's `--verify` passes on the record at its
  own commit and at the commit that adds it.
- No row of the claim ledger cites it. A row for a board run needs
  the claim's words for the board (B-11), which come only with
  M11-B's result.

### What was run, and what was not

- **On the board:** the sitting's steps, each through the tools. Six
  resets by the dongle. The typed lines of two readings, each of them
  one key to stop the autoboot and ten lines from eight templates.
  Nothing while the card was in.
- **On the workstation:** the card's read-back; the record; the
  text-level checks of each commit of this range.
- **A whole `check`** at the words' commit, the last commit before
  this section, from a clean clone, 06:05Z to 06:35Z:
  `BE_MVP_CHECK: PASS`, after the tool lock (`roles=33`). 118 runs
  under QEMU in 127 attempts; the nine other attempts were refused
  by `BE_MVP:02` and made again, as before. Six sessions. The frame's
  check and the sittings' dry run pass with `mvp/k3/observed.json`
  present. Beside it ran a card's write and read-back for the second
  sitting, and the text-level checks of this range's commits, on four
  cores at the lowest priority.
- **No other gate.** Outside the two records, the range changes the
  README, the guide, the disclosure, `mvp/k3/observed.json`, and
  planning pages: no source, tool, test, scenario, or build rule. So
  the ten gates' results of the two sections above stand, and
  `verify`'s inputs are unchanged.

### Departures and readings for review

Each stands unless the responsible human says otherwise.

1. **One request for two acts.** The owner asked for the card's
   removal and its return to the reader together, and recorded his
   one reply, `card out`, as the removal's. The reader's own record
   shows the card's return: a new sequence number, and the read-back.
2. **The record's name holds the run's UTC date**, 2026-11-21, where
   the first run's holds 2026-11-20. Both are records of the first
   sitting.
3. **`mvp/k3/observed.json` is written by hand** (above). No tool
   writes it; the conventions of M11-B's tools leave it to the owner.
4. **The disclosure gains a section** for the work since the
   corrections (section 12), where the plan's work packages name none
   for M11-B4.
5. **The halt and U-Boot's watchdog** (above): a reading, for the
   second sitting, in which the board stays halted between a run's
   end and the next reset.
6. **The range was built twice.** It was first built on the
   sitting's commit, and a whole `check` at its words' commit passed
   (04:38Z to 05:09Z). The public `main` then had three later commits
   of the M12 lane (the section above, departure 5). So the owner
   built the range again on `main` as it stood, with the same changes
   but for that section's corrected words, and ran its checks again;
   the whole check above is the second. Under `mvp/` and `bringup/`
   the two builds of the words' commit have the same trees.

### What is not shown

- Anything of the boundary on the board: no profile was entered, no
  record was printed, and no hostile-monitor image ran.
- The PMP of harts 1 and 2: the banner speaks for the boot hart.
- More than three boots, one card, and one board. The run is
  diagnostic evidence for one board, never hardware validation.

## M11-B4, second part, continued: the second sitting's builds and card images, and two tools corrected

This section follows the first sitting's second run. It tells the
second sitting's preparation: its three firmware builds, their card
images, the first of its cards written, and two corrections of tools
that the work brought out. No board step is in it.

### Outcome first

- **The second sitting's three firmware builds were made on the host
  and inside the evaluator, and each pair is equal** (the addendum's
  B-1), at two commits: the words' commit of the section above, and
  this range's last commit under `mvp/`. They are recorded in the
  plan's decision record and pinned.
- **Their card images are made and pinned**, for a card of the size
  of the one card so far. They were made again at this range's
  content, and are byte for byte the same.
- **`anchor`'s image is on that card**, written whole and read back:
  each of the card's fourteen regions equals the image's.
- **Two tools were corrected first**, each after a whole check
  stopped:
  - the frame tool's self-test, which rested on the tree's own pins
    (the README's open item 144);
  - **the console tool's helper**, whose verdicts after a quiet could
    rest on a stale read of the serial log (the README's open item
    142, closed). It decides when the console tool may type and when
    it may ask for a reset, so its change is the part of this range
    that most needs the responsible human's eye.
- **Not done:** the cards of the two hostile-monitor images, which
  wait for the responsible human's answer on the cards (QB3); and
  the second sitting, each of whose sessions is on his word.

### What happened, in order

All times are UTC, on 2026-11-21.

| UTC | What | Result |
| --- | --- | --- |
| 05:09 to 05:43 | The board gate on the host, then `evaluate` with the gate inside the evaluator, at the words' commit of the section above, in its first build (departure 6 there) | Passed; each output equal |
| 05:44 to 05:47 | The first form of the two pins' commits, and between them the three card images | Made |
| 05:48 to 06:23 | `anchor`'s image written to the card | Passed |
| 05:48 to 05:58 | A whole `check` at the first form of the card pins' commit | **Stopped**, in the frame tool's self-test |
| 06:23 to 06:51 | The card read back | Passed: fourteen regions equal |
| 06:50 to 06:56 | The frame tool's correction, the pins' commits again with the same values, and the words, on the range of the section above | Committed |
| 06:57 to 07:07 | A whole `check` at that content | **Stopped**, at the board tools' dry run, in its `late-prompt` case |
| 07:09 to 07:19 | The whole `check` again, with one sentence of the README changed | **Stopped**, at the same case |
| 07:20 to 07:25 | The owner's reading of the two stops' records, and a reproduction | The cause: a stale read in the console tool's helper |
| 07:28 to 09:12 | A sub-agent's correction of the helper, with a case for the dry run and a reading of the board tools' waits | Delivered; read by the owner |
| 09:21 to 09:22 | This range as it is: the two corrections, the pins, the words | Committed |
| 09:22 to 09:52 | A whole `check` at the words' commit | Passed |
| 09:52 to 10:22 | The board gate on the host, then `evaluate` with the gate inside the evaluator, in that check's clone | Passed; each output equal |
| 10:22 to 10:24 | The four card images again, in the same clone | Each equals its pin |

### The builds, made twice, at two commits

**First**, at the words' commit of the section above (the commit "the
words for the first sitting's second run", whose `mvp/` tree is
`512c0d5d0b80a6f12b51241f29c3b87294157b43`), in the clean clone of
that commit's first whole check:

| Step | UTC | Result |
| --- | --- | --- |
| The board gate, on the vendor's published files, on the host | 05:09:00 to 05:09:32 | `BE_MVP_K3_GATE: PASS steps=9 images=38` |
| `./mvp/mvp evaluate`, with the board gate inside the evaluator | 05:09:32 to 05:43:35 | `BE_MVP_EVALUATE: PASS`. Inside: `check` passes (118 runs in 124 attempts). The host's and the evaluator's outputs are equal: 865 of 865 of `check`'s, and 38 of 38 of the gate's |

**Then**, at this range's words' commit (the commit "the words for
the second sitting's preparation", whose `mvp/` tree is
`5a6eeb46d42984bec2bb647bc9292a22e885cf39`), in the clean clone of
its whole check:

| Step | UTC | Result |
| --- | --- | --- |
| The whole `check` | 09:22:34 to 09:52:19 | `BE_MVP_CHECK: PASS`, after the tool lock (`roles=33`). 118 runs under QEMU in 129 attempts; the eleven other attempts were refused by `BE_MVP:02` and made again. Six sessions. The board tools' dry run passes with 42 cases, `late-prompt` and `stale-read` among them; the sittings' dry run passes (`self_test=195 cases=31`); the frame's self-test and check pass (`cases=62`, `files=26`) |
| The board gate, on the host | 09:52:19 to 09:52:48 | `BE_MVP_K3_GATE: PASS steps=9 images=38` |
| `./mvp/mvp evaluate`, with the board gate inside the evaluator | 09:52:48 to 10:22:07 | `BE_MVP_EVALUATE: PASS`. Inside: `check` passes (118 runs in 128 attempts), its dry runs among it. The host's and the evaluator's outputs are equal: 865 of 865 of `check`'s, and 38 of 38 of the gate's |

So each of the board's four firmware builds is byte for byte the
same on the host and inside the evaluator, at both commits. Each has
540,600 bytes:

| Image | Sitting | SHA-256 of `fw_dynamic.bin` |
| --- | --- | --- |
| `two-guests-off` | first | `d2b4af5d7e246279cbfb7c665ab48c19c440357b13462eec162232636676c9b4` |
| `anchor` | second | `a95128a2140951fdb1a442d178ebbb3ce70219c3f9f582f28a658dd09b254cb4` |
| `k3-breach-g1` | second | `0fd9b322f91ca805844ddd95d073ca6662a77b0f2ab579595efaa4a9e7a028ff` |
| `k3-breach-c` | second | `1f0ad1f9724bef6bdadab2255883bad884b1e7e9b6464b298e85994103d6794b` |

These are the values of the table in "The gates again", above: the
builds have not changed since the corrections' commit, where they
were also made twice, and the board gate made them once more at the
commit of the first sitting's second run. The commit "the second
sitting's firmware builds are pinned" records the three and adds
their lines to `mvp/k3/sitting-pins.txt`. After the second making,
each of the four builds was compared with its line there: equal.

### The card images

Made from the first making's outputs of the gate, for a card of
31,927,042,048 bytes, at the first form of the firmware pins' commit
(05:45Z to 05:46Z):

| Image | SHA-256 of `card.img` | Its FIT |
| --- | --- | --- |
| `anchor` | `6338fd6848c198d7482fb41ad168edf0c2bc9c4d1c30ee3972e9a698c5acff41` | 541,299 bytes |
| `k3-breach-g1` | `ce9c87b2708a5cee01e61a54245ec7a73fbad05ffa14e0c87e07d696b0bf24a2` | 541,307 bytes |
| `k3-breach-c` | `70e2300b5639a911e3b5d777b1f192f5f072c2bed878295eaba440947de18040` | 541,303 bytes |

- Each image's FIT and environment are byte for byte the ones that
  the board gate made; the decision record's entry has their SHA-256
  values. The card image's maker compared each firmware with its pin.
- The commit "the second sitting's card images are pinned" adds the
  three `card` lines. No image is committed: each holds the vendor's
  files.
- **Made again** at this range's words' commit, from the second
  making's outputs (10:22:07Z to 10:24:16Z): each of the four images,
  the first sitting's among them, has the SHA-256 of its `card` line.

### `anchor`'s card

The one card so far, the first sitting's, in the same reader, under
the access rule of M11-B3.

- **The dry run** (05:47Z) passed each of the tool's checks on the
  reader, and printed the write's confirmation for this insertion of
  the card.
- **The write** (05:48:45Z to 06:23:54Z, by the tool's record):
  31,927,042,048 bytes in 2,108.9 s, 15.1 MB/s; `BE_MVP_K3_CARD: PASS
  write image=anchor`.
- **The read-back** (06:24:26Z to 06:51:47Z): each of the card's
  fourteen regions equals the image's, and the card is in the same
  insertion as at the write; `BE_MVP_K3_CARD: PASS readback
  image=anchor`.
- The first sitting's image on the card went with the write. It can
  be made again from its pins, and was (above).
- The write and the read-back ran at the first form of the card
  pins' commit. The tool compared the image with its pin there, and
  that pin's value is this range's.

### The frame tool's self-test

- **What stopped.** A whole `check` at the first form of the card
  pins' commit, from a clean clone (05:48:18Z to 05:58:07Z), stopped
  at `k3-frame-check`: `FAIL check: a firmware pin and a card pin for
  one image`, `BE_MVP_K3_FRAME_SELF_TEST: FAIL cases=62`.
- **The cause.** Two cases of the self-test added made-up pins for
  `anchor` to a copy of the tree's own `k3/sitting-pins.txt`. Once
  the tree pinned `anchor`'s firmware build, the first case's copy
  named `firmware anchor` twice, which the tool rightly refuses. The
  tool's rules were right; the case rested on what the tree pinned.
- **The correction** is the commit "the frame tool's self-test rests
  on its own pins": both cases write the copied file whole, for a
  made-up image `x`. Nine lines added and six removed, inside the
  self-test alone; no case added or removed, and no rule changed. A
  coding sub-agent of the session wrote it, on Claude Opus 5.5, in a
  clone of its own, from a brief; the owner read each line.
- **Tried**, by the sub-agent and again by the owner (06:54Z), each in
  scratch trees: the self-test passes with no pin line, with the
  first sitting's two, and with both sittings' eight; without the
  correction it passes with two and fails with eight, by that one
  case; with the tool's rule against a name twice switched off for
  the sitting pins, the second case fails and no other. By the owner
  also: with a rule that takes one image's two pins for one name, in
  a tree with no pin line, the two cases fail and no other. By the
  sub-agent also: with a rule that refuses a card pin for an image
  that has a firmware pin, in a tree with no pin line, the first case
  fails and no other; and with the second case's own second line
  removed, that case fails.
- **Found and left** (the README's open item 144): no case of the
  self-test covers `k3/firmware-pins.txt`.

### The console tool's helper

`mvp/tools/k3-uboot.py` reads the serial log for the console tool and
judges what U-Boot has printed, before a line is typed or a reset is
asked for.

- **What stopped.** Two whole checks of this range, one after the
  other (06:57:46Z to 07:07:33Z, and 07:09:39Z to 07:19:23Z), stopped
  at `run-tool-check`: `BE_MVP_RUN_TOOL_DRY_RUN: FAIL
  late-prompt.record: exit 1, expected 0`. Every other case of the dry
  run passed; nothing after the dry run was reached. Nothing else of
  the owner session's ran beside either case, the M12 lane's lock for
  heavy work was free, and the load average was under 1.
- **The first reading was wrong.** The same case had stopped one
  whole check on 2026-11-20. The section "M11-B4, first part" above
  (its departure 2) and the README's open item 142 gave its cause as
  the dry run's stand-in U-Boot, held up between two writes for
  longer than the dry run's quiet of 0.05 s. After the first of
  today's two stops the owner still read it so, changed one sentence
  of the item, and ran the check again. After the second the owner
  read the two runs' records.
- **What the records show.** The stand-in's own records have its
  echo of the tool's second `s` written about a millisecond after its
  late prompt, in both runs: it was not held up. The console tool's
  record of the first run names a fresh prompt at a log size of
  1,025 bytes, which is the log with the echo in it.
- **The cause.** The helper's probe after the `s` that stops the
  autoboot read the log, and then waited for a quiet whose first
  measure of the log's size came after the read. The echo reached
  the log between the two, so it was in neither, and the probe
  reported a fresh prompt. The console tool's next step found the
  prompt's line not empty and stopped, typing nothing. The owner
  reproduced it in scratch with no timing: the helper loaded by its
  path, and the echo appended right after the read that returned the
  prompt alone.
- **The same pattern elsewhere.** A second coding sub-agent, on
  Claude Opus 5.5, read every wait of the board tools for it: the
  helper whole, the console tool's own waits, the sittings' driver,
  and the session tool's loops. It found the pattern under the
  helper's idle prompt, the two ends of a run, and the reasons that
  admit a reset at an idle prompt, with Fedora down, after a boot
  from a card, and for an MVP that hangs past its timeout. At a late
  prompt the wrong verdict errs toward a stop; in the reasons for a
  reset it errs toward a reset, when output reaches the log in the
  instant of the read, or in the quiet of a reason judged before.
- **The correction** is the commit "the console helper judges the log
  as it ends". Each such verdict is given only when the log, after
  the quiet, still ends where the judged text ended, the rule that
  the helper's wait for a prompt already had, as one function. Where
  the log has grown, the verdict is withheld, and the next reading
  judges the whole log by the rules as they are. The reason for an
  MVP that hangs is judged on the log read again instead: the
  sub-agent measured that the size rule refuses the reset of an MVP
  that keeps printing (3 of 200 calls on a small log; 50 of 50 with
  2 MB logged since the reset), stopped as its brief required, and
  put that reason to the owner, who chose the second reading. No
  template, message, or other rule of the console tool changes. 122
  lines added and 16 removed, in the helper and the dry run.
- **The test** is the dry run's new case `stale-read`: the helper
  loaded by its path, and a row's bytes landing at a fixed point,
  before a quiet, in it, or after it, with no timing. Twelve rows,
  each with its bytes and with none landing.
- **Tried by the sub-agent** (each in its report's logs): the whole
  dry run with the correction, seven times, each passing, with 42
  cases; the whole dry run with the helper as it was and the new
  case, failing by `stale-read` alone; twelve changes of the
  corrected helper, one guard at a time, each failing the row made
  for it; the busy MVP still given its reset (200 of 200 calls, and
  50 of 50 with 2 MB logged).
- **Tried by the owner** (09:13Z to 09:21Z): the case alone against
  the corrected helper (twelve rows pass) and against the helper as
  it was (ten rows fail); six changes of the corrected helper, one
  guard at a time, each failing its row or rows; the reproduction
  against both; and the sittings' dry run with the correction, in a
  built scratch clone: `BE_MVP_K3_SESSION: PASS self_test=195
  cases=31`.
- **Found and left**, each a weakness of the reset's rule that is
  older than M11 and outside this pattern (the README's open items
  145 to 147): the reset acts on a reading that is one dongle round
  trip old; past a run's timeout, Fedora's kernel lines are not taken
  for Fedora's; and a prompt cut before its second byte is taken for
  a missed stop.

### The soft limits

As the section "M11-B4, first part" counts them, with this range's
two corrections:

| Lane | Limit | Before this range | Now |
| --- | ---: | ---: | ---: |
| The frame | 1,200 | 1,123 | 1,132 |
| The card's tools and the session's tools, with their dry runs | 12,500 | 11,341 | 11,463 |

By the running counts, which count a rewritten line again: 1,159 and
11,907. No limit is passed by either count. The other lanes are
unchanged.

### What was run, and what was not

- **Run:** the board gate and `evaluate`, twice each; the card
  image's maker, seven times; the reader's dry run, the write, and
  the read-back; four whole checks, of which the last passed; the
  two tools' own tests in scratch trees, as above; and the
  text-level checks of each commit of the range (09:52Z to 09:54Z for
  the five commits before this section, on four cores at low
  priority; this section's commit after them).
- **Beside the first making** (05:09Z to 05:43Z) ran the owner's
  text-level checks of the section above's commits, on four cores at
  low priority (05:10Z to 05:24Z), and, by its status page, the M12
  lane's heavy work (05:05Z to 05:22Z; a build on all 32 threads to
  05:12Z). Beside the second making's `evaluate` ran the text-level
  checks of this range, and nothing else of the owner session's;
  nothing ran beside its whole check, and the M12 lane's lock for
  heavy work was free throughout.
- **One start set aside.** The owner started the checks of 06:57Z
  once before, at 06:57:14Z, under an emptied environment, stopped
  them within seconds, after the tool lock had passed, and started
  them again under the session's environment, as every earlier check
  ran.
- **Not run:** no board command and no dongle command since the first
  sitting's end. No other gate: the range changes the frame tool's
  self-test, the console tool's helper and its dry run, the pins'
  file, the README, the disclosure, and planning pages. `check` and
  `evaluate` run the helper's dry runs and the frame's check; no
  other gate reads them, and `verify`'s inputs are unchanged.

### Departures and readings for review

Each stands unless the responsible human says otherwise.

1. **A board tool was changed on the owner's decision.** The console
   tool's helper decides when the console tool may type and when it
   may ask for a reset. The decision record's entry of `fix: go`
   names the corrections that the first sitting asked for, and this
   is not one of them. The owner judged that a check which a defect
   of the tool stops should not be run again until it passes, and
   that the defect's other places err toward a reset. The change
   withholds verdicts and grants none. His sign-off of the range
   accepts it; without it, the helper is as the signed line has it.
2. **The owner's first reading of the dry run's stop was wrong**,
   on 2026-11-20 and again after the first stop of 2026-11-21, and
   the owner told the responsible human that cause twice. The signed
   section above keeps its words; this section and the README's item
   142 correct them. The records of the stop of 2026-11-20 were not
   kept; its lines are those of today's two.
3. **Two ranges, where the owner had said one.** The owner told the
   responsible human that one sign-off would cover the first
   sitting's result and the second sitting's preparation. The first
   whole check of the pins stopped (above), so the first sitting's
   result went to him as a range of its own, and this range follows
   it.
4. **The pins' first commits were set aside**, with the first build
   of the range of the section above. The card images were made, and
   `anchor`'s card written and read back, at those first commits; the
   card's records name the first form of the card pins' commit. The
   pins' values are unchanged, and the images were made again at this
   range's content. B-1's order held in the first form: the builds
   were recorded at 05:44Z, and the first card image was made at
   05:45Z.
5. **The builds were made twice at the words' commit of the section
   above**, in its first build, not at a commit of their own; and
   twice again at this range's words' commit, which holds their pins.
6. **The two hostile-monitor images' cards are pinned before their
   cards are known**, for a card of the first card's size. A card of
   another size would need its image made for that size and its pin
   replaced, in a commit of its own, before its session.
7. **The first sitting's card is written again before the
   sign-off**, as its second card was. After the sign-off the commits
   have other names, so the board gate and the card images are made
   again at the signed commit and must match the pins.
8. **The sittings' dry run with the corrected helper was first run in
   a scratch clone** of the section above's first build, with the
   correction applied by hand, because the sub-agent's clone lacked
   two images. The whole check above runs it at this range's content.
9. **The disclosure's opening** named sections 10 and 11 for the
   board's work while section 12 existed, since the words' commit of
   the section above. This range's words make it sections 10 to 13.

### What is not shown

- Anything of the second sitting: no boot of a boundary-on image has
  been made on the board.
- That the two hostile-monitor images' cards can be written as
  pinned: their cards are not known.
- That the corrected helper behaves on the board as in the dry run:
  no board step has used it. The first sitting's two runs used the
  helper as it was.

## M11-B5, first part: the second sitting's first run, and the firmware's heap on the board

This section follows the second sitting's preparation. It tells the
second sitting's first run, which stopped at its first boot from the
card; the cause; the correction; and the second sitting's firmware
builds and card images, made again.

### Outcome first

- **The second sitting's first run stopped at its first boot from the
  card** (the addendum's stop B6). The project's firmware stopped in
  its cold boot and said why, in two lines: its heap could not hold
  the switch contexts of the tree's OpenSBI domains. No line of
  U-Boot or of the monitor was printed, and no hart was confined.
- **The NOR is unchanged, and the card equals its image.** The
  closing reading equals the opening reading in all six ranges, and
  the card, read back whole, equals its image in each of its fourteen
  regions.
- **The owner session's first account of the stop was wrong.** It
  told the responsible human that the firmware had gone silent. The
  firmware had printed the cause; the form of that time did not quote
  it, and the owner session had not read the capture's end.
- **The cause is established** from the capture's two lines, the
  series' source, and the build's own sizes, and **reproduced under
  QEMU**: with the board's hart count, vector length, and M-level
  APLIC sources, the firmware base's default heap stops the cold boot
  with the same two lines.
- **The correction** is in two commits. A board tree that holds the
  OpenSBI domains gives the firmware a heap of 256 KiB, by the
  firmware base's own property (an erratum to the addendum's B-3,
  which the responsible human's sign-off of this range decides).
  Three rows of the firmware's tests size the heap on the board's
  load. The form now quotes a firmware's own failure lines and judges
  the banner's heap.
- **The second sitting's three firmware builds and their card images
  were made again and pinned.** The first sitting's build and card
  image are byte for byte what they were.
- **Not done:** the second sitting. It needs the responsible human's
  sign-off of this range, the builds and the card images made again
  at his signed commit, the card written again, and his word for each
  session.

### What happened, in order

All times are UTC, on 2026-11-21.

| UTC | What | Result |
| --- | --- | --- |
| 14:32 | The responsible human chose to run the sitting with the one card of the images' size | Taken by the owner session as his word for the sitting (departure 1) |
| 14:37 to 14:39 | The owner's precheck; `begin`, the preflight, the staging, and the opening reading | Passed |
| 14:41 to 14:43 | His direction to use a second card reader afterwards; the card into the board, on his word | `card-in-1` passed |
| 14:43 to 14:45 | The first boot from the card, one reset by the dongle, nothing typed | **Stopped**: stop B6 |
| 14:48 | The owner session's first account to him, that the firmware had gone silent | Wrong (departure 2) |
| 14:57 to 14:59 | The card out, on his word; the closing reading; `end` | Passed: six ranges equal; the preflight's verdict line as before |
| 15:13 to 15:20 | His one command for the second reader's access rule; the card read back whole through it; the sitting's record | Fourteen regions equal; the record made |
| 15:20 to 15:30 | The owner session read the capture's end by its lines' forms, the series' source, and the build's sizes | The cause |
| 15:32 to 18:21 | A sub-agent's design, its measurements under QEMU, and the correction, in three parts and two fix-ups after the owner's reviews | Delivered; read by the owner |
| 17:10 to 17:35 | The owner judged the four real captures with the changed form, twice | One defect found in the form's first version, and corrected |
| 18:14 to 18:15 | The two commits of the correction on the working branch | Committed |
| 18:15 to 19:46 | A whole `check`, the board gate on the host, `evaluate` with the gate inside the evaluator, the U-Boot rehearsal, and the CHERI check, at the second of them | Passed, each step |
| 19:20 to 19:25 | The firmware pins' commit; the three card images; the card pins' commit; the words' commit | Made |
| 19:46 to 20:19 | A whole `check`, the board gate, the four builds and the four card images against the pins, at this range's last commit under `mvp/` | Passed, each step |
| 20:19 to 20:49 | A whole `check` at the first of the correction's two commits | Passed |

### The run, and its stop

The run's record is `mvp/results/20261121-com260-m11b-second/`
(103 files), made by the sittings' record tool at the
sitting's commit: `result=closed boots=1 readings=2 readbacks=1
stops=B6`. The M11 plan's decision record has the account of the run.
In short:

- **Before the boot:** the preflight from the board's own Linux; the
  three images staged on partition 6; the opening reading of the NOR,
  in a boot from the NOR in which U-Boot showed 8 GiB of memory; and
  the card's insertion.
- **The boot:** the boot ROM's four lines, as in the first sitting;
  the vendor SPL's banner; then the project's firmware: its logo, its
  line for the configuration digest, which is the build's, and

  ```
  sbi_domain_finalize: domain context allocation failed (error -1004)
  init_coldboot: domain finalize failed (error -1004)
  ```

  and nothing for 120 s. The capture is 723 bytes.
- **The tools:** the form refused the capture with 116 findings and
  quoted neither line; the driver's stop named the missing U-Boot
  banner. The console tool admitted the one reset for the closing
  reading by its rule for a boot from a card that stopped.
- **The close:** the card out; the closing reading, equal in all six
  ranges; the board's own Linux; the preflight, with the same verdict
  line.
- **The card:** read back whole after the session, equal to its image
  in each of fourteen regions. The read-back went through a second
  reader (departure 3).

### The cause

`-1004` is the firmware base's code for no memory, and the first of
the two lines is the series' own. The series allocates, in the
firmware's cold boot, one switch context for each pair of an OpenSBI
domain and a hart that the domain lists, each with a vector area
sized for the cold boot hart (the M11 plan's design rule "No heap":
no allocation that a hart's own call could cause after cold boot).

| | Switch contexts | The banner's heap |
| --- | --- | --- |
| The first sitting's build: the root OpenSBI domain alone, sixteen harts | 16 | 104 KB in all, 67 KB in use, 34 KB free (on the board) |
| `anchor`'s tree: the root, `be_boot`, `be_control`, `be_g0`, `be_g1`, and `be_park` | 16 + 3 + 1 + 1 + 1 + 13 = 35 | no banner: the cold boot stopped |

Each context is 768 bytes and, with a vector length of 256 bits, a
vector area of 1,088 bytes, as the heap aligns them. The firmware
base sizes its heap from the hart count, 104 KiB for sixteen harts,
and the nineteen further contexts and five domain structures do not
fit in the 34 KB that the first sitting's banner shows free.

**Why no gate showed it.** Three things each hid it:

- the suite's row of the board trees' shape ran on QEMU's machine of
  eight harts, with no vector extension: there the same OpenSBI
  domains leave 19 KB of a 66 KB heap free;
- on sixteen harts with a vector length of 256 bits the cold boot
  still completes under QEMU, with 3 KB free: QEMU's interrupt
  controllers are smaller than the board's, whose M-level APLIC has
  512 sources where QEMU's has 96, and the firmware sizes a table on
  its heap from that count;
- the firmware's own test of a heap that cannot hold the contexts
  (`alloc-fail`) shows the stop as a mechanism, and no run sized the
  heap for the board.

The owner session's research after the first sitting's first run had
named the heap at this step as a risk, with the property that sets
it. It was not followed up before this sitting (departure 4).

### The correction

**The heap's size.** A board tree that holds the OpenSBI domains
carries `heap-size = <0x40000>` in `/chosen/opensbi-config`, the
firmware base's own property, which its generic platform reads in
place of its default. The value is the board description's
`firmware.heap`; the description also holds a floor,
`firmware.heap_free_min`, 64 KiB, on the free heap that the banner
prints.

- `mvp/tools/partition-backend.py` writes the property into a board
  tree with OpenSBI domains, and into no other tree. It refuses a heap
  that would move either of the firmware's two regions.
- `mvp/tests/check-partition.py`, which shares no code with the
  backend, requires the property there with the description's value,
  refuses it anywhere else and in a tree without OpenSBI domains, and
  takes the firmware's end from the tree's own property, as the
  firmware reads it.
- `mvp/tools/k3-recipe.py`'s check of a board tree against QEMU's
  requires the property too, and its check of the description
  requires the M-level APLIC's sources of the published tree.
- The firmware's two regions in the root OpenSBI domain are where
  they were: the heap grows inside the read-write region as the
  firmware rounds it, and the firmware ends below the first real-time
  core's entry. The tables of every hart are unchanged.

**The measurement.** Three rows of the firmware's own tests
(`mvp/firmware/tests/fwtest.py`) run on QEMU with what the
description gives of the board: sixteen harts, a cold boot hart whose
vector length is 256 bits, the PMP's grain of 4 KiB, the M-level
APLIC's 512 sources, and D-6's OpenSBI domains for sixteen harts.

| Row | The tree's heap | What it shows |
| --- | --- | --- |
| `board-heap-default` | none: the default, 104 KiB | The cold boot stops with the board's two lines, after the configuration digest's line |
| `board-heap` | 256 KiB | The banner: 256 KB in all, 4 KB reserved, 105 KB in use, 145 KB free; D-6's sequence runs on harts 0 to 2 |
| `board-heap-floor` | 160 KiB | The banner: 49 KB free, which the floor's rule finds; D-6's sequence still runs |

The sub-agent measured each part of the load apart, before it wrote
the rows: with the root OpenSBI domain alone, sixteen harts, and a
vector length of 256 bits, QEMU's firmware uses 51 KB; with the
APLIC's 512 sources, 61 KB. The first sitting's banner on the board
shows 67 KB. The 6 KB between them fits the board's IMSIC, by the
sizes of the firmware's tables for it: its 511 identities cannot be
given to QEMU's IMSIC, which takes the firmware's enables only up to
its own 255. No run shows that part.

**What the measurement predicts for the board:** about 6 KB more in
use than `board-heap` shows, so about 139 KB free at the banner.
Under QEMU, in that row's shape, 142,400 bytes were still free at the
end of D-6's sequence, after harts 1 and 2 had started (a scratch run
that read the heap's control block; no row reads it). The second
sitting's form requires at least 64 KiB.

**The vector length is an inference** (departure 6). The description
gives 256 bits because the first sitting's 67 KB fits it: 128 bits
would give 8 KB less in use, and 512 bits 16 KB more. No register was
read. With 512 bits the 35 contexts would take about 35 KB more, and
the heap would still have about 100 KB free.

**The form.** `mvp/tests/check-capture.py`, in its card mode:

- takes a line of the firmware's failure form, `FUNCTION: TEXT (error
  N)`, between the firmware's version line and U-Boot's banner, for a
  finding of the sitting's stop, and puts such findings first in the
  record. The driver's stop takes the first finding of its stop, so
  it quotes the firmware's line; the driver is unchanged;
- counts and notes the lines after the banner's last field, up to
  U-Boot's banner, with the banner's other lines. A line of the
  vendor U-Boot's time stamp alone is none;
- records the banner's heap line, and in the second sitting requires
  it to be of the firmware's form, its total the description's heap,
  and its free heap at least the floor.

### The form's first version, and the real captures

The owner session judged the first sitting's three captures and the
stopped capture with the changed form, privately, before it accepted
the change.

- With the form's first version, each of the first sitting's three
  captures passed, but each showed one other line, where the
  committed `mvp/k3/observed.json` has none. The line is the vendor
  U-Boot's stamp alone: its U-Boot prints a stamped empty line before
  its banner, with another time in each boot. The form's test could
  not show it, because its stand-in U-Boot printed no stamp.
- **With that version, every boot of the second sitting would have
  stopped**, on a line that says nothing. The sub-agent corrected it:
  a line that is empty once the stamp is removed is no line. The
  stand-in's U-Boot now begins with a stamp alone.
- With the corrected form: the three captures pass as before, with no
  other line and a heap of 104 KB, 67 in use and 34 free; the stopped
  capture is refused with the firmware's two lines as its first two
  findings, under stop B6. `mvp/k3/observed.json` is unchanged.

The owner session also ran the form's banner reader and its rules for
the OpenSBI domains on the real console of the row `board-heap`: 137
fields, each known field once and in the form's order, no other line
inside the banner, and the parked harts assigned to one OpenSBI
domain of their own. The second sitting's form had been run on no
real banner with OpenSBI domains before.

### The builds and the card images, made again

**The builds.** At the correction's second commit the board gate
built the four firmware builds on the host, and `evaluate` built each
again inside the evaluator: all 38 of the gate's outputs are equal
byte for byte, and all 865 of `check`'s. The plan's decision record
has the three new builds' SHA-256 values with their device trees',
and `mvp/k3/sitting-pins.txt` the three `firmware` lines, replaced.

- Each new tree is its old tree with the one property added, 26
  bytes more as compiled.
- Each new build has the size of the old, 540,600 bytes. The tree is
  at the same offset in it; the read-only data after the tree lies 32
  bytes further on; `_fw_rw_start` and `_fw_end` are where they were.
- **The first sitting's build is byte for byte what it was**, and so
  are its tree, its FIT, and its environment.

**The candidate's images.** Of the 801 outputs of M11-E's
candidate's record, the 566 that do not carry the build's directory
are equal byte for byte at each of the three commits that the checks
ran at, every flat image, boot image, and device tree among them. The
other 235 are the ELF files and the tables and records that carry the
directory, as between any two clones.

**The card images.** The three were made again from those builds
(19:21Z to 19:24Z), after the firmware pins' commit, for a card of
31,927,042,048 bytes, and are pinned; the decision record has each
image's SHA-256 with its FIT's and its environment's. Each
environment is byte for byte what it was. At this range's last commit
under `mvp/`, the four card images were made once more, and each
equals its pin, the first sitting's among them.

**The card itself** still holds `anchor`'s image of the first run,
whose pin is no longer in the tree (departure 10). It is written
again, whole, with the new image, and read back, before the second
sitting runs again.

### The soft limits

Counted as the section "M11-B4, first part" counts them, at the
second commit of the correction: one diff from M11-E's candidate, each
line given to the lane of the commit that wrote it; and the running
counts, which count a rewritten line again.

| Lane | Limit | One diff | Running |
| --- | ---: | ---: | ---: |
| The addition's tests and the board's build rules | 3,000 | 2,652 | 2,657 |
| The frame | 1,200 | 1,126 | 1,159 |
| The tree's recipe, the backend's second platform, the checker on the board's trees, and the hostile-monitor declarations | 3,000 | 2,676 | 2,824 |
| The card's tools and the session's tools, with their dry runs | 12,500 | 11,468 | 11,917 |
| The checker's form for a boot from a card, the harness's end of a halting run, and the ledger tool's method | 4,000 | 3,302 | 3,430 |

This range's two commits add 178 lines to the first lane, 237 to the
third, 10 to the fourth, and 191 to the fifth. No limit is passed by
either count.

**A reading, for review** (departure 8). The three board rows are 174
lines of `mvp/firmware/tests/fwtest.py`, a file of M11's own lane
"the firmware's tests and build rules" (3,000; 2,825 at the
candidate). They test the board's firmware configuration, so they are
counted here in the addendum's lane for the board's build rules.
Counted in M11's lane instead, that lane would stand at 2,999 of its
3,000.

### The owner's own tests

- **The four real captures**, judged with the changed form, twice
  (above): the first sitting's three and the stopped one. Private:
  the captures are not published.
- **The form's rules for the OpenSBI domains on a real banner**
  (above): the console of the row `board-heap`.
- **Eight rules changed one at a time**, each in a copy of the tools,
  with the test that must then fail:
  - the backend writing the property into `/chosen` and not into the
    configuration node; the backend writing another value; the
    checker comparing only the property's last cell: each failed its
    test by the rule's own case;
  - the form taking failure lines only after the banner's last field;
    the form counting a stamp alone; the floor's comparison made
    inclusive; the heap's rules applied in the first sitting and not
    the second: each failed the form's test;
  - **one survived**: a heap total larger than the description's
    accepted. The rule was right and its only negative had a smaller
    total. The sub-agent added a row with a larger one, and the
    change now fails it.
- **The old and the new builds compared.** Each of the three new
  device trees is its old tree with the one property added, as source
  and as the compiled tree read back (62,239 and 62,265 bytes). In
  each new firmware build the tree is at the same offset, the 33
  read-only symbols after it are 32 bytes further on, and
  `_fw_rw_start` and `_fw_end` are where they were. The old and the
  new binary therefore differ in more than the tree's bytes; each is
  540,600 bytes.
- The sub-agent's own seeded changes, which the owner read and did
  not run again: 14 of the backend, the checker, and the recipe; 6 of
  the rows; 10 of the form. Each fails the test that holds its rule.

### What was run, and what was not

- **Run on the board:** the second sitting's first run, as above:
  three resets by the dongle (the opening reading's, the boot from
  the card, and the closing reading's), and the typing of the two
  readings alone. Nothing since `end`.
- **Run on the card:** one read-back of the whole card, through the
  second reader. No write.
- **Run at the correction's second commit**, from clean clones: the
  tool lock and a whole `check` (18:15Z to 18:46Z: 118 runs under
  QEMU in 129 attempts; six sessions; the firmware's tests, 44 runs;
  865 outputs); the board gate on the host (18:47Z: nine steps, 38
  outputs); `evaluate` with the gate inside the evaluator (18:47Z to
  19:17Z: all 865 of `check`'s outputs and all 38 of the gate's equal
  byte for byte); the U-Boot rehearsal (19:17Z to 19:21Z: seven
  cases); and the CHERI check, from a second clean clone (19:21Z to
  19:46Z: 56 runs under the CHERI emulator in 57 attempts, the 222
  plain images equal to those of a plain build of the same commit,
  and the regression build's 50 runs in 55 attempts).
- **Run at this range's last commit under `mvp/`**, from a clean
  clone: the tool lock and a whole `check` (19:46Z to 20:16Z: 118
  runs under QEMU in 122 attempts; six sessions; 865 outputs); the
  board gate (20:16Z to 20:17Z: nine steps, 38 outputs); each of the
  four firmware builds, equal to its pin; and the four card images,
  made again (20:17Z to 20:19Z), each equal to its pin.
- **Run at the correction's first commit**, from a clean clone, after
  the others: the tool lock and a whole `check` (20:19Z to 20:49Z:
  118 runs under QEMU in 128 attempts; six sessions; the firmware's
  tests, 44 runs, the three board rows among them; 865 outputs).
- **The sub-agent's runs**, in its own clone, are not this range's
  checks: the firmware's tests, the tree's and the form's checks, the
  sittings' dry run, a whole `check`, the board gate, and the U-Boot
  rehearsal at its commits.
- **Beside the checks:** beside the first chain's whole `check`, the
  owner's count of the lanes, twice, a few seconds each, and, in its
  first minutes, perhaps the last of the sub-agent's seeded changes
  (its report came at 18:21Z); beside the first chain's `evaluate`,
  the text-level checks of the correction's two commits (18:54Z to
  18:55Z), on eight cores at low priority; beside its CHERI check,
  the making of the three card images (19:21Z to 19:24Z) and the
  text-level checks of the pins' and the words' commits (19:25Z to
  19:27Z). Beside the second chain, and beside the whole `check` at
  the first commit, the owner read logs, compared lists of outputs,
  and wrote this section, and ran nothing heavier. The M12 lane's
  status page, last written at 06:07Z, says that nothing of the
  lane's runs.
- **Not run:** `verify`, `kernel-repro`, and the model's two gates.
  The range changes no path that the proofs' records bind, no guest
  input, and nothing of the model: the backend, the checker, the
  recipe, the firmware's tests, the board's description and its Make
  file, the form and its tests, the pins' file, and pages.
- **Not run again on the board:** the second sitting. Its card still
  holds the first run's image.

### Departures and readings for review

Each stands unless the responsible human says otherwise.

1. **The owner took his choice of the card for his word for the
   sitting.** Asked how to run the sitting with one card of the
   images' size, he chose to run it with that card (14:32Z). The
   owner had told him that the first session was ready, and began the
   sitting on that. He gave his word for the session as he put the
   card in.
2. **The owner's first account of the stop was wrong.** Right after
   the boot it told him that the firmware had gone silent after its
   digest line, and asked for the card out on that account. The
   capture held the firmware's own two lines; the owner had read the
   form's findings, which did not quote them, and not the capture's
   end. It found them within the hour, after the close, and told him.
   The form now quotes such lines first.
3. **A second card reader**, a departure from the letter of QB4 ("the
   one reader"): a card slot on a USB 3 hub, at his direction,
   approved by him with the card tool's one command, which replaces
   the first reader's rule. The card was written through the first
   reader and read back through the second; the tools accept that,
   and each record names its reader by a digest.
4. **A risk that the owner had named was not followed up.** Its
   research after the first sitting's first run named the heap at the
   domains' set-up, with the property that sets it. No row sized the
   heap for the board before the second sitting ran.
5. **The erratum to the addendum's B-3 is made before his decision.**
   The board's trees with OpenSBI domains carry `heap-size` in this
   range's commits; B-3's step 4 has the descriptor's nodes added as
   the backend renders them for QEMU. His sign-off of the range
   decides it. Without it, the second sitting cannot run: the
   firmware of the signed line does not complete its cold boot from
   those trees.
6. **The vector length is inferred, and the heap's size and floor are
   the owner's choices.** 256 KiB and 64 KiB are chosen from the
   sub-agent's measurements under QEMU, with the vector length that
   the first sitting's banner suggests. The README's open items 148
   and 150 say what is not measured.
7. **The form's first version would have stopped every boot of the
   second sitting**, and no test showed it. The owner found it by
   judging the first sitting's real captures, which the tests do not
   hold: they are private. The stand-in now prints the stamp that
   showed it. Other differences between the stand-in and the board's
   real lines may remain; the second sitting's form has still judged
   no real boot that passes.
8. **The three board rows are counted in the addendum's lane** for
   the board's build rules (above). In M11's lane for the firmware's
   tests they would stand one line under its limit.
9. **One sentence of the board's description was the owner's and was
   inexact**: it gave a scratch measurement to the suite's rows. It
   is corrected in this range, before any pin was made.
10. **The sitting's pins are replaced, and the old builds' pins are
    gone from the tree.** The decision record keeps both sets. A
    card that holds an old image no longer has a pin; the one card is
    written again before the sitting.
11. **The chain of checks ran once, at the correction's second
    commit; the checks at the other commits are fewer.** At the
    correction's first commit a whole `check` ran, and at the range's
    last commit under `mvp/` a whole `check`, the board gate, and the
    builds and card images against their pins. `evaluate`, the
    rehearsal, and the CHERI check ran at the correction's second
    commit alone: the three commits after it change the pins' file
    and pages. The whole `check` at the first commit ran last of all.
    The first chain's driver, a script of the owner's, stopped after
    its whole `check`, on a wrong path of its own for the list of
    outputs; the owner continued it 89 s later from the next step,
    and no step ran twice. `evaluate` took 43 of its closure's 259
    packages from Fedora's `updates` repository, and the others from
    the workstation's cache.
12. **The owner's estimate of the time between two sessions was
    low.** With the one card, a read-back, a write, and a read-back
    lie between two sessions. The owner had told him about an hour;
    with the first reader, which wrote at 15 MB/s and reads at 19, it
    is about an hour and a half. The owner corrected it when he asked
    about the reader. The second reader reads at 89 MB/s; its writing
    speed is not yet known.

### What is not shown

- **Nothing of the boundary on the board.** No hart was confined, and
  M-mode printed no commit record there.
- **That the corrected heap is enough on the board.** It is measured
  under QEMU and predicted for the board. QEMU's IMSIC is smaller
  than the board's, and its harts are of one kind.
- **That nothing else stops the second sitting.** Its first boot
  ended in the firmware's cold boot, so nothing after that point has
  run on the board from a tree with OpenSBI domains: the vendor's
  U-Boot in the boot OpenSBI domain, the monitor's starts and
  confines, and the hostile-monitor images.
- **The board's vector length.** It is inferred.
- No claim changes. The claim's page and the ledger's rows say what
  they said.

## M11-B5, second part: the second sitting's second run; and M11-B6, the words for the board's result

This section follows "M11-B5, first part". It tells the second
sitting as it was run again, with the heap's correction, and the
commits that put M11-B's result to the responsible human.

### Outcome first

- **The second sitting passed** (2026-11-22, 15:52Z to 22:47Z), at
  the signed commit that holds the heap's correction and the builds
  and card images made again
  (`593bf3542054c73543b0fe051a079fed6af82e80`), on the responsible
  human's word and with him at the board. Each of its three sessions
  passed: three boots of `anchor`, and one boot each of the board's
  two hostile-monitor images, `k3-breach-g1` and `k3-breach-c`, from
  the card with the boundary on. The form admitted each of the five
  boots with no stop.
- **It is the first time that an image with the boundary on ran on
  the board.** In each boot M-mode's printed records show harts 0 to
  2 committed, each with the entries of its profile's table, and the
  thirteen other harts not committed.
- **M-mode's counts are the sums that the images declare**: none on
  any hart in `anchor`'s three boots; 73 access faults and 33
  refused calls on hart 2 in `k3-breach-g1`'s boot; 85 access
  faults, 31 refused calls, and 7 rejected calls on hart 0 in
  `k3-breach-c`'s.
- **The heap is as the measurement under QEMU predicted.** The
  banner shows 256 KB in all, 111 KB in use, and 139 KB free in each
  boot; about 139 KB was predicted, and the form requires 64 KB.
- **The NOR and the card are unchanged.** Each of the four readings
  equals the one before it in all six ranges; the card, read back
  whole after each write and after each session, equals its image.
- **One step stopped and was taken up once**: the first preflight,
  before any reset of the sitting's (departure 1).
- **The words for a board result are proposed** in this range, in the
  form that the addendum's B-11 fixes: the claim page's paragraph
  about the board, the limit's sentences for it, and the ledger's
  three board rows. They are used only if the responsible human
  accepts M11-B's result; his sign-off of this range is that
  decision.
- **This is diagnostic evidence from one board, on one day. It is
  not hardware validation.** What M-mode printed is the only witness
  there.

The plan's decision record has the account of the run ("the second
sitting, run again"). This section adds what the record of a run
needs beside it.

### The run

All times are UTC, on 2026-11-22.

| Step | UTC | Result |
| --- | --- | --- |
| `begin` | 15:52:56 | Passed, on his `sitting: go` (15:51:47Z) |
| `preflight`, first attempt | 15:53:02 to 15:53:12 | **Stopped**: the board did not answer over SSH (departure 1) |
| `preflight`, second attempt | 15:55:38 to 15:55:41 | Passed, from the board's own Linux |
| `stage` | 15:55:46 to 15:55:48 | Passed: the three images on partition 6 |
| `reading-0` | 15:55:57 to 15:56:37 | Passed: the board's Linux halted; one reset; a boot from the NOR; U-Boot's memory, 8 GiB; the flash read twice, equal |
| `card-in-1` | 16:12:24 | Passed, on his `card in` (16:12:16Z) |
| `boot-1.1` | 16:12:34 to 16:12:59 | Passed: one reset, nothing typed, the form's verdict `PASS stops=none` |
| `boot-1.2` | 16:14:00 to 16:14:29 | Passed, the same |
| `boot-1.3` | 16:14:36 to 16:15:05 | Passed, the same |
| `card-out-1` | 16:18:07 | Passed, on his `card out` (16:18:00Z) |
| `reading-1` | 16:18:22 to 16:18:52 | Passed: one reset; a boot from the NOR; each of the six ranges equal to `reading-0`'s |
| The card: read back, written with `k3-breach-g1`'s image, read back | 16:18:59 to 16:58:13 | Each read-back equal in fourteen regions |
| `card-in-2` | 21:44:06 | Passed, on his `card in` (21:43:32Z) |
| `boot-2.1` | 21:44:14 to 21:44:39 | Passed: one reset, nothing typed, `PASS stops=none` |
| `card-out-2` | 21:46:27 | Passed, on his `card out` (21:46:19Z) |
| `reading-2` | 21:46:35 to 21:47:02 | Passed: each of the six ranges equal to `reading-1`'s |
| The card: read back, written with `k3-breach-c`'s image, read back | 21:48:31 to 22:27:14 | Each read-back equal in fourteen regions |
| `card-in-3` | 22:41:02 | Passed, on his `card in` (22:40:53Z) |
| `boot-3.1` | 22:41:10 to 22:41:35 | Passed: one reset, nothing typed, `PASS stops=none` |
| `card-out-3` | 22:45:57 | Passed, on his `card out` (22:45:49Z) |
| `reading-3` | 22:46:03 to 22:46:30 | Passed: each of the six ranges equal to `reading-2`'s |
| `end` | 22:46:38 to 22:47:19 | Passed: one reset; the board's own Linux up; the preflight's verdict line equal to the first; the sitting's audit, `banners=10 resets=10 findings=0` |
| The card's last read-back; the record | 22:47:44 to 22:54:12 | Equal in fourteen regions; the record made |

No other job of the owner session's ran on the workstation during the
sitting's steps, but the card's reads and writes between the
sessions. The M12 lane's status page, last written on 2026-11-21,
names no run of the lane's since that day.

**Each boot from the card**, as the form judged it and as the record
tool judged it again, with the same output:

- `BE_MVP_CARD: sitting=second rom_lines=4 … memory=8_GiB
  product=k3_com260_ifx harts=16 priv_version=v1.12 pmp_count=16
  pmp_granularity=12_bits pmp_address_bits=38 digest=… parked=be_park:13
  heap_kb=256,4,111,139 other_lines=0 no_flash_device=d420c000.spi …
  reference=observed`: the same line in the five boots, but for the
  digest, which is each image's own, and for the count of the lines
  that the card host's driver prints while U-Boot loads its
  environment, which is 5 in four boots and 6 in one. The form admits
  both;
- `BE_MVP_COUNTS: boot_hart=0 started=none exits_g0=246 exits_g1=128
  denials_g0=4 denials_g1=1 mgmt_g0=13 mgmt_g1=2 records=174 …
  alternations=122`: the same counts in the five boots, with other
  tick values in each;
- `BE_MVP_LOG: contract=v3/complete r2=kept state=closed count=15`,
  and each of the fifteen records equal to the reference's;
- `BE_MVP_BOUNDARY: PASS image=… pmp_mode=plain control_hart=confined
  harts=0:confined,1:confined,2:confined others=13:uncommitted
  witness=printed identity=…`, with `hook=not-read` in the two
  hostile-monitor images' boots;
- `BE_MVP_RESULT: PASS terminal=shutdown-requested`;
- `BE_MVP_CAPTURE[card …]: PASS stops=none`.

The five captures have 496 lines each, but the last, which has 497.

**The halt held, and so did U-Boot's prompt.** After each session's
last boot the board stayed halted, with the card in, until the next
reading's reset: for 3 min 27 s, 2 min 4 s, and 4 min 36 s. It
printed nothing in that time: the serial log's offset at each of
those resets is the offset at the card's removal. Between the first
session's closing reading and the second session's boot the board
waited at U-Boot's prompt for 5 h 25 min, and between the second and
the third for 54 min; the serial log did not grow, and nothing reset
the board.

### What M-mode printed

On the board no oracle reads the machine. The boundary's judge takes
M-mode's commit records as the firmware prints them after the
monitor's last line, and the banner. In each of the five boots:

- sixteen records, one for each hart, in order;
- harts 0, 1, and 2: committed; the configuration bytes and the
  addresses of the sixteen PMP entries those of the hart's profile's
  table for plain PMP, which the gate's record holds for the image;
  `menvcfg` with the invalidate control clear; `mseccfg` zero;
- harts 3 to 15: not committed;
- the banner's configuration digest, the monitor's own line for it,
  and the gate's record of the image: one identity.

| Boot | Hart 0 | Hart 1 | Hart 2 | Harts 3 to 15 |
| --- | --- | --- | --- | --- |
| `anchor`, three boots | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |
| `k3-breach-g1` | 0, 0, 0 | 0, 0, 0 | 73, 33, 0 | 0, 0, 0 |
| `k3-breach-c` | 85, 31, 7 | 0, 0, 0 | 0, 0, 0 | 0, 0, 0 |

Each cell: access faults, refused calls, rejected calls. The two
hostile-monitor images' sums are those of the board's declarations,
`mvp/k3/breach/breach-g1.json` (112 attempts by the hook on hart 2)
and `breach-c.json` (132 attempts by the hook on hart 0), which the
gate's record holds as each image's expectation. Under QEMU, where
the same two images ran first, the oracle read the hook's record of
each attempt; on the board that record stays in memory and was not
read (`hook=not-read`).

**What the counts do not hold.** They are sums for each hart, not one
for each attempt. The trap of the cache-block instruction is in none
of them. A fault on a register of one of the board's devices may
have a cause other than PMP, and would be counted the same. The
limit on the claim's page says each of these.

### The heap

The banner's line, in each of the five boots: 256 KB in all, 4 KB
reserved, 111 KB in use, 139 KB free.

| | In all | In use | Free |
| --- | ---: | ---: | ---: |
| The row `board-heap` under QEMU | 256 KB | 105 KB | 145 KB |
| The prediction for the board ("M11-B5, first part") | 256 KB | about 111 KB | about 139 KB |
| The board, five boots | 256 KB | 111 KB | 139 KB |
| The form's floor | | | 64 KB |

The 6 KB between QEMU's row and the board is what the board's IMSIC
was expected to add. That agrees with the vector length of 256 bits
that the board's description infers; it is still an inference, and
the README's open item 148 stays open. Nothing reads the heap after
the banner: what the harts' later allocations took on the board is
not shown (open item 149).

### The NOR, and the card

- **The readings.** Four: before the first session, and after each
  session. Each read the whole flash twice at U-Boot's prompt, with
  the two reads equal, and digested the six ranges of S3-E's item 9.
  The six digests of each reading after the first equal those of the
  reading before it. The digests stay in the private store; the
  record says `equal` for each range.
- **The lines.** Each boot's capture holds the vendor's line that it
  found no valid device for the flash's controller, and none that the
  form refuses: no flash detected, and no write to the NOR.
- **The card.** One card, of 31,927,042,048 bytes, through the second
  reader throughout.

  | Image | Written | Read back after the write | Read back after its session |
  | --- | --- | --- | --- |
  | `anchor` | 2026-11-21, 21:56 to 22:22 | 22:22 to 22:28 | 2026-11-22, 16:18 to 16:25 |
  | `k3-breach-g1` | 16:26 to 16:51 | 16:51 to 16:58 | 21:48 to 21:54 |
  | `k3-breach-c` | 21:55 to 22:20 | 22:20 to 22:27 | 22:47 to 22:54 |

  Each write took 25 minutes (21.3 MB/s) and each read-back less than
  seven. Each read-back found the whole card's SHA-256 the image's,
  and each of the fourteen regions equal. A read-back after a
  session found a new insertion of the card, as it must after the
  card was out; a read-back after a write, the write's own insertion.
- **Before the first write**, the owner session compared the first
  12,582,912 bytes of the card in the reader with the image of the
  sitting's first run, and found them equal: the card in the slot was
  the one card, which the responsible human had left there while he
  used the board for other work.

### The record

`mvp/results/20261122-com260-m11b-second/` (156 files), made by
`tools/evidence.py --sitting` at the sitting's commit, in the
sitting's clone, after the card's last read-back:
`result=closed boots=5 readings=4 readbacks=3 stops=tool`. Its
bundle says `tool_tree=source` and `source_tree=clean`, and names one
commit as the source's, the sitting's, and the gate's.

- It holds the sitting's twenty step records; each boot's record,
  judged again with the same output, with the banner as the form
  took it, the capture from U-Boot's autoboot line on (269 lines,
  M-mode's commit records among them), and the measurement log's
  export; the four readings' records; the card's three writes and
  six read-backs; the gate's record's digests; and no raw capture.
- The one stop that it names, `tool`, is the first preflight's.
- **Read by the owner before it was committed:** the boot ROM's four
  lines, which hold no identifier; and a search of every file for a
  home path, the account's and the host's names, an IPv4 or MAC
  address, a USB ID, a reader's link, the board's SSH name, and any
  value of an MD5's form. Each such value is a staged image's MD5,
  which U-Boot prints for the load, or a PMP configuration word of
  M-mode's records (fifteen: three harts in five boots), but two: the
  build host's name in the banner of the board's own kernel, which
  the preflight keeps as MVP 1.0's records do. The preflight also
  keeps that kernel's boot identifier, as before.
- The record tool's own verify passes on it, at its commit and on the
  working branch.

### The words for the board's result (M11-B6)

**The claim's page**, `mvp/docs/claim-boundary.md`, in B-11's form:

- the clause keeps its words;
- a paragraph about the board follows it, B-11's first blockquote;
- the limit's second sentence begins "Under emulation,", and the
  limit gains six sentences at its end: B-11's second blockquote,
  with the words that the decision record of 2026-11-18 adds after
  "not one for each attempt;";
- a section names the board's four records: the two that the board
  rows cite, and the two runs that stopped.

The owner compared the words with the addendum and the decision
record by a script: the paragraph, the second sentence, and the six
sentences are equal to the plan's, and the seven clause rows and the
ten other sentences of the limit are unchanged.

**The ledger's second set:** three board rows after the clause's
seven, the parts of the page's paragraph, each with the method of a
diagnostic board run, and each citing a sitting's record that its
source's own tool made:

| Row | Part | Records cited |
| --- | --- | --- |
| M11-C08 | The images ran on one board with plain PMP, from a card with the vendor's boot chain and the project's firmware build | The first sitting's second run; the second sitting's second run |
| M11-C09 | M-mode's printed record showed the three harts confined, with their profiles' entries | The second sitting's second run |
| M11-C10 | The counts equal the sums that the test declares | The second sitting's second run |

Each row also cites, by SHA-256, the tools and the declarations that
its part rests on. The set has seventeen non-claim rows, one for each
sentence of the limit. No tool changed: the ledger tool has had the
rules for board rows since M11-B1, and its check and its self-test
pass with the rows in place.

**B-11's condition.** B-11 has its form "used only if M11-B's result
is accepted with every session passed". Each sitting's first run
stopped, and was corrected and run again from its start; in the runs
that the board rows cite, every session passed. The owner reads the
condition as met by those runs (departure 6).

**Other words.** The README's two entries under "Design", its table's
rows, and its open items 148 and 150; the guide's section 11; the
disclosure's section 15; on the planning side, the glossary's two
rows, the hardware page's two bullets, and the planning index's entry
for the addendum; and the root README's note on M11, which had said
that nothing of it had run on a board.

### What was run, and what was not

- **Run on the board:** the second sitting, as above: ten resets by
  the dongle, none by hand; the typing of the four readings alone;
  nothing typed while the card was in. One TCP connection to the
  board's SSH port by the owner session, outside the driver's steps
  (departure 1).
- **Run on the card:** three writes and six read-backs, through the
  card's tools.
- **Run at this range's commits**, from clean clones, on the
  workstation (2026-11-22 and 23):
  - at the commit of the claim's words and the ledger's rows
    (`0d5283cf`), the tool lock and a whole `./mvp/mvp check`
    (23:09Z to 23:40Z): 118 runs under QEMU in 129 attempts, 82 of
    them under the boundary; six sessions; the ledger's check, with
    ten claim rows and seventeen non-claim rows in its second set;
  - at the last commit before this section (`3cc98103`), which holds
    every change of the range but this page: the tool lock and a
    whole check (23:40Z to 00:11Z): 118 runs in 127 attempts, 82
    under the boundary, six sessions, the firmware's 44 test runs,
    the same line of the ledger's; the board gate on the host
    (00:11Z; nine steps, 38 outputs), with each of its four firmware
    builds equal to its sitting pin; and `evaluate`, with the board
    gate inside the evaluator (00:11Z to 00:41Z): 865 of 865
    recorded outputs, and 38 of 38 of the gate's, equal to the
    host's.

  In each check, each refused attempt is a run without the boundary
  that QEMU's firmware booted on a VS-domain hart, repeated. Of the
  865 outputs that a check records, 605 are equal, byte for byte, to
  those of the check at the sitting's signed commit, made in another
  directory: every flat image, boot image, device tree, firmware
  binary, and generated header among them. The 260 others are ELF
  files, tables, and lists that follow the build directory's name
  or name their commit.
- **The text-level checks** of each commit of the range (the
  release's scan, the text check of the added lines and of the
  message, and the publication gate's audit; with the ledger's
  check, lint, and the tool lock for a commit under `mvp/`, and the
  documentation's checks for the root README's): each passed
  (23:16Z to 23:41Z; this page's commit after it). Two commits were
  made again on the way. The root README's commit, in its first
  form, named the board's vendor in the note and in its message,
  which the release's scan refuses there; the note now says "one K3
  COM260 board". And the disclosure's section 15 did not at first
  name the root README's note and the planning pages among the
  owner's words; it was amended inside its own commit, and the two
  commits after it were made again with the same changes.
- **Not run:** the U-Boot rehearsal, the CHERI check, `verify`,
  `kernel-repro`, and the model's two gates. The range changes no
  tool, no image, no pin, and no path that the proofs' records bind:
  it adds a record, rows of the ledger's JSON with their rendering,
  and pages.
- **No counted line** was written: the soft limits stand where the
  section "M11-B5, first part" has them.

### Departures and readings for review

Each stands unless the responsible human says otherwise.

1. **The first preflight stopped, and the owner made one contact
   with the board outside the driver's steps.** The preflight's SSH
   connection timed out. The board had been reset a little before,
   not by the session, and was still booting its own Linux: the
   owner read the end of that boot in the serial log by the form of
   its lines, without printing the log. It then made one TCP
   connection to the board's SSH port, which answered with the
   server's banner, to be sure of the one retry that the driver
   allows, and ran the step again, which passed. The responsible
   human said afterwards that the session may use SSH to the board
   as it needs. The reset before the sitting is outside the
   sitting's audit: its banner came before `begin`.
2. **His word that the board was free was not taken for his word for
   the sitting.** He said that the board was free nine hours before
   he gave his word for the sitting; the owner started no board step
   in between.
3. **Long waits between the sessions.** More than five hours passed
   between the first session and the second, and nearly an hour
   between the second and the third; the board waited at U-Boot's
   prompt, and the card in the reader. The sitting's plan has no
   limit on such a wait. Nothing was printed, and nothing reset the
   board, in either.
4. **The card's steps between two sessions ran from a script of the
   owner's**, which gave the dry run's confirmation to the write. The
   owner did not read the dry run's output between the two. The
   read-back before the dry run had shown the card in the reader to
   be the one card with the last session's image, and the write's
   own checks are the tool's.
5. **The owner printed M-mode's count lines from the private
   captures** while the sitting ran, to see them, and the forms'
   verdict lines. The record's excerpts hold the same lines. It
   printed no other line of a capture, and nothing of a reading.
6. **B-11's condition "with every session passed" is read as met**
   by the sittings' second runs (above). The two stopped runs are
   recorded, and the claim page names them.
7. **The methods of the board rows.** Each has the method of a
   diagnostic board run. M11-C08 and M11-C09 also have the semantic
   checker's, for the form and the boundary's judge; M11-C10 also
   has the adversarial test's, for the hostile-monitor images. The
   ledger tool admits those methods in a board row; B-11 names none.
8. **The hardware page's bullet on the X100's PMP now gives the
   banner's entry count, grain, and address bits** as the project's
   firmware reports them on one board, for its boot hart. They were
   in the decision record since the first sitting, and the page had
   still called the grain not established.
9. **The card reader's access rule is still installed.** The driver
   says, at the last sitting's end, that it is to be removed, and
   prints the command, which is the responsible human's to run.
10. **After the second session the card reached the reader only on
    a second request.** The card's removal from the board was
    recorded on his word; the reader showed no card until he put it
    in, two minutes later. No step read the reader in between.

### What is not shown

- **An attempt's effect on the board.** Nothing read the machine
  from outside, and no hostile-monitor image ran there with the
  boundary built off. What M-mode printed is the only witness, and
  code on the confined control hart could print the same lines.
- **The hostile-monitor images' own records** of their attempts, and
  with them the trap of the cache-block instruction.
- **That a counted fault on a device's register was PMP's.**
- **Smepmp on the board.** The runs use plain PMP.
- **The state of the thirteen harts that the monitor does not use**,
  and anything of the vendor's two real-time cores, its boot chain,
  or the resident firmware in the NOR.
- **The board's vector length**, and the heap's use after the banner.
- **More than one board, or more than one day.** Three boots of one
  scenario and one boot of each hostile-monitor image.
- No claim of MVP 1.0 changes. The claim page's words for the board
  are proposed, with their limit.
