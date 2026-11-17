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
