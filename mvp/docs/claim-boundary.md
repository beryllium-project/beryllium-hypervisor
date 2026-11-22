<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com> -->

# The physical boundary: the M11 candidate's claim

This page is the single statement of the claim for the M11 candidate,
the physical boundary under the monitor. It is not part of MVP 1.0: the
release's claim is [claim.md](claim.md), which this page does not
change, and the released images have no such boundary. The words below
are those that the [M11 plan](../../planning/mvp-m11-plan.md) fixes
("Claim text"), in the form for a candidate in which all three of the
monitor's harts are confined; and, for the runs on one board, those
that the plan's
[board addendum](../../planning/mvp-m11-board-addendum.md) fixes
("The words for a board result"), with the words that the plan's
decision record adds to its limit (2026-11-18).

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

## On one board

The clause above is about emulation, and keeps its words. This
paragraph is about the runs on one board. Its evidence is diagnostic:
the last six sentences of the limit are about it.

> On one SpacemiT K3 COM260 board, the images that the ledger names ran
> with plain PMP, booted from a microSD card that held the vendor's
> published boot chain and, in the firmware's place, a build of that
> firmware with one more addition, a reset device that only halts, and a
> device tree built in. In each run with the boundary on, M-mode's
> printed record showed each of the monitor's three harts confined, with
> its profile's entries, and, for each hart, counts of access faults, of
> refused calls, and of rejected calls equal to the sums that the test
> declares: none in a scenario's run.

## Required limit

> This is emulation evidence, by adversarial tests and a semantic
> checker; nothing is proved. Under emulation, PMP's behaviour is the
> emulator's, which has no cache. The firmware, the hardware's physical
> memory protection, the descriptor's generator, the boot chain, and the
> monitor's boot code before each hart's activation are trusted for the
> containment, and the offline check of the descriptor for the evidence.
> The tests are a list of attempts made by a test hook: not every
> access, and not an exploit. The runs with the boundary off do not
> cover the attempts on M-mode's own memory, on another hart's interrupt
> file, or on the machine's power device, nor the jumps, the cache-block
> invalidate, and the calls. A breached hart keeps its own VS domain and
> the mailboxes that it writes, and may stop or withhold its work. The
> control hart stays a hub between the others. A breached control hart
> can also pause or terminate a VS domain, see every line that any VS
> domain prints, type into a VS domain that is granted console input,
> with that VS domain's shell's reach, print anything, and shut the
> system down. What a breached hart prints is not evidence: the evidence
> is M-mode's counts and the reads from outside the machine. Nothing
> here protects against cache or timing channels between harts, or
> against a defective firmware. The released MVP 1.0 images have no such
> boundary. On the board this is diagnostic evidence from one board, and
> it is not hardware validation. What M-mode prints there is the only
> witness: nothing read the machine from outside, and no hostile-monitor
> image ran with the boundary built off, so no attempt's effect was told
> apart; M-mode's counts are sums for each hart, not one for each
> attempt; the hostile-monitor images' own records of their attempts
> were not read, so the trap of the cache-block instruction, which those
> counts do not hold, is not shown on the board; and code on the
> confined control hart could print the same lines. A fault on a
> device's register there may have a cause other than PMP. The vendor's
> boot chain and its two real-time cores with their image are outside
> the boundary and trusted, as is the recipe that makes the firmware's
> device tree; nothing in M11 confines those cores. The thirteen harts
> that the monitor does not use, the eight without a hypervisor
> extension among them, are started by nothing in the firmware or the
> monitor, by their sources; with the boundary on, the firmware's banner
> shows them parked, as under emulation. Nothing shows their state.

## The candidate

The candidate is one tree of this repository:
`7a826991eb80d19c03caae883c19271a52f42963`, the tree at which the nine
gates passed on 2026-11-17 and 18. The ledger names it. It is named by
its tree because the responsible human's sign-off gives a commit
another name and keeps its tree: `git log --format='%H %T'` finds the
commit of this line that has it.

The gates' records are under `mvp/results/`:

- [`20261118-m11-candidate/`](../results/20261118-m11-candidate/rc.txt):
  the tool lock, `check`, `evaluate`, the U-Boot rehearsal,
  `kernel-repro`, `model-check`, and the model's evaluator. Each claim
  row of the ledger's second set cites it;
- [`20261118-cheri-check-m11-candidate/`](../results/20261118-cheri-check-m11-candidate/README.md):
  the CHERI check;
- [`20261118-verify-m11-candidate/`](../results/20261118-verify-m11-candidate/README.md):
  `verify`.

The records name the candidate's commit as it was when the gates ran,
before its sign-off, and the same tree.

## The board's runs

The runs on the board are M11-B's, under the plan's board addendum.
They were made after the candidate, at signed commits of this line that
hold the board's tools; each record names its commit. The firmware
builds and the card images of both sittings are named by SHA-256 in
[`k3/sitting-pins.txt`](../k3/sitting-pins.txt).

The two records that the ledger's board rows cite:

- [`20261121-com260-m11b-first/`](../results/20261121-com260-m11b-first/MANIFEST.sha256):
  the first sitting, as it was run again on 2026-11-21. The image is
  `two-guests`, built without the boundary: three boots from the card;
- [`20261122-com260-m11b-second/`](../results/20261122-com260-m11b-second/MANIFEST.sha256):
  the second sitting, as it was run again on 2026-11-22, with the
  boundary on: `anchor`, three boots, and the board's two
  hostile-monitor images, `k3-breach-g1` and `k3-breach-c`, one boot
  each.

Each sitting's first run stopped at its first boot from the card, and
has a record too:
[`20261120-com260-m11b-first/`](../results/20261120-com260-m11b-first/MANIFEST.sha256),
in which the firmware printed nothing, because of the console's node
in its device tree; and
[`20261121-com260-m11b-second/`](../results/20261121-com260-m11b-second/MANIFEST.sha256),
in which the firmware's cold boot stopped for want of heap. Each cause
was corrected in the device tree that the firmware is given, with no
change to the firmware's code, and the sitting was then run again from
its start. No board row cites a run that stopped.

## Where the evidence is

The claim ledger holds this claim's rows as a set of their own, apart
from the release's: [claim-ledger-boundary.md](claim-ledger-boundary.md),
rendered from [`claim-ledger.json`](claim-ledger.json). Each part of the
clause, and each part of the board's paragraph, has a row with its
methods and its evidence, each artifact with its SHA-256; each
sentence of the limit has a row with a note.
`tools/claim-ledger.py check` checks that set, and that its parts are
this page's clause and its board paragraph, and its sentences this
page's limit, word for word. The evidence record is
[`planning/mvp-m11-evidence.md`](../../planning/mvp-m11-evidence.md).
The [guide](guide.md)'s section 10 says how to build the firmware,
make the runs, and read their records, and its section 11 how the
board's runs are made and read. Every part of the claim is read
with the [required limit](#required-limit).
