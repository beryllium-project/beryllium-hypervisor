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
printed; it makes no claim beyond those lines. Every run here is on the
development host `lx2` (an Intel i7-10610U, 4 cores and 8 threads,
46 GB, Fedora 44, the performance profile) and under emulation; nothing
here ran on a board.

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
