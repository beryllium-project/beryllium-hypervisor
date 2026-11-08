<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The verifier at the release's step 4

The records of `./mvp/mvp verify`, the eighth of the gates the release
path's step 4 ran (`RELEASE.md`, "Gate results (step 4)"), from a clean
local clone of this repository at commit
`d6f96ddd56533853f52f201536d9ab04897433d9`, made 2026-11-08 02:10 to
05:54 UTC (`wall_seconds=13396`) in the verifier image
`localhost/beryllium-mvp-verifier:ce7ca11cb755-b71721530f48-36eaf6d2362b`,
against the specification's Revision 1, whose frozen copy is
`mvp/verify/specification-93a8d136.md` (SHA-256 `aeb75682…`). A verifier
run is evidence of these tools on these bytes, never a proof of the
whole monitor. WP and CN remain OPEN; CBMC's results are bounded model
checks.

The 33 files have the shape of release candidate 4's record,
[`20261105-verify-rc4/`](../20261105-verify-rc4/README.md):
`verify.txt`; `qualification.txt` and `.json`; `litmus.txt`; the six
retained records of each Leaf A arm; and the ring's ten text/JSON
records (no raw logs or mutant sources; `defect-room.txt` carries its
bounded excerpt and says so). The two cache paths in `verify.txt` are
relative to the checkout; nothing else is rewritten. No file holds a
home path, IP address, ssh target, or serial number.

Every suite's verdict and count equals release candidate 4's: sequences
PASS (`elfs=2 symbols=55 lines=206`, the path-dependent `elf_files`
field set aside); digests PASS `files=13`; token-equal PASS
`tokens=686`, range `201-324`; qualify PASS `arms=9 qualified=6`; litmus
PASS `premises=5 never=5`; WP OPEN
`goals=134 proved=130 rounds=1 killed=18`; CN OPEN
`goals=55 proved=5 killed=1 unobservable=1`; CBMC Leaf A SUCCESSFUL
`properties=336 killed=22 unobservable=1 contract-findings=1 unwind=4`;
the ring OPEN
`properties=14931 checked=13547 open=1384 killed=22 unobservable=1 harness-findings=1`.
Once the start times, the durations, the CBMC solver-run counts, the
moments a solver timed out, and the solver each ring mutant's run used
(the one that answered the unmodified leaf's same run sooner) are set
aside, each of the other 32 files equals the file of the same name in
release candidate 4's record, byte for byte. Timings, digests, and
solver-run counts are run metadata, not verdicts.
