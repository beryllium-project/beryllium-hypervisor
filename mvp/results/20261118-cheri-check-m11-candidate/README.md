<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# The CHERI check at the M11 candidate's gates

[`summary.txt`](summary.txt) is the summary that
`mvp/tools/cheri-check.sh` wrote when it ran among the M11 candidate's
nine gates, on 2026-11-17, from 23:08 to 23:32 UTC: after the seven
whose record is
[`../20261118-m11-candidate/`](../20261118-m11-candidate/), and before
`verify`
([`../20261118-verify-m11-candidate/`](../20261118-verify-m11-candidate/README.md)).
The M11 plan's D-11 makes the check a gate of the candidate, and its
failure there a stop (stop 10).
- **Where it ran.** A clean local clone, of its own, at commit
  `2fb5c69d34efb492fd66aa7d30bc4168c4e37948`, before that commit was
  signed off. Its tree is `7a826991eb80d19c03caae883c19271a52f42963`,
  the candidate's tree, which a sign-off keeps.
- **The CHERI stack.** It is outside the MVP's tool lock. The check used
  the stack built in the CHERI research repository, by path, with
  `cheri/pins.txt` as its lock. The stack root's absolute path is
  written `<stack-root>`; nothing else in the summary is changed.

The check passed all three parts (`BE_MVP_CHERI_CHECK: PASS`, 1,454 s):
1. **The CHERI-aware monitor with the CHERI Linux guests.**
   - The 24 checks of `make check` that the variant runs, among them
     the five that M11 brought.
   - The guests' build against `mvp/guest/cheri-pins.txt`, and the
     firmware's pin.
   - 56 QEMU runs in 63 attempts, the CHERI rules' 94 capture
     mutations, and six sessions.
2. **The plain variant.** Its 222 boot images equal, byte for byte, a
   second build of the same commit in another directory, which is the
   check's reference on the development line. No earlier record of the
   gates has the candidate's build inputs, so the check compared none
   (`records=none`). The 222 digests are also those of the same images
   in the gates' record beside this one (`host/images.sha256` there),
   which a separate build made.
3. **The CHERI-aware monitor with the Linux guests.** The image check,
   50 QEMU runs in 60 attempts, ten capture mutations, and six sessions
   in seven attempts.

Every refused attempt is a run that the emulator's firmware booted on a
VS-domain hart, repeated as since M0.

The CHERI variant is built without M11's boundary: its emulated
platform has another firmware. The CHERI work runs on CHERI v0.9.3
under emulation. None of it is evidence for MVP 1.0's claim
([`mvp/docs/claim.md`](../../docs/claim.md)), and none for the M11
candidate's ([`mvp/docs/claim-boundary.md`](../../docs/claim-boundary.md)).
