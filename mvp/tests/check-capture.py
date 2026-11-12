#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 James Morris <jamorris@linux.microsoft.com>
"""Check one MVP serial capture against its image's expectation file.

  check-capture.py CAPTURE --expect FILE [--mode direct|kexec|uboot]
                   [--monitor riscv|cheri [--cheri-mutations]]
                   [--pins F] [--sbi-version V] [--kexec-fdt ADDR]
                   [--image BOOT_IMG | --image-bytes N [--image-md5 HEX]
                   [--image-crc32 HEX]]
                   [--toolchain gcc|clang] [--report REPORT] [--json OUT]
                   [--kernel IMAGE --dtb DTB]
                   [--typed TYPED --nonce NONCE --session SESSION]
                   [--reference REF] [--build-root BUILD] [--log-json OUT]
  check-capture.py --check-image TOOLCHAIN:IMG:BIN[:VARIANT] [--pins F]
                   [--kernel IMAGE] [--expect FILE --report REPORT]
  check-capture.py --self-test --expect-dir DIR ... [--pins F] --report R ...
                   --kernel IMAGE --dtb DTB
  check-capture.py --mutation-test (as --self-test)
  check-capture.py --write-fixtures OUT --expect-dir DIR ... [--report R ...]
                   [--kernel IMAGE --dtb DTB] [--image KIND=BOOT_IMG ...]

Purpose: the harness's Check stage (planning/mvp-m0-plan.md, "Scenarios and
the harness", "Markers"). The expectation is data: tools/gen-scenario.py
writes one file per image (the scenario, each negative variant, each probe
image), and this checker reads it; nothing here names a scenario's lines.
Trust: it reads the capture once (S1 H26), splits it into hart 0's monitor
stream and each domain's prefixed stream, and judges each stream on its
own; it executes nothing it reads. Scope: M0's captures, QEMU (direct boot
of the boot ELF under OpenSBI), Linux kexec (the rehearsal and the board
until release candidate 1; kept test-only for the retained kexec captures,
planning/mvp-m5-plan.md Q4), or U-Boot's booti (the board from a reset, and
the U-Boot rehearsal in QEMU, planning/mvp-m5-plan.md); a verdict, findings,
the probe stops, and the recorded costs.

The capture: CRs dropped. Only loader output (OpenSBI's banner, Linux up
to its kexec handoff, or the firmware and U-Boot up to `Starting kernel
...`) precedes the first marker line; from there every non-blank line is a
marker line that starts with its tag (BE_MVP_SHIM:, BE_K3_B3:, BE_R3:,
BE_MVP:, or a domain's prefix), holds no other tag, and is printable ASCII;
a domain line's text is at most 256 bytes and mixes no second line (no
MVPINIT or kernel timestamp after its start); the last line is whole.

  direct  exactly one `Boot HART ID` and `Runtime SBI Version` in the
          banner; --sbi-version, when given, must match
  kexec   Linux's handoff, each line once and in order: `kexec_core:
          Starting new kernel`, `Will call new kernel at L from hart id H`,
          `FDT image at F`, `Bye...`; F the loader's (--kexec-fdt), or the
          slot after the image (--image), or an aligned slot after L below
          the windows; the SHIM line's fdt is F
  uboot   U-Boot's booti of the image (planning/mvp-m5-plan.md, "The boot
          path of release candidate 2" and "Tool changes (M5-2)"): exactly
          one U-Boot banner (`U-Boot 20yy.mm ...`, the fact uboot_banner),
          and exactly one SPL banner (`U-Boot SPL 20yy.mm ...`) without an
          OpenSBI banner (the board, whose OpenSBI prints none), at most
          one with one (QEMU); then, after the last autoboot line
          (`Autoboot in N seconds`, the BSP's, or `Hit any key to stop
          autoboot`, before which the BSP's U-Boot loads env_k3.txt with a
          `bytes read` line of its own), each of these once and in order,
          a leading three-decimal `[ nnn.nnn] ` stamp (the BSP's U-Boot
          lines; never Linux's six) stripped and the line stripped:
            N bytes read in T ms ...            be_ld's load; N the
                                                image's size (--image or
                                                --image-bytes)
            md5 for 140000000 ... X ==> D       be_ld's digest, one line of
              (or crc32 for 140000000 ...       either form, of the N bytes
              X ==> C)                          from the load address (Q2),
                                                X their last byte's: D the
                                                image's MD5, 32 digits
                                                (--image or --image-md5),
                                                or C its CRC-32, 8 (--image
                                                or --image-crc32)
            Moving Image from 0x140000000 to 0x108000000, end=E0
                                                booti's move to L, E0 = L+N
            ## Flattened Device Tree blob at A
            Booting using the fdt blob at 0xA
            Loading Device Tree to F, end E ... OK   (the board), or
            Using Device Tree in place at F, end E   (QEMU; F = A)
            Starting kernel ...
          the addresses lower-case hex as U-Boot prints them; then only
          blank lines and the BSP's `fail to get alias node efuse_power`
          and `Removing MTD device #0 (nor0) with use count 1` up to the
          first marker; the SHIM line's fdt is F, U-Boot's relocated
          control device tree, and [F, E] (E U-Boot's last byte) lies
          outside every MVP extent (the layout rule: the core,
          the pool, the hart region, the MVP region, the staging region
          with the kexec FDT slot after it, both windows, and the shared
          pages); no kexec FDT applies. The digest line is either form,
          wherever the capture was made: the board's be_ld types md5sum,
          since this BSP's crc32 prints nothing (its usage is upstream's,
          but no line comes; the characterization of 2026-10-30), and the
          QEMU rehearsal's types crc32, since upstream's
          qemu-riscv64_smode_defconfig has no md5sum; --image gives both
          digests. Without the image's size or digest the lines are
          required and recorded, not compared. The facts:
          launcher_mode=uboot, uboot_banner, spl_banner (or none),
          uboot_watchdog (U-Boot's `WDT:` line, when it prints one),
          load_bytes, load_digest_kind (md5 or crc32) and load_digest (its
          hexadecimal digits), moving_from, moving_to, moving_end,
          fdt_blob, fdt_loaded (F), fdt_end (E), fdt_in_place (true or
          false). With an OpenSBI banner (QEMU) the banner is direct's, and
          so is the boot hart; without (the board) the boot hart is 0: a
          start-rule line, or a SHIM line naming another hart, is a finding
          (the board tools' stop condition 6), never a refusal

The shim (Plan revision M0-A.2): a boot hart B other than 0 prints
`BE_MVP_SHIM: boot_hart=0x<B> starting hart 0` first, and B is the
banner's boot hart (direct, and uboot in QEMU) or the handoff's hart
(kexec); hart 0 then prints exactly one SHIM line (the expectation's first
line). BE_MVP:02 prints `started=<B>` (decimal) with B's status 0 and every
other hart's 1, or `started=none` with every status 1 when there is no
rule line; the shim-rule variant prints its declared rule line and
`started=none`.

Verdicts: PASS, the capture shows its expectation; REFUSED, the precondition
M0-A.2 declares failed (the boot hart is a domain hart of the run, which
BE_MVP:02 names as `started=<B>` with B STARTED, then exactly `BE_MVP:FAIL
firmware`); STOP, a probe value fired a stop condition the plan names;
FAIL, anything else. Exit status 0, 1, 3, and 4 respectively.

Monitor stream: the expectation's control lines in order, each matching its
regular expression; per domain, BE_MVP:09, :10, :11, and :12 in that order,
the two domains' chains in either hart order (the plan's "either hart
order"); then :13 and :14, after which no line of any stream may follow.
Probe images: one fixed sequence with the probe lines in place.

Pass (the scenario, sbi-time, shim-rule): each domain's stream holds the
required lines in order with its own guest ID, every MVPINIT line once (the
STEP line once per step, t_ms rising), no other MVPINIT line, the memory
within its window, and no rejected substring (panic excepted in the command
line); its lines lie between its own :10 and :12, and its :11 follows its
first line. Counters, from each :12: those the expectation fixes (ipi=1,
srst=1, time=0 or above 0 for sbi-time, ...) and ranges (exits, ring_peak,
at most half the outbound ring: stop condition 3); exits = sbi + ipi; sbi =
base + time + dbcn_write + dbcn_read + dbcn_byte + srst + refused; lines =
the domain's printed lines; entered = its :10 ticks; ticks between entered
and the budget. From :13: records = every record-drained line (each domain's
lines, :09-:12); idle_ticks at most ticks; ticks at most the budget and at
least each domain's; overlap_ticks = the intersection of the two domains'
entered-to-shutdown intervals, at least half the shorter (Q5); and at
least K alternations between the domains' lines (Q5). With hart 0's
round-robin drain (Plan revision M0-C.2), two domains that produce lines at
once alternate on the console at least once per wake in which both rings
hold a record; a console-bound hart 0 lowers the wakes, not the alternation
within a wake. :09's hedeleg is a WARL reading of 0xb15d holding 0xb10c;
:04 and :06 carry the pinned kernel_bytes and image_size. beryllium-cheri:
--monitor cheri judges the CHERI-aware monitor (planning/cheri-platform.md),
whose :09 hedeleg is a WARL reading of 0x1000b15d holding 0x1000b10c (cause
28, CHERI v0.9.3's CHERI fault, too); --monitor riscv, the default, the
RISC-V monitor. An expectation of the CHERI-aware monitor's may state the
hedeleg its image arms (cheri-fault-hs's, 0xb15d holding 0xb10c), which
:09 is then a WARL reading of, and the lines its faulting domain ends with,
the domain its DETAIL names (cheri_findings(): cheri-fault-hs's trace line
0; cap-store's module's lines before its tagged store). With
--cheri-mutations, a passing capture of the
CHERI-aware monitor's is also mutated by the CHERI enforcement rules'
mutations that apply to its image (planning/cheri-enforcement-plan.md,
section 6; cheri_mutations()), each judged as the capture was and each
to be rejected for its own reason; one that is not fails the run.

Fail (the variants): the first BE_MVP:FAIL has the declared class; the
monitor lines before it follow the pass order and include every line of the
declared `after` group, and no line of a later group unless that group is
BE_MVP:07 or :10 (after the publication or the entries the run's timing
decides where a failure lands); then its DETAIL line in the class's form
(none for boot, gstage, payload, firmware; henvcfg for sstc; ticks for
run-timeout; the start form for hart-start; the exit form for a domain's
exit classes, naming the binding's domain and hart, a domain that entered,
and a cause that fits); then at most BE_MVP:SRST_RETURNED. Domain lines may
appear only after their own :10. The
ring-full fallback (Plan revision M0-A.3, as implemented): both :10, then
only `BE_MVP:FAIL ring` and DETAIL lines of domain harts, at most one of
each per domain, at least one whole DETAIL, no domain line and no :11-:14;
the last line may be cut short by the other hart's shutdown.

Probe stops (the plan's probe table, applied only as the stops it names):
a hart other than the start rule's not STOPPED; htval not GPA >> 2; an IPI
not delivered; a stale read with fences; B's value not read under a
distinct VMID. probe-console-input (M7-5; planning/mvp-m7-plan.md, D-12):
its lines of received bytes (`BE_MVP:PROBE console-input bytes=N hex=H`)
are taken out of hart 0's order, each between its window's line and its
counts' line, bytes= the count so far, 64 bytes on every line but the
last; total= the bytes' count, sha256= the first 16 hex digits of their
SHA-256, nonzero_polls at most polls, and max_per_poll at most 256; in
direct mode (QEMU, where nothing is typed) total=0 and errors=0. Its
values are recorded as the other probes' are; the board's judgement of
them is tools/k3-input-characterize.sh's.

M1's schema-v2 expectations (planning/mvp-m1-plan.md, "Scenarios and the
harness" and "Markers", with Plan revision M1-A) add: each domain's own
required lines, with the roles' placeholders; BE_MVP:03 CHANNEL_CHECKED
and :05 CHANNEL_CLEARED in their places; hart 0's BE_MVP:DENY lines, taken
out of the monitor order, each between its domain's :10 and :12; the
denial log against the guests' reports, rules 1 to 4 verbatim: for each
domain its DENY lines D, its MVPINIT 08 lines R, and its expected denials
E, n = m = k, Di's seq i and Di before Ri, gpa equal across Di, Ri, and Ei,
htval = Ei's GPA >> 2 as 64-bit values, stval = va, sepc = pc, cause and
injected 20/1, 21/5, or 23/7 for a fetch, load, or store, kind as the
sealed record gives it, htinst zero or the transformed form of the init's
instruction (HTINST), signo=11 code=2 observed=1 and, for the store,
unchanged=1, and one Direct-mode vstvec per domain; the writer's and the
reader's MVPINIT 07 digests equal with match=1; exits = sbi + ipi +
denials; and the authority report (--report, required): the expectation's
SHA-256 and configuration identity, its grants each with a rule, its
declared flows, every check A1-A8 pass, each :03 GSTAGE_BUILT_REWALKED line
its window grant's GPA, HPA, and size, and CHANNEL_CHECKED the channel's
GPA, HPA, size, endpoints, both leaves from the derived flags, and the
configuration identity. A declared failure may name its DETAIL lines (one
must match) and line prefixes that no line may start with (absent). Only
hart 0's lines are terminal: a domain line is never one, whatever it
holds.

M2's schema-v3 expectations (planning/mvp-m2-plan.md, "Scenarios and the
harness", "Markers") add, with M1's rules unchanged: BE_MVP:03
PAGE_CHECKED, :05 PAGE_CLEARED and SECRET_PLACED, and :06 MEASURED in
their places, each against the report (the page's GPA, HPA, size, kind,
ends, leaves, and identity, as CHANNEL_CHECKED's); hart 0's BE_MVP:MGMT
lines, taken out of hart 0's order as DENY lines are, against the
guests' MVPINIT 10 MGMT calls (a burst line standing for its count) and
the declared requests, in order per domain, seq i the i-th call of pause
or terminate, each before its call's report and between its domain's :10
and its first :12 (its shutdown, or the transition that ended its guest),
a delivered one after its target's DOMAIN_PAUSED or DOMAIN_TERMINATED,
which names its requester; another FID answered -2 on its hart, with no
line; each MVPINIT 09 REQUEST and RESPONSE digest the checker's own
HMAC-SHA-256 (hmac, hashlib; the key the secret, the message the request's
number as 8 little-endian bytes and its message zero-padded to 64 bytes),
equal on both sides per request, the unanswered one only on the
requester's, timeout=1, after the report of its pause call; the
measurement recomputed from the build outputs (--kernel and --dtb, the
measured domain's kernel and DTB, then its secret page, the secret
zero-padded to the page, then the report's configuration identity) equal
to MEASURED's sha256= and bytes= and to the measured domain's
DOMAIN_TERMINATED's sha256=, and, for wrong-measurement, its DETAIL's
computed=, its expected= the variant's value, one bit from it; a paused
domain's DOMAIN_TERMINATED with DOMAIN_PAUSED's exits; the declared order
(DOMAIN_PAUSED, DOMAIN_TERMINATED, the host's DOMAIN_SHUTDOWN,
RUN_COMPLETE, each once); sbi the sum of sbi_terms, the printed ones and
mgmt, hart 0's requests, sbi_derived's exact count; refused exact; a
terminated domain's end, its DOMAIN_TERMINATED, in the run's intervals;
each request a drained record. A failure whose domains ran (no-grant-check)
shows its required lines once each before the FAIL, its run-timeout
DETAIL's ticks at least its budget, and, for each domain in
prefix_domains, which another's request ended, a prefix of its lines,
denials, and requests, with the server answering only a first run of the
requests.

Plan revision M2-A (planning/mvp-m2-plan.md, M2-A.1) adds one rule, the
IPI probe's SPV: a BE_MVP:11 IPI_PROBE line shows spv=1, M0's rule, or,
only where the expectation is a v3 one with the management extension
(mgmt; its probe template carries spv=<S>, which this rule resolves),
spv=0 with its received= inside a management wait of its own hart,
[ticks, ticks + service] of a BE_MVP:MGMT line naming that hart, both
ticks since the barrier as the monitor prints them: a hart that waits in
HS for hart 0's MGMT_RESULT serves a PING it finds meanwhile (Q14), and
its PONG shows SPV 0. Such a probe is recorded among the costs
(g<d>_ping_in_mgmt_wait=1, and g<d>_ping_mgmt_seq, the seq of the request
whose wait holds it).

M7-4's images with console input (planning/mvp-m7-plan.md, D-3, D-4,
D-11; an expectation with a console_input section, written from the
variant's session by tools/gen-scenario.py) add: BE_MVP:15 INPUT_ARMED
with the declared grants and prefix=0x7e, then BE_MVP:16 FOCUS none,
after :07 in hart 0's order, and :18 before :13; each BE_MVP:16 FOCUS g<d>
and BE_MVP:17 INPUT_DROP line taken out of that order, the focus lines the
session's focus steps in order, one :17 line per reason and only for the
reasons the session provokes (before-armed allowed), and no second FOCUS
none; and :18 reconciled with the run's keys (--typed,
tests/session-typist.py's typed.txt), nonce (--nonce), and session file
(--session, the expectation's by SHA-256): typed.txt's keys each step's
bytes with NONCE the nonce, in the steps' order; read the keys typed, at
least delivered plus dropped; each domain's delivered count and the first
16 hex digits of its SHA-256 those of the bytes src/mvp-input.c's table
(D-3, input_model()) routes to it from the keys, after the first poll's
before-armed discards, and an ungranted domain's none; the drops the
table's; the nonce on its focused domain's lines in each focus period
whose steps type it and on no other line; each channel read's text the
text last written; a v3 scenario's secret, raw or in hex, nowhere in the
capture; each shell's lines with the run's nonce in place of <nonce>; sbi
less its printed terms within the range of dbcn_input, the served reads,
which the guest's polling paces; and no blank line among the markers. Any
other image shows no :15 to :18 line. The hostile guest's image (D-4; its
expectation's forged lines) admits each look-alike once as a line of the
domain that printed it, behind that domain's prefix, the word forged on no
other domain's line and none of hart 0's, and no blank line among the
markers.

M9's log (planning/mvp-m9-plan.md, D-4; mvp/docs/log-profile.md): an
expectation that carries the generator's log data (its "log" section,
tools/gen-scenario.py's apply_log(): the sequence, run class, R2 state,
count, header, records, ranges, registers, launch constants, terminal
line, and lines, which must be what the image's reference implies, field
by field) has its BE_MVP:19 and :20 lines and its :06 LAUNCH lines taken
out of hart 0's order and judged by tests/log_module.py's judge(): from
hart 0's
unprefixed stream alone, the page rebuilt and refused if it does not
rebuild, the registers replayed (unprotected), every digest recomputed
(the monitor's ranges from the boot image, --image or the build's; each
domain's kernel and device tree from the build input the reference names
under --build-root, default build/mvp; the core identity, the console
grants, and the report's identities from the generator's canonical
inputs), every field compared with the image's reference manifest
(--reference, default BUILD/references/TOOLCHAIN/IMAGE.json), the global
order and the run class's prefix held, DOMAIN_TERMINATED's digest the
domain's launch register, and stream 0 a self-report whose difference is
the finding `self-report differs: OBJECT` (self-report-flip's one finding,
which its run declares). The report gains the BE_MVP_LOG lines and the
record its log; the rebuilt log (log.json) is written in the run record,
beside --json's result.json as log.json (STEM.result.json, STEM.log.json),
or to --log-json. The pinned
M2 measurement of the retained fixtures serves no such capture. The
self-test and mutations judge retained M9 fixtures against the pinned
pre-M11 era set, and exercise recomputation on synthetic stand-ins whose
whole log surface comes from the current reference; M7's stay against
the expectations of their time (tests/fixtures/pre-m9/). The self-test
also adds the log module's own cases.

--check-image runs tests/check-image.py's boot-image rules (B3's header and
descriptor, the shim, the ranges, the payload, the DTBs and kernel against
their pins) on a board image before any loader sees it; a te-poc or anchor
image (or a variant's) is checked against its scenario, given as its v2 or
v3 expectation and authority report (--expect, --report). --self-test and
--mutation-test run on the fixtures in tests/fixtures/ (real QEMU captures,
CRs removed) and B7's recorded COM260 kexec handoff; every seeded and named
mutation of a passing capture must be rejected for its own reason. Each
fixture is judged against the guest pins its capture was made with: M0's
twelve against M0's (tests/fixtures/m0-guest-pins.txt, guest/pins.txt at
the M0 result), M1's five against M1's (m1-guest-pins.txt, at the M1
result), M2's, M5's, and M6's against M2's (m2-guest-pins.txt, at the M2
result, the same bytes through M7-3, before M7-2's userland changed the
kernel), and M7's against --pins; each expectation with the --report its
SHA-256 names, and anchor's with its --kernel and --dtb, but for an anchor
capture made with M2's pins, whose kernel is not retained: its measurement
is the one its pinned expectation records (measurement_hex), the
generator's over the build outputs of its time.
Each fixture is also judged against the expectations its image was built
with: M1's and M2's against te-poc's and anchor's at 366c8af4
(tests/fixtures/pre-m6/); M0's, M5's, and M6's against every scenario's
at ae3e9537 (tests/fixtures/pre-m7/), before M7 raised the SBI
implementation version every guest prints (planning/mvp-m7-plan.md,
D-10); and M7's twelve against the current ones (--expect-dir), as are
M7-4's: the hostile guest's capture and each console variant's typed
session (a hart-0 boot) with its keys (NAME.typed.txt), its nonce
(NAME.nonce.txt), and its scenario's session file. The
self-test also holds the first COM260 scenario run's capture (CRs removed),
which stopped the board campaign (stop condition 6, Plan revision M0-C):
hart 0's drain-batched order, which the alternation floor alone rejects;
the first M1 board campaign's no-inject capture (CRs removed), which
stopped that campaign (stop condition 6, Plan revision M1-B): both domain
harts' own FAIL and DETAIL lines among hart 0's drain, rejected for
exactly those lines and the guest lines after the first FAIL; and the
first M2 board campaign's anchor capture (CRs removed), which stopped
that campaign (stop condition 6, Plan revision M2-A): hart 2's PONG
answered with spv=0 inside its first management wait, which the rule
above admits, so it passes, with the probe among its costs; moved out of
that wait, or without that request's line, it fails.

The uboot fixtures: until the characterization (M5-6a) and the rehearsal
(M5-3) record a boot from the Beryllium partition, U-Boot's lines are a
fixed template (uboot_form): the board's after B6's recorded U-Boot run
(bringup/k3-b6/results/20261008-com260-uboot/), with the env_k3.txt lines
B3's runs recorded (bringup/k3-b3/results/20261006-com260/) and be_ld's
load and md5sum's line (the form this BSP's md5sum printed in the
characterization of 2026-10-30) in place of loady's YMODEM lines; QEMU's
after B3's QEMU run of the pinned upstream v2022.10 (the control device
tree in place at 0xff73a250 under 8 GiB), with its crc32 line, behind the
capture's own OpenSBI banner.
tests/fixtures/board-uboot-two-guests-gcc.log is the board form of release
candidate 1's first COM260 run (GCC two-guests, 20261029T171402Z in
mvp/results/20261029-com260-rc/, made with the current guest pins), with
its image's size and MD5 (2,584,576 bytes,
c3f201e9319ea88b8035b61231c701ec; its CRC-32 043fe676);
tests/fixtures/qemu-uboot-two-guests-clang-hart6.log is the QEMU form of
M0's hart-6 capture (M0's pins), with the Clang two-guests QEMU-only
image's size and CRC-32 (2,584,576 bytes, de60ac10; its MD5
9c454eb9a7455a5cf18bee3fdc96b836), both images as the sources at M5-2
build them. The self-test requires each to be exactly that form, so
`check-capture.py --write-fixtures OUT` (with capture-check's arguments,
tools.mk) reproduces both, which `cmp OUT/NAME.log tests/fixtures/NAME.log`
shows; it judges them and the uboot mutations, a QEMU boot from hart 3
(PASS) and from a domain hart (REFUSED), and each fixture with the other
digest form (PASS) among its cases.
--write-fixtures writes kexec-mode captures from them (M9's) for the
board-tool dry run: each board image kind's passing capture, and a refused
one; each
carries the current guest pins in BE_MVP:04 and :06 and its image's
measurement log, which the board tools judge against the image's
reference manifest under --build-root; with te-poc's expectations and its
--report, te-poc's passing capture and reader-write's and no-inject's,
which fail as declared; with anchor's, its --report, --kernel, and --dtb,
anchor's passing capture and wrong-measurement's and no-grant-check's,
which fail as declared. It also writes the two uboot fixtures
and, for each kind given as --image KIND=BOOT_IMG, the kind's uboot form
(uboot-KIND.console.log, CRLF) with that image's size and MD5, which
passes in uboot mode as its kexec capture does, but for the refused kind,
which fails there (a board boot is a hart-0 boot).
"""

import argparse
import hashlib
import hmac
import importlib.util
import json
import pathlib
import random
import re
import sys
import zlib

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
MVP_DIR = HERE.parent
LAYOUT_H = MVP_DIR / "src" / "mvp-layout.h"
# beryllium-cheri: the monitor's header, for its console line's length.
MVP_H = MVP_DIR / "src" / "mvp.h"
DEFAULT_PINS = MVP_DIR / "guest" / "pins.txt"
FIXTURES = HERE / "fixtures"
# B7's recorded COM260 kexec handoff (accepted at 7b6b846b): its first
# eleven lines are Fedora's handoff, which the kexec fixtures reuse.
B7_HANDOFF = MVP_DIR.parent / "bringup" / "k3-b7" / "results" / \
    "20261008-com260" / "20261008T200212Z" / "handoff-excerpt.log"
B7_HANDOFF_SHA256 = \
    "b6e3bdc081ed9eb43cce2ca2b1690b86924374195aee0761f8ab0e4258d2ba13"


def layout_constants(path=LAYOUT_H):
    """Every BE_MVP_* literal of mvp-layout.h."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    return {name: int(value, 0) for name, value in re.findall(
        r"^#define\s+BE_MVP_(\w+)\s+BE_MVP_C\((0x[0-9a-fA-F]+|\d+)\)",
        text, re.M)}


LAYOUT = layout_constants()


def header_constant(name, path=MVP_H):
    """beryllium-cheri: BE_MVP_<name>, an unsigned literal #define of
    src/mvp.h; its absence, or a second definition, is an error."""
    found = re.findall(
        rf"^#define\s+BE_MVP_{name}\s+(0x[0-9a-fA-F]+|\d+)U?\s*$",
        pathlib.Path(path).read_text(encoding="utf-8"), re.M)
    if len(found) != 1:
        raise SystemExit(f"{path}: BE_MVP_{name} is not one literal #define")
    return int(found[0], 0)


STAGING = LAYOUT["STAGING_HPA"]
# The kexec era's FDT slot after the staged image (test-only, for the
# retained kexec records; the layout no longer names it since M6, Q3).
KEXEC_FDT_ALIGN = 0x200000
KEXEC_FDT_MAX = 0x200000
FDT_ALIGN = KEXEC_FDT_ALIGN
WINDOWS = (LAYOUT["G0_HPA"], LAYOUT["G1_HPA"])
RING_PEAK_BUDGET = LAYOUT["RING_PEAK_BUDGET"]
LINE_BYTES_MAX = 256
HEX = r"0x(?:0|[1-9a-f][0-9a-f]{0,15})"
DEC = r"(?:0|[1-9][0-9]*)"
SIGNED = rf"-?{DEC}"
STAMP = re.compile(r"\[ *[0-9]+\.[0-9]{6}\]")
RULE_TAG = "BE_MVP_SHIM: "
SHIM_TAG = "BE_K3_B3: "
MONITOR_TAGS = (RULE_TAG, SHIM_TAG, "BE_R3:", "BE_MVP:")
RULE = re.compile(r"BE_MVP_SHIM: boot_hart=0x([1-9a-f][0-9a-f]{0,15}) "
                  r"starting hart 0")
SHIM_LINE = re.compile(r"BE_K3_B3: SHIM hart=0x([0-9a-f]{16}) "
                       r"shim=0x([0-9a-f]{16}) fdt=0x([0-9a-f]{16}) "
                       r"dest=0x([0-9a-f]{16}) bytes=0x([0-9a-f]{16})")
BOOT_HART = re.compile(r"Boot HART ID\s*:\s*([0-9]+)$")
SBI_VERSION = re.compile(r"Runtime SBI Version\s*:\s*([0-9.]+)$")
HANDOFF = (("start", re.compile(r"kexec_core: Starting new kernel")),
           ("call", re.compile(r"Will call new kernel at ([0-9a-f]+) from "
                               r"hart id ([0-9a-f]+)")),
           ("fdt", re.compile(r"FDT image at ([0-9a-f]+)")),
           ("bye", re.compile(r"Bye\.\.\.")))
# U-Boot's boot of the image (planning/mvp-m5-plan.md, "The boot path of
# release candidate 2"): be_ld loads it at the literal 0x1_4000_0000 (Q2)
# and prints its digest, and be_go's booti moves it to L; each line as
# U-Boot 2022.10 prints it (fs/fs.c; common/hash.c's hash_show for crc32,
# whose `NAME for START ... END ==> DIGEST` form this BSP's md5sum printed
# in the characterization of 2026-10-30; cmd/booti.c, boot/image-fdt.c,
# arch/riscv/lib/bootm.c), after the BSP's stamp. The digest line is
# md5sum's on the board (this BSP's crc32 prints nothing) and crc32's in
# QEMU (upstream's qemu-riscv64_smode_defconfig has no md5sum): one line of
# either form, with its kind's number of hexadecimal digits.
UBOOT_LOAD = 0x140000000
UBOOT_STAMP = re.compile(r"^\[ *[0-9]+\.[0-9]{3}\] ?")
UBOOT_DIGEST_DIGITS = {"md5": 32, "crc32": 8}
UBOOT_LINES = (
    ("bytes read", re.compile(r"([0-9]+) bytes read in [0-9]+ ms"
                              r"(?: \(.*\))?")),
    ("digest", re.compile(r"(md5|crc32) for ([0-9a-f]+) \.\.\. ([0-9a-f]+) "
                          r"==> ([0-9a-f]{32}|[0-9a-f]{8})")),
    ("Moving Image", re.compile(r"Moving Image from 0x([0-9a-f]+) to "
                                r"0x([0-9a-f]+), end=([0-9a-f]+)")),
    ("Flattened Device Tree", re.compile(r"## Flattened Device Tree blob "
                                         r"at ([0-9a-f]+)")),
    ("Booting using", re.compile(r"Booting using the fdt blob at "
                                 r"0x([0-9a-f]+)")),
    ("Device Tree", re.compile(
        r"Loading Device Tree to ([0-9a-f]{16}), end ([0-9a-f]{16}) "
        r"\.\.\. OK|Using Device Tree in place at ([0-9a-f]{16}), end "
        r"([0-9a-f]{16})")),
    ("Starting kernel", re.compile(r"Starting kernel \.\.\.")))
UBOOT_BANNER = re.compile(r"U-Boot [0-9]{4}\.[0-9]{2}\S* \(.*")
SPL_BANNER = re.compile(r"U-Boot SPL [0-9]{4}\.[0-9]{2}\S* \(.*")
UBOOT_AUTOBOOT = re.compile(r"Autoboot in [0-9]+ seconds|Hit any key to "
                            r"stop autoboot")
UBOOT_WATCHDOG = re.compile(r"WDT: +\S.*")
OPENSBI_BANNER = re.compile(r"OpenSBI v[0-9]")
# The BSP's lines U-Boot's handoff prints before the shim's.
UBOOT_NOISE = ("fail to get alias node efuse_power",
               "Removing MTD device #0 (nor0) with use count 1")
FIRMWARE = re.compile(r"BE_MVP:02 FIRMWARE_PROBED hsm=([01]) ipi=([01]) "
                      rf"status=((?:[0-9]+:{SIGNED},)*[0-9]+:{SIGNED}) "
                      r"started=(none|[0-9]+)")
COUNTERS = ("exits", "sbi", "ipi", "base", "time", "dbcn_write", "dbcn_read",
            "dbcn_byte", "srst", "refused", "lines")
CALL_CLASSES = ("base", "time", "dbcn_write", "dbcn_read", "dbcn_byte",
                "srst", "refused")
SHUTDOWN = re.compile(rf"BE_MVP:12 DOMAIN_SHUTDOWN hart=({DEC}) "
                      rf"domain=({DEC}) " +
                      " ".join(f"{name}=({DEC})" for name in COUNTERS) +
                      rf" ring_peak=({HEX}) entered=({HEX}) ticks=({HEX})")
COMPLETE = re.compile(rf"BE_MVP:13 RUN_COMPLETE domains=({DEC}) "
                      rf"records=({DEC}) wakes=({DEC}) idle_ticks=({HEX}) "
                      rf"overlap_ticks=({HEX}) ticks=({HEX})")
IPI_PROBE = re.compile(rf"BE_MVP:11 IPI_PROBE hart=({DEC}) domain=({DEC}) "
                       rf"sent=({HEX}) received=({HEX}) answered=({HEX}) "
                       r"spv=([01])")
# hedeleg is WARL (B6's fix-warl): a reading of 0xb15d that holds 0xb10c.
# beryllium-cheri: the values per monitor variant (--monitor): the
# CHERI-aware monitor's delegate cause 28, CHERI v0.9.3's CHERI fault, too,
# which a CHERI guest needs: 0x1000b15d holding 0x1000b10c.
MONITOR_HEDELEG = {"riscv": (0xb15d, 0xb10c),
                   "cheri": (0x1000b15d, 0x1000b10c)}
HEDELEG, HEDELEG_REQUIRED = MONITOR_HEDELEG["riscv"]
# beryllium-cheri: the monitor's console line, read from src/mvp.h
# (BE_MVP_CONSOLE_LINE_BYTES), and Linux's boot timestamp,
# "[    0.000000] ".
CONSOLE_LINE_BYTES = header_constant("CONSOLE_LINE_BYTES")
BOOT_STAMP_BYTES = 15
# The marker IDs whose lines name a domain, and those that run per domain
# in either hart order.
PER_DOMAIN = ("BE_MVP:03", "BE_MVP:05", "BE_MVP:06", "BE_MVP:08",
              "BE_MVP:09", "BE_MVP:10", "BE_MVP:11", "BE_MVP:12")
CHAINED = ("BE_MVP:09", "BE_MVP:10", "BE_MVP:11", "BE_MVP:12")
# A boot-step failure has one place; a run failure (after the publication or
# the domains' entries) may follow any later line.
RUN_GROUPS = ("BE_MVP:07", "BE_MVP:10")
FAIL_PREFIX = "BE_MVP:FAIL "
# The prelude (planning/mvp-m6-plan.md, D-3): the MVP's two BE_MVP:00
# lines, which an expectation declares, or, in a capture of an image built
# before M6, the accepted R3 sequence in their place.
CORE_PRELUDE = "BE_MVP:00"
R3_PRELUDE = ("BE_R3:01 BOOT_VALIDATED", "BE_R3:02 R1_DERIVED",
              "BE_R3:03 R2_BUILT_REWALKED", "BE_R3:04 HS_VS_STATE_VERIFIED",
              "BE_R3:05 BINDING_PREPARED", "BE_R3:06 HGATP_FENCED_PUBLISHED")
DETAIL_PREFIX = "BE_MVP:DETAIL "
SRST_RETURNED = "BE_MVP:SRST_RETURNED"
EXIT_FORM = (rf" cause=({HEX}) pc=({HEX}) tval=({HEX}) htval=({HEX}) "
             rf"htinst=({HEX}) spvp=([01]) vsatp=({HEX}) exits=({DEC})")
DETAIL_FORMS = {
    "henvcfg": re.compile(rf"BE_MVP:DETAIL henvcfg=({HEX})"),
    "ticks": re.compile(rf"BE_MVP:DETAIL ticks=({HEX})"),
    "start": re.compile(rf"BE_MVP:DETAIL domain=({DEC}) hart=({DEC}) "
                        rf"result=({SIGNED}) status=({SIGNED}) "
                        rf"ticks=({HEX})"),
    "waited": re.compile(rf"BE_MVP:DETAIL domain=({DEC}) hart=({DEC}) "
                         rf"ticks=({HEX})"),
    "record": re.compile(rf"BE_MVP:DETAIL domain=({DEC}) hart=({DEC}) "
                         rf"record=({DEC})"),
    "exit": re.compile(rf"BE_MVP:DETAIL domain=({DEC}) hart=({DEC})"
                       + EXIT_FORM),
    "domain": re.compile(
        rf"BE_MVP:DETAIL domain=({DEC}) hart=({DEC})(?: hgatp=({HEX}) "
        rf"hstatus_controls=({HEX}) hedeleg=({HEX}) hideleg=({HEX}) "
        rf"hcounteren=({HEX}) sie=({HEX}) henvcfg=({HEX}) "
        rf"vstimecmp=({HEX})| register=([a-z]+) wanted=({HEX}) "
        rf"readback=({HEX}))?"),
}
# Each class's DETAIL forms, from src/mvp-runtime.c and src/mvp-hartmain.c:
# () for none; a domain hart's exit failures carry the exit form.
EXIT_CLASSES = ("interrupt", "guest-page-fault", "virtual-instruction",
                "access-fault", "illegal-instruction", "exit-budget",
                "guest-reboot", "guest-failure")
CLASS_DETAIL = dict(
    {name: () for name in ("boot", "gstage", "payload", "firmware",
                           "console", "shutdown-returned")},
    sstc=("henvcfg",), **{"run-timeout": ("ticks",),
                          "hart-start": ("start",),
                          "hart-ready": ("waited",)},
    **{name: ("exit",) for name in EXIT_CLASSES})
OPTIONAL_DETAIL = ("exit", "domain", "record")
# The exit cause each exit class admits (the SBI core's classification).
CAUSE_FITS = {
    "guest-page-fault": lambda cause: cause in (20, 21, 23),
    "virtual-instruction": lambda cause: cause == 22,
    "access-fault": lambda cause: cause in (1, 5, 7),
    "illegal-instruction": lambda cause: cause == 2,
    "guest-reboot": lambda cause: cause == 10,
    "guest-failure": lambda cause: cause == 10,
    "interrupt": lambda cause: cause >> 63 == 1,
}
DOMAIN_PLACEHOLDERS = {
    "[<s>]": STAMP.pattern, "<m>": r"[1-9][0-9]*", "<rest>": r"\S.*",
    "<e>": r"1[0-9]{3}", "<r>": r"[1-9][0-9]*", "<t>": DEC,
}
PLACEHOLDER = re.compile(r"\[<s>\]|<[A-Za-z]+>")
STEP = re.compile(r"MVPINIT 03 STEP n=([0-9]+)/([0-9]+) rounds=[0-9]+ "
                  r"t_ms=([0-9]+)")
GUEST_IDS = (re.compile(r"\] Kernel command line: .* be\.guest=(\S*)"),
             re.compile(r"^MVPINIT 01 START guest=(\S*)"))
SSTC_LINE = "riscv-timer: Timer interrupt in S-mode is available via sstc"
VERDICT_STATUS = {"PASS": 0, "FAIL": 1, "REFUSED": 3, "STOP": 4}
# M1's lines (planning/mvp-m1-plan.md, Markers): hart 0's DENY line, the
# guests' channel and denial reports, and the channel's boot line.
DENY_PREFIX = "BE_MVP:DENY "
DENY_FIELDS = ("hart", "domain", "seq", "kind", "cause", "injected", "gpa",
               "htval", "htinst", "stval", "sepc", "vsstatus", "vstvec",
               "ticks", "service")
DENY = re.compile(
    rf"BE_MVP:DENY hart=({DEC}) domain=({DEC}) seq=({DEC}) "
    rf"kind=(unmapped|read-only) cause=({HEX}) injected=({HEX}) "
    rf"gpa=({HEX}) htval=({HEX}) htinst=({HEX}) stval=({HEX}) "
    rf"sepc=({HEX}) vsstatus=({HEX}) vstvec=({HEX}) ticks=({HEX}) "
    rf"service=({HEX})")
DENIED = re.compile(
    rf"MVPINIT 08 DENIED n=({DEC}) kind=([a-z]+) gpa=({HEX}) va=({HEX}) "
    rf"pc=({HEX}) signo=({SIGNED}) code=({SIGNED}) observed=([01])"
    r"(?: unchanged=([01]))?")
CHANNEL_REPORT = re.compile(
    rf"MVPINIT 07 CHANNEL role=(writer|reader) gpa=({HEX}) bytes=({DEC}) "
    r"digest=0x([0-9a-f]{16}) (?:flag=0x[0-9a-f]+|polls=[0-9]+ "
    r"match=([01]))")
CHANNEL_CHECKED = re.compile(
    rf"BE_MVP:03 CHANNEL_CHECKED channel={DEC} writer=({DEC}) "
    rf"reader=({DEC}) gpa=({HEX}) hpa=({HEX}) bytes=({HEX}) "
    rf"level0={HEX},{HEX} writer_pte=({HEX}) reader_pte=({HEX}) "
    r"config=([0-9a-f]{64})")
GSTAGE = re.compile(rf"BE_MVP:03 GSTAGE_BUILT_REWALKED domain={DEC} "
                    rf"hart={DEC} gpa=({HEX}) hpa=({HEX}) size=({HEX}) ")
# The guest-page fault each access takes and the access fault injected for
# it (Q5); htinst zero or the transformed form of the init's instruction
# for that access, its offset and rs1 zero (guest/mvp-init.c: ld t1, 0(a0)
# and sd zero, 0(a0); M0's K3 probe read the same two). No scenario access
# is a fetch (Q3).
ACCESS_FAULT = {"fetch": (20, 1), "load": (21, 5), "store": (23, 7)}
HTINST = {"fetch": (0,), "load": (0, 0x3303), "store": (0, 0x3023)}
SIGSEGV, SEGV_ACCERR = 11, 2
ANALYSES = [f"A{number}" for number in range(1, 9)]
# M2's lines (planning/mvp-m2-plan.md, Markers): hart 0's page, secret,
# measurement, management, and transition lines; the guests' request,
# response, and management reports. hart 0 decides pause and terminate
# (Q3, Q14); the requester's hart answers any other FID itself with
# SBI_ERR_NOT_SUPPORTED, and no line.
MGMT_PREFIX = "BE_MVP:MGMT "
MGMT_FIELDS = ("hart", "domain", "seq", "fid", "target", "result",
               "target_state", "ticks", "service")
MGMT = re.compile(
    rf"BE_MVP:MGMT hart=({DEC}) domain=({DEC}) seq=({DEC}) "
    rf"fid=([a-z]+|{DEC}) target=({SIGNED}) result=({SIGNED}) "
    rf"target_state=([a-z]+|-) ticks=({HEX}) service=({HEX})")
MGMT_NAMES = ("pause", "terminate")
SBI_NOT_SUPPORTED = -2
GUEST_MGMT = re.compile(
    rf"MVPINIT 10 MGMT (?:fid=([a-z]+|{DEC}) target=({SIGNED}) "
    rf"result=({SIGNED})|burst=([1-9][0-9]*) fid=([a-z]+|{DEC}) "
    rf"target=({SIGNED}) results=({SIGNED})x([1-9][0-9]*))")
REQUEST = re.compile(rf"MVPINIT 09 (REQUEST|RESPONSE) n=({DEC}) "
                     r"(?:digest=([0-9a-f]{64})|timeout=1)")
PAUSED = re.compile(rf"BE_MVP:12 DOMAIN_PAUSED hart=({DEC}) domain=({DEC}) "
                    rf"by=({DEC}) exits=({DEC}) ticks=({HEX})")
TERMINATED = re.compile(
    rf"BE_MVP:12 DOMAIN_TERMINATED hart=({DEC}) domain=({DEC}) by=({DEC}) "
    rf"exits=({DEC}) sha256=([0-9a-f]{{64}}|-) ticks=({HEX})")
TRANSITION = {"pause": ("DOMAIN_PAUSED", PAUSED),
              "terminate": ("DOMAIN_TERMINATED", TERMINATED)}
MEASURED = re.compile(rf"BE_MVP:06 MEASURED domain=({DEC}) hart=({DEC}) "
                      rf"bytes=({DEC}) sha256=([0-9a-f]{{64}}) "
                      rf"expected=match ticks=({HEX})")
PAGE_CHECKED = re.compile(
    rf"BE_MVP:03 PAGE_CHECKED page=({DEC}) kind=(channel|secret)"
    rf"(?: writer=({DEC}))? reader=({DEC}) gpa=({HEX}) hpa=({HEX}) "
    rf"bytes=({HEX}) level0={HEX},{HEX}(?: writer_pte=({HEX}))? "
    rf"reader_pte=({HEX}) config=([0-9a-f]{{64}})")
PAGE_PLACED = re.compile(rf"BE_MVP:05 (PAGE_CLEARED|SECRET_PLACED) "
                         rf"page=({DEC}) hpa=({HEX}) bytes=({HEX}) "
                         rf"ticks=({HEX})")
DETAIL_FORMS["measurement"] = re.compile(
    rf"BE_MVP:DETAIL domain=({DEC}) hart=({DEC}) "
    r"computed=([0-9a-f]{64}) expected=([0-9a-f]{64})")
CLASS_DETAIL["measurement"] = ("measurement",)
# M9's log (planning/mvp-m9-plan.md, D-4; mvp/docs/log-profile.md): a log
# failure (overflow, or a page that cannot close) prints no DETAIL (4.5).
CLASS_DETAIL["log"] = ()


def load_log_module():
    """tests/log_module.py, the profile's reading and the log's judgment,
    on every capture whose expectation carries M9's log data."""
    spec = importlib.util.spec_from_file_location("mvp_log_module",
                                                  HERE / "log_module.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LOG = load_log_module()
# The build root the references and the build inputs they name lie under
# (mvp/Makefile's BUILD): references/TOOLCHAIN/IMAGE.json, guest/, ...
DEFAULT_BUILD = MVP_DIR.parent / "build" / "mvp"


class Line:
    """One marker line: its line number in the capture and its text from
    the tag on (for a domain line, the text after the prefix)."""

    def __init__(self, number, text):
        self.number = number
        self.text = text


class Capture:
    """One parse of one capture: every line, the loader's lines before the
    first marker, hart 0's monitor stream, each domain's stream, and the
    findings about the lines themselves."""

    def __init__(self, data, prefixes, forged=None, strict=False):
        """FORGED, {domain: [text]}: a hostile guest's look-alike lines
        (M7-4, D-4), each a domain line whose text may hold another tag;
        STRICT: a blank line among the markers is a finding too (an image
        with console input, or the hostile guest's: every line hart 0
        prints is tagged)."""
        forged = forged or {}
        text = data.decode("utf-8", "replace") if isinstance(data, bytes) \
            else data
        self.cut = bool(text) and not text.endswith("\n")
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        self.lines = [line.rstrip("\r") for line in lines]
        self.prefixes = tuple(prefixes)
        self.monitor = []
        self.domains = [[] for _ in prefixes]
        self.order = []
        self.findings = []
        self.first = None
        tags = MONITOR_TAGS + self.prefixes
        for number, line in enumerate(self.lines, 1):
            found = [(line.find(tag), tag) for tag in tags if tag in line]
            if not found:
                if self.first is not None and line.strip():
                    self.findings.append(f"line {number}: untagged text "
                                         f"among the markers: {line[:80]!r}")
                elif self.first is not None and strict:
                    self.findings.append(f"line {number}: a blank line "
                                         f"among the markers")
                continue
            start, tag = min(found)
            if self.first is None:
                self.first = number
            elif start:
                self.findings.append(f"line {number}: text before the "
                                     f"marker: {line[:80]!r}")
            marker = line[start:]
            odd = [char for char in marker if not " " <= char <= "~"]
            if odd:
                self.findings.append(f"line {number}: non-printable "
                                     f"{odd[0]!r} in {marker[:80]!r}")
            rest = marker[len(tag):]
            inner = [other for other in tags if other in rest]
            if inner and tag in self.prefixes and rest in forged.get(
                    self.prefixes.index(tag), ()):
                inner = []
            if inner:
                self.findings.append(f"line {number}: mixed line, "
                                     f"{inner[0]!r} inside {marker[:80]!r}")
            if tag not in self.prefixes:
                self.monitor.append(Line(number, marker))
                continue
            domain = self.prefixes.index(tag)
            if rest.find("MVPINIT", 1) >= 0 or STAMP.search(rest, 1):
                self.findings.append(f"line {number}: mixed G{domain} line "
                                     f"{marker[:80]!r}")
            if len(rest) > LINE_BYTES_MAX:
                self.findings.append(f"line {number}: G{domain} line of "
                                     f"{len(rest)} bytes, above the "
                                     f"{LINE_BYTES_MAX}-byte line buffer")
            self.domains[domain].append(Line(number, rest))
            self.order.append(domain)
        self.loader = self.lines[:self.first - 1] if self.first else \
            list(self.lines)


def key_of(text):
    """A monitor line's identity: its marker ID, and the domain it names
    when the ID is per domain."""
    if text.startswith(RULE_TAG):
        return ("rule", None)
    words = text.split(" ", 2)
    ident = " ".join(words[:2]) if words[0] in (
        "BE_K3_B3:", "BE_MVP:PROBE", CORE_PRELUDE) else words[0]
    if ident in PER_DOMAIN:
        match = re.search(r" domain=([0-9]+)", text)
        return (ident, int(match.group(1)) if match else None)
    return (ident, None)


def read_pins(path=DEFAULT_PINS):
    """kernel_bytes, image_size, and the banner from guest/pins.txt."""
    pins = {}
    for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"file Image sha256=[0-9a-f]{64} bytes=([0-9]+)",
                             line)
        if match:
            pins["kernel_bytes"] = int(match.group(1))
        elif line.startswith("kernel image_size="):
            pins["image_size"] = int(line.split("=", 1)[1], 16)
        elif line.startswith("kernel banner="):
            pins["banner"] = line.split("=", 1)[1]
    missing = {"kernel_bytes", "image_size", "banner"} - set(pins)
    if missing:
        raise ValueError(f"{path} has no {', '.join(sorted(missing))} pin")
    return pins


def domain_pattern(template, domain, pins, extra=None):
    """A domain template line as a full-line pattern; EXTRA, an
    expectation's own placeholders (v2's roles), adds to M0's."""
    placeholders = dict(extra or {}, **DOMAIN_PLACEHOLDERS)
    out, position = [], 0
    for match in PLACEHOLDER.finditer(template):
        out.append(re.escape(template[position:match.start()]))
        token = match.group(0)
        if token == "<banner>":
            prefix = template[:match.start()].split("] ", 1)[-1]
            banner = pins["banner"]
            # beryllium-cheri: a guest line longer than the monitor's
            # console line (src/mvp.h, BE_MVP_CONSOLE_LINE_BYTES) arrives in
            # pieces, so a long banner's line holds its first piece: the
            # boot timestamp "[    0.000000] ", the prefix, and what fits
            # of the rest. The CHERI LLVM's version strings make the CHERI
            # guest's banner such a line.
            room = CONSOLE_LINE_BYTES - BOOT_STAMP_BYTES - len(prefix)
            out.append(re.escape(banner[len(prefix):][:room])
                       if banner.startswith(prefix) else r"\S.*")
        elif token == "<g>":
            out.append(str(domain))
        elif token == "<i>":
            out.append("<i>")
        else:
            out.append(placeholders[token])
        position = match.end()
    out.append(re.escape(template[position:]))
    return "".join(out)


def align_up(value, alignment):
    return (value + alignment - 1) & ~(alignment - 1)


def prelude_form(entries, legacy):
    """The control lines with, when LEGACY (the capture shows a BE_R3
    line), the R3 sequence in place of the MVP's BE_MVP:00 lines: either
    form, each whole, before BE_MVP:01, and never both."""
    out = []
    for entry in entries:
        if not legacy or not entry["template"].startswith(CORE_PRELUDE):
            out.append(entry)
        elif not any(item["template"] == R3_PRELUDE[0] for item in out):
            out += [{"template": text, "regex": f"^{re.escape(text)}$"}
                    for text in R3_PRELUDE]
    return out


class Plan:
    """The expected monitor stream: the fixed prelude, in the capture's
    form (prelude_form), each domain's chain (BE_MVP:09-:12, in either hart
    order), and the final lines."""

    def __init__(self, expect, legacy=False):
        chained = "domain_control_lines" in expect
        self.prelude, self.chains = [], {}
        for entry in prelude_form(expect["control_lines"], legacy):
            key = key_of(entry["template"])
            if chained and key[0] in CHAINED:
                self.chains.setdefault(key[1], []).append(entry)
            else:
                self.prelude.append(entry)
        for domain, entries in sorted(expect.get("domain_control_lines",
                                                 {}).items()):
            self.chains.setdefault(int(domain), []).extend(entries)
        self.final = expect.get("final_lines", [])
        self.ids = []
        for entry in self.prelude + [entry for domain in sorted(self.chains)
                                     for entry in self.chains[domain]] + \
                self.final:
            ident = key_of(entry["template"])[0]
            if ident not in self.ids:
                self.ids.append(ident)


class Walk:
    """The expected order followed through monitor lines: which entries
    matched (key -> Line), and the findings."""

    def __init__(self, plan):
        self.plan = plan
        self.prelude = 0
        self.chain = {domain: 0 for domain in plan.chains}
        self.final = 0
        self.matched = {}
        self.sequence = []
        self.findings = []
        self.broken = False

    def heads(self):
        """The entries the next line may match."""
        if self.prelude < len(self.plan.prelude):
            return [self.plan.prelude[self.prelude]]
        if self.final == 0:
            heads = [entries[self.chain[domain]] for domain, entries in
                     sorted(self.plan.chains.items())
                     if self.chain[domain] < len(entries)]
            return heads + self.plan.final[:1]
        return self.plan.final[self.final:self.final + 1]

    def step(self, line):
        key = key_of(line.text)
        for entry in self.heads():
            if key_of(entry["template"]) != key:
                continue
            if not re.fullmatch(entry["regex"], line.text):
                self.findings.append(f"line {line.number}: {line.text!r} is "
                                     f"not {entry['template']!r}")
            if self.prelude < len(self.plan.prelude):
                self.prelude += 1
            elif key[0] in CHAINED and self.final == 0 and \
                    key[1] in self.chain:
                self.chain[key[1]] += 1
            else:
                missing = [entries[self.chain[domain]]["template"] for
                           domain, entries in sorted(self.plan.chains.items())
                           if self.chain[domain] < len(entries)]
                if missing:
                    self.findings.append(f"line {line.number}: "
                                         f"{line.text[:40]!r} before "
                                         f"{missing[0]!r}")
                self.final += 1
            self.matched[key] = line
            self.sequence.append((key, line))
            return True
        wanted = " or ".join(repr(entry["template"][:60])
                             for entry in self.heads()) or "nothing"
        self.findings.append(f"line {line.number}: {line.text[:90]!r} where "
                             f"the order expects {wanted}")
        self.broken = True
        return False

    def complete(self):
        return not self.heads()

    def started(self, ident):
        return any(key[0] == ident for key in self.matched)

    def holds(self, ident):
        """Whether every expected line of the group IDENT matched."""
        entries = [entry for entry in self.plan.prelude +
                   [entry for chain in self.plan.chains.values()
                    for entry in chain] + self.plan.final
                   if key_of(entry["template"])[0] == ident]
        return bool(entries) and all(key_of(entry["template"]) in
                                     self.matched for entry in entries)


def walk(lines, plan):
    state = Walk(plan)
    for line in lines:
        if not state.step(line):
            break
    return state


def handoff_facts(capture, options, findings, facts):
    """Linux's kexec handoff (B7's rules): (kexec hart, FDT) or Nones."""
    found = {}
    for name, pattern in HANDOFF:
        hits = [(number, match) for number, line in
                enumerate(capture.loader, 1)
                for match in [pattern.search(line)] if match]
        if len(hits) != 1:
            findings.append(f"{len(hits)} kexec handoff {name!r} lines "
                            f"before the markers, expected 1")
        else:
            found[name] = hits[0]
    numbers = [found[name][0] for name, _ in HANDOFF if name in found]
    if numbers != sorted(numbers):
        findings.append("the kexec handoff lines are out of order")
    hart = fdt = None
    if "call" in found:
        entry, hart = (int(value, 16) for value in found["call"][1].groups())
        facts.update(kexec_entry=f"0x{entry:x}", kexec_hart=str(hart))
        if entry != STAGING:
            findings.append(f"kexec entry 0x{entry:x} is not L 0x{STAGING:x}")
    if "fdt" in found:
        fdt = int(found["fdt"][1].group(1), 16)
        facts["kexec_fdt"] = f"0x{fdt:x}"
        wanted = options.get("kexec_fdt")
        if wanted is None and options.get("image_bytes"):
            wanted = STAGING + align_up(options["image_bytes"], FDT_ALIGN)
        lowest = STAGING + FDT_ALIGN
        highest = STAGING + align_up(LAYOUT["BOOT_IMAGE_MAX"], FDT_ALIGN)
        if wanted is not None and fdt != wanted:
            findings.append(f"kexec FDT 0x{fdt:x} is not the loader's "
                            f"0x{wanted:x}")
        elif fdt % FDT_ALIGN or not lowest <= fdt <= highest or \
                fdt + KEXEC_FDT_MAX > min(WINDOWS):
            findings.append(f"kexec FDT 0x{fdt:x} is not an aligned slot "
                            f"after L below the windows")
    return hart, fdt


# Every MVP extent (the layout rule, as the preflight applies it): the flat
# image's core, pool, hart region, and MVP region; the staging reserve at
# L (the image's maximum rounded to 2 MiB plus the kexec era's FDT slot,
# which the retained kexec records used); both domain windows; and the
# shared pages.
EXTENTS = (
    ("the core", LAYOUT["MONITOR_HPA"], LAYOUT["CORE_BYTES"]),
    ("the pool", LAYOUT["POOL_HPA"], LAYOUT["POOL_BYTES"]),
    ("the hart region", LAYOUT["HART_REGION_HPA"],
     LAYOUT["HART_REGION_BYTES"]),
    ("the MVP region", LAYOUT["REGION_HPA"], LAYOUT["REGION_BYTES"]),
    ("the staging reserve", STAGING, LAYOUT["STAGING_BYTES"]),
    ("G0's window", LAYOUT["G0_HPA"], LAYOUT["GUEST_BYTES"]),
    ("G1's window", LAYOUT["G1_HPA"], LAYOUT["GUEST_BYTES"]),
    ("the shared pages", LAYOUT["SHARED_PAGES_HPA"],
     LAYOUT["SHARED_PAGES_BYTES"]))


def uboot_text(line):
    """A loader line as U-Boot printed it: the BSP's stamp gone, stripped."""
    return UBOOT_STAMP.sub("", line, count=1).strip()


def image_digest(options, kind):
    """The image's digest of KIND (md5 or crc32) as U-Boot prints it, from
    the options (image_md5, image_crc32), or None when not given."""
    if kind == "crc32":
        crc = options.get("image_crc32")
        return None if crc is None else f"{crc:08x}"
    return options.get("image_md5")


def uboot_facts(capture, options, findings, facts):
    """U-Boot's booti (the uboot mode): (the OpenSBI banner's boot hart, in
    QEMU, or None, on the board; U-Boot's device tree, which the shim must
    report)."""
    facts["launcher_mode"] = "uboot"
    texts = [uboot_text(line) for line in capture.loader]
    qemu = any(OPENSBI_BANNER.match(text) for text in texts)
    hart = boot_facts(capture, "direct", options, findings, facts)[0] \
        if qemu else None
    for name, label, pattern, counts in (
            ("uboot_banner", "U-Boot", UBOOT_BANNER, (1,)),
            ("spl_banner", "U-Boot SPL", SPL_BANNER,
             (0, 1) if qemu else (1,))):
        hits = [text for text in texts if pattern.fullmatch(text)]
        if len(hits) not in counts:
            findings.append(f"{len(hits)} {label} banner lines before the "
                            f"markers, expected "
                            f"{' or '.join(map(str, counts))}")
        facts[name] = hits[0] if hits else "none"
    watchdog = [text for text in texts if UBOOT_WATCHDOG.fullmatch(text)]
    if watchdog:
        facts["uboot_watchdog"] = watchdog[-1]
    # One boot per run (M5's attribution rule): exactly one autoboot line,
    # and U-Boot's lines are read after it. Reading them after the *last*
    # autoboot line let an image print its own autoboot line and a forged
    # loader block before its first marker, in place of U-Boot's (row Z of
    # the S3-C reviews' reconciliation; mvp/README.md item 100).
    autoboot = [index for index, text in enumerate(texts)
                if UBOOT_AUTOBOOT.search(text)]
    if len(autoboot) != 1:
        findings.append(f"{len(autoboot)} U-Boot autoboot lines before the "
                        f"markers, expected 1: one boot per run")
    after = autoboot[0] + 1 if autoboot else 0
    found = {}
    for name, pattern in UBOOT_LINES:
        hits = [(index, match) for index, text in
                enumerate(texts[after:], after)
                for match in [pattern.fullmatch(text)] if match]
        if len(hits) != 1:
            findings.append(f"{len(hits)} U-Boot {name!r} lines after the "
                            f"autoboot, expected 1")
        else:
            found[name] = hits[0]
    indexes = [found[name][0] for name, _ in UBOOT_LINES if name in found]
    if indexes != sorted(indexes):
        findings.append("the U-Boot boot lines are out of order")
    values = {name: match.groups() for name, (_, match) in found.items()}
    size = options.get("image_bytes")
    loaded = int(values["bytes read"][0]) if "bytes read" in values else None
    if loaded is not None:
        facts["load_bytes"] = str(loaded)
        if size is not None and loaded != size:
            findings.append(f"U-Boot read {loaded} bytes, not the image's "
                            f"{size}")
    if "digest" in values:
        kind, first, last, digest = values["digest"]
        first, last = int(first, 16), int(last, 16)
        facts.update(load_digest_kind=kind, load_digest=digest)
        if len(digest) != UBOOT_DIGEST_DIGITS[kind]:
            findings.append(f"U-Boot's {kind} has {len(digest)} hexadecimal "
                            f"digits, not {UBOOT_DIGEST_DIGITS[kind]}")
        if first != UBOOT_LOAD:
            findings.append(f"{kind} starts at 0x{first:x}, not the load "
                            f"address 0x{UBOOT_LOAD:x}")
        if loaded is not None and last != first + loaded - 1:
            findings.append(f"{kind} covers 0x{first:x}-0x{last:x}, not the "
                            f"{loaded} bytes read")
        wanted = image_digest(options, kind)
        if wanted is not None and digest != wanted:
            findings.append(f"U-Boot's {kind} {digest} is not the image's "
                            f"{wanted}")
    if "Moving Image" in values:
        source, target, moved = (int(value, 16)
                                 for value in values["Moving Image"])
        facts.update(moving_from=f"0x{source:x}", moving_to=f"0x{target:x}",
                     moving_end=f"0x{moved:x}")
        if source != UBOOT_LOAD:
            findings.append(f"booti moved the image from 0x{source:x}, not "
                            f"the load address 0x{UBOOT_LOAD:x}")
        if target != STAGING:
            findings.append(f"booti moved the image to 0x{target:x}, not L "
                            f"0x{STAGING:x}")
        length = loaded if loaded is not None else size
        if length is not None and moved != STAGING + length:
            findings.append(f"booti's end 0x{moved:x} is not L + {length} "
                            f"bytes")
    blob = int(values["Flattened Device Tree"][0], 16) \
        if "Flattened Device Tree" in values else None
    if blob is not None:
        facts["fdt_blob"] = f"0x{blob:x}"
        if "Booting using" in values and \
                int(values["Booting using"][0], 16) != blob:
            findings.append(f"booti boots the fdt blob at "
                            f"0x{values['Booting using'][0]}, not the blob "
                            f"at 0x{blob:x}")
    fdt = None
    if "Device Tree" in values:
        loading = values["Device Tree"][0] is not None
        fdt, end = (int(value, 16) for value in
                    values["Device Tree"][0 if loading else 2:][:2])
        facts.update(fdt_loaded=f"0x{fdt:x}", fdt_end=f"0x{end:x}",
                     fdt_in_place="false" if loading else "true")
        if not loading and blob is not None and fdt != blob:
            findings.append(f"the device tree in place at 0x{fdt:x} is not "
                            f"the blob at 0x{blob:x}")
        if end < fdt:
            findings.append(f"U-Boot's device tree ends at 0x{end:x}, "
                            f"before its start 0x{fdt:x}")
        findings += [f"U-Boot's device tree 0x{fdt:x}-0x{end:x} overlaps "
                     f"{name} 0x{base:x}-0x{base + extent - 1:x}"
                     for name, base, extent in EXTENTS
                     if fdt < base + extent and base <= end]
    if "Starting kernel" in found:
        findings += [f"line {index + 1}: {capture.loader[index][:80]!r} "
                     f"between 'Starting kernel ...' and the markers"
                     for index in range(found["Starting kernel"][0] + 1,
                                        len(texts))
                     if texts[index] and texts[index] not in UBOOT_NOISE]
    if not qemu:
        for line in capture.monitor[:2]:
            shim = SHIM_LINE.fullmatch(line.text)
            if line.text.startswith(RULE_TAG) or \
                    shim and int(shim.group(1), 16):
                findings.append(f"line {line.number}: {line.text[:40]!r}: "
                                f"a board boot enters the shim on hart 0 "
                                f"(stop condition 6)")
    return hart, fdt


def boot_facts(capture, mode, options, findings, facts):
    """The boot hart the loader names, and the FDT the shim must report."""
    if mode == "kexec":
        return handoff_facts(capture, options, findings, facts)
    if mode == "uboot":
        return uboot_facts(capture, options, findings, facts)
    values = {}
    for name, pattern in (("boot_hart", BOOT_HART),
                          ("sbi_version", SBI_VERSION)):
        hits = [match.group(1) for line in capture.loader
                for match in [pattern.search(line)] if match]
        if len(hits) != 1:
            findings.append(f"{len(hits)} OpenSBI {name} lines before the "
                            f"markers, expected 1")
        else:
            values[name] = hits[0]
            facts[name] = hits[0]
    wanted = options.get("sbi_version")
    if wanted and values.get("sbi_version") not in (None, wanted):
        findings.append(f"the firmware's SBI version is "
                        f"{values['sbi_version']}, not {wanted}")
    hart = values.get("boot_hart")
    return (int(hart) if hart is not None else None), None


def shim_findings(stream, expect, boot_hart, kexec_fdt, findings, facts):
    """The start rule's line and the SHIM line; returns (rule hart, the
    stream after them)."""
    rule = None
    if stream and stream[0].text.startswith(RULE_TAG):
        match = RULE.fullmatch(stream[0].text)
        if not match:
            findings.append(f"line {stream[0].number}: malformed start-rule "
                            f"line {stream[0].text!r}")
        else:
            rule = int(match.group(1), 16)
            facts["rule_hart"] = str(rule)
        stream = stream[1:]
    declared = expect["outcome"].get("shim_line")
    if declared is not None:
        text = f"{RULE_TAG}boot_hart=0x{rule:x} starting hart 0" \
            if rule is not None else None
        if text != declared:
            findings.append(f"the start-rule line is {text!r}, not the "
                            f"declared {declared!r}")
    elif boot_hart is not None and (rule or 0) != boot_hart:
        findings.append(f"the loader's boot hart is {boot_hart}, but the "
                        f"start-rule line names "
                        f"{'none' if rule is None else f'0x{rule:x}'}")
    if not stream or not stream[0].text.startswith(SHIM_TAG):
        findings.append("no BE_K3_B3 SHIM line opens the monitor stream")
        return rule, stream
    match = SHIM_LINE.fullmatch(stream[0].text)
    if match:
        facts.update(zip(("hart", "base", "fdt", "dest", "bytes"),
                         (f"0x{value}" for value in match.groups())))
        if kexec_fdt is not None and int(match.group(3), 16) != kexec_fdt:
            findings.append(f"the shim's fdt 0x{match.group(3)} is not the "
                            f"handoff's 0x{kexec_fdt:x}")
    return rule, stream


def firmware_findings(line, rule, shim_rule, findings, facts):
    """BE_MVP:02's statuses and started field (Plan revision M0-A.2)."""
    match = FIRMWARE.fullmatch(line.text)
    if not match:
        findings.append(f"line {line.number}: malformed BE_MVP:02 "
                        f"{line.text!r}")
        return None
    statuses = {int(hart): int(status) for hart, status in
                (pair.split(":") for pair in match.group(3).split(","))}
    started = None if match.group(4) == "none" else int(match.group(4))
    facts["started"] = match.group(4)
    want = None if shim_rule else rule
    if started != want:
        findings.append(f"BE_MVP:02 started={match.group(4)}, but the shim "
                        f"names {'no STARTED hart' if want is None else want}")
    for hart, status in sorted(statuses.items()):
        if status != (0 if hart == started else 1):
            findings.append(f"BE_MVP:02 hart {hart} status {status} with "
                            f"started={match.group(4)}")
    return started


def run_harts(expect):
    """The run's domain harts, as its BE_MVP:01 line names them."""
    for entry in expect["control_lines"]:
        match = re.search(r"^BE_MVP:01 .* harts=([0-9,]+) ",
                          entry["template"])
        if match:
            return [int(hart) for hart in match.group(1).split(",")[1:]]
    return []


def domain_findings(domain, lines, expect, pins, sbi_time, prefix=False,
                    optional=()):
    """One domain's stream in a passing run (B7's guest rules). PREFIX: the
    run may end the domain anywhere (M2's no-grant-check), so its lines
    need only be a prefix of its required ones, with no gap; OPTIONAL,
    full-line patterns of init lines it may also print."""
    findings = []
    name = f"G{domain}"
    templates = []
    own = expect["domain_lines"]
    # v1 lists one set for both domains; v2 gives each domain its own.
    if isinstance(own, dict):
        own = own.get(str(domain), [])
    for template in own:
        steps = re.search(r"n=<i>/([0-9]+) ", template)
        if steps:
            templates += [template.replace("<i>", str(step)) for step in
                          range(1, int(steps.group(1)) + 1)]
        elif not (sbi_time and SSTC_LINE in template):
            templates.append(template)
    patterns = [domain_pattern(template, domain, pins,
                               expect.get("domain_placeholders"))
                for template in templates]
    inits = [pattern for template, pattern in zip(templates, patterns)
             if template.startswith("MVPINIT ")]
    position, last = 0, -1
    for at, line in enumerate(lines):
        body = line.text
        exempt = ("panic",) if "] Kernel command line: " in body else ()
        for pattern in expect["rejected"]:
            if pattern in body and pattern not in exempt:
                findings.append(f"line {line.number}: rejected {pattern!r} "
                                f"in {name} line {body[:80]!r}")
        if sbi_time and SSTC_LINE in body:
            findings.append(f"line {line.number}: the sbi-time {name} "
                            f"reported the Sstc timer")
        if body.startswith("MVPINIT ") and \
                not any(re.fullmatch(init, body)
                        for init in inits + list(optional)):
            findings.append(f"line {line.number}: unexpected {name} init "
                            f"line {body!r}")
        if position < len(patterns) and re.fullmatch(patterns[position],
                                                      body):
            position, last = position + 1, at
    skipped = [line for line in lines[last + 1:] if any(
        re.fullmatch(pattern, line.text) for pattern in
        patterns[position + 1:])] if prefix else []
    if position < len(patterns) and (not prefix or skipped):
        findings.append(f"{name} lacks the required line "
                        f"{templates[position]!r} (or a later one is out of "
                        f"order)")
    for init in inits:
        count = sum(1 for line in lines if re.fullmatch(init, line.text))
        if count > 1:
            findings.append(f"{name} init line {init!r} appears {count} "
                            f"times")
    times = [int(step.group(3)) for step in
             (STEP.fullmatch(line.text) for line in lines) if step]
    if any(later <= earlier for earlier, later in zip(times, times[1:])):
        findings.append(f"{name} step times t_ms={times} do not rise")
    window_k = expect["domains"][domain]["bytes"] // 1024
    for line in lines:
        memory = re.search(r"\] Memory: ([0-9]+)K/", line.text)
        if memory and int(memory.group(1)) > window_k:
            findings.append(f"{name}: {memory.group(1)}K available exceeds "
                            f"the {window_k}K window")
    return findings


def guest_id_findings(capture):
    """Each domain line that names a guest names its own (the binding of
    the prefix to the domain)."""
    findings = []
    for domain, lines in enumerate(capture.domains):
        for line in lines:
            for pattern in GUEST_IDS:
                named = pattern.search(line.text)
                if named and named.group(1) != str(domain):
                    findings.append(f"line {line.number}: a G{domain} line "
                                    f"names guest {named.group(1)!r}")
    return findings


def counter_rule(name, rule, value, where):
    if "exact" in rule and value != rule["exact"]:
        return f"{where}: {name}={value}, expected exactly {rule['exact']}"
    if "min" in rule and not rule["min"] <= value <= rule["max"]:
        return (f"{where}: {name}={value} is outside {rule['min']}-"
                f"{rule['max']}")
    return None


def sbi_findings(expect, domain, values, where):
    """sbi as the sum of its terms (M0's and M1's call classes, all
    printed; M2's sbi_terms, which add mgmt, hart 0's requests, which the
    :12 line does not print): the printed terms' sum, plus each unprinted
    term's exact count (sbi_derived)."""
    terms = expect.get("sbi_terms", CALL_CLASSES)
    printed = sum(values[term] for term in terms if term in values)
    unprinted = [term for term in terms if term not in values]
    if not unprinted:
        return [] if values["sbi"] == printed else [
            f"{where}: sbi={values['sbi']} is not the sum {printed} of the "
            f"call classes"]
    rules = [expect.get("sbi_derived", {}).get(term, {}).get(str(domain), {})
             for term in unprinted]
    if any("exact" not in rule and set(rule) != {"min", "max"}
           for rule in rules):
        return [f"{where}: the sbi terms {unprinted} have no exact count"]
    counts = [rule.get("exact") for rule in rules]
    if None not in counts:
        if values["sbi"] - printed != sum(counts):
            return [f"{where}: sbi={values['sbi']} less its printed terms is "
                    f"{values['sbi'] - printed}, not " + " + ".join(
                        f"{term}={count}" for term, count in
                        zip(unprinted, counts))]
        return []
    # M7-4's dbcn_input, the served reads of a domain with console input,
    # which the guest's polling paces: within its range.
    low = sum(rule.get("exact", rule.get("min")) for rule in rules)
    high = sum(rule.get("exact", rule.get("max")) for rule in rules)
    if not low <= values["sbi"] - printed <= high:
        return [f"{where}: sbi={values['sbi']} less its printed terms is "
                f"{values['sbi'] - printed}, outside {low}-{high}, the sum "
                f"of " + " + ".join(unprinted)]
    return []


def terminated_findings(state, domain, binding, match, counters, budget,
                        findings, facts):
    """A domain another terminated (M2): its DOMAIN_TERMINATED's hart, its
    exits within the counters' range, and its ticks after its entry and
    within the budget; returns its end, for the run's intervals."""
    where = f"G{domain}'s DOMAIN_TERMINATED"
    values = {"hart": int(match.group(1)), "exits": int(match.group(4)),
              "ticks": int(match.group(6), 16), "entered": 0}
    if values["hart"] != binding["hart"]:
        findings.append(f"{where}: hart={values['hart']}, but the binding "
                        f"names {binding['hart']}")
    finding = counter_rule("exits", counters["exits"], values["exits"],
                           where)
    if finding:
        findings.append(finding)
    entered = state.matched.get(("BE_MVP:10", domain))
    ticks = re.search(rf" ticks=({HEX})$", entered.text) if entered \
        else None
    if ticks:
        values["entered"] = int(ticks.group(1), 16)
    if not values["entered"] < values["ticks"] <= budget:
        findings.append(f"{where}: ticks=0x{values['ticks']:x} is not after "
                        f"its entry and within the budget")
    facts[f"exits_g{domain}"] = str(values["exits"])
    return values


def shutdown_findings(state, capture, expect, budget, findings, facts,
                      denials=None, requests=0):
    """Each BE_MVP:12's counters and sums, and BE_MVP:13 (Markers,
    Consistency and Concurrency), with each domain's DENY lines (DENIALS,
    {domain: count}, M1) in its exits and every one in the drained
    records, as each of hart 0's REQUESTS (BE_MVP:MGMT lines, M2); a v3
    scenario's sbi holds its printed terms and each unprinted one
    (sbi_terms; mgmt, sbi_derived's exact count), and a domain another
    terminated ends at its DOMAIN_TERMINATED (exits, ticks) instead of a
    shutdown; returns the parsed ends."""
    denials = denials or {}
    counters = dict(expect["counters"])
    if expect["outcome"].get("time_above_zero"):
        counters["time"] = {"min": 1, "max": counters["exits"]["max"]}
    shutdowns = {}
    for domain, binding in enumerate(expect["domains"]):
        line = state.matched.get(("BE_MVP:12", domain))
        match = SHUTDOWN.fullmatch(line.text) if line else None
        if not match:
            ended = TERMINATED.fullmatch(line.text) if line else None
            if ended:
                shutdowns[domain] = terminated_findings(
                    state, domain, binding, ended, counters, budget,
                    findings, facts)
            continue
        values = dict(zip(("hart", "domain") + COUNTERS,
                          (int(value) for value in match.groups()[:13])))
        values.update(zip(("ring_peak", "entered", "ticks"),
                          (int(value, 16) for value in match.groups()[13:])))
        shutdowns[domain] = values
        where = f"G{domain}'s BE_MVP:12"
        if values["hart"] != binding["hart"]:
            findings.append(f"{where}: hart={values['hart']}, but the "
                            f"binding names {binding['hart']}")
        for name, rule in sorted(counters.items()):
            finding = counter_rule(name, rule, values[name], where)
            if finding:
                findings.append(finding)
        if values["ring_peak"] > RING_PEAK_BUDGET:
            findings.append(f"{where}: ring_peak=0x{values['ring_peak']:x} "
                            f"is above half the ring (stop condition 3)")
        names = expect.get("exit_sum", ["sbi", "ipi"])
        total = sum(denials.get(domain, 0) if name == "denials" else
                    values[name] for name in names)
        if values["exits"] != total:
            findings.append(f"{where}: exits={values['exits']} is not "
                            f"{' + '.join(names)} = {total}")
        findings += sbi_findings(expect, domain, values, where)
        if values["lines"] != len(capture.domains[domain]):
            findings.append(f"{where}: lines={values['lines']} is not the "
                            f"{len(capture.domains[domain])} lines printed")
        entered = state.matched.get(("BE_MVP:10", domain))
        ticks = re.search(rf" ticks=({HEX})$", entered.text) if entered \
            else None
        if not ticks or int(ticks.group(1), 16) != values["entered"]:
            findings.append(f"{where}: entered=0x{values['entered']:x} is "
                            f"not its BE_MVP:10 ticks")
        if not values["entered"] < values["ticks"] <= budget:
            findings.append(f"{where}: ticks=0x{values['ticks']:x} is not "
                            f"after its entry and within the budget")
        facts[f"exits_g{domain}"] = str(values["exits"])
    line = state.matched.get(("BE_MVP:13", None))
    match = COMPLETE.fullmatch(line.text) if line else None
    if match and len(shutdowns) == len(expect["domains"]):
        domains, records, wakes = (int(value) for value in match.groups()[:3])
        idle, overlap, ticks = (int(value, 16) for value in
                                match.groups()[3:])
        drained = sum(len(lines) for lines in capture.domains) + sum(
            1 for key, _ in state.sequence if key[0] in CHAINED) + sum(
            denials.values()) + requests
        if domains != len(expect["domains"]):
            findings.append(f"BE_MVP:13 domains={domains}")
        if records != drained:
            findings.append(f"BE_MVP:13 records={records} is not the "
                            f"{drained} lines its records printed")
        if idle > ticks or ticks > budget or \
                ticks < max(value["ticks"] for value in shutdowns.values()):
            findings.append(f"BE_MVP:13 ticks=0x{ticks:x} idle_ticks="
                            f"0x{idle:x} are not within the run")
        spans = [(value["entered"], value["ticks"])
                 for value in shutdowns.values()]
        computed = max(0, min(end for _, end in spans) -
                       max(start for start, _ in spans))
        shorter = min(end - start for start, end in spans)
        if overlap != computed:
            findings.append(f"BE_MVP:13 overlap_ticks=0x{overlap:x} is not "
                            f"the intervals' 0x{computed:x}")
        if 2 * computed < shorter:
            findings.append(f"the domains overlap for 0x{computed:x} ticks, "
                            f"below half the shorter interval 0x{shorter:x} "
                            f"(the overlap floor, Q5)")
        facts.update(records=str(records), wakes=str(wakes),
                     overlap_ticks=f"0x{computed:x}",
                     shorter_ticks=f"0x{shorter:x}")
    return shutdowns


def stop_line(state, domain):
    """DOMAIN's first BE_MVP:12 line: its shutdown, or the transition
    (paused, terminated) after which its guest runs no more (M2)."""
    return next((line for key, line in state.sequence
                 if key == ("BE_MVP:12", domain)), None)


def cross_findings(state, capture, expect, phase_end=None):
    """Cross-stream order, only where the scenario declares it: a domain's
    lines after its own BE_MVP:10 (and before its first :12 and
    PHASE_END), and its :11 after its first line."""
    findings = []
    for domain, lines in enumerate(capture.domains):
        entered = state.matched.get(("BE_MVP:10", domain))
        stopped = stop_line(state, domain)
        ping = state.matched.get(("BE_MVP:11", domain))
        for line in lines:
            if entered is None or line.number < entered.number:
                findings.append(f"line {line.number}: G{domain} line before "
                                f"its BE_MVP:10")
            elif stopped is not None and line.number > stopped.number:
                findings.append(f"line {line.number}: G{domain} line after "
                                f"its BE_MVP:12")
            elif phase_end is not None and line.number > phase_end:
                findings.append(f"line {line.number}: G{domain} line after "
                                f"the failure")
        if ping is not None and (not lines or ping.number < lines[0].number):
            findings.append(f"line {ping.number}: G{domain}'s BE_MVP:11 "
                            f"before its first line")
    return findings


def alternations(order):
    return sum(1 for before, after in zip(order, order[1:])
               if before != after)


def monitor_value_findings(state, pins):
    """:09's WARL hedeleg, and :04/:06 against the kernel pins."""
    findings = []
    for key, line in state.sequence:
        if key[0] == "BE_MVP:09":
            value = re.search(rf" hedeleg=({HEX}) ", line.text)
            if value and (int(value.group(1), 16) & ~HEDELEG or
                          int(value.group(1), 16) & HEDELEG_REQUIRED !=
                          HEDELEG_REQUIRED):
                findings.append(f"line {line.number}: hedeleg="
                                f"{value.group(1)} is not a WARL reading of "
                                f"0x{HEDELEG:x}")
        if key[0] in ("BE_MVP:04", "BE_MVP:06"):
            for field, pin in (("kernel_bytes", "kernel_bytes"),
                               ("image_size", "image_size")):
                value = re.search(rf" {field}=({HEX})", line.text)
                if value and int(value.group(1), 16) != pins[pin]:
                    findings.append(f"line {line.number}: {field}="
                                    f"{value.group(1)} is not the pin "
                                    f"0x{pins[pin]:x}")
    return findings


def deny_counts(lines):
    """Each domain's DENY lines, {domain: count}, by the domain they name."""
    counts = {}
    for line in lines:
        named = re.search(r" domain=([0-9]+) ", line.text)
        domain = int(named.group(1)) if named else -1
        counts[domain] = counts.get(domain, 0) + 1
    return counts


def denial_findings(capture, state, expect, denies, facts, prefix=()):
    """The denial log against the guests' reports (planning/mvp-m1-plan.md,
    "The denial log against the guests' reports", rules 1 to 4): for each
    domain d, its DENY lines D1..Dn in capture order, its MVPINIT 08 lines
    R1..Rm, and its expected denials E1..Ek. A domain in PREFIX, which
    another's request may end anywhere in its run (M2's no-grant-check),
    shows E1..En only, n <= k, and Rn may be cut off (m = n or n - 1)."""
    findings, parsed = [], {}
    for line in denies:
        match = DENY.fullmatch(line.text)
        if not match:
            findings.append(f"line {line.number}: malformed BE_MVP:DENY line "
                            f"{line.text[:80]!r}")
            continue
        values = {key: value if key == "kind" else int(value, 0)
                  for key, value in zip(DENY_FIELDS, match.groups())}
        if values["domain"] >= len(expect["domains"]):
            findings.append(f"line {line.number}: a DENY line names domain "
                            f"{values['domain']}, which the binding lacks")
            continue
        parsed.setdefault(values["domain"], []).append((line, values))
    for domain, binding in enumerate(expect["domains"]):
        name = f"G{domain}"
        log = parsed.get(domain, [])
        reports = [(line, DENIED.fullmatch(line.text))
                   for line in capture.domains[domain]
                   if line.text.startswith("MVPINIT 08 ")]
        expected = expect["denials"].get(str(domain), [])
        facts[f"denials_g{domain}"] = str(len(log))
        if domain in prefix:
            if not len(log) - 1 <= len(reports) <= len(log) <= \
                    len(expected):
                findings.append(f"{name}: {len(log)} BE_MVP:DENY lines and "
                                f"{len(reports)} MVPINIT 08 reports are not "
                                f"a prefix of its {len(expected)} expected "
                                f"denials")
            # A last DENY line whose report the run's end cut off.
            reports += [(None, None)] * (len(log) - len(reports))
        elif not len(log) == len(reports) == len(expected):
            findings.append(f"{name}: {len(log)} BE_MVP:DENY lines, "
                            f"{len(reports)} MVPINIT 08 reports, and "
                            f"{len(expected)} expected denials differ")
        entered = state.matched.get(("BE_MVP:10", domain))
        stopped = stop_line(state, domain)
        for index, ((line, deny), (report, seen), entry) in enumerate(
                zip(log, reports, expected), 1):
            where = f"line {line.number}: {name} denial {index}"
            if not re.fullmatch(entry["line"]["regex"], line.text) or \
                    deny["hart"] != binding["hart"]:
                findings.append(f"{where}: {line.text[:60]!r} is not "
                                f"{entry['line']['template'][:60]!r}")
            if entered is None or line.number < entered.number or \
                    (stopped is not None and line.number > stopped.number):
                findings.append(f"{where}: not between its BE_MVP:10 and "
                                f":12")
            if report is None:
                # PREFIX's last denial, its report cut off: its line alone.
                if deny["seq"] != index:
                    findings.append(f"{where}: seq={deny['seq']}, not "
                                    f"{index}")
                continue
            if seen is None:
                findings.append(f"line {report.number}: malformed MVPINIT 08 "
                                f"line {report.text[:80]!r}")
                continue
            gpa, access = int(entry["gpa"], 16), entry["access"]
            r_gpa, va, pc = (int(seen.group(key), 16) for key in (3, 4, 5))
            # 1: Di's seq is i, and Di precedes Ri.
            if deny["seq"] != index:
                findings.append(f"{where}: seq={deny['seq']}, not {index}, "
                                f"the order the guest reports")
            if line.number > report.number:
                findings.append(f"{where}: follows its report at line "
                                f"{report.number}; the record precedes the "
                                f"resume")
            # 2: gpa, htval (64-bit, alias-rejecting), stval, sepc.
            if not deny["gpa"] == r_gpa == gpa:
                findings.append(f"{where}: the DENY line's gpa=0x"
                                f"{deny['gpa']:x}, the report's 0x{r_gpa:x}, "
                                f"and the expected 0x{gpa:x} differ")
            if deny["htval"] != gpa >> 2:
                findings.append(f"{where}: htval=0x{deny['htval']:x} is not "
                                f"the GPA 0x{gpa:x} >> 2, compared as 64-bit "
                                f"values")
            if deny["stval"] != va or deny["sepc"] != pc:
                findings.append(f"{where}: stval=0x{deny['stval']:x} sepc=0x"
                                f"{deny['sepc']:x} are not the report's va=0x"
                                f"{va:x} pc=0x{pc:x}")
            # 3: cause and injected, kind, htinst.
            if seen.group(2) != access or \
                    (deny["cause"], deny["injected"]) != ACCESS_FAULT[access]:
                findings.append(f"{where}: cause=0x{deny['cause']:x} "
                                f"injected=0x{deny['injected']:x} for a "
                                f"reported {seen.group(2)}, not the access "
                                f"fault for the expected {access}")
            if deny["kind"] != entry["kind"]:
                findings.append(f"{where}: kind={deny['kind']} is not the "
                                f"sealed record's {entry['kind']}")
            if deny["htinst"] not in HTINST[access]:
                findings.append(f"{where}: htinst=0x{deny['htinst']:x} is "
                                f"neither zero nor the init's transformed "
                                f"{access}")
            # 4: the report shows the fault observed (and the page kept).
            if (int(seen.group(6)), int(seen.group(7)), seen.group(8)) != \
                    (SIGSEGV, SEGV_ACCERR, "1"):
                findings.append(f"line {report.number}: {name} reports signo="
                                f"{seen.group(6)} code={seen.group(7)} "
                                f"observed={seen.group(8)}")
            if access == "store" and seen.group(9) != "1":
                findings.append(f"line {report.number}: {name} reports "
                                f"unchanged={seen.group(9)}: the denied store "
                                f"changed the page")
        vstvecs = sorted({deny["vstvec"] for _, deny in log})
        if len(vstvecs) > 1 or any(vstvec & 3 for vstvec in vstvecs):
            findings.append(f"{name}: the DENY lines show vstvec "
                            f"{[hex(vstvec) for vstvec in vstvecs]}, not one "
                            f"in Direct mode")
    return findings, parsed


def channel_findings(capture, expect):
    """Data crosses the channel from the writer to the reader: equal
    MVPINIT 07 digests, and the reader's match=1."""
    findings, digests = [], {}
    for domain, binding in enumerate(expect["domains"]):
        role = binding.get("role")
        lines = [match for match in (CHANNEL_REPORT.fullmatch(line.text)
                                     for line in capture.domains[domain])
                 if match and match.group(1) == role]
        if len(lines) != 1:
            findings.append(f"G{domain}: {len(lines)} MVPINIT 07 CHANNEL "
                            f"lines for its role {role}")
            continue
        digests[role] = lines[0].group(4)
        if role == "reader" and lines[0].group(5) != "1":
            findings.append(f"G{domain}: the reader shows match="
                            f"{lines[0].group(5)}")
    if len(set(digests.values())) > 1:
        findings.append(f"the writer's digest 0x{digests.get('writer')} and "
                        f"the reader's 0x{digests.get('reader')} differ")
    return findings


def rule_texts(source, rules):
    """Whether SOURCE is one or more of the policy's rule texts, joined by
    spaces (tools/policy-check.py)."""
    rest = source
    while rest:
        text = next((text for text in rules if rest == text or
                     rest.startswith(text + " ")), None)
        if text is None:
            return False
        rest = rest[len(text):].lstrip(" ")
    return bool(source)


def report_findings(expect, data):
    """The authority report (--report) itself: the expectation's, with its
    grants each allowed by a rule, its flows declared, and every check A1
    to A8 pass; returns (findings, the parsed report or None)."""
    want = expect["report"]
    if data is None:
        return [f"the expectation names {want['file']}, but no --report was "
                f"given"], None
    try:
        report = json.loads(data)
        grants, flows = report["grants"], report["flows"]
        rules = {rule["text"] for rule in report["policy"]["rules"]}
        checks = {check["analysis"]: check["result"]
                  for check in report["checks"]}
        identity = report["identity"]["configuration_identity"]
    except (ValueError, KeyError, TypeError) as error:
        return [f"the report is malformed ({error})"], None
    findings = []
    if hashlib.sha256(data).hexdigest() != want["sha256"]:
        findings.append("the report is not the one the expectation was "
                        "generated with (SHA-256)")
    if identity != want["configuration_identity"]:
        findings.append(f"the report's configuration identity {identity} is "
                        f"not the expectation's")
    instance = "Instance 3's" if "management" in want else "Instance 2's"
    if len(grants) != want["grants"]:
        findings.append(f"the report holds {len(grants)} grants, not "
                        f"{instance} {want['grants']}")
    findings += [f"the report's grant {grant.get('subject')} "
                 f"{grant.get('object')} has no rule ({grant.get('source')!r})"
                 for grant in grants
                 if not rule_texts(str(grant.get("source")), rules)]
    if flows != want["flows"] or any(flow.get("declared") != "yes"
                                     for flow in flows):
        findings.append(f"the report's flows {flows} are not the "
                        f"expectation's " + ("declared flows" if len(
                            want["flows"]) > 1 else "one declared flow"))
    if sorted(checks) != ANALYSES or set(checks.values()) != {"pass"}:
        findings.append(f"the report's checks {checks} are not A1 to A8, "
                        f"each pass")
    if "management" in want:
        # M2: exactly the expectation's management grants, each a domain
        # rule's, with its permissions.
        management = [{"subject": grant.get("subject"),
                       "object": grant.get("object"),
                       "permissions": sorted(grant.get("permissions", [])),
                       "source": grant.get("source")}
                      for grant in grants if grant.get("class") == "domain"]
        if management != [dict(entry, permissions=sorted(
                entry["permissions"])) for entry in want["management"]]:
            findings.append(f"the report's management grants {management} "
                            f"are not the expectation's")
    return findings, report


def boot_report_findings(state, report):
    """The boot lines against the report (planning/mvp-m1-plan.md, "The
    channel and the report"): each :03 GSTAGE_BUILT_REWALKED line its
    window grant's GPA, HPA, and size; CHANNEL_CHECKED the channel's GPA,
    HPA, and size, its endpoints, each endpoint's leaf from the derived
    flags (map V U A, read R, write W D), and the configuration
    identity."""
    findings = []
    try:
        index = {subject["name"]: subject["domain_index"]
                 for subject in report["subjects"]}
        base = {item["name"]: int(item["extent"]["base"], 16)
                for item in report["objects"]}
        channel = next(item for item in report["labeling"]["objects"]
                       if item["class"] == "channel")
        ends = {perm: index[grant["subject"]] for grant in report["grants"]
                if grant["object"] == channel["name"]
                for perm in grant["permissions"]}
        leaves, page = {}, None
        for grant in report["grants"]:
            derived = grant.get("derived")
            if grant["class"] != "memory" or not derived:
                continue
            gpa, size, flags = (int(derived[key], 16)
                                for key in ("gpa", "size", "flags"))
            hpa = base[grant["object"]]
            domain = index[grant["subject"]]
            if grant["object"] == channel["object"]:
                leaves[domain] = (hpa >> 12) << 10 | flags
                page = (gpa, hpa, size)
                continue
            line = state.matched.get(("BE_MVP:03", domain))
            match = GSTAGE.match(line.text) if line else None
            if match and tuple(int(value, 16) for value in match.groups()) \
                    != (gpa, hpa, size):
                findings.append(f"line {line.number}: G{domain}'s window is "
                                f"not its grant's GPA 0x{gpa:x}, HPA 0x"
                                f"{hpa:x}, and size 0x{size:x}")
        identity = report["identity"]["configuration_identity"]
        want = (ends["send"], ends["receive"]) + page + (
            leaves[ends["send"]], leaves[ends["receive"]], identity)
    except (KeyError, StopIteration, TypeError, ValueError) as error:
        return findings + [f"the report has no channel to match ({error!r})"]
    line = state.matched.get(("BE_MVP:03", None))
    match = CHANNEL_CHECKED.fullmatch(line.text) if line else None
    if not match:
        return findings
    got = tuple(int(value, 0) for value in match.groups()[:-1]) + (
        match.group(8),)
    names = ("writer", "reader", "gpa", "hpa", "bytes", "writer_pte",
             "reader_pte", "config")
    for name, value, wanted in zip(names, got, want):
        if value == wanted:
            continue
        if name == "config":
            findings.append(f"line {line.number}: CHANNEL_CHECKED config="
                            f"{value} is not the report's configuration "
                            f"identity {wanted}")
        else:
            findings.append(f"line {line.number}: CHANNEL_CHECKED {name}="
                            f"{value:#x} is not the report's {wanted:#x}")
    return findings


def absent_findings(capture, outcome):
    """No line of either stream starts with a prefix the variant declares
    absent (M1: reader-write's CHANNEL_CHECKED; no-inject's DENY and
    MVPINIT 08 lines)."""
    lines = capture.monitor + [line for own in capture.domains
                               for line in own]
    return [f"line {line.number}: {line.text[:60]!r}, which the variant "
            f"declares absent" for prefix in outcome.get("absent", [])
            for line in lines if line.text.startswith(prefix)]


# ------------------------------------------------------------ M2's rules
def shown(value):
    """A field's value as a line shows it: an integer in hex."""
    return f"{value:#x}" if isinstance(value, int) else str(value)


def pages_report_findings(state, expect, report):
    """The boot lines against the report (planning/mvp-m2-plan.md,
    Markers; M1's channel rule for each page): each :03
    GSTAGE_BUILT_REWALKED line its window grant's GPA, HPA, and size; each
    :03 PAGE_CHECKED its page's GPA and size (each end's grant's) and HPA,
    its kind, its writer (a channel page's send grant) and reader (its
    receive grant, or a secret page's one memory grant), each end's leaf
    from the derived flags, and the configuration identity; each :05
    PAGE_CLEARED (a channel page) and SECRET_PLACED (the secret page, the
    secret's bytes) its page's HPA."""
    findings, names = [], [page["name"] for page in expect["pages"]]
    try:
        index = {subject["name"]: subject["domain_index"]
                 for subject in report["subjects"]}
        base = {item["name"]: int(item["extent"]["base"], 16)
                for item in report["objects"]}
        channels = {item["name"]: item["object"]
                    for item in report["labeling"]["objects"]
                    if item["class"] == "channel"}
        ends, leaves, extents = {}, {}, {}
        for grant in report["grants"]:
            if grant["class"] == "channel":
                for permission in grant["permissions"]:
                    ends.setdefault(channels[grant["object"]], {})[
                        permission] = index[grant["subject"]]
            derived = grant.get("derived")
            if grant["class"] != "memory" or not derived:
                continue
            gpa, size, flags = (int(derived[key], 16)
                                for key in ("gpa", "size", "flags"))
            hpa, domain = base[grant["object"]], index[grant["subject"]]
            if grant["object"] in names:
                leaves.setdefault(grant["object"], {})[domain] = \
                    (hpa >> 12) << 10 | flags
                extents.setdefault(grant["object"], set()).add((gpa, size))
                continue
            line = state.matched.get(("BE_MVP:03", domain))
            match = GSTAGE.match(line.text) if line else None
            if match and tuple(int(value, 16) for value in match.groups()) \
                    != (gpa, hpa, size):
                findings.append(f"line {line.number}: G{domain}'s window is "
                                f"not its grant's GPA 0x{gpa:x}, HPA 0x"
                                f"{hpa:x}, and size 0x{size:x}")
        want = {}
        for number, page in enumerate(expect["pages"]):
            name = page["name"]
            (gpa, size), = extents[name]
            if page["kind"] == "channel":
                writer, reader = ends[name]["send"], ends[name]["receive"]
            else:
                (reader,), writer = leaves[name], None
            want[number] = {
                "kind": page["kind"], "writer": writer, "reader": reader,
                "gpa": gpa, "hpa": base[name], "bytes": size,
                "writer_pte": leaves[name].get(writer),
                "reader_pte": leaves[name][reader],
                "config": report["identity"]["configuration_identity"]}
    except (KeyError, TypeError, ValueError) as error:
        return findings + [f"the report has no pages to match ({error!r})"]
    fields = ("kind", "writer", "reader", "gpa", "hpa", "bytes",
              "writer_pte", "reader_pte", "config")
    secret = len(bytes.fromhex(expect["secret_hex"]))
    for _, line in state.sequence:
        if line.text.startswith("BE_MVP:03 PAGE_CHECKED "):
            match = PAGE_CHECKED.fullmatch(line.text)
            number = int(match.group(1)) if match else -1
            if number not in want:
                findings.append(f"line {line.number}: no report page for "
                                f"{line.text[:50]!r}")
                continue
            got = {field: value if field in ("kind", "config") or
                   value is None else int(value, 0)
                   for field, value in zip(fields, match.groups()[1:])}
            findings += [f"line {line.number}: PAGE_CHECKED page={number} "
                         f"{field}={shown(got[field])} is not the report's "
                         f"{shown(want[number][field])}" for field in fields
                         if got[field] != want[number][field]]
        match = PAGE_PLACED.fullmatch(line.text)
        if match:
            number = int(match.group(2))
            kind = "secret" if match.group(1) == "SECRET_PLACED" else \
                "channel"
            page = want.get(number, {})
            if page.get("kind") != kind or int(match.group(3), 16) != \
                    page["hpa"] or int(match.group(4), 16) != (
                        secret if kind == "secret" else page["bytes"]):
                findings.append(f"line {line.number}: {line.text[:60]!r} is "
                                f"not the report's {kind} page {number}")
    return findings


def measurement_value(expect, report, measured):
    """The checker's own measurement (planning/mvp-m2-plan.md, Q7):
    SHA-256 over MEASURED's inputs, the measured domain's kernel and DTB
    as built (--kernel, --dtb), its secret page (the secret, then zeros
    to the page's size), and the report's configuration identity, in that
    order; (hex digest, bytes), or None without the build outputs or the
    report. MEASURED PINNED_MEASUREMENT stands for a fixture captured with
    an earlier guest kernel, whose build outputs are not retained: the
    measurement its pinned expectation records (measurement_hex and its
    bytes), the generator's over those outputs. An expectation that
    carries M9's log data has no such measurement (planning/mvp-m9-plan.md,
    D-4): None, the pinned value above all."""
    if "log" in expect:
        return None
    if measured == PINNED_MEASUREMENT:
        try:
            return expect["measurement_hex"], int(
                expect["measurement"]["bytes"])
        except (KeyError, TypeError, ValueError):
            return None
    if not measured or report is None:
        return None
    try:
        page = next(int(item["bytes"], 16) for item in expect["pages"]
                    if item["kind"] == "secret")
        secret = bytes.fromhex(expect["secret_hex"])
        identity = bytes.fromhex(
            report["identity"]["configuration_identity"])
    except (KeyError, StopIteration, TypeError, ValueError):
        return None
    data = measured[0] + measured[1] + secret.ljust(page, b"\0") + identity
    return hashlib.sha256(data).hexdigest(), len(data)


def measurement_findings(capture, expect, own, facts):
    """The measurement (Q7): BE_MVP:06 MEASURED's digest and bytes the
    checker's own (measurement_value), as is DOMAIN_TERMINATED's for the
    measured domain, read again from the same memory; a declared failure
    measurement's DETAIL shows the checker's own value as computed= and
    the variant's expected_hex, one bit from it, as expected=."""
    findings, where = [], expect["measurement"]
    if own is None:
        return ["the expectation measures its domain, but the checker has "
                "no --kernel and --dtb, or no report, to compute it"]
    digest, total = own
    facts["measurement"] = digest
    for line in capture.monitor:
        match = MEASURED.fullmatch(line.text)
        if match and (int(match.group(1)), int(match.group(2)),
                      int(match.group(3)), match.group(4)) != (
                where["domain"], where["hart"], total, digest):
            findings.append(f"line {line.number}: MEASURED domain="
                            f"{match.group(1)} bytes={match.group(3)} sha256="
                            f"{match.group(4)} is not the checker's own "
                            f"domain={where['domain']} bytes={total} sha256="
                            f"{digest}")
        match = TERMINATED.fullmatch(line.text)
        if match and int(match.group(2)) == where["domain"] and \
                match.group(5) != digest:
            findings.append(f"line {line.number}: DOMAIN_TERMINATED sha256="
                            f"{match.group(5)} is not the measurement, the "
                            f"checker's own {digest}")
        match = DETAIL_FORMS["measurement"].fullmatch(line.text)
        if match and (match.group(3) != digest or match.group(4) !=
                      expect["outcome"].get("expected_hex") or bin(
                          int(match.group(3), 16) ^ int(match.group(4), 16)
                      ).count("1") != 1):
            findings.append(f"line {line.number}: the DETAIL's computed="
                            f"{match.group(3)[:16]}... expected="
                            f"{match.group(4)[:16]}... are not the checker's "
                            f"own {digest[:16]}... and the variant's one bit "
                            f"from it")
    return findings


def transitions(state):
    """hart 0's DOMAIN_PAUSED and DOMAIN_TERMINATED lines, in order: [(the
    function that causes it, line, match)]."""
    out = []
    for key, line in state.sequence:
        for function, (_, pattern) in TRANSITION.items():
            match = pattern.fullmatch(line.text) if key[0] == "BE_MVP:12" \
                else None
            if match:
                out.append((function, line, match))
    return out


def transition_findings(state, expect):
    """The paused and terminated states (Q4, Q15): each transition names
    its domain's hart; a domain is paused at most once and before it is
    terminated, and the paused hart takes no further exit (equal exits),
    no earlier in time."""
    findings, seen = [], {}
    for function, line, match in transitions(state):
        domain = int(match.group(2))
        bindings = expect["domains"]
        if domain >= len(bindings) or int(match.group(1)) != \
                bindings[domain]["hart"] or int(match.group(3)) >= \
                len(bindings):
            findings.append(f"line {line.number}: {line.text[:60]!r} names "
                            f"no domain's hart and requester")
            continue
        if (domain, function) in seen:
            findings.append(f"line {line.number}: domain {domain}'s second "
                            f"{TRANSITION[function][0]}")
        seen[domain, function] = match
        paused = seen.get((domain, "pause"))
        if function == "terminate" and paused and (
                match.group(4) != paused.group(4) or
                int(match.group(6), 16) < int(paused.group(5), 16)):
            findings.append(f"line {line.number}: DOMAIN_TERMINATED exits="
                            f"{match.group(4)} ticks={match.group(6)} after "
                            f"DOMAIN_PAUSED exits={paused.group(4)} ticks="
                            f"{paused.group(5)}: the paused hart took an exit")
        if function == "pause" and (domain, "terminate") in seen:
            findings.append(f"line {line.number}: domain {domain} paused "
                            f"after its termination")
    return findings


def guest_calls(lines):
    """A domain's management calls as its MVPINIT 10 lines report them, a
    burst line standing for its count of calls, each with the burst's
    result: ([(line, fid, target, result)], findings)."""
    calls, findings = [], []
    for line in lines:
        if not line.text.startswith("MVPINIT 10 "):
            continue
        match = GUEST_MGMT.fullmatch(line.text)
        if not match:
            findings.append(f"line {line.number}: malformed MVPINIT 10 line "
                            f"{line.text[:80]!r}")
        elif match.group(1) is not None:
            calls.append((line, match.group(1), int(match.group(2)),
                          int(match.group(3))))
        else:
            calls += [(line, match.group(5), int(match.group(6)),
                       int(match.group(7)))] * int(match.group(4))
            if match.group(4) != match.group(8):
                findings.append(f"line {line.number}: a burst of "
                                f"{match.group(4)} with {match.group(8)} "
                                f"results")
    return calls, findings


def mgmt_findings(capture, state, expect, mgmts, facts, prefix=()):
    """The management log against the guests' reports and the declared
    requests (planning/mvp-m2-plan.md, Markers, Q9, Q14): for each domain
    d, its BE_MVP:MGMT lines M1..Mn in capture order, its guest's calls of
    pause and terminate C1..Cm (MVPINIT 10 MGMT; a burst line stands for
    its count of calls), and its expected requests E1..Ek: n = m = k (n =
    m <= k for a domain in PREFIX, which the run may end); Mi is Ei's line
    (seq i, the function, the target, the result, the target's state),
    Ci's function, target, and result, between d's :10 and :12, and
    before Ci's line; a delivered request's line follows its target's
    transition, which names d. Another FID's call is answered on d's hart
    (-2) with no line, and hart 0 never logs one."""
    findings, parsed = [], {}
    for line in mgmts:
        match = MGMT.fullmatch(line.text)
        if not match:
            findings.append(f"line {line.number}: malformed BE_MVP:MGMT line "
                            f"{line.text[:80]!r}")
            continue
        values = dict(zip(MGMT_FIELDS, match.groups()))
        if values["fid"] not in MGMT_NAMES:
            findings.append(f"line {line.number}: a BE_MVP:MGMT line for FID "
                            f"{values['fid']}, which the requester's hart "
                            f"answers itself")
        if int(values["domain"]) >= len(expect["domains"]):
            findings.append(f"line {line.number}: a BE_MVP:MGMT line names "
                            f"domain {values['domain']}, which the binding "
                            f"lacks")
            continue
        parsed.setdefault(int(values["domain"]), []).append((line, values))
    moved = {(int(match.group(2)), function): (line, int(match.group(3)))
             for function, line, match in transitions(state)}
    for domain, binding in enumerate(expect["domains"]):
        name = f"G{domain}"
        log = parsed.get(domain, [])
        calls, found = guest_calls(capture.domains[domain])
        findings += found
        named = [call for call in calls if call[1] in MGMT_NAMES]
        findings += [f"line {call[0].number}: {name}'s FID {call[1]} call "
                     f"returned {call[3]}, not {SBI_NOT_SUPPORTED}"
                     for call in calls if call[1] not in MGMT_NAMES and
                     call[3] != SBI_NOT_SUPPORTED]
        expected = expect["mgmt"].get(str(domain), [])
        facts[f"mgmt_g{domain}"] = str(len(log))
        if len(log) != len(named) or len(log) > len(expected) or (
                domain not in prefix and len(log) != len(expected)):
            findings.append(f"{name}: {len(log)} BE_MVP:MGMT lines, "
                            f"{len(named)} reported calls, and "
                            f"{len(expected)} expected requests differ")
        entered = state.matched.get(("BE_MVP:10", domain))
        stopped = stop_line(state, domain)
        for index, ((line, values), call, entry) in enumerate(
                zip(log, named, expected), 1):
            where = f"line {line.number}: {name} request {index}"
            if not re.fullmatch(entry["line"]["regex"], line.text) or \
                    int(values["hart"]) != binding["hart"]:
                findings.append(f"{where}: {line.text[:70]!r} is not "
                                f"{entry['line']['template'][:70]!r}")
            if int(values["seq"]) != index:
                findings.append(f"{where}: seq={values['seq']}, not {index}")
            if (values["fid"], int(values["target"]), int(
                    values["result"])) != call[1:]:
                findings.append(f"{where}: fid={values['fid']} target="
                                f"{values['target']} result="
                                f"{values['result']} is not the call "
                                f"{name} reports at line {call[0].number}")
            if line.number > call[0].number:
                findings.append(f"{where}: follows the report of its call "
                                f"at line {call[0].number}")
            if entered is None or line.number < entered.number or (
                    stopped is not None and line.number > stopped.number):
                findings.append(f"{where}: not between its BE_MVP:10 and "
                                f":12")
            if int(values["result"]) == 0:
                done = moved.get((int(values["target"]), values["fid"]))
                if done is None or done[1] != domain or \
                        done[0].number > line.number:
                    findings.append(f"{where}: a delivered {values['fid']} "
                                    f"without its target's transition by "
                                    f"{name} before it")
    return findings, parsed


def request_findings(capture, expect, failed=False):
    """The keyed digests (Q6, Q8): each MVPINIT 09 REQUEST (the
    requester's) and RESPONSE (the server's) digest is the checker's own
    HMAC-SHA-256, keyed by the secret, of the request's sequence number as
    8 little-endian bytes and its message zero-padded to 64 bytes; the
    two sides' digests equal for each n; every answered request on both
    sides once and the unanswered one on the requester's alone, timeout=1,
    after the report of its pause call, the requester's call of seq
    unanswered_after_seq. A FAILED run (the requester ended early) shows
    any of its lines, each with the right digest, in order."""
    findings, requests = [], expect["requests"]
    key = bytes.fromhex(expect["secret_hex"])
    messages = {item["n"]: item for item in requests["messages"]}
    sides = {"REQUEST": requests["requester"], "RESPONSE": requests["server"]}
    seen = {}
    for domain, lines in enumerate(capture.domains):
        for line in lines:
            if not line.text.startswith("MVPINIT 09 "):
                continue
            match = REQUEST.fullmatch(line.text)
            if not match or sides[match.group(1)] != domain or int(
                    match.group(2)) not in messages:
                findings.append(f"line {line.number}: {line.text[:60]!r} is "
                                f"no request of G{domain}'s")
                continue
            kind, number = match.group(1), int(match.group(2))
            seen.setdefault((kind, number), []).append((line, match.group(3)))
    for (kind, number), entries in sorted(seen.items()):
        item = messages[number]
        text = item["message"].encode("ascii").ljust(64, b"\0")
        if text.hex() != item["message_hex"] or len(text) != 64:
            findings.append(f"request {number}'s message_hex is not its "
                            f"message zero-padded to 64 bytes")
        own = hmac.new(key, number.to_bytes(8, "little") + text,
                       hashlib.sha256).hexdigest()
        for line, digest in entries:
            if digest is None and (kind != "REQUEST" or
                                   not item.get("timeout")):
                findings.append(f"line {line.number}: a timeout for request "
                                f"{number}, which is answered")
            elif digest is not None and (digest != own or
                                         item.get("timeout")):
                findings.append(f"line {line.number}: {kind} n={number} "
                                f"digest={digest[:16]}... is not the "
                                f"HMAC-SHA-256 {own[:16]}... of its request"
                                + (", which is unanswered" if
                                   item.get("timeout") else ""))
        if len(entries) > 1:
            findings.append(f"{len(entries)} {kind} lines for request "
                            f"{number}")
    digests = {key: entries[0][1] for key, entries in seen.items()}
    for number, item in sorted(messages.items()):
        both = digests.get(("REQUEST", number)), digests.get(("RESPONSE",
                                                               number))
        if None not in both and both[0] != both[1]:
            findings.append(f"request {number}: the requester's digest "
                            f"{both[0][:16]}... and the server's "
                            f"{both[1][:16]}... differ")
        want = {"REQUEST": 1, "RESPONSE": 0 if item.get("timeout") else 1}
        for kind, count in want.items():
            if not failed and len(seen.get((kind, number), [])) != count:
                findings.append(f"{len(seen.get((kind, number), []))} {kind} "
                                f"lines for request {number}, expected "
                                f"{count}")
    if failed:
        answered = [number for kind, number in sorted(seen)
                    if kind == "RESPONSE"]
        if answered != list(range(1, len(answered) + 1)):
            findings.append(f"the server answered requests {answered}, not "
                            f"a first run of them")
    calls = [call for call in guest_calls(capture.domains[
        requests["requester"]])[0] if call[1] in MGMT_NAMES]
    after = requests.get("unanswered_after_seq")
    for (kind, number), entries in seen.items():
        line = entries[0][0]
        if entries[0][1] is None and after and (
                len(calls) < after or line.number < calls[after - 1][0]
                .number):
            findings.append(f"line {line.number}: request {number}'s timeout "
                            f"precedes the report of request {after}, the "
                            f"pause")
    return findings


def order_findings(capture, expect):
    """The declared order of the transitions and the ends (Markers): each
    of the expectation's order prefixes on exactly one of hart 0's lines,
    in that order."""
    findings, last = [], None
    for prefix in expect.get("order", []):
        hits = [line for line in capture.monitor
                if (line.text + " ").startswith(prefix + " ")]
        if len(hits) != 1:
            findings.append(f"{len(hits)} lines start {prefix!r}, expected "
                            f"one")
            continue
        if last is not None and hits[0].number < last.number:
            findings.append(f"line {hits[0].number}: {prefix!r} precedes "
                            f"line {last.number}, {last.text[:40]!r}, "
                            f"against the declared order")
        last = hits[0]
    return findings


def required_findings(capture, outcome):
    """A declared failure's required lines (M2's no-grant-check): each on
    exactly one of hart 0's lines before its first FAIL; and a declared
    run budget at most the run-timeout DETAIL's ticks."""
    lines = []
    for line in capture.monitor:
        if line.text.startswith(FAIL_PREFIX):
            break
        lines.append(line)
    findings = [f"{count} of hart 0's lines before the failure are "
                f"{entry['template'][:60]!r}, expected one"
                for entry in outcome.get("required_lines", [])
                for count in [sum(1 for line in lines
                                  if re.fullmatch(entry["regex"],
                                                  line.text))]
                if count != 1]
    if "run_budget_ticks" in outcome:
        budget = int(outcome["run_budget_ticks"], 16)
        details = [DETAIL_FORMS["ticks"].fullmatch(line.text)
                   for line in capture.monitor[len(lines):]]
        ticks = [int(match.group(1), 16) for match in details if match]
        if not ticks or ticks[0] < budget:
            findings.append(f"the run-timeout DETAIL's ticks "
                            f"{hex(ticks[0]) if ticks else 'none'} are not "
                            f"at least the budget 0x{budget:x}")
    return findings


def ping_findings(state, expect, mgmts):
    """The IPI probe's SPV (Plan revision M2-A.1): each BE_MVP:11 line
    shows spv=1, M0's rule, or spv=0 where the image has the management
    extension (a v3 expectation's mgmt) and its received= lies in a
    management wait of its own hart, [ticks, ticks + service] of one of
    MGMTS (hart 0's BE_MVP:MGMT lines) naming that hart, both since the
    barrier as the monitor prints them: a hart that waits in HS for hart
    0's MGMT_RESULT serves a PING it finds meanwhile (Q14), and its PONG
    shows SPV 0. Returns (findings, {domain: the fields of the request
    whose wait holds its probe})."""
    findings, waited = [], {}
    waits = [dict(zip(MGMT_FIELDS, match.groups())) for match in (
        MGMT.fullmatch(line.text) for line in mgmts) if match]
    for key, line in state.sequence:
        match = IPI_PROBE.fullmatch(line.text) if key[0] == "BE_MVP:11" \
            else None
        if not match or match.group(6) == "1":
            continue
        hart, domain = int(match.group(1)), int(match.group(2))
        received = int(match.group(4), 16)
        where = (f"line {line.number}: G{domain}'s BE_MVP:11 spv=0, a PONG "
                 f"answered in HS")
        if "mgmt" not in expect:
            findings.append(f"{where}, but the image has no management "
                            f"extension, so its hart never waits in HS "
                            f"(Plan revision M2-A.1)")
            continue
        wait = next((values for values in waits
                     if int(values["hart"]) == hart and
                     int(values["ticks"], 16) <= received <=
                     int(values["ticks"], 16) + int(values["service"], 16)),
                    None)
        if wait is None:
            findings.append(f"{where}, but received=0x{received:x} lies in "
                            f"no management wait of hart {hart}, [ticks, "
                            f"ticks + service] of a BE_MVP:MGMT line naming "
                            f"it (Plan revision M2-A.1)")
        else:
            waited[domain] = wait
    return findings, waited


def budget_of(state, layout_budget):
    line = state.matched.get(("BE_MVP:07", None))
    match = re.search(rf" budget_ticks=({HEX})$", line.text) if line else None
    return int(match.group(1), 16) if match else layout_budget


def costs(state, shutdowns, denials=None, requests=None, waited=None):
    """The Costs stage, recorded only: ticks from the records' times, each
    denial's service ticks (its post minus its exit, M1), and each
    management request's (its answer minus the request) and the
    measurement's ticks (M2); and, for a probe served inside a management
    wait (WAITED, ping_findings(); Plan revision M2-A.1), that fact and
    the seq of the request whose wait holds it."""
    out = {}
    waited = waited or {}
    for domain, log in sorted((denials or {}).items()):
        for index, (_, values) in enumerate(log, 1):
            out[f"g{domain}_denial{index}_service_ticks"] = values["service"]
    for domain, log in sorted((requests or {}).items()):
        for _, values in log:
            out[f"g{domain}_mgmt{values['seq']}_service_ticks"] = int(
                values["service"], 16)
    for _, line in state.sequence:
        match = MEASURED.fullmatch(line.text)
        if match:
            out["hart0_measure_ticks"] = int(match.group(5), 16)
    for domain, values in sorted(shutdowns.items()):
        run = values["ticks"] - values["entered"]
        out[f"g{domain}_run_ticks"] = run
        out[f"g{domain}_run_ticks_per_exit"] = run // max(values["exits"], 1)
        ping = state.matched.get(("BE_MVP:11", domain))
        match = IPI_PROBE.fullmatch(ping.text) if ping else None
        if match:
            sent, received, answered = (int(value, 16) for value in
                                        match.groups()[2:5])
            out[f"g{domain}_ping_to_receipt_ticks"] = received - sent
            out[f"g{domain}_receipt_to_pong_ticks"] = answered - received
            if domain in waited:
                out[f"g{domain}_ping_in_mgmt_wait"] = 1
                out[f"g{domain}_ping_mgmt_seq"] = int(waited[domain]["seq"])
    line = state.matched.get(("BE_MVP:13", None))
    match = COMPLETE.fullmatch(line.text) if line else None
    if match:
        records, wakes = int(match.group(2)), int(match.group(3))
        idle, ticks = int(match.group(4), 16), int(match.group(6), 16)
        out.update(hart0_idle_ticks=idle, hart0_run_ticks=ticks,
                   hart0_wakes=wakes, hart0_records=records,
                   hart0_idle_permille=idle * 1000 // max(ticks, 1))
    return out


def detail_findings(klass, outcome, detail, expect, state, findings):
    """The DETAIL line after a declared failure (or its absence); a
    variant that declares its DETAIL lines (M1's) needs one of them, even
    for a class whose own form takes none (gstage, the channel check)."""
    forms = CLASS_DETAIL.get(klass)
    declared = outcome.get("detail_lines")
    if detail is None:
        if forms or outcome.get("detail") or declared:
            findings.append(f"class {klass} needs a BE_MVP:DETAIL line")
        return
    if declared is not None:
        if not any(re.fullmatch(entry["regex"], detail.text)
                   for entry in declared):
            findings.append(f"line {detail.number}: {detail.text[:70]!r} is "
                            f"none of the variant's DETAIL lines")
        if not forms:
            return
    allowed = OPTIONAL_DETAIL if forms is None else forms
    if not allowed:
        findings.append(f"line {detail.number}: class {klass} takes no "
                        f"BE_MVP:DETAIL line")
        return
    named = [(form, DETAIL_FORMS[form].fullmatch(detail.text))
             for form in allowed]
    named = [(form, match) for form, match in named if match]
    if not named:
        findings.append(f"line {detail.number}: {detail.text!r} is not a "
                        f"{'/'.join(allowed)} DETAIL for class {klass}")
        return
    form, match = named[0]
    if form in ("henvcfg", "ticks"):
        if outcome.get("detail") == "domain":
            findings.append(f"line {detail.number}: the DETAIL names no "
                            f"domain")
        return
    domain, hart = int(match.group(1)), int(match.group(2))
    bindings = expect["domains"]
    wanted = outcome.get("domain", domain)
    if domain != wanted or domain >= len(bindings):
        findings.append(f"line {detail.number}: the DETAIL names domain "
                        f"{domain}, expected {wanted}")
    elif hart != outcome.get("hart", bindings[domain]["hart"]):
        findings.append(f"line {detail.number}: the DETAIL names hart {hart},"
                        f" not domain {domain}'s")
    elif form == "exit" and ("BE_MVP:10", domain) not in state.matched:
        findings.append(f"line {detail.number}: the DETAIL names domain "
                        f"{domain}, which never entered")
    if form == "exit":
        cause = int(match.group(3), 16)
        if not CAUSE_FITS.get(klass, lambda value: True)(cause):
            findings.append(f"line {detail.number}: cause 0x{cause:x} does "
                            f"not fit class {klass}")
        if "cause" in outcome and cause != outcome["cause"]:
            findings.append(f"line {detail.number}: cause 0x{cause:x}, "
                            f"expected 0x{outcome['cause']:x}")


def fallback_findings(capture, expect, state, tail, findings):
    """ring-full (Plan revision M0-A.3, as implemented): hart 0 drained
    nothing after both entries; each domain hart printed its own FAIL and
    DETAIL lines; the other hart's shutdown may cut the last line."""
    klass = expect["outcome"]["fail"]
    for ident in ("BE_MVP:11", "BE_MVP:12", "BE_MVP:13", "BE_MVP:14"):
        if state.started(ident):
            findings.append(f"hart 0 printed {ident} before the first FAIL")
    if not state.holds("BE_MVP:10"):
        findings.append("the fallback FAIL precedes both domains' entries")
    if any(capture.domains):
        findings.append("hart 0 printed a domain line before the fallback")
    fails, details = 1, 0
    domains = set()
    for position, line in enumerate(tail):
        last = capture.cut and position == len(tail) - 1
        if line.text == FAIL_PREFIX + klass:
            fails += 1
            continue
        match = DETAIL_FORMS["exit"].fullmatch(line.text) or \
            DETAIL_FORMS["domain"].fullmatch(line.text)
        if match:
            domain, hart = int(match.group(1)), int(match.group(2))
            bindings = expect["domains"]
            if domain >= len(bindings) or hart != bindings[domain]["hart"] \
                    or domain in domains:
                findings.append(f"line {line.number}: the fallback DETAIL "
                                f"does not name a domain hart once")
            domains.add(domain)
            details += 1
            if details > fails:
                findings.append(f"line {line.number}: a DETAIL before its "
                                f"FAIL")
            continue
        if last and (line.text.startswith(DETAIL_PREFIX + "domain=") or
                     (FAIL_PREFIX + klass).startswith(line.text)):
            capture.findings = [finding for finding in capture.findings
                                if "mid-line" not in finding]
            continue
        findings.append(f"line {line.number}: {line.text[:60]!r} is not a "
                        f"domain hart's fallback line")
    if fails > len(expect["domains"]) or details == 0:
        findings.append(f"{fails} fallback FAIL and {details} DETAIL lines")


def failure_findings(capture, expect, plan, stream, findings):
    """A declared failure: class, place, DETAIL, and nothing after."""
    outcome = expect["outcome"]
    klass = outcome["fail"]
    first = next((index for index, line in enumerate(stream)
                  if line.text.startswith(FAIL_PREFIX)), None)
    if first is None:
        state = walk(stream, plan)
        findings += state.findings
        findings.append(f"no BE_MVP:FAIL {klass} line")
        return state
    state = walk(stream[:first], plan)
    findings += state.findings
    fail = stream[first]
    if fail.text != FAIL_PREFIX + klass:
        findings.append(f"line {fail.number}: {fail.text!r}, expected "
                        f"{FAIL_PREFIX + klass!r}")
    after = outcome["after"]
    if after == "none":
        begun = [ident for ident in (R3_PRELUDE[0].split()[0],
                                     f"{CORE_PRELUDE} BOOT_VALIDATED")
                 if state.started(ident)]
        if begun:
            findings.append(f"the failure follows {begun[0]}, expected none")
    elif not state.holds(after):
        findings.append(f"the failure precedes the end of {after}")
    elif after not in RUN_GROUPS:
        later = plan.ids[plan.ids.index(after) + 1:]
        early = [ident for ident in later if state.started(ident)]
        if early:
            findings.append(f"the failure follows {early[-1]}, expected "
                            f"{after}")
    tail = stream[first + 1:]
    findings += cross_findings(state, capture, expect, fail.number)
    if outcome.get("fallback"):
        fallback_findings(capture, expect, state, tail, findings)
        return state
    detail = tail[0] if tail and tail[0].text.startswith(DETAIL_PREFIX) \
        else None
    detail_findings(klass, outcome, detail, expect, state, findings)
    rest = tail[1:] if detail else tail
    if rest and rest[0].text == SRST_RETURNED:
        rest = rest[1:]
    for line in rest:
        findings.append(f"line {line.number}: {line.text[:60]!r} after the "
                        f"failure")
    return state


def refusal(capture, expect, plan, stream, rule, boot_hart):
    """Findings against the declared refusal (Plan revision M0-A.2): a boot
    hart that is one of the run's domain harts is BE_MVP:02's STARTED hart
    and fails it as firmware; None when the start rule names no domain
    hart, so the capture is no refusal at all."""
    if rule is None or rule not in run_harts(expect) or \
            "shim_line" in expect["outcome"]:
        return None
    findings = []
    upto = next((index for index, line in enumerate(stream)
                 if line.text.startswith("BE_MVP:02 ")), len(stream))
    state = walk(stream[:upto], plan)
    findings += state.findings
    if not state.holds("BE_MVP:01") or state.started("BE_MVP:02"):
        findings.append("the refusal does not follow BE_MVP:01")
    rest = stream[upto:]
    if not rest:
        return findings + ["no BE_MVP:02 names the refused boot hart"]
    started = firmware_findings(rest[0], rule, False, findings, {})
    if started != rule:
        findings.append(f"BE_MVP:02 does not name the boot hart {rule}")
    rest = rest[1:]
    if rest and rest[0].text.startswith("BE_MVP:PROBE hsm ") and \
            any(key_of(entry["template"]) == ("BE_MVP:PROBE hsm", None)
                for entry in plan.prelude):
        rest = rest[1:]
    if not rest or rest[0].text != FAIL_PREFIX + "firmware":
        findings.append("BE_MVP:FAIL firmware does not follow BE_MVP:02")
    rest = rest[1:]
    if rest and rest[0].text == SRST_RETURNED:
        rest = rest[1:]
    findings += [f"line {line.number}: {line.text[:60]!r} after the refusal"
                 for line in rest]
    if any(capture.domains):
        findings.append("a domain line in a refused run")
    if boot_hart is not None and boot_hart != rule:
        findings.append(f"the loader's boot hart {boot_hart} is not the "
                        f"refused {rule}")
    return findings


PROBE_VALUES = re.compile(r"([a-z_0-9]+)=([^ ]+)")


def probe_stops(state, started):
    """The probe table's stop conditions on the probe lines' values; every
    value is recorded either way."""
    stops, values = [], {}
    for key, line in state.sequence:
        if not key[0].startswith("BE_MVP:PROBE "):
            continue
        fields = dict(PROBE_VALUES.findall(line.text))
        kind = key[0].split(" ", 1)[1]
        label = kind + ("-" + fields[next(iter(fields))]
                        if kind in ("gpf", "ipi", "order", "vmid") else
                        "-" + next(iter(fields)).split("_")[0]
                        if kind == "console-input" else "")
        values[label] = fields
        if kind == "hsm":
            for pair in fields["status"].split(","):
                hart, status = (int(value) for value in pair.split(":"))
                if status != (0 if hart == started else 1):
                    stops.append(f"stop 6: hart {hart} HSM status {status}")
        elif kind == "gpf" and int(fields["htval"], 16) != \
                int(fields["gpa"], 16) >> 2:
            stops.append(f"stop 6: {label} htval {fields['htval']} is not "
                         f"GPA >> 2")
        elif kind == "ipi" and fields["delivered"] != fields["sent"]:
            stops.append(f"stop 6: {label} delivered {fields['delivered']} "
                         f"of {fields['sent']}")
        elif kind == "order" and fields["mode"] == "fenced" and \
                fields["stale"] != "0":
            stops.append(f"stop 6: {fields['stale']} stale reads with "
                         f"fences")
        elif kind == "vmid" and fields["mode"] == "distinct" and \
                fields["after"] != fields["value_b"]:
            stops.append("stop 6: a stale translation under distinct VMIDs")
    return stops, values


# probe-console-input (M7-5; planning/mvp-m7-plan.md, D-12).
PROBE_INPUT_TAG = "BE_MVP:PROBE console-input"
PROBE_BYTES_LINE = re.compile(r"BE_MVP:PROBE console-input bytes=")
PROBE_BYTES = re.compile(rf"BE_MVP:PROBE console-input bytes=({DEC}) "
                         r"hex=((?:[0-9a-f]{2}){1,64})")


def input_probe_findings(state, received, mode):
    """probe-console-input's lines of received bytes RECEIVED against
    its window's line and its counts' line (the docstring's rule)."""
    probe = [line for key, line in state.sequence
             if key[0] == PROBE_INPUT_TAG]
    if len(probe) != 2:
        return [] if not received else ["lines of received bytes without "
                                        "the probe's window and counts"]
    window, counts = probe
    findings, data = [], bytearray()
    for index, line in enumerate(received):
        match = PROBE_BYTES.fullmatch(line.text)
        chunk = bytes.fromhex(match.group(2)) if match else b""
        data += chunk
        if not match or int(match.group(1)) != len(data) or (
                index + 1 < len(received) and len(chunk) != 64):
            findings.append(f"line {line.number}: {line.text[:48]!r} is not "
                            f"the count so far, {len(data)}, in lines of 64")
        if not window.number < line.number < counts.number:
            findings.append(f"line {line.number}: received bytes outside the "
                            f"probe's window")
    fields = {name: value for name, value in PROBE_VALUES.findall(
        counts.text)}
    numbers = {name: int(value) for name, value in fields.items()
               if name != "sha256"}
    if numbers.get("total") != len(data) or fields.get("sha256") != \
            hashlib.sha256(data).hexdigest()[:16]:
        findings.append(f"the counts' total and sha256 are not those of the "
                        f"{len(data)} bytes received")
    if numbers.get("nonzero_polls", 0) > numbers.get("polls", 0) or \
            numbers.get("max_per_poll", 0) > 256:
        findings.append("nonzero_polls above polls, or max_per_poll above "
                        "256")
    if mode == "direct" and (numbers.get("total"), numbers.get("errors")) \
            != (0, 0):
        findings.append("total or errors not 0 in a QEMU run, where nothing "
                        "is typed")
    return findings


def anchor_findings(capture, state, expect, parsed, measured, mgmts, facts):
    """M2's rules on a v3 capture (planning/mvp-m2-plan.md, "Scenarios and
    the harness", Markers): the pages against the report; the measurement
    against the checker's own, from MEASURED (the build outputs);
    the management log against the guests' calls and the declared
    requests; the transitions; the keyed digests, where the domains ran;
    the declared order; and a declared failure's required lines. Returns
    (findings, hart 0's parsed requests by domain)."""
    outcome = expect["outcome"]
    prefix = outcome.get("prefix_domains", [])
    findings = [] if parsed is None else pages_report_findings(
        state, expect, parsed)
    # M9's launch records and registers replace M2's one measurement
    # (planning/mvp-m9-plan.md, D-2, D-4): the log module judges them, and
    # the pinned measurement serves the retained M2 to RC3 fixtures alone.
    if "log" not in expect:
        findings += measurement_findings(capture, expect, measurement_value(
            expect, parsed, measured), facts)
    elif measured == PINNED_MEASUREMENT:
        findings.append("the pinned measurement serves the retained M2 to "
                        "RC3 fixtures alone, never a capture whose "
                        "expectation carries M9's log data")
    found, requests = mgmt_findings(capture, state, expect, mgmts, facts,
                                    prefix)
    findings += found + transition_findings(state, expect)
    if outcome.get("pass") or prefix:
        findings += request_findings(capture, expect, "fail" in outcome)
    findings += order_findings(capture, expect)
    if "fail" in outcome:
        findings += required_findings(capture, outcome)
    return findings, requests


# ------------------------------------------------- M7-4: console input
# planning/mvp-m7-plan.md, D-3, D-4, D-11, Q8, Q15: hart 0's input lines,
# BE_MVP:15 to :18, the session's typed keys (tests/session-typist.py's
# typed.txt), and the run nonce.
INPUT_TAGS = ("BE_MVP:15", "BE_MVP:16", "BE_MVP:17", "BE_MVP:18")
FOCUS_NONE = "BE_MVP:16 FOCUS none"
FOCUS_LINE = re.compile(r"BE_MVP:16 FOCUS (none|g([0-9]))")
DROP_REASONS = ("no-focus", "no-grant", "not-running", "ring-full",
                "bad-sequence", "before-armed")
DROP_LINE = re.compile(r"BE_MVP:17 INPUT_DROP (" + "|".join(DROP_REASONS) +
                       ")")
INPUT_SUMMARY = re.compile(
    rf"BE_MVP:18 INPUT read=({DEC}) g0=({DEC}):([0-9a-f]{{16}}) "
    rf"g1=({DEC}):([0-9a-f]{{16}}) dropped=(none|[a-z-]+:{DEC}"
    rf"(?:,[a-z-]+:{DEC})*)")
TYPED_ROW = re.compile(r"\+[0-9]+\.[0-9]{3} [0-9TZ:.-]+ step=([0-9]+) "
                       r"key=0x([0-9a-f]{2})")
INPUT_PREFIX = 0x7e
NONCE_TOKEN, NONCE_FORM = "NONCE", re.compile(r"[0-9a-f]{16}")
# The hostile guest's look-alikes (guest/mvp-init.c, /init-hostile).
FORGED_RUN, FORGED_PREFIX = "BE_MVP:13 RUN_COMPLETE forged", \
    "BE_MVP_G1: forged"
CHAN_LINE = re.compile(r"MVPINIT 12 CHAN (write|read) gpa=(0x[0-9a-f]+) "
                       rf"bytes=({DEC}) text=(.*)")


def input_model(data, grants):
    """src/mvp-input.c's routing of DATA, the bytes after the first poll's
    discards, with GRANTS (domain indices): the table (D-3) at the start of
    a line, after the prefix, and in a line; a selection of an ungranted
    domain a no-grant drop, input without a focus a no-focus drop, a bad
    sequence's byte a bad-sequence drop. (each domain's delivered bytes,
    {reason: dropped}, the focus selections, the reasons in first-drop
    order). Not modelled: not-running and ring-full, which no session
    provokes."""
    state, focus = "start", None
    delivered = [bytearray(), bytearray()]
    dropped = dict.fromkeys(DROP_REASONS, 0)
    selected, firsts = [], []

    def drop(reason):
        dropped[reason] += 1
        if reason not in firsts:
            firsts.append(reason)
    for byte in data:
        if state == "prefix":
            if byte == INPUT_PREFIX:
                state = "line"
            elif byte in (0x30, 0x31):
                state = "start"
                if byte - 0x30 in grants:
                    focus = byte - 0x30
                    selected.append(focus)
                else:
                    drop("no-grant")
                continue
            else:
                state = "start"
                drop("bad-sequence")
                continue
        elif state == "start" and byte == INPUT_PREFIX:
            state = "prefix"
            continue
        else:
            state = "start" if byte in (0x0d, 0x0a) else "line"
        if focus is None:
            drop("no-focus")
        else:
            delivered[focus].append(byte)
    return delivered, dropped, selected, firsts


def typed_keys(text, section, nonce, findings):
    """typed.txt's keys, each step's the bytes the expectation's step
    types with the nonce in place of NONCE, in the steps' order; or None
    with a finding."""
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        match = TYPED_ROW.fullmatch(line)
        if not match:
            findings.append(f"typed.txt line {number}: {line[:60]!r} is no "
                            f"key")
            return None
        rows.append((int(match.group(1)), int(match.group(2), 16)))
    keys, at = [], 0
    for step in section["steps"]:
        want = step["typed"].replace(NONCE_TOKEN, nonce).encode("ascii")
        got = bytes(byte for index, byte in rows[at:at + len(want)]
                    if index == step["index"])
        if got != want:
            findings.append(f"typed.txt: step {step['index']}'s keys are "
                            f"{got!r}, not the session's {want!r}")
            return None
        keys += want
        at += len(want)
    if at != len(rows):
        findings.append(f"typed.txt: {len(rows) - at} keys after the "
                        f"session's last step")
        return None
    return bytes(keys)


def nonce_periods(section, focus_lines):
    """Each focus period (the line its BE_MVP:16 opens it at, the next
    :16's, and its domain) in which the session types or expects the
    nonce."""
    periods, current = [], -1
    for step in section["steps"]:
        if step["kind"] == "focus":
            current += 1
            continue
        if NONCE_TOKEN in step["typed"] or (
                step["kind"] == "expect" and NONCE_TOKEN in step["value"]):
            if 0 <= current < len(focus_lines) and current not in [
                    period[3] for period in periods]:
                line, domain = focus_lines[current]
                end = focus_lines[current + 1][0].number \
                    if current + 1 < len(focus_lines) else 1 << 62
                periods.append((line.number, end, domain, current))
    return periods


def console_findings(data, capture, state, expect, events, options, facts):
    """An image with console input (M7-4; planning/mvp-m7-plan.md, D-11):
    BE_MVP:15 and :16 FOCUS none in the prelude (the plan's order), then
    the session's :16 FOCUS lines in its order, :17 only for the reasons it
    provokes (before-armed at most once), and :18 before :13 reconciled
    with typed.txt, the session, and the nonce: read the keys typed, at
    least delivered plus dropped; each domain's delivered count and the
    first 16 hex digits of its SHA-256 those of the bytes typed while it
    had the focus (input_model()), an ungranted domain's none; the drops
    the model's; the nonce in its focused domain's lines in each focus
    period that types it and in no other line; each channel read the text
    last written; and the secret, raw or in hex, nowhere in the
    capture."""
    findings = []
    section = expect["console_input"]
    grants = section["grants"]
    nonce, typed, session = (options.get(key) for key in (
        "nonce", "typed", "session"))
    if session is not None and hashlib.sha256(session).hexdigest() != \
            section["session"]["sha256"]:
        findings.append("the session file is not the one the expectation "
                        "was generated from")
    if nonce is None or not NONCE_FORM.fullmatch(nonce):
        findings.append("no run nonce (--nonce, 16 hex digits) for an image "
                        "with console input")
        nonce = None
    focus_lines, reasons = [], []
    for line in events:
        match = FOCUS_LINE.fullmatch(line.text)
        if match and match.group(2) is not None:
            focus_lines.append((line, int(match.group(2))))
        elif match:
            findings.append(f"line {line.number}: a second {FOCUS_NONE}")
        elif DROP_LINE.fullmatch(line.text):
            reasons.append(DROP_LINE.fullmatch(line.text).group(1))
        else:
            findings.append(f"line {line.number}: malformed input line "
                            f"{line.text[:60]!r}")
    focused = [domain for _, domain in focus_lines]
    if focused != section["focus"]:
        findings.append(f"the BE_MVP:16 FOCUS lines name "
                        f"{['g%d' % domain for domain in focused]}, not the "
                        f"session's {['g%d' % d for d in section['focus']]}")
    for reason in sorted(set(reasons)):
        if reasons.count(reason) > 1:
            findings.append(f"BE_MVP:17 INPUT_DROP {reason} "
                            f"{reasons.count(reason)} times; only a reason's "
                            f"first drop prints it")
    provoked = set(section["drops"]) | {"before-armed"}
    findings += [f"a BE_MVP:17 INPUT_DROP {reason}, which the session does "
                 f"not provoke" for reason in sorted(set(reasons) - provoked)]
    findings += [f"no BE_MVP:17 INPUT_DROP {reason}, which the session "
                 f"provokes" for reason in section["drops"]
                 if reason not in reasons]
    line = state.matched.get(("BE_MVP:18", None))
    summary = INPUT_SUMMARY.fullmatch(line.text) if line else None
    if summary is None:
        return findings + ["no well-formed BE_MVP:18 INPUT line"]
    read = int(summary.group(1))
    delivered = [(int(summary.group(2)), summary.group(3)),
                 (int(summary.group(4)), summary.group(5))]
    dropped = {} if summary.group(6) == "none" else {
        reason: int(count) for reason, count in (
            item.split(":") for item in summary.group(6).split(","))}
    facts.update(input_read=str(read), input_dropped=summary.group(6),
                 input_delivered=",".join(f"g{domain}={count}" for domain,
                                          (count, _) in enumerate(delivered)))
    if any(reason not in DROP_REASONS for reason in dropped):
        findings.append(f"BE_MVP:18 dropped={summary.group(6)} names an "
                        f"unknown reason")
    findings += [f"BE_MVP:18 dropped {reason}:{count}, which the session "
                 f"does not provoke" for reason, count in sorted(
                     dropped.items()) if reason not in provoked]
    if set(dropped) - {"before-armed"} != set(reasons) - {"before-armed"} or \
            ("before-armed" in dropped) != ("before-armed" in reasons):
        findings.append(f"BE_MVP:18 dropped={summary.group(6)} and the "
                        f"BE_MVP:17 reasons {reasons} differ")
    if read < sum(count for count, _ in delivered) + sum(dropped.values()):
        findings.append(f"BE_MVP:18 read={read} is less than the bytes "
                        f"delivered and dropped")
    for domain, (count, _) in enumerate(delivered):
        if domain not in grants and count:
            findings.append(f"BE_MVP:18 g{domain}={count}: bytes delivered to "
                            f"a domain without the console input grant")
    keys = typed_keys(typed, section, nonce, findings) \
        if typed is not None and nonce else None
    if typed is None:
        findings.append("no typed record (--typed) for an image with console "
                        "input")
    if keys is not None:
        armed = dropped.get("before-armed", 0)
        model, drops, selected, firsts = input_model(keys[armed:], grants)
        if armed:
            drops["before-armed"] = armed
            firsts.insert(0, "before-armed")
        if read != len(keys):
            findings.append(f"BE_MVP:18 read={read} is not the {len(keys)} "
                            f"keys typed")
        for domain, (count, digest) in enumerate(delivered):
            own = hashlib.sha256(bytes(model[domain])).hexdigest()[:16]
            if count != len(model[domain]):
                findings.append(f"BE_MVP:18 g{domain}={count}: the keys typed "
                                f"while g{domain} had the focus are "
                                f"{len(model[domain])}")
            if digest != own:
                findings.append(f"BE_MVP:18 g{domain}'s SHA-256 {digest} is "
                                f"not {own}, the keys typed while it had the "
                                f"focus")
        wanted = {reason: count for reason, count in drops.items() if count}
        if dropped != wanted:
            findings.append(f"BE_MVP:18 dropped={summary.group(6)}, the keys "
                            f"typed give {wanted or 'none'}")
        if selected != section["focus"] or [
                reason for reason in firsts if reason != "before-armed"] != \
                section["drops"]:
            findings.append(f"the keys typed select {selected} and drop "
                            f"{firsts}, not the session's")
    if nonce:
        periods = nonce_periods(section, focus_lines)
        seen = set()
        for line in capture.monitor:
            if nonce in line.text:
                findings.append(f"line {line.number}: hart 0's line holds the "
                                f"run nonce")
        for domain, lines in enumerate(capture.domains):
            for line in lines:
                if nonce not in line.text:
                    continue
                period = next((period for period in periods if
                               period[0] < line.number < period[1]), None)
                if period is None or period[2] != domain:
                    findings.append(f"line {line.number}: G{domain} prints "
                                    f"the run nonce outside a focus period "
                                    f"of its own that types it")
                else:
                    seen.add(period[3])
        findings += [f"focus period {period[3] + 1} (G{period[2]}): no line "
                     f"of its domain echoes the run nonce"
                     for period in periods if period[3] not in seen]
        if any(nonce in line for line in capture.loader):
            findings.append("the loader's lines hold the run nonce")
    written = []
    for domain, lines in enumerate(capture.domains):
        for line in lines:
            match = CHAN_LINE.fullmatch(line.text)
            if match:
                written.append((line.number, domain, match.group(1),
                                match.group(3), match.group(4)))
    for number, domain, kind, size, text in sorted(written):
        if kind != "read":
            continue
        last = [row for row in sorted(written) if row[2] == "write" and
                row[0] < number]
        if not last or last[-1][3:] != (size, text):
            findings.append(f"line {number}: G{domain} reads bytes={size} "
                            f"text={text!r} back, not the text last written")
    if "secret_hex" in expect:
        secret = bytes.fromhex(expect["secret_hex"])
        raw = data if isinstance(data, bytes) else data.encode(
            "utf-8", "replace")
        for form in (secret, secret.hex().encode(),
                     secret.hex().upper().encode()):
            if form in raw:
                findings.append("the capture holds the secret" +
                                ("" if form == secret else " in hex"))
    return findings


def forged_findings(capture, expect):
    """The hostile guest's look-alikes (M7-4; planning/mvp-m7-plan.md,
    D-4): each exactly once, as a line of the domain that printed it,
    behind that domain's prefix; the word forged in no other domain's line
    and in none of hart 0's."""
    findings = []
    forged = {int(domain): texts for domain, texts in
              expect.get("forged", {}).items()}
    for domain, texts in sorted(forged.items()):
        for text in texts:
            count = sum(line.text == text for line in capture.domains[domain])
            if count != 1:
                findings.append(f"the forged line {text!r} is {count} lines "
                                f"of G{domain}'s, not one")
    for line in capture.monitor:
        if "forged" in line.text:
            findings.append(f"line {line.number}: a forged line as hart 0's: "
                            f"{line.text[:60]!r}")
    for domain, lines in enumerate(capture.domains):
        if domain in forged:
            continue
        for line in lines:
            if "forged" in line.text:
                findings.append(f"line {line.number}: a forged line as "
                                f"G{domain}'s: {line.text[:60]!r}")
    return findings


def evaluate(data, expect, mode="direct", pins=None, report=None,
             **options):
    """(verdict, record) for one capture against one expectation; REPORT,
    the authority report's bytes, which a v2 expectation requires, and
    options["measured"], the measured domain's kernel and DTB as built
    (their bytes), which a v3 one's measurement requires."""
    pins = pins or read_pins()
    prefixes = [domain["prefix"] for domain in expect["domains"]]
    console = expect.get("console_input")
    capture = Capture(data, prefixes, {
        int(domain): texts for domain, texts in expect.get(
            "forged", {}).items()}, bool(console or "forged" in expect))
    findings, facts = [], {"mode": mode, "image": expect["image"]}
    if capture.cut:
        capture.findings.append("the capture ends mid-line")
    if capture.first is None:
        findings.append("no marker line")
    boot_hart, kexec_fdt = boot_facts(capture, mode, options, findings,
                                      facts)
    outcome = expect["outcome"]
    rule, stream = shim_findings(capture.monitor, expect, boot_hart,
                                 kexec_fdt, findings, facts)
    # M9's log lines leave hart 0's order, and their templates the walk's:
    # tests/log_module.py's judge() holds their places (log_judgement()).
    logged = "log" in expect
    walked = LOG.without_log(expect) if logged else expect
    plan = Plan(walked, any(line.text.startswith("BE_R3:")
                            for line in stream))
    logs = [line for line in stream if LOG.is_log_line(line.text)] \
        if logged else []
    # A v2 expectation's DENY lines leave hart 0's order: each is judged
    # against its domain's chain and its guest's report; a v3 one's MGMT
    # lines too, each against its guest's call.
    denies = [line for line in stream if line.text.startswith(DENY_PREFIX)] \
        if "denials" in expect else []
    mgmts = [line for line in stream if line.text.startswith(MGMT_PREFIX)] \
        if "mgmt" in expect else []
    # M7-4's input lines: an image with console input has :15, :16 FOCUS
    # none, and :18 in hart 0's order, and each :16 focus and :17 drop
    # line outside it, judged against the session; any other image, none.
    inputs = [line for line in stream if key_of(line.text)[0] in INPUT_TAGS]
    armed = next((line for line in inputs if line.text == FOCUS_NONE), None)
    events = [line for line in inputs if line is not armed and
              line.text.startswith(("BE_MVP:16 ", "BE_MVP:17 "))] \
        if console else inputs
    if not console:
        findings += [f"line {line.number}: {line.text[:40]!r}, an input "
                     f"line, where the image declares no console input"
                     for line in events]
    # probe-console-input's lines of received bytes leave it too.
    received = [line for line in stream if PROBE_BYTES_LINE.match(line.text)]\
        if any(entry["template"].startswith(PROBE_INPUT_TAG) for entry in
               expect.get("probe_lines", ())) else []
    stream = [line for line in stream
              if line not in denies + mgmts + events + received + logs]
    findings += guest_id_findings(capture)
    stops, values, state = [], {}, None
    log_record, declared, exported = None, [], None
    refused = refusal(capture, expect, plan, stream, rule, boot_hart) \
        if "probe" in outcome or outcome.get("after") != "none" else None
    if refused == [] and not capture.findings and not findings:
        verdict = "REFUSED"
    else:
        if refused is not None:
            findings.append(f"the boot hart {rule} is a domain hart, but the "
                            f"run is no declared refusal: {refused[:2]}")
        if "fail" in outcome:
            state = failure_findings(capture, walked, plan, stream,
                                     findings)
        else:
            state = walk(stream, plan)
            findings += state.findings
            if not state.broken and not state.complete():
                findings.append(f"the sequence stops before "
                                f"{state.heads()[0]['template'][:70]!r}")
            findings += cross_findings(state, capture, expect)
        firmware = state.matched.get(("BE_MVP:02", None))
        started = firmware_findings(firmware, rule, "shim_line" in outcome,
                                    findings, facts) if firmware else None
        findings += monitor_value_findings(state, pins)
        found, waited = ping_findings(state, expect, mgmts)
        findings += found
        parsed = None
        if "report" in expect:
            found, parsed = report_findings(expect, report)
            findings += found
            if parsed is not None and "pages" not in expect:
                findings += boot_report_findings(state, parsed)
        findings += absent_findings(capture, outcome)
        # beryllium-cheri: a CHERI variant's faulting domain's last lines.
        findings += cheri_findings(capture, outcome, pins, expect)
        log, requests = {}, {}
        # A v3 failure whose domains ran (no-grant-check) has its denials,
        # a prefix of the declared ones for each of PREFIX.
        prefix = outcome.get("prefix_domains", [])
        if "denials" in expect and (outcome.get("pass") or prefix):
            found, log = denial_findings(capture, state, expect, denies,
                                         facts, prefix)
            findings += found
            # A shell's channel is its session's (console_findings()).
            if outcome.get("pass") and "requests" not in expect and \
                    not console:
                findings += channel_findings(capture, expect)
        else:
            findings += [f"line {line.number}: a DENY line, where the image "
                         f"declares no denial" for line in denies]
        if "mgmt" in expect:
            found, requests = anchor_findings(capture, state, expect, parsed,
                                              options.get("measured"), mgmts,
                                              facts)
            findings += found
        if console and outcome.get("pass"):
            findings += console_findings(data, capture, state, expect,
                                         events, options, facts)
        if "forged" in expect:
            findings += forged_findings(capture, expect)
        if logged:
            found, declared, log_record, exported = log_judgement(
                capture, expect, parsed, options)
            findings += found
        if outcome.get("pass"):
            budget = budget_of(state, LAYOUT["RUN_BUDGET"])
            shutdowns = shutdown_findings(state, capture, expect, budget,
                                          findings, facts,
                                          deny_counts(denies), len(mgmts))
            # The run's nonce in place of a shell's <nonce>, when known.
            nonce = options.get("nonce")
            own = dict(expect, domain_placeholders=dict(
                expect.get("domain_placeholders") or {},
                **{"<nonce>": re.escape(nonce)})) if console and nonce and \
                NONCE_FORM.fullmatch(nonce) else expect
            for domain, lines in enumerate(capture.domains):
                findings += domain_findings(domain, lines, own, pins,
                                            outcome.get("time_above_zero"))
            count = alternations(capture.order)
            facts["alternations"] = str(count)
            floor = expect["concurrency"]["alternations"]
            if count < floor:
                findings.append(f"{count} alternations between the domains' "
                                f"lines, fewer than K = {floor} (Q5)")
            facts["costs"] = costs(state, shutdowns, log, requests, waited)
        elif prefix:
            # The server may answer what the requester asked before its
            # end; request_findings judges each answer.
            server = expect["requests"]["server"]
            for domain, lines in enumerate(capture.domains):
                findings += domain_findings(
                    domain, lines, expect, pins, False, domain in prefix,
                    [r"MVPINIT 09 RESPONSE n=[0-9]+ digest=[0-9a-f]{64}"]
                    if domain == server else ())
        elif "probe" in outcome:
            if any(capture.domains):
                findings.append("a domain line in a probe capture")
            findings += input_probe_findings(state, received, mode)
            stops, values = probe_stops(state, started)
        findings = capture.findings + findings
        verdict = "FAIL" if findings else "STOP" if stops else "PASS"
    if verdict == "REFUSED":
        findings = []
    last = capture.monitor[-1].text if capture.monitor else ""
    terminal = "fail-marker" if any(
        line.text.startswith((FAIL_PREFIX, "BE_K3_B3: FAIL"))
        for line in capture.monitor) else "shutdown-requested" \
        if last.startswith("BE_MVP:14 ") else "none"
    out = {
        "result": verdict, "boot_marker": "PASS" if verdict == "PASS"
        else "FAIL", "terminal": terminal, "findings": findings,
        "stops": stops, "probe_values": values,
        "fields": {key: value for key, value in facts.items()
                   if key != "costs"},
        "costs": facts.get("costs", {}),
        "markers": [line.text for line in capture.monitor],
        "lines": {f"g{domain}": len(lines)
                  for domain, lines in enumerate(capture.domains)},
    }
    # M9's: the log's record, the self-report findings the run declares
    # (self-report-flip's one), and the export main() writes (--log-json).
    if logged and verdict != "REFUSED":
        out.update(log=log_record, log_declared=declared,
                   log_export=exported)
    return verdict, out


def log_judgement(capture, expect, report, options):
    """M9's log (planning/mvp-m9-plan.md, D-4; tests/log_module.py's
    judge()): (findings, the self-report findings the run declares, the
    record, the export). The reference is --reference, or the build's
    references/TOOLCHAIN/IMAGE.json; the boot image --image, or the
    build's for the image (log_module.default_paths()); the canonical
    inputs the scenario file, the policy tool's core identity, the grants,
    and the report's identities (log_module.scenario_inputs()). The
    self-test gives its own (reference_data, log_inputs), or its internal
    retained_era flag for a pinned saved-capture set."""
    findings, toolchain = [], options.get("toolchain")
    retained = bool(options.get("retained_era"))
    root = pathlib.Path(options.get("build_root") or DEFAULT_BUILD)
    reference_path = boot_path = None
    if toolchain:
        reference_path, boot_path = LOG.default_paths(root, toolchain,
                                                      expect)
    data, reference = options.get("reference_data"), None
    path = options.get("reference") or reference_path
    if data is None and path is not None:
        try:
            data = pathlib.Path(path).read_bytes()
        except OSError as error:
            findings.append(f"log: the reference cannot be read: {error}")
    if data is not None:
        try:
            reference = LOG.Reference(data)
        except LOG.Refused as error:
            findings.append(f"log: the reference is refused: {error}")
    inputs = None if retained else options.get("log_inputs")
    if not retained and inputs is None:
        boot = options.get("image_data")
        if boot is None and boot_path is not None and boot_path.is_file():
            boot = boot_path.read_bytes()
        try:
            inputs = LOG.scenario_inputs(expect, report, boot, root, LAYOUT)
        except (LOG.Refused, OSError, KeyError, TypeError,
                ValueError) as error:
            findings.append(f"log: the canonical inputs cannot be read: "
                            f"{error}")
            inputs = LOG.Inputs(boot=boot)
    if retained and options.get("reference_data") is None:
        findings.append("log: retained-era mode needs its pinned reference")
    found, declared, record, exported = LOG.judge(
        capture.monitor, expect, reference, inputs, toolchain, retained)
    return findings + found, declared, record, exported


# ---------------------------------------------------------------- fixtures
# Fedora's shutdown before a kexec (B7's capture checker's noise lines).
FEDORA_NOISE = (
    "\x1b[0;1;39m         Stopping\x1b[0m session-3.scope - Session 3 of "
    "User fedora...",
    "[  OK  ] Finished systemd-kexec.service - Reboot via kexec.",
    "[ 4207.902114] systemd-shutdown[1]: Rebooting with kexec.",
)
BOARD_IMAGE_BYTES = 0x223000
# The first COM260 scenario run (GCC, 20261025T022152Z), CRs removed: it
# stopped the board campaign on the alternation floor alone (stop
# condition 6), hart 0's drain then taking each ring to empty in turn
# (Plan revision M0-C). The checker must go on rejecting it for that.
BOARD_STOP6 = "k3-two-guests-gcc-stop6-alternations"
BOARD_STOP6_FDT = 0x108400000
BOARD_STOP6_FINDINGS = ["5 alternations between the domains' lines, fewer "
                        "than K = 8 (Q5)"]
# The guest pins M0's twelve fixtures were captured with (guest/pins.txt at
# the M0 result, b2669725, verbatim): their BE_MVP:04 and :06 carry M0's
# kernel, which M1's fragment and init then changed (planning/mvp-m1-plan.md,
# Guest software); and M1's five, M1's (guest/pins.txt at the M1 result,
# ff84533c, verbatim), whose kernel M2's module option, roles, and module
# then changed (planning/mvp-m2-plan.md, Guest software). Every other
# fixture was captured with the current pins; QEMU's uboot fixture (below)
# holds the markers of M0's hart-6 capture, so M0's pins.
M0_PINS = FIXTURES / "m0-guest-pins.txt"
M0_PINS_SHA256 = \
    "094df1904a1fc6f746d41230137748dd72be08e7e71ec5b4db2b69cc516ca0c8"
BOARD_UBOOT = "board-uboot-two-guests-gcc"
QEMU_UBOOT = "qemu-uboot-two-guests-clang-hart6"
M0_FIXTURES = ("qemu-two-guests-gcc", "qemu-two-guests-clang-hart6",
               "qemu-shim-rule-gcc", "qemu-ring-full-gcc",
               "qemu-ring-full-clang", "qemu-rdcycle-clang",
               "qemu-payload-gcc", "qemu-plic-gcc-refused",
               "qemu-probe-platform-gcc", "qemu-probe-vmid-distinct-gcc",
               "qemu-probe-vmid-shared-gcc", BOARD_STOP6, QEMU_UBOOT)
M1_PINS = FIXTURES / "m1-guest-pins.txt"
M1_PINS_SHA256 = \
    "229146c1f0a8838c65ae23e35a024320edc16e747835b82dd209d061d0da8702"
# And M2's (guest/pins.txt at the M2 result, 18d552bc, verbatim; the same
# bytes through M7-3): the kernel M2's, M5's, and M6's fixtures were
# captured with, which M7-2's userland then changed (planning/
# mvp-m7-plan.md, D-9). Their measured kernel is not retained, so an anchor
# fixture among them is measured as its pinned expectation records it
# (PINNED_MEASUREMENT), the generator's value over the build outputs of its
# time.
M2_PINS = FIXTURES / "m2-guest-pins.txt"
M2_PINS_SHA256 = \
    "d1be8ad50ab02bde3b7696be369aa40554db76421d9196b1d3dd4dee02751366"
PINNED_MEASUREMENT = "pinned"
# The first te-poc captures, from M1-4's init that made its denied
# accesses as pid 1, which stopped the work package (stop condition 6,
# Plan revision M1-A): Linux printed "unhandled signal" for each handled
# fault. The checker must go on rejecting it for that alone.
PID1_STOP6 = "qemu-te-poc-gcc-stop6-pid1"
# The first M1 board campaign's no-inject run (GCC, 20261027T094024Z), CRs
# removed, which stopped the campaign (stop condition 6, Plan revision
# M1-B): both domain harts' 2^24-tick waits for hart 0's ACK ran out while
# hart 0's drain was bound by the console, so each printed its own FAIL and
# DETAIL lines among hart 0's guest lines, and a domain hart's SRST ended
# the run before hart 0 took either FAIL record. The checker must go on
# rejecting it for exactly these findings: the first FAIL without its
# DETAIL, the second FAIL and both DETAIL lines, and the guest lines after
# the first FAIL.
BOARD_NO_INJECT = "k3-no-inject-gcc-stop6-fallback"
BOARD_NO_INJECT_FDT = 0x108400000
BOARD_NO_INJECT_FINDINGS = [
    "line 315: G0 line after the failure",
    "line 312: G1 line after the failure",
    "class guest-page-fault needs a BE_MVP:DETAIL line",
    "line 313: 'BE_MVP:FAIL guest-page-fault' after the failure",
    "line 314: 'BE_MVP:DETAIL domain=0 hart=1 cause=0x15 pc=0x112bc "
    "tval=0x3' after the failure",
    "line 316: 'BE_MVP:DETAIL domain=1 hart=2 cause=0x17 pc=0x112c8 "
    "tval=0x3' after the failure",
]
M1_FIXTURES = ("qemu-te-poc-gcc", "qemu-reader-write-gcc",
               "qemu-no-inject-gcc", PID1_STOP6, BOARD_NO_INJECT)
# M2's (planning/mvp-m2-plan.md, "Scenarios and the harness"): anchor's
# QEMU captures, from tests/run-qemu.sh, each with the current pins: the
# scenario's, and its four runtime negatives', each failing as declared.
ANCHOR_FIXTURES = {"anchor": "qemu-anchor-gcc",
                   "secret-shared": "qemu-secret-shared-gcc",
                   "response-writable": "qemu-response-writable-gcc",
                   "wrong-measurement": "qemu-wrong-measurement-gcc",
                   "no-grant-check": "qemu-no-grant-check-gcc"}
# The first M2 board campaign's first anchor run (GCC, 20261028T023339Z),
# CRs removed, which stopped the campaign (stop condition 6, Plan revision
# M2-A): the protected domain made its first management call 0xa5f3d ticks
# (28.3 ms at 24 MHz) after the barrier and waited 0x149e641 ticks (900.8
# ms) in HS for hart 0's answer, hart 0 draining both guests' boot lines at
# 115200 baud, while hart 0 sent that domain's PING when it took its first
# console line, at 0x23598b ticks (96.5 ms); hart 2 served the PING in the
# wait, and its PONG showed spv=0. Every other rule held. Under Plan
# revision M2-A.1 it passes, with the probe among its costs (and the counts
# the board's check recorded); moved out of that wait, or without that
# request's line, it fails. BOARD_PING_WAIT_SPAN is that wait, [ticks,
# ticks + service].
BOARD_PING_WAIT = "k3-anchor-gcc-m2a-ping-in-wait"
BOARD_PING_WAIT_FDT = 0x108400000
BOARD_PING_WAIT_SPAN = (0xa5f3d, 0xa5f3d + 0x149e641)
BOARD_PING_WAIT_COSTS = {"g0_ping_to_receipt_ticks": 81,
                         "g1_ping_to_receipt_ticks": 54,
                         "g1_ping_in_mgmt_wait": 1, "g1_ping_mgmt_seq": 1}
BOARD_PING_WAIT_COUNTS = {"exits_g0": "248", "exits_g1": "132",
                          "denials_g0": "4", "denials_g1": "1",
                          "mgmt_g0": "13", "mgmt_g1": "2", "records": "174"}
# The board's own captures, judged as the board recorded them (through
# Linux's kexec), never re-hosted behind B7's handoff.
BOARD_CAPTURES = (BOARD_STOP6, BOARD_NO_INJECT, BOARD_PING_WAIT)
# M6's (planning/mvp-m6-plan.md, D-3): QEMU captures of the MVP core
# profile's images, from tests/run-qemu.sh, with the current pins, each
# showing the MVP's prelude, BE_MVP:00 BOOT_VALIDATED and CONFIG_SEALED:
# one per board image kind of the board-tool dry run (GCC's, k3-like but
# te-poc's on rva23; each boot on hart 0, as a board's is, but anchor's
# variants', as M2's were), and the scenario's refused boot (Clang's, on
# rva23, from hart 2).
M6_FIXTURES = {
    "two-guests": "qemu-two-guests-gcc-m6",
    "payload": "qemu-payload-gcc-m6",
    "probe-platform": "qemu-probe-platform-gcc-m6",
    "probe-vmid-distinct": "qemu-probe-vmid-distinct-gcc-m6",
    "probe-vmid-shared": "qemu-probe-vmid-shared-gcc-m6",
    "refused": "qemu-rva23-clang-m6-refused",
    "te-poc": "qemu-te-poc-gcc-m6",
    "reader-write": "qemu-reader-write-gcc-m6",
    "no-inject": "qemu-no-inject-gcc-m6",
    "anchor": "qemu-anchor-gcc-m6",
    "wrong-measurement": "qemu-wrong-measurement-gcc-m6",
    "no-grant-check": "qemu-no-grant-check-gcc-m6"}
# The te-poc and anchor expectations and authority reports M1's and M2's
# fixtures are judged with: tools/gen-scenario.py's at 366c8af4, verbatim
# (SCENARIO/expect/*.json and SCENARIO/authority-report.json). M6 removed
# the scenarios' kexec FDT object (planning/mvp-m6-plan.md, Q3), which
# changed their configuration identities and anchor's measurement; every
# other fixture is judged against the current expectations.
PRE_M6 = FIXTURES / "pre-m6"
PRE_M6_SHA256 = \
    "3bfcfc5cfb9573b008c974e5b776257ab8d3a5f74e588246e24a91b184f42cd9"
# M7's (planning/mvp-m7-plan.md, D-10): QEMU captures of the images with
# SBI implementation version 5 (6 with the management extension), from
# tests/run-qemu.sh, with the current pins: one per kind of M6's, each made
# as M6's was (GCC's, k3-like but te-poc's on rva23; each boot on hart 0
# but wrong-measurement's, and the refused one Clang's on rva23 from a
# domain hart); and M7-5's probe-console-input (D-12), GCC's on k3-like
# from hart 0, with nothing typed.
M7_FIXTURES = {
    "two-guests": "qemu-two-guests-gcc-m7",
    "payload": "qemu-payload-gcc-m7",
    "probe-platform": "qemu-probe-platform-gcc-m7",
    "probe-vmid-distinct": "qemu-probe-vmid-distinct-gcc-m7",
    "probe-vmid-shared": "qemu-probe-vmid-shared-gcc-m7",
    "probe-console-input": "qemu-probe-console-input-gcc-m7",
    "refused": "qemu-rva23-clang-m7-refused",
    "te-poc": "qemu-te-poc-gcc-m7",
    "reader-write": "qemu-reader-write-gcc-m7",
    "no-inject": "qemu-no-inject-gcc-m7",
    "anchor": "qemu-anchor-gcc-m7",
    "wrong-measurement": "qemu-wrong-measurement-gcc-m7",
    "no-grant-check": "qemu-no-grant-check-gcc-m7"}
# Every scenario's expectations (and te-poc's and anchor's authority
# reports) M0's, M5's, and M6's fixtures are judged with:
# tools/gen-scenario.py's at ae3e9537, verbatim (SCENARIO/expect/*.json and
# SCENARIO/authority-report.json). M7 raised the SBI implementation version
# each guest's kernel line names (planning/mvp-m7-plan.md, D-10) from 3 to
# 5 and, with the management extension, from 4 to 6; M1's and M2's
# fixtures keep PRE_M6's, and M7's are judged against the current ones.
# M7-4's fixtures (planning/mvp-m7-plan.md, D-4 and D-11), QEMU runs of
# the merged tree with the current pins, each judged against the current
# expectations: the hostile guest's capture (tests/run-qemu.sh), and each
# console variant's typed session (tests/session-typist.py, a hart-0 boot)
# with its keys (NAME.typed.txt) and nonce (NAME.nonce.txt), and the
# scenario's session file it was typed from.
HOSTILE_FIXTURE = "qemu-hostile-gcc-m7"
SESSION_FIXTURES = {"two-guests-shell": "qemu-two-guests-shell-gcc-m7",
                    "te-poc-shell": "qemu-te-poc-shell-gcc-m7",
                    "anchor-shell": "qemu-anchor-shell-gcc-m7"}
M74_FIXTURES = (HOSTILE_FIXTURE,) + tuple(SESSION_FIXTURES.values())
PRE_M7 = FIXTURES / "pre-m7"
PRE_M7_SHA256 = \
    "ee4c0618af087a32047339a38a42f222f4e1b906f7976cf1cd07b888fea0efeb"
# M9's (planning/mvp-m9-plan.md, D-2 to D-4): M7's set made again from
# tests/run-qemu.sh and tests/session-typist.py on M9-3's images, each
# capture carrying its image's measurement log, and self-report-flip's
# beside them; each judged against the pinned pre-M11 era set. Synthetic
# stand-ins rendered from the current references keep recomputation
# coverage. M7's and M7-4's fixtures keep
# the expectations of their time: every scenario's and te-poc's and
# anchor's authority reports at ca48456f, verbatim (PRE_M9), before M9
# added the log and dropped the report's measurement.
M9_FIXTURES = {
    "two-guests": "qemu-two-guests-gcc-m9",
    "payload": "qemu-payload-gcc-m9",
    "probe-platform": "qemu-probe-platform-gcc-m9",
    "probe-vmid-distinct": "qemu-probe-vmid-distinct-gcc-m9",
    "probe-vmid-shared": "qemu-probe-vmid-shared-gcc-m9",
    "probe-console-input": "qemu-probe-console-input-gcc-m9",
    "refused": "qemu-rva23-clang-m9-refused",
    "te-poc": "qemu-te-poc-gcc-m9",
    "reader-write": "qemu-reader-write-gcc-m9",
    "no-inject": "qemu-no-inject-gcc-m9",
    "anchor": "qemu-anchor-gcc-m9",
    "wrong-measurement": "qemu-wrong-measurement-gcc-m9",
    "no-grant-check": "qemu-no-grant-check-gcc-m9",
    "hostile": "qemu-hostile-gcc-m9",
    "self-report-flip": "qemu-self-report-flip-gcc-m9"}
M9_SESSION_FIXTURES = {"two-guests-shell": "qemu-two-guests-shell-gcc-m9",
                       "te-poc-shell": "qemu-te-poc-shell-gcc-m9",
                       "anchor-shell": "qemu-anchor-shell-gcc-m9"}
PRE_M9 = FIXTURES / "pre-m9"
PRE_M9_SHA256 = \
    "19d0cbd43424333e363a53cac52bf443a419e100a4086adb6adf4a7faec9586f"
PRE_M11 = FIXTURES / "pre-m11"
PRE_M11_SHA256 = \
    "dd6e8c1072d1c65466858ff6e29c3854af3f2532eb302c5644d551e2c21a388a"
# The uboot form's U-Boot lines (uboot_lines), a fixed template until the
# characterization (M5-6a) and the rehearsal (M5-3) record a boot from the
# Beryllium partition: the board's after B6's U-Boot run
# (bringup/k3-b6/results/20261008-com260-uboot/20261008T113140Z: its
# excerpt's lines, and its check.txt's banner and watchdog lines), with
# B3's env_k3.txt lines (bringup/k3-b3/results/20261006-com260/
# 20261006T193201Z) and be_ld's load and md5sum line (this BSP's crc32
# prints nothing) where loady's YMODEM lines were; QEMU's after B3's QEMU
# run of the pinned upstream v2022.10 (bringup/k3-b3/README.md: 8 GiB, the
# control device tree in place at 0xff73a250), with its crc32 line (it has
# no md5sum) and QEMU's OpenSBI handing U-Boot its kernel address. Each
# device tree's blob A, start F, and last byte E.
UBOOT_BOARD_FDT = (0x2fbe8aa50, 0x2fbd6b000, 0x2fbd7d2ef)
UBOOT_QEMU_FDT = (0xff73a250, 0xff73a250, 0xff73edd1)
UBOOT_QEMU_ENTRY = 0x80200000
# The uboot fixtures' sources and images: release candidate 1's first
# COM260 run (GCC two-guests, the current guest pins; its excerpt Linux's
# kexec handoff and then the run, CRs removed), with its board image (RC1's
# image_sha256=80ac8e33, as these sources build it), and M0's QEMU run from
# hart 6, with the Clang two-guests QEMU-only image these sources build;
# each image's size, CRC-32, and MD5.
RC1_RUN = MVP_DIR / "results" / "20261029-com260-rc" / "20261029T171402Z" / \
    "handoff-excerpt.log"
RC1_RUN_SHA256 = \
    "97589fb8a3e11c3a1d880805538086d94f8052d2dcb445617b45679e817d5257"
UBOOT_FIXTURES = {
    BOARD_UBOOT: (RC1_RUN, False, 0x277000, 0x043fe676,
                  "c3f201e9319ea88b8035b61231c701ec"),
    QEMU_UBOOT: ("qemu-two-guests-clang-hart6", True, 0x277000, 0xde60ac10,
                 "9c454eb9a7455a5cf18bee3fdc96b836")}
# The board fixture's facts, as U-Boot's lines give them.
BOARD_UBOOT_FACTS = {
    "launcher_mode": "uboot", "load_bytes": "2584576",
    "load_digest_kind": "md5",
    "load_digest": "c3f201e9319ea88b8035b61231c701ec",
    "moving_from": "0x140000000",
    "moving_to": "0x108000000", "moving_end": "0x108277000",
    "fdt_blob": "0x2fbe8aa50", "fdt_loaded": "0x2fbd6b000",
    "fdt_end": "0x2fbd7d2ef", "fdt_in_place": "false",
    "spl_banner": "U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)",
    "uboot_banner": "U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), "
                    "Build: jenkins-BSP-build-bsp-deb-395",
    "uboot_watchdog": "WDT:   Started watchdog@d4014000 with servicing "
                      "(60s timeout)"}


def m0_pins():
    """M0's guest pins, as M0's fixtures were captured with them."""
    if hashlib.sha256(M0_PINS.read_bytes()).hexdigest() != M0_PINS_SHA256:
        raise ValueError(f"{M0_PINS} is not M0's guest pins")
    return read_pins(M0_PINS)


def m1_pins():
    """M1's guest pins, as M1's fixtures were captured with them."""
    if hashlib.sha256(M1_PINS.read_bytes()).hexdigest() != M1_PINS_SHA256:
        raise ValueError(f"{M1_PINS} is not M1's guest pins")
    return read_pins(M1_PINS)


def m2_pins():
    """M2's guest pins, as M2's, M5's, and M6's fixtures were captured with
    them."""
    if hashlib.sha256(M2_PINS.read_bytes()).hexdigest() != M2_PINS_SHA256:
        raise ValueError(f"{M2_PINS} is not M2's guest pins")
    return read_pins(M2_PINS)


def m2_fixture(name):
    """Whether the fixture NAME was captured with M2's guest pins."""
    return name in ANCHOR_FIXTURES.values() or name in M6_FIXTURES.values() \
        or name in (BOARD_PING_WAIT, BOARD_UBOOT)


def pre_m6():
    """({image: expectation}, {SHA-256: report}) of PRE_M6, which must be
    the files pinned: each file's SHA-256 and path, as sha256sum lists
    them, hash to PRE_M6_SHA256."""
    listing = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
        f"{path.relative_to(PRE_M6)}\n"
        for path in sorted(PRE_M6.rglob("*.json")))
    if hashlib.sha256(listing.encode()).hexdigest() != PRE_M6_SHA256:
        raise ValueError(f"{PRE_M6} is not the expectations at 366c8af4")
    expects, reports = {}, {}
    for scenario in ("te-poc", "anchor"):
        expects.update(load_expects(PRE_M6 / scenario / "expect"))
        data = (PRE_M6 / scenario / "authority-report.json").read_bytes()
        reports[hashlib.sha256(data).hexdigest()] = data
    return expects, reports


def pre_m7():
    """({image: expectation}, {SHA-256: report}) of PRE_M7, which must be
    the files pinned: each file's SHA-256 and path, as sha256sum lists
    them, hash to PRE_M7_SHA256."""
    listing = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
        f"{path.relative_to(PRE_M7)}\n"
        for path in sorted(PRE_M7.rglob("*.json")))
    if hashlib.sha256(listing.encode()).hexdigest() != PRE_M7_SHA256:
        raise ValueError(f"{PRE_M7} is not the expectations at ae3e9537")
    expects, reports = {}, {}
    for scenario in ("two-guests", "te-poc", "anchor"):
        expects.update(load_expects(PRE_M7 / scenario / "expect"))
        if scenario == "two-guests":
            continue
        data = (PRE_M7 / scenario / "authority-report.json").read_bytes()
        reports[hashlib.sha256(data).hexdigest()] = data
    return expects, reports


def pre_m9():
    """({image: expectation}, {SHA-256: report}) of PRE_M9, which must be
    the files pinned: each file's SHA-256 and path, as sha256sum lists
    them, hash to PRE_M9_SHA256."""
    listing = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
        f"{path.relative_to(PRE_M9)}\n"
        for path in sorted(PRE_M9.rglob("*.json")))
    if hashlib.sha256(listing.encode()).hexdigest() != PRE_M9_SHA256:
        raise ValueError(f"{PRE_M9} is not the expectations at ca48456f")
    expects, reports = {}, {}
    for scenario in ("two-guests", "te-poc", "anchor"):
        expects.update(load_expects(PRE_M9 / scenario / "expect"))
        if scenario == "two-guests":
            continue
        data = (PRE_M9 / scenario / "authority-report.json").read_bytes()
        reports[hashlib.sha256(data).hexdigest()] = data
    return expects, reports


def pre_m11():
    """The lock-commit expectations, reports, and references for M9's
    retained captures, pinned as one set by its listing SHA-256."""
    listing = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  "
        f"{path.relative_to(PRE_M11)}\n"
        for path in sorted(PRE_M11.rglob("*.json")))
    if hashlib.sha256(listing.encode()).hexdigest() != PRE_M11_SHA256:
        raise ValueError(f"{PRE_M11} is not the pinned pre-M11 era set")
    expects, reports = {}, {}
    for scenario in ("two-guests", "te-poc", "anchor"):
        expects.update(load_expects(PRE_M11 / scenario / "expect"))
        if scenario == "two-guests":
            continue
        data = (PRE_M11 / scenario / "authority-report.json").read_bytes()
        reports[hashlib.sha256(data).hexdigest()] = data
    references = {
        path.stem: path.read_bytes()
        for path in sorted((PRE_M11 / "references" / "gcc").glob("*.json"))
    }
    return expects, reports, references


def load_expects(directory):
    return {path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(pathlib.Path(directory).glob("*.json"))}


def fixture(name):
    return (FIXTURES / f"{name}.log").read_text(encoding="ascii")


def b7_handoff():
    """Fedora's kexec handoff as B7 recorded it on the COM260, pinned."""
    data = B7_HANDOFF.read_bytes()
    if hashlib.sha256(data).hexdigest() != B7_HANDOFF_SHA256:
        raise ValueError(f"{B7_HANDOFF} differs from B7's accepted record")
    return data.decode("ascii").split("\n")[:11]


def kexec_form(text, hart=0, image_bytes=BOARD_IMAGE_BYTES):
    """A direct-boot capture re-hosted behind B7's recorded handoff: the
    handoff's hart and FDT slot, the markers from the capture, CRLF."""
    fdt = STAGING + align_up(image_bytes, FDT_ALIGN)
    handoff = [line.replace("FDT image at 108200000", f"FDT image at {fdt:x}")
               .replace("from hart id 0", f"from hart id {hart:x}")
               for line in b7_handoff()]
    lines = text.split("\n")
    first = next(index for index, line in enumerate(lines)
                 if line.startswith((RULE_TAG, SHIM_TAG)))
    markers = [re.sub(r"(?<= fdt=0x)[0-9a-f]{16}", f"{fdt:016x}", line)
               if line.startswith(SHIM_TAG) else line
               for line in lines[first:]]
    return "\r\n".join(list(FEDORA_NOISE) + handoff + markers)


def rule_hart(text):
    """The boot hart a capture's start-rule line names, else 0 (the boot
    hart a kexec form of it must hand off from)."""
    match = re.search(r"^BE_MVP_SHIM: boot_hart=0x([0-9a-f]+) ", text, re.M)
    return int(match.group(1), 16) if match else 0


def digest_line(kind, size, digest):
    """U-Boot's line for KIND's (md5 or crc32) DIGEST of SIZE bytes from
    the load address."""
    return (f"{kind} for {UBOOT_LOAD:x} ... {UBOOT_LOAD + size - 1:x} ==> "
            f"{digest}")


def uboot_lines(size, crc, md5, qemu=False):
    """U-Boot's lines, the template, for its boot of an image of SIZE bytes,
    CRC-32 CRC, and MD5 MD5 through be_ld and be_go: the board's, whose
    be_ld prints md5sum's line, or QEMU's, whose prints crc32's."""
    blob, fdt, end = UBOOT_QEMU_FDT if qemu else UBOOT_BOARD_FDT
    boot = [f"{size} bytes read in " +
            ("2 ms (1.2 GiB/s)" if qemu else "33 ms (74.7 MiB/s)"),
            digest_line("crc32", size, f"{crc:08x}") if qemu else
            digest_line("md5", size, md5),
            f"Moving Image from 0x{UBOOT_LOAD:x} to 0x{STAGING:x}, "
            f"end={STAGING + size:x}",
            f"## Flattened Device Tree blob at {blob:x}",
            f"   Booting using the fdt blob at 0x{blob:x}",
            f"   Using Device Tree in place at {fdt:016x}, end {end:016x}"
            if qemu else
            f"   Loading Device Tree to {fdt:016x}, end {end:016x} ... OK"]
    if qemu:
        return ["", "", "U-Boot 2022.10 (Oct 03 2022 - 19:25:32 +0000)", "",
                "DRAM:  8 GiB",
                "Core:  25 devices, 12 uclasses, devicetree: board",
                "Flash: 32 MiB", "Loading Environment from nowhere... OK",
                "In:    serial@10000000", "Out:   serial@10000000",
                "Err:   serial@10000000", "Net:   No ethernet found.",
                "Hit any key to stop autoboot:  0", "=> boot"] + boot + \
            ["", "Starting kernel ...", ""]
    stamps = ("4.950", "4.983", "5.001", "5.008", "5.012", "5.018")
    return ["U-Boot SPL 2022.10 (May 21 2026 - 07:43:32 +0000)", "",
            "U-Boot 2022.10 (May 21 2026 - 07:43:32 +0000), Build: "
            "jenkins-BSP-build-bsp-deb-395", "",
            "WDT:   Started watchdog@d4014000 with servicing (60s timeout)",
            "[   1.928] 227 bytes read in 1 ms (221.7 KiB/s)",
            "[   1.933] ## Info: input data size = 228 = 0xE4",
            "[   1.937] load env_k3.txt from bootfs successful",
            "[   1.942] Autoboot in 3 seconds"] + \
        [f"[{stamp:>8}] {line}" for stamp, line in zip(stamps, boot)] + \
        ["fail to get alias node efuse_power", "[   5.229]",
         "Starting kernel ...", "",
         "[   5.229] Removing MTD device #0 (nor0) with use count 1"]


def uboot_form(text, size, crc, md5, qemu=False):
    """TEXT's markers behind U-Boot's lines (uboot_lines) for an image of
    SIZE bytes, CRC-32 CRC, and MD5 MD5, the SHIM line's fdt U-Boot's
    device tree: the board's, or, with QEMU, behind TEXT's own OpenSBI
    banner too; LF."""
    parts = [line.rstrip("\r") for line in text.split("\n")]
    first = next(index for index, line in enumerate(parts)
                 if line.startswith((RULE_TAG, SHIM_TAG)))
    fdt = (UBOOT_QEMU_FDT if qemu else UBOOT_BOARD_FDT)[1]
    head = [re.sub(r"^(Domain0 Next Address +: 0x)[0-9a-f]{16}$",
                   rf"\g<1>{UBOOT_QEMU_ENTRY:016x}", line)
            for line in parts[:first]] if qemu else []
    return "\n".join(head + uboot_lines(size, crc, md5, qemu) + [
        re.sub(r"(?<= fdt=0x)[0-9a-f]{16}", f"{fdt:016x}", line)
        if line.startswith(SHIM_TAG) else line for line in parts[first:]])


def hart_zero(text):
    """TEXT as a boot on hart 0, for a board form: no start-rule line, and
    BE_MVP:02 with the started hart STOPPED and started=none."""
    hart = rule_hart(text)
    return text if not hart else "\n".join(
        re.sub(rf"(?<=[=,]){hart}:0(?=[, ])", f"{hart}:1", line).replace(
            f"started={hart}", "started=none")
        if line.startswith("BE_MVP:02 ") else line
        for line in text.split("\n") if not line.startswith(RULE_TAG))


def uboot_fixture(name):
    """The uboot fixture NAME as uboot_form makes it from its source."""
    source, qemu, size, crc, md5 = UBOOT_FIXTURES[name]
    if qemu:
        return uboot_form(fixture(source), size, crc, md5, qemu)
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != RC1_RUN_SHA256:
        raise ValueError(f"{source} differs from release candidate 1's "
                         f"record")
    return uboot_form(data.decode("ascii"), size, crc, md5)


def uboot_options(name):
    """A uboot fixture's image values (its size and both digests, as
    --image gives them), and QEMU's SBI version."""
    _, qemu, size, crc, md5 = UBOOT_FIXTURES[name]
    return dict({"sbi_version": "2.0"} if qemu else {}, image_bytes=size,
                image_crc32=crc, image_md5=md5)


def current_log_standin(text, expect, root):
    """TEXT with its whole measurement-log surface rendered for the
    current image from its reference, preserving only the retained run's
    ticks. The result is a synthetic stand-in, never a captured log."""
    if "BE_MVP:19 LOG record seq=0 " not in text:
        return text
    reference_path, boot_path = LOG.default_paths(root, "gcc", expect)
    reference = LOG.Reference(reference_path.read_bytes())
    rendered = LOG.expected_lines(reference, LOG.log_harts(expect))
    boot = boot_path.read_bytes()
    standin_records = [dict(record) for record in reference.records]
    for record in standin_records:
        if record["object"] in LOG.R2:
            offset = record["base"] - LOG.MONITOR_HPA + LOG.MONITOR_OFFSET
            record["digest"] = hashlib.sha256(
                boot[offset:offset + record["length"]]).hexdigest()
    standin_registers = LOG.replay(standin_records)
    parts = lines(text)

    launch_ticks = {}
    for line_ in parts:
        match = re.fullmatch(
            r"BE_MVP:06 LAUNCH domain=([0-9]+) .* ticks=(0x[0-9a-f]+)",
            line_)
        if match:
            launch_ticks[int(match.group(1))] = match.group(2)
    barrier = next((re.search(r" ticks=(0x[0-9a-f]+)$", line_).group(1)
                    for line_ in parts
                    if line_.startswith("BE_MVP:20 REGISTERS at=barrier ")),
                   None)

    def filled(line_):
        match = re.search(r" record seq=([0-9]+) ", line_)
        if match:
            record = standin_records[int(match.group(1))]
            line_ = line_.replace(" base=<Y> ",
                                  f" base={LOG.hex64(record['base'])} ", 1)
            line_ = line_.replace(" length=<Y> ",
                                  f" length={LOG.hex64(record['length'])} ",
                                  1)
            line_ = line_.replace(" digest=<Z>",
                                  f" digest={record['digest']}", 1)
        return line_.replace("r0=<Z>", f"r0={standin_registers[0]}")

    launches = {}
    for line_ in rendered["launch"]:
        domain = int(re.search(r"domain=([0-9]+)", line_).group(1))
        if domain not in launch_ticks:
            raise ValueError(
                f"{expect['image']}'s retained capture has no launch tick "
                f"for domain {domain}")
        launches[domain] = line_.replace("<T>", launch_ticks[domain])
    for index, line_ in enumerate(parts):
        match = re.match(r"BE_MVP:06 LAUNCH domain=([0-9]+) ", line_)
        if match and int(match.group(1)) in launches:
            parts[index] = launches[int(match.group(1))]

    starts = [index for index, line_ in enumerate(parts)
              if line_.startswith("BE_MVP:19 LOG header ")]
    if len(starts) != 1:
        raise ValueError(
            f"{expect['image']}'s retained capture has {len(starts)} "
            "measurement-log blocks, not one")
    start = starts[0]
    end = start
    while end < len(parts) and parts[end].startswith("BE_MVP:19 LOG "):
        end += 1
    parts[start:end] = [filled(line_) for line_ in rendered["block"]]

    for index, line_ in enumerate(parts):
        if line_.startswith("BE_MVP:20 REGISTERS at=barrier "):
            if barrier is None:
                raise ValueError(
                    f"{expect['image']}'s retained capture has no barrier "
                    "tick")
            parts[index] = filled(rendered["barrier"]).replace(
                "<U>", barrier)
        elif line_.startswith("BE_MVP:20 REGISTERS at=terminal "):
            parts[index] = filled(rendered["terminal"])
        elif rendered["detail"] and line_.startswith(
                "BE_MVP:DETAIL domain="):
            parts[index] = rendered["detail"]
    return text_of(parts)


def write_fixtures(directory, expects, pins, reports=None, measured=None,
                   images=None, root=DEFAULT_BUILD):
    """The board-tool dry run's synthetic stand-ins, one per board image
    kind, from M9's retained QEMU fixtures with the whole log surface
    rendered from the current reference, each behind a handoff from its
    boot hart and judged with the current image's reference manifest and
    build inputs under ROOT: the scenario's, payload's, probe images', and a
    refused one; with te-poc's expectations (and its authority report
    among REPORTS), te-poc's passing capture and its two board variants',
    each failing as declared; and with anchor's (its report, and MEASURED,
    its measured domain's kernel and DTB), anchor's passing capture and
    its two board variants', wrong-measurement and no-grant-check, each
    failing as declared. M2's board capture of anchor (anchor-k3 before
    M9) prints no log and is not one. Then the uboot fixtures, judged
    against the two-guests expectation they were made with (PRE_M7's),
    and, for each kind IMAGES ({kind: the board image's bytes}) names, its
    board uboot form, a boot on hart 0 (but the refused kind's, which
    fails), CRLF."""
    reports, images = reports or {}, images or {}
    out = pathlib.Path(directory)
    out.mkdir(parents=True, exist_ok=True)
    previous = m0_pins()
    kinds = [(name, image, M9_FIXTURES[name],
              rule_hart(fixture(M9_FIXTURES[name])),
              "REFUSED" if name == "refused" else "PASS")
             for name, image in (
                 (name, "two-guests" if name == "refused" else name)
                 for name in M7_FIXTURES) if image in expects]
    unknown = sorted(set(images) - {kind[0] for kind in kinds})
    if unknown:
        print(f"BE_MVP_CAPTURE_FIXTURES: FAIL no kind {' '.join(unknown)}")
        return 1
    built = {"toolchain": "gcc", "build_root": root}
    standins = [
        "# Synthetic stand-ins derived from retained captures.",
        "# Each measurement-log surface is rendered from the current "
        "reference; these files are not captures.",
    ]
    for name, image, source, hart, wanted in kinds:
        text = kexec_form(current_log_standin(
            fixture(source), expects[image], root), hart)
        verdict, _ = evaluate(text, expects[image], "kexec", pins,
                              report_for(expects[image], reports),
                              measured=measured, **built)
        if verdict != wanted:
            print(f"BE_MVP_CAPTURE_FIXTURES: FAIL {name} is {verdict}")
            return 1
        output = out / f"standin-kexec-{name}.console.log"
        output.write_text(text, encoding="ascii")
        standins.append(f"{output.name} source={source}.log image={image}")
        if name not in images:
            continue
        size, crc = len(images[name]), zlib.crc32(images[name])
        md5 = hashlib.md5(images[name]).hexdigest()
        text = uboot_form(text if name == "refused" else hart_zero(text),
                          size, crc, md5).replace("\n", "\r\n")
        verdict, _ = evaluate(text, expects[image], "uboot", pins,
                              report_for(expects[image], reports),
                              measured=measured, image_bytes=size,
                              image_crc32=crc, image_md5=md5,
                              image_data=images[name], **built)
        if verdict != ("FAIL" if name == "refused" else wanted):
            print(f"BE_MVP_CAPTURE_FIXTURES: FAIL uboot {name} is {verdict}")
            return 1
        output = out / f"standin-uboot-{name}.console.log"
        output.write_text(text, encoding="ascii")
        standins.append(f"{output.name} source={source}.log image={image}")
    current = dict(M9_SESSION_FIXTURES,
                   **{"self-report-flip": M9_FIXTURES["self-report-flip"]})
    for image, source in current.items():
        if image in expects:
            text = current_log_standin(fixture(source), expects[image], root)
            output = out / f"standin-{source}.log"
            output.write_text(text, encoding="ascii")
            standins.append(
                f"{output.name} source={source}.log image={image}")
    (out / "STANDINS.txt").write_text(
        "\n".join(standins) + "\n", encoding="utf-8")
    before = pre_m7()[0]
    for name in UBOOT_FIXTURES:
        text = uboot_fixture(name)
        verdict, _ = evaluate(text, before["two-guests"], "uboot",
                              previous if name in M0_FIXTURES else m2_pins(),
                              **uboot_options(name))
        if verdict != "PASS":
            print(f"BE_MVP_CAPTURE_FIXTURES: FAIL {name} is {verdict}")
            return 1
        (out / f"{name}.log").write_text(text, encoding="ascii")
    print(f"BE_MVP_CAPTURE_FIXTURES: PASS {out} captures={len(kinds)} "
          f"current_standins={len(current)} "
          f"kexec_fdt=0x{STAGING + align_up(BOARD_IMAGE_BYTES, FDT_ALIGN):x} "
          f"uboot={len(images)} uboot_fixtures={len(UBOOT_FIXTURES)}")
    return 0

# --------------------------------------------------------- self-test cases
def lines(text):
    return text.split("\n")


def text_of(parts):
    return "\n".join(parts)


def where(parts, needle, nth=0):
    """The index of the NTH line holding NEEDLE."""
    hits = [index for index, line in enumerate(parts) if needle in line]
    return hits[nth]


def replace_in(text, needle, old, new, nth=0):
    parts = lines(text)
    index = where(parts, needle, nth)
    if old not in parts[index]:
        raise ValueError(f"{old!r} not in {parts[index]!r}")
    parts[index] = parts[index].replace(old, new, 1)
    return text_of(parts)


def delete(text, needle, nth=0):
    parts = lines(text)
    del parts[where(parts, needle, nth)]
    return text_of(parts)


def insert(text, needle, line, nth=0, after=True):
    parts = lines(text)
    index = where(parts, needle, nth) + (1 if after else 0)
    parts.insert(index, line)
    return text_of(parts)


def two_blocks(text):
    """The domains' lines regrouped: all of G0's, then all of G1's, each
    domain's :11 and :12 after its block, every other order kept."""
    parts = lines(text)
    first = where(parts, "BE_MVP:10 ", 1) + 1
    last = where(parts, "BE_MVP:13 ")
    body = parts[first:last]
    blocks = []
    for domain in (0, 1):
        own = [line for line in body if line.startswith(f"BE_MVP_G{domain}: ")
               or f" domain={domain} " in line]
        blocks += [line for line in own if not line.startswith("BE_MVP:1")]
        blocks += [line for line in own if line.startswith("BE_MVP:1")]
    return text_of(parts[:first] + blocks + parts[last:])


def narrow_overlap(text):
    """G0's run moved to start where G1's ends but for a quarter of it:
    the overlap below half the shorter interval, every sum kept."""
    parts = lines(text)
    shutdowns = {}
    for index, line in enumerate(parts):
        match = SHUTDOWN.fullmatch(line)
        if match:
            shutdowns[int(match.group(2))] = index
    g1 = SHUTDOWN.fullmatch(parts[shutdowns[1]])
    start1, end1 = int(g1.group(15), 16), int(g1.group(16), 16)
    entered = end1 - (end1 - start1) // 4
    g0 = SHUTDOWN.fullmatch(parts[shutdowns[0]])
    end0 = entered + (int(g0.group(16), 16) - int(g0.group(15), 16))
    parts[shutdowns[0]] = re.sub(r"entered=0x[0-9a-f]+ ticks=0x[0-9a-f]+$",
                                 f"entered=0x{entered:x} ticks=0x{end0:x}",
                                 parts[shutdowns[0]])
    entry = where(parts, "BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0")
    parts[entry] = re.sub(r"ticks=0x[0-9a-f]+$", f"ticks=0x{entered:x}",
                          parts[entry])
    complete = where(parts, "BE_MVP:13 ")
    overlap = max(0, end1 - entered)
    parts[complete] = re.sub(r"overlap_ticks=0x[0-9a-f]+ ticks=0x[0-9a-f]+$",
                             f"overlap_ticks=0x{overlap:x} "
                             f"ticks=0x{max(end0, end1) + 0x100:x}",
                             parts[complete])
    return text_of(parts)


def cut(text, keep):
    """The capture cut KEEP characters into its last line."""
    parts = lines(text.rstrip("\n"))
    parts[-1] = parts[-1][:keep]
    return text_of(parts)


def probe_at(text, needle, received):
    """TEXT with its BE_MVP:11 line holding NEEDLE moved in time: its
    received= RECEIVED, and its sent= and answered= as far from it as they
    were."""
    parts = lines(text)
    index = where(parts, needle)
    sent, was, answered = (int(value, 16) for value in IPI_PROBE.fullmatch(
        parts[index]).groups()[2:5])
    parts[index] = re.sub(
        r"sent=0x[0-9a-f]+ received=0x[0-9a-f]+ answered=0x[0-9a-f]+",
        f"sent=0x{received - was + sent:x} received=0x{received:x} "
        f"answered=0x{received - was + answered:x}", parts[index])
    return text_of(parts)


def self_cases():
    """(name, image, mode, text, options, verdict)."""
    two = fixture("qemu-two-guests-gcc")
    hart6 = fixture("qemu-two-guests-clang-hart6")
    fallback = fixture("qemu-ring-full-gcc")
    platform = fixture("qemu-probe-platform-gcc")
    distinct = fixture("qemu-probe-vmid-distinct-gcc")
    refused = fixture("qemu-plic-gcc-refused")
    payload = fixture("qemu-payload-gcc")
    v2 = {"sbi_version": "2.0"}
    banner_end = where(lines(payload), SHIM_TAG)
    firmware_version = text_of(lines(payload)[:banner_end + 1] +
                               ["BE_MVP:FAIL boot", ""])
    exit_budget = text_of(lines(two)[:where(lines(two), "MVPINIT 03", 4)] + [
        "BE_MVP:FAIL exit-budget", "BE_MVP:DETAIL domain=0 hart=1 cause=0xa "
        "pc=0xffffffff800071ec tval=0x0 htval=0x0 htinst=0x0 spvp=1 "
        "vsatp=0x8000000000080385 exits=65", "BE_MVP:SRST_RETURNED", ""])
    return [
        ("scenario, boot hart 0", "two-guests", "direct", two, v2, "PASS"),
        ("scenario, CRLF", "two-guests", "direct", two.replace("\n", "\r\n"),
         v2, "PASS"),
        ("scenario, boot hart 6 and its start rule", "two-guests", "direct",
         hart6, v2, "PASS"),
        ("shim-rule variant", "shim-rule", "direct",
         fixture("qemu-shim-rule-gcc"), v2, "PASS"),
        ("a domain hart's boot, refused", "two-guests", "direct", refused,
         v2, "REFUSED"),
        ("ring-full, both fallbacks", "ring-full", "direct", fallback, v2,
         "PASS"),
        ("ring-full, the second hart cut short", "ring-full", "direct",
         fixture("qemu-ring-full-clang"), v2, "PASS"),
        ("ring-full, the last DETAIL cut mid-line", "ring-full", "direct",
         cut(fallback, 40), v2, "PASS"),
        ("rdcycle variant, cause 22", "rdcycle", "direct",
         fixture("qemu-rdcycle-clang"), v2, "PASS"),
        ("payload variant", "payload", "direct", payload, v2, "PASS"),
        ("exit-budget variant, synthetic", "exit-budget", "direct",
         exit_budget, v2, "PASS"),
        ("firmware-version variant, synthetic", "firmware-version", "direct",
         firmware_version, v2, "PASS"),
        ("probe-platform", "probe-platform", "direct", platform, v2, "PASS"),
        ("probe-vmid-distinct", "probe-vmid-distinct", "direct", distinct,
         v2, "PASS"),
        ("probe-vmid-shared", "probe-vmid-shared", "direct",
         fixture("qemu-probe-vmid-shared-gcc"), v2, "PASS"),
        ("probe-vmid-shared, A's value is a fact", "probe-vmid-shared",
         "direct", replace_in(fixture("qemu-probe-vmid-shared-gcc"),
                              "PROBE vmid", "after=0x5a5a5a5a5a5a5a5a",
                              "after=0xa5a5a5a5a5a5a5a5"), v2, "PASS"),
        ("probe stop: a stale translation under distinct VMIDs",
         "probe-vmid-distinct", "direct",
         replace_in(distinct, "PROBE vmid", "after=0x5a5a5a5a5a5a5a5a",
                    "after=0xa5a5a5a5a5a5a5a5"), v2, "STOP"),
        ("probe stop: an IPI not delivered at V=1", "probe-platform",
         "direct", replace_in(platform, "mode=vs", "delivered=100",
                              "delivered=99"), v2, "STOP"),
        ("probe stop: htval not GPA >> 2", "probe-platform", "direct",
         replace_in(platform, "access=store", "htval=0x24000000",
                    "htval=0x90000000"), v2, "STOP"),
        ("probe stop: a stale read with fences", "probe-platform", "direct",
         replace_in(platform, "mode=fenced", "stale=0", "stale=3"), v2,
         "STOP"),
        ("probe stop: a hart not STOPPED", "probe-platform", "direct",
         replace_in(platform, "PROBE hsm", "4:1", "4:0"), v2, "STOP"),
        ("probe: the unfenced stale count is a fact", "probe-platform",
         "direct", replace_in(platform, "mode=unfenced", "stale=0",
                              "stale=17"), v2, "PASS"),
        ("kexec scenario, B7's recorded handoff", "two-guests", "kexec",
         kexec_form(two), {}, "PASS"),
        ("kexec scenario, the loader's FDT", "two-guests", "kexec",
         kexec_form(two), {"kexec_fdt": 0x108400000}, "PASS"),
        ("kexec scenario, the image's FDT slot", "two-guests", "kexec",
         kexec_form(two), {"image_bytes": BOARD_IMAGE_BYTES}, "PASS"),
        ("kexec scenario from hart 6", "two-guests", "kexec",
         kexec_form(hart6, 6), {}, "PASS"),
        ("kexec refusal from hart 1", "two-guests", "kexec",
         kexec_form(refused, 1), {}, "REFUSED"),
        ("kexec payload", "payload", "kexec", kexec_form(payload), {},
         "PASS"),
        ("kexec probe-platform", "probe-platform", "kexec",
         kexec_form(platform), {}, "PASS"),
        ("board run 1, hart 0's drain-batched order (stop 6)", "two-guests",
         "kexec", fixture(BOARD_STOP6), {"kexec_fdt": BOARD_STOP6_FDT},
         "FAIL"),
    ]


def te_poc_cases(report):
    """M1's cases, judged with M1's pins and te-poc's report."""
    tepoc = fixture("qemu-te-poc-gcc")
    v2 = {"sbi_version": "2.0", "report": report}
    return [
        ("te-poc: the channel and three denials", "te-poc", "direct", tepoc,
         v2, "PASS"),
        ("te-poc, B7's recorded handoff", "te-poc", "kexec",
         kexec_form(tepoc), {"report": report}, "PASS"),
        ("reader-write: the channel check refuses the reader's W",
         "reader-write", "direct", fixture("qemu-reader-write-gcc"), v2,
         "PASS"),
        ("no-inject: the first denied access ends the run", "no-inject",
         "direct", fixture("qemu-no-inject-gcc"), v2, "PASS"),
        ("te-poc without its report", "te-poc", "direct", tepoc,
         {"sbi_version": "2.0"}, "FAIL"),
        ("the denials made by pid 1 (stop 6, Plan revision M1-A)", "te-poc",
         "direct", fixture(PID1_STOP6), v2, "FAIL"),
        ("no-inject on the board, both domain harts' own FAIL lines (stop "
         "6, Plan revision M1-B)", "no-inject", "kexec",
         fixture(BOARD_NO_INJECT),
         {"report": report, "kexec_fdt": BOARD_NO_INJECT_FDT}, "FAIL"),
    ]


# The anchor mutations (anchor_mutations) the self-test also judges, as
# the smallest edits of the anchor fixture that each new rule rejects
# (M2-5's, and Plan revision M2-A.1's).
ANCHOR_SELF_EDITS = (
    "a REQUEST's digest one digit off", "a BE_MVP:MGMT line removed",
    "a denied request's result -3 for -4",
    "DOMAIN_TERMINATED after the host's shutdown",
    "MEASURED one digit off", "DOMAIN_TERMINATED's sha256 one digit off",
    "the host's refused=0", "a G0 line after the host's shutdown",
    "FID 7's request on hart 0", "a RESULT line from the protected domain",
    "the protected domain's PONG spv=0 before its first request")


def anchor_cases(report, measured):
    """M2's cases, judged with the current pins, anchor's report, and its
    measured domain's kernel and DTB (MEASURED); among them the first M2
    board campaign's anchor capture as the board recorded it (Plan
    revision M2-A), and with its probe at either end of its wait."""
    anchor = fixture(ANCHOR_FIXTURES["anchor"])
    board = fixture(BOARD_PING_WAIT)
    first, last = BOARD_PING_WAIT_SPAN
    probe = "BE_MVP:11 IPI_PROBE hart=2"
    v3 = {"sbi_version": "2.0", "report": report, "measured": measured}
    on_board = dict(v3, sbi_version=None, kexec_fdt=BOARD_PING_WAIT_FDT)
    return [
        ("anchor: the pages, the measurement, four requests, fifteen "
         "requests on hart 0, the pause and the termination", "anchor",
         "direct", anchor, v3, "PASS"),
        ("anchor, B7's recorded handoff", "anchor", "kexec",
         kexec_form(anchor, rule_hart(anchor)), dict(v3, sbi_version=None),
         "PASS"),
        ("secret-shared: the page check refuses the secret page in the "
         "host's root", "secret-shared", "direct",
         fixture(ANCHOR_FIXTURES["secret-shared"]), v3, "PASS"),
        ("response-writable: the page check refuses W in the host's "
         "response leaf", "response-writable", "direct",
         fixture(ANCHOR_FIXTURES["response-writable"]), v3, "PASS"),
        ("wrong-measurement: both values, before any hart starts",
         "wrong-measurement", "direct",
         fixture(ANCHOR_FIXTURES["wrong-measurement"]), v3, "PASS"),
        ("no-grant-check: the protected domain's terminate 0 ends the "
         "host, then run-timeout", "no-grant-check", "direct",
         fixture(ANCHOR_FIXTURES["no-grant-check"]), v3, "PASS"),
        ("anchor without its measured domain's kernel and DTB", "anchor",
         "direct", anchor, dict(v3, measured=None), "FAIL"),
        ("anchor on the board: hart 2's PONG spv=0 inside its request 1's "
         "wait (stop 6, Plan revision M2-A)", "anchor", "kexec", board,
         on_board, "PASS"),
        ("anchor on the board, the PING received at its wait's first tick",
         "anchor", "kexec", probe_at(board, probe, first), on_board,
         "PASS"),
        ("anchor on the board, the PING received at its wait's last tick",
         "anchor", "kexec", probe_at(board, probe, last), on_board, "PASS"),
    ]


def uboot_cases(pins, previous):
    """The uboot mode's cases (planning/mvp-m5-plan.md, "Tool changes
    (M5-2)"), each with the guest pins its markers were made with: the
    board fixture as recorded, with CRLF and the stamped blank line's
    space, with its image unknown, and with crc32's line of its image in
    place of md5sum's; QEMU's from hart 6, from hart 3, with md5sum's line
    of its image in place of crc32's (either digest form, wherever made),
    and with the session's be_ld echoed before the boot; a domain hart's
    boot in QEMU, refused; and B7's kexec handoff, which is no U-Boot
    boot."""
    board, qemu = fixture(BOARD_UBOOT), fixture(QEMU_UBOOT)
    on_board, in_qemu = uboot_options(BOARD_UBOOT), uboot_options(QEMU_UBOOT)
    hart3 = qemu
    for needle, old, new in (("Boot HART ID", ": 6", ": 3"),
                             ("Domain0 Boot HART", ": 6", ": 3"),
                             (RULE_TAG, "0x6", "0x3"),
                             ("BE_MVP:02 ", "3:1", "3:0"),
                             ("BE_MVP:02 ", "6:0", "6:1"),
                             ("BE_MVP:02 ", "started=6", "started=3")):
        hart3 = replace_in(hart3, needle, old, new)
    typed = insert(qemu, "=> boot", "=> setenv be_ld 'load nvme 0:${be_part} "
                   "0x140000000 /${be_image} && md5sum 0x140000000 "
                   "${filesize}'", after=False)
    # Each fixture with the other digest form of its own image.
    swapped = {}
    for name, text, kind, other in ((BOARD_UBOOT, board, "md5", "crc32"),
                                    (QEMU_UBOOT, qemu, "crc32", "md5")):
        _, _, size, crc, md5 = UBOOT_FIXTURES[name]
        digests = {"crc32": f"{crc:08x}", "md5": md5}
        swapped[name] = replace_in(
            text, f"{kind} for ", digest_line(kind, size, digests[kind]),
            digest_line(other, size, digests[other]))
    return [
        ("uboot: the board from a reset, release candidate 1's GCC "
         "two-guests run", "two-guests", "uboot", board, on_board, "PASS",
         pins),
        ("uboot: the board, CRLF, the stamped blank line's space",
         "two-guests", "uboot", board.replace("[   5.229]\n", "[   5.229] \n")
         .replace("\n", "\r\n"), on_board, "PASS", pins),
        ("uboot: the board, the image unknown", "two-guests", "uboot", board,
         {}, "PASS", pins),
        ("uboot: the board, crc32's line of its image in place of md5sum's",
         "two-guests", "uboot", swapped[BOARD_UBOOT], on_board, "PASS", pins),
        ("uboot: QEMU, boot hart 6 and its start rule", "two-guests",
         "uboot", qemu, in_qemu, "PASS", previous),
        ("uboot: QEMU, boot hart 3 and its start rule", "two-guests",
         "uboot", hart3, in_qemu, "PASS", previous),
        ("uboot: QEMU, md5sum's line of its image in place of crc32's",
         "two-guests", "uboot", swapped[QEMU_UBOOT], in_qemu, "PASS",
         previous),
        ("uboot: QEMU, be_ld echoed before the boot", "two-guests", "uboot",
         typed, in_qemu, "PASS", previous),
        ("uboot: QEMU, a domain hart's boot, refused", "two-guests", "uboot",
         uboot_form(fixture("qemu-plic-gcc-refused"),
                    *UBOOT_FIXTURES[QEMU_UBOOT][2:], qemu=True), in_qemu,
         "REFUSED", previous),
        ("uboot: B7's kexec handoff, no U-Boot boot", "two-guests", "uboot",
         kexec_form(fixture("qemu-two-guests-gcc")), {}, "FAIL", previous),
    ]


def m6_cases(expects, reports, measured):
    """M6's cases (planning/mvp-m6-plan.md, D-3), judged against the
    expectations EXPECTS they were made with (PRE_M7's): each M6 fixture as
    captured, the MVP's prelude in place of R3's; the scenario behind B7's
    handoff from its boot hart, and in the board's U-Boot form; and the
    sbi-3.0 variant's failure after BOOT_VALIDATED, which its declared
    place (none) rejects."""
    two = fixture(M6_FIXTURES["two-guests"])
    cases = []
    for kind, name in M6_FIXTURES.items():
        image = "two-guests" if kind == "refused" else kind
        cases.append((f"M6 {kind}", image, "direct", fixture(name),
                      {"sbi_version": "2.0", "measured": measured,
                       "report": report_for(expects[image], reports)},
                      "REFUSED" if kind == "refused" else "PASS"))
    payload = lines(fixture(M6_FIXTURES["payload"]))
    sbi3 = [text_of([line.replace(": 2.0", ": 3.0") if "Runtime SBI" in line
                     else line for line in
                     payload[:where(payload, SHIM_TAG) + extra]] +
                    ["BE_MVP:FAIL boot", ""]) for extra in (1, 2)]
    return cases + [
        ("M6 two-guests, B7's recorded handoff", "two-guests", "kexec",
         kexec_form(two, rule_hart(two)), {}, "PASS"),
        ("M6 two-guests, the board's U-Boot form", "two-guests", "uboot",
         uboot_form(hart_zero(two), *UBOOT_FIXTURES[BOARD_UBOOT][2:]), {},
         "PASS"),
        ("M6 sbi-3.0, synthetic", "sbi-3.0", "direct", sbi3[0],
         {"sbi_version": "3.0"}, "PASS"),
        ("M6 sbi-3.0, the failure after BOOT_VALIDATED", "sbi-3.0",
         "direct", sbi3[1], {"sbi_version": "3.0"}, "FAIL"),
    ]


def m7_cases(expects, reports, measured):
    """M7's cases (planning/mvp-m7-plan.md, D-10), judged against the
    expectations EXPECTS they were made with (PRE_M9's, before M9 added
    the log): each M7 fixture as captured, its guests' kernel lines naming SBI implementation version 5, or 6 with the
    management extension; the scenario behind B7's handoff from its boot
    hart, and in the board's U-Boot form; and M6's scenario capture, whose
    guests name version 3, which fails them."""
    two = fixture(M7_FIXTURES["two-guests"])
    cases = []
    for kind, name in M7_FIXTURES.items():
        image = "two-guests" if kind == "refused" else kind
        cases.append((f"M7 {kind}", image, "direct", fixture(name),
                      {"sbi_version": "2.0", "measured": measured,
                       "report": report_for(expects[image], reports)},
                      "REFUSED" if kind == "refused" else "PASS"))
    received = probe_received(fixture(M7_FIXTURES["probe-console-input"]),
                              PROBE_TEXT * 4)
    return cases + [
        ("M7 probe-console-input, 256 bytes behind B7's handoff",
         "probe-console-input", "kexec", kexec_form(received), {}, "PASS"),
        ("M7 probe-console-input, 256 bytes in the board's U-Boot form",
         "probe-console-input", "uboot", uboot_form(
             received, *UBOOT_FIXTURES[BOARD_UBOOT][2:]), {}, "PASS"),
        ("M7 probe-console-input, bytes in a QEMU run, where nothing is "
         "typed", "probe-console-input", "direct", received,
         {"sbi_version": "2.0"}, "FAIL"),
        ("M7 two-guests, B7's recorded handoff", "two-guests", "kexec",
         kexec_form(two, rule_hart(two)), {}, "PASS"),
        ("M7 two-guests, the board's U-Boot form", "two-guests", "uboot",
         uboot_form(hart_zero(two), *UBOOT_FIXTURES[BOARD_UBOOT][2:]), {},
         "PASS"),
        ("M6 two-guests against M7's expectation", "two-guests", "direct",
         fixture(M6_FIXTURES["two-guests"]), {"sbi_version": "2.0"},
         "FAIL"),
    ]


# Q14's characterization text (planning/mvp-m7-plan.md, D-12), which
# tools/k3-console.sh probe-type types four times.
PROBE_TEXT = b"0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-="


def retained_options(expect, references, **extra):
    """The pinned era reference for one retained M9 capture."""
    return dict({"sbi_version": "2.0", "toolchain": "gcc",
                 "reference_data": references[expect["image"]],
                 "retained_era": True}, **extra)


def m9_fixture_cases(expects, reports, references):
    """M9's cases (planning/mvp-m9-plan.md, D-4), judged against the
    pinned pre-M11 era set: each M9 fixture as captured; each console
    variant's session with its keys, nonce, and session file; and M7's
    scenario capture, which prints no log, against M9's expectation."""
    cases = []
    for kind, name in M9_FIXTURES.items():
        image = "two-guests" if kind == "refused" else kind
        cases.append((f"M9 {kind}", image, "direct", fixture(name),
                      retained_options(
                          expects[image], references,
                          report=report_for(expects[image], reports)),
                      "REFUSED" if kind == "refused" else "PASS"))
    for image, name in M9_SESSION_FIXTURES.items():
        cases.append((f"M9 {image}", image, "direct", fixture(name),
                      session_options(
                          image, M9_SESSION_FIXTURES,
                          **retained_options(
                              expects[image], references,
                              report=report_for(expects[image], reports))),
                      "PASS"))
    return cases + [
        ("M7 two-guests against M9's expectation, no log", "two-guests",
         "direct", fixture(M7_FIXTURES["two-guests"]),
         retained_options(expects["two-guests"], references),
         "FAIL")]


def current_m9_fixture_cases(expects, reports, root):
    """M9's retained cases as current synthetic stand-ins, through the live
    recomputing path so none of recompute()'s coverage is lost."""
    cases = []
    base = {"sbi_version": "2.0", "toolchain": "gcc",
            "build_root": root}
    for kind, name in M9_FIXTURES.items():
        image = "two-guests" if kind == "refused" else kind
        text = current_log_standin(fixture(name), expects[image], root)
        cases.append((f"M11 stand-in {kind}", image, "direct", text,
                      dict(base, report=report_for(expects[image], reports)),
                      "REFUSED" if kind == "refused" else "PASS"))
    for image, name in M9_SESSION_FIXTURES.items():
        text = current_log_standin(fixture(name), expects[image], root)
        cases.append((
            f"M11 stand-in {image}", image, "direct", text,
            session_options(
                image, M9_SESSION_FIXTURES, **base,
                report=report_for(expects[image], reports)), "PASS"))
    return cases


def relogged(text, change):
    """TEXT, an M9 capture, with CHANGE (its lines, edited in place)
    applied, and every register it prints (the :20 lines', each LAUNCH
    line's, a DETAIL's computed=, each DOMAIN_TERMINATED digest) made the
    replay of the changed records, as a monitor that printed what it
    hashed would: the replay passes, and only what the registers do not
    bind can fail."""
    def replayed(parts):
        return LOG.rebuild(LOG.lines_of([line for line in parts
                                         if LOG.is_log_line(line)])
                           ).replayed
    parts = lines(text)
    before = replayed(parts)
    change(parts)
    out = text_of(parts)
    for old, new in zip(before, replayed(parts)):
        out = out.replace(old, new)
    return out


def log_json_path(log_json, result_json):
    """Where main() writes log.json (mvp/docs/log-profile.md, 5.2: in the
    run record): --log-json; else beside --json's result.json, as k3-run.sh,
    the U-Boot rehearsal, and the reference boot name it, or STEM.log.json
    beside run-qemu.sh's STEM.result.json; else nowhere."""
    if log_json:
        return pathlib.Path(log_json)
    if result_json:
        path = pathlib.Path(result_json)
        if path.name == "result.json":
            return path.with_name("log.json")
        if path.name.endswith(".result.json"):
            return path.with_name(path.name[:-len("result.json")] + "log.json")
    return None


def m9_cases(expects, reports, pins, root):
    """The checker's wiring of the log module (planning/mvp-m9-plan.md,
    D-4) on current synthetic stand-ins, each reference the current build's:
    [(kind, name, ok, detail)]."""
    te_poc = report_for(expects["te-poc"], reports)
    anchor = report_for(expects["anchor"], reports)
    plain = current_log_standin(
        fixture(M9_FIXTURES["te-poc"]), expects["te-poc"], root)
    held = current_log_standin(
        fixture(M9_FIXTURES["anchor"]), expects["anchor"], root)
    boot = LOG.default_paths(root, "gcc", expects["te-poc"])[1].read_bytes()
    board = uboot_form(hart_zero(plain), len(boot), zlib.crc32(boot),
                       hashlib.md5(boot).hexdigest())
    record_line = next(line for line in plain.split("\n")
                       if line.startswith("BE_MVP:19 LOG record seq=6 "))
    looks = plain.replace(record_line, g(0, record_line))

    def judged(image, text, report_data, mode="direct", **options):
        if mode == "direct":
            defaults = {"sbi_version": "2.0", "toolchain": "gcc",
                        "build_root": root}
        else:
            image_data = LOG.default_paths(
                root, "gcc", expects[image])[1].read_bytes()
            defaults = {"toolchain": "gcc", "build_root": root,
                        "image_data": image_data,
                        "image_bytes": len(image_data),
                        "image_crc32": zlib.crc32(image_data),
                        "image_md5": hashlib.md5(image_data).hexdigest()}
        options = dict(defaults, **options)
        return evaluate(text, expects[image], mode, pins, report_data,
                        **options)

    def digest_of(seq):
        """A record line's edit: its digest another's."""
        def change(parts):
            index = next(index for index, line in enumerate(parts)
                         if line.startswith(f"BE_MVP:19 LOG record seq={seq} "))
            parts[index] = re.sub(r"digest=[0-9a-f]{64}$", "digest=" +
                                  hashlib.sha256(b"wrong").hexdigest(),
                                  parts[index])
        return change
    cases = []
    verdict, record = judged("te-poc", plain, te_poc)
    export = record.get("log_export")
    page = LOG.encode(*LOG.read_export(LOG.render(export))[:2]) \
        if export else None
    cases.append(("wiring", "te-poc's M9 capture: PASS, closed, every "
                  "digest recomputed equal, and its log.json rebuilds the "
                  "page", verdict == "PASS" and record["log"]["state"] ==
                  "closed" and all(row.get("recomputed") == "equal" for row
                                   in record["log"]["records"][:-1]) and
                  page is not None and len(page) == LOG.PAGE_BYTES,
                  record["findings"]))
    verdict, record = judged("anchor", held, anchor)
    cases.append(("wiring", "anchor's M9 capture: PASS, no MEASURED line, "
                  "DOMAIN_TERMINATED's digest the launch register",
                  verdict == "PASS" and "BE_MVP:06 MEASURED" not in held,
                  record["findings"]))
    verdict, record = judged("anchor", held, anchor,
                             measured=PINNED_MEASUREMENT)
    cases.append(("kind1", "anchor's M9 capture with the pinned measurement "
                  "of the retained fixtures, refused", verdict == "FAIL" and
                  any("the pinned measurement serves" in finding
                      for finding in record["findings"]),
                  record["findings"]))
    flip = current_log_standin(
        fixture(M9_FIXTURES["self-report-flip"]),
        expects["self-report-flip"], root)
    verdict, record = judged("self-report-flip", flip, anchor)
    cases.append(("kind5", "self-report-flip's M9 capture: PASS with exactly "
                  "its one declared finding", verdict == "PASS" and
                  record["log_declared"] == [LOG.FLIP_FINDING] and not
                  record["findings"], record["findings"]))
    verdict, record = judged("anchor", flip, anchor)
    cases.append(("kind5", "self-report-flip's capture judged as the "
                  "nominal anchor's, refused for mvp-rodata alone: its "
                  "printed digest not the nominal image's bytes, and the "
                  "self-report", verdict == "FAIL" and LOG.FLIP_FINDING in
                  record["findings"] and all(
                      "mvp-rodata" in finding
                      for finding in record["findings"]),
                  record["findings"]))
    verdict, record = judged("te-poc", board, te_poc, "uboot")
    cases.append(("wiring", "te-poc's M9 capture in the board's U-Boot "
                  "form, its loader observation beside the log: PASS",
                  verdict == "PASS", record["findings"]))
    verdict, record = judged("te-poc", forged_loader_block(
        board, hashlib.md5(boot).hexdigest(), "0" * 32), te_poc, "uboot")
    cases.append(("kind1", "a forged loader block before an M9 log, refused",
                  verdict == "FAIL" and any(
                      "2 U-Boot autoboot lines" in finding
                      for finding in record["findings"]),
                  record["findings"]))
    verdict, record = judged("te-poc", looks, te_poc)
    cases.append(("kind2", "a guest-prefixed look-alike of a record line, "
                  "no record and a mixed line", verdict == "FAIL" and all(
                      any(wanted in finding for finding in record[
                          "findings"]) for wanted in (
                          "mixed line", "seq=7 is not the line's position 6")),
                  record["findings"]))
    for kind, image, text, report_data, name, wanted in (
            ("kind3", "te-poc", relogged(plain, digest_of(9)), te_poc,
             "domain 0's kernel", "kernel-image's printed digest"),
            ("kind3", "anchor", relogged(held, digest_of(13)), anchor,
             "the secret page", "secret-page's printed digest"),
            ("kind3", "anchor", relogged(held, digest_of(3)), anchor,
             "mvp-text's range", "mvp-text's printed digest")):
        verdict, record = judged(image, text, report_data)
        cases.append((kind, f"{image}'s M9 capture with a wrong digest at "
                      f"{name}, its registers recomputed: the replay "
                      f"passes, the recomputation does not",
                      verdict == "FAIL" and any(
                          wanted in finding for finding in record[
                              "findings"]) and not any(
                          "replay" in finding for finding in record[
                              "findings"]), record["findings"]))
    cases.append(("wiring", "log.json in the run record: beside result.json "
                  "and STEM.result.json, or at --log-json", [
                      log_json_path(given, result) for given, result in (
                          (None, "RUN/result.json"),
                          (None, "suite/gcc-te-poc.1.result.json"),
                          ("OUT/log.json", "RUN/result.json"),
                          (None, "RUN/other.json"), (None, None))] == [
                      pathlib.Path("RUN/log.json"),
                      pathlib.Path("suite/gcc-te-poc.1.log.json"),
                      pathlib.Path("OUT/log.json"), None, None], []))
    return cases


def probe_received(text, data, sizes=None):
    """probe-console-input's capture TEXT as if it had received DATA: its
    lines of SIZES bytes (64 each by default) and its counts."""
    sizes = sizes or [64] * ((len(data) + 63) // 64)
    rows, at = [], 0
    for size in sizes:
        at += size
        rows.append(f"BE_MVP:PROBE console-input bytes={at} "
                    f"hex={data[at - size:at].hex()}")
    parts = lines(text)
    index = where(parts, "BE_MVP:PROBE console-input total=")
    parts[index:index + 1] = rows + [
        f"BE_MVP:PROBE console-input total={len(data)} polls=2030 "
        f"nonzero_polls={len(rows)} max_per_poll=64 errors=0 sha256="
        f"{hashlib.sha256(data).hexdigest()[:16]}"]
    return text_of(parts)


def session_options(image, fixtures=SESSION_FIXTURES, **extra):
    """A session fixture's options (M7-4's, or FIXTURES'): its keys, its
    nonce, and its scenario's session file, as tests/session-typist.py
    gives them."""
    name = fixtures[image]
    scenario = image[:-len("-shell")]
    return dict({"sbi_version": "2.0",
                 "typed": (FIXTURES / f"{name}.typed.txt").read_text(
                     encoding="ascii"),
                 "nonce": (FIXTURES / f"{name}.nonce.txt").read_text(
                     encoding="ascii").strip(),
                 "session": (MVP_DIR / "scenarios" / scenario / "sessions" /
                             "shell.json").read_bytes()}, **extra)


def hostile_bare(text, forged):
    """The hostile capture with its G0 line FORGED bare, as hart 0's or a
    line of G1's would be."""
    return replace_in(text, g(0, forged), g(0, forged), forged)


def m74_cases(expects, reports, measured):
    """M7-4's cases (planning/mvp-m7-plan.md, D-4, D-11), judged against
    the expectations EXPECTS they were made with (PRE_M9's): the hostile
    guest's capture, each
    typed session with its keys, nonce, and session file; a session
    without its keys or with another nonce; and the hostile capture with a
    forged line bare."""
    hostile = fixture(HOSTILE_FIXTURE)
    cases = [("M7-4 hostile", "hostile", "direct", hostile,
              {"sbi_version": "2.0"}, "PASS")]
    for image, name in SESSION_FIXTURES.items():
        cases.append((f"M7-4 {image}", image, "direct", fixture(name),
                      session_options(image, measured=measured,
                                      report=report_for(expects[image],
                                                        reports)), "PASS"))
    two = fixture(SESSION_FIXTURES["two-guests-shell"])
    options = session_options("two-guests-shell")
    del options["typed"]
    return cases + [
        ("M7-4 two-guests-shell without its keys", "two-guests-shell",
         "direct", two, options, "FAIL"),
        ("M7-4 two-guests-shell with another run's nonce",
         "two-guests-shell", "direct", two,
         session_options("two-guests-shell", nonce="0123456789abcdef"),
         "FAIL"),
        ("M7-4 two-guests-shell against two-guests' expectation",
         "two-guests", "direct", two, {"sbi_version": "2.0"}, "FAIL"),
        ("M7-4 hostile, a forged run line bare", "hostile", "direct",
         hostile_bare(hostile, FORGED_RUN), {"sbi_version": "2.0"}, "FAIL"),
        ("M7-4 hostile, a forged prefix bare", "hostile", "direct",
         hostile_bare(hostile, FORGED_PREFIX), {"sbi_version": "2.0"},
         "FAIL"),
    ]


def self_test(expects, pins, reports, measured, current, prior, latest,
              era, era_references, root):
    """The cases, each fixture against the expectations its capture was
    made with: EXPECTS (te-poc's and anchor's at 366c8af4, PRE_M6, and
    two-guests' at ae3e9537, PRE_M7), for M6's fixtures CURRENT (every
    scenario's at ae3e9537, PRE_M7), for M7's PRIOR (every scenario's at
    ca48456f, PRE_M9), and for M9's retained captures against ERA; current
    stand-ins use LATEST and the build at ROOT."""
    failed = 0
    previous, m1, m2 = m0_pins(), m1_pins(), m2_pins()
    report = report_for(expects["te-poc"], reports)
    anchor = report_for(expects["anchor"], reports)
    pinned = PINNED_MEASUREMENT
    base_cases = []
    for name, image, mode, text, options, wanted in self_cases():
        table = latest if image == "firmware-version" else expects
        if image == "firmware-version":
            options = dict(options, toolchain="gcc", build_root=root)
        base_cases.append((name, image, mode, text, options, wanted,
                           previous, table))
    cases = base_cases + \
        [case + (m1, expects) for case in te_poc_cases(report)] + \
        [case + (m2, expects) for case in anchor_cases(anchor, pinned)] + \
        [case + (expects,) for case in uboot_cases(m2, previous)] + \
        [case + (m2, current)
         for case in m6_cases(current, reports, pinned)] + \
        [case + (pins, prior)
         for case in m7_cases(prior, reports, measured)] + \
        [case + (pins, prior)
         for case in m74_cases(prior, reports, measured)] + \
        [case + (pins, era)
         for case in m9_fixture_cases(era, reports, era_references)] + \
        [case + (pins, latest)
         for case in current_m9_fixture_cases(latest, reports, root)]
    classes = {}
    for name, image, mode, text, options, wanted, case_pins, table in cases:
        verdict, record = evaluate(text, table[image], mode, case_pins,
                                   **options)
        failed += verdict != wanted
        if name.startswith("M9 "):
            run = "refused" if verdict == "REFUSED" else (
                record.get("log") or {}).get("contract", {}).get("run")
            classes[run, verdict == wanted] = classes.get(
                (run, verdict == wanted), 0) + 1
        why = "" if verdict == wanted else \
            f" {record['findings'][:3] + record['stops'][:2]}"
        print(f"{'ok  ' if verdict == wanted else 'FAIL'} {name}: "
              f"{verdict}{why}")
    # Each new rule's smallest edit: FAIL, for its own finding.
    edits = [row for row in anchor_mutations(anchor)
             if row[2] in ANCHOR_SELF_EDITS]
    for _, _, name, text, wanted, data in edits:
        verdict, record = evaluate(text, expects["anchor"], "direct", m2,
                                   data, sbi_version="2.0",
                                   measured=pinned)
        ok = verdict == "FAIL" and any(wanted in finding
                                       for finding in record["findings"])
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} anchor, {name}: {verdict}"
              f"{'' if ok else ' ' + str(record['findings'][:3])}")
    checks = len(edits) + (len(edits) != len(ANCHOR_SELF_EDITS))
    failed += len(edits) != len(ANCHOR_SELF_EDITS)
    # The uboot mode's rules, each one's smallest edit: FAIL, for its own
    # finding.
    for _, base, name, text, wanted in uboot_mutations():
        verdict, record = evaluate(text, expects["two-guests"], "uboot",
                                   previous if base == "quboot" else m2,
                                   **BASE_OPTIONS[base])
        ok = verdict == "FAIL" and any(wanted in finding
                                       for finding in record["findings"])
        checks += 1
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} uboot, {name}: {verdict}"
              f"{'' if ok else ' ' + str(record['findings'][:3])}")
    # The parser's one pass: a capture's streams and line findings.
    capture = Capture(fixture("qemu-two-guests-gcc"),
                      ("BE_MVP_G0: ", "BE_MVP_G1: "))
    for name, ok in (
            ("both domains' lines", [len(lines) for lines in
                                     capture.domains] == [65, 65]),
            ("hart 0's stream", len(capture.monitor) == 29),
            ("no line finding", capture.findings == []),
            ("the loader's lines", capture.first == len(capture.loader) + 1),
            ("alternations", alternations(capture.order) >= 8)):
        checks += 1
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} parse: {name}")
    # The stopped board run: every rule holds but the alternation floor.
    _, board = evaluate(fixture(BOARD_STOP6), expects["two-guests"], "kexec",
                        previous, kexec_fdt=BOARD_STOP6_FDT)
    ok = board["findings"] == BOARD_STOP6_FINDINGS and \
        board["fields"].get("records") == "138" and \
        board["fields"].get("wakes") == "3" and \
        board["fields"].get("alternations") == "5"
    checks += 1
    failed += not ok
    print(f"{'ok  ' if ok else 'FAIL'} board stop 6: the alternation finding "
          f"alone{'' if ok else ' ' + str(board['findings'][:3])}")
    # The pid-1 te-poc run: every rule holds but M0's rejected substring.
    _, pid1 = evaluate(fixture(PID1_STOP6), expects["te-poc"], "direct", m1,
                       report=report, sbi_version="2.0")
    # The stopped no-inject board run: its own FAIL and DETAIL lines and
    # the guest lines after the first FAIL, exactly.
    _, fallback = evaluate(fixture(BOARD_NO_INJECT), expects["no-inject"],
                           "kexec", m1, report=report,
                           kexec_fdt=BOARD_NO_INJECT_FDT)
    # M0's scenario and M1's under the current pins: the kernel comparison
    # alone.
    _, moved = evaluate(fixture("qemu-two-guests-gcc"), expects["two-guests"],
                        "direct", pins, sbi_version="2.0")
    _, moved1 = evaluate(fixture("qemu-te-poc-gcc"), expects["te-poc"],
                         "direct", pins, report=report, sbi_version="2.0")
    # Hart 0's lines alone are terminal: a domain line holding :14's text
    # after hart 0 stopped short is none.
    parts = lines(fixture("qemu-te-poc-gcc"))
    verdict, short = evaluate(
        text_of(parts[:where(parts, "BE_MVP:13 ")] +
                [g(0, "BE_MVP:14 SHUTDOWN type=0 reason=0"), ""]),
        expects["te-poc"], "direct", m1, report=report, sbi_version="2.0")
    # The stopped M2 board run (Plan revision M2-A): its probe among the
    # costs as served in hart 2's request 1's wait, and the counts the
    # board's check recorded.
    waited_verdict, waited = evaluate(
        fixture(BOARD_PING_WAIT), expects["anchor"], "kexec", m2, anchor,
        kexec_fdt=BOARD_PING_WAIT_FDT, measured=pinned)
    # The uboot fixtures: uboot_form's of their sources, and their facts.
    _, on_board = evaluate(fixture(BOARD_UBOOT), expects["two-guests"],
                           "uboot", m2, **uboot_options(BOARD_UBOOT))
    _, in_qemu = evaluate(fixture(QEMU_UBOOT), expects["two-guests"],
                          "uboot", previous, **uboot_options(QEMU_UBOOT))
    # M7-4's: a forged line bare is rejected for being where it is
    # (D-4); a shell's keys give its :18 (src/mvp-input.c's table).
    hostile = fixture(HOSTILE_FIXTURE)
    _, bare_run = evaluate(hostile_bare(hostile, FORGED_RUN),
                           prior["hostile"], "direct", pins,
                           sbi_version="2.0")
    _, bare_prefix = evaluate(hostile_bare(hostile, FORGED_PREFIX),
                              prior["hostile"], "direct", pins,
                              sbi_version="2.0")
    model, drops, selected, firsts = input_model(
        b"echo x\r~0~~a\r~1~x~2b\r~0\n", [0])
    qemu_facts = {"boot_hart": "6", "rule_hart": "6", "spl_banner": "none",
                  "fdt_loaded": "0xff73a250", "fdt_in_place": "true",
                  "fdt": "0x00000000ff73a250", "load_digest_kind": "crc32",
                  "load_digest": "de60ac10"}
    for name, ok, findings in (
            ("pid 1's three handled faults, rejected 'unhandled signal' alone",
             len(pid1["findings"]) == 3 and all(
                 "rejected 'unhandled signal'" in finding
                 for finding in pid1["findings"]), pid1["findings"]),
            ("board no-inject stop 6: both domain harts' fallback lines and "
             "the guest lines after the first FAIL, exactly",
             fallback["findings"] == BOARD_NO_INJECT_FINDINGS and
             fallback["terminal"] == "fail-marker", fallback["findings"]),
            ("M0's capture fails the current pins on the kernel alone",
             moved["findings"] and all(" is not the pin 0x" in finding
                                       for finding in moved["findings"]),
             moved["findings"]),
            ("M1's capture fails the current pins on the kernel alone",
             moved1["findings"] and all(" is not the pin 0x" in finding
                                        for finding in moved1["findings"]),
             moved1["findings"]),
            ("a domain line is never terminal",
             verdict == "FAIL" and short["terminal"] == "none",
             short["findings"]),
            ("board anchor stop 6 (Plan revision M2-A): the probe in hart "
             "2's request 1's wait among the costs, the counts as recorded",
             waited_verdict == "PASS" and {
                 key: value for key, value in waited["costs"].items()
                 if "_ping_" in key} == BOARD_PING_WAIT_COSTS and all(
                     waited["fields"].get(key) == value for key, value in
                     BOARD_PING_WAIT_COUNTS.items()), waited["findings"]),
            ("the uboot fixtures, uboot_form's of their sources",
             all(uboot_fixture(name) == fixture(name)
                 for name in UBOOT_FIXTURES), []),
            ("the board's U-Boot facts, as its lines give them",
             all(on_board["fields"].get(key) == value for key, value in
                 dict(BOARD_UBOOT_FACTS, fdt="0x00000002fbd6b000").items()),
             on_board["findings"]),
            ("QEMU's U-Boot facts, the boot hart the banner's",
             all(in_qemu["fields"].get(key) == value
                 for key, value in qemu_facts.items()),
             in_qemu["findings"]),
            ("M7-4: hostile, a forged run line bare, as hart 0's",
             any("a forged line as hart 0's" in finding
                 for finding in bare_run["findings"]),
             bare_run["findings"]),
            ("M7-4: hostile, a forged prefix bare, as G1's",
             any("a forged line as G1's" in finding
                 for finding in bare_prefix["findings"]),
             bare_prefix["findings"]),
            ("M7-4: the input table: no focus, a literal ~, an ungranted "
             "digit, bad sequences (a digit of no domain among them), a "
             "selection again, CR and LF",
             (bytes(model[0]), bytes(model[1]), selected, firsts,
              {key: value for key, value in drops.items() if value}) ==
             (b"~a\rb\r\n", b"", [0, 0], ["no-focus", "no-grant",
                                           "bad-sequence"],
              {"no-focus": 7, "no-grant": 1, "bad-sequence": 2}),
             [model, drops, selected, firsts])):
        checks += 1
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}"
              f"{'' if ok else ' ' + str(findings[:3])}")
    # M9's log (planning/mvp-m9-plan.md, D-4): tests/log_module.py's cases
    # (the profile's vectors, the round trip, the reader, the expectation's
    # section, and the plan's five kinds of negatives, each reference
    # frozen), then the checker's wiring on M9's fixtures, each reference
    # the build's; and M9's fixtures by run class, each as declared.
    print("BE_MVP_LOG_FIXTURES: " + " ".join(
        f"{run}={count}" + ("" if ok else "-not-as-declared")
        for (run, ok), count in sorted(classes.items(), key=str)))
    kinds = {}
    for kind, name, ok, detail in LOG.self_cases() + m9_cases(
            latest, reports, pins, root):
        checks += 1
        failed += not ok
        kinds[kind] = kinds.get(kind, 0) + 1
        print(f"{'ok  ' if ok else 'FAIL'} log [{kind}] {name}"
              f"{'' if ok else ' ' + str(detail)[:300]}")
    print("BE_MVP_LOG_CASES: " + " ".join(
        f"{kind}={count}" for kind, count in sorted(kinds.items())))
    total = len(cases) + checks
    print(f"BE_MVP_CAPTURE_SELF_TEST: {'PASS' if not failed else 'FAIL'} "
          f"cases={total} failed={failed}")
    return 0 if not failed else 1

# ----------------------------------------------------------- mutation test
MUTATION_SEED = 0x4d30   # "M0"


def g(domain, body):
    return f"BE_MVP_G{domain}: {body}"


def named_mutations():
    """(claim, base, name, mutated text, a finding the rejection names)."""
    two = fixture("qemu-two-guests-gcc")
    hart6 = fixture("qemu-two-guests-clang-hart6")
    kexec = kexec_form(two)
    fallback = fixture("qemu-ring-full-gcc")
    rdcycle = fixture("qemu-rdcycle-clang")
    payload = fixture("qemu-payload-gcc")
    refused = fixture("qemu-plic-gcc-refused")
    platform = fixture("qemu-probe-platform-gcc")
    shut0 = "BE_MVP:12 DOMAIN_SHUTDOWN hart=1 domain=0"
    shut1 = "BE_MVP:12 DOMAIN_SHUTDOWN hart=2 domain=1"
    command = "Kernel command line:"
    late = g(0, "[    9.000000] late")
    return [
        ("missing line", "two", "a control line, BE_MVP:05 for G1",
         delete(two, "BE_MVP:05 DOMAIN_RAM_CLEARED domain=1"),
         "order expects"),
        ("missing line", "two", "an R3 line", delete(two, "BE_R3:04"),
         "order expects"),
        ("missing line", "two", "the SHIM line", delete(two, SHIM_TAG),
         "no BE_K3_B3 SHIM line"),
        ("missing line", "two", "G1's RESULT line",
         delete(two, g(1, "MVPINIT 05 RESULT pass")), "G1 lacks"),
        ("missing line", "two", "G0's power-down line",
         delete(two, g(0, "[    1.729012] reboot: Power down")), "G0 lacks"),
        ("missing line", "two", "G0's Sstc timer line",
         delete(two, g(0, "[    0.001044] riscv-timer")), "G0 lacks"),
        ("binding", "two", "BE_MVP:09 naming another hart",
         replace_in(two, "BE_MVP:09 HART_READY hart=1", "hart=1", "hart=3"),
         "is not 'BE_MVP:09"),
        ("binding", "two", "BE_MVP:12 naming another hart",
         replace_in(two, shut1, "hart=2", "hart=1"), "binding names"),
        ("binding", "two", "BE_MVP:10 naming the other domain",
         replace_in(two, "BE_MVP:10 DOMAIN_ENTERED hart=2", "domain=1",
                    "domain=0"), "order expects"),
        ("binding", "two", "BE_MVP:03 with G1's VMID for G0",
         replace_in(two, "BE_MVP:03 GSTAGE_BUILT_REWALKED domain=0", "vmid=1",
                    "vmid=2"), "is not 'BE_MVP:03"),
        ("binding", "two", "G1's command line under G0's prefix",
         replace_in(two, g(1, "[    0.000000] " + command), "BE_MVP_G1: ",
                    "BE_MVP_G0: "), "names guest '1'"),
        ("mixed line", "two", "two domains' lines in one",
         replace_in(two, g(0, "[    0.000000] Zone ranges:"), "ranges:",
                    "ranges:" + g(1, "[    0.000000] Zone ranges:")),
         "mixed line"),
        ("mixed line", "two", "two init lines in one",
         replace_in(two, g(0, "MVPINIT 05 RESULT pass"), "pass",
                    "passMVPINIT 06 POWER_OFF"), "mixed G0 line"),
        ("mixed line", "two", "a kernel timestamp inside a line",
         replace_in(two, g(1, "[    0.000000] Zone ranges:"), "ranges:",
                    "ranges: [    0.000001] x"), "mixed G1 line"),
        ("mixed line", "two", "a domain prefix inside a control line",
         replace_in(two, "BE_MVP:13 ", "ticks=", g(0, "ticks=")),
         "mixed line"),
        ("overlap floor", "two", "the overlap below half the shorter",
         narrow_overlap(two), "overlap floor"),
        ("alternations", "two", "the domains' lines in two blocks",
         two_blocks(two), "alternations"),
        ("ipi=1", "two", "G0's shutdown without its IPI",
         replace_in(replace_in(two, shut0, "ipi=1", "ipi=0"), shut0,
                    "exits=157", "exits=156"), "ipi=0"),
        ("sums", "two", "sbi not the sum of the classes",
         replace_in(two, shut0, "sbi=156", "sbi=155"), "sum"),
        ("sums", "two", "exits not sbi + ipi",
         replace_in(two, shut1, "exits=157", "exits=158"), "sbi + ipi"),
        ("sums", "two", "records not the drained lines",
         replace_in(two, "BE_MVP:13 ", "records=138", "records=137"),
         "records=137"),
        ("sums", "two", "lines not the printed lines",
         replace_in(two, shut0, "lines=65", "lines=66"), "lines printed"),
        ("sums", "two", "overlap_ticks not the intervals'",
         replace_in(two, "BE_MVP:13 ", "overlap_ticks=0x28bfe93",
                    "overlap_ticks=0x28bfe94"), "overlap_ticks"),
        ("one shutdown", "two", "G1's shutdown missing",
         delete(two, shut1), "before 'BE_MVP:12"),
        ("one shutdown", "two", "BE_MVP:14 missing",
         delete(two, "BE_MVP:14 "), "stops before"),
        ("after :14", "two", "a control line after BE_MVP:14",
         two + "BE_MVP:13 RUN_COMPLETE\n", "order expects nothing"),
        ("after :14", "two", "a domain line after BE_MVP:14",
         two + late + "\n", "after its BE_MVP:12"),
        ("after :14", "two", "BE_MVP:14 twice",
         two + "BE_MVP:14 SHUTDOWN type=0 reason=0\n",
         "order expects nothing"),
        ("started", "two", "started=3 with no start rule",
         replace_in(two, "BE_MVP:02 ", "3:1", "3:0").replace(
             "started=none", "started=3"), "started=3"),
        ("started", "hart6", "started=none with the start rule",
         replace_in(hart6, "BE_MVP:02 ", "started=6", "started=none"),
         "started=none"),
        ("started", "hart6", "started= not the shim's boot hart",
         replace_in(replace_in(hart6, "BE_MVP:02 ", "started=6",
                               "started=5"), "BE_MVP:02 ", "5:1", "5:0"),
         "started=5"),
        ("started", "hart6", "no start-rule line for boot hart 6",
         delete(hart6, RULE_TAG), "boot hart is 6"),
        ("started", "hart6", "the start rule naming another hart",
         replace_in(hart6, RULE_TAG, "0x6", "0x5"), "boot hart is 6"),
        ("started", "two", "a STARTED hart with started=none",
         replace_in(two, "BE_MVP:02 ", "4:1", "4:0"), "hart 4 status 0"),
        ("failure", "two", "a FAIL among a passing run's lines",
         insert(two, "BE_MVP:13 ", "BE_MVP:FAIL ring", after=False),
         "order expects"),
        ("marker", "two", "BE_MVP:01 without the MVP region",
         replace_in(two, "BE_MVP:01 ", " mvp_region=0x102064000", ""),
         "is not 'BE_MVP:01"),
        ("stop 3", "two", "a ring high-water mark above half",
         replace_in(two, shut0, "ring_peak=0xd0", "ring_peak=0x4008"),
         "stop condition 3"),
        ("counter", "two", "G0 using SBI TIME",
         replace_in(replace_in(replace_in(two, shut0, "time=0", "time=1"),
                               shut0, "sbi=156", "sbi=157"), shut0,
                    "exits=157", "exits=158"), "time=1"),
        ("marker", "two", "an IPI probe answered outside V=1",
         replace_in(two, "BE_MVP:11 IPI_PROBE hart=1", "spv=1", "spv=0"),
         "is not 'BE_MVP:11"),
        ("spv", "two", "an IPI probe answered in HS, with no management "
         "extension",
         replace_in(two, "BE_MVP:11 IPI_PROBE hart=2", "spv=1", "spv=0"),
         "the image has no management extension"),
        ("marker", "two", "hedeleg not a WARL reading",
         replace_in(two, "BE_MVP:09 HART_READY hart=2", "hedeleg=0xb15d",
                    "hedeleg=0xb15f"), "WARL"),
        ("marker", "two", "kernel_bytes not the pin",
         replace_in(two, "BE_MVP:04 ", "kernel_bytes=0x17b3b4",
                    "kernel_bytes=0x17b3b8"), "is not the pin"),
        ("marker", "two", "BE_MVP:10 ticks not G0's entered",
         replace_in(two, "BE_MVP:10 DOMAIN_ENTERED hart=1", "ticks=0xc934",
                    "ticks=0xc935"), "is not its BE_MVP:10 ticks"),
        ("console", "two", "untagged text among the markers",
         insert(two, "BE_MVP:13 ", "stray text", after=False),
         "untagged text"),
        ("console", "two", "text before a marker",
         replace_in(two, "BE_MVP:07 ", "BE_MVP:07", "x BE_MVP:07"),
         "text before the marker"),
        ("console", "two", "a byte outside 0x20-0x7e",
         replace_in(two, g(0, "[    0.000000] Zone ranges:"), "Zone",
                    "Zo\x01e"), "non-printable"),
        ("console", "two", "a line longer than the line buffer",
         replace_in(two, g(0, "[    0.000000] Zone ranges:"), "ranges:",
                    "ranges:" + "x" * 300), "line buffer"),
        ("console", "two", "the capture cut mid-line",
         cut(two, 20), "ends mid-line"),
        ("rejected", "two", "a rejected substring in a domain line",
         replace_in(two, g(1, "[    0.000000] Zone ranges:"), "Zone",
                    "Oops Zone"), "rejected 'Oops'"),
        ("domain", "two", "a STEP line out of order",
         replace_in(replace_in(two, g(0, "MVPINIT 03 STEP n=3/8"), "n=3/8",
                               "n=9/8"), g(0, "MVPINIT 03 STEP n=4/8"),
                    "n=4/8", "n=3/8"), "G0"),
        ("domain", "two", "an init line twice",
         insert(two, g(1, "MVPINIT 05 RESULT pass"),
                g(1, "MVPINIT 05 RESULT pass")), "appears 2 times"),
        ("domain", "two", "memory beyond the window",
         replace_in(two, g(0, "[    0.024882] Memory:"), "62008K/",
                    "70000K/"), "exceeds"),
        ("cross-stream", "two", "G0's BE_MVP:11 before its first line",
         insert(delete(two, "BE_MVP:11 IPI_PROBE hart=1"),
                "BE_MVP:10 DOMAIN_ENTERED hart=1",
                lines(two)[where(lines(two), "BE_MVP:11 IPI_PROBE hart=1")]),
         "before its first line"),
        ("cross-stream", "two", "a G1 line before G1's BE_MVP:10",
         insert(delete(two, g(1, "[    0.000000] Linux version")),
                "BE_MVP:08 HART_STARTED hart=2",
                lines(two)[where(lines(two), g(1, "[    0.000000] Linux "
                                                 "version"))]),
         "before its BE_MVP:10"),
        ("firmware", "two", "another SBI version in the banner",
         replace_in(two, "Runtime SBI Version", "2.0", "3.0"),
         "SBI version"),
        ("kexec", "kexec", "the handoff FDT not the loader's",
         kexec.replace("FDT image at 108400000", "FDT image at 108600000"),
         "is not the loader's"),
        ("kexec", "kexec", "the kexec from hart 3 without the start rule",
         kexec.replace("from hart id 0", "from hart id 3"), "boot hart is 3"),
        ("kexec", "kexec", "no Bye...", kexec.replace("Bye...", "Bye"),
         "'bye' lines"),
        ("kexec", "kexec", "the kexec entry not L",
         kexec.replace("new kernel at 108000000", "new kernel at 102000000"),
         "kexec entry"),
        ("kexec", "kexec", "the shim's FDT not the handoff's",
         re.sub(r"(?<=SHIM hart=0x0{16} shim=0x0000000108000000 fdt=0x)"
                r"[0-9a-f]{16}", "0000000108600000", kexec),
         "not the handoff's"),
        ("fallback", "fallback", "a domain line before the fallback",
         insert(fallback, "BE_MVP:10 DOMAIN_ENTERED hart=2",
                g(1, "[    0.000000] Linux version 7.2.0")),
         "domain line before the fallback"),
        ("fallback", "fallback", "BE_MVP:11 before the fallback",
         insert(fallback, "BE_MVP:10 DOMAIN_ENTERED ",
                "BE_MVP:11 IPI_PROBE hart=1 domain=0 sent=0x1 received=0x2 "
                "answered=0x3 spv=1", 1), "BE_MVP:11 before the first FAIL"),
        ("fallback", "fallback", "a DETAIL naming no domain hart",
         replace_in(fallback, "BE_MVP:DETAIL domain=0", "hart=1", "hart=0"),
         "does not name a domain hart"),
        ("fallback", "fallback", "another class first",
         replace_in(fallback, "BE_MVP:FAIL ring", "ring", "ipi"),
         "expected 'BE_MVP:FAIL ring'"),
        ("fallback", "fallback", "no DETAIL at all",
         delete(delete(fallback, "BE_MVP:DETAIL "), "BE_MVP:DETAIL "),
         "0 DETAIL"),
        ("fallback", "fallback", "a third FAIL",
         fallback + "BE_MVP:FAIL ring\n", "3 fallback FAIL"),
        ("fallback", "fallback", "hart 0's shutdown after the fallback",
         fallback + "BE_MVP:14 SHUTDOWN type=0 reason=0\n",
         "fallback line"),
        ("failure", "rdcycle", "the DETAIL naming the other domain",
         replace_in(rdcycle, "BE_MVP:DETAIL ", "domain=0 hart=1",
                    "domain=1 hart=2"), "names domain 1, expected 0"),
        ("failure", "rdcycle", "a cause that does not fit",
         replace_in(rdcycle, "BE_MVP:DETAIL ", "cause=0x16", "cause=0x2"),
         "does not fit"),
        ("failure", "rdcycle", "the DETAIL missing",
         delete(rdcycle, "BE_MVP:DETAIL "), "needs a BE_MVP:DETAIL"),
        ("failure", "rdcycle", "a line after the failure",
         rdcycle + "BE_MVP:12 DOMAIN_SHUTDOWN\n", "after the failure"),
        ("failure", "rdcycle", "another class",
         replace_in(rdcycle, "BE_MVP:FAIL ", "virtual-instruction",
                    "illegal-instruction"), "expected 'BE_MVP:FAIL"),
        ("failure", "rdcycle", "a domain line after the failure",
         rdcycle + late + "\n", "after the failure"),
        ("failure", "payload", "the failure after a later line",
         insert(payload, "BE_MVP:FAIL ", "BE_MVP:04 PAYLOAD_CHECKED "
                "kernel_bytes=0x17b3b4 image_size=0x1af628", after=False),
         "expected BE_MVP:03"),
        ("failure", "payload", "the failure before its line",
         delete(payload, "BE_MVP:03 GSTAGE_BUILT_REWALKED domain=1"),
         "precedes the end of BE_MVP:03"),
        ("failure", "payload", "a DETAIL for a class that takes none",
         insert(payload, "BE_MVP:FAIL ", "BE_MVP:DETAIL ticks=0x1"),
         "takes no BE_MVP:DETAIL"),
        ("refusal", "refused", "a FAIL firmware with no domain hart's boot",
         replace_in(replace_in(replace_in(refused, RULE_TAG, "0x1", "0x3"),
                               "BE_MVP:02 ", "1:0,", "1:1,"), "BE_MVP:02 ",
                    "3:1,", "3:0,").replace("started=1", "started=3"),
         "order expects"),
        ("refusal", "refused", "a refusal after BE_MVP:03",
         insert(refused, "BE_MVP:FAIL firmware",
                "BE_MVP:03 GSTAGE_BUILT_REWALKED domain=0", after=False),
         "does not follow BE_MVP:02"),
        ("refusal", "refused", "the refused hart not BE_MVP:02's",
         replace_in(refused, "BE_MVP:02 ", "started=1", "started=none"),
         "no declared refusal"),
        ("probe", "platform", "a probe line missing",
         delete(platform, "PROBE gpf access=store"), "order expects"),
        ("probe", "platform", "the IPI lines swapped",
         replace_in(replace_in(platform, "PROBE ipi mode=hs", "mode=hs",
                               "mode=xx"), "PROBE ipi mode=vs", "mode=vs",
                    "mode=hs").replace("mode=xx", "mode=vs"), "is not"),
        ("probe", "platform", "a domain line in a probe run",
         insert(platform, "BE_MVP:10 ", g(0, "[    0.000000] x")),
         "domain line"),
        ("probe", "platform", "the probe's BE_MVP:14 missing",
         delete(platform, "BE_MVP:14 "), "stops before"),
    ]


def prelude_mutations():
    """The prelude's rows (planning/mvp-m6-plan.md, D-3): exactly one form,
    whole, before BE_MVP:01, on M6's passing captures and M0's."""
    two, m6two = fixture("qemu-two-guests-gcc"), fixture(M6_FIXTURES[
        "two-guests"])
    valid, sealed = f"{CORE_PRELUDE} BOOT_VALIDATED", \
        f"{CORE_PRELUDE} CONFIG_SEALED"
    identity = re.search(r" identity=([0-9a-f]{16})", m6two).group(1)
    parts = lines(m6two)
    both = text_of(parts[:where(parts, valid)] + list(R3_PRELUDE) +
                   parts[where(parts, valid):])
    after = text_of(parts[:where(parts, sealed) + 1] + list(R3_PRELUDE) +
                    parts[where(parts, sealed) + 1:])
    return [
        ("prelude", "m6two", "BOOT_VALIDATED missing", delete(m6two, valid),
         "order expects"),
        ("prelude", "m6two", "CONFIG_SEALED missing", delete(m6two, sealed),
         "order expects"),
        ("prelude", "m6two", "the two lines swapped",
         swap(m6two, valid, sealed), "order expects"),
        ("prelude", "m6two", "CONFIG_SEALED's identity one digit off",
         replace_in(m6two, sealed, identity,
                    identity[:-1] + "0123456789abcdef"[
                        (int(identity[-1], 16) + 1) % 16]), "is not"),
        ("prelude", "m6two", "CONFIG_SEALED's inventory count",
         replace_in(m6two, sealed, "inventory=14", "inventory=13"), "is not"),
        ("prelude", "m6two", "CONFIG_SEALED's domain harts swapped",
         replace_in(m6two, sealed, "harts=0,1,2", "harts=0,2,1"), "is not"),
        ("prelude", "m6two", "R3's form before the MVP's", both,
         "order expects"),
        ("prelude", "m6two", "R3's form after the MVP's", after,
         "order expects"),
        ("prelude", "two", "the MVP's BOOT_VALIDATED among R3's lines",
         insert(two, "BE_R3:03 ", valid), "order expects"),
        ("prelude", "two", "R3's form without BE_R3:06",
         delete(two, "BE_R3:06 "), "order expects"),
    ]


BASES = {"two": ("qemu-two-guests-gcc", "two-guests", "direct"),
         "hart6": ("qemu-two-guests-clang-hart6", "two-guests", "direct"),
         "kexec": ("qemu-two-guests-gcc", "two-guests", "kexec"),
         "fallback": ("qemu-ring-full-gcc", "ring-full", "direct"),
         "rdcycle": ("qemu-rdcycle-clang", "rdcycle", "direct"),
         "payload": ("qemu-payload-gcc", "payload", "direct"),
         "refused": ("qemu-plic-gcc-refused", "two-guests", "direct"),
         "platform": ("qemu-probe-platform-gcc", "probe-platform",
                      "direct"),
         "tepoc": ("qemu-te-poc-gcc", "te-poc", "direct"),
         "anchor": (ANCHOR_FIXTURES["anchor"], "anchor", "direct"),
         "wrongm": (ANCHOR_FIXTURES["wrong-measurement"],
                    "wrong-measurement", "direct"),
         "ngc": (ANCHOR_FIXTURES["no-grant-check"], "no-grant-check",
                 "direct"),
         "k3anchor": (BOARD_PING_WAIT, "anchor", "kexec"),
         "uboot": (BOARD_UBOOT, "two-guests", "uboot"),
         "quboot": (QEMU_UBOOT, "two-guests", "uboot"),
         "m6two": (M6_FIXTURES["two-guests"], "two-guests", "direct"),
         "m6tepoc": (M6_FIXTURES["te-poc"], "te-poc", "direct"),
         "m6anchor": (M6_FIXTURES["anchor"], "anchor", "direct"),
         "m7two": (M7_FIXTURES["two-guests"], "two-guests", "direct"),
         "m7tepoc": (M7_FIXTURES["te-poc"], "te-poc", "direct"),
         "m7anchor": (M7_FIXTURES["anchor"], "anchor", "direct"),
         "m7input": (M7_FIXTURES["probe-console-input"],
                     "probe-console-input", "kexec"),
         "m74two": (SESSION_FIXTURES["two-guests-shell"], "two-guests-shell",
                    "direct"),
         "m74tepoc": (SESSION_FIXTURES["te-poc-shell"], "te-poc-shell",
                      "direct"),
         "m74anchor": (SESSION_FIXTURES["anchor-shell"], "anchor-shell",
                       "direct"),
         "m74hostile": (HOSTILE_FIXTURE, "hostile", "direct"),
         "m9two": (M9_FIXTURES["two-guests"], "two-guests", "direct"),
         "m9tepoc": (M9_FIXTURES["te-poc"], "te-poc", "direct"),
         "m9anchor": (M9_FIXTURES["anchor"], "anchor", "direct"),
         "m9wrongm": (M9_FIXTURES["wrong-measurement"],
                      "wrong-measurement", "direct"),
         "m9flip": (M9_FIXTURES["self-report-flip"], "self-report-flip",
                    "direct"),
         "c9two": (M9_FIXTURES["two-guests"], "two-guests", "direct"),
         "c9tepoc": (M9_FIXTURES["te-poc"], "te-poc", "direct"),
         "c9anchor": (M9_FIXTURES["anchor"], "anchor", "direct"),
         "c9wrongm": (M9_FIXTURES["wrong-measurement"],
                      "wrong-measurement", "direct"),
         "c9flip": (M9_FIXTURES["self-report-flip"], "self-report-flip",
                    "direct")}
# Each mode's options, or a base's own (the uboot fixtures' images).
BASE_OPTIONS = {"direct": {"sbi_version": "2.0"},
                "kexec": {"kexec_fdt": STAGING + align_up(BOARD_IMAGE_BYTES,
                                                          FDT_ALIGN)},
                "uboot": uboot_options(BOARD_UBOOT),
                "quboot": uboot_options(QEMU_UBOOT)}


def seeded_mutations(seed=MUTATION_SEED, current=None):
    """Single defects at seeded places: a line of either stream deleted or
    repeated, two neighbouring fixed lines swapped, the capture cut short
    at a line, and stray text inserted."""
    chooser = random.Random(seed)
    out = []
    for base in ("two", "hart6", "kexec", "anchor", "uboot", "m6two",
                 "m7two", "m74tepoc", "c9tepoc", "c9anchor"):
        text = kexec_form(fixture(BASES[base][0])) if base == "kexec" \
            else fixture(BASES[base][0])
        if base.startswith("c9"):
            text = current(BASES[base][1], text)
        parts = text.split("\n")
        first = next(index for index, line in enumerate(parts)
                     if line.startswith((RULE_TAG, SHIM_TAG)))
        marked = [index for index in range(first, len(parts) - 1)
                  if parts[index].strip()]
        monitor = [index for index in marked
                   if not parts[index].startswith("BE_MVP_G")]
        domain = [index for index in marked
                  if parts[index].startswith("BE_MVP_G")]
        prelude = [index for index in monitor
                   if index + 1 in monitor and
                   key_of(parts[index].strip("\r")) !=
                   key_of(parts[index + 1].strip("\r")) and
                   not parts[index].startswith(("BE_MVP:09", "BE_MVP:1"))]
        for index in chooser.sample(monitor, 6):
            out.append((base, f"monitor line {index + 1} deleted",
                        "\n".join(parts[:index] + parts[index + 1:])))
        for index in chooser.sample(domain, 6):
            out.append((base, f"domain line {index + 1} deleted",
                        "\n".join(parts[:index] + parts[index + 1:])))
        for index in chooser.sample(domain + monitor, 4):
            out.append((base, f"line {index + 1} repeated",
                        "\n".join(parts[:index + 1] + parts[index:])))
        for index in chooser.sample(prelude, 3):
            out.append((base, f"lines {index + 1} and {index + 2} swapped",
                        "\n".join(parts[:index] + [parts[index + 1],
                                                   parts[index]] +
                                  parts[index + 2:])))
        for index in chooser.sample(marked[:-1], 3):
            out.append((base, f"cut after line {index + 1}",
                        "\n".join(parts[:index + 1]) + "\n"))
        for index in chooser.sample(marked, 2):
            out.append((base, f"stray text before line {index + 1}",
                        "\n".join(parts[:index] + ["stray"] + parts[index:])))
    return out


def swap(text, first, second):
    parts = lines(text)
    one, other = where(parts, first), where(parts, second)
    parts[one], parts[other] = parts[other], parts[one]
    return text_of(parts)


def move_after(text, needle, anchor):
    parts = lines(text)
    moved = parts.pop(where(parts, needle))
    parts.insert(where(parts, anchor) + 1, moved)
    return text_of(parts)


def te_poc_mutations(report):
    """The plan's capture rows (planning/mvp-m1-plan.md, "Scenarios and the
    harness", Mutations), on the passing te-poc capture: (claim, base,
    name, text, a finding the rejection names, the report's bytes)."""
    tepoc = fixture("qemu-te-poc-gcc")
    deny0 = "BE_MVP:DENY hart=1 domain=0 seq=1"
    deny1 = "BE_MVP:DENY hart=2 domain=1 seq=1"
    deny2 = "BE_MVP:DENY hart=2 domain=1 seq=2"
    load0 = g(0, "MVPINIT 08 DENIED n=1")
    store1 = g(1, "MVPINIT 08 DENIED n=1")
    reader = g(1, "MVPINIT 07 CHANNEL")
    checked = "BE_MVP:03 CHANNEL_CHECKED "
    parsed = json.loads(report)
    seventh = dict(parsed, grants=parsed["grants"] + parsed["grants"][:1])
    undeclared = dict(parsed, flows=[dict(parsed["flows"][0],
                                          declared="no")])
    rows = [
        ("the log carries the fields the guest reports",
         "a DENY line's gpa changed",
         replace_in(tepoc, deny0, "gpa=0x84001000", "gpa=0x84001008"),
         "the DENY line's gpa=0x84001008"),
        ("every denied access appears exactly once", "a DENY line removed",
         delete(tepoc, deny0), "0 BE_MVP:DENY lines"),
        ("exactly once", "a DENY line duplicated",
         insert(tepoc, deny0, lines(tepoc)[where(lines(tepoc), deny0)]),
         "2 BE_MVP:DENY lines"),
        ("delivered as the corresponding access fault",
         "a load's injected=0x7",
         replace_in(tepoc, deny0, "injected=0x5", "injected=0x7"),
         "not the access fault for the expected load"),
        ("in the order the guest reports them", "G1's two DENY lines swapped",
         swap(tepoc, deny1, deny2), "the order the guest reports"),
        ("the kind follows the sealed record",
         "kind=read-only at a GPA outside the channel page",
         replace_in(tepoc, deny0, "kind=unmapped", "kind=read-only"),
         "is not the sealed record's unmapped"),
        ("the guest observed the logged fault", "a guest report's pc changed",
         replace_in(tepoc, load0, "pc=0x112bc", "pc=0x112c0"),
         "are not the report's"),
        ("the record precedes the resume", "a DENY line moved after its "
         "report", move_after(tepoc, deny0, load0),
         "the record precedes the resume"),
        ("the alias-rejecting comparison", "htval with bit 39 set",
         replace_in(tepoc, deny0, "htval=0x21000400", "htval=0x8021000400"),
         "compared as 64-bit values"),
        ("data crosses from the writer to the reader", "the reader's match=0",
         replace_in(tepoc, reader, "match=1", "match=0"),
         "the reader shows match=0"),
        ("data crosses from the writer to the reader",
         "the digests differing",
         replace_in(tepoc, reader, "digest=0xeacaea8433f5c641",
                    "digest=0xeacaea8433f5c640"), "and the reader's"),
        ("the denied store changed nothing", "the reader's unchanged=0",
         replace_in(tepoc, store1, "unchanged=1", "unchanged=0"),
         "unchanged=0: the denied store changed the page"),
        ("the reader's root maps the page read-only", "reader_pte=0x460000d7",
         replace_in(tepoc, checked, "reader_pte=0x46000053",
                    "reader_pte=0x460000d7"),
         "CHANNEL_CHECKED reader_pte=0x460000d7"),
        ("the boot-time re-walk is the report's configuration",
         "one digit of config changed",
         replace_in(tepoc, checked, "config=9cf0", "config=9cf1"),
         "is not the report's configuration identity"),
    ]
    out = [(claim, "tepoc", name, text, wanted, report)
           for claim, name, text, wanted in rows]
    out += [("exactly Instance 2's grants", "tepoc",
             "a report with a seventh grant", tepoc,
             "7 grants, not Instance 2's 6",
             json.dumps(seventh, sort_keys=True).encode()),
            ("one flow, writer_t -> reader_t, declared", "tepoc",
             "a report flow with declared: no", tepoc,
             "are not the expectation's one declared flow",
             json.dumps(undeclared, sort_keys=True).encode())]
    return out


def anchor_mutations(report):
    """The plan's new capture rules (planning/mvp-m2-plan.md, "Scenarios
    and the harness", "Mutations cover each new rule"), each a single
    defect of anchor's passing capture or of its negatives', and Plan
    revision M2-A.2's, of the first M2 board campaign's anchor capture
    too: (claim, base, name, text, a finding the rejection names, the
    report's bytes)."""
    anchor = fixture(ANCHOR_FIXTURES["anchor"])
    wrong = fixture(ANCHOR_FIXTURES["wrong-measurement"])
    ngc = fixture(ANCHOR_FIXTURES["no-grant-check"])
    board = fixture(BOARD_PING_WAIT)
    first, last = BOARD_PING_WAIT_SPAN
    probe = "BE_MVP:11 IPI_PROBE hart=2"
    mgmt = "BE_MVP:MGMT hart=1 domain=0 seq="
    shutdown = "BE_MVP:12 DOMAIN_SHUTDOWN"
    ended = "BE_MVP:12 DOMAIN_TERMINATED"
    measured = "BE_MVP:06 MEASURED"
    digest3 = ("6c3197da22d3a0797ae901b5b72d996e"
               "562b6a96bad43cd0173efa1e4767ea97")
    parsed = json.loads(report)
    narrowed = dict(parsed, grants=[
        dict(grant, permissions=["pause"]) if grant["class"] == "domain"
        else grant for grant in parsed["grants"]])
    rows = [
        ("anchor", "the digests are each request's HMAC-SHA-256",
         "a REQUEST's digest one digit off",
         replace_in(anchor, g(0, "MVPINIT 09 REQUEST n=2 "), "digest=42c7",
                    "digest=42c8"), "is not the HMAC-SHA-256"),
        ("anchor", "the two sides' digests equal",
         "a RESPONSE's digest one digit off",
         replace_in(anchor, g(1, "MVPINIT 09 RESPONSE n=3 "), "digest=6c31",
                    "digest=6c32"), "and the server's"),
        ("anchor", "the unanswered request only after the pause",
         "the timeout before the pause's report",
         move_after(anchor, g(0, "MVPINIT 09 REQUEST n=5 timeout=1"),
                    g(0, "MVPINIT 10 MGMT burst=8 ")),
         "timeout precedes the report of request 12"),
        ("anchor", "the unanswered request is never answered",
         "a response to the fifth request",
         insert(anchor, g(1, "MVPINIT 09 RESPONSE n=4 "),
                g(1, "MVPINIT 09 RESPONSE n=5 digest=" + digest3)),
         "which is unanswered"),
        ("anchor", "every request on hart 0 exactly once",
         "a BE_MVP:MGMT line removed", delete(anchor, f"{mgmt}3 "),
         "12 BE_MVP:MGMT lines"),
        ("anchor", "each request's result as the guest reports it",
         "a denied request's result -3 for -4",
         replace_in(anchor, f"{mgmt}1 ", "result=-4", "result=-3"),
         "is not the call G0 reports"),
        ("anchor", "the requests in the guest's order",
         "two requests' lines swapped",
         swap(anchor, f"{mgmt}1 ", f"{mgmt}2 "), "seq=2, not 1"),
        ("anchor", "hart 0 decides before the call returns",
         "a request's line after its call's report",
         move_after(anchor, f"{mgmt}3 ",
                    g(0, "MVPINIT 10 MGMT fid=pause target=2 ")),
         "follows the report of its call"),
        ("anchor", "a delivered request after its target's transition",
         "the pause's line before DOMAIN_PAUSED",
         swap(anchor, "BE_MVP:12 DOMAIN_PAUSED", f"{mgmt}12 "),
         "without its target's transition by G0 before it"),
        ("anchor", "the burst stands for its count of calls",
         "a burst of 7 with 8 results",
         replace_in(anchor, g(0, "MVPINIT 10 MGMT burst=8 "), "burst=8",
                    "burst=7"), "a burst of 7 with 8 results"),
        ("anchor", "another FID is answered on its hart",
         "FID 7's request on hart 0",
         insert(anchor, g(0, "MVPINIT 10 MGMT fid=7 "),
                "BE_MVP:MGMT hart=1 domain=0 seq=4 fid=7 target=1 result=-2 "
                "target_state=- ticks=0x24d000 service=0x10", after=False),
         "which the requester's hart answers itself"),
        ("anchor", "another FID is answered -2",
         "FID 7 answered 0",
         replace_in(anchor, g(0, "MVPINIT 10 MGMT fid=7 "), "result=-2",
                    "result=0"), "returned 0, not -2"),
        ("anchor", "refused counts FID 7's call", "the host's refused=0",
         replace_in(anchor, shutdown, "refused=1", "refused=0"),
         "refused=0, expected exactly 1"),
        ("anchor", "sbi holds hart 0's requests (mgmt)",
         "sbi and exits one less",
         replace_in(replace_in(anchor, shutdown, "sbi=233", "sbi=232"),
                    shutdown, "exits=238", "exits=237"),
         "less its printed terms is 12, not mgmt=13"),
        ("anchor", "every request is a drained record",
         "records without the requests",
         replace_in(anchor, "BE_MVP:13 ", "records=174", "records=159"),
         "records=159 is not the 174"),
        ("anchor", "the measurement is the checker's own",
         "MEASURED one digit off",
         replace_in(anchor, measured, "sha256=e0c6", "sha256=e0c7"),
         "is not the checker's own"),
        ("anchor", "the measurement's bytes are its inputs'",
         "MEASURED with one byte more",
         replace_in(anchor, measured, "bytes=1907940", "bytes=1907941"),
         "is not the checker's own"),
        ("anchor", "DOMAIN_TERMINATED shows the measurement unaltered",
         "DOMAIN_TERMINATED's sha256 one digit off",
         replace_in(anchor, ended, "sha256=e0c6", "sha256=e0c7"),
         "is not the measurement, the checker's own"),
        ("anchor", "the paused hart takes no further exit",
         "DOMAIN_TERMINATED with one more exit",
         replace_in(anchor, ended, "exits=124", "exits=125"),
         "the paused hart took an exit"),
        ("anchor", "paused, terminated, the host's shutdown, the run's end",
         "DOMAIN_TERMINATED after the host's shutdown",
         move_after(anchor, ended, shutdown), "against the declared order"),
        ("anchor", "no guest line after its domain's end",
         "a G0 line after the host's shutdown",
         insert(anchor, shutdown, g(0, "[    2.800000] late")),
         "G0 line after its BE_MVP:12"),
        ("anchor", "the protected domain ends by termination",
         "a RESULT line from the protected domain",
         insert(anchor, g(1, "MVPINIT 09 RESPONSE n=4 "),
                g(1, "MVPINIT 05 RESULT pass")), "unexpected G1 init line"),
        ("anchor", "each page's check is the report's",
         "the secret page's leaf with W",
         replace_in(anchor, "BE_MVP:03 PAGE_CHECKED page=2",
                    "reader_pte=0x46000853", "reader_pte=0x460008d7"),
         "PAGE_CHECKED page=2 reader_pte=0x460008d7"),
        ("anchor", "the secret placed in the report's secret page",
         "SECRET_PLACED at the response page",
         replace_in(anchor, "BE_MVP:05 SECRET_PLACED", "hpa=0x118002000",
                    "hpa=0x118001000"), "is not the report's secret page 2"),
        ("wrongm", "the DETAIL's computed value is the checker's own",
         "computed= one digit off",
         replace_in(wrong, "BE_MVP:DETAIL ", "computed=e0c6",
                    "computed=e0c7"), "are not the checker's own"),
        ("ngc", "the variant's budget ran out",
         "the run-timeout DETAIL below 2^27 ticks",
         re.sub(r"BE_MVP:DETAIL ticks=0x[0-9a-f]+",
                "BE_MVP:DETAIL ticks=0x7ffffff", ngc),
         "are not at least the budget"),
        ("ngc", "the delivered terminate on hart 0 before the failure",
         "the protected domain's terminate 0 line removed",
         delete(ngc, "BE_MVP:MGMT hart=2 domain=1 seq=1 "),
         "of hart 0's lines before the failure are"),
        ("ngc", "the server answers only what was asked, in order",
         "a response to request 3 alone",
         replace_in(ngc, g(1, "MVPINIT 09 RESPONSE n=1 "),
                    "n=1 digest=cfa178e1a716ea360e7828e40d6d23fb0df925efc7d6"
                    "4693424ddfe8a0770251", f"n=3 digest={digest3}"),
         "not a first run of them"),
        ("ngc", "the host's lines a prefix of its own, with no gap",
         "a gap in the host's lines",
         delete(ngc, g(0, "MVPINIT 07 PAGES ")), "G0 lacks the required"),
        # Plan revision M2-A.1: spv=0 only inside a management wait of the
        # probe's own hart.
        ("anchor", "spv=0 only inside a management wait of its hart",
         "the protected domain's PONG spv=0 before its first request",
         replace_in(anchor, probe, "spv=1", "spv=0"),
         "lies in no management wait of hart 2"),
        ("k3anchor", "spv=0 only inside a management wait of its hart",
         "the board's PING received a tick before its request",
         probe_at(board, probe, first - 1),
         "lies in no management wait of hart 2"),
        ("k3anchor", "spv=0 only inside a management wait of its hart",
         "the board's PING received a tick after its answer",
         probe_at(board, probe, last + 1),
         "lies in no management wait of hart 2"),
        ("k3anchor", "spv=0 only inside a management wait of its hart",
         "the board's request whose wait holds the PING removed",
         delete(board, "BE_MVP:MGMT hart=2 domain=1 seq=1 "),
         "lies in no management wait of hart 2"),
    ]
    out = [(claim, base, name, text, wanted, report)
           for base, claim, name, text, wanted in rows]
    out.append(("exactly the instance's management grants", "anchor",
                "a report with pause alone", anchor,
                "the report's management grants",
                json.dumps(narrowed, sort_keys=True).encode()))
    return out


def forged_loader_block(text, digest, forged):
    """TEXT with a copy of its loader block, from its autoboot line to its
    `Starting kernel ...` line, inserted before its first marker line, the
    copy's DIGEST replaced by FORGED: what an image substituted after
    staging could print to pass off its own loader lines as U-Boot's."""
    lines = text.split("\n")
    start = next(index for index, line in enumerate(lines)
                 if UBOOT_AUTOBOOT.search(line))
    end = next(index for index, line in enumerate(lines)
               if "Starting kernel ..." in line)
    first = next(index for index, line in enumerate(lines)
                 if line.startswith((RULE_TAG, SHIM_TAG)))
    block = [line.replace(digest, forged) for line in lines[start:end + 1]]
    return "\n".join(lines[:first] + block + lines[first:])


def uboot_mutations():
    """The uboot mode's rules (planning/mvp-m5-plan.md, "Tests and
    evidence", Mutation), each a single defect of a uboot fixture, the
    board's (uboot) or QEMU's (quboot): (claim, base, name, text, a finding
    the rejection names)."""
    board, qemu = fixture(BOARD_UBOOT), fixture(QEMU_UBOOT)
    shim, banner = SHIM_TAG + "SHIM ", "U-Boot 2022.10 (May 21 2026 - "
    load, digest, moving = " bytes read in 33 ms", "md5 for ", "Moving Image"
    md5 = UBOOT_FIXTURES[BOARD_UBOOT][4]
    rows = [("uboot", f"the {name!r} line missing", delete(board, needle),
             f"0 U-Boot {name!r} lines")
            for name, needle in (("bytes read", load), ("digest", digest),
                                 ("Moving Image", moving),
                                 ("Flattened Device Tree", "## Flattened"),
                                 ("Booting using", "Booting using"),
                                 ("Device Tree", "Loading Device Tree"),
                                 ("Starting kernel", "Starting kernel"))]
    rows += [
        ("uboot", "the load not the image's size",
         replace_in(board, load, "2584576", "2580480"),
         "U-Boot read 2580480 bytes, not the image's 2584576"),
        ("uboot", "an MD5 not the image's",
         replace_in(board, digest, f"==> {md5}", f"==> {md5[:-1]}d"),
         f"md5 {md5[:-1]}d is not the image's {md5}"),
        ("uboot", "md5 from another address",
         replace_in(board, digest, "140000000 ... 140276fff",
                    "140001000 ... 140277fff"), "md5 starts at 0x140001000"),
        ("uboot", "md5 over another length than the load's",
         replace_in(board, digest, "... 140276fff", "... 140275fff"),
         "not the 2584576 bytes read"),
        ("uboot", "two digest lines, crc32's after md5sum's",
         insert(board, digest, "[   4.990] crc32 for 140000000 ... "
                "140276fff ==> 043fe676"), "2 U-Boot 'digest' lines"),
        ("uboot", "md5sum's line with a CRC-32's eight digits",
         replace_in(board, digest, f"==> {md5}", "==> 043fe676"),
         "U-Boot's md5 has 8 hexadecimal digits, not 32"),
        ("quboot", "a CRC-32 not the image's",
         replace_in(qemu, "crc32 for ", "==> de60ac10", "==> de60ac11"),
         "crc32 de60ac11 is not the image's de60ac10"),
        ("uboot", "booti's move to B3's 0x102200000",
         replace_in(board, moving, "to 0x108000000", "to 0x102200000"),
         "moved the image to 0x102200000, not L"),
        ("uboot", "booti's move from another address",
         replace_in(board, moving, "from 0x140000000", "from 0x140001000"),
         "moved the image from 0x140001000"),
        ("uboot", "booti's end not L + N",
         replace_in(board, moving, "end=108277000", "end=108278000"),
         "booti's end 0x108278000"),
        ("uboot", "the shim's fdt not U-Boot's device tree",
         replace_in(board, shim, "fdt=0x00000002fbd6b000",
                    "fdt=0x00000002fbd6c000"), "the shim's fdt"),
        ("uboot", "the device tree in the core",
         replace_in(replace_in(board, "Loading Device Tree",
                               "00000002fbd6b000, end 00000002fbd7d2ef",
                               "0000000102010000, end 00000001020222ef"),
                    shim, "fdt=0x00000002fbd6b000", "fdt=0x0000000102010000"),
         "overlaps the core"),
        ("uboot", "the device tree ending before it starts",
         replace_in(board, "Loading Device Tree", "end 00000002fbd7d2ef",
                    "end 00000002fbd6a000"), "before its start"),
        ("uboot", "a second U-Boot banner",
         insert(board, "WDT:", banner + "07:43:32 +0000)"),
         "2 U-Boot banner lines"),
        ("uboot", "no SPL banner on the board", delete(board, "U-Boot SPL "),
         "0 U-Boot SPL banner lines"),
        ("uboot", "the shim on hart 1 on the board",
         replace_in(board, shim, "hart=0x0000000000000000",
                    "hart=0x0000000000000001"),
         "a board boot enters the shim on hart 0"),
        ("uboot", "the start rule on the board",
         insert(board, shim, RULE_TAG + "boot_hart=0x3 starting hart 0",
                after=False), "a board boot enters the shim on hart 0"),
        ("uboot", "the digest before the load", swap(board, load, digest),
         "the U-Boot boot lines are out of order"),
        ("uboot", "no autoboot line: env_k3.txt's load counts",
         delete(board, "Autoboot in "), "2 U-Boot 'bytes read' lines"),
        ("uboot", "no autoboot line, counted",
         delete(board, "Autoboot in "), "0 U-Boot autoboot lines"),
        ("uboot", "a forged loader block before the shim, with its own "
         "autoboot line and another MD5",
         forged_loader_block(board, md5, f"{md5[:-1]}d"),
         "2 U-Boot autoboot lines"),
        ("uboot", "a forged loader block before the shim, the MD5 repeated",
         forged_loader_block(board, md5, md5), "2 U-Boot autoboot lines"),
        ("quboot", "a forged loader block before the shim in QEMU",
         forged_loader_block(qemu, "de60ac10", "de60ac11"),
         "2 U-Boot autoboot lines"),
        ("uboot", "a line between Starting kernel ... and the shim",
         insert(board, "Starting kernel", "[   5.230] ## Loading kernel"),
         "between 'Starting kernel ...' and the markers"),
        ("quboot", "in place at another address than the blob",
         replace_in(replace_in(qemu, "Using Device Tree",
                               "00000000ff73a250, end",
                               "00000000ff73b250, end"),
                    shim, "fdt=0x00000000ff73a250", "fdt=0x00000000ff73b250"),
         "in place at 0xff73b250 is not the blob at 0xff73a250"),
        ("quboot", "another blob booted",
         replace_in(qemu, "Booting using", "0xff73a250", "0xff73a260"),
         "boots the fdt blob at 0xff73a260"),
        ("quboot", "two SPL banners in QEMU",
         insert(insert(qemu, "U-Boot 2022.10", "U-Boot SPL 2022.10 (Oct 03 "
                       "2022 - 19:25:32 +0000)", after=False),
                "U-Boot 2022.10", "U-Boot SPL 2022.10 (Oct 03 2022 - "
                "19:25:32 +0000)", after=False),
         "2 U-Boot SPL banner lines")]
    return [("uboot", base, name, text, wanted)
            for base, name, text, wanted in rows]


def m7_mutations():
    """M7's SBI implementation version (planning/mvp-m7-plan.md, D-10),
    each a single defect of an M7 fixture: a guest's kernel line naming
    the version before M7, or the version of an image with the other
    extension set: (claim, base, name, text, a finding the rejection
    names)."""
    two = fixture(M7_FIXTURES["two-guests"])
    tepoc = fixture(M7_FIXTURES["te-poc"])
    anchor = fixture(M7_FIXTURES["anchor"])
    probe, data = fixture(M7_FIXTURES["probe-console-input"]), PROBE_TEXT * 4
    return [
        ("SBI version", "m7two", "G0's kernel naming version 3",
         sbi_version_line(two, 0, "0x5", "0x3"), "G0 lacks"),
        ("SBI version", "m7two", "G1's kernel naming version 6",
         sbi_version_line(two, 1, "0x5", "0x6"), "G1 lacks"),
        ("SBI version", "m7tepoc", "G1's kernel naming version 3",
         sbi_version_line(tepoc, 1, "0x5", "0x3"), "G1 lacks"),
        ("SBI version", "m7anchor", "the protected domain's kernel naming "
         "version 4", sbi_version_line(anchor, 1, "0x6", "0x4"), "G1 lacks"),
        ("SBI version", "m7anchor", "the host's kernel naming version 5",
         sbi_version_line(anchor, 0, "0x6", "0x5"), "G0 lacks"),
    ] + [("probe-console-input", "m7input", name, kexec_form(text), wanted)
         for name, text, wanted in (
             ("a line of 63 bytes before the last",
              probe_received(probe, data, [63, 64, 64, 64, 1]),
              "in lines of 64"),
             ("the counts' total one short", replace_in(
                 probe_received(probe, data), "console-input total=",
                 "total=256", "total=255"), "the counts' total and sha256"),
             ("the counts' sha256 another's", replace_in(
                 probe_received(probe, data), "console-input total=",
                 hashlib.sha256(data).hexdigest()[:16], "0" * 16),
              "the counts' total and sha256"),
             ("a line of received bytes after the counts", insert(
                 probe_received(probe, data[:192]), "console-input total=",
                 f"BE_MVP:PROBE console-input bytes=256 "
                 f"hex={data[192:].hex()}"), "outside the probe's window"))]


def m74_mutations():
    """M7-4's console input and hostile guest (planning/mvp-m7-plan.md,
    D-4, D-11), each a single defect of an M7-4 fixture or its keys, nonce,
    or session file: (claim, base, name, text, a finding the rejection
    names[, None, the options it changes])."""
    two = fixture(SESSION_FIXTURES["two-guests-shell"])
    tepoc = fixture(SESSION_FIXTURES["te-poc-shell"])
    anchor = fixture(SESSION_FIXTURES["anchor-shell"])
    hostile = fixture(HOSTILE_FIXTURE)
    m7two = fixture(M7_FIXTURES["two-guests"])
    options = session_options("te-poc-shell")
    nonce = options["nonce"]
    summary = lines(tepoc)[where(lines(tepoc), "BE_MVP:18 ")]
    g1_sha = re.search(r" g1=83:([0-9a-f]{16}) ", summary).group(1)
    other_sha = f"{int(g1_sha, 16) ^ 1:016x}"
    secret = "42452d4d56502d4d322d544553542d5345435245542d30303030303030303030"
    return [
        ("console input", "m74tepoc", "a byte delivered to the wrong "
         "domain", replace_in(tepoc, "BE_MVP:18 ", " g0=86:", " g0=85:")
         .replace(" g1=83:", " g1=84:", 1), "BE_MVP:18 g0=85: the keys "
         "typed while g0 had the focus are 86"),
        ("console input", "m74tepoc", "a missing focus line",
         delete(tepoc, "BE_MVP:16 FOCUS g1"),
         "the BE_MVP:16 FOCUS lines name"),
        ("console input", "m74tepoc", "the nonce echoed in the wrong period",
         insert(tepoc, g(0, nonce), g(1, nonce)),
         "G1 prints the run nonce outside a focus period of its own"),
        ("console input", "m74tepoc", "a forged :18",
         replace_in(tepoc, "BE_MVP:18 ", summary, "BE_MVP:18 INPUT read=0 "
                    "g0=0:e3b0c44298fc1c14 g1=0:e3b0c44298fc1c14 "
                    "dropped=none"),
         "BE_MVP:18 read=0 is not the 193 keys typed"),
        ("console input", "m74anchor", "the secret in hex in a domain line",
         insert(anchor, "BE_MVP_G0: # echo ", g(0, secret)),
         "the capture holds the secret in hex"),
        ("output invariants", "m74tepoc", "a byte outside 0x20-0x7e in a "
         "domain line", replace_in(tepoc, "MVPINIT 12 CHAN write", "hello",
                                   "hel\x1blo"), "non-printable"),
        ("output invariants", "m74tepoc", "a guest line without its prefix",
         replace_in(tepoc, g(1, "MVPINIT 11 SHELL exit=0"),
                    g(1, "MVPINIT 11"), "MVPINIT 11"),
         "untagged text among the markers"),
        ("console input", "m74tepoc", "a :17 for an unprovoked reason",
         insert(tepoc, "BE_MVP:17 INPUT_DROP no-focus",
                "BE_MVP:17 INPUT_DROP ring-full"),
         "a BE_MVP:17 INPUT_DROP ring-full, which the session does not "
         "provoke"),
        ("console input", "m74tepoc", "a delivered SHA that does not match",
         replace_in(tepoc, "BE_MVP:18 ", g1_sha, other_sha),
         f"BE_MVP:18 g1's SHA-256 {other_sha} is not"),
        ("console input", "m7two", ":15 in a non-granting image",
         insert(m7two, "BE_MVP:07 ",
                "BE_MVP:15 INPUT_ARMED grants=g0,g1 prefix=0x7e"),
         "an input line, where the image declares no console input"),
        ("console input", "m74tepoc", "a missing :16 FOCUS none",
         delete(tepoc, FOCUS_NONE),
         "where the order expects 'BE_MVP:16 FOCUS none'"),
        ("denials", "m74tepoc", "an MVPINIT 08 with observed=0",
         replace_in(tepoc, "kind=store gpa=0x84000ff8 va=", "observed=1",
                    "observed=0"), "observed=0"),
        ("hostile guest", "m74hostile", "a forged run line bare",
         hostile_bare(hostile, FORGED_RUN), "a forged line as hart 0's"),
        ("hostile guest", "m74hostile", "a forged prefix bare",
         hostile_bare(hostile, FORGED_PREFIX), "a forged line as G1's"),
        ("console input", "m74anchor", "a byte delivered to the ungranted "
         "domain", replace_in(anchor, "BE_MVP:18 ", " g1=0:e3b0c44298fc1c14",
                              " g1=1:" + hashlib.sha256(b"x").hexdigest()[
                                  :16]),
         "bytes delivered to a domain without the console input grant"),
        ("console input", "m74tepoc", "the channel's text read back changed",
         replace_in(tepoc, "MVPINIT 12 CHAN read", "text=hello",
                    "text=jello"), "back, not the text last written"),
        ("console input", "m74two", "a second FOCUS none",
         insert(two, "BE_MVP:16 FOCUS g1", FOCUS_NONE),
         "a second BE_MVP:16 FOCUS none"),
        ("console input", "m74two", "a literal ~ dropped as well",
         replace_in(two, "BE_MVP:18 ", "dropped=bad-sequence:1",
                    "dropped=bad-sequence:2"),
         "BE_MVP:18 dropped=bad-sequence:2, the keys typed give"),
        ("console input", "m74anchor", "the no-grant drop's line missing",
         delete(anchor, "BE_MVP:17 INPUT_DROP no-grant"),
         "no BE_MVP:17 INPUT_DROP no-grant, which the session provokes"),
        ("console input", "m74tepoc", "a key the session does not type",
         tepoc, "typed.txt: step 2's keys", None, {
             "typed": options["typed"].replace("step=2 key=0x65",
                                               "step=2 key=0x66", 1)}),
        ("console input", "m74tepoc", "another session file", tepoc,
         "the session file is not the one", None,
         {"session": options["session"] + b"\n"}),
    ]


def m9_mutations(current=None, prefix="m9"):
    """M9's log (planning/mvp-m9-plan.md, D-4), each a single defect of an
    M9 fixture, judged against its image's reference: a line of the block
    or a registers line deleted, two record lines swapped, a LAUNCH line
    gone, a record printed after BE_MVP:07, a digest changed with the
    registers left as printed (the replay fails) or recomputed (the
    recomputation fails), DOMAIN_TERMINATED's digest another, a gate-fail
    without its DETAIL, and self-report-flip with a second difference:
    (claim, base, name, text, a finding the rejection names)."""
    def source(image):
        text = fixture(M9_FIXTURES[image])
        return current(image, text) if current else text

    two = source("two-guests")
    tepoc = source("te-poc")
    anchor = source("anchor")
    wrong = source("wrong-measurement")
    flipped = source("self-report-flip")
    base = lambda name: f"{prefix}{name}"

    def record(seq):
        return f"BE_MVP:19 LOG record seq={seq} "

    def digest_of(seq):
        def change(parts):
            index = where(parts, record(seq))
            parts[index] = re.sub(r"digest=[0-9a-f]{64}$", "digest=" +
                                  hashlib.sha256(b"wrong").hexdigest(),
                                  parts[index])
        return change

    def swapped(text, one, two_):
        parts = lines(text)
        first, second = where(parts, one), where(parts, two_)
        parts[first], parts[second] = parts[second], parts[first]
        return text_of(parts)

    def moved(text, needle, after):
        parts = lines(text)
        line = parts.pop(where(parts, needle))
        parts.insert(where(parts, after) + 1, line)
        return text_of(parts)
    terminated = next(line for line in lines(anchor) if line.startswith(
        "BE_MVP:12 DOMAIN_TERMINATED "))
    return [
        ("log", base("tepoc"), "a record line deleted", delete(tepoc, record(9)),
         "is not the line's position"),
        ("log", base("tepoc"), "two record lines swapped", swapped(
            tepoc, record(9), record(10)), "is not the line's position"),
        ("log", base("tepoc"), "the barrier's registers line deleted", delete(
            tepoc, "BE_MVP:20 REGISTERS at=barrier"),
         "no barrier registers line"),
        ("log", base("tepoc"), "the terminal registers line deleted", delete(
            tepoc, "BE_MVP:20 REGISTERS at=terminal"),
         "no terminal registers line"),
        ("log", base("tepoc"), "domain 1's LAUNCH line deleted", delete(
            tepoc, "BE_MVP:06 LAUNCH domain=1 "), "LAUNCH lines for domains"),
        ("log", base("two"), "a record line after BE_MVP:07", moved(
            two, record(5), "BE_MVP:07 "), "a log line after BE_MVP:07"),
        ("log", base("tepoc"), "a kernel digest another, the registers as "
         "printed", replace_in(tepoc, record(9), tepoc.split(record(9))[1]
                               .split("digest=")[1][:64],
                               hashlib.sha256(b"wrong").hexdigest()),
         "does not replay"),
        ("log", base("tepoc"), "a kernel digest another, the registers "
         "recomputed", relogged(tepoc, digest_of(9)),
         "kernel-image's printed digest"),
        ("log", base("anchor"), "the secret page's digest another, the "
         "registers recomputed", relogged(anchor, digest_of(13)),
         "secret-page's printed digest"),
        ("log", base("anchor"), "DOMAIN_TERMINATED's digest another", replace_in(
            anchor, terminated, re.search(r"sha256=([0-9a-f]{64})",
                                          terminated).group(1),
            hashlib.sha256(b"wrong").hexdigest()), "DOMAIN_TERMINATED"),
        ("log", base("wrongm"), "the gate-fail's DETAIL line deleted", delete(
            wrong, "BE_MVP:DETAIL "), "no DETAIL line"),
        ("log", base("flip"), "self-report-flip with a second difference, the "
         "registers recomputed", relogged(flipped, digest_of(0)),
         "not exactly"),
    ]


def retained_m9_mutations():
    """Two single defects judged only against the pinned pre-M11 era
    reference, proving that retained mode is active in the mutation test."""
    tepoc = fixture(M9_FIXTURES["te-poc"])
    record = "BE_MVP:19 LOG record seq=9 "
    digest = tepoc.split(record)[1].split("digest=")[1][:64]
    return [
        ("retained log", "m9tepoc", "a retained record line deleted",
         delete(tepoc, record), "is not the line's position"),
        ("retained log", "m9tepoc", "a retained digest unlike its era "
         "reference", replace_in(
             tepoc, record, digest, hashlib.sha256(b"wrong").hexdigest()),
         "kernel-image digest="),
    ]


def sbi_version_line(text, domain, before, after):
    """TEXT with domain DOMAIN's kernel line naming SBI implementation
    version AFTER in place of BEFORE."""
    parts = lines(text)
    old = f"SBI implementation ID=0x4245 Version={before}"
    index = next(index for index, line in enumerate(parts)
                 if line.startswith(g(domain, "")) and old in line)
    parts[index] = parts[index].replace(
        old, f"SBI implementation ID=0x4245 Version={after}")
    return text_of(parts)


def mutation_test(expects, pins, reports, measured, current, prior, latest,
                  era, era_references, root):
    """Every mutation of a passing capture must be rejected for its own
    reason (S1 H39): a verdict other than the base's, and the named
    finding. M0's bases are judged with M0's guest pins, te-poc's with
    M1's and its report, anchor's (the M2 board capture's too, as the
    board recorded it) with the current pins, its report, and its
    measured domain's kernel and DTB, and the uboot fixtures' with their
    markers' pins and their images' sizes and digests; each against
    EXPECTS, the expectations its capture was made with, but M6's against
    CURRENT (PRE_M7's), M7's against PRIOR (PRE_M9's), retained M9
    captures against ERA, and current M9 stand-ins against LATEST with the
    build at ROOT."""
    failed = count = 0
    verdicts = {}
    previous, m1, m2 = m0_pins(), m1_pins(), m2_pins()

    def judge(base, text, report_data=None, extra=None):
        name, image, mode = BASES[base]
        base_pins = previous if name in M0_FIXTURES else m1 \
            if name in M1_FIXTURES else m2 if m2_fixture(name) else pins
        retained = base.startswith("m9")
        current_m9 = base.startswith("c9")
        table = era if retained else latest if current_m9 else prior \
            if name in M7_FIXTURES.values() or \
            name in M74_FIXTURES else current \
            if name in M6_FIXTURES.values() else expects
        if report_data is None:
            report_data = report_for(table[image], reports)
        # A session's keys, nonce, and session file, a retained era
        # reference, or a current stand-in's build.
        options = dict(session_options(image) if image in SESSION_FIXTURES
                       and not (retained or current_m9) else BASE_OPTIONS.get(
                           base, BASE_OPTIONS[mode]),
                       **(retained_options(table[image], era_references)
                          if retained else {}),
                       **({"toolchain": "gcc", "build_root": root}
                          if current_m9 else {}),
                       **(extra or {}))
        return evaluate(text, table[image], mode, base_pins, report_data,
                        measured=PINNED_MEASUREMENT if m2_fixture(name)
                        else measured, **options)
    for base, (name, image, mode) in BASES.items():
        text = kexec_form(fixture(name)) if mode == "kexec" and \
            name not in BOARD_CAPTURES else fixture(name)
        if base.startswith("c9"):
            text = current_log_standin(text, latest[image], root)
        verdicts[base] = judge(base, text)[0]
    for claim, base, name, text, wanted, *rest in named_mutations() + \
            prelude_mutations() + \
            te_poc_mutations(report_for(expects["te-poc"], reports)) + \
            anchor_mutations(report_for(expects["anchor"], reports)) + \
            uboot_mutations() + m7_mutations() + m74_mutations() + \
            retained_m9_mutations() + m9_mutations(
                lambda image, text: current_log_standin(
                    text, latest[image], root), "c9"):
        verdict, record = judge(base, text, *rest)
        named = [finding for finding in record["findings"] + record["stops"]
                 if wanted in finding]
        ok = verdict != verdicts[base] and bool(named)
        count += 1
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} [{claim}] {base}: {name}: "
              f"{verdict} {named[:1] if ok else record['findings'][:3]}")
    for base, name, text in seeded_mutations(
            current=lambda image, data: current_log_standin(
                data, latest[image], root)):
        verdict, record = judge(base, text)
        ok = verdict != verdicts[base] and bool(record["findings"])
        count += 1
        failed += not ok
        if not ok:
            print(f"FAIL [seeded] {base}: {name}: {verdict}")
    bases_ok = verdicts == {"two": "PASS", "hart6": "PASS", "kexec": "PASS",
                            "fallback": "PASS", "rdcycle": "PASS",
                            "payload": "PASS", "refused": "REFUSED",
                            "platform": "PASS", "tepoc": "PASS",
                            "anchor": "PASS", "wrongm": "PASS",
                            "ngc": "PASS", "k3anchor": "PASS",
                            "uboot": "PASS", "quboot": "PASS",
                            "m6two": "PASS", "m6tepoc": "PASS",
                            "m6anchor": "PASS", "m7two": "PASS",
                            "m7tepoc": "PASS", "m7anchor": "PASS",
                            "m7input": "PASS",
                            "m74two": "PASS", "m74tepoc": "PASS",
                            "m74anchor": "PASS", "m74hostile": "PASS",
                            "m9two": "PASS", "m9tepoc": "PASS",
                            "m9anchor": "PASS", "m9wrongm": "PASS",
                            "m9flip": "PASS", "c9two": "PASS",
                            "c9tepoc": "PASS", "c9anchor": "PASS",
                            "c9wrongm": "PASS", "c9flip": "PASS"}
    failed += not bases_ok
    print(f"BE_MVP_CAPTURE_MUTATIONS: {'PASS' if not failed else 'FAIL'} "
          f"mutations={count} rejected={count - failed + (not bases_ok)} "
          f"seed=0x{MUTATION_SEED:x}")
    return 0 if not failed else 1


# ------------------------------------------- beryllium-cheri: mutations
# The CHERI enforcement rules (planning/cheri-enforcement-plan.md, section
# 6) are the CHERI expectations' (tools/gen-scenario.py, --monitor cheri
# and --guest-flavour cheri-linux), and their mutations are of the passing
# capture this checker has just judged (--cheri-mutations, which
# tests/run-qemu.sh gives the CHERI-aware monitor's runs): each must be
# rejected for its own reason, a verdict other than PASS and the named
# finding. B1: the CHERI Linux guest's capability-write PTE line, and Q6,
# its root capability's line, in each scenario's own image; B2: channel-cw,
# whose walker refuses its level-0 leaf before any root's line; C1 and C2:
# te-poc's roles' lines of their own CHERI faults, each by value; C3:
# cheri-fault-hs, whose hedeleg leaves the CHERI fault to HS; B3:
# cap-store, whose G0 module's tagged store into the channel page the
# G-stage faults under Zcheripte; B4: cap-store-control, the same image
# without Zcheripte, whose store lands.
CHERI_PTE_LINE = ("[<s>] CHERI: Selected SATP mode: 0x8000000000000000 "
                  "PTE.CW support: yes")
CHERI_ROOT_PREFIX = "[<s>] CHERI: Root capability: "
CHERI_WHOLE = "0x0000000000000000-0xffffffffffffffff"
CHERI_TESTS = "MVPINIT 14 CHERI "
CHERI_TRACE_OFF = CHERI_TESTS + "exception-trace=0"
CHERI_REPORT_LINE = ("[    0.000000] ===== CHERI exception: addr=0x100000010 "
                     "xtval2=0x10004 (length violation, data fault due to "
                     "load store or AMO)")


def cheri_findings(capture, outcome, pins, expect):
    """beryllium-cheri: a declared failure's faulting domain, the one its
    exit DETAIL names, ends with the lines the variant declares, domain
    templates (cheri-fault-hs: its trace line 0, so that its child printed
    nothing; cap-store: its module's lines before the store, so that the
    module printed nothing after it); detail_findings() judges the DETAIL
    itself."""
    last = outcome.get("last_lines")
    details = [DETAIL_FORMS["exit"].fullmatch(line.text)
               for line in capture.monitor
               if line.text.startswith(DETAIL_PREFIX)]
    if not last or not details or details[0] is None:
        return []
    domain = int(details[0].group(1))
    own = capture.domains[domain] if domain < len(capture.domains) else []
    ends = [line.text for line in own[-len(last):]]
    matched = len(ends) == len(last) and all(
        re.fullmatch(domain_pattern(template, domain, pins,
                                    expect.get("domain_placeholders")), text)
        for template, text in zip(last, ends))
    return [] if matched else [
        f"G{domain}, which the DETAIL names, ends with "
        f"{[text[:60] for text in ends]!r}, not {last!r}"]


def cheri_line_edit(text, prefix, needle, old=None, new=None):
    """beryllium-cheri: TEXT with its first line that starts with PREFIX
    and holds NEEDLE deleted, or with OLD in it replaced by NEW."""
    parts = lines(text)
    index = next(at for at, line in enumerate(parts)
                 if line.startswith(prefix) and needle in line)
    if old is None:
        del parts[index]
    elif old in parts[index]:
        parts[index] = parts[index].replace(old, new, 1)
    else:
        raise ValueError(f"{old!r} not in {parts[index]!r}")
    return text_of(parts)


def cheri_mutations(expect):
    """beryllium-cheri: the mutations that apply to EXPECT's image, each
    (name, edit of the capture's text, the finding)."""
    own = expect.get("domain_lines") or {}
    first = own.get("0", []) if isinstance(own, dict) else own
    out = []
    if expect["outcome"].get("pass") and \
            expect["image"] == expect["scenario"]:
        lacks = "{} lacks the required line '{}"
        if CHERI_PTE_LINE in first:
            out += [
                ("B1: G0's PTE.CW line missing", lambda text: cheri_line_edit(
                    text, "BE_MVP_G0: ", "PTE.CW support: yes"),
                 lacks.format("G0", CHERI_PTE_LINE)),
                ("B1: G1's PTE.CW support no", lambda text: cheri_line_edit(
                    text, "BE_MVP_G1: ", "PTE.CW support: yes", "yes",
                    "no"), lacks.format("G1", CHERI_PTE_LINE))]
        if any(line.startswith(CHERI_ROOT_PREFIX) for line in first):
            out += [
                ("Q6: G0's root capability bounded to its window",
                 lambda text: cheri_line_edit(
                     text, "BE_MVP_G0: ", "] CHERI: Root capability: ",
                     CHERI_WHOLE, "0x0000000080000000-0x0000000084000000"),
                 lacks.format("G0", CHERI_ROOT_PREFIX)),
                ("Q6: G1's root capability line missing",
                 lambda text: cheri_line_edit(
                     text, "BE_MVP_G1: ", "] CHERI: Root capability: "),
                 lacks.format("G1", CHERI_ROOT_PREFIX))]
        if CHERI_TRACE_OFF in first:
            out += cheri_test_mutations(first, lacks)
    if expect["image"] == "cheri-fault-hs":
        out += cheri_fault_mutations(first)
    if expect["image"] == "channel-cw":
        walked = next(entry["template"] for entry in expect["control_lines"]
                      if entry["template"].startswith(
                          "BE_MVP:03 GSTAGE_BUILT_REWALKED domain=0 "))
        fail = FAIL_PREFIX + "gstage"
        out += [
            ("B2: a BE_MVP:07 line", lambda text: insert(
                text, fail, "BE_MVP:07 BLOCKS_PUBLISHED region=0x102044000 "
                "bytes=0x20000 generation=1 budget_ticks=0x100000000",
                after=False), "where the order expects"),
            ("B2: the failure after a domain entered", lambda text: insert(
                text, fail, "BE_MVP:10 DOMAIN_ENTERED hart=1 domain=0 "
                "pc=0x80200000 a0=0x0 a1=0x83e00000 ticks=0x47a7",
                after=False), "where the order expects"),
            ("B2: the failure after domain 0's root was walked",
             lambda text: insert(text, fail, walked, after=False),
             "the failure follows BE_MVP:03, expected BE_MVP:02"),
            ("B2: the channel check's DETAIL", lambda text: insert(
                text, fail, "BE_MVP:DETAIL channel=0 domain=0 hart=1 "
                "walked=0x10000000460000d7 declared=0x460000d7"),
             "class gstage takes no BE_MVP:DETAIL line"),
            ("B2: another failure class", lambda text: replace_in(
                text, fail, "gstage", "payload"),
             f"expected {fail!r}")]
    if expect["image"] == "cap-store":
        out += cap_store_mutations(expect)
    if expect["image"] == "cap-store-control":
        out += cap_store_control_mutations(first)
    return out


def cap_store_mutations(expect):
    """beryllium-cheri: B3's mutations of cap-store's capture: its DETAIL's
    htval of the next page, the store from VU mode, a transformed
    instruction, tval at another page offset, and a zero vsatp; and G0's
    lines: the module's post-store line present, its own-data tag 0, and
    its integer readback missing."""
    template = expect["outcome"]["detail_lines"][0]["template"]
    htval = re.search(r" htval=(0x[0-9a-f]+) ", template).group(1)
    detail = "none of the variant's DETAIL lines"
    ends = "which the DETAIL names, ends with"

    def field(name, value):
        def edit(text):
            old = re.search(rf"^{DETAIL_PREFIX}.* ({name}=0x[0-9a-f]+) ",
                            text, re.M).group(1)
            return replace_in(text, DETAIL_PREFIX, old, f"{name}={value(old)}")
        return edit

    def module(needle, old=None, new=None):
        return lambda text: cheri_line_edit(
            text, "BE_MVP_G0: ", "be_cheri_store: " + needle, old, new)
    return [
        ("B3: htval of the next page", lambda text: replace_in(
            text, DETAIL_PREFIX, f"htval={htval} ",
            f"htval={int(htval, 16) + 0x400:#x} "), detail),
        ("B3: the store from VU mode", lambda text: replace_in(
            text, DETAIL_PREFIX, "spvp=1", "spvp=0"), detail),
        ("B3: a transformed instruction", lambda text: replace_in(
            text, DETAIL_PREFIX, "htinst=0x0 ", "htinst=0x3023 "), detail),
        ("B3: tval at page offset 0x088", field(
            "tval", lambda old: old[5:-3] + "088"), detail),
        ("B3: vsatp zero", field("vsatp", lambda old: "0x0"), detail),
        ("B3: the module's post-store line", lambda text: insert(
            text, "be_cheri_store: channel gpa=", "BE_MVP_G0: [    0.092300] "
            "be_cheri_store: channel offset=0x80 tag=1"), ends),
        ("B3: the own-data tag 0", module("own tag=", "tag=1", "tag=0"),
         ends),
        ("B3: the integer readback missing", module("channel gpa="), ends)]


def cap_store_control_mutations(first):
    """beryllium-cheri: B4's mutations of cap-store-control's capture
    (FIRST, domain 0's required lines, holds the module's post-store line):
    that line with tag 0 or missing, G0's capability-write PTE line reading
    yes, and a BE_MVP:FAIL."""
    lacks = "{} lacks the required line '{}"
    stored = next(text for text in first
                  if text.startswith("[<s>] be_cheri_store: channel offset="))
    probe = CHERI_PTE_LINE.replace("yes", "no")

    def edit(needle, old=None, new=None):
        return lambda text: cheri_line_edit(text, "BE_MVP_G0: ", needle, old,
                                            new)
    return [
        ("B4: the post-store tag 0", edit(stored[6:], "tag=1", "tag=0"),
         lacks.format("G0", stored)),
        ("B4: the post-store line missing", edit(stored[6:]),
         lacks.format("G0", stored)),
        ("B4: G0's PTE.CW support yes", edit(
            "PTE.CW support: no", "no", "yes"), lacks.format("G0", probe)),
        ("B4: a BE_MVP:FAIL", lambda text: insert(
            text, "BE_MVP:13 ", FAIL_PREFIX + "guest-page-fault",
            after=False), "where the order expects")]


def cheri_test_mutations(first, lacks):
    """beryllium-cheri: C1's and C2's mutations of a capture whose domains
    print te-poc's roles' CHERI test lines (FIRST, domain 0's required
    lines, holds them): each value, in G0's lines or G1's, and the guest
    kernel's report of the fault, each a required line's absence or a
    rejected substring (LACKS, the absence's finding)."""
    trace_on, bounds, short, whole = (
        next(line for line in first if line.startswith(CHERI_TESTS + kind))
        for kind in ("exception-trace=1", "bounds ", "write bound=16 ",
                     "write bound=64 "))
    base, addr = re.search(r" base=(0x[0-9a-f]+) addr=(0x[0-9a-f]+)$",
                           bounds).groups()

    def edit(domain, needle, old=None, new=None):
        return lambda text: cheri_line_edit(text, f"BE_MVP_G{domain}: ",
                                            needle, old, new)
    return [
        ("C1: G0's fault SEGV_ACCERR", edit(0, bounds, "code=12", "code=2"),
         lacks.format("G0", bounds)),
        ("C1: G1's signal SIGBUS", edit(1, bounds, "signo=11", "signo=7"),
         lacks.format("G1", bounds)),
        ("C1: G0's si_addr at the base", edit(
            0, bounds, f"addr={addr}", f"addr={base}"),
         lacks.format("G0", bounds)),
        ("C1: G1's si_addr at the base plus 17", edit(
            1, bounds, f"addr={addr}", f"addr={int(base, 16) + 17:#x}"),
         lacks.format("G1", bounds)),
        ("C1: G0's child without a fault", edit(
            0, bounds, bounds.split("bounds ")[1], "no-fault"),
         lacks.format("G0", bounds)),
        ("C1: G1's trace line 1 missing", edit(1, trace_on),
         lacks.format("G1", trace_on)),
        ("C1: G0's trace line 1 reading 0", edit(
            0, trace_on, "exception-trace=1", "exception-trace=0"),
         lacks.format("G0", trace_on)),
        ("C1: G1's kernel report of the fault", lambda text: insert(
            text, f"BE_MVP_G1: {CHERI_TRACE_OFF}",
            f"BE_MVP_G1: {CHERI_REPORT_LINE}"),
         "rejected '===== CHERI exception'"),
        ("C2: G0's bounded write of all 64 bytes", edit(
            0, short, "result=-1 errno=14", "result=64 errno=0"),
         lacks.format("G0", short)),
        ("C2: G1's bounded write of 16 bytes", edit(
            1, short, "result=-1 errno=14", "result=16 errno=0"),
         lacks.format("G1", short)),
        ("C2: G0's whole write failing", edit(
            0, whole, "result=64 errno=0", "result=-1 errno=14"),
         lacks.format("G0", whole))]


def cheri_fault_mutations(first):
    """beryllium-cheri: C3's mutations of cheri-fault-hs's capture (FIRST,
    domain 0's required lines, holds the child's line): the CHERI fault
    delegated, another cause, address, or mode in the DETAIL, the run
    passing, and the faulting domain's child printing or its trace line 0
    missing."""
    bounds = next(line for line in first
                  if line.startswith(CHERI_TESTS + "bounds "))
    base, addr = re.search(r" base=(0x[0-9a-f]+) addr=(0x[0-9a-f]+)$",
                           bounds).groups()
    detail = "none of the variant's DETAIL lines"

    def faulting(text):
        return "BE_MVP_G" + re.search(r"^BE_MVP:DETAIL domain=([0-9]+) ",
                                      text, re.M).group(1) + ": "
    return [
        ("C3: hedeleg with the CHERI fault", lambda text: replace_in(
            text, "BE_MVP:09 HART_READY ", "hedeleg=0xb15d",
            "hedeleg=0x1000b15d"), "is not a WARL reading of 0xb15d"),
        ("C3: another cause", lambda text: replace_in(
            text, DETAIL_PREFIX, "cause=0x1c", "cause=0x17"), detail),
        ("C3: tval at the base", lambda text: replace_in(
            text, DETAIL_PREFIX, f"tval={addr}", f"tval={base}"), detail),
        ("C3: the fault from VS mode", lambda text: replace_in(
            text, DETAIL_PREFIX, "spvp=0", "spvp=1"), detail),
        ("C3: the run passing", lambda text: delete(delete(
            text, DETAIL_PREFIX), FAIL_PREFIX + "exception"),
         "no BE_MVP:FAIL exception line"),
        ("C3: the child's line after the trace line 0", lambda text: insert(
            text, faulting(text) + CHERI_TRACE_OFF, faulting(text) + bounds),
         "which the variant declares absent"),
        ("C3: the trace line 0 missing", lambda text: delete(
            text, faulting(text) + CHERI_TRACE_OFF),
         "which the DETAIL names, ends with")]


def cheri_mutation_test(data, expect, args, options, verdict, record):
    """beryllium-cheri: each of cheri_mutations() on the capture DATA,
    judged as main() judged it; the run's verdict, FAIL with a finding
    when a mutation was not rejected for its own reason. Its lines go to
    record["cheri_mutations"]."""
    mutations = cheri_mutations(expect) if verdict == "PASS" else []
    if not mutations:
        return verdict
    pins = read_pins(args.pins)
    report_data = pathlib.Path(args.report[0]).read_bytes() \
        if args.report else None
    text = data.decode("utf-8", "replace")
    out, failed = [], []
    for name, edit, wanted in mutations:
        got, judged = evaluate(edit(text), expect, args.mode, pins,
                               report_data, **options)
        named = [finding for finding in judged["findings"]
                 if wanted in finding]
        ok = got != "PASS" and bool(named)
        failed += [] if ok else [name]
        out.append(f"cheri-mutation {'ok  ' if ok else 'FAIL'} {name}: "
                   f"{got} {named[:1] if ok else judged['findings'][:2]}")
    out.append(f"BE_MVP_CHERI_MUTATIONS: {'FAIL' if failed else 'PASS'} "
               f"image={expect['image']} mutations={len(mutations)} "
               f"rejected={len(mutations) - len(failed)}")
    record["cheri_mutations"] = out
    if not failed:
        return verdict
    record["findings"] += [f"CHERI mutation {name!r} was not rejected for "
                           f"its own reason" for name in failed]
    record["result"], record["boot_marker"] = "FAIL", "FAIL"
    return "FAIL"


def report(verdict, record, name):
    """The checker's printed lines."""
    out = [f"finding: {finding}" for finding in record["findings"]]
    out += [f"{stop}" for stop in record["stops"]]
    fields = record["fields"]
    counts = " ".join(f"{key}={fields[key]}" for key in (
        "boot_hart", "kexec_hart", "rule_hart", "started", "exits_g0",
        "exits_g1", "denials_g0", "denials_g1", "mgmt_g0", "mgmt_g1",
        "records", "wakes", "overlap_ticks", "shorter_ticks",
        "alternations") if key in fields)
    lines = " ".join(f"{key}={value}" for key, value in
                     sorted(record["lines"].items()))
    out.append(f"BE_MVP_COUNTS: {counts} {lines}".rstrip())
    if record["costs"]:
        out.append("BE_MVP_COSTS: " + " ".join(
            f"{key}={value}" for key, value in sorted(
                record["costs"].items())))
    for label, values in sorted(record["probe_values"].items()):
        out.append(f"BE_MVP_PROBE_VALUES: {label} " + " ".join(
            f"{key}={value}" for key, value in values.items()))
    if fields.get("launcher_mode") == "uboot":
        out.append(("BE_MVP_UBOOT: " + " ".join(
            f"{key}={fields[key]}" for key in (
                "load_bytes", "load_digest_kind", "load_digest",
                "moving_from", "moving_to", "moving_end", "fdt_blob",
                "fdt_loaded", "fdt_end", "fdt_in_place")
            if key in fields)).rstrip())
    out += log_report(record)
    # beryllium-cheri: the CHERI rules' mutations (--cheri-mutations).
    out += record.get("cheri_mutations", [])
    out.append(f"BE_MVP_RESULT: {verdict} terminal={record['terminal']}")
    out.append(f"BE_MVP_CAPTURE[{fields['mode']} {name}]: {verdict}")
    return "\n".join(out)


def log_report(record):
    """M9's log lines of the checker's report: the class, state, and
    bindings; the printed registers and the replay (unprotected); the
    ticks, recorded and judged by form alone; each record's comparison
    with the reference and its recomputation; the declared self-report."""
    log = record.get("log")
    if not log:
        return []
    contract, registers = log.get("contract") or {}, log.get(
        "registers") or {}
    ticks = log.get("ticks") or {}
    out = [f"BE_MVP_LOG: contract={contract.get('sequence', '-')}/"
           f"{contract.get('run', '-')} r2={log.get('r2') or '-'} "
           f"state={log.get('state') or '-'} count={log.get('count')} "
           f"lines={log.get('lines', 0)} bytes={log.get('volume_bytes', 0)}"
           f" boot_image={log.get('boot_image') or '-'} reference="
           f"{(log.get('reference') or '-')[:16]} export="
           f"{(log.get('export_sha256') or '-')[:16]}"]
    for at in ("barrier", "terminal", "replayed"):
        values = registers.get(at)
        out.append(f"BE_MVP_LOG_REGISTERS: at={at}" + "".join(
            f" r{index}={value}" for index, value in enumerate(
                values or [])) + (" none" if not values else "") +
            (" (unprotected)" if at == "replayed" else ""))
    out.append("BE_MVP_LOG_TICKS: barrier=" + (ticks.get("barrier") or
                                               "none") + "".join(
        f" launch_g{domain}={value}" for domain, value in sorted(
            (ticks.get("launch") or {}).items())))
    out += [f"BE_MVP_LOG_RECORD: seq={row['recnum']} object={row['object']}"
            f" stream={row['stream']} reference={row['fields']} "
            f"recomputed={row.get('recomputed', 'none')}"
            for row in log.get("records") or []]
    out += [f"BE_MVP_LOG_SELF_REPORT: {finding} (declared)"
            for finding in record.get("log_declared") or []]
    return out


def load_check_image():
    spec = importlib.util.spec_from_file_location(
        "mvp_check_image", HERE / "check-image.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_image(spec, pins_path, kernel_path, expect_path=None,
                report_path=None):
    """--check-image TOOLCHAIN:IMG:BIN[:VARIANT]: a board image, before any
    loader sees it, by tests/check-image.py's boot-image rules; with a v2
    expectation (--expect, te-poc's or a variant's) and its authority
    report (--report), against that scenario's DTBs and bootargs, the
    expectation naming the image's variant (or its scenario)."""
    parts = spec.split(":")
    if len(parts) not in (3, 4) or parts[0] not in ("gcc", "clang"):
        print(f"--check-image {spec!r} is not TOOLCHAIN:IMG:BIN[:VARIANT]")
        return 2
    toolchain, image_path, flat_path = parts[:3]
    variant = parts[3] if len(parts) == 4 else None
    images = load_check_image()
    data = pathlib.Path(image_path).read_bytes()
    flat = pathlib.Path(flat_path).read_bytes()
    kernel = pathlib.Path(kernel_path).read_bytes() if kernel_path else None
    scenario_name = None
    try:
        scenario = images.TWO_GUESTS
        if expect_path:
            expect = json.loads(pathlib.Path(expect_path).read_text(
                encoding="utf-8"))
            report_data = pathlib.Path(report_path).read_bytes() \
                if report_path else None
            if report_data is None or hashlib.sha256(
                    report_data).hexdigest() != expect["report"]["sha256"]:
                raise ValueError("the --report file is not the "
                                 "expectation's authority report")
            if expect["image"] != (variant or expect["scenario"]):
                raise ValueError(f"the expectation is {expect['image']}'s, "
                                 f"not {variant or expect['scenario']}'s")
            scenario = images.Scenario(expect, json.loads(report_data))
            scenario_name = scenario.name
        boot = images.check_boot(data, images.BOOT_TEXT_OFFSET, flat,
                                 images.read_pins(pins_path), kernel,
                                 variant=variant, scenario=scenario)
        result = "PASS"
    except (images.ImageError, KeyError, ValueError, TypeError) as error:
        boot, result = {}, f"FAIL {error}"
    fdt = STAGING + align_up(len(data), FDT_ALIGN)
    print(f"BE_MVP_BOOT_IMAGE[{toolchain}]: {result} {image_path} "
          f"bytes=0x{len(data):x} "
          f"sha256={hashlib.sha256(data).hexdigest()} "
          f"flat_sha256={hashlib.sha256(flat).hexdigest()} "
          f"kexec_fdt=0x{fdt:x} variant={variant or 'none'} "
          f"dtb0=0x{boot.get('dtb0_offset', 0):x}"
          + (f" scenario={scenario_name}" if scenario_name else ""))
    return 0 if result == "PASS" else 1


def number(text):
    return int(text, 0)


def crc32_text(text):
    """A CRC-32 as U-Boot prints it, or with 0x."""
    return int(text, 16)


def md5_text(text):
    """An MD5 as U-Boot's md5sum prints it: 32 hexadecimal digits."""
    if not re.fullmatch(r"[0-9a-fA-F]{32}", text):
        raise argparse.ArgumentTypeError(f"{text!r} is not an MD5's 32 "
                                         f"hexadecimal digits")
    return text.lower()


def report_for(expect, reports):
    """The authority report among REPORTS ({SHA-256: bytes}) that EXPECT
    names by its SHA-256, or None."""
    return reports.get(expect.get("report", {}).get("sha256"))


def main(argv):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("capture", nargs="?")
    parser.add_argument("--expect")
    parser.add_argument("--expect-dir", action="append")
    parser.add_argument("--report", action="append", default=[])
    parser.add_argument("--mode", choices=("direct", "kexec", "uboot"),
                        default="direct")
    # beryllium-cheri: the monitor variant whose values the checks expect.
    parser.add_argument("--monitor", choices=tuple(MONITOR_HEDELEG),
                        default="riscv")
    # beryllium-cheri: the CHERI rules' mutations of a passing capture
    # (cheri_mutation_test()), for the CHERI-aware monitor's runs.
    parser.add_argument("--cheri-mutations", action="store_true")
    parser.add_argument("--pins", default=str(DEFAULT_PINS))
    parser.add_argument("--sbi-version")
    parser.add_argument("--kexec-fdt", type=number)
    parser.add_argument("--image", action="append", default=[])
    parser.add_argument("--image-bytes", type=number)
    parser.add_argument("--image-crc32", type=crc32_text)
    parser.add_argument("--image-md5", type=md5_text)
    parser.add_argument("--toolchain", choices=("gcc", "clang"))
    parser.add_argument("--json")
    parser.add_argument("--check-image")
    parser.add_argument("--kernel")
    parser.add_argument("--dtb")
    parser.add_argument("--typed")
    parser.add_argument("--nonce")
    parser.add_argument("--session")
    parser.add_argument("--reference")
    parser.add_argument("--build-root")
    parser.add_argument("--log-json")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--mutation-test", action="store_true")
    parser.add_argument("--write-fixtures")
    args = parser.parse_args(argv[1:])
    global HEDELEG, HEDELEG_REQUIRED
    HEDELEG, HEDELEG_REQUIRED = MONITOR_HEDELEG[args.monitor]
    many = args.self_test or args.mutation_test or args.write_fixtures
    if args.cheri_mutations and (args.monitor != "cheri" or many):
        parser.error("--cheri-mutations judges one capture of the "
                     "CHERI-aware monitor (--monitor cheri)")
    if len(args.report) > 1 and not many:
        parser.error("one --report, the expectation's")
    if len(args.image) > 1 and not args.write_fixtures:
        parser.error("one --image, the capture's")
    if args.dtb and not args.kernel:
        parser.error("--dtb, the measured domain's DTB, needs its --kernel")
    measured = (pathlib.Path(args.kernel).read_bytes(),
                pathlib.Path(args.dtb).read_bytes()) if args.dtb else None
    if args.check_image:
        return check_image(args.check_image, args.pins, args.kernel,
                           args.expect, (args.report or [None])[0])
    if many:
        if not args.expect_dir:
            parser.error("--expect-dir is required")
        expects = {}
        for directory in args.expect_dir:
            expects.update(load_expects(directory))
        pins = read_pins(args.pins)
        reports = {hashlib.sha256(data).hexdigest(): data for data in (
            pathlib.Path(path).read_bytes() for path in args.report)}
        for name in ("te-poc", "anchor"):
            if name in expects and report_for(expects[name], reports) is \
                    None:
                parser.error(f"{name}'s expectations need its --report")
        if "anchor" in expects and measured is None:
            parser.error("anchor's expectations need its measured domain's "
                         "--kernel and --dtb")
        if args.write_fixtures:
            if any("=" not in spec for spec in args.image):
                parser.error("--image KIND=BOOT_IMG with --write-fixtures")
            return write_fixtures(args.write_fixtures, expects, pins,
                                  reports, measured, {
                                      kind: pathlib.Path(path).read_bytes()
                                      for kind, path in (
                                          spec.split("=", 1)
                                          for spec in args.image)},
                                  pathlib.Path(args.build_root or
                                               DEFAULT_BUILD))
        if not {"te-poc", "anchor"} <= set(expects):
            parser.error("the self-test and mutations need te-poc's and "
                         "anchor's expectations (--expect-dir), their "
                         "--report, and anchor's --kernel and --dtb")
        old, old_reports = pre_m6()
        before, before_reports = pre_m7()
        prior, prior_reports = pre_m9()
        era, era_reports, era_references = pre_m11()
        reports.update(old_reports)
        reports.update(before_reports)
        reports.update(prior_reports)
        reports.update(era_reports)
        root = pathlib.Path(args.build_root or DEFAULT_BUILD)
        if args.self_test:
            return self_test(dict(before, **old), pins, reports, measured,
                             before, prior, expects, era, era_references,
                             root)
        return mutation_test(dict(before, **old), pins, reports, measured,
                             before, prior, expects, era, era_references,
                             root)
    if not args.capture or not args.expect:
        parser.error("a capture and --expect are required")
    expect = json.loads(pathlib.Path(args.expect).read_text(encoding="utf-8"))
    # beryllium-cheri: the hedeleg a CHERI variant's image arms, which its
    # expectation states (cheri-fault-hs's, without cause 28).
    if args.monitor == "cheri" and "hedeleg" in expect["outcome"]:
        HEDELEG, HEDELEG_REQUIRED = (int(value, 16) for value in
                                     expect["outcome"]["hedeleg"])
    data = pathlib.Path(args.capture).read_bytes()
    options = {"sbi_version": args.sbi_version, "kexec_fdt": args.kexec_fdt,
               "measured": measured, "toolchain": args.toolchain,
               "reference": args.reference, "build_root": args.build_root}
    # A console image's run (tests/session-typist.py): its keys, its
    # nonce, and its session file.
    if args.typed:
        options["typed"] = pathlib.Path(args.typed).read_text(
            encoding="ascii")
    if args.nonce:
        options["nonce"] = pathlib.Path(args.nonce).read_text(
            encoding="ascii").strip()
    if args.session:
        options["session"] = pathlib.Path(args.session).read_bytes()
    if args.image:
        image = pathlib.Path(args.image[0]).read_bytes()
        options.update(image_bytes=len(image), image_crc32=zlib.crc32(image),
                       image_md5=hashlib.md5(image).hexdigest(),
                       image_data=image)
    for key, given in (("image_bytes", args.image_bytes),
                       ("image_crc32", args.image_crc32),
                       ("image_md5", args.image_md5)):
        if given is not None and options.get(key, given) != given:
            parser.error(f"--{key.replace('_', '-')} is not --image's")
        if given is not None:
            options[key] = given
    verdict, record = evaluate(
        data, expect, args.mode, read_pins(args.pins),
        pathlib.Path(args.report[0]).read_bytes() if args.report else None,
        **options)
    if args.cheri_mutations:
        verdict = cheri_mutation_test(data, expect, args, options, verdict,
                                      record)
    record["capture"] = {"sha256": hashlib.sha256(data).hexdigest(),
                         "bytes": len(data)}
    record["expect"] = {"image": expect["image"],
                        "scenario_sha256": expect["scenario_sha256"]}
    record["toolchain"] = args.toolchain
    # The rebuilt log (log.json; mvp/docs/log-profile.md, 5.2), when the
    # run printed a block that rebuilds, in the run record.
    exported = record.pop("log_export", None)
    target = log_json_path(args.log_json, args.json)
    if target is not None and exported is not None:
        target.write_bytes(LOG.render(exported))
    if args.json:
        pathlib.Path(args.json).write_text(
            json.dumps(record, indent=1, sort_keys=True) + "\n",
            encoding="utf-8")
    print(report(verdict, record, expect["image"]))
    return VERDICT_STATUS[verdict]


if __name__ == "__main__":
    sys.exit(main(sys.argv))
