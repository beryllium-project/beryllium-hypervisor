<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# The verifier at the CHERI integration's gates

The records of `./mvp/mvp verify`, the eighth of release candidate 4's
gates, as the CHERI integration's work package CI-6 ran them on the
research branch `cheri-platform`.
- **Where it ran.** A clean local clone at commit
  `759f9d888fa9da065eb9132f6a232505b5f56e70`, before that commit was
  signed off. Its tree is `06468512ea19bb737d13530af30ef21a3ca14aa7`,
  which the signed commit keeps.
- **When.** 2026-11-09, 08:01 to 11:52 UTC (`wall_seconds=13843`).
- **The image.** The verifier image
  `localhost/beryllium-mvp-verifier:ce7ca11cb755-b71721530f48-36eaf6d2362b`.
- **The specification.** Revision 1, whose frozen copy is
  `mvp/verify/specification-93a8d136.md` (SHA-256 `aeb75682…`).
- **The target digests.** `mvp/verify/target-digests.txt`, re-written
  against `5980edff` because the CHERI variant changes `mvp-sbi.c` and
  `mvp.h`.

A verifier run is evidence of these tools on these bytes, never a proof
of the whole monitor. WP and CN remain OPEN, and CBMC's results are
bounded model checks.

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

**Every suite's verdict and count equals the release's and release
candidate 4's:**

| Suite | Verdict and counts |
| --- | --- |
| sequences | PASS `elfs=2 symbols=55 lines=206`, with the path-dependent `elf_files` field set aside |
| digests | PASS `files=13` |
| token-equal | PASS `tokens=686`, range `201-324` |
| qualify | PASS `arms=9 qualified=6` |
| litmus | PASS `premises=5 never=5` |
| WP | OPEN `goals=134 proved=130 rounds=1 killed=18` |
| CN | OPEN `goals=55 proved=5 killed=1 unobservable=1` |
| CBMC Leaf A | SUCCESSFUL `properties=336 killed=22 unobservable=1 contract-findings=1 unwind=4` |
| The ring | OPEN `properties=14931 checked=13547 open=1384 killed=22 unobservable=1 harness-findings=1` |

**Comparison with the release's record.** The same run metadata are set
aside as the release's README sets aside: start times, durations,
solver-run counts, the moments a solver timed out, and the solver that
answered each ring mutant's run first. Once they are set aside, 30 of
the 32 files besides this README equal the files of the same name in
the release's record and in release candidate 4's
([`20261105-verify-rc4/`](../20261105-verify-rc4/README.md)), byte for
byte, and two differ.

The two remaining differences come from the CHERI variant's lines in
`mvp/src/mvp.h`, not from load. The CHERI integration's CI-5 diagnosed
them with single CBMC runs in the same image:
- **Leaf A's `rounds.txt`:** `check_frame`'s MiniSAT run times out at
  300 s, where the records' answered in about 5 s, and cvc5 then closes
  those goals.
- **The ring's `defect-room.txt`:** the same failing property is
  confirmed with the same four contradictions, but with other
  counterexample values.

Both reproduce with this branch's `mvp/src` and vanish with MVP 1.0's.
MVP 1.0's `mvp-sbi.c` with this branch's `mvp.h` reproduces the timeout.
`mvp.h`'s added lines are inactive in the plain build, and the plain
build's preprocessed leaves are MVP 1.0's, but they still change CBMC's
encoding. No verdict or count changes.
