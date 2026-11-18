<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# The verifier at the M11 candidate's gates

The records of `./mvp/mvp verify`, the last of the M11 candidate's nine
gates to run. The candidate is the fourth of the points at which the
M11 plan's D-11 has every arm run again.
- **Where it ran.** On the workstation `l1`, the host that the M11
  plan's decision record names for `verify`, in a clean local clone at
  commit `2fb5c69d34efb492fd66aa7d30bc4168c4e37948`, before that commit
  was signed off. Its tree is
  `7a826991eb80d19c03caae883c19271a52f42963`, the candidate's tree,
  which a sign-off keeps.
- **When.** From 23:32 UTC on 2026-11-17 to 05:03 UTC on 2026-11-18
  (`wall_seconds=19847`).
- **The image.** The verifier image
  `localhost/beryllium-mvp-verifier:ce7ca11cb755-b71721530f48-36eaf6d2362b`,
  which the host held. The clone's package and source caches were
  copies of the host's earlier ones, and each file in them was admitted
  by its SHA-256 in the closure (`mvp/README.md`, open item 133, says
  why a run from an empty cache stops).
- **The specification.** Revision 1, whose frozen copy is
  `mvp/verify/specification-93a8d136.md` (SHA-256 `aeb75682…`).
- **The target digests and the litmus record.** Both were written at
  `d6a1aa02`, the signed commit before the candidate's last three,
  whose monitor sources and build rules are the candidate's. The litmus
  record was written from another clone's build, so the summary's
  `elf_files` field reads `differ(path-dependent)`: the two monitors'
  ELF files hold their build directory's name, and the cited sections
  are compared byte for byte.

A verifier run is evidence of these tools on these bytes, never a proof
of the whole monitor. WP and CN remain OPEN, and CBMC's results are
bounded model checks. None of it is about M11's boundary: the
confinement is not modelled, and no arm runs on it (the M11 plan's
D-11).

The 33 files have the shape of the release's record,
[`20261108-verify-release/`](../20261108-verify-release/README.md):
- `verify.txt`;
- `qualification.txt` and `.json`;
- `litmus.txt`;
- the six retained records of each Leaf A arm;
- the ring's ten text and JSON records. These hold no raw logs or mutant
  sources, and `defect-room.txt` carries its bounded excerpt.

The two cache paths in `verify.txt` are relative to the checkout, and
nothing else is rewritten. No file holds a home path, IP address, ssh
target, or serial number.

**Every suite's verdict and count equals those of the last record in
this tree,
[`20261109-verify-cheri-integration/`](../20261109-verify-cheri-integration/README.md):**

| Suite | Verdict and counts |
| --- | --- |
| sequences | PASS `elfs=2 symbols=55 lines=206`, with the path-dependent `elf_files` field set aside |
| digests | PASS `files=13` |
| token-equal | PASS `tokens=686`, range `204-327` (the same tokens, three lines lower since M11-4) |
| qualify | PASS `arms=9 qualified=6` |
| litmus | PASS `premises=5 never=5` |
| WP | OPEN `goals=134 proved=130 rounds=1 killed=18` |
| CN | OPEN `goals=55 proved=5 killed=1 unobservable=1` |
| CBMC Leaf A | SUCCESSFUL `properties=336 killed=22 unobservable=1 contract-findings=1 unwind=4` |
| The ring | OPEN `properties=14931 checked=13547 open=1384 killed=22 unobservable=1 harness-findings=1` |

The summary has one line more than that record's: the list of solver
runs at or near their time limit, which `verify` writes since M11-2
(`runs=4419 near=0 crossed=263`). Since M11-3 every time limit of the
arms is twice the release's.

**Comparison with M11-4's point**, the last of D-11's points before
this one, with the same leaves' inputs. Its record is not in this
tree; the evidence record, `planning/mvp-m11-evidence.md`, describes
it. The same run metadata are
set aside as the release's README sets aside. Once they are, 27 of the
32 files besides this README equal that point's, 12 of them byte for
byte, and five differ:
- **`litmus.txt`:** the digests of the litmus record and of the five
  tests, which were written again at the candidate. Each test's result
  and its states are that point's.
- **`verify.txt`, `qualification.txt` and `.json`, and Leaf A's
  `wp/mutants.txt`:** three prover runs that are recorded as timeouts
  at that point, at the 120 s limit, are not here.
  - One goal of the WP qualification's `wrong-implementation` case is
    recorded as failed, where it was a timeout. The case is unproved
    either way, as it must be.
  - Mutant m16 is killed by the same goals; for one of them the
    prover's run is recorded as failed, where it was a timeout.
  - Mutant m17 is killed by one goal at the limit, where two were: the
    other is proved here, in 24 s.
  - So the list of runs at their limit has 263 where it had 265.

  No verdict and no suite's count changes. These are effects of a time
  limit and the host's load, not of the code.

**Comparison with the last record in this tree.** Once the same run
metadata are set aside, 16 of the 32 files equal those of
`20261109-verify-cheri-integration/` (7 byte for byte), and 16 differ,
each by something that M11 changed and that its evidence record tells
at the point where it changed:
- **The arms' time limits**, twice the release's since M11-3: in the
  arms' own notes, and in the runs that now end inside a limit. Leaf
  A's `check_frame` run under MiniSAT completes, where it had timed out
  and cvc5 had closed its goals; three cases in which the prover must
  fail are recorded as failed, where they were timeouts; and round 0 of
  the WP arm proves 1,088 of its split obligations where it had proved
  1,080, with the same goals proved and open.
- **The leaf's place in its file**, three lines lower since M11-4: in
  the summary, in CN's transcription record, in each mutant's place in
  the three arms' mutant records, and in the unreachable statements
  that the WP vacuity record lists.
- **The qualification's expectations**, whose digest follows the
  limits.
- **The litmus record's and the tests' digests**, written again at
  each of M11's points.
- **The ring's recorded finding `room`**: the same assertion and
  reason, with other counterexample values since M11-4 changed a header
  that the ring's header includes.
- **The three prover runs** named above.
