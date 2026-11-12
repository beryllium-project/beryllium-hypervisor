<!-- SPDX-License-Identifier: GPL-3.0-only -->
<!-- Copyright (C) 2026 James Morris <jmorris@namei.org> -->

# MVP 2.0 milestone M11 plan: the physical boundary under the monitor

**Status.** Proposed by the commit that adds this page, on the public
development line, where each commit is prepared unsigned and the
responsible human signs it off and pushes it. If that commit is on the
public `main` with the responsible human's `Signed-off-by`, this plan is
accepted as written, with Q1 to Q22 at their defaults. Any other answer
needs a revised commit before the sign-off. The signed commit differs
from the one reviewed only by that line and its committer date; if it
must be rebased first, the internal record says so. The project's
internal records keep both commit IDs and the instruction, as they do
for Plan revision S3-D and for security model v1 Part 1 Revision 4.

This is the bounded plan of milestone M11, which
[Plan revision S3-D](mvp-plan.md) of the MVP plan names in outline
(S3-D.4) and puts first in MVP 2.0 (D23). It is proposed after
[security model v1](security-model-v1.md) Part 1 Revision 4, as S3-D
orders, and it takes that revision's invariants I21 to I28 as its
requirements. Its acceptance presupposes that revision's: a change to
Revision 4 revises this plan first. Terms are S3-D.2's and Revision
4's: VS domain, VS-domain
hart, OpenSBI domain, physical access profile (profile), confined, a
hart's activation, parked, shared region, mailbox, partition descriptor
(descriptor), firmware call.

It selects a design, as S3-D asks of it (its Q53). It fixes what
S3-D's stop (m) asks before any M-mode code of the project's is
committed: the language rules, the licence, the location, and the
build. It names each accepted decision that the design changes, for
the responsible human's decision here (S3-D.8). It authorizes nothing
on the board.

## Purpose

After its activation, each hart that the monitor uses can reach only
the physical memory that its profile allows, under rules that M-mode
programs from a description built offline and that HS-mode code on
that hart cannot change. The five harts that the monitor does not use
stay stopped. Every scenario still passes. Hostile-monitor test images
show that a forbidden access has no effect, with M-mode's own count as
the witness.

M11 has two results, in this order.

| Result | What | Decided by |
| --- | --- | --- |
| **M11-E**, under emulation | The candidate: the new memory layout, the descriptor and its tools, the firmware build with the project's M-mode additions, the monitor confined on all three harts, the evidence, and the gates | This plan's work packages M11-2 to M11-9, then the responsible human's decision on the exact result commit |
| **M11-B**, on the board | The same candidate's images on the K3 COM260, under a firmware build of the project's own | Not planned in detail here. It needs the board-firmware amendment of S3-D.6 and a board addendum to this plan, each at its own exact commit (D-15) |

MVP 1.0's images, its claim, and its tag are not changed by either.

## Inputs

- The MVP plan's Plan revision S3-D: S3-D.1 (what a boundary would and
  would not protect), S3-D.2 (terms), S3-D.4 (M11's goal, requirements
  M11-R1 to M11-R10, the order of work, the evidence in outline),
  S3-D.5 (the characterization), S3-D.6 (the board firmware), S3-D.7
  (the claim), S3-D.8 (D23 to D27; stops (j) to (o)), and its Q55.
- Security model v1 Part 1 Revision 4: the attacker, the classes
  `profile`, `shared_region`, `descriptor`, and `firmware_call`,
  invariants I21 to I28, the allowed effects, the required containment,
  and the rows of the trusted computing base.
- The MVP plan's D8, D15, D16, stop condition 3, and S3-C's stops (e)
  and (i), which S3-D.8 names for decision here.
