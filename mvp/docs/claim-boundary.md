<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The physical boundary: the M11 candidate's claim

This page is the single statement of the claim for the M11 candidate,
the physical boundary under the monitor. It is not part of MVP 1.0: the
release's claim is [claim.md](claim.md), which this page does not
change, and the released images have no such boundary. The words below
are those that the [M11 plan](../../planning/mvp-m11-plan.md) fixes
("Claim text"), in the form for a candidate in which all three of the
monitor's harts are confined.

> In QEMU, under a firmware build of the project's own (OpenSBI at the
> commit that the ledger names, with the project's M-mode additions),
> each of the two harts that run a VS domain is confined before its
> first guest entry, and the control hart at the end of its boot work,
> before it reads anything that they write: each to a physical access
> profile that M-mode installs from a partition descriptor built
> offline. The five harts that the monitor does not use stay stopped.
> In the hostile-monitor test images, with plain PMP and with Smepmp,
> each tested attempt by HS-mode code on a confined hart to reach
> memory outside its profile, or to make a firmware call outside its
> list, had no effect and was counted by M-mode. With the boundary
> built off, each of those memory attempts that the tests can
> discriminate took effect.

## Required limit

> This is emulation evidence, by adversarial tests and a semantic
> checker; nothing is proved. PMP's behaviour is the emulator's, which
> has no cache. The firmware, the hardware's physical memory
> protection, the descriptor's generator, the boot chain, and the
> monitor's boot code before each hart's activation are trusted for the
> containment, and the offline check of the descriptor for the
> evidence. The tests are a list of attempts made by a test hook: not
> every access, and not an exploit. The runs with the boundary off do
> not cover the attempts on M-mode's own memory, on another hart's
> interrupt file, or on the machine's power device, nor the jumps, the
> cache-block invalidate, and the calls. A breached hart keeps its own
> VS domain and the mailboxes that it writes, and may stop or withhold
> its work. The control hart stays a hub between the others. A
> breached control hart can also
> pause or terminate a VS domain, see every line that any VS domain
> prints, type into a VS domain that is granted console input, with
> that VS domain's shell's reach, print anything, and shut the system
> down. What a breached hart prints is not evidence: the evidence is
> M-mode's counts and the reads from outside the machine. Nothing here
> protects against cache or timing channels between harts, or against
> a defective firmware. The released MVP 1.0 images have no such
> boundary.

## The candidate

The candidate is one tree of this repository: the tree at which the
gates pass. The ledger names it once they have passed, and this page
then names it too. Until then, the ledger's rows cite the tools and
tests of the tree that holds them, and no gates' record.

## Where the evidence is

The claim ledger holds this claim's rows as a set of their own, apart
from the release's: [claim-ledger-boundary.md](claim-ledger-boundary.md),
rendered from [`claim-ledger.json`](claim-ledger.json). Each part of the
clause has a row with its methods and its evidence, each artifact with
its SHA-256; each sentence of the limit has a row with a note.
`tools/claim-ledger.py check` checks that set, and that its parts are
this page's clause and its sentences this page's limit, word for word.
The evidence record is
[`planning/mvp-m11-evidence.md`](../../planning/mvp-m11-evidence.md),
and the [guide](guide.md)'s section 10 says how to build the firmware,
make the runs, and read their records. Every part of the claim is read
with the [required limit](#required-limit).
