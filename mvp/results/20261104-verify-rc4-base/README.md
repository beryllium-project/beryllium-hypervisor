<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The verifier at the M10 base tree (M10-2)

The records of one `./mvp/mvp verify` run, the M10 plan's re-proof at the
base tree (`planning/mvp-m10-plan.md`, D-2, work package M10-2), made on
branch `beryllium/mvp-m10-wp2` at exact commit
`52e816cb8c18f6a18330a9e93ed0f4d7abc90a53`, whose `mvp/src` and
`mvp/Makefile` equal the M10 plan's acceptance record `b5842520`'s: the
litmus sequences re-extracted from that tree's monitors (`5e4110eb`), the
WP arm's line note (`c43ba773`), and `mvp/verify/target-digests.txt`
re-written at target `c43ba773` (`52e816cb`; the plan's Q3). The run
started 2026-11-05T03:03:28Z and ended 06:49:23Z (`wall_seconds=13554`)
in the accepted verifier image
`localhost/beryllium-mvp-verifier:ce7ca11cb755-b71721530f48-36eaf6d2362b`,
against the specification's Revision 1 (`93a8d136`, SHA-256
`aeb75682…`). It is the base run; the gate is the plan's second run, at
`X4` from a clean checkout, under `<date>-verify-rc4/` (Q13). A run of
the verifier is a record of these tools on these bytes; the WP and CN
arms are OPEN, both CBMC runs bounded model checks, never proofs.

| File | What |
| --- | --- |
| `verify.txt` | the run's `BE_MVP_VERIFY:` lines: the caches, the image, the tools, the specification, each suite's result line, the wall time, the verdict |
| `qualification.txt`, `qualification.json` | the qualification matrix (D-7 item 2), per arm and solver |
| `litmus.txt` | the ordering premises L1 to L5 under herd7 7.58 |
| `leaf-a/wp/`, `leaf-a/cn/`, `leaf-a/cbmc/` | each Leaf A arm's six records, copied by its runner's `--retain` |
| `leaf-b/` | the ring's text records from `build/mvp/verify/cbmc-ring/`, as M8's `20261103-verify-r1/leaf-b/` holds them: no logs, no mutant sources; `defect-room.txt` keeps, of each trace, the states in `main` or assigning a call's return value and the violated property, and says so |

Redaction: in `verify.txt` the two cache paths were absolute paths under
the checkout and are written relative to it; nothing else was changed.
No file holds a home path, an address, or an ssh target.

Every suite's verdict and count equals the accepted M8 result's at its
gates commit `f1813841` (`planning/mvp-m8-evidence.md`): the differences
are the token gate's line range (`mvp/src/mvp-sbi.c:201-324`, M9's one
added line before Leaf A), the sequences line's reported, path-dependent
`elf_files` field, the line numbers the records cite in `mvp-sbi.c`
(each one more), the timings, the ring's per-mutant solver-run counts,
and the number of trace states the room record's excerpt keeps (95 of
241, where M8's kept 123 of 241).
