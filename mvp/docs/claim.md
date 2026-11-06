<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The Beryllium MVP 1.0 claim

This is the single statement of the claim for MVP 1.0 release candidate
4, over its candidate tree `X4`, exact commit `a6eaa885` (the eight gates
passed from a clean checkout and the board session ran its images): every
other release surface links here rather than restating it, and the
[claim ledger](claim-ledger.md)'s release table names `X4` and the
responsible-human accepted release-candidate commit `RC4`, exact commit
`d70a8535`, accepted 2026-11-05, which adds the final board record,
evidence record and ledger updates over it. The ledger is the one source
every surface is checked against (`tools/claim-ledger.py check`,
its release-surfaces check). Release
candidate 1, exact commit `c5df0cfa` (board runs launched by Linux kexec
from the board's Fedora host), release candidate 2, exact commit
`3867c66c` (the first boots from system reset), and release candidate 3,
exact commit `89ef04e9` (the MVP core profile, accepted 2026-10-31), are
accepted history; each holds its own claim text.

> In QEMU and on one SpacemiT K3 COM260 board (harts 0 to 2 of eight,
> statically assigned, one control hart and one hart per domain; booted
> from system reset by the board's installed firmware and U-Boot, which
> loaded the MVP image from a Beryllium partition on the board's NVMe
> under a boot command installed in U-Boot's saved environment for the
> campaign and restored after it; the firmware recorded by its SBI
> identity, OpenSBI 1.6), the Beryllium MVP runs
> Linux guests, one per hart, in separate G-stage domains. In the
> `te-poc` and `anchor` scenarios, the domains' memory authority is
> specified by a declarative policy in the Type Enforcement family,
> checked offline against the sealed configuration, and enforced through
> derived mappings; every tested access not authorized by the declared
> rights was denied, logged, and delivered to the offending guest as a
> fault; and in `anchor`, the untrusted Linux domain's tested attempts to
> read the protected domain's secret, to alter its result, and to reach
> its private window and the monitor's region were each denied, while
> the protected domain's measurement stayed unaltered. Over the one
> serial console an operator may type into a shell in a domain the
> configuration grants console input, selecting the domain by a focus
> sequence; the control hart delivers each typed byte to the selected
> domain and to no other, and no guest byte outside printable ASCII, and
> no guest byte at the start of a line, reaches the terminal. For the
> Linux-guest runs the ledger identifies, before any domain runs, the
> control hart records in a bounded log the digests it computes over what
> it placed or sealed on that platform (the sealed configuration's core
> identity and console grants, each domain's kernel Image and device tree
> as placed, and `anchor`'s secret page) and the identities the build
> carries, extends one register per stream with the measured records'
> digests only, and compares each domain's launch register with the
> image's expected value before that domain starts; the checker rebuilds
> the log from its printed lines, replays the registers, recomputes every
> digest from the build's inputs, and compares every record with the
> image's post-link reference.

## Required limit

This is unit-test, emulation, and diagnostic bring-up evidence for one
board, one reported SBI implementation identity and version, and one
U-Boot build as its banner reports it, made at the exact commits the
ledger names. The board's installed firmware and U-Boot, identified by
their banners and SBI identity, were the same before, during, and after
the campaign; no campaign step wrote them. U-Boot's saved environment,
data in the same NOR, was changed for the campaign and restored: the
environment U-Boot printed at a fresh prompt after the restore equalled
the pre-session record, normalized as the M5 plan states; the stored
bytes were not compared. The stored copy may also differ from the
pre-session one by U-Boot's runtime `fdtcontroladdr`, which `saveenv`
stores with the rest. The `two-guests` scenario exercises the substrate
(two Linux domains on two harts, the boot barrier, the rings, the
console) and has no policy.
The guests are unmodified upstream Linux `v7.2` kernels built from a
recorded configuration with an in-tree `nolibc` init and, for M2's
domains, one module under its own license. The guests' software is a
test input: unmodified Linux `v7.2`, a static BusyBox with musl from
pinned sources, and the in-tree `nolibc` programs; a shell in a domain
is a demonstration, not evidence that arbitrary guests are contained.
The operator at the console and the typing tool are trusted inputs: what
they type, and what they relay from one domain's output into another's
input, is outside the claim; so are the loss of typed bytes the firmware
console does not buffer and the availability of a domain that fills its
output ring. The policy-to-manifest
relation and the static hart binding are proved only in the abstract
model; the MVP's offline checker is shown to agree with that model on the
instances and a seeded mutation set, and is not the proved function. The
monitor's implementation is unproved: the boot barrier, the rings, the
IPI protocol, the control loop, the G-stage builder, the denial path, the
management decision, and the measurement are covered by host tests,
image and capture checks, emulation, and the board runs, and by nothing
else; R7's bounded proof covers the accepted R5 single-hart bytes only.
Isolation is architectural only: the denials are the declared, tested
accesses (stores to declared pages beyond the accessor's rights, and
loads from addresses no root of the accessor maps); the result the
protected domain writes to the response page is read by the host by
design; nothing is claimed about untested accesses, microarchitectural
channels, availability, or the harts that are never started, whose state
is a firmware assumption. The log is a local identity, not attestation:
it has no key, nonce, freshness, or root of trust, so code able to alter
the monitor can fabricate its records, and a record does not show the
bytes unchanged after the point of measurement; the monitor's digest of
its own text and read-only data is a self-report, compared offline and
gating nothing. On the board, U-Boot, identified by its banner and
unmeasured, prints an MD5 of the loaded boot image, which the checker
holds as attribution of the run to its image and as nothing more; no
loader observation exists in direct QEMU boots, and the U-Boot rehearsal
records a CRC-32 separately. SPL, OpenSBI, and U-Boot are unmeasured.
The board's lifecycle and debug state were not determined as of
2026-11-05; no probe was performed. The hart assignment is
fixed before any domain runs;
nothing is claimed about migration, overcommit, or dynamic multicore
operation. It is not formal verification, hardware validation, or
certification.

## Forbidden phrasings

Each phrasing below is matched case-insensitively, on whitespace-normalized
text with hyphens and spaces equivalent, as a whole phrase at word
boundaries, so "production" does not match "reproduction" and "certified"
does not match "certified-free" but does match "Certified"; this section is
the only place in a release surface where these phrasings may appear, and
`tools/claim-ledger.py` reads the list from it.

- literal: "formally verified"
- literal: "verified hypervisor"
- literal: "proven secure"
- literal: "hardware-validated"
- literal: "multicore-validated"
- literal: "certified"
- literal: "attested"
- literal: "confidential computing"
- literal: "SELinux for RISC-V"
- literal: "FLASK for RISC-V"
- literal: "XSM for RISC-V"
- literal: "production-ready"
- literal: "production"
- literal: "secure hypervisor"
- literal: "trusted execution environment"
- literal: "TEE"
- literal: "guarantees isolation"
- literal: "isolation guarantee"
- literal: "tamper-proof"
- literal: "tamper-resistant"
- literal: "secure boot"
- literal: "measured boot"
- literal: "verified boot"
- literal: "remote attestation"
- literal: "memory-safe"
- literal: "side-channel resistant"
- literal: "constant-time"
- literal: "noninterference"
- literal: "capability-based"
- literal: "zero-trust"
- literal: "complete isolation"
- literal: "full isolation"
- literal: "no known vulnerabilities"
- literal: "audited"
- literal: "independently reviewed"
- conditional: "secure against a compromised host" requires: "It is not formal verification, hardware validation, or certification."
- conditional: "SMP" requires: "static hart ownership"
- conditional: "multicore hypervisor" requires: "static hart ownership"
- review: TE presented as a runtime mechanism Beryllium selected
- review: a Helium, Model, or R-series result presented as an MVP result
- review: M8's pilot presented as a proof of the C: its outcome is inconclusive (no arm met the M8 plan's D-7 on Leaf A; WP open on four goals that time out, CN open on tool limits, CBMC a bounded model check at unwind 4; the ring's bounded check open at its bound), so no monitor function has a C-level contract proof and the required limit's sentence on the implementation stands unnarrowed

The first 11 literals, the 3 conditional phrasings, and the first 2 review
items are the MVP plan's list, with its "SELinux, FLASK, or XSM for RISC-V"
written as three literals; the M4 plan adds the other 24 literals, in 14
groups; the M8 plan's D-11 adds the third review item, which records the
pilot's outcome. A conditional phrasing may appear outside this section only in a
document that also carries its condition outside this section: the required
limit's closing sentence, or the words "static hart ownership". The review
items are not matched as text: the responsible human's review judges them,
and the claim ledger names them.

The M4 plan forbids "noninterference" stated as a result; the checker
matches it as a plain literal, so the word appears in no release surface
outside this section.

## Where the evidence is

The [claim ledger](claim-ledger.md) maps every claim to its method, its
evidence (each artifact with its SHA-256 and the exact commit of its
evidence), and its non-claim, and lists the unproved boundary;
`tools/claim-ledger.py check` checks its schema, every artifact's path and
SHA-256, every commit it names, its rendering, and the release surfaces'
naming of the current candidate. The board runs the ledger cites were
launched by Linux kexec in the M0 to M2 campaigns and release candidate
1's (the rows that are those campaigns' own are marked historical), and
booted from system reset under the board policy in release candidate 2's
session (M5-7), release candidate 3's (M6-7), and release candidate 4's
(M10-6: the probes, the scenarios, the negatives, and the three shell
images with their sessions typed under the board policy's item 8, the
measurement log judged in every run). The evidence records are
`planning/mvp-m4-evidence.md` (release candidate 1),
`planning/mvp-m5-evidence.md` (release candidate 2),
`planning/mvp-m6-evidence.md` (release candidate 3), and
`planning/mvp-m10-evidence.md` (release candidate 4, added by the
release-candidate commit over the candidate tree). Every claim here is
read with the [required limit](#required-limit).
