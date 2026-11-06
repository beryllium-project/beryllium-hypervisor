<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The verifier at the release candidate 4 candidate tree (M10-5)

The records of the second `./mvp/mvp verify` run the M10 plan requires,
from a clean standalone checkout of exact candidate tree
`a6eaa88501b1d08b9e83c734d692c82376117e77` (`X4`), made 2026-11-05
13:51 to 17:32 UTC (`wall_seconds=13254`) in the accepted verifier image
`localhost/beryllium-mvp-verifier:ce7ca11cb755-b71721530f48-36eaf6d2362b`,
against the specification's Revision 1 (`93a8d136`, SHA-256
`aeb75682…`). It is the gate run, after M10-2's base-tree run under
`20261104-verify-rc4-base/`; a verifier run is evidence of these tools on
these bytes, never a proof of the whole monitor. WP and CN remain OPEN;
CBMC's results are bounded model checks.

The 33 files have the same shape as the base-tree record: `verify.txt`;
`qualification.txt` and `.json`; `litmus.txt`; the six retained records
of each Leaf A arm; and the ring's ten text/JSON records (no raw logs or
mutant sources; `defect-room.txt` carries its bounded excerpt and says
so). The two cache paths in `verify.txt` are relative to this checkout;
nothing else is rewritten. No file holds a home path, IP address, ssh
target, or serial number.

Every suite's verdict and count equals the base run's and the accepted M8
result's: sequences PASS (`elfs=2 symbols=55 lines=206`, the path-dependent
`elf_files` field set aside); digests PASS `files=13`; token-equal PASS
`tokens=686`, range `201-324`; qualify PASS `arms=9 qualified=6`; litmus
PASS `premises=5 never=5`; WP OPEN `goals=134 proved=130 rounds=1
killed=18`; CN OPEN `goals=55 proved=5 killed=1 unobservable=1`; CBMC
Leaf A SUCCESSFUL `properties=336 killed=22 unobservable=1
contract-findings=1 unwind=4`; the ring OPEN `properties=14931
checked=13547 open=1384 killed=22 unobservable=1 harness-findings=1`.
Timings, digests, and solver-run counts are run metadata, not verdicts.