- The M0 plan (the substrate: the boot barrier, the rings, hart start),
  with its revisions M0-A to M0-C; the M1 plan's revision M1-B; the M2
  plan and its revision M2-A (management); the M6 plan (the core
  profile, its D-4 and D-5); the M7 plan (console input, its D-2); the
  M8 specification (stage 1's properties P1 to P9 and the two leaves)
  and the M8 plan's rule for the target digests; the M9 plan (the log).
- The [implementation plan](implementation-plan.md)'s required
  comparison of three M-mode arrangements.
- The MVP line at this plan's base: `mvp/src`, the scenarios, the
  harness, the checkers, the port's counted rules, and the tool lock.

## Facts the design rests on

These are the characterization's findings (S3-D.5), with the kind of
evidence behind each. The characterization was reading of sources at
pinned commits, and emulation in scratch space outside the repository:
bare-metal test payloads and prototype patches to OpenSBI, run under
the locked QEMU, each run made a second time, independently, with the
same results. That scratch is never committed and never cited as
evidence for a claim (S3-D's stop (m)). So every fact that the design
depends on is established again by a committed test in M11: the last
column says where.

Firmware versions: upstream OpenSBI v1.6 (the version that the project
pins for emulation today), v1.9, and the development line at commit
`ed70256dd22c09962d146e433834239825ef0616` ("the base"), the first line
with platform support for the K3.

| # | Fact | Evidence in the characterization | Established again in |
| --- | --- | --- | --- |
| F1 | PMP gives each hart its own view. Sixteen entries at 4-byte grain in QEMU; the lowest matching entry wins. The same page was read-write on one hart, read-only on a second, and unreachable on a third | Emulation | M11-6 |
| F2 | A PMP denial goes to M-mode, for HS-mode code and for a guest alike: the firmware does not delegate access faults. OpenSBI hands the fault back to HS mode on the same hart. Nothing else notices | Emulation for HS-mode code; source for a guest | M11-6, M11-7 |
| F3 | A forged `hgatp` is not stopped. The accesses that follow it are, each checked at its final physical address and at every table page | Emulation | M11-7, M11-8 |
| F4 | Read-only G-stage tables work when the A and D bits are preset, as the monitor builds them, under Svade | Emulation | M11-7 |
| F5 | One OpenSBI domain for each hart, described in the firmware's device tree, enforces distinct memory for each hart. Across OpenSBI domains the firmware refuses hart start and hart status on all three versions. An IPI across OpenSBI domains is refused by v1.9 and by the base; v1.6 returns success and drops it | Emulation | M11-6 |
| F6 | The firmware's calls that take an address check it against the caller's OpenSBI domain, and then M-mode touches the memory itself. In v1.6 a length that wraps passes that check; v1.9 and the base refuse it (upstream commit `9595829a3367`). A zero length passes with any address and touches nothing | Emulation for the wrap; source for the zero length | M11-6 |
| F7 | Each family of firmware calls has its own build switch. A v1.9 build with Base, TIME, IPI, HSM, the debug console, and system reset booted, and every removed family reported absent. M11's own configuration, at the base, was not built | Emulation, v1.9 | M11-2, M11-6 |
| F8 | At the base a hart is assigned, at boot, to the OpenSBI domain with the least `init-order` among those that list it. The default OpenSBI domain, ROOT, lists every hart and has the greatest order | Source and emulation | M11-6 |
| F9 | The firmware has code, which nothing calls, that switches a hart from one OpenSBI domain to another. A call that invokes its "exit" moves the calling hart from a wide boot OpenSBI domain into its own narrow one: the hart's PMP narrows, it resumes at the narrow OpenSBI domain's entry address, and the firmware's own checks then follow the narrow OpenSBI domain. The move resumes the hart only if the narrow OpenSBI domain names that hart as its boot hart; otherwise the base stops the hart | Emulation, with a 90-line prototype patch; the last sentence from source | M11-6 |
| F10 | That move is one-way only with a guard. Unguarded, a second call moved the hart into ROOT, with every region; and a tree that listed the hart in two narrow OpenSBI domains moved it sideways first. Guarded, the second call was refused and changed nothing, and the mis-declared tree was refused before any change | Emulation, 50 runs | M11-6 |
| F11 | After the move, both forms of suspend, and a hart stop, keep the narrow PMP. No hart start, status, or IPI crosses OpenSBI domains. A system reset obeys the narrow OpenSBI domain's own flag | Emulation | M11-6 |
| F12 | With the firmware's cold boot restricted to hart 0 by its device tree, harts in a park OpenSBI domain whose boot hart is not among them stay stopped in M-mode with no PMP entry, and no hart of another OpenSBI domain can start or signal them. A hart that no OpenSBI domain lists falls to ROOT. Without the restriction any hart may win the cold boot | Emulation; the last sentence from source and from F20 | M11-6, M11-8 |
| F13 | The limit that binds a profile is the hart's sixteen PMP entries: the base's device-tree parser allows more regions than that. On QEMU's `virt` machine five entries go to regions that every OpenSBI domain inherits, which leaves eleven with plain PMP and ten under Smepmp. A tree with an OpenSBI domain one region over did not reach S-mode: the firmware printed an error and stopped. At the move itself the base ignores a failed PMP programming | Emulation; the last sentence from source | M11-6 |
| F14 | Under Smepmp the firmware keeps `mseccfg.RLB` set, so no rule is fixed against M-mode. It reserves one entry for its own use during a call | Source and emulation | M11-6 |
| F15 | After its first guest entry, a VS-domain hart's HS-mode code writes nothing but its own block and its VS domain's window | Static analysis of the built images | M11-7, by M-mode's count staying zero in every honest run |
| F16 | After it has started the VS-domain harts, the control hart needs no window, no G-stage pool, and no declared page | Static analysis, and the sources | M11-8, the same way |
| F17 | The monitor touches no device. Its console and its reset go through firmware calls | Static analysis | M11-7, M11-8 |
| F18 | Today's layout does not fit: a VS-domain hart would need 13 or 14 entries. One state page holds both writers' ring words and the hart's private state. The secret's source lies among constants that every hart reads | The layout header and the built images | M11-3 |
| F19 | By the vendor's documents and published source, the K3 has execution contexts beyond the eight X100 harts: eight A100 harts without the H extension, and cores that run the vendor's real-time firmware. Whether this board runs them, and what they can reach, is not established | Vendor documents and source | Not in M11-E. The board addendum (D-15) |
| F20 | QEMU's monitor reads each hart's PMP registers by name, and physical memory, for a client outside the machine. Started so that it does not exit at the guest's shutdown, it still answers with the machine stopped. On today's `two-guests` image, the monitor's three harts held the firmware's one wide table, and so did the hart that had won the firmware's cold boot, when that was not hart 0 | Emulation, QEMU 10.2.2, two runs | M11-2 |
| F21 | Every plain image fails closed at its boot check unless the firmware reports SBI version 2.0, which the firmware pinned today does. The base reports 3.0. An earlier milestone's counted port rule sets the expected value to 2.0, and the CHERI variant has a rule that raises it again | The sources, and the `sbi-3.0` variant's declared outcome | M11-2 |
| F22 | On a hart that has the cache-block management extension, the base lets code below M-mode invalidate cache blocks. QEMU's `k3-like` CPU has the extension, and today's firmware sets the same control. By the cache-block specification, an invalidate needs only the right to load from the block, and it may discard stores that a cache still holds. A hart with a read right could so undo another hart's writes. QEMU has no cache, so emulation cannot show the effect | Source; the specification's text; the control's value as QEMU's monitor reads it under today's firmware | M11-6, for the control's value and the instruction's trap. The effect itself cannot be tested under emulation |
| F23 | The development host satisfies neither tool lock since the workspace moved back to the laptop `lx2` on 2026-11-10; the MVP's lock was last refreshed for the workstation `l1`, on 2026-10-26, with roles and pins added since. Of its 32 roles, 5 differ on `lx2`: `python3`, the host GCC with its two helpers, and the host-only `sfdisk`. Of its closure's 259 packages, 34 are at another version and 5 are not installed. The cross compilers and binutils, Clang, lld, QEMU, and `dtc` match the lock byte for byte. The model's tool check fails on `python3` alone. Since the move, every check that needs a lock has run inside the pinned evaluator image. `verify` has not run on this host. Every `verify` record was made on `l1`, which has 32 processors, the last in 3 h 51 min. The ring's arm limits each solver run to 600 s, and a run that crosses the limit lowers its count of checked properties. The records keep each row's total time, not each run's, so the margin of the slowest run is not known. One single run took 64.5 s and 78.4 s in the two records made at the same inputs, and 329.8 s in the one record made at the line's present inputs: lines of a header that are inactive in the plain build had changed the solver's encoding. The laptop has 8 processors (4 cores), and 46 GB of memory where that arm runs up to four solver processes of 6 to 10 GB each at once. The verifier image builds there with the `verify` record's package list. One harness of the ring's check, run there as a sample, gave the record's verdicts and counts for its eight rows; its two single runs at 512 bytes took 413 s and 466 s with two running at once, against 329.8 s and 358.2 s in the record made at the same inputs, and a whole run has six at once | The locks' own checks on the host (2026-11-11); package queries (2026-11-10); the `verify` records, and `mvp/README.md`'s account of the hosts; the arm's source; the image build and the sample (2026-11-11), which are scratch | M11-2 |

Four limits of these facts, stated so that no later text overstates
them. "One-way" is shown for the calls that were tried: it is not a
proof, and it holds for one firmware commit. QEMU's PMP is an
emulator's: in one case seen, on a CPU with Svadu, it updated A and D
bits in a table page that PMP made read-only; the boundary's runs use
the MVP's `k3-like` CPU, which has Svade and not Svadu. QEMU has no
cache, so nothing about caches is shown (F22). And nothing here has run
the monitor under the base: M11-2 does that first.

## A reading that this plan depends on: S3-D's stop (n)

Stop (n) bars "a boundary design in which M-mode takes a physical
range, a profile, or a hart from HS-mode code after activation, or in
which a confined hart can widen its own profile by any firmware call".

Read word for word, its first half would bar every firmware call that
takes an address, the console's among them. The same accepted text
expects such calls: M11-R2 has "Every call that takes an address is
checked against the caller's profile". M11-R1 ties the rule to
installing a profile, and Revision 4's I24 states it that way: "In
installing or selecting a profile, it takes no range, no profile, and no
hart from HS-mode code".

This plan reads stop (n) as I24 does, and the reading is put to the
responsible human as Q3:

- M-mode never installs or selects a profile from anything that HS-mode
  code supplies;
- no firmware call widens a confined hart's profile;
- a call that a confined hart's list keeps may take a buffer's address
  and length, which M-mode checks against the caller's profile (I27).

On the stricter reading, a confined control hart could not print
through the firmware, and the console would need a design of its own.

## Design

### D-1 The design: per-hart OpenSBI domains, entered by a guarded one-way firmware call

S3-D.4 names four candidates at least. This plan chooses the third.

| | A. One OpenSBI domain and an activation call | B. One OpenSBI domain for each hart, nothing else | **C. Per-hart OpenSBI domains with a small amount of M-mode code of the project's** | D. A minimal M-mode runtime |
| --- | --- | --- | --- | --- |
| How | A call reprograms PMP for the caller | The firmware's device tree gives each hart its regions at boot | Harts start as today, in one wide boot OpenSBI domain. Each then moves itself, once, into its own narrow OpenSBI domain by a guarded call (F9, F10) | M-mode implements only the allowlist |
| The firmware's own accesses for a caller | Unbounded: the firmware's view of the hart stays wide (F6) | Bounded by the narrow OpenSBI domain | Bounded by the narrow OpenSBI domain | Bounded by construction |
| Hart start (D15) | Kept | Lost: no start across OpenSBI domains (F5). The firmware would have to start each hart itself, before the monitor is loaded | Kept: made in the boot OpenSBI domain, before any hart is confined | Kept |
| The control hart | Narrowed | Stays wide | Narrowed | Narrowed |
| A per-role allowlist of calls (M11-R2) | Not by itself | Only for the whole build | Yes: the additions refuse a confined hart every call that its list lacks | Yes |
| M-mode's count, the readback, the identity (M11-R5 to M11-R7) | No | No | Yes | Yes |
| New M-mode code | Changes through OpenSBI's calls | None | Small, in one patch series | All of it, with platform support for the board |

A is ruled out by F6. B cannot start the monitor's harts and leaves the
control hart wide. D ends with the smallest trusted base and costs the
most: it needs the project's own platform support for the board. C is
chosen. D stays open as a later milestone's candidate: once C has shown
which calls a confined hart needs, the case for a runtime that
implements only those can be made on evidence.

**The implementation plan's three-way comparison**, for this static
profile. The criteria: platform support for QEMU's `virt` machine and
for the K3; a per-hart memory model that a device tree can describe;
the calls that the monitor's boot code needs; size; licence; and who
maintains it.

| Arrangement | Assessment for M11 |
| --- | --- |
| "OpenSBI below Beryllium HS" | Chosen, with the additions of D-2. It has platform support for both machines, and the OpenSBI-domain and PMP machinery that the characterization tested. BSD-2-Clause; maintained upstream. Its cost is a large firmware in the trusted base, and additions that must be derived again for each firmware version (F8 to F10) |
| "a Beryllium-owned M-mode component" | Design D. It would meet the allowlist by construction, and it would need the project's own boot, timer, interrupt, reset, and power support for each machine. Deferred, with the trigger above |
| "a separately maintained minimal M-mode runtime" | One candidate was looked at, RustSBI, in its public issue tracker on 2026-11-11 and not in its source: its support for the K3 is tracked there as in progress, with an open pull request whose runtime wiring and hardware validation are pending. Whether it has a per-hart memory model that a device tree can describe was not established. Nothing was built or run. It is not a candidate for M11; a later plan that takes up D compares it again |

What the implementation plan says a runtime plan "must separately
define", for this profile:

| Item | Where |
| --- | --- |
| "the SBI implementation used by HS during platform boot" | D-2 |
| "the virtualized SBI interface exposed to Linux-class VS domains" | Unchanged by M11 (D-12) |
| "the HS-to-M-mode forwarding and ownership contract" | D-8: no guest request is forwarded; the calls of each role and phase |
| "timer, interrupt, hart, reset, and power request mediation" | D-7 (each hart's own timer; no interrupt between harts), D-6 and D-8 (harts started once, by boot code; none stopped), D-8 (reset as a shutdown, by the control hart). No power request exists |
| "exact trusted firmware and delegation assumptions" | D-2, and Revision 4's R4.4. M11-6 records what the firmware delegates, as the oracle reads it |
| "fail-closed behavior for unsupported or malicious requests" | D-2's rule 4 and call filter; D-10's hostile calls |

The firmware and virtual-SBI boundary of a later Linux profile is not
selected by this: the comparison is for M11's static profile only.

### D-2 The firmware build, and the project's M-mode additions (S3-D's stop (m))

**The base.** Upstream OpenSBI at exact commit
`ed70256dd22c09962d146e433834239825ef0616`, the commit that the
characterization tested. It is an unreleased development commit. The
guard of F10 follows from that commit's assignment rule (F8), so the
pin moves only by a recorded change with the firmware's tests run
again (Q2).

**The firmware's SBI version.** The base reports SBI version 3.0, and
every plain image today requires 2.0 (F21). From M11-2 on, every plain
image expects the base's version, by a new counted rule in the MVP's
port. The earlier milestone's accepted port script is not touched, and
the CHERI variant's rule, which would then match nothing, is retired.
The firmware that the project pins today stays pinned for one purpose:
the negative that runs an image under a firmware of another version,
which must fail closed at the boot check. One consequence: from M11-2
on, no plain image of the working line boots under the board's
resident firmware, which reports 2.0. The board waits for M11-B in any
case, and MVP 1.0's images are untouched.

**The configuration.** M11-R2 allows a call to be "absent from the
firmware or refused after activation". The allowlist is the call
filter's, below. The build is reduced as well, as a second barrier:
M11-2 starts from the base's default families of firmware calls, and
M11-6 removes each family that nothing calls in the boot chain before
the monitor, in the monitor's boot code, or in the probe images. Its
report lists each family that stays, with its caller. By this plan's
expectation those are Base, HSM, the debug console, system reset, the
boundary extension, and IPI, which only the probe images and perhaps
the boot chain use. Error output stays enabled.

**The additions**, as one patch series over the base.

| Addition | What it does | Requirement |
| --- | --- | --- |
| The boundary extension, function 0, `confine` | No argument. It moves the calling hart from the boot OpenSBI domain into the one narrow OpenSBI domain that the firmware's device tree names for that hart, by the firmware's own context exit. It is refused, with nothing changed, unless the guard holds, below. On success it does not return: the hart resumes at the narrow OpenSBI domain's entry address | M11-R1, M11-R6; I24, I25 |
| The boundary extension, function 1, `identity` | One argument, a word index from 0 to 3. It returns that word of the descriptor's identity, as the firmware read it from its device tree. Served to the boot OpenSBI domain only | M11-R1; I24 |
| The call filter | For a hart in an OpenSBI domain that has a call list, M-mode performs only the calls on that list, and refuses every other call before any other code sees it, with nothing changed. A list entry is an extension, a function, and, where D-8 gives one, a limit on an argument. The lists come from the device tree | M11-R2; I27 (a), (c), (d) |
| The counts | For each hart, three counts. `denied`: the access faults, on a load, a store, or a fetch, that M-mode hands back to the hart: those that it takes from the hart's HS, VS, or VU mode, and those on its own accesses made for the hart in handling a trap. `refused`: the calls that the filter refuses the hart. `rejected`: the listed calls that the firmware's own argument checks refuse, such as a console call whose buffer lies outside the caller's OpenSBI domain | M11-R7 |
| The cache-block control | At `confine`, M-mode makes the cache-block invalidate instruction illegal below M-mode on that hart (F22). The monitor does not use the instruction, and it gives it to no guest | I21 |
| The readback | When M-mode programs a hart's PMP for a narrow OpenSBI domain, the addition checks the programming's result, reads every entry back, and compares the entries with the full table that the OpenSBI domain's regions require. A failed programming, a missing region, or any difference stops the hart in M-mode. It keeps each hart's readback, with the cache-block control's value | M11-R5 |
| The record | M-mode prints the descriptor's identity at its cold boot. At a system reset it prints, for each hart: whether it confined the hart, the readback that it kept, and the three counts | M11-R5, M11-R6, M11-R7 |

**The guard of `confine`.** All four conditions, or the call is
refused:

1. the caller's OpenSBI domain is not ROOT, and has the least
   `init-order` among the OpenSBI domains that list the hart, ROOT
   aside;
2. exactly one other OpenSBI domain lists the hart, ROOT aside: the
   target;
3. the target names this hart as its boot hart (F9);
4. the target has a call list, which may be empty.

The first two are the conditions that the characterization tested
(F10). The last two close what the base would otherwise do silently: a
hart stopped at the move, and a confined hart with no filter.

**The extension's ID** is `0x08004246`, in the SBI's experimental
space, unused at the base. The additions are an experiment carried as a
patch series. The SBI's firmware-specific space belongs to the
firmware's own project, which would choose the number if the additions
were ever offered and taken. It is a firmware-facing interface: no
guest call reaches the firmware, and it is unrelated to the
guest-facing management extension `0x08004245`.

**Language rules.** S3-D's Q55 has "The project's restricted-C and
evidence rules". The additions are changes to OpenSBI, so they are C in
OpenSBI's own style, and the project's rules bind them as follows.

| The project's rule | For the additions |
| --- | --- |
| No heap | No allocation after cold boot. Where the base allocates on first use, as it does for the per-hart contexts of the context switch, the series moves that allocation to cold boot; if that cannot be done cleanly, M11-6 records the exception and tests the allocation's failure path |
| No recursion; bounded loops | Binds |
| No variadic interface; no uncontrolled function pointer | The additions define none. They call the base's print function, and they fill the registration structures that the base's extension mechanism requires |
| Fixed-width types and checked extent arithmetic | Binds |
| One assembly boundary | The additions have no assembly |
| GCC and Clang | Yields: the firmware is built by the locked GCC alone |
| Automated tests at the lowest practical layer | The guard's decision and the filter's decision are pure functions with host unit tests. Everything else is tested under emulation (M11-6) |

Six rules of their own bind the additions, and the review of each
change checks them:

1. No function of the additions installs or selects a profile from
   anything that its caller supplies. The one argument that exists is
   function 1's index.
2. No function reads or writes memory at an address that HS-mode code
   supplied.
3. Everything that the additions act on comes from the firmware's own
   device tree, read once at cold boot through OpenSBI's existing
   parser. The additions parse two properties of their own, each a list
   of fixed-size cells with a fixed maximum.
4. A refusal changes no state but its own count. A success is
   complete, or the hart stops in M-mode.
5. No loop without a constant bound.
6. State is one small record for each hart, written only on that hart.

**Licence.** OpenSBI is BSD-2-Clause. The patch series, and any new
file that it adds to OpenSBI, are BSD-2-Clause, so that the firmware
stays under one licence and the additions can be offered to OpenSBI.
The descriptor's tools, the tests, and everything else that M11 adds to
this repository are GPL-3.0-only, as `COPYING` makes the default. The
licence manifest's row for the firmware changes with it (Q7).

**Location.** This repository, under `mvp/firmware/`: the base's pin,
the configuration, the patch series, the build rules, and the
firmware's own tests. OpenSBI's source is a pinned external input,
never committed, as the guest's kernel is: it is fetched by commit and
checked against the pinned commit and tree IDs, and the evaluator
receives it offline (Q8).

**Build.** By the tools that the tool lock already names, on the host
and inside the evaluator image, with build information and timestamps
off. Building the firmware inside the evaluator is new: today the
evaluator checks a binary that the host built. The binary's SHA-256 is
pinned in the tool lock beside today's firmware pin, and every run
checks it before the firmware is used. The build is reproducible when
the host's binary and the evaluator's are byte-identical; a difference
is stop 7.

**Who writes them.** The additions may be offered to OpenSBI one day.
S3-D's stop (o) then applies from the first line: they are written
afresh from this plan, with an AI tool that can be disclosed by name,
with a record of that tool in each change. They derive from nothing
in the characterization's scratch, and they carry no text of this
repository (Q9). Whether to offer them is the
responsible human's decision, later, and nothing is sent by automation.

### D-3 The partition descriptor (M11-R1, M11-R10)

One descriptor for each scenario image, generated offline from the
scenario's file and the layout header: the same two inputs that the
image's sealed configuration is built from (I24).

**Form.** A JSON document, schema `be-partition-v1`, in one canonical
form: UTF-8, object keys sorted, no white space outside strings,
addresses and sizes as lowercase hexadecimal strings, and one final
newline. Its identity is the SHA-256 of those bytes.

| Section | Content |
| --- | --- |
| `harts` | Every hart of the platform: its number, its role (control, VS-domain, or parked), and, for a VS-domain hart, its VS domain |
| `extents` | Every physical extent that a profile or a shared region names: a name, a base, a size, and what it holds |
| `profiles` | For each hart that the monitor uses: the extents that it may reach after its confinement, each with its rights |
| `shared` | Every shared region: its extent, its parties, each party's rights, its kind (immutable, mailbox, or declared page), and its one writer, if any (I23) |
| `lifecycle` | For each hart: boot access until its confinement, then its profile, with no way back within a boot; for a parked hart, stopped throughout. For each hart that the monitor uses, the address at which it resumes confined |
| `calls` | For each role, the firmware calls that M-mode performs for a confined hart of that role: extension, function, and argument limit (D-8) |
| `interrupts` | For each hart, the interrupt sources that it takes: its own timer, and nothing from another hart (D-7) |
| `devices` | None. A device assigned to a role would be listed here with its registers' extent (I22 (c)) |

The descriptor states extents by base and size. It makes no
power-of-two assumption and names no PMP entry: those belong to a
backend (M11-R10).

**Backends.** A backend turns the descriptor into what one mechanism
on one platform consumes, and into the exact table that the mechanism
should then hold.

- M11's backend is the OpenSBI domains of the firmware's device tree.
  It writes the region nodes, the OpenSBI domain nodes of D-6 with
  every property that the base needs, the cold-boot restriction, the
  additions' two properties (the identity and each call list), and,
  for each hart, the sixteen PMP entries expected under plain PMP and
  under Smepmp (M11-R5).
- It refuses a profile that does not fit the platform's entry budget
  (F13), an extent that is not a power of two in size or is not aligned
  to its size, and any tree that the guard of D-2 would refuse.
- M11's platform is QEMU's `virt` machine in the MVP's `k3-like`
  profile. One base device tree is committed for it without Smepmp and
  one with, each as the locked QEMU generates it, and a check compares
  each with a fresh one, apart from the values that QEMU makes new at
  every start.
- A backend for memory protection tables is M12's.

**Tools.**

| Tool | Role | Trust |
| --- | --- | --- |
| The generator | Writes the descriptor, the device tree, and the expected tables | Running TCB by its output (Revision 4, R4.4) |
| The checker | Reads the descriptor, the built image's sections and symbols, the scenario's authority report, and the device tree as built. It checks I22's clauses (a) to (f) and I23 for each profile, that every profile's extents are the layout's, that each confined entry address is the image's, and that the device tree says what the descriptor says | Offline evidence TCB. It shares no code with the generator, and it reads the device tree with its own reader |

The checker's own tests include mutations of the descriptor and of the
device tree, each of which it must refuse: a widened right, an added
extent, a secret's extent in a profile, a second writer, a missing
party, a hart in two narrow OpenSBI domains, a narrow OpenSBI domain
whose boot hart is another hart, a missing call list, a missing
cold-boot restriction, a system reset allowed to a VS-domain hart.

**Pairing.** A descriptor belongs to one image. The image carries the
identity as a constant; the firmware's device tree carries it too. Boot
code on the control hart asks the firmware for the identity, where it
probes the firmware today, and stops the run if the two differ. The
firmware removes its own nodes from the tree that it passes on, so the
monitor cannot compare by reading. The authority report gains a section
for the descriptor and its identity. The addresses at which harts
resume confined are fixed by the layout header (D-4), so the
descriptor and its identity exist before the image is linked.

**What the monitor knows.** Its own layout and the identity. It reads
no descriptor at run time, and passes none to M-mode.

### D-4 The memory layout (M11-R4)

The layout changes before anything else in the monitor does (F18). Its
rules:

1. **Text and constants are grouped by role**: boot-only, control-only,
   VS-domain-hart-only, and shared by both roles. Boot-only code and
   constants lie in extents that no profile names.
2. **The secret's source is a boot-only constant.** The staged copy of
   the boot image, which also holds it, is in no profile either
   (I22 (e)).
3. **The control hart's data is split**: what it writes after its
   confinement; and the boot outputs that it only reads afterwards,
   which are the sealed configuration with its identity and derived
   maps, and the log page with its registers (I22 (b), (d)).
4. **Each VS-domain hart's block is split by writer**: the hart's
   private state; the words that boot code published to it, which
   nobody writes afterwards; the mailbox extent that the control hart
   writes (the inbound and input rings' records and heads, and the
   outbound ring's tail); and the mailbox extent that the hart writes
   (the outbound ring's records and head, and the other two rings'
   tails).
5. **Every extent that a profile names is a power of two in size, at
   least 4 KiB, and aligned to its size.** So no cache block lies in
   two extents. Extents that one profile holds with the same rights
   are placed so that one region covers them where that saves an
   entry.
6. **What stays.** The image's base, `0x102000000`. The windows, the
   declared pages, and the staging address. The rings' sizes.
7. **Each address at which a hart resumes confined is fixed by the
   layout header**, so the descriptor does not wait for the link
   (D-3). All three are fixed in M11-3, the control hart's among them,
   so that no later package changes that header.
8. **What the measurement log pins stays.** M9's log profile, its
   tools, and the image checker fix more than five symbols, and the
   layout keeps all of it:
   - each of the five self-report ranges stays one output section
     under its present name, with its link symbols at the section's
     two ends: the core's text (`.monitor.text`), its read-only data
     (`.monitor.rodata`), the R1 input (`.monitor.input`), the MVP
     region's text (`.mvp.text`), and its read-only data
     (`.mvp.rodata`);
   - the role groups of rules 1 and 2 are groups of input sections
     inside those output sections, and any padding that rule 5 needs
     lies inside the section. So a range is still exactly its
     section's extent, and no extent that a profile names covers
     another section's bytes;
   - the secret's source stays inside the MVP region's read-only data,
     as a boot-only group there. The range's digest covers it, as it
     does today;
   - the self-report canary and the log's constants stay in
     `.mvp.rodata`, the canary strictly inside it;
   - the log page and its registers stay inside the control hart's
     MVP-region BSS, so the extent that rule 3 gives them lies in
     that BSS.

   So the log's profile, its record count, and the ledger's row on
   the self-report stand as written. The records' ranges and digests
   change, as the generated references and expectations follow the
   link. A layout that cannot keep all of this is stop 3.

**The core.** The image's first part holds code and data that the
port copies from accepted sources, and the boot check that comes with
them sees one code extent and one data extent, with the console's
buffer page at the data's end. Three things follow.

- The core's code stays one extent for that check. Inside it, boot-only
  functions come first and the rest follows from an aligned boundary,
  by function section, so that a profile names only the second part.
  Where a ported file cannot be separated that way, M11-3 says so, and
  the result lists every boot-only function that stays executable to a
  confined hart. That would be an exception to rule 1, and it needs the
  responsible human's word (stop 3).
- The core's data is laid out so that the sealed input and state, the
  constants, and the console's buffer page fall in extents of their
  own. The ported check's view is kept where it can be; each constant
  of it that moves is named in M11-3's report.
- The table that binds each VS domain to its hart stays among the
  shared constants: both roles read it.

**What moves, and its bounds.** The pools, the blocks, and the region
after them move, and the image grows. Each pool's address is part of
its VS domain's `hgatp` value, so both values, and every line that
prints one, change. Two bounds stay as they are:

- the image ends below `0x102200000`, as today;
- the boot image's limit of `0x400000` and the guest Image's budget of
  `0x300000` (the M7 plan's Q13) still hold. By today's constants that
  caps the monitor's image near `0xfd000`.

The layout header's assertions carry both. A layout that needs more is
stop 3.

**The estimate**, to be confirmed by the generator: eight or nine
entries for a VS-domain hart in the largest scenario, and eight for the
control hart, against a budget of ten. The declared pages cost the
most: they stay where they are, so `anchor`'s protected VS domain needs
three entries for its three pages.

Grouping is by linker section. Whether each function inside a role's
extent is in fact needed after confinement is reviewed, not checked;
this plan claims no more than that.

The layout lands first, with the boundary off, so that a regression in
it is seen apart from the boundary (M11-3).

### D-5 The profiles

Each profile holds what I22 allows its role, and no more. The
descriptor's generator writes them; this table is their shape.

| Extent | A VS-domain hart | The control hart |
| --- | --- | --- |
| Text and constants of its role, and those shared by both roles | Execute, and read for constants | Execute, and read for constants |
| Boot-only text and constants, the secret's source among them | None | None |
| The staged boot image, and any other copy that a loader left | None | None |
| The boot outputs: the sealed configuration, the log page and its registers | None | Read |
| The control hart's own data: its stack, its console buffers, its state | None | Read and write |
| The hart's own G-stage pool | Read | None |
| What boot code published to the hart | Read | None |
| The hart's private state | Read and write | None |
| The mailbox extent that the hart writes | Read and write | Read |
| The mailbox extent that the control hart writes | Read | Read and write |
| The hart's VS domain's window | Read, write, and execute | None |
| The declared pages of the hart's VS domain | Each with the rights that the sealed configuration's mappings give that VS domain, and no page that they do not give it | None |
| Another hart's pool, published words, private state, or window | None | None |
| A device's registers | None | None |
| M-mode's memory | None | None |
| Memory that no extent names | None | None |

The other VS-domain hart's mailboxes are in no VS-domain hart's
profile: the two VS-domain harts share only the declared pages that the
policy gives both of their VS domains.

The control hart attributes each record to the VS domain of the ring
that it came from, and refuses a record that names another, as it does
today. I23 asks for that, and the boundary keeps it.

A parked hart has no profile to install: it never leaves M-mode (D-9).

**Two PMP modes.** The backend writes each table for plain PMP and for
Smepmp, and M11-E's evidence runs in both (Q10). Under Smepmp the
firmware keeps its lock-bypass bit set (F14), so "locked" binds nothing
against M-mode in either mode: what makes a profile fixed is that no
firmware call changes it (D-6, D-8), not a lock.

### D-6 Lifecycle: boot access, confinement, activation

**The OpenSBI domains** that the backend declares, with the properties
that the base needs of each:

| OpenSBI domain | Lists | Boot hart | Regions | Order | Entry | Call list | System reset |
| --- | --- | --- | --- | --- | --- | --- | --- |
| The boot OpenSBI domain | Harts 0 to 2 | Hart 0 | Everything but M-mode's own memory, as ROOT has today | Least | Left to the firmware's loader: the monitor, or U-Boot in the rehearsal | None: every call that the build has | Allowed |
| The control hart's narrow OpenSBI domain | Hart 0 | Hart 0 | The control hart's profile | Greater | The control hart's confined entry | D-8's | Allowed; the filter makes it a shutdown only |
| A VS-domain hart's narrow OpenSBI domain, one for each | That hart | That hart | That hart's profile | Greater | The hart entry of today, with the hart's block as its argument | Empty | Not allowed |
| The park OpenSBI domain | Harts 3 to 7 | Hart 0, which it does not list, so the firmware starts none of them | One execute-only page that nothing else names, which the firmware requires as an entry and no hart reaches | Greatest but ROOT | That page | None needed | Not allowed |

The device tree also restricts the firmware's cold boot to hart 0, by
the base's own property for that. Today any hart may win the cold boot,
and the winner holds the firmware's wide table for the rest of the run
(F20). Under the boundary the monitor always enters on hart 0, and a
boundary-on image refuses any other: its shim's start rule is built
out, and a boot on another hart starts nothing.

**The sequence.** New steps are marked.

1. The firmware boots hart 0 in the boot OpenSBI domain. Harts 1 and 2
   stay stopped. Harts 3 to 7 stay stopped for the whole boot (F12).
2. *New.* Where hart 0 probes the firmware today, it also probes the
   boundary extension and compares the descriptor's identity (D-3). A
   firmware without the extension, or another identity, ends the run
   there, long before any hart starts.
3. Hart 0 runs the rest of the monitor's boot code as today: it
   validates, seals, and derives the configuration, builds the G-stage
   pools, measures and closes the log, publishes the blocks, and arms
   console input.
4. Hart 0 starts harts 1 and 2 by HSM. *Changed:* it checks each
   start's result and does not ask for the hart's status afterwards,
   because a hart that has moved is no longer visible from the boot
   OpenSBI domain (F5). A started hart's progress is its READY record,
   within the wait that READY has today.
5. *New.* Each started hart begins at a stub that does one thing: it
   checks its argument by arithmetic and sets its stack, as the hart
   entry does today, and calls `confine` through the executor's one
   call site. The hart resumes at the hart
   entry of today, with the same contract: its hart number and its
   block's address, both now from M-mode's device tree. Everything that
   the hart does today from that entry on, it now does confined: its
   checks, READY, and its first guest entry.
6. *New.* Hart 0 calls `confine` itself when the second hart start has
   returned: before it reads any ring, and before it makes any other
   firmware call. It resumes at the control hart's confined entry,
   prints the lines of step 4, and enters the control loop.

In M11-7's configuration, which confines the VS-domain harts alone,
the device tree has no narrow OpenSBI domain for hart 0, and hart 0
skips step 6: it stays in the boot OpenSBI domain for the whole run.

**The events that Revision 4 leaves to this plan.**

- A VS-domain hart's activation is its first guest entry. It is
  confined well before that, at step 5 (I26 (a)), and before it reads
  its inbound ring (I26 (b)).
- The control hart's activation is its confinement at step 6: the end
  of its boot work, the hart starts included, and before the first
  input that it takes from a VS-domain hart (I26 (b), (d)).
- A VS-domain hart may reach its first guest entry while hart 0 is
  still making the second hart start. In that interval hart 0 is boot
  code, and it reads nothing that a VS-domain hart can write.
- Between a hart's start and its `confine`, a VS-domain hart executes
  the stub alone. That is boot code (I26 (c)).

**What crosses the move.** The move swaps the hart's supervisor
control registers for the narrow OpenSBI domain's fresh ones. The
first entry that follows is made as HSM start makes one: the trap
vector is the entry address, and the scratch register, the interrupt
enables, and the address translation are cleared. The hypervisor and
virtual-supervisor registers, and the timer comparator, carry over
untouched; so the control hart's budget deadline survives. Each
confined entry therefore treats every register as unknown and sets up
what its role needs, as the hart entry does today; the control hart's
confined entry resets its HS-mode state through the same function. All
state that the monitor keeps across the move lies in memory that the
hart's profile allows.

**Refusal.** If `confine` returns, the boundary is absent or the tree
is wrong. A VS-domain hart then parks in HS mode at once, having
entered no guest, and the control hart's wait for its READY ends the
run. The control hart ends the run with a failure line. Neither
continues unconfined into a guest or into the control loop.

**One-way (I25, M11-R6).** After the move the guard refuses a second
`confine`, the call filter refuses every hart-management call, and the
firmware refuses hart start and status across OpenSBI domains (F5,
F11). The only way to a new boot access is a system reset, which begins
in boot code.

Stop condition 3 excludes "a hart started or stopped after the boot
barrier". Revision 4 reads those words as the plans use them: the
barrier is the end of the control hart's boot work, and the hart starts
come before it. In the source's naming, the hart starts follow the
publication of the blocks (`BE_MVP:07`), as they do today.

### D-7 Signalling between harts: rings, read on each hart's own timer tick

Across OpenSBI domains the firmware delivers no IPI (F5). So after
confinement the harts cannot signal each other as D15 has it. This plan
replaces the IPI by a timer tick on each hart, in every phase and in
every scenario image.

- **A VS-domain hart** arms its own HS-level timer when it is
  confined, with a fixed period. A tick at guest level is a new kind of
  exit: the hart re-arms the timer, reads its inbound ring, serves a
  record if there is one, as it does today on an IPI, and resumes the
  same guest. In its waits in HS mode it sleeps until the tick. It
  never switches a guest.
- **The control hart** reads the outbound rings on its own timer's
  tick. It has that timer today, for the run's budget and, in shell
  images, for console input. Now it ticks in every image.
- **A record is its own announcement.** Each ring's writer publishes
  the record, and the reader finds it at its next tick or exit.

B7 took the HS timer interrupt at guest level for its time slice, and
M0 replaced it by the IPI. M11 takes it again, as a tick that switches
nothing.

What changes, and what does not:

| | Today | With M11 |
| --- | --- | --- |
| The rings, their one-writer rule, their fences | As the M0 plan and M8's stage 1 state them | The same; split by writer in the layout (D-4) |
| The M8 specification's properties P1 to P9, and the ordering premises | None of them has an IPI step | Unchanged in statement. The concrete model's exit decision names the IPI's cause, so that definition and its readings change (D-11) |
| A wake-up | One IPI after each published record | The reader's next tick |
| The interrupts that a VS-domain hart takes | The IPI, at guest level and in its waits | Its timer, at guest level and in its waits. Any other interrupt fails the hart, an IPI now among them |
| The timer comparator's writers | The control hart's budget alone | Each hart's own tick as well |
| Latency | The IPI's | One tick period at most for each hop. A pause or a terminate takes up to four hops: the request, its delivery, the answer, and the result |
| Back-pressure | None: a full outbound ring fails its hart. The control hart drains as soon as it is woken | None. The control hart drains at its next tick, so a ring's peak may rise by what its guest prints in one period |
| The probe of each run | One PING, one IPI, one PONG, with the mode in which the IPI arrived | A tick probe: one PING, answered at the hart's next tick, with the mode in which the tick arrived |
| A VS-domain hart's exits | Counted, with exactly one IPI exit in some scenarios | Tick exits are counted apart, bounded, and not charged to the exit ceiling. The other counts stay exact, derived again |
| A guest in native `wfi` | Sleeps until its own timer | Is also woken at each tick, and sleeps again |
| The control hart's wake and idle counts | Few wakes, in images without console input | One wake for each tick, in every image |

The default period is 2^18 timebase ticks for both roles, the M7
plan's console-poll period (Q12).

**What ticks cost.** A periodic interrupt on each hart that runs a
guest. The expectations above, derived again. And the platform's IPI is
no longer exercised by the scenarios: it stays in the probe images,
which run with the boundary off (D-12).

**The alternatives** (Q4). On either reading of stop (n), neither is
barred.

- *A relay call in M-mode*, with no argument, which raises the
  interrupt on each hart that the descriptor pairs with the caller. It
  keeps today's wake-ups, counts, and latency. It costs M-mode code, a
  firmware call that stays open to every confined hart, VS-domain harts
  included, and a cross-hart effect after confinement, which I27 (c)
  allows only as the descriptor names it. A breached hart could
  interrupt its peers at will; that is availability, and the monitor
  would have to tolerate an interrupt with no record behind it, which
  fails a hart today.
- *Interrupts through the interrupt controller's files*, written from
  HS mode. It needs a device extent in every profile, against a budget
  that is already tight, and interrupt-controller handling that the
  monitor does not have. A breached hart could raise interrupts in
  every file that it can reach.

Ticks need no M-mode code and leave a confined VS-domain hart with no
firmware call at all. S3-D.1 says that the firmware's call interface
"becomes the next thing that a breached hart attacks". That is why
ticks are the default.

### D-8 The firmware calls for each role and phase (M11-R2)

| Hart and phase | Calls that M-mode performs | Enforced by |
| --- | --- | --- |
| The control hart, as boot code, in the boot OpenSBI domain | Base: the version and probe calls. HSM: the status of harts 1 and 2 before their start, for the list in `BE_MVP:02`, and their start. The console's write. The system reset. The boundary extension's two functions | Boot code is trusted. The build has few other families (D-2) |
| A VS-domain hart, as boot code | `confine` | The same |
| The control hart, confined | The console's write. The console's read, in images whose sealed configuration grants console input to a VS domain. The system reset, with the shutdown type only | The call filter, from the narrow OpenSBI domain's list |
| A VS-domain hart, confined | None | The call filter, with an empty list |
| A parked hart | None | It never leaves M-mode |

- **Every call that takes an address** is the console's write or
  read. The firmware checks the buffer against the caller's narrow
  OpenSBI domain, with the range check that refuses a wrapping length
  (F6). The control hart's console buffers lie in its own data extent.
  No kept call registers memory for M-mode to use later (I27 (b)).
- **Hart management.** A confined hart can start, stop, or suspend no
  hart, itself included: the filter refuses the family. That closes
  the paths that reprogram PMP, though the characterization saw none
  of them widen it (F11).
- **A VS-domain hart loses its last calls.** Today its failure path
  may print through the firmware and reset the system, when its ring
  cannot carry its failure record or the control hart does not
  acknowledge it (the M0 plan's Q10, and revision M1-B). Confined, it
  cannot. So from M11-4 on, every VS-domain hart keeps room in its
  outbound ring for its last records: 360 bytes, which hold one full
  line record and the largest failure record. Before any post other
  than its failure path's own, the hart computes the ring's free bytes
  from its own view and from the reader's tail, which a writer may
  already read. If the post would leave fewer than 360, the hart makes
  no such post and fails at once, with the ring's class. Its failure
  path then posts its unfinished line and its failure record into the
  room kept, where both always fit. The reader's tail only grows, so
  an old reading of it can only make the hart fail early. The hart
  waits for the acknowledgement as today. If none comes, a hart that
  is not confined prints and resets as today. A confined hart parks in
  HS mode whether or not one came, and the control hart reports the
  failure. The ring's own code is unchanged and still fails closed,
  and no word is added between harts: I16 stands as written. A
  confined hart whose ring view has failed for another reason, such as
  a malformed tail, parks without a report, and the run then ends by
  the control hart's budget; a hart that is not confined prints and
  resets, as today. Revision 4 lists a
  VS-domain hart's console write as an allowed effect only "where its
  role's allowlist keeps" it. This plan does not keep it (Q5).
- **What the filter does not cover**: what M-mode does for a hart in
  handling a trap (I27 (e)). At the base those paths are the fetch of a
  faulting instruction for decoding, the emulation of a misaligned
  access, the emulation of an illegal instruction, a platform's hook on
  an access fault, which QEMU's machine does not have, and the
  delivery of a pending software event, which goes with its call
  family. M11-6 lists each path that the build keeps, shows that it
  touches only memory that the hart's PMP allows, and removes what the
  monitor does not need.

### D-9 Every execution context (M11-R3, I28)

| Context | State under M11 | Evidence in M11-E |
| --- | --- | --- |
| Harts 0 to 2 | Confined, each by its profile | D-10 |
| Harts 3 to 7 | Parked: listed in the park OpenSBI domain, never started, in M-mode throughout | The oracle reads all eight harts at the end of every run. Hostile-monitor images try to start and to query them, from each confined role |
| The board's other contexts (F19) | Named in the trusted computing base, with no evidence yet | None under emulation: QEMU's machine has none. The board addendum |

D16 keeps its words: harts 3 to 7 are never started. M11-R3's test of
all eight harts is a test that the five stay stopped and out of reach.

Under the boundary the control hart cannot ask the firmware for the
state of harts 3 to 7: the firmware refuses a query across OpenSBI
domains. Boot code asks for harts 1 and 2 only, and the run's line says
so.

### D-10 Evidence under emulation (M11-R5 to M11-R7)

**The oracle outside the monitor.** QEMU's own monitor interface, read
by a small client in the harness (F20).

- QEMU is started so that it stops, and does not exit, at the guest's
  shutdown. Today a run passes only if QEMU exits by itself with status
  0; that rule becomes: QEMU reports a guest shutdown, the client
  reads, and the client ends QEMU.
- With the machine stopped, the client reads, for all eight harts: the
  PMP registers, and the PMP control register under Smepmp; the
  cache-block control; the program counter; and M-mode's record from
  the firmware's memory. It reads the witness words that a test names.
  Every memory read is physical, never through a hart's translation. A
  device's register is read only where the read has no side effect.
- A run that ends by the harness's timeout is read the same way, after
  the client stops the machine.
- The client reads only after the machine has stopped: nothing inside
  it runs during the read.

**M-mode's record** (D-2) is printed by the firmware at the system
reset. Under emulation the checker compares it with the oracle's read
of the same values. On the board it will be the only witness (D-15).

**What every boundary-on run must show**, hostile or not. The expected
end state follows how the run ends, which the image's declared outcome
gives:

1. A hart that M-mode confined holds the backend's expected table for
   its profile and mode, equal to M-mode's readback, and the
   cache-block control is set for it. A hart of the monitor's that
   ended before its `confine`, or that the configuration leaves
   unconfined, holds the boot OpenSBI domain's table, which the
   backend also writes. A hart that was never started holds no PMP
   entry. M-mode's record says which harts it confined, and the
   checker requires that set to be the one that the declared outcome
   implies: in a run that passes, every hart that the configuration
   confines.
2. Harts 3 to 7 hold no PMP entry, and each one's program counter lies
   in the firmware: they are stopped in M-mode.
3. The descriptor's identity that M-mode printed is the image's.
4. M-mode's three counts are those that the declared outcome gives.
   In a run without a test hook they are zero for every hart, but for
   the negative that removes a needed extent: the monitor and its
   guests asked for nothing outside their profiles and lists (F15 to
   F17).

**The hostile-monitor images** are variants of the scenario images,
named `breach-…` to keep them apart from the M7 plan's `hostile`
variant, which is a hostile guest. Each has a test hook compiled into
one hart's HS-mode code. The hook runs once, after that hart's
activation. It installs its own trap vector, makes a list of attempts
from HS mode on that hart, records what each one did, restores the
monitor's vector, and lets the scenario continue to its normal end. The
hook writes registers that only named code may write in a scenario
image; the image checker admits it in these images alone, under a
rule set of its own.

What the attempts reach for:

| Target | From a VS-domain hart | From the control hart |
| --- | --- | --- |
| Another VS domain's window | Yes | Both windows |
| A declared page beyond its VS domain's rights, the secret page among them | Yes | Every declared page |
| The secret's source; boot-only text and constants; the staged boot image | Yes | Yes |
| The monitor's text and constants, the sealed configuration, the log page, to write them | Yes; and to read the last two | Yes |
| The G-stage pools | Its own, to write; the other, to read and write | Both, to read and write |
| The published words | Its own, to write; the other hart's, to read and write | Both harts', to read and write |
| Another hart's private state; the control hart's data | Yes | Each VS-domain hart's private state |
| The mailbox extent that it only reads, to write it; the other VS-domain hart's mailboxes | Yes | The first |
| Device registers: the console's; the S-level interrupt controller's; another hart's interrupt file; the machine's power device | Yes | Yes |
| M-mode's memory, the timer and the M-level interrupt controller among it; memory that no extent names | Yes | Yes |

How they reach:

- by a plain load, store, and jump, and by an access that straddles an
  extent's edge;
- through translation: an HS-mode page table that the hart can read,
  with a leaf that maps forbidden memory; and tables that themselves
  lie in forbidden memory, reached through the guest-stage registers by
  the hypervisor's load and store instructions, a forged `hgatp` among
  them (F3). Both roles do this: the control hart has the H extension
  too;
- by other instructions that write, on a mailbox that the hart only
  reads: an atomic memory operation, a load-reserved followed by a
  store-conditional of the same word, and the cache-block zero
  instruction, where the CPU has them;
- by the cache-block invalidate instruction on a block that the hart
  may only read (F22);
- by a misaligned access, which M-mode may emulate (D-8);
- by firmware calls: `confine` again; hart start, stop, and suspend,
  of itself and of every other hart; a call outside its list, from
  each family that the build keeps; a console call with a buffer
  outside its profile, with a wrapping length, and with a zero length;
  a system reset of another type.

**Each attempt declares its outcome**, and a hostile-monitor image
passes when every attempt meets its own (M11-R7):

| Attempt | What it must show | M-mode's count |
| --- | --- | --- |
| A write to forbidden memory, by any instruction | The hook's record shows the access fault, and the witness word that the oracle reads is unchanged | `denied`, one for each |
| A read of forbidden memory, or a jump into it | The hook's record shows the access fault | `denied`, one for each |
| The cache-block invalidate | The hook's record shows an illegal-instruction fault | None |
| A call outside the hart's list | The call's error; the oracle's read shows nothing changed | `refused`, one for each |
| A listed call with a buffer outside the profile, or a wrapping length | The call's error; the witness word is unchanged | `rejected`, one for each |
| A listed call with a zero length | Success; nothing is written | None |

The counts for the hooked hart equal the sums that this table gives,
and are zero for the other harts. The scenario then runs to its
declared end, with its declared lines and counts.

The hook's own report is secondary: the image is a fixture built from
the candidate, and its report alone proves nothing. A hart that merely
stops is not a pass.

**Discrimination.** Each hostile-monitor image is also built with the
boundary off and run under the same firmware with QEMU's own device
tree, which declares no narrow OpenSBI domain. That build makes only
the attempts that can be discriminated, and each of those must take
effect. The rules that keep those runs sound:

- a write's witness is a word that nothing else uses, inside the
  target extent: padding that the layout reserves, a spare page of a
  pool, or, in a window, a page that the variant's guest device tree
  reserves;
- a read's witness is the value that the hook read, which it copies to
  a word of its own; the oracle compares it with the target's known
  content;
- a device attempt uses a register whose write changes nothing else
  and can be read back: the console's scratch register, and a source's
  configuration in the S-level interrupt controller;
- an attempt whose boundary-off run does not show the effect is a
  failed discrimination, which fails the test (stop 15). It is never
  dropped.

What is not discriminated, which the result lists by attempt:

- attempts on M-mode's memory, which the firmware denies in both
  builds;
- attempts on another hart's interrupt file and on the machine's power
  device, which leave nothing that a read can show, or end the run;
- the jumps, the cache-block invalidate, and the calls. Each kept
  call's own working is shown by every run: the harts are started by
  HSM, the lines are printed through the console, and the run ends by
  a system reset.

**The boundary's own negatives.** Each rule of the boundary has a
test built to break it:

| Negative | Declared outcome |
| --- | --- |
| A boundary-on image under a firmware that reports the right SBI version and lacks the boundary extension | The run ends at the firmware probe; no hart starts |
| A device tree whose descriptor identity is another image's | The run ends at the identity check; no hart starts |
| A device tree that lists a hart in two narrow OpenSBI domains, or names another hart as a narrow OpenSBI domain's boot hart, or gives one no call list | `confine` is refused; the run ends with a failure line; no guest is entered |
| A profile with one needed extent removed | The hart that needs the extent faults and fails closed; M-mode's `denied` count for it is not zero; the run is judged failed |
| A device tree with no cold-boot restriction | The checker refuses the device tree before any run |

**What this evidence is not.** It is emulation. Nothing is proved. The
attempts are a list, not every access. QEMU has no cache: the
cache-block control is shown by its value and by the instruction's
fault, never by an effect on memory. The oracle sees the machine's
final state: a rule that was widened and narrowed again during a run
would be seen only by M-mode's readback and counts. A test hook is not
an exploit: it shows what the boundary does to HS-mode code that tries,
not that any flaw exists that would let a guest run such code.

### D-11 Proofs, and the CHERI variant (M11-R9)

**A proof-impact review comes before any proof is re-run** (M11-2). It
lists, for each of these, whether M11 changes it and why: the M8
specification's nine properties and the two leaves' contracts; stage
1's modules, its generated layout constants, and its readings by
symbol; the five ordering premises and their litmus tests; the two
leaves' translation units, headers, flags, and pins; and M3's and Model
0.2's theorems as stage 1's lineage table classes them.

What this plan expects of that review, to be confirmed by it:

- **No property's statement changes.** Stage 1 models no IPI delivery,
  and its one-writer property P2 is what the layout makes physical. No
  word is added between harts (D-8), so P2 and I16 stand as written.
- **Definitions and readings do change.** The generated layout
  constants change with D-4. The concrete model's exit decision names
  the IPI exit by its cause, and the tick replaces that cause. A
  VS-domain hart now computes its outbound ring's free bytes before a
  post. It reads only what the `post` step already reads, the
  reader's tail, and its outcome is the `fail` step. It is modelled
  inside the `post` step's definition, and not as the table's
  `room(r)` step, which stays the input ring's alone. So the
  specification's step table is left as written, and the review
  records that reading. Stage 1 is read again and re-proved with every
  statement unchanged, as M10 did for M9's change.
- **Both leaves' pinned inputs change**, and S3-C's stop (i) applies
  as written: before every merge that changes a byte, a flag, or a pin
  that a leaf's proof names, each arm is re-run, with the target
  digests written again at that commit; a verdict that changes is stop
  9, and so is a count that changes because a run crossed its time
  limit, which is recorded as that ("The host for `verify`"). This
  plan expects four such points: M11-2, whose port rule changes a
  ported header of both leaves; M11-3, the layout header; M11-4, the
  unit that holds the exit classification; and the
  candidate. To add no fifth: the layout header is complete at
  M11-3; every failure class that M11 adds, the boundary's among
  them, is added at M11-4; the boundary's other constants live in a
  header that neither leaf includes; and its build option reaches the
  monitor by no compile flag that a leaf's compile receives. A further
  point, if one arises, is handled the same way.
- **The confinement itself is not modelled in M11.** I21 to I28 are
  invariants of M-mode and of the offline derivation; their evidence is
  D-10's and the checker's, not a theorem. A model of the boundary is
  a later plan's.

If the review finds a statement that must change, the specification is
revised and accepted first, at its own exact commit, with the
responsible human as reviewer of record (stop 9).

**The CHERI variant** is built with the boundary off: its emulated
platform has a different firmware. The CHERI check guards the plain
images' identity against a pinned record, and M11 changes every plain
image from M11-2 on, so the check's record is derived again at the
candidate, by name. The check is a gate of M11-E's result. It may fail
on the working branch in between (S3-D's Q54).

### D-12 Images, machines, and names

**The boundary is a build option of the monitor**, on by default from
M11-7 on. Off, the monitor makes no boundary call and accepts a boot on
any hart, as today. I21 to I28 are asserted of every image that is
built with the boundary on, and of no other.

**The run matrix.** "M11 build" is the firmware of D-2.

| Images | Boundary | Machine | PMP mode | Firmware | Device tree |
| --- | --- | --- | --- | --- | --- |
| The three scenarios, their shell variants, and their negative variants, except those named below | On | `k3-like` | Plain | M11 build | The backend's |
| The hostile-monitor images; one run of each scenario; the firmware's own tests | On | `k3-like` | Smepmp as well | M11 build | The backend's |
| The hostile-monitor images' discrimination builds | Off | `k3-like` | Plain | M11 build | QEMU's own |
| The scenarios on the `rva23` and `plic` machines; the `no-sstc` negative; the `shim-rule` variant; the probe images | Off | As today | Plain | M11 build | QEMU's own |
| The firmware-version negative | Off | `k3-like` | Plain | The firmware pinned today | QEMU's own |
| The U-Boot rehearsal | On | `k3-like` | Plain | M11 build | The backend's |
| The CHERI variant | Off | Its emulator | | Its own | Its own |

Each existing row runs for the toolchains that it runs for today, and
the hostile-monitor images and their discrimination builds run for
both. Boundary-on runs use the `k3-like` machine alone: it has the
CPU configuration recorded for the board, and each further machine
would need base device trees of its own (Q11).

**Existing variants under the boundary.** Each keeps its intent. Their
declared outcomes:

| Variant | Under the boundary |
| --- | --- |
| `payload`, `wrong-measurement`, `reader-write`, `secret-shared`, `response-writable` | As today: each fails closed in boot code, before any hart starts |
| `run-timeout`, `exit-budget`, `init-exit`, `rdcycle`, `sbi-time`, `no-inject`, `no-grant-check`, `hostile`, `self-report-flip`, the shell variants | As today in outcome; their lines and counts are derived again (D-7) |
| `hart-start` | As today in outcome: the firmware refuses the start. Its detail no longer has a status |
| `ring-full` | Changed. Today each VS-domain hart prints its own failure through the firmware. Confined, it fails while the room for its last records remains, and the control hart reports each failure (D-8). With the boundary off, the hart's own print must still come: M11-4 checks that the variant's ring fills, and its acknowledgement window ends, before the control hart's delayed first drain |
| `no-sstc`, `shim-rule` | Boundary-off rows, as today: the first runs on another machine, and the second tests the shim's start rule, which a boundary-on image does not have |
| `sbi-3.0` | Re-declared as the firmware-version negative, and renamed `firmware-version`, since the other firmware will be the one that reports 2.0: an image under a firmware of another SBI version fails closed at its boot check |

A variant whose intent cannot be kept is stop 13.

**The probe images** characterize a platform under its boot access.
They stay boundary-off, they keep their IPI phases, and their table in
the M0 plan is unchanged (Q16).

**Identifiers.** New code names the new things as S3-D.2 does: profile,
confine, descriptor, boundary. No existing identifier is renamed in
the name of terminology (S3-D's stop (l)); one variant is renamed
because its name would state the wrong version.

**The guest-visible interface does not change.** No guest call is
added, removed, or renumbered, and the SBI implementation version that
guests see stays as it is. One trap differs on a confined hart. A
guest that executes the cache-block invalidate instruction, which no
guest's device tree offers, takes an illegal-instruction exception
itself; today the instruction fails its VS domain.

### D-13 The specification's words (S3-D's stop (k))

M11 names no Beryllium unit a supervisor domain, an RDSM, or an SDSM,
and gives none an SDID or a memory protection table. That is this
plan's decision under stop (k), and M12's plan may take the question
up again with the tables running.

As a reading, not a naming: each hart's narrow OpenSBI domain holds
that hart's part of the monitor and the VS domain that it runs, which
is the shape that the specification gives a supervisor domain. Three
differences would have to be stated before any such naming:

- the monitor's boot code runs with boot access before the move, so it
  is in the trusted base of every profile;
- a pause or a terminate of a VS domain is decided by the control
  hart, a peer in HS mode, and not by M-mode;
- the specification's operative text names Smepmp "or equivalent" for
  the M-mode manager's own protection, and M11's firmware leaves no
  rule fixed against M-mode (F14).

The descriptor is written so that the tables could enforce it
unchanged (D-3; M11-R10). M12's last step tests that.

### D-14 The triggers (security model v1, Part 5)

Revision 4 asks this plan to evaluate Part 5's two triggers if its
design adds a decision at run time. It adds two, both in M-mode: the
guard of `confine`, and the call filter.

**The capability trigger does not fire.** Every profile, every call
list, and the guard's conditions are fixed by the offline descriptor
and the build. Nothing is designated, delegated, attenuated,
transferred, or revoked at run time. A hart's move from its boot access
to its profile is a fixed step that happens once; M-mode selects the
profile from the hart's number, and no hart can ask for another.

**The runtime-check trigger does not fire.** No operation is allowed
by the mappings or the grants and then denied by a further rule. A call
that the filter refuses is a service that the hart's role was never
given, like a load of an unmapped address. A profile gives a VS-domain
hart exactly the rights that the sealed configuration's mappings give
its VS domain. HS-mode code evaluates no policy for the boundary, and
M11 adds no type, label, or `decide` to it.

If a later milestone lets a profile or a call list change at run time,
Part 6 reopens the question. Neither answer selects a runtime
mechanism.

### D-15 The board (not authorized by this plan)

M11-B needs three things that do not exist yet, each the responsible
human's decision at its own exact commit:

1. the read-only inventory of S3-D.6's step 1, in sessions that he
   opens;
2. the amendment to the board policy (S3-D.6, step 2);
3. a board addendum to this plan, written on the inventory's facts.
   S3-D.7 has this plan fix the words for a board result; the
   addendum, as part of this plan, fixes them.

The addendum has to settle at least:

- the firmware base for the K3, between upstream's development line
  and the vendor's tree;
- the entry budget. By the table that the vendor's own commit prints,
  its root OpenSBI domain has sixteen regions, of which every other
  OpenSBI domain inherits fourteen, which leaves two. Upstream's K3
  support at the pinned commit adds none of its own, and its count on
  the board needs the board's device tree;
- PMP's grain on the X100, which this plan's layout tolerates up to
  4 KiB, and whether the board has Smepmp;
- the trap paths of D-8 on the board: the vendor's tree has a hook
  that emulates some accesses for S-mode;
- the cache-block control (F22), whose effect only hardware with
  caches can show;
- the other execution contexts (F19);
- how the board is given one firmware device tree for each scenario,
  since a descriptor belongs to one image;
- what witness the board has. A microSD card in the slot excludes the
  debug probe (S3-D.6), so M-mode's printed record would be the only
  one, and a breached hart that can print can imitate it.

Until then stop (j) stands, and no M11 step touches the board.

## Claim text (the subject pre-authorized by S3-D.7; the words fixed here)

MVP 1.0's claim page, `mvp/docs/claim.md`, is not changed: its
blockquote and its limit describe the release, and stay true of it. The
clause lives on a page of its own, `mvp/docs/claim-boundary.md`, "The
physical boundary: the M11 candidate's claim" (Q19). The clause has one
form for each outcome, and no other claim text changes (S3-C's stop
(d)).

**If M11-E is accepted with all three harts confined:**

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

**If only the VS-domain harts are confined** (M11-8 stops, and the
responsible human accepts M11-7's state as the result): the same
clause without the words on the control hart, with "a VS-domain hart"
for "a confined hart", and with this sentence added: "The control hart
is not confined, and its HS-mode code is trusted."

**If a tested attempt has an effect that is not removed:** no clause.
The finding is recorded, and the candidate is not presented as a
result.

**After M11-B**, the clause's first words become "In QEMU and on one
SpacemiT K3 COM260 board, booted there from", followed by the words
that the board addendum fixes for the firmware's source and its medium
(D-15).

**The limit that goes with the clause**, in every form:

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

**The release's rows during M11.** The ledger cites 79 files as
evidence for the release's rows, each by its SHA-256, and its check is
part of `check`. Of them, 53 are neither records nor planning pages:
sources, tools, tests, and saved captures. M11 changes many of those.
So far each change of a pin went to the responsible human. Accepting
this plan lets a work package make it, by this rule. A work package
that changes, moves, or removes a cited file reads the row's claim
again, and does one of three things in the same commit, with the
ledger's rendering:

- the claim is still true of the changed file: the pin is refreshed.
  The entry keeps its source commit, and its note says whose bytes
  the new SHA-256 is and names the re-reading, as the release's first
  fix, the CHERI integration, and Revision 4 did;
- the claim, as it is worded, is about the release, and a record of
  the release holds the fact: the entry is pointed at that record.
  The release's records hold 25 of the 53 files, by copy or by
  digest: the lock, its closure, and the evaluator's recipe among
  them. They hold none of the monitor's sources, the MVP's scripts
  and tests, the saved captures, the guest's pins, or the log's
  profile. For those, this branch does not exist;
- neither fits: stop 2.

In no case does a row's claim, its methods, or its non-claim change.
The saved captures that the ledger cites are not changed at all: they
are kept byte for byte and judged against the expectations of their
time, in a set pinned by SHA-256, as M6, M7, and M9 kept theirs.

The claim ledger gains rows for the clause's parts (methods: host unit
test, adversarial test, semantic checker, emulation), and non-claim
rows for the limit's sentences. They are kept apart from the release's
rows: the ledger's release object and its release-surface check name
MVP 1.0 alone and are unchanged; the candidate's rows carry their own
scope, and the ledger's tool checks them as a second set. The
forbidden-phrasing check must pass on the new page. "Isolated",
"sandboxed", and "verified" are not used of the boundary.

## Accepted decisions that this plan changes, by name

S3-D.8 asks this plan to name each one for the responsible human's
decision. Accepting this plan decides them as the right-hand column
says. None changes anything at the tag `mvp-1.0`.

| Accepted text | Says | With M11 |
| --- | --- | --- |
| D8, scheduling | "no HS time slice" | One HS-level timer tick on each VS-domain hart, which reads a ring and resumes the same guest. Still no scheduler, and no guest switch (D-7) |
| D8, the exits | "an exact accepted-exit set per scenario" | Each scenario's set gains the tick and loses the IPI (D-7) |
| D8, the firmware surface | "grows from Base, DBCN, and SRST by HSM and IPI" | The monitor's own calls are Base, the debug console, system reset, HSM for the status and the start of harts 1 and 2, and the boundary extension's two functions. The build keeps IPI for the probe images; no scenario image calls it (D-2, D-8) |
| D15, signalling | "the SBI IPI extension for signalling in both directions" | Rings read on each hart's own tick. D15's hart start and its rings stay (D-7) |
| The M0 plan: its table's rows on HS interrupts and on the timer comparator; its departure 2; its Q4 | The IPI at guest level and in hart 0's wait; "no `stimecmp` write but hart 0's budget"; the IPI probe in the scenario | The timer at guest level and in every wait; each hart writes its own comparator; a tick probe (D-7) |
| The M0 plan: its boot steps 4 and 5 | Hart 0 enables the software and the timer interrupt; it starts each hart at the hart entry and "polls `hart_get_status(h)` until `STARTED`", within a timeout | Hart 0 enables the timer interrupt alone. It starts each hart at the stub and checks the start's result; the status poll and its timeout go, and READY shows the hart's progress (D-6) |
| The M0 plan: its departure 7 | The firmware calls beyond the first four are "HSM start and status, IPI send", at one call site | IPI send goes, and the boundary extension's two functions come in. The one call site is kept |
| The M0 plan: the image checker's rules for the comparator's and the pending bit's writers, and its mutation for the first | One writer of each | The rules follow D-7, each with its mutation |
| The M0 plan's Q10 fallback, its revision M0-A.3, and revision M1-B | A VS-domain hart whose ring cannot carry its failure, or whose failure the control hart does not acknowledge, prints its own failure and resets; `ring-full`'s declared outcome is that print | From M11-4 on, every image keeps room in each outbound ring for the last records (D-8). A confined VS-domain hart makes no firmware call: it posts its failure and parks. A hart that is not confined keeps the print and the reset after a failure that is not acknowledged, or that its ring cannot carry. `ring-full` is declared again under the boundary (D-12) |
| The M0 plan's revisions M0-A.1 and M0-A.2; the M6 plan's D-4 | The pool, the hart region, the MVP region, and the image's size at fixed places: "The MVP-owned extents do not move". One started hart beside the monitor's own is accepted, and the shim's rule starts hart 0 | The extents move and the image grows, within D-4's bounds. A boundary-on image boots on hart 0 alone (D-6). Boundary-off images keep the shim's rule |
| The M2 plan's Q14 and Q15, and its revision M2-A | A management record is delivered with "one IPI to the target's hart"; the checker's rule for the mode in which the IPI probe arrives | Delivered by the record, found at the target's tick. The rule is stated for the tick probe (D-7) |
| The M7 plan's D-2 | The output bound holds "before hart 0 drains" | The drain comes at the control hart's tick. The bound is kept, and measured again (stop 13) |
| The markers and counts that accepted plans fix | `BE_MVP:02`'s `ipi=` field and its list of harts 1 to 7; `:08`'s status; `:09`'s interrupt-enable value; `:11`, the IPI probe; `:12`'s `ipi=1` and "exits = sbi + ipi"; `:13`'s wake and idle counts; the `hgatp` values; the firmware's SBI version | Each is derived again and pinned: the boundary's fields and harts 1 and 2 in `:02`; no status in `:08`; the timer's enable in `:09`; a tick probe; tick exits counted apart; the new pools' addresses; version 3.0 |
| The firmware's SBI version in the port; the tool lock's firmware pin; the `sbi-3.0` variant | Every plain image requires 2.0, the version of the firmware pinned today | Every plain image requires the base's 3.0 from M11-2 on, by a new rule of the MVP's port; the CHERI variant's rule is retired. Two firmware pins: the M11 build, and today's, kept for the firmware-version negative, which is the `sbi-3.0` variant declared again and renamed `firmware-version`. No plain image of the working line boots under the board's resident firmware (D-2, D-12) |
| The two tool locks, and what pins them | The MVP's lock and its evaluator closure as last refreshed for `l1` on 2026-10-26, with the roles and pins added since; the model's tool profile as M3 moved it; the interpreter version that the mutant generator's self-test pins; the ledger's two rows on the lock | Moved to the development host in M11-2's first commit, unless the responsible human has directed the move earlier: the files that "The development host" lists, and no other, with the baseline runs. `verify` runs on a host that reproduces the last record (Q22) |
| The harness's pass rule | QEMU exits by itself with status 0 | QEMU reports the guest's shutdown, the oracle reads, and the harness ends QEMU (D-10) |
| S3-C's stop (e) | No change to monitor source beyond comments; none to an accepted model file or gate beyond those enumerated | Lifted for the monitor changes that this plan's work packages enumerate, and for these model edits: the generated layout constants; the concrete model's exit decision and ring steps with their readings (D-11); the `python3` version in the model's tool profile and in its tool check; and the interpreter version that the mutant generator's self-test pins. For nothing else |
| The claim ledger's evidence pins for the release's rows | Each refresh so far went to the responsible human: the release's first fix, the CHERI integration, and Revision 4 | A work package refreshes or re-points a pin in the commit that changes, moves, or removes the cited file, by the rule in "Claim text". No claim, method, or non-claim changes that way: that is stop 2 |
| The M8 plan's rule for the target digests | Written again only on the responsible human's direction | Accepting this plan is that direction, at each merge that D-11's rule names |
| The rule that the plain images equal MVP 1.0's byte for byte | The CHERI check's guard | The candidate's plain images are new. The guard's record is derived again at the candidate (D-11) |
| The glossary and the hardware roadmap, maintained pages | PMP as "the subject of M11" | Updated with the result |

Not changed, though S3-D.8 names them as possible: D16 and stop
condition 3 (D-6, D-9); S3-C's stop (i), which applies as written
(D-11). Also kept: I16 and the M8 specification's P2, since no word is
added between harts (D-8); the M6 plan's D-5, every privileged effect
behind one executor, and its Q3, the staging reserve; the M7 plan's
Q13, the guest Image's budget, by D-4's cap; and the M0 plan's probe
table, with its IPI rows (D-12). The board policy, S3-A.1's items 1 to
8, and stops (a) and (j) are not touched (D-15).

## Work packages

| WP | Delivers | Exit |
| --- | --- | --- |
| M11-1 | This plan; its review packet | The plan accepted |
| M11-2 | **Preparation.** First, both tool locks pass on the development host, by a move if one is still needed, with the baseline runs and the baseline `verify` on its host (below), and the step that lists, from the arms' own logs, each solver run near its limit. The proof-impact review (D-11). The firmware base: its pin, its default configuration with no addition yet, the build rules on the host and inside the evaluator, the binary's pin in the tool lock. The switch: the MVP port's new rule for the firmware's SBI version in every plain image, with the checker's expectation and the firmware-version negative. The oracle: the client of QEMU's monitor, the end-of-run read, the harness's new pass rule, and its self-tests (F20) | Both locks pass on the host, and both baselines hold. The review written. The firmware binary identical between the host's build and the evaluator's. Every scenario and variant passes under the base with no change but those named here, and the rehearsal runs under it. The oracle reads all eight harts' PMP registers and a named word of memory at the end of every run. The list of call families that the boot chain before the monitor uses |
| M11-3 | **The layout** (D-4), with the boundary off: the linker scripts, the sections by role, the blocks by writer, the boot-only extents, the layout header, the image checker's rules for every extent, the board tools' layout rule, stage 1's generated constants and readings | `check` passes on both toolchains. The image checker refuses a mutated layout. `model-check` passes with stage 1 re-proved and no statement changed |
| M11-4 | **Signalling** (D-7), with the boundary off: ticks on each VS-domain hart, the control hart's ring read on its tick, the tick probe, the room kept for the last records, the failure classes that M11 adds, no IPI in any scenario image; the trap path's and the waits' changes; host tests; the scenarios' expectations and the capture checker's rules derived again; the concrete model's exit decision and ring steps | `check` passes on both toolchains with no IPI call in any scenario image. The counts are pinned. The shell sessions pass, and each ring's peak stays within its budget. `model-check` passes with no statement changed |
| M11-5 | **The descriptor** (D-3): the schema, the generator, the device-tree backend with the expected tables for both PMP modes, the independent checker with its mutations, the authority report's section, the two pinned base device trees and their check | The checker passes every scenario's descriptor and refuses every mutation. No profile exceeds ten entries. The generator's and the checker's outputs are identical between toolchains and between the host and the evaluator. It completes after M11-3, whose layout it reads |
| M11-6 | **The firmware additions** (D-2): the patch series; the reduced configuration, with its list of families and their callers; and the firmware's own tests, which are bare-metal payloads run under QEMU in both PMP modes and judged through the oracle. They establish F1, F2, F5, F6, and F8 to F14 again, and test the guard's four conditions, the filter, the three counts, the cache-block control, the readback against a table cut short, the record, each trap path that the build keeps, a tree one region over the budget, and D-6's sequence in both orders | Every firmware test passes in both modes. The patched binary is reproducible and pinned. Every scenario still passes under it with the boundary off. Every line of the series has been reviewed against D-2's rules, and the review is recorded |
| M11-7 | **Step 1: the VS-domain harts confined**, the control hart not. The stub, the identity check, the failure path of D-8; the boundary-on runs of every scenario; the hostile-monitor images for a VS-domain hart, with their discrimination builds; the boundary's own negatives | Every scenario passes with the boundary on, with D-10's four checks. Every hostile-monitor image passes, and its boundary-off run shows each effect that can be discriminated. A checkpoint report goes to the responsible human; no decision is needed to continue |
| M11-8 | **Step 2: the control hart confined.** Its `confine`, its confined entry, its call list; the hostile-monitor images for the control hart; the parked harts' tests; the run matrix of D-12 | As M11-7, for all three harts and all eight |
| M11-9 | **The words and the gates.** The claim's page and the ledger's rows, with the ledger tool's second set; the guide's section on the boundary and on building the firmware; the AI-assistance disclosure; the glossary's and the hardware roadmap's rows; the gates from a clean checkout at the candidate; the evidence record; the result packet | The gates pass at one exact candidate commit. M11-E's result is presented |

**S3-C's stop (i) in M11.** M11's work lands on one working branch,
and the merge that stop (i) speaks of is each work package's merge
into it. D-11 gives the rule and the four points that this plan
expects: M11-2, M11-3, M11-4, and the candidate.

**The development host.** The MVP plan requires "A tool lock that the
development host can satisfy", and makes a lock that it cannot satisfy
with open tools a stop (its stop condition 5). M11's gates need the
host: `evaluate` compares the host's build with the evaluator's.
Neither lock is satisfied today (F23). So M11-2 begins by making both
pass. If they already do, because the responsible human directed the
move earlier, nothing is left to change. Otherwise one commit moves
them, on the direction that accepting this plan gives (Q22), and
changes these files and no other:

- the MVP's lock and its closure, by the lock's own `refresh`, with
  each new package's digest recorded from a verified file. The commit
  explains each package that the refresh adds or drops, as the earlier
  refreshes did. The evaluator's recipe changes only if its list of
  base packages removed by name must;
- the model's tool profile and the version string in its tool check,
  for `python3` alone;
- the interpreter version that the self-test of M8's mutant generator
  pins, in its check and in its comment, after that self-test's
  selection case has shown the same selection under the new
  interpreter;
- the claim ledger's two rows on the lock, with the ledger's
  rendering. The row on the tool lock keeps its claim, and its pin is
  refreshed with a note, as the release's first fix did. The row on
  the evaluator image names that image by the old closure's digest,
  so its evidence is pointed at the release's record,
  `mvp/results/20261108-release/`, by its manifest: that record holds
  that lock and that name. Neither row's claim, methods, or non-claim
  changes;
- the lock's table in `mvp/README.md`.

The verifier image is not affected: its closure is its own.

At the lock commit, or at M11-2's first commit if the locks already
pass, and before any other change, the baseline is run: `check`;
`evaluate`; the U-Boot rehearsal, which uses one of the roles that
differ; `kernel-repro`, the one gate that builds the guest kernel a
second time, with build programs that the host's compiler makes;
`model-check`; and the model's evaluator. The model's evaluator image
is not pinned by version: it must pass its tool check with the moved
profile, and the packages of the image that the baseline builds are
recorded, as the release recorded its own.

The baseline is compared with the last record made under the old
lock, `mvp/results/20261109-cheri-integration/`:

- every flat image must have the digest that the record holds for it,
  with none missing and none extra. The flat images are the monitor's
  binary and its boot images of three kinds, 162 files in that record.
  The CHERI check selects the same files when it compares images with
  a record; the baseline makes the comparison itself, because that
  check applies its rule only while a record's build inputs are
  unchanged, and the lock is one of them;
- `check`'s deterministic records must equal the record's, byte for
  byte: the image checker's, the variants', the probes', and the
  capture checker's self-test and mutation test. That shows that the
  seeded selections of those tests did not move with the interpreter.

A difference in either, or a tool check that fails inside the model's
evaluator, is stop 11.

**The host for `verify`.** The arms limit each solver run by time, so
their counts depend on the host and on its load: a run that crosses
its limit is a non-result, and one killed for want of memory is
another. Bytes that change no behaviour can move a run's time: one
run took five times as long after inactive lines of a header changed
the solver's encoding (F23), and M11 changes headers of both leaves
at three of its points. Every `verify` record was made on one
workstation, and the development host has a quarter of its
processors. So the question is whether a host reproduces the last
record,
`mvp/results/20261109-verify-cheri-integration/`, which was made at
the target digests that the line has now: every file equal, with only
the run metadata that the record's own page sets aside differing.

- The responsible human names the host (Q22). It need not pass the
  moved lock: `verify` runs no lock check, and what it builds on its
  host, the port and the two monitor images, its digests and
  sequences suites bind. The baseline records that host's lock check,
  its processors, and its memory.
- `verify` is run there first at the lock commit, or at M11-2's
  first commit if the locks already pass, as a baseline, and D-11's
  four points are run on the same host.
- Each run's record lists every solver run that took more than nine
  tenths of its limit. The records keep row totals only; each run's
  time is in the arms' logs under `build/`. So M11-2 adds one step
  that reads those logs after a run and writes the list beside the
  record. The arms themselves do not change. The proof arm's logs
  keep a job's time and not each goal's, so its entries are jobs.
- A baseline that differs from the last record is stop 11, before M11
  changes anything else. If the only differences are runs that
  crossed a time limit, the responsible human may accept that run as
  the baseline.
- The same holds at D-11's four points: a count that changes only
  because a run crossed its limit is recorded as that, and goes to
  the responsible human under stop 9 with that reading. It is never
  passed over.

**The gates** at the candidate: the tool lock; `check`, which now
includes the firmware's own tests and the Smepmp runs; `evaluate`, with
every image and the firmware binary identical between the host and the
evaluator; the U-Boot rehearsal, under the boundary; `kernel-repro`;
`model-check`; the model's evaluator; `verify`, with every suite, on
its host; and the CHERI check.

**Order.** M11-2 first. Then M11-3, with M11-6 beside it; M11-4 and
M11-5 follow M11-3; M11-7 needs M11-3 to M11-6; M11-8 follows M11-7;
M11-9 is last. The work follows the project's standing practice for
AI assistance, which its disclosure describes: every change is
reviewed line by line before it is merged, and the checks and the
gates are run on the merged tree. The firmware additions are written
under D-2's last paragraph.

## Soft limits (re-evaluation stops)

**Counting rule:** added lines by `git diff --numstat` from this
plan's acceptance, in C, assembly, linker scripts, Python, shell, Make,
and device-tree source, tests included; generated files, fixtures,
JSON, Markdown, and the model's Rocq are excluded and reported apart.
The patch series is counted by the lines that it adds to OpenSBI.

| Lane | Soft limit | Estimate |
| --- | --- | --- |
| The firmware additions | 600 | 300 to 450 |
| The firmware's own tests, and the firmware's build rules | 2,500 | 1,200 to 2,000 |
| The monitor: the layout, signalling, the stub and entries, the failure path, the test hook; with the image checker's rules and the board tools' layout rule | 3,500 | 1,800 to 2,800 |
| The descriptor's generator, backend, and checker, with their tests | 3,500 | 2,000 to 3,000 |
| The harness, the oracle, the capture checker's rules, the scenarios' generator, the ledger's tool, and the model's tools | 3,500 | 1,800 to 2,800 |

A limit exceeded is a stop for re-evaluation of the limit, never a cut
to the work. Only the responsible human re-sets one. Checkpoints:
after M11-4, after M11-6, and after M11-7. The firmware additions'
limit is the one that matters most: every line of them is in the
running trusted base.

## Stop conditions (each returns to the responsible human)

The MVP plan's stop conditions 1 to 7 and (a) to (o) stand beside
these.

1. Any need to change an accepted byte or an accepted document's text,
   other than what "Accepted decisions that this plan changes" names.
2. Any claim-text change other than the page and the forms fixed
   above.
3. A profile that needs more than the platform's entry budget, or an
   extent that I22 forbids it, boot-only code among them; a layout
   that needs the image beyond D-4's bounds, or that cannot keep the
   log's five self-report ranges; an honest run in which
   one of M-mode's counts is not zero and no change inside I22 and D-8
   removes it.
4. A tested attempt that has an effect with the boundary on. The
   counterexample and a failing test are recorded first.
5. Any sequence of firmware calls, traps, or interrupts that gives a
   confined hart another profile or its boot access back; or a design
   step in which M-mode would install or select a profile from a
   range, a profile, or a hart that HS-mode code supplies (S3-D's stop
   (n), as this plan reads it).
6. The firmware base failing a scenario that passes today, apart from
   the changes that M11-2 names; or a need to move the base's pin.
7. A firmware binary that differs between the host's build and the
   evaluator's.
8. The U-Boot rehearsal unable to run under the base, or under the
   boundary.
9. A stage 1 statement, or a leaf's contract, that would have to
   change; a leaf's verdict or count that changes; a global axiom.
10. The CHERI check failing at the candidate.
11. A tool that the tool lock does not name. At the lock commit, or
    at M11-2's first commit if the locks already pass: a file to
    change beyond those that "The development host" lists; a lock
    that the host cannot satisfy with open tools; a flat image, or a
    deterministic record of `check`, that differs from the last record
    made under the old lock; a tool check that fails inside the
    model's evaluator; or a baseline `verify`, on the host chosen for
    it, that differs from the last record.
12. The oracle unable to read a hart's PMP registers, its
    cache-block control, or memory, with the machine stopped at the
    end of a run; or a run whose outcome differs with the oracle
    attached.
13. An accepted expectation that breaks and that this plan does not
    name as changed: for example a concurrency check, a shell session,
    the run's budget, or a ring's peak over its budget; or an existing
    variant whose intent cannot be kept under the boundary.
14. A pinned base device tree that differs from what the locked QEMU
    generates; a machine without Smepmp, or without the cache-block
    management extension, where the matrix needs it; or
    an emulator behaviour of PMP that a test depends on and that the
    privileged specification does not give.
15. A failed discrimination: an attempt that the boundary-off runs
    cover and that shows no effect there.
16. A soft limit exceeded.
17. Any board step (S3-D's stop (j)); any naming under stop (k); any
    M-mode code outside D-2's rules, licence, location, or build (stop
    (m)); anything that stop (o) bars.
18. Any push, merge, tag, publication, or release step.

## Open questions and defaults

| ID | Question | Default | Alternative |
| --- | --- | --- | --- |
| Q1 | The design | C: per-hart OpenSBI domains entered by a guarded one-way call, with the additions of D-2 | B, with no M-mode code, which meets neither M11-R2 nor M11-R5 to M11-R7 and loses hart start; or D now |
| Q2 | The firmware base | The development commit that was characterized, pinned exactly | The first upstream release with K3 support, once it exists, with the guard derived again; or v1.9 with the entry form of the move, which has no K3 support |
| Q3 | The reading of S3-D's stop (n) | Revision 4's I24: M-mode never installs or selects a profile from what HS-mode code supplies, and no call widens a profile. A kept call may take a buffer, checked against the caller's profile | The words as they stand: no kept call takes an address. A confined control hart then cannot print through the firmware, and the console needs a design of its own before M11-8 |
| Q4 | Signalling after confinement | Rings read on each hart's own timer tick; no IPI | A relay call in M-mode for the harts that the descriptor pairs; or interrupts through the interrupt controller's files |
| Q5 | A confined VS-domain hart's calls | None; it keeps room in its ring for its failure record, in place of its last print | Keep the failure path's console write and reset, which lets a breached hart print anything and reset the system |
| Q6 | A confined control hart's reset | The shutdown type only | Any reset type |
| Q7 | The additions' licence | BSD-2-Clause, as OpenSBI's | GPL-3.0-only, which keeps them from being offered to OpenSBI as they are |
| Q8 | Where the additions live | A patch series in this repository | A public fork of OpenSBI |
| Q9 | Who writes the additions | An AI tool that can be disclosed by name, afresh from this plan, with a record in each change | Any tool, with the additions then never offered to another project |
| Q10 | PMP modes under emulation | Both: plain PMP for every run, Smepmp as well for the hostile-monitor images, one run of each scenario, and the firmware's tests | Plain PMP only |
| Q11 | Machines for boundary-on runs | `k3-like` alone; the other machines' rows run with the boundary off | Also `rva23` and `plic`, each with base device trees of its own |
| Q12 | The tick's period | 2^18 timebase ticks for both roles | A shorter period for the control hart |
| Q13 | The descriptor's identity and the measurement log | Not a log record in M11: printed by M-mode, compared by boot code and by the checker | A record of the log, which changes the log's profile version |
| Q14 | M11's results | Two: M11-E accepted at its own commit, then M11-B under the amendment and an addendum | One result, with the board |
| Q15 | The specification's words | No unit is named in M11 (D-13) | A naming now, with its three differences stated |
| Q16 | The probe images | Boundary off, with their IPI phases, so the build keeps the IPI family | Their IPI phases dropped, and the family removed from the build |
| Q17 | The hostile tests' form | A test hook compiled into variant images of the scenarios | Separate payloads without guests |
| Q18 | The CHERI check during M11 | A gate at the result (S3-D's Q54) | A gate throughout |
| Q19 | Where the clause lives | A page of its own; MVP 1.0's claim page unchanged | A section of MVP 1.0's claim page |
| Q20 | M-mode's record on the board | Left to the board addendum, with its limit stated: a breached hart that can print can imitate it | A record that carries a value which only M-mode holds, designed now |
| Q21 | A further independent review of this plan | Those made before it was presented | Another, by a reviewer that the responsible human names |
| Q22 | The gates' hosts | Both tool locks moved to the development host in M11-2's first commit, with the baseline runs, unless the responsible human directs the move earlier as a change of its own. `verify` on the host that the responsible human names; if none is named, it is tried on the development host, and a baseline that differs is stop 11 | Every gate inside the evaluator image, with the host's lock recorded as failing: `evaluate` refuses to run under a failing lock, so that needs a driver outside the repository, and it has no host build to compare. Or a decision in advance that the development host's own baseline is the reference for `verify`, with each count that differs from the last record explained by a time limit |

## What acceptance would authorize

M11-2 to M11-9, on a working branch from this plan's accepted commit,
with Q1 to Q22 at their defaults unless answered, under the stop
conditions above; the changes to accepted decisions that this plan
names, the move of both tool locks to the development host among
them; the refresh or re-pointing of the ledger's evidence pins by the
rule in "Claim text"; M-mode code of the project's under D-2 and
nowhere else; and the target digests written again at each merge that
D-11's rule names.

It would authorize no board command, no firmware write, no card, and
nothing of M11-B; no claim text beyond the page and the forms fixed
above; no change to anything at the tag `mvp-1.0`; nothing sent to
another project; and no push, merge, tag, or release step. Each commit
on the public line stays the responsible human's to sign off and push.

## Review record

Independent, read-only, automated reviews read the drafts of this plan
before it was presented. Their findings and their disposition are in
the plan's review packet, in the project's internal records.

## Status record

```text
mvp_m11_plan=accepted-if-its-proposing-commit-is-on-the-public-main-with-the-responsible-human's-sign-off;otherwise-proposed
mvp_m11_plan_basis=mvp-plan.md-Plan-revision-S3-D;security-model-v1-Part-1-Revision-4
mvp_m11_design=per-hart-OpenSBI-domains-entered-by-a-guarded-one-way-firmware-call;M-mode-additions-in-one-patch-series
mvp_m11_firmware_base=OpenSBI-ed70256dd22c09962d146e433834239825ef0616;SBI-version-3.0
mvp_m11_signalling=rings-read-on-each-hart's-own-timer-tick;no-IPI-in-any-scenario-image
mvp_m11_stop_n_reading=Revision-4's-I24;put-to-the-responsible-human-as-Q3
mvp_m11_failure_path=360-bytes-kept-in-each-outbound-ring-for-the-last-records;no-word-added-between-harts
mvp_m11_results=M11-E-under-emulation;M11-B-on-the-board-not-authorized-here
mvp_m11_work_packages=M11-1..M11-9
mvp_m11_decisions_changed=D8-tick-exit-set-and-firmware-surface;D15-signalling;M0-rows-on-interrupts-and-comparator;M0-steps-4-and-5;M0-departures-2-and-7;M0-Q4;M0-checker-rules;M0-Q10-fallback-M0-A.3-and-M1-B;M0-A.1-M0-A.2-and-M6-D-4;M2-Q14-Q15-and-M2-A;M7-D-2-measured-again;markers-and-counts;firmware-SBI-version-pins-and-sbi-3.0;both-tool-locks-moved-to-the-development-host;a-named-host-for-verify;the-ledger's-evidence-pins-refreshed-or-re-pointed-by-rule;harness-pass-rule;S3-C-stop-e-for-the-enumerated-changes;M8-target-digests-at-each-merge-that-D-11-names;plain-image-identity-record;glossary-and-hardware-roadmap
mvp_m11_decisions_kept=D16;stop-condition-3;S3-C-stop-i;I16-and-P2;the-log's-profile-and-its-five-self-report-ranges;M6-D-5-and-Q3;M7-Q13;M0-probe-table;S3-A.1-items-1-8;stops-a-and-j
mvp_m11_claim=a-page-of-its-own;one-clause-with-a-form-for-each-outcome;MVP-1.0's-claim-page-unchanged
mvp_m11_stops=1..18
mvp_m11_open_questions=Q1-Q22-defaults
mvp_m11_board=not-authorized;needs-the-inventory-the-amendment-and-an-addendum
```

## Decision record

The responsible human's decisions on this plan's stops and questions
after its acceptance, each by his reply and its date. Each changes the
text above as it says; the text above is otherwise as accepted.

- **2026-11-11, `ar: yes`** (stop 11: a tool that the tool lock does
  not name). The firmware base's build runs the RISC-V archiver, which
  the lock did not name. The lock gains a role, `cross_ar`, for the
  archiver of the closure's `binutils-riscv64-linux-gnu` package, which
  the closure already held.
- **2026-11-11, `review: yes`**: the proof-impact review's three
  items, recorded in the review itself
  ([`mvp-m11-proof-impact.md`](mvp-m11-proof-impact.md)).
- **2026-11-12, `verify: wp3`** (stop 11: a baseline `verify` that
  differs from the last record; Q22). The host for `verify` is the
  development host, `lx2`. Its baseline at the lock commit equals the
  last record in every suite but the WP arm, which proved 127 of 134
  goals where the record has 130: six provers at once on four cores
  took three goals past the prover's 60 s limit. So the WP arm runs at
  most as many provers at once as the host has physical cores less
  one, and never more than six, and at most as many mutant jobs at
  once as those cores allow, and never more than two: three and one on
  `lx2`; six and two, as before, on `l1`, the workstation that made
  the last record. This changes one arm, against "The host for
  `verify`" ("The arms themselves do not change"). The WP arm alone is
  run again at the lock commit with this change. If its records equal
  the last record's, the baseline is the run of 2026-11-11 with those
  records, and the one qualification case whose prover stopped at its
  limit is accepted as a time-limit crossing; otherwise the baseline
  returns to the responsible human. D-11's four points run with the
  changed arm.
- **2026-11-12, `oracle: absent`** (stop 12: the oracle unable to read
  a hart's PMP registers at the end of a run). Two of D-12's machines
  cannot show them, and both run with the boundary off: QEMU's
  `rva23s64` CPU has no PMP, and the CHERI variant's emulator ends its
  process at the guest's shutdown, so no stopped machine remains to
  read. Each machine row declares each register class readable or
  absent. On `rva23` the oracle requires and records the PMP
  registers' absence, and reads the rest as on the other machines. The
  CHERI variant's runs end as before, with no oracle attached, and each
  attempt keeps a fixed record that says so. A boundary-on run must be
  on `k3-like` with every class readable, or it is refused before QEMU
  starts. D-12's `rva23` row has no PMP mode, and M11-2's exit "The
  oracle reads all eight harts' PMP registers" holds of every run on a
  machine whose CPU has PMP.
- **2026-11-12, `harness: 7000`** (stop 16). The soft limit of the
  lane "The harness, the oracle, the capture checker's rules, the
  scenarios' generator, the ledger's tool, and the model's tools" is
  7,000 counted lines, in place of 3,500: M11-2 alone reached the
  earlier limit.
- **2026-11-12, `fw: 800, fw-tests: 3000, monitor: 6000`** (stop 16).
  Three soft limits are re-set:
  - "The firmware additions": 800 counted lines, in place of 600.
    M11-6's patch series adds 690: 431 of code, 156 of comment, and
    103 blank, each addition a row of D-2.
  - "The firmware's own tests, and the firmware's build rules": 3,000,
    in place of 2,500. They stood at 2,243 before the host unit test.
  - "The monitor: the layout, signalling, the stub and entries, the
    failure path, the test hook; with the image checker's rules and
    the board tools' layout rule": 6,000, in place of 3,500. M11-3's
    content adds 1,914, and M11-4's design about 1,790, most of them
    host tests and the image checker's rules; M11-7 and M11-8 follow.
