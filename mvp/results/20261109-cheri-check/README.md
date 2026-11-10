<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# The CHERI check at the CHERI integration's gates

[`summary.txt`](summary.txt) is the summary that
`mvp/tools/cheri-check.sh` wrote when the CHERI integration's work
package CI-6 ran it on 2026-11-09, from 07:05 to 07:25 UTC, before
release candidate 4's eight gates
([`../20261109-cheri-integration/`](../20261109-cheri-integration/)).
- **Where it ran.** A clean local clone of the research branch
  `cheri-platform` at commit
  `759f9d888fa9da065eb9132f6a232505b5f56e70`, before that commit was
  signed off. Its tree is `06468512ea19bb737d13530af30ef21a3ca14aa7`,
  which the signed commit keeps.
- **The CHERI stack.** It is outside the MVP's tool lock. The check used
  the stack built in the CHERI research repository, by path, with
  `cheri/pins.txt` as its lock. The stack root's absolute path is
  written `<stack-root>`; nothing else in the summary is changed.

The check passed all three parts (`BE_MVP_CHERI_CHECK: PASS`, 1,242 s):
1. **The CHERI-aware monitor with the CHERI Linux guests.**
   - Every check of `make check` that the variant runs.
   - The guests' build against `mvp/guest/cheri-pins.txt`, and the
     firmware's pin.
   - 56 QEMU runs, the CHERI rules' 94 capture mutations, and six
     sessions.
2. **The plain variant.** Its 162 boot images equal, byte for byte, a
   build of the release's commit `0b2a4367` and the release's record,
   [`../20261108-release/`](../20261108-release/).
3. **The CHERI-aware monitor with the Linux guests.** The image check,
   50 QEMU runs, ten capture mutations, and six sessions.

The CHERI work runs on CHERI v0.9.3 under emulation, and none of it is
evidence for MVP 1.0's claim ([`mvp/docs/claim.md`](../../docs/claim.md)).
